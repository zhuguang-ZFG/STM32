"""Optional cloud adapters with mocked HTTP only; no request ever leaves the machine, keys never appear in output."""
import base64
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import numpy as np
import gemini_tts
import volcengine_tts
from test_audio_gate import speech_like, save


class CloudTTSTests(unittest.TestCase):
    def test_volcengine_request_follows_v3_api_and_keeps_keys_private(self):
        body = volcengine_tts.request_body('你好。', {'speaker': 'zh_male_xuanyijieshuo_uranus_bigtts'})
        self.assertEqual(body['req_params']['speaker'], 'zh_male_xuanyijieshuo_uranus_bigtts')
        self.assertTrue(body['req_params']['audio_params']['enable_subtitle'])
        self.assertTrue(json.loads(body['req_params']['additions'])['aigc_metadata']['enable'])
        with patch.dict(os.environ, {'VOLC_TTS_APP_ID': 'app', 'VOLC_TTS_ACCESS_KEY': 'secret-token'}, clear=True):
            headers = volcengine_tts.headers('seed-tts-2.0')
            self.assertEqual((headers['X-Api-App-Id'], headers['X-Api-Resource-Id']), ('app', 'seed-tts-2.0'))
        with patch.dict(os.environ, {}, clear=True), self.assertRaises(SystemExit) as raised:
            volcengine_tts.headers('seed-tts-2.0')
        self.assertNotIn('secret-token', str(raised.exception))

    def test_volcengine_stream_returns_audio_and_subtitle_timestamps(self):
        with tempfile.TemporaryDirectory() as directory:
            wav = save(Path(directory) / 'speech.wav', speech_like([(1.5, .3)]))
            mp3 = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(wav), '-f', 'mp3', '-'], capture_output=True, check=True).stdout
        lines = [json.dumps({'code': 0, 'data': base64.b64encode(mp3[:len(mp3) // 2]).decode()}),
                 json.dumps({'code': 0, 'data': base64.b64encode(mp3[len(mp3) // 2:]).decode()}),
                 json.dumps({'code': 0, 'data': None, 'sentence': {'text': '你好。', 'words': [
                     {'word': '你', 'startTime': .1, 'endTime': .3, 'confidence': .9}, {'word': '好。', 'startTime': .3, 'endTime': .6, 'confidence': .9}]}}),
                 '', json.dumps({'code': 20000000, 'message': 'ok', 'data': None})]
        response = MagicMock(status_code=200)
        response.iter_lines.return_value = lines
        response.__enter__.return_value = response
        with patch.dict(os.environ, {'VOLC_TTS_API_KEY': 'secret'}), patch('requests.post', return_value=response) as post:
            samples, rate, words = volcengine_tts.synthesizer({})('你好。', 1)
        self.assertEqual(post.call_args.kwargs['headers']['X-Api-Key'], 'secret')
        self.assertEqual(rate, 48000)
        self.assertAlmostEqual(len(samples) / rate, 1.8, delta=.1)
        self.assertEqual([word['text'] for word in words], ['你', '好。'])
        with self.assertRaisesRegex(RuntimeError, '45000001'):
            volcengine_tts.parse_stream([json.dumps({'code': 45000001, 'message': 'bad request'})])

    def test_gemini_request_and_pcm_response(self):
        body = gemini_tts.request_body('你好。', {'style': '沉稳的纪录片旁白'})
        self.assertEqual(body['response_format'], {'type': 'audio', 'mime_type': 'audio/l16', 'sample_rate': 24000})
        self.assertEqual(body['generation_config']['speech_config'], [{'voice': 'Iapetus'}])
        self.assertEqual(body['input'][0]['content'][0]['annotations'][0]['style'], '沉稳的纪录片旁白')
        pcm = (np.sin(np.arange(2400) / 10) * 8000).astype('<i2').tobytes()
        response = MagicMock(status_code=200)
        response.json.return_value = {'steps': [{'type': 'thinking'}, {'type': 'model_output', 'content': [{'type': 'audio', 'data': base64.b64encode(pcm).decode()}]}]}
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'secret'}, clear=True), patch('requests.post', return_value=response) as post:
            samples, rate = gemini_tts.synthesizer({})('你好。', 1)
        self.assertEqual(post.call_args.kwargs['headers']['x-goog-api-key'], 'secret')
        self.assertEqual((len(samples), rate), (2400, 24000))
        with patch.dict(os.environ, {}, clear=True), self.assertRaises(SystemExit):
            gemini_tts.synthesizer({})

    def test_voice_studio_sends_sampling_fields_per_chunk_and_reads_transcripts(self):
        from voice_studio import studio_synthesizer, studio_transcriber, SAMPLING
        with tempfile.TemporaryDirectory() as directory:
            wav = save(Path(directory) / 'speech.wav', speech_like([(1., .3)]))
            response = MagicMock(status_code=200, headers={'Content-Type': 'audio/wav'}, content=wav.read_bytes())
            with patch('requests.post', return_value=response) as post:
                samples, rate = studio_synthesizer('http://127.0.0.1:3900', {'ref_text': '参考。', 'max_chunk_chars': '0', **SAMPLING}, wav)('一段。', 7)
            fields = post.call_args.kwargs['data']
            self.assertEqual((fields['text'], fields['seed'], fields['temperature'], fields['top_k'], fields['max_chunk_chars']), ('一段。', '7', '0.9', '50', '0'))
            self.assertEqual((len(samples), rate), (len(speech_like([(1., .3)])), 48000))
            response = MagicMock(status_code=200)
            response.json.return_value = {'text': '你好世界', 'segments': [{'start': 0., 'end': 1., 'text': '你好世界',
                                          'words': [{'word': '你好', 'start': 0., 'end': .4}, {'word': '世界', 'start': .5, 'end': 1.}]}]}
            with patch('requests.post', return_value=response):
                words = studio_transcriber('http://127.0.0.1:3900', 'zh')(wav)
            self.assertEqual([word['text'] for word in words['words']], ['你好', '世界'])

    def test_mix_normalizes_linearly_without_changing_duration(self):
        from video_renderer import mix_audio
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'work').mkdir()
            save(root / 'work/narration.wav', .3 * speech_like([(2.5, .5)] * 4) + .01)
            mix_audio(root, {'duration': 12.})
            report = json.loads((root / 'work/audio-mix-report.json').read_text())
            self.assertEqual(report['loudnorm_mode'], 'linear')
            self.assertIn('highpass=f=70', report['narration_filter'])
            from audio_gate import decode, measure
            mixed = decode(root / 'work/mix.wav')
            self.assertEqual(len(mixed), len(decode(root / 'work/narration.wav')))
            self.assertLess(abs(measure(mixed)['dc_offset']), .001)


if __name__ == '__main__':
    unittest.main()

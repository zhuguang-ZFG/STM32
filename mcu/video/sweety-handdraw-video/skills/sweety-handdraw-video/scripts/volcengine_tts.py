#!/usr/bin/env python3
"""Optional cloud narration: Doubao TTS 2.0 through the Volcengine V3 HTTP chunked API, only with the user's key.

Docs: https://www.volcengine.com/docs/6561/1598757 (API) and https://www.volcengine.com/docs/6561/1257544
(voices). Auth: VOLC_TTS_API_KEY (new console) or VOLC_TTS_APP_ID + VOLC_TTS_ACCESS_KEY (old console).
One request per semantic chunk; enable_subtitle word timestamps feed the caption alignment and
aigc_metadata asks the service to label the audio. Live calls are untested here; tests mock HTTP.
"""
import argparse
import base64
import json
import os
from pathlib import Path
import tempfile
import uuid
from narration_master import build_master, SAMPLE_RATE

URL = 'https://openspeech.bytedance.com/api/v3/tts/unidirectional'
RESOURCE_ID = 'seed-tts-2.0'
SPEAKER = 'zh_male_cixingjieshuonan_uranus_bigtts'
FINISHED = 20000000


def headers(resource_id):
    if os.environ.get('VOLC_TTS_API_KEY'):
        auth = {'X-Api-Key': os.environ['VOLC_TTS_API_KEY']}
    elif os.environ.get('VOLC_TTS_APP_ID') and os.environ.get('VOLC_TTS_ACCESS_KEY'):
        auth = {'X-Api-App-Id': os.environ['VOLC_TTS_APP_ID'], 'X-Api-Access-Key': os.environ['VOLC_TTS_ACCESS_KEY']}
    else:
        raise SystemExit('Optional Volcengine TTS needs VOLC_TTS_API_KEY, or VOLC_TTS_APP_ID and VOLC_TTS_ACCESS_KEY; local VoxCPM2 stays the default')
    return {**auth, 'X-Api-Resource-Id': resource_id, 'X-Api-Request-Id': str(uuid.uuid4()), 'Content-Type': 'application/json'}


def request_body(text, options):
    additions = {'explicit_language': 'zh', 'aigc_metadata': {'enable': True, 'content_producer': options.get('content_producer', '')}}
    audio = {'format': 'mp3', 'sample_rate': SAMPLE_RATE, 'enable_subtitle': True, 'speech_rate': int(options.get('speech_rate', 0))}
    return {'user': {'uid': 'sweety-handdraw-video'},
            'req_params': {'text': text, 'speaker': options.get('speaker', SPEAKER), 'audio_params': audio,
                           'additions': json.dumps(additions, ensure_ascii=False)}}


def parse_stream(lines):
    """Audio lines carry base64 `data`; subtitle lines carry `sentence.words` (seconds from request start)."""
    audio, words = bytearray(), []
    for line in lines:
        if not line:
            continue
        data = json.loads(line)
        code = data.get('code', 0)
        if code == FINISHED:
            return bytes(audio), words
        if code:
            raise RuntimeError(f"Volcengine TTS error {code}: {data.get('message', '')}")
        if data.get('data'):
            audio += base64.b64decode(data['data'])
        if data.get('sentence'):
            words += [{'text': word['word'], 'start': word['startTime'], 'end': word['endTime']} for word in data['sentence'].get('words', [])]
    raise RuntimeError('Volcengine TTS stream ended without the completion code')


def synthesizer(options):
    import requests
    from audio_gate import decode
    resource = options.get('resource_id', RESOURCE_ID)

    def synthesize(text, seed):  # the service takes no seed; a retry is simply a new request
        with requests.post(URL, headers=headers(resource), json=request_body(text, options), stream=True, timeout=300) as response:
            if response.status_code != 200:
                raise RuntimeError(f"Volcengine TTS HTTP {response.status_code}, logid {response.headers.get('X-Tt-Logid')}")
            content, words = parse_stream(response.iter_lines(decode_unicode=True))
        with tempfile.NamedTemporaryFile(suffix='.mp3') as handle:
            handle.write(content)
            handle.flush()
            return decode(handle.name), SAMPLE_RATE, words
    return synthesize


def generate(job):
    root = Path(job).resolve()
    manifest = json.loads((root/'job.json').read_text())
    options = manifest.get('volcengine', {})
    identity = {'engine': 'volcengine-v3', 'resource_id': options.get('resource_id', RESOURCE_ID), 'speaker': options.get('speaker', SPEAKER),
                'speech_rate': int(options.get('speech_rate', 0)), 'aigc_metadata': True}
    target, alignment = build_master(root, manifest, synthesizer(options), identity, options)
    print('READY', target, alignment, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('job', type=Path)
    generate(parser.parse_args().job)

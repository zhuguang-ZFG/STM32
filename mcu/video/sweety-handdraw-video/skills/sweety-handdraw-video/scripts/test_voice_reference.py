"""Prevent derivative previews, dirty or changed files and unconsented voices from becoming references."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np

from import_voice import import_reference
from production_options import load_voices
from voice_studio import voice_reference, load_voice_catalog
from voxcpm_voice import resolved_options, enhancement_fingerprint, generation_kwargs
from test_audio_gate import speech_like, save

TEXT = '这是一段准确的原文，用来检查参考音频。'


class VoiceReferenceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.audio = save(self.root / 'source.wav', speech_like([(1., .4)] * 3 + [(1., .6)]))
        self.text = self.root / 'source.txt'
        self.text.write_text(TEXT)
        self.personal = patch('voice_studio.PERSONAL_CATALOG', self.root/'personal/catalog.json')
        self.personal.start()

    def tearDown(self):
        self.personal.stop()
        self.temporary.cleanup()

    def test_packaged_derivative_is_unavailable_for_exact_source_voice(self):
        profile = next(item for item in load_voices(self.root) if item['id'] == 'bilibili-outro')
        self.assertFalse(profile['available'])
        with self.assertRaisesRegex(ValueError, 'Import'):
            voice_reference({'voice': 'bilibili-outro'}, self.root)

    def test_source_import_can_be_used_and_audio_changes_are_rejected(self):
        import_reference(self.root, 'bilibili-outro', '原片女声', self.audio, self.text, 'source_recording')
        audio, text = voice_reference({'voice': 'bilibili-outro'}, self.root)
        self.assertEqual(text, TEXT)
        self.assertTrue(next(item for item in load_voices(self.root) if item['id'] == 'bilibili-outro')['available'])
        audio.write_bytes(b'replaced by generated preview')
        with self.assertRaisesRegex(ValueError, 'changed after import'):
            voice_reference({'voice': 'bilibili-outro'}, self.root)

    def test_synthetic_import_cannot_satisfy_an_original_reference(self):
        import_reference(self.root, 'bilibili-outro', '合成方向', self.audio, self.text, 'synthetic_direction')
        self.assertFalse(next(item for item in load_voices(self.root) if item['id'] == 'bilibili-outro')['available'])
        with self.assertRaisesRegex(ValueError, 'generated previews'):
            voice_reference({'voice': 'bilibili-outro'}, self.root)

    def test_transcript_changes_and_partial_transcripts_are_rejected(self):
        catalog = import_reference(self.root, 'magnetic-narrator', '磁性解说男声', self.audio, self.text)
        profile = json.loads(catalog.read_text())['voices'][0]
        Path(profile['reference_text']).write_text('不同的文本。')
        with self.assertRaisesRegex(ValueError, 'transcript changed'):
            voice_reference({'voice': 'magnetic-narrator'}, self.root)
        self.text.write_text('只有半句。')
        with self.assertRaisesRegex(ValueError, 'cover the whole clip'):
            import_reference(self.root/'other', 'magnetic-narrator', '磁性解说男声', self.audio, self.text)

    def test_dirty_reference_is_rejected_on_import(self):
        noisy = speech_like([(1., .4)] * 3 + [(1., .6)])
        dirty = save(self.root / 'dirty.wav', noisy + .02 * np.sin(2 * np.pi * 50 * np.arange(len(noisy)) / 48000))
        with self.assertRaisesRegex(ValueError, 'clean_reference.py'):
            import_reference(self.root, 'realistic-man', '逼真男声', dirty, self.text, 'source_recording')

    def test_custom_voices_need_consent_and_presets_keep_their_names(self):
        with self.assertRaisesRegex(ValueError, 'consent'):
            import_reference(self.root, 'my-voice', '我的声音', self.audio, self.text)
        import_reference(self.root, 'my-voice', '我的声音', self.audio, self.text, consent='self')
        catalog = json.loads((self.root/'options/local-voices.json').read_text())
        catalog['voices'] += [{'id': 'friendly-man', 'name': '旧男声'}, {'id': 'bilibili-outro', 'name': '旧女声名', 'requires_original_reference': False}]
        catalog['default'] = 'my-voice'
        (self.root/'options/local-voices.json').write_text(json.dumps(catalog))
        merged = load_voice_catalog(self.root)
        self.assertEqual([voice['name'] for voice in merged['voices']],
                         ['逼真男声', '逼真女声', '磁性解说男声', '儒雅青年', '温柔知性女声', '悬疑故事解说', '我的声音'])
        self.assertEqual(merged['default'], 'my-voice')
        self.assertEqual(voice_reference({}, self.root)[1], TEXT)
        with self.assertRaisesRegex(ValueError, 'Unknown voice'):
            voice_reference({'voice': 'friendly-man'}, self.root)
        self.assertTrue(next(voice for voice in merged['voices'] if voice['id'] == 'bilibili-outro')['requires_original_reference'])
        self.assertTrue(next(voice for voice in load_voices(self.root) if voice['id'] == 'my-voice')['available'])

    def test_both_film_voices_keep_preview_separate_from_source_reference(self):
        for identifier in ('realistic-man', 'bilibili-outro'):
            profile = next(voice for voice in load_voices(self.root) if voice['id'] == identifier)
            self.assertFalse(profile['available'])
            self.assertTrue(profile['preview_available'])
            import_reference(self.root, identifier, profile['name'], self.audio, self.text, 'source_recording')
            reference, _ = voice_reference({'voice': identifier}, self.root)
            self.assertNotEqual(str(reference), profile['audio_path'])
            self.assertTrue(next(voice for voice in load_voices(self.root) if voice['id'] == identifier)['available'])

    def test_public_default_is_a_bundled_synthetic_voice_and_personal_default_wins(self):
        self.assertEqual(load_voice_catalog(self.root)['default'], 'magnetic-narrator')
        reference, text = voice_reference({}, self.root)
        self.assertEqual(reference.name, 'magnetic-narrator.wav')
        self.assertTrue(text.startswith('很多人以为'))
        catalog = import_reference(self.root/'personal', 'bilibili-outro', '主力女声', self.audio, self.text, 'source_recording')
        personal = json.loads(catalog.read_text())
        personal['default'] = 'bilibili-outro'
        personal['voices'][0]['verified_generation_parameters'] = {'mode': 'combined', 'cfg_value': 1.5, 'timesteps': 24}
        (self.root/'personal/catalog.json').write_text(json.dumps(personal))
        reference, _ = voice_reference({}, self.root)
        self.assertEqual(reference, Path(personal['voices'][0]['reference_audio']))
        self.assertTrue(next(item for item in load_voices(self.root) if item['id'] == 'bilibili-outro')['preferred'])
        self.assertEqual(resolved_options({}, self.root)['cfg_value'], 1.5)
        self.assertEqual(resolved_options({'cfg_value': 1.7}, self.root)['cfg_value'], 1.7)

    def test_voxcpm_modes_follow_the_official_parameters(self):
        params = {'mode': 'combined', 'cfg_value': 2., 'timesteps': 10, 'style': '更慢一点', 'design': None}
        combined = generation_kwargs(params, '一句话。', 'ref.wav', '参考原文。')
        self.assertEqual((combined['ref_audio'], combined['prompt_audio'], combined['prompt_text']), ('ref.wav', 'ref.wav', '参考原文。'))
        self.assertNotIn('instruct', combined)
        self.assertEqual(combined['max_tokens'], 4 * 6 + 10)
        self.assertEqual(generation_kwargs({**params, 'mode': 'reference'}, '一句话。', 'ref.wav')['instruct'], '更慢一点')
        self.assertEqual(generation_kwargs({**params, 'mode': 'design', 'design': '中年男性'}, '一句话。')['instruct'], '中年男性')

    def test_cleanup_model_is_local_and_model_change_invalidates_cache(self):
        self.assertIsNone(enhancement_fingerprint(None))
        with self.assertRaisesRegex(ValueError, 'installed local model'):
            enhancement_fingerprint(self.root/'missing')
        directory = self.root/'cleanup-model'
        directory.mkdir()
        weights = directory/'model.safetensors'
        weights.write_bytes(b'first fixture')
        original = enhancement_fingerprint(directory)
        weights.write_bytes(b'changed fixture')
        self.assertNotEqual(original, enhancement_fingerprint(directory))


if __name__ == '__main__':
    unittest.main()

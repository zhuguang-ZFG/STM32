import hashlib
from pathlib import Path
import tempfile
import unittest
import wave
import numpy as np
import audio_contract
import music_bed
from video_job import save_wave


def write_stereo(path, seconds, frequency=440.):
    samples = (8000 * np.sin(np.arange(round(seconds * 48000)) * 2 * np.pi * frequency / 48000)).astype('<i2')
    with wave.open(str(path), 'wb') as stream:
        stream.setparams((2, 2, 48000, 0, 'NONE', 'not compressed'))
        stream.writeframes(np.repeat(samples[:, None], 2, axis=1).tobytes())


def read_wave(path):
    with wave.open(str(path), 'rb') as stream:
        return (stream.getframerate(), stream.getnchannels(),
                np.frombuffer(stream.readframes(stream.getnframes()), dtype='<i2').astype(float))


def rms(samples, start, end):
    return float(np.sqrt(np.mean((samples[round(start * 48000):round(end * 48000)]) ** 2)))


class MusicBedTests(unittest.TestCase):
    def test_looped_samples_have_exact_length_and_blended_seams(self):
        source = np.repeat(np.arange(12, dtype=np.float32)[:, None], 2, axis=1)
        looped = music_bed.loop_music(source, 27, 4)
        self.assertEqual(looped.shape, (27, 2))
        self.assertTrue(np.isfinite(looped).all())
        self.assertTrue(np.all(looped[8:12, 0] < source[8:12, 0]))
        np.testing.assert_array_equal(looped[12:16], source[4:8])
        np.testing.assert_array_equal(music_bed.loop_music(source, 5, 4), source[:5])

    def prepare(self, directory, music, source_seconds=3.):
        root = Path(directory)
        work = root / 'work'
        work.mkdir(exist_ok=True)
        narration = np.zeros(6 * 48000, np.int16)
        narration[2 * 48000:4 * 48000] = (4000 * np.sin(np.arange(2 * 48000) * 2 * np.pi * 180 / 48000)).astype(np.int16)
        save_wave(work / 'narration.wav', narration)
        write_stereo(root / 'music.wav', source_seconds)
        return music_bed.prepare(root, work, {'source': 'music.wav', **music})

    def test_bed_matches_narration_and_ducks_under_speech(self):
        with tempfile.TemporaryDirectory() as directory:
            bed, report = self.prepare(directory, {})
            rate, channels, interleaved = read_wave(bed)
            self.assertEqual((rate, channels), (48000, 2))
            samples = interleaved.reshape(-1, 2)
            self.assertEqual(len(samples), 6 * 48000)
            # A 3 s source loops with a 1 s clamped crossfade to cover the 6 s film; the duck holds the
            # music down while the sentence plays (2-4 s) and recovers between sentences.
            self.assertLessEqual(report['crossfade_seconds'], 1.)
            self.assertLess(rms(samples, 3.15, 3.85), .85 * rms(samples, 1.35, 1.95))
            self.assertTrue(report['duck'])
            self.assertEqual(report['dips'], [])

    def test_dips_lower_a_named_window(self):
        with tempfile.TemporaryDirectory() as directory:
            bed, _ = self.prepare(directory, {'dips': [[2.2, 2.7]]})
            _, _, interleaved = read_wave(bed)
            samples = interleaved.reshape(-1, 2)
            self.assertLess(rms(samples, 2.35, 2.55), .25 * rms(samples, 1.35, 1.95))

    def test_resolution_prepares_a_bed_and_keeps_host_prepared_beds(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'work').mkdir()
            save_wave(root / 'work/narration.wav', np.zeros(3 * 48000, np.int16))
            write_stereo(root / 'music.wav', 2.)
            manifest = {'audio': {'music': {'source': 'music.wav', 'user_instruction': '加一段配乐', 'gain': .12}}}
            policy = audio_contract.resolve_audio_layers(root, manifest)
            layer = policy['layers'][0]
            self.assertEqual(Path(layer['source']).name, 'music-bed.wav')
            self.assertTrue(layer['preparation']['duck'])
            self.assertTrue(policy['background_music'])
            ready = {'audio': {'music': {'source': 'music.wav', 'user_instruction': '加一段配乐', 'prepared': True}}}
            resolved = audio_contract.resolve_audio_layers(root, ready)['layers'][0]
            self.assertEqual(Path(resolved['source']), (root / 'music.wav').resolve())

    def test_music_still_needs_the_user_instruction(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'work').mkdir()
            with self.assertRaises(ValueError):
                audio_contract.resolve_audio_layers(root, {'audio': {'music': {'source': 'music.wav'}}})


if __name__ == '__main__':
    unittest.main()

"""Procedural foley, builtin music beds and the layered-mix audio gate."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import wave
import numpy as np
from scipy import signal
import foley
import music_synth
from audio_contract import resolve_audio_layers
from audio_gate import measure_layered_mix, read_pcm, SAMPLE_RATE, MIN_VOICE_MARGIN_DB
from test_audio_gate import speech_like
from video_job import save_wave

RATE = SAMPLE_RATE


def line(start, end, count=40):
    points = np.linspace(start, end, count)
    lengths = np.r_[0., np.cumsum(np.linalg.norm(np.diff(points, axis=0), axis=1))]
    return points.tolist(), lengths.tolist()


def zigzag(width=180, rows=6, height=60):
    points = []
    for row in range(rows):
        y = 10 + row * height / rows
        points += [[10, y], [10 + width, y + 4]] if row % 2 == 0 else [[10 + width, y], [10, y + 4]]
    points = np.array(points, float)
    lengths = np.r_[0., np.cumsum(np.linalg.norm(np.diff(points, axis=0), axis=1))]
    return points.tolist(), lengths.tolist()


def drawing_asset(kind='illustration'):
    """ink 0-0.3, pen lifted 0.3-0.6, ink 0.6-1.0."""
    first, first_lengths = line((10, 20), (210, 60))
    second, second_lengths = line((210, 60), (20, 120))
    return {'type': kind, 'width': 240, 'height': 160, 'segments': [
        {'kind': 'ink', 'start': 0., 'end': .3, 'points': first, 'lengths': first_lengths, 'profile': 'minjerk'},
        {'kind': 'travel', 'start': .3, 'end': .6, 'points': [first[-1], second[0]]},
        {'kind': 'ink', 'start': .6, 'end': 1., 'points': second, 'lengths': second_lengths, 'profile': 'minjerk'}]}


def coloring_asset():
    points, lengths = zigzag()
    return {'type': 'illustration', 'width': 240, 'height': 160, 'segments': [
        {'kind': 'color', 'start': 0., 'end': 1., 'points': points, 'lengths': lengths, 'radius': 14.}]}


def timeline_with(events, assets, duration=8.):
    return {'duration': duration, 'canvas': {'width': 960, 'height': 540, 'fps': 30}, 'hand': {'preset': 'navy'},
            'pages': [{'index': 0, 'events': [{'caption': False, **event} for event in events]}], 'assets': assets,
            'audio_policy': {'background_music': False, 'layers': []}}


def basic_timeline(x=360, duration=8.):
    return timeline_with([{'asset': 'drawing', 'x': x, 'y': 100, 'start': 1., 'end': 2.},
                          {'asset': 'fill', 'x': x, 'y': 100, 'start': 3., 'end': 4.2}],
                         {'drawing': drawing_asset(), 'fill': coloring_asset()}, duration)


def rms(samples):
    return float(np.sqrt(np.mean(np.asarray(samples, dtype=np.float64) ** 2)))


def window(stereo, start, end):
    return stereo[round(start * RATE):round(end * RATE)]


def centroid(samples):
    frequencies, power = signal.welch(np.asarray(samples, dtype=np.float64), RATE, nperseg=4096)
    return float((frequencies * power).sum() / power.sum())


def write_stereo(path, stereo):
    data = np.rint(np.clip(stereo, -1, 32767 / 32768) * 32768).astype('<i2')
    with wave.open(str(path), 'wb') as stream:
        stream.setparams((2, 2, RATE, 0, 'NONE', 'not compressed'))
        stream.writeframes(data.tobytes())
    return Path(path)


def layer(path, gain, kind):
    return {'source': str(path), 'gain': gain, 'start': 0., 'kind': kind, 'sha256': hashlib.sha256(Path(path).read_bytes()).hexdigest()}


class FoleyTests(unittest.TestCase):
    def test_same_timeline_gives_identical_foley(self):
        options = foley.parse_options({'scope': 'all'})
        first, report = foley.synthesize(basic_timeline(), options)
        second, _ = foley.synthesize(basic_timeline(), options)
        np.testing.assert_array_equal(first, second)
        self.assertEqual(report['segments'], {'ink': 2, 'color': 1})
        other, _ = foley.synthesize(basic_timeline(), foley.parse_options({'seed': 7, 'scope': 'all'}))
        self.assertFalse(np.array_equal(first, other))
        with tempfile.TemporaryDirectory() as one, tempfile.TemporaryDirectory() as two:
            self.assertEqual(foley.build_layer(one, basic_timeline(), {'scope': 'all'})['sha256'], foley.build_layer(two, basic_timeline(), {'scope': 'all'})['sha256'])

    def test_pen_lifts_and_idle_time_are_silent(self):
        stereo, _ = foley.synthesize(basic_timeline(), foley.parse_options({'scope': 'all'}))
        stroke = rms(window(stereo, 1.05, 1.28))
        self.assertGreater(stroke, 1e-4)
        # Travel 1.3-1.6 s: after a ~40 ms release the pen is off the paper until the next stroke's attack.
        self.assertLess(rms(window(stereo, 1.345, 1.595)), stroke * 10 ** (-50 / 20))
        self.assertEqual(np.abs(window(stereo, 0, .99)).max(), 0)
        self.assertEqual(np.abs(window(stereo, 2.1, 2.99)).max(), 0)
        self.assertEqual(np.abs(window(stereo, 4.3, 8)).max(), 0)

    def test_levels_stay_low_and_follow_gain(self):
        stereo, _ = foley.synthesize(basic_timeline(), foley.parse_options({'scope': 'all'}))
        active = stereo[np.abs(stereo).max(axis=1) > 1e-5]
        level = 20 * np.log10(rms(active))
        self.assertTrue(-48 < level < -32, level)
        self.assertLessEqual(20 * np.log10(np.abs(stereo).max()), foley.CEILING_DBFS + .01)
        quieter, _ = foley.synthesize(basic_timeline(), foley.parse_options({'gain_db': -6, 'scope': 'all'}))
        self.assertAlmostEqual(20 * np.log10(rms(quieter[np.abs(stereo).max(axis=1) > 1e-5])) - level, -6, delta=.3)

    def test_marker_rub_is_darker_than_the_nib_and_handwriting_is_distinct(self):
        stereo, _ = foley.synthesize(basic_timeline(), foley.parse_options({'stereo': False, 'scope': 'all'}))
        ink, rub = window(stereo, 1.02, 1.6)[:, 0], window(stereo, 3.05, 4.15)[:, 0]
        self.assertLess(centroid(rub), .8 * centroid(ink))
        written = timeline_with([{'asset': 'text', 'x': 360, 'y': 100, 'start': 1., 'end': 2.}],
                                {'text': drawing_asset('handwritten_text')})
        text, _ = foley.synthesize(written, foley.parse_options({'stereo': False, 'scope': 'all'}))
        self.assertGreater(rms(window(text, 1.02, 1.6)[:, 0]), 0)  # a softer whisper than the drawing nib since v1.5 feedback

    def test_by_default_only_handwriting_makes_a_sound(self):
        # Users found a constant scratch under the voice tiring: drawing and coloring stay silent unless scope is "all".
        silent, report = foley.synthesize(basic_timeline(), foley.parse_options(None))
        self.assertEqual((report['scope'], report['events'], float(np.abs(silent).max())), ('writing', 0, 0.))
        written = timeline_with([{'asset': 'text', 'x': 360, 'y': 100, 'start': 1., 'end': 2.}],
                                {'text': drawing_asset('handwritten_text')})
        text, report = foley.synthesize(written, foley.parse_options(None))
        self.assertEqual(report['events'], 1)
        self.assertGreater(float(np.abs(text).max()), 0.)
        with self.assertRaisesRegex(ValueError, 'scope'):
            foley.parse_options({'scope': 'drawing'})

    def test_pan_follows_the_nib_and_can_be_disabled(self):
        left, _ = foley.synthesize(basic_timeline(x=0), foley.parse_options({'scope': 'all'}))
        right, _ = foley.synthesize(basic_timeline(x=700), foley.parse_options({'scope': 'all'}))
        self.assertGreater(rms(left[:, 0]), 1.3 * rms(left[:, 1]))
        self.assertGreater(rms(right[:, 1]), 1.3 * rms(right[:, 0]))
        mono, _ = foley.synthesize(basic_timeline(x=0), foley.parse_options({'stereo': False, 'scope': 'all'}))
        np.testing.assert_array_equal(mono[:, 0], mono[:, 1])

    def test_speech_ducks_the_foley(self):
        events = [{'asset': 'drawing', 'x': 360, 'y': 100, 'start': 1., 'end': 2.},
                  {'asset': 'drawing', 'x': 360, 'y': 100, 'start': 5., 'end': 6.}]
        timeline = timeline_with(events, {'drawing': drawing_asset()})
        narration = np.zeros(8 * RATE)
        narration[4 * RATE:7 * RATE] = speech_like([(3., 0.)], seed=4)[:3 * RATE]
        plain, _ = foley.synthesize(timeline, foley.parse_options({'duck_db': 6, 'scope': 'all'}))
        ducked, _ = foley.synthesize(timeline, foley.parse_options({'duck_db': 6, 'scope': 'all'}), narration)
        quiet = 20 * np.log10(rms(window(ducked, 1, 2)) / rms(window(plain, 1, 2)))
        speech = 20 * np.log10(rms(window(ducked, 5, 6)) / rms(window(plain, 5, 6)))
        self.assertGreater(quiet, -.5)
        self.assertAlmostEqual(speech, -6, delta=1.)

    def test_options_and_attach(self):
        self.assertIsNone(foley.parse_options(False))
        self.assertIsNone(foley.parse_options({'enabled': False}))
        self.assertEqual(foley.parse_options(True)['duck_db'], foley.DUCK_DB)
        for bad in ({'gain': 1}, {'gain_db': 20}, {'duck_db': -1}, {'tool': 'chalk'}, {'seed': 'x'}, 'loud'):
            with self.assertRaises(ValueError):
                foley.parse_options(bad)
        with self.assertRaises(ValueError):
            resolve_audio_layers('.', {'audio': {'foley': {'gain_db': 40}}})
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'work').mkdir()
            self.assertIsNone(foley.attach(root, basic_timeline(), {'audio': {'foley': False}}))
            timeline = basic_timeline()
            first = foley.attach(root, timeline, {'audio': {'foley': {'scope': 'all'}}})
            foley.attach(root, timeline, {'audio': {'foley': {'gain_db': -3, 'scope': 'all'}}})
            layers = timeline['audio_policy']['layers']
            self.assertEqual([entry['kind'] for entry in layers], ['foley'])
            self.assertEqual(layers[0]['foley']['gain_db'], -3)
            self.assertTrue(0 < first['gain'] <= .3 and Path(first['source']).is_file())
            self.assertEqual(first['foley']['tool'], 'marker')
            self.assertIsNone(foley.attach(root, timeline_with([], {}), {}))


class MusicSynthTests(unittest.TestCase):
    def test_each_mood_is_deterministic_soft_and_unclipped(self):
        for mood in music_synth.MOODS:
            first, record = music_synth.render(mood, 6., seed=1)
            second, _ = music_synth.render(mood, 6., seed=1)
            np.testing.assert_array_equal(first, second)
            self.assertEqual(first.shape, (6 * RATE, 2))
            self.assertTrue(np.isfinite(first).all())
            self.assertLessEqual(20 * np.log10(np.abs(first).max()), music_synth.CEILING_DBFS + .01)
            self.assertAlmostEqual(record['loudness_lufs'], music_synth.TARGET_LUFS, delta=.6)
            frequencies, power = signal.welch(first.mean(axis=1).astype(np.float64), RATE, nperseg=8192)
            self.assertLess(power[frequencies > 8000].sum() / power.sum(), 1e-3, mood)  # no harsh highs
            self.assertLess(np.abs(first.mean(axis=0)).max(), 1e-3)
        other, _ = music_synth.render('calm', 6., seed=2)
        self.assertFalse(np.array_equal(music_synth.render('calm', 6., seed=1)[0], other))

    def test_loop_render_is_whole_bars_and_seamless(self):
        for mood in ('warm', 'tense'):
            bed, record = music_synth.render(mood, 10., seed=3, loop=True)
            bar = 4 * 60 / music_synth.MOODS[mood]['bpm']
            self.assertEqual(len(bed), round(record['bars'] * bar * RATE))
            steps = np.abs(np.diff(bed.astype(np.float64), axis=0)).max(axis=1)
            seam = np.abs(bed[0].astype(np.float64) - bed[-1]).max()
            self.assertLess(seam, np.percentile(steps, 99.9))
            around = np.concatenate([bed[-RATE // 10:], bed[:RATE // 10]])
            self.assertLess(abs(20 * np.log10(rms(around[:RATE // 10]) / rms(around[RATE // 10:]))), 6)

    def test_builtin_source_goes_through_the_music_bed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'work').mkdir()
            save_wave(root / 'work/narration.wav', (12000 * speech_like([(2.5, .5)] * 2, seed=5)).astype(np.int16))
            music = {'source': 'builtin:warm', 'user_instruction': '加一段轻松的配乐', 'seed': 4}
            policy = resolve_audio_layers(root, {'audio': {'music': music}})
            entry = policy['layers'][0]
            self.assertEqual(Path(entry['source']).name, 'music-bed.wav')
            self.assertEqual((entry['builtin']['mood'], entry['builtin']['seed']), ('warm', 4))
            self.assertEqual(entry['gain'], music_synth.DEFAULT_GAIN)
            self.assertTrue(entry['preparation']['duck'])
            self.assertIn('builtin:warm', policy['delivery_notice'])
            self.assertIsNotNone(entry['levels']['loudness_lufs'])
            for bad in ({**music, 'prepared': True}, {**music, 'source': 'builtin:epic'}, {'source': 'builtin:calm'}):
                with self.assertRaises(ValueError):
                    resolve_audio_layers(root, {'audio': {'music': bad}})


class LayeredGateTests(unittest.TestCase):
    def mixed(self, root, layers):
        from video_renderer import mix_audio
        mix_audio(root, {'audio_policy': {'layers': layers}})
        return read_pcm(root / 'work/normalized-narration.wav'), read_pcm(root / 'work/mix.wav')

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        (self.root / 'work').mkdir()
        self.voice = speech_like([(2.5, .5)] * 4, seed=6)
        save_wave(self.root / 'work/narration.wav', (32767 * .8 * self.voice / np.abs(self.voice).max()).astype(np.int16))
        self.timeline = basic_timeline(duration=len(self.voice) / RATE)
        self.foley = foley.build_layer(self.root / 'work', self.timeline, {'scope': 'all'})
        bed, _ = music_synth.render('calm', len(self.voice) / RATE, seed=0)
        self.music = layer(write_stereo(self.root / 'bed.wav', bed), .25, 'music')

    def tearDown(self):
        self.directory.cleanup()

    def test_intended_foley_and_music_pass_with_the_narration_intact(self):
        narration, mix = self.mixed(self.root, [self.music, self.foley])
        report = measure_layered_mix(narration, mix, [self.music, self.foley])
        self.assertEqual(report['status'], 'PASS', report['failures'])
        self.assertLess(report['mix']['narration_residual_db'], -60)
        self.assertGreater(report['mix']['narration_correlation'], .9999)
        self.assertEqual([entry['kind'] for entry in report['layers']], ['music', 'foley'])
        self.assertGreater(report['mix']['voice_margin_db'], MIN_VOICE_MARGIN_DB)
        from video_verifier import verify_film_audio
        cues = [{'text': f'第{index}句', 'start': 3. * index, 'end': 3. * index + 2.5} for index in range(4)]
        checked = verify_film_audio(self.root / 'work', {'cues': cues}, None, {'layers': [self.music, self.foley]})
        self.assertEqual((checked['audio_gate']['status'], checked['caption_sync']['status']), ('PASS', 'PASS'))

    def test_broken_narration_hum_clipping_and_masking_fail(self):
        narration, mix = self.mixed(self.root, [self.foley])
        broken = mix.copy()
        broken[RATE:2 * RATE] = 0  # a second of the voice missing from the film track
        self.assertTrue(any('not intact' in failure for failure in measure_layered_mix(narration, broken, [self.foley])['failures']))
        quieter = mix - .5 * narration[:, None]  # voice at the wrong gain
        self.assertEqual(measure_layered_mix(narration, quieter, [self.foley])['status'], 'FAIL')
        clipped = np.clip(mix * 6, -1, 1)
        self.assertTrue(any('clips' in failure for failure in measure_layered_mix(narration, clipped, [self.foley])['failures']))
        time = np.arange(len(self.voice)) / RATE
        hum = write_stereo(self.root / 'hum.wav', np.repeat((.05 * np.sin(2 * np.pi * 60 * time))[:, None], 2, axis=1))
        humming = layer(hum, .3, 'foley')
        narration, mix = self.mixed(self.root, [self.foley, humming])
        report = measure_layered_mix(narration, mix, [self.foley, humming])
        self.assertTrue(any('outside the music' in failure for failure in report['failures']), report['failures'])
        # The same sustained tone is accepted as music (tonal by design) but not when it buries the voice.
        tonal = layer(hum, .3, 'music')
        narration, mix = self.mixed(self.root, [tonal])
        self.assertEqual(measure_layered_mix(narration, mix, [tonal])['status'], 'PASS')
        loud = layer(write_stereo(self.root / 'loud.wav', .9 * np.sign(np.sin(2 * np.pi * 3 * time))[:, None] *
                                  np.repeat(np.random.default_rng(1).standard_normal((len(time), 1)) * .5, 2, axis=1)), .3, 'music')
        narration, mix = self.mixed(self.root, [loud])
        self.assertTrue(any('mask the voice' in failure for failure in measure_layered_mix(narration, mix, [loud])['failures']))

    def test_noisy_narration_stem_still_fails_under_layers(self):
        noisy = self.voice + .01 * np.random.default_rng(2).standard_normal(len(self.voice))
        save_wave(self.root / 'work/narration.wav', (32767 * .8 * noisy / np.abs(noisy).max()).astype(np.int16))
        narration, mix = self.mixed(self.root, [self.music, self.foley])
        report = measure_layered_mix(narration, mix, [self.music, self.foley])
        self.assertTrue(any(failure.startswith('narration stem: pauses not quiet') for failure in report['failures']), report['failures'])


if __name__ == '__main__':
    unittest.main()

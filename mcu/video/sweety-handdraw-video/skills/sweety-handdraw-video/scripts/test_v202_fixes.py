"""2.0.2: the pen never writes outside the camera view, and narration chunks end cleanly (no hard cut, no sound the
voice model added after the sentence)."""
import math
import unittest

import numpy as np

import framing
import narration_master

RATE = narration_master.SAMPLE_RATE


def voiced(seconds, level=.5, frequency=180.):
    """A speech-like sound: a tone under a syllable-rate envelope that rises and decays."""
    t = np.arange(round(seconds * RATE)) / RATE
    envelope = np.clip(np.sin(np.pi * t / seconds), 0, 1) ** .5 * (.6 + .4 * np.sin(2 * np.pi * 4 * t) ** 2)
    return level * envelope * np.sin(2 * np.pi * frequency * t)


def level_db(samples, peak):
    return 20 * math.log10(max(float(np.sqrt(np.mean(samples ** 2))), 1e-12) / peak)


class NarrationTailTests(unittest.TestCase):
    def test_a_sound_after_the_sentence_is_dropped_and_the_end_fades_to_silence(self):
        speech, gap, burst = voiced(1.2), np.zeros(round(.15 * RATE)), voiced(.25, .45, 260.)
        chunk = np.concatenate([speech, gap, burst])
        cleaned, report = narration_master.clean_edges(chunk, [{'text': '么', 'start': .9, 'end': 1.15}])
        self.assertEqual(report['status'], 'artifact_dropped')
        self.assertLess(len(cleaned) / RATE, 1.2 + .15)                       # the burst is gone
        self.assertGreater(len(cleaned) / RATE, 1.15)                         # the sentence itself is kept
        self.assertLess(level_db(cleaned[-round(.01 * RATE):], .5), -60)       # no edge lands on a sound

    def test_a_breath_cut_hard_gets_a_fade(self):
        speech = voiced(1.)
        breath = .006 * np.random.default_rng(1).standard_normal(round(.08 * RATE))
        cleaned, report = narration_master.clean_edges(np.concatenate([speech, breath]), [{'text': '你', 'start': .8, 'end': .98}])
        self.assertEqual(report['status'], 'clean')
        self.assertLess(level_db(cleaned[-round(.01 * RATE):], .5), -60)

    def test_a_chunk_that_ends_mid_word_is_reported_cut_off(self):
        t = np.arange(round(1. * RATE)) / RATE
        loud_to_the_end = .5 * np.sin(2 * np.pi * 180 * t)
        cleaned, report = narration_master.clean_edges(loud_to_the_end, [{'text': '后', 'start': .7, 'end': 1.}])
        self.assertIsNone(cleaned)
        self.assertEqual(report['status'], 'cut_off')


def timeline(camera, events, width=400, height=600, overlays=()):
    caption = {'asset': 'cap', 'x': 40, 'y': 500, 'start': 0., 'end': 10., 'hide': 10., 'caption': True, 'z': 90}
    return {'canvas': {'width': width, 'height': height, 'fps': 30}, 'cover_seconds': 1.,
            'pages': [{'index': 0, 'start': 0., 'end': 10., 'beats': [{'id': 'b1', 'start': 0., 'end': 9.}], 'camera': camera,
                       'events': events + [caption], 'overlays': list(overlays)}],
            'assets': {'word': {'width': 80, 'height': 40, 'segments': []}, 'cap': {'width': 300, 'height': 40, 'segments': []}}}


def word(x, y, start, end):
    return {'asset': 'word', 'x': x, 'y': y, 'start': start, 'end': end, 'hide': 10., 'caption': False, 'z': 30, 'role': 'text'}


def box(x, y, start, end):
    return {'recipe': 'rough_annotate', 'space': 'board', 'x': x, 'y': y, 'width': 90, 'height': 50, 'scale': 1., 'start': start, 'end': end, 'z': 60}


class FramingTests(unittest.TestCase):
    def test_a_word_written_outside_a_push_in_gets_a_framing_move(self):
        line = timeline([{'at': 0, 'center': [100, 200], 'zoom': 2.}], [word(300, 380, 3., 4.)])
        renderer = framing.renderer_for(line)
        self.assertTrue(framing.check_page(renderer, 0))                       # the camera holds the left; the word is on the right
        report = framing.keep_drawing_in_view(line)
        self.assertEqual(report['unfixable'], [])
        self.assertEqual(len(report['adjustments']), 1)
        key = next(item for item in line['pages'][0]['camera'] if item.get('auto') == 'framing')
        self.assertLessEqual(key['at'], 3.)
        self.assertEqual(framing.check_page(framing.renderer_for(line), 0), [])

    def test_one_framing_move_serves_a_run_of_labels(self):
        line = timeline([{'at': 0, 'center': [100, 150], 'zoom': 2.}], [word(300, 300, 3., 4.), word(220, 400, 4.5, 5.5)])
        report = framing.keep_drawing_in_view(line)
        self.assertEqual(report['unfixable'], [])
        self.assertEqual(len([key for key in line['pages'][0]['camera'] if key.get('auto') == 'framing']), 1)

    def test_a_designed_move_waits_for_the_pen(self):
        camera = [{'at': 0, 'center': [200, 250], 'zoom': 1.5}, {'at': 3.5, 'move': 'cut', 'center': [80, 120], 'zoom': 2.5},
                  {'at': 6., 'move': 'pull_out', 'center': [200, 300], 'zoom': 1.}]
        line = timeline(camera, [word(160, 230, 3., 5.)])
        report = framing.keep_drawing_in_view(line)
        self.assertEqual(report['unfixable'], [])
        keys = line['pages'][0]['camera']
        self.assertTrue(report['adjustments'][0].get('moves_waited_seconds'))
        self.assertGreaterEqual(keys[1]['at'], 5.)                              # the cut now comes after the word is written
        self.assertEqual(keys[2]['at'], 6.)                                     # a later move keeps its cue when there is room
        self.assertEqual(framing.check_page(framing.renderer_for(line), 0), [])

    def test_the_opening_frame_stays_and_only_the_move_during_the_drawing_waits(self):
        camera = [{'at': 0, 'move': 'cut', 'center': [100, 200], 'zoom': 2.}, {'at': 1., 'move': 'hop', 'center': [300, 200], 'zoom': 2.},
                  {'at': 4., 'move': 'pull_out', 'center': [200, 300], 'zoom': 1.}]
        line = timeline(camera, [word(40, 150, .3, 3.)])                                         # written on the left while the hop leaves it
        report = framing.keep_drawing_in_view(line)
        keys = line['pages'][0]['camera']
        self.assertEqual(report['unfixable'], [])
        self.assertEqual(keys[0]['at'], 0)
        self.assertGreaterEqual(keys[1]['at'], 3.)
        self.assertGreaterEqual(keys[2]['at'] - keys[1]['at'], framing.move_seconds(keys[1]))    # the pull-out follows once the hop has landed

    def test_moves_pushed_past_the_page_end_are_dropped_but_the_last_is_kept(self):
        camera = [{'at': 0, 'center': [100, 200], 'zoom': 2.}, {'at': 2., 'move': 'hop', 'center': [300, 200], 'zoom': 2.},
                  {'at': 8.5, 'move': 'pan', 'center': [300, 400], 'zoom': 2.}, {'at': 9.2, 'move': 'pull_out', 'center': [200, 300], 'zoom': 1.}]
        line = timeline(camera, [word(40, 150, 1., 9.)])                                         # the hop has to wait until 9.1 s
        framing.keep_drawing_in_view(line)
        keys = line['pages'][0]['camera']
        self.assertEqual([key.get('move') for key in keys], [None, 'pull_out'])
        self.assertLessEqual(keys[-1]['at'], 9.7)

    def test_the_page_edge_is_in_view_when_the_camera_cannot_go_further(self):
        line = timeline([{'at': 0, 'center': [200, 300], 'zoom': 1.}], [word(316, 30, 3., 4.)])   # 4px from the right edge, 30px from the top
        report = framing.keep_drawing_in_view(line)
        self.assertEqual(report, {'adjustments': [], 'unfixable': []})
        self.assertEqual(len(line['pages'][0]['camera']), 1)

    def test_what_no_camera_can_show_is_reported_once_and_the_design_kept(self):
        camera = [{'at': 0, 'center': [200, 450], 'zoom': 2.}]                                     # already as close as a camera gets
        line = timeline([dict(key) for key in camera], [word(160, 560, 3., 4.)])                 # under the caption band at any zoom
        report = framing.keep_drawing_in_view(line)
        self.assertEqual(report['adjustments'], [])
        self.assertEqual(len(report['unfixable']), 1)
        self.assertEqual(line['pages'][0]['camera'], camera)

    def test_a_box_marked_outside_the_view_gets_a_framing_move(self):
        line = timeline([{'at': 0, 'center': [100, 150], 'zoom': 2.}], [], overlays=[box(280, 330, 3., 4.)])
        report = framing.keep_drawing_in_view(line)
        self.assertEqual(report['unfixable'], [])
        self.assertEqual(report['adjustments'][0]['role'], 'overlay')
        self.assertEqual(framing.check_page(framing.renderer_for(line), 0), [])

    def test_a_box_arriving_while_the_pen_works_elsewhere_gets_a_view_that_holds_both(self):
        line = timeline([{'at': 0, 'center': [100, 150], 'zoom': 2.}], [word(20, 40, .5, 6.)], overlays=[box(290, 400, 3., 4.)])
        report = framing.keep_drawing_in_view(line)                                             # centring on the box would lose the word
        self.assertEqual(report['unfixable'], [])
        self.assertEqual(report['adjustments'][0]['framing'], 'widen')
        self.assertEqual(framing.page_score(line, 0), (0., 0.))

    def test_titles_in_the_same_spot_take_turns(self):
        from video_job import take_turns
        page = {'start': 0., 'end': 10.}
        first = {'x': 77, 'y': 150, 'width': 1126, 'height': 170, 'start': 1., 'end': 2.4, 'exit': {'style': 'fade', 'start': 5., 'end': 5.35}}
        second = {'x': 77, 'y': 150, 'width': 1126, 'height': 170, 'start': 5., 'end': 6.6}
        third = {'x': 77, 'y': 150, 'width': 1126, 'height': 170, 'start': 8., 'end': 9.}
        take_turns([third, second, first], page)
        self.assertLessEqual(first['exit']['end'], second['start'])
        self.assertLessEqual(second['exit']['end'], third['start'])                             # a title with no exit leaves for the next
        self.assertNotIn('exit', third)

    def test_inserted_keys_pass_the_camera_contract(self):
        from timeline_contract import validate_page_motion
        line = timeline([{'at': 0, 'center': [100, 200], 'zoom': 2.}], [word(300, 380, 3., 4.)])
        framing.keep_drawing_in_view(line)
        self.assertTrue(validate_page_motion(line['pages'][0], line['canvas'], first=True))
        with self.assertRaises(ValueError):
            validate_page_motion({**line['pages'][0], 'camera': [{'at': 0, 'auto': 'anything'}]}, line['canvas'], first=True)


if __name__ == '__main__':
    unittest.main()

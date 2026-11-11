"""Pen arcs, wrist turn, page camera and transitions on a tiny synthetic timeline."""
import unittest
import numpy as np
from PIL import Image, ImageDraw
from timeline_contract import validate_page_motion
from video_renderer import Renderer, MAX_TILT, PEN_SHADOW_SLOPE, SHADOW_DIRECTION


def renderer(camera=None, transition=None, points=((0., 0.), (200., 0.)), x=100):
    hand = Image.new('RGBA', (120, 260))
    ImageDraw.Draw(hand).polygon([(6, 6), (14, 6), (110, 259), (80, 259)], fill=(90, 70, 60, 255))  # arm cut only at the bottom
    length = float(np.linalg.norm(np.subtract(points[1], points[0])))
    stroke = {'kind': 'ink', 'start': 0., 'end': 1., 'points': [list(point) for point in points], 'lengths': [0., length], 'profile': 'minjerk'}
    caption = Image.new('RGBA', (60, 20), (10, 20, 30, 255))
    events = lambda start: [{'asset': 'line', 'x': x, 'y': 120, 'z': 30, 'caption': False, 'start': start, 'end': start + 1., 'hide': 99.},
                            {'asset': 'caption', 'x': 290, 'y': 300, 'z': 91, 'caption': True, 'start': start - .5, 'end': start + 2, 'hide': start + 2}]
    r = Renderer.__new__(Renderer)
    r.width, r.height, r.fps, r.paper = 640, 360, 30, (250, 249, 241, 255)
    r.hand, r.nib = hand, np.array([8., 9.])
    r.artwork = {'caption': caption, 'line': Image.new('RGBA', (604, 4), (40, 40, 40, 255))}
    r.pixels = {'line': np.zeros((4, 604, 4), np.uint8)}
    r.maps = {'line': {'reveal': np.zeros((4, 604), np.float32)}}
    r.timeline = {'cover_seconds': 1., 'assets': {'line': {'segments': [stroke]}}, 'pages': [
        {'index': 0, 'start': 1., 'end': 4., 'beats': [{'id': 'a', 'start': 1.5}], 'events': events(1.6), 'last_drawing_end': 2.6, 'camera': camera},
        {'index': 1, 'start': 4., 'end': 7., 'beats': [{'id': 'b', 'start': 4.}], 'events': events(4.8), 'last_drawing_end': 5.8, 'transition': transition}]}
    r.starts = [1., 4.]
    return r


class RenderMotionTests(unittest.TestCase):
    def test_pen_enters_and_leaves_on_smooth_arcs(self):
        r = renderer()
        self.assertIsNone(r.pen_state(1.))
        path = [r.pen_state(1.6 - .45 + index / 30) for index in range(int(.45 * 30) + 1)]
        self.assertGreater(path[0][0][1], r.height + 40)  # starts fully below the frame
        points = np.array([state[0] for state in path])
        steps = np.linalg.norm(np.diff(points, axis=0), axis=1)
        self.assertLess(steps.max(), 160)
        self.assertLess(steps[-1], steps.max() / 4)  # decelerates onto the paper
        self.assertTrue(np.allclose(r.pen_state(1.6)[0], [100, 120]))
        self.assertGreater(r.pen_state(2.6 + .25)[0][1], 120)  # leaving downward
        self.assertIsNone(r.pen_state(2.6 + .55))
        self.assertEqual(r.pen_state(4.6)[2], 1)

    def test_wrist_turn_is_bounded_smooth_and_pivots_on_the_nib(self):
        r = renderer()
        angles = [r.hand_angle(time, r.pen_state(time)[0]) for time in np.arange(1.6, 2.6, 1 / 30)]
        self.assertLessEqual(max(map(abs, angles)), MAX_TILT)
        self.assertLessEqual(max(abs(a - b) for a, b in zip(angles, angles[1:])), 1)
        self.assertLess(min(angles), 0)  # rightward stroke turns the hand clockwise
        marked = r.hand.copy()
        marked.putpixel((8, 9), (255, 0, 0, 255))
        r.hand = marked
        for angle in (-6, 5):
            hand, _, nib, _, _ = r.hand_pose(angle)
            pixels = np.array(hand)
            ys, xs = np.nonzero((pixels[:, :, 0] > 150) & (pixels[:, :, 1] < 90))
            self.assertLess(np.hypot(xs.mean() - nib[0], ys.mean() - nib[1]), 1.5)
        # Turning against the arm would lift its cut edge into view near the bottom: that turn is withheld.
        leftward = renderer(points=((600., 0.), (0., 0.)), x=20)
        turns = [leftward.hand_angle(time, leftward.pen_state(time)[0]) for time in np.arange(1.9, 2.3, 1 / 30)]
        self.assertEqual(max(turns), 5)
        for time, angle in zip(np.arange(1.9, 2.3, 1 / 30), turns):
            cut = leftward.pen_state(time)[0] + leftward.hand_pose(angle)[4]
            self.assertFalse(((cut[:, 0] >= 0) & (cut[:, 0] < 640) & (cut[:, 1] >= 0) & (cut[:, 1] < 360)).any())

    def test_bare_pen_shadow_starts_at_the_nib_and_falls_away_along_the_barrel(self):
        r = renderer()
        r.hand = Image.new('RGBA', (120, 260))
        ImageDraw.Draw(r.hand).line([(8, 9), (100, 240)], fill=(20, 20, 20, 255), width=12)
        r.timeline['hand'] = {'kind': 'pen'}
        pen, shadow, nib, pad, _ = r.hand_pose(0)
        alpha = np.array(shadow)[:, :, 3]
        self.assertGreater(alpha[round(nib[1]) + pad, round(nib[0]) + pad], 0)  # the pen rests on the paper at its nib
        ys, xs = np.nonzero(alpha)
        barrel = float(np.hypot(100 - 8, 240 - 9))
        reach = np.array([xs.max(), ys.max()]) - (np.array([100, 240]) + pad)
        np.testing.assert_allclose(reach, PEN_SHADOW_SLOPE * barrel * SHADOW_DIRECTION, atol=3 * pad)
        self.assertGreater(float(reach @ SHADOW_DIRECTION), .6 * PEN_SHADOW_SLOPE * barrel)

    def test_camera_frames_glides_follows_and_stays_on_the_board(self):
        r = renderer(camera=[{'at': 0, 'center': [200, 150], 'zoom': 1.25},
                             {'at': 'beat:a', 'center': [320, 180], 'zoom': 1.0, 'seconds': .5},
                             {'at': 1.5, 'center': [0, 0], 'zoom': 1.3, 'seconds': .5, 'follow': True}])
        center, zoom = r.camera(0, 1.)
        self.assertEqual((zoom, center.tolist()), (1.25, [256., 150.]))  # framed from the start, clamped to the board
        center, zoom = r.camera(0, 1.75)
        self.assertTrue(1. < zoom < 1.25)  # gliding towards the beat:a key
        center, zoom = r.camera(0, 3.1)
        self.assertAlmostEqual(zoom, 1.3)
        half = np.array([r.width, r.height]) / (2 * zoom)
        self.assertTrue((center >= half - 1e-6).all() and (center <= np.array([r.width, r.height]) - half + 1e-6).all())
        frame = r.view(0, 3.1)
        caption = np.array(frame)[300:320, 290:350, :3]
        self.assertTrue((caption == [10, 20, 30]).all())  # captions are screen-space, never zoomed

    def test_transitions_fit_between_ink_and_keep_legacy_default(self):
        legacy = renderer()
        self.assertEqual(legacy.transition(1), {'type': 'legacy', 'start': 3.76, 'end': 4.})
        pan = renderer(transition={'type': 'pan', 'seconds': .8})
        window = pan.transition(1)
        self.assertEqual((window['type'], window['start'], window['end']), ('pan', 3.6, 4.4))
        self.assertIsNone(renderer(transition={'type': 'cut'}).transition(1))
        frame = pan.scene(0, 3.9)
        self.assertEqual(frame.size, (640, 360))
        fade = renderer(transition={'type': 'fade', 'seconds': .4})
        self.assertEqual(np.array(fade.scene(1, 4.1)).shape, (360, 640, 4))

    def test_page_motion_validation(self):
        canvas = {'width': 640, 'height': 360}
        page = {'start': 1., 'end': 4., 'beats': [{'id': 'a'}]}
        self.assertTrue(validate_page_motion({**page, 'camera': [{'at': 'beat:a', 'zoom': 1.2, 'follow': True}],
                                              'transition': {'type': 'pan', 'seconds': .8}}, canvas))
        # Boards are drawn at up to 3x resolution, so close-ups to 3x stay sharp; erasing takes longer than a camera move.
        for good in ({'camera': [{'zoom': 2.5}]}, {'transition': {'type': 'erase', 'seconds': 1.5}},
                     {'transition': {'type': 'wipe', 'direction': 'up'}}, {'transition': {'type': 'zoom'}}):
            self.assertTrue(validate_page_motion({**page, **good}, canvas))
        for bad, message in [({'camera': [{'zoom': 3.2}]}, 'zoom'), ({'camera': [{'at': 'beat:x'}]}, 'beat'),
                             ({'camera': [{'at': 5}]}, 'inside the page'), ({'camera': [{'center': [900, 10]}]}, 'center'),
                             ({'camera': [{'ease': 'bounce'}]}, 'ease'), ({'camera': {'at': 0}}, 'list'),
                             ({'transition': {'type': 'spin'}}, 'Transition'), ({'transition': {'type': 'fade', 'seconds': 2}}, 'seconds'),
                             ({'transition': {'type': 'erase', 'seconds': 2.5}}, 'seconds'),
                             ({'transition': {'type': 'wipe', 'direction': 'diagonal'}}, 'direction')]:
            with self.assertRaisesRegex(ValueError, message):
                validate_page_motion({**page, **bad}, canvas)
        with self.assertRaisesRegex(ValueError, 'first page'):
            validate_page_motion({**page, 'transition': {'type': 'cut'}}, canvas, first=True)


if __name__ == '__main__':
    unittest.main()

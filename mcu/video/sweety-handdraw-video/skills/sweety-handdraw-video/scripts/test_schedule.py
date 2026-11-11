import unittest
from video_job import FilmBuilder


class ScheduleTest(unittest.TestCase):
    def test_hanzi_get_a_readable_floor_and_other_actions_none(self):
        self.assertAlmostEqual(FilmBuilder.minimum_seconds({'type': 'text', 'text': '葡萄A'}), .72)
        self.assertEqual(FilmBuilder.minimum_seconds({'type': 'illustration'}), 0.)

    def test_travel_gap_grows_with_distance_within_bounds(self):
        near = FilmBuilder.travel_gap({'x': 0, 'y': 0, 'size': 60}, {'x': 40, 'y': 0, 'size': 60}, .07)
        far = FilmBuilder.travel_gap({'x': 0, 'y': 0, 'width': 200, 'height': 200}, {'x': 1500, 'y': 800, 'width': 200, 'height': 200}, .07)
        self.assertAlmostEqual(near, .12)
        self.assertAlmostEqual(far, .45)


if __name__ == '__main__':
    unittest.main()

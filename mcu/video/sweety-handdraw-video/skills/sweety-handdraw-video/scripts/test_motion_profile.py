import unittest
import numpy as np
from motion_profile import PEAK, distance_fraction, time_fraction


class MotionProfileTest(unittest.TestCase):
    def test_minjerk_is_monotonic_eased_and_invertible(self):
        samples = np.linspace(0, 1, 101)
        distances = distance_fraction(samples, 'minjerk')
        self.assertTrue(np.all(np.diff(distances) >= 0))
        self.assertLess(distances[5], samples[5])  # slow start
        self.assertGreater(distances[95], samples[95])  # slow finish
        self.assertTrue(np.allclose(time_fraction(distances, 'minjerk'), samples, atol=2e-3))

    def test_plateau_cruises_between_eased_ends(self):
        samples = np.linspace(0, 1, 101)
        distances = distance_fraction(samples, 'plateau')
        steps = np.diff(distances)
        self.assertTrue(np.all(steps >= 0))
        self.assertLess(steps[0], steps[50] / 10)  # starts from rest
        self.assertAlmostEqual(steps[40], steps[60], places=6)  # constant cruise
        self.assertAlmostEqual(PEAK['plateau'], 1.25, places=3)
        self.assertTrue(np.allclose(time_fraction(distances, 'plateau'), samples, atol=2e-3))

    def test_linear_profile_is_identity(self):
        self.assertAlmostEqual(float(distance_fraction(.3)), .3)
        self.assertAlmostEqual(float(time_fraction(.7)), .7)


if __name__ == '__main__':
    unittest.main()

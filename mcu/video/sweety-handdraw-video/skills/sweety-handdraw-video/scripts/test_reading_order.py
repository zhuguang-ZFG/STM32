"""Reading order survives a pen starting nearer a lower or right-hand stroke; draw-v3 plans object by object."""
import unittest
import numpy as np
from line_drawing import order, SILHOUETTE, STRUCTURE, DETAIL


def stroke(identity, x, y, tier=STRUCTURE, shape=None):
    points = np.array([[x, y], [x + 20, y]], dtype=float)
    entry = {'index': identity, 'part': 0, 'tier': tier, 'points': points, 'closed': False,
             'radius': np.ones(2), 'color': np.zeros((2, 3)), 'length': 20.}
    if shape is not None:
        entry['object'] = shape
    return entry


class ReadingOrderTests(unittest.TestCase):
    def test_top_left_wins_over_shorter_pen_travel(self):
        strokes = [stroke(0, 100, 100), stroke(1, 100, 20), stroke(2, 10, 20)]
        arranged, _ = order(strokes, 1, np.array([100, 100]))
        self.assertEqual([entry['index'] for entry in arranged], [2, 1, 0])

    def test_outline_precedes_structure_and_details_within_the_object(self):
        # An eye above the chin line still waits for the face outline: all three sit on one solid shape.
        strokes = [stroke(0, 0, 0, DETAIL, 1), stroke(1, 0, 20, STRUCTURE, 1), stroke(2, 0, 40, SILHOUETTE, 1)]
        arranged, _ = order(strokes, 1, np.array([0, 0]))
        self.assertEqual([entry['index'] for entry in arranged], [2, 1, 0])

    def test_each_object_is_finished_before_the_next_in_reading_order(self):
        # Two robots side by side: the left one is drawn completely (outline, then its details) before the right one,
        # instead of sweeping every outline of the part and then coming back for the details.
        left = [stroke(0, 0, 60, SILHOUETTE, 1), stroke(1, 0, 70, DETAIL, 1)]
        right = [stroke(2, 200, 60, SILHOUETTE, 2), stroke(3, 200, 70, DETAIL, 2)]
        arranged, _ = order(right + left, 1, np.array([220, 70]))
        self.assertEqual([entry['index'] for entry in arranged], [0, 1, 2, 3])

    def test_marker_keeps_the_planned_top_first_sweep_even_when_tip_is_lower(self):
        from paint_motion import timeline
        region = {'part': 0, 'radius': 7, 'cells': [np.array([[10, 10], [80, 10]]), np.array([[10, 100], [80, 100]])]}
        segments = timeline([region], [], 1, np.array([80, 100]), pace=100)[0]
        sweeps = [segment for segment in segments if segment['kind'] == 'color']
        self.assertEqual(sweeps[0]['points'][0], [10, 10])
        self.assertEqual(sweeps[1]['points'][0], [10, 100])


if __name__ == '__main__':
    unittest.main()

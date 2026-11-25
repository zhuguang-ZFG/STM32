"""Regression tests for hand-drawn figure layer ordering and paper texture."""
import math
import random
import re
import unittest
import xml.etree.ElementTree as ET

from tools.handraw_track.hd import Fig


class HandrawChromeTests(unittest.TestCase):
    def _children(self, grid=True):
        fig = Fig(seed="paper-layer-test", title="Test", grid=grid)
        fig.chrome()
        root = ET.fromstring(f'<svg xmlns="http://www.w3.org/2000/svg">{fig.body[0]}</svg>')
        return list(root)

    @staticmethod
    def _fibers(children):
        return [
            node for node in children
            if node.tag.endswith("path") and node.attrib.get("stroke") == "#C9BEA6"
        ]

    def test_paper_fibers_render_above_paper_and_grid(self):
        children = self._children(grid=True)

        paper_index = next(
            i for i, node in enumerate(children)
            if node.tag.endswith("rect") and node.attrib.get("fill") == "#FDF8EA"
        )
        grid_index = next(
            i for i, node in enumerate(children)
            if node.tag.endswith("rect") and node.attrib.get("fill") == "url(#dotgrid)"
        )
        fiber_indices = [children.index(node) for node in self._fibers(children)]

        self.assertEqual(len(fiber_indices), 12)
        self.assertLess(paper_index, grid_index)
        self.assertLess(grid_index, min(fiber_indices))

    def test_paper_fibers_render_above_paper_without_grid(self):
        children = self._children(grid=False)

        paper_index = next(
            i for i, node in enumerate(children)
            if node.tag.endswith("rect") and node.attrib.get("fill") == "#FDF8EA"
        )
        fiber_indices = [children.index(node) for node in self._fibers(children)]

        self.assertEqual(len(fiber_indices), 12)
        self.assertLess(paper_index, min(fiber_indices))

    def test_paper_fibers_are_short_subtle_and_deterministic(self):
        fibers_a = self._fibers(self._children())
        fibers_b = self._fibers(self._children())
        self.assertEqual(len(fibers_a), 12)
        self.assertEqual([n.attrib["d"] for n in fibers_a], [n.attrib["d"] for n in fibers_b])

        angles = []
        for fiber in fibers_a:
            points = [float(value) for value in re.findall(r"-?\d+(?:\.\d+)?", fiber.attrib["d"])]
            xs, ys = points[0::2], points[1::2]
            dx, dy = xs[-1] - xs[0], ys[-1] - ys[0]
            length = math.hypot(dx, dy)
            angle = math.degrees(math.atan2(dy, dx))
            angles.append(angle)
            self.assertGreaterEqual(length, 49)
            self.assertLessEqual(length, 181)
            self.assertLessEqual(abs(angle), 20.1)
            self.assertGreaterEqual(float(fiber.attrib["opacity"]), 0.08)
            self.assertLessEqual(float(fiber.attrib["opacity"]), 0.151)

        self.assertGreater(max(angles) - min(angles), 10)

    def test_paper_fibers_preserve_existing_chrome_rng_sequence(self):
        seed = "paper-layer-test"
        fig = Fig(seed=seed, title="", badge="", grid=False)
        fig.chrome()

        expected = random.Random(seed)
        for _ in range(12 * 7):
            expected.random()
        self.assertEqual(fig.rng.getstate(), expected.getstate())


if __name__ == "__main__":
    unittest.main()

"""Regression tests for hand-drawn figure layer ordering."""
import unittest
import xml.etree.ElementTree as ET

from tools.handraw_track.hd import Fig


class HandrawChromeTests(unittest.TestCase):
    def test_paper_fibers_render_above_paper_and_grid(self):
        fig = Fig(seed="paper-layer-test", title="Test", grid=True)
        fig.chrome()
        root = ET.fromstring(f'<svg xmlns="http://www.w3.org/2000/svg">{fig.body[0]}</svg>')
        children = list(root)

        paper_index = next(
            i for i, node in enumerate(children)
            if node.tag.endswith("rect") and node.attrib.get("fill") == "#FDF8EA"
        )
        grid_index = next(
            i for i, node in enumerate(children)
            if node.tag.endswith("rect") and node.attrib.get("fill") == "url(#dotgrid)"
        )
        fiber_indices = [
            i for i, node in enumerate(children)
            if node.tag.endswith("path") and node.attrib.get("stroke") == "#C9BEA6"
        ]

        self.assertEqual(len(fiber_indices), 12)
        self.assertLess(paper_index, grid_index)
        self.assertLess(grid_index, min(fiber_indices))

    def test_paper_fibers_render_above_paper_without_grid(self):
        fig = Fig(seed="paper-layer-test", title="Test", grid=False)
        fig.chrome()
        root = ET.fromstring(f'<svg xmlns="http://www.w3.org/2000/svg">{fig.body[0]}</svg>')
        children = list(root)

        paper_index = next(
            i for i, node in enumerate(children)
            if node.tag.endswith("rect") and node.attrib.get("fill") == "#FDF8EA"
        )
        fiber_indices = [
            i for i, node in enumerate(children)
            if node.tag.endswith("path") and node.attrib.get("stroke") == "#C9BEA6"
        ]

        self.assertEqual(len(fiber_indices), 12)
        self.assertLess(paper_index, min(fiber_indices))


if __name__ == "__main__":
    unittest.main()

"""Regression checks for technical figure text staying on-canvas."""
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TRACK = ROOT / "tools" / "handraw_track"
sys.path.insert(0, str(TRACK))

import fig_ch32  # noqa: E402
from hd import W, text_w  # noqa: E402


class HandrawLayoutTests(unittest.TestCase):
    def test_ch32_pi_step_text_fits_canvas_width(self):
        root = ET.fromstring(fig_ch32.pi_step().svg())
        anchor_offsets = {"start": 0, "middle": 0.5, "end": 1}
        for node in root.iter("{http://www.w3.org/2000/svg}text"):
            text = "".join(node.itertext())
            x = float(node.attrib["x"])
            width = text_w(text, float(node.attrib["font-size"]))
            left = x - width * anchor_offsets[node.get("text-anchor", "start")]
            with self.subTest(text=text):
                self.assertGreaterEqual(left, 0)
                self.assertLessEqual(left + width, W)


if __name__ == "__main__":
    unittest.main()

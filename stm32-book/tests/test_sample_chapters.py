#!/usr/bin/env python3
"""Checks for the two thickened sample chapters and their static figures."""

from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIAGRAMS = ROOT / "assets" / "diagrams"
BOOT = DIAGRAMS / "sample-00-boot-state.svg"
GPIO = DIAGRAMS / "sample-03-gpio-led.svg"


class SampleFigureTests(unittest.TestCase):
    def test_key_figures_are_static_and_under_60_kib(self) -> None:
        for path, tokens in (
            (BOOT, ("STM32F103C8T6", "BOOT0", "BOOT1", "SWDIO", "SWCLK", "0x08000000", "0x00000000", "0x1FFFF000", "SYSCLK")),
            (GPIO, ("STM32F103C8T6", "LQFP48", "PA0", "PC13", "270", "260", "3.3", "3 mA", "2 MHz", "30 pF", "LCKR", "0x18")),
        ):
            raw = path.read_text(encoding="utf-8")
            self.assertLess(path.stat().st_size, 60 * 1024, path.name)
            for banned in ("<animate", "@keyframes", "animation:"):
                self.assertNotIn(banned, raw)
            for token in tokens:
                self.assertIn(token, raw)
            self.assertIn("自绘", raw)
            self.assertNotIn("实拍", raw)
            self.assertNotIn("矢量动画", raw)


if __name__ == "__main__":
    unittest.main()

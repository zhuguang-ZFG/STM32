#!/usr/bin/env python3
"""Checks for thickened chapters 16, 17, 18, and 19 and their static figures."""

from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIAGRAMS = ROOT / "assets" / "diagrams"
STOP = DIAGRAMS / "sample-16-stop-wake.svg"
CFSR = DIAGRAMS / "sample-17-cfsr.svg"
BOOT = DIAGRAMS / "sample-18-boot-triage.svg"
FLASH = DIAGRAMS / "sample-19-flash-fit.svg"


class Batch6FigureTests(unittest.TestCase):
    def test_key_figures_are_static_and_under_60_kib(self) -> None:
        for path, tokens, banned in (
            (
                STOP,
                (
                    "STM32F103C8T6",
                    "LQFP48",
                    "14 uA",
                    "24 uA",
                    "5.4 us",
                    "8 MHz",
                    "72 MHz",
                    "0x271",
                    "12800",
                    "115200",
                    "SLEEPDEEP=1",
                    "PDDS=0",
                    "pin 10",
                    "PA0",
                    "自绘",
                ),
                ("14~20", "780", "8/16", "<animate", "@keyframes", "animation:", "矢量动画", "实拍"),
            ),
            (
                CFSR,
                (
                    "STM32F103C8T6",
                    "0xE000ED28",
                    "0xE000ED2C",
                    "0xE000ED38",
                    "0xE000EDFC",
                    "0xE0001004",
                    "0x40000000",
                    "bit 15",
                    "bit 24",
                    "bit 30",
                    "1 us",
                    "72",
                    "6",
                    "pin 39",
                    "JTDO",
                    "自绘",
                ),
                ("167 ns", "<animate", "@keyframes", "animation:", "矢量动画", "实拍"),
            ),
            (
                BOOT,
                (
                    "STM32F103C8T6",
                    "pin 34",
                    "PA13",
                    "pin 37",
                    "PA14",
                    "pin 7",
                    "0.1 uF",
                    "pin 44",
                    "BOOT0",
                    "0x08000000",
                    "0x1FFFF000",
                    "自绘",
                ),
                ("0x1FFFB000", "<animate", "@keyframes", "animation:", "矢量动画", "实拍"),
            ),
            (
                FLASH,
                (
                    "STM32F103C8T6",
                    "0x08000000",
                    "0x08004000",
                    "0x08004800",
                    "0x08010000",
                    "0x0801B800",
                    "0xB800",
                    "110 KB",
                    "20480",
                    "65536",
                    "4096",
                    "自绘",
                ),
                ("0x5A5A0001", "<animate", "@keyframes", "animation:", "矢量动画", "实拍"),
            ),
        ):
            text = path.read_text(encoding="utf-8")
            self.assertLess(path.stat().st_size, 60 * 1024, path.name)
            self.assertNotIn("Svg.footer", text)
            for token in tokens:
                self.assertIn(token, text, path.name)
            for token in banned:
                self.assertNotIn(token, text, path.name)


if __name__ == "__main__":
    unittest.main()

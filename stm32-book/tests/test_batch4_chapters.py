#!/usr/bin/env python3
"""Checks for thickened chapters 01, 07, 10, and 11 and their static figures."""

from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIAGRAMS = ROOT / "assets" / "diagrams"
SWD = DIAGRAMS / "sample-01-swd-vectors.svg"
I2C = DIAGRAMS / "sample-07-i2c-addr.svg"
DMA = DIAGRAMS / "sample-10-dma-cndtr.svg"
IWDG = DIAGRAMS / "sample-11-iwdg-1s.svg"


class Batch4FigureTests(unittest.TestCase):
    def test_key_figures_are_static_and_under_60_kib(self) -> None:
        for path, tokens in (
            (
                SWD,
                (
                    "STM32F103C8T6",
                    "LQFP48",
                    "pin 34",
                    "PA13",
                    "SWDIO",
                    "pin 35",
                    "VSS_2",
                    "pin 36",
                    "VDD_2",
                    "pin 37",
                    "PA14",
                    "SWCLK",
                    "pin 44",
                    "BOOT0",
                    "0x08000000",
                    "0x00000000",
                    "MSP",
                    "Reset_Handler",
                    "GPIO",
                    "0x1FFFF000",
                    "0xA5",
                    "0xAA",
                    "64 KB",
                    "20 KB",
                ),
            ),
            (
                I2C,
                (
                    "STM32F103C8T6",
                    "LQFP48",
                    "pin 42",
                    "PB6",
                    "pin 43",
                    "PB7",
                    "4.7",
                    "0x78",
                    "0x3C",
                    "0x801E",
                    "400 kHz",
                    "ACK",
                    "NACK",
                    "36 MHz",
                    "0x00B4",
                ),
            ),
            (
                DMA,
                (
                    "STM32F103C8T6",
                    "DMA1",
                    "channel 4",
                    "CNDTR",
                    "5 samples",
                    "10 bytes",
                    "4 samples",
                    "8 bytes",
                    "DMA2",
                    "pin 30",
                    "PA9",
                ),
            ),
            (
                IWDG,
                (
                    "STM32F103C8T6",
                    "40 kHz",
                    "30 kHz",
                    "60 kHz",
                    "prescaler 64",
                    "625 Hz",
                    "Reload = 624",
                    "Reload = 625",
                    "pin 1",
                    "VBAT",
                    "pin 3",
                    "pin 4",
                    "32767",
                    "32768",
                    "0x50",
                    "58.25",
                ),
            ),
        ):
            raw = path.read_text(encoding="utf-8")
            self.assertLess(path.stat().st_size, 60 * 1024, path.name)
            for banned in ("<animate", "@keyframes", "animation:", "矢量动画", "实拍"):
                self.assertNotIn(banned, raw)
            for token in tokens:
                self.assertIn(token, raw)
            self.assertIn("自绘", raw)
            self.assertNotIn("Svg.footer", raw)
        dma = DMA.read_text(encoding="utf-8")
        self.assertNotIn("21 us", dma)
        self.assertNotIn("21 µs", dma)
        iwdg = IWDG.read_text(encoding="utf-8")
        self.assertNotIn("6 pF", iwdg)


if __name__ == "__main__":
    unittest.main()

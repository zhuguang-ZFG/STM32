#!/usr/bin/env python3
"""Checks for thickened chapters 02, 05, 08, and 09 and their static figures."""

from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIAGRAMS = ROOT / "assets" / "diagrams"
CLOCK = DIAGRAMS / "sample-02-clock-tree.svg"
PWM = DIAGRAMS / "sample-05-pwm-1khz.svg"
SPI = DIAGRAMS / "sample-08-spi-jedec.svg"
ADC = DIAGRAMS / "sample-09-adc-sar.svg"


class Batch3FigureTests(unittest.TestCase):
    def test_key_figures_are_static_and_under_60_kib(self) -> None:
        for path, tokens in (
            (
                CLOCK,
                (
                    "STM32F103C8T6",
                    "LQFP48",
                    "pin 5 PD0",
                    "pin 6 PD1",
                    "pin 29 PA8",
                    "PLLMUL=0111",
                    "PLLSRC=1",
                    "PLLXTPRE=0",
                    "72 MHz",
                    "36 MHz",
                    "12 MHz",
                    "18 MHz",
                    "14 MHz",
                    "48 MHz",
                    "50 MHz",
                    "USBPRE=0",
                    "LATENCY=2",
                    "LATENCY=0",
                    "CSSC",
                    "HSI 8 MHz",
                    "7.3.2",
                ),
            ),
            (
                PWM,
                (
                    "STM32F103C8T6",
                    "LQFP48",
                    "pin 16",
                    "PA6",
                    "TIM3_CH1",
                    "PSC=71",
                    "ARR=999",
                    "CCR=500",
                    "1000 Hz",
                    "500 Hz",
                    "500 us",
                    "72 MHz",
                    "36 MHz",
                    "999999",
                    "16-bit",
                    "MOE",
                    "0x44",
                    "SPI1_MISO is not on this trace",
                ),
            ),
            (
                SPI,
                (
                    "STM32F103C8T6",
                    "LQFP48",
                    "pin 14 PA4",
                    "pin 15 PA5",
                    "pin 16 PA6",
                    "pin 17 PA7",
                    "CPOL=0",
                    "CPHA=0",
                    "BR=010",
                    "9 MHz",
                    "0x9F",
                    "0xEF",
                    "0x40",
                    "0x17",
                    "36 MHz",
                    "MOSI",
                    "MISO",
                    "swapped",
                ),
            ),
            (
                ADC,
                (
                    "STM32F103C8T6",
                    "LQFP48",
                    "pin 9 VDDA",
                    "pin 10 PA0",
                    "ADC12_IN0",
                    "12 MHz",
                    "21 us",
                    "239.5",
                    "12.5",
                    "4096",
                    "18 MHz",
                    "14 MHz",
                    "previous voltage",
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
        spi = SPI.read_text(encoding="utf-8")
        self.assertNotIn("0x40013000", spi)
        adc = ADC.read_text(encoding="utf-8")
        self.assertNotIn("270", adc)


if __name__ == "__main__":
    unittest.main()

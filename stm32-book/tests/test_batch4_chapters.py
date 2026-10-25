#!/usr/bin/env python3
"""Checks for thickened chapters 01, 07, 10, and 11 and their static figures."""

from __future__ import annotations

import importlib.util
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


def load_gen_gifs():
    path = ROOT / "tools" / "gen_gifs.py"
    spec = importlib.util.spec_from_file_location("gen_gifs_batch4", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Batch4GifTests(unittest.TestCase):
    def test_new_gifs_are_short_auxiliaries(self) -> None:
        gifs = load_gen_gifs()
        for name in (
            "led-blink",
            "pwm-breath",
            "uart-bits",
            "i2c-timing",
            "dma-ring",
            "sar-adc",
            "nvic-preempt",
            "uart-idle",
            "clock-css",
            "pwm-1khz",
            "spi-jedec",
            "adc-sample",
            "swd-fetch",
            "i2c-addr",
            "dma-cndtr",
            "iwdg-1s",
        ):
            self.assertIn(name, gifs.BUILDERS)
        source = (ROOT / "tools" / "gen_gifs.py").read_text(encoding="utf-8")
        swd_src = source.split("def swd_fetch", 1)[1].split("def i2c_addr", 1)[0]
        i2c_src = source.split("def i2c_addr", 1)[1].split("def dma_cndtr", 1)[0]
        dma_src = source.split("def dma_cndtr", 1)[1].split("def iwdg_1s", 1)[0]
        iwdg_src = source.split("def iwdg_1s", 1)[1].split("BUILDERS", 1)[0]
        self.assertIn("pin 34", swd_src)
        self.assertIn("pin 37", swd_src)
        self.assertIn("MSP", swd_src)
        self.assertIn("Reset_Handler", swd_src)
        self.assertNotIn("0xAA", swd_src)
        self.assertNotIn("GPIO", swd_src)
        self.assertIn("0x78", i2c_src)
        self.assertIn("0x801E", i2c_src)
        self.assertIn("4.7", i2c_src)
        self.assertIn("ACK", i2c_src)
        self.assertNotIn("0x3C", i2c_src)
        self.assertIn("CNDTR", dma_src)
        self.assertIn("5 samples", dma_src)
        self.assertIn("10 bytes", dma_src)
        self.assertNotIn("DMA2", dma_src)
        self.assertNotIn("3 bytes", dma_src)
        self.assertIn("Reload = 624", iwdg_src)
        self.assertIn("40 kHz", iwdg_src)
        self.assertIn("625 Hz", iwdg_src)
        self.assertNotIn("Reload = 625", iwdg_src)
        self.assertNotIn("0x50", iwdg_src)
        for name in ("swd-fetch", "i2c-addr", "dma-cndtr", "iwdg-1s"):
            gif = gifs.BUILDERS[name]()
            self.assertGreaterEqual(len(gif.frames), 3)
            self.assertLessEqual(len(gif.frames), 12)
            path = ROOT / "assets" / "gif" / f"{name}.gif"
            self.assertLess(path.stat().st_size, 500 * 1024, path.name)


if __name__ == "__main__":
    unittest.main()

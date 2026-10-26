#!/usr/bin/env python3
"""Checks for thickened chapters 16, 17, 18, and 19 and their static figures."""

from __future__ import annotations

import importlib.util
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


def _load_gifs():
    path = ROOT / "tools" / "gen_gifs.py"
    spec = importlib.util.spec_from_file_location("gen_gifs_batch6", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Batch6GifTests(unittest.TestCase):
    def test_four_auxiliary_gifs_are_short_and_ascii(self) -> None:
        gifs = _load_gifs()
        names = (
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
            "iap-jump",
            "can-500k",
            "usb-48m",
            "rtos-tick",
            "stop-wake",
            "cfsr-read",
            "boot0-low",
            "one-slot",
        )
        for name in names:
            self.assertIn(name, gifs.BUILDERS)
        self.assertEqual(list(gifs.BUILDERS)[-4:], ["stop-wake", "cfsr-read", "boot0-low", "one-slot"])
        source = (ROOT / "tools" / "gen_gifs.py").read_text(encoding="utf-8")
        stop_src = source.split("def stop_wake_gif", 1)[1].split("def cfsr_read_gif", 1)[0]
        cfsr_src = source.split("def cfsr_read_gif", 1)[1].split("def boot0_low", 1)[0]
        boot_src = source.split("def boot0_low", 1)[1].split("def one_slot", 1)[0]
        slot_src = source.split("def one_slot", 1)[1].split("BUILDERS", 1)[0]
        self.assertIn("8 MHz", stop_src)
        self.assertIn("72 MHz", stop_src)
        self.assertIn("115200", stop_src)
        self.assertNotIn("12800", stop_src)
        self.assertNotIn("24 uA", stop_src)
        self.assertIn("CFSR", cfsr_src)
        self.assertIn("bit 15 = 1", cfsr_src)
        self.assertIn("1 us", cfsr_src)
        self.assertIn("72", cfsr_src)
        self.assertNotIn("bit 15 = 0", cfsr_src)
        self.assertNotIn("delta 0", cfsr_src)
        self.assertIn("pin 44", boot_src)
        self.assertIn("pin 34", boot_src)
        self.assertIn("pin 37", boot_src)
        self.assertIn("BOOT0 = 0", boot_src)
        self.assertNotIn("BOOT0 = 1", boot_src)
        self.assertNotIn("-O2", boot_src)
        self.assertIn("16 KB", slot_src)
        self.assertIn("2 KB", slot_src)
        self.assertIn("0xB800", slot_src)
        self.assertIn("0x08010000", slot_src)
        self.assertNotIn("0x0801B800", slot_src)
        self.assertNotIn("65536", slot_src)
        for name in ("stop-wake", "cfsr-read", "boot0-low", "one-slot"):
            gif = gifs.BUILDERS[name]()
            self.assertGreaterEqual(len(gif.frames), 3)
            self.assertLessEqual(len(gif.frames), 12)
            path = ROOT / "assets" / "gif" / f"{name}.gif"
            self.assertLess(path.stat().st_size, 500 * 1024, path.name)


if __name__ == "__main__":
    unittest.main()

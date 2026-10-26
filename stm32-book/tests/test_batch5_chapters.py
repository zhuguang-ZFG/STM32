#!/usr/bin/env python3
"""Checks for thickened chapters 12, 13, 14, and 15 and their static figures."""

from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIAGRAMS = ROOT / "assets" / "diagrams"
IAP = DIAGRAMS / "sample-12-iap-map.svg"
CAN = DIAGRAMS / "sample-13-can-bit.svg"
USB = DIAGRAMS / "sample-14-usb-enum.svg"
RTOS = DIAGRAMS / "sample-15-rtos-prio.svg"


class Batch5FigureTests(unittest.TestCase):
    def test_key_figures_are_static_and_under_60_kib(self) -> None:
        for path, tokens in (
            (
                IAP,
                (
                    "STM32F103C8T6",
                    "LQFP48",
                    "0x08000000",
                    "0x08004000",
                    "0x08004800",
                    "0x08004804",
                    "0x0800FC00",
                    "0x08010000",
                    "0xB800",
                    "0x45670123",
                    "0xCDEF89AB",
                    "0x0801FC00",
                    "LOCK",
                    "VTOR",
                    "MSP",
                    "Reset_Handler",
                    "1 KB",
                    "64 KB",
                    "medium-density",
                ),
            ),
            (
                CAN,
                (
                    "STM32F103C8T6",
                    "36 MHz",
                    "pin 45",
                    "PB8",
                    "pin 46",
                    "PB9",
                    "250 ns",
                    "2 us",
                    "500 kbit/s",
                    "75%",
                    "prescaler 9",
                    "450 kbit/s",
                    "70%",
                    "120",
                    "CANH",
                    "CANL",
                    "pin 32",
                    "PA11",
                    "pin 5",
                    "PD0",
                    "pin 6",
                    "PD1",
                ),
            ),
            (
                USB,
                (
                    "STM32F103C8T6",
                    "pin 32",
                    "PA11",
                    "DM",
                    "pin 33",
                    "PA12",
                    "DP",
                    "1.5",
                    "48 MHz",
                    "USBPRE = 0",
                    "USBPRE = 1",
                    "72 MHz",
                    "18",
                    "67",
                    "0x1209",
                    "0x0001",
                    "64",
                    "100 mA",
                    "1023",
                    "0x0483",
                ),
            ),
            (
                RTOS,
                (
                    "STM32F103C8T6",
                    "1 ms",
                    "TIM4",
                    "128 words",
                    "512 bytes",
                    "0x50",
                    "priority 2",
                    "priority 1",
                    "EXTI0",
                    "configASSERT",
                    "SysTick",
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
        iap = IAP.read_text(encoding="utf-8")
        self.assertNotIn("0x1FFFF000", iap)
        can = CAN.read_text(encoding="utf-8")
        self.assertNotIn("absent", can.lower())
        rtos = RTOS.read_text(encoding="utf-8")
        self.assertNotIn("167 ns", rtos)
        self.assertNotIn("17.2", rtos)


if __name__ == "__main__":
    unittest.main()

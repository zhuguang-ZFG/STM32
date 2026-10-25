#!/usr/bin/env python3
"""Checks for thickened chapters 04 and 06 and their static figures."""

from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIAGRAMS = ROOT / "assets" / "diagrams"
NVIC = DIAGRAMS / "sample-04-exception-stack.svg"
UART = DIAGRAMS / "sample-06-uart-frame.svg"


class Batch2FigureTests(unittest.TestCase):
    def test_key_figures_are_static_and_under_60_kib(self) -> None:
        for path, tokens in (
            (
                NVIC,
                (
                    "STM32F103C8T6",
                    "NVIC_PRIORITYGROUP_4",
                    "xPSR",
                    "PC",
                    "LR",
                    "R12",
                    "R3",
                    "R2",
                    "R1",
                    "R0",
                    "167 ns",
                    "PA0",
                    "EXTI0",
                    "EXTI_PR",
                    "EXTI0_IRQn",
                    "TIM2",
                    "PRIMASK",
                    "NMI",
                    "GROUP_4",
                ),
            ),
            (
                UART,
                (
                    "STM32F103C8T6",
                    "LQFP48",
                    "PA9",
                    "PA10",
                    "30",
                    "31",
                    "0xA5",
                    "0x271",
                    "39.0625",
                    "8.68",
                    "86.8",
                    "USART_SR",
                    "0x00",
                    "USART_DR",
                    "0x04",
                    "USART_BRR",
                    "0x08",
                    "USART_CR1",
                    "0x0C",
                    "FE",
                    "OVER8",
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


if __name__ == "__main__":
    unittest.main()

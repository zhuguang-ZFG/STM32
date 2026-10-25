#!/usr/bin/env python3
"""Checks for thickened chapters 04 and 06 and their static figures."""

from __future__ import annotations

import importlib.util
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


def load_gen_gifs():
    path = ROOT / "tools" / "gen_gifs.py"
    spec = importlib.util.spec_from_file_location("gen_gifs_batch2", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Batch2GifTests(unittest.TestCase):
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
        ):
            self.assertIn(name, gifs.BUILDERS)
        source = (ROOT / "tools" / "gen_gifs.py").read_text(encoding="utf-8")
        nvic_src = source.split("def nvic_preempt", 1)[1].split("def uart_idle", 1)[0]
        idle_src = source.split("def uart_idle", 1)[1].split("BUILDERS", 1)[0]
        self.assertIn("TIM2", nvic_src)
        self.assertIn("EXTI0", nvic_src)
        self.assertNotIn("SAME PREEMPT", nvic_src)
        self.assertIn("86.8 us", idle_src)
        self.assertIn("IDLE", idle_src)
        self.assertNotIn("FE", idle_src)
        for name in ("nvic-preempt", "uart-idle"):
            gif = gifs.BUILDERS[name]()
            self.assertGreaterEqual(len(gif.frames), 3)
            self.assertLessEqual(len(gif.frames), 12)
            path = ROOT / "assets" / "gif" / f"{name}.gif"
            self.assertLess(path.stat().st_size, 500 * 1024, path.name)


if __name__ == "__main__":
    unittest.main()

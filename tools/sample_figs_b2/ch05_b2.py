#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Chapter 05 B2 figure: three read-back rings behind a silent or mistuned PWM.

Static SVG only: no CSS animation, no SMIL. Panel titles are Chinese, body copy
is English, matching sample-19-flash-fit.svg used by both editions.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from svgkit import Svg, T


def _credit(canvas: Svg, note: str) -> None:
    canvas.line(24, canvas.h - 36, canvas.w - 24, canvas.h - 36, stroke=T.GRID, sw=1)
    canvas.text(24, canvas.h - 16, note, size=11, fill=T.MUTED)
    canvas.text(canvas.w - 24, canvas.h - 16, "自绘 · 静态 · CC BY 4.0", size=11, fill=T.DIM, anchor="end")


def pwm_debug() -> Svg:
    canvas = Svg(
        960,
        920,
        "有波形而周期差整数倍时停在环 ①；PA6 全无波形时，CC1E = 0 与 CRL MODE6 = 00 要分开读",
        "STM32F103C8T6 LQFP48 · RM0008 Rev 21 §15 · DS5319 Rev 20 Table 5",
    )
    canvas.header(tag="05", tag_color=T.CYAN)
    canvas.text(40, 86, "STM32F103C8T6  LQFP48 pin 16 PA6 = TIM3_CH1  TIM3 on APB1",
                size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112,
                "offsets: TIM3_CCER 0x20   TIM3_CCMR1 0x18   GPIOA_CRL 0x00   TIM3_REMAP lives in AFIO_MAPR",
                size=13, fill=T.CYAN)
    canvas.text(40, 138,
                "counter clock 72 MHz: PCLK1 = 36 MHz, doubled because the APB1 prescaler is not 1",
                size=14, fill=T.AMBER)
    canvas.text(40, 164,
                "read the rings in this order; a later ring never repairs an earlier one",
                size=13, fill=T.MUTED)

    canvas.text(40, 196, "正常路径  three rings open, PA6 carries 1 kHz", size=16,
                fill=T.GREEN, weight="700")
    canvas.rect(40, 210, 880, 188, fill=T.PANEL, stroke=T.GREEN, rx=8)
    rings = [
        ("① 分频比", "TIM3_PSC = 71  TIM3_ARR = 999",
         "72e6 / (72 × 1000) = 1000 Hz", "PSC+1 and ARR+1 are the counts"),
        ("② 输出使能", "TIM3_CCER bit 0",
         "CC1E = 1", "CCMR1 OC1M[6:4] = 110"),
        ("③ GPIO 复用", "GPIOA_CRL[27:24] = 0xB",
         "CNF6 = 10  MODE6 = 11", "TIM3_REMAP = 00 keeps PA6"),
    ]
    for index, (title, reg, value, note) in enumerate(rings):
        left = 58 + index * 290
        canvas.rect(left, 230, 260, 132, fill=T.BG, stroke=T.CYAN, rx=6)
        canvas.text(left + 14, 260, title, size=14, fill=T.CYAN, weight="700")
        canvas.text(left + 14, 292, reg, size=12, fill=T.TEXT, mono=True)
        canvas.text(left + 14, 320, value, size=13, fill=T.GREEN, weight="700")
        canvas.text(left + 14, 346, note, size=11, fill=T.MUTED)
        if index < 2:
            canvas.arrow(left + 260, 296, left + 290, 296, color=T.GREEN, sw=2, head=6)
    canvas.text(56, 384, "read PSC, ARR, CCER, and CRL back before touching the code again",
                size=12, fill=T.MUTED)

    canvas.text(40, 430, "失败路径  each ring fails on its own read-back", size=16,
                fill=T.RED, weight="700")
    canvas.rect(40, 444, 880, 196, fill=T.PANEL, stroke=T.RED, rx=8)
    rows = [
        ("①  PSC/ARR from 36 MHz",
         "a 500 Hz waveform is still there, so only ring ① is wrong"),
        ("②  CCER bit 0 CC1E = 0",
         "OC1 never reaches the pin: PA6 stays quiet"),
        ("③a  CRL[27:24] MODE6 = 00",
         "the pin is still an input: AF push-pull never drives it"),
        ("③b  TIM3_REMAP != 00",
         "the waveform moves to PB4 or PC6: PA6 stays quiet"),
    ]
    for index, (left_text, right_text) in enumerate(rows):
        base = 478 + index * 38
        canvas.text(56, base, left_text, size=13, fill=T.RED, mono=True)
        canvas.text(360, base, right_text, size=14, fill=T.TEXT)
    canvas.text(56, 622, "start from the scope: is there any waveform at all?",
                size=13, fill=T.MUTED)

    canvas.text(40, 672, "判据  waveform first, then the read-back", size=16,
                fill=T.VIOLET, weight="700")
    canvas.rect(40, 686, 880, 180, fill=T.BG2, stroke=T.VIOLET, rx=8)
    canvas.text(56, 716,
                "A waveform with the period off by a whole ratio: ring ①. Nothing at all: rings ② and ③.",
                size=14, fill=T.TEXT, weight="700")
    canvas.text(56, 742,
                "CC1E = 0 disconnects OC1; MODE6 = 00 leaves PA6 an input; a non-zero remap moves the channel.",
                size=14, fill=T.GREEN)
    canvas.text(56, 768,
                "TIM1 also needs BDTR bit 15 MOE = 1 at offset 0x44, reset 0x0000; TIM3 has no MOE.",
                size=14, fill=T.AMBER)
    canvas.text(56, 794,
                "CCR sets only the duty, never the frequency. Read PSC, ARR, CCER, and CRL in that order.",
                size=14, fill=T.TEXT)
    canvas.text(56, 820,
                "Does not prove: the CCR duty, the probe ground, or whether chapter 08 holds PA6 as SPI1_MISO.",
                size=13, fill=T.MUTED)
    canvas.text(56, 846,
                "one ring at a time: three numbers turned together hide which one was wrong.",
                size=13, fill=T.MUTED)

    _credit(canvas, "自绘。CCER/CCMR1 位号与 BDTR 偏移来自 RM0008 Rev 21 第 15 章；"
                    "PA6 第 16 脚与默认复用来自 DS5319 Rev 20 表 5。")
    return canvas


FIGURES = [
    ("sample-05-pwm-debug.svg", pwm_debug),
]


def main(argv: list[str]) -> int:
    out_dir = argv[1] if len(argv) > 1 else os.path.join(os.getcwd(), ".temp", "b2ch05")
    os.makedirs(out_dir, exist_ok=True)
    for name, make in FIGURES:
        make().save(os.path.join(out_dir, name))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

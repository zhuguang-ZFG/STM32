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
    canvas.text(40, 122, "PA6 的波形就是判据：先看有没有，再看周期对不对", size=15, fill=T.TEXT, weight="700")

    # 判据：三种波形
    judges = [
        (40, [1, 0, 1, 0, 1, 0, 1, 0], "1 kHz ✓", "三环都通", T.GREEN),
        (340, [1, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0], "500 Hz", "差整数倍 → 只查环 ①", T.AMBER),
        (640, [0, 0, 0, 0, 0, 0, 0, 0], "全无", "→ 查环 ② ③", T.RED),
    ]
    for jx, bits, head, note, c in judges:
        canvas.rect(jx, 146, 280, 120, fill=T.PANEL, stroke=c, rx=8)
        canvas.waveform(jx + 18, 156, 244, 64, bits, color=c, sw=2)
        canvas.text(jx + 18, 242, head, size=13, fill=c, weight="700")
        canvas.text(jx + 100, 242, note, size=12, fill=T.TEXT)

    # 信号链三环
    rings = [
        (40, "环 ① 分频比", "TIM3_PSC = 71", "TIM3_ARR = 999",
         "72e6 / (72 × 1000) = 1000 Hz"),
        (360, "环 ② 输出使能", "TIM3_CCER bit 0 = 1", "CCMR1 OC1M = 110",
         "CC1E = 0 → OC1 到不了引脚"),
        (680, "环 ③ GPIO 复用", "CRL[27:24] = 0xB", "TIM3_REMAP = 00",
         "MODE6 = 00 → 脚还是输入"),
    ]
    for rx_, title, l1, l2, l3 in rings:
        canvas.rect(rx_, 300, 250, 140, fill=T.PANEL, stroke=T.CYAN, rx=8)
        canvas.text(rx_ + 14, 328, title, size=14, fill=T.CYAN, weight="700")
        canvas.text(rx_ + 14, 356, l1, size=12, fill=T.TEXT, mono=True)
        canvas.text(rx_ + 14, 378, l2, size=12, fill=T.TEXT, mono=True)
        canvas.text(rx_ + 14, 406, l3, size=11, fill=T.GREEN)
    canvas.arrow(292, 370, 358, 370, color=T.GREEN, sw=2, head=7)
    canvas.arrow(612, 370, 678, 370, color=T.GREEN, sw=2, head=7)
    canvas.circle(922, 370, 26, fill=T.BG, stroke=T.GREEN, sw=2)
    canvas.text(922, 366, "PA6", size=12, fill=T.GREEN, anchor="middle", weight="700")
    canvas.text(922, 384, "第 16 脚", size=9, fill=T.MUTED, anchor="middle")

    # 环① 的专属症状
    canvas.rect(680, 456, 250, 54, fill=T.BG2, stroke=T.AMBER, rx=4)
    canvas.text(692, 478, "REMAP ≠ 00 → 波形跑到", size=11, fill=T.AMBER)
    canvas.text(692, 496, "PB4 或 PC6，PA6 安静", size=11, fill=T.AMBER)
    canvas.text(40, 540, "counter clock 72 MHz：PCLK1 = 36 MHz，APB1 预分频 ≠ 1 时翻倍——"
                        "按 36 MHz 算 PSC/ARR 就得到 500 Hz", size=12, fill=T.AMBER)

    canvas.rect(40, 566, 880, 210, fill=T.BG2, stroke=T.VIOLET, rx=8)
    canvas.text(56, 596, "判据  先看波形，再做读回", size=15, fill=T.VIOLET, weight="700")
    rows = [
        ("CCR 只管占空比，频率由 PSC / ARR 定", T.TEXT),
        ("TIM1 还要 BDTR bit 15 MOE = 1（偏移 0x44，复位 0x0000）；TIM3 没有 MOE", T.AMBER),
        ("读回顺序：PSC → ARR → CCER → CRL，按这个顺序对数", T.TEXT),
        ("一次只动一个环：三个数一起改，就不知道错的是谁", T.GREEN),
        ("不证明：CCR 占空比、探头地线、以及第 08 章是否把 PA6 用作 SPI1_MISO", T.MUTED),
    ]
    for i, (line, c) in enumerate(rows):
        canvas.text(56, 626 + i * 28, line, size=13, fill=c)

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

# -*- coding: utf-8 -*-
"""EXTI-to-ISR four-gate plate (ch10).

Facts pinned to the chapter: SYSCFG 0x40013800 selects the port for EXTI0,
EXTI 0x40013C00 has IMR/RTSR/FTSR/PR, NVIC 0xE000E100 uses ISER bit and IP
byte 0xE000E406 for EXTI0, IRQn 6 maps to vector slot 22 (offset 0x58), and
EXTI_PR is cleared by writing 1.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hd import *  # noqa: E402,F401,F403


def _gate(f, x, y, w, h, title, lines, color):
    f.rect(x, y, w, h, color=color, fill=WHITE, sw=2.4)
    f.htext(x + 12, y + 30, title, size=20, color=color, weight="bold")
    for i, ln in enumerate(lines):
        f.text(x + 12, y + 56 + i * 24, ln, size=14, color=INK)


def exti_chain():
    f = Fig("arch-exti-chain", "从引脚到 ISR / four gates")

    # address lanes
    ax, ay, aw, ah = 48, 120, 1056, 88
    f.rect(ax, ay, aw, ah, color=BLUE_D, fill=PAPER, sw=2.6)
    f.text(ax + 14, ay + 28, "外设侧（APB2）", size=17, color=BLUE_D,
           weight="bold")
    f.text(ax + 14, ay + 54, "SYSCFG 0x40013800", size=15, color=INK)
    f.text(ax + 230, ay + 54, "EXTI 0x40013C00", size=15, color=INK)
    f.text(ax + 610, ay + 28, "内核侧（SCS）", size=17, color=GREEN_D,
           weight="bold")
    f.text(ax + 610, ay + 54, "NVIC 0xE000E100", size=15, color=INK)
    f.text(ax + 830, ay + 54, "SCB 0xE000ED00", size=15, color=INK)

    # four gates
    gy, gh = 240, 170
    gap = 24
    gw = 240
    gates = [
        ("① SYSCFG", ["EXTICR2[11:8] = 0x5", "PF6 → EXTI6"], AMBER_STROKE),
        ("② EXTI", ["IMR bit6 开线", "RTSR/FTSR 选沿", "PR bit6 挂起"], BLUE_D),
        ("③ NVIC", ["ISER0 bit23 放行", "IP[23] @0xE000E417", "IRQn = 23"], GREEN_D),
        ("④ ISR", ["EXTI9_5_IRQHandler", "查 PR bit6，写 1 清", "0~4 才有专属向量"], RED),
    ]
    x = 64
    for i, (title, lines, c) in enumerate(gates):
        _gate(f, x, gy, gw, gh, title, lines, c)
        if i < 3:
            f.arrow(x + gw + 2, gy + gh / 2, x + gw + gap - 2, gy + gh / 2,
                    color=INK, sw=2.4, bend=0.0)
        x += gw + gap

    # address formula
    fx, fy, fw, fh = 48, 446, 1056, 130
    f.rect(fx, fy, fw, fh, color=AMBER_STROKE, fill=WHITE, sw=2.6)
    f.htext(fx + 14, fy + 30, "名字对不上，中断就停在死循环", size=21,
            color=AMBER_STROKE, weight="bold")
    f.text(fx + 16, fy + 64,
           "IRQn 23 → 向量槽 39（39×4 = 0x9C）→ ISER[0] bit23 → IP 字节 0xE000E417",
           size=16, color=INK)
    f.text(fx + 16, fy + 94,
           "EXTI6 没有专属向量：ISR 里先查 PR 的 bit6，再写 1 清挂起。", size=16, color=RED)

    f.htext(576, 650, "四道门缺一不可：前三道管进门，最后一道管收尾。",
            size=23, color=AMBER_STROKE, anchor="middle", weight="bold",
            hl=True, hl_fill=AMBER_FILL)
    f.text(576, 690, "忘了清 PR：中断持续挂起、反复进 ISR，不是进不来。",
           size=16, color=MUTED, anchor="middle")
    return f


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[2] / "assets" / "illustrations" / "handraw"
    save(exti_chain(), str(out / "arch-exti-chain.svg"))
    print("wrote arch-exti-chain.svg")

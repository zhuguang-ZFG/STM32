# -*- coding: utf-8 -*-
"""GD32 USART register-map plate (ch29).

Pinned to gd32f4xx_usart.h:51-60 as quoted in the chapter:
STAT0 0x00, DATA 0x04, BAUD 0x08, CTL0 0x0C, CTL1 0x10,
CTL2 0x14, GP 0x18, plus STAT1 0x88.
Also records USART0 base 0x40011000 on APB2, not APB1+0x4400.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hd import *  # noqa: E402,F401,F403


def _row(f, y, role, stm, gd, color=INK, stm_color=MUTED, gd_color=INK):
    f.line(68, y + 40, 1084, y + 40, color=GRAY_FILL, sw=1.4, amp=0.5)
    f.text(74, y + 26, role, size=18, color=INK)
    f.text(322, y + 26, stm, size=18, color=stm_color)
    f.text(672, y + 26, gd, size=18, color=gd_color, weight="bold")


def usart_map():
    f = Fig("arch-usart-rename-map",
            "GD32 USART：改名，不改偏移 / same offsets, new names")

    px, py, pw, ph = 48, 120, 1036, 514
    f.rect(px, py, pw, ph, color=BLUE_D, fill=PAPER, sw=3.0)
    f.text(74, py + 38, "职责", size=19, color=BLUE_D, weight="bold")
    f.text(322, py + 38, "STM32F407（RM0090）", size=19, color=BLUE_D,
           weight="bold")
    f.text(672, py + 38, "GD32F4xx（上游 @10d02f4）", size=19, color=BLUE_D,
           weight="bold")
    f.line(68, py + 52, 1084, py + 52, color=INK, sw=2.0, amp=0.8)

    rows = [
        ("状态", "SR      @0x00", "STAT0   @0x00", BLUE_D),
        ("数据", "DR      @0x04", "DATA    @0x04", BLUE_D),
        ("波特率", "BRR     @0x08", "BAUD    @0x08", BLUE_D),
        ("使能 / 帧 / 中断", "CR1     @0x0C", "CTL0    @0x0C", BLUE_D),
        ("停止位 / 时钟", "CR2     @0x10", "CTL1    @0x10", BLUE_D),
        ("流控 / DMA", "CR3     @0x14", "CTL2    @0x14", BLUE_D),
        ("保护 / 预分频", "GTPR    @0x18", "GP      @0x18", BLUE_D),
        ("额外状态", "—", "STAT1   @0x88", GREEN_D),
    ]
    y = py + 64
    for role, stm, gd, c in rows:
        _row(f, y, role, stm, gd, gd_color=c)
        y += 52
    f.text(74, py + ph - 18,
           "偏移逐项相同；名字换了，另多一个 STAT1@0x88。", size=16,
           color=MUTED)

    # anchors
    ax, ay, aw, ah = 48, 654, 620, 82
    f.rect(ax, ay, aw, ah, color=AMBER_STROKE, fill=WHITE, sw=2.6)
    f.htext(ax + 16, ay + 32, "记忆锚点", size=22, color=AMBER_STROKE,
            weight="bold")
    f.text(ax + 16, ay + 62,
           "0x00 状态、0x04 数据、0x08 波特率、0x0C 控制 1；名字换、位置不换。", size=17, color=INK)

    bx, by, bw, bh = 690, 654, 394, 82
    f.rect(bx, by, bw, bh, color=RED, fill=WHITE, sw=2.6)
    f.text(bx + 16, by + 28, "基址也别记反", size=20, color=RED,
           weight="bold")
    f.text(bx + 16, by + 56, "USART0 = 0x40011000（APB2）", size=17,
           color=INK, weight="bold")
    f.text(bx + 16, by + 76, "0x40004400 是 USART1。", size=15, color=MUTED)

    return f


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[2] / "assets" / "illustrations" / "handraw"
    save(usart_map(), str(out / "arch-usart-rename-map.svg"))
    print("wrote arch-usart-rename-map.svg")

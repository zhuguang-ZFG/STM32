# -*- coding: utf-8 -*-
"""GD32 RCU clock-tree plate (ch29).

Facts pinned to the chapter: 200M profile uses PSC=25 / N=400 / P=2 / Q=9,
VCO 400 MHz, SYSCLK 200 MHz; PLL1/PLL2 are configured and enabled but are not
in the clock path; the official default is 168 MHz and 200M requires a preset
function; CK48M has three sources and PLLQ=400/9 is about 44.4 MHz, not 48.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hd import *  # noqa: E402,F401,F403


def _node(f, x, y, w, h, title, lines, color, size=20, body=16):
    f.rect(x, y, w, h, color=color, fill=WHITE, sw=2.4)
    f.text(x + 14, y + size + 6, title, size=size, color=color,
           weight="bold")
    for i, ln in enumerate(lines):
        f.text(x + 14, y + size + 34 + i * (body * 1.4), ln,
               size=body, color=INK)


def rcu_tree():
    f = Fig("arch-rcu-tree", "GD32 RCU 时钟树 / same skeleton, new names")

    # sources
    _node(f, 48, 128, 238, 154, "时钟源",
          ["IRC16M  16 MHz", "HXTAL  25 MHz（板）", "8 MHz 分支另配"],
          AMBER_STROKE, size=22, body=17)

    # PLL
    _node(f, 382, 128, 330, 188, "PLL：200M 档三件套",
          ["PSC=25 / N=400", "P=2 / Q=9", "VCO = 25 MHz ÷ 25 × 400 = 400 MHz"],
          BLUE_D, size=21, body=17)
    f.htext(548, 280, "SYSCLK = 200 MHz", size=22, color=BLUE_D,
            anchor="middle", weight="bold", hl=True, hl_fill=AMBER_FILL)

    # SYSCLK + buses
    f.rect(760, 184, 104, 48, color=GREEN_D, fill=PAPER, sw=2.2)
    f.text(812, 214, "SYSCLK", size=17, color=GREEN_D, anchor="middle",
           weight="bold")
    _node(f, 900, 144, 204, 104, "AHB /1", ["HCLK = 200 MHz"],
          GREEN_D, size=20, body=17)
    _node(f, 900, 270, 204, 120, "APB1 · APB2",
          ["外设时钟两级", "分频在 RCU_CFG0"],
          GREEN_D, size=19, body=16)

    # main arrows
    f.arrow(288, 206, 378, 206, color=INK, sw=2.4, bend=0.0)
    f.arrow(714, 206, 756, 206, color=INK, sw=2.4, bend=0.0)
    f.arrow(866, 208, 896, 196, color=INK, sw=2.4, bend=-0.05)
    f.arrow(1002, 250, 1002, 266, color=INK, sw=2.2, bend=0.0)
    f.text(300, 192, "选源", size=15, color=MUTED)
    f.text(726, 192, "SCS", size=14, color=MUTED)
    f.text(874, 186, "HCLK", size=14, color=MUTED)

    # CK48M panel
    cx, cy, cw, ch = 48, 438, 624, 190
    f.rect(cx, cy, cw, ch, color=AMBER_STROKE, fill=PAPER, sw=2.8)
    f.htext(cx + 16, cy + 32, "CK48M：USB 不走 SYSCLK", size=23,
            color=AMBER_STROKE, weight="bold")
    f.text(cx + 18, cy + 56, "三源选一；PLLQ 不是 48 MHz 的保证。", size=15,
           color=MUTED)
    f.rect(cx + 18, cy + 72, 210, 34, color=RED, fill=WHITE, sw=2.0)
    f.text(cx + 30, cy + 94, "PLLQ    400/9 ≈ 44.4", size=15, color=RED,
           weight="bold")
    f.rect(cx + 18, cy + 110, 210, 34, color=BLUE_D, fill=WHITE, sw=2.0)
    f.text(cx + 30, cy + 132, "PLLSAIP    另算", size=15, color=BLUE_D,
           weight="bold")
    f.rect(cx + 18, cy + 148, 210, 34, color=GREEN_D, fill=WHITE, sw=2.0)
    f.text(cx + 30, cy + 170, "IRC48M    48 MHz", size=15, color=GREEN_D,
           weight="bold")
    _node(f, 342, cy + 82, 84, 58, "三选一", [], MUTED, size=17)
    _node(f, 458, cy + 82, 190, 58, "CK48M", ["48 MHz → USB"], BLUE_D,
          size=18, body=15)
    for yy in (cy + 89, cy + 127, cy + 165):
        f.arrow(cx + 230, yy, 338, yy, color=INK, sw=1.8, bend=0.0)
    f.arrow(428, cy + 111, 454, cy + 111, color=INK, sw=2.0, bend=0.0)
    f.text(cx + 18, cy + ch + 26,
           "Q=9 只有 44.4；48 要走 PLLSAIP 或 IRC48M。", size=16,
           color=RED)

    # PLL1/PLL2 decoy
    dx, dy, dw, dh = 700, 438, 404, 190
    f.rect(dx, dy, dw, dh, color=MUTED, fill=WHITE, sw=2.6, dash="7 5")
    f.text(dx + 16, dy + 32, "另例：8M 分支 PLL1/PLL2 配而不用", size=19, color=MUTED,
           weight="bold")
    f.text(dx + 16, dy + 66, "CFG1 写了 MUL20，PLL1EN/PLL2EN 也置了；", size=17,
           color=INK)
    f.text(dx + 16, dy + 94, "但它们不在时钟路径上。", size=17, color=INK)
    f.text(dx + 16, dy + 132, "别把「使能」读成「SYSCLK 来源」。", size=17,
           color=RED)
    f.line(dx + 16, dy + 154, dx + 360, dy + 154, color=MUTED, sw=1.8,
           dash="4 5", amp=0.8)

    # closing
    f.htext(576, 694, "默认档 168M；200M 是预设函数 + 宏，不是 SystemInit 默认。",
            size=21, color=AMBER_STROKE, anchor="middle", weight="bold",
            hl=True, hl_fill=AMBER_FILL)
    f.text(576, 734, "官方 system 文件全文不设 Flash 等待；WSCNT 4 位 + WSEN。",
           size=17, color=RED, anchor="middle")
    return f


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[2] / "assets" / "illustrations" / "handraw"
    save(rcu_tree(), str(out / "arch-rcu-tree.svg"))
    print("wrote arch-rcu-tree.svg")

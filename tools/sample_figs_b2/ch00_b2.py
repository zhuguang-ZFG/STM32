#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第 00 章 B2 静态图：学习闭环、验收三门槛、上板无现象三环排查。

静态矢量，无 CSS 动画、无 SMIL。面板内技术正文用英文，面板标题用「正常路径 / 失败路径 / 旁注」。
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


def _ring(canvas: Svg, cx: float, cy: float, num: str, color: str) -> None:
    canvas.circle(cx, cy, 15, fill=color, stroke=color, sw=1.5)
    canvas.text(cx, cy + 5, num, size=14, fill=T.BG, anchor="middle", weight="700")


def learn_loop() -> Svg:
    canvas = Svg(
        960,
        860,
        "学习闭环：读 RM0008 对应节、写最小代码、上板、逐行能解释；跳手册抄代码则停在不能解释",
        "STM32F103C8T6 · PC13 · RM0008 Rev 21 §9 GPIO / DS5319 Rev 20 Table 5",
    )
    canvas.header(tag="00", tag_color=T.CYAN)
    canvas.text(40, 86, "STM32F103C8T6  LQFP48  PC13 LED at 1 Hz, 500 ms per half period",
                size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "one register per turn: RCC_APB2ENR.IOPCEN, GPIOC_CRH[23:20], GPIOC_ODR[13]",
                size=14, fill=T.CYAN)
    canvas.text(40, 138, "the image lands at 0x08000000; BOOT0 = 0 is what makes this reset run it",
                size=14, fill=T.AMBER)

    canvas.text(40, 170, "正常路径  四步一轮，每一步都要被板上现象检验", size=16, fill=T.GREEN, weight="700")
    canvas.rect(40, 184, 880, 240, fill=T.PANEL, stroke=T.GREEN, rx=8)
    cards = (
        ("1  read one section", "RM0008 Rev 21 §9 GPIO", "IOPCEN, CRH, ODR", "one register per turn"),
        ("2  write 20 lines", "APB2ENR |= IOPCEN", "CRH[23:20] = 0x2", "ODR ^= ODR13"),
        ("3  put it on the board", "flash at 0x08000000", "BOOT0 = 0, PC13 toggles", "500 ms per half period"),
        ("4  explain each line", "why the clock comes first", "why 0x2 means push-pull", "why 500 ms is half a period"),
    )
    for i, (head, l1, l2, l3) in enumerate(cards):
        x = 40 + i * 210
        canvas.rect(x, 206, 190, 124, fill=T.BG, stroke=T.GREEN, rx=8)
        canvas.text(x + 12, 234, head, size=15, fill=T.GREEN, weight="700")
        canvas.text(x + 12, 262, l1, size=12, fill=T.MUTED)
        canvas.text(x + 12, 286, l2, size=12, fill=T.TEXT)
        canvas.text(x + 12, 310, l3, size=11, fill=T.MUTED)
    for x in (232, 442, 652):
        canvas.arrow(x, 268, x + 16, 268, color=T.GREEN, sw=2, head=7)
    canvas.line(765, 330, 765, 356, stroke=T.GREEN, sw=2)
    canvas.line(765, 356, 135, 356, stroke=T.GREEN, sw=2)
    canvas.arrow(135, 356, 135, 332, color=T.GREEN, sw=2, head=7)
    canvas.text(450, 382, "next register: the same four steps", size=12, fill=T.MUTED, anchor="middle")

    canvas.text(40, 452, "The loop closes only when step 4 can name every line it wrote.",
                size=14, fill=T.TEXT)

    canvas.text(40, 492, "失败路径  跳过手册，直接抄一个不能解释的工程", size=16, fill=T.RED, weight="700")
    canvas.rect(40, 506, 880, 150, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(56, 536, "Copy 200 lines, and the first broken build has no owner", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 564, "the board shows nothing, and no line of the copy names PC13", size=14, fill=T.RED)
    canvas.text(56, 590, "an unopened clock and an unwired pin look identical from the outside", size=14, fill=T.TEXT)
    canvas.text(56, 616, "step 4 fails first: the demo board still blinks, so the copy looks correct", size=14, fill=T.AMBER)
    canvas.text(56, 642, "searching the error text now buys a symptom, not a cause", size=13, fill=T.MUTED)

    canvas.rect(40, 672, 880, 120, fill=T.BG2, stroke=T.VIOLET, rx=8)
    canvas.text(56, 702, "旁注  one claim per turn keeps the loop honest", size=15, fill=T.VIOLET, weight="700")
    canvas.text(56, 728, "PC13 is on when low: LED lit means ODR13 = 0", size=14, fill=T.TEXT)
    canvas.text(56, 754, "1 Hz is a period; a single on or off proves nothing", size=14, fill=T.AMBER)
    canvas.text(56, 780, "clock tree and exception stack are other chapters, not this loop", size=13, fill=T.MUTED)
    _credit(canvas, "自绘。寄存器写法与 500 ms 半周期来自第 00 章；GPIO 章节与 Table 5 脚位来自 RM0008 Rev 21 第 9 章和 DS5319 Rev 20。")
    return canvas


def accept_gate() -> Svg:
    canvas = Svg(
        960,
        860,
        "第一份能验收的程序有三道门槛：编译 0 Error、板上有可见现象、逐行能解释；只看编译过不算验收",
        "STM32F103C8T6 · PC13 低电平点亮 · RM0008 Rev 21 §9 GPIO",
    )
    canvas.header(tag="00", tag_color=T.CYAN)
    canvas.text(40, 86, "STM32F103C8T6  one program, three gates: build, board, explanation",
                size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "gate 1 is a log file; gates 2 and 3 need the board in front of you",
                size=14, fill=T.CYAN)
    canvas.text(40, 138, "0 Error is necessary. It is not one of the two gates that use the board.",
                size=14, fill=T.AMBER)

    canvas.text(40, 170, "正常路径  三道门槛按顺序全过，才叫验收", size=16, fill=T.GREEN, weight="700")
    canvas.rect(40, 184, 880, 252, fill=T.PANEL, stroke=T.GREEN, rx=8)
    gates = (
        ("gate 1  build with 0 Error", "the .elf comes from STM32F103C8Tx_FLASH.ld and the flash tool writes 0x08000000",
         "the build log proves syntax and linking, not pins"),
        ("gate 2  the board shows it", "the PC13 LED completes one on/off cycle per second",
         "500 ms on plus 500 ms off is 1 s: count the time, not the brightness"),
        ("gate 3  every line is explainable", "why APB2ENR.IOPCEN is set before CRH is written",
         "why CRH[23:20] = 0x2 is 2 MHz push-pull, and why ODR13 toggles"),
    )
    for i, (head, d1, d2) in enumerate(gates):
        top = 196 + i * 80
        _ring(canvas, 74, top + 40, str(i + 1), T.GREEN)
        canvas.text(100, top + 34, head, size=15, fill=T.GREEN, weight="700")
        canvas.text(100, top + 58, d1, size=13, fill=T.TEXT)
        canvas.text(100, top + 76, d2, size=12, fill=T.MUTED)

    canvas.text(40, 478, "失败路径  只看编译过", size=16, fill=T.RED, weight="700")
    canvas.rect(40, 492, 880, 164, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(56, 522, "0 Error and nothing else", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 550, "the LED never moves and no waveform appears on PC13", size=14, fill=T.RED)
    canvas.text(56, 576, "a clean build says nothing about BOOT0, a wire, or the 500 ms", size=14, fill=T.TEXT)
    canvas.text(56, 602, "gates 2 and 3 need the board in front of you; a log cannot supply them", size=14, fill=T.AMBER)
    canvas.text(56, 628, "the build is the only gate that fails out loud", size=13, fill=T.MUTED)

    canvas.rect(40, 672, 880, 118, fill=T.BG2, stroke=T.VIOLET, rx=8)
    canvas.text(56, 702, "旁注  a gate is a yes or no, not a feeling", size=15, fill=T.VIOLET, weight="700")
    canvas.text(56, 728, "PC13 is on when low: lit means ODR13 = 0", size=14, fill=T.TEXT)
    canvas.text(56, 754, "a logic analyzer shows the 1 s period; the eye only sees blinking", size=14, fill=T.AMBER)
    canvas.text(56, 780, "the four-gate ladder in the hands-on section adds flash, reset, and measurement", size=13, fill=T.MUTED)
    _credit(canvas, "自绘。PC13 低电平点亮与 500 ms 半周期来自第 00 章；CRH / ODR 与 GPIO 时钟来自 RM0008 Rev 21 第 9 章。")
    return canvas


def boot_triage() -> Svg:
    canvas = Svg(
        960,
        970,
        "上板无现象时按供电、BOOT0、SWDIO/SWCLK 三环依次排查，第一环不通过就不改代码",
        "STM32F103C8T6 LQFP48 · DS5319 Rev 20 Table 5 / RM0008 Rev 21 Table 9",
    )
    canvas.header(tag="00", tag_color=T.CYAN)
    canvas.text(40, 86, "STM32F103C8T6  LQFP48  three rings, stop at the first one that fails",
                size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "ring 1 supply    ring 2 BOOT0    ring 3 SWDIO / SWCLK",
                size=14, fill=T.CYAN)
    canvas.text(40, 138, "pin 34 PA13 = SWDIO    pin 37 PA14 = SWCLK    pin 44 = BOOT0    pin 7 = NRST",
                size=14, fill=T.AMBER)

    canvas.text(40, 170, "正常路径  先量电，再看 BOOT0，最后才接探针", size=16, fill=T.GREEN, weight="700")

    canvas.rect(40, 184, 880, 138, fill=T.PANEL, stroke=T.GREEN, rx=8)
    _ring(canvas, 78, 218, "1", T.GREEN)
    canvas.text(108, 214, "ring 1  supply: 3.3 V between VDD and VSS, measured at the MCU", size=15, fill=T.TEXT, weight="700")
    canvas.text(108, 244, "one source only: Micro-USB; the clone ST-Link 3V3 stays unconnected", size=14, fill=T.GREEN)
    canvas.text(108, 270, "a reading at the USB plug does not prove the MCU pin sees 3.3 V", size=14, fill=T.TEXT)
    canvas.arrow(78, 322, 78, 338, color=T.GREEN, sw=2, head=7)

    canvas.rect(40, 338, 880, 120, fill=T.PANEL, stroke=T.GREEN, rx=8)
    _ring(canvas, 78, 372, "2", T.GREEN)
    canvas.text(108, 368, "ring 2  boot: pin 44 BOOT0 = 0", size=15, fill=T.TEXT, weight="700")
    canvas.text(108, 396, "0x00000000 then aliases Flash at 0x08000000; the 4th SYSCLK edge latches it", size=14, fill=T.GREEN)
    canvas.text(108, 422, "setting BOOT0 inside main means this reset already took the other path", size=14, fill=T.TEXT)
    canvas.arrow(78, 458, 78, 474, color=T.GREEN, sw=2, head=7)

    canvas.rect(40, 474, 880, 120, fill=T.PANEL, stroke=T.GREEN, rx=8)
    _ring(canvas, 78, 508, "3", T.GREEN)
    canvas.text(108, 504, "ring 3  debug: pin 34 SWDIO, pin 37 SWCLK, common ground", size=15, fill=T.TEXT, weight="700")
    canvas.text(108, 532, "pin 7 NRST is optional and enables connect-under-reset", size=14, fill=T.GREEN)
    canvas.text(108, 558, "pin 35 is VSS_2; a probe parked there has no clock", size=14, fill=T.TEXT)

    canvas.text(40, 626, "失败路径  跳过前两环，直接在代码里找原因", size=16, fill=T.RED, weight="700")
    canvas.rect(40, 640, 880, 146, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(56, 670, "BOOT0 = 1 and BOOT1 = 0: the CPU runs 0x1FFFF000", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 698, "the image is in Flash and looks as if it was never programmed", size=14, fill=T.RED)
    canvas.text(56, 724, "3.3 V read at the plug while the MCU pin reads 0 V", size=14, fill=T.AMBER)
    canvas.text(56, 750, "a probe on pin 35 VSS_2 instead of pin 37 SWCLK: no clock, no target", size=14, fill=T.TEXT)
    canvas.text(56, 772, "-O2 does not move a boot pin or close a missing ground", size=13, fill=T.MUTED)

    canvas.rect(40, 802, 880, 120, fill=T.BG2, stroke=T.VIOLET, rx=8)
    canvas.text(56, 832, "旁注  three rings in this order, and stop at the first failure", size=15, fill=T.VIOLET, weight="700")
    canvas.text(56, 858, "pin 35 VSS_2 and pin 36 VDD_2 sit between the two SWD pins", size=14, fill=T.TEXT)
    canvas.text(56, 884, "a probe that sees no target is still ring 3, not a program bug", size=13, fill=T.MUTED)
    _credit(canvas, "自绘。脚位来自 DS5319 Rev 20 表 5；0x1FFFF000 与第 4 个 SYSCLK 上升沿来自 RM0008 Rev 21 表 9。")
    return canvas


FIGURES = [
    ("sample-00-learn-loop.svg", learn_loop),
    ("sample-00-accept-gate.svg", accept_gate),
    ("sample-00-boot-triage.svg", boot_triage),
]


def main() -> None:
    out_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join("assets", "diagrams")
    os.makedirs(out_dir, exist_ok=True)
    for name, fn in FIGURES:
        fn().save(os.path.join(out_dir, name))


if __name__ == "__main__":
    main()

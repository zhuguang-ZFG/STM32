#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Chapter 02 B2 figures: the HSE-stall ledger and the BOOT0/BOOT1 alias.

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


def hse_fail() -> Svg:
    canvas = Svg(
        960,
        900,
        "HSE 停振后 SYSCLK 落在 HSI 8 MHz：115200 变 12800，1 ms 变 9 ms",
        "STM32F103C8T6 LQFP48 · RM0008 Rev 21 §7.3.2",
    )
    canvas.header(tag="02", tag_color=T.CYAN)
    canvas.text(40, 86, "STM32F103C8T6  LQFP48  HSE 8 MHz on pin 5 PD0 / pin 6 PD1", size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "PLLXTPRE=0  PLLSRC=1  PLLMUL=0111  8 MHz x 9 = 72 MHz", size=14, fill=T.CYAN)
    canvas.text(40, 138, "72 MHz: SYSCLK = HCLK = PCLK2, PCLK1 = 36 MHz, LATENCY = 2, USART1 BRR = 0x271", size=14, fill=T.AMBER)

    canvas.text(40, 170, "正常路径  the 72 MHz ledger adds up", size=16, fill=T.GREEN, weight="700")
    canvas.rect(40, 184, 880, 150, fill=T.PANEL, stroke=T.GREEN, rx=8)
    canvas.text(56, 214, "USART1 at 115200: 72e6 / (16 x 115200) = 39.0625, BRR 0x271, error 0%", size=14, fill=T.TEXT, weight="700")
    canvas.text(56, 240, "SysTick reload 72000 at 72 MHz is 1.000 ms", size=14, fill=T.GREEN)
    canvas.text(56, 266, "RCC_CR HSERDY = 1 and PLLRDY = 1; RCC_CFGR SWS = 10 means the PLL drives SYSCLK", size=14, fill=T.TEXT)
    canvas.text(56, 292, "LATENCY = 2 is the 48 to 72 MHz row, 2.7 V to 3.6 V; 24 to 48 MHz is 1 and below 24 MHz is 0", size=13, fill=T.MUTED)
    canvas.text(56, 318, "this row is what the code was written against; nothing below re-tunes it", size=13, fill=T.MUTED)

    canvas.text(40, 380, "失败路径  HSE stops, CSS falls back to HSI 8 MHz", size=16, fill=T.RED, weight="700")
    canvas.rect(40, 394, 880, 150, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(56, 424, "SYSCLK drops to 8 MHz, SWS reads 00, the PLL is off, the NMI keeps firing", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 450, "the same BRR 0x271 now divides 8 MHz: 8e6 / (16 x 39.0625) = 12800 baud", size=14, fill=T.RED)
    canvas.text(56, 476, "115200 to 12800 is exactly one ninth, 88.9% slow; the receiver reports framing errors", size=14, fill=T.RED)
    canvas.text(56, 502, "SysTick reload 72000 becomes 9.000 ms, so a delay written as 1 s takes 9 s", size=14, fill=T.AMBER)
    canvas.text(56, 528, "none of this is a baud rounding problem; it is the wrong clock behind a correct divider", size=13, fill=T.MUTED)

    canvas.text(40, 588, "检查点  read these three before touching the code", size=16, fill=T.CYAN, weight="700")
    canvas.rect(40, 602, 880, 150, fill=T.PANEL, stroke=T.CYAN, rx=8)
    canvas.text(56, 632, "RCC_CR bit 17 HSERDY: 0 means the crystal never started, so PLLMUL never gets an input", size=14, fill=T.TEXT, weight="700")
    canvas.text(56, 658, "RCC_CFGR [21:18] PLLMUL = 0111, [17] PLLXTPRE = 0, [16] PLLSRC = 1, [3:2] SWS = 10", size=14, fill=T.TEXT)
    canvas.text(56, 684, "FLASH_ACR [2:0] LATENCY = 2 in this band; 8 MHz alone would only need 0", size=14, fill=T.TEXT)
    canvas.text(56, 710, "a 2.7 V rail and a probe on PD0 are worth more than one more build", size=13, fill=T.MUTED)

    canvas.rect(40, 782, 880, 70, fill=T.BG2, stroke=T.VIOLET, rx=8)
    canvas.text(56, 812, "旁注  8 MHz is the reset clock, not a repaired 72 MHz", size=15, fill=T.VIOLET, weight="700")
    canvas.text(56, 838, "write CSSC in the NMI or the handler re-enters forever; LATENCY 2 at 8 MHz is safe but proves nobody recomputed", size=13, fill=T.MUTED)

    _credit(canvas, "自绘。分频与等待来自 RM0008 Rev 21 第 7.3.2 节；BRR 39.0625 与 0x271 来自第 06 章；64 KB 与脚位来自 DS5319 Rev 20。")
    return canvas


def boot_mode() -> Svg:
    canvas = Svg(
        960,
        920,
        "BOOT0=1 且 BOOT1=1 从 SRAM 起：取到的是上电随机内容",
        "STM32F103C8T6 LQFP48 · RM0008 Rev 21 §3.4 Table 9",
    )
    canvas.header(tag="02", tag_color=T.CYAN)
    canvas.text(40, 86, "STM32F103C8T6  LQFP48  pin 44 BOOT0, BOOT1 shared with PB2", size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "the pair is latched on the 4th rising edge of SYSCLK after reset", size=14, fill=T.CYAN)
    canvas.text(40, 138, "0x00000000 is only an alias: bodies sit at 0x08000000, 0x1FFFF000 and 0x20000000", size=14, fill=T.AMBER)

    canvas.text(40, 170, "正常路径  BOOT1 = 0, BOOT0 = 0, main Flash", size=16, fill=T.GREEN, weight="700")
    canvas.rect(40, 184, 880, 150, fill=T.PANEL, stroke=T.GREEN, rx=8)
    canvas.text(56, 214, "0x00000000 aliases the 64 KB image at 0x08000000, which ends at 0x08010000", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 240, "word 0 is the initial MSP, word 1 is Reset_Handler, and only then does main run", size=14, fill=T.GREEN)
    canvas.text(56, 266, "SWD programming and a normal power-up both leave BOOT0 low", size=14, fill=T.TEXT)
    canvas.text(56, 292, "the image cannot change this: the pin decides, the linker script only places bytes", size=13, fill=T.MUTED)

    canvas.text(40, 380, "失败路径  BOOT1 = 1, BOOT0 = 1, SRAM", size=16, fill=T.RED, weight="700")
    canvas.rect(40, 394, 880, 150, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(56, 424, "0x00000000 aliases SRAM at 0x20000000, 20 KB up to 0x20005000", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 450, "word 0 is power-on SRAM: that is not a stack top, and word 1 is not code", size=14, fill=T.RED)
    canvas.text(56, 476, "execution never reaches main: the core faults or jumps wild", size=14, fill=T.RED)
    canvas.text(56, 502, "the image in Flash is intact at 0x08000000 and simply not fetched", size=14, fill=T.AMBER)
    canvas.text(56, 528, "SRAM loses everything at power-down, so this is a debug state, not a delivery", size=13, fill=T.MUTED)

    canvas.text(40, 588, "对照  the three rows behind the alias", size=16, fill=T.CYAN, weight="700")
    canvas.rect(40, 602, 880, 120, fill=T.PANEL, stroke=T.CYAN, rx=8)
    canvas.text(56, 632, "BOOT1=0  BOOT0=0    main Flash at 0x08000000, the case that runs the book", size=14, fill=T.GREEN)
    canvas.text(56, 658, "BOOT1=0  BOOT0=1    system memory at 0x1FFFF000, the factory UART ISP loader", size=14, fill=T.TEXT)
    canvas.text(56, 684, "BOOT1=1  BOOT0=1    SRAM at 0x20000000, RAM content only, gone at power-down", size=14, fill=T.RED)
    canvas.text(56, 710, "0x1FFFB000 belongs to the interconnect line and 0x08080000 to XL density; neither is this C8", size=13, fill=T.MUTED)

    canvas.text(40, 770, "检查点  three readings before the next reset", size=16, fill=T.VIOLET, weight="700")
    canvas.rect(40, 784, 880, 100, fill=T.BG2, stroke=T.VIOLET, rx=8)
    canvas.text(56, 814, "meter pin 44 and PB2 with reset held: 1 and 1 is the SRAM alias, not Flash", size=14, fill=T.TEXT, weight="700")
    canvas.text(56, 840, "read 0x00000000 over SWD: a sane MSP lands inside 0x20000000 to 0x20005000", size=14, fill=T.TEXT)
    canvas.text(56, 866, "setting BOOT pins inside main is one reset too late", size=13, fill=T.MUTED)

    _credit(canvas, "自绘。启动区别名与锁存点来自 RM0008 Rev 21 第 3.4 节表 9；脚位与 64 KB / 20 KB 来自 DS5319 Rev 20。")
    return canvas


FIGURES = [
    ("sample-02-hse-fail.svg", hse_fail),
    ("sample-02-boot-mode.svg", boot_mode),
]


def main(argv: list[str]) -> int:
    out_dir = argv[1] if len(argv) > 1 else os.path.join(os.getcwd(), ".temp", "b2ch02")
    os.makedirs(out_dir, exist_ok=True)
    for name, builder in FIGURES:
        path = builder().save(os.path.join(out_dir, name))
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

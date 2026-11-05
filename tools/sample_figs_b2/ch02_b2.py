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
    """同一份分频账，两种时钟：72 MHz 对得上，8 MHz 全错档。

    画的是字段与算式，不是波形；每个数字都能在章节正文里找到出处。
    """
    c = Svg(
        960,
        720,
        "HSE 停振后 SYSCLK 落在 HSI 8 MHz：115200 变 12800，1 ms 变 9 ms",
        "STM32F103C8T6 LQFP48 · RM0008 Rev 21 §7.3.2",
    )
    c.header(tag="02", tag_color=T.CYAN)

    # ---- 正常路径：HSE → PLL ×9 → 72 MHz ----
    c.text(40, 94, "正常：HSE 8 MHz 经 PLL ×9 上到 72 MHz", size=17,
           fill=T.GREEN, weight="700")
    c.box(40, 112, 162, 56, "HSE 8 MHz", "PD0/PD1 · 5/6 脚", stroke=T.GREEN)
    c.arrow(204, 140, 236, 140, color=T.GREEN)
    c.box(238, 112, 172, 56, "PLL ×9", "PLLMUL=0111 · PLLSRC=1",
          stroke=T.GREEN)
    c.arrow(412, 140, 444, 140, color=T.GREEN)
    c.box(446, 112, 190, 56, "SYSCLK 72 MHz", "SWS=10 · HCLK 72 MHz",
          stroke=T.GREEN)
    c.box(672, 96, 268, 46, "USART1 → 115200",
          "72e6/(16×115200)=39.0625 · BRR 0x271", stroke=T.GREEN, size=13)
    c.box(672, 152, 268, 46, "SysTick 重装 72000", "→ 1.000 ms",
          stroke=T.GREEN, size=13)
    c.box(672, 208, 268, 46, "FLASH LATENCY=2", "48–72 MHz 档，配得上",
          stroke=T.GREEN, size=13)
    for yy in (119, 175, 231):
        c.arrow(638, 140, 670, yy, color=T.GREEN, sw=1.5, head=6)

    c.line(40, 286, 920, 286, stroke=T.GRID, sw=1)

    # ---- 失败路径：CSS 切 HSI，同一份分频全错档 ----
    c.text(40, 318, "停振：CSS 把 SYSCLK 切到 HSI 8 MHz，分频一个没改", size=17,
           fill=T.RED, weight="700")
    c.box(40, 336, 162, 56, "HSE 停振", "HSERDY=0", stroke=T.RED,
          color=T.RED)
    # 交叉线画在方框右上角，比在框内写 ✗ 更清楚，也不压住框里的字
    c.line(168, 340, 186, 358, stroke=T.RED, sw=2)
    c.line(186, 340, 168, 358, stroke=T.RED, sw=2)
    c.arrow(204, 364, 236, 364, color=T.RED, dash="5 3")
    c.text(220, 350, "CSS", size=11, fill=T.RED, anchor="middle")
    c.box(238, 336, 172, 56, "HSI 8 MHz", "内部 RC · 上电默认", stroke=T.RED)
    c.arrow(412, 364, 444, 364, color=T.RED)
    c.box(446, 336, 190, 56, "SYSCLK 8 MHz", "SWS=00 · PLL 已关", stroke=T.RED,
          color=T.RED)
    c.box(672, 320, 268, 46, "同一份 0x271 → 12800",
          "8e6/(16×39.0625) · 慢 88.9%", stroke=T.RED, color=T.RED, size=13)
    c.box(672, 376, 268, 46, "SysTick 72000 → 9.000 ms",
          "代码写 1 s，实际 9 s", stroke=T.RED, color=T.RED, size=13)
    c.box(672, 432, 268, 46, "LATENCY=2 仍生效",
          "8 MHz 只需 0，没人重算", stroke=T.RED, color=T.RED, size=13)
    for yy in (343, 399, 455):
        c.arrow(638, 364, 670, yy, color=T.RED, sw=1.5, head=6)

    # ---- 9 倍差：同一份分频，两根长度 ----
    c.text(40, 512, "115200 与 12800 是同一份分频，差 9 倍；不是波特率凑不出来",
           size=13, fill=T.MUTED)
    c.rect(40, 522, 560, 16, fill=T.PANEL, stroke=T.GREEN, rx=4)
    c.rect(40, 522, 560, 16, fill=T.GREEN, opacity=0.22, rx=4)
    c.text(610, 535, "115200（72 MHz）", size=11, fill=T.GREEN)
    c.rect(40, 550, 62, 16, fill=T.PANEL, stroke=T.RED, rx=4)
    c.rect(40, 550, 62, 16, fill=T.RED, opacity=0.22, rx=4)
    c.text(610, 563, "12800（8 MHz，÷9）", size=11, fill=T.RED)

    # ---- 检查点：三个寄存器读数 + 处置 ----
    c.text(40, 600, "检查点：三个读数，先定住时钟，再谈波特率", size=15,
           fill=T.CYAN, weight="700")
    c.box(40, 612, 200, 50, "RCC_CR[17] HSERDY", "0 = 晶振没起振", stroke=T.CYAN,
          size=12)
    c.box(252, 612, 200, 50, "RCC_CFGR[3:2] SWS", "00 = 系统跑在 HSI", stroke=T.CYAN,
          size=12)
    c.box(464, 612, 200, 50, "FLASH_ACR[2:0]", "2 仍生效，8 MHz 只需 0",
          stroke=T.CYAN, size=12)
    c.box(676, 612, 264, 50, "NMI 里写 CSSC", "否则 NMI 一直重进",
          stroke=T.VIOLET, color=T.VIOLET, size=12)

    _credit(c, "自绘。倍频与等待周期来自 RM0008 Rev 21 第 7.3.2 节；BRR 39.0625 与 0x271 来自第 06 章；引脚与容量来自 DS5319 Rev 20。")
    return c


def boot_mode() -> Svg:
    """BOOT1/BOOT0 决定 0x00000000 别名到哪块本体，三个组合画成开关而不是句子。"""
    c = Svg(
        960,
        620,
        "BOOT0=1 且 BOOT1=1 从 SRAM 起：取到的是上电随机内容",
        "STM32F103C8T6 LQFP48 · RM0008 Rev 21 §3.4 Table 9",
    )
    c.header(tag="02", tag_color=T.CYAN)

    c.text(40, 92, "0x00000000 只是别名：取指来源由 BOOT0 / BOOT1 决定", size=17,
           fill=T.TEXT, weight="700")
    c.box(40, 116, 158, 46, "BOOT0 · 第 44 脚", "复位期间量这一脚", stroke=T.AMBER,
          size=12)
    c.box(40, 176, 158, 46, "BOOT1 = PB2", "与 GPIO 共脚", stroke=T.AMBER,
          size=12)
    c.arrow(200, 139, 230, 155, color=T.AMBER)
    c.arrow(200, 199, 230, 183, color=T.AMBER)
    c.box(232, 130, 176, 78, "启动选择", "复位后按这两脚取指", stroke=T.VIOLET,
          size=13)

    c.box(468, 104, 452, 50, "主 Flash · 0x0800 0000",
          "64 KB 到 0x0801 0000 · 第 0 字 MSP，第 1 字 Reset_Handler",
          stroke=T.GREEN, size=13)
    c.box(468, 166, 452, 50, "系统存储器 · 0x1FFF F000",
          "出厂 Bootloader · 串口 ISP 下载", stroke=T.AMBER, size=13)
    c.box(468, 228, 452, 50, "内置 SRAM · 0x2000 0000",
          "20 KB 到 0x2000 5000 · 上电随机内容", stroke=T.RED, size=13)
    for yy in (129, 191, 253):
        c.arrow(410, 169, 466, yy, color=T.VIOLET, sw=1.5, head=6)

    c.text(40, 312, "三种组合：BOOT0=0 时 BOOT1 随便（x）", size=14,
           fill=T.MUTED, weight="700")
    rows = [
        ("0", "0", "主 Flash · 正常运行", T.GREEN),
        ("0", "1", "系统存储器 · 串口 ISP 救砖", T.AMBER),
        ("1", "1", "内置 SRAM · 上电随机，掉电即失", T.RED),
    ]
    for i, (b1, b0, label, col) in enumerate(rows):
        y = 330 + i * 54
        c.text(40, y + 20, "BOOT1", size=11, fill=T.DIM, mono=True)
        c.box(88, y, 44, 30, b1, "", stroke=col, size=13)
        c.text(148, y + 20, "BOOT0", size=11, fill=T.DIM, mono=True)
        c.box(196, y, 44, 30, b0, "", stroke=col, size=13)
        c.arrow(246, y + 15, 276, y + 15, color=col, sw=1.5, head=6)
        c.box(278, y, 420, 30, label, "", stroke=col, color=col, size=12)

    c.text(40, 520, "检查点：三处读数，比再烧一次快", size=15, fill=T.CYAN,
           weight="700")
    c.box(40, 532, 268, 50, "复位期间量第 44 脚", "1 且 PB2 = 1 → 落到 SRAM",
          stroke=T.CYAN, size=12)
    c.box(324, 532, 268, 50, "读 0x00000000 的第 0 字", "落进 0x2000 0000 段才对",
          stroke=T.CYAN, size=12)
    c.box(608, 532, 312, 50, "运行中改 BOOT 引脚", "要等下一次复位才生效",
          stroke=T.VIOLET, color=T.VIOLET, size=12)

    _credit(c, "自绘。启动区别名与选择表来自 RM0008 Rev 21 第 3.4 节表 9；引脚与 64 KB / 20 KB 来自 DS5319 Rev 20。")
    return c


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

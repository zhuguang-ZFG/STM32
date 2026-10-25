#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Static key figures for the two sample chapters. No CSS animation and no SMIL."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from svgkit import Svg, T

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _credit(canvas: Svg, note: str) -> None:
    canvas.line(24, canvas.h - 36, canvas.w - 24, canvas.h - 36, stroke=T.GRID, sw=1)
    canvas.text(24, canvas.h - 16, note, size=11, fill=T.MUTED)
    canvas.text(canvas.w - 24, canvas.h - 16, "自绘 · 静态 · CC BY 4.0", size=11, fill=T.DIM, anchor="end")


def boot_state() -> Svg:
    canvas = Svg(
        960,
        620,
        "BOOT0=0 取到刚烧入的闪存；BOOT0=1 取到系统存储器",
        "STM32F103C8T6 · RM0008 Rev 21 §3.4 Table 9",
    )
    canvas.header(tag="00", tag_color=T.CYAN)
    canvas.text(40, 88, "正常路径  BOOT1=x  BOOT0=0", size=16, fill=T.GREEN, weight="700")
    steps = [
        (40, "main.c", "源文件"),
        (230, ".elf", "STM32F103C8Tx_FLASH.ld"),
        (460, "SWDIO / SWCLK", "写入 0x08000000"),
        (700, "0x00000000", "别名到主闪存"),
    ]
    for left, title, sub in steps:
        canvas.rect(left, 108, 180, 78, fill=T.PANEL, stroke=T.GREEN, rx=8)
        canvas.text(left + 12, 140, title, size=14, fill=T.TEXT, weight="700")
        canvas.text(left + 12, 164, sub, size=11, fill=T.MUTED)
    canvas.text(40, 214, "第 4 个 SYSCLK 上升沿锁存 BOOT 脚，然后 CPU 读 0x00000000 与 0x00000004", size=14, fill=T.TEXT)
    canvas.text(40, 268, "失败路径  BOOT1=0  BOOT0=1", size=16, fill=T.RED, weight="700")
    canvas.rect(40, 284, 880, 130, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(56, 316, "烧录仍然写在 0x08000000，程序还在闪存里", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 344, "CPU 从 0x00000000 取到的是系统存储器别名，不是这颗闪存", size=14, fill=T.AMBER)
    canvas.text(56, 370, "STM32F103C8T6 的系统存储器在 0x1FFFF000", size=14, fill=T.TEXT)
    canvas.text(56, 396, "互联型 0x1FFFB000 与 XL 密度 Bank2 的 0x08080000 对这颗料作废", size=13, fill=T.MUTED)
    canvas.rect(40, 434, 880, 110, fill=T.BG2, stroke=T.STROKE, rx=8)
    canvas.text(56, 466, "信号名", size=14, fill=T.CYAN, weight="700")
    canvas.text(56, 492, "SWDIO = PA13     SWCLK = PA14     BOOT0     BOOT1", size=15, fill=T.TEXT)
    canvas.text(56, 518, "退出 Standby 时 BOOT 脚会再采样一次", size=13, fill=T.MUTED)
    _credit(canvas, "自绘。地址与启动行来自 RM0008 Rev 21 第 3.4 节表 9。")
    return canvas


def gpio_led() -> Svg:
    canvas = Svg(
        960,
        660,
        "PA0 推挽可以点灯；PC13 不能当电流源",
        "STM32F103C8T6 LQFP48 · DS5319 Rev 20 Figure 8 / Table 5 / note 5",
    )
    canvas.header(tag="03", tag_color=T.AMBER)
    canvas.rect(40, 86, 420, 250, fill=T.PANEL, stroke=T.CYAN, rx=10)
    canvas.text(56, 116, "STM32F103C8T6  LQFP48", size=16, fill=T.TEXT, weight="700")
    canvas.rect(56, 140, 150, 40, fill=T.BG2, stroke=T.GREEN, rx=6)
    canvas.text(68, 166, "10   PA0-WKUP", size=14, fill=T.GREEN, weight="700")
    canvas.rect(56, 196, 190, 40, fill=T.BG2, stroke=T.RED, rx=6)
    canvas.text(68, 222, "2   PC13-TAMPER-RTC", size=14, fill=T.RED, weight="700")
    canvas.text(56, 270, "PA0 推挽写 1：电流从脚流出", size=13, fill=T.GREEN)
    canvas.text(56, 296, "PC13 走电源开关，禁止作电流源", size=13, fill=T.RED)
    canvas.text(460, 108, "正常路径", size=16, fill=T.GREEN, weight="700")
    canvas.rect(460, 124, 460, 160, fill=T.PANEL, stroke=T.GREEN, rx=10)
    canvas.text(476, 154, "PA0 第 10 脚", size=14, fill=T.TEXT, weight="700")
    canvas.text(476, 180, "3.3 V → 推挽 PMOS → 270 Ω → LED → GND", size=13, fill=T.CYAN)
    canvas.text(476, 206, "R = (3.3 − 2.0) / 0.005 = 260 Ω，取 270 Ω", size=13, fill=T.TEXT)
    canvas.text(476, 232, "高 500 ms，低 500 ms，合起来 1 Hz", size=13, fill=T.MUTED)
    canvas.text(476, 256, "周期来自 HAL_Delay(500)，不是速度位", size=12, fill=T.MUTED)
    canvas.text(460, 316, "失败路径", size=16, fill=T.RED, weight="700")
    canvas.rect(460, 332, 460, 150, fill=T.PANEL, stroke=T.RED, rx=10)
    canvas.text(476, 362, "PC13 第 2 脚", size=14, fill=T.TEXT, weight="700")
    canvas.text(476, 388, "把 PA0「写 1 点灯」原样搬过来", size=13, fill=T.AMBER)
    canvas.text(476, 414, "灌电流上限 3 mA，不能作电流源", size=13, fill=T.RED)
    canvas.text(476, 440, "速度 ≤ 2 MHz，负载 ≤ 30 pF", size=13, fill=T.TEXT)
    canvas.text(476, 464, "25 mA / 50 MHz 对 PC13–PC15 作废", size=12, fill=T.MUTED)
    canvas.rect(40, 360, 400, 200, fill=T.BG2, stroke=T.VIOLET, rx=10)
    canvas.text(56, 390, "GPIOx_LCKR  偏移 0x18", size=14, fill=T.VIOLET, weight="700")
    canvas.text(56, 420, "LCK[15:0] 在序列中保持不变", size=13, fill=T.TEXT)
    canvas.text(56, 446, "LCKK：写 1，写 0，写 1", size=13, fill=T.TEXT)
    canvas.text(56, 472, "再读，确认读回 1，锁保持到复位", size=13, fill=T.TEXT)
    canvas.text(56, 498, "错一步，锁中止，配置仍可改", size=13, fill=T.AMBER)
    canvas.text(56, 528, "RM0008 Rev 21 §9.2.7", size=12, fill=T.MUTED)
    _credit(canvas, "自绘。脚位与 3 mA / 2 MHz / 30 pF 来自 DS5319 Rev 20。")
    return canvas


def main() -> None:
    out_dir = os.path.join(ROOT, "assets", "diagrams")
    os.makedirs(out_dir, exist_ok=True)
    boot_state().save(os.path.join(out_dir, "sample-00-boot-state.svg"))
    gpio_led().save(os.path.join(out_dir, "sample-03-gpio-led.svg"))


if __name__ == "__main__":
    main()

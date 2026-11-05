#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Static B2 figures for chapter 01. No CSS animation and no SMIL.

    python tools/sample_figs_b2/ch01_b2.py .temp/b2ch01
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from svgkit import Svg, T

from triage_plates import debug_connect  # shared plate drawing, one source of truth


def _credit(canvas: Svg, note: str) -> None:
    canvas.line(24, canvas.h - 36, canvas.w - 24, canvas.h - 36, stroke=T.GRID, sw=1)
    canvas.text(24, canvas.h - 16, note, size=11, fill=T.MUTED)
    canvas.text(canvas.w - 24, canvas.h - 16, "自绘 · 静态 · CC BY 4.0", size=11, fill=T.DIM, anchor="end")


def build_accept() -> Svg:
    canvas = Svg(
        960,
        840,
        "一次链接派生 ELF、map 与 bin；只有 Build succeeded 而没有产物路径，等于还没进入烧录边界",
        "STM32F103C8T6 · chapter 01 · linker/stm32f103c8.ld",
    )
    canvas.header(tag="01", tag_color=T.CYAN)
    canvas.text(40, 86, "STM32F103C8T6  Flash 0x08000000 to 0x08010000  SRAM 0x20000000 to 0x20005000",
                size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, ".elf keeps symbols and debug info. .bin is the bytes. .map is the address book.",
                size=14, fill=T.CYAN)
    canvas.text(40, 138, "-Wl,-Map=...  --gc-sections  --print-memory-usage    objcopy -O ihex    objcopy -O binary",
                size=13, fill=T.AMBER, mono=True)

    canvas.text(40, 170, "正常路径  一次链接，三份产物", size=16, fill=T.GREEN, weight="700")
    canvas.rect(40, 184, 880, 246, fill=T.PANEL, stroke=T.GREEN, rx=8)
    canvas.box(56, 204, 176, 52, label=".o + .ld", sub="compile, then link", size=14)
    canvas.box(272, 204, 204, 52, label="spl-f1-blink.elf", sub="symbols + debug info", size=14,
               stroke=T.GREEN, color=T.TEXT)
    canvas.box(516, 204, 150, 52, label="objcopy", sub="-O binary", size=14)
    canvas.box(706, 204, 194, 52, label="spl-f1-blink.bin", sub="bytes at 0x08000000", size=14,
               stroke=T.GREEN, color=T.TEXT)
    canvas.arrow(232, 230, 272, 230, color=T.GREEN)
    canvas.arrow(476, 230, 516, 230, color=T.GREEN)
    canvas.arrow(666, 230, 706, 230, color=T.GREEN)
    canvas.text(56, 296, "elf: the debugger reads it. A breakpoint needs a source line, and the line table lives here.",
                size=14, fill=T.TEXT)
    canvas.text(56, 322, "bin: the flasher reads it. There are no address fields, so it always lands at 0x08000000.",
                size=14, fill=T.TEXT)
    canvas.text(56, 348, "map: sections and symbols with addresses. 64 KB and 20 KB are checked here, nowhere else.",
                size=14, fill=T.TEXT)
    canvas.text(56, 374, "first 8 bytes of the bin:  00 50 00 20 25 07 00 08", size=15,
                fill=T.AMBER, mono=True)
    canvas.text(56, 400, "word 0 is 0x20005000, the top of 20 KB SRAM; word 1 is 0x08000725, Reset_Handler in Flash",
                size=13, fill=T.MUTED)

    canvas.text(40, 452, "失败路径  Build succeeded 之后没有产物路径", size=16, fill=T.RED, weight="700")
    canvas.rect(40, 466, 880, 138, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(56, 496, "the build log cannot name the compiler, the .ld, or where the ELF sits",
                size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 522, "a host .exe came out instead: the toolchain file never loaded",
                size=14, fill=T.RED)
    canvas.text(56, 548, "no .map, so nobody can say whether .text still ends before 0x08010000",
                size=14, fill=T.AMBER)
    canvas.text(56, 574, "until an artifact path exists, flashing has not started",
                size=13, fill=T.MUTED)

    canvas.text(40, 626, "不证明什么  这张图停在产物边界", size=16, fill=T.VIOLET, weight="700")
    canvas.rect(40, 640, 880, 152, fill=T.BG2, stroke=T.VIOLET, rx=8)
    canvas.text(56, 670, "a .bin on disk does not prove the part was programmed",
                size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 696, "a .map inside 64 KB does not prove reset reaches main",
                size=14, fill=T.TEXT)
    canvas.text(56, 722, "an .elf does not prove the probe can attach; that is the next figure",
                size=14, fill=T.TEXT)
    canvas.text(56, 748, "while a host .exe is what came out, do not touch the C code",
                size=14, fill=T.AMBER)
    _credit(canvas, "自绘。64 KB / 20 KB 与两个起点来自 DS5319 与本章；产物取 examples/spl-f1-blink 的构建输出。")
    return canvas



def flash_path() -> Svg:
    canvas = Svg(
        960,
        880,
        "三条把 .bin 送进 0x08000000 的路径：SWD 调试口随时可用，串口与 USB DFU 都住在 ROM bootloader 里",
        "STM32F103C8T6 · chapter 01 · RM0008 2.4 · AN3155 · AN3156",
    )
    canvas.header(tag="01", tag_color=T.CYAN)
    canvas.text(40, 86, "STM32F103C8T6  Flash 0x08000000..0x0800FFFF (64 KB)  page 1 KB",
                size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "every path ends at the same address; they differ in who opens the door",
                size=14, fill=T.CYAN)
    canvas.text(40, 138, "SWD = debug port, no bootloader involved    ISP/DFU = ROM bootloader at 0x1FFFF000",
                size=13, fill=T.AMBER, mono=True)

    canvas.text(40, 170, "路径一  SWD 调试口（BOOT0 = 0 也能烧）", size=16, fill=T.GREEN, weight="700")
    canvas.rect(40, 184, 880, 200, fill=T.PANEL, stroke=T.GREEN, rx=8)
    canvas.box(56, 208, 200, 52, label="host tools", sub="openocd / pyocd / Keil", size=14)
    canvas.box(300, 208, 170, 52, label="ST-Link V2", sub="USB to SWD", size=14)
    canvas.box(514, 208, 190, 52, label="SWD pins", sub="PA13 SWDIO · PA14 SWCLK", size=13)
    canvas.box(748, 208, 156, 52, label="Flash", sub="0x08000000", size=14, stroke=T.GREEN, color=T.TEXT)
    canvas.arrow(256, 234, 300, 234, color=T.GREEN)
    canvas.arrow(470, 234, 514, 234, color=T.GREEN)
    canvas.arrow(704, 234, 748, 234, color=T.GREEN)
    canvas.text(56, 296, "two wires plus NRST; the same cable then runs the debugger, so this is the default path",
                size=14, fill=T.TEXT)
    canvas.text(56, 322, "keeps working while user firmware runs, unless PA13/PA14 were reused as GPIO",
                size=14, fill=T.TEXT)
    canvas.text(56, 352, "checkpoint before blaming the cable: the .ioc must set SYS → Debug = Serial Wire",
                size=13, fill=T.MUTED)

    canvas.text(40, 424, "路径二 / 三  BOOT0 = 1 复位 → ROM bootloader，二选一传输", size=16, fill=T.AMBER, weight="700")
    canvas.rect(40, 438, 880, 252, fill=T.PANEL, stroke=T.AMBER, rx=8)
    canvas.text(56, 466, "BOOT0 = 1 at reset makes the core fetch from system memory 0x1FFFF000, not from Flash",
                size=14, fill=T.TEXT)
    canvas.text(56, 490, "the bootloader listens on two transports at once; pick either, the entry condition is identical",
                size=13, fill=T.MUTED)
    canvas.box(56, 508, 404, 60, label="USART1 ISP", sub="PA9 TX · PA10 RX, 8N1, auto-baud", size=14)
    canvas.text(76, 596, "host: Flash Loader Demonstrator / stm32flash   (AN3155)", size=13, fill=T.AMBER, mono=True)
    canvas.box(500, 508, 404, 60, label="USB DFU", sub="PA11 DM · PA12 DP, device FS", size=14)
    canvas.text(520, 596, "host: DfuSe demo / dfu-util   (AN3156)", size=13, fill=T.AMBER, mono=True)
    canvas.text(56, 628, "no SWD pins involved here: a part whose debug port was killed can still be flashed this way",
                size=14, fill=T.TEXT)
    canvas.text(56, 654, "BOOT0 is sampled at reset; toggling it while running changes nothing until the next reset",
                size=13, fill=T.MUTED)

    canvas.text(40, 706, "不证明什么  通路存在不等于烧写成功", size=16, fill=T.VIOLET, weight="700")
    canvas.rect(40, 720, 880, 116, fill=T.BG2, stroke=T.VIOLET, rx=8)
    canvas.text(56, 750, "a working path proves transport only; the write itself is the next chapter's triage figure",
                size=14, fill=T.TEXT)
    canvas.text(56, 776, "ISP and DFU live inside the ROM bootloader, so they cannot flash while user code is running",
                size=14, fill=T.TEXT)
    canvas.text(56, 806, "none of the three says the application logic is correct; verify compares bytes, not behavior",
                size=14, fill=T.TEXT)
    _credit(canvas, "自绘。bootloader 入口与两个传输来自 RM0008 2.4 与 AN3155/AN3156；64 KB 容量与基址来自 DS5319 Rev 20。")
    return canvas


def _wrap(c: Svg, x: float, y: float, s: str, w: float, size: float,
          color: str, lh: float = 16, mono: bool = False) -> float:
    """按像素宽度折行；返回下一行的基线。"""
    from svgkit import text_width
    words, line, yy = s.split(), "", y
    for word in words:
        probe = (line + " " + word).strip()
        if text_width(probe, size, mono) > w and line:
            c.text(x, yy, line, size=size, fill=color, mono=mono)
            yy += lh
            line = word
        else:
            line = probe
    if line:
        c.text(x, yy, line, size=size, fill=color, mono=mono)
        yy += lh
    return yy


def flash_triage() -> Svg:
    canvas = Svg(
        960,
        800,
        "attach 已通过、卡在下载或校验：按下载失败、校验失败、烧进去了但没跑三岔口排查",
        "STM32F103C8T6 · chapter 01 · RM0008 2.5 · DS5319 Rev 20",
    )
    canvas.header(tag="01", tag_color=T.CYAN)

    # ① 先把「哪一段已经证明没问题」画成链：attach 通了，前面的环节都不用再怀疑
    canvas.text(30, 82, "OpenOCD reports `target state: halted`, yet the flash step fails",
                size=14.5, fill=T.TEXT, weight="700")
    chain = [
        ("OpenOCD", "cfg 已加载", T.CYAN, True),
        ("ST-Link", "USB 枚举通过", T.CYAN, True),
        ("PA13 / PA14", "第 34 / 37 脚", T.CYAN, True),
        ("Cortex-M3", "halted ✓", T.GREEN, True),
        ("Flash 写入", "✗ 失败", T.RED, False),
    ]
    cx, cw2, gap = 30, 168, 30
    for i, (name, note, color, ok) in enumerate(chain):
        x = cx + i * (cw2 + gap)
        canvas.rect(x, 96, cw2, 56, fill=T.PANEL, stroke=color,
                    sw=2 if not ok else 1.5, rx=8)
        canvas.text(x + 12, 120, name, size=12.5, fill=T.TEXT, weight="700")
        canvas.text(x + 12, 140, note, size=10.5, fill=color)
        if i < len(chain) - 1:
            canvas.arrow(x + cw2 + 2, 124, x + cw2 + gap - 4, 124,
                         color=T.STROKE, sw=1.5, head=6)
    canvas.text(30, 174,
                "attach 通了，工具、探针、接线、cfg 都已证明可用 —— 剩下的问题都在写入这一侧。"
                "先看 OpenOCD 打印的那一行，再决定查哪个岔口。",
                size=11.5, fill=T.MUTED)

    # ② 三个岔口：每列症状 → 三个检查点 → 一句修法
    branches = [
        ("①", "Flash Download failed", "Error: flash download failed",
         T.RED,
         [("算法要和 64 KB 中密度匹配", "128 KB 的算法会在高地址报错"),
          ("RDP 选项字节可能还锁着", "读保护状态下拒绝改写，RM0008 2.5"),
          ("内核停在上次失败的怪状态", "改用 connect under reset 重新接")],
         "选中 C8T6 的算法 → 全片擦除 → 再下载",
         "解除 RDP（键 0x00A5）会整片擦除，用户代码一起没了"),
        ("②", "Verification failed", "Error: verify failed",
         T.AMBER,
         [("写入说成功、回读不一样", "先怀疑物理链路，不要先改软件"),
          ("带载量 3V3，看有没有下跌", "低于 2.7 V 时闪存写入会静默出错"),
          ("把 adapter speed 1000 降到 100", "再换一根线和另一个 USB 口")],
         "先稳住供电，再降时钟；校验错不能靠软件糊过去",
         "3.3 V 是空载值；下载时电流上升，表笔要留在板子上"),
        ("③", "下载成功却没有运行", "wrote … but no LED",
         T.VIOLET,
         [("BOOT0 还挂在 1", "复位后进系统存储器，闪存里的程序根本没取指"),
          ("bin 头 8 字节对不对", "00 50 00 20 25 07 00 08：栈顶 + Reset_Handler"),
          ("向量表基址是 0x08000000", ".ld 起点写错，第一次取指就跑飞")],
         "BOOT0 = 0 → 按复位 → 还不动就用示波器看 NRST",
         "“下载成功”只说明字节进去了，不说明它会跑")]

    by = 190
    bw, bgap = 290, 15
    for i, (num, title, errline, color, checks, fix, note) in enumerate(branches):
        x = 30 + i * (bw + bgap)
        canvas.rect(x, by, bw, 372, fill=T.PANEL, stroke=color, rx=8)
        canvas.rect(x, by, bw, 5, fill=color, rx=2)
        canvas.text(x + 16, by + 32, num, size=15, fill=color, weight="700")
        canvas.text(x + 40, by + 32, title, size=14, fill=T.TEXT, weight="700")
        canvas.text(x + 16, by + 52, errline, size=10, fill=color, mono=True)
        yy = by + 78
        for cnum, (head, detail) in enumerate(checks, 1):
            canvas.circle(x + 22, yy - 4, 8, fill=T.BG2, stroke=color, sw=1.5)
            canvas.text(x + 22, yy, str(cnum), size=9.5, anchor="middle",
                        fill=color, weight="700")
            canvas.text(x + 38, yy, head, size=11.5, fill=T.TEXT, weight="600")
            yy = _wrap(canvas, x + 38, yy + 15, detail, bw - 54, 10.5, T.MUTED,
                       lh=13) + 7
        canvas.rect(x + 12, by + 268, bw - 24, 56, fill=T.BG2, stroke=color,
                    rx=4)
        _wrap(canvas, x + 24, by + 288, fix, bw - 48, 11, T.GREEN, lh=14)
        _wrap(canvas, x + 24, by + 336, note, bw - 48, 9.5, T.DIM, lh=12)

    # ③ 岔口二那条「先量电压」值得画出来：2.7 V 是编程下限，不是建议值
    gy = 586
    canvas.text(30, gy, "为什么不先改代码：VDD 掉到 2.7 V 以下，写入就已经不可信了",
                size=12, fill=T.TEXT, weight="600")
    canvas.rect(30, gy + 10, 560, 22, fill=T.BG2, stroke=T.GRID, rx=4)
    x0, x1, v0, v1 = 30, 590, 2.0, 3.6
    def vx(v):
        return x0 + (v - v0) / (v1 - v0) * (x1 - x0)
    canvas.rect(x0, gy + 10, vx(2.7) - x0, 22, fill=T.RED, rx=4, opacity=0.28)
    canvas.rect(vx(3.3) - 6, gy + 6, 12, 30, fill=T.GREEN, rx=2)
    for v, lab in ((2.0, "2.0"), (2.7, "2.7"), (3.3, "3.3"), (3.6, "3.6")):
        canvas.line(vx(v), gy + 32, vx(v), gy + 38, stroke=T.STROKE, sw=1)
        canvas.text(vx(v), gy + 50, lab + " V", size=10, anchor="middle",
                    fill=T.MUTED, mono=True)
    canvas.text(vx(2.7) + 8, gy + 26, "编程电压下限 2.7 V", size=10.5, fill=T.RED)
    canvas.text(620, gy + 18, "adapter speed", size=11, fill=T.MUTED)
    canvas.chip(720, gy + 4, 70, 26, "1000", color=T.AMBER, size=12)
    canvas.arrow(796, gy + 17, 820, gy + 17, color=T.STROKE, sw=1.5, head=6)
    canvas.chip(826, gy + 4, 70, 26, "100", color=T.GREEN, size=12)

    # ④ 边界：verify 干净证明什么、不证明什么
    canvas.rect(30, gy + 62, 900, 34, fill=T.BG2, stroke=T.VIOLET, rx=8)
    canvas.text(44, gy + 84,
                "verify 干净 = 字节一致；它不证明时序、外设、栈深与中断行为 —— 那要靠逻辑分析仪和断点",
                size=11.5, fill=T.TEXT)

    _credit(canvas, "自绘。RDP 与页擦除见 RM0008 2.5；容量与算法名见 DS5319 Rev 20；"
                    "2.7 V 为 DS5319 编程电压下限。")
    return canvas


FIGURES = [
    ("sample-01-build-accept.svg", build_accept),
    ("sample-01-debug-connect.svg", debug_connect),
    ("sample-01-flash-path.svg", flash_path),
    ("sample-01-flash-triage.svg", flash_triage),
]


def main(argv: list[str] | None = None) -> None:
    args = sys.argv[1:] if argv is None else argv
    out_dir = args[0] if args else os.path.join("assets", "diagrams")
    os.makedirs(out_dir, exist_ok=True)
    for name, make in FIGURES:
        make().save(os.path.join(out_dir, name))


if __name__ == "__main__":
    main()

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


def debug_connect() -> Svg:
    canvas = Svg(
        960,
        990,
        "ELF 已生成却连不上：先查 PA13/PA14 复用，再查供电与共地，最后才动 adapter speed",
        "STM32F103C8T6 LQFP48 · DS5319 Rev 20 表 5 · openocd/bluepill-stlink.cfg",
    )
    canvas.header(tag="01", tag_color=T.CYAN)
    canvas.text(40, 86, "STM32F103C8T6  LQFP48  Cortex-Debug + OpenOCD  arm-none-eabi-gdb",
                size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "the ELF exists and the build is green, so this failure is past the build boundary",
                size=14, fill=T.CYAN)
    canvas.text(40, 138, "pin 34 PA13 = SWDIO    pin 37 PA14 = SWCLK    pin 7 NRST    pin 44 BOOT0",
                size=14, fill=T.AMBER)

    canvas.text(40, 170, "第一环  PA13/PA14 被复用成 GPIO", size=16, fill=T.GREEN, weight="700")
    canvas.rect(40, 184, 880, 188, fill=T.PANEL, stroke=T.GREEN, rx=8)
    canvas.text(56, 214, "symptom: No target connected, or every SWD attempt fails after one flash",
                size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 240, "symptom: the part still boots, but the two debug pins are ordinary GPIO from then on",
                size=14, fill=T.TEXT)
    canvas.text(56, 266, "checkpoint: the .ioc has SYS → Debug = Serial Wire", size=15,
                fill=T.AMBER, weight="700")
    canvas.text(56, 292, "and the generated GPIO init does not list PA13 or PA14 as an output",
                size=13, fill=T.MUTED)
    canvas.text(56, 318, "recovery: BOOT0 high, connect, erase, set Serial Wire, flash again",
                size=14, fill=T.TEXT)
    canvas.text(56, 344, "No Debug is a one-way door here; no C change reopens the port",
                size=13, fill=T.MUTED)

    canvas.text(40, 400, "第二环  供电与共地先量，再谈别的", size=16, fill=T.GREEN, weight="700")
    canvas.rect(40, 414, 880, 188, fill=T.PANEL, stroke=T.GREEN, rx=8)
    canvas.text(56, 444, "symptom: Cannot access target, No STM32 target found, a link that drops",
                size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 470, "pin 35 VSS_2 and pin 36 VDD_2 sit beside the debug pins and must not float",
                size=14, fill=T.TEXT)
    canvas.text(56, 496, "checkpoint: 3V3 to GND reads 3.3 V, and probe GND is board GND", size=15,
                fill=T.AMBER, weight="700")
    canvas.text(56, 522, "this lab powers the BluePill over Micro-USB; do not parallel the probe's 3.3 V",
                size=13, fill=T.MUTED)
    canvas.text(56, 548, "pin 7 NRST is not an SWD signal, but it is how a probe hard-resets the chip",
                size=14, fill=T.TEXT)
    canvas.text(56, 574, "a dead rail and a miscounted pin report the same error",
                size=13, fill=T.MUTED)

    canvas.text(40, 630, "第三环  接口与 cfg：速率是最后才动的旋钮", size=16, fill=T.GREEN, weight="700")
    canvas.rect(40, 644, 880, 188, fill=T.PANEL, stroke=T.GREEN, rx=8)
    canvas.text(56, 674, "symptom: the probe attaches sometimes, or drops right after reset",
                size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 700, "openocd/bluepill-stlink.cfg: transport select hla_swd / adapter speed 1000",
                size=14, fill=T.AMBER, mono=True)
    canvas.text(56, 726, "checkpoint: launch.json configFiles loads that cfg, not an older copy", size=15,
                fill=T.AMBER, weight="700")
    canvas.text(56, 752, "then lower adapter speed below 1000 and retry, one knob at a time",
                size=14, fill=T.TEXT)
    canvas.text(56, 778, "target/stm32f1x.cfg is this part's target file; the ELF path stays as it is",
                size=13, fill=T.MUTED)
    canvas.text(56, 804, "a stale ST-Link firmware reports DFU errors; upgrade it first",
                size=13, fill=T.MUTED)

    canvas.text(40, 862, "查的顺序  环 1 → 环 2 → 环 3", size=16, fill=T.VIOLET, weight="700")
    canvas.rect(40, 876, 880, 66, fill=T.BG2, stroke=T.VIOLET, rx=8)
    canvas.text(56, 906, "do not rewrite main while the line is not connected",
                size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 932, "do not change -O2 to fix an attach failure; the build already succeeded",
                size=14, fill=T.TEXT)
    _credit(canvas, "自绘。脚位来自 DS5319 Rev 20 表 5；速率与 transport 取自 openocd/bluepill-stlink.cfg。")
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


def flash_triage() -> Svg:
    canvas = Svg(
        960,
        920,
        "attach 已通过、卡在下载或校验：按下载失败、校验失败、烧进去了但没跑三岔口排查",
        "STM32F103C8T6 · chapter 01 · RM0008 2.5 · DS5319 Rev 20",
    )
    canvas.header(tag="01", tag_color=T.CYAN)
    canvas.text(40, 86, "STM32F103C8T6  OpenOCD reports `target state: halted`, yet the flash step fails",
                size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "attach is proven, so the debug port, the probe and the cfg are innocent",
                size=14, fill=T.CYAN)
    canvas.text(40, 138, "branch by the exact error line before touching anything    3V3 > 2.7 V always assumed",
                size=13, fill=T.AMBER, mono=True)

    canvas.text(40, 170, "岔口一  Flash Download failed", size=16, fill=T.RED, weight="700")
    canvas.rect(40, 184, 880, 200, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(56, 214, "checkpoint 1: the Flash algorithm must match 64 KB medium density, not 128 KB", size=14, fill=T.TEXT)
    canvas.text(56, 240, "checkpoint 2: the option byte RDP may be set — the part refuses mass writes (RM0008 2.5)", size=14, fill=T.TEXT)
    canvas.text(56, 266, "checkpoint 3: a previous run left the core in a weird state — retry with connect under reset", size=14, fill=T.TEXT)
    canvas.text(56, 296, "fix: select the C8T6 algorithm, full chip erase, then download again", size=15, fill=T.AMBER, weight="700")
    canvas.text(56, 322, "note: removing RDP by the 0x00A5 key triggers a mass erase — user code is gone", size=13, fill=T.MUTED)

    canvas.text(40, 424, "岔口二  Verification failed", size=16, fill=T.AMBER, weight="700")
    canvas.rect(40, 438, 880, 168, fill=T.PANEL, stroke=T.AMBER, rx=8)
    canvas.text(56, 468, "the write claimed success but the read-back differs: suspect the physical link first", size=14, fill=T.TEXT)
    canvas.text(56, 494, "measure 3V3 under load; a droop below 2.7 V corrupts flash writes silently", size=14, fill=T.TEXT)
    canvas.text(56, 520, "drop `adapter speed 1000` to 100 and retry; swap the USB cable and port", size=14, fill=T.TEXT)
    canvas.text(56, 550, "fix: stable power first, then a slower clock; never fix verify errors in software", size=14, fill=T.AMBER)

    canvas.text(40, 646, "岔口三  下载成功但没有运行", size=16, fill=T.VIOLET, weight="700")
    canvas.rect(40, 660, 880, 148, fill=T.PANEL, stroke=T.VIOLET, rx=8)
    canvas.text(56, 690, "checkpoint 1: BOOT0 may still be wired high — reset then enters the bootloader, not Flash", size=14, fill=T.TEXT)
    canvas.text(56, 716, "checkpoint 2: the bin must start with 00 50 00 20 25 07 00 08 (stack + Reset_Handler)", size=14, fill=T.TEXT, mono=True)
    canvas.text(56, 742, "checkpoint 3: the vector table base is 0x08000000; a wrong .ld start breaks the fetch", size=14, fill=T.TEXT)
    canvas.text(56, 772, "fix: set BOOT0 = 0, press reset, and watch NRST with the scope if it still will not run", size=14, fill=T.AMBER)

    canvas.text(40, 824, "不证明什么", size=16, fill=T.VIOLET, weight="700")
    canvas.rect(40, 838, 880, 38, fill=T.BG2, stroke=T.VIOLET, rx=8)
    canvas.text(56, 862, "a clean verify proves the bytes match, not that the timing or the peripherals behave", size=14, fill=T.TEXT)
    _credit(canvas, "自绘。RDP 键值与页擦除语义来自 RM0008 2.5；容量与算法名来自 DS5319 Rev 20；bin 头样例来自 examples/spl-f1-blink。")
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

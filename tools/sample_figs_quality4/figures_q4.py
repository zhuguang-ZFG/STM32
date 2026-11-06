#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""High-density static Handraw figures for ch00/01/18–22."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from svgkit import Svg, T
from sample_figs_quality4._common import credit, audit_static

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                   "assets", "diagrams")


def ch00_three_ways() -> Svg:
    c = Svg(960, 880, "Three ways to write firmware", "Register / SPL / HAL — pick one lane first week")
    c.header(tag="00", tag_color=T.CYAN)
    c.text(40, 86, "First week: one board, one LED, one toolchain lane. Mixing three APIs burns the week.", size=15, fill=T.TEXT, weight="700")
    ways = [
        ("Register", "RM0008 direct", "max control, slowest start", "good after clocks click", T.AMBER),
        ("SPL", "stm32f10x_*.c", "legacy F1 books", "still useful on BluePill", T.GREEN),
        ("HAL / LL", "CubeMX + HAL", "fastest bring-up", "hide clocks until you dig", T.CYAN),
        ("This book", "register + labs", "numbers on the wire", "HAL only when noted", T.VIOLET),
    ]
    for i, (t, a, b, d, col) in enumerate(ways):
        x = 40 + (i % 2) * 460
        y = 120 + (i // 2) * 150
        c.rect(x, y, 440, 130, fill=T.PANEL, stroke=col, rx=8)
        c.text(x + 24, y + 34, t, size=17, fill=col, weight="700")
        c.text(x + 24, y + 64, a, size=14, fill=T.TEXT, mono=True, weight="700")
        c.text(x + 24, y + 92, b, size=13, fill=T.MUTED)
        c.text(x + 24, y + 116, d, size=13, fill=T.TEXT)
    c.rect(40, 440, 880, 130, fill=T.BG2, stroke=T.GREEN, rx=8)
    c.text(56, 474, "Accept bar week 1: LED blinks at a measured period after reset (not only after flash).", size=14, fill=T.GREEN, weight="700")
    c.text(56, 506, "BOOT0=0, 0x08000000 image, SWD still attached — then open chapter 02 clocks.", size=13, fill=T.TEXT)
    c.text(56, 536, "If reset blanks the LED: treat as boot triage, not as 'compiler broken'.", size=13, fill=T.MUTED)
    c.rect(40, 590, 880, 100, fill=T.PANEL, stroke=T.RED, rx=8)
    c.text(56, 624, "Trap: Cube project + hand-edit startup + second IDE = three truths for one binary.", size=14, fill=T.RED, weight="700")
    c.text(56, 654, "Keep one build command that a stranger can run from a clean clone.", size=13, fill=T.MUTED)
    credit(c, "Hand-drawn. First-week lane choice for F103 BluePill labs.")
    return c


def ch00_roadmap_gates() -> Svg:
    c = Svg(960, 880, "Three-stage roadmap gates", "Blink → bus → system — each gate is measurable")
    c.header(tag="00", tag_color=T.AMBER)
    c.text(40, 86, "Do not jump to RTOS before UART prints a line you can hash against a golden file.", size=15, fill=T.TEXT, weight="700")
    stages = [
        ("Stage A", "GPIO / TIM / UART", "LED 1 Hz ± 50 ms", "ch02–06", T.CYAN),
        ("Stage B", "I2C / SPI / ADC / DMA", "bus scope match", "ch07–10", T.GREEN),
        ("Stage C", "IAP / USB / RTOS / LP", "accept scripts green", "ch11–17", T.AMBER),
    ]
    for i, (t, body, gate, ch, col) in enumerate(stages):
        x = 40 + i * 300
        c.rect(x, 130, 280, 220, fill=T.PANEL, stroke=col, rx=8)
        c.text(x + 140, 168, t, size=18, anchor="middle", fill=col, weight="700")
        c.text(x + 140, 210, body, size=13, anchor="middle", fill=T.TEXT)
        c.text(x + 140, 250, "gate:", size=12, anchor="middle", fill=T.MUTED)
        c.text(x + 140, 280, gate, size=14, anchor="middle", fill=T.TEXT, mono=True, weight="700")
        c.text(x + 140, 320, ch, size=13, anchor="middle", fill=T.MUTED, mono=True)
        if i < 2:
            c.arrow(x + 284, 240, x + 296, 240, color=T.STROKE, sw=2)
    c.rect(40, 380, 880, 150, fill=T.BG2, stroke=T.VIOLET, rx=8)
    c.text(56, 414, "Shopping minimum: BluePill F103C8, ST-Link V2, USB-TTL, breadboard, 2× LED + 220 Ω.", size=14, fill=T.VIOLET, weight="700")
    c.text(56, 446, "Optional week 2: logic analyzer ≥24 MHz sample, 32.768 kHz can, CR2032 for VBAT labs.", size=13, fill=T.TEXT)
    c.text(56, 478, "Skip 'full kit' shopping until Stage A gate passes on the desk you already own.", size=13, fill=T.MUTED)
    c.rect(40, 550, 880, 130, fill=T.PANEL, stroke=T.RED, rx=8)
    c.text(56, 584, "Slowdowns: chasing every HAL example, rewriting startup weekly, no measured accept.", size=14, fill=T.RED, weight="700")
    c.text(56, 616, "Fix: one lab sheet with numbers (Hz, baud, address) before the next chapter.", size=13, fill=T.TEXT)
    c.text(56, 646, "Pairs with sample-00-accept-gate and first-success-gates.", size=13, fill=T.MUTED)
    credit(c, "Hand-drawn. Roadmap gates aligned to this book's chapter bands.")
    return c


def ch01_env_compare() -> Svg:
    c = Svg(960, 880, "Four environments, one contract", "CubeIDE / Keil / CLion / VS Code — one flash path")
    c.header(tag="01", tag_color=T.CYAN)
    c.text(40, 86, "IDE is a caller. The contract is: same ELF, same OpenOCD/ST-Link script, same 0x08000000.", size=15, fill=T.TEXT, weight="700")
    rows = [
        ("STM32CubeIDE", "Eclipse + Cube", "MX → Makefile/GCC", "good defaults, heavy UI", T.CYAN),
        ("Keil MDK", "armcc/armclang", "μVision project", "pack-centric, license", T.AMBER),
        ("CLion", "CMake truth", "OpenOCD run cfg", "IDE only invokes CMake", T.GREEN),
        ("VS Code", "tasks.json", "Cortex-Debug", "thin shell around CLI", T.VIOLET),
    ]
    for i, (t, a, b, d, col) in enumerate(rows):
        y = 120 + i * 100
        c.rect(40, y, 880, 88, fill=T.PANEL, stroke=col, rx=8)
        c.text(56, y + 28, t, size=16, fill=col, weight="700")
        c.text(280, y + 28, a, size=13, fill=T.TEXT, mono=True)
        c.text(560, y + 28, b, size=13, fill=T.TEXT, mono=True)
        c.text(56, y + 58, d, size=13, fill=T.MUTED)
    c.rect(40, 540, 880, 120, fill=T.BG2, stroke=T.GREEN, rx=8)
    c.text(56, 574, "Accept: `arm-none-eabi-size` + OpenOCD program_elf → reset → LED matches lab sheet.", size=14, fill=T.GREEN, weight="700")
    c.text(56, 606, "SWD: PA13/PA14 (pins 34/37), GND, 3.3 V sense — never 5 V into ST-Link target pin.", size=13, fill=T.TEXT)
    c.text(56, 636, "If IDE 'download ok' but reset dark: BOOT0 and vector table, not the editor theme.", size=13, fill=T.MUTED)
    c.rect(40, 680, 880, 80, fill=T.PANEL, stroke=T.RED, rx=8)
    c.text(56, 714, "Trap: two flash tools fighting (IDE + external ST-Link Utility) without a single script.", size=14, fill=T.RED, weight="700")
    credit(c, "Hand-drawn. Environment compare for ch01 bring-up.")
    return c


def ch01_rdp_unlock() -> Svg:
    c = Svg(960, 880, "Readout protection unlock", "RDP level 1 → mass erase → level 0")
    c.header(tag="01", tag_color=T.AMBER)
    c.text(40, 86, "Cannot attach / flash fails with protection: check FLASH_OBR RDP before rewriting wiring.", size=15, fill=T.TEXT, weight="700")
    steps = [
        ("1 Detect", "OpenOCD / CubeProg", "RDP=1 reported", T.CYAN),
        ("2 Unlock cmd", "stm32f1x unlock", "or CubeProg UI", T.GREEN),
        ("3 Mass erase", "full Flash wipe", "user code gone", T.AMBER),
        ("4 RDP=0", "option bytes", "SWD returns", T.VIOLET),
    ]
    for i, (t, a, b, col) in enumerate(steps):
        x = 40 + i * 230
        c.rect(x, 130, 210, 140, fill=T.PANEL, stroke=col, rx=8)
        c.text(x + 105, 168, t, size=15, anchor="middle", fill=col, weight="700")
        c.text(x + 105, 204, a, size=13, anchor="middle", fill=T.TEXT, mono=True)
        c.text(x + 105, 236, b, size=12, anchor="middle", fill=T.MUTED)
        if i < 3:
            c.arrow(x + 214, 200, x + 226, 200, color=T.STROKE, sw=2)
    c.rect(40, 300, 880, 150, fill=T.BG2, stroke=T.GREEN, rx=8)
    c.text(56, 334, "F103 option bytes live near 0x1FFFF800; RDP level 2 is a one-way door on many parts.", size=14, fill=T.GREEN, weight="700")
    c.text(56, 366, "Level 1 unlock always mass-erases — expect to reflash the blink lab afterward.", size=13, fill=T.TEXT)
    c.text(56, 398, "Confirm with `stm32f1x options_read` (or CubeProg) that RDP reads 0xA5 / level 0.", size=13, fill=T.MUTED)
    c.rect(40, 470, 880, 140, fill=T.PANEL, stroke=T.RED, rx=8)
    c.text(56, 504, "Trap: chasing SWD wiring for hours while OBR says protected.", size=14, fill=T.RED, weight="700")
    c.text(56, 536, "Trap: assuming unlock keeps Flash contents — it does not on level-1 exit.", size=13, fill=T.TEXT)
    c.text(56, 568, "Document the unlock in the lab notebook; production units may intentionally stay locked.", size=13, fill=T.MUTED)
    c.rect(40, 630, 880, 80, fill=T.PANEL, stroke=T.STROKE, rx=8)
    c.text(56, 664, "Place under '芯片被读保护时怎么解锁' — pairs with sample-01-debug-connect.", size=14, fill=T.TEXT, weight="700")
    credit(c, "Hand-drawn. RDP unlock path from RM0008 option-byte chapter.")
    return c


def ch18_link_map() -> Svg:
    c = Svg(960, 880, "链接失败：先对照容量，再读段的落点", "STM32F103C8T6 · Flash 64 KB / SRAM 20 KB")
    c.header(tag="18", tag_color=T.CYAN)
    c.text(40, 104, "地址轴只比较容量；具体占用以本次 map 文件为准。", size=20, fill=T.TEXT, weight="700")
    for y, label, width, start, end, color in (
        (158, "Flash · 64 KB", 704, "0x08000000", "0x08010000", T.CYAN),
        (306, "SRAM · 20 KB", 220, "0x20000000", "0x20005000", T.GREEN),
    ):
        c.text(40, y, label, size=23, fill=color, weight="700")
        c.rect(40, y+20, width, 44, fill=T.BG2, stroke=color, rx=2)
        c.line(40, y+64, 40, y+77, stroke=color, sw=2)
        c.line(40+width, y+64, 40+width, y+77, stroke=color, sw=2)
        c.text(40, y+105, start, size=17, fill=T.TEXT, mono=True)
        c.text(40+width+18, y+51, end, size=17, fill=T.TEXT, mono=True)
    c.text(40, 450, "初始化的 .data 占两处", size=22, fill=T.AMBER, weight="700")
    c.rect(40, 474, 340, 76, fill=T.PANEL, stroke=T.CYAN, rx=8)
    c.text(210, 505, "Flash：初值（LMA）", size=18, fill=T.CYAN, anchor="middle", weight="700")
    c.text(210, 532, ".text / .rodata 也存放于此", size=15, fill=T.TEXT, anchor="middle")
    c.arrow(388, 512, 560, 512, color=T.AMBER)
    c.text(474, 492, "启动时复制", size=15, fill=T.MUTED, anchor="middle")
    c.rect(572, 474, 348, 76, fill=T.PANEL, stroke=T.GREEN, rx=8)
    c.text(746, 505, "SRAM：运行地址（VMA）", size=18, fill=T.GREEN, anchor="middle", weight="700")
    c.text(746, 532, ".bss 清零；栈和堆另留空间", size=15, fill=T.TEXT, anchor="middle")
    c.line(40, 586, 920, 586, stroke=T.GRID)
    c.text(40, 626, "region overflowed", size=21, fill=T.RED, weight="700", mono=True)
    c.text(40, 661, "读报错区域、LENGTH 与段占用；包括保留区、对齐和栈/堆。", size=18, fill=T.TEXT)
    c.text(40, 713, "链接通过，复位后没运行", size=21, fill=T.CYAN, weight="700")
    c.text(40, 748, "再对照镜像位置、启动向量、BOOT 与 VTOR；ORIGIN 和 VTOR 各有用途。", size=18, fill=T.TEXT)
    c.text(40, 797, "size 是汇总，map 才能显示每段和符号的地址；容量上界不包含终点地址。", size=17, fill=T.MUTED)
    credit(c, "自绘矢量图 · F103C8 容量与链接段关系；无虚构占用量。")
    return c


def ch18_hardfault_ladder() -> Svg:
    c = Svg(960, 880, "HardFault：地址和栈帧分开核对", "CFSR 0xE000ED28 · BFAR 0xE000ED38")
    c.header(tag="18", tag_color=T.AMBER)
    c.rect(40, 106, 880, 108, fill=T.PANEL, stroke=T.CYAN, rx=8)
    c.text(60, 145, "先保存 BFAR / MMFAR，再读取对应有效位", size=23, fill=T.CYAN, weight="700")
    c.text(60, 182, "一并保存 CFSR、HFSR、EXC_RETURN 与可用栈帧；以下解读同一快照。", size=18, fill=T.TEXT)
    c.arrow(480, 218, 480, 256, color=T.STROKE)
    c.text(480, 294, "BFARVALID · CFSR bit 15", size=23, fill=T.TEXT, anchor="middle", weight="700")
    c.line(480, 312, 480, 330, stroke=T.STROKE)
    c.line(256, 330, 704, 330, stroke=T.STROKE)
    c.arrow(256, 330, 256, 366, color=T.GREEN)
    c.arrow(704, 330, 704, 366, color=T.RED)
    c.text(280, 354, "1", size=19, fill=T.GREEN)
    c.text(728, 354, "0", size=19, fill=T.RED)
    for x, title, detail, color in (
        (40, "使用保存的 BFAR 地址", "结合故障类型与访问指令解释", T.GREEN),
        (496, "舍弃保存的 BFAR 地址", "数值看起来合理也不能用于定位", T.RED),
    ):
        c.rect(x, 370, 424, 108, fill=T.PANEL, stroke=color, rx=8)
        c.text(x+20, 411, title, size=21, fill=color, weight="700")
        c.text(x+20, 449, detail, size=17, fill=T.TEXT)
    c.line(40, 520, 920, 520, stroke=T.GRID)
    c.text(40, 563, "继续检查异常栈帧", size=23, fill=T.CYAN, weight="700")
    c.text(40, 604, "STKERR / MSTKERR：入栈失败，不能假定 frame 中每个字段都完整。", size=18, fill=T.RED)
    c.text(40, 644, "先验证 MSP / PSP、栈边界与 EXC_RETURN，再解释选定 frame 的 PC。", size=18, fill=T.TEXT)
    c.text(40, 684, "IMPRECISERR：异常可滞后于写访问，栈中 PC 未必是肇事指令。", size=18, fill=T.TEXT)
    c.rect(40, 728, 880, 72, fill=T.PANEL, stroke=T.AMBER, rx=8)
    c.text(60, 759, "定位源码使用同一份 ELF 与可信 PC；BFAR 是访问地址。", size=19, fill=T.AMBER, weight="700")
    c.text(60, 786, "MMFAR 同样先保存，再检查 MMARVALID；避免在故障中阻塞打印。", size=16, fill=T.MUTED)
    credit(c, "自绘矢量图 · ARM DUI0552A §4.3.10–4.3.15；采集、地址有效性与栈完整性分别判断。")
    return c


def ch18_uart_garbled() -> Svg:
    c = Svg(960, 880, "串口乱码：沿时钟和 TX 信号逐段检查", "USART1 · PPRE2 = 1 · BRR 保持 0x271")
    c.header(tag="18", tag_color=T.CYAN)
    c.text(40, 101, "先读 SWS 与 APB2 分频，得到 USART1 的 PCLK2。", size=21, fill=T.TEXT, weight="700")
    c.text(40, 141, "BRR raw = 0x271 = 625；USARTDIV = 39 + 1/16 = 39.0625", size=19, fill=T.CYAN, mono=True)
    for y, clock, baud, width, length, color in (
        (204, "PCLK2 = 72 MHz", "115200 bit/s", "8.68 µs", 78, T.GREEN),
        (352, "PCLK2 = 8 MHz", "12800 bit/s", "78.125 µs", 702, T.RED),
    ):
        c.text(40, y, clock, size=22, fill=color, weight="700")
        c.text(40, y+37, f"PCLK2 / 625 = {baud}", size=19, fill=T.TEXT, mono=True)
        c.line(178, y+75, 880, y+75, stroke=T.GRID)
        c.line(178, y+56, 178, y+94, stroke=color, sw=2)
        c.line(178+length, y+56, 178+length, y+94, stroke=color, sw=2)
        c.arrow(178, y+75, 178+length, y+75, color=color)
        c.text(40, y+82, width, size=18, fill=color, mono=True)
    c.text(40, 494, "两行按同一比例画单个位宽；数值为换算，不是实测波形。", size=18, fill=T.MUTED)
    c.line(40, 529, 920, 529, stroke=T.GRID)
    c.text(40, 571, "再核对接线与主机设置", size=23, fill=T.CYAN, weight="700")
    c.text(60, 622, "MCU PA9 · TX", size=20, fill=T.GREEN, mono=True)
    c.arrow(316, 615, 620, 615, color=T.GREEN)
    c.text(654, 622, "USB-TTL · RX", size=20, fill=T.TEXT, mono=True)
    c.text(60, 669, "MCU PA10 · RX", size=20, fill=T.CYAN, mono=True)
    c.arrow(620, 662, 316, 662, color=T.CYAN)
    c.text(654, 669, "USB-TTL · TX", size=20, fill=T.TEXT, mono=True)
    c.text(60, 716, "GND", size=20, fill=T.TEXT, mono=True)
    c.line(316, 709, 620, 709, stroke=T.STROKE, sw=2)
    c.text(654, 716, "GND", size=20, fill=T.TEXT, mono=True)
    c.text(40, 771, "使用 3.3 V 逻辑电平；两端波特率、数据位、校验与停止位一致。", size=18, fill=T.TEXT)
    c.text(40, 808, "HSE 没就绪时程序可能停在等待；当前 SYSCLK 必须从 SWS 核实。", size=17, fill=T.MUTED)
    credit(c, "自绘矢量图 · RM0008 USART/RCC；波特率按 PCLK2 与完整 BRR 换算。")
    return c


def ch19_pick_ladder() -> Svg:
    c = Svg(960, 880, "Project pick ladder", "★ count vs skills you already accepted")
    c.header(tag="19", tag_color=T.CYAN)
    c.text(40, 86, "Pick the smallest project that forces one new bus — not the coolest demo GIF.", size=15, fill=T.TEXT, weight="700")
    tiers = [
        ("★★", "BT car / DHT logger", "need: UART + GPIO", "adds: one sensor bus", T.GREEN),
        ("★★★", "ADC+DMA scope / USB / IAP", "need: DMA or USB clock", "adds: buffers + accept", T.AMBER),
        ("★★★★", "LA / CAN / balance / gateway", "need: Stage C gates", "adds: RTOS or multi-node", T.VIOLET),
    ]
    for i, (stars, names, need, adds, col) in enumerate(tiers):
        y = 120 + i * 130
        c.rect(40, y, 880, 110, fill=T.PANEL, stroke=col, rx=8)
        c.text(56, y + 34, stars, size=20, fill=col, weight="700")
        c.text(160, y + 34, names, size=15, fill=T.TEXT, weight="700")
        c.text(56, y + 68, need, size=13, fill=T.MUTED)
        c.text(480, y + 68, adds, size=13, fill=T.TEXT)
    c.rect(40, 530, 880, 140, fill=T.BG2, stroke=T.GREEN, rx=8)
    c.text(56, 564, "Milestone rule: each week ends with a scriptable accept (LED/UART/file/hash).", size=14, fill=T.GREEN, weight="700")
    c.text(56, 596, "Flash budget reminder: boot 16 KB + gap + APP 0xB800 on 64 KB C8 — see one-slot.gif.", size=13, fill=T.TEXT)
    c.text(56, 628, "If SRAM < 4 KB free in map, drop printf/float before adding another task.", size=13, fill=T.MUTED)
    credit(c, "Hand-drawn. Project selection ladder for ch19.")
    return c


def ch19_sram_budget() -> Svg:
    c = Svg(960, 880, "SRAM 20 KB budget", "stacks + DMA buffers + .bss on F103C8")
    c.header(tag="19", tag_color=T.AMBER)
    c.text(40, 86, "Projects die in RAM before Flash: count buffers with the 20 KB ceiling visible.", size=15, fill=T.TEXT, weight="700")
    rows = [
        (".data+.bss", "~2–6 KB", "globals / tables", T.CYAN),
        ("Main stack", "1–2 KB", "startup default", T.GREEN),
        ("Task stacks", "N × 256–1024 B", "FreeRTOS", T.AMBER),
        ("DMA ping-pong", "2 × ADC buf", "scope lab", T.VIOLET),
        ("Heap", "configTOTAL_HEAP", "printf cost", T.RED),
        ("Headroom", "≥2 KB", "interrupt nesting", T.CYAN),
    ]
    for i, (t, a, b, col) in enumerate(rows):
        x = 40 + (i % 3) * 300
        y = 120 + (i // 3) * 160
        c.rect(x, y, 280, 140, fill=T.PANEL, stroke=col, rx=8)
        c.text(x + 24, y + 36, t, size=15, fill=col, weight="700", mono=True)
        c.text(x + 24, y + 72, a, size=16, fill=T.TEXT, weight="700", mono=True)
        c.text(x + 24, y + 106, b, size=13, fill=T.MUTED)
    c.rect(40, 460, 880, 140, fill=T.BG2, stroke=T.GREEN, rx=8)
    c.text(56, 494, "Worked example: 2×1024 ADC + 3×512 stacks + 4 KB .bss ≈ 9 KB — fits with margin.", size=14, fill=T.GREEN, weight="700")
    c.text(56, 526, "2×4096 ADC + fat printf heap ⇒ HardFault that looks like 'DMA bug'.", size=13, fill=T.TEXT)
    c.text(56, 558, "Check map: `_end` / `_estack` gap; on RTOS also `xPortGetFreeHeapSize()`.", size=13, fill=T.MUTED)
    c.rect(40, 620, 880, 80, fill=T.PANEL, stroke=T.RED, rx=8)
    c.text(56, 654, "Trap: copying an F4 128 KB-RAM demo buffer sizes into BluePill.", size=14, fill=T.RED, weight="700")
    credit(c, "Hand-drawn. SRAM budget card for F103C8 projects.")
    return c


def ch20_manual_names() -> Svg:
    c = Svg(960, 880, "Manual naming map", "RM / DS / ES / PM — pick the right PDF")
    c.header(tag="20", tag_color=T.CYAN)
    c.text(40, 86, "Wrong PDF wastes the evening: match the acronym to the question before Ctrl+F.", size=15, fill=T.TEXT, weight="700")
    cards = [
        ("RM", "Reference Manual", "RM0008 for F1", "registers + peripherals", T.CYAN),
        ("DS", "Datasheet", "DS5319 C8/CB", "pins, electrical, packages", T.GREEN),
        ("ES", "Errata Sheet", "device limitations", "silicon bugs / workarounds", T.AMBER),
        ("PM", "Programming Manual", "PM0056 Cortex-M3", "core CPU, not chip pins", T.VIOLET),
        ("UM", "User Manual", "Nucleo / board UM", "on-board ST-Link, jumpers", T.CYAN),
        ("AN", "Application Note", "AN examples", "patterns, not the contract", T.GREEN),
    ]
    for i, (t, a, b, d, col) in enumerate(cards):
        x = 40 + (i % 3) * 300
        y = 120 + (i // 3) * 160
        c.rect(x, y, 280, 140, fill=T.PANEL, stroke=col, rx=8)
        c.text(x + 24, y + 36, t, size=22, fill=col, weight="700", mono=True)
        c.text(x + 24, y + 70, a, size=14, fill=T.TEXT, weight="700")
        c.text(x + 24, y + 98, b, size=13, fill=T.TEXT, mono=True)
        c.text(x + 24, y + 122, d, size=12, fill=T.MUTED)
    c.rect(40, 460, 880, 140, fill=T.BG2, stroke=T.GREEN, rx=8)
    c.text(56, 494, "Example: 'what is USART_BRR' → RM; 'can PA10 take 5 V' → DS; 'why HSE stuck' → ES+RM.", size=14, fill=T.GREEN, weight="700")
    c.text(56, 526, "Freeze versions in the lab notebook (RM0008 Rev 21, etc.) so diffs stay explainable.", size=13, fill=T.TEXT)
    c.text(56, 558, "Pairs with sample-20-lookup-flow animation.", size=13, fill=T.MUTED)
    c.rect(40, 620, 880, 80, fill=T.PANEL, stroke=T.RED, rx=8)
    c.text(56, 654, "Trap: googling a blog when the RM table already has the bit field.", size=14, fill=T.RED, weight="700")
    credit(c, "Hand-drawn. ST document acronym map for evidence lookup.")
    return c


def ch20_lib_compare() -> Svg:
    c = Svg(960, 880, "Firmware library compare", "SPL vs HAL vs LL vs libopencm3")
    c.header(tag="20", tag_color=T.AMBER)
    c.text(40, 86, "Libraries change the call shape, not the silicon. Pick one for a project and freeze it.", size=15, fill=T.TEXT, weight="700")
    rows = [
        ("SPL", "stm32f10x_*", "F1-era books", "still fine on BluePill", T.CYAN),
        ("HAL", "stm32f1xx_hal_*", "CubeMX default", "portable, heavier", T.GREEN),
        ("LL", "stm32f1xx_ll_*", "register-ish", "less hidden state", T.AMBER),
        ("libopencm3", "community", "no Cube lock-in", "API differs from ST", T.VIOLET),
    ]
    for i, (t, a, b, d, col) in enumerate(rows):
        x = 40 + (i % 2) * 460
        y = 120 + (i // 2) * 150
        c.rect(x, y, 440, 130, fill=T.PANEL, stroke=col, rx=8)
        c.text(x + 24, y + 34, t, size=17, fill=col, weight="700")
        c.text(x + 24, y + 64, a, size=14, fill=T.TEXT, mono=True, weight="700")
        c.text(x + 24, y + 94, f"{b} · {d}", size=13, fill=T.MUTED)
    c.rect(40, 440, 880, 140, fill=T.BG2, stroke=T.GREEN, rx=8)
    c.text(56, 474, "This book: register-first labs; SPL/HAL cited when a chapter needs their headers.", size=14, fill=T.GREEN, weight="700")
    c.text(56, 506, "Mixing HAL init + bare IRQs without reading MSP hooks ⇒ double-handled interrupts.", size=13, fill=T.TEXT)
    c.text(56, 538, "Freeze CMSIS + library commit hashes beside the RM revision.", size=13, fill=T.MUTED)
    c.rect(40, 600, 880, 100, fill=T.PANEL, stroke=T.RED, rx=8)
    c.text(56, 634, "Trap: copying HAL examples into an SPL tree 'just for this file'.", size=14, fill=T.RED, weight="700")
    c.text(56, 664, "Trap: upgrading Cube packs mid-project without rebuilding the accept suite.", size=13, fill=T.MUTED)
    credit(c, "Hand-drawn. Library compare for ch20 resource chapter.")
    return c


def ch21_vdd_3v3() -> Svg:
    c = Svg(960, 880, "BluePill power rails", "5 V USB · 3.3 V LDO · VDDA · VBAT")
    c.header(tag="21", tag_color=T.CYAN)
    c.text(40, 86, "Most 'mystery resets' on clone BluePills are power, not firmware. Name the rails.", size=15, fill=T.TEXT, weight="700")
    rails = [
        ("USB 5 V", "micro-USB", "into AMS1117-3.3", "hot under load", T.AMBER),
        ("3V3", "LDO out", "VDD pins", "logic + SWD target", T.GREEN),
        ("VDDA", "analog VDD", "ADC/DAC/PLL", "tie to 3V3 + caps", T.CYAN),
        ("VBAT", "pin 1", "RTC backup", "coin or 3V3", T.VIOLET),
    ]
    for i, (t, a, b, d, col) in enumerate(rails):
        x = 40 + (i % 2) * 460
        y = 120 + (i // 2) * 140
        c.rect(x, y, 440, 120, fill=T.PANEL, stroke=col, rx=8)
        c.text(x + 24, y + 32, t, size=16, fill=col, weight="700")
        c.text(x + 24, y + 60, a, size=14, fill=T.TEXT, mono=True)
        c.text(x + 24, y + 88, f"{b} · {d}", size=13, fill=T.MUTED)
    c.rect(40, 420, 880, 140, fill=T.BG2, stroke=T.GREEN, rx=8)
    c.text(56, 454, "Measure: USB 5 V present, 3V3 within 3.2–3.4 V, GND common with ST-Link.", size=14, fill=T.GREEN, weight="700")
    c.text(56, 486, "Never feed 5 V into a 3.3 V-only pin; ST-Link 'VCC' is sense, not a PSU for fat loads.", size=13, fill=T.TEXT)
    c.text(56, 518, "Clone tip: bad 1117 or missing decoupling ⇒ SWD flaky when LED turns on.", size=13, fill=T.MUTED)
    c.rect(40, 580, 880, 110, fill=T.PANEL, stroke=T.RED, rx=8)
    c.text(56, 614, "Trap: powering from ST-Link 3.3 V while USB also powers — two sources fight.", size=14, fill=T.RED, weight="700")
    c.text(56, 646, "Trap: floating VDDA on a hand-wired minimum system.", size=13, fill=T.MUTED)
    credit(c, "Hand-drawn. BluePill rail map from DS5319 + common clone practice.")
    return c


def ch21_hse_load() -> Svg:
    c = Svg(960, 880, "HSE 8 MHz load caps", "PD0/PD1 · ~20 pF class · CSS backup")
    c.header(tag="21", tag_color=T.AMBER)
    c.text(40, 86, "BluePill silkscreen says 8 MHz: confirm the can and load caps before blaming PLLMUL.", size=15, fill=T.TEXT, weight="700")
    steps = [
        ("PD0", "OSC_IN", "crystal pin", T.CYAN),
        ("PD1", "OSC_OUT", "crystal pin", T.GREEN),
        ("CL1/CL2", "~20 pF class", "board dependent", T.AMBER),
        ("HSERDY", "RCC_CR", "wait before PLL", T.VIOLET),
    ]
    for i, (t, a, b, col) in enumerate(steps):
        x = 40 + i * 230
        c.rect(x, 130, 210, 130, fill=T.PANEL, stroke=col, rx=8)
        c.text(x + 105, 168, t, size=16, anchor="middle", fill=col, weight="700", mono=True)
        c.text(x + 105, 204, a, size=14, anchor="middle", fill=T.TEXT, mono=True)
        c.text(x + 105, 236, b, size=12, anchor="middle", fill=T.MUTED)
    c.rect(40, 290, 880, 150, fill=T.BG2, stroke=T.GREEN, rx=8)
    c.text(56, 324, "Bring-up: HSEON → HSERDY → PLLSRC/PLLMUL → SW=PLL → SWS=PLL → LATENCY=2 @72 MHz.", size=14, fill=T.GREEN, weight="700")
    c.text(56, 356, "If HSERDY never sets: short timeout, bad solder, missing can, or wrong CL values.", size=13, fill=T.TEXT)
    c.text(56, 388, "CSS can fall back to HSI — your UART baud then lies while 'code looks fine'.", size=13, fill=T.MUTED)
    c.rect(40, 460, 880, 140, fill=T.PANEL, stroke=T.RED, rx=8)
    c.text(56, 494, "Trap: assuming every BluePill clone has a working 8 MHz can.", size=14, fill=T.RED, weight="700")
    c.text(56, 526, "Trap: probing OSC_OUT with a ×1 scope probe that kills start-up.", size=13, fill=T.TEXT)
    c.text(56, 558, "Lab: temporarily run on HSI to prove firmware, then restore HSE.", size=13, fill=T.MUTED)
    c.rect(40, 620, 880, 80, fill=T.PANEL, stroke=T.STROKE, rx=8)
    c.text(56, 654, "Pairs with sample-21-power-swd and clock chapters.", size=14, fill=T.TEXT, weight="700")
    credit(c, "Hand-drawn. HSE pin/load checklist for F103 BluePill.")
    return c


def ch21_usb_ttl() -> Svg:
    c = Svg(960, 880, "USB-TTL to USART1", "PA9 TX · PA10 RX · GND · 3.3 V I/O")
    c.header(tag="21", tag_color=T.GREEN)
    c.text(40, 86, "Wiring table people skip: cross TX/RX, share GND, keep levels at 3.3 V.", size=15, fill=T.TEXT, weight="700")
    rows = [
        ("MCU PA9", "USART1_TX", "→ adapter RX", "cross", T.CYAN),
        ("MCU PA10", "USART1_RX", "← adapter TX", "cross", T.GREEN),
        ("GND", "common", "must share", "else float junk", T.AMBER),
        ("VCC", "usually NC", "don't backfeed 5 V", "power from USB/LDO", T.RED),
    ]
    for i, (t, a, b, d, col) in enumerate(rows):
        y = 120 + i * 100
        c.rect(40, y, 880, 88, fill=T.PANEL, stroke=col, rx=8)
        c.text(56, y + 28, t, size=15, fill=col, weight="700", mono=True)
        c.text(280, y + 28, a, size=14, fill=T.TEXT, mono=True)
        c.text(520, y + 28, b, size=14, fill=T.TEXT)
        c.text(56, y + 58, d, size=13, fill=T.MUTED)
    c.rect(40, 540, 880, 120, fill=T.BG2, stroke=T.GREEN, rx=8)
    c.text(56, 574, "Accept: 115200 8N1, idle high ~3.3 V, 'ping' echo matches lab sheet.", size=14, fill=T.GREEN, weight="700")
    c.text(56, 606, "BlackPill / Nucleo may route VCP elsewhere — read the board UM, not BluePill muscle memory.", size=13, fill=T.TEXT)
    c.text(56, 636, "If using on-board USB device (ch14), do not fight the same pins with TTL adapters.", size=13, fill=T.MUTED)
    credit(c, "Hand-drawn. USB-TTL wiring card for board maps.")
    return c


def ch21_nrst_boot0() -> Svg:
    c = Svg(960, 880, "NRST and BOOT0 pins", "pin 7 NRST · pin 44 BOOT0 · pull habits")
    c.header(tag="21", tag_color=T.VIOLET)
    c.text(40, 86, "Reset and boot straps are hardware. Firmware cannot fix a BOOT0 tied high.", size=15, fill=T.TEXT, weight="700")
    boxes = [
        ("NRST", "pin 7", "active low reset", "10 kΩ pull-up typical", T.CYAN),
        ("BOOT0", "pin 44", "0 = Flash alias", "1 = system memory", T.AMBER),
        ("BOOT1", "PB2", "with BOOT0 combo", "keep 0 for Flash boot", T.GREEN),
        ("SWD", "PA13/14", "pins 34/37", "leave after flash", T.VIOLET),
    ]
    for i, (t, a, b, d, col) in enumerate(boxes):
        x = 40 + (i % 2) * 460
        y = 120 + (i // 2) * 150
        c.rect(x, y, 440, 130, fill=T.PANEL, stroke=col, rx=8)
        c.text(x + 24, y + 34, t, size=17, fill=col, weight="700")
        c.text(x + 24, y + 64, a, size=14, fill=T.TEXT, mono=True, weight="700")
        c.text(x + 24, y + 94, f"{b} · {d}", size=13, fill=T.MUTED)
    c.rect(40, 440, 880, 140, fill=T.BG2, stroke=T.GREEN, rx=8)
    c.text(56, 474, "Flash run path: BOOT0=0, image at 0x08000000, NRST released, SWD optional.", size=14, fill=T.GREEN, weight="700")
    c.text(56, 506, "System memory boot (BOOT0=1) explains 'flash ok, runs ISP not my app'.", size=13, fill=T.TEXT)
    c.text(56, 538, "Pairs with boot0-low.gif and sample-00-boot-state.", size=13, fill=T.MUTED)
    c.rect(40, 600, 880, 100, fill=T.PANEL, stroke=T.RED, rx=8)
    c.text(56, 634, "Trap: button on NRST without debounce cap → random restarts in the field.", size=14, fill=T.RED, weight="700")
    c.text(56, 664, "Trap: leaving BOOT0 jumper on '1' after using the ROM bootloader.", size=13, fill=T.MUTED)
    credit(c, "Hand-drawn. NRST/BOOT straps from DS5319 pinout.")
    return c


def ch22_wokwi_scope() -> Svg:
    c = Svg(960, 880, "Wokwi scope and limits", "good for logic + LED; not for analog truth")
    c.header(tag="22", tag_color=T.CYAN)
    c.text(40, 86, "Use Wokwi to prove control flow and pin diagrams — not ADC millivolts or bit timing lawsuits.", size=15, fill=T.TEXT, weight="700")
    goods = [
        ("Good fit", "GPIO/UART/I2C diagrams", "LED + serial labs", "fast iterate", T.GREEN),
        ("OK w/ care", "SPI patterns", "simple timers", "check real scope later", T.AMBER),
        ("Poor fit", "ADC accuracy", "USB eye / CAN PHY", "crystal start margins", T.RED),
        ("Always", "keep same accept text", "hash UART lines", "port to hardware", T.CYAN),
    ]
    for i, (t, a, b, d, col) in enumerate(goods):
        x = 40 + (i % 2) * 460
        y = 120 + (i // 2) * 150
        c.rect(x, y, 440, 130, fill=T.PANEL, stroke=col, rx=8)
        c.text(x + 24, y + 34, t, size=16, fill=col, weight="700")
        c.text(x + 24, y + 64, a, size=13, fill=T.TEXT)
        c.text(x + 24, y + 94, f"{b} · {d}", size=13, fill=T.MUTED)
    c.rect(40, 440, 880, 140, fill=T.BG2, stroke=T.GREEN, rx=8)
    c.text(56, 474, "Book rule: every Wokwi example has a twin accept on BluePill before you call it done.", size=14, fill=T.GREEN, weight="700")
    c.text(56, 506, "diagram.json + sketch tell the story; silicon errata still need the DS/ES.", size=13, fill=T.TEXT)
    c.text(56, 538, "Pairs with simulator-comparison.svg.", size=13, fill=T.MUTED)
    c.rect(40, 600, 880, 100, fill=T.PANEL, stroke=T.RED, rx=8)
    c.text(56, 634, "Trap: debugging timing races only in the browser, then surprised on the desk.", size=14, fill=T.RED, weight="700")
    c.text(56, 664, "Trap: copying Wokwi pin numbers that do not match your BluePill silk.", size=13, fill=T.MUTED)
    credit(c, "Hand-drawn. Wokwi fitness card for ch22.")
    return c


def ch22_renode_path() -> Svg:
    c = Svg(960, 880, "Renode script path", "REPL · platform · ELF · UART analyzer")
    c.header(tag="22", tag_color=T.AMBER)
    c.text(40, 86, "Renode shines when you need scripted CPU+peripheral logs without soldering.", size=15, fill=T.TEXT, weight="700")
    steps = [
        ("1", "platform", ".resc board", T.CYAN),
        ("2", "load ELF", "sysbus LoadELF", T.GREEN),
        ("3", "start", "start / pause", T.AMBER),
        ("4", "UART", "analyzer / log", T.VIOLET),
    ]
    for i, (n, t, a, col) in enumerate(steps):
        x = 40 + i * 230
        c.rect(x, 130, 210, 130, fill=T.PANEL, stroke=col, rx=8)
        c.text(x + 105, 168, f"{n}. {t}", size=15, anchor="middle", fill=col, weight="700")
        c.text(x + 105, 210, a, size=13, anchor="middle", fill=T.TEXT, mono=True)
        if i < 3:
            c.arrow(x + 214, 195, x + 226, 195, color=T.STROKE, sw=2)
    c.rect(40, 290, 880, 150, fill=T.BG2, stroke=T.GREEN, rx=8)
    c.text(56, 324, "Two scripts in this repo cover the smoke path — run them before editing platforms.", size=14, fill=T.GREEN, weight="700")
    c.text(56, 356, "Good for CI-like UART asserts; weak for analog and undocumented clone wiring.", size=13, fill=T.TEXT)
    c.text(56, 388, "Keep the same golden string as the hardware lab sheet.", size=13, fill=T.MUTED)
    c.rect(40, 460, 880, 140, fill=T.PANEL, stroke=T.RED, rx=8)
    c.text(56, 494, "Trap: treating a green Renode log as proof of HSE solder quality.", size=14, fill=T.RED, weight="700")
    c.text(56, 526, "Trap: forking platform files without recording the Renode version.", size=13, fill=T.TEXT)
    c.text(56, 558, "Pairs with sample-22-sim-triage.", size=13, fill=T.MUTED)
    c.rect(40, 620, 880, 80, fill=T.PANEL, stroke=T.STROKE, rx=8)
    c.text(56, 654, "Place under 'Renode：两条脚本'.", size=14, fill=T.TEXT, weight="700")
    credit(c, "Hand-drawn. Renode bring-up path for ch22.")
    return c


def ch22_hw_gap() -> Svg:
    c = Svg(960, 880, "Simulation vs hardware gap", "what still needs the desk")
    c.header(tag="22", tag_color=T.VIOLET)
    c.text(40, 86, "Honest dual-track: sim teaches structure; hardware teaches margins.", size=15, fill=T.TEXT, weight="700")
    rows = [
        ("Needs desk", "crystal start / CSS", "USB enumerate / CAN PHY", "power droop", T.RED),
        ("Sim OK first", "state machines", "IRQ ordering stories", "map/overflow", T.GREEN),
        ("Both", "UART accept strings", "GPIO truth tables", "IAP slot math", T.CYAN),
        ("Never skip", "BOOT0=0 check", "3.3 V rail measure", "SWD pin continuity", T.AMBER),
    ]
    for i, (t, a, b, d, col) in enumerate(rows):
        y = 120 + i * 100
        c.rect(40, y, 880, 88, fill=T.PANEL, stroke=col, rx=8)
        c.text(56, y + 28, t, size=15, fill=col, weight="700")
        c.text(260, y + 28, a, size=13, fill=T.TEXT)
        c.text(560, y + 28, b, size=13, fill=T.TEXT)
        c.text(56, y + 58, d, size=13, fill=T.MUTED)
    c.rect(40, 540, 880, 120, fill=T.BG2, stroke=T.GREEN, rx=8)
    c.text(56, 574, "Accept promotion: sim green → desk green → only then call the chapter done.", size=14, fill=T.GREEN, weight="700")
    c.text(56, 606, "Document failures that only reproduce on clone PCBs — that is the point of ch21.", size=13, fill=T.TEXT)
    c.text(56, 636, "Pairs with simulation-model-boundary.svg.", size=13, fill=T.MUTED)
    credit(c, "Hand-drawn. Sim-vs-hardware gap card.")
    return c


FIGURES = [
    ("sample-00-three-ways.svg", ch00_three_ways),
    ("sample-00-roadmap-gates.svg", ch00_roadmap_gates),
    ("sample-01-env-compare.svg", ch01_env_compare),
    ("sample-01-rdp-unlock.svg", ch01_rdp_unlock),
    ("sample-18-link-map.svg", ch18_link_map),
    ("sample-18-hardfault-ladder.svg", ch18_hardfault_ladder),
    ("sample-18-uart-garbled.svg", ch18_uart_garbled),
    ("sample-19-pick-ladder.svg", ch19_pick_ladder),
    ("sample-19-sram-budget.svg", ch19_sram_budget),
    ("sample-20-manual-names.svg", ch20_manual_names),
    ("sample-20-lib-compare.svg", ch20_lib_compare),
    ("sample-21-vdd-3v3.svg", ch21_vdd_3v3),
    ("sample-21-hse-load.svg", ch21_hse_load),
    ("sample-21-usb-ttl.svg", ch21_usb_ttl),
    ("sample-21-nrst-boot0.svg", ch21_nrst_boot0),
    ("sample-22-wokwi-scope.svg", ch22_wokwi_scope),
    ("sample-22-renode-path.svg", ch22_renode_path),
    ("sample-22-hw-gap.svg", ch22_hw_gap),
]


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    for name, fn in FIGURES:
        path = os.path.join(OUT, name)
        fn().save(path)
        audit_static(name, path)
    print(f"wrote {len(FIGURES)} figures -> {OUT}")


if __name__ == "__main__":
    main()

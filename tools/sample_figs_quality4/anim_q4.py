#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mechanism animations for ch00/01/18–22 — new files only."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from svgkit import Svg, T, anim_flow
from sample_figs_quality4._common import audit_anim

W, H = 900, 620
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                   "assets", "animations")


def _step_highlight(prefix: str, n: int, period=6.0, window=0.2, peak=0.35, rest=0.06) -> str:
    css = []
    step = 100.0 / n
    for i in range(n):
        a = i * step
        b = min(a + step * window, 99.0)
        name = f"{prefix}{i}-flash"
        css.append(
            f"@keyframes {name}{{0%,{a:.2f}%{{opacity:{rest}}}"
            f"{a + 0.25:.2f}%,{b:.2f}%{{opacity:{peak}}}"
            f"{min(b + 0.25, 100):.2f}%,100%{{opacity:{rest}}}}}"
        )
        css.append(f".{prefix}{i}{{animation:{name} {period}s linear infinite;}}")
    return "\n".join(css)


def _flow_row(s, steps, css, y0=100):
    bw, gap, x0, bh = 120, 18, 40, 100
    for i, (t, n, col) in enumerate(steps):
        x = x0 + i * (bw + gap)
        s.rect(x, y0, bw, bh, fill=T.PANEL, stroke=col, rx=8)
        s.text(x + bw / 2, y0 + 32, t, size=13, anchor="middle", fill=col, weight="700")
        s.text(x + bw / 2, y0 + 60, n, size=11, anchor="middle", fill=T.TEXT, mono=True)
        s.rect(x, y0, bw, bh, fill=col, rx=8, cls=f"s{i}", opacity=0.12)
        if i < len(steps) - 1:
            ax1, ax2 = x + bw + 4, x + bw + gap - 4
            s.arrow(ax1, y0 + bh / 2, ax2, y0 + bh / 2, color=T.STROKE, sw=2)
            s.line(ax1, y0 + bh / 2, ax2, y0 + bh / 2, stroke=T.CYAN, sw=2, cls=f"f{i}")
            css.append(anim_flow(f".f{i}", dur="1.2s", dash="6 12", shift=-18))
    css.append(_step_highlight("s", len(steps), period=7.0))


def boot_fetch_flow() -> Svg:
    s = Svg(W, H, "BOOT0 Flash fetch", "BOOT0=0 → 0x08000000 MSP + Reset")
    s.header(title="BOOT0=0：从 0x08000000 取 MSP 与复位向量", subtitle="mechanism · FA-002 continuous-line",
             tag="00", tag_color=T.CYAN)
    css = []
    steps = [
        ("BOOT0", "pin44=0", T.CYAN),
        ("ALIAS", "Flash @0", T.GREEN),
        ("MSP", "word0", T.AMBER),
        ("RESET", "word1", T.VIOLET),
        ("RUN", "user app", T.GREEN),
        ("OK", "LED gate", T.CYAN),
    ]
    _flow_row(s, steps, css)
    s.title_block(40, 230, "Happy path only — BOOT0=1 system memory stays on static SVG", color=T.GREEN)
    rows = [
        ("BOOT0", "0 => Flash alias at 0x00000000", T.CYAN),
        ("Vector", "MSP @ +0, Reset_Handler @ +4", T.AMBER),
        ("Accept", "after NRST, LED matches lab sheet", T.GREEN),
        ("SWD", "optional after image is trusted", T.VIOLET),
    ]
    for i, (a, b, col) in enumerate(rows):
        y = 265 + i * 44
        s.rect(40, y, 820, 38, fill=T.PANEL, stroke=T.STROKE, rx=8)
        s.text(56, y + 24, a, size=13, fill=col, weight="700", mono=True)
        s.text(840, y + 24, b, size=13, fill=T.TEXT, anchor="end")
    s.rect(40, 450, 820, 70, fill=T.BG2, stroke=T.RED, rx=8)
    s.text(56, 478, "Motion is BOOT0→alias→vectors→run — not a bootloader menu.", size=13, fill=T.TEXT)
    s.text(56, 500, "High BOOT0 and optimizer traps stay on sample-00-boot-triage.", size=12, fill=T.MUTED)
    css.append("@media (prefers-reduced-motion: reduce){*{animation:none!important}}")
    s.add_style("\n".join(css))
    s.footer(note="自绘矢量动画 · FA-002 · BOOT0 取指机制，非示波器实测",
             label="自绘矢量动画 · STM32 知识库")
    return s


def flash_swd_flow() -> Svg:
    s = Svg(W, H, "SWD flash then fetch", "program ELF → reset → MSP/Reset")
    s.header(title="SWD：烧录 ELF 后复位再取向量", subtitle="mechanism · FA-002 continuous-line",
             tag="01", tag_color=T.AMBER)
    css = []
    steps = [
        ("ELF", "image", T.CYAN),
        ("SWDIO", "PA13", T.GREEN),
        ("SWCLK", "PA14", T.AMBER),
        ("PROG", "0x08000000", T.VIOLET),
        ("NRST", "release", T.GREEN),
        ("FETCH", "MSP+RH", T.CYAN),
    ]
    _flow_row(s, steps, css)
    s.title_block(40, 230, "Pin reuse failures stay on the static SVG — this strip is the happy path", color=T.GREEN)
    rows = [
        ("Pins", "34=SWDIO, 37=SWCLK, shared GND", T.CYAN),
        ("Address", "bank at 0x08000000 for Flash boot", T.AMBER),
        ("Verify", "read MSP then Reset_Handler once", T.GREEN),
        ("BOOT0", "must stay 0 or you boot the ROM", T.VIOLET),
    ]
    for i, (a, b, col) in enumerate(rows):
        y = 265 + i * 44
        s.rect(40, y, 820, 38, fill=T.PANEL, stroke=T.STROKE, rx=8)
        s.text(56, y + 24, a, size=13, fill=col, weight="700", mono=True)
        s.text(840, y + 24, b, size=13, fill=T.TEXT, anchor="end")
    s.rect(40, 450, 820, 70, fill=T.BG2, stroke=T.RED, rx=8)
    s.text(56, 478, "IDE 'download ok' is not the gate — reset + measured LED is.", size=13, fill=T.TEXT)
    s.text(56, 500, "RDP unlock mass-erase path stays on sample-01-rdp-unlock.", size=12, fill=T.MUTED)
    css.append("@media (prefers-reduced-motion: reduce){*{animation:none!important}}")
    s.add_style("\n".join(css))
    s.footer(note="自绘矢量动画 · FA-002 · SWD 烧录取指，非抓包实录",
             label="自绘矢量动画 · STM32 知识库")
    return s


def boot0_faq_flow() -> Svg:
    s = Svg(W, H, "Boot pin sampling and boot memory selection",
            "STM32F103C8T6 · FA-002 · BOOT 选择启动存储器，应用是否有效还要检查向量")
    s.header(title="复位后，BOOT 引脚决定从哪里启动",
             tag="18", tag_color=T.CYAN)

    s.rect(40, 104, 250, 148, fill=T.PANEL, stroke=T.CYAN, rx=4, sw=2)
    s.text(56, 132, "复位释放", size=18, weight="700", fill=T.CYAN)
    s.text(56, 163, "第 4 个 SYSCLK 上升沿", size=16)
    s.text(56, 188, "锁存 BOOT0 与 BOOT1", size=16)
    s.text(56, 220, "BOOT0：pin 44  ·  BOOT1：PB2", size=13, fill=T.MUTED)
    s.line(290, 178, 350, 178, stroke=T.STROKE, sw=2)
    s.line(350, 124, 350, 308, stroke=T.STROKE, sw=2)
    branches = [
        (86, "BOOT0 = 0 · BOOT1 任意", "主 Flash", "0x08000000", T.GREEN),
        (178, "BOOT0 = 1 · BOOT1 = 0", "系统存储器", "0x1FFFF000", T.AMBER),
        (270, "BOOT0 = 1 · BOOT1 = 1", "SRAM", "0x20000000", T.VIOLET),
    ]
    css = []
    for i, (y, condition, name, address, color) in enumerate(branches):
        s.arrow(350, y + 38, 408, y + 38, color=color, sw=2, head=6)
        s.rect(410, y, 450, 76, fill=T.PANEL, stroke=color, rx=4, sw=1.5)
        s.text(426, y + 26, condition, size=15, fill=color, weight="700")
        s.text(426, y + 54, name, size=17)
        s.text(844, y + 54, address, size=17, mono=True, anchor="end", fill=color)
        s.circle(290, 178, 4, fill=color, cls=f"boot-route boot-route-{i}")
        dy = y + 38 - 178
        # One possible selection per third of the loop. All three conditions
        # remain printed; the animation duration is not a hardware timescale.
        a, b, c, d = i * 33.333, i * 33.333 + 4, i * 33.333 + 12, i * 33.333 + 20
        e = min(i * 33.333 + 31, 99.999)
        css.append(
            f"@keyframes boot-route-{i}{{"
            f"0%,{a:.3f}%{{transform:translate(0,0);opacity:0}}"
            f"{a + 0.1:.3f}%{{transform:translate(0,0);opacity:1}}"
            f"{b:.3f}%{{transform:translate(60px,0);opacity:1}}"
            f"{c:.3f}%{{transform:translate(60px,{dy}px);opacity:1}}"
            f"{d:.3f}%,{e:.3f}%{{transform:translate(118px,{dy}px);opacity:1}}"
            f"{min(e + 0.1, 100):.3f}%,100%{{transform:translate(118px,{dy}px);opacity:0}}}}"
            f".boot-route-{i}{{animation:boot-route-{i} 9s linear infinite;}}"
        )
    s.text(40, 284, "采样后按组合选择一支", size=14, fill=T.MUTED)
    s.text(40, 309, "不由探针是否连上决定", size=14, fill=T.MUTED)

    s.line(40, 367, 860, 367, stroke=T.GRID, sw=1)
    s.text(40, 397, "Flash 启动：0x08000000 的内容在 0x00000000 可读", size=17,
           fill=T.GREEN, weight="700")
    s.rect(40, 414, 820, 72, fill=T.PANEL, stroke=T.STROKE, rx=4)
    s.text(56, 440, "0x00000000 · 第 1 字", size=15, mono=True)
    s.arrow(316, 435, 376, 435, color=T.GREEN, sw=2, head=6)
    s.text(396, 440, "初始 MSP", size=16, fill=T.GREEN)
    s.text(56, 468, "0x00000004 · 第 2 字", size=15, mono=True)
    s.arrow(316, 463, 376, 463, color=T.GREEN, sw=2, head=6)
    s.text(396, 468, "Reset 向量 · bit 0 = 1（Thumb）", size=16, fill=T.GREEN)
    s.text(40, 521, "BOOT0 = 0 只选中 Flash；MSP、复位向量和程序镜像仍须有效。",
           size=15)
    s.text(40, 549, "探针读 ID 另查供电、共地、PA13 / PA14 与复位；读到 ID 不等于应用已运行。",
           size=14, fill=T.MUTED)
    css.append("@media(prefers-reduced-motion:reduce){.boot-route{animation:none!important;display:none}}")
    css.append("@media print{.boot-route{animation:none!important;display:none}}")
    s.add_style("\n".join(css))
    s.footer(note="每次复位只选择一个启动入口", label="自绘矢量动画 · 原理示意 / 非实拍")
    return s


def slot_fill_flow() -> Svg:
    s = Svg(W, H, "Single APP slot address ranges",
            "STM32F103C8T6 · FA-002 · Boot 16 KiB + 参数 2 KiB + APP 46 KiB = 64 KiB")
    s.header(title="单槽 Flash：先算范围，再放镜像",
             tag="19", tag_color=T.AMBER)
    x0, unit, y, height = 66, 12, 178, 66
    x1, x2, end = x0 + 16 * unit, x0 + 18 * unit, x0 + 64 * unit
    s.text(40, 100, "64 KiB Flash · 1 KiB = 1024 字节", size=19, weight="700")
    s.text(40, 128, "地址条按容量比例绘制；参数区用于保存数据。", size=15, fill=T.MUTED)
    ranges = [
        (x0, 16 * unit, T.CYAN, T.PANEL2),
        (x1, 2 * unit, T.AMBER, T.BG2),
        (x2, 46 * unit, T.GREEN, T.PANEL),
    ]
    css = []
    for i, (x, width, color, fill) in enumerate(ranges):
        s.rect(x, y, width, height, fill=fill, stroke=color, sw=1.5)
        s.rect(x, y - 4, width, height + 8, stroke=color, sw=2,
               cls=f"slot-range slot-range-{i}", opacity=0)
        a, b = i * 33.333, min((i + 1) * 33.333 - 1, 99)
        css.append(
            f"@keyframes slot-range-{i}{{0%,{a:.3f}%{{opacity:0}}"
            f"{a + .1:.3f}%,{b:.3f}%{{opacity:1}}"
            f"{b + .1:.3f}%,100%{{opacity:0}}}}"
            f".slot-range-{i}{{animation:slot-range-{i} 7.2s steps(1,end) infinite;}}"
        )
    s.text((x0 + x1) / 2, 207, "Bootloader", size=18, anchor="middle", fill=T.CYAN, weight="700")
    s.text((x0 + x1) / 2, 231, "16 KiB", size=16, anchor="middle", fill=T.CYAN)
    s.text((x2 + end) / 2, 207, "APP · 46 KiB", size=21, anchor="middle", fill=T.GREEN, weight="700")
    s.text((x2 + end) / 2, 232, "长度 0xB800", size=16, anchor="middle", fill=T.GREEN)
    s.line((x1 + x2) / 2, y - 1, (x1 + x2) / 2, 154, stroke=T.AMBER, sw=1.5)
    s.text((x1 + x2) / 2, 150, "参数 2 KiB", size=15, anchor="middle", fill=T.AMBER)
    for x in (x0, x1, x2, end):
        s.line(x, y + height + 2, x, y + height + 14, stroke=T.STROKE, sw=1)
    s.text(x0, 276, "0x08000000", size=15, mono=True, fill=T.CYAN)
    s.line(x1, 258, x1, 287, stroke=T.CYAN, sw=1)
    s.text(x1 - 8, 304, "0x08004000", size=15, mono=True, anchor="end", fill=T.CYAN)
    s.line(x2, 258, x2, 316, stroke=T.AMBER, sw=1)
    s.text(x2 + 8, 332, "0x08004800", size=15, mono=True, fill=T.AMBER)
    s.text(end, 276, "0x08010000", size=15, mono=True, anchor="end", fill=T.GREEN)
    s.text(end, 302, "排他上限 · 不包含这个地址", size=14, anchor="end", fill=T.MUTED)
    s.line(40, 354, 860, 354, stroke=T.GRID, sw=1)
    rows = [
        ("Bootloader", "[0x08000000, 0x08004000)  ·  16 KiB", T.CYAN),
        ("参数区", "[0x08004000, 0x08004800)  ·  2 KiB", T.AMBER),
        ("APP", "[0x08004800, 0x08010000)  ·  46 KiB", T.GREEN),
    ]
    for i, (name, value, color) in enumerate(rows):
        yy = 389 + i * 36
        s.text(40, yy, name, size=17, fill=color, weight="700")
        s.text(842, yy, value, size=16, mono=True, anchor="end")
    s.text(40, 505, "最后有效字节：0x0800FFFF；0x08004800 + 0xB800 = 0x08010000。",
           size=15, fill=T.GREEN)
    s.text(40, 542, "容量放得下，仍需检查镜像有效性与掉电恢复；单槽没有第二份 APP 备份。",
           size=15, fill=T.MUTED)
    css.append("@media(prefers-reduced-motion:reduce){.slot-range{animation:none!important;display:none}}")
    css.append("@media print{.slot-range{animation:none!important;display:none}}")
    s.add_style("\n".join(css))
    s.footer(note="范围分配示意，播放速度不代表写入速度", label="自绘矢量动画 · 原理示意 / 非实拍")
    return s


def evidence_flow() -> Svg:
    s = Svg(W, H, "Evidence lookup flow", "symptom → DS/RM/ES → note revision")
    s.header(title="取证：症状 → 选手册 → 记版本", subtitle="mechanism · FA-002 continuous-line",
             tag="20", tag_color=T.CYAN)
    css = []
    steps = [
        ("SYM", "symptom", T.CYAN),
        ("PICK", "RM/DS/ES", T.GREEN),
        ("FIND", "table/bit", T.AMBER),
        ("NOTE", "Rev x", T.VIOLET),
        ("LAB", "measure", T.GREEN),
        ("FIX", "one change", T.CYAN),
    ]
    _flow_row(s, steps, css)
    s.title_block(40, 230, "Complements sample-20-lookup-flow — this strip freezes the revision habit", color=T.GREEN)
    rows = [
        ("Pins/electrical", "Datasheet first", T.CYAN),
        ("Registers", "Reference Manual", T.AMBER),
        ("Silicon oddity", "Errata Sheet", T.GREEN),
        ("Core CPU", "PM0056, not RM pins", T.VIOLET),
    ]
    for i, (a, b, col) in enumerate(rows):
        y = 265 + i * 44
        s.rect(40, y, 820, 38, fill=T.PANEL, stroke=T.STROKE, rx=8)
        s.text(56, y + 24, a, size=13, fill=col, weight="700", mono=True)
        s.text(840, y + 24, b, size=13, fill=T.TEXT, anchor="end")
    s.rect(40, 450, 820, 70, fill=T.BG2, stroke=T.RED, rx=8)
    s.text(56, 478, "Blog posts are hints; the frozen PDF is the contract.", size=13, fill=T.TEXT)
    s.text(56, 500, "Manual acronym cards live on sample-20-manual-names.", size=12, fill=T.MUTED)
    css.append("@media (prefers-reduced-motion: reduce){*{animation:none!important}}")
    s.add_style("\n".join(css))
    s.footer(note="自绘矢量动画 · FA-002 · 手册取证流程",
             label="自绘矢量动画 · STM32 知识库")
    return s


def crystal_boot_flow() -> Svg:
    s = Svg(W, H, "HSE then Flash boot", "3V3 → HSE ready → BOOT0=0 → vectors")
    s.header(title="板级：3V3 与 HSE 就绪后再从 Flash 启动", subtitle="mechanism · FA-002 continuous-line",
             tag="21", tag_color=T.GREEN)
    css = []
    steps = [
        ("3V3", "rail OK", T.CYAN),
        ("HSE", "8 MHz", T.GREEN),
        ("RDY", "HSERDY", T.AMBER),
        ("BOOT0", "=0", T.VIOLET),
        ("VEC", "MSP+RH", T.GREEN),
        ("APP", "run", T.CYAN),
    ]
    _flow_row(s, steps, css)
    s.title_block(40, 230, "Board bring-up order — USB-TTL wiring stays on its static card", color=T.GREEN)
    rows = [
        ("Power", "3.2–3.4 V on 3V3, common GND", T.CYAN),
        ("Crystal", "PD0/PD1, wait HSERDY", T.AMBER),
        ("Boot strap", "BOOT0 low for Flash alias", T.GREEN),
        ("SWD", "PA13/PA14 if you still need attach", T.VIOLET),
    ]
    for i, (a, b, col) in enumerate(rows):
        y = 265 + i * 44
        s.rect(40, y, 820, 38, fill=T.PANEL, stroke=T.STROKE, rx=8)
        s.text(56, y + 24, a, size=13, fill=col, weight="700", mono=True)
        s.text(840, y + 24, b, size=13, fill=T.TEXT, anchor="end")
    s.rect(40, 450, 820, 70, fill=T.BG2, stroke=T.RED, rx=8)
    s.text(56, 478, "Missing can / dual 5 V sources stay on sample-21-vdd-3v3 / hse-load.", size=13, fill=T.TEXT)
    s.text(56, 500, "Complements sample-21-power-swd without replacing it.", size=12, fill=T.MUTED)
    css.append("@media (prefers-reduced-motion: reduce){*{animation:none!important}}")
    s.add_style("\n".join(css))
    s.footer(note="自绘矢量动画 · FA-002 · 板级上电启动顺序",
             label="自绘矢量动画 · STM32 知识库")
    return s


def sim_pick_flow() -> Svg:
    s = Svg(W, H, "Sim pick then desk", "Wokwi/Renode → golden → BluePill")
    s.header(title="仿真：先选工具，绿线后再上桌", subtitle="mechanism · FA-002 continuous-line",
             tag="22", tag_color=T.VIOLET)
    css = []
    steps = [
        ("PICK", "tool", T.CYAN),
        ("MODEL", "limits", T.GREEN),
        ("RUN", "script", T.AMBER),
        ("GOLD", "UART/LED", T.VIOLET),
        ("DESK", "BluePill", T.GREEN),
        ("PASS", "both", T.CYAN),
    ]
    _flow_row(s, steps, css)
    s.title_block(40, 230, "Dual-track honesty — analog margins never graduate from the browser alone", color=T.GREEN)
    rows = [
        ("Wokwi", "diagrams + fast GPIO/UART", T.CYAN),
        ("Renode", "scripted ELF + analyzers", T.AMBER),
        ("Desk", "HSE/USB/CAN/power truth", T.GREEN),
        ("Gate", "same accept string on both", T.VIOLET),
    ]
    for i, (a, b, col) in enumerate(rows):
        y = 265 + i * 44
        s.rect(40, y, 820, 38, fill=T.PANEL, stroke=T.STROKE, rx=8)
        s.text(56, y + 24, a, size=13, fill=col, weight="700", mono=True)
        s.text(840, y + 24, b, size=13, fill=T.TEXT, anchor="end")
    s.rect(40, 450, 820, 70, fill=T.BG2, stroke=T.RED, rx=8)
    s.text(56, 478, "Motion is pick→prove→port — not 'sim replaces soldering'.", size=13, fill=T.TEXT)
    s.text(56, 500, "Gap details on sample-22-hw-gap.", size=12, fill=T.MUTED)
    css.append("@media (prefers-reduced-motion: reduce){*{animation:none!important}}")
    s.add_style("\n".join(css))
    s.footer(note="自绘矢量动画 · FA-002 · 仿真选型与上桌",
             label="自绘矢量动画 · STM32 知识库")
    return s


ANIMS = [
    ("sample-00-boot-fetch-flow.svg", boot_fetch_flow),
    ("sample-01-flash-swd-flow.svg", flash_swd_flow),
    ("sample-18-boot0-flow.svg", boot0_faq_flow),
    ("sample-19-slot-fill-flow.svg", slot_fill_flow),
    ("sample-20-evidence-flow.svg", evidence_flow),
    ("sample-21-crystal-boot-flow.svg", crystal_boot_flow),
    ("sample-22-sim-pick-flow.svg", sim_pick_flow),
]


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    for name, fn in ANIMS:
        path = os.path.join(OUT, name)
        fn().save(path)
        audit_anim(name, path)
    print(f"wrote {len(ANIMS)} anims -> {OUT}")


if __name__ == "__main__":
    main()

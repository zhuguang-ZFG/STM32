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
    s = Svg(W, H, "FAQ BOOT0 low path", "jumper 0 → Flash alias → app runs")
    s.header(title="FAQ：BOOT0 拉低后从 Flash 启动", subtitle="mechanism · FA-002 continuous-line",
             tag="18", tag_color=T.CYAN)
    css = []
    steps = [
        ("CHECK", "pin44", T.CYAN),
        ("LOW", "BOOT0=0", T.GREEN),
        ("FLASH", "0x08000000", T.AMBER),
        ("MSP", "stack", T.VIOLET),
        ("PC", "Reset", T.GREEN),
        ("APP", "runs", T.CYAN),
    ]
    _flow_row(s, steps, css)
    s.title_block(40, 230, "Symptom 'flash ok, dead after reset' — measure BOOT0 before rewriting C", color=T.GREEN)
    rows = [
        ("Meter", "BOOT0 near 0 V to GND", T.CYAN),
        ("Silk", "jumper on '0' / Flash", T.AMBER),
        ("Vectors", "first two words look like stack+Thumb", T.GREEN),
        ("Next", "if still dead → CFSR ladder", T.VIOLET),
    ]
    for i, (a, b, col) in enumerate(rows):
        y = 265 + i * 44
        s.rect(40, y, 820, 38, fill=T.PANEL, stroke=T.STROKE, rx=8)
        s.text(56, y + 24, a, size=13, fill=col, weight="700", mono=True)
        s.text(840, y + 24, b, size=13, fill=T.TEXT, anchor="end")
    s.rect(40, 450, 820, 70, fill=T.BG2, stroke=T.RED, rx=8)
    s.text(56, 478, "High BOOT / ISP mode stays on static FAQ cards + boot0-low.gif.", size=13, fill=T.TEXT)
    s.text(56, 500, "Do not animate optimizer -O0 myths here.", size=12, fill=T.MUTED)
    css.append("@media (prefers-reduced-motion: reduce){*{animation:none!important}}")
    s.add_style("\n".join(css))
    s.footer(note="自绘矢量动画 · FA-002 · FAQ BOOT0 路径",
             label="自绘矢量动画 · STM32 知识库")
    return s


def slot_fill_flow() -> Svg:
    s = Svg(W, H, "One APP slot fill", "16 KB + 2 KB + 0xB800 → 0x08010000")
    s.header(title="单槽：16 KB 引导 + 2 KB 缝 + 0xB800 应用", subtitle="mechanism · FA-002 continuous-line",
             tag="19", tag_color=T.AMBER)
    css = []
    steps = [
        ("BOOT", "16 KB", T.CYAN),
        ("GAP", "2 KB", T.GREEN),
        ("APP0", "0x08004800", T.AMBER),
        ("SIZE", "0xB800", T.VIOLET),
        ("END", "0x08010000", T.GREEN),
        ("FIT", "64 KB", T.CYAN),
    ]
    _flow_row(s, steps, css)
    s.title_block(40, 230, "Single image only — second slot / SRAM overflow stay on static SVG", color=T.GREEN)
    rows = [
        ("Boot", "0x08000000 .. 16 KB", T.CYAN),
        ("APP base", "0x08004800", T.AMBER),
        ("Length", "0xB800 ends at 0x08010000", T.GREEN),
        ("C8 ceiling", "64 KB Flash total", T.VIOLET),
    ]
    for i, (a, b, col) in enumerate(rows):
        y = 265 + i * 44
        s.rect(40, y, 820, 38, fill=T.PANEL, stroke=T.STROKE, rx=8)
        s.text(56, y + 24, a, size=13, fill=col, weight="700", mono=True)
        s.text(840, y + 24, b, size=13, fill=T.TEXT, anchor="end")
    s.rect(40, 450, 820, 70, fill=T.BG2, stroke=T.RED, rx=8)
    s.text(56, 478, "Motion fills one slot math — not a dual-bank story.", size=13, fill=T.TEXT)
    s.text(56, 500, "Oversized .bss demos stay on sample-19-sram-budget.", size=12, fill=T.MUTED)
    css.append("@media (prefers-reduced-motion: reduce){*{animation:none!important}}")
    s.add_style("\n".join(css))
    s.footer(note="自绘矢量动画 · FA-002 · 单槽 Flash 布局",
             label="自绘矢量动画 · STM32 知识库")
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

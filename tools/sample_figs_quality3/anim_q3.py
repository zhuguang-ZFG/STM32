#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mechanism animations for ch11–17 — new files only."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from svgkit import Svg, T, anim_flow
from sample_figs_quality3._common import audit_anim

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


def iwdg_feed_flow() -> Svg:
    s = Svg(W, H, "IWDG feed before zero", "625 Hz countdown; feed while count > 0")
    s.header(title="IWDG：625 Hz 倒数，到 0 前喂狗", subtitle="mechanism · FA-002 continuous-line",
             tag="11", tag_color=T.AMBER)
    css = []
    steps = [
        ("LSI", "40 kHz typ", T.CYAN),
        ("/64", "625 Hz", T.GREEN),
        ("RLR", "624", T.AMBER),
        ("COUNT", "N..1", T.VIOLET),
        ("FEED", "KR=0xAAAA", T.GREEN),
        ("OK", "no reset", T.CYAN),
    ]
    bw, gap, x0, y0, bh = 120, 18, 40, 100, 100
    for i, (t, n, col) in enumerate(steps):
        x = x0 + i * (bw + gap)
        s.rect(x, y0, bw, bh, fill=T.PANEL, stroke=col, rx=8)
        s.text(x + bw / 2, y0 + 32, t, size=13, anchor="middle", fill=col, weight="700")
        s.text(x + bw / 2, y0 + 60, n, size=12, anchor="middle", fill=T.TEXT, mono=True)
        s.rect(x, y0, bw, bh, fill=col, rx=8, cls=f"s{i}", opacity=0.12)
        if i < len(steps) - 1:
            ax1, ax2 = x + bw + 4, x + bw + gap - 4
            s.arrow(ax1, y0 + bh / 2, ax2, y0 + bh / 2, color=T.STROKE, sw=2)
            s.line(ax1, y0 + bh / 2, ax2, y0 + bh / 2, stroke=T.CYAN, sw=2, cls=f"f{i}")
            css.append(anim_flow(f".f{i}", dur="1.2s", dash="6 12", shift=-18))
    css.append(_step_highlight("s", 6, period=7.0))
    s.title_block(40, 230, "Happy path only — zero and WWDG window stay on static SVGs", color=T.GREEN)
    rows = [
        ("f_LSI typical", "40 kHz (DS range 30–60)", T.CYAN),
        ("Prescaler 64", "tick = 625 Hz", T.GREEN),
        ("Reload", "624 => (624+1)/625 = 1 s", T.AMBER),
        ("Feed key", "0xAAAA reloads the counter", T.VIOLET),
    ]
    for i, (a, b, col) in enumerate(rows):
        y = 265 + i * 44
        s.rect(40, y, 820, 38, fill=T.PANEL, stroke=T.STROKE, rx=8)
        s.text(56, y + 24, a, size=13, fill=col, weight="700", mono=True)
        s.text(840, y + 24, b, size=13, fill=T.TEXT, anchor="end")
    s.rect(40, 450, 820, 70, fill=T.BG2, stroke=T.RED, rx=8)
    s.text(56, 478, "Motion advances LSI→tick→count→feed — not a bounce loop.", size=13, fill=T.TEXT)
    s.text(56, 500, "Late feed (=0) and Reload=625 mistakes stay on sample-11-iwdg-math.", size=12, fill=T.MUTED)
    css.append("@media (prefers-reduced-motion: reduce){*{animation:none!important}}")
    s.add_style("\n".join(css))
    s.footer(note="自绘矢量动画 · FA-002 · IWDG 喂狗机制，非示波器实测",
             label="自绘矢量动画 · STM32 知识库")
    return s


def iap_jump_flow() -> Svg:
    s = Svg(W, H, "IAP unlock and jump", "KEY1 KEY2 then MSP + Reset_Handler")
    s.header(title="IAP：按序解锁，再装 MSP 与复位向量", subtitle="mechanism · FA-002 continuous-line",
             tag="12", tag_color=T.CYAN)
    css = []
    steps = [
        ("KEY1", "0x45670123", T.CYAN),
        ("KEY2", "0xCDEF89AB", T.GREEN),
        ("PROG", "half-word", T.AMBER),
        ("MSP", "word0", T.VIOLET),
        ("RESET", "word1", T.GREEN),
        ("VTOR", "0x08004800", T.CYAN),
    ]
    bw, gap, x0, y0, bh = 120, 18, 40, 100, 100
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
    css.append(_step_highlight("s", 6, period=7.0))
    s.title_block(40, 230, "APP base 0x08004800 · length 0xB800 — reverse keys stay on static SVG", color=T.GREEN)
    rows = [
        ("FLASH_KEYR", "KEY1 then KEY2 clears CR.LOCK", T.CYAN),
        ("Program", "16-bit half-word only on F1", T.AMBER),
        ("Vector load", "MSP @ +0, Reset_Handler @ +4", T.GREEN),
        ("VTOR", "must equal APP base", T.VIOLET),
    ]
    for i, (a, b, col) in enumerate(rows):
        y = 265 + i * 44
        s.rect(40, y, 820, 38, fill=T.PANEL, stroke=T.STROKE, rx=8)
        s.text(56, y + 24, a, size=13, fill=col, weight="700", mono=True)
        s.text(840, y + 24, b, size=13, fill=T.TEXT, anchor="end")
    s.rect(40, 450, 820, 70, fill=T.BG2, stroke=T.RED, rx=8)
    s.text(56, 478, "Motion advances unlock→program→vector→VTOR — teaching path only.", size=13, fill=T.TEXT)
    s.text(56, 500, "Reversed keys / wrong end page stay on sample-12-key-order.", size=12, fill=T.MUTED)
    css.append("@media (prefers-reduced-motion: reduce){*{animation:none!important}}")
    s.add_style("\n".join(css))
    s.footer(note="自绘矢量动画 · FA-002 · IAP 跳转机制，非量产升级日志",
             label="自绘矢量动画 · STM32 知识库")
    return s


def can_arb_flow() -> Svg:
    s = Svg(W, H, "CAN 500 kbit bit time", "8 quanta of 250 ns; sample at 75%")
    s.header(title="CAN：8 个 250 ns 时间份额组成 500 kbit/s", subtitle="mechanism · FA-002 continuous-line",
             tag="13", tag_color=T.GREEN)
    css = []
    steps = [
        ("TQ1", "sync", T.CYAN),
        ("TQ2-3", "BS1", T.GREEN),
        ("TQ4-6", "BS1", T.GREEN),
        ("SAMPLE", "75%", T.AMBER),
        ("TQ7-8", "BS2", T.VIOLET),
        ("BIT", "2 us", T.CYAN),
    ]
    bw, gap, x0, y0, bh = 120, 18, 40, 100, 100
    for i, (t, n, col) in enumerate(steps):
        x = x0 + i * (bw + gap)
        s.rect(x, y0, bw, bh, fill=T.PANEL, stroke=col, rx=8)
        s.text(x + bw / 2, y0 + 32, t, size=13, anchor="middle", fill=col, weight="700", mono=True)
        s.text(x + bw / 2, y0 + 60, n, size=12, anchor="middle", fill=T.TEXT)
        s.rect(x, y0, bw, bh, fill=col, rx=8, cls=f"s{i}", opacity=0.12)
        if i < len(steps) - 1:
            ax1, ax2 = x + bw + 4, x + bw + gap - 4
            s.arrow(ax1, y0 + bh / 2, ax2, y0 + bh / 2, color=T.STROKE, sw=2)
            s.line(ax1, y0 + bh / 2, ax2, y0 + bh / 2, stroke=T.CYAN, sw=2, cls=f"f{i}")
            css.append(anim_flow(f".f{i}", dur="1.0s", dash="5 10", shift=-15))
    css.append(_step_highlight("s", 6, period=6.5))
    s.title_block(40, 230, "36 MHz APB1 · prescaler 9 · 8 TQ — wrong 450 kbit stays on static SVG", color=T.GREEN)
    rows = [
        ("Tq", "9 / 36e6 = 250 ns", T.CYAN),
        ("Bit", "8 x 250 ns = 2 us => 500 kbit/s", T.GREEN),
        ("Sample", "(1+5)/8 = 75% at 1.5 us", T.AMBER),
        ("Wire", "CANH/CANL + 120 Ω each end", T.VIOLET),
    ]
    for i, (a, b, col) in enumerate(rows):
        y = 265 + i * 44
        s.rect(40, y, 820, 38, fill=T.PANEL, stroke=T.STROKE, rx=8)
        s.text(56, y + 24, a, size=13, fill=col, weight="700", mono=True)
        s.text(840, y + 24, b, size=13, fill=T.TEXT, anchor="end")
    s.rect(40, 450, 820, 70, fill=T.BG2, stroke=T.RED, rx=8)
    s.text(56, 478, "Motion walks quanta to the sample point — continuous teaching line.", size=13, fill=T.TEXT)
    s.text(56, 500, "TEC 128 / bus-off story stays on sample-13-tec-busoff.", size=12, fill=T.MUTED)
    css.append("@media (prefers-reduced-motion: reduce){*{animation:none!important}}")
    s.add_style("\n".join(css))
    s.footer(note="自绘矢量动画 · FA-002 · CAN 位时机制，非总线分析仪截图",
             label="自绘矢量动画 · STM32 知识库")
    return s


def usb_48m_flow() -> Svg:
    s = Svg(W, H, "USB 48 MHz enum path", "D+ pull-up, 48 MHz, 18 then 67 bytes")
    s.header(title="USB：D+ 上拉 → 48 MHz → 18/67 字节描述符", subtitle="mechanism · FA-002 continuous-line",
             tag="14", tag_color=T.VIOLET)
    css = []
    steps = [
        ("D+", "pull-up", T.CYAN),
        ("HOST", "sees FS", T.GREEN),
        ("USBPRE", "= 0", T.AMBER),
        ("48 MHz", "USBCLK", T.VIOLET),
        ("18 B", "device", T.GREEN),
        ("67 B", "config", T.CYAN),
    ]
    bw, gap, x0, y0, bh = 120, 18, 40, 100, 100
    for i, (t, n, col) in enumerate(steps):
        x = x0 + i * (bw + gap)
        s.rect(x, y0, bw, bh, fill=T.PANEL, stroke=col, rx=8)
        s.text(x + bw / 2, y0 + 32, t, size=13, anchor="middle", fill=col, weight="700", mono=True)
        s.text(x + bw / 2, y0 + 60, n, size=12, anchor="middle", fill=T.TEXT)
        s.rect(x, y0, bw, bh, fill=col, rx=8, cls=f"s{i}", opacity=0.12)
        if i < len(steps) - 1:
            ax1, ax2 = x + bw + 4, x + bw + gap - 4
            s.arrow(ax1, y0 + bh / 2, ax2, y0 + bh / 2, color=T.STROKE, sw=2)
            s.line(ax1, y0 + bh / 2, ax2, y0 + bh / 2, stroke=T.CYAN, sw=2, cls=f"f{i}")
            css.append(anim_flow(f".f{i}", dur="1.2s", dash="6 12", shift=-18))
    css.append(_step_highlight("s", 6, period=7.0))
    s.title_block(40, 230, "Happy enum path — wrong USBPRE / D− pull-up stay on static SVGs", color=T.GREEN)
    rows = [
        ("PA12 DP", "1.5 kΩ to 3.3 V marks full-speed", T.CYAN),
        ("USBPRE", "0 => divide PLL by 1.5 => 48 MHz", T.GREEN),
        ("Device desc", "18 bytes", T.AMBER),
        ("Config set", "67 bytes (wTotalLength)", T.VIOLET),
    ]
    for i, (a, b, col) in enumerate(rows):
        y = 265 + i * 44
        s.rect(40, y, 820, 38, fill=T.PANEL, stroke=T.STROKE, rx=8)
        s.text(56, y + 24, a, size=13, fill=col, weight="700", mono=True)
        s.text(840, y + 24, b, size=13, fill=T.TEXT, anchor="end")
    s.rect(40, 450, 820, 70, fill=T.BG2, stroke=T.RED, rx=8)
    s.text(56, 478, "Motion advances attach→clock→descriptors — not a bounce loop.", size=13, fill=T.TEXT)
    s.text(56, 500, "PMA overlap / endpoint mistakes stay on sample-14-pma-map.", size=12, fill=T.MUTED)
    css.append("@media (prefers-reduced-motion: reduce){*{animation:none!important}}")
    s.add_style("\n".join(css))
    s.footer(note="自绘矢量动画 · FA-002 · USB 枚举时钟路径，非抓包证明",
             label="自绘矢量动画 · STM32 知识库")
    return s


def rtos_tick_flow() -> Svg:
    s = Svg(W, H, "RTOS 1 ms tick", "priority 2 runs; priority 1 waits; 128 words")
    s.header(title="RTOS：1 ms 节拍，优先级 2 先跑", subtitle="mechanism · FA-002 continuous-line",
             tag="15", tag_color=T.AMBER)
    css = []
    steps = [
        ("TICK", "1 ms", T.CYAN),
        ("READY", "prio list", T.GREEN),
        ("RUN p2", "on CPU", T.AMBER),
        ("WAIT p1", "ready", T.VIOLET),
        ("STACK", "128 words", T.GREEN),
        ("BYTES", "512 B", T.CYAN),
    ]
    bw, gap, x0, y0, bh = 120, 18, 40, 100, 100
    for i, (t, n, col) in enumerate(steps):
        x = x0 + i * (bw + gap)
        s.rect(x, y0, bw, bh, fill=T.PANEL, stroke=col, rx=8)
        s.text(x + bw / 2, y0 + 32, t, size=13, anchor="middle", fill=col, weight="700")
        s.text(x + bw / 2, y0 + 60, n, size=12, anchor="middle", fill=T.TEXT, mono=True)
        s.rect(x, y0, bw, bh, fill=col, rx=8, cls=f"s{i}", opacity=0.12)
        if i < len(steps) - 1:
            ax1, ax2 = x + bw + 4, x + bw + gap - 4
            s.arrow(ax1, y0 + bh / 2, ax2, y0 + bh / 2, color=T.STROKE, sw=2)
            s.line(ax1, y0 + bh / 2, ax2, y0 + bh / 2, stroke=T.CYAN, sw=2, cls=f"f{i}")
            css.append(anim_flow(f".f{i}", dur="1.2s", dash="6 12", shift=-18))
    css.append(_step_highlight("s", 6, period=7.0))
    s.title_block(40, 230, "1000 Hz tick · words not bytes — FromISR mistakes stay on static SVG", color=T.GREEN)
    rows = [
        ("configTICK_RATE_HZ", "1000 => 1 ms", T.CYAN),
        ("Preemption", "priority 2 before priority 1", T.AMBER),
        ("Stack unit", "128 words = 512 bytes", T.GREEN),
        ("HAL clash", "move HAL timebase off SysTick", T.VIOLET),
    ]
    for i, (a, b, col) in enumerate(rows):
        y = 265 + i * 44
        s.rect(40, y, 820, 38, fill=T.PANEL, stroke=T.STROKE, rx=8)
        s.text(56, y + 24, a, size=13, fill=col, weight="700", mono=True)
        s.text(840, y + 24, b, size=13, fill=T.TEXT, anchor="end")
    s.rect(40, 450, 820, 70, fill=T.BG2, stroke=T.RED, rx=8)
    s.text(56, 478, "Motion advances tick→schedule→stack math — teaching path only.", size=13, fill=T.TEXT)
    s.text(56, 500, "FromISR wall chart is sample-15-fromisr; assert stops stay there too.", size=12, fill=T.MUTED)
    css.append("@media (prefers-reduced-motion: reduce){*{animation:none!important}}")
    s.add_style("\n".join(css))
    s.footer(note="自绘矢量动画 · FA-002 · RTOS 节拍调度，非逻辑分析仪轨迹",
             label="自绘矢量动画 · STM32 知识库")
    return s


def stop_wake_flow() -> Svg:
    s = Svg(W, H, "Stop wake restore", "HSI 8 MHz → PLL 72 MHz → 115200")
    s.header(title="Stop 唤醒：HSI 8 MHz 装回 72 MHz 再开串口", subtitle="mechanism · FA-002 continuous-line",
             tag="16", tag_color=T.GREEN)
    css = []
    steps = [
        ("STOP", "LP reg", T.CYAN),
        ("WAKE", "PA0/RTC", T.GREEN),
        ("HSI", "8 MHz", T.AMBER),
        ("PLL", "72 MHz", T.VIOLET),
        ("UART", "re-init", T.GREEN),
        ("115200", "clean", T.CYAN),
    ]
    bw, gap, x0, y0, bh = 120, 18, 40, 100, 100
    for i, (t, n, col) in enumerate(steps):
        x = x0 + i * (bw + gap)
        s.rect(x, y0, bw, bh, fill=T.PANEL, stroke=col, rx=8)
        s.text(x + bw / 2, y0 + 32, t, size=13, anchor="middle", fill=col, weight="700")
        s.text(x + bw / 2, y0 + 60, n, size=12, anchor="middle", fill=T.TEXT, mono=True)
        s.rect(x, y0, bw, bh, fill=col, rx=8, cls=f"s{i}", opacity=0.12)
        if i < len(steps) - 1:
            ax1, ax2 = x + bw + 4, x + bw + gap - 4
            s.arrow(ax1, y0 + bh / 2, ax2, y0 + bh / 2, color=T.STROKE, sw=2)
            s.line(ax1, y0 + bh / 2, ax2, y0 + bh / 2, stroke=T.CYAN, sw=2, cls=f"f{i}")
            css.append(anim_flow(f".f{i}", dur="1.2s", dash="6 12", shift=-18))
    css.append(_step_highlight("s", 6, period=7.0))
    s.title_block(40, 230, "Happy restore — 12800 bit/s miss stays on sample-16-clock-restore", color=T.GREEN)
    rows = [
        ("Stop current", "14 µA LP regulator, no IWDG (DS)", T.CYAN),
        ("Wake clock", "HSI 8 MHz until SystemClock_Config", T.AMBER),
        ("Restore", "PLL back to 72 MHz", T.GREEN),
        ("UART proof", "115200 after restore", T.VIOLET),
    ]
    for i, (a, b, col) in enumerate(rows):
        y = 265 + i * 44
        s.rect(40, y, 820, 38, fill=T.PANEL, stroke=T.STROKE, rx=8)
        s.text(56, y + 24, a, size=13, fill=col, weight="700", mono=True)
        s.text(840, y + 24, b, size=13, fill=T.TEXT, anchor="end")
    s.rect(40, 450, 820, 70, fill=T.BG2, stroke=T.RED, rx=8)
    s.text(56, 478, "Motion advances Stop→wake→HSI→PLL→UART — continuous teaching line.", size=13, fill=T.TEXT)
    s.text(56, 500, "Current-table nuance stays on sample-16-mode-current.", size=12, fill=T.MUTED)
    css.append("@media (prefers-reduced-motion: reduce){*{animation:none!important}}")
    s.add_style("\n".join(css))
    s.footer(note="自绘矢量动画 · FA-002 · Stop 唤醒时钟恢复，非电流探头波形",
             label="自绘矢量动画 · STM32 知识库")
    return s


def cfsr_flow() -> Svg:
    s = Svg(W, H, "CFSR then BFAR", "bit 15 = 1 unlocks BFAR; 72 counts = 1 us")
    s.header(title="CFSR：bit 15=1 才采信 BFAR，再数 72 拍", subtitle="mechanism · FA-002 continuous-line",
             tag="17", tag_color=T.AMBER)
    css = []
    steps = [
        ("FAULT", "HardFault", T.RED),
        ("CFSR", "0xE000ED28", T.CYAN),
        ("bit15", "= 1", T.GREEN),
        ("BFAR", "address", T.AMBER),
        ("DWT", "count 72", T.VIOLET),
        ("1 us", "@ 72 MHz", T.CYAN),
    ]
    bw, gap, x0, y0, bh = 120, 18, 40, 100, 100
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
    css.append(_step_highlight("s", 6, period=7.0))
    s.title_block(40, 230, "Happy decode — bit15=0 stale BFAR stays on sample-17-cfsr-bits", color=T.GREEN)
    rows = [
        ("CFSR", "read first at 0xE000ED28", T.CYAN),
        ("BFARVALID", "bit 15 must be 1", T.GREEN),
        ("HFSR FORCED", "bit 30 => look inside CFSR", T.AMBER),
        ("DWT CYCCNT", "72 counts = 1 us at 72 MHz", T.VIOLET),
    ]
    for i, (a, b, col) in enumerate(rows):
        y = 265 + i * 44
        s.rect(40, y, 820, 38, fill=T.PANEL, stroke=T.STROKE, rx=8)
        s.text(56, y + 24, a, size=13, fill=col, weight="700", mono=True)
        s.text(840, y + 24, b, size=13, fill=T.TEXT, anchor="end")
    s.rect(40, 450, 820, 70, fill=T.BG2, stroke=T.RED, rx=8)
    s.text(56, 478, "Motion advances fault→CFSR→BFAR→timing — teaching path only.", size=13, fill=T.TEXT)
    s.text(56, 500, "SWD pin conflicts stay on sample-17-swd-pins.", size=12, fill=T.MUTED)
    css.append("@media (prefers-reduced-motion: reduce){*{animation:none!important}}")
    s.add_style("\n".join(css))
    s.footer(note="自绘矢量动画 · FA-002 · CFSR 判读机制，非在线调试会话",
             label="自绘矢量动画 · STM32 知识库")
    return s


ANIMS = [
    ("sample-11-iwdg-feed-flow.svg", iwdg_feed_flow),
    ("sample-12-iap-jump-flow.svg", iap_jump_flow),
    ("sample-13-can-arb-flow.svg", can_arb_flow),
    ("sample-14-usb-48m-flow.svg", usb_48m_flow),
    ("sample-15-rtos-tick-flow.svg", rtos_tick_flow),
    ("sample-16-stop-wake-flow.svg", stop_wake_flow),
    ("sample-17-cfsr-flow.svg", cfsr_flow),
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

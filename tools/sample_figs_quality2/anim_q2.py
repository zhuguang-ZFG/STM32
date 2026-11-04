#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mechanism animations for ch04/05/07/08 — new files only."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from svgkit import Svg, T, anim_flow, anim_tx
from sample_figs_quality2._common import audit_anim

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


def nvic_preempt_flow() -> Svg:
    s = Svg(W, H, "NVIC preemption", "EXTI0 preempt 1 interrupts TIM2 preempt 2")
    s.header(title="NVIC 抢占：EXTI0 打断 TIM2，再返回", subtitle="mechanism · FA-002 continuous-line",
             tag="04", tag_color=T.CYAN)
    css = []
    steps = [
        ("TIM2 RUN", "preempt 2", T.AMBER),
        ("EXTI0", "preempt 1", T.GREEN),
        ("STACK 8", "R0-R3,R12,LR,PC,xPSR", T.CYAN),
        ("EXTI ISR", "higher runs", T.VIOLET),
        ("UNSTACK", "return", T.AMBER),
        ("TIM2", "resumes", T.GREEN),
    ]
    bw = 120
    gap = 18
    x0, y0, bh = 40, 100, 100
    for i, (t, n, col) in enumerate(steps):
        x = x0 + i * (bw + gap)
        s.rect(x, y0, bw, bh, fill=T.PANEL, stroke=col, rx=8)
        s.text(x + bw / 2, y0 + 32, t, size=13, anchor="middle", fill=col, weight="700")
        s.text(x + bw / 2, y0 + 60, n, size=11, anchor="middle", fill=T.TEXT)
        s.rect(x, y0, bw, bh, fill=col, rx=8, cls=f"s{i}", opacity=0.12)
        if i < len(steps) - 1:
            ax1, ax2 = x + bw + 4, x + bw + gap - 4
            s.arrow(ax1, y0 + bh / 2, ax2, y0 + bh / 2, color=T.STROKE, sw=2)
            s.line(ax1, y0 + bh / 2, ax2, y0 + bh / 2, stroke=T.CYAN, sw=2, cls=f"f{i}")
            css.append(anim_flow(f".f{i}", dur="1.2s", dash="6 12", shift=-18))
    css.append(_step_highlight("s", 6, period=7.0))
    s.title_block(40, 230, "GROUP4 example — higher preempt wins (failure path on static SVG)", color=T.GREEN)
    rows = [
        ("AIRCR PRIGROUP", "GROUP4 => 3 preempt bits", T.CYAN),
        ("TIM2 IPRx", "preempt=2 running", T.AMBER),
        ("EXTI0 IPRx", "preempt=1 arrives", T.GREEN),
        ("Stacking", "~12 cycles entry on M3", T.VIOLET),
    ]
    for i, (a, b, col) in enumerate(rows):
        y = 265 + i * 44
        s.rect(40, y, 820, 38, fill=T.PANEL, stroke=T.STROKE, rx=8)
        s.text(56, y + 24, a, size=13, fill=col, weight="700", mono=True)
        s.text(840, y + 24, b, size=13, fill=T.TEXT, anchor="end")
    s.rect(40, 450, 820, 70, fill=T.BG2, stroke=T.RED, rx=8)
    s.text(56, 478, "Motion advances TIM2→EXTI→stack→ISR→return — not a bounce loop.", size=13, fill=T.TEXT)
    s.text(56, 500, "Equal preempt failure stays on sample-04-exti-triage / exception-stack.", size=12, fill=T.MUTED)
    css.append("@media (prefers-reduced-motion: reduce){*{animation:none!important}}")
    s.add_style("\n".join(css))
    s.footer(note="自绘矢量动画 · FA-002 · NVIC 抢占机制，非逻辑分析仪实拍",
             label="自绘矢量动画 · STM32 知识库")
    return s


def pwm_edge_flow() -> Svg:
    s = Svg(W, H, "PWM compare edge", "CNT walks; CCR=500 flips output")
    s.header(title="PWM 边沿：CNT 走到 CCR=500 翻电平", subtitle="mechanism · FA-002 continuous-line",
             tag="05", tag_color=T.AMBER)
    css = []
    s.rect(40, 100, 820, 70, fill=T.PANEL, stroke=T.STROKE, rx=8)
    s.text(56, 130, "TIM3  PSC=71  ARR=999  CCR=500  => 1 kHz, 50%", size=15, fill=T.TEXT, weight="700", mono=True)
    s.text(56, 154, "f_tim 72 MHz / 72 / 1000 = 1000 Hz", size=13, fill=T.MUTED, mono=True)
    marks = [
        ("CNT=0", "HIGH", T.GREEN, 0.0),
        ("250", "HIGH", T.GREEN, 0.25),
        ("CCR 500", "EDGE", T.AMBER, 0.5),
        ("750", "LOW", T.CYAN, 0.75),
        ("999", "LOW", T.CYAN, 1.0),
    ]
    for i, (t, st, col, frac) in enumerate(marks):
        x = 60 + i * 160
        s.rect(x, 200, 140, 90, fill=T.PANEL, stroke=col, rx=8)
        s.text(x + 70, 232, t, size=13, anchor="middle", fill=col, weight="700", mono=True)
        s.text(x + 70, 264, st, size=14, anchor="middle", fill=T.TEXT, weight="700")
        s.rect(x, 200, 140, 90, fill=col, rx=8, cls=f"s{i}", opacity=0.12)
        if i < len(marks) - 1:
            s.arrow(x + 144, 245, x + 156, 245, color=T.STROKE, sw=2)
            s.line(x + 144, 245, x + 156, 245, stroke=T.CYAN, sw=2, cls=f"f{i}")
            css.append(anim_flow(f".f{i}", dur="1.0s", dash="5 10", shift=-15))
    css.append(_step_highlight("s", 5, period=5.5))
    # waveform bar
    s.rect(40, 320, 820, 80, fill=T.BG2, stroke=T.GREEN, rx=8)
    s.text(56, 350, "Output high ________/          \\________  (edge at CCR)", size=14, fill=T.GREEN, mono=True)
    s.text(56, 378, "500 us high + 500 us low each 1 ms period", size=13, fill=T.TEXT)
    s.rect(40, 430, 820, 80, fill=T.PANEL, stroke=T.RED, rx=8)
    s.text(56, 460, "Slow-path mistakes (wrong f_tim) stay on sample-05-pwm-debug — this anim only shows the happy edge.",
           size=13, fill=T.TEXT)
    s.text(56, 486, "Pairs with pwm-1khz.gif denser frames; PDF first frame still readable.", size=12, fill=T.MUTED)
    css.append("@media (prefers-reduced-motion: reduce){*{animation:none!important}}")
    s.add_style("\n".join(css))
    s.footer(note="自绘矢量动画 · FA-002 · PWM 比较翻转，非示波器实拍",
             label="自绘矢量动画 · STM32 知识库")
    return s


def i2c_ack_flow() -> Svg:
    s = Svg(W, H, "I2C address ACK", "START → 0x78 → 9th clock ACK")
    s.header(title="I2C 寻址应答：START → 0x78 → ACK", subtitle="mechanism · FA-002 continuous-line",
             tag="07", tag_color=T.GREEN)
    css = []
    steps = [
        ("START", "SDA↓ SCL=1", T.AMBER),
        ("0x78", "shift 8 bits", T.CYAN),
        ("R/W0", "write", T.VIOLET),
        ("9th", "SCL pulse", T.AMBER),
        ("ACK", "SDA low", T.GREEN),
        ("0x801E", "4.7 k", T.CYAN),
    ]
    bw = 120
    gap = 18
    for i, (t, n, col) in enumerate(steps):
        x = 40 + i * (bw + gap)
        s.rect(x, 100, bw, 100, fill=T.PANEL, stroke=col, rx=8)
        s.text(x + bw / 2, 132, t, size=14, anchor="middle", fill=col, weight="700", mono=True)
        s.text(x + bw / 2, 164, n, size=12, anchor="middle", fill=T.TEXT)
        s.rect(x, 100, bw, 100, fill=col, rx=8, cls=f"s{i}", opacity=0.12)
        if i < len(steps) - 1:
            ax1 = x + bw + 4
            ax2 = x + bw + gap - 4
            s.arrow(ax1, 150, ax2, 150, color=T.STROKE, sw=2)
            s.line(ax1, 150, ax2, 150, stroke=T.CYAN, sw=2, cls=f"f{i}")
            css.append(anim_flow(f".f{i}", dur="1.1s", dash="6 12", shift=-18))
    css.append(_step_highlight("s", 6, period=6.5))
    s.title_block(40, 230, "Wire facts (PB6 SCL / PB7 SDA)", color=T.GREEN)
    rows = [
        ("HAL OLED_ADDR", "0x3C<<1 = 0x78 on the bus", T.CYAN),
        ("9th clock", "slave drives ACK low", T.GREEN),
        ("CCR hint", "0x801E @ ~100 kHz class", T.AMBER),
        ("Pull-up", "4.7 k to 3.3 V typical start", T.VIOLET),
    ]
    for i, (a, b, col) in enumerate(rows):
        y = 265 + i * 44
        s.rect(40, y, 820, 38, fill=T.PANEL, stroke=T.STROKE, rx=8)
        s.text(56, y + 24, a, size=13, fill=col, weight="700", mono=True)
        s.text(840, y + 24, b, size=13, fill=T.TEXT, anchor="end")
    s.rect(40, 450, 820, 70, fill=T.BG2, stroke=T.RED, rx=8)
    s.text(56, 478, "NACK / missing pull-up stay on sample-07-i2c-triage — this anim is the ACK success path.",
           size=13, fill=T.TEXT)
    s.text(56, 500, "Motion is phase advance, not decorative pulse.", size=12, fill=T.MUTED)
    css.append("@media (prefers-reduced-motion: reduce){*{animation:none!important}}")
    s.add_style("\n".join(css))
    s.footer(note="自绘矢量动画 · FA-002 · I2C 寻址应答，非逻辑分析仪实拍",
             label="自绘矢量动画 · STM32 知识库")
    return s


def spi_jedec_flow() -> Svg:
    s = Svg(W, H, "SPI JEDEC read", "CS↓ 0x9F → EF 40 17 @ 9 MHz")
    s.header(title="SPI JEDEC：CS↓ → 0x9F → EF 40 17", subtitle="mechanism · FA-002 continuous-line",
             tag="08", tag_color=T.AMBER)
    css = []
    steps = [
        ("CS LOW", "PA4", T.AMBER),
        ("MOSI", "0x9F", T.CYAN),
        ("MISO", "0xEF", T.GREEN),
        ("MISO", "0x40", T.GREEN),
        ("MISO", "0x17", T.GREEN),
        ("CS HIGH", "9 MHz", T.VIOLET),
    ]
    bw = 120
    gap = 18
    for i, (t, n, col) in enumerate(steps):
        x = 40 + i * (bw + gap)
        s.rect(x, 100, bw, 100, fill=T.PANEL, stroke=col, rx=8)
        s.text(x + bw / 2, 132, t, size=13, anchor="middle", fill=col, weight="700")
        s.text(x + bw / 2, 164, n, size=14, anchor="middle", fill=T.TEXT, weight="700", mono=True)
        s.rect(x, 100, bw, 100, fill=col, rx=8, cls=f"s{i}", opacity=0.12)
        if i < len(steps) - 1:
            ax1 = x + bw + 4
            ax2 = x + bw + gap - 4
            s.arrow(ax1, 150, ax2, 150, color=T.STROKE, sw=2)
            s.line(ax1, 150, ax2, 150, stroke=T.CYAN, sw=2, cls=f"f{i}")
            css.append(anim_flow(f".f{i}", dur="1.0s", dash="6 12", shift=-18))
    css.append(_step_highlight("s", 6, period=6.0))
    s.title_block(40, 230, "Mode0 lab pins · BR=010 → 9 MHz from 72 MHz APB2", color=T.AMBER)
    rows = [
        ("PA5 / PA7 / PA6", "SCK / MOSI / MISO", T.CYAN),
        ("CMD 0x9F", "JEDEC ID read", T.AMBER),
        ("Winbond example", "0xEF 0x40 0x17 family", T.GREEN),
        ("BR=010", "/8 => 9 MHz SCK", T.VIOLET),
    ]
    for i, (a, b, col) in enumerate(rows):
        y = 265 + i * 44
        s.rect(40, y, 820, 38, fill=T.PANEL, stroke=T.STROKE, rx=8)
        s.text(56, y + 24, a, size=13, fill=col, weight="700", mono=True)
        s.text(840, y + 24, b, size=13, fill=T.TEXT, anchor="end")
    s.rect(40, 450, 820, 70, fill=T.BG2, stroke=T.RED, rx=8)
    s.text(56, 478, "Swapped MOSI/MISO failure stays on sample-08-spi-jedec / triage — success path only here.",
           size=13, fill=T.TEXT)
    s.text(56, 500, "Phase order matches spi-jedec.gif remake tokens.", size=12, fill=T.MUTED)
    css.append("@media (prefers-reduced-motion: reduce){*{animation:none!important}}")
    s.add_style("\n".join(css))
    s.footer(note="自绘矢量动画 · FA-002 · SPI JEDEC 读 ID，非逻辑分析仪实拍",
             label="自绘矢量动画 · STM32 知识库")
    return s


ANIMS = [
    ("sample-04-nvic-preempt-flow.svg", nvic_preempt_flow),
    ("sample-05-pwm-edge-flow.svg", pwm_edge_flow),
    ("sample-07-i2c-ack-flow.svg", i2c_ack_flow),
    ("sample-08-spi-jedec-flow.svg", spi_jedec_flow),
]


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    for name, fn in ANIMS:
        svg = fn()
        path = os.path.join(OUT, name)
        svg.save(path)
        audit_anim(name, path)
    print(f"wrote {len(ANIMS)} animations -> {OUT}")


if __name__ == "__main__":
    main()

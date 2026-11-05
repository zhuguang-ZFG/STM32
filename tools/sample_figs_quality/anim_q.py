#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Remade / new mechanism animations for pilot chapters 02/03/06/09/10.

New files only — does not overwrite text_hash-locked classics
(clock-tree, gpio-blink, uart-frame, adc-sar, dma-circular).

    python tools/sample_figs_quality/anim_q.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from svgkit import Svg, T, anim_flow, anim_tx
from sample_figs_quality._common import audit_anim

W, H = 900, 620


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


def pll_lock_flow() -> Svg:
    s = Svg(W, H, "PLL lock sequence", "HSE ready → multiply → SWS=PLL")
    s.header(title="PLL 上锁：HSE → x9 → SYSCLK 72 MHz", subtitle="mechanism · FA-002 continuous-line",
             tag="02", tag_color=T.CYAN)
    steps = [
        ("HSEON", "wait HSERDY", "8 MHz", T.AMBER),
        ("PLLSRC", "HSE into PLL", "no /2", T.CYAN),
        ("PLLMUL", "x9 lock", "72 MHz", T.GREEN),
        ("SW/SWS", "switch", "SWS=10", T.VIOLET),
    ]
    bw, gap, x0, y0, bh = 170, 36, 50, 100, 96
    css = []
    for i, (title, sub, note, color) in enumerate(steps):
        x = x0 + i * (bw + gap)
        s.rect(x, y0, bw, bh, fill=T.PANEL, stroke=color, rx=8)
        s.text(x + bw / 2, y0 + 28, title, size=15, anchor="middle", fill=color, weight="700", mono=True)
        s.text(x + bw / 2, y0 + 52, sub, size=13, anchor="middle", fill=T.TEXT)
        s.text(x + bw / 2, y0 + 76, note, size=12, anchor="middle", fill=T.MUTED)
        s.rect(x, y0, bw, bh, fill=color, rx=8, cls=f"s{i}", opacity=0.12)
        if i < len(steps) - 1:
            ax1, ax2 = x + bw + 6, x + bw + gap - 6
            s.arrow(ax1, y0 + bh / 2, ax2, y0 + bh / 2, color=T.STROKE, sw=2)
            s.line(ax1, y0 + bh / 2, ax2, y0 + bh / 2, stroke=T.CYAN, sw=2, cls=f"f{i}")
            s.circle(ax1, y0 + bh / 2, 4, fill=T.CYAN, cls=f"p{i}")
            css.append(anim_flow(f".f{i}", dur="1.5s", dash="6 12", shift=-18))
            css.append(anim_tx(f".p{i}", dur="1.5s", x1=0, x2=gap - 12, delay=f"{i * 0.3:.2f}s"))
    css.append(_step_highlight("s", 4, period=5.5))

    rows = [
        ("RCC_CR HSERDY", "must be 1 before PLLMUL touch", T.AMBER),
        ("RCC_CR PLLRDY", "1 means VCO locked at 72 MHz", T.GREEN),
        ("RCC_CFGR SWS", "10 = SYSCLK from PLL (not HSI)", T.CYAN),
        ("FLASH_ACR LATENCY", "2 wait-states for 48..72 MHz", T.VIOLET),
    ]
    s.title_block(40, 240, "First-frame register ledger (readable in PDF)", color=T.GREEN)
    for i, (reg, note, color) in enumerate(rows):
        y = 270 + i * 48
        s.rect(40, y, 820, 42, fill=T.PANEL, stroke=T.STROKE, rx=8)
        s.text(56, y + 26, reg, size=13, fill=color, weight="700", mono=True)
        s.text(840, y + 26, note, size=13, fill=T.TEXT, anchor="end")

    s.rect(40, 470, 820, 70, fill=T.BG2, stroke=T.RED, rx=8)
    s.text(56, 498, "Motion meaning: highlight advances only after the prior ready bit — not a bounce loop.",
           size=13, fill=T.TEXT)
    s.text(56, 520, "Fail path (HSE lost → CSS → HSI) stays on sample-02-hse-fail / clock-css GIF.",
           size=12, fill=T.MUTED)

    css.append("@media (prefers-reduced-motion: reduce){*{animation:none!important}}")
    s.add_style("\n".join(css))
    s.footer(note="自绘矢量动画 · FA-002 · PLL 上锁机制，非示波器实拍",
             label="自绘矢量动画 · STM32 知识库")
    return s


def gpio_bsrr_flow() -> Svg:
    s = Svg(W, H, "BSRR atomic write", "PC13 active-low LED without ODR RMW")
    s.header(title="GPIO 点灯：BSRR 原子写，避开 ODR 读改写", subtitle="mechanism · FA-002 continuous-line",
             tag="03", tag_color=T.GREEN)
    css = []
    boxes = [
        ("MODER=01", "PC13 output", T.CYAN),
        ("OTYPER=0", "push-pull", T.GREEN),
        ("BSRR set/reset", "one write", T.AMBER),
        ("Pin / LED", "active-low", T.RED),
    ]
    for i, (t, sub, col) in enumerate(boxes):
        x = 40 + i * 215
        s.rect(x, 100, 200, 88, fill=T.PANEL, stroke=col, rx=8)
        s.text(x + 100, 132, t, size=14, anchor="middle", fill=col, weight="700", mono=True)
        s.text(x + 100, 160, sub, size=13, anchor="middle", fill=T.TEXT)
        s.rect(x, 100, 200, 88, fill=col, rx=8, cls=f"g{i}", opacity=0.12)
        if i < 3:
            s.arrow(x + 204, 144, x + 211, 144, color=T.STROKE, sw=2)
            s.line(x + 204, 144, x + 211, 144, stroke=T.CYAN, sw=2, cls=f"gf{i}")
            css.append(anim_flow(f".gf{i}", dur="1.2s"))
    css.append(_step_highlight("g", 4, period=5.0))

    # LED polarity row
    s.title_block(40, 220, "Blue Pill PC13: cathode toward MCU (active-low)", color=T.AMBER)
    s.rect(40, 250, 400, 120, fill=T.PANEL, stroke=T.GREEN, rx=8)
    s.text(56, 280, "ON  BSRR = (1<<13)<<16", size=14, fill=T.GREEN, weight="700", mono=True)
    s.text(56, 308, "drives pin LOW → LED lights", size=13, fill=T.TEXT)
    s.text(56, 336, "EST current ~0.6 mA @ 2.2k", size=12, fill=T.MUTED)
    s.rect(460, 250, 400, 120, fill=T.PANEL, stroke=T.MUTED, rx=8)
    s.text(476, 280, "OFF BSRR = (1<<13)", size=14, fill=T.MUTED, weight="700", mono=True)
    s.text(476, 308, "drives pin HIGH → LED dark", size=13, fill=T.TEXT)
    s.text(476, 336, "Never ODR |= under IRQ", size=12, fill=T.RED)

    s.rect(40, 400, 820, 56, fill=T.BG2, stroke=T.CYAN, rx=8)
    s.text(56, 424, "Highlight order: mode → type → BSRR → pin. First frame keeps both ON/OFF formulas.",
           size=13, fill=T.TEXT)
    s.text(56, 444, "Nucleo PA5 is often active-high — polarity follows the schematic, not this PC13 path.",
           size=12, fill=T.MUTED)

    # soft LED pulse marker
    s.circle(820, 160, 14, fill=T.RED, cls="ledpulse", opacity=0.85)
    css.append(
        "@keyframes ledpulse{0%,45%{opacity:0.25}50%,95%{opacity:0.95}100%{opacity:0.25}}"
        ".ledpulse{animation:ledpulse 2s linear infinite;}"
    )
    css.append("@media (prefers-reduced-motion: reduce){*{animation:none!important}}")
    s.add_style("\n".join(css))
    s.footer(note="自绘矢量动画 · FA-002 · BSRR/PC13 机制，非板级实拍",
             label="自绘矢量动画 · STM32 知识库")
    return s


def uart_baud_wire() -> Svg:
    s = Svg(W, H, "UART baud + wire", "BRR from the right PCLK; TX crosses to RX")
    s.header(title="UART：波特率公式 + TX/RX 交叉", subtitle="mechanism · FA-002 continuous-line",
             tag="06", tag_color=T.CYAN)
    css = []
    # left: baud
    s.rect(40, 96, 400, 200, fill=T.PANEL, stroke=T.CYAN, rx=8)
    s.text(60, 128, "USART1 / PCLK2=72e6", size=14, fill=T.CYAN, weight="700")
    s.text(60, 156, "115200 → BRR 0x0271", size=14, fill=T.TEXT, mono=True)
    s.text(60, 184, "USART2 / PCLK1=36e6", size=14, fill=T.PINK, weight="700")
    s.text(60, 212, "115200 → BRR 0x0139", size=14, fill=T.TEXT, mono=True)
    s.text(60, 248, "Same baud string, half clock → half BRR", size=12, fill=T.MUTED)
    s.rect(40, 96, 400, 200, fill=T.CYAN, rx=8, cls="u0", opacity=0.08)

    # right: crossover
    s.rect(460, 96, 400, 200, fill=T.PANEL, stroke=T.GREEN, rx=8)
    s.text(560, 128, "MCU", size=14, fill=T.CYAN, weight="700")
    s.text(760, 128, "USB-UART", size=14, fill=T.GREEN, weight="700")
    s.text(520, 168, "TX", size=13, fill=T.TEXT)
    s.text(800, 168, "RX", size=13, fill=T.TEXT)
    s.text(520, 208, "RX", size=13, fill=T.TEXT)
    s.text(800, 208, "TX", size=13, fill=T.TEXT)
    s.arrow(545, 164, 785, 164, color=T.AMBER, sw=2)
    s.line(545, 164, 785, 164, stroke=T.AMBER, sw=2, cls="ux0")
    s.arrow(785, 204, 545, 204, color=T.VIOLET, sw=2)
    s.line(545, 204, 785, 204, stroke=T.VIOLET, sw=2, cls="ux1")
    s.text(660, 250, "common GND  ·  3V3 only", size=12, anchor="middle", fill=T.MUTED)
    css.append(anim_flow(".ux0", dur="1.4s", dash="5 10", shift=-15))
    css.append(anim_flow(".ux1", dur="1.4s", dash="5 10", shift=15))
    s.rect(460, 96, 400, 200, fill=T.GREEN, rx=8, cls="u1", opacity=0.08)

    # frame timeline
    s.title_block(40, 330, "8N1 bit time @ 115200 ≈ 8.68 µs (PDF-readable)", color=T.AMBER)
    bits = [("Idle", "1"), ("S", "0"), ("0", "1"), ("1", "0"), ("2", "1"), ("3", "0"),
            ("4", "0"), ("5", "1"), ("6", "0"), ("7", "1"), ("P", "1")]
    for i, (lab, val) in enumerate(bits):
        x = 40 + i * 76
        col = T.RED if lab == "S" else (T.GREEN if lab == "P" else (T.MUTED if lab == "Idle" else T.CYAN))
        s.rect(x, 360, 70, 70, fill=T.PANEL, stroke=col, rx=4)
        s.text(x + 35, 388, lab, size=12, anchor="middle", fill=col, weight="700")
        s.text(x + 35, 412, val, size=16, anchor="middle", fill=T.TEXT, weight="700", mono=True)
        s.rect(x, 360, 70, 70, fill=col, rx=4, cls=f"b{i}", opacity=0.1)
    css.append(_step_highlight("u", 2, period=4.5))
    css.append(_step_highlight("b", 11, period=7.0, window=0.12))

    s.rect(40, 460, 820, 70, fill=T.BG2, stroke=T.RED, rx=8)
    s.text(56, 488, "Trap: USART1 BRR pasted onto USART2; TX-TX wiring; 5V TTL into 3V3 pin.",
           size=13, fill=T.RED, weight="700")
    s.text(56, 510, "Evidence: bit width on scope = 1/baud; idle high before start.",
           size=12, fill=T.MUTED)

    css.append("@media (prefers-reduced-motion: reduce){*{animation:none!important}}")
    s.add_style("\n".join(css))
    s.footer(note="自绘矢量动画 · FA-002 · 波特率与交叉接线，非逻辑分析仪截图",
             label="自绘矢量动画 · STM32 知识库")
    return s


def adc_sar_weights() -> Svg:
    s = Svg(W, H, "SAR weight walk", "12-bit decisions with real thresholds")
    s.header(title="ADC SAR：权重台阶与采样时间预算", subtitle="mechanism · FA-002 continuous-line",
             tag="09", tag_color=T.AMBER)
    css = []
    weights = [
        ("b11", "2048", "1.65 V"),
        ("b10", "1024", "0.825"),
        ("b9", "512", "0.413"),
        ("b8", "256", "0.206"),
        ("…", "…", "…"),
        ("b0", "1", "0.8 mV"),
    ]
    for i, (b, w, v) in enumerate(weights):
        x = 40 + i * 140
        col = T.GREEN if i == 0 else (T.AMBER if i == 5 else T.CYAN)
        s.rect(x, 100, 128, 100, fill=T.PANEL, stroke=col, rx=8)
        s.text(x + 64, 132, b, size=14, anchor="middle", fill=col, weight="700", mono=True)
        s.text(x + 64, 158, w, size=13, anchor="middle", fill=T.TEXT, mono=True)
        s.text(x + 64, 182, v, size=12, anchor="middle", fill=T.MUTED)
        s.rect(x, 100, 128, 100, fill=col, rx=8, cls=f"w{i}", opacity=0.12)
        if i < 5:
            s.arrow(x + 132, 150, x + 136, 150, color=T.STROKE, sw=2)
            # 台阶之间跟一个 token，眼睛能顺着它从 b11 走到 b0
            s.circle(x + 142, 150, 4.6, fill=col, cls=f"d{i}")
    css.append(_step_highlight("w", 6, period=8.4, window=0.18))
    css.append(_step_highlight("d", 6, period=8.4, window=0.18, peak=1.0,
                               rest=0.12))

    s.title_block(40, 240, "Sample time vs soft sources (ADCCLK ≤ 14 MHz)", color=T.CYAN)
    rows = [
        ("SMP 1.5", "low-R pin only", T.GREEN),
        ("SMP 7.5", "general first guess", T.CYAN),
        ("SMP 28.5", "filtered / higher R", T.AMBER),
        ("SMP 239.5", "thermistor / soft", T.VIOLET),
    ]
    for i, (smp, note, col) in enumerate(rows):
        x = 40 + i * 215
        s.rect(x, 270, 200, 70, fill=T.PANEL, stroke=col, rx=8)
        s.text(x + 100, 298, smp, size=14, anchor="middle", fill=col, weight="700", mono=True)
        s.text(x + 100, 322, note, size=12, anchor="middle", fill=T.TEXT)
        s.rect(x, 270, 200, 70, fill=col, rx=8, cls=f"m{i}", opacity=0.1)
    css.append(_step_highlight("m", 4, period=5.0))

    s.rect(40, 370, 820, 100, fill=T.BG2, stroke=T.RED, rx=8)
    s.text(56, 404, "Vin example 1.65 V @ Vref+=3.3 V → mid-scale ~2048. Codes are EST until averaged.",
           size=13, fill=T.TEXT, weight="700")
    s.text(56, 432, "Motion: weight highlight walks MSB→LSB; SMP row shows settling budget, not a bounce.",
           size=12, fill=T.MUTED)

    s.rect(40, 490, 820, 50, fill=T.PANEL, stroke=T.STROKE, rx=8)
    s.text(56, 520, "Pairs with remade adc-sample.gif; static sample-09-sar-ladder freezes the weights.",
           size=13, fill=T.TEXT)

    css.append("@media (prefers-reduced-motion: reduce){*{animation:none!important}}")
    s.add_style("\n".join(css))
    s.footer(note="自绘矢量动画 · FA-002 · SAR 权重与采样时间，非采集卡截图",
             label="自绘矢量动画 · STM32 知识库")
    return s


def dma_circular_ht() -> Svg:
    s = Svg(W, H, "DMA circular HT/TC", "CNDTR countdown with half/full ownership")
    s.header(title="DMA 环形缓冲：CNDTR 倒数与 HT/TC 半区所有权", subtitle="mechanism · FA-002 continuous-line",
             tag="10", tag_color=T.VIOLET)
    css = []
    # buffer halves
    s.rect(40, 100, 400, 140, fill=T.PANEL, stroke=T.GREEN, rx=8)
    s.text(240, 140, "Half A  [0 .. N/2)", size=16, anchor="middle", fill=T.GREEN, weight="700")
    s.text(240, 172, "HT: CPU may read A", size=13, anchor="middle", fill=T.TEXT)
    s.text(240, 200, "DMA writes B", size=13, anchor="middle", fill=T.MUTED)
    s.rect(40, 100, 400, 140, fill=T.GREEN, rx=8, cls="h0", opacity=0.12)

    s.rect(460, 100, 400, 140, fill=T.PANEL, stroke=T.AMBER, rx=8)
    s.text(660, 140, "Half B  [N/2 .. N)", size=16, anchor="middle", fill=T.AMBER, weight="700")
    s.text(660, 172, "TC: CPU may read B", size=13, anchor="middle", fill=T.TEXT)
    s.text(660, 200, "DMA reloads + writes A", size=13, anchor="middle", fill=T.MUTED)
    s.rect(460, 100, 400, 140, fill=T.AMBER, rx=8, cls="h1", opacity=0.12)
    css.append(_step_highlight("h", 2, period=3.6, window=0.45, peak=0.28))

    # CNDTR strip
    s.title_block(40, 280, "Example N=256 halfwords · CNDTR live", color=T.CYAN)
    marks = [("256", "armed"), ("192", "filling A"), ("128", "HT"), ("64", "filling B"), ("0→256", "TC")]
    for i, (n, lab) in enumerate(marks):
        x = 40 + i * 170
        col = T.GREEN if "HT" in lab or "TC" in lab else T.CYAN
        s.rect(x, 310, 155, 70, fill=T.PANEL, stroke=col, rx=8)
        s.text(x + 77, 338, n, size=14, anchor="middle", fill=col, weight="700", mono=True)
        s.text(x + 77, 362, lab, size=12, anchor="middle", fill=T.TEXT)
        s.rect(x, 310, 155, 70, fill=col, rx=8, cls=f"c{i}", opacity=0.1)
    css.append(_step_highlight("c", 5, period=6.0, window=0.16))

    # flowing request line
    s.line(60, 420, 840, 420, stroke=T.VIOLET, sw=2, cls="req")
    s.circle(60, 420, 5, fill=T.VIOLET, cls="tok")
    css.append(anim_flow(".req", dur="2.2s", dash="8 12", shift=-20))
    css.append(anim_tx(".tok", dur="2.2s", x1=0, x2=780))
    s.text(60, 448, "peripheral request → DMA grant → mem write → CNDTR--", size=13, fill=T.MUTED)

    s.rect(40, 470, 820, 70, fill=T.BG2, stroke=T.RED, rx=8)
    s.text(56, 498, "Trap: parse the wrong half after HT/TC; printf inside HT longer than half-buffer time.",
           size=13, fill=T.RED, weight="700")
    s.text(56, 520, "ISR sets a flag; main drains the finished half. Matches sample-10-cndtr-ledger.",
           size=12, fill=T.MUTED)

    css.append("@media (prefers-reduced-motion: reduce){*{animation:none!important}}")
    s.add_style("\n".join(css))
    s.footer(note="自绘矢量动画 · FA-002 · 环形 DMA 半区所有权，非逻辑分析仪截图",
             label="自绘矢量动画 · STM32 知识库")
    return s


ANIMS = [
    ("sample-02-pll-lock-flow.svg", pll_lock_flow),
    ("sample-03-gpio-bsrr-flow.svg", gpio_bsrr_flow),
    ("sample-06-uart-baud-wire.svg", uart_baud_wire),
    ("sample-09-adc-sar-weights.svg", adc_sar_weights),
    ("sample-10-dma-circular-ht.svg", dma_circular_ht),
]


def main() -> None:
    root = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                        "assets", "animations")
    os.makedirs(root, exist_ok=True)
    for name, fn in ANIMS:
        path = os.path.join(root, name)
        fn().save(path)
        audit_anim(name, path)
    print(f"wrote {len(ANIMS)} animations -> {root}")


if __name__ == "__main__":
    main()

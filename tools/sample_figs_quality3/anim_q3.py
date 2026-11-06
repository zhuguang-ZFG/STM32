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
    s = Svg(W, H, "Stop wake restore", "Restore the clock before sending the next UART byte")
    s.add('<metadata>FA-002 · IG-009 · knowledge-track sequence</metadata>')
    s.header(title="Stop 醒来：先恢复时钟，再发送", subtitle="STM32F103 · PPRE2 不分频 · BRR 保持 0x271",
             tag="16", tag_color=T.GREEN)
    s.text(40, 96, "硬件完成唤醒；恢复到 72 MHz 由软件完成。", size=17, fill=T.TEXT, weight="700")
    steps = [
        ("Stop", "HSE / PLL 关", T.CYAN),
        ("EXTI 唤醒", "HSI 8 MHz", T.AMBER),
        ("配置 HSE / PLL", "等待就绪位", T.VIOLET),
        ("切换 SYSCLK", "确认 SWS", T.GREEN),
        ("USART1 TX", "115200 bit/s", T.CYAN),
    ]
    bw, gap, x0, y0, bh = 148, 20, 40, 124, 100
    for i, (t, n, col) in enumerate(steps):
        x = x0 + i * (bw + gap)
        s.rect(x, y0, bw, bh, fill=T.PANEL, stroke=col, rx=8)
        s.text(x + bw / 2, y0 + 34, t, size=15, anchor="middle", fill=col, weight="700")
        s.text(x + bw / 2, y0 + 65, n, size=13, anchor="middle", fill=T.TEXT)
        if i < len(steps) - 1:
            s.arrow(x + bw + 3, y0 + bh / 2, x + bw + gap - 3, y0 + bh / 2, color=T.STROKE, sw=2)
    s.line(114, 250, 786, 250, stroke=T.GRID, sw=2)
    for x in (114, 282, 450, 618, 786):
        s.circle(x, 250, 4, fill=T.STROKE)
    s.circle(114, 250, 7, fill=T.GREEN, cls="restore-dot")
    s.text(40, 290, "位置表示先后顺序，间距不表示实际耗时。", size=12, fill=T.MUTED)
    s.rect(40, 320, 820, 112, fill=T.PANEL, stroke=T.GREEN, rx=8)
    s.text(60, 350, "恢复后：发 0x55，检查 TX 位宽", size=18, fill=T.GREEN, weight="700")
    s.text(60, 381, "72 MHz / 625 = 115200 bit/s", size=18, fill=T.TEXT, mono=True)
    s.text(60, 410, "单个位宽约 8.68 µs；GPIO 标记可区分唤醒与软件恢复。", size=14, fill=T.MUTED)
    s.rect(40, 450, 820, 84, fill=T.BG2, stroke=T.RED, rx=8)
    s.text(60, 480, "若跳过恢复：8 MHz / 625 = 12800 bit/s", size=17, fill=T.RED, weight="700")
    s.text(60, 511, "同一 BRR，位宽变为 78.125 µs；先核对时钟，再检查主机设置。", size=14, fill=T.TEXT)
    s.add_style("""
      @keyframes restore-position {
        0%,12%{transform:translateX(0)} 20%,32%{transform:translateX(168px)}
        40%,52%{transform:translateX(336px)} 60%,72%{transform:translateX(504px)}
        80%,100%{transform:translateX(672px)}
      }
      .restore-dot{animation:restore-position 7s linear infinite}
      @media(prefers-reduced-motion:reduce){.restore-dot{animation:none!important;display:none}}
      @media print{.restore-dot{animation:none!important;display:none}}
    """.rstrip() + "\n")
    s.footer(note="自绘矢量动画 · RM0008 Rev 21 PWR/RCC/USART · 顺序示意，非实测波形",
             label="STM32 知识库")
    return s


def cfsr_flow() -> Svg:
    s = Svg(W, H, "Preserve the fault snapshot, then decode", "BFARVALID gates address use, not the accuracy of the stacked PC")
    s.add('<metadata>FA-002 · IG-008 · knowledge-track branch</metadata>')
    s.header(title="HardFault：先保存，再判读地址", subtitle="STM32F103 · BFARVALID = CFSR bit 15",
             tag="17", tag_color=T.AMBER)
    s.rect(40, 100, 820, 108, fill=T.PANEL, stroke=T.CYAN, rx=8)
    s.text(60, 132, "保存 BFAR / MMFAR，再检查对应 VALID 位", size=19, fill=T.CYAN, weight="700")
    s.text(60, 164, "同时保留 HFSR、CFSR、EXC_RETURN 与异常栈；避免嵌套异常更新现场。", size=15, fill=T.TEXT)
    s.text(60, 191, "HFSR.FORCED = bit 30：进一步解码保存的 CFSR。", size=14, fill=T.MUTED)
    s.line(450, 208, 450, 242, stroke=T.STROKE, sw=2)
    s.line(242, 242, 658, 242, stroke=T.STROKE, sw=2)
    s.arrow(242, 242, 242, 280, color=T.GREEN, sw=2)
    s.arrow(658, 242, 658, 280, color=T.RED, sw=2)
    for x, color, label, line1, line2 in (
        (40, T.GREEN, "bit 15 = 1", "BFAR 地址有效", "继续结合故障类型与指令分析"),
        (460, T.RED, "bit 15 = 0", "弃用 BFAR 地址", "地址看起来合理也不能采用"),
    ):
        s.rect(x, 280, 400, 124, fill=T.PANEL, stroke=color, rx=8)
        s.text(x + 20, 313, label, size=19, fill=color, weight="700", mono=True)
        s.text(x + 20, 347, line1, size=20, fill=T.TEXT, weight="700")
        s.text(x + 20, 381, line2, size=15, fill=T.MUTED)
    s.circle(450, 220, 6, fill=T.GREEN, cls="fault-dot fault-valid")
    s.circle(450, 220, 6, fill=T.RED, cls="fault-dot fault-invalid")
    s.text(40, 437, "IMPRECISERR：PC 可能滞后；STKERR / MSTKERR：栈帧可能不完整。", size=15, fill=T.RED)
    s.text(40, 465, "addr2line 使用同一 ELF 与可信的栈 PC；BFAR 是访问地址。", size=15, fill=T.TEXT)
    s.line(40, 490, 860, 490, stroke=T.GRID, sw=1)
    s.text(40, 520, "另一个实验：DWT Δ = 72，在 72 MHz 下换算为 1 µs。", size=16, fill=T.VIOLET)
    s.text(40, 546, "需同时使能 TRCENA 与 CYCCNTENA；不属于故障地址判读流程。", size=13, fill=T.MUTED)
    s.add_style("""
      @keyframes fault-valid-route {
        0%,16%{transform:translate(0,0)} 24%{transform:translate(0,22px)}
        50%,62%{transform:translate(-208px,22px)} 82%,100%{transform:translate(-208px,48px)}
      }
      @keyframes fault-invalid-route {
        0%,16%{transform:translate(0,0)} 24%{transform:translate(0,22px)}
        50%,62%{transform:translate(208px,22px)} 82%,100%{transform:translate(208px,48px)}
      }
      .fault-valid{animation:fault-valid-route 6s linear infinite;opacity:.8}
      .fault-invalid{animation:fault-invalid-route 6s linear infinite;opacity:.8}
      @media(prefers-reduced-motion:reduce){.fault-dot{animation:none!important;display:none}}
      @media print{.fault-dot{animation:none!important;display:none}}
    """.rstrip() + "\n")
    s.footer(note="自绘矢量动画 · ARM DUI0552A §4.3.10–4.3.15 · 两种有效位结果的分支示意",
             label="STM32 知识库")
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

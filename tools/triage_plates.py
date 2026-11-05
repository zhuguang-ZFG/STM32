#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shared drawings for the six triage plates (ch01, ch06, ch08, ch09, ch10, ch12).

Each plate is imported by the chapter generator that owns the file name:

    tools/sample_figs_b2/ch01_b2.py   sample-01-debug-connect.svg
    tools/sample_figs_b3/ch06_b3.py   sample-06-baud-triage.svg
    tools/sample_figs_b3/ch08_b3.py   sample-08-spi-triage.svg
    tools/sample_figs_b3/ch09_b3.py   sample-09-adc-triage.svg
    tools/sample_figs_b3/ch10_b3.py   sample-10-dma-triage.svg
    tools/sample_figs_b4/ch12_b4.py   sample-12-flash-triage.svg

So `python tools/sample_figs_b3/ch09_b3.py` still writes the real plate; there is
no second writer to overwrite it. This module only draws — the chapter
generators keep their own `_audit()` assertions and FIGURES lists.

The plates were redrawn as pictures, not prose walls: page grids, scope traces,
charging curves, wire routes and register strips carry the facts that used to
sit in 26–35 stacked sentences.

    python tools/sample_figs_b3/ch09_b3.py .temp/out   # regenerate one chapter
"""

from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from svgkit import Svg, T

M = 40  # page margin


# ---------------------------------------------------------------- shared bits


def credit(c: Svg, note: str) -> None:
    c.line(24, c.h - 44, c.w - 24, c.h - 44, stroke=T.GRID, sw=1)
    c.text(24, c.h - 22, note, size=11, fill=T.MUTED)
    c.text(c.w - 24, c.h - 22, "自绘 · 静态 · CC BY 4.0", size=11, fill=T.DIM, anchor="end")


def card(c: Svg, x: float, y: float, w: float, h: float, num: str, title: str,
         color: str, rows, size: float = 13) -> None:
    """One branch card: colour bar, number, bold title, then short rows."""
    c.rect(x, y, w, h, fill=T.PANEL, stroke=T.GRID, rx=8)
    c.rect(x, y, 4, h, fill=color, rx=2)
    c.text(x + 20, y + 27, num, size=15, fill=color, weight="700")
    c.text(x + 46, y + 27, title, size=15, fill=T.TEXT, weight="700")
    yy = y + 52
    for kind, s in rows:
        if kind == "mono":
            c.text(x + 20, yy, s, size=12.5, mono=True, fill=T.MUTED)
        elif kind == "fix":
            c.text(x + 20, yy, s, size=size, fill=T.GREEN)
        elif kind == "bad":
            c.text(x + 20, yy, s, size=size, fill=T.RED)
        else:
            c.text(x + 20, yy, s, size=size, fill=T.TEXT)
        yy += 19


def strip(c: Svg, y: float, items, label: str = "判定顺序",
          color: str = T.VIOLET, w: float = 196) -> None:
    c.text(M, y + 12, label, size=14, weight="700", fill=color)
    x = M + 104
    for i, s in enumerate(items):
        c.chip(x, y - 8, w, 36, s, color=color, size=12.5)
        if i < len(items) - 1:
            c.arrow(x + w + 6, y + 10, x + w + 30, y + 10, color=color, sw=1.5)
        x += w + 36


def bitfield(c: Svg, x: float, y: float, w: float, name: str, bits,
             color: str = T.CYAN, cell: float = 26) -> None:
    c.text(x, y - 6, name, size=11.5, mono=True, fill=T.MUTED)
    cw = w / len(bits)
    for i, b in enumerate(bits):
        c.rect(x + i * cw, y, cw, cell, fill=T.PANEL2, stroke=T.GRID, rx=2)
        c.text(x + i * cw + cw / 2, y + cell * 0.68, b, size=11, mono=True,
               fill=color, anchor="middle")


def scope(c: Svg, x: float, y: float, w: float, h: float, rows, ticks=None) -> None:
    """A small scope screen: one digital trace per row."""
    c.rect(x, y, w, h, fill=T.BG, stroke=T.GRID, rx=2)
    rh = h / len(rows)
    for i, (lab, bits, col) in enumerate(rows):
        yy = y + i * rh
        c.text(x + 8, yy + 13, lab, size=10.5, mono=True, fill=T.MUTED)
        c.waveform(x + 62, yy + 3, w - 76, rh - 12, bits, color=col, sw=1.5)
    if ticks:
        for tx, lab in ticks:
            c.line(x + tx, y, x + tx, y + h, stroke=T.CYAN, sw=1, dash="3 4")
            c.text(x + tx, y - 4, lab, size=10, fill=T.CYAN, anchor="middle")


def arrow_label(c: Svg, x1: float, y1: float, x2: float, y2: float, s: str,
                color: str = T.CYAN) -> None:
    c.arrow(x1, y1, x2, y2, color=color, sw=1.5)
    c.text((x1 + x2) / 2, min(y1, y2) - 6, s, size=11, fill=T.MUTED, anchor="middle")


# ------------------------------------------------------------------ ch12


def flash_triage() -> Svg:
    c = Svg(960, 880,
            "闪存 64 个 1 KB 页：擦不掉先读 CR.LOCK，写不进看半字与 0xFFFF，读不回按 0x08004800 的 46 页逐页比对",
            "STM32F103C8T6 · 1 KB 页 × 64 · RM0008 Rev 21 ch.3")
    c.header(title="闪存三岔口：擦不掉、写不进、读不回", tag="12", tag_color=T.CYAN)

    c.title_block(M, 88, "64 KB = 8 × 8 个格子，不是一根长条")
    gx, gy, cw, ch = M, 104, 50, 34
    for p in range(64):
        col = T.BLUE if p < 16 else (T.AMBER if p < 18 else T.GREEN)
        x, y = gx + (p % 8) * cw, gy + (p // 8) * ch
        c.rect(x, y, cw, ch, fill=T.PANEL, stroke=col, sw=2 if p == 18 else 1, rx=2)
        c.text(x + cw / 2, y + 21, str(p), size=10, mono=True, fill=col,
               anchor="middle")

    ly = 402
    for col, lab, addr in (
        (T.BLUE, "0–15 引导 16 KB", "0x08000000"),
        (T.AMBER, "16–17 参数 2 KB", "0x08004000"),
        (T.GREEN, "18–63 APP 46 KB = 0xB800", "0x08010000 止"),
    ):
        c.rect(M, ly - 10, 12, 12, fill=col, rx=2)
        c.text(M + 20, ly, lab, size=12.5, fill=T.TEXT)
        c.text(M + 250, ly, addr, size=11.5, mono=True, fill=T.MUTED)
        ly += 24
    c.text(M, 478, "第 18 页（粗框）= 0x08004800，APP 从这里起", size=12.5, fill=T.GREEN)

    c.rect(M, 492, 400, 38, fill=T.BG, stroke=T.RED, rx=2, dash="4 4")
    c.text(M + 12, 516, "第 127 页 = 0x0801FC00，不在这 64 KB 里", size=12.5, fill=T.RED)

    x0, w0 = 490, 430
    card(c, x0, 88, w0, 190, "①", "擦除没生效", T.RED, [
        ("mono", "CR.LOCK=0 → KEY1 0x45670123 → KEY2 0xCDEF89AB"),
        ("mono", "CR.PER=1 → CR.STRT=1 → 轮询 SR.BSY"),
        ("say", "钥匙反序：LOCK 恒 1，每条擦除命令都报错"),
        ("say", "地址低 10 位不为 0，或 STRT 撞上 BSY 未落"),
        ("say", "自检：擦一页读回全 0xFFFF，说明擦除本身通了"),
    ])
    card(c, x0, 290, w0, 190, "②", "写不进去", T.AMBER, [
        ("mono", "半字 16 位、偶地址：0x1234 5678 拆两次写"),
        ("mono", "只能 1→0：目标必须先擦成 0xFFFF"),
        ("say", "SR.PGERR：地址为奇 / 目标不是 0xFFFF / CR.PG 没置"),
        ("say", "自检：从 0x08004800 回读 0xB800，坏半字定位到页"),
    ])
    card(c, x0, 492, w0, 190, "③", "读回不对", T.VIOLET, [
        ("mono", "0x08004800 + 0xB800 = 46 页，逐页比对"),
        ("mono", "PM0075 读保护 0xA5 → 整片擦除"),
        ("say", "写得干净但 CRC 不对：先怀疑越界页 0x0801FC00"),
        ("say", "自检：差异落在哪一页，就只重写那一页"),
    ])

    strip(c, 714, ["看 CR.LOCK 与页边界", "看半字与 0xFFFF", "逐页比对 0xB800"],
          w=210)
    credit(c, "自绘。页、半字与钥匙来自 RM0008 Rev 21 第 3 章；读保护来自 PM0075。")
    return c


# ------------------------------------------------------------------ ch10


def dma_triage() -> Svg:
    c = Svg(960, 880,
            "DMA 不动了先读 CNDTR：不减查 EN 与通道映射，写错址查 PSIZE/MSIZE 与 MINC，归零不中断查 TCIF 清除",
            "STM32F103C8T6 · DMA1 7 通道 · RM0008 Rev 21 ch.13")
    c.header(title="DMA 不动了：三个旋钮，一次只拧一个", tag="10", tag_color=T.CYAN)

    c.title_block(M, 88, "一条事务：外设寄存器 → 内存缓冲，CNDTR 数到 0")
    c.box(M, 106, 150, 54, "CPAR", "0x40013804 USART1_DR", size=14)
    arrow_label(c, M + 154, 133, M + 196, 133, "请求")

    bx = M + 200
    c.text(bx, 100, "CMAR 缓冲 · MINC=1 每项 +1", size=11.5, mono=True, fill=T.MUTED)
    for i in range(8):
        x = bx + i * 40
        c.rect(x, 108, 38, 22, fill=T.PANEL, stroke=T.CYAN, sw=1, rx=2)
        c.text(x + 19, 124, f"{i}", size=10, mono=True, fill=T.CYAN, anchor="middle")
        if i:
            c.arrow(x - 2, 119, x - 12, 119, color=T.CYAN, sw=1, head=4)
    c.text(bx + 8 * 40 - 4, 124, "…", size=14, fill=T.MUTED)

    c.box(576, 106, 150, 54, "CNDTR", "0x0080 项（不是字节）", size=14)
    c.arrow(576 + 152, 133, 576 + 196, 133, color=T.GREEN, sw=1.5)
    c.text(760, 118, "0x0080", size=12, mono=True, fill=T.MUTED, anchor="middle")
    c.text(760, 154, "0x0000", size=12, mono=True, fill=T.MUTED, anchor="middle")
    c.line(736, 128, 784, 128, stroke=T.GRID, sw=1)
    c.text(800, 108, "HT", size=11, mono=True, fill=T.AMBER)
    c.text(800, 124, "TC", size=11, mono=True, fill=T.GREEN)
    c.text(824, 108, "0x0040", size=11, mono=True, fill=T.MUTED)
    c.text(824, 124, "0x0000", size=11, mono=True, fill=T.MUTED)

    c.rect(M, 176, 880, 58, fill=T.BG2, stroke=T.GRID, rx=8)
    c.text(M + 14, 198, "顺序固定：CPAR → CMAR → CNDTR → CCR.EN=1", size=13.5, fill=T.TEXT)
    c.text(M + 14, 220, "8-bit × 0x0080 项 = 128 B；16-bit 同值 = 256 B —— CNDTR 数的是数据项", size=12, fill=T.MUTED)

    card(c, M, 250, 880, 96, "①", "CNDTR 不减：事务从未启动", T.RED, [
        ("mono", "CCR.EN（bit 0）= 0 → 三个地址写完就停在那里"),
        ("say", "USART1_RX 硬连 DMA1 通道 5，不是 4 或 6；USART_CR3.DMAR 也要为 1"),
        ("fix", "自检：从调试器把 EN 置 1，看 CNDTR 是否开始减 —— 会减就是请求路径的锅"),
    ])
    card(c, M, 358, 880, 96, "②", "数据错位或全写同址：宽度与自增", T.AMBER, [
        ("mono", "PSIZE[9:8] ≠ MSIZE[11:10] → 截断或补零；MINC（bit 7）= 0 → 每项写同一字"),
        ("say", "USART1_RX 用 PSIZE=MSIZE=00、MINC=1、PINC=0（外设地址固定是正常的）"),
        ("fix", "自检：传 4 项后断点，CMAR 每次应 +4 字节（MSIZE=00），+8 则 MSIZE=01"),
    ])
    card(c, M, 466, 880, 96, "③", "CNDTR 归零但 TC 中断不进：标志与使能", T.VIOLET, [
        ("mono", "旧 TCIF5 还挂着 → 新中断被挡住；写 1 到 CTCIF5（IFCR bit 17）才清"),
        ("say", "TCIE（bit 1）= 0 时 TC、HT、TE 全静默；NVIC 里 DMA1_Channel5 也要开"),
        ("fix", "自检：清零四个标志后再武装，CNDTR 归零那一刻必须进一次 ISR"),
    ])

    strip(c, 592, ["读 CNDTR 有没有减", "看目的缓冲有没有动", "看 TCIF5 有没有清"],
          label="三个旋钮", w=210)
    c.text(M, 664, "底注：F103 只有 DMA1（7 通道）；CNDTR 按配置宽度计数据项，8-bit 通道 0x0080 = 128 字节。",
           size=12, fill=T.MUTED)
    credit(c, "自绘。通道映射与 CR/IFCR 语义来自 RM0008 Rev 21 第 13 章；DMA1 结构来自 DS5319 Rev 20。")
    return c


# ------------------------------------------------------------------ ch06


def baud_triage() -> Svg:
    c = Svg(960, 880,
            "串口乱码先按实际 fCK 重算 BRR，无输出先查交叉与时钟门，丢字节先读 SR 再读 DR",
            "STM32F103C8T6 · USART1 115200 8N1 · PCLK2 72 MHz")
    c.header(title="串口三岔口：乱码、没输出、丢字节", tag="06", tag_color=T.CYAN)

    c.title_block(M, 88, "同一 100 µs 窗口：115200 走完 10 位一帧，12800 还卡在起始位")
    frame = [0, 1, 0, 1, 0, 1, 0, 1, 0, 1]  # 起始位 + 0x55（LSB 先，8 位）+ 停止位 = 10 位
    c.text(M, 116, "期望 115200：8.68 µs/位，10 位一帧", size=12, fill=T.MUTED)
    c.waveform(M + 190, 100, 280, 46, frame, color=T.GREEN, sw=1.5)
    c.text(M + 478, 128, "≈ 87 µs", size=11, mono=True, fill=T.GREEN)

    c.text(M, 176, "实际 12800：78 µs/位（慢 9×）", size=12, fill=T.MUTED)
    # 100 µs 窗口 = 280 px；起始位就要 78 µs ≈ 218 px，帧远没走完
    wx0, wy0, wy1 = M + 190, 160 + 46 * 0.84, 160 + 46 * 0.16
    c.path(f"M {wx0} {wy0} L {wx0 + 218} {wy0} L {wx0 + 218} {wy1} L {wx0 + 280} {wy1}",
           stroke=T.RED, sw=1.5)
    c.text(M + 478, 188, "帧走不完", size=11, fill=T.RED)

    c.line(M + 190, 210, M + 470, 210, stroke=T.GRID, sw=1)
    c.text(M + 190, 226, "0 µs", size=10, mono=True, fill=T.MUTED)
    c.text(M + 470, 226, "100 µs", size=10, mono=True, fill=T.MUTED, anchor="end")

    c.rect(568, 84, 352, 146, fill=T.PANEL, stroke=T.CYAN, rx=8)
    c.text(582, 108, "BRR 是一步除法，不是猜", size=13.5, weight="700", fill=T.TEXT)
    c.code(582, 132, [
        "USARTDIV = 72e6 / (16 × 115200)",
        "         = 39.0625 → 0x271（误差 0%）",
        "HSI 8 MHz 还按 72 MHz 算 → 12,800",
    ], size=12, lh=20, color=T.GREEN)
    c.text(582, 214, "RCC_CFGR SWS[3:2]：00=HSI  01=HSE  10=PLL",
           size=11.5, mono=True, fill=T.AMBER)

    card(c, M, 250, 880, 112, "①", "乱码：分频对不上真正喂进去的时钟", T.RED, [
        ("mono", "HSE 起振失败 → RCC 回落 HSI 8 MHz，代码仍按 72 MHz 算 BRR"),
        ("say", "先读 RCC_CFGR 的 SWS 位确认真实时钟；改 BRR 修不好 9 倍的时钟差"),
        ("fix", "自检：读 RCC_CFGR 的 SWS，确认 PLL 的源是 HSE 还是 HSI；别拿 BRR 掩盖时钟"),
    ])
    card(c, M, 378, 880, 112, "②", "没输出：先量线，再查时钟门", T.AMBER, [
        ("mono", "PA9(30) → 对方 RX；PA10(31) ← 对方 TX；TX 接 TX 看起来对，其实什么都不发"),
        ("say", "USART1 门控 RCC_APB2ENR bit 14（0x40021018）；门关着 BRR 写进去也不生效"),
        ("fix", "自检：把 PA9 与 PA10 短接回环一个字节，先排除 USB-TTL"),
    ])
    card(c, M, 506, 880, 112, "③", "丢字节：ORE 没清，或清的顺序错", T.VIOLET, [
        ("mono", "下一个字来时 RXNE 还没读走 → 移位寄存器被覆盖，ORE 置位"),
        ("say", "清 ORE 必须按顺序：先读 SR(0x00) 再读 DR(0x04)；只读 DR 清不掉，接收停死"),
        ("fix", "自检：连续发 256 字节，末了 SR 的 ORE 位必须还是 0"),
    ])

    strip(c, 648, ["确认真实 fCK", "量线 + 时钟门", "ORE 清对顺序"], w=210)
    c.text(M, 712, "时钟不对时，BRR 只是把错误算得更精确；先读 RCC_CFGR 的 SWS 位。", size=12, fill=T.MUTED)
    credit(c, "自绘。USARTDIV、ORE 清除与 APB 时钟位来自 RM0008 Rev 21 第 27 章；引脚来自 DS5319 Rev 20。")
    return c


# ------------------------------------------------------------------ ch08


def spi_triage() -> Svg:
    c = Svg(960, 880,
            "SPI 读回全 0xFF 查片选与 MISO，没有 SCK 查 SPE/MSTR 与时钟门，只在高 BR 出错就先降速",
            "STM32F103C8T6 · SPI1 on APB2 72 MHz · PA4..PA7 = pin 14..17")
    c.header(title="SPI 三条死路：先看线上回来什么", tag="08", tag_color=T.CYAN)

    panels = [
        ("① 有 SCK，MISO 恒高", [0, 1] * 8, [1] * 16, "返回 0xFF：没人驱动 MISO", T.RED),
        ("② SCK 根本不动", [0] * 16, [1] * 16, "没有时钟：SPE/MSTR 或门控", T.AMBER),
        ("③ 低速对、高速乱", [0, 1] * 8, [0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0],
         "限速：先降到 BR=010", T.VIOLET),
    ]
    for i, (title, sck, miso, note, col) in enumerate(panels):
        x = M + i * 300
        c.text(x, 92, title, size=13, weight="700", fill=col)
        scope(c, x, 102, 280, 112, [("SCK", sck, T.CYAN), ("MISO", miso, T.GREEN)])
        c.text(x, 232, note, size=11.5, fill=col)

    c.rect(M, 250, 880, 62, fill=T.BG2, stroke=T.GRID, rx=8)
    c.text(M + 14, 272, "PA4=CS  PA5=SCK  PA6=MISO  PA7=MOSI（pin 14..17）",
           size=12.5, mono=True, fill=T.TEXT)
    c.text(M + 14, 296, "SPE = CR1 bit 6 · MSTR = CR1 bit 2 · 门控 = RCC_APB2ENR bit 12（关着时 CR1 读回 0x0000）",
           size=12, mono=True, fill=T.MUTED)

    card(c, M, 326, 880, 96, "①", "全 0xFF：片选没低，或者 MISO 悬空", T.RED, [
        ("mono", "PA4 必须从第一个 SCK 沿到最后一个沿都为低；两次命令之间回到高"),
        ("say", "PA4 常高 → 从机 Hi-Z；PA4 常低 → 两条命令并成一帧；0x00 则是线被拉低/CPOL 反"),
        ("fix", "自检：示波器夹在从机端看 PA4 与 PA6，别在主板端猜"),
    ])
    card(c, M, 432, 880, 96, "②", "没有 SCK：主机没启动，或脚不是复用推挽", T.AMBER, [
        ("mono", "SPE 与 MSTR 复位都是 0；MSTR=0 时它当从机，永远等外部时钟"),
        ("say", "PA5 的 CRL 半字节必须是 0xB（复用推挽），配成输入或模拟就没波形"),
        ("fix", "自检：读 CR1，若为 0x0000 且 APB2ENR bit 12 = 0，先开门再谈别的"),
    ])
    card(c, M, 538, 880, 96, "③", "低速对、高速错：先降到 9 MHz 再谈协议", T.VIOLET, [
        ("mono", "BR=000 是 72/2 = 36 MHz；跳线接的 W25Q64 没按这个速率规定"),
        ("say", "BR=010（÷8 = 9 MHz）重跑同一条事务；ID 回 0xEF 0x40 0x17 就说明协议没错"),
        ("fix", "自检：010 → 001（18 MHz）逐级爬，停在第一个读错的档位并退回去"),
    ])

    strip(c, 664, ["片选与 MISO", "SCK 与门控", "最后才降 BR"], w=210)
    credit(c, "自绘。SPE/MSTR 与 BR 分频来自 RM0008 Rev 21 第 25 章；引脚来自 DS5319 Rev 20 表 5。")
    return c


# ------------------------------------------------------------------ ch09


def adc_triage() -> Svg:
    c = Svg(960, 880,
            "ADC 末位抖动查采样时间，顶满或贴零查 VDDA，整体偏置查校准；三岔互不替代",
            "STM32F103C8T6 · PA0 = ADC12_IN0（pin 10）· VDDA = pin 9 · AN2834")
    c.header(title="ADC 读数不对：先看采样窗，再看基准，最后才校准", tag="09", tag_color=T.CYAN)

    # charging curve: 100 kΩ 源，τ = (100 kΩ + 1 kΩ) × 8 pF = 0.808 µs
    ax, ay, aw, ah = 66, 92, 420, 170
    tau, t_end = 0.808, 1.0
    c.axis(ax, ay, aw, ah, ylabel="码值")
    c.text(ax + 6, ay + 14, "4096", size=10, mono=True, fill=T.MUTED)
    c.text(ax + 12, ay + ah - 2, "0", size=10, mono=True, fill=T.MUTED)
    c.line(ax + 4, ay + 20, ax + aw, ay + 20, stroke=T.GRID, sw=1, dash="3 4")
    c.text(ax + aw - 4, ay + 14, "满量程", size=10, fill=T.MUTED, anchor="end")
    for t, lab in ((0.2, "0.2"), (0.4, "0.4"), (0.6, "0.6"), (0.8, "0.8"), (1.0, "1.0 µs")):
        x = ax + aw * t / t_end
        c.line(x, ay + ah, x, ay + ah + 4, stroke=T.STROKE, sw=1)
        c.text(x, ay + ah + 18, lab, size=10, mono=True, fill=T.MUTED, anchor="middle")

    def vy(t: float) -> float:
        return ay + ah - 6 - (1 - math.exp(-t / tau)) * (ah - 30)

    from svgkit import polyline_d
    c.path(polyline_d([(ax + aw * t_end * i / 80, vy(t_end * i / 80)) for i in range(81)]),
           stroke=T.GREEN, sw=2)

    wx = aw * 0.125 / t_end
    c.rect(ax, ay + 4, wx, ah - 4, fill=T.RED, opacity=0.16, rx=2)
    c.circle(ax + wx, vy(0.125), 4, fill=T.RED)
    c.arrow(ax + 150, ay + 150, ax + wx + 8, vy(0.125) + 4, color=T.RED, sw=1.5)
    c.text(ax + 156, ay + 154, "采样窗 125 ns → 只到 14%", size=12, fill=T.RED)
    c.text(ax + aw - 4, ay + 96, "1 µs 也才 71%", size=12, fill=T.GREEN, anchor="end")

    # symptom → root
    sx = 530
    c.title_block(sx, 96, "三种症状，三个不同的根")
    tri = [
        ("末位抖动", "采样电容没充满", T.AMBER),
        ("恒 4095 / 0", "VIN 越界或 VDDA 偏低", T.RED),
        ("整体偏置", "上电没做校准", T.VIOLET),
    ]
    for i, (sym, root, col) in enumerate(tri):
        y = 116 + i * 54
        c.chip(sx, y, 130, 34, sym, color=col, size=12.5)
        c.text(sx + 144, y + 22, root, size=12.5, fill=T.TEXT)

    c.rect(M, 296, 880, 40, fill=T.BG2, stroke=T.GRID, rx=8)
    c.text(M + 14, 321, "code × VDDA / 4096　·　Tconv = SMP + 12.5 周期　·　ADCCLK ≤ 14 MHz（÷6 = 12 MHz）",
           size=12.5, mono=True, fill=T.TEXT)

    card(c, M, 352, 880, 98, "①", "末位抖动：等 RC 充完，不是加平均", T.AMBER, [
        ("mono", "t ≈ (R_AIN + 1 kΩ) × 8 pF × ln(2^14) ≈ (R_AIN + 1 kΩ) × 78 ns"),
        ("say", "100 kΩ 要 7.8 µs；SMP=1.5 cycles 只有 125 ns，差 62 倍 → SMPR2 SMP0 = 111（239.5 周期）"),
        ("fix", "自检：100 kΩ 源各取 100 次读数，比较 1.5 与 239.5 档的均值与极差"),
    ])
    card(c, M, 460, 880, 98, "②", "顶满或贴零：先看 VDDA 与脚的方向", T.RED, [
        ("mono", "4095 是钳位不是读数；VIN > VDDA 会打开输入保护二极管，码值饱和"),
        ("say", "LQFP48 没有独立 VREF+：pin 9 的 VDDA 就是满量程，1% 下垂让所有码偏 1%"),
        ("fix", "自检：转换进行时量 pin 9 到 GND；再用 CH17 Vrefint 反算 VDDA 交叉核对"),
    ])
    card(c, M, 568, 880, 98, "③", "整体偏置：校准顺序错一步就白做", T.VIOLET, [
        ("mono", "ADON=1 → 等 2 ADCCLK → RSTCAL=1 → 轮询 RSTCAL=0 → CAL=1 → 轮询 CAL=0"),
        ("say", "RSTCAL 未清就写 CAL，新校准不生效；校准期间不能有转换在跑"),
        ("fix", "自检：0 V 与半量程各测一次 —— 两处台阶一样是偏置，越往上越大是增益"),
    ])

    strip(c, 692, ["先算采样时间", "再核 VDDA 与脚", "最后才校准"], w=210)
    credit(c, "自绘。采样时间档位与校准流程来自 RM0008 Rev 21 第 11 章；精度实践来自 AN2834。")
    return c


# ------------------------------------------------------------------ ch01


def debug_connect() -> Svg:
    c = Svg(960, 990,
            "ELF 生成却连不上：先查 PA13/PA14 是否被复用成 GPIO，再查供电与共地，最后才动 adapter speed",
            "STM32F103C8T6 LQFP48 · DS5319 Rev 20 表 5 · openocd/bluepill-stlink.cfg")
    c.header(title="连不上 SWD：五根线、三个环、一个单向门", tag="01", tag_color=T.CYAN)

    # probe
    c.rect(M, 92, 150, 196, fill=T.PANEL, stroke=T.STROKE, rx=8)
    c.text(M + 75, 116, "ST-Link", size=14, weight="700", anchor="middle")
    c.text(M + 75, 134, "hla_swd", size=11, mono=True, fill=T.MUTED, anchor="middle")
    wires = [
        ("3V3", T.RED, "只供电，不与板载 3.3 V 并联"),
        ("GND", T.STROKE, "探针地与板地必须是同一个地"),
        ("SWDIO", T.CYAN, "34 / PA13"),
        ("SWCLK", T.CYAN, "37 / PA14"),
        ("NRST", T.AMBER, "7 / 复位，不是 SWD 信号"),
    ]
    for i, (name, col, note) in enumerate(wires):
        y = 156 + i * 26
        c.text(M + 16, y + 4, name, size=11.5, mono=True, fill=col)
        c.line(M + 62, y, 232, y, stroke=col, sw=1.5)
        c.text(238, y + 4, note, size=11.5, fill=T.MUTED)

    # LQFP48 pin map
    px, py, side = 566, 96, 300
    c.rect(px, py, side, side, fill=T.PANEL, stroke=T.STROKE, rx=4)
    c.text(px + side / 2, py + 40, "LQFP48", size=15, weight="700", anchor="middle")
    c.text(px + side / 2, py + 62, "俯视：只标要用的 6 个脚", size=11.5, fill=T.MUTED,
           anchor="middle")
    hot = {7: "NRST", 34: "PA13 SWDIO", 35: "VSS_2", 36: "VDD_2", 37: "PA14 SWCLK", 44: "BOOT0"}
    for p in range(1, 49):
        if p <= 12:
            i = p - 1
            x, y, horiz = px - 22, py + 10 + i * 24, True
        elif p <= 24:
            i = p - 13
            x, y, horiz = px + 10 + i * 24, py + side + 2, False
        elif p <= 36:
            i = p - 25
            x, y, horiz = px + side + 2, py + side - 34 - i * 24, True
        else:
            i = p - 37
            x, y, horiz = px + side - 34 - i * 24, py - 22, False
        col = T.RED if p in hot else T.GRID
        if horiz:
            c.line(x, y + 8, x + 16, y + 8, stroke=col, sw=2 if p in hot else 1)
        else:
            c.line(x + 8, y, x + 8, y + 16, stroke=col, sw=2 if p in hot else 1)
        c.text(x + 8, y + 22 if horiz else y + 30, str(p), size=9.5, mono=True,
               fill=col, anchor="middle")
    c.text(px + 24, py + 150, "红脚 = 必须接对的 6 个", size=11.5, fill=T.RED, weight="700")
    for i, s in enumerate((
        "7  NRST",
        "34 PA13 SWDIO",
        "35 VSS_2 · 36 VDD_2",
        "37 PA14 SWCLK",
        "44 BOOT0",
    )):
        c.text(px + 30, py + 174 + i * 21, s, size=11.5, mono=True, fill=T.TEXT)
    c.text(px + 24, py + 276, "其余 42 脚不标：", size=11, fill=T.DIM)
    c.text(px + 24, py + 294, "别把 35/36 数成 34/37。", size=11, fill=T.DIM)

    # traps
    traps = [
        ("①", "复用：No Debug 是单向门", T.RED,
         "SYS → Debug 选了 No Debug，生成代码把 PA13/PA14 配成推挽输出；",
         "程序一跑调试口就消失，下一次连接失败 —— 改 C 代码关不回来。"),
        ("②", "供电与共地：先量 3V3，再谈别的", T.AMBER,
         "pin 35 VSS_2 与 36 VDD_2 紧挨调试脚，常被数错；探针地必须与板地同地。",
         "本实验室用 Micro-USB 供电，不要再并探针的 3.3 V。"),
        ("③", "接口与 cfg：速率是最后一个旋钮", T.VIOLET,
         "bluepill-stlink.cfg：transport select hla_swd / adapter speed 1000；",
         "launch.json 要加载这份 cfg，别指向旧副本；ST-Link 固件旧会报 DFU 错误。"),
    ]
    for i, (num, title, col, l1, l2) in enumerate(traps):
        y = 434 + i * 88
        c.rect(M, y, 880, 76, fill=T.PANEL, stroke=T.GRID, rx=8)
        c.rect(M, y, 4, 76, fill=col, rx=2)
        c.text(M + 20, y + 26, num, size=15, fill=col, weight="700")
        c.text(M + 46, y + 26, title, size=14, weight="700", fill=T.TEXT)
        c.text(M + 46, y + 48, l1, size=12, fill=T.MUTED)
        c.text(M + 46, y + 66, l2, size=12, fill=T.MUTED)

    c.rect(M, 704, 880, 86, fill=T.BG2, stroke=T.RED, rx=8)
    c.text(M + 14, 728, "救砖：BOOT0 拉高 → 上电 → 接上 → 擦除 → SYS 选 Serial Wire → 烧回 → BOOT0 归零",
           size=13, fill=T.TEXT, weight="700")
    c.text(M + 14, 752, "顺序不能换：先让芯片从系统存储器起来，SWD 才有机会接上；接上之后才谈得到改选项字节。",
           size=12, fill=T.MUTED)
    c.text(M + 14, 774, "别为了连不上就改 -O2 或重写 main —— 编译已经过了，故障在板子和线。",
           size=12, fill=T.MUTED)

    strip(c, 812, ["复用 Debug=Serial Wire", "量 3V3 与共地", "最后才降 adapter speed"],
          label="排查顺序", w=200)
    credit(c, "自绘。脚位来自 DS5319 Rev 20 表 5；速率与 transport 取自 openocd/bluepill-stlink.cfg。")
    return c

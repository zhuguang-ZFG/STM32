#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Static B3 figures for chapter 06: USART triage and IDLE + DMA reception.

No CSS animation and no SMIL.

    python tools/sample_figs_b3/ch06_b3.py assets/diagrams
"""

from __future__ import annotations

import hashlib
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from svgkit import Svg, T

from triage_plates import baud_triage  # shared plate drawing, one source of truth


def _credit(canvas: Svg, note: str) -> None:
    canvas.line(24, canvas.h - 36, canvas.w - 24, canvas.h - 36, stroke=T.GRID, sw=1)
    canvas.text(24, canvas.h - 16, note, size=11, fill=T.MUTED)
    canvas.text(canvas.w - 24, canvas.h - 16, "自绘 · 静态 · CC BY 4.0", size=11, fill=T.DIM, anchor="end")



def idle_dma() -> Svg:
    canvas = Svg(
        960,
        840,
        "IDLE + DMA 收整帧：DMA 搬字节，IDLE 划帧边界，CNDTR 差值给出这一帧的长度",
        "STM32F103C8T6 · chapter 06 · RM0008 Rev 21 ch.27 · ch.13",
    )
    canvas.header(tag="06", tag_color=T.CYAN)
    canvas.text(40, 86, "USART1 + DMA1 Channel 5  buf[256]  CIRC = 1  CNDTR reloads at 256",
                size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "the CPU never reads DR per byte; it wakes once at the frame boundary",
                size=14, fill=T.CYAN)
    canvas.text(40, 138, "DMAR = CR3 bit 6    IDLE = SR bit 4    IDLEIE = CR1 bit 4    DMA1 Ch5 = USART1_RX",
                size=13, fill=T.AMBER, mono=True)

    canvas.text(40, 170, "数据通路  线 → DMA → 环形缓冲", size=16, fill=T.GREEN, weight="700")
    canvas.rect(40, 184, 880, 226, fill=T.PANEL, stroke=T.GREEN, rx=8)
    canvas.box(56, 204, 170, 52, label="RX PA10", sub="pin 31", size=14)
    canvas.box(252, 204, 190, 52, label="USART1_DR", sub="0x40013804", size=14)
    canvas.box(468, 204, 190, 52, label="DMA1 Ch5", sub="USART1_RX", size=14)
    canvas.box(684, 204, 222, 52, label="ring buffer", sub="buf[256], CIRC=1", size=14,
               stroke=T.GREEN, color=T.TEXT)
    canvas.arrow(226, 230, 252, 230, color=T.GREEN)
    canvas.arrow(442, 230, 468, 230, color=T.GREEN)
    canvas.arrow(658, 230, 684, 230, color=T.GREEN)
    canvas.box(684, 314, 222, 52, label="IDLE frame", sub="line high ≈ 86.8 µs", size=14)
    canvas.box(468, 314, 190, 52, label="IDLE IRQ", sub="IDLEIE = 1", size=14)
    canvas.box(252, 314, 190, 52, label="length + parse", sub="len = pos − CNDTR", size=14,
               stroke=T.CYAN, color=T.TEXT)
    canvas.arrow(684, 340, 658, 340, color=T.CYAN)
    canvas.arrow(468, 340, 442, 340, color=T.CYAN)
    canvas.arrow(795, 256, 795, 314, color=T.CYAN)
    canvas.text(805, 290, "frame edge", size=11, fill=T.MUTED)
    canvas.text(56, 396, "DMAR = 1 makes RXNE raise a DMA request; CNDTR counts down from 256, so the ring never stalls",
                size=13, fill=T.MUTED)

    canvas.text(40, 442, "空闲判定  一帧的高电平才算 IDLE", size=16, fill=T.CYAN, weight="700")
    canvas.rect(40, 456, 880, 140, fill=T.PANEL, stroke=T.CYAN, rx=8)
    canvas.text(56, 484, "an idle character is a whole frame of 1s:", size=13, fill=T.TEXT)
    canvas.text(56, 506, "10 bits at 115200 8N1 = 86.8 µs", size=13, fill=T.AMBER, mono=True)
    bits = [0, 1, 0, 1, 1, 0, 0, 1, 1, 1] + [1] * 8
    wx, wy, ww, wh = 56, 514, 420, 36
    canvas.waveform(wx, wy, ww, wh, bits, color=T.GREEN, sw=2)
    marker = wx + ww * 10 / len(bits)
    canvas.line(marker, wy, marker, wy + wh, stroke=T.MUTED, sw=1, dash="4 4")
    canvas.text(56, 566, "stop bit → 10 bit-times of high → IDLE", size=13, fill=T.MUTED)
    canvas.text(520, 486, "one interrupt per frame", size=14, fill=T.TEXT, weight="700")
    canvas.text(520, 512, "IDLE is set after one full frame of 1s; no byte moves",
                size=13, fill=T.TEXT)
    canvas.text(520, 538, "IDLEIE in CR1 turns that flag into an interrupt",
                size=13, fill=T.TEXT)
    canvas.text(520, 564, "read SR then DR in the ISR; the same pair clears ORE",
                size=13, fill=T.TEXT)
    canvas.text(520, 588, "the line is quiet — that is not the peer's packet end",
                size=12, fill=T.MUTED)

    canvas.text(40, 622, "对比  轮询逐字节 vs IDLE+DMA 整帧", size=16, fill=T.VIOLET, weight="700")
    canvas.rect(40, 636, 880, 150, fill=T.PANEL, stroke=T.VIOLET, rx=8)
    canvas.text(56, 668, "轮询 polling", size=14, fill=T.RED, weight="700")
    canvas.rect(250, 650, 650, 26, fill=T.BG2, stroke=T.STROKE, rx=4)
    cell_w, gap, n = 57.4, 8.0, 10
    step = (646 - cell_w) / (n - 1)
    for i in range(n):
        canvas.rect(252 + i * step, 651, cell_w, 24, fill=T.AMBER, rx=2)
    canvas.text(250, 700, "10 bytes = 10 SR reads + 10 DR reads; the CPU owns the port for the whole frame",
                size=13, fill=T.TEXT)
    canvas.text(56, 740, "IDLE + DMA", size=14, fill=T.GREEN, weight="700")
    canvas.rect(250, 722, 650, 26, fill=T.PANEL2, stroke=T.STROKE, rx=4)
    canvas.rect(840, 723, 58, 24, fill=T.GREEN, rx=2)
    canvas.text(869, 740, "IRQ", size=11, fill=T.BG, anchor="middle", weight="700")
    canvas.text(260, 739, "DMA moves all 10 bytes; the CPU sleeps until the frame ends",
                size=12, fill=T.MUTED)
    canvas.text(250, 772, "one interrupt at the frame edge; CNDTR delta gives the length, nothing per byte",
                size=13, fill=T.TEXT)
    _credit(canvas, "自绘。IDLE 检测与 DMA1 通道 5 映射来自 RM0008 Rev 21 第 27、13 章。")
    return canvas


FIGURES = [
    ("sample-06-baud-triage.svg", baud_triage),
    ("sample-06-idle-dma.svg", idle_dma),
]

T_COLORS = {
    value
    for name in dir(T)
    if name.isupper() and isinstance(value := getattr(T, name), str) and value.startswith("#")
}
TEXT_RE = re.compile(r"<text\b[^>]*>(.*?)</text>", flags=re.DOTALL)


def _audit(name: str, path: str) -> str:
    raw = open(path, "rb").read()
    text = raw.decode("utf-8")
    width, height = (int(part) for part in re.search(r'\bwidth="(\d+)" height="(\d+)"', text).groups())
    strokes = set(re.findall(r'stroke-width="([^"]+)"', text))
    radii = set(re.findall(r'\brx="([^"]+)"', text))
    colors = {item.lower() for item in re.findall(r"#(?:[0-9A-Fa-f]{6})(?![0-9A-Fa-f])", text)}
    digest = hashlib.sha256("\n".join(TEXT_RE.findall(text)).encode("utf-8")).hexdigest()

    assert width == 960, (name, "width", width)
    assert strokes <= {"1", "1.5", "2"}, (name, "stroke-width", sorted(strokes))
    assert radii <= {"2", "4", "8"}, (name, "rx", sorted(radii))
    assert colors <= T_COLORS, (name, "colors", sorted(colors - T_COLORS))
    assert "自绘" in text, (name, "credit")
    for banned in ("<animate", "@keyframes", "animation:", "矢量动画"):
        assert banned not in text, (name, "animation", banned)
    assert len(raw) < 60 * 1024, (name, "bytes", len(raw))
    print(f"{name}  {width}x{height}  {len(raw)} bytes  text_hash={digest}")
    return digest


def main(argv: list[str] | None = None) -> None:
    args = sys.argv[1:] if argv is None else argv
    out_dir = args[0] if args else os.path.join("assets", "diagrams")
    os.makedirs(out_dir, exist_ok=True)
    for name, make in FIGURES:
        path = make().save(os.path.join(out_dir, name))
        _audit(name, path)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Static B3 figure for chapter 10: DMA triage.

No CSS animation and no SMIL.

    python tools/sample_figs_b3/ch10_b3.py assets/diagrams
"""

from __future__ import annotations

import hashlib
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from svgkit import Svg, T


def _credit(canvas: Svg, note: str) -> None:
    canvas.line(24, canvas.h - 36, canvas.w - 24, canvas.h - 36, stroke=T.GRID, sw=1)
    canvas.text(24, canvas.h - 16, note, size=11, fill=T.MUTED)
    canvas.text(canvas.w - 24, canvas.h - 16, "自绘 · 静态 · CC BY 4.0", size=11, fill=T.DIM, anchor="end")


def dma_triage() -> Svg:
    canvas = Svg(
        960,
        880,
        "DMA 传输不动了：CNDTR 不减、数据错位、TC 中断不进，三个岔口一次只改一个寄存器",
        "STM32F103C8T6 · chapter 10 · DMA1 7 channels",
    )
    canvas.header(tag="10", tag_color=T.CYAN)
    canvas.text(40, 86, "DMA 传输不动了：先读 CNDTR，再看目的缓冲区，最后看中断标志",
                size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "three branches, one register field each: EN / PSIZE-MSIZE-MINC / TCIE-IFCR",
                size=14, fill=T.CYAN)
    canvas.text(40, 138,
                "DMA1_Channel5 (USART1_RX)  CPAR=0x40013804  CMAR=0x20000100  CNDTR=0x0080 at t0",
                size=13, fill=T.AMBER, mono=True)

    canvas.text(40, 170, "岔口一  CNDTR 不减：事务从未启动", size=16, fill=T.RED, weight="700")
    canvas.text(920, 170, "CCR.EN", size=11, fill=T.MUTED, anchor="end", mono=True)
    canvas.rect(40, 184, 880, 178, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(56, 214, "symptom: CNDTR still reads 0x0080, no byte reached the buffer, and TCIF5 is 0",
                size=14, fill=T.TEXT)
    canvas.text(56, 240, "cause A: CCR.EN = 0 (bit 0): CPAR, CMAR and CNDTR were written, then the channel was never enabled",
                size=14, fill=T.TEXT)
    canvas.text(56, 266, "cause B: the peripheral request never arrives: USART1_RX is hard-wired to DMA1 channel 5, not 4 or 6",
                size=14, fill=T.TEXT)
    canvas.text(56, 292, "cause B check: USART_CR3.DMAR = 1, and RXNE sets on every received byte; no RXNE, no request",
                size=14, fill=T.TEXT)
    canvas.text(56, 318, "checkpoint: order matters — CPAR, CMAR, CNDTR, then CCR, and EN = 1 last",
                size=14, fill=T.TEXT)
    canvas.text(56, 344, "probe: set EN from the debugger and watch CNDTR fall; if it falls, the request path was the fault",
                size=14, fill=T.MUTED)

    canvas.text(40, 396, "岔口二  数据错位或全写同一地址：宽度与自增", size=16, fill=T.AMBER, weight="700")
    canvas.text(920, 396, "CCR.PSIZE · CCR.MSIZE · CCR.MINC", size=11, fill=T.MUTED, anchor="end", mono=True)
    canvas.rect(40, 410, 880, 178, fill=T.PANEL, stroke=T.AMBER, rx=8)
    canvas.text(56, 440, "symptom: bytes arrive shifted by one, or every item overwrites CMAR[0] while CNDTR counts down",
                size=14, fill=T.TEXT)
    canvas.text(56, 466, "cause A: PSIZE[1:0] (CCR 9:8) and MSIZE[1:0] (CCR 11:10) disagree: items are truncated or padded",
                size=14, fill=T.TEXT)
    canvas.text(56, 492, "cause B: MINC = 0 (CCR bit 7): the memory address never increments, so each item writes the same word",
                size=14, fill=T.TEXT)
    canvas.text(56, 518, "not a bug: PINC = 0 (CCR bit 6) on a fixed data register such as USART_DR is the normal setting",
                size=14, fill=T.TEXT)
    canvas.text(56, 544, "checkpoint: for 8-bit USART1_RX set PSIZE = MSIZE = 00, MINC = 1, PINC = 0; CMAR 32-bit aligned",
                size=14, fill=T.TEXT)
    canvas.text(56, 570, "probe: break after 4 items; CMAR must grow by 4 bytes at MSIZE = 00 and by 8 at MSIZE = 01",
                size=14, fill=T.MUTED)

    canvas.text(40, 622, "岔口三  CNDTR 归零但 TC 中断不进：标志与使能", size=16, fill=T.VIOLET, weight="700")
    canvas.text(920, 622, "CCR.TCIE · IFCR.CTCIF5", size=11, fill=T.MUTED, anchor="end", mono=True)
    canvas.rect(40, 636, 880, 152, fill=T.PANEL, stroke=T.VIOLET, rx=8)
    canvas.text(56, 666, "symptom: CNDTR reaches 0 and TCIF5 sets, but the ISR never runs",
                size=14, fill=T.TEXT)
    canvas.text(56, 692, "cause A: TCIF5 was already 1 from an earlier run — a set flag blocks a new interrupt until cleared",
                size=14, fill=T.TEXT)
    canvas.text(56, 718, "fix A: write 1 to CTCIF5 (DMA_IFCR bit 17 for channel 5); writing 0 leaves the flag set",
                size=14, fill=T.TEXT)
    canvas.text(56, 744, "cause B: TCIE = 0 (CCR bit 1); TEIE and HTIE also silent, so error and half-transfer never surface",
                size=14, fill=T.TEXT)
    canvas.text(56, 770, "checkpoint: enable the DMA1_Channel5 IRQ in NVIC, then clear all four flags before re-arming",
                size=14, fill=T.MUTED)

    canvas.rect(40, 800, 880, 32, fill=T.BG2, stroke=T.GREEN, rx=8)
    canvas.text(56, 821, "底注  F103 仅 DMA1（7 通道）；CNDTR 计配置宽度的数据项数，不是字节：8-bit × 0x0080 = 128 B，16-bit 同值 = 256 B。",
                size=12, fill=T.TEXT)

    _credit(canvas, "自绘。通道映射与 CR/IFCR 语义来自 RM0008 Rev 21 第 13 章；DMA1 结构来自 DS5319 Rev 20 第 2.3.13 节。")
    return canvas


FIGURES = [
    ("sample-10-dma-triage.svg", dma_triage),
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
    assert height == 880, (name, "height", height)
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

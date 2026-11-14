# -*- coding: utf-8 -*-
"""DMA selection and counting plate (ch14).

Facts pinned to the chapter: F407 has DMA1 0x40026000 / DMA2 0x40026400,
8 streams each, stream 5 at +0x88; CHSEL is SxCR[27:25]. F103 has DMA1
0x40020000 and fixed channels: USART1_RX=CH5, USART1_TX=CH4. The F407
USART1_RX Stream5/CH4 mapping is the chapter's "common, pending review"
value. NDTR counts items: 64 halfwords with NDTR=3 means 61 items = 122 B.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hd import *  # noqa: E402,F401,F403


def _box(f, x, y, w, h, title, sub, color, size=17):
    f.rect(x, y, w, h, color=color, fill=WHITE, sw=2.2)
    f.text(x + 10, y + size + 6, title, size=size, color=color,
           weight="bold")
    if sub:
        f.text(x + 10, y + size + 26, sub, size=13, color=MUTED)


def _row(f, y, first, boxes, note):
    x = 64
    _box(f, x, y, 170, 58, first[0], first[1], first[2], size=16)
    x += 186
    for title, sub, c in boxes:
        f.arrow(x - 16, y + 29, x - 2, y + 29, color=INK, sw=1.9, bend=0.0)
        _box(f, x, y, 180, 58, title, sub, c, size=16)
        x += 196
    f.htext(850, y + 22, note[0], size=15, color=note[2], weight="bold")
    f.text(850, y + 44, note[1], size=13, color=MUTED)


def dma_paths():
    f = Fig("arch-dma-paths", "DMA：两级选路，两个地址，一个长度")

    # top: same USART1, two families
    tx, ty, tw, th = 48, 120, 1056, 188
    f.rect(tx, ty, tw, th, color=BLUE_D, fill=WHITE, sw=2.6)
    f.htext(tx + 16, ty + 30, "同一个 USART1，两套选路", size=21,
            color=BLUE_D, weight="bold")
    _row(f, ty + 48,
         ("USART1", "APB2", BLUE_D),
         [("DMA2", "0x40026400", BLUE_D),
          ("Stream5", "+0x88", BLUE_D),
          ("CHSEL=4", "SxCR[27:25]", BLUE_D)],
         ("常用映射", "流/通道待复核", RED))
    _row(f, ty + 118,
         ("USART1", "APB2", GREEN_D),
         [("DMA1", "0x40020000", GREEN_D),
          ("CH5 / CH4", "RX / TX", GREEN_D),
          ("无 CHSEL", "通道即槽位", GREEN_D)],
         ("固定绑定", "C8 只有 DMA1", GREEN_D))

    # middle: PAR / M0AR / NDTR
    mx, my, mw, mh = 48, 330, 1056, 190
    f.rect(mx, my, mw, mh, color=AMBER_STROKE, fill=WHITE, sw=2.6)
    f.htext(mx + 16, my + 30, "两个地址，一个长度", size=21,
            color=AMBER_STROKE, weight="bold")
    cards = [
        ("PAR / CPAR", ["外设地址：固定", "PINC = 0"], BLUE_D),
        ("M0AR / CMAR", ["内存地址：递增", "MINC = 1"], GREEN_D),
        ("NDTR / CNDTR", ["剩余项数：每项减 1", "CIRC=1 到 0 回装"], RED),
    ]
    x = 64
    for title, lines, c in cards:
        f.rect(x, my + 50, 300, 82, color=c, fill=WHITE, sw=2.2)
        f.text(x + 12, my + 76, title, size=18, color=c, weight="bold")
        for i, ln in enumerate(lines):
            f.text(x + 12, my + 98 + i * 20, ln, size=13, color=INK)
        x += 328
    f.text(64, my + 158,
           "EN=0 才能改 CHSEL/CIRC/MINC/PSIZE；EN=1 时写入不生效，硬件也不会替你停流。",
           size=14, color=RED)

    # bottom: NDTR counts items, not bytes
    bx, by, bw, bh = 48, 540, 1056, 154
    f.rect(bx, by, bw, bh, color=RED, fill=WHITE, sw=2.6)
    f.htext(bx + 16, by + 30, "NDTR 数项，不数字节", size=21, color=RED,
            weight="bold")
    f.text(64, by + 64, "ADC：64 个半字缓冲，NDTR = 3：", size=15, color=INK)
    f.text(64, by + 90, "已搬 64 − 3 = 61 项 = 122 字节", size=17, color=RED,
           weight="bold")
    f.text(64, by + 120, "把 NDTR 当字节，后半段就从奇数地址开始切。", size=14,
           color=MUTED)
    f.text(610, by + 64, "UART：64 字节环，半满 32 字节", size=15, color=INK)
    f.text(610, by + 90, "32 × 10 / 115200 ≈ 2.78 ms", size=17,
           color=GREEN_D, weight="bold")
    f.text(610, by + 120, "8N1、8 位环；不是上面的半字 ADC 例。", size=14,
           color=MUTED)

    f.htext(576, 736, "CIRC=1 时，NDTR 到 0 回装；环形位置不是累计进度。",
            size=19, color=AMBER_STROKE, anchor="middle", weight="bold",
            hl=True, hl_fill=AMBER_FILL)
    return f


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[2] / "assets" / "illustrations" / "handraw"
    save(dma_paths(), str(out / "arch-dma-paths.svg"))
    print("wrote arch-dma-paths.svg")

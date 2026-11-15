# -*- coding: utf-8 -*-
"""DMA deadline plate (ch14): double buffering swaps blocks, not deadlines.

Facts pinned to the chapter: F407 DBM is SxCR bit18, CT is bit19 and selects
M0AR/M1AR; ADC at 1 Msps with 64 halfword blocks gives a 64 us refill deadline;
UART 115200 8N1 with a 32 B half-buffer gives 32*10/115200 ~= 2.78 ms; F103 has
no DBM and can only emulate ping-pong with HT/TC half ownership; CCM starts at
0x1000_0000 and is unreachable by DMA.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hd import *  # noqa: E402,F401,F403


def dma_deadline():
    f = Fig("arch-dma-deadline", "双缓冲换的是块，不是期限")

    f.rect(48, 118, 1056, 186, color=BLUE_D, fill=WHITE, sw=2.6)
    f.htext(64, 150, "F407：DBM=1，两块轮换", size=22,
            color=BLUE_D, weight="bold")
    cards = [
        (70, "M0AR / 64 B", "CT=0 时 DMA 写块 0", BLUE_D),
        (430, "CT（bit19）", "0 选 M0AR；1 选 M1AR", AMBER_STROKE),
        (770, "M1AR / 64 B", "CT=1 时 DMA 写块 1", GREEN_D),
    ]
    for x, title, sub, c in cards:
        f.rect(x, 180, 300, 82, color=c, fill=PAPER, sw=2.2)
        f.text(x + 12, 210, title, size=19, color=c, weight="bold")
        f.text(x + 12, 240, sub, size=15, color=MUTED)
    f.text(64, 288,
           "SxCR bit18 DBM=1；每块填满触发一次 TC，CPU 处理 CT 指向之外的那一块。",
           size=16, color=INK)

    f.rect(48, 326, 520, 210, color=RED, fill=WHITE, sw=2.6)
    f.htext(64, 358, "ADC：64 µs 的硬期限", size=22, color=RED, weight="bold")
    f.text(64, 392, "1 Msps × 64 个半字 = 64 µs", size=19, color=RED,
           weight="bold")
    f.text(64, 424, "处理函数超过 64 µs，下一次 TC 就把上一块整块覆盖。",
           size=16, color=INK)
    f.text(64, 454, "这是按输入速率算的期限，不是某块板的实测值。", size=16,
           color=MUTED)
    f.htext(64, 504, "块是缓冲单位，期限由源端速率决定", size=17,
            color=AMBER_STROKE, weight="bold")

    f.rect(584, 326, 520, 210, color=GREEN_D, fill=WHITE, sw=2.6)
    f.htext(600, 358, "UART：2.78 ms 的预算", size=22, color=GREEN_D,
            weight="bold")
    f.text(600, 392, "115200 8N1，半满交出 32 B：", size=16, color=INK)
    f.text(600, 422, "32 × 10 / 115200 ≈ 2.78 ms", size=19, color=GREEN_D,
           weight="bold")
    f.text(600, 454, "这是 HT→TC 的预算，不是整帧预算。", size=16, color=INK)
    f.text(600, 484, "两个例子的单位不同，不能互抄。", size=15, color=MUTED)

    f.rect(48, 552, 1056, 150, color=AMBER_STROKE, fill=WHITE, sw=2.6)
    f.htext(64, 584, "F103 没有 DBM：半区所有权只是模拟", size=21,
            color=AMBER_STROKE, weight="bold")
    f.text(64, 618,
           "HT 交前半区、TC 交后半区；DMA 不会在边界停，慢一拍就写进你正在读的半区。",
           size=16, color=INK)
    f.text(64, 648,
           "CCM 在 0x1000_0000；DMA 无路可达，缓冲必须放在主 SRAM。",
           size=16, color=RED)
    f.text(64, 678,
           "EN=0 才能改 CHSEL/CIRC/MINC；改参数先关流，等 EN 读回 0。",
           size=15, color=MUTED)

    f.htext(576, 736, "双缓冲换的是块，不是期限。", size=22,
            color=AMBER_STROKE, anchor="middle", weight="bold", hl=True,
            hl_fill=AMBER_FILL)
    return f


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[2] / "assets" / "illustrations" / "handraw"
    save(dma_deadline(), str(out / "arch-dma-deadline.svg"))
    print("wrote arch-dma-deadline.svg")

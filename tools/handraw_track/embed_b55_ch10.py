# -*- coding: utf-8 -*-
"""B55: embed the two ch10 knowledge-track plates (bottom-up)."""
from embed import embed_after_text

SPECS = [
    # 2. ch10-two-level-bind — §1 anchor paragraph, before the F1/F4 table
    ("docs/10-DMA.md",
     "F1 一个外设请求固定绑到某条 DMA 通道；F4 先把请求绑到「流」，再用 `CHSEL` 选通道，灵活性更高。",
     "ch10-two-level-bind.png",
     "Handraw：一层与两层的请求绑定（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。看哪里：左边 F1 只有一层——USART1_RX 的请求线焊在通道 5 上，配到通道 4 就永远等不到；右边 F4 有两层——请求先进 CHSEL（USART1_RX 是 CH4），Stream 由软件在 SxCR 里选，同一请求落在 DMA2 Stream 5，TX 落在 Stream 7、同样 CH4；证明什么：F1 选通道，F4 先定 Stream 再由 CHSEL 定 Channel；不能证明什么：不涉及 FIFO、突发与优先级仲裁，也不保证某块板的流号，仍要查 RM0090 表 42/43。出处：本章正文与 [RM0090](#source-rm0090)。"),
    ("docs/en/10-dma.md",
     "On F1, a peripheral request is fixed to one DMA channel. On F4, you first bind the request to a stream, then pick the channel with `CHSEL`. That is more flexible.",
     "ch10-two-level-bind.png",
     "Handraw: one-level vs two-level request binding (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). Where to look: on the left F1 has one level — the USART1_RX request is soldered to channel 5, and a config on channel 4 waits forever; on the right F4 has two — the request goes into CHSEL (CH4 for USART1_RX), the stream is chosen in software through SxCR, so RX lands on DMA2 Stream 5 and TX on Stream 7, also CH4; Proves F1 picks a channel while F4 settles the stream first and lets CHSEL pick the channel; Cannot cover FIFO, burst, or priority arbitration, or guarantee a stream number on a given board; those come from RM0090 Table 42/43. See [RM0090](#source-rm0090)."),

    # 1. ch10-goal-evidence — last learning goal, before "## 核心原理 / ## Core ideas"
    ("docs/10-DMA.md",
     "- [ ] 理解 DMA 与 CPU 的总线争抢，以及 H7/F7 的 Cache 一致性问题。",
     "ch10-goal-evidence.png",
     "Handraw：学习目标的五个落点（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。看哪里：五级梯子对应五条学习目标，每级只挂一个能指认的东西——映射表的一行、USART1_TX=通道 4 与 USART1_RX=通道 5、DIR/CIRC 两个位、HT 在第 4 个采样（8 字节）而 TC 在 N、AHB 主设备与 F1 没有 D-Cache；证明什么：目标要落成编号、位或读数，「代码能跑」不算；不能证明什么：这张卡不是映射表，也不含任何板上测量。出处是本章正文与 [RM0008 Rev 21 第 13 章](#source-rm0008-dma)。"),
    ("docs/en/10-dma.md",
     "- [ ] Understand bus contention between DMA and the CPU, and the cache-coherency problem on H7 and F7.",
     "ch10-goal-evidence.png",
     "Handraw: five evidence rungs for the learning goals (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). Where to look: five rungs, one per learning goal, each carrying the one thing you can point at — a row of the map, USART1_TX = channel 4 and USART1_RX = channel 5, the DIR and CIRC bits, HT at sample 4 (8 bytes) against TC at N, the AHB master and no D-Cache on F1; Proves a goal has to land on a number, a bit, or a reading — code that runs is not evidence; Cannot stand in for the map table or prove any board measurement. See [RM0008 Rev 21 ch.13](#source-rm0008-dma)."),
]

if __name__ == "__main__":
    bad = 0
    for spec in SPECS:
        if not embed_after_text(*spec):
            bad += 1
    if bad:
        raise SystemExit(f"{bad} embed(s) failed")

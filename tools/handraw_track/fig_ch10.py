# -*- coding: utf-8 -*-
"""ch10 knowledge-track figure (facts from docs/10, RM0008 Rev 21 ch.13).

The C8 is medium-density: one DMA1 with 7 channels, no DMA2. The three
requests this chapter uses: ADC1 -> channel 1, USART1_TX -> channel 4,
USART1_RX -> channel 5. F4 numbers are DMA2 Stream 5 / Channel 4 for
USART1_RX; ported onto a C8 the writes raise no error but CNDTR never moves.
"""
from hd import *


def channel_map():
    f = Fig("ch10-channel-map",
            "C8 只有一条 DMA1：先把请求对上通道号 / one DMA1, match the request first")

    # ---- 左：DMA1 七条通道 ----
    f.rect(84, 150, 480, 412, color=BLUE_D, fill=WHITE, sw=2.6)
    f.text(324, 182, "STM32F103C8 的 DMA1（中密度）", size=22, color=BLUE_D,
           anchor="middle", weight="bold")
    chans = [("通道 1", "ADC1", GREEN_D),
             ("通道 2", "", MUTED),
             ("通道 3", "", MUTED),
             ("通道 4", "USART1_TX", BLUE_D),
             ("通道 5", "USART1_RX", BLUE_D),
             ("通道 6", "", MUTED),
             ("通道 7", "", MUTED)]
    y = 198
    for name, peri, color in chans:
        used = bool(peri)
        f.rect(140, y, 130, 40, color=color, fill=WHITE if used else GRAY_FILL,
               sw=2.2 if used else 1.6)
        f.text(205, y + 27, name, size=18, color=color if used else MUTED,
               anchor="middle", weight="bold" if used else "normal")
        if used:
            f.text(300, y + 27, "← " + peri, size=18, color=color,
                   weight="bold")
        else:
            f.text(300, y + 27, "（空着）", size=16, color=MUTED)
        y += 46
    f.text(140, 546, "没有 DMA2 —— 「DMA2（5 通道）」那一行属于大容量型号", size=17,
           color=RED, weight="bold")

    # ---- 右：F4 编号搬过来的下场 ----
    f.rect(620, 150, 472, 190, color=RED, fill=WHITE, sw=2.4)
    f.text(636, 180, "把 F4 例程的编号照搬过来", size=21, color=RED,
           weight="bold")
    f.multi(636, 212, ["F4：USART1_RX 走 DMA2 Stream 5 / Ch 4",
                       "C8 写进去不报错，但 CNDTR 一动不动",
                       "——C8 根本没有 DMA2 这台 DMA"],
            size=18, color=INK, lh=28)
    f.rect(620, 364, 472, 190, color=GREEN_D, fill=WHITE, sw=2.4)
    f.text(636, 394, "配置完先问一句：CNDTR 动了吗", size=21, color=GREEN_D,
           weight="bold")
    f.multi(636, 426, ["配置不报错 ≠ 在搬运",
                       "断点看 CNDTR：在读回值上做减法",
                       "数组纹丝不动时，先查通道映射、方向、使能"],
            size=18, color=INK, lh=28)

    # ---- 下：本章三条请求 ----
    reqs = [("ADC1", "通道 1", GREEN_D, "存储器到存储器的实验也抢这条通道"),
            ("USART1_TX", "通道 4", BLUE_D, "第 30 脚 PA9 出去"),
            ("USART1_RX", "通道 5", BLUE_D, "不是 DMA2 Stream 5")]
    x = 84
    for peri, ch, color, note in reqs:
        f.rect(x, 584, 340, 74, color=color, fill=WHITE, sw=2.2)
        f.text(x + 16, 610, f"{peri} → DMA1 {ch}", size=19, color=color,
               weight="bold")
        f.text(x + 16, 638, note, size=15, color=MUTED)
        x += 348

    f.htext(84, 712, "F1 记通道号，F4 记 Stream 号——两套编号不能互相抄", size=23,
            color=INK, weight="bold", hl=True)
    return f


FIGS = {
    "ch10-channel-map": channel_map,
}

if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        f = FIGS[n]()
        OUT.mkdir(parents=True, exist_ok=True)
        save(f, str(OUT / (n + ".svg")))
        print("wrote", OUT / (n + ".svg"))

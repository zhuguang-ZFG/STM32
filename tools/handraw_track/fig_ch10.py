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
    f.text(140, 546, "没有 DMA2——「5 通道」那行是大容量型号", size=17,
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


def request_beat():
    """One transfer beat: request -> arbitrate -> move one item -> count down."""
    f = Fig("ch10-request-beat",
            "一拍搬运：请求来了才动 / one request, one item")

    f.text(84, 132, "DMA 平时不动：外设每就绪一次，它才走一拍——请求、仲裁、搬运、记账",
           size=21, color=MUTED)

    beats = [
        (84, 216, GREEN_D, "① 外设就绪",
         ["USART1_RX 收到 1 字节", "RXNE 置 1", "CR3.DMAR=1 才放行"]),
        (324, 216, BLUE_D, "② 请求上硬连线",
         ["USART1_RX → DMA1 通道 5", "不是 4 也不是 6", "配错就永远等不到"]),
        (564, 216, AMBER_STROKE, "③ 仲裁",
         ["多通道同时请求时", "通道间固定优先级", "+ 软件优先级"]),
        (804, 260, RED, "④ 搬一拍",
         ["读一次 CPAR", "写一次 CMAR", "CNDTR 减 1"]),
    ]
    for x, w, col, title, lines in beats:
        f.rect(x, 156, w, 140, color=col, fill=WHITE, sw=2.4)
        f.text(x + 14, 186, title, size=20, color=col, weight="bold")
        f.multi(x + 14, 214, lines, size=15, color=INK, lh=25)
    f.arrow(302, 226, 322, 226, color=INK, sw=2.4, bend=0.0)
    f.arrow(542, 226, 562, 226, color=INK, sw=2.4, bend=0.0)
    f.arrow(782, 226, 802, 226, color=INK, sw=2.4, bend=0.0)

    # ---- 中：三大要素 ----
    f.text(84, 344, "启动前写好的三样，每一拍都绕着它们转：", size=21, color=INK)
    regs = [
        (84, 300, BLUE_D, "CPAR：外设地址",
         ["外设寄存器只有一个地址", "整轮都不挪（PINC=0）", "配固定数据寄存器是正常配置"]),
        (412, 300, GREEN_D, "CMAR：内存地址",
         ["数组在内存里的位置", "每搬一项往后挪一格（MINC=1）", "内存那头往后挪"]),
        (740, 324, RED, "CNDTR：剩余项数",
         ["数的是配置宽度的项", "不是字节", "每搬一项减 1"]),
    ]
    for x, w, col, title, lines in regs:
        f.rect(x, 368, w, 124, color=col, fill=WHITE, sw=2.4)
        f.text(x + 14, 398, title, size=20, color=col, weight="bold")
        f.multi(x + 14, 426, lines, size=15, color=INK, lh=24)

    f.rect(84, 516, 980, 44, color=MUTED, fill=WHITE, sw=2.0)
    f.text(102, 545, "配置顺序：CPAR → CMAR → CNDTR → CCR，EN 最后置 1，之后每个请求各搬各的",
           size=17, color=INK)

    # ---- 下：CPU 与收尾 ----
    f.rect(84, 584, 470, 116, color=MUTED, fill=WHITE, sw=2.2)
    f.text(100, 614, "搬运时 CPU 在干嘛", size=20, color=MUTED, weight="bold")
    f.multi(100, 642, ["DMA 是 AHB 上的主设备，自己上总线", "CPU 继续算别的，一拍也不用等"],
            size=15, color=INK, lh=24)

    f.rect(594, 584, 470, 116, color=BLUE_D, fill=WHITE, sw=2.2)
    f.text(610, 614, "CNDTR 减到 0 之后", size=20, color=BLUE_D, weight="bold")
    f.multi(610, 642, ["普通模式：停下，产生 TC 中断", "循环模式：硬件重装，接着搬下一圈"],
            size=15, color=INK, lh=24)

    f.htext(84, 736, "外设不挪、内存 +1、计数 −1：等请求才动，动完接着等",
            size=23, color=INK, weight="bold", hl=True)
    return f


FIGS = {
    "ch10-channel-map": channel_map,
    "ch10-request-beat": request_beat,
}

if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        f = FIGS[n]()
        OUT.mkdir(parents=True, exist_ok=True)
        save(f, str(OUT / (n + ".svg")))
        print("wrote", OUT / (n + ".svg"))

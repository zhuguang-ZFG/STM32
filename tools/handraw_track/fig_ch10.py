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


def goal_evidence():
    """Five learning goals as rungs; each rung hangs one checkable artifact."""
    f = Fig("ch10-goal-evidence",
            "学习目标五级梯：每条只挂一件能指认的东西 / five goals, one artifact each")

    f.text(84, 124, "目标不是「跑通」：每一级梯子只挂一个能指认的编号、位或读数",
           size=18, color=MUTED)
    f.text(128, 158, "学习目标（五级梯）", size=15, color=MUTED)
    f.text(486, 158, "证明它的那一个东西", size=15, color=MUTED)

    # ladder rails
    f.line(92, 174, 92, 620, color=INK, sw=2.6, amp=1.0)
    f.line(452, 174, 452, 620, color=INK, sw=2.6, amp=1.0)

    rows = [
        (202, BLUE_D, "说清结构：F1 通道 / F4 流×通道",
         "映射表的一行：DMA2 Stream 5 / CH4",
         "同一行里同时有 Stream 号与 Channel 号"),
        (296, GREEN_D, "会查映射表，接对通道 / 流",
         "USART1_TX = 通道 4；USART1_RX = 通道 5",
         "F1 上这两条请求的编号是固定的"),
        (390, AMBER_STROKE, "方向、普通 / 循环、FIFO 与双缓冲",
         "DIR 与 CIRC 两个位",
         "DIR=1 内存→外设；CIRC=1 回卷"),
        (484, BLUE_D, "用 TC / HT 中断实现边收边处理",
         "HT 在第 4 个采样（8 字节），TC 在 N",
         "8 个半字缓冲：半传输不是 4 字节"),
        (578, RED, "总线争抢与 H7/F7 的 Cache 一致性",
         "AHB 主设备；F1 没有 D-Cache",
         "DMA 自己上总线，CPU 直接读新数据"),
    ]
    for i, (y, col, goal, title, sub) in enumerate(rows, 1):
        f.line(92, y, 452, y, color=col, sw=2.0, amp=1.2)
        f.circle(92, y, 15, color=col, sw=2.2, fill=WHITE)
        f.text(92, y + 6, str(i), size=16, color=col, anchor="middle",
               weight="bold")
        f.arrow(454, y, 482, y, color=col, sw=2.4, bend=0.0, head=9)
        f.rect(486, y - 38, 582, 76, color=col, fill=WHITE, sw=2.2)
        f.text(504, y - 8, title, size=19, color=col, weight="bold")
        f.text(504, y + 18, sub, size=15, color=INK)
        f.text(128, y - 12, goal, size=17, color=INK)

    f.htext(84, 690, "每一级只挂一个落点：编号、位或读数——「跑通」不算数",
            size=22, color=INK, weight="bold", hl=True)
    f.text(84, 726, "落点均取自本章正文与 RM0008 Rev 21 第 13 章；这张卡不是映射表，也不含板上测量",
           size=15, color=MUTED)
    return f


def two_level_bind():
    """F1 binds request to channel in one level; F4 adds Stream + CHSEL."""
    f = Fig("ch10-two-level-bind",
            "一层焊死，两层可配：请求怎么找到通道 / one level vs two")

    f.text(84, 124, "同一个问题——请求落在哪条通道上；F1 只有一层，F4 有两层",
           size=18, color=MUTED)

    # ---- 左：F1 只有一层 ----
    f.rect(84, 144, 472, 532, color=BLUE_D, fill=WHITE, sw=2.6)
    f.text(108, 186, "F1 · 只有一层", size=26, color=BLUE_D, weight="bold")
    f.text(108, 216, "请求线直接焊在通道上", size=17, color=MUTED)
    # mini ladder: one rung
    f.line(480, 162, 480, 206, color=BLUE_D, sw=2.2, amp=0.6)
    f.line(512, 162, 512, 206, color=BLUE_D, sw=2.2, amp=0.6)
    f.line(480, 184, 512, 184, color=BLUE_D, sw=2.2, amp=0.4)
    f.text(496, 224, "一层", size=13, color=MUTED, anchor="middle")

    f.rect(108, 252, 168, 54, color=BLUE_D, fill=WHITE, sw=2.4)
    f.text(192, 285, "USART1_RX 请求", size=15.5, color=BLUE_D,
           anchor="middle", weight="bold")
    # soldered joint
    f.line(276, 279, 304, 279, color=RED, sw=5.0, amp=0.4)
    f.circle(290, 279, 7, color=RED, fill=AMBER_FILL, sw=2.0)
    f.text(290, 244, "焊死", size=13, color=RED, anchor="middle",
           weight="bold")
    f.rect(304, 252, 228, 54, color=BLUE_D, fill=WHITE, sw=2.4)
    f.text(418, 285, "DMA1 通道 5", size=18, color=BLUE_D, anchor="middle",
           weight="bold")
    f.text(108, 340, "一根线连到底：请求只进通道 5", size=15, color=MUTED)

    # wrong channel config
    f.rect(108, 376, 424, 88, color=MUTED, fill=WHITE, sw=2.2, dash="8 5")
    f.text(124, 406, "通道 4 上写满整套参数（方向、宽度、使能）", size=16,
           color=RED, weight="bold")
    f.text(124, 436, "请求线不经过它：不报错，也永远等不到", size=15,
           color=INK)
    f.stroke([(462, 374), (462, 330)], color=RED, sw=2.0, dash="6 6", amp=0.8)
    f.stroke([(454, 322), (470, 338)], color=RED, sw=2.6, amp=0.4)
    f.stroke([(470, 322), (454, 338)], color=RED, sw=2.6, amp=0.4)
    f.text(452, 358, "请求不来", size=14, color=RED, anchor="end")

    f.text(108, 508, "一层：只有一个编号要查——通道号", size=19,
           color=BLUE_D, weight="bold")
    f.multi(108, 542, ["通道号写错，参数再全也换不来一拍",
                       "而且不报错：没有标志会提醒你"],
            size=15, color=INK, lh=26)
    f.text(108, 612, "F1 没有第二层：同一个请求换不到别的通道", size=14.5,
           color=MUTED)

    # ---- 右：F4 有两层 ----
    f.rect(596, 144, 472, 532, color=GREEN_D, fill=WHITE, sw=2.6)
    f.text(620, 186, "F4 · 有两层", size=26, color=GREEN_D, weight="bold")
    f.text(620, 216, "Stream 软件选，Channel 由 CHSEL 选", size=16,
           color=MUTED)
    # mini ladder: two rungs
    f.line(986, 158, 986, 212, color=GREEN_D, sw=2.2, amp=0.6)
    f.line(1018, 158, 1018, 212, color=GREEN_D, sw=2.2, amp=0.6)
    f.line(986, 180, 1018, 180, color=GREEN_D, sw=2.2, amp=0.4)
    f.line(986, 198, 1018, 198, color=GREEN_D, sw=2.2, amp=0.4)
    f.text(1002, 230, "两层", size=13, color=MUTED, anchor="middle")

    for x, w, req, stream in [(620, 200, "USART1_RX · CH4", "5"),
                              (848, 196, "USART1_TX · CH4", "7")]:
        cx = x + w / 2
        f.rect(x, 248, w, 46, color=GREEN_D, fill=WHITE, sw=2.2)
        f.text(cx, 277, req, size=15, color=GREEN_D, anchor="middle",
               weight="bold")
        f.arrow(cx, 294, cx, 314, color=INK, sw=2.4, bend=0.0, head=9)
        f.rect(x, 316, w, 62, color=BLUE_D, fill=WHITE, sw=2.2)
        f.text(cx, 340, "① Stream " + stream, size=17, color=BLUE_D,
               anchor="middle", weight="bold")
        f.text(cx, 361, "软件在 SxCR 里选", size=11.5, color=MUTED,
               anchor="middle")
        f.arrow(cx, 378, cx, 396, color=INK, sw=2.4, bend=0.0, head=9)
        f.rect(x, 398, w, 62, color=AMBER_STROKE, fill=WHITE, sw=2.2)
        f.text(cx, 422, "② CHSEL = 4", size=17, color=AMBER_STROKE,
               anchor="middle", weight="bold")
        f.text(cx, 443, "选 Channel", size=11.5, color=MUTED, anchor="middle")
        f.arrow(cx, 460, cx, 482, color=INK, sw=2.4, bend=0.0, head=9)
        f.text(cx, 506, "→ DMA2 Stream " + stream, size=15, color=GREEN_D,
               anchor="middle", weight="bold")

    f.text(620, 542, "同一外设 TX/RX：Stream 不同，Channel 同为 CH4",
           size=14.5, color=INK)
    f.text(620, 566, "流号错或通道号错，请求都进不来", size=14.5, color=MUTED)
    f.rect(620, 586, 424, 60, color=GREEN_D, fill=WHITE, sw=2.0)
    f.text(638, 610, "两层都要对上：Stream 号 + CHSEL 通道号", size=14,
           color=GREEN_D, weight="bold")
    f.text(638, 634, "查表时先定 Stream，再定 Channel", size=14, color=MUTED)

    f.htext(84, 716, "F1 选通道；F4 先定 Stream，再由 CHSEL 定 Channel",
            size=21, color=INK, weight="bold", hl=True)
    return f


FIGS = {
    "ch10-channel-map": channel_map,
    "ch10-request-beat": request_beat,
    "ch10-goal-evidence": goal_evidence,
    "ch10-two-level-bind": two_level_bind,
}

if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        f = FIGS[n]()
        OUT.mkdir(parents=True, exist_ok=True)
        save(f, str(OUT / (n + ".svg")))
        print("wrote", OUT / (n + ".svg"))

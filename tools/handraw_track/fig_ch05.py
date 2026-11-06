# -*- coding: utf-8 -*-
"""ch05 knowledge-track figure (facts from docs/05, RM0008 Rev 21 ch.15).

The chapter's PWM working point is 1 kHz / 50% (PSC=71 -> 1 MHz tick, ARR=999,
CCR=500); the input-capture experiment loops PA6 into PA0 (TIM2_CH1). Three
edges latch CNT into CCR: (CCR2-CCR1) x 1 us = 500 us high level, the period
needs the ARR+1 wrap fix, duty comes out 50%.
"""
from hd import *


def capture_pulse():
    f = Fig("ch05-capture-pulse",
            "捕获锁的是 CNT：三个沿一减，脉宽就出来 / capture latches the count")

    # ---- 上：PA0 上的波形与三个被锁存的边沿 ----
    f.text(84, 140, "PA6 的 1 kHz / 50% PWM 跳线接到 PA0（TIM2_CH1）：边沿一到，CNT 被硬件抄进 CCR",
           size=21, color=MUTED)
    hi, lo = 222, 306
    x1, x2, x3 = 240, 598, 986
    f.stroke([(84, lo), (x1, lo), (x1, hi), (x2, hi), (x2, lo),
              (x3, lo), (x3, hi), (1064, hi)],
             color=BLUE_D, sw=3.2, amp=1.2)
    for xx in (x1, x2, x3):
        f.stroke([(xx, hi - 12), (xx, 342)], color=INK, sw=1.4, amp=0.8,
                 dash="4 6", opacity=0.55)
    f.text(84, 186, "PA0 上的波形", size=19, color=BLUE_D, weight="bold")

    f.text(x1, 372, "① 上升沿 CCR = 0004", size=20, color=GREEN_D,
           anchor="middle", weight="bold")
    f.text(x2, 372, "② 下降沿 CCR = 0504", size=20, color=RED,
           anchor="middle", weight="bold")
    f.text(x3, 372, "③ 上升沿 CCR = 0004", size=20, color=GREEN_D,
           anchor="middle", weight="bold")
    f.text(x3, 398, "CNT 已从 999 绕回 0", size=17, color=MUTED,
           anchor="middle")

    # ---- 中：三个账本盒子 ----
    by, bh = 428, 140
    f.rect(84, by, 300, bh, color=GREEN_D, fill=WHITE, sw=2.4)
    f.text(100, by + 32, "高电平", size=22, color=GREEN_D, weight="bold")
    f.multi(100, by + 64, ["0504 − 0004 = 500 个数", "× 1 µs"],
            size=18, color=INK, lh=25)
    f.text(100, by + 120, "= 500 µs", size=24, color=GREEN_D, weight="bold")

    f.rect(412, by, 344, bh, color=BLUE_D, fill=WHITE, sw=2.4)
    f.text(428, by + 32, "周期", size=22, color=BLUE_D, weight="bold")
    f.multi(428, by + 64, ["0004 − 0004 = 0：差被吃掉了", "补上 ARR+1 = 1000 个数"],
            size=18, color=INK, lh=25)
    f.text(428, by + 120, "= 1 ms → 1 kHz", size=24, color=BLUE_D, weight="bold")

    f.rect(784, by, 280, bh, color=AMBER_STROKE, fill=WHITE, sw=2.4)
    f.text(800, by + 32, "占空比", size=22, color=AMBER_STROKE, weight="bold")
    f.text(800, by + 66, "500 / 1000", size=18, color=INK)
    f.text(800, by + 120, "= 50%", size=24, color=AMBER_STROKE, weight="bold")

    # ---- 下：溢出补偿与计数时钟 ----
    f.rect(84, 596, 620, 92, color=RED, fill=WHITE, sw=2.4)
    f.text(100, 626, "溢出要自己补：两个沿之间数到 999 又绕回 0", size=20,
           color=RED, weight="bold")
    f.multi(100, 654, ["更新中断里给差值加 ARR+1；或用 PWM 输入模式，硬件两沿一起锁"],
            size=18, color=INK, lh=26)

    f.rect(732, 596, 332, 92, color=MUTED, fill=WHITE, sw=2.2)
    f.multi(748, 624, ["72 MHz ÷ (71+1) = 1 MHz", "1 个数 = 1 µs（与 PWM 同组数）"],
            size=18, color=INK, lh=28)

    f.htext(84, 732, "口诀：捕获锁的是 CNT，两个沿相减再乘计数周期", size=24,
            color=INK, weight="bold", hl=True)
    return f


FIGS = {
    "ch05-capture-pulse": capture_pulse,
}

if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        f = FIGS[n]()
        OUT.mkdir(parents=True, exist_ok=True)
        save(f, str(OUT / (n + ".svg")))
        print("wrote", OUT / (n + ".svg"))

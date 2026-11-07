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




def resolution_grid():
    f = Fig("ch05-resolution-grid",
            "一圈的格子数 = 占空比的档位数 / duty steps = ARR+1 cells per lap")

    # ---- 顶：结论行 ----
    f.text(84, 128, "一圈只有 ARR+1 格：频率越高，一圈越短，能切的档位越少",
           size=22, color=MUTED)

    # ---- 左：10 kHz（7200 格）----
    gx, gy, cw, ch = 84, 180, 9, 9
    cols, rows = 40, 9   # 360 格代表 7200（一格 = 20 档）
    f.text(gx, gy - 16, "10 kHz：PSC=0，ARR+1 = 7200", size=20, color=BLUE_D, weight="bold")
    f.text(gx, gy + 152, "CCR = 3600 → 50%", size=19, color=INK)
    for r in range(rows):
        for c in range(cols):
            idx = r * cols + c
            x = gx + c * (cw + 2)
            y = gy + r * (ch + 2)
            filled = idx < 180
            f.rect(x, y, cw, ch,
                   color=BLUE_D if filled else MUTED,
                   fill=AMBER_FILL if filled else None, sw=1.4, r=1)
    f.text(gx, gy + 196, "占空比 1/7200 一档", size=18, color=MUTED)

    # ---- 右：50 Hz 舵机（20000 格）----
    gx2 = 636
    cols2, rows2 = 40, 10
    cw2, ch2 = 9, 8
    f.text(gx2, gy - 16, "50 Hz 舵机：PSC=71，ARR+1 = 20000", size=20, color=GREEN_D, weight="bold")
    f.text(gx2, gy + 152, "CCR = 1500 → 1.5 ms 脉宽", size=19, color=INK)
    for r in range(rows2):
        for c in range(cols2):
            idx = r * cols2 + c
            x = gx2 + c * (cw2 + 2)
            y = gy + r * (ch2 + 2)
            filled = 25 <= idx < 40      # 1.5 ms = CCR 1500：400 格里取 7.5%
            f.rect(x, y, cw2, ch2,
                   color=GREEN_D if filled else MUTED,
                   fill=GRAY_FILL if filled else None, sw=1.4, r=1)
    f.text(gx2, gy + 196, "1/20000 一档，脉宽 1–2 ms = CCR 1000–2000",
           size=18, color=MUTED)

    # ---- 底：权衡结论 ----
    f.rect(84, 470, 980, 150, color=AMBER_STROKE, fill=WHITE, sw=2.6)
    f.multi(104, 502,
            ["20 kHz 电机 PWM：PSC=0，ARR+1 = 3600 → 1/3600 一档",
             "1 kHz  breathing：PSC=71，ARR+1 = 1000 → 1/1000 一档",
             "同一 72 MHz：频率 ÷10，档位 ×10 —— 按需折中，没有双赢"],
            size=20, color=INK, lh=34)
    f.text(104, 596, "结论：先定频率需要多高，再接受剩下的分辨率",
           size=21, color=AMBER_STROKE, weight="bold")
    return f


def quadrature_decode():
    f = Fig("ch05-quadrature",
            "正交编码：A 跳变时看 B，方向就出来 / quadrature: B level at A edge")

    hi, lo = 236, 300
    # A 的半周期 132px；90° = 66px
    ax = [84, 216, 216, 348, 348, 480, 480, 612, 612, 744, 744, 876, 876, 940]
    ay = [lo, lo, hi, hi, lo, lo, hi, hi, lo, lo, hi, hi, lo, lo]
    # ---- 上：正转（B 比 A 晚 66px = 90°）----
    f.text(84, 128, "正转：B 比 A 落后 90°", size=22, color=GREEN_D, weight="bold")
    f.stroke(list(zip(ax, ay)), color=BLUE_D, sw=3.0, amp=1.2)
    bx = [84, 282, 282, 414, 414, 546, 546, 678, 678, 810, 810, 940]
    by = [lo, lo, hi, hi, lo, lo, hi, hi, lo, lo, hi, hi]
    f.stroke(list(zip(bx, by)), color=GREEN_D, sw=3.0, amp=1.2)
    f.text(952, hi - 22, "A", size=24, color=BLUE_D, weight="bold")
    f.text(952, lo + 6, "B", size=24, color=GREEN_D, weight="bold")
    for xx in (216, 480, 744):
        f.line(xx, 330, xx, 360, color=RED, sw=1.6, dash="4 5")
        f.text(xx, 386, "A↑ 时 B=0 → +1", size=17, color=RED, anchor="middle")
    f.text(1064, 342, "CNT", size=20, color=INK, anchor="end", weight="bold")
    f.text(1064, 386, "一直往上数", size=19, color=GREEN_D, anchor="end", weight="bold")

    # ---- 下：反转（B 比 A 早 66px = 90°；A 波形不变）----
    y0 = 452
    f.text(84, y0, "反转：B 比 A 超前 90°（同一对线，谁先跳交换了）",
           size=22, color=RED, weight="bold")
    ay2 = [v + y0 - 236 for v in ay]
    f.stroke(list(zip(ax, ay2)), color=BLUE_D, sw=3.0, amp=1.2)
    bx2 = [84, 150, 150, 282, 282, 414, 414, 546, 546, 678, 678, 810, 810, 940]
    by2 = [y0 + 44, y0 + 44, y0 + 108, y0 + 108, y0 + 44, y0 + 44,
           y0 + 108, y0 + 108, y0 + 44, y0 + 44, y0 + 108, y0 + 108,
           y0 + 44, y0 + 44]
    f.stroke(list(zip(bx2, by2)), color=GREEN_D, sw=3.0, amp=1.2)
    f.text(952, y0 + 22, "A", size=24, color=BLUE_D, weight="bold")
    f.text(952, y0 + 86, "B", size=24, color=GREEN_D, weight="bold")
    for xx in (216, 480, 744):
        f.line(xx, y0 + 132, xx, y0 + 162, color=RED, sw=1.6, dash="4 5")
        f.text(xx, y0 + 188, "A↑ 时 B=1 → −1", size=17, color=RED, anchor="middle")
    f.text(1064, y0 + 150, "CNT", size=20, color=INK, anchor="end", weight="bold")
    f.text(1064, y0 + 188, "一直往下数", size=19, color=RED, anchor="end", weight="bold")

    # ---- 底：为什么一路不够 ----
    f.rect(84, 700, 980, 84, color=BLUE_D, fill=WHITE, sw=2.6)
    f.multi(104, 730,
            ["只有一路方波：数得出快慢，分不清正反 —— 边沿都长一样",
             "两路相差 90°：A 跳变那一刻问一句 B 是高是低，方向就有了"],
            size=20, color=INK, lh=32)
    return f


def trgo_trigger_adc():
    f = Fig("ch05-trgo-adc",
            "TRGO：让 ADC 每 1 ms 自动转一次 / TRGO fires the ADC on schedule")

    # ---- 上：硬件触发链 ----
    boxes = [(84, "TIM3 计数", "PSC=71  ARR=999", GREEN_D),
             (392, "更新事件 UEV", "每 1 ms 一次", BLUE_D),
             (700, "TRGO 主模式", "把 UEV 送出去", AMBER_STROKE),
             (928, "ADC 开始转换", "ADCCLK 12 MHz", RED)]
    for x, title, sub, col in boxes:
        w = 240 if x == 84 else (264 if x == 392 else 208)
        f.rect(x, 200, w, 130, color=col, fill=WHITE, sw=2.6)
        f.multi(x + 16, 234, [title] + sub.split("  "), size=20, color=col,
                weight="bold", lh=32)
    f.arrow(324, 265, 392, 265, color=INK, sw=2.4, bend=0.0)
    f.arrow(656, 265, 700, 265, color=INK, sw=2.4, bend=0.0)
    f.arrow(908, 265, 928, 265, color=INK, sw=2.4, bend=0.0)

    # ---- 中：均匀采样时间轴 ----
    f.line(84, 436, 1064, 436, color=INK, sw=2.2)
    f.text(84, 404, "TRGO 触发：每 1 ms 一个转换，间隔由硬件保证",
           size=20, color=GREEN_D, weight="bold")
    for k in range(10):
        x = 100 + k * 106
        f.circle(x, 436, 7, color=GREEN_D, fill=GRAY_FILL, sw=2.2)
        f.text(x, 470, f"{k}ms", size=15, color=MUTED, anchor="middle")
        f.stroke([(x, 486), (x, 530)], color=GREEN_D, sw=2.0, amp=0.8)
    f.text(84, 552, "每拍一个结果进 DR，间隔不打折", size=17, color=MUTED)

    # ---- 下：主循环软件触发的抖动 ----
    f.text(84, 636, "主循环里软件触发：间隔 = 循环周期，忙起来就抖",
           size=20, color=RED, weight="bold")
    f.line(84, 676, 1064, 676, color=INK, sw=2.2)
    jitter = [0, 122, 210, 356, 402, 560, 588, 760, 774, 950]
    for x in jitter:
        f.circle(84 + x, 676, 7, color=RED, fill=WHITE, sw=2.2)

    f.rect(84, 726, 980, 58, color=RED, fill=WHITE, sw=2.4)
    f.text(104, 762, "采样间隔要稳，就交给定时器硬件；主循环只管取数",
           size=21, color=RED, weight="bold")
    return f


FIGS = {
    "ch05-capture-pulse": capture_pulse,
    "ch05-resolution-grid": resolution_grid,
    "ch05-quadrature": quadrature_decode,
    "ch05-trgo-adc": trgo_trigger_adc,
}

if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        f = FIGS[n]()
        OUT.mkdir(parents=True, exist_ok=True)
        save(f, str(OUT / (n + ".svg")))
        print("wrote", OUT / (n + ".svg"))

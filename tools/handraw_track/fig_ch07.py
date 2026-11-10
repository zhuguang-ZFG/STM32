# -*- coding: utf-8 -*-
"""ch07 knowledge-track figure (facts from docs/07 section 3 and the triage
caption; UM10204 Rev 6 ch. 3 as cited there).

Clock stretching gets one sentence and one table row in the chapter: a slave
that is not ready holds SCL low, the master lets go, sees the wire stay down
and has to wait (an easy way to get HAL_BUSY). It works because SCL is
wired-AND: the device that holds low the longest decides how long the low
lasts, and open-drain pins never drive the wire high. The 400 kHz working
point gives one SCL period of 2.5 us (3 x 30 / 36e6). From the triage
caption: a stretched low can outlast the HAL timeout - prove the level first,
then raise the timeout; the example keeps NoStretchMode = I2C_NOSTRETCH_DISABLE.
"""
from hd import *


def clock_stretch():
    f = Fig("ch07-clock-stretch",
            "时钟拉伸：从机按住 SCL，主机只能等 / clock stretching")

    f.text(84, 126, "400 kHz 的拍子是 2.5 µs 一拍；从机没准备好，就把 SCL 多按一会儿",
           size=20, color=MUTED)

    # ---- 上：SCL / SDA 波形，中间一拍被拉长 ----
    scl_hi, scl_lo = 180, 238
    f.stroke([(84, scl_hi), (128, scl_hi), (128, scl_lo), (183, scl_lo),
              (183, scl_hi), (238, scl_hi), (238, scl_lo), (293, scl_lo),
              (293, scl_hi), (348, scl_hi), (348, scl_lo), (403, scl_lo),
              (403, scl_hi), (458, scl_hi), (458, scl_lo), (768, scl_lo),
              (768, scl_hi), (823, scl_hi), (823, scl_lo), (878, scl_lo),
              (878, scl_hi), (1020, scl_hi)],
             color=BLUE_D, sw=3.2, amp=1.2)
    # 主机松手的位置：本该在这里升起，线没跟上
    f.line(513, 184, 513, 234, color=MUTED, sw=1.6, dash="4 4")
    f.text(513, 176, "主机松手", size=13, color=MUTED, anchor="middle")
    # 正常一拍的标注
    f.line(128, 160, 238, 160, color=MUTED, sw=1.4, amp=0.8)
    f.line(128, 154, 128, 166, color=MUTED, sw=1.4, amp=0.8)
    f.line(238, 154, 238, 166, color=MUTED, sw=1.4, amp=0.8)
    f.text(183, 150, "一拍 2.5 µs（400 kHz）", size=14, color=MUTED,
           anchor="middle")
    # 拉伸段括弧（从主机松手到从机放手）
    f.line(513, 252, 768, 252, color=RED, sw=2.0, amp=0.8)
    f.line(513, 246, 513, 258, color=RED, sw=2.0, amp=0.8)
    f.line(768, 246, 768, 258, color=RED, sw=2.0, amp=0.8)
    f.text(640, 280, "拉伸段：从机按住 SCL 不放", size=17, color=RED,
           anchor="middle", weight="bold")
    f.text(640, 302, "时钟被延长，主机需等待", size=14, color=MUTED,
           anchor="middle")

    # SDA：只在 SCL 低时变，拉伸期间纹丝不动
    sda_hi, sda_lo = 316, 360
    f.stroke([(84, sda_hi), (155, sda_hi), (155, sda_lo), (265, sda_lo),
              (265, sda_hi), (375, sda_hi), (375, sda_lo), (840, sda_lo),
              (840, sda_hi), (1020, sda_hi)],
             color=GREEN_D, sw=3.0, amp=1.2)
    f.text(640, 342, "SDA 不动：从机只是还没准备好", size=15, color=GREEN_D,
           anchor="middle")
    f.text(1032, 186, "SCL", size=18, color=BLUE_D, weight="bold")
    f.text(1032, 322, "SDA", size=18, color=GREEN_D, weight="bold")

    # ---- 中：线与机制 —— 谁低听谁的 ----
    f.text(84, 420, "为什么从机按得住：SCL 是线与，低电平最长的说了算",
           size=21, color=BLUE_D, weight="bold")
    lanes = [(452, 474, 420, BLUE_D, 2.8, "主机"),
             (498, 520, 700, RED, 2.8, "从机"),
             (544, 566, 700, INK, 3.4, "线上")]
    for hi, lo, rel, col, sw, name in lanes:
        f.stroke([(240, hi), (240, lo), (rel, lo), (rel, hi), (1010, hi)],
                 color=col, sw=sw, amp=1.0)
        mid = (hi + lo) / 2
        f.text(90, mid + 6, name, size=15, color=col, weight="bold")
    f.line(240, 448, 240, 570, color=MUTED, sw=1.2, dash="3 5", opacity=0.6)
    f.line(700, 448, 700, 570, color=MUTED, sw=1.2, dash="3 5", opacity=0.6)
    f.text(420, 446, "主机先放手", size=13, color=MUTED, anchor="middle")
    f.text(855, 590, "都松手了，上拉才把线抬回高电平", size=14, color=MUTED,
           anchor="middle")

    # ---- 下：两个结论盒子 ----
    f.rect(84, 612, 480, 116, color=GREEN_D, fill=WHITE, sw=2.4)
    f.text(100, 644, "先认出来：总线没死", size=19, color=GREEN_D,
           weight="bold")
    f.multi(100, 674, ["主机松手后 SCL 仍被拉低 = 时钟拉伸：先等从机放手",
                       "所有 I2C 主机（含 STM32 外设）都必须容忍被拉长的低电平"],
            size=15.5, color=INK, lh=26)

    f.rect(580, 612, 484, 116, color=RED, fill=WHITE, sw=2.4)
    f.text(596, 644, "后果：容易撞上 HAL_BUSY", size=19, color=RED,
           weight="bold")
    f.multi(596, 674, ["被拉伸的低电平可以超过 HAL 超时，调用返回 BUSY",
                       "先证明电平，再放大超时，别急着复位"],
            size=15.5, color=INK, lh=26)

    f.text(84, 754, "本章例程 NoStretchMode = I2C_NOSTRETCH_DISABLE：默认允许从机拉伸时钟",
           size=15, color=MUTED)
    return f


def ccr_timing():
    """Two CCR rows at PCLK1 = 36 MHz: 0x801E -> 400 kHz, 0x00B4 -> 100 kHz."""
    f = Fig("ch07-ccr-timing",
            "0x801E 与 0x00B4：36 MHz 下两行 CCR 的账 / two CCR rows at 36 MHz")

    f.text(84, 126,
           "PCLK1 = 36 MHz：一个计数 27.8 ns；快速模式 T = 3 × CCR / f，标准模式 T = 2 × CCR / f",
           size=19, color=MUTED)

    # ---- 上：快速模式 0x801E，一拍 3 个 CCR 单位 ----
    f.text(84, 222, "0x801E", size=24, color=BLUE_D, weight="bold")
    f.text(84, 250, "FAST=1, DUTY=0", size=14, color=MUTED)
    f.text(84, 272, "CCR = 30", size=14, color=MUTED)
    f.stroke([(240, 282), (240, 200), (493, 200), (493, 282), (1000, 282)],
             color=BLUE_D, sw=3.0, amp=1.2)
    f.text(366, 180, "T_high = 30 × 27.8 ns = 0.83 µs", size=14,
           color=BLUE_D, anchor="middle")
    f.text(746, 180, "T_low = 2 × 30 × 27.8 ns = 1.67 µs", size=14,
           color=BLUE_D, anchor="middle")
    f.line(240, 294, 1000, 294, color=MUTED, sw=1.3, amp=0.5)
    f.line(240, 288, 240, 300, color=MUTED, sw=1.3, amp=0.4)
    f.line(1000, 288, 1000, 300, color=MUTED, sw=1.3, amp=0.4)
    f.text(620, 320, "一拍 2.5 µs → 400 kHz", size=17, color=BLUE_D,
           anchor="middle", weight="bold")

    # ---- 下：标准模式 0x00B4，一拍 2 个 CCR 单位 ----
    f.text(84, 372, "0x00B4", size=24, color=GREEN_D, weight="bold")
    f.text(84, 400, "FAST=0, DUTY=0", size=14, color=MUTED)
    f.text(84, 422, "CCR = 180", size=14, color=MUTED)
    f.stroke([(240, 432), (240, 350), (620, 350), (620, 432), (1000, 432)],
             color=GREEN_D, sw=3.0, amp=1.2)
    f.text(430, 330, "T_high = 180 × 27.8 ns = 5 µs", size=14,
           color=GREEN_D, anchor="middle")
    f.text(810, 330, "T_low = 180 × 27.8 ns = 5 µs", size=14,
           color=GREEN_D, anchor="middle")
    f.line(240, 444, 1000, 444, color=MUTED, sw=1.3, amp=0.5)
    f.line(240, 438, 240, 450, color=MUTED, sw=1.3, amp=0.4)
    f.line(1000, 438, 1000, 450, color=MUTED, sw=1.3, amp=0.4)
    f.text(620, 470, "一拍 10 µs → 100 kHz", size=17, color=GREEN_D,
           anchor="middle", weight="bold")

    f.text(84, 502,
           "0x801E：FAST=1、DUTY=0、CCR=0x01E=30；0x00B4：FAST=0、CCR=0xB4=180",
           size=15, color=MUTED)
    f.text(84, 526,
           "两行横轴刻度不同：上一行 2.5 µs，下一行 10 µs；周期比 (3×30) : (2×180) = 1 : 4",
           size=15, color=MUTED)

    # ---- 两条边界：±2% 与没有 1 MHz ----
    f.rect(84, 548, 476, 138, color=BLUE_D, fill=WHITE, sw=2.4)
    f.text(100, 578, "±2% 从哪来", size=19, color=BLUE_D, weight="bold")
    f.multi(100, 608, ["表 41：PCLK1 取 10 MHz 的整数倍，400 kHz 才精确",
                       "36 MHz 不是 → 表 42 注 2 给 ±2%",
                       "这是时钟源的账，不是 CCR 写错"],
            size=15, color=INK, lh=25)

    f.rect(584, 548, 484, 138, color=RED, fill=WHITE, sw=2.4)
    f.text(600, 578, "为什么没有 1 MHz", size=19, color=RED, weight="bold")
    f.multi(600, 608, ["表 41 / 表 42 里没有 1 MHz 这一档",
                       "F103 的 I2C 没有 Fast-mode Plus",
                       "「可达 1 MHz」在这颗芯片上不成立"],
            size=15, color=INK, lh=25)

    f.htext(84, 720, "0x801E 不是魔法数：CCR = 30，一拍 = 3 × 30 ÷ 36 MHz = 2.5 µs",
            size=21, color=INK, weight="bold", hl=True)
    f.text(84, 750,
           "两行都按 PCLK1 = 36 MHz 复算，不含晶振实际误差与从机时钟拉伸。",
           size=15, color=MUTED)
    return f


FIGS = {
    "ch07-clock-stretch": clock_stretch,
    "ch07-ccr-timing": ccr_timing,
}

if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        f = FIGS[n]()
        OUT.mkdir(parents=True, exist_ok=True)
        save(f, str(OUT / (n + ".svg")))
        print("wrote", OUT / (n + ".svg"))

# -*- coding: utf-8 -*-
"""ch09 knowledge-track figure (facts from docs/09, RM0008 Rev 21 ch.11).

ADCCLK = 12 MHz (PCLK2 72 MHz / 6), Tconv = sample time + 12.5 cycles.
"""
from hd import *


def scan_sequence():
    """Four regular channels, their sample times, and the 30 us they add up to."""
    f = Fig("ch09-scan-sequence", "一次扫描要多久 / one scan, four channels")

    # ---- 左：SQR 序列 ----
    f.text(96, 148, "SQR 序列（规则组按顺序转）", size=24, color=MUTED)
    rows = [
        ("CH0", "1.5", "14", "1.167", GREEN_D),
        ("CH1", "13.5", "26", "2.167", BLUE_D),
        ("CH2", "55.5", "68", "5.667", AMBER_STROKE),
        ("CH3", "239.5", "252", "21.000", RED),
    ]
    y = 176
    f.text(120, y + 22, "序", size=20, color=MUTED, anchor="middle")
    f.text(210, y + 22, "采样", size=20, color=MUTED, anchor="middle")
    f.text(300, y + 22, "周期", size=20, color=MUTED, anchor="middle")
    f.text(398, y + 22, "µs", size=20, color=MUTED, anchor="middle")
    for i, (ch, smp, cyc, us, color) in enumerate(rows):
        yy = y + 40 + i * 62
        f.rect(84, yy, 60, 50, color=color, fill=WHITE)
        f.text(114, yy + 33, ch, size=20, color=color, anchor="middle",
               weight="bold")
        f.rect(160, yy, 92, 50, color=color, fill=None, sw=2.0)
        f.text(206, yy + 33, smp, size=20, color=INK, anchor="middle")
        f.rect(258, yy, 92, 50, color=color, fill=None, sw=2.0)
        f.text(304, yy + 33, cyc, size=20, color=INK, anchor="middle")
        f.rect(356, yy, 96, 50, color=color, fill=None, sw=2.0)
        f.text(404, yy + 33, us, size=20, color=INK, anchor="middle")

    f.text(84, 470, "周期 = 采样档 + 12.5（SAR 的 12 位加一次保持）", size=21,
           color=INK)
    f.text(84, 500, "ADCCLK = 72 MHz ÷ 6 = 12 MHz，不是 14 MHz", size=21,
           color=MUTED)
    f.text(84, 530, "C8 上 ÷4 会得到 18 MHz，超过 14 MHz 上限", size=21,
           color=RED)

    # ---- 右：时间条 ----
    f.text(600, 148, "一次扫描的时间条（按周期数等比）", size=24, color=MUTED)
    total_cyc = 360
    bx, by, bw, bh = 560, 176, 520, 74
    f.rect(bx, by, bw, bh, color=INK, fill=WHITE, sw=2.4)
    x = bx
    colors = [GREEN, BLUE, AMBER_STROKE, RED]
    marks = []
    for (ch, smp, cyc, us, _), color in zip(rows, colors):
        w = bw * int(cyc) / total_cyc
        f.fillrect(x, by, w, bh, color)
        f.rect(x, by, w, bh, color=color, fill=None, sw=2.2)
        if w > 52:
            f.text(x + w / 2, by + 46, ch, size=20, color=WHITE, anchor="middle",
                   weight="bold")
        marks.append((x, w, cyc, us))
        x += w
    f.text(bx + bw + 8, by + 46, "µs", size=18, color=MUTED)
    f.text(bx, by + bh + 26, "每段宽度按周期数等比", size=18, color=MUTED)

    f.htext(820, 306, "14 + 26 + 68 + 252 = 360 周期 = 30 µs", size=23,
            color=INK, weight="bold", hl=True, anchor="middle")
    f.text(600, 342, "12 MHz 下 360 ÷ 12 = 30，正好整 30 µs", size=21, color=MUTED)
    f.text(600, 374, "换一档采样时间，整轮间隔就跟着变", size=21, color=MUTED)

    # 注入组
    f.rect(560, 404, 236, 96, color=BLUE_D, fill=WHITE, sw=2.4)
    f.text(576, 434, "注入组 4 个", size=21, color=BLUE_D, weight="bold")
    f.multi(576, 462, ["可插在规则组两次转换之间", "电机电流那种紧急量走这里"],
            size=18, color=INK, lh=26)
    f.rect(806, 404, 274, 96, color=AMBER_STROKE, fill=WHITE, sw=2.4)
    f.text(820, 432, "结果寄存器只有一个", size=19, color=AMBER_STROKE,
           weight="bold")
    f.multi(820, 458, ["要配 DMA，否则后一个盖前一个", "读数顺序还要和 SQR 对齐"],
            size=17, color=INK, lh=25)

    # 温度通道
    f.arrow(300, 560, 420, 610, color=RED, bend=0.14)
    f.rect(430, 580, 620, 96, color=RED, fill=WHITE, sw=2.4)
    f.text(446, 610, "温度传感器要求 ≥ 17.1 µs：17.1 × 12 = 205.2 周期",
           size=20, color=RED, weight="bold")
    f.multi(446, 638, ["所以要选 239.5 档；71.5 档的 5.958 µs 不够",
                       "它接 CH16，内部参考接 CH17，都要先置 TSVREFE"],
            size=18, color=INK, lh=26)

    f.htext(96, 716, "先算时间，再决定通道数：一轮 30 µs 只够 33 kHz 的采样率",
            size=24, color=INK, weight="bold", hl=True)
    return f


def vrefint_cal():
    """Vrefint (ADC1 CH17, about 1.20 V) measured back to the real VDDA."""
    f = Fig("ch09-vrefint-cal",
            "Vrefint 反推 VDDA：先量尺子，再读数 / measure the ruler, then read")

    # ---- 上：机制链 ----
    f.text(84, 132, "VDDA 本身就是量尺：先用片内固定的 1.20 V 把尺子量一遍，再读别的通道",
           size=21, color=MUTED)
    f.rect(84, 156, 280, 118, color=GREEN_D, fill=WHITE, sw=2.4)
    f.text(100, 188, "ADC1 通道 17", size=21, color=GREEN_D, weight="bold")
    f.multi(100, 216, ["内部基准 ≈ 1.20 V", "先置 TSVREFE 才接通"],
            size=16, color=INK, lh=25)
    f.arrow(366, 213, 410, 213, color=INK, sw=2.4, bend=0.0)
    f.rect(414, 156, 260, 118, color=BLUE_D, fill=WHITE, sw=2.4)
    f.text(430, 188, "读 CH17 的码", size=21, color=BLUE_D, weight="bold")
    f.multi(430, 216, ["ADC_Read(Vrefint_CH17)", "典型值，不是出厂校准"],
            size=16, color=INK, lh=25)
    f.arrow(678, 213, 722, 213, color=INK, sw=2.4, bend=0.0)
    f.rect(726, 156, 338, 118, color=RED, fill=WHITE, sw=2.4)
    f.text(742, 188, "反推并修正", size=21, color=RED, weight="bold")
    f.multi(742, 216, ["VDDA = 1.20 V × 4096 ÷ code",
                       "真实 V_in = code × VDDA ÷ 4096"],
            size=16, color=INK, lh=25)

    # ---- 中：同一把尺的两种长度 ----
    f.text(84, 324, "同一个码 2048（半量程），尺子长度不同，它代表的电压就不同：",
           size=21, color=INK)

    def ruler(x, y, w, mid_v, color):
        f.line(x, y, x + w, y, color=INK, sw=2.4)
        for xx in (x, x + w / 2, x + w):
            f.line(xx, y - 9, xx, y + 9, color=INK, sw=2.0)
        f.text(x + w / 2, y - 18, mid_v, size=18, color=color, anchor="middle",
               weight="bold")
        f.text(x, y + 34, "0", size=16, color=MUTED, anchor="middle")
        f.text(x + w / 2, y + 34, "2048", size=16, color=MUTED, anchor="middle")
        f.text(x + w, y + 34, "4096", size=16, color=MUTED, anchor="middle")

    # 左：名义 3.3 V
    f.rect(84, 352, 464, 204, color=AMBER_STROKE, fill=WHITE, sw=2.4)
    f.text(102, 384, "VDDA 真是 3.30 V 时（正文换算）", size=20,
           color=AMBER_STROKE, weight="bold")
    ruler(108, 446, 416, "2048 ↔ 1.65 V", AMBER_STROKE)
    f.multi(102, 512, ["1 LSB = 3.3 V ÷ 4096 ≈ 0.806 mV",
                       "量化误差天生 ±0.5 LSB"],
            size=16, color=INK, lh=25)

    # 右：Vrefint 反推出的 2.4 V
    f.rect(600, 352, 464, 204, color=RED, fill=WHITE, sw=2.4)
    f.text(618, 384, "CH17 只读出 2048：VDDA 实际 = 2.40 V", size=20,
           color=RED, weight="bold")
    ruler(624, 446, 416, "2048 ↔ 1.20 V", RED)
    f.multi(618, 512, ["1.20 × 4096 ÷ 2048 = 2.40 V（尺子短了）",
                       "1 LSB ≈ 0.586 mV；还按 3.3 V 算就整体虚高"],
            size=16, color=INK, lh=25)

    # ---- 下：别踩 ----
    f.rect(84, 580, 980, 108, color=MUTED, fill=WHITE, sw=2.2)
    f.multi(102, 610, [
        "ADC2 的通道 16/17 接 VSS——Vrefint 只能从 ADC1 读",
        "1.20 V 是典型值：F4 才有出厂 VREFINT_CAL，F103C8 没有",
        "LQFP48 没有独立 VREF+，第 9 脚 VDDA 就是量尺，跌 1% 全表偏 1%",
    ], size=17, color=INK, lh=26)

    f.htext(84, 724, "先读 CH17 反推 VDDA，再换算别的通道——顺序不能反",
            size=23, color=INK, weight="bold", hl=True)
    return f


FIGS = {
    "ch09-scan-sequence": scan_sequence,
    "ch09-vrefint-cal": vrefint_cal,
}

if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        f = FIGS[n]()
        OUT.mkdir(parents=True, exist_ok=True)
        save(f, str(OUT / (n + ".svg")))
        print("wrote", OUT / (n + ".svg"))

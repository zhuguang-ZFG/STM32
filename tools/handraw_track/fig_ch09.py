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

    f.text(84, 470, "周期 = 采样档 + 12.5（SAR 的 12 位加一次保持）", size=18,
           color=INK)
    f.text(84, 500, "ADCCLK = 72 MHz ÷ 6 = 12 MHz，不是 14 MHz", size=18,
           color=MUTED)
    f.text(84, 530, "C8 上 ÷4 会得到 18 MHz，超过 14 MHz 上限", size=18,
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


def pa0_two_configs():
    """Same PA0: push-pull LED output in ch03 vs analog input for the ADC."""
    f = Fig("ch09-pa0-analog-config",
            "同一只 PA0：点灯与采样 / one pin, two configs")

    f.text(84, 128, "第 10 脚还是那只脚，配成输出时 ADC 读的是自己的驱动电平",
           size=21, color=MUTED)

    # ---- 左：第 03 章的推挽输出 ----
    f.rect(84, 156, 466, 216, color=AMBER_STROKE, fill=WHITE, sw=2.4)
    f.text(100, 190, "第 03 章：推挽输出", size=23, color=AMBER_STROKE,
           weight="bold")
    f.multi(100, 222, [
        "GPIO_MODE_OUTPUT_PP：输出级接通",
        "ODR=1/0，脚上是被驱动的电平",
        "ADC 采它，读到接近 0 或 VDDA 的固定码",
    ], size=17, color=INK, lh=27)
    f.text(100, 348, "灯会亮，采样却永远不动", size=18, color=AMBER_STROKE,
           weight="bold")

    # ---- 右：本章的模拟输入 ----
    f.rect(602, 156, 466, 216, color=GREEN_D, fill=WHITE, sw=2.4)
    f.text(618, 190, "本章：模拟输入", size=23, color=GREEN_D, weight="bold")
    f.multi(618, 222, [
        "GPIO_MODE_ANALOG：输出级断开",
        "引脚直连采样开关，外压经 R_AIN 充 C_ADC",
        "只改模式，通道号仍是 ADC1_IN0",
    ], size=17, color=INK, lh=27)
    f.text(618, 348, "先改脚，再开 ADC", size=18, color=GREEN_D,
           weight="bold")

    f.arrow(556, 264, 596, 264, color=INK, sw=2.6, bend=0.0)
    f.text(576, 242, "改", size=16, color=MUTED, anchor="middle")

    # ---- 中：三根脚 ----
    f.text(84, 396, "LQFP48 上真正要盯的三根脚", size=20, color=MUTED)
    pins = [
        (84, 302, GREEN_D, "第 9 脚 VDDA",
         ["参考就是它", "48 脚封装没有独立 VREF+"]),
        (402, 302, BLUE_D, "第 10 脚 PA0",
         ["ADC12_IN0", "本章的采样脚"]),
        (720, 348, RED, "第 14 脚 PA4",
         ["ADC12_IN4 / SPI1_NSS", "C8 上没有 DAC_OUT1"]),
    ]
    for x, w, color, name, lines in pins:
        f.rect(x, 412, w, 128, color=color, fill=WHITE, sw=2.2)
        f.text(x + 14, 446, name, size=20, color=color, weight="bold")
        f.multi(x + 14, 480, lines, size=16, color=INK, lh=25)

    # ---- 下：改完还要对的三件事 ----
    f.rect(84, 570, 984, 118, color=MUTED, fill=WHITE, sw=2.2)
    f.multi(102, 602, [
        "参考用第 9 脚实测的 VDDA，不是想当然的 3.3 V",
        "采样时间按源阻抗选档，高阻源先加跟随器",
        "型号查功能表：C8 没有 DAC，HAL_DAC_Start 落空",
    ], size=17, color=INK, lh=27)

    f.htext(84, 740, "点灯配输出，采样配模拟输入——同一只脚，两套配置",
            size=22, color=INK, weight="bold", hl=True)
    return f


def dac_buffer():
    """12-bit DAC: code-to-volt line and what the output buffer clips."""
    f = Fig("ch09-dac-buffer",
            "DAC 缓冲器：能带载，到不了两头 / buffer and rails")

    f.text(84, 126, "V_out = Vref × DOR / 4096：写进 DHR 的 12 位数直接决定引脚电压",
           size=20, color=MUTED)

    # ---- 左上：码值到电压 ----
    f.text(84, 170, "码值 → 电压（Vref 就是 VDDA）", size=20, color=MUTED)
    x0, x1, y = 100, 520, 228
    f.line(x0, y, x1, y, color=INK, sw=2.4)
    for xx, lab in ((x0, "0"), ((x0 + x1) / 2, "2048"), (x1, "4096")):
        f.line(xx, y - 9, xx, y + 9, color=INK, sw=2.0)
        f.text(xx, y - 18, lab, size=16, color=MUTED, anchor="middle")
    f.text(x0, y + 34, "0 V", size=16, color=MUTED, anchor="middle")
    f.text((x0 + x1) / 2, y + 34, "Vref/2", size=16, color=BLUE_D,
           anchor="middle")
    f.text(x1, y + 34, "Vref", size=16, color=MUTED, anchor="middle")
    f.multi(84, 296, [
        "12 位 4096 格：1 LSB = Vref ÷ 4096 ≈ 0.806 mV（3.3 V）",
        "缓冲器的失调会把整条线平移，两端还会削顶",
    ], size=16, color=INK, lh=25)

    # ---- 右上：任意波形的链路 ----
    f.text(570, 170, "任意波形 = 触发 + DMA + 查找表", size=20, color=MUTED)
    boxes = [(570, 116, "定时器 TRGO"), (714, 132, "DMA 循环"), (872, 168, "DHR → DOR")]
    for bx, bw, lab in boxes:
        f.rect(bx, 190, bw, 62, color=BLUE_D, fill=WHITE, sw=2.2)
        f.text(bx + bw / 2, 228, lab, size=17, color=BLUE_D, anchor="middle",
               weight="bold")
    f.arrow(688, 221, 708, 221, color=INK, sw=2.4, bend=0.0)
    f.arrow(848, 221, 866, 221, color=INK, sw=2.4, bend=0.0)
    f.multi(570, 288, [
        "触发频率决定输出频率，表在内存里自动回卷",
        "噪声：VDDA 纹波 · 数字耦合 · 缓冲器 · 量化",
    ], size=16, color=INK, lh=26)

    # ---- 中：两种缓冲 ----
    f.rect(84, 360, 466, 182, color=GREEN_D, fill=WHITE, sw=2.4)
    f.text(100, 394, "缓冲关（BOFFx=1）", size=22, color=GREEN_D,
           weight="bold")
    f.multi(100, 426, [
        "输出阻抗 ≈ 15 kΩ",
        "能贴近满摆幅，只适合高阻负载",
        "接低阻负载，电压会被拉走",
    ], size=17, color=INK, lh=27)
    f.text(100, 516, "精密的直流电平先选这一侧", size=17, color=GREEN_D)

    f.rect(602, 360, 466, 182, color=RED, fill=WHITE, sw=2.4)
    f.text(618, 394, "缓冲开（BOFFx=0）", size=22, color=RED, weight="bold")
    f.multi(618, 426, [
        "能带更重的负载",
        "失调典型 ±10 mV",
        "到不了 0 V 与 VDDA 两端",
    ], size=17, color=INK, lh=27)
    f.text(618, 516, "带载优先，但两端读数不可信", size=17, color=RED)

    # ---- 下：摆幅条 ----
    f.text(84, 576, "同一个 DOR，缓冲开与关在两端不一样：", size=20, color=INK)
    f.rect(100, 598, 950, 46, color=INK, fill=WHITE, sw=2.2)
    f.fillrect(100, 598, 26, 46, RED)
    f.fillrect(1024, 598, 26, 46, RED)
    f.text(100, 676, "0 V", size=16, color=MUTED, anchor="middle")
    f.text(1050, 676, "VDDA", size=16, color=MUTED, anchor="middle")
    f.text(576, 676, "红色两端：缓冲开时到不了，缓冲关也只能接近",
           size=16, color=MUTED, anchor="middle")

    f.htext(84, 736, "C8 没有 DAC：这段先看懂，换到带 DAC 的型号再用",
            size=21, color=INK, weight="bold", hl=True)
    return f


def adcclk_budget():
    f = Fig("ch09-adcclk-budget",
            "ADC 时钟预算：72 MHz 下的合法档 / legal ADC clock choices at 72 MHz")
    f.text(84, 118, "ADC 上限 14 MHz：PCLK2 = 72 MHz 时四个档位逐个试",
           size=21, color=MUTED)
    rows = [
        ("ADCPRE=00  ÷2", "72 ÷ 2 = 36 MHz", "超上限两倍，不行", RED, True),
        ("ADCPRE=01  ÷4", "72 ÷ 4 = 18 MHz", "还是超过 14 MHz，不行", RED, True),
        ("ADCPRE=10  ÷6", "72 ÷ 6 = 12 MHz", "最高合法档，速度优先选它", GREEN_D, False),
        ("ADCPRE=11  ÷8", "72 ÷ 8 = 9 MHz", "也合法，只是转换更慢", GREEN_D, False),
    ]
    y = 158
    for t, m, n, c, bad in rows:
        f.rect(84, y, 980, 82, color=c, fill=WHITE, sw=2.6)
        f.text(116, y + 36, t, size=24, color=c, weight="bold")
        f.text(430, y + 36, m, size=24, color=INK, weight="bold")
        f.text(700, y + 36, n, size=19, color=MUTED)
        if bad:
            f.text(1000, y + 46, "✗", size=32, color=c, weight="bold")
        else:
            f.text(1000, y + 46, "✓", size=32, color=c, weight="bold")
        y += 100
    f.rect(84, y + 12, 980, 92, color=INK, fill=WHITE, sw=2.2)
    f.text(112, y + 48,
           "RM0008 的「Tconv = 1 µs」是 14 MHz、采样 1.5 周期的例子；",
           size=20, color=INK)
    f.text(112, y + 80,
           "C8 在 72 MHz 主频下取 ÷6 = 12 MHz（最快合法档），换算分母用 4096。",
           size=20, color=INK)
    return f


def part_scope():
    """Three parts x four capability rows (DAC, adder, calibration, factory)."""
    f = Fig("ch09-part-scope", "三种型号，四行能力 / three parts, four rows")
    f.text(84, 124, "同一段 DAC 与校准文字，只在带这些功能的型号上成立",
           size=21, color=MUTED)

    label_x, label_w = 84, 240
    cols = [(324, GREEN_D, "F103C8 中容量"),
            (572, BLUE_D, "F103 大容量"),
            (820, AMBER_STROKE, "F4")]
    top, hdr_h, row_h = 142, 64, 104
    f.rect(label_x, top, label_w, hdr_h, color=MUTED, fill=WHITE, sw=2.2)
    f.text(label_x + 16, top + 40, "能力 / 型号", size=18, color=MUTED,
           weight="bold")
    for x, color, name in cols:
        f.rect(x, top, 248, hdr_h, color=color, fill=WHITE, sw=2.4)
        f.text(x + 124, top + 40, name, size=19, color=color, anchor="middle",
               weight="bold")

    rows = [
        ("DAC 有无", [
            (["无：调用没有输出"], RED, "✗"),
            (["有：大容量才有"], GREEN_D, "✓"),
            (["有：DAC1 / DAC2"], GREEN_D, "✓"),
        ]),
        ("转换段", [
            (["12.5 周期"], INK, ""),
            (["12.5 周期"], INK, ""),
            (["12 周期"], INK, ""),
        ]),
        ("上电校准", [
            (["要：ADON 后置 CAL"], INK, ""),
            (["要（同 F1）"], INK, ""),
            (["不要", "（HAL 无此步）"], INK, ""),
        ]),
        ("出厂校准值", [
            (["没有", "（典型值非出厂）"], RED, "✗"),
            (["F1 典型值", "不是出厂校准"], MUTED, ""),
            (["TS_CAL1 / TS_CAL2", "VREFINT_CAL"], GREEN_D, "✓"),
        ]),
    ]
    for i, (label, cells) in enumerate(rows):
        y = top + hdr_h + i * row_h
        f.rect(label_x, y, label_w, row_h, color=MUTED, fill=WHITE, sw=2.0)
        f.text(label_x + 16, y + 52, label, size=18, color=INK, weight="bold")
        for (x, color, _), (lines, tcolor, mark) in zip(cols, cells):
            f.rect(x, y, 248, row_h, color=color, fill=WHITE, sw=1.8)
            if len(lines) == 1:
                f.text(x + 14, y + 52, lines[0], size=16, color=tcolor)
            else:
                f.multi(x + 14, y + 40, lines, size=16, color=tcolor, lh=25)
            if mark:
                f.text(x + 222, y + 34, mark, size=22, color=tcolor,
                       anchor="middle", weight="bold")

    f.rect(84, 640, 984, 84, color=MUTED, fill=WHITE, sw=2.2)
    f.multi(102, 670, [
        "DS5319：中容量都有两个 12 位 ADC；C8 有 ADC1/ADC2，没有 ADC3，没有 DAC",
        "DAC 缓冲器、噪声与上电校准那几段，只对带这些功能的型号成立",
    ], size=17, color=INK, lh=28)

    f.htext(84, 760, "先查型号有没有这个外设，再照抄那段配置",
            size=22, color=INK, weight="bold", hl=True)
    return f


def tconv_floor():
    """Three gates in series end at the 14-cycle floor."""
    f = Fig("ch09-tconv-floor",
            "一次转换的三道闸 / three gates to one conversion")
    f.text(84, 124, "ADCCLK、采样段、转换段依次收窄；最短也绕不过 14 周期",
           size=21, color=MUTED)

    cards = [
        (84, GREEN_D, "闸一 · ADCCLK",
         ["≤ 14 MHz 硬上限", "72 ÷ 6 = 12 MHz", "÷4 得 18 MHz，越限"]),
        (426, BLUE_D, "闸二 · 采样段",
         ["1.5 周期只有 125 ns", "100 kΩ 源约需 7.8 µs", "充不满就带上次电压"]),
        (768, AMBER_STROKE, "闸三 · 12.5 周期",
         ["SAR 12 位加一次保持", "固定跟在采样之后", "不能再削"]),
    ]
    for x, color, head, lines in cards:
        f.rect(x, 156, 300, 160, color=color, fill=WHITE, sw=2.4)
        f.text(x + 16, 192, head, size=20, color=color, weight="bold")
        f.multi(x + 16, 226, lines, size=16, color=INK, lh=27)
    f.arrow(388, 236, 420, 236, color=INK, sw=2.4, bend=0.0)
    f.arrow(730, 236, 762, 236, color=INK, sw=2.4, bend=0.0)

    f.htext(576, 388, "1.5 + 12.5 = 14 周期", size=28, color=INK,
            weight="bold", hl=True, anchor="middle")

    f.text(84, 448, "把 14 周期摊开（ADCCLK = 12 MHz）", size=18,
           color=MUTED)
    bx, by, bw, bh = 84, 482, 900, 72
    gw = bw * 1.5 / 14
    f.fillrect(bx, by, gw, bh, GREEN)
    f.fillrect(bx + gw, by, bw - gw, bh, BLUE)
    f.rect(bx, by, gw, bh, color=GREEN_D, fill=None, sw=2.2)
    f.rect(bx + gw, by, bw - gw, bh, color=BLUE_D, fill=None, sw=2.2)
    f.text(bx + gw / 2, by - 8, "采样 1.5", size=15, color=GREEN_D,
           anchor="middle", weight="bold")
    f.text(bx + gw + (bw - gw) / 2, by + 44, "转换 12.5 周期", size=18,
           color=WHITE, anchor="middle", weight="bold", halo=False)
    f.text(bx, by + bh + 26, "0", size=15, color=MUTED, anchor="middle")
    f.text(bx + bw, by + bh + 26, "14 周期 = 1.167 µs", size=17, color=INK,
           anchor="end", weight="bold")
    f.line(bx + bw, by - 24, bx + bw, by + bh + 6, color=RED, sw=2.4,
           dash="8 6")
    f.text(bx + bw + 12, by + 10, "下限", size=16, color=RED, weight="bold")

    f.rect(84, 596, 984, 88, color=INK, fill=WHITE, sw=2.2)
    f.text(104, 628, "最短一次转换 = 14 周期 ≈ 1.167 µs", size=21,
           color=INK, weight="bold")
    f.text(104, 660, "继续把采样削下去，也到不了 14 周期以下", size=17,
           color=MUTED)

    f.text(84, 716, "1.167 µs 是按 12 MHz 算出的下限；触发与 DMA 开销另计。",
           size=16, color=MUTED)
    f.htext(84, 752, "先守住 14 周期这个地板，再谈采样率", size=22,
            color=INK, weight="bold", hl=True)
    return f


def evidence_lanes():
    """Three evidence lanes around one crossed-out printed voltage."""
    f = Fig("ch09-evidence-lanes", "三份证据，一个数不够 / three evidence lanes")
    f.text(84, 120, "串口只打印一个电压，分不清量化误差、源阻抗与缓冲区顺序",
           size=20, color=MUTED)

    f.rect(496, 138, 160, 64, color=RED, fill=WHITE, sw=2.6)
    f.line(506, 148, 528, 157, color=RED, sw=3.2)
    f.line(624, 181, 646, 192, color=RED, sw=3.2)
    f.line(646, 148, 624, 157, color=RED, sw=3.2)
    f.line(528, 181, 506, 192, color=RED, sw=3.2)
    f.text(576, 178, "1.65 V", size=24, color=INK, anchor="middle",
           weight="bold")
    f.text(486, 176, "只打印一个电压", size=17, color=RED, anchor="end")
    f.text(666, 176, "分不开三类误差", size=17, color=MUTED)

    f.arrow(520, 206, 236, 258, color=INK, sw=2.2, bend=0.10)
    f.arrow(576, 206, 576, 258, color=INK, sw=2.2, bend=0.0)
    f.arrow(632, 206, 916, 258, color=INK, sw=2.2, bend=0.10)

    lanes = [
        (84, GREEN_D, "① 引脚电压", "输入与码值对账",
         ["万用表量 V_in", "低 / 中 / 高三点", "记录实测 VDDA", "换算电压对码值"]),
        (424, BLUE_D, "② 配置与状态", "外设状态对账",
         ["ADON / EOC 状态", "SMPR 采样档", "ADCCLK 12 MHz", "校准前后各一组"]),
        (764, AMBER_STROKE, "③ 内存码值数组", "内存结果对账",
         ["数组顺序对齐 SQR", "HT / TC 次数", "CNDTR 剩余计数", "64 个半字的记录"]),
    ]
    for x, color, head, sub, items in lanes:
        f.rect(x, 270, 304, 252, color=color, fill=WHITE, sw=2.4)
        f.text(x + 16, 306, head, size=20, color=color, weight="bold")
        f.text(x + 16, 332, sub, size=15, color=MUTED)
        f.line(x + 16, 346, x + 288, 346, color=color, sw=1.4, dash="6 5")
        for j, item in enumerate(items):
            f.circle(x + 24, 371 + j * 33, 4, color=color, sw=1.6)
            f.text(x + 38, 377 + j * 33, item, size=16, color=INK)

    f.rect(84, 548, 984, 92, color=MUTED, fill=WHITE, sw=2.2)
    f.text(102, 582,
           "一个数分不开量化误差、源阻抗与缓冲区顺序；三条道各排除一类",
           size=17, color=INK)
    f.text(102, 614, "它们都不能替代万用表或示波器，本身不记录任何实测",
           size=17, color=INK)

    f.htext(84, 704, "先凑齐三份证据，再动一个参数", size=22,
            color=INK, weight="bold", hl=True)
    return f


def mode_stops():
    """Four lanes from one trigger, plus the scan+continuous+DMA stack."""
    f = Fig("ch09-mode-stops", "四条道，同一次触发 / four lanes, one trigger")
    f.text(84, 118, "四种模式只在「什么时候停、什么让它再开始」上不同",
           size=20, color=MUTED)

    f.rect(212, 130, 180, 50, color=INK, fill=WHITE, sw=2.2)
    f.text(302, 162, "同一次触发", size=18, color=INK, anchor="middle",
           weight="bold")

    labels = [
        (190, "单次 Single", "叫一声转一次"),
        (290, "连续 Continuous", "转完立即重启"),
        (390, "扫描 Scan", "按 SQR 走完清单"),
        (490, "间断 Discontinuous", "走 n 个就暂停"),
    ]
    for y, name, sub in labels:
        f.rect(318, y, 750, 92, color=MUTED, fill=WHITE, sw=1.8)
        f.text(84, y + 38, name, size=20, color=INK, weight="bold")
        f.text(84, y + 64, sub, size=16, color=MUTED)

    # trigger bus drawn over the lane cards
    f.line(302, 180, 302, 536, color=INK, sw=2.4)
    for y in (236, 336, 436, 536):
        f.circle(330, y, 3.5, color=INK, sw=1.4)
        f.line(302, y, 330, y, color=INK, sw=2.0)

    # lane 1: single
    y = 190
    f.rect(338, y + 18, 170, 56, color=GREEN_D, fill=WHITE, sw=2.2)
    f.text(423, y + 52, "转换 1 次", size=17, color=GREEN_D,
           anchor="middle", weight="bold")
    f.arrow(512, y + 46, 552, y + 46, color=INK, sw=2.4, bend=0.0)
    f.rect(556, y + 18, 110, 56, color=RED, fill=WHITE, sw=2.2)
    f.text(611, y + 52, "停", size=18, color=RED, anchor="middle",
           weight="bold")
    f.text(690, y + 51, "转完就停，等下一次触发", size=16, color=MUTED)

    # lane 2: continuous
    y = 290
    f.rect(338, y + 18, 300, 56, color=BLUE_D, fill=WHITE, sw=2.2)
    f.text(488, y + 52, "转换完立即重启", size=17, color=BLUE_D,
           anchor="middle", weight="bold")
    f.arrow(620, y + 12, 360, y + 12, color=GREEN_D, sw=2.2, bend=0.05,
            head=10)
    f.text(660, y + 51, "一直不停，直到关掉", size=16, color=MUTED)

    # lane 3: scan
    y = 390
    for j, ch in enumerate(("CH0", "CH1", "CH2", "CH3")):
        bx = 338 + j * 98
        f.rect(bx, y + 18, 90, 56, color=AMBER_STROKE, fill=WHITE, sw=2.0)
        f.text(bx + 45, y + 52, ch, size=17, color=AMBER_STROKE,
               anchor="middle", weight="bold")
    f.text(744, y + 51, "走完清单才停", size=16, color=MUTED)

    # lane 4: discontinuous
    y = 490
    f.rect(338, y + 18, 170, 56, color=GREEN_D, fill=WHITE, sw=2.2)
    f.text(423, y + 52, "n 个通道", size=17, color=GREEN_D,
           anchor="middle", weight="bold")
    f.arrow(512, y + 46, 552, y + 46, color=INK, sw=2.4, bend=0.0)
    f.rect(556, y + 18, 110, 56, color=RED, fill=WHITE, sw=2.2)
    f.text(611, y + 52, "暂停", size=18, color=RED, anchor="middle",
           weight="bold")
    f.text(690, y + 51, "等下一次触发再走 n 个", size=16, color=MUTED)

    # bottom: the common stack
    f.rect(84, 602, 984, 104, color=INK, fill=WHITE, sw=2.4)
    f.text(104, 634, "项目常态：扫描 + 连续 + DMA 循环", size=19,
           color=INK, weight="bold")
    stack = [(104, "SQR 多通道"), (404, "连续重启"), (704, "DMA 循环搬数")]
    for bx, name in stack:
        f.rect(bx, 648, 250, 46, color=BLUE_D, fill=WHITE, sw=2.0)
        f.text(bx + 125, 677, name, size=16, color=BLUE_D, anchor="middle",
               weight="bold")
    f.arrow(356, 671, 400, 671, color=INK, sw=2.2, bend=0.0)
    f.arrow(656, 671, 700, 671, color=INK, sw=2.2, bend=0.0)

    f.htext(84, 752, "扫描 + 连续 + DMA 是常态，单次与间断按需用", size=22,
            color=INK, weight="bold", hl=True)
    return f


FIGS = {
    "ch09-scan-sequence": scan_sequence,
    "ch09-vrefint-cal": vrefint_cal,
    "ch09-pa0-analog-config": pa0_two_configs,
    "ch09-dac-buffer": dac_buffer,
    "ch09-adcclk-budget": adcclk_budget,
    "ch09-part-scope": part_scope,
    "ch09-tconv-floor": tconv_floor,
    "ch09-evidence-lanes": evidence_lanes,
    "ch09-mode-stops": mode_stops,
}

if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        f = FIGS[n]()
        OUT.mkdir(parents=True, exist_ok=True)
        save(f, str(OUT / (n + ".svg")))
        print("wrote", OUT / (n + ".svg"))

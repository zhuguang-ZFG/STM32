# -*- coding: utf-8 -*-
"""V4a redraws: six legacy AI-generated plates rebuilt in the handraw
grammar (deterministic, Chinese labels, pinned facts).

The old PNGs (ch13-can-bit, ch13-bit-quanta, ch13-filter-fifo,
ch14-usb-enum, ch14-usbpre-48, ch00-three-api-lanes) were one-off AI
images with no script; two carried content errors (three FIFO boxes all
labelled FIFO0; a 'HAL 入门推荐' stamp contradicting ch46's unified
caliber) and one had garbled glyphs. Slugs stay unchanged so chapter
embeds keep working; the legacy ch13/ch14 prefixes point at merged
ch35 (CAN/USB) and ch46 (API lanes).

Facts pinned from ch35/ch46 sheets:
- CAN: F103@36M P9x8Tq=500k@75%; F407@42M P6x14Tq=500k@85.7% and
  P7x12Tq=500k@83.3%; 450k needs P=8x10Tq (36M/80), 500k@10Tq wants
  P=7.2 -> P=7 gives 514.3k; cross-copy F103->F407 583.3k, F407->F103
  428.6k; sample point (1+BS1)/(1+BS1+BS2); 14 banks F103 / 28 F407;
  standard ID << 5 (0x123<<5=0x2460); FOVR = lost frame.
- USB: seven enumeration steps; device desc 18 B (0x12, EP0 64);
  config set 67 B = 9+9+5+5+4+5+7+9+7+7; VID/PID 0x1209/0x0001 vs ST
  0x0483/0x5740; F103 USBPRE=0 -> 72/1.5=48, USBPRE=1 -> 72 direct;
  F407 PLLQ 336/7=48 dedicated line; D+ 1.5k on PA12.
- ch46 unified caliber: 寄存器打底 + HAL 做产品, one lane per week.
"""
from pathlib import Path

from hd import (AMBER_PALE, AMBER_STROKE, BLUE_D, BLUE_FILL, GRAY_FILL,
                GREEN_D, GREEN_FILL, INK, MUTED, RED, RED_FILL, WHITE, Fig,
                save)

STAGE = Path(__file__).resolve().parents[2] / ".temp" / "l0-l5-pass" / "figures"
MONO = "'Consolas','Courier New',monospace"


def ch13_can_bit():
    """500k working points on two clocks + the 450k divisibility trap."""
    f = Fig("ch13-can-bit",
            "CAN 位时序：分母不同，数字不能互抄",
            title_color=BLUE_D, tag="CH 35 · CAN")
    f.text(64, 126,
           "同一个 500 kbit/s，APB1 一变工作点就变；先验算整除，再挑档位。",
           size=19, color=MUTED)

    pts = [
        ("F103 @ 36 MHz", "P=9 × 8 Tq", "500 kbit/s", "采样 75%", BLUE_D, BLUE_FILL),
        ("F407 @ 42 MHz", "P=6 × 14 Tq", "500 kbit/s", "采样 85.7%", GREEN_D, GREEN_FILL),
        ("F407 @ 42 MHz", "P=7 × 12 Tq", "500 kbit/s", "采样 83.3%", GREEN_D, GREEN_FILL),
    ]
    for i, (plat, wp, rate, sp, c, fl) in enumerate(pts):
        x = 64 + i * 344
        f.card(x, 156, 328, 190, c, fill=fl)
        f.text(x + 16, 188, plat, size=17, color=c, weight="bold")
        f.text(x + 16, 222, wp, size=19, color=INK, font=MONO, weight="bold")
        f.metric(x + 16, 286, rate, sp, c, value_size=21)
        if i < 2:
            f.arrow(x + 328, 250, x + 344, 250, color=MUTED, sw=2.0,
                    bend=0.0, head=8)

    # cross-copy consequences
    f.panel(64, 366, 1024, 96, RED_FILL, amp=1.6)
    f.rect(64, 366, 1024, 96, color=RED, sw=1.8, fill=None, amp=1.6)
    f.text(88, 396, "互抄的下场（都错）：", size=15.5, color=RED,
           weight="bold")
    f.text(88, 424, "F103 的 (P9,5,2) 抄到 F407 → 42M/(9×8) = 583.3 kbit/s；F407 的 (6,11,2) 抄回 F103 → 36M/(6×14) = 428.6 kbit/s",
           size=14.5, color=INK, font=MONO)
    f.text(88, 450, "整条总线跟着错——这正是「波特率算错一步整条总线瘫痪」的源头",
           size=13.5, color=MUTED)

    # 450k counterexample
    f.panel(64, 486, 1024, 110, AMBER_PALE, amp=1.6)
    f.rect(64, 486, 1024, 110, color=AMBER_STROKE, sw=1.8, fill=None,
           amp=1.6)
    f.text(88, 518, "450 kbit/s 反例：先验算整除", size=15.5,
           color=AMBER_STROKE, weight="bold")
    f.text(88, 548, "P=8 × 10 Tq：36M/(8×10) = 450 kbit/s，恰好成立；", size=14.5,
           color=INK, font=MONO)
    f.text(88, 576, "500 kbit/s@10 Tq 要 P=7.2——非整数；硬写 7 → 36M/70 = 514.3 kbit/s",
           size=14.5, color=INK, font=MONO)

    f.htext(64, 700, "SYNC 1 Tq + BS1 + BS2；采样点 = (1+BS1) ÷ 总 Tq",
            size=22, color=INK, weight="bold", hl=True)
    f.text(576, 730,
           "工作点与反例取自本章算术（36M/42M 口径）；布局示意，非实测。",
           size=14, color=MUTED, anchor="middle")
    return f


def ch13_bit_quanta():
    """The 8-Tq bar: SYNC + BS1 + BS2, sample at 75%."""
    f = Fig("ch13-bit-quanta",
            "CAN 位时间三段式",
            title_color=BLUE_D, tag="CH 35 · CAN")
    f.text(64, 126,
           "F103@36 MHz、P=9：一个 Tq 250 ns，8 个 Tq = 2 µs = 一位，500 kbit/s。",
           size=19, color=MUTED)

    # ---- the Tq bar ----
    segs = [("SYNC 1 Tq", 1, GREEN_D, GREEN_FILL),
            ("BS1 5 Tq", 5, AMBER_STROKE, AMBER_PALE),
            ("BS2 2 Tq", 2, BLUE_D, BLUE_FILL)]
    x = 120
    unit = 106
    for name, tq, c, fl in segs:
        w = unit * tq
        f.rect(x, 190, w, 92, color=c, fill=fl, sw=2.6, double=False)
        f.text(x + w / 2, 246, name, size=19, color=c, anchor="middle",
               weight="bold")
        x += w
    sx = 120 + unit * 6  # sample point after SYNC+BS1
    f.line(sx, 168, sx, 306, color=RED, sw=2.6, amp=0.6)
    f.text(sx + 14, 164, "采样点：(1+5)/8 = 75%", size=15, color=RED,
           weight="bold")

    # ---- arithmetic strip ----
    f.panel(120, 340, 960, 96, GRAY_FILL, amp=1.6)
    f.rect(120, 340, 960, 96, color=MUTED, sw=1.6, fill=None, amp=1.6)
    f.text(144, 372, "Tq = APB1 ÷ 预分频：36 MHz ÷ 9 = 4 MHz → 250 ns",
           size=15.5, color=INK, font=MONO)
    f.text(144, 402, "位时间 = 8 × 250 ns = 2 µs → 36M/(9×8) = 500 kbit/s",
           size=15.5, color=BLUE_D, font=MONO, weight="bold")
    f.text(144, 426, "SJW=1：再同步一次最多伸/缩 1 个 Tq", size=13.5,
           color=MUTED)

    # ---- two notes ----
    f.card(120, 466, 460, 130, GREEN_D, fill=GREEN_FILL)
    f.text(140, 498, "总线上还要有的", size=16.5, color=GREEN_D,
           weight="bold")
    f.text(140, 528, "两端位时间相同；各 120 Ω 终端", size=14.5, color=INK)
    f.text(140, 554, "BluePill 的 CAN 重映射到 PB8/PB9", size=14.5,
           color=INK)
    f.text(140, 580, "PA11/PA12 让给 USB", size=14.5, color=MUTED)

    f.card(620, 466, 460, 130, RED, fill=RED_FILL)
    f.text(640, 498, "数字抄错平台的症状", size=16.5, color=RED,
           weight="bold")
    f.text(640, 528, "位时间整体偏掉，采样点错位", size=14.5, color=INK)
    f.text(640, 554, "轻则误码重试，重则整网无 ACK", size=14.5, color=INK)
    f.text(640, 580, "先把 (P, BS1, BS2) 三元组算对", size=14.5, color=MUTED)

    f.htext(64, 700, "波特率 = APB1 ÷ (P × 总 Tq)；三个数都是算出来的，不是抄的",
            size=21, color=INK, weight="bold", hl=True)
    f.text(576, 730,
           "取自本章 500k 工作点复算；比例示意，非实测波形。",
           size=14, color=MUTED, anchor="middle")
    return f


def ch13_filter_fifo():
    """14 filter banks feed two FIFOs (fixes the triple-FIFO0 old plate)."""
    f = Fig("ch13-filter-fifo",
            "CAN 过滤器：14 组银行，两个 FIFO",
            title_color=GREEN_D, tag="CH 35 · CAN")
    f.text(64, 126,
           "F103 有 14 组过滤器（F407 是 28 组，CAN1/CAN2 共享）；收到的帧进 FIFO0 还是 FIFO1 由分配决定。",
           size=19, color=MUTED)

    # ---- banks column ----
    f.card(64, 156, 470, 330, BLUE_D, fill=BLUE_FILL)
    f.text(84, 188, "过滤器银行 Bank 0–13", size=18, color=BLUE_D,
           weight="bold")
    banks = [("掩码模式", "ID+掩码，一段位宽内比对"),
             ("列表模式", "精确 ID 逐个列出"),
             ("32 位宽", "扩展 ID / 标准 ID 全量"),
             ("16 位宽", "两个标准 ID 拼一组")]
    for i, (a, b) in enumerate(banks):
        y = 218 + i * 52
        f.pill(84, y - 20, 170, 36, a, BLUE_D, fill=WHITE, size=14.5)
        f.text(272, y + 4, b, size=13.5, color=INK)
    f.text(84, 452, "留在初始化模式的过滤器收不到任何帧", size=13.5,
           color=RED, weight="bold")

    # ---- FIFO column ----
    f.card(600, 156, 488, 330, GREEN_D, fill=GREEN_FILL)
    f.text(620, 188, "两个接收 FIFO（各 3 级深）", size=18, color=GREEN_D,
           weight="bold")
    f.pill(620, 208, 200, 40, "FIFO0", GREEN_D, fill=WHITE, size=17)
    f.text(840, 234, "硬实时 ID 走这", size=13.5, color=INK)
    f.pill(620, 262, 200, 40, "FIFO1", AMBER_STROKE, fill=WHITE, size=17)
    f.text(840, 288, "大批量遥测走这", size=13.5, color=INK)
    f.text(620, 330, "各挂各自的中断线；", size=14, color=INK)
    f.text(620, 354, "把硬实时和遥测分开，遥测洪峰不淹实时", size=14,
           color=INK)
    f.text(620, 396, "组→FIFO 的分配在初始化时写死", size=13.5, color=MUTED)
    f.text(620, 452, "FOVR 置位 = FIFO 满溢出，帧已丢——修消费速率，不是修过滤器",
           size=13.5, color=RED, weight="bold")

    # ---- ID left-shift strip ----
    f.panel(64, 516, 1024, 96, AMBER_PALE, amp=1.6)
    f.rect(64, 516, 1024, 96, color=AMBER_STROKE, sw=1.8, fill=None,
           amp=1.6)
    f.text(88, 548, "32 位掩码模式下标准 ID 左移 5 位：STID[10:0] 落在寄存器高半的 bit[15:5]",
           size=15, color=AMBER_STROKE, weight="bold")
    f.text(88, 578, "0x123 << 5 = 0x2460；掩码 0x7FF << 5 = 0xFFE0——不左移，邮箱一直为空",
           size=14.5, color=INK, font=MONO)
    f.text(88, 602, "F407 是 28 组（CAN1/CAN2 共享）：把 F103 的 14 组照抄过去，只收到一半的帧",
           size=13.5, color=MUTED)

    f.htext(64, 700, "过滤器决定「收谁的帧」，FIFO 决定「进哪条中断」——两件事别混",
            size=21, color=INK, weight="bold", hl=True)
    f.text(576, 730,
           "组数与模式取自本章 RM0008/RM0090 §32 口径；结构示意。",
           size=14, color=MUTED, anchor="middle")
    return f


def ch14_usb_enum():
    """Seven enumeration steps with the choke points and pinned numbers."""
    f = Fig("ch14-usb-enum",
            "USB 枚举七步与卡点分诊",
            title_color=BLUE_D, tag="CH 35 · USB")
    f.text(64, 126,
           "全速设备的枚举顺序（USB 2.0 规范第 9 章口径）；哪一步卡住，查的方向不同。",
           size=19, color=MUTED)

    steps = ["复位", "地址 0 取设备\n描述符前 8 字节", "Set Address",
             "读全设备描述符", "配置集合\n（校验 wTotalLength）",
             "Set Configuration", "就绪"]
    xs = 66
    step_w = 136
    pitch = 152
    marks = "①②③④⑤⑥⑦"
    for i, s in enumerate(steps):
        x = xs + i * pitch
        c = GREEN_D if i in (0, 6) else BLUE_D
        fl = GREEN_FILL if i in (0, 6) else BLUE_FILL
        lines = s.split("\n")
        f.card(x, 162, step_w, 76, c, fill=fl)
        f.text(x + step_w / 2, 148, marks[i], size=13, color=c,
               anchor="middle", weight="bold")
        for j, ln in enumerate(lines):
            f.text(x + 10, 190 + j * 22, ln, size=12.5,
                   color=c if j == 0 else INK, weight="bold" if j == 0 else "normal")
        if i < 6:
            f.arrow(x + step_w + 2, 200, x + pitch - 2, 200, color=MUTED,
                    sw=2.0, bend=0.0, head=7)

    # ---- pinned numbers ----
    f.card(64, 268, 500, 220, GREEN_D, fill=GREEN_FILL)
    f.text(84, 300, "例程描述符的硬数（cdc 实读）", size=17,
           color=GREEN_D, weight="bold")
    nums = [("设备描述符 18 B", "首字节 0x12；bMaxPacketSize0 = 64"),
            ("配置集合 67 B", "wTotalLength 0x0043，不是 9 B 本体"),
            ("VID/PID 0x1209/0x0001", "pid.codes 占位号，别印进量产"),
            ("bMaxPower 0x32", "= 100 mA")]
    for i, (a, b) in enumerate(nums):
        y = 330 + i * 38
        f.text(84, y, a, size=14.5, color=INK, font=MONO, weight="bold")
        f.text(84, y + 18, b, size=12.5, color=MUTED)

    # ---- choke points ----
    f.card(588, 268, 500, 220, RED, fill=RED_FILL)
    f.text(608, 300, "卡点分诊", size=17, color=RED, weight="bold")
    cps = [("第一步就失败", "查 48 MHz 时钟来路"),
           ("wTotalLength 不对", "查描述符链拼接"),
           ("配置后不工作", "查端点就绪与 bMaxPower"),
           ("报「未知设备」", "时钟偏了，主机读不出描述符")]
    for i, (a, b) in enumerate(cps):
        y = 330 + i * 38
        f.text(608, y, a, size=14.5, color=RED, weight="bold")
        f.text(608, y + 18, b, size=12.5, color=INK)

    # ---- USBPRE strip ----
    f.panel(64, 516, 1024, 84, AMBER_PALE, amp=1.6)
    f.rect(64, 516, 1024, 84, color=AMBER_STROKE, sw=1.8, fill=None,
           amp=1.6)
    f.text(88, 548, "时钟前提：F103 USBPRE=0 → 72÷1.5 = 48 MHz；USBPRE=1 → 72 MHz 直进，枚举必败",
           size=15, color=AMBER_STROKE, weight="bold")
    f.text(88, 578, "F407 走 OTG_FS 专用 48 MHz（PLLQ 336/7）；ST 例程的 VID/PID 0x0483/0x5740 不是这份固件",
           size=13.5, color=MUTED)

    f.htext(64, 700, "先查时钟，再查描述符，最后查端点——顺序反了会绕远路",
            size=21, color=INK, weight="bold", hl=True)
    f.text(576, 730,
           "硬数取自 examples/usb-cdc 描述符实读与 USB 2.0 规范第 9 章；流程示意。",
           size=14, color=MUTED, anchor="middle")
    return f


def ch14_usbpre_48():
    """Two 48 MHz origins: F103 USBPRE vs F407 dedicated PLLQ."""
    f = Fig("ch14-usbpre-48",
            "USB 48 MHz：两个分母，两种来路",
            title_color=BLUE_D, tag="CH 35 · USB")
    f.text(64, 126,
           "全速 USB 的时钟要求是死的 48 MHz；F103 与 F407 的来路完全不同，错了主机直接不认。",
           size=19, color=MUTED)

    # ---- F103 path ----
    f.card(64, 156, 500, 330, BLUE_D, fill=BLUE_FILL)
    f.text(84, 188, "F103：PLL 出来再分 1.5", size=17, color=BLUE_D,
           weight="bold")
    f.pill(84, 206, 200, 40, "PLL 72 MHz", BLUE_D, fill=WHITE, size=15.5,
           text_color=INK)
    f.arrow(294, 226, 330, 226, color=MUTED, sw=2.2, bend=0.0, head=8)
    f.pill(330, 206, 210, 40, "USBPRE=0 ÷1.5", GREEN_D, fill=WHITE,
           size=15.5, text_color=INK)
    f.arrow(540, 226, 470, 268, color=GREEN_D, sw=2.4, bend=0.0, head=9)
    f.metric(96, 330, "48 MHz", "USBCLK，全速要求", GREEN_D)
    f.text(84, 380, "USBPRE=1：72 MHz 直进——枚举必败，", size=14.5,
           color=RED, weight="bold")
    f.text(84, 406, "主机报「未知设备」", size=14.5, color=RED, weight="bold")
    f.text(84, 442, "先量 USBCLK 再怪 CDC 代码", size=14, color=MUTED)
    f.text(84, 466, "D+ 的 1.5 kΩ 上拉在 PA12（pin33）", size=14,
           color=MUTED)

    # ---- F407 path ----
    f.card(588, 156, 500, 330, GREEN_D, fill=GREEN_FILL)
    f.text(608, 188, "F407：OTG_FS 专用线", size=17, color=GREEN_D,
           weight="bold")
    f.pill(608, 206, 220, 40, "PLLN 336 ÷ PLLQ 7", GREEN_D, fill=WHITE,
           size=15, text_color=INK)
    f.arrow(718, 246, 780, 268, color=GREEN_D, sw=2.4, bend=0.0, head=9)
    f.metric(620, 330, "48 MHz", "PLL48CLK 专用档", GREEN_D)
    f.text(608, 380, "不随 SYSCLK 走：168 MHz 主频下", size=14.5, color=INK)
    f.text(608, 406, "USB 仍是独立的 48 MHz 档", size=14.5, color=INK)
    f.text(608, 442, "8M HSE × 336 ÷ 7 = 48", size=14, color=MUTED,
           font=MONO)
    f.text(608, 466, "与时钟树解耦，换主频不动 USB", size=14, color=MUTED)

    # ---- strip ----
    f.panel(64, 516, 1024, 84, GRAY_FILL, amp=1.6)
    f.rect(64, 516, 1024, 84, color=MUTED, sw=1.6, fill=None, amp=1.6)
    f.text(88, 548, "两个分母一个要求：72÷1.5 与 336÷7 都恰好 48——偏差一点，主机读描述符就失败",
           size=15, color=INK, weight="bold")
    f.text(88, 578, "排障顺序：量 48 MHz → 看 USBPRE/PLLQ → 再谈 CDC 描述符代码",
           size=14, color=MUTED)

    f.htext(64, 700, "48 MHz 是「未知设备」问题的第一嫌疑人，代码是最后一位",
            size=21, color=INK, weight="bold", hl=True)
    f.text(576, 730,
           "来路取自本章 RM0008 §23 / RM0090 §30 与数据手册口径；结构示意。",
           size=14, color=MUTED, anchor="middle")
    return f


def ch00_three_api_lanes():
    """Three abstraction heights; unified caliber from ch46."""
    f = Fig("ch00-three-api-lanes",
            "同一外设，三种抽象高度",
            title_color=BLUE_D, tag="CH 46 · 路线")
    f.text(64, 126,
           "寄存器、SPL、HAL 是同一条总线的三种写法；差别是 abstraction 高度与成本。",
           size=19, color=MUTED)

    # ---- three lanes as stacked blocks ----
    lanes = [
        ("寄存器", 12, BLUE_D, BLUE_FILL, "最厚：每一步都看得见"),
        ("SPL", 7, BLUE_D, BLUE_FILL, "居中：旧 F1 工程的读法"),
        ("HAL", 4, GREEN_D, GREEN_FILL, "最薄：生态与移植的通行证"),
    ]
    for i, (name, blocks, c, fl, note) in enumerate(lanes):
        x = 140 + i * 330
        base = 500
        bh = 22
        for b in range(blocks):
            y = base - b * (bh + 4)
            f.rect(x, y - bh, 180, bh, color=c, fill=fl, sw=1.8,
                   double=False, amp=1.2)
        f.text(x + 90, 644, name, size=19, color=c, anchor="middle",
               weight="bold")
        f.text(x + 90, 668, note, size=13.5, color=MUTED, anchor="middle")

    f.pill(700, 148, 386, 72, "本书口径：寄存器打底 + HAL 做产品",
           AMBER_STROKE, fill=AMBER_PALE, size=16)

    # ---- rules ----
    f.panel(64, 516, 1024, 96, RED_FILL, amp=1.6)
    f.rect(64, 516, 1024, 96, color=RED, sw=1.8, fill=None, amp=1.6)
    f.text(88, 548, "第一周只走一条车道：混开是坑", size=15.5, color=RED,
           weight="bold")
    f.text(88, 578, "同一外设别又写寄存器又调库——初始化双份，谁覆盖谁说不清（附录 B 的工程纪律同源）",
           size=14, color=INK)

    f.htext(64, 700, "高度可以换，一层一层换；同周期混开三条车道必乱",
            size=21, color=INK, weight="bold", hl=True)
    f.text(576, 730,
           "口径取自第 46 章统一声明；厚度示意，不按代码行数比例。",
           size=14, color=MUTED, anchor="middle")
    return f


FIGS = {
    "ch13-can-bit": ch13_can_bit,
    "ch13-bit-quanta": ch13_bit_quanta,
    "ch13-filter-fifo": ch13_filter_fifo,
    "ch14-usb-enum": ch14_usb_enum,
    "ch14-usbpre-48": ch14_usbpre_48,
    "ch00-three-api-lanes": ch00_three_api_lanes,
}


if __name__ == "__main__":
    import sys

    STAGE.mkdir(parents=True, exist_ok=True)
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        f = FIGS[n]()
        save(f, str(STAGE / (n + ".svg")))
        print("wrote", STAGE / (n + ".svg"))

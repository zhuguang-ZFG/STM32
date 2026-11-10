# -*- coding: utf-8 -*-
"""Six reproducible chapter-16 plates: wake paths, current conditions, triage,
Stop/UART branches, retained state and a GPIO/bit-width experiment.

DS5319 Rev 20 supplies the conditional current and first-instruction timings;
RM0008 Rev 21 and Arm DUI0552A supply clock, EXTI, reset and WFI/WFE behavior.
These are mechanism illustrations, never board measurements.
"""
from hd import *


def wake_matrix():
    f = Fig("ch16-wake-matrix", "醒来后，是接着跑，还是重新启动？")
    f.text(72, 143, "模式", size=21, color=MUTED)
    f.text(270, 143, "退出条件（STM32F103）", size=21, color=MUTED)
    f.text(758, 143, "退出后的程序", size=21, color=MUTED)
    rows = [
        ("Sleep", GREEN_D,
         ["WFI：满足 NVIC 与优先级条件的中断", "WFE：已配置的事件"],
         ["沿用睡前时钟", "退出等待后继续"], "1.8 µs"),
        ("Stop", BLUE_D,
         ["WFI：EXTI 中断 + NVIC 使能", "WFE：EXTI 事件；RTC 闹钟走 EXTI17"],
         ["先用 HSI 8 MHz", "本书再恢复 72 MHz"], "5.4 µs · LP 稳压器"),
        ("Standby", RED,
         ["WKUP：第 10 脚 PA0 上升沿；RTC 闹钟", "NRST、IWDG 复位也能退出"],
         ["从复位向量重启", "普通 SRAM 不保留"], "50 µs"),
    ]
    for i, (name, color, sources, result, timing) in enumerate(rows):
        y = 164 + i * 146
        f.panel(60, y, 1032, 128, WHITE)
        f.rect(60, y, 1032, 128, color=color, sw=2.4)
        f.text(80, y + 51, name, size=28, color=color, weight="bold")
        f.multi(270, y + 38, sources, size=20, color=INK, lh=32)
        f.arrow(690, y + 51, 735, y + 51, color=color)
        f.multi(758, y + 38, result, size=21, color=color, lh=32)
        f.text(270, y + 105, "事件至第一条指令：" + timing, size=19, color=MUTED)
    f.text(72, 648, "先配唤醒源，再进入低功耗。", size=24, color=INK, weight="bold")
    f.multi(72, 686, [
        "Stop 的 EXTI 可以选下降沿；Standby 的 WKUP 固定认上升沿。",
        "IWDG 超时是复位，不能当作 Stop 的普通返回。",
        "时间为 DS5319 表 26 的典型值；不含 PLL 恢复与后续业务。",
    ], size=21, color=MUTED, lh=32)
    return f


def mode_current():
    f = Fig("ch16-mode-current", "电流差多少，先把单位和条件放在一起")
    f.text(72, 142, "DS5319 表 16 · 3.3 V、25°C 典型值 · 非板上实测", size=21, color=MUTED)
    # 真正的对数刻度：14400 / 14 / 2 µA，避免用任意柱高暗示比例。
    x0, x1, y = 118, 1026, 250
    pos = lambda ua: x0 + math.log10(ua) / 5 * (x1 - x0)
    f.line(x0, y, x1, y, color=INK)
    for ua, label in [(1, "1 µA"), (10, "10 µA"), (100, "100 µA"), (1000, "1 mA"), (10000, "10 mA"), (100000, "100 mA")]:
        x = pos(ua)
        f.line(x, y - 7, x, y + 7, color=MUTED, sw=1.8)
        f.text(x, y + 35, label, size=18, color=MUTED, anchor="middle")
    for ua, name, color in [(2, "Standby 2 µA", BLUE_D), (14, "Stop 14 µA", GREEN_D), (14400, "Sleep 14.4 mA", AMBER_STROKE)]:
        x = pos(ua)
        f.circle(x, y, 7, color=color, fill=color)
        label_y = y - 42 if ua == 14 else y - 74
        f.line(x, y - 12, x, label_y + 12, color=color)
        f.text(x, label_y, name, size=22, color=color, anchor="middle", weight="bold")
    f.text(576, 332, "对数刻度：相邻刻度差 10 倍", size=20, color=MUTED, anchor="middle")
    cells = [
        (60, 374, "Sleep · 72 MHz", AMBER_STROKE, ["外设全开 14.4 mA", "外设全关 5.5 mA"]),
        (590, 374, "Stop · 无 IWDG", GREEN_D, ["低功耗稳压器 14 µA", "主稳压器 24 µA"]),
        (60, 568, "Standby", BLUE_D, ["LSI / IWDG / LSE / RTC 全关：2 µA", "LSI 开：3.2 µA；加 IWDG：3.4 µA"]),
        (590, 568, "VBAT 备份域", RED, ["LSE 与 RTC 开：1.4 µA", "测量边界不同，不能当成整机 Standby"]),
    ]
    for x, yy, title, color, lines in cells:
        f.rect(x, yy, 502, 164, color=color, fill=WHITE)
        f.text(x + 22, yy + 42, title, size=25, color=color, weight="bold")
        f.multi(x + 22, yy + 82, lines, size=20, color=INK, lh=34)
    return f


def pwr_triage():
    f = Fig("ch16-pwr-triage", "低功耗不对劲，先分清是哪一种现象")
    cases = [
        ("01", "没有真正进入 Stop", RED,
         ["读回 SLEEPDEEP=1、PDDS=0", "查 EXTI / 外设 / RTC 是否仍有挂起标志"],
         ["先排除刚睡就醒", "LPDS 选择稳压器；两位模式位不保证 14 µA"]),
        ("02", "醒来后 UART 乱码", BLUE_D,
         ["查 SYSCLK 是否仍是 HSI 8 MHz", "同一个 BRR 0x271：12800 ≠ 115200"],
         ["恢复本书的 72 MHz 时钟树", "在恢复完成之后，再发送 0x55 检查位宽"]),
        ("03", "能睡能醒，电流仍高", GREEN_D,
         ["区分 MCU 电源支路与整板输入电流", "核对 IWDG / LSI / LSE / RTC 和稳压器条件"],
         ["逐项断开 LED、调试器和外设", "记录差值；同时查引脚反向供电与 LDO 静态电流"]),
    ]
    for i, (num, title, color, checks, nexts) in enumerate(cases):
        y = 150 + i * 204
        f.rect(60, y, 1032, 182, color=color, fill=WHITE)
        f.text(82, y + 44, num, size=30, color=color, weight="bold")
        f.text(150, y + 44, title, size=27, color=color, weight="bold")
        f.multi(82, y + 87, checks, size=20, color=INK, lh=31)
        f.arrow(82, y + 140, 130, y + 140, color=color)
        f.text(150, y + 144, nexts[0], size=21, color=color, weight="bold")
        f.text(150, y + 170, nexts[1], size=18, color=MUTED)
    return f


def stop_wake():
    f = Fig("ch16-stop-wake", "Stop 醒来后，串口为何慢了 9 倍？")
    f.text(72, 144, "STM32F103C8T6 · USART1 · PPRE2 不分频 · BRR 始终为 0x271", size=21, color=MUTED)
    f.rect(72, 174, 1008, 120, color=GREEN_D, fill=WHITE)
    f.text(96, 213, "Stop：SLEEPDEEP=1、PDDS=0；LPDS=1 选低功耗稳压器", size=24, color=GREEN_D)
    f.text(96, 253, "14 µA：3.3 V、25°C 典型值，振荡器关、无 IWDG（DS5319 表 16）", size=21, color=INK)
    f.arrow(576, 300, 576, 336, color=BLUE_D)
    f.rect(292, 344, 568, 108, color=BLUE_D, fill=WHITE)
    f.text(576, 382, "EXTI 唤醒 → 第一条指令用 HSI 8 MHz", size=24, color=BLUE_D, anchor="middle")
    f.text(576, 420, "5.4 µs：事件到首条指令，非 HSI 运行时长", size=20, color=MUTED, anchor="middle")
    f.arrow(460, 460, 318, 506, color=GREEN_D)
    f.arrow(692, 460, 834, 506, color=RED)
    f.rect(72, 516, 480, 190, color=GREEN_D, fill=WHITE)
    f.rect(600, 516, 480, 190, color=RED, fill=WHITE)
    f.text(96, 555, "恢复本书的 72 MHz 时钟树", size=25, color=GREEN_D, weight="bold")
    f.text(624, 555, "跳过时钟恢复，仍用 8 MHz", size=25, color=RED, weight="bold")
    f.text(96, 599, "72 MHz ÷ 625 = 115200 bit/s", size=24, color=INK)
    f.text(624, 599, "8 MHz ÷ 625 = 12800 bit/s", size=24, color=INK)
    f.text(96, 649, "主机仍设 115200：位宽匹配", size=22, color=GREEN_D)
    f.text(624, 649, "主机仍设 115200：收到乱码", size=22, color=RED)
    f.text(96, 683, "HSE 起振、PLL 锁定后再发下一字节", size=19, color=MUTED)
    f.text(624, 683, "115200 / 12800 = 9；帧格式未改变", size=19, color=MUTED)
    f.text(576, 754, "PLL 锁定最大 200 µs；它与 5.4 µs 是不同指标。", size=22, color=MUTED, anchor="middle")
    return f


def stop_compare():
    f = Fig("ch16-stop-compare", "省电之外，还要选醒来后保留什么")
    f.text(72, 143, "STM32F103 · 系统时钟与普通 SRAM / 寄存器的去向", size=22, color=MUTED)
    rows = [
        (GREEN_D, "Sleep", "内核时钟暂停", ["系统时钟继续", "外设按配置运行"], "普通 SRAM / 寄存器保持", "继续原程序", "SLEEPDEEP=0"),
        (BLUE_D, "Stop", "HSI / HSE / PLL 关", ["唤醒先用 HSI 8 MHz", "本书随后恢复 72 MHz"], "普通 SRAM / 寄存器保持", "继续原程序", "SLEEPDEEP=1 · PDDS=0"),
        (RED, "Standby", "1.8 V 电源域关闭", ["退出后走复位启动", "重新初始化业务状态"], "普通 SRAM 丢失；备份域保留", "从复位向量重启", "SLEEPDEEP=1 · PDDS=1"),
    ]
    for i, (color, name, title, lines, state, dest, regs) in enumerate(rows):
        y = 171 + i * 188
        f.rect(60, y, 1032, 166, color=color, fill=WHITE)
        f.text(82, y + 43, name, size=31, color=color, weight="bold")
        f.text(82, y + 83, regs, size=17, color=MUTED)
        f.text(340, y + 43, title, size=24, color=INK, weight="bold")
        f.multi(340, y + 80, lines, size=20, color=MUTED, lh=31)
        f.arrow(664, y + 75, 714, y + 75, color=color)
        f.text(742, y + 48, dest, size=25, color=color, weight="bold")
        f.text(742, y + 91, state.split("；")[0], size=20, color=INK)
        if "；" in state:
            f.text(742, y + 124, state.split("；")[1], size=20, color=INK)
    f.text(576, 766, "Stop / Standby 的 RTC、LSI、LSE 是否运行，仍取决于各自配置。", size=21, color=MUTED, anchor="middle")
    return f


def clock_restore():
    f = Fig("ch16-clock-restore", "恢复时钟，用 GPIO 标记与位宽来核对")
    f.text(72, 143, "PA0 边沿 → ISR 标记 A → 时钟恢复 → 标记 B → UART 0x55", size=23, color=INK)
    steps = [(124, "PA0", "唤醒边沿", BLUE_D), (414, "标记 A", "ISR 入口", BLUE_D),
             (704, "标记 B", "72 MHz 已恢复", GREEN_D), (994, "USART1", "开始发送", GREEN_D)]
    for i, (x, title, note, color) in enumerate(steps):
        f.circle(x, 219, 9, color=color, fill=WHITE)
        f.text(x, 190, title, size=24, color=color, anchor="middle", weight="bold")
        f.text(x, 260, note, size=21, color=INK, anchor="middle")
        if i < len(steps) - 1:
            f.arrow(x + 15, 219, steps[i + 1][0] - 15, 219, color=color)
    f.text(576, 309, "A 包含中断入口延迟；A→B 含时钟配置。上方间距不代表耗时。", size=20, color=MUTED, anchor="middle")
    f.line(72, 340, 1080, 340, color=MUTED, sw=1.2)
    f.text(72, 386, "同一时间尺下的单个位宽（理论值，非仪器截图）", size=24, color=INK, weight="bold")
    x0, scale = 350, 7.8
    for y, rate, us, clock, color in [(466, "115200 bit/s", 1e6 / 115200, "恢复后：72 MHz", GREEN_D),
                                      (604, "12800 bit/s", 1e6 / 12800, "未恢复：HSI 8 MHz", RED)]:
        f.text(72, y - 3, rate, size=24, color=color, weight="bold")
        f.text(72, y + 30, clock, size=20, color=MUTED)
        end = x0 + us * scale
        f.stroke([(x0 - 32, y - 32), (x0, y - 32), (x0, y + 14), (end, y + 14), (end, y - 32), (1040, y - 32)], color=color)
        f.text((x0 + end) / 2, y + 51, f"{us:.3f} µs", size=20, color=color, anchor="middle")
    f.line(x0, 699, 1052, 699, color=MUTED, sw=1.4)
    for us in (0, 10, 30, 50, 70, 90):
        x = x0 + us * scale
        f.line(x, 693, x, 705, color=MUTED, sw=1.3)
        f.text(x, 731, str(us), size=18, color=MUTED, anchor="middle")
    f.text(1052, 762, "时间 / µs", size=19, color=MUTED, anchor="end")
    f.text(72, 762, "USART1：PPRE2 不分频，BRR 保持 0x271", size=20, color=MUTED)
    return f


def pvd_window():
    f = Fig("ch16-pvd-window", "PVD：掉电前的最后一声")
    f.text(84, 140, "PVD 监视 VDD（STM32F103）· 例程选 PWR_PVDLEVEL_6 档 · 别把档位背成毫伏数，电压与迟滞以 RM 为准",
           size=19, color=MUTED)

    # ---- 三条参考线（相对位置，非毫伏值）----
    f.line(100, 256, 1064, 256, color=MUTED, sw=2.0, dash="7 7", opacity=0.8)
    f.text(1060, 246, "门槛 + 迟滞：回升再报（RM 为准）", size=17, color=MUTED,
           anchor="end")
    f.line(100, 300, 1064, 300, color=BLUE_D, sw=2.2, dash="7 7")
    f.text(1060, 288, "所选门槛：具体电压见 RM", size=17, color=BLUE_D,
           anchor="end")
    f.line(100, 520, 1064, 520, color=RED, sw=2.2, dash="7 7")
    f.text(1060, 546, "最低工作电压：低于它，写入不再有保证", size=18,
           color=RED, anchor="end")

    # ---- 抢救窗口：斜线阴影 ----
    for i in range(8):
        x0 = 436 + i * 18
        f.line(x0, 500, x0 + 24, 324, color=MUTED, sw=2.2, amp=0.8,
               opacity=0.3)
    f.text(514, 402, "② 抢救窗口", size=22, color=AMBER_STROKE,
           anchor="middle", weight="bold")

    # ---- VDD 下落曲线 ----
    curve = [(100, 190), (300, 184), (380, 200), (430, 300), (475, 392),
             (520, 454), (560, 502), (600, 520), (648, 560)]
    f.stroke(curve, color=BLUE_D, sw=3.2, amp=1.2)
    f.arrowhead(648, 560, 48, 40, color=BLUE_D, head=12)
    f.text(104, 176, "VDD", size=20, color=BLUE_D, weight="bold")

    # ---- 两个事件点 ----
    f.circle(430, 300, 7, color=RED, fill=RED)
    f.text(446, 294, "①", size=24, color=RED, weight="bold")
    f.circle(600, 520, 7, color=RED, fill=RED)
    f.text(616, 506, "③", size=24, color=RED, weight="bold")

    # ---- 底：三段说明 ----
    f.rect(84, 588, 300, 124, color=GREEN_D, fill=WHITE, sw=2.4)
    f.text(100, 620, "① 下穿门槛：报警", size=20, color=GREEN_D, weight="bold")
    f.multi(100, 650, ["配好 EXTI16 与 NVIC；", "IT_RISING_FALLING：",
                       "下穿、回升都报"], size=17, color=INK, lh=23)
    f.rect(424, 588, 300, 124, color=AMBER_STROKE, fill=WHITE, sw=2.4)
    f.text(440, 620, "② 抢救窗口：只做保存", size=20, color=AMBER_STROKE,
           weight="bold")
    f.multi(440, 650, ["把关键数据写进备份域或闪存", "能写多久看：供电余量、",
                       "写入时间、最低工作电压"], size=17, color=INK, lh=23)
    f.rect(764, 588, 300, 124, color=RED, fill=WHITE, sw=2.4)
    f.text(780, 620, "③ PVD 不承诺的事", size=20, color=RED, weight="bold")
    f.multi(780, 650, ["没有固定的剩余毫秒数；", "它是掉电通知，",
                       "不是备用电池"], size=17, color=INK, lh=23)
    f.htext(576, 748, "门槛一穿就喊；还剩多少毫秒，PVD 不说，余量自己留",
            size=24, color=INK, weight="bold", anchor="middle", hl=True)
    return f


def no_ammeter_check():
    f = Fig("ch16-no-ammeter-check",
            "没有电流表，先这样证明唤醒是对的 / prove wakeup without an ammeter")
    f.text(84, 130, "逻辑分析仪四路：PA0 下降沿、两个 GPIO 标记、TX；先对顺序，再对位宽",
           size=20, color=MUTED)

    # timeline lanes
    lanes = [
        ("PA0 EXTI 下降沿", "唤醒源", BLUE_D, 210),
        ("GPIO① ISR 入口翻转", "中断入口+软件延迟 ≠ 手册 5.4 µs", GREEN_D, 300),
        ("GPIO② 时钟恢复后翻转", "分开「醒来」和「重配完成」两个阶段", GREEN_D, 390),
        ("TX 发 0x55", "位宽是判决量", AMBER_STROKE, 480),
    ]
    for name, note, c, y in lanes:
        f.text(84, y + 24, name, size=18, color=c, weight="bold")
        f.text(400, y + 24, note, size=15, color=MUTED)
        f.line(84, y + 40, 1068, y + 40, color=c, sw=1.8, amp=0.5)

    # edge markers on lanes
    f.line(300, 210, 300, 480, color=RED, sw=2.2, amp=0.4)
    f.text(300, 198, "唤醒事件", size=14, color=RED, anchor="middle")
    f.line(560, 300, 560, 480, color=RED, sw=2.2, amp=0.4)
    f.text(560, 288, "①", size=16, color=RED, anchor="middle", weight="bold")
    f.line(760, 390, 760, 480, color=RED, sw=2.2, amp=0.4)
    f.text(760, 378, "②", size=16, color=RED, anchor="middle", weight="bold")

    # verdict boxes
    f.rect(84, 540, 470, 128, color=GREEN_D, fill=WHITE, sw=2.4)
    f.text(319, 576, "位宽 ≈ 8.68 µs", size=21, color=GREEN_D, anchor="middle",
           weight="bold")
    f.text(319, 612, "72 MHz 已恢复，USART1 = 115200 ✓", size=16, color=INK,
           anchor="middle")
    f.rect(598, 540, 470, 128, color=RED, fill=WHITE, sw=2.4)
    f.text(833, 576, "位宽 = 78.125 µs", size=21, color=RED, anchor="middle",
           weight="bold")
    f.text(833, 612, "时钟停在 HSI 8 MHz：0x271 → 12800；先 SystemClock_Config()",
           size=15, color=INK, anchor="middle")

    f.text(W / 2, 712, "顺序与位宽都对上之后，再接电流仪测完整周期",
           size=18, color=INK, anchor="middle")
    return f


def cell_triage():
    f = Fig("ch16-cell-triage",
            "引用电流格子前，先问三句 / three questions before citing a cell")
    f.text(84, 130, "DS5319 表 16 的每格都有前提；条件不同不能混用",
           size=20, color=MUTED)

    qs = [
        ("哪只稳压器？", "低功耗稳压器 14 µA；主稳压器 24 µA；20 µA 不是格子", BLUE_D),
        ("IWDG 开没开？", "14 µA 那格不含 IWDG；IWDG 启动后停不下来，Stop/Standby 都计数", RED),
        ("是不是备份域？", "1.4 µA 是 VBAT 备份域（LSE+RTC），不是整机 Standby", AMBER_STROKE),
        ("Standby 分三格", "2 µA = LSI/IWDG/LSE/RTC 全关；LSI 开 3.2 µA；+IWDG 3.4 µA", GREEN_D),
    ]
    y = 186
    for t, s, c in qs:
        f.rect(84, y, 984, 92, color=c, fill=WHITE, sw=2.4)
        f.text(108, y + 36, t, size=20, color=c, weight="bold")
        f.text(108, y + 70, s, size=17, color=INK)
        y += 108

    f.text(W / 2, 650, "「2~3 µA」「20 µA」这类合并写法，都是把不同前提的格子并成了一格",
           size=18, color=RED, anchor="middle", weight="bold")
    return f


def battery_budget():
    f = Fig("ch16-battery-budget",
            "电池账本：一个周期里谁在花电 / one period, three numbers")
    f.text(84, 128, "占空比 δ = t_active / T 往往远小于 1；平均值按一个完整周期算",
           size=20, color=MUTED)

    # ---- 周期条：醒 + 睡 ----
    y, x0 = 200, 84
    f.text(x0, y - 18, "一个周期 T（概念示意，长度不代表真实比例）", size=17,
           color=MUTED)
    f.rect(x0, y, 300, 78, color=AMBER_STROKE, fill=WHITE, sw=2.4)
    f.text(x0 + 150, y + 32, "t_active：醒着", size=20, color=AMBER_STROKE,
           anchor="middle", weight="bold")
    f.text(x0 + 150, y + 60, "I_active：内核 + 外设都在要电", size=16,
           color=INK, anchor="middle")
    f.rect(x0 + 300, y, 684, 78, color=GREEN_D, fill=WHITE, sw=2.4)
    f.text(x0 + 642, y + 32, "T − t_active：睡着", size=20, color=GREEN_D,
           anchor="middle", weight="bold")
    f.text(x0 + 642, y + 60, "I_sleep：Stop / Standby 的电流地板", size=16,
           color=INK, anchor="middle")

    # ---- 公式带 ----
    f.rect(84, 318, 984, 92, color=BLUE_D, fill=WHITE, sw=2.4)
    f.text(108, 352, "I_avg = ( I_active × t_active + I_sleep × (T − t_active) ) ÷ T",
           size=21, color=BLUE_D, weight="bold")
    f.text(108, 390, "续航 h ≈ 电池容量 (mAh) ÷ I_avg (mA)；先把一个周期画出来，再谈省电",
           size=17, color=INK)

    # ---- 两栏：地板不是全部 / 常驻漏电 ----
    f.rect(84, 446, 470, 208, color=RED, fill=WHITE, sw=2.4)
    f.text(104, 480, "地板单独决定不了续航", size=21, color=RED, weight="bold")
    f.multi(104, 514, [
        "Stop 地板再低，也挡不住",
        "醒着那一段把电荷吃掉：",
        "功耗 = 电流 × 时间，两段都要乘。",
        "「地板 14 µA，所以能撑一年」",
        "是漏掉了 t_active 的账。",
    ], size=17, color=INK, lh=25)

    f.rect(598, 446, 470, 208, color=BLUE_D, fill=WHITE, sw=2.4)
    f.text(618, 480, "常驻漏电也要进账本", size=21, color=BLUE_D, weight="bold")
    f.multi(618, 514, [
        "LDO 静态电流 Iq：典型值 <1 µA，仍要计入",
        "10 kΩ 分压在 3.3 V 上：≈0.33 mA，一直流",
        "分压串 MOS 门：只在采样窗口导通，窗口也算",
        "IWDG 由 LSI 供钟：Stop 里照样计数",
    ], size=17, color=INK, lh=27)

    f.htext(W / 2, 706, "地板回答「睡着有多省」；续航还要问「醒多久、多久醒一次」",
            size=22, color=INK, weight="bold", anchor="middle", hl=True)
    f.text(84, 748, "公式与漏电项取自本章正文；本图是算术示意，不是实测曲线",
           size=16, color=MUTED)
    return f


def wake_ladder():
    f = Fig("ch16-wake-ladder",
            "醒来的时间阶梯：到第一条指令要多久")

    f.text(84, 136, "四种睡法的唤醒代价；阶梯高度只示量级，不按比例",
           size=18, color=MUTED)

    axis_y = 592
    data = [
        ("Sleep", "1.8 µs", "沿用睡前时钟", 132, BLUE),
        ("Stop · 主稳压器", "3.6 µs", "醒来是 HSI 8 MHz", 186, GREEN_D),
        ("Stop · 低功耗稳压器", "5.4 µs", "到第一条指令，仍是 HSI", 240, GREEN_D),
        ("Standby", "50 µs", "从复位向量重启", 340, RED),
    ]
    for i, (name, t, note, h, col) in enumerate(data):
        x = 96 + i * 240
        y = axis_y - h
        f.rect(x, y, 216, h, color=col, fill=WHITE, sw=2.4)
        f.text(x + 108, y + 32, name, size=15.5, color=col, anchor="middle", weight="bold")
        f.text(x + 108, y + 78, t, size=30, color=col, anchor="middle", weight="bold")
        f.text(x + 108, y + h - 16, note, size=13, color=INK, anchor="middle")

    f.line(84, axis_y, 1068, axis_y, color=INK, sw=2.2, amp=0.5)
    for i in range(4):
        cxx = 96 + i * 240 + 108
        f.line(cxx, axis_y - 3, cxx, axis_y + 9, color=INK, sw=1.6, amp=0.2)
    f.text(576, 622, "唤醒事件 → 第一条用户指令（典型值，条件见 DS5319 表 26）",
           size=15, color=MUTED, anchor="middle")

    f.text(576, 668, "PLL 锁定最长 200 µs 是另一项，不和 5.4 µs 相加；恢复 72 MHz 还要 HSE、PLL 与软件配置",
           size=17, color=INK, anchor="middle")

    f.htext(84, 718, "先问「醒来」到哪一步：第一条指令 ≠ 时钟恢复 ≠ 应用就绪",
            size=20, weight="bold")
    f.text(84, 750, "数字取自本章「时序与状态」与 DS5319 Rev 20 表 26；Standby 经复位启动，不是中断返回",
           size=14, color=MUTED)
    return f


def acceptance_record():
    f = Fig("ch16-acceptance-record",
            "低功耗验收的五个格子：一个稳定数字不算数")

    f.text(84, 136, "静态底电流之外，还要把峰值、活跃时间、周期和唤醒原因一起记下来",
           size=18, color=MUTED)

    cells = [
        ("① 静态底电流", ["进 Stop 后的稳定值", "µA 档先算量程压降", "记：读数 + 量程档位"]),
        ("② 唤醒峰值", ["醒来瞬间的电流尖峰", "峰值 × 时间也进平均", "记：采样电阻波形"]),
        ("③ 活跃时长", ["醒来做事持续多久", "含时钟恢复与外设启动", "记：GPIO 标记前后"]),
        ("④ 周期", ["多久醒一次", "周期决定占空比", "记：RTC 闹钟间隔"]),
        ("⑤ 唤醒原因", ["引脚、RTC 还是看门狗", "醒来先读标志", "记：PWR / RCC 标志"]),
    ]
    for i, (head, lines) in enumerate(cells):
        x = 84 + i * 212
        f.rect(x, 196, 196, 236, color=INK, fill=WHITE, sw=2.0, double=False)
        f.text(x + 16, 238, head, size=17, color=INK, weight="bold")
        f.multi(x + 16, 282, lines, size=13.5, color=MUTED, lh=26)

    f.panel(84, 464, 984, 74, "#E7EFE3", amp=1.8)
    f.text(576, 496, "续航只认周期平均：I_avg = Σ(I_k × t_k) / T",
           size=19, color=GREEN_D, anchor="middle", weight="bold")
    f.text(576, 524, "底电流再低，活跃时间一长，平均值照样被抬起来",
           size=14, color=INK, anchor="middle")

    f.panel(84, 556, 984, 74, "#F7DCD8", amp=1.8)
    f.text(576, 588, "电流表发现不了时钟问题：底电流对，串口仍可能是 12800",
           size=19, color=RED, anchor="middle", weight="bold")
    f.text(576, 616, "醒来后的 115200 要用「顺序 + 位宽」单独验证（见本章无电流表检查图）",
           size=14, color=INK, anchor="middle")

    f.htext(84, 700, "五个格子填齐，才叫一次低功耗验收",
            size=20, weight="bold")
    f.text(84, 736, "记录格式见本章「动手实验」第 1 条；本图是验收清单，不是实测数据",
           size=14, color=MUTED)
    return f


def wfi_wfe():
    f = Fig("ch16-wfi-wfe",
            "WFI 与 WFE：一个等中断，一个等事件")

    f.text(84, 136, "本章 F103 是单核；两种等待指令都要先配好唤醒路径，不能只换一条指令",
           size=18, color=MUTED)

    f.rect(84, 168, 476, 330, color=BLUE, fill=WHITE, sw=2.4)
    f.text(110, 208, "WFI：等满足条件的中断", size=21, color=BLUE_D, weight="bold")
    f.multi(110, 250, [
        "中断须 NVIC 使能且过得了当前优先级",
        "PRIMASK 可推迟 ISR，不一定阻止唤醒",
        "Stop 里还要 EXTI 中断与 NVIC 通道使能",
    ], size=16, color=INK, lh=40)

    flow_l = [(110, 118, "中断"), (252, 136, "NVIC 仲裁"), (410, 126, "进 ISR")]
    for bx, bw, name in flow_l:
        f.rect(bx, 372, bw, 78, color=BLUE, fill=WHITE, sw=1.8, double=False)
        f.text(bx + bw / 2, 404, name, size=14, color=INK, anchor="middle", weight="bold")
        f.text(bx + bw / 2, 432, "再返回继续" if name == "进 ISR" else "", size=12.5,
               color=MUTED, anchor="middle")
    for bx, bw, _ in flow_l[:-1]:
        f.arrow(bx + bw + 2, 411, bx + bw + 24, 411, color=BLUE, bend=0.0, head=8)

    f.rect(592, 168, 476, 330, color=GREEN_D, fill=WHITE, sw=2.4)
    f.text(618, 208, "WFE：等事件寄存器", size=21, color=GREEN_D, weight="bold")
    f.multi(618, 250, [
        "事件已为 1：清零并立即返回",
        "SEVONPEND 可让挂起中断产生事件",
        "事件只记「发生过」，不是可累计队列",
    ], size=16, color=INK, lh=40)

    flow_r = [(618, 112, "事件"), (760, 136, "事件寄存器"), (926, 118, "直接返回")]
    for bx, bw, name in flow_r:
        f.rect(bx, 372, bw, 78, color=GREEN_D, fill=WHITE, sw=1.8, double=False)
        f.text(bx + bw / 2, 404, name, size=14, color=INK, anchor="middle", weight="bold")
        f.text(bx + bw / 2, 432, "未必进 ISR" if name == "直接返回" else "", size=12.5,
               color=MUTED, anchor="middle")
    for bx, bw, _ in flow_r[:-1]:
        f.arrow(bx + bw + 2, 411, bx + bw + 24, 411, color=GREEN_D, bend=0.0, head=8)

    f.panel(84, 528, 984, 84, "#FBEFD3", amp=1.8)
    f.text(576, 560, "共同前提：入睡前清掉旧标志、确认唤醒源仍成立",
           size=19, color=INK, anchor="middle", weight="bold")
    f.text(576, 590, "只换指令不改配置，结果会「刚睡就醒」或「睡下去不醒」",
           size=15, color=MUTED, anchor="middle")

    f.htext(84, 676, "WFI 选中断语义，WFE 选事件语义；先配唤醒路径，再选指令",
            size=20, weight="bold")
    f.text(84, 714, "复位后的睡眠退出条件还受异常屏蔽与当前优先级影响；对照见本章 §2 表与 RM0008 第 5 章",
           size=14, color=MUTED)
    return f


def board_vs_chip():
    f = Fig("ch16-board-vs-chip",
            "整板电流、MCU 支路、芯片格子：µA 指标只在最里面成立")

    f.text(84, 136, "开发板读数是三层叠加的结果；DS5319 表 16 的 µA 只对应最里面那格",
           size=18, color=MUTED)

    f.rect(84, 170, 680, 426, color=INK, fill=WHITE, sw=2.4)
    f.text(108, 204, "整板（USB 供电）", size=18, color=INK, weight="bold")

    loads = ["LDO 静态电流", "板载 LED", "USB / 串口", "传感器"]
    for i, name in enumerate(loads):
        x = 108 + i * 162
        f.rect(x, 218, 150, 44, color=AMBER_STROKE, fill="#FBEFD3", sw=1.8,
               double=False)
        f.text(x + 75, 246, name, size=14, color=INK, anchor="middle")

    f.rect(124, 288, 600, 282, color=BLUE, fill=WHITE, sw=2.2)
    f.text(146, 320, "MCU 支路（3V3）", size=17, color=BLUE_D, weight="bold")
    f.text(146, 346, "含调试器与信号线可能的反向供电", size=13, color=MUTED)

    f.rect(164, 368, 520, 176, color=GREEN_D, fill="#E7EFE3", sw=2.2)
    f.text(184, 400, "芯片 VDD：表 16 的同一格", size=16, color=GREEN_D, weight="bold")
    f.multi(184, 434, [
        "Stop 低功耗稳压器 14 µA：3.3 V、25°C、无 IWDG",
        "主稳压器 24 µA；20 µA 不是表 16 的格子",
        "1.4 µA 是备份域 IDD_VBAT，不是整机",
    ], size=14.5, color=INK, lh=30)

    f.rect(800, 170, 268, 330, color=RED, fill=WHITE, sw=2.4)
    f.text(822, 210, "要让 µA 读数成立", size=19, color=RED, weight="bold")
    f.multi(822, 252, [
        "断开调试器与 SWD 反向供电",
        "断开 LED、USB、传感器负载",
        "只留芯片支路，再对表 16 条件",
        "电压与温度也要同一格",
    ], size=15, color=INK, lh=36)

    f.htext(84, 662, "板子上的 µA 不是芯片的 µA：先隔离负载，再谈指标",
            size=20, weight="bold")
    f.text(84, 700, "条件与格子见本章「原理与适用范围」；整板测量顺序见「动手实验」第 4 条",
           size=14, color=MUTED)
    return f


FIGS = {
    "ch16-battery-budget": battery_budget,
    "ch16-wake-matrix": wake_matrix,
    "ch16-mode-current": mode_current,
    "ch16-pwr-triage": pwr_triage,
    "ch16-stop-wake": stop_wake,
    "ch16-stop-compare": stop_compare,
    "ch16-clock-restore": clock_restore,
    "ch16-pvd-window": pvd_window,
    "ch16-no-ammeter-check": no_ammeter_check,
    "ch16-cell-triage": cell_triage,
    "ch16-wake-ladder": wake_ladder,
    "ch16-acceptance-record": acceptance_record,
    "ch16-wfi-wfe": wfi_wfe,
    "ch16-board-vs-chip": board_vs_chip,
}

if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        f = FIGS[n]()
        OUT.mkdir(parents=True, exist_ok=True)
        save(f, str(OUT / (n + ".svg")))
        print("wrote", OUT / (n + ".svg"))

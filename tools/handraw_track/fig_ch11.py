# -*- coding: utf-8 -*-
"""ch11 knowledge-track figure (facts from docs/11, RM0008 Rev 21 ch.20).

The window watchdog counts 0x7F down to 0x3F on a 36 MHz / prescaler-8 tick
(4096 x 8 / 36e6 = 910.2 us per count, 64 counts = 58.25 ms). With W = 0x50,
feeding while the counter is still above 0x50 resets at once, and so does
letting the counter roll below 0x40: the safe feed zone is [0x40, 0x50].
"""
from hd import *


def wwdg_window():
    f = Fig("ch11-wwdg-window",
            "窗口看门狗：喂早喂晚都复位 / feed too early or too late, both reset")

    f.text(84, 138, "PCLK1 = 36 MHz，预分频 8；每格约 910.2 µs，横轴按计数差等比例",
           size=21, color=MUTED)
    start, window, floor, end = 128, 786, 1010, 1024
    f.rect(start, 182, window - start, 58, color=RED, fill=WHITE, sw=2.4)
    f.rect(window, 182, floor - window, 58, color=GREEN_D, fill=WHITE, sw=2.4)
    f.rect(floor, 182, end - floor, 58, color=RED, fill=RED, sw=2.0)
    f.text(440, 218, "计数 T > W：此时喂狗立刻复位", size=23, color=RED, anchor="middle")
    f.text(898, 218, "允许喂狗", size=22, color=GREEN_D, anchor="middle", weight="bold")
    f.stroke([(start, 258), (end, 258)], color=INK, sw=2.4, amp=0.4)
    for tick in range(65):
        position = start + tick * 14
        f.stroke([(position, 250), (position, 266)], color=INK, sw=1.2, amp=0.2)
    for label, position in (("0x7F", start), ("0x50 = W", window)):
        f.text(position, 302, label, size=20, color=INK, anchor="middle", weight="bold")
    f.stroke([(floor, 267), (floor, 282), (958, 282)], color=INK, sw=1.6, amp=0.2)
    f.text(958, 306, "0x40", size=17, color=INK, anchor="middle")
    f.stroke([(end, 267), (end, 282), (1072, 282)], color=RED, sw=1.6, amp=0.2)
    f.text(1072, 306, "0x3F", size=17, color=RED, anchor="middle")
    f.text(440, 337, "47 拍才到窗口：约 42.78 ms", size=20, color=RED, anchor="middle")
    f.text(898, 337, "再过 17 拍会复位", size=18, color=GREEN_D, anchor="middle")
    f.arrow(898, 368, 128, 368, color=GREEN_D, bend=0.0, head=12)
    f.text(510, 399, "在 T=0x48 重载 0x7F → 回到起点，再数下一轮", size=21,
           color=GREEN_D, anchor="middle", weight="bold")
    f.rect(84, 438, 500, 112, color=BLUE_D, fill=WHITE, sw=2.4)
    f.text(100, 470, "一直不喂：64 拍后复位", size=22, color=BLUE_D, weight="bold")
    f.multi(100, 501, ["4096 × 8 / 36e6 ≈ 910.2 µs/拍",
                       "64 拍 ≈ 58.25 ms；0x40→0x3F 时复位"], size=18, color=INK, lh=29)
    f.rect(612, 438, 480, 112, color=MUTED, fill=WHITE, sw=2.2)
    f.text(628, 470, "IWDG 没有这个喂狗窗口", size=22, color=MUTED, weight="bold")
    f.multi(628, 501, ["IWDG：超时前可重载；早喂不复位",
                       "WWDG：0x40 ≤ T ≤ 0x50 才可重载"], size=18, color=INK, lh=29)
    f.htext(84, 604, "喂狗是重载计数器；成功喂狗后，不会沿原倒计时继续走向复位",
            size=23, color=INK, weight="bold", hl=True)
    f.text(84, 647, "这些时间按给定 PCLK1 复算，不是板上测量值；W 是计数上限，不是时间下限寄存器。",
           size=18, color=MUTED)
    return f


def lsi_drift():
    f = Fig("ch11-lsi-drift",
            "LSI 漂移：标称 1 秒，实际 2/3 ~ 4/3 秒 / LSI drift: the 1 s timeout swings")

    f.text(84, 138, "预分频 64、Reload 624 不变；只有 LSI 在 30 / 40 / 60 kHz 之间漂",
           size=21, color=MUTED)

    # 标称 1 s 竖线：40 kHz 那条的右缘正好落在它上面
    f.stroke([(714, 178), (714, 452)], color=MUTED, sw=1.6, amp=0.6, dash="6 7",
             opacity=0.75)
    f.text(714, 168, "标称 1 s", size=17, color=MUTED, anchor="middle")

    bars = [
        ("LSI = 30 kHz（最小）", 840, BLUE_D, "4/3 s（偏长）", 196, "in"),
        ("LSI = 40 kHz（典型）", 630, GREEN_D, "1 s（标称）", 292, "in"),
        ("LSI = 60 kHz（最大）", 420, RED, "2/3 s（偏短）", 388, "out"),
    ]
    for label, wdt, color, value, y, where in bars:
        f.rect(84, y, wdt, 56, color=color, fill=WHITE, sw=2.4)
        f.text(100, y + 36, label, size=21, color=color, weight="bold")
        if where == "in":
            f.text(84 + wdt - 14, y + 36, value, size=21, color=color,
                   anchor="end", weight="bold")
        else:
            f.text(84 + wdt + 14, y + 36, value, size=21, color=color,
                   weight="bold")

    f.text(84, 480, "条长按超时等比例画：60 kHz 档（2/3 s）恰是 30 kHz 档（4/3 s）的一半",
           size=18, color=MUTED)

    f.rect(84, 508, 480, 116, color=RED, fill=WHITE, sw=2.4)
    f.text(100, 540, "板上会偏短或偏长", size=21, color=RED, weight="bold")
    f.multi(100, 572, ["30 / 40 / 60 kHz 是范围端点，不是单颗实测",
                       "超时留余量，不要卡在标称值上"], size=18, color=INK, lh=28)

    f.rect(596, 508, 468, 116, color=BLUE_D, fill=WHITE, sw=2.4)
    f.text(612, 540, "不变的公式", size=21, color=BLUE_D, weight="bold")
    f.multi(612, 572, ["T = 64 ÷ f_LSI × (Reload + 1)",
                       "40 kHz ÷ 64 → 每秒 625 个数 → 标称 1 s"], size=18,
            color=INK, lh=28)

    f.htext(84, 668, "喂狗节奏别卡在标称 1 s：按 30–60 kHz 的范围留余量",
            size=24, color=INK, weight="bold", hl=True)
    f.text(84, 708, "条长按超时等比例；时间为手册端点复算值，不是板上实测；Reload 始终写 624。",
           size=18, color=MUTED)
    return f


def backup_path():
    """Backup-domain power path, reset boundary and DBP write gate."""
    f = Fig("ch11-backup-path",
            "备份域：VBAT 续电、复位碰不到 / why the calendar survives")

    f.text(84, 126,
           "主程序住主域，RTC 与 BKP 住备份域：供电、复位边界、写门三道关口",
           size=18, color=MUTED)

    # ---- ① 供电：VDD / VBAT 片内切换 ----
    f.text(84, 166, "① 电：两路电源在片内切换", size=20, color=BLUE_D,
           weight="bold")
    f.rect(84, 184, 196, 64, color=BLUE_D, fill=WHITE, sw=2.4)
    f.text(182, 211, "VDD 3.3 V", size=19, color=BLUE_D, anchor="middle",
           weight="bold")
    f.text(182, 237, "主电源", size=14, color=MUTED, anchor="middle")
    f.rect(84, 280, 196, 64, color=AMBER_STROKE, fill=WHITE, sw=2.4)
    f.text(182, 307, "VBAT 第 1 脚", size=18, color=AMBER_STROKE,
           anchor="middle", weight="bold")
    f.text(182, 333, "CR2032 ~3 V", size=14, color=MUTED, anchor="middle")
    f.rect(360, 196, 240, 146, color=GREEN_D, fill=WHITE, sw=2.4)
    f.text(480, 224, "片内电源切换", size=19, color=GREEN_D, anchor="middle",
           weight="bold")
    f.multi(376, 256, ["VDD 在：备份域用 VDD",
                       "VDD 掉：切到 VBAT",
                       "两路都掉：备份域复位"],
            size=15, color=INK, lh=26)
    f.arrow(282, 216, 356, 238, color=BLUE_D, sw=2.4, bend=0.0)
    f.arrow(282, 312, 356, 300, color=AMBER_STROKE, sw=2.4, bend=0.0)

    f.rect(650, 184, 418, 164, color=INK, fill=WHITE, sw=2.6)
    f.text(674, 212, "备份域（VBAT 域）", size=19, color=INK, weight="bold")
    f.multi(674, 244, ["RTC：32 位秒计数器",
                       "BKP_DR1–DR10：10 × 16 位 = 20 字节",
                       "LSE 32.768 kHz（PC14/PC15）"],
            size=16, color=INK, lh=27)
    f.arrow(602, 268, 646, 268, color=GREEN_D, sw=2.6, bend=0.0)

    # ---- ② 复位边界 ----
    f.text(84, 392, "② 复位：系统复位到不了备份域", size=20, color=RED,
           weight="bold")
    f.arrow(120, 524, 582, 524, color=RED, sw=3.2, bend=0.0)
    f.text(120, 498, "系统复位：NRST / IWDG / WWDG / 上电", size=16, color=RED)
    f.text(120, 556, "主域：CPU、RAM、Flash、外设清零重来", size=16, color=INK)
    f.line(604, 462, 604, 586, color=RED, sw=3.6, amp=1.4)
    for i in range(4):
        f.line(604, 470 + i * 30, 622, 456 + i * 30, color=RED, sw=1.6)
    f.text(596, 440, "复位边界", size=14, color=RED, anchor="middle")
    f.rect(650, 462, 418, 124, color=GREEN_D, fill=WHITE, sw=2.4)
    f.text(674, 490, "备份域：这一刀砍不到", size=19, color=GREEN_D,
           weight="bold")
    f.multi(674, 520, ["RTC 秒计数、BKP_DR1–DR10 原样保留",
                       "只有 VDD 与 VBAT 都掉，或 BDRST，才复位备份域"],
            size=15.5, color=INK, lh=26)

    # ---- ③ 写门与首次上电判断 ----
    f.rect(84, 606, 476, 112, color=BLUE_D, fill=WHITE, sw=2.4)
    f.text(100, 636, "写门：DBP 不解锁，写不进", size=19, color=BLUE_D,
           weight="bold")
    f.multi(100, 666, ["先开 PWR 与 BKP 时钟，再置 PWR_CR.DBP = 1",
                       "否则写 BKP_DR 与 RTC 设置不生效"],
            size=15.5, color=INK, lh=26)

    f.rect(584, 606, 484, 112, color=GREEN_D, fill=WHITE, sw=2.4)
    f.text(600, 636, "上电先问：是不是第一次", size=19, color=GREEN_D,
           weight="bold")
    f.multi(600, 666, ["读 BKP_DR1 的 0xA5A5：在 → 直接读时间",
                       "不在 → 设日历，再把 0xA5A5 写回"],
            size=15.5, color=INK, lh=26)

    f.htext(84, 750, "复位后表还在走、程序没了：两件事分属两个域",
            size=21, color=INK, weight="bold", hl=True)
    return f


def bkp_magic():
    f = Fig("ch11-bkp-magic",
            "上电先看那张便签：魔数决定初始化 / magic decides init")
    f.text(84, 128, "BKP_DRx 由 VBAT 供电：主电断了，便签还在；流程只用图前已给的寄存器",
           size=20, color=MUTED)

    # ---- 判定流程 ----
    steps = [
        (200, "上电", "主电恢复", BLUE_D),
        (470, "读 BKP_DR1", "16-bit 读回", BLUE_D),
        (760, "= 0xA5A5 ?", "魔数比对", AMBER_STROKE),
    ]
    y = 180
    for x, t, s, c in steps:
        f.rect(x - 110, y, 220, 92, color=c, fill=WHITE, sw=2.4)
        f.text(x, y + 38, t, size=21, color=c, anchor="middle", weight="bold")
        f.text(x, y + 70, s, size=16, color=MUTED, anchor="middle")
    f.arrow(310, y + 46, 358, y + 46, color=BLUE_D)
    f.arrow(580, y + 46, 648, y + 46, color=AMBER_STROKE)

    # 两条分支
    f.arrow(760, y + 92, 620, y + 150, color=GREEN_D, bend=-0.12)
    f.text(612, y + 126, "是：读日历", size=17, color=GREEN_D,
           anchor="end", weight="bold")
    f.rect(430, y + 150, 330, 92, color=GREEN_D, fill=WHITE, sw=2.4)
    f.text(595, y + 186, "RTC 计时没断", size=20, color=GREEN_D,
           anchor="middle", weight="bold")
    f.text(595, y + 220, "直接读时间，不重设", size=16, color=INK,
           anchor="middle")

    f.arrow(760, y + 92, 900, y + 150, color=RED, bend=0.12)
    f.text(908, y + 126, "否：初始化", size=17, color=RED, weight="bold")
    f.rect(780, y + 150, 300, 124, color=RED, fill=WHITE, sw=2.4)
    f.multi(796, y + 182, ["① 配置日历 / 时钟源", "② 写入 0xA5A5",
                           "③ 下次上电走「是」分支"],
            size=16, color=INK, lh=26)

    # ---- 容量栏 ----
    f.rect(84, 486, 470, 140, color=BLUE_D, fill=WHITE, sw=2.4)
    f.text(104, 520, "F103C8T6", size=20, color=BLUE_D, weight="bold")
    f.multi(104, 556, ["BKP_DR1–DR10，十个 16-bit",
                       "共 20 字节；宽度是 16-bit",
                       "够放魔数与少量校准常数"],
            size=16, color=INK, lh=26)

    f.rect(598, 486, 470, 140, color=AMBER_STROKE, fill=WHITE, sw=2.4)
    f.text(618, 520, "STM32F4", size=20, color=AMBER_STROKE, weight="bold")
    f.multi(618, 556, ["RTC_BKP_DR0–DR19，每个 32-bit",
                       "数量更多、宽度更宽；",
                       "流程不变：读魔数再决定"],
            size=16, color=INK, lh=26)

    f.rect(84, 648, 984, 60, color=MUTED, fill=WHITE, sw=2.0)
    f.text(104, 684, "进备份域之前：先开 PWR / BKP 时钟，再置 PWR_CR.DBP 解锁；魔数只回答「初始化过没有」，走时准不准由时钟源决定",
           size=15, color=INK)
    return f


def rtc_lines():
    f = Fig("ch11-rtc-lines",
            "RTC 一条线、看门狗一条线：四个问题各配第一项证据")

    f.text(84, 136, "先问「哪条线」，再问「哪一格」；复位原因、持久状态和实际时间不能混成一个问题",
           size=19, color=MUTED)

    f.htext(84, 190, "RTC 线：时间还在不在", size=24, color=BLUE_D, weight="bold")
    f.htext(84, 452, "看门狗线：死机之后还剩下什么", size=24, color=RED, weight="bold")

    cards = [
        (84, 208, BLUE, "① 复位后它还在走吗",
         ["证据：读 BKP_DR1 的魔数，再读秒计数",
          "主域复位不清备份域；第 1 脚 VBAT 续电",
          "魔数不对 = 首次上电或备份域掉过电"]),
        (596, 208, BLUE, "② 走得准吗",
         ["LSE 32.768 kHz，PRL = 32767 才是 1 Hz",
          "LSI 漂 30–60 kHz，整数 PRL 得不到稳定 1 Hz",
          "分频比是 (PRL + 1)：PRL 写成 32768 会慢"]),
        (84, 470, RED, "③ 死机能把它拉回来吗",
         ["IWDG：Reload 624 → 典型 1 s，减到 0 复位",
          "LSI 30–60 kHz 时是 4/3 s 到 2/3 s，不是保证值",
          "WWDG：窗口外喂狗也复位，58.25 ms 一程"]),
        (596, 470, RED, "④ 这次重启是谁干的",
         ["启动代码读 RCC_CSR 的 IWDGRSTF / WWDRSTF",
          "持久 boot_id 在备份域里每次自增",
          "LED 重新闪烁只证明重启，不证明来源"]),
    ]
    for x, y, color, head, lines in cards:
        f.rect(x, y, 472, 196, color=color, fill=WHITE, sw=2.4)
        f.text(x + 26, y + 40, head, size=21, color=color, weight="bold")
        f.multi(x + 26, y + 82, lines, size=17, color=INK, lh=31)

    f.htext(84, 712, "复位原因、持久状态、实际时间，缺一个就分不清「重启过」和「重启后还是原样」",
            size=20, weight="bold")
    f.text(84, 750,
           "四个问题分别指向：备份域魔数、LSE 与 PRL、IWDG/WWDG 计数、复位标志与 boot_id；本章实验按这个顺序做",
           size=14, color=MUTED)
    return f


def debug_freeze():
    f = Fig("ch11-debug-freeze",
            "断点停住时，看门狗还在数：调试冻结 IWDG")

    f.text(84, 136, "调试器停的是 CPU；LSI 驱动的 IWDG 不归 CPU 管，除非把它和内核一起冻住",
           size=19, color=MUTED)

    for x, frozen in ((84, False), (596, True)):
        color = GREEN_D if frozen else RED
        f.rect(x, 168, 472, 286, color=color, fill=WHITE, sw=2.4)
        f.text(x + 26, 208, "冻住了 IWDG" if frozen else "没有冻住 IWDG",
               size=22, color=color, weight="bold")

        ty = 292
        x0, x1 = x + 30, x + 442
        f.line(x0, ty, x1, ty, color=INK, sw=2.2, amp=0.5)
        for i in range(9):
            tx = x0 + i * (x1 - x0) / 8
            f.line(tx, ty, tx, ty + 12, color=INK, sw=1.4, amp=0.2)

        xb = x0 + 132
        f.stroke([(xb, ty - 54), (xb, ty - 14)], color=RED, sw=2.4,
                 amp=0.6, dash="7 6")
        f.text(xb, ty - 62, "断点", size=17, color=RED, anchor="middle", weight="bold")

        span = 196
        fill = "#DDEBD9" if frozen else "#F7DCD8"
        f.panel(xb + 8, ty - 40, span, 74, fill, amp=1.6)
        f.text(xb + 8 + span / 2, ty + 2,
               "计数冻住" if frozen else "LSI 继续数",
               size=19, color=color, anchor="middle", weight="bold")

        if frozen:
            f.arrow(xb + 8 + span, ty + 34, x1 - 10, ty + 34, color=GREEN_D, bend=0.0)
            f.text(x1, ty + 70, "恢复运行，从同一计数继续", size=16,
                   color=GREEN_D, anchor="end")
        else:
            f.arrow(xb + 8 + span, ty + 34, x1 - 10, ty + 34, color=RED, bend=0.0)
            f.text(x1, ty + 70, "减到 0 → 复位", size=17,
                   color=RED, anchor="end", weight="bold")

        f.text(x + 26, 428,
               "DBGMCU->CR 的 DBG_IWDG_STOP = 1" if frozen
               else "LSI 不受内核停机影响，计数照减",
               size=16, color=INK)

    cards = [
        (84, "一次启动，只有复位能停",
         ["HAL_IWDG_Init 成功后立即运行",
          "软件没有 stop；只能等复位",
          "WDG_SW = 0 时上电即硬件启动"]),
        (436, "F1 / F4 冻结寄存器不同",
         ["F1 写 DBGMCU->CR；F4 写 APB1FZ",
          "__HAL_DBGMCU_FREEZE_IWDG()",
          "WWDG 有同样的冻结位"]),
        (788, "冻住只是调试手段",
         ["手册只印位名 DBG_IWDG_STOP",
          "没给位号；用法见 §19.3.3",
          "脱离调试器后照常计数",
          "不能当成产品的看门狗策略"]),
    ]
    for x, head, lines in cards:
        f.rect(x, 486, 316, 150, color=INK, fill=WHITE, sw=2.0, double=False)
        f.text(x + 20, 519, head, size=17, color=INK, weight="bold")
        f.multi(x + 20, 550, lines, size=14, color=INK, lh=21)

    f.htext(84, 700, "冻住计数器是为了单步安全；产品里该复位的时候还是要它复位",
            size=20, weight="bold")
    f.text(84, 738,
           "顺序：删断点排查前先确认板子不是被 IWDG 复位；用法见上一张「四个问题」的 ③ 和 ④",
           size=14, color=MUTED)
    return f


FIGS = {
    "ch11-bkp-magic": bkp_magic,
    "ch11-wwdg-window": wwdg_window,
    "ch11-lsi-drift": lsi_drift,
    "ch11-backup-path": backup_path,
    "ch11-rtc-lines": rtc_lines,
    "ch11-debug-freeze": debug_freeze,
}

if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        f = FIGS[n]()
        OUT.mkdir(parents=True, exist_ok=True)
        save(f, str(OUT / (n + ".svg")))
        print("wrote", OUT / (n + ".svg"))

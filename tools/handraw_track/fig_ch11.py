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


FIGS = {
    "ch11-wwdg-window": wwdg_window,
    "ch11-lsi-drift": lsi_drift,
    "ch11-backup-path": backup_path,
}

if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        f = FIGS[n]()
        OUT.mkdir(parents=True, exist_ok=True)
        save(f, str(OUT / (n + ".svg")))
        print("wrote", OUT / (n + ".svg"))

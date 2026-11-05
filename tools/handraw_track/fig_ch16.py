# -*- coding: utf-8 -*-
"""ch16 knowledge-track figure: which wake sources each low-power mode accepts.

Facts from docs/16: Sleep resumes the pre-sleep clock at 1.8 us, Stop restarts on
the 8 MHz HSI at 5.4 us, Standby goes through the reset vector at 50 us; WKUP is
the rising edge on pin 10 PA0, and a falling-edge EXTI wakes Stop but not Standby.
"""
from hd import *


def wake_matrix():
    f = Fig("ch16-wake-matrix", "三种睡法，叫醒的方式不一样 / what can wake you")

    cols = [("醒后时钟", 470), ("到第一条指令", 640), ("能唤醒", 830), ("叫不醒", 1035)]
    for label, cx in cols:
        f.text(cx, 146, label, size=21, color=MUTED, anchor="middle")

    rows = [
        ("Sleep", GREEN_D, "沿用睡前时钟", "1.8 µs",
         "任意中断", "—"),
        ("Stop", BLUE_D, "HSI 8 MHz", "5.4 µs",
         "EXTI 边沿（含下降沿）· RTC", "普通中断"),
        ("Standby", RED, "走复位向量", "50 µs",
         "WKUP 第 10 脚上升沿 · RTC", "下降沿 EXTI"),
    ]

    y = 168
    for name, color, clock, t, can, cannot in rows:
        f.panel(60, y, 1032, 104, WHITE)
        f.rect(60, y, 1032, 104, color=color, sw=2.4, fill=None)
        f.rect(60, y, 214, 104, color=color, sw=2.4, fill=WHITE)
        f.text(167, y + 64, name, size=28, color=color, anchor="middle",
               weight="bold")
        f.text(470, y + 44, clock, size=20, color=INK, anchor="middle")
        f.text(640, y + 46, t, size=24, color=color, anchor="middle",
               weight="bold")
        f.multi(726, y + 34, [can[i:i + 13] for i in (0, 13) if can[i:i + 13]],
                size=18, color=INK, lh=26)
        f.multi(948, y + 34, [cannot[i:i + 10] for i in (0, 10) if cannot[i:i + 10]],
                size=18, color=MUTED, lh=26)
        y += 116

    # 唤醒时间梯
    f.text(60, 528, "醒来多久：越深的睡法越贵", size=22, color=MUTED)
    bw, bh = 330, 42
    for i, (label, us, color) in enumerate((("Sleep 1.8", 1.8, GREEN_D),
                                            ("Stop 5.4", 5.4, BLUE_D),
                                            ("Standby 50", 50, RED))):
        yy = 544 + i * 52
        f.text(64, yy + 28, label, size=19, color=color, weight="bold")
        f.rect(212, yy, max(bw * us / 50, 8), bh, color=color, fill=WHITE,
               sw=2.2)
        f.text(556, yy + 28, f"{us} µs", size=19, color=color)

    f.rect(620, 540, 472, 168, color=AMBER_STROKE, fill=WHITE, sw=2.4)
    f.text(636, 570, "两件事先做，再睡", size=22, color=AMBER_STROKE,
           weight="bold")
    f.multi(636, 600, ["① 先武装唤醒源：按键配边沿，RTC 设闹钟",
                       "② 醒来清标志，否则同一面旗又把你叫醒",
                       "IWDG 一旦启动就停不下来，超时是复位不是唤醒"],
            size=18, color=INK, lh=28)

    f.htext(560, 748, "PDDS=1 的 Standby 醒来看起来就是一次上电", size=21,
            color=INK, weight="bold", hl=True, anchor="middle")
    return f


FIGS = {
    "ch16-wake-matrix": wake_matrix,
}

if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        f = FIGS[n]()
        OUT.mkdir(parents=True, exist_ok=True)
        save(f, str(OUT / (n + ".svg")))
        print("wrote", OUT / (n + ".svg"))

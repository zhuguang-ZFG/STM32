# -*- coding: utf-8 -*-
"""ch11 knowledge-track figure (facts from docs/11, RM0008 Rev 21 ch.19).

The window watchdog counts 0x7F down to 0x3F on a 36 MHz / prescaler-8 tick
(4096 x 8 / 36e6 = 910.2 us per count, 64 counts = 58.25 ms). With W = 0x50,
feeding while the counter is still above 0x50 resets at once, and so does
letting the counter roll below 0x40: the safe feed zone is [0x40, 0x50].
"""
from hd import *


def wwdg_window():
    f = Fig("ch11-wwdg-window",
            "窗口看门狗：喂早喂晚都复位 / feed too early or too late, both reset")

    # ---- 主尺：0x7F 数到 0x3F ----
    f.text(84, 138, "计数器从 0x7F 往下数，每格约 910 µs（(1/36 MHz) × 4096 × 8），全程 64 格 = 58.25 ms",
           size=20, color=MUTED)
    ax0, ax1, ay = 140, 1012, 208
    # 三段：太早 / 安全 / 太晚
    f.rect(ax0, ay - 34, 360, 68, color=RED, fill=WHITE, sw=2.4)
    f.text(ax0 + 180, ay + 12, "喂早了：立刻复位", size=20, color=RED,
           anchor="middle", weight="bold")
    f.rect(ax0 + 360, ay - 34, 200, 68, color=GREEN_D, fill=WHITE, sw=2.4)
    f.text(ax0 + 460, ay + 12, "安全喂狗区", size=20, color=GREEN_D,
           anchor="middle", weight="bold")
    f.rect(ax0 + 560, ay - 34, 512, 68, color=RED, fill=WHITE, sw=2.4)
    f.text(ax0 + 816, ay + 12, "喂晚了：减穿 0x40，T6 清零，复位", size=20,
           color=RED, anchor="middle", weight="bold")
    # 轴与刻度
    f.stroke([(ax0, ay + 44), (ax1, ay + 44)], color=INK, sw=2.6, amp=1.2)
    ticks = [("0x7F", ax0, "起"), ("0x50", ax0 + 360, "W"), ("0x40", ax0 + 560, ""),
             ("0x3F", ax1, "复位")]
    for label, tx, note in ticks:
        f.stroke([(tx, ay + 40), (tx, ay + 56)], color=INK, sw=2.2, amp=0.8)
        f.text(tx, ay + 82, label, size=19, color=INK, anchor="middle",
               weight="bold")
        if note:
            f.text(tx, ay + 108, note, size=15, color=MUTED, anchor="middle")
    # 窗口线
    f.stroke([(ax0 + 360, ay + 34), (ax0 + 360, ay + 140)], color=AMBER_STROKE,
             sw=2.4, amp=1.0, dash="6 6")
    f.text(ax0 + 372, ay + 132, "W[6:0] = 0x50：不能早于这条线", size=17,
           color=AMBER_STROKE, weight="bold")
    # 三段的喂狗判决，直接标在轴下
    f.text(ax0 + 180, ay + 108, "这段喂 ✗", size=18, color=RED,
           anchor="middle", weight="bold")
    f.text(ax0 + 460, ay + 108, "这段喂 ✓", size=18, color=GREEN_D,
           anchor="middle", weight="bold")
    f.text(ax0 + 790, ay + 108, "这段喂 ✗", size=18, color=RED,
           anchor="middle", weight="bold")

    # ---- 换算盒 ----
    f.rect(84, 392, 500, 108, color=BLUE_D, fill=WHITE, sw=2.4)
    f.text(100, 422, "超时怎么来的", size=20, color=BLUE_D, weight="bold")
    f.multi(100, 452, ["(1/36e6) × 4096 × 8 × 64 = 58.25 ms",
                       "36 MHz 是 PCLK1，预分频 8，0x7F 起步共 64 格"],
            size=18, color=INK, lh=27)

    # ---- IWDG 对照 ----
    f.rect(612, 392, 480, 108, color=MUTED, fill=WHITE, sw=2.2)
    f.text(628, 422, "和独立看门狗就差在这", size=20, color=MUTED, weight="bold")
    f.multi(628, 452, ["IWDG：只罚晚，早喂没事",
                       "WWDG：早喂、晚喂都罚，代码跑太快也躲不掉"],
            size=18, color=INK, lh=27)

    f.htext(84, 560, "W 是「不能早于」的下限线：比它还高喂狗=复位，比 0x40 低也是复位",
            size=23, color=INK, weight="bold", hl=True)
    f.text(84, 598, "喂狗 = 把初值重写进计数器；58.25 ms 是典型值不是保证值", size=18,
           color=MUTED)
    return f


FIGS = {
    "ch11-wwdg-window": wwdg_window,
}

if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        f = FIGS[n]()
        OUT.mkdir(parents=True, exist_ok=True)
        save(f, str(OUT / (n + ".svg")))
        print("wrote", OUT / (n + ".svg"))

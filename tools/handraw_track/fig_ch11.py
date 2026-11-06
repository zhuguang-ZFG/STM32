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

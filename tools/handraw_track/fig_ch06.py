# -*- coding: utf-8 -*-
"""ch06 knowledge-track figure (facts from docs/06, RM0008 Rev 21 ch.27).

ORE: the next byte arrives while RXNE is still unread, the shift register is
overwritten, ORE sets. FE: the stop bit is not high at samples 8/9/10, FE sets,
the bad byte still lands in DR. Both clear only by reading SR (0x00) then DR
(0x04); FE alone never raises an interrupt.
"""
from hd import *


def ore_fe():
    f = Fig("ch06-ore-fe",
            "ORE 和 FE：字节还在 DR 里，标志要按顺序读走 / byte in DR, clear SR first")

    f.text(84, 136, "115200 8N1：一位约 8.68 µs，一帧 10 位约 86.8 µs。两个标志都不会自己消失",
           size=20, color=MUTED)

    # ---- 上：ORE 时间线 ----
    f.text(84, 178, "ORE 溢出错误", size=22, color=RED, weight="bold")
    f.text(84, 204, "来不及取走", size=15, color=MUTED)
    # RX 行：两个字节包
    f.text(320, 176, "RX 线上", size=16, color=MUTED)
    for i, (bx, tag) in enumerate(((320, "字节 1"), (600, "字节 2"))):
        f.rect(bx, 188, 220, 40, color=BLUE_D, fill=WHITE, sw=2.2)
        f.text(bx + 110, 214, tag, size=18, color=BLUE_D, anchor="middle",
               weight="bold")
    # RXNE 行
    f.text(320, 262, "RXNE", size=16, color=MUTED)
    f.stroke([(320, 282), (520, 282), (520, 246), (830, 246)], color=GREEN_D,
             sw=2.8, amp=1.0)
    f.text(545, 240, "置 1，没人读", size=17, color=GREEN_D, weight="bold")
    f.arrow(830, 246, 830, 196, color=RED, bend=0.0, head=10)
    f.text(846, 214, "字节 2 直接覆盖", size=17, color=RED, weight="bold")
    f.rect(1000, 188, 92, 40, color=RED, fill=RED, sw=2.2)
    f.text(1046, 214, "ORE", size=19, color=WHITE, anchor="middle",
           weight="bold", halo=False)
    f.text(320, 306, "字节 1 还在 DR，字节 2 丢了；ORE 置位后每来一个字都重复这套覆盖",
           size=17, color=INK)

    # ---- 中：FE 帧 ----
    f.text(84, 356, "FE 帧错误", size=22, color=RED, weight="bold")
    f.text(84, 382, "停止位不对", size=15, color=MUTED)
    bits = [("起", GRAY_FILL, INK), ("1", WHITE, INK), ("0", WHITE, INK),
            ("1", WHITE, INK), ("0", WHITE, INK), ("0", WHITE, INK),
            ("1", WHITE, INK), ("0", WHITE, INK), ("1", WHITE, INK),
            ("停", RED, WHITE)]
    bx = 320
    for tag, fill, tcol in bits:
        f.rect(bx, 366, 62, 44, color=INK if fill == WHITE else MUTED,
               fill=fill, sw=2.0)
        f.text(bx + 31, 394, tag, size=17, color=tcol, anchor="middle",
               weight="bold", halo=(fill != RED))
        if tag == "停":
            for k in (8, 9, 10):
                sx = bx + 8 + (k - 8) * 18
                f.circle(sx, 428, 4, color=RED, fill=RED)
            f.text(bx + 31, 456, "第 8/9/10 采样点都是低", size=15, color=RED,
                   anchor="middle")
        bx += 68
    f.rect(1024, 366, 68, 44, color=RED, fill=RED, sw=2.2)
    f.text(1058, 394, "FE", size=19, color=WHITE, anchor="middle",
           weight="bold", halo=False)
    f.text(320, 480, "0xA5 的数据位没错也白搭：坏字节照样进 DR，会不会进中断要看 RXNE 中断或 EIE",
           size=17, color=INK)

    # ---- 下：清除顺序 ----
    f.rect(84, 508, 640, 100, color=GREEN_D, fill=WHITE, sw=2.4)
    f.text(100, 538, "清 ORE / FE 的顺序不能反", size=21, color=GREEN_D,
           weight="bold")
    f.multi(100, 568, ["① 先读一次 SR（偏移 0x00）　② 再读一次 DR（偏移 0x04）",
                       "顺序反了标志清不掉，后面的字节会全部卡住"],
            size=18, color=INK, lh=27)

    f.rect(752, 508, 340, 100, color=AMBER_STROKE, fill=WHITE, sw=2.2)
    f.multi(768, 538, ["只读 DR 清不掉标志", "读错一次，浪费一次重试",
                       "串口助手上的表现：卡死"],
            size=17, color=INK, lh=27)

    f.htext(84, 656, "ORE 丢的是后来的字节，FE 不丢出事的字节——两个都在等一次「先 SR 后 DR」",
            size=22, color=INK, weight="bold", hl=True)
    return f


FIGS = {
    "ch06-ore-fe": ore_fe,
}

if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        f = FIGS[n]()
        OUT.mkdir(parents=True, exist_ok=True)
        save(f, str(OUT / (n + ".svg")))
        print("wrote", OUT / (n + ".svg"))

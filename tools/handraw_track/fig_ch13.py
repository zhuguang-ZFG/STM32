# -*- coding: utf-8 -*-
"""ch13 knowledge-track figure (facts from docs/13, RM0008 Rev 21 bxCAN).

Wired-AND arbitration: dominant (0) overwrites recessive (1). Node A sends
0x100, node B sends 0x0F0; they agree through bit9, and at bit8 A sends a
recessive 1 while B drives dominant 0, so A drops out and turns to receiving.
B finishes its frame without losing a bit; A resends when the bus is free.
"""
from hd import *

CW, GAP = 92, 8
CX0 = 300


def _cell(f, cx, y, s, color=INK, fill=WHITE, sw=2.2, bold=True, tcolor=None):
    f.rect(cx, y, CW, 56, color=color, fill=fill, sw=sw)
    f.text(cx + CW / 2, y + 36, s, size=21, color=tcolor or (color if fill == WHITE
           else WHITE), anchor="middle", weight="bold" if bold else "normal",
           halo=(fill == WHITE))


def arb_ladder():
    f = Fig("ch13-arb-ladder",
            "线与仲裁：发 1 却听到 0 的一方退出 / smaller ID wins")

    f.text(84, 138, "A 发 ID 0x100，B 发 ID 0x0F0，同时开口——一位一位比，显性（0）盖过隐性（1）",
           size=21, color=MUTED)

    heads = ["SOF", "bit10", "bit9", "bit8", "bit7", "bit6", "bit5", "…"]
    for i, h in enumerate(heads):
        f.text(CX0 + i * (CW + GAP) + CW / 2, 176, h, size=18, color=MUTED,
               anchor="middle")

    # ---- 三行：A 发 / B 发 / 线上 ----
    yA, yB, yBus = 192, 264, 336
    f.text(84, yA + 26, "A：0x100", size=21, color=RED, weight="bold")
    f.text(84, yA + 48, "实时控制", size=15, color=MUTED)
    f.text(84, yB + 26, "B：0x0F0", size=21, color=GREEN_D, weight="bold")
    f.text(84, yB + 48, "更小的 ID", size=15, color=MUTED)
    f.text(84, yBus + 26, "线上", size=21, color=BLUE_D, weight="bold")
    f.text(84, yBus + 48, "线与的结果", size=15, color=MUTED)

    a_row = ["0", "0", "0", "1", "—", "—", "—", "—"]
    b_row = ["0", "0", "0", "0", "1", "1", "1", "…"]
    bus_row = ["0", "0", "0", "0", "1", "1", "1", "…"]
    for i in range(8):
        cx = CX0 + i * (CW + GAP)
        if i < 3:
            _cell(f, cx, yA, a_row[i])
        elif i == 3:
            _cell(f, cx, yA, "1", color=RED, fill=RED)
        else:
            _cell(f, cx, yA, "改收", color=MUTED, fill=GRAY_FILL, bold=False,
                  tcolor=MUTED)
        _cell(f, cx, yB, b_row[i], color=GREEN_D if b_row[i] != "…" else MUTED)
        if bus_row[i] == "0":
            _cell(f, cx, yBus, "0", color=BLUE_D, fill=BLUE_D)
        else:
            _cell(f, cx, yBus, bus_row[i])

    # ---- bit8 的判决箭头（从线上行的 bit8 格往下指，不穿过别的格） ----
    lose_x = CX0 + 3 * (CW + GAP) + CW / 2
    f.arrow(lose_x, yBus + 60, lose_x, yBus + 86, color=RED, bend=0.0, head=10)
    f.rect(480, 424, 612, 84, color=RED, fill=WHITE, sw=2.4)
    f.text(496, 454, "bit8：A 发 1（隐性），线上却是 0（显性）", size=20,
           color=RED, weight="bold")
    f.text(496, 484, "A 知道有人 ID 更小，立刻闭嘴改成接收，等总线空了再发",
           size=18, color=INK)

    # ---- 显性/隐性图例 ----
    f.rect(84, 530, 500, 108, color=BLUE_D, fill=WHITE, sw=2.4)
    f.text(100, 560, "线与：只要有人拉显性，全线就是显性", size=20,
           color=BLUE_D, weight="bold")
    f.multi(100, 590, ["显性 0：CANH−CANL ≈ 2 V，先出现 0 的 ID 赢",
                       "隐性 1：差值 ≈ 0，所有节点都发隐性才是 1"],
            size=18, color=INK, lh=27)

    # ---- 优先级梯 ----
    f.text(620, 546, "ID 越小优先级越高（章里的表）", size=19, color=MUTED)
    ladder = [("0x000", "紧急/控制", 380), ("0x100", "实时控制", 300),
              ("0x500", "状态上报", 220), ("0x7FF", "非关键/日志", 150)]
    yy = 560
    for idv, use, w in ladder:
        f.rect(620, yy, w, 26, color=GREEN_D, fill=WHITE, sw=1.8)
        f.text(632, yy + 19, f"{idv}  {use}", size=15, color=INK)
        yy += 32

    f.htext(84, 726, "输的一方不用重传、不产生错误帧，赢的一方一位没坏——这就是「非破坏」",
            size=23, color=INK, weight="bold", hl=True)
    return f


FIGS = {
    "ch13-arb-ladder": arb_ladder,
}

if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        f = FIGS[n]()
        OUT.mkdir(parents=True, exist_ok=True)
        save(f, str(OUT / (n + ".svg")))
        print("wrote", OUT / (n + ".svg"))

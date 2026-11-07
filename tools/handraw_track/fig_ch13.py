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
    f.text(620, 546, "标准数据帧：ID 小的优先", size=19, color=MUTED)
    ladder = [("0x000", "紧急/控制", 380), ("0x100", "实时控制", 300),
              ("0x500", "状态上报", 220), ("0x7FF", "非关键/日志", 150)]
    yy = 560
    for idv, use, w in ladder:
        f.rect(620, yy, w, 26, color=GREEN_D, fill=WHITE, sw=1.8)
        f.text(632, yy + 19, f"{idv}  {use}", size=15, color=INK)
        yy += 32

    f.htext(84, 726, "A 输后转接收、稍后再争总线；B 的帧继续发送，仲裁没有破坏它",
            size=23, color=INK, weight="bold", hl=True)
    return f


def filter_mask():
    f = Fig("ch13-filter-mask",
            "掩码逐位打分，列表精确点名 / mask grades bit by bit, list names exact IDs")

    f.text(84, 138, "两种配法：掩码模式逐位打分，列表模式精确点名；标准 ID 还要左移 5 位放对位置",
           size=21, color=MUTED)

    # ---- 左：掩码模式 ----
    f.rect(84, 168, 480, 216, color=BLUE_D, fill=WHITE, sw=2.4)
    f.text(100, 200, "掩码模式：逐位打分", size=22, color=BLUE_D, weight="bold")
    f.multi(100, 238, ["掩码位 = 1 → 这一位必须相同",
                       "掩码位 = 0 → 这一位不关心"], size=19, color=INK, lh=30)
    f.multi(100, 306, ["本章例：掩码 0x7FF << 5",
                       "→ 11 位 ID 全部必须匹配"], size=18, color=BLUE_D, lh=28)

    # ---- 右：列表模式 ----
    f.rect(596, 168, 468, 216, color=GREEN_D, fill=WHITE, sw=2.4)
    f.text(612, 200, "列表模式：精确点名", size=22, color=GREEN_D, weight="bold")
    f.multi(612, 238, ["只收写进过滤器的 ID，一位都不能差",
                       "32 位位宽：一个完整 ID（标准+扩展）",
                       "16 位位宽：两个标准 ID",
                       "命中的报文进绑定的 FIFO0/FIFO1"], size=18, color=INK, lh=30)

    # ---- 中下：0x123 << 5 的位条 ----
    f.text(84, 424, "标准 ID 写进 FilterIdHigh：0x123 << 5 = 0x2460", size=21,
           color=INK, weight="bold")
    bits = [0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0]   # 0x2460, b15..b0
    for i, b in enumerate(bits):
        cx = 84 + i * 52
        if i < 11:
            f.rect(cx, 452, 46, 46, color=AMBER_STROKE, fill=AMBER_FILL, sw=1.8)
            f.text(cx + 23, 483, str(b), size=19, color=INK, anchor="middle",
                   weight="bold")
        else:
            f.rect(cx, 452, 46, 46, color=MUTED, fill=GRAY_FILL, sw=1.4)
            f.text(cx + 23, 483, str(b), size=19, color=MUTED, anchor="middle")
    f.text(367, 442, "0x123 的 11 位 ID（001 0010 0011）", size=15, color=MUTED,
           anchor="middle")
    f.text(783, 442, "左移补的 5 个 0", size=15, color=MUTED, anchor="middle")
    f.text(84, 524, "位放对了，掩码才逐位比得起来", size=18, color=MUTED)

    # ---- 不左移的下场 ----
    f.rect(84, 552, 980, 96, color=RED, fill=WHITE, sw=2.4)
    f.text(104, 584, "不左移：位置全错，掩码一位都对不上", size=21, color=RED,
           weight="bold")
    f.multi(104, 616, ["总线上明明有帧，邮箱却一直是空的",
                       "本章写入：FilterIdHigh = 0x123 << 5，FilterMaskIdHigh = 0x7FF << 5"],
            size=18, color=INK, lh=26)

    f.htext(84, 690, "掩码定「哪些位必须一样」，左移定「ID 放哪」——两处都对，邮箱才有帧",
            size=23, color=INK, weight="bold", hl=True)
    f.text(84, 730, "例值 0x123 / 0x7FF 取自本章例程；图为匹配行为示意，未画全部 32 位位域。",
           size=18, color=MUTED)
    return f


FIGS = {
    "ch13-arb-ladder": arb_ladder,
    "ch13-filter-mask": filter_mask,
}

if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        f = FIGS[n]()
        OUT.mkdir(parents=True, exist_ok=True)
        save(f, str(OUT / (n + ".svg")))
        print("wrote", OUT / (n + ".svg"))

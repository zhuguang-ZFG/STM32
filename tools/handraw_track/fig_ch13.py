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



def diff_levels():
    f = Fig("ch13-diff-levels",
            "差分看压差：显性 0 盖过隐性 1 / dominant 0 wins")
    f.text(84, 134, "同一干扰同时打在两根线上，压差不变——CAN 只认 CAN_H − CAN_L",
           size=21, color=MUTED)
    bits = [1, 0, 0, 1, 0, 1]
    x0, bw = 220, 140
    f.text(96, 214, "CAN_H", size=21, color=BLUE_D, weight="bold")
    f.text(96, 336, "CAN_L", size=21, color=RED, weight="bold")
    hp, lp = [], []
    for i, b in enumerate(bits):
        xa, xb = x0 + i * bw, x0 + (i + 1) * bw
        hy, ly = (262, 274) if b else (206, 330)
        hp += [(xa, hy), (xb, hy)]
        lp += [(xa, ly), (xb, ly)]
        f.text((xa + xb) / 2, 176, "1 隐性" if b else "0 显性", size=19,
               color=MUTED if b else BLUE_D, anchor="middle", weight="bold")
        if i:
            f.line(xa, 160, xa, 344, color=GRAY_FILL, sw=1.6, amp=0.4, dash="4 6")
    f.stroke(hp, color=BLUE_D, sw=3.4, amp=0.6)
    f.stroke(lp, color=RED, sw=3.4, amp=0.6)
    f.htext(84, 386, "压差 ≈ 2 V → 显性 0；压差 ≈ 0 V → 隐性 1；任一节点发显性，整条线就是显性",
            size=20, color=INK)

    # bus topology
    f.line(150, 560, 1002, 560, color=BLUE_D, sw=3.2, amp=0.8)
    f.line(150, 596, 1002, 596, color=RED, sw=3.2, amp=0.8)
    for rx in (106, 1006):
        f.rect(rx, 548, 40, 60, color=AMBER_STROKE, fill=WHITE, sw=2.4)
        f.text(rx + 20, 636, "120 Ω", size=19, color=AMBER_STROKE,
               anchor="middle", weight="bold")
    for nx in (220, 440, 660):
        f.rect(nx, 420, 200, 48, color=GREEN_D, fill=WHITE, sw=2.4)
        f.text(nx + 100, 452, "MCU · CAN 控制器", size=17, color=GREEN_D,
               anchor="middle", weight="bold")
        f.line(nx + 100, 468, nx + 100, 486, color=INK, sw=2.0, amp=0.4)
        f.rect(nx + 30, 486, 140, 40, color=INK, fill=GRAY_FILL, sw=2.2)
        f.text(nx + 100, 513, "收发器", size=18, color=INK, anchor="middle",
               weight="bold")
        f.line(nx + 80, 526, nx + 80, 560, color=BLUE_D, sw=2.2, amp=0.4)
        f.line(nx + 120, 526, nx + 120, 596, color=RED, sw=2.2, amp=0.4)
    f.multi(884, 440, ["MCU 侧 TX/RX", "是 TTL 电平"], size=17, color=MUTED, lh=26)
    f.text(576, 666, "两只 120 Ω 接在 CANH–CANL 两端：并联直流 60 Ω，不是电缆特性阻抗",
           size=19, color=INK, anchor="middle")
    f.panel(84, 692, 984, 66, AMBER_FILL)
    f.rect(84, 692, 984, 66, color=AMBER_STROKE, sw=2.6)
    f.text(576, 734, "MCU 里只有控制器，收发器必须外接；1 Mbps ≤ 40 m，125 kbps 约 500 m",
           size=21, color=INK, anchor="middle", weight="bold")
    return f


def data_frame():
    f = Fig("ch13-data-frame",
            "数据帧只写「是什么」，不写收件人 / the data frame")
    f.text(84, 134, "标准数据帧，从左到右上线（位数）；所有节点都听，按 ID 自己决定收不收",
           size=20, color=MUTED)
    fields = [("SOF", "1", 64, INK), ("ID", "11 位", 170, BLUE_D),
              ("RTR", "1", 64, BLUE_D), ("IDE r0", "2", 90, GREEN_D),
              ("DLC", "4", 80, GREEN_D), ("数据", "0–8 B", 200, INK),
              ("CRC", "15+1", 130, RED), ("ACK", "2", 70, AMBER_STROKE),
              ("EOF", "7", 70, MUTED), ("IFS", "", 46, MUTED)]
    x = 84
    spans = {}
    for name, bits, w, c in fields:
        f.rect(x, 160, w, 76, color=c, fill=WHITE, sw=2.4, double=False)
        f.text(x + w / 2, 190, name, size=18, color=c, anchor="middle", weight="bold")
        f.text(x + w / 2, 222, bits, size=17, color=INK, anchor="middle")
        spans[name] = (x, x + w)
        x += w
    groups = [("仲裁场", "ID", "RTR", BLUE_D), ("控制场", "IDE r0", "DLC", GREEN_D),
              ("数据场", "数据", "数据", INK), ("CRC 场", "CRC", "CRC", RED)]
    for label, a, b, c in groups:
        xa, xb = spans[a][0] + 6, spans[b][1] - 6
        f.stroke([(xa, 248), (xa, 258), (xb, 258), (xb, 248)], color=c, sw=2.2, amp=0.6)
        f.text((xa + xb) / 2, 284, label, size=18, color=c, anchor="middle", weight="bold")
    f.text(1068, 284, "EOF = 7 个隐性位", size=17, color=MUTED, anchor="end")

    # left: standard vs extended
    f.rect(84, 318, 470, 210, color=BLUE_D, fill=WHITE, sw=2.6)
    f.text(104, 354, "标准帧与扩展帧", size=22, color=BLUE_D, weight="bold")
    f.multi(104, 394, ["标准帧：11 位 ID，IDE = 0",
                       "扩展帧：11 位基础 ID + 18 位",
                       "　　　　扩展 ID = 29 位，IDE = 1",
                       "比 ID 时数值越小，优先级越高"],
            size=19, color=INK, lh=33)
    # right: bit stuffing
    f.rect(578, 318, 490, 210, color=RED, fill=WHITE, sw=2.6)
    f.text(598, 354, "位填充：给接收方对表", size=22, color=RED, weight="bold")
    seq = ["0", "0", "0", "0", "0", "1", "0", "0"]
    for i, s in enumerate(seq):
        stuffed = i == 5
        cx = 604 + i * 54
        f.rect(cx, 376, 46, 46, color=RED if stuffed else INK,
               fill=AMBER_FILL if stuffed else WHITE, sw=2.2, double=False)
        f.text(cx + 23, 408, s, size=21, color=RED if stuffed else INK,
               anchor="middle", weight="bold")
    f.text(604 + 5 * 54 + 23, 446, "插入位", size=16, color=RED, anchor="middle")
    f.multi(598, 482, ["连续 5 个相同位后插 1 个相反位，",
                       "收端自动拿掉；CRC 定界符起的固定格式段不填充"],
            size=17, color=INK, lh=28)

    boxes = [("CRC", "15 位 + 1 位定界符；校验错就发错误帧", RED),
             ("ACK", "发端发隐性；任一正确收到的节点拉显性", AMBER_STROKE),
             ("单节点", "正常模式没人 ACK，发送会一直重试", BLUE_D)]
    for i, (t, s, c) in enumerate(boxes):
        y = 560 + i * 66
        f.rect(84, y, 984, 54, color=c, fill=WHITE, sw=2.2, double=False)
        f.text(108, y + 36, t, size=20, color=c, weight="bold")
        f.text(220, y + 36, s, size=19, color=INK)
    return f


def pitfall_triage():
    f = Fig("ch13-pitfall-triage",
            "七个常见坑对号入座：现象 → 第一边界 → 出处 / pitfall triage")
    f.text(84, 126, "先对现象，再找第一处边界，最后按标签查出处；不要从第三列开始改",
           size=20, color=MUTED)
    rows = [
        ("线上是 450 kbit/s", "位时间除不尽 → 预分频 9、BS1 5、BS2 2", "RM0008", BLUE_D),
        ("单节点帧一直重发", "无人 ACK → 先用回环，上总线要有应答节点", "RM0008", BLUE_D),
        ("总线上有帧、邮箱空", "标准 ID 没左移 → FilterIdHigh 左移 5", "本仓库例程", GREEN_D),
        ("两端都在报错", "位时间不一致或没接终端 → 两端各 120 Ω", "本仓库例程", GREEN_D),
        ("CAN 占了 USB 的脚", "停在复位默认 → 重映射到第 45/46 脚", "DS5319", AMBER_STROKE),
        ("重映射后晶振停", "第 5/6 脚是 HSE → 别把 CAN 放过去", "DS5319", AMBER_STROKE),
        ("和 I2C 抢 PB8/PB9", "PB8/PB9 也是 I2C1 重映射 → 二选一", "DS5319", AMBER_STROKE),
    ]
    y = 158
    for i, (sym, fix, tag, tc) in enumerate(rows):
        f.circle(112, y + 26, 24, color=INK, fill=WHITE, sw=2.4)
        f.text(112, y + 36, str(i + 1), size=22, color=INK, anchor="middle",
               weight="bold", halo=True)
        f.rect(150, y, 268, 56, color=RED, fill=WHITE, sw=2.4)
        f.text(166, y + 36, sym, size=20, color=RED, weight="bold", halo=True)
        f.arrow(428, y + 28, 470, y + 28, color=MUTED, sw=2.4)
        f.rect(478, y, 420, 56, color=INK, fill=WHITE, sw=2.2)
        f.text(494, y + 36, fix, size=18, color=INK, halo=True)
        f.rect(918, y, 150, 56, color=tc, fill=WHITE, sw=2.4)
        f.text(993, y + 36, tag, size=17, color=tc, anchor="middle", weight="bold",
               halo=True)
        y += 76
    f.panel(84, y + 8, 984, 54, AMBER_FILL)
    f.rect(84, y + 8, 984, 54, color=AMBER_STROKE, sw=2.6)
    f.text(576, y + 42, "出处标签：RM0008 = 参考手册 · 本仓库例程 = examples/can-bxcan · DS5319 = 数据手册",
           size=18, color=INK, anchor="middle", weight="bold")
    return f


FIGS = {
    "ch13-pitfall-triage": pitfall_triage,
    "ch13-diff-levels": diff_levels,
    "ch13-data-frame": data_frame,
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

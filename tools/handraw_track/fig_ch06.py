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
    f.text(846, 214, "字节 2 进不了 DR", size=17, color=RED, weight="bold")
    f.rect(1000, 188, 92, 40, color=RED, fill=RED, sw=2.2)
    f.text(1046, 214, "ORE", size=19, color=WHITE, anchor="middle",
           weight="bold", halo=False)
    f.text(320, 306, "DR 留着字节 1；字节 2 无法转入，移位寄存器随后被新数据覆盖",
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
    f.text(320, 480, "图中未发生 ORE：坏字节仍进 DR；FE 本身不单独触发中断，DMA 模式可用 EIE",
           size=17, color=INK)

    # ---- 下：清除顺序 ----
    f.rect(84, 508, 640, 100, color=GREEN_D, fill=WHITE, sw=2.4)
    f.text(100, 538, "清 ORE / FE 的顺序不能反", size=21, color=GREEN_D,
           weight="bold")
    f.multi(100, 568, ["① 先读一次 SR（偏移 0x00）　② 再读一次 DR（偏移 0x04）",
                       "清错误标志后还要检查接收流程；已丢的字节不会回来"],
            size=18, color=INK, lh=27)

    f.rect(752, 508, 340, 100, color=AMBER_STROKE, fill=WHITE, sw=2.2)
    f.multi(768, 538, ["只读 DR：会清 RXNE", "清 ORE / FE：先 SR 后 DR",
                       "两种清除动作要分开看"],
            size=17, color=INK, lh=27)

    f.htext(84, 656, "ORE：来不及取；FE：停止位不对。先保存 SR，再读 DR 处理数据与错误",
            size=22, color=INK, weight="bold", hl=True)
    return f


def sample_points():
    f = Fig("ch06-sample-points",
            "16 倍过采样：起始位问 3、5、7，表决看 8、9、10 / sample points in one bit")

    f.text(84, 136, "RX 空闲为高。下降沿一到，接收器按 16 倍波特率数采样点：一位 16 格",
           size=20, color=MUTED)

    # ---- 上：起始位放大，16 格与确认/表决点 ----
    f.text(84, 178, "起始位：先确认，再表决（放大看）", size=21, color=GREEN_D,
           weight="bold")
    hi, lo = 210, 272
    # 毛刺（撑不满一位）→ 空闲 → 真正的起始位（16 格）→ 下一位
    f.stroke([(84, hi), (150, hi), (150, lo), (205, lo), (205, hi),
              (420, hi), (420, lo), (820, lo), (820, hi), (1064, hi)],
             color=BLUE_D, sw=3.2, amp=1.0)
    f.text(177, 318, "毛刺", size=16, color=RED, anchor="middle", weight="bold")
    f.text(84, 346, "毛刺：3/5/7 已回高 → 丢弃", size=17, color=RED,
           weight="bold")
    # 16 个格子编号
    for k in range(1, 17):
        cx = 420 + (k - 1) * 25 + 12.5
        f.text(cx, 300, str(k), size=13, color=MUTED, anchor="middle")
    # 确认点 3/5/7（绿）与表决点 8/9/10（蓝），都压在低电平线上
    for k in (3, 5, 7):
        f.circle(420 + (k - 1) * 25 + 12.5, lo, 7, color=GREEN_D, fill=GREEN)
    for k in (8, 9, 10):
        f.circle(420 + (k - 1) * 25 + 12.5, lo, 7, color=BLUE_D, fill=BLUE)
    f.text(545, 346, "3、5、7 都是 0 → 起始位确认", size=17, color=GREEN_D,
           anchor="middle", weight="bold")
    f.text(632, 372, "8、9、10 三点表决：落在位中间", size=17, color=BLUE_D,
           anchor="middle", weight="bold")
    f.text(942, 196, "下一位起：数据位", size=15, color=MUTED, anchor="middle")

    # ---- 中：一帧 10 位，色条 = 采样点落点 ----
    f.text(84, 436, "一帧 10 位，每位 16 格：色条 = 采样点落点", size=21,
           color=INK, weight="bold")
    names = ["起", "D0", "D1", "D2", "D3", "D4", "D5", "D6", "D7", "停"]
    for i, nm in enumerate(names):
        cx = 84 + i * 92
        f.rect(cx, 458, 88, 60, color=INK, fill=WHITE, sw=2.0)
        f.text(cx + 44, 480, nm, size=17, color=INK, anchor="middle",
               weight="bold")
        # 16 格的细刻度
        for j in range(1, 16):
            f.line(cx + j * 5.5, 488, cx + j * 5.5, 514, color=MUTED, sw=0.8,
                   amp=0.3, opacity=0.25)
        if i == 0:
            # 起始位：3/5/7 确认条 + 8/9/10 表决条
            f.rect(cx + 11, 490, 27.5, 18, color=GREEN_D, fill=GREEN, sw=1.6,
                   r=2, double=False)
        f.rect(cx + 38.5, 490, 16.5, 18, color=AMBER_STROKE, fill=AMBER_FILL,
               sw=1.6, r=2, double=False)
    f.text(84, 546, "绿条：起始位确认点（3、5、7）", size=17, color=GREEN_D,
           weight="bold")
    f.text(360, 546, "琥珀条：表决点（8、9、10）= 位中间", size=17,
           color=AMBER_STROKE, weight="bold")

    # ---- 下：过采样档位与时间账 ----
    f.rect(84, 590, 552, 96, color=GREEN_D, fill=WHITE, sw=2.4)
    f.text(100, 622, "F103 固定 16 倍过采样", size=20, color=GREEN_D,
           weight="bold")
    f.multi(100, 652, ["CR1 位 31:14 保留，没有 OVER8 位", "想用 8 倍过采样得换系列"],
            size=17, color=INK, lh=26)

    f.rect(664, 590, 400, 96, color=BLUE_D, fill=WHITE, sw=2.4)
    f.text(680, 622, "115200 8N1 的时间账", size=20, color=BLUE_D,
           weight="bold")
    f.multi(680, 652, ["一位约 8.68 µs；一帧 10 位约 86.8 µs",
                       "16 倍时钟把每位切成 16 格"],
            size=17, color=INK, lh=26)

    f.htext(84, 716, "口诀：起始位先问 3、5、7，数据与停止位看 8、9、10",
            size=22, color=INK, weight="bold", hl=True)
    return f


FIGS = {
    "ch06-ore-fe": ore_fe,
    "ch06-sample-points": sample_points,
}

if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        f = FIGS[n]()
        OUT.mkdir(parents=True, exist_ok=True)
        save(f, str(OUT / (n + ".svg")))
        print("wrote", OUT / (n + ".svg"))

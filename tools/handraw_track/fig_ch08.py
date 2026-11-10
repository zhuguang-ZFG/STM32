# -*- coding: utf-8 -*-
"""ch08 knowledge-track figure (facts from docs/08, RM0008 Rev 21 §25.5.1).

Full duplex is one ring: master and slave each hold an 8-bit shift register,
every SCK edge shifts one bit out and one bit in on both sides. The JEDEC read
sends 9F FF FF FF and simultaneously receives ?? EF 40 17 — rx[0] is the tail
of the previous transaction, not the vendor id.
"""
from hd import *


def byte_exchange():
    f = Fig("ch08-byte-exchange",
            "全双工就是一个环：发一位的同时也收一位 / one ring, 8 clocks, 1 byte")

    # ---- 上：两个移位寄存器构成的环 ----
    f.text(84, 138, "读 W25Q64 的 JEDEC ID：主机发 9F FF FF FF，同一串 SCK 里从机也回了 4 个字节",
           size=21, color=MUTED)

    mbx, sby, by, bh = 84, 768, 168, 168
    f.rect(mbx, by, 300, bh, color=BLUE_D, fill=WHITE, sw=2.6)
    f.text(mbx + 150, by + 34, "主机 STM32", size=23, color=BLUE_D,
           anchor="middle", weight="bold")
    f.text(mbx + 150, by + 62, "8 位移位寄存器（发 0x9F）", size=17,
           color=MUTED, anchor="middle")
    bits = "10011111"
    cw = 30
    cx = mbx + 12
    for i, b in enumerate(bits):
        f.rect(cx, by + 78, cw, 36, color=BLUE_D, fill=WHITE, sw=1.8)
        f.text(cx + cw / 2, by + 103, b, size=19, color=BLUE_D,
               anchor="middle", weight="bold")
        cx += cw + 2.5
    f.text(mbx + 150, by + 148, "每个沿：左移出 1 位，右端进 1 位", size=16,
           color=MUTED, anchor="middle")

    f.rect(sby, by, 300, bh, color=GREEN_D, fill=WHITE, sw=2.6)
    f.text(sby + 150, by + 34, "从机 W25Q64", size=23, color=GREEN_D,
           anchor="middle", weight="bold")
    f.text(sby + 150, by + 62, "它也在移位：一边收 0x9F", size=17,
           color=MUTED, anchor="middle")
    cx = sby + 12
    for i in range(8):
        f.rect(cx, by + 78, cw, 36, color=GREEN_D, fill=WHITE, sw=1.8)
        f.text(cx + cw / 2, by + 103, "?", size=19, color=MUTED,
               anchor="middle", weight="bold")
        cx += cw + 2.5
    f.text(sby + 150, by + 148, "一边把要回的位从 MISO 移出", size=16,
           color=MUTED, anchor="middle")

    # 中间的两条线
    f.arrow(396, 216, 756, 216, color=BLUE_D, bend=0.05, sw=3.2)
    f.text(576, 200, "MOSI", size=20, color=BLUE_D, anchor="middle",
           weight="bold")
    f.arrow(756, 276, 396, 276, color=GREEN_D, bend=-0.05, sw=3.2)
    f.text(576, 262, "MISO", size=20, color=GREEN_D, anchor="middle",
           weight="bold")
    f.text(576, 306, "两个寄存器首尾相接，构成环", size=17, color=INK,
           anchor="middle")
    f.text(576, 360, "SCK 由主机给：8 个沿换 1 个字节（BR=010 时 9 MHz）",
           size=17, color=MUTED, anchor="middle")
    f.text(576, 386, "CS ↓ 事务期间保持低", size=17, color=MUTED,
           anchor="middle")

    # ---- 下：JEDEC 四行账 ----
    cols = [("时钟", 84, 150), ("MOSI 上发", 246, 170), ("MISO 上收", 428, 210),
            ("这 8 个沿换来了什么", 650, 414)]
    f.text(cols[0][1] + 12, 428, cols[0][0], size=19, color=MUTED)
    f.text(cols[1][1] + 12, 428, cols[1][0], size=19, color=MUTED)
    f.text(cols[2][1] + 12, 428, cols[2][0], size=19, color=MUTED)
    f.text(cols[3][1] + 12, 428, cols[3][0], size=19, color=MUTED)
    rows = [
        ("1 – 8", "0x9F", "rx[0] = ??", "命令本身；回的是上一包的剩菜", MUTED),
        ("9 – 16", "0xFF", "rx[1] = 0xEF", "厂商号：Winbond", GREEN_D),
        ("17 – 24", "0xFF", "rx[2] = 0x40", "存储器类型（不是容量）", BLUE_D),
        ("25 – 32", "0xFF", "rx[3] = 0x17", "容量：64 Mbit → W25Q64", AMBER_STROKE),
    ]
    y = 444
    for rng, tx, rx, what, color in rows:
        f.rect(84, y, 150, 50, color=color, fill=WHITE, sw=2.2)
        f.text(159, y + 32, rng, size=19, color=INK, anchor="middle")
        f.rect(246, y, 170, 50, color=color, fill=WHITE, sw=2.2)
        f.text(331, y + 32, tx, size=20, color=INK, anchor="middle")
        f.rect(428, y, 210, 50, color=color, fill=WHITE, sw=2.2)
        f.text(533, y + 32, rx, size=20, color=color, anchor="middle",
               weight="bold")
        f.text(660, y + 32, what, size=19, color=INK)
        y += 58

    f.htext(84, 704, "拼 ID：rx[1]<<16 | rx[2]<<8 | rx[3] = 0xEF 40 17 —— rx[0] 永远别用",
            size=23, color=INK, weight="bold", hl=True)
    f.text(84, 738, "只写不读会丢包：下一次读到的可能是上一包的剩菜。HAL 里用收发一起的接口，把两边一次做完",
           size=18, color=MUTED)
    return f


def cs_bracket():
    f = Fig("ch08-cs-bracket",
            "片选是括号：先拉低，再给时钟，最后才拉高 / chip select brackets the transaction")

    f.text(84, 136, "PA4（第 14 脚）推挽输出当片选：拉低 = 开始，拉高 = 结束",
           size=20, color=MUTED)

    # ---- 上：一个字节的括号（Mode 0）----
    f.text(84, 178, "一个字节的括号（Mode 0：SCK 空闲低，上升沿采样）", size=21,
           color=INK, weight="bold")
    # CS 行
    f.text(92, 224, "CS", size=18, color=RED, weight="bold")
    f.stroke([(140, 200), (190, 200), (190, 236), (800, 236), (800, 200),
              (1064, 200)], color=RED, sw=3.2, amp=1.0)
    # SCK 行：8 个脉冲
    f.text(92, 306, "SCK", size=18, color=BLUE_D, weight="bold")
    pts = [(140, 318)]
    for k in range(8):
        r_ = 250 + 65 * k
        pts += [(r_, 318), (r_, 282), (r_ + 32, 282), (r_ + 32, 318)]
    pts += [(1064, 318)]
    f.stroke(pts, color=BLUE_D, sw=3.0, amp=1.0)
    for k in range(8):
        f.circle(250 + 65 * k, 282, 5.5, color=GREEN_D, fill=GREEN)
    # MOSI 行：位格对齐到「下降沿换位、上升沿采样」
    f.text(92, 366, "MOSI", size=18, color=INK, weight="bold")
    f.line(150, 362, 217, 362, color=MUTED, sw=1.6, dash="5 6", opacity=0.6)
    f.line(737, 362, 1064, 362, color=MUTED, sw=1.6, dash="5 6", opacity=0.6)
    bits = "10011111"          # 0x9F，MSB 先发
    for k, b in enumerate(bits):
        x = 217 + 65 * k
        f.rect(x, 340, 65, 44, color=INK, fill=WHITE, sw=2.0)
        f.text(x + 32.5, 368, b, size=20, color=INK, anchor="middle",
               weight="bold")
    f.text(477, 410, "0x9F，MSB 先发：换位在下降沿，采样在上升沿", size=17,
           color=MUTED, anchor="middle")
    # 三个阶段小标注
    f.text(220, 264, "先拉低", size=16, color=RED, anchor="middle",
           weight="bold")
    f.text(510, 264, "上升沿采样 ×8", size=16, color=GREEN_D, anchor="middle",
           weight="bold")
    f.text(768, 264, "再拉高", size=16, color=RED, anchor="middle",
           weight="bold")
    f.arrow(810, 196, 878, 182, color=RED, sw=2.0, bend=0.0, head=9)
    f.text(890, 178, "有的从机此刻才把字节收下", size=16, color=RED,
           weight="bold")
    # 三句结论
    f.text(84, 440, "CS↓ 早于第 1 个采样沿", size=19, color=RED, weight="bold")
    f.text(436, 440, "每个上升沿采 1 位", size=19, color=GREEN_D, weight="bold")
    f.text(712, 440, "最后一个下降沿之后才 CS↑", size=19, color=BLUE_D,
           weight="bold")

    # ---- 中：括号装命令，一条一个 ----
    f.text(84, 486, "括号装命令：CS 拉低到拉高之间，正好一条命令", size=21,
           color=INK, weight="bold")
    # 左：正确
    f.stroke([(92, 522), (116, 522), (116, 548), (296, 548), (296, 522),
              (348, 522), (348, 548), (528, 548), (528, 522), (552, 522)],
             color=RED, sw=2.8, amp=0.9)
    pts = [(92, 600)]
    for span in (116, 348):
        for k in range(8):
            r_ = span + 22.5 * k
            pts += [(r_, 600), (r_, 576), (r_ + 11, 576), (r_ + 11, 600)]
    pts += [(552, 600)]
    f.stroke(pts, color=BLUE_D, sw=2.4, amp=0.8)
    f.text(322, 516, "CS↑", size=13, color=GREEN_D, anchor="middle")
    f.text(206, 628, "命令 A（8 拍）", size=16, color=INK, anchor="middle")
    f.text(438, 628, "命令 B（8 拍）", size=16, color=INK, anchor="middle")
    f.text(92, 656, "对：一条命令一个括号", size=20, color=GREEN_D,
           weight="bold")
    # 右：错误（一直压低）
    f.stroke([(588, 522), (612, 522), (612, 548), (1040, 548), (1040, 522),
              (1064, 522)], color=RED, sw=2.8, amp=0.9)
    pts = [(588, 600)]
    for k in range(16):
        r_ = 612 + 26.75 * k
        pts += [(r_, 600), (r_, 576), (r_ + 13, 576), (r_ + 13, 600)]
    pts += [(1064, 600)]
    f.stroke(pts, color=BLUE_D, sw=2.4, amp=0.8)
    f.line(819, 540, 819, 610, color=RED, sw=1.8, dash="4 5")
    f.text(819, 628, "第 9 拍起已是下一条命令", size=15, color=RED,
           anchor="middle")
    f.text(588, 656, "错：PA4 一直压低 → 粘成一条 16 拍长帧", size=20,
           color=RED, weight="bold")

    # ---- 下：做法与口诀 ----
    f.rect(84, 688, 560, 66, color=GREEN_D, fill=WHITE, sw=2.4)
    f.multi(100, 714, ["PA4 是推挽输出，不是硬件 NSS：何时拉低、拉多久由代码决定",
                       "每条事务结束把 PA4 拉高，下一包才有自己的括号"],
            size=17, color=INK, lh=28)
    f.rect(672, 688, 392, 66, color=AMBER_STROKE, fill=WHITE, sw=2.2)
    f.text(688, 718, "口诀：先拉低，再给时钟，最后拉高", size=19,
           color=AMBER_STROKE, weight="bold")
    f.text(688, 744, "有的从机在 CS↑ 才把字节收下", size=15, color=MUTED)
    return f


def cs_triage():
    f = Fig("ch08-cs-triage",
            "片选失焦分诊：先看括号，再数几片 CS 低 / chip-select triage")

    f.text(84, 134, "多从机共用 SCK/MOSI/MISO，每片一根 CS；同一时刻只允许一片为低",
           size=19, color=MUTED)

    # ---- 左上：一个括号包住一次事务 ----
    f.text(84, 176, "① 一条事务 = 一个括号（Mode 0）", size=20,
           color=GREEN_D, weight="bold")
    f.text(92, 232, "CS", size=17, color=RED, weight="bold")
    f.stroke([(140, 210), (190, 210), (190, 246), (470, 246), (470, 210),
              (566, 210)], color=RED, sw=3.0, amp=1.0)
    f.text(200, 200, "拉低", size=15, color=RED, weight="bold")
    f.text(480, 200, "拉高", size=15, color=RED, weight="bold")
    f.text(92, 288, "SCK", size=17, color=BLUE_D, weight="bold")
    pts = [(140, 300)]
    for k in range(8):
        rx = 210 + 32 * k
        pts += [(rx, 300), (rx, 268), (rx + 16, 268), (rx + 16, 300)]
    pts += [(566, 300)]
    f.stroke(pts, color=BLUE_D, sw=2.8, amp=1.0)
    f.text(84, 340, "括号里 8 个沿换 1 个字节；CS↑ 之后才允许下一条命令",
           size=16, color=INK)
    f.text(84, 368, "一直压着 CS：下一条命令接在上一条后面，两包粘成一包",
           size=16, color=RED, weight="bold")

    # ---- 右上：每片一根 CS ----
    f.text(584, 176, "② 每个从机一根 CS", size=20, color=GREEN_D,
           weight="bold")
    f.rect(584, 206, 110, 90, color=BLUE_D, fill=WHITE, sw=2.4)
    f.text(639, 245, "主机", size=17, color=BLUE_D, anchor="middle",
           weight="bold")
    f.text(639, 270, "SPI1", size=16, color=MUTED, anchor="middle")
    f.line(694, 236, 800, 236, color=BLUE_D, sw=2.4)
    f.line(800, 236, 800, 371, color=BLUE_D, sw=2.4)
    f.text(704, 222, "SCK / MOSI / MISO 共用", size=14, color=BLUE_D)
    for k, (tag, state, col) in enumerate((
            ("从机 A · CS 低", "A", GREEN_D),
            ("从机 B · CS 高", "B", MUTED),
            ("从机 C · CS 高", "C", MUTED))):
        sy = 206 + k * 70
        f.line(800, sy + 25, 900, sy + 25, color=col, sw=2.2,
               dash=None if col == GREEN_D else "6 6")
        f.rect(900, sy, 156, 50, color=col, fill=WHITE, sw=2.2)
        f.text(978, sy + 31, tag, size=15, color=col, anchor="middle",
               weight="bold")
    f.text(584, 400, "两片同时低 → 两个从机一起驱动 MISO，读数互撞", size=16,
           color=RED, weight="bold")

    # ---- 下：三张分诊卡 ----
    cards = [
        ("读回全 FF（换慢时钟也一样）", BLUE_D, [
            "先查：事务期间 CS 真为低？",
            "没选中 → MISO 悬空读 1",
            "不是先降 SCK 速率",
        ]),
        ("第二条命令带出上一条尾巴", AMBER_STROKE, [
            "先查：每条事务后 CS 拉高？",
            "一直低 → 两条命令粘成一包",
            "有的从机在 CS↑ 才收下",
        ]),
        ("两片从机读数打架、随机", RED, [
            "先查：同时低了几片 CS？",
            "两片都驱动 MISO = 冲突",
            "初始化先把所有 CS 拉高",
        ]),
    ]
    for k, (head, col, lines) in enumerate(cards):
        cx = 84 + k * 340
        f.rect(cx, 436, 320, 44, color=col, fill=WHITE, sw=2.2)
        f.text(cx + 14, 465, head, size=15, color=col, weight="bold")
        f.multi(cx + 14, 510, lines, size=15.5, color=INK, lh=28)

    # ---- 底：软件 NSS 的边界 ----
    f.rect(84, 606, 984, 72, color=GREEN_D, fill=WHITE, sw=2.2)
    f.text(100, 636, "单主多从：软件 GPIO 管 CS（本章做法）；硬件 NSS 只在多主系统里出现",
           size=18, color=GREEN_D, weight="bold")
    f.text(100, 662, "PA4 还是普通推挽输出时，别再把它配成复用 NSS——两种管法只能选一种",
           size=15, color=MUTED)

    f.htext(84, 728, "口诀：先看 PA4 括号，再数同时低几片 CS；模式和速率放最后",
            size=20, color=INK, weight="bold", hl=True)
    return f


FIGS = {
    "ch08-byte-exchange": byte_exchange,
    "ch08-cs-bracket": cs_bracket,
    "ch08-cs-triage": cs_triage,
}

if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        f = FIGS[n]()
        OUT.mkdir(parents=True, exist_ok=True)
        save(f, str(OUT / (n + ".svg")))
        print("wrote", OUT / (n + ".svg"))

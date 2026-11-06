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


FIGS = {
    "ch08-byte-exchange": byte_exchange,
}

if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        f = FIGS[n]()
        OUT.mkdir(parents=True, exist_ok=True)
        save(f, str(OUT / (n + ".svg")))
        print("wrote", OUT / (n + ".svg"))

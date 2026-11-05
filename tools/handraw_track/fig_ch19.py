# -*- coding: utf-8 -*-
"""ch19 knowledge-track figure (facts from docs/19, DS5319).

The C8 has 64 KB flash ending at 0x08010000. Chapter 12's single-slot plan
(boot 16 KB + 2 KB + APP 46 KB = 64 KB) fits exactly. The online A/B dual-slot
needs a second 0xB800 image: 16 + 2 + 46 + 46 = 110 KB; slot B starts at
0x08010000 — exactly where the flash ends — and ends at 0x0801B800. A real
dual-slot design cuts the 46 KB into two 23 KB slots and shrinks the app.
"""
from hd import *


def _flash_bar(f, x, y, segs, scale):
    """segs: list of (label, kb, color); 8.6 px per KB, 62 px tall."""
    cx = x
    for label, kb, color in segs:
        seg_w = max(kb * scale, 14)
        f.rect(cx, y, seg_w, 62, color=color, fill=WHITE, sw=2.2)
        if seg_w >= 56:
            f.text(cx + seg_w / 2, y + 30, label, size=16, color=color,
                   anchor="middle", weight="bold")
        if seg_w >= 40:
            f.text(cx + seg_w / 2, y + 52, f"{kb:g}K", size=13, color=MUTED,
                   anchor="middle")
        cx += seg_w
    return cx


def ab_partition():
    f = Fig("ch19-ab-partition",
            "A/B 双分区在 C8 上算一笔账 / 64 KB of flash, count before you split")

    f.text(84, 136, "C8 的闪存到 0x08010000 为止，一共 64 KB——先按比例画出来，再看放不放得下",
           size=20, color=MUTED)

    scale = 8.6                    # px per KB：110 KB 也能画进画面
    end_x = 84 + 64 * scale        # 0x08010000 的位置

    # ---- 上：单 APP 方案 ----
    f.text(84, 176, "第 12 章的方案：只有一个 APP 槽", size=21, color=GREEN_D,
           weight="bold")
    _flash_bar(f, 84, 190, [("Boot", 16, BLUE_D), ("参数", 2, AMBER_STROKE),
                            ("APP", 46, GREEN_D)], scale)
    f.stroke([(end_x, 184), (end_x, 262)], color=INK, sw=2.4, amp=1.0)
    f.text(end_x + 10, 226, "0x08010000", size=16, color=INK)
    f.htext(84, 288, "16 + 2 + 46 = 64，正好装满", size=20, color=GREEN_D,
            weight="bold", hl=True)

    # ---- 下：A/B 双分区 ----
    f.text(84, 348, "网上的 A/B 双分区：要再放一张同样的 0xB800", size=21,
           color=RED, weight="bold")
    _flash_bar(f, 84, 362, [("Boot", 16, BLUE_D), ("参数", 2, AMBER_STROKE),
                            ("A 槽", 46, GREEN_D), ("B 槽", 46, RED)], scale)
    f.stroke([(end_x, 356), (end_x, 434)], color=INK, sw=2.4, amp=1.0)
    f.text(end_x - 8, 448, "0x08010000", size=16, color=INK, anchor="end")
    f.text(84, 462, "B 槽从 0x08010000 起步——正好从闪存的结束地址开始，直到 0x0801B800 都在片外",
           size=18, color=RED, weight="bold")
    f.htext(84, 500, "16 + 2 + 46 + 46 = 110 KB，C8 装不下", size=21,
            color=RED, weight="bold", hl=True)

    # ---- 真要双分区 ----
    f.rect(84, 528, 1008, 96, color=BLUE_D, fill=WHITE, sw=2.4)
    f.text(100, 558, "真要双分区，是另一套设计", size=21, color=BLUE_D,
           weight="bold")
    f.multi(100, 588, ["把 46 KB 切成两个 23 KB 槽，APP 也要跟着缩小",
                       "先算地址再画内存图：0x08000000 + 0x1B800 = 0x0801B800，一看越界就该停手"],
            size=18, color=INK, lh=27)

    f.text(84, 672, "闪存容量与结束地址按 DS5319 的存储器表；第 12 章的单槽方案见该章正文", size=17,
           color=MUTED)
    return f


FIGS = {
    "ch19-ab-partition": ab_partition,
}

if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        f = FIGS[n]()
        OUT.mkdir(parents=True, exist_ok=True)
        save(f, str(OUT / (n + ".svg")))
        print("wrote", OUT / (n + ".svg"))

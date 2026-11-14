# -*- coding: utf-8 -*-
"""heap_4 free-list plate (ch25).

Pinned to the chapter: ucHeap is 16 KB in this lab; each block carries an
8 B BlockLink_t header and no footer; xFreeList is address-ordered; release
coalesces only address-adjacent free blocks; heap_4 exposes free size, minimum
ever free, and heap stats including the largest free block.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hd import *  # noqa: E402,F401,F403


def _block(f, x, y, w, h, label, sub, color, fill):
    f.rect(x, y, w, h, color=color, fill=fill, sw=2.2)
    f.text(x + 12, y + 52, label, size=19, color=color, weight="bold")
    f.text(x + 12, y + 76, sub, size=15, color=MUTED)
    # 8 B header cap
    f.fillrect(x + 8, y + 10, 46, 22, INK, r=2)
    f.text(x + 12, y + 26, "8 B", size=13, color=PAPER, halo=False)


def heap_free_list():
    f = Fig("arch-heap-free-list",
            "heap_4 的账本 / address order + coalesce")

    # ---- heap strip -------------------------------------------------
    hx, hy, hw, hh = 48, 124, 1056, 174
    f.rect(hx, hy, hw, hh, color=AMBER_STROKE, fill=PAPER, sw=3.0)
    f.text(hx + 16, hy + 30, "ucHeap（示意）：A/B/C 各 1 KB，尾块 1 KB", size=21,
           color=AMBER_STROKE, weight="bold")
    bx, by, bh = hx + 16, hy + 50, 100
    blocks = [
        (230, "A · used", "1 KB", GREEN_D, WHITE),
        (230, "B · used", "1 KB", GREEN_D, WHITE),
        (230, "C · used", "1 KB", GREEN_D, WHITE),
        (230, "尾块", "free 1 KB", BLUE_D, GRAY_FILL),
    ]
    for w, label, sub, c, fill in blocks:
        _block(f, bx, by, w, bh, label, sub, c, fill)
        bx += w

    # ---- two release scenarios -------------------------------------
    lx, ly, lw, lh = 48, 328, 512, 196
    f.rect(lx, ly, lw, lh, color=RED, fill=WHITE, sw=2.8)
    f.htext(lx + 16, ly + 32, "释放 B：只多一个洞", size=23, color=RED,
            weight="bold")
    # four cells: A used / B hole / C used / tail hole
    f.rect(lx + 20, ly + 54, 112, 56, color=GREEN_D, fill=WHITE, sw=2.0)
    f.text(lx + 32, ly + 78, "A used", size=18, color=GREEN_D)
    f.text(lx + 32, ly + 100, "1 KB", size=15, color=MUTED)
    f.rect(lx + 132, ly + 54, 112, 56, color=BLUE_D, fill=GRAY_FILL, sw=2.0)
    f.text(lx + 144, ly + 78, "B 洞", size=18, color=BLUE_D)
    f.text(lx + 144, ly + 100, "刚释放", size=15, color=MUTED)
    f.rect(lx + 244, ly + 54, 112, 56, color=GREEN_D, fill=WHITE, sw=2.0)
    f.text(lx + 256, ly + 78, "C used", size=18, color=GREEN_D)
    f.text(lx + 256, ly + 100, "挡在中间", size=15, color=MUTED)
    f.rect(lx + 356, ly + 54, 112, 56, color=BLUE_D, fill=GRAY_FILL, sw=2.0)
    f.text(lx + 368, ly + 78, "尾洞", size=18, color=BLUE_D)
    f.text(lx + 368, ly + 100, "free", size=15, color=MUTED)
    f.text(lx + 20, ly + 140,
           "B 洞与尾洞隔着 C：不并。", size=18, color=INK)
    f.text(lx + 20, ly + 170,
           "总空闲够，最大连续块不够 → 2 KB 失败。", size=17, color=RED)

    rx, ry, rw, rh = 588, 328, 516, 196
    f.rect(rx, ry, rw, rh, color=GREEN_D, fill=WHITE, sw=2.8)
    f.htext(rx + 16, ry + 32, "再释放 A：相邻才并", size=23, color=GREEN_D,
            weight="bold")
    f.rect(rx + 20, ry + 54, 220, 56, color=GREEN_D, fill=WHITE, sw=2.2)
    f.text(rx + 34, ry + 78, "A + B 洞", size=18, color=GREEN_D,
           weight="bold")
    f.text(rx + 34, ry + 100, "2 KB 可用", size=15, color=MUTED)
    f.rect(rx + 240, ry + 54, 120, 56, color=GREEN_D, fill=WHITE, sw=2.0)
    f.text(rx + 254, ry + 78, "C used", size=18, color=GREEN_D)
    f.text(rx + 254, ry + 100, "仍隔开", size=15, color=MUTED)
    f.rect(rx + 360, ry + 54, 120, 56, color=BLUE_D, fill=GRAY_FILL, sw=2.0)
    f.text(rx + 374, ry + 78, "尾洞", size=18, color=BLUE_D)
    f.text(rx + 374, ry + 100, "free 1 KB", size=15, color=MUTED)
    f.text(rx + 20, ry + 140,
           "A 与 B 洞焊成 2 KB 可用，请求从同一链表取到。", size=17, color=GREEN_D)
    f.text(rx + 20, ry + 170,
           "合并块含两头 8 B 头，装得下 2 KB 负载。", size=17, color=MUTED)

    # ---- address-ordered list + metrics ----------------------------
    cx, cy, cw, ch = 48, 552, 1056, 162
    f.rect(cx, cy, cw, ch, color=BLUE_D, fill=PAPER, sw=3.0)
    f.text(cx + 16, cy + 30, "xFreeList：按地址升序，不是按大小", size=21,
           color=BLUE_D, weight="bold")
    # chain
    nx, ny = cx + 20, cy + 50
    for i, (addr, size) in enumerate((("块 A（低）", "1 KB"),
                                      ("块 B（中）", "1 KB"),
                                      ("块 C（高）", "2 KB"))):
        f.rect(nx, ny, 142, 54, color=BLUE_D, fill=WHITE, sw=2.0)
        f.text(nx + 10, ny + 22, addr, size=15, color=BLUE_D)
        f.text(nx + 10, ny + 43, size, size=15, color=INK)
        if i < 2:
            f.arrow(nx + 144, ny + 27, nx + 168, ny + 27, color=BLUE,
                    sw=1.9, bend=0.0)
        nx += 170
    f.text(cx + 20, cy + 130,
           "释放时按地址遍历找插入点；前邻/后邻各一次指针比较。", size=16,
           color=MUTED)

    # metrics
    mx = cx + 610
    f.text(mx, cy + 54, "三个读数", size=18, color=AMBER_STROKE, weight="bold")
    f.text(mx, cy + 82, "xPortGetFreeHeapSize → 当前总空闲", size=16, color=INK)
    f.text(mx, cy + 108, "xPortGetMinimumEverFreeHeapSize → 历史最低", size=16,
           color=INK)
    f.text(mx, cy + 134, "vPortGetHeapStats → 最大连续块（仅 heap_4）", size=16,
           color=INK)

    # ---- closing ----------------------------------------------------
    f.htext(576, 750, "两个洞隔着一块 used：永远各留各的；相邻才焊得成一片。",
            size=23, color=AMBER_STROKE, anchor="middle", weight="bold",
            hl=True, hl_fill=AMBER_FILL)
    return f


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[2] / "assets" / "illustrations" / "handraw"
    save(heap_free_list(), str(out / "arch-heap-free-list.svg"))
    print("wrote arch-heap-free-list.svg")

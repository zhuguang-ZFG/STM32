# -*- coding: utf-8 -*-
"""FreeRTOS scheduler structures plate (ch22).

Facts pinned to the chapter: pxReadyTasksLists[configMAX_PRIORITIES] is an
array of List_t; ready insertion is vListInsertEnd (tail), selection takes the
next entry (round-robin within a priority); the delayed list uses vListInsert
ordered by xItemValue (wake tick); xTaskIncrementTick compares
xNextTaskUnblockTime, pops due heads, re-adds them to the ready lists.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hd import *  # noqa: E402,F401,F403


def _card(f, x, y, w, h, title, lines, color, size=22, body=18):
    f.rect(x, y, w, h, color=color, fill=WHITE, sw=2.3)
    f.htext(x + 16, y + size + 8, title, size=size, color=color,
            weight="bold")
    for i, ln in enumerate(lines):
        f.text(x + 16, y + size + 42 + i * (body * 1.45), ln,
               size=body, color=INK)


def scheduler_structs():
    f = Fig("arch-scheduler-structs",
            "调度器三件事 / ready, delayed, tick")

    # ---- left: highest-ready shortcut -------------------------------
    lx, ly, lw, lh = 48, 122, 500, 330
    f.rect(lx, ly, lw, lh, color=AMBER_STROKE, fill=PAPER, sw=3.0)
    f.htext(lx + 18, ly + 38, "速查器：谁下一个上", size=26,
            color=AMBER_STROKE, weight="bold")
    _card(f, lx + 18, ly + 58, lw - 36, 122,
          "位图 + CLZ（ARM_CM4F 默认）",
          ["每位一个优先级；31 − CLZ 取最高位",
           "0x0020_0008 → bit 21 → 选 21 级"],
          GREEN_D, size=21, body=18)
    _card(f, lx + 18, ly + 194, lw - 36, 118,
          "标量递减（通用路径）",
          ["从 uxTopReadyPriority 逐级下扫",
           "最坏 O(configMAX_PRIORITIES)"],
          BLUE_D, size=21, body=18)

    # ---- right top: ready array ------------------------------------
    rx, ry, rw, rh = 580, 122, 524, 154
    f.rect(rx, ry, rw, rh, color=GREEN_D, fill=WHITE, sw=3.0)
    f.text(rx + 16, ry + 30, "就绪表 pxReadyTasksLists[5]", size=22,
           color=GREEN_D, weight="bold")
    f.text(rx + 16, ry + 54, "每个优先级一条 List_t；尾插，从上次位置的下一个取", size=16,
           color=MUTED)
    bx = rx + 28
    slots = ("—", "—", "T1", "T2", "—")
    for prio, slot in zip((4, 3, 2, 1, 0), slots):
        f.rect(bx, ry + 66, 78, 58, color=GREEN_D, fill=PAPER, sw=2.0)
        f.text(bx + 8, ry + 86, f"prio {prio}", size=15, color=GREEN_D)
        f.text(bx + 8, ry + 110, slot, size=18,
               color=INK if slot != "—" else MUTED)
        bx += 94
    f.arrow(rx + 28, ry + 142, rx + 376, ry + 142, color=GREEN,
            sw=2.2, bend=0.0)
    f.text(rx + 400, ry + 147, "轮转取", size=16, color=GREEN_D)

    # ---- right bottom: delayed list --------------------------------
    dx, dy, dw, dh = 580, 292, 524, 160
    f.rect(dx, dy, dw, dh, color=BLUE_D, fill=WHITE, sw=3.0)
    f.text(dx + 16, dy + 30, "延时表：按值排序的兄弟", size=22,
           color=BLUE_D, weight="bold")
    f.text(dx + 16, dy + 54, "vListInsert 按 xItemValue（唤醒 tick）升序", size=17,
           color=MUTED)
    xs = dx + 24
    for i, (name, tick) in enumerate((("T3", "10"), ("T4", "20"), ("T5", "30"))):
        f.rect(xs, dy + 72, 132, 54, color=BLUE_D, fill=PAPER, sw=2.0)
        f.text(xs + 10, dy + 95, name, size=18, color=BLUE_D, weight="bold")
        f.text(xs + 48, dy + 95, f"@{tick}", size=18, color=INK)
        f.text(xs + 10, dy + 117, "xItemValue", size=14, color=MUTED)
        if i < 2:
            f.arrow(xs + 134, dy + 99, xs + 164, dy + 99, color=BLUE,
                    sw=2.0, bend=0.0)
        xs += 166
    f.text(dx + 16, dy + 146, "队首最早醒；tick 只看队首", size=17,
           color=BLUE_D)

    # ---- bottom: tick loop -----------------------------------------
    tx, ty, tw, th = 48, 498, 1056, 196
    f.rect(tx, ty, tw, th, color=AMBER_STROKE, fill=PAPER, sw=3.0)
    f.text(tx + 18, ty + 34, "tick 中断 xTaskIncrementTick：三段", size=24,
           color=AMBER_STROKE, weight="bold")
    _card(f, tx + 18, ty + 54, 242, 112, "① 节拍++",
          ["xTickCount++", "1 kHz = 每毫秒一次"], BLUE_D, size=20, body=17)
    _card(f, tx + 292, ty + 54, 300, 112, "② 剪枝：先看时刻",
          ["未到 xNextTaskUnblockTime", "整段延时检查跳过"],
          GREEN_D, size=20, body=17)
    _card(f, tx + 624, ty + 54, 414, 112, "③ 到期：搬家 + 请求切换",
          ["摘延时队首 → 挂回就绪表", "更高/同优先级轮转 → 返回 pdTRUE"],
          RED, size=20, body=17)
    f.arrow(tx + 262, ty + 110, tx + 288, ty + 110, color=INK, sw=2.2,
            bend=0.0)
    f.arrow(tx + 596, ty + 110, tx + 620, ty + 110, color=INK, sw=2.2,
            bend=0.0)
    f.arrow(842, dy + dh + 4, 842, ty + 54, color=BLUE, sw=2.2, bend=0.0)
    f.text(854, dy + dh + 30, "到期才搬", size=16, color=BLUE_D)

    # ---- closing line ----------------------------------------------
    f.htext(576, 720, "就绪表尾插 + 上次位置的下一个取 = 同优先级轮转；延时表按值插入 = 队首最早醒。",
            size=24, color=AMBER_STROKE, anchor="middle", weight="bold",
            hl=True, hl_fill=AMBER_FILL)
    f.text(576, 758, "vTaskDelay 不是原地等，是把任务从就绪表搬到延时表。",
           size=19, color=RED, anchor="middle")
    return f


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[2] / "assets" / "illustrations" / "handraw"
    save(scheduler_structs(), str(out / "arch-scheduler-structs.svg"))
    print("wrote arch-scheduler-structs.svg")

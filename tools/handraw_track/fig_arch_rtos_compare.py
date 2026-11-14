# -*- coding: utf-8 -*-
"""FreeRTOS vs RT-Thread migration-danger plate (ch27).

Facts pinned to the chapter: FreeRTOS priority values grow upward (big = high),
RT-Thread 0 is highest, NVIC small = high; FreeRTOS levels come from
configMAX_PRIORITIES (lab 5) and the CM4F bitmap path caps at 32; RT-Thread
defaults to 32 with 8/32/256 options and switches from single-level to
two-level bitmap above 32. Queue/message-queue and notification semantics are
not equivalent by name.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hd import *  # noqa: E402,F401,F403


def _scale(f, y, name, left, right, color, mark=None, mark_label=""):
    f.text(74, y - 10, name, size=20, color=color, weight="bold")
    f.line(250, y, 620, y, color=color, sw=2.8, amp=1.0)
    f.arrowhead(620, y, 1, 0, color=color, head=9)
    f.text(250, y + 26, left, size=16, color=MUTED)
    f.text(620, y + 26, right, size=16, color=MUTED, anchor="end")
    if mark is not None:
        f.circle(mark, y, 8, color=RED, sw=2.4, fill=WHITE)
        f.text(mark, y - 16, mark_label, size=15, color=RED, anchor="middle",
               weight="bold")


def rtos_compare():
    f = Fig("arch-rtos-side-by-side",
            "FreeRTOS ↔ RT-Thread / same question, new coordinates")

    # priority scales
    px, py, pw, ph = 48, 120, 650, 300
    f.rect(px, py, pw, ph, color=AMBER_STROKE, fill=PAPER, sw=3.0)
    f.htext(px + 16, py + 34, "优先级：三套坐标", size=25,
            color=AMBER_STROKE, weight="bold")
    f.text(px + 18, py + 62, "同一个数字 5，在三张 32 级坐标里高度不同。", size=17,
           color=MUTED)
    _scale(f, py + 112, "FreeRTOS", "0 = 低", "数值大 = 高", GREEN_D,
           mark=px + 190, mark_label="5")
    _scale(f, py + 188, "RT-Thread", "31 = 低", "0 = 高（数值小）", BLUE_D,
           mark=px + 520, mark_label="5")
    _scale(f, py + 264, "NVIC", "15 = 低", "0 = 高（数值小）", RED,
           mark=px + 520, mark_label="5")

    # level counts
    rx, ry, rw, rh = 728, 120, 376, 300
    f.rect(rx, ry, rw, rh, color=BLUE_D, fill=WHITE, sw=3.0)
    f.htext(rx + 16, ry + 34, "级别数量：都别写死", size=23,
            color=BLUE_D, weight="bold")
    f.text(rx + 18, ry + 84, "FreeRTOS", size=19, color=GREEN_D,
           weight="bold")
    f.text(rx + 18, ry + 110, "configMAX_PRIORITIES 决定；", size=16, color=INK)
    f.text(rx + 18, ry + 132, "lab 只有 0–4；CM4F ≤ 32。", size=16,
           color=INK)
    f.text(rx + 18, ry + 178, "RT-Thread", size=19, color=BLUE_D,
           weight="bold")
    f.text(rx + 18, ry + 204, "默认 32；可配 8/32/256。", size=16, color=INK)
    f.text(rx + 18, ry + 226, "≤32 单级位图，>32 才二级位图。", size=16,
           color=INK)
    f.text(rx + 18, ry + 268, "别把可配置项写成固定规格。", size=16,
           color=RED)

    # semantic traps
    tx, ty, tw, th = 48, 448, 1056, 190
    f.rect(tx, ty, tw, th, color=GREEN_D, fill=WHITE, sw=3.0)
    f.htext(tx + 16, ty + 34, "名字相近，语义不等价", size=24,
            color=GREEN_D, weight="bold")
    rows = [
        ("队列", "创建时定死项宽", "槽宽固定，实发长度可短", "都不是“变长队列”"),
        ("轻量通知", "任务通知（写 TCB 字段）", "无直接等价，sem/event 替代", "别按名字对号入座"),
        ("设备/配置", "无内置驱动模型；FreeRTOSConfig.h", "rt_device；Kconfig + scons", "工程形态不同"),
    ]
    yy = ty + 62
    for role, a, b, c in rows:
        f.text(tx + 18, yy + 18, role, size=17, color=GREEN_D, weight="bold")
        f.text(tx + 130, yy + 18, a, size=15, color=INK)
        f.text(tx + 470, yy + 18, b, size=15, color=INK)
        f.text(tx + 820, yy + 18, c, size=15, color=RED)
        f.line(tx + 18, yy + 34, tx + 1038, yy + 34, color=GRAY_FILL,
               sw=1.3, amp=0.4)
        yy += 42

    f.htext(576, 696, "选型不是排行榜：方向、数量、语义都带条件。",
            size=24, color=AMBER_STROKE, anchor="middle", weight="bold",
            hl=True, hl_fill=AMBER_FILL)
    f.text(576, 738, "先查合法范围，再按任务的相对顺序映射；lab 只有 0–4。",
           size=17, color=RED, anchor="middle")
    return f


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[2] / "assets" / "illustrations" / "handraw"
    save(rtos_compare(), str(out / "arch-rtos-side-by-side.svg"))
    print("wrote arch-rtos-side-by-side.svg")

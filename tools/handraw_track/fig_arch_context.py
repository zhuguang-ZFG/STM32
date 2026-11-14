# -*- coding: utf-8 -*-
"""PendSV hardware/software split plate (ch23).

Pinned to the chapter: hardware stacks 8 core words (R0-R3, R12, LR, PC,
xPSR); PendSV stores 9 words (R4-R11 + EXC_RETURN), writes the new top to
TCB offset 0, switches pxCurrentTCB, then restores and bx r14. First frame is
18 words = 72 B; EXC_RETURN 0xFFFFFFFD has bit4=1 (no FPU luggage).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hd import *  # noqa: E402,F401,F403


def context_switch():
    f = Fig("arch-context-switch", "PendSV 软硬分工 / 8 + 9 words")

    # ---- hardware frame --------------------------------------------
    ax, ay, aw, ah = 48, 124, 512, 236
    f.rect(ax, ay, aw, ah, color=AMBER_STROKE, fill=PAPER, sw=3.0)
    f.htext(ax + 18, ay + 38, "① 硬件自动压 8 字", size=26,
            color=AMBER_STROKE, weight="bold")
    f.text(ax + 20, ay + 82, "R0  R1  R2  R3  R12  LR  PC  xPSR", size=24,
           color=INK, weight="bold")
    f.text(ax + 20, ay + 116, "异常入场时压进当前任务的 PSP 栈", size=19,
           color=MUTED)
    f.rect(ax + 20, ay + 142, 300, 52, color=AMBER_STROKE, fill=WHITE, sw=2.0)
    f.text(ax + 36, ay + 176, "线程态 SPSEL=1 → 压 PSP", size=17,
           color=AMBER_STROKE)
    f.text(ax + 20, ay + 224, "不用写一行汇编。", size=18, color=GREEN_D)

    # ---- software frame --------------------------------------------
    bx, by, bw, bh = 592, 124, 512, 236
    f.rect(bx, by, bw, bh, color=BLUE_D, fill=PAPER, sw=3.0)
    f.htext(bx + 18, by + 38, "② PendSV 补 9 字", size=26,
            color=BLUE_D, weight="bold")
    f.text(bx + 20, by + 82, "stmdb r0!, {r4-r11, r14}", size=24,
           color=INK, weight="bold")
    f.text(bx + 20, by + 116, "= R4–R11 + EXC_RETURN = 36 B", size=19,
           color=BLUE_D)
    f.text(bx + 20, by + 148, "str r0, [r2] → TCB 偏移 0", size=19,
           color=INK)
    f.text(bx + 20, by + 182, "少存 EXC_RETURN，ldmia 偏移全错位", size=18,
           color=RED)
    f.text(bx + 20, by + 220, "软件帧 9 字，不是 8 字。", size=18, color=MUTED)

    # ---- TCB switch + restore --------------------------------------
    cx, cy, cw, ch = 48, 398, 1056, 252
    f.rect(cx, cy, cw, ch, color=GREEN_D, fill=WHITE, sw=3.0)
    f.text(cx + 18, cy + 34, "③ 换 TCB，再倒着放回去", size=24,
           color=GREEN_D, weight="bold")

    # two TCBs
    f.rect(cx + 24, cy + 58, 250, 86, color=GREEN_D, fill=PAPER, sw=2.2)
    f.text(cx + 40, cy + 86, "TCB A", size=22, color=GREEN_D, weight="bold")
    f.text(cx + 40, cy + 114, "pxTopOfStack → 栈顶", size=17, color=INK)
    f.text(cx + 40, cy + 136, "软件 9 + 硬件 8", size=16, color=MUTED)

    f.arrow(cx + 290, cy + 100, cx + 500, cy + 100, color=BLUE, sw=2.6,
            bend=-0.05)
    f.text(cx + 300, cy + 76, "vTaskSwitchContext", size=17, color=BLUE_D,
           weight="bold")
    f.text(cx + 300, cy + 128, "只改 pxCurrentTCB", size=16, color=MUTED)

    f.rect(cx + 520, cy + 58, 250, 86, color=GREEN_D, fill=PAPER, sw=2.2)
    f.text(cx + 536, cy + 86, "TCB B", size=22, color=GREEN_D, weight="bold")
    f.text(cx + 536, cy + 114, "pxTopOfStack → 栈顶", size=17, color=INK)
    f.text(cx + 536, cy + 136, "先弹 9、写 PSP，再 bx r14", size=14, color=MUTED)

    # restore chain
    ys = cy + 168
    f.text(cx + 24, ys + 18, "ldr r0,[r1]", size=19, color=BLUE_D)
    f.arrow(cx + 160, ys + 12, cx + 196, ys + 12, color=INK, sw=2.0, bend=0.0)
    f.text(cx + 210, ys + 18, "ldmia r0!, {r4-r11,r14}", size=17, color=BLUE_D)
    f.arrow(cx + 446, ys + 12, cx + 470, ys + 12, color=INK, sw=2.0, bend=0.0)
    f.text(cx + 482, ys + 18, "msr psp, r0", size=17, color=BLUE_D)
    f.arrow(cx + 600, ys + 12, cx + 624, ys + 12, color=INK, sw=2.0, bend=0.0)
    f.text(cx + 636, ys + 18, "bx r14", size=18, color=BLUE_D)
    f.arrow(cx + 710, ys + 12, cx + 734, ys + 12, color=INK, sw=2.0, bend=0.0)
    f.text(cx + 746, ys + 18, "硬件按 EXC_RETURN 弹 8 字", size=17, color=GREEN_D)

    f.text(cx + 24, cy + ch - 16,
           "首帧 18 字 = 72 B；EXC_RETURN = 0xFFFFFFFD，bit4=1 → 首帧没有 FPU 行李。",
           size=17, color=MUTED)

    # ---- FPU strip --------------------------------------------------
    f.htext(576, 700, "有 FPU：硬件 26 字 + 软件 25 字（9 + 16）= 51 字。",
            size=23, color=AMBER_STROKE, anchor="middle", weight="bold",
            hl=True, hl_fill=AMBER_FILL)
    f.text(576, 742, "26 字是扩展帧；9 字软件帧始终在，别只算 16 字高寄存器。",
           size=17, color=RED, anchor="middle")
    return f


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[2] / "assets" / "illustrations" / "handraw"
    save(context_switch(), str(out / "arch-context-switch.svg"))
    print("wrote arch-context-switch.svg")

# -*- coding: utf-8 -*-
"""Linker-script contracts plate (ch06): MEMORY regions, SECTIONS rooms,
and the .data double home. Facts follow stm32f407xx.ld as quoted in ch06.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hd import *  # noqa: E402,F401,F403


def _room(f, x, y, w, h, name, note, color, size=23):
    f.rect(x, y, w, h, color=color, fill=WHITE, sw=2.3)
    f.htext(x + 16, y + size + 4, name, size=size, color=color,
            weight="bold")
    f.text(x + 16, y + size + 34, note, size=19, color=INK)


def linker_map():
    f = Fig("arch-linker-map", "链接脚本先圈地，再分房 / regions, then rooms")

    # contract strip
    f.rect(64, 122, 1024, 88, color=INK, fill=WHITE, sw=2.2)
    f.text(86, 160, "ENTRY(Reset_Handler)", size=21, color=INK)
    f.text(360, 160, "_estack = 0x20020000", size=21, color=BLUE_D)
    f.text(676, 160, "_Min_Heap_Size = 0x200", size=21, color=AMBER_STROKE)
    f.text(86, 192, "_Min_Stack_Size = 0x400", size=21, color=RED)
    f.text(676, 192, "两份预算写进 ._user_heap_stack", size=19, color=MUTED)

    # flash region
    fx, fy, fw, fh = 56, 242, 420, 380
    f.rect(fx, fy, fw, fh, color=GREEN_D, fill=PAPER, sw=3.0)
    f.htext(fx + 18, fy + 36, "FLASH (rxa) · 1 MB", size=27, color=GREEN_D,
            weight="bold")
    f.text(fx + 18, fy + 62, "ORIGIN = 0x0800_0000", size=19, color=MUTED)
    rooms = [
        (".isr_vector", "KEEP：硬件读，GC 看不见", GREEN_D),
        (".text", "指令；.rodata 并入", GREEN_D),
        (".data 初值", "LMA：随固件躺在 Flash", AMBER_STROKE),
    ]
    by = fy + 82
    for name, note, c in rooms:
        _room(f, fx + 18, by, fw - 36, 88, name, note, c)
        by += 96
    f.text(fx + 18, fy + fh - 20, "收尾：_sidata 指向这里的初值副本",
           size=18, color=MUTED)

    # ram region
    sx, sy, sw, sh = 676, 242, 420, 380
    f.rect(sx, sy, sw, sh, color=BLUE_D, fill=PAPER, sw=3.0)
    f.htext(sx + 18, sy + 36, "RAM (xrw) · 128 KB", size=27, color=BLUE_D,
            weight="bold")
    f.text(sx + 18, sy + 62, "ORIGIN = 0x2000_0000", size=19, color=MUTED)
    rooms = [
        (".data 本体", "VMA：Reset_Handler 搬进来", AMBER_STROKE),
        (".bss", "NOBITS：文件里一个字节都没有", BLUE_D),
        ("heap 0x200 →", "_ebss 之后向上长", BLUE_D),
        ("← stack 0x400", "从 _estack 向下长", RED),
    ]
    by = sy + 82
    for name, note, c in rooms:
        _room(f, sx + 18, by, sw - 36, 66, name, note, c, size=21)
        by += 72

    # double home
    f.arrow(fx + fw + 6, 700 - 80, sx - 6, 340, color=AMBER_STROKE,
            sw=3.0, bend=0.02)
    f.text(576, 392, ">RAM AT> FLASH", size=19, color=AMBER_STROKE,
           anchor="middle", weight="bold")
    f.text(576, 418, "同一段，两个地址", size=17, color=MUTED,
           anchor="middle")

    # bottom
    f.htext(576, 690, "MEMORY 圈地，SECTIONS 分房；AT> 给 .data 第二个住址。",
            size=25, color=AMBER_STROKE, anchor="middle", weight="bold",
            hl=True, hl_fill=AMBER_FILL)
    f.text(576, 734,
           "少一句 KEEP，向量表会被 --gc-sections 收走；ld 不报错，固件一上电就死。",
           size=20, color=RED, anchor="middle")
    return f


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[2] / "assets" / "illustrations" / "handraw"
    save(linker_map(), str(out / "arch-linker-map.svg"))
    print("wrote arch-linker-map.svg")

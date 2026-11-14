# -*- coding: utf-8 -*-
"""Cross-toolchain pipeline plate (ch05): source -> ELF -> binary -> Flash."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hd import *  # noqa: E402,F401,F403


def _card(f, x, y, w, h, head, lines, color, size=21):
    f.rect(x, y, w, h, color=color, fill=WHITE, sw=2.4)
    f.htext(x + w / 2, y + 38, head, size=size, color=color,
            anchor="middle", weight="bold")
    f.multi(x + 14, y + 76, lines, size=17, color=INK, lh=23)


def toolchain():
    f = Fig("arch-toolchain-pipeline",
            "从 main.c 到 Flash：两条车道 / host builds, target runs")

    # host lane
    f.htext(46, 132, "宿主机 · build = host = x86-64", size=24,
            color=GREEN_D, weight="bold")
    top = [
        ("main.c", ["C 源码", "输入"], GREEN_D),
        ("arm-none-eabi-gcc", ["预处理 · 编译", "汇编"], BLUE_D),
        ("main.o", ["可重定位目标", "地址还没定"], BLUE_D),
        ("arm-none-eabi-ld", ["读 main.ld", "定地址与段"], AMBER_STROKE),
        ("blink.elf", ["完整映像", "带符号与段表"], GREEN_D),
    ]
    cw, gap, x0, y0, ch = 190, 18, 46, 168, 186
    for i, (head, lines, color) in enumerate(top):
        x = x0 + i * (cw + gap)
        _card(f, x, y0, cw, ch, head, lines, color,
              size=18 if len(head) > 8 else 21)
        if i < len(top) - 1:
            f.arrow(x + cw + 2, y0 + 92, x + cw + gap - 3, y0 + 92,
                    color=BLUE, sw=2.4, bend=0.03, head=8)

    # down to the binary
    ex = x0 + 4 * (cw + gap) + cw / 2
    f.arrow(ex, y0 + ch + 4, ex, 476, color=AMBER_STROKE, sw=2.6,
            bend=0.0, head=9)
    f.text(ex + 14, 430, "objcopy", size=18, color=AMBER_STROKE,
           weight="bold")

    # target lane, flowing right to left
    f.htext(60, 500, "目标板 · target = arm", size=24, color=BLUE_D,
            weight="bold")
    bottom = [
        ("blink.bin", ["纯二进制", "丢掉符号与段表"], AMBER_STROKE),
        ("OpenOCD", ["烧录 / 调试服务器", "听 TCP 3333"], BLUE_D),
        ("ST-Link", ["USB ↔ SWD", "探针"], BLUE_D),
        ("STM32F407", ["Cortex-M4 · 168 MHz", "Flash 0x0800_0000"], RED),
    ]
    bw, bgap = 210, 24
    xs = [762, 528, 294, 60]
    by, bh = 536, 160
    for i, (head, lines, color) in enumerate(bottom):
        x = xs[i]
        _card(f, x, by, bw, bh, head, lines, color,
              size=19 if len(head) > 8 else 21)
        if i < len(bottom) - 1:
            f.arrow(x - 3, by + 85, xs[i + 1] + bw + 3, by + 85,
                    color=color, sw=2.4, bend=-0.03, head=8)

    # one reading rule and one tool boundary
    f.htext(W / 2, 748,
            "ld 定地址，objcopy 换格式：烧进 Flash 的 bin 不带符号与段表。",
            size=23, color=AMBER_STROKE, anchor="middle", weight="bold",
            hl=True, hl_fill=AMBER_FILL)

    return f


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[2] / "assets" / "illustrations" / "handraw"
    save(toolchain(), str(out / "arch-toolchain-pipeline.svg"))
    print("wrote arch-toolchain-pipeline.svg")

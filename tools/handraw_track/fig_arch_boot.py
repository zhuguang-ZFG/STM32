# -*- coding: utf-8 -*-
"""Reset_Handler five-station plate (ch06): boot sequence before main.

Facts: the first two reads are hardware (vector table word 0 = MSP, word 1 =
Reset_Handler); the rest run inside Reset_Handler in assembly, then `bl main`.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hd import *  # noqa: E402,F401,F403


def boot_sequence():
    f = Fig("arch-boot-sequence", "Reset_Handler 的五站 / five stations before main")

    stations = [
        ("① 硬件两读", ["第 0 字 → MSP", "第 1 字 → 复位入口"], GREEN_D),
        ("② 开 FPU", ["CPACR：CP10/11", "F407 才有这一站"], AMBER_STROKE),
        ("③ 搬 .data", ["_sidata → RAM", ".data 初值"], AMBER_STROKE),
        ("④ 清 .bss", ["_sbss.._ebss 写 0", "不占 Flash"], BLUE_D),
        ("⑤ bl main", ["进 C 世界", "main 不返回"], RED),
    ]

    cw, gap = 188, 22
    x0 = (W - (cw * 5 + gap * 4)) / 2
    y0 = 200
    for i, (head, lines, color) in enumerate(stations):
        x = x0 + i * (cw + gap)
        f.rect(x, y0, cw, 170, color=color, fill=WHITE, sw=2.4)
        f.htext(x + cw / 2, y0 + 42, head, size=22, color=color,
                anchor="middle", weight="bold")
        f.multi(x + 16, y0 + 92, lines, size=18, color=INK, lh=25)
        if i < 4:
            f.arrow(x + cw + 2, y0 + 85, x + cw + gap - 3, y0 + 85,
                    color=color, sw=2.4, bend=0.0, head=8)

    # two truths that readers routinely invert
    f.htext(W / 2, 470,
            "前两读由硬件完成：复位时 C 运行时还不存在，没有代码去“读”向量表。",
            size=25, color=GREEN_D, anchor="middle", weight="bold",
            hl=True, hl_fill=AMBER_FILL)
    f.text(W / 2, 520,
           "③④ 是汇编里的搬运与清零；地址符号 _sidata/_sdata/_sbss 由链接脚本给出。",
           size=22, color=INK, anchor="middle")
    f.text(W / 2, 558,
           "⑤ 之后才进 main；main 返回没有调用者，固件通常 while(1) 或复位。",
           size=22, color=MUTED, anchor="middle")
    f.text(W / 2, 610,
           "F103 没有 FPU，② 这一站不存在；同一份启动思路，站点数随内核变。",
           size=20, color=MUTED, anchor="middle")
    return f


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[2] / "assets" / "illustrations" / "handraw"
    save(boot_sequence(), str(out / "arch-boot-sequence.svg"))
    print("wrote arch-boot-sequence.svg")

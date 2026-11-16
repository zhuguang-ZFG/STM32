# -*- coding: utf-8 -*-
"""Reconciliation gate plate (ch44): three questions, then evidence feedback.

Facts pinned to the chapter: the AI claim "GPIOF clock needs RCC_APB1ENR bit5"
fails the name check (bit5 there is TIM7EN), passes the bit-number check
(GPIOFEN is AHB1ENR bit5), and passes the order check. A correction needs the
three-part feedback (measurement + manual citation + board fact); an apology
alone does not move the sampling distribution.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hd import *  # noqa: E402,F401,F403


def reconcile_gates():
    f = Fig("arch-reconcile-gates", "一条断言过三关")

    f.rect(48, 118, 1056, 96, color=BLUE_D, fill=WHITE, sw=2.6)
    f.text(64, 148, "AI 断言：", size=15, color=MUTED)
    f.text(64, 180, "「开 GPIOF 时钟要置 RCC_APB1ENR bit5」", size=21,
           color=BLUE_D, weight="bold")

    gates = [
        (48, "① 名：寄存器名", ["RCC_APB1ENR bit5", "实际是 TIM7EN",
                              "不是 GPIOFEN"], "✗ 张冠李戴", RED),
        (416, "② 位：位号", ["GPIOFEN 在", "RCC_AHB1ENR bit5",
                            "位号 5 碰巧对"], "✓ 位号对", GREEN_D),
        (784, "③ 序：顺序", ["先开 GPIO 时钟", "再写 GPIO 寄存器",
                            "这个序说对了"], "✓ 顺序对", GREEN_D),
    ]
    for x, title, lines, verdict, c in gates:
        f.rect(x, 232, 320, 200, color=c, fill=WHITE, sw=2.6)
        f.htext(x + 16, 266, title, size=20, color=c, weight="bold")
        for i, ln in enumerate(lines):
            f.text(x + 16, 304 + i * 28, ln, size=18 if i == 1 else 15,
                   color=INK if i != 1 else c, weight="bold" if i == 1
                   else "normal")
        f.text(x + 16, 410, verdict, size=21, color=c, weight="bold")
    f.arrow(368, 332, 410, 332, color=INK, sw=2.0, bend=0.0)
    f.arrow(736, 332, 778, 332, color=INK, sw=2.0, bend=0.0)

    f.text(64, 462,
           "一条输出三问全过才算过；雷 1 是「位对、名错」，单看位号会漏判。",
           size=16, color=RED)

    f.rect(48, 486, 1056, 160, color=AMBER_STROKE, fill=WHITE, sw=2.6)
    f.htext(64, 516, "回喂三元组，不喂道歉", size=21, color=AMBER_STROKE,
            weight="bold")
    triad = [
        ("实测现象", "引脚没翻转"),
        ("手册出处", "RM0090 §7.3 原句"),
        ("板卡事实", "原理图网络名"),
    ]
    for i, (title, sub) in enumerate(triad):
        x = 64 + i * 330
        f.rect(x, 534, 300, 82, color=AMBER_STROKE, fill=PAPER, sw=2.0)
        f.text(x + 12, 562, title, size=17, color=AMBER_STROKE, weight="bold")
        f.text(x + 12, 592, sub, size=15, color=INK)
    f.text(64, 638,
           "三条一起写回对话或文档；只写「你错了」不会移动采样分布。",
           size=15, color=INK)

    f.rect(48, 664, 1056, 56, color=RED, fill=WHITE, sw=2.4)
    f.text(64, 700,
           "成本序：30 秒 grep → 1 分钟章节检索 → 分钟级勘误/逐位 → 分钟级跑现象",
           size=15, color=RED)

    f.htext(576, 746, "先存在性，后语义。", size=22, color=AMBER_STROKE,
            anchor="middle", weight="bold", hl=True, hl_fill=AMBER_FILL)
    return f


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[2] / "assets" / "illustrations" / "handraw"
    save(reconcile_gates(), str(out / "arch-reconcile-gates.svg"))
    print("wrote arch-reconcile-gates.svg")

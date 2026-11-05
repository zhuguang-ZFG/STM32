#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Chapter 04 B2 figure: the four gates between a PA0 edge and EXTI0_IRQHandler.

Static SVG only: no CSS animation, no SMIL. Panel titles are Chinese, body copy
is English, matching sample-19-flash-fit.svg used by both editions.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from svgkit import Svg, T


def _credit(canvas: Svg, note: str) -> None:
    canvas.line(24, canvas.h - 36, canvas.w - 24, canvas.h - 36, stroke=T.GRID, sw=1)
    canvas.text(24, canvas.h - 16, note, size=11, fill=T.MUTED)
    canvas.text(canvas.w - 24, canvas.h - 16, "自绘 · 静态 · CC BY 4.0", size=11, fill=T.DIM, anchor="end")


def exti_triage() -> Svg:
    canvas = Svg(
        960,
        880,
        "按键中断不进：四环依次读回，先时钟、再映射、后放行",
        "STM32F103C8T6 · RM0008 Rev 21 §8.3.7, §9.4.3, §10.3.1, §10.3.6 · PM0056",
    )
    canvas.header(tag="04", tag_color=T.CYAN)
    canvas.text(40, 86, "STM32F103C8T6  PA0 button  EXTI0  EXTI0_IRQn = 6", size=16,
                fill=T.TEXT, weight="700")
    canvas.text(40, 112,
                "RCC_APB2ENR 0x40021018   AFIO_EXTICR1 0x40010008   "
                "EXTI_IMR 0x40010400   NVIC_ISER0 0xE000E100",
                size=13, fill=T.CYAN)
    canvas.text(40, 138,
                "EXTICR1[3:0] picks the port: 0000 PA, 0001 PB, 0010 PC. "
                "EXTICR1 covers lines 0 to 3.",
                size=14, fill=T.AMBER)
    canvas.text(40, 164,
                "the boxes below are also the read-back order; a later gate never repairs "
                "an earlier one",
                size=13, fill=T.MUTED)

    canvas.text(40, 196, "正常路径  four gates open, in order", size=16,
                fill=T.GREEN, weight="700")
    canvas.rect(40, 210, 880, 170, fill=T.PANEL, stroke=T.GREEN, rx=8)
    gates = [
        ("① GPIO 时钟", "RCC_APB2ENR", "bit 2 = 1", "PA0 CRL writes land"),
        ("② AFIO 与映射", "AFIO_EXTICR1", "[3:0] = 0000", "AFIOEN bit 0 = 1 first"),
        ("③ EXTI 放行", "EXTI_IMR", "bit 0 = 1", "request reaches NVIC"),
        ("④ NVIC 放行", "NVIC_ISER0", "bit 6 = 1", "EXTI0_IRQn = 6"),
    ]
    for index, (title, reg, value, note) in enumerate(gates):
        left = 58 + index * 214
        canvas.rect(left, 232, 200, 118, fill=T.BG, stroke=T.CYAN, rx=4)
        canvas.text(left + 12, 262, title, size=14, fill=T.CYAN, weight="700")
        canvas.text(left + 12, 292, reg, size=12, fill=T.TEXT, mono=True)
        canvas.text(left + 12, 318, value, size=14, fill=T.GREEN, weight="700")
        canvas.text(left + 12, 340, note, size=11, fill=T.MUTED)
        if index < 3:
            canvas.arrow(left + 200, 291, left + 214, 291, color=T.GREEN, sw=2, head=6)
    canvas.text(56, 370, "read all four back before touching the code again",
                size=12, fill=T.MUTED)

    canvas.text(40, 412, "失败路径  one closed gate is enough", size=16,
                fill=T.RED, weight="700")
    canvas.rect(40, 426, 880, 170, fill=T.PANEL, stroke=T.RED, rx=8)
    rows = [
        ("RCC_APB2ENR bit 2 = 0",
         "PA0's CRL never takes the input mode, so no edge ever forms"),
        ("AFIOEN = 0, EXTICR1 = 0001",
         "the write is dropped, it reads 0000, the line stays on PA0"),
        ("EXTI_IMR bit 0 = 0",
         "EXTI_PR still sets bit 0, but the NVIC never sees a request"),
        ("NVIC_ISER0 bit 6 = 0",
         "the request stays pending, the handler never runs"),
    ]
    for index, (left_text, right_text) in enumerate(rows):
        base = 458 + index * 32
        canvas.text(56, base, left_text, size=13, fill=T.RED, mono=True)
        canvas.text(352, base, right_text, size=14, fill=T.TEXT)

    canvas.text(40, 620, "判据  EXTI_PR bit 0 separates ring ③ from ring ④",
                size=16, fill=T.VIOLET, weight="700")
    canvas.rect(40, 634, 880, 156, fill=T.BG2, stroke=T.VIOLET, rx=8)
    canvas.text(56, 664,
                "EXTI_PR 0x40010414: bit 0 sets on the selected edge even while IMR "
                "masks the request.",
                size=14, fill=T.TEXT)
    canvas.text(56, 690,
                "reads 1 and no handler runs: ring ④. reads 0 after a real edge: "
                "rings ① and ②.",
                size=14, fill=T.GREEN, weight="700")
    canvas.text(56, 716,
                "clear it by writing 1, not 0. An uncleared bit re-enters the handler "
                "when you return.",
                size=14, fill=T.AMBER)
    canvas.text(56, 742,
                "does not prove: CRL MODE/CNF, RTSR/FTSR edge choice, contact bounce, "
                "or priority order.",
                size=13, fill=T.MUTED)
    canvas.text(56, 768,
                "preemption and subpriority start after these four gates; that is this "
                "chapter's other figure.",
                size=13, fill=T.MUTED)

    _credit(canvas, "自绘。位号来自 RM0008 Rev 21 第 8.3.7、9.4.3、10.3.1、10.3.6 节；"
                    "EXTI0_IRQn 与 ISER 来自 PM0056 第 4 章。")
    return canvas


FIGURES = [
    ("sample-04-exti-triage.svg", exti_triage),
]


def main(argv: list[str]) -> int:
    out_dir = argv[1] if len(argv) > 1 else os.path.join(os.getcwd(), ".temp", "b2ch04")
    os.makedirs(out_dir, exist_ok=True)
    for name, builder in FIGURES:
        path = builder().save(os.path.join(out_dir, name))
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

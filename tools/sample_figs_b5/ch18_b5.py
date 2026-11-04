#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Static B5 figure for chapter 18: FAQ domain compare.

    python tools/sample_figs_b5/ch18_b5.py assets/diagrams
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from svgkit import Svg, T

import importlib.util

def _load_common():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_common.py")
    spec = importlib.util.spec_from_file_location("sample_figs_b5_common", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

_common = _load_common()
credit = _common.credit
audit_static = _common.audit_static


def faq_compare() -> Svg:
    canvas = Svg(
        960,
        880,
        "编译链接、下载调试、外设、硬件、RTOS 五域各有第一探针，不要把五处配置一次全改",
        "STM32F103C8T6 · chapter 18 · RM0008 / DS5319",
    )
    canvas.header(title="FAQ 五域对照：先问哪一把尺子", tag="18", tag_color=T.CYAN)
    canvas.text(40, 86, "同一块板五个症状域：探针不同，证据不同，禁止混改",
                size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "five domains · one first probe each · no shotgun config edits",
                size=14, fill=T.CYAN)
    canvas.text(40, 138,
                "map 文件 → SWD 电压 → 时钟/引脚 → 3V3·NRST·BOOT0 → 栈与优先级",
                size=13, fill=T.AMBER, mono=True)

    cols = (
        (40, "编译链接", "map / undefined", T.BLUE, "第一探针", "arm-none-eabi-nm\n看缺谁", "常见假阳性", "改了源码却\n没进链接"),
        (220, "下载调试", "SWD 认不出", T.CYAN, "第一探针", "3V3 / NRST\nBOOT0=0", "常见假阳性", "线序对了\n但板没上电"),
        (400, "外设", "串口乱码", T.GREEN, "第一探针", "PCLK 与 BRR\n同口径", "常见假阳性", "只改波特率\n不查时钟树"),
        (580, "硬件", "复位连环", T.AMBER, "第一探针", "NRST 波形\n去耦电容", "常见假阳性", "换程序不\n查供电纹波"),
        (760, "RTOS", "任务饿死", T.VIOLET, "第一探针", "uxTaskGet\nStackHighWater", "常见假阳性", "加延时掩盖\n优先级反转"),
    )
    for x, title, symptom, color, probe_h, probe, false_h, false in cols:
        canvas.rect(x, 168, 168, 52, fill=T.BG2, stroke=color, rx=8)
        canvas.text(x + 84, 190, title, size=15, fill=color, anchor="middle", weight="700")
        canvas.text(x + 84, 210, symptom, size=11, fill=T.MUTED, anchor="middle")

        canvas.rect(x, 232, 168, 150, fill=T.PANEL, stroke=color, rx=8)
        canvas.text(x + 84, 258, probe_h, size=12, fill=color, anchor="middle", weight="700")
        for i, line in enumerate(probe.split("\n")):
            canvas.text(x + 84, 286 + i * 22, line, size=13, fill=T.TEXT, anchor="middle")
        canvas.line(x + 16, 330, x + 152, 330, stroke=T.GRID, sw=1)
        canvas.text(x + 84, 352, "一次只动一处", size=12, fill=T.MUTED, anchor="middle")

        canvas.rect(x, 396, 168, 150, fill=T.PANEL, stroke=T.STROKE, rx=8)
        canvas.text(x + 84, 422, false_h, size=12, fill=T.RED, anchor="middle", weight="700")
        for i, line in enumerate(false.split("\n")):
            canvas.text(x + 84, 450 + i * 22, line, size=13, fill=T.TEXT, anchor="middle")
        canvas.line(x + 16, 494, x + 152, 494, stroke=T.GRID, sw=1)
        canvas.text(x + 84, 520, "证据未到先别改", size=12, fill=T.MUTED, anchor="middle")

    canvas.rect(40, 568, 880, 96, fill=T.BG2, stroke=T.GREEN, rx=8)
    canvas.text(56, 598, "读图顺序：先落域 → 只做该域第一探针 → 有证据再改一处配置 → 回看现象。",
                size=14, fill=T.TEXT)
    canvas.text(56, 626, "五域并排不是让你一次改五处；交叉域（例如串口乱码其实是时钟）先回外设列的时钟探针。",
                size=13, fill=T.TEXT)
    canvas.text(56, 650, "BOOT0 高电平进系统存储器、NRST 被拉低，都先归下载调试域，不要先怀疑应用代码。",
                size=13, fill=T.MUTED)

    canvas.rect(40, 684, 880, 72, fill=T.PANEL, stroke=T.STROKE, rx=8)
    canvas.text(56, 710, "底注  认不出芯片：先量 3V3 与 NRST，再确认 BOOT0=0；编译失败：先看 map 与 undefined reference。",
                size=12, fill=T.TEXT)
    canvas.text(56, 734, "串口乱码：PCLK 与 USART_BRR 必须同一时钟树口径；RTOS 饿死：先看栈水位与优先级，再加延时。",
                size=12, fill=T.TEXT)

    credit(canvas, "自绘。五域第一探针归纳自本章 FAQ 表与 RM0008 启动 / DS5319 NRST·SWD；不替代逐条排错正文。")
    return canvas


FIGURES = [
    ("sample-18-faq-compare.svg", faq_compare),
]


def main(out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    for name, builder in FIGURES:
        path = os.path.join(out_dir, name)
        builder().save(path)
        audit_static(name, path)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "assets/diagrams")

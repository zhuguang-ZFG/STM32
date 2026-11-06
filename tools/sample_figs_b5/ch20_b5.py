#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Static B5 figure for chapter 20: evidence triage.

    python tools/sample_figs_b5/ch20_b5.py assets/diagrams
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


def evidence_triage() -> Svg:
    canvas = Svg(
        960,
        880,
        "手册找错、仪器越级、固件栈选错：先 DS/RM/PM 对号，再选证据阶，最后才动栈",
        "STM32 · chapter 20 · manuals & evidence ladder",
    )
    canvas.header(title="证据三岔口：手册、仪器、固件栈", tag="20", tag_color=T.CYAN)
    canvas.text(40, 122, "卡住时先分岔：是手册拿错、仪器跳级，还是栈选错", size=15, fill=T.TEXT, weight="700")
    _ring = (80, 170)
    canvas.circle(80, 168, 17, fill=T.CYAN, stroke=T.CYAN, sw=1.5)
    canvas.text(80, 174, "？", size=15, fill=T.BG, anchor="middle", weight="700")
    canvas.text(106, 174, "查证卡住了", size=14, fill=T.TEXT, weight="700")

    # 岔口一：手册拿错
    canvas.rect(40, 206, 880, 182, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(56, 234, "岔口一  手册拿错：在 AN 和论坛帖里找电气上限", size=15, fill=T.RED, weight="700")
    canvas.text(56, 262, "症状：拿 HAL 符号搜 RM；F1 的问题打开 F4 的 RM", size=13, fill=T.TEXT)
    spines = [("DS", "引脚与极限", T.CYAN), ("RM", "位域与状态机", T.GREEN),
              ("PM", "内核与向量", T.AMBER), ("AN", "配方与做法", T.VIOLET)]
    for i, (name, what, c) in enumerate(spines):
        sx = 620 + i * 74
        canvas.rect(sx, 224, 58, 118, fill=T.BG, stroke=c, rx=4)
        canvas.rot_text(sx + 40, 336, name, angle=-90, size=15, fill=c, weight="700")
        canvas.text(sx + 29, 356, what[:3], size=9, fill=T.MUTED, anchor="middle")
        canvas.text(sx + 29, 368, what[3:], size=9, fill=T.MUTED, anchor="middle")
    canvas.text(56, 292, "对号：引脚与极限 → DS；位域与状态机 → RM；启动与内核 → PM；配方 → AN", size=13, fill=T.TEXT)
    canvas.text(56, 318, "先写订货号 + 手册编号 + Rev，再摘句子", size=12, fill=T.MUTED)
    canvas.text(56, 344, "F1 的问题配 F1 的手册，地址和位域才对得上", size=12, fill=T.MUTED)
    canvas.arrow(120, 200, 120, 206, color=T.RED, sw=2, head=7)

    # 岔口二：仪器越级
    canvas.rect(40, 408, 880, 202, fill=T.PANEL, stroke=T.AMBER, rx=8)
    canvas.text(56, 436, "岔口二  仪器越级：还没看日志就上示波器", size=15, fill=T.AMBER, weight="700")
    canvas.text(56, 464, "症状：波形很漂亮，问题其实出在链接脚本或选项字节", size=13, fill=T.TEXT)
    steps = ["构建日志", "调试器", "运行日志", "逻辑分析仪", "示波器"]
    base = 570
    for i, name in enumerate(steps):
        sx = 400 + i * 96
        sy = base - i * 26
        canvas.rect(sx, sy, 92, 34, fill=T.BG, stroke=T.AMBER, rx=4)
        canvas.text(sx + 46, sy + 22, name, size=10, fill=T.TEXT, anchor="middle")
        if i:
            canvas.line(sx - 4, sy + 34, sx - 4, sy + 8, stroke=T.MUTED, sw=1)
    canvas.circle(446, 556, 6, fill=T.RED)
    canvas.text(56, 544, "从最低一级起步，", size=13, fill=T.TEXT)
    canvas.text(56, 566, "上一级没有结论不跳级", size=13, fill=T.AMBER, weight="700")
    canvas.text(56, 492, "链接失败看 map；认不出芯片看 SWD 电压；位时序才轮到逻辑分析仪", size=13, fill=T.TEXT)
    canvas.text(56, 518, "每级留一张截图或一段日志，写进排错笔记", size=12, fill=T.MUTED)
    canvas.arrow(120, 402, 120, 408, color=T.AMBER, sw=2, head=7)

    # 岔口三：栈选错
    canvas.rect(40, 630, 880, 164, fill=T.PANEL, stroke=T.VIOLET, rx=8)
    canvas.text(56, 658, "岔口三  固件栈选错：新项目硬上 SPL", size=15, fill=T.VIOLET, weight="700")
    canvas.text(56, 686, "症状：教程是 SPL，芯片是 G0/H7；把 libopencm3 当 ST 官方栈", size=13, fill=T.TEXT)
    forks = [("新项目", "HAL / LL", T.GREEN), ("锁版 F1 维护", "继续 SPL", T.AMBER),
             ("轻量裸机", "libopencm3 对照", T.CYAN)]
    for i, (left, right, c) in enumerate(forks):
        fy = 712 + i * 26
        canvas.text(400, fy, left, size=12, fill=T.TEXT)
        canvas.arrow(492, fy - 4, 540, fy - 4, color=c, sw=1.5, head=6)
        canvas.text(552, fy, right, size=12, fill=c, weight="700")
    canvas.text(56, 712, "手册冲突时以 ST 官方为准", size=12, fill=T.MUTED)
    canvas.text(56, 734, "选定后全工程统一，不混两套启动文件", size=12, fill=T.MUTED)
    canvas.arrow(120, 388, 120, 396, color=T.VIOLET, sw=2, head=7)

    canvas.rect(40, 810, 880, 30, fill=T.BG2, stroke=T.GREEN, rx=8)
    canvas.text(56, 830, "底注  手册编号+Rev 是证据的身份证；没有编号的截图只算线索，不算结论。", size=12, fill=T.TEXT)

    credit(canvas, "自绘。手册分工与证据阶对照本章 manual-choice-map / instrument-evidence-ladder；栈选择对照 firmware-stack-choice。")
    return canvas


FIGURES = [
    ("sample-20-evidence-triage.svg", evidence_triage),
]


def main(out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    for name, builder in FIGURES:
        path = os.path.join(out_dir, name)
        builder().save(path)
        audit_static(name, path)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "assets/diagrams")

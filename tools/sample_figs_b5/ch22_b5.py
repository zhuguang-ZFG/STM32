#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Static B5 figure for chapter 22: simulation triage.

    python tools/sample_figs_b5/ch22_b5.py assets/diagrams
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


def sim_triage() -> Svg:
    canvas = Svg(
        960,
        880,
        "模型缺口、主机环境、板级物理：仿真能过不等于板上能过，先分清失败属于哪一岔",
        "chapter 22 · Wokwi / Renode · model boundary",
    )
    canvas.header(title="仿真三岔口：模型、主机、板级物理", tag="22", tag_color=T.CYAN)
    canvas.text(40, 122, "失败先分岔：是模型没做、是主机环境，还是本来就只能在真板上验", size=15, fill=T.TEXT, weight="700")

    # 左侧源点
    canvas.rect(40, 160, 200, 560, fill=T.PANEL, stroke=T.CYAN, rx=8)
    canvas.text(140, 196, "同一份固件", size=18, fill=T.CYAN, anchor="middle", weight="700")
    canvas.text(140, 224, "在仿真里出问题", size=15, fill=T.TEXT, anchor="middle")
    for j, ln in enumerate(["先问一句：", "这个外设在", "支持表里吗？"]):
        canvas.text(60, 280 + j * 26, ln, size=15, fill=T.MUTED)
    canvas.rect(60, 370, 160, 60, fill=T.BG, stroke=T.GREEN, rx=4)
    canvas.text(140, 394, "GPIO / EXTI / TIM", size=12, fill=T.GREEN, anchor="middle", mono=True)
    canvas.text(140, 414, "有", size=13, fill=T.GREEN, anchor="middle", weight="700")
    canvas.rect(60, 446, 160, 60, fill=T.BG, stroke=T.RED, rx=4)
    canvas.text(140, 470, "DMA / RTC / IWDG", size=12, fill=T.RED, anchor="middle", mono=True)
    canvas.text(140, 490, "Wokwi 没有", size=13, fill=T.RED, anchor="middle", weight="700")
    canvas.text(60, 540, "Wokwi 的 BluePill", size=13, fill=T.TEXT)
    canvas.text(60, 562, "以打开文档的那一版", size=13, fill=T.TEXT)
    canvas.text(60, 584, "支持表为准", size=13, fill=T.TEXT)
    canvas.text(60, 640, "缺口写进测试计划，", size=13, fill=T.MUTED)
    canvas.text(60, 662, "不许静默跳过", size=13, fill=T.MUTED)

    # 三个岔口
    lanes = [
        (40, 160, "岔口一  模型缺口", T.RED, "外设根本没进模拟器",
         ["断言按全功能写，模型只做了子集", "时钟树简化：波特率/定时巧合正确", "→ 未建模项移出仿真验收"]),
        (40, 360, "岔口二  主机环境", T.AMBER, "脚本、路径、键名与文档假设不一致",
         ["别人的 .resc 跑不起来；缺 board.json 键名", "先让最小 blink ELF 跑通，再叠加外设", "→ 固定工具版本，留一条回归门脚本"]),
        (40, 560, "岔口三  板级物理", T.VIOLET, "仿真全绿，真板一上电就失败",
         ["滤波、起振、眼图、纹波不在数字模型里", "线长、上拉、地回流只在 PCB 上成立", "→ 仿真门与真板门分列，缺一不可"]),
    ]
    for lx, ly, title, c, sub, lines in lanes:
        canvas.rect(280, ly, 640, 180, fill=T.PANEL, stroke=c, rx=8)
        canvas.text(296, ly + 32, title, size=16, fill=c, weight="700")
        canvas.text(296, ly + 60, sub, size=13, fill=T.TEXT)
        for j, ln in enumerate(lines):
            canvas.text(296, ly + 94 + j * 26, ln, size=13,
                        fill=T.TEXT if j < 2 else c, weight="700" if j == 2 else "normal")
        canvas.arrow(242, 440, 278, ly + 90, color=c, sw=2, head=7)

    canvas.rect(40, 748, 880, 60, fill=T.BG2, stroke=T.GREEN, rx=8)
    canvas.text(56, 786, "底注  仿真证明「逻辑在模型假设下成立」；真板证明「物理世界也成立」。两句不能并成一句。", size=13, fill=T.TEXT)

    credit(canvas, "自绘。边界与验收门对照 simulation-model-boundary / simulation-acceptance-gates；Wokwi 板定义与 Renode 平台文档仅对照。")
    return canvas


FIGURES = [
    ("sample-22-sim-triage.svg", sim_triage),
]


def main(out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    for name, builder in FIGURES:
        path = os.path.join(out_dir, name)
        builder().save(path)
        audit_static(name, path)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "assets/diagrams")

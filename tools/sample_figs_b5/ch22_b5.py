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
    canvas.text(40, 86, "仿真失败先分岔：是模型没做、是主机环境，还是本来就只能在真板上验",
                size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "three branches: model gap / host environment / board-only physics",
                size=14, fill=T.CYAN)
    canvas.text(40, 138,
                "Wokwi ≠ full RM · Renode ≠ analog · PCB parasitics stay on the bench",
                size=13, fill=T.AMBER, mono=True)

    canvas.text(40, 170, "岔口一  模型缺口：外设根本没进模拟器", size=16, fill=T.RED, weight="700")
    canvas.text(920, 170, "supported vs assumed", size=11, fill=T.MUTED, anchor="end", mono=True)
    canvas.rect(40, 184, 880, 174, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(56, 214, "症状：同一份固件在仿真里外设无响应，或行为与 RM 状态机不一致",
                size=14, fill=T.TEXT)
    canvas.text(56, 240, "原因 A：把「板能选」当成「外设全建模」——先查 Wokwi/Renode 支持表",
                size=14, fill=T.TEXT)
    canvas.text(56, 266, "原因 B：USB/CAN/模拟前端等只做了子集，断言却按全功能写",
                size=14, fill=T.TEXT)
    canvas.text(56, 292, "原因 C：时钟树简化，波特率/定时只在模型时钟下巧合正确",
                size=14, fill=T.TEXT)
    canvas.text(56, 318, "检查点：对照 simulation-model-boundary，未建模项移出仿真验收",
                size=14, fill=T.TEXT)
    canvas.text(56, 344, "探针：用官方支持列表 + 本章边界图勾选；缺口写进测试计划而非静默跳过",
                size=13, fill=T.MUTED)

    canvas.text(40, 386, "岔口二  主机环境：脚本、路径、权限", size=16, fill=T.AMBER, weight="700")
    canvas.text(920, 386, " Renode script / ELF path", size=11, fill=T.MUTED, anchor="end", mono=True)
    canvas.rect(40, 400, 880, 174, fill=T.PANEL, stroke=T.AMBER, rx=8)
    canvas.text(56, 430, "症状：别人的 .resc 跑不起来；Wokwi 工程缺 board.json 键名",
                size=14, fill=T.TEXT)
    canvas.text(56, 456, "原因：主机 Python/路径/串口桥接与文档假设不一致，不是固件逻辑错",
                size=14, fill=T.TEXT)
    canvas.text(56, 482, "数值：ELF 入口与向量表仍按 PM；仿真器只是加载器，不改链接脚本",
                size=14, fill=T.TEXT)
    canvas.text(56, 508, "修复：先让最小 blink ELF 在仿真里跑通，再叠加外设；固定工具版本号",
                size=14, fill=T.TEXT)
    canvas.text(56, 534, "Wokwi：核对板定义引脚键；Renode：核对平台名与 machine 脚本",
                size=14, fill=T.TEXT)
    canvas.text(56, 560, "探针：保留一条「最小可运行」脚本作回归门，与业务测试分离",
                size=13, fill=T.MUTED)

    canvas.text(40, 612, "岔口三  板级物理：仿真替不了的事", size=16, fill=T.VIOLET, weight="700")
    canvas.text(920, 612, "bench only", size=11, fill=T.MUTED, anchor="end", mono=True)
    canvas.rect(40, 626, 880, 164, fill=T.PANEL, stroke=T.VIOLET, rx=8)
    canvas.text(56, 654, "症状：仿真全绿，真板噪声、时序、供电一上电就失败",
                size=14, fill=T.TEXT)
    canvas.text(56, 680, "原因 A：模拟滤波、晶振起振、USB 眼图、电源纹波不在数字模型里",
                size=14, fill=T.TEXT)
    canvas.text(56, 706, "原因 B：线长、上拉阻值、地回流只在 PCB 上成立",
                size=14, fill=T.TEXT)
    canvas.text(56, 732, "原因 C：用仿真绿灯当作量产放行，跳过真板验收门",
                size=14, fill=T.TEXT)
    canvas.text(56, 758, "探针：simulation-acceptance-gates——仿真门与真板门分列，缺一不可",
                size=13, fill=T.MUTED)

    canvas.rect(40, 806, 880, 30, fill=T.BG2, stroke=T.GREEN, rx=8)
    canvas.text(56, 826, "底注  仿真证明「逻辑在模型假设下成立」；真板证明「物理世界也成立」。两句不能并成一句。",
                size=12, fill=T.TEXT)

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

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Static B5 figure for chapter 19: project milestone triage.

    python tools/sample_figs_b5/ch19_b5.py assets/diagrams
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


def milestone_triage() -> Svg:
    canvas = Svg(
        960,
        880,
        "范围太大、跳过里程碑、集成无证据：一槽一位、每槽可演示、合入前要有通过门",
        "STM32F103C8T6 · chapter 19 · project milestones",
    )
    canvas.header(title="项目三岔口：范围、里程碑、证据", tag="19", tag_color=T.CYAN)
    canvas.text(40, 122, "选题卡住时先分清：是贪多、是跳步，还是没有可演示证据", size=15, fill=T.TEXT, weight="700")

    # 上：里程碑阶梯（主线）
    canvas.text(40, 158, "主线的走法：五个门，门未过不许跳", size=15, fill=T.GREEN, weight="700")
    gates = ["点亮", "采集", "传输", "存储", "升级"]
    base = 252
    for i, name in enumerate(gates):
        gx = 60 + i * 176
        gy = base - i * 22
        canvas.rect(gx, gy, 150, 56, fill=T.PANEL, stroke=T.GREEN, rx=8)
        canvas.circle(gx + 26, gy + 28, 13, fill=T.GREEN, stroke=T.GREEN, sw=1.5)
        canvas.text(gx + 26, gy + 33, str(i + 1), size=13, fill=T.BG, anchor="middle", weight="700")
        canvas.text(gx + 48, gy + 34, name, size=17, fill=T.GREEN, weight="700")
        if i < 4:
            canvas.arrow(gx + 152, gy + 20, gx + 174, gy - 8, color=T.GREEN, sw=2, head=7)
    canvas.text(60, 324, "每个门留一段 10 秒演示或串口日志哈希；合入 PR 必须附上", size=13, fill=T.MUTED)

    # 岔口一：范围太大
    canvas.rect(40, 330, 880, 150, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(56, 358, "岔口一  范围太大：十个外设一起上", size=15, fill=T.RED, weight="700")
    canvas.text(56, 386, "症状：原理图画满了，哪个都点不亮；半成品分支互相踩脚", size=13, fill=T.TEXT)
    slots = ["灯", "串口", "ADC", "一帧 USB"]
    canvas.text(56, 416, "一槽一位——本周只许一个可演示槽，四选一：", size=13, fill=T.TEXT, weight="700")
    for i, s_ in enumerate(slots):
        sx = 470 + i * 110
        sel = (i == 0)
        canvas.rect(sx, 396, 100, 32, fill=T.BG, stroke=T.GREEN if sel else T.MUTED, rx=4)
        canvas.text(sx + 50, 417, s_, size=13, fill=T.GREEN if sel else T.MUTED, anchor="middle",
                    weight="700" if sel else "normal")
    canvas.text(56, 452, "其余需求写进下一槽的验收表：输入、预期现象、失败时保留的日志", size=12, fill=T.MUTED)

    # 岔口二：跳过里程碑
    canvas.rect(40, 496, 880, 150, fill=T.PANEL, stroke=T.AMBER, rx=8)
    canvas.text(56, 524, "岔口二  跳过里程碑：直接拼整机", size=15, fill=T.AMBER, weight="700")
    canvas.text(56, 552, "症状：单模块曾经亮过，一接线就全灭；谁先坏说不清", size=13, fill=T.TEXT)
    canvas.text(56, 580, "模块门先过：每个外设单独通过演示，才允许进集成分支", size=13, fill=T.TEXT, weight="700")
    canvas.text(56, 608, "64 KB 里同时塞 Bootloader + APP + 胖日志会挤爆一槽——先看 flash-fit 的账", size=12, fill=T.MUTED)
    canvas.text(56, 630, "IAP 槽：先确认 APP 链接脚本与向量表，再谈 YMODEM；顺序反了只会砖机", size=12, fill=T.MUTED)

    # 岔口三：集成无证据
    canvas.rect(40, 662, 880, 150, fill=T.PANEL, stroke=T.VIOLET, rx=8)
    canvas.text(56, 690, "岔口三  集成无证据：现象在、数据不在", size=15, fill=T.VIOLET, weight="700")
    canvas.text(56, 718, "症状：「好像稳定了」但复现不了；比赛现场第一次失败", size=13, fill=T.TEXT)
    canvas.text(56, 746, "肉眼闪灯不算记录：换逻辑分析仪/串口日志，带时间戳", size=13, fill=T.TEXT, weight="700")
    canvas.text(56, 774, "DMA/中断路径改过，要有 CNDTR 或错误计数的前后对比", size=12, fill=T.MUTED)

    canvas.rect(40, 798, 880, 30, fill=T.BG2, stroke=T.GREEN, rx=8)
    canvas.text(56, 818, "底注  「好像稳定了」不是证据——可演示、可复现、可核对，三样齐了才算一个里程碑。", size=12, fill=T.TEXT)

    credit(canvas, "自绘。里程碑顺序与一槽一位对照本章里程碑表与 flash-fit / sram-budget；IAP 槽位对照第 12 章。")
    return canvas


FIGURES = [
    ("sample-19-milestone-triage.svg", milestone_triage),
]


def main(out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    for name, builder in FIGURES:
        path = os.path.join(out_dir, name)
        builder().save(path)
        audit_static(name, path)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "assets/diagrams")

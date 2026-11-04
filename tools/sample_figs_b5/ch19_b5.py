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
    canvas.text(40, 86, "选题卡住时先分清：是贪多、是跳步，还是没有可演示证据",
                size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "three branches: scope creep / skipped milestone / integration without evidence",
                size=14, fill=T.CYAN)
    canvas.text(40, 138,
                "one slot · one feature · demo gate before merge",
                size=13, fill=T.AMBER, mono=True)

    canvas.text(40, 170, "岔口一  范围太大：十个外设一起上", size=16, fill=T.RED, weight="700")
    canvas.text(920, 170, "one-slot rule", size=11, fill=T.MUTED, anchor="end", mono=True)
    canvas.rect(40, 184, 880, 174, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(56, 214, "症状：原理图画满了，但任何一个外设都点不亮；仓库里半成品分支互相踩脚",
                size=14, fill=T.TEXT)
    canvas.text(56, 240, "原因 A：把「最终产品」当成第一个里程碑，没有一槽一位的切片",
                size=14, fill=T.TEXT)
    canvas.text(56, 266, "原因 B：把蓝牙、USB、IAP 和网关写进同一周目标，集成面一次性爆炸",
                size=14, fill=T.TEXT)
    canvas.text(56, 292, "原因 C：复用了别人的巨型工程，却说不清自己改了哪一条数据路径",
                size=14, fill=T.TEXT)
    canvas.text(56, 318, "检查点：本周只许一个可演示槽——灯 / 串口 / ADC / 一帧 USB，四选一",
                size=14, fill=T.TEXT)
    canvas.text(56, 344, "探针：用一页验收表列出输入、预期现象、失败时保留的日志，其余需求进下一槽",
                size=13, fill=T.MUTED)

    canvas.text(40, 386, "岔口二  跳过里程碑：直接拼整机", size=16, fill=T.AMBER, weight="700")
    canvas.text(920, 170, "", size=11, fill=T.MUTED, anchor="end")
    canvas.text(920, 386, "gates before glue", size=11, fill=T.MUTED, anchor="end", mono=True)
    canvas.rect(40, 400, 880, 174, fill=T.PANEL, stroke=T.AMBER, rx=8)
    canvas.text(56, 430, "症状：单模块曾经亮过，一接线就全灭；谁先坏说不清",
                size=14, fill=T.TEXT)
    canvas.text(56, 456, "原因：没有「模块门」——每个外设单独通过演示，才允许进入集成分支",
                size=14, fill=T.TEXT)
    canvas.text(56, 482, "数值：Flash 64 KB 工程若同时塞 Bootloader + APP + 胖日志，一槽会挤爆",
                size=14, fill=T.TEXT)
    canvas.text(56, 508, "修复：按本章里程碑表走：点亮 → 采集 → 传输 → 存储 → 升级，门未过不许跳",
                size=14, fill=T.TEXT)
    canvas.text(56, 534, "IAP 槽：先确认 APP 链接脚本与向量表，再谈 YMODEM；顺序反了只会砖机",
                size=14, fill=T.TEXT)
    canvas.text(56, 560, "探针：每个门保留一段 10 秒演示视频或串口日志哈希，合入 PR 必须附上",
                size=13, fill=T.MUTED)

    canvas.text(40, 612, "岔口三  集成无证据：现象在、数据不在", size=16, fill=T.VIOLET, weight="700")
    canvas.text(920, 612, "evidence before claim", size=11, fill=T.MUTED, anchor="end", mono=True)
    canvas.rect(40, 626, 880, 164, fill=T.PANEL, stroke=T.VIOLET, rx=8)
    canvas.text(56, 654, "症状：「好像稳定了」但复现不了；比赛现场第一次失败",
                size=14, fill=T.TEXT)
    canvas.text(56, 680, "原因 A：用肉眼闪灯代替逻辑分析仪/串口记录，没有可核对的时间戳",
                size=14, fill=T.TEXT)
    canvas.text(56, 706, "原因 B：DMA/中断路径改过，却没有 CNDTR 或错误计数的前后对比",
                size=14, fill=T.TEXT)
    canvas.text(56, 732, "原因 C：验收表只写功能，不写失败分支与回退条件",
                size=14, fill=T.TEXT)
    canvas.text(56, 758, "探针：每槽至少留构建哈希、map 摘要、一次失败日志；无证据不算通过",
                size=13, fill=T.MUTED)

    canvas.rect(40, 806, 880, 30, fill=T.BG2, stroke=T.GREEN, rx=8)
    canvas.text(56, 826, "底注  一槽一位不是少做，是把失败面收窄到能定位；整机魅力放在最后一扇门之后。",
                size=12, fill=T.TEXT)

    credit(canvas, "自绘。里程碑与一槽一位来自本章选题表与 iap-acceptance / rtos-startup 门图；Flash 64 KB 边界见 sample-19-flash-fit。")
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

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
    canvas.text(40, 86, "查资料卡住时：先确认打开的是哪本手册，再确认仪器是否越级，最后才谈换栈",
                size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "three branches: wrong manual / wrong instrument / wrong firmware stack",
                size=14, fill=T.CYAN)
    canvas.text(40, 138,
                "DS pin & limits → RM registers → PM vectors → AN recipes → UM tools",
                size=13, fill=T.AMBER, mono=True)

    canvas.text(40, 170, "岔口一  手册找错：在 AN 里找电气上限", size=16, fill=T.RED, weight="700")
    canvas.text(920, 170, "DS / RM / PM", size=11, fill=T.MUTED, anchor="end", mono=True)
    canvas.rect(40, 184, 880, 174, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(56, 214, "症状：搜了半天「推荐电流」，却打开了应用笔记或论坛帖",
                size=14, fill=T.TEXT)
    canvas.text(56, 240, "原因 A：把 AN 当 DS——电气上限与引脚复用只在数据手册成立",
                size=14, fill=T.TEXT)
    canvas.text(56, 266, "原因 B：把 HAL 符号当寄存器名去 RM 里搜，自然搜不到",
                size=14, fill=T.TEXT)
    canvas.text(56, 292, "原因 C：F1 的问题打开了 F4 的 RM，外设地址与位域对不上",
                size=14, fill=T.TEXT)
    canvas.text(56, 318, "检查点：引脚/极限→DS；位域/状态机→RM；启动与内核→PM；配方→AN",
                size=14, fill=T.TEXT)
    canvas.text(56, 344, "探针：先写清订货号与手册编号+Rev，再摘句子；无编号的「经验」不进正文",
                size=13, fill=T.MUTED)

    canvas.text(40, 386, "岔口二  仪器越级：还没日志就上示波器", size=16, fill=T.AMBER, weight="700")
    canvas.text(920, 386, "evidence ladder", size=11, fill=T.MUTED, anchor="end", mono=True)
    canvas.rect(40, 400, 880, 174, fill=T.PANEL, stroke=T.AMBER, rx=8)
    canvas.text(56, 430, "症状：示波器波形很漂亮，但问题其实是链接脚本或选项字节",
                size=14, fill=T.TEXT)
    canvas.text(56, 456, "原因：跳过构建日志 → 调试器 → 运行日志 → 逻辑分析仪 → 示波器 的阶梯",
                size=14, fill=T.TEXT)
    canvas.text(56, 482, "数值：链接失败用 map；认不出芯片用 SWD 电压；位时序才需要逻辑分析仪",
                size=14, fill=T.TEXT)
    canvas.text(56, 508, "修复：按 instrument-evidence-ladder 逐级留证据，上一级无结论不跳级",
                size=14, fill=T.TEXT)
    canvas.text(56, 534, "电源纹波与 μA 级电流才上专用探头；万用表 μA 档会拖低电压，别当精密表",
                size=14, fill=T.TEXT)
    canvas.text(56, 560, "探针：每级至少留一张截图或一段日志哈希，写进排错笔记",
                size=13, fill=T.MUTED)

    canvas.text(40, 612, "岔口三  固件栈选错：新项目硬上 SPL", size=16, fill=T.VIOLET, weight="700")
    canvas.text(920, 612, "HAL / LL / SPL / libopencm3", size=11, fill=T.MUTED, anchor="end", mono=True)
    canvas.rect(40, 626, 880, 164, fill=T.PANEL, stroke=T.VIOLET, rx=8)
    canvas.text(56, 654, "症状：教程是 SPL，芯片是 G0/H7；或把 libopencm3 当 ST 支持栈",
                size=14, fill=T.TEXT)
    canvas.text(56, 680, "原因 A：新项目应优先 HAL/LL；锁版 F1 维护才继续 SPL",
                size=14, fill=T.TEXT)
    canvas.text(56, 706, "原因 B：轻量裸机可以对照 libopencm3，但手册冲突仍以 ST 官方为准",
                size=14, fill=T.TEXT)
    canvas.text(56, 732, "原因 C：CubeMX 生成与手写寄存器混用，时钟初始化打两次",
                size=14, fill=T.TEXT)
    canvas.text(56, 758, "探针：用 firmware-stack-choice 图对号；选定后全工程统一，不混两套启动文件",
                size=13, fill=T.MUTED)

    canvas.rect(40, 806, 880, 30, fill=T.BG2, stroke=T.GREEN, rx=8)
    canvas.text(56, 826, "底注  手册编号+Rev 是证据的身份证；没有编号的截图只算线索，不算结论。",
                size=12, fill=T.TEXT)

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

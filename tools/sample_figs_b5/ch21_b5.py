#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Static B5 figure for chapter 21: board family compare.

    python tools/sample_figs_b5/ch21_b5.py assets/diagrams
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


def board_compare() -> Svg:
    canvas = Svg(
        960,
        880,
        "BluePill F103、BlackPill F411、Nucleo-F411RE：封装、调试器、5V 容忍与 USB 路径对照",
        "chapter 21 · board maps · DS5319 / Nucleo UM",
    )
    canvas.header(title="三板对照：能力、调试器、电源边界", tag="21", tag_color=T.CYAN)
    canvas.text(40, 86, "选板先对四问：内核与 Flash、板上调试器、5V 引脚、USB 谁供电",
                size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "three boards · same five questions · no photo fakes",
                size=14, fill=T.CYAN)
    canvas.text(40, 138,
                "F103C8 LQFP48 · F411CE / F411RE · ST-LINK on Nucleo only",
                size=13, fill=T.AMBER, mono=True)

    cols = (
        (160, "BluePill", "STM32F103C8T6", "LQFP48 · 72 MHz", T.GREEN),
        (411, "BlackPill", "STM32F411CEU6", "UFQFPN48 · 100 MHz", T.CYAN),
        (662, "Nucleo-F411RE", "STM32F411RET6", "LQFP64 · on-board ST-LINK", T.VIOLET),
    )
    for x, name, mcu, tagline, color in cols:
        canvas.rect(x, 168, 246, 64, fill=T.BG2, stroke=color, rx=8)
        canvas.text(x + 123, 192, name, size=17, fill=color, anchor="middle", weight="700")
        canvas.text(x + 123, 214, mcu, size=12, fill=T.TEXT, anchor="middle", mono=True)
        canvas.text(x + 123, 232, tagline, size=11, fill=T.MUTED, anchor="middle")

    canvas.rect(160, 248, 748, 420, fill=T.PANEL, stroke=T.STROKE, rx=8)
    for y in (330, 400, 470, 540, 610):
        canvas.line(160, y, 908, y, stroke=T.GRID, sw=1)
    for x in (409, 660):
        canvas.line(x, 248, x, 668, stroke=T.GRID, sw=1)

    rows = (
        (270, "Flash / RAM", "64 KB / 20 KB", "512 KB / 128 KB", "512 KB / 128 KB"),
        (350, "板上调试器", "无，外接 ST-LINK", "无，外接 ST-LINK", "ST-LINK/V2-1 板载"),
        (420, "BOOT0 / NRST", "按键或跳线", "按键", "板载按键 + 跳线"),
        (490, "5V 容忍", "少数 FT 脚，勿假设全 5V", "多数 FT，仍看 DS", "按 UM 与 DS 脚注"),
        (560, "USB 路径", "需外电路 / 自制", "板载 Micro-USB 器件口", "ST-LINK USB + 用户 USB"),
        (630, "本章用途", "F1 主线例程默认板", "F4 性能对照", "官方形态与可复现布线"),
    )
    labels = ("40",)
    for y, label, a, b, c in rows:
        canvas.text(40, y + 10, label, size=13, fill=T.TEXT, weight="700")
        canvas.text(172, y + 10, a, size=13, fill=T.TEXT)
        canvas.text(423, y + 10, b, size=13, fill=T.TEXT)
        canvas.text(674, y + 10, c, size=13, fill=T.TEXT)

    canvas.rect(40, 688, 880, 72, fill=T.BG2, stroke=T.GREEN, rx=8)
    canvas.text(56, 714, "读图：需要官方调试器与可复现布线 → Nucleo；需要 F1 生态与本书例程 → BluePill；需要 F4 主频与更多 Flash → BlackPill。",
                size=13, fill=T.TEXT)
    canvas.text(56, 740, "板图是自绘知识轨，不是实拍；真板照片另走真证轨，禁止用 AI 假板冒充。",
                size=13, fill=T.TEXT)

    canvas.rect(40, 776, 880, 40, fill=T.PANEL, stroke=T.STROKE, rx=8)
    canvas.text(56, 800, "底注  PC13 LED 极性、USB D+ 上拉、5V 引脚名单以 DS/UM 为准；图鉴只帮你定位，不改电气上限。",
                size=12, fill=T.TEXT)

    credit(canvas, "自绘对照图。MCU 与存储器来自各板订货号对应 DS；Nucleo 调试器形态来自 ST UM；非实拍。")
    return canvas


FIGURES = [
    ("sample-21-board-compare.svg", board_compare),
]


def main(out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    for name, builder in FIGURES:
        path = os.path.join(out_dir, name)
        builder().save(path)
        audit_static(name, path)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "assets/diagrams")

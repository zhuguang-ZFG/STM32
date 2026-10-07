#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成 H7 / G0 / L4 的 LQFP 引脚图。

脚名与顺序只来自 ST 数据手册的引脚图 / 引脚表，脚本不补脚、不改序。
出处写在各图页脚，章节里再列关键复用。
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from svgkit import Svg, T  # noqa: E402


def _color(name: str) -> str:
    head = name.split("-")[0].split("/")[0].split("(")[0]
    if head.startswith(("VDD", "VSS", "VBA", "VREF", "VDDA", "VSSA", "VCAP", "PDR")):
        return T.RED
    if "NRST" in name or "BOOT" in name:
        return T.AMBER
    if head.startswith("PA"):
        return T.CYAN
    if head.startswith("PB"):
        return T.GREEN
    if head.startswith("PC"):
        return T.VIOLET
    if head.startswith("PD"):
        return T.PINK
    if head.startswith("PE"):
        return T.BLUE
    if head.startswith("PF") or head.startswith("PG"):
        return T.ORANGE
    if head.startswith("PH"):
        return T.AMBER
    return T.TEXT


def _rot_text(s: Svg, x, y, text, angle, size, fill):
    """绕 (x, y) 旋转。顶边 -90 让字往上长，底边 90 让字往下长，避免和邻脚重叠。"""
    s.add(
        f'<text x="{x:g}" y="{y:g}" font-size="{size:g}" fill="{fill}" '
        f'text-anchor="start" font-family="{T.MONO}" '
        f'transform="rotate({angle:g} {x:g} {y:g})">{text}</text>'
    )


def lqfp(title, subtitle, pins, cite, chip_lines):
    """pins 为长度 4*n 的列表，顺序为数据手册脚号 1..4n。

    封装画法与 ST 引脚图一致：左上为 1，左边向下，底边向右，右边向上，顶边向左。
    """
    if len(pins) % 4:
        raise ValueError(len(pins))
    n = len(pins) // 4
    left, bottom, right, top = (pins[0:n], pins[n:2 * n],
                                pins[2 * n:3 * n], pins[3 * n:4 * n])
    # 右边在手册图上是从下往上编号，列表里 2n+1 在下、3n 在上。
    # 顶边是从右往左编号。
    pitch = 20 if n <= 16 else 15
    size = 9 if n <= 16 else 7.5
    cs = n * pitch
    # 上下标签是旋转的，要给最长的脚名留出轴向空间，避免压到标题或页脚。
    label_room = 150
    header_h, footer_h = 78, 52
    w = int(label_room * 2 + cs)
    h = int(header_h + label_room + cs + label_room + footer_h)
    s = Svg(w, h, title, subtitle)
    s.header(tag="引脚图", tag_color=T.AMBER)
    cx = w / 2
    cy = header_h + label_room + cs / 2
    x0, y0 = cx - cs / 2, cy - cs / 2
    s.rect(x0, y0, cs, cs, fill="#1b1f28", stroke="#39424f", rx=6)
    s.circle(x0 + 12, y0 + 12, 4, fill="#5b6472")
    s.text(cx, cy - 8, chip_lines[0], size=13 if n <= 16 else 12,
           anchor="middle", fill="#dfe6f0", weight="700", mono=True)
    for i, line in enumerate(chip_lines[1:]):
        s.text(cx, cy + 14 + i * 16, line, size=10, anchor="middle", fill="#8b98b0")

    def stub_h(x1, x2, y):
        s.line(x1, y, x2, y, stroke="#e2b23c", sw=1.6)

    def stub_v(x, y1, y2):
        s.line(x, y1, x, y2, stroke="#e2b23c", sw=1.6)

    for i, name in enumerate(left):
        y = y0 + (i + 0.5) * pitch
        stub_h(x0 - 14, x0, y)
        num = str(i + 1)
        s.text(x0 - 18, y + 3, num, size=7, anchor="end", fill=T.DIM, mono=True)
        s.text(x0 - 18 - 7 * len(num) - 6, y + 3, name, size=size,
               anchor="end", fill=_color(name), mono=True)
    for i, name in enumerate(bottom):
        x = x0 + (i + 0.5) * pitch
        stub_v(x, y0 + cs, y0 + cs + 14)
        num = str(n + i + 1)
        s.text(x, y0 + cs + 26, num, size=7, anchor="middle", fill=T.DIM, mono=True)
        _rot_text(s, x + 3, y0 + cs + 34, name, 90, size, _color(name))
    for i, name in enumerate(right):
        # 列表第 0 项是较小脚号，位于底边一侧
        y = y0 + cs - (i + 0.5) * pitch
        stub_h(x0 + cs, x0 + cs + 14, y)
        num = str(2 * n + i + 1)
        s.text(x0 + cs + 18, y + 3, num, size=7, fill=T.DIM, mono=True)
        s.text(x0 + cs + 18 + 7 * len(num) + 4, y + 3, name, size=size,
               fill=_color(name), mono=True)
    for i, name in enumerate(top):
        # 列表第 0 项是较小脚号，位于右边一侧
        x = x0 + cs - (i + 0.5) * pitch
        stub_v(x, y0 - 14, y0)
        num = str(3 * n + i + 1)
        s.text(x, y0 - 18, num, size=7, anchor="middle", fill=T.DIM, mono=True)
        _rot_text(s, x - 3, y0 - 30, name, -90, size, _color(name))

    s.footer(cite)
    return s


# STM32G071RB LQFP64。DS12232 Rev 5，Table 12 的 LQFP64 列，脚 1 到脚 64。
# 与 Figure 9（STM32G071RxT LQFP64 pinout）同一封装。
G071_LQFP64 = [
    "PC11", "PC12", "PC13", "PC14-OSC32_IN", "PC15-OSC32_OUT", "VBAT",
    "VREF+", "VDD/VDDA", "VSS/VSSA", "PF0-OSC_IN", "PF1-OSC_OUT", "PF2-NRST",
    "PC0", "PC1", "PC2", "PC3", "PA0", "PA1", "PA2", "PA3", "PA4", "PA5",
    "PA6", "PA7", "PC4", "PC5", "PB0", "PB1", "PB2", "PB10", "PB11", "PB12",
    "PB13", "PB14", "PB15", "PA8", "PA9", "PC6", "PC7", "PD8", "PD9", "PA10",
    "PA11", "PA12", "PA13", "PA14-BOOT0", "PA15", "PC8", "PC9", "PD0", "PD1",
    "PD2", "PD3", "PD4", "PD5", "PD6", "PB3", "PB4", "PB5", "PB6", "PB7",
    "PB8", "PB9", "PC10",
]

# STM32L476Rx LQFP64。DS10198 Rev 11，Figure 16，并与 Table 16 的 LQFP64 列逐脚核对。
L476_LQFP64 = [
    "VBAT", "PC13", "PC14-OSC32_IN", "PC15-OSC32_OUT", "PH0-OSC_IN",
    "PH1-OSC_OUT", "NRST", "PC0", "PC1", "PC2", "PC3", "VSSA/VREF-", "VDDA/VREF+",
    "PA0", "PA1", "PA2", "PA3", "VSS", "VDD", "PA4", "PA5", "PA6", "PA7",
    "PC4", "PC5", "PB0", "PB1", "PB2", "PB10", "PB11", "VSS", "VDD",
    "PB12", "PB13", "PB14", "PB15", "PC6", "PC7", "PC8", "PC9", "PA8",
    "PA9", "PA10", "PA11", "PA12", "PA13", "VSS", "VDDUSB", "PA14", "PA15",
    "PC10", "PC11", "PC12", "PD2", "PB3", "PB4", "PB5", "PB6", "PB7",
    "BOOT0", "PB8", "PB9", "VSS", "VDD",
]

# STM32H743xI LQFP144。DS12110 Rev 11，Figure 7（MSv41917V4）。
# VCAP 两只脚在图上分别标成 VCAP1（脚 71）和 VCAP2（脚 106）。
H743_LQFP144 = [
    "PE2", "PE3", "PE4", "PE5", "PE6", "VBAT", "PC13", "PC14-OSC32_IN",
    "PC15-OSC32_OUT", "PF0", "PF1", "PF2", "PF3", "PF4", "PF5", "VSS", "VDD",
    "PF6", "PF7", "PF8", "PF9", "PF10", "PH0-OSC_IN", "PH1-OSC_OUT", "NRST",
    "PC0", "PC1", "PC2_C", "PC3_C", "VDD", "VSSA", "VREF+", "VDDA", "PA0",
    "PA1", "PA2", "PA3", "VSS", "VDD", "PA4", "PA5", "PA6", "PA7", "PC4",
    "PC5", "PB0", "PB1", "PB2", "PF11", "PF12", "VSS", "VDD", "PF13", "PF14",
    "PF15", "PG0", "PG1", "PE7", "PE8", "PE9", "VSS", "VDD", "PE10", "PE11",
    "PE12", "PE13", "PE14", "PE15", "PB10", "PB11", "VCAP1", "VDD", "PB12",
    "PB13", "PB14", "PB15", "PD8", "PD9", "PD10", "PD11", "PD12", "PD13",
    "VSS", "VDD", "PD14", "PD15", "PG2", "PG3", "PG4", "PG5", "PG6", "PG7",
    "PG8", "VSS", "VDD33USB", "PC6", "PC7", "PC8", "PC9", "PA8", "PA9",
    "PA10", "PA11", "PA12", "PA13", "VCAP2", "VSS", "VDD", "PA14", "PA15",
    "PC10", "PC11", "PC12", "PD0", "PD1", "PD2", "PD3", "PD4", "PD5", "VSS",
    "VDD", "PD6", "PD7", "PG9", "PG10", "PG11", "PG12", "PG13", "PG14", "VSS",
    "VDD", "PG15", "PB3", "PB4", "PB5", "PB6", "PB7", "BOOT0", "PB8", "PB9",
    "PE0", "PE1", "PDR_ON", "VDD",
]


def g071():
    return lqfp(
        "STM32G071RB LQFP64 引脚",
        "64 脚，顺序同 Table 12 的 LQFP64 列",
        G071_LQFP64,
        "DS12232 Rev 5 Table 12",
        ["STM32G071RB", "LQFP64 · 10 x 10 mm", "Cortex-M0+ · 最高 64 MHz"],
    )


def l476():
    return lqfp(
        "STM32L476RG LQFP64 引脚",
        "64 脚，顺序同 Figure 16",
        L476_LQFP64,
        "DS10198 Rev 11 Figure 16",
        ["STM32L476Rx", "LQFP64 · 10 x 10 mm", "Cortex-M4F · 最高 80 MHz"],
    )


def h743():
    return lqfp(
        "STM32H743ZI LQFP144 引脚",
        "144 脚，顺序同 Figure 7",
        H743_LQFP144,
        "DS12110 Rev 11 Figure 7",
        ["STM32H743xI", "LQFP144 · 20 x 20 mm", "Cortex-M7 · 最高 480 MHz"],
    )


ALL = [
    ("pinout-stm32g071rb-lqfp64", g071),
    ("pinout-stm32l476rg-lqfp64", l476),
    ("pinout-stm32h743zi-lqfp144", h743),
]


def main(argv):
    here = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(os.path.dirname(here), "assets", "boards")
    os.makedirs(out_dir, exist_ok=True)
    only = set(argv[1:])
    import xml.dom.minidom
    for name, fn in ALL:
        if only and name not in only:
            continue
        if len({"g": G071_LQFP64, "l": L476_LQFP64, "h": H743_LQFP144}[
                "g" if "g071" in name else "l" if "l476" in name else "h"]) % 4:
            raise SystemExit(name)
        path = os.path.join(out_dir, name + ".svg")
        fn().save(path)
        xml.dom.minidom.parse(path)
        print(f"[ok] {name}.svg  pins ok")


if __name__ == "__main__":
    # 脚数必须能被 4 整除，否则画出来的四边对不齐。
    for label, seq in (("G071", G071_LQFP64), ("L476", L476_LQFP64),
                       ("H743", H743_LQFP144)):
        if len(seq) not in (64, 144) or len(seq) % 4:
            raise SystemExit(f"{label} 脚数 {len(seq)} 不对")
    main(sys.argv)

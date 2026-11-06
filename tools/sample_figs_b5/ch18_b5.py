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
    canvas = Svg(960, 880, "FAQ：从症状找到下一项检查", "编译链接 / 下载调试 / 外设 / 硬件 / RTOS")
    canvas.header(tag="18", tag_color=T.CYAN)
    canvas.text(40, 104, "保存一次失败的日志或波形，再选下面对应的一行。", size=21, fill=T.TEXT, weight="700")
    canvas.text(40, 162, "症状", size=19, fill=T.MUTED)
    canvas.text(316, 162, "检查什么", size=19, fill=T.MUTED)
    canvas.text(650, 162, "读到什么才往下查", size=19, fill=T.MUTED)
    for y, label, symptom, check, detail, evidence, next_step, color in (
        (196, "编译链接", "未定义 / 区域溢出", "构建日志、map 与符号表", "区分缺少输入与容量不足", "缺哪个符号或哪个段超限", "再核对源文件或链接区域", T.CYAN),
        (307, "下载调试", "SWD 读不到目标", "供电、共地、线序与 NRST", "PA13 / PA14 · 第 34 / 37 脚", "探针能否稳定读取目标 ID", "能连接后再查烧录和启动", T.BLUE),
        (418, "外设", "USART1 收到乱码", "SWS、PPRE2 与完整 BRR", "用 PCLK2 换算波特率", "TX 位宽与接收设置是否一致", "再查接线、电平和数据格式", T.GREEN),
        (529, "硬件", "板卡反复复位", "供电与 NRST 波形", "让波形与失败时刻对应", "电压跌落或复位脉冲", "再查负载、去耦与复位电路", T.AMBER),
        (640, "RTOS", "某任务一直没运行", "任务状态、优先级与阻塞点", "栈水位另作内存余量检查", "任务被阻塞，还是就绪却未调度", "再查等待条件与高优先级负载", T.VIOLET),
    ):
        canvas.line(40, y-12, 920, y-12, stroke=T.GRID)
        canvas.rect(40, y+2, 4, 77, fill=color)
        canvas.text(60, y+24, label, size=21, fill=color, weight="700")
        canvas.text(60, y+60, symptom, size=17, fill=T.TEXT)
        canvas.text(316, y+24, check, size=17, fill=T.TEXT, weight="700")
        canvas.text(316, y+60, detail, size=15, fill=T.MUTED)
        canvas.arrow(598, y+36, 628, y+36, color=color)
        canvas.text(650, y+24, evidence, size=17, fill=T.TEXT)
        canvas.text(650, y+60, next_step, size=15, fill=T.MUTED)
    canvas.line(40, 748, 920, 748, stroke=T.GRID)
    canvas.text(40, 790, "BOOT 选择启动存储区；任务栈水位也不能证明任务获得了 CPU。", size=19, fill=T.TEXT)
    credit(canvas, "自绘。FAQ 检查索引；观测结果用于缩小范围，不代表已经证明根因。")
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

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
    c=Svg(960,880,"项目卡住时，沿第一条失败边界检查","每个项目选择自己的模块路径；不是所有项目都需要存储和升级")
    c.header(tag="19",tag_color=T.CYAN)
    c.text(40,110,"先回答：这次新增的结果，能否单独演示？",size=24,fill=T.TEXT,weight="700")
    rows=(
        (164,"需求同时增加", "范围", "只保留一个可验证输入 / 输出",T.RED),
        (346,"单模块还没跑通", "模块", "断开其他模块，保留配置和错误码",T.AMBER),
        (528,"单独正常，组合失败", "集成", "比较时序、资源和缓冲所有权",T.CYAN),
    )
    for y,question,label,action,color in rows:
        c.rect(40,y,310,98,fill=T.PANEL,stroke=color,rx=8)
        c.text(60,y+41,question,size=23,fill=color,weight="700")
        c.text(60,y+76,"先保存能复现的现象",size=18,fill=T.MUTED)
        c.arrow(362,y+49,416,y+49,color=color,sw=2)
        c.text(440,y+35,label,size=24,fill=color,weight="700")
        c.text(440,y+77,action,size=20,fill=T.TEXT)
    c.line(40,678,920,678,stroke=T.GRID)
    c.text(40,722,"输入 / 配置",size=22,fill=T.CYAN,weight="700")
    c.arrow(218,715,278,715,color=T.CYAN,sw=2)
    c.text(300,722,"预期与实测",size=22,fill=T.GREEN,weight="700")
    c.arrow(478,715,538,715,color=T.GREEN,sw=2)
    c.text(560,722,"失败注入与恢复",size=22,fill=T.AMBER,weight="700")
    c.text(40,777,"交付记录要包含板卡、固件、接线、复现步骤和已知限制。",size=20,fill=T.TEXT)
    c.text(40,814,"证据可用波形、日志或缓冲记录；按要验证的机制选择。",size=18,fill=T.MUTED)
    credit(c,"自绘。本章项目推进方法；按具体项目选择模块与验收项。")
    return c


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

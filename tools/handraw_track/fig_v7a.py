# -*- coding: utf-8 -*-
"""V7a hand-drawn plate: ch43 pair-not-ghost division of labor.

Facts pinned verbatim from docs/v7-delivery/43-ai-pair-programming.md
§机制一「五维分工表：结对不是代笔」:
  初稿  模型 生成第一版代码/文档      你 逐行读，标出「我没验过的行」
  判据  模型 建议可能的判据          你 定义正确性（公共知识还是你的板子？）
  验证  模型 提出验证思路            你 执行验证，记录读数
  排查  模型 列可能原因清单          你 按清单实测归因
  责任  模型 无                      你 全部在你
Thesis: 模型输出是分布，不是事实；责任全部在你。
The 三次一致性实验 is a teaching design (no readings); layout is schematic.

Deterministic: hd.Fig seeds its own RNG; re-running gives the same SVG.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hd import (AMBER_PALE, AMBER_STROKE, BLUE_D, BLUE_FILL, GREEN_D,  # noqa: E402
                GREEN_FILL, INK, MUTED, RED, RED_FILL, WHITE, Fig, save)

STAGE = Path(__file__).resolve().parents[2] / "assets" / "illustrations" / "staged" / "l0-l5-pass" / "figures"


def ch43_pair_not_ghost():
    f = Fig("ch43-pair-not-ghost", "结对不是代笔：模型生成，你定义正确性",
            title_color=BLUE_D, tag="CH 43 · AI 结对")
    f.text(64, 126, "模型输出是分布，不是事实；判据由你定、验证由你做，责任全部在你。",
           size=19, color=MUTED)

    # ---- dimension label strip ----
    rows = ["初稿", "判据", "验证", "排查", "责任"]
    bases = [258, 332, 406, 480, 558]
    for label, y in zip(rows, bases):
        f.text(128, y, label, size=19, color=INK, anchor="middle",
               weight="bold")
    f.line(196, 232, 196, 612, color=MUTED, sw=1.6, amp=0.6)

    # ---- 模型 column (blue) ----
    f.card(210, 158, 430, 478, BLUE_D, fill=BLUE_FILL)
    f.text(425, 194, "模型", size=25, color=BLUE_D, anchor="middle",
           weight="bold")
    f.text(425, 216, "输出是分布", size=13, color=MUTED, anchor="middle")
    f.line(228, 228, 622, 228, color=BLUE_D, sw=1.4, amp=0.5)
    model = [
        ["生成第一版代码/文档"],
        ["建议可能的判据"],
        ["提出验证思路"],
        ["列可能原因清单"],
    ]
    for lines, y in zip(model, bases[:4]):
        for j, ln in enumerate(lines):
            f.text(232, y + j * 25, ln, size=17, color=INK)

    # ---- 你 column (green) ----
    f.card(660, 158, 438, 478, GREEN_D, fill=GREEN_FILL)
    f.text(879, 194, "你", size=25, color=GREEN_D, anchor="middle",
           weight="bold")
    f.text(879, 216, "正确性由你定", size=13, color=MUTED, anchor="middle")
    f.line(678, 228, 1080, 228, color=GREEN_D, sw=1.4, amp=0.5)
    you = [
        ["逐行读，标出", "「我没验过的行」"],
        ["定义正确性", "（公共知识还是你的板子？）"],
        ["执行验证，记录读数"],
        ["按清单实测归因"],
    ]
    for lines, y in zip(you, bases[:4]):
        for j, ln in enumerate(lines):
            f.text(682, y + j * 25, ln, size=17, color=INK)

    # ---- 责任 row: red band, the hard verdict ----
    f.panel(216, 532, 418, 80, RED_FILL, amp=1.6)
    f.panel(666, 532, 426, 80, RED_FILL, amp=1.6)
    f.text(425, 582, "无", size=27, color=MUTED, anchor="middle",
           weight="bold")
    f.text(879, 582, "全部在你", size=27, color=RED, anchor="middle",
           weight="bold")
    f.stamp(985, 656, "责任不可代签", RED, size=17, angle=-7)

    # ---- takeaway + evidence footer ----
    f.htext(54, 738, "模型给初稿与思路；你定判据、做验证、实测归因",
            size=22, color=INK, weight="bold", hl=True)
    f.text(576, 764,
           "分工表转引自 ch43 §机制一 · 一致性实验为教学设计非实测 · 布局示意，非实测",
           size=15, color=MUTED, anchor="middle")
    return f


def ch43_six_delegation_classes():
    """Six delegation classes from 'fine to sign' to 'never'. Facts from
    ch43 (review three steps, official red lines, register caveat)."""
    f = Fig("ch43-six-delegation-classes",
            "六类代签：从随便签到永不代签",
            title_color=BLUE_D, tag="CH 43 · AI 结对")
    f.text(64, 126,
           "评审三步的第一步是归类：把输出里的每个决定标类，判断该类可不可以让模型代签。",
           size=19, color=MUTED)

    rows = [
        ("命名", "变量、函数取个合适的名字", "可代签", GREEN_D, GREEN_FILL),
        ("格式", "排版、风格、批量重命名", "可代签", GREEN_D, GREEN_FILL),
        ("结构", "拆函数、选容器、摆模块", "可代签", GREEN_D, GREEN_FILL),
        ("接口签名", "参数、返回、调用顺序", "谨慎", AMBER_STROKE, AMBER_PALE),
        ("寄存器/时序", "地址、位段、先后顺序", "不可——须对账", RED, RED_FILL),
        ("安全边界", "阈值、超时、终审决定", "永不", RED, RED_FILL),
    ]
    for i, (name, desc, verdict, c, fl) in enumerate(rows):
        y = 164 + i * 72
        f.panel(96, y - 30, 700, 62, fl, amp=1.6)
        f.rect(96, y - 30, 700, 62, color=c, sw=1.8, fill=None, amp=1.6)
        f.text(116, y + 4, name, size=18, color=c, weight="bold")
        f.text(250, y + 4, desc, size=15, color=INK)
        f.pill(620, y - 18, 156, 38, verdict, c, fill=WHITE, size=15)
    f.arrow(840, 190, 840, 570, color=MUTED, sw=2.0, bend=0.0, head=9)
    f.text(864, 200, "代签自由度递减", size=15, color=MUTED, weight="bold")

    # ---- register caveat + red lines ----
    f.panel(96, 560, 700, 78, BLUE_FILL, amp=1.6)
    f.rect(96, 560, 700, 78, color=BLUE_D, sw=1.8, fill=None, amp=1.6)
    f.text(116, 588, "中间地带是寄存器代码：能生成，但必须带对账条件",
           size=15, color=BLUE_D, weight="bold")
    f.text(116, 614, "正确性一半在公共知识（手册），一半在你的板子——对账三问接手",
           size=13.5, color=MUTED)

    f.panel(96, 648, 700, 44, RED_FILL, amp=1.4)
    f.rect(96, 648, 700, 44, color=RED, sw=1.6, fill=None, amp=1.4)
    f.text(116, 676, "官方红线三句（快照 2026-10-27）：分工句 · Logs do not replace review · You remain responsible",
           size=13, color=RED, weight="bold")

    f.htext(64, 730, "归类先于重写：不可代签的，写回提示词要求人工确认",
            size=21, color=INK, weight="bold", hl=True)
    f.text(576, 758,
           "六类清单与红线取自本章快照记录；分级示意，非测量。",
           size=14, color=MUTED, anchor="middle")
    return f


FIGS = {
    "ch43-pair-not-ghost": ch43_pair_not_ghost,
    "ch43-six-delegation-classes": ch43_six_delegation_classes,
}


if __name__ == "__main__":
    names = sys.argv[1:] or list(FIGS)
    STAGE.mkdir(parents=True, exist_ok=True)
    for n in names:
        f = FIGS[n]()
        save(f, str(STAGE / (n + ".svg")))
        print("wrote", STAGE / (n + ".svg"))
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
from hd import (BLUE_D, BLUE_FILL, GREEN_D, GREEN_FILL, INK,  # noqa: E402
                MUTED, RED, RED_FILL, WHITE, Fig, save)

STAGE = Path(__file__).resolve().parents[2] / ".temp" / "l0-l5-pass" / "figures"


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


FIGS = {
    "ch43-pair-not-ghost": ch43_pair_not_ghost,
}


if __name__ == "__main__":
    names = sys.argv[1:] or list(FIGS)
    STAGE.mkdir(parents=True, exist_ok=True)
    for n in names:
        f = FIGS[n]()
        save(f, str(STAGE / (n + ".svg")))
        print("wrote", STAGE / (n + ".svg"))
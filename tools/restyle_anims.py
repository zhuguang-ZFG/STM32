#!/usr/bin/env python3
"""去 AI 味：把 SMIL 动画与自绘 SVG 的扁平色板重映射为全书手绘米纸色系。

只做纯属性值替换（fill/stroke/stop-color/font-family），不动几何与 SMIL 动画元素——
同一映射表可重跑（幂等），映射后文件与手绘知识板（app-*/ch*-handdraw）同一视觉语言：
米纸底、墨色字、普鲁士蓝/灰绿/砖红/拿坡里黄四色语义。

覆盖 docs/public/anim/ 与 docs/public/figures/ 两个目录。

用法：python tools/restyle_anims.py            # 应用到两个目录
      python tools/restyle_anims.py --dry-run  # 只统计命中，不改文件
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ANIM_DIR = REPO / "docs" / "public" / "anim"
FIG_DIR = REPO / "docs" / "public" / "figures"

# 旧（扁平/AI 风）→ 新（手绘米纸色系）。目标色取自 tools/handraw_track/hd.py 的
# 色板常量与手绘板的实际用色；文本灰全部收进墨/暖灰两档。
COLOR_MAP = {
    # 背景与面板
    "#f6f8fa": "#FDF8EA",
    "#f8fafc": "#FBF3DF",
    "#f1f5f7": "#F7EFDA",
    "#ffffff": "#FFFDF6",
    # 主蓝 → 普鲁士蓝两档
    "#3451b2": "#2B5EA7",
    "#dbe7ff": "#DCE6F2",
    "#075e84": "#1F4680",
    # 绿 → 灰绿两档
    "#3eaf7c": "#3F7D57",
    "#1a7f56": "#3F7D57",
    "#1b5c45": "#2E5F42",
    # 琥珀 → 拿坡里黄两档
    "#d97706": "#A8801F",
    "#7a4e00": "#7A5B14",
    # 红 → 砖红
    "#dc2626": "#B3392F",
    # 文本：收进墨与暖灰
    "#333": "#2F2E2B",
    "#17202a": "#2F2E2B",
    "#24292f": "#2F2E2B",
    "#666": "#6E6B60",
    "#5e6872": "#6E6B60",
    # 线框灰：暖化
    "#94a3b8": "#9A937F",
    "#cbd5e1": "#D8D2C0",
    "#e2e8f0": "#E7E2D4",
    # 紫：弱化为暮紫（少量特殊标记用）
    "#5b3a8c": "#6E569B",
    # figures/ 根书自绘色系（与 anim/ 不同的"根书蓝"体系，同样扁平化）
    "#fbfaf7": "#FBF3DF",
    "#e5f3f8": "#DCE6F2",
    "#d7dce1": "#D8D2C0",
    "#8f2d2d": "#B3392F",
    "#1e4d63": "#1F4680",
    "#123a2e": "#2E5F42",
    "#151922": "#2F2E2B",
    "#0d2b22": "#2E5F42",
    "#9a3412": "#B3392F",
    "#dbeafe": "#DCE6F2",
    "#dfe6f0": "#E7E2D4",
}

FONT_MAP = {
    "'Segoe UI','Microsoft YaHei',sans-serif": "'Segoe Print','Comic Sans MS','Microsoft YaHei',sans-serif",
    "Segoe UI,Microsoft YaHei,sans-serif": "Segoe Print,Comic Sans MS,Microsoft YaHei,sans-serif",
}

# 大小写不敏感的十六进制替换（保留原大小写风格无意义——直接落到规范目标色）。
_HEX_RE = {re.compile(re.escape(old), re.IGNORECASE): new for old, new in COLOR_MAP.items()}
_FONT_RES = {re.compile(re.escape(old), re.IGNORECASE): new for old, new in FONT_MAP.items()}


def restyle(text: str) -> tuple[str, int]:
    hits = 0
    for rx, new in _HEX_RE.items():
        text, n = rx.subn(new, text)
        hits += n
    for rx, new in _FONT_RES.items():
        text, n = rx.subn(new, text)
        hits += n
    return text, hits


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    total_files = total_hits = 0
    for directory in (ANIM_DIR, FIG_DIR):
        for path in sorted(directory.glob("*.svg")):
            original = path.read_text(encoding="utf-8")
            restyled, hits = restyle(original)
            if hits == 0:
                continue
            total_files += 1
            total_hits += hits
            if not args.dry_run:
                path.write_text(restyled, encoding="utf-8", newline="\n")
            print(f"{path.name}: {hits} replacements")
    print(f"files touched: {total_files}, replacements: {total_hits}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

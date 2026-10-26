#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Confirm chapters 16, 17, 18, and 19 are still missing the four blocks.

Run from the repository root:

    python3 tools/scan_batch6_chapters.py

Rewrites docs/superpowers/plans/2026-10-25-batch6-16-17-18-19-lock.json and
exits 0 when all eight manuscripts lack the four headings. Chapters 16 and 17
must still have the old pitfall heading. Chapters 18 and 19 must not have it.
Exits 2 without writing the lock otherwise. Does not score other chapters and
does not touch earlier locks.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch6-16-17-18-19-lock.json"
FILES = {
    "16": (
        ROOT / "docs" / "16-低功耗设计.md",
        ROOT / "docs" / "en" / "16-low-power.md",
        "## ⚠️ Pitfalls and troubleshooting",
        True,
    ),
    "17": (
        ROOT / "docs" / "17-调试与性能优化.md",
        ROOT / "docs" / "en" / "17-debug.md",
        "## ⚠️ Pitfalls and troubleshooting",
        True,
    ),
    "18": (
        ROOT / "docs" / "18-常见问题FAQ.md",
        ROOT / "docs" / "en" / "18-faq.md",
        "## ⚠️ Pitfalls and troubleshooting",
        False,
    ),
    "19": (
        ROOT / "docs" / "19-项目实战合集.md",
        ROOT / "docs" / "en" / "19-projects.md",
        "## ⚠️ Pitfalls and troubleshooting",
        False,
    ),
}
ZH_BLOCKS = ("## 原理与边界", "## 关键插图", "## 时序或状态", "## 坑与出处卡")
EN_BLOCKS = (
    "## Principle and boundary",
    "## Key figures",
    "## Timing or state",
    "## Pitfalls and source cards",
)
ZH_OLD = "## ⚠️ 常见坑与排查"


def four_blocks(text: str, headings: tuple[str, ...]) -> bool:
    return any(heading in text for heading in headings)


def main() -> int:
    payload_files: dict[str, dict] = {}
    blocked = False
    for prefix, (zh_path, en_path, en_old, expects_old) in FILES.items():
        if not zh_path.is_file() or not en_path.is_file():
            print(f"missing manuscript for {prefix}", file=sys.stderr)
            return 2
        zh = zh_path.read_text(encoding="utf-8")
        en = en_path.read_text(encoding="utf-8")
        row = {
            "zh": zh_path.relative_to(ROOT).as_posix(),
            "en": en_path.relative_to(ROOT).as_posix(),
            "zh_four_blocks": four_blocks(zh, ZH_BLOCKS),
            "en_four_blocks": four_blocks(en, EN_BLOCKS),
            "expects_old_pitfall": expects_old,
            "zh_old_pitfall": ZH_OLD in zh,
            "en_old_pitfall": en_old in en,
            "en_old_heading": en_old,
        }
        payload_files[prefix] = row
        if row["zh_four_blocks"] or row["en_four_blocks"]:
            print(f"{prefix} already has a four-block heading; stop", file=sys.stderr)
            blocked = True
        if expects_old and (not row["zh_old_pitfall"] or not row["en_old_pitfall"]):
            print(f"{prefix} is missing the old pitfall heading; stop", file=sys.stderr)
            blocked = True
        if (not expects_old) and (row["zh_old_pitfall"] or row["en_old_pitfall"]):
            print(f"{prefix} already has an old pitfall heading; do not invent one to delete", file=sys.stderr)
            blocked = True
        old = "yes" if row["zh_old_pitfall"] and row["en_old_pitfall"] else "no"
        print(
            f"{prefix} four_blocks={'yes' if row['zh_four_blocks'] or row['en_four_blocks'] else 'no'} "
            f"old_pitfall={old}"
        )
    if blocked:
        return 2
    baseline = subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True
    ).strip()
    payload = {
        "rubric": "2026-10-25-classic-encyclopedia-batch6-16-17-18-19",
        "baseline": baseline,
        "chapters": ["16", "17", "18", "19"],
        "four_blocks_absent": True,
        "old_pitfall_heading_present": True,
        "chapters_without_old_pitfall": ["18", "19"],
        "files": payload_files,
    }
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOCK_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"baseline={baseline}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

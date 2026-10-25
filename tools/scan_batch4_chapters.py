#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Confirm chapters 01, 07, 10, and 11 are still missing the four blocks.

Run from the repository root:

    python3 tools/scan_batch4_chapters.py

Rewrites docs/superpowers/plans/2026-10-25-batch4-01-07-10-11-lock.json and
exits 0 when all eight manuscripts lack the four headings and still have the
old pitfall heading. Exits 2 without writing the lock if a four-block heading
is already present, or if the old pitfall heading is already gone.
Does not score other chapters and does not touch the sample lock, the
batch-2 lock, or the batch-3 lock.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch4-01-07-10-11-lock.json"
FILES = {
    "01": (
        ROOT / "docs" / "01-开发环境搭建.md",
        ROOT / "docs" / "en" / "01-dev-environment.md",
    ),
    "07": (
        ROOT / "docs" / "07-I2C总线.md",
        ROOT / "docs" / "en" / "07-i2c.md",
    ),
    "10": (
        ROOT / "docs" / "10-DMA.md",
        ROOT / "docs" / "en" / "10-dma.md",
    ),
    "11": (
        ROOT / "docs" / "11-RTC与看门狗.md",
        ROOT / "docs" / "en" / "11-rtc-watchdog.md",
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
EN_OLD = "## ⚠️ Pitfalls and troubleshooting"


def four_blocks(text: str, headings: tuple[str, ...]) -> bool:
    return any(heading in text for heading in headings)


def main() -> int:
    payload_files: dict[str, dict] = {}
    blocked = False
    for prefix, (zh_path, en_path) in FILES.items():
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
            "zh_old_pitfall": ZH_OLD in zh,
            "en_old_pitfall": EN_OLD in en,
        }
        payload_files[prefix] = row
        if row["zh_four_blocks"] or row["en_four_blocks"]:
            print(f"{prefix} already has a four-block heading; stop", file=sys.stderr)
            blocked = True
        if not row["zh_old_pitfall"] or not row["en_old_pitfall"]:
            print(f"{prefix} is missing the old pitfall heading; stop", file=sys.stderr)
            blocked = True
        print(
            f"{prefix} four_blocks={'yes' if row['zh_four_blocks'] or row['en_four_blocks'] else 'no'} "
            f"old_pitfall={'yes' if row['zh_old_pitfall'] and row['en_old_pitfall'] else 'no'}"
        )
    if blocked:
        return 2
    baseline = subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True
    ).strip()
    payload = {
        "rubric": "2026-10-25-classic-encyclopedia-batch4-01-07-10-11",
        "baseline": baseline,
        "chapters": ["01", "07", "10", "11"],
        "four_blocks_absent": True,
        "old_pitfall_heading_present": True,
        "files": payload_files,
    }
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOCK_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"baseline={baseline}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

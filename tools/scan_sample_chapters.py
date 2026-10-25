#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Score the sample-chapter pools once, before the four new headings exist.

Run from the repository root:

    python3 tools/scan_sample_chapters.py

The script writes docs/superpowers/plans/2026-10-25-sample-chapter-lock.json
and exits 0 when the rubric selects peripheral 03 and foundation 00.
If the tree has already grown the heading 原理与边界, it refuses to re-score
and exits 0 only when the lock file already records 03 and 00.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-sample-chapter-lock.json"
PERIPHERAL = [f"{i:02d}" for i in range(3, 15)] + ["16"]
FOUNDATION = ["00", "01", "02"]
LOCAL_SUFFIXES = {".svg", ".gif", ".jpg", ".jpeg", ".png"}
ORDERABLE = re.compile(r"STM32[A-Z]\d{3}[A-Z][A-Z0-9]{3,}")
VOID = re.compile(r"作废|整行重写|不再成立|does not hold|is void")
IMG = re.compile(r"""src=["']([^"']+)["']""")
VIDEO = re.compile(r"<!-- video:.*?<!-- /video:.*?-->", re.S)
SERIES = {
    "F1": re.compile(r"RM0008|STM32F10|\bF103\b|\bF1\b"),
    "F4": re.compile(r"RM0090|RM0383|STM32F4|\bF4\b"),
    "G0": re.compile(r"RM0444|STM32G0|\bG0\b"),
    "L4": re.compile(r"RM0351|STM32L4|\bL4\b"),
    "H7": re.compile(r"RM0433|RM0399|STM32H7|\bH7\b"),
}


def chapters(directory: Path) -> dict[str, Path]:
    found: dict[str, Path] = {}
    for path in sorted(directory.glob("[0-2][0-9]-*.md")):
        found[path.name[:2]] = path
    return found


def strip_unreadable(text: str) -> str:
    text = VIDEO.sub("", text)
    text = re.sub(r"<p align=\"center\">.*?</p>", "", text, flags=re.S)
    fence = chr(96) * 3
    text = re.sub(fence + r".*?" + fence, "", text, flags=re.S)
    return text


def tables(text: str) -> list[tuple[str, list[str]]]:
    lines = text.splitlines()
    found: list[tuple[str, list[str]]] = []
    index = 0
    while index < len(lines):
        if lines[index].startswith("|") and index + 1 < len(lines) and re.match(r"\|\s*-+", lines[index + 1]):
            header = lines[index]
            body: list[str] = []
            cursor = index + 2
            while cursor < len(lines) and lines[cursor].startswith("|"):
                body.append(lines[cursor])
                cursor += 1
            found.append((header, body))
            index = cursor
        else:
            index += 1
    return found


def has_boundary(text: str) -> bool:
    parts = re.split(r"(?m)^#{2,3} .*$", text)
    heads = re.findall(r"(?m)^#{2,3} .*$", text)
    chunks = [("preamble", parts[0]), *zip(heads, parts[1:])]
    for heading, body in chunks:
        blob = heading + "\n" + body
        if ORDERABLE.search(blob) and VOID.search(blob):
            return True
    return False


def has_timing_or_state(text: str) -> bool:
    """A debounce-delay table is not the peripheral's timing or state."""
    for header, rows in tables(strip_unreadable(text)):
        if re.search(r"现象|Symptom|原因|Cause|消抖|debounce", header, re.I):
            continue
        blob = header + "\n" + "\n".join(rows)
        if re.search(r"时序|时间尺度|周期|波特|采样时间|唤醒时间|PSC|ARR|BRR|分频|SCK", header) and re.search(r"\d", blob):
            return True
        if re.search(r"阶段|步骤|状态", header) and len(rows) >= 3:
            return True
        if re.search(r"\d+(?:\.\d+)?\s*(?:µs|μs|ns|ms)\b", blob):
            return True
        if ("普通模式" in blob and "循环模式" in blob) or ("睡眠" in blob and "待机" in blob):
            return True
    return False


def pitfalls_linked(text: str) -> bool:
    match = re.search(r"(?m)^## .*(常见坑|Pitfalls).*$", text)
    if not match:
        return False
    rest = text[match.end():]
    nxt = re.search(r"(?m)^## ", rest)
    section = rest[: nxt.start()] if nxt else rest
    return "#source-" in section


def local_images(text: str, chapter_path: Path) -> list[str]:
    visible = VIDEO.sub("", text)
    found: list[str] = []
    for src in IMG.findall(visible):
        low = src.lower().split("?", 1)[0]
        if low.startswith("http"):
            continue
        if Path(low).suffix.lower() not in LOCAL_SUFFIXES:
            continue
        found.append(src)
    return found


def figure_is_numbered_state(chapter_path: Path, src: str) -> bool:
    if not src.lower().split("?", 1)[0].endswith(".svg"):
        return False
    target = (chapter_path.parent / src).resolve()
    if not target.is_file():
        return False
    raw = target.read_text(encoding="utf-8", errors="replace")
    texts = re.findall(r"<text[^>]*>(.*?)</text>", raw, flags=re.S)
    blob = re.sub(r"<[^>]+>", " ", " ".join(texts))
    if "BOOT0" in blob:
        return True
    if re.search(r"\d+\s*MHz", blob) and re.search(r"PLL|时钟|APB", blob):
        return True
    return False


def series_flags(text: str) -> dict[str, bool]:
    return {name: bool(pattern.search(text)) for name, pattern in SERIES.items()}


def figure_roles(chapter_path: Path, src: str) -> list[str]:
    """Record roles. Selection does not read this list."""
    roles: list[str] = []
    low = src.lower().split("?", 1)[0]
    suffix = Path(low).suffix
    if suffix in {".jpg", ".jpeg", ".png"}:
        roles.append("实拍")
    if figure_is_numbered_state(chapter_path, src):
        roles.append("带数字的时序或状态")
    blob = ""
    if suffix == ".svg":
        target = (chapter_path.parent / src).resolve()
        if target.is_file():
            raw = target.read_text(encoding="utf-8", errors="replace")
            texts = re.findall(r"<text[^>]*>(.*?)</text>", raw, flags=re.S)
            blob = re.sub(r"<[^>]+>", " ", " ".join(texts))
    if re.search(r"LQFP|引脚|PA\d+|PC\d+|PB\d+", blob) or re.search(
        r"pinout|bluepill|nucleo|board", Path(low).name
    ):
        roles.append("板卡/引脚结构")
    if suffix == ".gif" or (
        suffix == ".svg" and "带数字的时序或状态" not in roles and "板卡/引脚结构" not in roles
    ):
        roles.append("简化示意")
    if not roles:
        roles.append("简化示意")
    return roles


def score_one(prefix: str, path: Path, english: Path) -> dict:
    chinese = path.read_text(encoding="utf-8")
    english_text = english.read_text(encoding="utf-8")
    images = local_images(chinese, path)
    english_images = local_images(english_text, english)
    numbered = any(figure_is_numbered_state(path, src) for src in images)
    english_numbered = any(figure_is_numbered_state(english, src) for src in english_images)
    boundary = has_boundary(chinese)
    timing = has_timing_or_state(chinese)
    linked = pitfalls_linked(chinese)
    missing = (0 if boundary else 1) + (0 if timing else 1) + (0 if linked else 1)
    suffixes: dict[str, int] = {}
    for src in images:
        suffix = Path(src.lower()).suffix
        suffixes[suffix] = suffixes.get(suffix, 0) + 1
    english_suffixes: dict[str, int] = {}
    for src in english_images:
        suffix = Path(src.lower()).suffix
        english_suffixes[suffix] = english_suffixes.get(suffix, 0) + 1
    z_lines = len(chinese.splitlines())
    e_lines = len(english_text.splitlines())
    return {
        "prefix": prefix,
        "zh": path.as_posix(),
        "en": english.as_posix(),
        "zh_lines": z_lines,
        "en_lines": e_lines,
        "translation_gap": e_lines * 2 < z_lines,
        "local_images": suffixes,
        "en_local_images": english_suffixes,
        "local_image_count": len(images),
        "en_local_image_count": len(english_images),
        "numbered_timing_or_state_figure": numbered,
        "en_numbered_timing_or_state_figure": english_numbered,
        "figures_zh": [{"src": src, "roles": figure_roles(path, src)} for src in images],
        "figures_en": [{"src": src, "roles": figure_roles(english, src)} for src in english_images],
        "series_en": series_flags(english_text),
        "principle_boundary": boundary,
        "timing_or_state": timing,
        "pitfall_source_link": linked,
        "missing_count": missing,
        "series_zh": series_flags(chinese),
    }


def select(rows: list[dict]) -> dict:
    peripheral = [row for row in rows if row["prefix"] in PERIPHERAL]
    foundation = [row for row in rows if row["prefix"] in FOUNDATION]
    highest = max(row["missing_count"] for row in peripheral)
    peripheral_tied = sorted(row["prefix"] for row in peripheral if row["missing_count"] == highest)
    unnumbered = [
        row
        for row in foundation
        if not row["numbered_timing_or_state_figure"] or not row["en_numbered_timing_or_state_figure"]
    ]
    foundation_pool = unnumbered if unnumbered else foundation
    fewest = min(min(row["local_image_count"], row["en_local_image_count"]) for row in foundation_pool)
    foundation_tied = sorted(
        row["prefix"]
        for row in foundation_pool
        if min(row["local_image_count"], row["en_local_image_count"]) == fewest
    )
    return {
        "peripheral": peripheral_tied[0],
        "peripheral_tied": peripheral_tied,
        "peripheral_missing_count": highest,
        "foundation": foundation_tied[0],
        "foundation_tied": foundation_tied,
    }


def already_thickened(zh: dict[str, Path]) -> bool:
    for path in zh.values():
        if "## 原理与边界" in path.read_text(encoding="utf-8"):
            return True
    return False


def main() -> int:
    zh = chapters(ROOT / "docs")
    en = chapters(ROOT / "docs" / "en")
    if already_thickened(zh):
        if not LOCK_PATH.is_file():
            print("chapters already contain 原理与边界, and the lock file is missing", file=sys.stderr)
            return 2
        lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
        print(json.dumps({"kept_lock": lock["peripheral"], "foundation": lock["foundation"]}, ensure_ascii=False))
        return 0 if lock["peripheral"] == "03" and lock["foundation"] == "00" else 2

    rows = [score_one(prefix, zh[prefix], en[prefix]) for prefix in FOUNDATION + PERIPHERAL]
    choice = select(rows)
    payload = {
        "rubric": "2026-10-25-classic-encyclopedia-sample-chapters",
        "baseline": subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True
        ).strip(),
        "peripheral": choice["peripheral"],
        "foundation": choice["foundation"],
        "peripheral_tied": choice["peripheral_tied"],
        "foundation_tied": choice["foundation_tied"],
        "peripheral_missing_count": choice["peripheral_missing_count"],
        "rows": rows,
    }
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOCK_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"peripheral={choice['peripheral']} tied={choice['peripheral_tied']} "
        f"missing={choice['peripheral_missing_count']}"
    )
    print(f"foundation={choice['foundation']} tied={choice['foundation_tied']}")
    if choice["peripheral"] != "03" or choice["foundation"] != "00":
        print("lock disagrees with the plan's baseline winners; stop and edit later tasks", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())

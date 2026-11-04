#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rebuild SVG ROWS + GIF listing hash + audit/CHAPTERS sequences after q4 embeds."""
from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "assets"
TEST = ROOT / "stm32-book" / "tests" / "test_sample_svg_c.py"
AUDIT = ROOT / "stm32-book" / "tests" / "test_book_audit.py"
ADV = ROOT / "stm32-book" / "tests" / "test_advanced_visuals.py"
UPLIFT = ROOT / "stm32-book" / "audits" / "visual-quality-uplift.md"

VIDEO_BLOCK_RE = re.compile(
    r'<p align="center">\s*<video\b.*?</video>.*?</p>',
    re.S | re.I,
)
IMG_RE = re.compile(r'<img\b[^>]*\bsrc="([^"]+)"', re.I)

ZH_FILES = {
    "00": ROOT / "docs" / "00-如何学习STM32.md",
    "01": ROOT / "docs" / "01-开发环境搭建.md",
    "18": ROOT / "docs" / "18-常见问题FAQ.md",
    "19": ROOT / "docs" / "19-项目实战合集.md",
    "20": ROOT / "docs" / "20-学习资源与工具链.md",
    "21": ROOT / "docs" / "21-原理图与实物图鉴.md",
    "22": ROOT / "docs" / "22-仿真实验Wokwi与Renode.md",
}

ADV_KEYS = {
    "00": 'ROOT / "docs" / "00-如何学习STM32.md"',
    "01": 'ROOT / "docs" / "01-开发环境搭建.md"',
    "18": 'ROOT / "docs" / "18-常见问题FAQ.md"',
    "19": 'ROOT / "docs" / "19-项目实战合集.md"',
    "20": 'ROOT / "docs" / "20-学习资源与工具链.md"',
    "21": 'ROOT / "docs" / "21-原理图与实物图鉴.md"',
    "22": 'ROOT / "docs" / "22-仿真实验Wokwi与Renode.md"',
}

AUDIT_IDS = ("18", "19", "20", "21", "22")
BEFORE = {"00": 7, "01": 9, "18": 4, "19": 8, "20": 7, "21": 3, "22": 5}


def text_hash(svg: str) -> str:
    parts = re.findall(r"<text\b[^>]*>(.*?)</text>", svg, flags=re.DOTALL)
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


def rebuild_rows() -> tuple[str, int, str]:
    svgs = sorted(ASSETS.rglob("*.svg"), key=lambda p: p.relative_to(ASSETS).as_posix())
    lines = []
    for path in svgs:
        rel = path.relative_to(ASSETS).as_posix()
        raw = path.read_bytes()
        text = raw.decode("utf-8")
        m = re.search(r'\bwidth="(\d+)"[^>]*\bheight="(\d+)"', text)
        if not m:
            m = re.search(r'\bheight="(\d+)"[^>]*\bwidth="(\d+)"', text)
            w, h = int(m.group(2)), int(m.group(1))
        else:
            w, h = int(m.group(1)), int(m.group(2))
        digest = text_hash(text)
        lines.append(f"{rel} {w}x{h} {len(raw)} {digest}")
    rows = "\n".join(lines) + "\n"
    gifs = sorted((ASSETS / "gif").glob("*.gif"), key=lambda p: p.name)
    listing = "".join(f"{p.name} {hashlib.sha256(p.read_bytes()).hexdigest()}\n" for p in gifs)
    gif_hash = hashlib.sha256(listing.encode("utf-8")).hexdigest()
    return rows, len(svgs), gif_hash


def patch_test_sample(rows: str, n: int, gif_hash: str) -> None:
    text = TEST.read_text(encoding="utf-8")
    text2, c1 = re.subn(
        r'ROWS = """\n.*?"""',
        'ROWS = """\n' + rows + '"""',
        text,
        count=1,
        flags=re.S,
    )
    if c1 != 1:
        raise SystemExit(f"ROWS replace count={c1}")
    text2, c2 = re.subn(
        r"self\.assertEqual\(\d+, len\(found\)\)",
        f"self.assertEqual({n}, len(found))",
        text2,
        count=1,
    )
    if c2 != 1:
        raise SystemExit(f"len(found) replace count={c2}")
    text2, c3 = re.subn(
        r'(self\.assertEqual\(\s*")[0-9a-f]{64}(",\s*hashlib\.sha256\(listing)',
        rf"\g<1>{gif_hash}\2",
        text2,
        count=1,
    )
    if c3 != 1:
        raise SystemExit(f"gif hash replace count={c3}")
    TEST.write_text(text2, encoding="utf-8")
    print("updated", TEST.name, "svgs", n, "gif_hash", gif_hash)


def img_only_assets(path: Path) -> list[str]:
    raw = path.read_text(encoding="utf-8")
    raw = VIDEO_BLOCK_RE.sub("", raw)
    return [Path(src).name for src in IMG_RE.findall(raw)]


def full_asset_sequence(path: Path) -> list[str]:
    sys.path.insert(0, str(ROOT / "tools"))
    from audit_book import extract_visual_anchors  # type: ignore

    text = path.read_text(encoding="utf-8")
    anchors = extract_visual_anchors(text)
    out: list[str] = []
    for a in anchors:
        out.extend(Path(s).name for s in a.assets)
    return out


def update_audit(seq: dict[str, list[str]]) -> None:
    text = AUDIT.read_text(encoding="utf-8")
    for cid in AUDIT_IDS:
        assets = seq[cid]
        body = ",\n                ".join(f'"{a}"' for a in assets)
        new_tuple = f'"{cid}": (\n                {body},\n            )'
        pat = rf'"{cid}":\s*\((?:[^()]|\([^()]*\))*?\)'
        text2, n = re.subn(pat, new_tuple, text, count=1)
        if n != 1:
            raise SystemExit(f"audit replace failed for {cid}: {n}")
        text = text2
        print(f"audit {cid}: {len(assets)} assets")
    AUDIT.write_text(text, encoding="utf-8")


def update_advanced(img_seq: dict[str, list[str]]) -> None:
    text = ADV.read_text(encoding="utf-8")
    for cid, key in ADV_KEYS.items():
        assets = img_seq[cid]
        body = ",\n            ".join(f'"{a}"' for a in assets)
        entry = (
            f"{key}: (\n"
            f"        {len(assets)},\n"
            f"        (\n"
            f"            {body},\n"
            f"        ),\n"
            f"    )"
        )
        if key not in text:
            raise SystemExit(f"CHAPTERS key missing for {cid}: {key}")
        pat = re.escape(key) + r"\s*:\s*\([\s\S]*?\n    \),"
        text2, n = re.subn(pat, entry + ",", text, count=1)
        if n != 1:
            pat2 = re.escape(key) + r"\s*:\s*\([\s\S]*?\n    \)"
            text2, n = re.subn(pat2, entry, text, count=1)
            if n != 1:
                raise SystemExit(f"CHAPTERS replace failed for {cid}: {n}")
        text = text2
        print(f"CHAPTERS update {cid}: {len(assets)}")
    ADV.write_text(text, encoding="utf-8")


def update_uplift(img_seq: dict[str, list[str]]) -> None:
    text = UPLIFT.read_text(encoding="utf-8")
    if "Batch 4 — ch00" in text:
        print("uplift already has batch4")
        return
    rows = []
    for cid in ["00", "01", "18", "19", "20", "21", "22"]:
        after = len(img_seq[cid])
        rows.append(f"| ch{cid} | {BEFORE[cid]} | **{after}** | +{after - BEFORE[cid]} |")
    section = """

## Batch 4 — ch00/01 + ch18–22

Date: 2026-11-04 (America/Adak). Same bar as prior quality batches: denser Handraw figures, remade AUX GIFs, FA-002 CSS-SVG anims. Video untouched.

### New static Handraw SVGs (+18)

| Chapter | Assets |
|---|---|
| ch00 | `sample-00-three-ways.svg`, `sample-00-roadmap-gates.svg` |
| ch01 | `sample-01-env-compare.svg`, `sample-01-rdp-unlock.svg` |
| ch18 | `sample-18-link-map.svg`, `sample-18-hardfault-ladder.svg`, `sample-18-uart-garbled.svg` |
| ch19 | `sample-19-pick-ladder.svg`, `sample-19-sram-budget.svg` |
| ch20 | `sample-20-manual-names.svg`, `sample-20-lib-compare.svg` |
| ch21 | `sample-21-vdd-3v3.svg`, `sample-21-hse-load.svg`, `sample-21-usb-ttl.svg`, `sample-21-nrst-boot0.svg` |
| ch22 | `sample-22-wokwi-scope.svg`, `sample-22-renode-path.svg`, `sample-22-hw-gap.svg` |

### New CSS-SVG mechanism animations (+7)

| Chapter | Asset |
|---|---|
| ch00 | `sample-00-boot-fetch-flow.svg` |
| ch01 | `sample-01-flash-swd-flow.svg` |
| ch18 | `sample-18-boot0-flow.svg` |
| ch19 | `sample-19-slot-fill-flow.svg` |
| ch20 | `sample-20-evidence-flow.svg` |
| ch21 | `sample-21-crystal-boot-flow.svg` |
| ch22 | `sample-22-sim-pick-flow.svg` |

### Remade crude AUX GIFs (in place, test-bounded)

`boot0-low.gif`, `one-slot.gif`, `swd-fetch.gif` — denser multi-panel frames; builders in `tools/gen_gifs.py` via `tools/sample_figs_quality4/gif_snippets/`.

### Embeds

zh + en for all 25 new assets (50 insert ops) via `tools/sample_figs_quality4/embed_q4.py`.

### Anchor deltas (ADV <img> count; video stripped)

| Chapter | Before | After | Δ |
|---|---:|---:|---:|
""" + "\n".join(rows) + """

### Gates

`pytest` book tests + `tools/check_assets.py` + `build_html.py --check` (zh+en) green after this batch.

### Next round

ch23–28 + appendix (same bar). No video.
"""
    UPLIFT.write_text(text.rstrip() + section + "\n", encoding="utf-8")
    print("appended batch4 to uplift")


def main() -> None:
    rows, n, gif_hash = rebuild_rows()
    patch_test_sample(rows, n, gif_hash)
    img_seq = {cid: img_only_assets(p) for cid, p in ZH_FILES.items()}
    full_seq = {cid: full_asset_sequence(p) for cid, p in ZH_FILES.items()}
    for cid in ZH_FILES:
        print(f"seq {cid}: img={len(img_seq[cid])} full={len(full_seq[cid])}")
    update_audit(full_seq)
    update_advanced(img_seq)
    update_uplift(img_seq)
    print("done")


if __name__ == "__main__":
    main()

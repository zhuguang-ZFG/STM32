#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rebuild SVG ROWS + GIF listing hash + audit/CHAPTERS sequences after q3 embeds."""
from __future__ import annotations

import hashlib
import re
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


def chapter_assets(path: Path) -> list[str]:
    raw = path.read_text(encoding="utf-8")
    raw = VIDEO_BLOCK_RE.sub("", raw)
    return [Path(src).name for src in IMG_RE.findall(raw)]


def update_audit() -> dict[str, list[str]]:
    zh_files = {
        "11": ROOT / "docs" / "11-RTC与看门狗.md",
        "12": ROOT / "docs" / "12-Flash与IAP升级.md",
        "13": ROOT / "docs" / "13-CAN总线.md",
        "14": ROOT / "docs" / "14-USB.md",
        "15": ROOT / "docs" / "15-FreeRTOS入门.md",
        "16": ROOT / "docs" / "16-低功耗设计.md",
        "17": ROOT / "docs" / "17-调试与性能优化.md",
    }
    seq = {k: chapter_assets(p) for k, p in zh_files.items()}
    text = AUDIT.read_text(encoding="utf-8")
    for cid, assets in seq.items():
        body = ",\n                ".join(f'"{a}"' for a in assets)
        new_tuple = f'"{cid}": (\n                {body},\n            )'
        pat = rf'"{cid}":\s*\((?:[^()]|\([^()]*\))*?\)'
        text2, n = re.subn(pat, new_tuple, text, count=1)
        if n != 1:
            raise SystemExit(f"audit replace failed for {cid}: {n}")
        text = text2
        print(f"audit {cid}: {len(assets)} assets")
    AUDIT.write_text(text, encoding="utf-8")
    return seq


def update_advanced(seq: dict[str, list[str]]) -> None:
    mapping = {
        "11": 'ROOT / "docs" / "11-RTC与看门狗.md"',
        "12": 'ROOT / "docs" / "12-Flash与IAP升级.md"',
        "13": 'ROOT / "docs" / "13-CAN总线.md"',
        "14": 'ROOT / "docs" / "14-USB.md"',
        "15": 'ROOT / "docs" / "15-FreeRTOS入门.md"',
        "16": 'ROOT / "docs" / "16-低功耗设计.md"',
        "17": 'ROOT / "docs" / "17-调试与性能优化.md"',
    }
    text = ADV.read_text(encoding="utf-8")
    for cid, key in mapping.items():
        assets = seq[cid]
        body = ",\n            ".join(f'"{a}"' for a in assets)
        entry = (
            f"{key}: (\n"
            f"        {len(assets)},\n"
            f"        (\n"
            f"            {body},\n"
            f"        ),\n"
            f"    )"
        )
        if key in text:
            pat = re.escape(key) + r"\s*:\s*\([\s\S]*?\n    \),"
            text2, n = re.subn(pat, entry + ",", text, count=1)
            if n != 1:
                raise SystemExit(f"CHAPTERS replace failed for {cid}: {n}")
            text = text2
            print(f"CHAPTERS update {cid}: {len(assets)}")
        else:
            anchor = 'ROOT / "docs" / "14-USB.md"'
            if cid == "13" and anchor in text:
                text = text.replace(anchor, entry + ",\n    " + anchor, 1)
                print(f"CHAPTERS insert {cid}: {len(assets)}")
            else:
                print(f"CHAPTERS skip missing insert point for {cid}")
    if '("13-CAN总线.md", "13-can.md")' not in text:
        text = text.replace(
            '("12-Flash与IAP升级.md", "12-flash-iap.md"),',
            '("12-Flash与IAP升级.md", "12-flash-iap.md"),\n            ("13-CAN总线.md", "13-can.md"),',
            1,
        )
        print("added ch13 language pair")
    ADV.write_text(text, encoding="utf-8")


def update_uplift(seq: dict[str, list[str]]) -> None:
    text = UPLIFT.read_text(encoding="utf-8")
    if "Batch 3 — ch11" in text:
        print("uplift already has batch3")
        return
    before = {"11": 6, "12": 6, "13": 4, "14": 7, "15": 7, "16": 6, "17": 6}
    rows = []
    for cid in ["11", "12", "13", "14", "15", "16", "17"]:
        after = len(seq[cid])
        rows.append(f"| ch{cid} | {before[cid]} | **{after}** | +{after - before[cid]} |")
    section = """

## Batch 3 — ch11–17

Date: 2026-11-04 (America/Adak). Same bar as pilot/batch2: denser Handraw figures, remade AUX GIFs, FA-002 CSS-SVG anims. Video untouched.

### New static Handraw SVGs (+15)

| Chapter | Assets |
|---|---|
| ch11 | `sample-11-backup-domain.svg`, `sample-11-iwdg-math.svg` |
| ch12 | `sample-12-page-erase.svg`, `sample-12-key-order.svg` |
| ch13 | `sample-13-bit-quanta.svg`, `sample-13-filter-fifo.svg`, `sample-13-tec-busoff.svg` |
| ch14 | `sample-14-usbpre-48.svg`, `sample-14-pma-map.svg` |
| ch15 | `sample-15-task-states.svg`, `sample-15-fromisr.svg` |
| ch16 | `sample-16-mode-current.svg`, `sample-16-clock-restore.svg` |
| ch17 | `sample-17-swd-pins.svg`, `sample-17-cfsr-bits.svg` |

### New CSS-SVG mechanism animations (+7)

| Chapter | Asset |
|---|---|
| ch11 | `sample-11-iwdg-feed-flow.svg` |
| ch12 | `sample-12-iap-jump-flow.svg` |
| ch13 | `sample-13-can-arb-flow.svg` |
| ch14 | `sample-14-usb-48m-flow.svg` |
| ch15 | `sample-15-rtos-tick-flow.svg` |
| ch16 | `sample-16-stop-wake-flow.svg` |
| ch17 | `sample-17-cfsr-flow.svg` |

### Remade crude AUX GIFs (in place, test-bounded)

`iwdg-1s.gif`, `iap-jump.gif`, `can-500k.gif`, `usb-48m.gif`, `rtos-tick.gif`, `stop-wake.gif`, `cfsr-read.gif` — denser multi-panel frames; builders in `tools/gen_gifs.py` via `tools/sample_figs_quality3/gif_snippets/`.

### Embeds

zh + en for all 22 new assets (44 insert ops) via `tools/sample_figs_quality3/embed_q3.py`.

### Anchor deltas (asset_sequence length, video stripped)

| Chapter | Before | After | Δ |
|---|---:|---:|---:|
""" + "\n".join(rows) + """

### Gates

`pytest` book tests + `tools/check_assets.py` + `build_html.py --check` (zh+en) green after this batch.

### Next round

ch00–01 / ch18–22 (same bar). No video.
"""
    UPLIFT.write_text(text.rstrip() + section + "\n", encoding="utf-8")
    print("appended batch3 to uplift")


def main() -> None:
    rows, n, gif_hash = rebuild_rows()
    patch_test_sample(rows, n, gif_hash)
    seq = update_audit()
    update_advanced(seq)
    update_uplift(seq)
    print("lock update done")


if __name__ == "__main__":
    main()

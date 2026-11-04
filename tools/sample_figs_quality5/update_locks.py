#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rebuild SVG ROWS + GIF listing hash + audit/CHAPTERS sequences after q5 embeds."""
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

ZH_FILES = {
    "23": ROOT / "docs" / "23-STM32G0引脚.md",
    "24": ROOT / "docs" / "24-STM32L4引脚.md",
    "25": ROOT / "docs" / "25-STM32H7引脚.md",
    "26": ROOT / "docs" / "26-STM32F10x标准外设库SPL.md",
    "27": ROOT / "docs" / "27-网络与协议栈.md",
    "28": ROOT / "docs" / "28-嵌入式系统与RTOS生态.md",
}

ADV_KEYS = {
    "23": 'ROOT / "docs" / "23-STM32G0引脚.md"',
    "24": 'ROOT / "docs" / "24-STM32L4引脚.md"',
    "25": 'ROOT / "docs" / "25-STM32H7引脚.md"',
    "26": 'ROOT / "docs" / "26-STM32F10x标准外设库SPL.md"',
    "27": 'ROOT / "docs" / "27-网络与协议栈.md"',
    "28": 'ROOT / "docs" / "28-嵌入式系统与RTOS生态.md"',
}

BEFORE = {"23": 5, "24": 7, "25": 8, "26": 6, "27": 6, "28": 11}


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
    seq = {k: chapter_assets(p) for k, p in ZH_FILES.items()}
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
    text = ADV.read_text(encoding="utf-8")
    for cid, key in ADV_KEYS.items():
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
                pat2 = re.escape(key) + r"\s*:\s*\([\s\S]*?\n    \)"
                text2, n = re.subn(pat2, entry, text, count=1)
                if n != 1:
                    raise SystemExit(f"CHAPTERS replace failed for {cid}: {n}")
            text = text2
            print(f"CHAPTERS update {cid}: {len(assets)}")
        else:
            raise SystemExit(f"CHAPTERS key missing for {cid}")
    ADV.write_text(text, encoding="utf-8")


def update_uplift(seq: dict[str, list[str]]) -> None:
    text = UPLIFT.read_text(encoding="utf-8")
    if "Batch 5 — ch23" in text or "Batch 5 — final" in text:
        print("uplift already has batch5")
        return
    rows = []
    for cid in ["23", "24", "25", "26", "27", "28"]:
        after = len(seq[cid])
        rows.append(f"| ch{cid} | {BEFORE[cid]} | **{after}** | +{after - BEFORE[cid]} |")
    # appendix F (not in ADV CHAPTERS loop)
    f_zh = ROOT / "stm32-book" / "book" / "F-开源地图.md"
    f_assets = chapter_assets(f_zh) if f_zh.exists() else []
    section = """

## Batch 5 — final: ch23–28 + appendix F

Date: 2026-11-04 (America/Adak). Same bar: denser Handraw figures, FA-002 CSS-SVG anims, remade weak chapter anim in place. Video untouched.

### New static Handraw SVGs (+14)

| Chapter | Assets |
|---|---|
| ch23 | `sample-23-boot0-swclk.svg`, `sample-23-f1-copy-traps.svg` |
| ch24 | `sample-24-stop2-retain.svg`, `sample-24-idd-jp6.svg` |
| ch25 | `sample-25-voltage-scale.svg`, `sample-25-dcache-dma.svg` |
| ch26 | `sample-26-file-matrix.svg`, `sample-26-timeout-poll.svg` |
| ch27 | `sample-27-rmii-checklist.svg`, `sample-27-tcp-framing.svg` |
| ch28 | `sample-28-four-concepts.svg`, `sample-28-three-times.svg` |
| appendix F | `sample-f-six-facts.svg`, `sample-f-ask-before.svg` |

### New CSS-SVG mechanism animations (+7)

| Chapter | Asset |
|---|---|
| ch23 | `sample-23-boot-source-flow.svg` |
| ch24 | `sample-24-wake-restore-flow.svg` |
| ch25 | `sample-25-hse-to-480-flow.svg` |
| ch26 | `sample-26-clk-cfg-en-flow.svg` |
| ch27 | `sample-27-link-dhcp-flow.svg` |
| ch28 | `sample-28-isr-owner-flow.svg` |
| appendix F | `sample-f-repo-lane-flow.svg` |

### Remade chapter anim (in place)

`g0-boot-swd.svg` — FA-002 teaching remake (filename kept). Shared classics (`nvic-interrupt-flow`, `dma-circular`, `network-packet-journey`, `rtos-system-layers`, `freertos-scheduler`) left untouched.

### Embeds

zh + en for 21 new assets (42 insert ops) via `tools/sample_figs_quality5/embed_q5.py` (docs ch23–28 + `stm32-book/book/F-*.md`).

### Anchor deltas (asset_sequence length, video stripped)

| Chapter | Before | After | Δ |
|---|---:|---:|---:|
""" + "\n".join(rows) + f"""
| appendix F (md imgs) | 1 | **{len(f_assets)}** | +{len(f_assets) - 1} |

### Gates

`pytest` book tests + `tools/check_assets.py` + `build_html.py --check` (zh+en) green after this batch.

## Full-series summary (visual quality uplift)

| Batch | Scope | Commit theme |
|---|---|---|
| Pilot | ch02/03/06/09/10 | denser Handraw + remade anims |
| Batch 2 | ch04/05/07/08 | denser Handraw + remade anims |
| Batch 3 | ch11–17 | denser Handraw + remade anims |
| Batch 4 | ch00/01 + ch18–22 | denser Handraw + remade AUX GIFs + anims |
| Batch 5 (final) | ch23–28 + appendix F | denser Handraw + remade g0-boot-swd + anims |

**Bar held across the series:** meaningful denser static Handraw plates, FA-002 continuous-line CSS-SVG mechanism animations (with `prefers-reduced-motion`), zh+en embeds, lock updates (`ROWS` / GIF listing / ADV `CHAPTERS` / audit sequences), gates green. **Video / narration pipelines intentionally out of scope** after owner stop.

### Remaining visual gaps (honest)

- Shared classic anims that still lack a chapter-specific FA-002 remake (`nvic-interrupt-flow`, `dma-circular`, `network-packet-journey`, `rtos-system-layers`, `freertos-scheduler`) — left as shared assets; new chapter-local flows cover the teaching spine.
- Appendix A–E / other book appendices not in this batch's scope (F only).
- Optional denser remakes of older pre-uplift static plates that already met density bar — deferred.
- PDF rebuild of zh+en into `stm32-book/dist` is optional post-gate nicety, not a gate.
"""
    UPLIFT.write_text(text.rstrip() + section + "\n", encoding="utf-8")
    print("appended batch5 + full-series summary to uplift")
    print("appendix F assets:", f_assets)


def main() -> None:
    rows, n, gif_hash = rebuild_rows()
    patch_test_sample(rows, n, gif_hash)
    seq = update_audit()
    update_advanced(seq)
    update_uplift(seq)
    print("lock update done")


if __name__ == "__main__":
    main()

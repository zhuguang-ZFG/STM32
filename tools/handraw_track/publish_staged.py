# -*- coding: utf-8 -*-
"""Rebuild the staged figure family end to end.

The v0 / v1 / v2 / b3 / learning / onramp modules draw their plates into
`assets/illustrations/staged/`, and the PNG that ships to readers lives in
`docs/public/images/`. Those PNGs are committed, so the chain has to be
reproducible from a clean checkout:

    python publish_staged.py            # rebuild SVGs, render, sync
    python publish_staged.py --check    # render and report drift, exit 1 on any

Expected targets are derived from the **generator output** (every staged SVG),
never from what happens to sit in `docs/public/images/`. Listing the existing
files is how a deleted plate once passed as "no drift": it simply stopped being
expected. A staged plate with no published PNG is drift, and a normal run
creates it.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
STAGED = REPO / "assets" / "illustrations" / "staged"
IMAGES = REPO / "docs" / "public" / "images"
HANDRAW = REPO / "assets" / "illustrations" / "handraw"
ARCH = REPO / "docs" / "public" / "arch"

# doc 引用名与生成器文件名不一致的落地点：目录名对齐了，文件名没有。
# docs/v1-drivers/08-architecture-memory-clock.md 引用 /arch/cortex-m-4gb-map.png，
# 生成器写的是 arch-cortex-m-4gb.png，按前缀批量复制必然漏掉它。
ARCH_ALIASES = {"cortex-m-4gb-map": "cortex-m-4gb"}

MODULES = [
    "fig_v0", "fig_v1a", "fig_v1b", "fig_v1c",
    "fig_v2a", "fig_v2b", "fig_v2c", "fig_v2d", "fig_v2e",
    "fig_v4a", "fig_v7a", "fig_onramp", "fig_merged_b3", "fig_learning",
    "fig_reading",
]


def regenerate() -> None:
    for mod in MODULES:
        subprocess.run([sys.executable, str(HERE / f"{mod}.py")], check=True,
                       stdout=subprocess.DEVNULL)


def expected_plates(root: Path = STAGED) -> dict[str, Path]:
    """Every plate the generators produce: stem -> SVG. This is the contract."""
    return {p.stem: p for p in sorted(root.rglob("*.svg"))}


def render_bytes(svg: Path) -> bytes:
    """Render one SVG to PNG bytes without leaving anything in the repo."""
    import render as R  # same directory as this script

    with tempfile.TemporaryDirectory() as td:
        copy = Path(td) / svg.name
        shutil.copy2(svg, copy)
        R.render_all([str(copy)])
        return copy.with_suffix(".png").read_bytes()


def diff(expected: dict[str, Path], images: Path = IMAGES,
         render=render_bytes) -> tuple[list[str], list[str], list[str]]:
    """Return (missing, stale, orphan) against the published directory."""
    missing, stale = [], []
    for stem, svg in expected.items():
        target = images / f"{stem}.png"
        if not target.exists():
            missing.append(stem)
            continue
        if render(svg) != target.read_bytes():
            stale.append(stem)
    published = {p.stem for p in images.glob("*.png")}
    orphan = sorted(published - set(expected))
    return sorted(missing), sorted(stale), orphan


def publish(expected: dict[str, Path], images: Path = IMAGES,
            render=render_bytes) -> tuple[list[str], list[str]]:
    """Write every expected plate, creating targets that went missing."""
    created, updated = [], []
    for stem, svg in expected.items():
        target = images / f"{stem}.png"
        data = render(svg)
        if not target.exists():
            target.write_bytes(data)
            created.append(stem)
        elif data != target.read_bytes():
            target.write_bytes(data)
            updated.append(stem)
    return sorted(created), sorted(updated)


def _rel(p: Path) -> str:
    """Path for humans: repo-relative when possible, absolute otherwise.

    `relative_to` raises for anything outside the repo, which is exactly what a
    temp-tree test hands us.
    """
    try:
        return str(p.relative_to(REPO))
    except ValueError:
        return str(p)


def mirrored_plates() -> dict[Path, Path]:
    """Published PNGs copied verbatim from the handraw tree: target -> source.

    These carry no staged SVG, so `diff()` used to skip them entirely and they
    drifted silently: 163 of them sat a commit behind, and the one doc-facing
    alias under docs/public/arch/ drifted the same way. Copy is byte-for-byte
    (verified against history: a matching source blob exists at the last sync).
    """
    out: dict[Path, Path] = {}
    # A staged plate owns its published PNG: publish() renders it from the SVG,
    # so a same-stem handraw file must never claim it (staged PNGs in that tree
    # are stale artefacts; one was once copied over a fresh publish that way).
    staged = {p.stem for p in STAGED.rglob("*.svg")}
    for p in IMAGES.glob("*.png"):
        if p.stem in staged:
            continue
        src = HANDRAW / f"{p.stem}.png"
        if src.exists():
            out[p] = src
    for p in ARCH.glob("*.png"):
        src = HANDRAW / f"arch-{p.stem}.png"
        if not src.exists() and p.stem in ARCH_ALIASES:
            src = HANDRAW / f"arch-{ARCH_ALIASES[p.stem]}.png"
        if src.exists():
            out[p] = src
    return out


def mirror_drift() -> list[Path]:
    """Published copies that no longer match their handraw source."""
    return sorted(t for t, s in mirrored_plates().items()
                  if t.read_bytes() != s.read_bytes())


def sync_mirrors() -> list[Path]:
    """Rewrite drifted handraw-sourced copies; return what was rewritten."""
    updated = []
    for target, src in sorted(mirrored_plates().items()):
        data = src.read_bytes()
        if target.read_bytes() != data:
            target.write_bytes(data)
            updated.append(target)
    return updated


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="report drift instead of writing")
    args = ap.parse_args()

    regenerate()
    expected = expected_plates()
    if not expected:
        print(f"no staged plates under {STAGED}", file=sys.stderr)
        return 2

    if args.check:
        missing, stale, orphan = diff(expected)
        mirrors = mirror_drift()
        print(f"checked {len(expected)} plate(s); "
              f"missing {len(missing)}, stale {len(stale)}; "
              f"handraw mirrors stale {len(mirrors)}")
        if missing:
            print("missing:", missing[:10])
        if stale:
            print("stale:", stale[:10])
        if mirrors:
            print("mirror stale:", [_rel(p) for p in mirrors[:10]])
        covered = {t.stem for t in mirrored_plates()}
        orphan = [o for o in orphan if o not in covered]
        if orphan:
            print(f"note: {len(orphan)} published PNG(s) have no source SVG: "
                  f"{orphan[:5]}")
        return 1 if missing or stale or mirrors else 0

    created, updated = publish(expected)
    print(f"rebuilt {len(expected)} plate(s); created {len(created)}, "
          f"updated {len(updated)}")
    if created:
        print("created:", created[:10])
    if updated:
        print("updated:", updated[:10])
    synced = sync_mirrors()
    print(f"synced {len(synced)} handraw mirror(s)")
    if synced:
        print("synced:", [_rel(p) for p in synced[:10]])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

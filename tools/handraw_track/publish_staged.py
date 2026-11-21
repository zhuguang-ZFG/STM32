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
        print(f"checked {len(expected)} plate(s); "
              f"missing {len(missing)}, stale {len(stale)}")
        if missing:
            print("missing:", missing[:10])
        if stale:
            print("stale:", stale[:10])
        if orphan:
            print(f"note: {len(orphan)} published PNG(s) have no staged SVG: "
                  f"{orphan[:5]}")
        return 1 if missing or stale else 0

    created, updated = publish(expected)
    print(f"rebuilt {len(expected)} plate(s); created {len(created)}, "
          f"updated {len(updated)}")
    if created:
        print("created:", created[:10])
    if updated:
        print("updated:", updated[:10])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

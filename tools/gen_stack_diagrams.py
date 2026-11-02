#!/usr/bin/env python3
"""Rebuild stack-diagram HTML and, with --render, its light/dark PNGs.

Requires the reviewed caru-ini/stack-diagram skill. Set STACK_DIAGRAM_SKILL when
it is not installed at .claude/skills/stack-diagram. PNG rendering additionally
requires Playwright and Chromium. Icons and fonts are embedded in the HTML.
"""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
SKILL = Path(os.environ.get(
    "STACK_DIAGRAM_SKILL", str(ROOT / ".claude" / "skills" / "stack-diagram")
))
DRAFT = ROOT / "tools" / "stack-diagrams" / "gpio-pc13-led.html"
ICONS = ROOT / "tools" / "stack-diagrams" / "icons"
OUT = ROOT / "assets" / "diagrams" / "stack-gpio-pc13-led"


def main(argv: list[str]) -> int:
    for path in (SKILL / "scripts" / "build.py", DRAFT, ICONS):
        if not path.exists():
            raise SystemExit(f"missing stack-diagram input: {path}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    subprocess.check_call([
        sys.executable,
        str(SKILL / "scripts" / "build.py"),
        str(DRAFT),
        str(ICONS),
        str(OUT.with_suffix(".html")),
        "--fonts",
        str(SKILL / "assets" / "fonts"),
    ])
    if "--render" in argv:
        subprocess.check_call([
            sys.executable,
            str(SKILL / "scripts" / "render_png.py"),
            str(OUT.with_suffix(".html")),
            str(OUT.with_suffix(".png")),
            "--selector",
            ".canvas",
            "--scale",
            "2",
        ])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

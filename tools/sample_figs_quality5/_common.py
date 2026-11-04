#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shared helpers for visual-quality uplift batch 5 (ch23–28 + appendix F)."""
from __future__ import annotations

import hashlib
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from svgkit import Svg, T

T_COLORS = {
    value
    for name in dir(T)
    if name.isupper() and isinstance(value := getattr(T, name), str) and value.startswith("#")
}
TEXT_RE = re.compile(r"<text\b[^>]*>(.*?)</text>", flags=re.DOTALL)


def credit(canvas: Svg, note: str) -> None:
    canvas.line(24, canvas.h - 36, canvas.w - 24, canvas.h - 36, stroke=T.GRID, sw=1)
    canvas.text(24, canvas.h - 16, note, size=11, fill=T.MUTED)
    canvas.text(canvas.w - 24, canvas.h - 16, "自绘 · 静态 · CC BY 4.0", size=11, fill=T.DIM, anchor="end")


def audit_static(name: str, path: str, *, width: int = 960, height: int = 880) -> str:
    raw = open(path, "rb").read()
    text = raw.decode("utf-8")
    w, h = (int(part) for part in re.search(r'\bwidth="(\d+)" height="(\d+)"', text).groups())
    strokes = set(re.findall(r'stroke-width="([^"]+)"', text))
    radii = set(re.findall(r'\brx="([^"]+)"', text))
    colors = {item.lower() for item in re.findall(r"#(?:[0-9A-Fa-f]{6})(?![0-9A-Fa-f])", text)}
    digest = hashlib.sha256("\n".join(TEXT_RE.findall(text)).encode("utf-8")).hexdigest()
    assert w == width, (name, "width", w)
    assert h == height, (name, "height", h)
    assert strokes <= {"1", "1.5", "2"}, (name, "stroke-width", sorted(strokes))
    assert radii <= {"2", "4", "8"}, (name, "rx", sorted(radii))
    assert colors <= T_COLORS, (name, "colors", sorted(colors - T_COLORS))
    assert "自绘" in text, (name, "credit")
    for banned in ("<animate", "@keyframes", "animation:", "矢量动画"):
        assert banned not in text, (name, "animation", banned)
    assert len(raw) < 80 * 1024, (name, "bytes", len(raw))
    print(f"{name}  {w}x{h}  {len(raw)} bytes  text_hash={digest}")
    return digest


def audit_anim(name: str, path: str, *, width: int = 900, height: int = 620) -> str:
    raw = open(path, "rb").read()
    text = raw.decode("utf-8")
    w, h = (int(part) for part in re.search(r'\bwidth="(\d+)" height="(\d+)"', text).groups())
    digest = hashlib.sha256("\n".join(TEXT_RE.findall(text)).encode("utf-8")).hexdigest()
    assert w == width and h == height, (name, w, h)
    assert "@keyframes" in text or "animation:" in text, (name, "needs motion")
    assert "prefers-reduced-motion" in text, (name, "reduced-motion")
    assert "FA-002" in text, (name, "FA-002")
    assert "自绘" in text, (name, "credit")
    assert len(raw) < 90 * 1024, (name, "bytes", len(raw))
    print(f"{name}  {w}x{h}  {len(raw)} bytes  text_hash={digest}")
    return digest

# -*- coding: utf-8 -*-
"""Render handraw SVG files to 1152x864 PNG with headless Chromium.

Usage: python render.py a.svg b.svg ...
Each SVG is screenshotted to the same name with .png suffix.

Deterministic: same SVG bytes -> same PNG pixels. The plates are flat ink and
flat tints (no gradients, no photos), so an adaptive 256-colour rewrite is
lossless to the eye (PSNR 42-45 dB) and cuts the committed PNG weight by ~60%.
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

W, H = 1152, 864


def _encode(shot: bytes) -> bytes:
    im = Image.open(io.BytesIO(shot)).convert("RGB")
    if im.size != (W, H):
        raise RuntimeError(f"unexpected plate size {im.size}")
    q = im.quantize(colors=256, method=Image.MEDIANCUT, dither=Image.NONE)
    buf = io.BytesIO()
    q.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def render_all(paths):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(
            viewport={"width": 1180, "height": 900},
            device_scale_factor=1,
        )
        for src in paths:
            src = Path(src).resolve()
            dst = src.with_suffix(".png")
            page.goto(src.as_uri())
            page.wait_for_load_state("load")
            page.wait_for_timeout(150)  # font settle
            el = page.query_selector("svg")
            if el is None:
                raise RuntimeError(f"no <svg> in {src}")
            dst.write_bytes(_encode(el.screenshot()))
            print(f"OK {dst.name}  {dst.stat().st_size} bytes")
        browser.close()


if __name__ == "__main__":
    render_all(sys.argv[1:])

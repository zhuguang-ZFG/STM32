# -*- coding: utf-8 -*-
"""Render handraw SVG files to 1152x864 PNG with headless Chromium.

Usage: python render.py a.svg b.svg ...
Each SVG is screenshotted to the same name with .png suffix.
Deterministic: same SVG bytes -> same PNG pixels.
"""
from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright


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
            el.screenshot(path=str(dst))
            print(f"OK {dst.name}  {dst.stat().st_size} bytes")
        browser.close()


if __name__ == "__main__":
    render_all(sys.argv[1:])

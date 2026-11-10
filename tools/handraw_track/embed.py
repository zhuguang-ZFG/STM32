# -*- coding: utf-8 -*-
"""Insert handraw knowledge-track PNG blocks after anchor figure paragraphs.

Follows the exact embed grammar already used for ch00-ch12:
zh: <p align="center"> + img + <sub>▲ 知识轨（Handraw · 原理示意/非实拍）。…</sub>
en: same with English caption text.
Insertion happens right after the anchor paragraph's closing </p>.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def embed(doc: str, anchor_img: str, png: str, alt: str, caption: str,
          img_width: str = "760") -> bool:
    path = ROOT / doc
    text = path.read_text(encoding="utf-8")
    if f"illustrations/handraw/{png}" in text:
        print(f"SKIP {doc}: {png} already embedded")
        return True
    # find the <p ...> ... anchor img ... </p> block
    pat = re.compile(
        r'(<p align="center">\s*\n\s*<img src="[^"]*?' + re.escape(anchor_img) +
        r'".*?</p>)', re.DOTALL)
    m = pat.search(text)
    if not m:
        print(f"MISS {doc}: anchor {anchor_img} not found")
        return False
    block = (f'\n\n<p align="center">\n'
             f'  <img src="../assets/illustrations/handraw/{png}" '
             f'width="{img_width}" alt="{alt}">\n'
             f'  <br><sub>{caption}</sub>\n'
             f'</p>')
    # en docs use ../../assets
    if doc.startswith("docs/en"):
        block = block.replace('"../assets/', '"../../assets/')
    new = text[:m.end()] + block + text[m.end():]
    path.write_text(new, encoding="utf-8", newline="\n")
    print(f"OK   {doc}: {png} after {anchor_img}")
    return True


def embed_after_text(doc: str, anchor: str, png: str, alt: str, caption: str,
                     img_width: str = "760") -> bool:
    """Insert a handraw block after the paragraph (or heading) containing
    `anchor`. The anchor must appear exactly once in the document."""
    path = ROOT / doc
    text = path.read_text(encoding="utf-8")
    if f"illustrations/handraw/{png}" in text:
        print(f"SKIP {doc}: {png} already embedded")
        return True
    idx = text.find(anchor)
    if idx < 0:
        print(f"MISS {doc}: text anchor not found: {anchor[:60]}…")
        return False
    if text.find(anchor, idx + len(anchor)) >= 0:
        print(f"AMBIGUOUS {doc}: text anchor appears twice: {anchor[:60]}…")
        return False
    eol = text.find("\n", idx)
    if eol < 0:
        eol = len(text)
    block = (f'\n\n<p align="center">\n'
             f'  <img src="../assets/illustrations/handraw/{png}" '
             f'width="{img_width}" alt="{alt}">\n'
             f'  <br><sub>{caption}</sub>\n'
             f'</p>')
    if doc.startswith("docs/en"):
        block = block.replace('"../assets/', '"../../assets/')
    new = text[:eol + 1] + block + text[eol + 1:]
    path.write_text(new, encoding="utf-8", newline="\n")
    print(f"OK   {doc}: {png} after text anchor")
    return True


def run(specs):
    bad = 0
    for spec in specs:
        if not embed(*spec):
            bad += 1
    if bad:
        sys.exit(f"{bad} embed(s) failed")

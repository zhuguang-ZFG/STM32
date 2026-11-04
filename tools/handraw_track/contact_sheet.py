# -*- coding: utf-8 -*-
"""Contact sheets for the handraw knowledge track: 2x2 tiles per PNG sheet.

Usage: python contact_sheet.py <glob...> --out <dir> [--prefix sheets]
Each output sheet holds 4 figures at 1152x864 native (sheet 2304x1728) with the
file name printed under each tile, so defects can be located precisely.
"""
from __future__ import annotations

import argparse
import glob as globmod
import os
import sys

from PIL import Image, ImageDraw

TW, TH = 1152, 864
COLS, ROWS = 2, 2
LABEL_H = 46


def sheets_for(paths, out_dir, prefix):
    os.makedirs(out_dir, exist_ok=True)
    made = []
    for i in range(0, len(paths), COLS * ROWS):
        chunk = paths[i:i + COLS * ROWS]
        sheet = Image.new("RGB", (TW * COLS, (TH + LABEL_H) * ROWS), "#333333")
        d = ImageDraw.Draw(sheet)
        for k, p in enumerate(chunk):
            im = Image.open(p).convert("RGB")
            if im.size != (TW, TH):
                im = im.resize((TW, TH))
            cx = (k % COLS) * TW
            cy = (k // COLS) * (TH + LABEL_H)
            sheet.paste(im, (cx, cy))
            d.text((cx + 14, cy + TH + 10), os.path.basename(p),
                   fill="#ffffff")
        out = os.path.join(out_dir, f"{prefix}-{i // (COLS * ROWS) + 1:02d}.png")
        sheet.save(out)
        made.append(out)
    return made


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("globs", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--prefix", default="sheet")
    a = ap.parse_args()
    paths = []
    for g in a.globs:
        paths.extend(sorted(globmod.glob(g)))
    for s in sheets_for(paths, a.out, a.prefix):
        print(s)


if __name__ == "__main__":
    main()

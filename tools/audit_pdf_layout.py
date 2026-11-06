#!/usr/bin/env python3
"""Whole-book print layout audit for the built PDFs.

Reads the PDFs in ``stm32-book/dist`` and reports page-level typography
defects that single-asset checks cannot see:

- text or table content overflowing the right page margin;
- a heading stranded as the last content block of a page;
- a figure caption starting a page with no figure on it;
- a large empty band at the bottom of a page that is followed by more
  content of the same section (a pushed unbreakable block);
- a near-blank page that carries neither figure nor text.

The bottom-gap check skips pages whose successor starts a new TOC
section: those breaks are intentional (chapters, parts, appendices).
Intentional short pages (cover, part dividers, chapter tails) are
therefore never reported.

Usage: ``python tools/audit_pdf_layout.py [--json PATH]``
Exit code is 0 unless ``--max-*`` thresholds are exceeded.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import pymupdf

REPO = Path(__file__).resolve().parents[1]
MM = 72 / 25.4
PAGE_W, PAGE_H = 210 * MM, 297 * MM
LEFT, RIGHT = 15 * MM, PAGE_W - 15 * MM
BOTTOM = PAGE_H - 18 * MM
STAMP_TOP = PAGE_H - 22 * MM  # footer rule/label live below this line

PDFS = (
    (REPO / "stm32-book/dist/stm32-practical-book.pdf", "zh"),
    (REPO / "stm32-book/dist/stm32-practical-book-en.pdf", "en"),
)


def _content_rects(page: pymupdf.Page) -> list[pymupdf.Rect]:
    rects = [
        pymupdf.Rect(b["bbox"])
        for b in page.get_text("dict")["blocks"]
        if b.get("lines") and b["bbox"][3] < STAMP_TOP - 2
    ]
    rects += [
        pymupdf.Rect(im["bbox"])
        for im in page.get_image_info()
        if im["bbox"][3] < STAMP_TOP - 2
    ]
    rects += [
        d["rect"]
        for d in page.get_drawings()
        if d["rect"].y1 < STAMP_TOP - 2 and d["rect"].height > 3
    ]
    return rects


def _figure_coverage(page: pymupdf.Page, used: float) -> float:
    boxes = [
        (r.y0, r.y1)
        for r in _content_rects(page)
        if (r.y1 - r.y0) > 20 and (r.x1 - r.x0) > 100
    ]
    boxes.sort()
    merged: list[list[float]] = []
    for y0, y1 in boxes:
        if merged and y0 <= merged[-1][1] + 5:
            merged[-1][1] = max(merged[-1][1], y1)
        else:
            merged.append([y0, y1])
    height = sum(y1 - y0 for y0, y1 in merged)
    return height / max(used, 1.0)


def scan(path: Path) -> dict:
    doc = pymupdf.open(path)
    starts = {page for _lvl, _title, page in doc.get_toc()}
    issues: dict[str, list] = {
        "margin_overflow": [],
        "orphan_heading": [],
        "caption_orphan": [],
        "bottom_gap": [],
        "near_blank": [],
    }
    for index in range(doc.page_count):
        page = doc[index]
        pno = index + 1
        blocks = [
            b
            for b in page.get_text("dict")["blocks"]
            if b.get("lines") and b["bbox"][3] < STAMP_TOP - 2
        ]
        for b in blocks:
            if b["bbox"][2] > RIGHT + 3 and b["bbox"][1] < STAMP_TOP - 2:
                text = " ".join(
                    s["text"] for line in b["lines"] for s in line["spans"]
                )[:60]
                issues["margin_overflow"].append({"page": pno, "text": text})
        if blocks:
            last = max(blocks, key=lambda b: b["bbox"][3])
            spans = [s for line in last["lines"] for s in line["spans"]]
            size = max(s["size"] for s in spans)
            bold = any(s["flags"] & 16 or "Bold" in s["font"] for s in spans)
            text = " ".join(s["text"] for s in spans).strip()
            if size >= 11 and bold and len(text) < 80 and last["bbox"][3] > BOTTOM - 8:
                issues["orphan_heading"].append({"page": pno, "text": text[:60]})
            first = min(blocks, key=lambda b: b["bbox"][1])
            ftext = " ".join(
                s["text"] for line in first["lines"] for s in line["spans"]
            ).strip()
            if ftext.startswith("▲") and not page.get_images():
                issues["caption_orphan"].append({"page": pno, "text": ftext[:70]})
        chars = len(page.get_text().strip())
        if chars < 40 and pno > 1 and not page.get_images():
            issues["near_blank"].append({"page": pno, "chars": chars})
        rects = _content_rects(page)
        if rects and pno < doc.page_count and pno + 1 not in starts:
            ybot = max(r.y1 for r in rects)
            gap = BOTTOM - ybot
            if gap > 150:
                used = ybot - min(r.y0 for r in rects)
                issues["bottom_gap"].append(
                    {
                        "page": pno,
                        "gap_pt": round(gap, 1),
                        "figure_ratio": round(_figure_coverage(page, used), 2),
                    }
                )
    summary = {k: len(v) for k, v in issues.items()}
    biggest = Counter()
    for item in issues["bottom_gap"]:
        band = 200 if item["gap_pt"] < 250 else (350 if item["gap_pt"] < 400 else 999)
        biggest[band] += 1
    return {
        "file": path.name,
        "pages": doc.page_count,
        "summary": summary,
        "gap_bands": {"150-249pt": biggest[200], "250-349pt": biggest[350], ">=350pt": biggest[999]},
        "issues": issues,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path, help="write the full report here")
    parser.add_argument("--max-gap-pages", type=int, default=None,
                        help="fail if more pages than this have a bottom gap over 150pt")
    args = parser.parse_args(argv)

    reports = []
    failed = False
    for path, lang in PDFS:
        if not path.exists():
            print(f"{lang}: missing {path}")
            failed = True
            continue
        report = scan(path)
        reports.append(report)
        gaps = report["summary"]["bottom_gap"]
        print(
            f"{lang}: {report['pages']}p  gaps>150pt={gaps} "
            f"{report['gap_bands']}  overflow={report['summary']['margin_overflow']} "
            f"orphan_h={report['summary']['orphan_heading']} "
            f"caption_orphan={report['summary']['caption_orphan']} "
            f"near_blank={report['summary']['near_blank']}"
        )
        if args.max_gap_pages is not None and gaps > args.max_gap_pages:
            failed = True
    if args.json:
        args.json.write_text(
            json.dumps(reports, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"report: {args.json}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

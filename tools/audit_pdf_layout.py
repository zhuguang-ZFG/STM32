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
from typing import Any, cast

import pymupdf

REPO = Path(__file__).resolve().parents[1]
MM = 72 / 25.4
PAGE_W, PAGE_H = 210 * MM, 297 * MM
LEFT, RIGHT = 17 * MM, PAGE_W - 17 * MM   # print_css @page 17mm 左右边距
BOTTOM = PAGE_H - 19 * MM                 # 版心底：下边距 19mm
STAMP_TOP = PAGE_H - 17 * MM  # printed margin; footer rule/label live below this line

PDFS = (
    (REPO / "book/dist/print/merged-book.pdf", "zh"),
)

# 收尾类标点（W3C clreq）：悬挂在行尾右缘属于正常中文排版，不算溢出。
CLOSING_PUNCT = "。，、；：！？）】》」』”’…～"


def _is_white(d: dict) -> bool:
    fill = d.get("fill")
    return fill is None or all(c >= 0.98 for c in fill)

def _text_dict(page: pymupdf.Page) -> dict[str, Any]:
    """`get_text("dict")` 的结构化结果。

    PyMuPDF 的 `Page.get_text` 运行时是 `(*args, **kwargs)`，`utils.get_text`
    又没有返回注解，静态检查只能把返回值推断成 `str | list | dict` 的联合。
    这里按实际返回类型收窄，免得下游每次取 `["blocks"]` 都被判为类型错误。
    """
    return cast(dict[str, Any], page.get_text("dict"))

def _plain_text(page: pymupdf.Page) -> str:
    """`get_text()` 的纯文本结果，理由同 `_text_dict`。"""
    return cast(str, page.get_text())


def _content_rects(page: pymupdf.Page) -> list[pymupdf.Rect]:
    rects = [
        pymupdf.Rect(b["bbox"])
        for b in _text_dict(page)["blocks"]
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
        # skip the page/column background fills Chromium paints (body/.book
        # 白底竖栏 176mm 宽会盖住真实内容高度), and anything in the stamped
        # footer zone
        if d["rect"].y1 < STAMP_TOP - 2
        and d["rect"].height > 3
        and not (d["rect"].width > 400 and d["rect"].height > 500
                 and _is_white(d))
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
            for b in _text_dict(page)["blocks"]
            if b.get("lines") and b["bbox"][3] < STAMP_TOP - 2
        ]
        for b in blocks:
            if b["bbox"][2] > RIGHT + 3 and b["bbox"][1] < STAMP_TOP - 2:
                text = " ".join(
                    s["text"] for line in b["lines"] for s in line["spans"]
                )
                # text-justify: inter-ideograph 会把行尾收尾标点悬挂出右缘
                # （~5pt 半个标点宽，clreq 允许），这不是溢出。
                tail = text.rstrip()[-1:]
                if tail in CLOSING_PUNCT:
                    continue
                issues["margin_overflow"].append({"page": pno, "text": text[:60]})
        if blocks:
            last = max(blocks, key=lambda b: b["bbox"][3])
            spans = [s for line in last["lines"] for s in line["spans"]]
            size = max(s["size"] for s in spans)
            bold = any(s["flags"] & 16 or "Bold" in s["font"] for s in spans)
            text = " ".join(s["text"] for s in spans).strip()
            if size >= 11 and bold and len(text) < 80 and last["bbox"][3] > BOTTOM - 8:
                issues["orphan_heading"].append({"page": pno, "text": text[:60]})
            first = min(blocks, key=lambda b: b["bbox"][1])
            fspans = [s for line in first["lines"] for s in line["spans"]]
            ftext = " ".join(s["text"] for s in fspans).strip()
            # 合并书 figcaption = 0.8em ≈ 8.2pt，比正文所有起点元素都小
            # （罗盘卡标签 8pt 前面必有 h2，表格 8.8pt、代码 8.6pt 均高于阈值）。
            # 页眉字也是小字但贴着纸上缘（<50pt），版心从 21mm ≈ 59.5pt 起。
            cap_size = max((s["size"] for s in fspans), default=0)
            if ftext and cap_size < 8.5 and 55 < first["bbox"][1] < 130 \
                    and not page.get_images():
                issues["caption_orphan"].append({"page": pno, "text": ftext[:70]})
        chars = len(_plain_text(page).strip())
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
    chapters = _chapter_anchor_stats(doc)
    return {
        "file": path.name,
        "pages": doc.page_count,
        "summary": summary,
        "gap_bands": {"150-249pt": biggest[200], "250-399pt": biggest[350], ">=400pt": biggest[999]},
        "chapters": chapters,
        "issues": issues,
    }


def _has_visual_anchor(page: pymupdf.Page) -> bool:
    """A page carries a visual anchor if it holds a figure-sized raster or
    a vector plate cluster (the inline SVG plates print as drawings)."""
    for im in page.get_image_info():
        if im["bbox"][3] < STAMP_TOP - 2 and (im["bbox"][3] - im["bbox"][1]) > 60:
            return True
    for d in page.get_drawings():
        r = d["rect"]
        if (
            r.y1 < STAMP_TOP - 2
            and r.width > 250
            and r.height > 100
            and not (r.width > 500 and r.height > 700)  # page background fill
        ):
            return True
    return False


def _chapter_anchor_stats(doc: pymupdf.Document) -> list[dict]:
    """Per TOC level-2 section: visual anchors and the longest run of pages
    without one (BOOK_REDESIGN_SPEC 11: 每章锚点与最大无图区间)."""
    sections = [(page, title) for lvl, title, page in doc.get_toc() if lvl == 2]
    if not sections:
        sections = [(page, title) for lvl, title, page in doc.get_toc()]
    anchors = [
        _has_visual_anchor(doc[i]) and i + 1 or 0 for i in range(doc.page_count)
    ]
    stats = []
    for idx, (start, title) in enumerate(sections):
        end = sections[idx + 1][0] - 1 if idx + 1 < len(sections) else doc.page_count
        if end < start:
            continue
        span = range(start, end + 1)
        count = sum(1 for p in span if anchors[p - 1])
        worst = run = 0
        for p in span:
            run = 0 if anchors[p - 1] else run + 1
            worst = max(worst, run)
        stats.append(
            {
                "title": title[:40],
                "pages": end - start + 1,
                "anchors": count,
                "max_fig_free_pages": worst,
            }
        )
    return stats


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path, help="write the full report here")
    parser.add_argument("--lang", choices=("zh", "en"), help="audit only one language")
    parser.add_argument("--max-gap-pages", type=int, default=None,
                        help="fail if more pages than this have a bottom gap over 150pt")
    parser.add_argument("--max-large-gap-pages", type=int, default=None,
                        help="fail if more pages than this have a bottom gap of 250pt or more")
    parser.add_argument("--min-anchors", type=int, default=None,
                        help="fail if any TOC section carries fewer visual anchors")
    parser.add_argument("--max-fig-free-pages", type=int, default=None,
                        help="fail if any TOC section has a longer figure-free page run")
    args = parser.parse_args(argv)

    reports = []
    failed = False
    for path, lang in PDFS:
        if args.lang and lang != args.lang:
            continue
        if not path.exists():
            print(f"{lang}: missing {path}")
            failed = True
            continue
        report = scan(path)
        reports.append(report)
        gaps = report["summary"]["bottom_gap"]
        hard = sum(
            report["summary"][k]
            for k in ("margin_overflow", "orphan_heading", "caption_orphan", "near_blank")
        )
        stats = report["chapters"]
        thin = [c for c in stats if args.min_anchors is not None and c["anchors"] < args.min_anchors]
        longfree = [
            c for c in stats
            if args.max_fig_free_pages is not None and c["max_fig_free_pages"] > args.max_fig_free_pages
        ]
        print(
            f"{lang}: {report['pages']}p  gaps>150pt={gaps} "
            f"{report['gap_bands']}  overflow={report['summary']['margin_overflow']} "
            f"orphan_h={report['summary']['orphan_heading']} "
            f"caption_orphan={report['summary']['caption_orphan']} "
            f"near_blank={report['summary']['near_blank']}  "
            f"anchors[min={min((c['anchors'] for c in stats), default=0)} "
            f"max_free={max((c['max_fig_free_pages'] for c in stats), default=0)}]"
        )
        if args.max_gap_pages is not None and gaps > args.max_gap_pages:
            failed = True
        large = report["gap_bands"]["250-399pt"] + report["gap_bands"][">=400pt"]
        if args.max_large_gap_pages is not None and large > args.max_large_gap_pages:
            failed = True
            print(f"  {lang} large bottom gaps: {large} pages >= 250pt")
        if hard:
            failed = True
        if thin:
            failed = True
            for c in thin:
                print(f"  {lang} thin anchors: {c['title']} ({c['anchors']})")
        if longfree:
            failed = True
            for c in longfree:
                print(f"  {lang} long figure-free run: {c['title']} ({c['max_fig_free_pages']}p)")
    if args.json:
        args.json.write_text(
            json.dumps(reports, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"report: {args.json}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

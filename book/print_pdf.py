#!/usr/bin/env python3
"""PDF 后处理管线：Chromium 打印 → PyMuPDF 精加工。

架构对齐 yuyu_book/pdf.py（参考项目已验证的路线）：
- Chromium `page.pdf` 打印单文件书稿（A4、零边距——CSS @page 已声明版心）；
  文内链接在 PDF 里自动成为命名目的地；
- PyMuPDF 后处理读取目的地：落书签树（卷=1 级、章=2 级、附录=1 级）、盖页眉
  （单数页书名/双数页章名）与居中页码 `n / total`、目录行页码盖进保留槽位；
- 空页检测：只有页眉页码没有正文的纸直接报错（一节必须收在结束的那页上）；
- 中文字形：Helvetica 数字 + 本机 CJK 字体子集化（找不到 CJK 直接报错，
  页眉页码不能静默丢汉字）。

用法：
  python book/print_pdf.py --html book/dist/print/merged-book.html \
      --meta book/dist/print/merged-book.meta.json --out book/dist/print/merged-book.pdf
  可选 --browser "C:/…/chrome.exe" 指定浏览器可执行文件。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import fitz  # PyMuPDF

CJK_FONTS = ["C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simsun.ttc",
             "C:/Windows/Fonts/simhei.ttf",
             "/System/Library/Fonts/PingFang.ttc",
             "/System/Library/Fonts/Supplemental/Songti.ttc",
             "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
             "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"]
MARGIN = 48.0
INK = (0.42, 0.36, 0.26)
RULE = (0.82, 0.76, 0.62)


def sheet_count(pdf_path: Path) -> int:
    doc = fitz.open(str(pdf_path))
    try:
        return doc.page_count
    finally:
        doc.close()


def empty_sheets(doc) -> list[int]:
    """1-based 页号：除页眉/页码家具外没有任何正文的纸。

    判定（对 yuyu 原版放宽——本书的整页表格会穿过页眉带，按「带内相交」算
    有正文）：页 55pt 至页底-35pt 的带内存在任何文本块、矢量绘制面积 ≥1% 页面
    或位图，即视为有正文。家具（页眉行/页码行及其细线）都在带外。
    """
    holes = []
    for i, page in enumerate(doc):
        h = page.rect.height
        band = fitz.Rect(0, 55, page.rect.width, h - 35)
        has_body = False
        for b in page.get_text("blocks"):
            r = fitz.Rect(b[:4])
            if b[4].strip() and r.y1 > 55 and r.y0 < h - 35:
                has_body = True
                break
        if not has_body:
            area = sum(fitz.Rect(d["rect"]).get_area()
                       for d in page.get_drawings()
                       if fitz.Rect(d["rect"]).intersects(band))
            if area >= 0.01 * page.rect.get_area():
                has_body = True
        if not has_body:
            for im in page.get_images(full=True):
                try:
                    if page.get_image_bbox(im).intersects(band):
                        has_body = True
                        break
                except Exception:
                    continue
        if not has_body:
            holes.append(i + 1)
    return holes


def _launch(p, browser: str | None):
    if browser:
        try:
            return p.chromium.launch(executable_path=browser)
        except Exception:
            pass
    for kind in ("msedge", "chrome", None):
        try:
            return (p.chromium.launch(channel=kind) if kind
                    else pw_launch_plain(p))
        except Exception:
            continue
    raise RuntimeError("pdf: no Chromium/Edge available")


def pw_launch_plain(p):
    return p.chromium.launch()


def _print_pdf(html_path: Path, raw: Path, browser: str | None) -> None:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        launched = _launch(p, browser)
        page = launched.new_page(viewport={"width": 1280, "height": 900})
        page.goto(html_path.resolve().as_uri(), wait_until="load")
        try:
            page.evaluate("() => document.fonts.ready.then(() => true)")
        except Exception:
            pass
        page.emulate_media(media="print")
        page.pdf(path=str(raw), format="A4", print_background=True,
                 prefer_css_page_size=True,
                 margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
        launched.close()


def _destinations(doc, anchors: list[str]) -> dict[str, int]:
    want = set(anchors)
    found: dict[str, int] = {}
    for pno in range(doc.page_count):
        if want <= set(found):
            break
        for link in doc[pno].get_links():
            name, page = link.get("nameddest"), link.get("page")
            if name in want and isinstance(page, int) and 0 <= page < doc.page_count:
                found.setdefault(name, page)
    return found


def _fit(text: str, width: float, size: float, width_of):
    if width_of(text) <= width:
        return text
    trimmed = text
    while trimmed and width_of(trimmed + "…") > width:
        trimmed = trimmed[:-1]
    return (trimmed + "…") if trimmed else ""


class _Head:
    """页眉/页码墨水：数字用 Helvetica，中文用本机字体（宽度按真实字面）。"""

    def __init__(self, fontfile: str | None):
        self.fontfile = fontfile
        self.face = None
        if fontfile:
            try:
                self.face = fitz.Font(fontfile=fontfile)
            except Exception:
                self.fontfile = None

    def width(self, text: str, size: float) -> float:
        if self.face:
            return self.face.text_length(text, fontsize=size)
        return fitz.get_text_length(text, fontname="helv", fontsize=size)

    def draw(self, page, x: float, y: float, text: str, size: float,
             color: tuple) -> None:
        if self.face:
            page.insert_text((x, y), text, fontsize=size, fontname="b5-head",
                             fontfile=self.fontfile, color=color)
        else:
            page.insert_text((x, y), text.encode("latin-1", "ignore").decode(),
                             fontsize=size, fontname="helv", color=color)


def _folio(head: _Head, page, n: int, total: int) -> None:
    text, size = f"{n} / {total}", 8.2
    rect = page.rect
    w = head.width(text, size)
    cx, y = rect.width / 2, rect.height - 26
    head.draw(page, cx - w / 2, y, text, size, INK)
    shape = page.new_shape()
    shape.draw_line((cx - w / 2 - 26, y - 3), (cx - w / 2 - 9, y - 3))
    shape.draw_line((cx + w / 2 + 9, y - 3), (cx + w / 2 + 26, y - 3))
    shape.finish(color=RULE, width=0.5)
    shape.commit()


def _running_head(head: _Head, page, text: str, side: str) -> None:
    size = 8.0
    rect = page.rect
    text = _fit(text, (rect.width - 2 * MARGIN) / 2, size,
                lambda t: head.width(t, size))
    if not text:
        return
    w = head.width(text, size)
    x = MARGIN if side == "left" else rect.width - MARGIN - w
    head.draw(page, x, 40, text, size, INK)
    shape = page.new_shape()
    shape.draw_line((MARGIN, 46), (rect.width - MARGIN, 46))
    shape.finish(color=RULE, width=0.5)
    shape.commit()


def build_pdf(html_path: Path, meta_path: Path, out: Path | None = None,
              browser: str | None = None) -> Path:
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    out = out or html_path.with_suffix(".pdf")
    raw = html_path.with_name(html_path.stem + ".raw.pdf")
    _print_pdf(html_path, raw, browser)
    doc = fitz.open(raw)
    n = doc.page_count

    outline = meta["outline"]
    anchors = [entry["anchor"] for entry in outline]
    dest = _destinations(doc, anchors)
    missing = sorted({a for a in anchors if a not in dest})
    if missing:
        doc.close()
        raise RuntimeError(f"pdf: no destination found for {missing[:8]}")

    doc.set_toc([[entry["level"], entry["label"], dest[entry["anchor"]] + 1]
                 for entry in outline])

    fontfile = next((f for f in CJK_FONTS if Path(f).exists()), None)
    if fontfile is None:
        doc.close()
        raise RuntimeError(
            "pdf: no CJK face available, so the running heads and folios "
            f"would lose every Chinese glyph (searched: {', '.join(CJK_FONTS)})")
    head = _Head(fontfile)
    book = meta["title"]
    starts = sorted((dest[a], label) for a, label in meta["heads"])

    def head_for(pno: int) -> str:
        cur = ""
        for page_start, label in starts:
            if page_start <= pno:
                cur = label
            else:
                break
        return cur

    front = dest[meta["front_anchor"]]          # 第一章正文页（0-based）
    for pno in range(1, n):                     # 封面保持干净
        page = doc[pno]
        _folio(head, page, pno + 1, n)
        if pno < front:
            continue
        if pno % 2 == 0:                        # 双数页（recto）：章名，外侧
            _running_head(head, page, head_for(pno) or book, "right")
        else:                                   # 单数页（verso）：书名
            _running_head(head, page, book, "left")

    # 目录行页码：盖进构建时保留的槽位（整行 flex 链接，宽 rect 才算行）
    rows = set(meta["toc_rows"]) - {"front"}
    hits = [pno for pno in range(front) if doc[pno].search_for(meta["toc_title"])]
    if not hits:
        doc.close()
        raise RuntimeError("pdf: contents pages not found")
    min_row = doc[0].rect.width * 0.5
    best: dict[str, tuple[int, fitz.Rect]] = {}
    for pno in range(hits[0], front):
        for link in doc[pno].get_links():
            anchor = link.get("nameddest")
            if anchor not in rows:
                continue
            r = fitz.Rect(link["from"])
            if r.width < min_row:
                continue
            if anchor not in best or r.height > best[anchor][1].height:
                best[anchor] = (pno, r)
    for anchor, (pno, r) in best.items():
        label = str(dest[anchor] + 1)
        w = fitz.get_text_length(label, fontname="helv", fontsize=8.2)
        doc[pno].insert_text((r.x1 - w, r.y1 - 7), label, fontsize=8.2,
                             fontname="helv", color=(0.36, 0.32, 0.24))
    if len(best) < len(rows):
        missed = sorted(rows - set(best))
        doc.close()
        raise RuntimeError(f"pdf: stamped only {len(best)} of {len(rows)} "
                           f"contents rows (missing {missed[:8]})")

    holes = empty_sheets(doc)
    if holes:
        doc.close()
        raise RuntimeError(
            f"pdf: {len(holes)} sheet(s) carry nothing but a running head and a "
            f"folio (pages {holes[:8]}{'…' if len(holes) > 8 else ''}) — a unit "
            "must close on the page it ends on")

    doc.set_metadata({
        "title": meta["title"], "author": meta.get("author", ""),
        "subject": meta.get("subtitle", ""),
        "creator": "stm32-merged-book", "producer": "stm32-merged-book"})
    doc.subset_fonts()
    doc.save(out, garbage=4, deflate=True)
    doc.close()
    raw.unlink(missing_ok=True)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--html", required=True)
    parser.add_argument("--meta", required=True)
    parser.add_argument("--out", default=None)
    parser.add_argument("--browser", default=None)
    args = parser.parse_args(argv)
    out = build_pdf(Path(args.html), Path(args.meta),
                    Path(args.out) if args.out else None, args.browser)
    print(f"pdf: {out} ({sheet_count(out)} pages)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

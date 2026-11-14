#!/usr/bin/env python3
"""EPUB 3 构建器：读印刷版单文件 HTML，打包成 EPUB。

薄壳复用 `tools/build_epub.py` 的成熟机制（节拆分、data URI 抽取为真实图片、
XHTML 序列化带 SVG 命名空间、nav + NCX、锚点跨文件改写），输入切到合并书的
印刷版 HTML（`book/dist/print/merged-book.html`，由 `build_print_edition.py`
产出、`print_pdf.py` 打印同一份）——三个版本（HTML 站点 / PDF / EPUB）同源，
不会漂移。

用法：
  python book/build_epub.py                            # 默认输入/输出
  python book/build_epub.py --html PATH --out PATH
  可选 --cover-png PATH 覆盖封面；缺省从印刷版 #front 自动截取 A4 封面。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BOOK_DIR = Path(__file__).resolve().parent
REPO_ROOT = BOOK_DIR.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))
sys.path.insert(0, str(BOOK_DIR))

import importlib.util as _ilu
_spec = _ilu.spec_from_file_location(
    'tools_build_epub', REPO_ROOT / 'tools' / 'build_epub.py')
epub_lib = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(epub_lib)
from build_print_edition import DEFAULT_OUT  # noqa: E402

DEFAULT_HTML = DEFAULT_OUT
DEFAULT_EPUB = DEFAULT_OUT.with_suffix(".epub")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--html", default=str(DEFAULT_HTML))
    parser.add_argument("--out", default=str(DEFAULT_EPUB))
    parser.add_argument("--cover-png", default=None)
    args = parser.parse_args(argv)

    html_path = Path(args.html)
    if not html_path.exists():
        raise SystemExit(f"print edition not found: {html_path} — run "
                         "book/build_print_edition.py first")
    book_html = html_path.read_text(encoding="utf-8")

    out_path = Path(args.out)
    cover_png = Path(args.cover_png).read_bytes() if args.cover_png else None
    if cover_png is None:
        cover_tmp = out_path.with_suffix(".cover.png")
        if epub_lib.render_cover_png(html_path, cover_tmp):
            cover_png = cover_tmp.read_bytes()
            print(f"epub cover: {cover_tmp.name} ({len(cover_png)} bytes)")
        cover_tmp.unlink(missing_ok=True)
    report = epub_lib.build_epub(
        book_html, out_path, language="zh-CN",
        title="通往单片机之路", cover_png=cover_png)
    print(f"epub: {args.out} — spine {report.get('spine', '?')} items, "
          f"images {report.get('images', '?')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

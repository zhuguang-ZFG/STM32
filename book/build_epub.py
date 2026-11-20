#!/usr/bin/env python3
"""EPUB 3 构建器：读印刷版单文件 HTML，打包成 EPUB。

薄壳复用 `tools/build_epub.py` 的成熟机制（节拆分、data URI 抽取为真实图片、
XHTML 序列化带 SVG 命名空间、nav + NCX、锚点跨文件改写），输入切到合并书的
印刷版 HTML（`book/dist/print/merged-book.html`，由 `build_print_edition.py`
产出、`print_pdf.py` 打印同一份）——三个版本（HTML 站点 / PDF / EPUB）同源，
不会漂移。

EPUB 特有一步：全部 SVG 图片光栅化成 PNG。阅读器对 `<img>` 指向 SVG 的支持
参差（NeatReader 实测不渲染），矢量在纸上/站里的优势到了 EPUB 里换不来兼容；
按 viewBox 尺寸定倍率（小图 2x、大图 1.5x）+ 256 色量化，线条图几乎无损。
PDF 与站点不受影响（Chromium 打印吃矢量，浏览器原生渲染 SVG）。

用法：
  python book/build_epub.py                            # 默认输入/输出
  python book/build_epub.py --html PATH --out PATH
  可选 --cover-png PATH 覆盖封面；缺省从印刷版 #front 自动截取 A4 封面。
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import io
import re
import sys
import tempfile
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

SVG_URI_RE = re.compile(r'data:image/svg\+xml;base64,([A-Za-z0-9+/=]+)')
VIEWBOX_RE = re.compile(r'viewBox="0 0 ([\d.]+) ([\d.]+)"')


def _quantize_png(shot: bytes) -> bytes:
    """手绘板是平色线条图：256 色中位切分量化，肉眼无损，体积降一个量级。"""
    from PIL import Image

    im = Image.open(io.BytesIO(shot)).convert("RGB")
    q = im.quantize(colors=256, method=Image.MEDIANCUT, dither=Image.NONE)
    buf = io.BytesIO()
    q.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def rasterize_svg_data_uris(html: str) -> str:
    """把 data:image/svg+xml 的 <img> 换成 PNG 数据 URI；同一 SVG 只截一次。"""

    payloads = sorted(set(SVG_URI_RE.findall(html)))
    if not payloads:
        return html

    def render_all(workdir: Path) -> dict[str, str]:
        from playwright.sync_api import sync_playwright

        out: dict[str, str] = {}
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            for payload in payloads:
                key = hashlib.sha1(payload.encode("ascii")).hexdigest()[:16]
                svg_path = workdir / f"{key}.svg"
                svg_path.write_bytes(base64.b64decode(payload))
                text = svg_path.read_text(encoding="utf-8")
                vb = VIEWBOX_RE.search(text)
                w, h = (float(vb.group(1)), float(vb.group(2))) if vb \
                    else (900.0, 560.0)
                scale = 2.0 if max(w, h) < 500 else 1.5
                page = browser.new_page(
                    viewport={"width": int(w * scale) + 20,
                              "height": int(h * scale) + 20},
                    device_scale_factor=scale)
                page.goto(svg_path.as_uri())
                page.wait_for_timeout(120)
                element = page.query_selector("svg")
                if element is None:
                    raise RuntimeError(f"rasterize: no <svg> in staged {key}")
                shot = element.screenshot()
                page.close()
                uri = "data:image/png;base64," + base64.b64encode(
                    _quantize_png(shot)).decode("ascii")
                out[payload] = uri
            browser.close()
        return out

    with tempfile.TemporaryDirectory(prefix="epub-svg-") as tmp:
        mapping = render_all(Path(tmp))
    html = SVG_URI_RE.sub(lambda m: mapping[m.group(1)], html)
    print(f"epub svg->png: {len(payloads)} figures rasterized")
    return html


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
    book_html = rasterize_svg_data_uris(book_html)

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

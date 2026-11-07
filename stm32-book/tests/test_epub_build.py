"""EPUB packager contract (tools/build_epub.py).

Feeds a synthetic mini book HTML (same section structure as the real
build) through the packager and asserts the EPUB container rules:
mimetype first and stored, well-formed XHTML, spine completeness,
cross-chapter anchors rewritten to file-qualified links, and data-URI
images extracted to manifest files.
"""
from __future__ import annotations

import base64
import importlib.util
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

_SVG = ("<svg xmlns='http://www.w3.org/2000/svg' width='10' height='10'>"
        "<rect width='10' height='10' fill='#075e84'/></svg>")
_DATA = "data:image/svg+xml;base64," + base64.b64encode(_SVG.encode()).decode()

BOOK_HTML = f"""<!doctype html>
<html lang="zh-CN"><head><title>STM32 实战：测试版</title></head>
<body><main class="book">
<section class="cover" id="cover"><h1>STM32 实战</h1></section>
<section class="imprint" id="imprint"><h2>版本与许可</h2></section>
<section class="frontmatter" id="how-to-read"><h2>怎么读</h2></section>
<section class="contents" id="contents"><a href="#ch00-1">第 1 章</a></section>
<section class="part-divider" id="part-p0"><h1>第一部分</h1></section>
<article class="chapter" id="chapter-00">
<header><h1 id="ch00-1">如何学习 STM32</h1></header>
<h2 id="ch00-2">最小胜利</h2>
<p align="center"><img src="{_DATA}" width="10" alt="示意"></p>
<p>先读<a href="#ch01-1">下一章</a>和<a href="#ch00-1">本章小节</a>。</p>
</article>
<article class="chapter" id="chapter-01">
<header><h1>开发环境搭建</h1></header><p id="ch01-1">环境四步。</p>
</article>
</main></body></html>"""


def load_builder():
    path = ROOT / "tools" / "build_epub.py"
    spec = importlib.util.spec_from_file_location("build_epub_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class EpubBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.be = load_builder()
        cls.out = Path(__import__("tempfile").mkdtemp()) / "mini.epub"
        cls.info = cls.be.build_epub(BOOK_HTML, cls.out, "zh-CN",
                                     "STM32 实战：测试版")

    def test_container_rules_hold(self) -> None:
        errors = self.be._validate(self.out)
        self.assertEqual([], errors, errors)

    def test_mimetype_is_first_and_stored(self) -> None:
        with zipfile.ZipFile(self.out) as zf:
            self.assertEqual("mimetype", zf.namelist()[0])
            self.assertEqual(zipfile.ZIP_STORED,
                             zf.getinfo("mimetype").compress_type)
            self.assertEqual(b"application/epub+zip", zf.read("mimetype"))

    def test_images_are_extracted_not_inlined(self) -> None:
        with zipfile.ZipFile(self.out) as zf:
            names = zf.namelist()
            images = [n for n in names if n.startswith("OEBPS/images/")]
            self.assertEqual(1, len(images), names)
            self.assertTrue(images[0].endswith(".svg"))
            seg = zf.read("OEBPS/seg06.xhtml").decode("utf-8")
            self.assertNotIn("data:image", seg)
            self.assertIn('src="images/', seg)

    def test_cross_chapter_anchor_is_file_qualified(self) -> None:
        with zipfile.ZipFile(self.out) as zf:
            seg = zf.read("OEBPS/seg06.xhtml").decode("utf-8")
            self.assertIn('href="seg07.xhtml#ch01-1"', seg)
            self.assertIn('href="#ch00-1"', seg)

    def test_nav_nests_section_level(self) -> None:
        with zipfile.ZipFile(self.out) as zf:
            nav = zf.read("OEBPS/nav.xhtml").decode("utf-8")
            self.assertIn('href="seg06.xhtml#ch00-2"', nav)
            self.assertIn("最小胜利", nav)
            ncx = zf.read("OEBPS/toc.ncx").decode("utf-8")
            self.assertIn('content src="seg06.xhtml#ch00-2"', ncx)
            self.assertIn('dtb:depth" content="2"', ncx)

    def test_nav_covers_spine_order(self) -> None:
        with zipfile.ZipFile(self.out) as zf:
            nav = zf.read("OEBPS/nav.xhtml").decode("utf-8")
            self.assertIn("第一部分", nav)
            self.assertIn("如何学习 STM32", nav)
            self.assertIn("开发环境搭建", nav)


if __name__ == "__main__":
    unittest.main()

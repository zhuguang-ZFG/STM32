import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from book.build_print_edition import build, chapter_number, chapter_section
from book.print_css import build_css


class CoverCopyTests(unittest.TestCase):
    def test_cover_describes_guidance_without_claiming_hardware_validation(self):
        manifest = {"title": "测试书", "subtitle": "测试副题", "parts": [], "appendices": []}
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "cover.html"
            with patch("book.manifest.load_toc", return_value=[]), patch(
                "book.manifest.build_manifest", return_value=manifest
            ):
                build(out)
            html = out.read_text(encoding="utf-8")
        matched = re.search(r'<p class="book-sub">([^<]*)</p>', html)
        if matched is None:
            self.fail("渲染结果里没有 book-sub 段落")
        subtitle = matched.group(1)
        self.assertEqual(subtitle, "原理讲解 · 工程示例 · 实验指南")
        self.assertNotIn("全程实物实验", subtitle)
        self.assertNotIn("全程实测", subtitle)


class PrintCssTests(unittest.TestCase):
    def test_no_element_can_expand_the_print_viewport(self):
        css = build_css()
        # 宽表 auto 布局、带首行缩进的整段图片、不可断的长 API 名都会把
        # 176mm 版心撑宽；Chromium 会因此把整本书缩到 0.8x。这些是防回归契约。
        self.assertIn("table-layout: fixed", css)
        self.assertIn("p:has(img) { text-indent: 0; }", css)
        self.assertIn("code, a { overflow-wrap: anywhere; }", css)
        self.assertIn("width: 176mm", css)

    def test_figure_size_tiers_default_m_and_bounded_l(self):
        css = build_css()
        # Default/M remains the existing 150mm cap.
        self.assertRegex(
            css,
            r"figure img,\s*figure svg \{\s*max-height: 150mm;\s*max-width: 100%;\s*width: auto;\s*\}",
        )
        # S tier.
        self.assertIn("figure.book-figure.fig-s img,", css)
        self.assertIn("max-height: 72mm;", css)
        # M tier explicit (same cap as default; class makes intent visible).
        self.assertIn("figure.book-figure.fig-m img,", css)
        # L tier: landscape only, block budget 170mm, image cap 150mm, never 190mm.
        self.assertIn("figure.book-figure.fig-l.landscape {", css)
        self.assertIn("max-height: 170mm;", css)
        self.assertRegex(
            css,
            r"figure\.book-figure\.fig-l\.landscape img,\s*figure\.book-figure\.fig-l\.landscape svg \{(?s:.*?)max-height: 150mm;",
        )
        self.assertNotIn("max-height: 190mm", css)
        # Existing landscape semantics preserved.
        self.assertIn("@page plate-landscape { size: A4 landscape; margin: 21mm 17mm 19mm; }", css)
        self.assertIn("figure.landscape { page: plate-landscape; break-before: page;", css)


class ChapterSectionTests(unittest.TestCase):
    def test_chapter_number_from_anchor(self):
        self.assertEqual(chapter_number("ch07"), "07")
        self.assertEqual(chapter_number("appendix-a"), "A")
        self.assertEqual(chapter_number("part-v1"), "")

    def test_markdown_h1_is_not_printed_twice(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ch07.md").write_text(
                "---\ntitle: 测试章\n---\n\n# 测试章\n\n正文。\n",
                encoding="utf-8",
            )
            html, title = chapter_section(
                {"id": "ch07", "file": "ch07.md", "title": "测试章"},
                root,
                {},
            )
        self.assertEqual(title, "测试章")
        self.assertEqual(html.count("<h1"), 1)
        self.assertIn('<div class="chapter-no" aria-hidden="true">07</div>', html)
        self.assertIn('<h1 id="测试章">测试章</h1>', html)


    def test_label_colon_stays_with_bold_label(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ch07.md").write_text(
                "---\ntitle: 测试章\n---\n\n# 测试章\n\n**问题**：正文。\n",
                encoding="utf-8",
            )
            html, _title = chapter_section(
                {"id": "ch07", "file": "ch07.md", "title": "测试章"},
                root,
                {},
            )
        self.assertIn("<strong>问题：</strong>正文。", html)


class SiteStyleTests(unittest.TestCase):
    def test_figure_size_tiers_present(self):
        css = (ROOT / "docs" / ".vitepress" / "theme" / "style.css").read_text(encoding="utf-8")
        self.assertIn(".vp-doc figure.book-figure.fig-s img", css)
        self.assertIn("max-width: min(100%, 28rem);", css)
        self.assertIn(".vp-doc figure.book-figure.fig-m img", css)
        self.assertIn("max-width: min(100%, 42rem);", css)
        self.assertIn(".vp-doc figure.book-figure.fig-l img", css)
        # Default figure remains responsive.
        self.assertIn(".vp-doc figure.book-figure img {", css)
        self.assertIn("max-width: 100%;", css)


if __name__ == "__main__":
    unittest.main()

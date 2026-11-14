import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from book.build_print_edition import chapter_number, chapter_section
from book.print_css import build_css


class PrintCssTests(unittest.TestCase):
    def test_no_element_can_expand_the_print_viewport(self):
        css = build_css()
        # 宽表 auto 布局、带首行缩进的整段图片、不可断的长 API 名都会把
        # 176mm 版心撑宽；Chromium 会因此把整本书缩到 0.8x。这些是防回归契约。
        self.assertIn("table-layout: fixed", css)
        self.assertIn("p:has(img) { text-indent: 0; }", css)
        self.assertIn("code, a { overflow-wrap: anywhere; }", css)
        self.assertIn("width: 176mm", css)


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


if __name__ == "__main__":
    unittest.main()

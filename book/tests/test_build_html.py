import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from book import build_html

CHAPTER = """---
title: "测试章"
platforms: [generic]
---

# 测试章

## 本章罗盘

- **问题**：测试。
- **交付**：测试。
- **边界**：测试。
- **依据锚点**：测试。

## 先做出来

![演示图](/arch/demo.svg)

[去第二章](./02-other.md)

## 机制

<QuizBank chapter="q1" />
"""

MANIFEST = {
    "title": "测试书",
    "subtitle": "",
    "version": "0.1.0",
    "language": "zh",
    "parts": [
        {
            "id": "v0",
            "title": "卷 0",
            "goal": "",
            "chapters": [
                {
                    "id": "ch01",
                    "title": "测试章",
                    "file": "v0-foundations/01-a.md",
                    "status": "planned",
                    "platforms": ["generic"],
                },
                {
                    "id": "ch02",
                    "title": "缺章",
                    "file": "v0-foundations/02-other.md",
                    "status": "planned",
                    "platforms": ["generic"],
                },
            ],
        }
    ],
    "appendices": [],
}


class BuildHtmlTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.docs = Path(self.tmp.name) / "docs"
        self.quiz_dir = self.docs / ".vitepress" / "data" / "quizzes"
        self.quiz_dir.mkdir(parents=True)
        (self.docs / "v0-foundations").mkdir(parents=True)
        (self.docs / "public" / "arch").mkdir(parents=True)
        (self.docs / "public" / "arch" / "demo.svg").write_text(
            '<svg width="10" height="5" viewBox="0 0 10 5"></svg>', encoding="utf-8"
        )
        (self.docs / "v0-foundations" / "01-a.md").write_text(CHAPTER, encoding="utf-8")
        (self.quiz_dir / "q1.json").write_text(
            '{"title": "自测", "chapter": "q1", "questions": ['
            '{"q": "题?", "options": ["A", "B"], "answer": 0, "a": "解析"}]}',
            encoding="utf-8",
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_build_renders_pages(self):
        out = Path(self.tmp.name) / "out"
        pages, missing = build_html.build(
            out, docs_root=self.docs, quiz_dir=self.quiz_dir, manifest=MANIFEST
        )
        self.assertEqual(pages, ["v0-foundations/01-a.html"])
        self.assertEqual(missing, ["ch02"])
        page = (out / "v0-foundations" / "01-a.html").read_text(encoding="utf-8")
        self.assertIn('id="先做出来"', page)
        self.assertIn('<section class="quiz">', page)
        self.assertIn('src="../arch/demo.svg"', page)
        self.assertIn('width="10" height="5"', page)
        self.assertIn('class="book-figure"', page)
        self.assertIn('<figcaption>演示图</figcaption>', page)
        self.assertIn('href="./02-other.html"', page)
        self.assertTrue((out / "index.html").exists())
        self.assertTrue((out / "arch" / "demo.svg").exists())

    def test_wrap_figures_only_for_standalone_captioned_images(self):
        standalone = '<p><img alt="图注" src="/a.png" /></p>'
        inline = '<p>看图 <img alt="图注" src="/a.png" /> 说明</p>'
        empty = '<p><img alt="" src="/a.png" /></p>'
        self.assertIn('<figure class="book-figure">', build_html.wrap_figures(standalone))
        self.assertNotIn('<figure', build_html.wrap_figures(inline))
        self.assertNotIn('<figure', build_html.wrap_figures(empty))

    def test_add_image_dimensions_keeps_existing_width_ratio(self):
        png = b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\rIHDR" + (100).to_bytes(4, "big") + (50).to_bytes(4, "big")
        (self.docs / "public" / "arch" / "demo.png").write_bytes(png)
        html_text = '<p><img src="/arch/demo.png" alt="示意" width="76"></p>'
        rendered = build_html.add_image_dimensions(html_text, self.docs / "public")
        self.assertIn('width="76" height="38"', rendered)

    def test_wrap_tables_marks_scroll_container(self):
        wrapped = build_html.wrap_tables("<table><tr><td>x</td></tr></table>")
        self.assertEqual(
            wrapped,
            '<div class="table-scroll"><table><tr><td>x</td></tr></table></div>',
        )

    def test_build_requires_at_least_one_chapter(self):
        (self.docs / "v0-foundations" / "01-a.md").unlink()
        with self.assertRaises(ValueError):
            build_html.build(
                Path(self.tmp.name) / "out",
                docs_root=self.docs,
                quiz_dir=self.quiz_dir,
                manifest=MANIFEST,
            )


class StickSceneEmbedTest(unittest.TestCase):
    def test_marker_in_paragraph_becomes_scene_figure(self):
        html_in = "<p>前文</p>\n<p><!-- stick-scene: ch00-unbox-blink --></p>\n<p>后文</p>"
        out = build_html.embed_stick_scenes(html_in)
        self.assertIn('class="book-figure book-scene"', out)
        self.assertIn('<stick-scene scene="ch00-unbox-blink" play="view" no-font', out)
        self.assertIn("aria-label=", out)
        self.assertIn('<noscript><img src="/images/ch00-unbox-blink-frame.png"', out)
        self.assertIn('<figcaption>手绘动画：从 make 到 1 Hz', out)
        # runtime must precede the scene script so window.RIG exists on load
        self.assertLess(
            out.index('src="/scenes/stick.js"'),
            out.index('src="/scenes/ch00-unbox-blink.js"'),
        )
        self.assertTrue(out.startswith("<p>前文</p>"))
        self.assertTrue(out.rstrip().endswith("<p>后文</p>"))

    def test_bare_comment_marker_also_matches(self):
        out = build_html.embed_stick_scenes("x\n<!-- stick-scene: ch00-unbox-blink -->\ny")
        self.assertIn("<stick-scene", out)
        self.assertNotIn("stick-scene:", out)

    def test_unknown_scene_id_is_a_build_error(self):
        with self.assertRaises(ValueError):
            build_html.embed_stick_scenes("<!-- stick-scene: no-such-scene -->")

    def test_plain_comment_without_marker_is_untouched(self):
        html_in = "<p><!-- 构建提示：保留 --></p>"
        self.assertEqual(build_html.embed_stick_scenes(html_in), html_in)

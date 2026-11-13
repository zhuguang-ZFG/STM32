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
        (self.docs / "public" / "arch" / "demo.svg").write_text("<svg/>", encoding="utf-8")
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
        self.assertIn('href="./02-other.html"', page)
        self.assertTrue((out / "index.html").exists())
        self.assertTrue((out / "arch" / "demo.svg").exists())

    def test_build_requires_at_least_one_chapter(self):
        (self.docs / "v0-foundations" / "01-a.md").unlink()
        with self.assertRaises(ValueError):
            build_html.build(
                Path(self.tmp.name) / "out",
                docs_root=self.docs,
                quiz_dir=self.quiz_dir,
                manifest=MANIFEST,
            )

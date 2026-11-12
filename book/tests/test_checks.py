import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from book import checks
from book import manifest as mf


def chapter_text(title: str, platforms: str, body: str = "") -> str:
    return (
        "---\n"
        f'title: "{title}"\n'
        f"platforms: [{platforms}]\n"
        "---\n\n"
        f"# {title}\n\n"
        "## 本章罗盘\n\n"
        "- **问题**：测试问题。\n"
        "- **交付**：测试交付。\n"
        "- **边界**：测试边界。\n"
        "- **依据锚点**：测试锚点。\n\n"
        f"{body}"
    )


class ChecksTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.docs = Path(self.tmp.name)
        self.quiz_dir = self.docs / ".vitepress" / "data" / "quizzes"
        self.quiz_dir.mkdir(parents=True)
        self.rows = {row["id"]: row for row in mf.load_toc()}
        (self.docs / "public" / "arch").mkdir(parents=True)
        (self.docs / "public" / "arch" / "demo.svg").write_text("<svg/>", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def write_chapter(self, chapter_id: str, body: str = "") -> Path:
        row = self.rows[chapter_id]
        path = self.docs / row["file"]
        path.parent.mkdir(parents=True, exist_ok=True)
        platforms = ", ".join(row["platforms"])
        path.write_text(chapter_text(row["title"], platforms, body), encoding="utf-8")
        return path

    def write_quiz(self, quiz_id: str, answer: int = 0) -> Path:
        path = self.quiz_dir / f"{quiz_id}.json"
        options = ["A", "B"]
        path.write_text(
            '{"title": "自测", "chapter": "%s", "questions": ['
            '{"q": "题?", "options": ["A", "B"], "answer": %d, "a": "解析"}]}'
            % (quiz_id, answer),
            encoding="utf-8",
        )
        return path

    def test_valid_chapter_passes(self):
        self.write_chapter(
            "ch01",
            '![图](/arch/demo.svg)\n\n<a id="self"></a>\n\n'
            "## 小节\n\n[本章](#小节)\n\n<QuizBank chapter=\"q1\" />\n",
        )
        self.write_quiz("q1")
        self.assertEqual(checks.check_book(docs_root=self.docs, quiz_dir=self.quiz_dir), [])

    def test_missing_anchor_detected(self):
        self.write_chapter("ch01", "## 小节\n\n[跳到](#不存在)\n")
        errors = checks.check_book(docs_root=self.docs, quiz_dir=self.quiz_dir)
        self.assertTrue(any("missing anchor" in error for error in errors), errors)

    def test_missing_image_detected(self):
        self.write_chapter("ch01", "![图](/arch/nope.svg)\n")
        errors = checks.check_book(docs_root=self.docs, quiz_dir=self.quiz_dir)
        self.assertTrue(any("missing asset" in error for error in errors), errors)

    def test_external_image_detected(self):
        self.write_chapter("ch01", "![图](https://example.com/a.png)\n")
        errors = checks.check_book(docs_root=self.docs, quiz_dir=self.quiz_dir)
        self.assertTrue(any("external image" in error for error in errors), errors)

    def test_quiz_schema_detected(self):
        self.write_chapter("ch01", '<QuizBank chapter="q1" />\n')
        self.write_quiz("q1", answer=5)
        errors = checks.check_book(docs_root=self.docs, quiz_dir=self.quiz_dir)
        self.assertTrue(any("answer out of range" in error for error in errors), errors)

    def test_orphan_quiz_detected(self):
        self.write_chapter("ch01")
        self.write_quiz("q1")
        errors = checks.check_book(docs_root=self.docs, quiz_dir=self.quiz_dir)
        self.assertTrue(any("orphan quiz" in error for error in errors), errors)

    def test_duplicate_quiz_reference_detected(self):
        self.write_chapter("ch01", '<QuizBank chapter="q1" />\n')
        self.write_chapter("ch02", '<QuizBank chapter="q1" />\n')
        self.write_quiz("q1")
        errors = checks.check_book(docs_root=self.docs, quiz_dir=self.quiz_dir)
        self.assertTrue(any("multiple chapters" in error for error in errors), errors)

    def test_code_spans_are_not_scanned_as_links(self):
        self.write_chapter(
            "ch01",
            "函数指针调用 `callbacks[i](arg)` 不是链接。\n\n"
            "```c\nint x = table[i](arg);\n// [文档](./missing.md) 在代码块里\n```\n\n"
            "<QuizBank chapter=\"q1\" />\n",
        )
        self.write_quiz("q1")
        self.assertEqual(checks.check_book(docs_root=self.docs, quiz_dir=self.quiz_dir), [])

    def test_title_or_platform_mismatch_detected(self):
        self.write_chapter("ch01")
        path = self.docs / self.rows["ch01"]["file"]
        path.write_text(chapter_text("错标题", "f407"), encoding="utf-8")
        errors = checks.check_book(docs_root=self.docs, quiz_dir=self.quiz_dir)
        self.assertTrue(any("frontmatter title" in error for error in errors), errors)
        self.assertTrue(any("frontmatter platforms" in error for error in errors), errors)

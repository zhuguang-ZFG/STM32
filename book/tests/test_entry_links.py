"""Entry documents (README and friends) carry links too, and they rot.

`check_book` walks the manifest, which holds the 47 chapters and 6 appendices.
README / CREDITS / STRUCTURE / assets README / tool READMEs sit outside that
list, so a renamed directory or a retired image left a dead link that no gate
caught: the first thing a visitor clicks could 404 with `checks passed`.
"""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from book.checks import (
    ENTRY_DOCS,
    blockquote_anchors,
    check_book,
    check_entry_doc,
    heading_anchors,
)


class EntryDocLinkTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        (self.repo / "docs" / "public" / "images").mkdir(parents=True)
        (self.repo / "docs" / "public" / "images" / "plate.png").write_bytes(b"png")
        (self.repo / "docs" / "other.md").write_text(
            "# 另一篇\n\n## 小节甲\n\n## 重复\n\n## 重复\n\n正文。\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def _write(self, text: str, name: str = "README.md") -> Path:
        path = self.repo / name
        path.write_text(text, encoding="utf-8")
        return path

    def test_missing_relative_target_is_an_error(self):
        path = self._write("[指南](docs/CONTENT_GUIDE-GONE.md)\n")
        errors = check_entry_doc(path, self.repo)
        self.assertIn("missing target: docs/CONTENT_GUIDE-GONE.md", errors[0])
        self.assertIn("README.md:", errors[0], "output should stay repo-relative")

    def test_existing_relative_target_passes(self):
        path = self._write("[另一篇](docs/other.md)\n")
        self.assertEqual(check_entry_doc(path, self.repo), [])

    def test_missing_anchor_is_an_error(self):
        path = self._write("[跳](docs/other.md#不存在的小节)\n")
        errors = check_entry_doc(path, self.repo)
        self.assertTrue(any("missing anchor" in e for e in errors), errors)

    def test_existing_anchor_passes(self):
        path = self._write("[跳](docs/other.md#小节甲)\n")
        self.assertEqual(check_entry_doc(path, self.repo), [])
        # docs/ is rendered by VitePress: a repeated slug becomes `_1`, so the
        # cross-file check must use the target's rule, not the entry doc's.
        path = self._write("[跳](docs/other.md#重复_1)\n")
        self.assertEqual(check_entry_doc(path, self.repo), [])

    def test_same_page_blockquote_heading_is_exempt_not_asserted(self):
        """`> ### 标题` targets are skipped, not blessed.

        Whether a renderer gives blockquote headings an id is the renderer's
        business and could not be observed here, so the checker must not
        report such a fragment as valid — and must not fail on it either.
        """
        path = self._write("> ### 公众号连载版\n\n[去](#公众号连载版)\n")
        self.assertEqual(check_entry_doc(path, self.repo), [])
        self.assertNotIn("公众号连载版", heading_anchors(path.read_text(encoding="utf-8")))
        self.assertIn("公众号连载版", blockquote_anchors(path.read_text(encoding="utf-8")))

    def test_unknown_same_page_anchor_still_errors(self):
        path = self._write("> ### 甲\n\n[去](#乙)\n")
        errors = check_entry_doc(path, self.repo)
        self.assertTrue(any("missing anchor: #乙" in e for e in errors), errors)

    def test_site_absolute_image_maps_to_public(self):
        path = self._write("![图](/images/plate.png)\n")
        self.assertEqual(check_entry_doc(path, self.repo), [])
        broken = self._write("![图](/images/missing.png)\n")
        errors = check_entry_doc(broken, self.repo)
        self.assertTrue(any("missing image" in e for e in errors), errors)

    def test_external_and_code_span_links_ignored(self):
        path = self._write(
            "[外](https://example.com/x)\n\n`[代码里的](不存在.md)`\n\n"
            "```\n[围栏里的](不存在.md)\n```\n")
        self.assertEqual(check_entry_doc(path, self.repo), [])

    def test_check_book_covers_entry_docs(self):
        """The gate must fail when a shipped entry document loses a link."""
        doc = self.repo / "README.md"
        doc.write_text("[坏的](nope/missing.md)\n", encoding="utf-8")
        errors = check_book(docs_root=self.repo / "docs",
                            quiz_dir=self.repo / "quizzes")
        self.assertTrue(any("nope/missing.md" in e for e in errors), errors)


class ShippedEntryDocsTest(unittest.TestCase):
    """The real repository's entry documents must stay link-clean."""

    def test_every_entry_doc_resolves(self):
        missing = [rel for rel in ENTRY_DOCS if not (ROOT / rel).exists()]
        self.assertEqual(missing, [], "entry document went missing")
        broken = []
        for rel in ENTRY_DOCS:
            broken.extend(check_entry_doc(ROOT / rel, ROOT))
        self.assertEqual(broken, [], "broken links in entry documents")


if __name__ == "__main__":
    unittest.main()

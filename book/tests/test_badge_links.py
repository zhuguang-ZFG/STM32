"""Badge-style links are the common README idiom and were invisible to the scan.

`[![alt](badge.svg)](target)` puts a nested image inside the link text; the
original link pattern refused any `]` in the text, so the whole construct was
skipped and a dead badge target could never fail the gate. Verified by
injecting an unknown same-page anchor into README: the gate stayed green.
"""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from book.checks import LINK_RE, check_entry_doc


class BadgeLinkTests(unittest.TestCase):
    def test_badge_link_target_is_matched(self):
        text = "[![alt](https://img.example/b.svg)](#目标)\n"
        targets = [m.group(2) for m in LINK_RE.finditer(text)]
        self.assertEqual(targets, ["#目标"])

    def test_plain_image_is_not_treated_as_link(self):
        text = "![图](img.png)\n"
        self.assertEqual([m.group(2) for m in LINK_RE.finditer(text)], [])

    def test_dead_badge_target_fails_the_check(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            (repo / "README.md").write_text(
                "[![alt](https://img.example/b.svg)](#没有这个锚点)\n",
                encoding="utf-8")
            errors = check_entry_doc(repo / "README.md", repo)
            self.assertTrue(any("missing anchor" in e for e in errors), errors)

    def test_badge_pointing_at_real_file_passes(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            (repo / "docs").mkdir()
            (repo / "docs" / "README.md").write_text("# 文档\n", encoding="utf-8")
            (repo / "README.md").write_text(
                "[![docs](https://img.example/b.svg)](docs/README.md)\n",
                encoding="utf-8")
            self.assertEqual(check_entry_doc(repo / "README.md", repo), [])


if __name__ == "__main__":
    unittest.main()

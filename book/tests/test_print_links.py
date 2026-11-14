import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from book.build_print_edition import rewrite_book_links


class PrintLinkTests(unittest.TestCase):
    def setUp(self):
        self.files = {
            "v1-drivers/12-timers-pwm.md": "ch12",
            "v6-labs-projects/41-dual-board-logger-project.md": "ch41",
        }
        self.current = "v6-labs-projects/41-dual-board-logger-project.md"

    def test_cross_chapter_link_becomes_chapter_anchor(self):
        html = '<a href="../v1-drivers/12-timers-pwm.md">timer</a>'
        self.assertEqual(
            rewrite_book_links(html, self.current, self.files),
            '<a href="#ch12">timer</a>',
        )

    def test_cross_chapter_fragment_collapses_to_chapter_anchor(self):
        html = '<a href="../v1-drivers/12-timers-pwm.md#counting">timer</a>'
        self.assertEqual(
            rewrite_book_links(html, self.current, self.files),
            '<a href="#ch12">timer</a>',
        )

    def test_same_chapter_fragment_is_preserved(self):
        html = '<a href="./41-dual-board-logger-project.md#faults">here</a>'
        self.assertEqual(
            rewrite_book_links(html, self.current, self.files),
            '<a href="#faults">here</a>',
        )

    def test_unknown_target_stays_a_page_link(self):
        html = '<a href="./missing.md">missing</a>'
        self.assertEqual(
            rewrite_book_links(html, self.current, self.files),
            '<a href="./missing.html">missing</a>',
        )

    def test_external_link_is_untouched(self):
        html = '<a href="https://example.com/a.md">external</a>'
        self.assertEqual(rewrite_book_links(html, self.current, self.files), html)


if __name__ == "__main__":
    unittest.main()

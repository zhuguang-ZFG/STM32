import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from book import contracts as c

FIXTURES = Path(__file__).parent / "fixtures"


class ContractsTest(unittest.TestCase):
    def test_valid_fixture_passes(self):
        self.assertEqual(c.validate_chapter_file(FIXTURES / "valid-chapter.md"), [])

    def test_missing_compass_detected(self):
        errors = c.validate_chapter_file(FIXTURES / "invalid-missing-compass.md")
        self.assertTrue(any("本章罗盘" in error for error in errors), errors)

    def test_unknown_platform_detected(self):
        errors = c.validate_chapter_file(FIXTURES / "invalid-platform.md")
        self.assertTrue(any("platform" in error for error in errors), errors)

    def test_missing_file_detected(self):
        errors = c.validate_chapter_file(FIXTURES / "does-not-exist.md")
        self.assertTrue(any("missing file" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()

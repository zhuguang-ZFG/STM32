from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AUDIT_PATH = ROOT / "tools" / "audit_book.py"


def load_auditor():
    spec = importlib.util.spec_from_file_location("book_auditor", AUDIT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load auditor: {AUDIT_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


audit_book = load_auditor()


class BookAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = audit_book.build_audit()
        cls.by_id = {item["id"]: item for item in cls.payload["chapters"]}

    def test_audit_covers_both_editions(self) -> None:
        self.assertEqual(29, self.payload["chapter_count"])
        self.assertEqual({f"{number:02d}" for number in range(29)}, set(self.by_id))
        for item in self.payload["chapters"]:
            self.assertTrue(item["zh"]["file"].startswith("docs/"))
            self.assertTrue(item["en"]["file"].startswith("docs/en/"))

    def test_video_is_not_counted_as_a_pdf_visual(self) -> None:
        chapter = self.by_id["20"]["zh"]
        self.assertEqual(1, chapter["videos"])
        self.assertGreaterEqual(chapter["visual_assets"], chapter["pdf_visual_anchors"])

    def test_grouped_photos_are_one_reading_position(self) -> None:
        chapter = self.by_id["28"]["zh"]
        self.assertEqual(2, chapter["photos"])
        self.assertEqual(chapter["pdf_visual_anchors"] + 1, chapter["visual_assets"])

    def test_all_chapters_have_a_pdf_anchor_and_a_gap_measurement(self) -> None:
        for item in self.payload["chapters"]:
            for language in ("zh", "en"):
                chapter = item[language]
                self.assertGreaterEqual(chapter["pdf_visual_anchors"], 1, (item["id"], language))
                self.assertGreater(chapter["max_visual_gap_chars"], 0, (item["id"], language))
                self.assertGreaterEqual(chapter["target_visual_anchors"], 3)
            self.assertEqual(item["zh"]["target_visual_anchors"], item["en"]["target_visual_anchors"])

    def test_bilingual_visual_drift_is_reported_without_hiding_the_first_batch(self) -> None:
        for item in self.payload["chapters"]:
            self.assertIsInstance(item["parity"]["asset_sequence_equal"], bool)
        self.assertFalse(self.by_id["24"]["parity"]["asset_sequence_equal"])
        for chapter_id in ("20", "22", "25"):
            self.assertTrue(self.by_id[chapter_id]["parity"]["asset_sequence_equal"])

    def test_json_report_round_trips(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "audit.json"
            result = audit_book.main(["--format", "json", "--write", str(output)])
            self.assertEqual(0, result)
            loaded = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(29, loaded["chapter_count"])


if __name__ == "__main__":
    unittest.main()

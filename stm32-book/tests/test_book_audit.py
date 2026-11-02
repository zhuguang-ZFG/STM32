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

    def test_bilingual_visual_sequence_matches_repaired_chapters(self) -> None:
        for item in self.payload["chapters"]:
            self.assertIsInstance(item["parity"]["asset_sequence_equal"], bool)
        for chapter_id in ("01", "02", "20", "22", "24", "25"):
            self.assertTrue(self.by_id[chapter_id]["parity"]["asset_sequence_equal"])

    def test_first_hardware_loop_has_visual_and_structure_parity(self) -> None:
        chapter = self.by_id["01"]
        expected_assets = (
            "boot-sequence.svg",
            "sample-01-swd-vectors.svg",
            "swd-fetch.gif",
            "single-build-contract.svg",
            "project-structure.svg",
        )
        for language in ("zh", "en"):
            edition = chapter[language]
            self.assertEqual(5, edition["pdf_visual_anchors"])
            self.assertEqual(0, edition["visual_anchor_deficit"])
            self.assertEqual(expected_assets, edition["asset_sequence"])
        for field in ("h2_delta", "h3_delta", "table_delta", "code_block_delta"):
            self.assertEqual(0, chapter["parity"][field])

    def test_chapter_24_has_matching_structure_and_visual_distribution(self) -> None:
        chapter = self.by_id["24"]
        expected_assets = (
            "pinout-stm32l476rg-lqfp64.svg",
            "nucleo-f411re-embedded-world.jpg",
            "nucleo-f401re-embedded-world.jpg",
            "l4-stop2-evidence.svg",
            "l4-idd-bench.svg",
        )

        for language in ("zh", "en"):
            edition = chapter[language]
            self.assertEqual(4, edition["pdf_visual_anchors"])
            self.assertEqual(0, edition["visual_anchor_deficit"])
            self.assertEqual(2, edition["photos"])
            self.assertEqual(1, edition["animations"])
            self.assertEqual(expected_assets, edition["asset_sequence"])

        for path in (
            ROOT / "docs" / "24-STM32L4引脚.md",
            ROOT / "docs" / "en" / "24-stm32l4-pins.md",
        ):
            self.assertIn('class="photo-pair"', path.read_text(encoding="utf-8"))

        for field in ("h2_delta", "h3_delta", "table_delta", "code_block_delta"):
            self.assertEqual(0, chapter["parity"][field])

    def test_json_report_round_trips(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "audit.json"
            result = audit_book.main(["--format", "json", "--write", str(output)])
            self.assertEqual(0, result)
            loaded = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(29, loaded["chapter_count"])


if __name__ == "__main__":
    unittest.main()

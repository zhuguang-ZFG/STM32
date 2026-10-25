#!/usr/bin/env python3
"""License gate for chapters 04 and 06. The manifest is updated later."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE_LIST = ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch2-04-06-source-list.json"
LOCK = ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch2-04-06-lock.json"
ALLOWED = {
    "ST-facts-restated",
    "MIT",
    "BSD-2-Clause",
    "BSD-3-Clause",
    "ISC",
    "CC BY 4.0",
    "CC BY 3.0",
    "CC0",
}
REJECTED = ("GPL", "LGPL", "CC BY-NC", "CC BY-ND", "All rights reserved", "Apache-2.0")


class Batch2SourceListTests(unittest.TestCase):
    def test_lock_keeps_chapters_04_and_06(self) -> None:
        lock = json.loads(LOCK.read_text(encoding="utf-8"))
        self.assertEqual(["04", "06"], lock["chapters"])
        self.assertTrue(lock["four_blocks_absent"])
        self.assertTrue(lock["old_pitfall_heading_present"])
        self.assertEqual(40, len(lock["baseline"]))
        self.assertEqual("2026-10-25-classic-encyclopedia-batch2-04-06", lock["rubric"])

    def test_source_list_keeps_the_license_gate(self) -> None:
        payload = json.loads(SOURCE_LIST.read_text(encoding="utf-8"))
        self.assertEqual(["04", "06"], payload["chapters"])
        self.assertEqual([], payload["community"])
        ids = [item["id"] for item in payload["absorb"]]
        self.assertEqual(
            ["rm0008-exti", "pm0056-nvic", "rm0008-usart", "ds5319-usart"],
            ids,
        )
        self.assertNotIn("rm0090-usart-over8", ids)
        for item in payload["absorb"]:
            self.assertIn(item["license_class"], ALLOWED)
            self.assertTrue(item["url"].startswith("https://"))
            self.assertNotIn("http://", item["url"])
            for banned in REJECTED:
                self.assertNotIn(banned, item["license"])
                self.assertNotIn(banned, item["license_class"])
            self.assertTrue(item["do_not_copy"])
            self.assertGreaterEqual(len(item["points"]), 1)
            self.assertNotIn(".pdf", item["repo_path"] if "repo_path" in item else "")
        by_id = {item["id"]: item for item in payload["absorb"]}
        self.assertEqual("9.4.3", by_id["rm0008-exti"]["section"])
        self.assertEqual("2.3.7", by_id["pm0056-nvic"]["section"])
        self.assertEqual("27.3.3", by_id["rm0008-usart"]["section"])
        self.assertEqual("Figure 8", by_id["ds5319-usart"]["section"])
        self.assertNotIn("cycle", by_id["pm0056-nvic"]["snapshot"].lower())
        reused = [item["id"] for item in payload["reuse_existing"]]
        self.assertEqual(
            ["freertos-priority", "majerle-uart", "st-uart-idle", "stm32cube-f4"],
            reused,
        )


if __name__ == "__main__":
    unittest.main()

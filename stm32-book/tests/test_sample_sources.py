#!/usr/bin/env python3
"""License gate for the two sample chapters. The manifest is updated later."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE_LIST = ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-sample-source-list.json"
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
REJECTED = ("GPL", "LGPL", "CC BY-NC", "CC BY-ND", "All rights reserved")


class SampleSourceListTests(unittest.TestCase):
    def test_source_list_keeps_the_license_gate(self) -> None:
        payload = json.loads(SOURCE_LIST.read_text(encoding="utf-8"))
        self.assertEqual(["00", "03"], sorted(payload["chapters"]))
        self.assertEqual([], payload["community"])
        ids = [item["id"] for item in payload["absorb"]]
        self.assertEqual(["rm0008-boot", "rm0008-gpio", "ds5319-gpio"], ids)
        for item in payload["absorb"]:
            self.assertIn(item["license_class"], ALLOWED)
            self.assertTrue(item["url"].startswith("https://"))
            self.assertNotIn("http://", item["url"])
            for banned in REJECTED:
                self.assertNotIn(banned, item["license"])
            self.assertTrue(item["do_not_copy"])
            self.assertNotIn(".pdf", item["repo_path"] if "repo_path" in item else "")
        by_id = {item["id"]: item for item in payload["absorb"]}
        self.assertEqual("3.4", by_id["rm0008-boot"]["section"])
        self.assertEqual("9.2.7", by_id["rm0008-gpio"]["section"])
        self.assertEqual("note 5", by_id["ds5319-gpio"]["section"])
        self.assertEqual("project-examples", payload["reuse_existing"][0]["id"])


if __name__ == "__main__":
    unittest.main()

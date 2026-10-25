#!/usr/bin/env python3
"""License gate for chapters 01, 07, 10, and 11. The manifest is updated later."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE_LIST = ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch4-01-07-10-11-source-list.json"
LOCK = ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch4-01-07-10-11-lock.json"
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
ABSORB = [
    "ds5319-swd",
    "pm0075-rdp",
    "pm0056-vector",
    "ds5319-i2c",
    "rm0008-i2c",
    "rm0008-dma",
    "ds5319-dma",
    "rm0008-wdg",
    "rm0008-rtc",
    "ds5319-rtc",
]


class Batch4SourceListTests(unittest.TestCase):
    def test_lock_keeps_chapters_01_07_10_11(self) -> None:
        lock = json.loads(LOCK.read_text(encoding="utf-8"))
        self.assertEqual(["01", "07", "10", "11"], lock["chapters"])
        self.assertTrue(lock["four_blocks_absent"])
        self.assertTrue(lock["old_pitfall_heading_present"])
        self.assertEqual(40, len(lock["baseline"]))
        self.assertEqual("2026-10-25-classic-encyclopedia-batch4-01-07-10-11", lock["rubric"])
        for prefix, zh_name, en_name in (
            ("01", "docs/01-开发环境搭建.md", "docs/en/01-dev-environment.md"),
            ("07", "docs/07-I2C总线.md", "docs/en/07-i2c.md"),
            ("10", "docs/10-DMA.md", "docs/en/10-dma.md"),
            ("11", "docs/11-RTC与看门狗.md", "docs/en/11-rtc-watchdog.md"),
        ):
            row = lock["files"][prefix]
            self.assertEqual(zh_name, row["zh"])
            self.assertEqual(en_name, row["en"])
            self.assertFalse(row["zh_four_blocks"])
            self.assertFalse(row["en_four_blocks"])
            self.assertTrue(row["zh_old_pitfall"])
            self.assertTrue(row["en_old_pitfall"])

    def test_source_list_keeps_the_license_gate(self) -> None:
        payload = json.loads(SOURCE_LIST.read_text(encoding="utf-8"))
        self.assertEqual(["01", "07", "10", "11"], payload["chapters"])
        self.assertEqual([], payload["community"])
        ids = [item["id"] for item in payload["absorb"]]
        self.assertEqual(ABSORB, ids)
        self.assertEqual(10, len(ids))
        for item in payload["absorb"]:
            self.assertIn(item["license_class"], ALLOWED)
            self.assertTrue(item["url"].startswith("https://"))
            self.assertNotIn("http://", item["url"])
            for banned in REJECTED:
                self.assertNotIn(banned, item["license"])
                self.assertNotIn(banned, item["license_class"])
            self.assertTrue(item["do_not_copy"])
            self.assertGreaterEqual(len(item["points"]), 1)
        by_id = {item["id"]: item for item in payload["absorb"]}
        self.assertEqual("Table 5", by_id["ds5319-swd"]["section"])
        self.assertEqual("2.4.1", by_id["pm0075-rdp"]["section"])
        self.assertEqual("2.3.4", by_id["pm0056-vector"]["section"])
        self.assertEqual("Table 42", by_id["ds5319-i2c"]["section"])
        self.assertEqual("26", by_id["rm0008-i2c"]["section"])
        self.assertEqual("13", by_id["rm0008-dma"]["section"])
        self.assertEqual("2.3.13", by_id["ds5319-dma"]["section"])
        self.assertEqual("19", by_id["rm0008-wdg"]["section"])
        self.assertEqual("18", by_id["rm0008-rtc"]["section"])
        self.assertEqual("Table 25", by_id["ds5319-rtc"]["section"])
        rdp = by_id["pm0075-rdp"]["snapshot"]
        self.assertIn("0x00A5", rdp)
        self.assertIn("mass erase", rdp)
        self.assertNotIn("0xCC", rdp)
        rtc = by_id["ds5319-rtc"]["snapshot"]
        self.assertNotIn("pF", rtc)
        self.assertNotIn("ppm", rtc)
        self.assertNotIn("50%", rtc)
        i2c = by_id["rm0008-i2c"]["snapshot"]
        self.assertNotIn("0x40005400", i2c)
        dma = by_id["rm0008-dma"]["snapshot"]
        self.assertIn("chapter 13", dma)
        self.assertNotIn("chapter 10", dma)
        self.assertNotIn("21 µs", dma)
        self.assertNotIn("21 us", dma)
        wdg = by_id["rm0008-wdg"]["snapshot"]
        self.assertIn("chapters 19 and 20", wdg)
        self.assertIn("DBG_IWDG_STOP", wdg)
        self.assertIn("19.3.3", wdg)
        self.assertIn("does not record a bit number", wdg)
        self.assertNotIn("DBGMCU_CR", wdg)
        self.assertNotIn("chapter 17", wdg)
        rtc_rm = by_id["rm0008-rtc"]["snapshot"]
        self.assertIn("chapter 18", rtc_rm)
        self.assertNotIn("chapter 16", rtc_rm)
        vector = by_id["pm0056-vector"]["snapshot"]
        self.assertNotIn("167 ns", vector)
        reused = [item["id"] for item in payload["reuse_existing"]]
        self.assertEqual(["rm0008-boot", "project-examples", "rm0090"], reused)


if __name__ == "__main__":
    unittest.main()

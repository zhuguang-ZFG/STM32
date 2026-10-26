#!/usr/bin/env python3
"""License gate for chapters 16, 17, 18, and 19. The manifest is updated later."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE_LIST = ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch6-16-17-18-19-source-list.json"
LOCK = ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch6-16-17-18-19-lock.json"
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
    "ds5319-pwr",
    "rm0008-pwr",
    "pm0056-dwt",
    "ds5319-nrst",
    "ds5319-lse",
]
REUSED = [
    "rm0008-rcc",
    "rm0008-usart",
    "ds5319-usart",
    "ds5319-adc",
    "ds5319-gpio",
    "ds5319-swd",
    "ds5319-rtc",
    "rm0008-rtc",
    "rm0008-wdg",
    "pm0075-rdp",
    "pm0056",
    "rm0008-boot",
    "project-examples",
    "rm0008-adc",
    "rm0008-flash",
    "freertos-syscall",
]


class Batch6SourceListTests(unittest.TestCase):
    def test_lock_keeps_chapters_16_17_18_19(self) -> None:
        lock = json.loads(LOCK.read_text(encoding="utf-8"))
        self.assertEqual(["16", "17", "18", "19"], lock["chapters"])
        self.assertTrue(lock["four_blocks_absent"])
        self.assertTrue(lock["old_pitfall_heading_present"])
        self.assertEqual(["18", "19"], lock["chapters_without_old_pitfall"])
        self.assertEqual(40, len(lock["baseline"]))
        self.assertEqual("2026-10-25-classic-encyclopedia-batch6-16-17-18-19", lock["rubric"])
        expected = (
            ("16", "docs/16-低功耗设计.md", "docs/en/16-low-power.md", True),
            ("17", "docs/17-调试与性能优化.md", "docs/en/17-debug.md", True),
            ("18", "docs/18-常见问题FAQ.md", "docs/en/18-faq.md", False),
            ("19", "docs/19-项目实战合集.md", "docs/en/19-projects.md", False),
        )
        for prefix, zh_name, en_name, expects_old in expected:
            row = lock["files"][prefix]
            self.assertEqual(zh_name, row["zh"])
            self.assertEqual(en_name, row["en"])
            self.assertFalse(row["zh_four_blocks"])
            self.assertFalse(row["en_four_blocks"])
            self.assertEqual(expects_old, row["expects_old_pitfall"])
            self.assertEqual(expects_old, row["zh_old_pitfall"])
            self.assertEqual(expects_old, row["en_old_pitfall"])
            self.assertEqual("## ⚠️ Pitfalls and troubleshooting", row["en_old_heading"])

    def test_source_list_keeps_the_license_gate(self) -> None:
        payload = json.loads(SOURCE_LIST.read_text(encoding="utf-8"))
        self.assertEqual(["16", "17", "18", "19"], payload["chapters"])
        self.assertEqual([], payload["community"])
        ids = [item["id"] for item in payload["absorb"]]
        self.assertEqual(ABSORB, ids)
        self.assertEqual(5, len(ids))
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
        self.assertEqual("Table 16", by_id["ds5319-pwr"]["section"])
        self.assertEqual("power control", by_id["rm0008-pwr"]["section"])
        self.assertEqual("DWT", by_id["pm0056-dwt"]["section"])
        self.assertEqual("Figure 31", by_id["ds5319-nrst"]["section"])
        self.assertEqual("LSE oscillator", by_id["ds5319-lse"]["section"])
        power = by_id["ds5319-pwr"]["snapshot"]
        self.assertIn("14 µA", power)
        self.assertIn("24 µA", power)
        self.assertIn("5.4 µs", power)
        self.assertIn("14.4 mA", power)
        self.assertIn("5.5 mA", power)
        self.assertNotIn("14 to 20", power)
        self.assertNotIn("14~20", power)
        stop = by_id["rm0008-pwr"]["snapshot"]
        self.assertIn("HSI", stop)
        self.assertNotIn("HAL_RTCEx_SetWakeUpTimer_IT", stop)
        dwt = by_id["pm0056-dwt"]["snapshot"]
        self.assertIn("0xE000EDFC", dwt)
        self.assertIn("0xE0001004", dwt)
        self.assertIn("bit 24", dwt)
        self.assertNotIn("167 ns", dwt)
        nrst = by_id["ds5319-nrst"]["snapshot"]
        self.assertIn("0.1 µF", nrst)
        self.assertNotIn("30 kΩ", nrst)
        self.assertNotIn("40 kΩ", nrst)
        lse = by_id["ds5319-lse"]["snapshot"]
        self.assertIn("5 pF", lse)
        self.assertIn("15 pF", lse)
        self.assertIn("6 pF is not a required value", lse)
        reused = [item["id"] for item in payload["reuse_existing"]]
        self.assertEqual(REUSED, reused)
        self.assertNotIn("pm0056-nvic", ids)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""License gate for chapters 02, 05, 08, and 09. The manifest is updated later."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE_LIST = ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch3-02-05-08-09-source-list.json"
LOCK = ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch3-02-05-08-09-lock.json"
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
    "rm0008-rcc",
    "ds5319-clock",
    "rm0008-tim",
    "ds5319-tim",
    "rm0008-spi",
    "ds5319-spi",
    "rm0008-adc",
    "ds5319-adc",
]


class Batch3SourceListTests(unittest.TestCase):
    def test_lock_keeps_chapters_02_05_08_09(self) -> None:
        lock = json.loads(LOCK.read_text(encoding="utf-8"))
        self.assertEqual(["02", "05", "08", "09"], lock["chapters"])
        self.assertTrue(lock["four_blocks_absent"])
        self.assertTrue(lock["old_pitfall_heading_present"])
        self.assertEqual(40, len(lock["baseline"]))
        self.assertEqual("2026-10-25-classic-encyclopedia-batch3-02-05-08-09", lock["rubric"])
        for prefix, zh_name, en_name in (
            ("02", "docs/02-芯片选型与存储器时钟.md", "docs/en/02-part-and-clock.md"),
            ("05", "docs/05-定时器与PWM.md", "docs/en/05-timer-pwm.md"),
            ("08", "docs/08-SPI总线.md", "docs/en/08-spi.md"),
            ("09", "docs/09-ADC与DAC.md", "docs/en/09-adc-dac.md"),
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
        self.assertEqual(["02", "05", "08", "09"], payload["chapters"])
        self.assertEqual([], payload["community"])
        ids = [item["id"] for item in payload["absorb"]]
        self.assertEqual(ABSORB, ids)
        self.assertEqual(8, len(ids))
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
        self.assertEqual("7.3.2", by_id["rm0008-rcc"]["section"])
        self.assertEqual("Figure 8", by_id["ds5319-clock"]["section"])
        self.assertEqual("15", by_id["rm0008-tim"]["section"])
        self.assertEqual("Table 5", by_id["ds5319-tim"]["section"])
        self.assertEqual("25.5.1", by_id["rm0008-spi"]["section"])
        self.assertEqual("Table 5", by_id["ds5319-spi"]["section"])
        self.assertEqual("11.4", by_id["rm0008-adc"]["section"])
        self.assertEqual("Figure 8", by_id["ds5319-adc"]["section"])
        adc_snap = by_id["rm0008-adc"]["snapshot"]
        self.assertNotIn("pF", adc_snap)
        self.assertNotIn("kΩ", adc_snap)
        self.assertNotIn("kilohm", adc_snap.lower())
        spi_snap = by_id["rm0008-spi"]["snapshot"]
        self.assertIn("9 MHz", spi_snap)
        self.assertIn("18 MHz", spi_snap)
        self.assertIn("36 MHz", spi_snap)
        self.assertNotIn("0x40013", spi_snap)
        reused = [item["id"] for item in payload["reuse_existing"]]
        self.assertEqual(["project-examples"], reused)


if __name__ == "__main__":
    unittest.main()

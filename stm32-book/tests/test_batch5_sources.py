#!/usr/bin/env python3
"""License gate for chapters 12, 13, 14, and 15. The manifest is updated later."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE_LIST = ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch5-12-13-14-15-source-list.json"
LOCK = ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch5-12-13-14-15-lock.json"
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
    "rm0008-flash",
    "rm0008-can",
    "ds5319-usbcan",
    "rm0008-usb",
    "freertos-syscall",
]
REUSED = [
    "pm0075-rdp",
    "pm0056-vector",
    "ds5319-swd",
    "ds5319-clock",
    "rm0008-rcc",
    "ds5319-i2c",
    "project-examples",
    "rm0090",
]


class Batch5SourceListTests(unittest.TestCase):
    def test_lock_keeps_chapters_12_13_14_15(self) -> None:
        lock = json.loads(LOCK.read_text(encoding="utf-8"))
        self.assertEqual(["12", "13", "14", "15"], lock["chapters"])
        self.assertTrue(lock["four_blocks_absent"])
        self.assertTrue(lock["old_pitfall_heading_present"])
        self.assertEqual(40, len(lock["baseline"]))
        self.assertEqual("2026-10-25-classic-encyclopedia-batch5-12-13-14-15", lock["rubric"])
        expected = (
            ("12", "docs/12-Flash与IAP升级.md", "docs/en/12-flash-iap.md", "## ⚠️ Pitfalls and troubleshooting"),
            ("13", "docs/13-CAN总线.md", "docs/en/13-can.md", "## ⚠️ Pitfalls"),
            ("14", "docs/14-USB.md", "docs/en/14-usb.md", "## ⚠️ Pitfalls"),
            ("15", "docs/15-FreeRTOS入门.md", "docs/en/15-freertos.md", "## ⚠️ Pitfalls and troubleshooting"),
        )
        for prefix, zh_name, en_name, en_old in expected:
            row = lock["files"][prefix]
            self.assertEqual(zh_name, row["zh"])
            self.assertEqual(en_name, row["en"])
            self.assertFalse(row["zh_four_blocks"])
            self.assertFalse(row["en_four_blocks"])
            self.assertTrue(row["zh_old_pitfall"])
            self.assertTrue(row["en_old_pitfall"])
            self.assertEqual(en_old, row["en_old_heading"])

    def test_source_list_keeps_the_license_gate(self) -> None:
        payload = json.loads(SOURCE_LIST.read_text(encoding="utf-8"))
        self.assertEqual(["12", "13", "14", "15"], payload["chapters"])
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
        self.assertEqual("3", by_id["rm0008-flash"]["section"])
        self.assertEqual("24", by_id["rm0008-can"]["section"])
        self.assertEqual("Table 5", by_id["ds5319-usbcan"]["section"])
        self.assertEqual("23", by_id["rm0008-usb"]["section"])
        self.assertEqual("V11.3.2", by_id["freertos-syscall"]["section"])
        self.assertEqual("MIT", by_id["freertos-syscall"]["license"])
        self.assertEqual("MIT", by_id["freertos-syscall"]["license_class"])
        flash = by_id["rm0008-flash"]["snapshot"]
        self.assertIn("0x45670123", flash)
        self.assertIn("0xCDEF89AB", flash)
        self.assertIn("1 KB", flash)
        self.assertNotIn("20-40 ms", flash)
        self.assertNotIn("0xAA", flash)
        can = by_id["rm0008-can"]["snapshot"]
        self.assertIn("256", can)
        self.assertIn("128", can)
        self.assertNotIn("0x40006400", can)
        usb = by_id["rm0008-usb"]["snapshot"]
        self.assertIn("USB_LP_CAN1_RX0", usb)
        self.assertIn("48 MHz", usb)
        self.assertNotIn("480 Mbit/s is the", usb)
        pins = by_id["ds5319-usbcan"]["snapshot"]
        self.assertIn("pin 32", pins)
        self.assertIn("pin 45", pins)
        self.assertNotIn("absent", pins.lower())
        rtos = by_id["freertos-syscall"]["snapshot"]
        self.assertIn("0x50", rtos)
        self.assertNotIn("17.2", rtos)
        self.assertNotIn("167 ns", rtos)
        reused = [item["id"] for item in payload["reuse_existing"]]
        self.assertEqual(REUSED, reused)
        for banned_id in (
            "usb20",
            "freertos-priority",
            "freertos-1132",
            "an2606",
            "an3965",
            "pm0056",
            "pm0056-nvic",
        ):
            self.assertNotIn(banned_id, ids)


if __name__ == "__main__":
    unittest.main()

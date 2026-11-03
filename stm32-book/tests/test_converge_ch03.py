# -*- coding: utf-8 -*-
"""ch03 BOOK_CLASSIC_CONVERGE_SPECS §10.2 teaching-contract checks."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_FIELDS = (
    "question",
    "prerequisites",
    "minimum_victory",
    "mechanism",
    "failure_branch",
    "boundary",
    "memory_anchor",
    "exit_check",
    "deliverable",
    "sources",
)


class ConvergeCh03Tests(unittest.TestCase):
    def test_teaching_contract_fields_registered_and_aligned(self) -> None:
        zh = json.loads((ROOT / "stm32-book" / "manifest.json").read_text(encoding="utf-8"))
        en = json.loads((ROOT / "stm32-book" / "manifest-en.json").read_text(encoding="utf-8"))
        zh_g = zh["chapter_guides"]["03-GPIO与LED.md"]
        en_g = en["chapter_guides"]["03-gpio-and-led.md"]
        for guide in (zh_g, en_g):
            for field in CONTRACT_FIELDS:
                self.assertIn(field, guide, field)
                if field == "sources":
                    self.assertTrue(guide[field])
                else:
                    self.assertTrue(str(guide[field]).strip(), field)
        self.assertEqual(zh_g["sources"], en_g["sources"])
        # fact alignment smoke: both mention PC13 active-low / write 0
        self.assertIn("PC13", zh_g["minimum_victory"])
        self.assertIn("PC13", en_g["minimum_victory"])
        self.assertIn("0", zh_g["minimum_victory"])
        self.assertIn("0", en_g["minimum_victory"])

    def test_minimum_victory_precedes_handbook_density(self) -> None:
        zh = (ROOT / "docs" / "03-GPIO与LED.md").read_text(encoding="utf-8")
        en = (ROOT / "docs" / "en" / "03-gpio-and-led.md").read_text(encoding="utf-8")
        self.assertLess(zh.index("## 最小胜利"), zh.index("## 原理与适用范围"))
        self.assertLess(zh.index("## 最小胜利"), zh.index("## 核心原理"))
        self.assertLess(en.index("## Minimum victory"), en.index("## Principle and scope"))
        self.assertLess(en.index("## Minimum victory"), en.index("## Core ideas"))
        self.assertIn("ch03-handdraw.svg", zh)
        self.assertIn("ch03-handdraw.svg", en)
        self.assertIn("真证轨缺口", zh)
        self.assertIn("Evidence-track gap", en)
        self.assertIn("待补", zh)
        self.assertIn("to supply", en)


if __name__ == "__main__":
    unittest.main()

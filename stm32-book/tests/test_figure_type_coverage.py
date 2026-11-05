"""三类插图逐图机检（Overlay §15.1-23 的机器化落地）。

`figure-types.json` 登记每一张被章节正文引用的图片的知识类型
（concept / technical / triage / comparison / calculation / truth-track）。
规则：
1. 正文引用的每一张图都必须登记——新增图不登记，此测试失败；
2. 每章必须同时覆盖 concept、technical 与（triage 或 comparison）三类；
3. photos/ 下的真证照片登记为 truth-track，豁免三类覆盖，但同样必须登记。

2026-11-05：初版登记覆盖 29 章 413 张图；ch05/07/09/12/13/17 的 12 张
结构类图经人工复核归位为 concept（见登记表 review 字段）。
"""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "stm32-book" / "tests" / "fixtures" / "figure-types.json"
VALID_TYPES = {"concept", "technical", "triage", "comparison", "calculation",
               "truth-track"}


class FigureTypeCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = json.loads(REGISTRY.read_text(encoding="utf-8"))

    def referenced(self, chapter: str) -> set[str]:
        doc = next((ROOT / "docs").glob(f"{chapter}-*.md"))
        return set(re.findall(r'<img src="\.\./assets/([^"]+)"',
                              doc.read_text(encoding="utf-8")))

    def test_every_referenced_figure_is_registered(self) -> None:
        for n in range(29):
            chapter = f"{n:02d}"
            refs = self.referenced(chapter)
            unregistered = [r for r in refs if r not in self.registry]
            self.assertEqual([], unregistered, chapter)

    def test_registry_types_are_valid(self) -> None:
        for name, entry in self.registry.items():
            self.assertIn(entry["type"], VALID_TYPES, name)

    def test_every_chapter_covers_three_figure_kinds(self) -> None:
        for n in range(29):
            chapter = f"{n:02d}"
            refs = self.referenced(chapter)
            types = {self.registry[r]["type"] for r in refs}
            missing = []
            if "concept" not in types:
                missing.append("concept")
            if "technical" not in types:
                missing.append("technical")
            if not {"triage", "comparison"} & types:
                missing.append("triage/comparison")
            self.assertEqual([], missing, (chapter, sorted(types)))


if __name__ == "__main__":
    unittest.main()

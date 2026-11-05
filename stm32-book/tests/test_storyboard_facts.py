"""storyboard fact-source 锚点校验（ch21–28 自编长课分镜）。

Batch G 的八份 storyboard 里 fact_source 引用了 `docs/<文件>#<锚点>`；
本测试断言：文档存在、锚点字符串出现在文档正文中（锚点即章节标题或
正文片段，无需是严格链接目标），防止后续章节重构时证据指针悄悄失效。
"""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROLES = {"hook", "mechanism", "failure", "experiment", "recall"}
CHAPTERS = ["21", "22", "23", "24", "25", "26", "27", "28"]


class StoryboardFactsTests(unittest.TestCase):
    def load(self, chapter: str) -> dict:
        path = ROOT / "video" / f"ch{chapter}" / "storyboard.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def test_every_scene_has_28_counts_and_five_roles(self) -> None:
        for chapter in CHAPTERS:
            data = self.load(chapter)
            scenes = data["scenes"]
            self.assertEqual(28, len(scenes), chapter)
            roles = {scene["purpose"] for scene in scenes}
            self.assertEqual(ROLES, roles, chapter)
            ids = [scene["scene_id"] for scene in scenes]
            self.assertEqual(
                [f"ch{chapter}-s{n:02d}" for n in range(1, 29)], ids, chapter
            )

    def test_fact_source_doc_anchors_exist(self) -> None:
        checked = 0
        for chapter in CHAPTERS:
            data = self.load(chapter)
            for scene in data["scenes"]:
                for fact in scene["fact_source"]:
                    if not fact.startswith("docs/"):
                        continue
                    rel, _, anchor = fact.partition("#")
                    doc = ROOT / rel
                    self.assertTrue(doc.is_file(), fact)
                    if anchor:
                        text = doc.read_text(encoding="utf-8")
                        self.assertIn(anchor, text, fact)
                        checked += 1
        self.assertGreater(checked, 50)

    def test_visual_sources_exist(self) -> None:
        for chapter in CHAPTERS:
            data = self.load(chapter)
            for scene in data["scenes"]:
                rel = scene["visual_source"]
                if rel:
                    self.assertTrue((ROOT / "assets" / rel).is_file(),
                                    (chapter, rel))


if __name__ == "__main__":
    unittest.main()

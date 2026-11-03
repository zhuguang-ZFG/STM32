from __future__ import annotations

import importlib.util
import unittest
from collections import Counter
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
CHAPTERS = {11: "11", 12: "12", 13: "13", 14: "14", 15: "15"}
ROLES = {"hook", "mechanism", "failure", "experiment", "recall"}
ROLE_COUNTS = Counter({"hook": 1, "mechanism": 18, "failure": 5, "experiment": 2, "recall": 2})


def load_tool(name: str):
    path = REPO / "tools" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"classic_l4_{name}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ClassicL4Tests(unittest.TestCase):
    def test_l4_storyboards_are_complete_and_use_local_visuals(self) -> None:
        storyboards = load_tool("storyboards")
        for index, chapter in CHAPTERS.items():
            with self.subTest(chapter=chapter):
                board = storyboards.load(chapter)
                scenes = board["segments"]
                self.assertEqual(28, len(scenes))
                self.assertEqual(ROLES, {scene["purpose"] for scene in scenes})
                self.assertEqual(ROLE_COUNTS, Counter(scene["purpose"] for scene in scenes))
                self.assertEqual(f"tools/narration.py#CHAPTERS[{index}]", board["short_source"])
                self.assertEqual([f"ch{chapter}-s{i:02d}" for i in range(1, 29)], [s["scene_id"] for s in scenes])
                for scene in scenes:
                    visual = scene["visual_source"]
                    if visual:
                        self.assertTrue((REPO / "assets" / visual).is_file(), (chapter, visual))

    def test_l4_shorts_have_exactly_ten_dedicated_visuals(self) -> None:
        narration = load_tool("narration")
        for index, chapter_id in CHAPTERS.items():
            with self.subTest(chapter=chapter_id):
                segments = narration.CHAPTERS[index]["segments"]
                paths = [seg.get("svg") for seg in segments if isinstance(seg.get("svg"), str)]
                self.assertEqual(10, len(paths), chapter_id)
                self.assertEqual(10, len(set(paths)), (chapter_id, len(set(paths))))
                for visual in set(paths):
                    self.assertTrue((REPO / "assets" / visual).is_file(), (chapter_id, visual))

    def test_l4_storyboards_use_all_ten_short_visuals(self) -> None:
        narration = load_tool("narration")
        storyboards = load_tool("storyboards")
        for index, chapter in CHAPTERS.items():
            with self.subTest(chapter=chapter):
                whitelist = set(narration.SHORT_VISUALS[str(index)])
                used = {
                    scene["visual_source"]
                    for scene in storyboards.load(chapter)["segments"]
                    if scene["visual_source"]
                }
                self.assertEqual(10, len(whitelist))
                self.assertEqual(
                    whitelist,
                    used,
                    (chapter, sorted(whitelist - used), sorted(used - whitelist)),
                )

    def test_l4_short_visuals_are_not_generic_placeholders(self) -> None:
        narration = load_tool("narration")
        required = {
            "11": "diagrams/sample-11-iwdg-1s.svg",
            "12": "diagrams/sample-12-iap-map.svg",
            "13": "diagrams/sample-13-can-bit.svg",
            "14": "diagrams/sample-14-usb-enum.svg",
            "15": "diagrams/sample-15-rtos-prio.svg",
        }
        for index, chapter_id in CHAPTERS.items():
            with self.subTest(chapter=chapter_id):
                paths = {seg.get("svg") for seg in narration.CHAPTERS[index]["segments"]}
                self.assertIn(required[chapter_id], paths)


if __name__ == "__main__":
    unittest.main()

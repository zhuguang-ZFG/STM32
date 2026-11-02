from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
CHAPTERS = {0: "00", 1: "01", 2: "02", 4: "04", 5: "05"}
ROLES = {"hook", "mechanism", "failure", "experiment", "recall"}


def load_tool(name: str):
    path = REPO / "tools" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"classic_l2_{name}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ClassicL2Tests(unittest.TestCase):
    def test_l2_storyboards_are_complete_and_use_local_visuals(self) -> None:
        storyboards = load_tool("storyboards")
        for index, chapter in CHAPTERS.items():
            with self.subTest(chapter=chapter):
                board = storyboards.load(chapter)
                scenes = board["segments"]
                self.assertEqual(28, len(scenes))
                self.assertEqual(ROLES, {scene["purpose"] for scene in scenes})
                self.assertEqual(f"tools/narration.py#CHAPTERS[{index}]", board["short_source"])
                self.assertEqual([f"ch{chapter}-s{i:02d}" for i in range(1, 29)], [s["scene_id"] for s in scenes])
                for scene in scenes:
                    visual = scene["visual_source"]
                    if visual:
                        self.assertTrue((REPO / "assets" / visual).is_file(), (chapter, visual))
                    self.assertNotEqual("illustrations/ch03-handdraw.svg", visual)

    def test_l2_shorts_have_at_least_eight_dedicated_visuals(self) -> None:
        narration = load_tool("narration")
        for index, chapter_id in CHAPTERS.items():
            with self.subTest(chapter=chapter_id):
                chapter = narration.CHAPTERS[index]
                self.assertGreaterEqual(sum(bool(seg.get("svg")) for seg in chapter["segments"]), 8)

    def test_l2_short_visuals_are_not_generic_placeholders(self) -> None:
        narration = load_tool("narration")
        required = {
            "00": "diagrams/first-success-gates.svg",
            "01": "diagrams/sample-01-swd-vectors.svg",
            "02": "diagrams/sample-02-clock-tree.svg",
            "04": "diagrams/interrupt-priority.svg",
            "05": "diagrams/sample-05-pwm-1khz.svg",
        }
        for index, chapter_id in CHAPTERS.items():
            with self.subTest(chapter=chapter_id):
                paths = {seg.get("svg") for seg in narration.CHAPTERS[index]["segments"]}
                self.assertIn(required[chapter_id], paths)


if __name__ == "__main__":
    unittest.main()

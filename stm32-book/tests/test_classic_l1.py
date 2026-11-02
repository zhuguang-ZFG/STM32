from __future__ import annotations

import importlib.util
import struct
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]


def load_tool(name: str):
    path = REPO / "tools" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"classic_l1_{name}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ClassicL1VisualTests(unittest.TestCase):
    def test_gpio_plate_shows_both_electrical_states(self) -> None:
        raw = (REPO / "assets" / "illustrations" / "ch03-handdraw.svg").read_text(
            encoding="utf-8"
        )
        self.assertIn("CH 04", raw)
        self.assertIn("写 1 · 灯灭", raw)
        self.assertIn("写 0 · 灯亮", raw)
        self.assertIn("共阳接法", raw)

    def test_beat_specific_visual_is_not_overwritten(self) -> None:
        narration = load_tool("narration")
        chapter = narration.ch(
            "03",
            "gpio",
            "GPIO 与 LED",
            "animations/gpio-blink.svg",
            [
                narration.b("默认", ["默认动画"], "默认动画。", svg=True),
                narration.b(
                    "专属",
                    ["专属视觉"],
                    "专属视觉。",
                    svg="diagrams/stack-gpio-pc13-led.png",
                ),
            ],
        )
        self.assertEqual("animations/gpio-blink.svg", chapter["segments"][0]["svg"])
        self.assertEqual(
            "diagrams/stack-gpio-pc13-led.png", chapter["segments"][1]["svg"]
        )

    def test_png_storyboard_visual_loads_without_chrome(self) -> None:
        generator = load_tool("gen_narrated")
        image = generator._visual_png("video/ch03-gpio.png")
        self.assertEqual((1920, 1080), image.size)

    def test_ch03_short_storyboard_leads_with_the_active_low_mechanism(self) -> None:
        narration = load_tool("narration")
        chapter = narration.CHAPTERS[3]
        segments = chapter["segments"]
        self.assertEqual(10, len(segments))
        self.assertEqual("illustrations/ch03-handdraw.svg", segments[0]["svg"])
        self.assertEqual("diagrams/stack-gpio-pc13-led.png", segments[1]["svg"])
        self.assertGreaterEqual(8, sum(bool(seg.get("svg")) for seg in segments))
        self.assertIn("写 1", segments[0]["say"])
        self.assertIn("不是实测", segments[1]["say"])

    def test_long_storyboard_is_complete_and_covers_five_learning_roles(self) -> None:
        storyboards = load_tool("storyboards")
        board = storyboards.load("03")
        scenes = board["segments"]
        self.assertEqual(28, len(scenes))
        required = {
            "scene_id", "purpose", "prerequisite", "narration", "on_screen",
            "visual_source", "fact_source", "start", "duration", "memory_anchor",
            "evidence_type", "subtitle_ref",
        }
        for index, scene in enumerate(scenes, 1):
            self.assertFalse(required - scene.keys(), (index, required - scene.keys()))
            self.assertEqual(f"ch03.srt#{index:02d}", scene["subtitle_ref"])
            self.assertGreater(scene["duration"], 0)
        self.assertEqual(
            {"hook", "mechanism", "failure", "experiment", "recall"},
            {scene["purpose"] for scene in scenes},
        )
        starts = [scene["start"] for scene in scenes]
        self.assertEqual(sorted(starts), starts)

    def test_three_keyframe_split_preserves_duration_boundaries(self) -> None:
        storyboards = load_tool("storyboards")
        for duration in (0.5, 4.0, 12.0, 31.75):
            parts = storyboards.keyframe_durations(duration)
            self.assertEqual(3, len(parts))
            self.assertTrue(all(part > 0 for part in parts))
            self.assertAlmostEqual(duration, sum(parts))

    def test_stack_boundary_asset_is_complete(self) -> None:
        diagram = REPO / "assets" / "diagrams" / "stack-gpio-pc13-led.html"
        self.assertTrue(diagram.is_file(), diagram)
        html = diagram.read_text(encoding="utf-8")
        for label in ("写 1 灯灭，写 0 灯亮", "共阳 LED", "PC13 输出级", "电流（写 0 时）"):
            self.assertIn(label, html)
        self.assertNotIn("%%ICON_", html)
        for name in ("stack-gpio-pc13-led.png", "stack-gpio-pc13-led-dark.png"):
            raw = (REPO / "assets" / "diagrams" / name).read_bytes()
            self.assertEqual(b"\x89PNG\r\n\x1a\n", raw[:8])
            self.assertEqual((2000, 1200), struct.unpack(">II", raw[16:24]))

    def test_stack_boundary_is_linked_once_in_both_languages(self) -> None:
        for name in ("docs/03-GPIO与LED.md", "docs/en/03-gpio-and-led.md"):
            text = (REPO / name).read_text(encoding="utf-8")
            self.assertEqual(1, text.count("diagrams/stack-gpio-pc13-led.png"), name)


if __name__ == "__main__":
    unittest.main()

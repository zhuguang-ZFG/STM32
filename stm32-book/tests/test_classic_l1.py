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
        self.assertEqual((960, 540), image.size)

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

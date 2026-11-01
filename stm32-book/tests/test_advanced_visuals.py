from __future__ import annotations

import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


CHAPTERS = {
    ROOT / "docs" / "26-STM32F10x标准外设库SPL.md": (
        5,
        (
            "spl-ownership-boundary.svg",
            "spl-init-pipeline.svg",
            "bluepill-stm32f103c8t6.svg",
            "nvic-interrupt-flow.svg",
            "dma-circular.svg",
        ),
    ),
    ROOT / "docs" / "27-网络与协议栈.md": (
        5,
        (
            "network-packet-journey.svg",
            "network-cache-ownership.svg",
            "network-online-state.svg",
            "tcp-byte-stream.svg",
            "network-debug-ladder.svg",
        ),
    ),
    ROOT / "docs" / "28-嵌入式系统与RTOS生态.md": (
        8,
        (
            "rtos-system-layers.svg",
            "nucleo-f411re-embedded-world.jpg",
            "nucleo-f401re-embedded-world.jpg",
            "rtos-owner-task.svg",
            "rtos-deadline-budget.svg",
            "freertos-scheduler.svg",
            "rtos-config-paths.svg",
            "rtos-startup-gates.svg",
        ),
    ),
}


class AdvancedVisualTests(unittest.TestCase):
    def test_visual_anchors_are_present_and_distributed(self) -> None:
        for path, (count, assets) in CHAPTERS.items():
            text = path.read_text(encoding="utf-8")
            positions = [match.start() for match in re.finditer(r"<img\b", text)]
            self.assertEqual(count, len(positions), path.name)
            for asset in assets:
                self.assertEqual(1, text.count(asset), (path.name, asset))

            points = [0, *positions, len(text)]
            largest_gap = max(right - left for left, right in zip(points, points[1:]))
            self.assertLessEqual(largest_gap, 5500, (path.name, largest_gap))

    def test_english_chapters_keep_the_same_visual_sequence(self) -> None:
        pairs = (
            ("26-STM32F10x标准外设库SPL.md", "26-spl.md"),
            ("27-网络与协议栈.md", "27-network.md"),
            ("28-嵌入式系统与RTOS生态.md", "28-system-rtos.md"),
        )
        for zh_name, en_name in pairs:
            zh = (ROOT / "docs" / zh_name).read_text(encoding="utf-8")
            en = (ROOT / "docs" / "en" / en_name).read_text(encoding="utf-8")
            zh_assets = [Path(item).name for item in re.findall(r'<img\b[^>]*src="([^"]+)"', zh)]
            en_assets = [Path(item).name for item in re.findall(r'<img\b[^>]*src="([^"]+)"', en)]
            self.assertEqual(zh_assets, en_assets, zh_name)

    def test_new_svg_assets_are_valid_and_use_recorded_handdraw_ids(self) -> None:
        animated = (
            "spl-init-pipeline.svg",
            "network-online-state.svg",
            "rtos-startup-gates.svg",
        )
        static = (
            "spl-ownership-boundary.svg",
            "network-cache-ownership.svg",
            "tcp-byte-stream.svg",
            "rtos-owner-task.svg",
            "rtos-deadline-budget.svg",
            "rtos-config-paths.svg",
        )
        for name in animated:
            path = ROOT / "assets" / "animations" / name
            ET.parse(path)
            text = path.read_text(encoding="utf-8")
            self.assertIn("animation:", text, name)
            self.assertIn("prefers-reduced-motion", text, name)
            self.assertIn("FA-002", text, name)

        for name in static:
            path = ROOT / "assets" / "diagrams" / name
            ET.parse(path)
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("animation:", text, name)
            self.assertIn("自绘矢量图", text, name)
            self.assertRegex(text, r"FA-(?:002|029)")

        readme = (ROOT / "assets" / "README.md").read_text(encoding="utf-8")
        for token in (
            "FA-002",
            "FA-029",
            "IG-004",
            "IG-008",
            "IG-009",
            "IG-011",
            "IG-012",
            "C-03",
            "C-10",
            "C-27",
            "C-31",
        ):
            self.assertIn(token, readme)

    def test_photo_spread_is_honest_about_exact_models(self) -> None:
        for path in (
            ROOT / "docs" / "28-嵌入式系统与RTOS生态.md",
            ROOT / "docs" / "en" / "28-system-rtos.md",
        ):
            text = path.read_text(encoding="utf-8")
            self.assertIn('class="photo-pair"', text)
            self.assertIn("Nucleo-F411RE", text)
            self.assertIn("Nucleo-F401RE", text)
            self.assertIn("assets/photos/README.md", text)

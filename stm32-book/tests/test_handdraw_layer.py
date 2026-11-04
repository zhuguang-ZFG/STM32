from __future__ import annotations

import importlib.util
import json
import re
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


BOOK_DIR = Path(__file__).resolve().parents[1]
REPO = BOOK_DIR.parent
BUILD_PATH = BOOK_DIR / "build_html.py"


def load_builder():
    spec = importlib.util.spec_from_file_location("stm32_book_builder", BUILD_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load builder: {BUILD_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class HanddrawLayerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.builder = load_builder()
        cls.entries = cls.builder.load_handdraw_manifest()

    def test_manifest_covers_every_chapter_in_order(self) -> None:
        self.assertEqual([f"{index:02d}" for index in range(29)], list(self.entries))
        for chapter, entry in self.entries.items():
            self.assertEqual(f"ch{chapter}-handdraw.svg", entry["file"])
            for key in ("zh", "en"):
                self.assertTrue(entry[key].strip(), (chapter, key))
            path = self.builder.HANDDRAW_DIR / entry["file"]
            self.assertTrue(path.is_file(), path)
            self.assertLessEqual(
                path.stat().st_size, self.builder.HANDDRAW_MAX_BYTES, path
            )

    def test_plates_are_safe_animated_and_distinct(self) -> None:
        titles: set[str] = set()
        drawings: set[str] = set()
        for chapter, entry in self.entries.items():
            path = self.builder.HANDDRAW_DIR / entry["file"]
            raw = path.read_bytes()
            text = raw.decode("utf-8")
            ET.parse(path)
            self.assertIn('width="900"', text, chapter)
            self.assertIn('height="560"', text, chapter)
            self.assertIn('viewBox="0 0 900 560"', text, chapter)
            self.assertIn("FA-002", text, chapter)
            self.assertIn("@keyframes", text, chapter)
            self.assertIn("prefers-reduced-motion", text, chapter)
            self.assertIn("自绘矢量动画", text, chapter)
            for banned in (
                "<script",
                "<image",
                "<foreignObject",
                "<filter",
                "url(",
                "href=",
            ):
                self.assertNotIn(banned, text, (chapter, banned))
            titles.add(entry["en"])
            drawings.add(text)
        self.assertEqual(29, len(titles))
        self.assertEqual(29, len(drawings))

    def test_screen_css_keeps_plates_out_of_the_figure_card(self) -> None:
        screen = self.builder.CSS.split("@media", 1)[0]
        plate = re.search(r"\.chapter-plate\s*\{([^}]*)\}", screen)
        self.assertIsNotNone(plate)
        self.assertIn("border: 0", plate.group(1))
        self.assertIn("box-shadow: none", plate.group(1))
        image = re.search(r"\.chapter-plate img\s*\{([^}]*)\}", screen)
        self.assertIsNotNone(image)
        self.assertIn("max-width: min(100%, 820px)", image.group(1))

    def test_build_inlines_one_localized_plate_per_chapter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = self.builder.build_html(Path(tmp))
            html = output.read_text(encoding="utf-8")

        self.assertEqual(29, html.count('class="chapter-plate"'))
        self.assertEqual(
            29,
            len(
                re.findall(
                    r'<figure class="chapter-plate">\s*'
                    r'<img src="data:image/svg\+xml;base64,',
                    html,
                )
            ),
        )
        self.assertEqual(29, html.count('alt="手绘概念图：'))
        self.assertEqual(29, html.count("▲ 手绘概念图："))
        self.assertNotIn("Hand-drawn concept:", html)
        self.assertNotIn('src="../assets/illustrations', html)

        start = html.index('id="chapter-00"')
        end = html.index('id="chapter-01"')
        section = html[start:end]
        compass = section.index('class="chapter-compass"')
        plate = section.index('class="chapter-plate"')
        self.assertLess(compass, plate)
        self.assertLess(plate, section.index("<h2"))
        self.assertLess(plate, section.index("<blockquote"))

    def test_english_build_uses_english_plate_captions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = self.builder.build_html(
                Path(tmp), manifest_path=BOOK_DIR / "manifest-en.json"
            )
            html = output.read_text(encoding="utf-8")

        self.assertEqual(29, html.count('class="chapter-plate"'))
        self.assertEqual(29, html.count('alt="Hand-drawn concept:'))
        self.assertEqual(29, html.count("▲ Hand-drawn concept:"))
        self.assertNotIn('alt="手绘概念图：', html)
        self.assertNotIn("▲ 手绘概念图：", html)

    def test_missing_or_incomplete_manifest_is_a_build_error(self) -> None:
        manifest = json.loads(
            (self.builder.HANDDRAW_MANIFEST).read_text(encoding="utf-8")
        )
        original_dir = self.builder.HANDDRAW_DIR
        original_manifest = self.builder.HANDDRAW_MANIFEST
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.builder.HANDDRAW_DIR = root
            self.builder.HANDDRAW_MANIFEST = root / "manifest.json"
            try:
                with self.assertRaises(self.builder.BuildError):
                    self.builder.load_handdraw_manifest()

                (root / "manifest.json").write_text(
                    json.dumps(manifest), encoding="utf-8", newline="\n"
                )
                with self.assertRaises(self.builder.BuildError):
                    self.builder.load_handdraw_manifest()

                (root / "ch00-handdraw.svg").write_text(
                    (original_dir / "ch00-handdraw.svg").read_text(encoding="utf-8"),
                    encoding="utf-8",
                    newline="\n",
                )
                with self.assertRaises(self.builder.BuildError):
                    self.builder.load_handdraw_manifest()
            finally:
                self.builder.HANDDRAW_DIR = original_dir
                self.builder.HANDDRAW_MANIFEST = original_manifest

    def test_manifest_with_a_short_inventory_is_a_build_error(self) -> None:
        manifest = json.loads(
            (self.builder.HANDDRAW_MANIFEST).read_text(encoding="utf-8")
        )
        manifest["files"] = manifest["files"][:-1]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            path.write_text(json.dumps(manifest), encoding="utf-8", newline="\n")
            original = self.builder.HANDDRAW_MANIFEST
            self.builder.HANDDRAW_MANIFEST = path
            try:
                with self.assertRaises(self.builder.BuildError):
                    self.builder.load_handdraw_manifest()
            finally:
                self.builder.HANDDRAW_MANIFEST = original


class PartHanddrawTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.builder = load_builder()
        cls.parts = cls.builder.load_handdraw_parts()

    def test_manifest_covers_every_part_in_order(self) -> None:
        self.assertEqual([f"p{index}" for index in range(7)], list(self.parts))
        for part_id, entry in self.parts.items():
            self.assertEqual(f"part-{part_id}-handdraw.svg", entry["file"])
            for key in ("zh", "en"):
                self.assertTrue(entry[key].strip(), (part_id, key))
            path = self.builder.HANDDRAW_DIR / entry["file"]
            self.assertTrue(path.is_file(), path)
            self.assertLessEqual(
                path.stat().st_size, self.builder.HANDDRAW_MAX_BYTES, path
            )

    def test_part_plates_are_safe_animated_and_distinct(self) -> None:
        drawings: set[str] = set()
        for part_id, entry in self.parts.items():
            path = self.builder.HANDDRAW_DIR / entry["file"]
            text = path.read_text(encoding="utf-8")
            ET.parse(path)
            self.assertIn('width="900"', text, part_id)
            self.assertIn('viewBox="0 0 900 560"', text, part_id)
            self.assertIn("FA-002", text, part_id)
            self.assertIn("prefers-reduced-motion", text, part_id)
            self.assertIn("自绘矢量动画", text, part_id)
            for banned in ("<script", "<image", "<foreignObject", "<filter",
                           "url(", "href="):
                self.assertNotIn(banned, text, (part_id, banned))
            drawings.add(text)
        self.assertEqual(7, len(drawings))

    def test_build_inlines_one_localized_plate_per_part(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            html = self.builder.build_html(Path(tmp)).read_text(encoding="utf-8")
        self.assertEqual(7, html.count('class="part-plate"'))
        self.assertEqual(
            7,
            len(re.findall(
                r'<figure class="part-plate">\s*'
                r'<img src="data:image/svg\+xml;base64,',
                html,
            )),
        )
        self.assertEqual(7, html.count('alt="分部概念图：'))
        self.assertEqual(7, html.count("▲ 分部概念图："))
        section = html[html.index('id="part-p0"'):html.index('id="chapter-00"')]
        self.assertLess(section.index('class="part-goal"'),
                        section.index('class="part-plate"'))

    def test_english_build_uses_english_part_captions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            html = self.builder.build_html(
                Path(tmp), manifest_path=BOOK_DIR / "manifest-en.json"
            ).read_text(encoding="utf-8")
        self.assertEqual(7, html.count('class="part-plate"'))
        self.assertEqual(7, html.count('alt="Part concept:'))
        self.assertNotIn('alt="分部概念图：', html)

    def test_missing_part_inventory_is_a_build_error(self) -> None:
        manifest = json.loads(
            (self.builder.HANDDRAW_MANIFEST).read_text(encoding="utf-8")
        )
        manifest.pop("parts", None)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            path.write_text(json.dumps(manifest), encoding="utf-8", newline="\n")
            original = self.builder.HANDDRAW_MANIFEST
            self.builder.HANDDRAW_MANIFEST = path
            try:
                with self.assertRaises(self.builder.BuildError):
                    self.builder.load_handdraw_parts()
            finally:
                self.builder.HANDDRAW_MANIFEST = original


class MidHanddrawTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.builder = load_builder()
        cls.entries = cls.builder.load_handdraw_mid()

    def test_manifest_covers_every_chapter_in_order(self) -> None:
        self.assertEqual([f"{index:02d}" for index in range(29)], list(self.entries))
        for chapter, entry in self.entries.items():
            self.assertEqual(f"ch{chapter}-mid-handdraw.svg", entry["file"])
            for key in ("zh", "en", "anchor_zh", "anchor_en"):
                self.assertTrue(entry[key].strip(), (chapter, key))
            path = self.builder.HANDDRAW_DIR / entry["file"]
            self.assertTrue(path.is_file(), path)
            self.assertLessEqual(
                path.stat().st_size, self.builder.HANDDRAW_MAX_BYTES, path
            )

    def test_mid_plates_are_safe_animated_and_distinct(self) -> None:
        titles: set[str] = set()
        drawings: set[str] = set()
        for chapter, entry in self.entries.items():
            path = self.builder.HANDDRAW_DIR / entry["file"]
            text = path.read_text(encoding="utf-8")
            ET.parse(path)
            self.assertIn('width="900"', text, chapter)
            self.assertIn('viewBox="0 0 900 560"', text, chapter)
            self.assertIn("FA-002", text, chapter)
            self.assertIn("prefers-reduced-motion", text, chapter)
            self.assertIn("自绘矢量动画", text, chapter)
            for banned in ("<script", "<image", "<foreignObject", "<filter",
                           "url(", "href="):
                self.assertNotIn(banned, text, (chapter, banned))
            titles.add(entry["en"])
            drawings.add(text)
        self.assertEqual(29, len(titles))
        self.assertEqual(29, len(drawings))

    def test_build_inlines_one_plate_after_each_anchor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            html = self.builder.build_html(Path(tmp)).read_text(encoding="utf-8")
        self.assertEqual(29, html.count('class="mid-plate"'))
        self.assertEqual(
            29,
            len(re.findall(
                r'<figure class="mid-plate">\s*'
                r'<img src="data:image/svg\+xml;base64,',
                html,
            )),
        )
        self.assertEqual(29, html.count('alt="本节概念图：'))
        self.assertEqual(29, html.count("▲ 本节概念图："))
        for chapter, entry in self.entries.items():
            start = html.index(f'id="chapter-{chapter}"')
            end = html.find('id="chapter-', start + 10)
            if end < 0:
                end = html.index('class="part-closing"', start)
            section = html[start:end]
            self.assertEqual(1, section.count('class="mid-plate"'), chapter)
            heading = f'>{entry["anchor_zh"]}</h2>'
            self.assertIn(heading, section, chapter)
            self.assertLess(
                section.index(heading), section.index('class="mid-plate"'), chapter
            )

    def test_english_build_uses_english_mid_captions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            html = self.builder.build_html(
                Path(tmp), manifest_path=BOOK_DIR / "manifest-en.json"
            ).read_text(encoding="utf-8")
        self.assertEqual(29, html.count('class="mid-plate"'))
        self.assertEqual(29, html.count('alt="Section concept:'))
        self.assertNotIn('alt="本节概念图：', html)
        for chapter, entry in self.entries.items():
            start = html.index(f'id="chapter-{chapter}"')
            end = html.find('id="chapter-', start + 10)
            if end < 0:
                end = html.index('class="part-closing"', start)
            section = html[start:end]
            heading = f'>{entry["anchor_en"]}</h2>'
            self.assertIn(heading, section, chapter)
            self.assertLess(
                section.index(heading), section.index('class="mid-plate"'), chapter
            )

    def test_missing_mid_inventory_is_a_build_error(self) -> None:
        manifest = json.loads(
            (self.builder.HANDDRAW_MANIFEST).read_text(encoding="utf-8")
        )
        manifest.pop("mid", None)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            path.write_text(json.dumps(manifest), encoding="utf-8", newline="\n")
            original = self.builder.HANDDRAW_MANIFEST
            self.builder.HANDDRAW_MANIFEST = path
            try:
                with self.assertRaises(self.builder.BuildError):
                    self.builder.load_handdraw_mid()
            finally:
                self.builder.HANDDRAW_MANIFEST = original

    def test_wrong_anchor_is_a_build_error(self) -> None:
        entry = next(iter(self.entries.values()))
        broken = dict(entry, anchor_zh="不存在的锚点标题")
        with self.assertRaises(self.builder.BuildError):
            self.builder.inject_mid_plate(
                "<h2 id=\"ch00-_1\">核心原理</h2>", broken, "zh", {"language": "zh-CN"}
            )


class AppendixHanddrawTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.builder = load_builder()
        cls.entries = cls.builder.load_handdraw_appendices()

    def test_manifest_covers_every_appendix_in_order(self) -> None:
        self.assertEqual(
            ["appendix-engineering", "appendix-examples", "appendix-exercises",
             "appendix-glossary", "appendix-references", "appendix-oss-map"],
            list(self.entries),
        )
        for index, (appendix_id, entry) in enumerate(self.entries.items()):
            letter = chr(ord("a") + index)
            self.assertEqual(f"app-{letter}-handdraw.svg", entry["file"])
            for key in ("zh", "en"):
                self.assertTrue(entry[key].strip(), (appendix_id, key))
            path = self.builder.HANDDRAW_DIR / entry["file"]
            self.assertTrue(path.is_file(), path)
            self.assertLessEqual(
                path.stat().st_size, self.builder.HANDDRAW_MAX_BYTES, path
            )

    def test_appendix_plates_are_safe_animated_and_distinct(self) -> None:
        titles: set[str] = set()
        drawings: set[str] = set()
        for appendix_id, entry in self.entries.items():
            path = self.builder.HANDDRAW_DIR / entry["file"]
            text = path.read_text(encoding="utf-8")
            ET.parse(path)
            self.assertIn('width="900"', text, appendix_id)
            self.assertIn('viewBox="0 0 900 560"', text, appendix_id)
            self.assertIn("FA-002", text, appendix_id)
            self.assertIn("prefers-reduced-motion", text, appendix_id)
            self.assertIn("自绘矢量动画", text, appendix_id)
            for banned in ("<script", "<image", "<foreignObject", "<filter",
                           "url(", "href="):
                self.assertNotIn(banned, text, (appendix_id, banned))
            titles.add(entry["en"])
            drawings.add(text)
        self.assertEqual(6, len(titles))
        self.assertEqual(6, len(drawings))

    def test_build_inlines_one_plate_per_appendix(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            html = self.builder.build_html(Path(tmp)).read_text(encoding="utf-8")
        self.assertEqual(6, html.count('class="appendix-plate"'))
        self.assertEqual(
            6,
            len(re.findall(
                r'<figure class="appendix-plate">\s*'
                r'<img src="data:image/svg\+xml;base64,',
                html,
            )),
        )
        self.assertEqual(6, html.count('alt="附录概念图：'))
        for appendix_id in self.entries:
            section = html[html.index(f'id="{appendix_id}"'):]
            self.assertLess(
                section.index('</header>'), section.index('class="appendix-plate"'),
                appendix_id,
            )

    def test_english_build_inlines_all_six_appendices_including_oss_map(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            html = self.builder.build_html(
                Path(tmp), manifest_path=BOOK_DIR / "manifest-en.json"
            ).read_text(encoding="utf-8")
        self.assertEqual(6, html.count('class="appendix-plate"'))
        self.assertEqual(6, html.count('alt="Appendix concept:'))
        self.assertNotIn('alt="附录概念图：', html)
        self.assertIn('id="appendix-oss-map"', html)

    def test_missing_appendix_inventory_is_a_build_error(self) -> None:
        manifest = json.loads(
            (self.builder.HANDDRAW_MANIFEST).read_text(encoding="utf-8")
        )
        manifest.pop("appendices", None)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            path.write_text(json.dumps(manifest), encoding="utf-8", newline="\n")
            original = self.builder.HANDDRAW_MANIFEST
            self.builder.HANDDRAW_MANIFEST = path
            try:
                with self.assertRaises(self.builder.BuildError):
                    self.builder.load_handdraw_appendices()
            finally:
                self.builder.HANDDRAW_MANIFEST = original

    def test_appendix_without_plate_is_a_build_error(self) -> None:
        original = self.builder.load_handdraw_appendices
        trimmed = {k: v for k, v in self.entries.items() if k != "appendix-oss-map"}
        self.builder.load_handdraw_appendices = lambda: trimmed
        try:
            with tempfile.TemporaryDirectory() as tmp:
                with self.assertRaises(self.builder.BuildError):
                    self.builder.build_html(Path(tmp))
        finally:
            self.builder.load_handdraw_appendices = original


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import copy
import importlib.util
import json
import re
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path


BOOK_DIR = Path(__file__).resolve().parents[1]
BUILD_PATH = BOOK_DIR / "build_html.py"


def load_builder():
    spec = importlib.util.spec_from_file_location("mcu_book_builder", BUILD_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load builder: {BUILD_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BookHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.hrefs: list[str] = []
        self.image_sources: list[str] = []
        self.chapter_numbers: list[str] = []
        self.compasses = 0
        self.appendices: set[str] = set()
        self.quiz_groups = 0
        self.has_viewport = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        classes = (values.get("class") or "").split()
        element_id = values.get("id")
        if element_id:
            self.ids.add(element_id)
        if tag == "article" and "appendix" in classes:
            self.appendices.add(element_id)
        if tag == "a" and values.get("href"):
            self.hrefs.append(values["href"] or "")
        if tag == "img" and values.get("src"):
            self.image_sources.append(values["src"] or "")
        if tag == "article" and "chapter" in classes:
            chapter = values.get("data-chapter")
            if chapter is not None:
                self.chapter_numbers.append(chapter)
        if "chapter-compass" in classes:
            self.compasses += 1
        if "quiz-appendix-group" in classes:
            self.quiz_groups += 1
        if tag == "meta" and values.get("name") == "viewport":
            self.has_viewport = True


class BookBuildContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.builder = load_builder()
        cls.manifest = json.loads((BOOK_DIR / "manifest.json").read_text(encoding="utf-8"))

    def test_manifest_covers_exactly_all_source_chapters(self) -> None:
        self.builder.validate_manifest(self.manifest)
        files = [name for part in self.manifest["parts"] for name in part["files"]]
        # 集合相等是主门（清单与磁盘一一对应）；计数只作地板防双删。
        self.assertGreaterEqual(len(files), 88)
        self.assertEqual(len(set(files)), len(files))
        docs = self.builder.DOCS_DIR
        expected: list[str] = []
        for section in ("c", "build", "stm32", "rtos/freertos", "rtos/rtthread", "rtos/compare", "esp32", "gd32", "lab", "projects", "ai"):
            for path in sorted((docs / section).glob("*.md")):
                if path.name == "index.md" or (section == "lab" and path.name == "template.md"):
                    continue
                expected.append(f"{section}/{path.name}")
        self.assertEqual(set(expected), set(files))
        self.assertEqual(set(files), set(self.manifest["chapter_guides"]))
        for name, guide in self.manifest["chapter_guides"].items():
            with self.subTest(chapter=name):
                self.assertTrue(guide["question"].strip())
                self.assertTrue(guide["deliverable"].strip())
                self.assertTrue(guide["boundary"].strip())
                self.assertGreaterEqual(len(guide["sources"]), 1)

    def test_build_produces_one_complete_offline_book(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = self.builder.build_html(Path(tmp))
            html = output.read_text(encoding="utf-8")

        parsed = BookHTMLParser()
        parsed.feed(html)
        chapter_total = sum(len(part["files"]) for part in self.manifest["parts"])
        self.assertEqual([f"{index:02d}" for index in range(1, chapter_total + 1)], parsed.chapter_numbers)
        self.assertEqual(chapter_total, parsed.compasses)
        self.assertEqual(
            {
                "appendix-engineering",
                "appendix-examples",
                "appendix-exercises",
                "appendix-glossary",
                "appendix-references",
                "appendix-faq",
                "appendix-oss-map",
            },
            parsed.appendices,
        )
        self.assertTrue(parsed.has_viewport)
        self.assertEqual(13, parsed.quiz_groups)
        self.assertGreaterEqual(len(parsed.image_sources), 90)
        self.assertTrue(all(src.startswith("data:image/") for src in parsed.image_sources))

        details_open = len(re.findall(r"<details\b", html))
        details_close = len(re.findall(r"</details>", html))
        self.assertGreater(details_open, 300)
        self.assertEqual(details_open, details_close)
        self.assertIn("beforeprint", html)
        self.assertIn("IntersectionObserver", html)
        self.assertIn('href="#appendix-exercises-answers-c03-volatile"', html)
        self.assertIn("reading-progress", html)
        self.assertIn("part-intro", html)

        fragment_links = [href[1:] for href in parsed.hrefs if href.startswith("#")]
        missing = sorted({fragment for fragment in fragment_links if fragment not in parsed.ids})
        self.assertEqual([], missing)
        local_markdown = [href for href in parsed.hrefs if re.search(r"\.md(?:#|$|\?)", href) and "github.com" not in href]
        self.assertEqual([], local_markdown)
        self.assertIn("通往单片机之路", html)
        self.assertIn("V11.1.0", html)
        self.assertIn("v5.5.2", html)
        self.assertIn("五个契约", html)

    def test_running_header_map_marks_chapters_and_appendices_only(self) -> None:
        toc = [
            [1, "这不是文章合集，是一本书", 2],
            [2, "01 C0 为什么嵌入式 C 是另一种 C", 7],
            [3, "本章精髓", 7],
            [2, "02 C1 内存模型", 13],
            [1, "第二部分 构建与运行全过程", 82],
            [2, "10 B0 工具链全景", 83],
            [1, "附录 A 工程深读", 670],
            [2, "附录小节", 671],
        ]
        marks = self.builder.running_header_map(toc, "通往单片机之路")
        self.assertEqual(
            [
                (2, "通往单片机之路"),
                (7, "01 C0 为什么嵌入式 C 是另一种 C"),
                (13, "02 C1 内存模型"),
                (83, "10 B0 工具链全景"),
                (670, "附录 A 工程深读"),
            ],
            marks,
        )

    def test_manifest_rejects_a_part_without_intro(self) -> None:
        broken = copy.deepcopy(self.manifest)
        broken["parts"][0].pop("intro")
        with self.assertRaisesRegex(self.builder.BuildError, "part missing field: intro"):
            self.builder.validate_manifest(broken)

    def test_container_close_without_open_is_a_build_error(self) -> None:
        with self.assertRaisesRegex(self.builder.BuildError, "unbalanced :::"):
            self.builder.convert_containers("before\n:::\nafter\n", "sample.md")

    def test_unclosed_container_at_eof_is_a_build_error(self) -> None:
        with self.assertRaisesRegex(self.builder.BuildError, "unclosed :::"):
            self.builder.convert_containers("::: tip 标题\ncontent\n", "sample.md")

    def test_missing_local_image_is_a_build_error(self) -> None:
        source = self.builder.DOCS_DIR / "stm32" / "03-gpio.md"
        with self.assertRaisesRegex(self.builder.BuildError, "missing local image"):
            self.builder.embed_local_images('<img src="../public/anim/no-such.svg">', source, "stm32/03-gpio.md")

    def test_manifest_rejects_a_missing_chapter_guide(self) -> None:
        broken = copy.deepcopy(self.manifest)
        broken["chapter_guides"].pop(next(iter(broken["chapter_guides"])))
        with self.assertRaisesRegex(self.builder.BuildError, "chapter guide mismatch"):
            self.builder.validate_manifest(broken)

    def test_manifest_rejects_unknown_source_ids(self) -> None:
        broken = copy.deepcopy(self.manifest)
        name = next(iter(broken["chapter_guides"]))
        broken["chapter_guides"][name]["sources"] = ["no-such-source"]
        with self.assertRaisesRegex(self.builder.BuildError, "unknown chapter sources"):
            self.builder.validate_manifest(broken)

    def test_examples_appendix_must_cover_projects_json(self) -> None:
        class _Ctx:
            manifest = self.manifest

        self.builder.audit_examples_appendix(_Ctx())  # must not raise

    def _synthetic_outline(self) -> tuple[dict, dict[str, str], list]:
        manifest = self.manifest
        title_map = {}
        entries = [[1, "通往单片机之路", 1], [1, "目录与分部目标", 3]]
        # 书内目录页：全部分部/章标题在此重复出现，但 level 是 2/3——
        # 结构匹配必须跳过它们，只认 level 1 的正文 h1。
        number = 0
        for part in manifest["parts"]:
            entries.append([2, part["title"], 3])
            for name in part["files"]:
                number += 1
                entries.append([3, f"{number:02d} 第{number}课标题{name}", 3])
        number = 0
        for part in manifest["parts"]:
            entries.append([1, part["title"], 10])
            for name in part["files"]:
                number += 1
                title = f"第{number}课标题{name}"
                title_map[name] = title
                entries.append([1, title, 20])
                entries.append([2, "本章罗盘", 20])
                entries.append([2, "第一节", 21])
                entries.append([3, "小节", 22])
        for appendix in manifest["appendices"]:
            entries.append([1, appendix["title"], 500])
            entries.append([2, "附录小节", 501])
        return manifest, title_map, entries

    def test_outline_restructure_builds_part_chapter_section_tree(self) -> None:
        manifest, title_map, entries = self._synthetic_outline()
        toc = self.builder.restructured_outline(entries, manifest, title_map)
        levels = [row[0] for row in toc]
        self.assertEqual(1, levels[0])  # 目录与分部目标 stays top-level
        parts = [row for row in toc if row[0] == 1 and row[1].startswith("第")]
        self.assertEqual(len(manifest["parts"]), len(parts))
        chapter_total = sum(len(part["files"]) for part in manifest["parts"])
        chapters = [row for row in toc if row[0] == 2 and re.match(r"^\d{2} ", row[1])]
        self.assertEqual(chapter_total, len(chapters))
        self.assertRegex(chapters[0][1], r"^01 第1课标题")
        sections = [row for row in toc if row[0] >= 3]
        self.assertEqual(chapter_total, len(sections))  # chapter h2 only; compass and h3 dropped
        appendix_sections = [row for row in toc if row[1] == "附录小节"]
        self.assertEqual(len(manifest["appendices"]), len(appendix_sections))
        self.assertTrue(all(row[0] == 2 for row in appendix_sections))
        self.assertEqual(3, max(row[0] for row in toc))  # strictly three levels

    def test_outline_restructure_fails_loudly_on_missing_chapter(self) -> None:
        manifest, title_map, entries = self._synthetic_outline()
        # Drop one chapter h1 from the printed outline.
        broken = [row for row in entries if row[1] != title_map["c/00-c-in-mcu.md"]]
        with self.assertRaisesRegex(self.builder.BuildError, "structural entry not found"):
            self.builder.restructured_outline(broken, manifest, title_map)


if __name__ == "__main__":
    unittest.main()

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
    spec = importlib.util.spec_from_file_location("stm32_book_builder", BUILD_PATH)
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
        if tag == "meta" and values.get("name") == "viewport":
            self.has_viewport = True


class BookBuildContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.builder = load_builder()
        cls.manifest = json.loads((BOOK_DIR / "manifest.json").read_text(encoding="utf-8"))

    def test_manifest_covers_exactly_the_29_source_chapters(self) -> None:
        self.builder.validate_manifest(self.manifest)
        files = [name for part in self.manifest["parts"] for name in part["files"]]
        expected = [path.name for path in sorted((BOOK_DIR.parent / "docs").glob("[0-2][0-9]-*.md"))]
        self.assertEqual(29, len(expected))
        self.assertEqual(expected, files)
        self.assertEqual(set(expected), set(self.manifest["chapter_guides"]))
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
        self.assertEqual([f"{index:02d}" for index in range(29)], parsed.chapter_numbers)
        self.assertEqual(29, parsed.compasses)
        self.assertEqual(
            {
                "appendix-engineering",
                "appendix-examples",
                "appendix-exercises",
                "appendix-glossary",
                "appendix-references",
            },
            parsed.appendices,
        )
        self.assertTrue(parsed.has_viewport)
        self.assertGreater(len(parsed.image_sources), 25)
        self.assertTrue(all(src.startswith("data:image/") for src in parsed.image_sources))
        self.assertNotIn("<!-- video:", html)
        self.assertNotIn("<video", html.lower())
        self.assertNotIn("旁白（与字幕、配音同一份稿）", html)
        self.assertIn("STM32CubeF4 v1.28.3", html)
        self.assertIn("c242589d766eada3ad1d795630f2b1c2482a2af8", html)
        self.assertIn("STSW-STM32054", html)
        self.assertIn("afa743577f2784e95be2d5003380fdb84a702519", html)

        fragment_links = [href[1:] for href in parsed.hrefs if href.startswith("#")]
        missing = sorted({fragment for fragment in fragment_links if fragment not in parsed.ids})
        self.assertEqual([], missing)
        local_markdown = [href for href in parsed.hrefs if re.search(r"\.md(?:#|$)", href)]
        self.assertEqual([], local_markdown)

    def test_mobile_layout_has_no_page_level_horizontal_overflow(self) -> None:
        from playwright.sync_api import sync_playwright

        with tempfile.TemporaryDirectory() as tmp:
            output = self.builder.build_html(Path(tmp))
            candidates = self.builder._browser_candidates(None)
            launch_args = {"headless": True}
            if candidates:
                launch_args["executable_path"] = str(candidates[0])
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(**launch_args)
                try:
                    page = browser.new_page(
                        viewport={"width": 390, "height": 844},
                        is_mobile=True,
                        color_scheme="light",
                    )
                    page.goto(output.resolve().as_uri(), wait_until="load")
                    page.wait_for_function(
                        "Array.from(document.images).every(img => img.complete && img.naturalWidth > 0)"
                    )
                    overflow = page.evaluate(
                        "document.documentElement.scrollWidth - document.documentElement.clientWidth"
                    )
                finally:
                    browser.close()
        self.assertEqual(0, overflow)

    def test_mobile_wide_tables_scroll_without_crushing_columns(self) -> None:
        from playwright.sync_api import sync_playwright

        with tempfile.TemporaryDirectory() as tmp:
            output = self.builder.build_html(Path(tmp))
            candidates = self.builder._browser_candidates(None)
            launch_args = {"headless": True}
            if candidates:
                launch_args["executable_path"] = str(candidates[0])
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(**launch_args)
                try:
                    page = browser.new_page(
                        viewport={"width": 390, "height": 844},
                        is_mobile=True,
                        color_scheme="light",
                    )
                    page.goto(output.resolve().as_uri() + "#chapter-10", wait_until="load")
                    tables = page.locator("#chapter-10 table").evaluate_all(
                        """tables => tables
                            .filter(table => table.rows[0]?.cells.length >= 4)
                            .map(table => ({
                                wrapperClientWidth: table.parentElement.clientWidth,
                                wrapperScrollWidth: table.parentElement.scrollWidth,
                                narrowestHeader: Math.min(
                                    ...Array.from(table.rows[0].cells, cell =>
                                        cell.getBoundingClientRect().width)
                                ),
                            }))"""
                    )
                finally:
                    browser.close()

        self.assertGreater(len(tables), 0)
        for table in tables:
            with self.subTest(table=table):
                self.assertGreater(table["wrapperScrollWidth"], table["wrapperClientWidth"])
                self.assertGreaterEqual(table["narrowestHeader"], 72)

    def test_print_layout_keeps_reading_units_together(self) -> None:
        from playwright.sync_api import sync_playwright

        with tempfile.TemporaryDirectory() as tmp:
            output = self.builder.build_html(Path(tmp))
            candidates = self.builder._browser_candidates(None)
            launch_args = {"headless": True}
            if candidates:
                launch_args["executable_path"] = str(candidates[0])
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(**launch_args)
                try:
                    page = browser.new_page(viewport={"width": 1280, "height": 900})
                    page.emulate_media(media="print")
                    page.goto(output.resolve().as_uri() + "#chapter-27", wait_until="load")
                    styles = page.evaluate(
                        """() => {
                            const chapter = document.querySelector('#chapter-27');
                            const css = selector => getComputedStyle(chapter.querySelector(selector));
                            const body = getComputedStyle(document.body);
                            return {
                                headingBreakAfter: css('h2').breakAfter,
                                mediaBreakInside: css('p[align="center"]').breakInside,
                                rowBreakInside: css('tr').breakInside,
                                preWhiteSpace: css('pre').whiteSpace,
                                orphans: Number(body.orphans),
                                widows: Number(body.widows),
                            };
                        }"""
                    )
                finally:
                    browser.close()

        self.assertIn(styles["headingBreakAfter"], {"avoid", "avoid-page"})
        self.assertIn(styles["mediaBreakInside"], {"avoid", "avoid-page"})
        self.assertIn(styles["rowBreakInside"], {"avoid", "avoid-page"})
        self.assertEqual("pre-wrap", styles["preWhiteSpace"])
        self.assertGreaterEqual(styles["orphans"], 3)
        self.assertGreaterEqual(styles["widows"], 3)

    def test_rendered_table_without_cells_is_a_build_error(self) -> None:
        with self.assertRaisesRegex(self.builder.BuildError, "rendered table has no cells"):
            self.builder.wrap_tables("<table><caption>empty</caption></table>")


    def test_unclosed_video_block_is_a_build_error(self) -> None:
        with self.assertRaisesRegex(self.builder.BuildError, "unclosed video block"):
            self.builder.strip_video_blocks("before\n<!-- video:ch00 -->\nafter\n", "sample.md")

    def test_missing_local_image_is_a_build_error(self) -> None:
        source = BOOK_DIR.parent / "docs" / "00-如何学习STM32.md"
        with self.assertRaisesRegex(self.builder.BuildError, "missing local image"):
            self.builder.embed_local_images('<img src="../assets/no-such-image.svg">', source)

    def test_pdf_stamping_preserves_publication_metadata(self) -> None:
        import fitz

        metadata = {
            "title": "STM32 实战",
            "author": "zhuguang-ZFG 与贡献者",
            "subject": "证据驱动的嵌入式入门与工程手册",
            "keywords": "STM32, Cortex-M, lwIP, FreeRTOS, embedded systems",
        }
        with tempfile.TemporaryDirectory() as tmp:
            raw = Path(tmp) / "raw.pdf"
            output = Path(tmp) / "book.pdf"
            document = fitz.open()
            document.new_page()
            document.new_page()
            document.save(raw)
            document.close()

            self.builder._stamp_page_numbers(raw, output, metadata)
            stamped = fitz.open(output)
            try:
                actual = {key: stamped.metadata.get(key) for key in metadata}
                page_label = stamped[1].get_text()
            finally:
                stamped.close()

        self.assertEqual(metadata, actual)
        self.assertIn("1 / 1", page_label)

    def test_pdf_stamping_adds_running_headers_and_toc_page_numbers(self) -> None:
        import fitz

        metadata = {"title": "STM32 实战", "author": "作者", "subject": "主题", "keywords": "STM32"}
        with tempfile.TemporaryDirectory() as tmp:
            raw = Path(tmp) / "raw.pdf"
            output = Path(tmp) / "book.pdf"
            document = fitz.open()
            document.new_page()  # cover
            document.new_page()  # contents
            document.new_page()  # chapter 00 opening
            document.new_page()  # chapter 00 continuation
            document.new_page()  # chapter 01 opening
            toc = document[1]
            toc.insert_text((50, 50), "目录与分部目标", fontname="china-s", fontsize=12)
            toc.insert_text(
                (50, 82),
                "第一部分 很长的全宽目录标题必须为右侧页码保留空间",
                fontname="china-s",
                fontsize=12,
            )
            toc.insert_link({"kind": fitz.LINK_GOTO, "from": fitz.Rect(45, 66, 520, 88), "page": 3})
            toc.insert_text((70, 116), "00 系统", fontname="china-s", fontsize=8)
            toc.insert_link({"kind": fitz.LINK_GOTO, "from": fitz.Rect(65, 100, 250, 122), "page": 2})
            toc.insert_text((325, 116), "01 下一章", fontname="china-s", fontsize=8)
            toc.insert_link({"kind": fitz.LINK_GOTO, "from": fitz.Rect(320, 100, 510, 122), "page": 4})
            document.set_toc([[1, "00 系统", 3], [1, "01 下一章", 5]])
            document.save(raw)
            document.close()

            self.builder._stamp_page_numbers(raw, output, metadata)
            stamped = fitz.open(output)
            try:
                toc_words = stamped[1].get_text("words")
                continuation = stamped[3].get_text()
                opening = stamped[2].get_text()
            finally:
                stamped.close()

        heading_reference_words = [
            word for word in toc_words
            if word[4] == "3" and 70 < word[1] < 100
        ]
        self.assertEqual(1, len(heading_reference_words))
        self.assertGreater(
            heading_reference_words[0][0],
            500,
            "full-width TOC headings must keep page references in the page gutter",
        )
        page_reference_words = [
            word for word in toc_words
            if word[4] in {"2", "4"} and 104 < word[1] < 135
        ]
        self.assertEqual({"2", "4"}, {word[4] for word in page_reference_words})
        self.assertGreater(
            abs(page_reference_words[0][0] - page_reference_words[1][0]),
            100,
            "same-row TOC page references must use separate column gutters",
        )
        self.assertIn("00 系统", continuation)
        self.assertNotIn("00 系统", opening)

    def test_manifest_rejects_a_missing_chapter_guide(self) -> None:
        broken = copy.deepcopy(self.manifest)
        broken["chapter_guides"].pop(next(iter(broken["chapter_guides"])))
        with self.assertRaisesRegex(self.builder.BuildError, "chapter guide mismatch"):
            self.builder.validate_manifest(broken)


if __name__ == "__main__":
    unittest.main()

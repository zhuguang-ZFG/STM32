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

    def test_english_edition_covers_all_29_source_chapters(self) -> None:
        docs = BOOK_DIR.parent / "docs"
        chinese_numbers = [path.name[:2] for path in sorted(docs.glob("[0-2][0-9]-*.md"))]
        english_numbers = [path.name[:2] for path in sorted((docs / "en").glob("[0-2][0-9]-*.md"))]

        self.assertEqual([f"{index:02d}" for index in range(29)], chinese_numbers)
        self.assertEqual(chinese_numbers, english_numbers)

    def test_narrated_blocks_include_direct_mp4_links(self) -> None:
        generator_path = BOOK_DIR.parent / "tools" / "gen_narrated.py"
        spec = importlib.util.spec_from_file_location("narrated_generator_test", generator_path)
        if spec is None or spec.loader is None:
            self.fail(f"cannot load narration generator: {generator_path}")
        generator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(generator)
        chapter = {"id": "28", "slug": "rtos-system", "segments": []}

        chinese = generator._doc_block(chapter, "../assets/video", "zh", 180)
        english = generator._doc_block(chapter, "../../assets/video", "en", 180)
        self.assertIn('href="../assets/video/ch28-rtos-system.mp4"', chinese)
        self.assertIn('href="../../assets/video/ch28-rtos-system.mp4"', english)

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
        self.assertIn("<strong>v1.0.6</strong>", html)
        self.assertNotIn("1.0.0-rc", html)
        self.assertIn('<p class="part-label">第 1 部</p>', html)
        self.assertIn('<span class="chapter-number">第 00 章</span>', html)
        self.assertIn('<span class="chapter-number">附录</span>', html)
        self.assertNotIn(">PART 0<", html)
        self.assertNotIn(">CHAPTER 00<", html)
        self.assertIn('class="compass-card compass-boundary"', html)
        self.assertNotIn("<h2>本章罗盘</h2>", html)
        self.assertNotIn("<h2>合上书，三问</h2>", html)
        self.assertIn("本部分到此结束", html)
        self.assertIn('class="source-id"', html)
        self.assertIn('<p class="callout-label">注意</p>', html)
        self.assertIn('<p class="callout-label">提示</p>', html)
        self.assertIn('<p class="callout-label">说明</p>', html)
        self.assertIn('class="toc-jump"', html)
        self.assertIn(">目录</a>", html)
        self.assertIn("position: sticky", html)
        self.assertIn("max-height: 200mm", html)
        self.assertIn("break-before: avoid-page", html)
        self.assertIn('id="imprint"', html)
        self.assertIn("版权页", html)
        self.assertIn('class="cover-art"', html)
        self.assertIn("<figcaption>", html)
        body = html.split("</style>", 1)[1]
        self.assertNotIn('align="center"', body)
        self.assertNotIn("fonts.googleapis", html)
        self.assertNotIn("fonts.gstatic", html)
        self.assertIn("配套资源", html)
        self.assertIn('id="part-closing-p6"', html)
        self.assertIn("学习路线收束", html)
        self.assertIn("会上手的几笔账", html)
        self.assertIn("换系列之前先对的账", html)
        self.assertIn("通道、描述符与故障寄存器", html)
        self.assertIn("0xE000ED28", html)
        self.assertIn("0x1209", html)
        self.assertIn("17.2%", html)
        self.assertIn("0x271", html)
        self.assertIn("0x1FFFF7E0", html)
        self.assertIn("0x50", html)
        self.assertIn("450 kbit/s", html)
        self.assertIn("第四个 SYSCLK", html)
        self.assertIn("把一格填满", html)
        self.assertNotIn("英文整书不在这一版", html)
        self.assertIn('class="part-closing"', html)
        self.assertIn("00 如何学习 STM32", html)
        self.assertNotIn("00-如何学习STM32", html)
        self.assertNotIn("mp.weixin.qq.com", html)
        self.assertNotIn("手机阅读版", html)
        self.assertNotIn("上一篇：", html)
        self.assertNotIn("下一篇：", html)
        self.assertNotIn("📌", html)
        self.assertIn("FAQ STM32 boot process", html)
        self.assertIn("mp.weixin.qq.com", (BOOK_DIR.parent / "docs" / "00-如何学习STM32.md").read_text(encoding="utf-8"))

    def test_book_mode_strips_promo_without_touching_fenced_headings(self) -> None:
        raw = """# 00 标题

## 📌 学习目标

正文

```
## 📌 不要改代码围栏
```

## 🔗 相关资源

- 官方手册：**RM0008** 第 9 章
- 下一篇：[01 标题](01.md)
- 📱 手机阅读版：[章](https://mp.weixin.qq.com/s/abc)
- 免责声明：本仓库插画均为作者自绘矢量图/程序生成动画，非厂商实拍照片。
"""
        title, content, questions = self.builder.prepare_chapter_markdown(raw, "sample")
        self.assertEqual("00 标题", title)
        self.assertEqual([], questions)
        self.assertIn("## 学习目标", content)
        self.assertNotIn("📌 学习目标", content)
        self.assertIn("## 📌 不要改代码围栏", content)
        self.assertIn("**RM0008**", content)
        self.assertIn("## 相关资源", content)
        self.assertNotIn("mp.weixin.qq.com", content)
        self.assertNotIn("下一篇", content)
        self.assertNotIn("免责声明", content)

    def test_semanticize_figures_wraps_the_known_caption(self) -> None:
        rendered = '<p align="center"><img src="a.svg"><br><sub>▲ 图 1 接线</sub></p>'
        converted = self.builder.semanticize_figures(rendered)
        self.assertEqual(
            "<figure><img src=\"a.svg\"><figcaption>图 1 接线</figcaption></figure>",
            converted,
        )
        untouched = self.builder.semanticize_figures("<p>plain</p>")
        self.assertEqual("<p>plain</p>", untouched)

    def test_english_book_mode_drops_serial_footer_lines(self) -> None:
        raw = """# 00 Title

> 中文: 对应章节

## Related resources

- **RM0008**, chapter 9
- Next: [01 Title](01-dev-environment.md)
- Previous: [start](start.md)
- Disclaimer: every illustration in this repo is a vector drawing.
- Related: [board](21-board-maps.md)
"""
        title, content, questions = self.builder.prepare_chapter_markdown(raw, "sample", "en")
        self.assertEqual("00 Title", title)
        self.assertEqual([], questions)
        self.assertNotIn("中文:", content)
        self.assertIn("**RM0008**", content)
        self.assertIn("## Related resources", content)
        self.assertNotIn("Next:", content)
        self.assertNotIn("Previous:", content)
        self.assertNotIn("Disclaimer:", content)
        self.assertNotIn("Related:", content)

    def test_english_book_is_a_separate_offline_edition(self) -> None:
        manifest = json.loads((BOOK_DIR / "manifest-en.json").read_text(encoding="utf-8"))
        self.builder.validate_manifest(manifest)
        self.assertEqual("en", manifest["language"])
        self.assertEqual("docs/en", manifest["docs_dir"])
        self.assertEqual("book/en", manifest["book_dir"])
        self.assertEqual("stm32-practical-book-en.html", manifest["output_name"])
        self.assertEqual("stm32-practical-book-en.pdf", manifest["pdf_name"])
        self.assertEqual("1.0.6", manifest["version"])
        self.assertEqual(self.manifest["version"], manifest["version"])
        self.assertEqual(set(self.builder.UI["zh-CN"]), set(self.builder.UI["en"]))
        zh_sources = {name[:2]: guide["sources"] for name, guide in self.manifest["chapter_guides"].items()}
        for name, guide in manifest["chapter_guides"].items():
            self.assertEqual(zh_sources[name[:2]], guide["sources"])

        with tempfile.TemporaryDirectory() as tmp:
            output = self.builder.build_html(Path(tmp), BOOK_DIR / "manifest-en.json")
            self.assertEqual("stm32-practical-book-en.html", output.name)
            html = output.read_text(encoding="utf-8")

        parsed = BookHTMLParser()
        parsed.feed(html)
        self.assertEqual([f"{index:02d}" for index in range(29)], parsed.chapter_numbers)
        self.assertEqual(29, parsed.compasses)
        self.assertIn('<html lang="en">', html)
        self.assertIn("<strong>v1.0.6</strong>", html)
        self.assertNotIn("1.0.0-rc", html)
        self.assertIn('<p class="part-label">Part 1</p>', html)
        self.assertIn('<span class="chapter-number">Chapter 00</span>', html)
        self.assertIn('<span class="chapter-number">Appendix</span>', html)
        self.assertNotIn(">PART 0<", html)
        self.assertNotIn(">CHAPTER 00<", html)
        self.assertIn('class="compass-card compass-question"', html)
        self.assertNotIn("<h2>Chapter compass</h2>", html)
        self.assertIn("End of this part", html)
        self.assertIn('class="source-id"', html)
        self.assertIn('<p class="callout-label">Warning</p>', html)
        self.assertIn('<p class="callout-label">Tip</p>', html)
        self.assertIn('<p class="callout-label">Note</p>', html)
        self.assertIn(">Contents</a>", html)
        self.assertIn("<figcaption>", html)
        self.assertIn('class="cover-art"', html)
        self.assertIn('id="part-closing-p6"', html)
        self.assertIn("Where the road goes next", html)
        self.assertIn("Numbers you will actually use", html)
        self.assertIn("Numbers to reconcile before changing family", html)
        self.assertIn("Channels, descriptors, and fault registers", html)
        self.assertIn("0xE000ED28", html)
        self.assertIn("0x1209", html)
        self.assertIn("17.2%", html)
        self.assertIn("0x271", html)
        self.assertIn("0x1FFFF7E0", html)
        self.assertIn("0x50", html)
        self.assertIn("450 kbit/s", html)
        self.assertIn("fourth rising edge", html)
        self.assertIn("What fills one cell", html)
        self.assertIn("STM32CubeF4 v1.28.3", html)
        self.assertNotIn("Next:", html)
        self.assertNotIn("Previous:", html)
        self.assertNotIn("mp.weixin.qq.com", html)
        self.assertNotIn("合上书，三问", html)
        self.assertNotIn("学习路线收束", html)
        source = (BOOK_DIR.parent / "docs" / "en" / "00-how-to-learn-stm32.md").read_text(encoding="utf-8")
        self.assertIn("Next:", source)
        self.assertIn("Disclaimer: every illustration", source)

    def test_english_glossary_covers_the_same_themes(self) -> None:
        text = (BOOK_DIR / "book" / "en" / "D-glossary.md").read_text(encoding="utf-8")
        rows = [
            line
            for line in text.splitlines()
            if line.startswith("| ") and not line.startswith("| Term") and not line.startswith("| ---")
        ]
        self.assertGreaterEqual(len(rows), 120)
        for heading in (
            "## Clocks and reset",
            "## Pins, GPIO, and alternate functions",
            "## Interrupts and core exceptions",
            "## Timers and PWM",
            "## UART, I2C, SPI, CAN, and USB",
            "## ADC, DAC, and DMA",
            "## Flash, boot, and low power",
            "## RTOS and concurrency",
            "## Ethernet, lwIP, and MQTT",
            "## Debug",
            "## Numbers you will actually use",
            "## Numbers to reconcile before changing family",
            "## Channels, descriptors, and fault registers",
        ):
            self.assertIn(heading, text)

    def test_number_ledger_is_the_same_arithmetic_in_both_editions(self) -> None:
        chinese = (BOOK_DIR / "book" / "D-术语表.md").read_text(encoding="utf-8")
        english = (BOOK_DIR / "book" / "en" / "D-glossary.md").read_text(encoding="utf-8")
        for token in ("STM32F103C8T6", "0x1FFFF7E0", "0x410", "0x271", "86.8", "624", "21 µs", "32"):
            with self.subTest(token=token):
                self.assertIn(token, chinese)
                self.assertIn(token, english)
        for token in ("167 ns", "0x50", "450 kbit/s", "7.2", "0x45670123", "0xCDEF89AB", "1.1 µA", "PC11", "PE2", "0x20000000"):
            with self.subTest(token=token):
                self.assertIn(token, chinese)
                self.assertIn(token, english)
        for token in ("0xEF4017", "0xE000ED28", "0x40000000", "0x1209", "0x0043", "17.2%", "1460", "50 MHz", "Channel 5"):
            with self.subTest(token=token):
                self.assertIn(token, chinese)
                self.assertIn(token, english)
        self.assertIn("会上手的几笔账", chinese)
        self.assertIn("换系列之前先对的账", chinese)
        self.assertIn("通道、描述符与故障寄存器", chinese)
        self.assertIn("Numbers to reconcile before changing family", english)
        self.assertIn("Channels, descriptors, and fault registers", english)
        self.assertEqual(1, (BOOK_DIR / "manifest.json").read_text(encoding="utf-8").count('"an2606":'))
        self.assertEqual(1, (BOOK_DIR / "manifest-en.json").read_text(encoding="utf-8").count('"an2606":'))
        self.assertIn("rm0090", self.manifest["chapter_guides"]["10-DMA.md"]["sources"])
        self.assertIn("project-examples", self.manifest["chapter_guides"]["14-USB.md"]["sources"])
        self.assertNotIn("英文整书不在这一版", (BOOK_DIR / "book" / "F-学习路线收束.md").read_text(encoding="utf-8"))
        for name in ("A-工程深读.md", "B-例程索引.md", "E-参考资料.md", "F-学习路线收束.md"):
            self.assertIn("0x271", (BOOK_DIR / "book" / name).read_text(encoding="utf-8"))
        for name in ("A-uart-dma.md", "B-examples.md", "E-sources.md", "F-closing.md"):
            self.assertIn("0x271", (BOOK_DIR / "book" / "en" / name).read_text(encoding="utf-8"))

    def test_dbg_swen_usbpre_and_jedec_facts_stay_scoped(self) -> None:
        for path in (
            BOOK_DIR / "book" / "F-学习路线收束.md",
            BOOK_DIR / "book" / "en" / "F-closing.md",
        ):
            line = next(row for row in path.read_text(encoding="utf-8").splitlines() if "DBG_SWEN" in row)
            self.assertTrue("BOOT_LOCK" in line or "RDP" in line, path.name)
            self.assertTrue("复位值为 0" in line or "resets to 0" in line, line)

        usb_texts = [
            (BOOK_DIR.parent / "docs" / "14-USB.md").read_text(encoding="utf-8"),
            (BOOK_DIR.parent / "docs" / "en" / "14-usb.md").read_text(encoding="utf-8"),
            (BOOK_DIR / "book" / "B-例程索引.md").read_text(encoding="utf-8"),
            (BOOK_DIR / "book" / "en" / "B-examples.md").read_text(encoding="utf-8"),
            (BOOK_DIR / "book" / "C-习题答案.md").read_text(encoding="utf-8"),
            (BOOK_DIR / "book" / "en" / "C-answers.md").read_text(encoding="utf-8"),
            (BOOK_DIR / "book" / "D-术语表.md").read_text(encoding="utf-8"),
            (BOOK_DIR / "book" / "en" / "D-glossary.md").read_text(encoding="utf-8"),
        ]
        bad_usbpre = re.compile(r"USBPRE\s*=\s*1\.5")
        for text in usb_texts:
            self.assertIsNone(bad_usbpre.search(text))
        for text in usb_texts[:2]:
            self.assertRegex(text, r"USBPRE\s*=\s*0")
            self.assertIn("1.5", text)
        for text in usb_texts[-2:]:
            self.assertIn("0xEF4017", text)
            self.assertIn("1023", text)
            self.assertTrue("等时" in text or "isochronous" in text)

        for name in ("08-SPI总线.md", "en/08-spi.md"):
            self.assertIn("0xEF4017", (BOOK_DIR.parent / "docs" / name).read_text(encoding="utf-8"))
        for name in ("14-USB.md", "en/14-usb.md"):
            chapter = (BOOK_DIR.parent / "docs" / name).read_text(encoding="utf-8")
            self.assertIn("1023", chapter)
            self.assertTrue("等时" in chapter or "isochronous" in chapter)

        spi = (BOOK_DIR.parent / "examples" / "spi-flash" / "main.c").read_text(encoding="utf-8")
        self.assertRegex(spi, r"id\[0\]\s*!=\s*0xEFU\s*\|\|\s*id\[1\]\s*!=\s*0x40U\s*\|\|\s*id\[2\]\s*!=\s*0x17U")

    def test_glossary_covers_terms_from_all_seven_parts(self) -> None:
        text = (BOOK_DIR / "book" / "D-术语表.md").read_text(encoding="utf-8")
        rows = [
            line
            for line in text.splitlines()
            if line.startswith("| ") and not line.startswith("| 术语") and not line.startswith("| ---")
        ]
        self.assertGreaterEqual(len(rows), 120)
        for heading in (
            "## 时钟与复位",
            "## 引脚、GPIO 与复用",
            "## 中断与内核异常",
            "## 定时器与 PWM",
            "## UART、I2C、SPI、CAN 与 USB",
            "## ADC、DAC 与 DMA",
            "## Flash、启动与低功耗",
            "## RTOS 与并发",
            "## 以太网、lwIP 与 MQTT",
            "## 调试",
            "## 会上手的几笔账",
            "## 换系列之前先对的账",
            "## 通道、描述符与故障寄存器",
        ):
            self.assertIn(heading, text)
        for term in ("TIMCLK", "AF", "NVIC", "DMA", "SAR ADC", "PWM", "lwIP", "SWDIO / SWCLK"):
            self.assertIn(term, text)

    def test_part_seven_closing_stays_out_of_the_docs_tree(self) -> None:
        closing = self.manifest["parts"][-1]["closing"]
        self.assertEqual("part-closing-p6", closing["id"])
        self.assertEqual("F-学习路线收束.md", closing["file"])
        self.assertTrue((BOOK_DIR / "book" / closing["file"]).is_file())
        self.assertFalse((BOOK_DIR.parent / "docs" / closing["file"]).exists())
        broken = copy.deepcopy(self.manifest)
        broken["parts"][-1]["closing"] = {"id": "part-closing-p6", "file": "missing.md"}
        with self.assertRaisesRegex(self.builder.BuildError, "missing part closing manuscript"):
            self.builder.validate_manifest(broken)

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

    def test_mobile_three_column_tables_keep_readable_columns(self) -> None:
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
                    page.goto(output.resolve().as_uri() + "#chapter-28", wait_until="load")
                    tables = page.locator("#chapter-28 table").evaluate_all(
                        """tables => tables
                            .filter(table => table.rows[0]?.cells.length === 3)
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
                                mediaBreakInside: css('figure').breakInside,
                                captionBreakBefore: css('figcaption').breakBefore,
                                imageMaxHeight: css('img').maxHeight,
                                rowBreakInside: css('tr').breakInside,
                                preWhiteSpace: css('pre').whiteSpace,
                                orphans: Number(body.orphans),
                                widows: Number(body.widows),
                                tocJumpPosition: getComputedStyle(document.querySelector('.toc-jump')).position,
                            };
                        }"""
                    )
                finally:
                    browser.close()

        self.assertIn(styles["headingBreakAfter"], {"avoid", "avoid-page"})
        self.assertIn(styles["mediaBreakInside"], {"avoid", "avoid-page"})
        self.assertIn(styles["captionBreakBefore"], {"avoid", "avoid-page"})
        self.assertNotEqual("none", styles["imageMaxHeight"])
        self.assertIn(styles["rowBreakInside"], {"avoid", "avoid-page"})
        self.assertEqual("pre-wrap", styles["preWhiteSpace"])
        self.assertGreaterEqual(styles["orphans"], 3)
        self.assertGreaterEqual(styles["widows"], 3)
        self.assertEqual("fixed", styles["tocJumpPosition"])

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

    def test_callout_classifier_marks_warning_tip_and_note(self) -> None:
        rendered = (
            "<blockquote><p>⚠️ 不要关掉 SWD。</p></blockquote>"
            "<blockquote><p>⚠️ <strong>重要说明</strong>：第一行。</p><p>第二行仍是同一条注意。</p></blockquote>"
            "<blockquote><p>提示：<strong>用命令行</strong>。</p></blockquote>"
            "<blockquote><p>记忆：<strong>R 看寄存器</strong>。</p></blockquote>"
            "<blockquote><p>Search tip: use the manual number.</p></blockquote>"
            "<blockquote><p>GPIO 是一切外设的入口。</p></blockquote>"
        )
        chinese = self.builder.classify_callouts(
            rendered, {"warning": "注意", "tip": "提示", "note": "说明"}
        )
        self.assertEqual(2, chinese.count("callout-warning"))
        self.assertEqual(3, chinese.count("callout-tip"))
        self.assertEqual(1, chinese.count("callout-note"))
        self.assertIn('<p class="callout-label">注意</p>', chinese)
        self.assertIn("不要关掉 SWD", chinese)
        self.assertIn("<strong>用命令行</strong>", chinese)
        self.assertIn("第二行仍是同一条注意。", chinese)
        english = self.builder.classify_callouts(
            rendered, {"warning": "Warning", "tip": "Tip", "note": "Note"}
        )
        self.assertIn('<p class="callout-label">Warning</p>', english)
        self.assertIn('<p class="callout-label">Tip</p>', english)
        self.assertIn('<p class="callout-label">Note</p>', english)
        self.assertEqual("<p>plain</p>", self.builder.classify_callouts("<p>plain</p>"))

    def test_cover_svg_stays_self_contained(self) -> None:
        svg = (BOOK_DIR / "cover.svg").read_text(encoding="utf-8")
        self.assertIn("<svg", svg)
        self.assertIn('aria-label="STM32 board"', svg)
        self.assertNotIn("@font-face", svg)
        self.assertNotRegex(svg, r"https?://(?!www\.w3\.org/)")
        self.assertNotRegex(svg, r"<(?:image|use)\b[^>]*\b(?:href|xlink:href)=")
        self.assertIn("#c4552a", svg)
        self.assertIn("#8ecae6", svg)
        self.assertNotIn("#9fd7c4", svg)
        self.assertIn("--spine: #c4552a", self.builder.CSS)

    def test_running_headers_follow_appendices_and_shorten_long_titles(self) -> None:
        import fitz

        metadata = {
            "title": "STM32 in Practice: From One LED to a System You Can Ship",
            "author": "author",
            "subject": "subject",
            "keywords": "STM32",
        }
        long_chapter = "00 " + ("寄存器" * 40)
        with tempfile.TemporaryDirectory() as tmp:
            raw = Path(tmp) / "raw.pdf"
            output = Path(tmp) / "book.pdf"
            document = fitz.open()
            for _ in range(6):
                document.new_page()
            document.set_toc(
                [
                    [1, long_chapter, 2],
                    [1, "Part 2  GPIO, interrupts, and time", 4],
                    [1, "A close reading: two valid contracts", 5],
                ]
            )
            document.save(raw)
            document.close()

            self.builder._stamp_page_numbers(raw, output, metadata)
            stamped = fitz.open(output)
            try:
                even_page = stamped[2].get_text()
                continued = stamped[3].get_text()
                appendix_open = stamped[4].get_text()
                appendix_cont = stamped[5].get_text()
                drawings = stamped[1].get_drawings()
            finally:
                stamped.close()

        self.assertIn("STM32 in Practice", even_page)
        self.assertNotIn("From One LED", even_page)
        self.assertNotIn(long_chapter, continued)
        self.assertIn("...", continued)
        self.assertNotIn("Part 2", continued)
        self.assertNotIn("A close reading", appendix_open)
        self.assertIn("A close reading: two valid contracts", appendix_cont)
        self.assertGreaterEqual(len(drawings), 1)

    def test_compass_and_closing_chrome_are_labeled_without_fake_headings(self) -> None:
        guide = {
            "question": "问题句",
            "deliverable": "交付句",
            "boundary": "边界句",
            "sources": ["rm0008"],
        }
        en_manifest = json.loads((BOOK_DIR / "manifest-en.json").read_text(encoding="utf-8"))
        for manifest, question, deliverable, boundary in (
            (self.manifest, "问题", "交付", "边界"),
            (en_manifest, "Question", "Deliverable", "Boundary"),
        ):
            fragment = self.builder.compass_html(guide, manifest)
            self.assertNotIn("<h2", fragment)
            self.assertIn('class="compass-card compass-question"', fragment)
            self.assertIn('class="compass-card compass-deliverable"', fragment)
            self.assertIn('class="compass-card compass-boundary"', fragment)
            self.assertIn(f'class="compass-role">{question}</p>', fragment)
            self.assertIn(f'class="compass-role">{deliverable}</p>', fragment)
            self.assertIn(f'class="compass-role">{boundary}</p>', fragment)
            self.assertIn('href="#source-rm0008"', fragment)
            self.assertIn("问题句", fragment)

        questions = self.builder.quick_check_html(["第一问？"], self.manifest)
        self.assertNotIn("<h2", questions)
        self.assertIn('class="quick-title">合上书，三问</p>', questions)
        english_questions = self.builder.quick_check_html(["One?"], en_manifest)
        self.assertIn('class="quick-title">Close the book: three questions</p>', english_questions)
        self.assertEqual("", self.builder.quick_check_html([], self.manifest))

        closing = self.builder.part_closing_html(self.manifest["parts"][-1], self.manifest, {})
        self.assertIn('class="closing-banner">本部分到此结束</p>', closing)
        english_closing = self.builder.part_closing_html(en_manifest["parts"][-1], en_manifest, {})
        self.assertIn('class="closing-banner">End of this part</p>', english_closing)

        card = self.builder.source_registry_html(self.manifest)
        self.assertIn('class="source-id"><code>rm0008</code>', card)
        self.assertIn('class="source-link"', card)
        self.assertIn(">打开来源</a>", card)
        english_card = self.builder.source_registry_html(en_manifest)
        self.assertIn(">Open source</a>", english_card)
        self.assertNotIn("<dt>标识</dt>", card)
        self.assertNotIn("<dt>Id</dt>", english_card)

    def test_code_glossary_and_print_css_keep_reading_units_movable(self) -> None:
        screen_css, print_css = self.builder.CSS.split("@media print", 1)
        self.assertIn("tab-size: 4", screen_css)
        self.assertIn("scrollbar-color:", screen_css)
        self.assertIn("user-select: text", screen_css)
        self.assertIn(
            '#appendix-glossary .table-scroll[style*="--table-columns: 3"] td:nth-child(3)',
            screen_css,
        )
        self.assertIn(
            '#appendix-glossary .table-scroll[style*="--table-columns: 4"] td:nth-child(4)',
            screen_css,
        )
        self.assertIn("li::marker", screen_css)
        self.assertIn("border-left: 3px solid var(--accent)", screen_css)
        self.assertIn("color-mix(in srgb, var(--code-ink) 28%, transparent)", screen_css)
        self.assertNotIn("rgba(0, 0, 0, .4)", screen_css)
        self.assertIn("position: sticky; left: 0", screen_css)
        self.assertIn("@media (max-width: 960px)", screen_css)
        self.assertIn(".part-index", screen_css)
        pre_rule = re.search(r"\bpre \{([^}]+)\}", print_css)
        self.assertIsNotNone(pre_rule)
        self.assertIn("white-space: pre-wrap", pre_rule.group(1))
        self.assertIn("break-inside: auto", pre_rule.group(1))
        self.assertNotIn("avoid", pre_rule.group(1))
        self.assertNotRegex(print_css, r"\.imprint[^{}]*\{[^}]*page-break-before:\s*always")
        self.assertRegex(
            print_css,
            r"\.chapter > header[^{]*\{[^}]*page-break-after:\s*avoid",
        )
        self.assertIn("--spine: #c4552a", print_css)
        self.assertIn("figure { background: transparent; }", print_css)
        self.assertIn("position: static", print_css)

    def test_narrow_desktop_stacks_compass_without_part_number_collision(self) -> None:
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
                    page = browser.new_page(viewport={"width": 1200, "height": 900})
                    page.goto(output.resolve().as_uri() + "#part-p0", wait_until="load")
                    page.wait_for_function(
                        "Array.from(document.images).every(img => img.complete && img.naturalWidth > 0)"
                    )

                    def measure():
                        return page.evaluate(
                            """() => {
                                const columns = value => value.trim().split(/\\s+/).filter(Boolean).length;
                                const compass = document.querySelector('#chapter-00 .chapter-compass');
                                const pre = document.querySelector('pre');
                                const preStyle = getComputedStyle(pre);
                                const term = document.querySelector('#appendix-glossary td');
                                const mixup = document.querySelector('#appendix-glossary td:nth-child(3)');
                                const section = document.querySelector('#chapter-00 h2');
                                const plate = document.querySelector('figure');
                                const marker = getComputedStyle(document.querySelector('#chapter-00 li'), '::marker');
                                const divider = document.querySelector('#part-p0');
                                const index = divider.querySelector('.part-index').getBoundingClientRect();
                                const title = divider.querySelector('h1').getBoundingClientRect();
                                const goal = divider.querySelector('.part-goal').getBoundingClientRect();
                                const overlaps = (box) =>
                                    box.right > index.left + 1
                                    && box.bottom > index.top + 1
                                    && box.top < index.bottom - 1;
                                return {
                                    compassColumns: columns(getComputedStyle(compass).gridTemplateColumns),
                                    fakeHeadings: document.querySelectorAll('.chapter-compass h2, .quick-check h2').length,
                                    tabSize: preStyle.tabSize,
                                    overflowX: preStyle.overflowX,
                                    whiteSpace: preStyle.whiteSpace,
                                    userSelect: preStyle.userSelect,
                                    glossaryWeightsDiffer:
                                        getComputedStyle(term).fontWeight !== getComputedStyle(mixup).fontWeight
                                        || getComputedStyle(term).backgroundColor !== getComputedStyle(mixup).backgroundColor,
                                    mixupBackground: getComputedStyle(mixup).backgroundColor,
                                    glossarySticky: getComputedStyle(term).position,
                                    sectionRule: section ? getComputedStyle(section).borderLeftWidth : '',
                                    figureBorder: plate ? getComputedStyle(plate).borderTopWidth : '',
                                    figureFill: plate ? getComputedStyle(plate).backgroundColor : '',
                                    markerColor: marker.color,
                                    imprintColumns: columns(getComputedStyle(document.querySelector('.imprint dl')).gridTemplateColumns),
                                    sourceColumns: columns(getComputedStyle(document.querySelector('.source-registry')).gridTemplateColumns),
                                    titleHitsIndex: overlaps(title),
                                    goalHitsIndex: overlaps(goal),
                                    pageOverflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
                                };
                            }"""
                        )

                    wide = measure()
                    page.set_viewport_size({"width": 840, "height": 900})
                    narrow = measure()
                    page.set_viewport_size({"width": 390, "height": 844})
                    phone = measure()
                    page.emulate_media(media="print")
                    printed = page.evaluate(
                        """() => {
                            const pre = getComputedStyle(document.querySelector('pre'));
                            const header = getComputedStyle(document.querySelector('#chapter-00 > header'));
                            const imprint = getComputedStyle(document.querySelector('.imprint'));
                            const cover = getComputedStyle(document.querySelector('.cover'));
                            const term = getComputedStyle(document.querySelector('#appendix-glossary td'));
                            const plate = getComputedStyle(document.querySelector('figure'));
                            return {
                                preBreakInside: pre.breakInside,
                                preWhiteSpace: pre.whiteSpace,
                                headerBreakAfter: header.breakAfter,
                                imprintBreakBefore: imprint.breakBefore,
                                coverBreakAfter: cover.breakAfter,
                                glossarySticky: term.position,
                                figureFill: plate.backgroundColor,
                            };
                        }"""
                    )
                finally:
                    browser.close()

        self.assertEqual(3, wide["compassColumns"])
        self.assertEqual(1, narrow["compassColumns"])
        self.assertEqual(0, wide["fakeHeadings"])
        self.assertEqual("4", wide["tabSize"])
        self.assertEqual("auto", wide["overflowX"])
        self.assertEqual("pre", wide["whiteSpace"])
        self.assertEqual("text", wide["userSelect"])
        self.assertTrue(wide["glossaryWeightsDiffer"])
        self.assertNotIn("rgba(0, 0, 0, 0)", wide["mixupBackground"])
        self.assertGreaterEqual(wide["imprintColumns"], 2)
        self.assertEqual(1, narrow["imprintColumns"])
        self.assertEqual(2, wide["sourceColumns"])
        self.assertEqual(1, narrow["sourceColumns"])
        self.assertFalse(wide["titleHitsIndex"])
        self.assertFalse(wide["goalHitsIndex"])
        self.assertFalse(narrow["titleHitsIndex"])
        self.assertFalse(narrow["goalHitsIndex"])
        self.assertFalse(phone["titleHitsIndex"])
        self.assertFalse(phone["goalHitsIndex"])
        self.assertEqual(1, phone["compassColumns"])
        self.assertEqual(0, wide["pageOverflow"])
        self.assertEqual(0, narrow["pageOverflow"])
        self.assertEqual(0, phone["pageOverflow"])
        self.assertEqual("static", wide["glossarySticky"])
        self.assertEqual("sticky", phone["glossarySticky"])
        self.assertEqual("3px", wide["sectionRule"])
        self.assertEqual("1px", wide["figureBorder"])
        self.assertNotIn("rgba(0, 0, 0, 0)", wide["figureFill"])
        self.assertEqual("rgb(7, 94, 132)", wide["markerColor"])
        self.assertEqual("static", printed["glossarySticky"])
        self.assertIn("rgba(0, 0, 0, 0)", printed["figureFill"])
        self.assertEqual("auto", printed["preBreakInside"])
        self.assertEqual("pre-wrap", printed["preWhiteSpace"])
        self.assertIn(printed["headerBreakAfter"], {"avoid", "avoid-page"})
        self.assertEqual("auto", printed["imprintBreakBefore"])
        self.assertIn(printed["coverBreakAfter"], {"page", "always"})

    def test_manifest_rejects_a_missing_chapter_guide(self) -> None:
        broken = copy.deepcopy(self.manifest)
        broken["chapter_guides"].pop(next(iter(broken["chapter_guides"])))
        with self.assertRaisesRegex(self.builder.BuildError, "chapter guide mismatch"):
            self.builder.validate_manifest(broken)


if __name__ == "__main__":
    unittest.main()

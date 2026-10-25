from __future__ import annotations

import copy
import hashlib
import importlib.util
import inspect
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


def _relative_luminance(hex_color: str) -> float:
    """WCAG 2.x sRGB relative luminance. Accepts #RGB and #RRGGBB."""
    text = hex_color.removeprefix("#")
    if len(text) == 3:
        text = "".join(character * 2 for character in text)
    red, green, blue = (int(text[index:index + 2], 16) for index in (0, 2, 4))

    def channel(value: int) -> float:
        unit = value / 255
        if unit <= 0.04045:
            return unit / 12.92
        return ((unit + 0.055) / 1.055) ** 2.4

    return 0.2126 * channel(red) + 0.7152 * channel(green) + 0.0722 * channel(blue)


def _contrast_ratio(foreground: str, background: str) -> float:
    lighter = max(_relative_luminance(foreground), _relative_luminance(background))
    darker = min(_relative_luminance(foreground), _relative_luminance(background))
    return (lighter + 0.05) / (darker + 0.05)


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


_TOKEN_LIGHT_KEYS = (
    "--paper",
    "--ink",
    "--muted",
    "--line",
    "--panel",
    "--accent",
    "--accent-soft",
    "--warn",
    "--warn-soft",
    "--tip",
    "--tip-soft",
    "--spine",
    "--spine-soft",
    "--code",
    "--code-ink",
    "--measure",
    "--space-bar",
    "--space-paragraph",
    "--space-figure",
    "--space-chapter",
    "--inset",
    "--leading-body",
    "--tracking-body",
    "--tracking-kicker",
    "--radius",
    "--elev",
    "--font-sans",
    "--font-mono",
    "--type-body",
    "--type-h1",
    "--type-h2",
    "--type-h3",
    "--type-h4",
    "--type-kicker",
    "--type-small",
    "--type-code",
    "--leading-heading",
    "--leading-caption",
    "--leading-toc",
    "--leading-code",
)
_TOKEN_COLOR_KEYS = _TOKEN_LIGHT_KEYS[:15]
_TOKEN_COVER_LOCK = ("--paper", "--ink", "--muted", "--warn", "--line", "--spine")


class BookBuildContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.builder = load_builder()
        cls.manifest = json.loads((BOOK_DIR / "manifest.json").read_text(encoding="utf-8"))

    def assert_version_history_and_index(self, html: str, language: str) -> None:
        """Front matter lists real editions; the subject index is back matter and in the TOC."""
        self.assertLess(html.index('id="imprint"'), html.index('id="version-history"'))
        self.assertLess(html.index('id="version-history"'), html.index('id="how-to-read"'))
        self.assertLess(html.index('id="part-closing-p6"'), html.index('id="subject-index"'))
        self.assertLess(html.index('id="appendix-references"'), html.index('id="subject-index"'))
        self.assertNotIn('class="appendix" id="subject-index"', html)
        self.assertIn('class="back-matter subject-index"', html)

        history = html.split('id="version-history"', 1)[1].split('id="how-to-read"', 1)[0]
        versions = ("1.2.9", "1.2.8", "1.2.7", "1.2.6", "1.2.5", "1.2.4", "1.2.3", "1.2.2", "1.2.1", "1.2.0", "1.1.1", "1.1.0", "1.0.8", "1.0.7", "1.0.6", "1.0.5", "1.0.4", "1.0.3", "1.0.2", "1.0.1", "1.0.0")
        for version in versions:
            self.assertIn(f">{version}<", history)
        self.assertLess(history.index(">1.2.9<"), history.index(">1.2.8<"))
        self.assertLess(history.index(">1.2.8<"), history.index(">1.2.7<"))
        self.assertLess(history.index(">1.2.7<"), history.index(">1.2.6<"))
        self.assertLess(history.index(">1.2.6<"), history.index(">1.2.5<"))
        self.assertLess(history.index(">1.2.5<"), history.index(">1.2.4<"))
        self.assertLess(history.index(">1.2.4<"), history.index(">1.2.3<"))
        self.assertLess(history.index(">1.2.3<"), history.index(">1.2.2<"))
        self.assertLess(history.index(">1.2.2<"), history.index(">1.2.1<"))
        self.assertLess(history.index(">1.2.1<"), history.index(">1.2.0<"))
        self.assertLess(history.index(">1.2.0<"), history.index(">1.1.1<"))
        self.assertLess(history.index(">1.1.1<"), history.index(">1.1.0<"))
        self.assertLess(history.index(">1.1.0<"), history.index(">1.0.8<"))
        self.assertLess(history.index(">1.0.8<"), history.index(">1.0.7<"))
        self.assertLess(history.index(">1.0.7<"), history.index(">1.0.0<"))
        self.assertIn("DBG_SWEN", history)
        self.assertIn("USBPRE", history)
        self.assertIn("1.0.0-rc.8", history)
        if language == "zh":
            self.assertIn("版本与修订", history)
            self.assertIn("主题索引", html.split('id="contents"', 1)[1].split('id="part-p0"', 1)[0])
        else:
            self.assertIn("Version history", history)
            self.assertIn("Subject index", html.split('id="contents"', 1)[1].split('id="part-p0"', 1)[0])
        contents = html.split('id="contents"', 1)[1].split('id="part-p0"', 1)[0]
        self.assertIn('href="#version-history"', contents)
        self.assertIn('href="#subject-index"', contents)

        index_html = html.split('id="subject-index"', 1)[1]
        self.assertGreaterEqual(index_html.count('class="index-entry"'), 60)
        self.assertGreaterEqual(len(re.findall(r'class="index-letter">[A-Z]<', index_html)), 8)
        for marker in ("GPIO", "NVIC", "DMA", "BRR", "CFSR", "FreeRTOS", "lwIP", "USBPRE", "DBG_SWEN"):
            self.assertIn(marker, index_html)
        for chapter in ("03", "06", "10", "15", "17", "23", "27"):
            self.assertIn(f'href="#ch{chapter}-', index_html)

    def test_revision_file_lists_1_0_0_through_manifest_version(self) -> None:
        revisions = json.loads((BOOK_DIR / "revisions.json").read_text(encoding="utf-8"))
        versions = [entry["version"] for entry in revisions["entries"]]
        self.assertEqual(
            ["1.2.9", "1.2.8", "1.2.7", "1.2.6", "1.2.5", "1.2.4", "1.2.3", "1.2.2", "1.2.1", "1.2.0", "1.1.1", "1.1.0", "1.0.8", "1.0.7", "1.0.6", "1.0.5", "1.0.4", "1.0.3", "1.0.2", "1.0.1", "1.0.0"],
            versions,
        )
        self.assertEqual(versions[0], self.manifest["version"])
        english = json.loads((BOOK_DIR / "manifest-en.json").read_text(encoding="utf-8"))
        self.assertEqual(versions[0], english["version"])
        index = json.loads((BOOK_DIR / "subject-index.json").read_text(encoding="utf-8"))
        keys = [entry["key"] for entry in index["entries"]]
        self.assertGreaterEqual(len(keys), 60)
        self.assertEqual(len(keys), len(set(keys)))
        for key in ("gpio", "nvic", "dma", "brr", "cfsr", "freertos", "lwip", "usbpre", "dbg-swen"):
            self.assertIn(key, keys)
        for entry in index["entries"]:
            for language in ("zh", "en"):
                term = entry[language]["term"]
                letter = re.search(r"[A-Za-z]", term)
                self.assertIsNotNone(letter, entry["key"])
                self.assertEqual(entry["letter"], letter.group(0).upper(), entry["key"])
        titles = {item["id"]: item["title"] for item in self.manifest["back_matter"]}
        self.assertEqual("主题索引", titles["subject-index"])
        english_titles = {item["id"]: item["title"] for item in english["back_matter"]}
        self.assertEqual("Subject index", english_titles["subject-index"])

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
        self.assertIn("<strong>v1.2.9</strong>", html)
        self.assertNotIn("<strong>v1.0.0-rc", html)
        self.assert_version_history_and_index(html, "zh")
        self.assertIn('<p class="part-label">第 1 部</p>', html)
        self.assertIn('id="chapter-00" data-chapter="00"', html)
        self.assertIn('id="chapter-28" data-chapter="28"', html)
        self.assertIn('<span class="chapter-number">第 1 章</span><h1>如何学习 STM32</h1>', html)
        self.assertIn(
            'href="#chapter-00">第 1 章 如何学习 STM32</a>',
            html,
        )
        self.assertIn(
            'href="#chapter-28">第 29 章 嵌入式系统与 RTOS 生态：FreeRTOS、RT-Thread、Zephyr</a>',
            html,
        )
        self.assertNotIn('<span class="chapter-number">第 00 章</span>', html)
        self.assertNotIn('href="#chapter-00">00 ', html)
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
        self.assertNotIn(">00 如何学习 STM32</h1>", html)
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
        self.assertEqual("1.2.9", manifest["version"])
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
        self.assertIn("<strong>v1.2.9</strong>", html)
        self.assertNotIn("<strong>v1.0.0-rc", html)
        self.assert_version_history_and_index(html, "en")
        self.assertIn('<p class="part-label">Part 1</p>', html)
        self.assertIn('id="chapter-00" data-chapter="00"', html)
        self.assertIn('id="chapter-28" data-chapter="28"', html)
        self.assertIn('<span class="chapter-number">Chapter 1</span><h1>How to Learn STM32</h1>', html)
        self.assertIn('href="#chapter-00">Chapter 1 How to Learn STM32</a>', html)
        self.assertIn(
            'href="#chapter-28">Chapter 29 Embedded systems and the RTOS ecosystem: FreeRTOS, RT-Thread, and Zephyr</a>',
            html,
        )
        self.assertNotIn('<span class="chapter-number">Chapter 00</span>', html)
        self.assertNotIn('href="#chapter-00">00 ', html)
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

    def _exploded_heading_outline(self, manifest: dict) -> list[list]:
        toc: list[list] = []
        for _level, _label, source in self.builder.outline_lookup_headings(manifest):
            toc.append([1, source, 2])
            for number in range(8):
                toc.append([2, f"{source} section {number}", 3])
                toc.append([3, f"{source} detail {number}", 3])
        return toc

    def test_publication_outline_keeps_parts_chapters_and_appendices(self) -> None:
        import fitz

        for manifest_name in ("manifest.json", "manifest-en.json"):
            manifest = json.loads((BOOK_DIR / manifest_name).read_text(encoding="utf-8"))
            fat = self._exploded_heading_outline(manifest)
            self.assertGreater(len(fat), 600)
            outline = self.builder.publication_outline(manifest, fat)
            self.assertEqual(44, len(outline))
            self.assertTrue(all(item[0] <= 2 for item in outline))
            self.assertFalse(any(item[0] >= 3 for item in outline))
            titles = [item[1] for item in outline]
            self.assertFalse(any(re.match(r"^\d{2}\s", title) for title in titles))
            self.assertLess(len(outline), 80)
            if str(manifest["language"]).lower().startswith("zh"):
                self.assertIn("第 1 章 如何学习 STM32", titles)
                self.assertTrue(any(title.startswith("第 29 章 ") for title in titles))
                self.assertIn("版本与修订", titles)
                self.assertIn("主题索引", titles)
                self.assertTrue(any(title.startswith("附录 A") for title in titles))
                chapter_prefix = "第 1 章"
            else:
                self.assertIn("Chapter 1 How to Learn STM32", titles)
                self.assertTrue(any(title.startswith("Chapter 29 ") for title in titles))
                self.assertIn("Version history", titles)
                self.assertIn("Subject index", titles)
                self.assertTrue(any(title.startswith("Appendix A") for title in titles))
                chapter_prefix = "Chapter 1 "
            part = manifest["parts"][0]["title"]
            part_at = next(index for index, item in enumerate(outline) if item[1] == part)
            self.assertEqual(1, outline[part_at][0])
            self.assertEqual(2, outline[part_at + 1][0])
            self.assertTrue(outline[part_at + 1][1].startswith(chapter_prefix))
            self.assertIsNotNone(self.builder._CHAPTER_RUNNING_TITLE.fullmatch(outline[part_at + 1][1]))
            self.assertIsNone(self.builder._CHAPTER_RUNNING_TITLE.fullmatch(part))

            with tempfile.TemporaryDirectory() as tmp:
                raw = Path(tmp) / "raw.pdf"
                output = Path(tmp) / "book.pdf"
                document = fitz.open()
                for _ in range(4):
                    document.new_page()
                document.set_toc(fat)
                document.save(raw)
                document.close()
                self.builder._stamp_page_numbers(
                    raw,
                    output,
                    {
                        "title": manifest["title"],
                        "author": manifest["author"],
                        "subject": manifest["subtitle"],
                        "keywords": manifest["keywords"],
                    },
                    manifest,
                )
                stamped = fitz.open(output)
                try:
                    toc = stamped.get_toc()
                finally:
                    stamped.close()
            self.assertEqual([item[:3] for item in outline], [item[:3] for item in toc])
            self.assertTrue(all(item[0] <= 2 for item in toc))
            self.assertLess(len(toc), 80)

            wrapped = [
                [level, source.replace(" ", ""), 2]
                for level, _label, source in self.builder.outline_lookup_headings(manifest)
            ]
            recovered = self.builder.publication_outline(manifest, wrapped)
            self.assertEqual([item[1] for item in outline], [item[1] for item in recovered])

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

    def test_pdf_stamping_adds_index_page_numbers_beside_entries(self) -> None:
        import fitz

        metadata = {"title": "STM32 实战", "author": "作者", "subject": "主题", "keywords": "STM32"}
        with tempfile.TemporaryDirectory() as tmp:
            raw = Path(tmp) / "raw.pdf"
            output = Path(tmp) / "book.pdf"
            document = fitz.open()
            document.new_page()  # cover
            document.new_page()  # index
            document.new_page()  # target section
            index = document[1]
            index.insert_text((50, 50), "这是书末主题索引", fontname="china-s", fontsize=12)
            index.insert_text((50, 90), "ADC · 09 分辨率", fontname="china-s", fontsize=9)
            index.insert_link({"kind": fitz.LINK_GOTO, "from": fitz.Rect(48, 76, 180, 96), "page": 2})
            document.save(raw)
            document.close()

            self.builder._stamp_page_numbers(raw, output, metadata)
            stamped = fitz.open(output)
            try:
                words = stamped[1].get_text("words")
            finally:
                stamped.close()

        page_numbers = [word for word in words if word[4] == "2" and word[0] > 400]
        self.assertEqual(1, len(page_numbers))

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

    def _css_rule(self, css: str, selector: str) -> str:
        match = re.search(rf"{re.escape(selector)}\s*\{{([^}}]*)\}}", css)
        self.assertIsNotNone(match, selector)
        return match.group(1)

    def test_visual_polish_css_contract(self) -> None:
        css = self.builder.CSS
        screen = css.split("@media", 1)[0]
        dark = css.split("@media (prefers-color-scheme: dark)", 1)[1].split("@media", 1)[0]
        printed = css.split("@media print", 1)[1]
        narrow = css.split("@media (max-width: 720px)", 1)[1].split("@media", 1)[0]

        for token in (
            "--paper: #fbfaf7",
            "--ink: #17202a",
            "--accent: #075e84",
            "--muted: #5e6872",
            "--warn: #9a3d1c",
            "--tip: #1b5c45",
            "--spine: #c4552a",
            "--space-bar: 0.625rem",
            "--space-paragraph: 1rem",
            "--space-figure: 1.25rem",
            "--space-chapter: 2.75rem",
            "--inset: 4.5%",
            "--leading-body: 1.65",
            "--measure: 42rem",
            "--tracking-body: 0.01em",
            "--tracking-kicker: 0.14em",
            "--radius: 0.7rem",
            "--elev: 0 1px 2px color-mix(in srgb, var(--ink) 8%, transparent)",
        ):
            self.assertIn(token, screen)

        self.assertIn("line-height: var(--leading-body)", self._css_rule(screen, "body"))
        paragraphs = self._css_rule(screen, ".chapter > p, .appendix > p, .part-closing > p")
        self.assertIn("margin-top: var(--space-paragraph)", paragraphs)
        self.assertIn("margin-bottom: var(--space-paragraph)", paragraphs)
        self.assertIn("letter-spacing: var(--tracking-body)", paragraphs)
        headings = self._css_rule(screen, ".chapter > h2, .appendix > h2, .part-closing > h2")
        self.assertIn("border-left: 3px solid var(--accent)", headings)
        self.assertIn("padding-left: var(--space-bar)", headings)
        self.assertIn(
            "margin: calc(var(--space-figure) + var(--space-paragraph)) 0 var(--space-bar)",
            headings,
        )
        self.assertNotIn("padding-left: var(--space-bar)", self._css_rule(screen, ".source-card h2"))

        for selector in (
            ".chapter-compass",
            "blockquote.callout",
            ".source-card",
            "figure",
            ".quick-check",
            ".companion",
            ".route",
        ):
            block = self._css_rule(screen, selector)
            self.assertIn("border-radius: var(--radius)", block, selector)
            self.assertIn("box-shadow: var(--elev)", block, selector)
            self.assertIn("border: 1px solid var(--line)", block, selector)
        figure = self._css_rule(screen, "figure")
        self.assertIn("margin: var(--space-figure) auto", figure)
        self.assertIn("color-mix(in srgb, var(--panel) 70%, var(--paper))", figure)
        self.assertIn("margin: var(--space-figure) auto", self._css_rule(screen, "img"))
        self.assertIn("margin: 0 auto .4rem", self._css_rule(screen, "figure img"))
        self.assertIn("border-left: 4px solid var(--accent)", self._css_rule(screen, "blockquote.callout"))
        pre = self._css_rule(screen, "pre")
        self.assertIn("border-radius: var(--radius)", pre)
        self.assertNotIn("box-shadow", pre)
        self.assertIn("border-left: 3px solid var(--accent)", pre)
        self.assertIn("tab-size: 4", pre)
        self.assertIn("user-select: text", pre)

        divider = self._css_rule(screen, ".part-divider")
        self.assertIn("padding: 4.5rem var(--inset) 4.5rem", divider)
        self.assertIn("margin-top: var(--space-chapter)", divider)
        self.assertIn("min-height: 52vh", divider)
        self.assertNotIn("border-radius", divider)
        self.assertNotIn("--elev", divider)
        self.assertIn("border-top: 4px solid var(--accent)", divider)

        self.assertIn("color: var(--warn)", self._css_rule(screen, ".closing-banner"))
        self.assertIn("color: var(--warn)", self._css_rule(screen, ".compass-boundary .compass-role"))
        self.assertIn("border-top-color: var(--spine)", self._css_rule(screen, ".compass-boundary"))
        self.assertNotRegex(css, r"letter-spacing:\s*\.(?:12|14|16|18)em")
        self.assertIn("letter-spacing: .04em", css)
        self.assertIn("text-underline-offset: .18em", css)
        self.assertIn("box-shadow: 0 .45rem 1.2rem rgba(16, 24, 32, .18)", css)
        self.assertIn("border-radius: .5rem", self._css_rule(screen, ".compass-card"))

        cover = self._css_rule(screen, ".cover")
        self.assertIn("background: #10242e", cover)
        self.assertIn("color: #f4f1ea", cover)
        for token in (
            "--paper: #fbfaf7",
            "--ink: #17202a",
            "--muted: #5e6872",
            "--warn: #9a3d1c",
            "--line: #d7dce1",
            "--spine: #c4552a",
        ):
            self.assertIn(token, cover)
        panel = self._css_rule(screen, ".cover-panel")
        self.assertIn("background: var(--paper)", panel)
        self.assertIn("color: var(--ink)", panel)
        self.assertIn("padding: 1.8rem 6% 2.6rem", panel)
        self.assertIn("background: var(--spine)", self._css_rule(screen, ".cover-panel::before"))
        self.assertIn("background: var(--spine)", self._css_rule(screen, ".cover .rule"))
        self.assertIn("color: var(--warn)", self._css_rule(screen, ".cover .eyebrow"))
        self.assertIn("color: var(--ink)", self._css_rule(screen, ".cover h1"))
        self.assertIn("color: var(--ink)", self._css_rule(screen, ".cover .subtitle"))
        self.assertIn("color: var(--muted)", self._css_rule(screen, ".cover .edition"))
        self.assertIn("color: var(--muted)", self._css_rule(screen, ".cover .edition strong"))
        self.assertIn("border-top: 1px solid var(--line)", self._css_rule(screen, ".cover .edition"))
        self.assertIn("background: #0c1c24", self._css_rule(screen, ".cover-art"))
        for gone in ("#f7f4ee", "#d7d0c4", "#5c6570", "#24323c"):
            self.assertNotIn(gone, css)

        self.assertIn(".cover-panel { padding: 1.3rem 1rem 1.8rem; }", narrow)
        self.assertNotIn("var(--inset)", narrow)
        self.assertIn("padding-left: 1rem; padding-right: 1rem", narrow)

        for token in (
            "--paper: #11171b",
            "--ink: #e9eef1",
            "--accent: #78c8e8",
            "--muted: #acb7bf",
            "--warn: #f0b090",
            "--tip: #8fd4b4",
            "--spine: #f0b090",
        ):
            self.assertIn(token, dark)

        self.assertIn("orphans: 3", printed)
        self.assertIn("widows: 3", printed)
        self.assertIn("--spine: #c4552a", printed)
        self.assertIn("--paper: #fff", printed)
        self.assertIn("--ink: #111", printed)
        self.assertIn("--muted: #444", printed)
        self.assertIn("--accent: #075e84", printed)
        self.assertIn("figure { background: transparent; }", printed)
        self.assertIn("@page { size: A4; margin: 16mm 15mm 18mm; }", printed)
        self.assertIn("h1, h2, h3, h4 { break-after: avoid-page; page-break-after: avoid; }", printed)
        caption = self._css_rule(printed, "figcaption")
        self.assertIn("break-before: avoid-page", caption)
        self.assertIn("page-break-before: avoid", caption)
        self.assertIn("break-inside: avoid-page", caption)
        self.assertIn("page-break-inside: avoid", caption)
        self.assertIn("box-shadow: none", self._css_rule(
            printed,
            ".chapter-compass,\n  blockquote.callout,\n  .source-card,\n  figure,\n  .quick-check,\n  .companion,\n  .route",
        ))
        pre_print = self._css_rule(printed, "pre")
        self.assertIn("white-space: pre-wrap", pre_print)
        self.assertIn("break-inside: auto", pre_print)
        self.assertNotIn("avoid", pre_print)
        self.assertIn(".imprint { break-before: auto; page-break-before: auto; }", printed)

    def test_visual_polish_contrast_clears_4_5(self) -> None:
        # spine 对纸色不在这张表里。#c4552a 对 #fbfaf7 约 4.30，规格不把它当正文门槛。
        pairs = (
            ("#17202a", "#fbfaf7"),
            ("#075e84", "#fbfaf7"),
            ("#5e6872", "#fbfaf7"),
            ("#9a3d1c", "#fbfaf7"),
            ("#1b5c45", "#fbfaf7"),
            ("#e9eef1", "#11171b"),
            ("#78c8e8", "#11171b"),
            ("#acb7bf", "#11171b"),
            ("#f0b090", "#11171b"),
            ("#8fd4b4", "#11171b"),
            ("#111", "#fff"),
            ("#075e84", "#fff"),
            ("#444", "#fff"),
            ("#eef6f8", "#101820"),
            ("#edf6f9", "#0a141c"),
            ("#111", "#f6f6f6"),
            ("#075e84", "#e5f3f8"),
        )
        for foreground, background in pairs:
            with self.subTest(foreground=foreground, background=background):
                self.assertGreaterEqual(_contrast_ratio(foreground, background), 4.5)

    def test_typography_e_css_contract(self) -> None:
        css = self.builder.CSS
        screen = css.split("@media", 1)[0]
        dark = css.split("@media (prefers-color-scheme: dark)", 1)[1].split("@media", 1)[0]
        printed = css.split("@media print", 1)[1]
        narrow = css.split("@media (max-width: 720px)", 1)[1].split("@media", 1)[0]

        def custom_value(block: str, name: str) -> str:
            match = re.search(rf"{re.escape(name)}:\s*([^;]+);", block)
            self.assertIsNotNone(match, name)
            return match.group(1).strip()

        for token in (
            "--font-sans:",
            "--font-mono:",
            "--type-body: 1.0625rem",
            "--type-h1: clamp(1.85rem, 4.2vw, 2.7rem)",
            "--type-h2: 1.55rem",
            "--type-h3: 1.35rem",
            "--type-h4: 1.2rem",
            "--type-kicker: 0.78rem",
            "--type-small: 0.9375rem",
            "--type-code: 0.92em",
            "--leading-heading: 1.35",
            "--leading-caption: 1.55",
            "--leading-toc: 1.45",
            "--leading-code: 1.65",
        ):
            self.assertIn(token, screen, token)

        sans = custom_value(screen, "--font-sans")
        self.assertTrue(
            sans.startswith('"Noto Sans CJK SC", "Microsoft YaHei", "PingFang SC"'),
            sans,
        )
        for face in ('"Noto Sans SC"', '"Source Han Sans SC"', '"Segoe UI"'):
            self.assertIn(face, sans)
        mono = custom_value(screen, "--font-mono")
        self.assertTrue(
            mono.startswith('"Cascadia Mono", "SFMono-Regular", Consolas'),
            mono,
        )
        for face in (
            '"Noto Sans Mono CJK SC"',
            '"Source Han Mono SC"',
            '"Sarasa Mono SC"',
            '"Liberation Mono"',
            "ui-monospace",
        ):
            self.assertIn(face, mono)

        self.assertIn("font-family: var(--font-sans)", self._css_rule(screen, ":root"))
        self.assertNotIn("font-size", self._css_rule(screen, "html"))
        self.assertIn("font-size: var(--type-body)", self._css_rule(screen, "body"))
        self.assertIn("line-height: var(--leading-body)", self._css_rule(screen, "body"))
        self.assertNotIn("--font-sans", dark)
        self.assertNotIn("--type-body", dark)
        self.assertIn("--code: #0a141c", dark)
        self.assertIn("--code-ink: #edf6f9", dark)
        self.assertIn("--code: #101820", screen)
        self.assertIn("--code-ink: #eef6f8", screen)

        code_rule = re.search(r"(?m)^code\s*\{([^}]*)\}", screen)
        self.assertIsNotNone(code_rule)
        self.assertIn("font-family: var(--font-mono)", code_rule.group(1))
        self.assertIn("font-size: var(--type-code)", code_rule.group(1))
        pre_code = self._css_rule(screen, "pre code")
        self.assertNotIn("font-size", pre_code)
        self.assertIn("color: inherit", pre_code)
        self.assertIn("background: transparent", pre_code)
        self.assertIn("padding: 0", pre_code)
        self.assertIn("white-space: inherit", pre_code)
        self.assertIn("user-select: text", pre_code)

        inline = self._css_rule(screen, ":not(pre) > code")
        self.assertIn("color-mix(in srgb, var(--accent) 18%, var(--paper))", inline)
        self.assertIn("padding: .12em .35em", inline)
        self.assertIn("border-radius: .3em", inline)
        names = [part.split(":", 1)[0].strip() for part in inline.split(";") if part.strip()]
        self.assertNotIn("border", names)
        self.assertIn("border-radius", names)
        self.assertIn("background: var(--accent-soft)", self._css_rule(screen, ".source-id code"))

        pre = self._css_rule(screen, "pre")
        self.assertIn("line-height: var(--leading-code)", pre)
        self.assertIn("margin: var(--space-paragraph) 0 var(--space-figure)", pre)
        self.assertIn("border-left: 3px solid var(--accent)", pre)
        self.assertIn("border-radius: var(--radius)", pre)
        self.assertIn("tab-size: 4", pre)
        self.assertIn("user-select: text", pre)
        self.assertNotIn("box-shadow", pre)

        for selector in ("figcaption", "sub"):
            block = self._css_rule(screen, selector)
            self.assertIn("font-size: var(--type-small)", block, selector)
            self.assertIn("line-height: var(--leading-caption)", block, selector)
        self.assertIn("margin: 0 auto .4rem", self._css_rule(screen, "figure img"))
        self.assertIn("font-size: var(--type-small)", self._css_rule(screen, "table"))
        self.assertIn("font-size: var(--type-small)", self._css_rule(screen, ".source-card dl"))

        self.assertIn("line-height: var(--leading-toc)", self._css_rule(screen, ".contents li"))
        self.assertIn("margin: .2rem 0", self._css_rule(screen, ".contents li"))
        self.assertIn("break-inside: avoid", self._css_rule(screen, ".contents li"))
        goal = self._css_rule(screen, ".contents > section > p:not(.toc-closing)")
        self.assertIn("color: var(--muted)", goal)
        self.assertIn("font-size: var(--type-small)", goal)
        self.assertIn("line-height: var(--leading-caption)", goal)
        self.assertIn("max-width: var(--measure)", goal)
        closing = self._css_rule(screen, ".toc-closing")
        self.assertIn("border-top: 1px solid var(--line)", closing)
        self.assertIn("margin: var(--space-bar) 0 0", closing)
        self.assertIn("font-weight: 700", closing)
        self.assertNotIn("font-size", closing)
        contents_h2 = self._css_rule(screen, ".contents > section > h2")
        self.assertIn("font-size: var(--type-h3)", contents_h2)
        self.assertIn("line-height: var(--leading-heading)", contents_h2)
        self.assertIn("position: sticky", contents_h2)
        self.assertIn("background: var(--paper)", contents_h2)
        self.assertIn("box-shadow: 0 1px 0 var(--line)", contents_h2)
        self.assertIn("columns: 2", self._css_rule(screen, ".contents ol"))
        self.assertIn("column-gap: 2.25rem", self._css_rule(screen, ".contents ol"))
        self.assertIn("columns: 1", self._css_rule(narrow, ".contents ol"))

        self.assertIn(
            "h2, h3, h4 { line-height: var(--leading-heading); scroll-margin-top: 1.25rem; }",
            screen,
        )
        self.assertIn(
            "h2 { font-size: var(--type-h2); margin: calc(var(--space-figure) + var(--space-paragraph)) 0 var(--space-bar); }",
            screen,
        )
        self.assertIn(
            "h3 { font-size: var(--type-h3); margin: var(--space-figure) 0 calc(var(--space-bar) / 2); }",
            screen,
        )
        self.assertIn(
            "h4 { font-size: var(--type-h4); margin: var(--space-paragraph) 0 calc(var(--space-bar) / 2); }",
            screen,
        )
        self.assertIn(
            ".chapter > h2, .appendix > h2, .part-closing > h2 { margin: calc(var(--space-figure) + var(--space-paragraph)) 0 var(--space-bar); padding-left: var(--space-bar); border-left: 3px solid var(--accent); }",
            screen,
        )
        self.assertIn(
            ".chapter > header h1, .appendix > header h1, .part-closing > header h1, .back-matter > header h1 { font-size: var(--type-h1); line-height: 1.22; margin: .28em 0 0; max-width: 18em; }",
            screen,
        )
        self.assertIn("font-size: var(--type-h4)", self._css_rule(screen, ".quick-title"))
        source_h2 = self._css_rule(screen, ".source-card h2")
        self.assertIn("font-size: var(--type-h4)", source_h2)
        self.assertIn("line-height: var(--leading-heading)", source_h2)
        self.assertIn("margin: 0 0 .3rem", source_h2)
        self.assertNotIn("padding-left", source_h2)
        self.assertIn("margin-top: 0", self._css_rule(screen, ".imprint h1, .companion h2"))

        for selector in (
            ".compass-role",
            ".callout-label",
            ".source-card dt",
            ".part-label",
            ".cover .eyebrow",
            ".closing-banner",
            ".chapter-number",
            ".compass-title",
            ".source-id",
            ".imprint .kicker",
            ".index-letter",
            ".revision-history .kicker, .subject-index .kicker",
        ):
            self.assertIn("font-size: var(--type-kicker)", self._css_rule(screen, selector), selector)
        self.assertIn("letter-spacing: .04em", self._css_rule(screen, ".source-id"))
        self.assertIn("letter-spacing: .04em", self._css_rule(screen, ".source-card dt"))

        self.assertIn("clamp(2.15rem, 5.6vw, 3.7rem)", self._css_rule(screen, ".cover h1"))
        self.assertIn("clamp(1.05rem, 2.4vw, 1.35rem)", self._css_rule(screen, ".cover .subtitle"))
        self.assertIn("clamp(2rem, 5vw, 3.35rem)", self._css_rule(screen, ".part-divider h1"))
        part_goal = self._css_rule(screen, ".part-goal")
        self.assertIn("font-size: 1.12rem", part_goal)
        self.assertIn("line-height: 1.6", part_goal)
        self.assertIn("clamp(4.5rem, 14vw, 8.5rem)", self._css_rule(screen, ".part-index"))
        self.assertIn("font-size: 3rem", self._css_rule(narrow, ".part-index"))
        jump = self._css_rule(screen, ".toc-jump")
        self.assertIn("font-size: .85rem", jump)
        self.assertIn("box-shadow: 0 .45rem 1.2rem rgba(16, 24, 32, .18)", jump)
        self.assertIn(".book { width: min(100% - 2rem, 980px); margin: 0 auto; }", screen)
        self.assertIn(".book { width: min(100% - 1rem, 980px); }", narrow)

        for retired in (
            "font-size: .72rem",
            "font-size: .74rem",
            "font-size: .75rem",
            "font-size: .78rem",
            "font-size: .82rem",
            "font-size: .88rem",
            "font-size: .9rem",
            "font-size: .91em",
            "font-size: .92em",
            "font-size: .94rem",
            "font-size: 1.02rem",
            "font-size: 1.05rem",
            "font-size: 1.16rem",
            "font-size: 1.42rem",
            "margin: 2.35rem 0 .6rem",
            "line-height: 1.35;",
            "line-height: 1.45;",
        ):
            self.assertNotIn(retired, screen, retired)

        self.assertNotIn("@font-face", css)
        self.assertNotIn("url(", css)

        print_root = self._css_rule(printed, ":root")
        self.assertIn("--code: #f6f6f6", print_root)
        self.assertIn("--code-ink: #111", print_root)
        self.assertNotIn("--font-sans", printed)
        self.assertNotIn("--type-body", printed)
        self.assertIn("font-size: 9.5pt; line-height: 1.55", printed)
        pre_print = self._css_rule(printed, "pre")
        self.assertIn("line-height: 1.45", pre_print)
        self.assertIn("white-space: pre-wrap", pre_print)
        self.assertIn("overflow-wrap: anywhere", pre_print)
        self.assertIn("break-inside: auto", pre_print)
        self.assertIn("page-break-inside: auto", pre_print)
        self.assertNotIn("avoid", pre_print)
        caption = self._css_rule(printed, "figcaption")
        self.assertIn("font-size: 9pt", caption)
        self.assertIn("line-height: 1.4", caption)
        self.assertIn("break-before: avoid-page", caption)
        self.assertIn("page-break-before: avoid", caption)
        self.assertIn("break-inside: avoid-page", caption)
        self.assertIn("page-break-inside: avoid", caption)
        printed_sub = self._css_rule(printed, "sub")
        self.assertIn("font-size: 9pt", printed_sub)
        self.assertIn("line-height: 1.4", printed_sub)
        self.assertIn("position: static", self._css_rule(printed, ".contents > section > h2"))
        self.assertIn("figure { background: transparent; }", printed)
        self.assertIn("@page { size: A4; margin: 16mm 15mm 18mm; }", printed)

    def test_css_token_extract_contract(self) -> None:
        tokens_path = BOOK_DIR / "styles" / "tokens.json"
        css_path = BOOK_DIR / "styles" / "book.css"
        self.assertTrue(tokens_path.is_file(), tokens_path)
        self.assertTrue(css_path.is_file(), css_path)
        raw_tokens = tokens_path.read_bytes()
        self.assertFalse(raw_tokens.startswith(b"\xef\xbb\xbf"), "tokens.json BOM")
        token_text = raw_tokens.decode("utf-8")
        self.assertTrue(token_text.endswith("\n"))
        tokens = json.loads(token_text)
        self.assertEqual(
            ["schema", "light", "dark", "print", "coverLock"],
            list(tokens),
        )
        self.assertIs(type(tokens["schema"]), int)
        self.assertEqual(1, tokens["schema"])
        self.assertEqual(list(_TOKEN_LIGHT_KEYS), list(tokens["light"]))
        self.assertEqual(list(_TOKEN_COLOR_KEYS), list(tokens["dark"]))
        self.assertEqual(list(_TOKEN_COLOR_KEYS), list(tokens["print"]))
        self.assertEqual(list(_TOKEN_COVER_LOCK), tokens["coverLock"])

        css_source = css_path.read_text(encoding="utf-8")
        self.assertTrue(css_source.startswith("\n"))
        for sentinel in (
            "  /* @tokens light */",
            "  /* @tokens dark */",
            "/* @tokens print */",
            "  /* @tokens cover */",
        ):
            self.assertEqual(1, css_source.count(sentinel), sentinel)
        self.assertIn(
            "  color-scheme: light dark;\n  /* @tokens light */\n  font-family: var(--font-sans);",
            css_source,
        )
        self.assertIn(
            "@media (prefers-color-scheme: dark) {\n  /* @tokens dark */\n}",
            css_source,
        )
        self.assertIn(
            "  :root { color-scheme: light; /* @tokens print */ }",
            css_source,
        )
        self.assertIn(
            "  background: #10242e;\n  color: #f4f1ea;\n  /* @tokens cover */\n",
            css_source,
        )
        names = set(tokens["light"]) | set(tokens["dark"]) | set(tokens["print"])
        for name in names:
            self.assertNotIn(f"{name}:", css_source, name)
        self.assertEqual(
            {"#10242e", "#f4f1ea", "#0c1c24"},
            set(re.findall(r"#[0-9A-Fa-f]{3,8}", css_source)),
        )
        self.assertIn("rgba(16, 24, 32, .18)", css_source)
        self.assertIn("--table-columns", css_source)
        self.assertNotIn("@font-face", css_source)
        self.assertNotIn("url(", css_source)

        self.assertEqual(
            ("tokens_path", "css_path"),
            tuple(inspect.signature(self.builder.load_css).parameters),
        )
        self.assertIsInstance(self.builder.CSS, str)
        self.assertEqual(self.builder.load_css(), self.builder.CSS)
        self.assertEqual(
            "aacd30dcb0efbff80d004295338c9be99b35e19cb744d6f4b1e662a0b8f31baf",
            hashlib.sha256(self.builder.CSS.encode("utf-8")).hexdigest(),
        )
        css = self.builder.CSS
        self.assertNotIn("/* @tokens", css)
        medias = [item.strip() for item in re.findall(r"@media[^{]+", css)]
        self.assertEqual(
            [
                "@media (max-width: 960px)",
                "@media (max-width: 720px)",
                "@media (prefers-color-scheme: dark)",
                "@media (prefers-reduced-motion: reduce)",
                "@media print",
            ],
            medias,
        )
        screen = css.split("@media", 1)[0]
        dark = css.split("@media (prefers-color-scheme: dark)", 1)[1].split("@media", 1)[0]
        printed = css.split("@media print", 1)[1]
        for name, value in tokens["light"].items():
            self.assertIn(f"{name}: {value}", screen, name)
        for name, value in tokens["dark"].items():
            self.assertIn(f"{name}: {value}", dark, name)
        print_root = self._css_rule(printed, ":root")
        for name, value in tokens["print"].items():
            self.assertIn(f"{name}: {value}", print_root, name)
        cover = self._css_rule(screen, ".cover")
        for name in tokens["coverLock"]:
            self.assertIn(f"{name}: {tokens['light'][name]}", cover, name)

        def embedded(html: str) -> None:
            self.assertEqual(1, html.count("<style>"))
            self.assertEqual(1, html.count("</style>"))
            self.assertNotIn("<link", html)
            inner = html.split("<style>", 1)[1].split("</style>", 1)[0]
            self.assertEqual(self.builder.CSS, inner)
            self.assertNotIn("fonts.googleapis", html)
            self.assertNotIn("fonts.gstatic", html)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            chinese = self.builder.build_html(root / "zh")
            english = self.builder.build_html(root / "en", BOOK_DIR / "manifest-en.json")
            embedded(chinese.read_text(encoding="utf-8"))
            embedded(english.read_text(encoding="utf-8"))

    def test_css_token_extract_rejects_bad_tokens(self) -> None:
        before = self.builder.CSS

        def legal() -> dict:
            light = {key: "1" for key in _TOKEN_LIGHT_KEYS}
            colors = {key: "1" for key in _TOKEN_COLOR_KEYS}
            return {
                "schema": 1,
                "light": light,
                "dark": dict(colors),
                "print": dict(colors),
                "coverLock": list(_TOKEN_COVER_LOCK),
            }

        sheet = (
            "\n:root {\n"
            "  color-scheme: light dark;\n"
            "  /* @tokens light */\n"
            "  font-family: var(--font-sans);\n"
            "}\n"
            ".cover {\n"
            "  background: #10242e;\n"
            "  color: #f4f1ea;\n"
            "  /* @tokens cover */\n"
            "}\n"
            "@media (prefers-color-scheme: dark) {\n"
            "  /* @tokens dark */\n"
            "}\n"
            "@media print {\n"
            "  :root { color-scheme: light; /* @tokens print */ }\n"
            "}\n"
        )

        def write_pair(directory: Path, document: str) -> tuple[Path, Path]:
            directory.mkdir(parents=True, exist_ok=True)
            tokens_path = directory / "tokens.json"
            css_path = directory / "book.css"
            tokens_path.write_text(document, encoding="utf-8", newline="\n")
            css_path.write_text(sheet, encoding="utf-8", newline="\n")
            return tokens_path, css_path

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing = legal()
            del missing["light"]["--ink"]
            tokens_path, css_path = write_pair(
                root / "missing",
                json.dumps(missing, indent=2, ensure_ascii=False) + "\n",
            )
            with self.assertRaisesRegex(self.builder.BuildError, "--ink"):
                self.builder.load_css(tokens_path, css_path)

            poisoned = legal()
            poisoned["light"]["--paper"] = "url("
            tokens_path, css_path = write_pair(
                root / "url",
                json.dumps(poisoned, indent=2, ensure_ascii=False) + "\n",
            )
            with self.assertRaisesRegex(self.builder.BuildError, r"url\("):
                self.builder.load_css(tokens_path, css_path)

            duplicate = json.dumps(legal(), indent=2, ensure_ascii=False) + "\n"
            duplicate = duplicate.replace(
                '"--paper": "1"',
                '"--paper": "1",\n    "--paper": "#fff"',
                1,
            )
            light_text, _, _rest = duplicate.partition('\n  "dark"')
            self.assertEqual(2, light_text.count('"--paper"'))
            tokens_path, css_path = write_pair(root / "duplicate", duplicate)
            with self.assertRaisesRegex(self.builder.BuildError, "--paper"):
                self.builder.load_css(tokens_path, css_path)

        self.assertIs(before, self.builder.CSS)

    def test_visual_polish_version_is_1_2_0(self) -> None:
        revisions = json.loads((BOOK_DIR / "revisions.json").read_text(encoding="utf-8"))
        english = json.loads((BOOK_DIR / "manifest-en.json").read_text(encoding="utf-8"))
        readme = (BOOK_DIR / "README.md").read_text(encoding="utf-8")
        posters = revisions["entries"][0]
        density = revisions["entries"][1]
        entry = revisions["entries"][2]
        cover = revisions["entries"][3]
        tokens = revisions["entries"][4]
        typography = revisions["entries"][5]
        batch4 = revisions["entries"][6]
        batch3 = revisions["entries"][7]
        guide = revisions["entries"][8]
        previous = revisions["entries"][9]
        self.assertEqual("1.2.9", self.manifest["version"])
        self.assertEqual("2026-10-25", self.manifest["date"])
        self.assertEqual("1.2.9", english["version"])
        self.assertEqual("2026-10-25", english["date"])
        self.assertEqual("1.2.9", posters["version"])
        self.assertEqual("2026-10-25", posters["date"])
        self.assertEqual(posters["date"], self.manifest["date"])
        self.assertEqual(posters["date"], english["date"])
        self.assertEqual(
            [
                "29 张讲解海报按当前完整帧重画：标题下有青条，无插图的卡有小芯，要点用正文色。",
                "样式令牌、封面、样本图和旁白成片不改。",
            ],
            posters["zh"],
        )
        self.assertEqual(
            [
                "The 29 lecture posters are redrawn from the current finished frame: a cyan rule under the title, a mascot on cards without a figure, and bullet text in the body color.",
                "Style tokens, the cover, the sample drawings, and the narrated videos stay.",
            ],
            posters["en"],
        )
        self.assertEqual("1.2.8", density["version"])
        self.assertEqual("2026-10-25", density["date"])
        self.assertEqual(
            [
                "章距、段距、图距、左右页边和正文行高各收一档，行长从 40rem 调到 42rem。字号和颜色不变。",
                "封面标题板的左右页边仍是 6%。暗色和印刷的颜色不改。样本图、封面图和 GIF 不重画。",
            ],
            density["zh"],
        )
        self.assertEqual(
            [
                "Chapter, paragraph, and figure spacing, the side inset, and the body line-height each move one step tighter. The measure moves from 40rem to 42rem. Type size and colors stay.",
                "The cover title plate keeps a 6% side inset. The dark palette and the print palette stay. Sample drawings, the cover drawing, and GIFs are not redrawn.",
            ],
            density["en"],
        )
        self.assertEqual("1.2.7", entry["version"])
        self.assertEqual("2026-10-25", entry["date"])
        self.assertEqual(
            [
                "仓库里的样本图、框图、动画和板卡图改成浅色纸底，语义色与正文的强调色、提示色对齐。描边只留 1、1.5 和 2，圆角只留 2、4 和 8。",
                "封面、样式令牌和章节正文不改。光栅 GIF 仍是原来的深色，不随这批矢量图重画。",
            ],
            entry["zh"],
        )
        self.assertEqual(
            [
                "The sample drawings, diagrams, animations, and board drawings in the repository now use light paper. Their semantic colors line up with the text accent and tip. Strokes are only 1, 1.5, and 2. Corners are only 2, 4, and 8.",
                "The cover, the style tokens, and the chapter text stay as they are. The raster GIFs keep the previous dark palette and are not redrawn with these vectors.",
            ],
            entry["en"],
        )
        self.assertEqual("1.2.6", cover["version"])
        self.assertEqual("2026-10-25", cover["date"])
        self.assertEqual(
            [
                "封面图不再写英文眉题，板卡外框加了一道内线；发光的灯点改成平涂。中英文仍共用这一张图。",
                "标题板把书名放在书脊短线上面。扉页标题改用章标题的字号，并在标题下重复这条书脊短线。",
            ],
            cover["zh"],
        )
        self.assertEqual(
            [
                "The cover drawing no longer carries an English kicker. The board frame gains an inner rule, and the glowing lamp is flat. Both languages still share this drawing.",
                "The title plate places the title above the spine rule. The imprint heading uses the chapter title size and repeats that spine rule.",
            ],
            cover["en"],
        )
        self.assertEqual("1.2.5", tokens["version"])
        self.assertEqual("2026-10-25", tokens["date"])
        self.assertEqual(
            [
                "整书样式的颜色、字号、间距、圆角和阴影改由一份令牌表提供，组件继续引用它们。屏幕、暗色和印刷的观感与 1.2.4 相同。",
                "中文和英文 HTML 仍把样式内嵌在单个文件里，不引用外部字体。",
            ],
            tokens["zh"],
        )
        self.assertEqual(
            [
                "Colors, type, spacing, radius, and shadow now come from a token file. Components still reference them. Screen, dark, and print look the same as 1.2.4.",
                "Chinese and English HTML still embed the stylesheet in a single file and do not load a font from the network.",
            ],
            tokens["en"],
        )
        self.assertEqual("1.2.4", typography["version"])
        self.assertEqual("2026-10-25", typography["date"])
        self.assertEqual(
            [
                "正文、标题和眉题改用一组字号；目录里的分部目标改成次要色，分部收束行加上分隔线。",
                "代码块补上能显示中文的等宽字体，行距略增；图注行距加大。印刷时代码块改为浅底，图注改为 9pt，不再大于正文。",
            ],
            typography["zh"],
        )
        self.assertEqual(
            [
                "Body, headings, and kickers use one type scale. Part goals in the contents are muted, and each part-closing line has a divider.",
                "Code blocks gain a monospace stack that can show Chinese, with a slightly looser line-height. Captions gain line-height. In print, code blocks are light and captions are 9pt, no longer larger than the body.",
            ],
            typography["en"],
        )
        self.assertEqual("1.2.3", batch4["version"])
        self.assertEqual("2026-10-25", batch4["date"])
        self.assertEqual(
            [
                "第 01 章写上 SWD 在第 34 脚 PA13 和第 37 脚 PA14，读保护解除写 0xA5，BOOT0=1 且 BOOT1=0 进的是系统存储器。第 07 章写上 0x3C 在 HAL 里是 0x78，表 42 的 400 kHz 行是 0x801E 和 4.7 kΩ。",
                "第 10 章写上只有 DMA1，8 个半字且 CNDTR 为 3 时已写 5 个采样、10 字节。第 11 章写上预分频 64、Reload 624 在 40 kHz 典型值下是 1 秒，LSI 是 30–60 kHz，备份寄存器是 10 个。",
            ],
            batch4["zh"],
        )
        self.assertEqual(
            [
                "Chapter file 01 records SWD on pin 34 PA13 and pin 37 PA14, readout protection level 0 as 0xA5, and BOOT0=1 with BOOT1=0 entering system memory. Chapter file 07 records that 0x3C is 0x78 in HAL, and that Table 42's 400 kHz row is 0x801E with 4.7 kΩ.",
                "Chapter file 10 records DMA1 only, and that eight half-words with CNDTR 3 means 5 samples and 10 bytes written. Chapter file 11 records prescaler 64 and Reload 624 as 1 second at a typical 40 kHz, LSI as 30–60 kHz, and ten backup registers.",
            ],
            batch4["en"],
        )
        self.assertEqual("1.2.2", batch3["version"])
        self.assertEqual(
            [
                "第 02 章把 CFGR 改回第 7.3.2 节，并写上 72 MHz 要 2 个等待、CSS 回到 HSI。第 05 章写上 1 kHz 和 500 Hz 两条路径。",
                "第 08 章写上 Mode 0、9 MHz，以及 0x9F 之后的 0xEF、0x40、0x17。第 09 章写上 12 MHz 下的 21 µs、除以 4096，以及 C8 有 ADC1/ADC2、没有 DAC。",
            ],
            batch3["zh"],
        )
        self.assertEqual(
            [
                "Chapter file 02 moves CFGR back to section 7.3.2, with two Flash wait states at 72 MHz and CSS falling back to HSI. Chapter file 05 records both the 1 kHz path and the 500 Hz path.",
                "Chapter file 08 records Mode 0 at 9 MHz and, after 0x9F, the bytes 0xEF, 0x40, and 0x17. Chapter file 09 records 21 µs at 12 MHz, division by 4096, and that the C8 has ADC1 and ADC2 and no DAC.",
            ],
            batch3["en"],
        )
        self.assertEqual("1.2.1", guide["version"])
        self.assertEqual(
            [
                "贡献指南把大典四块写成每章必选，放在视频块之后、学习目标之前。",
                "旧的常见坑与排查迁入坑与出处卡，并用 `#source-` 链到附录 E。这一版不改正文章。",
            ],
            guide["zh"],
        )
        self.assertEqual(
            [
                "The contributor guide requires the four compendium sections after the video block and before the learning goals.",
                "The old pitfalls section moves into Pitfalls and source cards, with `#source-` links to Appendix E. This edition does not rewrite chapter prose.",
            ],
            guide["en"],
        )
        self.assertEqual("1.2.0", previous["version"])
        self.assertEqual(
            [
                "整书样式收到同一组纸色、墨色和强调色，章距、段距、图距使用固定阶梯。",
                "章首罗盘、提示框、出处卡和插图共用一档圆角和轻阴影；印刷时的孤行、寡行和图注不断页仍按原规则。",
            ],
            previous["zh"],
        )
        self.assertEqual(
            [
                "The book stylesheet uses one paper, ink, and accent set, with a fixed step for chapter, paragraph, and figure spacing.",
                "Chapter compasses, callouts, source cards, and figures share one radius and a light shadow; print orphans, widows, and caption keep-together rules stay as they were.",
            ],
            previous["en"],
        )
        self.assertIn("当前版本：**v1.2.9 · 2026-10-25**", readme)
        self.assertIn("版本号已经是 1.2.9。", readme)
        self.assertIn("样式来自 `stm32-book/styles/tokens.json` 和 `stm32-book/styles/book.css`，构建时拼进 HTML 的 `<style>`，`dist/` 里不另放 CSS。", readme)
        self.assertIn("也不要把 1.1.1 的产物标成 1.2.0，", readme)
        self.assertIn("也不要把 1.2.0 的产物标成 1.2.1，", readme)
        self.assertIn("也不要把 1.2.1 的产物标成 1.2.2，", readme)
        self.assertIn("也不要把 1.2.2 的产物标成 1.2.3，", readme)
        self.assertIn("也不要把 1.2.3 的产物标成 1.2.4，", readme)
        self.assertIn("也不要把 1.2.4 的产物标成 1.2.5，", readme)
        self.assertIn("也不要把 1.2.5 的产物标成 1.2.6。", readme)
        self.assertIn("也不要把 1.2.6 的产物标成 1.2.7。", readme)
        self.assertIn("也不要把 1.2.7 的产物标成 1.2.8。", readme)
        self.assertIn("也不要把 1.2.8 的产物标成 1.2.9。", readme)
        self.assertIn("打 tag `v1.2.9`", readme)
        self.assertNotIn("当前版本：**v1.2.8", readme)
        self.assertNotIn("打 tag `v1.2.8`", readme)

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
        self.assertIn('transform="translate(148 114)"', svg)
        self.assertNotIn('transform="translate(118 100)"', svg)
        self.assertNotIn("<text", svg)
        self.assertNotIn("OFFLINE EDITION", svg)
        self.assertNotIn('opacity="0.18"', svg)
        self.assertNotIn("<style", svg)
        self.assertIn('fill="#1b5c45"', svg)
        self.assertIn('fill="#ffb020"', svg)
        self.assertIn("--spine: #c4552a", self.builder.CSS)

    def test_cover_imprint_d_contract(self) -> None:
        svg = (BOOK_DIR / "cover.svg").read_text(encoding="utf-8")
        self.assertIn('viewBox="0 0 1200 760"', svg)
        self.assertIn(
            '<rect x="22" y="32" width="896" height="468" rx="18" fill="none" stroke="#d7c4a3" stroke-width="4"/>',
            svg,
        )
        self.assertIn(
            '<rect x="34" y="44" width="872" height="444" rx="12" fill="none" stroke="#d7c4a3" stroke-width="1"/>',
            svg,
        )
        self.assertIn('stroke="#8ecae6"', svg)
        self.assertIn('<circle r="22" fill="#ffb020"/>', svg)
        self.assertNotIn("<text", svg)
        self.assertNotIn("font-family", svg)
        self.assertNotIn("font-size", svg)
        self.assertNotIn("<filter", svg)
        self.assertNotIn("<foreignObject", svg)
        self.assertNotIn('opacity="0.18"', svg)
        found = re.findall(r"#[0-9A-Fa-f]{3,8}", svg)
        self.assertEqual(
            {
                "#07141a",
                "#0c1c24",
                "#14181c",
                "#1b5c45",
                "#1e4d63",
                "#5c6770",
                "#8d99a3",
                "#8ecae6",
                "#c4552a",
                "#c5ced6",
                "#d7c4a3",
                "#d9dde2",
                "#e7d7a1",
                "#f4f1ea",
                "#ffb020",
                "#fff4d2",
            },
            set(found),
        )
        self.assertTrue(all(item == item.lower() for item in found))
        self.assertEqual(["0.28", "0.45"], re.findall(r'opacity="([^"]*)"', svg))
        self.assertLessEqual(len(svg.encode("utf-8")), 8192)

        def panel_of(html: str) -> str:
            start = html.index('<div class="cover-panel">')
            end = html.index("</div>", start)
            return html[start:end]

        def heading_text(panel: str) -> str:
            match = re.search(r"<h1>(.*?)</h1>", panel, re.S)
            self.assertIsNotNone(match)
            return match.group(1)

        def assert_plate(html: str, title: str) -> None:
            panel = panel_of(html)
            self.assertLess(panel.index('class="eyebrow"'), panel.index("<h1>"))
            self.assertLess(panel.index("<h1>"), panel.index('class="rule"'))
            self.assertLess(panel.index('class="rule"'), panel.index('class="subtitle"'))
            self.assertEqual(title, heading_text(panel))
            self.assertNotIn("OFFLINE EDITION", html)
            self.assertNotIn("fonts.googleapis", html)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            chinese = self.builder.build_html(root / "zh")
            english = self.builder.build_html(root / "en", BOOK_DIR / "manifest-en.json")
            zh = json.loads((BOOK_DIR / "manifest.json").read_text(encoding="utf-8"))
            en = json.loads((BOOK_DIR / "manifest-en.json").read_text(encoding="utf-8"))
            assert_plate(chinese.read_text(encoding="utf-8"), zh["title"])
            assert_plate(english.read_text(encoding="utf-8"), en["title"])

        css = self.builder.CSS
        screen = css.split("@media", 1)[0]
        dark = css.split("@media (prefers-color-scheme: dark)", 1)[1].split("@media", 1)[0]
        printed = css.split("@media print", 1)[1]
        imprint = self._css_rule(screen, ".imprint h1")
        self.assertIn("margin-bottom: .4rem", imprint)
        self.assertIn("font-size: var(--type-h1)", imprint)
        self.assertIn("line-height: 1.22", imprint)
        companion = self._css_rule(screen, ".imprint h1, .companion h2")
        self.assertIn("margin-top: 0", companion)
        self.assertNotIn("font-size", companion)
        rule = self._css_rule(screen, ".imprint h1::after")
        self.assertIn('content: ""', rule)
        self.assertIn("width: 4.2rem", rule)
        self.assertIn("height: .18rem", rule)
        self.assertIn("background: var(--spine)", rule)
        self.assertNotIn("url(", rule)
        self.assertIn("clamp(2.15rem, 5.6vw, 3.7rem)", self._css_rule(screen, ".cover h1"))
        self.assertIn("clamp(1.05rem, 2.4vw, 1.35rem)", self._css_rule(screen, ".cover .subtitle"))
        self.assertIn("clamp(2rem, 5vw, 3.35rem)", self._css_rule(screen, ".part-divider h1"))
        self.assertIn("font-size: 9.5pt", printed)
        self.assertIn("font-size: 9pt", printed)
        self.assertIn(".imprint { break-before: auto; page-break-before: auto; }", printed)
        self.assertIn("background: #10242e", self._css_rule(printed, ".cover"))
        self.assertNotIn(".cover", dark)

        tokens = json.loads((BOOK_DIR / "styles" / "tokens.json").read_text(encoding="utf-8"))
        self.assertEqual(1, tokens["schema"])
        self.assertEqual(
            ["--paper", "--ink", "--muted", "--warn", "--line", "--spine"],
            tokens["coverLock"],
        )
        css_source = (BOOK_DIR / "styles" / "book.css").read_text(encoding="utf-8")
        self.assertEqual(
            {"#10242e", "#f4f1ea", "#0c1c24"},
            set(re.findall(r"#[0-9A-Fa-f]{3,8}", css_source)),
        )

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
        self.assertIn("bookmark-level: none", print_css)

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

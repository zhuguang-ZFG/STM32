"""Current entry points must not depend on the archived bilingual tree."""
import importlib.util
import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

HAS_PIL = importlib.util.find_spec("PIL") is not None
HAS_PLAYWRIGHT = importlib.util.find_spec("playwright") is not None
HAS_FITZ = importlib.util.find_spec("fitz") is not None

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("asset_entry", ROOT / "tools/check_assets.py")
if SPEC is None or SPEC.loader is None:
    raise ImportError("无法按文件路径加载 tools/check_assets.py")
assets = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(assets)


def recipe(name):
    lines = (ROOT / "Makefile").read_text(encoding="utf-8").splitlines()
    # 允许目标带前置依赖（如 `book-pdf: book-html`）
    start = next(i for i, line in enumerate(lines) if line.split("#")[0].strip().startswith(name + ":")) + 1
    result = []
    for line in lines[start:]:
        if line and not line.startswith("\t"):
            break
        if line.startswith("\t"):
            result.append(line.strip())
    return "\n".join(result)


class BuildEntrypointTests(unittest.TestCase):
    def setUp(self):
        self.capture = contextlib.redirect_stdout(io.StringIO())
        self.capture.__enter__()
        self.addCleanup(self.capture.__exit__, None, None, None)

    @unittest.skipUnless(HAS_PLAYWRIGHT and HAS_FITZ, "optional PDF integration: install Playwright/Chromium and PyMuPDF")
    def test_print_list_image_fits_its_container(self):
        from playwright.sync_api import sync_playwright
        from book.print_pdf import _launch
        from book.print_css import PRINT_CSS
        with sync_playwright() as pw:
            browser = _launch(pw, None)
            try:
                page = browser.new_page(viewport={"width": 1280, "height": 900})
                page.set_content('<style>' + PRINT_CSS + '</style>'
                                 '<main class="book"><section class="chapter">'
                                 '<ul><li><img width="1152" height="560" alt="test"></li></ul>'
                                 '</section></main>')
                page.emulate_media(media="print")
                image = page.locator("img").bounding_box()
                container = page.locator("li").bounding_box()
                if image is None or container is None:
                    self.fail("打印视口里量不到 img / li 的位置")
                self.assertLessEqual(image["width"], container["width"] + 1,
                                     "a list image must not shrink the entire printed book")
            finally:
                browser.close()

    @unittest.skipUnless(HAS_PLAYWRIGHT, "optional print snapshot regression: install Playwright")
    def test_print_snapshot_does_not_overwrite_adjacent_probe(self):
        from book import build_print_edition as print_book
        with tempfile.TemporaryDirectory() as tmp:
            svg = Path(tmp) / "test-no-write.svg"
            svg.write_text('<svg viewBox="0 0 900 620"/>')
            probe = svg.with_suffix(".probe.png")
            probe.write_bytes(b"existing user file")
            element = MagicMock()
            def screenshot(**kwargs):
                if "path" in kwargs:
                    Path(kwargs["path"]).write_bytes(b"test screenshot")
                return b"test screenshot"
            element.screenshot.side_effect = screenshot
            pw = MagicMock()
            pw.chromium.launch.return_value.new_page.return_value.query_selector.return_value = element
            manager = MagicMock()
            manager.__enter__.return_value = pw
            print_book._anim_cache.clear()
            with patch("playwright.sync_api.sync_playwright", return_value=manager):
                uri = print_book.anim_frame_uri(svg)
            self.assertTrue(probe.exists(), "print build removed an adjacent user probe")
            self.assertEqual(probe.read_bytes(), b"existing user file")
            self.assertTrue(uri.startswith("data:image/png;base64,"))
            element.screenshot.assert_called_once_with()

    def test_book_is_the_current_site_builder(self):
        # B5 之后站点入口是 VitePress（base /STM32/）；book.build_html 降级为
        # 内容渲染契约，由 book-check 固定（见下一条测试）。
        commands = recipe("book")
        self.assertIn("npm run docs:build", commands)
        self.assertNotIn("stm32-book/", commands)

    def test_python_renderer_is_still_the_print_contract(self):
        commands = recipe("book-check")
        self.assertIn("-m book.build_html --check", commands)
        self.assertIn("-m book.build_print_edition", recipe("book-html"))

    def test_pdf_uses_both_documented_print_stages(self):
        # 两段流水线现在拆成“book-html 出单文件书稿 → book-pdf 打印”两个目标，
        # 依赖关系保证顺序；仍钉住两段各自可单独调用。
        self.assertIn("-m book.build_print_edition", recipe("book-html"))
        self.assertIn("-m book.print_pdf", recipe("book-pdf"))
        self.assertIn("--meta", recipe("book-pdf"))
        makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
        self.assertIn("book-pdf: book-html", makefile)

    def test_book_check_uses_current_tests_and_checks(self):
        commands = recipe("book-check")
        for part in ("discover book/tests", "-m book.manifest --check",
                     "-m book.checks --check", "-m book.build_html --check"):
            self.assertIn(part, commands)
        self.assertNotIn("stm32-book/", commands)

    def test_current_print_commands_are_documented(self):
        guide = ROOT / "book/README.md"
        self.assertTrue(guide.exists(), "book/ needs an actual build guide")
        text = guide.read_text(encoding="utf-8")
        for command in ("book.build_html", "book.build_print_edition", "book.print_pdf"):
            self.assertIn(command, text)

    @unittest.skipUnless(HAS_PIL, "optional raster asset regression: install Pillow")
    def test_merged_assets_validate_xml_and_images(self):
        self.assertTrue(callable(getattr(assets, "check_public_assets", None)), "missing merged entry: check_public_assets")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "anim").mkdir()
            (root / "anim/good.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"/>')
            self.assertTrue(assets.check_public_assets(root))
            (root / "anim/bad.svg").write_text('<svg><broken>')
            self.assertFalse(assets.check_public_assets(root))
            (root / "anim/bad.svg").unlink()
            (root / "broken.png").write_bytes(b"not a PNG")
            self.assertFalse(assets.check_public_assets(root))

    @unittest.skipUnless(HAS_PIL, "optional raster asset regression: install Pillow")
    def test_merged_entry_keeps_book_errors_fatal(self):
        self.assertTrue(callable(getattr(assets, "check_merged_book", None)), "missing merged entry: check_merged_book")
        with patch("book.checks.check_book", return_value=["ch00: missing image: /images/gone.png"]):
            self.assertFalse(assets.check_merged_book())

    @unittest.skipUnless(HAS_PIL, "optional raster asset regression: install Pillow")
    def test_merged_entry_checks_missing_chapters(self):
        self.assertTrue(callable(getattr(assets, "check_merged_book", None)), "missing merged entry: check_merged_book")
        with tempfile.TemporaryDirectory() as tmp:
            self.assertFalse(assets.check_merged_book(Path(tmp)))

    def test_merged_main_does_not_launch_legacy_video_checks(self):
        self.assertTrue(callable(getattr(assets, "main", None)), "missing merged entry: main")
        with patch.object(assets, "check_merged_book", create=True, return_value=True), \
             patch.object(assets, "check_videos", side_effect=AssertionError("legacy video checker called")):
            self.assertEqual(assets.main(), 0)


if __name__ == "__main__":
    unittest.main()

"""EPUB content must keep legacy figure alignment and comparison text."""
import importlib.util
import unittest
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[2]
HAS_LXML = importlib.util.find_spec("lxml") is not None
XHTML = {"html": "http://www.w3.org/1999/xhtml"}


@unittest.skipUnless(HAS_LXML, "EPUB integration: install book/requirements-print.txt")
class EpubCompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("epub_compat", ROOT / "tools/build_epub.py")
        cls.epub = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.epub)

    def test_legacy_paragraph_alignment_becomes_css(self):
        for alignment in ("center", "left", "right", "justify"):
            with self.subTest(alignment=alignment):
                payload, _ = self.epub._to_xhtml_document(
                    f'<p align="{alignment}" class="figure-caption">Figure <sub>caption</sub></p>',
                    "Alignment", "epub.css")
                paragraph = ElementTree.fromstring(payload).find(".//html:p", XHTML)
                self.assertNotIn("align", paragraph.attrib)
                self.assertIn("figure-caption", paragraph.attrib["class"].split())
                self.assertIn(f"epub-align-{alignment}", paragraph.attrib["class"].split())
                self.assertEqual("".join(paragraph.itertext()), "Figure caption")
                self.assertIn(f".epub-align-{alignment} {{ text-align: {alignment};", self.epub.NAV_CSS)

    def test_motor_comparison_survives_markdown_and_xhtml(self):
        from book import build_html
        text = (ROOT / "docs/v5-motion/37-dc-motor-openloop.md").read_text(encoding="utf-8")
        _, body = build_html.split_frontmatter(text)
        rendered = build_html.render_markdown(body, ROOT / "docs/quizzes")
        payload, _ = self.epub._to_xhtml_document(rendered, "PWM", "epub.css")
        document = ElementTree.fromstring(payload)
        self.assertEqual(document.findall(".//html:ccr", XHTML), [])
        self.assertIn("CNT < CCR", "".join(document.itertext()))


if __name__ == "__main__":
    unittest.main()

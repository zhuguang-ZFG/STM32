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
        if spec is None or spec.loader is None:
            raise unittest.SkipTest("tools/build_epub.py 无法按文件路径加载")
        cls.epub = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.epub)

    def test_legacy_paragraph_alignment_becomes_css(self):
        for alignment in ("center", "left", "right", "justify"):
            with self.subTest(alignment=alignment):
                payload, _ = self.epub._to_xhtml_document(
                    f'<p align="{alignment}" class="figure-caption">Figure <sub>caption</sub></p>',
                    "Alignment", "epub.css")
                paragraph = ElementTree.fromstring(payload).find(".//html:p", XHTML)
                if paragraph is None:
                    self.fail("XHTML 里没有 <p>，合成器没按预期输出")
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

    def test_repo_table_gets_fixed_layout_class(self):
        """「仓库/文件/看什么」三列表（首格链接）挂 repo-table；四列与
        无链接首格的表不挂——窄窗口阅读器的固定列宽只该给这一形状。"""
        repo = ('<table><thead><tr><th>仓库</th><th>文件</th><th>看什么</th></tr></thead>'
                '<tbody><tr><td><a href="https://github.com/a/b">a/b</a></td>'
                '<td><code>x.c</code></td><td>看 <code>y</code> 的写法</td></tr></tbody></table>')
        payload, _ = self.epub._to_xhtml_document(repo, "Repo", "epub.css")
        table = ElementTree.fromstring(payload).find(".//html:table", XHTML)
        self.assertIn("repo-table", table.attrib["class"].split())
        self.assertIn("table.repo-table { table-layout: fixed; }", self.epub.NAV_CSS)

        four = repo.replace("<th>看什么</th>", "<th>看什么</th><th>备注</th>").replace(
            "<td>看 <code>y</code> 的写法</td>", "<td>看 <code>y</code> 的写法</td><td>n</td>")
        payload4, _ = self.epub._to_xhtml_document(four, "Repo4", "epub.css")
        table4 = ElementTree.fromstring(payload4).find(".//html:table", XHTML)
        self.assertNotIn("repo-table", (table4.attrib.get("class") or "").split())

        nolink = repo.replace('<td><a href="https://github.com/a/b">a/b</a></td>', "<td>a/b</td>")
        payload3, _ = self.epub._to_xhtml_document(nolink, "Repo3", "epub.css")
        table3 = ElementTree.fromstring(payload3).find(".//html:table", XHTML)
        self.assertNotIn("repo-table", (table3.attrib.get("class") or "").split())


if __name__ == "__main__":
    unittest.main()

"""build_print 印前 HTML 冻结变换的单测。

strip_table_scroll_inline_vars 的失败模式是**静默 no-op**：build_html 改一下
table-scroll 的写法（属性顺序、变量格式），正则就一条都剥不掉，而孤行标题
的复发没有任何契约门能看见（paged.js 把带内联 style 的表格容器标成
data-undisplayed，break-after: avoid 的跟随标记落空）。所以把计数一致性
钉在这里：剥掉数必须等于 table-scroll 出现数，少一条都是回归。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

BOOK_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BOOK_DIR))

import build_print  # noqa: E402

# 与 build_html.py:535 的实际输出同形
SAMPLE = (
    '<div class="table-scroll" role="region" tabindex="0"'
    ' aria-label="数据表，可横向滚动" style="--table-columns: 2"><table></table></div>'
)


class StripTableScrollVarsTests(unittest.TestCase):
    def test_strips_var_and_keeps_other_attributes(self) -> None:
        html, count = build_print.strip_table_scroll_inline_vars(SAMPLE)
        self.assertEqual(1, count)
        self.assertNotIn("--table-columns", html)
        self.assertIn('class="table-scroll"', html)
        self.assertIn('aria-label="数据表，可横向滚动"', html)
        self.assertIn("<table></table>", html)

    def test_count_matches_wrapper_count(self) -> None:
        """计数一致性：有几个 table-scroll 就得剥掉几个，漏剥即复发。"""
        html = SAMPLE + '<div class="table-scroll" style="--table-columns: 12"><table></table></div>'
        stripped, count = build_print.strip_table_scroll_inline_vars(html)
        self.assertEqual(2, count)
        self.assertEqual(0, stripped.count("--table-columns"))
        self.assertEqual(2, stripped.count('class="table-scroll"'))

    def test_wrapper_without_var_is_untouched(self) -> None:
        html = '<div class="table-scroll"><table></table></div>'
        stripped, count = build_print.strip_table_scroll_inline_vars(html)
        self.assertEqual(0, count)
        self.assertEqual(html, stripped)


if __name__ == "__main__":
    unittest.main()

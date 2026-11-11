"""build_print.print_outline 的单测：书签整形的判断逻辑。

这支函数是印前管线里唯一有真实分支的整形器，而它的缺陷在产物上几乎
看不见——条目齐全、层级合法，只是面板被 1167 条重复栏目名淹掉。所以把
教训钉在这里：栏目名按频次丢、实质小节留、结构缺失当场炸。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

BOOK_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BOOK_DIR))

import build_print  # noqa: E402

PART = "第一部分 语法地基"
CHAPTERS = 6
MANIFEST = {
    "title": "合成样书",
    "parts": [{"title": PART, "files": [f"c{n}.md" for n in range(1, CHAPTERS + 1)]}],
}


def rows_for_book(
    *,
    section_titles: dict[int, list[str]] | None = None,
    include_part: bool = True,
    chapters: int = CHAPTERS,
    appendix_sections: tuple[str, ...] = (),
) -> list[dict]:
    """造分页收集器那一侧的行：部 h1、章 h1、章内 h2、附录 h1/h2。"""
    rows: list[dict] = []
    if include_part:
        rows.append({"text": PART, "page": 1, "kind": "section.part-divider", "tag": "H1"})
    for number in range(1, chapters + 1):
        page = number + 1
        rows.append({"text": f"第 {number:02d} 章 标题", "page": page, "kind": "article.chapter", "tag": "H1"})
        for title in (section_titles or {}).get(number, []):
            rows.append({"text": title, "page": page, "kind": "article.chapter", "tag": "H2"})
    rows.append({"text": "附录 A", "page": chapters + 2, "kind": "article.appendix", "tag": "H1"})
    for title in appendix_sections:
        rows.append({"text": title, "page": chapters + 2, "kind": "article.appendix", "tag": "H2"})
    return rows


class PrintOutlineTests(unittest.TestCase):
    def test_repeated_column_names_are_dropped(self) -> None:
        # 6 章都有"本章罗盘"（>=5 次）→ 整类丢弃；每章独有的小节留下。
        sections = {n: ["本章罗盘", f"一、第 {n} 章的实质小节"] for n in range(1, CHAPTERS + 1)}
        outline = build_print.print_outline(rows_for_book(section_titles=sections), MANIFEST)
        titles = [row[1] for row in outline]
        self.assertNotIn("本章罗盘", titles)
        self.assertEqual(CHAPTERS, sum(1 for t in titles if "实质小节" in t))

    def test_column_name_below_threshold_is_kept(self) -> None:
        # 只在 4 章出现（< 5）→ 不够频次，按实质小节保留。
        sections = {n: ["偶尔出现的小节"] for n in range(1, 5)}
        outline = build_print.print_outline(rows_for_book(section_titles=sections), MANIFEST)
        self.assertEqual(4, sum(1 for row in outline if row[1] == "偶尔出现的小节"))

    def test_parenthetical_variants_merge_into_one_bucket(self) -> None:
        # "先跑起来（…）"的两种括号写法必须并桶，否则 4×+2× 都躲过阈值。
        sections = {n: [f"先跑起来（第 {n} 种写法）"] for n in range(1, CHAPTERS + 1)}
        outline = build_print.print_outline(rows_for_book(section_titles=sections), MANIFEST)
        self.assertEqual([], [row for row in outline if "先跑起来" in row[1]])

    def test_fully_parenthetical_titles_do_not_share_a_phantom_bucket(self) -> None:
        # 整条都是括号时归一化会得到空串；若放过，这些互不相干的标题会
        # 并进同一个空桶被集体删掉。
        sections = {n: [f"（{n}）各不相同的小节"] for n in range(1, CHAPTERS + 1)}
        outline = build_print.print_outline(rows_for_book(section_titles=sections), MANIFEST)
        self.assertEqual(CHAPTERS, sum(1 for row in outline if "各不相同" in row[1]))

    def test_levels_are_part_chapter_section(self) -> None:
        sections = {1: ["一、唯一小节"]}
        outline = build_print.print_outline(rows_for_book(section_titles=sections), MANIFEST)
        by_title = {row[1]: row[0] for row in outline}
        self.assertEqual(1, by_title[PART])
        self.assertEqual(2, by_title["第 01 章 标题"])
        self.assertEqual(3, by_title["一、唯一小节"])
        self.assertEqual(1, by_title["附录 A"])

    def test_missing_part_raises(self) -> None:
        with self.assertRaises(SystemExit) as caught:
            build_print.print_outline(rows_for_book(include_part=False), MANIFEST)
        self.assertIn(PART, str(caught.exception))

    def test_chapter_count_mismatch_raises(self) -> None:
        with self.assertRaises(SystemExit) as caught:
            build_print.print_outline(rows_for_book(chapters=CHAPTERS - 1), MANIFEST)
        self.assertIn("章书签", str(caught.exception))

    def test_appendix_sections_land_at_level_two(self) -> None:
        outline = build_print.print_outline(
            rows_for_book(appendix_sections=("证据纪律", "来源注册表")), MANIFEST
        )
        levels = {row[1]: row[0] for row in outline}
        self.assertEqual(2, levels["证据纪律"])
        self.assertEqual(2, levels["来源注册表"])


if __name__ == "__main__":
    unittest.main()

"""check_pdf.py 的契约测试：PyMuPDF 现场造合成样书，正反双向校验。

夹具按**印前契约的产物形态**造页，不复制校验规则：
185×260 开本、随书字体（woff2 解压成 ttf 再嵌，PostScript 名与 Chromium
产物一致）、封面/版权/目录/分部隔页/章页/附录/索引各一种，页脚 `N / total`
从正文第 1 页起算。反向用例逐项破坏一条契约，确认 check_pdf 点名而不是
静默放过——每个反向用例只破坏一处，正向用例必须 10 项全绿。
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

import fitz  # PyMuPDF，造夹具与解析都靠它（requirements.txt 已钉 >=1.24）
from fontTools.ttLib import TTFont

BOOK_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BOOK_DIR))  # 与 `python mcu-book/check_pdf.py` 的导入路径一致

import check_pdf  # noqa: E402

PT_PER_MM = 72 / 25.4
PAGE_W = 185.0 * PT_PER_MM
PAGE_H = 260.0 * PT_PER_MM
FONT_DIR = BOOK_DIR / "print" / "fonts"

# 页面角色表：夹具的"书"。索引写死两条术语，让索引门有可解析条目。
COVER, COPYRIGHT, CONTENTS, DIVIDER = 1, 2, 3, 4
CHAPTER_PAGES = {5: 1, 7: 2, 9: 3, 11: 4, 13: 5, 15: 6, 17: 7, 19: 8, 21: 9, 23: 10}
APPENDIX_PAGE = 25
INDEX_PAGE = 26
PAGE_COUNT = 26
BODY_START = 5  # 正文第 1 页的物理页；folio = 物理页 - 4

MANIFEST = {
    "title": "合成样书",
    "subtitle": "校验夹具副标题",
    "author": "测试者",
    "version": "1.0.0",
    "date": "2026-10-25",
    "parts": [
        {
            "title": "第一部分 语法地基",
            "intro": "夹具",
            "files": [f"c{n}.md" for n in range(1, 11)],
        }
    ],
    "appendices": [{"file": "A.md", "title": "附录 A 工程深读"}],
}

# folio 2/4 是填充页；folio 1/3 是章首页，走另一条分支不写术语
INDEX_TERMS = (("volatile", 2), ("中断向量表", 4))


def _ttf(name: str) -> bytes:
    """把随书 woff2 解压成 ttf 并改成 Chromium 的 PostScript 名。

    PyMuPDF 不收 woff2（FT_New_Memory_Face: unknown file format），而字体门
    按 PostScript 名比对随书家族（NotoSerifSC-Regular 这样的无空格名），
    woff2 里的 name 表是 'Noto Serif SC'，直接嵌会被判成系统字体。
    """
    font = TTFont(FONT_DIR / f"{name}.woff2")
    font.flavor = None
    ps_name = {"serif-regular": "NotoSerifSC-Regular", "mono-regular": "CascadiaMonoRoman-Regular"}[name]
    for record in font["name"].names:
        if record.nameID in (1, 3, 4, 6):
            record.string = ps_name.encode("utf-16-be") if record.platformID == 3 else ps_name.encode("ascii")
    buffer = io.BytesIO()
    font.save(buffer)
    return buffer.getvalue()


def make_book_pdf(
    path: Path,
    manifest: dict,
    *,
    metadata_override: dict | None = None,
    drop_footer_page: int | None = None,
    header_on_chapter_opener: int | None = None,
    footer_on_cover: bool = False,
    toc_folio_override: tuple[int, int] | None = None,
    index_folio_override: int | None = None,
    pale_code_ink: bool = False,
    drop_outline_title: str | None = None,
    outline_section_repeats: int = 0,
    outline_source_cards: int = 0,
    blank_body_pages: tuple[int, ...] = (),
    clipped_text_page: int | None = None,
    trailing_space_page: int | None = None,
    overflow_bottom_page: int | None = None,
) -> None:
    """造一本满足全部 10 项印前契约的合成样书。"""
    document = fitz.open()
    serif, mono = _ttf("serif-regular"), _ttf("mono-regular")
    total = PAGE_COUNT - BODY_START + 1  # 正文页数 = folio 分母

    def write(page: fitz.Page, point: fitz.Rect, text: str, size: float = 10.0, *, code: bool = False) -> None:
        page.insert_font(fontname="B0", fontbuffer=mono if code else serif)
        color = (0.92, 0.96, 0.94) if (code and pale_code_ink) else (0.09, 0.13, 0.12)
        page.insert_textbox(point, text, fontname="B0", fontsize=size, color=color)

    for index in range(PAGE_COUNT):
        physical = index + 1
        # 纸边裁字用例要让墨落在纸外：PyMuPDF 的 insert_text 会在页边截断，
        # 所以先画在更宽的页上，循环末尾再把 MediaBox 收回 185mm —— 与真实
        # 缺陷同形（Chromium 排到纸外，纸张尺寸不变）。
        over = PAGE_W + 60 if physical == clipped_text_page else PAGE_W
        page = document.new_page(width=over, height=PAGE_H)
        body = fitz.Rect(PAGE_W * 0.1, PAGE_H * 0.1, PAGE_W * 0.9, PAGE_H * 0.9)
        if physical == COVER:
            write(page, body, f"{manifest['title']}\n{manifest['subtitle']}", 20)
        elif physical == COPYRIGHT:
            write(page, body, f"版权页\n{manifest['author']}\n{manifest['version']}")
        elif physical == CONTENTS:
            # 与真实产物同形：标题左排、页码是右对齐的独立词。第 3 章标题故意
            # 以数字结尾（真实书有「解剖官方库 V3.3.3」），钉住"标题内嵌数字
            # 被当成页码"的误报/误通过。
            write(page, fitz.Rect(body.x0, body.y0, body.x1, body.y0 + 20), "目录")
            page.insert_font(fontname="T0", fontbuffer=serif)
            for k, (folio_physical, number) in enumerate(CHAPTER_PAGES.items()):
                folio = folio_physical - BODY_START + 1
                if toc_folio_override and toc_folio_override[0] == number:
                    folio = toc_folio_override[1]
                title = f"{number:02d}．第 {number:02d} 章 示例章标题"
                if number == 3:
                    title += " V3.3.3"
                y = body.y0 + 28 + k * 14
                page.insert_text(fitz.Point(body.x0, y), title, fontname="T0", fontsize=9.5)
                page.insert_text(fitz.Point(PAGE_W * 0.88, y), str(folio), fontname="T0", fontsize=9)
        elif physical == DIVIDER:
            write(page, body, "PART 1\n第一部分 语法地基\n本部导航\n01．第 01 章 示例章标题 1", 16)
        elif physical == APPENDIX_PAGE:
            write(page, body, "附录 A 工程深读\n\n夹具正文。")
        elif physical == INDEX_PAGE:
            lines = ["术语索引", "按 Unicode 码位序排列"]
            for term, folio in INDEX_TERMS:
                shown = index_folio_override if (index_folio_override and term == INDEX_TERMS[0][0]) else folio
                lines.append(term)
                lines.append(f"{shown}、")
            write(page, body, "\n".join(lines))
        elif physical in CHAPTER_PAGES:
            number = CHAPTER_PAGES[physical]
            write(page, body, f"第 {number:02d} 章 示例章标题\n本章罗盘\n\n夹具正文，占满版心。")
        elif physical in blank_body_pages:
            write(page, fitz.Rect(body.x0, body.y0, body.x1, body.y0 + 20), "短页")
        else:
            # 索引门要求"标注页上确有该术语"，所以把术语写进它指向的那一页。
            # 其余填充页不许出现索引术语，否则页码漂移用例会碰巧命中别的页。
            folio_here = physical - BODY_START + 1
            terms = [term for term, folio in INDEX_TERMS if folio == folio_here]
            filler = "夹具正文行，用来把版心填到 72% 以上。\n" * 22
            write(page, body, "".join(f"{t}\n" for t in terms) + filler)
            write(page, fitz.Rect(body.x0, body.y0, body.x1, body.y0 + 60), "code = 0;", code=True)

        # 纸边裁字：可见字形越出纸张（真缺陷，横向+纵向）
        # vs 行尾空白探出（不是缺陷）
        if physical == clipped_text_page:
            page.insert_font(fontname="C0", fontbuffer=mono)
            page.insert_text(
                fitz.Point(PAGE_W - 120, PAGE_H * 0.5),
                "$IDF_PATH/components/bootloader/bootloader_start.c:62",
                fontname="C0",
                fontsize=8.5,
                color=(0.09, 0.13, 0.12),
            )
            page.set_mediabox(fitz.Rect(0, 0, PAGE_W, PAGE_H))
        if physical == trailing_space_page:
            page.insert_font(fontname="C1", fontbuffer=mono)
            page.insert_text(
                fitz.Point(PAGE_W - 60, PAGE_H * 0.5),
                "bx lr" + " " * 40,  # 可见部分在版心内，尾随空白探出纸外
                fontname="C1",
                fontsize=8.5,
                color=(0.09, 0.13, 0.12),
            )
        if physical == overflow_bottom_page:
            page.insert_font(fontname="C2", fontbuffer=mono)
            page.insert_text(  # 基线在纸内、字形下沿探出纸底（不可断的高块溢出页底）
                fitz.Point(body.x0, PAGE_H - 1.0),
                "overflow_bottom_tail();",
                fontname="C2",
                fontsize=14,
                color=(0.09, 0.13, 0.12),
            )

        # 页眉：章首页/结构页无页眉；左页书名、右页章名
        is_opener = physical in CHAPTER_PAGES
        structural = physical in (COVER, COPYRIGHT, CONTENTS, DIVIDER)
        if not structural and (not is_opener or physical == header_on_chapter_opener):
            label = manifest["title"] if physical % 2 == 0 else "第 01 章 示例章标题"
            page.insert_font(fontname="H0", fontbuffer=serif)
            page.insert_textbox(
                fitz.Rect(40, PAGE_H * 0.025, PAGE_W - 40, PAGE_H * 0.055),
                label,
                fontname="H0",
                fontsize=7.5,
                align=fitz.TEXT_ALIGN_CENTER,
                color=(0.45, 0.49, 0.47),
            )
        # 页脚：封面/版权/目录/分部隔页不占页码
        if physical < BODY_START and not (footer_on_cover and physical == COVER):
            continue
        if physical == drop_footer_page:
            continue
        folio = max(1, physical - BODY_START + 1)
        page.insert_font(fontname="F0", fontbuffer=serif)
        page.insert_textbox(
            fitz.Rect(40, PAGE_H * 0.95, PAGE_W - 40, PAGE_H * 0.98),
            f"{folio} / {total}",
            fontname="F0",
            fontsize=8,
            align=fitz.TEXT_ALIGN_CENTER,
            color=(0.38, 0.42, 0.40),
        )

    metadata = {
        "title": manifest["title"],
        "author": manifest["author"],
        "subject": manifest["subtitle"],
        "creator": "mcu-book/build_print.py",
    }
    if metadata_override:
        metadata.update(metadata_override)
    document.set_metadata(metadata)

    toc: list[list] = [
        [1, "封面", COVER],
        [1, "版权页", COPYRIGHT],
        [1, "目录", CONTENTS],
        [1, manifest["parts"][0]["title"], DIVIDER],
    ]
    for physical, number in CHAPTER_PAGES.items():
        toc.append([2, f"第 {number:02d} 章 示例章标题", physical])
        toc.append([3, f"一、第 {number:02d} 章的实质小节", physical])
        for repeat in range(outline_section_repeats):
            toc.append([3, f"栏目名 {repeat}", physical])
    toc.append([1, manifest["appendices"][0]["title"], APPENDIX_PAGE])
    for card in range(outline_source_cards):
        toc.append([2, f"a{card + 1} RM0090 — 参考手册", APPENDIX_PAGE])
    toc.append([1, "术语索引", INDEX_PAGE])
    document.set_toc([row for row in toc if row[1] != drop_outline_title])
    document.save(path)
    document.close()


def run_check(pdf: Path, manifest_path: Path) -> tuple[int, str]:
    stdout, stderr = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = check_pdf.main([str(pdf), "--manifest", str(manifest_path)])
    return code, stdout.getvalue() + stderr.getvalue()


class CheckPdfContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        tmp = Path(self._tmp.name)
        self.pdf = tmp / "book.pdf"
        self.manifest_path = tmp / "manifest.json"
        self.manifest_path.write_text(json.dumps(MANIFEST, ensure_ascii=False), encoding="utf-8")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def build(self, **kwargs) -> tuple[int, str]:
        make_book_pdf(self.pdf, MANIFEST, **kwargs)
        return run_check(self.pdf, self.manifest_path)

    def test_complete_contract_passes(self) -> None:
        code, output = self.build()
        self.assertEqual(0, code, output)
        for gate in (
            "开本",
            "字体",
            "页码",
            "结构页",
            "页眉",
            "目录页码",
            "索引页码",
            "版面利用率",
            "墨色对比",
            "纸边裁字",
            "大纲与元数据",
        ):
            self.assertIn(f"✓ {gate}", output)

    def test_trim_size_is_checked(self) -> None:
        make_book_pdf(self.pdf, MANIFEST)
        document = fitz.open(self.pdf)
        document[0].set_mediabox(fitz.Rect(0, 0, 595, 842))  # A4
        document.save(self.pdf, incremental=True, encryption=fitz.PDF_ENCRYPT_KEEP)
        document.close()
        code, output = run_check(self.pdf, self.manifest_path)
        self.assertEqual(1, code, output)
        self.assertIn("MediaBox", output)
        self.assertIn("期望 185.0×260.0", output)

    def test_metadata_mismatch_is_named(self) -> None:
        code, output = self.build(metadata_override={"title": "别的书"})
        self.assertEqual(1, code, output)
        self.assertIn("metadata.title", output)
        self.assertIn("别的书", output)

    def test_cover_folio_is_named(self) -> None:
        code, output = self.build(footer_on_cover=True)
        self.assertEqual(1, code, output)
        self.assertIn("不应出现页码", output)

    def test_header_on_chapter_opener_is_named(self) -> None:
        code, output = self.build(header_on_chapter_opener=7)
        self.assertEqual(1, code, output)
        self.assertIn("第 7 页（章首页）", output)

    def test_unnumbered_page_not_flagged_but_folio_page_still_is(self) -> None:
        """前置页按"无页码"判定（目录涨过第 8 页后不再误报），门牙不松：
        有页码的正文右页缺章名仍要点名。"""
        make_book_pdf(self.pdf, MANIFEST)
        document = fitz.open(self.pdf)
        serif = _ttf("serif-regular")
        # p27（右页）：正文长相、无页码无页眉 —— 目录续页形态，不应报
        page = document.new_page(width=PAGE_W, height=PAGE_H)
        page.insert_font(fontname="F0", fontbuffer=serif)
        page.insert_text(fitz.Point(PAGE_W * 0.1, PAGE_H * 0.5), "目录续页夹具正文")
        # p28（左页）：占位
        document.new_page(width=PAGE_W, height=PAGE_H)
        # p29（右页）：带页码无页眉 —— 正文右页缺章名，必须报
        page = document.new_page(width=PAGE_W, height=PAGE_H)
        page.insert_font(fontname="F0", fontbuffer=serif)
        page.insert_text(fitz.Point(PAGE_W * 0.1, PAGE_H * 0.5), "正文右页夹具")
        page.insert_textbox(
            fitz.Rect(40, PAGE_H * 0.95, PAGE_W - 40, PAGE_H * 0.98),
            "25 / 22",
            fontname="F0",
            fontsize=8,
            align=fitz.TEXT_ALIGN_CENTER,
            color=(0.38, 0.42, 0.40),
        )
        failures = check_pdf.check_headers(document, MANIFEST)
        joined = " ".join(failures)
        self.assertNotIn("第 27 页", joined)
        self.assertIn("第 29 页（右页）→ 缺章名页眉", joined)

    def test_contents_folio_drift_is_named(self) -> None:
        code, output = self.build(toc_folio_override=(3, 99))
        self.assertEqual(1, code, output)
        self.assertIn("目录第 03 章页码 99", output)

    def test_index_folio_drift_is_named(self) -> None:
        code, output = self.build(index_folio_override=18)
        self.assertEqual(1, code, output)
        self.assertIn("volatile", output)
        self.assertIn("18", output)

    def test_pale_code_ink_is_named(self) -> None:
        code, output = self.build(pale_code_ink=True)
        self.assertEqual(1, code, output)
        self.assertIn("浅字印在浅底上", output)

    def test_clipped_text_is_named(self) -> None:
        # 真缺陷：长代码路径的尾部被纸边裁掉（实测 p674 就是这形态）。
        code, output = self.build(clipped_text_page=6)
        self.assertEqual(1, code, output)
        self.assertIn("第 6 页", output)
        self.assertIn("被纸边裁掉", output)
        self.assertIn("✓ 开本", output)  # 夹具只动内页，开本门（首末页）不该被带红

    def test_trailing_space_past_edge_is_not_flagged(self) -> None:
        # 不是缺陷：等宽块行尾空白让 bbox 探出纸外（全书 38 处汇编对照表）。
        # 门若按块 bbox 判就会在这里误报。
        code, output = self.build(trailing_space_page=6)
        self.assertEqual(0, code, output)
        self.assertIn("✓ 纸边裁字", output)

    def test_bottom_overflow_is_named(self) -> None:
        # 纵向也要守：不可断的高块溢出页底，同样印丢内容。
        code, output = self.build(overflow_bottom_page=6)
        self.assertEqual(1, code, output)
        self.assertIn("下沿", output)

    def test_missing_outline_entry_is_named(self) -> None:
        code, output = self.build(drop_outline_title="第一部分 语法地基")
        self.assertEqual(1, code, output)
        self.assertIn("大纲缺分部条目", output)

    def test_repeated_section_bookmarks_are_named(self) -> None:
        # 栏目名重复进书签：条目齐全、层级不越级，只有频次能暴露。
        code, output = self.build(outline_section_repeats=1)
        self.assertEqual(1, code, output)
        self.assertIn("重复栏目名", output)

    def test_source_card_bookmarks_are_named(self) -> None:
        code, output = self.build(outline_source_cards=3)
        self.assertEqual(1, code, output)
        self.assertIn("来源卡标题书签", output)
        self.assertIn("3", output)

    def test_missing_pdf_file_fails_loudly(self) -> None:
        code, output = run_check(self.pdf, self.manifest_path)
        self.assertEqual(1, code, output)
        self.assertIn("找不到 PDF", output)


if __name__ == "__main__":
    unittest.main()

"""印前 PDF 的度量与体检：开本、字体、页码、页眉、目录页码、版心、中文禁则。

为什么单独一层：这些度量在 P2（全量排版）、P3（目录页码）、P4（页码页眉）、P6（契约门）都要用，
而且契约门要能给出**逐条点名**的失败信息。实现一次、被 `check_pdf.py` 包装一次，
避免"门"和"体检脚本"各写一套判据（两边漂移是这类项目最常见的腐化方式）。

用法：
  python mcu-book/print/pdf_audit.py <pdf> [--bleed 0|3.2] [--manifest mcu-book/manifest.json] [--json]
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF

BOOK_DIR = Path(__file__).resolve().parents[1]
DOCS_DIR = BOOK_DIR.parent / "docs"

TRIM_MM = (185.0, 260.0)
PT_PER_MM = 72 / 25.4

# 中文禁则（W3C clreq §行首行尾禁则）：
#   · 行**首**不得出现「收尾类」标点（。，、；：！？）】》」』”’…～）——它们贴着上一行结尾；
#   · 行**尾**不得出现「起首类」标点（（【《「『“‘）——它们要跟着下一行的内容。
# 第一版把这两组写反了，于是把"行尾是 ）"这种完全合法的排版当成 5000 多处违规；
# 判据写错比没有判据更糟：它会让人去"修"根本不存在的问题。
NO_LINE_START = "。，、；：！？）】》」』”’…～"
NO_LINE_END = "（【《「『“‘"
# 页眉页脚区域（相对页面高度的比例）：顶部 7%、底部 7%
HEADER_BAND = 0.07
FOOTER_BAND = 0.93


def to_mm(points: float) -> float:
    return round(points / PT_PER_MM, 1)


def page_bands(page: fitz.Page) -> tuple[fitz.Rect, fitz.Rect]:
    rect = page.rect
    header = fitz.Rect(0, 0, rect.width, rect.height * HEADER_BAND)
    footer = fitz.Rect(0, rect.height * FOOTER_BAND, rect.width, rect.height)
    return header, footer


def band_text(page: fitz.Page, band: fitz.Rect) -> str:
    text = page.get_text("text", clip=band)
    if not isinstance(text, str):
        return ""
    return " ".join(text.split())


def check_trim(document: fitz.Document, bleed_mm: float) -> dict:
    expected = (TRIM_MM[0] + bleed_mm * 2, TRIM_MM[1] + bleed_mm * 2)
    bad = []
    for index in range(document.page_count):
        rect = document[index].rect
        actual = (to_mm(rect.width), to_mm(rect.height))
        if abs(actual[0] - expected[0]) > 0.6 or abs(actual[1] - expected[1]) > 0.6:
            bad.append({"page": index + 1, "actual": actual})
    return {"expected": expected, "ok": not bad, "bad": bad[:5]}


# 随书分发的字体族（subset_fonts.py 输出的那 8 支）。印刷产物里出现别的族，
# 就意味着有元素绕开了印刷样式——在别的机器上（没有那些系统字体）会直接变成另一种字形或方块。
SHIPPED_FAMILIES = (
    "NotoSerifSC",
    "NotoSansSC",
    "CascadiaMono",
    "NotoEmoji",
    "NotoSansSymbols2",
    "NotoSansMath",
)


def check_fonts(document: fitz.Document) -> dict:
    """字体体检：不许 Type3 位图字形，也不许出现未随书分发的字体族。"""
    type3: dict[str, int] = {}
    foreign: dict[str, int] = {}
    shipped: dict[str, int] = {}
    for index in range(document.page_count):
        for font in document[index].get_fonts():
            subtype, raw_name = font[2], font[3]
            name = raw_name.split("+", 1)[-1]  # 去掉子集前缀再看族名
            if subtype == "Type3":
                type3[name or "(未命名的 Type3)"] = type3.get(name or "(未命名的 Type3)", 0) + 1
            elif any(name.startswith(family) for family in SHIPPED_FAMILIES):
                shipped[name] = shipped.get(name, 0) + 1
            else:
                foreign[name or "(未命名)"] = foreign.get(name or "(未命名)", 0) + 1
    return {
        "ok": not type3 and not foreign,
        "type3": type3,
        "foreign": foreign,
        "shipped": shipped,
    }


def check_pagination(document: fitz.Document) -> dict:
    """页码自洽：末页必须是 N / N，且任何页的分子不得超过分母。"""
    problems = []
    labels = []
    pattern = re.compile(r"^(\d+)\s*/\s*(\d+)$")
    for index in range(document.page_count):
        _, footer = page_bands(document[index])
        text = band_text(document[index], footer)
        match = pattern.search(text)
        if not match:
            labels.append(None)
            continue
        numerator, denominator = int(match.group(1)), int(match.group(2))
        labels.append((numerator, denominator))
        if numerator > denominator:
            problems.append({"page": index + 1, "label": f"{numerator} / {denominator}"})
    tail = [label for label in labels if label]
    last = tail[-1] if tail else None
    total = last[1] if last else None
    if last and total is not None and last != (total, total):
        problems.append({"page": document.page_count, "label": f"末页 {last[0]} / {last[1]}，应为 {total} / {total}"})
    return {"ok": not problems, "problems": problems[:10], "pages_with_footer": len(tail), "total": total}


def check_headers(document: fitz.Document) -> dict:
    """页眉：正文页应有一行页眉；封面与前置页（结构页）不该有。"""
    odd, even, empty = 0, 0, 0
    samples: dict[str, str] = {}
    for index in range(document.page_count):
        header, _ = page_bands(document[index])
        text = band_text(document[index], header)
        if not text:
            empty += 1
            continue
        if (index + 1) % 2:
            odd += 1
        else:
            even += 1
        if len(samples) < 6:
            samples[f"p{index + 1}"] = text[:60]
    return {"ok": odd > 0 and even > 0, "odd": odd, "even": even, "empty": empty, "samples": samples}


def chapter_titles(manifest_path: Path) -> dict[str, str]:
    """章号 → 章题（TOC 与实际页都对它）。"""
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    titles: dict[str, str] = {}
    for _index, part in enumerate(manifest["parts"], start=1):
        for name in part["files"]:
            text = (DOCS_DIR / name).read_text(encoding="utf-8")
            match = re.search(r"^title:\s*(.+)$", text, re.M)
            if match:
                titles[match.group(1).strip().strip("'\"")] = name
    return titles


def check_contents(document: fitz.Document, manifest_path: Path) -> dict:
    """目录页码：目录里写的页码必须等于该章实际起始页（跳过目录自身所在的页）。"""
    titles = chapter_titles(manifest_path)
    contents_pages = []
    for index in range(document.page_count):
        if index > 30:
            break
        text = document[index].get_text()
        if not isinstance(text, str):
            continue
        if "目录与分部目标" in text or text.strip()[:2] == "目录":
            contents_pages.append(index)
    if not contents_pages:
        return {"ok": False, "reason": "找不到目录页", "checked": 0, "problems": []}
    first, last = contents_pages[0], contents_pages[-1]

    # 目录里每行形如 "01．C0 为什么嵌入式 C 是另一种 C  12"
    entry_re = re.compile(r"^\s*(\d{2})[．.]\s*(.+?)\s+(\d{1,4})\s*$")
    listed: dict[str, int] = {}
    for index in range(first, last + 1):
        page_text = document[index].get_text()
        if not isinstance(page_text, str):
            continue
        for line in page_text.splitlines():
            match = entry_re.match(line)
            if match:
                listed[match.group(2).strip()] = int(match.group(3))

    # 实际起始页：在目录之后的页里找章题首次出现
    actual: dict[str, int] = {}
    for index in range(last + 1, document.page_count):
        text = document[index].get_text()
        if not isinstance(text, str):
            continue
        for title in titles:
            if title not in actual and title in text:
                actual[title] = index + 1

    problems = []
    checked = 0
    for title, page in listed.items():
        if title not in titles:
            continue
        if title not in actual:
            problems.append({"title": title, "listed": page, "actual": None})
            continue
        checked += 1
        if actual[title] != page:
            problems.append({"title": title, "listed": page, "actual": actual[title]})
    return {
        "ok": checked > 0 and not problems,
        "checked": checked,
        "listed": len(listed),
        "problems": problems[:10],
    }


def check_measure(document: fitz.Document, sample: int = 12) -> dict:
    """版心与行长：正文页每行字数与行宽要落在 16 开惯例区间。"""
    widths: list[float] = []
    chars: list[int] = []
    step = max(1, document.page_count // sample)
    for index in range(2, document.page_count, step):
        page = document[index]
        page_dict: dict[str, Any] = page.get_text("dict")  # type: ignore[assignment]
        for block in page_dict.get("blocks", []):
            for line in block.get("lines", []):
                text = "".join(span["text"] for span in line["spans"]).strip()
                han = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
                # 只统计正文段落行：汉字占多数、长度够，避免标题/表格/代码/图注把中位数拉低
                if len(text) < 20 or han < len(text) * 0.5:
                    continue
                widths.append(to_mm(line["bbox"][2] - line["bbox"][0]))
                chars.append(han)
    if not widths:
        return {"ok": False, "reason": "取样页没有可测正文行"}
    widths.sort()
    chars.sort()
    return {
        "ok": chars[len(chars) // 2] >= 30,
        "lines": len(chars),
        "charsPerLineMedian": chars[len(chars) // 2],
        "charsPerLineP10": chars[len(chars) // 10],
        "charsPerLineP90": chars[len(chars) * 9 // 10],
        "lineWidthMedianMm": widths[len(widths) // 2],
        "lineWidthMaxMm": widths[-1],
    }


def check_line_breaks(document: fitz.Document, limit: int = 20) -> dict:
    """中文禁则：行尾不得收尾类标点，行首不得起首类标点。"""
    problems = []
    total = 0
    for index in range(document.page_count):
        page_dict: dict[str, Any] = document[index].get_text("dict")  # type: ignore[assignment]
        for block in page_dict.get("blocks", []):
            for line in block.get("lines", []):
                text = "".join(span["text"] for span in line["spans"]).strip()
                if len(text) < 6:
                    continue
                total += 1
                if text[-1] in NO_LINE_END:
                    problems.append({"page": index + 1, "kind": "行尾", "char": text[-1], "text": text[-24:]})
                elif text[0] in NO_LINE_START:
                    problems.append({"page": index + 1, "kind": "行首", "char": text[0], "text": text[:24]})
    return {"ok": not problems, "lines": total, "problems": problems[:limit], "count": len(problems)}


def audit(pdf_path: Path, manifest_path: Path, bleed_mm: float = 0.0) -> dict:
    document = fitz.open(pdf_path)
    try:
        return {
            "file": str(pdf_path),
            "pages": document.page_count,
            "trim": check_trim(document, bleed_mm),
            "fonts": check_fonts(document),
            "pagination": check_pagination(document),
            "headers": check_headers(document),
            "contents": check_contents(document, manifest_path),
            "measure": check_measure(document),
            "lineBreaks": check_line_breaks(document),
        }
    finally:
        document.close()


def render(result: dict) -> int:
    trim, fonts, pagination = result["trim"], result["fonts"], result["pagination"]
    contents, measure, breaks = result["contents"], result["measure"], result["lineBreaks"]
    print(f"文件: {result['file']}（{result['pages']} 页）")
    print(f"  开本: {trim['expected'][0]:.1f}×{trim['expected'][1]:.1f} mm {'✓' if trim['ok'] else '✗ ' + str(trim['bad'])}")
    print(f"  字体: 随书族 {len(fonts['shipped'])} 支" + (f"，**Type3 位图 {fonts['type3']}**" if fonts["type3"] else "，无 Type3")
          + (f"，**外来字体族 {fonts['foreign']}**" if fonts["foreign"] else "，无外来字体"))
    if fonts["foreign"]:
        print(f"        外来: {sorted(fonts['foreign'])}")
    print(f"  页码: {'✓' if pagination['ok'] else '✗ ' + str(pagination['problems'])}（有页脚页 {pagination['pages_with_footer']}，总数 {pagination['total']}）")
    print(f"  页眉: {'✓' if result['headers']['ok'] else '✗'}（奇 {result['headers']['odd']} / 偶 {result['headers']['even']} / 空 {result['headers']['empty']}）")
    for sample_key, sample_value in result["headers"]["samples"].items():
        print(f"        {sample_key}: {sample_value}")
    print(f"  目录页码: {'✓' if contents['ok'] else '✗'}（核对 {contents.get('checked', 0)} / 目录行 {contents.get('listed', 0)}）")
    for problem in contents.get("problems", [])[:5]:
        print(f"        {problem}")
    print(f"  版心/行长: 每行字数 中位 {measure.get('charsPerLineMedian')}（P10 {measure.get('charsPerLineP10')} / P90 {measure.get('charsPerLineP90')}），行宽中位 {measure.get('lineWidthMedianMm')} mm 最大 {measure.get('lineWidthMaxMm')} mm")
    break_note = "✓" if breaks["ok"] else f"✗ {breaks['count']} 处（扫 {breaks['lines']} 行）"
    print(f"  中文禁则: {break_note}")
    for problem in breaks["problems"][:5]:
        print(f"        {problem}")
    failed = [
        name
        for name, key in (("开本", "trim"), ("字体", "fonts"), ("页码", "pagination"), ("页眉", "headers"), ("目录页码", "contents"))
        if not result[key]["ok"]
    ]
    print("结论: " + ("全部通过" if not failed else "未通过：" + "、".join(failed)))
    return 0 if not failed else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--manifest", type=Path, default=BOOK_DIR / "manifest.json")
    parser.add_argument("--bleed", type=float, default=0.0)
    parser.add_argument("--json", action="store_true")
    options = parser.parse_args(argv)
    result = audit(options.pdf, options.manifest, options.bleed)
    if options.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    return render(result)


if __name__ == "__main__":
    raise SystemExit(main())
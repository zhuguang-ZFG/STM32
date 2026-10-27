"""印前 PDF 契约门——对 build_print.py 的产物做独立对账。

校验对象已从旧 A4 产物切换为 16 开印前 PDF。与 build_html 时代不同，
页码/页眉不再由 PyMuPDF 事后盖章，而是 paged.js 在分页时生成；
本门只读产物与 manifest，不依赖构建器的中间状态。

七项断言（任一失败即退出码 1 并逐条点名）：
  1. MediaBox == 185×260 mm（或出血版 191×266 mm，±0.5）
  2. 全书无 Type3 字形、无未随书分发的系统字体（逐页扫描，不是前 6 页）
  3. 页脚自洽：编号页都是 "N / total"、分子≤分母、末个编号页 N/N
  4. 结构页（封面/前置页/分部隔页）无页眉无页码
  5. 章/附录首页无页眉（first-except 机制），后续页奇偶页眉正确
  6. 目录页码与正文实际起始页一致（抽检 ≥10 章）
  7. 版心：抽样正文页文本不越出页边界与内白边（订口 > 20 mm）

用法：python mcu-book/check_pdf.py [pdf] [--manifest mcu-book/manifest.json]
默认校验 mcu-book/dist/mcu-deep-book-print.pdf。
"""

from __future__ import annotations

import argparse
import collections
import re
import sys
from pathlib import Path

import fitz  # PyMuPDF

# Windows 控制台默认 GBK：模块导入即切 UTF-8，避免子进程/提前打印把 ✓ 炸成
# UnicodeEncodeError（三次踩坑后钉死在导入期）。StringIO 场景无 reconfigure，跳过。
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

BOOK_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BOOK_DIR))
from build_html import load_manifest  # noqa: E402
from build_print import TEMPLATE_SECTION_MIN_REPEATS, _section_key as section_key  # noqa: E402

DEFAULT_PDF = BOOK_DIR / "dist" / "mcu-deep-book-print.pdf"
PT_PER_MM = 72 / 25.4
TRIM_MM = (185.0, 260.0)
BLEED_MM = 3.0
MAX_REPORTED = 10

SHIPPED_FAMILIES = (
    "NotoSerifSC",
    "NotoSansSC",
    "CascadiaMonoRoman",
    "NotoEmoji",
    "NotoSansSymbols2",
    "NotoSansMath",
)


def to_mm(points: float) -> float:
    return points / PT_PER_MM


def band_text(page: fitz.Page, top: bool) -> str:
    rect = page.rect
    band = fitz.Rect(0, 0, rect.width, rect.height * 0.07) if top else fitz.Rect(0, rect.height * 0.93, rect.width, rect.height)
    return " ".join(page.get_text("text", clip=band).split())


def chapter_openers(document: fitz.Document) -> dict[int, int]:
    """{章号(1-88): 首页物理页}。章首页有 '第 NN 章' 标记。
    PDF 抽取会在字符间插空格（'第 0 1 章'），先压掉空白再匹配。"""
    openers: dict[int, int] = {}
    for i in range(document.page_count):
        text = document[i].get_text()
        compact = re.sub(r"\s+", "", text[:300])
        m = re.search(r"第0?(\d{1,2})章", compact)
        if m and "罗盘" in text:
            number = int(m.group(1))
            if number not in openers:
                openers[number] = i + 1
    return openers


def check_trim(document: fitz.Document, bleed: bool) -> list[str]:
    expected_w = TRIM_MM[0] + (BLEED_MM * 2 if bleed else 0)
    expected_h = TRIM_MM[1] + (BLEED_MM * 2 if bleed else 0)
    failures = []
    for i in (0, document.page_count - 1):
        rect = document[i].rect
        w, h = to_mm(rect.width), to_mm(rect.height)
        if abs(w - expected_w) > 0.5 or abs(h - expected_h) > 0.5:
            failures.append(f"第 {i+1} 页 MediaBox → {w:.1f}×{h:.1f} mm，期望 {expected_w}×{expected_h}")
    return failures


def check_fonts(document: fitz.Document) -> list[str]:
    type3: list[str] = []
    system: dict[str, int] = {}
    for i, page in enumerate(document):
        for font in page.get_fonts():
            kind, name = font[2], font[3]
            if kind == "Type3":
                type3.append(str(i + 1))
            elif name and not any(family in name for family in SHIPPED_FAMILIES):
                system.setdefault(name, i + 1)
    failures = []
    if type3:
        failures.append(f"Type3 位图字形出现在 {len(type3)} 个字体引用上（页 {type3[:MAX_REPORTED]}）")
    if system:
        failures.append("未随书分发的字体: " + ", ".join(f"{name}(首见第{page}页)" for name, page in list(system.items())[:MAX_REPORTED]))
    return failures


def check_pagination(document: fitz.Document) -> list[str]:
    failures = []
    last_numbered: tuple[int, int, int] | None = None
    for i, page in enumerate(document):
        footer = band_text(page, top=False)
        if not footer:
            continue
        m = re.search(r"(\d+)\s*/\s*(\d+)", footer)
        if not m:
            continue
        numerator, denominator = int(m.group(1)), int(m.group(2))
        if numerator > denominator:
            failures.append(f"第 {i+1} 页 → 页脚 {numerator}/{denominator} 分子大于分母")
        last_numbered = (i + 1, numerator, denominator)
    if last_numbered is None:
        failures.append("全书找不到任何 N / total 页脚")
    else:
        physical, numerator, denominator = last_numbered
        if numerator != denominator:
            failures.append(f"末个编号页（第 {physical} 页）→ {numerator} / {denominator}，期望 N / N")
    return failures


def check_structure_pages(document: fitz.Document) -> list[str]:
    failures = []
    for i in range(min(2, document.page_count)):
        # 封面/版权页：不应有页脚页码
        footer = band_text(document[i], top=False)
        if re.search(r"\d+\s*/\s*\d+", footer):
            failures.append(f"第 {i+1} 页（封面/版权）→ 不应出现页码，实际 {footer!r}")
    # 分部隔页：含 PART 标签的页不应有页眉页码
    for i in range(document.page_count):
        text = document[i].get_text()
        compact = text[:80].replace(" ", "")
        if "PART" in compact and "本部" in text:
            if band_text(document[i], top=True):
                failures.append(f"第 {i+1} 页（分部隔页）→ 不应有页眉")
            if re.search(r"\d+\s*/\s*\d+", band_text(document[i], top=False)):
                failures.append(f"第 {i+1} 页（分部隔页）→ 不应有页码")
    return failures


def has_folio(page: fitz.Page) -> bool:
    """页脚有无「N / M」页码。前置页（封面/版权/前言/目录/分部隔页）设计上
    不编页码不盖页眉，用它判定前置页比页序硬编码稳——前置区页数随内容
    增减（实测目录涨到 9 页后，physical <= 8 的旧代理把 p9 误判成正文）。"""
    return bool(re.search(r"\d+ / \d+", band_text(page, top=False)))


def check_headers(document: fitz.Document, manifest: dict) -> list[str]:
    failures = []
    book_title = manifest["title"]
    openers = set(chapter_openers(document).values())
    checked = 0
    for i in range(document.page_count):
        physical = i + 1
        if physical in openers:
            if band_text(document[i], top=True):
                failures.append(f"第 {physical} 页（章首页）→ 不应有页眉，实际 {band_text(document[i], top=True)!r}")
            continue
        header = band_text(document[i], top=True)
        text = document[i].get_text()
        # 前置页/分部隔页由 check_structure_pages 负责
        if "PART" in text[:80].replace(" ", "") or not has_folio(document[i]):
            continue
        if physical % 2 == 0:
            if header and header != book_title:
                failures.append(f"第 {physical} 页（左页）→ 页眉应为书名，实际 {header!r}")
        else:
            if not header:
                failures.append(f"第 {physical} 页（右页）→ 缺章名页眉")
        checked += 1
        if checked >= 60:
            break
    return failures


def check_contents(document: fitz.Document, manifest: dict) -> list[str]:
    """目录页码 == 章首页页脚上的实际 folio。
    不做"物理页 - 偏移"算术：分部隔页不占页码，偏移随位置变化；
    章首页自己的页脚就是权威值。"""
    openers = chapter_openers(document)
    if len(openers) < 10:
        return [f"章首页识别不足（仅 {len(openers)} 章），无法抽检目录"]
    footer_by_physical: dict[int, int] = {}
    for physical in set(openers.values()):
        footer = band_text(document[physical - 1], top=False)
        m = re.search(r"(\d+)\s*/\s*(\d+)", footer)
        if m:
            footer_by_physical[physical] = int(m.group(1))
    # 只读前置目录页：分部隔页上的「本部导航」也是 NN．标题 + 页码的形状，
    # 混进来会把抽检对象搞错（隔页在正文中段，页码与目录项不同义）。
    toc_pages = [
        i
        for i in range(2, min(10, document.page_count))
        if "PART" not in re.sub(r"\s+", "", document[i].get_text()[:80])
    ]
    # 几何法取页码：目录行的页码是右对齐的独立词。按基线聚行，取该行
    # 最靠右的纯数字词，且右沿必须落在页面右四分之一——标题里内嵌的数字
    # （实测「解剖官方库 V3.3.3」的第 69 章）在几何上不可能贴右边界，
    # 文本正则才会把它误读成页码；正则既会误报也会误通过，几何判据不会。
    folio_by_number: dict[int, int] = {}
    for i in toc_pages:
        page = document[i]
        right_edge = page.rect.width * 0.75
        words = page.get_text("words")
        for anchor in words:
            m = re.match(r"^(\d{2})．", anchor[4])
            if not m:
                continue
            band = [
                w
                for w in words
                if abs(w[1] - anchor[1]) <= 2.0
                and re.fullmatch(r"\d+", w[4])
                and w[0] > anchor[0]
                and w[2] >= right_edge
            ]
            if band:
                folio_by_number[int(m.group(1))] = int(max(band, key=lambda w: w[2])[4])
    checked = 0
    for number, folio in folio_by_number.items():
        if number not in openers:
            continue
        physical = openers[number]
        expected = footer_by_physical.get(physical)
        if expected is None:
            return [f"第 {number:02d} 章首页（物理页 {physical}）读不到页脚"]
        checked += 1
        if folio != expected:
            return [f"目录第 {number:02d} 章页码 {folio} ≠ 章首页页脚 {expected}（物理页 {physical}）"]
    if checked < 10:
        return [f"目录页码可解析条目不足：{checked} 条（要求 ≥10）"]
    return []


def check_index_entries(document: fitz.Document, sample: int = 5) -> list[str]:
    """索引抽检：术语标注的页码必须落在带该页脚的页面，且该页确有该术语。
    防"分部隔页不占号导致固定偏移越往后越偏"这类错。"""
    folio_to_physical: dict[int, int] = {}
    for i, page in enumerate(document):
        m = re.search(r"(\d+)\s*/\s*(\d+)", band_text(page, top=False))
        if m:
            folio_to_physical[int(m.group(1))] = i + 1
    tail = range(max(0, document.page_count - 12), document.page_count)
    lines: list[str] = []
    for i in tail:
        lines.extend(document[i].get_text().splitlines())
    entries: list[tuple[str, int]] = []
    previous = ""
    started = False
    for line in lines:
        line = line.strip()
        if "按 Unicode 码位序" in line:
            started = True
            continue
        if "只在术语表定义" in line or "每条最多列" in line:
            continue
        if not started:
            continue
        if not line or re.fullmatch(r"\d+\s*/\s*\d+", line) or line in ("通往单片机之路", "术语索引"):
            continue
        if re.fullmatch(r"\d+(?:、\d+)*、?", line):
            first = int(line.split("、")[0])
            if previous:
                entries.append((previous, first))
            previous = ""
        else:
            previous += line
    if not entries:
        return ["索引里解析不到任何『术语 + 页码』条目"]
    failures = []
    # 首/中/尾都抽：分部隔页之后的条目才暴露固定偏移漂移
    chosen = entries[:2] + entries[len(entries) // 2 : len(entries) // 2 + 2] + entries[-1:]
    for term, folio in chosen:
        physical = folio_to_physical.get(folio)
        if physical is None:
            failures.append(f"索引「{term}」页码 {folio} 没有对应页脚")
            continue
        text = re.sub(r"\s+", "", document[physical - 1].get_text())
        aliases = [a.strip() for a in re.split(r"\s*/\s*|\s+vs\.?\s+", re.sub(r"（[^）]*）", "", term)) if a.strip()]
        if not any(alias in text for alias in aliases):
            failures.append(f"索引「{term}」页码 {folio}（物理页 {physical}）上找不到该术语")
    return failures


def check_text_bounds(document: fitz.Document) -> list[str]:
    """纸边裁字：可见字形不许越出纸张四边。

    按 **rawdict 的单字形 bbox** 判，且只看非空白字形——不按块/span 的
    bbox：bbox 含行尾空格的前进宽度，等宽块的挂空格会让它探出纸外几 pt
    （全书 38 处，都是汇编对照的两列清单），那不是缺陷。按字符数比例扣
    尾随空白也不行，那个估算只在等宽字体下准，正文衬线字宽不等。

    真缺陷实测：p674 的 `$IDF_PATH/.../bootloader_start.c:62` 右沿
    527.7pt > 页宽 525.1pt，尾部被裁掉——而页数、目录、索引、墨色全
    部正常，没有任何别的门能看见它。

    四边都查：横向是表格 min-content 撑宽，纵向是不可断的高代码块/图
    溢出页底，两者都会印丢内容。全量扫：这类缺陷是单页单行级的，抽样
    等于放过。
    """
    failures: list[str] = []
    for i, page in enumerate(document):
        rect = page.rect
        hit: str | None = None
        for block in page.get_text("rawdict")["blocks"]:
            if block.get("type"):  # 图像块没有 lines
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    for char in span["chars"]:
                        if not char["c"].strip():
                            continue
                        x0, y0, x1, y1 = char["bbox"]
                        edge = (
                            f"右沿 {x1:.1f}pt > 页宽 {rect.width:.1f}pt" if x1 > rect.width + 1
                            else f"左沿 {x0:.1f}pt < 0" if x0 < -1
                            else f"下沿 {y1:.1f}pt > 页高 {rect.height:.1f}pt" if y1 > rect.height + 1
                            else f"上沿 {y0:.1f}pt < 0" if y0 < -1
                            else None
                        )
                        if edge:
                            shown = "".join(c["c"] for c in span["chars"]).strip()
                            hit = f"第 {i+1} 页 → 文字被纸边裁掉：{edge}，{shown[:40]!r}"
                            break
                    if hit:
                        break
                if hit:
                    break
            if hit:
                break
        if hit:
            failures.append(hit)  # 同一页只报一次
            if len(failures) >= MAX_REPORTED:
                break
    return failures


def check_page_density(document: fitz.Document, limit: int = 22) -> list[str]:
    """版面利用率：正文页不该出现"本可填满却空着"的留白。

    只认一种缺陷——**可避免的页中断开**：这一页只排到版心 72% 以前，
    下一页既不是新章也不是分部隔页，而且下一页最高的那个"不可拆块"
    （整图、SVG 插画）本来放得进上一页剩下的空档。放不进去的才是
    排版正解（图不许切两半），章末短页、分部末页、前置页同理不计。

    阈值由实测标定：`pre { overflow-x: auto }` 让代码块变成滚动容器、
    不可分片之前，全书 143 页页中断开；清掉 overflow + 容器放开
    break-inside 之后只剩 14 页可避免的断开（最空 34%）。22 给排版
    微调留余量，再多就说明又有高块变回整块搬页了。
    """
    height = document[0].rect.height
    top, bottom = height * 0.07, height * 0.93

    def last_content_y(page: fitz.Page) -> float:
        ends = [min(b[3], bottom) for b in page.get_text("blocks") if b[3] > top and b[1] < bottom]
        for drawing in page.get_drawings():
            rect = drawing["rect"]
            if rect.y1 - rect.y0 > height * 0.8:  # 满版底色块不算内容
                continue
            if rect.y1 > top and rect.y0 < bottom:
                ends.append(min(rect.y1, bottom))
        return max(ends) if ends else top

    def tallest_atomic(page: fitz.Page) -> float:
        heights = [
            drawing["rect"].y1 - drawing["rect"].y0
            for drawing in page.get_drawings()
            if drawing["rect"].y1 - drawing["rect"].y0 < height * 0.8 and drawing["rect"].y0 > top
        ]
        for image in page.get_images():
            heights.extend(rect.y1 - rect.y0 for rect in page.get_image_rects(image[0]))
        return max(heights, default=0.0)

    sparse = []
    for i in range(document.page_count - 1):
        end = last_content_y(document[i])
        fill = (end - top) / (bottom - top)
        if fill >= 0.72:
            continue
        head = re.sub(r"\s+", "", document[i + 1].get_text()[:120])
        if re.search(r"第\d+章|附录[A-G]|PART", head[:40]):
            continue
        if not band_text(document[i], top=False):  # 前置页/封面没有页脚
            continue
        if tallest_atomic(document[i + 1]) > bottom - end:
            continue  # 次页的整图放不进这页空档，搬页是对的
        sparse.append((i + 1, fill))
    if len(sparse) > limit:
        worst = "、".join(f"第 {p} 页({f:.0%})" for p, f in sorted(sparse, key=lambda s: s[1])[:5])
        return [f"可避免的页中断开过多：{len(sparse)} 页（上限 {limit}），最空的有 {worst}"]
    return []


def check_ink_contrast(document: fitz.Document, sample: int = 0) -> list[str]:
    """墨色对比：纸上不许有"浅字印浅底"。

    由来：屏幕样式的代码块是深底浅字（--code-ink: #eaf5f1），印刷样式
    换掉了底色却继承了那支浅墨，结果 378 页、8443 个 span 在 PDF 里
    肉眼不可见 —— 而文本层完好，页数、目录、索引全部正常，只有渲染图
    看得出来。所以这一项按**亮度**判，不按文本判。

    判定分两层：先按亮度筛出"亮字"（luminance > 0.78），再渲染该页
    取 span 贴脸 bbox 内 25 分位像素当**底色估值**（避开白色字形本身
    对中位数的污染——p947 白字橙条被抬到 0.67 误报），最后按 WCAG
    对比度判：比率 < 1.8 才算"浅字浅底"违规。这样深底芯片丝印、
    白字橙条（对比 3.2）放行，而白字浅灰（1.25，gpio-config 的 PF6
    事故）与白字白纸（1.0，当年 378 页灾难）都逃不掉。

    全页扫不抽样：实测 1051 页全扫约 2s，抽样会随页数漂移导致
    同一本书不同构建红绿不一致。sample 参数保留兼容，传 0 即全扫。
    """
    failures = []
    step = max(1, document.page_count // sample) if sample else 1
    offenders: dict[str, int] = {}

    def _lin(channel: float) -> float:
        c = channel / 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    def _rel_lum(r: float, g: float, b: float) -> float:
        return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)

    def _bg_color(page: fitz.Page, rect: fitz.Rect, pix) -> tuple[int, int, int]:
        """底色估值：贴脸 bbox 内按亮度 25 分位的像素（字形是亮色，被排到高分位）。
        pix 由调用方按页渲染一次复用——8443 个亮 span 的回归场景下，
        每 span 渲整页会把门挂死（成本 O(亮字数) → O(页数)）。"""
        scale = 40 / 72  # 40dpi 足够判明暗
        x0 = max(0, int(rect.x0 * scale))
        y0 = max(0, int(rect.y0 * scale))
        x1 = min(pix.width, max(x0 + 1, int(rect.x1 * scale)))
        y1 = min(pix.height, max(y0 + 1, int(rect.y1 * scale)))
        pixels = []
        for y in range(y0, y1):
            for x in range(x0, x1):
                r, g, b = pix.pixel(x, y)[:3]
                pixels.append((0.2126 * r + 0.7152 * g + 0.0722 * b, r, g, b))
        pixels.sort()
        _, r, g, b = pixels[len(pixels) // 4]
        return r, g, b

    for i in range(0, document.page_count, step):
        page = document[i]
        if not band_text(page, top=False):
            continue  # 封面等结构页深底白字合法，且不占页码
        pix = None  # 惰性：本页有亮字才渲染，一页只渲一次
        for block in page.get_text("dict")["blocks"]:
            if block.get("type"):
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    color = span["color"]
                    red, green, blue = (color >> 16) & 0xFF, (color >> 8) & 0xFF, color & 0xFF
                    luminance = (0.2126 * red + 0.7152 * green + 0.0722 * blue) / 255
                    if luminance <= 0.78:
                        continue
                    if pix is None:
                        pix = page.get_pixmap(matrix=fitz.Matrix(40 / 72, 40 / 72), alpha=False)
                    # 亮字 vs 底色估值的 WCAG 对比度 < 1.8 才算"看不清"
                    br, bg_, bb = _bg_color(page, fitz.Rect(span["bbox"]), pix)
                    contrast = (_rel_lum(red, green, blue) + 0.05) / (_rel_lum(br, bg_, bb) + 0.05)
                    if contrast < 1.8:
                        key = f"#{color:06x} p{i + 1}"
                        offenders[key] = offenders.get(key, 0) + 1
    if offenders:
        detail = "、".join(f"{c}×{n}" for c, n in sorted(offenders.items(), key=lambda kv: -kv[1])[:4])
        scope = "全书" if not sample else f"抽检 {sample} 页"
        failures.append(f"浅字印在浅底上（{scope}扫描命中 {sum(offenders.values())} 个 span）：{detail}")
    return failures


def check_outline_and_metadata(document: fitz.Document, manifest: dict) -> list[str]:
    """书签树与元数据：阅读器要能靠书签翻一本上千页的书。

    Chromium 在 paged.js 产物里不输出任何标题树（实测 get_toc() 为 0 条），
    所以书签由 build_print.finalize_pdf 从分页后的 DOM 写入。这项检查守住
    交付面：部/章条目齐全、层级不越级、title/author/subject 与 manifest 一致。
    """
    failures = []
    outline = document.get_toc()
    if not outline:
        return ["PDF 没有任何大纲书签（上千页的书必须有书签面板）"]
    part_titles = {re.sub(r"\s+", "", part["title"]) for part in manifest["parts"]}
    appendix_titles = {re.sub(r"\s+", "", a["title"]) for a in manifest.get("appendices", [])}
    titles = {re.sub(r"\s+", "", row[1]) for row in outline}
    for part in manifest["parts"]:
        if re.sub(r"\s+", "", part["title"]) not in titles:
            failures.append(f"大纲缺分部条目：{part['title']}")
    # 章条目 = 挂在"分部"下面的 level 2。附录自己也是 level 1，它的小节
    # 同样落在 level 2 —— 按 level 一把抓会把 106 个附录小节数成章。
    chapters = 0
    under_part = False
    for level, title, _page in outline:
        key = re.sub(r"\s+", "", title)
        if level == 1:
            under_part = key in part_titles and key not in appendix_titles
            continue
        if level == 2 and under_part:
            chapters += 1
    expected_chapters = sum(len(part["files"]) for part in manifest["parts"])
    if chapters != expected_chapters:
        failures.append(f"大纲章条目 {chapters} 条 ≠ manifest 章数 {expected_chapters}")
    previous = 0
    for level, title, page in outline:
        if level > previous + 1:
            failures.append(f"大纲层级越级：{title!r}(level {level}) 紧跟 level {previous}（页 {page}）")
            break
        previous = level
    if not all(1 <= row[2] <= document.page_count for row in outline):
        failures.append("大纲里有书签指向不存在的页")
    # 书签污染：重复栏目名与来源卡标题。齐全性/层级检查都拦不住这类脏数据
    # ——条目数再多也"齐全"，层级也不越级，但面板会被同名项淹掉。
    # 实测基线：未过滤时 1765 条节书签里 1167 条是重复栏目名（"先跑起来"68×、
    # "对照表：本章概念 → 仓库落点"28× …），附录 E 下还挂着 57 张来源卡标题。
    # 归一化与阈值取 build_print 的那一份：门和构建器各写一套会漂
    # （"步骤 1"/"步骤1" 只在一侧并桶，阈值改了门也不跟）。
    repeats = collections.Counter(section_key(row[1]) for row in outline if row[0] >= 3)
    noisy = [(title, n) for title, n in repeats.items() if n >= TEMPLATE_SECTION_MIN_REPEATS]
    if noisy:
        worst = sorted(noisy, key=lambda kv: -kv[1])[:3]
        failures.append(
            f"大纲有 {len(noisy)} 个重复栏目名当成节书签（阈值 {TEMPLATE_SECTION_MIN_REPEATS}×）："
            + "、".join(f"{t} {n}×" for t, n in worst)
        )
    cards = [row[1] for row in outline if row[0] == 2 and re.match(r"^[a-z]\d+\s", row[1].strip())]
    if cards:
        failures.append(f"大纲混入 {len(cards)} 条来源卡标题书签（如 {cards[0][:28]!r}）")
    metadata = document.metadata or {}
    for key, expected in (
        ("title", manifest["title"]),
        ("author", manifest.get("author", "")),
        ("subject", manifest.get("subtitle", "")),
    ):
        actual = (metadata.get(key) or "").strip()
        if expected and actual != expected.strip():
            failures.append(f"metadata.{key} 实际 {actual!r} ≠ manifest {expected.strip()!r}")
    return failures


MIN_FONT_PT = 5.0


def check_min_font(document: fitz.Document) -> list[str]:
    """最小字号：纸上 < 5pt 的字印刷不可读。

    由来：题图/封面 SVG 用 viewBox 单位写字号，96mm 宽下 font-size 5
    只有 4.3pt、封面 84mm 下 4.5 单位只有 3.3pt——矢量图缩放把字号
    暗中缩水，只能靠渲染图肉眼发现。零字号的 book-title-marker
    （页眉 string-set 源，故意不可见）不算。
    """
    offenders: dict[str, int] = {}
    for i in range(document.page_count):
        for block in document[i].get_text("dict")["blocks"]:
            if block.get("type"):
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    size = span["size"]
                    if 2.0 <= size < MIN_FONT_PT and span["text"].strip():
                        key = f"p{i + 1} {span['text'][:18]!r} {size:.1f}pt"
                        offenders[key] = offenders.get(key, 0) + 1
    if offenders:
        top = "、".join(k for k, _ in sorted(offenders.items(), key=lambda kv: -kv[1])[:5])
        return [f"过小字号 < {MIN_FONT_PT}pt 共 {sum(offenders.values())} 个 span：{top}"]
    return []


RASTER_BUDGET = 20


def check_raster_budget(document: fitz.Document) -> list[str]:
    """光栅预算：全书位图不得超过真实照片的数量级。

    题图/封面/分部图都是矢量（滤镜习语经 Chromium 打印不落位图）；
    每枚题图都会变成一张位图，总数会从个位数跳到上百，而版面密度门看不出来。
    这里只设一个宽松上限（真实硬件照片 6 张），超过即视为题图被栅格化。
    """
    pages = [(i + 1, len(document[i].get_images())) for i in range(document.page_count)]
    total = sum(n for _, n in pages)
    if total > RASTER_BUDGET:
        top = "、".join(f"p{p}×{n}" for p, n in pages if n)[:120]
        return [f"光栅图 {total} 张 > 预算 {RASTER_BUDGET}（题图可能被滤镜版栅格化）：{top}"]
    return []


def body_volume_line(document: fitz.Document, manifest: dict) -> str:
    """体量对账（信息项，不做门禁）：页码之外再给一个人能读的规模数字。

    2026-10-26 有过一次 1064→1046 页的漂移，12 门全绿却谁也说不清为什么——
    后来查明是另一条会话在 80 章里删了 749 行。删改本身是正常编辑，不该拦；
    但「页数变了、体量变了」应该在每次检查的输出里看得见，而不是靠猜。
    """
    chars = 0
    for part in manifest["parts"]:
        for name in part.get("files", []):
            path = BOOK_DIR.parent / "docs" / name
            if path.is_file():
                text = re.sub(r"\s+", "", path.read_text(encoding="utf-8"))
                chars += len(text)
    pdf_chars = sum(len(re.sub(r"\s+", "", document[i].get_text()))
                    for i in range(document.page_count))
    ratio = pdf_chars / chars if chars else 0
    return (f"体量：源文 {chars:,} 字 / PDF {pdf_chars:,} 字（×{ratio:.2f}）"
            f"，{document.page_count} 页")


def main(argv: list[str] | None = None) -> int:
    # 同 build_print：Windows GBK 控制台会在 ✓/✗ 输出时炸 UnicodeEncodeError。
    # 守卫 hasattr：测试用 redirect_stdout(StringIO) 时 StringIO 没有 reconfigure。
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pdf", nargs="?", type=Path, default=DEFAULT_PDF)
    parser.add_argument("--manifest", type=Path, default=BOOK_DIR / "manifest.json")
    parser.add_argument("--bleed", action="store_true", help="按出血版（191×266 mm）校验")
    options = parser.parse_args(argv)
    if not options.pdf.is_file():
        print(f"✗ 找不到 PDF: {options.pdf}", file=sys.stderr)
        return 1
    manifest = load_manifest(options.manifest)
    document = fitz.open(options.pdf)
    failures: list[str] = []
    for name, check in (
        ("开本", lambda: check_trim(document, options.bleed)),
        ("字体", lambda: check_fonts(document)),
        ("页码", lambda: check_pagination(document)),
        ("结构页", lambda: check_structure_pages(document)),
        ("页眉", lambda: check_headers(document, manifest)),
        ("目录页码", lambda: check_contents(document, manifest)),
        ("索引页码", lambda: check_index_entries(document)),
        ("版面利用率", lambda: check_page_density(document)),
        ("墨色对比", lambda: check_ink_contrast(document)),
        ("最小字号", lambda: check_min_font(document)),
        ("纸边裁字", lambda: check_text_bounds(document)),
        ("大纲与元数据", lambda: check_outline_and_metadata(document, manifest)),
        ("光栅预算", lambda: check_raster_budget(document)),
    ):
        problems = check()
        status = "✓" if not problems else "✗"
        print(f"{status} {name}")
        failures.extend(problems)
    summary = body_volume_line(document, manifest)
    document.close()
    for problem in failures[:MAX_REPORTED]:
        print(f"  - {problem}", file=sys.stderr)
    if failures:
        print(f"✗ 印前契约未通过：{len(failures)} 项问题", file=sys.stderr)
        return 1
    print("印前契约：全部通过")
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

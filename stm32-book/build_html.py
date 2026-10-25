#!/usr/bin/env python3
"""Build the offline HTML/PDF edition of the STM32 book."""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import html
import json
import mimetypes
import re
import shutil
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

import markdown


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parent
DOCS_DIR = REPO_ROOT / "docs"
BOOK_DIR = ROOT / "book"
DIST_DIR = ROOT / "dist"
MANIFEST_PATH = ROOT / "manifest.json"
TOKENS_PATH = ROOT / "styles" / "tokens.json"
BOOK_CSS_PATH = ROOT / "styles" / "book.css"
OUTPUT_NAME = "stm32-practical-book.html"
PDF_NAME = "stm32-practical-book.pdf"
CHAPTER_NAME = re.compile(r"^(?:0\d|1\d|2[0-8])-.+\.md$")
VIDEO_OPEN = re.compile(r"<!--\s*video:(ch\d+)\s*-->")
VIDEO_CLOSE = re.compile(r"<!--\s*/video:(ch\d+)\s*-->")
VIDEO_BLOCK = re.compile(
    r"<!--\s*video:(ch\d+)\s*-->.*?<!--\s*/video:\1\s*-->", re.DOTALL
)
HEADING_EMOJI = re.compile(
    r"^(#{2,3})(?!#)\s+"
    r"(?:[\U0001F300-\U0001FAFF\u2600-\u27BF]\uFE0F?\s*)+"
    r"(\S.*?)\s*$"
)
RESOURCE_HEADING = re.compile(
    r"^##(?!#)[ \t]+"
    r"(?:[\U0001F300-\U0001FAFF\u2600-\u27BF]\uFE0F?[ \t]*)*"
    r"(?P<title>相关资源|权威来源与冻结点|Related resources|Further reading|Sources"
    r"|Authoritative sources and frozen versions)"
    r"[ \t]*$",
    re.MULTILINE,
)
PROMO_RESOURCE_LINE = re.compile(
    r"mp\.weixin\.qq\.com|手机阅读版|(?:上一篇|下一篇)\s*[:：]"
    r"|免责声明：本仓库插画均为作者自绘"
    r"|(?:Previous|Next)\s*:"
    r"|Disclaimer:\s*every illustration"
    r"|^\s*-\s*Related\s*:",
    re.IGNORECASE,
)
CENTERED_FIGURE = re.compile(
    r"<p\s+align=[\"']center[\"']>\s*"
    r"(?P<images>(?:\s*<img\b[^>]*>\s*)+)"
    r"(?:<br\s*/?>\s*<sub>(?P<caption>.*?)</sub>\s*)?"
    r"</p>",
    re.IGNORECASE | re.DOTALL,
)
HREF_ATTR = re.compile(r"(?P<prefix>\bhref\s*=\s*)(?P<quote>[\"'])(?P<value>.*?)(?P=quote)", re.I)
SRC_ATTR = re.compile(r"(?P<prefix>\bsrc\s*=\s*)(?P<quote>[\"'])(?P<value>.*?)(?P=quote)", re.I)
ID_ATTR = re.compile(r"(?P<prefix>\bid\s*=\s*)(?P<quote>[\"'])(?P<value>.*?)(?P=quote)", re.I)
TABLE_BLOCK = re.compile(r"<table\b[^>]*>.*?</table>", re.I | re.DOTALL)
TABLE_ROW = re.compile(r"<tr\b[^>]*>.*?</tr>", re.I | re.DOTALL)
TABLE_CELL = re.compile(r"<(?:th|td)\b", re.I)



class BuildError(RuntimeError):
    """Raised when the manuscript violates the whole-book contract."""


def load_manifest(path: Path = MANIFEST_PATH) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BuildError(f"cannot read manifest {path}: {exc}") from exc


def source_chapters(docs_dir: Path = DOCS_DIR) -> list[str]:
    return sorted(path.name for path in docs_dir.glob("*.md") if CHAPTER_NAME.match(path.name))


def edition_dirs(manifest: dict) -> tuple[Path, Path]:
    docs_dir = (REPO_ROOT / manifest.get("docs_dir", "docs")).resolve()
    book_dir = (ROOT / manifest.get("book_dir", "book")).resolve()
    return docs_dir, book_dir


def validate_manifest(manifest: dict) -> None:
    required = {
        "title",
        "subtitle",
        "version",
        "date",
        "parts",
        "chapter_guides",
        "appendices",
        "keywords",
        "sources",
    }
    missing_keys = sorted(required - set(manifest))
    if missing_keys:
        raise BuildError(f"manifest missing keys: {missing_keys}")

    parts = manifest["parts"]
    if not isinstance(parts, list) or not parts:
        raise BuildError("manifest parts must be a non-empty list")
    docs_dir, book_dir = edition_dirs(manifest)
    flattened = [name for part in parts for name in part.get("files", [])]
    expected = source_chapters(docs_dir)
    if flattened != expected or len(flattened) != len(set(flattened)):
        raise BuildError(f"chapter list mismatch: expected={expected}, actual={flattened}")

    guides = manifest["chapter_guides"]
    if set(guides) != set(expected):
        missing = sorted(set(expected) - set(guides))
        extra = sorted(set(guides) - set(expected))
        raise BuildError(f"chapter guide mismatch: missing={missing}, extra={extra}")

    source_ids = set(manifest["sources"])
    for name, guide in guides.items():
        for field in ("question", "deliverable", "boundary"):
            if not isinstance(guide.get(field), str) or not guide[field].strip():
                raise BuildError(f"empty chapter guide field: {name}:{field}")
        if not guide.get("sources"):
            raise BuildError(f"chapter guide has no sources: {name}")
        unknown = sorted(set(guide["sources"]) - source_ids)
        if unknown:
            raise BuildError(f"unknown chapter sources: {name}:{unknown}")

    closing_ids: set[str] = set()
    for part in parts:
        closing = part.get("closing")
        if closing is None:
            continue
        part_id = part.get("id", "")
        if not isinstance(closing, dict):
            raise BuildError(f"part closing must be an object: {part_id}")
        closing_id = closing.get("id", "")
        filename = closing.get("file", "")
        if (
            not isinstance(closing_id, str)
            or not closing_id.startswith("part-closing-")
            or closing_id in closing_ids
        ):
            raise BuildError(f"invalid part closing id: {part_id}:{closing_id}")
        closing_ids.add(closing_id)
        if (
            not isinstance(filename, str)
            or "/" in filename
            or "\\" in filename
            or not filename.endswith(".md")
            or filename in flattened
        ):
            raise BuildError(f"invalid part closing manuscript: {part_id}:{filename}")
        if not (book_dir / filename).is_file():
            raise BuildError(f"missing part closing manuscript: {filename}")

    appendix_ids: set[str] = set()
    appendix_files: set[str] = set()
    for appendix in manifest["appendices"]:
        appendix_id = appendix.get("id", "")
        filename = appendix.get("file", "")
        if not appendix_id.startswith("appendix-") or not appendix.get("title") or not filename:
            raise BuildError(f"invalid appendix entry: {appendix}")
        if appendix_id in appendix_ids or filename in appendix_files:
            raise BuildError(f"duplicate appendix entry: {appendix}")
        appendix_ids.add(appendix_id)
        appendix_files.add(filename)
        if not (book_dir / filename).is_file():
            raise BuildError(f"missing appendix manuscript: {filename}")

    validate_back_matter(manifest)
    validate_revisions(manifest)

    for source_id, source in manifest["sources"].items():
        if not re.fullmatch(r"[a-z0-9-]+", source_id):
            raise BuildError(f"invalid source id: {source_id}")
        for field in ("title", "authority", "url", "snapshot", "accessed", "license", "scope"):
            if not isinstance(source.get(field), str) or not source[field].strip():
                raise BuildError(f"empty source field: {source_id}:{field}")


def strip_video_blocks(text: str, source_label: str) -> str:
    opens = VIDEO_OPEN.findall(text)
    closes = VIDEO_CLOSE.findall(text)
    if opens != closes:
        raise BuildError(
            f"unclosed video block in {source_label}: opens={opens}, closes={closes}"
        )
    stripped, count = VIDEO_BLOCK.subn("", text)
    if count != len(opens):
        raise BuildError(f"malformed video block in {source_label}")
    return stripped


def extract_title(text: str, source_label: str) -> str:
    match = re.search(r"^#\s+(.+?)\s*$", text, re.MULTILINE)
    if not match:
        raise BuildError(f"missing chapter title: {source_label}")
    return match.group(1).strip()


_SOURCE_CHAPTER_PREFIX = re.compile(r"^\d{2}\s+")


def display_chapter_number(filename: str) -> int:
    """Reader-facing chapter number. Source files stay 00–28; the book shows 1–29."""
    match = re.match(r"(\d{2})", filename)
    if match is None:
        raise BuildError(f"chapter file is missing an index: {filename}")
    return int(match.group(1)) + 1


def source_chapter_heading(title: str) -> str:
    """Drop the file index that source chapters put on the Markdown H1."""
    stripped = _SOURCE_CHAPTER_PREFIX.sub("", title.strip(), count=1)
    if not stripped or stripped == title.strip():
        raise BuildError(f"chapter title is missing a file index: {title}")
    return stripped


def reader_chapter_title(manifest: dict, filename: str, source_title: str) -> str:
    label = ui(manifest, "chapter_kicker").format(n=display_chapter_number(filename))
    return f"{label} {source_chapter_heading(source_title)}"


def _outline_key(title: str) -> str:
    # Chromium drops a space when a heading wraps in the PDF outline, so
    # "Development Environment" can arrive as "DevelopmentEnvironment".
    return re.sub(r"\s+", "", title)


def outline_lookup_headings(manifest: dict) -> list[tuple[int, str, str]]:
    """Publication outline rows: level, bookmark label, heading text Chromium records.

    Chapters nest under their part. Appendices stay at the top level. The
    version history and subject index stay only because the book already
    bookmarks those pages. In-chapter H2/H3 headings are not rows.
    """
    docs_dir, book_dir = edition_dirs(manifest)
    rows: list[tuple[int, str, str]] = []
    revision = str(ui(manifest, "revision_title"))
    rows.append((1, revision, revision))
    for part in manifest["parts"]:
        part_title = str(part["title"])
        rows.append((1, part_title, part_title))
        for filename in part["files"]:
            raw = extract_title((docs_dir / filename).read_text(encoding="utf-8"), filename)
            rows.append((2, reader_chapter_title(manifest, filename, raw), source_chapter_heading(raw)))
        closing = part.get("closing")
        if closing:
            closing_title = extract_title(
                (book_dir / closing["file"]).read_text(encoding="utf-8"),
                closing["file"],
            )
            rows.append((2, closing_title, closing_title))
    for appendix in manifest["appendices"]:
        raw = extract_title(
            (book_dir / appendix["file"]).read_text(encoding="utf-8"),
            appendix["file"],
        )
        rows.append((1, str(appendix["title"]), raw))
    for item in manifest.get("back_matter") or []:
        title = str(item["title"])
        rows.append((1, title, title))
    keys = [_outline_key(source) for _level, _label, source in rows]
    if len(keys) != len(set(keys)):
        raise BuildError("publication outline headings are not unique")
    return rows


def publication_outline(manifest: dict, toc: list) -> list[list]:
    """Replace a heading-per-section outline with parts, chapters, and appendices."""
    pages: dict[str, tuple[int, int]] = {}
    for item in toc:
        level = int(item[0])
        title = _outline_key(str(item[1]))
        page = int(item[2])
        if page < 1 or not title:
            continue
        previous = pages.get(title)
        if previous is None or level < previous[0]:
            pages[title] = (level, page)
    outline: list[list] = []
    for level, label, source in outline_lookup_headings(manifest):
        found = pages.get(_outline_key(source))
        if found is None:
            raise BuildError(f"PDF outline is missing a bookmark for {source!r}")
        outline.append([level, label, found[1]])
    return outline


def extract_quick_questions(text: str) -> list[str]:
    match = re.search(r"^\s*10\.\s*合上书，三问。(.+?)\s*$", text, re.MULTILINE)
    if not match:
        return []
    body = match.group(1).strip()
    questions = [piece.strip() + "？" for piece in body.split("？") if piece.strip()]
    return questions[:3]


def remove_chapter_frontmatter(text: str) -> str:
    text = re.sub(r"^#\s+.+?\s*$", "", text, count=1, flags=re.MULTILINE)
    text = re.sub(r"^>\s*English:\s*.+?\s*$", "", text, count=1, flags=re.MULTILINE)
    text = re.sub(r"^>\s*中文:\s*.+?\s*$", "", text, count=1, flags=re.MULTILINE)
    return text.strip()


def strip_heading_emoji(text: str) -> str:
    """Drop a leading emoji from ## and ### headings. Leave fenced code alone."""
    lines: list[str] = []
    fenced = False
    for line in text.splitlines(keepends=True):
        if line.lstrip().startswith("```"):
            fenced = not fenced
        elif not fenced:
            line = HEADING_EMOJI.sub(r"\1 \2", line)
        lines.append(line)
    return "".join(lines)


def strip_serial_resources(text: str) -> str:
    """Drop WeChat / prev-next lines from a chapter-end 相关资源 section.

    Official handbook lines stay. The website edition of docs/ is not edited.
    """
    match = RESOURCE_HEADING.search(text)
    if not match:
        return text
    rest = text[match.end():]
    following = re.search(r"^##(?!#)[ \t]+", rest, re.MULTILINE)
    if following:
        section, tail = rest[: following.start()], rest[following.start():]
    else:
        section, tail = rest, ""
    kept = [line for line in section.splitlines() if not PROMO_RESOURCE_LINE.search(line)]
    body = "\n".join(kept).strip()
    head = text[: match.start()].rstrip()
    title = match.group("title")
    if body:
        rebuilt = f"{head}\n\n## {title}\n\n{body}\n"
    else:
        rebuilt = head + "\n"
    if tail.strip():
        rebuilt = rebuilt.rstrip() + "\n\n" + tail.lstrip("\n")
    return rebuilt


def prepare_chapter_markdown(
    raw: str,
    source_label: str,
    language: str = "zh-CN",
) -> tuple[str, str, list[str]]:
    title = extract_title(raw, source_label)
    # English chapters repeat the Chinese narration, including 三问, inside the video block.
    questions = [] if str(language).lower().startswith("en") else extract_quick_questions(raw)
    text = strip_video_blocks(raw, source_label)
    text = strip_serial_resources(text)
    text = strip_heading_emoji(text)
    return title, remove_chapter_frontmatter(text), questions


def semanticize_figures(rendered: str) -> str:
    """Turn the known centered image + sub caption into figure/figcaption."""

    def replace(match: re.Match[str]) -> str:
        images = match.group("images").strip()
        caption = match.group("caption")
        if caption and caption.strip():
            text = re.sub(r"^\s*▲\s*", "", caption.strip())
            return f"<figure>{images}<figcaption>{text}</figcaption></figure>"
        return f"<figure>{images}</figure>"

    return CENTERED_FIGURE.sub(replace, rendered)


_CALLOUT_TIP = re.compile(
    r"^(?:提示|检索技巧|记忆[:：]|Tip\b|A tip\b|Search tip\b|A measuring tip\b|Remember\b)",
    re.IGNORECASE,
)


def classify_callouts(rendered: str, labels: dict[str, str] | None = None) -> str:
    """Turn plain Markdown blockquotes into note, tip, or warning callouts.

    The manuscript already uses ⚠️, 提示, and ordinary lead quotes. This only
    adds a class and a label; it does not rewrite the quoted text.
    """
    chosen = labels or {"warning": "注意", "tip": "提示", "note": "说明"}

    def replace(match: re.Match[str]) -> str:
        inner = match.group(1)
        text = re.sub(r"<[^>]+>", "", inner)
        text = html.unescape(text).replace("\xa0", " ").strip()
        if text.startswith("⚠") or text.startswith("警告") or text.lower().startswith("warning"):
            kind = "warning"
        elif _CALLOUT_TIP.match(text):
            kind = "tip"
        else:
            kind = "note"
        label = html.escape(chosen[kind])
        return (
            f'<blockquote class="callout callout-{kind}">'
            f'<p class="callout-label">{label}</p>{inner}</blockquote>'
        )

    return re.sub(r"<blockquote>(.*?)</blockquote>", replace, rendered, flags=re.DOTALL)


def _safe_local_path(source_file: Path, raw_path: str) -> Path:
    decoded = unquote(raw_path.replace("\\", "/"))
    target = (source_file.parent / decoded).resolve()
    try:
        target.relative_to(REPO_ROOT.resolve())
    except ValueError as exc:
        raise BuildError(f"local path escapes repository: {source_file}:{raw_path}") from exc
    return target


def _data_uri(path: Path) -> str:
    if not path.is_file():
        raise BuildError(f"missing local image: {path}")
    mime, _ = mimetypes.guess_type(path.name)
    if not mime or not mime.startswith("image/"):
        raise BuildError(f"unsupported local image type: {path}")
    payload = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{payload}"


def embed_local_images(rendered: str, source_file: Path) -> str:
    def replace_tag(match: re.Match[str]) -> str:
        tag = match.group(0)

        def replace_src(src_match: re.Match[str]) -> str:
            value = html.unescape(src_match.group("value")).strip()
            parts = urlsplit(value)
            if value.startswith("data:image/"):
                return src_match.group(0)
            if parts.scheme or parts.netloc:
                raise BuildError(f"external image is not offline-safe: {source_file}:{value}")
            target = _safe_local_path(source_file, parts.path)
            uri = _data_uri(target)
            quote = src_match.group("quote")
            return f"{src_match.group('prefix')}{quote}{uri}{quote}"

        return SRC_ATTR.sub(replace_src, tag, count=1)

    return re.sub(r"<img\b[^>]*>", replace_tag, rendered, flags=re.I)


def _repository_url(target: Path) -> str:
    relative = target.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    base = "https://github.com/zhuguang-ZFG/STM32"
    if target.is_dir():
        return f"{base}/tree/main/{relative}"
    if target.suffix.lower() == ".md":
        parent = target.parent.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
        return f"{base}/tree/main/{parent}"
    return f"{base}/blob/main/{relative}"


def rewrite_local_links(
    rendered: str,
    source_file: Path,
    chapter_anchors: dict[Path, str],
) -> str:
    def replace_href(match: re.Match[str]) -> str:
        original = html.unescape(match.group("value")).strip()
        if not original:
            return match.group(0)
        parts = urlsplit(original)
        if original.startswith("#") or parts.scheme or parts.netloc:
            value = original
            if re.search(r"\.md$", parts.path, re.I) and not parts.query:
                value = original + "?plain=1"
        else:
            target = _safe_local_path(source_file, parts.path)
            if target in chapter_anchors:
                value = f"#{chapter_anchors[target]}"
            elif target.is_file() and target.suffix.lower() in {
                ".svg",
                ".png",
                ".jpg",
                ".jpeg",
                ".gif",
                ".webp",
            }:
                value = _data_uri(target)
            elif target.exists():
                try:
                    target.relative_to((REPO_ROOT / "examples").resolve())
                    value = "#appendix-examples"
                except ValueError:
                    value = _repository_url(target)
            else:
                raise BuildError(f"missing local link: {source_file}:{original}")
        quote = match.group("quote")
        return f"{match.group('prefix')}{quote}{html.escape(value, quote=True)}{quote}"

    return HREF_ATTR.sub(replace_href, rendered)


def prefix_local_ids(rendered: str, prefix: str) -> str:
    ids = [match.group("value") for match in ID_ATTR.finditer(rendered)]
    mapping = {old: f"{prefix}-{old}" for old in ids}

    def replace_id(match: re.Match[str]) -> str:
        quote = match.group("quote")
        value = mapping[match.group("value")]
        return f"{match.group('prefix')}{quote}{value}{quote}"

    rendered = ID_ATTR.sub(replace_id, rendered)

    def replace_href(match: re.Match[str]) -> str:
        value = match.group("value")
        if value.startswith("#") and value[1:] in mapping:
            value = "#" + mapping[value[1:]]
        quote = match.group("quote")
        return f"{match.group('prefix')}{quote}{value}{quote}"

    return HREF_ATTR.sub(replace_href, rendered)


def render_markdown(source: str) -> str:
    renderer = markdown.Markdown(
        extensions=["extra", "toc", "sane_lists"],
        extension_configs={
            "toc": {"permalink": False},
            "extra": {"footnotes": {"UNIQUE_IDS": True}},
        },
        output_format="html5",
    )
    return renderer.convert(source)

def wrap_tables(rendered: str, table_label: str = "数据表，可横向滚动") -> str:
    def replace_table(match: re.Match[str]) -> str:
        table = match.group(0)
        first_row = TABLE_ROW.search(table)
        columns = len(TABLE_CELL.findall(first_row.group(0))) if first_row else 0
        if columns == 0:
            raise BuildError("rendered table has no cells")
        return (
            '<div class="table-scroll" role="region" tabindex="0" '
            f'aria-label="{html.escape(table_label, quote=True)}" '
            f'style="--table-columns: {columns}">{table}</div>'
        )

    return TABLE_BLOCK.sub(replace_table, rendered)



def render_document(
    source_text: str,
    source_file: Path,
    prefix: str,
    chapter_anchors: dict[Path, str],
    table_label: str = "数据表，可横向滚动",
    callout_labels: dict[str, str] | None = None,
) -> str:
    rendered = render_markdown(source_text)
    rendered = semanticize_figures(rendered)
    rendered = classify_callouts(rendered, callout_labels)
    rendered = wrap_tables(rendered, table_label)
    rendered = rewrite_local_links(rendered, source_file, chapter_anchors)
    rendered = embed_local_images(rendered, source_file)
    return prefix_local_ids(rendered, prefix)


UI = {
    "zh-CN": {
        "cover_kicker": "STM32 实战手册",
        "imprint_kicker": "版权页",
        "imprint_title": "版本与许可",
        "imprint_lead": "这一页记录本次构建的版本、日期和许可。引脚、时序和电气参数仍以目标型号手册为准。",
        "license_labels": ("版本", "版本日期", "构建日期", "作者", "原创正文与原创图片", "第三方实拍", "代码"),
        "repository_label": "仓库",
        "trademark": "STM32、STM32Cube、Nucleo、Discovery 是 STMicroelectronics 的商标。本书用于学习，与 ST 没有隶属关系。外部手册只作链接和事实引用，不随本书再分发。",
        "companion_title": "配套资源",
        "companion_body": "网页版、动画、示例和速查表在仓库里。手机连载在微信公众号「SIAI小宇宙」。书稿不逐章重复公众号链接，也不保留上一篇 / 下一篇导航。",
        "companion_note": "各章末仍保留手册编号和图示引用。插画是作者自绘或程序生成，不是厂商实拍。",
        "read_title": "这不是文章合集",
        "read_lead": "全书沿“开发闭环 → 引脚与时间 → 数据搬运 → 系统可靠性 → 项目交付 → 跨系列迁移 → 系统收束”推进。每章先用罗盘约定问题、交付和边界，再进入原章节；章末三问把结论拉回可检查的工程状态。",
        "routes": (
            ("第一次上手", "00–05 → 06/07/08 任一通信章 → 17 排错。"),
            ("做数据采集", "02 → 05 → 09 → 10 → 06/14 → 15。"),
            ("做可升级设备", "11 → 12 → 17 → 附录 A/B，补齐失败路径。"),
            ("迁移到新系列", "20/21 → 23/24/25；每次重新核对电源、复用、时钟、内存。"),
        ),
        "evidence": "证据口径：手册参数写文档号/修订点；GitHub 实现冻结 tag/commit；社区内容只作线索；“能跑”必须附期望、实际、测量条件和未覆盖边界。",
        "toc_title": "目录与分部目标",
        "appendix_heading": "附录",
        "toc_closing_note": "",
        "compass_label": "本章罗盘",
        "compass_question": "问题",
        "compass_deliverable": "交付",
        "compass_boundary": "边界",
        "compass_sources": "来源锚点",
        "quick_title": "合上书，三问",
        "quick_link": "做完再看附录 C 的参考答案",
        "back_to_toc": "返回目录 ↑",
        "toc_jump": "目录",
        "part_kicker": "第 {n} 部",
        "chapter_kicker": "第 {n} 章",
        "appendix_kicker": "附录",
        "callout_warning": "注意",
        "callout_tip": "提示",
        "callout_note": "说明",
        "closing_kicker": "收束",
        "closing_banner": "本部分到此结束",
        "revision_kicker": "文前",
        "revision_title": "版本与修订",
        "revision_lead": "这一页只记已经合并进书稿的版本。引脚、时序和电气参数仍以目标型号手册为准。",
        "front_heading": "文前",
        "back_matter_heading": "书末",
        "index_kicker": "书末",
        "index_lead": "这是书末主题索引，不是附录 D 的术语定义。条目按拉丁字母排列，链到章内小节。PDF 在该行右侧印出页码。",
        "footer": "本书由 stm32-book/build_html.py 从 {count} 章源文档构建；来源、冻结点与许可见附录 E。",
        "table_label": "数据表，可横向滚动",
        "skip": "跳到目录",
        "source_authority": "权威层级",
        "source_snapshot": "冻结点",
        "source_accessed": "访问日期",
        "source_license": "许可边界",
        "source_scope": "适用范围",
        "source_open": "打开来源",
    },
    "en": {
        "cover_kicker": "STM32 PRACTICAL BOOK",
        "imprint_kicker": "COLOPHON",
        "imprint_title": "Version and license",
        "imprint_lead": "This page records the version, dates, and license of this build. Pin, timing, and electrical values still come from the manual for the exact part.",
        "license_labels": ("Version", "Edition date", "Build date", "Author", "Original prose and drawings", "Third-party photos", "Code"),
        "repository_label": "Repository",
        "trademark": "STM32, STM32Cube, Nucleo, and Discovery are trademarks of STMicroelectronics. This book is for study and is not affiliated with ST. External manuals are linked and cited, not redistributed.",
        "companion_title": "Companion material",
        "companion_body": "The website, animations, examples, and cheatsheets live in the repository. The phone serialization is the WeChat account SIAI小宇宙. This book does not repeat those links, or the previous/next chapter navigation, at the end of every chapter.",
        "companion_note": "Handbook numbers and figure references stay at the end of a chapter. Drawings are by the author or generated; they are not vendor photographs.",
        "read_title": "This is not a pile of articles",
        "read_lead": "The book moves from a closed development loop, to pins and time, to moving data, to reliability, to delivery, to a new family, and then to a system. Each chapter opens with a compass — question, deliverable, boundary — and then the original chapter.",
        "routes": (
            ("First board", "00–05, then any of 06/07/08, then 17 when something breaks."),
            ("Data in and out", "02 → 05 → 09 → 10 → 06/14 → 15."),
            ("A device you can update", "11 → 12 → 17, then appendices A and B, including the failure path."),
            ("A different family", "20/21 → 23/24/25. Recheck power, alternate functions, clocks, and memory every time."),
        ),
        "evidence": "Evidence: cite a document number or revision for manual values; freeze a tag or commit for code; treat community posts as clues; a claim that it works needs the expected value, the measured value, the conditions, and what was not covered.",
        "toc_title": "Contents and part goals",
        "appendix_heading": "Appendices",
        "toc_closing_note": "",
        "compass_label": "Chapter compass",
        "compass_question": "Question",
        "compass_deliverable": "Deliverable",
        "compass_boundary": "Boundary",
        "compass_sources": "Sources",
        "quick_title": "Close the book: three questions",
        "quick_link": "Then compare with the answers in Appendix C",
        "back_to_toc": "Back to contents ↑",
        "toc_jump": "Contents",
        "part_kicker": "Part {n}",
        "chapter_kicker": "Chapter {n}",
        "appendix_kicker": "Appendix",
        "callout_warning": "Warning",
        "callout_tip": "Tip",
        "callout_note": "Note",
        "closing_kicker": "CLOSE",
        "closing_banner": "End of this part",
        "revision_kicker": "FRONT",
        "revision_title": "Version history",
        "revision_lead": "This page records editions that have already been merged. Pin, timing, and electrical values still come from the manual for the exact part.",
        "front_heading": "Front matter",
        "back_matter_heading": "Back matter",
        "index_kicker": "BACK MATTER",
        "index_lead": "This is the subject index, not the definitions in Appendix D. Entries are alphabetical and link to a chapter section. The PDF prints the page number at the right of the row.",
        "footer": "Built by stm32-book/build_html.py from {count} source chapters. Sources, frozen versions, and the license are in Appendix E.",
        "table_label": "Data table, scroll sideways",
        "skip": "Skip to contents",
        "source_authority": "Authority",
        "source_snapshot": "Snapshot",
        "source_accessed": "Accessed",
        "source_license": "License",
        "source_scope": "Scope",
        "source_open": "Open source",
    },
}


def ui(manifest: dict, key: str):
    language = str(manifest.get("language", "zh-CN"))
    table = UI["en"] if language.lower().startswith("en") else UI["zh-CN"]
    return table[key]


def callout_label_map(manifest: dict) -> dict[str, str]:
    return {
        "warning": ui(manifest, "callout_warning"),
        "tip": ui(manifest, "callout_tip"),
        "note": ui(manifest, "callout_note"),
    }


def compass_html(guide: dict, manifest: dict) -> str:
    source_links = " · ".join(
        f'<a href="#source-{html.escape(source_id)}">{html.escape(source_id)}</a>'
        for source_id in guide["sources"]
    )
    cards = (
        ("question", "compass_question", guide["question"]),
        ("deliverable", "compass_deliverable", guide["deliverable"]),
        ("boundary", "compass_boundary", guide["boundary"]),
    )
    card_html = "".join(
        f'<div class="compass-card compass-{role}">'
        f'<p class="compass-role">{html.escape(ui(manifest, key))}</p>'
        f"<p>{html.escape(text)}</p></div>"
        for role, key, text in cards
    )
    return f"""
<aside class="chapter-compass" aria-label="{html.escape(ui(manifest, 'compass_label'))}">
  <p class="compass-title">{html.escape(ui(manifest, 'compass_label'))}</p>
  {card_html}
  <p class="source-anchors"><span class="compass-role">{html.escape(ui(manifest, 'compass_sources'))}</span> {source_links}</p>
</aside>"""


def quick_check_html(questions: list[str], manifest: dict) -> str:
    if not questions:
        return ""
    items = "".join(f"<li>{html.escape(question)}</li>" for question in questions)
    return f"""
<section class="quick-check">
  <p class="quick-title">{html.escape(ui(manifest, 'quick_title'))}</p>
  <ol>{items}</ol>
  <p><a href="#appendix-exercises">{html.escape(ui(manifest, 'quick_link'))}</a></p>
</section>"""


_REVISION_VERSION = re.compile(r"^\d+\.\d+\.\d+$")
_REVISION_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def edition_language(manifest: dict) -> str:
    return "en" if str(manifest.get("language", "zh-CN")).lower().startswith("en") else "zh"


def resolve_book_asset(filename: str) -> Path:
    if (
        not isinstance(filename, str)
        or "/" in filename
        or "\\" in filename
        or not filename.endswith(".json")
    ):
        raise BuildError(f"invalid book asset name: {filename}")
    candidate = ROOT / filename
    if not candidate.is_file():
        raise BuildError(f"missing book asset: {filename}")
    return candidate


def validate_back_matter(manifest: dict) -> None:
    items = manifest.get("back_matter")
    if not isinstance(items, list) or not items:
        raise BuildError("manifest back_matter must list the subject index")
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            raise BuildError(f"invalid back matter entry: {item}")
        item_id = item.get("id", "")
        title = item.get("title", "")
        filename = item.get("file", "")
        if not isinstance(item_id, str) or not item_id or item_id in seen:
            raise BuildError(f"invalid back matter id: {item_id}")
        if not isinstance(title, str) or not title.strip():
            raise BuildError(f"empty back matter title: {item_id}")
        seen.add(item_id)
        resolve_book_asset(str(filename))
    if "subject-index" not in seen:
        raise BuildError("manifest back_matter is missing subject-index")


def load_revisions() -> list[dict]:
    path = ROOT / "revisions.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BuildError(f"cannot read revisions: {exc}") from exc
    entries = data.get("entries") if isinstance(data, dict) else None
    if not isinstance(entries, list) or not entries:
        raise BuildError("revisions.json has no entries")
    seen: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise BuildError(f"invalid revision entry: {entry}")
        version = entry.get("version", "")
        date = entry.get("date", "")
        if not isinstance(version, str) or not _REVISION_VERSION.fullmatch(version) or version in seen:
            raise BuildError(f"invalid revision version: {version}")
        seen.add(version)
        if not isinstance(date, str) or not _REVISION_DATE.fullmatch(date):
            raise BuildError(f"invalid revision date: {version}")
        for language in ("zh", "en"):
            notes = entry.get(language)
            if (
                not isinstance(notes, list)
                or not notes
                or not all(isinstance(note, str) and note.strip() for note in notes)
            ):
                raise BuildError(f"empty revision notes: {version}:{language}")
    return entries


def validate_revisions(manifest: dict) -> list[dict]:
    entries = load_revisions()
    if entries[0]["version"] != manifest["version"]:
        raise BuildError(
            f"revision history starts at {entries[0]['version']}, manifest is {manifest['version']}"
        )
    return entries


def imprint_html(manifest: dict, built_on: str) -> str:
    labels = ui(manifest, "license_labels")
    values = (
        manifest["version"],
        manifest["date"],
        built_on,
        manifest["author"],
        manifest["license"]["prose_and_original_images"],
        manifest["license"]["third_party_images"],
        manifest["license"]["code"],
    )
    license_rows = "".join(
        f"<dt>{html.escape(label)}</dt><dd>{html.escape(value)}</dd>"
        for label, value in zip(labels, values, strict=True)
    )
    repository = html.escape(manifest["repository"], quote=True)
    return f"""
<section class="imprint" id="imprint">
  <p class="kicker">{html.escape(ui(manifest, 'imprint_kicker'))}</p>
  <h1>{html.escape(ui(manifest, 'imprint_title'))}</h1>
  <p class="imprint-lead">{html.escape(ui(manifest, 'imprint_lead'))}</p>
  <dl>{license_rows}</dl>
  <p class="colophon">{html.escape(ui(manifest, 'repository_label'))}: <a href="{repository}">{html.escape(manifest["repository"])}</a></p>
  <p class="colophon">{html.escape(ui(manifest, 'trademark'))}</p>
</section>"""


def revision_history_html(manifest: dict) -> str:
    language = edition_language(manifest)
    items: list[str] = []
    for entry in load_revisions():
        notes = "".join(f"<li>{html.escape(note)}</li>" for note in entry[language])
        items.append(
            "<li>"
            f'<p class="revision-version"><strong>{html.escape(entry["version"])}</strong>'
            f"<span>{html.escape(entry['date'])}</span></p>"
            f"<ul>{notes}</ul></li>"
        )
    return f"""
<section class="frontmatter revision-history" id="version-history">
  <p class="kicker">{html.escape(ui(manifest, 'revision_kicker'))}</p>
  <h1>{html.escape(ui(manifest, 'revision_title'))}</h1>
  <p>{html.escape(ui(manifest, 'revision_lead'))}</p>
  <ol class="revision-list">{''.join(items)}</ol>
</section>"""


def companion_html(manifest: dict) -> str:
    repository = html.escape(manifest["repository"], quote=True)
    return f"""
<aside class="companion" id="companion">
  <h2>{html.escape(ui(manifest, 'companion_title'))}</h2>
  <p>{html.escape(ui(manifest, 'companion_body'))} <a href="{repository}">{html.escape(manifest["repository"])}</a></p>
  <p>{html.escape(ui(manifest, 'companion_note'))}</p>
</aside>"""


def source_registry_html(manifest: dict) -> str:
    cards: list[str] = []
    for source_id, source in manifest["sources"].items():
        cards.append(
            f"""
<article class="source-card" id="source-{html.escape(source_id)}">
  <p class="source-id"><code>{html.escape(source_id)}</code></p>
  <h2>{html.escape(source['title'])}</h2>
  <dl>
    <dt>{html.escape(ui(manifest, 'source_authority'))}</dt><dd>{html.escape(source['authority'])}</dd>
    <dt>{html.escape(ui(manifest, 'source_snapshot'))}</dt><dd>{html.escape(source['snapshot'])}</dd>
    <dt>{html.escape(ui(manifest, 'source_accessed'))}</dt><dd>{html.escape(source['accessed'])}</dd>
    <dt>{html.escape(ui(manifest, 'source_license'))}</dt><dd>{html.escape(source['license'])}</dd>
    <dt>{html.escape(ui(manifest, 'source_scope'))}</dt><dd>{html.escape(source['scope'])}</dd>
  </dl>
  <p class="source-link"><a href="{html.escape(source['url'], quote=True)}">{html.escape(ui(manifest, 'source_open'))}</a></p>
</article>"""
        )
    return '<section class="source-registry">' + "".join(cards) + "</section>"


def toc_html(manifest: dict) -> str:
    docs_dir, book_dir = edition_dirs(manifest)
    sections: list[str] = [
        f'<section><h2>{html.escape(ui(manifest, "front_heading"))}</h2><ol>'
        f'<li><a href="#version-history">{html.escape(ui(manifest, "revision_title"))}</a></li>'
        "</ol></section>"
    ]
    for part in manifest["parts"]:
        items: list[str] = []
        for name in part["files"]:
            title = extract_title((docs_dir / name).read_text(encoding="utf-8"), name)
            label = reader_chapter_title(manifest, name, title)
            items.append(
                f'<li><a href="#chapter-{name[:2]}">{html.escape(label)}</a></li>'
            )
        chapters = "".join(items)
        closing = part.get("closing")
        closing_html = ""
        if closing:
            closing_title = extract_title(
                (book_dir / closing["file"]).read_text(encoding="utf-8"),
                closing["file"],
            )
            closing_html = (
                f'<p class="toc-closing"><a href="#{html.escape(closing["id"])}">'
                f"{html.escape(closing_title)}</a></p>"
            )
        sections.append(
            f'<section><h2><a href="#part-{html.escape(part["id"])}">'
            f'{html.escape(part["title"])}</a></h2><p>{html.escape(part["goal"])}</p>'
            f"<ol>{chapters}</ol>{closing_html}</section>"
        )
    appendices = "".join(
        f'<li><a href="#{html.escape(item["id"])}">{html.escape(item["title"])}</a></li>'
        for item in manifest["appendices"]
    )
    heading = html.escape(ui(manifest, "appendix_heading"))
    back_items = "".join(
        f'<li><a href="#{html.escape(item["id"])}">{html.escape(item["title"])}</a></li>'
        for item in manifest["back_matter"]
    )
    back_heading = html.escape(ui(manifest, "back_matter_heading"))
    return (
        "".join(sections)
        + f"<section><h2>{heading}</h2><ol>{appendices}</ol></section>"
        + f"<section><h2>{back_heading}</h2><ol>{back_items}</ol></section>"
    )


_CSS_LIGHT_KEYS = (
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
_CSS_COLOR_KEYS = _CSS_LIGHT_KEYS[:15]
_CSS_COVER_LOCK = ("--paper", "--ink", "--muted", "--warn", "--line", "--spine")
_TOKEN_NAME = re.compile(r"^--[a-z0-9-]+$")
_FORBIDDEN_VALUE = ("\n", "\r", ";", "{", "}", "url(", "@import", "@font-face", "!important")


def _token_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    found: dict[str, object] = {}
    for key, value in pairs:
        if key in found:
            raise BuildError(f"duplicate token key {key}")
        found[key] = value
    return found


def _read_token_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise BuildError(f"missing token file: {path}") from exc


def _read_css_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise BuildError(f"missing stylesheet: {path}") from exc


def _require_keys(section: str, actual: dict, expected: tuple[str, ...]) -> None:
    actual_keys = tuple(actual)
    if actual_keys == expected:
        return
    missing = [key for key in expected if key not in actual]
    if missing:
        raise BuildError(f"token {section} missing {missing[0]}")
    extra = [key for key in actual_keys if key not in expected]
    if extra:
        raise BuildError(f"token {section} has extra {extra[0]}")
    for want, got in zip(expected, actual_keys):
        if want != got:
            raise BuildError(f"token {section} key order {got}")


def _require_value(key: str, value: object) -> None:
    if not isinstance(value, str) or not 1 <= len(value) <= 500:
        raise BuildError(f"token {key} value")
    for forbidden in _FORBIDDEN_VALUE:
        if forbidden in value:
            raise BuildError(f"token {key} contains {forbidden}")


def _section(tokens: dict, name: str) -> dict:
    value = tokens[name]
    if not isinstance(value, dict):
        raise BuildError(f"token {name} is not an object")
    for key in value:
        if not isinstance(key, str) or _TOKEN_NAME.fullmatch(key) is None:
            raise BuildError(f"token name {key}")
    return value


def _declaration_lines(pairs: list[tuple[str, str]]) -> str:
    return "\n".join(f"  {name}: {value};" for name, value in pairs)


def _declaration_inline(pairs: list[tuple[str, str]]) -> str:
    return " ".join(f"{name}: {value};" for name, value in pairs)


def load_css(tokens_path: Path = TOKENS_PATH, css_path: Path = BOOK_CSS_PATH) -> str:
    try:
        tokens = json.loads(_read_token_text(tokens_path), object_pairs_hook=_token_object)
    except BuildError:
        raise
    except json.JSONDecodeError as exc:
        raise BuildError(f"invalid token JSON: {tokens_path}: {exc.msg}") from exc
    if not isinstance(tokens, dict):
        raise BuildError(f"invalid token JSON: {tokens_path}")
    if tuple(tokens) != ("schema", "light", "dark", "print", "coverLock"):
        raise BuildError(f"token file keys {tuple(tokens)!r} in {tokens_path}")
    schema = tokens["schema"]
    if type(schema) is not int or schema != 1:
        raise BuildError(f"token schema {schema!r}")
    light = _section(tokens, "light")
    dark = _section(tokens, "dark")
    printed = _section(tokens, "print")
    _require_keys("light", light, _CSS_LIGHT_KEYS)
    _require_keys("dark", dark, _CSS_COLOR_KEYS)
    _require_keys("print", printed, _CSS_COLOR_KEYS)
    for group in (light, dark, printed):
        for key, value in group.items():
            _require_value(key, value)
    cover_lock = tokens["coverLock"]
    if cover_lock != list(_CSS_COVER_LOCK):
        raise BuildError(f"token coverLock {cover_lock!r}")
    css = _read_css_text(css_path)
    replacements = (
        ("  /* @tokens light */", _declaration_lines(list(light.items()))),
        ("  /* @tokens dark */", f"  :root {{ {_declaration_inline(list(dark.items()))} }}"),
        ("/* @tokens print */", _declaration_inline(list(printed.items()))),
        (
            "  /* @tokens cover */",
            _declaration_lines([(name, light[name]) for name in cover_lock]),
        ),
    )
    for sentinel, value in replacements:
        count = css.count(sentinel)
        if count != 1:
            raise BuildError(f"token sentinel {sentinel.strip()} count {count}")
        css = css.replace(sentinel, value, 1)
    return css


CSS = load_css()



class _AuditParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.fragments: list[str] = []
        self.images: list[str] = []
        self.chapters: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if values.get("id"):
            self.ids.add(values["id"] or "")
        href = values.get("href")
        if tag == "a" and href and href.startswith("#"):
            self.fragments.append(href[1:])
        src = values.get("src")
        if tag == "img" and src:
            self.images.append(src)
        classes = (values.get("class") or "").split()
        if tag == "article" and "chapter" in classes:
            self.chapters.append(values.get("data-chapter") or "")


def audit_html(document: str, docs_dir: Path = DOCS_DIR) -> None:
    parser = _AuditParser()
    parser.feed(document)
    expected_chapters = [name[:2] for name in source_chapters(docs_dir)]
    if parser.chapters != expected_chapters:
        raise BuildError(f"built chapter order is wrong: {parser.chapters}")
    broken = sorted({fragment for fragment in parser.fragments if fragment not in parser.ids})
    if broken:
        raise BuildError(f"broken internal fragments: {broken}")
    external_images = [src for src in parser.images if not src.startswith("data:image/")]
    if external_images:
        raise BuildError(f"non-embedded images remain: {external_images}")
    if "<video" in document.lower() or "<!-- video:" in document:
        raise BuildError("video content remains in offline book")


def cover_art_svg() -> str:
    path = ROOT / "cover.svg"
    if not path.is_file():
        raise BuildError(f"missing cover art: {path}")
    raw = path.read_text(encoding="utf-8")
    raw = re.sub(r"<\?xml[^>]*\?>", "", raw).strip()
    if "<svg" not in raw:
        raise BuildError("cover art is not an SVG")
    return raw


class _HeadingParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._tag: str | None = None
        self._buf: list[str] = []
        self._id = ""
        self.found: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"h2", "h3"}:
            self._tag = tag
            self._buf = []
            self._id = dict(attrs).get("id") or ""

    def handle_endtag(self, tag: str) -> None:
        if self._tag and tag == self._tag:
            text = " ".join("".join(self._buf).split())
            if self._id and text:
                self.found.append((self._id, text))
            self._tag = None

    def handle_data(self, data: str) -> None:
        if self._tag:
            self._buf.append(data)


def collect_headings(rendered: str) -> list[tuple[str, str]]:
    parser = _HeadingParser()
    parser.feed(rendered)
    return parser.found


def resolve_index_heading(
    container: str,
    query: str,
    headings: dict[str, list[tuple[str, str]]],
) -> str:
    hits = [(anchor, text) for anchor, text in headings.get(container, []) if query in text]
    if len(hits) != 1:
        shown = "; ".join(text for _anchor, text in hits[:6])
        raise BuildError(f"index heading {query!r} in {container} matched {len(hits)}: {shown}")
    return hits[0][0]


def index_lookup_letter(term: str) -> str:
    match = re.search(r"[A-Za-z]", term)
    if not match:
        raise BuildError(f"index term has no Latin letter: {term}")
    return match.group(0).upper()


def index_sort_token(term: str) -> str:
    match = re.search(r"[A-Za-z0-9]+", term)
    return match.group(0).casefold() if match else term.casefold()


def load_subject_index() -> list[dict]:
    data = json.loads(resolve_book_asset("subject-index.json").read_text(encoding="utf-8"))
    entries = data.get("entries") if isinstance(data, dict) else None
    if not isinstance(entries, list) or len(entries) < 60:
        raise BuildError("subject index needs at least 60 entries")
    keys = [entry.get("key") for entry in entries]
    if any(not isinstance(key, str) or not key for key in keys) or len(keys) != len(set(keys)):
        raise BuildError("subject index keys must be unique")
    for entry in entries:
        letter = entry.get("letter")
        if not isinstance(letter, str) or not re.fullmatch(r"[A-Z]", letter):
            raise BuildError(f"index letter must be A–Z: {entry.get('key')}")
        for language in ("zh", "en"):
            localized = entry.get(language)
            term = localized.get("term") if isinstance(localized, dict) else None
            refs = localized.get("refs") if isinstance(localized, dict) else None
            if not isinstance(term, str) or not term.strip() or not isinstance(refs, list) or not refs:
                raise BuildError(f"index entry is incomplete: {entry.get('key')}:{language}")
            if index_lookup_letter(term) != letter:
                raise BuildError(
                    f"index letter {letter} does not match {language} term {term!r}"
                )
    return entries


def subject_index_html(
    manifest: dict,
    headings: dict[str, list[tuple[str, str]]],
) -> str:
    language = edition_language(manifest)
    item = next(piece for piece in manifest["back_matter"] if piece["id"] == "subject-index")
    grouped: dict[str, list[str]] = {}
    order: list[str] = []
    for entry in sorted(
        load_subject_index(),
        key=lambda piece: (
            piece["letter"],
            index_sort_token(piece[language]["term"]),
            piece["key"],
        ),
    ):
        localized = entry[language]
        letter = str(entry["letter"])
        if letter not in grouped:
            grouped[letter] = []
            order.append(letter)
        for ref in localized["refs"]:
            chapter = str(ref["chapter"])
            anchor = resolve_index_heading(f"chapter-{chapter}", str(ref["heading"]), headings)
            text = f"{html.escape(str(localized['term']))} · {html.escape(str(ref['label']))}"
            grouped[letter].append(
                f'<li class="index-entry"><a href="#{html.escape(anchor)}">{text}</a></li>'
            )
    groups = "".join(
        f'<section class="index-group"><p class="index-letter">{html.escape(letter)}</p>'
        f"<ol>{''.join(grouped[letter])}</ol></section>"
        for letter in order
    )
    return f"""
<article class="back-matter subject-index" id="subject-index">
  <header><span class="chapter-number">{html.escape(ui(manifest, 'index_kicker'))}</span><h1>{html.escape(item['title'])}</h1></header>
  <p class="index-lead">{html.escape(ui(manifest, 'index_lead'))}</p>
  <div class="index-columns">{groups}</div>
  <a class="back-to-toc" href="#contents">{html.escape(ui(manifest, 'back_to_toc'))}</a>
</article>"""


def part_closing_html(part: dict, manifest: dict, chapter_anchors: dict[Path, str]) -> str:
    closing = part.get("closing")
    if not closing:
        return ""
    book_dir = edition_dirs(manifest)[1]
    path = book_dir / closing["file"]
    raw = path.read_text(encoding="utf-8")
    title = extract_title(raw, closing["file"])
    content = strip_heading_emoji(remove_chapter_frontmatter(raw))
    rendered = render_document(
        content,
        path,
        closing["id"],
        chapter_anchors,
        ui(manifest, "table_label"),
        callout_label_map(manifest),
    )
    return f"""
<article class="part-closing" id="{html.escape(closing['id'])}">
  <header><span class="chapter-number">{html.escape(ui(manifest, 'closing_kicker'))}</span><h1>{html.escape(title)}</h1><p class="closing-banner">{html.escape(ui(manifest, 'closing_banner'))}</p></header>
  {rendered}
  <a class="back-to-toc" href="#contents">{html.escape(ui(manifest, 'back_to_toc'))}</a>
</article>"""


def build_html(output_dir: Path | None = None, manifest_path: Path = MANIFEST_PATH) -> Path:
    manifest = load_manifest(manifest_path)
    validate_manifest(manifest)
    docs_dir, book_dir = edition_dirs(manifest)
    chapter_count = len(source_chapters(docs_dir))
    destination = (output_dir or DIST_DIR).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    table_label = ui(manifest, "table_label")
    labels = callout_label_map(manifest)

    chapter_anchors = {
        (docs_dir / filename).resolve(): f"chapter-{filename[:2]}"
        for part in manifest["parts"]
        for filename in part["files"]
    }

    built_on = dt.date.today().isoformat()
    routes = "".join(
        f'<div class="route"><strong>{html.escape(title)}</strong><p>{html.escape(text)}</p></div>'
        for title, text in ui(manifest, "routes")
    )
    body: list[str] = []
    body.append(
        f"""
<section class="cover" id="cover">
  <div class="cover-sheet">
    <div class="cover-art" aria-hidden="true">{cover_art_svg()}</div>
    <div class="cover-panel">
      <p class="eyebrow">{html.escape(ui(manifest, 'cover_kicker'))}</p>
      <hr class="rule">
      <h1>{html.escape(manifest['title'])}</h1>
      <p class="subtitle">{html.escape(manifest['subtitle'])}</p>
      <p class="edition"><strong>v{html.escape(manifest['version'])}</strong><span>{html.escape(manifest['date'])} · {html.escape(manifest['author'])}</span></p>
    </div>
  </div>
</section>
{imprint_html(manifest, built_on)}
{revision_history_html(manifest)}
<section class="frontmatter" id="how-to-read">
  <h1>{html.escape(ui(manifest, 'read_title'))}</h1>
  <p>{html.escape(ui(manifest, 'read_lead'))}</p>
  {companion_html(manifest)}
  <div class="routes">
    {routes}
  </div>
  <p>{html.escape(ui(manifest, 'evidence'))}</p>
</section>
<section class="contents" id="contents"><h1>{html.escape(ui(manifest, 'toc_title'))}</h1>{toc_html(manifest)}</section>"""
    )

    chapter_index = 0
    headings: dict[str, list[tuple[str, str]]] = {}
    for index, part in enumerate(manifest["parts"], start=1):
        body.append(
            f"""
<section class="part-divider" id="part-{html.escape(part['id'])}" data-part-index="{index:02d}">
  <p class="part-index" aria-hidden="true">{index:02d}</p>
  <p class="part-label">{html.escape(ui(manifest, 'part_kicker').format(n=index))}</p>
  <h1>{html.escape(part['title'])}</h1>
  <p class="part-goal">{html.escape(part['goal'])}</p>
</section>"""
        )
        for filename in part["files"]:
            path = docs_dir / filename
            raw = path.read_text(encoding="utf-8")
            title, content, questions = prepare_chapter_markdown(
                raw, filename, manifest.get("language", "zh-CN")
            )
            rendered = render_document(
                content, path, f"ch{filename[:2]}", chapter_anchors, table_label, labels
            )
            headings[f"chapter-{filename[:2]}"] = collect_headings(rendered)
            guide = manifest["chapter_guides"][filename]
            chapter_kicker = ui(manifest, "chapter_kicker").format(n=display_chapter_number(filename))
            heading = source_chapter_heading(title)
            body.append(
                f"""
<article class="chapter" id="chapter-{filename[:2]}" data-chapter="{filename[:2]}">
  <header><span class="chapter-number">{html.escape(chapter_kicker)}</span><h1>{html.escape(heading)}</h1></header>
  {compass_html(guide, manifest)}
  {rendered}
  {quick_check_html(questions, manifest)}
  <a class="back-to-toc" href="#contents">{html.escape(ui(manifest, 'back_to_toc'))}</a>
</article>"""
            )
            chapter_index += 1
        body.append(part_closing_html(part, manifest, chapter_anchors))

    for appendix in manifest["appendices"]:
        path = book_dir / appendix["file"]
        raw = path.read_text(encoding="utf-8")
        title = extract_title(raw, appendix["file"])
        content = strip_heading_emoji(remove_chapter_frontmatter(raw))
        rendered = render_document(
            content, path, appendix["id"], chapter_anchors, table_label, labels
        )
        registry = source_registry_html(manifest) if appendix["id"] == "appendix-references" else ""
        body.append(
            f"""
<article class="appendix" id="{html.escape(appendix['id'])}">
  <header><span class="chapter-number">{html.escape(ui(manifest, 'appendix_kicker'))}</span><h1>{html.escape(title)}</h1></header>
  {rendered}
  {registry}
  <a class="back-to-toc" href="#contents">{html.escape(ui(manifest, 'back_to_toc'))}</a>
</article>"""
        )

    body.append(subject_index_html(manifest, headings))

    document = f"""<!doctype html>
<html lang="{html.escape(manifest['language'])}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>{html.escape(manifest['title'])}</title>
<meta name="description" content="{html.escape(manifest['subtitle'], quote=True)}">
<style>{CSS}</style>
</head>
<body>
<a class="skip-link" href="#contents">{html.escape(ui(manifest, 'skip'))}</a>
<main class="book">{''.join(body)}</main>
<footer class="book-footer">{html.escape(ui(manifest, 'footer').format(count=chapter_count))}</footer>
<a class="toc-jump" href="#contents">{html.escape(ui(manifest, 'toc_jump'))}</a>
</body>
</html>
"""
    audit_html(document, docs_dir)
    output = destination / manifest.get("output_name", OUTPUT_NAME)
    output.write_text(document, encoding="utf-8", newline="\n")
    print(f"html  {output} ({output.stat().st_size} bytes, {chapter_index} chapters)")
    return output


def _browser_candidates(override: str | None) -> list[Path]:
    candidates: list[Path] = []
    if override:
        candidates.append(Path(override))
    for command in ("msedge", "chrome", "chromium"):
        found = shutil.which(command)
        if found:
            candidates.append(Path(found))
    for raw in (
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ):
        candidates.append(Path(raw))
    result: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.expanduser().resolve()
        if resolved not in seen and resolved.is_file():
            result.append(resolved)
            seen.add(resolved)
    return result


_CHAPTER_RUNNING_TITLE = re.compile(
    r"(?:\d{2}\s+.+|第\s*\d+\s*章(?:\s+.+)?|Chapter\s+\d+\b.*)"
)
_PART_RUNNING_TITLE = re.compile(r"第[一二三四五六七八九十0-9]+部分|Part \d+\b")


def _pdf_running_sections(document) -> list[tuple[int, str]]:
    """Return zero-based page starts whose following pages get a running header.

    Numbered chapters, the part closing, and appendices qualify. Part-divider
    titles are full pages, and front matter before the first chapter stays bare.
    Chapters may sit at outline level 2 under a part.
    """
    raw: list[tuple[int, str]] = []
    for item in document.get_toc():
        _level, title, page_number = item[0], item[1], item[2]
        if page_number < 1:
            continue
        raw.append((page_number - 1, str(title).strip()))
    first_chapter = next(
        (index for index, (_page, title) in enumerate(raw) if _CHAPTER_RUNNING_TITLE.fullmatch(title)),
        None,
    )
    sections: list[tuple[int, str]] = []
    for index, (page, title) in enumerate(raw):
        numbered = _CHAPTER_RUNNING_TITLE.fullmatch(title) is not None
        if not numbered and (first_chapter is None or index <= first_chapter):
            continue
        if _PART_RUNNING_TITLE.match(title):
            continue
        sections.append((page, title))
    return sections


def _short_running_title(title: str) -> str:
    for separator in ("：", ":"):
        if separator in title:
            return title.split(separator, 1)[0].strip()
    return title.strip()


def _fit_running_header(text: str, *, fontname: str, fontsize: float, max_width: float, fitz) -> str:
    if fitz.get_text_length(text, fontname=fontname, fontsize=fontsize) <= max_width:
        return text
    ellipsis = "..."
    trimmed = text
    while trimmed and fitz.get_text_length(trimmed + ellipsis, fontname=fontname, fontsize=fontsize) > max_width:
        trimmed = trimmed[:-1]
    return f"{trimmed}{ellipsis}" if trimmed else ellipsis


def _stamp_toc_page_references(document, fitz) -> None:
    """Right-align physical page references in the contents and the subject index."""
    mode = None
    for page in document:
        text = page.get_text()
        if "目录与分部目标" in text or "Contents and part goals" in text:
            mode = "toc"
        elif "这是书末主题索引" in text or "This is the subject index" in text:
            mode = "index"
        if mode is None:
            continue

        links = [
            link for link in page.get_links()
            if isinstance(link.get("page"), int) and link["page"] >= 1
        ]
        if not links:
            mode = None
            continue

        link_rects = [(link, fitz.Rect(link["from"])) for link in links]
        midpoint = page.rect.width / 2
        has_two_columns = (
            any(rect.x0 < midpoint for _link, rect in link_rects)
            and any(rect.x0 >= midpoint for _link, rect in link_rects)
        )
        text_spans = [
            (fitz.Rect(span["bbox"]), float(span["size"]))
            for block in page.get_text("dict")["blocks"]
            for line in block.get("lines", [])
            for span in line.get("spans", [])
            if span.get("text", "").strip()
        ]
        links_with_size = [
            (
                link,
                rect,
                max(
                    (size for span_rect, size in text_spans if span_rect.intersects(rect)),
                    default=0.0,
                ),
            )
            for link, rect in link_rects
        ]
        body_sizes = [size for _link, _rect, size in links_with_size if size > 0]
        body_size = min(body_sizes, default=0.0)
        page_right = page.rect.width - 42
        left_column_right = midpoint - 18
        for link, link_rect, font_size in links_with_size:
            destination = link.get("page", -1)
            if destination < 1:  # cover has no printed page number
                continue
            label = str(destination)
            width = fitz.get_text_length(label, fontname="helv", fontsize=8)
            is_full_width_heading = body_size > 0 and font_size > body_size * 1.2
            column_right = (
                left_column_right
                if has_two_columns
                and link_rect.x0 < midpoint
                and not is_full_width_heading
                else page_right
            )
            page.insert_text(
                fitz.Point(column_right - width, link_rect.y1 - 2),
                label,
                fontname="helv",
                fontsize=8,
                color=(0.38, 0.42, 0.45),
            )


def _stamp_page_numbers(
    raw_pdf: Path,
    output_pdf: Path,
    metadata: dict[str, str],
    manifest: dict | None = None,
) -> None:
    try:
        import fitz
    except ImportError as exc:
        raise BuildError("PyMuPDF is required for page numbers") from exc

    document = fitz.open(raw_pdf)
    try:
        document.set_metadata({**document.metadata, **metadata})
        if manifest is not None:
            document.set_toc(publication_outline(manifest, document.get_toc()))
        sections = _pdf_running_sections(document)
        section_starts = {start for start, _title in sections}
        total = max(0, document.page_count - 1)
        current_title: str | None = None
        next_section = 0
        short_title = _short_running_title(metadata.get("title") or "STM32")
        rule = (0.72, 0.74, 0.76)
        header_font = "china-s"
        header_size = 7.5

        for index in range(1, document.page_count):
            while next_section < len(sections) and sections[next_section][0] <= index:
                current_title = sections[next_section][1]
                next_section += 1

            page = document[index]
            label = f"{index} / {total}"
            width = fitz.get_text_length(label, fontname="helv", fontsize=8)
            point = fitz.Point((page.rect.width - width) / 2, page.rect.height - 8)
            page.insert_text(point, label, fontname="helv", fontsize=8, color=(0.38, 0.42, 0.45))
            page.draw_line(
                fitz.Point(42, page.rect.height - 22),
                fitz.Point(page.rect.width - 42, page.rect.height - 22),
                color=rule,
                width=0.35,
            )

            if current_title is None or index in section_starts:
                continue
            header = short_title if index % 2 == 0 else current_title
            header = _fit_running_header(
                header,
                fontname=header_font,
                fontsize=header_size,
                max_width=page.rect.width - 84,
                fitz=fitz,
            )
            header_width = fitz.get_text_length(header, fontname=header_font, fontsize=header_size)
            x = 42 if index % 2 == 0 else page.rect.width - 42 - header_width
            page.insert_text(
                fitz.Point(x, 20),
                header,
                fontname=header_font,
                fontsize=header_size,
                color=(0.38, 0.42, 0.45),
            )
            page.draw_line(
                fitz.Point(42, 27),
                fitz.Point(page.rect.width - 42, 27),
                color=rule,
                width=0.35,
            )

        _stamp_toc_page_references(document, fitz)
        document.save(output_pdf, garbage=3, deflate=True)
    finally:
        document.close()


def build_pdf(
    html_path: Path,
    browser_override: str | None = None,
    manifest_path: Path = MANIFEST_PATH,
) -> Path:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise BuildError("Playwright is required for PDF output") from exc

    browsers = _browser_candidates(browser_override)
    executable = browsers[0] if browsers else None
    if browser_override and executable is None:
        raise BuildError(f"browser does not exist: {browser_override}")

    manifest = load_manifest(manifest_path)
    output = html_path.with_name(manifest.get("pdf_name", PDF_NAME))
    raw_pdf = html_path.with_name(".stm32-book.raw.pdf")
    try:
        with sync_playwright() as playwright:
            launch_args = {"headless": True}
            if executable is not None:
                launch_args["executable_path"] = str(executable)
            browser = playwright.chromium.launch(**launch_args)
            try:
                page = browser.new_page(viewport={"width": 1280, "height": 900})
                page.goto(html_path.resolve().as_uri(), wait_until="load")
                page.evaluate("document.fonts ? document.fonts.ready : Promise.resolve()")
                page.wait_for_function(
                    "Array.from(document.images).every(img => img.complete && img.naturalWidth > 0)",
                    timeout=30_000,
                )
                page.pdf(
                    path=str(raw_pdf),
                    print_background=True,
                    prefer_css_page_size=True,
                    outline=True,
                    tagged=True,
                )
            finally:
                browser.close()
        publication_metadata = {
            "title": manifest["title"],
            "author": manifest["author"],
            "subject": manifest["subtitle"],
            "keywords": manifest["keywords"],
        }
        _stamp_page_numbers(raw_pdf, output, publication_metadata, manifest)
    except Exception as exc:
        raise BuildError(f"PDF build failed: {exc}") from exc
    finally:
        raw_pdf.unlink(missing_ok=True)
    print(f"pdf   {output} ({output.stat().st_size} bytes)")
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DIST_DIR, help="output directory")
    parser.add_argument("--pdf", action="store_true", help="also print an A4 PDF")
    parser.add_argument("--browser", help="Chrome/Edge executable for PDF output")
    parser.add_argument("--check", action="store_true", help="validate by building in a temporary directory")
    parser.add_argument("--lang", choices=("zh", "en"), default="zh", help="edition to build")
    options = parser.parse_args(argv)
    manifest_path = ROOT / ("manifest-en.json" if options.lang == "en" else "manifest.json")

    try:
        if options.check:
            with tempfile.TemporaryDirectory(prefix="stm32-book-check-") as temporary:
                build_html(Path(temporary), manifest_path)
            print(f"check whole-book HTML contract ({options.lang}): PASS")
            return 0
        html_path = build_html(options.out_dir, manifest_path)
        if options.pdf:
            build_pdf(html_path, options.browser, manifest_path)
        return 0
    except BuildError as exc:
        print(f"book build error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

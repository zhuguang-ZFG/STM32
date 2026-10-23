#!/usr/bin/env python3
"""Build the offline HTML/PDF edition of the STM32 book."""

from __future__ import annotations

import argparse
import base64
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
OUTPUT_NAME = "stm32-practical-book.html"
PDF_NAME = "stm32-practical-book.pdf"
CHAPTER_NAME = re.compile(r"^(?:0\d|1\d|2[0-8])-.+\.md$")
VIDEO_OPEN = re.compile(r"<!--\s*video:(ch\d+)\s*-->")
VIDEO_CLOSE = re.compile(r"<!--\s*/video:(ch\d+)\s*-->")
VIDEO_BLOCK = re.compile(
    r"<!--\s*video:(ch\d+)\s*-->.*?<!--\s*/video:\1\s*-->", re.DOTALL
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


def source_chapters() -> list[str]:
    return sorted(path.name for path in DOCS_DIR.glob("*.md") if CHAPTER_NAME.match(path.name))


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
    flattened = [name for part in parts for name in part.get("files", [])]
    expected = source_chapters()
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
        if not (BOOK_DIR / filename).is_file():
            raise BuildError(f"missing appendix manuscript: {filename}")

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
    return text.strip()


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

def wrap_tables(rendered: str) -> str:
    def replace_table(match: re.Match[str]) -> str:
        table = match.group(0)
        first_row = TABLE_ROW.search(table)
        columns = len(TABLE_CELL.findall(first_row.group(0))) if first_row else 0
        if columns == 0:
            raise BuildError("rendered table has no cells")
        return (
            '<div class="table-scroll" role="region" tabindex="0" '
            'aria-label="数据表，可横向滚动" '
            f'style="--table-columns: {columns}">{table}</div>'
        )

    return TABLE_BLOCK.sub(replace_table, rendered)



def render_document(
    source_text: str,
    source_file: Path,
    prefix: str,
    chapter_anchors: dict[Path, str],
) -> str:
    rendered = render_markdown(source_text)
    rendered = wrap_tables(rendered)
    rendered = rewrite_local_links(rendered, source_file, chapter_anchors)
    rendered = embed_local_images(rendered, source_file)
    return prefix_local_ids(rendered, prefix)


def compass_html(guide: dict) -> str:
    source_links = " · ".join(
        f'<a href="#source-{html.escape(source_id)}">{html.escape(source_id)}</a>'
        for source_id in guide["sources"]
    )
    return f"""
<aside class="chapter-compass" aria-label="本章罗盘">
  <h2>本章罗盘</h2>
  <div><strong>问题</strong><p>{html.escape(guide['question'])}</p></div>
  <div><strong>交付</strong><p>{html.escape(guide['deliverable'])}</p></div>
  <div><strong>边界</strong><p>{html.escape(guide['boundary'])}</p></div>
  <p class="source-anchors"><strong>来源锚点</strong> {source_links}</p>
</aside>"""


def quick_check_html(questions: list[str]) -> str:
    if not questions:
        return ""
    items = "".join(f"<li>{html.escape(question)}</li>" for question in questions)
    return f"""
<section class="quick-check">
  <h2>合上书，三问</h2>
  <ol>{items}</ol>
  <p><a href="#appendix-exercises">做完再看附录 C 的参考答案</a></p>
</section>"""


def source_registry_html(manifest: dict) -> str:
    cards: list[str] = []
    for source_id, source in manifest["sources"].items():
        cards.append(
            f"""
<article class="source-card" id="source-{html.escape(source_id)}">
  <h2>{html.escape(source['title'])}</h2>
  <dl>
    <dt>标识</dt><dd><code>{html.escape(source_id)}</code></dd>
    <dt>权威层级</dt><dd>{html.escape(source['authority'])}</dd>
    <dt>冻结点</dt><dd>{html.escape(source['snapshot'])}</dd>
    <dt>访问日期</dt><dd>{html.escape(source['accessed'])}</dd>
    <dt>许可边界</dt><dd>{html.escape(source['license'])}</dd>
    <dt>适用范围</dt><dd>{html.escape(source['scope'])}</dd>
  </dl>
  <p><a href="{html.escape(source['url'], quote=True)}">打开来源</a></p>
</article>"""
        )
    return '<section class="source-registry">' + "".join(cards) + "</section>"


def toc_html(manifest: dict) -> str:
    sections: list[str] = []
    for part in manifest["parts"]:
        chapters = "".join(
            f'<li><a href="#chapter-{name[:2]}">{html.escape(name[:-3])}</a></li>'
            for name in part["files"]
        )
        sections.append(
            f'<section><h2><a href="#part-{html.escape(part["id"])}">'
            f'{html.escape(part["title"])}</a></h2><p>{html.escape(part["goal"])}</p>'
            f"<ol>{chapters}</ol></section>"
        )
    appendices = "".join(
        f'<li><a href="#{html.escape(item["id"])}">{html.escape(item["title"])}</a></li>'
        for item in manifest["appendices"]
    )
    return "".join(sections) + f"<section><h2>附录</h2><ol>{appendices}</ol></section>"


CSS = r"""
:root {
  color-scheme: light dark;
  --paper: #fbfaf7;
  --ink: #17202a;
  --muted: #5e6872;
  --line: #d7dce1;
  --panel: #f1f5f7;
  --accent: #075e84;
  --accent-soft: #e5f3f8;
  --code: #101820;
  --code-ink: #eef6f8;
  font-family: "Noto Sans CJK SC", "Microsoft YaHei", "PingFang SC", system-ui, sans-serif;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body { margin: 0; background: var(--paper); color: var(--ink); line-height: 1.78; }
a { color: var(--accent); text-underline-offset: .18em; }
a:focus-visible { outline: 3px solid var(--accent); outline-offset: 3px; }
.skip-link { position: fixed; left: 1rem; top: -5rem; z-index: 20; padding: .6rem 1rem; background: var(--ink); color: var(--paper); }
.skip-link:focus { top: 1rem; }
.book { width: min(100% - 2rem, 980px); margin: 0 auto; }
.cover { min-height: 92vh; display: grid; align-content: center; padding: 5rem 7%; border-bottom: 4px solid var(--accent); }
.cover .eyebrow { font-weight: 700; letter-spacing: .16em; color: var(--accent); }
.cover h1 { font-size: clamp(2.6rem, 8vw, 5.8rem); line-height: 1.06; margin: .25em 0; max-width: 12ch; }
.cover .subtitle { font-size: clamp(1.15rem, 3vw, 1.7rem); max-width: 30em; }
.cover .edition { color: var(--muted); margin-top: 3rem; }
.frontmatter, .contents { padding: 4rem 6%; }
.frontmatter { border-bottom: 1px solid var(--line); }
.frontmatter .routes { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1rem; }
.route { border: 1px solid var(--line); border-radius: .8rem; padding: 1rem 1.2rem; background: var(--panel); }
.contents > section { border-top: 1px solid var(--line); padding: 1.2rem 0; }
.contents ol { columns: 2; column-gap: 3rem; }
.contents li { break-inside: avoid; margin: .28rem 0; }
.part-divider { min-height: 45vh; display: grid; align-content: center; padding: 5rem 7%; margin-top: 3rem; border-top: 4px solid var(--accent); border-bottom: 1px solid var(--line); }
.part-divider .part-label { color: var(--accent); font-weight: 800; letter-spacing: .12em; }
.part-divider h1 { font-size: clamp(2rem, 5vw, 3.7rem); line-height: 1.15; }
.chapter, .appendix { padding: 4rem 6%; border-bottom: 1px solid var(--line); }
.chapter > header, .appendix > header { margin-bottom: 2.2rem; }
.chapter > header h1, .appendix > header h1 { font-size: clamp(2rem, 5vw, 3.2rem); line-height: 1.15; margin: .2em 0; }
.chapter-number { color: var(--accent); font-weight: 800; letter-spacing: .12em; }
h2, h3, h4 { line-height: 1.35; scroll-margin-top: 1.5rem; }
h2 { margin-top: 2.4rem; }
h3 { margin-top: 1.8rem; }
.chapter-compass { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: .8rem; margin: 1.8rem 0 3rem; padding: 1rem; background: var(--accent-soft); border-left: 5px solid var(--accent); border-radius: .6rem; }
.chapter-compass h2, .chapter-compass .source-anchors { grid-column: 1 / -1; margin: 0; }
.chapter-compass div { background: color-mix(in srgb, var(--paper) 72%, transparent); padding: .8rem; border-radius: .45rem; }
.chapter-compass div p { margin: .35rem 0 0; }
.chapter-compass strong { color: var(--accent); }
.quick-check { margin: 3rem 0 1rem; padding: 1rem 1.4rem; border: 1px solid var(--line); border-radius: .7rem; background: var(--panel); }
.quick-check h2 { margin-top: 0; }
blockquote { margin: 1.4rem 0; padding: .25rem 1.2rem; border-left: 4px solid var(--accent); color: var(--muted); }
img { display: block; max-width: 100%; height: auto; margin: 1.2rem auto .4rem; }
sub { display: block; color: var(--muted); text-align: center; font-size: .88rem; }
table { width: 100%; border-collapse: collapse; font-size: .94rem; }
.table-scroll { max-width: 100%; overflow-x: auto; margin: 1.25rem 0 2rem; overscroll-behavior-inline: contain; }
.table-scroll:focus-visible { outline: 3px solid var(--accent); outline-offset: 3px; }
.table-scroll table { margin: 0; }
th, td { border: 1px solid var(--line); padding: .55rem .65rem; vertical-align: top; text-align: left; }
th { background: var(--panel); }
code { font-family: "Cascadia Mono", "SFMono-Regular", Consolas, monospace; font-size: .91em; }
:not(pre) > code { padding: .12em .35em; border-radius: .3em; background: var(--panel); }
pre { overflow-x: auto; padding: 1rem 1.15rem; background: var(--code); color: var(--code-ink); border-radius: .65rem; line-height: 1.55; }
pre code { font-size: .86rem; }
dl { display: grid; grid-template-columns: 8rem 1fr; gap: .35rem 1rem; }
dt { font-weight: 700; }
dd { margin: 0; }
p, li, dd { overflow-wrap: anywhere; }
.source-registry { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1rem; margin-top: 2rem; }
.source-card { min-width: 0; overflow-wrap: anywhere; border: 1px solid var(--line); border-radius: .7rem; padding: 1rem 1.2rem; break-inside: avoid; }
.source-card h2 { min-width: 0; font-size: 1.15rem; margin-top: 0; }
.source-card dl { min-width: 0; grid-template-columns: 5rem minmax(0, 1fr); font-size: .9rem; }
.back-to-toc { display: inline-block; margin-top: 2rem; }
footer.book-footer { padding: 3rem 6%; color: var(--muted); text-align: center; }
@media (max-width: 720px) {
  .book { width: min(100% - 1rem, 980px); }
  .cover, .frontmatter, .contents, .part-divider, .chapter, .appendix { padding-left: 1rem; padding-right: 1rem; }
  .frontmatter .routes, .chapter-compass, .source-registry { grid-template-columns: minmax(0, 1fr); }
  .chapter-compass h2, .chapter-compass .source-anchors { grid-column: 1; }
  .contents ol { columns: 1; }
  .table-scroll table { display: table; min-width: max(100%, calc(var(--table-columns) * 8rem)); white-space: normal; }
  dl { grid-template-columns: 1fr; }
}
@media (prefers-color-scheme: dark) {
  :root { --paper: #11171b; --ink: #e9eef1; --muted: #acb7bf; --line: #3a454d; --panel: #1c252b; --accent: #78c8e8; --accent-soft: #17313c; --code: #080c0f; --code-ink: #edf6f9; }
}
@media (prefers-reduced-motion: reduce) {
  html { scroll-behavior: auto; }
}
@media print {
  :root { color-scheme: light; --paper: #fff; --ink: #111; --muted: #444; --line: #bbb; --panel: #f4f4f4; --accent: #075e84; --accent-soft: #edf6f9; }
  @page { size: A4; margin: 16mm 15mm 18mm; }
  body { font-size: 9.5pt; line-height: 1.55; orphans: 3; widows: 3; print-color-adjust: exact; -webkit-print-color-adjust: exact; }
  .book { width: auto; max-width: none; }
  .cover { min-height: 245mm; page-break-after: always; }
  .frontmatter, .contents, .part-divider, .chapter, .appendix { padding: 0; }
  .frontmatter, .contents, .part-divider, .chapter, .appendix { page-break-before: always; }
  .part-divider { min-height: 220mm; }
  h1, h2, h3, h4 { break-after: avoid-page; page-break-after: avoid; }
  p[align="center"], figure, .chapter-compass, .quick-check, blockquote, .source-card, img { break-inside: avoid-page; page-break-inside: avoid; }
  .table-scroll { overflow: visible; }
  .table-scroll table { min-width: 0; }
  thead { display: table-header-group; }
  tr { break-inside: avoid-page; page-break-inside: avoid; }
  pre { white-space: pre-wrap; overflow-wrap: anywhere; break-inside: avoid-page; page-break-inside: avoid; }
  .source-registry { grid-template-columns: 1fr; }
  a { color: inherit; text-decoration: none; }
  .back-to-toc, .skip-link { display: none; }
}
"""


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


def audit_html(document: str) -> None:
    parser = _AuditParser()
    parser.feed(document)
    expected_chapters = [name[:2] for name in source_chapters()]
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


def build_html(output_dir: Path | None = None, manifest_path: Path = MANIFEST_PATH) -> Path:
    manifest = load_manifest(manifest_path)
    validate_manifest(manifest)
    chapter_count = len(source_chapters())
    destination = (output_dir or DIST_DIR).resolve()
    destination.mkdir(parents=True, exist_ok=True)

    chapter_anchors = {
        (DOCS_DIR / filename).resolve(): f"chapter-{filename[:2]}"
        for part in manifest["parts"]
        for filename in part["files"]
    }

    body: list[str] = []
    body.append(
        f"""
<section class="cover" id="cover">
  <p class="eyebrow">STM32 · OFFLINE BOOK</p>
  <h1>{html.escape(manifest['title'])}</h1>
  <p class="subtitle">{html.escape(manifest['subtitle'])}</p>
  <p class="edition">v{html.escape(manifest['version'])} · {html.escape(manifest['date'])}<br>
  {html.escape(manifest['author'])}<br>
  原创正文/图片 {html.escape(manifest['license']['prose_and_original_images'])} · 第三方实拍 {html.escape(manifest['license']['third_party_images'])} · 代码 {html.escape(manifest['license']['code'])}</p>
</section>
<section class="frontmatter" id="how-to-read">
  <h1>这不是文章合集</h1>
  <p>全书沿“开发闭环 → 引脚与时间 → 数据搬运 → 系统可靠性 → 项目交付 → 跨系列迁移”推进。每章先用罗盘约定问题、交付和边界，再进入原章节；章末三问把结论拉回可检查的工程状态。</p>
  <div class="routes">
    <div class="route"><strong>第一次上手</strong><p>00–05 → 06/07/08 任一通信章 → 17 排错。</p></div>
    <div class="route"><strong>做数据采集</strong><p>02 → 05 → 09 → 10 → 06/14 → 15。</p></div>
    <div class="route"><strong>做可升级设备</strong><p>11 → 12 → 17 → 附录 A/B，补齐失败路径。</p></div>
    <div class="route"><strong>迁移到新系列</strong><p>20/21 → 23/24/25；每次重新核对电源、复用、时钟、内存。</p></div>
  </div>
  <p><strong>证据口径：</strong>手册参数写文档号/修订点；GitHub 实现冻结 tag/commit；社区内容只作线索；“能跑”必须附期望、实际、测量条件和未覆盖边界。</p>
</section>
<section class="contents" id="contents"><h1>目录与分部目标</h1>{toc_html(manifest)}</section>"""
    )

    chapter_index = 0
    for part in manifest["parts"]:
        body.append(
            f"""
<section class="part-divider" id="part-{html.escape(part['id'])}">
  <p class="part-label">PART {html.escape(part['id'][1:])}</p>
  <h1>{html.escape(part['title'])}</h1>
  <p>{html.escape(part['goal'])}</p>
</section>"""
        )
        for filename in part["files"]:
            path = DOCS_DIR / filename
            raw = path.read_text(encoding="utf-8")
            title = extract_title(raw, filename)
            questions = extract_quick_questions(raw)
            stripped = strip_video_blocks(raw, filename)
            content = remove_chapter_frontmatter(stripped)
            rendered = render_document(content, path, f"ch{filename[:2]}", chapter_anchors)
            guide = manifest["chapter_guides"][filename]
            body.append(
                f"""
<article class="chapter" id="chapter-{filename[:2]}" data-chapter="{filename[:2]}">
  <header><span class="chapter-number">CHAPTER {filename[:2]}</span><h1>{html.escape(title)}</h1></header>
  {compass_html(guide)}
  {rendered}
  {quick_check_html(questions)}
  <a class="back-to-toc" href="#contents">返回目录 ↑</a>
</article>"""
            )
            chapter_index += 1

    for appendix in manifest["appendices"]:
        path = BOOK_DIR / appendix["file"]
        raw = path.read_text(encoding="utf-8")
        title = extract_title(raw, appendix["file"])
        content = remove_chapter_frontmatter(raw)
        rendered = render_document(content, path, appendix["id"], chapter_anchors)
        registry = source_registry_html(manifest) if appendix["id"] == "appendix-references" else ""
        body.append(
            f"""
<article class="appendix" id="{html.escape(appendix['id'])}">
  <header><span class="chapter-number">APPENDIX</span><h1>{html.escape(title)}</h1></header>
  {rendered}
  {registry}
  <a class="back-to-toc" href="#contents">返回目录 ↑</a>
</article>"""
        )

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
<a class="skip-link" href="#contents">跳到目录</a>
<main class="book">{''.join(body)}</main>
<footer class="book-footer">本书由 <code>stm32-book/build_html.py</code> 从 {chapter_count} 章源文档构建；来源、冻结点与许可见附录 E。</footer>
</body>
</html>
"""
    audit_html(document)
    output = destination / OUTPUT_NAME
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


def _pdf_running_sections(document) -> list[tuple[int, str]]:
    """Return zero-based PDF page starts for chapters and appendices."""
    sections: list[tuple[int, str]] = []
    for level, title, page_number in document.get_toc():
        if level != 1 or page_number < 1:
            continue
        if re.fullmatch(r"\d{2}\s+.+", title) or title.startswith("附录 "):
            sections.append((page_number - 1, title))
    return sections


def _stamp_toc_page_references(document, fitz) -> None:
    """Right-align physical page references in each rendered TOC column."""
    in_contents = False
    for page in document:
        text = page.get_text()
        if "目录与分部目标" in text:
            in_contents = True
        if not in_contents:
            continue

        links = [
            link for link in page.get_links()
            if isinstance(link.get("page"), int) and link["page"] >= 1
        ]
        if not links:
            in_contents = False
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


def _stamp_page_numbers(raw_pdf: Path, output_pdf: Path, metadata: dict[str, str]) -> None:
    try:
        import fitz
    except ImportError as exc:
        raise BuildError("PyMuPDF is required for page numbers") from exc

    document = fitz.open(raw_pdf)
    try:
        document.set_metadata({**document.metadata, **metadata})
        sections = _pdf_running_sections(document)
        section_starts = {start for start, _title in sections}
        total = max(0, document.page_count - 1)
        current_title: str | None = None
        next_section = 0
        short_title = metadata.get("title", "STM32 实战").split("：", 1)[0]

        for index in range(1, document.page_count):
            while next_section < len(sections) and sections[next_section][0] <= index:
                current_title = sections[next_section][1]
                next_section += 1

            page = document[index]
            label = f"{index} / {total}"
            width = fitz.get_text_length(label, fontname="helv", fontsize=8)
            point = fitz.Point((page.rect.width - width) / 2, page.rect.height - 8)
            page.insert_text(point, label, fontname="helv", fontsize=8, color=(0.38, 0.42, 0.45))

            if current_title is None or index in section_starts:
                continue
            header = short_title if index % 2 == 0 else current_title
            header_width = fitz.get_text_length(header, fontname="china-s", fontsize=7.5)
            x = 42 if index % 2 == 0 else page.rect.width - 42 - header_width
            page.insert_text(
                fitz.Point(x, 20),
                header,
                fontname="china-s",
                fontsize=7.5,
                color=(0.38, 0.42, 0.45),
            )
            page.draw_line(
                fitz.Point(42, 27),
                fitz.Point(page.rect.width - 42, 27),
                color=(0.72, 0.74, 0.76),
                width=0.35,
            )

        _stamp_toc_page_references(document, fitz)
        document.save(output_pdf, garbage=3, deflate=True)
    finally:
        document.close()


def build_pdf(html_path: Path, browser_override: str | None = None) -> Path:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise BuildError("Playwright is required for PDF output") from exc

    browsers = _browser_candidates(browser_override)
    executable = browsers[0] if browsers else None
    if browser_override and executable is None:
        raise BuildError(f"browser does not exist: {browser_override}")

    output = html_path.with_name(PDF_NAME)
    raw_pdf = html_path.with_name(".stm32-book.raw.pdf")
    manifest = load_manifest()
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
        _stamp_page_numbers(raw_pdf, output, publication_metadata)
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
    options = parser.parse_args(argv)

    try:
        if options.check:
            with tempfile.TemporaryDirectory(prefix="stm32-book-check-") as temporary:
                build_html(Path(temporary))
            print("check whole-book HTML contract: PASS")
            return 0
        html_path = build_html(options.out_dir)
        if options.pdf:
            build_pdf(html_path, options.browser)
        return 0
    except BuildError as exc:
        print(f"book build error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

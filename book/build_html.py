"""Build the merged book as a temporary static site."""

from __future__ import annotations

import argparse
import html as html_lib
import json
import posixpath
import re
import shutil
import struct
import sys
import tempfile
from pathlib import Path

import markdown

from book import manifest as manifest_module
from book.checks import cjk_slugify
from book.contracts import split_frontmatter

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
QUIZ_DIR = DOCS / ".vitepress" / "data" / "quizzes"
DEFAULT_OUT = ROOT / "book" / "dist" / "site"

QUIZ_RE = re.compile(r'<QuizBank\s+chapter="([^"]+)"\s*/>')
MD_HREF_RE = re.compile(r'href="([^"]*?)\.md(#[^"]*)?"')
ROOT_SRC_RE = re.compile(r'(src|href)="(/[^"]*)"')
STYLE = """
:root {
  --ink: #26221b;
  --muted: #6e6b60;
  --rule: #d8d2c0;
  --accent: #1f4680;
  --code-bg: #f4eee0;
  --paper: #ffffff;
  --serif: "Source Han Serif SC", "Noto Serif CJK SC", "Songti SC",
           "STSong", "SimSun", serif;
  --sans: "Source Han Sans SC", "Noto Sans CJK SC", "Microsoft YaHei",
          "PingFang SC", system-ui, sans-serif;
  --mono: "Cascadia Mono", "JetBrains Mono", "Sarasa Mono SC",
          Consolas, "Courier New", monospace;
}
html { font-size: 17px; }
body {
  max-width: 46rem; margin: 0 auto; padding: 2.4rem 1.2rem 5rem;
  font-family: var(--serif);
  background: var(--paper);
  line-height: 1.82; color: var(--ink); text-align: justify;
  text-justify: inter-ideograph; overflow-wrap: break-word;
}
nav.book-nav, .chapter-pager, .back-to-top, figcaption, table,
h1, h2, h3, h4 { font-family: var(--sans); }
pre, code { font-family: var(--mono); }
::selection { background: #d7e3f4; }
nav.book-nav {
  border-bottom: 1px solid var(--rule); margin-bottom: 2.2rem;
  padding-bottom: 0.9rem; font-size: 0.86rem; line-height: 1.6; text-align: left;
}
nav.book-nav summary { cursor: pointer; font-weight: 600; color: var(--accent); list-style: none; }
nav.book-nav summary::marker { content: ""; }
nav.book-nav summary::before { content: "▸ "; }
nav.book-nav[open] summary::before { content: "▾ "; }
nav.book-nav ol { display: flex; flex-wrap: wrap; gap: 0.3rem 1rem; list-style: none; padding: 0; margin: 0.6rem 0 0; }
nav.book-nav a[aria-current="page"] { font-weight: 700; text-decoration: none; }
a { color: var(--accent); text-underline-offset: 3px; }
a:hover { text-decoration-thickness: 2px; }
h1, h2, h3, h4 { line-height: 1.35; text-align: left; text-wrap: balance; }
h1 { font-size: 2rem; margin: 0 0 1rem; letter-spacing: 0.01em; }
h2 { font-size: 1.5rem; margin: 2.2em 0 0.7em; padding-bottom: 0.28em; border-bottom: 1px solid var(--rule); }
h3 { font-size: 1.18rem; margin: 1.7em 0 0.5em; }
p { margin: 0.7em 0; }
p + p { text-indent: 2em; }
p[align="center"] + p { text-indent: 0; }
li > p, blockquote p, figure p { text-indent: 0; }
ul, ol { padding-left: 1.55em; }
li { margin: 0.25em 0; }
blockquote {
  margin: 1.4em 0; padding: 0.65em 1.1em; color: #4a4234;
  background: #faf4e4; border-left: 3px solid var(--rule);
}
hr { border: 0; border-top: 1px solid var(--rule); margin: 2rem 0; }
pre {
  background: var(--code-bg); border: 1px solid var(--rule); border-radius: 4px;
  padding: 0.8rem 0.95rem; overflow-x: auto; line-height: 1.55; text-align: left;
  font-size: 0.86rem; overflow-wrap: normal;
}
code { background: var(--code-bg); padding: 0.08rem 0.28rem; border-radius: 3px; font-size: 0.9em; }
:not(pre) > code { overflow-wrap: anywhere; }
pre code { background: transparent; padding: 0; font-size: inherit; }
table {
  width: 100%; border-collapse: collapse; margin: 1.4em 0;
  font-size: 0.9rem; line-height: 1.55; text-align: left;
}
.table-scroll { max-width: 100%; overflow-x: auto; margin: 1.4em 0; }
.table-scroll table { margin: 0; }
th, td { border: 1px solid var(--rule); padding: 0.45rem 0.65rem; vertical-align: top; overflow-wrap: break-word; }
thead th { background: #f3ecdc; font-weight: 600; }
tbody tr:nth-child(even) { background: #fbf7ec; }
@media (min-width: 900px) {
  th, td { overflow-wrap: anywhere; }
}
figure.book-figure { margin: 1.9em 0; text-align: center; }
img { max-width: 100%; height: auto; }
a.figure-zoom { display: block; cursor: zoom-in; }
figure.book-figure img {
  display: block; margin: 0 auto; max-width: 100%; height: auto;
  border-radius: 4px;
}
figure.book-figure figcaption {
  max-width: 36em; margin: 0.65em auto 0; color: var(--muted);
  font-size: 0.88rem; line-height: 1.6; text-align: center;
}
.quiz { border: 1px solid var(--rule); border-radius: 6px; padding: 1rem 1.15rem; margin: 1.8rem 0; }
.quiz-q { margin-top: 0.8em; }
.quiz-options { margin: 0.35em 0 0.7em; }
@media (max-width: 700px) {
  html { font-size: 16px; }
  body { padding: 1.4rem 1rem 3.5rem; }
  h1 { font-size: 1.7rem; }
  h2 { font-size: 1.35rem; }
  table { font-size: 0.84rem; }
  th, td { padding: 0.35rem 0.45rem; }
}
nav.chapter-pager {
  display: grid; grid-template-columns: 1fr 1fr; gap: 0.8rem;
  margin: 3rem 0 0; padding-top: 1.4rem;
  border-top: 1px solid var(--rule); text-align: left; line-height: 1.5;
}
nav.chapter-pager a {
  display: block; padding: 0.7rem 0.9rem; border: 1px solid var(--rule);
  border-radius: 6px; text-decoration: none;
}
nav.chapter-pager a:hover { border-color: var(--accent); text-decoration: none; }
nav.chapter-pager .pager-dir { display: block; font-size: 0.78rem; color: var(--muted); }
nav.chapter-pager .pager-title { display: block; margin-top: 0.2rem; font-weight: 600; }
a.pager-next { grid-column: 2; text-align: right; }
a.pager-prev { grid-column: 1; }
nav.chapter-pager a:focus-visible, .back-to-top:focus-visible, a:focus-visible {
  outline: 2px solid var(--accent); outline-offset: 2px;
}
.back-to-top {
  position: fixed; right: 1.2rem; bottom: 1.4rem;
  width: 2.6rem; height: 2.6rem; border-radius: 50%;
  border: 1px solid var(--rule); background: var(--paper); color: var(--accent);
  font-size: 1.2rem; line-height: 1; cursor: pointer; opacity: 0.92;
  box-shadow: 0 1px 4px rgb(0 0 0 / 0.12);
}
.back-to-top:hover { border-color: var(--accent); }
p.book-subtitle { font-size: 1.05rem; color: var(--muted); margin: -0.4em 0 1.6em; }
p.book-version { font-size: 0.82rem; color: var(--muted); margin: 0 0 2rem; }
@media (prefers-color-scheme: dark) {
  :root {
    --ink: #e6e1d3;
    --muted: #a39d8d;
    --rule: #4a453a;
    --accent: #8fb0e6;
    --code-bg: #2a2620;
    --paper: #1b1813;
  }
  body { background: var(--paper); }
  ::selection { background: #33415c; }
  blockquote { background: #25211a; color: #cfc8b6; }
  thead th { background: #2a2620; }
  tbody tr:nth-child(even) { background: #211d17; }
  figure.book-figure img { border-radius: 4px; }
  .back-to-top { box-shadow: 0 1px 4px rgb(0 0 0 / 0.5); }
}
"""
PAGE_SCRIPT = """<script>
window.addEventListener('beforeprint', () => {
  document.querySelectorAll('details').forEach((item) => { item.open = true; });
});
const topButton = document.createElement('button');
topButton.type = 'button';
topButton.className = 'back-to-top';
topButton.setAttribute('aria-label', '回到顶部');
topButton.textContent = '\\u2191';
topButton.hidden = true;
document.body.appendChild(topButton);
const syncTopButton = () => { topButton.hidden = window.scrollY < 600; };
window.addEventListener('scroll', syncTopButton, { passive: true });
topButton.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
syncTopButton();
</script>"""


def quiz_html(quiz_id: str, quiz_dir: Path) -> str:
    data = json.loads((quiz_dir / f"{quiz_id}.json").read_text(encoding="utf-8"))
    parts = [f'<section class="quiz"><h3>{html_lib.escape(data["title"])}</h3>']
    for index, item in enumerate(data["questions"], 1):
        parts.append(f'<p class="quiz-q"><strong>Q{index}.</strong> {html_lib.escape(item["q"])}</p>')
        parts.append('<ol class="quiz-options">')
        parts.extend(f"<li>{html_lib.escape(option)}</li>" for option in item["options"])
        parts.append("</ol>")
        parts.append(
            '<details class="quiz-answer"><summary>答案与解析</summary>'
            f'<p>{html_lib.escape(item["a"])}</p></details>'
        )
    parts.append("</section>")
    return "\n".join(parts)


def render_markdown(text: str, quiz_dir: Path) -> str:
    text = QUIZ_RE.sub(lambda match: quiz_html(match.group(1), quiz_dir), text)
    return markdown.Markdown(
        extensions=["extra", "sane_lists", "toc"],
        extension_configs={"toc": {"slugify": cjk_slugify, "permalink": False}},
    ).convert(text)


def relativize(html_text: str, depth: int) -> str:
    prefix = "../" * depth
    return ROOT_SRC_RE.sub(
        lambda match: f'{match.group(1)}="{prefix}{match.group(2).lstrip("/")}"', html_text
    )


FIGURE_P_RE = re.compile(r'<p>\s*<img\s+([^>]*?)\s*/?>\s*</p>')
ALT_RE = re.compile(r'\balt="([^"]*)"')
SRC_RE = re.compile(r'\bsrc="([^"]*)"')
IMG_TAG_RE = re.compile(r'<img\b([^>]*?)(\s*/?)>', re.I)
TABLE_RE = re.compile(r'<table>.*?</table>', re.S)


def wrap_tables(html_text: str) -> str:
    """Keep wide register tables inside a scroll container on small screens."""
    return TABLE_RE.sub(
        lambda match: f'<div class="table-scroll">{match.group(0)}</div>',
        html_text,
    )


def _svg_size(text: str) -> tuple[int, int] | None:
    root = re.search(r'<svg\b([^>]*)>', text, re.I | re.S)
    if root is None:
        return None
    attrs = root.group(1)
    numeric = {}
    for key in ("width", "height"):
        match = re.search(rf'\b{key}="([0-9.]+)(?:px)?"', attrs, re.I)
        if match:
            numeric[key] = float(match.group(1))
    if "width" in numeric and "height" in numeric:
        return round(numeric["width"]), round(numeric["height"])
    viewbox = re.search(r'\bviewBox="([^"]+)"', attrs, re.I)
    if viewbox:
        parts = re.split(r'[\s,]+', viewbox.group(1).strip())
        if len(parts) == 4:
            try:
                return round(float(parts[2])), round(float(parts[3]))
            except ValueError:
                pass
    return None


def _jpeg_size(data: bytes) -> tuple[int, int] | None:
    if data[:2] != b"\xff\xd8":
        return None
    offset = 2
    sof = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}
    while offset + 4 <= len(data):
        if data[offset] != 0xFF:
            offset += 1
            continue
        while offset < len(data) and data[offset] == 0xFF:
            offset += 1
        if offset >= len(data):
            return None
        marker = data[offset]
        offset += 1
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            continue
        if offset + 2 > len(data):
            return None
        length = int.from_bytes(data[offset : offset + 2], "big")
        if length < 2:
            return None
        if marker in sof and offset + 7 <= len(data):
            height = int.from_bytes(data[offset + 3 : offset + 5], "big")
            width = int.from_bytes(data[offset + 5 : offset + 7], "big")
            return (width, height) if width and height else None
        offset += length
    return None


def _image_size(path: Path) -> tuple[int, int] | None:
    suffix = path.suffix.lower()
    if suffix == ".svg":
        return _svg_size(path.read_text(encoding="utf-8", errors="ignore"))
    data = path.read_bytes()
    if suffix == ".png" and data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
        return struct.unpack(">II", data[16:24])
    if suffix == ".gif" and data[:3] == b"GIF" and len(data) >= 10:
        return struct.unpack("<HH", data[6:10])
    if suffix in {".jpg", ".jpeg"}:
        return _jpeg_size(data)
    return None


def add_image_dimensions(html_text: str, public_dir: Path) -> str:
    """Reserve layout space for lazy images before they load."""

    def repl(match: re.Match[str]) -> str:
        attrs = match.group(1)
        tail = match.group(2)
        src = SRC_RE.search(attrs)
        if src is None or not src.group(1).startswith("/"):
            return match.group(0)
        asset = public_dir / src.group(1).lstrip("/")
        if not asset.is_file():
            return match.group(0)
        size = _image_size(asset)
        if size is None:
            return match.group(0)
        width, height = size
        width_attr = re.search(r'\bwidth="([0-9.]+)(?:px)?"', attrs, re.I)
        height_attr = re.search(r'\bheight="([0-9.]+)(?:px)?"', attrs, re.I)
        additions = []
        if width_attr and height_attr:
            return match.group(0)
        if width_attr:
            scaled = round(float(width_attr.group(1)) * height / width)
            additions.append(f'height="{scaled}"')
        elif height_attr:
            scaled = round(float(height_attr.group(1)) * width / height)
            additions.append(f'width="{scaled}"')
        else:
            additions.extend((f'width="{width}"', f'height="{height}"'))
        return f'<img{attrs.rstrip()} {" ".join(additions)}{tail}>'

    return IMG_TAG_RE.sub(repl, html_text)


def wrap_figures(html_text: str, lazy: bool = False, zoom: bool = False) -> str:
    """Turn a standalone Markdown image into a captioned figure.

    Markdown keeps the author's alt text in the HTML but browsers never show
    it. Lifting it into a <figcaption> gives every plate a visible caption and
    a stable block for print/page-break rules.
    """
    def repl(match: re.Match[str]) -> str:
        attrs = match.group(1).strip()
        alt = ALT_RE.search(attrs)
        if alt is None or not alt.group(1).strip():
            return match.group(0)
        if lazy and "loading=" not in attrs:
            attrs += ' loading="lazy"'
        image = f'<img {attrs}>'
        src = SRC_RE.search(attrs)
        if zoom and src:
            image = (
                f'<a class="figure-zoom" href="{src.group(1)}" '
                f'target="_blank" rel="noopener">{image}</a>'
            )
        return (
            f'<figure class="book-figure">{image}'
            f'<figcaption>{alt.group(1)}</figcaption></figure>'
        )

    return FIGURE_P_RE.sub(repl, html_text)


def nav_html(items: list[tuple[str, str, str]], current_path: str) -> str:
    current_dir = posixpath.dirname(current_path)
    links = []
    for _, title, path in items:
        href = posixpath.relpath(path, current_dir or ".")
        current = ' aria-current="page"' if path == current_path else ""
        links.append(
            f'<li><a href="{href}"{current}>{html_lib.escape(title)}</a></li>'
        )
    return (
        '<details class="book-toc">'
        f'<summary>全书目录 · {len(links)} 章</summary>'
        "<ol>" + "".join(links) + "</ol></details>"
    )


def _pager_link(current_dir: str, direction: str, entry: tuple[str, str, str]) -> str:
    _, title, path = entry
    href = posixpath.relpath(path, current_dir or ".")
    label = "上一章" if direction == "prev" else "下一章"
    rel = ' rel="prev"' if direction == "prev" else ' rel="next"'
    side = "pager-prev" if direction == "prev" else "pager-next"
    return (
        f'<a class="{side}" href="{href}"{rel}>'
        f'<span class="pager-dir">{label}</span>'
        f'<span class="pager-title">{html_lib.escape(title)}</span></a>'
    )


def chapter_pager_html(items: list[tuple[str, str, str]], current_path: str) -> str:
    paths = [path for _, _, path in items]
    if current_path not in paths:
        return ""
    index = paths.index(current_path)
    current_dir = posixpath.dirname(current_path)
    links = []
    if index > 0:
        links.append(_pager_link(current_dir, "prev", items[index - 1]))
    if index + 1 < len(items):
        links.append(_pager_link(current_dir, "next", items[index + 1]))
    if not links:
        return ""
    return f'<nav class="chapter-pager" aria-label="章节导航">{"".join(links)}</nav>'


def page_shell(title: str, body: str, nav: str, pager: str = "") -> str:
    return (
        "<!DOCTYPE html>\n"
        '<html lang="zh-CN">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{html_lib.escape(title)}</title>\n<style>{STYLE}</style>\n</head>\n<body>\n"
        f'<nav class="book-nav">{nav}</nav>\n<main>\n{body}\n{pager}\n</main>\n{PAGE_SCRIPT}\n'
        "</body>\n</html>\n"
    )


def index_body(manifest: dict, present: set[str], page_paths: dict[str, str]) -> str:
    blocks = [f"<h1>{html_lib.escape(manifest['title'])}</h1>"]
    for part in manifest["parts"]:
        chapters = [chapter for chapter in part["chapters"] if chapter["id"] in present]
        if not chapters:
            continue
        items = "".join(
            f'<li><a href="{page_paths[chapter["id"]]}">{html_lib.escape(chapter["title"])}</a></li>'
            for chapter in chapters
        )
        blocks.append(f'<h2>{html_lib.escape(part["title"])}</h2><ol>{items}</ol>')
    appendices = [appendix for appendix in manifest["appendices"] if appendix["id"] in present]
    if appendices:
        items = "".join(
            f'<li><a href="{page_paths[appendix["id"]]}">{html_lib.escape(appendix["title"])}</a></li>'
            for appendix in appendices
        )
        blocks.append(f"<h2>附录</h2><ol>{items}</ol>")
    return "\n".join(blocks)


def build(
    out_dir: Path = DEFAULT_OUT,
    docs_root: Path = DOCS,
    quiz_dir: Path = QUIZ_DIR,
    manifest: dict | None = None,
) -> tuple[list[str], list[str]]:
    manifest = manifest or manifest_module.build_manifest(manifest_module.load_toc())
    entries = [chapter for part in manifest["parts"] for chapter in part["chapters"]]
    entries += manifest["appendices"]
    present = [entry for entry in entries if (docs_root / entry["file"]).exists()]
    missing = [entry["id"] for entry in entries if not (docs_root / entry["file"]).exists()]
    if not present:
        raise ValueError(f"no chapter files found under {docs_root}")
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    public = docs_root / "public"
    if public.exists():
        shutil.copytree(public, out_dir, dirs_exist_ok=True)
    page_paths = {
        entry["id"]: Path(entry["file"]).with_suffix(".html").as_posix() for entry in present
    }
    items = [(entry["id"], entry["title"], page_paths[entry["id"]]) for entry in present]
    pages = []
    for entry in present:
        text = (docs_root / entry["file"]).read_text(encoding="utf-8")
        _, body = split_frontmatter(text)
        content = render_markdown(body, quiz_dir)
        content = wrap_tables(content)
        content = MD_HREF_RE.sub(
            lambda match: f'href="{match.group(1)}.html{match.group(2) or ""}"', content
        )
        content = add_image_dimensions(content, public)
        depth = len(Path(entry["file"]).parts) - 1
        content = relativize(content, depth)
        content = wrap_figures(content, lazy=True, zoom=True)
        page_path = out_dir / page_paths[entry["id"]]
        page_path.parent.mkdir(parents=True, exist_ok=True)
        pager = chapter_pager_html(items, page_paths[entry["id"]])
        page_path.write_text(
            page_shell(entry["title"], content, nav_html(items, page_paths[entry["id"]]), pager),
            encoding="utf-8",
        )
        pages.append(page_paths[entry["id"]])
    index = index_body(manifest, {entry["id"] for entry in present}, page_paths)
    (out_dir / "index.html").write_text(
        page_shell(manifest["title"], index, nav_html(items, "index.html")), encoding="utf-8"
    )
    return pages, missing


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="把统一 manifest 渲染为临时静态站。")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.check:
            with tempfile.TemporaryDirectory() as tmp:
                pages, missing = build(Path(tmp))
                absent = [page for page in pages if not (Path(tmp) / page).exists()]
        else:
            pages, missing = build(args.out_dir)
            absent = [page for page in pages if not (args.out_dir / page).exists()]
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 1
    if absent:
        print("missing output pages: " + ", ".join(absent), file=sys.stderr)
        return 1
    print(f"built {len(pages)} pages, {len(missing)} planned chapters missing")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

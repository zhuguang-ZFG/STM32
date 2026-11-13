"""Build the merged book as a temporary static site."""

from __future__ import annotations

import argparse
import html as html_lib
import json
import posixpath
import re
import shutil
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
body { max-width: 48rem; margin: 0 auto; padding: 2rem 1rem 4rem; font-family: system-ui, sans-serif; line-height: 1.75; color: #1f2328; }
nav.book-nav { border-bottom: 1px solid #d0d7de; margin-bottom: 2rem; padding-bottom: 1rem; font-size: 0.9rem; }
nav.book-nav ol { display: flex; flex-wrap: wrap; gap: 0.25rem 1rem; list-style: none; padding: 0; }
pre { background: #f6f8fa; padding: 0.75rem; overflow-x: auto; }
code { background: #f6f8fa; padding: 0.1rem 0.25rem; }
table { border-collapse: collapse; }
th, td { border: 1px solid #d0d7de; padding: 0.35rem 0.6rem; }
.quiz { border: 1px solid #d0d7de; border-radius: 6px; padding: 1rem; margin: 1.5rem 0; }
img { max-width: 100%; }
"""
PRINT_SCRIPT = """<script>
window.addEventListener('beforeprint', () => {
  document.querySelectorAll('details').forEach((item) => { item.open = true; });
});
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


def nav_html(items: list[tuple[str, str, str]], current_path: str) -> str:
    current_dir = posixpath.dirname(current_path)
    links = []
    for _, title, path in items:
        href = posixpath.relpath(path, current_dir or ".")
        links.append(f'<li><a href="{href}">{html_lib.escape(title)}</a></li>')
    return "<ol>" + "".join(links) + "</ol>"


def page_shell(title: str, body: str, nav: str) -> str:
    return (
        "<!DOCTYPE html>\n"
        '<html lang="zh-CN">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{html_lib.escape(title)}</title>\n<style>{STYLE}</style>\n</head>\n<body>\n"
        f'<nav class="book-nav">{nav}</nav>\n<main>\n{body}\n</main>\n{PRINT_SCRIPT}\n'
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
        content = MD_HREF_RE.sub(
            lambda match: f'href="{match.group(1)}.html{match.group(2) or ""}"', content
        )
        depth = len(Path(entry["file"]).parts) - 1
        content = relativize(content, depth)
        page_path = out_dir / page_paths[entry["id"]]
        page_path.parent.mkdir(parents=True, exist_ok=True)
        page_path.write_text(
            page_shell(entry["title"], content, nav_html(items, page_paths[entry["id"]])),
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

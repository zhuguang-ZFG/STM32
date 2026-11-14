#!/usr/bin/env python3
"""印刷版构建器：把 52 章装配成单文件 A4 书稿 HTML（打印的输入）。

与 `build_html.py` 的分工：那个负责**站点**（多页、导航、测验交互）；这个
负责**单文件书稿**——封面、目录（页码槽位）、卷分隔页、52 章按序连排。
内容复用前者的 `render_markdown`/`quiz_html`，所以"工艺改、内容不改"。

印刷特有处理：
- SMIL 动画在纸上会停在第一帧（多为透明），构建时用 Chromium 截取
  dur×62% 处的画面转成 PNG 数据 URI（确定性、可重跑）；
- 全部本地图片转数据 URI，单文件自包含，Chromium 在任何路径都能打印；
- 跨章 `.md` 链接改写为书内锚点（`#chNN`），PyMuPDF 后处理据此落书签与页码；
- 测验答案 `details[open]` 直接展开（纸上点不开）。

用法：
  python book/build_print_edition.py                    # 全量 → book/dist/print/merged-book.html
  python book/build_print_edition.py --sample 3         # 原型：封面+目录+前 3 章
"""

from __future__ import annotations

import argparse
import base64
import html as html_lib
import posixpath
import re
import sys
from pathlib import Path

BOOK_DIR = Path(__file__).resolve().parent
REPO_ROOT = BOOK_DIR.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(BOOK_DIR))

import build_html as site  # noqa: E402  — build_html 里相对 book/ 导入 manifest
from print_css import PRINT_CSS  # noqa: E402

DOCS = REPO_ROOT / "docs"
QUIZ_DIR = DOCS / ".vitepress" / "data" / "quizzes"
PUBLIC = DOCS / "public"
DEFAULT_OUT = REPO_ROOT / "book" / "dist" / "print" / "merged-book.html"

ANIM_SEEK_RATIO = 0.62          # 动画帧取 62% 处：中后段、信息最全
CHAPTER_HEAD = re.compile(r"^#\s+(.+)$", re.M)


def data_uri(path: Path, mime: str) -> str:
    payload = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{payload}"


def svg_mime(path: Path) -> str:
    return "image/svg+xml" if path.suffix == ".svg" else "image/png"


_anim_cache: dict[str, str] = {}


def anim_frame_uri(svg_path: Path) -> str:
    """SMIL 动画截取 dur×62% 的确定性一帧转 PNG（打印纸上动画是死图）。"""
    key = svg_path.name
    if key in _anim_cache:
        return _anim_cache[key]
    from playwright.sync_api import sync_playwright

    text = svg_path.read_text(encoding="utf-8")
    durs = [float(v) for v in re.findall(r'dur="([0-9.]+)s"', text)]
    seek_ms = int((max(durs) if durs else 10.0) * ANIM_SEEK_RATIO * 1000)
    width = int(re.search(r'viewBox="0 0 ([\d.]+)', text).group(1))
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": width + 20, "height": 900})
        page.goto(svg_path.as_uri())
        page.wait_for_timeout(seek_ms + 150)
        element = page.query_selector("svg")
        if element is None:
            raise RuntimeError(f"no <svg> in {svg_path}")
        tmp = svg_path.with_suffix(".probe.png")
        element.screenshot(path=str(tmp))
        browser.close()
    uri = data_uri(tmp, "image/png")
    tmp.unlink(missing_ok=True)
    _anim_cache[key] = uri
    return uri


def inline_image_uri(src: str) -> tuple[str, bool]:
    """本地资产 → 数据 URI；返回 (uri, 是否动画帧)。"""
    rel = src.lstrip("/")
    path = PUBLIC / rel
    if not path.exists():
        return src, False
    if path.suffix == ".svg" and "/anim/" in f"/{rel}":
        return anim_frame_uri(path), True
    mime = {
        ".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg", ".webp": "image/webp", ".gif": "image/gif",
    }.get(path.suffix, "application/octet-stream")
    return data_uri(path, mime), False


def inline_assets(html: str) -> str:
    """把 src/href 指向本地资产的 <img> 全部换成数据 URI。"""

    def repl(match: re.Match) -> str:
        src = match.group(2)
        if src.startswith(("http", "data:")):
            return match.group(0)
        uri, _ = inline_image_uri(src)
        return f'{match.group(1)}="{uri}"'

    return re.sub(r'(src)="(/[^"]+)"', repl, html)


def open_quiz_details(html: str) -> str:
    """印刷版答案直接展开：quiz-answer 与其他 details 全部 open。"""
    return html.replace("<details", "<details open")


def rewrite_book_links(content: str, current_file: str,
                       file_to_id: dict[str, str]) -> str:
    """把跨章 `.md` 链接改成书内锚点，同章链接保留小节 fragment。"""
    current_file = posixpath.normpath(current_file)

    def replace(match: re.Match[str]) -> str:
        target, frag = match.group(1), match.group(2) or ""
        if target.startswith(("http://", "https://", "mailto:")):
            return match.group(0)
        target_file = f"{target}.md"
        if target_file.startswith("/"):
            normalized = posixpath.normpath(target_file.lstrip("/"))
        else:
            normalized = posixpath.normpath(
                posixpath.join(posixpath.dirname(current_file), target_file))
        anchor = file_to_id.get(normalized)
        if not anchor:
            return f'href="{target}.html{frag}"'
        if normalized == current_file:
            return f'href="{frag}"' if frag and frag != "#" else f'href="#{anchor}"'
        return f'href="#{anchor}"'

    return site.MD_HREF_RE.sub(replace, content)


def chapter_section(entry: dict, docs_root: Path,
                    file_to_id: dict[str, str]) -> str:
    """一章 → <section id=…>。返回 (html, 标题)。"""
    text = (docs_root / entry["file"]).read_text(encoding="utf-8")
    _, body = site.split_frontmatter(text)
    content = site.render_markdown(body, QUIZ_DIR)
    content = rewrite_book_links(content, entry["file"], file_to_id)
    content = inline_assets(content)
    content = open_quiz_details(content)
    head = CHAPTER_HEAD.search(body)
    title = head.group(1).strip() if head else entry["title"]
    return (f'<section class="chapter" id="{entry["id"]}">\n'
            f'<h1>{html_lib.escape(entry["title"])}</h1>\n{content}\n</section>\n'), title


def build(out_path: Path | None = None, sample: int | None = None) -> Path:
    from book import manifest as manifest_module
    manifest = manifest_module.build_manifest(manifest_module.load_toc())
    out_path = Path(out_path) if out_path else DEFAULT_OUT
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # 章清单：卷 → 章
    parts = manifest["parts"]
    file_to_id = {
        posixpath.normpath(entry["file"]): entry["id"]
        for part in parts for entry in part["chapters"]
    }
    file_to_id.update({
        posixpath.normpath(entry["file"]): entry["id"]
        for entry in manifest["appendices"]
    })
    flat = []
    for part in parts:
        for chapter in part["chapters"]:
            if (DOCS / chapter["file"]).exists():
                flat.append((part, chapter))

    if sample:
        flat = flat[:sample]

    cover = (
        '<section class="cover" id="front">\n'
        '<div class="kicker">STM32 · ESP32-S3 · GD32 · FreeRTOS · RT-Thread</div>\n'
        f'<h1>{html_lib.escape(manifest["title"])}</h1>\n'
        f'<p class="subtitle">{html_lib.escape(manifest.get("subtitle", ""))}</p>\n'
        '<div class="rule-block meta">寄存器级深度教学 · 全程实物实验 · 双书合并版<br>'
        'GitHub: zhuguang-ZFG/STM32</div>\n</section>\n'
    )

    toc_rows = []
    sections = []
    heads = []
    outline = []
    outline.append((1, "封面", "front"))
    toc_rows.append(("front", "封面"))
    for part in parts:
        in_part = [c for c in flat if c[0]["id"] == part["id"]]
        if not in_part:
            continue
        outline.append((1, part["title"], f"part-{part['id']}"))
        parts_html = (
            f'<section class="part-page" id="part-{part["id"]}">\n'
            f'<div class="part-kicker">{html_lib.escape(part["id"].upper())}</div>\n'
            f"<h1>{html_lib.escape(part['title'][0:40])}</h1>\n"
            f'<p class="part-goal">{html_lib.escape(part.get("goal", ""))}</p>\n</section>\n'
        )
        sections.append(parts_html)
        toc_rows.append((f"part-{part['id']}", part["title"]))
        for _, chapter in in_part:
            html, _title = chapter_section(chapter, DOCS, file_to_id)
            sections.append(html)
            heads.append((chapter["id"], chapter["title"]))
            outline.append((2, chapter["title"], chapter["id"]))
            toc_rows.append((chapter["id"], chapter["title"]))
    for appendix in manifest["appendices"]:
        if (DOCS / appendix["file"]).exists():
            html, _title = chapter_section(appendix, DOCS, file_to_id)
            sections.append(html)
            heads.append((appendix["id"], appendix["title"]))
            outline.append((1, appendix["title"], appendix["id"]))
            toc_rows.append((appendix["id"], appendix["title"]))

    toc_html = ['<section class="toc-page" id="toc"><h2>目录</h2>']
    for anchor, label in toc_rows:
        css = "toc-part" if anchor.startswith("part-") else "toc-row"
        page_ref = "" if anchor.startswith("part-") else '<span class="page-ref"></span>'
        # 每一行都是真链接：PyMuPDF 后处理依赖这些链接产生命名目的地
        toc_html.append(
            f'<a class="{css}" href="#{anchor}">'
            f'<span class="toc-label">{html_lib.escape(label)}</span>'
            f'{page_ref}</a>'
        )
    toc_html.append("</section>\n")

    document = (
        "<!DOCTYPE html>\n<html lang=\"zh-CN\">\n<head>\n<meta charset=\"utf-8\">\n"
        f"<title>{html_lib.escape(manifest['title'])}</title>\n"
        f"<style>{PRINT_CSS}</style>\n</head>\n<body>\n"
        + '<main class="book">\n' + cover + "\n".join(toc_html) + "\n" + "\n".join(sections) + "\n</main>\n</body>\n</html>\n"
    )
    document = inline_assets(document)          # 封面/分隔页若有内联资源一并处理
    out_path.write_text(document, encoding="utf-8", newline="\n")

    # 元数据交给 print_pdf.py：outline / toc_rows / heads
    meta = {
        "outline": [{"level": lvl, "label": label, "anchor": anchor}
                    for lvl, label, anchor in outline],
        "toc_rows": [a for a, _ in toc_rows],
        "heads": heads, "title": manifest["title"],
        "subtitle": manifest.get("subtitle", ""),
        "author": "zhuguang-ZFG", "lang": "zh",
        # front_anchor = 第一章正文页（目录页码的搜索范围在其之前），不是封面
        "front_anchor": (flat[0][1]["id"] if flat else "front"),
        "toc_title": "目录",
    }
    meta_path = out_path.with_suffix(".meta.json")
    import json as _json
    meta_path.write_text(_json.dumps(meta, ensure_ascii=False, indent=1) + "\n",
                         encoding="utf-8", newline="\n")
    print(f"print edition: {out_path} ({len(flat)} chapters, "
          f"{len(outline)} outline entries)")
    return out_path


def manifest_parts_iter(manifest: dict):
    return [c for part in manifest["parts"] for c in part["chapters"]]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--sample", type=int, default=None,
                        help="原型：只装配前 N 章")
    args = parser.parse_args(argv)
    build(Path(args.out), sample=args.sample)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

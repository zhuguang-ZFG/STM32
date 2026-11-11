#!/usr/bin/env python3
"""Build the offline single-file HTML/PDF edition of 《通往单片机之路》.

Source of truth:
  - 88 chapter manuscripts live in docs/<section>/ (VitePress markdown);
  - parts / chapter compasses / sources live in manifest.json;
  - appendices live in mcu-book/book/;
  - quiz data lives in docs/.vitepress/data/quizzes/*.json.

The builder adapts the site dialect (::: containers, <AnimFigure>, <QuizBank>,
<LabStatus>, <VideoEmbed>, calculators, mermaid) into static offline HTML,
inlines every image and animation as a data URI, and audits the whole-book
contract before emitting dist/mcu-deep-book.html.
"""

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
PUBLIC_DIR = DOCS_DIR / "public"
BOOK_DIR = ROOT / "book"
QUIZ_DIR = DOCS_DIR / ".vitepress" / "data" / "quizzes"
PROJECTS_JSON = REPO_ROOT / "code" / "projects.json"
sys.path.insert(0, str(ROOT / "print"))
import art  # noqa: E402 — 自绘主题插图（书稿工艺层）
DIST_DIR = ROOT / "dist"
MANIFEST_PATH = ROOT / "manifest.json"
OUTPUT_NAME = "mcu-deep-book.html"
PDF_NAME = "mcu-deep-book.pdf"
SITE_BASE = "https://zhuguang-zfg.github.io/STM32/mcu/"
REPO_BASE = "https://github.com/zhuguang-ZFG/STM32"
def chapter_count(manifest: dict) -> int:
    """正文章数从 manifest 推导：新部落地即自动纳入，不再钉死常量。"""
    return sum(len(part["files"]) for part in manifest["parts"])

HREF_ATTR = re.compile(r"(?P<prefix>\bhref\s*=\s*)(?P<quote>[\"'])(?P<value>.*?)(?P=quote)", re.I)
SRC_ATTR = re.compile(r"(?P<prefix>\bsrc\s*=\s*)(?P<quote>[\"'])(?P<value>.*?)(?P=quote)", re.I)
ID_ATTR = re.compile(r"(?P<prefix>\bid\s*=\s*)(?P<quote>[\"'])(?P<value>.*?)(?P=quote)", re.I)
TABLE_BLOCK = re.compile(r"<table\b[^>]*>.*?</table>", re.I | re.DOTALL)
TABLE_ROW = re.compile(r"<tr\b[^>]*>.*?</tr>", re.I | re.DOTALL)
TABLE_CELL = re.compile(r"<(?:th|td)\b", re.I)
FRONTMATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
H1_LINE = re.compile(r"^#\s+.+?\s*$", re.MULTILINE)
CONTAINER_OPEN = re.compile(r"^:::\s*(tip|warning|info|danger|details)\b\s*(.*?)\s*$")
QUIZ_TAG = re.compile(r"<QuizBank\s+chapter=\"([^\"]+)\"\s*/>")
ANIM_TAG = re.compile(r"<AnimFigure\s+src=\"([^\"]+)\"(?:\s+caption=\"([^\"]*)\")?\s*/>")
LAB_STATUS_TAG = re.compile(r"<LabStatus\s*/>")
VIDEO_TAG = re.compile(
    r"<VideoEmbed\s+type=\"(bilibili|youtube)\"\s+id=\"([^\"]+)\"(?:\s+title=\"([^\"]*)\")?\s*/>"
)
WIDGET_TAG = re.compile(r"<(BaudCalc|ClockCalc|LabOverview|PathFinder|LearningMap|McuUpdates)\s*/>")
MERMAID_FENCE = re.compile(r"```mermaid\n.*?\n```", re.DOTALL)
PARAGRAPH_IMAGE = re.compile(r"<p>\s*(<img\b[^>]*>)\s*</p>", re.I)
IMAGE_TAG = re.compile(r"<img\b[^>]*>", re.I)
ALT_ATTR = re.compile(r"\balt=\"(.*?)\"", re.I)
RESIDUAL_COMPONENT = re.compile(
    r"<(?:QuizBank|AnimFigure|LabStatus|VideoEmbed|BaudCalc|ClockCalc|LabOverview"
    r"|PathFinder|LearningMap|McuUpdates|RegisterExplorer)[\s>/]|:::|<video\b",
    re.I,
)
ADMONITION_ICONS = {"tip": "💡", "warning": "⚠️", "info": "ℹ️", "danger": "🛑", "details": "📋"}
ADMONITION_LABELS = {"tip": "提示", "warning": "注意", "info": "背景", "danger": "危险", "details": "清单"}


class BuildError(RuntimeError):
    """Raised when the manuscript violates the whole-book contract."""


# ---------------------------------------------------------------------------
# manifest


def load_manifest(path: Path = MANIFEST_PATH) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BuildError(f"cannot read manifest {path}: {exc}") from exc


def chapter_files(manifest: dict) -> list[str]:
    return [name for part in manifest["parts"] for name in part["files"]]


def validate_manifest(manifest: dict) -> None:
    required = {
        "title",
        "subtitle",
        "version",
        "date",
        "language",
        "author",
        "repository",
        "license",
        "parts",
        "chapter_guides",
        "appendices",
        "sources",
    }
    missing_keys = sorted(required - set(manifest))
    if missing_keys:
        raise BuildError(f"manifest missing keys: {missing_keys}")

    parts = manifest["parts"]
    if not isinstance(parts, list) or not parts:
        raise BuildError("manifest parts must be a non-empty list")
    flattened = chapter_files(manifest)
    if len(set(flattened)) != len(flattened):
        raise BuildError(
            f"chapter list must not contain duplicates, got {len(flattened)} entries / {len(set(flattened))} unique"
        )
    for name in flattened:
        if not (DOCS_DIR / name).is_file():
            raise BuildError(f"chapter manuscript missing: docs/{name}")
    for part in parts:
        for field in ("id", "title", "goal", "intro", "files"):
            if not part.get(field):
                raise BuildError(f"part missing field: {field}")

    guides = manifest["chapter_guides"]
    if set(guides) != set(flattened):
        missing = sorted(set(flattened) - set(guides))
        extra = sorted(set(guides) - set(flattened))
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


# ---------------------------------------------------------------------------
# frontmatter and markdown dialect


def parse_frontmatter(text: str, source_label: str) -> tuple[dict, str]:
    match = FRONTMATTER.match(text)
    fields: dict[str, object] = {}
    if not match:
        raise BuildError(f"chapter is missing frontmatter: {source_label}")
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, _, raw = line.partition(":")
        value = raw.strip().strip('"').strip("'")
        if re.fullmatch(r"\d+", value):
            fields[key.strip()] = int(value)
        elif value.startswith("[") and value.endswith("]"):
            try:
                fields[key.strip()] = json.loads(value)
            except json.JSONDecodeError:
                fields[key.strip()] = value
        else:
            fields[key.strip()] = value
    if fields.get("status") != "done":
        raise BuildError(f"chapter is not status=done: {source_label} ({fields.get('status')!r})")
    return fields, text[match.end():].lstrip("\n")


def strip_h1(text: str) -> str:
    return H1_LINE.sub("", text, count=1).strip()


def _stars(level: object) -> str:
    try:
        filled = int(level)
    except (TypeError, ValueError):
        return ""
    return "★" * max(0, min(filled, 5)) + "☆" * max(0, 5 - filled)


def convert_containers(text: str, source_label: str) -> str:
    """Rewrite VitePress ::: tip/warning blocks into md_in_html divs."""
    output: list[str] = []
    stack: list[tuple[str, str]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == ":::":
            if not stack:
                raise BuildError(f"unbalanced ::: close in {source_label}")
            stack.pop()
            output.append("")
            output.append("</div>")
            continue
        match = CONTAINER_OPEN.match(stripped)
        if match:
            kind, title = match.group(1), match.group(2).strip()
            label = f"{ADMONITION_LABELS[kind]} · {title}" if title else ADMONITION_LABELS[kind]
            stack.append((kind, label))
            output.append(
                f'<div class="admonition admonition-{kind}" markdown="1">'
                f'<p class="admonition-title">{ADMONITION_ICONS[kind]} {html.escape(label)}</p>'
            )
            output.append("")
            continue
        output.append(line)
    if stack:
        raise BuildError(f"unclosed ::: container in {source_label}: {stack[-1]}")
    return "\n".join(output)


def load_quizzes() -> dict[str, dict]:
    quizzes: dict[str, dict] = {}
    for path in sorted(QUIZ_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        quizzes[data["chapter"]] = data
    return quizzes


def _quiz_question_items(quiz: dict) -> list[str]:
    items: list[str] = []
    for question in quiz["questions"]:
        options = "".join(
            f'<li>{html.escape(option)}</li>' for option in question["options"]
        )
        items.append(
            "<li class=\"quiz-question\">"
            f"<p class=\"quiz-q\">{html.escape(question['q'])}</p>"
            f'<ul class="quiz-options">{options}</ul></li>'
        )
    return items


def quiz_html(quiz: dict, chapter_id: str) -> str:
    items = "".join(_quiz_question_items(quiz))
    return (
        f'<section class="quiz-bank" aria-label="本章自测">'
        f'<h2 class="quiz-title">🎯 {html.escape(quiz["title"])}</h2>'
        f'<ol class="quiz-questions">{items}</ol>'
        f'<p class="quiz-note">先选完再翻：<a href="#appendix-exercises-answers-{html.escape(chapter_id, quote=True)}">'
        f'答案与逐项解析在附录 C 的本组</a>；在线版可点击即时判分。</p></section>'
    )


def quiz_answer_html(quiz: dict) -> str:
    blocks: list[str] = []
    for index, question in enumerate(quiz["questions"], start=1):
        answer = question["answer"]
        letter = chr(ord("A") + answer) if isinstance(answer, int) and 0 <= answer < 26 else "?"
        answer_text = re.sub(r"^[A-F][.、]\s*", "", question["options"][answer])
        blocks.append(
            f'<div class="quiz-answer-item">'
            f'<p class="quiz-answer-q">{index}. {html.escape(question["q"])}</p>'
            f'<p class="quiz-answer-key"><strong>答案 {letter}</strong>'
            f'<span class="quiz-answer-text">{html.escape(answer_text)}</span></p>'
            f'<p class="quiz-answer-why">{html.escape(question["a"])}</p>'
            f'</div>'
        )
    return "".join(blocks)


def substitute_components(
    text: str,
    source_label: str,
    frontmatter: dict,
    quizzes: dict[str, dict],
) -> str:
    def quiz_repl(match: re.Match[str]) -> str:
        chapter = match.group(1)
        quiz = quizzes.get(chapter)
        if quiz is None:
            raise BuildError(f"quiz data missing for <QuizBank chapter=\"{chapter}\"> in {source_label}")
        if quiz.get("title") is None or not quiz.get("questions"):
            raise BuildError(f"quiz data is empty: {chapter}")
        return quiz_html(quiz, chapter)

    text = QUIZ_TAG.sub(quiz_repl, text)

    def anim_repl(match: re.Match[str]) -> str:
        src = match.group(1)
        caption = match.group(2) or ""
        return f'<p><img class="anim" src="{html.escape(src, quote=True)}" alt="{html.escape(caption, quote=True)}"></p>'

    text = ANIM_TAG.sub(anim_repl, text)

    if LAB_STATUS_TAG.search(text):
        text = LAB_STATUS_TAG.sub(lab_status_html(frontmatter, source_label), text)

    def video_repl(match: re.Match[str]) -> str:
        kind, video_id, title = match.group(1), match.group(2), match.group(3) or match.group(2)
        url = (
            f"https://www.bilibili.com/video/{video_id}"
            if kind == "bilibili"
            else f"https://youtu.be/{video_id}"
        )
        site = "哔哩哔哩" if kind == "bilibili" else "YouTube"
        return (
            f'<aside class="video-card"><p class="video-card-title">🎬 {html.escape(title)}'
            f'<span class="video-card-site">@ {site}</span></p>'
            f'<p class="video-card-note">离线书不内嵌在线视频；'
            f'<a href="{html.escape(url, quote=True)}">去 {site} 观看 ↗</a></p></aside>'
        )

    text = VIDEO_TAG.sub(video_repl, text)

    site_page = site_url_for_chapter(source_label)

    def widget_repl(match: re.Match[str]) -> str:
        name = match.group(1)
        return (
            f'<aside class="widget-note"><p>🧮 这里在在线版是一个可交互组件'
            f'（<code>{html.escape(name)}</code>，改参数即时出数）；'
            f'离线书请按正文给定的参数手算，或到'
            f'<a href="{html.escape(site_page, quote=True)}">在线版该页</a>把玩。</p></aside>'
        )

    text = WIDGET_TAG.sub(widget_repl, text)

    if source_label == "rtos/compare/01-choose.md":
        text = MERMAID_FENCE.sub(DECISION_TREE_HTML, text)
    else:
        def mermaid_repl(match: re.Match[str]) -> str:
            return (
                '<aside class="widget-note"><p>🧮 这一节在在线版是可交互图表；'
                "离线书未收录其渲染，需对照在线版阅读。</p></aside>"
            )

        text = MERMAID_FENCE.sub(mermaid_repl, text)

    residual = RESIDUAL_COMPONENT.search(text)
    if residual:
        raise BuildError(f"unsupported component syntax remains in {source_label}: {residual.group(0)!r}")
    return text


def lab_status_html(frontmatter: dict, source_label: str) -> str:
    minutes = frontmatter.get("minutes", "")
    difficulty = _stars(frontmatter.get("difficulty"))
    code_ready = frontmatter.get("code_status") == "ready"
    code_note = frontmatter.get("code_note", "")
    code_cell = ("工程已提供" if code_ready else "工程建设中") + (
        f" · {html.escape(str(code_note))}" if code_note else ""
    )
    if frontmatter.get("hardware_status") == "verified":
        evidence = str(frontmatter.get("evidence", "")).removesuffix(".md")
        verify_cell = f'<a href="{html.escape(SITE_BASE + evidence + ".html", quote=True)}">查看实测记录</a>'
    else:
        verify_cell = "待上板实测；下文为预期现象，空白记录不表示验证通过"
    return (
        '<table class="lab-status"><tbody>'
        f'<tr><th scope="row">时长</th><td>约 {html.escape(str(minutes))} 分钟</td></tr>'
        f'<tr><th scope="row">难度</th><td>{difficulty}</td></tr>'
        f'<tr><th scope="row">配套代码</th><td>{code_cell}</td></tr>'
        f'<tr><th scope="row">上板验证</th><td>{verify_cell}</td></tr>'
        "</tbody></table>"
    )


DECISION_TREE_HTML = """
<div class="decision-tree" role="img" aria-label="RTOS 选型决策树（静态版）">
  <p class="dt-node dt-start">项目立项</p>
  <p class="dt-arrow">↓</p>
  <div class="dt-branch">
    <p class="dt-question">芯片平台已定？</p>
    <ul class="dt-options">
      <li><span class="dt-label">ESP32 系列</span><span class="dt-result">ESP-IDF 自带 FreeRTOS，别折腾，直接用</span></li>
      <li><span class="dt-label">STM32 / 国产 MCU</span><span class="dt-continue">继续 ↓</span></li>
    </ul>
  </div>
  <div class="dt-branch">
    <p class="dt-question">需要现成组件吗？（网络 / 文件系统 / UI / OTA）</p>
    <ul class="dt-options">
      <li><span class="dt-label">需要且想省事</span><span class="dt-result">RT-Thread 标准版，软件包点单</span></li>
      <li><span class="dt-label">安全认证场景</span><span class="dt-continue">见下方认证分支</span></li>
      <li><span class="dt-label">不需要或自研</span><span class="dt-continue">继续 ↓</span></li>
    </ul>
  </div>
  <div class="dt-branch">
    <p class="dt-question">团队熟悉谁？</p>
    <ul class="dt-options">
      <li><span class="dt-label">FreeRTOS</span><span class="dt-result">FreeRTOS，极简可控</span></li>
      <li><span class="dt-label">RT-Thread</span><span class="dt-result">RT-Thread 标准版</span></li>
    </ul>
  </div>
  <div class="dt-branch">
    <p class="dt-question">有认证包袱？（车规 / 医疗）</p>
    <ul class="dt-options">
      <li><span class="dt-label">有</span><span class="dt-result">考虑商用认证内核，或静态化 FreeRTOS</span></li>
      <li><span class="dt-label">无</span><span class="dt-continue">回到「团队熟悉谁」</span></li>
    </ul>
  </div>
  <div class="dt-branch">
    <p class="dt-question">资源够吗？（标准版约 32K Flash 起步）</p>
    <ul class="dt-options">
      <li><span class="dt-label">紧张</span><span class="dt-result">RT-Thread Nano：3K 起步 + 手工扩展</span></li>
      <li><span class="dt-label">宽裕</span><span class="dt-result">RT-Thread 标准版</span></li>
    </ul>
  </div>
  <p class="dt-source">静态版由在线版 mermaid 决策树整理而来；逐节点依据见正文。</p>
</div>
"""


# ---------------------------------------------------------------------------
# path helpers


def _safe_local_path(base: Path, raw_path: str, source_label: str) -> Path:
    decoded = unquote(raw_path.replace("\\", "/"))
    target = (base / decoded.lstrip("/")).resolve()
    try:
        target.relative_to(REPO_ROOT.resolve())
    except ValueError as exc:
        raise BuildError(f"local path escapes repository: {source_label}:{raw_path}") from exc
    return target


def _resolve_md_target(source_file: Path, raw_path: str, source_label: str) -> Path:
    if raw_path.startswith("/"):
        return _safe_local_path(DOCS_DIR, raw_path, source_label)
    # Site pages live under base /STM32/mcu/, so relative links (and their ../ counts)
    # resolve in URL space, which is one level deeper than the file system.
    import posixpath

    section = source_label.rsplit("/", 1)[0] if "/" in source_label else ""
    url_dir = posixpath.join("/STM32/mcu", section) + "/"
    resolved = posixpath.normpath(posixpath.join(url_dir, raw_path))
    if not resolved.startswith("/STM32/mcu/"):
        raise BuildError(f"local link escapes site base: {source_label}:{raw_path}")
    return _safe_local_path(DOCS_DIR, resolved[len("/STM32/mcu"):], source_label)


def _resolve_asset_target(source_file: Path, raw_path: str, source_label: str) -> Path:
    if raw_path.startswith("/"):
        public = _safe_local_path(PUBLIC_DIR, raw_path, source_label)
        if public.is_file():
            return public
        return _safe_local_path(DOCS_DIR, raw_path, source_label)
    return _safe_local_path(source_file.parent, raw_path, source_label)


def _data_uri(path: Path, source_label: str) -> str:
    if not path.is_file():
        raise BuildError(f"missing local image in {source_label}: {path.relative_to(REPO_ROOT)}")
    mime, _ = mimetypes.guess_type(path.name)
    if not mime or not mime.startswith("image/"):
        raise BuildError(f"unsupported local image type: {path}")
    payload = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{payload}"


def _repository_url(target: Path) -> str:
    relative = target.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    # 合并进 STM32 单仓后，GitHub 上的源码路径多一层 mcu/ 前缀。
    if target.is_dir():
        return f"{REPO_BASE}/tree/main/mcu/{relative}"
    return f"{REPO_BASE}/blob/main/mcu/{relative}"


def site_url_for_chapter(chapter_path: str) -> str:
    page = chapter_path.removesuffix(".md")
    return f"{SITE_BASE}{page}.html"


# ---------------------------------------------------------------------------
# rendering


def cjk_slugify(value: str, separator: str) -> str:
    """VitePress-style slug: keep CJK word characters, drop punctuation, spaces to '-'."""
    value = re.sub(r"[^\w\s-]", "", value, flags=re.UNICODE).strip().lower()
    return re.sub(r"[\s-]+", separator, value) or "section"


def fragment_key(fragment: str) -> str:
    """锚点比较键：去掉连字符/下划线/空白再小写。

    为什么需要它：同一个标题在三处的锚点不一样 —— 书籍构建器直接丢标点
    （`第五步：接线（SWD 四线）` → `第五步接线swd-四线`），站点侧 VitePress 把全角标点
    折成 `-`（→ `第五步-接线-swd-四线`），GitHub 又是另一种。源码里的链接只能写一条，
    所以解析时按"去分隔符后比较"，两边都能落到同一个 id 上。
    """
    return re.sub(r"[-_\s]+", "", fragment).lower()


def render_markdown(source: str) -> str:
    renderer = markdown.Markdown(
        extensions=["extra", "toc", "sane_lists"],
        extension_configs={"toc": {"permalink": False, "slugify": cjk_slugify}},
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


class BookContext:
    """Shared state for one build: anchors, quizzes, manifest."""

    def __init__(self, manifest: dict) -> None:
        self.manifest = manifest
        self.chapters = chapter_files(manifest)
        self.chapter_anchor = {
            name: f"ch{index:02d}" for index, name in enumerate(self.chapters, start=1)
        }
        self.chapter_meta = {
            name: {
                "number": index,
                "anchor": f"ch{index:02d}",
                "path": DOCS_DIR / name,
            }
            for index, name in enumerate(self.chapters, start=1)
        }
        self.part_of_index: dict[str, str] = {}
        self.part_anchor: dict[str, str] = {}
        for part in manifest["parts"]:
            anchor = f"part-{part['id']}"
            self.part_anchor[part["id"]] = anchor
            for name in part["files"]:
                self.part_of_index[name] = part["id"]
        self.section_index_anchor: dict[Path, str] = {}
        for part in manifest["parts"]:
            section = next(iter(part["files"])).rsplit("/", 1)[0]
            index_path = (DOCS_DIR / section / "index.md").resolve()
            self.section_index_anchor[index_path] = f"part-{part['id']}"
        for hub in (DOCS_DIR / "index.md", DOCS_DIR / "rtos" / "index.md"):
            if hub.is_file():
                self.section_index_anchor[hub.resolve()] = "contents"
        self.quizzes = load_quizzes()
        self.path_to_name = {info["path"].resolve(): name for name, info in self.chapter_meta.items()}
        self._fragment_index: dict[str, dict[str, str]] = {}
        self.stats = {"figures": 0}
        self.part_minutes: dict[str, int] = {}

    def anchor_lookup(self, target: Path) -> str | None:
        resolved = target.resolve()
        if resolved in self.path_to_name:
            name = self.path_to_name[resolved]
            return f"#{self.chapter_anchor[name]}"
        if resolved in self.section_index_anchor:
            return f"#{self.section_index_anchor[resolved]}"
        return None

    def resolve_fragment(self, chapter: str | None, fragment: str) -> str | None:
        """把源文件里的锚点解析成书内真实 id（失败返回 None，交给既有回退路径）。

        源文件里的锚点可能是站点风格（VitePress 把全角标点折成 "-"），而书里的 id
        是构建器自己 slug 出来的（直接丢标点）。两边不同源，所以按 fragment_key 比较。
        """
        if not chapter or not fragment:
            return None
        index = self._fragment_index.get(chapter)
        if index is None:
            index = self._build_fragment_index(chapter)
            self._fragment_index[chapter] = index
        return index.get(fragment_key(fragment))

    def _build_fragment_index(self, chapter: str) -> dict[str, str]:
        """渲染目标章一次，把「比较键 → 书内 id」记下来（按章缓存）。

        不去自己复刻 markdown toc 的重复标题计数规则，而是直接从渲染结果里读 id，
        与真正产出的 id 天然一致。
        """
        info = self.chapter_meta.get(chapter)
        if not info or not info["path"].is_file():
            return {}
        rendered = render_markdown(info["path"].read_text(encoding="utf-8"))
        index: dict[str, str] = {}
        ambiguous: set[str] = set()
        for match in ID_ATTR.finditer(rendered):
            real = f"{info['anchor']}-{match.group('value')}"
            key = fragment_key(match.group("value"))
            if key in index and index[key] != real:
                ambiguous.add(key)
                continue
            index[key] = real
        for key in ambiguous:
            index.pop(key, None)
        return index


def rewrite_local_links(rendered: str, source_file: Path, source_label: str, ctx: BookContext) -> str:
    def replace_href(match: re.Match[str]) -> str:
        original = html.unescape(match.group("value")).strip()
        if not original or original.startswith("#"):
            return match.group(0)
        parts = urlsplit(original)
        if parts.scheme or parts.netloc:
            value = original
            if re.search(r"\.md$", parts.path, re.I) and "github.com" in parts.netloc:
                value = original + "?plain=1"
        else:
            fragment = parts.fragment
            if re.search(r"\.(?:svg|png|jpe?g|gif|webp)$", parts.path, re.I):
                target = _resolve_asset_target(source_file, parts.path, source_label)
                value = _data_uri(target, source_label)
                quote = match.group("quote")
                return f"{match.group('prefix')}{quote}{html.escape(value, quote=True)}{quote}"
            raw_path = parts.path
            if raw_path.lower().endswith(".html"):
                raw_path = raw_path[:-5] + ".md"
            target = _resolve_md_target(source_file, raw_path, source_label)
            anchor = ctx.anchor_lookup(target)
            if anchor is not None:
                # 先按"去分隔符比较"把站点风格锚点解析成书内 id；解析不到才退回原来的
                # 直接拼接（那条路走不通时由 audit_html 的坏锚点检查兜住并报错）。
                resolved = ctx.resolve_fragment(ctx.path_to_name.get(target.resolve()), fragment)
                if resolved is not None:
                    value = "#" + resolved
                else:
                    value = anchor + (f"-{fragment}" if fragment else "")
            elif target.suffix.lower() == ".md" and target.is_file() and target.resolve().is_relative_to(DOCS_DIR.resolve()):
                page = target.resolve().relative_to(DOCS_DIR.resolve()).as_posix().removesuffix(".md")
                value = f"{SITE_BASE}{page}.html" + (f"#{fragment}" if fragment else "")
            elif target.resolve().is_relative_to((REPO_ROOT / "code").resolve()) and target.exists():
                value = "#appendix-examples"
            elif target.is_file() and target.suffix.lower() in {".svg", ".png", ".jpg", ".jpeg", ".gif", ".webp"}:
                value = _data_uri(target, source_label)
            elif target.exists():
                value = _repository_url(target)
            else:
                raise BuildError(f"missing local link in {source_label}: {original}")
        quote = match.group("quote")
        return f"{match.group('prefix')}{quote}{html.escape(value, quote=True)}{quote}"

    return HREF_ATTR.sub(replace_href, rendered)


def embed_local_images(rendered: str, source_file: Path, source_label: str) -> str:
    def replace_tag(match: re.Match[str]) -> str:
        tag = match.group(0)

        def replace_src(src_match: re.Match[str]) -> str:
            value = html.unescape(src_match.group("value")).strip()
            parts = urlsplit(value)
            if value.startswith("data:image/"):
                return src_match.group(0)
            if parts.scheme or parts.netloc:
                raise BuildError(f"external image is not offline-safe: {source_label}:{value}")
            target = _resolve_asset_target(source_file, parts.path, source_label)
            uri = _data_uri(target, source_label)
            quote = src_match.group("quote")
            return f"{src_match.group('prefix')}{quote}{uri}{quote}"

        return SRC_ATTR.sub(replace_src, tag, count=1)

    return IMAGE_TAG.sub(replace_tag, rendered)


def upgrade_images_to_figures(rendered: str, ctx: BookContext | None = None) -> str:
    """Give every standalone image a <figure> with its caption (alt text)."""

    def replace_paragraph(match: re.Match[str]) -> str:
        if ctx is not None:
            ctx.stats["figures"] += 1
        tag = match.group(1)
        alt_match = ALT_ATTR.search(tag)
        alt = html.unescape(alt_match.group(1)).strip() if alt_match else ""
        if alt:
            return (
                f'<figure class="anim-figure">{tag}'
                f"<figcaption>{html.escape(alt)}</figcaption></figure>"
            )
        return f'<figure class="anim-figure">{tag}</figure>'

    return PARAGRAPH_IMAGE.sub(replace_paragraph, rendered)


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


def render_document(
    markdown_text: str,
    source_file: Path,
    source_label: str,
    prefix: str,
    ctx: BookContext,
) -> str:
    rendered = render_markdown(markdown_text)
    rendered = wrap_tables(rendered)
    rendered = rewrite_local_links(rendered, source_file, source_label, ctx)
    rendered = embed_local_images(rendered, source_file, source_label)
    rendered = upgrade_images_to_figures(rendered, ctx)
    return prefix_local_ids(rendered, prefix)


# ---------------------------------------------------------------------------
# book scaffolding


def compass_html(guide: dict) -> str:
    source_links = " · ".join(
        f'<a href="#source-{html.escape(source_id)}"><code>{html.escape(source_id)}</code></a>'
        for source_id in guide["sources"]
    )
    return f"""
<aside class="chapter-compass" aria-label="本章罗盘">
  <h2>本章罗盘</h2>
  <div><strong>问题</strong><p>{html.escape(guide['question'])}</p></div>
  <div><strong>交付</strong><p>{html.escape(guide['deliverable'])}</p></div>
  <div><strong>边界</strong><p>{html.escape(guide['boundary'])}</p></div>
  <p class="source-anchors"><strong>依据锚点</strong> {source_links}</p>
</aside>"""


def chapter_header_html(chapter_number: int, title: str, frontmatter: dict, book_title: str = "") -> str:
    meta_bits: list[str] = []
    stars = _stars(frontmatter.get("difficulty"))
    if stars:
        meta_bits.append(f"难度 {stars}")
    minutes = frontmatter.get("minutes")
    if minutes:
        meta_bits.append(f"约 {html.escape(str(minutes))} 分钟")
    meta = f'<p class="chapter-meta">{" · ".join(meta_bits)}</p>' if meta_bits else ""
    # 书名号元素：印刷版用它做 string-set 的 content() 源（paged.js 只支持
    # content()/attr()，不支持字符串字面量）。零字号不占版面。
    marker = f'<span class="book-title-marker" aria-hidden="true">{html.escape(book_title)}</span>'
    return (
        f'<header>{marker}<span class="chapter-number">第 {chapter_number:02d} 章</span>'
        f"<h1>{html.escape(title)}</h1>{meta}</header>"
    )


def chapter_art_html(name: str) -> str:
    """章首手绘题图：assets/chapter-art/<分部>-<章>.svg 存在即内联，缺失静默跳过。

    题图是纯装饰题花（机制图解由正文插图承担），缺图不许阻塞构建。
    每枚 SVG 必须纯矢量、零 filter/id/url：art_guard 全目录把守 + 本函数
    装配期硬门（历史实证：带 feTurbulence 的题图会被 Chromium 整块光栅化）。
    """
    slug = name.replace("/", "-").removesuffix(".md")
    svg_path = BOOK_DIR / "assets" / "chapter-art" / f"{slug}.svg"
    if not svg_path.is_file():
        return ""
    svg = svg_path.read_text(encoding="utf-8")
    # 题图必须纯矢量：带 feTurbulence/<filter> 的题图内联进印前 HTML 后，
    # Chromium 会把它们整块光栅化（实测：滤镜版全书多 94 张位图）。
    # 该门在装配期就拦，把"静默降质"变成硬失败。
    if "feTurbulence" in svg or "<filter" in svg:
        raise BuildError(f"题图必须纯矢量（含滤镜会光栅化）：{svg_path}")
    return f'<div class="chapter-art">{svg}</div>'


def source_registry_html(manifest: dict) -> str:
    cards: list[str] = []
    for source_id, source in manifest["sources"].items():
        cards.append(
            f"""
<article class="source-card" id="source-{html.escape(source_id)}">
  <h2><code>{html.escape(source_id)}</code> {html.escape(source['title'])}</h2>
  <dl>
    <dt>权威层级</dt><dd>{html.escape(source['authority'])}</dd>
    <dt>冻结点</dt><dd>{html.escape(source['snapshot'])}</dd>
    <dt>访问日期</dt><dd>{html.escape(source['accessed'])}</dd>
    <dt>许可边界</dt><dd>{html.escape(source['license'])}</dd>
    <dt>适用范围</dt><dd>{html.escape(source['scope'])}</dd>
  </dl>
  <p><a href="{html.escape(source['url'], quote=True)}">打开来源 ↗</a></p>
</article>"""
        )
    return '<section class="source-registry">' + "".join(cards) + "</section>"


def quiz_appendix_html(ctx: BookContext) -> str:
    sections: list[str] = []
    seen_quizzes: list[str] = []
    for name in ctx.chapters:
        raw = (DOCS_DIR / name).read_text(encoding="utf-8")
        for quiz_id in QUIZ_TAG.findall(raw):
            if quiz_id in seen_quizzes:
                raise BuildError(f"quiz {quiz_id} is embedded twice in chapters")
            seen_quizzes.append(quiz_id)
            quiz = ctx.quizzes.get(quiz_id)
            if quiz is None:
                raise BuildError(f"quiz data file missing for chapter key {quiz_id}")
            number = ctx.chapter_meta[name]["number"]
            title = quiz.get("title", quiz_id)
            sections.append(
                f'<section class="quiz-appendix-group" id="answers-{quiz_id}">'
                f"<h2>第 {number:02d} 章 · {html.escape(title)}</h2>"
                f"{quiz_answer_html(quiz)}"
                f'<p class="back-to-chapter"><a href="#{ctx.chapter_anchor[name]}">回到第 {number:02d} 章 ↑</a></p>'
                "</section>"
            )
    orphans = sorted(set(ctx.quizzes) - set(seen_quizzes))
    if orphans:
        raise BuildError(f"quiz data files not referenced by any chapter: {orphans}")
    return '<section class="quiz-appendix">' + "".join(sections) + "</section>" if sections else ""


def toc_html(manifest: dict, ctx: BookContext) -> str:
    sections: list[str] = []
    for part in manifest["parts"]:
        items: list[str] = []
        for name in part["files"]:
            number = ctx.chapter_meta[name]["number"]
            title = ctx.chapter_meta[name].get("title", name)
            items.append(
                f'<li><a href="#{ctx.chapter_anchor[name]}">{number:02d}．'
                f"{html.escape(title)}</a></li>"
            )
        sections.append(
            f'<section><h2><a href="#part-{html.escape(part["id"])}">'
            f"{html.escape(part['title'])}</a></h2><p>{html.escape(part['goal'])}</p>"
            f'<ol class="toc-chapters">{"".join(items)}</ol></section>'
        )
    appendices = "".join(
        f'<li><a href="#{html.escape(item["id"])}">{html.escape(item["title"])}</a></li>'
        for item in manifest["appendices"]
    )
    return "".join(sections) + f'<section><h2>附录</h2><ol class="toc-chapters">{appendices}</ol></section>'


COPYRIGHT_HTML = """
<section class="frontmatter copyright" id="copyright">
  <h1>版权与版本</h1>
  <dl class="copyright-fields">
    <dt>书名</dt><dd>__TITLE__</dd>
    <dt>版本</dt><dd>v__VERSION__ · __DATE__</dd>
    <dt>作者</dt><dd>__AUTHOR__</dd>
    <dt>许可</dt><dd>正文与图片 __L_PROSE__ · 代码 __L_CODE__（仓库 LICENSE）</dd>
    <dt>来源</dt><dd>__REPO__/ · 在线阅读 __SITE__</dd>
    <dt>证据冻结点</dt><dd>__SOURCES__ 项来源注册（附录 E）；被引用的上游代码冻结到 tag/commit；未上板实测的现象一律标「待上板实测」。</dd>
    <dt>构建</dt><dd>由 <code>mcu-book/build_html.py</code> + <code>build_print.py</code> 从仓库 88 章源文档一键构建；同一输入两次构建的页数与开本一致（构建信息含时间戳除外）。</dd>
    <dt>书号</dt><dd>自制版本页，未申请 ISBN/CIP；发行渠道另行决定。</dd>
  </dl>
</section>
"""

COLOPHON_HTML = """
<section class="frontmatter colophon" id="colophon">
  <h1>勘误与贡献</h1>
  <p><strong>发现错误？</strong>到仓库提 Issue：<a href="__REPO__/issues">__REPO__/issues</a>。请带上章节号（如 S7）、原文一句、以及你认为正确的说法与出处——「证据驱动」对勘误同样适用。</p>
  <p><strong>想参与？</strong>校对、翻译、新章节与实验复现都欢迎；入口见仓库 <code>CONTRIBUTING.md</code>，排版与书稿工艺的讨论见 <code>docs/reference/book.md</code>。</p>
  <p><strong>贡献者</strong>：__AUTHOR__；完整名单见 <a href="__REPO__/graphs/contributors">GitHub Contributors</a>。</p>
  <p><strong>全书规模</strong>：__STATS__</p>
</section>
"""

FRONTMATTER_HTML = """
<section class="frontmatter" id="how-to-read">
  <h1>这不是文章合集，是一本书</h1>
  <p>全书 __CHAPTERS__ 章沿同一条主线推进：先把 <strong>C 与构建</strong>的地基打牢，再把 <strong>STM32F407 寄存器</strong>逐个拆开，随后上 <strong>双 RTOS</strong>、跨到 <strong>ESP32-S3</strong>、对照 <strong>GD32 双系</strong>，最后在 <strong>实物实验与双板项目</strong>里把知识钉在板子上，收官教你怎么把 <strong>大模型变成结对工程师</strong>。每章开头的「本章罗盘」约定这一章回答什么问题、交付什么、边界在哪；章末自测的答案与逐项解析集中在附录 C。</p>
  <div class="routes">
    <div class="route"><strong>零基础第一遍</strong><p>C0 → B0 → S0 → S2/S3 → 实验 E01；编译出第一个 .bin 时，你已经摸到真机器码。</p></div>
    <div class="route"><strong>只想先点灯</strong><p>S0 → S3 → E01；半小时内让霸天虎的红灯按你写的寄存器位闪烁。</p></div>
    <div class="route"><strong>面试/校招深挖</strong><p>C 篇全读 → B2/B3/B4 → S4 → S16 HardFault 取证 → F2 上下文切换。</p></div>
    <div class="route"><strong>AIoT 方向</strong><p>S 篇 → P 篇（重点 P8 Wi-Fi、P12 音频）→ J2 S3 记录器。</p></div>
    <div class="route"><strong>RTOS 进阶</strong><p>F 篇源码级 → R 篇 → 对照篇选型 → E04 优先级反转复现。</p></div>
    <div class="route"><strong>换国产芯</strong><p>G 篇 GD32F4 逐字段对照 → V 篇 RISC-V/CLIC → 拿旧工程逐项迁移。</p></div>
    <div class="route"><strong>想用 AI 加速</strong><p>A0 定位 → A2 手册对账 → A1 提示词模式；模型写假设，你对账拿终审权。</p></div>
  </div>
  <p><strong>证据口径：</strong>手册参数写文档号与修订点（附录 E 来源注册表）；被逐行引用的代码冻结到 tag/commit（FreeRTOS V11.1.0、ESP-IDF v5.5.2 等）；凡是没接仪器量过的现象，正文与实验页一律标「待上板实测」，不冒充已验证数据。</p>
  <p><strong>关于插图：</strong>书中 100 余张机制动画以内嵌 SVG 收录——HTML 版打开即播（SMIL 动画随翻页运行）；PDF 版为静态首帧。交互式计算器与在线视频在离线书中替换为提示卡片并给出在线版入口。</p>
</section>
"""


# ---------------------------------------------------------------------------
# stylesheet


CSS = r"""
:root {
  color-scheme: light dark;
  --paper: #fbfaf7;
  --ink: #17211e;
  --muted: #5c6a66;
  --line: #d5ddd9;
  --panel: #eef4f1;
  --accent: #0e6e5c;
  --accent-deep: #0a5044;
  --accent-soft: #e2f1ec;
  --warn: #9a5b00;
  --warn-soft: #fdf3e3;
  --code: #101a17;
  --code-ink: #eaf5f1;
  --cover-ink: #123b33;
  font-family: "Noto Sans CJK SC", "Microsoft YaHei", "PingFang SC", system-ui, sans-serif;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body { margin: 0; background: var(--paper); color: var(--ink); line-height: 1.78; }
a { color: var(--accent); text-underline-offset: .18em; }
a:focus-visible { outline: 3px solid var(--accent); outline-offset: 3px; }
.skip-link { position: fixed; left: 1rem; top: -5rem; z-index: 20; padding: .6rem 1rem; background: var(--ink); color: var(--paper); }
.skip-link:focus { top: 1rem; }
.book { width: min(100% - 2rem, 1000px); margin: 0 auto; }
.cover { min-height: 92vh; display: grid; align-content: center; padding: 5rem 7%; border-bottom: 4px solid var(--accent); }
.cover .eyebrow { font-weight: 700; letter-spacing: .16em; color: var(--accent); }
.cover h1 { font-size: clamp(2.6rem, 8vw, 5.6rem); line-height: 1.06; margin: .25em 0; max-width: 14ch; }
.cover .subtitle { font-size: clamp(1.1rem, 3vw, 1.65rem); max-width: 32em; }
.cover .edition { color: var(--muted); margin-top: 3rem; }
.frontmatter, .contents { padding: 4rem 6%; }
.frontmatter { border-bottom: 1px solid var(--line); }
.frontmatter .routes { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1rem; margin: 1.6rem 0; }
.route { border: 1px solid var(--line); border-radius: .8rem; padding: 1rem 1.2rem; background: var(--panel); }
.route p { margin: .35rem 0 0; }
.contents > section { border-top: 1px solid var(--line); padding: 1.2rem 0; }
.contents > section > h2 { margin: .4rem 0 .2rem; }
.contents > section > p { margin-top: 0; color: var(--muted); }
.toc-chapters { columns: 2; column-gap: 3rem; padding-left: 1.4rem; }
.toc-chapters li { break-inside: avoid; margin: .28rem 0; }
.part-divider { min-height: 42vh; display: grid; align-content: center; padding: 5rem 7%; margin-top: 3rem; border-top: 4px solid var(--accent); border-bottom: 1px solid var(--line); }
.part-divider .part-label { color: var(--accent); font-weight: 800; letter-spacing: .12em; }
.part-divider h1 { font-size: clamp(1.9rem, 5vw, 3.5rem); line-height: 1.15; }
.part-divider .part-goal { max-width: 42em; }
.part-divider .part-intro { max-width: 44em; margin-top: 1.2rem; padding: 1rem 1.2rem; border-left: 3px solid var(--line); color: var(--muted); background: color-mix(in srgb, var(--panel) 60%, transparent); border-radius: .4rem; }
.part-divider .part-stats { margin-top: 1.2rem; color: var(--accent-deep); font-weight: 600; letter-spacing: .06em; }
.part-divider .part-art { text-align: right; margin-bottom: 1rem; }
.part-divider .part-art svg { display: inline-block; height: 110px; width: auto; max-width: 100%; }
.part-divider .part-toc { columns: 2; column-gap: 2.4rem; margin-top: 1.6rem; padding: 1.1rem 0 0; border-top: 1px solid var(--line); list-style: none; font-size: .94rem; }
.part-divider .part-toc li { break-inside: avoid; margin: .22rem 0; }
.part-divider .part-toc a { color: inherit; text-decoration: none; border-bottom: 1px solid transparent; }
.part-divider .part-toc a:hover { border-bottom-color: var(--accent); }
.cover-art { width: min(340px, 72%); margin: 2rem 0 0; }
.chapter-art { width: min(400px, 84%); margin: 1.4rem auto 0.6rem; }
.chapter-art svg { display: block; width: 100%; height: auto; }
.cover-art svg { display: block; width: 100%; height: auto; }
.chapter, .appendix { padding: 4rem 6%; border-bottom: 1px solid var(--line); }
.chapter > header, .appendix > header { margin-bottom: 2.2rem; }
.chapter > header h1, .appendix > header h1 { font-size: clamp(1.9rem, 5vw, 3rem); line-height: 1.18; margin: .2em 0; }
.chapter-number { color: var(--accent); font-weight: 800; letter-spacing: .12em; }
.chapter-meta { color: var(--muted); margin: .2rem 0 0; }
h2, h3, h4 { line-height: 1.35; scroll-margin-top: 1.5rem; }
h2 { margin-top: 2.4rem; }
h3 { margin-top: 1.8rem; }
.chapter-compass { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: .8rem; margin: 1.8rem 0 3rem; padding: 1rem; background: var(--accent-soft); border-left: 5px solid var(--accent); border-radius: .6rem; }
.chapter-compass h2, .chapter-compass .source-anchors { grid-column: 1 / -1; margin: 0; }
.chapter-compass div { background: color-mix(in srgb, var(--paper) 74%, transparent); padding: .8rem; border-radius: .45rem; }
.chapter-compass div p { margin: .35rem 0 0; }
.chapter-compass strong { color: var(--accent-deep); }
.admonition { margin: 1.4rem 0; padding: .9rem 1.2rem; border-radius: .6rem; border: 1px solid var(--line); background: var(--panel); border-left: 5px solid var(--accent); }
.admonition-warning { background: var(--warn-soft); border-left-color: var(--warn); }
.admonition-title { margin: 0 0 .4rem; font-weight: 700; color: var(--accent-deep); }
.admonition-warning .admonition-title { color: var(--warn); }
.admonition > *:last-child { margin-bottom: 0; }
blockquote { margin: 1.4rem 0; padding: .25rem 1.2rem; border-left: 4px solid var(--accent); color: var(--muted); }
.anim-figure { margin: 1.6rem 0; padding: .8rem; border: 1px solid var(--line); border-radius: .8rem; background: #ffffff; break-inside: avoid; }
.anim-figure img { display: block; width: 100%; height: auto; margin: 0 auto; border-radius: .4rem; }
.anim-figure figcaption { margin-top: .6rem; text-align: center; font-size: .9rem; color: var(--muted); }
img { max-width: 100%; height: auto; }
figure > img:not(.anim-figure img) { display: block; margin: 1.2rem auto .4rem; }
table { width: 100%; border-collapse: collapse; font-size: .94rem; }
.table-scroll { max-width: 100%; overflow-x: auto; margin: 1.25rem 0 2rem; overscroll-behavior-inline: contain; }
.table-scroll:focus-visible { outline: 3px solid var(--accent); outline-offset: 3px; }
.table-scroll table { margin: 0; }
th, td { border: 1px solid var(--line); padding: .55rem .65rem; vertical-align: top; text-align: left; }
th { background: var(--panel); }
.lab-status { max-width: 34rem; margin: 1.4rem 0; }
.lab-status th { width: 6.5rem; background: var(--accent-soft); color: var(--accent-deep); }
code { font-family: "Cascadia Mono", "SFMono-Regular", Consolas, monospace; font-size: .91em; }
:not(pre) > code { padding: .12em .35em; border-radius: .3em; background: var(--panel); }
pre { overflow-x: auto; padding: 1rem 1.15rem; background: var(--code); color: var(--code-ink); border-radius: .65rem; line-height: 1.55; }
pre code { font-size: .86rem; }
details { margin: 1.2rem 0; padding: .8rem 1.1rem; border: 1px dashed var(--line); border-radius: .6rem; background: var(--panel); }
details[open] { border-style: solid; }
details > summary { cursor: pointer; font-weight: 600; }
.quiz-bank { margin: 2.6rem 0 1rem; padding: 1.2rem 1.4rem; border: 1px solid var(--accent); border-radius: .8rem; background: var(--accent-soft); }
.quiz-bank .quiz-title { margin: 0 0 .8rem; font-size: 1.15rem; }
.quiz-questions { margin: 0; padding-left: 1.4rem; }
.quiz-questions > li { margin: .9rem 0; }
.quiz-questions .quiz-q { margin: 0 0 .3rem; font-weight: 600; }
.quiz-options { margin: .2rem 0 0; padding-left: 1.3rem; color: var(--muted); list-style: none; }
.quiz-options li { margin: .15rem 0; }
.quiz-note { margin: 1rem 0 0; font-size: .9rem; color: var(--muted); }
.quiz-appendix-group { margin: 2.2rem 0; }
.quiz-answer-item { margin: 1.1rem 0; padding: .9rem 1.1rem; border: 1px solid var(--line); border-radius: .6rem; break-inside: avoid; }
.quiz-answer-q { margin: 0 0 .4rem; font-weight: 600; }
.quiz-answer-key { margin: .2rem 0; color: var(--accent-deep); }
.quiz-answer-why { margin: .3rem 0 0; color: var(--muted); }
.video-card, .widget-note { margin: 1.4rem 0; padding: .9rem 1.2rem; border: 1px solid var(--line); border-left: 5px solid var(--muted); border-radius: .6rem; background: var(--panel); }
.video-card-title { margin: 0; font-weight: 700; }
.video-card-site { margin-left: .5rem; color: var(--muted); font-weight: 400; font-size: .9em; }
.video-card-note, .widget-note p { margin: .3rem 0 0; font-size: .93rem; color: var(--muted); }
.decision-tree { margin: 1.8rem 0; padding: 1.2rem 1.4rem; border: 1px solid var(--line); border-radius: .8rem; background: var(--panel); }
.dt-start { display: inline-block; margin: 0; padding: .3rem 1rem; border-radius: 2rem; background: var(--accent); color: #fff; font-weight: 700; }
.dt-arrow { margin: .2rem 0 .2rem 1.6rem; color: var(--accent); font-weight: 700; }
.dt-branch { margin: .8rem 0 .8rem .6rem; padding: .8rem 1rem; border-left: 3px solid var(--accent); background: color-mix(in srgb, var(--paper) 82%, transparent); border-radius: .4rem; }
.dt-question { margin: 0 0 .5rem; font-weight: 700; color: var(--accent-deep); }
.dt-options { margin: 0; padding: 0; list-style: none; }
.dt-options li { display: flex; flex-wrap: wrap; gap: .4rem 1rem; margin: .3rem 0; }
.dt-label { min-width: 8rem; font-weight: 600; }
.dt-label::before { content: "↳ "; color: var(--accent); }
.dt-result { color: var(--ink); }
.dt-continue { color: var(--muted); }
.dt-source { margin: 1rem 0 0; font-size: .85rem; color: var(--muted); }
dl { display: grid; grid-template-columns: 6rem 1fr; gap: .35rem 1rem; }
dt { font-weight: 700; }
dd { margin: 0; }
p, li, dd { overflow-wrap: anywhere; }
.source-registry { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1rem; margin-top: 2rem; }
.source-card { min-width: 0; overflow-wrap: anywhere; border: 1px solid var(--line); border-radius: .7rem; padding: 1rem 1.2rem; break-inside: avoid; }
.source-card h2 { min-width: 0; font-size: 1.05rem; margin-top: 0; }
.source-card dl { min-width: 0; grid-template-columns: 5rem minmax(0, 1fr); font-size: .9rem; }
.back-to-toc, .back-to-chapter { display: inline-block; margin-top: 2rem; font-size: .92rem; }
.reading-progress { position: fixed; top: 0; left: 0; height: 3px; width: 0; background: var(--accent); z-index: 60; pointer-events: none; }
footer.book-footer { padding: 3rem 6%; color: var(--muted); text-align: center; }
@media (max-width: 720px) {
  .book { width: min(100% - 1rem, 1000px); }
  .cover, .frontmatter, .contents, .part-divider, .chapter, .appendix { padding-left: 1rem; padding-right: 1rem; }
  .frontmatter .routes, .chapter-compass, .source-registry { grid-template-columns: minmax(0, 1fr); }
  .chapter-compass h2, .chapter-compass .source-anchors { grid-column: 1; }
  .toc-chapters { columns: 1; }
  .table-scroll table { display: table; min-width: max(100%, calc(var(--table-columns) * 8rem)); white-space: normal; }
  dl { grid-template-columns: 1fr; }
  .dt-label { min-width: 0; }
}
@media (prefers-color-scheme: dark) {
  :root { --paper: #101816; --ink: #e8efec; --muted: #a9b6b1; --line: #39463f; --panel: #1a2420; --accent: #6fc6ae; --accent-deep: #8fd6c2; --accent-soft: #173129; --warn: #e0a35c; --warn-soft: #2e2415; --code: #0a100e; --code-ink: #ebf5f1; --cover-ink: #8fd6c2; }
  .anim-figure { background: #ffffff; }
}
@media print {
  :root { color-scheme: light; --paper: #fff; --ink: #111; --muted: #444; --line: #bbb; --panel: #f4f6f5; --accent: #0e6e5c; --accent-deep: #0a5044; --accent-soft: #edf6f2; }
  @page { size: A4; margin: 16mm 15mm 18mm; }
  body { font-size: 9.5pt; line-height: 1.55; print-color-adjust: exact; -webkit-print-color-adjust: exact; }
  .book { width: auto; max-width: none; }
  .cover { min-height: 245mm; page-break-after: always; }
  .frontmatter, .contents, .part-divider, .chapter, .appendix { padding: 0; }
  .frontmatter, .contents, .part-divider, .chapter, .appendix { page-break-before: always; }
  .part-divider { min-height: 200mm; }
  .table-scroll { overflow: visible; }
  .table-scroll table { min-width: 0; }
  .chapter-compass, .quiz-bank, .quiz-answer-item, table, pre, blockquote, .admonition, .source-card, .anim-figure, .decision-tree { break-inside: avoid; }
  h1, h2, h3, h4 { break-after: avoid; }
  .chapter > header { break-after: avoid; }
  details > summary { break-after: avoid; }
  .source-registry { grid-template-columns: 1fr; }
  a { color: inherit; text-decoration: none; }
  .back-to-toc, .back-to-chapter, .skip-link { display: none; }
  .reading-progress { display: none; }
  details { border: 1px solid #bbb; }
  details:not([open]) > *:not(summary) { display: block; }
}
"""


# ---------------------------------------------------------------------------
# audit


class _AuditParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.fragments: list[str] = []
        self.images: list[str] = []
        self.chapters: list[str] = []
        self.compasses = 0
        self.appendices: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        element_id = values.get("id")
        if element_id:
            self.ids.add(element_id)
            classes = (values.get("class") or "").split()
            if tag == "article" and "appendix" in classes:
                self.appendices.add(element_id)
        href = values.get("href")
        if tag == "a" and href and href.startswith("#"):
            self.fragments.append(href[1:])
        src = values.get("src")
        if tag == "img" and src:
            self.images.append(src)
        classes = (values.get("class") or "").split()
        if tag == "article" and "chapter" in classes:
            self.chapters.append(values.get("data-chapter") or "")
        if "chapter-compass" in classes:
            self.compasses += 1


def audit_html(document: str, ctx: BookContext) -> None:
    parser = _AuditParser()
    parser.feed(document)
    total = chapter_count(ctx.manifest)
    expected = [f"{index:02d}" for index in range(1, total + 1)]
    if parser.chapters != expected:
        raise BuildError(f"built chapter order is wrong: {len(parser.chapters)} chapters")
    if parser.compasses != total:
        raise BuildError(f"compass count mismatch: {parser.compasses}")
    expected_appendices = {item["id"] for item in ctx.manifest["appendices"]}
    if parser.appendices != expected_appendices:
        raise BuildError(f"appendix mismatch: {sorted(parser.appendices)}")
    broken = sorted({fragment for fragment in parser.fragments if fragment not in parser.ids})
    if broken:
        preview = ", ".join(broken[:8])
        raise BuildError(f"broken internal fragments ({len(broken)}): {preview}")
    external_images = [src for src in parser.images if not src.startswith("data:image/")]
    if external_images:
        raise BuildError(f"non-embedded images remain: {external_images[:3]}")
    if len(parser.images) < 90:
        raise BuildError(f"embedded image count suspiciously low: {len(parser.images)}")
    residual = RESIDUAL_COMPONENT.search(document)
    if residual:
        raise BuildError(f"component residue remains in book: {residual.group(0)!r}")
    for quiz_id in ctx.quizzes:
        if f'answers-{quiz_id}"' not in document:
            raise BuildError(f"quiz answers missing in appendix: {quiz_id}")


def audit_examples_appendix(ctx: BookContext) -> None:
    appendix_b = next(
        (item for item in ctx.manifest["appendices"] if item["id"] == "appendix-examples"), None
    )
    if appendix_b is None:
        raise BuildError("manifest must register appendix-examples")
    text = (BOOK_DIR / appendix_b["file"]).read_text(encoding="utf-8")
    try:
        projects = json.loads(PROJECTS_JSON.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BuildError(f"cannot read {PROJECTS_JSON}: {exc}") from exc
    missing = [project["id"] for project in projects if project["id"] not in text]
    if missing:
        raise BuildError(f"examples appendix is missing project ids: {missing}")


# ---------------------------------------------------------------------------
# assembly


def build_html(output_dir: Path | None = None, manifest_path: Path = MANIFEST_PATH) -> Path:
    manifest = load_manifest(manifest_path)
    validate_manifest(manifest)
    ctx = BookContext(manifest)
    audit_examples_appendix(ctx)
    destination = (output_dir or DIST_DIR).resolve()
    destination.mkdir(parents=True, exist_ok=True)

    # First pass: parse every chapter so titles and reading stats are available.
    parsed: dict[str, dict] = {}
    total_minutes = 0
    for part in manifest["parts"]:
        ctx.part_minutes[part["id"]] = 0
    for name in ctx.chapters:
        raw = (DOCS_DIR / name).read_text(encoding="utf-8")
        frontmatter, body = parse_frontmatter(raw, name)
        title = str(frontmatter.get("title") or "").strip()
        if not title:
            raise BuildError(f"frontmatter has no title: {name}")
        parsed[name] = {"frontmatter": frontmatter, "body": body}
        ctx.chapter_meta[name]["title"] = title
        minutes = frontmatter.get("minutes")
        if isinstance(minutes, int):
            total_minutes += minutes
            part_id = next(p["id"] for p in manifest["parts"] if name in p["files"])
            ctx.part_minutes[part_id] += minutes

    quiz_questions = sum(len(quiz.get("questions", [])) for quiz in ctx.quizzes.values())
    try:
        projects_count = len(json.loads(PROJECTS_JSON.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError):
        projects_count = 0

    body_parts: list[str | None] = [None]  # cover slot, filled after stats are known
    license_note = manifest["license"]
    copyright_page = (
        COPYRIGHT_HTML.replace("__TITLE__", html.escape(manifest["title"]))
        .replace("__VERSION__", html.escape(manifest["version"]))
        .replace("__DATE__", html.escape(manifest["date"]))
        .replace("__AUTHOR__", html.escape(manifest["author"]))
        .replace("__L_PROSE__", html.escape(license_note["prose_and_images"]))
        .replace("__L_CODE__", html.escape(license_note["code"]))
        .replace("__REPO__", REPO_BASE)
        .replace("__SITE__", SITE_BASE)
        .replace("__SOURCES__", str(len(manifest["sources"])))
    )
    body_parts.append(
        f"""
{copyright_page}
{FRONTMATTER_HTML.replace("__CHAPTERS__", str(chapter_count(manifest)))}
<section class="contents" id="contents"><h1>目录与分部目标</h1>{toc_html(manifest, ctx)}</section>"""
    )

    art_inlined = 0
    for part in manifest["parts"]:
        part_minutes = ctx.part_minutes.get(part["id"], 0)
        part_hours = round(part_minutes / 60, 1)
        part_toc = "".join(
            f'<li><a href="#ch{ctx.chapter_meta[name]["number"]:02d}">'
            f"{ctx.chapter_meta[name]['number']:02d}．"
            f"{html.escape(ctx.chapter_meta[name]['title'])}</a></li>"
            for name in part["files"]
        )
        body_parts.append(
            f"""
<section class="part-divider" id="part-{html.escape(part['id'])}">
  <div class="part-art">{art.part_art(part['id'])}</div>
  <p class="part-label">PART {html.escape(part['id'].upper())}</p>
  <h1>{html.escape(part['title'])}</h1>
  <p class="part-goal">{html.escape(part['goal'])}</p>
  <p class="part-intro">{html.escape(part['intro'])}</p>
  <p class="part-stats">本部 {len(part['files'])} 章 · 约 {part_minutes} 分钟（{part_hours} 小时）</p>
  <ol class="toc-chapters part-toc">{part_toc}</ol>
</section>"""
        )
        for name in part["files"]:
            info = parsed[name]
            number = ctx.chapter_meta[name]["number"]
            source_file = ctx.chapter_meta[name]["path"]
            prepared = convert_containers(info["body"], name)
            prepared = substitute_components(
                prepared, name, info["frontmatter"], ctx.quizzes
            )
            prepared = strip_h1(prepared)
            rendered = render_document(prepared, source_file, name, f"ch{number:02d}", ctx)
            guide = manifest["chapter_guides"][name]
            art_html = chapter_art_html(name)
            art_inlined += bool(art_html)
            body_parts.append(
                f"""
<article class="chapter" id="ch{number:02d}" data-chapter="{number:02d}">
  {chapter_header_html(number, info['frontmatter'].get('title', name), info['frontmatter'], manifest['title'])}
  {art_html}
  {compass_html(guide)}
  {rendered}
  <a class="back-to-toc" href="#contents">返回目录 ↑</a>
</article>"""
            )

    for appendix in manifest["appendices"]:
        path = BOOK_DIR / appendix["file"]
        raw = path.read_text(encoding="utf-8")
        # 标题以 manifest 为准：页面 header、书内目录、PDF 书签三处同源；
        # 正文 h1 只做存在性校验（防空文件），渲染时删除避免双标题。
        title = appendix["title"]
        extract_appendix_title(raw, appendix["file"])
        content = strip_h1(raw)
        if appendix["id"] == "appendix-exercises":
            content = content.replace("<!-- quizzes:auto -->", quiz_appendix_html(ctx))
            if "<!-- quizzes:auto -->" not in raw:
                raise BuildError("exercises appendix is missing the quizzes:auto placeholder")
        rendered = render_document(content, path, appendix["id"], appendix["id"], ctx)
        registry = (
            source_registry_html(manifest) if appendix["id"] == "appendix-references" else ""
        )
        art_html = chapter_art_html(appendix["file"])
        body_parts.append(
            f"""
<article class="appendix" id="{html.escape(appendix['id'])}">
  <header><span class="book-title-marker" aria-hidden="true">{html.escape(manifest['title'])}</span><span class="chapter-number">APPENDIX</span><h1>{html.escape(title)}</h1></header>
  {art_html}
  {rendered}
  {registry}
  <a class="back-to-toc" href="#contents">返回目录 ↑</a>
</article>"""
        )

    reading_hours = round(total_minutes / 60)
    body_parts.append(
        COLOPHON_HTML.replace("__REPO__", REPO_BASE)
        .replace("__AUTHOR__", html.escape(manifest["author"]))
        .replace(
            "__STATS__",
            f"{chapter_count(manifest)} 章正文（{len(manifest['parts'])} 部），约 {reading_hours} 小时通读，"
            f"{ctx.stats['figures']} 张机制动画与插图，{projects_count} 个配套工程（附录 B），"
            f"{quiz_questions} 道自测题（附录 C），{len(manifest['sources'])} 个冻结来源（附录 E）。",
        )
    )

    body_parts[0] = f"""
<section class="cover" id="cover">
  <p class="eyebrow">通往单片机之路</p>
  <h1>{html.escape(manifest['title'])}</h1>
  <p class="subtitle">{html.escape(manifest['subtitle'])}</p>
  <div class="cover-art">{art.cover_art()}</div>
  <p class="edition">v{html.escape(manifest['version'])} · {html.escape(manifest['date'])}<br>
  {html.escape(manifest['author'])}<br>
  正文与图片 {html.escape(license_note['prose_and_images'])} · 代码 {html.escape(license_note['code'])}</p>
</section>"""

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
<main class="book">{''.join(body_parts)}</main>
<footer class="book-footer">本书由 <code>mcu-book/build_html.py</code> 从 88 章源文档构建；来源、冻结点与许可见附录 E。</footer>
<script>
/* 打印/PDF 前展开全部折叠块（章节参考答案不许在纸书里失踪），打完恢复。 */
(function () {{
  var openAll = function () {{
    document.querySelectorAll('details:not([open])').forEach(function (d) {{
      d.open = true; d.dataset.bookAutoOpened = '1';
    }});
  }};
  var restore = function () {{
    document.querySelectorAll('details[data-book-auto-opened]').forEach(function (d) {{
      delete d.dataset.bookAutoOpened; d.open = false;
    }});
  }};
  window.addEventListener('beforeprint', openAll);
  window.addEventListener('afterprint', restore);
}})();
/* 109 张 SMIL 动画跑在主线程上：离屏（含 200px 预载带）暂停、回视口续播；
   系统「减少动效」偏好下全部停在首帧——与在线站点 AnimFigure 同一口径。 */
(function () {{
  var apply = function (svg, pause) {{
    if (svg && typeof svg.pauseAnimations === 'function') {{
      if (pause) svg.pauseAnimations(); else svg.unpauseAnimations();
    }}
  }};
  var svgs = Array.prototype.slice.call(document.querySelectorAll('.anim-figure svg'));
  if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {{
    svgs.forEach(function (s) {{ apply(s, true); }});
    return;
  }}
  if (!('IntersectionObserver' in window)) return;
  var io = new IntersectionObserver(function (entries) {{
    entries.forEach(function (entry) {{ apply(entry.target, !entry.isIntersecting); }});
  }}, {{ rootMargin: '200px 0px' }});
  svgs.forEach(function (s) {{ io.observe(s); }});
}})();
/* 顶部阅读进度条 + ←/→ 章间跳转：纯增强，无 JS 时阅读不受影响。 */
(function () {{
  var bar = document.createElement('div');
  bar.className = 'reading-progress';
  document.body.appendChild(bar);
  var chapters = Array.prototype.slice.call(document.querySelectorAll('article.chapter, article.appendix'));
  function onScroll() {{
    var h = document.documentElement;
    var max = h.scrollHeight - h.clientHeight;
    bar.style.width = (max > 0 ? (h.scrollTop / max) * 100 : 0) + '%';
  }}
  window.addEventListener('scroll', onScroll, {{ passive: true }});
  onScroll();
  function currentIndex() {{
    var y = window.scrollY + 120;
    var idx = 0;
    for (var i = 0; i < chapters.length; i++) {{
      if (chapters[i].offsetTop <= y) idx = i;
    }}
    return idx;
  }}
  document.addEventListener('keydown', function (e) {{
    if (e.altKey || e.ctrlKey || e.metaKey) return;
    var tag = (e.target && e.target.tagName) || '';
    if (/INPUT|TEXTAREA|SELECT/.test(tag)) return;
    if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
    var idx = currentIndex() + (e.key === 'ArrowRight' ? 1 : -1);
    if (idx < 0 || idx >= chapters.length) return;
    e.preventDefault();
    chapters[idx].scrollIntoView({{ behavior: 'smooth', block: 'start' }});
  }});
}})();
</script>
</body>
</html>
"""
    audit_html(document, ctx)
    output = destination / OUTPUT_NAME
    output.write_text(document, encoding="utf-8", newline="\n")
    print(f"html  {output} ({output.stat().st_size} bytes, {chapter_count(manifest)} chapters, 题图 {art_inlined}/{chapter_count(manifest)})")
    return output


def extract_appendix_title(text: str, source_label: str) -> str:
    match = re.search(r"^#\s+(.+?)\s*$", text, re.MULTILINE)
    if not match:
        raise BuildError(f"missing appendix title: {source_label}")
    return match.group(1).strip()


# ---------------------------------------------------------------------------
# pdf


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


def restructured_outline(entries: list, manifest: dict, title_map: dict[str, str]) -> list:
    """Reshape Chromium's flat heading outline into 部(1) → 章(2) → 节(3/4).

    entries: [[level, title, page], ...] in print order. The expected part /
    chapter / appendix sequence must all be found, in order — a miss is a
    contract failure, not a cosmetic downgrade.
    """
    expected: list[tuple[str, str, str | None]] = []
    chapter_numbers: dict[str, int] = {}
    number = 0
    for part in manifest["parts"]:
        expected.append(("part", part["title"], None))
        for name in part["files"]:
            number += 1
            chapter_numbers[name] = number
            expected.append(("chapter", title_map[name], name))
    for appendix in manifest["appendices"]:
        expected.append(("appendix", appendix["title"], None))

    def find(title: str, start: int) -> int:
        # 结构条目只会是 level 1（正文 h1）；书内目录页里的同名标题是
        # level 2/3 条目，必须跳过。Chromium 生成 outline 时会吞掉个别空格
        # （"CMake 与"→"CMake与"），匹配忽略全部空白。
        needle = re.sub(r"\s+", "", title)
        for index in range(start, len(entries)):
            level, entry_title, _ = entries[index]
            if level == 1 and re.sub(r"\s+", "", entry_title) == needle:
                return index
        raise BuildError(f"pdf outline: structural entry not found: {needle!r}")

    first_part = find(expected[0][1], 0)
    new_toc: list[list] = []
    front_pages = {"这不是文章合集，是一本书", "目录与分部目标"}
    for _level, title, page in entries[:first_part]:
        clean = title.strip()
        if clean in front_pages:
            new_toc.append([1, clean, page])

    positions = []
    cursor = first_part
    for kind, title, name in expected:
        cursor = find(title, cursor)
        positions.append((kind, title, name, cursor))
        cursor += 1

    for index, (kind, title, name, entry_index) in enumerate(positions):
        _, _, page = entries[entry_index]
        clean = title.strip()
        if kind == "chapter":
            new_toc.append([2, f"{chapter_numbers[name]:02d} {clean}", page])
        else:
            new_toc.append([1, clean, page])
        next_index = positions[index + 1][3] if index + 1 < len(positions) else len(entries)
        # 附录在书签树里是「章」级（level 1），其 h2 小节收 level 2；
        # 正文章在 level 2，其 h2 小节收 level 3——保持逐级 +1。
        section_level = 2 if kind == "appendix" else 3
        for level, section_title, section_page in entries[entry_index + 1:next_index]:
            section = section_title.strip()
            if level != 2 or section in {"本章罗盘", ""}:
                continue
            new_toc.append([section_level, section, section_page])
    for position, row in enumerate(new_toc):
        level = row[0]
        previous = new_toc[position - 1][0] if position else 0
        if level < 1 or level > 4 or level > previous + 1:
            context = new_toc[max(0, position - 2):position + 2]
            raise BuildError(f"pdf outline: bad hierarchy at row {position + 1} (level {level} after {previous}): {context!r}")
    return new_toc


def running_header_map(toc: list, book_title: str) -> list[tuple[int, str]]:
    """[(start_page, label)] — running-head marks from the reshaped outline.

    Chapter (level 2) and appendix (level 1 "附录…") entries each own their
    pages; earlier front-matter pages fall back to the book title.
    """
    marks: list[tuple[int, str]] = []
    in_appendix = False
    for level, title, page in toc:
        clean = title.strip()
        if level == 1:
            in_appendix = clean.startswith("附录")
            if in_appendix:
                marks.append((page, clean))
            elif not marks:
                marks.append((page, book_title))
        elif level == 2 and not in_appendix:
            # 附录内的 h2 小节不另起页眉，附录标题覆盖到附录末页。
            marks.append((page, clean))
    return marks


def header_label_for_page(headers: list[tuple[int, str]], book_title: str, page_number: int) -> str:
    """某一页应画的页眉文字（含 >48 字截断规则）。

    _stamp_page_numbers 与 check_pdf.py 共用：页眉“该是什么”只有这一处定义。
    """
    label = book_title
    for start, text in headers:
        if start <= page_number:
            label = text
        else:
            break
    if len(label) > 48:
        label = label[:47] + "…"
    return label


def header_skip_pages(toc: list) -> set[int]:
    """不画页眉的页码集合——前言、目录、分部隔页（level 1 且非附录条目）。

    与 _stamp_page_numbers 单真源：check_pdf.py 用同一函数对产物做反向校验，
    避免“画页眉的规则”和“查页眉的规则”各自维护一份而悄悄漂移。
    """
    return {
        page
        for level, text, page in toc
        if level == 1 and not text.strip().startswith("附录")
    }


def _stamp_page_numbers(raw_pdf: Path, output_pdf: Path, title: str) -> None:
    try:
        import fitz
    except ImportError as exc:
        raise BuildError("PyMuPDF is required for page numbers") from exc

    document = fitz.open(raw_pdf)
    try:
        manifest = load_manifest()
        title_map = {}
        for name in chapter_files(manifest):
            raw = (DOCS_DIR / name).read_text(encoding="utf-8")
            frontmatter, _ = parse_frontmatter(raw, name)
            title_map[name] = str(frontmatter.get("title", "")).strip()
        toc = restructured_outline(document.get_toc(), manifest, title_map)
        document.set_toc(toc)
        headers = running_header_map(toc, title)
        # 扉页（封面由 range 起点跳过、前言、目录、部隔页）不画页眉。
        skip_header = header_skip_pages(toc)
        document.set_metadata({
            **document.metadata,
            "title": title,
            "author": manifest.get("author", ""),
            "subject": manifest.get("subtitle", ""),
            "creator": "mcu-book/build_html.py",
        })
        total = max(0, document.page_count - 1)
        for index in range(1, document.page_count):
            page = document[index]
            page_number = index + 1
            # 页眉：当前章/附录标题（中文走内置 china-s 字体），正文上边距 16mm≈45pt，画在 22pt 处不侵入。
            if page_number not in skip_header:
                label = header_label_for_page(headers, title, page_number)
                page.insert_textbox(
                    fitz.Rect(45, 16, page.rect.width - 45, 34),
                    label,
                    fontname="china-s",
                    fontsize=7.5,
                    align=fitz.TEXT_ALIGN_CENTER,
                    color=(0.45, 0.49, 0.47),
                )
            label_num = f"{page_number} / {total}"
            width = fitz.get_text_length(label_num, fontname="helv", fontsize=8)
            point = fitz.Point((page.rect.width - width) / 2, page.rect.height - 8)
            page.insert_text(point, label_num, fontname="helv", fontsize=8, color=(0.38, 0.42, 0.40))
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
    raw_pdf = html_path.with_name(".mcu-book.raw.pdf")
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
                    "Array.from(document.images).every(img => img.complete)",
                    timeout=180_000,
                )
                page.wait_for_timeout(1500)
                page.emulate_media(media="print")
                # Chromium 的 page.pdf() 不触发 beforeprint：显式展开全部折叠块，
                # 否则 344 处「参考答案」等内容在 PDF 里缺失。
                page.evaluate(
                    "document.querySelectorAll('details:not([open])')"
                    ".forEach(function (d) { d.open = true; })"
                )
                page.wait_for_timeout(400)
                page.pdf(
                    path=str(raw_pdf),
                    print_background=True,
                    prefer_css_page_size=True,
                    outline=True,
                    tagged=True,
                )
            finally:
                browser.close()
        _stamp_page_numbers(raw_pdf, output, manifest["title"])
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
            with tempfile.TemporaryDirectory(prefix="mcu-book-check-") as temporary:
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

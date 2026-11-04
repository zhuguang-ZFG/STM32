#!/usr/bin/env python3
"""Audit the book's visual distribution and bilingual structure.

The report separates web-only video from visual anchors that survive the PDF
build. It does not decide whether prose is AI-written; style and factual review
still need a human pass.

Examples:

    python tools/audit_book.py
    python tools/audit_book.py --format json
    python tools/audit_book.py --format json --write .temp/book-audit.json
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
EN_DOCS = DOCS / "en"

VIDEO_BLOCK_RE = re.compile(
    r"<!--\s*video:[^>]*-->.*?<!--\s*/video:[^>]*-->",
    re.DOTALL | re.IGNORECASE,
)
VIDEO_RE = re.compile(r"<video\b", re.IGNORECASE)
IMG_SRC_RE = re.compile(r'<img\b[^>]*\bsrc="([^"]+)"[^>]*>', re.IGNORECASE)
MD_IMG_RE = re.compile(r"!\[[^\]]*\]\(([^)\s]+)(?:\s+['\"][^'\"]*['\"])?\)")
FIGURE_RE = re.compile(r"<figure\b[^>]*>.*?</figure>", re.DOTALL | re.IGNORECASE)
CENTERED_P_RE = re.compile(
    r'<p\b[^>]*\balign=["\']center["\'][^>]*>.*?</p>',
    re.DOTALL | re.IGNORECASE,
)
FENCE_RE = re.compile(r"(?ms)^```.*?^```\s*$|^~~~.*?^~~~\s*$")
COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
TAG_RE = re.compile(r"<[^>]+>")
LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")
TABLE_RULE_RE = re.compile(
    r"(?m)^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$"
)
HEADING_RE = re.compile(r"(?m)^(#{2,3})\s+(.+?)\s*$")


@dataclass(frozen=True)
class VisualAnchor:
    position: int
    end: int
    line: int
    assets: tuple[str, ...]
    kinds: tuple[str, ...]


@dataclass(frozen=True)
class ChapterAudit:
    file: str
    chars: int
    h2: int
    h3: int
    tables: int
    code_blocks: int
    formulas: int
    videos: int
    pdf_visual_anchors: int
    visual_assets: int
    photos: int
    diagrams: int
    animations: int
    evidence_images: int
    target_visual_anchors: int
    visual_anchor_deficit: int
    max_visual_gap_chars: int
    max_visual_gap_from: str
    max_visual_gap_to: str
    asset_sequence: tuple[str, ...]


def _chapter_files(folder: Path) -> dict[str, Path]:
    found: dict[str, Path] = {}
    for path in sorted(folder.glob("[0-2][0-9]-*.md")):
        chapter_id = path.name[:2]
        if chapter_id in found:
            raise ValueError(f"duplicate chapter id {chapter_id}: {path}")
        found[chapter_id] = path
    return found


def _inside(position: int, spans: Iterable[tuple[int, int]]) -> bool:
    return any(start <= position < end for start, end in spans)


def _asset_kind(source: str) -> str:
    normalized = source.replace("\\", "/").lower()
    suffix = Path(normalized.split("#", 1)[0]).suffix
    if "/photos/" in normalized:
        return "photo"
    if "/animations/" in normalized or "/gif/" in normalized or suffix == ".gif":
        return "animation"
    if "/diagrams/" in normalized or "/boards/" in normalized:
        return "diagram"
    return "evidence"


def _sources(block: str) -> tuple[str, ...]:
    html = tuple(match.group(1) for match in IMG_SRC_RE.finditer(block))
    markdown = tuple(match.group(1) for match in MD_IMG_RE.finditer(block))
    return html + markdown


def extract_visual_anchors(text: str) -> tuple[VisualAnchor, ...]:
    """Return PDF-readable image positions, grouping one figure as one anchor."""
    without_video = VIDEO_BLOCK_RE.sub("", text)
    groups: list[tuple[int, int, tuple[str, ...]]] = []
    spans: list[tuple[int, int]] = []

    for pattern in (FIGURE_RE, CENTERED_P_RE):
        for match in pattern.finditer(without_video):
            if _inside(match.start(), spans):
                continue
            assets = _sources(match.group(0))
            if not assets:
                continue
            groups.append((match.start(), match.end(), assets))
            spans.append((match.start(), match.end()))

    for pattern in (IMG_SRC_RE, MD_IMG_RE):
        for match in pattern.finditer(without_video):
            if _inside(match.start(), spans):
                continue
            source = match.group(1)
            groups.append((match.start(), match.end(), (source,)))
            spans.append((match.start(), match.end()))

    anchors = []
    for start, end, assets in sorted(groups):
        anchors.append(
            VisualAnchor(
                position=start,
                end=end,
                line=without_video.count("\n", 0, start) + 1,
                assets=assets,
                kinds=tuple(_asset_kind(source) for source in assets),
            )
        )
    return tuple(anchors)


def _reading_chars(text: str, *, drop_code: bool) -> int:
    value = VIDEO_BLOCK_RE.sub("", text)
    if drop_code:
        value = FENCE_RE.sub("", value)
    value = COMMENT_RE.sub("", value)
    value = LINK_RE.sub(r"\1", value)
    value = TAG_RE.sub("", value)
    value = TABLE_RULE_RE.sub("", value)
    value = re.sub(r"(?m)^#{1,6}\s*", "", value)
    value = re.sub(r"[`*_>|]", "", value)
    return len(re.sub(r"\s+", "", value))


def _section_at(text: str, position: int, *, after: bool = False) -> str:
    headings = [
        (match.start(), re.sub(r"\s+#+$", "", match.group(2)).strip())
        for match in HEADING_RE.finditer(text)
    ]
    if after:
        for start, title in headings:
            if start >= position:
                return title
        return "章末"
    title = "章首"
    for start, candidate in headings:
        if start > position:
            break
        title = candidate
    return title


def _max_visual_gap(text: str, anchors: tuple[VisualAnchor, ...]) -> tuple[int, str, str]:
    without_video = VIDEO_BLOCK_RE.sub("", text)
    boundaries = [(0, 0, "章首")]
    boundaries.extend((anchor.position, anchor.end, _section_at(without_video, anchor.position)) for anchor in anchors)
    boundaries.append((len(without_video), len(without_video), "章末"))

    largest = (-1, "章首", "章末")
    for left, right in zip(boundaries, boundaries[1:]):
        gap_start = left[1]
        gap_end = right[0]
        chars = _reading_chars(without_video[gap_start:gap_end], drop_code=True)
        if chars > largest[0]:
            largest = (chars, left[2], _section_at(without_video, gap_end, after=True))
    return largest


def _target_visuals(chars: int) -> int:
    """Book 2.0 §6.3 floor — kept as the gate field for visual_anchor_deficit."""
    if chars < 6000:
        return 3
    if chars <= 10000:
        return 4
    return 6


def _overlay_target_visuals(chars: int) -> int:
    """Classic Converge Overlay §15.2: short +1 / mid +2 / long +3 on Book 2.0 floors."""
    return _target_visuals(chars) + (1 if chars < 6000 else 2 if chars <= 10000 else 3)


def _overlay_gap_budget_chars(chars: int, chapter_id: str) -> int:
    """Overlay max-gap soft budget; ch18/23/28 hard-capped at 3500.

    Book 2.0 mid band cites 1,000–1,200 continuous chars; Overlay applies 90/85/80%
    to the 1,200 reference and floors to 100. Full cutover of target_visual_anchors
    to Overlay is deferred while any chapter still has overlay deficit (see B7 census).
    """
    if chapter_id in {"18", "23", "28"}:
        return 3500
    old_upper = 1200
    if chars < 6000:
        return int((old_upper * 0.90) // 100 * 100)
    if chars <= 10000:
        return int((old_upper * 0.85) // 100 * 100)
    return int((old_upper * 0.80) // 100 * 100)


def audit_chapter(path: Path) -> ChapterAudit:
    text = path.read_text(encoding="utf-8")
    anchors = extract_visual_anchors(text)
    kinds = [kind for anchor in anchors for kind in anchor.kinds]
    assets = [Path(source.split("#", 1)[0]).name for anchor in anchors for source in anchor.assets]
    chars = _reading_chars(text, drop_code=False)
    target = _target_visuals(chars)
    gap_chars, gap_from, gap_to = _max_visual_gap(text, anchors)
    headings = list(HEADING_RE.finditer(text))
    formulas = len(re.findall(r"(?<!\\)\$[^$\n]+(?<!\\)\$", text))

    return ChapterAudit(
        file=path.relative_to(ROOT).as_posix(),
        chars=chars,
        h2=sum(match.group(1) == "##" for match in headings),
        h3=sum(match.group(1) == "###" for match in headings),
        tables=len(TABLE_RULE_RE.findall(text)),
        code_blocks=len(re.findall(r"(?m)^```|^~~~", text)) // 2,
        formulas=formulas,
        videos=len(VIDEO_RE.findall(text)),
        pdf_visual_anchors=len(anchors),
        visual_assets=len(assets),
        photos=kinds.count("photo"),
        diagrams=kinds.count("diagram"),
        animations=kinds.count("animation"),
        evidence_images=kinds.count("evidence"),
        target_visual_anchors=target,
        visual_anchor_deficit=max(0, target - len(anchors)),
        max_visual_gap_chars=gap_chars,
        max_visual_gap_from=gap_from,
        max_visual_gap_to=gap_to,
        asset_sequence=tuple(assets),
    )


def _parity(zh: ChapterAudit, en: ChapterAudit) -> dict[str, object]:
    return {
        "asset_sequence_equal": zh.asset_sequence == en.asset_sequence,
        "pdf_visual_anchor_delta": en.pdf_visual_anchors - zh.pdf_visual_anchors,
        "h2_delta": en.h2 - zh.h2,
        "h3_delta": en.h3 - zh.h3,
        "table_delta": en.tables - zh.tables,
        "code_block_delta": en.code_blocks - zh.code_blocks,
        "formula_delta": en.formulas - zh.formulas,
    }


def build_audit() -> dict[str, object]:
    zh_files = _chapter_files(DOCS)
    en_files = _chapter_files(EN_DOCS)
    expected = {f"{index:02d}" for index in range(29)}
    if set(zh_files) != expected or set(en_files) != expected:
        raise ValueError("Chinese and English docs must both contain chapter ids 00 through 28")

    chapters = []
    for chapter_id in sorted(expected):
        zh = audit_chapter(zh_files[chapter_id])
        en = audit_chapter(en_files[chapter_id])
        en = replace(
            en,
            target_visual_anchors=zh.target_visual_anchors,
            visual_anchor_deficit=max(0, zh.target_visual_anchors - en.pdf_visual_anchors),
        )
        zh_payload = asdict(zh)
        en_payload = asdict(en)
        overlay_target = _overlay_target_visuals(zh.chars)
        overlay_gap = _overlay_gap_budget_chars(zh.chars, chapter_id)
        for payload, anchors in ((zh_payload, zh.pdf_visual_anchors), (en_payload, en.pdf_visual_anchors)):
            payload["overlay_target_visual_anchors"] = overlay_target
            payload["overlay_visual_anchor_deficit"] = max(0, overlay_target - anchors)
            payload["overlay_gap_budget_chars"] = overlay_gap
        chapters.append(
            {
                "id": chapter_id,
                "zh": zh_payload,
                "en": en_payload,
                "parity": _parity(zh, en),
            }
        )

    return {
        "schema_version": 1,
        "chapter_count": len(chapters),
        "definitions": {
            "pdf_visual_anchor": "one PDF-readable image or grouped figure; video is excluded",
            "max_visual_gap_chars": "running text between PDF anchors; fenced code is excluded",
            "target_visual_anchors": "Book 2.0 §6.3 floor; both editions use the Chinese chapter scale",
            "overlay_target_visual_anchors": "Classic Converge Overlay §15.2 floor (old+1/+2/+3); informational until full cutover",
            "overlay_gap_budget_chars": "Overlay §15.2 max-gap soft budget (90/85/80% of 1200 ref; ch18/23/28 ≤3500)",
        },
        "summary": {
            language: {
                "pdf_visual_anchors": sum(item[language]["pdf_visual_anchors"] for item in chapters),
                "visual_anchor_deficit": sum(item[language]["visual_anchor_deficit"] for item in chapters),
                "chapters_below_target": sum(item[language]["visual_anchor_deficit"] > 0 for item in chapters),
                "chapters_with_photos": sum(item[language]["photos"] > 0 for item in chapters),
            }
            for language in ("zh", "en")
        },
        "chapters": chapters,
    }


def render_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# STM32 Book audit",
        "",
        "`PDF 图` excludes chapter video. `缺图` is the Book 2.0 Spec deficit; JSON also carries Overlay §15.2 fields (see B7 census).",
        "",
        "| 章 | 中文字符 | 中文 PDF 图 | 缺图 | 最大无图区 | 英文 PDF 图 | 图序一致 | 结构差异 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | :---: | --- |",
    ]
    for item in payload["chapters"]:  # type: ignore[index]
        zh = item["zh"]
        en = item["en"]
        parity = item["parity"]
        deltas = []
        for label, key in (("H2", "h2_delta"), ("H3", "h3_delta"), ("表", "table_delta"), ("码", "code_block_delta"), ("式", "formula_delta")):
            if parity[key]:
                deltas.append(f"{label}{parity[key]:+d}")
        lines.append(
            f"| {item['id']} | {zh['chars']} | {zh['pdf_visual_anchors']} | "
            f"{zh['visual_anchor_deficit']} | {zh['max_visual_gap_chars']} | "
            f"{en['pdf_visual_anchors']} | {'是' if parity['asset_sequence_equal'] else '否'} | "
            f"{', '.join(deltas) or '—'} |"
        )
    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"- 中文 PDF 视觉锚点：{payload['summary']['zh']['pdf_visual_anchors']}",  # type: ignore[index]
            f"- 中文低于目标章节：{payload['summary']['zh']['chapters_below_target']}",  # type: ignore[index]
            f"- 中文含实拍章节：{payload['summary']['zh']['chapters_with_photos']}",  # type: ignore[index]
            f"- 英文 PDF 视觉锚点：{payload['summary']['en']['pdf_visual_anchors']}",  # type: ignore[index]
        ]
    )
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--write", type=Path, help="write the report instead of stdout")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = build_audit()
    if args.format == "json":
        output = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    else:
        output = render_markdown(payload)
    if args.write:
        path = args.write if args.write.is_absolute() else ROOT / args.write
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(output, encoding="utf-8", newline="\n")
        print(path)
    else:
        print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

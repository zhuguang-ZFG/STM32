#!/usr/bin/env python3
"""Mechanical check for AI-flavoured writing in this repo's Markdown.

Catches only what is decidable by pattern: stock phrases, marketing verbs,
performative honesty, decision glyphs standing in for words, and emoji in
headings. Rhythm, rule-of-three, and paragraph flow stay with human reading.

    python3 tools/slop_lint.py                     # the whole repo
    python3 tools/slop_lint.py docs/03-GPIO与LED.md
    python3 tools/slop_lint.py --list              # show the rules

Exit code: 0 clean, 1 hits, 2 bad invocation.

Shape follows two public skills: tazhate/anti-ai-slop (rule groups, scrubbing
code and quotes before matching, escape directives) and
HermeticOrmus/markdown-discipline (no emoji, no marketing adjectives, no
glyph decision cells, headings that describe rather than announce).

What is deliberately NOT flagged, because it is correct here:
  - ★ difficulty ratings in the project chapter; a tested rating scale
  - — as the empty cell in a table, and – inside numeric ranges (48–72 MHz)
  - 破折号 in Chinese prose, which is ordinary punctuation
  - technical verbs that happen to look like marketing: unlock, 支持, 使能
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Directories that are build output, vendored, or local operations.
# `superpowers` holds design notes and implementation plans. Those are working
# documents, not published prose, and both reference skills leave internal and
# formal documents alone. Skipping it also keeps this gate from depending on
# whether that directory is present.
SKIP_DIRS = {
    ".git",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    ".temp",
    ".tmp",
    ".playwright-mcp",
    ".omp",
    "wechat-mp",
    "final-videos",
    "superpowers",
}

# Each group maps a human-readable name to the patterns that betray it.
RULES: dict[str, list[str]] = {
    "中文套话": [
        r"让我们",
        r"我们一起来?",
        r"综上所述",
        r"总的来说",
        r"总而言之",
        r"值得注意的是",
        r"众所周知",
        r"不难发现",
        r"在当今[^，。]{0,10}(时代|社会|世界)",
        r"随着[^，。]{0,12}的(飞速)?(发展|普及|到来)",
        r"希望(本文|本章|这篇)",
        r"相信你(已经|很快)",
        r"显得尤为重要",
        r"不可或缺",
        r"保驾护航",
        r"大显身手",
        r"如虎添翼",
    ],
    "中文营销词": [
        r"赋能",
        r"助力",
        r"一站式",
        r"全方位",
        r"全面提升",
        r"深度(赋能|融合)",
        r"极大地",
        r"完美(支持|兼容|解决|适配)",
        r"轻松(搞定|应对|驾驭)",
        r"强大而",
        r"业界领先",
        r"黑科技",
    ],
    "中文虚假坦诚": [
        r"说实话",
        r"老实说",
        r"坦白(说|讲)",
        r"不吹不黑",
        r"划重点",
        r"干货(满满|分享)",
    ],
    "英文 AI 词典": [
        r"\bdelv(e|es|ed|ing)\b",
        r"\butiliz(e|es|ed|ing)\b",
        r"\bleverag(e|es|ed|ing)\b",
        r"\bstreamlin(e|es|ed|ing)\b",
        r"\bunderscor(e|es|ed|ing)\b",
        r"\btapestry\b",
        r"\bmultifaceted\b",
        r"\brobust\b",
        r"\bcomprehensive\b",
        r"\bpivotal\b",
        r"\bseamless(ly)?\b",
        r"\bfurthermore\b",
        r"\bmoreover\b",
        r"\bworld.class\b",
        r"\bcutting.edge\b",
        r"\bgame.?changer\b",
        r"\bit'?s important to note\b",
        r"\bin conclusion\b",
        r"\bin today'?s .{0,20}world\b",
        r"\bdive (in|into)\b",
        r"\beffortless(ly)?\b",
    ],
    "英文虚假坦诚与软收尾": [
        r"\blet'?s be (honest|real)\b",
        r"\bto be honest\b",
        r"\bhere'?s the (thing|deal|kicker)\b",
        r"\bbottom line\b",
        r"\bhope (this|that) helps\b",
        r"\blet me know if\b",
        r"\bfeel free to\b",
    ],
    "空心分词尾": [
        r",\s*(highlighting|reflecting|underscoring|showcasing|emphasizing)\b",
        r"，(?:从而|进而)?(?:凸显|彰显)了?",
    ],
}

# Notes written for a reviewer rather than a reader: which figure is "main",
# what was deliberately left out, what a source is "allowed" to support.
# A reader needs the fact and the condition, not the bookkeeping.
RULES["审稿用语"] = [
    r"只钉在",
    r"整格照抄",
    r"不另(开|算)一套",
    r"不画进",
    r"留在核心原理",
    r"放在旁注",
    r"主图的失败路径",
    r"该来源允许支持的主张",
    r"不编(一个|一块|位号|[^。，]{0,8}(基址|地址|容量|皮法|周期数|微安|BRR))",
    # 「清洁或作废」是 Cache invalidate 的译法，是术语。
    r"(?<!清洁或)作废",
    # 附录 A 逐字锁定，那里的 "numbers are pinned to" 指工作点，不算。
    r"\b(conclusions?|ledgers?|tables?|chapter)\b[^.]{0,40}\bpinned to\b",
    r"\bcopied whole\b",
    r"\bis void\b",
    r"\bsecond ledger\b",
    r"\bstays? in the core ideas\b",
    r"\bfailure path on the key figure\b",
    r"\bclaim this source may support\b",
    r"\bdo(es)? not invent\b",
]

# Decisions belong in words, so a glyph never carries a table cell or a
# callout. The book build reads GitHub alert syntax for warnings.
HOUSE_STYLE: dict[str, list[str]] = {
    "判定符号应写成文字": [r"[✅❌]"],
    "警告请用 > [!WARNING]": [r"⚠"],
    "装饰性 emoji": [r"[\U0001F300-\U0001FAFF\U0001F000-\U0001F0FF]"],
}

# Emoji anywhere in a heading, including the dingbat range that ★ lives in.
HEADING_EMOJI = re.compile(
    r"^#{1,6} .*[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F0FF]"
)
# ★ is a rating in the project chapter, not decoration.
HEADING_EMOJI_OK = re.compile(r"[★☆]")

FENCE = re.compile(r"^\s*(```|~~~)")
# An opening fence names its language. Prose blocks (ASCII diagrams, formulas,
# console output) are tagged `text`, which keeps a highlighter off them.
FENCE_OPEN = re.compile(r"^\s*(?:```|~~~)\s*(\S+)?\s*$")
INLINE_CODE = re.compile(r"`[^`]*`")
URL = re.compile(r"\[[^\]]*\]\([^)]*\)|https?://\S+")
QUOTED = re.compile(r"「[^」]*」|“[^”]*”|\"[^\"]*\"")
HTML_TAG = re.compile(r"<[^>]+>")

IGNORE_LINE = re.compile(r"<!--\s*slop-lint:\s*ignore\s*-->")
IGNORE_OFF = re.compile(r"<!--\s*slop-lint:\s*off\s*-->")
IGNORE_ON = re.compile(r"<!--\s*slop-lint:\s*on\s*-->")


@dataclass(frozen=True)
class Hit:
    path: str
    line_no: int
    group: str
    match: str
    text: str


def _blank(match: re.Match[str]) -> str:
    return " " * len(match.group())


def scrub(line: str) -> str:
    """Blank out code, links, quotes, and tags; a banned word is fair there."""
    for pattern in (INLINE_CODE, URL, QUOTED, HTML_TAG):
        line = pattern.sub(_blank, line)
    return line


def lint(text: str, path: str, house_style: bool = True) -> list[Hit]:
    groups = dict(RULES)
    if house_style:
        groups |= HOUSE_STYLE
    compiled = {
        name: [re.compile(p, re.IGNORECASE | re.UNICODE) for p in patterns]
        for name, patterns in groups.items()
    }

    hits: list[Hit] = []
    in_fence = False
    muted = False
    for line_no, raw in enumerate(text.replace("\r\n", "\n").split("\n"), start=1):
        if IGNORE_OFF.search(raw):
            muted = True
            continue
        if IGNORE_ON.search(raw):
            muted = False
            continue
        if FENCE.match(raw):
            opening = not in_fence
            in_fence = not in_fence
            if opening and not muted:
                named = FENCE_OPEN.match(raw)
                if named and named.group(1) is None:
                    hits.append(
                        Hit(path, line_no, "代码块没写语言", raw.strip(), raw.strip())
                    )
            continue
        if in_fence or muted or IGNORE_LINE.search(raw):
            continue

        if HEADING_EMOJI.match(raw) and not HEADING_EMOJI_OK.search(raw):
            hits.append(Hit(path, line_no, "标题里的 emoji", raw.strip()[:40], raw.strip()))

        line = scrub(raw)
        for name, patterns in compiled.items():
            for pattern in patterns:
                for found in pattern.finditer(line):
                    hits.append(Hit(path, line_no, name, found.group(), raw.strip()))
    return hits


def targets(given: list[str]) -> list[Path]:
    if given:
        return [Path(name) for name in given]
    found: list[Path] = []
    for path in sorted(ROOT.rglob("*.md")):
        if any(part in SKIP_DIRS for part in path.relative_to(ROOT).parts):
            continue
        found.append(path)
    return found


def report(hits: list[Hit]) -> None:
    by_group: dict[str, list[Hit]] = {}
    for hit in hits:
        by_group.setdefault(hit.group, []).append(hit)
    for group, items in sorted(by_group.items(), key=lambda kv: -len(kv[1])):
        print(f"\n{group} ({len(items)})")
        for hit in items:
            snippet = hit.text if len(hit.text) <= 96 else hit.text[:93] + "..."
            print(f"  {hit.path}:{hit.line_no}  {hit.match!r}")
            print(f"      {snippet}")


def main(argv: list[str] | None = None) -> int:
    # The report prints Chinese and the very glyphs it flags, so a GBK console
    # would raise instead of reporting.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="查 Markdown 里的 AI 味。")
    parser.add_argument("files", nargs="*", help="要检查的文件，留空就查整个仓库")
    parser.add_argument(
        "--house-style",
        choices=["on", "off"],
        default="on",
        help="是否检查本仓库的排版约定：判定符号、警告写法、装饰 emoji（默认 on）",
    )
    parser.add_argument("--list", action="store_true", help="打印规则后退出")
    args = parser.parse_args(argv)

    if args.list:
        for name, patterns in (RULES | HOUSE_STYLE).items():
            print(f"\n{name}")
            for pattern in patterns:
                print(f"  {pattern}")
        return 0

    hits: list[Hit] = []
    for path in targets(args.files):
        if not path.is_file():
            print(f"没有这个文件：{path}", file=sys.stderr)
            return 2
        try:
            rel = path.resolve().relative_to(ROOT).as_posix()
        except ValueError:
            rel = path.as_posix()
        hits += lint(
            path.read_text(encoding="utf-8"), rel, args.house_style == "on"
        )

    if not hits:
        print("干净：没有机械命中。")
        print("节奏、三连排比、段落走向仍需人眼复读。")
        return 0

    report(hits)
    print(f"\n命中合计：{len(hits)}")
    return 1


if __name__ == "__main__":
    sys.exit(main())

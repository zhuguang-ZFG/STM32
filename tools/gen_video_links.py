#!/usr/bin/env python3
"""Write each chapter's "推荐视频 / Recommended videos" section from one file.

The links live in stm32-book/video-links.json. Every entry was opened through
the platform's own API on the date it records (Bilibili view and pagelist,
YouTube oEmbed), so a link here is a video that existed and was public then.
The chapters never hold a hand-typed link; this script renders the block
between <!-- links:chNN --> and <!-- /links:chNN --> and nothing else.

    python3 tools/gen_video_links.py           # rewrite the sections in docs/
    python3 tools/gen_video_links.py --check   # exit 1 if a chapter is stale

The section goes after "自测 / Self-test" and before the deep part
("原理与适用范围 / Principle and scope"). A chapter without that part gets it
right before its resources heading. Videos are not source cards: the numbers
in the text still come from the manuals, and nothing here enters the manifest.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "stm32-book" / "video-links.json"
ZH_DIR = ROOT / "docs"
EN_DIR = ROOT / "docs" / "en"
CHAPTER_FILE = re.compile(r"^(?P<num>0\d|1\d|2[0-8])-.+\.md$")

BILIBILI_URL = re.compile(r"^https://www\.bilibili\.com/video/(?P<id>BV[0-9A-Za-z]{10})(?:\?p=(?P<part>\d+))?$")
YOUTUBE_URL = re.compile(r"^https://www\.youtube\.com/watch\?v=(?P<id>[0-9A-Za-z_-]{11})$")
VERIFY_WAYS = {"bilibili view API", "bilibili view+pagelist API", "youtube oembed"}
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿⬀-⯿]")
KEYS = {
    "platform", "url", "id", "part", "title", "part_title", "author",
    "duration_s", "lang", "why_zh", "why_en", "verified_at", "verify",
}

LANGS = {
    "zh": {
        "heading": "## 推荐视频",
        "lead": "下面是站外的公开视频，不属于本书。和本章或手册说法不一致的地方，以手册为准。链接核对于 {date}。",
        "before": ("## 原理与适用范围",),
        "after": "## 自测",
        "platform": {"bilibili": "B 站", "youtube": "YouTube"},
        "lang": {"zh": "中文", "en": "英文"},
        "order": ("bilibili", "youtube"),
    },
    "en": {
        "heading": "## Recommended videos",
        "lead": "These are public videos outside this book. Where one disagrees with this chapter or the manuals, go by the manuals. Links checked on {date}.",
        "before": ("## Principle and scope",),
        "after": "## Self-test",
        "platform": {"bilibili": "Bilibili", "youtube": "YouTube"},
        "lang": {"zh": "Chinese", "en": "English"},
        "order": ("youtube", "bilibili"),
    },
}
RESOURCE_HEADINGS = (
    "## 相关资源", "## 权威来源与冻结点", "## Related resources", "## Further reading",
    "## Sources", "## Authoritative sources and frozen versions",
)


def load(path: Path = DATA_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(data: dict) -> list[str]:
    """Return every problem found; an empty list means the file is usable."""
    errors: list[str] = []
    extra = set(data) - {"about", "chapters"}
    if extra:
        errors.append(f"顶层只认 about 和 chapters，多了 {sorted(extra)}")
    chapters = data.get("chapters")
    if not isinstance(chapters, dict):
        return errors + ["chapters 必须是对象"]
    for num, entries in chapters.items():
        if not re.fullmatch(r"0\d|1\d|2[0-8]", num):
            errors.append(f"{num}: 章号不在 00–28")
            continue
        seen: set[str] = set()
        for i, item in enumerate(entries):
            where = f"{num}[{i}]"
            if set(item) != KEYS:
                errors.append(f"{where}: 字段不对，多了 {sorted(set(item) - KEYS)}，少了 {sorted(KEYS - set(item))}")
                continue
            url = item["url"]
            if url in seen:
                errors.append(f"{where}: 同一章里重复的链接 {url}")
            seen.add(url)
            if item["platform"] == "bilibili":
                m = BILIBILI_URL.match(url)
                if not m:
                    errors.append(f"{where}: B 站链接格式不对 {url}")
                else:
                    part = int(m.group("part")) if m.group("part") else None
                    if m.group("id") != item["id"]:
                        errors.append(f"{where}: id 与链接不一致")
                    if part != item["part"]:
                        errors.append(f"{where}: part 与链接里的 ?p= 不一致")
                    if (item["part"] is None) != (item["part_title"] is None):
                        errors.append(f"{where}: part 和 part_title 要么都有，要么都没有")
            elif item["platform"] == "youtube":
                m = YOUTUBE_URL.match(url)
                if not m:
                    errors.append(f"{where}: YouTube 链接格式不对 {url}")
                elif m.group("id") != item["id"]:
                    errors.append(f"{where}: id 与链接不一致")
                if item["part"] is not None or item["part_title"] is not None:
                    errors.append(f"{where}: YouTube 条目没有分集")
            else:
                errors.append(f"{where}: 未知平台 {item['platform']}")
            if item["lang"] not in ("zh", "en"):
                errors.append(f"{where}: lang 只能是 zh 或 en")
            if item["verify"] not in VERIFY_WAYS:
                errors.append(f"{where}: verify 写法不认识 {item['verify']}")
            try:
                dt.date.fromisoformat(item["verified_at"])
            except (TypeError, ValueError):
                errors.append(f"{where}: verified_at 不是日期")
            for key in ("title", "author", "why_zh", "why_en"):
                if not isinstance(item[key], str) or not item[key].strip():
                    errors.append(f"{where}: {key} 为空")
            if item["duration_s"] is not None and (not isinstance(item["duration_s"], int) or item["duration_s"] <= 0):
                errors.append(f"{where}: duration_s 要么是正整数，要么是 null")
            if len(item["why_zh"]) > 60:
                errors.append(f"{where}: why_zh 超过 60 字")
            if len(item["why_en"].split()) > 30:
                errors.append(f"{where}: why_en 超过 30 个词")
            for key in ("why_zh", "why_en"):
                if EMOJI.search(item[key]):
                    errors.append(f"{where}: {key} 里有 emoji")
    return errors


def duration(seconds: int | None) -> str:
    if not seconds:
        return ""
    h, rest = divmod(seconds, 3600)
    m, s = divmod(rest, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def entry_line(item: dict, lang: str) -> str:
    cfg = LANGS[lang]
    title = item["title"].replace("[", "［").replace("]", "］")
    bits = [item["author"], cfg["platform"][item["platform"]]]
    if item["part"] is not None:
        if lang == "zh":
            bits.append(f"第 {item['part']} 集「{item['part_title']}」")
        else:
            bits.append(f"part {item['part']} \"{item['part_title']}\"")
    bits.append(cfg["lang"][item["lang"]])
    length = duration(item["duration_s"])
    if length:
        bits.append(length)
    if lang == "zh":
        why = item["why_zh"].rstrip("。") + "。"
        return f"- [{title}]({item['url']})：{' · '.join(bits)}。{why}"
    why = item["why_en"].rstrip(".") + "."
    return f"- [{title}]({item['url']}): {' · '.join(bits)}. {why}"


def render(num: str, entries: list[dict], lang: str) -> str:
    cfg = LANGS[lang]
    dates = sorted(item["verified_at"] for item in entries)
    # sorted() is stable, so entries keep their file order within a platform.
    ordered = sorted(entries, key=lambda item: cfg["order"].index(item["platform"]))
    # Blank lines around the markers keep Markdown from gluing a comment to
    # the paragraph or list next to it.
    lines = [
        cfg["heading"],
        "",
        f"<!-- links:ch{num} -->",
        "",
        cfg["lead"].format(date=dates[-1]),
        "",
        *(entry_line(item, lang) for item in ordered),
        "",
        f"<!-- /links:ch{num} -->",
    ]
    return "\n".join(lines)


def h2_spans(text: str) -> list[tuple[int, str]]:
    """Offsets of H2 headings outside fenced code."""
    spans: list[tuple[int, str]] = []
    fenced = False
    pos = 0
    for line in text.split("\n"):
        if line.lstrip().startswith("```"):
            fenced = not fenced
        elif not fenced and line.startswith("## "):
            spans.append((pos, line.rstrip()))
        pos += len(line) + 1
    return spans


def patch(text: str, num: str, entries: list[dict], lang: str) -> str:
    cfg = LANGS[lang]
    crlf = "\r\n" in text
    body = text.replace("\r\n", "\n")
    spans = h2_spans(body)
    old = [i for i, (_, line) in enumerate(spans) if line == cfg["heading"]]
    if not old and not entries:
        return text
    # Drop the section this script wrote last time, if any.
    if old:
        i = old[0]
        start = spans[i][0]
        end = spans[i + 1][0] if i + 1 < len(spans) else len(body)
        body = body[:start].rstrip("\n") + "\n\n" + body[end:].lstrip("\n")
        spans = h2_spans(body)
    if entries:
        block = render(num, entries, lang)
        where = None
        for start, line in spans:
            if line in cfg["before"]:
                where = start
                break
        if where is None:
            for start, line in spans:
                if line in RESOURCE_HEADINGS:
                    where = start
                    break
        if where is None:
            body = body.rstrip("\n") + "\n\n" + block + "\n"
        else:
            body = body[:where].rstrip("\n") + "\n\n" + block + "\n\n" + body[where:]
    body = body.rstrip("\n") + "\n"
    return body.replace("\n", "\r\n") if crlf else body


def chapter_files() -> dict[str, dict[str, Path]]:
    found: dict[str, dict[str, Path]] = {}
    for lang, folder in (("zh", ZH_DIR), ("en", EN_DIR)):
        for path in sorted(folder.glob("*.md")):
            m = CHAPTER_FILE.match(path.name)
            if m:
                found.setdefault(m.group("num"), {})[lang] = path
    return found


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="按 video-links.json 写各章的推荐视频。")
    parser.add_argument("--check", action="store_true", help="只检查，不改文件；有章节过期就返回 1")
    args = parser.parse_args(argv)

    data = load()
    errors = validate(data)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    stale: list[str] = []
    for num, paths in chapter_files().items():
        entries = data["chapters"].get(num, [])
        for lang, path in paths.items():
            old = path.read_bytes().decode("utf-8")
            new = patch(old, num, entries, lang)
            if new == old:
                continue
            rel = path.relative_to(ROOT).as_posix()
            if args.check:
                stale.append(rel)
            else:
                path.write_bytes(new.encode("utf-8"))
                print("写入", rel)
    if stale:
        print("这些章节的推荐视频和 video-links.json 不一致，运行 tools/gen_video_links.py：", file=sys.stderr)
        print("\n".join("  " + rel for rel in stale), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

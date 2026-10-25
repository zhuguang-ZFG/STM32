# Classic Encyclopedia Sample Chapters Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 只加厚两章样本（中文和英文一起），把它们写成能单独读完原理、看见静态写实主图、跟上时序或状态、并把每个坑钉在附录 E 出处上的样子，样本合入时把整书升到 1.1.0，然后停下来等用户复审。

**Architecture:** 先用一次可重复的缺口扫描锁定文件名前缀，再把允许吸收的材料写成来源清单，然后才改这两章正文。新出处只追加进 `stm32-book/manifest.json` 与 `stm32-book/manifest-en.json` 的 `sources`，附录 E 的卡片由 `stm32-book/build_html.py` 的 `source_registry_html()` 生成，不手写第二份登记表。主图是 `tools/svgkit.py` 生成的静态 SVG。版本号同时写进两份 manifest、`stm32-book/revisions.json` 和 `stm32-book/README.md`。

**Tech Stack:** Python 3 标准库、现有 `stm32-book/build_html.py`、`python3 -m unittest`、`tools/svgkit.py`、`tools/check_assets.py`。不新增依赖，不改 `requirements.txt`。

单文件测试写成 `python3 stm32-book/tests/<file>.py -v`。`stm32-book/tests/` 不是 Python 包，目录名里的连字符也会让「把目录名当成包名」的加载方式失败。整套测试仍用 `python3 -m unittest discover stm32-book/tests -v`。

## Global Constraints

- 样本只加厚两章，中文和英文必须一起改。用户书面接受之前，不再改其余 27 章的正文。
- 外设池文件名是 `03`–`14` 与 `16`。基础池文件名是 `00`–`02`。`15`、`17`–`22`、`23`–`25`、`26`–`28` 不进入第一对样本。
- 扫描基线是执行当天的 `main`。本计划在 `70a8bc0`（章节正文与 v1.0.7 `dd2dfb7` 相同，其后只有设计规格）上跑过同一套脚本，结果是外设章 `03`、基础章 `00`。若执行当天脚本退出码为 2，停下来，先改本计划后面任务的路径，再写正文。
- 四块标题必须原样出现：中文 `## 原理与边界`、`## 关键插图`、`## 时序或状态`、`## 坑与出处卡`；英文 `## Principle and boundary`、`## Key figures`、`## Timing or state`、`## Pitfalls and source cards`。标题不加表情符号。
- 保留「学习目标、硬件与接线、代码实现、动手实验、相关资源」及其英文对应标题。与新块重复的「核心原理」「常见坑与排查」并入新块，不留两套说法。
- 代码继续按 `docs/CONTENT_GUIDE.md`：HAL，参数用宏。本样本不新写一套可烧录工程，保留两章现有的 HAL 片段和 `examples/gpio-blink/`。
- 改写吸收的许可顺序：先用 ST 公开 RM/DS 的事实、用自己的话重写；然后才是 MIT、BSD-2-Clause、BSD-3-Clause、ISC、CC BY 4.0、CC BY 3.0、CC0。GPL、LGPL、CC BY-NC、CC BY-ND、保留所有权利、未写许可的博客和视频只留链接，不吸收。libopencm3 保持索引。本样本不吸收社区帖。
- 新来源 id 只追加。已有 id 的对象一个字段都不改。中英两份 manifest 的 `url`、`snapshot`、`license`、`accessed` 用同一串字符；`title`、`authority`、`scope` 用对应语言。
- 章内第四块每一行只有一个主张，并链到 `#source-...`。每一块至少有一处 `#source-` 链接。
- 主图是静态 SVG，印刷后不靠 GIF 或 CSS 动画也能看懂。图上同时有正常路径和失败路径。图注写「自绘」，替代文本写结论。目标体积小于 60 KB。不把 60 KB 改成仓库新默认值。
- 不调用 `Svg.footer()`。那个方法会在图上印「自绘矢量动画」。
- 两章共用同一张 SVG。英文图注重复全部关键数字、订货号、文档号和寄存器名。
- 样本合入时版本升到 **1.1.0**。当时 `main` 若仍是 1.0.7，或并行轨道已先变成 1.0.8，都升到 1.1.0。中英文整书共用这个版本号。日期用准备合并当天的 UTC 日期。
- 不修改 `stm32-book/build_html.py`。`outline=True` 保持原样。章眉继续用文件名前两位，格式仍是 `第 {n} 章` / `Chapter {n}`。
- 并行轨道 v1.0.8（显示章号 1–29、浅层 PDF 书签）不放进样本提交。若它已先在 `main` 上，rebase 到那次提交之上，保留它的章眉和书签行为，版本仍写 1.1.0。
- 不改附录 D 三套账，不改附录 A 的既有契约，不手改 `stm32-book/book/E-参考资料.md` 或 `stm32-book/book/en/E-sources.md`。
- 不加图目录、表目录，不加第 30 章，不改 `docs/00`–`28` 的文件名，不把 `assets/video/` 收进书，不新增实拍。
- 不把厂商手册、官方插图或社区原文放进仓库。
- 不打 tag，不创建 GitHub Release。
- 不修改 `docs/superpowers/specs/2026-10-25-classic-encyclopedia-thicken-design.md`。设计规格不回写章号。

## File map

| 路径 | 责任 |
| --- | --- |
| `tools/scan_sample_chapters.py` | 只在加厚前打分，写出锁定文件 |
| `docs/superpowers/plans/2026-10-25-sample-chapter-lock.json` | 扫描表和锁定的两个前缀 |
| `docs/superpowers/plans/2026-10-25-sample-source-list.json` | 动笔前的来源清单；登记以 manifest 为准 |
| `tools/gen_sample_figures.py` | 生成两张静态主图 |
| `assets/diagrams/sample-00-boot-state.svg` | 第 00 章主图 |
| `assets/diagrams/sample-03-gpio-led.svg` | 第 03 章主图 |
| `assets/README.md` | 登记这两张图 |
| `docs/00-如何学习STM32.md` 与 `docs/en/00-how-to-learn-stm32.md` | 基础样本 |
| `docs/03-GPIO与LED.md` 与 `docs/en/03-gpio-and-led.md` | 外设样本 |
| `stm32-book/manifest.json` 与 `stm32-book/manifest-en.json` | 新 `sources`、章罗盘、版本号 |
| `stm32-book/revisions.json` | 1.1.0 修订条目 |
| `stm32-book/README.md` | 当前版本句 |
| `CREDITS.md` | 样本改写吸收小节 |
| `stm32-book/tests/test_sample_sources.py` | 来源清单的许可门 |
| `stm32-book/tests/test_sample_chapters.py` | 四块、数字、主图 |
| `stm32-book/tests/test_build.py` | 只改版本断言，账本断言保留 |

---

### Task 1: Gap scan and lock

**Files:**
- Create: `tools/scan_sample_chapters.py`
- Create: `docs/superpowers/plans/2026-10-25-sample-chapter-lock.json`（由脚本写出）

**Interfaces:**
- Consumes: `docs/00`–`docs/16` 与 `docs/en/` 里同前缀的章节。视频块 `<!-- video:` … `<!-- /video:` 内的图不算本地图。
- Produces: 锁定文件字段 `peripheral`（字符串 `"03"`）、`foundation`（字符串 `"00"`）、`peripheral_tied`、`foundation_tied`、`rows`、`baseline`。`rows` 里每章有中英行数、翻译缺口、本地图张数与后缀、`figures_zh` / `figures_en`、原理边界、时序或状态、坑的出处、`series_zh` / `series_en`。后面的任务只改这两个前缀。

打分规则（脚本已实现，不要另写一套感觉分）：

- 原理边界算「有」：同一节里同时出现完整订货号（`STM32` 加封装式后缀，例如 `STM32F103C8T6`）和「作废 / 整行重写 / 不再成立 / does not hold / is void」之一。
- 时序或状态算「有」：去掉视频块、居中 `<p>` 图和围栏代码之后，有一张 Markdown 表，且表头不是现象、Symptom、原因、Cause、消抖或 debounce，并满足下面任一条件：表头含时序、时间尺度、周期、波特、采样时间、唤醒时间、PSC、ARR、BRR、分频或 SCK 且格子里有数字；表头含阶段、步骤或状态且至少 3 行；格子里有带 `µs`、`μs`、`ns` 或 `ms` 的数字；同时出现「普通模式」和「循环模式」，或同时出现「睡眠」和「待机」。消抖延时表不算外设时序。
- 坑的出处算「有」：`##` 标题含「常见坑」或 `Pitfalls` 的那一节里有 `#source-`。
- 外设池按这三项缺失个数取最大；并列时取较小的文件名前缀，并把其余并列前缀写入 `peripheral_tied`。
- 基础池先取「没有带数字的时序或状态图」的章。一张本地 SVG 算这类图，仅当它的 `<text>` 含 `BOOT0`，或同时含 `MHz` 与 `PLL`、`时钟`、`APB` 之一。中英任一语缺这种图，该章就进入优先组。优先组里再取本地图较少的章，仍并列则取较小前缀。
- 视频海报 PNG 在视频块里，不计数。外链图不计数。
- 每一行另记 `figures_zh` / `figures_en`。一张图的角色可以多于一个：后缀是 jpg、jpeg、png 时记「实拍」；`<text>` 满足上面的带数字规则时记「带数字的时序或状态」；SVG 文本含 `LQFP`、`引脚`，或 `PA`/`PB`/`PC` 后接数字，或文件名含 `pinout`、`bluepill`、`nucleo`、`board` 时记「板卡/引脚结构」；GIF，以及既不是带数字时序也不是板卡/引脚的 SVG，记「简化示意」。角色和 `series_zh` / `series_en` 只记录，不参加排序。
- 锁定文件的 `baseline` 是运行时 `git rev-parse HEAD` 的完整哈希。

在 `70a8bc0`（完整哈希 `70a8bc0dd4315d9de1c1dc7410c2452e51ef36b6`）上这套规则的结果是：外设池只有 `03` 缺 3 分（没有原理边界、没有外设时序或状态表、坑没有 `#source-`），其余外设章缺 2 分。基础池只有 `00` 的 `toolchain-flow.svg` 角色是简化示意，不算带数字的时序或状态图；`01` 的 `boot-sequence.svg` 含 `BOOT0`；`02` 的时钟树和总线图含 MHz。`03` 的 `gpio-blink.svg` 会被记成带数字的时序或状态，外加板卡/引脚结构；那张动画不填补正文里的时序表，外设分仍按正文三项缺失计算。中英行数比都高于一半，没有翻译缺口单独入选。

- [ ] **Step 1: 写入扫描脚本**

把下面的程序保存为 `tools/scan_sample_chapters.py`。

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Score the sample-chapter pools once, before the four new headings exist.

Run from the repository root:

    python3 tools/scan_sample_chapters.py

The script writes docs/superpowers/plans/2026-10-25-sample-chapter-lock.json
and exits 0 when the rubric selects peripheral 03 and foundation 00.
If the tree has already grown the heading 原理与边界, it refuses to re-score
and exits 0 only when the lock file already records 03 and 00.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-sample-chapter-lock.json"
PERIPHERAL = [f"{i:02d}" for i in range(3, 15)] + ["16"]
FOUNDATION = ["00", "01", "02"]
LOCAL_SUFFIXES = {".svg", ".gif", ".jpg", ".jpeg", ".png"}
ORDERABLE = re.compile(r"STM32[A-Z]\d{3}[A-Z][A-Z0-9]{3,}")
VOID = re.compile(r"作废|整行重写|不再成立|does not hold|is void")
IMG = re.compile(r"""src=["']([^"']+)["']""")
VIDEO = re.compile(r"<!-- video:.*?<!-- /video:.*?-->", re.S)
SERIES = {
    "F1": re.compile(r"RM0008|STM32F10|\bF103\b|\bF1\b"),
    "F4": re.compile(r"RM0090|RM0383|STM32F4|\bF4\b"),
    "G0": re.compile(r"RM0444|STM32G0|\bG0\b"),
    "L4": re.compile(r"RM0351|STM32L4|\bL4\b"),
    "H7": re.compile(r"RM0433|RM0399|STM32H7|\bH7\b"),
}


def chapters(directory: Path) -> dict[str, Path]:
    found: dict[str, Path] = {}
    for path in sorted(directory.glob("[0-2][0-9]-*.md")):
        found[path.name[:2]] = path
    return found


def strip_unreadable(text: str) -> str:
    text = VIDEO.sub("", text)
    text = re.sub(r"<p align=\"center\">.*?</p>", "", text, flags=re.S)
    fence = chr(96) * 3
    text = re.sub(fence + r".*?" + fence, "", text, flags=re.S)
    return text


def tables(text: str) -> list[tuple[str, list[str]]]:
    lines = text.splitlines()
    found: list[tuple[str, list[str]]] = []
    index = 0
    while index < len(lines):
        if lines[index].startswith("|") and index + 1 < len(lines) and re.match(r"\|\s*-+", lines[index + 1]):
            header = lines[index]
            body: list[str] = []
            cursor = index + 2
            while cursor < len(lines) and lines[cursor].startswith("|"):
                body.append(lines[cursor])
                cursor += 1
            found.append((header, body))
            index = cursor
        else:
            index += 1
    return found


def has_boundary(text: str) -> bool:
    parts = re.split(r"(?m)^#{2,3} .*$", text)
    heads = re.findall(r"(?m)^#{2,3} .*$", text)
    chunks = [("preamble", parts[0]), *zip(heads, parts[1:])]
    for heading, body in chunks:
        blob = heading + "\n" + body
        if ORDERABLE.search(blob) and VOID.search(blob):
            return True
    return False


def has_timing_or_state(text: str) -> bool:
    """A debounce-delay table is not the peripheral's timing or state."""
    for header, rows in tables(strip_unreadable(text)):
        if re.search(r"现象|Symptom|原因|Cause|消抖|debounce", header, re.I):
            continue
        blob = header + "\n" + "\n".join(rows)
        if re.search(r"时序|时间尺度|周期|波特|采样时间|唤醒时间|PSC|ARR|BRR|分频|SCK", header) and re.search(r"\d", blob):
            return True
        if re.search(r"阶段|步骤|状态", header) and len(rows) >= 3:
            return True
        if re.search(r"\d+(?:\.\d+)?\s*(?:µs|μs|ns|ms)\b", blob):
            return True
        if ("普通模式" in blob and "循环模式" in blob) or ("睡眠" in blob and "待机" in blob):
            return True
    return False


def pitfalls_linked(text: str) -> bool:
    match = re.search(r"(?m)^## .*(常见坑|Pitfalls).*$", text)
    if not match:
        return False
    rest = text[match.end():]
    nxt = re.search(r"(?m)^## ", rest)
    section = rest[: nxt.start()] if nxt else rest
    return "#source-" in section


def local_images(text: str, chapter_path: Path) -> list[str]:
    visible = VIDEO.sub("", text)
    found: list[str] = []
    for src in IMG.findall(visible):
        low = src.lower().split("?", 1)[0]
        if low.startswith("http"):
            continue
        if Path(low).suffix.lower() not in LOCAL_SUFFIXES:
            continue
        found.append(src)
    return found


def figure_is_numbered_state(chapter_path: Path, src: str) -> bool:
    if not src.lower().split("?", 1)[0].endswith(".svg"):
        return False
    target = (chapter_path.parent / src).resolve()
    if not target.is_file():
        return False
    raw = target.read_text(encoding="utf-8", errors="replace")
    texts = re.findall(r"<text[^>]*>(.*?)</text>", raw, flags=re.S)
    blob = re.sub(r"<[^>]+>", " ", " ".join(texts))
    if "BOOT0" in blob:
        return True
    if re.search(r"\d+\s*MHz", blob) and re.search(r"PLL|时钟|APB", blob):
        return True
    return False


def series_flags(text: str) -> dict[str, bool]:
    return {name: bool(pattern.search(text)) for name, pattern in SERIES.items()}


def figure_roles(chapter_path: Path, src: str) -> list[str]:
    """Record roles. Selection does not read this list."""
    roles: list[str] = []
    low = src.lower().split("?", 1)[0]
    suffix = Path(low).suffix
    if suffix in {".jpg", ".jpeg", ".png"}:
        roles.append("实拍")
    if figure_is_numbered_state(chapter_path, src):
        roles.append("带数字的时序或状态")
    blob = ""
    if suffix == ".svg":
        target = (chapter_path.parent / src).resolve()
        if target.is_file():
            raw = target.read_text(encoding="utf-8", errors="replace")
            texts = re.findall(r"<text[^>]*>(.*?)</text>", raw, flags=re.S)
            blob = re.sub(r"<[^>]+>", " ", " ".join(texts))
    if re.search(r"LQFP|引脚|PA\d+|PC\d+|PB\d+", blob) or re.search(
        r"pinout|bluepill|nucleo|board", Path(low).name
    ):
        roles.append("板卡/引脚结构")
    if suffix == ".gif" or (
        suffix == ".svg" and "带数字的时序或状态" not in roles and "板卡/引脚结构" not in roles
    ):
        roles.append("简化示意")
    if not roles:
        roles.append("简化示意")
    return roles


def score_one(prefix: str, path: Path, english: Path) -> dict:
    chinese = path.read_text(encoding="utf-8")
    english_text = english.read_text(encoding="utf-8")
    images = local_images(chinese, path)
    english_images = local_images(english_text, english)
    numbered = any(figure_is_numbered_state(path, src) for src in images)
    english_numbered = any(figure_is_numbered_state(english, src) for src in english_images)
    boundary = has_boundary(chinese)
    timing = has_timing_or_state(chinese)
    linked = pitfalls_linked(chinese)
    missing = (0 if boundary else 1) + (0 if timing else 1) + (0 if linked else 1)
    suffixes: dict[str, int] = {}
    for src in images:
        suffix = Path(src.lower()).suffix
        suffixes[suffix] = suffixes.get(suffix, 0) + 1
    english_suffixes: dict[str, int] = {}
    for src in english_images:
        suffix = Path(src.lower()).suffix
        english_suffixes[suffix] = english_suffixes.get(suffix, 0) + 1
    z_lines = len(chinese.splitlines())
    e_lines = len(english_text.splitlines())
    return {
        "prefix": prefix,
        "zh": path.as_posix(),
        "en": english.as_posix(),
        "zh_lines": z_lines,
        "en_lines": e_lines,
        "translation_gap": e_lines * 2 < z_lines,
        "local_images": suffixes,
        "en_local_images": english_suffixes,
        "local_image_count": len(images),
        "en_local_image_count": len(english_images),
        "numbered_timing_or_state_figure": numbered,
        "en_numbered_timing_or_state_figure": english_numbered,
        "figures_zh": [{"src": src, "roles": figure_roles(path, src)} for src in images],
        "figures_en": [{"src": src, "roles": figure_roles(english, src)} for src in english_images],
        "series_en": series_flags(english_text),
        "principle_boundary": boundary,
        "timing_or_state": timing,
        "pitfall_source_link": linked,
        "missing_count": missing,
        "series_zh": series_flags(chinese),
    }


def select(rows: list[dict]) -> dict:
    peripheral = [row for row in rows if row["prefix"] in PERIPHERAL]
    foundation = [row for row in rows if row["prefix"] in FOUNDATION]
    highest = max(row["missing_count"] for row in peripheral)
    peripheral_tied = sorted(row["prefix"] for row in peripheral if row["missing_count"] == highest)
    unnumbered = [
        row
        for row in foundation
        if not row["numbered_timing_or_state_figure"] or not row["en_numbered_timing_or_state_figure"]
    ]
    foundation_pool = unnumbered if unnumbered else foundation
    fewest = min(min(row["local_image_count"], row["en_local_image_count"]) for row in foundation_pool)
    foundation_tied = sorted(
        row["prefix"]
        for row in foundation_pool
        if min(row["local_image_count"], row["en_local_image_count"]) == fewest
    )
    return {
        "peripheral": peripheral_tied[0],
        "peripheral_tied": peripheral_tied,
        "peripheral_missing_count": highest,
        "foundation": foundation_tied[0],
        "foundation_tied": foundation_tied,
    }


def already_thickened(zh: dict[str, Path]) -> bool:
    for path in zh.values():
        if "## 原理与边界" in path.read_text(encoding="utf-8"):
            return True
    return False


def main() -> int:
    zh = chapters(ROOT / "docs")
    en = chapters(ROOT / "docs" / "en")
    if already_thickened(zh):
        if not LOCK_PATH.is_file():
            print("chapters already contain 原理与边界, and the lock file is missing", file=sys.stderr)
            return 2
        lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
        print(json.dumps({"kept_lock": lock["peripheral"], "foundation": lock["foundation"]}, ensure_ascii=False))
        return 0 if lock["peripheral"] == "03" and lock["foundation"] == "00" else 2

    rows = [score_one(prefix, zh[prefix], en[prefix]) for prefix in FOUNDATION + PERIPHERAL]
    choice = select(rows)
    payload = {
        "rubric": "2026-10-25-classic-encyclopedia-sample-chapters",
        "baseline": subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True
        ).strip(),
        "peripheral": choice["peripheral"],
        "foundation": choice["foundation"],
        "peripheral_tied": choice["peripheral_tied"],
        "foundation_tied": choice["foundation_tied"],
        "peripheral_missing_count": choice["peripheral_missing_count"],
        "rows": rows,
    }
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOCK_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"peripheral={choice['peripheral']} tied={choice['peripheral_tied']} "
        f"missing={choice['peripheral_missing_count']}"
    )
    print(f"foundation={choice['foundation']} tied={choice['foundation_tied']}")
    if choice["peripheral"] != "03" or choice["foundation"] != "00":
        print("lock disagrees with the plan's baseline winners; stop and edit later tasks", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: 在改任何章节之前运行扫描**

Run: `python3 tools/scan_sample_chapters.py`

Expected: 退出码 0，标准输出含

```text
peripheral=03 tied=['03'] missing=3
foundation=00 tied=['00']
```

并生成 `docs/superpowers/plans/2026-10-25-sample-chapter-lock.json`，其中 `peripheral` 为 `03`，`foundation` 为 `00`。

若退出码为 2：停止。把脚本打印的实际前缀写进锁定文件后，先改 Task 3 以后所有写死的 `00` / `03` 路径，再继续。不要为了让退出码变成 0 去改规则。

- [ ] **Step 3: 确认设计规格没被改写**

Run: `git diff --name-only -- docs/superpowers/specs/2026-10-25-classic-encyclopedia-thicken-design.md`

Expected: 无输出。

- [ ] **Step 4: Commit**

```bash
git add tools/scan_sample_chapters.py docs/superpowers/plans/2026-10-25-sample-chapter-lock.json
git commit -m "docs: 锁定大典样本章为 00 与 03"
```

### Task 2: Source list with the license gate

**Files:**
- Create: `docs/superpowers/plans/2026-10-25-sample-source-list.json`
- Create: `stm32-book/tests/test_sample_sources.py`
- Test: `stm32-book/tests/test_sample_sources.py`

**Interfaces:**
- Consumes: Task 1 的 `peripheral == "03"` 与 `foundation == "00"`。
- Produces: 三个新 id：`rm0008-boot`、`rm0008-gpio`、`ds5319-gpio`。另有一个允许引用、但不新建对象的已有 id：`project-examples`。清单里 `community` 数组为空。

事实在 2026-10-25 从这两份 ST 入口核对过，首页分别是 RM0008 Rev 21（February 2021）和 DS5319 Rev 20（July 2025）：

- RM0008 Rev 21 第 3.4 节表 9：BOOT1 任意且 BOOT0=0 时主闪存映射到启动区；BOOT1=0 且 BOOT0=1 时系统存储器映射到启动区；BOOT1=1 且 BOOT0=1 时从内置 SRAM 启动。BOOT 脚在复位后 SYSCLK 的第 4 个上升沿锁存，退出 Standby 时重新采样。CPU 先从 `0x00000000` 取栈顶，再从 `0x00000004` 取复位向量。主闪存本体在 `0x08000000`。非互联型的系统存储器在 `0x1FFFF000`；互联型在 `0x1FFFB000`。
- RM0008 Rev 21 第 9.2.7 节 `GPIOx_LCKR`（偏移 `0x18`）：LCK[15:0] 在序列期间不变；对 LCKK 写 1、写 0、写 1，再读。确认读回 1 时锁生效，直到下次复位。序列出错则锁中止。第 9.3.5 节表 36：SWDIO 在 PA13，SWCLK 在 PA14。
- DS5319 Rev 20 图 8 与表 5，LQFP48：第 2 脚是 PC13-TAMPER-RTC，第 10 脚是 PA0-WKUP。注 5：PC13、PC14、PC15 走电源开关，灌电流能力有限（3 mA），速度不超过 2 MHz，负载不超过 30 pF，不能当作电流源去驱动 LED。
- `examples/gpio-blink/README.md` 已有的算术：3.3 V、Vf 2.0 V、5 mA，`(3.3 − 2.0) / 0.005 = 260`，取 270 Ω。板载灯在 PC13，共阳，低电平点亮。这是例程事实，用已有 id `project-examples`，不要写成数据手册结论。

打开上面两个 URL。首页修订号仍是 Rev 21 与 Rev 20 时，`accessed` 用准备合并当天的 UTC 日期，数字保持本任务的值。修订号变了就停，先按新修订改清单里的数字，再画图、再写正文。

- [ ] **Step 1: 写会失败的许可门测试**

保存为 `stm32-book/tests/test_sample_sources.py`：

```python
#!/usr/bin/env python3
"""License gate for the two sample chapters. The manifest is updated later."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE_LIST = ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-sample-source-list.json"
ALLOWED = {
    "ST-facts-restated",
    "MIT",
    "BSD-2-Clause",
    "BSD-3-Clause",
    "ISC",
    "CC BY 4.0",
    "CC BY 3.0",
    "CC0",
}
REJECTED = ("GPL", "LGPL", "CC BY-NC", "CC BY-ND", "All rights reserved")


class SampleSourceListTests(unittest.TestCase):
    def test_source_list_keeps_the_license_gate(self) -> None:
        payload = json.loads(SOURCE_LIST.read_text(encoding="utf-8"))
        self.assertEqual(["00", "03"], sorted(payload["chapters"]))
        self.assertEqual([], payload["community"])
        ids = [item["id"] for item in payload["absorb"]]
        self.assertEqual(["rm0008-boot", "rm0008-gpio", "ds5319-gpio"], ids)
        for item in payload["absorb"]:
            self.assertIn(item["license_class"], ALLOWED)
            self.assertTrue(item["url"].startswith("https://"))
            self.assertNotIn("http://", item["url"])
            for banned in REJECTED:
                self.assertNotIn(banned, item["license"])
            self.assertTrue(item["do_not_copy"])
            self.assertNotIn(".pdf", item["repo_path"] if "repo_path" in item else "")
        by_id = {item["id"]: item for item in payload["absorb"]}
        self.assertEqual("3.4", by_id["rm0008-boot"]["section"])
        self.assertEqual("9.2.7", by_id["rm0008-gpio"]["section"])
        self.assertEqual("note 5", by_id["ds5319-gpio"]["section"])
        self.assertEqual("project-examples", payload["reuse_existing"][0]["id"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试，确认它因为清单不存在而失败**

Run: `python3 stm32-book/tests/test_sample_sources.py -v`

Expected: FAIL，`FileNotFoundError` 或清单无法读取。

- [ ] **Step 3: 写入来源清单**

保存为 `docs/superpowers/plans/2026-10-25-sample-source-list.json`：

```json
{
  "chapters": ["00", "03"],
  "community": [],
  "reuse_existing": [
    {
      "id": "project-examples",
      "claim": "3.3 V, Vf 2.0 V, 5 mA gives 260 ohm, fitted as 270 ohm. The BluePill onboard LED on PC13 is common-anode and lights when the pin is low.",
      "do_not_copy": "Do not treat that resistor arithmetic or the board LED polarity as a DS5319 cell."
    }
  ],
  "absorb": [
    {
      "id": "rm0008-boot",
      "chapters": ["00"],
      "title_zh": "RM0008 Rev 21 启动配置",
      "title_en": "RM0008 Rev 21 boot configuration",
      "authority_zh": "ST 官方参考手册",
      "authority_en": "ST reference manual",
      "url": "https://www.st.com/resource/en/reference_manual/rm0008-stm32f101xx-stm32f102xx-stm32f103xx-advanced-arm-based-32-bit-mcus-stmicroelectronics.pdf",
      "snapshot": "RM0008 Rev 21, February 2021, section 3.4 Table 9",
      "license": "ST document terms (link and restated facts only; the manual is not redistributed)",
      "license_class": "ST-facts-restated",
      "section": "3.4",
      "do_not_copy": "Do not paste section 3.4 or Table 9. Do not commit the PDF.",
      "points": [
        "BOOT0=0 aliases main Flash at 0x00000000; the Flash array remains at 0x08000000",
        "BOOT1=0 and BOOT0=1 alias system memory; STM32F103C8 uses 0x1FFFF000, not the connectivity-line address 0x1FFFB000",
        "BOOT pins latch on the 4th rising edge of SYSCLK and are sampled again when leaving Standby"
      ]
    },
    {
      "id": "rm0008-gpio",
      "chapters": ["03"],
      "title_zh": "RM0008 Rev 21 GPIO 锁定与 SWD 脚",
      "title_en": "RM0008 Rev 21 GPIO lock and SWD pins",
      "authority_zh": "ST 官方参考手册",
      "authority_en": "ST reference manual",
      "url": "https://www.st.com/resource/en/reference_manual/rm0008-stm32f101xx-stm32f102xx-stm32f103xx-advanced-arm-based-32-bit-mcus-stmicroelectronics.pdf",
      "snapshot": "RM0008 Rev 21, February 2021, sections 9.2.7 and 9.3.5 Table 36",
      "license": "ST document terms (link and restated facts only; the manual is not redistributed)",
      "license_class": "ST-facts-restated",
      "section": "9.2.7",
      "do_not_copy": "Do not paste the LCKR sequence or Table 36. F4 AFR is outside this manual.",
      "points": [
        "GPIOx_LCKR offset 0x18; write 1, write 0, write 1, then read; a confirming read of 1 means the lock holds until reset",
        "Any error in that sequence aborts the lock",
        "SWDIO is PA13 and SWCLK is PA14"
      ]
    },
    {
      "id": "ds5319-gpio",
      "chapters": ["03"],
      "title_zh": "DS5319 Rev 20 LQFP48 的 PA0 与 PC13",
      "title_en": "DS5319 Rev 20 LQFP48 pins PA0 and PC13",
      "authority_zh": "ST 官方数据手册",
      "authority_en": "ST datasheet",
      "url": "https://www.st.com/resource/en/datasheet/stm32f103c8.pdf",
      "snapshot": "DS5319 Rev 20, July 2025, Table 5, Figure 8, note 5",
      "license": "ST document terms (link and restated facts only; the manual is not redistributed)",
      "license_class": "ST-facts-restated",
      "section": "note 5",
      "do_not_copy": "Do not paste note 5, Table 5, or Figure 8. Do not trace the pinout drawing.",
      "points": [
        "LQFP48 pin 2 is PC13-TAMPER-RTC and pin 10 is PA0-WKUP",
        "PC13, PC14, and PC15 sink at most 3 mA, must not source an LED, and stay at or below 2 MHz into 30 pF"
      ]
    }
  ]
}
```

`accessed` 不写进这份清单。Task 4 写 manifest 时用当天 UTC 日期，中英相同。

- [ ] **Step 4: 运行测试，确认通过**

Run: `python3 stm32-book/tests/test_sample_sources.py -v`

Expected: OK。

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/plans/2026-10-25-sample-source-list.json stm32-book/tests/test_sample_sources.py
git commit -m "docs: 列上 00 与 03 的可吸收来源"
```

### Task 3: Static key figures

**Files:**
- Create: `tools/gen_sample_figures.py`
- Create: `assets/diagrams/sample-00-boot-state.svg`
- Create: `assets/diagrams/sample-03-gpio-led.svg`
- Modify: `assets/README.md`（第四节「静态框图」表，加两行）
- Test: `stm32-book/tests/test_sample_chapters.py`

**Interfaces:**
- Consumes: Task 2 清单里的订货号、脚位、地址和电流界限。
- Produces: 两张不含 `<animate`、`@keyframes`、`animation:` 的 SVG。`sample-00-boot-state.svg` 的文本含 `STM32F103C8T6`、`BOOT0`、`BOOT1`、`SWDIO`、`SWCLK`、`0x08000000`、`0x00000000`、`0x1FFFF000`、`SYSCLK`。`sample-03-gpio-led.svg` 的文本含 `STM32F103C8T6`、`LQFP48`、`PA0`、`PC13`、`270`、`260`、`3.3`、`3 mA`、`2 MHz`、`30 pF`、`LCKR`、`0x18`。

- [ ] **Step 1: 写会失败的主图测试**

保存为 `stm32-book/tests/test_sample_chapters.py`：

```python
#!/usr/bin/env python3
"""Checks for the two thickened sample chapters and their static figures."""

from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIAGRAMS = ROOT / "assets" / "diagrams"
BOOT = DIAGRAMS / "sample-00-boot-state.svg"
GPIO = DIAGRAMS / "sample-03-gpio-led.svg"


class SampleFigureTests(unittest.TestCase):
    def test_key_figures_are_static_and_under_60_kib(self) -> None:
        for path, tokens in (
            (BOOT, ("STM32F103C8T6", "BOOT0", "BOOT1", "SWDIO", "SWCLK", "0x08000000", "0x00000000", "0x1FFFF000", "SYSCLK")),
            (GPIO, ("STM32F103C8T6", "LQFP48", "PA0", "PC13", "270", "260", "3.3", "3 mA", "2 MHz", "30 pF", "LCKR", "0x18")),
        ):
            raw = path.read_text(encoding="utf-8")
            self.assertLess(path.stat().st_size, 60 * 1024, path.name)
            for banned in ("<animate", "@keyframes", "animation:"):
                self.assertNotIn(banned, raw)
            for token in tokens:
                self.assertIn(token, raw)
            self.assertIn("自绘", raw)
            self.assertNotIn("实拍", raw)
            self.assertNotIn("矢量动画", raw)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试，确认它因为文件不存在而失败**

Run: `python3 stm32-book/tests/test_sample_chapters.py -v`

Expected: FAIL，`sample-00-boot-state.svg` 不存在。

- [ ] **Step 3: 写入生成脚本并生成 SVG**

保存为 `tools/gen_sample_figures.py`：

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Static key figures for the two sample chapters. No CSS animation and no SMIL."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from svgkit import Svg, T

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _credit(canvas: Svg, note: str) -> None:
    canvas.line(24, canvas.h - 36, canvas.w - 24, canvas.h - 36, stroke=T.GRID, sw=1)
    canvas.text(24, canvas.h - 16, note, size=11, fill=T.MUTED)
    canvas.text(canvas.w - 24, canvas.h - 16, "自绘 · 静态 · CC BY 4.0", size=11, fill=T.DIM, anchor="end")


def boot_state() -> Svg:
    canvas = Svg(
        960,
        620,
        "BOOT0=0 取到刚烧入的闪存；BOOT0=1 取到系统存储器",
        "STM32F103C8T6 · RM0008 Rev 21 §3.4 Table 9",
    )
    canvas.header(tag="00", tag_color=T.CYAN)
    canvas.text(40, 88, "正常路径  BOOT1=x  BOOT0=0", size=16, fill=T.GREEN, weight="700")
    steps = [
        (40, "main.c", "源文件"),
        (230, ".elf", "STM32F103C8Tx_FLASH.ld"),
        (460, "SWDIO / SWCLK", "写入 0x08000000"),
        (700, "0x00000000", "别名到主闪存"),
    ]
    for left, title, sub in steps:
        canvas.rect(left, 108, 180, 78, fill=T.PANEL, stroke=T.GREEN, rx=8)
        canvas.text(left + 12, 140, title, size=14, fill=T.TEXT, weight="700")
        canvas.text(left + 12, 164, sub, size=11, fill=T.MUTED)
    canvas.text(40, 214, "第 4 个 SYSCLK 上升沿锁存 BOOT 脚，然后 CPU 读 0x00000000 与 0x00000004", size=14, fill=T.TEXT)
    canvas.text(40, 268, "失败路径  BOOT1=0  BOOT0=1", size=16, fill=T.RED, weight="700")
    canvas.rect(40, 284, 880, 130, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(56, 316, "烧录仍然写在 0x08000000，程序还在闪存里", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 344, "CPU 从 0x00000000 取到的是系统存储器别名，不是这颗闪存", size=14, fill=T.AMBER)
    canvas.text(56, 370, "STM32F103C8T6 的系统存储器在 0x1FFFF000", size=14, fill=T.TEXT)
    canvas.text(56, 396, "互联型 0x1FFFB000 与 XL 密度 Bank2 的 0x08080000 对这颗料作废", size=13, fill=T.MUTED)
    canvas.rect(40, 434, 880, 110, fill=T.BG2, stroke=T.STROKE, rx=8)
    canvas.text(56, 466, "信号名", size=14, fill=T.CYAN, weight="700")
    canvas.text(56, 492, "SWDIO = PA13     SWCLK = PA14     BOOT0     BOOT1", size=15, fill=T.TEXT)
    canvas.text(56, 518, "退出 Standby 时 BOOT 脚会再采样一次", size=13, fill=T.MUTED)
    _credit(canvas, "自绘。地址与启动行来自 RM0008 Rev 21 第 3.4 节表 9。")
    return canvas


def gpio_led() -> Svg:
    canvas = Svg(
        960,
        660,
        "PA0 推挽可以点灯；PC13 不能当电流源",
        "STM32F103C8T6 LQFP48 · DS5319 Rev 20 Figure 8 / Table 5 / note 5",
    )
    canvas.header(tag="03", tag_color=T.AMBER)
    canvas.rect(40, 86, 420, 250, fill=T.PANEL, stroke=T.CYAN, rx=10)
    canvas.text(56, 116, "STM32F103C8T6  LQFP48", size=16, fill=T.TEXT, weight="700")
    canvas.rect(56, 140, 150, 40, fill=T.BG2, stroke=T.GREEN, rx=6)
    canvas.text(68, 166, "10   PA0-WKUP", size=14, fill=T.GREEN, weight="700")
    canvas.rect(56, 196, 190, 40, fill=T.BG2, stroke=T.RED, rx=6)
    canvas.text(68, 222, "2   PC13-TAMPER-RTC", size=14, fill=T.RED, weight="700")
    canvas.text(56, 270, "PA0 推挽写 1：电流从脚流出", size=13, fill=T.GREEN)
    canvas.text(56, 296, "PC13 走电源开关，禁止作电流源", size=13, fill=T.RED)
    canvas.text(460, 108, "正常路径", size=16, fill=T.GREEN, weight="700")
    canvas.rect(460, 124, 460, 160, fill=T.PANEL, stroke=T.GREEN, rx=10)
    canvas.text(476, 154, "PA0 第 10 脚", size=14, fill=T.TEXT, weight="700")
    canvas.text(476, 180, "3.3 V → 推挽 PMOS → 270 Ω → LED → GND", size=13, fill=T.CYAN)
    canvas.text(476, 206, "R = (3.3 − 2.0) / 0.005 = 260 Ω，取 270 Ω", size=13, fill=T.TEXT)
    canvas.text(476, 232, "高 500 ms，低 500 ms，合起来 1 Hz", size=13, fill=T.MUTED)
    canvas.text(476, 256, "周期来自 HAL_Delay(500)，不是速度位", size=12, fill=T.MUTED)
    canvas.text(460, 316, "失败路径", size=16, fill=T.RED, weight="700")
    canvas.rect(460, 332, 460, 150, fill=T.PANEL, stroke=T.RED, rx=10)
    canvas.text(476, 362, "PC13 第 2 脚", size=14, fill=T.TEXT, weight="700")
    canvas.text(476, 388, "把 PA0「写 1 点灯」原样搬过来", size=13, fill=T.AMBER)
    canvas.text(476, 414, "灌电流上限 3 mA，不能作电流源", size=13, fill=T.RED)
    canvas.text(476, 440, "速度 ≤ 2 MHz，负载 ≤ 30 pF", size=13, fill=T.TEXT)
    canvas.text(476, 464, "25 mA / 50 MHz 对 PC13–PC15 作废", size=12, fill=T.MUTED)
    canvas.rect(40, 360, 400, 200, fill=T.BG2, stroke=T.VIOLET, rx=10)
    canvas.text(56, 390, "GPIOx_LCKR  偏移 0x18", size=14, fill=T.VIOLET, weight="700")
    canvas.text(56, 420, "LCK[15:0] 在序列中保持不变", size=13, fill=T.TEXT)
    canvas.text(56, 446, "LCKK：写 1，写 0，写 1", size=13, fill=T.TEXT)
    canvas.text(56, 472, "再读，确认读回 1，锁保持到复位", size=13, fill=T.TEXT)
    canvas.text(56, 498, "错一步，锁中止，配置仍可改", size=13, fill=T.AMBER)
    canvas.text(56, 528, "RM0008 Rev 21 §9.2.7", size=12, fill=T.MUTED)
    _credit(canvas, "自绘。脚位与 3 mA / 2 MHz / 30 pF 来自 DS5319 Rev 20。")
    return canvas


def main() -> None:
    out_dir = os.path.join(ROOT, "assets", "diagrams")
    os.makedirs(out_dir, exist_ok=True)
    boot_state().save(os.path.join(out_dir, "sample-00-boot-state.svg"))
    gpio_led().save(os.path.join(out_dir, "sample-03-gpio-led.svg"))


if __name__ == "__main__":
    main()
```

Run: `python3 tools/gen_sample_figures.py`

Expected: 退出码 0。两张 SVG 出现在 `assets/diagrams/`。2026-10-25 在本仓库的 `tools/svgkit.py` 上，这两张图是 7103 字节和 8221 字节。测试只要求小于 60 KB。字节数变了，先看 `svgkit.py` 有没有变；不要为了凑字节数改画法。

在 `assets/README.md` 开头的生成命令代码块里，`python3 tools/gen_diagrams.py` 那一行下面加：

```bash
python3 tools/gen_sample_figures.py   # 第 00、03 章的静态主图
```

第四节表格现有两列（文件、内容）。在表格末尾追加这两行，不要另起第三列：

```markdown
| `sample-00-boot-state.svg` | 第 00 章静态主图：BOOT0=0 的闪存别名，以及 BOOT0=1 时 CPU 取到系统存储器。由 `tools/gen_sample_figures.py` 生成 |
| `sample-03-gpio-led.svg` | 第 03 章静态主图：PA0 经 270 Ω 点灯，PC13 不能当电流源，并画出 LCKR 序列。由 `tools/gen_sample_figures.py` 生成 |
```

- [ ] **Step 4: 运行测试和素材检查**

Run: `python3 stm32-book/tests/test_sample_chapters.py -v`

Expected: OK。

Run: `python3 tools/check_assets.py`

Expected: 退出码 0，输出含 `全部通过`。

- [ ] **Step 5: Commit**

```bash
git add tools/gen_sample_figures.py assets/diagrams/sample-00-boot-state.svg assets/diagrams/sample-03-gpio-led.svg assets/README.md stm32-book/tests/test_sample_chapters.py
git commit -m "assets: 为 00 与 03 加上可印刷的静态主图"
```

### Task 4: Thicken chapter 03 in both languages

**Files:**
- Modify: `docs/03-GPIO与LED.md`
- Modify: `docs/en/03-gpio-and-led.md`
- Modify: `stm32-book/manifest.json`（追加 `rm0008-gpio`、`ds5319-gpio`；`03-GPIO与LED.md` 的 `sources` 改为 `["rm0008", "ds5319", "rm0008-gpio", "ds5319-gpio", "project-examples"]`。这一步不追加 `rm0008-boot`）
- Modify: `stm32-book/manifest-en.json`（同一组 id 与同一组 `url` / `snapshot` / `license` / `accessed`；英文 `title`、`authority`、`scope`；`03-gpio-and-led.md` 的 `sources` 与中文数组相同）
- Modify: `stm32-book/tests/test_sample_chapters.py`
- Test: `stm32-book/tests/test_sample_chapters.py`

**Interfaces:**
- Consumes: `ds5319-gpio`、`rm0008-gpio`、`project-examples`，以及 `assets/diagrams/sample-03-gpio-led.svg`。
- Produces: 中文章在 `## 📌 学习目标` 之前出现四个新的二级标题；英文在 `## 📌 Learning goals` 之前出现四个英文标题。旧的 `## ⚠️ 常见坑与排查` 与 `## ⚠️ Pitfalls and troubleshooting` 删除。速度表里 25 mA / 50 MHz 那两行保留，但说明指向新的边界节，不把 3 mA 再写一遍。

`accessed` 用准备当天的 UTC 日期，例如 `2026-10-25` 这种 `YYYY-MM-DD`。中英 manifest 写同一天。

`rm0008-gpio` 的中文 `scope`：`第 03 章原理与边界、时序或状态、坑与出处卡。只改写 GPIOx_LCKR 偏移 0x18 的锁定序列，以及 SWDIO=PA13、SWCLK=PA14。不复制手册段落，不覆盖 F4 的 AFR。`

`rm0008-gpio` 的英文 `scope`：`Chapter 03 principle, timing, and source cards. Restates the GPIOx_LCKR lock at offset 0x18 and SWDIO=PA13, SWCLK=PA14. Does not copy manual prose and does not cover F4 AFR.`

`ds5319-gpio` 的中文 `scope`：`第 03 章原理与边界、关键插图、坑与出处卡。只改写 LQFP48 第 10 脚 PA0、第 2 脚 PC13，以及注 5 的 3 mA、2 MHz、30 pF。不复制注 5 原文，不描图 8。`

`ds5319-gpio` 的英文 `scope`：`Chapter 03 principle, key figures, and source cards. Restates LQFP48 pin 10 PA0, pin 2 PC13, and note 5: 3 mA, 2 MHz, 30 pF. Does not copy note 5 and does not trace Figure 8.`

两份 `license`、`url`、`snapshot` 都用清单里的字符串，中英相同。`title` 用清单的 `title_zh` / `title_en`，`authority` 用 `authority_zh` / `authority_en`。

- [ ] **Step 1: 把章节断言加进测试**

在 `SampleFigureTests` 同一文件里追加这个类：

```python
class SampleGpioChapterTests(unittest.TestCase):
    def test_gpio_chapters_have_four_blocks_and_the_same_numbers(self) -> None:
        zh = (ROOT / "docs" / "03-GPIO与LED.md").read_text(encoding="utf-8")
        en = (ROOT / "docs" / "en" / "03-gpio-and-led.md").read_text(encoding="utf-8")
        for heading in ("## 原理与边界", "## 关键插图", "## 时序或状态", "## 坑与出处卡"):
            self.assertEqual(1, zh.count(heading))
        for heading in ("## Principle and boundary", "## Key figures", "## Timing or state", "## Pitfalls and source cards"):
            self.assertEqual(1, en.count(heading))
        self.assertNotIn("## ⚠️ 常见坑与排查", zh)
        self.assertNotIn("## ⚠️ Pitfalls and troubleshooting", en)
        self.assertIn("## 📌 学习目标", zh)
        self.assertIn("## 📌 Learning goals", en)
        for text in (zh, en):
            for token in ("STM32F103C8T6", "LQFP48", "PA0", "PC13", "270", "260", "3.3", "3 mA", "2 MHz", "30 pF", "GPIOx_LCKR", "0x18", "PA13", "PA14", "#source-ds5319-gpio", "#source-rm0008-gpio", "#source-project-examples"):
                self.assertIn(token, text)
            self.assertIn("../assets/diagrams/sample-03-gpio-led.svg" if text is zh else "../../assets/diagrams/sample-03-gpio-led.svg", text)
        for start, end in (
            ("## 原理与边界", "## 关键插图"),
            ("## 关键插图", "## 时序或状态"),
            ("## 时序或状态", "## 坑与出处卡"),
            ("## 坑与出处卡", "## 📌 学习目标"),
        ):
            self.assertIn("#source-", zh.split(start, 1)[1].split(end, 1)[0])
        for start, end in (
            ("## Principle and boundary", "## Key figures"),
            ("## Key figures", "## Timing or state"),
            ("## Timing or state", "## Pitfalls and source cards"),
            ("## Pitfalls and source cards", "## 📌 Learning goals"),
        ):
            self.assertIn("#source-", en.split(start, 1)[1].split(end, 1)[0])
        core = zh.split("## 🧠 核心原理", 1)[1].split("## 🛠️ 硬件与接线", 1)[0]
        core_en = en.split("## 🧠 Core ideas", 1)[1].split("## 🛠️ Hardware and wiring", 1)[0]
        for block in (core, core_en):
            self.assertNotIn("260", block)
            self.assertNotIn("270", block)
            self.assertNotIn("3 mA", block)
            self.assertNotIn("3mA", block)
        self.assertNotIn("示意图", zh.split("## 关键插图", 1)[1].split("## 时序或状态", 1)[0])
        self.assertNotIn("schematic", en.split("## Key figures", 1)[1].split("## Timing or state", 1)[0].lower())
        self.assertIn("自绘", zh)
        self.assertIn("Drawn for this book", en)
        listed = json.loads((ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-sample-source-list.json").read_text(encoding="utf-8"))
        by_id = {item["id"]: item for item in listed["absorb"]}
        scopes = {
            "rm0008-gpio": (
                "第 03 章原理与边界、时序或状态、坑与出处卡。只改写 GPIOx_LCKR 偏移 0x18 的锁定序列，以及 SWDIO=PA13、SWCLK=PA14。不复制手册段落，不覆盖 F4 的 AFR。",
                "Chapter 03 principle, timing, and source cards. Restates the GPIOx_LCKR lock at offset 0x18 and SWDIO=PA13, SWCLK=PA14. Does not copy manual prose and does not cover F4 AFR.",
            ),
            "ds5319-gpio": (
                "第 03 章原理与边界、关键插图、坑与出处卡。只改写 LQFP48 第 10 脚 PA0、第 2 脚 PC13，以及注 5 的 3 mA、2 MHz、30 pF。不复制注 5 原文，不描图 8。",
                "Chapter 03 principle, key figures, and source cards. Restates LQFP48 pin 10 PA0, pin 2 PC13, and note 5: 3 mA, 2 MHz, 30 pF. Does not copy note 5 and does not trace Figure 8.",
            ),
        }
        zh_manifest = json.loads((ROOT / "stm32-book" / "manifest.json").read_text(encoding="utf-8"))
        en_manifest = json.loads((ROOT / "stm32-book" / "manifest-en.json").read_text(encoding="utf-8"))
        self.assertEqual(
            ["rm0008", "ds5319", "rm0008-gpio", "ds5319-gpio", "project-examples"],
            zh_manifest["chapter_guides"]["03-GPIO与LED.md"]["sources"],
        )
        self.assertEqual(
            ["rm0008", "ds5319", "rm0008-gpio", "ds5319-gpio", "project-examples"],
            en_manifest["chapter_guides"]["03-gpio-and-led.md"]["sources"],
        )
        for source_id, (scope_zh, scope_en) in scopes.items():
            card_zh = zh_manifest["sources"][source_id]
            card_en = en_manifest["sources"][source_id]
            for key in ("url", "snapshot", "license"):
                self.assertEqual(by_id[source_id][key], card_zh[key])
                self.assertEqual(card_zh[key], card_en[key])
            self.assertEqual(card_zh["accessed"], card_en["accessed"])
            self.assertRegex(card_zh["accessed"], r"^\d{4}-\d{2}-\d{2}$")
            self.assertEqual(by_id[source_id]["title_zh"], card_zh["title"])
            self.assertEqual(by_id[source_id]["title_en"], card_en["title"])
            self.assertEqual(by_id[source_id]["authority_zh"], card_zh["authority"])
            self.assertEqual(by_id[source_id]["authority_en"], card_en["authority"])
            self.assertEqual(scope_zh, card_zh["scope"])
            self.assertEqual(scope_en, card_en["scope"])
        baseline = json.loads(subprocess.check_output(["git", "show", "origin/main:stm32-book/manifest.json"], cwd=ROOT, text=True))
        baseline_en = json.loads(subprocess.check_output(["git", "show", "origin/main:stm32-book/manifest-en.json"], cwd=ROOT, text=True))
        for source_id, obj in baseline["sources"].items():
            self.assertEqual(obj, zh_manifest["sources"][source_id])
        for source_id, obj in baseline_en["sources"].items():
            self.assertEqual(obj, en_manifest["sources"][source_id])
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `python3 stm32-book/tests/test_sample_chapters.py SampleGpioChapterTests -v`

Expected: FAIL，中文缺少 `## 原理与边界`。

- [ ] **Step 3: 改速度表的两行说明，并删掉旧坑表**

中文 `docs/03-GPIO与LED.md` 把这两格的说明改成：

```markdown
| 输出速度（F1） | 2/10/50MHz | 越高边沿越陡。PC13、PC14、PC15 不用这一行，界限写在「原理与边界」。 |
| 单脚灌/拉电流 | 25mA（F103） | 其他脚仍用这一行。PC13、PC14、PC15 不用这一行，界限写在「原理与边界」。 |
```

英文 `docs/en/03-gpio-and-led.md`：

```markdown
| Output speed (F1) | 2/10/50 MHz | Steeper edges cost more EMI. PC13, PC14, and PC15 do not use this row; their limit is in Principle and boundary. |
| Sink or source, one pin | 25 mA (F103) | Other pins still use this row. PC13, PC14, and PC15 do not use this row; their limit is in Principle and boundary. |
```

删除从 `## ⚠️ 常见坑与排查` 到下一节 `## 🧪 动手实验` 之前的整段（含表）。英文删除从 `## ⚠️ Pitfalls and troubleshooting` 到 `## 🧪 Hands-on labs` 之前的整段。动手实验保留。

模式表、推挽/开漏对照和寄存器表留在「核心原理」。限流公式 `R = (Vcc − Vf) / I` 也留在那里。把中文例题整句

`例：3.3V、红 LED Vf=2.0V、I=5mA → R=(3.3−2.0)/0.005 = **260Ω**，取标准值 270Ω。`

换成

`具体订货号上的算例写在「原理与边界」，并标明它来自例程而不是数据手册。这里只保留公式。`

把英文例题整句

`Example: 3.3 V, red LED Vf=2.0 V, I=5 mA → R=(3.3−2.0)/0.005 = **260 Ω**. Take the standard value 270 Ω.`

换成

`The worked example for this orderable is in Principle and boundary, and it is an example-project fact rather than a datasheet cell. This section keeps only the formula.`

260 Ω、270 Ω 和 3 mA 只出现在新的四块和图注里，不再出现在「核心原理」。

- [ ] **Step 4: 在学习目标之前插入四块**

中文插在 `## 📌 学习目标` 之前：

```markdown
## 原理与边界

这一章的点灯结论只钉在订货号 STM32F103C8T6、封装 LQFP48 上。[DS5319 Rev 20](#source-ds5319-gpio) 的图 8 和表 5 把 PA0-WKUP 放在第 10 脚，把 PC13-TAMPER-RTC 放在第 2 脚。

PA0 可以做电流源。把它配成推挽、写 1，电流从 3.3 V 经脚内的 PMOS 流出，再经过电阻和发光二极管到地。例程里的算术是 `(3.3 − 2.0) / 0.005 = 260`，取标准值 270 Ω。[例程](#source-project-examples) 只支持这组输入和这个商，不支持把它说成数据手册里的推荐电流。

PC13、PC14、PC15 走电源开关。同一份数据手册的注 5 给出的界限是：灌电流不超过 3 mA，速度不超过 2 MHz，负载不超过 30 pF，而且不能拿这三只脚去当电流源点灯。BluePill 板载灯接在 PC13 上还能亮，是因为灯的阳极在 3.3 V，脚只负责灌电流，写 0 才亮。把 PA0「写 1 点亮」的电路原样搬到 PC13，这一行作废。

上面速度表里的 25 mA 和 50 MHz 对这三只脚作废。换封装或换订货号时，第 2 脚和第 10 脚整行重写。F4 每个脚自己的 AFR 不在 RM0008 里；本书旧句「F1 用 AFIO 的 MAPR」只在 F1 上成立，换到 F4 时那一行作废。

## 关键插图

<p align="center">
  <img src="../assets/diagrams/sample-03-gpio-led.svg" width="760" alt="STM32F103C8T6 上 PA0 经 270 欧点亮外接灯，PC13 不能输出这股电流">
  <br><sub>▲ 自绘。STM32F103C8T6，LQFP48：PA0 是第 10 脚，PC13 是第 2 脚。正常路径是 3.3 V 经推挽和 270 Ω 到 LED；260 Ω 是 (3.3 − 2.0) / 0.005 的商。失败路径是把这条路搬到 PC13：注 5 只允许 3 mA 灌电流，速度不超过 2 MHz，负载不超过 30 pF。锁序列见 GPIOx_LCKR，偏移 0x18。脚位与电流来自 [DS5319 Rev 20](#source-ds5319-gpio) 表 5、图 8、注 5；锁与 SWD 来自 [RM0008 Rev 21](#source-rm0008-gpio) 第 9.2.7 节和第 9.3.5 节表 36。</sub>
</p>

章首那张 `gpio-blink.svg` 仍是动画辅图。这一节的主图不播放也能指出失败发生在 PC13 那段。

## 时序或状态

1 Hz 的高低电平不是 GPIO 速度位算出来的。高 500 ms、低 500 ms 来自 [gpio-blink 例程](#source-project-examples) 的 `HAL_Delay(500)`。速度位写成 50 MHz 不会把 PC13 变成可以点灯的脚。

| 步骤 | LCK[15:0] | LCKK | 读回 | 结果 |
| --- | --- | --- | --- | --- |
| 1 | 保持要锁的脚 | 写 1 | — | 序列开始 |
| 2 | 同上，不能改 | 写 0 | — | 序列继续 |
| 3 | 同上，不能改 | 写 1 | — | 序列写完 |
| 4 | 同上 | — | 再读，确认读回 1 | 锁住，直到复位 |
| 失败 | 中途改了掩码，或少了一次写 | — | 确认读回不是 1 | 锁中止，配置仍可改 |

寄存器是 `GPIOx_LCKR`，偏移 `0x18`。出处是 [RM0008 Rev 21 第 9.2.7 节](#source-rm0008-gpio)。

## 坑与出处卡

| 现象 | 原因 | 处理 | 出处 | 该来源允许支持的主张 |
| --- | --- | --- | --- | --- |
| 外接灯接在 PC13 上，写 1 也不按 PA0 的方式亮 | PC13 不能当电流源 | 外接灯改到 PA0，串 270 Ω | [DS5319 Rev 20 注 5](#source-ds5319-gpio) | LQFP48 第 2 脚是 PC13；PC13–PC15 灌电流不超过 3 mA，速度不超过 2 MHz，负载不超过 30 pF |
| 板载灯写 1 反而不亮 | 板载灯共阳，PC13 灌电流才亮 | 写 0 点亮 | [gpio-blink 例程](#source-project-examples) | 只支持这块 BluePill 的接法，不支持 3 mA 这个手册数字 |
| 写了 ODR，脚上没有电平 | 口时钟还没开，配置寄存器还没进外设 | 先打开对应 GPIO 口的时钟，再写 CRL/CRH | [RM0008 GPIO](#source-rm0008-gpio) | 只支持「先给这个口时钟，再写第 9 章的配置寄存器」 |
| LCKR 写了三次，之后仍能改配置 | 序列出错，或确认读回不是 1 | 掩码保持不变，写 1、写 0、写 1，再读到 1 | [RM0008 第 9.2.7 节](#source-rm0008-gpio) | 锁成立后保持到复位；错一步则锁中止 |
| 烧完就再也连不上 | PA13/PA14 被配成普通 GPIO | 把 SWD 留在 PA13 与 PA14 | [RM0008 表 36](#source-rm0008-gpio) | SWDIO 是 PA13，SWCLK 是 PA14 |

旧表里的按键抖动不放进这张卡：10 ms 到 20 ms 的消抖没有钉在 RM0008 或 DS5319 上。动手实验可以继续做消抖，不把它写成手册数字。

```

英文插在 `## 📌 Learning goals` 之前。图的路径用 `../../assets/diagrams/sample-03-gpio-led.svg`。正文用下面这一份，数字和寄存器名与中文相同：

```markdown
## Principle and boundary

The LED conclusion of this chapter holds for orderable STM32F103C8T6 in LQFP48. [DS5319 Rev 20](#source-ds5319-gpio) Figure 8 and Table 5 place PA0-WKUP on pin 10 and PC13-TAMPER-RTC on pin 2.

PA0 may source current. As a push-pull output written to 1, current leaves the pin from 3.3 V through the internal PMOS, then through the resistor and the LED to ground. The example arithmetic is `(3.3 − 2.0) / 0.005 = 260`, fitted as 270 Ω. The [example](#source-project-examples) supports those three inputs and that quotient. It does not support calling 270 Ω a datasheet recommendation.

PC13, PC14, and PC15 sit behind the power switch. Note 5 of the same datasheet limits them to 3 mA of sink current, 2 MHz, and 30 pF, and they must not source an LED. The BluePill onboard LED can still use PC13 because its anode is at 3.3 V and the pin only sinks; writing 0 lights it. Copying the PA0 "write 1 to light" circuit onto PC13 makes that row void.

The 25 mA and 50 MHz cells in the speed table are void for these three pins. A different package or orderable rewrites pin 2 and pin 10 as a whole row. F4 per-pin AFR is outside RM0008. The older sentence "F1 remaps through AFIO MAPR" holds on F1; on F4 that row is void.

## Key figures

<p align="center">
  <img src="../../assets/diagrams/sample-03-gpio-led.svg" width="760" alt="On STM32F103C8T6, PA0 lights an external LED through 270 ohms; PC13 must not source that current">
  <br><sub>▲ Drawn for this book. STM32F103C8T6, LQFP48: PA0 is pin 10 and PC13 is pin 2. The normal path is 3.3 V through a push-pull pin and 270 Ω into the LED; 260 Ω is the quotient (3.3 − 2.0) / 0.005. The failure path copies that circuit onto PC13: note 5 allows 3 mA sink, at most 2 MHz, into 30 pF. The lock sequence is GPIOx_LCKR at offset 0x18. Pin and current facts are [DS5319 Rev 20](#source-ds5319-gpio) Table 5, Figure 8, and note 5. The lock and SWD pins are [RM0008 Rev 21](#source-rm0008-gpio) section 9.2.7 and section 9.3.5 Table 36.</sub>
</p>

The opening `gpio-blink.svg` stays an animated side figure. This key figure still shows the failure on PC13 when the animation is not playing.

## Timing or state

The 1 Hz high and low times are not a GPIO speed-bit result. High 500 ms and low 500 ms come from the [gpio-blink example](#source-project-examples) `HAL_Delay(500)`. Writing the speed bits as 50 MHz does not turn PC13 into a pin that may source an LED.

| Step | LCK[15:0] | LCKK | Read-back | Result |
| --- | --- | --- | --- | --- |
| 1 | Hold the pins to lock | Write 1 | — | Sequence starts |
| 2 | Same mask | Write 0 | — | Sequence continues |
| 3 | Same mask | Write 1 | — | Writes are done |
| 4 | Same mask | — | Read again and see 1 | Locked until reset |
| Failure | Mask changes, or a write is skipped | — | Confirming read is not 1 | Lock aborts; the configuration can still change |

The register is `GPIOx_LCKR` at offset `0x18`. Source: [RM0008 Rev 21 section 9.2.7](#source-rm0008-gpio).

## Pitfalls and source cards

| Symptom | Cause | What to do | Source | Claim this source may support |
| --- | --- | --- | --- | --- |
| An external LED on PC13 does not behave like PA0 when the pin is written 1 | PC13 must not source the LED | Move the external LED to PA0 with 270 Ω | [DS5319 Rev 20 note 5](#source-ds5319-gpio) | LQFP48 pin 2 is PC13; PC13–PC15 sink at most 3 mA, at or below 2 MHz, into 30 pF |
| The onboard LED stays dark when PC13 is written 1 | The onboard LED is common-anode; PC13 lights it by sinking | Write 0 | [gpio-blink example](#source-project-examples) | Only the BluePill wiring. Not the 3 mA datasheet limit |
| An ODR write does nothing on the pin | The port clock is still off | Enable that GPIO port clock, then write CRL/CRH | [RM0008 GPIO](#source-rm0008-gpio) | Enable the port clock before writing the section 9 configuration registers |
| Three writes to LCKR still leave the pin editable | The sequence was broken, or the confirming read was not 1 | Keep the mask, write 1, write 0, write 1, and read 1 | [RM0008 section 9.2.7](#source-rm0008-gpio) | A finished lock holds until reset; one bad step aborts it |
| The probe never connects after a flash | PA13 and PA14 were configured as ordinary GPIO | Leave SWD on PA13 and PA14 | [RM0008 Table 36](#source-rm0008-gpio) | SWDIO is PA13 and SWCLK is PA14 |

The old debounce row stays out of this card. A 10 ms to 20 ms debounce is not pinned to RM0008 or DS5319. The lab may still debounce a button without calling that interval a manual number.
```

- [ ] **Step 5: 把两个新 id 追加进两份 manifest**

在两份 manifest 的 `sources` 对象末尾、`cmsis-640` 之后追加 `rm0008-gpio` 与 `ds5319-gpio`。`url`、`snapshot`、`license` 用 Task 2 清单里的字符串。`accessed` 用同一个 UTC 日期。中文 `title` / `authority` / `scope` 用清单的 `title_zh` 与 `authority_zh` 以及本任务写的中文 scope。英文用 `title_en`、`authority_en` 和英文 scope。

`chapter_guides` 里中文键 `03-GPIO与LED.md` 与英文键 `03-gpio-and-led.md` 的 `sources` 都改成：

```json
["rm0008", "ds5319", "rm0008-gpio", "ds5319-gpio", "project-examples"]
```

不要改 `rm0008`、`ds5319`、`project-examples` 这三个已有对象。不要在这一步追加 `rm0008-boot`；那是 Task 5 的来源。

- [ ] **Step 6: 运行测试和构建检查**

Run: `python3 stm32-book/tests/test_sample_chapters.py -v && python3 stm32-book/tests/test_sample_sources.py -v`

Expected: OK。

Run: `python3 stm32-book/build_html.py --check`

Expected: 退出码 0。

Run: `python3 stm32-book/build_html.py --lang en --check`

Expected: 退出码 0。

- [ ] **Step 7: Commit**

```bash
git add docs/03-GPIO与LED.md docs/en/03-gpio-and-led.md stm32-book/manifest.json stm32-book/manifest-en.json stm32-book/tests/test_sample_chapters.py
git commit -m "book: 加厚第 03 章的边界、主图、时序和出处"
```

### Task 5: Thicken chapter 00 in both languages

**Files:**
- Modify: `docs/00-如何学习STM32.md`
- Modify: `docs/en/00-how-to-learn-stm32.md`
- Modify: `stm32-book/manifest.json` 与 `stm32-book/manifest-en.json`（追加 `rm0008-boot`；两个 `00-` 章的 `sources` 在原数组末尾追加它）
- Modify: `stm32-book/tests/test_sample_chapters.py`
- Test: `stm32-book/tests/test_sample_chapters.py`

**Interfaces:**
- Consumes: `rm0008-boot` 的 snapshot `RM0008 Rev 21, February 2021, section 3.4 Table 9`，以及 `assets/diagrams/sample-00-boot-state.svg`。
- Produces: 四个英文和四个中文标题；旧坑表删除；关键数字在两种语言里都是 `STM32F103C8T6`、`0x08000000`、`0x00000000`、`0x00000004`、`0x1FFFF000`、`0x1FFFB000`、`0x08080000`、`BOOT0`、`BOOT1`、`SYSCLK`。

中文 scope：`第 00 章的启动状态与失败路径。只改写 RM0008 Rev 21 第 3.4 节表 9；互联型地址和 XL 密度 Bank2 在这颗 STM32F103C8T6 上作废。不复制该节原文。`

英文 scope：`Chapter 00 boot states and the failure path. Restates RM0008 Rev 21 section 3.4 Table 9. The connectivity-line address and the XL-density Bank2 row are void on STM32F103C8T6. Does not copy that section.`

这一章的「核心原理」是学习路线，不和启动表重复，保留 `## 🧠 核心原理` 与 `## 🧠 Core ideas`。

- [ ] **Step 1: 追加会失败的测试**

在 `stm32-book/tests/test_sample_chapters.py` 里追加：

```python
class SampleFoundationChapterTests(unittest.TestCase):
    def test_foundation_chapters_have_four_blocks_and_the_same_addresses(self) -> None:
        zh = (ROOT / "docs" / "00-如何学习STM32.md").read_text(encoding="utf-8")
        en = (ROOT / "docs" / "en" / "00-how-to-learn-stm32.md").read_text(encoding="utf-8")
        for heading in ("## 原理与边界", "## 关键插图", "## 时序或状态", "## 坑与出处卡"):
            self.assertEqual(1, zh.count(heading))
        for heading in ("## Principle and boundary", "## Key figures", "## Timing or state", "## Pitfalls and source cards"):
            self.assertEqual(1, en.count(heading))
        self.assertNotIn("## ⚠️ 常见坑与排查", zh)
        self.assertNotIn("## ⚠️ Pitfalls and troubleshooting", en)
        self.assertIn("## 🧠 核心原理", zh)
        self.assertIn("## 🧠 Core ideas", en)
        for text in (zh, en):
            for token in ("STM32F103C8T6", "0x08000000", "0x00000000", "0x00000004", "0x1FFFF000", "0x1FFFB000", "0x08080000", "BOOT0", "BOOT1", "SYSCLK", "#source-rm0008-boot"):
                self.assertIn(token, text)
        self.assertIn("../assets/diagrams/sample-00-boot-state.svg", zh)
        self.assertIn("../../assets/diagrams/sample-00-boot-state.svg", en)
        self.assertIn("自绘", zh.split("## 关键插图", 1)[1].split("## 时序或状态", 1)[0])
        self.assertIn("Drawn for this book", en.split("## Key figures", 1)[1].split("## Timing or state", 1)[0])
        for start, end in (
            ("## 原理与边界", "## 关键插图"),
            ("## 关键插图", "## 时序或状态"),
            ("## 时序或状态", "## 坑与出处卡"),
            ("## 坑与出处卡", "## 📌 学习目标"),
        ):
            self.assertIn("#source-", zh.split(start, 1)[1].split(end, 1)[0])
        for start, end in (
            ("## Principle and boundary", "## Key figures"),
            ("## Key figures", "## Timing or state"),
            ("## Timing or state", "## Pitfalls and source cards"),
            ("## Pitfalls and source cards", "## 📌 Learning goals"),
        ):
            self.assertIn("#source-", en.split(start, 1)[1].split(end, 1)[0])
        listed = json.loads((ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-sample-source-list.json").read_text(encoding="utf-8"))
        by_id = {item["id"]: item for item in listed["absorb"]}
        zh_manifest = json.loads((ROOT / "stm32-book" / "manifest.json").read_text(encoding="utf-8"))
        en_manifest = json.loads((ROOT / "stm32-book" / "manifest-en.json").read_text(encoding="utf-8"))
        self.assertEqual(
            ["project-guide", "rm0008", "ds5319", "rm0008-boot"],
            zh_manifest["chapter_guides"]["00-如何学习STM32.md"]["sources"],
        )
        self.assertEqual(
            ["project-guide", "rm0008", "ds5319", "rm0008-boot"],
            en_manifest["chapter_guides"]["00-how-to-learn-stm32.md"]["sources"],
        )
        card_zh = zh_manifest["sources"]["rm0008-boot"]
        card_en = en_manifest["sources"]["rm0008-boot"]
        for key in ("url", "snapshot", "license"):
            self.assertEqual(by_id["rm0008-boot"][key], card_zh[key])
            self.assertEqual(card_zh[key], card_en[key])
        self.assertEqual(card_zh["accessed"], card_en["accessed"])
        self.assertEqual(
            "第 00 章的启动状态与失败路径。只改写 RM0008 Rev 21 第 3.4 节表 9；互联型地址和 XL 密度 Bank2 在这颗 STM32F103C8T6 上作废。不复制该节原文。",
            card_zh["scope"],
        )
        self.assertEqual(
            "Chapter 00 boot states and the failure path. Restates RM0008 Rev 21 section 3.4 Table 9. The connectivity-line address and the XL-density Bank2 row are void on STM32F103C8T6. Does not copy that section.",
            card_en["scope"],
        )
        baseline = json.loads(subprocess.check_output(["git", "show", "origin/main:stm32-book/manifest.json"], cwd=ROOT, text=True))
        baseline_en = json.loads(subprocess.check_output(["git", "show", "origin/main:stm32-book/manifest-en.json"], cwd=ROOT, text=True))
        self.assertEqual(set(zh_manifest["sources"]) - set(baseline["sources"]), {"rm0008-boot", "rm0008-gpio", "ds5319-gpio"})
        self.assertEqual(set(en_manifest["sources"]) - set(baseline_en["sources"]), {"rm0008-boot", "rm0008-gpio", "ds5319-gpio"})
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `python3 stm32-book/tests/test_sample_chapters.py SampleFoundationChapterTests -v`

Expected: FAIL，中文缺少 `## 原理与边界`。

- [ ] **Step 3: 删除旧坑表**

中文删除 `## ⚠️ 常见坑与排查` 到 `## 🧪 动手实验` 之前的内容。英文删除 `## ⚠️ Pitfalls and troubleshooting` 到 `## 🧪 Hands-on labs` 之前的内容。学习路线、代码和实验保留。

- [ ] **Step 4: 插入四块**

中文放在 `## 📌 学习目标` 之前：

```markdown
## 原理与边界

第一块板按订货号 STM32F103C8T6 来记。启动结论来自 [RM0008 Rev 21 第 3.4 节表 9](#source-rm0008-boot)，不要拿 G0 或 H7 的启动表来填这一行。

BOOT 脚在复位之后 SYSCLK 的第 4 个上升沿锁存。退出 Standby 时会再采样一次。锁存完成之前，`main` 里再改 BOOT 脚已经晚了。CPU 接着从 `0x00000000` 取栈顶，从 `0x00000004` 取复位向量。

BOOT0=0 时，不管 BOOT1 是什么，主闪存被别名到 `0x00000000`，闪存本体仍在 `0x08000000`。刚烧进去的程序要被取到，走的是这一行。

BOOT1=0 且 BOOT0=1 时，系统存储器被别名到 `0x00000000`。STM32F103C8T6 不是互联型，系统存储器在 `0x1FFFF000`。互联型的 `0x1FFFB000` 这一行作废。BOOT1=1 且 BOOT0=1 时从内置 SRAM 启动，SRAM 本体在 `0x20000000`，它不会变成 `0x08000000` 里的那份程序。XL 密度 Bank2 的 `0x08080000` 对这颗 64 KB 的 C8 作废。

## 关键插图

<p align="center">
  <img src="../assets/diagrams/sample-00-boot-state.svg" width="760" alt="BOOT0 为 0 时 CPU 从 0x00000000 取到 0x08000000 的闪存；BOOT0 为 1 且 BOOT1 为 0 时取到系统存储器">
  <br><sub>▲ 自绘。STM32F103C8T6。正常路径经 SWDIO（PA13）和 SWCLK（PA14）把程序写入 0x08000000，BOOT0=0 时 0x00000000 别名到这块闪存。失败路径是 BOOT1=0 且 BOOT0=1：CPU 仍读 0x00000000，但取到的是 0x1FFFF000 的系统存储器，闪存里的程序还在，只是没有被取指。第 4 个 SYSCLK 上升沿锁存 BOOT 脚。出处是 [RM0008 Rev 21 第 3.4 节表 9](#source-rm0008-boot)。</sub>
</p>

章首的 `toolchain-flow.svg` 仍是工具链辅图。这一节的主图不播放也能指出失败在 BOOT0=1 那一段。

## 时序或状态

| 状态 | BOOT1 | BOOT0 | CPU 从 0x00000000 取到什么 | 在 STM32F103C8T6 上 |
| --- | --- | --- | --- | --- |
| 正常：刚烧入的程序会跑 | x | 0 | 主闪存的别名；本体仍在 0x08000000 | 成立。下一字地址是 0x00000004 |
| 失败：烧了仍停在系统存储器 | 0 | 1 | 系统存储器的别名 | 成立的本体地址是 0x1FFFF000。0x1FFFB000 作废 |
| 失败：从 SRAM 启动 | 1 | 1 | 不是闪存里的程序 | SRAM 在 0x20000000。0x08080000 作废 |

锁存点是复位后第 4 个 SYSCLK 上升沿。出处是 [RM0008 Rev 21 表 9](#source-rm0008-boot)。

## 坑与出处卡

| 现象 | 原因 | 处理 | 出处 | 该来源允许支持的主张 |
| --- | --- | --- | --- | --- |
| 程序已经写进 0x08000000，复位后跑的却不是它 | BOOT1=0 且 BOOT0=1，启动区别名到系统存储器 | 把 BOOT0 拉到 0，再复位 | [RM0008 表 9](#source-rm0008-boot) | 闪存本体仍在 0x08000000；这颗料的系统存储器是 0x1FFFF000 |
| 在 main 里才改 BOOT 脚，这一次复位已经走错 | 脚电平在第 4 个 SYSCLK 上升沿已经锁存 | 在复位之前摆好 BOOT0 与 BOOT1 | [RM0008 第 3.4 节](#source-rm0008-boot) | 锁存点是 SYSCLK 的第 4 个上升沿；退出 Standby 会再采样 |
| 把互联型或 XL 密度的启动地址抄进 C8 工程 | 0x1FFFB000 与 0x08080000 不是这颗料的行 | 系统存储器用 0x1FFFF000，闪存用 0x08000000 | [RM0008 第 3.4 节](#source-rm0008-boot) | 这两行在 STM32F103C8T6 上作废 |

```

英文放在 `## 📌 Learning goals` 之前，图路径用 `../../assets/`：

```markdown
## Principle and boundary

Record the first board as orderable STM32F103C8T6. The boot conclusion is [RM0008 Rev 21 section 3.4 Table 9](#source-rm0008-boot). Do not fill this row from a G0 or H7 boot table.

The BOOT pins latch on the 4th rising edge of SYSCLK after reset. They are sampled again when leaving Standby. Changing them later inside `main` misses that edge. The CPU then reads the stack pointer from `0x00000000` and the reset vector from `0x00000004`.

When BOOT0=0, main Flash is aliased at `0x00000000` for either BOOT1 value, and the array itself stays at `0x08000000`. A program that was just flashed is fetched on this row.

When BOOT1=0 and BOOT0=1, system memory is aliased at `0x00000000`. STM32F103C8T6 is not a connectivity-line part, so that memory is at `0x1FFFF000`. The connectivity-line address `0x1FFFB000` is void here. When BOOT1=1 and BOOT0=1 the core boots from embedded SRAM at `0x20000000`; that does not become the image at `0x08000000`. The XL-density Bank2 address `0x08080000` is void on this 64 KB C8.

## Key figures

<p align="center">
  <img src="../../assets/diagrams/sample-00-boot-state.svg" width="760" alt="With BOOT0 at 0 the CPU fetches Flash at 0x08000000 through 0x00000000; with BOOT0 at 1 and BOOT1 at 0 it fetches system memory">
  <br><sub>▲ Drawn for this book. STM32F103C8T6. The normal path writes the image through SWDIO (PA13) and SWCLK (PA14) at 0x08000000, and BOOT0=0 aliases 0x00000000 onto that Flash. The failure path is BOOT1=0 and BOOT0=1: the CPU still reads 0x00000000, but the alias is system memory at 0x1FFFF000. The flashed image is still in Flash and is simply not fetched. The BOOT pins latch on the 4th rising edge of SYSCLK. Source: [RM0008 Rev 21 section 3.4 Table 9](#source-rm0008-boot).</sub>
</p>

The opening `toolchain-flow.svg` stays a side figure of the tools. This key figure shows the BOOT0=1 failure without playing an animation.

## Timing or state

| State | BOOT1 | BOOT0 | What the CPU fetches from 0x00000000 | On STM32F103C8T6 |
| --- | --- | --- | --- | --- |
| Normal: the flashed program runs | x | 0 | The main-Flash alias; the array remains at 0x08000000 | Holds. The next word is at 0x00000004 |
| Failure: the chip stays in system memory | 0 | 1 | The system-memory alias | The address that holds is 0x1FFFF000. 0x1FFFB000 is void |
| Failure: boot from SRAM | 1 | 1 | Not the program in Flash | SRAM is at 0x20000000. 0x08080000 is void |

The latch is the 4th rising edge of SYSCLK after reset. Source: [RM0008 Rev 21 Table 9](#source-rm0008-boot).

## Pitfalls and source cards

| Symptom | Cause | What to do | Source | Claim this source may support |
| --- | --- | --- | --- | --- |
| The image is at 0x08000000, and reset runs something else | BOOT1=0 and BOOT0=1, so the boot alias is system memory | Pull BOOT0 to 0 and reset | [RM0008 Table 9](#source-rm0008-boot) | Flash itself remains at 0x08000000; this part's system memory is 0x1FFFF000 |
| BOOT pins changed inside main, and this reset already went the wrong way | The pins latched on the 4th rising edge of SYSCLK | Set BOOT0 and BOOT1 before reset | [RM0008 section 3.4](#source-rm0008-boot) | The latch is the 4th rising edge of SYSCLK; Standby exit samples them again |
| A connectivity-line or XL-density boot address was copied into the C8 project | 0x1FFFB000 and 0x08080000 are not rows for this part | Use 0x1FFFF000 for system memory and 0x08000000 for Flash | [RM0008 section 3.4](#source-rm0008-boot) | Those two rows are void on STM32F103C8T6 |
```

- [ ] **Step 5: 追加 `rm0008-boot` 并更新第 00 章罗盘**

两份 manifest 的 `sources` 末尾追加 `rm0008-boot`。`url`、`snapshot`、`license` 与清单相同，`accessed` 与 Task 4 的日期相同。`title`、`authority`、`scope` 用本任务的中英文本。

中文键 `00-如何学习STM32.md` 与英文键 `00-how-to-learn-stm32.md` 的 `sources` 都改成：

```json
["project-guide", "rm0008", "ds5319", "rm0008-boot"]
```

不要改 `project-guide` 的旧对象。

- [ ] **Step 6: 运行测试和构建检查**

Run: `python3 -m unittest discover stm32-book/tests -v`

Expected: OK。版本断言此时仍是 1.0.7，应继续通过。

Run: `python3 stm32-book/build_html.py --check && python3 stm32-book/build_html.py --lang en --check`

Expected: 两个命令都退出码 0。

- [ ] **Step 7: Commit**

```bash
git add docs/00-如何学习STM32.md docs/en/00-how-to-learn-stm32.md stm32-book/manifest.json stm32-book/manifest-en.json stm32-book/tests/test_sample_chapters.py
git commit -m "book: 加厚第 00 章的启动边界和静态主图"
```

### Task 6: Register the sample, bump 1.1.0, keep the ledgers

**Files:**
- Modify: `CREDITS.md`
- Modify: `stm32-book/manifest.json` 与 `stm32-book/manifest-en.json` 的 `version` 与 `date`
- Modify: `stm32-book/revisions.json`
- Modify: `stm32-book/README.md`
- Modify: `stm32-book/tests/test_build.py`
- Test: `stm32-book/tests/test_build.py`

**Interfaces:**
- Consumes: Task 4 和 Task 5 已经写进 manifest 的三个新 id。
- Produces: 两份 manifest 的 `version` 都是 `1.1.0`，`date` 都是同一个 `YYYY-MM-DD`。`revisions.json` 的 `entries[0].version` 是 `1.1.0`。`test_build.py` 里原来断言 `1.0.7` 为当前版的位置改为 `1.1.0`，账本字符串保持不动。

- [ ] **Step 1: 先改版本断言，让测试失败**

在 `stm32-book/tests/test_build.py` 里只改当前版断言，不要删 `0x271`、`会上手的几笔账`、`Numbers to reconcile before changing family`、`Channels, descriptors, and fault registers` 这些账本检查。若 `main` 上的章眉断言已经不是 `第 00 章`，那是 v1.0.8，保持它的断言，不要改回去。

把当前版元组从

```python
versions = ("1.0.7", "1.0.6", "1.0.5", "1.0.4", "1.0.3", "1.0.2", "1.0.1", "1.0.0")
```

改成

```python
versions = ("1.1.0", "1.0.7", "1.0.6", "1.0.5", "1.0.4", "1.0.3", "1.0.2", "1.0.1", "1.0.0")
```

把 `history.index(">1.0.7<")` 改成 `history.index(">1.1.0<")`。

把 `test_revision_file_lists_1_0_0_through_manifest_version` 里的期望列表首项改成 `"1.1.0"`，后面仍是 `"1.0.7"` 到 `"1.0.0"`。

把 `self.assertEqual("1.0.7", manifest["version"])` 改成 `self.assertEqual("1.1.0", manifest["version"])`。

把两处 `self.assertIn("<strong>v1.0.7</strong>", html)` 改成 `self.assertIn("<strong>v1.1.0</strong>", html)`。

- [ ] **Step 2: 运行版本测试，确认失败**

Run: `python3 stm32-book/tests/test_build.py BookBuildTests.test_revision_file_lists_1_0_0_through_manifest_version -v`

Expected: FAIL，修订列表的首项仍是 `1.0.7`。

- [ ] **Step 3: 写 1.1.0**

取日期：

```bash
date -u +%Y-%m-%d
```

把打印出的日期记为 `SAMPLE_DATE`，写入下面三处，中英相同。

两份 manifest 的 `version` 改为 `1.1.0`，`date` 改为 `SAMPLE_DATE`。

在 `stm32-book/revisions.json` 的 `entries` 数组最前面插入：

```json
{
  "version": "1.1.0",
  "date": "SAMPLE_DATE",
  "zh": [
    "第 00 章写上 STM32F103C8T6 的启动状态：BOOT0=0 时 0x00000000 别名到 0x08000000，并加了一张不播放也能读的静态图。",
    "第 03 章写上 PA0 与 PC13 的电流界限、GPIOx_LCKR 序列和出处卡，并加了一张静态主图。"
  ],
  "en": [
    "Chapter 00 records the STM32F103C8T6 boot state: with BOOT0=0, 0x00000000 aliases 0x08000000, plus a static figure that stays readable in print.",
    "Chapter 03 records the PA0 versus PC13 current limit, the GPIOx_LCKR sequence, and source cards, plus a static key figure."
  ]
}
```

把 `SAMPLE_DATE` 换成命令打印的日期。修订说明只写这两章，不写尚未加厚的章。

`stm32-book/README.md` 的当前版本句改为：

```markdown
当前版本：**v1.1.0 · SAMPLE_DATE**。中文整书和英文整书共用这一版号。GitHub Release 仍要等这次提交进入 `main` 且 Book CI 产出四份文件之后再打。
```

把 `stm32-book/README.md` 里「发布 GitHub Release」一节的前两段和第三步换成：

```markdown
版本号已经是 1.1.0。构建脚本不会自己创建 GitHub Release。不要把 rc.8（`0c24f76`）的产物标成 1.0.0，也不要把 1.0.6 的产物标成 1.0.7，也不要把 1.0.7 的产物标成 1.1.0。

这次提交进入 `main` 并且 Book CI 变绿之后，由有权限的人：
```

第三步的原文是「在该提交上打 tag `v1.0.7`」。改成「在该提交上打 tag `v1.1.0`」。本样本提交在进入 `main` 之前不打这个 tag，也不创建 Release。前面的 artifact 名称和四份文件名保持不动。

- [ ] **Step 4: 在 CREDITS.md 增加第六节，并改正静态框图的张数**

第一节表格里这一行：

`| 静态框图（6 张） | `assets/diagrams/` | **本仓库作者用代码绘制**，脚本见 `tools/gen_diagrams.py`，采用 CC BY 4.0 |`

换成：

`| 静态框图（8 张） | `assets/diagrams/` | **本仓库作者用代码绘制**，脚本见 `tools/gen_diagrams.py` 与 `tools/gen_sample_figures.py`，采用 CC BY 4.0 |`

然后在文件末尾追加：

```markdown
## 六、样本章的改写吸收（v1.1.0）

第 00 章和第 03 章用改写吸收补了四块：原理与边界、关键插图、时序或状态、坑与出处卡。吸收的是事实，用本书的句子重写，并配上自绘静态图。手册正文、官方插图和 PDF 不放进仓库。社区原文这一对样本没有吸收；GPL、LGPL 和未写许可的材料仍只留在上面的索引里。

| 作品 | 许可证 | 用在 | 链接 |
| --- | --- | --- | --- |
| RM0008 Rev 21（2021-02），第 3.4 节表 9，以及第 9.2.7 节、第 9.3.5 节表 36 | ST 文档条款；只链接并改写事实，不转载手册 | 第 00 章启动状态；第 03 章 LCKR 与 SWD 脚 | https://www.st.com/resource/en/reference_manual/rm0008-stm32f101xx-stm32f102xx-stm32f103xx-advanced-arm-based-32-bit-mcus-stmicroelectronics.pdf |
| DS5319 Rev 20（2025-07），表 5、图 8、注 5 | ST 文档条款；只链接并改写事实，不转载手册 | 第 03 章 LQFP48 的 PA0 第 10 脚、PC13 第 2 脚，以及 3 mA / 2 MHz / 30 pF | https://www.st.com/resource/en/datasheet/stm32f103c8.pdf |
```

- [ ] **Step 5: 运行整套测试和构建检查**

Run: `python3 -m unittest discover stm32-book/tests -v`

Expected: OK。

Run: `python3 stm32-book/build_html.py --check && python3 stm32-book/build_html.py --lang en --check`

Expected: 两个命令都退出码 0。构建出的 HTML 里有 `v1.1.0`，并且 `#source-rm0008-boot`、`#source-rm0008-gpio`、`#source-ds5319-gpio` 都有对应的 `id="source-..."`。

- [ ] **Step 6: Commit**

```bash
git add CREDITS.md stm32-book/manifest.json stm32-book/manifest-en.json stm32-book/revisions.json stm32-book/README.md stm32-book/tests/test_build.py
git commit -m "book: 样本章登记来源并把整书标成 1.1.0"
```

### Task 7: Scope gate, then stop

**Files:**
- 不新增文件。这一任务只核对 diff。核对失败时，只撤销越界改动，不顺手加厚别的章。

**Interfaces:**
- Consumes: Task 1 到 Task 6 的提交。
- Produces: 一份只含样本两章的 diff。用户复审之前，没有其余章节的加厚提交。

- [ ] **Step 1: 核对样本 diff 的路径**

Run:

```bash
git diff --name-only origin/main...HEAD
```

Expected: 只出现这些路径。

```text
CREDITS.md
assets/README.md
assets/diagrams/sample-00-boot-state.svg
assets/diagrams/sample-03-gpio-led.svg
docs/00-如何学习STM32.md
docs/03-GPIO与LED.md
docs/en/00-how-to-learn-stm32.md
docs/en/03-gpio-and-led.md
docs/superpowers/plans/2026-10-25-classic-encyclopedia-sample-chapters.md
docs/superpowers/plans/2026-10-25-sample-chapter-lock.json
docs/superpowers/plans/2026-10-25-sample-source-list.json
stm32-book/README.md
stm32-book/manifest-en.json
stm32-book/manifest.json
stm32-book/revisions.json
stm32-book/tests/test_build.py
stm32-book/tests/test_sample_chapters.py
stm32-book/tests/test_sample_sources.py
tools/gen_sample_figures.py
tools/scan_sample_chapters.py
```

`docs/superpowers/plans/2026-10-25-classic-encyclopedia-sample-chapters.md` 只在「先合并了本计划」的历史上出现。若样本分支从本计划提交切开，它会留在 diff 里，这是允许的。它不是章节正文。

`stm32-book/build_html.py`、`stm32-book/book/`、`stm32-book/subject-index.json`、其余 `docs/0`–`docs/28` 与 `docs/en/` 章节都不在这份列表里。

- [ ] **Step 2: 核对 v1.0.8 没有被卷进来，也没有被改回去**

Run:

```bash
git diff origin/main...HEAD -- stm32-book/build_html.py
```

Expected: 无输出。

在 `stm32-book/build_html.py` 里确认仍有 `outline=True`，以及 `chapter_kicker` 仍用文件名前两位格式化。若 `main` 已经带上 v1.0.8 的章眉或浅书签，这里的 diff 仍然必须为空：样本提交不实现那条轨道，也不把那条轨道改回去。

Run:

```bash
git diff --name-only origin/main...HEAD -- docs/01-开发环境搭建.md docs/02-芯片选型与存储器时钟.md docs/04-中断与NVIC.md docs/en/01-dev-environment.md docs/en/02-part-and-clock.md docs/en/04-interrupts-nvic.md
```

Expected: 无输出。其余未入选章节同样不出现在 Step 1 的列表里。

- [ ] **Step 3: 再跑一遍验收命令**

```bash
python3 -m unittest discover stm32-book/tests -v
python3 stm32-book/build_html.py --check
python3 stm32-book/build_html.py --lang en --check
python3 tools/check_assets.py
```

Expected: 四条命令都退出码 0。

- [ ] **Step 4: 确认没有 tag 和 Release**

Run: `git tag --points-at HEAD`

Expected: 无输出。

不要运行 `gh release create`，不要 `git tag`。

- [ ] **Step 5: 停在用户复审**

样本 PR 的说明里贴上锁定文件里的两行结论和 `rows` 表：外设章为什么是 `03`，基础章为什么是 `00`。请用户看构建出的中英 HTML 里的这两章：四块是否都在、主图是否不播放也能看出失败、出处链接是否点得开。

用户书面接受之前：

- 不为 `01`、`02`、`04`–`28` 开加厚 PR。
- 不加图目录或表目录。
- 不改显示章号，不改 PDF 书签深度。
- 不打 `v1.1.0` 的 tag，不创建 GitHub Release。

这一步没有新的提交。若 Step 1 到 Step 3 发现越界文件，撤销那些文件里的越界改动后再提交一次，提交说明写明撤回了哪一处，然后仍停在这里。

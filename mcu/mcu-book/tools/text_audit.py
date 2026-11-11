"""text_audit：全书文字质量体检（只读，不改稿）。

扫 94 章 + 6 附录，按类别报问题与样本：
1. 重复句（同一句在本章出现 ≥2 次）
2. 叠标点（，，。。：：；；！！？？…）
3. 句中残留空格（中文夹半角空格，如"地址， ownership"）
4. 中文句里混用半角标点（，后跟 ASCII 逗号句号等）
5. 空括号（）、【】、()
6. 超长句（>110 汉字，精炼候选）
7. 套话（"换句话说/也就是说/这就是为什么/值得一提的是/不难发现"）
8. 连续重复词（"的的/了了/是是"）

用法：python mcu-book/tools/text_audit.py [--top 5]
输出：每类计数 + 每类前 N 条样本（文件:行号）。
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

BOOK = Path("mcu-book/book")
DIRS = ["docs/c", "docs/build", "docs/stm32", "docs/gd32", "docs/esp32",
        "docs/rtos/freertos", "docs/rtos/rtthread", "docs/rtos/compare",
        "docs/lab", "docs/projects"]

PROTECT = re.compile(r"^```.*?^```\s*$", re.S | re.M)
# 教学脚手架区（自测答案、英文摘要）不参与"长句/重复句"判据：
# 答案区复述正文是刻意设计；英文摘要不是中文散文。
DETAILS = re.compile(r"<details>.*?</details>", re.S)
CITATION_LINE = re.compile(r"^\s*[-*]\s*\*\*\[", re.M)


def narrative(text: str) -> str:
    """只保留正文叙事：去围栏、自测答案块、参考文献链接行。"""
    text = PROTECT.sub("", text)
    text = DETAILS.sub("", text)
    return CITATION_LINE.sub("", text)


def prose_lines(text: str):
    """去围栏、表格、标题后的散文行 → (行号, 内容)。"""
    no_fence = narrative(text)
    no_fence = re.sub(r"[^\n]", lambda m: m.group(0), no_fence)
    for i, ln in enumerate(no_fence.split("\n"), 1):
        s = ln.strip()
        if not s or s.startswith("|") or s.startswith("#") or s.startswith(":::"):
            continue
        if re.fullmatch(r"[-*_]{3,}", s):
            continue
        yield i, ln


def audit(path: Path) -> dict[str, list[str]]:
    text = path.read_text(encoding="utf-8")
    out: dict[str, list[str]] = {k: [] for k in (
        "重复句", "叠标点", "中英粘连", "半角标点", "空括号", "超长句", "套话", "重复词")}

    # 1) 重复句（≥12 字的完全相同句子）
    sents = re.findall(r"[^。！？\n]{12,}?[。！？]", narrative(text))
    dup = [s for s, n in Counter(sents).items() if n >= 2]
    for s in dup[:5]:
        out["重复句"].append(f"{path.name}: {s[:50]}")

    for ln, line in prose_lines(text):
        body = re.sub(r"`[^`]*`", "", line)

        raw = re.sub(r"`[^`]*`", "码", line)
        for m in re.finditer(r"[，。：；！？]{2,}", raw):
            if m.group(0) not in ("……", "——"):
                out["叠标点"].append(f"{path.name}:{ln} …{raw[max(0,m.start()-14):m.start()+len(m.group(0))+10]}…")

        for m in re.finditer(r"[\u4e00-\u9fff][A-Za-z]{2,}|[A-Za-z]{2,}[\u4e00-\u9fff]", re.sub(r"`[^`]*`", "码", line)):
            out["中英粘连"].append(f"{path.name}:{ln} …{body[max(0,m.start()-8):m.start()+18]}…")

        for m in re.finditer(r"[\u4e00-\u9fff][,.;:?!](?![0-9A-Za-z])", body):
            out["半角标点"].append(f"{path.name}:{ln} …{body[max(0,m.start()-10):m.start()+14]}…")

        for _m in re.finditer(r"（[ \t]*）|【[ \t]*】|\（\）", line):
            out["空括号"].append(f"{path.name}:{ln}")

        plain = re.sub(r"\[[^\]]*\]\([^)]*\)", "链接", body)
        for m in re.finditer(r"[^。！？\n]{110,}", plain):
            out["超长句"].append(f"{path.name}:{ln} ({len(m.group(0))} 字) {m.group(0)[:40]}…")

        for kw in ("换句话说", "也就是说", "这就是为什么", "值得一提的是", "不难发现"):
            if kw in body:
                out["套话"].append(f"{path.name}:{ln} {kw}")

        for mm in re.finditer(r"(的的|了了|是是|在在|地地)", body):
            out["重复词"].append(f"{path.name}:{ln} {mm.group(0)}")
    return out


def main() -> int:
    top = 5
    if "--top" in sys.argv:
        top = int(sys.argv[sys.argv.index("--top") + 1])
    files = [p for d in DIRS for p in sorted(Path(d).glob("*.md")) if p.name != "index.md"]
    files += sorted(BOOK.glob("[A-F]-*.md"))

    agg: dict[str, list[str]] = {}
    for f in files:
        for k, v in audit(f).items():
            agg.setdefault(k, []).extend(v)
    for k, v in agg.items():
        print(f"\n## {k}：{len(v)} 处")
        for s in v[:top]:
            print("   ", s)
    total = sum(len(v) for v in agg.values())
    print(f"\n合计 {total} 处 / {len(files)} 个文件")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""prose_guard：文字精修的不可动清单校验 + 口癖计数。

精修只许动散文。本工具对「原文 vs 精修稿」逐章断言以下内容字节级一致：
代码围栏块、行内代码、表格行、标题行、链接/图片目标、frontmatter。
另输出 AI 口癖前后计数（破折号、一句话、记住、下一站），供批次报告。

用法：
    python mcu-book/tools/prose_guard.py 原文.md 精修稿.md
    python mcu-book/tools/prose_guard.py --batch 对照清单.tsv   # 每行: 原文<TAB>精修稿
退出码：0 全过；1 有违规。
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

MARKERS = {
    "破折号——": "——",
    "一句话": "一句话",
    "记住：": "记住：",
    "下一站": "下一站",
}

# 散文事实 token：改写代理最容易"润色"坏的数字类事实。
# 从剥离代码/表格/标题/frontmatter 后的散文面提取，多重集合必须一致。
FACT_TOKEN_PATTERNS = [
    r"0x[0-9A-Fa-f]+",                                        # 十六进制地址/值
    r"§\s?\d+(?:\.\d+)*",                                     # 手册引用 §2.13
    r"第\s?\d+(?:\.\d+)*\s?[章节部篇]",                        # 文内交叉引用 第3章
    r"\d+(?:\.\d+)?\s?(?:MHz|kHz|GHz|KiB|MiB|GiB|Mbps|kbps"
    r"|KB|MB|GB|kB|Hz|ms|μs|us|ns|mA|mV|V"
    r"|字节|比特|位|万|亿|行|页|天|年|秒|分钟|小时|次|个|条|章|节"
    r"|格|档|步|种|层|路|级)",                             # 带单位数字
    r"\b\d+\.\d+(?:\.\d+)*\b",                                # 版本号/小数 3.3.3
    r"\b\d{2,}\b",                                            # 裸数兜底（≥2 位）
]


def prose_surface(text: str) -> str:
    """剥离全部受保护区，返回纯散文面。"""
    text = re.sub(r"\A---\n.*?\n---\n", "", text, flags=re.S)
    text = re.sub(r"^```[^\n]*\n.*?^```\s*$", "", text, flags=re.S | re.M)
    lines = [
        ln
        for ln in text.splitlines()
        if not ln.lstrip().startswith("|") and not re.match(r"^#{1,6}\s", ln)
    ]
    text = "\n".join(lines)
    text = re.sub(r"`[^`\n]+`", " ", text)
    return re.sub(r"!?\[([^\]]*)\]\([^)]+\)", r"\1", text)


def fact_tokens(text: str) -> Counter[str]:
    """事实 token 多重集。token 内空白一律折叠——"64 字节"与"64字节"同义
    （排版空格增删不算事实变化，数字/单位本身的变化仍逃不掉）。"""
    # 排版空格（中文↔拉丁/数字）在 token 化前折叠：判等的对象是"事实"，
    # 不是空格策略。否则 "16槽"→"16 槽" 这类纯排版改动会伪造 bare 数字 token。
    text = re.sub(r"(?<=[\u4e00-\u9fff])\s+(?=[A-Za-z0-9])", "", text)
    text = re.sub(r"(?<=[A-Za-z0-9])\s+(?=[\u4e00-\u9fff])", "", text)
    c: Counter[str] = Counter()
    spans: list[tuple[int, int]] = []
    # 前几类是"带语义的完整 token"；裸数是兜底，必须跳过已被完整 token 覆盖的数字
    for pat in FACT_TOKEN_PATTERNS[:-1]:
        for m in re.finditer(pat, text):
            spans.append((m.start(), m.end()))
            c[re.sub(r"\s+", "", m.group(0))] += 1
    for m in re.finditer(FACT_TOKEN_PATTERNS[-1], text):
        if any(s <= m.start() and m.end() <= e for s, e in spans):
            continue
        c[re.sub(r"\s+", "", m.group(0))] += 1
    return c


@dataclass
class ProtectedSet:
    """一章里不许动的字节段。"""

    fenced_code: list[str] = field(default_factory=list)
    inline_code: list[str] = field(default_factory=list)
    tables: list[str] = field(default_factory=list)
    headings: list[str] = field(default_factory=list)
    link_targets: list[str] = field(default_factory=list)
    frontmatter: str = ""


def extract_protected(text: str) -> ProtectedSet:
    ps = ProtectedSet()
    # frontmatter（--- 包裹的头部）
    fm = re.match(r"\A---\n.*?\n---\n", text, re.S)
    if fm:
        ps.frontmatter = fm.group(0)
    # 代码围栏块（含语言标记与全部内容）
    ps.fenced_code = re.findall(r"^```[^\n]*\n.*?^```\s*$", text, re.S | re.M)
    # 表格行（连续的 | 开头行逐行记录）
    ps.tables = [ln for ln in text.splitlines() if ln.lstrip().startswith("|")]
    # 标题行
    ps.headings = [ln for ln in text.splitlines() if re.match(r"^#{1,6}\s", ln)]
    # 链接与图片目标
    ps.link_targets = re.findall(r"\[[^\]]*\]\(([^)]+)\)", text)
    ps.link_targets += re.findall(r'href="([^"]+)"', text)
    ps.link_targets += re.findall(r'src="([^"]+)"', text)
    # 行内代码：去掉围栏块后再提取，避免误吞块内反引号
    no_fence = re.sub(r"^```[^\n]*\n.*?^```\s*$", "", text, flags=re.S | re.M)
    ps.inline_code = re.findall(r"`([^`\n]+)`", no_fence)
    return ps


def count_markers(text: str) -> dict[str, int]:
    """口癖计数分两层：散文面（阈值考核对象）+ 受保护区（表格/代码，不修只记录）。"""
    prose = prose_surface(text)
    protected_total = {
        name: text.count(pat) - prose.count(pat) for name, pat in MARKERS.items()
    }
    return {
        name: text.count(pat) for name, pat in MARKERS.items()
    } | {f"{name}·散文": prose.count(pat) for name, pat in MARKERS.items()} | {
        f"{name}·保护": protected_total[name] for name in MARKERS
    }


def compare(orig_path: Path, new_path: Path) -> list[str]:
    """返回违规清单；空 = 全过。"""
    orig_bytes = orig_path.read_bytes()
    new_bytes = new_path.read_bytes()
    errors: list[str] = []
    # LF 纪律：read_text 的 universal newlines 会掩盖 CRLF，字节层判
    if b"\r" in new_bytes:
        errors.append("精修稿含 CR（必须纯 LF；B3 事故就有代理写 CRLF 落地）")
    orig = orig_bytes.decode("utf-8")
    new = new_bytes.decode("utf-8")
    po, pn = extract_protected(orig), extract_protected(new)

    def check(name: str, a: list[str], b: list[str]) -> None:
        if a == b:
            return
        errors.append(f"{name} 不一致：原文 {len(a)} 段 vs 精修 {len(b)} 段")
        for i, (x, y) in enumerate(zip(a, b, strict=False)):
            if x != y:
                errors.append(
                    f"  第 {i + 1} 段首处差异：\n    原: {x[:90]!r}\n    新: {y[:90]!r}"
                )
                break
        if len(a) != len(b):
            errors.append(f"  数量也变了：{len(a)} → {len(b)}")

    check("代码围栏块", po.fenced_code, pn.fenced_code)
    check("行内代码", po.inline_code, pn.inline_code)
    check("表格行", po.tables, pn.tables)
    check("标题行", po.headings, pn.headings)
    check("链接/图片目标", po.link_targets, pn.link_targets)
    if po.frontmatter != pn.frontmatter:
        errors.append("frontmatter 不一致")

    co = fact_tokens(prose_surface(orig))
    cn = fact_tokens(prose_surface(new))
    if co != cn:
        errors.append(
            "散文事实 token 不一致："
            f"原文独有 {dict((co - cn).most_common(8))}；"
            f"精修独有 {dict((cn - co).most_common(8))}"
        )

    # 阈值硬门（用户批的决定 3）：散文面 —— 每章 ≤ 2，超了算违规
    prose_dashes = prose_surface(new).count("——")
    if prose_dashes > 2:
        errors.append(f"散文面破折号超标：{prose_dashes} 处（阈值 ≤ 2）")
    return errors



def _subseq(small: list[str], big: list[str]) -> bool:
    it = iter(big)
    return all(x in it for x in small)


def compare_additive(orig_path: Path, new_path: Path) -> list[str]:
    """内容增补轮的判据（解释性增写，不是逐字润色）。

    与 compare() 的区别：允许**新增**散文与行内代码（讲解新概念时必然要引新符号），
    但仍禁止改/删既有受保护内容、禁止发明新事实值：

    1. 围栏代码块：与原文逐字节一致
    2. 表格行 / 链接目标 / 标题：原文序列必须**保序出现在新文件里**（不许改写/删除）
    3. 行内代码：原文序列保序出现（新增允许）
    4. 事实 token：新出现的 token 必须已存在于原文**全文**（含表格/代码）——
       即可以"把表里的数字讲进正文"，不许出现原文没有的数值
    5. 散文破折号：仍受每章 ≤2 限制
    """
    errors: list[str] = []
    orig_bytes, new_bytes = orig_path.read_bytes(), new_path.read_bytes()
    if b"\r" in new_bytes:
        errors.append("精修稿含 CR（必须纯 LF）")
    orig, new = orig_bytes.decode("utf-8"), new_bytes.decode("utf-8")
    po, pn = extract_protected(orig), extract_protected(new)
    if po.fenced_code != pn.fenced_code:
        errors.append("围栏代码块被改动")
    for name, a, b in (
        ("表格行", po.tables, pn.tables),
        ("链接目标", po.link_targets, pn.link_targets),
        ("标题", po.headings, pn.headings),
        ("行内代码（原文保序）", po.inline_code, pn.inline_code),
    ):
        if not _subseq(a, b):
            errors.append(f"{name}：原文序列未能保序保留（被改写或删除）")
    if po.frontmatter != pn.frontmatter:
        errors.append("frontmatter 不一致")
    full = fact_tokens(orig)
    invented = fact_tokens(prose_surface(new)) - full
    if invented:
        errors.append(f"出现原文没有的事实值：{dict(invented.most_common(5))}")
    pd = prose_surface(new).count("——")
    if pd > 2:
        errors.append(f"散文面破折号 {pd} 处（上限 2）")
    return errors

def main() -> int:
    argv = sys.argv[1:]
    if not argv:
        print(__doc__)
        return 2
    additive = False
    if argv and argv[0] == "--additions":
        additive = True
        argv = argv[1:]
    if argv and argv[0] == "--single":
        # 新章起草门：没有原文可对照，对单文件做绝对计数。
        # 阈值 = 成书逐章预算（10-26-prose-polish 用户批）：—— 散文面 ≤2/章，
        # 一句话/记住：散文本体 0。::: 容器标签（::: tip 一句话记住）不是散文，
        # 计数前先剥掉；<details> 答案区算散文，沿用 prose_surface 定义。
        path = Path(argv[1])
        raw = path.read_text(encoding="utf-8")
        stripped = "\n".join(
            ln for ln in raw.splitlines() if not ln.lstrip().startswith(":::")
        )
        counts = count_markers(stripped)
        cols = ["破折号——·散文", "一句话·散文", "记住：·散文", "下一站·散文"]
        budget = {"破折号——·散文": 2, "一句话·散文": 0, "记住：·散文": 0}
        print(f"{path.name}: " + "  ".join(f"{k}={counts.get(k, 0)}" for k in cols))
        bad = {k: (counts.get(k, 0), lim) for k, lim in budget.items() if counts.get(k, 0) > lim}
        for k, (n, lim) in bad.items():
            print(f"  ✗ {k} {n} 处 > 预算 {lim}")
        if bad:
            return 1
        print("  ✓ 口癖预算内")
        return 0
    pairs: list[tuple[Path, Path]] = []
    if argv[0] == "--batch":
        for line in Path(argv[1]).read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            a, b = line.split("\t")
            pairs.append((Path(a), Path(b)))
    else:
        pairs.append((Path(argv[0]), Path(argv[1])))

    total_errors = 0
    print(f"{'文件':<46} {'——散文':>10} {'——保护':>10} {'一句话':>8} {'记住：':>8} {'下一站':>8}")
    for orig_path, new_path in pairs:
        errors = compare_additive(orig_path, new_path) if additive else compare(orig_path, new_path)
        total_errors += len(errors)
        co = count_markers(orig_path.read_text(encoding="utf-8"))
        cn = count_markers(new_path.read_text(encoding="utf-8"))
        name = f"{orig_path.name}"
        cols = ["破折号——·散文", "破折号——·保护", "一句话", "记住：", "下一站"]
        delta = "  ".join(f"{co[k]:>3}→{cn[k]:<3}" for k in cols)
        status = "✓" if not errors else f"✗ {len(errors)} 违规"
        print(f"{name:<46} {delta} {status}")
        for e in errors:
            print(f"  {e}")
    if total_errors:
        print(f"\n不可动清单违规 {total_errors} 处")
        return 1
    print("\n不可动清单：全部一致")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

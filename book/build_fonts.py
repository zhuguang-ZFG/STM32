#!/usr/bin/env python3
"""生成随书分发的印刷字体子集。

为什么必须自己出一套：印刷/电子书都要真字体嵌入；靠“机器上装了雅黑”
永远得不到可复现的产物。只随仓库分发许可允许分发的字体（SIL OFL），
按书本实际用字 + 保险集出子集，并把来源、许可、参数写进 provenance.json。

用法：
  python book/build_fonts.py
  python book/build_fonts.py --out-dir .temp/fonts   # 原型
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = Path(__file__).resolve().parent.parent
FONT_DIR = ROOT / "book" / "print" / "fonts"

# 源字体只用于本机重建；产物（woff2）才是随仓库分发的部分。
SOURCES = {
    "Noto Serif SC": Path("C:/Windows/Fonts/NotoSerifSC-VF.ttf"),
    "Noto Sans SC": Path("C:/Windows/Fonts/NotoSansSC-VF.ttf"),
    "Cascadia Mono": Path("C:/Windows/Fonts/CascadiaMono.ttf"),
}

INSURANCE = (
    "".join(chr(c) for c in range(0x20, 0x7F))
    + "　、。〃々〈〉《》「」『』【】〔〕〖〗！＂＃％＆＇（）＊＋，－．／０１２３４５６７８９：；＜＝＞？＠［］＿｛｜｝～"
    + "←→↑↓↔⇒⇐⇔±×÷≤≥≠≈∞°℃§¶†‡•…‰′″‹›«»—–‒−─│┌┐└┘├┤┬┴┼╔╗╚╝╭╮╯╰■□●○◆◇★☆✓✔✗✘⚠ℹ"
    + "①②③④⑤⑥⑦⑧⑨⑩⑴⑵⑶⑷⑸⒈⒉⒊"
    + "αβγδεζηθικλμνξπρστυφχψωΑΒΓΔΕΖΗΘΙΚΛΜΝΞΠΡΣΤΥΦΧΨΩ"
)

# 已有符号字体子集不重建（源字体不在本机），但参与覆盖判定。
EXISTING = ("symbols-regular.woff2", "math-regular.woff2", "emoji-regular.woff2")


def collect_chars() -> set[str]:
    chars: set[str] = set()
    roots = [ROOT / "docs", ROOT / "book"]
    for root in roots:
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in (".md", ".svg", ".json", ".py", ".css"):
                continue
            if "dist" in path.parts or "fonts" in path.parts or "__pycache__" in path.parts:
                continue
            chars.update(path.read_text(encoding="utf-8", errors="ignore"))
    chars -= {"\n", "\r", "\t"}
    return chars


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build(source: Path, out: Path, chars: set[str], axes: dict[str, float] | None) -> dict:
    font = TTFont(source)
    if axes:
        font = instancer.instantiateVariableFont(
            font, axes, inplace=False, updateFontNames=True)
    options = subset.Options()
    options.layout_features = ["*"]
    # fontTools 的桩把 name_IDs 声明成 list，运行时 "*" 表示「全部」。
    options.name_IDs = "*"  # pyright: ignore[reportAttributeAccessIssue]
    options.notdef_outline = True
    options.recalc_bounds = True
    options.desubroutinize = False
    # 带 hinting 的 TrueType 子集在 Chromium 打印里会变成 Type3 位图。
    options.drop_tables += ["prep", "fpgm", "cvt ", "VDMX", "gasp", "hdmx", "LTSH"]
    subsetter = subset.Subsetter(options=options)
    subsetter.populate(text="".join(sorted(chars | set(INSURANCE))))
    subsetter.subset(font)
    out.parent.mkdir(parents=True, exist_ok=True)
    font.flavor = "woff2"
    font.save(out)
    return {
        "output": str(out.relative_to(ROOT)),
        "bytes": out.stat().st_size,
        "cmap": len(font.getBestCmap() or {}),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=FONT_DIR)
    args = parser.parse_args()
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    chars = collect_chars()
    if not chars:
        raise SystemExit("no source characters found")

    jobs: tuple[tuple[str, dict[str, float], str], ...] = (
        ("Noto Serif SC", {"wght": 400.0}, "serif-regular.woff2"),
        ("Noto Serif SC", {"wght": 700.0}, "serif-bold.woff2"),
        ("Noto Sans SC", {"wght": 400.0}, "sans-regular.woff2"),
        ("Noto Sans SC", {"wght": 700.0}, "sans-bold.woff2"),
        ("Cascadia Mono", {"wght": 400.0}, "mono-regular.woff2"),
        ("Cascadia Mono", {"wght": 700.0}, "mono-bold.woff2"),
    )
    records = []
    for family, axes, name in jobs:
        source = SOURCES[family]
        if not source.is_file():
            raise SystemExit(f"source font missing: {source}")
        result = build(source, out_dir / name, chars, axes)
        records.append({
            "family": family,
            "axes": ",".join(f"{k}={v}" for k, v in axes.items()),
            "source": str(source),
            "sourceSha256": sha256(source),
            **result,
        })
        print(f"built {name}: {result['bytes'] / 1024:.0f} KB")

    covered: set[int] = set()
    for path in out_dir.glob("*.woff2"):
        covered |= set(TTFont(path).getBestCmap() or {})
    missing = sorted(ch for ch in chars if ord(ch) not in covered)
    if missing:
        raise SystemExit(
            "font subsets do not cover: "
            + ", ".join(f"U+{ord(ch):04X} {ch!r}" for ch in missing[:20]))

    # 页眉/页码由 PyMuPDF 后处理写入，必须给它一份 TTF（woff2 不被 MuPDF 接受）。
    head = TTFont(out_dir / "sans-regular.woff2")
    head.flavor = None
    for rec in head["name"].names:
        if rec.nameID in (1, 4, 6):
            # 桩写的是 bytes，运行时对 nameID 1/4/6 直接给 str 即可（内部编码）。
            rec.string = "NotoSansSC"  # pyright: ignore[reportAttributeAccessIssue]
    head.save(out_dir / "head-regular.ttf")

    provenance = {
        "generated": date.today().isoformat(),
        "generator": "book/build_fonts.py",
        "license": "SIL Open Font License 1.1（Noto / Cascadia；OFL.txt 同目录）",
        "chars": len(chars),
        "insurance": "ASCII + 常用中英标点 + 框线/箭头/数学符号",
        "fonts": records,
        "reused": list(EXISTING),
        "header": "head-regular.ttf（由 sans-regular.woff2 转出，供 print_pdf.py 盖页眉页码）",
    }
    (out_dir / "provenance.json").write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"covered {len(chars)} chars; wrote {out_dir / 'provenance.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

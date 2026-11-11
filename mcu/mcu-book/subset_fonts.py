"""字体子集与实例化：给印前 PDF / EPUB 用的可嵌入字体。

为什么必须自己出一套：
  1. 印刷/电子书都要**真字体嵌入**（现在那份 A4 PDF 的正文是 Type3 位图字形，
     既不能检索也不能印好）；靠"机器上装了雅黑"永远得不到可复现的产物。
  2. 只随仓库分发**许可允许分发**的字体（本脚本只接受 SIL OFL / 同一类自由许可），
     并把来源、许可、参数、字符覆盖写进 provenance.json——书里用了别人的字，
     这件事必须能被查。
  3. 全量 CJK 字体一个 17–25 MB，随仓库发不起：按**书本实际用字 + 保险集**出子集。

用法：
  python mcu-book/subset_fonts.py \
    --font "Noto Serif SC|/c/Windows/Fonts/NotoSerifSC-VF.ttf|wght=400|mcu-book/print/fonts/serif-regular.woff2" \
    --font "Noto Serif SC|/c/Windows/Fonts/NotoSerifSC-VF.ttf|wght=700|mcu-book/print/fonts/serif-bold.woff2" \
    --chars-from docs mcu-book/book --out-dir mcu-book/print/fonts

  # 原型/局部：只取前 N 章用字
  python mcu-book/subset_fonts.py --font ... --chars-from-sample 2 --out-dir .temp/font-proto
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

BOOK_DIR = Path(__file__).resolve().parent
REPO_ROOT = BOOK_DIR.parent

# 保险集：书本用字之外，正文偶尔会用到的标点/框线/箭头/货币/数学符号，
# 以及 ASCII 全量与常用中文标点。宁可多几千字，也不要印刷时缺字回退。
INSURANCE = (
    "".join(chr(c) for c in range(0x20, 0x7F))
    + "　、。〃々〈〉《》「」『』【】〔〕〖〗！＂＃％＆＇（）＊＋，－．／０１２３４５６７８９：；＜＝＞？＠［］＿｛｜｝～"
    + "←→↑↓↔⇒⇐⇔±×÷≤≥≠≈∞°℃§¶†‡•…‰′″‹›«»—–‒−─│┌┐└┘├┤┬┴┼╔╗╚╝╭╮╯╰■□●○◆◇★☆✓✔✗✘⚠ℹ"
    + "①②③④⑤⑥⑦⑧⑨⑩⑴⑵⑶⑷⑸⒈⒉⒊"
    + "αβγδεζηθικλμνξπρστυφχψωΑΒΓΔΕΖΗΘΙΚΛΜΝΞΠΡΣΤΥΦΧΨΩ"
)


def normalize_font_path(raw: str) -> Path:
    """把 /c/Windows/… 这类 MSYS 风格路径转成 Windows 路径（脚本在两种 shell 下都要能用）。"""
    m = re.match(r"^/([a-zA-Z])/(.*)$", raw)
    if m:
        return Path(f"{m.group(1).upper()}:/{m.group(2)}")
    return Path(raw)


def collect_chars(paths: list[Path], sample_chapters: int | None = None) -> set[str]:
    """收集书本用字：markdown 正文 + 附录 + 引用到的源文件（代码块里的 ASCII 也要）。

    目录还要收 **SVG 资产**（docs/public/anim、images）：内联进印前 PDF 的
    图内文字同样要被子集覆盖——实测漏收时 '垂/雇/∴/³' 落回系统字体，
    🔔/🔑/🔓 这些新 emoji 落成 Type3 位图。
    """
    chars: set[str] = set()
    files: list[Path] = []
    for path in paths:
        if path.is_dir():
            files.extend(
                sorted(
                    p
                    for p in path.rglob("*")
                    if p.is_file() and p.suffix in (".md", ".svg", ".json")
                )
            )
        elif path.is_file():
            files.append(path)
    if sample_chapters:
        # 原型模式：按路径序取前 N 个文件，够验证流水线即可
        files = files[: sample_chapters * 2]
    for path in files:
        chars.update(path.read_text(encoding="utf-8"))
    return chars - {"\n", "\r", "\t"}


def instance_axes(ttfont: TTFont, spec: str | None) -> TTFont:
    """把变量字体实例化成静态字重（wght=400 等）；静态字体直接返回。"""
    if not spec:
        return ttfont
    axes: dict[str, float] = {}
    for item in spec.split(","):
        key, _, value = item.partition("=")
        if not key or not value:
            raise SystemExit(f"轴向参数无法解析: {spec!r}（形如 wght=400）")
        axes[key.strip()] = float(value)
    return instancer.instantiateVariableFont(ttfont, axes, inplace=False, updateFontNames=True)


def subset_font(source: Path, out: Path, chars: set[str], axes: str | None) -> dict:
    font = instance_axes(TTFont(source), axes)
    options = subset.Options()
    options.layout_features = ["*"]           # 保留连字/小型大写等排版特性
    options.name_IDs = "*"                    # 保留全部 name 记录（字体名/许可声明）
    options.notdef_outline = True
    options.recalc_bounds = True
    options.desubroutinize = False
    # 带指令程序（prep/fpgm/cvt）的 TrueType 子集，Chromium 打印会把字形嵌成
    # Type3 位图（实测：同一页里带提示的 Book Mono 全部变无名 Type3，去掉后回到
    # Type0 TrueType 子集；1 页对照实验，2026-10-25）。印刷不需要 hinting。
    options.drop_tables += ["prep", "fpgm", "cvt ", "VDMX", "gasp", "hdmx", "LTSH"]
    text = "".join(sorted(chars | set(INSURANCE)))
    subsetter = subset.Subsetter(options=options)
    subsetter.populate(text=text)
    subsetter.subset(font)
    out.parent.mkdir(parents=True, exist_ok=True)
    font.flavor = "woff2"
    font.save(out)
    cmap = font.getBestCmap() or {}
    return {
        "output": str(out.relative_to(REPO_ROOT)) if out.is_relative_to(REPO_ROOT) else str(out),
        "bytes": out.stat().st_size,
        "chars": len(chars),
        "covered": set(cmap.keys()),
    }


def describe(ch: str) -> str:
    import unicodedata

    try:
        name = unicodedata.name(ch)
    except ValueError:
        name = "?"
    return f"U+{ord(ch):04X} {ch!r} {name}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--font",
        action="append",
        required=True,
        metavar="家族|源文件|轴向|输出",
        help="每个字体一条：家族名|源文件路径|wght=400|输出路径（轴向可留空）",
    )
    parser.add_argument(
        "--chars-from",
        nargs="*",
        default=[],
        help="收集用字的文件/目录（默认 docs、mcu-book/book、manifest.json 与 build_html.py 自身的界面文案）",
    )
    parser.add_argument("--chars-from-sample", type=int, default=None, help="原型模式：只取前 N 章")
    parser.add_argument("--out-dir", type=Path, required=True, help="字体与 provenance.json 的输出目录")
    options = parser.parse_args(argv)

    # 默认根必须包含**构建器注入的字面量**，不只正文：manifest.json 的标题/罗盘/
    # 来源卡与 build_html.py 里写死的界面文案（🧮 计算器、🎬 视频、↗ 箭头、
    # 来源卡字段）都会印进书里——实测全书 PDF 里 '筛'/'↗'/🧮 落回系统
    # SimSun/雅黑，就是 charset 漏了这些来源（字符覆盖按并集判定，
    # 缺一个字在纸上就是空白方块）。
    roots = [normalize_font_path(p) for p in options.chars_from] or [
        REPO_ROOT / "docs",
        REPO_ROOT / "docs" / "public",
        BOOK_DIR / "book",
        BOOK_DIR / "manifest.json",
        BOOK_DIR / "build_html.py",
    ]
    chars = collect_chars(roots, options.chars_from_sample)
    if not chars:
        print("✗ 收集到的用字为空——检查 --chars-from 指向", file=sys.stderr)
        return 1

    out_dir = options.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    records = []
    covered_union: set[int] = set()
    for spec in options.font:
        family, _, rest = spec.partition("|")
        raw_path, _, tail = rest.partition("|")
        axes, _, raw_out = tail.partition("|")
        if not raw_out:
            print(f"✗ --font 参数缺输出路径: {spec!r}", file=sys.stderr)
            return 1
        source = normalize_font_path(raw_path)
        if not source.is_file():
            print(f"✗ 源字体不存在: {source}", file=sys.stderr)
            return 1
        out = Path(raw_out)
        result = subset_font(source, out, chars, axes or None)
        covered_union |= result.pop("covered")
        records.append({"family": family, "axes": axes or "static", "source": str(source), "sourceSha256": sha256(source), **result})
        print(f"✓ {family} → {out}（{result['bytes'] / 1024:.0f} KB，覆盖 {result['chars']} 字）")

    # 判定按**并集**：某族缺 emoji 不算错（正文族 + emoji 回退族共同覆盖即可），
    # 但全书用字必须被提供的所有族合起来覆盖——否则印刷时会出现空白方块，
    # 而那种缺字在纸上是看不出来的（屏幕上有系统字体兜着）。
    missing = sorted({ch for ch in chars if ord(ch) not in covered_union})
    if missing:
        print(
            f"✗ 提供的字体合起来仍缺 {len(missing)} 个书里出现的字符："
            + "、".join(describe(ch) for ch in missing[:12]),
            file=sys.stderr,
        )
        return 1

    provenance = {
        "generated": date.today().isoformat(),
        "generator": "mcu-book/subset_fonts.py",
        "license": "SIL Open Font License 1.1（Noto / Cascadia 系列；见同目录 OFL.txt）",
        "charsFrom": [str(p) for p in roots],
        "insuranceSet": "ASCII + 常用中英标点 + 框线/箭头/数学符号（见脚本 INSURANCE）",
        "fonts": records,
    }
    (out_dir / "provenance.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"✓ 登记写入 {out_dir / 'provenance.json'}")
    return 0


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
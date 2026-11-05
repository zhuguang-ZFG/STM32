"""art_guard：手绘题图结构断言（纯矢量习语，88+6 枚量产的机器门）。

习语与判定（2026-10-26 实证钉死）：章首题图带 feTurbulence 滤镜内联进印前
HTML 会被 Chromium 整块光栅化（全书多出 94 张位图，印刷分辨率与可搜索性净损），
故题图一律纯矢量：无 filter / id / url() / 外链，手绘感靠曲线与笔压分级。

每枚 SVG 必须：
1. viewBox="0 0 320 88"（横幅题花规格）
2. 零 filter / id= / href= / src= / url()（同文档内联零撞车、印前零光栅化）
3. 无 <image> / <script> / <style>
4. 颜色不写死：fill=/stroke= 只许 "none" 或 var(--cover-ink, …)（暗色主题靠变量）
5. font-size ≥ 7（96mm 宽下 7 单位 ≈ 6pt，印刷地板）
6. 手绘感：同图 stroke-width 至少 2 档（笔压分级，硬信号）；
   C/Q/A 曲线命令 < 2 条时仅提示不判违规（直线+圆也是合法习语）
7. 纯 LF，字节 ≤ 6000（预算逼着曲线复用，拒绝堆料）

用法：
    python mcu-book/tools/art_guard.py 图1.svg [图2.svg …]
    python mcu-book/tools/art_guard.py --dir mcu-book/book/assets/chapter-art
退出码：0 全过；1 有违规。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

EXPECTED_VIEWBOX = 'viewBox="0 0 320 88"'
MAX_BYTES = 6000


def check_svg(path: Path, yuyu: bool = True) -> list[str]:
    # yuyu 参数仅为兼容旧调用；纯矢量是现唯一模式（滤镜版印前会光栅化）。
    # 读字节判 CRLF：read_text 的 universal newlines 会把 \r\n 解码成 \n，文本层判不出来
    errors: list[str] = ["含 CR（必须纯 LF 落盘）"] if b"\r" in path.read_bytes() else []
    text = path.read_text(encoding="utf-8")

    if EXPECTED_VIEWBOX not in text:
        m = re.search(r'viewBox="([^"]+)"', text)
        errors.append(f"viewBox 应为 0 0 320 88，实际 {m.group(1) if m else '缺失'}")

    # 纯矢量准入：滤镜/id/引用一律禁（御舆路线准入，印前零光栅化）
    for pat, label in [
        (r"<filter[\s>]", "<filter>（带滤镜会被印前光栅化）"),
        (r"\bid\s*=", "id=（同文档内联，无 id 即零撞车）"),
        (r"(?:href|src)\s*=", "href/src 引用"),
        (r"url\(", "url() 引用"),
        (r"<image[\s>]", "<image> 位图"),
        (r"<script[\s>]", "<script>"),
        (r"<style[\s>]", "<style>"),
        (r"url\(https?://", "外链 url()"),
    ]:
        if re.search(pat, text):
            errors.append(f"违规内容：{label}")

    size = len(text.encode("utf-8"))
    if size > MAX_BYTES:
        errors.append(f"{size} 字节超预算 {MAX_BYTES}")

    # 手绘感：笔压分级硬信号；曲线命令不足仅提示
    d_attrs = re.findall(r'\bd="([^"]+)"', text)
    curves = sum(1 for d in d_attrs for _ in re.findall(r"[CcQqAa]", d))
    if curves < 2:
        print(f"  ⚠ {path.name}: 曲线命令 {curves} 条（<2，提示级）")
    widths = {float(w) for w in re.findall(r'stroke-width="([\d.]+)"', text)}
    if len(widths) < 2:
        errors.append(f"stroke-width 仅 {len(widths)} 档 {sorted(widths)}（笔压分级要求 ≥2 档）")

    for m in re.finditer(r'(?:fill|stroke)="([^"]+)"', text):
        v = m.group(1)
        if v != "none" and not v.startswith("var(--cover-ink"):
            errors.append(f'颜色写死 {v!r}（只许 none 或 var(--cover-ink, …)）')
    for m in re.finditer(r'font-size="([\d.]+)"', text):
        if float(m.group(1)) < 7:
            errors.append(f"font-size {m.group(1)} < 7（印刷地板）")
    # 文本基线越界：text 的 y 是基线，超过画布下缘（88）则降部落出画外
    for m in re.finditer(r'<text[^>]*\sy="([\d.]+)"', text):
        if float(m.group(1)) > 87:
            errors.append(f"text 基线 y={m.group(1)} 超出画布下缘（基线须 < 88，否则降部落出画外）")
    return errors


def main() -> int:
    argv = sys.argv[1:]
    if not argv:
        print(__doc__)
        return 2
    if argv and argv[0] == "--dir":
        files = sorted(Path(argv[1]).glob("*.svg"))
    else:
        files = [Path(a) for a in argv]
    total = 0
    for f in files:
        errs = check_svg(f)
        total += len(errs)
        print(f"{f.name:<32} {'✓' if not errs else '✗'}")
        for e in errs:
            print(f"  {e}")
    print(f"\n{len(files)} 枚，违规 {total} 处")
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main())

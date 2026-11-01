#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""assets/animations/*.svg（CSS 动画）→ assets/gif/<name>-zh.gif 动图。

用途：公众号文章里的「▲ 动画」配图从静态快照升级为真动图（md2mp 会优先取这里的 gif）。
原理：为临时 SVG 冻结 CSS 动画时间轴，Chrome 逐帧截图，再由 PIL 用共享调色板组装 GIF
      （宽 640、64 色、8fps、循环）。默认对全部动画 svg 生效；已存在的 gif 仅在 --force 时重生成。

用法：
    python tools/svg2gif.py            # 缺啥生成啥
    python tools/svg2gif.py --force    # 全部重生成
    python tools/svg2gif.py timer-pwm  # 只做一个（stem 名）
"""
from __future__ import annotations

import math
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
ANIM = ROOT / "assets" / "animations"
OUT = ROOT / "assets" / "gif"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

FPS = 8
MAX_SECONDS = 12.0
WIDTH = 640


def svg_size(head: str) -> tuple[int, int]:
    m = re.search(r'width="(\d+)"[^>]*height="(\d+)"', head)
    if m:
        return int(m.group(1)), int(m.group(2))
    m = re.search(r'viewBox="[\d.]+ [\d.]+ ([\d.]+) ([\d.]+)"', head)
    if m:
        return int(float(m.group(1))), int(float(m.group(2)))
    return 900, 620


def loop_seconds(body: str) -> float:
    """CSS 动画周期取最小公倍数（秒，封顶 MAX_SECONDS）。"""
    durs = set()
    for m in re.finditer(r"animation:[^;{}]*?([\d.]+)s", body):
        durs.add(float(m.group(1)))
    for m in re.finditer(r"([\d.]+)s\s+(?:linear|ease|ease-in|ease-out|ease-in-out|infinite)", body):
        durs.add(float(m.group(1)))
    if not durs:
        return MAX_SECONDS
    # 转毫秒取整数 LCM，再回秒
    ms = [int(round(d * 1000)) for d in durs]

    def lcm(a: int, b: int) -> int:
        return a * b // math.gcd(a, b)

    total = ms[0]
    for x in ms[1:]:
        total = lcm(total, x)
    return min(total / 1000.0, MAX_SECONDS)


def render_frames(svg: Path, tmp: Path, dur: float, w: int, h: int) -> list[Path]:
    n = max(2, int(dur * FPS))
    frames = []
    source = svg.read_text(encoding="utf-8")
    # The source keeps its reduced-motion fallback for readers. A GIF render must
    # sample the animation even when the build machine asks Chrome to reduce motion.
    source = re.sub(
        r"@media\s*\(prefers-reduced-motion:\s*reduce\)\s*"
        r"\{\s*\*\s*\{\s*animation:none!important\s*\}\s*\}",
        "",
        source,
    )
    for i in range(n):
        t_ms = int(i * 1000 / FPS)
        frozen_svg = tmp / f"s{i:03d}.svg"
        freeze_script = f"""<script><![CDATA[
(() => {{
  const seek = () => document.getAnimations().forEach((animation) => {{
    animation.pause();
    animation.currentTime = {t_ms};
  }});
  seek();
  requestAnimationFrame(seek);
}})();
]]></script>"""
        frozen_svg.write_text(source.replace("</svg>", freeze_script + "</svg>"),
                              encoding="utf-8")
        f = tmp / f"f{i:03d}.png"
        cmd = [
            CHROME, "--headless", "--disable-gpu", "--hide-scrollbars",
            "--force-prefers-reduced-motion=no-preference",
            f"--user-data-dir={tmp / 'prof'}", "--force-device-scale-factor=1",
            f"--screenshot={f}", f"--window-size={w},{h}",
            "--virtual-time-budget=100",
            frozen_svg.as_uri(),
        ]
        subprocess.run(cmd, check=True, capture_output=True, timeout=60)
        frames.append(f)
    return frames


def assemble(frames: list[Path], dst: Path, fps: int = FPS, width: int = WIDTH):
    imgs = [Image.open(f).convert("RGB") for f in frames]
    scaled = [im.resize((width, round(im.height * width / im.width)), Image.LANCZOS) for im in imgs]
    # A shared palette keeps unchanged text and panels byte-identical between
    # frames. It also avoids the edge shimmer caused by per-frame dithering.
    palette = scaled[0].quantize(colors=64, method=Image.MEDIANCUT,
                                 dither=Image.Dither.NONE)
    quant = [s.quantize(palette=palette, dither=Image.Dither.NONE) for s in scaled]
    quant[0].save(dst, save_all=True, append_images=quant[1:],
                  duration=round(1000 / fps), loop=0, optimize=True, disposal=1)
    return len(quant)


def main(argv: list[str]) -> int:
    force = "--force" in argv
    only = [a for a in argv[1:] if not a.startswith("--")]
    OUT.mkdir(parents=True, exist_ok=True)
    svgs = sorted(ANIM.glob("*.svg"))
    if only:
        svgs = [s for s in svgs if s.stem in only]
    fail = 0
    for svg in svgs:
        dst = OUT / f"{svg.stem}-zh.gif"
        if dst.exists() and not force:
            print(f"[skip] {dst.name} 已存在")
            continue
        head = svg.read_text(encoding="utf-8", errors="ignore")
        if "animation" not in head[:4000] and "<animate" not in head:
            print(f"[skip] {svg.name} 无动画")
            continue
        w, h = svg_size(head)
        dur = loop_seconds(head)
        n = max(2, int(dur * FPS))
        print(f"[render] {svg.name} {w}x{h} 周期 {dur:.2f}s → {n} 帧 …")
        with tempfile.TemporaryDirectory(prefix="svg2gif-") as td:
            try:
                frames = render_frames(svg, Path(td), dur, w, h)
                cnt = assemble(frames, dst)
                size_mb = dst.stat().st_size / 1024 / 1024
                print(f"[ok] {dst.name} {cnt} 帧 {size_mb:.2f}MB")
            except Exception as e:  # noqa: BLE001
                fail += 1
                print(f"[FAIL] {svg.name}: {e}", file=sys.stderr)
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

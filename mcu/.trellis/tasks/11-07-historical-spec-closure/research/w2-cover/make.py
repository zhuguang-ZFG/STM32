#!/usr/bin/env python3
"""W2 封面隔离预览生成器（不接生产）。

输出 4 张 185×260 比例（740×1040 viewBox）的纯矢量封面：
  A-light / A-dark  —— 字上图下：标题区在上，开发板线稿居中偏下
  B-light / B-dark  —— 图右出血：左栏竖排式标题，开发板放大后从右侧出血
配色沿用书稿令牌：墨绿 #123b33 / 纸白 #f6f2e7；暗色 #e8efec / #0f1714，
accent #0e6e5c / #6fc6ae，暖色 #d97706 / #e0a35c。
开发板线稿直接复用 mcu-book/print/art.py 的 cover_art()，只做缩放、平移与裁切。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]  # mcu/
sys.path.insert(0, str(ROOT / "mcu-book" / "print"))
import art  # noqa: E402

OUT = ROOT / ".trellis/tasks/11-07-historical-spec-closure/research/w2-cover"
OUT.mkdir(parents=True, exist_ok=True)

TITLE = "通往单片机之路"
SUBTITLE_1 = "把一颗芯片讲透：以 STM32F407 为主线，"
SUBTITLE_2 = "对照 GD32 与 ESP32-S3，从寄存器一路走进双 RTOS。"
AUTHOR = "zhuguang-ZFG 与贡献者"
EDITION = "v1.0.0 · 2026-10-23"

THEMES = {
    "light": dict(
        paper="#f6f2e7", ink="#123b33", accent="#0e6e5c",
        soft="#dcebe4", warm="#d97706", muted="#5d6f68", line="#c9d8d1",
    ),
    "dark": dict(
        paper="#0f1714", ink="#e8efec", accent="#6fc6ae",
        soft="#173129", warm="#e0a35c", muted="#a9b6b1", line="#39463f",
    ),
}


def board_body() -> str:
    svg = art.cover_art()
    return re.search(r"<svg[^>]*>(.*)</svg>", svg, re.S).group(1)


BOARD = board_body()


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def frame(t: dict, bg: str = None) -> str:
    return f'<rect width="740" height="1040" fill="{bg or t["paper"]}"/>'


def hairlines(t: dict, x: int, y: int, w: int, gap: int = 10, n: int = 3) -> str:
    return "".join(
        f'<line x1="{x}" y1="{y + i * gap}" x2="{x + w}" y2="{y + i * gap}" '
        f'stroke="{t["line"]}" stroke-width="1"/>'
        for i in range(n)
    )


def pads(t: dict, x: int, y: int, n: int = 4, step: int = 18) -> str:
    out = []
    for i in range(n):
        cx = x + i * step
        out.append(
            f'<rect x="{cx}" y="{y}" width="9" height="9" fill="none" stroke="{t["accent"]}" stroke-width="1.4"/>'
            f'<circle cx="{cx + 4.5}" cy="{y + 4.5}" r="1.6" fill="{t["warm"]}"/>'
        )
    return "".join(out)


def cover_a(name: str, t: dict) -> str:
    body = f"""{frame(t)}
<g font-family="'Noto Sans SC','Source Han Sans SC','Microsoft YaHei',sans-serif">
  <text x="64" y="92" font-size="17" letter-spacing="6" fill="{t['accent']}">通往单片机之路</text>
  <text x="60" y="206" font-size="86" font-weight="800" fill="{t['ink']}" letter-spacing="2">{esc(TITLE)}</text>
  <line x1="64" y1="252" x2="196" y2="252" stroke="{t['warm']}" stroke-width="6"/>
  <text x="64" y="306" font-size="21" fill="{t['muted']}">{esc(SUBTITLE_1)}</text>
  <text x="64" y="340" font-size="21" fill="{t['muted']}">对照 GD32 与 ESP32-S3，从寄存器</text>
  <text x="64" y="374" font-size="21" fill="{t['muted']}">一路走进双 RTOS。</text>
  <g transform="translate(62 446)">
    <svg width="616" height="250" viewBox="0 30 320 130" preserveAspectRatio="xMidYMid meet" style="--cover-ink:{t['ink']}">{BOARD}</svg>
  </g>
  {hairlines(t, 64, 754, 612, 12, 2)}
  <text x="64" y="862" font-size="20" fill="{t['ink']}">{esc(AUTHOR)}</text>
  <text x="64" y="894" font-size="16" fill="{t['muted']}">{esc(EDITION)}</text>
  {pads(t, 560, 846, 4, 22)}
  <text x="64" y="972" font-size="12" letter-spacing="3" fill="{t['muted']}">185 × 260 mm · 纯矢量 · 无外部素材</text>
</g>"""
    return wrap(name, t, body)


def cover_b(name: str, t: dict) -> str:
    body = f"""{frame(t)}
<defs><clipPath id="page"><rect width="740" height="1040"/></clipPath></defs>
<g clip-path="url(#page)">
  <g font-family="'Noto Sans SC','Source Han Sans SC','Microsoft YaHei',sans-serif">
    <rect x="64" y="104" width="10" height="212" fill="{t['accent']}"/>
    <text x="104" y="196" font-size="84" font-weight="800" fill="{t['ink']}" letter-spacing="4">通往</text>
    <text x="104" y="288" font-size="84" font-weight="800" fill="{t['ink']}" letter-spacing="4">单片机之路</text>
    <line x1="106" y1="330" x2="238" y2="330" stroke="{t['warm']}" stroke-width="6"/>
    <text x="106" y="386" font-size="21" fill="{t['muted']}">把一颗芯片讲透：</text>
    <text x="106" y="420" font-size="21" fill="{t['muted']}">以 STM32F407 为主线，对照 GD32</text>
    <text x="106" y="454" font-size="21" fill="{t['muted']}">与 ESP32-S3，从寄存器一路走进双 RTOS。</text>
    <text x="106" y="520" font-size="16" letter-spacing="2" fill="{t['accent']}">C · 构建 · STM32 · 双 RTOS · ESP32-S3 · GD32</text>
    <text x="106" y="610" font-size="20" fill="{t['ink']}">{esc(AUTHOR)}</text>
    <text x="106" y="642" font-size="16" fill="{t['muted']}">{esc(EDITION)}</text>
    {pads(t, 600, 600, 4, 22)}
  </g>
  <g transform="translate(180 700) rotate(-6) scale(2.35)" opacity="0.98">
    <svg width="320" height="130" viewBox="0 30 320 130" preserveAspectRatio="xMidYMid meet" style="--cover-ink:{t['ink']}">{BOARD}</svg>
  </g>
  <circle cx="636" cy="150" r="92" fill="none" stroke="{t['line']}" stroke-width="1.2"/>
  <text x="596" y="158" font-size="12" letter-spacing="3" fill="{t['muted']}">REGISTER→RTOS</text>
</g>"""
    return wrap(name, t, body)


def wrap(name: str, t: dict, body: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="740" height="1040" '
        f'viewBox="0 0 740 1040" role="img" aria-label="{esc(name)} 封面预览" '
        f'style="--cover-ink:{t["ink"]}">{body}</svg>\n'
    )


INDEX = """<!doctype html>
<html lang="zh-CN"><meta charset="utf-8"><title>W2 封面隔离预览</title>
<style>
  :root { color-scheme: light dark; }
  body { margin: 0; padding: 28px; background: #202523; color: #e8efec;
         font: 15px/1.6 "Noto Sans SC","Microsoft YaHei",sans-serif; }
  h1 { font-size: 20px; margin: 0 0 6px; }
  p { margin: 0 0 22px; color: #a9b6b1; max-width: 980px; }
  .grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 18px; }
  @media (max-width: 1100px) { .grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
  @media (max-width: 620px) { .grid { grid-template-columns: 1fr; } }
  figure { margin: 0; background: #141a17; border: 1px solid #39463f; padding: 10px; }
  img { width: 100%; height: auto; display: block; }
  figcaption { padding-top: 8px; color: #c7d3ce; font-size: 13px; }
  figure:hover { border-color: #6fc6ae; }
</style>
<h1>W2 封面隔离预览：两构图 × 两配色</h1>
<p>均为 185×260 mm 比例（740×1040 viewBox）、纯矢量、无外部素材，复用 <code>mcu-book/print/art.py</code> 的开发板线稿。
本目录不接生产构建；用户选定构图与配色后，才进入 <code>build_html.py</code> / <code>build_print.py</code> 的封面接入评审。</p>
<div class="grid">
  <figure><img src="A-light.svg" alt="构图 A 浅色"><figcaption>A · 字上图下 / 纸白墨绿</figcaption></figure>
  <figure><img src="A-dark.svg" alt="构图 A 深色"><figcaption>A · 字上图下 / 夜墨青金</figcaption></figure>
  <figure><img src="B-light.svg" alt="构图 B 浅色"><figcaption>B · 图右出血 / 纸白墨绿</figcaption></figure>
  <figure><img src="B-dark.svg" alt="构图 B 深色"><figcaption>B · 图右出血 / 夜墨青金</figcaption></figure>
</div>
</html>
"""

for key, t in THEMES.items():
    (OUT / f"A-{key}.svg").write_text(cover_a(f"A-{key}", t), encoding="utf-8")
    (OUT / f"B-{key}.svg").write_text(cover_b(f"B-{key}", t), encoding="utf-8")
(OUT / "index.html").write_text(INDEX, encoding="utf-8")
print("written:", sorted(p.name for p in OUT.iterdir()))

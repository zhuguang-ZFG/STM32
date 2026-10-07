#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
svgkit.py —— 轻量 SVG 绘图 / 动画工具库（纯标准库，无第三方依赖）

本仓库所有 `assets/**/*.svg` 都由 tools/ 下的脚本用本库生成。
生成的是**自包含** SVG：样式写在 <style> 里，动画用 CSS @keyframes 或 SMIL，
因此在 GitHub 页面里用 <img> 引用即可直接播放动画（无需脚本，GitHub 也不会过滤）。

设计约定
--------
* 画布：默认 900x520，viewBox 与 width/height 一致，缩放交给 Markdown 的 width 属性。
* 主题：深色卡片（在 GitHub 亮色/暗色主题下都可读）。
* 字体：'PingFang SC','Microsoft YaHei',system-ui,sans-serif，等宽用 ui-monospace/Consolas。
* 每个动画都要有标题栏、图例、以及一句“说明字幕”。
"""

from __future__ import annotations

import math
import os


class T:
    """配色 / 尺寸常量。"""

    BG = "#0b1220"
    BG2 = "#0e1626"
    PANEL = "#111c31"
    PANEL2 = "#16233c"
    STROKE = "#243354"
    GRID = "#1a2742"

    TEXT = "#e6edf3"
    MUTED = "#93a4c0"
    DIM = "#64748b"

    CYAN = "#22d3ee"
    BLUE = "#60a5fa"
    GREEN = "#34d399"
    AMBER = "#fbbf24"
    ORANGE = "#fb923c"
    RED = "#f87171"
    VIOLET = "#a78bfa"
    PINK = "#f472b6"
    WHITE = "#f8fafc"

    FONT = ("'PingFang SC','Hiragino Sans GB','Microsoft YaHei',system-ui,"
            "-apple-system,'Segoe UI',sans-serif")
    MONO = ("ui-monospace,SFMono-Regular,'JetBrains Mono',Consolas,"
            "'Courier New',monospace")


def esc(s) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))

class Svg:
    """一张 SVG 画布。所有方法都返回 self 或生成的元素字符串。"""

    def __init__(self, w: int = 900, h: int = 520, title: str = "",
                 subtitle: str = "", bg: str = T.BG):
        self.w, self.h = w, h
        self.parts: list[str] = []
        self.styles: list[str] = []
        self.defs: list[str] = []
        self._ids: set[str] = set()
        self.bg = bg
        self.title = title
        self.subtitle = subtitle

    # ---------------- 基础 ----------------

    def add(self, raw: str) -> "Svg":
        self.parts.append(raw)
        return self

    def add_def(self, raw: str) -> "Svg":
        self.defs.append(raw)
        return self

    def add_style(self, raw: str) -> "Svg":
        self.styles.append(raw)
        return self

    def uid(self, prefix: str = "id") -> str:
        i = 0
        while f"{prefix}{i}" in self._ids:
            i += 1
        self._ids.add(f"{prefix}{i}")
        return f"{prefix}{i}"

    # ---------------- 图元 ----------------

    def rect(self, x, y, w, h, fill="none", stroke=None, rx=0, sw=1.5,
             opacity=1.0, dash=None, cls=None, style=None) -> str:
        a = [f'x="{x:g}"', f'y="{y:g}"', f'width="{w:g}"', f'height="{h:g}"',
             f'fill="{fill}"', f'opacity="{opacity:g}"']
        if rx:
            a.append(f'rx="{rx:g}"')
        if stroke:
            a += [f'stroke="{stroke}"', f'stroke-width="{sw:g}"']
        if dash:
            a.append(f'stroke-dasharray="{dash}"')
        if cls:
            a.append(f'class="{cls}"')
        if style:
            a.append(f'style="{style}"')
        el = f"<rect {' '.join(a)}/>"
        self.parts.append(el)
        return el

    def panel(self, x, y, w, h, rx=12, fill=T.PANEL, stroke=T.STROKE) -> "Svg":
        self.rect(x, y, w, h, fill=fill, stroke=stroke, rx=rx)
        return self

    def line(self, x1, y1, x2, y2, stroke=T.STROKE, sw=1.5, dash=None, cls=None,
             opacity=1.0, cap="round") -> str:
        a = [f'x1="{x1:g}"', f'y1="{y1:g}"', f'x2="{x2:g}"', f'y2="{y2:g}"',
             f'stroke="{stroke}"', f'stroke-width="{sw:g}"',
             f'stroke-linecap="{cap}"', f'opacity="{opacity:g}"']
        if dash:
            a.append(f'stroke-dasharray="{dash}"')
        if cls:
            a.append(f'class="{cls}"')
        el = f"<line {' '.join(a)}/>"
        self.parts.append(el)
        return el

    def circle(self, cx, cy, r, fill="none", stroke=None, sw=1.5, opacity=1.0,
               cls=None, style=None) -> str:
        a = [f'cx="{cx:g}"', f'cy="{cy:g}"', f'r="{r:g}"', f'fill="{fill}"',
             f'opacity="{opacity:g}"']
        if stroke:
            a += [f'stroke="{stroke}"', f'stroke-width="{sw:g}"']
        if cls:
            a.append(f'class="{cls}"')
        if style:
            a.append(f'style="{style}"')
        el = f"<circle {' '.join(a)}/>"
        self.parts.append(el)
        return el

    def path(self, d, fill="none", stroke=None, sw=1.5, dash=None, cls=None,
             opacity=1.0, cap="round", join="round", style=None,
             length=None) -> str:
        a = [f'd="{d}"', f'fill="{fill}"', f'opacity="{opacity:g}"',
             f'stroke-linecap="{cap}"', f'stroke-linejoin="{join}"']
        if stroke:
            a += [f'stroke="{stroke}"', f'stroke-width="{sw:g}"']
        if dash:
            a.append(f'stroke-dasharray="{dash}"')
        if cls:
            a.append(f'class="{cls}"')
        if style:
            a.append(f'style="{style}"')
        if length is not None:
            a.append(f'pathLength="{length:g}"')
        el = f"<path {' '.join(a)}/>"
        self.parts.append(el)
        return el

    def poly(self, pts, fill="none", stroke=None, sw=1.5, cls=None, opacity=1.0,
             dash=None) -> str:
        p = " ".join(f"{x:.2f},{y:.2f}" for x, y in pts)
        a = [f'points="{p}"', f'fill="{fill}"', f'opacity="{opacity:g}"']
        if stroke:
            a += [f'stroke="{stroke}"', f'stroke-width="{sw:g}"']
        if dash:
            a.append(f'stroke-dasharray="{dash}"')
        if cls:
            a.append(f'class="{cls}"')
        el = f"<polygon {' '.join(a)}/>"
        self.parts.append(el)
        return el


    def text(self, x, y, s, size=14, fill=T.TEXT, anchor="start", weight="normal",
             mono=False, opacity=1.0, cls=None, ls=None, style=None) -> str:
        a = [f'x="{x:g}"', f'y="{y:g}"', f'font-size="{size:g}"',
             f'fill="{fill}"', f'text-anchor="{anchor}"', f'opacity="{opacity:g}"']
        a.append(f'font-family="{T.MONO if mono else T.FONT}"')
        if weight != "normal":
            a.append(f'font-weight="{weight}"')
        if ls:
            a.append(f'letter-spacing="{ls}"')
        if cls:
            a.append(f'class="{cls}"')
        if style:
            a.append(f'style="{style}"')
        el = f"<text {' '.join(a)}>{esc(s)}</text>"
        self.parts.append(el)
        return el

    # ---------------- 组合元件 ----------------

    def box(self, x, y, w, h, label="", sub="", fill=T.PANEL, stroke=T.STROKE,
            color=T.TEXT, rx=10, size=15, cls=None, mono=False,
            icon=None) -> "Svg":
        self.rect(x, y, w, h, fill=fill, stroke=stroke, rx=rx, cls=cls)
        cy = y + h / 2
        if icon:
            self.text(x + 12, cy + size * 0.35, icon, size=size + 2, fill=color)
            tx, anchor = x + 32, "start"
        else:
            tx, anchor = x + w / 2, "middle"
        if label:
            self.text(tx, cy + (0 if not sub else -6) + size * 0.35, label, size=size,
                      fill=color, anchor=anchor, weight="600", mono=mono)
        if sub:
            self.text(x + w / 2, cy + 15, sub, size=size - 3, fill=T.MUTED,
                      anchor="middle")
        return self

    def chip(self, x, y, w, h, label, fill=T.PANEL2, stroke=T.STROKE,
             color=T.CYAN, size=13, rx=8) -> "Svg":
        self.rect(x, y, w, h, fill=fill, stroke=stroke, rx=rx)
        self.text(x + w / 2, y + h / 2 + size * 0.36, label, size=size, fill=color,
                  anchor="middle", weight="600")
        return self

    def arrow(self, x1, y1, x2, y2, color=T.CYAN, sw=2, dash=None, head=7,
              cls=None, marker=True, opacity=1.0) -> str:
        ang = math.atan2(y2 - y1, x2 - x1)
        if marker:
            bx, by = x2 - head * math.cos(ang), y2 - head * math.sin(ang)
        else:
            bx, by = x2, y2
        el = self.line(x1, y1, bx, by, stroke=color, sw=sw, dash=dash, cls=cls,
                       opacity=opacity)
        if marker:
            p1 = (x2 - head * math.cos(ang) + head * 0.5 * math.cos(ang + math.pi / 2),
                  y2 - head * math.sin(ang) + head * 0.5 * math.sin(ang + math.pi / 2))
            p2 = (x2 - head * math.cos(ang) + head * 0.5 * math.cos(ang - math.pi / 2),
                  y2 - head * math.sin(ang) + head * 0.5 * math.sin(ang - math.pi / 2))
            self.poly([(x2, y2), p1, p2], fill=color, opacity=opacity)
        return el

    def double_arrow(self, x1, y1, x2, y2, color=T.STROKE, sw=1, text_=""):
        self.line(x1, y1, x2, y2, stroke=color, sw=sw)
        for (ax, ay, bx, by) in ((x1, y1, x2, y2), (x2, y2, x1, y1)):
            ang = math.atan2(by - ay, bx - ax)
            self.poly([(bx, by),
                       (bx - 7 * math.cos(ang) + 3 * math.cos(ang + math.pi / 2),
                        by - 7 * math.sin(ang) + 3 * math.sin(ang + math.pi / 2)),
                       (bx - 7 * math.cos(ang) + 3 * math.cos(ang - math.pi / 2),
                        by - 7 * math.sin(ang) + 3 * math.sin(ang - math.pi / 2))],
                      fill=color)
        if text_:
            self.text((x1 + x2) / 2, (y1 + y2) / 2 - 6, text_, size=11,
                      fill=T.MUTED, anchor="middle")
        return self

    def led(self, cx, cy, r=12, color=T.RED, cls=None, glow=True) -> "Svg":
        if glow:
            self.circle(cx, cy, r * 2.1, fill=color, opacity=0.16,
                        cls=(cls + "-glow") if cls else None)
        self.circle(cx, cy, r, fill=color, stroke="#00000066", sw=1, cls=cls)
        self.circle(cx - r * 0.3, cy - r * 0.35, r * 0.28, fill="#ffffff",
                    opacity=0.7)
        return self

    def waveform(self, x, y, w, h, bits, color=T.GREEN, sw=2.4, cls=None,
                 label=None, label_color=None) -> "Svg":
        """数字波形：bits 为 0/1 序列，等宽绘制。"""
        n = len(bits)
        step = w / n
        y0, y1 = y + h * 0.84, y + h * 0.16
        d = [f"M {x:g} {y0 if bits[0] == 0 else y1:g}"]
        for i in range(n):
            yy = y0 if bits[i] == 0 else y1
            d.append(f"L {x + i * step:.2f} {yy:.2f}")
            d.append(f"L {x + (i + 1) * step:.2f} {yy:.2f}")
        self.path(" ".join(d), stroke=color, sw=sw, cls=cls)
        if label:
            self.text(x, y + h + 15, label, size=12,
                      fill=label_color or T.MUTED)
        return self

    def grid(self, x, y, w, h, cols=10, rows=5, color=T.GRID, sw=1):
        for i in range(cols + 1):
            xx = x + w * i / cols
            self.line(xx, y, xx, y + h, stroke=color, sw=sw)
        for j in range(rows + 1):
            yy = y + h * j / rows
            self.line(x, yy, x + w, yy, stroke=color, sw=sw)
        return self

    def axis(self, x, y, w, h, ylabel="", xlabel="", color=T.STROKE):
        self.line(x, y, x, y + h, stroke=color, sw=1.4)
        self.line(x, y + h, x + w, y + h, stroke=color, sw=1.4)
        if ylabel:
            self.text(x - 8, y + 10, ylabel, size=11, fill=T.DIM, anchor="end")
        if xlabel:
            self.text(x + w, y + h + 16, xlabel, size=11, fill=T.DIM, anchor="end")
        return self


    def header(self, title=None, subtitle=None, tag=None, tag_color=T.CYAN) -> "Svg":
        title = self.title if title is None else title
        subtitle = self.subtitle if subtitle is None else subtitle
        self.rect(0, 0, self.w, 58, fill=T.BG2)
        self.line(0, 58, self.w, 58, stroke=T.STROKE, sw=1)
        self.rect(0, 0, 4, 58, fill=tag_color)
        self.text(22, 32, title, size=20, weight="700")
        if subtitle:
            self.text(22, 50, subtitle, size=12, fill=T.MUTED)
        if tag:
            w = 14 + len(tag) * 9
            self.chip(self.w - w - 22, 15, w, 28, tag, color=tag_color, size=12)
        return self

    def footer(self, note="", color=T.DIM) -> "Svg":
        if note:
            self.line(24, self.h - 42, self.w - 24, self.h - 42, stroke=T.GRID, sw=1)
            self.text(24, self.h - 18, note, size=12, fill=color)
        self.text(self.w - 24, self.h - 18, "自绘矢量动画 · STM32 知识库", size=11,
                  fill=T.DIM, anchor="end")
        return self

    def legend(self, x, y, items, size=12, dx=130) -> "Svg":
        """items: [(color, label), ...]"""
        for i, (c, lab) in enumerate(items):
            self.rect(x + i * dx, y - 10, 12, 12, fill=c, rx=3)
            self.text(x + i * dx + 18, y + 1, lab, size=size, fill=T.MUTED)
        return self

    def title_block(self, x, y, text_, color=T.CYAN, size=14) -> "Svg":
        self.rect(x, y - size + 1, 3, size + 4, fill=color)
        self.text(x + 12, y, text_, size=size, weight="600", fill=T.TEXT)
        return self

    def code(self, x, y, lines, size=13, lh=19, color=T.GREEN, cls=None) -> "Svg":
        for i, ln in enumerate(lines):
            self.text(x, y + i * lh, ln, size=size, mono=True, fill=color, cls=cls)
        return self

    # ---------------- 输出 ----------------

    def render(self) -> str:
        head = (f'<svg xmlns="http://www.w3.org/2000/svg" '
                f'xmlns:xlink="http://www.w3.org/1999/xlink" '
                f'width="{self.w}" height="{self.h}" '
                f'viewBox="0 0 {self.w} {self.h}" role="img" '
                f'aria-label="{esc(self.title)}">')
        style = ""
        if self.styles:
            style = "<style>\n" + "\n".join(self.styles) + "\n</style>"
        defs = ""
        if self.defs:
            defs = "<defs>\n" + "\n".join(self.defs) + "\n</defs>"
        bg = (f'<rect x="0" y="0" width="{self.w}" height="{self.h}" '
              f'fill="{self.bg}"/>')
        return "\n".join([head, style, defs, bg, *self.parts, "</svg>", ""])

    def save(self, path: str) -> str:
        d = os.path.dirname(os.path.abspath(path))
        os.makedirs(d, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.render())
        return path




# ======================================================================================
# 常用动画片段（CSS keyframes / SMIL）
# ======================================================================================


def css_kf(name: str, frames) -> str:
    """css_kf('x', [('0%', 'opacity:1'), ('100%', 'opacity:0')])"""
    body = "".join(f"{p}{{{v}}}" for p, v in frames)
    return f"@keyframes {name}{{{body}}}"


def _n(sel: str) -> str:
    return (sel.strip("#.").replace(" ", "-").replace(",", "-")
            .replace(">", "-").replace(":", "-"))


def anim_blink(selector: str, dur="1s", dim=0.1, delay="0s", glow=True) -> str:
    """LED 闪烁：亮/灭硬切换。"""
    n = _n(selector)
    a = "opacity:1" + (";filter:drop-shadow(0 0 9px currentColor)" if glow else "")
    return (css_kf(f"{n}-blink",
                   [("0%,48%", a), ("50%,98%", f"opacity:{dim};filter:none")])
            + f"\n{selector}{{animation:{n}-blink {dur} steps(1,end) infinite {delay};}}")


def anim_fade(selector: str, dur="2s", a=0.15, b=1.0, delay="0s") -> str:
    n = _n(selector)
    return (css_kf(f"{n}-fade", [("0%,100%", f"opacity:{a}"), ("50%", f"opacity:{b}")])
            + f"\n{selector}{{animation:{n}-fade {dur} ease-in-out infinite {delay};}}")


def anim_pulse(selector: str, dur="2s", scale=1.07, delay="0s") -> str:
    n = _n(selector)
    return (css_kf(f"{n}-pulse", [("0%,100%", "transform:scale(1)"),
                                  ("50%", f"transform:scale({scale})")])
            + f"\n{selector}{{animation:{n}-pulse {dur} ease-in-out infinite {delay};"
              f"transform-box:fill-box;transform-origin:center;}}")


def anim_flow(selector: str, dur="1.6s", dash="10 14", shift=-24) -> str:
    """信号流动：虚线偏移滚动。"""
    n = _n(selector)
    return (f"\n{selector}{{stroke-dasharray:{dash};"
            f"animation:{n}-flow {dur} linear infinite;}}"
            + css_kf(f"{n}-flow", [("from", "stroke-dashoffset:0"),
                                   ("to", f"stroke-dashoffset:{shift}px")]))


def anim_move(selector: str, dur="3s", dx=0, dy=0, delay="0s",
              ease="ease-in-out") -> str:
    """往复平移（transform-box:fill-box 使其相对自身坐标）。"""
    n = _n(selector)
    return (css_kf(f"{n}-move", [("0%,100%", "transform:translate(0,0)"),
                                 ("50%", f"transform:translate({dx}px,{dy}px)")])
            + f"\n{selector}{{animation:{n}-move {dur} {ease} infinite {delay};"
              f"transform-box:fill-box;}}")


def anim_tx(selector: str, dur="4s", x1=0, x2=200, delay="0s",
            timing="linear") -> str:
    """单向平移循环。"""
    n = _n(selector)
    return (css_kf(f"{n}-tx", [("0%", f"transform:translateX({x1}px)"),
                               ("100%", f"transform:translateX({x2}px)")])
            + f"\n{selector}{{animation:{n}-tx {dur} {timing} infinite {delay};}}")


def anim_rotate(selector: str, dur="3s", cx=0, cy=0, ccw=False) -> str:
    n = _n(selector)
    end = "rotate(-360deg)" if ccw else "rotate(360deg)"
    return (css_kf(f"{n}-rot", [("from", "rotate(0deg)"), ("to", end)])
            + f"\n{selector}{{animation:{n}-rot {dur} linear infinite;"
              f"transform-origin:{cx}px {cy}px;}}")


def anim_draw(selector: str, dur="2.4s", delay="0s") -> str:
    """线条描绘效果：元素需带 pathLength="1" 与 stroke-dasharray:1。"""
    n = _n(selector)
    return (f"\n{selector}{{stroke-dasharray:1;stroke-dashoffset:1;"
            f"animation:{n}-draw {dur} ease-in-out infinite alternate {delay};}}"
            + css_kf(f"{n}-draw", [("from", "stroke-dashoffset:1"),
                                   ("to", "stroke-dashoffset:0")]))


def anim_width(selector: str, dur="3s", values=(0.15, 1.0), delay="0s") -> str:
    """宽度往复变化（PWM 占空比、进度条）：元素用 <rect>，以左端为原点缩放。"""
    n = _n(selector)
    a, b = values
    return (css_kf(f"{n}-w", [("0%,100%", f"transform:scaleX({a:.3f})"),
                              ("50%", "transform:scaleX(1)")])
            + f"\n{selector}{{animation:{n}-w {dur} ease-in-out infinite {delay};"
              f"transform-box:fill-box;transform-origin:left center;}}")


def anim_height(selector: str, dur="3s", values=(0.15, 1.0), delay="0s") -> str:
    n = _n(selector)
    a, b = values
    return (css_kf(f"{n}-h", [("0%,100%", f"transform:scaleY({a})"),
                              ("50%", f"transform:scaleY({b})")])
            + f"\n{selector}{{animation:{n}-h {dur} ease-in-out infinite {delay};"
              f"transform-box:fill-box;transform-origin:center bottom;}}")


def anim_flash(selector: str, dur="2s", delay="0s", base=0.25) -> str:
    """瞬时高亮（用于「当前步骤」指示）。"""
    n = _n(selector)
    return (css_kf(f"{n}-flash",
                   [("0%,12%", "opacity:1"), ("16%,100%", f"opacity:{base}")])
            + f"\n{selector}{{animation:{n}-flash {dur} linear infinite {delay};}}")


def smil_motion(path_id: str, dur="3s", begin="0s", rotate=False,
                repeat="indefinite") -> str:
    rot = ' rotate="auto"' if rotate else ""
    return (f'<animateMotion dur="{dur}" begin="{begin}" '
            f'repeatCount="{repeat}"{rot}><mpath xlink:href="#{path_id}"/>'
            f'</animateMotion>')


def smil_animate(attr: str, values: str, dur="2s", begin="0s",
                 repeat="indefinite", keytimes=None, calc="linear",
                 fill="freeze") -> str:
    kt = f' keyTimes="{keytimes}"' if keytimes else ""
    return (f'<animate attributeName="{attr}" values="{values}" dur="{dur}" '
            f'begin="{begin}" repeatCount="{repeat}" calcMode="{calc}"{kt} '
            f'fill="{fill}"/>')


def polyline_d(pts) -> str:
    return "M " + " L ".join(f"{x:.2f} {y:.2f}" for x, y in pts)


def wave_points(x, y, w, h, fn, n=120):
    """生成函数曲线点集；fn(t) -> [-1,1]，t ∈ [0,1]。"""
    return [(x + i / n * w, y + h / 2 - fn(i / n) * h / 2) for i in range(n + 1)]


def sine(t, cycles=2.0):
    return math.sin(2 * math.pi * cycles * t)

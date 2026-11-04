#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B5 mechanism animations for chapters 20 and 21.

CSS keyframes only; first frame PDF-readable; prefers-reduced-motion.

    python tools/sample_figs_b5/anim_b5.py assets/animations
"""

from __future__ import annotations

import hashlib
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from svgkit import Svg, T, anim_flow, anim_tx

W, H = 900, 620
TEXT_RE = re.compile(r"<text\b[^>]*>(.*?)</text>", flags=re.DOTALL)


def _step_highlight(prefix: str, n: int, period=6.0, window=0.22,
                    peak=0.42, rest=0.08) -> str:
    css = []
    step = 100.0 / n
    for i in range(n):
        a = i * step
        b = min(a + step * window, 99.2)
        name = f"{prefix}{i}-flash"
        css.append(
            f"@keyframes {name}{{0%,{a:.2f}%{{opacity:{rest}}}"
            f"{a + 0.3:.2f}%,{b:.2f}%{{opacity:{peak}}}"
            f"{min(b + 0.3, 100):.2f}%,100%{{opacity:{rest}}}}}"
        )
        css.append(f".{prefix}{i}{{animation:{name} {period}s linear infinite;}}")
    return "\n".join(css)


def lookup_flow() -> Svg:
    """DS → RM → PM → AN → UM sequential lookup mechanism."""
    s = Svg(W, H, "手册查找数据流", "订货号对上手册，再按问题类型下钻")
    s.header(title="证据查找：从订货号到正确手册", subtitle="mechanism · FA-002 continuous-line",
             tag="20", tag_color=T.CYAN)

    boxes = [
        ("订货号", "F103C8T6", T.BLUE, "先写清芯片"),
        ("DS", "电气/引脚", T.CYAN, "极限与复用"),
        ("RM", "寄存器", T.GREEN, "位域与状态机"),
        ("PM", "内核/启动", T.AMBER, "向量与异常"),
        ("AN/UM", "配方/工具", T.VIOLET, "步骤与 IDE"),
    ]
    bw, gap, x0, y0, bh = 120, 42, 40, 110, 78
    for i, (label, sub, color, note) in enumerate(boxes):
        x = x0 + i * (bw + gap)
        s.rect(x, y0, bw, bh, fill=T.PANEL, stroke=color, rx=8)
        s.text(x + bw / 2, y0 + 28, label, size=15, anchor="middle",
               fill=T.TEXT, weight="700")
        s.text(x + bw / 2, y0 + 50, sub, size=12, anchor="middle", fill=color)
        s.text(x + bw / 2, y0 + bh + 22, note, size=11, anchor="middle", fill=T.MUTED)
        if i < len(boxes) - 1:
            ax1, ax2 = x + bw + 6, x + bw + gap - 6
            s.arrow(ax1, y0 + bh / 2, ax2, y0 + bh / 2, color=T.STROKE, sw=2, marker=True)
            s.line(ax1, y0 + bh / 2, ax2, y0 + bh / 2, stroke=T.CYAN, sw=2, cls=f"f{i}")
            s.circle(ax1, y0 + bh / 2, 4, fill=T.CYAN, cls=f"p{i}")

    css = []
    for i in range(len(boxes) - 1):
        css.append(anim_flow(f".f{i}", dur="1.4s", dash="6 12", shift=-18))
        css.append(anim_tx(f".p{i}", dur="1.4s", x1=0, x2=gap - 12, delay=f"{i * 0.28:.2f}s"))
    css.append(_step_highlight("m", 5, period=5.0))
    for i in range(5):
        x = x0 + i * (bw + gap)
        s.rect(x, y0, bw, bh, fill=T.CYAN, rx=8, cls=f"m{i}", opacity=0.1)

    s.title_block(40, 260, "问题类型 → 手册（首帧即可读）", color=T.GREEN)
    rows = [
        ("引脚能否接 5V / 最大电流", "DS 表与脚注", T.CYAN),
        ("USART_BRR 怎么算", "RM 时钟树 + USART", T.GREEN),
        ("复位后 MSP 从哪来", "PM 向量表", T.AMBER),
        ("CubeMX 点哪", "UM + 官方例程", T.VIOLET),
    ]
    for i, (q, ans, color) in enumerate(rows):
        y = 292 + i * 48
        s.rect(40, y, 820, 42, fill=T.PANEL, stroke=T.STROKE, rx=8)
        s.text(56, y + 26, q, size=13, fill=T.TEXT)
        s.text(840, y + 26, ans, size=13, fill=color, anchor="end", weight="700")

    s.rect(40, 500, 820, 56, fill=T.BG2, stroke=T.GREEN, rx=8)
    s.text(56, 524, "动画语义：高亮沿订货号 → DS → RM → PM → AN/UM 前进；不是装饰扫光。",
           size=13, fill=T.TEXT)
    s.text(56, 546, "PDF 首帧保留完整五盒与四问对照；减动效时只显示静态底图。",
           size=12, fill=T.MUTED)

    css.append("@media (prefers-reduced-motion: reduce){*{animation:none!important}}")
    s.add_style("\n".join(css))
    s.footer(note="自绘矢量动画 · FA-002 · 手册分工机制演示，非实拍",
             label="自绘矢量动画 · STM32 知识库")
    return s


def power_swd() -> Svg:
    """Power → NRST → BOOT0 → SWD connect sequence on LQFP48 mental model."""
    s = Svg(W, H, "上电到 SWD 接通", "先电源与复位，再 BOOT0，最后才谈调试器")
    s.header(title="板级接通：3V3 → NRST → BOOT0 → SWD", subtitle="mechanism · FA-002 continuous-line",
             tag="21", tag_color=T.CYAN)

    steps = [
        ("1 供电", "3V3 / GND", "先量电压", T.GREEN),
        ("2 复位", "NRST 高", "松开复位", T.CYAN),
        ("3 启动脚", "BOOT0 = 0", "跑用户 Flash", T.AMBER),
        ("4 调试", "SWDIO/SWCLK", "PA13 / PA14", T.VIOLET),
    ]
    bw, gap, x0, y0, bh = 170, 36, 50, 108, 90
    for i, (title, sub, note, color) in enumerate(steps):
        x = x0 + i * (bw + gap)
        s.rect(x, y0, bw, bh, fill=T.PANEL, stroke=color, rx=8)
        s.text(x + bw / 2, y0 + 28, title, size=16, anchor="middle", fill=color, weight="700")
        s.text(x + bw / 2, y0 + 52, sub, size=13, anchor="middle", fill=T.TEXT, mono=True)
        s.text(x + bw / 2, y0 + 74, note, size=12, anchor="middle", fill=T.MUTED)
        if i < len(steps) - 1:
            ax1, ax2 = x + bw + 4, x + bw + gap - 4
            s.arrow(ax1, y0 + bh / 2, ax2, y0 + bh / 2, color=T.STROKE, sw=2, marker=True)
            s.line(ax1, y0 + bh / 2, ax2, y0 + bh / 2, stroke=color, sw=2, cls=f"f{i}")
            s.circle(ax1, y0 + bh / 2, 4, fill=color, cls=f"p{i}")

    css = []
    for i, (_, _, _, color) in enumerate(steps[:-1]):
        css.append(anim_flow(f".f{i}", dur="1.5s", dash="6 12", shift=-18))
        css.append(anim_tx(f".p{i}", dur="1.5s", x1=0, x2=gap - 10, delay=f"{i * 0.35:.2f}s"))
    css.append(_step_highlight("s", 4, period=5.2))
    for i in range(4):
        x = x0 + i * (bw + gap)
        s.rect(x, y0, bw, bh, fill=T.CYAN, rx=8, cls=f"s{i}", opacity=0.1)

    # chip mental model
    s.title_block(40, 250, "LQFP48 心智模型（非实拍引脚图）", color=T.GREEN)
    s.rect(80, 280, 320, 200, fill=T.PANEL, stroke=T.STROKE, rx=8)
    s.rect(140, 320, 200, 120, fill=T.BG2, stroke=T.CYAN, rx=8)
    s.text(240, 370, "STM32F103", size=16, anchor="middle", fill=T.TEXT, weight="700")
    s.text(240, 396, "C8T6", size=13, anchor="middle", fill=T.MUTED, mono=True)
    # pins labels around
    s.text(100, 350, "3V3", size=12, fill=T.GREEN, weight="700")
    s.text(100, 372, "GND", size=12, fill=T.MUTED)
    s.text(100, 410, "NRST", size=12, fill=T.CYAN, weight="700")
    s.text(360, 350, "BOOT0", size=12, fill=T.AMBER, weight="700")
    s.text(360, 380, "PA13 SWDIO", size=12, fill=T.VIOLET)
    s.text(360, 402, "PA14 SWCLK", size=12, fill=T.VIOLET)

    s.rect(440, 280, 420, 200, fill=T.PANEL, stroke=T.STROKE, rx=8)
    checks = [
        ("供电未稳就连 SWD", "先看 3V3 纹波与电流", T.RED),
        ("BOOT0 悬空或拉高", "进系统存储器，应用像「没烧进去」", T.AMBER),
        ("NRST 被外部拉低", "调试器偶发断开", T.CYAN),
        ("线序对但未共地", "认不出芯片", T.VIOLET),
    ]
    for i, (bad, fix, color) in enumerate(checks):
        y = 304 + i * 42
        s.text(456, y, "× " + bad, size=13, fill=color, weight="700")
        s.text(456, y + 18, "→ " + fix, size=12, fill=T.TEXT)

    s.rect(40, 500, 820, 56, fill=T.BG2, stroke=T.GREEN, rx=8)
    s.text(56, 524, "动画语义：四步依次点亮；跳步连 SWD 是本章最常见假阳性。",
           size=13, fill=T.TEXT)
    s.text(56, 546, "首帧含完整顺序与失败对照；减动效时保持静态可读。",
           size=12, fill=T.MUTED)

    css.append("@media (prefers-reduced-motion: reduce){*{animation:none!important}}")
    s.add_style("\n".join(css))
    s.footer(note="自绘矢量动画 · FA-002 · 上电到 SWD 机制演示，非实拍",
             label="自绘矢量动画 · STM32 知识库")
    return s


FIGURES = [
    ("sample-20-lookup-flow.svg", lookup_flow),
    ("sample-21-power-swd.svg", power_swd),
]


def _audit(name: str, path: str) -> None:
    raw = open(path, "rb").read()
    text = raw.decode("utf-8")
    assert 'width="900"' in text and 'height="620"' in text, name
    assert "animation:" in text and "prefers-reduced-motion" in text, name
    assert "FA-002" in text and "自绘" in text, name
    assert "<animate" not in text, name
    digest = hashlib.sha256("\n".join(TEXT_RE.findall(text)).encode("utf-8")).hexdigest()
    print(f"{name}  900x620  {len(raw)} bytes  text_hash={digest}")


def main(out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    for name, builder in FIGURES:
        path = os.path.join(out_dir, name)
        builder().save(path)
        _audit(name, path)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "assets/animations")

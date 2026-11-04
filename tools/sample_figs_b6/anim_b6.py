#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B6 mechanism animations for chapters 23 and 28.

CSS keyframes only; first frame PDF-readable; prefers-reduced-motion.

    python tools/sample_figs_b6/anim_b6.py assets/animations
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


def _audit(name: str, path: str) -> str:
    raw = open(path, "rb").read()
    text = raw.decode("utf-8")
    assert "@keyframes" in text, name
    assert "prefers-reduced-motion" in text, name
    assert "自绘矢量动画" in text, name
    digest = hashlib.sha256("\n".join(TEXT_RE.findall(text)).encode("utf-8")).hexdigest()
    print(f"{name}  {W}x{H}  {len(raw)} bytes  text_hash={digest}")
    return digest


def boot_latch() -> Svg:
    """G0 BOOT0/SWCLK sample latch at 4th SYSCLK rising edge."""
    s = Svg(W, H, "G0 启动锁存：第四个 SYSCLK 上升沿采样 BOOT0/SWCLK 共脚",
            "mechanism · FA-002 · DS12232 / RM0444 / AN2606")
    s.header(title="BOOT 锁存机制：共脚上的四个上升沿", subtitle="sample then freeze · SWD after latch",
             tag="23", tag_color=T.CYAN)

    # timeline
    s.title_block(40, 100, "SYSCLK 上升沿 1→4（首帧完整可读）", color=T.CYAN)
    edges = [("边沿 1", "上电稳定"), ("边沿 2", "采样窗逼近"), ("边沿 3", "仍可扰动"), ("边沿 4", "锁存 BOOT")]
    for i, (lab, note) in enumerate(edges):
        x = 50 + i * 210
        s.rect(x, 140, 180, 90, fill=T.PANEL, stroke=T.CYAN if i == 3 else T.STROKE, rx=8)
        s.text(x + 90, 172, lab, size=15, fill=T.CYAN if i == 3 else T.TEXT, anchor="middle", weight="700")
        s.text(x + 90, 200, note, size=12, fill=T.MUTED, anchor="middle")
        s.circle(x + 90, 250, 7, fill=T.CYAN, cls=f"e{i}")
        if i < 3:
            s.line(x + 180, 250, x + 210, 250, stroke=T.STROKE, sw=1.5)
            s.line(x + 180, 250, x + 210, 250, stroke=T.CYAN, sw=2, cls=f"f{i}")

    # dual role pin
    s.rect(40, 290, 820, 120, fill=T.PANEL, stroke=T.AMBER, rx=8)
    s.text(56, 322, "PA14 = BOOT0 输入  ∩  SWCLK", size=16, fill=T.AMBER, weight="700")
    s.text(56, 352, "锁存前：脚上电平必须对启动源成立；锁存后：同一脚交给调试时钟。", size=14, fill=T.TEXT)
    s.text(56, 380, "动画语义：高亮沿 1→4 前进；第 4 沿冻结启动源——不是装饰扫光。", size=13, fill=T.MUTED)

    # decision
    s.title_block(40, 440, "失联时的第一分支", color=T.GREEN)
    for i, (title, detail, color) in enumerate((
        ("Under Reset", "不保证可连接", T.RED),
        ("读选项字节", "BOOT_LOCK / RDP / DBG_SWEN", T.AMBER),
        ("受控恢复", "读回验证后再改", T.GREEN),
    )):
        x = 40 + i * 280
        s.rect(x, 470, 260, 70, fill=T.BG2, stroke=color, rx=8)
        s.text(x + 130, 498, title, size=14, fill=color, anchor="middle", weight="700")
        s.text(x + 130, 522, detail, size=12, fill=T.TEXT, anchor="middle")

    css = [_step_highlight("m", 4, period=5.2)]
    for i in range(4):
        x = 50 + i * 210
        s.rect(x, 140, 180, 90, fill=T.CYAN, rx=8, cls=f"m{i}", opacity=0.1)
    for i in range(3):
        css.append(anim_flow(f".f{i}", dur="1.2s", dash="6 12", shift=-18))
        css.append(anim_tx(f".e{i}", dur="1.2s", x1=0, x2=30, delay=f"{i * 0.25:.2f}s"))
    # Edge 4: latch hold — peak then stay readable (not a missing class)
    css.append(
        "@keyframes e3-latch{0%,70%{opacity:0.25}78%,100%{opacity:1}}"
    )
    css.append(".e3{animation:e3-latch 5.2s linear infinite;}")
    css.append("@media (prefers-reduced-motion: reduce){*{animation:none!important}}")
    s.add_style("\n".join(css))
    s.footer(note="自绘矢量动画 · FA-002 · BOOT 锁存机制演示，非实拍",
             label="自绘矢量动画 · STM32 知识轨")
    return s


def owner_flow() -> Svg:
    """Owner-task handoff: IRQ posts, owner runs, supervisor feeds WDG."""
    s = Svg(W, H, "所有者任务机制：IRQ 只投递，所有者消费，监督者喂狗",
            "mechanism · FA-002 · chapter 28 system model")
    s.header(title="所有者任务数据流：证明比到处加锁更容易", subtitle="IRQ → queue → owner → actuator · supervisor → WDG",
             tag="28", tag_color=T.VIOLET)

    boxes = [
        ("IRQ", "短且无阻塞", T.RED, "只写队列"),
        ("队列", "深度有预算", T.AMBER, "水位可观测"),
        ("所有者", "唯一写外设", T.CYAN, "超时+恢复"),
        ("执行器", "驱动状态机", T.GREEN, "完成回执"),
        ("监督者", "健康合成", T.VIOLET, "唯一喂狗"),
    ]
    bw, gap, x0, y0, bh = 140, 28, 40, 110, 86
    for i, (lab, sub, color, note) in enumerate(boxes):
        x = x0 + i * (bw + gap)
        s.rect(x, y0, bw, bh, fill=T.PANEL, stroke=color, rx=8)
        s.text(x + bw / 2, y0 + 28, lab, size=15, anchor="middle", fill=T.TEXT, weight="700")
        s.text(x + bw / 2, y0 + 52, sub, size=12, anchor="middle", fill=color)
        s.text(x + bw / 2, y0 + bh + 20, note, size=11, anchor="middle", fill=T.MUTED)
        if i < len(boxes) - 1:
            ax1, ax2 = x + bw + 4, x + bw + gap - 4
            s.arrow(ax1, y0 + bh / 2, ax2, y0 + bh / 2, color=T.STROKE, sw=2, marker=True)
            s.line(ax1, y0 + bh / 2, ax2, y0 + bh / 2, stroke=T.CYAN, sw=2, cls=f"f{i}")
            s.circle(ax1, y0 + bh / 2, 4, fill=T.CYAN, cls=f"p{i}")

    s.title_block(40, 260, "故障注入落点（首帧可读）", color=T.GREEN)
    rows = [
        ("队列满", "看生产者速率与消费者阻塞点", T.AMBER),
        ("任务冻结", "高水位 / 任务状态 / 持锁时间", T.RED),
        ("驱动超时", "状态机时间戳与 IRQ 计数", T.VIOLET),
        ("误喂狗", "业务成功 ≠ 允许直接 IWDG reload", T.CYAN),
    ]
    for i, (q, ans, color) in enumerate(rows):
        y = 292 + i * 48
        s.rect(40, y, 820, 42, fill=T.PANEL, stroke=T.STROKE, rx=8)
        s.text(56, y + 26, q, size=13, fill=color, weight="700")
        s.text(840, y + 26, ans, size=13, fill=T.TEXT, anchor="end")

    s.rect(40, 500, 820, 56, fill=T.BG2, stroke=T.GREEN, rx=8)
    s.text(56, 524, "动画语义：令牌沿 IRQ→队列→所有者→执行器→监督者前进；减动效时保留静态五盒与四问。",
           size=13, fill=T.TEXT)
    s.text(56, 546, "PDF 首帧即可用于排错分工；开源 tag 仍须写进验收记录。", size=12, fill=T.MUTED)

    css = []
    for i in range(len(boxes) - 1):
        css.append(anim_flow(f".f{i}", dur="1.3s", dash="6 12", shift=-18))
        css.append(anim_tx(f".p{i}", dur="1.3s", x1=0, x2=gap - 8, delay=f"{i * 0.22:.2f}s"))
    css.append(_step_highlight("m", 5, period=5.0))
    for i in range(5):
        x = x0 + i * (bw + gap)
        s.rect(x, y0, bw, bh, fill=T.CYAN, rx=8, cls=f"m{i}", opacity=0.1)
    css.append("@media (prefers-reduced-motion: reduce){*{animation:none!important}}")
    s.add_style("\n".join(css))
    s.footer(note="自绘矢量动画 · FA-002 · 所有者任务机制演示，非实拍",
             label="自绘矢量动画 · STM32 知识轨")
    return s


FIGURES = (
    ("sample-23-boot-latch.svg", boot_latch),
    ("sample-28-owner-flow.svg", owner_flow),
)


def main(out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    for name, builder in FIGURES:
        path = os.path.join(out_dir, name)
        builder().save(path)
        _audit(name, path)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "assets/animations")

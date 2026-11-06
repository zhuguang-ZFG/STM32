#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mechanism animations for ch06 / ch11 / ch28 — b23 round, new files only.

    python tools/sample_figs_quality6/anim_q6.py [out_dir]
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from svgkit import Svg, T, anim_flow
from sample_figs_quality3._common import audit_anim

W, H = 900, 620
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                   "assets", "animations")


def _step_highlight(prefix: str, n: int, period=7.0, window=0.2, peak=0.35, rest=0.06) -> str:
    css = []
    step = 100.0 / n
    for i in range(n):
        a = i * step
        b = min(a + step * window, 99.0)
        name = f"{prefix}{i}-flash"
        css.append(
            f"@keyframes {name}{{0%,{a:.2f}%{{opacity:{rest}}}"
            f"{a + 0.25:.2f}%,{b:.2f}%{{opacity:{peak}}}"
            f"{min(b + 0.25, 100):.2f}%,100%{{opacity:{rest}}}}}"
        )
        css.append(f".{prefix}{i}{{animation:{name} {period}s linear infinite;}}")
    return "\n".join(css)


def _flow_row(s, css, steps, y0=100, bh=100, bw=120, gap=18):
    for i, (t, n, col) in enumerate(steps):
        x = 40 + i * (bw + gap)
        s.rect(x, y0, bw, bh, fill=T.PANEL, stroke=col, rx=8)
        s.text(x + bw / 2, y0 + 32, t, size=13, anchor="middle", fill=col, weight="700")
        s.text(x + bw / 2, y0 + 60, n, size=11, anchor="middle", fill=T.TEXT, mono=True)
        s.rect(x, y0, bw, bh, fill=col, rx=8, cls=f"s{i}", opacity=0.12)
        if i < len(steps) - 1:
            ax1, ax2 = x + bw + 4, x + bw + gap - 4
            s.arrow(ax1, y0 + bh / 2, ax2, y0 + bh / 2, color=T.STROKE, sw=2)
            s.line(ax1, y0 + bh / 2, ax2, y0 + bh / 2, stroke=T.CYAN, sw=2, cls=f"f{i}")
            css.append(anim_flow(f".f{i}", dur="1.2s", dash="6 12", shift=-18))


def _facts(s, rows, y0=265):
    for i, (a, b, col) in enumerate(rows):
        y = y0 + i * 44
        s.rect(40, y, 820, 38, fill=T.PANEL, stroke=T.STROKE, rx=8)
        s.text(56, y + 24, a, size=13, fill=col, weight="700", mono=True)
        s.text(840, y + 24, b, size=13, fill=T.TEXT, anchor="end")


def _note(s, l1, l2, y0=460):
    s.rect(40, y0, 820, 70, fill=T.BG2, stroke=T.RED, rx=8)
    s.text(56, y0 + 28, l1, size=13, fill=T.TEXT)
    s.text(56, y0 + 50, l2, size=12, fill=T.MUTED)


def ore_overwrite_flow() -> Svg:
    s = Svg(W, H, "ORE overwrite moment", "byte 2 lands while RXNE is still unread")
    s.header(title="ORE：RXNE 没人读，字节 2 直接覆盖", subtitle="mechanism · FA-002 continuous-line",
             tag="06", tag_color=T.CYAN)
    css = []
    steps = [
        ("BYTE 1", "0xA5 lands", T.GREEN),
        ("RXNE=1", "wait for read", T.CYAN),
        ("BYTE 2", "next 86.8 us", T.AMBER),
        ("OVERWRITE", "shift reg lost", T.RED),
        ("ORE=1", "byte 1 safe", T.RED),
        ("CLEAR", "SR then DR", T.GREEN),
    ]
    _flow_row(s, css, steps)
    css.append(_step_highlight("s", 6, period=7.0))
    s.title_block(40, 230, "Motion is the overwrite moment — the FE story stays on the handraw plate", color=T.GREEN)
    _facts(s, [
        ("115200 8N1", "1 bit = 8.68 us, 10 bits = 86.8 us", T.CYAN),
        ("Clear order", "read SR (0x00) then DR (0x04)", T.GREEN),
        ("Wrong order", "DR alone clears nothing; the port stalls", T.AMBER),
        ("FE alone", "never raises an interrupt (needs RXNE/EIE)", T.VIOLET),
    ])
    _note(s, "Motion advances byte1 → RXNE → byte2 → overwrite → ORE → clear — not a bounce loop.",
          "The stop-bit sampling story stays on ch06-ore-fe (handraw) and sample-06-frame-annotated.")
    css.append("@media (prefers-reduced-motion: reduce){*{animation:none!important}}")
    s.add_style("\n".join(css))
    s.footer(note="自绘矢量动画 · FA-002 · ORE 覆盖瞬间，非示波器实测",
             label="自绘矢量动画 · STM32 知识库")
    return s


def wwdg_window_flow() -> Svg:
    s = Svg(W, H, "WWDG count and the feed window", "0x7F down to 0x3F; feed only inside [0x40, 0x50]")
    s.header(title="WWDG：往下数，窗口里才准喂", subtitle="mechanism · FA-002 continuous-line",
             tag="11", tag_color=T.AMBER)
    css = []
    steps = [
        ("START", "0x7F", T.CYAN),
        ("COUNT", "-1 per 910 us", T.CYAN),
        ("0x50", "W line: feed opens", T.GREEN),
        ("FEED", "inside [0x40,0x50]", T.GREEN),
        ("0x40", "floor", T.AMBER),
        ("0x3F", "T6=0 reset", T.RED),
    ]
    _flow_row(s, css, steps)
    css.append(_step_highlight("s", 6, period=7.0))
    s.title_block(40, 230, "Motion walks the count — the zone arithmetic stays on the handraw plate", color=T.GREEN)
    _facts(s, [
        ("Tick", "(1/36e6) x 4096 x 8 = 910 us per count", T.CYAN),
        ("Full run", "64 counts = 58.25 ms (typical, not guaranteed)", T.GREEN),
        ("Window", "W = 0x50: feeding above it resets at once", T.AMBER),
        ("Floor", "rolling below 0x40 (T6 cleared) resets too", T.VIOLET),
    ])
    _note(s, "Motion advances start → count → window → feed → floor → reset — not a bounce loop.",
          "IWDG only punishes a late feed; that contrast stays on sample-11-iwdg-math.")
    css.append("@media (prefers-reduced-motion: reduce){*{animation:none!important}}")
    s.add_style("\n".join(css))
    s.footer(note="自绘矢量动画 · FA-002 · WWDG 窗口机制，非示波器实测",
             label="自绘矢量动画 · STM32 知识库")
    return s


def supervisor_flow() -> Svg:
    s = Svg(W, H, "One supervisor feeds the IWDG", "all epochs healthy, or no feed")
    s.header(title="看门狗健康监督者：全部健康才喂", subtitle="mechanism · FA-002 continuous-line",
             tag="28", tag_color=T.CYAN)
    css = []
    steps = [
        ("TASK A", "epoch++", T.GREEN),
        ("TASK B", "epoch++", T.GREEN),
        ("TASK C", "epoch++", T.GREEN),
        ("CHECK", "all + backlog", T.CYAN),
        ("FEED", "IWDG refresh", T.AMBER),
        ("HEALTHY", "no reset", T.GREEN),
    ]
    _flow_row(s, css, steps)
    css.append(_step_highlight("s", 6, period=7.0))
    s.title_block(40, 230, "Motion is the health round — the false-health story stays on the handraw plate", color=T.GREEN)
    _facts(s, [
        ("Epoch rule", "each critical task updates its own after real work", T.GREEN),
        ("Supervisor", "checks every epoch, backlog, watermarks, state machines", T.CYAN),
        ("Feed gate", "IWDG refreshes only when everything passes", T.AMBER),
        ("Failure", "persist a bounded fault summary first; it has a deadline too", T.VIOLET),
    ])
    _note(s, "Motion advances the health round A → B → C → check → feed — not a bounce loop.",
          "Per-task feeding reports false health: tasks stuck while an interrupt keeps feeding.")
    css.append("@media (prefers-reduced-motion: reduce){*{animation:none!important}}")
    s.add_style("\n".join(css))
    s.footer(note="自绘矢量动画 · FA-002 · 看门狗监督者机制，非示波器实测",
             label="自绘矢量动画 · STM32 知识库")
    return s


ANIMS = [
    ("sample-06-ore-overwrite-flow.svg", ore_overwrite_flow),
    ("sample-11-wwdg-window-flow.svg", wwdg_window_flow),
    ("sample-28-supervisor-flow.svg", supervisor_flow),
]


def main() -> None:
    out = sys.argv[1] if len(sys.argv) > 1 else OUT
    os.makedirs(out, exist_ok=True)
    for name, fn in ANIMS:
        path = os.path.join(out, name)
        fn().save(path)
        audit_anim(name, path)
    print(f"wrote {len(ANIMS)} anims -> {out}")


if __name__ == "__main__":
    main()

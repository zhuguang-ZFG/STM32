#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Static B4 figure for chapter 13: CAN triage across bit timing, filters and TEC.

No CSS animation and no SMIL.

    python tools/sample_figs_b4/ch13_b4.py assets/diagrams
"""

from __future__ import annotations

import hashlib
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from svgkit import Svg, T


def _credit(canvas: Svg, note: str) -> None:
    canvas.line(24, canvas.h - 36, canvas.w - 24, canvas.h - 36, stroke=T.GRID, sw=1)
    canvas.text(24, canvas.h - 16, note, size=11, fill=T.MUTED)
    canvas.text(canvas.w - 24, canvas.h - 16, "自绘 · 静态 · CC BY 4.0", size=11, fill=T.DIM, anchor="end")


def _branch(canvas: Svg, y: int, color: str, heading: str, panel_h: int,
            lead: str, body: list[tuple[str, str]], check: str) -> None:
    canvas.text(40, y, heading, size=16, fill=color, weight="700")
    canvas.rect(40, y + 14, 880, panel_h, fill=T.PANEL, stroke=color, rx=8)
    canvas.text(56, y + 44, lead, size=15, fill=T.TEXT, weight="700")
    cy = y + 72
    for line, tone in body:
        canvas.text(56, cy, line, size=13, fill=tone)
        cy += 26
    canvas.text(56, cy, check, size=13, fill=T.MUTED)


def _wrap(c: Svg, x: float, y: float, s: str, w: float, size: float,
          color: str, lh: float = 15, mono: bool = False) -> float:
    from svgkit import text_width
    words, line, yy = s.split(), "", y
    for word in words:
        probe = (line + " " + word).strip()
        if text_width(probe, size, mono) > w and line:
            c.text(x, yy, line, size=size, fill=color, mono=mono)
            yy += lh
            line = word
        else:
            line = probe
    if line:
        c.text(x, yy, line, size=size, fill=color, mono=mono)
        yy += lh
    return yy


def can_triage() -> Svg:
    canvas = Svg(
        960,
        880,
        "预分频 9 配 8 个份额是 500 kbit/s；邮箱空是标准 ID 没左移 5 位；错误帧暴涨查采样点与终端",
        "STM32F103C8T6 · chapter 13 · RM0008 Rev 21 第 21 章 bxCAN · DS5319 Rev 20 表 5",
    )
    canvas.header(title="CAN 三岔口：发不出、收不到、错误帧暴涨",
                  tag="13", tag_color=T.ORANGE)

    # 顶条：一位 = 2 µs = 8 个 Tq，采样点在 6/8
    canvas.text(24, 82, "先把一位拆开：36 MHz ÷ 9 = 4 MHz，Tq = 250 ns，8 个 Tq = 2 µs = 500 kbit/s",
                size=12.5, fill=T.TEXT, weight="700")
    bx, by, bw, bh = 24, 92, 900, 62
    canvas.rect(bx, by, bw, bh, fill=T.PANEL, stroke=T.GRID, rx=8)
    segs = [("Sync", 1, T.CYAN), ("BS1 = 5", 5, T.GREEN), ("BS2 = 2", 2, T.AMBER)]
    x = bx + 12
    unit = (bw - 24) / 8
    for name, n, color in segs:
        w = unit * n
        canvas.rect(x, by + 10, w, 24, fill=color, rx=2, opacity=0.28)
        canvas.text(x + w / 2, by + 27, name, size=10.5, anchor="middle",
                    fill=color, weight="700")
        for k in range(n):
            canvas.line(x + k * unit, by + 10, x + k * unit, by + 34,
                        stroke=T.GRID, sw=1)
        x += w
    canvas.line(bx + 12 + unit * 6, by + 6, bx + 12 + unit * 6, by + 40,
                stroke=T.RED, sw=2)
    canvas.text(bx + 12 + unit * 6, by + 54, "采样点 75% = 1.5 µs", size=10,
                anchor="middle", fill=T.RED)
    canvas.text(bx + 16, by + 54, "0", size=9.5, fill=T.MUTED, mono=True)
    canvas.text(bx + bw - 16, by + 54, "2 µs", size=9.5, fill=T.MUTED,
                anchor="end", mono=True)

    # 三条岔口
    ay, ah = 176, 330
    # ① TEC 阶梯
    canvas.rect(24, ay, 290, ah, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.rect(24, ay, 290, 5, fill=T.RED, rx=2)
    canvas.text(38, ay + 30, "① 发不出：帧一直重发", size=13, fill=T.TEXT,
                weight="700")
    canvas.text(38, ay + 50, "单节点没开回环，没人给 ACK", size=10, fill=T.RED,
                mono=True)
    steps = [("每次尝试 ACK 错误", "+8 TEC", T.MUTED),
             ("第 16 次到 128", "error-passive", T.AMBER),
             ("被动错误标志", "仍然重传", T.AMBER),
             ("到不了 256", "不会 Bus-Off", T.MUTED)]
    for i, (head, note, color) in enumerate(steps):
        y = ay + 78 + i * 44
        canvas.circle(48, y, 10, fill=T.BG2, stroke=color, sw=1.5)
        canvas.text(48, y + 3.5, str(i + 1), size=9.5, anchor="middle",
                    fill=color, weight="700")
        canvas.text(66, y, head, size=10.5, fill=T.TEXT)
        canvas.text(66, y + 16, note, size=9.5, fill=color, mono=True)
        if i < 3:
            canvas.line(48, y + 12, 48, y + 32, stroke=T.STROKE, sw=1.5)
    canvas.rect(38, ay + 250, 262, 30, fill=T.BG2, stroke=T.GREEN, rx=4)
    canvas.text(50, ay + 270, "先开回环跑 100 帧，再怀疑收发器", size=9.5,
                fill=T.GREEN)
    canvas.text(38, ay + 300, "读 TEC / ESR：128 = 总线没人应答，不是控制器坏",
                size=9, fill=T.MUTED)

    # ② 过滤器左移 5 位
    canvas.rect(326, ay, 300, ah, fill=T.PANEL, stroke=T.AMBER, rx=8)
    canvas.rect(326, ay, 300, 5, fill=T.AMBER, rx=2)
    canvas.text(340, ay + 30, "② 收不到：邮箱一直是空的", size=13, fill=T.TEXT,
                weight="700")
    canvas.text(340, ay + 50, "标准 ID 进 FilterIdHigh 要左移 5 位", size=10,
                fill=T.AMBER, mono=True)
    # 32 位过滤器寄存器
    fx, fw = 340, 272
    cells = [("STDID[10:0]", 11, T.AMBER), ("EXID", 2, T.CYAN),
             ("I R 0", 3, T.MUTED)]
    cx2 = fx
    canvas.text(fx, ay + 74, "FilterIdHigh（高 16 位）", size=9, fill=T.MUTED)
    for name, n, color in cells:
        w = fw * n / 16
        canvas.rect(cx2, ay + 80, w - 2, 26, fill=T.PANEL2, stroke=color,
                    sw=1.5 if color == T.AMBER else 1, rx=2)
        canvas.text(cx2 + w / 2, ay + 97, name, size=8.5, anchor="middle",
                    fill=color, mono=True)
        cx2 += w
    canvas.text(340, ay + 124, "0x123  →  0x123 << 5", size=10.5, fill=T.GREEN,
                mono=True)
    canvas.arrow(340, ay + 132, 610, ay + 132, color=T.GREEN, sw=1.5, head=5)
    canvas.text(340, ay + 154, "不左移：掩码对上了，数据位却错位 → 邮箱永远空",
                size=9.5, fill=T.RED)
    canvas.text(340, ay + 176, "掩码 0x7FF << 5 = 11 位全匹配；EXID/IDE/RTR 占低位", size=9,
                fill=T.MUTED, mono=True)
    canvas.text(340, ay + 194, "F1：14 组过滤器 / 2 个 RX FIFO", size=9.5,
                fill=T.MUTED)
    canvas.text(340, ay + 216, "过滤器要挂 FIFO0 或 FIFO1，中断开", size=9.5,
                fill=T.MUTED)
    canvas.text(340, ay + 234, "CAN_IT_RX_FIFO0_MSG_PENDING", size=9, fill=T.CYAN,
                mono=True)
    canvas.rect(340, ay + 250, 272, 30, fill=T.BG2, stroke=T.VIOLET, rx=4)
    canvas.text(352, ay + 262, "向量名 USB_LP_CAN_RX0", size=9, fill=T.VIOLET,
                mono=True)
    canvas.text(352, ay + 274, "CAN 与 USB 共用，别编进同一个工程", size=9,
                fill=T.MUTED)

    # ③ 采样点与终端
    canvas.rect(638, ay, 298, ah, fill=T.PANEL, stroke=T.VIOLET, rx=8)
    canvas.rect(638, ay, 298, 5, fill=T.VIOLET, rx=2)
    canvas.text(652, ay + 30, "③ 错误帧暴涨：两端都报错", size=13, fill=T.TEXT,
                weight="700")
    canvas.text(652, ay + 50, "先对齐位时间与采样点，再查线与终端", size=10,
                fill=T.VIOLET, mono=True)
    # 两条采样点不同的位时间
    for i, (lab, frac, color) in enumerate((("75% · BS1 5 / BS2 2", 6 / 8, T.GREEN),
                                            ("70% · BS1 6 / BS2 3", 7 / 10, T.RED))):
        y = ay + 78 + i * 40
        canvas.text(652, y, lab, size=9.5, fill=color, mono=True)
        canvas.rect(652, y + 8, 270, 16, fill=T.BG2, stroke=T.GRID, rx=2)
        canvas.line(652 + 270 * frac, y + 4, 652 + 270 * frac, y + 28,
                    stroke=color, sw=2)
        canvas.circle(652 + 270 * frac, y + 16, 4, fill=color)
    canvas.text(652, ay + 168, "混用两种分法，边沿永远对不齐", size=9.5,
                fill=T.MUTED)
    # 终端电阻
    canvas.text(652, ay + 192, "终端：总线两端各一只 120 Ω", size=10,
                fill=T.TEXT)
    canvas.line(652, ay + 208, 928, ay + 208, stroke=T.STROKE, sw=2)
    for xx in (672, 906):
        canvas.rect(xx, ay + 200, 24, 16, fill=T.PANEL2, stroke=T.CYAN, rx=2)
        canvas.text(xx + 12, ay + 212, "120", size=8.5, anchor="middle",
                    fill=T.CYAN, mono=True)
    canvas.text(652, ay + 236, "两只并联 = 60 Ω 直流负载，不是电缆特性阻抗",
                size=9, fill=T.MUTED)
    canvas.text(652, ay + 258, "TEC 256 = Bus-Off：恢复要 128 × 11 个连续隐性位",
                size=9, fill=T.RED)
    canvas.text(652, ay + 276, "ABOM 可自动回；先存一份 CANH−CANL 差分波形",
                size=9, fill=T.MUTED)

    # 底条：引脚重映射
    py = 528
    canvas.text(24, py, "引脚先确认：默认在 PA11/PA12，BluePill 用第一种重映射", size=12.5,
                fill=T.TEXT, weight="700")
    pins = [("第 32 脚 PA11", "CAN_RX（默认）", "也是 USB D−", T.MUTED),
            ("第 33 脚 PA12", "CAN_TX（默认）", "也是 USB D+", T.MUTED),
            ("第 45 脚 PB8", "CAN_RX（重映射）", "本例程使用", T.GREEN),
            ("第 46 脚 PB9", "CAN_TX（重映射）", "接收发器 TXD", T.GREEN)]
    for i, (pin, func, note, color) in enumerate(pins):
        x = 24 + i * 228
        canvas.rect(x, py + 12, 216, 56, fill=T.PANEL, stroke=color, rx=8)
        canvas.text(x + 12, py + 32, pin, size=11, fill=T.TEXT, weight="600")
        canvas.text(x + 12, py + 48, func, size=9.5, fill=color, mono=True)
        canvas.text(x + 12, py + 62, note, size=9, fill=T.MUTED)

    # 位时间换算对照
    ty = 616
    canvas.text(24, ty, "两组数不能混：36 MHz 下预分频必须整除", size=12.5,
                fill=T.TEXT, weight="700")
    rows = [("9 × 8 Tq", "500 kbit/s", "采样 75%（本例程）", T.GREEN),
            ("8 × 10 Tq", "450 kbit/s", "对端 500 → 双方都报错", T.RED),
            ("10 Tq 想要 500k", "需 7.2 分频", "不是整数，配不出来", T.AMBER)]
    for i, (calc, speed, note, color) in enumerate(rows):
        y = ty + 18 + i * 34
        canvas.rect(24, y, 900, 28, fill=T.BG2 if i % 2 == 0 else T.PANEL,
                    stroke=T.GRID, rx=4)
        canvas.text(36, y + 19, calc, size=10.5, fill=T.TEXT, mono=True)
        canvas.text(190, y + 19, speed, size=10.5, fill=color, mono=True)
        canvas.text(330, y + 19, note, size=10, fill=T.MUTED)

    _credit(canvas, "自绘。位时间、过滤器与 TEC 来自 RM0008 Rev 21 第 21 章；PB8/PB9 来自 DS5319 Rev 20 表 5。")
    return canvas


FIGURES = [
    ("sample-13-can-triage.svg", can_triage),
]

T_COLORS = {
    value
    for name in dir(T)
    if name.isupper() and isinstance(value := getattr(T, name), str) and value.startswith("#")
}
TEXT_RE = re.compile(r"<text\b[^>]*>(.*?)</text>", flags=re.DOTALL)


def _audit(name: str, path: str) -> str:
    raw = open(path, "rb").read()
    text = raw.decode("utf-8")
    width, height = (int(part) for part in re.search(r'\bwidth="(\d+)" height="(\d+)"', text).groups())
    strokes = set(re.findall(r'stroke-width="([^"]+)"', text))
    radii = set(re.findall(r'\brx="([^"]+)"', text))
    colors = {item.lower() for item in re.findall(r"#(?:[0-9A-Fa-f]{6})(?![0-9A-Fa-f])", text)}
    digest = hashlib.sha256("\n".join(TEXT_RE.findall(text)).encode("utf-8")).hexdigest()

    assert width == 960, (name, "width", width)
    assert height == 880, (name, "height", height)
    assert strokes <= {"1", "1.5", "2"}, (name, "stroke-width", sorted(strokes))
    assert radii <= {"2", "4", "8"}, (name, "rx", sorted(radii))
    assert colors <= T_COLORS, (name, "colors", sorted(colors - T_COLORS))
    assert "自绘" in text, (name, "credit")
    for banned in ("<animate", "@keyframes", "animation:", "矢量动画"):
        assert banned not in text, (name, "animation", banned)
    assert len(raw) < 60 * 1024, (name, "bytes", len(raw))
    print(f"{name}  {width}x{height}  {len(raw)} bytes  text_hash={digest}")
    return digest


def main(argv: list[str] | None = None) -> None:
    args = sys.argv[1:] if argv is None else argv
    out_dir = args[0] if args else os.path.join("assets", "diagrams")
    os.makedirs(out_dir, exist_ok=True)
    for name, make in FIGURES:
        path = make().save(os.path.join(out_dir, name))
        _audit(name, path)


if __name__ == "__main__":
    main()

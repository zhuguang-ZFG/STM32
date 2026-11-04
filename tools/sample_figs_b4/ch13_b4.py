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


def can_triage() -> Svg:
    canvas = Svg(
        960,
        880,
        "预分频 8 配 10 个份额是 450 kbit/s；邮箱空是没左移 5 位；错误帧暴涨查采样点",
        "STM32F103C8T6 · chapter 13 · RM0008 Rev 21 第 21 章 bxCAN · DS5319 Rev 20 表 5",
    )
    canvas.header(tag="13", tag_color=T.CYAN)
    canvas.text(40, 86, "STM32F103C8T6   CAN1 on APB1 36 MHz   prescaler 9   BS1 5   BS2 2   SJW 1",
                size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "three symptoms, three branches: silent TX, empty mailbox, error frames piling up",
                size=14, fill=T.CYAN)
    canvas.text(40, 138, "36e6 / (9 × 8) = 500 kbit/s   Tq = 250 ns   8 × 250 ns = 2 µs   sample 75% = 1.5 µs",
                size=13, fill=T.AMBER, mono=True)

    _branch(
        canvas, 170, T.AMBER, "岔口一  发不出：帧一直重发", 188,
        "先量位时间：2 µs 一位才是 500 kbit/s，两端必须用同一组数",
        [
            ("预分频 8 配 10 个时间份额是 36e6 / (8 × 10) = 450 kbit/s；10 个份额要 7.2 分频，不是整数", T.TEXT),
            ("单节点、没开回环：每次尝试都是 ACK 错误，TEC 每次加 8，十六次到 128 进 error-passive", T.TEXT),
            ("error-passive 只发被动错误标志，仍持续重传同一帧，到不了 256，也就不会 Bus-Off", T.TEXT),
            ("单板调试先开回环模式跑 100 帧，别先怀疑收发器坏了", T.TEXT),
        ],
        "checkpoint：读 TEC 与 ESR，128 说明总线没人应答，不是控制器坏了",
    )

    _branch(
        canvas, 396, T.GREEN, "岔口二  收不到：邮箱一直是空的", 188,
        "总线上有帧、邮箱却是空的：先查过滤器，不是先换收发器",
        [
            ("标准 ID 写 FilterIdHigh 要左移 5 位：0x123 写成 0x123 << 5，不左移邮箱永远空", T.TEXT),
            ("掩码 0x7FF << 5 表示 11 位全部必须匹配；F1 有 14 组过滤器、2 个接收 FIFO", T.TEXT),
            ("过滤器要挂到 FIFO0 或 FIFO1，中断用 CAN_IT_RX_FIFO0_MSG_PENDING 打开", T.TEXT),
            ("向量表里这条中断叫 USB_LP_CAN_RX0，和 USB 共用：CAN 与 USB 例程不能编进同一个工程", T.RED),
        ],
        "checkpoint：先回环数清 FIFO0 的接收数量，再上真实总线",
    )

    _branch(
        canvas, 622, T.RED, "岔口三  错误帧暴涨：两端都在报错", 160,
        "两端都报错：先对齐位时间与采样点，再去查线和终端",
        [
            ("采样点 75%（BS1 5 / BS2 2）与 70%（BS1 6 / BS2 3）混用，边沿就对不齐", T.TEXT),
            ("终端电阻接在总线两端 CANH 与 CANL 之间，各一只 120 Ω；两只并联是 60 Ω 直流负载，不是电缆特性阻抗", T.TEXT),
            ("TEC 到 256 进 Bus-Off：恢复要 128 次、每次 11 个连续隐性位，ABOM 可自动回", T.TEXT),
        ],
        "checkpoint：存一份 CAN_H 减 CAN_L 的差分波形，先看位宽与采样点",
    )

    canvas.rect(40, 800, 880, 30, fill=T.BG2, stroke=T.GREEN, rx=8)
    canvas.text(56, 820, "底注  重映射后 CAN_RX 是第 45 脚 PB8、CAN_TX 是第 46 脚 PB9；第 32、33 脚 PA11/PA12 是复位默认，也是 USB 的 D- 和 D+。",
                size=12, fill=T.TEXT)

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

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Static B4 figure for chapter 14: the USB descriptor tree of examples/usb-cdc.

One figure, 960x880, text-only SVG drawn with tools/svgkit.py:

    sample-14-descriptor-map.svg   type (2) technical relationship

Every number comes from docs/14-USB.md: device descriptor 18 bytes, configuration set
wTotalLength 67 (0x0043), VID/PID 0x1209/0x0001, bMaxPacketSize0 64, bMaxPower 0x32 =
100 mA, bulk 64 bytes, notification endpoint 8 bytes, PMA 512 bytes, EP0-EP7.

No CSS animation and no SMIL.

    python tools/sample_figs_b4/ch14_b4.py assets/diagrams
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


def descriptor_map() -> Svg:
    canvas = Svg(
        960,
        880,
        "设备描述符 18 字节，配置集合 67 字节 = 9+9+5+5+4+5+7+9+7+7，VID/PID 0x1209/0x0001，批量端点 64 字节、通知端点 8 字节",
        "STM32F103C8T6 · chapter 14 · RM0008 Rev 21 ch.23 USB device",
    )
    canvas.header(title="描述符树：18 字节设备，67 字节配置集合", tag="14", tag_color=T.CYAN)
    canvas.text(40, 86, "设备描述符 18 字节 → 配置集合 67 字节（0x0043）→ 2 个接口 → 4 个端点",
                size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "one device, one configuration set, two interfaces, four endpoints; every bLength must add up",
                size=14, fill=T.CYAN)
    canvas.text(40, 138, "18 = device    67 = 9 config + 9 interface + 19 CDC class + 7 EP + 9 interface + 7 EP + 7 EP",
                size=13, fill=T.AMBER, mono=True)

    canvas.text(40, 176, "层级  设备 → 配置 → 接口 → 端点", size=16, fill=T.CYAN, weight="700")
    canvas.line(56, 248, 56, 674, stroke=T.STROKE, sw=1.5)
    canvas.box(40, 190, 520, 58, label="设备描述符 Device  18 B",
               sub="bMaxPacketSize0 = 64 · 1 个配置 · class 0x02", stroke=T.CYAN, size=15)
    canvas.text(72, 270, "VID 0x1209 · PID 0x0001 · bcdUSB 0x0200", size=13, fill=T.AMBER, mono=True)
    canvas.line(56, 311, 72, 311, stroke=T.STROKE, sw=1.5)
    canvas.box(72, 282, 488, 58, label="配置描述符 Config  9 B",
               sub="wTotalLength = 0x0043 = 67 · bMaxPower 0x32 = 100 mA", stroke=T.GREEN, size=15)
    canvas.line(56, 403, 104, 403, stroke=T.STROKE, sw=1.5)
    canvas.box(104, 374, 456, 58, label="接口 0 Interface  9 B",
               sub="CDC 控制 · class 0x02 / subclass 0x02 / protocol 0x01", stroke=T.VIOLET, size=15)
    canvas.line(56, 482, 136, 482, stroke=T.STROKE, sw=1.5)
    canvas.box(136, 456, 424, 52, label="CDC 功能描述符  19 B",
               sub="header 5 + call mgmt 5 + ACM 4 + union 5", stroke=T.VIOLET, size=14)
    canvas.line(56, 546, 136, 546, stroke=T.STROKE, sw=1.5)
    canvas.box(136, 520, 424, 52, label="端点 0x81 IN  7 B",
               sub="中断 · wMaxPacketSize 8 · bInterval 0x10 = 16 ms", stroke=T.AMBER, size=14)
    canvas.line(56, 610, 104, 610, stroke=T.STROKE, sw=1.5)
    canvas.box(104, 584, 456, 52, label="接口 1 Interface  9 B",
               sub="数据类 · class 0x0A · 2 个端点", stroke=T.VIOLET, size=14)
    canvas.line(56, 674, 136, 674, stroke=T.STROKE, sw=1.5)
    canvas.line(136, 674, 460, 674, stroke=T.STROKE, sw=1.5)
    canvas.box(136, 648, 200, 52, label="端点 0x02 OUT  7 B", sub="批量 · 64 B", stroke=T.AMBER, size=13)
    canvas.box(360, 648, 200, 52, label="端点 0x82 IN  7 B", sub="批量 · 64 B", stroke=T.AMBER, size=13)

    canvas.text(580, 176, "67 字节怎么分", size=15, fill=T.GREEN, weight="700")
    segs = ((9, T.CYAN), (9, T.GREEN), (19, T.VIOLET), (7, T.AMBER),
            (9, T.GREEN), (7, T.AMBER), (7, T.AMBER))
    left, run = 580.0, 0
    for count, fill in segs:
        seg_w = 340.0 * count / 67.0
        canvas.rect(left, 190, seg_w, 34, fill=fill, rx=2)
        canvas.text(left + seg_w / 2, 212, str(count), size=11, fill=T.BG,
                    anchor="middle", weight="700")
        left += seg_w
        run += count
    assert run == 67, run
    canvas.text(580, 248, "9 config · 9 interface 0 · 19 CDC class", size=12, fill=T.MUTED)
    canvas.text(580, 270, "7 EP 0x81 · 9 interface 1 · 7 EP 0x02 · 7 EP 0x82", size=12, fill=T.MUTED)

    canvas.text(580, 306, "对不上就停在这里", size=14, fill=T.RED, weight="700")
    rules = (
        "18 counts the device only",
        "67 counts the whole config set",
        "bLength: 9 config/interface, 7 EP",
        "step 3: 8 bytes, bMaxPacketSize0 = 64",
        "step 5: 18; step 6: 9 then 67",
        "EP0 is the only two-way pipe",
        "0x81, 0x02, 0x82 are one-way",
        "all buffers share 512 B of PMA",
    )
    for i, line in enumerate(rules):
        canvas.text(580, 332 + i * 24, line, size=12, fill=T.TEXT)

    canvas.text(580, 546, "主机一次读多少", size=14, fill=T.CYAN, weight="700")
    reads = (("8 B", "bMaxPacketSize0"), ("18 B", "VID / PID"), ("9 B", "wTotalLength = 67"),
             ("67 B", "接口与端点"), ("Set", "配置选中，功能可用"))
    for i, (head, tail) in enumerate(reads):
        y = 572 + i * 26
        canvas.text(580, y, head, size=12, fill=T.AMBER, mono=True, weight="600")
        canvas.text(632, y, tail, size=12, fill=T.TEXT)

    canvas.rect(40, 714, 880, 96, fill=T.BG2, stroke=T.GREEN, rx=8)
    canvas.text(56, 744, "0x81 是通知管道 8 字节，0x02 / 0x82 是批量 64 字节；三者的缓冲区都在同一块 512 字节 PMA 里。",
                size=13, fill=T.TEXT)
    canvas.text(56, 770, "class 0x0A 的数据接口后面直接跟端点，没有类描述符；那 19 字节只挂在接口 0 上。",
                size=13, fill=T.TEXT)
    canvas.text(56, 796, "wTotalLength 写成 18 是最常见的错：它数的是整套配置，不是设备描述符。",
                size=13, fill=T.MUTED)

    _credit(canvas, "自绘。18 与 67 字节、VID/PID 与端点包长来自本仓库 examples/usb-cdc；层级与 PMA 来自 RM0008 Rev 21 第 23 章。")
    return canvas


FIGURES = [
    ("sample-14-descriptor-map.svg", descriptor_map),
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
    assert 840 <= height <= 900, (name, "height", height)
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

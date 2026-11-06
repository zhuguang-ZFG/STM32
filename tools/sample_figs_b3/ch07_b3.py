#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Static B3 figures for chapter 07: I2C bus triage.

No CSS animation and no SMIL.

    python tools/sample_figs_b3/ch07_b3.py assets/diagrams
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


def bus_triage() -> Svg:
    canvas = Svg(
        960,
        880,
        "I2C 三岔口：SDA 卡低先补 9 个 SCL，NACK 先查 7 位 / 8 位地址，SCL 不动是时钟拉伸",
        "STM32F103C8T6 · chapter 07 · UM10204 Rev 6 第 3 章 · RM0008 Rev 21 第 26 章",
    )
    canvas.header(tag="07", tag_color=T.CYAN)
    canvas.text(40, 86, "STM32F103C8T6  I2C1  PB6 = SCL  PB7 = SDA  both open-drain, 4.7 kΩ to 3.3 V",
                size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "three dead-bus symptoms; the branch is decided by which line is low when the bus should idle",
                size=14, fill=T.CYAN)
    canvas.text(40, 138, "SDA low + SCL high  →  bus clear    9th clock high  →  address    SCL low after release  →  stretch",
                size=13, fill=T.AMBER, mono=True)

    canvas.text(40, 170, "岔口一  SDA 卡低：最多 9 个 SCL 脉冲，再补 STOP", size=16, fill=T.RED, weight="700")
    canvas.rect(40, 184, 880, 220, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(56, 212, "SDA sits low while SCL idles high: no START can be formed, and every HAL call returns BUSY",
                size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 238, "a slave that lost power or froze mid-byte holds SDA down; the master must finish that byte",
                size=14, fill=T.TEXT)
    canvas.text(56, 262, "drive SCL as open-drain GPIO: up to 9 pulses, sampling SDA between clocks and stopping early",
                size=14, fill=T.TEXT)

    wx, wy, ww = 56, 272, 480
    scl_bits = [1, 0] * 9 + [1, 1]
    sda_bits = [0] * 17 + [1] * (len(scl_bits) - 17)
    canvas.waveform(wx, wy, ww, 30, scl_bits, color=T.RED, sw=2)
    canvas.waveform(wx, wy + 40, ww, 30, sda_bits, color=T.GREEN, sw=2)
    release_x = wx + ww * 17 / len(scl_bits)
    canvas.line(release_x, wy - 6, release_x, wy + 70, stroke=T.MUTED, sw=1, dash="4 4")
    canvas.text(548, wy + 21, "SCL: 9 clocks, GPIO open-drain", size=13, fill=T.RED)
    canvas.text(548, wy + 61, "SDA: slave releases on clock 9", size=13, fill=T.GREEN)
    canvas.text(548, wy + 84, "9 is the ceiling, not a target", size=11, fill=T.MUTED)

    canvas.text(56, 368, "then a real STOP: SDA low with SCL low → SCL high → SDA high; re-init I2C1 before retrying",
                size=13, fill=T.TEXT)
    canvas.text(56, 390, "8 data bits + 1 ACK is what frees the slave; a 10th pulse would look like another byte",
                size=13, fill=T.MUTED)

    canvas.text(40, 434, "岔口二  一直 NACK：7 位 0x3C 还是 8 位 0x78", size=16, fill=T.AMBER, weight="700")
    canvas.rect(40, 448, 880, 200, fill=T.PANEL, stroke=T.AMBER, rx=8)
    canvas.text(56, 476, "the bus is alive and the 9th clock stays high: no slave owns the address on the wire",
                size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 502, "7-bit 0x3C = 0111100; the first byte on the wire is A6..A0 plus R/W: write 0x78, read 0x79",
                size=14, fill=T.TEXT)
    canvas.text(56, 528, "driver macro keeps 0x3C; HAL_I2C_* is called with 0x3C << 1, and CR2 SADD carries those 8 bits",
                size=14, fill=T.TEXT)

    cell_w, pitch, cells_y = 40, 43, 544
    for i, bit in enumerate([0, 1, 1, 1, 1, 0, 0, 0]):
        is_rw = i == 7
        canvas.rect(56 + i * pitch, cells_y, cell_w, 26,
                    fill=T.PANEL2 if is_rw else T.BG,
                    stroke=T.AMBER if is_rw else T.STROKE, rx=2, sw=2 if is_rw else 1)
        canvas.text(56 + i * pitch + cell_w / 2, cells_y + 18, str(bit), size=14,
                    fill=T.AMBER if is_rw else T.TEXT, anchor="middle", weight="700", mono=True)
        canvas.text(56 + i * pitch + cell_w / 2, cells_y + 44,
                    "R/W" if is_rw else f"A{6 - i}", size=11, fill=T.MUTED, anchor="middle")
    canvas.text(420, 556, "scan tool prints the 7-bit address: 0x3C", size=13, fill=T.TEXT)
    canvas.text(420, 580, "HAL macro holds the shifted byte: (0x3C << 1) = 0x78", size=13, fill=T.TEXT)
    canvas.text(56, 622, "0x3C sent as-is is 7-bit 0x1E: nobody answers, so check both conventions before swapping the panel",
                size=14, fill=T.AMBER)

    canvas.text(40, 678, "岔口三  SCL 被拉低不动：先认时钟拉伸", size=16, fill=T.VIOLET, weight="700")
    canvas.rect(40, 692, 880, 150, fill=T.PANEL, stroke=T.VIOLET, rx=8)
    canvas.text(56, 720, "SCL stays low after the master lets go: the slave is stretching the clock, the bus is not dead",
                size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 745, "wait for SCL to rise; every I2C master must tolerate a stretched low", size=14, fill=T.TEXT)
    canvas.text(56, 770, "if it never rises: read SCL as GPIO, time it with a TIM, then run the 9-pulse clear", size=14, fill=T.TEXT)
    canvas.text(56, 795, "a stretched low can outlast the HAL timeout: prove the level first", size=13, fill=T.MUTED)
    # 拉伸时序小图：主机想放手，从机按住
    rx0 = 680
    canvas.text(rx0 - 10, 742, "SCL", size=11, fill=T.MUTED, anchor="end")
    canvas.line(rx0, 738, rx0 + 40, 738, stroke=T.GREEN, sw=2)
    canvas.line(rx0 + 40, 738, rx0 + 40, 758, stroke=T.GREEN, sw=2)
    canvas.line(rx0 + 40, 758, rx0 + 220, 758, stroke=T.RED, sw=2)
    canvas.line(rx0 + 40, 738, rx0 + 220, 738, stroke=T.MUTED, sw=1.5, dash="4 4")
    canvas.text(rx0 + 50, 782, "虚线 = 主机松手后的期望", size=10, fill=T.MUTED)
    canvas.text(rx0 + 50, 798, "从机按住：低电平更长", size=11, fill=T.RED)

    canvas.text(40, 828, "清除只还你一条空闲的线，不解释从机为何停在半个字节上", size=13, fill=T.MUTED)
    _credit(canvas, "自绘。总线清除与时钟拉伸来自 UM10204 Rev 6 第 3 章；I2C 寄存器语义来自 RM0008 Rev 21 第 26 章。")
    return canvas


FIGURES = [
    ("sample-07-i2c-triage.svg", bus_triage),
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

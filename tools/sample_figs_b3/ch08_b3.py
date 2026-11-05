#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Static B3/B7 figures for chapter 08: CPOL/CPHA modes, SPI triage, and bus compare.

No CSS animation and no SMIL.

    python tools/sample_figs_b3/ch08_b3.py assets/diagrams
"""

from __future__ import annotations

import hashlib
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from svgkit import Svg, T

from triage_plates import spi_triage  # shared plate drawing, one source of truth


def _credit(canvas: Svg, note: str) -> None:
    canvas.line(24, canvas.h - 36, canvas.w - 24, canvas.h - 36, stroke=T.GRID, sw=1)
    canvas.text(24, canvas.h - 16, note, size=11, fill=T.MUTED)
    canvas.text(canvas.w - 24, canvas.h - 16, "自绘 · 静态 · CC BY 4.0", size=11, fill=T.DIM, anchor="end")


def _spi_cell(canvas: Svg, x: float, y: float, w: float, h: float, mode: int,
              cpol: int, cpha: int, bits: list[int], accent: str, note: str,
              highlight: bool = False) -> None:
    """One 2x2 matrix cell: NSS, SCK and MOSI with the sampling edges marked."""
    canvas.rect(x, y, w, h, fill=T.PANEL, stroke=accent, rx=8, sw=2 if highlight else 1.5)
    canvas.text(x + 14, y + 24, f"Mode {mode}", size=15, fill=accent, weight="700")
    tag = f"CPOL={cpol}  CPHA={cpha}" + ("  most used" if mode == 0 else "")
    canvas.text(x + w - 14, y + 24, tag, size=11, mono=True, anchor="end",
                fill=T.GREEN if mode == 0 else T.MUTED)
    canvas.line(x + 14, y + 34, x + w - 14, y + 34, stroke=T.GRID, sw=1)

    lx = x + 14
    wx0 = x + 52
    wx1 = x + w - 16
    pre, post = wx0 - 12, wx1 + 10
    drop, rise = wx0 - 6, wx1 + 2
    period = (wx1 - wx0) / 4.0

    cs_hi, cs_lo = y + 50, y + 62
    sc_mid = y + 98
    sc_hi, sc_lo = sc_mid - 14, sc_mid + 14
    mo_mid = y + 150
    mo_hi, mo_lo = mo_mid - 11, mo_mid + 11

    canvas.text(lx, cs_hi + 4, "NSS", size=10, mono=True, fill=T.DIM)
    canvas.text(lx, sc_mid + 4, "SCK", size=10, mono=True, fill=T.DIM)
    canvas.text(lx, mo_mid + 4, "MOSI", size=10, mono=True, fill=T.DIM)

    # sampling edges: CPHA = 0 -> first edge of each clock, CPHA = 1 -> second edge
    samples = [wx0 + i * period + (0.0 if cpha == 0 else period / 2) for i in range(4)]
    for sx in samples:
        canvas.line(sx, y + 76, sx, mo_lo + 4, stroke=T.AMBER, sw=1, dash="3 3", opacity=0.5)

    # NSS: low for the whole transfer, high between commands
    canvas.poly([(pre, cs_hi), (drop, cs_hi), (drop, cs_lo), (rise, cs_lo),
                 (rise, cs_hi), (post, cs_hi)], stroke=T.VIOLET, sw=1.5)

    # SCK: idle level from CPOL, one pulse per bit
    if cpol == 0:
        clock = [(pre, sc_lo)]
        for i in range(4):
            a = wx0 + i * period
            clock += [(a, sc_lo), (a, sc_hi), (a + period / 2, sc_hi),
                      (a + period / 2, sc_lo), (a + period, sc_lo)]
        clock.append((post, sc_lo))
    else:
        clock = [(pre, sc_hi)]
        for i in range(4):
            a = wx0 + i * period
            clock += [(a, sc_hi), (a, sc_lo), (a + period / 2, sc_lo),
                      (a + period / 2, sc_hi), (a + period, sc_hi)]
        clock.append((post, sc_hi))
    canvas.poly(clock, stroke=T.CYAN, sw=2)

    # sample dots sit on the clock level reached at that edge
    for sx in samples:
        level = (sc_hi if cpol == 0 else sc_lo) if cpha == 0 else (sc_hi if cpol == 1 else sc_lo)
        canvas.circle(sx, level, 3, fill=T.AMBER, stroke=T.PANEL, sw=1)

    # MOSI: CPHA = 0 changes on the trailing edge, CPHA = 1 on the leading edge
    if cpha == 0:
        bounds = [wx0, wx0 + period / 2, wx0 + 1.5 * period, wx0 + 2.5 * period, wx1]
    else:
        bounds = [wx0, wx0 + period, wx0 + 2 * period, wx0 + 3 * period, wx1]
    level0 = mo_hi if bits[0] else mo_lo
    mosi = [(pre, level0)]
    for i, bit in enumerate(bits):
        level = mo_hi if bit else mo_lo
        mosi += [(bounds[i], level), (bounds[i + 1], level)]
    mosi.append((post, mo_hi if bits[-1] else mo_lo))
    canvas.poly(mosi, stroke=T.GREEN, sw=2)

    canvas.text(x + 14, y + h - 12, note, size=11, fill=T.AMBER)


def cpha_modes() -> Svg:
    canvas = Svg(
        960,
        880,
        "CPOL 定空闲电平，CPHA 定第几个边沿采样：四种模式只是 CR1 里的两位",
        "STM32F103C8T6 · chapter 08 · RM0008 Rev 21 第 25 章",
    )
    canvas.header(tag="08", tag_color=T.CYAN)
    canvas.text(40, 86, "STM32F103C8T6  SPI1 on APB2 72 MHz   CPOL = CR1 bit 1   CPHA = CR1 bit 0",
                size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "CPOL sets the idle level; CPHA picks the edge that samples: edge 1 for CPHA = 0, edge 2 for CPHA = 1",
                size=14, fill=T.CYAN)
    canvas.text(40, 138, "BR=000 → 72 / 2 = 36 MHz        BR=010 → 72 / 8 = 9 MHz",
                size=13, fill=T.AMBER, mono=True)

    canvas.text(338, 170, "CPOL = 0 · 空闲低", size=14, fill=T.TEXT, weight="700", anchor="middle")
    canvas.text(730, 170, "CPOL = 1 · 空闲高", size=14, fill=T.TEXT, weight="700", anchor="middle")

    canvas.text(40, 284, "CPHA = 0", size=14, fill=T.TEXT, weight="700")
    canvas.text(40, 306, "第 1 个边沿采样", size=11, fill=T.MUTED)
    canvas.text(40, 496, "CPHA = 1", size=14, fill=T.TEXT, weight="700")
    canvas.text(40, 518, "第 2 个边沿采样", size=11, fill=T.MUTED)

    bits = [1, 0, 1, 1]
    _spi_cell(canvas, 148, 186, 380, 204, 0, 0, 0, bits, T.GREEN,
              "sample on edge 1 (rising); shift on edge 2 (falling)", highlight=True)
    _spi_cell(canvas, 540, 186, 380, 204, 2, 1, 0, bits, T.VIOLET,
              "sample on edge 1 (falling); shift on edge 2 (rising)")
    _spi_cell(canvas, 148, 398, 380, 204, 1, 0, 1, bits, T.AMBER,
              "sample on edge 2 (falling); shift on edge 1 (rising)")
    _spi_cell(canvas, 540, 398, 380, 204, 3, 1, 1, bits, T.CYAN,
              "sample on edge 2 (rising); shift on edge 1 (falling)")

    canvas.text(40, 644, "读法  边沿编号跟着 CPOL 走，CPHA 只数第几个", size=16, fill=T.CYAN, weight="700")
    canvas.rect(40, 656, 880, 68, fill=T.PANEL, stroke=T.CYAN, rx=8)
    canvas.text(56, 684, "edge 1 is the first transition after NSS falls: rising when CPOL = 0, falling when CPOL = 1",
                size=14, fill=T.TEXT)
    canvas.text(56, 710, "CPHA = 1 samples edge 2, half a clock later; the slave still answers, so the bytes look plausible",
                size=14, fill=T.TEXT)

    canvas.text(40, 766, "底注  Mode 0 (0,0) 最通用", size=16, fill=T.VIOLET, weight="700")
    canvas.rect(40, 778, 880, 50, fill=T.BG2, stroke=T.VIOLET, rx=8)
    canvas.text(56, 806, "W25Q64, ST7789 and most parts here run Mode 0; Mode 3 is the other common choice, Mode 1/2 are rare",
                size=14, fill=T.TEXT)
    _credit(canvas, "自绘。CPOL/CPHA 采样边沿与分频定义来自 RM0008 Rev 21 第 25 章。")
    return canvas



def bus_compare() -> Svg:
    """SPI / I2C / UART side-by-side: wires, addressing, duplex, first pick."""
    canvas = Svg(
        960,
        880,
        "SPI / I2C / UART 总线对照：线数、寻址与双工不能混用",
        "STM32F103C8T6 · chapter 08 · 对照第 06 / 07 / 08 章，不替代各章验收",
    )
    canvas.header(title="SPI / I2C / UART 三总线对照：先问线、再问寻址、最后才问速率",
                  tag="08", tag_color=T.CYAN)
    canvas.text(40, 88, "同一「通信」词，电气与主机关系完全不同——抄接线之前先对这一表",
                size=15, fill=T.TEXT, weight="700")
    canvas.text(40, 114, "compare · wire count · multi-drop · duplex · who drives the clock",
                size=13, fill=T.CYAN)

    buses = [
        ("SPI", "4 线", "SCK+MOSI+MISO+CS", "每从机一根 CS", "全双工移位",
         "主机驱动 SCK", "Flash / 显示屏", T.CYAN),
        ("I2C", "2 线", "SCL + SDA（开漏）", "7/10 位地址", "半双工共享",
         "主机驱动 SCL", "传感器 / EEPROM", T.GREEN),
        ("UART", "2 线", "TX + RX（+GND）", "点对点（无总线地址）", "全双工异步",
         "双方自有波特率", "调试打印 / 模组", T.AMBER),
    ]
    heads = ("总线", "线数", "信号", "多设备", "双工", "时钟/节拍", "典型负载")
    xs = [40, 120, 230, 420, 580, 720, 860]
    # widths derived from xs; last col to 920
    rights = [120, 230, 420, 580, 720, 860, 920]
    widths = [rights[i] - xs[i] for i in range(7)]
    y0 = 140
    for i, h in enumerate(heads):
        canvas.rect(xs[i], y0, widths[i], 40, fill=T.BG2, stroke=T.STROKE, rx=4)
        canvas.text(xs[i] + widths[i] / 2, y0 + 26, h, size=13, fill=T.MUTED,
                    anchor="middle", weight="700")
    for r, row in enumerate(buses):
        name, wires, signals, multi, duplex, clock, load, color = row
        vals = (name, wires, signals, multi, duplex, clock, load)
        y = y0 + 52 + r * 110
        for i, val in enumerate(vals):
            canvas.rect(
                xs[i], y, widths[i], 98,
                fill=T.PANEL,
                stroke=color if i == 0 else T.STROKE,
                rx=8,
                sw=2 if i == 0 else 1.5,
            )
            size = 16 if i == 0 else 13
            canvas.text(
                xs[i] + widths[i] / 2, y + 52, val,
                size=size, fill=color if i == 0 else T.TEXT,
                anchor="middle", weight="700" if i == 0 else "400",
            )

    canvas.text(40, 530, "选型口诀（本章只钉 SPI 验收，其余见对章）", size=15,
                fill=T.TEXT, weight="700")
    tips = [
        (T.CYAN, "要高速 + 全双工 + 可拉片选", "选 SPI；CS 必须整事务保持低，否则读回 0xFF"),
        (T.GREEN, "要少线 + 多从机地址", "选 I2C；开漏上拉与 ACK 是硬门槛，见第 07 章"),
        (T.AMBER, "要异步点对点 / 打印", "选 UART；双方波特率各自负责，见第 06 章"),
    ]
    for i, (color, title, body) in enumerate(tips):
        y = 548 + i * 70
        canvas.rect(40, y, 880, 60, fill=T.BG2, stroke=color, rx=8)
        canvas.text(56, y + 24, title, size=14, fill=color, weight="700")
        canvas.text(56, y + 46, body, size=13, fill=T.TEXT)

    canvas.rect(40, 760, 880, 56, fill=T.PANEL, stroke=T.GREEN, rx=8)
    canvas.text(56, 784, "对照边界：本图只整理线数/寻址/双工关系，不替代 RM0008 第 25/26/27 章时序与寄存器。",
                size=13, fill=T.TEXT)
    canvas.text(56, 804, "开源对照：配套 examples/spi-flash（MIT）只提供结构与验收格式，不替代本表与手册。",
                size=12, fill=T.MUTED)
    _credit(canvas, "自绘 · SPI/I2C/UART 三总线对照 · 非实拍")
    return canvas


FIGURES = [
    ("sample-08-cpha-modes.svg", cpha_modes),
    ("sample-08-spi-triage.svg", spi_triage),
    ("sample-08-bus-compare.svg", bus_compare),
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

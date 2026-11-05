#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Static B4 figures for chapter 12: Flash erase/program triage and boot-area comparison.

Two figures, both 960x880, text-only SVG drawn with tools/svgkit.py:

    sample-12-flash-triage.svg   type (3) troubleshooting, three-branch fork
    sample-12-boot-compare.svg   type (3) comparison, two boot areas side by side

Every number on the canvas comes from docs/12-Flash与IAP升级.md: 64 KB / 1 KB pages /
64 pages / last page 0x0800FC00 / app 0x08004800 length 0xB800 (46 KB, 46 pages) /
erased half-word 0xFFFF / keys 0x45670123 then 0xCDEF89AB / readout 0xA5.

No CSS animation and no SMIL.

    python tools/sample_figs_b4/ch12_b4.py assets/diagrams
"""

from __future__ import annotations

import hashlib
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from svgkit import Svg, T

from triage_plates import flash_triage  # shared plate drawing, one source of truth


def _credit(canvas: Svg, note: str) -> None:
    canvas.line(24, canvas.h - 36, canvas.w - 24, canvas.h - 36, stroke=T.GRID, sw=1)
    canvas.text(24, canvas.h - 16, note, size=11, fill=T.MUTED)
    canvas.text(canvas.w - 24, canvas.h - 16, "自绘 · 静态 · CC BY 4.0", size=11, fill=T.DIM, anchor="end")



def boot_compare() -> Svg:
    canvas = Svg(
        960,
        880,
        "常驻 Bootloader 走 0x08000000 的 16 KB，出厂系统存储器不占这 64 KB；两条路都在复位时选好，之后共用 0x08004800 的 46 KB",
        "STM32F103C8T6 · chapter 12 · RM0008 Rev 21 ch.3",
    )
    canvas.header(title="两条引导路径：自写 Bootloader 与出厂系统存储器",
                  tag="12", tag_color=T.CYAN)

    # ① 64 KB 分区图
    canvas.text(24, 82, "先看这块 64 KB：两条路要在同一张地图上比较", size=12.5,
                fill=T.TEXT, weight="700")
    bx, bw = 24, 800
    canvas.text(bx, 100, "", size=9.5, fill=T.MUTED, mono=True)
    parts = [("Bootloader", "16 KB · 16 页", 16, T.GREEN),
             ("参数", "2 KB · 2 页", 2, T.AMBER),
             ("APP", "46 KB · 0xB800", 46, T.VIOLET)]
    x = bx
    for name, note, kb, color in parts:
        w = bw * kb / 64
        canvas.rect(x, 106, w - 2, 44, fill=color, rx=4, opacity=0.24)
        canvas.rect(x, 106, w - 2, 44, fill="none", stroke=color, sw=1.5, rx=4)
        if kb >= 8:
            canvas.text(x + 8, 126, name, size=11, fill=color, weight="700")
            canvas.text(x + 8, 142, note, size=8.5, fill=T.TEXT)
        x += w
    canvas.text(bx, 172, "0x08000000", size=9, fill=T.MUTED, mono=True)
    canvas.text(bx + bw * 16 / 64 - 6, 172, "0x08004000", size=8.5, fill=T.MUTED,
                anchor="end", mono=True)
    canvas.text(bx + bw * 18 / 64 + 2, 172, "0x08004800", size=8.5, fill=T.MUTED,
                mono=True)
    canvas.text(bx + bw, 172, "0x08010000", size=9, fill=T.MUTED, anchor="end",
                mono=True)
    canvas.line(bx, 160, bx + bw, 160, stroke=T.GRID, sw=1)
    # 2 KB 参数区太窄，文字改在上方引线标注
    px_par = bx + bw * 17 / 64
    canvas.line(px_par, 106, px_par, 68, stroke=T.AMBER, sw=1)
    canvas.text(px_par + 6, 64, "参数区 2 KB · 2 页（0x08004000）", size=9, fill=T.AMBER)
    # 片外：系统存储器
    canvas.rect(848, 106, 88, 44, fill=T.RED, rx=4, opacity=0.18)
    canvas.rect(848, 106, 88, 44, fill="none", stroke=T.RED, sw=1.5, rx=4)
    canvas.text(892, 124, "系统存储器", size=9.5, anchor="middle", fill=T.RED,
                weight="700")
    canvas.text(892, 140, "0x1FFFF000", size=9, anchor="middle", fill=T.TEXT,
                mono=True)
    canvas.text(892, 172, "不占这 64 KB", size=9, anchor="middle", fill=T.MUTED)

    # ② 两条路径
    py, ph = 196, 250
    cards = [
        (24, T.GREEN, "路径甲  自写 Bootloader 常驻用户闪存", [
            ("复位锁存", "BOOT0 = 0，之后一直保持"),
            ("首次取指", "0x08000000（主闪存）"),
            ("刷写通道", "串口 PA9 / PA10 —— 第 30 / 31 脚"),
            ("账", "16 + 2 = 18 KB，占掉 28%"),
            ("交接", "MSP、0x08004804、VTOR 三处都改"),
        ], "examples/iap-bootloader"),
        (504, T.RED, "路径乙  芯片自带系统存储器（出厂）", [
            ("复位锁存", "BOOT1 = 0 且 BOOT0 = 1"),
            ("首次取指", "系统存储器，在 64 KB 之外"),
            ("刷写通道", "出厂固件自带的串口/USB 协议"),
            ("账", "这 64 KB 一格不占"),
            ("交接", "BOOT0 拨回 0，再复位一次"),
        ], "本书只作对照，不依赖它"),
    ]
    for cx, color, title, rows, foot in cards:
        canvas.rect(cx, py, 432, ph, fill=T.PANEL, stroke=color, rx=8)
        canvas.rect(cx, py, 432, 5, fill=color, rx=2)
        canvas.text(cx + 14, py + 26, title, size=12.5, fill=T.TEXT, weight="700")
        for i, (key, val) in enumerate(rows):
            y = py + 54 + i * 34
            canvas.text(cx + 14, y, key, size=9.5, fill=color)
            canvas.text(cx + 96, y, val, size=10, fill=T.TEXT)
        canvas.text(cx + 14, py + ph - 14, foot, size=9, fill=T.MUTED)

    # ③ 同一个槽位
    hy = 470
    canvas.text(24, hy, "分水岭：两条路都必须把控制权交到同一个槽位", size=12.5,
                fill=T.VIOLET, weight="700")
    canvas.rect(24, hy + 12, 912, 96, fill=T.PANEL, stroke=T.VIOLET, rx=8)
    canvas.arrow(240, py + ph, 300, hy + 12, color=T.GREEN, sw=1.5, head=6)
    canvas.arrow(720, py + ph, 660, hy + 12, color=T.RED, sw=1.5, head=6)
    checks = [("链接脚本", "起始 0x08004800"), ("向量表", "SCB->VTOR = 0x08004800"),
              ("头两个字", "MSP / 0x08004804")]
    for i, (key, val) in enumerate(checks):
        x = 40 + i * 296
        canvas.rect(x, hy + 26, 276, 40, fill=T.BG2, stroke=T.VIOLET, rx=4)
        canvas.text(x + 12, hy + 42, key, size=9.5, fill=T.VIOLET)
        canvas.text(x + 12, hy + 58, val, size=10, fill=T.TEXT, mono=True)
    canvas.text(40, hy + 92, "三处只改一处，APP 的中断仍会跳回 Bootloader 的向量表",
                size=9.5, fill=T.MUTED)

    # ④ 各自的失败长相
    fy = 600
    canvas.text(24, fy, "两条路坏掉的样子不一样", size=12.5, fill=T.TEXT,
                weight="700")
    fails = [(T.GREEN, "甲 坏在钥匙顺序", ["0x45670123 与 0xCDEF89AB 写反，", "或半字写成了字 → 写保护不动"]),
             (T.RED, "乙 坏在 BOOT0 忘了拨回", ["下次复位仍进系统存储器，", "APP 永远不跑，却不像坏了"])]
    for i, (color, head, lines) in enumerate(fails):
        x = 24 + i * 462
        canvas.rect(x, fy + 12, 450, 74, fill=T.PANEL, stroke=color, rx=8)
        canvas.text(x + 14, fy + 34, head, size=10.5, fill=color, weight="700")
        for j, line in enumerate(lines):
            canvas.text(x + 14, fy + 54 + j * 16, line, size=9.5, fill=T.TEXT)

    # ⑤ 选择与边界
    canvas.rect(24, 704, 912, 66, fill=T.BG2, stroke=T.GREEN, rx=8)
    canvas.text(40, 728, "能改 Bootloader 就走甲；板子焊死、只想救砖才拨乙。", size=11,
                fill=T.TEXT)
    canvas.text(40, 750, "两者都不证明 APP 真的跑起来 —— 心跳在应用里，不在引导区。",
                size=11, fill=T.MUTED)

    _credit(canvas, "自绘。分区、页与钥匙来自 RM0008 Rev 21 第 3 章；两字来自 PM0056；BOOT 脚口径来自第 00、01 章。")
    return canvas


FIGURES = [
    ("sample-12-flash-triage.svg", flash_triage),
    ("sample-12-boot-compare.svg", boot_compare),
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

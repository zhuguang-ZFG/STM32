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


def _credit(canvas: Svg, note: str) -> None:
    canvas.line(24, canvas.h - 36, canvas.w - 24, canvas.h - 36, stroke=T.GRID, sw=1)
    canvas.text(24, canvas.h - 16, note, size=11, fill=T.MUTED)
    canvas.text(canvas.w - 24, canvas.h - 16, "自绘 · 静态 · CC BY 4.0", size=11, fill=T.DIM, anchor="end")


def flash_triage() -> Svg:
    canvas = Svg(
        960,
        880,
        "擦除报错先读 CR.LOCK 与 1 KB 页边界；写不进去看半字与 0xFFFF；读回不对按 0x08004800、0xB800 逐页比对",
        "STM32F103C8T6 · chapter 12 · RM0008 Rev 21 ch.3",
    )
    canvas.header(title="擦写三岔口：擦不掉、写不进、读不回", tag="12", tag_color=T.CYAN)
    canvas.text(40, 86, "STM32F103C8T6  64 KB 闪存 · 1 KB 页共 64 页（0–63）· 第 63 页从 0x0800FC00 起",
                size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "three failures in the order the controller reports them: erase, program, read back",
                size=14, fill=T.CYAN)
    canvas.text(40, 138, "CR.LOCK · CR.PER · CR.PG · CR.STRT    SR.BSY · SR.EOP · SR.PGERR    keys 0x45670123 then 0xCDEF89AB",
                size=13, fill=T.AMBER, mono=True)

    canvas.text(40, 170, "岔口一  擦除没生效：SR 报错，或页里还是旧数据", size=16, fill=T.RED, weight="700")
    canvas.text(920, 170, "CR.LOCK · CR.PER · SR.BSY", size=11, fill=T.MUTED, anchor="end", mono=True)
    canvas.rect(40, 184, 880, 196, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(56, 214, "symptom: the page still holds old bytes, or SR comes back with an error after STRT",
                size=14, fill=T.TEXT)
    canvas.text(56, 240, "cause A: KEY2 was written before KEY1 — CR.LOCK stays 1 and every erase returns an error",
                size=14, fill=T.TEXT)
    canvas.text(56, 266, "cause B: the address is not on a 1 KB page boundary — 0x08004800 is; 0x08004400 is; 0x08004200 is not",
                size=14, fill=T.TEXT)
    canvas.text(56, 292, "cause C: STRT was set while SR.BSY was still 1; the second command is dropped",
                size=14, fill=T.TEXT)
    canvas.text(56, 318, "checkpoint: read CR.LOCK = 0 first, then use an address whose low 10 bits are 0, and poll SR.BSY",
                size=14, fill=T.TEXT)
    canvas.text(56, 344, "probe: erase one page and read it back — 0xFFFF everywhere means the erase itself worked",
                size=13, fill=T.MUTED)

    canvas.text(40, 412, "岔口二  写不进去：SR.PGERR，或只有一半落盘", size=16, fill=T.AMBER, weight="700")
    canvas.text(920, 412, "CR.PG · SR.PGERR", size=11, fill=T.MUTED, anchor="end", mono=True)
    canvas.rect(40, 426, 880, 196, fill=T.PANEL, stroke=T.AMBER, rx=8)
    canvas.text(56, 456, "symptom: the half-word write returns an error, or a 32-bit store leaves only 16 bits changed",
                size=14, fill=T.TEXT)
    canvas.text(56, 482, "cause A: the address is odd — this C8 programs half-words at even addresses only, never bytes",
                size=14, fill=T.TEXT)
    canvas.text(56, 508, "cause B: the target is not 0xFFFF yet; programming only turns 1 into 0, so a rewrite needs an erase",
                size=14, fill=T.TEXT)
    canvas.text(56, 534, "cause C: CR.PG was never set, so the store ran as ordinary memory access and nothing was programmed",
                size=14, fill=T.TEXT)
    canvas.text(56, 560, "checkpoint: erase the page, read 0xFFFF, then write one 32-bit value as two half-words",
                size=14, fill=T.TEXT)
    canvas.text(56, 586, "probe: read back the whole 0xB800 range from 0x08004800; one wrong half-word marks its page",
                size=13, fill=T.MUTED)

    canvas.text(40, 650, "岔口三  读回不对：写说成功，比对失败", size=16, fill=T.VIOLET, weight="700")
    canvas.text(920, 650, "0xB800 · 0x08010000", size=11, fill=T.MUTED, anchor="end", mono=True)
    canvas.rect(40, 664, 880, 150, fill=T.PANEL, stroke=T.VIOLET, rx=8)
    canvas.text(56, 694, "symptom: every step looks clean, yet the CRC over the app does not match",
                size=14, fill=T.TEXT)
    canvas.text(56, 720, "cause A: the last page was written as 0x0801FC00 — that address is not in this 64 KB at all",
                size=14, fill=T.TEXT)
    canvas.text(56, 746, "cause B: read-out protection was put back to 0xA5, and that transition mass-erases the whole Flash",
                size=14, fill=T.TEXT)
    canvas.text(56, 772, "checkpoint: 46 pages from 0x08004800 to 0x08010000, 0xB800 bytes — compare page by page, not once",
                size=13, fill=T.MUTED)

    _credit(canvas, "自绘。页、半字与钥匙来自 RM0008 Rev 21 第 3 章；读保护 0xA5 来自 PM0075。")
    return canvas


def boot_compare() -> Svg:
    canvas = Svg(
        960,
        880,
        "常驻 Bootloader 走 0x08000000 的 16 KB，出厂系统存储器不占这 64 KB；两条路都在复位时选好，之后共用 0x08004800 的 46 KB",
        "STM32F103C8T6 · chapter 12 · RM0008 Rev 21 ch.3",
    )
    canvas.header(title="两条引导路径：自写 Bootloader 与出厂系统存储器", tag="12", tag_color=T.CYAN)
    canvas.text(40, 86, "STM32F103C8T6  64 KB · Bootloader 16 KB（16 页）+ 参数区 2 KB（2 页）+ APP 46 KB（0xB800）",
                size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "the same 46 KB app slot, two different things that can run before it",
                size=14, fill=T.CYAN)
    canvas.text(40, 138, "path A: BOOT0 = 0, reset runs 0x08000000      path B: BOOT0 = 1, reset runs the system memory",
                size=13, fill=T.AMBER, mono=True)

    canvas.text(40, 170, "路径甲  自写 Bootloader 常驻用户闪存", size=15, fill=T.GREEN, weight="700")
    canvas.text(490, 170, "路径乙  芯片自带系统存储器（出厂）", size=15, fill=T.RED, weight="700")
    canvas.rect(40, 184, 430, 216, fill=T.PANEL, stroke=T.GREEN, rx=8)
    canvas.rect(490, 184, 430, 216, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.line(475, 190, 475, 394, stroke=T.GRID, sw=1, dash="4 4")
    canvas.text(56, 214, "first fetch: 0x08000000, main Flash", size=14, fill=T.TEXT)
    canvas.text(56, 240, "BOOT0 = 0, left there for good", size=14, fill=T.TEXT)
    canvas.text(56, 266, "16 KB + 2 KB params = 18 KB spent", size=14, fill=T.TEXT)
    canvas.text(56, 292, "app at 0x08004800, 0xB800 long", size=14, fill=T.TEXT)
    canvas.text(56, 318, "update over PA9 / PA10, pins 30 / 31", size=14, fill=T.TEXT)
    canvas.text(56, 344, "hand over: MSP, 0x08004804, VTOR", size=14, fill=T.TEXT)
    canvas.text(56, 370, "this repo: examples/iap-bootloader", size=13, fill=T.MUTED)
    canvas.text(506, 214, "first fetch: system memory, outside 64 KB", size=14, fill=T.TEXT)
    canvas.text(506, 240, "BOOT1 = 0 and BOOT0 = 1 at reset", size=14, fill=T.TEXT)
    canvas.text(506, 266, "0 KB of the 64 KB map: it lives outside", size=14, fill=T.TEXT)
    canvas.text(506, 292, "app still at 0x08004800, 0xB800", size=14, fill=T.TEXT)
    canvas.text(506, 318, "update channel: the factory firmware", size=14, fill=T.TEXT)
    canvas.text(506, 344, "hand over: BOOT0 back to 0, then reset", size=14, fill=T.TEXT)
    canvas.text(506, 370, "this repo: not used, only the contrast", size=13, fill=T.MUTED)

    canvas.text(40, 428, "分水岭  两条路都会交到同一个槽位", size=16, fill=T.VIOLET, weight="700")
    canvas.rect(40, 442, 880, 132, fill=T.PANEL, stroke=T.VIOLET, rx=8)
    canvas.text(56, 472, "same app slot: either path must hand over to 0x08004800 with MSP and VTOR set",
                size=14, fill=T.TEXT)
    canvas.text(56, 498, "different bill: path A spends 18 of the 64 KB, path B spends none of it",
                size=14, fill=T.TEXT)
    canvas.text(56, 524, "different failure: path A breaks on key order or the two words; path B fails when BOOT0",
                size=14, fill=T.TEXT)
    canvas.text(56, 550, "is still 1 at the next reset, so the app slot never runs and nothing looks wrong",
                size=14, fill=T.TEXT)

    canvas.text(40, 604, "复位那一刻  先锁存电平，再取指", size=16, fill=T.CYAN, weight="700")
    canvas.rect(40, 618, 880, 104, fill=T.PANEL, stroke=T.CYAN, rx=8)
    canvas.text(56, 648, "reset samples the BOOT pins once; the alias at 0x00000000 decides what runs next",
                size=14, fill=T.TEXT)
    canvas.text(56, 674, "path A: the alias lands on 0x08000000 — your bootloader, app waiting at 0x08004800",
                size=14, fill=T.TEXT)
    canvas.text(56, 700, "path B: the alias lands on the system memory — your Flash is still there, never fetched",
                size=14, fill=T.TEXT)

    canvas.rect(40, 738, 880, 78, fill=T.BG2, stroke=T.GREEN, rx=8)
    canvas.text(56, 762, "选哪条：能改 Bootloader 就走甲；板子焊死、只想救砖才拨乙。",
                size=13, fill=T.TEXT)
    canvas.text(56, 786, "甲必须让 0x08004800、0xB800 和 VTOR 三处一致；乙要的是跳线，不是链接脚本。",
                size=13, fill=T.TEXT)
    canvas.text(56, 808, "两者都不证明 APP 真的跑起来——心跳在应用里，不在引导区。",
                size=13, fill=T.MUTED)

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

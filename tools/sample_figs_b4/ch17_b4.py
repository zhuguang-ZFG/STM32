#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Static B4 figures for chapter 17: observation instruments and perf triage.

No CSS animation and no SMIL.

    python tools/sample_figs_b4/ch17_b4.py assets/diagrams
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


# ---------------------------------------------------------------- figure 1
# Three instruments side by side. Each column carries the same four rows, so a
# reader compares across at one y and reads down for one tool.
COLS = [
    (
        T.RED,
        "断点停机",
        "Halt at a breakpoint",
        [
            ("对时序的干扰", ["命中即停住内核；软件", "断点还要由调试器改写", "Flash，断点处的内容", "会短暂改变"]),
            ("能看见什么", ["命中那一刻的寄存器", "与内存：CFSR、BFAR", "可以当场读出来"]),
            ("适用故障", ["确定的代码路径与单", "个变量；数据观察点", "只有 2~4 个"]),
            ("前提与代价", ["M3 有 6 个硬件断点，", "M7 有 8 个；打到第 7", "个会报错或不停"]),
        ],
        "停在命中点：看状态",
    ),
    (
        T.CYAN,
        "SWO 实时",
        "Stream ITM over SWO",
        [
            ("对时序的干扰", ["不停内核，但不是零", "代价：阻塞或丢字符", "取决于重定向、探针", "和主机是否持续接收"]),
            ("能看见什么", ["ITM 有 32 个通道，", "Port 0 常作 printf；", "按时间顺序出值"]),
            ("适用故障", ["要过程不要停机的场", "景：状态机推进、偶", "发分支与接口时序"]),
            ("前提与代价", ["第 39 脚 PB3 复位后", "是 JTDO：先关 JTAG", "只留 SWD；SWO 时钟", "要配成内核时钟"]),
        ],
        "不停机：看过程",
    ),
    (
        T.AMBER,
        "日志留痕",
        "Persist printf output",
        [
            ("对时序的干扰", ["printf 走 UART：占用", "一路串口，字符按线", "速排出，主机侧要有", "人一直在收"]),
            ("能看见什么", ["跑完还能查：PC/LR、", "CFSR/HFSR/BFAR 的", "有效位与 ELF 哈希"]),
            ("适用故障", ["硬故障现场与偶发问", "题；IMPRECISERR 下", "栈 PC 也可能不是最", "初写错的位置"]),
            ("前提与代价", ["要有一路空闲 USART；", "串口被占用时只能上", "SWO，或 J-Link 的", "SWO/ITM 与 RTT"]),
        ],
        "跑完再看：看留痕",
    ),
]

BLOCK_TOPS = (246, 378, 510, 642)


def obs_compare() -> Svg:
    canvas = Svg(
        960,
        880,
        "观测手段不可互替：M3 只有 6 个硬件断点，SWO 占 PB3 不占串口，日志留痕留下 PC 与 CFSR",
        "STM32F103C8T6 · chapter 17 · SWD / SWO / ITM",
    )
    canvas.header(tag="17", tag_color=T.CYAN)
    canvas.text(40, 86, "三种观测手段各看一段：停在哪里、走过什么、事后留下什么",
                size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "halt, stream, persist: three instruments for one fault",
                size=14, fill=T.CYAN)
    canvas.text(40, 138,
                "PA13 SWDIO · PA14 SWCLK · PB3 TRACESWO (pin 39)   M3 6 HW breakpoints · M7 8   CFSR 0xE000ED28",
                size=13, fill=T.AMBER, mono=True)

    for index, (color, name, latin, blocks, verdict) in enumerate(COLS):
        x = 40 + index * 300
        canvas.rect(x, 158, 280, 632, fill=T.PANEL, stroke=color, rx=8)
        canvas.text(x + 18, 190, name, size=17, fill=color, weight="700")
        canvas.text(x + 18, 212, latin, size=11, fill=T.MUTED)
        canvas.line(x + 18, 226, x + 262, 226, stroke=T.GRID, sw=1)

        for j, (label, lines) in enumerate(blocks):
            top = BLOCK_TOPS[j]
            if j:
                canvas.line(x + 18, top - 16, x + 262, top - 16, stroke=T.GRID, sw=1)
            canvas.text(x + 18, top, label, size=11, fill=T.MUTED)
            for i, line in enumerate(lines):
                canvas.text(x + 18, top + 22 + i * 19, line, size=12.5, fill=T.TEXT)

        canvas.line(x + 18, 742, x + 262, 742, stroke=T.GRID, sw=1)
        canvas.text(x + 18, 768, verdict, size=13, fill=color, weight="700")

    canvas.rect(40, 798, 880, 34, fill=T.BG2, stroke=T.GREEN, rx=8)
    canvas.text(56, 819,
                "底注  SWD 两根信号线加 GND；JTAG 四根且支持菊花链。把 PA13/PA14 改成普通 GPIO，烧录后就再也连不上。",
                size=12, fill=T.TEXT)

    _credit(canvas, "自绘。SWD/SWO 引脚与断点数量按本章「时序与状态」表；故障寄存器地址来自 PM0056。")
    return canvas


# ---------------------------------------------------------------- figure 2
# Three forks, same internal shape: symptom -> check -> branch.
BANDS = [
    (
        T.RED,
        "岔口一  觉得慢：先测周期，别先猜循环",
        "DEMCR bit 24 · DWT_CYCCNT",
        "觉得慢就去展开汇编，改到满意为止，却没人说得出到底快了多少",
        ["先把 DEMCR 0xE000EDFC 的 bit 24 置 1，再清 DWT_CYCCNT 0xE0001004",
         "72 MHz 下 72 个计数是 1 µs；被测代码夹在两次读数之间，跑多次取个数"],
        ["读数是 0：bit 24 没置，两次读数之差就是 0 —— 先修测量，别改代码",
         "dt 有数：按收益排序改，DMA 卸载 > 优化等级 > 减少浮点/除法 > Cache/预取 > 汇编"],
        "顺序：先量出来，再只改一处，改完立刻复现刚才的现象",
        T.MUTED,
    ),
    (
        T.AMBER,
        "岔口二  优化后时序变了：换条件就没有对照",
        "-Og / -O2 / -Os",
        "优化等级一升，断言还在，时序却变了：以为按顺序发生的读写被重排",
        ["同一测试向量在 -Og、-O2、-Os 下各记周期、代码大小和输出一致性",
         "对照必须同条件：先有 bit 24 和 CYCCNT 的基线，再改优化等级"],
        ["三项都一致：接受这次优化，把周期数写进记录",
         "有一项不一致：回 -Og 定位，与硬件时序有关的变量标 volatile，再跑原测试"],
        "改优化等级本身不是问题，用不同条件的两组数比较才是",
        T.MUTED,
    ),
    (
        T.VIOLET,
        "岔口三  栈或内存异常：先冻结 CFSR，再决定信不信 BFAR",
        "CFSR[15] · BFAR 0xE000ED38",
        "一进 HardFault 就只复位，现场没了；BFAR 里有个数，却对不上这次访问",
        ["冻住现场：CFSR 0xE000ED28 → HFSR 0xE000ED2C（FORCED bit 30 = 0x40000000）→ BFAR",
         "再从栈里取 PC：R0 起算第 6 个字，SP + 0x18；用同一个 ELF 跑 addr2line -e -f -C"],
        ["CFSR bit 15 = 1：BFAR 才是这次出错的地址，拿它去对源码行",
         "bit 15 = 0：BFAR 是旧值，不能用；IMPRECISERR 下栈 PC 也可能不是最初写错的位置"],
        "原因表：UNDEFINSTR 栈被冲；INVSTATE 跳转目标 bit0=0；FORCED 且 CFSR=0 查 VTOR 与链接脚本",
        T.TEXT,
    ),
]


def perf_triage() -> Svg:
    canvas = Svg(
        960,
        880,
        "排错三岔口：读数为 0 查 bit 24；72 MHz 下 72 个计数是 1 µs；BFAR 要 CFSR bit 15 为 1",
        "STM32F103C8T6 · chapter 17 · DWT / optimization / HardFault",
    )
    canvas.header(tag="17", tag_color=T.CYAN)
    canvas.text(40, 84, "性能排错三岔口：一个是测量坏了，一个是条件换了，一个是现场没冻结",
                size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 110, "three forks, one order: measure first, compare like with like, freeze the fault",
                size=14, fill=T.CYAN)
    canvas.text(40, 134, "DWT_CYCCNT 0xE0001004 · 72 MHz: 72 counts = 1 µs   CFSR 0xE000ED28 · BFAR 0xE000ED38",
                size=13, fill=T.AMBER, mono=True)

    for k, (color, title, hint, symptom, checks, branches, note, note_fill) in enumerate(BANDS):
        top = 182 + k * 226
        canvas.text(40, top - 12, title, size=16, fill=color, weight="700")
        canvas.text(920, top - 12, hint, size=11, fill=T.MUTED, anchor="end", mono=True)
        canvas.rect(40, top, 880, 198, fill=T.PANEL, stroke=color, rx=8)

        rows = [("现象", symptom), ("检查", checks[0]), ("", checks[1]), ("岔口", branches[0]), ("", branches[1])]
        for i, (label, line) in enumerate(rows):
            y = top + 24 + i * 26
            if label:
                canvas.text(56, y, label, size=12, fill=color, weight="700")
            canvas.text(112, y, line, size=14, fill=T.TEXT)
        canvas.text(112, top + 24 + 5 * 26, note, size=12, fill=note_fill)

    _credit(canvas, "自绘。故障寄存器地址来自 PM0056；DWT 使能顺序按本章时序表，先 bit 24，再 CYCCNT。")
    return canvas


FIGURES = [
    ("sample-17-obs-compare.svg", obs_compare),
    ("sample-17-perf-triage.svg", perf_triage),
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

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
            ("对时序的干扰", ["命中即停住内核；软件", "断点会改写目标指令，", "Flash 需探针支持并", "受存储器权限影响"]),
            ("能看见什么", ["命中那一刻的寄存器", "与内存：CFSR、BFAR", "可以当场读出来"]),
            ("适用故障", ["确定的代码路径；数据", "观察点使用独立 DWT，", "不占 FPB 代码比较器"]),
            ("前提与代价", ["F103 有 6 个代码比较", "器；条件硬件断点也", "占用，需留意临时断点"]),
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
            ("前提与代价", ["PB3 第 39 脚复位为", "JTDO，需启用 trace；", "查看器的目标内核频率", "与 SWO 速率需匹配"]),
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
            ("前提与代价", ["UART 需空闲 USART；", "也可选 SWO、RTT 或", "RAM 环形缓冲，按接口", "与故障情形决定"]),
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
                "PA13 SWDIO · PA14 SWCLK · PB3 TRACESWO (pin 39)   F103: 6 FPB code comparators · CFSR 0xE000ED28",
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
                "SWD 共地并按探针要求接 VTref；若固件关闭 SWD，可接 NRST 尝试 connect-under-reset 恢复。",
                size=12, fill=T.TEXT)

    _credit(canvas, "自绘。SWD/SWO 引脚与断点数量按本章「时序与状态」表；故障寄存器地址来自 PM0056。")
    return canvas


# ---------------------------------------------------------------- figure 2

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


def perf_triage() -> Svg:
    canvas = Svg(
        960,
        880,
        "性能三岔口：DWT 读数为 0 先查 bit 24；72 MHz 下 72 个计数是 1 µs；BFAR 要 CFSR bit 15 才可信",
        "STM32F103C8T6 · chapter 17 · DWT / optimization / HardFault",
    )
    canvas.header(title="性能三岔口：先测出来、同条件比较、冻结现场",
                  tag="17", tag_color=T.CYAN)

    # 顶条：把「测一次」画成时间轴，右边给出 1 µs 的刻度
    canvas.text(24, 82, "先把测量修好：DWT_CYCCNT 在两次读数之间只数周期",
                size=12.5, fill=T.TEXT, weight="700")
    canvas.rect(24, 92, 560, 66, fill=T.PANEL, stroke=T.CYAN, rx=8)
    canvas.text(38, 114, "DEMCR 0xE000EDFC bit24 = 1", size=10.5, fill=T.CYAN,
                mono=True)
    canvas.line(38, 140, 546, 140, stroke=T.GRID, sw=1)
    for k, (x, lab, color) in enumerate(((70, "T0 读", T.GREEN),
                                         (300, "被测代码", T.AMBER),
                                         (470, "T1 读", T.GREEN))):
        canvas.line(x, 130, x, 150, stroke=color, sw=2)
        canvas.text(x, 124, lab, size=10, anchor="middle", fill=color)
    canvas.arrow(70, 137, 470, 137, color=T.STROKE, sw=1.5, head=5)
    canvas.arrow(470, 137, 70, 137, color=T.STROKE, sw=1.5, head=5)
    canvas.text(270, 154, "Δ 周期数（T0 → 被测代码 → T1）", size=10, fill=T.MUTED,
                anchor="middle")
    # 1 µs 刻度：72 格
    canvas.text(600, 104, "72 MHz 下 72 个计数 = 1 µs", size=11.5, fill=T.TEXT,
                weight="600")
    gx, gy = 600, 114
    for i in range(72):
        canvas.line(gx + i * 4.4, gy, gx + i * 4.4, gy + (14 if i % 12 == 0 else 7),
                    stroke=T.CYAN, sw=1)
    canvas.text(600, 150, "一格 13.9 ns", size=10, fill=T.MUTED)

    # 面板 A：测量坏了
    ax, ay, aw, ah = 24, 176, 440, 244
    canvas.rect(ax, ay, aw, ah, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.rect(ax, ay, aw, 5, fill=T.RED, rx=2)
    canvas.text(ax + 14, ay + 30, "① 读数为 0：测量坏了，不是代码快",
                size=13, fill=T.TEXT, weight="700")
    canvas.text(ax + 14, ay + 50, "DEMCR bit24 · DWT_CYCCNT 0xE0001004",
                size=10, fill=T.RED, mono=True)
    canvas.text(ax + 14, ay + 78, "两次读数一样 → Δ = 0", size=11.5, fill=T.TEXT)
    canvas.text(ax + 14, ay + 98,
                "核对 TRCENA、CYCCNTENA、是否停核，以及被测代码是否仍存在。",
                size=10.5, fill=T.MUTED)
    canvas.text(ax + 14, ay + 128, "按瓶颈选候选项，再测收益：", size=11,
                fill=T.TEXT, weight="600")
    ladder = ["搬运占 CPU：比较 DMA", "比较 -Og / -O2 / -Os", "软件浮点、除法与算法",
              "F1 Flash 预取；没有 D-Cache", "热点反汇编与访存等待"]
    for i, item in enumerate(ladder):
        yy = ay + 148 + i * 18
        canvas.rect(ax + 14, yy - 11, 8, 14, fill=T.CYAN, rx=2,
                    opacity=0.85 - i * 0.12)
        canvas.text(ax + 32, yy, item, size=10.5,
                    fill=T.MUTED if i == 3 else T.TEXT)
    canvas.text(ax + 250, ay + 128, "只改一处，改完立刻复现", size=10.5,
                fill=T.GREEN)

    # 面板 B：优化等级换了条件
    bx, bw2 = 480, 456
    canvas.rect(bx, ay, bw2, ah, fill=T.PANEL, stroke=T.AMBER, rx=8)
    canvas.rect(bx, ay, bw2, 5, fill=T.AMBER, rx=2)
    canvas.text(bx + 14, ay + 30, "② 升优化等级后时序变了：条件不再相同",
                size=13, fill=T.TEXT, weight="700")
    canvas.text(bx + 14, ay + 50, "同一测试向量 × 三种优化等级", size=10,
                fill=T.AMBER, mono=True)
    cols = [("-Og", "基线", T.CYAN), ("-O2", "重排读写", T.AMBER),
            ("-Os", "体积优先", T.VIOLET)]
    for i, (flag, note, color) in enumerate(cols):
        x = bx + 14 + i * 144
        canvas.rect(x, ay + 62, 132, 96, fill=T.BG2, stroke=color, rx=4)
        canvas.text(x + 12, ay + 84, flag, size=12, fill=color, weight="700",
                    mono=True)
        canvas.text(x + 12, ay + 102, note, size=9.5, fill=T.MUTED)
        for k, lab in enumerate(("周期数", "代码大小", "输出一致")):
            canvas.circle(x + 18, ay + 120 + k * 15, 4, fill=T.BG,
                          stroke=color, sw=1)
            canvas.text(x + 30, ay + 124 + k * 15, lab, size=9.5, fill=T.MUTED)
    canvas.text(bx + 14, ay + 182,
                "输出必须一致，周期数和大小用于比较；固定输入、时钟及中断条件，",
                size=10.5, fill=T.MUTED)
    canvas.text(bx + 14, ay + 200,
                "核对寄存器声明与并发同步；volatile 不提供原子性或同步。", size=10.5,
                fill=T.MUTED)
    canvas.text(bx + 14, ay + 224, "拿两个不同条件的数去比较，才是真正的问题来源。",
                size=10.5, fill=T.AMBER)

    # 面板 C：冻结现场
    cy = 436
    canvas.rect(24, cy, 912, 300, fill=T.PANEL, stroke=T.VIOLET, rx=8)
    canvas.rect(24, cy, 912, 5, fill=T.VIOLET, rx=2)
    canvas.text(38, cy + 30, "③ HardFault：立即保存现场，再解码；不必先做性能测量",
                size=13, fill=T.TEXT, weight="700")
    regs = [("BFAR", "0xE000ED38", "先保存地址，再判 VALID", T.CYAN),
            ("HFSR", "0xE000ED2C", "FORCED = bit30", T.AMBER),
            ("CFSR", "0xE000ED28", "保存后解码错误类型", T.VIOLET)]
    for i, (name, addr, note, color) in enumerate(regs):
        x = 38 + i * 200
        canvas.rect(x, cy + 50, 186, 64, fill=T.BG2, stroke=color, rx=4)
        canvas.text(x + 12, cy + 74, name, size=13, fill=color, weight="700",
                    mono=True)
        canvas.text(x + 12, cy + 92, addr, size=10, fill=T.MUTED, mono=True)
        canvas.text(x + 12, cy + 108, note, size=9.5, fill=T.MUTED)
        if i < 2:
            canvas.arrow(x + 188, cy + 82, x + 198, cy + 82, color=T.STROKE,
                         sw=1.5, head=5)
    # bit15 的判断门
    canvas.rect(638, cy + 50, 284, 64, fill=T.BG2, stroke=T.STROKE, rx=4)
    canvas.text(650, cy + 74, "CFSR bit15", size=11.5, fill=T.TEXT, weight="600")
    canvas.rect(650, cy + 84, 118, 22, fill=T.GREEN, rx=4, opacity=0.28)
    canvas.text(659, cy + 100, "= 1 → 地址有效", size=10, fill=T.GREEN)
    canvas.rect(778, cy + 84, 132, 22, fill=T.RED, rx=4, opacity=0.28)
    canvas.text(787, cy + 100, "= 0 → 无效，弃用", size=10, fill=T.RED)

    # 栈帧：SP + 0x18 取 PC
    canvas.text(38, cy + 140, "基本栈帧完整时：PC = 选定栈帧基址 + 0x18；用 EXC_RETURN 选栈，同一 ELF 跑 addr2line",
                size=11, fill=T.TEXT)
    sx, sw = 38, 46
    frame = ["R0", "R1", "R2", "R3", "R12", "LR", "PC", "xPSR"]
    for i, r in enumerate(frame):
        canvas.rect(sx + i * sw, cy + 150, sw - 6, 30, fill=T.PANEL2,
                    stroke=T.GREEN if r == "PC" else T.GRID,
                    sw=2 if r == "PC" else 1, rx=2)
        canvas.text(sx + i * sw + (sw - 6) / 2, cy + 170, r, size=10,
                    anchor="middle", fill=T.GREEN if r == "PC" else T.MUTED,
                    mono=True)
    canvas.text(sx + 6 * sw, cy + 196, "frame + 0x18", size=9.5, fill=T.GREEN,
                mono=True)

    # 常见原因表
    causes = [("UNDEFINSTR", "未定义指令：查指令与代码地址", T.RED),
              ("INVSTATE", "非法状态：查 Thumb 状态与跳转", T.AMBER),
              ("IMPRECISERR", "PC 可能滞后，不能直接认定原写入", T.VIOLET)]
    canvas.text(38, cy + 224, "按故障类型继续检查：STKERR / MSTKERR 时先确认栈帧是否完整", size=11, fill=T.TEXT,
                weight="600")
    for i, (name, note, color) in enumerate(causes):
        x = 38 + i * 300
        canvas.text(x, cy + 248, name, size=10.5, fill=color, mono=True)
        canvas.text(x, cy + 266, note, size=10, fill=T.MUTED)

    canvas.rect(24, 752, 912, 34, fill=T.BG2, stroke=T.GREEN, rx=8)
    canvas.text(38, 774,
                "性能比较与故障取证是两项任务：前者固定测量条件，后者立即保留现场与匹配的 ELF。",
                size=11, fill=T.TEXT)
    _credit(canvas, "自绘。故障寄存器地址来自 PM0056；DWT 使能顺序按本章时序表，先 bit 24 再 CYCCNT。")
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

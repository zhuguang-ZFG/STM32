#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Static B4 figure for chapter 15: FreeRTOS triage.

No CSS animation and no SMIL.

    python tools/sample_figs_b4/ch15_b4.py assets/diagrams
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


def rtos_triage() -> Svg:
    canvas = Svg(
        960,
        880,
        "任务不动、栈溢出、优先级异常：1 ms 一个 tick，128 字是 512 字节，FromISR 的抢占优先级数值至少 5",
        "STM32F103C8T6 · chapter 15 · FreeRTOS Kernel V11.3.2",
    )
    canvas.header(title="RTOS 排错：先确认启动，再核对栈与优先级",
                  tag="15", tag_color=T.CYAN)

    # 顶条：两个时钟源各归各家，这一眼就能看出「抢 SysTick」为什么全卡
    canvas.text(24, 82, "本例时基分工：内核用 SysTick，HAL 用 TIM4",
                size=15, fill=T.TEXT, weight="700")
    canvas.rect(24, 92, 300, 46, fill=T.PANEL, stroke=T.GREEN, rx=8)
    canvas.text(38, 112, "SysTick · 1000 Hz", size=14, fill=T.GREEN, weight="700")
    canvas.text(38, 130, "内核计时：1 tick = 1 ms", size=12, fill=T.MUTED)
    canvas.rect(340, 92, 300, 46, fill=T.PANEL, stroke=T.CYAN, rx=8)
    canvas.text(354, 112, "TIM4 · HAL 时基", size=14, fill=T.CYAN, weight="700")
    canvas.text(354, 130, "CubeMX：SYS → Timebase Source", size=12, fill=T.MUTED)
    canvas.rect(656, 92, 280, 46, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(670, 112, "若 HAL_Delay 卡住", size=14, fill=T.RED, weight="700")
    canvas.text(670, 130, "先查 HAL tick 是否还在递增", size=12, fill=T.MUTED)

    # 岔口一：三道闸门 → 调度器
    ax, ay, aw, ah = 24, 158, 300, 290
    canvas.rect(ax, ay, aw, ah, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.rect(ax, ay, aw, 5, fill=T.RED, rx=2)
    canvas.text(ax + 14, ay + 30, "① 任务不动", size=16, fill=T.TEXT, weight="700")
    canvas.text(ax + 14, ay + 52, "启动后应切到任务，不再返回 main",
                size=12, fill=T.MUTED)
    gates = [
        ("SysTick 被两边共用", "SYS 改成 TIM4"),
        ("移植层选了 ARM_CM4F", "M3 无 FPU → 启动即 HardFault"),
        ("xTaskCreate 返回 pdFAIL", "检查 10240 字节堆的剩余容量"),
    ]
    yy = ay + 76
    for i, (head, fix) in enumerate(gates, 1):
        canvas.circle(ax + 22, yy - 4, 8, fill=T.BG2, stroke=T.RED, sw=1.5)
        canvas.text(ax + 22, yy, str(i), size=9.5, anchor="middle", fill=T.RED,
                    weight="700")
        yy = _wrap(canvas, ax + 38, yy, head, aw - 54, 12.5, T.TEXT, lh=16) + 4
        yy = _wrap(canvas, ax + 38, yy, fix, aw - 54, 11.5, T.MUTED, lh=15) + 12
    canvas.rect(ax + 12, ay + ah - 52, aw - 24, 40, fill=T.BG2, stroke=T.RED,
                rx=4)
    canvas.text(ax + 24, ay + ah - 32, "启动前逐个检查任务创建返回值",
                size=12, fill=T.GREEN)
    canvas.text(ax + 24, ay + ah - 16, "启动函数返回：再查内核任务分配",
                size=11.5, fill=T.DIM)

    # 岔口二：把「字」画成格子，128 格 × 4 B，按字节理解只给了四分之一
    bx = 336
    canvas.rect(bx, ay, aw, ah, fill=T.PANEL, stroke=T.AMBER, rx=8)
    canvas.rect(bx, ay, aw, 5, fill=T.AMBER, rx=2)
    canvas.text(bx + 14, ay + 30, "② 打印后 HardFault：查栈",
                size=16, fill=T.TEXT, weight="700")
    canvas.text(bx + 14, ay + 50, "xTaskCreate depth 的单位是字（4 B）",
                size=10, fill=T.AMBER, mono=True)
    gx, gy2, gcw, gch = bx + 16, ay + 64, 17, 17
    for i in range(128):
        cx2, cy2 = gx + (i % 16) * gcw, gy2 + (i // 16) * gch
        canvas.rect(cx2, cy2, gcw - 1.5, gch - 1.5,
                    fill=T.AMBER if i < 32 else T.BG,
                    stroke=T.AMBER if i < 32 else T.GRID, sw=1, rx=2)
    canvas.text(bx + 16, gy2 + 8 * gch + 14, "128 格，一格 4 字节 = 512 字节",
                size=12, fill=T.TEXT)
    canvas.text(bx + 16, gy2 + 8 * gch + 30, "当成 128 字节来给：只剩 32 格",
                size=12, fill=T.RED)
    canvas.rect(bx + 16, gy2 + 8 * gch + 36, 16 * gcw / 4, 7, fill=T.AMBER,
                rx=2)
    canvas.rect(bx + 16 + 16 * gcw / 4, gy2 + 8 * gch + 36, 16 * gcw * 3 / 4, 7,
                fill=T.RED, rx=2, opacity=0.35)
    canvas.text(bx + 16, ay + ah - 34, "深色 32 格 = 128 B，少分配了 96 格",
                size=11.5, fill=T.MUTED)
    canvas.text(bx + 16, ay + ah - 16, "是否溢出：看栈水位与溢出钩子",
                size=12, fill=T.RED)

    # 岔口三：两条方向相反的优先级轴，0~4 是禁区
    cx3 = 648
    canvas.rect(cx3, ay, aw, ah, fill=T.PANEL, stroke=T.VIOLET, rx=8)
    canvas.rect(cx3, ay, aw, 5, fill=T.VIOLET, rx=2)
    canvas.text(cx3 + 14, ay + 30, "③ 核对优先级方向",
                size=16, fill=T.TEXT, weight="700")
    canvas.text(cx3 + 14, ay + 50, "0x50 = 5 << (8 − 4)", size=10,
                fill=T.VIOLET, mono=True)
    ax0, ax1 = cx3 + 16, cx3 + aw - 16
    canvas.text(ax0, ay + 72, "任务优先级：数值大，优先运行", size=12.5, fill=T.CYAN)
    canvas.line(ax0, ay + 78, ax1, ay + 78, stroke=T.CYAN, sw=1.5)
    canvas.arrow(ax0 + 120, ay + 78, ax1, ay + 78, color=T.CYAN, sw=1.5, head=6)
    canvas.text(ax0, ay + 106, "NVIC 抢占：数值小，优先响应", size=12.5, fill=T.AMBER)
    canvas.line(ax0, ay + 112, ax1, ay + 112, stroke=T.AMBER, sw=1.5)
    canvas.arrow(ax1 - 120, ay + 112, ax0, ay + 112, color=T.AMBER, sw=1.5,
                 head=6)
    canvas.rect(ax0, ay + 126, 60, 22, fill=T.RED, rx=4, opacity=0.28)
    canvas.text(ax0 + 30, ay + 141, "0–4", size=10.5, anchor="middle",
                fill=T.RED, weight="700")
    canvas.text(ax0 + 70, ay + 141, "禁止调用 FromISR", size=12, fill=T.RED)
    canvas.rect(ax0 + 214, ay + 126, 30, 22, fill=T.PANEL2, stroke=T.GREEN,
                rx=4)
    canvas.text(ax0 + 229, ay + 141, "5", size=11, anchor="middle",
                fill=T.GREEN, weight="700")
    canvas.text(cx3 + 14, ay + 170, "本例 EXTI0 填 5：0x50 = 5 << 4",
                size=12, fill=T.GREEN, mono=True)
    canvas.text(cx3 + 14, ay + 194, "0–4 中调 FromISR：触发 configASSERT",
                size=12, fill=T.RED)
    canvas.text(cx3 + 14, ay + 224, "若是优先级反转：比较二值信号量与互斥量",
                size=11.5, fill=T.MUTED)
    canvas.text(cx3 + 14, ay + 245, "互斥量有优先级继承；用 GPIO 量最长等待",
                size=11.5, fill=T.MUTED)
    canvas.text(cx3 + 14, ay + 273, "数值 5 适用本例的 4 位 NVIC 优先级配置",
                size=11.5, fill=T.DIM)

    # 堆预算：10240 字节怎么分给三个任务
    hy = 480
    canvas.text(24, hy, "10240 字节堆：先扣三块任务栈，再计算其他开销", size=15,
                fill=T.TEXT, weight="700")
    total_w = 900
    seg = [("LED 512 B", 512, T.CYAN), ("KEY 768 B", 768, T.GREEN),
           ("UART 1024 B", 1024, T.AMBER), ("尚未扣除其他开销：7936 B", 7936, T.STROKE)]
    hx = 24
    for label, n, color in seg:
        w = total_w * n / 10240
        canvas.rect(hx, hy + 12, w, 30, fill=color, rx=4,
                    opacity=0.85 if color != T.STROKE else 0.25)
        if n > 1024:
            canvas.text(hx + w / 2, hy + 32, label, size=13, anchor="middle",
                        fill=T.MUTED, weight="700")
        hx += w
    for offset, label, color in ((0, "LED 512 B", T.CYAN), (180, "KEY 768 B", T.GREEN),
                                 (360, "UART 1024 B", T.AMBER)):
        canvas.rect(24 + offset, hy + 53, 12, 12, fill=color, rx=2)
        canvas.text(44 + offset, hy + 64, label, size=12.5, fill=T.TEXT)
    canvas.text(24, hy + 90,
                "栈合计 2304 B；7936 B 还要放 TCB、队列、内核任务及分配开销，并非实际空闲堆。",
                size=12.5, fill=T.MUTED)

    # 周期：3 ms 干活 + 10 tick 延时 = 13 ms；vTaskDelayUntil 才是固定 10
    ty = 610
    canvas.text(24, ty, "工作 3 ms，再延时 10 tick：周期会累积工作时间", size=15, fill=T.TEXT,
                weight="700")
    canvas.rect(24, ty + 12, 430, 34, fill=T.BG2, stroke=T.STROKE, rx=4)
    canvas.rect(24, ty + 12, 430 * 3 / 13, 34, fill=T.AMBER, rx=4, opacity=0.8)
    canvas.text(30, ty + 34, "工作 3 ms", size=12, fill=T.BG, weight="700")
    canvas.text(24 + 430 * 3 / 13 + 8, ty + 34, "vTaskDelay(10) = 10 ms",
                size=12, fill=T.TEXT)
    canvas.text(466, ty + 34, "约 13 ms", size=13, fill=T.RED, weight="700")
    canvas.rect(24, ty + 56, 430 * 10 / 13, 30, fill=T.BG2, stroke=T.GREEN,
                rx=4)
    canvas.rect(24, ty + 56, 430 * 10 / 13, 30, fill=T.GREEN, rx=4, opacity=0.25)
    canvas.text(30, ty + 76, "vTaskDelayUntil：按上次计划唤醒时刻算",
                size=12, fill=T.TEXT)
    canvas.text(466, ty + 76, "目标周期 10 ms", size=13, fill=T.GREEN, weight="700")
    canvas.text(24, ty + 106,
                "图示忽略 tick 相位与调度抖动；1000 Hz 下，延时 API 的分辨率为 1 ms。",
                size=12.5, fill=T.MUTED)

    canvas.rect(24, ty + 122, 900, 34, fill=T.BG2, stroke=T.VIOLET, rx=8)
    canvas.text(38, ty + 144,
                "验证顺序：创建返回值 → 任务实际运行 → 栈水位 → 中断优先级 → 实测周期与最长等待。",
                size=13, fill=T.TEXT)

    _credit(canvas,
            "自绘。优先级、FromISR 与堆语义来自 FreeRTOS Kernel V11.3.2；"
            "栈、TIM4 与任务优先级来自本仓库 freertos-task。")
    return canvas


FIGURES = [
    ("sample-15-rtos-triage.svg", rtos_triage),
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

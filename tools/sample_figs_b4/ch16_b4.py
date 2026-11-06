#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Static B4 figures for chapter 16: Sleep/Stop/Standby side by side, and low-power triage.

No CSS animation and no SMIL.

    python tools/sample_figs_b4/ch16_b4.py assets/diagrams
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


def mode_compare() -> Svg:
    canvas = Svg(
        960,
        880,
        "Sleep 是 14.4 mA 且沿用 72 MHz，Stop 是 14 µA、醒来 HSI 8 MHz 要重配时钟，Standby 2 µA 醒来从复位向量重启",
        "STM32F103C8T6 · chapter 16 · DS5319 Rev 20 表 16 与表 26",
    )
    canvas.header(title="Sleep / Stop / Standby：五问并排", tag="16", tag_color=T.CYAN)
    canvas.text(40, 86, "三档并排：省电越多，唤醒越慢，保住的状态越少",
                size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "same five questions per mode: current / wake source / wake time / clock after wake / state kept",
                size=14, fill=T.CYAN)
    canvas.text(40, 138,
                "SLEEPDEEP=0  → Sleep    SLEEPDEEP=1 + PDDS=0  → Stop    SLEEPDEEP=1 + PDDS=1  → Standby",
                size=13, fill=T.AMBER, mono=True)

    cols = (
        (160, "Sleep", "打个盹", "SLEEPDEEP=0", T.GREEN),
        (411, "Stop", "睡一觉，醒来对表", "SLEEPDEEP=1 PDDS=0", T.CYAN),
        (662, "Standby", "主电源域关，醒来重启", "SLEEPDEEP=1 PDDS=1", T.VIOLET),
    )
    for x, name, tagline, regs, color in cols:
        canvas.rect(x, 168, 246, 56, fill=T.BG2, stroke=color, rx=8)
        canvas.text(x + 124, 192, name, size=17, fill=color, anchor="middle", weight="700")
        canvas.text(x + 124, 212, tagline, size=11, fill=T.MUTED, anchor="middle")

    regs_y = 232
    canvas.rect(160, regs_y, 748, 420, fill=T.PANEL, stroke=T.STROKE, rx=8)
    for y in (330, 410, 492, 578):
        canvas.line(160, y, 908, y, stroke=T.GRID, sw=1)
    for x in (409, 660):
        canvas.line(x, 232, x, 652, stroke=T.GRID, sw=1)

    canvas.text(40, 260, "电流量级", size=13, fill=T.TEXT, weight="700")
    canvas.text(40, 280, "3.3 V · 25 °C", size=11, fill=T.MUTED)
    canvas.text(172, 258, "14.4 mA", size=15, fill=T.GREEN, weight="700")
    canvas.text(172, 282, "72 MHz 外设全开", size=12, fill=T.TEXT)
    canvas.text(172, 306, "5.5 mA 外设全关", size=12, fill=T.TEXT)
    canvas.text(423, 258, "14 µA", size=15, fill=T.CYAN, weight="700")
    canvas.text(423, 282, "低功耗稳压器，无 IWDG", size=12, fill=T.TEXT)
    canvas.text(423, 306, "24 µA 主稳压器", size=12, fill=T.TEXT)
    canvas.text(674, 258, "2 µA", size=15, fill=T.VIOLET, weight="700")
    canvas.text(674, 282, "LSI、IWDG、LSE、RTC 全关", size=12, fill=T.TEXT)
    canvas.text(674, 306, "LSI 开 3.2，加 IWDG 3.4", size=12, fill=T.TEXT)

    canvas.text(40, 358, "唤醒源", size=13, fill=T.TEXT, weight="700")
    canvas.text(40, 378, "谁把它叫醒", size=11, fill=T.MUTED)
    canvas.text(172, 354, "满足条件的中断或事件", size=13, fill=T.TEXT)
    canvas.text(172, 376, "看 WFI/WFE 与 NVIC/优先级配置", size=11, fill=T.MUTED)
    canvas.text(423, 354, "EXTI（含 RTC / USB 唤醒）", size=12, fill=T.TEXT)
    canvas.text(423, 376, "IWDG / NRST 走复位", size=12, fill=T.MUTED)
    canvas.text(674, 354, "WKUP 引脚（PA0 上升沿）", size=13, fill=T.TEXT)
    canvas.text(674, 376, "RTC 闹钟；IWDG / NRST 复位", size=12, fill=T.MUTED)

    canvas.text(40, 438, "唤醒时间", size=13, fill=T.TEXT, weight="700")
    canvas.text(40, 458, "到第一条指令", size=11, fill=T.MUTED)
    canvas.text(172, 434, "1.8 µs", size=15, fill=T.GREEN, weight="700")
    canvas.text(172, 458, "沿用睡前的时钟", size=12, fill=T.TEXT)
    canvas.text(423, 434, "5.4 µs", size=15, fill=T.CYAN, weight="700")
    canvas.text(423, 458, "主稳压器那格 3.6 µs", size=12, fill=T.TEXT)
    canvas.text(674, 434, "50 µs", size=15, fill=T.VIOLET, weight="700")
    canvas.text(674, 458, "经复位启动，到第一条指令", size=12, fill=T.TEXT)

    canvas.text(40, 520, "唤醒后时钟", size=13, fill=T.TEXT, weight="700")
    canvas.text(40, 540, "本章的主坑", size=11, fill=T.MUTED)
    canvas.text(172, 518, "仍是 72 MHz", size=14, fill=T.GREEN, weight="700")
    canvas.text(172, 542, "不用重配 PLL", size=12, fill=T.TEXT)
    canvas.text(423, 518, "HSI 8 MHz", size=14, fill=T.CYAN, weight="700")
    canvas.text(423, 542, "先 SystemClock_Config() 才回 72 MHz", size=12, fill=T.TEXT)
    canvas.text(674, 518, "从头走复位", size=14, fill=T.VIOLET, weight="700")
    canvas.text(674, 542, "重新配置时钟树", size=12, fill=T.TEXT)

    canvas.text(40, 606, "保持状态", size=13, fill=T.TEXT, weight="700")
    canvas.text(40, 626, "唤醒后还剩什么", size=11, fill=T.MUTED)
    canvas.text(172, 606, "SRAM 与寄存器全保持", size=12, fill=T.TEXT)
    canvas.text(423, 606, "SRAM 与寄存器全保持", size=12, fill=T.TEXT)
    canvas.text(674, 606, "丢失，只剩备份域", size=12, fill=T.TEXT)

    canvas.rect(40, 662, 880, 72, fill=T.BG2, stroke=T.GREEN, rx=8)
    canvas.text(56, 688, "同一个 0x271：72 MHz 上是 115200 bit/s，停在 8 MHz 上只有 12800 bit/s，差 9 倍。",
                size=13, fill=T.TEXT)
    canvas.text(56, 714, "所以 Stop 醒来先 SystemClock_Config()，再发下一个字节；Sleep 不用这一步。",
                size=13, fill=T.TEXT)

    canvas.rect(40, 744, 880, 58, fill=T.PANEL, stroke=T.STROKE, rx=8)
    canvas.text(56, 766, "14.4 mA 与 14 µA 相差约 1000 倍；三种模式条件不同，电流都是典型值，不是最大值。",
                size=12, fill=T.TEXT)
    canvas.text(56, 788, "1.4 µA 是备份域 IDD_VBAT，不是整机 Standby；表 16 没有「Stop 加 IWDG」这一格。",
                size=12, fill=T.TEXT)

    _credit(canvas, "自绘。电流、唤醒时间与保持状态来自 DS5319 Rev 20 表 16 与表 26；HSI 8 MHz 与重配时钟来自 RM0008 时钟。")
    return canvas


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


def pwr_triage() -> Svg:
    canvas = Svg(
        960,
        880,
        "低功耗三岔口：先确认真进了 Stop，再看醒来的时钟，最后用差值法抓耗电大户",
        "STM32F103C8T6 · chapter 16 · DS5319 Rev 20 表 16",
    )
    canvas.header(title="低功耗三岔口：模式、时钟、电流",
                  tag="16", tag_color=T.CYAN)

    # 顶条：三档电流按对数刻度排开，「µA 与 mA 差三个数量级」一眼可见
    canvas.text(24, 82, "先给三个数找到位置：对数刻度，差的是数量级",
                size=12.5, fill=T.TEXT, weight="700")
    import math
    stages = [("Sleep 14.4 mA", 14400, T.RED), ("Stop 14 µA", 14, T.AMBER),
              ("Standby 2 µA", 2, T.CYAN)]
    x0, x1 = 120, 700

    def lx(ua: float) -> float:
        return x0 + (math.log10(ua) - math.log10(1.5)) / (math.log10(20000) - math.log10(1.5)) * (x1 - x0)

    canvas.line(x0, 128, x1, 128, stroke=T.GRID, sw=1)
    for ua, lab in ((2, "2 µA"), (14, "14 µA"), (1000, "1 mA"), (14400, "14 mA")):
        canvas.line(lx(ua), 122, lx(ua), 134, stroke=T.STROKE, sw=1)
        canvas.text(lx(ua), 148, lab, size=9.5, anchor="middle", fill=T.MUTED,
                    mono=True)
    for i, (lab, ua, color) in enumerate(stages):
        canvas.circle(lx(ua), 128, 7, fill=color)
        canvas.text(lx(ua), 112 - i * 0, lab, size=10.5, anchor="middle",
                    fill=color, weight="700")

    # 面板 A：模式锁存
    ay, ah = 168, 236
    canvas.rect(24, ay, 290, ah, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.rect(24, ay, 290, 5, fill=T.RED, rx=2)
    canvas.text(38, ay + 30, "① 进不去 Stop", size=13, fill=T.TEXT, weight="700")
    canvas.text(38, ay + 50, "电流停在 mA 级", size=10, fill=T.RED, mono=True)
    canvas.text(38, ay + 74, "两个位都要对：", size=11, fill=T.TEXT)
    canvas.rect(38, ay + 84, 262, 26, fill=T.BG2, stroke=T.GREEN, rx=4)
    canvas.text(50, ay + 102, "SCB_SCR  SLEEPDEEP = 1", size=10, fill=T.GREEN,
                mono=True)
    canvas.rect(38, ay + 114, 262, 26, fill=T.BG2, stroke=T.GREEN, rx=4)
    canvas.text(50, ay + 132, "PWR_CR   PDDS = 0", size=10, fill=T.GREEN,
                mono=True)
    canvas.text(38, ay + 160, "PDDS = 1 就是 Standby：", size=10.5, fill=T.RED)
    canvas.text(38, ay + 178, "SRAM / 寄存器丢，醒来走复位", size=10, fill=T.MUTED)
    canvas.text(38, ay + 200, "还要 PWR_CR LPDS = 1（低功耗稳压器）", size=9.5,
                fill=T.MUTED, mono=True)
    canvas.text(38, ay + 218, "且不开 IWDG —— 14 µA 那一格不含它", size=9.5,
                fill=T.RED)

    # 面板 B：醒来先 HSI 8 MHz
    bx, bw = 326, 300
    canvas.rect(bx, ay, bw, ah, fill=T.PANEL, stroke=T.AMBER, rx=8)
    canvas.rect(bx, ay, bw, 5, fill=T.AMBER, rx=2)
    canvas.text(bx + 14, ay + 30, "② 醒来跑飞", size=13, fill=T.TEXT,
                weight="700")
    canvas.text(bx + 14, ay + 50, "同一个 0x271，波特率差 9 倍", size=10,
                fill=T.AMBER, mono=True)
    canvas.text(bx + 14, ay + 74, "Stop 退出后的系统时钟：", size=11, fill=T.TEXT)
    bars = [("HSI 8 MHz", 8, "12800 bit/s", T.AMBER),
            ("PLL 72 MHz", 72, "115200 bit/s", T.GREEN)]
    for i, (lab, mhz, note, color) in enumerate(bars):
        y = ay + 88 + i * 46
        canvas.text(bx + 14, y, f"{lab} → {note}", size=10.5, fill=color,
                    weight="600")
        canvas.rect(bx + 14, y + 8, mhz / 72 * 246, 14, fill=color, rx=2,
                    opacity=0.8)
    canvas.text(bx + 14, ay + 190, "醒来第一件事：SystemClock_Config()",
                size=10.5, fill=T.GREEN)
    canvas.text(bx + 14, ay + 208, "定时叫醒靠 RTC 闹钟：LSE 32.768 kHz，", size=9.5,
                fill=T.MUTED)
    canvas.text(bx + 14, ay + 222, "PRL = 32767 → 1 Hz（F103 无周期唤醒定时器）",
                size=9.5, fill=T.MUTED)

    # 面板 C：µA 门槛的差值法
    cx, cw = 638, 298
    canvas.rect(cx, ay, cw, ah, fill=T.PANEL, stroke=T.CYAN, rx=8)
    canvas.rect(cx, ay, cw, 5, fill=T.CYAN, rx=2)
    canvas.text(cx + 14, ay + 30, "③ 电流降不下来", size=13, fill=T.TEXT,
                weight="700")
    canvas.text(cx + 14, ay + 50, "差值法：先测底，再逐个打开", size=10,
                fill=T.CYAN, mono=True)
    leaks = [("Stop 加 IWDG", "查实测", T.RED),
             ("Standby + LSI", "3.2 µA 总值", T.AMBER),
             ("10 kΩ 两端压差 3.3 V", "0.33 mA", T.VIOLET),
             ("2 mA LED 常亮", "2 mA", T.RED),
             ("悬空输入脚", "依电平测量", T.AMBER)]
    for i, (name, val, color) in enumerate(leaks):
        y = ay + 72 + i * 30
        canvas.text(cx + 14, y + 10, name, size=10, fill=T.TEXT)
        canvas.line(cx + 14, y + 19, cx + 180, y + 19, stroke=T.GRID, sw=1)
        canvas.text(cx + 192, y + 17, val, size=9.5, fill=color, mono=True)
    canvas.text(cx + 14, ay + 226, "悬空脚配 GPIO_MODE_ANALOG；输出脚给定电平",
                size=9, fill=T.MUTED)

    # 底条：Standby 的 2 µA 只属于一格
    by = 424
    canvas.rect(24, by, 912, 92, fill=T.BG2, stroke=T.VIOLET, rx=8)
    canvas.text(38, by + 24, "别把一格的条件当成整个模式：Standby 的 2 µA 有前提",
                size=12.5, fill=T.TEXT, weight="700")
    conds = [("LSI / IWDG / LSE / RTC 全关", "2 µA", T.GREEN),
             ("LSI 开着", "3.2 µA", T.AMBER),
             ("LSI + IWDG 都开", "3.4 µA", T.RED),
             ("Stop 用主稳压器", "24 µA", T.MUTED)]
    for i, (cond, val, color) in enumerate(conds):
        x = 38 + i * 222
        canvas.rect(x, by + 38, 208, 42, fill=T.PANEL, stroke=color, rx=4)
        canvas.text(x + 10, by + 56, cond, size=9.5, fill=T.MUTED)
        canvas.text(x + 10, by + 72, val, size=12, fill=color, weight="700",
                    mono=True)

    # 唤醒时间对照
    ty = 532
    canvas.text(24, ty, "唤醒时间不是加法：先到第一条指令，再算 PLL 锁定",
                size=12.5, fill=T.TEXT, weight="700")
    wakes = [("Stop · 低功耗稳压器", "5.4 µs", 5.4 / 50, T.GREEN),
             ("Stop · 主稳压器", "3.6 µs", 3.6 / 50, T.CYAN),
             ("Sleep", "1.8 µs", 1.8 / 50, T.VIOLET),
             ("Standby（走复位）", "50 µs", 1.0, T.AMBER)]
    for i, (name, val, frac, color) in enumerate(wakes):
        y = ty + 16 + i * 26
        canvas.text(24, y + 14, name, size=10.5, fill=T.TEXT)
        canvas.rect(220, y + 4, 420, 12, fill=T.BG2, stroke=T.GRID, rx=2)
        canvas.rect(220, y + 4, max(6, 420 * frac), 12, fill=color, rx=2,
                    opacity=0.8)
        canvas.text(652, y + 14, val, size=10.5, fill=color, mono=True)
    canvas.text(700, ty + 40, "PLL 锁定最大 200 µs，", size=10, fill=T.MUTED)
    canvas.text(700, ty + 58, "不与唤醒时间相加称呼。", size=10, fill=T.MUTED)
    canvas.text(700, ty + 76, "14 / 24 µA 是 3.3 V·25 °C 典型值；", size=9.5,
                fill=T.DIM)
    canvas.text(700, ty + 92, "200 / 180 µA 是 85 °C 最大值。", size=9.5,
                fill=T.DIM)

    canvas.rect(24, 674, 912, 34, fill=T.BG2, stroke=T.GREEN, rx=8)
    canvas.text(38, 696,
                "排查顺序：先确认模式位真的进了 Stop（电流台阶），再修唤醒后的时钟，最后才用差值法一颗颗抓耗电。",
                size=11, fill=T.TEXT)
    _credit(canvas, "自绘。电流与唤醒时间来自 DS5319 Rev 20 表 16 与表 26；IWDG 在 Stop 继续计数来自 RM0008 看门狗；12800 bit/s 由本章 0x271 与 8 MHz 算出。")
    return canvas


FIGURES = [
    ("sample-16-stop-compare.svg", mode_compare),
    ("sample-16-pwr-triage.svg", pwr_triage),
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

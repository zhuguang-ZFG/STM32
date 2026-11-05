#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Static B4 figures for chapter 11: IWDG vs WWDG side by side, RTC triage.

No CSS animation and no SMIL.

    python tools/sample_figs_b4/ch11_b4.py assets/diagrams
"""

from __future__ import annotations

import hashlib
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from svgkit import Svg, T, polyline_d


def _credit(canvas: Svg, note: str) -> None:
    canvas.line(24, canvas.h - 36, canvas.w - 24, canvas.h - 36, stroke=T.GRID, sw=1)
    canvas.text(24, canvas.h - 16, note, size=11, fill=T.MUTED)
    canvas.text(canvas.w - 24, canvas.h - 16, "自绘 · 静态 · CC BY 4.0", size=11, fill=T.DIM, anchor="end")


def _stairs(canvas: Svg, x: float, y: float, dx: float, dy: float, steps: int,
            color: str) -> tuple[float, float]:
    """Descending counter staircase; returns the final point."""
    pts = [(x, y)]
    for i in range(steps):
        pts.append((x + (i + 1) * dx, y + i * dy))
        pts.append((x + (i + 1) * dx, y + (i + 1) * dy))
    canvas.path(polyline_d(pts), stroke=color, sw=2)
    return pts[-1]


def wdg_compare() -> Svg:
    canvas = Svg(
        960,
        880,
        "Reload 624 是 1 秒且减到 0 才复位；WWDG 58.25 ms，大于 0x50 喂狗也复位",
        "STM32F103C8T6 · chapter 11 · DS5319 Rev 20 表 25 · RM0008 Rev 21 第 19、20 章",
    )
    canvas.header(tag="11", tag_color=T.CYAN)
    canvas.text(40, 86, "STM32F103C8T6   IWDG  LSI 40 kHz 典型、64 分频   WWDG  PCLK1 36 MHz、8 分频",
                size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "two countdowns, two reset rules: run to 0, or feed inside the window",
                size=14, fill=T.CYAN)
    canvas.text(40, 138, "IWDG 64 / 40000 × (624 + 1) = 1 s      WWDG 36e6 / 4096 / 8 × 64 = 58.25 ms",
                size=13, fill=T.AMBER, mono=True)

    canvas.text(40, 170, "两侧并置  IWDG 与 WWDG：复位条件不是一回事", size=16, fill=T.VIOLET, weight="700")
    canvas.rect(40, 184, 880, 276, fill=T.PANEL, stroke=T.VIOLET, rx=8)
    canvas.line(480, 200, 480, 444, stroke=T.GRID, sw=1)
    canvas.text(56, 216, "IWDG  独立看门狗", size=15, fill=T.GREEN, weight="700")
    canvas.text(496, 216, "WWDG  窗口看门狗", size=15, fill=T.RED, weight="700")

    rows = [
        ("时钟源", "LSI，独立于主时钟", "PCLK1，跟随 APB1"),
        ("计数器", "12 位递减，8 位预分频", "7 位递减 T[6:0]"),
        ("窗口", "无，随时可喂", "有，W[6:0] = 0x50"),
        ("复位条件", "减到 0 才复位", "喂早或喂晚都复位"),
        ("超时尺度", "0.1 ms ~ 26 s", "0.1 ms ~ 60 ms"),
        ("典型场景", "死机兜底、低功耗", "查周期任务是否按时"),
    ]
    for index, (label, left, right) in enumerate(rows):
        y = 252 + index * 36
        canvas.text(56, y, label, size=12, fill=T.MUTED)
        canvas.text(496, y, label, size=12, fill=T.MUTED)
        canvas.text(136, y, left, size=13,
                    fill=T.GREEN if index == 3 else T.TEXT, weight="600" if index == 3 else "normal")
        canvas.text(576, y, right, size=13,
                    fill=T.RED if index == 3 else T.TEXT, weight="600" if index == 3 else "normal")

    canvas.text(40, 492, "IWDG 的喂早不算错；WWDG 把喂狗时刻也纳入检查：太早说明程序跑快了，太晚说明跑慢了。",
                size=13, fill=T.MUTED)

    canvas.text(40, 530, "计数视角  两条曲线在哪里停下", size=16, fill=T.CYAN, weight="700")
    canvas.rect(40, 544, 880, 240, fill=T.PANEL, stroke=T.CYAN, rx=8)
    canvas.line(484, 556, 484, 780, stroke=T.GRID, sw=1)

    # IWDG: a plain countdown. Feeding early is legal.
    canvas.text(64, 584, "624", size=12, fill=T.MUTED, anchor="end", mono=True)
    canvas.text(64, 744, "0", size=12, fill=T.MUTED, anchor="end", mono=True)
    canvas.line(84, 580, 84, 740, stroke=T.STROKE, sw=1.5)
    end_x, end_y = _stairs(canvas, 84, 580, 52, 160 / 6, 6, T.GREEN)
    canvas.circle(end_x, end_y, 5, fill=T.RED)
    canvas.circle(188, 633, 5, fill=T.GREEN)
    canvas.text(120, 574, "喂早：不复位", size=12, fill=T.GREEN)
    canvas.line(196, 578, 190, 626, stroke=T.GREEN, sw=1, dash="4 4")
    canvas.text(56, 766, "624 → 0：喂早不复位，减到 0 才复位", size=12, fill=T.MUTED)

    # WWDG: the refresh window is a narrow band near the bottom.
    canvas.text(620, 572, "0x7F 起递减", size=11, fill=T.MUTED)
    canvas.text(612, 584, "0x7F", size=11, fill=T.MUTED, anchor="end", mono=True)
    canvas.text(612, 643, "0x50", size=11, fill=T.MUTED, anchor="end", mono=True)
    canvas.text(612, 663, "0x40", size=11, fill=T.MUTED, anchor="end", mono=True)
    canvas.text(612, 744, "0", size=11, fill=T.MUTED, anchor="end", mono=True)
    canvas.rect(620, 580, 130, 59, fill=T.BG2, stroke=T.RED, rx=2)
    canvas.rect(620, 639, 130, 20, fill=T.GREEN, stroke=T.GREEN, rx=2)
    canvas.rect(620, 659, 130, 81, fill=T.BG2, stroke=T.RED, rx=2)
    canvas.text(762, 612, "喂早 → 复位", size=12, fill=T.RED)
    canvas.text(762, 654, "窗口内 → 正常", size=12, fill=T.GREEN)
    canvas.text(762, 700, "喂晚 → 复位", size=12, fill=T.RED)
    canvas.text(500, 766, "窗口 0x50 到 0x40：两边喂都复位，只有中间能喂", size=12, fill=T.MUTED)

    _credit(canvas, "自绘。LSI 范围与 12/7 位递减来自 DS5319 Rev 20 表 25；1 秒与 58.25 ms 来自 RM0008 Rev 21 第 19、20 章。")
    return canvas


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


def rtc_triage() -> Svg:
    canvas = Svg(
        960,
        880,
        "PRL = 32767 才是 1 Hz；复位后归零查 VBAT 与 0xA5A5；闹钟比的是 32 位秒计数器",
        "STM32F103C8T6 · chapter 11 · DS5319 Rev 20 表 25 · RM0008 Rev 21 第 18 章",
    )
    canvas.header(title="RTC 三岔口：偏慢、归零、闹钟不响", tag="11", tag_color=T.CYAN)

    # ① 分频链
    canvas.text(24, 82, "先把分频链摆出来：分频比是 (PRL + 1)，不是 PRL", size=12.5,
                fill=T.TEXT, weight="700")
    canvas.rect(24, 92, 250, 44, fill=T.PANEL, stroke=T.CYAN, rx=8)
    canvas.text(38, 112, "LSE 32.768 kHz", size=11, fill=T.CYAN, weight="700")
    canvas.text(38, 128, "第 3 脚 PC14 / 第 4 脚 PC15", size=9, fill=T.MUTED)
    canvas.arrow(278, 114, 322, 114, color=T.STROKE, sw=1.5, head=6)
    canvas.rect(326, 92, 200, 44, fill=T.PANEL2, stroke=T.AMBER, rx=8)
    canvas.text(426, 112, "÷ (PRL + 1)", size=11, anchor="middle", fill=T.AMBER,
                weight="700", mono=True)
    canvas.text(426, 128, "写进 RTC_PRL 的值再加一", size=9, anchor="middle",
                fill=T.MUTED)
    canvas.arrow(530, 114, 574, 114, color=T.STROKE, sw=1.5, head=6)
    canvas.rect(578, 92, 130, 44, fill=T.PANEL, stroke=T.GREEN, rx=8)
    canvas.text(643, 112, "1 Hz", size=12, anchor="middle", fill=T.GREEN,
                weight="700")
    canvas.text(643, 128, "秒计数器 +1", size=9, anchor="middle", fill=T.MUTED)

    rows = [(T.GREEN, "PRL = 32767", "32768 ÷ 32768 = 1.000000 Hz", "✓ 正好 1 Hz"),
            (T.RED, "PRL = 32768", "32768 ÷ 32769 = 0.9999695 Hz", "✗ 慢 30.5 ppm ≈ 2.6 s/天")]
    for i, (color, key, calc, verdict) in enumerate(rows):
        y = 148 + i * 30
        canvas.rect(24, y, 912, 26, fill=T.BG2 if i == 0 else T.PANEL,
                    stroke=T.GRID, rx=4)
        canvas.text(36, y + 18, key, size=10, fill=color, mono=True)
        canvas.text(180, y + 18, calc, size=10, fill=T.TEXT, mono=True)
        canvas.text(560, y + 18, verdict, size=10, fill=color)

    # ② 三个岔口
    ay, ah = 220, 300
    cards = [
        (24, T.GREEN, "① 秒脉冲偏慢", "先确认源，再谈 PRL"),
        (326, T.AMBER, "② 复位后归零", "备份域没续上"),
        (628, T.VIOLET, "③ 闹钟不响", "比的是秒，不是日期"),
    ]
    for x, color, title, sub in cards:
        canvas.rect(x, ay, 292, ah, fill=T.PANEL, stroke=color, rx=8)
        canvas.rect(x, ay, 292, 5, fill=color, rx=2)
        canvas.text(x + 14, ay + 28, title, size=12.5, fill=T.TEXT, weight="700")
        canvas.text(x + 14, ay + 46, sub, size=9.5, fill=color)

    # ① LSI 范围条
    cx = 38
    canvas.text(cx, ay + 72, "LSI 备选：只给范围，不给保证", size=9.5, fill=T.TEXT)
    bx, bw2 = cx, 264
    canvas.rect(bx, ay + 80, bw2, 14, fill=T.BG2, stroke=T.GRID, rx=2)
    lo = bx + bw2 * (30 - 25) / 40
    hi = bx + bw2 * (60 - 25) / 40
    canvas.rect(lo, ay + 80, hi - lo, 14, fill=T.RED, rx=2, opacity=0.22)
    typ = bx + bw2 * (40 - 25) / 40
    canvas.line(typ, ay + 76, typ, ay + 98, stroke=T.AMBER, sw=2)
    canvas.text(bx, ay + 110, "25 kHz", size=8, fill=T.MUTED, mono=True)
    canvas.text(bx + bw2, ay + 110, "65 kHz", size=8, fill=T.MUTED, anchor="end",
                mono=True)
    canvas.text(typ, ay + 110, "40（典型）", size=8, anchor="middle", fill=T.AMBER,
                mono=True)
    canvas.text(cx, ay + 134, "30–60 kHz 漂：任何整数 PRL", size=9.5, fill=T.TEXT)
    canvas.text(cx, ay + 150, "都得不到稳定的 1 Hz", size=9.5, fill=T.RED)
    canvas.text(cx, ay + 174, "表 25 的 40 kHz 是典型值，", size=9.5, fill=T.MUTED)
    canvas.text(cx, ay + 190, "不是每片都保证的值", size=9.5, fill=T.MUTED)
    canvas.text(cx, ay + 214, "LSE 占了 PC14/PC15，", size=9.5, fill=T.TEXT)
    canvas.text(cx, ay + 230, "这两只脚就不能再当 GPIO", size=9.5, fill=T.TEXT)
    canvas.rect(cx, ay + 250, 264, 30, fill=T.BG2, stroke=T.GREEN, rx=4)
    canvas.text(cx + 10, ay + 269, "量 1 Hz 输出，或隔天读秒差", size=9,
                fill=T.GREEN)

    # ② VBAT 与魔法值
    cx = 340
    canvas.text(cx, ay + 72, "VBAT 第 1 脚续电，掉主电靠它", size=9.5, fill=T.TEXT)
    canvas.rect(cx, ay + 82, 120, 30, fill=T.PANEL2, stroke=T.CYAN, rx=4)
    canvas.text(cx + 60, ay + 101, "VBAT 第 1 脚", size=9, anchor="middle",
                fill=T.CYAN, mono=True)
    canvas.arrow(cx + 124, ay + 97, cx + 150, ay + 97, color=T.STROKE, sw=1.5, head=5)
    canvas.rect(cx + 154, ay + 82, 110, 30, fill=T.PANEL2, stroke=T.CYAN, rx=4)
    canvas.text(cx + 209, ay + 96, "备份域", size=9.5, anchor="middle", fill=T.TEXT)
    canvas.text(cx + 209, ay + 108, "10 × 16 位 = 20 B", size=8, anchor="middle",
                fill=T.MUTED, mono=True)
    canvas.text(cx, ay + 130, "上电先读 BKP_DR1", size=9.5, fill=T.TEXT)
    flow = [("= 0xA5A5", "读时间", T.GREEN), ("≠ 0xA5A5", "初始化日历并写回", T.RED)]
    for i, (test, act, color) in enumerate(flow):
        y = ay + 142 + i * 26
        canvas.text(cx + 4, y, test, size=9, fill=color, mono=True)
        canvas.arrow(cx + 62, y - 3, cx + 78, y - 3, color=color, sw=1, head=4)
        canvas.text(cx + 84, y, act, size=9, fill=T.TEXT)
    canvas.text(cx, ay + 202, "写备份域前：开 PWR 与 BKP 时钟，", size=9.5,
                fill=T.TEXT)
    canvas.text(cx, ay + 218, "再置 PWR_CR.DBP（没解锁写不进）", size=9.5,
                fill=T.AMBER)
    canvas.text(cx, ay + 240, "F1 只有 32 位秒计数，年月日软件算", size=9.5,
                fill=T.MUTED)
    canvas.rect(cx, ay + 250, 264, 30, fill=T.BG2, stroke=T.AMBER, rx=4)
    canvas.text(cx + 10, ay + 269, "断主电 60 s，看时间差与标记", size=9,
                fill=T.AMBER)

    # ③ 闹钟标尺
    cx = 642
    canvas.text(cx, ay + 72, "RTC_ALR 比的是 32 位秒计数", size=9.5, fill=T.TEXT)
    sx, sw2 = cx, 264
    canvas.rect(sx, ay + 88, sw2, 12, fill=T.BG2, stroke=T.GRID, rx=2)
    ticks = [(0, "0"), (21600, "6 h"), (43200, "12 h"), (64800, "18 h"), (86400, "24 h")]
    for sec, lab in ticks:
        px = sx + sw2 * sec / 86400
        canvas.line(px, ay + 100, px, ay + 106, stroke=T.GRID, sw=1)
        canvas.text(px, ay + 120, lab, size=8, fill=T.MUTED, anchor="middle",
                    mono=True)
    alarm = sx + sw2 * 28800 / 86400
    canvas.line(alarm, ay + 84, alarm, ay + 104, stroke=T.RED, sw=2)
    canvas.text(alarm + 4, ay + 82, "ALR = 28800 s", size=8.5, fill=T.RED, mono=True)
    canvas.text(cx, ay + 144, "写 08:00 却按日期匹配 → 不响", size=9.5, fill=T.TEXT)
    canvas.text(cx, ay + 160, "每天触发要掩掉日期与星期：", size=9.5, fill=T.TEXT)
    canvas.text(cx, ay + 176, "RTC_ALARMMASK_DATEWEEKDAY", size=8.5, fill=T.VIOLET,
                mono=True)
    canvas.text(cx, ay + 200, "先 HAL_RTC_GetTime 再 GetDate", size=9.5, fill=T.TEXT)
    canvas.text(cx, ay + 216, "读日期会锁存时间寄存器", size=9.5, fill=T.MUTED)
    canvas.text(cx, ay + 240, "F4 才是 BCD 的 TR/DR + RTC_ALRMxR", size=9.5,
                fill=T.MUTED)
    canvas.rect(cx, ay + 250, 264, 30, fill=T.BG2, stroke=T.VIOLET, rx=4)
    canvas.text(cx + 10, ay + 269, "先看中断使能，再看 ALR 落在哪秒", size=9,
                fill=T.VIOLET)

    # ③ 底部：机型差异与调试陷阱
    by = 542
    canvas.text(24, by, "两处容易记混的地方", size=12.5, fill=T.TEXT, weight="700")
    notes = [(T.CYAN, "备份寄存器数量", "C8（中容量）是 10 个 16 位，共 20 字节；", "资料里的 42 个是大容量型号"),
             (T.RED, "断点进来时间归零", "IWDG 没冻住：先 __HAL_DBGMCU_FREEZE_IWDG()，", "这不是 RTC 的问题")]
    for i, (color, head, l1, l2) in enumerate(notes):
        x = 24 + i * 462
        canvas.rect(x, by + 12, 450, 62, fill=T.PANEL, stroke=color, rx=8)
        canvas.text(x + 14, by + 32, head, size=10.5, fill=color, weight="700")
        canvas.text(x + 14, by + 50, l1, size=9.5, fill=T.TEXT)
        canvas.text(x + 14, by + 66, l2, size=9.5, fill=T.MUTED)

    canvas.rect(24, 636, 912, 56, fill=T.BG2, stroke=T.GREEN, rx=8)
    canvas.text(40, 660, "三个岔口各自的第一个动作：确认时钟源是 LSE；读 BKP_DR1；确认闹钟中断已使能。",
                size=11, fill=T.TEXT)
    canvas.text(40, 680, "三者都是先看「是不是我以为的那条路」，再谈寄存器数值。", size=11,
                fill=T.MUTED)

    # ④ 时钟源三选一
    sy = 712
    canvas.text(24, sy, "三种时钟源：精度差在源头，换 PRL 补不回来", size=12.5,
                fill=T.TEXT, weight="700")
    srcs = [(T.GREEN, "LSE", "32.768 kHz 晶振", "第 3 / 4 脚，走时才准"),
            (T.AMBER, "LSI", "40 kHz 典型，30–60 kHz", "内部 RC，只作备用"),
            (T.CYAN, "HSE ÷ 128", "8 MHz ÷ 128 = 62.5 kHz", "精度跟外部晶振走")]
    for i, (color, name, freq, note) in enumerate(srcs):
        x = 24 + i * 236
        canvas.rect(x, sy + 12, 224, 56, fill=T.PANEL, stroke=color, rx=8)
        canvas.text(x + 12, sy + 32, name, size=11, fill=color, weight="700")
        canvas.text(x + 12, sy + 48, freq, size=9.5, fill=T.TEXT, mono=True)
        canvas.text(x + 12, sy + 62, note, size=8.5, fill=T.MUTED)
    canvas.rect(740, sy + 12, 196, 56, fill=T.PANEL2, stroke=T.VIOLET, rx=8)
    canvas.text(838, sy + 33, "RTC 分频链", size=10.5, anchor="middle",
                fill=T.VIOLET, weight="700")
    canvas.text(838, sy + 49, "RTCCLK → (PRL+1) → 1 Hz", size=8, anchor="middle",
                fill=T.MUTED, mono=True)
    canvas.text(838, sy + 62, "换源就等于换 PRL", size=8.5, anchor="middle",
                fill=T.MUTED)

    _credit(canvas, "自绘。VBAT 与备份寄存器来自 DS5319 Rev 20 表 25；PRL、RTC_ALR 与 DBP 解锁来自 RM0008 Rev 21 第 18 章。")
    return canvas


FIGURES = [
    ("sample-11-wdg-compare.svg", wdg_compare),
    ("sample-11-rtc-triage.svg", rtc_triage),
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

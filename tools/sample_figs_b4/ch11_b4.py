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
        "PRL = 32767 才是 1 Hz；复位后归零查 VBAT；闹钟比的是 32 位秒计数器",
        "STM32F103C8T6 · chapter 11 · DS5319 Rev 20 表 25 · RM0008 Rev 21 第 18 章",
    )
    canvas.header(tag="11", tag_color=T.CYAN)
    canvas.text(40, 86, "STM32F103C8T6  LSE 32.768 kHz  PRL = 32767  VBAT pin 1  BKP_DR1 = 0xA5A5",
                size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "three symptoms, three branches: slow seconds, lost time, silent alarm",
                size=14, fill=T.CYAN)
    canvas.text(40, 138, "1 Hz = 32768 / (PRL + 1) → PRL = 32767      LSI 30 / 40 / 60 kHz 只给范围，不给保证",
                size=13, fill=T.AMBER, mono=True)

    _branch(
        canvas, 170, T.AMBER, "岔口一  秒脉冲偏慢：分频比是 (PRL + 1)", 196,
        "32768 Hz 除以 (PRL + 1)：写 32768 就是 32769 分频，秒脉冲偏慢",
        [
            ("PRL 写 32767 才是 32768 分频，正好 1 Hz。分频比里那个 +1 不能漏", T.TEXT),
            ("LSI 典型 40 kHz，实际在 30 到 60 kHz 之间漂：任何整数 PRL 都得不到稳定的 1 Hz", T.TEXT),
            ("40 kHz 只是表 25 的典型值，不是保证值；要走得准只能上 LSE 32.768 kHz", T.AMBER),
            ("LSE 占着第 3 脚 PC14 与第 4 脚 PC15，这两只脚就不能再当 GPIO", T.TEXT),
        ],
        "checkpoint：先确认走的是 LSE 不是 LSI，再谈 PRL；量 1 Hz 输出或隔天读秒差",
    )

    _branch(
        canvas, 396, T.RED, "岔口二  复位后时间归零：备份域没续上", 196,
        "备份域靠第 1 脚 VBAT 续电；主电源掉了、纽扣电池没接，日历就归零",
        [
            ("上电先读 BKP_DR1：读到 0xA5A5 才读时间，不匹配才初始化日历并写回魔法值", T.TEXT),
            ("写备份域前先开 PWR 与 BKP 时钟并置位 PWR_CR.DBP；没解锁，寄存器写不进去", T.TEXT),
            ("C8 是 10 个 16 位备份寄存器，共 20 字节；资料里的 42 个是大容量型号", T.TEXT),
            ("F1 的 RTC 只有 32 位秒计数器，年月日要软件换算；F4 才是 BCD 的 TR/DR", T.TEXT),
        ],
        "checkpoint：断开主电源 60 s 再恢复，时间差与 BKP 标记都在，续电链才算通",
    )

    _branch(
        canvas, 622, T.VIOLET, "岔口三  闹钟不响：比的是秒计数器", 160,
        "F1 的 RTC_ALR 比较的是 32 位秒计数器，不是年月日",
        [
            ("每天触发要掩掉日期与星期：AlarmMask = RTC_ALARMMASK_DATEWEEKDAY", T.TEXT),
            ("先 HAL_RTC_GetTime 再 HAL_RTC_GetDate：读日期会锁存时间寄存器", T.TEXT),
            ("F4 换成 BCD 日历与 RTC_ALRMxR，可按秒/分/时/日/星期掩码匹配", T.TEXT),
        ],
        "checkpoint：先确认闹钟中断已使能，再看 ALR 落在哪个秒数上",
    )

    canvas.rect(40, 800, 880, 30, fill=T.BG2, stroke=T.GREEN, rx=8)
    canvas.text(56, 820, "底注  断点停在 HAL_Delay 里被复位是 IWDG 没冻住，先用 __HAL_DBGMCU_FREEZE_IWDG()，不是 RTC 的问题。",
                size=12, fill=T.TEXT)

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

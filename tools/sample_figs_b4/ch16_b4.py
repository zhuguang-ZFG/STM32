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
        (662, "Standby", "关机，醒来重启", "SLEEPDEEP=1 PDDS=1", T.VIOLET),
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
    canvas.text(172, 354, "任意中断或事件", size=13, fill=T.TEXT)
    canvas.text(172, 376, "NVIC 使能的中断都算", size=12, fill=T.MUTED)
    canvas.text(423, 354, "EXTI 16 条、RTC", size=13, fill=T.TEXT)
    canvas.text(423, 376, "IWDG、USB 唤醒", size=12, fill=T.MUTED)
    canvas.text(674, 354, "WKUP 引脚（PA0 上升沿）", size=13, fill=T.TEXT)
    canvas.text(674, 376, "RTC 闹钟、IWDG、NRST", size=12, fill=T.MUTED)

    canvas.text(40, 438, "唤醒时间", size=13, fill=T.TEXT, weight="700")
    canvas.text(40, 458, "到第一条指令", size=11, fill=T.MUTED)
    canvas.text(172, 434, "1.8 µs", size=15, fill=T.GREEN, weight="700")
    canvas.text(172, 458, "沿用睡前的时钟", size=12, fill=T.TEXT)
    canvas.text(423, 434, "5.4 µs", size=15, fill=T.CYAN, weight="700")
    canvas.text(423, 458, "主稳压器那格 3.6 µs", size=12, fill=T.TEXT)
    canvas.text(674, 434, "50 µs", size=15, fill=T.VIOLET, weight="700")
    canvas.text(674, 458, "然后从复位向量重启", size=12, fill=T.TEXT)

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
    canvas.text(56, 766, "底注  14.4 mA 与 14 µA 差 1000 倍，三档不能写在同一行 mA 里；电流都是典型值，不是最大值。",
                size=12, fill=T.TEXT)
    canvas.text(56, 788, "1.4 µA 是备份域 IDD_VBAT，不是整机 Standby；表 16 没有「Stop 加 IWDG」这一格。",
                size=12, fill=T.TEXT)

    _credit(canvas, "自绘。电流、唤醒时间与保持状态来自 DS5319 Rev 20 表 16 与表 26；HSI 8 MHz 与重配时钟来自 RM0008 时钟。")
    return canvas


def pwr_triage() -> Svg:
    canvas = Svg(
        960,
        880,
        "进不去 Stop、醒来串口乱码、电流降不下来：14 µA 要 SLEEPDEEP=1 且 PDDS=0，醒来是 HSI 8 MHz，2 µA 只在 LSI、IWDG、LSE、RTC 全关时成立",
        "STM32F103C8T6 · chapter 16 · DS5319 Rev 20 表 16",
    )
    canvas.header(title="低功耗三岔口：模式、时钟、电流", tag="16", tag_color=T.CYAN)
    canvas.text(40, 86, "低功耗三岔口：先确认真进了 Stop，再看醒来的时钟，最后用差值法抓耗电大户",
                size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "three branches: mode latch / clock restore / idle current",
                size=14, fill=T.CYAN)
    canvas.text(40, 138,
                "SLEEPDEEP=1  PDDS=0  →  Stop 14 µA    唤醒 5.4 µs  →  HSI 8 MHz",
                size=13, fill=T.AMBER, mono=True)

    canvas.text(40, 170, "岔口一  进不去 Stop：电流还是 mA 级", size=16, fill=T.RED, weight="700")
    canvas.text(920, 170, "SLEEPDEEP · PDDS · PWR_CR", size=11, fill=T.MUTED, anchor="end", mono=True)
    canvas.rect(40, 184, 880, 174, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(56, 214, "症状：电流还在 14.4 mA 量级，醒来也不用重配时钟——它根本没进 Stop",
                size=14, fill=T.TEXT)
    canvas.text(56, 240, "原因 A：SLEEPDEEP 没置 1，只进了 Sleep。进 Stop 要 SLEEPDEEP=1、PDDS=0",
                size=14, fill=T.TEXT)
    canvas.text(56, 266, "原因 B：PDDS 写成 1，那是 Standby：SRAM 和寄存器丢失，醒来从复位向量重启",
                size=14, fill=T.TEXT)
    canvas.text(56, 292, "原因 C：WFI 前还有挂起中断，或 SWD/JTAG、USB 芯片在漏电，量不到 14 µA 那一格",
                size=14, fill=T.TEXT)
    canvas.text(56, 318, "检查点：14 µA 要求低功耗稳压器 PWR_LOWPOWERREGULATOR_ON，且不开 IWDG",
                size=14, fill=T.TEXT)
    canvas.text(56, 344, "探针：0.1 Ω 采样电阻串 3V3，用差分探头看进入瞬间的电流台阶",
                size=13, fill=T.MUTED)

    canvas.text(40, 386, "岔口二  醒来跑飞：时钟停在 HSI 8 MHz", size=16, fill=T.AMBER, weight="700")
    canvas.text(920, 386, "BRR 0x271 · 8 MHz vs 72 MHz", size=11, fill=T.MUTED, anchor="end", mono=True)
    canvas.rect(40, 400, 880, 174, fill=T.PANEL, stroke=T.AMBER, rx=8)
    canvas.text(56, 430, "症状：一帧串口乱码，或定时器变慢、外设不工作",
                size=14, fill=T.TEXT)
    canvas.text(56, 456, "原因：Stop 退出后系统时钟是 HSI 8 MHz，不是 16 MHz，也不是 72 MHz",
                size=14, fill=T.TEXT)
    canvas.text(56, 482, "数值：BRR 仍是 0x271，8e6 / (16 × 39.0625) = 12800；主机还停在 115200，差 9 倍",
                size=14, fill=T.TEXT)
    canvas.text(56, 508, "修复：醒来第一件事调 SystemClock_Config()，PLL 回 72 MHz 后再发下一个字节",
                size=14, fill=T.TEXT)
    canvas.text(56, 534, "定时唤醒：F103 没有 F4 的周期唤醒定时器，用 RTC 闹钟，LSE 32.768 kHz、PRL = 32767 得 1 Hz",
                size=14, fill=T.TEXT)
    canvas.text(56, 560, "别忘了：Stop 期间 SysTick 不跳，1000 Hz 的 1 ms 节拍要在醒来后重新对齐",
                size=13, fill=T.MUTED)

    canvas.text(40, 612, "岔口三  电流降不下来：µA 那一格的门槛", size=16, fill=T.VIOLET, weight="700")
    canvas.text(920, 612, "IWDG · GPIO_MODE_ANALOG · 0.33 mA", size=11, fill=T.MUTED,
                anchor="end", mono=True)
    canvas.rect(40, 626, 880, 164, fill=T.PANEL, stroke=T.VIOLET, rx=8)
    canvas.text(56, 654, "症状：进了 Stop 还是几十 µA 到 mA，或者待机被写成 2~3 µA 一个区间",
                size=14, fill=T.TEXT)
    canvas.text(56, 680, "原因 A：IWDG 在 Stop 和 Standby 里照走 LSI，而 14 µA 那一格不含独立看门狗",
                size=14, fill=T.TEXT)
    canvas.text(56, 706, "原因 B：悬空输入脚翻转漏电，配成模拟输入 GPIO_MODE_ANALOG；输出脚给定电平",
                size=14, fill=T.TEXT)
    canvas.text(56, 732, "原因 C：10 kΩ 上拉在 3.3 V 下约 0.33 mA，一颗 2 mA 的 LED 常亮就全白费",
                size=14, fill=T.TEXT)
    canvas.text(56, 758, "探针：先全关测干净底电流，再逐个打开做差值法；万用表 µA 档会拖低电压",
                size=13, fill=T.MUTED)

    canvas.rect(40, 796, 880, 40, fill=T.BG2, stroke=T.GREEN, rx=8)
    canvas.text(56, 812, "底注  Standby 的 2 µA 只属于 LSI、IWDG、LSE、RTC 全关那一格：LSI 开 3.2 µA，加 IWDG 3.4 µA。",
                size=12, fill=T.TEXT)
    canvas.text(56, 828, "14 µA 与 24 µA 是 3.3 V、25 °C 的典型值，5.4 µs 与 3.6 µs 是表 26 的唤醒时间；200 µA 与 180 µA 是 85 °C 最大值。",
                size=12, fill=T.TEXT)

    _credit(canvas, "自绘。电流与唤醒时间来自 DS5319 Rev 20 表 16 与表 26；IWDG 在 Stop 继续计数来自 RM0008 看门狗；12800 bit/s 由本章的 0x271 与 8 MHz 算出。")
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

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Static B3 figure for chapter 09: ADC reading triage in three branches.

No CSS animation and no SMIL.

    python tools/sample_figs_b3/ch09_b3.py assets/diagrams
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


def adc_triage() -> Svg:
    canvas = Svg(
        960,
        880,
        "ADC 读数不对先分三岔：末位抖动查采样时间，顶满或贴零查 VDDA，整体偏置查校准",
        "STM32F103C8T6 · chapter 09 · RM0008 Rev 21 第 11 章 · AN2834",
    )
    canvas.header(tag="09", tag_color=T.CYAN)
    canvas.text(40, 84, "STM32F103C8T6  LQFP48  pin 10 PA0 = ADC12_IN0    pin 9 VDDA = the reference",
                size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 108, "three symptoms, three different roots; one fix does not cover another branch",
                size=14, fill=T.CYAN)
    canvas.text(40, 132, "ADCCLK = 12 MHz (ADCPRE ÷ 6)   Tconv = SMP + 12.5 cycles   code × VDDA / 4096",
                size=13, fill=T.AMBER, mono=True)

    canvas.box(40, 140, 280, 54, label="① 末位抖动  jitter", sub="last bits move, mean drifts",
               size=14, color=T.RED, stroke=T.RED)
    canvas.box(340, 140, 280, 54, label="② 顶满或贴零  rail", sub="code stuck at 4095 or 0",
               size=14, color=T.AMBER, stroke=T.AMBER)
    canvas.box(640, 140, 280, 54, label="③ 系统性偏置  offset", sub="the same step on every code",
               size=14, color=T.VIOLET, stroke=T.VIOLET)

    canvas.text(40, 212, "岔口一  码值抖动  Low bits never settle", size=16, fill=T.RED, weight="700")
    canvas.rect(40, 224, 880, 218, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(56, 254, "Not random noise: the sampling capacitor never finished charging, so the leftover differs each read.",
                size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 281, "t_s ≈ (R_AIN + 1 kΩ) × 8 pF × ln(2^14) ≈ (R_AIN + 1 kΩ) × 78 ns",
                size=14, fill=T.AMBER, mono=True)
    canvas.text(56, 308, "100 kΩ source needs ≈ 7.8 µs; 1.5 cycles at 12 MHz gives only 125 ns, off by 60×.",
                size=14, fill=T.TEXT)
    canvas.text(56, 335, "SMPR2 SMP0[2:0] = 111  →  239.5 cycles = 19.958 µs at 12 MHz",
                size=14, fill=T.AMBER, mono=True)
    canvas.text(56, 362, "ADCCLK must stay ≤ 14 MHz: ADCPRE ÷ 6 gives 12 MHz; ÷ 4 gives 18 MHz and is out of spec.",
                size=14, fill=T.TEXT)
    canvas.text(56, 389, "R in series with C to GND helps only if R×C ≪ sample interval; ≥ 1 MΩ still needs a follower.",
                size=14, fill=T.TEXT)
    canvas.text(56, 416, "checkpoint: 100 kΩ source, 1.5 vs 239.5 cycles, 100 reads each, compare mean and spread.",
                size=13, fill=T.MUTED)

    canvas.text(40, 458, "岔口二  恒 4095 或恒 0  Code pinned to a rail", size=16, fill=T.AMBER, weight="700")
    canvas.rect(40, 470, 880, 184, fill=T.PANEL, stroke=T.AMBER, rx=8)
    canvas.text(56, 500, "4095 is a clamp, not a reading: VIN above VDDA turns on the input protection and the code saturates.",
                size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 526, "0 first: PA0 still a push-pull output reads the level it drives, not the divider behind it.",
                size=14, fill=T.TEXT)
    canvas.text(56, 552, "LQFP48 has no separate VREF+: pin 9 VDDA is the scale, so a 1 % droop shifts every code by 1 %.",
                size=14, fill=T.TEXT)
    canvas.text(56, 578, "Measure pin 9 to GND while conversions run, not at idle; a rail that sags under load moves full scale.",
                size=14, fill=T.TEXT)
    canvas.text(56, 604, "Keep VSSA ≤ VIN ≤ VDDA; size the divider for the highest input so a 5 V node never reaches the pin.",
                size=14, fill=T.TEXT)
    canvas.text(56, 630, "checkpoint: CH17 Vrefint → VDDA = 1.20 V × 4096 / code; cross-check with the meter at pin 9.",
                size=13, fill=T.MUTED)

    canvas.text(40, 670, "岔口三  系统性偏置  The same step on every code", size=16, fill=T.VIOLET, weight="700")
    canvas.rect(40, 682, 880, 140, fill=T.PANEL, stroke=T.VIOLET, rx=8)
    canvas.text(56, 710, "First codes after power-up are offset, and the offset does not follow the input: calibration was skipped.",
                size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 734, "Set ADON, wait two ADCCLK, then RSTCAL; RSTCAL must clear before a new CAL can take effect.",
                size=13, fill=T.TEXT)
    canvas.text(56, 758, "ADON=1 → 2 ADCCLK → RSTCAL=1 → poll RSTCAL=0 → CAL=1 → poll CAL=0",
                size=13, fill=T.AMBER, mono=True)
    canvas.text(56, 782, "No conversion runs during calibration; HAL_ADCEx_Calibration_Start goes before HAL_ADC_Start.",
                size=13, fill=T.TEXT)
    canvas.text(56, 806, "checkpoint: 0 V and half scale; a constant step at both is offset, a growing one is gain.",
                size=13, fill=T.MUTED)
    _credit(canvas, "自绘。校准流程与采样时间档位来自 RM0008 Rev 21 第 11 章；精度实践来自 AN2834。")
    return canvas


FIGURES = [
    ("sample-09-adc-triage.svg", adc_triage),
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

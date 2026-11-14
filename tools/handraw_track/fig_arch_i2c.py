# -*- coding: utf-8 -*-
"""I2C bus plate (ch16).

Facts pinned to the chapter: SDA/SCL are open-drain with pull-ups to 3.3 V;
the 7-bit addresses are 0x50 (24C02), 0x3C (SSD1306), 0x68 (MPU6050); and
t_r ~= 0.8473*R*C, so 4.7k/100pF is about 398 ns -- fine for 100 kHz,
too slow for 400 kHz (300 ns limit).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hd import *  # noqa: E402,F401,F403


def _device(f, x, y, w, h, title, lines, color):
    f.rect(x, y, w, h, color=color, fill=WHITE, sw=2.4)
    f.text(x + 14, y + 28, title, size=18, color=color, weight="bold")
    for i, ln in enumerate(lines):
        f.text(x + 14, y + 52 + i * 20, ln, size=13, color=INK)


def _tap(f, x, y_top, y_bottom, cross_y=None, color=INK, sw=2.2):
    """Vertical tap; optionally hop over a horizontal bus line at cross_y."""
    if cross_y is None:
        f.line(x, y_top, x, y_bottom, color=color, sw=sw)
    else:
        d = (f"M{x:.1f} {y_bottom:.1f} L{x:.1f} {cross_y + 9:.1f} "
             f"Q{x + 11:.1f} {cross_y:.1f} {x:.1f} {cross_y - 9:.1f} "
             f"L{x:.1f} {y_top:.1f}")
        f.body.append(
            f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{sw}" '
            f'stroke-linecap="round" stroke-linejoin="round"/>')


def i2c_bus():
    f = Fig("arch-i2c-bus", "I2C 总线：两根线、两只上拉、三种地址")

    scl_y, sda_y = 240, 290
    rail_y = 140

    # 3.3 V rail and two pull-ups
    f.line(40, rail_y, 960, rail_y, color=RED, sw=2.8)
    f.text(40, rail_y - 10, "3.3 V", size=14, color=RED, weight="bold")
    f.text(880, rail_y - 10, "上拉 4.7k ×2", size=14, color=AMBER_STROKE,
           weight="bold")
    for x in (60, 100):
        f.line(x, rail_y, x, rail_y + 16, color=INK, sw=2.0)
        f.rect(x - 17, rail_y + 16, 34, 30, color=AMBER_STROKE, fill=WHITE, sw=2.0)
        f.line(x, rail_y + 46, x, sda_y if x == 60 else scl_y, color=INK, sw=2.0)

    # horizontal SCL/SDA bus
    f.line(100, scl_y, 1060, scl_y, color=BLUE_D, sw=3.0)
    f.line(60, sda_y, 1060, sda_y, color=GREEN_D, sw=3.0)
    f.text(1066, scl_y - 6, "SCL", size=16, color=BLUE_D, weight="bold")
    f.text(1066, sda_y - 6, "SDA", size=16, color=GREEN_D, weight="bold")

    # devices below the bus, each with two taps (parallel, not a bridge)
    devices = [
        (60, "F407 / I2C1", ["PB6 SCL · PB7 SDA", "主机：发 START / STOP"],
         BLUE_D),
        (330, "24C02 EEPROM", ["7 位地址 0x50", "A2/A1/A0 接地"], RED),
        (580, "SSD1306 OLED", ["7 位地址 0x3C", "HAL 要传 0x78"], AMBER_STROKE),
        (830, "MPU6050", ["7 位地址 0x68", "上电默认睡眠，先唤醒"], GREEN_D),
    ]
    for x, title, lines, c in devices:
        _device(f, x, 360, 210, 110, title, lines, c)
        xs, xc = x + 40, x + 80
        _tap(f, xs, sda_y, 360, cross_y=None, color=GREEN_D)
        _tap(f, xc, scl_y, 360, cross_y=sda_y, color=BLUE_D)
        f.circle(xs, sda_y, 3.2, color=GREEN_D, fill=GREEN_D, sw=1.0)
        f.circle(xc, scl_y, 3.2, color=BLUE_D, fill=BLUE_D, sw=1.0)

    # notes
    f.text(78, 540, "开漏：器件只能拉低；全放开，上拉才把线送回高。", size=15,
           color=INK)
    f.text(78, 570, "线与：任何一个器件拉低，整条线就是低。", size=15, color=INK)
    f.text(700, 540, "t_r ≈ 0.8473·R·C", size=15, color=GREEN_D,
           weight="bold")
    f.text(700, 568, "4.7k / 100pF ≈ 398 ns", size=14, color=INK)
    f.text(700, 596, "100 kHz 够；400 kHz 不够", size=14, color=RED)

    f.htext(576, 700, "ACK、仲裁、时钟拉伸，都长在“线与”这条电气规则上。",
            size=18, color=AMBER_STROKE, anchor="middle", weight="bold",
            hl=True, hl_fill=AMBER_FILL)
    return f


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[2] / "assets" / "illustrations" / "handraw"
    save(i2c_bus(), str(out / "arch-i2c-bus.svg"))
    print("wrote arch-i2c-bus.svg")

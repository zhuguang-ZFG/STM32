# -*- coding: utf-8 -*-
"""BLE stack and GATT plate (ch32).

Facts pinned to the chapter: ESP32-S3 is BLE-only (BLE 5.0), Controller is a
precompiled library, Host is Bluedroid by default or NimBLE as a BLE-only
alternative, HCI is the internal VHCI path, and GATT nests
service -> characteristic -> descriptor. The CCCD is UUID 0x2902 and the
client writes 0x0001 to enable notifications. Legacy advertising is
31 bytes plus a 31-byte scan response.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hd import *  # noqa: E402,F401,F403


def _stack_box(f, y, title, sub, color, w=420):
    x = 80
    f.rect(x, y, w, 62, color=color, fill=WHITE, sw=2.3)
    f.text(x + 14, y + 26, title, size=18, color=color, weight="bold")
    f.text(x + 14, y + 48, sub, size=13, color=INK)


def _gatt_box(f, y, h, title, lines, color, w=400):
    x = 640
    f.rect(x, y, w, h, color=color, fill=WHITE, sw=2.4)
    f.text(x + 14, y + 28, title, size=19, color=color, weight="bold")
    for i, ln in enumerate(lines):
        f.text(x + 14, y + 52 + i * 21, ln, size=13, color=INK)


def ble_stack():
    f = Fig("arch-wifi-stack", "BLE 协议栈与 GATT 容器")

    # left: stack
    lx, ly, lw, lh = 48, 120, 520, 560
    f.rect(lx, ly, lw, lh, color=BLUE_D, fill=WHITE, sw=2.6)
    f.htext(lx + 16, ly + 30, "协议栈：上层调用，下层预编译", size=20,
            color=BLUE_D, weight="bold")
    layers = [
        (180, "App", "GATT / GAP 调用", BLUE_D),
        (264, "Host", "Bluedroid 默认；NimBLE 可选", GREEN_D),
        (348, "HCI", "VHCI 虚拟接口，不走串口", AMBER_STROKE),
        (432, "Controller", "预编译库；BLE 5.0", RED),
        (516, "PHY", "2.4 GHz；S3 单模 BLE", BLUE_D),
    ]
    for y, title, sub, c in layers:
        _stack_box(f, y, title, sub, c)
    for y in (242, 326, 410, 494):
        f.arrow(290, y, 290, y + 20, color=INK, sw=2.2, bend=0.0)
    f.text(80, 620,
           "Host 二选一，默认 Bluedroid；不是 NimBLE。", size=15, color=RED)

    # right: GATT tree
    rx, ry, rw, rh = 600, 120, 504, 560
    f.rect(rx, ry, rw, rh, color=GREEN_D, fill=WHITE, sw=2.6)
    f.htext(rx + 16, ry + 30, "GATT：三级容器", size=20,
            color=GREEN_D, weight="bold")
    _gatt_box(f, 180, 80, "Service", ["一组相关特征"], GREEN_D)
    _gatt_box(f, 300, 95, "Characteristic",
              ["值 + properties", "notify / read / write"], BLUE_D)
    _gatt_box(f, 435, 95, "Descriptor",
              ["CCCD：UUID 0x2902", "客户端写 0x0001 开 notify"], RED)
    f.arrow(840, 260, 840, 298, color=GREEN_D, sw=2.2, bend=0.0)
    f.arrow(840, 395, 840, 433, color=BLUE_D, sw=2.2, bend=0.0)
    f.text(640, 575, "订阅后，服务端在值变化时推送。", size=15, color=INK)
    f.text(640, 605, "legacy 广播 31B + scan response 31B。", size=14, color=MUTED)

    f.htext(576, 736,
            "S3 单模 BLE：没有经典蓝牙；Host 默认 Bluedroid，订阅靠 CCCD。",
            size=19, color=AMBER_STROKE, anchor="middle", weight="bold",
            hl=True, hl_fill=AMBER_FILL)
    return f


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[2] / "assets" / "illustrations" / "handraw"
    save(ble_stack(), str(out / "arch-wifi-stack.svg"))
    print("wrote arch-wifi-stack.svg")

# -*- coding: utf-8 -*-
"""ESP32 16 MB dual-OTA layout plate (ch17).

Offsets pinned to the chapter's partition CSV:
nvs 0x9000/0x5000, otadata 0xE000/0x2000, phy_init 0x10000/0x1000,
ota_0 0x20000/0x300000, ota_1 0x320000/0x300000, spiffs 0x620000/0x9E0000.
The arithmetic closes at 0x1000000 (16 MB).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hd import *  # noqa: E402,F401,F403


def _box(f, x, y, w, h, title, sub, color, size=17, body=13):
    f.rect(x, y, w, h, color=color, fill=WHITE, sw=2.2)
    f.text(x + 10, y + size + 6, title, size=size, color=color,
           weight="bold")
    if sub:
        f.text(x + 10, y + size + 26, sub, size=body, color=MUTED)


def ota_slots():
    f = Fig("arch-ota-slots", "ESP32 双 OTA / 16 MB address map")

    # metadata strip (not to scale)
    mx, my, mw, mh = 48, 120, 1056, 130
    f.rect(mx, my, mw, mh, color=AMBER_STROKE, fill=PAPER, sw=2.8)
    f.text(mx + 16, my + 28, "前 128 KB：启动与记账（放大，不按比例）", size=19,
           color=AMBER_STROKE, weight="bold")
    items = [
        ("0x0000", "bootloader", GREEN_D),
        ("0x8000", "分区表", AMBER_STROKE),
        ("0x9000", "nvs\n0x5000", BLUE_D),
        ("0xE000", "otadata\n0x2000", RED),
        ("0x10000", "phy_init\n0x1000", BLUE_D),
    ]
    x = mx + 16
    for addr, name, c in items:
        f.rect(x, my + 46, 190, 64, color=c, fill=WHITE, sw=1.9)
        f.text(x + 10, my + 68, addr, size=14, color=c, weight="bold")
        f.text(x + 10, my + 90, name.replace("\n", " / "), size=13, color=INK)
        x += 202

    # main area to scale: 0x20000..0x1000000
    bx, by, bw, bh = 48, 278, 1056, 128
    f.rect(bx, by, bw, bh, color=BLUE_D, fill=WHITE, sw=2.8)
    f.text(bx + 16, by + 28, "主区：ota_0 → ota_1 → spiffs（按比例）", size=19,
           color=BLUE_D, weight="bold")
    # widths proportional to 3MB/3MB/9.875MB over 16MB-0.125MB
    usable = 1024
    span = 0x1000000 - 0x20000
    w0 = int(usable * 0x300000 / span)
    w1 = w0
    w2 = usable - w0 - w1
    x = bx + 16
    for label, sub, w, c in [
        ("ota_0", "0x20000 / 3M", w0, RED),
        ("ota_1", "0x320000 / 3M", w1, RED),
        ("spiffs", "0x620000 / 0x9E0000", w2, GREEN_D),
    ]:
        f.rect(x, by + 46, w, 54, color=c, fill=PAPER, sw=2.0)
        f.text(x + 10, by + 68, label, size=16, color=c, weight="bold")
        f.text(x + 10, by + 88, sub, size=12, color=MUTED)
        x += w
    f.text(bx + 16, by + 118,
           "0x20000 + 0x300000 = 0x320000；+0x300000 = 0x620000；+0x9E0000 = 0x1000000。",
           size=14, color=MUTED)

    # OTA flow
    ox, oy, ow, oh = 48, 430, 1056, 196
    f.rect(ox, oy, ow, oh, color=RED, fill=WHITE, sw=2.8)
    f.htext(ox + 16, oy + 34, "OTA 轮换：先验镜像，再改票，重启自检", size=23,
            color=RED, weight="bold")
    boxes = [
        (66, "esp_ota_end", "镜像校验", GREEN_D),
        (306, "set_boot_partition", "改 otadata", AMBER_STROKE),
        (546, "reboot", "PENDING_VERIFY", BLUE_D),
        (786, "self-test", "mark valid / 回滚", RED),
    ]
    for x, title, sub, c in boxes:
        _box(f, x, oy + 54, 220, 58, title, sub, c, size=15)
    for x in (288, 528, 768):
        f.arrow(x, oy + 83, x + 16, oy + 83, color=INK, sw=1.9, bend=0.0)
    f.text(ox + 18, oy + 142,
           "校验不过：otadata 不动，旧槽继续跑；通过后才改票，下次启动进新槽。", size=16,
           color=INK)
    f.text(ox + 18, oy + 168,
           "自检不过：显式标 INVALID / 复位后 ABORTED，下次回旧槽；未开回滚则直接算有效。",
           size=15, color=RED)

    f.htext(576, 694, "两个 3 MB 槽 + 0x9E0000 spiffs，首尾相接正好铺满 16 MB。",
            size=21, color=AMBER_STROKE, anchor="middle", weight="bold",
            hl=True, hl_fill=AMBER_FILL)
    return f


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[2] / "assets" / "illustrations" / "handraw"
    save(ota_slots(), str(out / "arch-ota-slots.svg"))
    print("wrote arch-ota-slots.svg")

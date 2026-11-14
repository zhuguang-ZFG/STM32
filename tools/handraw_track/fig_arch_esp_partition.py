# -*- coding: utf-8 -*-
"""ESP32-S3 default single-app partition map (ch30).

Pinned to ESP-IDF v5.5.2:
- BOOTLOADER_OFFSET_IN_FLASH default 0x0 for ESP32-S3.
- PARTITION_TABLE_OFFSET default 0x8000.
- partitions_singleapp.csv auto-places nvs 0x9000/0x6000,
  phy_init 0xf000/0x1000, factory 0x10000/1M.
The CSV leaves Offset blank; gen_esp32part.py fills it.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hd import *  # noqa: E402,F401,F403


def _cell(f, x, y, w, h, label, color, size=17, fill=WHITE):
    f.rect(x, y, w, h, color=color, fill=fill, sw=2.0)
    f.text(x + 12, y + h / 2 + 6, label, size=size, color=INK)


def esp_partition():
    f = Fig("arch-esp32-partition-map",
            "ESP32-S3 默认分区表 / data-driven memory")

    # table header
    px, py, pw, ph = 48, 120, 1056, 400
    f.rect(px, py, pw, ph, color=BLUE_D, fill=PAPER, sw=3.0)
    f.text(px + 16, py + 36, "Name", size=18, color=BLUE_D, weight="bold")
    f.text(px + 220, py + 36, "Type / SubType", size=18, color=BLUE_D,
           weight="bold")
    f.text(px + 500, py + 36, "Offset", size=18, color=BLUE_D, weight="bold")
    f.text(px + 700, py + 36, "Size", size=18, color=BLUE_D, weight="bold")
    f.text(px + 860, py + 36, "它是什么", size=18, color=BLUE_D, weight="bold")
    f.line(px + 12, py + 48, px + pw - 12, py + 48, color=INK, sw=1.8,
           amp=0.8)

    rows = [
        ("bootloader", "—", "0x0000", "—", "第二棒；不在 CSV", GREEN_D),
        ("partition_table", "—", "0x8000", "0x1000", "表自身", AMBER_STROKE),
        ("nvs", "data / nvs", "0x9000", "0x6000", "Wi-Fi/BT 键值", BLUE_D),
        ("phy_init", "data / phy", "0xF000", "0x1000", "PHY 初始化参数", BLUE_D),
        ("factory", "app / factory", "0x10000", "1M", "当前 app", RED),
    ]
    y = py + 62
    for name, typ, off, size, note, c in rows:
        f.text(px + 16, y + 24, name, size=17, color=c, weight="bold")
        f.text(px + 220, y + 24, typ, size=16, color=INK)
        f.text(px + 500, y + 24, off, size=16, color=INK)
        f.text(px + 700, y + 24, size, size=16, color=INK)
        f.text(px + 860, y + 24, note, size=16, color=MUTED)
        f.line(px + 12, y + 36, px + pw - 12, y + 36, color=GRAY_FILL,
               sw=1.2, amp=0.3)
        y += 56

    f.text(px + 16, py + ph - 18,
           "Offset 在 CSV 里留空；gen_esp32part.py 按类型对齐：data 0x1000、app 0x10000。", size=16,
           color=MUTED)

    # OTA callout
    ox, oy, ow, oh = 48, 540, 1056, 146
    f.rect(ox, oy, ow, oh, color=RED, fill=WHITE, sw=2.8)
    f.htext(ox + 16, oy + 34, "OTA 双槽：factory 换成两个 app 区 + otadata", size=22,
            color=RED, weight="bold")
    f.text(ox + 18, oy + 68, "默认单 app：", size=16, color=MUTED)
    _cell(f, ox + 150, oy + 48, 150, 34, "factory 1M", RED, size=15)
    f.text(ox + 18, oy + 112, "双 OTA：", size=16, color=MUTED)
    _cell(f, ox + 150, oy + 90, 130, 34, "ota_0", RED, size=15)
    _cell(f, ox + 292, oy + 90, 130, 34, "ota_1", RED, size=15)
    _cell(f, ox + 434, oy + 90, 150, 34, "otadata", AMBER_STROKE, size=15)
    f.text(ox + 620, oy + 78,
           "nvs 存 Wi-Fi/BT 键值与 PHY 校准数据。", size=15, color=INK)
    f.text(ox + 620, oy + 104, "phy_init 默认不用；", size=12, color=MUTED)
    f.text(ox + 620, oy + 124, "开 CONFIG_ESP_PHY_INIT_DATA_IN_PARTITION 才读。",
           size=11, color=MUTED)

    # closing
    f.htext(576, 730, "留空不是没地址：data 0x1000、app 0x10000 对齐，排完再回读。",
            size=22, color=AMBER_STROKE, anchor="middle", weight="bold",
            hl=True, hl_fill=AMBER_FILL)
    return f


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[2] / "assets" / "illustrations" / "handraw"
    save(esp_partition(), str(out / "arch-esp32-partition-map.svg"))
    print("wrote arch-esp32-partition-map.svg")

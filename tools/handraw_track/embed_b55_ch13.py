# -*- coding: utf-8 -*-
"""B55: embed the ch13 remap-decision plate into the zh/en chapters."""
from embed import embed_after_text

SPECS = [
    ("docs/13-CAN总线.md",
     "第 45、46 脚同时是第 07 章 I2C1 的重映射脚，一个工程里只能给 CAN 或 I2C 之一。见 [DS5319](#source-ds5319-i2c)。",
     "ch13-remap-decision.png",
     "Handraw：CAN 引脚三选一（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。看哪里：三段梯子依次排除 PA11/PA12（第 14 章 USB 要用 D−/D+）、PD0/PD1（LQFP48 上是 HSE 晶振，且 36/48/64 脚封装不能重映射到端口 D）、落到 PB8/PB9（第 45/46 脚，也是 I2C1 的重映射脚）；证明什么：这块板只能选 PB8/PB9，而且这一对脚只给 CAN 或 I2C 之一；不能证明什么：板上实际接线、收发器供电与总线电平。出处：[DS5319 Rev 20 表 5](#source-ds5319-usbcan)、[RM0008 Rev 21](#source-rm0008-can)。"),
    ("docs/en/13-can.md",
     "Pins 45 and 46 are also the I2C1 remap from chapter 07, so one project can give them to CAN or to I2C, not both. See [DS5319](#source-ds5319-i2c).",
     "ch13-remap-decision.png",
     "Handraw: the CAN pin-pair decision (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). Where to look: three rungs rule out PA11/PA12 (chapter 14 USB needs D−/D+), then PD0/PD1 (HSE crystal on LQFP48, and 36/48/64-pin packages cannot remap CAN to port D), and land on PB8/PB9 (pins 45/46, also the I2C1 remap); Proves this board can only pick PB8/PB9, and that pair goes to CAN or I2C, not both; Cannot show board wiring, transceiver supply, or bus levels. See [DS5319 Rev 20 Table 5](#source-ds5319-usbcan) and [RM0008 Rev 21](#source-rm0008-can)."),
]

if __name__ == "__main__":
    bad = 0
    for spec in SPECS:
        if not embed_after_text(*spec):
            bad += 1
    if bad:
        raise SystemExit(f"{bad} embed(s) failed")

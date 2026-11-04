# -*- coding: utf-8 -*-
"""Embed ch21 handraw knowledge-track PNGs (ZH+EN)."""
from embed import run

ZH = "docs/21-原理图与实物图鉴.md"
EN = "docs/en/21-board-maps.md"

run([
    (ZH, "sample-21-board-compare.svg", "ch21-board-compare.png",
     "Handraw：BluePill/BlackPill/Nucleo 对照（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。三板对照封装、调试器、5 V 与 USB 路径；不是实拍。"),
    (ZH, "sample-21-vdd-3v3.svg", "ch21-vdd-3v3.png",
     "Handraw：BluePill 电源轨 5 V·3V3·VDDA·VBAT（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。先量 3V3 再怀疑固件；5 V→AMS1117→VDD/VDDA/VBAT；不是实拍。"),
    (ZH, "sample-21-usb-ttl.svg", "ch21-usb-ttl.png",
     "Handraw：USB-TTL 与 USART1 PA9/PA10（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。TX→PA10、RX→PA9、共地 3.3 V；勿把 5 V 灌进 PA10；不是实拍。"),
    (ZH, "sample-21-hse-load.svg", "ch21-hse-load.png",
     "Handraw：HSE 8 MHz PD0/PD1 与负载电容（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。HSERDY 不到先查晶振焊接，再怪 PLLMUL；不是实拍。"),
    (ZH, "sample-21-nrst-boot0.svg", "ch21-nrst-boot0.png",
     "Handraw：NRST 与 BOOT0 引脚 7/44（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。BOOT0=0 从 Flash；BOOT0=1 进系统存储器，不是程序丢了；不是实拍。"),

    (EN, "sample-21-board-compare.svg", "ch21-board-compare.png",
     "Handraw: BluePill/BlackPill/Nucleo compare (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). Compare package, debugger, 5 V path, and USB path across three boards; not a photo."),
    (EN, "sample-21-vdd-3v3.svg", "ch21-vdd-3v3.png",
     "Handraw: BluePill rails 5 V·3V3·VDDA·VBAT (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). Measure 3V3 before blaming firmware; 5 V→AMS1117→VDD/VDDA/VBAT; not a photo."),
    (EN, "sample-21-usb-ttl.svg", "ch21-usb-ttl.png",
     "Handraw: USB-TTL to USART1 PA9/PA10 (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). TX→PA10, RX→PA9, shared GND at 3.3 V; do not feed 5 V into PA10; not a photo."),
    (EN, "sample-21-hse-load.svg", "ch21-hse-load.png",
     "Handraw: HSE 8 MHz PD0/PD1 and load caps (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). If HSERDY never sets, check crystal solder first, then PLLMUL; not a photo."),
    (EN, "sample-21-nrst-boot0.svg", "ch21-nrst-boot0.png",
     "Handraw: NRST and BOOT0 pins 7/44 (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). BOOT0=0 boots Flash; BOOT0=1 runs system memory—not lost firmware; not a photo."),
])

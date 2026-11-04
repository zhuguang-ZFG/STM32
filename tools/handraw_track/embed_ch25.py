# -*- coding: utf-8 -*-
"""Embed ch25 handraw knowledge-track PNGs (ZH+EN)."""
from embed import run

ZH = "docs/25-STM32H7引脚.md"
EN = "docs/en/25-stm32h7-pins.md"

run([
    (ZH, "pinout-stm32h743zi-lqfp144.svg", "ch25-part-id.png",
     "Handraw：H743ZIT6 订购解码（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。Z=144 脚、I=2 MB Flash；1.62–3.6 V；D1/D2/D3 三域；2×FDCAN 与 2×OTG；封装核对从 PE2 起再数 VCAP1/2、VDD33USB、PDR_ON；不是实拍。"),
    (ZH, "h7-power-domains.svg", "ch25-pin-compare.png",
     "Handraw：F1/F4 与 H7 的脚差异（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。第 1 脚 PE2；VCAP1=71、VCAP2=106 外接电容；脚 95 VDD33USB；脚 143 PDR_ON；脚 138 BOOT0；CAN 是 FDCAN 不是 bxCAN；不是实拍。"),
    (ZH, "sample-25-voltage-scale.svg", "ch25-rev-vos.png",
     "Handraw：revision 与 VOS 门禁（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。Rev Y/W 无 VOS0，VOS1 上限 400 MHz；Rev V 才可进 VOS0 到 480 MHz，每次换挡等 VOSRDY；读 DBGMCU->IDCODE 的 REV_ID 对照 RM0433/ES0392；不是实拍。"),
    (ZH, "sample-25-hse-to-480-flow.svg", "ch25-clock-math.png",
     "Handraw：8 MHz 到 400/480 可复算（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。8/PLLM4×PLLN/PLLP2：N=400 得 400 MHz，Rev V 改 N=480 得 480 MHz；CPU 480 / HCLK 240 / PCLK 120 / APB 定时器 240 各算各的；不是实拍。"),
    (ZH, "h7-pinmux-conflicts.svg", "ch25-pinmux.png",
     "Handraw：一只脚一个所有者（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。PA11/PA12 是 FDCAN1 与 OTG_FS 抢的脚，FDCAN1 迁 PD0/PD1 或 PB8/PB9；PB6/PB7 同理在 USART1 与 I2C1 之间二选一；不是实拍。"),

    (EN, "pinout-stm32h743zi-lqfp144.svg", "ch25-part-id.png",
     "Handraw: decoding STM32H743ZIT6 (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). Z=144 pins, I=2 MB Flash; 1.62–3.6 V; D1/D2/D3 domains; 2×FDCAN and 2×OTG; verify from PE2 pin 1, then VCAP1/2, VDD33USB, PDR_ON; not a photo."),
    (EN, "h7-power-domains.svg", "ch25-pin-compare.png",
     "Handraw: F1/F4 vs H7 pins (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). Pin 1 is PE2; VCAP1=71, VCAP2=106 with external caps; pin 95 VDD33USB; pin 143 PDR_ON; pin 138 BOOT0; CAN is FDCAN, not bxCAN; not a photo."),
    (EN, "sample-25-voltage-scale.svg", "ch25-rev-vos.png",
     "Handraw: revision and VOS gate (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). Rev Y/W lack VOS0, capped at 400 MHz in VOS1; only Rev V may enter VOS0 for 480 MHz, waiting for VOSRDY each step; read REV_ID from DBGMCU->IDCODE; not a photo."),
    (EN, "sample-25-hse-to-480-flow.svg", "ch25-clock-math.png",
     "Handraw: 8 MHz to 400/480 arithmetic (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). 8/PLLM4×PLLN/PLLP2: N=400 gives 400 MHz; Rev V sets N=480; CPU 480 / HCLK 240 / PCLK 120 / APB timer 240 are separate numbers; not a photo."),
    (EN, "h7-pinmux-conflicts.svg", "ch25-pinmux.png",
     "Handraw: one pin, one owner (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). PA11/PA12 is shared by FDCAN1 and OTG_FS; move FDCAN1 to PD0/PD1 or PB8/PB9; PB6/PB7 likewise sits between USART1 and I2C1; not a photo."),
])

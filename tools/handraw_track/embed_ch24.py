# -*- coding: utf-8 -*-
"""Embed ch24 handraw knowledge-track PNGs (ZH+EN)."""
from embed import run

ZH = "docs/24-STM32L4引脚.md"
EN = "docs/en/24-stm32l4-pins.md"

run([
    (ZH, "pinout-stm32l476rg-lqfp64.svg", "ch24-part-id.png",
     "Handraw：L476RG 电流档（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。M4F @ 80 MHz、1.71–3.6 V；VBAT 300 nA、Shutdown 30 nA、Standby 120 nA、Stop 2 1.1 µA、Run LDO 100 µA/MHz；封面典型值不等于整板实测；不是实拍。"),
    (ZH, "sample-24-mode-compare.svg", "ch24-modes.png",
     "Handraw：醒来从哪里继续（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。Sleep/Stop 0·1·2 从 WFI 下一条指令继续，SRAM1/2 保持；Standby/Shutdown 唤醒走复位，主 SRAM 丢；两类混记会把丢的 RAM 当还在；不是实拍。"),
    (ZH, "sample-24-wake-restore-flow.svg", "ch24-wake-clocks.png",
     "Handraw：醒后时钟恢复（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。STOPWUCK 选 MSI/HSI16 临时接管；SysTick、UART BRR、Flash LATENCY、ARR/PSC 都要按新时钟重算；USB 等 PLL 回来再用；不是实拍。"),
    (ZH, "sample-24-wake-triage.svg", "ch24-pin-mux.png",
     "Handraw：L476RG 抢脚清单（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。PA11/PA12 是 CAN1 与 OTG_FS 抢脚，都要就 CAN 改 PB8/PB9；VDDUSB 脚 48 是电源不是 GPIO；BOOT0=60 不与 SWCLK 共用；不是实拍。"),
    (ZH, "sample-24-idd-jp6.svg", "ch24-idd.png",
     "Handraw：JP6 测量边界（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。JP6 串表只量 MCU IDD；ST-LINK/LED/回灌不在其中；万用表负担电压会让 VDD 下跌；f_s ≥ 10/t_min；不是实拍。"),

    (EN, "pinout-stm32l476rg-lqfp64.svg", "ch24-part-id.png",
     "Handraw: L476RG current tiers (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). M4F @ 80 MHz, 1.71–3.6 V; VBAT 300 nA, Shutdown 30 nA, Standby 120 nA, Stop 2 1.1 µA, Run LDO 100 µA/MHz; datasheet typicals are not your board's measurement; not a photo."),
    (EN, "sample-24-mode-compare.svg", "ch24-modes.png",
     "Handraw: where do you wake up (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). Sleep/Stop 0·1·2 resume after WFI with SRAM1/2 kept; Standby/Shutdown wake through reset and lose main SRAM; mixing them treats lost RAM as alive; not a photo."),
    (EN, "sample-24-wake-restore-flow.svg", "ch24-wake-clocks.png",
     "Handraw: clocks after Stop 2 (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). STOPWUCK hands over to MSI/HSI16; SysTick, UART BRR, Flash LATENCY and ARR/PSC all need recomputing; wait for PLL before USB; not a photo."),
    (EN, "sample-24-wake-triage.svg", "ch24-pin-mux.png",
     "Handraw: L476RG shared pins (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). PA11/PA12 is shared between CAN1 and OTG_FS — move CAN to PB8/PB9; VDDUSB pin 48 is a supply pin; BOOT0=60 is separate from SWCLK; not a photo."),
    (EN, "sample-24-idd-jp6.svg", "ch24-idd.png",
     "Handraw: JP6 measures the MCU only (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). Removing JP6 (IDD) meters only the MCU current; ST-LINK, LEDs and GPIO back-feed are outside it; meter burden voltage can reset the MCU; f_s ≥ 10/t_min; not a photo."),
])

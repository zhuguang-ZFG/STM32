# -*- coding: utf-8 -*-
"""Embed ch23 handraw knowledge-track PNGs (ZH+EN)."""
from embed import run

ZH = "docs/23-STM32G0引脚.md"
EN = "docs/en/23-stm32g0-pins.md"

run([
    (ZH, "pinout-stm32g071rb-lqfp64.svg", "ch23-part-id.png",
     "Handraw：STM32G071RB 订购解码（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。M0+ @ 64 MHz、R=64 脚、B=128 KB；UCPD 不是 USB 设备控制器；无 CAN；不是实拍。"),
    (ZH, "sample-23-boot-latch.svg", "ch23-boot-latch.png",
     "Handraw：PA14 BOOT0=SWCLK 锁存（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。第四个 SYSCLK 上升沿锁存启动源；BOOT_LOCK / nBOOT_SEL 边界；不是实拍。"),
    (ZH, "sample-23-f1-g0-compare.svg", "ch23-pin-compare.png",
     "Handraw：F103 与 G071RB 脚差异（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。第 1 脚、NRST、BOOT/SWD 共脚、复位后模拟输入；AF 看 DS12232 Table 13/14；不是实拍。"),
    (ZH, "sample-23-f1-copy-traps.svg", "ch23-pinmux.png",
     "Handraw：G071RB 复用速查（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。PA14=BOOT0+SWCLK；USART/I2C/SPI 脚位；PA9/PA10 重映射先动 SYSCFG_CFGR1；不是实拍。"),

    (EN, "pinout-stm32g071rb-lqfp64.svg", "ch23-part-id.png",
     "Handraw: decoding STM32G071RB (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). M0+ @ 64 MHz, R=64 pins, B=128 KB; UCPD is not a USB device controller; no CAN; not a photo."),
    (EN, "sample-23-boot-latch.svg", "ch23-boot-latch.png",
     "Handraw: PA14 BOOT0=SWCLK latch (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). Boot source latches on the 4th SYSCLK rising edge; BOOT_LOCK / nBOOT_SEL boundaries; not a photo."),
    (EN, "sample-23-f1-g0-compare.svg", "ch23-pin-compare.png",
     "Handraw: F103 vs G071RB pins (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). Pin 1, NRST, shared BOOT/SWD, analog reset state; AF from DS12232 Table 13/14; not a photo."),
    (EN, "sample-23-f1-copy-traps.svg", "ch23-pinmux.png",
     "Handraw: G071RB AF quick map (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). PA14=BOOT0+SWCLK; USART/I2C/SPI homes; remap PA9/PA10 only after SYSCFG_CFGR1; not a photo."),
])

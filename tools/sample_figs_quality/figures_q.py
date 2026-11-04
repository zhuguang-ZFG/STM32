#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""High-density static Handraw figures for pilot chapters 02/03/06/09/10."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from svgkit import Svg, T
from sample_figs_quality._common import credit


def ch02_pll_lock() -> Svg:
    c = Svg(960, 880, "PLL lock ledger", "HSE 8 MHz x9 = 72 MHz")
    c.header(tag="02", tag_color=T.CYAN)
    c.text(40, 86, "STM32F103C8T6  LQFP48  HSE 8 MHz on PD0/PD1", size=16, fill=T.TEXT, weight="700")
    c.text(40, 112, "Goal: SYSCLK=72 MHz, SWS=10, LATENCY=2", size=14, fill=T.CYAN)
    steps = [
        ("1 HSE ON", "RCC_CR HSEON=1", "wait HSERDY=1", T.AMBER),
        ("2 PLL src", "PLLSRC=1 PLLXTPRE=0", "8 MHz into PLL", T.CYAN),
        ("3 multiply", "PLLMUL=0111 (x9)", "lock at 72 MHz", T.GREEN),
        ("4 switch", "SW=10 wait SWS=10", "SYSCLK from PLL", T.VIOLET),
    ]
    for i, (t, a, b, col) in enumerate(steps):
        x = 40 + i * 230
        c.rect(x, 140, 210, 120, fill=T.PANEL, stroke=col, rx=8)
        c.text(x + 105, 172, t, size=15, anchor="middle", fill=col, weight="700")
        c.text(x + 105, 200, a, size=12, anchor="middle", fill=T.TEXT, mono=True)
        c.text(x + 105, 228, b, size=12, anchor="middle", fill=T.MUTED)
        if i < 3:
            c.arrow(x + 214, 200, x + 226, 200, color=T.STROKE, sw=2)
    c.title_block(40, 290, "Register snapshot (RM0008 Rev 21 sec.7)", color=T.GREEN)
    rows = [
        ("RCC_CR", "bit17 HSERDY", "1 = crystal ready", T.AMBER),
        ("RCC_CR", "bit25 PLLRDY", "1 = PLL locked", T.GREEN),
        ("RCC_CFGR", "[3:2] SWS", "10 = PLL drives SYSCLK", T.CYAN),
        ("FLASH_ACR", "[2:0] LATENCY", "2 = 48..72 MHz @ 2.7-3.6 V", T.VIOLET),
    ]
    for i, (reg, bit, note, col) in enumerate(rows):
        y = 322 + i * 52
        c.rect(40, y, 880, 46, fill=T.PANEL, stroke=T.STROKE, rx=8)
        c.text(56, y + 28, reg, size=14, fill=col, weight="700", mono=True)
        c.text(220, y + 28, bit, size=13, fill=T.TEXT, mono=True)
        c.text(880, y + 28, note, size=13, fill=T.MUTED, anchor="end")
    c.rect(40, 540, 880, 100, fill=T.BG2, stroke=T.RED, rx=8)
    c.text(56, 574, "Fail read: HSERDY=0 => do not touch PLLMUL; SWS=00 means still HSI 8 MHz", size=14, fill=T.RED, weight="700")
    c.text(56, 604, "BRR/SysTick written for 72 MHz then divide wrong (115200->12800, 1 ms->9 ms)", size=13, fill=T.MUTED)
    c.rect(40, 660, 880, 90, fill=T.PANEL, stroke=T.CYAN, rx=8)
    c.text(56, 694, "First frame readable: four lock steps + four registers. Not a decor bar.", size=14, fill=T.TEXT, weight="700")
    c.text(56, 724, "Numbers from RM0008 clock tree and DS5319 HSE pins; knowledge track, not a scope photo.", size=13, fill=T.MUTED)
    credit(c, "Hand-drawn. PLL/SWS/LATENCY from RM0008 Rev 21 sec.7; package pins from DS5319 Rev 20.")
    return c


def ch02_flash_latency() -> Svg:
    c = Svg(960, 880, "Flash wait-state bands", "SYSCLK band sets LATENCY")
    c.header(tag="02", tag_color=T.AMBER)
    c.text(40, 86, "FLASH_ACR LATENCY vs SYSCLK (2.7-3.6 V)", size=16, fill=T.TEXT, weight="700")
    bands = [
        ("0 WS", "0 - 24 MHz", "reset default", T.GREEN, "HSI 8 MHz lives here"),
        ("1 WS", "24 - 48 MHz", "mid band", T.CYAN, "common 36/48 MHz setups"),
        ("2 WS", "48 - 72 MHz", "F103 full speed", T.AMBER, "HSE x9 = 72 MHz needs 2"),
    ]
    for i, (ws, band, tag, col, note) in enumerate(bands):
        y = 120 + i * 110
        c.rect(40, y, 880, 96, fill=T.PANEL, stroke=col, rx=8)
        c.text(64, y + 36, ws, size=22, fill=col, weight="700", mono=True)
        c.text(200, y + 32, band, size=16, fill=T.TEXT, weight="700")
        c.text(200, y + 58, tag, size=13, fill=T.MUTED)
        c.text(880, y + 48, note, size=13, fill=col, anchor="end")
    c.rect(40, 460, 880, 120, fill=T.BG2, stroke=T.RED, rx=8)
    c.text(56, 494, "Mismatch: LATENCY=0 at 72 MHz -> fetch HardFault / Flash garbage", size=14, fill=T.RED, weight="700")
    c.text(56, 524, "Mismatch: LATENCY=2 stuck on HSI 8 MHz -> safe, but proves nobody recomputed after switch", size=14, fill=T.AMBER)
    c.text(56, 554, "Order: raise LATENCY before raising SYSCLK; reverse when lowering", size=13, fill=T.MUTED)
    c.rect(40, 610, 880, 100, fill=T.PANEL, stroke=T.VIOLET, rx=8)
    c.text(56, 644, "Probe: read FLASH_ACR[2:0] and RCC_CFGR SWS, then match SystemCoreClock", size=14, fill=T.TEXT, weight="700")
    c.text(56, 674, "Do not trust CubeMX ticks alone; three registers must tell one story after boot", size=13, fill=T.MUTED)
    credit(c, "Hand-drawn. Wait-state bands compressed from RM0008 Flash interface; pairs with HSE-fail ledger.")
    return c


def ch02_bus_matrix() -> Svg:
    c = Svg(960, 880, "AHB/APB attachment map", "Who sits on 72 MHz vs APB1 /2")
    c.header(tag="02", tag_color=T.VIOLET)
    c.text(40, 86, "F103 @ SYSCLK 72 MHz: HCLK=72, PCLK2=72, PCLK1=36", size=15, fill=T.TEXT, weight="700")
    c.rect(40, 120, 880, 70, fill=T.PANEL, stroke=T.GREEN, rx=8)
    c.text(56, 150, "AHB 72 MHz", size=16, fill=T.GREEN, weight="700")
    c.text(220, 150, "GPIO / DMA / SRAM / Flash I/F / CRC", size=14, fill=T.TEXT)
    c.rect(40, 210, 420, 200, fill=T.PANEL, stroke=T.CYAN, rx=8)
    c.text(56, 244, "APB2 72 MHz", size=16, fill=T.CYAN, weight="700")
    for i, line in enumerate(["USART1", "SPI1", "ADC1/2 (ADC prescaler <=14 MHz)", "TIM1", "GPIO clocks also from APB2"]):
        c.text(56, 280 + i * 24, "- " + line, size=13, fill=T.TEXT)
    c.rect(500, 210, 420, 200, fill=T.PANEL, stroke=T.PINK, rx=8)
    c.text(516, 244, "APB1 36 MHz", size=16, fill=T.PINK, weight="700")
    for i, line in enumerate(["USART2/3", "I2C1/2", "SPI2", "TIM2-7 (timer clk may x2=72)", "CAN / USB 48 MHz separate"]):
        c.text(516, 280 + i * 24, "- " + line, size=13, fill=T.TEXT)
    c.rect(40, 440, 880, 130, fill=T.BG2, stroke=T.AMBER, rx=8)
    c.text(56, 476, "Before baud/timer math: which bus is the peripheral on?", size=15, fill=T.AMBER, weight="700")
    c.text(56, 508, "USART1 uses PCLK2=72e6; USART2 uses PCLK1=36e6. Same BRR formula, different input clock.", size=13, fill=T.TEXT)
    c.text(56, 540, "TIM2-7: when APB1 prescaler != 1, timer clock auto-x2 back to 72 MHz.", size=13, fill=T.MUTED)
    c.rect(40, 600, 880, 100, fill=T.PANEL, stroke=T.STROKE, rx=8)
    c.text(56, 636, "Placed after naming rules, before boot modes — breaks the long text wall.", size=14, fill=T.TEXT, weight="700")
    c.text(56, 666, "Knowledge-track schematic, not PCB routing; numbers follow RM0008 full-speed tree.", size=13, fill=T.MUTED)
    credit(c, "Hand-drawn. Bus map compressed from RM0008 clock tree; complements sample-02-clock-tree.")
    return c


def ch03_moder_map() -> Svg:
    c = Svg(960, 880, "GPIO four-register map", "PC13 LED: MODER/OTYPER/PUPDR/OSPEEDR + BSRR")
    c.header(tag="03", tag_color=T.GREEN)
    c.text(40, 86, "Blue Pill user LED = PC13, active-low (cathode to MCU)", size=15, fill=T.TEXT, weight="700")
    regs = [
        ("MODER", "01 = output", "PC13 as GPO, not AF", T.CYAN),
        ("OTYPER", "0 = push-pull", "push-pull drives LED; OD needs pull-up", T.GREEN),
        ("PUPDR", "00 = none", "board already has series resistor path", T.AMBER),
        ("OSPEEDR", "00/01 enough", "LED does not need 50 MHz", T.VIOLET),
    ]
    for i, (r, v, note, col) in enumerate(regs):
        y = 120 + i * 78
        c.rect(40, y, 880, 68, fill=T.PANEL, stroke=col, rx=8)
        c.text(56, y + 28, r, size=16, fill=col, weight="700", mono=True)
        c.text(200, y + 28, v, size=15, fill=T.TEXT, weight="700", mono=True)
        c.text(56, y + 52, note, size=13, fill=T.MUTED)
    c.rect(40, 450, 880, 140, fill=T.BG2, stroke=T.RED, rx=8)
    c.text(56, 486, "Write the pin with BSRR/BRR — never read-modify-write ODR", size=15, fill=T.RED, weight="700")
    c.text(56, 518, "BSRR high-half resets, low-half sets; one write is atomic. ODR |= loses bits under IRQ.", size=13, fill=T.TEXT)
    c.text(56, 548, "PC13 ON: BSRR=(1<<13)<<16; OFF: BSRR=(1<<13).", size=13, fill=T.MUTED, mono=True)
    c.rect(40, 620, 880, 90, fill=T.PANEL, stroke=T.CYAN, rx=8)
    c.text(56, 654, "Contrast: Nucleo user LED often PA5 active-high — polarity follows the schematic.", size=14, fill=T.TEXT)
    c.text(56, 684, "Sources: RM0008 GPIO; board polarity is evidence-track; this figure is knowledge-track.", size=13, fill=T.MUTED)
    credit(c, "Hand-drawn. Register semantics from RM0008 GPIO; PC13 polarity is Blue Pill board fact.")
    return c


def ch03_current_path() -> Svg:
    c = Svg(960, 880, "LED current-path estimate", "3.3V -> R -> LED Vf -> PC13 low; EST not lab")
    c.header(tag="03", tag_color=T.AMBER)
    c.text(40, 86, "Knowledge-track estimate: I ~= (3.3 - Vf) / R. Mark EST, not a lab reading.", size=14, fill=T.AMBER, weight="700")
    boxes = [
        ("3V3", "rail", T.GREEN),
        ("R", "2.2k / 330", T.CYAN),
        ("LED", "Vf~2.0 V", T.AMBER),
        ("PC13", "drive low", T.RED),
        ("GND", "return", T.MUTED),
    ]
    for i, (lab, sub, col) in enumerate(boxes):
        x = 40 + i * 185
        c.rect(x, 130, 165, 90, fill=T.PANEL, stroke=col, rx=8)
        c.text(x + 82, 166, lab, size=18, anchor="middle", fill=col, weight="700")
        c.text(x + 82, 196, sub, size=13, anchor="middle", fill=T.MUTED)
        if i < 4:
            c.arrow(x + 169, 175, x + 181, 175, color=T.STROKE, sw=2)
    c.title_block(40, 250, "Two common values", color=T.CYAN)
    c.rect(40, 280, 430, 160, fill=T.PANEL, stroke=T.CYAN, rx=8)
    c.text(56, 314, "Blue Pill typical 2.2 kOhm", size=15, fill=T.CYAN, weight="700")
    c.text(56, 346, "I ~= (3.3-2.0)/2200 ~= 0.59 mA", size=14, fill=T.TEXT, mono=True)
    c.text(56, 376, "Dim but thrifty; photos often look 'off'", size=13, fill=T.MUTED)
    c.text(56, 406, "Still a legal digital load", size=13, fill=T.MUTED)
    c.rect(490, 280, 430, 160, fill=T.PANEL, stroke=T.AMBER, rx=8)
    c.text(506, 314, "Breadboard example 330 Ohm", size=15, fill=T.AMBER, weight="700")
    c.text(506, 346, "I ~= (3.3-2.0)/330 ~= 3.9 mA", size=14, fill=T.TEXT, mono=True)
    c.text(506, 376, "Brighter; still far under 20 mA abs max", size=13, fill=T.MUTED)
    c.text(506, 406, "PA5 high-side path reverses the stack", size=13, fill=T.MUTED)
    c.rect(40, 470, 880, 120, fill=T.BG2, stroke=T.RED, rx=8)
    c.text(56, 506, "Trap: treat PC13 as high-side push to a 3V3 LED — polarity wrong => dark or odd sink", size=14, fill=T.RED, weight="700")
    c.text(56, 538, "Trap: continuity beep on the LED is not operating-point current", size=14, fill=T.AMBER)
    c.text(56, 568, "Evidence: scope PC13 level + schematic cathode; series-ammeter for current", size=13, fill=T.MUTED)
    c.rect(40, 620, 880, 90, fill=T.PANEL, stroke=T.STROKE, rx=8)
    c.text(56, 654, "Pairs with led-blink / gpio-blink: animation = timing; this figure = current ledger", size=14, fill=T.TEXT)
    c.text(56, 684, "Keep the EST label so nobody cites it as measured.", size=13, fill=T.MUTED)
    credit(c, "Hand-drawn estimate. Resistor/polarity follow common Blue Pill schematics; not a lab calibration.")
    return c


def ch03_exti_vs_poll() -> Svg:
    c = Svg(960, 880, "Poll vs EXTI", "Buttons: blocking poll wastes the loop; EXTI + debounce is the event")
    c.header(tag="03", tag_color=T.VIOLET)
    c.rect(40, 120, 420, 280, fill=T.PANEL, stroke=T.AMBER, rx=8)
    c.text(56, 156, "Polling", size=18, fill=T.AMBER, weight="700")
    for i, line in enumerate(["while(1){ if(pin) ... }", "main loop glued to the key", "multi-key debounce hard to share", "low-power almost impossible", "OK for a one-shot power-on check"]):
        c.text(56, 200 + i * 32, "- " + line, size=14, fill=T.TEXT)
    c.rect(500, 120, 420, 280, fill=T.PANEL, stroke=T.GREEN, rx=8)
    c.text(516, 156, "EXTI", size=18, fill=T.GREEN, weight="700")
    for i, line in enumerate(["edge into ISR", "main loop free / sleep OK", "one EXTI line shared by pins", "debounce: timer or software", "design with NVIC priority"]):
        c.text(516, 200 + i * 32, "- " + line, size=14, fill=T.TEXT)
    c.rect(40, 430, 880, 140, fill=T.BG2, stroke=T.CYAN, rx=8)
    c.text(56, 466, "GPIO chapter lights the pin first; input events continue in ch04 NVIC/EXTI", size=15, fill=T.CYAN, weight="700")
    c.text(56, 500, "Place after hardware wiring so readers do not freeze a poll architecture in the LED chapter", size=13, fill=T.TEXT)
    c.text(56, 530, "Shared EXTI line: PA0/PB0/PC0 cannot all be EXTI0 sources at once", size=13, fill=T.MUTED)
    c.rect(40, 600, 880, 100, fill=T.PANEL, stroke=T.STROKE, rx=8)
    c.text(56, 636, "Accept: edge flag on press; no retrigger on release; debounce fires business once", size=14, fill=T.TEXT, weight="700")
    c.text(56, 666, "Knowledge-track compare, not a scope capture.", size=13, fill=T.MUTED)
    credit(c, "Hand-drawn compare. EXTI sharing from RM0008; debounce policy continues in ch04.")
    return c


def ch06_baud_formula() -> Svg:
    c = Svg(960, 880, "USART baud formula", "BRR = fCK / baud; USART1 vs USART2 clock")
    c.header(tag="06", tag_color=T.CYAN)
    c.text(40, 86, "USARTDIV = fCK / baud; BRR packs mantissa.fraction", size=15, fill=T.TEXT, weight="700")
    c.rect(40, 120, 880, 120, fill=T.PANEL, stroke=T.CYAN, rx=8)
    c.text(56, 156, "USART1 on APB2: fCK = PCLK2 = 72e6", size=15, fill=T.CYAN, weight="700")
    c.text(56, 188, "115200 => DIV ~= 625 => BRR = 0x0271", size=14, fill=T.TEXT, mono=True)
    c.text(56, 216, "9600 => DIV ~= 7500 => BRR = 0x1D4C", size=14, fill=T.TEXT, mono=True)
    c.rect(40, 260, 880, 120, fill=T.PANEL, stroke=T.PINK, rx=8)
    c.text(56, 296, "USART2 on APB1: fCK = PCLK1 = 36e6", size=15, fill=T.PINK, weight="700")
    c.text(56, 328, "115200 => DIV ~= 312.5 => BRR = 0x0139", size=14, fill=T.TEXT, mono=True)
    c.text(56, 356, "Same baud string, half the input clock -> half BRR", size=13, fill=T.MUTED)
    c.rect(40, 410, 880, 140, fill=T.BG2, stroke=T.RED, rx=8)
    c.text(56, 446, "Trap: copy USART1 BRR onto USART2 -> ~2x baud error", size=15, fill=T.RED, weight="700")
    c.text(56, 478, "Trap: SystemCoreClock=72e6 but still on HSI -> every baud wrong", size=14, fill=T.AMBER)
    c.text(56, 510, "Evidence: scope bit width = 1/baud; idle high, start bit low", size=13, fill=T.MUTED)
    c.rect(40, 580, 880, 110, fill=T.PANEL, stroke=T.GREEN, rx=8)
    c.text(56, 616, "Teaching: frame animation shows start/data/stop; this figure does the math", size=14, fill=T.TEXT, weight="700")
    c.text(56, 646, "Over-sampling 16x is the default path on F1; keep OVER8 off unless documented", size=13, fill=T.MUTED)
    credit(c, "Hand-drawn. BRR examples for 72/36 MHz trees; RM0008 USART baud rate.")
    return c


def ch06_frame_annotated() -> Svg:
    c = Svg(960, 880, "UART frame annotated", "Idle 1, start 0, 8 data LSB-first, stop 1")
    c.header(tag="06", tag_color=T.GREEN)
    c.text(40, 86, "One byte 0xA5 = 10100101b, LSB first on the wire", size=15, fill=T.TEXT, weight="700")
    # bit boxes
    bits = [("Idle", "1", T.MUTED), ("Start", "0", T.RED), ("b0", "1", T.CYAN), ("b1", "0", T.CYAN),
            ("b2", "1", T.CYAN), ("b3", "0", T.CYAN), ("b4", "0", T.CYAN), ("b5", "1", T.CYAN),
            ("b6", "0", T.CYAN), ("b7", "1", T.CYAN), ("Stop", "1", T.GREEN)]
    for i, (lab, val, col) in enumerate(bits):
        x = 40 + i * 82
        c.rect(x, 130, 74, 100, fill=T.PANEL, stroke=col, rx=4)
        c.text(x + 37, 168, lab, size=12, anchor="middle", fill=col, weight="700")
        c.text(x + 37, 200, val, size=20, anchor="middle", fill=T.TEXT, weight="700", mono=True)
    c.rect(40, 260, 880, 120, fill=T.BG2, stroke=T.AMBER, rx=8)
    c.text(56, 296, "Bit time at 115200 ~= 8.68 us; sample near mid-bit (~1.5 bit after start edge)", size=14, fill=T.AMBER, weight="700")
    c.text(56, 328, "LSB first: wire order for 0xA5 is 1 0 1 0 0 1 0 1 after start", size=13, fill=T.TEXT)
    c.text(56, 358, "Idle must stay high; a stuck-low line is break / wiring, not a valid frame", size=13, fill=T.MUTED)
    c.rect(40, 410, 880, 140, fill=T.PANEL, stroke=T.CYAN, rx=8)
    c.text(56, 446, "Scope accept: start falling edge, eight bit slots, stop high, then idle", size=14, fill=T.TEXT, weight="700")
    c.text(56, 478, "Reject: missing stop, wrong baud (bit width off), or TX/RX swapped", size=13, fill=T.MUTED)
    c.text(56, 510, "Pairs with uart-frame / uart-idle animations; this is the printable first-frame ledger", size=13, fill=T.MUTED)
    c.rect(40, 580, 880, 110, fill=T.PANEL, stroke=T.STROKE, rx=8)
    c.text(56, 616, "Common-ground + 3.3 V logic levels assumed; RS-232 needs a level shifter", size=14, fill=T.TEXT)
    c.text(56, 646, "Knowledge-track wire grammar, not a captured scope PNG.", size=13, fill=T.MUTED)
    credit(c, "Hand-drawn. UART 8N1 grammar; example byte 0xA5 for teaching.")
    return c


def ch06_tx_rx_crossover() -> Svg:
    c = Svg(960, 880, "TX/RX crossover", "MCU TX -> adapter RX; share GND; 3V3 only")
    c.header(tag="06", tag_color=T.PINK)
    c.rect(40, 120, 280, 200, fill=T.PANEL, stroke=T.CYAN, rx=8)
    c.text(180, 160, "MCU", size=18, anchor="middle", fill=T.CYAN, weight="700")
    c.text(180, 200, "TX (PA9 / USART1)", size=14, anchor="middle", fill=T.TEXT)
    c.text(180, 230, "RX (PA10)", size=14, anchor="middle", fill=T.TEXT)
    c.text(180, 260, "GND", size=14, anchor="middle", fill=T.MUTED)
    c.rect(640, 120, 280, 200, fill=T.PANEL, stroke=T.GREEN, rx=8)
    c.text(780, 160, "USB-UART", size=18, anchor="middle", fill=T.GREEN, weight="700")
    c.text(780, 200, "RX", size=14, anchor="middle", fill=T.TEXT)
    c.text(780, 230, "TX", size=14, anchor="middle", fill=T.TEXT)
    c.text(780, 260, "GND", size=14, anchor="middle", fill=T.MUTED)
    c.arrow(330, 200, 630, 200, color=T.AMBER, sw=2)
    c.text(480, 186, "TX -> RX", size=13, anchor="middle", fill=T.AMBER, weight="700")
    c.arrow(630, 230, 330, 230, color=T.VIOLET, sw=2)
    c.text(480, 254, "RX <- TX", size=13, anchor="middle", fill=T.VIOLET, weight="700")
    c.line(320, 260, 640, 260, stroke=T.MUTED, sw=2)
    c.text(480, 286, "common GND", size=13, anchor="middle", fill=T.MUTED)
    c.rect(40, 360, 880, 160, fill=T.BG2, stroke=T.RED, rx=8)
    c.text(56, 396, "Trap: TX-TX / RX-RX => silence forever", size=15, fill=T.RED, weight="700")
    c.text(56, 428, "Trap: 5 V USB-TTL into 3.3 V MCU pin => risk permanent damage", size=14, fill=T.AMBER)
    c.text(56, 460, "Trap: floating GND between laptop and board => garbage / resets", size=14, fill=T.AMBER)
    c.text(56, 492, "Accept: loopback TX-RX on adapter alone first, then cross to MCU", size=13, fill=T.MUTED)
    c.rect(40, 550, 880, 130, fill=T.PANEL, stroke=T.STROKE, rx=8)
    c.text(56, 586, "Blue Pill USART1 default AF: PA9 TX / PA10 RX (remap changes pins)", size=14, fill=T.TEXT, weight="700")
    c.text(56, 618, "Evidence: continuity + idle-high scope; knowledge track for the cross rule", size=13, fill=T.MUTED)
    credit(c, "Hand-drawn wiring rule. Pin defaults from DS5319 / RM0008 AF map.")
    return c


def ch09_sar_ladder() -> Svg:
    c = Svg(960, 880, "SAR bit ladder", "12-bit successive approximation with real thresholds")
    c.header(tag="09", tag_color=T.CYAN)
    c.text(40, 86, "Vin example 1.65 V on 3.3 V Vref+ => mid-scale ~2048 counts", size=14, fill=T.TEXT, weight="700")
    steps = [
        ("MSB", "2048", "1.65 V", "keep 1", T.GREEN),
        ("bit10", "1024", "0.825", "add?", T.CYAN),
        ("bit9", "512", "0.4125", "add?", T.CYAN),
        ("...", "...", "...", "10 more", T.MUTED),
        ("LSB", "1", "0.8 mV", "final", T.AMBER),
    ]
    for i, (b, code, v, act, col) in enumerate(steps):
        y = 120 + i * 70
        c.rect(40, y, 880, 60, fill=T.PANEL, stroke=col, rx=8)
        c.text(56, y + 36, b, size=15, fill=col, weight="700")
        c.text(160, y + 36, "weight " + code, size=14, fill=T.TEXT, mono=True)
        c.text(360, y + 36, "Vref step " + v, size=14, fill=T.MUTED)
        c.text(880, y + 36, act, size=14, fill=col, anchor="end", weight="700")
    c.rect(40, 490, 880, 120, fill=T.BG2, stroke=T.AMBER, rx=8)
    c.text(56, 526, "One compare per bit; 12 bits => 12 decisions after sample", size=14, fill=T.AMBER, weight="700")
    c.text(56, 558, "EOC marks end; reading DR clears EOC on F1 — do not double-read blindly", size=13, fill=T.TEXT)
    c.text(56, 588, "Pairs with adc-sar animation; this page freezes the weights for PDF", size=13, fill=T.MUTED)
    c.rect(40, 640, 880, 90, fill=T.PANEL, stroke=T.STROKE, rx=8)
    c.text(56, 674, "Noise / INL / DNL are real; treat single-shot counts as EST until averaged", size=14, fill=T.TEXT)
    credit(c, "Hand-drawn. SAR weights for 12-bit / 3.3 V; RM0008 ADC successive approximation.")
    return c


def ch09_sample_time() -> Svg:
    c = Svg(960, 880, "ADC sample-time budget", "SMPR cycles vs source impedance")
    c.header(tag="09", tag_color=T.AMBER)
    c.text(40, 86, "t_sample = SMP cycles / ADCCLK; ADCCLK = PCLK2 / (2,4,6,8) <= 14 MHz", size=14, fill=T.TEXT, weight="700")
    rows = [
        ("SMP=1.5", "fast pin, low R", "risk if source is soft", T.GREEN),
        ("SMP=7.5", "general GPIO", "good first guess", T.CYAN),
        ("SMP=28.5", "higher R / filter", "safer settling", T.AMBER),
        ("SMP=239.5", "very soft / thermistor", "slow but honest", T.VIOLET),
    ]
    for i, (smp, use, note, col) in enumerate(rows):
        y = 120 + i * 78
        c.rect(40, y, 880, 68, fill=T.PANEL, stroke=col, rx=8)
        c.text(56, y + 28, smp, size=16, fill=col, weight="700", mono=True)
        c.text(220, y + 28, use, size=14, fill=T.TEXT)
        c.text(880, y + 28, note, size=13, fill=T.MUTED, anchor="end")
    c.rect(40, 450, 880, 130, fill=T.BG2, stroke=T.RED, rx=8)
    c.text(56, 486, "Trap: ADCCLK > 14 MHz (illegal) or SMP too short on high-Z => wrong codes", size=14, fill=T.RED, weight="700")
    c.text(56, 518, "Trap: share one channel for DC and AC without re-settling", size=14, fill=T.AMBER)
    c.text(56, 550, "Evidence: change SMP and see DR move; if it moves a lot, settling was the bug", size=13, fill=T.MUTED)
    c.rect(40, 610, 880, 100, fill=T.PANEL, stroke=T.STROKE, rx=8)
    c.text(56, 646, "Example: ADCCLK=12 MHz, SMP=7.5 => t_sample=0.625 us before conversion", size=14, fill=T.TEXT, weight="700")
    c.text(56, 676, "Knowledge-track budget, not a scope photo of the sample capacitor.", size=13, fill=T.MUTED)
    credit(c, "Hand-drawn. SMPR options from RM0008 ADC; ADCCLK limit from DS5319.")
    return c


def ch09_vref_rails() -> Svg:
    c = Svg(960, 880, "Vref+ rails", "What the code actually means in volts")
    c.header(tag="09", tag_color=T.GREEN)
    c.text(40, 86, "Code / 4095 * Vref+  (12-bit right-aligned DR)", size=15, fill=T.TEXT, weight="700")
    c.rect(40, 120, 880, 160, fill=T.PANEL, stroke=T.CYAN, rx=8)
    c.text(56, 156, "If Vref+ = VDDA = 3.30 V", size=15, fill=T.CYAN, weight="700")
    c.text(56, 188, "1 LSB ~= 0.806 mV; mid-scale 2048 ~= 1.65 V", size=14, fill=T.TEXT, mono=True)
    c.text(56, 220, "USB 5V boards often have VDDA noise — treat absolute volts as EST", size=13, fill=T.MUTED)
    c.rect(40, 310, 880, 160, fill=T.PANEL, stroke=T.AMBER, rx=8)
    c.text(56, 346, "Internal Vrefint (~1.2 V) for relative / temperature paths", size=15, fill=T.AMBER, weight="700")
    c.text(56, 378, "Factory cal addresses exist; do not invent the constant", size=14, fill=T.TEXT)
    c.text(56, 410, "Use Vrefint to estimate VDDA when the 3V3 rail is soft", size=13, fill=T.MUTED)
    c.rect(40, 500, 880, 120, fill=T.BG2, stroke=T.RED, rx=8)
    c.text(56, 536, "Trap: convert codes with 3.3 hardcoded while VDDA is actually 3.0", size=14, fill=T.RED, weight="700")
    c.text(56, 568, "Trap: leave ADC uncalibrated after power-up on parts that require it", size=14, fill=T.AMBER)
    c.rect(40, 650, 880, 80, fill=T.PANEL, stroke=T.STROKE, rx=8)
    c.text(56, 684, "Printable ledger for ch09; animation shows SAR decisions, this shows volts.", size=14, fill=T.TEXT)
    credit(c, "Hand-drawn. 12-bit / Vref math; Vrefint is device-data-sheet territory.")
    return c


def ch10_dma_phases() -> Svg:
    c = Svg(960, 880, "DMA request phases", "Peripheral request -> memory write -> CNDTR countdown")
    c.header(tag="10", tag_color=T.VIOLET)
    steps = [
        ("1 Request", "USART/ADC/TIM asserts DMA req", T.AMBER),
        ("2 Grant", "DMA arbiter picks channel", T.CYAN),
        ("3 Transfer", "byte/half/word per CCR", T.GREEN),
        ("4 Count", "CNDTR-- ; TC/HT flags", T.VIOLET),
    ]
    for i, (t, d, col) in enumerate(steps):
        x = 40 + i * 230
        c.rect(x, 120, 210, 140, fill=T.PANEL, stroke=col, rx=8)
        c.text(x + 105, 160, t, size=16, anchor="middle", fill=col, weight="700")
        c.text(x + 20, 200, d, size=13, fill=T.TEXT)
        if i < 3:
            c.arrow(x + 214, 190, x + 226, 190, color=T.STROKE, sw=2)
    c.rect(40, 300, 880, 160, fill=T.BG2, stroke=T.CYAN, rx=8)
    c.text(56, 336, "Circular mode: CNDTR reloads; HT/TC become buffer half/full events", size=15, fill=T.CYAN, weight="700")
    c.text(56, 368, "Normal mode: CNDTR hits 0 and stops until you re-arm", size=14, fill=T.TEXT)
    c.text(56, 400, "Priority vs CPU: DMA can steal cycles; keep bursts short on busy buses", size=13, fill=T.MUTED)
    c.text(56, 432, "Evidence: watch CNDTR live; if stuck, EN/req map/address is wrong", size=13, fill=T.MUTED)
    c.rect(40, 490, 880, 140, fill=T.PANEL, stroke=T.RED, rx=8)
    c.text(56, 526, "Trap: peripheral address wrong size (byte vs word) => scrambled buffer", size=14, fill=T.RED, weight="700")
    c.text(56, 558, "Trap: forget circular + HT ISR => overflow while printf in main", size=14, fill=T.AMBER)
    c.text(56, 590, "Pairs with dma-circular / dma-cndtr; this is the phase ledger for PDF", size=13, fill=T.MUTED)
    c.rect(40, 660, 880, 80, fill=T.PANEL, stroke=T.STROKE, rx=8)
    c.text(56, 694, "F1 DMA1 channels are fixed-function; remap in your head before coding.", size=14, fill=T.TEXT)
    credit(c, "Hand-drawn. DMA phases from RM0008 DMA; circular vs normal semantics.")
    return c


def ch10_cndtr_ledger() -> Svg:
    c = Svg(960, 880, "CNDTR live ledger", "What remaining count means in circular ADC buffer")
    c.header(tag="10", tag_color=T.AMBER)
    c.text(40, 86, "Example: NDTR init = 256 halfwords; circular ADC1 -> mem", size=14, fill=T.TEXT, weight="700")
    rows = [
        ("256", "just armed", "buffer empty from SW view", T.MUTED),
        ("192", "64 written", "still first half", T.CYAN),
        ("128", "HT flag", "first half ready to parse", T.GREEN),
        ("64", "second half filling", "do not touch second half yet", T.AMBER),
        ("0->256", "TC + reload", "second half ready; count wraps", T.VIOLET),
    ]
    for i, (n, state, note, col) in enumerate(rows):
        y = 120 + i * 70
        c.rect(40, y, 880, 60, fill=T.PANEL, stroke=col, rx=8)
        c.text(56, y + 36, "CNDTR=" + n, size=15, fill=col, weight="700", mono=True)
        c.text(260, y + 36, state, size=14, fill=T.TEXT)
        c.text(880, y + 36, note, size=13, fill=T.MUTED, anchor="end")
    c.rect(40, 490, 880, 120, fill=T.BG2, stroke=T.RED, rx=8)
    c.text(56, 526, "Trap: parse the wrong half after HT/TC => silent data corruption", size=14, fill=T.RED, weight="700")
    c.text(56, 558, "Trap: print inside HT ISR longer than half-buffer time => overrun", size=14, fill=T.AMBER)
    c.text(56, 588, "Accept: ISR only sets a flag; main drains the finished half", size=13, fill=T.MUTED)
    c.rect(40, 640, 880, 90, fill=T.PANEL, stroke=T.STROKE, rx=8)
    c.text(56, 674, "Use with remade dma-cndtr GIF; numbers must match the animation labels.", size=14, fill=T.TEXT)
    credit(c, "Hand-drawn. Circular CNDTR story for ADC buffers; RM0008 DMA.")
    return c


def ch10_mem2mem_vs_peri() -> Svg:
    c = Svg(960, 880, "Mem2mem vs peripheral DMA", "When the request comes from soft vs hard")
    c.header(tag="10", tag_color=T.GREEN)
    c.rect(40, 120, 420, 260, fill=T.PANEL, stroke=T.CYAN, rx=8)
    c.text(56, 156, "Peripheral DMA", size=18, fill=T.CYAN, weight="700")
    for i, line in enumerate(["Hardware request line", "USART RX/TX, ADC, TIM", "pace set by peripheral", "usual streaming path", "circular + HT/TC common"]):
        c.text(56, 200 + i * 32, "- " + line, size=14, fill=T.TEXT)
    c.rect(500, 120, 420, 260, fill=T.PANEL, stroke=T.VIOLET, rx=8)
    c.text(516, 156, "Memory-to-memory", size=18, fill=T.VIOLET, weight="700")
    for i, line in enumerate(["Software start (no peri req)", "fast block copy / fill", "can hammer the bus", "watch priority vs CPU", "great for init buffers"]):
        c.text(516, 200 + i * 32, "- " + line, size=14, fill=T.TEXT)
    c.rect(40, 420, 880, 140, fill=T.BG2, stroke=T.AMBER, rx=8)
    c.text(56, 456, "Pick peripheral DMA for continuous ADC/USART; mem2mem for one-shot copies", size=14, fill=T.AMBER, weight="700")
    c.text(56, 488, "F1 channel mapping is fixed — mem2mem still uses a channel resource", size=13, fill=T.TEXT)
    c.text(56, 520, "Evidence: CNDTR moves without peripheral IRQ for mem2mem; with peri flags for streaming", size=13, fill=T.MUTED)
    c.rect(40, 590, 880, 110, fill=T.PANEL, stroke=T.STROKE, rx=8)
    c.text(56, 626, "Breaks the DMA chapter text wall with a crisp decision table.", size=14, fill=T.TEXT, weight="700")
    c.text(56, 656, "Knowledge-track; not a logic-analyzer capture.", size=13, fill=T.MUTED)
    credit(c, "Hand-drawn. Peripheral vs mem2mem modes from RM0008 DMA.")
    return c


FIGURES = [
    ("sample-02-pll-lock.svg", ch02_pll_lock),
    ("sample-02-flash-latency.svg", ch02_flash_latency),
    ("sample-02-bus-matrix.svg", ch02_bus_matrix),
    ("sample-03-moder-map.svg", ch03_moder_map),
    ("sample-03-current-path.svg", ch03_current_path),
    ("sample-03-exti-vs-poll.svg", ch03_exti_vs_poll),
    ("sample-06-baud-formula.svg", ch06_baud_formula),
    ("sample-06-frame-annotated.svg", ch06_frame_annotated),
    ("sample-06-tx-rx-crossover.svg", ch06_tx_rx_crossover),
    ("sample-09-sar-ladder.svg", ch09_sar_ladder),
    ("sample-09-sample-time.svg", ch09_sample_time),
    ("sample-09-vref-rails.svg", ch09_vref_rails),
    ("sample-10-dma-phases.svg", ch10_dma_phases),
    ("sample-10-cndtr-ledger.svg", ch10_cndtr_ledger),
    ("sample-10-mem2mem-vs-peri.svg", ch10_mem2mem_vs_peri),
]


def main() -> None:
    root = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "assets", "diagrams")
    os.makedirs(root, exist_ok=True)
    from sample_figs_quality._common import audit_static
    for name, fn in FIGURES:
        path = os.path.join(root, name)
        fn().save(path)
        audit_static(name, path)
    print(f"wrote {len(FIGURES)} figures -> {root}")


if __name__ == "__main__":
    main()

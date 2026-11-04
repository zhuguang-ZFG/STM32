#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""High-density static Handraw figures for ch04/05/07/08."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from svgkit import Svg, T
from sample_figs_quality2._common import credit, audit_static

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                   "assets", "diagrams")


def ch04_priority_group() -> Svg:
    c = Svg(960, 880, "NVIC priority grouping", "Preempt bits vs subpriority bits")
    c.header(tag="04", tag_color=T.CYAN)
    c.text(40, 86, "STM32F103: 4 priority bits. AIRCR PRIGROUP picks the split.", size=15, fill=T.TEXT, weight="700")
    rows = [
        ("GROUP 0", "7:1 preempt / 0 sub", "finest preempt", T.VIOLET),
        ("GROUP 3", "7:4 preempt / 3:0 sub", "Cube default often", T.CYAN),
        ("GROUP 4", "7:5 preempt / 4:0 sub", "3 preempt levels", T.GREEN),
        ("GROUP 7", "0 preempt / 7:0 sub", "no nesting by preempt", T.AMBER),
    ]
    for i, (g, split, note, col) in enumerate(rows):
        y = 120 + i * 70
        c.rect(40, y, 880, 60, fill=T.PANEL, stroke=col, rx=8)
        c.text(56, y + 36, g, size=16, fill=col, weight="700", mono=True)
        c.text(220, y + 36, split, size=14, fill=T.TEXT, mono=True)
        c.text(880, y + 36, note, size=13, fill=T.MUTED, anchor="end")
    c.rect(40, 420, 880, 130, fill=T.BG2, stroke=T.RED, rx=8)
    c.text(56, 454, "Same preempt number => no interrupt of each other; only tail-chain / pending order.", size=14, fill=T.RED, weight="700")
    c.text(56, 484, "Example: TIM2 preempt=2, EXTI0 preempt=1 => EXTI0 runs now, TIM2 stacked.", size=13, fill=T.TEXT)
    c.text(56, 514, "Equal preempt=2/2: EXTI0 waits until TIM2 ISR returns — failure stays on triage SVG.", size=13, fill=T.MUTED)
    c.rect(40, 570, 880, 100, fill=T.PANEL, stroke=T.GREEN, rx=8)
    c.text(56, 604, "Probe: SCB->AIRCR[10:8], NVIC_GetPriorityGrouping(), then IPRx nibbles.", size=14, fill=T.TEXT, weight="700")
    c.text(56, 634, "Numbers from PM0056 / RM0008 NVIC; knowledge track, not a logic-analyzer capture.", size=13, fill=T.MUTED)
    credit(c, "Hand-drawn. Priority split from PM0056 + RM0008 NVIC; pairs with nvic-preempt GIF.")
    return c


def ch04_tail_chain() -> Svg:
    c = Svg(960, 880, "Tail-chaining & late arrival", "Cycle counts that matter on Cortex-M3")
    c.header(tag="04", tag_color=T.AMBER)
    c.text(40, 86, "Cortex-M3 exception entry/exit shortcuts (PM0056)", size=15, fill=T.TEXT, weight="700")
    boxes = [
        ("Entry", "12 cycles", "push R0-R3,R12,LR,PC,xPSR", T.CYAN),
        ("Exit", "12 cycles", "pop the same eight", T.GREEN),
        ("Tail-chain", "~6 cycles", "skip pop+push when next IRQ pending", T.AMBER),
        ("Late arrival", "retarget", "higher preempt replaces before ISR body", T.VIOLET),
    ]
    for i, (t, n, note, col) in enumerate(boxes):
        x = 40 + (i % 2) * 460
        y = 120 + (i // 2) * 140
        c.rect(x, y, 440, 120, fill=T.PANEL, stroke=col, rx=8)
        c.text(x + 24, y + 36, t, size=16, fill=col, weight="700")
        c.text(x + 24, y + 66, n, size=20, fill=T.TEXT, weight="700", mono=True)
        c.text(x + 24, y + 96, note, size=13, fill=T.MUTED)
    c.rect(40, 420, 880, 140, fill=T.BG2, stroke=T.CYAN, rx=8)
    c.text(56, 454, "Teaching use: do not invent '6 cycle ISR' budgets without naming entry+body+exit.", size=14, fill=T.CYAN, weight="700")
    c.text(56, 484, "At 72 MHz, 12 cycles ~= 167 ns. A 1 us GPIO toggle is mostly software, not stacking.", size=13, fill=T.TEXT)
    c.text(56, 514, "Tail-chain helps back-to-back EXTI/TIM; it does not erase priority mistakes.", size=13, fill=T.MUTED)
    c.rect(40, 580, 880, 90, fill=T.PANEL, stroke=T.STROKE, rx=8)
    c.text(56, 614, "Place beside nesting labs — breaks the long ISR prose wall with real cycle numbers.", size=14, fill=T.TEXT, weight="700")
    c.text(56, 644, "Knowledge-track timing card; scope photos stay in the evidence track when available.", size=13, fill=T.MUTED)
    credit(c, "Hand-drawn. Cycle figures from PM0056 exception model; complements sample-04-exception-stack.")
    return c


def ch04_exti_map() -> Svg:
    c = Svg(960, 880, "EXTI line mux", "One EXTI line, many GPIO ports via AFIO")
    c.header(tag="04", tag_color=T.GREEN)
    c.text(40, 86, "F103: EXTI0..15 each pick one of PA..PG via AFIO_EXTICR", size=15, fill=T.TEXT, weight="700")
    c.rect(40, 120, 280, 220, fill=T.PANEL, stroke=T.CYAN, rx=8)
    c.text(180, 150, "GPIO ports", size=14, fill=T.CYAN, weight="700", anchor="middle")
    for i, p in enumerate(["PA0", "PB0", "PC0", "PD0"]):
        c.rect(70, 170 + i * 40, 220, 32, fill=T.BG2, stroke=T.STROKE, rx=4)
        c.text(180, 192 + i * 40, p, size=14, fill=T.TEXT, anchor="middle", mono=True)
    c.arrow(330, 230, 400, 230, color=T.STROKE, sw=2)
    c.rect(410, 160, 200, 140, fill=T.PANEL, stroke=T.AMBER, rx=8)
    c.text(510, 200, "AFIO_EXTICR1", size=14, fill=T.AMBER, weight="700", anchor="middle", mono=True)
    c.text(510, 232, "EXTI0[3:0]", size=13, fill=T.TEXT, anchor="middle", mono=True)
    c.text(510, 264, "0000=PA .. 0010=PC", size=12, fill=T.MUTED, anchor="middle")
    c.arrow(620, 230, 690, 230, color=T.STROKE, sw=2)
    c.rect(700, 160, 220, 140, fill=T.PANEL, stroke=T.GREEN, rx=8)
    c.text(810, 200, "EXTI0", size=16, fill=T.GREEN, weight="700", anchor="middle")
    c.text(810, 232, "IMR / RTSR / FTSR", size=13, fill=T.TEXT, anchor="middle", mono=True)
    c.text(810, 264, "shared IRQ vector", size=12, fill=T.MUTED, anchor="middle")
    c.rect(40, 380, 880, 150, fill=T.BG2, stroke=T.RED, rx=8)
    c.text(56, 414, "Trap: two pins on the same EXTI line cannot both be sources — last EXTICR write wins.", size=14, fill=T.RED, weight="700")
    c.text(56, 444, "EXTI5-9 and EXTI10-15 share IRQ handlers; check pending bits inside the ISR.", size=13, fill=T.TEXT)
    c.text(56, 474, "Blue Pill key on PA0 => EXTI0, AFIO_EXTICR1 EXTI0=0000, NVIC IRQ EXTI0_IRQn.", size=13, fill=T.MUTED)
    c.rect(40, 560, 880, 100, fill=T.PANEL, stroke=T.VIOLET, rx=8)
    c.text(56, 594, "First frame: mux diagram + shared-vector note. Not a decor icon strip.", size=14, fill=T.TEXT, weight="700")
    c.text(56, 624, "Register names from RM0008 AFIO/EXTI; pairs with gpio-input-interrupt animation.", size=13, fill=T.MUTED)
    credit(c, "Hand-drawn. EXTI mux from RM0008; lab pin PA0 matches chapter KEY_PIN.")
    return c


def ch05_timebase() -> Svg:
    c = Svg(960, 880, "Timer time-base math", "72 MHz → PSC/ARR → 1 kHz PWM")
    c.header(tag="05", tag_color=T.CYAN)
    c.text(40, 86, "TIM3 on APB1: timer clock = 72 MHz when APB1 prescaler != 1", size=15, fill=T.TEXT, weight="700")
    steps = [
        ("f_tim", "72 MHz", "timer kernel clock", T.CYAN),
        ("PSC+1", "72", "PSC=71 => 1 MHz tick", T.GREEN),
        ("ARR+1", "1000", "ARR=999 => 1 kHz", T.AMBER),
        ("CCR", "500", "50% high time", T.VIOLET),
    ]
    for i, (t, n, note, col) in enumerate(steps):
        x = 40 + i * 230
        c.rect(x, 130, 210, 130, fill=T.PANEL, stroke=col, rx=8)
        c.text(x + 105, 168, t, size=14, anchor="middle", fill=col, weight="700", mono=True)
        c.text(x + 105, 204, n, size=22, anchor="middle", fill=T.TEXT, weight="700", mono=True)
        c.text(x + 105, 236, note, size=12, anchor="middle", fill=T.MUTED)
        if i < 3:
            c.arrow(x + 214, 195, x + 226, 195, color=T.STROKE, sw=2)
    c.rect(40, 300, 880, 120, fill=T.BG2, stroke=T.GREEN, rx=8)
    c.text(56, 334, "f_pwm = f_tim / ((PSC+1)*(ARR+1)) = 72e6 / (72*1000) = 1000 Hz", size=15, fill=T.GREEN, weight="700", mono=True)
    c.text(56, 368, "Duty = CCR/(ARR+1) = 500/1000 = 50%. High time = 500 us at 1 kHz.", size=14, fill=T.TEXT)
    c.text(56, 396, "Code macros in chapter: PWM_PSC 71, PWM_ARR 999 — must match this ledger.", size=13, fill=T.MUTED)
    c.rect(40, 450, 880, 120, fill=T.PANEL, stroke=T.RED, rx=8)
    c.text(56, 484, "Fail: use PCLK1=36 MHz as f_tim without the x2 rule => 500 Hz surprise.", size=14, fill=T.RED, weight="700")
    c.text(56, 514, "Fail: ARR=1000 thinking '1000 counts' => off-by-one (period uses ARR+1).", size=13, fill=T.AMBER)
    c.text(56, 544, "Probe: read PSC/ARR/CCR1 and TIM3->CNT while scoping PA6 (TIM3_CH1 AF).", size=13, fill=T.MUTED)
    c.rect(40, 600, 880, 80, fill=T.PANEL, stroke=T.STROKE, rx=8)
    c.text(56, 636, "Sits next to PWM mode section — concrete numbers before generic mode tables.", size=14, fill=T.TEXT, weight="700")
    c.text(56, 664, "Knowledge-track formula card; pairs with sample-05-pwm-1khz and pwm-1khz.gif.", size=13, fill=T.MUTED)
    credit(c, "Hand-drawn. Time-base from RM0008 TIM; matches chapter PSC/ARR macros.")
    return c


def ch05_shadow() -> Svg:
    c = Svg(960, 880, "Shadow registers", "ARR/CCR buffered until update event")
    c.header(tag="05", tag_color=T.AMBER)
    c.text(40, 86, "ARPE / OCxPE: write preload, latch on UE (update event)", size=15, fill=T.TEXT, weight="700")
    c.rect(40, 120, 420, 220, fill=T.PANEL, stroke=T.CYAN, rx=8)
    c.text(250, 156, "Software write", size=15, fill=T.CYAN, weight="700", anchor="middle")
    c.text(250, 196, "TIMx_ARR = 999", size=14, fill=T.TEXT, anchor="middle", mono=True)
    c.text(250, 228, "TIMx_CCR1 = 250", size=14, fill=T.TEXT, anchor="middle", mono=True)
    c.text(250, 268, "preload only if *PE=1", size=13, fill=T.MUTED, anchor="middle")
    c.rect(500, 120, 420, 220, fill=T.PANEL, stroke=T.GREEN, rx=8)
    c.text(710, 156, "Active after UE", size=15, fill=T.GREEN, weight="700", anchor="middle")
    c.text(710, 196, "shadow ARR", size=14, fill=T.TEXT, anchor="middle")
    c.text(710, 228, "shadow CCR1", size=14, fill=T.TEXT, anchor="middle")
    c.text(710, 268, "output compare uses these", size=13, fill=T.MUTED, anchor="middle")
    c.arrow(470, 230, 490, 230, color=T.STROKE, sw=2)
    c.rect(40, 370, 880, 140, fill=T.BG2, stroke=T.AMBER, rx=8)
    c.text(56, 404, "Why it matters: change duty mid-period without a glitch — wait for update.", size=14, fill=T.AMBER, weight="700")
    c.text(56, 434, "Breathing LED: rewrite CCR every N ms; with preload, edges stay clean.", size=13, fill=T.TEXT)
    c.text(56, 464, "Without preload, CCR can change mid-count => runt pulse / audible tick on motor drivers.", size=13, fill=T.MUTED)
    c.rect(40, 540, 880, 120, fill=T.PANEL, stroke=T.RED, rx=8)
    c.text(56, 574, "Debug: if ARR write 'does nothing' until overflow — ARPE is working as designed.", size=14, fill=T.RED, weight="700")
    c.text(56, 604, "Force update: set UG (EGR) once after init so first period uses the new preload.", size=13, fill=T.TEXT)
    c.text(56, 634, "Pairs with pwm-breath.gif — motion shows CCR steps; this card shows why they latch.", size=13, fill=T.MUTED)
    credit(c, "Hand-drawn. Shadow/preload from RM0008 TIM; bridges 1 kHz lab and breath demo.")
    return c


def ch05_deadtime() -> Svg:
    c = Svg(960, 880, "Complementary dead time", "TIM1/8 break + DT for half-bridges")
    c.header(tag="05", tag_color=T.VIOLET)
    c.text(40, 86, "Advanced timers: CH1 + CH1N with BDTR DTG dead time", size=15, fill=T.TEXT, weight="700")
    c.rect(40, 120, 880, 160, fill=T.PANEL, stroke=T.CYAN, rx=8)
    c.text(56, 154, "CHx (high-side)", size=14, fill=T.CYAN, weight="700")
    c.text(56, 184, "____/¯¯¯¯¯\\____", size=18, fill=T.TEXT, mono=True)
    c.text(56, 220, "CHxN (low-side)", size=14, fill=T.GREEN, weight="700")
    c.text(56, 250, "¯¯¯¯\\_____/¯¯¯¯", size=18, fill=T.TEXT, mono=True)
    c.rect(40, 310, 880, 140, fill=T.BG2, stroke=T.AMBER, rx=8)
    c.text(56, 344, "Dead time both edges: both FETs off for t_dt before the other turns on.", size=14, fill=T.AMBER, weight="700")
    c.text(56, 374, "DTG field encodes duration from timer clock (see RM0008 BDTR). Example lab: start ~0.5-1 us.", size=13, fill=T.TEXT)
    c.text(56, 404, "Without DT on a real half-bridge: shoot-through current spike — board magic smoke risk.", size=13, fill=T.RED)
    c.rect(40, 480, 880, 140, fill=T.PANEL, stroke=T.STROKE, rx=8)
    c.text(56, 514, "Also need: MOE (main output enable), break input polarity, idle states.", size=14, fill=T.TEXT, weight="700")
    c.text(56, 544, "F103 Blue Pill has TIM1; complementary pins need AF remap check on the package.", size=13, fill=T.MUTED)
    c.text(56, 574, "Knowledge-track safety card for §互补输出 — not a substitute for FET datasheet timing.", size=13, fill=T.MUTED)
    credit(c, "Hand-drawn. Dead-time/break from RM0008 advanced TIM; for half-bridge labs only.")
    return c


def ch07_start_ack() -> Svg:
    c = Svg(960, 880, "I2C START + address + ACK", "0x3C OLED as 0x78 on the wire")
    c.header(tag="07", tag_color=T.GREEN)
    c.text(40, 86, "PB6=SCL, PB7=SDA, 4.7 k to 3.3 V. HAL addr 0x78 = 7-bit 0x3C << 1.", size=14, fill=T.TEXT, weight="700")
    phases = [
        ("START", "SDA↓ while SCL=1", T.AMBER),
        ("ADDR", "0x78 = 0111 1000", T.CYAN),
        ("R/W=0", "write bit", T.VIOLET),
        ("ACK", "slave pulls SDA low", T.GREEN),
    ]
    for i, (t, n, col) in enumerate(phases):
        x = 40 + i * 230
        c.rect(x, 130, 210, 110, fill=T.PANEL, stroke=col, rx=8)
        c.text(x + 105, 168, t, size=16, anchor="middle", fill=col, weight="700")
        c.text(x + 105, 204, n, size=13, anchor="middle", fill=T.TEXT, mono=True)
        if i < 3:
            c.arrow(x + 214, 185, x + 226, 185, color=T.STROKE, sw=2)
    c.rect(40, 280, 880, 160, fill=T.BG2, stroke=T.CYAN, rx=8)
    c.text(56, 314, "9th SCL: master releases SDA; slave ACK drives low. NACK = SDA still high.", size=14, fill=T.CYAN, weight="700")
    c.text(56, 344, "CCR example often 0x801E @ 36 MHz PCLK1 for ~100 kHz Standard mode.", size=13, fill=T.TEXT, mono=True)
    c.text(56, 374, "Scope both edges: START is a condition, not a data bit — beginners mis-count 8.", size=13, fill=T.MUTED)
    c.text(56, 404, "Chapter GIF i2c-addr walks the same story; this card freezes the numbers for PDF.", size=13, fill=T.MUTED)
    c.rect(40, 470, 880, 140, fill=T.PANEL, stroke=T.RED, rx=8)
    c.text(56, 504, "Fail: pass 0x3C to HAL without <<1 => wrong first byte on the bus.", size=14, fill=T.RED, weight="700")
    c.text(56, 534, "Fail: no pull-ups => SDA never rises, 'busy' forever; not a software ACK bug.", size=13, fill=T.AMBER)
    c.text(56, 564, "Fail: 5 V slave without level shift on a 3.3 V Blue Pill pin — electrical, not code.", size=13, fill=T.MUTED)
    credit(c, "Hand-drawn. Address/ACK from UM10204 + RM0008 I2C; matches OLED_ADDR macro.")
    return c


def ch07_pullup() -> Svg:
    c = Svg(960, 880, "I2C pull-up vs capacitance", "4.7 k starting point, not a religion")
    c.header(tag="07", tag_color=T.AMBER)
    c.text(40, 86, "Rise time roughly ~0.847 * Rpull * Cbus (to ~63%); stay inside mode limits.", size=14, fill=T.TEXT, weight="700")
    rows = [
        ("Short jumper", "~20-50 pF", "4.7 k–10 k", "100 kHz easy", T.GREEN),
        ("Breadboard mess", "~100-200 pF", "2.2–4.7 k", "edges soften", T.CYAN),
        ("Long cable / many slaves", ">200 pF", "1–2.2 k", "watch sink current", T.AMBER),
        ("400 kHz Fast-mode", "budget tight", "often 1–2.2 k", "scope rise time", T.VIOLET),
    ]
    for i, (a, b, c3, d, col) in enumerate(rows):
        y = 120 + i * 70
        c.rect(40, y, 880, 60, fill=T.PANEL, stroke=col, rx=8)
        c.text(56, y + 36, a, size=14, fill=col, weight="700")
        c.text(300, y + 36, b, size=13, fill=T.TEXT, mono=True)
        c.text(520, y + 36, c3, size=13, fill=T.TEXT, mono=True)
        c.text(880, y + 36, d, size=13, fill=T.MUTED, anchor="end")
    c.rect(40, 420, 880, 140, fill=T.BG2, stroke=T.RED, rx=8)
    c.text(56, 454, "Too strong pull-up: slave VOL may not reach low; ACK looks like NACK on a bad scope zoom.", size=14, fill=T.RED, weight="700")
    c.text(56, 484, "Internal MCU pull-ups are tens of kΩ — not a substitute for real bus resistors.", size=13, fill=T.TEXT)
    c.text(56, 514, "Chapter mentions 4.7 k with 0x801E — keep them together in the lab checklist.", size=13, fill=T.MUTED)
    c.rect(40, 590, 880, 80, fill=T.PANEL, stroke=T.STROKE, rx=8)
    c.text(56, 626, "Place in electrical-behavior section — stops 'just change CCR' cargo cult.", size=14, fill=T.TEXT, weight="700")
    c.text(56, 654, "Knowledge-track RC card; measure Cbus when the edge looks rounded.", size=13, fill=T.MUTED)
    credit(c, "Hand-drawn. Pull-up guidance compressed from UM10204 + lab practice; not a PCB fab note.")
    return c


def ch07_sr() -> Svg:
    c = Svg(960, 880, "Repeated START (Sr)", "No STOP between write pointer and read")
    c.header(tag="07", tag_color=T.VIOLET)
    c.text(40, 86, "MPU6050 / EEPROMs: write register index, Sr, then read data.", size=15, fill=T.TEXT, weight="700")
    steps = [
        ("START", "addr+W", "ACK", T.AMBER),
        ("DATA", "reg 0x6B", "ACK", T.CYAN),
        ("Sr", "addr+R", "ACK", T.GREEN),
        ("DATA", "read bytes", "NACK+STOP", T.VIOLET),
    ]
    for i, (a, b, c3, col) in enumerate(steps):
        x = 40 + i * 230
        c.rect(x, 130, 210, 130, fill=T.PANEL, stroke=col, rx=8)
        c.text(x + 105, 168, a, size=16, anchor="middle", fill=col, weight="700")
        c.text(x + 105, 204, b, size=13, anchor="middle", fill=T.TEXT, mono=True)
        c.text(x + 105, 236, c3, size=13, anchor="middle", fill=T.MUTED)
        if i < 3:
            c.arrow(x + 214, 195, x + 226, 195, color=T.STROKE, sw=2)
    c.rect(40, 300, 880, 160, fill=T.BG2, stroke=T.GREEN, rx=8)
    c.text(56, 334, "Sr = SDA↓ while SCL=1 again, without a STOP in between — bus stays owned.", size=14, fill=T.GREEN, weight="700")
    c.text(56, 364, "If you STOP after the register write, another master (or your own bug) can steal the bus.", size=13, fill=T.TEXT)
    c.text(56, 394, "HAL: often Mem_Read helpers issue Sr for you — know what the helper hides.", size=13, fill=T.MUTED)
    c.text(56, 424, "Bit-bang labs must code Sr explicitly; copying START code twice is not enough if STOP sneaks in.", size=13, fill=T.MUTED)
    c.rect(40, 490, 880, 120, fill=T.PANEL, stroke=T.RED, rx=8)
    c.text(56, 524, "Scope check: after reg byte ACK, next edge should be Sr, not STOP then START.", size=14, fill=T.RED, weight="700")
    c.text(56, 554, "MPU6050 init notes in chapter assume this pattern for whoami / wake-up reads.", size=13, fill=T.TEXT)
    c.text(56, 584, "Pairs with sample-07-i2c-addr — addr GIF is first byte; this card is the multi-phase story.", size=13, fill=T.MUTED)
    credit(c, "Hand-drawn. Sr semantics from UM10204; aligned with MPU6050 lab narrative.")
    return c


def ch08_mode0() -> Svg:
    c = Svg(960, 880, "SPI Mode 0 edges", "CPOL=0 CPHA=0 sample on rising SCK")
    c.header(tag="08", tag_color=T.CYAN)
    c.text(40, 86, "Idle SCK low. Capture on first edge (rising). Change on falling. JEDEC flash default.", size=14, fill=T.TEXT, weight="700")
    c.rect(40, 120, 880, 200, fill=T.PANEL, stroke=T.STROKE, rx=8)
    c.text(56, 154, "SCK  __/¯\\_/¯\\_/¯\\_  (first rising samples bit7)", size=16, fill=T.CYAN, weight="700", mono=True)
    c.text(56, 194, "MOSI ----< bit7 >< bit6 >----  stable before rising edge", size=14, fill=T.TEXT, mono=True)
    c.text(56, 234, "MISO ----< bit7 >< bit6 >----  slave also launches on trailing edge", size=14, fill=T.TEXT, mono=True)
    c.text(56, 274, "CS   ¯\\___________________/¯  asserted before first SCK", size=14, fill=T.AMBER, mono=True)
    modes = [
        ("Mode0", "CPOL0 CPHA0", "sample rising", T.GREEN),
        ("Mode1", "CPOL0 CPHA1", "sample falling", T.CYAN),
        ("Mode2", "CPOL1 CPHA0", "sample falling", T.AMBER),
        ("Mode3", "CPOL1 CPHA1", "sample rising", T.VIOLET),
    ]
    for i, (m, cpol, note, col) in enumerate(modes):
        x = 40 + i * 230
        c.rect(x, 350, 210, 100, fill=T.PANEL, stroke=col, rx=8)
        c.text(x + 105, 384, m, size=15, anchor="middle", fill=col, weight="700")
        c.text(x + 105, 412, cpol, size=12, anchor="middle", fill=T.TEXT, mono=True)
        c.text(x + 105, 436, note, size=12, anchor="middle", fill=T.MUTED)
    c.rect(40, 480, 880, 120, fill=T.BG2, stroke=T.RED, rx=8)
    c.text(56, 514, "Wrong mode => every bit shifted; JEDEC ID becomes garbage, not a wiring myth only.", size=14, fill=T.RED, weight="700")
    c.text(56, 544, "sample-08-cpha-modes already compares all four; this card zooms Mode0 for the flash lab.", size=13, fill=T.TEXT)
    c.text(56, 574, "Pins in chapter GIF: PA5 SCK, PA7 MOSI, PA6 MISO, software CS on PA4.", size=13, fill=T.MUTED)
    credit(c, "Hand-drawn. Mode0 timing from RM0008 SPI + flash JEDEC practice.")
    return c


def ch08_br_table() -> Svg:
    c = Svg(960, 880, "SPI baud-rate divider", "BR[2:0] from PCLK toward 9 MHz lab")
    c.header(tag="08", tag_color=T.AMBER)
    c.text(40, 86, "SPI1 on APB2 @ 72 MHz. BR=010 => /8 => 9 MHz SCK (chapter JEDEC GIF).", size=14, fill=T.TEXT, weight="700")
    rows = [
        ("000", "/2", "36 MHz", "often too fast for breadboard flash", T.RED),
        ("001", "/4", "18 MHz", "short wires / good flash", T.AMBER),
        ("010", "/8", "9 MHz", "chapter lab default", T.GREEN),
        ("011", "/16", "4.5 MHz", "safe debug speed", T.CYAN),
        ("100", "/32", "2.25 MHz", "long Dupont", T.VIOLET),
    ]
    for i, (br, div, f, note, col) in enumerate(rows):
        y = 120 + i * 62
        c.rect(40, y, 880, 54, fill=T.PANEL, stroke=col, rx=8)
        c.text(56, y + 34, "BR="+br, size=14, fill=col, weight="700", mono=True)
        c.text(180, y + 34, div, size=14, fill=T.TEXT, mono=True)
        c.text(300, y + 34, f, size=14, fill=T.TEXT, weight="700", mono=True)
        c.text(880, y + 34, note, size=13, fill=T.MUTED, anchor="end")
    c.rect(40, 450, 880, 140, fill=T.BG2, stroke=T.CYAN, rx=8)
    c.text(56, 484, "SPI2 on APB1 @ 36 MHz: same BR field, half the SCK — do not copy SPI1 numbers blindly.", size=14, fill=T.CYAN, weight="700")
    c.text(56, 514, "ST7789 write-only panels often tolerate higher SCK than SPI flash ID reads on jumper wire.", size=13, fill=T.TEXT)
    c.text(56, 544, "Probe: scope SCK frequency, not only CR1.BR bits — clock tree mistakes show up here.", size=13, fill=T.MUTED)
    c.rect(40, 620, 880, 70, fill=T.PANEL, stroke=T.STROKE, rx=8)
    c.text(56, 656, "Sits in rate/divider section — concrete MHz table instead of another bullet list.", size=14, fill=T.TEXT, weight="700")
    credit(c, "Hand-drawn. BR table from RM0008 SPI; 9 MHz matches spi-jedec.gif story.")
    return c


def ch08_nss() -> Svg:
    c = Svg(960, 880, "NSS / multi-slave map", "Software CS per flash or panel")
    c.header(tag="08", tag_color=T.VIOLET)
    c.text(40, 86, "Shared SCK/MOSI/MISO; each slave needs its own CS. Master mode SSM/SSI tricks.", size=14, fill=T.TEXT, weight="700")
    c.rect(40, 120, 200, 200, fill=T.PANEL, stroke=T.CYAN, rx=8)
    c.text(140, 160, "MCU", size=16, fill=T.CYAN, weight="700", anchor="middle")
    c.text(140, 196, "PA5 SCK", size=13, fill=T.TEXT, anchor="middle", mono=True)
    c.text(140, 224, "PA7 MOSI", size=13, fill=T.TEXT, anchor="middle", mono=True)
    c.text(140, 252, "PA6 MISO", size=13, fill=T.TEXT, anchor="middle", mono=True)
    c.text(140, 286, "PA4 CS0", size=13, fill=T.AMBER, anchor="middle", mono=True)
    c.arrow(250, 180, 320, 150, color=T.STROKE, sw=2)
    c.arrow(250, 220, 320, 220, color=T.STROKE, sw=2)
    c.arrow(250, 280, 320, 290, color=T.STROKE, sw=2)
    c.rect(330, 120, 280, 100, fill=T.PANEL, stroke=T.GREEN, rx=8)
    c.text(470, 160, "W25Q flash", size=15, fill=T.GREEN, weight="700", anchor="middle")
    c.text(470, 192, "CS = PA4 (active low)", size=13, fill=T.TEXT, anchor="middle")
    c.rect(330, 250, 280, 100, fill=T.PANEL, stroke=T.AMBER, rx=8)
    c.text(470, 290, "ST7789 panel", size=15, fill=T.AMBER, weight="700", anchor="middle")
    c.text(470, 322, "CS = PBy (separate)", size=13, fill=T.TEXT, anchor="middle")
    c.rect(640, 120, 280, 230, fill=T.PANEL, stroke=T.VIOLET, rx=8)
    c.text(780, 160, "Rules", size=15, fill=T.VIOLET, weight="700", anchor="middle")
    c.text(660, 200, "- only one CS low at a time", size=13, fill=T.TEXT)
    c.text(660, 232, "- idle CS high before init", size=13, fill=T.TEXT)
    c.text(660, 264, "- HW NSS single-slave only", size=13, fill=T.TEXT)
    c.text(660, 296, "- SSM=1 for soft NSS master", size=13, fill=T.TEXT)
    c.rect(40, 380, 880, 160, fill=T.BG2, stroke=T.RED, rx=8)
    c.text(56, 414, "Two CS low => both drive MISO => ID bytes corrupt; looks like 'bad mode'.", size=14, fill=T.RED, weight="700")
    c.text(56, 444, "Chapter macros FLASH_CS_LOW/HIGH are the multi-slave pattern even for one part.", size=13, fill=T.TEXT)
    c.text(56, 474, "Write-only panels may float MISO — do not share that line with a flash without a jumper plan.", size=13, fill=T.MUTED)
    c.text(56, 504, "Pairs with bus-compare SVG — this card is the CS topology, not protocol ranking.", size=13, fill=T.MUTED)
    c.rect(40, 570, 880, 90, fill=T.PANEL, stroke=T.STROKE, rx=8)
    c.text(56, 606, "Place under NSS/multi-slave — diagram beats another paragraph of CS folklore.", size=14, fill=T.TEXT, weight="700")
    c.text(56, 636, "Knowledge-track wiring card; pin letters follow the chapter flash lab.", size=13, fill=T.MUTED)
    credit(c, "Hand-drawn. NSS/multi-slave practice for F103 SPI labs; matches FLASH_CS macros.")
    return c


FIGURES = [
    ("sample-04-priority-group.svg", ch04_priority_group),
    ("sample-04-tail-chaining.svg", ch04_tail_chain),
    ("sample-04-exti-line-map.svg", ch04_exti_map),
    ("sample-05-timebase-math.svg", ch05_timebase),
    ("sample-05-shadow-regs.svg", ch05_shadow),
    ("sample-05-deadtime.svg", ch05_deadtime),
    ("sample-07-start-ack.svg", ch07_start_ack),
    ("sample-07-pullup-cap.svg", ch07_pullup),
    ("sample-07-sr-restart.svg", ch07_sr),
    ("sample-08-mode0-edges.svg", ch08_mode0),
    ("sample-08-br-table.svg", ch08_br_table),
    ("sample-08-nss-multi.svg", ch08_nss),
]


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    for name, fn in FIGURES:
        svg = fn()
        path = os.path.join(OUT, name)
        svg.save(path)
        audit_static(name, path)
    print(f"wrote {len(FIGURES)} figures -> {OUT}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""High-density static Handraw figures for ch11–17."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from svgkit import Svg, T
from sample_figs_quality3._common import credit, audit_static

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                   "assets", "diagrams")


def ch11_backup_domain() -> Svg:
    c = Svg(960, 880, "RTC backup domain", "VBAT keeps RTC + BKP when VDD drops")
    c.header(tag="11", tag_color=T.CYAN)
    c.text(40, 86, "F103 backup domain: RTC + BKP_DRx live on VBAT when VDD is gone.", size=15, fill=T.TEXT, weight="700")
    boxes = [
        ("VDD rail", "main 3.3 V", "powers core + most peripherals", T.AMBER),
        ("VBAT pin 1", "CR2032 ~3 V", "keeps backup domain alive", T.GREEN),
        ("LSE 32.768 kHz", "PC14 / PC15", "best calendar accuracy", T.CYAN),
        ("LSI ~40 kHz", "internal RC", "30–60 kHz range, no pins", T.VIOLET),
    ]
    for i, (t, n, note, col) in enumerate(boxes):
        x = 40 + (i % 2) * 460
        y = 120 + (i // 2) * 130
        c.rect(x, y, 440, 110, fill=T.PANEL, stroke=col, rx=8)
        c.text(x + 24, y + 34, t, size=16, fill=col, weight="700")
        c.text(x + 24, y + 64, n, size=15, fill=T.TEXT, mono=True, weight="700")
        c.text(x + 24, y + 92, note, size=13, fill=T.MUTED)
    c.rect(40, 400, 880, 140, fill=T.BG2, stroke=T.GREEN, rx=8)
    c.text(56, 434, "Calendar: LSE + PRL = 32767 => 1 Hz second counter.", size=14, fill=T.GREEN, weight="700")
    c.text(56, 464, "BKP: 10 x 16-bit = 20 bytes on medium-density F103 (42 on XL).", size=13, fill=T.TEXT)
    c.text(56, 494, "After reset to zero calendar: check VBAT solder and coin cell first.", size=13, fill=T.MUTED)
    c.rect(40, 560, 880, 110, fill=T.PANEL, stroke=T.RED, rx=8)
    c.text(56, 594, "Trap: short LSE timeout => false 'crystal failed' while it is still starting.", size=14, fill=T.RED, weight="700")
    c.text(56, 624, "Debug tip: temporarily run on LSI to prove calendar logic, then bring LSE back.", size=13, fill=T.MUTED)
    credit(c, "Hand-drawn. Backup domain from RM0008 RTC/BKP + DS5319 LSE/LSI.")
    return c


def ch11_iwdg_math() -> Svg:
    c = Svg(960, 880, "IWDG 1 s math", "LSI 40 kHz / 64 => 625 Hz; Reload 624")
    c.header(tag="11", tag_color=T.AMBER)
    c.text(40, 86, "T = (PSC divider) / f_LSI x (Reload + 1). Off-by-one lives in the +1.", size=15, fill=T.TEXT, weight="700")
    steps = [
        ("f_LSI", "40 kHz", "typical (30–60)", T.CYAN),
        ("/ PSC", "64", "IWDG_PRESCALER_64", T.GREEN),
        ("tick", "625 Hz", "40e3 / 64", T.AMBER),
        ("Reload", "624", "(624+1)/625 = 1 s", T.VIOLET),
    ]
    for i, (t, n, note, col) in enumerate(steps):
        x = 40 + i * 230
        c.rect(x, 130, 210, 130, fill=T.PANEL, stroke=col, rx=8)
        c.text(x + 105, 168, t, size=14, anchor="middle", fill=col, weight="700", mono=True)
        c.text(x + 105, 204, n, size=22, anchor="middle", fill=T.TEXT, weight="700", mono=True)
        c.text(x + 105, 236, note, size=12, anchor="middle", fill=T.MUTED)
        if i < 3:
            c.arrow(x + 214, 195, x + 226, 195, color=T.STROKE, sw=2)
    c.rect(40, 290, 880, 120, fill=T.BG2, stroke=T.GREEN, rx=8)
    c.text(56, 324, "Correct 1 s: Reload = 624. Reload = 625 => 626 ticks => not one second.", size=15, fill=T.GREEN, weight="700", mono=True)
    c.text(56, 358, "Max Reload 4095 => (4095+1)/625 = 6.5536 s — lab 'about 6.5 s' case.", size=13, fill=T.TEXT)
    c.text(56, 386, "LSI is not a crystal: leave margin for 30 kHz and 60 kHz corners.", size=13, fill=T.MUTED)
    c.rect(40, 430, 880, 130, fill=T.PANEL, stroke=T.RED, rx=8)
    c.text(56, 464, "Feed late (count hits 0) => reset. Feed early is fine for IWDG.", size=14, fill=T.RED, weight="700")
    c.text(56, 494, "WWDG is different: window opens late; feeding too early also resets (0x50 story).", size=13, fill=T.TEXT)
    c.text(56, 524, "Debug: set DBG_IWDG_STOP so a breakpoint does not look like a hang.", size=13, fill=T.MUTED)
    c.rect(40, 580, 880, 90, fill=T.PANEL, stroke=T.STROKE, rx=8)
    c.text(56, 614, "Place beside the IWDG lab — formula card before the feed GIF.", size=14, fill=T.TEXT, weight="700")
    c.text(56, 644, "Knowledge track; pairs with sample-11-iwdg-1s and iwdg-1s.gif.", size=13, fill=T.MUTED)
    credit(c, "Hand-drawn. IWDG timing from RM0008 §19; LSI range from DS5319 table 25.")
    return c


def ch12_page_erase() -> Svg:
    c = Svg(960, 880, "Flash page erase", "F103C8: 1 KB pages; erase before program")
    c.header(tag="12", tag_color=T.CYAN)
    c.text(40, 86, "Medium-density F1 erases 1 KB pages; program is half-word (16-bit) only.", size=15, fill=T.TEXT, weight="700")
    rows = [
        ("Bootloader", "0x08000000", "16 KB", "pages 0–15", T.AMBER),
        ("Param", "0x08004000", "2 KB", "pages 16–17", T.VIOLET),
        ("APP", "0x08004800", "46 KB / 0xB800", "pages 18–63", T.GREEN),
        ("End (C8)", "0x08010000", "64 KB total", "last page 0x0800FC00", T.CYAN),
    ]
    for i, (name, addr, size, note, col) in enumerate(rows):
        y = 120 + i * 70
        c.rect(40, y, 880, 60, fill=T.PANEL, stroke=col, rx=8)
        c.text(56, y + 36, name, size=15, fill=col, weight="700")
        c.text(220, y + 36, addr, size=14, fill=T.TEXT, mono=True, weight="700")
        c.text(480, y + 36, size, size=14, fill=T.TEXT, mono=True)
        c.text(880, y + 36, note, size=13, fill=T.MUTED, anchor="end")
    c.rect(40, 420, 880, 130, fill=T.BG2, stroke=T.RED, rx=8)
    c.text(56, 454, "Trap: erase address must sit on a page boundary — else FLASH error.", size=14, fill=T.RED, weight="700")
    c.text(56, 484, "Trap: 0x0801FC00 is a 128 KB part's last page — C8 ends at 0x0800FC00.", size=13, fill=T.TEXT)
    c.text(56, 514, "Blank check: erased half-word reads 0xFFFF before you program.", size=13, fill=T.MUTED)
    c.rect(40, 570, 880, 100, fill=T.PANEL, stroke=T.GREEN, rx=8)
    c.text(56, 604, "IAP map in this book: APP @ 0x08004800, length 0xB800 (46 KB).", size=14, fill=T.GREEN, weight="700")
    c.text(56, 634, "Matches examples/iap-bootloader linker script — keep VTOR in sync.", size=13, fill=T.MUTED)
    credit(c, "Hand-drawn. Page size + map from RM0008 FLASH and the IAP example.")
    return c


def ch12_key_order() -> Svg:
    c = Svg(960, 880, "FLASH unlock keys", "KEY1 then KEY2; reverse leaves LOCK set")
    c.header(tag="12", tag_color=T.AMBER)
    c.text(40, 86, "Write FLASH_KEYR in order, then program half-words, then re-lock.", size=15, fill=T.TEXT, weight="700")
    steps = [
        ("1 KEY1", "0x45670123", "first write", T.CYAN),
        ("2 KEY2", "0xCDEF89AB", "clears CR.LOCK", T.GREEN),
        ("3 ERASE/PROG", "page / half-word", "PG or PER set", T.AMBER),
        ("4 LOCK", "set CR.LOCK", "re-arm protection", T.VIOLET),
    ]
    for i, (t, n, note, col) in enumerate(steps):
        x = 40 + i * 230
        c.rect(x, 130, 210, 140, fill=T.PANEL, stroke=col, rx=8)
        c.text(x + 105, 170, t, size=14, anchor="middle", fill=col, weight="700")
        c.text(x + 105, 206, n, size=15, anchor="middle", fill=T.TEXT, weight="700", mono=True)
        c.text(x + 105, 240, note, size=12, anchor="middle", fill=T.MUTED)
        if i < 3:
            c.arrow(x + 214, 200, x + 226, 200, color=T.STROKE, sw=2)
    c.rect(40, 300, 880, 120, fill=T.BG2, stroke=T.GREEN, rx=8)
    c.text(56, 334, "Jump path: word0 @ APP = MSP, word1 = Reset_Handler; VTOR = 0x08004800.", size=14, fill=T.GREEN, weight="700")
    c.text(56, 364, "If VTOR stays 0, interrupts vector back into the bootloader.", size=13, fill=T.TEXT)
    c.text(56, 394, "Half-word program only — packing bytes wrong leaves 0xFF holes.", size=13, fill=T.MUTED)
    c.rect(40, 440, 880, 120, fill=T.PANEL, stroke=T.RED, rx=8)
    c.text(56, 474, "Fail: KEY2 then KEY1 => LOCK stays set; erase returns error.", size=14, fill=T.RED, weight="700")
    c.text(56, 504, "Fail: jump without loading MSP/Reset_Handler => hard fault / reboot loop.", size=13, fill=T.TEXT)
    c.text(56, 534, "Probe: read FLASH_CR.LOCK bit before PER/PG; confirm KEY order in debugger.", size=13, fill=T.MUTED)
    c.rect(40, 580, 880, 90, fill=T.PANEL, stroke=T.STROKE, rx=8)
    c.text(56, 614, "Teaching card for unlock + jump — failure cases stay on triage SVG.", size=14, fill=T.TEXT, weight="700")
    c.text(56, 644, "Pairs with sample-12-iap-map and iap-jump.gif.", size=13, fill=T.MUTED)
    credit(c, "Hand-drawn. Key values from RM0008 FLASH; APP base matches the IAP lab.")
    return c


def ch13_bit_quanta() -> Svg:
    c = Svg(960, 880, "CAN bit time", "36 MHz / 9 => 250 ns; 8 TQ => 500 kbit/s")
    c.header(tag="13", tag_color=T.CYAN)
    c.text(40, 86, "APB1 = 36 MHz. Prescaler 9 => Tq = 250 ns. 1+5+2 = 8 quanta => 2 us bit.", size=15, fill=T.TEXT, weight="700")
    marks = [
        ("Sync", "1 TQ", "edge", T.CYAN),
        ("BS1", "5 TQ", "prop+phase1", T.GREEN),
        ("Sample", "75%", "at 1.5 us", T.AMBER),
        ("BS2", "2 TQ", "phase2", T.VIOLET),
    ]
    for i, (t, n, note, col) in enumerate(marks):
        x = 40 + i * 230
        c.rect(x, 130, 210, 120, fill=T.PANEL, stroke=col, rx=8)
        c.text(x + 105, 168, t, size=15, anchor="middle", fill=col, weight="700")
        c.text(x + 105, 202, n, size=18, anchor="middle", fill=T.TEXT, weight="700", mono=True)
        c.text(x + 105, 232, note, size=12, anchor="middle", fill=T.MUTED)
    c.rect(40, 280, 880, 110, fill=T.BG2, stroke=T.GREEN, rx=8)
    c.text(56, 314, "500 kbit/s = 8 x 250 ns. Sample at (1+5)/8 = 75%.", size=15, fill=T.GREEN, weight="700", mono=True)
    c.text(56, 348, "Wrong: prescaler 8 + 10 TQ => 450 kbit/s — peers will error.", size=13, fill=T.TEXT)
    c.text(56, 376, "Both ends need the same bit time AND 120 ohm terminators at the ends.", size=13, fill=T.MUTED)
    c.rect(40, 410, 880, 130, fill=T.PANEL, stroke=T.AMBER, rx=8)
    c.text(56, 444, "Pins on Blue Pill: CAN_RX PB8 (remap) / CAN_TX PB9 via AFIO.", size=14, fill=T.AMBER, weight="700")
    c.text(56, 474, "Transceiver: SN65HVD230 = 3.3 V; TJA1050 = 5 V — match the rail.", size=13, fill=T.TEXT)
    c.text(56, 504, "Single node without loopback: TEC climbs to 128, stays error-passive.", size=13, fill=T.MUTED)
    c.rect(40, 560, 880, 110, fill=T.PANEL, stroke=T.STROKE, rx=8)
    c.text(56, 594, "Mnemonic: 36 MHz, /9, 8 quanta, 75% sample, 500 kbit/s.", size=14, fill=T.TEXT, weight="700")
    c.text(56, 624, "Pairs with sample-13-can-bit and can-500k.gif.", size=13, fill=T.MUTED)
    credit(c, "Hand-drawn. Bit timing from RM0008 CAN; matches chapter 500 kbit/s lab.")
    return c


def ch13_filter_fifo() -> Svg:
    c = Svg(960, 880, "CAN filters + dual FIFO", "F1: 14 banks, FIFO0/FIFO1")
    c.header(tag="13", tag_color=T.GREEN)
    c.text(40, 86, "Accepted frames land in FIFO0 or FIFO1; software drains before overrun.", size=15, fill=T.TEXT, weight="700")
    c.rect(40, 120, 420, 220, fill=T.PANEL, stroke=T.CYAN, rx=8)
    c.text(250, 156, "Filter banks", size=15, fill=T.CYAN, weight="700", anchor="middle")
    c.text(250, 196, "14 banks (F103)", size=14, fill=T.TEXT, anchor="middle", mono=True)
    c.text(250, 228, "Id / Mask or Id list", size=13, fill=T.MUTED, anchor="middle")
    c.text(250, 260, "Assign each bank → FIFO0/1", size=13, fill=T.MUTED, anchor="middle")
    c.text(250, 300, "Scale: 16-bit or 32-bit", size=13, fill=T.MUTED, anchor="middle")
    c.rect(500, 120, 420, 220, fill=T.PANEL, stroke=T.GREEN, rx=8)
    c.text(710, 156, "Dual FIFO", size=15, fill=T.GREEN, weight="700", anchor="middle")
    c.text(710, 196, "FIFO0  ·  FIFO1", size=16, fill=T.TEXT, anchor="middle", mono=True, weight="700")
    c.text(710, 228, "3 stages each", size=13, fill=T.MUTED, anchor="middle")
    c.text(710, 260, "Separate IRQ lines", size=13, fill=T.MUTED, anchor="middle")
    c.text(710, 300, "Priority by bank order", size=13, fill=T.MUTED, anchor="middle")
    c.rect(40, 370, 880, 140, fill=T.BG2, stroke=T.AMBER, rx=8)
    c.text(56, 404, "Why two FIFOs: hard realtime ID → FIFO0 IRQ; bulk telemetry → FIFO1.", size=14, fill=T.AMBER, weight="700")
    c.text(56, 434, "Overrun sets FOVR — you lost a frame; fix drain rate, not just filters.", size=13, fill=T.TEXT)
    c.text(56, 464, "Silent mode / loopback: useful for bring-up without a second node.", size=13, fill=T.MUTED)
    c.rect(40, 530, 880, 140, fill=T.PANEL, stroke=T.RED, rx=8)
    c.text(56, 564, "Trap: filter left in init mode => nothing is received (looks like wiring).", size=14, fill=T.RED, weight="700")
    c.text(56, 594, "Trap: Mask bits inverted vs Cube screenshot — verify with a known ID.", size=13, fill=T.TEXT)
    c.text(56, 624, "Knowledge-track mux card; scope photos stay on the evidence track.", size=13, fill=T.MUTED)
    credit(c, "Hand-drawn. Filter/FIFO model from RM0008 CAN §24.")
    return c


def ch13_tec_busoff() -> Svg:
    c = Svg(960, 880, "CAN error counters", "TEC 128 = passive; TEC > 255 = bus-off")
    c.header(tag="13", tag_color=T.AMBER)
    c.text(40, 86, "No ACK on a lone node: TEC climbs by 8 per try, stops at error-passive.", size=15, fill=T.TEXT, weight="700")
    stages = [
        ("Error-active", "TEC < 128", "drives active flags", T.GREEN),
        ("Error-passive", "TEC ≥ 128", "passive flags only", T.AMBER),
        ("Bus-off", "TEC > 255", "stops driving bus", T.RED),
        ("Recover", "128×11 recessives", "ABOM or software", T.CYAN),
    ]
    for i, (t, n, note, col) in enumerate(stages):
        x = 40 + i * 230
        c.rect(x, 130, 210, 130, fill=T.PANEL, stroke=col, rx=8)
        c.text(x + 105, 168, t, size=14, anchor="middle", fill=col, weight="700")
        c.text(x + 105, 204, n, size=15, anchor="middle", fill=T.TEXT, weight="700", mono=True)
        c.text(x + 105, 236, note, size=12, anchor="middle", fill=T.MUTED)
    c.rect(40, 290, 880, 130, fill=T.BG2, stroke=T.CYAN, rx=8)
    c.text(56, 324, "Single node, normal mode, no ACK: TEC reaches 128 and keeps retransmitting.", size=14, fill=T.CYAN, weight="700")
    c.text(56, 354, "It will NOT walk into bus-off from ACK-less alone — need real bit errors.", size=13, fill=T.TEXT)
    c.text(56, 384, "ABOM: hardware waits 128 sequences of 11 recessive bits, then retries.", size=13, fill=T.MUTED)
    c.rect(40, 440, 880, 120, fill=T.PANEL, stroke=T.RED, rx=8)
    c.text(56, 474, "Lab: unplug second node → watch TEC; plug back → first good frame clears stress.", size=14, fill=T.RED, weight="700")
    c.text(56, 504, "Do not call 'bus-off' when you are only error-passive at 128.", size=13, fill=T.TEXT)
    c.text(56, 534, "Pairs with can-arbitration animation — this card is the counter ladder.", size=13, fill=T.MUTED)
    c.rect(40, 580, 880, 90, fill=T.PANEL, stroke=T.STROKE, rx=8)
    c.text(56, 614, "Extra density for ch13 (thinnest chapter) — real TEC numbers, not icons.", size=14, fill=T.TEXT, weight="700")
    c.text(56, 644, "Numbers from RM0008 CAN error management.", size=13, fill=T.MUTED)
    credit(c, "Hand-drawn. TEC/REC thresholds from RM0008 CAN.")
    return c


def ch14_usbpre() -> Svg:
    c = Svg(960, 880, "USB 48 MHz clock", "USBPRE=0 => 72/1.5 = 48 MHz")
    c.header(tag="14", tag_color=T.CYAN)
    c.text(40, 86, "Full-speed device clock is hard: wrong USBCLK => enumeration dies early.", size=15, fill=T.TEXT, weight="700")
    steps = [
        ("PLL", "72 MHz", "system clock", T.CYAN),
        ("USBPRE", "0", "divide by 1.5", T.GREEN),
        ("USBCLK", "48 MHz", "FS requirement", T.AMBER),
        ("D+ pull-up", "1.5 kΩ", "PA12 / pin 33", T.VIOLET),
    ]
    for i, (t, n, note, col) in enumerate(steps):
        x = 40 + i * 230
        c.rect(x, 130, 210, 130, fill=T.PANEL, stroke=col, rx=8)
        c.text(x + 105, 168, t, size=14, anchor="middle", fill=col, weight="700", mono=True)
        c.text(x + 105, 204, n, size=20, anchor="middle", fill=T.TEXT, weight="700", mono=True)
        c.text(x + 105, 236, note, size=12, anchor="middle", fill=T.MUTED)
        if i < 3:
            c.arrow(x + 214, 195, x + 226, 195, color=T.STROKE, sw=2)
    c.rect(40, 290, 880, 120, fill=T.BG2, stroke=T.GREEN, rx=8)
    c.text(56, 324, "USBPRE=0 => 48 MHz (correct). USBPRE=1 => undivided PLL — host rejects.", size=14, fill=T.GREEN, weight="700")
    c.text(56, 354, "Descriptors in this book: device 18 bytes + config set 67 bytes.", size=13, fill=T.TEXT)
    c.text(56, 384, "VID/PID example 0x1209/0x0001 — still must match what the host driver expects.", size=13, fill=T.MUTED)
    c.rect(40, 430, 880, 120, fill=T.PANEL, stroke=T.RED, rx=8)
    c.text(56, 464, "Fail: pull-up on D− (low-speed) while coding a full-speed stack.", size=14, fill=T.RED, weight="700")
    c.text(56, 494, "Fail: blaming CDC code when RCC USB clock is wrong — check USBPRE first.", size=13, fill=T.TEXT)
    c.text(56, 524, "Bus current before config ≤ 100 mA; after config follow bMaxPower.", size=13, fill=T.MUTED)
    c.rect(40, 570, 880, 100, fill=T.PANEL, stroke=T.STROKE, rx=8)
    c.text(56, 604, "Clock card before enum animation — 48 MHz is non-negotiable.", size=14, fill=T.TEXT, weight="700")
    c.text(56, 634, "Pairs with sample-14-usb-enum and usb-48m.gif.", size=13, fill=T.MUTED)
    credit(c, "Hand-drawn. USBPRE from RM0008 RCC; FS 48 MHz from USB 2.0 FS rules.")
    return c


def ch14_pma_map() -> Svg:
    c = Svg(960, 880, "USB PMA + endpoints", "512-byte packet memory; EP0..EP7")
    c.header(tag="14", tag_color=T.AMBER)
    c.text(40, 86, "F1 USB FS: up to 8 bidirectional endpoints share a 512-byte PMA.", size=15, fill=T.TEXT, weight="700")
    rows = [
        ("EP0", "CONTROL", "8–64 B", "enumeration + standards", T.CYAN),
        ("EP1 IN", "BULK/INT", "CDC data IN", "device → host", T.GREEN),
        ("EP1 OUT", "BULK", "CDC data OUT", "host → device", T.AMBER),
        ("EP2", "INT IN", "CDC notif", "SerialState", T.VIOLET),
    ]
    for i, (ep, kind, size, note, col) in enumerate(rows):
        y = 120 + i * 70
        c.rect(40, y, 880, 60, fill=T.PANEL, stroke=col, rx=8)
        c.text(56, y + 36, ep, size=15, fill=col, weight="700", mono=True)
        c.text(180, y + 36, kind, size=14, fill=T.TEXT, mono=True)
        c.text(400, y + 36, size, size=14, fill=T.TEXT)
        c.text(880, y + 36, note, size=13, fill=T.MUTED, anchor="end")
    c.rect(40, 420, 880, 130, fill=T.BG2, stroke=T.GREEN, rx=8)
    c.text(56, 454, "IN/OUT are named from the host. Device 'send' is an IN endpoint.", size=14, fill=T.GREEN, weight="700")
    c.text(56, 484, "BTABLE + USB_EPnR point into PMA — overlap two buffers and packets corrupt.", size=13, fill=T.TEXT)
    c.text(56, 514, "wTotalLength must cover the whole config set (67 bytes in the chapter example).", size=13, fill=T.MUTED)
    c.rect(40, 570, 880, 100, fill=T.PANEL, stroke=T.RED, rx=8)
    c.text(56, 604, "Stuck at enum step 6/7: check wTotalLength, endpoint address, and PMA alloc.", size=14, fill=T.RED, weight="700")
    c.text(56, 634, "Knowledge-track memory map — not a USB analyzer capture.", size=13, fill=T.MUTED)
    credit(c, "Hand-drawn. PMA/endpoint model from RM0008 USB §23.")
    return c


def ch15_task_states() -> Svg:
    c = Svg(960, 880, "FreeRTOS task states", "Ready / Running / Blocked / Suspended")
    c.header(tag="15", tag_color=T.CYAN)
    c.text(40, 86, "One Running task per core. Ready waits for CPU time; Blocked waits for time or an event.", size=15, fill=T.TEXT, weight="700")
    states = [
        ("Running", "on CPU", "highest ready", T.GREEN),
        ("Ready", "in ready list", "waiting for CPU", T.CYAN),
        ("Blocked", "delay / queue / sem", "event exits block", T.AMBER),
        ("Suspended", "vTaskSuspend", "explicit only", T.VIOLET),
    ]
    for i, (t, n, note, col) in enumerate(states):
        x = 40 + i * 230
        c.rect(x, 130, 210, 130, fill=T.PANEL, stroke=col, rx=8)
        c.text(x + 105, 168, t, size=15, anchor="middle", fill=col, weight="700")
        c.text(x + 105, 204, n, size=13, anchor="middle", fill=T.TEXT)
        c.text(x + 105, 236, note, size=12, anchor="middle", fill=T.MUTED)
    c.rect(40, 290, 880, 130, fill=T.BG2, stroke=T.AMBER, rx=8)
    c.text(56, 324, "Tick = 1 ms when configTICK_RATE_HZ = 1000. Priority 2 preempts priority 1.", size=14, fill=T.AMBER, weight="700")
    c.text(56, 354, "Stack depth is in words: LED 128 words = 512 bytes (not 128 bytes).", size=13, fill=T.TEXT)
    c.text(56, 384, "This example uses SysTick for the kernel and TIM4 for HAL; sharing needs integration.", size=13, fill=T.MUTED)
    c.rect(40, 440, 880, 120, fill=T.PANEL, stroke=T.RED, rx=8)
    c.text(56, 474, "vTaskDelayUntil advances planned wake times; actual entry can still jitter.", size=14, fill=T.RED, weight="700")
    c.text(56, 504, "A high-priority task that stays Ready can starve lower priorities; blocking frees the CPU.", size=13, fill=T.TEXT)
    c.text(56, 534, "configASSERT catches many priority / ISR API mistakes early.", size=13, fill=T.MUTED)
    c.rect(40, 580, 880, 90, fill=T.PANEL, stroke=T.STROKE, rx=8)
    c.text(56, 614, "An event can wake a task between two ticks; Ready does not mean waiting for a tick.", size=14, fill=T.TEXT, weight="700")
    c.text(56, 644, "Suspended needs an explicit resume; a timeout does not resume it.", size=13, fill=T.MUTED)
    credit(c, "Hand-drawn. Task model from FreeRTOS kernel docs; numbers match chapter labs.")
    return c


def ch15_fromisr() -> Svg:
    c = Svg(960, 880, "FromISR API wall", "ISR may only call *FromISR variants")
    c.header(tag="15", tag_color=T.AMBER)
    c.text(40, 86, "Inside an ISR: queue/sem/task notify FromISR only; never the task versions.", size=15, fill=T.TEXT, weight="700")
    c.rect(40, 120, 440, 240, fill=T.PANEL, stroke=T.GREEN, rx=8)
    c.text(260, 156, "Allowed in ISR", size=15, fill=T.GREEN, weight="700", anchor="middle")
    for i, line in enumerate([
        "xQueueSendFromISR",
        "xSemaphoreGiveFromISR",
        "vTaskNotifyGiveFromISR",
        "portYIELD_FROM_ISR",
        "uxQueueMessagesWaitingFromISR",
    ]):
        c.text(70, 196 + i * 30, line, size=14, fill=T.TEXT, mono=True)
    c.rect(500, 120, 420, 240, fill=T.PANEL, stroke=T.RED, rx=8)
    c.text(710, 156, "Never in ISR", size=15, fill=T.RED, weight="700", anchor="middle")
    for i, line in enumerate([
        "xQueueSend / Receive",
        "xSemaphoreTake",
        "vTaskDelay",
        "malloc / printf heavy",
        "non-FromISR give/take",
    ]):
        c.text(530, 196 + i * 30, line, size=14, fill=T.TEXT, mono=True)
    c.rect(40, 390, 880, 130, fill=T.BG2, stroke=T.CYAN, rx=8)
    c.text(56, 424, "NVIC preempt priority numeric value must be >= 5 when using FromISR (library default).", size=14, fill=T.CYAN, weight="700")
    c.text(56, 454, "Wrong: EXTI0 at preempt 1 calling xQueueSend — configASSERT / hard fault.", size=13, fill=T.TEXT)
    c.text(56, 484, "Yield: set the pxHigherPriorityTaskWoken flag so the scheduler runs on exit.", size=13, fill=T.MUTED)
    c.rect(40, 540, 880, 130, fill=T.PANEL, stroke=T.STROKE, rx=8)
    c.text(56, 574, "Place next to §10 FromISR — turns a prose rule into a wall chart.", size=14, fill=T.TEXT, weight="700")
    c.text(56, 604, "Knowledge track; pairs with sample-15-rtos-triage.", size=13, fill=T.MUTED)
    c.text(56, 634, "Numbers: 128 words / 512 bytes stack reminder still applies to tasks, not ISRs.", size=13, fill=T.MUTED)
    credit(c, "Hand-drawn. FromISR rules from FreeRTOS + chapter priority note (>=5).")
    return c


def ch16_mode_current() -> Svg:
    c = Svg(960, 880, "Low-power mode currents", "Sleep mA · Stop 14 µA · Standby 2 µA")
    c.header(tag="16", tag_color=T.CYAN)
    c.text(40, 86, "DS5319 @ 3.3 V, 25°C typicals — board leakage is a different number.", size=15, fill=T.TEXT, weight="700")
    modes = [
        ("Sleep", "14.4 mA", "periph on, 72 MHz", "5.5 mA periph off", T.AMBER),
        ("Stop LP reg", "14 µA", "no IWDG", "24 µA main regulator", T.GREEN),
        ("Standby", "2 µA", "LSI/IWDG/LSE/RTC off", "3.2 / 3.4 µA if on", T.CYAN),
        ("VBAT domain", "1.4 µA", "LSE+RTC on", "not whole-chip Standby", T.VIOLET),
    ]
    for i, (t, n, a, b, col) in enumerate(modes):
        x = 40 + (i % 2) * 460
        y = 120 + (i // 2) * 150
        c.rect(x, y, 440, 130, fill=T.PANEL, stroke=col, rx=8)
        c.text(x + 24, y + 34, t, size=16, fill=col, weight="700")
        c.text(x + 24, y + 66, n, size=20, fill=T.TEXT, weight="700", mono=True)
        c.text(x + 24, y + 96, a, size=13, fill=T.TEXT)
        c.text(x + 24, y + 118, b, size=12, fill=T.MUTED)
    c.rect(40, 440, 880, 120, fill=T.BG2, stroke=T.RED, rx=8)
    c.text(56, 474, "Do not merge Stop's 14 µA and 24 µA into a fake '20 µA' band.", size=14, fill=T.RED, weight="700")
    c.text(56, 504, "Do not call VBAT 1.4 µA 'Standby current'. IWDG keeps counting in Stop.", size=13, fill=T.TEXT)
    c.text(56, 534, "Measure LED, LDO, USB paths and probe back-power on the actual board.", size=13, fill=T.MUTED)
    c.rect(40, 580, 880, 90, fill=T.PANEL, stroke=T.STROKE, rx=8)
    c.text(56, 614, "Use the matching voltage, temperature and enabled-clock conditions.", size=14, fill=T.TEXT, weight="700")
    c.text(56, 644, "Board input current also includes regulators and external loads.", size=13, fill=T.MUTED)
    credit(c, "Hand-drawn. Currents from DS5319 tables; conditions named on the card.")
    return c


def ch16_clock_restore() -> Svg:
    c = Svg(960, 880, "Stop wake clock restore", "HSI 8 MHz first; then PLL 72 MHz; then 115200")
    c.header(tag="16", tag_color=T.AMBER)
    c.text(40, 86, "After Stop, HSE/PLL are off. System comes back on HSI 8 MHz until you rebuild.", size=15, fill=T.TEXT, weight="700")
    steps = [
        ("1 WAKE", "EXTI/RTC", "exit Stop", T.CYAN),
        ("2 HSI", "8 MHz", "default clock", T.AMBER),
        ("3 PLL", "72 MHz", "SystemClock_Config", T.GREEN),
        ("4 UART", "115200", "BRR matches 72 M", T.VIOLET),
    ]
    for i, (t, n, note, col) in enumerate(steps):
        x = 40 + i * 230
        c.rect(x, 130, 210, 130, fill=T.PANEL, stroke=col, rx=8)
        c.text(x + 105, 168, t, size=14, anchor="middle", fill=col, weight="700")
        c.text(x + 105, 204, n, size=18, anchor="middle", fill=T.TEXT, weight="700", mono=True)
        c.text(x + 105, 236, note, size=12, anchor="middle", fill=T.MUTED)
        if i < 3:
            c.arrow(x + 214, 195, x + 226, 195, color=T.STROKE, sw=2)
    c.rect(40, 290, 880, 130, fill=T.BG2, stroke=T.RED, rx=8)
    c.text(56, 324, "Skip restore: BRR 0x271 at 8 MHz => 12800 bit/s on the wire (garbled log).", size=14, fill=T.RED, weight="700")
    c.text(56, 354, "Sleep keeps the pre-sleep clock; Stop does not. SysTick 1 ms wakes Sleep, not Stop.", size=13, fill=T.TEXT)
    c.text(56, 384, "Standby (PDDS=1) restarts from the reset vector — ~50 µs to first instruction.", size=13, fill=T.MUTED)
    c.rect(40, 440, 880, 120, fill=T.PANEL, stroke=T.GREEN, rx=8)
    c.text(56, 474, "Lab check: print before Stop, wake on PA0, print after SystemClock_Config.", size=14, fill=T.GREEN, weight="700")
    c.text(56, 504, "Second line must be clean 115200 — that is the restore evidence.", size=13, fill=T.TEXT)
    c.text(56, 534, "WKUP on Standby is rising edge on PA0 — falling edge that woke Stop may fail.", size=13, fill=T.MUTED)
    c.rect(40, 580, 880, 90, fill=T.PANEL, stroke=T.STROKE, rx=8)
    c.text(56, 614, "Mark ISR entry and clock-restore completion on two GPIOs.", size=14, fill=T.TEXT, weight="700")
    c.text(56, 644, "Check the 0x55 bit width: 8.68 us after restore, 78.125 us at HSI 8 MHz.", size=13, fill=T.MUTED)
    credit(c, "Hand-drawn. Post-Stop clock behavior from RM0008 PWR/RCC; UART math from chapter.")
    return c


def ch17_swd_pins() -> Svg:
    c = Svg(960, 880, "SWD debug pins", "SWDIO / SWCLK / NRST — keep them free")
    c.header(tag="17", tag_color=T.CYAN)
    c.text(40, 86, "Cortex-M3 debug on F103: two-wire SWD plus reset. JTAG needs more pins.", size=15, fill=T.TEXT, weight="700")
    pins = [
        ("PA13", "SWDIO", "bidirectional data", "do not reuse casually", T.CYAN),
        ("PA14", "SWCLK", "clock from probe", "keep short wires", T.GREEN),
        ("NRST", "reset", "probe may drive reset", "connect-under-reset recovery", T.AMBER),
        ("PB3", "SWO", "ITM trace out", "conflicts with JTDO", T.VIOLET),
    ]
    for i, (pin, name, note, warn, col) in enumerate(pins):
        y = 120 + i * 70
        c.rect(40, y, 880, 60, fill=T.PANEL, stroke=col, rx=8)
        c.text(56, y + 36, pin, size=15, fill=col, weight="700", mono=True)
        c.text(180, y + 36, name, size=15, fill=T.TEXT, weight="700", mono=True)
        c.text(360, y + 36, note, size=13, fill=T.TEXT)
        c.text(880, y + 36, warn, size=13, fill=T.MUTED, anchor="end")
    c.rect(40, 420, 880, 130, fill=T.BG2, stroke=T.AMBER, rx=8)
    c.text(56, 454, "F103: 6 FPB instruction comparators; data watchpoints use separate DWT hardware.", size=14, fill=T.AMBER, weight="700")
    c.text(56, 484, "SWO printf needs DEMCR + TPIU setup; baud must match the viewer.", size=13, fill=T.TEXT)
    c.text(56, 514, "If firmware disables SWD, try connect-under-reset with NRST wired.", size=13, fill=T.MUTED)
    c.rect(40, 570, 880, 100, fill=T.PANEL, stroke=T.STROKE, rx=8)
    c.text(56, 604, "Share GND. Connect VTref to the target voltage reference as the probe requires.", size=14, fill=T.TEXT, weight="700")
    c.text(56, 634, "PB3 is a trace output only when trace pins are enabled; check the board routing.", size=13, fill=T.MUTED)
    credit(c, "Hand-drawn. SWD pinout from DS5319 / PM0056 debug chapter.")
    return c


def ch17_cfsr_bits() -> Svg:
    c = Svg(960, 880, "CFSR bit map", "Read 0xE000ED28; BFARVALID is bit 15")
    c.header(tag="17", tag_color=T.AMBER)
    c.text(40, 86, "Save the fault snapshot before decoding CFSR or mapping a trusted stacked PC.", size=15, fill=T.TEXT, weight="700")
    rows = [
        ("CFSR", "0xE000ED28", "configurable fault status", T.CYAN),
        ("HFSR", "0xE000ED2C", "FORCED = bit 30 (0x40000000)", T.GREEN),
        ("BFAR", "0xE000ED38", "bus fault address", T.AMBER),
        ("BFARVALID", "CFSR bit 15", "1 => valid fault address", T.VIOLET),
    ]
    for i, (t, n, note, col) in enumerate(rows):
        y = 120 + i * 70
        c.rect(40, y, 880, 60, fill=T.PANEL, stroke=col, rx=8)
        c.text(56, y + 36, t, size=15, fill=col, weight="700", mono=True)
        c.text(240, y + 36, n, size=14, fill=T.TEXT, mono=True, weight="700")
        c.text(880, y + 36, note, size=13, fill=T.MUTED, anchor="end")
    c.rect(40, 420, 880, 130, fill=T.BG2, stroke=T.RED, rx=8)
    c.text(56, 454, "bit 15 = 0: BFAR is invalid. addr2line takes a code address, not BFAR.", size=14, fill=T.RED, weight="700")
    c.text(56, 484, "IMPRECISERR does not update BFAR; the stacked PC may follow the bad write.", size=13, fill=T.TEXT)
    c.text(56, 514, "STKERR / MSTKERR can leave an incomplete frame; check before using its PC.", size=13, fill=T.MUTED)
    c.rect(40, 570, 880, 100, fill=T.PANEL, stroke=T.STROKE, rx=8)
    c.text(56, 604, "Save BFAR/MMFAR before testing VALID; higher-priority faults can update them.", size=14, fill=T.TEXT, weight="700")
    c.text(56, 634, "DWT is a separate test: enable TRCENA and CYCCNTENA; 72 counts at 72 MHz = 1 us.", size=13, fill=T.MUTED)
    credit(c, "Hand-drawn. CFSR/HFSR/BFAR from PM0056; 72-count timing from chapter.")
    return c


FIGURES = [
    ("sample-11-backup-domain.svg", ch11_backup_domain),
    ("sample-11-iwdg-math.svg", ch11_iwdg_math),
    ("sample-12-page-erase.svg", ch12_page_erase),
    ("sample-12-key-order.svg", ch12_key_order),
    ("sample-13-bit-quanta.svg", ch13_bit_quanta),
    ("sample-13-filter-fifo.svg", ch13_filter_fifo),
    ("sample-13-tec-busoff.svg", ch13_tec_busoff),
    ("sample-14-usbpre-48.svg", ch14_usbpre),
    ("sample-14-pma-map.svg", ch14_pma_map),
    ("sample-15-task-states.svg", ch15_task_states),
    ("sample-15-fromisr.svg", ch15_fromisr),
    ("sample-16-mode-current.svg", ch16_mode_current),
    ("sample-16-clock-restore.svg", ch16_clock_restore),
    ("sample-17-swd-pins.svg", ch17_swd_pins),
    ("sample-17-cfsr-bits.svg", ch17_cfsr_bits),
]


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    for name, fn in FIGURES:
        path = os.path.join(OUT, name)
        fn().save(path)
        audit_static(name, path)
    print(f"wrote {len(FIGURES)} figures -> {OUT}")


if __name__ == "__main__":
    main()

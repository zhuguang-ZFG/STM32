#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""High-density static Handraw figures for ch23–28 + appendix F."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from svgkit import Svg, T
from sample_figs_quality5._common import credit, audit_static

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                   "assets", "diagrams")


def ch23_boot0_swclk() -> Svg:
    c = Svg(960, 880, "G0 BOOT0 shares SWCLK", "Sample BOOT0 before you trust SWD")
    c.header(tag="23", tag_color=T.CYAN)
    c.text(40, 86, "On G071 LQFP64, BOOT0 can sit on the same pad family as SWCLK — decide boot source first.", size=15, fill=T.TEXT, weight="700")
    rows = [
        ("BOOT0 sample", "at NRST release", "latches Flash vs system mem", T.CYAN),
        ("SWD attach", "after BOOT0=0 path", "SWCLK must stay free", T.GREEN),
        ("Option bytes", "nBOOT0 / nSWBOOT0", "can override pin sample", T.AMBER),
        ("Fail look", "probe sees noise", "often boot latch, not cable", T.RED),
    ]
    for i, (t, a, b, col) in enumerate(rows):
        y = 120 + i * 100
        c.rect(40, y, 880, 88, fill=T.PANEL, stroke=col, rx=8)
        c.text(56, y + 28, t, size=16, fill=col, weight="700")
        c.text(320, y + 28, a, size=14, fill=T.TEXT, mono=True)
        c.text(56, y + 60, b, size=13, fill=T.MUTED)
    c.rect(40, 540, 880, 120, fill=T.BG2, stroke=T.GREEN, rx=8)
    c.text(56, 574, "Accept: after NRST, option/boot path = Flash; then SWD halt reads MSP at 0x08000000.", size=14, fill=T.GREEN, weight="700")
    c.text(56, 606, "F1 habit (BOOT0 strap only) is incomplete — read G0 nBOOT_SEL before rewiring.", size=13, fill=T.TEXT)
    c.text(56, 636, "Pairs with g0-boot-swd animation and sample-23-boot-latch.", size=13, fill=T.MUTED)
    c.rect(40, 680, 880, 80, fill=T.PANEL, stroke=T.RED, rx=8)
    c.text(56, 714, "Trap: force SWCLK while BOOT0 still samples high → 'ST-Link not found' false lead.", size=14, fill=T.RED, weight="700")
    credit(c, "Hand-drawn. G0 boot-vs-SWD order for LQFP64 labs.")
    return c


def ch23_f1_copy_traps() -> Svg:
    c = Svg(960, 880, "Copying F1 pin code onto G0", "Table 12/13/14 beats F103 muscle memory")
    c.header(tag="23", tag_color=T.AMBER)
    c.text(40, 86, "Same peripheral name ≠ same pin. Remap bits and default AF changed.", size=15, fill=T.TEXT, weight="700")
    traps = [
        ("USART1 TX", "F1 PA9", "G0 check AF table", "often PA9 still, verify AF1"),
        ("I2C1 SCL", "F1 PB6", "G0 may need AF", "open-drain + pull-up still law"),
        ("SPI1 SCK", "F1 PA5", "G0 AF select", "do not inherit F1 remap bit"),
        ("SWD pins", "F1 34/37", "G0 package map", "read DS pinout, not BluePill silk"),
    ]
    for i, (p, f1, g0, note) in enumerate(traps):
        y = 120 + i * 110
        c.rect(40, y, 880, 98, fill=T.PANEL, stroke=T.STROKE, rx=8)
        c.text(56, y + 28, p, size=16, fill=T.CYAN, weight="700", mono=True)
        c.text(280, y + 28, f1, size=13, fill=T.MUTED, mono=True)
        c.text(520, y + 28, g0, size=13, fill=T.AMBER, mono=True)
        c.text(56, y + 64, note, size=13, fill=T.TEXT)
    c.rect(40, 580, 880, 120, fill=T.BG2, stroke=T.VIOLET, rx=8)
    c.text(56, 614, "Method: DS pinout table → RM AF column → one scope of idle level before code blame.", size=14, fill=T.VIOLET, weight="700")
    c.text(56, 646, "sample-23-f1-g0-compare stays the overview; this plate is the copy-paste checklist.", size=13, fill=T.MUTED)
    credit(c, "Hand-drawn. F1→G0 pin copy traps.")
    return c


def ch24_stop2_retain() -> Svg:
    c = Svg(960, 880, "Stop 2 retention map", "What survives sleep on L4")
    c.header(tag="24", tag_color=T.CYAN)
    c.text(40, 86, "Stop 2 is not 'RAM forever'. Know which banks and peripherals keep state.", size=15, fill=T.TEXT, weight="700")
    cols = [
        ("Kept", "SRAM2 (if selected)", "RTC / backup", "some GPIO latches", T.GREEN),
        ("Lost / gated", "most clocks", "HSI/HSE off path", "peripheral run state", T.AMBER),
        ("Must redo", "PLL / SYSCLK", "UART baud divisors", "DMA stream arming", T.RED),
    ]
    for i, (t, a, b, d, col) in enumerate(cols):
        x = 40 + i * 300
        c.rect(x, 120, 280, 260, fill=T.PANEL, stroke=col, rx=8)
        c.text(x + 140, 156, t, size=18, anchor="middle", fill=col, weight="700")
        c.text(x + 140, 210, a, size=13, anchor="middle", fill=T.TEXT)
        c.text(x + 140, 250, b, size=13, anchor="middle", fill=T.TEXT)
        c.text(x + 140, 290, d, size=13, anchor="middle", fill=T.MUTED)
    c.rect(40, 420, 880, 140, fill=T.BG2, stroke=T.CYAN, rx=8)
    c.text(56, 454, "Wake evidence: EXTI/RTC flag → restore clock tree → re-init comms → then app work.", size=14, fill=T.CYAN, weight="700")
    c.text(56, 486, "JP6 IDD path measures MCU only — do not average two DMM snapshots as 'Stop current'.", size=13, fill=T.TEXT)
    c.text(56, 518, "Pairs with l4-stop2-evidence and sample-24-wake-triage.", size=13, fill=T.MUTED)
    c.rect(40, 590, 880, 110, fill=T.PANEL, stroke=T.RED, rx=8)
    c.text(56, 624, "Trap: print over UART immediately after wake before HSI/PLL ready → framing garbage.", size=14, fill=T.RED, weight="700")
    c.text(56, 656, "Fix: gate logs on 'clock restore done' flag from the four evidence checks.", size=13, fill=T.MUTED)
    credit(c, "Hand-drawn. L4 Stop2 retain vs restore map.")
    return c


def ch24_idd_jp6() -> Svg:
    c = Svg(960, 880, "Nucleo IDD / JP6 boundary", "Integral of current, not two averages")
    c.header(tag="24", tag_color=T.GREEN)
    c.text(40, 86, "JP6 opens the MCU IDD path. ST-Link / target VDD mix will fake your Stop numbers.", size=15, fill=T.TEXT, weight="700")
    steps = [
        ("1 Open JP6", "series sense on MCU VDD", T.CYAN),
        ("2 Scope / meter", "integrate I(t)·dt over sleep", T.GREEN),
        ("3 Report", "mode, VDD, wake source, uAh", T.AMBER),
        ("4 Compare", "same board, same firmware tag", T.VIOLET),
    ]
    for i, (t, n, col) in enumerate(steps):
        x = 40 + (i % 2) * 460
        y = 120 + (i // 2) * 150
        c.rect(x, y, 440, 130, fill=T.PANEL, stroke=col, rx=8)
        c.text(x + 24, y + 40, t, size=17, fill=col, weight="700")
        c.text(x + 24, y + 80, n, size=14, fill=T.TEXT)
    c.rect(40, 440, 880, 130, fill=T.BG2, stroke=T.GREEN, rx=8)
    c.text(56, 474, "Accept sheet: Stop2 uA @ 3.3 V, wake=RTC, restore clocks < N ms, UART OK after restore.", size=14, fill=T.GREEN, weight="700")
    c.text(56, 506, "l4-idd-bench holds the worksheet; this plate is the measurement boundary.", size=13, fill=T.MUTED)
    c.rect(40, 600, 880, 100, fill=T.PANEL, stroke=T.RED, rx=8)
    c.text(56, 634, "Trap: USB powered ST-Link feeding target while claiming 'battery Stop current'.", size=14, fill=T.RED, weight="700")
    c.text(56, 666, "Remove ST-Link power path or power from the same rail you measure.", size=13, fill=T.MUTED)
    credit(c, "Hand-drawn. Nucleo JP6 IDD measurement boundary.")
    return c


def ch25_voltage_scale() -> Svg:
    c = Svg(960, 880, "H7 VOS before 480 MHz", "Power domain + scale gate the PLL")
    c.header(tag="25", tag_color=T.AMBER)
    c.text(40, 86, "Do not chase 480 MHz until VOS / LDO-SMPS choice matches the DS table.", size=15, fill=T.TEXT, weight="700")
    rows = [
        ("Pick supply", "LDO vs SMPS path", "board design locks this", T.CYAN),
        ("Set VOS", "scale for target f", "wait VOSRDY", T.GREEN),
        ("Enable HSE", "8 MHz typical Nucleo", "CSS optional later", T.AMBER),
        ("PLL1 → SYS", "to 480 MHz if allowed", "then bus dividers", T.VIOLET),
    ]
    for i, (t, a, b, col) in enumerate(rows):
        y = 120 + i * 100
        c.rect(40, y, 880, 88, fill=T.PANEL, stroke=col, rx=8)
        c.text(56, y + 28, f"{i+1}. {t}", size=16, fill=col, weight="700")
        c.text(320, y + 28, a, size=14, fill=T.TEXT, mono=True)
        c.text(56, y + 60, b, size=13, fill=T.MUTED)
    c.rect(40, 540, 880, 120, fill=T.BG2, stroke=T.GREEN, rx=8)
    c.text(56, 574, "Evidence triad after boot: SystemCoreClock, a timer tick, and one peripheral clock gate.", size=14, fill=T.GREEN, weight="700")
    c.text(56, 606, "h7-clock-chain animates the multiply; this plate is the voltage gate before PLL.", size=13, fill=T.MUTED)
    c.rect(40, 680, 880, 80, fill=T.PANEL, stroke=T.RED, rx=8)
    c.text(56, 714, "Trap: CubeMX 480 MHz profile on a board stuck in wrong VOS → random HardFaults.", size=14, fill=T.RED, weight="700")
    credit(c, "Hand-drawn. H7 voltage-scale gate before 480 MHz.")
    return c


def ch25_dcache_dma() -> Svg:
    c = Svg(960, 880, "H7 D-Cache vs DMA ownership", "CPU view and DMA view are not the same buffer")
    c.header(tag="25", tag_color=T.VIOLET)
    c.text(40, 86, "Ethernet / MDMA / DMA see physical memory. D-Cache can hide stores until clean.", size=15, fill=T.TEXT, weight="700")
    dirs = [
        ("CPU → DMA", "clean D-Cache line", "before start", "TX descriptors / payloads", T.CYAN),
        ("DMA → CPU", "invalidate before read", "after complete", "RX buffers / status", T.GREEN),
        ("Link script", "non-cacheable region", "or MPU window", "descriptors often here", T.AMBER),
        ("Ownership", "pbuf / driver", "one writer rule", "not 'share and hope'", T.RED),
    ]
    for i, (t, a, b, d, col) in enumerate(dirs):
        y = 120 + i * 110
        c.rect(40, y, 880, 98, fill=T.PANEL, stroke=col, rx=8)
        c.text(56, y + 28, t, size=16, fill=col, weight="700")
        c.text(280, y + 28, a, size=13, fill=T.TEXT, mono=True)
        c.text(560, y + 28, b, size=13, fill=T.MUTED, mono=True)
        c.text(56, y + 64, d, size=13, fill=T.TEXT)
    c.rect(40, 580, 880, 120, fill=T.BG2, stroke=T.VIOLET, rx=8)
    c.text(56, 614, "Accept: loopback or known pattern survives cache on + cache off builds.", size=14, fill=T.VIOLET, weight="700")
    c.text(56, 646, "network-cache-ownership is the overview; this plate is the clean/invalidate direction.", size=13, fill=T.MUTED)
    credit(c, "Hand-drawn. H7 D-Cache maintain directions for DMA.")
    return c


def ch26_file_matrix() -> Svg:
    c = Svg(960, 880, "SPL project file matrix", "Missing one .c → link error that looks like 'API vanished'")
    c.header(tag="26", tag_color=T.CYAN)
    c.text(40, 86, "SPL is a bag of drivers. The linker only sees what you add to the build.", size=15, fill=T.TEXT, weight="700")
    rows = [
        ("Always", "system_stm32f10x.c", "startup_*.s", "core + reset"),
        ("GPIO lab", "stm32f10x_gpio.c", "stm32f10x_rcc.c", "clock + pin"),
        ("USART", "+ stm32f10x_usart.c", "misc.c if NVIC", "IRQ via misc"),
        ("DMA", "+ stm32f10x_dma.c", "pair with peri .c", "no auto bind"),
    ]
    for i, (t, a, b, d) in enumerate(rows):
        y = 120 + i * 100
        c.rect(40, y, 880, 88, fill=T.PANEL, stroke=T.STROKE, rx=8)
        c.text(56, y + 28, t, size=16, fill=T.CYAN, weight="700")
        c.text(220, y + 28, a, size=13, fill=T.TEXT, mono=True)
        c.text(520, y + 28, b, size=13, fill=T.TEXT, mono=True)
        c.text(56, y + 60, d, size=13, fill=T.MUTED)
    c.rect(40, 540, 880, 120, fill=T.BG2, stroke=T.AMBER, rx=8)
    c.text(56, 574, "Macros: USE_STDPERIPH_DRIVER and the right STM32F10X_MD/HD — assert_param needs them.", size=14, fill=T.AMBER, weight="700")
    c.text(56, 606, "assert_param is not a product fault path; keep it on in lab builds.", size=13, fill=T.MUTED)
    c.rect(40, 680, 880, 80, fill=T.PANEL, stroke=T.RED, rx=8)
    c.text(56, 714, "Trap: header visible, .c omitted → 'undefined reference' blamed on 'SPL dead'.", size=14, fill=T.RED, weight="700")
    credit(c, "Hand-drawn. SPL file matrix for F103 labs.")
    return c


def ch26_timeout_poll() -> Svg:
    c = Svg(960, 880, "SPL poll must carry a timeout", "No HAL timeout helper — you own the loop")
    c.header(tag="26", tag_color=T.AMBER)
    c.text(40, 86, "Flag wait without a bound hangs the board. Bound it, then classify the failure.", size=15, fill=T.TEXT, weight="700")
    steps = [
        ("Arm", "clear status bits you care about", T.CYAN),
        ("Wait", "spin with decrement / DWT cycle", T.GREEN),
        ("Pass", "bit set in budget → continue", T.AMBER),
        ("Fail", "budget 0 → return code / LED", T.RED),
    ]
    for i, (t, n, col) in enumerate(steps):
        x = 40 + i * 230
        c.rect(x, 130, 210, 180, fill=T.PANEL, stroke=col, rx=8)
        c.text(x + 105, 170, t, size=18, anchor="middle", fill=col, weight="700")
        c.text(x + 105, 230, n, size=13, anchor="middle", fill=T.TEXT)
        if i < 3:
            c.arrow(x + 214, 220, x + 226, 220, color=T.STROKE, sw=2)
    c.rect(40, 360, 880, 160, fill=T.BG2, stroke=T.GREEN, rx=8)
    c.text(56, 394, "Pattern: while (!flag) { if (--t == 0) return TIMEOUT; }", size=14, fill=T.GREEN, weight="700", mono=True)
    c.text(56, 430, "Log which flag timed out (TXE vs TC vs RXNE) — same function, different wires.", size=13, fill=T.TEXT)
    c.text(56, 462, "Pairs with sample-26-spl-hal-compare for API mapping.", size=13, fill=T.MUTED)
    c.rect(40, 560, 880, 140, fill=T.PANEL, stroke=T.RED, rx=8)
    c.text(56, 594, "Trap: copy HAL examples' infinite waits into SPL drivers 'temporarily'.", size=14, fill=T.RED, weight="700")
    c.text(56, 626, "They ship. Field units wedge on a noisy line with no breadcrumb.", size=13, fill=T.MUTED)
    c.text(56, 658, "Also: misc.c NVIC config is explicit — no HAL_UART_IRQHandler dispatcher.", size=13, fill=T.MUTED)
    credit(c, "Hand-drawn. SPL timeout-poll ownership.")
    return c


def ch27_rmii_checklist() -> Svg:
    c = Svg(960, 880, "RMII bring-up checklist", "Link LED is a clue, not an accept test")
    c.header(tag="27", tag_color=T.CYAN)
    c.text(40, 86, "MAC ↔ PHY wiring must match RMII before lwIP ever sees a packet.", size=15, fill=T.TEXT, weight="700")
    pins = [
        ("REF_CLK", "50 MHz", "from PHY or MCU", T.CYAN),
        ("TXD[1:0] + TX_EN", "MCU → PHY", "direction fixed", T.GREEN),
        ("RXD[1:0] + CRS_DV", "PHY → MCU", "no RX_ER in RMII", T.AMBER),
        ("MDC / MDIO", "mgmt", "PHY address strap", T.VIOLET),
    ]
    for i, (t, a, b, col) in enumerate(pins):
        y = 120 + i * 100
        c.rect(40, y, 880, 88, fill=T.PANEL, stroke=col, rx=8)
        c.text(56, y + 28, t, size=16, fill=col, weight="700", mono=True)
        c.text(360, y + 28, a, size=14, fill=T.TEXT, mono=True)
        c.text(56, y + 60, b, size=13, fill=T.MUTED)
    c.rect(40, 540, 880, 120, fill=T.BG2, stroke=T.GREEN, rx=8)
    c.text(56, 574, "Accept: MDIO read PHY ID + link bit; then DHCP/static; ping with known MAC.", size=14, fill=T.GREEN, weight="700")
    c.text(56, 606, "Green LED alone can mean partner link while MAC clocks are wrong.", size=13, fill=T.MUTED)
    c.rect(40, 680, 880, 80, fill=T.PANEL, stroke=T.RED, rx=8)
    c.text(56, 714, "Trap: CubeMX RMII pins remapped after PCB silk was frozen to another AF.", size=14, fill=T.RED, weight="700")
    credit(c, "Hand-drawn. RMII signal checklist before stack bring-up.")
    return c


def ch27_tcp_framing() -> Svg:
    c = Svg(960, 880, "TCP is a byte stream", "You invent message boundaries")
    c.header(tag="27", tag_color=T.AMBER)
    c.text(40, 86, "recv() returning N bytes is not 'one protocol message'. Frame it yourself.", size=15, fill=T.TEXT, weight="700")
    ways = [
        ("Length prefix", "u16/u32 BE/LE", "simple, watch endian", T.CYAN),
        ("Delimiter", "newline / 0x00", "escaping cost", T.GREEN),
        ("TLV", "type+len+value", "extensible", T.AMBER),
        ("MQTT etc.", "library frames", "still buffer partials", T.VIOLET),
    ]
    for i, (t, a, b, col) in enumerate(ways):
        x = 40 + (i % 2) * 460
        y = 120 + (i // 2) * 150
        c.rect(x, y, 440, 130, fill=T.PANEL, stroke=col, rx=8)
        c.text(x + 24, y + 40, t, size=17, fill=col, weight="700")
        c.text(x + 24, y + 74, a, size=14, fill=T.TEXT, mono=True)
        c.text(x + 24, y + 104, b, size=13, fill=T.MUTED)
    c.rect(40, 440, 880, 140, fill=T.BG2, stroke=T.AMBER, rx=8)
    c.text(56, 474, "State machine: accumulate → parse header → wait body → dispatch → repeat.", size=14, fill=T.AMBER, weight="700")
    c.text(56, 506, "UDP keeps datagram edges; TCP does not. MQTT QoS ≠ business exactly-once.", size=13, fill=T.TEXT)
    c.text(56, 538, "Pairs with tcp-byte-stream diagram.", size=13, fill=T.MUTED)
    c.rect(40, 610, 880, 100, fill=T.PANEL, stroke=T.RED, rx=8)
    c.text(56, 644, "Trap: assume one recv = one JSON object; ship parsers that wedge on partials.", size=14, fill=T.RED, weight="700")
    c.text(56, 676, "Fuzz with 1-byte reads in lab before field MTU surprises you.", size=13, fill=T.MUTED)
    credit(c, "Hand-drawn. TCP framing ownership.")
    return c


def ch28_four_concepts() -> Svg:
    c = Svg(960, 880, "Four execution concepts", "Bare metal ≠ superloop ≠ RTOS ≠ rich OS")
    c.header(tag="28", tag_color=T.CYAN)
    c.text(40, 86, "Pick the model that matches deadlines and ownership — not the trend name.", size=15, fill=T.TEXT, weight="700")
    cards = [
        ("Bare metal", "IRQ + main flags", "smallest, clearest", "tight ISR budgets", T.CYAN),
        ("Superloop", "poll + timers", "easy until fan-out", "watch blocking calls", T.GREEN),
        ("RTOS", "tasks + IPC", "deadlines via design", "not magic priority", T.AMBER),
        ("Rich OS", "Linux / Zephyr full", "drivers + MMU story", "different evidence", T.VIOLET),
    ]
    for i, (t, a, b, d, col) in enumerate(cards):
        x = 40 + (i % 2) * 460
        y = 120 + (i // 2) * 180
        c.rect(x, y, 440, 160, fill=T.PANEL, stroke=col, rx=8)
        c.text(x + 24, y + 36, t, size=18, fill=col, weight="700")
        c.text(x + 24, y + 70, a, size=14, fill=T.TEXT, mono=True)
        c.text(x + 24, y + 100, b, size=13, fill=T.TEXT)
        c.text(x + 24, y + 130, d, size=13, fill=T.MUTED)
    c.rect(40, 500, 880, 140, fill=T.BG2, stroke=T.GREEN, rx=8)
    c.text(56, 534, "Owner task pattern: one writer for a resource beats sprinkling mutexes everywhere.", size=14, fill=T.GREEN, weight="700")
    c.text(56, 566, "sample-28-os-compare is the catalog; this plate forces the four-way split first.", size=13, fill=T.MUTED)
    c.rect(40, 670, 880, 80, fill=T.PANEL, stroke=T.RED, rx=8)
    c.text(56, 704, "Trap: 'we added FreeRTOS' as a substitute for measuring period/timeout/deadline.", size=14, fill=T.RED, weight="700")
    credit(c, "Hand-drawn. Four execution concepts before RTOS shopping.")
    return c


def ch28_three_times() -> Svg:
    c = Svg(960, 880, "Period · timeout · deadline", "Three clocks that are not synonyms")
    c.header(tag="28", tag_color=T.AMBER)
    c.text(40, 86, "Real-time is a budget. Name which clock you are proving.", size=15, fill=T.TEXT, weight="700")
    cols = [
        ("Period", "how often work starts", "tick / timer / sensor", "miss → jitter", T.CYAN),
        ("Timeout", "how long you wait", "queue / bus / mutex", "miss → error path", T.GREEN),
        ("Deadline", "when result must exist", "control loop / UI", "miss → hazard", T.RED),
    ]
    for i, (t, a, b, d, col) in enumerate(cols):
        x = 40 + i * 300
        c.rect(x, 120, 280, 280, fill=T.PANEL, stroke=col, rx=8)
        c.text(x + 140, 160, t, size=20, anchor="middle", fill=col, weight="700")
        c.text(x + 140, 220, a, size=13, anchor="middle", fill=T.TEXT)
        c.text(x + 140, 270, b, size=13, anchor="middle", fill=T.MUTED, mono=True)
        c.text(x + 140, 330, d, size=13, anchor="middle", fill=T.TEXT)
    c.rect(40, 440, 880, 140, fill=T.BG2, stroke=T.AMBER, rx=8)
    c.text(56, 474, "Measure with DWT / scope / logic — not with 'it feels smooth on the bench'.", size=14, fill=T.AMBER, weight="700")
    c.text(56, 506, "rtos-deadline-budget holds numbers; this plate keeps the vocabulary honest.", size=13, fill=T.MUTED)
    c.rect(40, 610, 880, 100, fill=T.PANEL, stroke=T.RED, rx=8)
    c.text(56, 644, "Trap: set task priority by politics; never write the deadline next to the period.", size=14, fill=T.RED, weight="700")
    c.text(56, 676, "Fix: one table — task, period, WCET, deadline, blocking calls.", size=13, fill=T.MUTED)
    credit(c, "Hand-drawn. Period vs timeout vs deadline.")
    return c


def f_six_facts() -> Svg:
    c = Svg(960, 880, "Six facts only source shows", "Appendix F — read the tree, not the README alone")
    c.header(tag="F", tag_color=T.VIOLET)
    c.text(40, 86, "Licenses, CMSIS IO types, port ASM, init order — none of that fits a tweet.", size=15, fill=T.TEXT, weight="700")
    facts = [
        ("1 Cube license", "ingredient list", "not one stew"),
        ("2 CMSIS __I/__O/__IO", "rights in the type", "volatile story"),
        ("3 libopencm3", "one header ≈ RM", "manual translation"),
        ("4 FreeRTOS switch", "in the port", "not tasks.c myth"),
        ("5 RT-Thread init", "spine numbers", "ordered bring-up"),
        ("6 Archived ≠ mirror", "read-only still moves", "pin a commit"),
    ]
    for i, (t, a, b) in enumerate(facts):
        x = 40 + (i % 3) * 300
        y = 120 + (i // 3) * 200
        c.rect(x, y, 280, 170, fill=T.PANEL, stroke=T.STROKE, rx=8)
        c.text(x + 20, y + 40, t, size=15, fill=T.VIOLET, weight="700")
        c.text(x + 20, y + 80, a, size=14, fill=T.TEXT)
        c.text(x + 20, y + 120, b, size=13, fill=T.MUTED)
    c.rect(40, 560, 880, 140, fill=T.BG2, stroke=T.GREEN, rx=8)
    c.text(56, 594, "Method: clone → find the file → quote the line in your lab notes.", size=14, fill=T.GREEN, weight="700")
    c.text(56, 626, "sample-f-oss-map is the repo map; this plate is the six reading targets.", size=13, fill=T.MUTED)
    credit(c, "Hand-drawn. Appendix F six source-reading facts.")
    return c


def f_ask_before() -> Svg:
    c = Svg(960, 880, "Five steps before you ask", "Community hygiene for STM32 / RTOS channels")
    c.header(tag="F", tag_color=T.GREEN)
    c.text(40, 86, "A good question already contains chip, clock, wiring, and a failing accept test.", size=15, fill=T.TEXT, weight="700")
    steps = [
        ("1 Reproduce", "minimal project", "one peripheral"),
        ("2 Measure", "scope / SWD", "numbers not vibes"),
        ("3 Search", "errata + issues", "exact register names"),
        ("4 Package", "MCU, board, tool", "commit / Cube ver"),
        ("5 Ask", "expected vs got", "attach the accept log"),
    ]
    for i, (t, a, b) in enumerate(steps):
        y = 120 + i * 90
        c.rect(40, y, 880, 78, fill=T.PANEL, stroke=T.STROKE, rx=8)
        c.text(56, y + 28, t, size=16, fill=T.GREEN, weight="700")
        c.text(280, y + 28, a, size=14, fill=T.TEXT)
        c.text(560, y + 28, b, size=14, fill=T.MUTED)
    c.rect(40, 590, 880, 110, fill=T.BG2, stroke=T.CYAN, rx=8)
    c.text(56, 624, "Template: chip + package, clock tree, pin table row, failing command, expected byte.", size=14, fill=T.CYAN, weight="700")
    c.text(56, 656, "Skip 'urgent' — attach the evidence instead.", size=13, fill=T.MUTED)
    credit(c, "Hand-drawn. Appendix F ask-before checklist.")
    return c


FIGURES = [
    ("sample-23-boot0-swclk.svg", ch23_boot0_swclk),
    ("sample-23-f1-copy-traps.svg", ch23_f1_copy_traps),
    ("sample-24-stop2-retain.svg", ch24_stop2_retain),
    ("sample-24-idd-jp6.svg", ch24_idd_jp6),
    ("sample-25-voltage-scale.svg", ch25_voltage_scale),
    ("sample-25-dcache-dma.svg", ch25_dcache_dma),
    ("sample-26-file-matrix.svg", ch26_file_matrix),
    ("sample-26-timeout-poll.svg", ch26_timeout_poll),
    ("sample-27-rmii-checklist.svg", ch27_rmii_checklist),
    ("sample-27-tcp-framing.svg", ch27_tcp_framing),
    ("sample-28-four-concepts.svg", ch28_four_concepts),
    ("sample-28-three-times.svg", ch28_three_times),
    ("sample-f-six-facts.svg", f_six_facts),
    ("sample-f-ask-before.svg", f_ask_before),
]


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    for name, fn in FIGURES:
        svg = fn()
        path = os.path.join(OUT, name)
        svg.save(path)
        audit_static(name, path)


if __name__ == "__main__":
    main()

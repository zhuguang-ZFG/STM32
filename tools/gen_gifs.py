#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成 assets/gif/*.gif —— 纯 Python 渲染的光栅动画（零依赖）。

为什么 GIF 里是英文：内置点阵字体只覆盖 5×7 ASCII。
中文讲解放在对应的 SVG 动画与文档里。

用法::

    python3 tools/gen_gifs.py            # 生成全部
    python3 tools/gen_gifs.py led-blink  # 只生成一个
    python3 tools/check_assets.py        # 解码回来逐像素校验
"""

from __future__ import annotations

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "assets", "gif")
sys.path.insert(0, HERE)

from minigfx import C, Canvas, Gif, dim, mix  # noqa: E402

W, H = 480, 300


def chrome(c, title, tag="", note=""):
    c.header(title, tag)
    if note:
        c.footer(note)


# --------------------------------------------------------------------------- LED 闪烁


def led_blink():
    """1 Hz：24 帧 × 4 cs ≈ 0.96 s。电流是估算，不是实测。"""
    g = Gif(W, H, delay=4)
    frames = 24
    for i in range(frames):
        on = i < frames // 2
        c = Canvas(W, H)
        chrome(c, "GPIO BLINK", "PA5",
               "1 Hz  HIGH 500 ms + LOW 500 ms")
        c.panel(16, 42, 448, 100, C.PANEL, C.STROKE)
        c.chip(30, 58, 90, 48, "STM32", C.PANEL2, C.CYAN, C.CYAN)
        c.text("PA5", 46, 92, C.MUTED, 1)
        c.line(120, 82, 150, 82, C.AMBER, 2)
        c.panel(150, 73, 34, 18, C.BG2, C.AMBER)
        c.text("330", 155, 79, C.AMBER, 1)
        c.line(184, 82, 206, 82, C.AMBER, 2)
        c.led(220, 82, 11, C.RED, on)
        c.line(232, 82, 300, 82, C.AMBER, 2)
        c.line(300, 82, 300, 112, C.MUTED, 2)
        c.line(288, 112, 312, 112, C.MUTED, 2)
        c.text("GND", 318, 108, C.MUTED, 1)
        c.text("LED ON" if on else "LED OFF", 336, 58,
               C.GREEN if on else C.DIM, 1)
        c.text("EST (3.3-2.0)/330", 336, 76, C.DIM, 1)
        c.text("= 3.9mA  NOT LAB", 336, 90, C.DIM, 1)
        c.text("PC13 = ACTIVE-LOW", 336, 108, C.AMBER, 1)
        c.text("PA5 LEVEL  1 Hz", 16, 156, C.MUTED, 1)
        c.hline(16, 198, 448, C.STROKE)
        c.hline(16, 164, 448, C.GRID)
        bits = [1] * 4 + [0] * 4
        c.waveform(16, 168, 448, 40, bits, C.GREEN, 2)
        px = 16 + int(448 * i / frames)
        c.vline(px, 164, 34, C.RED, 1)
        c.circle(px, 168 if on else 200, 3, C.RED)
        c.text("500 ms HIGH + 500 ms LOW", 16, 214, C.DIM, 1)
        c.text("TOGGLE WITH BSRR, NOT ODR", 16, 230, C.DIM, 1)
        c.text("PA5 HIGH-SIDE. BLUEPILL LED IS PC13", 16, 246, C.DIM, 1)
        g.add(c)
    return g


# --------------------------------------------------------------------------- PWM 呼吸灯


def pwm_breath():
    """PWM 占空比从 5% 变到 95%：波形、亮度、数值三者同步。"""
    g = Gif(W, H, delay=7)
    frames = 30
    for i in range(frames):
        t = i / (frames - 1)
        duty = 0.05 + 0.9 * (0.5 - 0.5 * math.cos(2 * math.pi * t))
        c = Canvas(W, H)
        chrome(c, "PWM BREATH", "TIM3 CH1",
               "f = 72MHz/((PSC+1)*(ARR+1))  DUTY=CCR/(ARR+1)")
        # LED 亮度
        c.panel(16, 42, 200, 108, C.PANEL, C.STROKE)
        c.led(80, 96, 22, mix(dim(C.RED, 0.25), C.RED, duty), True)
        ccr = int(round(duty * 1000))
        c.text_c(f"DUTY {int(round(duty * 100)):2d}%", 116, 76, C.AMBER, 1)
        c.text_c(f"CCR = {ccr}", 116, 96, C.MUTED, 1)
        c.text_c("ARR=999 PSC=0", 116, 116, C.MUTED, 1)
        c.text_c("f = 72 kHz", 116, 134, C.DIM, 1)
        # 占空比条
        c.panel(232, 42, 232, 108, C.PANEL, C.STROKE)
        c.text("CCR", 246, 58, C.MUTED, 1)
        c.panel(276, 52, 174, 16, C.BG2, C.STROKE)
        c.fill_rect(277, 53, int(172 * duty), 14, C.AMBER)
        c.text("0", 276, 74, C.DIM, 1)
        c.text("ARR", 424, 74, C.DIM, 1)
        c.hline(276, 88, 174, C.STROKE)
        c.circle(276 + int(172 * ((i * 3 % 30) / 30)), 88, 3, C.CYAN)
        c.text("CNT < CCR -> HIGH", 246, 104, C.GREEN, 1)
        c.text("CNT >= CCR -> LOW", 246, 118, C.RED, 1)
        c.text("UPDATE  EVENT  LOADS  CCR", 246, 134, C.DIM, 1)
        # PWM 波形
        c.text("TIM3_CH1 OUTPUT", 16, 166, C.MUTED, 1)
        c.hline(16, 214, 448, C.STROKE)
        period = 64
        x = 16
        while x < 464:
            hi = max(2, int(period * duty))
            c.line(x, 186, x, 214, C.CYAN, 2)
            c.line(x, 186, x + hi, 186, C.CYAN, 2)
            c.line(x + hi, 186, x + hi, 214, C.CYAN, 2)
            c.line(x + hi, 214, x + period, 214, C.CYAN, 2)
            x += period
        c.text("ONE PERIOD", 16, 226, C.DIM, 1)
        c.text("BRIGHTER = LONGER HIGH TIME = LARGER CCR", 16, 244, C.DIM, 1)
        g.add(c)
    return g


# --------------------------------------------------------------------------- I2C 时序


def _i2c_cell(kind, bit):
    """返回 (t, scl, sda)，t 为格内 0..1。数据位在 SCL 低时换电平。"""
    if kind == "ST":
        return [(0.00, 1, 1), (0.36, 1, 1), (0.36, 1, 0),
                (0.72, 1, 0), (0.72, 0, 0), (1.00, 0, 0)]
    if kind == "SP":
        return [(0.00, 0, 0), (0.28, 0, 0), (0.28, 1, 0),
                (0.58, 1, 0), (0.58, 1, 1), (1.00, 1, 1)]
    b = 1 if bit else 0
    return [(0.00, 0, b), (0.30, 0, b), (0.30, 1, b),
            (0.70, 1, b), (0.70, 0, b), (1.00, 0, b)]


def i2c_timing():
    """写 0x3C 的 0xA5：7 位地址 0111100，SDA 不在 SCL 上升沿翻转。"""
    g = Gif(W, H, delay=10)
    addr = (0, 1, 1, 1, 1, 0, 0)          # 0x3C，不是 0x1E
    data = (1, 0, 1, 0, 0, 1, 0, 1)       # 0xA5，MSB 先发
    cells = ([("ST", 0)] + [("BIT", b) for b in addr] + [("BIT", 0), ("BIT", 0)]
             + [("BIT", b) for b in data] + [("BIT", 0), ("SP", 0)])
    phases = [(0, 1, "ST"), (1, 8, "0x3C"), (8, 9, "W"),
              (9, 10, "AK"), (10, 18, "0xA5"), (18, 19, "AK"),
              (19, 20, "SP")]
    tips = [
        "START: SDA FALLS WHILE SCL STAYS HIGH",
        "0x3C = 0111100   MSB FIRST ON I2C",
        "R/W = 0 IS WRITE. NEXT CLOCK IS ACK",
        "ACK = 9TH CLOCK, SLAVE PULLS SDA LOW",
        "DATA 0xA5 = 10100101  MSB FIRST",
        "EACH BYTE HAS ITS OWN ACK CLOCK",
        "STOP: SDA RISES WHILE SCL STAYS HIGH",
    ]
    x0, pw = 18, 22
    total = len(phases)
    for f in range(total):
        c = Canvas(W, H)
        chrome(c, "I2C WRITE", "400 kHz",
               "SDA CHANGES WHILE SCL IS LOW")
        a, b, name = phases[f]
        for i, (ga, gb, gname) in enumerate(phases):
            x = x0 + ga * pw
            w = (gb - ga) * pw
            cur = i == f
            c.hline(x, 50, w - 2, C.GREEN if cur else C.STROKE, 2)
            c.text_c(gname, x + w / 2, 36, C.GREEN if cur else C.MUTED, 1)
        scl, sda = [], []
        for n, (kind, bit) in enumerate(cells):
            for t, sv, dv in _i2c_cell(kind, bit):
                xx = x0 + (n + t) * pw
                scl.append((xx, 78 if sv else 102))
                sda.append((xx, 128 if dv else 152))
        def stroke(pts, color, dim_color):
            for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
                mid = (x1 + x2) / 2
                on = x0 + a * pw <= mid < x0 + b * pw
                c.line(x1, y1, x2, y2, color if on else dim_color, 2)
        c.text("SCL", 18, 64, C.CYAN, 1)
        c.text("SDA", 18, 114, C.AMBER, 1)
        stroke(scl, C.CYAN, dim(C.CYAN, 0.35))
        stroke(sda, C.AMBER, dim(C.AMBER, 0.35))
        c.rect(x0 + a * pw, 70, (b - a) * pw, 90, C.GREEN, 1)
        c.text(f"{f + 1}/{total}  {name}", 18, 176, C.GREEN, 1)
        c.text(tips[f], 18, 194, C.TEXT, 1)
        c.text("7-BIT ADDR 0x3C. HAL WANTS 0x78", 18, 216, C.CYAN, 1)
        c.text("DATA BIT CHANGES ONLY IN SCL LOW", 18, 234, C.DIM, 1)
        c.text("STUCK BUS: 9 CLOCKS, THEN STOP", 18, 252, C.DIM, 1)
        g.add(c)
    return g



# --------------------------------------------------------------------------- UART 帧


def uart_bits():
    """逐位发送：10 个位格依次高亮，波形同步生长。"""
    g = Gif(W, H, delay=9)
    data = [1, 0, 1, 0, 0, 1, 0, 1]           # 0xA5，LSB 先发
    bits = [0] + data + [1]                    # 起始位 0、8 数据位、停止位 1
    labels = ["ST"] + [str(i) for i in range(8)] + ["SP"]
    total = len(bits) + 1                      # 开头留一帧空闲
    for f in range(total):
        step = f - 1                            # -1 = 空闲
        c = Canvas(W, H)
        chrome(c, "UART 0xA5", "8N1 LSB",
               "10 BITS x 8.68 us = 86.8 us")
        x0, cw = 24, 43
        for i in range(10):
            x = x0 + i * cw
            cur = (i == step)
            c.panel(x, 46, cw - 4, 34, C.PANEL2 if cur else C.PANEL,
                    C.CYAN if cur else C.STROKE)
            c.text_c(labels[i], x + (cw - 4) / 2, 56, C.MUTED, 1)
            c.text_c(str(bits[i]), x + (cw - 4) / 2, 68,
                     C.GREEN if bits[i] else C.RED, 1)
        c.text("IDLE = HIGH", 24, 92, C.DIM, 1)
        c.text("TX LINE", 24, 110, C.MUTED, 1)
        c.hline(24, 186, 432, C.STROKE)
        c.hline(24, 128, 432, C.GRID)
        show = bits[:step + 1] if step >= 0 else []
        if show:
            c.waveform(24, 132, 432 * len(show) / 10, 50, show, C.CYAN, 2)
        c.vline(24 + cw * (step + 1), 124, 62, C.AMBER, 1)
        if step < 0:
            c.text("LINE IDLE: WAITING FOR START BIT", 24, 206, C.TEXT, 1)
        else:
            c.text(f"BIT {labels[step]} = {bits[step]}", 24, 206, C.TEXT, 1)
            c.text("8.68 us" if step else "START: HIGH TO LOW", 220, 206,
                   C.AMBER, 1)
        c.text("0xA5 LSB FIRST  (SPI IS MSB FIRST)", 24, 226, C.MUTED, 1)
        c.text("SAMPLE AT BIT CENTER, OVERSAMPLE 16", 24, 242, C.DIM, 1)
        c.text("USARTDIV 39.0625 -> BRR 0x271", 24, 258, C.DIM, 1)
        g.add(c)
    return g


# --------------------------------------------------------------------------- DMA 环形缓冲


def dma_ring():
    """循环模式只覆盖正在写的那一格，旧数据留着。半字：4 个采样 = 8 字节。"""
    g = Gif(W, H, delay=7)
    lap0 = [2048, 2100, 2201, 2350, 2500, 2420, 2301, 2180]
    lap1 = [1900, 1800, 1700, 1600, 1750, 1900, 2000, 2100]
    frames = 16
    for f in range(frames):
        c = Canvas(W, H)
        slot = f % 8
        lap = f // 8
        chrome(c, "DMA CIRCULAR", "ADC1 CH1",
               "HT = 4 SAMPLES = 8 BYTES")
        c.chip(16, 48, 96, 40, "ADC1", C.PANEL2, C.AMBER, C.AMBER)
        c.text("CH0 PA0", 24, 96, C.MUTED, 1)
        c.panel(16, 108, 96, 52, C.PANEL, C.STROKE)
        c.text("DR", 24, 120, C.MUTED, 1)
        sample = (lap1 if lap else lap0)[slot]
        c.text_c(str(sample), 64, 138, C.AMBER, 1)
        c.chip(140, 70, 120, 40, "DMA1 CH1", C.PANEL2, C.CYAN, C.CYAN)
        c.text("CIRCULAR HALFWORD", 140, 122, C.MUTED, 1)
        c.text("F1 DMA IS ON AHB", 140, 136, C.MUTED, 1)
        c.text("BUF[8]", 300, 52, C.MUTED, 1)
        mark = "HT" if slot == 3 else ("TC" if slot == 7 else "")
        if mark:
            c.text(mark, 360, 52, C.GREEN, 1)
        for i in range(8):
            x = 300 + (i % 4) * 42
            y = 66 + (i // 4) * 34
            if lap == 0:
                shown = lap0[i] if i <= slot else None
            elif i <= slot:
                shown = lap1[i]
            else:
                shown = lap0[i]
            cur = i == slot
            c.panel(x, y, 38, 28, C.PANEL2 if shown is not None else C.PANEL,
                    C.CYAN if cur else C.STROKE)
            c.text_c(str(shown) if shown is not None else "----",
                     x + 19, y + 10, C.GREEN if shown is not None else C.DIM, 1)
        px = 112 + int(168 * slot / 7) if slot else 112
        c.circle(px, 90, 4, C.CYAN)
        c.panel(16, 176, 448, 78, C.PANEL, C.STROKE)
        busy = ["FILTER", "FFT", "PRINTF", "PID", "OLED", "CALC", "UART",
                "LOG"]
        c.text(f"CPU: {busy[slot]}", 28, 192, C.VIOLET, 1)
        c.text("OLD SLOTS STAY. ONLY THE CURSOR SLOT", 28, 210, C.MUTED, 1)
        c.text("IS OVERWRITTEN ON THE NEXT LAP", 28, 224, C.MUTED, 1)
        c.text("HALFWORD: 4 SAMPLES = 8 BYTES = HT", 28, 242, C.DIM, 1)
        g.add(c)
    return g



# --------------------------------------------------------------------------- SAR ADC


def sar_adc():
    """逐次逼近：试探位 = 已确定结果 | (1<<bit)，电压按 /4096。"""
    g = Gif(W, H, delay=10)
    vin = 2048
    result = 0
    for step in range(12):
        bit = 11 - step
        trial = result | (1 << bit)
        keep = trial <= vin
        result = trial if keep else result
        c = Canvas(W, H)
        chrome(c, "SAR ADC", "12 BIT",
               "1 LSB = VREF/4096  ERR +/-0.5 LSB")
        for i in range(12):
            b = 11 - i
            x = 20 + i * 37
            state = "done" if b > bit else ("test" if b == bit else "todo")
            stroke = C.AMBER if state == "test" else C.STROKE
            c.panel(x, 44, 33, 32, C.PANEL, stroke)
            c.text_c(str(b), x + 16, 50, C.MUTED, 1)
            if state == "todo":
                c.text_c("-", x + 16, 64, C.DIM, 1)
            else:
                bitv = (result >> b) & 1
                c.text_c(str(bitv), x + 16, 64,
                         C.GREEN if bitv else C.DIM, 1)
        c.panel(20, 88, 216, 100, C.PANEL, C.STROKE)
        c.text("TRIAL", 32, 102, C.MUTED, 1)
        c.text_c(str(trial), 128, 118, C.CYAN, 1)
        c.text(f"BIT {bit} SET ON RESULT", 32, 140, C.MUTED, 1)
        c.text("VIN = 2048", 32, 164, C.MUTED, 1)
        c.panel(248, 88, 216, 100, C.PANEL, C.STROKE)
        c.text("COMPARE", 260, 102, C.MUTED, 1)
        c.text_c("KEEP" if keep else "CLEAR", 356, 118,
                 C.GREEN if keep else C.RED, 1)
        c.text_c("DAC <= VIN" if keep else "DAC > VIN", 356, 136,
                 C.GREEN if keep else C.RED, 1)
        c.text(format(result, "012b"), 260, 162, C.CYAN, 1)
        volts = result * 3.3 / 4096
        c.text("CODE x 3.3 / 4096", 20, 206, C.MUTED, 1)
        c.panel(20, 214, 444, 16, C.BG2, C.STROKE)
        c.fill_rect(21, 215, max(1, int(442 * result / 4096)), 14, C.CYAN)
        c.text(f"{result} / 4096 = {volts:.3f} V", 20, 242, C.TEXT, 1)
        c.text("GUESS ONE NEW BIT. DO NOT SET ALL ABOVE IT", 20, 260, C.DIM, 1)
        g.add(c)
    return g


def nvic_preempt():
    """TIM2 is running. EXTI0 at a higher preemption interrupts it, then returns.

    The equal-preemption failure stays on the static SVG. This GIF does not draw it.
    """
    g = Gif(W, H, delay=12)
    stages = [
        ("TIM2 RUN  PREEMPT 2", True, False, False, False),
        ("EXTI0 ARRIVES  PREEMPT 1", True, True, False, False),
        ("STACK EIGHT REGS", True, True, True, False),
        ("EXTI0 ISR RUNS", True, True, True, True),
        ("UNSTACK AND RETURN", True, False, False, False),
        ("TIM2 RESUMES", True, False, False, False),
    ]
    for index, (line, tim_on, exti_on, stack_on, isr_on) in enumerate(stages):
        c = Canvas(W, H)
        chrome(c, "NVIC PREEMPT", "GROUP4", "AUX GIF  STATIC SVG HAS THE FAILURE")
        c.panel(16, 42, 210, 70, C.PANEL, C.AMBER if tim_on else C.STROKE)
        c.text("TIM2", 90, 58, C.AMBER if tim_on else C.DIM, 1)
        c.text("PREEMPT 2", 55, 84, C.TEXT if tim_on else C.DIM, 1)
        c.panel(250, 42, 210, 70, C.PANEL, C.GREEN if exti_on else C.STROKE)
        c.text("EXTI0", 320, 58, C.GREEN if exti_on else C.DIM, 1)
        c.text("PREEMPT 1", 295, 84, C.TEXT if exti_on else C.DIM, 1)
        c.line(226, 76, 248, 76, C.STROKE, 2)
        c.panel(16, 126, 444, 36, C.PANEL2 if stack_on else C.PANEL, C.STROKE)
        c.text("STACK  R0-R3 R12 LR PC xPSR" if stack_on else "STACK  IDLE", 28, 140, C.TEXT if stack_on else C.DIM, 1)
        c.panel(16, 172, 444, 28, C.PANEL, C.VIOLET if isr_on else C.STROKE)
        c.text("EXTI0 ISR  ACTIVE" if isr_on else "EXTI0 ISR  WAIT", 28, 184, C.TEXT if isr_on else C.DIM, 1)
        c.text(line, 16, 220, C.TEXT, 1)
        c.text(f"FRAME {index + 1} OF 6", 16, 242, C.MUTED, 1)
        c.text("HIGHER PREEMPTION INTERRUPTS TIM2", 16, 262, C.GREEN, 1)
        c.text("PRINT THE FAILURE ON THE STATIC SVG", 16, 282, C.DIM, 1)
        g.add(c)
    return g

def clock_css():
    """HSE enters the PLL, SYSCLK sits at 72 MHz, then HSE vanishes and SYSCLK returns to HSI.

    The fetch failure stays on the static SVG.
    """
    g = Gif(W, H, delay=10)
    stages = [
        ("HSE 8 MHz INTO PLL", True, False, "8", "HSI"),
        ("PLL x9 LOCKS", True, True, "8", "PLL"),
        ("SYSCLK 72 MHz", True, True, "72", "PLL"),
        ("HSE GONE", False, True, "72", "PLL"),
        ("PLL OFF", False, False, "8", "HSI"),
        ("SYSCLK IS HSI 8 MHz", False, False, "8", "HSI"),
    ]
    for index, (line, hse_on, pll_on, mhz, src) in enumerate(stages):
        c = Canvas(W, H)
        chrome(c, "CLOCK CSS", "HSE", "AUX GIF  STATIC SVG HAS THE FAILURE")
        c.panel(16, 42, 140, 70, C.PANEL, C.CYAN if hse_on else C.STROKE)
        c.text("HSE", 60, 58, C.CYAN if hse_on else C.DIM, 1)
        c.text("8 MHz" if hse_on else "OFF", 48, 84, C.TEXT if hse_on else C.DIM, 1)
        c.panel(170, 42, 140, 70, C.PANEL, C.GREEN if pll_on else C.STROKE)
        c.text("PLL", 220, 58, C.GREEN if pll_on else C.DIM, 1)
        c.text("x9" if pll_on else "OFF", 222, 84, C.TEXT if pll_on else C.DIM, 1)
        c.panel(324, 42, 140, 70, C.PANEL, C.AMBER)
        c.text("SYSCLK", 350, 58, C.AMBER, 1)
        c.text(f"{mhz} MHz", 348, 84, C.TEXT, 1)
        c.line(156, 76, 168, 76, C.STROKE, 2)
        c.line(310, 76, 322, 76, C.STROKE, 2)
        c.panel(16, 126, 448, 36, C.PANEL2 if src == "PLL" else C.PANEL, C.STROKE)
        c.text(f"SOURCE  {src}   SWS={'10' if src == 'PLL' else '00'}", 28, 140, C.TEXT, 1)
        c.text(line, 16, 184, C.TEXT, 1)
        c.text(f"FRAME {index + 1} OF 6", 16, 208, C.MUTED, 1)
        c.text("CSS RETURNS SYSCLK TO HSI", 16, 232, C.GREEN, 1)
        c.text("PRINT THE FETCH FAILURE ON THE SVG", 16, 252, C.DIM, 1)
        g.add(c)
    return g

def pwm_1khz():
    """CNT walks to ARR and the level flips at CCR=500.

    The slow path stays on the static SVG.
    """
    g = Gif(W, H, delay=12)
    stages = [
        ("CNT 0  HIGH", 0, True),
        ("CNT 250  HIGH", 250, True),
        ("CCR=500  EDGE", 500, True),
        ("CNT 750  LOW", 750, False),
        ("CNT 999  LOW", 999, False),
        ("1000 Hz  500 us HIGH", 0, True),
    ]
    for index, (note, cnt, high) in enumerate(stages):
        c = Canvas(W, H)
        chrome(c, "PWM 1 KHZ", "TIM3", "AUX GIF  1000 Hz")
        c.panel(16, 42, 448, 28, C.PANEL, C.STROKE)
        c.text("PSC=71 ARR=999 CCR=500", 28, 52, C.MUTED, 1)
        c.panel(16, 80, 140, 60, C.PANEL, C.CYAN)
        c.text("CNT", 60, 96, C.CYAN, 1)
        c.text(str(cnt), 55, 122, C.TEXT, 1)
        c.panel(170, 80, 140, 60, C.PANEL, C.AMBER)
        c.text("CCR", 215, 96, C.AMBER, 1)
        c.text("500", 215, 122, C.TEXT, 1)
        c.panel(324, 80, 140, 60, C.PANEL, C.GREEN if high else C.STROKE)
        c.text("OUT", 370, 96, C.GREEN if high else C.DIM, 1)
        c.text("HIGH" if high else "LOW", 360, 122, C.TEXT if high else C.DIM, 1)
        # crude duty bar
        c.hline(24, 160, 220 if high else 40, C.GREEN if high else C.AMBER, 2)
        c.text(note, 16, 190, C.TEXT, 1)
        c.text(f"FRAME {index + 1} OF 6", 16, 212, C.MUTED, 1)
        c.text("1000 Hz FROM A 72 MHz CLOCK", 16, 236, C.CYAN, 1)
        c.text("500 us HIGH THEN LOW", 16, 256, C.GREEN, 1)
        c.text("PRINT THE SLOW PATH ON THE STATIC SVG", 16, 278, C.DIM, 1)
        g.add(c)
    return g

def spi_jedec():
    """CS falls, MOSI shifts 0x9F, then MISO returns 0xEF 0x40 0x17 at 9 MHz.

    The swapped-wire failure stays on the static SVG.
    """
    g = Gif(W, H, delay=12)
    stages = [
        ("CS LOW", True, "", ""),
        ("MOSI 0x9F", True, "0x9F", ""),
        ("MISO 0xEF", True, "0x9F", "EF"),
        ("MISO 0x40", True, "0x9F", "EF 40"),
        ("MISO 0x17", True, "0x9F", "EF 40 17"),
        ("CS HIGH  9 MHz", False, "0x9F", "EF 40 17"),
    ]
    for index, (note, cs_low, mosi, miso) in enumerate(stages):
        c = Canvas(W, H)
        chrome(c, "SPI JEDEC", "MODE 0", "AUX GIF  9 MHz")
        c.panel(16, 42, 448, 28, C.PANEL, C.STROKE)
        c.text("PA5 SCK  PA7 MOSI  PA6 MISO", 28, 52, C.MUTED, 1)
        c.panel(16, 80, 100, 54, C.PANEL, C.AMBER if cs_low else C.STROKE)
        c.text("CS", 50, 96, C.AMBER if cs_low else C.DIM, 1)
        c.text("LOW" if cs_low else "HIGH", 40, 120, C.TEXT if cs_low else C.DIM, 1)
        c.panel(130, 80, 150, 54, C.PANEL, C.CYAN if mosi else C.STROKE)
        c.text("MOSI", 175, 96, C.CYAN if mosi else C.DIM, 1)
        c.text(mosi or "-", 170, 120, C.TEXT if mosi else C.DIM, 1)
        c.panel(294, 80, 170, 54, C.PANEL, C.GREEN if miso else C.STROKE)
        c.text("MISO", 350, 96, C.GREEN if miso else C.DIM, 1)
        c.text(miso or "-", 320, 120, C.TEXT if miso else C.DIM, 1)
        c.text(note, 16, 170, C.TEXT, 1)
        c.text(f"FRAME {index + 1} OF 6", 16, 194, C.MUTED, 1)
        c.text("0x9F THEN 0xEF 0x40 0x17", 16, 220, C.GREEN, 1)
        c.text("9 MHz  BR=010", 16, 242, C.CYAN, 1)
        c.text("PRINT THE SWAP ON THE STATIC SVG", 16, 266, C.DIM, 1)
        g.add(c)
    return g

def adc_sample():
    """One successful sample, then the MSB compare, at 12 MHz.

    Soft-source settling failures stay on the static SVG.
    """
    g = Gif(W, H, delay=10)
    notes = (
        "SAMPLE CAP CHARGING",
        "HOLD",
        "MSB COMPARE 2048",
        "KEEP / DROP BIT",
        "NEXT WEIGHT",
        "EOC  12 MHz",
    )
    progress = (1, 2, 3, 4, 5, 6)
    for index, note in enumerate(notes):
        c = Canvas(W, H)
        chrome(c, "ADC SAMPLE", "12 MHZ", "AUX GIF  ONE CONVERSION")
        c.panel(16, 42, 448, 28, C.PANEL, C.STROKE)
        c.text("ADCCLK 12 MHz  SMP then SAR", 28, 52, C.MUTED, 1)
        c.panel(16, 84, 448, 24, C.BG2, C.STROKE)
        fill = int(440 * min(1.0, progress[index] / 3))
        c.fill_rect(18, 86, max(2, fill), 20, C.CYAN if index < 2 else C.GREEN)
        c.text("SAMPLE" if index < 2 else "CONVERT", 20, 120, C.MUTED, 1)
        for i, (lab, w) in enumerate((("MSB", 2048), ("b10", 1024), ("b9", 512), ("LSB", 1))):
            x = 16 + i * 114
            active = index >= 2 and i <= max(0, index - 2)
            c.panel(x, 140, 104, 48, C.PANEL, C.AMBER if active else C.STROKE)
            c.text(lab, x + 12, 152, C.AMBER if active else C.DIM, 1)
            c.text(str(w), x + 12, 170, C.TEXT if active else C.DIM, 1)
        c.text(note, 16, 212, C.TEXT, 1)
        c.text(f"FRAME {index + 1} OF 6", 16, 232, C.MUTED, 1)
        c.text("MSB FIRST THEN LOWER WEIGHTS", 16, 252, C.GREEN, 1)
        c.text("PRINT SETTLING MISS ON THE SVG", 16, 270, C.DIM, 1)
        g.add(c)
    return g

def swd_fetch():
    """SWD writes Flash, then the CPU reads MSP and Reset_Handler.

    Pin reuse and the failure byte stay on the static SVG.
    """
    g = Gif(W, H, delay=12)
    lines = (
        "WRITE 0x08000000",
        "pin 34 SWDIO",
        "pin 37 SWCLK",
        "READ MSP",
        "READ Reset_Handler",
        "BOOT0 = 0",
    )
    for index, line in enumerate(lines):
        c = Canvas(W, H)
        chrome(c, "SWD FETCH", "BOOT0=0", "AUX GIF  STATIC SVG HAS THE FAILURE")
        c.panel(16, 48, 448, 36, C.PANEL, C.STROKE)
        c.text("pin 34  pin 37", 28, 60, C.CYAN, 1)
        c.text(line, 28, 120, C.TEXT, 1)
        c.text(f"FRAME {index + 1} OF 6", 28, 160, C.MUTED, 1)
        c.text("MSP THEN Reset_Handler", 28, 200, C.GREEN, 1)
        c.text("PRINT THE MISS ON THE STATIC SVG", 28, 222, C.DIM, 1)
        g.add(c)
    return g


def i2c_addr():
    """START, shift 0x78, then ACK on the 9th clock.

    A raw address byte and a missing pull-up stay on the static SVG.
    """
    g = Gif(W, H, delay=12)
    stages = [
        ("START", True, False, False, False),
        ("SHIFT 0x78", True, True, False, False),
        ("BIT 7 TO BIT 0", True, True, False, False),
        ("9TH CLOCK", True, True, True, False),
        ("SDA LOW  ACK", True, True, True, True),
        ("0x801E  4.7 k", True, True, True, True),
    ]
    for index, (note, st, sh, ninth, ack) in enumerate(stages):
        c = Canvas(W, H)
        chrome(c, "I2C ADDR", "0x78", "AUX GIF  ACK")
        c.panel(16, 42, 448, 28, C.PANEL, C.STROKE)
        c.text("PB6 SCL  PB7 SDA", 28, 52, C.MUTED, 1)
        c.panel(16, 80, 100, 54, C.PANEL, C.AMBER if st else C.STROKE)
        c.text("START", 35, 110, C.AMBER if st else C.DIM, 1)
        c.panel(130, 80, 120, 54, C.PANEL, C.CYAN if sh else C.STROKE)
        c.text("0x78", 165, 110, C.CYAN if sh else C.DIM, 1)
        c.panel(264, 80, 100, 54, C.PANEL, C.VIOLET if ninth else C.STROKE)
        c.text("9TH", 292, 110, C.VIOLET if ninth else C.DIM, 1)
        c.panel(378, 80, 86, 54, C.PANEL, C.GREEN if ack else C.STROKE)
        c.text("ACK", 398, 110, C.GREEN if ack else C.DIM, 1)
        c.text(note, 16, 170, C.TEXT, 1)
        c.text(f"FRAME {index + 1} OF 6", 16, 194, C.MUTED, 1)
        c.text("0x78 THEN ACK", 16, 220, C.GREEN, 1)
        c.text("0x801E AND 4.7 k", 16, 242, C.CYAN, 1)
        c.text("PRINT THE NACK ON THE STATIC SVG", 16, 266, C.DIM, 1)
        g.add(c)
    return g

def dma_cndtr():
    """Eight half-words, CNDTR falls to 3: 5 samples, 10 bytes.

    Treating the remainder as bytes stays on the static SVG.
    """
    g = Gif(W, H, delay=10)
    counts = (8, 8, 6, 4, 3, 3)
    notes = (
        "8 HALF-WORDS",
        "CNDTR 8",
        "CNDTR 6",
        "CNDTR 4",
        "CNDTR 3",
        "5 samples  10 bytes",
    )
    for index, note in enumerate(notes):
        c = Canvas(W, H)
        chrome(c, "DMA CNDTR", "DMA1", "AUX GIF  HALF-WORDS")
        c.panel(16, 42, 448, 28, C.PANEL, C.STROKE)
        c.text("channel 4  HALF-WORD", 28, 52, C.MUTED, 1)
        for i in range(8):
            x = 20 + i * 56
            filled = i < (8 - counts[index])
            c.panel(x, 88, 48, 40, C.PANEL2 if filled else C.PANEL,
                    C.GREEN if filled else C.STROKE)
            c.text(str(i), x + 18, 104, C.DIM, 1)
        c.panel(16, 144, 200, 48, C.PANEL, C.AMBER)
        c.text(f"CNDTR {counts[index]}", 36, 162, C.AMBER, 1)
        done = 8 - counts[index]
        c.panel(232, 144, 232, 48, C.PANEL, C.CYAN)
        c.text(f"DONE {done}  BYTES {done*2}", 248, 162, C.CYAN, 1)
        c.text(note, 16, 216, C.TEXT, 1)
        c.text(f"FRAME {index + 1} OF 6", 16, 236, C.MUTED, 1)
        c.text("5 samples IS 10 bytes", 16, 256, C.GREEN, 1)
        c.text("PRINT THE BYTE CUT ON THE SVG", 16, 274, C.DIM, 1)
        g.add(c)
    return g

def iwdg_1s():
    """A 625 Hz count is fed before it reaches 0.

    Off-by-one reload and the window watchdog stay on the static SVG.
    """
    g = Gif(W, H, delay=12)
    stages = [
        ("40 kHz TYPICAL", True, False, False, False, False),
        ("prescaler 64", True, True, False, False, False),
        ("625 Hz", True, True, True, False, False),
        ("COUNT DOWN", True, True, True, True, False),
        ("FEED BEFORE ZERO", True, True, True, True, True),
        ("Reload = 624", True, True, True, True, True),
    ]
    for index, (line, lsi, psc, tick, count, feed) in enumerate(stages):
        c = Canvas(W, H)
        chrome(c, "IWDG 1S", "624", "AUX GIF  TYPICAL 40 kHz")
        c.panel(16, 42, 140, 70, C.PANEL, C.CYAN if lsi else C.STROKE)
        c.text("LSI", 60, 58, C.CYAN if lsi else C.DIM, 1)
        c.text("40 kHz", 40, 84, C.TEXT if lsi else C.DIM, 1)
        c.panel(168, 42, 140, 70, C.PANEL, C.GREEN if psc else C.STROKE)
        c.text("/64", 214, 58, C.GREEN if psc else C.DIM, 1)
        c.text("PSC", 214, 84, C.TEXT if psc else C.DIM, 1)
        c.panel(320, 42, 140, 70, C.PANEL, C.AMBER if tick else C.STROKE)
        c.text("625 Hz", 350, 58, C.AMBER if tick else C.DIM, 1)
        c.text("TICK", 360, 84, C.TEXT if tick else C.DIM, 1)
        c.panel(16, 126, 300, 36, C.PANEL2 if count else C.PANEL, C.STROKE)
        c.text("COUNT  N .. 1" if count else "COUNT  IDLE", 28, 140, C.TEXT if count else C.DIM, 1)
        c.panel(328, 126, 132, 36, C.PANEL, C.GREEN if feed else C.STROKE)
        c.text("FEED" if feed else "WAIT", 360, 140, C.TEXT if feed else C.DIM, 1)
        c.text(line, 16, 190, C.TEXT, 1)
        c.text(f"FRAME {index + 1} OF 6", 16, 214, C.MUTED, 1)
        c.text("Reload = 624", 16, 240, C.GREEN, 1)
        c.text("625 Hz UNTIL THE FEED", 16, 262, C.CYAN, 1)
        c.text("PRINT ZERO AND THE WINDOW ON THE SVG", 16, 284, C.DIM, 1)
        g.add(c)
    return g

def uart_idle():
    """After one frame, RX stays high for one frame time, then IDLE is marked.

    Framing-error samples stay on the static SVG. This GIF does not replay 0xA5 bit by bit.
    """
    g = Gif(W, H, delay=10)
    notes = (
        "FRAME END  STOP HIGH",
        "RX STAYS HIGH",
        "RX STAYS HIGH",
        "RX STAYS HIGH",
        "ONE FRAME OF IDLE",
        "IDLE  86.8 us",
    )
    for index, note in enumerate(notes):
        c = Canvas(W, H)
        chrome(c, "UART IDLE", "8N1", "AUX GIF  86.8 us IS ONE FRAME")
        c.panel(16, 42, 448, 28, C.PANEL, C.STROKE)
        c.text("RX AFTER ONE FRAME @ 115200", 28, 52, C.MUTED, 1)
        c.hline(24, 120, 432, C.GREEN, 2)
        for t in range(11):
            x = 24 + t * 39
            c.vline(x, 112, 16, C.GRID, 1)
        mark = 24 + int(432 * index / 5)
        c.vline(mark, 96, 48, C.AMBER, 2)
        c.circle(mark, 120, 3, C.AMBER, True)
        c.panel(16, 150, 200, 40, C.PANEL, C.CYAN)
        c.text("BIT  8.68 us", 28, 166, C.CYAN, 1)
        c.panel(232, 150, 232, 40, C.PANEL, C.AMBER)
        c.text("FRAME  86.8 us", 248, 166, C.AMBER, 1)
        c.text(note, 16, 212, C.TEXT, 1)
        c.text(f"FRAME {index + 1} OF 6", 16, 232, C.MUTED, 1)
        c.text("IDLE IS THE LINE HIGH FOR 86.8 us", 16, 252, C.CYAN, 1)
        c.text("NOT A PROTOCOL LENGTH FIELD", 16, 270, C.AMBER, 1)
        g.add(c)
    return g

def iap_jump():
    """Write the two keys in order, then read MSP and Reset_Handler.

    A reversed key and the address past 64 KB stay on the static SVG.
    """
    g = Gif(W, H, delay=12)
    stages = [
        ("KEY1 0x45670123", True, False, False, False, False),
        ("KEY2 0xCDEF89AB", True, True, False, False, False),
        ("HALF-WORD IN APP", True, True, True, False, False),
        ("READ MSP", True, True, True, True, False),
        ("READ Reset_Handler", True, True, True, True, True),
        ("VTOR 0x08004800", True, True, True, True, True),
    ]
    for index, (line, k1, k2, prog, msp, vtor) in enumerate(stages):
        c = Canvas(W, H)
        chrome(c, "IAP JUMP", "APP", "AUX GIF  KEY ORDER")
        c.panel(16, 42, 210, 56, C.PANEL, C.CYAN if k1 else C.STROKE)
        c.text("KEY1", 90, 56, C.CYAN if k1 else C.DIM, 1)
        c.text("0x45670123", 40, 78, C.TEXT if k1 else C.DIM, 1)
        c.panel(250, 42, 210, 56, C.PANEL, C.GREEN if k2 else C.STROKE)
        c.text("KEY2", 324, 56, C.GREEN if k2 else C.DIM, 1)
        c.text("0xCDEF89AB", 274, 78, C.TEXT if k2 else C.DIM, 1)
        c.panel(16, 110, 210, 36, C.PANEL, C.AMBER if prog else C.STROKE)
        c.text("HALF-WORD" if prog else "PROG IDLE", 28, 124, C.TEXT if prog else C.DIM, 1)
        c.panel(250, 110, 210, 36, C.PANEL, C.VIOLET if msp else C.STROKE)
        c.text("MSP + Reset_Handler" if msp else "VECTOR IDLE", 258, 124, C.TEXT if msp else C.DIM, 1)
        c.panel(16, 158, 444, 28, C.PANEL2 if vtor else C.PANEL, C.STROKE)
        c.text("VTOR 0x08004800  0xB800" if vtor else "VTOR PENDING", 28, 170, C.TEXT if vtor else C.DIM, 1)
        c.text(line, 16, 210, C.TEXT, 1)
        c.text(f"FRAME {index + 1} OF 6", 16, 232, C.MUTED, 1)
        c.text("MSP THEN Reset_Handler", 16, 254, C.GREEN, 1)
        c.text("PRINT THE MISS ON THE STATIC SVG", 16, 276, C.DIM, 1)
        g.add(c)
    return g

def can_500k():
    """Eight 250 ns quanta make one 2 us bit at 500 kbit/s.

    The failed prescaler row and the crystal pins stay on the static SVG.
    """
    g = Gif(W, H, delay=12)
    stages = [
        ("TQ 1  250 ns", 1),
        ("TQ 2  250 ns", 2),
        ("TQ 3  250 ns", 3),
        ("TQ 6  SAMPLE 75%", 6),
        ("TQ 8  2 us", 8),
        ("500 kbit/s", 8),
    ]
    for index, (line, lit) in enumerate(stages):
        c = Canvas(W, H)
        chrome(c, "CAN 500K", "36 MHz", "AUX GIF  8 QUANTA")
        c.text("prescaler 9", 16, 50, C.MUTED, 1)
        x0 = 16
        for q in range(8):
            on = q < lit
            col = C.AMBER if (q == 5 and lit >= 6) else (C.GREEN if on else C.STROKE)
            c.panel(x0 + q * 56, 70, 50, 50, C.PANEL, col)
            c.text(f"T{q+1}", x0 + q * 56 + 12, 90, C.TEXT if on else C.DIM, 1)
        c.panel(16, 140, 444, 36, C.PANEL2, C.STROKE)
        c.text("SAMPLE AT 75%  /  1.5 us" if lit >= 6 else "BUILDING BIT TIME", 28, 154, C.TEXT, 1)
        c.text(line, 16, 200, C.TEXT, 1)
        c.text(f"FRAME {index + 1} OF 6", 16, 222, C.MUTED, 1)
        c.text("75% AT 1.5 us", 16, 246, C.GREEN, 1)
        c.text("250 ns TIMES 8 IS 2 us", 16, 268, C.CYAN, 1)
        c.text("PRINT THE MISS ON THE STATIC SVG", 16, 288, C.DIM, 1)
        g.add(c)
    return g

def usb_48m():
    """D+ is pulled up, the clock is 48 MHz, then 18 and 67 bytes.

    The undivided clock and the pull-up on DM stay on the static SVG.
    """
    g = Gif(W, H, delay=12)
    stages = [
        ("D+ PULL-UP", True, False, False, False, False),
        ("HOST SEES D+", True, True, False, False, False),
        ("USBPRE = 0", True, True, True, False, False),
        ("48 MHz", True, True, True, True, False),
        ("18 bytes", True, True, True, True, True),
        ("67 bytes", True, True, True, True, True),
    ]
    for index, (line, dp, host, pre, clk, desc) in enumerate(stages):
        c = Canvas(W, H)
        chrome(c, "USB 48M", "FS", "AUX GIF  D+")
        c.panel(16, 42, 140, 70, C.PANEL, C.CYAN if dp else C.STROKE)
        c.text("PA12", 60, 58, C.CYAN if dp else C.DIM, 1)
        c.text("D+ UP", 50, 84, C.TEXT if dp else C.DIM, 1)
        c.panel(168, 42, 140, 70, C.PANEL, C.GREEN if host else C.STROKE)
        c.text("HOST", 210, 58, C.GREEN if host else C.DIM, 1)
        c.text("SEES FS", 195, 84, C.TEXT if host else C.DIM, 1)
        c.panel(320, 42, 140, 70, C.PANEL, C.AMBER if pre else C.STROKE)
        c.text("USBPRE", 350, 58, C.AMBER if pre else C.DIM, 1)
        c.text("= 0", 365, 84, C.TEXT if pre else C.DIM, 1)
        c.panel(16, 126, 210, 36, C.PANEL, C.VIOLET if clk else C.STROKE)
        c.text("48 MHz USBCLK" if clk else "CLOCK PENDING", 28, 140, C.TEXT if clk else C.DIM, 1)
        c.panel(250, 126, 210, 36, C.PANEL2 if desc else C.PANEL, C.STROKE)
        label = "18 bytes THEN 67 bytes" if index >= 5 else ("18 bytes" if index == 4 else "DESC IDLE")
        c.text(label, 258, 140, C.TEXT if desc else C.DIM, 1)
        c.text(line, 16, 190, C.TEXT, 1)
        c.text(f"FRAME {index + 1} OF 6", 16, 214, C.MUTED, 1)
        c.text("18 bytes THEN 67 bytes", 16, 240, C.GREEN, 1)
        c.text("48 MHz", 16, 262, C.CYAN, 1)
        c.text("PRINT THE MISS ON THE STATIC SVG", 16, 284, C.DIM, 1)
        g.add(c)
    return g

def rtos_tick():
    """A 1 ms tick keeps priority 2 on the CPU and priority 1 waiting.

    The assert stop and a SysTick clash stay on the static SVG.
    """
    g = Gif(W, H, delay=12)
    stages = [
        ("TICK 1 ms", True, False, False, False),
        ("TICK 1 ms", True, True, False, False),
        ("priority 2 RUNS", True, True, True, False),
        ("priority 1 WAITS", True, True, True, True),
        ("128 words", True, True, True, True),
        ("512 bytes", True, True, True, True),
    ]
    for index, (line, tick, ready, p2, p1) in enumerate(stages):
        c = Canvas(W, H)
        chrome(c, "RTOS TICK", "1 ms", "AUX GIF  WORDS")
        c.panel(16, 42, 140, 70, C.PANEL, C.CYAN if tick else C.STROKE)
        c.text("1000 Hz", 45, 58, C.CYAN if tick else C.DIM, 1)
        c.text("1 ms", 60, 84, C.TEXT if tick else C.DIM, 1)
        c.panel(168, 42, 140, 70, C.PANEL, C.AMBER if p2 else C.STROKE)
        c.text("PRIO 2", 200, 58, C.AMBER if p2 else C.DIM, 1)
        c.text("RUNS" if p2 else "IDLE", 210, 84, C.TEXT if p2 else C.DIM, 1)
        c.panel(320, 42, 140, 70, C.PANEL, C.VIOLET if p1 else C.STROKE)
        c.text("PRIO 1", 352, 58, C.VIOLET if p1 else C.DIM, 1)
        c.text("WAITS" if p1 else "IDLE", 358, 84, C.TEXT if p1 else C.DIM, 1)
        c.panel(16, 126, 444, 36, C.PANEL2 if ready else C.PANEL, C.STROKE)
        stack = "128 words = 512 bytes" if index >= 5 else ("128 words" if index == 4 else "STACK LED TASK")
        c.text(stack if index >= 4 else ("READY LIST" if ready else "SCHEDULER"), 28, 140, C.TEXT, 1)
        c.text(line, 16, 190, C.TEXT, 1)
        c.text(f"FRAME {index + 1} OF 6", 16, 214, C.MUTED, 1)
        c.text("priority 2 BEFORE priority 1", 16, 240, C.GREEN, 1)
        c.text("128 words = 512 bytes", 16, 262, C.CYAN, 1)
        c.text("PRINT THE ASSERT ON THE STATIC SVG", 16, 284, C.DIM, 1)
        g.add(c)
    return g

def stop_wake_gif():
    """Wake from Stop, move the clock from 8 MHz back to 72 MHz, then mark 115200.

    The failed baud and the other Stop cell stay on the static SVG.
    """
    g = Gif(W, H, delay=12)
    stages = [
        ("STOP", True, False, False, False, False),
        ("WAKE ON HSI", True, True, False, False, False),
        ("8 MHz", True, True, True, False, False),
        ("PLL ON", True, True, True, True, False),
        ("72 MHz", True, True, True, True, True),
        ("115200", True, True, True, True, True),
    ]
    for index, (line, stop, wake, hsi, pll, uart) in enumerate(stages):
        c = Canvas(W, H)
        chrome(c, "STOP WAKE", "HSI", "AUX GIF  115200")
        c.panel(16, 42, 140, 70, C.PANEL, C.CYAN if stop else C.STROKE)
        c.text("STOP", 55, 58, C.CYAN if stop else C.DIM, 1)
        c.text("LP REG", 45, 84, C.TEXT if stop else C.DIM, 1)
        c.panel(168, 42, 140, 70, C.PANEL, C.GREEN if wake else C.STROKE)
        c.text("WAKE", 210, 58, C.GREEN if wake else C.DIM, 1)
        c.text("PA0/RTC", 190, 84, C.TEXT if wake else C.DIM, 1)
        c.panel(320, 42, 140, 70, C.PANEL, C.AMBER if hsi else C.STROKE)
        c.text("HSI", 365, 58, C.AMBER if hsi else C.DIM, 1)
        c.text("8 MHz", 350, 84, C.TEXT if hsi else C.DIM, 1)
        c.panel(16, 126, 210, 36, C.PANEL, C.VIOLET if pll else C.STROKE)
        c.text("PLL 72 MHz" if pll else "PLL OFF", 28, 140, C.TEXT if pll else C.DIM, 1)
        c.panel(250, 126, 210, 36, C.PANEL2 if uart else C.PANEL, C.STROKE)
        c.text("UART 115200" if uart else "UART HOLD", 262, 140, C.TEXT if uart else C.DIM, 1)
        c.text("0x271", 16, 180, C.MUTED, 1)
        c.text(line, 16, 206, C.TEXT, 1)
        c.text(f"FRAME {index + 1} OF 6", 16, 228, C.MUTED, 1)
        c.text("8 MHz THEN 72 MHz", 16, 252, C.GREEN, 1)
        c.text("PRINT THE MISS ON THE STATIC SVG", 16, 274, C.DIM, 1)
        g.add(c)
    return g

def cfsr_read_gif():
    """Read CFSR, see bit 15 set, then let 72 counts finish 1 us.

    A clear bit 15 and a cycle delta of 0 stay on the static SVG.
    """
    g = Gif(W, H, delay=12)
    stages = [
        ("READ CFSR", True, False, False, False),
        ("0xE000ED28", True, True, False, False),
        ("bit 15 = 1", True, True, True, False),
        ("COUNT 24", True, True, True, True),
        ("COUNT 72", True, True, True, True),
        ("1 us", True, True, True, True),
    ]
    for index, (line, cfsr, addr, bit, dwt) in enumerate(stages):
        c = Canvas(W, H)
        chrome(c, "CFSR", "DWT", "AUX GIF  1 us")
        c.panel(16, 42, 210, 70, C.PANEL, C.CYAN if cfsr else C.STROKE)
        c.text("CFSR", 90, 58, C.CYAN if cfsr else C.DIM, 1)
        c.text("0xE000ED28" if addr else "READ", 40, 84, C.TEXT if cfsr else C.DIM, 1)
        c.panel(250, 42, 210, 70, C.PANEL, C.GREEN if bit else C.STROKE)
        c.text("BFARVALID", 290, 58, C.GREEN if bit else C.DIM, 1)
        c.text("bit 15 = 1" if bit else "PENDING", 290, 84, C.TEXT if bit else C.DIM, 1)
        c.panel(16, 126, 444, 36, C.PANEL2 if dwt else C.PANEL, C.STROKE)
        dlabel = "72 COUNTS = 1 us" if index >= 5 else ("COUNT 72" if index == 4 else ("COUNT 24" if index == 3 else "DWT IDLE"))
        c.text(dlabel, 28, 140, C.TEXT if dwt else C.DIM, 1)
        c.text("72 MHz", 16, 180, C.MUTED, 1)
        c.text(line, 16, 206, C.TEXT, 1)
        c.text(f"FRAME {index + 1} OF 6", 16, 228, C.MUTED, 1)
        c.text("bit 15 = 1", 16, 252, C.GREEN, 1)
        c.text("72 COUNTS = 1 us", 16, 274, C.CYAN, 1)
        c.text("PRINT THE MISS ON THE STATIC SVG", 16, 294, C.DIM, 1)
        g.add(c)
    return g

def boot0_low():
    """Pin 44 is 0 and the probe sits on pins 34 and 37.

    The high BOOT pin and an optimizer edit stay on the static SVG.
    """
    g = Gif(W, H, delay=12)
    notes = (
        "pin 34 PA13",
        "pin 37 PA14",
        "GROUND",
        "3.3 V",
        "pin 44",
        "BOOT0 = 0",
    )
    for index, note in enumerate(notes):
        c = Canvas(W, H)
        chrome(c, "BOOT0", "SWD", "AUX GIF  TARGET")
        c.panel(16, 48, 448, 28, C.PANEL, C.STROKE)
        c.text("0x08000000", 28, 58, C.MUTED, 1)
        c.text(note, 28, 120, C.TEXT, 1)
        c.text(f"FRAME {index + 1} OF 6", 28, 160, C.MUTED, 1)
        c.text("BOOT0 = 0", 28, 200, C.GREEN, 1)
        c.text("TARGET SEEN", 28, 222, C.CYAN, 1)
        c.text("PRINT THE MISS ON THE STATIC SVG", 28, 248, C.DIM, 1)
        g.add(c)
    return g


def one_slot():
    """Fill 16 KB, 2 KB, and one 0xB800 image up to 0x08010000.

    The second image and the oversized SRAM array stay on the static SVG.
    """
    g = Gif(W, H, delay=12)
    notes = (
        "16 KB",
        "0x08004000",
        "2 KB",
        "0x08004800",
        "0xB800",
        "0x08010000",
    )
    for index, note in enumerate(notes):
        c = Canvas(W, H)
        chrome(c, "ONE SLOT", "64 KB", "AUX GIF  APP")
        c.panel(16, 48, 448, 28, C.PANEL, C.STROKE)
        c.text("ONE APP", 28, 58, C.MUTED, 1)
        c.text(note, 28, 120, C.TEXT, 1)
        c.text(f"FRAME {index + 1} OF 6", 28, 160, C.MUTED, 1)
        c.text("16 KB + 2 KB + 0xB800", 28, 200, C.GREEN, 1)
        c.text("ENDS AT 0x08010000", 28, 222, C.CYAN, 1)
        c.text("PRINT THE MISS ON THE STATIC SVG", 28, 248, C.DIM, 1)
        g.add(c)
    return g

BUILDERS = {
    "led-blink": led_blink,
    "pwm-breath": pwm_breath,
    "uart-bits": uart_bits,
    "i2c-timing": i2c_timing,
    "dma-ring": dma_ring,
    "sar-adc": sar_adc,
    "nvic-preempt": nvic_preempt,
    "uart-idle": uart_idle,
    "clock-css": clock_css,
    "pwm-1khz": pwm_1khz,
    "spi-jedec": spi_jedec,
    "adc-sample": adc_sample,
    "swd-fetch": swd_fetch,
    "i2c-addr": i2c_addr,
    "dma-cndtr": dma_cndtr,
    "iwdg-1s": iwdg_1s,
    "iap-jump": iap_jump,
    "can-500k": can_500k,
    "usb-48m": usb_48m,
    "rtos-tick": rtos_tick,
    "stop-wake": stop_wake_gif,
    "cfsr-read": cfsr_read_gif,
    "boot0-low": boot0_low,
    "one-slot": one_slot,
}


def main(argv):
    only = set(argv[1:])
    os.makedirs(OUT, exist_ok=True)
    for name, fn in BUILDERS.items():
        if only and name not in only:
            continue
        gif = fn()
        size = gif.save(os.path.join(OUT, name + ".gif"))
        print(f"[ok] {name:12s} {gif.w}×{gif.h} {len(gif.frames):3d} 帧 "
              f"{size / 1024:6.1f} KB")
    print("提示：python3 tools/check_assets.py 可解码回来逐像素校验")


if __name__ == "__main__":
    main(sys.argv)

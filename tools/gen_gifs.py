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
    lines = (
        "TIM2 RUN  PREEMPT 2",
        "EXTI0 ARRIVES  PREEMPT 1",
        "STACK EIGHT REGS",
        "EXTI0 ISR RUNS",
        "UNSTACK AND RETURN",
        "TIM2 RESUMES",
    )
    for index, line in enumerate(lines):
        c = Canvas(W, H)
        chrome(c, "NVIC PREEMPT", "GROUP4", "AUX GIF  STATIC SVG HAS THE FAILURE")
        c.panel(16, 48, 448, 36, C.PANEL, C.STROKE)
        c.text("TIM2  PREEMPT 2", 28, 60, C.AMBER, 1)
        c.panel(16, 96, 448, 36, C.PANEL, C.CYAN if index else C.STROKE)
        c.text("EXTI0  PREEMPT 1", 28, 108, C.GREEN if index else C.DIM, 1)
        c.text(line, 28, 160, C.TEXT, 1)
        c.text(f"FRAME {index + 1} OF 6", 28, 184, C.MUTED, 1)
        c.text("HIGHER PREEMPTION INTERRUPTS TIM2", 28, 214, C.GREEN, 1)
        c.text("THEN THE CORE RETURNS", 28, 232, C.MUTED, 1)
        c.text("PRINT THE FAILURE ON THE STATIC SVG", 28, 254, C.DIM, 1)
        g.add(c)
    return g


def uart_idle():
    """After one frame, RX stays high for one frame time, then IDLE is marked.

    Framing-error samples stay on the static SVG. This GIF does not replay 0xA5 bit by bit.
    """
    g = Gif(W, H, delay=12)
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
        c.panel(16, 48, 448, 28, C.PANEL, C.STROKE)
        c.text("RX LINE HIGH AFTER THE FRAME", 28, 58, C.MUTED, 1)
        c.hline(24, 120, 432, C.GREEN, 2)
        mark = 24 + int(432 * index / 5)
        c.vline(mark, 100, 40, C.AMBER, 1)
        c.text(note, 28, 160, C.TEXT, 1)
        c.text(f"FRAME {index + 1} OF 6", 28, 184, C.MUTED, 1)
        c.text("IDLE IS THE LINE HIGH FOR 86.8 us", 28, 214, C.CYAN, 1)
        c.text("NOT A PROTOCOL LENGTH FIELD", 28, 232, C.AMBER, 1)
        c.text("FRAMING ERROR STAYS ON THE STATIC SVG", 28, 254, C.DIM, 1)
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

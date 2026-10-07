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
    """1 Hz 闪烁：上半屏是电路，下半屏是波形 + 游标。"""
    g = Gif(W, H, delay=8)
    frames = 24
    for i in range(frames):
        on = i < frames // 2
        c = Canvas(W, H)
        chrome(c, "GPIO BLINK", "PA5", "1 HZ  HAL_DELAY(500)  PUSH-PULL OUTPUT")
        # 电路
        c.panel(16, 42, 448, 96, C.PANEL, C.STROKE)
        c.chip(30, 62, 90, 54, "STM32", C.PANEL2, C.CYAN, C.CYAN)
        c.text("PA5", 46, 100, C.MUTED, 1)
        c.line(120, 89, 150, 89, C.AMBER, 2)
        c.panel(150, 80, 34, 18, C.BG2, C.AMBER)
        c.text("330", 155, 86, C.AMBER, 1)
        c.line(184, 89, 206, 89, C.AMBER, 2)
        c.led(220, 89, 11, C.RED, on)
        c.line(232, 89, 300, 89, C.AMBER, 2)
        c.line(300, 89, 300, 120, C.MUTED, 2)
        c.line(288, 120, 312, 120, C.MUTED, 2)
        c.text("GND", 320, 116, C.MUTED, 1)
        c.text("LED ON" if on else "LED OFF", 380, 84,
               C.GREEN if on else C.DIM, 1)
        c.text("I = (3.3-2.0)/330 = 4 MA", 340, 104, C.DIM, 1)
        # 波形
        c.text("PA5 LEVEL", 16, 152, C.MUTED, 1)
        c.hline(16, 194, 448, C.STROKE)
        c.hline(16, 194 - 34, 448, C.GRID)
        bits = [1] * 4 + [0] * 4
        c.waveform(16, 168, 448, 40, bits, C.GREEN, 2)
        # 游标
        px = 16 + int(448 * (i % frames) / frames)
        c.vline(px, 164, 34, C.RED, 1)
        c.circle(px, 164 + (0 if on else 32), 3, C.RED)
        c.text("500 MS HIGH + 500 MS LOW", 16, 212, C.DIM, 1)
        c.text("TOGGLE  BSRR  ATOMIC  NO READ-MODIFY-WRITE", 16, 230, C.DIM, 1)
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
               "FREQ = 72MHZ / ((PSC+1)(ARR+1))   DUTY = CCR/(ARR+1)")
        # LED 亮度
        c.panel(16, 42, 200, 108, C.PANEL, C.STROKE)
        c.led(80, 96, 22, mix(dim(C.RED, 0.25), C.RED, duty), True)
        c.text_c(f"DUTY {int(duty * 100):2d}%", 116, 76, C.AMBER, 1)
        c.text_c("CCR = %d" % int(duty * 999), 116, 96, C.MUTED, 1)
        c.text_c("ARR = 999  PSC = 0", 116, 116, C.MUTED, 1)
        c.text_c("F = 72 KHZ", 116, 134, C.DIM, 1)
        # 占空比条
        c.panel(232, 42, 232, 108, C.PANEL, C.STROKE)
        c.text("CCR", 246, 58, C.MUTED, 1)
        c.panel(276, 52, 174, 16, C.BG2, C.STROKE)
        c.fill_rect(277, 53, int(172 * duty), 14, C.AMBER)
        c.text("CNT 0 -> ARR", 246, 82, C.MUTED, 1)
        cy = 82
        c.hline(276, cy + 6, 174, C.STROKE)
        c.circle(276 + int(172 * ((i * 3 % 30) / 30)), cy + 6, 3, C.CYAN)
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


def i2c_timing():
    """I2C 一次写事务：START / 地址 / R-W / ACK / 数据 / ACK / STOP 逐段高亮。"""
    g = Gif(W, H, delay=10)
    sda = [1, 0, 0, 1, 1, 1, 1, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 1]
    phases = [(0, 1, "START"), (1, 8, "ADDR 0x3C"), (8, 9, "R/W"),
              (9, 10, "ACK"), (10, 18, "DATA"), (18, 19, "ACK"),
              (19, 20, "STOP")]
    x0, pw = 20, 22
    total = len(phases)
    for f in range(total):
        c = Canvas(W, H)
        chrome(c, "I2C TIMING", "400 KHZ",
               "START: SDA FALLS WHILE SCL HIGH   STOP: SDA RISES WHILE SCL HIGH")
        for i, (a, b, name) in enumerate(phases):
            x = x0 + a * pw
            w = (b - a) * pw - 4
            cur = (i == f)
            c.panel(x, 40, w, 22, C.PANEL2 if cur else C.PANEL,
                    C.GREEN if cur else C.STROKE)
            c.text_c(name, x + w / 2, 46, C.GREEN if cur else C.MUTED, 1)

        a, b, name = phases[f]
        c.text("SCL", 20, 92, C.CYAN, 1)
        y_hi, y_lo = 100, 128
        for i in range(20):
            x = x0 + i * pw
            col = C.CYAN if a <= i < b else dim(C.CYAN, 0.4)
            c.line(x, y_lo, x, y_hi, col, 2)
            c.line(x, y_hi, x + pw / 2, y_hi, col, 2)
            c.line(x + pw / 2, y_hi, x + pw / 2, y_lo, col, 2)
            c.line(x + pw / 2, y_lo, x + pw, y_lo, col, 2)
        c.text("SDA", 20, 160, C.AMBER, 1)
        y1, y0 = 168, 196
        for i, bit in enumerate(sda):
            x = x0 + i * pw
            col = C.AMBER if a <= i < b else dim(C.AMBER, 0.4)
            yy = y1 if bit else y0
            c.line(x, yy, x + pw, yy, col, 2)
            if i < 19:
                nxt = y1 if sda[i + 1] else y0
                if nxt != yy:
                    c.line(x + pw, yy, x + pw, nxt, col, 2)
        c.rect(x0 + a * pw - 2, 88, (b - a) * pw + 2, 116, C.GREEN, 1)
        c.text(f"PHASE {f + 1}/{total}: {name}", 20, 226, C.GREEN, 1)
        tips = [
            "SCL HIGH + SDA HIGH->LOW = START",
            "7 BIT ADDRESS THEN R/W BIT (0 = WRITE)",
            "RECEIVER PULLS SDA LOW = ACK",
            "DATA 8 BIT, MSB FIRST",
            "EACH ACK IS THE 9TH CLOCK PULSE",
            "SCL HIGH + SDA LOW->HIGH = STOP",
            "PULL-UP 4.7K ON BOTH LINES",
        ]
        c.text(tips[f], 20, 244, C.TEXT, 1)
        c.text("HAL_I2C_Mem_Write(&hi2c1, 0x3C<<1, reg, 1, buf, len, 100)",
               20, 262, C.CYAN, 1)
        c.text("BUS STUCK? SEND 9 CLOCKS MANUALLY THEN A STOP", 20, 278, C.DIM, 1)
        g.add(c)
    return g


BUILDERS = {
    "led-blink": led_blink,
    "pwm-breath": pwm_breath,
}



# --------------------------------------------------------------------------- UART 帧


def uart_bits():
    """逐位发送：10 个位格依次高亮，波形同步生长。"""
    g = Gif(W, H, delay=9)
    data = [1, 0, 1, 0, 0, 1, 0, 1]           # 0xA5，LSB 先发
    bits = [0] + data + [1]                    # 起始位 0、8 数据位、停止位 1
    labels = ["S"] + [str(i) for i in range(8)] + ["P"]
    total = len(bits) + 1                      # 开头留一帧空闲
    for f in range(total):
        step = f - 1                            # -1 = 空闲
        c = Canvas(W, H)
        chrome(c, "UART FRAME", "115200 8N1",
               "1 START + 8 DATA + 0 PARITY + 1 STOP = 10 BITS = 86.8 US")
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
            c.text("8.68 US" if step else "START: HIGH->LOW EDGE", 200, 206,
                   C.AMBER, 1)
        c.text("1 BIT = 1/115200 S = 8.68 US", 24, 226, C.MUTED, 1)
        c.text("OVERSAMPLING 16X -> SAMPLE AT BIT CENTER", 24, 242, C.DIM, 1)
        c.text("BAUD ERROR MUST BE < 2.5% FOR 8N1", 24, 258, C.DIM, 1)
        g.add(c)
    return g


# --------------------------------------------------------------------------- DMA 环形缓冲


def dma_ring():
    """ADC 采样 → DMA 循环搬运到数组，CPU 同时在做别的事。"""
    g = Gif(W, H, delay=7)
    frames = 16
    vals = [2048, 2100, 2201, 2350, 2500, 2420, 2301, 2180]
    for f in range(frames):
        c = Canvas(W, H)
        chrome(c, "DMA CIRCULAR", "ADC1 -> RAM",
               "CPU COST: 0 CYCLES PER BYTE  HT/TC INTERRUPT EVERY 4 BYTES")
        c.chip(16, 52, 96, 46, "ADC1", C.PANEL2, C.AMBER, C.AMBER)
        c.text("CH0 PA0", 24, 108, C.MUTED, 1)
        c.panel(16, 120, 96, 60, C.PANEL, C.STROKE)
        c.text("DR", 24, 134, C.MUTED, 1)
        c.text_c(str(vals[f % 8]), 64, 154, C.AMBER, 1)
        c.chip(150, 74, 110, 46, "DMA1 CH1", C.PANEL2, C.CYAN, C.CYAN)
        c.text("CIRCULAR MODE", 150, 132, C.MUTED, 1)
        c.text("MINC / PSIZE=H", 150, 146, C.MUTED, 1)
        c.text("BUFFER [8]", 300, 66, C.MUTED, 1)
        for i in range(8):
            x = 300 + (i % 4) * 42
            y = 76 + (i // 4) * 34
            filled = i <= (f % 8)
            cur = i == (f % 8)
            c.panel(x, y, 38, 28, C.PANEL2 if filled else C.PANEL,
                    C.CYAN if cur else C.STROKE)
            c.text_c(str(vals[i]) if filled else "----", x + 19, y + 10,
                     C.GREEN if filled else C.DIM, 1)
        px = 112 + int((300 - 112) * ((f % 8) / 8))
        c.circle(px, 97, 5, C.CYAN)
        c.circle(px, 97, 2, C.WHITE)
        c.panel(16, 196, 448, 62, C.PANEL, C.STROKE)
        c.text("CPU", 28, 214, C.VIOLET, 1)
        busy = ["FILTER", "FFT", "PRINTF", "PID", "OLED", "CALC", "UART",
                "LOGGING"]
        c.text(f"DOING: {busy[f % 8]}", 60, 214, C.VIOLET, 1)
        c.text("DMA MOVES ADC DATA TO RAM, CPU NEVER TOUCHES A BYTE", 28, 232,
               C.MUTED, 1)
        c.text("HAL_ADC_Start_DMA(&hadc1, buf, 8) -> HT + TC INTERRUPT", 28,
               248, C.DIM, 1)
        g.add(c)
    return g



# --------------------------------------------------------------------------- SAR ADC


def sar_adc():
    """逐次逼近：从 bit11 到 bit0，每次猜一个值并比较。"""
    g = Gif(W, H, delay=10)
    vin = 2048                                  # 12 位结果（0.5 VREF）
    for step in range(12):
        bit = 11 - step
        trial = 0
        for b in range(11, bit - 1, -1):
            trial |= 1 << b
        keep = trial <= vin
        result = trial if keep else trial & ~(1 << bit)
        c = Canvas(W, H)
        chrome(c, "SAR ADC", "12 BIT", "T = 12 CLOCKS  ERROR = VREF/4096")
        for i in range(12):
            b = 11 - i
            x = 20 + i * 37
            state = "done" if b > bit else ("test" if b == bit else "todo")
            fill = C.PANEL2 if state == "todo" else C.PANEL
            stroke = C.AMBER if state == "test" else C.STROKE
            c.panel(x, 46, 33, 30, fill, stroke)
            c.text_c(str(b), x + 16, 52, C.MUTED, 1)
            if state == "done":
                c.text_c("1" if (result >> b) & 1 else "0", x + 16, 66,
                         C.GREEN if (result >> b) & 1 else C.DIM, 1)
            elif state == "test":
                c.text_c("?", x + 16, 66, C.AMBER, 1)
        c.panel(20, 92, 216, 104, C.PANEL, C.STROKE)
        c.text("TEST BIT", 32, 108, C.MUTED, 1)
        c.text_c(f"BIT {bit}", 128, 124, C.AMBER, 1)
        c.text("DAC OUTPUT", 32, 146, C.MUTED, 1)
        c.text_c(str(trial), 128, 162, C.CYAN, 1)
        c.text("VIN = 2048", 32, 182, C.MUTED, 1)
        c.panel(248, 92, 216, 104, C.PANEL, C.STROKE)
        c.text("COMPARE", 260, 108, C.MUTED, 1)
        c.text_c("DAC > VIN" if not keep else "DAC <= VIN", 356, 124,
                 C.RED if not keep else C.GREEN, 1)
        c.text_c("CLEAR BIT" if not keep else "KEEP BIT", 356, 146,
                 C.RED if not keep else C.GREEN, 1)
        c.text("REG = " + format(result, "012b"), 260, 170, C.CYAN, 1)
        c.text("RESULT", 20, 216, C.MUTED, 1)
        c.panel(20, 224, 444, 18, C.BG2, C.STROKE)
        c.fill_rect(21, 225, int(442 * result / 4095), 16, C.CYAN)
        c.text(f"{result} / 4095 = {result * 3.3 / 4095:.3f} V", 20, 252,
               C.TEXT, 1)
        c.text("SAR: 12 COMPARISONS FOR 12 BITS, ALWAYS GUESS 1 FIRST", 20,
               268, C.DIM, 1)
        g.add(c)
    return g


BUILDERS = {
    "led-blink": led_blink,
    "pwm-breath": pwm_breath,
    "uart-bits": uart_bits,
    "i2c-timing": i2c_timing,
    "dma-ring": dma_ring,
    "sar-adc": sar_adc,
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

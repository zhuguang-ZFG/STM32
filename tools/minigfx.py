#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
minigfx.py —— 纯标准库的位图绘制 + 动画 GIF 编码器（零依赖）。

为什么要自己写：本仓库要求「任何环境 clone 下来就能重新生成素材」，
所以 GIF 用 Python 标准库手写 GIF89a + LZW 编码，
位图字体是内置的 5×7 ASCII 点阵（因此 GIF 里的文字只能是英文/数字）。

能力
----
* Canvas：像素、矩形、线、圆、文字（5×7 点阵，可放大）
* Gif：多帧 GIF89a，支持循环、帧延时、**差分帧 + 透明索引**（体积小）
* 调色板自动从所有帧收集（最多 255 色 + 1 个透明索引）
"""

from __future__ import annotations

import math
import struct

# --------------------------------------------------------------------------- 颜色


class C:
    BG = (11, 18, 32)
    BG2 = (14, 22, 38)
    PANEL = (17, 28, 49)
    PANEL2 = (22, 35, 60)
    STROKE = (36, 51, 84)
    GRID = (26, 39, 66)
    TEXT = (230, 237, 243)
    MUTED = (147, 164, 192)
    DIM = (100, 116, 139)
    CYAN = (34, 211, 238)
    BLUE = (96, 165, 250)
    GREEN = (52, 211, 153)
    AMBER = (251, 191, 36)
    ORANGE = (251, 146, 60)
    RED = (248, 113, 113)
    VIOLET = (167, 139, 250)
    PINK = (244, 114, 182)
    WHITE = (248, 250, 252)
    GOLD = (226, 178, 60)
    PCB = (18, 58, 46)


def mix(a, b, t):
    """按 t∈[0,1] 混合两种颜色。"""
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def dim(color, k):
    """按比例调暗（用于「熄灭」的 LED）。"""
    return tuple(int(v * k) for v in color)


# --------------------------------------------------------------------------- 字体

FONT = {
    "A": "01110 10001 10001 11111 10001 10001 10001",
    "B": "11110 10001 10001 11110 10001 10001 11110",
    "C": "01110 10001 10000 10000 10000 10001 01110",
    "D": "11110 10001 10001 10001 10001 10001 11110",
    "E": "11111 10000 10000 11110 10000 10000 11111",
    "F": "11111 10000 10000 11110 10000 10000 10000",
    "G": "01110 10001 10000 10111 10001 10001 01111",
    "H": "10001 10001 10001 11111 10001 10001 10001",
    "I": "11111 00100 00100 00100 00100 00100 11111",
    "J": "00111 00010 00010 00010 00010 10010 01100",
    "K": "10001 10010 10100 11000 10100 10010 10001",
    "L": "10000 10000 10000 10000 10000 10000 11111",
    "M": "10001 11011 10101 10101 10001 10001 10001",
    "N": "10001 11001 10101 10011 10001 10001 10001",
    "O": "01110 10001 10001 10001 10001 10001 01110",
    "P": "11110 10001 10001 11110 10000 10000 10000",
    "Q": "01110 10001 10001 10001 10101 10010 01101",
    "R": "11110 10001 10001 11110 10100 10010 10001",
    "S": "01111 10000 10000 01110 00001 00001 11110",
    "T": "11111 00100 00100 00100 00100 00100 00100",
    "U": "10001 10001 10001 10001 10001 10001 01110",
    "V": "10001 10001 10001 10001 10001 01010 00100",
    "W": "10001 10001 10001 10101 10101 11011 10001",
    "X": "10001 10001 01010 00100 01010 10001 10001",
    "Y": "10001 10001 01010 00100 00100 00100 00100",
    "Z": "11111 00001 00010 00100 01000 10000 11111",
    # 小写只补单位常用字形（mA / kHz / us），避免 5×7 大写被读成兆、千的反义
    "a": "00000 00000 01110 00001 01111 10001 01111",
    "d": "00001 00001 01111 10001 10001 10001 01111",
    "e": "00000 00000 01110 10001 11111 10000 01110",
    "h": "10000 10000 11110 10001 10001 10001 10001",
    "i": "00100 00000 01100 00100 00100 00100 01110",
    "k": "10000 10000 10010 10100 11000 10100 10010",
    "m": "00000 00000 11010 10101 10101 10101 10001",
    "n": "00000 00000 11110 10001 10001 10001 10001",
    "o": "00000 00000 01110 10001 10001 10001 01110",
    "r": "00000 00000 10110 11000 10000 10000 10000",
    "s": "00000 00000 01111 10000 01110 00001 11110",
    "t": "00100 00100 11111 00100 00100 00100 00011",
    "u": "00000 00000 10001 10001 10001 10001 01111",
    "z": "00000 00000 11111 00010 00100 01000 11111",
    "0": "01110 10001 10011 10101 11001 10001 01110",
    "1": "00100 01100 00100 00100 00100 00100 01110",
    "2": "01110 10001 00001 00010 00100 01000 11111",
    "3": "11111 00010 00100 00010 00001 10001 01110",
    "4": "00010 00110 01010 10010 11111 00010 00010",
    "5": "11111 10000 11110 00001 00001 10001 01110",
    "6": "00110 01000 10000 11110 10001 10001 01110",
    "7": "11111 00001 00010 00100 01000 01000 01000",
    "8": "01110 10001 10001 01110 10001 10001 01110",
    "9": "01110 10001 10001 01111 00001 00010 01100",
    " ": "00000 00000 00000 00000 00000 00000 00000",
    ".": "00000 00000 00000 00000 00000 01100 01100",
    ",": "00000 00000 00000 00000 01100 00100 01000",
    ":": "00000 01100 01100 00000 01100 01100 00000",
    ";": "00000 01100 01100 00000 01100 00100 01000",
    "-": "00000 00000 00000 11111 00000 00000 00000",
    "+": "00000 00100 00100 11111 00100 00100 00000",
    "_": "00000 00000 00000 00000 00000 00000 11111",
    "/": "00001 00010 00010 00100 01000 01000 10000",
    "\\": "10000 01000 01000 00100 00010 00010 00001",
    "(": "00010 00100 01000 01000 01000 00100 00010",
    ")": "01000 00100 00010 00010 00010 00100 01000",
    "[": "01110 01000 01000 01000 01000 01000 01110",
    "]": "01110 00010 00010 00010 00010 00010 01110",
    "<": "00010 00100 01000 10000 01000 00100 00010",
    ">": "01000 00100 00010 00001 00010 00100 01000",
    "=": "00000 00000 11111 00000 11111 00000 00000",
    "!": "00100 00100 00100 00100 00100 00000 00100",
    "?": "01110 10001 00001 00110 00100 00000 00100",
    "*": "00000 10101 01110 11111 01110 10101 00000",
    "#": "01010 01010 11111 01010 11111 01010 01010",
    "%": "11001 11010 00010 00100 01011 10011 00000",
    "|": "00100 00100 00100 00100 00100 00100 00100",
    "^": "00100 01110 10101 00100 00100 00100 00100",
    "'": "00100 00100 00000 00000 00000 00000 00000",
    '"': "01010 01010 00000 00000 00000 00000 00000",
    "$": "00100 01111 10100 01110 00101 11110 00100",
    "@": "01110 10001 10111 10101 10111 10000 01110",
    "&": "01100 10010 10100 01000 10101 10010 01101",
    "~": "00000 00000 01001 10110 00000 00000 00000",
}


class Canvas:
    def __init__(self, w, h, bg=C.BG):
        self.w, self.h = w, h
        self.buf = bytearray(w * h * 3)
        self.fill_rect(0, 0, w, h, bg)

    # ---------------- 像素 ----------------

    def px(self, x, y, color):
        x, y = int(x), int(y)
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i] = color[0]
            self.buf[i + 1] = color[1]
            self.buf[i + 2] = color[2]

    def get(self, x, y):
        i = (int(y) * self.w + int(x)) * 3
        return (self.buf[i], self.buf[i + 1], self.buf[i + 2])

    # ---------------- 形状 ----------------

    def fill_rect(self, x, y, w, h, color):
        x, y, w, h = int(x), int(y), int(w), int(h)
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        if x0 >= x1 or y0 >= y1:
            return
        row = bytes(color) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.buf[i:i + len(row)] = row

    def rect(self, x, y, w, h, color, t=1):
        self.fill_rect(x, y, w, t, color)
        self.fill_rect(x, y + h - t, w, t, color)
        self.fill_rect(x, y, t, h, color)
        self.fill_rect(x + w - t, y, t, h, color)

    def hline(self, x, y, w, color, t=1):
        self.fill_rect(x, y, w, t, color)

    def vline(self, x, y, h, color, t=1):
        self.fill_rect(x, y, t, h, color)

    def line(self, x0, y0, x1, y1, color, t=1):
        x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            if t <= 1:
                self.px(x0, y0, color)
            else:
                self.fill_rect(x0 - t // 2, y0 - t // 2, t, t, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, color, fill=True):
        r = int(r)
        for dy in range(-r, r + 1):
            dx = int(math.sqrt(max(0, r * r - dy * dy)))
            if fill:
                self.fill_rect(cx - dx, cy + dy, 2 * dx + 1, 1, color)
            else:
                self.px(cx - dx, cy + dy, color)
                self.px(cx + dx, cy + dy, color)

    # ---------------- 文字 ----------------

    def char(self, ch, x, y, color, scale=1):
        rows = FONT.get(ch)
        if rows is None:
            rows = FONT.get(ch.upper())
        if not rows:
            return 6 * scale
        for r, row in enumerate(rows.split()):
            for c, bit in enumerate(row):
                if bit == "1":
                    self.fill_rect(x + c * scale, y + r * scale, scale, scale,
                                   color)
        return 6 * scale

    def text(self, s, x, y, color, scale=1, spacing=1):
        cx = x
        for ch in str(s):
            cx += self.char(ch, cx, y, color, scale) + spacing * scale
        return cx

    def text_w(self, s, scale=1, spacing=1):
        return len(str(s)) * (6 + spacing) * scale

    def text_c(self, s, cx, y, color, scale=1, spacing=1):
        """以 cx 为中心居中绘制。"""
        self.text(s, cx - self.text_w(s, scale, spacing) / 2, y, color, scale,
                  spacing)

    # ---------------- 组件 ----------------

    def panel(self, x, y, w, h, fill=C.PANEL, stroke=C.STROKE, t=1):
        self.fill_rect(x, y, w, h, fill)
        self.rect(x, y, w, h, stroke, t)

    def chip(self, x, y, w, h, label, fill=C.PANEL2, stroke=C.STROKE,
             color=C.CYAN, scale=1):
        self.panel(x, y, w, h, fill, stroke)
        self.text_c(label, x + w / 2, y + h / 2 - 3 * scale, color, scale)

    def led(self, cx, cy, r, color, on=True):
        if on:
            self.circle(cx, cy, r + 3, dim(color, 0.35), True)
            self.circle(cx, cy, r, color, True)
            self.circle(cx - r * 0.3, cy - r * 0.35, max(1, r * 0.28),
                        C.WHITE, True)
        else:
            self.circle(cx, cy, r + 3, dim(color, 0.12), True)
            self.circle(cx, cy, r, dim(color, 0.35), True)

    def waveform(self, x, y, w, h, bits, color, t=1):
        n = len(bits)
        step = w / n
        y0, y1 = y + h - 2, y + 2
        prev = y0 if bits[0] == 0 else y1
        for i, b in enumerate(bits):
            yy = y0 if b == 0 else y1
            self.line(x + i * step, prev, x + i * step, yy, color, t)
            self.line(x + i * step, yy, x + (i + 1) * step, yy, color, t)
            prev = yy

    def header(self, title, tag="", h=30):
        self.fill_rect(0, 0, self.w, h, C.BG2)
        self.fill_rect(0, 0, 3, h, C.CYAN)
        self.hline(0, h, self.w, C.STROKE)
        self.text(title, 12, (h - 7) // 2, C.TEXT, 1)
        if tag:
            tw = self.text_w(tag, 1) + 12
            self.chip(self.w - tw - 10, 6, tw, 18, tag, color=C.CYAN)

    def footer(self, note, h=18):
        self.hline(0, self.h - h, self.w, C.GRID)
        self.text(note, 12, self.h - h + 6, C.DIM, 1)
        self.text("STM32 KB", self.w - self.text_w("STM32 KB") - 12,
                  self.h - h + 6, C.DIM, 1)




# --------------------------------------------------------------------------- GIF 编码


class _BitWriter:
    """GIF 的 LZW 码流是 LSB-first 的位打包。"""

    def __init__(self):
        self.acc = 0
        self.n = 0
        self.out = bytearray()

    def write(self, code, bits):
        self.acc |= code << self.n
        self.n += bits
        while self.n >= 8:
            self.out.append(self.acc & 0xFF)
            self.acc >>= 8
            self.n -= 8

    def flush(self):
        if self.n > 0:
            self.out.append(self.acc & 0xFF)
            self.acc = 0
            self.n = 0
        return bytes(self.out)


def lzw_encode(indices, min_code_size):
    """GIF 变长 LZW 编码（与解码器保持同样的码长增长时机）。"""
    clear = 1 << min_code_size
    end = clear + 1
    code_size = min_code_size + 1
    table = {}
    next_code = end + 1
    bw = _BitWriter()
    bw.write(clear, code_size)
    prefix = None
    for k in indices:
        if prefix is None:
            prefix = k
            continue
        key = (prefix, k)
        if key in table:
            prefix = table[key]
            continue
        bw.write(prefix, code_size)
        if next_code < 4096:
            table[key] = next_code
            next_code += 1
            if next_code > (1 << code_size) and code_size < 12:
                code_size += 1
        else:
            bw.write(clear, code_size)
            table = {}
            next_code = end + 1
            code_size = min_code_size + 1
        prefix = k
    if prefix is not None:
        bw.write(prefix, code_size)
    bw.write(end, code_size)
    return bw.flush()


def _nearest(color, palette):
    best, bd = 0, 1 << 30
    for i, p in enumerate(palette):
        d = ((p[0] - color[0]) ** 2 + (p[1] - color[1]) ** 2
             + (p[2] - color[2]) ** 2)
        if d < bd:
            bd, best = d, i
    return best



class Gif:
    """把若干 Canvas 帧编码成 GIF89a（差分帧 + 透明索引，体积更小）。"""

    def __init__(self, w, h, delay=8, loop=0):
        self.w, self.h = w, h
        self.delay = delay          # 单位 1/100 秒
        self.loop = loop            # 0 = 无限循环
        self.frames = []            # list[bytes(RGB)]

    def add(self, canvas):
        if (canvas.w, canvas.h) != (self.w, self.h):
            raise ValueError("画布尺寸不一致")
        self.frames.append(bytes(canvas.buf))

    # ---------------- 调色板 ----------------

    def _palette(self):
        freq = {}
        for f in self.frames:
            for i in range(0, len(f), 3):
                c = (f[i], f[i + 1], f[i + 2])
                freq[c] = freq.get(c, 0) + 1
        colors = [c for c, _ in sorted(freq.items(), key=lambda kv: -kv[1])]
        self._extra = {}
        if len(colors) > 255:
            keep = colors[:255]
            for c in colors[255:]:
                self._extra[c] = _nearest(c, keep)
            colors = keep
        palette = [(0, 0, 0)] + colors      # 0 号留给透明色
        n = 2
        while n < len(palette):
            n *= 2
        n = max(2, min(256, n))
        while len(palette) < n:
            palette.append((0, 0, 0))
        self._idx = {c: i + 1 for i, c in enumerate(colors)}
        for c, i in self._extra.items():
            self._idx[c] = i + 1
        return palette, n

    # ---------------- 写出 ----------------

    def save(self, path):
        palette, n = self._palette()
        size_bits = {2: 1, 4: 2, 8: 3, 16: 4, 32: 5, 64: 6, 128: 7, 256: 8}[n]
        out = bytearray()
        out += b"GIF89a"
        out += struct.pack("<HH", self.w, self.h)
        out += bytes([0x80 | (7 << 4) | (size_bits - 1), 0, 0])
        for c in palette:
            out += bytes(c)
        if self.loop is not None:
            out += b"\x21\xff\x0bNETSCAPE2.0\x03\x01"
            out += struct.pack("<H", self.loop)
            out += b"\x00"
        min_code = max(2, size_bits)
        prev = None
        for frame in self.frames:
            idx = bytearray(len(frame) // 3)
            for p in range(len(idx)):
                idx[p] = self._idx[(frame[p * 3], frame[p * 3 + 1],
                                    frame[p * 3 + 2])]
            if prev is None:
                x0, y0, x1, y1 = 0, 0, self.w, self.h
                sub = idx
                transparent = False
            else:
                minx, miny, maxx, maxy = self.w, self.h, -1, -1
                for y in range(self.h):
                    row = y * self.w
                    for x in range(self.w):
                        a = (row + x) * 3
                        if frame[a:a + 3] != prev[a:a + 3]:
                            minx = min(minx, x)
                            maxx = max(maxx, x)
                            miny = min(miny, y)
                            maxy = max(maxy, y)
                if maxx < 0:
                    minx = miny = maxx = maxy = 0
                x0, y0 = minx, miny
                x1, y1 = maxx + 1, maxy + 1
                w, h = x1 - x0, y1 - y0
                sub = bytearray(w * h)
                for y in range(y0, y1):
                    for x in range(x0, x1):
                        a = (y * self.w + x) * 3
                        if frame[a:a + 3] == prev[a:a + 3]:
                            sub[(y - y0) * w + (x - x0)] = 0   # 透明
                        else:
                            sub[(y - y0) * w + (x - x0)] = idx[y * self.w + x]
                transparent = True
            packed = 0x05 if transparent else 0x04   # 处置方式 1：保留上一帧
            out += (b"\x21\xf9\x04" + bytes([packed])
                    + struct.pack("<H", self.delay) + b"\x00\x00")
            out += (b"\x2c" + struct.pack("<HHHH", x0, y0, x1 - x0, y1 - y0)
                    + b"\x00")
            out += bytes([min_code])
            data = lzw_encode(sub, min_code)
            for i in range(0, len(data), 255):
                blk = data[i:i + 255]
                out += bytes([len(blk)]) + blk
            out += b"\x00"
            prev = frame
        out += b"\x3b"
        with open(path, "wb") as f:
            f.write(out)
        return len(out)

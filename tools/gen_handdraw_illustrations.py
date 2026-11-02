#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate one hand-drawn conceptual illustration for every book chapter.

The drawings use the book palette but deliberately avoid the card-and-box visual
grammar of technical diagrams.  Each first frame is complete for PDF output;
small CSS motion gives the web edition a second animation layer.
"""

from __future__ import annotations

import json
import math
import os
import sys
import xml.dom.minidom

from svgkit import Svg, T


W, H = 900, 560


class Sketch:
    def __init__(self, chapter: int, title: str, aria: str, label: str | None = None):
        self.s = Svg(W, H, aria)
        self.chapter = chapter
        self.title = title
        self.s.add_style("""
@keyframes hd-float{0%,100%{transform:translateY(0)}50%{transform:translateY(-5px)}}
@keyframes hd-sway{0%,100%{transform:rotate(-1deg)}50%{transform:rotate(1deg)}}
@keyframes hd-pulse{0%,100%{opacity:.58}50%{opacity:1}}
@keyframes hd-flow{from{stroke-dashoffset:0}to{stroke-dashoffset:-24px}}
.hd-float{animation:hd-float 3.8s ease-in-out infinite;transform-origin:center}
.hd-sway{animation:hd-sway 4.6s ease-in-out infinite;transform-origin:center}
.hd-pulse{animation:hd-pulse 2.4s ease-in-out infinite}
.hd-flow{stroke-dasharray:12 12;animation:hd-flow 1.8s linear infinite}
@media (prefers-reduced-motion:reduce){*{animation:none!important}}
""")
        self.s.rect(0, 0, W, H, fill=T.BG)
        self.s.text(38, 48, label or f"CH {chapter + 1:02d}", size=12, fill=T.CYAN,
                    weight="800", mono=True, ls="1.4")
        self.s.text(862, 48, "FA-002 · continuous-line", size=10.5,
                    fill=T.MUTED, anchor="end", mono=True)
        self.s.path("M38 66 C190 60 335 73 470 65 S735 59 862 66",
                    stroke=T.GRID, sw=1)

    def line(self, x1, y1, x2, y2, color=T.STROKE, sw=2, cls=None,
             dash=None, opacity=1):
        self.s.line(x1 + 1.8, y1 + 1.2, x2 + 1.8, y2 + 1.2,
                    stroke=color, sw=1, opacity=.22)
        self.s.line(x1, y1, x2, y2, stroke=color, sw=sw, cls=cls,
                    dash=dash, opacity=opacity)

    def path(self, d, color=T.STROKE, sw=2, cls=None, fill="none",
             opacity=1, dash=None):
        self.s.path(d, fill=fill, stroke=color, sw=sw, cls=cls,
                    opacity=opacity, dash=dash)

    def circle(self, x, y, r, color=T.STROKE, fill="none", sw=2, cls=None):
        self.s.circle(x + 2, y + 1, r, fill="none", stroke=color, sw=1,
                      opacity=.2)
        self.s.circle(x, y, r, fill=fill, stroke=color, sw=sw, cls=cls)

    def blob(self, d, fill, color=T.STROKE, cls=None):
        self.s.path(d, fill=fill, stroke=color, sw=2, cls=cls, opacity=.92)

    def label(self, x, y, text, color=T.TEXT, size=11, anchor="middle"):
        self.s.text(x, y, text, size=size, fill=color, anchor=anchor,
                    mono=True, weight="700")

    def arrow(self, x1, y1, x2, y2, color=T.CYAN, cls="hd-flow"):
        self.s.arrow(x1, y1, x2, y2, color=color, sw=2, head=8, cls=cls)

    def footer(self):
        self.s.path("M38 510 C230 503 420 517 610 509 S790 504 862 510",
                    stroke=T.GRID, sw=1)
        self.s.text(38, 538,
                    "Conceptual Continuous-Line Editorial · Prussian Blue / Sage / Naples Yellow",
                    size=10.5, fill=T.MUTED)
        self.s.text(862, 538, "自绘矢量动画 · CC BY 4.0", size=10.5,
                    fill=T.MUTED, anchor="end")
        return self.s


def person(k: Sketch, x: float, y: float, scale=1.0, color=T.STROKE,
           pose="walk", cls=None):
    k.circle(x, y - 36 * scale, 10 * scale, color=color, fill=T.BG, cls=cls)
    k.path(f"M{x} {y-25*scale} C{x-4*scale} {y-6*scale} {x+4*scale} {y+8*scale} {x} {y+28*scale}",
           color=color, cls=cls)
    if pose == "walk":
        k.line(x, y - 8 * scale, x - 18 * scale, y + 7 * scale, color=color)
        k.line(x + 1 * scale, y - 7 * scale, x + 19 * scale, y - 16 * scale, color=color)
        k.line(x, y + 28 * scale, x - 16 * scale, y + 50 * scale, color=color)
        k.line(x, y + 28 * scale, x + 18 * scale, y + 45 * scale, color=color)
    else:
        k.line(x, y - 8 * scale, x - 20 * scale, y - 4 * scale, color=color)
        k.line(x, y - 8 * scale, x + 20 * scale, y - 4 * scale, color=color)
        k.line(x, y + 28 * scale, x - 12 * scale, y + 50 * scale, color=color)
        k.line(x, y + 28 * scale, x + 12 * scale, y + 50 * scale, color=color)


def chip(k: Sketch, x, y, w=150, h=100, color=T.CYAN, cls=None):
    k.blob(f"M{x} {y+8} Q{x+3} {y} {x+12} {y} L{x+w-8} {y} Q{x+w} {y+2} {x+w} {y+12} "
           f"L{x+w} {y+h-8} Q{x+w-2} {y+h} {x+w-12} {y+h} L{x+8} {y+h} Q{x} {y+h-2} {x} {y+h-12} Z",
           T.PANEL2, color, cls)
    for i in range(5):
        yy = y + 17 + i * 17
        k.line(x - 12, yy, x, yy, color=color)
        k.line(x + w, yy, x + w + 12, yy, color=color)
    k.path(f"M{x+28} {y+52} C{x+50} {y+20} {x+78} {y+82} {x+118} {y+42}",
           color=color, sw=1.5, cls=cls)


def gear(k: Sketch, x, y, r, color=T.AMBER, cls="hd-sway"):
    pts = []
    for i in range(24):
        a = i * math.pi / 12
        rr = r * (1.16 if i % 2 == 0 else 1)
        pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
    k.s.poly(pts, fill=T.BG2, stroke=color, sw=2, cls=cls)
    k.circle(x, y, r * .35, color=color, fill=T.BG, cls=cls)


def wave(k: Sketch, x, y, width, amp=25, color=T.CYAN, cls=None):
    d = [f"M{x} {y}"]
    steps = 8
    for i in range(steps):
        x0 = x + width * i / steps
        x1 = x + width * (i + .5) / steps
        x2 = x + width * (i + 1) / steps
        d.append(f"Q{x1} {y + (amp if i % 2 == 0 else -amp)} {x2} {y}")
    k.path(" ".join(d), color=color, cls=cls)


def chapter_scene(ch: int, title: str, aria: str, scene: str) -> Svg:
    k = Sketch(ch, title, aria)
    ground = "M52 455 C180 443 292 468 420 451 S690 440 848 454"
    k.path(ground, color=T.GRID, sw=1.5)

    if scene == "learning":
        k.path("M90 420 C180 330 230 390 310 280 S430 210 520 250 S660 190 790 120",
               color=T.CYAN, cls="hd-flow")
        person(k, 115, 395, .85, pose="walk", cls="hd-float")
        k.blob("M735 110 Q780 85 825 115 L810 165 Q770 145 735 170 Z", T.PANEL2, T.GREEN, "hd-sway")
        k.circle(325, 274, 22, T.AMBER, T.PANEL, cls="hd-pulse")
        k.line(325, 296, 325, 340, T.AMBER)
    elif scene == "toolchain":
        k.blob("M75 170 Q145 132 215 170 L205 310 Q142 342 75 305 Z", T.PANEL2, T.CYAN)
        k.path("M105 205 C132 183 160 220 188 194 M105 240 L182 240 M105 274 L165 274", T.CYAN)
        gear(k, 355, 246, 48, T.AMBER)
        gear(k, 470, 320, 34, T.GREEN)
        chip(k, 635, 205, 150, 105, T.VIOLET, "hd-float")
        k.arrow(220, 240, 300, 240); k.arrow(510, 280, 620, 255)
    elif scene == "clock":
        k.circle(165, 250, 62, T.AMBER, T.PANEL)
        for i in range(8):
            a = i * math.pi / 4
            k.line(165 + 45 * math.cos(a), 250 + 45 * math.sin(a),
                   165 + 56 * math.cos(a), 250 + 56 * math.sin(a), T.AMBER)
        k.line(165, 250, 198, 226, T.RED); k.line(165, 250, 147, 211, T.CYAN)
        k.path("M230 250 C315 250 285 140 390 170 S480 315 565 245 S690 150 800 190", T.CYAN, cls="hd-flow")
        for x, y, c in [(390,170,T.GREEN),(565,245,T.VIOLET),(800,190,T.RED)]:
            k.circle(x, y, 25, c, T.BG2, cls="hd-pulse")
    elif scene == "gpio":
        chip(k, 100, 220, 160, 110, T.CYAN)
        k.path("M272 275 C360 275 365 165 455 170", T.AMBER)
        k.circle(480, 170, 24, T.RED, T.PANEL, cls="hd-pulse")
        k.path("M455 170 C445 145 450 120 480 112 C510 120 515 145 505 170", T.RED)
        k.path("M272 300 C360 300 390 370 490 365", T.GREEN)
        person(k, 610, 350, .8, T.STROKE, pose="stand")
        k.circle(700, 335, 18, T.VIOLET, T.PANEL2, cls="hd-pulse")
        k.line(626, 344, 680, 338, T.VIOLET)
    elif scene == "interrupt":
        k.circle(160, 275, 60, T.AMBER, T.PANEL)
        k.circle(160, 275, 18, T.RED, T.RED, cls="hd-pulse")
        k.path("M218 275 C300 275 300 155 400 155 S520 265 610 210", T.CYAN, cls="hd-flow")
        for x, y, num, c in [(400,155,"1",T.RED),(610,210,"2",T.GREEN),(730,320,"3",T.VIOLET)]:
            k.circle(x, y, 35, c, T.BG2); k.label(x, y+5, num, c, 16)
        k.arrow(635, 230, 710, 300, T.VIOLET)
    elif scene == "timer":
        gear(k, 200, 260, 74, T.AMBER)
        gear(k, 355, 260, 45, T.GREEN)
        k.path("M420 260 C455 260 465 340 510 340", T.CYAN)
        wave(k, 510, 340, 280, 50, T.CYAN, "hd-flow")
        k.line(520, 405, 790, 405, T.GRID)
        k.path("M520 405 L520 375 L655 375 L655 405 L790 405", T.RED)
    elif scene == "uart":
        person(k, 135, 320, .8, T.STROKE, pose="stand")
        person(k, 765, 320, .8, T.STROKE, pose="stand")
        k.path("M190 280 C310 190 420 350 540 255 S660 210 710 275", T.CYAN, cls="hd-flow")
        bits = "01010101"
        for i, b in enumerate(bits):
            k.circle(260 + i * 52, 280 + (18 if i % 2 else -12), 17,
                     T.AMBER if b == "1" else T.GREEN, T.BG2)
            k.label(260 + i * 52, 285 + (18 if i % 2 else -12), b, T.TEXT, 11)
    elif scene == "i2c":
        k.path("M80 260 C230 205 360 315 520 250 S720 190 830 245", T.CYAN, cls="hd-flow")
        k.path("M80 315 C230 260 360 370 520 305 S720 245 830 300", T.GREEN, cls="hd-flow")
        for i, (x, addr) in enumerate([(250,"3C"),(470,"50"),(690,"68")]):
            k.blob(f"M{x-40} 150 L{x+40} 150 L{x+55} 210 L{x-55} 210 Z", T.PANEL2,
                   [T.AMBER,T.VIOLET,T.RED][i], "hd-float")
            k.label(x, 190, addr, [T.AMBER,T.VIOLET,T.RED][i], 12)
            k.line(x, 210, x, 250, [T.AMBER,T.VIOLET,T.RED][i])
    elif scene == "spi":
        person(k, 135, 335, .8, T.STROKE, pose="stand")
        person(k, 760, 335, .8, T.STROKE, pose="stand")
        for i in range(5):
            x = 250 + i * 90
            k.blob(f"M{x-28} {210+(i%2)*55} L{x+28} {210+(i%2)*55} L{x+34} {252+(i%2)*55} L{x-34} {252+(i%2)*55} Z",
                   T.PANEL2, T.CYAN if i % 2 == 0 else T.AMBER, "hd-float")
            k.label(x, 238+(i%2)*55, "9F" if i == 0 else f"{[0,239,64,23,255][i]:02X}", T.TEXT, 10)
        k.arrow(190, 250, 690, 250, T.CYAN); k.arrow(690, 330, 190, 330, T.GREEN)
    elif scene == "adc":
        k.blob("M90 155 Q155 120 220 155 L205 380 Q155 410 105 380 Z", T.PANEL2, T.CYAN)
        k.path("M105 305 Q155 270 205 305 L205 380 Q155 410 105 380 Z", fill=T.PANEL2, color=T.GREEN)
        k.line(280, 390, 280, 120, T.STROKE)
        for i in range(6):
            yy = 390 - i * 48
            k.line(280, yy, 305, yy, T.STROKE)
        k.path("M335 350 L390 350 L390 300 L445 300 L445 250 L500 250 L500 200 L555 200 L555 150 L610 150", T.AMBER)
        chip(k, 650, 210, 130, 95, T.VIOLET, "hd-float")
    elif scene == "dma":
        k.circle(110, 260, 34, T.AMBER, T.PANEL)
        k.path("M144 260 C235 205 290 330 380 270 S520 205 600 270", T.CYAN, cls="hd-flow")
        for i in range(8):
            x = 610 + (i % 4) * 55
            y = 185 + (i // 4) * 100
            k.blob(f"M{x} {y} l42 0 l5 42 l-47 0 Z", T.PANEL2,
                   T.GREEN if i < 4 else T.VIOLET, "hd-float")
    elif scene == "watchdog":
        k.circle(420, 260, 110, T.AMBER, T.PANEL)
        for i in range(12):
            a = i * math.pi / 6
            k.line(420+82*math.cos(a),260+82*math.sin(a),420+98*math.cos(a),260+98*math.sin(a),T.AMBER)
        k.line(420,260,475,215,T.RED); k.line(420,260,420,195,T.CYAN)
        k.path("M225 320 C210 235 270 170 335 202 C310 275 320 350 268 380 Z", T.STROKE)
        k.circle(270, 215, 18, T.STROKE, T.BG)
        k.circle(302, 215, 18, T.STROKE, T.BG)
        k.circle(270, 215, 4, T.RED, T.RED, cls="hd-pulse")
        k.circle(302, 215, 4, T.RED, T.RED, cls="hd-pulse")
        k.path("M510 350 C590 410 695 390 760 320", T.GREEN, cls="hd-flow")
    elif scene == "iap":
        k.blob("M95 160 L315 160 L315 390 L95 390 Z", T.PANEL2, T.CYAN)
        k.blob("M590 160 L810 160 L810 390 L590 390 Z", T.PANEL2, T.GREEN)
        k.path("M315 300 C385 220 520 220 590 300", T.AMBER, sw=2)
        k.path("M315 320 C385 240 520 240 590 320", T.AMBER, sw=2)
        person(k, 360, 275, .65, T.STROKE, pose="walk", cls="hd-float")
        k.arrow(390, 270, 545, 270, T.VIOLET)
        k.circle(700, 245, 44, T.GREEN, T.BG, cls="hd-pulse")
        k.path("M680 245 L696 261 L726 220", T.GREEN)
    elif scene == "can":
        k.path("M80 250 C250 180 420 315 820 220", T.CYAN, cls="hd-flow")
        k.path("M80 315 C250 245 420 380 820 285", T.GREEN, cls="hd-flow")
        for x, ident, c in [(180,"100",T.RED),(365,"200",T.AMBER),(640,"123",T.VIOLET)]:
            k.blob(f"M{x-55} 125 Q{x} 92 {x+55} 125 L{x+45} 200 Q{x} 218 {x-45} 200 Z", T.PANEL2, c, "hd-float")
            k.label(x, 170, ident, c, 12)
            k.line(x, 200, x, 245, c)
    elif scene == "usb":
        k.blob("M100 165 Q185 125 270 165 L260 350 Q185 385 110 350 Z", T.PANEL2, T.CYAN)
        k.circle(185, 220, 35, T.AMBER, T.BG)
        k.path("M165 220 L180 235 L210 195", T.GREEN)
        k.path("M275 260 C355 210 430 310 505 250 S650 190 770 250", T.VIOLET, cls="hd-flow")
        for i, (x, n) in enumerate([(350,"18"),(500,"67"),(650,"EP")]):
            k.circle(x, 250, 28, [T.CYAN,T.GREEN,T.RED][i], T.BG2, cls="hd-pulse")
            k.label(x, 255, n, T.TEXT, 10)
    elif scene == "rtos":
        k.circle(450, 285, 105, T.CYAN, T.PANEL)
        for i, (lab, c) in enumerate([("A",T.RED),("B",T.GREEN),("C",T.AMBER),("Q",T.VIOLET)]):
            a = -math.pi/2 + i * math.pi/2
            x, y = 450+170*math.cos(a), 285+150*math.sin(a)
            k.circle(x, y, 42, c, T.BG2, cls="hd-float")
            k.label(x, y+5, lab, c, 16)
            k.arrow(x + 42*math.cos(a+math.pi), y+42*math.sin(a+math.pi),
                    450+108*math.cos(a),285+108*math.sin(a),c)
        k.path("M410 285 C430 245 470 245 490 285 C470 325 430 325 410 285", T.CYAN, cls="hd-sway")
    elif scene == "lowpower":
        chip(k, 320, 245, 210, 125, T.GREEN, "hd-float")
        k.path("M285 230 C360 165 500 165 570 235 L545 335 C470 300 365 305 300 345 Z",
               color=T.CYAN, fill=T.PANEL2, opacity=.75)
        k.path("M650 150 C700 105 755 130 748 185 C725 230 675 220 660 190 C690 195 712 180 720 155 C690 172 668 165 650 150 Z", T.AMBER, fill=T.PANEL)
        wave(k, 110, 420, 680, 34, T.VIOLET, "hd-flow")
    elif scene == "fault":
        k.blob("M125 180 Q230 125 335 180 L320 360 Q230 405 140 355 Z", T.PANEL2, T.RED)
        k.path("M180 225 L285 325 M285 225 L180 325", T.RED)
        k.circle(500, 245, 75, T.CYAN, T.BG, cls="hd-sway")
        k.line(555, 300, 650, 395, T.CYAN, sw=2)
        k.path("M448 245 C475 205 510 285 550 235", T.VIOLET, cls="hd-flow")
        k.blob("M675 175 L805 175 L790 335 L690 335 Z", T.PANEL2, T.GREEN)
        k.path("M700 220 L770 220 M700 255 L750 255 M700 290 L780 290", T.GREEN)
    elif scene == "faq":
        person(k, 150, 360, .8, T.STROKE, pose="stand")
        signs = [(315,160,"?",T.RED),(470,260,"!",T.AMBER),(620,155,"→",T.GREEN),(760,300,"✓",T.CYAN)]
        for x,y,t,c in signs:
            k.blob(f"M{x-48} {y-38} L{x+48} {y-38} L{x+55} {y+38} L{x-55} {y+38} Z", T.PANEL2,c,"hd-float")
            k.label(x,y+8,t,c,24)
            k.line(x,y+38,x,y+88,c)
        k.path("M185 350 C280 345 275 240 315 210 S430 360 470 310 S580 220 620 205 S710 350 760 345", T.CYAN, cls="hd-flow")
    elif scene == "projects":
        k.blob("M90 345 Q220 245 350 345 L335 410 Q220 445 105 410 Z", T.PANEL2, T.AMBER)
        k.path("M145 340 L180 250 L220 340 M235 340 L285 220 L320 340", T.STROKE)
        for x,y,c in [(425,180,T.CYAN),(560,300,T.GREEN),(710,170,T.VIOLET),(785,350,T.RED)]:
            k.circle(x,y,38,c,T.BG2,cls="hd-float")
        k.path("M335 350 C430 345 395 210 425 210 S515 330 560 330 S650 190 710 205 S750 365 785 380", T.CYAN, cls="hd-flow")
    elif scene == "resources":
        k.path("M115 390 L115 150 L330 150 L330 390", T.CYAN)
        for y in [205,265,325]: k.line(115,y,330,y,T.CYAN)
        for i,(x,y,c) in enumerate([(145,165,T.RED),(205,165,T.GREEN),(265,165,T.AMBER),(155,225,T.VIOLET),(230,225,T.CYAN)]):
            k.blob(f"M{x} {y} l38 0 l0 42 l-38 0 Z", T.PANEL2,c)
        k.circle(555,250,85,T.AMBER,T.BG,cls="hd-sway")
        k.line(555,250,620,205,T.RED)
        k.path("M620 205 C680 165 740 190 790 135", T.CYAN, cls="hd-flow")
    elif scene == "boards":
        chip(k, 130, 170, 240, 170, T.GREEN, "hd-float")
        k.circle(180,215,20,T.AMBER,T.PANEL); k.circle(315,215,20,T.AMBER,T.PANEL)
        k.path("M160 290 C220 250 280 330 340 275", T.CYAN)
        k.circle(590,250,95,T.CYAN,T.BG,cls="hd-sway")
        k.line(657,317,760,420,T.CYAN)
        k.path("M535 245 C565 205 610 295 650 235", T.VIOLET)
    elif scene == "simulation":
        k.blob("M85 145 L380 145 L360 375 L105 375 Z", T.PANEL2, T.CYAN)
        k.path("M120 330 C175 245 260 350 330 220", T.CYAN, cls="hd-flow")
        k.blob("M540 145 L835 145 L815 375 L560 375 Z", T.BG2, T.GREEN)
        chip(k, 615, 215, 145, 100, T.GREEN, "hd-float")
        k.path("M380 260 C430 215 490 215 540 260", T.AMBER, cls="hd-flow")
        k.circle(460,260,28,T.AMBER,T.BG,cls="hd-pulse")
    elif scene == "g0":
        chip(k, 120, 180, 210, 150, T.CYAN)
        k.path("M330 255 C420 255 430 150 520 150", T.AMBER, cls="hd-flow")
        k.path("M330 270 C420 270 430 370 520 370", T.VIOLET, cls="hd-flow")
        k.circle(550,150,38,T.AMBER,T.BG2); k.label(550,155,"BOOT",T.AMBER,10)
        k.circle(550,370,38,T.VIOLET,T.BG2); k.label(550,375,"SWD",T.VIOLET,10)
        k.path("M590 150 C670 150 700 235 790 235 M590 370 C670 370 700 285 790 285", T.GREEN, cls="hd-flow")
    elif scene == "l4":
        chip(k, 335, 220, 230, 130, T.GREEN, "hd-float")
        k.path("M270 235 C210 185 145 190 100 235 M270 330 C190 380 130 365 95 330", T.CYAN, cls="hd-flow")
        k.circle(125,235,34,T.AMBER,T.BG2); k.label(125,240,"SLEEP",T.AMBER,9)
        k.circle(125,330,34,T.VIOLET,T.BG2); k.label(125,335,"STOP2",T.VIOLET,9)
        wave(k, 600, 400, 220, 40, T.RED, "hd-flow")
        k.path("M600 305 C660 255 730 340 810 260", T.CYAN, cls="hd-flow")
    elif scene == "h7":
        for i,(x,y,c) in enumerate([(110,155,T.CYAN),(340,155,T.GREEN),(570,155,T.VIOLET),(340,335,T.AMBER)]):
            k.blob(f"M{x} {y} Q{x+85} {y-20} {x+170} {y} L{x+160} {y+105} Q{x+85} {y+125} {x+10} {y+105} Z", T.PANEL2,c,"hd-float")
        k.arrow(280,210,335,210,T.CYAN); k.arrow(510,210,565,210,T.GREEN)
        k.arrow(650,275,500,345,T.VIOLET); k.arrow(340,345,285,265,T.AMBER)
        k.circle(790,315,48,T.RED,T.BG,cls="hd-pulse"); k.label(790,320,"480",T.RED,14)
    elif scene == "spl":
        k.path("M100 390 L100 145 L340 145 L340 390", T.AMBER)
        k.path("M560 390 L560 145 L800 145 L800 390", T.CYAN)
        for y in [210,275,340]:
            k.line(100,y,340,y,T.AMBER); k.line(560,y,800,y,T.CYAN)
        k.blob("M155 235 L285 235 L275 320 L165 320 Z", T.PANEL2,T.AMBER)
        k.blob("M615 235 L745 235 L735 320 L625 320 Z", T.PANEL2,T.CYAN)
        person(k, 440, 335, .75, T.STROKE, pose="walk", cls="hd-float")
        k.arrow(360,275,525,275,T.GREEN)
    elif scene == "network":
        k.blob("M70 190 Q145 150 220 190 L210 315 Q145 345 80 315 Z", T.PANEL2,T.CYAN)
        k.blob("M680 190 Q755 150 830 190 L820 315 Q755 345 690 315 Z", T.PANEL2,T.GREEN)
        k.path("M220 250 C330 125 470 390 680 250", T.VIOLET, cls="hd-flow")
        for i,(x,t,c) in enumerate([(300,"ARP",T.AMBER),(440,"TCP",T.CYAN),(570,"TLS",T.RED)]):
            k.circle(x,250+(i%2)*65,30,c,T.BG2,cls="hd-float"); k.label(x,255+(i%2)*65,t,c,9)
        k.path("M220 290 C350 420 520 110 680 290", T.GREEN, cls="hd-flow")
    else:  # system
        k.path("M80 410 C180 330 250 390 330 300 S450 160 550 245 S690 350 820 170", T.CYAN, cls="hd-flow")
        for i,(x,y,c) in enumerate([(150,340,T.AMBER),(330,300,T.GREEN),(520,230,T.VIOLET),(700,300,T.RED),(820,170,T.CYAN)]):
            k.blob(f"M{x-52} {y-42} Q{x} {y-65} {x+52} {y-42} L{x+45} {y+38} Q{x} {y+58} {x-45} {y+38} Z", T.PANEL2,c,"hd-float")
            k.label(x,y+5,["IRQ","TASK","DRV","NET","APP"][i],c,10)

    return k.footer()


CHAPTERS = [
    (0, "Learning path", "从第一盏灯走到能验收的系统",
     "A learner follows a winding path from a first light to a verified system", "learning"),
    (1, "Toolchain", "源码穿过工具和齿轮落进芯片",
     "Source code passes through tools and gears into a microcontroller", "toolchain"),
    (2, "Clock and memory", "时钟分叉成总线和存储区",
     "A clock branches into buses and memory regions", "clock"),
    (3, "GPIO", "一只引脚点亮灯，也读回按键",
     "A microcontroller pin drives a lamp and reads a button", "gpio"),
    (4, "Interrupt", "门铃事件进入优先级队列",
     "A doorbell event enters a priority queue", "interrupt"),
    (5, "Timer", "齿轮咬合出可测量的波形",
     "Clockwork gears create a measured PWM waveform", "timer"),
    (6, "UART", "两个人隔着一条线交换成帧的比特",
     "Two people exchange a framed stream of bits", "uart"),
    (7, "I2C", "两条开漏线依次拜访有地址的设备",
     "Two shared open-drain lines visit addressed devices", "i2c"),
    (8, "SPI", "每个时钟沿，两边交换一个字节",
     "Two sides exchange bytes on every clock", "spi"),
    (9, "ADC", "电压倒进桶里，变成二进制台阶",
     "A voltage bucket becomes a binary staircase", "adc"),
    (10, "DMA", "传送带把采样搬进环形缓冲区",
     "A conveyor moves samples into a circular buffer", "dma"),
    (11, "RTC and watchdog", "看门狗盯着时钟和复位留下的痕迹",
     "A watchdog watches a clock and the restart trail", "watchdog"),
    (12, "Flash and IAP", "校验过的镜像跨过带闸门的桥",
     "A verified image crosses a guarded bridge", "iap"),
    (13, "CAN", "多个节点在一条差分路上仲裁",
     "Several nodes arbitrate on one differential road", "can"),
    (14, "USB", "设备在主机桌前通过枚举检查点",
     "A device passes enumeration checkpoints at a host desk", "usb"),
    (15, "FreeRTOS", "任务绕着调度器转，交换事件",
     "Tasks orbit a scheduler and exchange events", "rtos"),
    (16, "Low power", "睡着的芯片在电池月亮下短暂醒来",
     "A sleeping chip wakes briefly under a battery moon", "lowpower"),
    (17, "Debug", "故障现场在证据消失前被检查",
     "A fault scene is inspected before evidence disappears", "fault"),
    (18, "FAQ", "技术员沿着症状路牌逐个边界排查",
     "A technician follows symptom signposts one boundary at a time", "faq"),
    (19, "Projects", "工作台把证据门拼成产品",
     "A workshop connects evidence gates into a product", "projects"),
    (20, "Resources", "手册图书馆和罗盘为工程问题引路",
     "A manual library and compass route engineering questions", "resources"),
    (21, "Board maps", "像解剖标本一样检查一块板",
     "A board is inspected like an anatomical specimen", "boards"),
    (22, "Simulation", "同一份固件从模型跨到真实工作台",
     "One firmware image crosses from a model into a real bench", "simulation"),
    (23, "STM32G0", "共用的 BOOT 和 SWCLK 脚分成两条受控路径",
     "A shared BOOT and SWCLK pin splits into two controlled paths", "g0"),
    (24, "STM32L4", "低功耗设备睡下、醒来、恢复时钟并报告",
     "A low-power device sleeps, wakes, restores clocks, and reports", "l4"),
    (25, "STM32H7", "电源域和时钟组成一座高性能城市",
     "Power domains and clocks form a high-performance city", "h7"),
    (26, "SPL", "冻结的旧库一格一格迁移",
     "A frozen old library is migrated shelf by shelf", "spl"),
    (27, "Network", "数据包穿过 ARP、TCP、TLS 与应用边界",
     "Packets cross ARP, TCP, TLS, and application boundaries", "network"),
    (28, "System", "中断、任务、驱动、网络与应用组成一套系统",
     "Interrupts, tasks, drivers, networks, and apps form one system", "system"),
]

PARTS = (
    (1, "工作台把构建、烧录和测量连成一个闭环",
     "A workbench loop connects build, flash, and measurement", "loop"),
    (2, "芯片的引脚分成事件、时基和波形三条路",
     "Chip pins branch into events, time base, and waveforms", "pins"),
    (3, "字节沿着传送带进入环形缓冲区",
     "Bytes travel along a conveyor into a ring buffer", "conveyor"),
    (4, "四道工程门把可靠性、升级、连接和调度串起来",
     "Four engineering gates chain reliability, update, link, and scheduling", "gates"),
    (5, "工作台把手册、项目盒和放大镜摆在一起",
     "A bench places manuals, a project box, and a magnifier together", "delivery"),
    (6, "三颗芯片在迁移路上交换手册和旧库",
     "Three chips trade manuals and a legacy library on the migration road", "migration"),
    (7, "硬件、内核、服务和应用叠成一套系统",
     "Hardware, kernel, services, and applications stack into one system", "stack"),
)


def part_scene(index: int, zh: str, aria: str, scene: str) -> Svg:
    """Return one hand-drawn plate for a part divider."""
    k = Sketch(index - 1, aria, aria, label=f"PART {index:02d}")
    k.path("M52 455 C180 443 292 468 420 451 S690 440 848 454",
           color=T.GRID, sw=1.5)
    if scene == "loop":
        k.path("M150 360 L820 360", color=T.GRID, sw=1.5)
        person(k, 120, 400, .85)
        gear(k, 300, 285, 42)
        chip(k, 455, 235, 160, 100)
        wave(k, 690, 300, 140, 20, T.GREEN)
        k.path("M195 330 C260 230 340 220 410 265 S560 355 650 295 S760 215 820 265",
               T.CYAN, cls="hd-flow")
        k.label(300, 390, "BUILD")
        k.label(535, 390, "FLASH")
        k.label(760, 390, "MEASURE")
    elif scene == "pins":
        chip(k, 230, 215, 240, 155)
        k.arrow(480, 250, 640, 180, T.RED)
        k.arrow(480, 292, 640, 292, T.AMBER)
        k.arrow(480, 334, 640, 410, T.GREEN)
        k.circle(690, 170, 28, T.RED, T.PANEL)
        k.label(690, 175, "IRQ", T.RED, size=10)
        gear(k, 690, 292, 34, T.AMBER)
        wave(k, 640, 410, 150, 20, T.GREEN)
        k.label(690, 225, "EVENT", T.RED, size=9)
        k.label(690, 345, "TIME", T.AMBER, size=9)
        k.label(690, 470, "WAVE", T.GREEN, size=9)
    elif scene == "conveyor":
        k.path("M80 400 L820 400", color=T.GRID, sw=2)
        for i in range(6):
            x = 150 + i * 100
            k.s.rect(x, 366, 58, 34, fill=T.PANEL2, stroke=T.CYAN, rx=4, sw=2)
            k.label(x + 29, 390, "B", T.CYAN, size=9)
        k.blob("M110 220 Q175 190 235 220 L225 320 Q170 348 120 320 Z",
               T.PANEL, T.AMBER)
        k.arrow(165, 330, 300, 380, T.AMBER)
        k.label(170, 470, "SAMPLE", T.AMBER, size=9)
        k.circle(700, 270, 68, T.VIOLET, T.PANEL2)
        k.circle(700, 270, 42, T.VIOLET, T.BG)
        for i in range(8):
            a = i * math.pi / 4
            k.circle(700 + 55 * math.cos(a), 270 + 55 * math.sin(a), 4,
                     T.VIOLET, T.PANEL)
        k.arrow(820, 380, 760, 330, T.VIOLET)
        k.label(700, 350, "RING", T.VIOLET, size=10)
    elif scene == "gates":
        k.path("M150 400 L820 400", T.CYAN, cls="hd-flow")
        person(k, 100, 400, .8)
        for x, label, color in (
            (300, "POWER", T.RED),
            (450, "UPDATE", T.AMBER),
            (600, "LINK", T.CYAN),
            (750, "SCHEDULE", T.GREEN),
        ):
            k.line(x - 34, 300, x - 34, 430, color)
            k.line(x + 34, 300, x + 34, 430, color)
            k.line(x - 34, 300, x + 34, 300, color)
            if label == "POWER":
                k.path(f"M{x+5} 334 L{x-8} 364 L{x+2} 364 L{x-9} 396", color)
            elif label == "UPDATE":
                k.path(f"M{x-15} 370 A15 15 0 1 1 {x+3} 383", color)
                k.s.poly([(x + 3, 383), (x - 5, 380), (x + 1, 373)],
                         fill=color, sw=1)
            elif label == "LINK":
                k.circle(x - 9, 365, 9, color, T.BG)
                k.circle(x + 9, 365, 9, color, T.BG)
            elif label == "SCHEDULE":
                k.circle(x, 365, 16, color, T.BG)
                k.line(x, 365, x, 354, color)
                k.line(x, 365, x + 9, 369, color)
            k.label(x, 470, label, color, size=9)
    elif scene == "delivery":
        person(k, 110, 400, .85)
        k.path("M180 380 L820 380", color=T.GRID, sw=2)
        k.blob("M300 250 L470 250 L470 380 L300 380 Z", T.PANEL2, T.CYAN)
        k.path("M350 250 L350 210 L420 210 L420 250", T.CYAN)
        k.path("M350 300 L385 335 L430 285", T.GREEN)
        k.label(385, 405, "PROJECT", T.CYAN, size=9)
        for i in range(3):
            k.s.rect(560, 330 - i * 30, 120, 24, fill=T.PANEL,
                     stroke=T.AMBER, rx=4, sw=2)
        k.label(620, 405, "MANUALS", T.AMBER, size=9)
        k.circle(740, 285, 38, T.VIOLET, T.PANEL)
        k.line(767, 312, 805, 350, T.VIOLET)
    elif scene == "migration":
        k.path("M80 400 C250 380 500 420 820 390", color=T.GRID, sw=2)
        chip(k, 130, 220, 140, 95, T.AMBER)
        chip(k, 365, 185, 150, 100, T.CYAN)
        chip(k, 620, 220, 140, 95, T.VIOLET)
        k.label(200, 345, "G0", T.AMBER, size=9)
        k.label(440, 315, "L4", T.CYAN, size=9)
        k.label(690, 345, "H7", T.VIOLET, size=9)
        k.arrow(270, 265, 360, 245, T.CYAN)
        k.arrow(515, 235, 615, 260, T.VIOLET)
        for i in range(2):
            k.s.rect(70, 330 - i * 24, 90, 20, fill=T.PANEL,
                     stroke=T.AMBER, rx=4, sw=2)
        k.label(115, 405, "MANUAL", T.AMBER, size=8)
        k.s.rect(700, 350, 120, 40, fill=T.PANEL2, stroke=T.RED, rx=4, sw=2)
        k.label(760, 405, "SPL", T.RED, size=9)
    elif scene == "stack":
        for i, (y, label, color) in enumerate((
            (400, "HW", T.STROKE),
            (340, "KERNEL", T.CYAN),
            (280, "SERVICES", T.VIOLET),
            (220, "APP", T.GREEN),
        )):
            x = 220 + i * 18
            k.s.rect(x, y, 360, 46, fill=T.PANEL2, stroke=color, rx=4, sw=2)
            k.label(x + 180, y + 29, label, color, size=10)
        k.path("M120 430 C200 380 180 300 250 250 S330 180 430 160",
               T.AMBER, cls="hd-flow")
        k.circle(430, 160, 20, T.AMBER, T.PANEL)
        k.blob("M300 110 L400 110 L400 160 L300 160 Z", T.PANEL, T.CYAN)
        k.label(350, 140, "PRODUCT", T.CYAN, size=8)
    return k.footer()


def main(argv: list[str]) -> int:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_dir = os.path.join(root, "assets", "illustrations")
    os.makedirs(out_dir, exist_ok=True)
    only = {item.zfill(2) for item in argv[1:]}
    count = 0
    part_count = 0
    for ch, title, zh, aria, scene in CHAPTERS:
        number = f"{ch:02d}"
        if only and number not in only:
            continue
        path = os.path.join(out_dir, f"ch{number}-handdraw.svg")
        chapter_scene(ch, title, aria, scene).save(path)
        xml.dom.minidom.parse(path)
        print(f"[ok] {os.path.relpath(path, root)}")
        count += 1
    if not only:
        for index, zh, aria, scene in PARTS:
            part_id = f"p{index - 1}"
            path = os.path.join(out_dir, f"part-{part_id}-handdraw.svg")
            part_scene(index, zh, aria, scene).save(path)
            xml.dom.minidom.parse(path)
            print(f"[ok] {os.path.relpath(path, root)}")
            part_count += 1
        manifest = {
            "schema_version": 1,
            "style": "FA-002",
            "colors": ["C-03", "C-10", "C-27", "C-31"],
            "files": [
                {
                    "chapter": f"{ch:02d}",
                    "file": f"ch{ch:02d}-handdraw.svg",
                    "zh": zh,
                    "en": aria,
                }
                for ch, _title, zh, aria, _scene in CHAPTERS
            ],
            "parts": [
                {
                    "id": f"p{index - 1}",
                    "file": f"part-p{index - 1}-handdraw.svg",
                    "zh": zh,
                    "en": aria,
                }
                for index, zh, aria, _scene in PARTS
            ],
        }
        manifest_path = os.path.join(out_dir, "manifest.json")
        with open(manifest_path, "w", encoding="utf-8") as handle:
            json.dump(manifest, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        print(f"[ok] {os.path.relpath(manifest_path, root)}")
    print(f"generated {count} chapter and {part_count} part illustrations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

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
        # IG-004: two aligned electrical states, not a decorative GPIO metaphor.
        k.label(450, 100, "共阳接法 · 3.3 V → LED → PC13", T.CYAN, 14)
        k.blob("M70 125 Q70 115 82 115 L408 115 Q420 115 420 128 L420 425 L70 425 Z",
               T.BG2, T.GRID)
        k.blob("M480 125 Q480 115 492 115 L818 115 Q830 115 830 128 L830 425 L480 425 Z",
               T.PANEL2, T.GREEN)
        for cx, state, level, result, color in [
            (245, "写 1 · 灯灭", "PC13 = 1", "断开灌电流 · 灯灭", T.RED),
            (655, "写 0 · 灯亮", "PC13 = 0", "导通 · 灌电流", T.GREEN),
        ]:
            k.label(cx, 158, state, color, 20)
            k.label(cx, 203, "3.3 V", T.AMBER, 12)
            k.circle(cx, 274, 34, color if cx == 655 else T.STROKE,
                     T.PANEL if cx == 655 else T.BG,
                     cls="hd-pulse" if cx == 655 else None)
            k.label(cx, 280, "LED", color, 13)
            k.line(cx, 220, cx, 238, T.AMBER)
            k.label(cx, 353, level, color, 15)
            k.label(cx, 398, result, color, 12)
            if cx == 655:
                k.arrow(cx, 312, cx, 330, T.GREEN)
                for x1, y1, x2, y2 in [(610,274,596,274),(700,274,686,274),
                                       (623,242,613,232),(687,242,697,232),
                                       (623,306,613,316),(687,306,697,316)]:
                    k.line(x1, y1, x2, y2, T.AMBER, cls="hd-pulse")
            else:
                k.line(cx, 312, cx, 330, T.GRID, dash="4 6")
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
    (3, "GPIO", "PC13 写高电平灯灭、写低电平灯亮的共阳接法双态对照",
     "Two states of the common-anode PC13 LED: high is off and low is on", "gpio"),
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


MID = [
    (0, "三条启动路径，只有一条走进你的程序",
     "Three boot doors, only one reaches your program",
     "三个启动状态", "Three boot states", "boot-gates"),
    (1, "编辑、构建、烧录、验收围成一个闭环",
     "Edit, build, flash, and accept form one loop",
     "核心原理", "Core ideas", "accept-loop"),
    (2, "时钟过两座桥，抵达快慢不同的外设区",
     "A clock crosses two bridges into fast and slow peripheral districts",
     "核心原理", "Core ideas", "bus-bridges"),
    (3, "上拉与下拉把浮空的引脚按住",
     "Pull-up and pull-down hold a floating pin in place",
     "核心原理", "Core ideas", "pull-lines"),
    (4, "高优先级打断正在运行的低优先级",
     "A higher priority interrupts the lower one mid-run",
     "核心原理", "Core ideas", "nesting"),
    (5, "比较线跨过锯齿波，切出占空比",
     "A compare line crosses the sawtooth and cuts out the duty cycle",
     "核心原理", "Core ideas", "duty"),
    (6, "一帧比特有头有尾，双方踩着同一个节拍",
     "A framed byte has a head and a tail on a shared beat",
     "核心原理", "Core ideas", "frame"),
    (7, "被点到名的设备把总线拉低应答",
     "The addressed device pulls the bus low to acknowledge",
     "核心原理", "Core ideas", "ack"),
    (8, "片选线点名，只有被选中的设备开口",
     "Chip-select names one device; only the chosen one speaks",
     "核心原理", "Core ideas", "chip-select"),
    (9, "采样先按住电压，再一格一格量化",
     "Sampling holds the voltage still, then quantizes step by step",
     "核心原理", "Core ideas", "sample-hold"),
    (10, "两块缓冲区轮流接住传送带",
     "Two buffers take turns catching the conveyor",
     "核心原理", "Core ideas", "pingpong"),
    (11, "喂狗只在窗口内有效，早喂晚喂都复位",
     "Feeding only counts inside the window; early or late both reset",
     "核心原理", "Core ideas", "feed-window"),
    (12, "验收不过的镜像退回旧版本",
     "An image that fails acceptance rolls back to the old one",
     "核心原理", "Core ideas", "rollback"),
    (13, "过滤器只放行掩码认可的标识符",
     "The filter admits only mask-approved identifiers",
     "核心原理", "Core ideas", "filter-mask"),
    (14, "端点是粗细不同的管道，各走各的数据",
     "Endpoints are pipes of different widths, each carrying its own data",
     "核心原理", "Core ideas", "endpoints"),
    (15, "任务在就绪、运行、阻塞之间循环",
     "A task cycles between ready, running, and blocked",
     "核心原理", "Core ideas", "task-states"),
    (16, "睡着的芯片仍留着几只闹钟",
     "A sleeping chip still keeps a few alarm bells",
     "核心原理", "Core ideas", "wake-sources"),
    (17, "二分逼近第一处分歧点",
     "Bisect toward the first point of divergence",
     "核心原理", "Core ideas", "bisect"),
    (18, "五步漏斗把症状筛成原因",
     "A five-step funnel sieves symptoms into a cause",
     "排错方法论（先做这 5 步）", "A method for debugging (do these 5 steps first)", "funnel"),
    (19, "先跑通最小闭环，再一块块加石头",
     "Prove the smallest loop first, then lay stone after stone",
     "1. 蓝牙小车（★★ 入门级）", "1. Bluetooth car (★★ beginner)", "milestone"),
    (20, "问题按层级送进对应的手册书架",
     "Route each question to the matching manual shelf",
     "遇到问题时去哪找证据", "Where to look for evidence", "doc-tiers"),
    (21, "读板先圈出电源、去耦、复位",
     "Reading a board starts by circling power, decoupling, and reset",
     "核心原理", "Core ideas", "schematic-read"),
    (22, "仿真到不了的地方：时序与电气",
     "Where simulation stops: timing and electrical truth",
     "仿真替不了的事", "What simulation will not do for you", "sim-limits"),
    (23, "F1 的桥板，有几块在 G0 上合不上",
     "Some F1 bridge planks do not fit the G0 side",
     "从 F1 抄代码时最容易摔的几处", "Common ways an F1 port falls over", "porting-traps"),
    (24, "Stop 2 睡下、唤醒、时钟重新转起来",
     "Stop 2 sleeps, wakes, and the clock spins up again",
     "Stop 2 进入、唤醒与时钟恢复闭环", "Stop 2: entry, wake evidence, and clock recovery", "stop2-loop"),
    (25, "8 MHz 一级一级倍到 480 MHz",
     "8 MHz gears up stage by stage to 480 MHz",
     "HSE 8 MHz 到 480 MHz：一条可复算的时钟链",
     "From 8 MHz HSE to 480 MHz: a reproducible clock chain", "clock-chain"),
    (26, "时钟、默认值、配置、使能，四级台阶",
     "Clock, defaults, configuration, enable: four steps",
     "3. 统一调用模型：时钟、默认值、配置、使能",
     "3. The common model: clock, defaults, configuration, enable", "call-model"),
    (27, "字节流要切成有边界的消息",
     "A byte stream must be cut into framed messages",
     "TCP 是字节流：必须自己定义消息边界",
     "TCP is a byte stream: define application framing", "stream-framing"),
    (28, "每件事都要装进自己的时间预算盒",
     "Every job must fit inside its own time-budget box",
     "⏱️ 实时性来自预算，不来自 RTOS 名字",
     "⏱️ Real time comes from budgets, not an RTOS name", "budget"),
]


APPENDICES = (
    ("a", "appendix-engineering", "两类 DMA 契约各自成环，不能混拼",
     "Two DMA contracts each close their own loop; never mix them", "dma-contracts"),
    ("b", "appendix-examples", "十四个例程，每个都留下可复现的证据",
     "Fourteen examples, each leaving reproducible evidence", "example-index"),
    ("c", "appendix-exercises", "先自己推一遍，再翻开答案对",
     "Work it out yourself before opening the answer key", "answer-key"),
    ("d", "appendix-glossary", "每个术语挂回它所属的章节",
     "Every term hangs from the chapter it belongs to", "glossary"),
    ("e", "appendix-references", "每条事实都能落回一份带版本的来源",
     "Every fact lands on a versioned source", "sources"),
    ("f", "appendix-oss-map", "开源项目按层次在地图上各就各位",
     "Open-source projects take their places on the map", "oss-map"),
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


def mid_scene(ch: int, zh: str, aria: str, scene: str) -> Svg:
    """Return one mid-chapter concept plate for the chapter's core section."""
    k = Sketch(ch, zh, aria)
    k.path("M52 455 C180 443 292 468 420 451 S690 440 848 454",
           color=T.GRID, sw=1.5)

    if scene == "boot-gates":
        for x, c, lab, lit in [
            (180, T.AMBER, "FLASH", True),
            (450, T.CYAN, "ROM", False),
            (720, T.VIOLET, "SRAM", False),
        ]:
            k.blob(f"M{x-70} 390 L{x-70} 220 Q{x} 165 {x+70} 220 L{x+70} 390 Z",
                   T.PANEL2 if lit else T.BG2, c)
            if lit:
                k.path(f"M{x-36} 390 L{x-36} 248 Q{x} 208 {x+36} 248 L{x+36} 390", c)
                k.circle(x, 320, 14, T.RED, T.PANEL, cls="hd-pulse")
            k.label(x, 430, lab, c, 9)
        person(k, 75, 395, .7, pose="walk", cls="hd-float")
        k.path("M115 380 C170 360 175 350 180 330", T.AMBER, cls="hd-flow")
    elif scene == "accept-loop":
        for i, (lab, c) in enumerate([
            ("EDIT", T.AMBER), ("BUILD", T.CYAN), ("FLASH", T.VIOLET), ("CHECK", T.GREEN),
        ]):
            a = -math.pi / 2 + i * math.pi / 2
            x, y = 450 + 170 * math.cos(a), 285 + 140 * math.sin(a)
            k.circle(x, y, 42, c, T.BG2, cls="hd-float")
            k.label(x, y + 5, lab, c, 9)
        for i in range(4):
            a1 = -math.pi / 2 + i * math.pi / 2 + .5
            a2 = -math.pi / 2 + (i + 1) * math.pi / 2 - .5
            k.arrow(450 + 170 * math.cos(a1), 285 + 140 * math.sin(a1),
                    450 + 170 * math.cos(a2), 285 + 140 * math.sin(a2), T.CYAN)
        k.path("M428 285 L444 301 L476 264", T.GREEN)
    elif scene == "bus-bridges":
        k.circle(125, 260, 52, T.AMBER, T.PANEL)
        k.line(125, 260, 153, 240, T.RED); k.line(125, 260, 113, 226, T.CYAN)
        k.path("M177 260 C250 260 245 180 325 180 M177 260 C250 260 245 340 325 340",
               T.CYAN, cls="hd-flow")
        for y, lab, c, names in [
            (180, "AHB", T.AMBER, ("FLASH", "DMA", "GPIO")),
            (340, "APB", T.GREEN, ("UART", "TIM", "I2C")),
        ]:
            k.path(f"M325 {y} C395 {y-30} 465 {y-30} 535 {y}", c, sw=2)
            k.path(f"M325 {y+14} C395 {y-16} 465 {y-16} 535 {y+14}", c, sw=2)
            k.label(430, y - 34, lab, c, 10)
            for x, name in zip((620, 715, 810), names):
                k.blob(f"M{x-38} {y-46} L{x+38} {y-46} L{x+44} {y-4} L{x-44} {y-4} Z",
                       T.PANEL2, c, "hd-float")
                k.label(x, y - 20, name, c, 8)
                k.line(x, y - 4, x, y + 10, c)
    elif scene == "pull-lines":
        k.line(80, 130, 820, 130, T.RED)
        k.line(80, 420, 820, 420, T.STROKE)
        k.label(56, 135, "VDD", T.RED, 9); k.label(56, 425, "GND", T.STROKE, 9)
        k.path("M260 130 L260 158", T.RED)
        k.path("M248 158 L272 176 L248 194 L272 212 L248 230 L260 246", T.RED)
        k.path("M260 246 L260 300", T.RED)
        k.circle(260, 300, 10, T.RED, T.PANEL, cls="hd-pulse")
        k.path("M270 300 C330 300 350 300 395 300", T.CYAN, cls="hd-flow")
        k.circle(425, 300, 22, T.CYAN, T.BG2); k.label(425, 305, "PIN", T.CYAN, 9)
        k.path("M260 310 L236 368", T.AMBER)
        k.circle(234, 376, 4, T.AMBER, T.AMBER); k.line(234, 382, 234, 420, T.AMBER)
        k.circle(620, 300, 10, T.GREEN, T.PANEL, cls="hd-pulse")
        k.path("M610 300 C560 300 545 300 505 300", T.GREEN, cls="hd-flow")
        k.circle(475, 300, 22, T.GREEN, T.BG2); k.label(475, 305, "PIN", T.GREEN, 9)
        k.path("M620 310 L620 336", T.GREEN)
        k.path("M608 336 L632 354 L608 372 L632 390 L620 402", T.GREEN)
        k.label(296, 196, "R", T.RED, 11); k.label(656, 362, "R", T.GREEN, 11)
    elif scene == "nesting":
        k.path("M110 360 C240 360 300 340 355 340", T.CYAN, sw=2)
        k.path("M565 340 C660 340 730 360 810 360", T.CYAN, sw=2)
        k.label(210, 395, "LOW", T.CYAN, 10)
        k.path("M355 340 C375 215 545 215 565 340", T.RED, sw=2, cls="hd-flow")
        k.label(460, 200, "HIGH", T.RED, 10)
        k.path("M378 278 L362 312 L376 312 L364 346", T.AMBER)
        k.circle(460, 278, 12, T.RED, T.PANEL, cls="hd-pulse")
        k.arrow(520, 250, 480, 320, T.RED)
    elif scene == "duty":
        k.path("M120 320 L250 200 L250 320 L380 200 L380 320 L510 200 L510 320 L640 200 L640 320",
               T.CYAN)
        k.label(660, 215, "CNT", T.CYAN, 9)
        k.line(100, 258, 770, 258, T.AMBER)
        k.label(782, 262, "CCR", T.AMBER, 9)
        for x in (185, 315, 445, 575):
            k.line(x, 200, x, 420, T.GRID)
        k.path("M120 380 L185 380 L185 420 L315 420 L315 380 L445 380 L445 420 L575 420 L575 380 L705 380",
               T.RED, cls="hd-flow")
        k.label(735, 415, "OUT", T.RED, 9)
    elif scene == "frame":
        k.line(100, 300, 800, 300, T.GRID)
        k.blob("M110 250 L162 250 L168 330 L104 330 Z", T.PANEL2, T.GREEN)
        k.label(136, 295, "S", T.GREEN, 14)
        for i, b in enumerate("01011001"):
            x = 214 + i * 60
            k.circle(x, 290, 21, T.AMBER if b == "1" else T.CYAN, T.BG2, cls="hd-float")
            k.label(x, 295, b, T.TEXT, 12)
        k.blob("M724 250 L776 250 L782 330 L718 330 Z", T.PANEL2, T.RED)
        k.label(750, 295, "P", T.RED, 14)
        k.path("M136 380 C310 425 560 425 750 380", T.VIOLET, cls="hd-flow")
        k.label(450, 448, "BAUD", T.VIOLET, 10)
    elif scene == "ack":
        k.path("M90 260 C260 215 420 300 810 240", T.CYAN, cls="hd-flow")
        k.blob("M115 155 L245 155 L253 222 L107 222 Z", T.PANEL2, T.AMBER, "hd-float")
        k.label(180, 197, "0x3C", T.AMBER, 13)
        k.line(180, 222, 180, 256, T.AMBER)
        k.blob("M555 140 L695 140 L707 225 L543 225 Z", T.PANEL2, T.GREEN, "hd-float")
        k.label(625, 188, "DEV", T.GREEN, 12)
        k.line(625, 225, 625, 250, T.GREEN)
        k.path("M515 255 L515 345 L655 345 L655 250", T.RED, sw=2)
        k.label(585, 388, "ACK", T.RED, 12)
        k.circle(765, 242, 15, T.VIOLET, T.PANEL, cls="hd-pulse")
        k.label(765, 288, "SDA", T.VIOLET, 9)
    elif scene == "chip-select":
        k.blob("M95 215 L225 215 L235 330 L105 330 Z", T.PANEL2, T.CYAN)
        k.label(165, 278, "MCU", T.CYAN, 12)
        for i, (x, c, on) in enumerate([
            (420, T.AMBER, True), (590, T.GREEN, False), (760, T.VIOLET, False),
        ]):
            k.blob(f"M{x-60} 200 L{x+60} 200 L{x+70} 320 L{x-70} 320 Z",
                   T.PANEL2 if on else T.BG2, c)
            k.label(x, 265, f"D{i+1}", c, 13)
            k.line(x, 200, x, 162, c)
        k.path("M190 215 C200 140 320 118 418 158", T.RED, cls="hd-flow")
        k.path("M590 162 C590 135 400 112 215 190", T.GRID)
        k.path("M760 162 C760 125 470 100 215 175", T.GRID)
        k.circle(420, 150, 10, T.RED, T.PANEL, cls="hd-pulse")
        k.label(420, 112, "CS", T.RED, 10)
    elif scene == "sample-hold":
        wave(k, 95, 260, 300, 55, T.CYAN)
        k.blob("M445 200 L560 200 L566 320 L439 320 Z", T.PANEL2, T.AMBER)
        k.path("M462 260 L477 232 L492 260 L507 232 L522 260 L537 232", T.AMBER)
        k.label(503, 350, "HOLD", T.AMBER, 9)
        k.path("M600 320 L600 240 L665 240 L665 290 L730 290 L730 205 L795 205",
               T.RED, cls="hd-flow")
        for x in (135, 205, 275, 345):
            k.line(x, 400, x, 416, T.VIOLET)
        k.label(240, 442, "CLK", T.VIOLET, 9)
    elif scene == "pingpong":
        k.path("M90 180 L810 180", T.GRID, sw=2)
        for i in range(7):
            k.s.rect(140 + i * 95, 152, 52, 30, fill=T.PANEL2, stroke=T.CYAN, rx=4, sw=2)
        k.arrow(450, 205, 335, 285, T.AMBER); k.arrow(520, 205, 635, 285, T.VIOLET)
        k.blob("M225 305 L435 305 L445 425 L215 425 Z", T.PANEL2, T.AMBER, "hd-float")
        k.label(330, 370, "BUF A", T.AMBER, 12)
        k.blob("M535 305 L745 305 L755 425 L525 425 Z", T.BG2, T.VIOLET)
        k.label(640, 370, "BUF B", T.VIOLET, 12)
        k.path("M472 350 C502 328 520 328 540 344", T.GREEN, cls="hd-flow")
        k.circle(505, 330, 15, T.GREEN, T.BG, cls="hd-pulse")
    elif scene == "feed-window":
        k.line(120, 380, 800, 380, T.GRID, sw=2)
        for x, lab in ((300, "OPEN"), (640, "CLOSE")):
            k.line(x, 210, x, 380, T.AMBER, sw=2)
            k.label(x, 200, lab, T.AMBER, 9)
        k.path("M300 210 C420 190 540 190 640 210", T.AMBER)
        k.blob("M430 300 Q470 272 510 300 L503 358 Q470 375 437 358 Z", T.PANEL, T.RED)
        k.label(470, 335, "DOG", T.RED, 9)
        k.path("M195 300 L255 345 M255 300 L195 345", T.RED)
        k.label(225, 285, "EARLY", T.RED, 8)
        k.path("M455 262 L470 277 L500 240", T.GREEN)
        k.path("M700 300 L760 345 M760 300 L700 345", T.RED)
        k.label(730, 285, "LATE", T.RED, 8)
    elif scene == "rollback":
        k.blob("M110 190 L330 190 L330 400 L110 400 Z", T.PANEL2, T.GREEN)
        k.label(220, 255, "V1", T.GREEN, 16)
        k.path("M195 320 L215 340 L255 295", T.GREEN)
        k.blob("M570 190 L790 190 L790 400 L570 400 Z", T.PANEL2, T.RED, "hd-float")
        k.label(680, 255, "V2", T.RED, 16)
        k.path("M650 305 L710 345 M710 305 L650 345", T.RED)
        k.path("M330 250 C420 195 480 195 570 250", T.CYAN, cls="hd-flow")
        k.s.poly([(556,236),(574,250),(552,258)], fill=T.CYAN, sw=1)
        k.path("M570 340 C480 420 420 420 330 340", T.VIOLET, cls="hd-flow")
        k.s.poly([(344,352),(326,338),(348,330)], fill=T.VIOLET, sw=1)
        k.label(450, 200, "BOOT", T.CYAN, 9); k.label(450, 418, "ROLLBACK", T.VIOLET, 9)
    elif scene == "filter-mask":
        for i, (ident, c) in enumerate([
            ("201", T.GREEN), ("405", T.RED), ("203", T.GREEN), ("7FF", T.RED),
        ]):
            y = 150 + i * 66
            k.blob(f"M90 {y} L210 {y} L216 {y+44} L84 {y+44} Z", T.PANEL2, c, "hd-float")
            k.label(150, y+29, ident, c, 11)
        k.path("M300 130 L300 430", T.AMBER, sw=2)
        for y in range(150, 430, 24):
            k.line(290, y, 310, y + 12, T.AMBER)
        k.label(300, 452, "MASK", T.AMBER, 10)
        for y in (172, 304):
            k.path(f"M216 {y+22} C250 {y+25} 262 {y+26} 296 {y+28}", T.GREEN, cls="hd-flow")
        for y in (238, 370):
            k.path(f"M232 {y} L268 {y+30} M268 {y} L232 {y+30}", T.RED)
        k.blob("M600 200 L790 200 L800 360 L590 360 Z", T.PANEL2, T.CYAN)
        k.label(695, 285, "RX FIFO", T.CYAN, 12)
        k.path("M300 194 C420 210 480 235 592 262", T.GREEN, cls="hd-flow")
        k.path("M300 326 C420 330 480 320 592 295", T.GREEN, cls="hd-flow")
    elif scene == "endpoints":
        k.blob("M95 190 L255 190 L265 370 L105 370 Z", T.PANEL2, T.CYAN)
        k.label(180, 285, "DEV", T.CYAN, 13)
        k.blob("M645 190 L805 190 L815 370 L655 370 Z", T.PANEL2, T.GREEN)
        k.label(730, 285, "HOST", T.GREEN, 13)
        k.path("M265 228 C400 193 510 193 645 228", T.AMBER, sw=2)
        k.path("M265 236 C400 201 510 201 645 236", T.AMBER, sw=2)
        k.label(452, 190, "EP0", T.AMBER, 9)
        k.path("M265 277 C400 277 510 277 645 277", T.CYAN, sw=2)
        k.path("M265 293 C400 293 510 293 645 293", T.CYAN, sw=2)
        k.label(452, 262, "EP1", T.CYAN, 9)
        k.path("M265 330 C400 372 510 372 645 330", T.VIOLET, sw=2)
        k.path("M265 356 C400 398 510 398 645 356", T.VIOLET, sw=2)
        k.label(452, 412, "EP2", T.VIOLET, 9)
        k.circle(340, 218, 9, T.AMBER, T.PANEL, cls="hd-pulse")
        k.circle(455, 285, 11, T.CYAN, T.PANEL, cls="hd-pulse")
        k.circle(565, 356, 13, T.VIOLET, T.PANEL, cls="hd-pulse")
    elif scene == "task-states":
        for x, y, lab, c in [
            (200, 200, "READY", T.GREEN), (620, 200, "RUN", T.CYAN), (410, 395, "BLOCK", T.VIOLET),
        ]:
            k.blob(f"M{x-82} {y-46} L{x+82} {y-46} L{x+90} {y+46} L{x-90} {y+46} Z",
                   T.PANEL2, c, "hd-float")
            k.label(x, y + 6, lab, c, 13)
        k.arrow(288, 200, 532, 200, T.GREEN)
        k.arrow(600, 246, 478, 360, T.CYAN)
        k.arrow(342, 360, 222, 246, T.VIOLET)
        k.path("M385 158 C420 122 470 122 505 158", T.AMBER, cls="hd-sway")
        k.circle(445, 120, 12, T.AMBER, T.PANEL)
        k.label(445, 100, "TICK", T.AMBER, 8)
    elif scene == "wake-sources":
        chip(k, 330, 230, 240, 130, T.GREEN, "hd-float")
        k.label(450, 302, "Z z z", T.GREEN, 16)
        for x, y, c, lab in [
            (140, 180, T.AMBER, "RTC"), (140, 350, T.CYAN, "PIN"), (770, 260, T.VIOLET, "UART"),
        ]:
            k.circle(x, y, 30, c, T.BG2, cls="hd-pulse")
            k.path(f"M{x-12} {y} L{x} {y+12} L{x+16} {y-14}", c)
            k.label(x, y + 54, lab, c, 9)
        k.path("M172 185 C240 200 280 230 322 250", T.AMBER, cls="hd-flow")
        k.path("M172 350 C250 340 290 320 328 305", T.CYAN, cls="hd-flow")
        k.path("M738 260 C670 260 620 268 574 280", T.VIOLET, cls="hd-flow")
    elif scene == "bisect":
        k.line(110, 300, 790, 300, T.GRID, sw=2)
        for x in (140, 250, 360, 470, 580, 690, 780):
            k.line(x, 285, x, 315, T.STROKE)
        k.path("M110 300 C250 205 380 212 470 300 S650 425 790 322", T.CYAN, cls="hd-flow")
        k.path("M250 244 L250 205 L580 205 L580 244", T.AMBER)
        k.label(415, 192, "1/2", T.AMBER, 10)
        k.path("M360 172 L360 138 L470 138 L470 172", T.GREEN)
        k.label(415, 126, "1/4", T.GREEN, 10)
        k.circle(470, 300, 18, T.RED, T.PANEL, cls="hd-pulse")
        k.label(470, 348, "DIFF", T.RED, 9)
        k.circle(660, 120, 30, T.VIOLET, T.BG, cls="hd-sway")
        k.line(681, 141, 712, 172, T.VIOLET)
    elif scene == "funnel":
        k.blob("M180 145 L720 145 L520 380 L520 445 L380 445 L380 380 Z", T.PANEL2, T.CYAN)
        for i, (t, c) in enumerate([
            ("LOG", T.AMBER), ("VCC", T.RED), ("CLK", T.CYAN), ("PIN", T.GREEN), ("IRQ", T.VIOLET),
        ]):
            x = 255 + i * 97
            k.circle(x, 108, 20, c, T.BG2, cls="hd-float")
            k.label(x, 113, t, c, 8)
        for i in range(5):
            y = 195 + i * 38
            w = 215 - i * 34
            k.line(450 - w, y, 450 + w, y, T.GRID)
            k.label(450 + w + 28, y + 4, f"{i+1}", T.STROKE, 10)
        k.arrow(450, 445, 450, 472, T.RED)
        k.circle(450, 492, 14, T.RED, T.PANEL, cls="hd-pulse")
        k.label(555, 497, "CAUSE", T.RED, 10)
    elif scene == "milestone":
        wave(k, 60, 435, 780, 16, T.CYAN)
        for i, (x, y, c) in enumerate([
            (170, 365, T.GREEN), (360, 315, T.CYAN), (550, 350, T.AMBER), (740, 285, T.VIOLET),
        ]):
            k.blob(f"M{x-70} {y} Q{x} {y-28} {x+70} {y} L{x+55} {y+40} Q{x} {y+55} {x-55} {y+40} Z",
                   T.PANEL2, c, "hd-float")
            k.label(x, y + 22, str(i + 1), c, 15)
            k.line(x, y - 28, x, y - 70, c)
            k.path(f"M{x} {y-70} L{x+34} {y-60} L{x} {y-48}", c)
        k.path("M145 356 L160 371 L195 338", T.GREEN)
        person(k, 78, 400, .7, pose="walk")
        k.path("M150 372 C240 345 300 332 330 322 S460 326 520 340 S660 312 700 296",
               T.GREEN, cls="hd-flow")
    elif scene == "doc-tiers":
        k.path("M560 425 L560 125 L840 125 L840 425", T.CYAN)
        for y, lab, c in [(190, "DS", T.RED), (290, "RM", T.AMBER), (390, "AN", T.GREEN)]:
            k.line(560, y, 840, y, T.CYAN)
            for i in range(3):
                k.s.rect(598 + i * 70, y - 40, 42, 36, fill=T.PANEL2, stroke=c, rx=4, sw=2)
            k.label(820, y - 20, lab, c, 10)
        k.circle(175, 250, 42, T.VIOLET, T.BG2, cls="hd-float")
        k.label(175, 262, "?", T.VIOLET, 26)
        k.path("M220 250 C330 250 430 185 552 172", T.RED, cls="hd-flow")
        k.path("M220 265 C340 280 430 285 552 285", T.GRID)
        k.path("M220 280 C350 335 440 385 552 388", T.GRID)
        k.circle(556, 172, 8, T.RED, T.RED, cls="hd-pulse")
    elif scene == "schematic-read":
        k.s.rect(105, 145, 425, 280, fill=T.PANEL2, stroke=T.GREEN, rx=8, sw=2)
        chip(k, 225, 220, 150, 100, T.CYAN)
        for cx, cy, c, sym in [(190, 195, T.RED, "PWR"), (400, 200, T.AMBER, "CAP"), (330, 365, T.VIOLET, "RST")]:
            k.circle(cx, cy, 52, c, T.BG, cls="hd-sway")
            k.label(cx, cy + 64, sym, c, 10)
        k.path("M170 195 L210 195 M190 175 L190 215", T.RED)
        k.path("M382 185 L418 185 M382 215 L418 215", T.AMBER)
        k.circle(330, 365, 13, T.VIOLET, T.PANEL)
        k.circle(690, 270, 60, T.CYAN, T.BG)
        k.line(732, 312, 800, 380, T.CYAN)
        k.path("M660 270 C685 235 715 305 745 258", T.VIOLET, cls="hd-flow")
    elif scene == "sim-limits":
        k.blob("M90 160 L360 160 L350 380 L100 380 Z", T.PANEL2, T.CYAN)
        k.path("M125 330 C175 250 260 350 330 235", T.CYAN, cls="hd-flow")
        k.label(225, 412, "MODEL", T.CYAN, 10)
        k.path("M450 115 L450 435", T.RED, sw=2)
        for y in range(135, 430, 30):
            k.line(437, y, 463, y + 15, T.RED)
        k.label(450, 102, "WALL", T.RED, 9)
        chip(k, 585, 215, 175, 120, T.GREEN, "hd-float")
        k.label(673, 412, "BENCH", T.GREEN, 10)
        k.path("M378 250 C408 235 424 235 444 246", T.AMBER, cls="hd-flow")
        k.s.poly([(444,236),(462,248),(442,258)], fill=T.AMBER, sw=1)
        k.path("M505 160 L490 195 L503 195 L492 232", T.AMBER)
        k.label(520, 130, "ns", T.AMBER, 10)
    elif scene == "porting-traps":
        k.path("M60 400 L60 180 L260 180 L260 400", T.GRID, sw=2)
        k.label(160, 162, "F1", T.AMBER, 12)
        k.path("M640 400 L640 180 L840 180 L840 400", T.GRID, sw=2)
        k.label(740, 162, "G0", T.CYAN, 12)
        for i in range(5):
            x = 292 + i * 66
            broken = i in (1, 3)
            c = T.RED if broken else T.GREEN
            k.s.poly([(x, 300), (x + 52, 296 if not broken else 314),
                      (x + 52, 330 if not broken else 348), (x, 334)],
                     fill=T.PANEL2 if not broken else T.BG2, stroke=c, sw=2)
        k.path("M358 292 L344 322 M352 332 L368 304", T.RED)
        k.path("M492 296 L480 326 M506 302 L492 332", T.RED)
        person(k, 130, 420, .7, pose="walk", cls="hd-float")
        k.arrow(252, 250, 296, 288, T.AMBER)
    elif scene == "stop2-loop":
        k.path("M700 120 C745 88 796 114 789 166 C768 206 722 196 708 168 C735 172 756 158 763 134 C735 151 715 142 700 120 Z",
               T.AMBER, fill=T.PANEL)
        k.s.rect(150, 285, 310, 90, fill=T.PANEL2, stroke=T.GREEN, rx=8, sw=2)
        k.path("M150 285 C195 252 265 252 305 285", T.GREEN)
        chip(k, 225, 295, 160, 66, T.GREEN)
        k.label(305, 338, "Z z", T.GREEN, 14)
        k.circle(560, 240, 30, T.RED, T.BG2, cls="hd-pulse")
        k.line(560, 240, 560, 224, T.RED); k.line(560, 240, 572, 247, T.RED)
        k.path("M560 208 L560 188 M540 214 L528 198 M580 214 L592 198", T.RED)
        k.path("M592 252 C645 262 665 305 653 345", T.CYAN, cls="hd-flow")
        k.circle(652, 360, 26, T.CYAN, T.BG)
        k.line(652, 360, 664, 349, T.CYAN); k.line(652, 360, 652, 345, T.CYAN)
        k.label(305, 415, "STOP2", T.GREEN, 9); k.label(652, 415, "CLK", T.CYAN, 9)
        k.label(560, 300, "WKUP", T.RED, 9)
    elif scene == "clock-chain":
        gear(k, 140, 300, 40, T.AMBER)
        k.label(140, 362, "8M", T.AMBER, 10)
        gear(k, 340, 255, 58, T.CYAN)
        k.label(340, 342, "PLL", T.CYAN, 10)
        gear(k, 560, 300, 40, T.VIOLET)
        k.label(560, 362, "VCO", T.VIOLET, 10)
        k.circle(740, 240, 46, T.RED, T.BG, cls="hd-pulse")
        k.label(740, 246, "480", T.RED, 14)
        k.path("M182 292 C240 282 255 268 284 262 M398 266 C460 274 480 290 520 296 M600 292 C660 276 678 256 696 246",
               T.CYAN, cls="hd-flow")
        for i, v in enumerate(("0.9", "1.0", "1.2")):
            y = 425 - i * 28
            k.line(130 + i * 42, y, 205 + i * 42, y, T.GREEN)
            k.label(106 + i * 42, y + 4, v, T.GREEN, 8)
        k.label(180, 458, "VOS", T.GREEN, 9)
    elif scene == "call-model":
        for i, (lab, c) in enumerate([
            ("CLK", T.AMBER), ("DEF", T.CYAN), ("CFG", T.VIOLET), ("EN", T.GREEN),
        ]):
            x = 175 + i * 155
            y = 375 - i * 58
            k.s.rect(x, y, 128, 44, fill=T.PANEL2, stroke=c, rx=4, sw=2)
            k.label(x + 64, y + 28, lab, c, 11)
        person(k, 115, 425, .7, pose="walk")
        k.path("M303 385 C330 370 330 350 332 333 M458 327 C485 312 485 292 487 275 M613 269 C640 254 640 234 642 217",
               T.CYAN, cls="hd-flow")
        k.circle(745, 130, 18, T.GREEN, T.PANEL, cls="hd-pulse")
        k.path("M735 130 L742 138 L757 118", T.GREEN)
    elif scene == "stream-framing":
        k.path("M70 215 C200 175 330 255 460 210 S700 175 830 220", T.CYAN, cls="hd-flow")
        for x in (260, 470, 660):
            k.path(f"M{x} 145 L{x} 278", T.RED, sw=2)
            k.path(f"M{x-9} 160 L{x} 145 L{x+9} 160", T.RED)
        for x, c, tag in [
            (150, T.AMBER, "LEN"), (365, T.GREEN, "SEQ"), (565, T.VIOLET, "ACK"), (745, T.RED, "CRC"),
        ]:
            k.blob(f"M{x-72} 330 L{x+72} 330 L{x+80} 402 L{x-80} 402 Z", T.PANEL2, c, "hd-float")
            k.label(x, 354, tag, c, 9)
            k.path(f"M{x-55} 374 L{x+55} 374", c)
        k.label(450, 448, "FRAMED", T.GREEN, 10)
    else:  # budget
        k.line(90, 350, 810, 350, T.STROKE, sw=2)
        for x in range(150, 811, 60):
            k.line(x, 342, x, 358, T.GRID)
        for x, w, c, lab in [
            (120, 170, T.GREEN, "SENSE"), (300, 140, T.CYAN, "TASK"),
            (450, 100, T.AMBER, "TX"), (560, 210, T.RED, "ISR"),
        ]:
            over = c == T.RED
            k.blob(f"M{x} {270 if not over else 256} L{x+w} {270 if not over else 256} L{x+w-6} 338 L{x+6} 338 Z",
                   T.PANEL2 if not over else T.BG2, c, "hd-float")
            k.label(x + w / 2, 310, lab, c, 9)
        k.path("M120 240 L770 240", T.VIOLET)
        k.path("M120 232 L120 248 M770 232 L770 248", T.VIOLET)
        k.label(445, 224, "PERIOD", T.VIOLET, 10)
        k.path("M732 262 L798 238", T.RED)
        k.label(820, 236, "OVER", T.RED, 9)

    return k.footer()


def appendix_scene(letter: str, zh: str, aria: str, scene: str) -> Svg:
    """Return one hand-drawn plate for an appendix opener."""
    k = Sketch(0, zh, aria, label=f"APP {letter.upper()}")
    k.path("M52 455 C180 443 292 468 420 451 S690 440 848 454",
           color=T.GRID, sw=1.5)

    if scene == "dma-contracts":
        k.path("M110 170 L790 170", T.GRID, sw=2)
        for i in range(8):
            k.s.rect(130 + i * 78, 140, 58, 30, fill=T.PANEL2, stroke=T.CYAN, rx=4, sw=2)
        k.circle(430, 120, 18, T.RED, T.PANEL, cls="hd-pulse")
        k.label(430, 125, "IDLE", T.RED, 7)
        k.path("M430 138 C430 150 430 155 430 165", T.RED)
        k.path("M700 185 C700 230 260 230 165 185", T.AMBER, cls="hd-flow")
        k.s.poly([(160,176),(178,186),(158,196)], fill=T.AMBER, sw=1)
        k.label(430, 250, "RE-ARM", T.AMBER, 9)
        k.path("M90 300 L810 300", T.RED, sw=2)
        for y in range(312, 336, 12):
            k.line(80, y, 820, y, T.RED)
        k.label(450, 292, "DO NOT MIX", T.RED, 9)
        k.circle(450, 400, 62, T.VIOLET, T.PANEL2)
        k.circle(450, 400, 34, T.VIOLET, T.BG)
        for i, lab in enumerate(("HT", "TC", "IDLE")):
            a = -math.pi / 2 + i * 2 * math.pi / 3
            k.circle(450 + 62 * math.cos(a), 400 + 62 * math.sin(a), 13,
                     T.VIOLET, T.BG2, cls="hd-pulse")
            k.label(450 + 62 * math.cos(a), 404 + 62 * math.sin(a), lab, T.VIOLET, 7)
        k.label(450, 405, "RING", T.VIOLET, 9)
    elif scene == "example-index":
        for i in range(14):
            x = 105 + (i % 7) * 100
            y = 175 + (i // 7) * 120
            k.blob(f"M{x} {y} L{x+74} {y} L{x+80} {y+62} L{x-6} {y+62} Z",
                   T.PANEL2, T.CYAN if i % 3 else T.AMBER, "hd-float")
            k.path(f"M{x+18} {y+32} L{x+32} {y+46} L{x+58} {y+16}", T.GREEN)
            k.label(x + 37, y + 82, f"E{i+1:02d}", T.STROKE, 8)
        k.path("M150 420 C300 445 560 445 750 425", T.GRID)
        k.label(450, 120, "14 VERIFIED", T.GREEN, 11)
    elif scene == "answer-key":
        k.blob("M300 180 L600 180 L612 380 L288 380 Z", T.PANEL2, T.CYAN)
        k.circle(450, 275, 34, T.AMBER, T.BG)
        k.path("M438 275 L448 285 L468 258", T.AMBER)
        k.path("M150 160 C200 140 260 170 250 215 C240 250 190 250 175 225",
               T.AMBER, sw=2)
        k.circle(212, 188, 16, T.AMBER, T.BG2)
        k.path("M248 220 C300 250 340 255 415 268", T.AMBER, cls="hd-flow")
        person(k, 690, 380, .8, T.STROKE, pose="stand", cls="hd-float")
        k.path("M700 330 C730 300 760 330 790 300", T.VIOLET, cls="hd-flow")
        k.label(450, 415, "CHECK AFTER", T.GREEN, 9)
    elif scene == "glossary":
        k.path("M90 120 L810 120", T.STROKE, sw=2)
        for i, (x, c, hang) in enumerate([
            (170, T.AMBER, 90), (300, T.CYAN, 130), (430, T.GREEN, 75),
            (560, T.VIOLET, 140), (690, T.RED, 100),
        ]):
            k.line(x, 120, x, 120 + hang, c)
            k.blob(f"M{x-52} {120+hang} L{x+52} {120+hang} L{x+58} {172+hang} L{x-58} {172+hang} Z",
                   T.PANEL2, c, "hd-sway")
            k.circle(x, 134 + hang, 5, c, T.BG)
            k.path(f"M{x-30} {152+hang} L{x+30} {152+hang}", c)
        k.path("M170 320 C260 380 340 360 430 395 S620 420 690 380", T.CYAN, cls="hd-flow")
        k.label(430, 445, "TERM -> CHAPTER", T.CYAN, 9)
    elif scene == "sources":
        for i, (lab, c) in enumerate([
            ("DS", T.RED), ("RM", T.AMBER), ("UM", T.CYAN), ("ERR", T.GREEN),
        ]):
            y = 380 - i * 62
            x = 230 + i * 16
            k.s.rect(x, y, 300, 48, fill=T.PANEL2, stroke=c, rx=4, sw=2)
            k.label(x + 36, y + 30, lab, c, 11)
            k.path(f"M{x+70} {y+24} L{x+270} {y+24}", c)
            k.label(x + 285, y + 30, f"rev{i+1}", T.MUTED, 8)
        k.circle(680, 220, 30, T.VIOLET, T.BG2, cls="hd-float")
        k.label(680, 226, "?", T.VIOLET, 20)
        k.path("M650 235 C600 265 570 285 545 300", T.VIOLET, cls="hd-flow")
        k.circle(545, 305, 9, T.VIOLET, T.PANEL, cls="hd-pulse")
    else:  # oss-map
        k.blob("M110 390 C140 260 260 150 430 140 S700 190 790 300 C760 390 600 430 430 425 S170 430 110 390 Z",
               T.PANEL2, T.GREEN)
        for x, y, c, lab in [
            (240, 260, T.CYAN, "KERNEL"), (420, 200, T.AMBER, "DRIVER"),
            (580, 250, T.VIOLET, "TOOL"), (360, 350, T.RED, "LIB"), (640, 360, T.GREEN, "COMMUNITY"),
        ]:
            k.circle(x, y, 14, c, T.PANEL, cls="hd-pulse")
            k.line(x, y + 14, x, y + 34, c)
            k.label(x, y + 52, lab, c, 8)
        k.path("M254 262 C320 240 360 225 405 212 M435 205 C490 212 530 230 565 244 M375 340 C400 300 405 260 415 215 M595 262 C620 300 630 330 636 350 M255 272 C300 310 330 330 350 344",
               T.CYAN, cls="hd-flow")

    return k.footer()


def main(argv: list[str]) -> int:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_dir = os.path.join(root, "assets", "illustrations")
    os.makedirs(out_dir, exist_ok=True)
    only = {item.zfill(2) for item in argv[1:]}
    count = 0
    mid_count = 0
    part_count = 0
    app_count = 0
    for ch, title, zh, aria, scene in CHAPTERS:
        number = f"{ch:02d}"
        if only and number not in only:
            continue
        path = os.path.join(out_dir, f"ch{number}-handdraw.svg")
        chapter_scene(ch, title, aria, scene).save(path)
        xml.dom.minidom.parse(path)
        print(f"[ok] {os.path.relpath(path, root)}")
        count += 1
    for ch, zh, aria, _anchor_zh, _anchor_en, scene in MID:
        number = f"{ch:02d}"
        if only and number not in only:
            continue
        path = os.path.join(out_dir, f"ch{number}-mid-handdraw.svg")
        mid_scene(ch, zh, aria, scene).save(path)
        xml.dom.minidom.parse(path)
        print(f"[ok] {os.path.relpath(path, root)}")
        mid_count += 1
    if not only:
        for index, zh, aria, scene in PARTS:
            part_id = f"p{index - 1}"
            path = os.path.join(out_dir, f"part-{part_id}-handdraw.svg")
            part_scene(index, zh, aria, scene).save(path)
            xml.dom.minidom.parse(path)
            print(f"[ok] {os.path.relpath(path, root)}")
            part_count += 1
        for letter, _appendix_id, zh, aria, scene in APPENDICES:
            path = os.path.join(out_dir, f"app-{letter}-handdraw.svg")
            appendix_scene(letter, zh, aria, scene).save(path)
            xml.dom.minidom.parse(path)
            print(f"[ok] {os.path.relpath(path, root)}")
            app_count += 1
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
            "mid": [
                {
                    "chapter": f"{ch:02d}",
                    "file": f"ch{ch:02d}-mid-handdraw.svg",
                    "zh": zh,
                    "en": aria,
                    "anchor_zh": anchor_zh,
                    "anchor_en": anchor_en,
                }
                for ch, zh, aria, anchor_zh, anchor_en, _scene in MID
            ],
            "appendices": [
                {
                    "id": appendix_id,
                    "file": f"app-{letter}-handdraw.svg",
                    "zh": zh,
                    "en": aria,
                }
                for letter, appendix_id, zh, aria, _scene in APPENDICES
            ],
        }
        manifest_path = os.path.join(out_dir, "manifest.json")
        with open(manifest_path, "w", encoding="utf-8") as handle:
            json.dump(manifest, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        print(f"[ok] {os.path.relpath(manifest_path, root)}")
    print(f"generated {count} chapter, {mid_count} mid-chapter, "
          f"{part_count} part and {app_count} appendix illustrations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

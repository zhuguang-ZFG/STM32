# -*- coding: utf-8 -*-
"""Handraw knowledge-track figure kit: deterministic hand-drawn SVG builder.

Visual grammar mirrors the yang0/handraw-style knowledge track already in
assets/illustrations/handraw/ (cream paper, wobbly ink strokes, Prussian blue /
sage green / brick red / Naples yellow, footer badge 原理示意 / 非实拍).

Everything is deterministic: seeded per-figure RNG, no network, no timestamps,
so re-running the script reproduces byte-identical SVG (and PNG once rendered).
"""

from __future__ import annotations

import math
import random
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "assets" / "illustrations" / "handraw"

W, H = 1152, 864

PAPER = "#FDF8EA"
INK = "#2F2E2B"
GREEN = "#3F7D57"
GREEN_D = "#2E5F42"
BLUE = "#2B5EA7"
BLUE_D = "#1F4680"
RED = "#B3392F"
AMBER_FILL = "#F6D576"
AMBER_STROKE = "#A8801F"
GRAY_FILL = "#E7E4DB"
MUTED = "#6E6B60"
WHITE = "#FFFFFF"

HAND = "'Segoe Print','Comic Sans MS','Microsoft YaHei','PingFang SC',sans-serif"


def esc(s: str) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def text_w(s: str, size: float) -> float:
    """Rough advance width: CJK ≈ 1.0em, Latin ≈ 0.55em, space 0.30em."""
    w = 0.0
    for ch in s:
        o = ord(ch)
        if o > 0x2E80:            # CJK ranges
            w += 1.0
        elif ch == " ":
            w += 0.32
        elif ch in "iljtf.,:;'|!":
            w += 0.30
        elif ch in "mMW":
            w += 0.85
        else:
            w += 0.55
    return w * size


class Fig:
    """One 1152x864 handraw figure."""

    def __init__(self, seed: str, title: str, title_color: str = INK,
                 badge: str = "原理示意 / 非实拍"):
        self.rng = random.Random(seed)
        self.seed = seed
        self.body: list[str] = []
        self.title = title
        self.title_color = title_color
        self.badge = badge

    # -- low level ------------------------------------------------------
    def _wob(self, x0, y0, x1, y1, amp=1.6):
        """Wobbly polyline points between two endpoints (deterministic)."""
        r = self.rng
        dx, dy = x1 - x0, y1 - y0
        dist = math.hypot(dx, dy)
        n = max(2, int(dist / 26))
        ux, uy = (dx / dist, dy / dist) if dist else (0.0, 0.0)
        px, py = -uy, ux
        pts = []
        for i in range(n + 1):
            t = i / n
            # ease toward exact endpoints
            a = amp * (1.0 - abs(2 * t - 1)) * 0.55 + 0.45
            off = r.uniform(-a, a)
            jx = r.uniform(-1.0, 1.0)
            jy = r.uniform(-1.0, 1.0)
            pts.append((x0 + dx * t + px * off + jx * 0.6,
                        y0 + dy * t + py * off + jy * 0.6))
        return pts

    def _poly_pts(self, pts, close=False, amp=1.6):
        seq = list(pts)
        if close and seq[0] != seq[-1]:
            seq = seq + [seq[0]]
        out = []
        for a, b in zip(seq, seq[1:]):
            out.append(self._wob(a[0], a[1], b[0], b[1], amp))
        flat = []
        for seg in out:
            flat.extend(seg)
        if not flat:
            flat = [seq[0]]
        return flat

    def _d(self, pts):
        d = f"M{pts[0][0]:.1f} {pts[0][1]:.1f}"
        for x, y in pts[1:]:
            d += f" L{x:.1f} {y:.1f}"
        return d

    def stroke(self, pts, color=INK, sw=2.6, amp=1.6, opacity=1.0,
               close=False, dash=None, cls=None):
        flat = self._poly_pts(pts, close=close, amp=amp)
        dashattr = f' stroke-dasharray="{dash}"' if dash else ""
        clsattr = f' class="{cls}"' if cls else ""
        self.body.append(
            f'<path d="{self._d(flat)}" fill="none" stroke="{color}" '
            f'stroke-width="{sw}" stroke-linecap="round" '
            f'stroke-linejoin="round" opacity="{opacity}"{dashattr}{clsattr}/>'
        )

    def line(self, x0, y0, x1, y1, **kw):
        self.stroke([(x0, y0), (x1, y1)], **kw)

    def rect(self, x, y, w, h, color=GREEN, sw=2.8, fill=None, r=6,
             amp=1.8, dash=None, opacity=1.0, double=True):
        if fill:
            self.body.append(
                f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" '
                f'fill="{fill}"/>'
            )
        pts = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
        self.stroke(pts, color=color, sw=sw, amp=amp, close=True,
                    dash=dash, opacity=opacity)
        if double and not dash:
            # faint second pencil pass, tiny offset
            self.stroke([(x + 2.2, y - 1.4), (x + w + 1.4, y + 2.0),
                         (x + w - 2.0, y + h + 1.4), (x - 1.4, y + h - 2.0)],
                        color=color, sw=1.1, amp=amp + 0.4, close=True,
                        opacity=0.28)

    def circle(self, x, y, rr, color=INK, sw=2.6, fill=None, amp=1.6):
        if fill:
            self.body.append(f'<circle cx="{x}" cy="{y}" r="{rr}" fill="{fill}"/>')
        r = self.rng
        pts = []
        n = 26
        a0 = r.uniform(0, 6.28)
        for i in range(n + 1):
            a = a0 + (i / n) * math.tau
            wob = 1 + r.uniform(-0.012, 0.012)
            pts.append((x + rr * wob * math.cos(a), y + rr * wob * math.sin(a)))
        self.stroke(pts, color=color, sw=sw, amp=amp, close=False)

    def blob(self, x, y, w, h, fill, color=None, sw=0, amp=3.2):
        """Rounded hand-drawn filled blob (for highlight bars)."""
        r = self.rng
        cx, cy = x + w / 2, y + h / 2
        n = 12
        pts = []
        for i in range(n):
            a = (i / n) * math.tau
            k = 1 + r.uniform(-0.02, 0.02)
            pts.append((cx + k * w / 2 * math.cos(a), cy + k * h / 2 * math.sin(a)))
        d = self._d(self._poly_pts(pts, close=True, amp=amp))
        extra = f' stroke="{color}" stroke-width="{sw}"' if color else ""
        self.body.append(f'<path d="{d}" fill="{fill}"{extra}/>')

    def panel(self, x, y, w, h, fill, color=None, sw=0, amp=2.2, r=8):
        """Slightly wobbly rounded-rect fill (matches panel grammar)."""
        # jitter each edge inward/outward a touch
        j = [self.rng.uniform(-amp, amp) for _ in range(4)]
        pts = [(x + j[0], y + j[1]), (x + w + j[2], y - j[1] * 0.4),
               (x + w - j[0] * 0.4, y + h + j[3]), (x - j[2] * 0.3, y + h - j[1])]
        d = self._d(self._poly_pts(pts, close=True, amp=amp * 0.6))
        extra = f' stroke="{color}" stroke-width="{sw}"' if color else ""
        self.body.append(f'<path d="{d}" fill="{fill}"{extra}/>')

    def fillrect(self, x, y, w, h, fill, r=6):
        self.body.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" '
            f'fill="{fill}"/>'
        )

    def arrow(self, x0, y0, x1, y1, color=BLUE, sw=3.0, bend=0.18,
              head=11):
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        dx, dy = x1 - x0, y1 - y0
        dist = math.hypot(dx, dy) or 1.0
        px, py = -dy / dist, dx / dist
        cx, cy = mx + px * dist * bend, my + py * dist * bend
        # shorten so the head sits on the target
        ux, uy = dx / dist, dy / dist
        ex, ey = x1 - ux * 5, y1 - uy * 5
        d = f"M{x0:.1f} {y0:.1f} Q{cx:.1f} {cy:.1f} {ex:.1f} {ey:.1f}"
        self.body.append(
            f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{sw}" '
            f'stroke-linecap="round"/>'
        )
        # end tangent of the quadratic at t=1
        tx, ty = ex - cx, ey - cy
        self.arrowhead(ex, ey, tx, ty, color=color, head=head)

    def arrowhead(self, x, y, tx, ty, color=BLUE, head=11):
        dist = math.hypot(tx, ty) or 1.0
        ux, uy = tx / dist, ty / dist
        px, py = -uy, ux
        a = (x - ux * head + px * head * 0.55, y - uy * head + py * head * 0.55)
        b = (x - ux * head - px * head * 0.55, y - uy * head - py * head * 0.55)
        self.stroke([(a[0], a[1]), (x, y), (b[0], b[1])], color=color, sw=3.0,
                    amp=0.8)

    # -- text -----------------------------------------------------------
    def text(self, x, y, s, size=26, color=INK, anchor="start", weight="normal",
             font=HAND, ls=None, halo=True):
        weightattr = f' font-weight="{weight}"' if weight != "normal" else ""
        anchorattr = f' text-anchor="{anchor}"' if anchor != "start" else ""
        halocl = ' class="t-halo"' if halo else ""
        self.body.append(
            f'<text x="{x}" y="{y}" font-family="{font}" font-size="{size}"'
            f'{weightattr}{anchorattr} fill="{color}"{halocl}>{esc(s)}</text>'
        )

    def htext(self, x, y, s, size=26, color=INK, anchor="start", weight="normal",
              hl=None, hl_fill=AMBER_FILL, pad=8):
        """Text with optional yellow highlight bar behind it."""
        w = text_w(s, size)
        if anchor == "middle":
            x0 = x - w / 2
        elif anchor == "end":
            x0 = x - w
        else:
            x0 = x
        if hl:
            self.blob(x0 - pad, y - size * 0.82, w + 2 * pad, size * 1.16,
                      hl_fill, amp=2.6)
        self.text(x, y, s, size=size, color=color, anchor=anchor, weight=weight)

    def multi(self, x, y, lines, size=26, color=INK, lh=None, anchor="start",
              weight="normal"):
        lh = lh or size * 1.42
        for i, ln in enumerate(lines):
            self.text(x, y + i * lh, ln, size=size, color=color,
                      anchor=anchor, weight=weight)

    # -- chrome ---------------------------------------------------------
    def chrome(self):
        """Paper, title, footer badge."""
        self.body.insert(0, f'<rect width="{W}" height="{H}" fill="{PAPER}"/>')
        if self.title:
            self.text(W / 2, 74, self.title, size=46, color=self.title_color,
                      anchor="middle", weight="bold", halo=False)
            # hand underline swash
            tw = text_w(self.title, 46)
            y0 = 92
            pts = [(W / 2 - tw / 2 + self.rng.uniform(-6, 6), y0)]
            for i in range(1, 7):
                t = i / 6
                pts.append((W / 2 - tw / 2 + tw * t,
                            y0 + self.rng.uniform(-3.5, 3.5)))
            self.stroke(pts, color=self.rng.choice([GREEN, AMBER_STROKE]),
                        sw=3.0, amp=2.0, opacity=0.75)
        if self.badge:
            bw = text_w(self.badge, 30) + 56
            bx, by = W / 2 - bw / 2, H - 86
            self.blob(bx, by, bw, 56, WHITE, amp=3.0)
            self.rect(bx, by, bw, 56, color=MUTED, sw=2.6, fill=None,
                      amp=2.6, double=False, r=10)
            self.text(W / 2, by + 38, self.badge, size=30, color=MUTED,
                      anchor="middle", weight="bold", halo=False)

    def svg(self) -> str:
        self.chrome()
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" '
            f'height="{H}" viewBox="0 0 {W} {H}">\n'
            f'<style>text{{dominant-baseline:alphabetic}} '
            f'.t-halo{{paint-order:stroke;stroke:{PAPER};stroke-width:7px; '
            f'stroke-linejoin:round}}</style>\n'
            + "\n".join(self.body) + "\n</svg>\n"
        )


def save(fig: Fig, path: str):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(fig.svg())

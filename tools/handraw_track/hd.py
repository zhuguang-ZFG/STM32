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
AMBER_STROKE = "#8A6510"   # 5.0:1 on paper; #A8801F was only 3.4:1
GRAY_FILL = "#E7E4DB"
MUTED = "#6E6B60"
WHITE = "#FFFFFF"

# Soft tints for large panels. Outlines stay saturated; the tint carries the
# panel without turning the plate into a wall of white boxes.
# Two consumers, different rules:
#  * the staged v0/v1/v2/b3 family (fig_v0.py, fig_v1*.py, fig_v2a.py,
#    fig_merged_b3.py, fig_learning.py) takes these names directly and ships
#    through docs/public/images/ — changing a value here DOES repaint them;
#  * the 285 chNN/app plates pass literal hexes ("#FBEFD3", ...) instead, so
#    these names do not reach them. Retint those by editing the literal.
# Hue, not darkness: darkening a panel always costs dark-ink contrast, so the
# tints sit at their original lightness with more saturation (GREEN_FILL
# chroma 9 -> 21, BLUE_FILL 17 -> 25). Every ink keeps or improves its ratio
# against them (floor 4.25 GREEN on BLUE_FILL, 4.36 on GREEN_FILL).
BLUE_FILL = "#E4F0FD"
GREEN_FILL = "#E2F7E5"
AMBER_PALE = "#FBF0D2"
RED_FILL = "#F8E6E1"
SHADOW = "#E4DCC9"

# Keep Latin in Segoe Print; give CJK a brush/kai fallback instead of the
# geometric YaHei sans. The PNGs are committed, so this only affects renders.
HAND = ("'Segoe Print','STKaiti','KaiTi','Microsoft YaHei',"
        "'PingFang SC',sans-serif")

# Fine print stays typeset: below 18 px the brush face loses too much
# legibility and its wider advance overflows tight technical panels.
SMALL = "'Microsoft YaHei','PingFang SC',sans-serif"


def esc(s: str) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def text_w(s: str, size: float) -> float:
    """Rough advance width: CJK ≈ 1.0em, Latin ≈ 0.63em, space 0.40em.

    Calibrated against the real Segoe Print / KaiTi stack in Chromium
    (see .temp/handdraw-quality/charwidths.json): the old 0.55/0.32/0.85
    weights under-estimated by 10-25 % and made highlight bars and title
    shrink too tight.
    """
    w = 0.0
    for ch in s:
        o = ord(ch)
        if o > 0x2E80:            # CJK ranges
            w += 1.0
        elif ch == " ":
            w += 0.40
        elif ch in "iljtf.,:;'|!":
            w += 0.32
        elif ch in "mMW":
            w += 1.0
        else:
            w += 0.63
    return w * size


class Fig:
    """One 1152x864 handraw figure."""

    def __init__(self, seed: str, title: str, title_color: str = INK,
                 badge: str = "原理示意 / 非实拍", tag: str | None = None,
                 grid: bool = True):
        self.rng = random.Random(seed)
        self.seed = seed
        self.body: list[str] = []
        self.title = title
        self.title_color = title_color
        self.badge = badge
        self.tag = tag
        self.grid = grid

    # -- low level ------------------------------------------------------
    def _wob(self, x0, y0, x1, y1, amp=1.6):
        """Wobbly polyline points between two endpoints (deterministic).

        A confident pen line bows once across its length and trembles only
        slightly; the old per-26px random zigzag read as a shaking hand.
        The bow fades out at both ends and short strokes get a proportionally
        smaller bow so arrows and small glyphs stay readable.
        """
        r = self.rng
        dx, dy = x1 - x0, y1 - y0
        dist = math.hypot(dx, dy)
        n = max(2, int(dist / 26))
        ux, uy = (dx / dist, dy / dist) if dist else (0.0, 0.0)
        px, py = -uy, ux
        # one bow per stroke, scaled down for short segments
        a = amp * min(1.0, dist / 70.0)
        bow = r.uniform(-1.0, 1.0) * a * 1.05
        phase = r.uniform(0.0, math.tau)
        tremor = a * 0.34
        pts = []
        for i in range(n + 1):
            t = i / n
            env = math.sin(math.pi * t)  # exact at both endpoints
            off = bow * env + tremor * env * math.sin(math.tau * 1.4 * t + phase)
            pts.append((x0 + dx * t + px * off, y0 + dy * t + py * off))
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

    def _d_smooth(self, pts):
        """Closed Catmull-Rom-like path: quadratic through edge midpoints.

        A 26-gon with per-point noise reads as a polygon at large radii; this
        keeps a hand-drawn wobble while the outline itself stays round.
        """
        n = len(pts)
        mid = lambda a, b: ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        start = mid(pts[-1], pts[0])
        d = f"M{start[0]:.1f} {start[1]:.1f}"
        for i in range(n):
            p = pts[i]
            q = pts[(i + 1) % n]
            m = mid(p, q)
            d += f" Q{p[0]:.1f} {p[1]:.1f} {m[0]:.1f} {m[1]:.1f}"
        return d + " Z"

    def _box_pts(self, x, y, w, h, r=6):
        """Rounded box outline; the corners read as a pen change of direction."""
        rr = max(0.0, min(r, w * 0.24, h * 0.24))
        if rr < 1.0:
            return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
        pts = []
        for cx, cy, a0 in (
            (x + rr, y + rr, math.pi),
            (x + w - rr, y + rr, math.pi * 1.5),
            (x + w - rr, y + h - rr, 0.0),
            (x + rr, y + h - rr, math.pi * 0.5),
        ):
            for i in range(3):
                a = a0 + (math.pi * 0.5) * i / 2
                pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
        return pts

    def stroke(self, pts, color=INK, sw=2.6, amp=1.6, opacity=1.0,
               close=False, dash=None, cls=None, fill=None, texture=None):
        flat = self._poly_pts(pts, close=close, amp=amp)
        dashattr = f' stroke-dasharray="{dash}"' if dash else ""
        clsattr = f' class="{cls}"' if cls else ""
        fillattr = f' fill="{fill}"' if fill else ' fill="none"'
        self.body.append(
            f'<path d="{self._d(flat)}"{fillattr} stroke="{color}" '
            f'stroke-width="{sw}" stroke-linecap="round" '
            f'stroke-linejoin="round" opacity="{opacity}"{dashattr}{clsattr}/>'
        )
        # Pen texture: a pen never lands on its own line twice. One looser,
        # thinner second pass gives the doubled-edge look that separates ink
        # from clip-art. Skipped for hairlines, dashes, already-faint layers
        # and animated paths, where the ghost reads as a blur instead.
        if texture is None:
            texture = (fill is None and dash is None and cls is None
                       and opacity >= 0.6 and sw >= 1.8)
        if texture:
            ghost = self._poly_pts(pts, close=close, amp=amp * 1.35 + 0.25)
            self.body.append(
                f'<path d="{self._d(ghost)}" fill="none" stroke="{color}" '
                f'stroke-width="{sw * 0.52:.2f}" stroke-linecap="round" '
                f'stroke-linejoin="round" opacity="0.22"/>'
            )

    def line(self, x0, y0, x1, y1, **kw):
        self.stroke([(x0, y0), (x1, y1)], **kw)

    def rect(self, x, y, w, h, color=GREEN, sw=2.8, fill=None, r=6,
             amp=1.8, dash=None, opacity=1.0, double=True):
        # Fill and outline share the same wobbled path. A crisp <rect> under a
        # wobbly stroke leaves a visible ghost edge and reads as clip-art.
        # `double` now selects the shared pen-texture pass in stroke(), so a
        # box is never drawn twice by two different mechanisms.
        pts = self._box_pts(x, y, w, h, r)
        self.stroke(pts, color=color, sw=sw, amp=amp, close=True,
                    dash=dash, opacity=opacity, fill=fill,
                    texture=(double and not dash))

    def circle(self, x, y, rr, color=INK, sw=2.6, fill=None, amp=1.6):
        r = self.rng
        n = 32
        a0 = r.uniform(0, math.tau)
        p1 = r.uniform(0, math.tau)
        p2 = r.uniform(0, math.tau)
        k1 = r.uniform(0.010, 0.020)
        k2 = r.uniform(0.004, 0.010)
        pts = []
        for i in range(n):
            a = a0 + (i / n) * math.tau
            wob = 1 + k1 * math.sin(3 * a + p1) + k2 * math.sin(5 * a + p2)
            pts.append((x + rr * wob * math.cos(a), y + rr * wob * math.sin(a)))
        fillattr = f' fill="{fill}"' if fill else ' fill="none"'
        self.body.append(
            f'<path d="{self._d_smooth(pts)}"{fillattr} stroke="{color}" '
            f'stroke-width="{sw}" stroke-linecap="round" '
            'stroke-linejoin="round"/>'
        )
        if fill is None and sw >= 1.8 and rr >= 12:
            ghost = [(x + (px - x) * 1.035, y + (py - y) * 1.035)
                     for px, py in pts]
            self.body.append(
                f'<path d="{self._d_smooth(ghost)}" fill="none" stroke="{color}" '
                f'stroke-width="{sw * 0.52:.2f}" stroke-linecap="round" '
                'stroke-linejoin="round" opacity="0.22"/>'
            )

    def marker(self, x, y, w, h, fill=AMBER_FILL, opacity=0.92):
        """Highlighter swipe: an uneven bar with slanted ends.

        A symmetric ellipse under a line of text reads as a sticker. A hand
        highlighter lands as a bar that starts and stops unevenly, and the felt
        tip doubles back, so the bar carries a second, fainter pass.
        """
        r = self.rng
        j = [r.uniform(-1.8, 1.8) for _ in range(6)]
        pts = [(x + j[0], y + h * 0.08 + j[1]),
               (x + w * 0.5, y + j[2] * 0.6),
               (x + w + j[3], y - j[1] * 0.8),
               (x + w + j[4] * 0.6, y + h + j[2] * 0.4),
               (x + w * 0.5, y + h + j[5] * 0.5),
               (x - j[3] * 0.5, y + h + j[0] * 0.4)]
        d = self._d(self._poly_pts(pts, close=True, amp=1.5))
        self.body.append(f'<path d="{d}" fill="{fill}" opacity="{opacity}"/>')
        # second pass: a lighter, slightly larger swipe, like a second stroke
        # of the felt tip that didn't quite land on the first.
        pts2 = [(px + r.uniform(-1.2, 1.2), py + r.uniform(-1.0, 1.0))
                for px, py in pts]
        d2 = self._d(self._poly_pts(pts2, close=True, amp=1.8))
        self.body.append(f'<path d="{d2}" fill="{fill}" opacity="0.18"/>')
        # felt tip doubles back: thinner overlap, slightly higher
        k = [r.uniform(-2.2, 2.2) for _ in range(4)]
        top = y + h * 0.16
        pts2 = [(x + 2 + k[0], top + k[1]),
                (x + w * 0.62, top - 1.5 + k[2]),
                (x + w - 4 + k[3], top + k[0])]
        d2 = self._d(self._poly_pts(pts2, amp=1.2))
        self.body.append(
            f'<path d="{d2}" fill="none" stroke="{fill}" '
            f'stroke-width="{h * 0.52:.1f}" stroke-linecap="round" '
            'opacity="0.30"/>'
        )

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
        # faint pen rim so the blob doesn't read as a vector ellipse
        self.body.append(
            f'<path d="{d}" fill="none" stroke="{color or MUTED}" '
            f'stroke-width="1.0" opacity="0.22"/>'
        )

    def panel(self, x, y, w, h, fill, color=None, sw=0, amp=2.2, r=8):
        """Slightly wobbly rounded-rect fill (matches panel grammar)."""
        pts = self._box_pts(x, y, w, h, r)
        d = self._d(self._poly_pts(pts, close=True, amp=amp * 0.6))
        extra = f' stroke="{color}" stroke-width="{sw}"' if color else ""
        self.body.append(f'<path d="{d}" fill="{fill}"{extra}/>')

    def fillrect(self, x, y, w, h, fill, r=6, wob=True):
        """Solid colour block: marker fill, not a printed rectangle.

        A crisp <rect> under a wobbly outline leaves the fill visibly short of
        the ink at every edge, which is the tell that gives a plate away. Large
        blocks therefore fill with the same wobbly panel path; a block with any
        side under 16 px keeps the exact rect, where a sub-pixel wobble would
        only blunt a thin bar or a small chip.
        """
        if wob and w >= 16 and h >= 16:
            self.panel(x, y, w, h, fill, amp=1.1, r=r)
            return
        self.body.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" '
            f'fill="{fill}"/>'
        )

    def arrow(self, x0, y0, x1, y1, color=BLUE, sw=3.0, bend=0.18,
              head=11):
        """Connector: a bowed shaft drawn by the same pen as everything else.

        The shaft used to be one exact `Q` command, the only shape on the plate
        that never went through the wobbler; next to the hand-drawn boxes it
        read as clip-art. Sampling the same bow into pen segments keeps the
        silhouette, adds the tremor and the ghost pass, and still lands exactly
        on both endpoints (the wobble envelope is zero at the ends).
        """
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        dx, dy = x1 - x0, y1 - y0
        dist = math.hypot(dx, dy) or 1.0
        px, py = -dy / dist, dx / dist
        cx, cy = mx + px * dist * bend, my + py * dist * bend
        # shorten so the head sits on the target
        ux, uy = dx / dist, dy / dist
        ex, ey = x1 - ux * 5, y1 - uy * 5
        # ~70 px pen segments: long enough for the bow to register, short
        # enough that a bent shaft still reads as one curved stroke
        n = max(2, int(dist / 70))
        shaft = []
        for i in range(n + 1):
            t = i / n
            b = 1.0 - t
            shaft.append((b * b * x0 + 2 * b * t * cx + t * t * ex,
                          b * b * y0 + 2 * b * t * cy + t * t * ey))
        self.stroke(shaft, color=color, sw=sw, amp=1.5)
        # end tangent of the quadratic at t=1
        tx, ty = ex - cx, ey - cy
        self.arrowhead(ex, ey, tx, ty, color=color, head=head)

    def arrowhead(self, x, y, tx, ty, color=BLUE, head=11):
        dist = math.hypot(tx, ty) or 1.0
        ux, uy = tx / dist, ty / dist
        px, py = -uy, ux
        a = (x - ux * head + px * head * 0.55, y - uy * head + py * head * 0.55)
        b = (x - ux * head - px * head * 0.55, y - uy * head - py * head * 0.55)
        # A solid nib reads at small sizes where an open V dissolves; the
        # slightly bowed base keeps it from looking like a clip-art triangle.
        mx = x - ux * head * 0.92
        my = y - uy * head * 0.92
        self.body.append(
            f'<path d="M{a[0]:.1f} {a[1]:.1f} L{x:.1f} {y:.1f} '
            f'L{b[0]:.1f} {b[1]:.1f} Q{mx:.1f} {my:.1f} {a[0]:.1f} {a[1]:.1f} Z" '
            f'fill="{color}" stroke="{color}" stroke-width="0.9" '
            'stroke-linejoin="round"/>'
        )

    # -- cards, tags, metric blocks ------------------------------------
    def card(self, x, y, w, h, color, fill=WHITE, sw=2.4, shadow=True,
             offset=6):
        """Panel with a soft offset shadow; reads as a card, not a box."""
        if shadow:
            self.panel(x + offset, y + offset, w, h, SHADOW, amp=1.6)
        self.panel(x, y, w, h, fill, amp=1.8)
        self.rect(x, y, w, h, color=color, sw=sw, fill=None, double=False,
                  amp=1.8)

    def pill(self, x, y, w, h, label, color, fill=None, text_color=None,
             size=16, weight="bold"):
        self.panel(x, y, w, h, fill or WHITE, amp=1.4)
        self.rect(x, y, w, h, color=color, sw=2.0, fill=None, double=False,
                  amp=1.4)
        self.text(x + w / 2, y + h / 2 + size * 0.36, label, size=size,
                  color=text_color or color, anchor="middle", weight=weight)

    def metric(self, x, y, value, label, color, value_size=34, label_size=15):
        self.text(x, y, value, size=value_size, color=color, weight="bold")
        self.text(x, y + label_size + 8, label, size=label_size, color=MUTED)

    def section(self, x, y, num, label, color, size=21):
        """Numbered section heading with a small filled circle."""
        self.circle(x + 13, y - size * 0.34, 15, color=color, sw=1.8,
                    fill=color)
        self.text(x + 13, y - size * 0.34 + 5, num, size=13, color=WHITE,
                  anchor="middle", weight="bold", halo=False)
        self.text(x + 38, y, label, size=size, color=color, weight="bold")

    def stamp(self, x, y, label, color=RED, size=20, angle=-11):
        """Rotated ink stamp, used sparingly for a hard verdict."""
        self.body.append(f'<g transform="rotate({angle} {x} {y})">')
        self.rect(x - 116, y - 30, 232, 60, color=color, sw=3, fill=None,
                  double=False, r=8)
        self.text(x, y + 7, label, size=size, color=color, anchor="middle",
                  weight="bold", font=HAND, halo=False)
        self.body.append('</g>')

    # -- pictograms -----------------------------------------------------
    def chip(self, x, y, w, h, color, label=None, size=20, pins=4):
        """MCU / package pictogram: body, notch and pins on both sides."""
        self.rect(x, y, w, h, color=color, sw=2.4, fill=WHITE, double=False)
        self.circle(x + 14, y + 14, 4, color=color, sw=1.4, fill=color)
        for i in range(pins):
            py = y + h * (i + 1) / (pins + 1)
            self.line(x - 12, py, x, py, color=color, sw=2.0, amp=0.3)
            self.line(x + w, py, x + w + 12, py, color=color, sw=2.0, amp=0.3)
        if label:
            self.text(x + w / 2, y + h / 2 + size * 0.36, label, size=size,
                      color=color, anchor="middle", weight="bold")

    def clockface(self, x, y, r, color, label=None, hand=(-1, 2),
                  label_size=15):
        self.circle(x, y, r, color=color, sw=2.2, fill=WHITE)
        for i in range(12):
            a = math.tau * i / 12
            self.line(x + math.cos(a) * (r - 7), y + math.sin(a) * (r - 7),
                      x + math.cos(a) * (r - 2), y + math.sin(a) * (r - 2),
                      color=MUTED, sw=1.0, amp=0.1)
        self.line(x, y, x + hand[0] * r * 0.48, y - hand[1] * r * 0.44,
                  color=color, sw=2.2, amp=0.3)
        self.line(x, y, x + r * 0.52, y + r * 0.18, color=color, sw=1.8,
                  amp=0.3)
        self.circle(x, y, 3, color=color, sw=1.0, fill=color)
        if label:
            self.text(x, y + r + label_size + 6, label, size=label_size,
                      color=MUTED, anchor="middle")

    def gear(self, x, y, r, color, teeth=8):
        for i in range(teeth):
            a = math.tau * i / teeth
            self.line(x + math.cos(a) * (r - 4), y + math.sin(a) * (r - 4),
                      x + math.cos(a) * (r + 7), y + math.sin(a) * (r + 7),
                      color=color, sw=3.0, amp=0.2)
        self.circle(x, y, r, color=color, sw=2.2, fill=WHITE)
        self.circle(x, y, r * 0.38, color=color, sw=1.8, fill=None)

    def wave(self, x, y, w, h, color, kind="sine", cycles=2, duty=0.5,
             sw=2.4):
        pts = []
        n = max(24, cycles * 16)
        for i in range(n + 1):
            t = i / n
            if kind == "square":
                yy = h if (t * cycles) % 1 < duty else 0
            elif kind == "pwm":
                yy = h if (t * cycles) % 1 < duty else 0
            else:
                yy = (1 - math.sin(t * math.tau * cycles)) * h / 2
            pts.append((x + w * t, y + yy))
        self.stroke(pts, color=color, sw=sw, amp=0.5)

    def doc(self, x, y, w, h, color, label=None, size=15):
        fold = min(24, w * 0.18)
        self.stroke([(x, y), (x + w, y), (x + w, y + h - fold),
                     (x + w - fold, y + h), (x, y + h)], color=color,
                    sw=2.2, close=True, fill=WHITE)
        self.line(x + w, y + h - fold, x + w - fold, y + h - fold,
                  color=color, sw=1.8)
        self.line(x + w - fold, y + h - fold, x + w - fold, y + h,
                  color=color, sw=1.8)
        if label:
            self.text(x + w / 2, y + h / 2 + size * 0.34, label, size=size,
                      color=color, anchor="middle", weight="bold")

    def icon_copy(self, x, y, s, color):
        self.rect(x, y, s * 0.56, s * 0.68, color=color, sw=1.8,
                  fill=WHITE, double=False)
        self.rect(x + s * 0.30, y + s * 0.22, s * 0.56, s * 0.68,
                  color=color, sw=1.8, fill=WHITE, double=False)

    def icon_trash(self, x, y, s, color):
        self.line(x, y + s * 0.18, x + s * 0.8, y + s * 0.18, color=color,
                  sw=2.2)
        self.line(x + s * 0.2, y + s * 0.18, x + s * 0.26, y + s * 0.82,
                  color=color, sw=2.0)
        self.line(x + s * 0.6, y + s * 0.18, x + s * 0.54, y + s * 0.82,
                  color=color, sw=2.0)
        self.line(x + s * 0.26, y + s * 0.82, x + s * 0.54, y + s * 0.82,
                  color=color, sw=2.0)
        self.line(x + s * 0.3, y + s * 0.06, x + s * 0.5, y + s * 0.06,
                  color=color, sw=2.0)

    def icon_merge(self, x, y, s, color):
        self.arrow(x, y + s * 0.12, x + s * 0.44, y + s * 0.5, color=color,
                   sw=2.0, bend=0, head=7)
        self.arrow(x + s * 0.8, y + s * 0.12, x + s * 0.56, y + s * 0.5,
                   color=color, sw=2.0, bend=0, head=7)
        self.arrow(x + s * 0.5, y + s * 0.5, x + s * 0.5, y + s * 0.9,
                   color=color, sw=2.0, bend=0, head=7)

    def gate(self, x, y, w, h, color, num):
        """Door pictogram with a number plate; the EXTI chain reads as gates."""
        self.rect(x, y, w, h, color=color, sw=2.4, fill=WHITE)
        self.rect(x + 18, y + 18, w - 36, h - 18, color=color, sw=1.8,
                  fill=None, double=False)
        self.circle(x + w - 38, y + h / 2, 4, color=color, sw=1.2, fill=color)
        self.pill(x + 6, y + 6, 26, 24, num, color, fill=WHITE, size=13)

    def envelope(self, x, y, w, h, color, label=None, size=15):
        self.rect(x, y, w, h, color=color, sw=2.0, fill=WHITE, double=False)
        self.line(x, y, x + w / 2, y + h * 0.56, color=color, sw=1.6)
        self.line(x + w, y, x + w / 2, y + h * 0.56, color=color, sw=1.6)
        if label:
            self.text(x + w / 2, y + h * 0.82, label, size=size, color=color,
                      anchor="middle", weight="bold")

    def motor(self, x, y, s, color, label="M"):
        self.circle(x + s * 0.42, y + s * 0.48, s * 0.32, color=color, sw=2.2,
                    fill=WHITE)
        self.text(x + s * 0.42, y + s * 0.58, label, size=s * 0.34,
                  color=color, anchor="middle", weight="bold")
        self.line(x + s * 0.74, y + s * 0.48, x + s * 0.96, y + s * 0.48,
                  color=color, sw=2.4)
        for i in range(4):
            a = math.tau * i / 4 + 0.5
            self.line(x + s * 0.42 + math.cos(a) * s * 0.38,
                      y + s * 0.48 + math.sin(a) * s * 0.38,
                      x + s * 0.42 + math.cos(a) * s * 0.48,
                      y + s * 0.48 + math.sin(a) * s * 0.48,
                      color=color, sw=1.8)

    def magnifier(self, x, y, s, color):
        self.circle(x + s * 0.38, y + s * 0.38, s * 0.28, color=color, sw=2.4,
                    fill=WHITE)
        self.line(x + s * 0.58, y + s * 0.62, x + s * 0.9, y + s * 0.94,
                  color=color, sw=3.0)

    # -- text -----------------------------------------------------------
    def text(self, x, y, s, size=26, color=INK, anchor="start", weight="normal",
             font=HAND, ls=None, halo=True, opacity=1.0, hand_min=0):
        if not str(s).strip():
            return  # empty spacer line: keep the row slot, emit no <text>
        if font == HAND and hand_min and size < hand_min:
            font = SMALL
        weightattr = f' font-weight="{weight}"' if weight != "normal" else ""
        anchorattr = f' text-anchor="{anchor}"' if anchor != "start" else ""
        halocl = ' class="t-halo"' if halo else ""
        opattr = f' opacity="{opacity}"' if opacity != 1.0 else ""
        self.body.append(
            f'<text x="{x}" y="{y}" font-family="{font}" font-size="{size}"'
            f'{weightattr}{anchorattr} fill="{color}"{halocl}{opattr}>'
            f'{esc(s)}</text>'
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
            self.marker(x0 - pad, y - size * 0.82, w + 2 * pad, size * 1.16,
                        fill=hl_fill)
        self.text(x, y, s, size=size, color=color, anchor=anchor, weight=weight)

    def multi(self, x, y, lines, size=26, color=INK, lh=None, anchor="start",
              weight="normal"):
        lh = lh or size * 1.42
        for i, ln in enumerate(lines):
            self.text(x, y + i * lh, ln, size=size, color=color,
                      anchor=anchor, weight=weight)

    # -- chrome ---------------------------------------------------------
    def _accent_color(self):
        """Stable accent for the title swash: same seed, same ink.

        The old draw came from the shared RNG, so changing any brush primitive
        silently repainted every title. A dedicated seeded pick keeps the
        accent stable across future brush work.
        """
        return random.Random(self.seed + ":accent").choice([GREEN, AMBER_STROKE])

    def chrome(self):
        """Paper, title, footer badge."""
        defs = ""
        if self.grid:
            defs = (
                '<defs><pattern id="dotgrid" width="24" height="24" '
                'patternUnits="userSpaceOnUse"><circle cx="3" cy="3" r="1.1" '
                'fill="#DED4BE"/></pattern></defs>'
            )
        bg = f'<rect width="{W}" height="{H}" fill="{PAPER}"/>'
        if self.grid:
            bg += (f'<rect width="{W}" height="{H}" fill="url(#dotgrid)" '
                   'opacity="0.36"/>')
        # paper fibers: a few long, faint, wobbly lines so the sheet doesn't
        # read as a flat vector rectangle.
        fibers = ""
        for _ in range(12):
            y = self.rng.uniform(40, H - 40)
            x0 = self.rng.uniform(-30, 30)
            x1 = W + self.rng.uniform(-30, 30)
            d = self._d(self._wob(x0, y, x1, y, amp=self.rng.uniform(0.6, 1.8)))
            fibers += (f'<path d="{d}" fill="none" stroke="#C9BEA6" '
                       f'stroke-width="0.8" opacity="{self.rng.uniform(0.025, 0.05):.3f}"/>')
        # SVG paints children in document order: keep the fibers above the
        # opaque paper and the optional grid so the texture remains visible.
        bg += fibers
        self.body.insert(0, defs + bg)
        tsize = 50
        if self.title:
            # auto-shrink long titles so they never clip the canvas
            # (Segoe Print runs ~25% wider than the estimator, so pad it)
            while text_w(self.title, tsize) * 1.30 > W - 80 and tsize > 28:
                tsize -= 2
        if self.tag:
            tw = text_w(self.tag, 15) + 30
            # long centered titles reach into the top-left corner; park the
            # tag bottom-left instead of letting the title overwrite it
            tag_right = 56 + text_w(self.tag, 15) * 1.25 + 30
            title_left = (W / 2 - text_w(self.title, tsize) * 0.85 / 2
                          if self.title else W)
            ty = 30 if title_left >= tag_right + 12 else H - 60
            self.panel(56, ty, tw, 30, PAPER, amp=1.2)
            self.rect(56, ty, tw, 30, color=MUTED, sw=1.4, fill=None,
                      double=False, amp=1.2)
            self.text(56 + tw / 2, ty + 21, self.tag, size=15, color=MUTED,
                      anchor="middle", weight="bold", halo=False)
        if self.title:
            # offset ink pass under the title: a print plate never lands twice
            # in the same place, and the doubled edge gives the title weight
            self.text(W / 2 + 3, 77, self.title, size=tsize, color=INK,
                      anchor="middle", weight="bold", halo=False,
                      opacity=0.16)
            self.text(W / 2, 74, self.title, size=tsize, color=self.title_color,
                      anchor="middle", weight="bold", halo=False)
            # hand underline: one heavy swash, one thin rider below
            tw = text_w(self.title, tsize) * 1.22
            y0 = 95
            pts = [(W / 2 - tw / 2 + self.rng.uniform(-6, 6), y0)]
            for i in range(1, 7):
                t = i / 6
                pts.append((W / 2 - tw / 2 + tw * t,
                            y0 + self.rng.uniform(-3.5, 3.5)))
            self.stroke(pts, color=self._accent_color(), sw=4.2, amp=2.0,
                        opacity=0.85)
            rider = [(x, y + 9 + self.rng.uniform(-1.5, 1.5))
                     for x, y in pts[1:]]
            self.stroke([pts[0]] + rider, color=INK, sw=1.5, amp=1.4,
                        opacity=0.30)
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

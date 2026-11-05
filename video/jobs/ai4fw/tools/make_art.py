"""风格 4 插画生成器：小豆人黑色涂鸦信息图（白底黑线 + 单橙焦点 + 红蓝箭头，纯图形无文字）。
确定性：zlib.crc32 种子，重跑字节级一致。数字一律走视频动作层，不烙进图。"""
import json
import math
import random
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # jobs/ai4fw
SRC = ROOT / 'inputs' / 'images' / 'src'
INK, ORANGE, RED, BLUE = '#26221E', '#F08900', '#7A2418', '#2A5FA8'
W = 9
BUILDERS = {}
PARTS = {}
WIDTHS = {}


def visual(name, width):
    def deco(fn):
        BUILDERS[name] = fn
        WIDTHS[name] = width
        return fn
    return deco


def rng_for(name):
    return random.Random(zlib.crc32(name.encode('utf-8')))


def jitter(pts, rng, amp=7):
    return [(x + rng.uniform(-amp, amp), y + rng.uniform(-amp, amp)) for x, y in pts]


def smooth(points, closed=True):
    """Catmull-Rom 平滑成三次贝塞尔；closed 闭合（Z），open 首末克隆端点。"""
    p = list(points)
    if not p:
        return ''
    if closed:
        at = lambda i: p[i % len(p)]
        starts = range(len(p))
        first = p[0]
    else:
        at = lambda i: p[max(0, min(len(p) - 1, i))]
        starts = range(len(p) - 1)
        first = p[0]
    d = ['M %.1f,%.1f' % first]
    for i in starts:
        p0, p1, p2, p3 = at(i - 1), at(i), at(i + 1), at(i + 2)
        c1 = (p1[0] + (p2[0] - p0[0]) / 6., p1[1] + (p2[1] - p0[1]) / 6.)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6., p2[1] - (p3[1] - p1[1]) / 6.)
        d.append('C %.1f,%.1f %.1f,%.1f %.1f,%.1f' % (c1 + c2 + p2))
    if closed:
        d.append('Z')
    return ' '.join(d)


def rect_pts(x, y, w, h):
    return [(x, y), (x + w * .5, y), (x + w, y), (x + w, y + h * .5),
            (x + w, y + h), (x + w * .5, y + h), (x, y + h), (x, y + h * .5)]


def ell_pts(cx, cy, rx, ry, n=12):
    return [(cx + rx * math.cos(2 * math.pi * i / n),
             cy + ry * math.sin(2 * math.pi * i / n)) for i in range(n)]


def line_pts(x1, y1, x2, y2, segs=4):
    return [(x1 + (x2 - x1) * i / segs, y1 + (y2 - y1) * i / segs)
            for i in range(segs + 1)]


def arc_pts(cx, cy, r, a0, a1, n=8, ry=None):
    ry = r if ry is None else ry
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / n),
             cy + ry * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


def ink(d, color=INK, width=W):
    return ('<path d="%s" fill="none" stroke="%s" stroke-width="%s" '
            'stroke-linecap="round" stroke-linejoin="round"/>' % (d, color, width))


def shape(d, fill, width=W, color=INK):
    return ('<path d="%s" fill="%s" stroke="%s" stroke-width="%s" '
            'stroke-linejoin="round"/>' % (d, fill, color, width))


def blob(d, fill=INK):
    return '<path d="%s" fill="%s" stroke="none"/>' % (d, fill)


def arrow(x1, y1, x2, y2, color, bend=.3, head=54):
    mx, my = (x1 + x2) / 2., (y1 + y2) / 2.
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy) or 1.
    cx, cy = mx - dy / L * bend * L, my + dx / L * bend * L
    d = 'M %.0f,%.0f Q %.0f,%.0f %.0f,%.0f' % (x1, y1, cx, cy, x2, y2)
    ax, ay = x2 - cx, y2 - cy
    al = math.hypot(ax, ay) or 1.
    a = math.atan2(ay / al, ax / al)
    for s in (-1, 1):
        t = a + s * .5
        d += ' M %.0f,%.0f L %.0f,%.0f' % (x2, y2,
                                           x2 - head * math.cos(t),
                                           y2 - head * math.sin(t))
    return ink(d, color)


def page(elements):
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1920" '
            'viewBox="0 0 1080 1920"><rect width="1080" height="1920" fill="#FFFFFF"/>'
            + ''.join(elements) + '</svg>')


def arrow_flat(x1, y1, x2, y2, color, bend=.3):
    """Single-stroke curved arrow: one ink curve + a filled triangular head (no wing strokes)."""
    mx, my = (x1 + x2) / 2., (y1 + y2) / 2.
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy) or 1.
    cx, cy = mx - dy / L * bend * L, my + dx / L * bend * L
    shaft = 'M %.0f,%.0f Q %.0f,%.0f %.0f,%.0f' % (x1, y1, cx, cy, x2, y2)
    a = math.atan2(y2 - cy, x2 - cx)
    head = [(x2, y2), (x2 - 40 * math.cos(a - .5), y2 - 40 * math.sin(a - .5)),
            (x2 - 40 * math.cos(a + .5), y2 - 40 * math.sin(a + .5))]
    return [ink(shaft, color), blob(smooth(jitter(head, random.Random(1), 2)), color)]


def part(vid, pid, x, y, w, h, exclude=None):
    n = lambda v: round(v, 4)
    entry = {
        'id': pid,
        'polygon': [[n(x / 1080), n(y / 1920)], [n((x + w) / 1080), n(y / 1920)],
                    [n((x + w) / 1080), n((y + h) / 1920)], [n(x / 1080), n((y + h) / 1920)]],
    }
    if exclude:
        entry['exclude_boxes'] = [[n(ex / 1080), n(ey / 1920), n((ex + ew) / 1080), n((ey + eh) / 1920)]
                                  for ex, ey, ew, eh in exclude]
    PARTS.setdefault(vid, []).append(entry)


@visual('v01', 880)
def v01():
    r = rng_for('v01')
    e = []
    e.append(ink(smooth(jitter(rect_pts(170, 480, 640, 450), r))))            # 代码窗口
    e.append(ink(smooth(jitter(line_pts(190, 595, 790, 595), r, 4), False)))  # 标题栏
    for y, x2 in ((685, 640), (765, 720), (845, 560)):
        e.append(ink(smooth(jitter(line_pts(215, y, x2, y), r, 5), False)))   # 代码行
    e.extend(arrow_flat(880, 690, 680, 1130, RED, -.3))                 # 红箭头
    e.append(shape(smooth(jitter(rect_pts(230, 1180, 640, 230), r)), ORANGE)) # 胶片条
    for x in (420, 660):
        e.append(ink(smooth(jitter(line_pts(x, 1212, x, 1378), r, 3), False)))  # 分格
    for x in range(255, 855, 75):                                              # 上下两排齿孔
        e.append(blob(smooth(jitter(rect_pts(x, 1197, 36, 20), r, 2)), '#FFFFFF'))
        e.append(blob(smooth(jitter(rect_pts(x, 1373, 36, 20), r, 2)), '#FFFFFF'))
    part('v01', 'window', 118, 428, 744, 524)
    part('v01', 'arrow', 610, 610, 400, 570)
    part('v01', 'film', 176, 1126, 748, 338)
    return e


@visual('v02', 900)
def v02():
    r = rng_for('v02')
    e = []
    x0, y0, cw, ch, g = 103, 300, 270, 180, 32
    for row in range(3):
        for col in range(3):
            x, y = x0 + col * (cw + g), y0 + row * (ch + g)
            d = smooth(jitter(rect_pts(x, y, cw, ch), r, 2))
            if (row, col) != (1, 1):
                e.append(ink(d))                                             # 格架方格
    e.append(shape(smooth(jitter(rect_pts(x0 + cw + g, y0 + ch + g, cw, ch), r, 5)), ORANGE))  # 橙色中心格
    e.append(arrow(900, 150, 560, 560, BLUE, .35))                           # 蓝箭头指橙格
    part('v02', 'wall', 70, 270, 940, 665)
    part('v02', 'arrow', 530, 140, 380, 450)
    return e


@visual('v03', 840)
def v03():
    r = rng_for('v03')
    e = []
    star = []
    for i in range(10):
        rad = 215 if i % 2 == 0 else 90
        a = -math.pi / 2 + i * math.pi / 5
        star.append((330 + rad * math.cos(a), 1160 + rad * math.sin(a)))
    e.append(shape(smooth(jitter(star, r, 6)), ORANGE))                       # 星徽章（下半带）
    e.append(ink(smooth(jitter(ell_pts(760, 1400, 160, 160, 14), r))))        # 胶片卷
    e.append(ink(smooth(jitter(ell_pts(760, 1400, 52, 52, 10), r, 4))))       # 卷轴芯
    e.append(ink(smooth(jitter(line_pts(625, 1420, 565, 1470), r, 3), False)))  # 拖尾胶片上边
    e.append(ink(smooth(jitter(line_pts(645, 1468, 580, 1518), r, 3), False)))  # 拖尾胶片下边
    e.append(arrow(530, 1120, 630, 1280, RED, .3))
    part('v03', 'star', 95, 930, 465, 520)
    part('v03', 'roll', 520, 1225, 415, 360, exclude=[(520, 1225, 140, 75)])
    part('v03', 'arrow', 520, 1110, 140, 190)
    return e


@visual('v04', 900)
def v04():
    r = rng_for('v04')
    e = []
    e.append(ink(smooth(jitter(ell_pts(430, 420, 345, 190, 14), r))))         # 调色盘（上半带）
    for (cx, cy), rr in (((300, 350), 40), ((585, 355), 40)):
        e.append(shape(smooth(jitter(ell_pts(cx, cy, rr, rr, 10), r, 4)), '#FFFFFF'))
    e.append(ink(smooth(jitter(ell_pts(445, 290, 40, 40, 10), r, 4)), ORANGE, 24))  # 橙环色格
    e.append(ink(smooth(jitter(rect_pts(300, 730, 500, 300), r))))            # 语法小卡
    for y, x2 in ((820, 620), (900, 560)):
        e.append(ink(smooth(jitter(line_pts(330, y, x2, y), r, 4), False)))   # 三条横线
    e.extend(arrow_flat(700, 640, 648, 712, RED, .25))
    part('v04', 'palette', 50, 180, 760, 455)
    part('v04', 'card', 246, 709, 608, 370)
    part('v04', 'arrow', 570, 600, 200, 150)
    return e
@visual('v05', 820)
def v05():
    r = rng_for('v05')
    e = []
    cap = arc_pts(545, 1345, 220, math.pi, 2 * math.pi, 10, ry=250)
    cap = cap + [(650, 1367), (545, 1359), (440, 1367)]                        # 伞底波边
    e.append(shape(smooth(jitter(cap, r, 6)), ORANGE))                       # 蘑菇伞（下半带）
    for cx, cy in ((455, 1210), (635, 1255)):
        e.append(shape(smooth(jitter(ell_pts(cx, cy, 40, 40, 10), r, 3)), '#FFFFFF', 7))  # 白斑
    e.append(ink(smooth(jitter(rect_pts(465, 1395, 170, 250), r, 5))))        # 菌柄
    e.append(blob(smooth(jitter(ell_pts(845, 1330, 52, 38, 10), r, 3))))      # 符头一
    e.append(ink(smooth(jitter(line_pts(893, 1322, 893, 1150), r, 4), False)))  # 符干一
    part('v05', 'mushroom', 300, 1075, 490, 600)
    part('v05', 'notes', 780, 1125, 270, 270)
    return e


@visual('v06', 900)
def v06():
    r = rng_for('v06')
    e = []
    for y in (610, 690, 770):
        e.append(ink(smooth(jitter(line_pts(120, y, 950, y), r, 7), False)))  # 三线谱
    for cx, cy in ((220, 610), (540, 690), (860, 610)):
        e.append(blob(smooth(jitter(ell_pts(cx, cy, 46, 34, 10), r, 3))))    # 音符头
    e.extend(arrow_flat(950, 540, 760, 1110, BLUE, -.3))
    e.append(shape(smooth(jitter(rect_pts(340, 1180, 420, 310), r)), ORANGE))  # 成片帧
    for x in range(362, 745, 68):                                              # 上下两排齿孔
        e.append(blob(smooth(jitter(rect_pts(x, 1197, 32, 18), r, 2)), '#FFFFFF'))
        e.append(blob(smooth(jitter(rect_pts(x, 1453, 32, 18), r, 2)), '#FFFFFF'))
    e.append(blob(smooth(jitter([(520, 1290), (520, 1380), (600, 1335)], r, 3)), '#FFFFFF'))  # 播放三角
    part('v06', 'staff', 100, 556, 870, 250)
    part('v06', 'arrow', 660, 460, 370, 730)
    part('v06', 'frame', 300, 1140, 510, 390)
    return e


@visual('v07', 880)
def v07():
    r = rng_for('v07')
    e = []
    e.append(ink(smooth(jitter(ell_pts(390, 795, 140, 140, 14), r))))         # 头（描边圆）
    e.append(blob(smooth(jitter(ell_pts(340, 780, 15, 15, 8), r, 2))))        # 左眼点
    e.append(blob(smooth(jitter(ell_pts(440, 780, 15, 15, 8), r, 2))))        # 右眼点
    e.append(ink(smooth(jitter(ell_pts(390, 1065, 130, 100, 12), r))))        # 躯干（描边椭圆）
    e.append(ink(smooth(jitter(line_pts(275, 1015, 120, 905), r, 4), False)))   # 左臂
    e.append(ink(smooth(jitter(line_pts(505, 1015, 655, 895), r, 4), False)))   # 右臂
    e.append(ink(smooth(jitter([(328, 1270), (345, 1140), (435, 1140), (455, 1270)], r, 3), False)))  # 双腿一笔
    e.append(blob(smooth(jitter([(662, 866), (688, 856), (762, 1008), (735, 992)], r, 3)), ORANGE))  # 画笔（单块笔形）
    e.append(ink(smooth(jitter(arc_pts(760, 1160, 150, math.radians(95),
                                     math.radians(255), 10), r, 4), False)))  # 自画像弧
    part('v07', 'head', 245, 655, 290, 290)
    part('v07', 'torso', 260, 950, 260, 200)
    part('v07', 'left_arm', 105, 890, 180, 140)
    part('v07', 'right_arm', 490, 880, 180, 140)
    part('v07', 'lower_body', 310, 1130, 165, 150)
    part('v07', 'pen', 645, 845, 165, 185)
    part('v07', 'portrait', 590, 990, 360, 370)
    return e
@visual('v08', 760)
def v08():
    r = rng_for('v08')
    e = []
    e.append(ink(smooth(jitter(rect_pts(140, 540, 800, 760), r))))            # 选型表外框
    e.append(ink(smooth(jitter(line_pts(155, 730, 925, 730), r, 6), False)))  # 行线一
    e.append(ink(smooth(jitter(line_pts(155, 920, 925, 920), r, 6), False)))  # 行线二
    e.append(ink(smooth(jitter(line_pts(155, 1110, 925, 1110), r, 6), False)))  # 行线三
    e.append(ink(smooth(jitter(line_pts(500, 555, 500, 1285), r, 6), False)))  # 竖线
    e.append(ink(smooth(jitter(rect_pts(200, 590, 95, 65), r, 4))))           # 抽屉图标
    e.append(ink(smooth(jitter(line_pts(212, 622, 283, 622), r, 3), False)))
    e.append(ink(smooth(jitter(ell_pts(248, 825, 50, 32, 10), r, 3))))        # 调色盘图标
    e.append(blob(smooth(jitter(ell_pts(248, 1030, 38, 27, 10), r, 3))))       # 音符图标头
    e.append(ink(smooth(jitter(line_pts(283, 1015, 283, 965), r, 3), False)))  # 符干
    e.append(ink(smooth(jitter(line_pts(205, 1205, 292, 1247), r, 3), False), INK, 16))  # 画笔图标
    e.extend(arrow_flat(525, 645, 690, 660, ORANGE, .25))
    e.extend(arrow_flat(525, 835, 690, 850, ORANGE, .25))
    e.extend(arrow_flat(525, 975, 690, 990, ORANGE, .25))
    e.extend(arrow_flat(525, 1190, 690, 1205, ORANGE, .25))
    part('v08', 'table', 86, 486, 908, 868, exclude=[(180, 531, 180, 769), (476, 591, 268, 668)])
    part('v08', 'icons', 180, 541, 180, 759)
    part('v08', 'arrow', 481, 596, 258, 658)
    return e


@visual('v10', 560)
def v10():
    r = rng_for('v10')
    e = []
    e.append(ink(smooth(jitter([(410, 950), (560, 975), (710, 950), (790, 1130),
                                (770, 1310), (560, 1335), (350, 1310), (330, 1130)], r, 5))))  # 纸身
    for y, x2 in ((1105, 685), (1215, 635)):
        e.append(ink(smooth(jitter(line_pts(405, y, x2, y), r, 4), False)))   # 清单横线
    clip = ('M 790 1335 L 790 1252 Q 790 1222 820 1222 L 872 1222 Q 902 1222 902 1252 '
            'L 902 1390 Q 902 1420 872 1420 L 826 1420 Q 796 1420 796 1390 '
            'L 796 1300 Q 796 1275 821 1275 L 848 1275 Q 868 1275 868 1298 L 868 1330')
    e.append(ink(clip, ORANGE, 10))                                           # 橙色回形针
    part('v10', 'sheet', 320, 930, 480, 420)
    part('v10', 'clip', 780, 1210, 130, 220)
    return e


@visual('cover', 1080)
def cover():
    r = rng_for('cover')
    e = []
    e.append(ink(smooth(jitter(rect_pts(240, 300, 560, 380), r))))            # 代码窗口
    e.append(ink(smooth(jitter(line_pts(258, 408, 782, 408), r, 4), False)))  # 标题栏
    for y, x2 in ((480, 560), (545, 640), (615, 470)):
        e.append(ink(smooth(jitter(line_pts(270, y, x2, y), r, 4), False)))   # 代码行
    e.append(arrow(830, 520, 700, 900, RED, -.3))
    strip = [shape(smooth(jitter(rect_pts(260, 740, 640, 190), r)), ORANGE)]  # 斜胶片
    for x in (420, 580, 740):
        strip.append(ink(smooth(jitter(line_pts(x, 768, x, 902), r, 3), False)))
    for x in range(285, 880, 75):                                              # 齿孔
        strip.append(blob(smooth(jitter(rect_pts(x, 756, 34, 18), r, 2)), '#FFFFFF'))
        strip.append(blob(smooth(jitter(rect_pts(x, 896, 34, 18), r, 2)), '#FFFFFF'))
    e.append('<g transform="rotate(16 580 835)">' + ''.join(strip) + '</g>')
    e.append('<text x="540" y="1235" font-family="KaiTi,STKaiti,serif" font-size="150" '
             'font-weight="700" text-anchor="middle" fill="#26221E">不用大模型</text>')
    e.append('<text x="540" y="1405" font-family="KaiTi,STKaiti,serif" font-size="150" '
             'font-weight="700" text-anchor="middle" fill="#26221E">代码出片</text>')
    e.append('<text x="540" y="1585" font-family="KaiTi,STKaiti,serif" font-size="62" '
             'text-anchor="middle" fill="#6A6257">369 仓库 · 四强盘点</text>')
    e.append('<text x="540" y="1730" font-family="KaiTi,STKaiti,serif" font-size="46" '
             'text-anchor="middle" fill="#9A9186">AI 视频工具盘点</text>')
    return e


def main():
    SRC.mkdir(parents=True, exist_ok=True)
    for name, fn in BUILDERS.items():
        (SRC / (name + '.svg')).write_text(page(fn()), encoding='utf-8')
        print('SVG', name)
    out = {'widths': WIDTHS, 'parts': PARTS}
    (ROOT / 'inputs' / 'images' / 'parts.json').write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
    print('parts.json', sum(len(v) for v in PARTS.values()), 'parts')


if __name__ == '__main__':
    main()

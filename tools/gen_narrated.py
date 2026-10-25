#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_narrated.py —— 把每章讲解做成带中文配音和字幕的 MP4。

画面：Pillow 绘制的标题卡 / 步骤卡，并贴上本仓库自己的 SVG（动画或引脚图的一帧）。
画面字体由 ``NARRATED_FONT`` 指定；默认使用文泉驿微米黑（GPL-3，带字体嵌入例外）。

配音：微软 Edge 在线神经语音 zh-CN-XiaoxiaoNeural（「晓晓」），
经 edge-tts 调用。edge-tts 大部分源码是 LGPLv3，srt_composer.py 是 MIT
（见 https://github.com/rany2/edge-tts/blob/master/LICENSE ）。
声线模型本身是微软在线服务，不是可再分发的开放模型；本仓库提交的是
合成后的教学 MP4，方便离线观看。重新生成需要联网，并保持同一个声线名。
在线合成不是逐比特稳定的，所以 ``make assets`` 只重画海报，不重跑配音。

用法::

    python3 tools/gen_narrated.py --check          # 只检查排版，不联网
    python3 tools/gen_narrated.py --posters        # 写每章海报 PNG
    python3 tools/gen_narrated.py --speak          # 配音 + ffmpeg 合成 MP4 与 SRT
    python3 tools/gen_narrated.py --speak 13       # 只做某一章
    python3 tools/gen_narrated.py --patch-docs     # 把播放器嵌回中英文章节
"""

from __future__ import annotations

import asyncio
import glob
import io
import math
import os
import shutil
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from importlib import import_module  # noqa: E402

CHAPTERS = import_module(os.environ.get("NARRATED_MODULE", "narration")).CHAPTERS  # noqa: E402

SCALE = float(os.environ.get("NARRATED_SCALE", "1"))
if SCALE < 1:
    raise ValueError("NARRATED_SCALE 必须 >= 1")
W, H = int(round(960 * SCALE)), int(round(540 * SCALE))
BAND_TOP = int(round(448 * SCALE))
PAD = 0.35
VOICE = "zh-CN-XiaoxiaoNeural"
RATE = "-6%"
FONT = os.environ.get("NARRATED_FONT", "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc")

# 校准自本机 edge-tts 7.2.8、rate=-8% 的一次短句（51 字 / 13.27 秒）。
# --check 只用它估算，成片时长以 ffprobe 为准。
EST_SEC_PER_CHAR = 13.27 / 51
MIN_SEC = float(os.environ.get("NARRATED_MIN_SEC", "120"))
MAX_SEC = float(os.environ.get("NARRATED_MAX_SEC", "240"))

BG = (23, 26, 36)
BG2 = (32, 37, 54)
BAND = (12, 14, 20)
CYAN = (72, 214, 198)
AMBER = (255, 186, 92)
TEXT = (236, 239, 244)
MUTED = (168, 178, 196)
LINE = (58, 68, 88)

VOICE_NOTE = (
    "配音是微软 Edge 在线神经语音「晓晓」（zh-CN-XiaoxiaoNeural），"
    "经 edge-tts 调用。edge-tts 大部分源码为 LGPLv3，srt_composer.py 为 MIT；"
    "声线模型是微软在线服务，不是开放模型。这里提交的是合成后的 MP4，离线可看。"
    "重新生成需要联网。画面由脚本和本仓库 SVG 生成，不是实拍。"
)


def _font(size):
    from PIL import ImageFont
    return ImageFont.truetype(FONT, int(round(size * SCALE)), index=0)


def _width(text, font):
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (8, 8))
    return ImageDraw.Draw(img).textlength(text, font=font)


def wrap_text(text, font, max_w, max_lines, what):
    lines, cur = [], ""
    for ch in text:
        trial = cur + ch
        if not cur or _width(trial, font) <= max_w:
            cur = trial
            continue
        lines.append(cur)
        cur = ch
    if cur:
        lines.append(cur)
    if len(lines) > max_lines:
        raise ValueError(f"{what} 超出 {max_lines} 行：{text}")
    for line in lines:
        if _width(line, font) > max_w + 0.5:
            raise ValueError(f"{what} 单行超宽：{line}")
    return lines


_BADGES = (
    ("口诀", "口诀", AMBER),
    ("最常忘", "坑", (255, 120, 96)),
    ("坑", "坑", (255, 120, 96)),
    ("下一集", "下集", CYAN),
    ("合上书", "自测", (150, 210, 255)),
    ("收尾", "完", (150, 255, 190)),
)


def _badge_for(head):
    for key, label, col in _BADGES:
        if key in head:
            return label, col
    return None


def _mascot(draw, cx, cy, mood, t, k=1.0):
    """小芯：一块带眼睛的芯片。mood = calm / happy / worried；t 驱动轻微上下浮动。"""
    sc = lambda v: int(round(v * k))
    lw = max(1, sc(3))
    cy += int(3 * math.sin(t * 6.28318))
    draw.line((cx, cy - sc(44), cx, cy - sc(56)), fill=CYAN, width=lw)
    draw.ellipse((cx - sc(5), cy - sc(64), cx + sc(5), cy - sc(54)), fill=AMBER)
    draw.rounded_rectangle((cx - sc(44), cy - sc(38), cx + sc(44), cy + sc(38)), radius=sc(10),
                           fill=(38, 44, 62), outline=CYAN, width=lw)
    for i in range(4):
        yy = cy - sc(24) + i * sc(16)
        draw.line((cx - sc(44), yy, cx - sc(56), yy), fill=LINE, width=lw)
        draw.line((cx + sc(44), yy, cx + sc(56), yy), fill=LINE, width=lw)
    ex = sc(18)
    if mood == "happy":
        draw.arc((cx - ex - sc(11), cy - sc(20), cx - ex + sc(11), cy + sc(2)), 200, 340, fill=TEXT, width=lw)
        draw.arc((cx + ex - sc(11), cy - sc(20), cx + ex + sc(11), cy + sc(2)), 200, 340, fill=TEXT, width=lw)
        draw.arc((cx - sc(11), cy + sc(8), cx + sc(11), cy + sc(24)), 0, 180, fill=AMBER, width=lw)
    elif mood == "worried":
        draw.line((cx - ex - sc(9), cy - sc(12), cx - ex + sc(9), cy - sc(2)), fill=TEXT, width=lw)
        draw.line((cx + ex - sc(9), cy - sc(12), cx + ex + sc(9), cy - sc(2)), fill=TEXT, width=lw)
        draw.arc((cx - sc(10), cy + sc(18), cx + sc(10), cy + sc(30)), 200, 340, fill=MUTED, width=lw)
    else:
        draw.ellipse((cx - ex - sc(6), cy - sc(10), cx - ex + sc(6), cy + sc(2)), fill=TEXT)
        draw.ellipse((cx + ex - sc(6), cy - sc(10), cx + ex + sc(6), cy + sc(2)), fill=TEXT)
        draw.line((cx - sc(9), cy + sc(16), cx + sc(9), cy + sc(16)), fill=MUTED, width=lw)


_HD_BG_CACHE = {}


def _hd_background():
    """缓存的深色渐变底 + 极浅斜线纹理；避免逐帧重复绘制。"""
    from PIL import Image, ImageDraw
    key = (W, H)
    if key not in _HD_BG_CACHE:
        img = Image.new("RGB", (W, H), BG)
        d = ImageDraw.Draw(img)
        bottom = (29, 34, 48)
        for yy in range(H):
            q = yy / max(1, H - 1)
            col = tuple(int(round(BG[i] * (1 - q) + bottom[i] * q)) for i in range(3))
            d.line((0, yy, W, yy), fill=col)
        step = max(80, int(round(120 * SCALE)))
        for xx in range(-H, W + H, step):
            d.line((xx, 0, xx + H, H), fill=(26, 31, 44), width=max(1, int(SCALE)))
        _HD_BG_CACHE[key] = img
    return _HD_BG_CACHE[key].copy()


def _render_card_hd(ch, seg, index, t=1.0, gprog=None, line=None, u=1.0):
    """高清版式：更大正文/字幕、要点面板、真实逐条高亮、更大的小芯。"""
    from PIL import Image, ImageDraw
    sc = lambda v: int(round(v * SCALE))
    t = 0.0 if t < 0 else (1.0 if t > 1 else float(t))
    img = _hd_background()
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, W, sc(46)), fill=BG2)
    draw.rectangle((0, 0, sc(6), sc(46)), fill=CYAN)
    title_font = _font(20)
    title = f"{ch['id']}  {ch['title']}"
    wrap_text(title, title_font, W - sc(120), 1, f"{ch['id']} 标题")
    draw.text((sc(16), sc(12)), title, font=title_font, fill=TEXT)
    step = f"{index}/{len(ch['segments'])}"
    sw = _width(step, title_font)
    draw.text((W - sc(16) - sw, sc(12)), step, font=title_font, fill=CYAN)

    head_font = _font(34)
    head_lines = wrap_text(seg["head"], head_font, W - sc(64), 1, f"{ch['id']} 卡标题")
    slide = int(sc(18) * (1.0 - min(1.0, t / 0.4)))
    typed = head_lines[0]
    if t < 0.6:
        typed = typed[: max(1, int(len(typed) * t / 0.6))]
    draw.text((sc(32) - slide, sc(62)), typed, font=head_font, fill=AMBER)
    bar_w = int(sc(96) * min(1.0, t / 0.55))
    if bar_w > 0:
        draw.rectangle((sc(32), sc(100), sc(32) + bar_w, sc(103)), fill=CYAN)
    badge = _badge_for(seg["head"])
    if badge:
        label, col = badge
        bf = _font(18)
        bw = _width(label, bf) + sc(22)
        draw.rounded_rectangle((W - sc(34) - bw, sc(56), W - sc(34), sc(90)), radius=sc(8), fill=col)
        draw.text((W - sc(34) - bw + sc(11), sc(60)), label, font=bf, fill=BG)

    if seg.get("svg"):
        shot = _svg_png(seg["svg"])
        box = (sc(32), sc(108), W - sc(32), BAND_TOP - sc(36))
        pasted = _fit(shot, box[2] - box[0], box[3] - box[1])
        zoom = 1.0 + 0.04 * max(0.0, min(1.0, u))
        if zoom > 1.001:
            zw, zh = int(pasted.width * zoom), int(pasted.height * zoom)
            z = pasted.resize((zw, zh), Image.Resampling.LANCZOS)
            ox, oy = (zw - pasted.width) // 2, (zh - pasted.height) // 2
            pasted = z.crop((ox, oy, ox + pasted.width, oy + pasted.height))
        px = box[0] + (box[2] - box[0] - pasted.width) // 2
        py = box[1] + (box[3] - box[1] - pasted.height) // 2
        if t >= 1.0:
            img.paste(pasted, (px, py))
        else:
            region = img.crop((px, py, px + pasted.width, py + pasted.height))
            img.paste(Image.blend(region, pasted, max(0.0, (t - 0.35) / 0.65)), (px, py))
    else:
        lines = seg["lines"]
        body_font = _font(27)
        panel_x0, panel_x1 = sc(28), W - sc(270)
        panel_y0 = sc(132)
        max_text_w = panel_x1 - panel_x0 - sc(48)
        wrapped = [wrap_text(txt, body_font, max_text_w, 1, f"{ch['id']} 要点")[0]
                   for txt in lines]
        panel_y1 = panel_y0 + sc(48) + len(lines) * sc(58)
        if panel_y1 > BAND_TOP - sc(24):
            raise ValueError(f"{ch['id']} 要点面板叠进字幕带：{seg['head']}")
        shift = max(0, min(sc(30), (BAND_TOP - sc(24) - panel_y1) // 2))
        panel_y0 += shift
        panel_y1 += shift
        draw.rounded_rectangle((panel_x0, panel_y0, panel_x1, panel_y1), radius=sc(18),
                               fill=(27, 32, 46), outline=LINE, width=max(1, sc(1)))
        y = panel_y0 + sc(24)
        for i, txt in enumerate(lines):
            shown = t >= 1.0 or t >= 0.22 + 0.24 * i
            if shown:
                dx = int(sc(12) * (1.0 - min(1.0, max(0.0, (t - (0.22 + 0.24 * i)) / 0.3))))
                active = line is None or i == line
                if line is not None and active:
                    draw.rounded_rectangle((panel_x0 + sc(12), y - sc(6),
                                            panel_x1 - sc(12), y + sc(42)),
                                           radius=sc(8), fill=(35, 47, 60))
                    draw.rectangle((panel_x0 + sc(12), y - sc(6),
                                    panel_x0 + sc(16), y + sc(42)), fill=CYAN)
                draw.text((panel_x0 + sc(28) + dx, y), wrapped[i], font=body_font,
                          fill=TEXT if active else MUTED)
            y += sc(58)
        mood = ("happy" if (badge and badge[0] == "口诀")
                else "worried" if (badge and badge[0] == "坑") else "calm")
        _mascot(draw, W - sc(165), sc(275) + shift, mood, u, k=1.4 * SCALE)

    draw.rectangle((0, BAND_TOP, W, H), fill=BAND)
    draw.line((0, BAND_TOP, W, BAND_TOP), fill=LINE, width=max(1, sc(2)))
    sub_font = None
    sub_lines = None
    for sub_size in (23, 22, 21, 20, 19, 18):
        candidate = _font(sub_size)
        try:
            sub_lines = wrap_text(seg["say"], candidate, W - sc(64), 2, f"{ch['id']} 字幕")
            sub_font = candidate
            break
        except ValueError:
            continue
    if sub_font is None:
        sub_lines = wrap_text(seg["say"], _font(18), W - sc(64), 2, f"{ch['id']} 字幕")
        sub_font = _font(18)
    sy = BAND_TOP + sc(14)
    for txt in sub_lines:
        draw.text((sc(32), sy), txt, font=sub_font, fill=TEXT)
        sy += sc(30)
    note_font = _font(14)
    note = "程序生成画面 · 不是实拍"
    nw = _width(note, note_font)
    draw.text((W - sc(16) - nw, BAND_TOP - sc(20)), note, font=note_font, fill=MUTED)
    if gprog is not None:
        gp = 0.0 if gprog < 0 else (1.0 if gprog > 1 else float(gprog))
        draw.rectangle((0, H - sc(4), W, H), fill=BG2)
        if gp > 0:
            draw.rectangle((0, H - sc(4), int(W * gp), H), fill=CYAN)
    return img


def render_card(ch, seg, index, t=1.0, gprog=None, line=None, u=1.0):
    """画一帧。字幕画在底部深色带里，正文停在带子上方。

    t      —— 入场进度（0→1）：卡标题从左滑入、要点逐条出现、插图渐显、青条扫过；
    line   —— 当前正在讲第几条要点（其余条变淡），None 表示不高亮；
    gprog  —— 整集进度（0→1），画在最底部一条细进度条。
    t=1、line=None 就是完整帧（海报用它）。
    """
    if SCALE != 1:
        return _render_card_hd(ch, seg, index, t, gprog, line, u)
    from PIL import Image, ImageDraw

    t = 0.0 if t < 0 else (1.0 if t > 1 else float(t))
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, W, 46), fill=BG2)
    draw.rectangle((0, 0, 6, 46), fill=CYAN)
    title_font = _font(20)
    title = f"{ch['id']}  {ch['title']}"
    wrap_text(title, title_font, W - 120, 1, f"{ch['id']} 标题")
    draw.text((16, 12), title, font=title_font, fill=TEXT)
    step = f"{index}/{len(ch['segments'])}"
    sw = _width(step, title_font)
    draw.text((W - 16 - sw, 12), step, font=title_font, fill=CYAN)

    head_font = _font(32)
    head_lines = wrap_text(seg["head"], head_font, W - 64, 1, f"{ch['id']} 卡标题")
    slide = int(18 * (1.0 - min(1.0, t / 0.4)))
    typed = head_lines[0]
    if t < 0.6:
        typed = typed[: max(1, int(len(typed) * t / 0.6))]      # 打字机式出现
    draw.text((32 - slide, 62), typed, font=head_font, fill=AMBER)
    bar_w = int(96 * min(1.0, t / 0.55))
    if bar_w > 0:
        draw.rectangle((32, 100, 32 + bar_w, 103), fill=CYAN)
    badge = _badge_for(seg["head"])
    if badge:
        label, col = badge
        bf = _font(18)
        bw = _width(label, bf) + 22
        draw.rounded_rectangle((W - 34 - bw, 56, W - 34, 90), radius=8, fill=col)
        draw.text((W - 34 - bw + 11, 60), label, font=bf, fill=BG)

    y = 112
    if seg.get("svg"):
        shot = _svg_png(seg["svg"])
        box = (32, 108, W - 32, BAND_TOP - 36)
        pasted = _fit(shot, box[2] - box[0], box[3] - box[1])
        zoom = 1.0 + 0.04 * max(0.0, min(1.0, u))               # 缓慢推近
        if zoom > 1.001:
            zw, zh = int(pasted.width * zoom), int(pasted.height * zoom)
            z = pasted.resize((zw, zh), Image.Resampling.LANCZOS)
            ox, oy = (zw - pasted.width) // 2, (zh - pasted.height) // 2
            pasted = z.crop((ox, oy, ox + pasted.width, oy + pasted.height))
        px = box[0] + (box[2] - box[0] - pasted.width) // 2
        py = box[1] + (box[3] - box[1] - pasted.height) // 2
        if t >= 1.0:
            img.paste(pasted, (px, py))
        else:
            region = img.crop((px, py, px + pasted.width, py + pasted.height))
            img.paste(Image.blend(region, pasted, max(0.0, (t - 0.35) / 0.65)), (px, py))
        y = BAND_TOP - 8
    else:
        body_font = _font(26)
        for i, txt in enumerate(seg["lines"]):
            shown = t >= 1.0 or t >= 0.22 + 0.24 * i
            wrapped = wrap_text(txt, body_font, W - 80, 1, f"{ch['id']} 要点")
            if y + 34 > BAND_TOP - 16:
                raise ValueError(f"{ch['id']} 要点叠进字幕带：{txt}")
            if shown:
                dx = 0 if t >= 1.0 else int(12 * (1.0 - min(1.0, max(0.0, (t - (0.22 + 0.24 * i)) / 0.3))))
                col = TEXT if (line is None or i == line) else MUTED
                draw.text((40 + dx, y), wrapped[0], font=body_font, fill=col)
            y += 40
        mood = ("happy" if (badge and badge[0] == "口诀")
                else "worried" if (badge and badge[0] == "坑") else "calm")
        _mascot(draw, W - 132, 248, mood, u)

    draw.rectangle((0, BAND_TOP, W, H), fill=BAND)
    draw.line((0, BAND_TOP, W, BAND_TOP), fill=LINE, width=2)
    sub_font = _font(22)
    sub_lines = wrap_text(seg["say"], sub_font, W - 64, 2, f"{ch['id']} 字幕")
    sy = BAND_TOP + 14
    for line in sub_lines:
        draw.text((32, sy), line, font=sub_font, fill=TEXT)
        sy += 30
    note_font = _font(14)
    note = "程序生成画面 · 不是实拍"
    draw.text((32, 28), "", font=note_font, fill=MUTED)
    nw = _width(note, note_font)
    draw.text((W - 16 - nw, BAND_TOP - 20), note, font=note_font, fill=MUTED)
    if gprog is not None:
        gp = 0.0 if gprog < 0 else (1.0 if gprog > 1 else float(gprog))
        draw.rectangle((0, H - 4, W, H), fill=BG2)
        if gp > 0:
            draw.rectangle((0, H - 4, int(W * gp), H), fill=CYAN)
    return img


def _fit(shot, bw, bh):
    from PIL import Image
    sw, sh = shot.size
    scale = min(bw / sw, bh / sh)
    nw, nh = max(1, int(sw * scale)), max(1, int(sh * scale))
    return shot.resize((nw, nh), Image.Resampling.LANCZOS)


_SVG_CACHE = {}


def _svg_png(rel):
    if rel in _SVG_CACHE:
        return _SVG_CACHE[rel]
    from PIL import Image
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    svg = os.path.join(root, "assets", rel)
    if not os.path.isfile(svg):
        raise SystemExit(f"缺少插图 {svg}")
    tmp = tempfile.mkdtemp(prefix="stm32svg-")
    html = os.path.join(tmp, "card.html")
    out = os.path.join(tmp, "card.png")
    rw, rh = int(round(880 * SCALE)), int(round(300 * SCALE))
    # 深色底，避免白边被当成「照片」。SVG 用仓库原文件。
    page = (
        "<!doctype html><meta charset=utf-8><style>"
        f"html,body{{margin:0;background:#171a24;width:{rw}px;height:{rh}px;overflow:hidden}}"
        f"img{{width:{rw}px;height:{rh}px;object-fit:contain}}"
        f"</style><img src='file://{svg}'>"
    )
    open(html, "w", encoding="utf-8").write(page)
    ud = os.path.join(tmp, "chrome")
    cmd = [
        os.environ.get("NARRATED_CHROME", "google-chrome"), "--headless=new", "--disable-gpu", "--no-sandbox",
        "--hide-scrollbars", "--no-first-run", "--disable-extensions",
        "--force-device-scale-factor=1",
        "--allow-file-access-from-files",
        f"--user-data-dir={ud}",
        "--virtual-time-budget=8000",
        f"--window-size={rw},{rh}",
        f"--screenshot={out}",
        "file://" + html,
    ]
    # 无 D-Bus 时 Chrome 写出 PNG 后往往不退出，截图一落地就结束它。
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    deadline = time.time() + 25
    while time.time() < deadline:
        if os.path.isfile(out) and os.path.getsize(out) > 1000:
            time.sleep(0.4)
            break
        if proc.poll() is not None:
            break
        time.sleep(0.2)
    if proc.poll() is None:
        proc.kill()
        proc.wait(timeout=5)
    if not os.path.isfile(out) or os.path.getsize(out) < 1000:
        raise SystemExit(f"SVG 栅格化失败：{rel}")
    img = Image.open(out).convert("RGB")
    _SVG_CACHE[rel] = img.copy()
    img.close()
    shutil.rmtree(tmp, ignore_errors=True)
    return _SVG_CACHE[rel]


def render_poster(ch):
    return render_card(ch, ch["segments"][0], 1)


def save_png(img, path):
    buf = io.BytesIO()
    img.save(buf, "PNG", compress_level=9)
    data = buf.getvalue()
    if os.path.isfile(path) and open(path, "rb").read() == data:
        return
    open(path, "wb").write(data)


def chapter_name(ch):
    return f"ch{ch['id']}-{ch['slug']}"


def selected(argv):
    keys = [a for a in argv if not a.startswith("-")]
    if not keys:
        return list(CHAPTERS)
    out = []
    for ch in CHAPTERS:
        name = chapter_name(ch)
        if ch["id"] in keys or name in keys:
            out.append(ch)
    if not out:
        raise SystemExit(f"没有匹配的章节：{keys}")
    return out


def check_layout(chapters):
    """排版检查不打开浏览器：带插图的那一帧只验标题和字幕。"""
    ok = True
    for ch in chapters:
        chars = sum(len(s["say"]) for s in ch["segments"])
        est = chars * EST_SEC_PER_CHAR + PAD * len(ch["segments"])
        try:
            for i, seg in enumerate(ch["segments"], start=1):
                probe = {
                    "head": seg["head"],
                    "lines": seg["lines"] or ["本章插图"],
                    "say": seg["say"],
                }
                render_card(ch, probe, i)
            flag = "ok" if MIN_SEC <= est <= MAX_SEC else "SHORT" if est < MIN_SEC else "LONG"
            print(f"[{flag}] {chapter_name(ch)}  {len(ch['segments'])} 段  "
                  f"{chars} 字  估算 {est:.0f}s")
            if flag != "ok":
                ok = False
        except ValueError as exc:
            print(f"[FAIL] {chapter_name(ch)}  {exc}")
            ok = False
    return ok


def write_posters(chapters, out_dir):
    for ch in chapters:
        name = chapter_name(ch)
        save_png(render_poster(ch), os.path.join(out_dir, name + ".png"))
        gif = os.path.join(out_dir, name + ".gif")
        if os.path.isfile(gif):
            os.remove(gif)
        print(f"[poster] {name}.png")


def _ts(seconds):
    if seconds < 0:
        seconds = 0
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _srt(cues):
    blocks = []
    for i, cue in enumerate(cues, start=1):
        blocks.append(f"{i}\n{_ts(cue['start'])} --> {_ts(cue['end'])}\n{cue['say']}\n")
    return "\n".join(blocks)


def _probe_duration(path):
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", path],
        text=True,
    )
    return float(out.strip())


async def _tts(text, dest, sem):
    import edge_tts
    last = None
    for attempt in range(4):
        try:
            async with sem:
                com = edge_tts.Communicate(text, VOICE, rate=RATE)
                await com.save(dest)
            if os.path.getsize(dest) < 800:
                raise RuntimeError("音频过小")
            return
        except Exception as exc:  # 在线服务偶发断开，换一次再试
            last = exc
            await asyncio.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"配音失败：{last}")


FPS = int(os.environ.get("NARRATED_FPS", "8"))  # 每段整段逐帧（入场 1.5 秒走完，其余时间缓慢推进）
CRF = os.environ.get("NARRATED_CRF", "30")
REVEAL = 1.5


def _segment_mp4_anim(work, idx, mp3, dest, dur):
    """整段逐帧 + 音频，一次 ffmpeg 合成（帧序列 f{idx:02d}_%04d.png）。"""
    pattern = os.path.join(work, f"f{idx:02d}_%04d.png")
    subprocess.check_call(
        [
            "ffmpeg", "-y", "-loglevel", "error",
            "-framerate", str(FPS), "-i", pattern,
            "-i", mp3,
            "-filter_complex", f"[1:a]apad=pad_dur={PAD}[a]",
            "-map", "0:v", "-map", "[a]",
            "-t", f"{dur:.3f}",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", CRF,
            "-pix_fmt", "yuv420p", "-r", str(FPS),
            "-c:a", "aac", "-b:a", "40k", "-ac", "1", "-ar", "44100",
            dest,
        ],
        stdout=subprocess.DEVNULL,
    )
    for f in glob.glob(os.path.join(work, f"f{idx:02d}_*.png")):
        try:
            os.remove(f)
        except OSError:
            pass


def _concat(segs, dest):
    lst = dest + ".txt"
    with open(lst, "w", encoding="utf-8") as fh:
        for seg in segs:
            fh.write(f"file '{seg}'\n")
    subprocess.check_call(
        [
            "ffmpeg", "-y", "-loglevel", "error",
            "-f", "concat", "-safe", "0", "-i", lst,
            "-c", "copy", "-movflags", "+faststart",
            dest,
        ],
        stdout=subprocess.DEVNULL,
    )
    os.remove(lst)


async def speak_one(ch, out_dir):
    name = chapter_name(ch)
    for seg in ch["segments"]:
        if seg.get("svg"):
            _svg_png(seg["svg"])
    work = tempfile.mkdtemp(prefix=f"narr-{name}-")
    sem = asyncio.Semaphore(4)
    mp3s = []
    jobs = []
    for i, seg in enumerate(ch["segments"]):
        dest = os.path.join(work, f"{i:02d}.mp3")
        mp3s.append(dest)
        jobs.append(_tts(seg["say"], dest, sem))
    await asyncio.gather(*jobs)

    durs = [_probe_duration(m) + PAD for m in mp3s]
    total = sum(durs) or 1.0
    cues = []
    cursor = 0.0
    segs = []
    for i, seg in enumerate(ch["segments"]):
        dur = durs[i]
        png = os.path.join(work, f"{i:02d}.png")
        render_card(ch, seg, i + 1).save(png, "PNG")   # t=1 完整帧（也是海报形态）
        n_frames = max(2, int(round(dur * FPS)))
        nline = max(1, len(seg.get("lines") or []))
        for k in range(n_frames):
            elapsed = dur * (k / float(n_frames - 1))
            tk = min(1.0, elapsed / REVEAL)
            uk = min(1.0, elapsed / max(0.001, dur))
            line_k = min(nline - 1, int(max(0.0, (uk - 0.12)) * nline / 0.88))
            render_card(ch, seg, i + 1, t=tk, u=uk,
                        gprog=(cursor + elapsed) / total,
                        line=(line_k if uk > 0.10 else None)).save(
                os.path.join(work, f"f{i:02d}_{k + 1:04d}.png"), "PNG")
        mp4 = os.path.join(work, f"{i:02d}.mp4")
        _segment_mp4_anim(work, i, mp3s[i], mp4, dur)
        cues.append({"start": cursor, "end": cursor + dur, "say": seg["say"]})
        cursor += dur
        segs.append(mp4)

    final = os.path.join(out_dir, name + ".mp4")
    _concat(segs, final)
    srt_path = os.path.join(out_dir, name + ".srt")
    open(srt_path, "w", encoding="utf-8").write(_srt(cues))
    save_png(render_poster(ch), os.path.join(out_dir, name + ".png"))
    gif = os.path.join(out_dir, name + ".gif")
    if os.path.isfile(gif):
        os.remove(gif)
    got = _probe_duration(final)
    size = os.path.getsize(final)
    flag = "ok" if MIN_SEC <= got <= MAX_SEC else "RANGE"
    print(f"[{flag}] {name}.mp4  {got:.1f}s  {size / 1048576:.2f} MB  "
          f"字幕 {len(cues)} 条")
    shutil.rmtree(work, ignore_errors=True)
    if not MIN_SEC <= got <= MAX_SEC:
        raise SystemExit(f"{name} 时长 {got:.1f}s 不在 {MIN_SEC / 60:g}–{MAX_SEC / 60:g} 分钟")
    if size > 12 * 1024 * 1024:
        raise SystemExit(f"{name} 超过 12 MB，不适合直接进 git")
    return got, size


def speak(chapters, out_dir):
    total_t = 0.0
    total_b = 0

    async def run():
        nonlocal total_t, total_b
        for ch in chapters:
            dur, size = await speak_one(ch, out_dir)
            total_t += dur
            total_b += size

    asyncio.run(run())
    print(f"合计 {len(chapters)} 章  {total_t / 60:.1f} 分钟  {total_b / 1048576:.1f} MB")
    print("存放：仓库 assets/video/（单章小于 12 MB，直接进 git，不用 LFS / Release）")


def _doc_block(ch, prefix, lang, duration):
    name = chapter_name(ch)
    minutes = f"{duration / 60:.1f} 分钟" if duration else "约 2–4 分钟"
    minutes_en = f"{duration / 60:.1f} min" if duration else "about 2–4 min"
    lines = "\n".join(f"{i}. {s['say']}" for i, s in enumerate(ch["segments"], start=1))
    if lang == "zh":
        return (
            f"<!-- video:ch{ch['id']} -->\n"
            "<p align=\"center\">\n"
            f"  <video width=\"640\" controls poster=\"{prefix}/{name}.png\">\n"
            f"    <source src=\"{prefix}/{name}.mp4\" type=\"video/mp4\">\n"
            "  </video>\n"
            f"  <br><sub>▲ 本章讲解 {minutes}。{VOICE_NOTE} "
            f'视频：<a href="{prefix}/{name}.mp4">MP4</a> · 字幕：<a href="{prefix}/{name}.srt">SRT</a>。'
            "由 <code>python3 tools/gen_narrated.py --speak</code> 用 ffmpeg 合成。</sub>\n"
            "</p>\n\n"
            "**旁白（与字幕、配音同一份稿）**\n\n"
            f"{lines}\n"
            f"<!-- /video:ch{ch['id']} -->\n"
        )
    return (
        f"<!-- video:ch{ch['id']} -->\n"
        "<p align=\"center\">\n"
        f"  <video width=\"640\" controls poster=\"{prefix}/{name}.png\">\n"
        f"    <source src=\"{prefix}/{name}.mp4\" type=\"video/mp4\">\n"
        "  </video>\n"
        f"  <br><sub>▲ Chinese voice-over, {minutes_en}. "
        "Voice: Microsoft Edge neural voice zh-CN-XiaoxiaoNeural via edge-tts "
        "(library mostly LGPLv3; the voice model is an online Microsoft service, not an open model). "
        "Pictures are generated from this repo's SVGs, not photographs. "
        f'Video: <a href="{prefix}/{name}.mp4">MP4</a> · subtitles: <a href="{prefix}/{name}.srt">SRT</a>. '
        "Rebuild with <code>python3 tools/gen_narrated.py --speak</code>.</sub>\n"
        "</p>\n\n"
        "**Narration script (Chinese, same text as the subtitles)**\n\n"
        f"{lines}\n"
        f"<!-- /video:ch{ch['id']} -->\n"
    )


def patch_docs(root, chapters):
    docs = os.path.join(root, "docs")
    video = os.path.join(root, "assets", "video")
    for ch in chapters:
        for folder, prefix, lang in (
            (docs, "../assets/video", "zh"),
            (os.path.join(docs, "en"), "../../assets/video", "en"),
        ):
            name = None
            prefix_id = ch["id"] + "-"
            for fn in os.listdir(folder):
                if fn.startswith(prefix_id) and fn.endswith(".md"):
                    name = fn
                    break
            if name is None:
                raise SystemExit(f"找不到 {folder} 里 {prefix_id}*.md")
            path = os.path.join(folder, name)
            text = open(path, encoding="utf-8").read()
            begin = f"<!-- video:ch{ch['id']} -->"
            end = f"<!-- /video:ch{ch['id']} -->"
            mp4 = os.path.join(video, chapter_name(ch) + ".mp4")
            duration = _probe_duration(mp4) if os.path.isfile(mp4) else None
            block = _doc_block(ch, prefix, lang, duration)
            if begin in text and end in text:
                pre, rest = text.split(begin, 1)
                _, post = rest.split(end, 1)
                text = pre + block + post.lstrip("\n")
            else:
                raise SystemExit(f"{path} 缺少 {begin}")
            open(path, "w", encoding="utf-8").write(text)
            print(f"[doc] {os.path.relpath(path, root)}")


def main(argv):
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)
    out_dir = os.environ.get("NARRATED_OUT", os.path.join(root, "assets", "video"))
    os.makedirs(out_dir, exist_ok=True)
    chapters = selected(argv[1:])
    if "--check" in argv:
        sys.exit(0 if check_layout(chapters) else 1)
    if "--posters" in argv or "--speak" not in argv and "--patch-docs" not in argv:
        if "--speak" not in argv:
            write_posters(chapters, out_dir)
    if "--speak" in argv:
        if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
            raise SystemExit("需要 ffmpeg 和 ffprobe")
        speak(chapters, out_dir)
    if "--patch-docs" in argv:
        patch_docs(root, chapters)


if __name__ == "__main__":
    main(sys.argv)

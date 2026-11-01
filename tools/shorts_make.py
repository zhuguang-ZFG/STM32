#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""竖版样片生成器：首帧即结论，一屏一个概念，字号 >=80px，字幕避开抖音 UI 遮挡。

安全区：顶部 120px、底部 300px 会被播放器 UI 覆盖 -> 内容放 y 200..1380，
字幕条放 y 1400..1600。

用法: python tools/shorts_make.py <章号>
产物: final-videos/chNN/chNN-short.mp4（1080x1920，<=40s）

每章内容写在 SHORTS 里：badge + beats。beats 的 layout 见 LAYOUTS。

注意：已发布的 ch01-short.mp4（2026-10-21 09:44，mid 7698932348557004083）
由重构前的代码生成，重跑本脚本不会得到逐像素一致的输出；不要为了「对齐」
重新上传那条作品，会打断正在进行的留存实验。
"""
from __future__ import annotations

import asyncio
import json
import pathlib
import re
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
W, H = 1080, 1920
BG = (23, 26, 36)
BG2 = (32, 37, 54)
TEXT = (236, 239, 244)
MUTED = (168, 178, 196)
LINE = (58, 68, 88)
CYAN = (72, 214, 198)
AMBER = (255, 186, 92)
RED = (255, 107, 90)
GREEN = (120, 230, 150)
VOICE = "zh-CN-XiaoxiaoNeural"
RATE = "-6%"
FONT_BOLD = "C:/Windows/Fonts/msyhbd.ttc"
FONT_REG = "C:/Windows/Fonts/msyh.ttc"
CAPTION_Y = 1400


def font(size, bold=True):
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size, index=0)


def fit_size(draw, s, size, max_w, bold=True):
    while size > 28:
        f = font(size, bold)
        if draw.textlength(s, font=f) <= max_w:
            return f
        size -= 2
    return font(size, bold)


def wrap(draw, s, f, max_w):
    """按字宽换行，但不切开连续的 ASCII 词。"""
    tokens = re.findall(r"[A-Za-z0-9\.\-]{2,}|.", s)
    lines, cur = [], ""
    for tok in tokens:
        if not cur or draw.textlength(cur + tok, font=f) <= max_w:
            cur += tok
        else:
            lines.append(cur)
            cur = tok
    if cur:
        lines.append(cur)
    return lines


def canvas():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    for y in range(0, H, 8):
        if y % 240 < 8:
            d.line((0, y, W, y), fill=(28, 32, 44))
    return img, d


def badge(d, text, color, y=200):
    f = font(46)
    w = d.textlength(text, font=f)
    d.rounded_rectangle((72, y, 72 + w + 56, y + 84), radius=42, outline=color, width=3)
    d.text((100, y + 16), text, font=f, fill=color)


def headline(d, lines, y, size=104, color=TEXT, gap=16):
    f = font(size)
    for ln in lines:
        d.text((72, y), ln, font=f, fill=color)
        y += size + gap


def caption(d, text, color=TEXT, y=CAPTION_Y):
    f = font(54)
    lines = wrap(d, text, f, W - 144)
    box_h = len(lines) * (54 + 14) + 44
    d.rounded_rectangle((48, y, W - 48, y + box_h), radius=28, fill=(10, 12, 18))
    d.line((48, y + 20, 48, y + box_h - 20), fill=color, width=8)
    yy = y + 22
    for ln in lines:
        d.text((84, yy), ln, font=f, fill=color)
        yy += 54 + 14


# ---------------- layouts ----------------

def lay_contrast(beats, y=350):
    """上绿下红的对照：编译/理论没问题，实际报错。"""
    img, d = canvas()
    top = beats.get("top", {})
    d.text((72, y), top.get("text", ""), font=font(84), fill=GREEN)
    d.text((72, y + 106), top.get("note", ""), font=font(56), fill=MUTED)
    d.line((72, y + 198, W - 72, y + 198), fill=LINE, width=3)
    lab = beats.get("label", "")
    d.text((72, y + 250), lab, font=font(72), fill=TEXT)
    big = beats.get("big", "")
    lines = big if isinstance(big, list) else [big]
    yy = y + 356
    for ln in lines:
        f2 = fit_size(d, ln, 132, W - 144)
        d.text((72, yy), ln, font=f2, fill=RED)
        yy += 146
    bottom = yy
    if beats.get("note"):
        d.rounded_rectangle((72, yy + 30, 640, yy + 134), radius=18, fill=(52, 22, 24))
        d.text((102, yy + 52), beats["note"], font=font(56), fill=RED)
        bottom = yy + 134
    caption(d, beats.get("caption", ""), color=RED)
    return img, bottom


def lay_points(beats, y=330):
    """大标题 + 三行要点（可带删除线式 ✕）。"""
    img, d = canvas()
    headline(d, beats.get("head", []), y, beats.get("size", 104))
    yy = beats.get("list_y", 620)
    for item in beats.get("points", []):
        if item.get("mark") == "x":
            d.line((76, yy + 18, 112, yy + 54), fill=MUTED, width=7)
            d.line((112, yy + 18, 76, yy + 54), fill=MUTED, width=7)
            d.text((142, yy), item["text"], font=font(60), fill=MUTED)
        yy += 104
    if beats.get("mid"):
        d.line((72, yy + 30, W - 72, yy + 30), fill=LINE, width=3)
        d.text((72, yy + 70), beats["mid"], font=font(72), fill=AMBER)
        yy += 170
    cards = beats.get("cards", [])
    for i, item in enumerate(cards):
        cy = yy + i * 130
        d.rounded_rectangle((72, cy, W - 72, cy + 112), radius=18, fill=BG2)
        d.ellipse((102, cy + 38, 138, cy + 74), fill=item.get("color", CYAN))
        d.text((170, cy + 22), item["text"], font=font(62), fill=TEXT)
    bottom = (yy + len(cards) * 130 - 18) if cards else yy
    caption(d, beats.get("caption", ""), color=beats.get("cap_color", AMBER))
    return img, bottom


def lay_rows(beats, y=330):
    """纵向清单：左色条 + 名称 + 右侧注释。"""
    img, d = canvas()
    headline(d, beats.get("head", []), y, beats.get("size", 96))
    rows = beats.get("rows", [])
    top = beats.get("rows_y", 600)
    step = beats.get("step", 146)
    for i, r in enumerate(rows):
        cy = top + i * step
        d.rounded_rectangle((72, cy, W - 72, cy + 126), radius=18, fill=BG2)
        d.rounded_rectangle((72, cy, 84, cy + 126), radius=6, fill=r.get("color", CYAN))
        d.text((120, cy + 30), r["name"], font=font(68), fill=TEXT)
        if r.get("note"):
            d.text((700, cy + 40), r["note"], font=font(54), fill=MUTED)
    bottom = top + len(rows) * step
    if beats.get("foot"):
        d.text((72, top + len(rows) * step + 20), beats["foot"],
               font=font(50), fill=beats.get("foot_color", RED))
        bottom += 80
    caption(d, beats.get("caption", ""), color=beats.get("cap_color", CYAN))
    return img, bottom


def lay_steps(beats, y=330):
    """编号步骤 + 底部提示块。"""
    img, d = canvas()
    headline(d, beats.get("head", []), y, beats.get("size", 96))
    top = beats.get("steps_y", 610)
    for i, s in enumerate(beats.get("steps", [])):
        cy = top + i * 150
        d.ellipse((72, cy, 146, cy + 74), outline=s.get("color", CYAN), width=4)
        d.text((96, cy + 8), str(i + 1), font=font(48), fill=s.get("color", CYAN))
        f = fit_size(d, s["text"], 62, W - 240, bold=False)
        d.text((186, cy + 4), s["text"], font=f, fill=TEXT)
    bottom = top + len(beats.get("steps", [])) * 150 - 26
    box = beats.get("box")
    if box:
        by = top + len(beats.get("steps", [])) * 150 + 40
        d.rounded_rectangle((72, by, W - 72, by + 210), radius=20, fill=(22, 34, 34))
        d.text((104, by + 32), box["title"], font=font(50), fill=CYAN)
        d.text((104, by + 106), box["note"], font=font(50), fill=MUTED)
        bottom = by + 210
    caption(d, beats.get("caption", ""), color=beats.get("cap_color", CYAN))
    return img, bottom


def lay_cta(beats, y=330):
    """收尾：要点 + 合集入口。"""
    img, d = canvas()
    headline(d, beats.get("head", []), y, beats.get("size", 92))
    for i, t in enumerate(beats.get("bullets", [])):
        f = fit_size(d, "· " + t, 58, W - 144, bold=False)
        d.text((72, 600 + i * 108), "· " + t, font=f, fill=TEXT)
    d.rounded_rectangle((72, 960, W - 72, 1290), radius=24, fill=BG2)
    d.text((104, 1000), beats.get("coll", ""), font=font(62), fill=CYAN)
    d.text((104, 1096), beats.get("coll2", ""), font=font(62), fill=TEXT)
    d.text((104, 1190), beats.get("coll3", ""), font=font(50), fill=MUTED)
    caption(d, beats.get("caption", ""), color=CYAN)
    return img, 1290


LAYOUTS = {"contrast": lay_contrast, "points": lay_points, "rows": lay_rows,
           "steps": lay_steps, "cta": lay_cta}


# ---------------- 内容 ----------------

SHORTS = {
    "01": {
        "badge": "第01章 · 开发环境搭建",
        "beats": [
            {"layout": "contrast", "say": "编译零错误，一下载就报 No target connected。",
             "top": {"text": "Build: 0 Error(s)", "note": "编译全过"},
             "label": "下载：", "big": ["No target", "connected"], "note": "ST-Link 没连上",
             "caption": "编译零错误，下载却报错——问题不在代码"},
            {"layout": "points", "say": "先别急着换芯片。ST-Link 只认三件事：供电、地线，还有两根 SWD。",
             "head": ["九成的人", "先查错方向"], "list_y": 620,
             "points": [{"text": "芯片坏了", "mark": "x"}, {"text": "代码写错了", "mark": "x"}],
             "mid": "ST-Link 只认三件事",
             "cards": [{"text": "供电 3.3V"}, {"text": "地线 GND"}, {"text": "SWD 两根"}],
             "caption": "三样里任何一样不对，都是同一句报错"},
            {"layout": "rows", "say": "SWD 四根：3.3 伏、地、SWDIO、SWCLK。接反或虚接任意一根，直接 No target。",
             "head": ["四根线", "接错一根就不认"],
             "rows": [{"name": "3.3V", "note": "供电", "color": AMBER},
                      {"name": "GND", "note": "地", "color": TEXT},
                      {"name": "SWDIO", "note": "数据", "color": CYAN},
                      {"name": "SWCLK", "note": "时钟", "color": CYAN}],
             "foot": "接反、虚接、共地不良 → 同样的报错",
             "caption": "先量 3.3V 在不在，再量地和地通不通"},
            {"layout": "steps", "say": "排查顺序：先量 3.3 伏，再量地通不通，最后看 CubeMX 的 Debug 有没有选 Serial Wire。",
             "head": ["三步", "排到报错消失"],
             "steps": [{"text": "量 3.3V 有没有"}, {"text": "量 GND 通不通"},
                       {"text": "CubeMX → Debug 选 Serial Wire", "color": CYAN}],
             "box": {"title": "Debug 选错 = SWD 根本没开", "note": "这一步最容易漏"},
             "caption": "按这三步走，No target 基本就没了"},
            {"layout": "cta", "say": "完整流程在第 01 章，合集共 26 集。",
             "head": ["从编译到烧录", "一条流水线讲透"],
             "bullets": ["CubeMX / Keil / PlatformIO 怎么选", "main 之前发生了什么", "排错救砖：灯不闪、连不上"],
             "coll": "合集《STM32零基础自学》", "coll2": "全 26 集 · 主页进入", "coll3": "顺序看，别跳步",
             "caption": "这一章把开发环境从头搭一遍"},
        ],
    },
    "02": {
        "badge": "第02章 · 芯片选型与存储器时钟",
        "beats": [
            {"layout": "contrast", "say": "只把 PLL 乘到 72 兆，程序一跑就死。",
             "top": {"text": "PLL ×9 → 72MHz", "note": "看着很简单"},
             "label": "结果：", "big": "一跑就死", "note": "等待周期没改",
             "caption": "改了 PLL 却没改闪存等待，取错指令"},
            {"layout": "steps", "say": "外部 8 兆进 PLL，乘 9 得到 72 兆；APB1 最高 36 兆，所以要再除以 2。",
             "head": ["72 兆怎么来", "三步算清楚"],
             "steps": [{"text": "HSE 8MHz", "color": AMBER},
                       {"text": "PLL × 9 = 72MHz", "color": AMBER},
                       {"text": "APB1 ÷ 2 = 36MHz", "color": CYAN}],
             "box": {"title": "APB1 最高 36 兆", "note": "串口和 CAN 的波特率都靠它"},
             "caption": "HSE 8 兆 → PLL ×9 → 系统 72 兆"},
            {"layout": "rows", "say": "主频到 72 兆，闪存要加两个等待周期。只改 PLL 不改等待，取错指令就死机。",
             "head": ["72 兆要等两拍", "否则取错指令"],
             "rows": [{"name": "48MHz", "note": "等待 1", "color": CYAN},
                      {"name": "72MHz", "note": "等待 2", "color": AMBER},
                      {"name": "只改 PLL", "note": "一跑就死", "color": RED}],
             "foot": "等待周期写在 Flash latency 里",
             "caption": "主频每上一档，闪存等待必须跟着改"},
            {"layout": "steps", "say": "外设时钟没开，写寄存器像写进虚空，调试器里还显示成功。先开时钟，再摸寄存器。",
             "head": ["时钟没开", "写入像写进虚空"],
             "steps": [{"text": "先开外设时钟（RCC）", "color": AMBER},
                       {"text": "再摸寄存器", "color": CYAN},
                       {"text": "调试器看着像成功，其实没写进去", "color": RED}],
             "box": {"title": "口诀：先开时钟，再摸寄存器", "note": "记住这条，能省一整晚"},
             "caption": "外设不响应，先查它的时钟门控"},
            {"layout": "cta", "say": "完整时钟树在第 02 章，合集共 26 集。",
             "head": ["时钟树讲透", "外设才跑得动"],
             "bullets": ["型号字母怎么看：F103 / C8 / T6", "存储器地图：Flash、SRAM、外设", "APB 分频还会给定时器加倍"],
             "coll": "合集《STM32零基础自学》", "coll2": "全 26 集 · 主页进入", "coll3": "顺序看，别跳步",
             "caption": "这一章把时钟和存储器地图讲清楚"},
        ],
    },
}


# ---------------- 合成 ----------------

async def _speak(text, out):
    import edge_tts
    last = None
    for attempt in range(3):
        try:
            await edge_tts.Communicate(text, VOICE, rate=RATE).save(str(out))
            if out.exists() and out.stat().st_size > 1024:
                return
            last = RuntimeError(f"音频为空（{out.stat().st_size if out.exists() else 0} 字节）")
        except Exception as exc:  # noqa: BLE001
            last = exc
        await asyncio.sleep(2 * (attempt + 1))
    raise RuntimeError(f"配音失败（已重试 3 次）: {last}")


def probe_dur(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "json", str(path)], capture_output=True, text=True, check=True)
    return float(json.loads(out.stdout)["format"]["duration"])


def render(beat, badge_text):
    img, bottom = LAYOUTS[beat["layout"]](beat)
    badge(ImageDraw.Draw(img), badge_text, CYAN)
    return img, bottom


SAFE_BOTTOM = 1390   # 播放器 UI 从约 1620 起遮挡；内容区留 230px 余量
CAPTION_MAX = 1620


def _ink_rows(img):
    """内容区（字幕条以上）最低的非背景像素行。"""
    import numpy as np
    a = np.asarray(img.convert("L").crop((0, 200, W, CAPTION_Y)))
    rows = np.where((a > 120).any(axis=1))[0]
    return int(200 + rows.max()) if rows.size else 0


def _caption_bottom(img):
    """字幕条（含彩色左边条）的最低非背景像素行。"""
    import numpy as np
    a = np.asarray(img.convert("L").crop((0, CAPTION_Y, W, H)))
    rows = np.where((a > 60).any(axis=1))[0]
    return int(CAPTION_Y + rows.max()) if rows.size else 0


def check():
    """不联网预检：渲染每章分镜、估算时长、检查字号是否被压得太小。"""
    EST = 0.20  # 秒/字，由 ch01/ch02 实测 0.190/0.223 取偏紧值；成片时长以 ffprobe 为准
    bad = []
    for ch, spec in sorted(SHORTS.items()):
        total = 0.0
        for i, beat in enumerate(spec["beats"]):
            try:
                img, bottom = render(beat, spec["badge"])
                img.verify()
                if bottom > SAFE_BOTTOM:
                    bad.append(f"ch{ch} s{i} 内容越界：最低内容行 {bottom} > {SAFE_BOTTOM}")
                cap_bottom = _caption_bottom(img)
                if cap_bottom > CAPTION_MAX:
                    bad.append(f"ch{ch} s{i} 字幕越界：{cap_bottom} > {CAPTION_MAX}")
            except Exception as exc:  # noqa: BLE001
                bad.append(f"ch{ch} s{i} 渲染失败: {exc}")
            est = len(beat["say"]) * EST
            total += est
            if est > 16:
                bad.append(f"ch{ch} s{i} 单段 {est:.1f}s 偏长（>{16}s）")
        flag = "OK" if total <= 40 else "TOO-LONG"
        print(f"ch{ch}  beats={len(spec['beats'])}  est={total:.1f}s  {flag}")
        if total > 40:
            bad.append(f"ch{ch} 估算 {total:.1f}s 超过 40s")
    if bad:
        print("\n[问题]")
        for b in bad:
            print(" -", b)
        return 1
    print("\n[通过] 全部分镜可渲染，时长在 40s 内")
    return 0


def outline(chs):
    """打印各章既有讲解要点，供写 SHORTS 时照抄改写，不新增事实。"""
    from importlib import import_module
    mod = import_module("narration")
    want = set(chs) if chs else None
    for chapter in mod.CHAPTERS:
        if want and chapter["id"] not in want:
            continue
        print(f"\n=== ch{chapter['id']}  {chapter['title']}  🔖 {chapter['svg']}")
        for i, seg in enumerate(chapter["segments"]):
            say = seg["say"]
            print(f"  [{i}] {seg['head']}  |  {' / '.join(seg['lines'])}")
            print(f"      {say}  （{len(say)} 字 ≈ {len(say)*0.2:.1f}s）")
        total_chars = sum(len(seg["say"]) for seg in chapter["segments"])
        print(f"  -- 本章 {len(chapter['segments'])} 个 beat、{total_chars} 字（原速约 {total_chars*0.2:.0f}s）")
        print(f"  -- 成片预算：40s ≈ 180 字，即选 4-5 个症状最强的 beat，每条压到 ≤45 字")


def main():
    if "--check" in sys.argv:
        raise SystemExit(check())
    if "--outline" in sys.argv:
        idx = sys.argv.index("--outline")
        outline(sys.argv[idx + 1:])
        raise SystemExit(0)
    ch = sys.argv[1] if len(sys.argv) > 1 else "01"
    spec = SHORTS[ch]
    out = ROOT / "final-videos" / f"ch{ch}" / f"ch{ch}-short.mp4"
    cache = ROOT / ".playwright-mcp" / "shortaudio"
    cache.mkdir(parents=True, exist_ok=True)
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="short-"))
    segs = []
    for i, beat in enumerate(spec["beats"]):
        say = beat["say"]
        mp3 = cache / f"ch{ch}-s{i}.mp3"
        side = cache / f"ch{ch}-s{i}.txt"
        if not mp3.exists() or not side.exists() or side.read_text(encoding="utf-8") != say:
            asyncio.run(_speak(say, mp3))
            side.write_text(say, encoding="utf-8")
        dur = probe_dur(mp3) + 0.18
        png = tmp / f"s{i}.png"
        render(beat, spec["badge"])[0].save(png)
        seg = tmp / f"s{i}.mp4"
        vf = (f"zoompan=z='1+0.00035*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
              f":d={int(dur*30)}:s={W}x{H}:fps=30,format=yuv420p")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", str(png),
                        "-i", str(mp3), "-vf", vf, "-t", f"{dur:.2f}",
                        "-c:v", "libx264", "-crf", "20", "-preset", "veryfast",
                        "-c:a", "aac", "-b:a", "160k", "-ar", "44100",
                        "-af", "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.02,apad=pad_dur=0.18", str(seg)], check=True)
        segs.append(seg)
        print(f"[seg {i}] {beat['layout']} {dur:.1f}s", flush=True)
    lst = tmp / "list.txt"
    lst.write_text("".join(f"file '{s}'\n" for s in segs), encoding="utf-8")
    raw = tmp / "concat.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0",
                    "-i", str(lst), "-c", "copy", str(raw)], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-c:v", "copy",
                    "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac",
                    "-b:a", "192k", "-ar", "44100", str(out)], check=True)
    import hashlib
    man_path = ROOT / "final-videos" / "shorts.json"
    man = json.loads(man_path.read_text(encoding="utf-8")) if man_path.exists() else {}
    man[f"ch{ch}"] = {
        "file": str(out.relative_to(ROOT)).replace("\\", "/"),
        "seconds": round(probe_dur(out), 2),
        "bytes": out.stat().st_size,
        "sha256": hashlib.sha256(out.read_bytes()).hexdigest()[:16],
        "beats": len(spec["beats"]),
        "rendered_at": subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"],
                                      capture_output=True, text=True).stdout.strip(),
    }
    man_path.write_text(json.dumps(man, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("[done]", out, round(probe_dur(out), 1), "s", out.stat().st_size // 1024, "KB", flush=True)


if __name__ == "__main__":
    main()

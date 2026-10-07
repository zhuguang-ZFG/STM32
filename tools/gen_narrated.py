#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_narrated.py —— 把每章讲解做成带中文配音和字幕的 MP4。

画面：Pillow 绘制的标题卡 / 步骤卡，并贴上本仓库自己的 SVG（动画或引脚图的一帧）。
不是实拍，不含版权素材。字体是系统里的文泉驿微米黑（GPL-3，带字体嵌入例外）。

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
import io
import os
import shutil
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from narration import CHAPTERS  # noqa: E402

W, H = 960, 540
BAND_TOP = 448
PAD = 0.35
VOICE = "zh-CN-XiaoxiaoNeural"
RATE = "-6%"
FONT = "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"

# 校准自本机 edge-tts 7.2.8、rate=-8% 的一次短句（51 字 / 13.27 秒）。
# --check 只用它估算，成片时长以 ffprobe 为准。
EST_SEC_PER_CHAR = 13.27 / 51

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
    "重新生成需要联网。画面用文泉驿微米黑绘制，插图是本仓库 SVG，不是实拍。"
)


def _font(size):
    from PIL import ImageFont
    return ImageFont.truetype(FONT, size, index=0)


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


def render_card(ch, seg, index):
    """画一帧。字幕画在底部深色带里，正文停在带子上方。"""
    from PIL import Image, ImageDraw

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
    draw.text((32, 62), head_lines[0], font=head_font, fill=AMBER)

    y = 112
    if seg.get("svg"):
        shot = _svg_png(seg["svg"])
        box = (32, 108, W - 32, BAND_TOP - 36)
        pasted = _fit(shot, box[2] - box[0], box[3] - box[1])
        px = box[0] + (box[2] - box[0] - pasted.width) // 2
        py = box[1] + (box[3] - box[1] - pasted.height) // 2
        img.paste(pasted, (px, py))
        y = BAND_TOP - 8
    else:
        body_font = _font(26)
        for line in seg["lines"]:
            wrapped = wrap_text(line, body_font, W - 80, 1, f"{ch['id']} 要点")
            if y + 34 > BAND_TOP - 16:
                raise ValueError(f"{ch['id']} 要点叠进字幕带：{line}")
            draw.text((40, y), wrapped[0], font=body_font, fill=TEXT)
            y += 40

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
    # 深色底，避免白边被当成「照片」。SVG 用仓库原文件。
    page = (
        "<!doctype html><meta charset=utf-8><style>"
        "html,body{margin:0;background:#171a24;width:880px;height:300px;overflow:hidden}"
        "img{width:880px;height:300px;object-fit:contain}"
        f"</style><img src='file://{svg}'>"
    )
    open(html, "w", encoding="utf-8").write(page)
    ud = os.path.join(tmp, "chrome")
    cmd = [
        "google-chrome", "--headless=new", "--disable-gpu", "--no-sandbox",
        "--hide-scrollbars", "--no-first-run", "--disable-extensions",
        "--force-device-scale-factor=1",
        "--allow-file-access-from-files",
        f"--user-data-dir={ud}",
        "--virtual-time-budget=8000",
        "--window-size=880,300",
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
            flag = "ok" if 120 <= est <= 240 else "SHORT" if est < 120 else "LONG"
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


def _segment_mp4(png, mp3, dest, dur):
    subprocess.check_call(
        [
            "ffmpeg", "-y", "-loglevel", "error",
            "-loop", "1", "-framerate", "8", "-i", png,
            "-i", mp3,
            "-filter_complex", f"[1:a]apad=pad_dur={PAD}[a]",
            "-map", "0:v", "-map", "[a]",
            "-t", f"{dur:.3f}",
            "-c:v", "libx264", "-preset", "veryfast", "-tune", "stillimage",
            "-crf", "32", "-pix_fmt", "yuv420p", "-r", "8",
            "-c:a", "aac", "-b:a", "40k", "-ac", "1", "-ar", "44100",
            dest,
        ],
        stdout=subprocess.DEVNULL,
    )


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

    cues = []
    cursor = 0.0
    segs = []
    for i, seg in enumerate(ch["segments"]):
        audio = _probe_duration(mp3s[i])
        dur = audio + PAD
        png = os.path.join(work, f"{i:02d}.png")
        card = render_card(ch, seg, i + 1)
        card.save(png, "PNG")
        mp4 = os.path.join(work, f"{i:02d}.mp4")
        _segment_mp4(png, mp3s[i], mp4, dur)
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
    flag = "ok" if 120 <= got <= 240 else "RANGE"
    print(f"[{flag}] {name}.mp4  {got:.1f}s  {size / 1048576:.2f} MB  "
          f"字幕 {len(cues)} 条")
    shutil.rmtree(work, ignore_errors=True)
    if not 120 <= got <= 240:
        raise SystemExit(f"{name} 时长 {got:.1f}s 不在 2–4 分钟")
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
            f"字幕：<a href=\"{prefix}/{name}.srt\">SRT</a>。"
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
        f"Subtitles: <a href=\"{prefix}/{name}.srt\">SRT</a>. "
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
    out_dir = os.path.join(root, "assets", "video")
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

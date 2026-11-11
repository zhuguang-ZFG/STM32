"""旁白合成 + 时间轴生成（视频产线的音频阶段）。

顺序是"先有声音、再定画面时长"：逐句 edge-tts → ffmpeg 量出真实时长 →
向上取整到整帧得到场景时长 → 每句补静音对齐到该时长 → 拼接成整条 narration.wav。
音画对位因此是构造出来的，不靠事后对齐。

字幕不走 ffmpeg subtitles / edge-tts SubMaker：前者要 fontconfig 配置才认得出中文，
后者给的是整句边界、句子太长不适合当花字。这里按标点切句、按字数把已实测到的
音频时长比例分配，同时产 .srt（给剪映）和 captions 数组（给 HTML 阶段逐帧烧字）。
"""

import asyncio
import json
import math
import os
import random
import re
import shutil
import subprocess
import sys

import edge_tts

# Windows 控制台默认 GBK，日志里的 emoji 会直接把进程打崩（UnicodeEncodeError）。
# 产线靠退出码判断成败，所以这里强制 UTF-8，编码不了的字符替换掉而不是抛异常。
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

MAX_ATTEMPTS = 5
CONCURRENCY = 3
# edge-tts 偶发"握手成功但流被截断"：文件几千字节、能解码，时长却只有零点几秒。
# 光看体积挡不住（2160 B 的残包照样 >200），所以用实测时长反推语速来判：
# 正常中文旁白 5–7 字/秒，超过 MAX_SPEED 或短于 MIN_SPEECH 一律当坏包重合成。
MAX_SPEED = 9.5
MIN_SPEECH = 0.5
# 断句点：中文逗号/句号/顿号/冒号/换行都算，切完再合并过碎的片段
BREAKS = "，。；！？、：,\n"
MAX_CAPTION_CHARS = 20


def sha1_of(text):
    import hashlib

    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def log(msg):
    print(msg, flush=True)


def probe_duration(ffmpeg, path):
    """ffmpeg 解码到 null，读最后一行 time=（流式 mp3 没有可信的容器头时长）。"""
    proc = subprocess.run(
        [ffmpeg, "-hide_banner", "-i", path, "-map", "a:0", "-f", "null", "-"],
        capture_output=True,
        text=True,
        errors="replace",
    )
    stamps = re.findall(r"time=(\d+):(\d+):([\d.]+)", proc.stderr or "")
    if not stamps:
        stamps = re.findall(r"Duration:\s*(\d+):(\d+):([\d.]+)", proc.stderr or "")
    if not stamps:
        raise RuntimeError(f"量不到时长: {path}\n{(proc.stderr or '')[-400:]}")
    h, m, s = stamps[-1]
    return int(h) * 3600 + int(m) * 60 + float(s)


def split_captions(text):
    parts = [p.strip() for p in re.split(f"(?<=[{BREAKS}])", text) if p.strip()]
    merged = []
    for part in parts:
        # 过短的（"对。"这种）并进上一句，免得屏幕上一闪而过一个词
        if merged and (len(part) < 5 or len(merged[-1]) < 5):
            merged[-1] += part
        else:
            merged.append(part)
    out = []
    for part in merged:
        while len(part) > MAX_CAPTION_CHARS:
            cut = part.rfind(" ", 0, MAX_CAPTION_CHARS)
            cut = cut if cut > MAX_CAPTION_CHARS // 2 else MAX_CAPTION_CHARS
            out.append(part[:cut].strip())
            part = part[cut:].strip()
        if part:
            out.append(part)
    return out


def srt_time(sec):
    ms = int(round(sec * 1000))
    return f"{ms // 3600000:02d}:{ms % 3600000 // 60000:02d}:{ms % 60000 // 1000:02d},{ms % 1000:03d}"


def spoken_text(sc):
    """送进 TTS 的文本（发音表展开后的 ttsText）；字幕仍用 sc["narration"] 原文。"""
    return (sc.get("ttsText") or sc["narration"]).strip()


def plausible(text, dur):
    return dur >= MIN_SPEECH and len(text) / max(dur, 1e-6) <= MAX_SPEED


async def synth(text, out_path, voice, rate, ffmpeg):
    last = None
    for attempt in range(MAX_ATTEMPTS):
        try:
            # 不传自定义 connector：edge-tts 自带 pinned SSL context，
            # 外部 connector 会让 TLS 上下文冲突（实测每次 5 连败）。
            await edge_tts.Communicate(text, voice, rate=rate).save(out_path)
            if not (os.path.exists(out_path) and os.path.getsize(out_path) > 200):
                raise RuntimeError("合成结果为空或过小")
            dur = probe_duration(ffmpeg, out_path)
            if not plausible(text, dur):
                raise RuntimeError(f"音频疑似截断：{len(text)} 字只量到 {dur:.2f}s（{len(text) / max(dur, 1e-6):.1f} 字/秒）")
            return
        except Exception as err:  # noqa: BLE001 - 403/断流/超时都是瞬时故障，退避后重试
            last = err
            log(f"  ↻ 第 {attempt + 1} 次失败：{type(err).__name__}: {err}")
            if os.path.exists(out_path):
                os.remove(out_path)
            if attempt == MAX_ATTEMPTS - 1:
                break
            await asyncio.sleep(min(16, 2**attempt) + random.random())
    raise RuntimeError(f"edge-tts 连续 {MAX_ATTEMPTS} 次失败: {last}")


async def synth_all(jobs, voice, rate, ffmpeg):
    sem = asyncio.Semaphore(CONCURRENCY)

    async def one(scene, path):
        async with sem:
            if os.path.exists(path) and os.path.getsize(path) > 200:
                return scene["id"], "cache"
            await synth(spoken_text(scene), path, voice, rate, ffmpeg)
            return scene["id"], "tts"

    results = await asyncio.gather(*(one(s, p) for s, p in jobs))
    return dict(results)


def main():
    manifest = json.load(open(sys.argv[1], encoding="utf-8"))
    ffmpeg = manifest["ffmpeg"]
    out_dir = manifest["outDir"]
    cache_dir = manifest["cacheDir"]
    fps = manifest["fps"]
    sr = manifest["sampleRate"]
    ch = manifest["channels"]
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(cache_dir, exist_ok=True)
    clips_dir = os.path.join(out_dir, "clips")
    shutil.rmtree(clips_dir, ignore_errors=True)
    os.makedirs(clips_dir, exist_ok=True)

    scenes = manifest["scenes"]
    for sc in scenes:
        if not sc["narration"].strip() or not spoken_text(sc):
            raise RuntimeError(f"场景 {sc['id']} 旁白或 ttsText 为空")

    paths = [
        os.path.join(cache_dir, sha1_of(f"{manifest['voice']}|{manifest['rate']}|{spoken_text(sc)}") + ".mp3")
        for sc in scenes
    ]
    todo = [p for p in paths if not (os.path.exists(p) and os.path.getsize(p) > 200)]
    log(f"🎙️  旁白 {len(scenes)} 句，其中 {len(todo)} 句需要新合成")

    async def _run(jobs=None):
        return await synth_all(jobs or list(zip(scenes, paths)), manifest["voice"], manifest["rate"], ffmpeg)

    sources = asyncio.run(_run())
    log(f"  新合成 {sum(1 for v in sources.values() if v == 'tts')} 句，命中缓存 {len(scenes) - sum(1 for v in sources.values() if v == 'tts')} 句")

    log("⏱️  量取每句真实时长…")
    durations = [probe_duration(ffmpeg, p) for p in paths]

    # 缓存里可能躺着上一轮留下的残包（体积正常、时长只有零点几秒），必须重合成再入轴。
    suspect = [i for i, sc in enumerate(scenes) if not plausible(spoken_text(sc), durations[i])]
    if suspect:
        log(f"  ⚠️  {len(suspect)} 句语速不合理（残包/静音），删缓存重合成：{[scenes[i]['id'] for i in suspect]}")
        for i in suspect:
            if os.path.exists(paths[i]):
                os.remove(paths[i])
        asyncio.run(_run([(scenes[i], paths[i]) for i in suspect]))
        for i in suspect:
            durations[i] = probe_duration(ffmpeg, paths[i])
            if not plausible(spoken_text(scenes[i]), durations[i]):
                raise RuntimeError(f"场景 {scenes[i]['id']} 重合成后仍不合理：{durations[i]:.2f}s / {len(spoken_text(scenes[i]))} 字")

    timeline_scenes = []
    cursor = 0.0
    captions = []
    log("🔗 生成每场景等长音频…")
    for i, sc in enumerate(scenes):
        head = float(sc.get("head", 0.25))
        tail = float(sc.get("tail", 0.45))
        min_sec = float(sc.get("minSec", 1.6))
        speech = durations[i]
        frames = math.ceil(max(min_sec, speech + head + tail) * fps)
        scene_dur = frames / fps
        if speech + head > scene_dur + 1e-6:
            raise RuntimeError(f"场景 {sc['id']} 音频放不下：{speech}+{head} > {scene_dur}")

        clip = os.path.join(clips_dir, f"{i:03d}-{sc['id']}.wav")
        af = []
        if head > 0:
            af.append(f"adelay={int(round(head * 1000))}:all=1")
        af.append("apad")
        subprocess.run(
            [
                ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
                "-i", paths[i], "-af", ",".join(af), "-t", f"{scene_dur:.6f}",
                "-ar", str(sr), "-ac", str(ch), "-c:a", "pcm_s16le", clip,
            ],
            check=True,
        )

        start = cursor + head
        text_spans = split_captions(sc["narration"])
        weight = [max(1, len(t)) for t in text_spans]
        total_w = sum(weight)
        t = start
        for k, seg in enumerate(text_spans):
            span = speech * weight[k] / total_w
            end = start + speech if k == len(text_spans) - 1 else t + span
            captions.append({"scene": sc["id"], "text": seg, "start": round(t, 3), "end": round(end, 3)})
            t = end

        timeline_scenes.append(
            {
                "id": sc["id"],
                "frames": frames,
                "start": round(cursor, 6),
                "duration": round(scene_dur, 6),
                "speech": round(speech, 3),
                "clip": clip,
            }
        )
        cursor += scene_dur
        log(f"  ✓ {sc['id']:<22} {speech:6.2f}s 语音 → {scene_dur:6.2f}s 画面 ({frames} 帧)")

    concat_list = os.path.join(out_dir, "concat.txt")
    with open(concat_list, "w", encoding="utf-8") as fh:
        for ts in timeline_scenes:
            fh.write("file '{}'\n".format(os.path.abspath(ts["clip"]).replace("\\", "/")))
    narration = os.path.join(out_dir, "narration.wav")
    subprocess.run(
        [ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", concat_list,
         "-c:a", "pcm_s16le", "-ar", str(sr), "-ac", str(ch), narration],
        check=True,
    )
    total_frames = sum(ts["frames"] for ts in timeline_scenes)
    audio_dur = probe_duration(ffmpeg, narration)
    drift = abs(audio_dur - total_frames / fps)
    if drift > 1.5 / fps:
        raise RuntimeError(f"整条旁白 {audio_dur:.3f}s 与 {total_frames} 帧（{total_frames / fps:.3f}s）偏差 {drift:.3f}s")

    srt_path = os.path.join(out_dir, "narration.srt")
    with open(srt_path, "w", encoding="utf-8") as fh:
        for i, cap in enumerate(captions, 1):
            fh.write(f"{i}\n{srt_time(cap['start'])} --> {srt_time(cap['end'])}\n{cap['text']}\n\n")

    result = {
        "platform": manifest["platform"],
        "fps": fps,
        "sampleRate": sr,
        "channels": ch,
        "totalFrames": total_frames,
        "duration": round(total_frames / fps, 6),
        "audioDuration": round(audio_dur, 6),
        "scenes": timeline_scenes,
        "captions": captions,
        "newSynth": sum(1 for v in sources.values() if v == "tts"),
    }
    with open(os.path.join(out_dir, "timeline.json"), "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=1)

    log(f"✅ narration.wav {audio_dur:.2f}s / {total_frames} 帧 / 字幕 {len(captions)} 条 → {narration}")


if __name__ == "__main__":
    main()

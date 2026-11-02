#!/usr/bin/env python3
"""Render a validated chapter storyboard into a reproducible long lesson.

Usage:
  python tools/gen_long_lesson.py --check 03
  python tools/gen_long_lesson.py --posters 03
  python tools/gen_long_lesson.py --speak 03
  python tools/gen_long_lesson.py --report 03

TTS requires edge-tts and network access. Rendering requires Pillow, Playwright,
Chromium and ffmpeg. Large MP4s stay in final-videos/; the storyboard, subtitles,
actual-frame contact sheet and media report remain reviewable in video/chNN/.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

os.environ.setdefault("NARRATED_SCALE", "2")
os.environ.setdefault("NARRATED_SUBTITLE_LINES", "4")
os.environ.setdefault("NARRATED_BAND_HEIGHT", "150")

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

import gen_narrated as narrated  # noqa: E402
import storyboards  # noqa: E402


FPS = 30
CRF = os.environ.get("LESSON_CRF", "23")
ROLE_TITLES = {
    "hook": "问题开场",
    "mechanism": "核心机制",
    "failure": "失败排查",
    "experiment": "动手实验",
    "recall": "回忆检查",
}


def load(chapter: str):
    board = storyboards.load(chapter)
    return board, storyboards.as_narrated_chapter(board)


def check_layout(chapter: str) -> bool:
    board, rendered = load(chapter)
    for index, scene in enumerate(rendered["segments"], 1):
        narrated.render_card(rendered, scene, index)
    print(
        f"[ok] ch{board['id']}-long  {len(board['segments'])} 场景  "
        f"估算 {board['estimated_duration']:.1f}s  1080p/{FPS}fps"
    )
    return True


def render_posters(chapter: str) -> None:
    board, rendered = load(chapter)
    out = ROOT / ".temp" / f"long-ch{board['id']}-posters"
    out.mkdir(parents=True, exist_ok=True)
    for index, scene in enumerate(rendered["segments"], 1):
        narrated.render_card(rendered, scene, index).save(out / f"{index:02d}.png")
    print(f"[ok] {len(board['segments'])} posters -> {out}")


def _chapter_markers(scenes: list[dict]) -> str:
    lines = []
    previous = None
    for scene in scenes:
        role = scene["purpose"]
        if role != previous:
            seconds = int(scene["start"])
            lines.append(f"{seconds // 60:02d}:{seconds % 60:02d} {ROLE_TITLES[role]}")
            previous = role
    return "\n".join(lines) + "\n"


def _scene_mp4(work: str, index: int, frames: list[str], mp3: str, dest: str, duration: float) -> None:
    durations = storyboards.keyframe_durations(duration)
    command = ["ffmpeg", "-y", "-loglevel", "error"]
    for frame in frames:
        command += ["-loop", "1", "-framerate", str(FPS), "-i", frame]
    command += ["-i", mp3]
    filters = []
    labels = []
    for frame_index, part in enumerate(durations):
        filters.append(
            f"[{frame_index}:v]trim=duration={part:.6f},setpts=PTS-STARTPTS,fps={FPS}[v{frame_index}]"
        )
        labels.append(f"[v{frame_index}]")
    filters.append("".join(labels) + f"concat=n={len(frames)}:v=1:a=0[v]")
    filters.append(f"[{len(frames)}:a]apad=pad_dur={narrated.PAD}[a]")
    command += [
        "-filter_complex", ";".join(filters),
        "-map", "[v]", "-map", "[a]", "-t", f"{duration:.3f}",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", CRF,
        "-pix_fmt", "yuv420p", "-r", str(FPS),
        "-c:a", "aac", "-b:a", "64k", "-ac", "1", "-ar", "44100",
        dest,
    ]
    subprocess.check_call(command, stdout=subprocess.DEVNULL)


def _louden(joined: str, final: str) -> None:
    subprocess.check_call([
        "ffmpeg", "-y", "-loglevel", "error", "-i", joined,
        "-c:v", "copy", "-af", "loudnorm=I=-16:TP=-1:LRA=11,alimiter=limit=0.75:level=false",
        "-c:a", "aac", "-b:a", "64k", "-ac", "1", "-ar", "44100",
        "-movflags", "+faststart", final,
    ], stdout=subprocess.DEVNULL)


async def speak(chapter: str) -> None:
    board, rendered = load(chapter)
    chapter_dir = ROOT / "final-videos" / f"ch{board['id']}"
    source_dir = ROOT / "video" / f"ch{board['id']}"
    chapter_dir.mkdir(parents=True, exist_ok=True)
    source_dir.mkdir(parents=True, exist_ok=True)

    for scene in rendered["segments"]:
        if scene.get("svg"):
            await asyncio.to_thread(narrated._visual_png, scene["svg"])

    with tempfile.TemporaryDirectory(prefix=f"lesson-ch{board['id']}-") as work:
        sem = asyncio.Semaphore(4)
        audio = []
        jobs = []
        for index, scene in enumerate(rendered["segments"]):
            dest = os.path.join(work, f"{index:02d}.mp3")
            audio.append(dest)
            jobs.append(narrated._tts(scene["say"], dest, sem))
        await asyncio.gather(*jobs)
        durations = [narrated._probe_duration(path) + narrated.PAD for path in audio]

        cursor = 0.0
        cues = []
        encoded = []
        actual_scenes = []
        for index, (scene, mp3, duration) in enumerate(
            zip(rendered["segments"], audio, durations), 1
        ):
            frames = []
            last_line = max(0, len(scene.get("lines", [])) - 1)
            for keyframe, (progress, line) in enumerate(((0.70, 0), (1.0, min(1, last_line)), (1.0, last_line))):
                frame = os.path.join(work, f"{index:02d}-{keyframe}.png")
                narrated.render_card(
                    rendered, scene, index, t=progress, line=line,
                    u=keyframe / 2, gprog=(cursor + duration * keyframe / 2) / sum(durations),
                ).save(frame)
                frames.append(frame)
            segment = os.path.join(work, f"{index:02d}.mp4")
            _scene_mp4(work, index, frames, mp3, segment, duration)
            encoded.append(segment)
            cues.append({"start": cursor, "end": cursor + duration, "say": scene["say"]})
            actual = dict(scene)
            actual.update({
                "start": round(cursor, 3),
                "duration": round(duration, 3),
                "subtitle_ref": f"ch{board['id']}.srt#{index:02d}",
            })
            actual_scenes.append(actual)
            cursor += duration

        joined = os.path.join(work, "joined.mp4")
        narrated._concat(encoded, joined)
        final = str(chapter_dir / f"ch{board['id']}-bilibili-safe.mp4")
        _louden(joined, final)

        srt = narrated._srt(cues)
        (source_dir / f"ch{board['id']}.srt").write_text(srt, encoding="utf-8")
        (chapter_dir / f"ch{board['id']}.srt").write_text(srt, encoding="utf-8")
        (chapter_dir / f"ch{board['id']}-chapters.txt").write_text(
            _chapter_markers(actual_scenes), encoding="utf-8"
        )
        rendered_board = {**board, "segments": actual_scenes, "actual_duration": round(cursor, 3)}
        (source_dir / "storyboard-rendered.json").write_text(
            json.dumps(rendered_board, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"[ok] ch{board['id']}-bilibili-safe.mp4  {cursor:.1f}s  {len(cues)} 字幕")
        contact_sheet(board["id"])
        if not media_report(board["id"]):
            raise SystemExit("media report failed")


def _read_rendered(chapter: str) -> dict:
    path = ROOT / "video" / f"ch{chapter.zfill(2)}" / "storyboard-rendered.json"
    return json.loads(path.read_text(encoding="utf-8"))


def contact_sheet(chapter: str) -> None:
    chapter = chapter.zfill(2)
    board = _read_rendered(chapter)
    scenes = board["segments"]
    selected = [0, 1, next(i for i, s in enumerate(scenes) if s["purpose"] == "failure"),
                next(i for i, s in enumerate(scenes) if s["purpose"] == "experiment"),
                next(i for i, s in enumerate(scenes) if s["purpose"] == "recall")]
    from PIL import Image, ImageDraw

    source_dir = ROOT / "video" / f"ch{chapter}"
    mp4 = ROOT / "final-videos" / f"ch{chapter}" / f"ch{chapter}-bilibili-safe.mp4"
    tiles = []
    with tempfile.TemporaryDirectory(prefix=f"lesson-contact-{chapter}-") as tmp:
        for index in selected:
            scene = scenes[index]
            at = scene["start"] + scene["duration"] / 2
            path = os.path.join(tmp, f"{index:02d}.jpg")
            subprocess.check_call([
                "ffmpeg", "-y", "-loglevel", "error", "-ss", f"{at:.3f}",
                "-i", str(mp4), "-frames:v", "1", "-vf", "scale=640:360", path,
            ])
            tiles.append((Image.open(path).convert("RGB"), scene["title"]))
        canvas = Image.new("RGB", (1920, 800), (23, 26, 36))
        draw = ImageDraw.Draw(canvas)
        title_font = narrated._font(14)
        for position, (image, title) in enumerate(tiles):
            x, y = (position % 3) * 640, (position // 3) * 400
            canvas.paste(image, (x, y))
            draw.text((x + 12, y + 366), title, font=title_font, fill=(236, 239, 244))
        canvas.save(source_dir / "contact-sheet.jpg", quality=90)
    print(f"[ok] contact-sheet.jpg  {len(tiles)} actual MP4 frames")


def media_report(chapter: str) -> bool:
    chapter = chapter.zfill(2)
    board = _read_rendered(chapter)
    source_dir = ROOT / "video" / f"ch{chapter}"
    mp4 = ROOT / "final-videos" / f"ch{chapter}" / f"ch{chapter}-bilibili-safe.mp4"
    probe = json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(mp4)
    ], text=True))
    video = next(stream for stream in probe["streams"] if stream["codec_type"] == "video")
    loud = subprocess.run([
        "ffmpeg", "-hide_banner", "-i", str(mp4), "-filter_complex", "ebur128=peak=true",
        "-f", "null", "-",
    ], capture_output=True, text=True)
    integrated = re.findall(r"I:\s*(-?\d+(?:\.\d+)?) LUFS", loud.stderr)
    peaks = re.findall(r"Peak:\s*(-?\d+(?:\.\d+)?) dBFS", loud.stderr)
    duration = float(probe["format"]["duration"])
    scenes = board["segments"]
    checks = {
        "28_scenes": len(scenes) == 28,
        "five_learning_roles": {s["purpose"] for s in scenes} == storyboards.ROLES,
        "1080p": (video["width"], video["height"]) == (1920, 1080),
        "30_fps": video["r_frame_rate"] == "30/1",
        "subtitle_count": len(scenes) == 28,
        "duration_matches_storyboard": abs(duration - scenes[-1]["start"] - scenes[-1]["duration"]) < 1.0,
        "integrated_loudness": bool(integrated) and -17.0 <= float(integrated[-1]) <= -15.0,
        "true_peak": bool(peaks) and float(peaks[-1]) <= -0.9,
        "contact_sheet": (source_dir / "contact-sheet.jpg").is_file(),
    }
    report = {
        "schema_version": 1,
        "chapter": chapter,
        "mp4": str(mp4.relative_to(ROOT)).replace("\\", "/"),
        "mp4_sha256": hashlib.sha256(mp4.read_bytes()).hexdigest(),
        "storyboard_sha256": hashlib.sha256((source_dir / "storyboard.json").read_bytes()).hexdigest(),
        "duration_seconds": duration,
        "width": video["width"],
        "height": video["height"],
        "frame_rate": video["r_frame_rate"],
        "integrated_lufs": float(integrated[-1]) if integrated else None,
        "true_peak_dbtp": float(peaks[-1]) if peaks else None,
        "subtitle_cues": len(scenes),
        "checks": checks,
    }
    (source_dir / "media-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    ok = all(checks.values())
    print(f"[{'ok' if ok else 'FAIL'}] media-report.json  {checks}")
    return ok


def main(argv: list[str]) -> int:
    chapter = next((arg.zfill(2) for arg in argv if arg.isdigit()), "03")
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise SystemExit("需要 ffmpeg 和 ffprobe")
    if "--speak" in argv:
        asyncio.run(speak(chapter))
        return 0
    if "--posters" in argv:
        render_posters(chapter)
        return 0
    if "--contact-sheet" in argv:
        contact_sheet(chapter)
        return 0
    if "--report" in argv:
        return 0 if media_report(chapter) else 1
    return 0 if check_layout(chapter) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

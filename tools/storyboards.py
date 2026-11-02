"""Load and validate machine-readable long-lesson storyboards."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EST_SEC_PER_CHAR = 13.27 / 51
PAD = 0.35
ROLES = {"hook", "mechanism", "failure", "experiment", "recall"}
MIN_ESTIMATED_DURATION = 480.0
MAX_ESTIMATED_DURATION = 1080.0
SOURCE_FIELDS = {
    "scene_id", "title", "purpose", "prerequisite", "narration", "on_screen",
    "visual_source", "fact_source", "memory_anchor", "evidence_type",
}


def keyframe_durations(duration: float) -> tuple[float, float, float]:
    """Split a scene into reveal, develop and settle thirds without losing time."""
    if duration <= 0:
        raise ValueError("scene duration must be positive")
    first = duration * 0.20
    second = duration * 0.30
    return first, second, duration - first - second


def load(chapter: str) -> dict:
    chapter = chapter.zfill(2)
    path = ROOT / "video" / f"ch{chapter}" / "storyboard.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    scenes = data.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        raise ValueError(f"{path}: scenes must be a non-empty list")

    cursor = 0.0
    enriched = []
    seen = set()
    for index, source in enumerate(scenes, 1):
        missing = SOURCE_FIELDS - source.keys()
        if missing:
            raise ValueError(f"{path}: scene {index} missing {sorted(missing)}")
        if source["scene_id"] != f"ch{chapter}-s{index:02d}" or source["scene_id"] in seen:
            raise ValueError(f"{path}: invalid or duplicate scene_id {source['scene_id']}")
        if any(parent not in seen for parent in source["prerequisite"]):
            raise ValueError(f"{path}: scene {index} has an unknown or forward prerequisite")
        if source["visual_source"] and not (ROOT / "assets" / source["visual_source"]).is_file():
            raise FileNotFoundError(f"{path}: missing visual_source {source['visual_source']}")
        seen.add(source["scene_id"])
        if source["purpose"] not in ROLES:
            raise ValueError(f"{path}: scene {index} has invalid purpose")
        if not source["narration"].strip() or not source["on_screen"]:
            raise ValueError(f"{path}: scene {index} needs narration and on_screen")
        if not source["fact_source"]:
            raise ValueError(f"{path}: scene {index} needs a fact source")
        scene = dict(source)
        duration = round(max(4.0, len(scene["narration"]) * EST_SEC_PER_CHAR + PAD), 3)
        scene.update({
            "start": round(cursor, 3),
            "duration": duration,
            "subtitle_ref": f"ch{chapter}.srt#{index:02d}",
        })
        enriched.append(scene)
        cursor = round(cursor + duration, 3)
    if not MIN_ESTIMATED_DURATION <= cursor <= MAX_ESTIMATED_DURATION:
        raise ValueError(f"{path}: estimated duration {cursor}s outside SPECS 8-18 min")
    return {
        "id": chapter,
        "slug": data["slug"],
        "title": data["title"],
        "short_source": data["short_source"],
        "segments": enriched,
        "estimated_duration": cursor,
    }


def as_narrated_chapter(board: dict) -> dict:
    """Adapt validated scenes to the existing narrated-card renderer."""
    segments = []
    for scene in board["segments"]:
        segments.append({
            **scene,
            "head": scene["title"],
            "lines": scene["on_screen"],
            "say": scene["narration"],
            "svg": scene["visual_source"] or False,
        })
    return {
        "id": board["id"],
        "slug": board["slug"],
        "title": board["title"],
        "segments": segments,
    }


def main(argv: list[str]) -> int:
    if "--check" in argv:
        chapters = [arg.zfill(2) for arg in argv if arg.isdigit()]
        if not chapters:
            print("usage: python tools/storyboards.py --check NN [NN ...]", file=sys.stderr)
            return 2
        for chapter in chapters:
            board = load(chapter)
            print(
                f"[ok] ch{board['id']}-long  {len(board['segments'])} scenes  "
                f"estimated {board['estimated_duration']:.1f}s"
            )
        return 0
    print("usage: python tools/storyboards.py --check NN [NN ...]", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""shorts_loudness —— 29 条短片逐条响度审计（ffmpeg ebur128）。

用法：
    python tools/shorts_loudness.py --report stm32-book/audits/shorts-loudness.json

对 assets/video/chNN-*.mp4 逐条跑 ffmpeg 的 ebur128 滤镜（EBU R128 扫描），
解析 integrated loudness（I）与 true peak，输出机器可读 JSON。
只出报告不做硬阈值判定；长课的响度合同（media-report）已另行覆盖。
依赖：ffmpeg 在 PATH。
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VIDEO = ROOT / "assets" / "video"


def measure(mp4: Path) -> dict:
    got = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats",
         "-i", str(mp4), "-filter_complex", "ebur128", "-f", "null", "-"],
        capture_output=True, timeout=600,
    )
    text = (got.stderr or b"").decode("utf-8", "replace")
    integrated = re.search(r"I:\s*(-?[\d.]+)\s*LUFS", text)
    peak = re.search(r"Peak:\s*(-?[\d.]+)\s*dBFS", text)
    lra = re.search(r"LRA:\s*(-?[\d.]+)\s*LU", text)
    dur = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", text)
    seconds = None
    if dur:
        seconds = round(int(dur.group(1)) * 3600 + int(dur.group(2)) * 60
                        + float(dur.group(3)), 2)
    return {
        "integrated_lufs": float(integrated.group(1)) if integrated else None,
        "true_peak_dbfs": float(peak.group(1)) if peak else None,
        "lra_lu": float(lra.group(1)) if lra else None,
        "duration_s": seconds,
    }


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", required=True)
    args = ap.parse_args()

    mp4s = sorted(VIDEO.glob("ch[0-9][0-9]-*.mp4"))
    chapters = []
    for mp4 in mp4s:
        m = measure(mp4)
        m["file"] = mp4.name
        m["chapter"] = mp4.name.split("-")[0]
        chapters.append(m)
        print(f"[ok] {mp4.name}  I={m['integrated_lufs']} LUFS  "
              f"Peak={m['true_peak_dbfs']} dBFS  {m['duration_s']}s", flush=True)

    ok = all(c["integrated_lufs"] is not None for c in chapters)
    report = {
        "schema_version": 1,
        "generated": datetime.datetime.now().isoformat(timespec="seconds"),
        "tool": "ffmpeg ebur128 (EBU R128)",
        "count": len(chapters),
        "all_measured": ok,
        "chapters": chapters,
    }
    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    Path(args.report).write_text(
        json.dumps(report, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8", newline="\n",
    )
    print(f"[done] {len(chapters)} chapters -> {args.report}")
    return 0 if ok else 1


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv[1:]))

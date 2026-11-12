"""Build and validate docs/manifest.json from book/data/toc.tsv."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOC = ROOT / "book" / "data" / "toc.tsv"
OUT = ROOT / "docs" / "manifest.json"

TITLE = "通往单片机之路"
SUBTITLE = "从点亮一颗灯到交付一个系统"
VERSION = "0.1.0"

ALLOWED_PLATFORMS = {"f103", "f407", "gd32", "esp32", "generic"}

VOLUMES = [
    ("v0", "卷 0 · 语言与构建", "把 C、工具链与固件构建的地基打牢：能解释一段代码如何变成可烧录的固件。"),
    ("v1", "卷 1 · 裸机驱动", "从寄存器与 HAL 两条路径驱动真实外设，并能用波形、寄存器读回与最小可见结果对账。"),
    ("v2", "卷 2 · 可靠性与故障", "处理掉电、升级、看门狗、低功耗与崩溃现场，能复现失败并留下可定位证据。"),
    ("v3", "卷 3 · RTOS", "从内核源码理解任务、调度、IPC 与内存，能在 FreeRTOS 与 RT-Thread 之间做出有依据的选型。"),
    ("v4", "卷 4 · 多平台与连接", "迁移芯片与软件栈：处理 GD32、ESP32-S3、多核、Cache、网络与现场总线的差异。"),
    ("v5", "卷 5 · 运动控制", "完成电机驱动、开环调速、编码器测速与闭环控制的完整证据链。"),
    ("v6", "卷 6 · 实验与项目", "用仪器与项目验收把“能跑”推进到“能测量、能交付”。"),
    ("v7", "卷 7 · 交付与资料", "用 AI 结对、手册对账与资料体系把学习与维护变成可持续的工程流程。"),
]

VOL_DIR = {
    "v0": "v0-foundations/",
    "v1": "v1-drivers/",
    "v2": "v2-reliability/",
    "v3": "v3-rtos/",
    "v4": "v4-platforms/",
    "v5": "v5-motion/",
    "v6": "v6-labs-projects/",
    "v7": "v7-delivery/",
}


def load_toc(path: Path = TOC) -> list[dict]:
    rows = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        columns = line.split("\t")
        if len(columns) != 5:
            raise ValueError(f"{path}:{number}: expected 5 columns, got {len(columns)}")
        chapter_id, volume, title, file, platforms = columns
        rows.append(
            {
                "id": chapter_id,
                "volume": volume,
                "title": title,
                "file": file,
                "platforms": [item.strip() for item in platforms.split(",") if item.strip()],
            }
        )
    return rows


def build_manifest(rows: list[dict]) -> dict:
    parts = []
    for volume_id, volume_title, goal in VOLUMES:
        chapters = [
            {
                "id": row["id"],
                "title": row["title"],
                "file": row["file"],
                "status": "planned",
                "platforms": row["platforms"],
            }
            for row in rows
            if row["volume"] == volume_id
        ]
        parts.append({"id": volume_id, "title": volume_title, "goal": goal, "chapters": chapters})
    appendices = [
        {"id": row["id"], "title": row["title"], "file": row["file"], "status": "planned"}
        for row in rows
        if row["volume"] == "ap"
    ]
    return {
        "title": TITLE,
        "subtitle": SUBTITLE,
        "version": VERSION,
        "language": "zh",
        "parts": parts,
        "appendices": appendices,
    }


def validate(manifest: dict, rows: list[dict]) -> list[str]:
    errors = []
    chapter_ids = [chapter["id"] for part in manifest["parts"] for chapter in part["chapters"]]
    appendix_ids = [appendix["id"] for appendix in manifest["appendices"]]
    all_ids = chapter_ids + appendix_ids
    if len(all_ids) != len(set(all_ids)):
        errors.append("duplicate ids across parts and appendices")
    expected = [f"ch{i:02d}" for i in range(1, 47)]
    if chapter_ids != expected:
        errors.append(f"chapter ids must be ch01..ch46 in order, got {chapter_ids[:3]}...{chapter_ids[-1:]}")
    if appendix_ids != [f"ap{x}" for x in "ABCDEF"]:
        errors.append(f"appendix ids must be apA..apF, got {appendix_ids}")
    for row in rows:
        if not row["platforms"]:
            errors.append(f"{row['id']}: empty platforms")
        elif not set(row["platforms"]) <= ALLOWED_PLATFORMS:
            errors.append(f"{row['id']}: unknown platforms {row['platforms']}")
        if row["volume"] == "ap":
            if not row["file"].startswith("appendix/"):
                errors.append(f"{row['id']}: appendix file must live under appendix/")
        elif row["volume"] not in VOL_DIR:
            errors.append(f"{row['id']}: unknown volume {row['volume']}")
        elif not row["file"].startswith(VOL_DIR[row["volume"]]):
            errors.append(f"{row['id']}: file must start with {VOL_DIR[row['volume']]}")
    return errors


def dumps(manifest: dict) -> str:
    return json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    rows = load_toc()
    manifest = build_manifest(rows)
    errors = validate(manifest, rows)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    text = dumps(manifest)
    if args.write:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(text, encoding="utf-8")
    if args.check:
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if current != text:
            print("docs/manifest.json is stale; run python -m book.manifest --write", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

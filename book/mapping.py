"""Build and validate the source-to-chapter mapping for the merged book."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAPPING_TSV = ROOT / "book" / "data" / "mapping.tsv"
MAPPING_JSON = ROOT / "plans" / "2026-11-12-merged-book" / "mapping.json"


def load_rows(path: Path = MAPPING_TSV) -> list[dict]:
    rows = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        columns = line.split("\t")
        if len(columns) != 4:
            raise ValueError(f"{path}:{number}: expected 4 columns, got {len(columns)}")
        book, source, targets, note = columns
        rows.append(
            {
                "book": book,
                "source": source,
                "targets": [target for target in targets.split(";") if target],
                "note": note,
            }
        )
    return rows


def build(rows: list[dict]) -> dict:
    return {
        "version": 1,
        "policy": {"english": "archive", "primary_target": "first"},
        "sources": rows,
    }


def dumps(mapping: dict) -> str:
    return json.dumps(mapping, ensure_ascii=False, indent=2) + "\n"


def expected_root_sources() -> list[str]:
    manifest = json.loads((ROOT / "stm32-book" / "manifest.json").read_text(encoding="utf-8"))
    sources = [f"docs/{name}" for part in manifest["parts"] for name in part["files"]]
    sources += [f"stm32-book/book/{appendix['file']}" for appendix in manifest["appendices"]]
    sources.append("stm32-book/book/F-学习路线收束.md")
    return sources


def expected_mcu_sources() -> list[str]:
    manifest = json.loads((ROOT / "mcu" / "mcu-book" / "manifest.json").read_text(encoding="utf-8"))
    sources = [f"mcu/docs/{name}" for part in manifest["parts"] for name in part["files"]]
    sources += [f"mcu/mcu-book/book/{appendix['file']}" for appendix in manifest["appendices"]]
    return sources


def expected_motor_sources() -> list[str]:
    drafts = ROOT / "plans" / "2026-11-11-motor-control" / "chapters-draft"
    return sorted(path.relative_to(ROOT).as_posix() for path in drafts.glob("*.md"))


def validate(rows: list[dict], manifest: dict) -> list[str]:
    errors = []
    seen = set()
    for row in rows:
        key = (row["book"], row["source"])
        if key in seen:
            errors.append(f"duplicate source: {row['book']}:{row['source']}")
        seen.add(key)
    target_ids = {chapter["id"] for part in manifest["parts"] for chapter in part["chapters"]}
    target_ids |= {appendix["id"] for appendix in manifest["appendices"]}
    for row in rows:
        if not row["targets"]:
            errors.append(f"empty targets: {row['source']}")
        for target in row["targets"]:
            if target not in target_ids:
                errors.append(f"unknown target {target} for {row['source']}")
        if not (ROOT / row["source"]).exists():
            errors.append(f"missing source file: {row['source']}")
    for book, expected in (
        ("root", expected_root_sources()),
        ("mcu", expected_mcu_sources()),
        ("motor", expected_motor_sources()),
    ):
        actual = {row["source"] for row in rows if row["book"] == book}
        for source in sorted(set(expected) - actual):
            errors.append(f"unmapped {book} source: {source}")
        for source in sorted(actual - set(expected)):
            errors.append(f"unexpected {book} source: {source}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    from book import manifest as manifest_module

    rows = load_rows()
    manifest = manifest_module.build_manifest(manifest_module.load_toc())
    errors = validate(rows, manifest)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    text = dumps(build(rows))
    if args.write:
        MAPPING_JSON.parent.mkdir(parents=True, exist_ok=True)
        MAPPING_JSON.write_text(text, encoding="utf-8")
    if args.check:
        current = MAPPING_JSON.read_text(encoding="utf-8") if MAPPING_JSON.exists() else ""
        if current != text:
            print("mapping.json is stale; run python -m book.mapping --write", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

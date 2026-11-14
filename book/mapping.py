"""Build and validate the source-to-chapter mapping for the merged book."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAPPING_TSV = ROOT / "book" / "data" / "mapping.tsv"
MAPPING_JSON = ROOT / "plans" / "2026-11-12-merged-book" / "mapping.json"

ALLOWED_STATUSES = {"planned", "partial", "migrated"}


def load_rows(path: Path = MAPPING_TSV) -> list[dict]:
    rows = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        columns = line.split("\t")
        if len(columns) != 6:
            raise ValueError(f"{path}:{number}: expected 6 columns, got {len(columns)}")
        book, source, targets, purpose, status, note = columns
        rows.append(
            {
                "book": book,
                "source": source,
                "targets": [target for target in targets.split(";") if target],
                "purpose": purpose,
                "status": status,
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


def _expected_sources() -> dict:
    """AC1 冻结清单（B4 迁移完成时两书 manifest 的源文件全集）。

    B5 删除旧树后，两书 manifest 不再存在于工作树，覆盖率核对改用本冻结文件。
    """
    return json.loads((ROOT / "book" / "data" / "expected-sources.json").read_text(encoding="utf-8"))


def expected_root_sources() -> list[str]:
    return _expected_sources()["root"]


def expected_mcu_sources() -> list[str]:
    return _expected_sources()["mcu"]


def expected_motor_sources() -> list[str]:
    drafts = ROOT / "plans" / "2026-11-11-motor-control" / "chapters-draft"
    return sorted(path.relative_to(ROOT).as_posix() for path in drafts.glob("*.md"))


def validate(rows: list[dict], manifest: dict, docs_root: Path | None = None) -> list[str]:
    docs_root = Path(docs_root) if docs_root is not None else ROOT / "docs"
    errors = []
    seen = set()
    for row in rows:
        key = (row["book"], row["source"])
        if key in seen:
            errors.append(f"duplicate source: {row['book']}:{row['source']}")
        seen.add(key)
    files: dict[str, str] = {}
    for part in manifest["parts"]:
        for chapter in part["chapters"]:
            files[chapter["id"]] = chapter["file"]
    for appendix in manifest["appendices"]:
        files[appendix["id"]] = appendix["file"]
    for row in rows:
        if not row["targets"]:
            errors.append(f"empty targets: {row['source']}")
        for target in row["targets"]:
            if target not in files:
                errors.append(f"unknown target {target} for {row['source']}")
        if row["status"] in ("planned", "partial") and not (ROOT / row["source"]).exists():
            errors.append(f"missing source file: {row['source']}")
        if not row["purpose"].strip():
            errors.append(f"missing purpose: {row['source']}")
        if row["status"] not in ALLOWED_STATUSES:
            errors.append(f"unknown status {row['status']}: {row['source']}")
            continue
        known = [target for target in row["targets"] if target in files]
        existing = [target for target in known if (docs_root / files[target]).exists()]
        if row["status"] == "migrated" and len(existing) != len(known):
            missing = sorted(set(known) - set(existing))
            errors.append(f"migrated but missing chapters: {row['source']} -> {missing}")
        elif row["status"] == "partial" and not (0 < len(existing) < len(known)):
            errors.append(f"partial status inconsistent: {row['source']}")
        elif row["status"] == "planned" and existing:
            errors.append(f"planned but target exists: {row['source']}")
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

"""Chapter quality checks: contracts, links, anchors, assets and quizzes."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from book import manifest as manifest_module
from book.contracts import parse_list, split_frontmatter, validate_chapter_file

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
QUIZ_DIR = DOCS / ".vitepress" / "data" / "quizzes"

FENCE_RE = re.compile(r"^(```|~~~)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
CUSTOM_ID_RE = re.compile(r"\s*\{#([^}]+)\}\s*$")
IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
LINK_RE = re.compile(r"(?<!!)\[([^\]]+)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
QUIZ_RE = re.compile(r"<QuizBank\s+chapter=\"([^\"]+)\"\s*/>")
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")


def cjk_slugify(value: str, separator: str = "-") -> str:
    value = re.sub(r"[^\w\s-]", "", value, flags=re.UNICODE).strip().lower()
    return re.sub(r"[\s-]+", separator, value) or "section"


def heading_anchors(text: str) -> set[str]:
    anchors: set[str] = set()
    in_fence = False
    for line in text.splitlines():
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = HEADING_RE.match(line)
        if not match:
            continue
        title = match.group(2)
        custom = CUSTOM_ID_RE.search(title)
        if custom:
            anchors.add(custom.group(1))
            continue
        anchors.add(cjk_slugify(title))
    return anchors


def _line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def strip_code(text: str) -> str:
    """Blank fenced blocks and inline code so scans keep true line numbers."""
    out = []
    in_fence = False
    for line in text.splitlines(keepends=True):
        newline = "\n" if line.endswith("\n") else ""
        if FENCE_RE.match(line):
            in_fence = not in_fence
            out.append(newline)
        elif in_fence:
            out.append(newline)
        else:
            out.append(INLINE_CODE_RE.sub(lambda match: " " * len(match.group(0)), line))
    return "".join(out)


def validate_quiz(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"{path.name}: invalid JSON: {exc}"]
    if data.get("chapter") != path.stem:
        errors.append(f"{path.name}: chapter field must be {path.stem!r}")
    if not str(data.get("title", "")).strip():
        errors.append(f"{path.name}: missing title")
    questions = data.get("questions")
    if not isinstance(questions, list) or not questions:
        errors.append(f"{path.name}: questions must be a non-empty list")
        return errors
    for number, question in enumerate(questions, 1):
        options = question.get("options")
        answer = question.get("answer")
        if not str(question.get("q", "")).strip():
            errors.append(f"{path.name}: Q{number} missing q")
        if not isinstance(options, list) or len(options) < 2:
            errors.append(f"{path.name}: Q{number} needs at least 2 options")
        elif not isinstance(answer, int) or not 0 <= answer < len(options):
            errors.append(f"{path.name}: Q{number} answer out of range")
        if not str(question.get("a", "")).strip():
            errors.append(f"{path.name}: Q{number} missing a")
    return errors


def check_file(path: Path, docs_root: Path, quiz_dir: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    scan = strip_code(text)
    anchored = heading_anchors(text)
    quiz_ids: list[str] = []
    for match in IMAGE_RE.finditer(scan):
        alt, target = match.group(1), match.group(2)
        line = _line_of(scan, match.start())
        if not alt.strip():
            errors.append(f"{path}:{line}: image missing alt")
        if target.startswith(("http://", "https://", "//")):
            errors.append(f"{path}:{line}: external image not allowed: {target}")
            continue
        if target.startswith("/"):
            candidate = docs_root / "public" / target.lstrip("/")
        else:
            candidate = (path.parent / target).resolve()
        if not candidate.exists():
            errors.append(f"{path}:{line}: missing asset: {target}")
    for match in LINK_RE.finditer(scan):
        target = match.group(2)
        line = _line_of(scan, match.start())
        if target.startswith(("http://", "https://", "mailto:", "tel:")):
            continue
        if target.startswith("/"):
            errors.append(f"{path}:{line}: root-absolute page link not allowed: {target}")
            continue
        target_path, _, fragment = target.partition("#")
        if not target_path:
            if fragment and fragment not in anchored:
                errors.append(f"{path}:{line}: missing anchor: #{fragment}")
            continue
        if not target_path.endswith(".md"):
            errors.append(f"{path}:{line}: link must target a .md file: {target}")
            continue
        candidate = (path.parent / target_path).resolve()
        try:
            candidate.relative_to(docs_root.resolve())
        except ValueError:
            errors.append(f"{path}:{line}: link escapes docs/: {target}")
            continue
        if not candidate.exists():
            errors.append(f"{path}:{line}: missing chapter file: {target_path}")
            continue
        if fragment and fragment not in heading_anchors(candidate.read_text(encoding="utf-8")):
            errors.append(f"{path}:{line}: missing anchor in {target_path}: #{fragment}")
    for match in QUIZ_RE.finditer(scan):
        quiz_id = match.group(1)
        line = _line_of(scan, match.start())
        quiz_ids.append(quiz_id)
        if not (quiz_dir / f"{quiz_id}.json").exists():
            errors.append(f"{path}:{line}: missing quiz: {quiz_id}")
    return errors, quiz_ids


def check_book(
    docs_root: Path = DOCS,
    quiz_dir: Path = QUIZ_DIR,
    only: list[str] | None = None,
) -> list[str]:
    manifest = manifest_module.build_manifest(manifest_module.load_toc())
    entries = [chapter for part in manifest["parts"] for chapter in part["chapters"]]
    entries += manifest["appendices"]
    if only:
        known = {entry["id"] for entry in entries}
        unknown = sorted(set(only) - known)
        if unknown:
            return [f"unknown chapter: {item}" for item in unknown]
        entries = [entry for entry in entries if entry["id"] in set(only)]
    errors: list[str] = []
    existing = 0
    quiz_refs: dict[str, set[str]] = {}
    for entry in entries:
        path = docs_root / entry["file"]
        if not path.exists():
            if only:
                errors.append(f"{entry['id']}: missing file: {entry['file']}")
            continue
        existing += 1
        errors.extend(f"{entry['id']}: {error}" for error in validate_chapter_file(path))
        text = path.read_text(encoding="utf-8")
        meta, _ = split_frontmatter(text)
        if meta.get("title", "").strip().strip("\"'") != entry["title"]:
            errors.append(f"{entry['id']}: frontmatter title must be {entry['title']!r}")
        expected_platforms = entry.get("platforms")
        if expected_platforms is not None:
            actual = set(parse_list(meta.get("platforms", "")))
            if actual != set(expected_platforms):
                errors.append(f"{entry['id']}: frontmatter platforms must be {expected_platforms}")
        file_errors, quiz_ids = check_file(path, docs_root, quiz_dir)
        errors.extend(file_errors)
        for quiz_id in quiz_ids:
            quiz_refs.setdefault(quiz_id, set()).add(entry["id"])
    if not only and existing == 0:
        errors.append(f"no chapter files found under {docs_root}")
    if only:
        for quiz_id in sorted(quiz_refs):
            quiz_path = quiz_dir / f"{quiz_id}.json"
            if quiz_path.exists():
                errors.extend(validate_quiz(quiz_path))
    elif quiz_dir.exists():
        for quiz_path in sorted(quiz_dir.glob("*.json")):
            errors.extend(validate_quiz(quiz_path))
            owners = quiz_refs.get(quiz_path.stem, set())
            if not owners:
                errors.append(f"orphan quiz: {quiz_path.name}")
            elif len(owners) > 1:
                errors.append(f"quiz referenced by multiple chapters: {quiz_path.name} -> {sorted(owners)}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="校验章节契约、链接锚点、资产与测验。")
    parser.add_argument("--chapter", action="append", default=[], help="只检查指定章 id，可重复")
    parser.add_argument("--check", action="store_true", help="兼容 CI 的显式开关")
    args = parser.parse_args(argv)
    errors = check_book(only=args.chapter or None)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

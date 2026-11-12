"""Chapter contract checks shared by every migration batch (B1-B4)."""

from __future__ import annotations

from pathlib import Path

REQUIRED_COMPASS = ("问题", "交付", "边界", "依据锚点")
ALLOWED_PLATFORMS = {"f103", "f407", "gd32", "esp32", "generic"}


def split_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    raw = text[4:end]
    body = text[end + 5 :]
    meta: dict[str, str] = {}
    for line in raw.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip()
    return meta, body


def parse_list(value: str) -> list[str]:
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        value = value[1:-1]
    return [item.strip().strip("\"'") for item in value.split(",") if item.strip()]


def validate_chapter_file(path: Path) -> list[str]:
    path = Path(path)
    if not path.exists():
        return [f"missing file: {path}"]
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    meta, body = split_frontmatter(text)
    if not meta.get("title"):
        errors.append("frontmatter missing title")
    platforms = parse_list(meta.get("platforms", ""))
    if not platforms:
        errors.append("frontmatter missing platforms")
    elif not set(platforms) <= ALLOWED_PLATFORMS:
        errors.append(f"unknown platform(s): {sorted(set(platforms) - ALLOWED_PLATFORMS)}")
    if "## 本章罗盘" not in body:
        errors.append("missing section: ## 本章罗盘")
    for label in REQUIRED_COMPASS:
        if f"**{label}**" not in body:
            errors.append(f"compass missing label: {label}")
    return errors

"""Read one H2 section of a chapter, wherever it sits in the chapter.

Chapter tests check facts inside a section. They do not care which
section comes next, so a chapter can reorder its sections freely.
"""

from __future__ import annotations

ZH_BLOCKS = ("## 原理与适用范围", "## 关键插图", "## 时序与状态", "## 常见坑与出处")
EN_BLOCKS = ("## Principle and scope", "## Key figures", "## Timing and state", "## Pitfalls and sources")


def section(text: str, heading: str) -> str:
    """Lines under ``heading`` up to the next H2. Fenced code is skipped when looking for H2."""
    lines = text.replace("\r\n", "\n").split("\n")
    start = None
    fence = False
    for i, line in enumerate(lines):
        if line.lstrip().startswith("```"):
            fence = not fence
            continue
        if fence:
            continue
        if start is None:
            if line.rstrip() == heading:
                start = i + 1
        elif line.startswith("## "):
            return "\n".join(lines[start:i])
    if start is None:
        raise AssertionError(f"heading not found: {heading!r}")
    return "\n".join(lines[start:])


def blocks(text: str, lang: str) -> str:
    """The four reference sections joined together: principle, figures, timing, pitfalls."""
    heads = ZH_BLOCKS if lang == "zh" else EN_BLOCKS
    return "\n".join(section(text, heading) for heading in heads)

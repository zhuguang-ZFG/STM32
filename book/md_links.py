"""Repo-wide Markdown link check for the surfaces book.checks does not cover.

book.checks validates the manifest chapters plus ENTRY_DOCS. The root README,
cheatsheets/*.md and examples/*/README.md sit outside both, and that is where
the last rounds of defects lived: eleven example READMEs still pointed at
retired docs/NN-*.md paths, and the HAL cheatsheet's TOC used five anchors no
renderer produces.

Fragments are resolved against the renderer each file actually ships to.
docs/** is built by VitePress, so book.checks.heading_anchors is the standard.
Everything else is read on github.com, which deletes punctuation but keeps the
spaces around it, so ``（HAL / RCC）`` becomes ``hal--rcc`` rather than
``hal-rcc``. github_slug implements that rule; the tests pin it to ids read
off a rendered GitHub page instead of a re-derivation.
"""

from __future__ import annotations

import re
import subprocess
import sys
import unicodedata
from pathlib import Path

from book import checks

ROOT = Path(__file__).resolve().parent.parent

#: Trees with their own gates or their own history. plans/ records past merge
#: decisions, mcu/ is the sister book, fixtures deliberately hold bad links.
SKIP_PREFIXES = (
    "mcu/",
    "plans/",
    "docs/superpowers/",
    "node_modules/",
    "book/tests/fixtures/",
)

#: Skipped by the VitePress build, so their fragments are GitHub's problem.
#: (Shared with ``checks.check_entry_doc`` via ``checks.SITE_EXCLUDED``.)

SCHEMES = ("http://", "https://", "//", "mailto:", "tel:", "data:")

#: Raw HTML contributes links too — the README gallery is a <table> of <img src>.
HTML_ATTR_RE = re.compile(r'(?:src|href)="([^"]+)"')

#: Built by deploy.yml and copied under /book/ at publish time, so they are
#: absent from a checkout by design (deploy.yml: book/dist/print/merged-book.*).
ALLOWED = {
    ("docs/index.md", "book/merged-book.pdf"),
    ("docs/index.md", "book/merged-book.html"),
    ("docs/index.md", "book/merged-book.epub"),
}


def github_slug(title: str) -> str:
    """Slug the way github.com does for a heading.

    Punctuation and symbols are dropped, every space becomes one hyphen and
    runs are *not* collapsed. Verified against ``id="user-content-..."``
    values on rendered pages, including the double hyphens.
    """
    out: list[str] = []
    for char in title.strip().lower():
        if char in "_-":
            out.append(char)
        elif char.isspace():
            out.append("-")
        elif unicodedata.category(char)[0] in "PSCZ":
            continue
        else:
            out.append(char)
    return "".join(out)


def github_anchors(text: str) -> set[str]:
    """Heading ids GitHub generates, including the ``-1`` duplicate suffix.

    Quoted headings count: the root README styles its note cards as
    ``> ### 标题`` and github.com does emit an id for them (verified on the
    rendered page), so a link to their anchor works.

    Fenced blocks are skipped, as GitHub skips them: a ``# fake`` line inside
    a fence is sample text, and counting it would both invent an anchor and
    push a later real duplicate onto ``-1``. Inline code in a heading stays,
    because GitHub slugs the rendered text (backticks removed, the rest kept).
    """
    seen: dict[str, int] = {}
    anchors: set[str] = set()
    in_fence = False
    for line in text.splitlines():
        if checks.FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        body = line
        while body.startswith(">"):
            body = body[1:].lstrip()
        match = checks.HEADING_RE.match(body)
        if not match:
            continue
        slug = github_slug(match.group(2))
        count = seen.get(slug, 0)
        seen[slug] = count + 1
        anchors.add(slug if count == 0 else f"{slug}-{count}")
    return anchors


def skipped(rel: str) -> bool:
    return any(rel.startswith(prefix) for prefix in SKIP_PREFIXES)


def markdown_files(root: Path) -> list[Path]:
    """Tracked Markdown, minus the trees listed in SKIP_PREFIXES.

    ``git ls-files -z`` emits raw UTF-8 path bytes, so they are decoded as
    UTF-8 explicitly; letting subprocess pick the locale codepage breaks on a
    stock Windows shell, where it would be cp936.
    """
    try:
        listed = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z", "*.md"],
            capture_output=True,
            check=True,
            encoding="utf-8",
        ).stdout
        paths = [root / name for name in listed.split("\0") if name]
    except (OSError, subprocess.CalledProcessError):
        paths = sorted(root.rglob("*.md"))
    files: list[Path] = []
    for path in paths:
        rel = path.relative_to(root).as_posix()
        if path.is_file() and not skipped(rel):
            files.append(path)
    return files


def anchors_for(path: Path, root: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    if checks.is_site_page(path, root):
        return checks.heading_anchors(text, duplicate_suffix="_")
    return github_anchors(text)


def check(root: Path = ROOT, files: list[Path] | None = None) -> list[str]:
    errors: list[str] = []
    for path in files if files is not None else markdown_files(root):
        rel = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8")
        scan = checks.strip_code(text)
        found = [
            (match.group(2), match.start())
            for pattern in (checks.IMAGE_RE, checks.LINK_RE)
            for match in pattern.finditer(scan)
        ]
        found += [(match.group(1), match.start()) for match in HTML_ATTR_RE.finditer(scan)]
        for target, offset in found:
            line = checks._line_of(scan, offset)
            if target.startswith(SCHEMES):
                continue
            if (rel, target) in ALLOWED:
                continue
            path_part, _, fragment = target.partition("#")
            if not path_part and not fragment:
                continue
            if path_part.startswith("/"):
                # VitePress serves docs/public/ at the site root.
                base = root / "docs" / "public" / path_part.lstrip("/")
            else:
                base = path if not path_part else (path.parent / path_part).resolve()
            if path_part and not base.exists():
                errors.append(f"{rel}:{line}: missing link target: {target}")
                continue
            if not fragment or base.suffix != ".md":
                continue
            if not base.is_relative_to(root):
                continue
            if fragment not in anchors_for(base, root):
                errors.append(
                    f"{rel}:{line}: missing anchor in "
                    f"{base.relative_to(root).as_posix()}: #{fragment}"
                )
    return errors


def main() -> int:
    files = markdown_files(ROOT)
    errors = check(ROOT, files)
    for error in errors:
        print(error)
    print(f"{len(files)} markdown files scanned, {len(errors)} problem(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

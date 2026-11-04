# -*- coding: utf-8 -*-
"""Rewrite crude gen_gifs builders for ch00/01/18/19 AUX GIFs."""
from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
GEN = ROOT / "tools" / "gen_gifs.py"
SNIP = Path(__file__).resolve().parent / "gif_snippets"

FUNCS = (
    "boot0_low",
    "one_slot",
    "swd_fetch",
)


def _replace_fn(src: str, fn_name: str, new_body: str) -> str:
    marker = f"def {fn_name}("
    start = src.index(marker)
    rest = src[start + len(marker) :]
    candidates = []
    for token in ("\ndef ", "\nBUILDERS", "\nif __name__"):
        i = rest.find(token)
        if i >= 0:
            candidates.append(i)
    if not candidates:
        raise RuntimeError(f"no next boundary after {fn_name}")
    end = start + len(marker) + min(candidates)
    return src[:start] + new_body.rstrip() + "\n" + src[end:]


def main() -> None:
    src = GEN.read_text(encoding="utf-8")
    if "BUILDERS =" not in src:
        raise SystemExit("gen_gifs.py missing BUILDERS before patch — restore first")
    for name in FUNCS:
        body = (SNIP / f"{name}.py").read_text(encoding="utf-8")
        src = _replace_fn(src, name, body)
        print("patched", name)
    if "BUILDERS =" not in src:
        raise SystemExit("BUILDERS wiped by patch — abort write")
    GEN.write_text(src, encoding="utf-8")
    print("wrote", GEN)


if __name__ == "__main__":
    main()

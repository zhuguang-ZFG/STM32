# -*- coding: utf-8 -*-
"""Rewrite crude gen_gifs builders for ch11–17 AUX GIFs."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GEN = ROOT / "tools" / "gen_gifs.py"
SNIP = Path(__file__).resolve().parent / "gif_snippets"

FUNCS = (
    "iwdg_1s",
    "iap_jump",
    "can_500k",
    "usb_48m",
    "rtos_tick",
    "stop_wake_gif",
    "cfsr_read_gif",
)


def _replace_fn(src: str, fn_name: str, new_body: str) -> str:
    marker = f"def {fn_name}("
    start = src.index(marker)
    rest = src[start + len(marker) :]
    next_def = rest.find("\ndef ")
    if next_def < 0:
        raise RuntimeError(f"no next def after {fn_name}")
    end = start + len(marker) + next_def
    return src[:start] + new_body.rstrip() + "\n" + src[end:]


def main() -> None:
    src = GEN.read_text(encoding="utf-8")
    for name in FUNCS:
        body = (SNIP / f"{name}.py").read_text(encoding="utf-8")
        src = _replace_fn(src, name, body)
        print("patched", name)
    GEN.write_text(src, encoding="utf-8")
    print("wrote", GEN)


if __name__ == "__main__":
    main()

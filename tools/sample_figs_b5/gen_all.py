#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regenerate all B5 static diagrams and mechanism animations."""

from __future__ import annotations

import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.dirname(HERE))


def _load(name: str):
    path = os.path.join(HERE, name)
    spec = importlib.util.spec_from_file_location(name.replace(".py", ""), path)
    mod = importlib.util.module_from_spec(spec)
    # register for sibling imports if needed
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def main() -> None:
    diagrams = os.path.join(ROOT, "assets", "diagrams")
    animations = os.path.join(ROOT, "assets", "animations")
    for name in ("ch18_b5.py", "ch19_b5.py", "ch20_b5.py", "ch21_b5.py", "ch22_b5.py"):
        _load(name).main(diagrams)
    _load("anim_b5.py").main(animations)


if __name__ == "__main__":
    main()

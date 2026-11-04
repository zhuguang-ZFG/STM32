#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import runpy
from pathlib import Path
HERE = Path(__file__).resolve().parent

def main() -> None:
    runpy.run_path(str(HERE / "figures_q3.py"), run_name="__main__")
    runpy.run_path(str(HERE / "anim_q3.py"), run_name="__main__")
    runpy.run_path(str(HERE / "patch_crude_gifs.py"), run_name="__main__")
    runpy.run_path(str(HERE / "embed_q3.py"), run_name="__main__")

if __name__ == "__main__":
    main()

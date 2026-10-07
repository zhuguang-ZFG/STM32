#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键生成 assets/animations/*.svg。

用法::

    python3 tools/gen_animations.py            # 生成全部
    python3 tools/gen_animations.py gpio-blink # 只生成指定文件

每个动画模块导出 ALL（函数列表）与 NAMES（函数名 -> 输出文件名）。
"""

from __future__ import annotations

import importlib
import os
import sys
import xml.dom.minidom

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "assets", "animations")
sys.path.insert(0, HERE)

MODULES = ["anim_basics", "anim_gpio", "anim_comm", "anim_sys"]


def collect():
    jobs = []
    for name in MODULES:
        try:
            mod = importlib.import_module(name)
        except ModuleNotFoundError:
            print(f"[skip] {name} 不存在")
            continue
        for fn in mod.ALL:
            out = mod.NAMES[fn.__name__] + ".svg"
            jobs.append((name, fn, out))
    return jobs


def main(argv):
    only = set(argv[1:])
    jobs = collect()
    ok = 0
    for mod_name, fn, out in jobs:
        if only and out not in only and out[:-4] not in only:
            continue
        svg = fn()
        path = os.path.join(OUT, out)
        svg.save(path)
        # 立即校验 XML 合法性，避免生成坏图
        xml.dom.minidom.parse(path)
        size = os.path.getsize(path)
        print(f"[ok] {mod_name}.{fn.__name__:26s} -> assets/animations/{out:26s} "
              f"{size / 1024:6.1f} KB")
        ok += 1
    print(f"共生成 {ok} 个动画")


if __name__ == "__main__":
    main(sys.argv)

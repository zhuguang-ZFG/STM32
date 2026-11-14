# -*- coding: utf-8 -*-
"""ESP-IDF project anatomy plate (ch30).

Facts pinned to ESP-IDF v5.5.2 build-system docs:
- main/ is the project component; components/ are local components.
- managed_components/ is populated by IDF Component Manager and is normally
  not versioned; do not edit it by hand.
- idf_component.yml declares dependency sources/versions (registry, git, path);
  dependencies.lock records resolved versions and is auto-generated.
- component search precedence: project components > EXTRA_COMPONENT_DIRS >
  managed components > ESP-IDF components.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hd import *  # noqa: E402,F401,F403


def _card(f, x, y, w, h, title, sub, color, size=19, body=13):
    f.rect(x, y, w, h, color=color, fill=WHITE, sw=2.2)
    f.text(x + 12, y + size + 6, title, size=size, color=color,
           weight="bold")
    if sub:
        f.text(x + 12, y + size + 22, sub, size=body, color=MUTED)


def idf_anatomy():
    f = Fig("arch-idf-anatomy", "ESP-IDF 工程解剖 / source → image")

    # project sources
    px, py, pw, ph = 48, 120, 330, 310
    f.rect(px, py, pw, ph, color=GREEN_D, fill=PAPER, sw=2.8)
    f.text(px + 14, py + 30, "工程源", size=23, color=GREEN_D, weight="bold")
    _card(f, px + 14, py + 46, pw - 28, 54, "main/", "项目组件，自动收集",
          GREEN_D)
    _card(f, px + 14, py + 104, pw - 28, 54, "components/", "本地组件，优先级最高",
          GREEN_D)
    _card(f, px + 14, py + 162, pw - 28, 54, "managed_components/",
          "组件管理器下载；通常不入库", BLUE_D)
    _card(f, px + 14, py + 220, pw - 28, 54, "idf_component.yml",
          "registry / git / path；lock 记版本", AMBER_STROKE)
    f.text(px + 14, py + 298, "解析结果进同一张组件图；lock 只记版本。", size=13,
           color=MUTED)

    # build graph
    bx, by, bw, bh = 402, 120, 338, 310
    f.rect(bx, by, bw, bh, color=BLUE_D, fill=WHITE, sw=2.8)
    f.text(bx + 14, by + 30, "组件图", size=23, color=BLUE_D, weight="bold")
    _card(f, bx + 14, by + 46, bw - 28, 54, "project.cmake",
          "include targets / idf / 收集 main", BLUE_D)
    _card(f, bx + 14, by + 106, bw - 28, 54, "idf_component_register",
          "SRCS / INCLUDE_DIRS / REQUIRES", BLUE_D)
    _card(f, bx + 14, by + 166, bw - 28, 54, "REQUIRES 依赖图",
          "按拓扑排序定编译顺序", BLUE_D)
    _card(f, bx + 14, by + 226, bw - 28, 54, "build/",
          "对象文件 + 静态库 + app.bin", AMBER_STROKE)
    f.text(bx + 14, by + 298, "先从源码找组件，再按依赖图编译。", size=14,
           color=MUTED)

    # image + flash
    rx, ry, rw, rh = 764, 120, 340, 310
    f.rect(rx, ry, rw, rh, color=RED, fill=WHITE, sw=2.8)
    f.text(rx + 14, ry + 30, "镜像与烧录", size=23, color=RED, weight="bold")
    _card(f, rx + 14, ry + 48, rw - 28, 54, "app.bin", "编译 + 链接产物",
          RED, size=19, body=14)
    _card(f, rx + 14, ry + 112, rw - 28, 54, "factory / ota_0 / ota_1",
          "分区表决定落点", RED, size=17, body=14)
    _card(f, rx + 14, ry + 176, rw - 28, 54, "ROM → 2nd bootloader → app",
          "上电三棒接力", BLUE_D, size=17, body=14)
    f.text(rx + 14, ry + 258, "app.bin 只是文件；分区表决定它住哪。", size=15,
           color=MUTED)

    # search precedence
    qx, qy, qw, qh = 48, 456, 1056, 176
    f.rect(qx, qy, qw, qh, color=AMBER_STROKE, fill=PAPER, sw=2.8)
    f.text(qx + 16, qy + 30, "同名组件谁优先？从高到低", size=22,
           color=AMBER_STROKE, weight="bold")
    items = [
        ("components/", "项目组件", GREEN_D),
        ("EXTRA_COMPONENT_DIRS", "额外目录", BLUE_D),
        ("managed_components/", "组件管理器", AMBER_STROKE),
        ("$IDF_PATH/components", "IDF 自带", MUTED),
    ]
    x = qx + 16
    for i, (name, sub, c) in enumerate(items):
        f.rect(x, qy + 52, 238, 58, color=c, fill=WHITE, sw=2.0)
        f.text(x + 10, qy + 76, name, size=15, color=c, weight="bold")
        f.text(x + 10, qy + 97, sub, size=14, color=MUTED)
        if i < 3:
            f.arrow(x + 240, qy + 81, x + 258, qy + 81, color=INK,
                    sw=1.9, bend=0.0)
        x += 258
    f.text(qx + 16, qy + 140,
           "managed_components 不手改、通常不入库；要改就复制到 components/。", size=16,
           color=RED)
    f.text(qx + 16, qy + 162,
           "没有 idf_component.yml 就不生成 dependencies.lock。", size=15,
           color=MUTED)

    # closing
    f.htext(576, 700, "idf.py build = CMake + Component Manager；menuconfig → sdkconfig → sdkconfig.h。",
            size=20, color=AMBER_STROKE, anchor="middle", weight="bold",
            hl=True, hl_fill=AMBER_FILL)
    return f


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[2] / "assets" / "illustrations" / "handraw"
    save(idf_anatomy(), str(out / "arch-idf-anatomy.svg"))
    print("wrote arch-idf-anatomy.svg")

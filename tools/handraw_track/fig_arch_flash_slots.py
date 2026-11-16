# -*- coding: utf-8 -*-
"""STM32 IAP slot plate (ch17): single slot has no way back, dual slots do.

Facts pinned to the chapter: F407VG has 1 MB in 12 sectors (4x16 + 64 + 7x128
KB), sector 11 at 0x080E0000. Single slot: boot sector 0, app at 0x08004000,
parameter sector 11. Dual slot: metadata in sector 1, Slot A sectors 2-7
(0x08008000, 480 KB), Slot B sectors 8-11 (0x08080000, 512 KB, 480 KB usable,
last 32 KB unused). F103C8: 64 KB, 1 KB pages; single slot boot 16 KB, param
2 KB, app 46 KB; dual slot 16 + 2 + 22 + 22 + 2 KB.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hd import *  # noqa: E402,F401,F403


def _slot(f, x, y, w, h, title, lines, color, fill=WHITE, size=17, sub=14):
    f.rect(x, y, w, h, color=color, fill=fill, sw=2.2)
    f.text(x + 12, y + 26, title, size=size, color=color, weight="bold")
    for i, ln in enumerate(lines):
        f.text(x + 12, y + 50 + i * 22, ln, size=sub, color=MUTED)


def flash_slots():
    f = Fig("arch-flash-slots", "双槽：先写备槽，再改票")

    f.text(64, 136, "布局示意，不按比例；地址与大小是本章算术。", size=14,
           color=MUTED)

    f.rect(48, 152, 1056, 186, color=BLUE_D, fill=WHITE, sw=2.6)
    f.htext(64, 184, "单槽：升级直接覆盖唯一副本", size=22,
            color=BLUE_D, weight="bold")
    _slot(f, 68, 206, 150, 82, "Bootloader",
          ["S0 / 0x08000000", "16 KB"], GREEN_D)
    _slot(f, 232, 206, 600, 82, "App",
          ["0x08004000 起", "单槽可用到扇区 10"], BLUE_D)
    _slot(f, 846, 206, 238, 82, "参数区",
          ["S11 / 0x080E0000", "128 KB"], AMBER_STROKE)
    f.text(64, 320,
           "写坏或断电，旧程序已经不在了；只能留在 Bootloader 等重传。",
           size=16, color=RED)

    f.rect(48, 356, 1056, 210, color=GREEN_D, fill=WHITE, sw=2.6)
    f.htext(64, 388, "双槽：新固件写另一个槽", size=22,
            color=GREEN_D, weight="bold")
    _slot(f, 68, 410, 130, 92, "Boot",
          ["S0 / 16 KB", "不参与升级"], GREEN_D, size=16)
    _slot(f, 212, 410, 130, 92, "元数据",
          ["S1 / 16 KB", "追加记录"], AMBER_STROKE, size=16)
    _slot(f, 356, 410, 350, 92, "Slot A（扇区 2–7）",
          ["0x08008000 / 480 KB", "16+16+64+128×3"], BLUE_D, size=16)
    _slot(f, 730, 410, 340, 92, "Slot B（扇区 8–11）",
          ["0x08080000 / 512 KB", "实用 480 KB；末尾 32 KB 留空"], RED,
          size=16)
    f.text(64, 538,
           "先写备槽 → 校验 → 追加提交记录 → 下次启动确认；当前槽不动。",
           size=16, color=INK)

    f.rect(48, 584, 1056, 130, color=AMBER_STROKE, fill=WHITE, sw=2.6)
    f.htext(64, 614, "两套版图的算术", size=20, color=AMBER_STROKE,
            weight="bold")
    f.text(64, 646,
           "F407：1 MB = 4×16 + 64 + 7×128 KB；Slot A 480 KB，Slot B 实用 480 KB。",
           size=15, color=INK)
    f.text(64, 674,
           "F103C8：64 KB = Boot 16 + 元数据 2 + Slot A 22 + Slot B 22 + 备用 2。",
           size=15, color=INK)
    f.text(64, 702,
           "双槽不是免费：单槽 App 46 KB，双槽每个槽只剩 22 KB。",
           size=15, color=RED)

    f.htext(576, 744, "先写备槽，再改票；记录写一半断电，上一条仍然有效。",
            size=22, color=AMBER_STROKE, anchor="middle", weight="bold",
            hl=True, hl_fill=AMBER_FILL)
    return f


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[2] / "assets" / "illustrations" / "handraw"
    save(flash_slots(), str(out / "arch-flash-slots.svg"))
    print("wrote arch-flash-slots.svg")

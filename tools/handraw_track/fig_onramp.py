# -*- coding: utf-8 -*-
"""Hand-drawn plates for the onramp volume (ch00 from-box-to-blink).

Facts pinned to the chapter (docs/onramp/00-from-box-to-blink.md), verbatim:
六站 = 开箱清点(BluePill+ST-Link+USB-TTL 3.3 V 档) → 装环境(arm-none-eabi-gcc
+ make, 两条 --version) → 第一次构建(make → *.elf/*.bin 无 error) → 烧录
(make flash, SWD 四线, 日志含 Flash write) → 点灯(PC13 约 1 Hz, 低电平点亮)
→ 第一句话(115200 8N1, AT→OK, TX/RX 交叉, 共地); L0 三样证据 = 构建日志 /
烧录记录 / 最小可见结果, 记进第 40 章记录表; 两条路 = 顺读第 1 章 / 按周走
第 46 章十八周排期。全部为章内冻结口径的转引, 无新数字。

Composition discipline borrowed from the stick-scene craft sheet (2026-11-17):
no text closer than ~4 px to a box edge, arrows as open chevrons, nothing
cropped at the canvas edge, one accent family per band.
"""
from pathlib import Path
import sys

from hd import *

STAGE = Path(__file__).resolve().parents[2] / ".temp" / "l0-l5-pass" / "figures"


def ch00_onramp_six_stops():
    f = Fig("ch00-onramp-six-stops", "第 0 周六站：从快递盒到 1 Hz",
            tag="上手卷 · 第 0 周")

    # ---- 六站卡片：2×3，蛇形读序 1→2→3 ↓ 4→5→6 --------------------------
    cards = [
        # (col, row, num, label, line1, line2, pictogram key)
        (0, 0, "1", "开箱清点", "BluePill + ST-Link + USB-TTL",
         "共地先于信号；USB-TTL 拨 3.3 V 档", "chip"),
        (1, 0, "2", "装环境", "arm-none-eabi-gcc + make",
         "两条 --version 有输出，环境就绪", None),
        (2, 0, "3", "第一次构建", "make → *.elf / *.bin",
         "结束无 error 才进烧录", "doc"),
        (0, 1, "4", "烧录", "make flash（SWD 四线）",
         "日志里出现 Flash write 字样", None),
        (1, 1, "5", "点灯", "PC13 约 1 Hz（低电平点亮）",
         "外接 PA0 灯每 5 s 翻转一次", "led"),
        (2, 1, "6", "第一句话", "115200 8N1，发 AT 回 OK",
         "TX/RX 交叉，忘了就「发了没回」", "ok"),
    ]
    CW, CH = 320, 136
    XS = [60, 416, 772]
    ROW_Y = [150, 420]

    for col, row, num, label, l1, l2, pict in cards:
        x, y = XS[col], ROW_Y[row]
        f.card(x, y, CW, CH, BLUE_D)
        f.circle(x + 34, y + 40, 15, color=BLUE_D, sw=1.8, fill=BLUE_D)
        f.text(x + 34, y + 45, num, size=13, color=WHITE, anchor="middle",
               weight="bold", halo=False)
        f.text(x + 62, y + 47, label, size=22, color=INK, weight="bold")
        f.text(x + 22, y + 82, l1, size=15, color=INK)
        f.text(x + 22, y + 110, l2, size=15, color=MUTED)
        if pict == "chip":
            f.chip(x + CW - 74, y + 22, 48, 36, BLUE_D, pins=3)
        elif pict == "doc":
            f.doc(x + CW - 74, y + 20, 50, 58, BLUE_D, label=".bin", size=13)
        elif pict == "led":
            f.circle(x + CW - 48, y + 36, 12, color=GREEN_D, sw=2.2,
                     fill=GREEN_D)
            f.text(x + CW - 48, y + 66, "1 Hz", size=13, color=GREEN_D,
                   anchor="middle", weight="bold")
        elif pict == "ok":
            f.pill(x + CW - 78, y + 22, 52, 30, "OK", GREEN_D, size=15)

    # 站间箭头（开口箭头，同排）
    for row_y in ROW_Y:
        cy = row_y + CH / 2
        for gx in (380, 736):
            f.arrow(gx + 4, cy, gx + 32, cy, color=BLUE, sw=2.6, bend=0,
                    head=10)
    # ③→④ 跨行大箭头：从第三张卡底部弯到第四张卡顶部，走行间空带
    f.arrow(900, 298, 240, 406, color=BLUE, sw=2.8, bend=-0.15, head=13)
    f.text(576, 342, "同一份例程，make 与 make flash 各一次", size=16,
           color=MUTED, anchor="middle")

    # ---- 收口带：L0 三样证据 + 两条路 ------------------------------------
    f.line(60, 586, 1092, 586, color=SHADOW, sw=1.4, amp=0.8, opacity=0.9)

    f.text(60, 632, "L0 三样证据", size=21, color=GREEN_D, weight="bold")
    ev = [("构建日志", 118), ("烧录记录", 118), ("最小可见结果", 158)]
    ex = 60
    for label, pw in ev:
        f.pill(ex, 654, pw, 42, label, GREEN_D, size=18)
        ex += pw + 16
    f.text(60, 736, "一句话记录即可：PC13 约 1 Hz——闪了，就过了；格式见第 40 章记录表",
           size=15, color=MUTED)

    f.text(620, 632, "两条路", size=21, color=GREEN_D, weight="bold")
    f.pill(620, 654, 74, 42, "顺读", GREEN_D, size=18)
    f.arrow(704, 675, 752, 675, color=GREEN_D, sw=2.4, bend=0, head=10)
    f.text(766, 681, "第 1 章 · 变量的两个地址", size=17, color=INK)
    f.pill(620, 706, 88, 42, "按周走", GREEN_D, size=18)
    f.arrow(718, 727, 766, 727, color=GREEN_D, sw=2.4, bend=0, head=10)
    f.text(780, 733, "第 46 章 · 十八周排期", size=17, color=INK)
    return f


FIGS = {
    "ch00-onramp-six-stops": ch00_onramp_six_stops,
}

if __name__ == "__main__":
    names = sys.argv[1:] or list(FIGS)
    STAGE.mkdir(parents=True, exist_ok=True)
    for n in names:
        f = FIGS[n]()
        save(f, str(STAGE / (n + ".svg")))
        print("wrote", STAGE / (n + ".svg"))

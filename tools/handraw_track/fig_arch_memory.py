# -*- coding: utf-8 -*-
"""Two architecture plates: linker sections and the Cortex-M 4GB map.

Both keep the chapter facts: F407 linker-section ownership (ch01) and the
ARMv7-M eight-region address map with F407 landmarks (ch08). Rendered to
docs/public/arch/ for the book; SVG source stays reproducible here.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hd import *  # noqa: E402,F401,F403


def _block(f, x, y, w, h, name, note, color, size=27):
    f.rect(x, y, w, h, color=color, fill=WHITE, sw=2.6)
    f.htext(x + 18, y + size + 6, name, size=size, color=color,
            weight="bold")
    f.text(x + 18, y + size + 40, note, size=21, color=INK)


def linker_sections():
    f = Fig("arch-memory-map-v2",
            "上电后，谁住在 Flash，谁住在 RAM / two homes")

    # Flash panel
    fx, fy, fw, fh = 48, 138, 420, 520
    f.rect(fx, fy, fw, fh, color=GREEN_D, fill=PAPER, sw=3.0)
    f.htext(fx + 20, fy + 38, "Flash · 0x0800_0000", size=29,
            color=GREEN_D, weight="bold")
    f.text(fx + 20, fy + 66, "掉电不丢；只读，跑代码", size=20, color=MUTED)

    blocks = [
        (".isr_vector", "第 0 字 = 栈顶；第 1 字 = 复位入口", GREEN_D),
        (".text", "指令；.rodata 也并进来", GREEN_D),
        (".rodata", "const 与字符串；地址仍在 Flash", GREEN_D),
        (".data 初值 (_sidata)", "12 B 初值副本；本体在 RAM", AMBER_STROKE),
    ]
    by = fy + 88
    for name, note, c in blocks:
        _block(f, fx + 20, by, fw - 40, 92, name, note, c, size=24)
        by += 100

    # SRAM panel
    sx, sy, sw, sh = 684, 138, 420, 520
    f.rect(sx, sy, sw, sh, color=BLUE_D, fill=PAPER, sw=3.0)
    f.htext(sx + 20, sy + 38, "SRAM · 0x2000_0000", size=29,
            color=BLUE_D, weight="bold")
    f.text(sx + 20, sy + 66, "掉电即失；上电瞬间内容不可信", size=20, color=RED)

    sblocks = [
        (".data", "已初始化变量的本体", AMBER_STROKE),
        (".bss", "零初始化；启动时清零", BLUE_D),
        ("heap ↑", "malloc 从这里向上长", BLUE_D),
        ("stack ↓", "局部变量与返回地址，向下长", RED),
    ]
    by = sy + 88
    for name, note, c in sblocks:
        _block(f, sx + 20, by, sw - 40, 92, name, note, c, size=24)
        by += 100

    # Reset_Handler: three moves between the panels
    cx, cy = 576, 400
    f.circle(cx, cy, 66, color=INK, sw=2.4, fill=WHITE)
    f.htext(cx, cy - 6, "Reset_", size=22, color=INK, anchor="middle",
            weight="bold")
    f.htext(cx, cy + 24, "Handler", size=22, color=INK, anchor="middle",
            weight="bold")
    f.text(cx, cy + 92, "main 之前跑完", size=19, color=MUTED,
           anchor="middle")

    # copy .data: Flash bottom block to SRAM top block
    f.arrow(fx + fw + 8, 600, sx - 8, 262, color=AMBER_STROKE, sw=3.0,
            bend=0.02)
    f.text(576, 250, "搬 .data", size=22, color=AMBER_STROKE,
           anchor="middle", weight="bold")
    f.text(576, 276, "Flash 初值 → RAM 本体", size=17, color=MUTED,
           anchor="middle")

    # zero .bss: from handler down-right
    f.arrow(cx + 66, cy + 18, sx - 8, 362, color=BLUE, sw=2.5, bend=0.12)
    f.text(576, 500, "清 .bss", size=20, color=BLUE, anchor="middle")

    # bottom truths
    f.htext(576, 700, ".data 有两个住址：LMA 在 Flash，VMA 在 RAM",
            size=28, color=AMBER_STROKE, anchor="middle", weight="bold",
            hl=True, hl_fill=AMBER_FILL)
    f.text(576, 744,
           "链接脚本 >RAM AT> FLASH 建立双重户籍；Reset_Handler 搬完、清完才进 main",
           size=22, color=INK, anchor="middle")
    return f


def cortex_4gb():
    f = Fig("arch-cortex-m-4gb", "Cortex-M 的 4GB 地址空间 / eight regions")

    rows = [
        ("0xE000_0000–0xFFFF_FFFF", "PPB",
         ["NVIC · SysTick · SCB", "CPUID 在 0xE000_ED00"], RED),
        ("0xA000_0000–0xDFFF_FFFF", "保留",
         ["跨两个 512 MB 区块，表里并成一行"], MUTED),
        ("0x8000_0000–0x9FFF_FFFF", "Device", ["外部设备"], MUTED),
        ("0x6000_0000–0x7FFF_FFFF", "RAM", ["外部 RAM，经 FSMC/FMC"], BLUE_D),
        ("0x4000_0000–0x5FFF_FFFF", "Peripheral", ["全部外设寄存器"], AMBER_STROKE),
        ("0x2000_0000–0x3FFF_FFFF", "SRAM",
         ["F407：128 KB 通用 + 64 KB CCM", "@0x1000_0000，仅 CPU 可达"], BLUE_D),
        ("0x0000_0000–0x1FFF_FFFF", "Code",
         ["F407 主 Flash @0x0800_0000", "0x0000_0000 是它的别名"], GREEN_D),
    ]

    x, y, w, h, gap = 92, 130, 968, 72, 8
    for i, (addr, name, notes, color) in enumerate(rows):
        yy = y + i * (h + gap)
        dash = "6 5" if name == "保留" else None
        f.rect(x, yy, w, h, color=color,
               fill=(PAPER if name == "保留" else WHITE),
               sw=2.2, dash=dash, double=(name != "保留"))
        f.htext(x + 16, yy + 31, addr, size=19, color=color, weight="bold")
        f.htext(x + 384, yy + 31, name, size=23, color=color, weight="bold")
        f.multi(x + 566, yy + 28, notes, size=18, color=INK, lh=23)

    # bottom truths
    f.text(x, 716, "段的边界由内核定；芯片厂商只在段内划房间。", size=23,
           color=INK)
    f.htext(x, 758, "CCM 在 0x1000_0000，只接 CPU：DMA 看不到这段地址。",
            size=22, color=RED, weight="bold", hl=True, hl_fill=AMBER_FILL)
    return f


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[2] / "assets" / "illustrations" / "handraw"
    save(linker_sections(), str(out / "arch-memory-map.svg"))
    save(cortex_4gb(), str(out / "arch-cortex-m-4gb.svg"))
    print("wrote arch-memory-map.svg, arch-cortex-m-4gb.svg")

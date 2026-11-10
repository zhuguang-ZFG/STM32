# -*- coding: utf-8 -*-
"""ch02 knowledge-track figure (facts from docs/02, RM0008 Rev 21 sec. 7.3.2).

The chapter gives the LATENCY bands (0-24 -> 0, 24-48 -> 1, 48-72 -> 2 wait
states, 2.7-3.6 V), says flash cannot keep up with 72 MHz so each fetch waits
two extra cycles, and warns that leaving LATENCY at 0 while switching the PLL
in makes the CPU read wrong instructions (runaway / HardFault). The order is
"write LATENCY = 2 first, then switch SYSCLK" (FLASH_ACR at 0x40022000+0x00,
LATENCY=010 for the 48-72 MHz step).
"""
from hd import *


def flash_fetch_wait():
    f = Fig("ch02-flash-fetch-wait",
            "等一拍：LATENCY 是取指的等待周期 / flash fetch wait states")

    # ---- 顶：三档 LATENCY 频段条 ----
    f.text(84, 132, "LATENCY 档位（2.7–3.6 V 供电）：", size=18, color=MUTED)
    bands = [(84, 300, "0–24 MHz", "等 0 拍 · LATENCY=0", GREEN_D),
             (416, 300, "24–48 MHz", "等 1 拍 · LATENCY=1", BLUE_D),
             (748, 316, "48–72 MHz", "等 2 拍 · LATENCY=2", RED)]
    for x, w, freq, wait, col in bands:
        f.rect(x, 146, w, 64, color=col, fill=WHITE, sw=2.4)
        f.text(x + 16, 174, freq, size=20, color=col, weight="bold")
        f.text(x + 16, 198, wait, size=17, color=INK)

    # ---- 中：两条取指时序道（4 拍对比）----
    f.text(84, 260, "① HSI 8 MHz（复位默认，0–24 档）：LATENCY=0，每拍交得出一条指令",
           size=20, color=GREEN_D, weight="bold")
    f.text(84, 368, "② 72 MHz（48–72 档）：LATENCY=2，每次取指要多等两个周期",
           size=20, color=RED, weight="bold")

    colx = [84, 328, 572, 816]
    cw = 220
    # 道 1：每拍取 ⇒ 得
    for x in colx:
        f.rect(x, 274, cw, 46, color=GREEN_D, fill=WHITE, sw=2.2)
        f.text(x + cw / 2, 303, "取 ⇒ 得", size=19, color=GREEN_D,
               anchor="middle", weight="bold")
    # 道 2：第 1 拍发取指，第 2、3 拍等，第 4 拍到手
    f.rect(colx[0], 382, cw, 46, color=RED, fill=WHITE, sw=2.2)
    f.text(colx[0] + cw / 2, 411, "发取指", size=19, color=RED,
           anchor="middle", weight="bold")
    f.fillrect(334, 388, 452, 34, AMBER_FILL, r=6)
    f.rect(328, 382, 464, 46, color=AMBER_STROKE, fill=None, sw=2.2,
           dash="6 6")
    f.text(560, 411, "等 2 拍——闪存还没交货", size=18, color=INK,
           anchor="middle", weight="bold")
    f.rect(colx[3], 382, cw, 46, color=GREEN_D, fill=WHITE, sw=2.4)
    f.text(colx[3] + cw / 2, 411, "到手", size=20, color=GREEN_D,
           anchor="middle", weight="bold")

    for i, x in enumerate(colx):
        f.text(x + cw / 2, 452, f"第 {i + 1} 拍", size=17, color=MUTED,
               anchor="middle")
    f.text(84, 482, "第 4 拍里：8 MHz 交到了第 4 条指令，72 MHz 才刚交到第 1 条",
           size=18, color=MUTED)

    # ---- 下：错误顺序 vs 正确顺序 ----
    f.rect(84, 506, 470, 112, color=RED, fill=WHITE, sw=2.4)
    f.text(100, 538, "翻车：只改 PLL，不改等待", size=21, color=RED,
           weight="bold")
    f.multi(100, 568, ["LATENCY 还留在 0 就切到 72 MHz",
                       "CPU 读到错的指令 → 跑飞或 HardFault"],
            size=17, color=INK, lh=26)

    f.rect(578, 506, 486, 112, color=GREEN_D, fill=WHITE, sw=2.4)
    f.text(594, 538, "对：先写等待，再切时钟", size=21, color=GREEN_D,
           weight="bold")
    f.multi(594, 568, ["先写 FLASH_ACR：LATENCY = 010（2 拍）",
                       "再 SW=10 切到 PLL，SWS 读回 10"],
            size=17, color=INK, lh=26)

    # ---- 底：寄存器与口诀 ----
    f.rect(84, 644, 980, 58, color=MUTED, fill=WHITE, sw=2.2)
    f.text(100, 680, "48 MHz 到 72 MHz 这一档写 LATENCY=2；换主频就要重查等待"
                     "——别人的主频数字，不能抄进你的工程",
           size=18, color=INK)

    f.htext(84, 744, "口诀：先写等待，再切 SW；升频先加拍，降频后减拍", size=24,
            color=INK, weight="bold", hl=True)
    return f


def flash_latency_ladder():
    f = Fig("ch02-flash-latency",
            "LATENCY 档位：先把等待周期加上，再切 SYSCLK（2.7–3.6 V）")
    f.text(84, 118, "闪存跟不上 72 MHz：每个档位先查供电电压，再查 SYSCLK 落在哪一档",
           size=21, color=MUTED)
    bands = [
        ("0 – 24 MHz", "LATENCY = 0", "0 个等待周期", GREEN_D),
        ("24 – 48 MHz", "LATENCY = 1", "1 个等待周期", AMBER_STROKE),
        ("48 – 72 MHz", "LATENCY = 2（010）", "2 个等待周期", RED),
    ]
    y = 165
    for band, lat, wait, c in bands:
        f.rect(84, y, 980, 88, color=c, fill=WHITE, sw=2.6)
        f.text(112, y + 36, band, size=25, color=INK, weight="bold")
        f.text(480, y + 36, lat, size=25, color=c, weight="bold")
        f.text(480, y + 68, wait, size=19, color=MUTED)
        y += 108
    f.rect(84, y + 12, 980, 92, color=RED, fill=WHITE, sw=2.6)
    f.text(112, y + 48, "顺序反了就是事故：只把 PLL 改成 ×9、LATENCY 还留在 0，",
           size=21, color=RED, weight="bold")
    f.text(112, y + 80, "CPU 读到错的指令——程序跑飞或进 HardFault。先写 2，再切时钟。",
           size=21, color=RED)
    return f


def part_number_decode():
    f = Fig("ch02-part-number-decode",
            "STM32F103C8T6：七段料号逐段解码 / part number, decoded")
    segs = [
        ("STM32", "品牌", 120),
        ("F", "系列", 90),
        ("103", "子系列 增强型", 140),
        ("C", "引脚 48", 105),
        ("8", "Flash 64 KB", 125),
        ("T", "封装 LQFP", 115),
        ("6", "温度 −40~85℃", 145),
    ]
    x = 84
    y = 200
    for i, (s, m, w) in enumerate(segs):
        c = (GREEN_D, BLUE_D, AMBER_STROKE, RED, GREEN_D, BLUE_D, AMBER_STROKE)[i]
        f.rect(x, y, w, 76, color=c, fill=WHITE, sw=2.6)
        f.htext(x + w / 2, y + 46, s, size=27, color=c, anchor="middle",
                weight="bold")
        f.text(x + 2, y + 108 + (34 if i % 2 else 0), m, size=17, color=INK)
        x += w + 10
    f.rect(84, 396, 980, 70, color=INK, fill=WHITE, sw=2.2)
    f.htext(W / 2, 433, "C8 = 48 脚 · 64 KB Flash · LQFP · −40~85℃",
            size=24, color=INK, anchor="middle", weight="bold", hl=True)
    f.text(84, 508, "后缀 A 属订购代码：采购按数据手册完整料号核对，不靠猜。",
           size=20, color=MUTED)
    return f


def part_funnel():
    f = Fig("ch02-part-funnel",
            "选型：先筛后用，再查完整订货号 / filter first, look up last")

    f.text(84, 130,
           "先用封装、存储器和外设排除不合适的料号，再按手册中的时钟树逐级计算",
           size=21, color=MUTED)

    # ---- 左：需求 ----
    f.rect(84, 160, 280, 430, color=GREEN_D, fill=WHITE, sw=2.6)
    f.text(104, 196, "需求先写清", size=23, color=GREEN_D, weight="bold")
    f.multi(104, 238, [
        "① 要几个引脚？",
        "② 多大 Flash / RAM？",
        "③ 要哪些外设？",
        "    USB / CAN / ADC / TIM",
        "④ 主频要多快？",
        "⑤ 什么温度等级？",
    ], size=18, color=INK, lh=38)
    f.text(104, 528, "问题越具体，筛得越快", size=17, color=MUTED)
    f.text(104, 558, "同一系列也可能容量、", size=17, color=RED)
    f.text(104, 580, "引脚、时钟都不同", size=17, color=RED, weight="bold")

    # ---- 中：三把筛子 ----
    sieves = [
        (160, "① 封装与引脚", BLUE_D,
         ["T=36 · C=48 · R=64 · V=100 · Z=144", "脚数不够，后面的都免谈"]),
        (300, "② 存储器", GREEN_D,
         ["4=16K · 6=32K · 8=64K · B=128K", "C=256K · E=512K · G=1M"]),
        (440, "③ 外设与主频", AMBER_STROKE,
         ["USB / CAN / ADC 在不在？", "103 = 72 MHz，带 USB 和 CAN"]),
    ]
    for y, name, col, lines in sieves:
        f.rect(408, y, 340, 124, color=col, fill=WHITE, sw=2.6)
        f.text(426, y + 34, name, size=21, color=col, weight="bold")
        f.multi(426, y + 68, lines, size=16, color=INK, lh=30)
    f.arrow(368, 260, 404, 220, color=MUTED, sw=2.2, bend=0.0)
    f.arrow(368, 360, 404, 360, color=MUTED, sw=2.2, bend=0.0)
    f.arrow(368, 460, 404, 500, color=MUTED, sw=2.2, bend=0.0)

    # ---- 右：剩下的才查手册 ----
    f.rect(792, 160, 276, 404, color=RED, fill=WHITE, sw=2.6)
    f.text(812, 196, "剩下的才查手册", size=22, color=RED, weight="bold")
    f.text(812, 240, "候选：STM32F103C8T6", size=18, color=INK,
           weight="bold")
    f.multi(812, 276, [
        "48 脚 · 64 KB Flash",
        "LQFP 封装",
        "−40 ~ 85 °C",
    ], size=17, color=INK, lh=30)
    f.text(812, 388, "完整订货号以", size=17, color=MUTED)
    f.text(812, 412, "数据手册为准，", size=17, color=MUTED)
    f.text(812, 436, "不确定的字段不猜", size=17, color=MUTED)
    f.arrow(752, 362, 788, 362, color=MUTED, sw=2.2, bend=0.0)

    f.rect(84, 612, 984, 56, color=AMBER_STROKE, fill=WHITE, sw=2.2)
    f.text(104, 648,
           "筛子问的是「够不够用」，数据手册回答「到底是哪一颗」",
           size=20, color=INK, weight="bold")

    f.htext(84, 724, "口诀：封装、存储、外设先过筛——最后才逐字对订货号",
            size=22, color=INK, weight="bold", hl=True)
    return f


def clock_gate():
    f = Fig("ch02-clock-gate",
            "先开时钟，再摸寄存器 / gate first, then init")

    f.text(84, 130,
           "任何外设第一次写寄存器之前，都要先 __HAL_RCC_*_CLK_ENABLE()",
           size=21, color=MUTED)

    # ---- 左：门关 vs 门开 ----
    f.rect(84, 160, 600, 330, color=INK, fill=WHITE, sw=2.4)
    # 门关
    f.rect(104, 190, 260, 270, color=MUTED, fill=GRAY_FILL, sw=2.2)
    f.text(234, 224, "门关：没开 CLK_ENABLE", size=19, color=MUTED,
           anchor="middle", weight="bold")
    f.rect(144, 246, 180, 64, color=MUTED, fill=WHITE, sw=2.0)
    f.text(234, 286, "外设（GPIO/I2C/…）", size=16, color=MUTED,
           anchor="middle")
    f.line(234, 310, 234, 350, color=MUTED, sw=2.2)
    f.line(214, 330, 254, 370, color=RED, sw=3.0)
    f.line(254, 330, 214, 370, color=RED, sw=3.0)
    f.rect(144, 370, 180, 56, color=MUTED, fill=WHITE, sw=2.0)
    f.text(234, 404, "RCC 时钟门（关）", size=16, color=MUTED,
           anchor="middle")
    f.text(234, 448, "读回 0，写入像写进虚空", size=16, color=RED,
           anchor="middle", weight="bold")
    # 门开
    f.rect(436, 190, 228, 270, color=GREEN_D, fill=WHITE, sw=2.2)
    f.text(550, 224, "门开：先 CLK_ENABLE", size=19, color=GREEN_D,
           anchor="middle", weight="bold")
    f.rect(448, 246, 204, 64, color=GREEN_D, fill=WHITE, sw=2.0)
    f.text(550, 286, "外设正常工作", size=16, color=INK, anchor="middle")
    f.line(550, 310, 550, 350, color=GREEN_D, sw=2.2)
    f.rect(448, 370, 204, 56, color=GREEN_D, fill=WHITE, sw=2.0)
    f.text(550, 404, "RCC 时钟门（开）", size=16, color=GREEN_D,
           anchor="middle")
    f.text(550, 448, "读写才有意义", size=16, color=GREEN_D,
           anchor="middle", weight="bold")

    # ---- 右：上电顺序 ----
    f.rect(716, 160, 352, 330, color=BLUE_D, fill=WHITE, sw=2.4)
    f.text(736, 196, "上电顺序", size=22, color=BLUE_D, weight="bold")
    steps = [
        ("① __HAL_RCC_*_CLK_ENABLE()", "先把门打开", BLUE_D),
        ("② HAL_xxx_Init()", "再初始化外设", GREEN_D),
        ("③ 读写寄存器", "这时才有意义", AMBER_STROKE),
    ]
    for i, (head, note, col) in enumerate(steps):
        y = 222 + i * 86
        f.rect(736, y, 312, 66, color=col, fill=WHITE, sw=2.2)
        f.text(752, y + 28, head, size=17, color=col, weight="bold")
        f.text(752, y + 54, note, size=16, color=MUTED)
        if i < 2:
            f.arrow(892, y + 68, 892, y + 84, color=MUTED, sw=2.0,
                    bend=0.0)
    f.text(736, 480, "顺序反了，Init 写的是关着的门", size=16, color=RED,
           anchor="start")

    f.rect(84, 520, 984, 104, color=AMBER_STROKE, fill=WHITE, sw=2.2)
    f.text(104, 556,
           "上电默认是 HSI 8 MHz，不是 Cube 配置页上的 72 MHz",
           size=19, color=INK, weight="bold")
    f.text(104, 590,
           "SystemClock_Config() 没运行到位时，先读 SWS——不要用串口输出反推主频",
           size=18, color=INK)

    f.htext(84, 700, "口诀：门不开，外设就不存在——先开时钟，再摸寄存器",
            size=22, color=INK, weight="bold", hl=True)
    return f


FIGS = {
    "ch02-flash-fetch-wait": flash_fetch_wait,
    "ch02-flash-latency": flash_latency_ladder,
    "ch02-part-number-decode": part_number_decode,
    "ch02-part-funnel": part_funnel,
    "ch02-clock-gate": clock_gate,
}

if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        f = FIGS[n]()
        OUT.mkdir(parents=True, exist_ok=True)
        save(f, str(OUT / (n + ".svg")))
        print("wrote", OUT / (n + ".svg"))

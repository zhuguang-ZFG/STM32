# -*- coding: utf-8 -*-
"""Hand-drawn plates for V1a (ch08 clock tree, ch10 EXTI/NVIC path).

Facts are pinned to the two chapters: ch08 uses 8MHz HSE / 16MHz HSI,
M=8 N=336 P=2 Q=7, VCO 336MHz, SYSCLK 168MHz, AHB 168MHz, APB1 42MHz,
APB2 84MHz, GPIOA 0x4002_0000 and PLLCFGR 0x07405408; ch10 uses PF6 ->
EXTI6 -> EXTI9_5 (IRQn 23, vector slot 39, offset 0x009C, ISER[0] bit23,
IP byte 0xE000E417), EXTI/SYSCFG bases, priority 5 -> 0x50 and AIRCR
0x05FA0500. No new measurements.

Deterministic: hd.Fig seeds its own RNG; re-running gives the same SVG.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hd import (AMBER_FILL, AMBER_STROKE, BLUE, BLUE_D, GREEN_D, INK, MUTED,  # noqa: E402
                RED, WHITE, Fig, save)

STAGE = Path(__file__).resolve().parents[2] / ".temp" / "l0-l5-pass" / "figures"


def _box(f, x, y, w, h, color, title, lines, title_size=19, line_size=14.5,
         fill=WHITE):
    f.rect(x, y, w, h, color=color, fill=fill, sw=2.4)
    f.text(x + 16, y + 32, title, size=title_size, color=color, weight="bold")
    for i, ln in enumerate(lines):
        f.text(x + 16, y + 62 + i * 25, ln, size=line_size, color=INK)


def ch08_clock_tree_path():
    f = Fig("ch08-clock-tree-path", "时钟树一条路：晶振到外设地址")
    f.text(56, 126,
           "8MHz 晶振或复位默认的 HSI 16MHz，经 PLL 与总线分频，最后落到一个外设寄存器地址。",
           size=16, color=MUTED)

    # sources
    _box(f, 56, 186, 196, 74, GREEN_D, "HSE 8MHz",
         ["外部晶振；SRC=1"], title_size=20, line_size=14)
    _box(f, 56, 286, 196, 74, BLUE_D, "HSI 16MHz",
         ["复位默认；SRC=0"], title_size=20, line_size=14)

    # PLL
    f.rect(306, 170, 316, 204, color=BLUE_D, fill=WHITE, sw=2.6)
    f.text(326, 204, "PLL：fVCO = 输入 × N / M", size=17, color=BLUE_D,
           weight="bold")
    f.multi(326, 238, [
        "M = 8    N = 336",
        "P = 2    Q = 7",
        "VCO = 1MHz × 336 = 336MHz",
        "SYSCLK = 336MHz ÷ 2 = 168MHz",
        "USB = 336MHz ÷ 7 = 48MHz",
    ], size=15.5, color=INK, lh=26)

    # SYSCLK
    f.rect(690, 196, 250, 120, color=AMBER_STROKE, fill=WHITE, sw=2.6)
    f.text(706, 232, "SYSCLK 168MHz", size=20, color=AMBER_STROKE,
           weight="bold")
    f.text(706, 262, "SW = 10b 切到 PLL", size=15, color=INK)
    f.text(706, 290, "读 SWS 确认已切换", size=15, color=INK)

    # source -> PLL -> SYSCLK
    f.arrow(256, 223, 300, 250, color=INK, sw=2.2, bend=0.0)
    f.arrow(256, 323, 300, 300, color=INK, sw=2.2, bend=0.0)
    f.arrow(626, 270, 686, 256, color=INK, sw=2.2, bend=0.0)

    # bus distribution bar
    f.text(270, 412, "分频控制：HPRE / PPRE1 / PPRE2", size=13.5, color=MUTED)
    f.line(815, 318, 815, 384, color=INK, sw=2.2, amp=1.0)
    f.line(250, 384, 890, 384, color=INK, sw=2.2, amp=1.0)
    for cx in (250, 570, 890):
        f.arrow(cx, 386, cx, 426, color=INK, sw=2.2, bend=0.0)

    # bus dividers
    _box(f, 110, 430, 280, 100, GREEN_D, "AHB ÷1 → HCLK 168MHz",
         ["GPIO / RCC / DMA"], title_size=17, line_size=14)
    _box(f, 430, 430, 280, 100, BLUE_D, "APB1 ÷4 → 42MHz",
         ["硬件上限 42MHz"], title_size=17, line_size=14)
    _box(f, 750, 430, 280, 100, AMBER_STROKE, "APB2 ÷2 → 84MHz",
         ["硬件上限 84MHz"], title_size=17, line_size=14)

    # one peripheral address
    f.arrow(250, 532, 250, 586, color=INK, sw=2.4, bend=0.0)
    f.panel(110, 590, 520, 116, AMBER_FILL)
    f.rect(110, 590, 520, 116, color=AMBER_STROKE, fill=None, sw=2.6,
           double=False)
    f.text(126, 622, "GPIOA->MODER = 0x4002_0000", size=19, color=INK,
           weight="bold", font="'Consolas','Courier New',monospace")
    f.text(126, 654, "AHB1 段基址 0x4002_0000 + 偏移 0x00", size=15,
           color=INK)
    f.text(126, 684, "每口隔 0x400：GPIOF = 0x4002_1400", size=15, color=INK)

    # side notes
    f.rect(670, 590, 420, 116, color=BLUE_D, fill=WHITE, sw=2.4)
    f.text(686, 620, "APB 分频 ≠ 1：定时器时钟 ×2", size=16, color=BLUE_D,
           weight="bold")
    f.text(686, 650, "TIM2 = 42MHz × 2 = 84MHz", size=15, color=INK)
    f.text(686, 678, "回读：168 / 168 / 42 / 84 / 84 MHz", size=15, color=INK)

    # order strip
    f.panel(56, 724, 1034, 44, WHITE)
    f.rect(56, 724, 1034, 44, color=MUTED, fill=None, sw=2.2, double=False)
    f.text(72, 753,
           "顺序：VOS=1 → 5WS → HSEON → PLLON → SW=10b → HPRE/PPRE；SWS 回读才算切换。",
           size=15, color=INK)
    return f


def ch10_exti_nvic_path():
    f = Fig("ch10-exti-nvic-path", "引脚到 ISR：四道门与优先级")
    f.text(56, 126,
           "边沿先变成 EXTI 请求，NVIC 按优先级放行，向量表给出 ISR 的入口。",
           size=16, color=MUTED)

    gates = [
        ("①", "SYSCFG", BLUE_D, [
            "EXTICR2[11:8] = 0x5",
            "PF6 → EXTI6",
            "基址 0x40013800",
            "先开 APB2 bit14 时钟",
        ]),
        ("②", "EXTI", AMBER_STROKE, [
            "IMR/RTSR/FTSR bit6",
            "PR bit6 挂起",
            "写 1 清（W1C）",
            "基址 0x40013C00",
        ]),
        ("③", "NVIC", GREEN_D, [
            "IRQn 23 → 向量槽 39",
            "ISER[0] bit23",
            "IP 字节 0xE000E417",
            "基址 0xE000E100",
        ]),
        ("④", "ISR", RED, [
            "EXTI9_5_IRQHandler",
            "槽 39 / 偏移 0x009C",
            "第一行清 PR",
            "名字错 → Default_Handler",
        ]),
    ]
    x = 56
    for i, (num, title, color, lines) in enumerate(gates):
        f.rect(x, 170, 244, 190, color=color, fill=WHITE, sw=2.4)
        f.circle(x + 30, 200, 16, color=color, sw=2.0)
        f.text(x + 30, 206, num, size=15, color=color, anchor="middle",
               weight="bold")
        f.text(x + 54, 207, title, size=19, color=color, weight="bold")
        for j, ln in enumerate(lines):
            f.text(x + 16, 246 + j * 27, ln, size=14, color=INK)
        if i < 3:
            f.arrow(x + 246, 265, x + 262, 265, color=INK, sw=2.2, bend=0.0)
        x += 264

    # priority encoding
    f.rect(56, 400, 500, 250, color=BLUE_D, fill=WHITE, sw=2.4)
    f.text(72, 434, "优先级：4 位字段，左移 4 位", size=19, color=BLUE_D,
           weight="bold")
    f.multi(72, 472, [
        "逻辑 5 → 存入 IP 字节 0x50",
        "逻辑 16 → 截断成 0x00（最高）",
        "AIRCR = 0x05FA0500：2 抢占 + 2 子",
        "写 AIRCR 必带 VECTKEY 0x5FA",
        "F407 只有 0~15 这 16 档",
    ], size=15, color=INK, lh=30)

    # preemption order
    f.rect(584, 400, 508, 250, color=GREEN_D, fill=WHITE, sw=2.4)
    f.text(600, 434, "抢占：谁能打断谁", size=19, color=GREEN_D,
           weight="bold")
    f.line(610, 464, 610, 566, color=GREEN_D, sw=1.8, amp=1.0)
    rows = [
        ("EXTI0（抢占 2）正在跑", INK),
        ("EXTI9_5（同级 2）挂起排队", INK),
        ("EXTI1（抢占号更小）立刻压栈换人", RED),
        ("ISR1 退出 → 回 EXTI0 → EXTI9 补位", INK),
    ]
    for i, (ln, color) in enumerate(rows):
        y = 470 + i * 32
        f.circle(610, y - 5, 5, color=color, sw=1.4)
        f.text(628, y, ln, size=15, color=color)
    f.text(600, 622, "子优先级只在同时挂起时排队，没有打断能力。",
           size=14, color=MUTED)

    # formula strip
    f.panel(56, 670, 1036, 76, AMBER_FILL)
    f.text(72, 704,
           "IRQn/32 = ISER 下标，IRQn%32 = 位号；IP 字节 = 0xE000E400 + IRQn。",
           size=17, color=INK, weight="bold")
    f.text(72, 732,
           "USART1：IRQn 37 → ISER[1] bit5、IP 0xE000E425；与槽号 IRQn + 16 一起对账。",
           size=15, color=MUTED)
    return f


PLATES = {
    "ch08-clock-tree-path": ch08_clock_tree_path,
    "ch10-exti-nvic-path": ch10_exti_nvic_path,
}


if __name__ == "__main__":
    names = sys.argv[1:] or list(PLATES)
    STAGE.mkdir(parents=True, exist_ok=True)
    for n in names:
        f = PLATES[n]()
        save(f, str(STAGE / (n + ".svg")))
        print("wrote", STAGE / (n + ".svg"))

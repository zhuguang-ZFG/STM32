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
from hd import (AMBER_FILL, AMBER_PALE, AMBER_STROKE, BLUE, BLUE_D,  # noqa: E402
                BLUE_FILL, GRAY_FILL, GREEN_D, GREEN_FILL, INK, MUTED, RED,
                RED_FILL, WHITE, Fig, save)

STAGE = Path(__file__).resolve().parents[2] / ".temp" / "l0-l5-pass" / "figures"
MONO = "'Consolas','Courier New',monospace"


def _box(f, x, y, w, h, color, title, lines, title_size=19, line_size=14.5,
         fill=WHITE):
    f.rect(x, y, w, h, color=color, fill=fill, sw=2.4)
    f.text(x + 16, y + 32, title, size=title_size, color=color, weight="bold")
    for i, ln in enumerate(lines):
        f.text(x + 16, y + 62 + i * 25, ln, size=line_size, color=INK)


def ch08_clock_tree_path():
    f = Fig("ch08-clock-tree-path", "时钟树一条路：晶振到外设地址",
            tag="CH 08 · 时钟与总线")
    f.text(64, 126,
           "晶振或 HSI 先过 PLL 变速箱，再沿三条总线分压，最后落到一个寄存器地址。",
           size=19, color=MUTED)

    # Two sources.
    f.card(64, 170, 220, 110, GREEN_D, fill=GREEN_FILL)
    f.rect(84, 194, 46, 26, color=GREEN_D, sw=2.0, fill=WHITE,
           double=False)
    f.line(84, 207, 130, 207, color=GREEN_D, sw=2.0)
    f.line(96, 184, 96, 230, color=GREEN_D, sw=2.0)
    f.line(118, 184, 118, 230, color=GREEN_D, sw=2.0)
    f.text(146, 206, "HSE", size=21, color=GREEN_D, weight="bold")
    f.text(146, 234, "8 MHz 晶振", size=16, color=INK)
    f.text(146, 260, "SRC = 1", size=14, color=MUTED)

    f.card(64, 300, 220, 100, BLUE_D, fill=BLUE_FILL)
    f.chip(84, 318, 46, 44, BLUE_D, size=12)
    f.text(146, 334, "HSI", size=21, color=BLUE_D, weight="bold")
    f.text(146, 362, "16 MHz，复位默认", size=15, color=INK)
    f.text(146, 388, "SRC = 0", size=14, color=MUTED)

    # PLL gearbox.
    f.card(320, 170, 340, 230, BLUE_D, fill=WHITE)
    f.gear(366, 214, 18, BLUE_D, teeth=8)
    f.gear(414, 236, 24, AMBER_STROKE, teeth=10)
    f.text(454, 206, "PLL 变速箱", size=22, color=BLUE_D, weight="bold")
    f.text(454, 234, "fVCO = 输入 × N / M", size=16, color=MUTED)
    f.text(342, 282, "M = 8", size=19, color=INK, weight="bold")
    f.text(432, 282, "N = 336", size=19, color=INK, weight="bold")
    f.text(540, 282, "P = 2", size=19, color=INK, weight="bold")
    f.text(342, 320, "VCO = 1 MHz × 336", size=17, color=INK)
    f.text(342, 348, "= 336 MHz", size=25, color=AMBER_STROKE, weight="bold")
    f.text(342, 382, "SYSCLK = 336 ÷ 2 = 168 MHz", size=17, color=GREEN_D,
           weight="bold")

    # SYSCLK gauge and USB tap.
    f.card(700, 170, 250, 150, AMBER_STROKE, fill=AMBER_PALE)
    f.clockface(748, 224, 32, AMBER_STROKE, hand=(-1, 2))
    f.text(796, 226, "168 MHz", size=28, color=AMBER_STROKE, weight="bold")
    f.text(796, 254, "SYSCLK", size=16, color=INK, weight="bold")
    f.text(720, 298, "SW = 10b 切到 PLL；SWS 回读确认", size=14, color=INK)

    f.card(974, 170, 114, 90, BLUE_D, fill=BLUE_FILL)
    f.text(1031, 204, "USB", size=19, color=BLUE_D, anchor="middle",
           weight="bold")
    f.text(1031, 232, "48 MHz", size=19, color=INK, anchor="middle")
    f.text(1031, 252, "Q = 7", size=13, color=MUTED, anchor="middle")

    # Source -> PLL -> SYSCLK.
    f.arrow(286, 222, 316, 236, color=GREEN_D, sw=2.2, bend=0.0)
    f.arrow(286, 350, 316, 330, color=BLUE_D, sw=2.2, bend=0.0)
    f.arrow(662, 270, 696, 250, color=AMBER_STROKE, sw=2.6, bend=0.0)
    f.arrow(952, 230, 972, 224, color=BLUE_D, sw=2.0, bend=0.0, head=8)

    # Main bus pipe: one trunk, three valves, three drops.
    f.line(825, 322, 825, 424, color=INK, sw=2.6, amp=0.8)
    f.line(214, 424, 906, 424, color=INK, sw=2.6, amp=0.8)
    for cx, label, color in ((214, "÷1", GREEN_D), (560, "÷4", BLUE_D),
                             (906, "÷2", AMBER_STROKE)):
        f.circle(cx, 424, 15, color=color, sw=1.8, fill=WHITE)
        f.text(cx, 430, label, size=13, color=color, anchor="middle",
               weight="bold")
        f.arrow(cx, 440, cx, 456, color=color, sw=2.4, bend=0.0)

    # Three bus cards.
    f.card(64, 460, 296, 136, GREEN_D, fill=GREEN_FILL)
    f.text(84, 494, "AHB ÷1 · HPRE", size=21, color=GREEN_D, weight="bold")
    f.text(84, 526, "HCLK 168 MHz", size=20, color=INK, weight="bold")
    f.text(84, 556, "GPIO / RCC / DMA", size=16, color=INK)

    f.card(400, 460, 296, 136, BLUE_D, fill=BLUE_FILL)
    f.text(420, 494, "APB1 ÷4 · PPRE1", size=21, color=BLUE_D, weight="bold")
    f.text(420, 526, "42 MHz", size=20, color=INK, weight="bold")
    f.text(420, 556, "硬件上限 42 MHz", size=16, color=INK)

    f.card(736, 460, 296, 136, AMBER_STROKE, fill=AMBER_PALE)
    f.text(756, 494, "APB2 ÷2 · PPRE2", size=21, color=AMBER_STROKE,
           weight="bold")
    f.text(756, 526, "84 MHz", size=20, color=INK, weight="bold")
    f.text(756, 556, "硬件上限 84 MHz", size=16, color=INK)

    # Landing point: one real register, plus the timer x2 rule.
    f.arrow(214, 598, 214, 626, color=GREEN_D, sw=2.4, bend=0.0)
    f.card(64, 630, 480, 88, AMBER_STROKE, fill=WHITE)
    f.text(84, 662, "GPIOA->MODER = 0x4002_0000", size=20, color=INK,
           weight="bold")
    f.text(84, 690, "AHB1 段基址 + 偏移 0x00；GPIOF = 0x4002_1400",
           size=15, color=MUTED)

    f.card(564, 630, 480, 88, BLUE_D, fill=WHITE)
    f.text(584, 660, "APB 分频 ≠ 1：定时器时钟 ×2", size=18, color=BLUE_D,
           weight="bold")
    f.text(584, 690, "TIM2 = 42 MHz × 2 = 84 MHz；回读 168 / 42 / 84",
           size=15, color=INK)

    # Order strip.
    f.panel(64, 736, 1024, 32, WHITE, amp=1.0)
    f.rect(64, 736, 1024, 32, color=MUTED, sw=1.8, fill=None, double=False,
           amp=1.0)
    f.text(80, 758,
           "顺序：VOS=1 → 5WS → HSEON → PLLON → SW=10b → HPRE/PPRE；SWS 回读才算切换。",
           size=14.5, color=INK)
    return f


def ch10_exti_nvic_path():
    f = Fig("ch10-exti-nvic-path", "引脚到 ISR：四道门与优先级",
            tag="CH 10 · 中断与 EXTI")
    f.text(64, 126,
           "PF6 的一个边沿，要走完四道门才变成 ISR；优先级决定谁能在半路插队。",
           size=19, color=MUTED)

    # A pulse leaves the pin and passes four gates.
    f.chip(64, 166, 58, 54, GREEN_D, size=13)
    f.text(93, 242, "PF6", size=16, color=GREEN_D, anchor="middle",
           weight="bold")
    f.line(93, 256, 93, 280, color=GREEN_D, sw=2.4)
    f.arrow(93, 280, 93, 306, color=GREEN_D, sw=2.4, bend=0.0)
    f.text(120, 292, "边沿", size=14, color=MUTED)

    gates = [
        ("1", "SYSCFG", BLUE_D, BLUE_FILL, [
            "EXTICR2[11:8] = 0x5",
            "PF6 → EXTI6",
            "基址 0x40013800",
        ]),
        ("2", "EXTI", AMBER_STROKE, AMBER_PALE, [
            "IMR / RTSR / FTSR bit6",
            "PR bit6 挂起，写 1 清",
            "基址 0x40013C00",
        ]),
        ("3", "NVIC", GREEN_D, GREEN_FILL, [
            "IRQn 23 → 向量槽 39",
            "ISER[0] bit23",
            "IP 字节 0xE000E417",
        ]),
        ("4", "ISR", RED, RED_FILL, [
            "EXTI9_5_IRQHandler",
            "槽 39 / 偏移 0x009C",
            "第一行清 PR",
        ]),
    ]
    x = 64
    for i, (num, title, color, fill, lines) in enumerate(gates):
        f.card(x, 318, 236, 178, color, fill=fill)
        f.gate(x + 14, 330, 50, 64, color, num)
        f.text(x + 20, 432, title, size=23, color=color, weight="bold")
        for j, ln in enumerate(lines):
            f.text(x + 20, 462 + j * 25, ln, size=15, color=INK)
        if i < 3:
            f.arrow(x + 238, 400, x + 258, 400, color=INK, sw=2.2,
                    bend=0.0, head=8)
        x += 256

    # Priority is a 4-bit field shifted into the IP byte.
    f.card(64, 516, 482, 190, BLUE_D, fill=WHITE)
    f.text(84, 550, "优先级：4 位字段，左移 4 位", size=21, color=BLUE_D,
           weight="bold")
    f.pill(84, 572, 122, 36, "逻辑 5", BLUE_D, fill=BLUE_FILL, size=16)
    f.arrow(210, 590, 246, 590, color=BLUE_D, sw=2.0, bend=0.0, head=7)
    f.pill(250, 572, 140, 36, "IP = 0x50", BLUE_D, fill=BLUE_FILL, size=16)
    f.text(84, 642, "逻辑 16 → 截断成 0x00（最高）", size=16, color=INK)
    f.text(84, 670, "AIRCR = 0x05FA0500：2 抢占 + 2 子", size=16, color=INK)
    f.text(84, 696, "写 AIRCR 必带 VECTKEY 0x5FA", size=15, color=MUTED)

    # Preemption: lower preempt number cuts the line; equal number queues.
    f.card(574, 516, 514, 190, GREEN_D, fill=WHITE)
    f.text(594, 550, "抢占：谁打断谁", size=21, color=GREEN_D,
           weight="bold")
    f.pill(594, 572, 204, 38, "EXTI0 · 抢占 2", GREEN_D, fill=GREEN_FILL,
           size=15)
    f.pill(594, 620, 204, 38, "EXTI9_5 · 同级 2", GREEN_D, fill=GREEN_FILL,
           size=15)
    f.pill(814, 572, 236, 38, "EXTI1 · 抢占 1", RED, fill=RED_FILL,
           size=15)
    f.arrow(812, 632, 812, 596, color=RED, sw=2.4, bend=0.0, head=8)
    f.text(820, 652, "号更小 → 立刻压栈换人", size=15, color=RED,
           weight="bold")
    f.text(594, 688, "同级只在同时挂起时排队，不能打断。", size=15,
           color=MUTED)

    # Formula strip: two short lines beat one clipped line.
    f.panel(64, 716, 1024, 54, AMBER_FILL, amp=1.2)
    f.text(80, 740,
           "IRQn/32 = ISER 下标；IRQn%32 = 位号；IP = 0xE000E400 + IRQn。",
           size=15.5, color=INK, weight="bold")
    f.text(80, 762,
           "USART1：IRQn 37 → ISER[1] bit5、IP 0xE000E425；槽号 = IRQn + 16。",
           size=14.5, color=MUTED)
    return f


def ch10_prio_four_bit_window():
    """4-bit priority window: left-shift 4, write-16 traps, 0x5FA key,
    PRIGROUP split. Facts from ch10 (stm32f407xx.h:49, core_cm4.h:1661)."""
    f = Fig("ch10-prio-four-bit-window",
            "4 位优先级窗口：写 16 变最高",
            title_color=RED, tag="CH 10 · NVIC")
    f.text(64, 126,
           "IP 字节只实现了高 4 位：越界不报错、不换字节，只在本字节截断，嵌套关系悄悄反掉。",
           size=19, color=MUTED)

    # ---- left: encoding ladder ----
    f.card(64, 156, 380, 330, BLUE_D, fill=BLUE_FILL)
    f.text(84, 188, "NVIC_PRIO_BITS = 4", size=18, color=BLUE_D,
           weight="bold", font=MONO)
    f.text(84, 212, "stm32f407xx.h:49 · 只用高 4 位", size=13, color=MUTED)
    enc = [("逻辑 5", "0x50"), ("逻辑 10", "0xA0"), ("逻辑 15", "0xF0")]
    for i, (lv, byte) in enumerate(enc):
        y = 244 + i * 44
        f.text(84, y, lv, size=15, color=INK)
        f.pill(210, y - 26, 120, 36, byte, BLUE_D, fill=WHITE, size=16,
               text_color=INK)
    f.text(84, 396, "存入值 = 逻辑优先级左移 4 位，低 4 位恒 0", size=14.5,
           color=INK)
    f.text(84, 424, "F407 上只有 0~15 这 16 档", size=14.5, color=MUTED)
    f.text(84, 456, "API 收 0~255，窗口只有 4 位", size=14, color=MUTED)

    # ---- middle: the truncate table (the trap) ----
    f.card(468, 156, 330, 330, RED, fill=RED_FILL)
    f.text(488, 188, "写越界的下场", size=19, color=RED, weight="bold")
    rows = [("16", "0x00", "0（最高！）"), ("17", "0x10", "1"),
            ("20", "0x40", "4"), ("255", "0xF0", "15"),
            ("256", "0x00", "0")]
    for i, (w_in, byte, back) in enumerate(rows):
        y = 226 + i * 40
        f.text(488, y, w_in, size=15, color=INK, font=MONO)
        f.text(556, y, "→", size=14, color=MUTED)
        f.text(596, y, byte, size=15, color=RED, weight="bold", font=MONO)
        f.text(676, y, back, size=14,
               color=RED if i in (0, 4) else MUTED,
               weight="bold" if i in (0, 4) else "normal")
    f.text(488, 440, "想给 16（最低），芯片收到 0（最高）", size=14.5,
           color=RED, weight="bold")
    f.text(488, 466, "程序照跑，只有嵌套悄悄反了", size=14, color=MUTED)

    # ---- right: AIRCR key + PRIGROUP ----
    f.card(822, 156, 266, 330, GREEN_D, fill=GREEN_FILL)
    f.text(842, 188, "SCB->AIRCR", size=18, color=GREEN_D, weight="bold",
           font=MONO)
    f.pill(842, 204, 226, 40, "VECTKEY 0x5FA", AMBER_STROKE, fill=WHITE,
           size=16)
    f.text(842, 272, "没钥匙：整个写被无视", size=13.5, color=RED)
    f.text(842, 298, "core_cm4.h:1661", size=12.5, color=MUTED)
    grp = [("0~3", "4 抢占+0 子"), ("4", "3+1"), ("5", "2+2"),
           ("6", "1+3"), ("7", "0+4")]
    for i, (g, split) in enumerate(grp):
        y = 326 + i * 30
        f.text(842, y, f"PRIGROUP {g}", size=13.5, color=INK, font=MONO)
        f.text(986, y, split, size=13.5, color=GREEN_D, weight="bold")
    f.text(842, 462, "FreeRTOS 要 4 位全给抢占", size=13.5, color=MUTED)

    # ---- bottom: fixed priorities ----
    f.panel(64, 516, 1024, 100, GRAY_FILL, amp=1.6)
    f.rect(64, 516, 1024, 100, color=MUTED, sw=1.6, fill=None, amp=1.6)
    f.text(88, 548, "三个设不了的：IRQn_Type 里 -13 被故意跳过（stm32f407xx.h:68-69）",
           size=15.5, color=INK, weight="bold")
    fixed = [("Reset -3", "最高"), ("NMI -2", "次之"), ("HardFault -1", "最低")]
    for i, (name, rank) in enumerate(fixed):
        x = 120 + i * 320
        f.text(x, 590, name, size=16, color=RED, weight="bold", font=MONO)
        f.text(x + 150, 590, rank, size=14, color=MUTED)
    f.text(936, 590, "硬件固定，SHP/IPR 都摸不到", size=13.5, color=MUTED)

    f.htext(64, 700, "危险的不是报错，是静默改写成另一个合法优先级",
            size=22, color=RED, weight="bold", hl=True)
    f.text(576, 730,
           "编码表与分组表取自本章 S4 probe 记录；布局示意，非实测。",
           size=14, color=MUTED, anchor="middle")
    return f


def ch08_six_frequency_steps():
    """The six register steps from 16 MHz reset to 168 MHz, in order.
    Facts from ch08 (RM0090 Rev 18 §7.2.3, probe record)."""
    f = Fig("ch08-six-frequency-steps",
            "提频六步：顺序错了全部重来",
            title_color=BLUE_D, tag="CH 08 · 时钟")
    f.text(64, 126,
           "复位后只有 HSI 16MHz；想跑 168MHz，六道手续一道不缺、一步不乱。",
           size=19, color=MUTED)

    steps = [
        ("① 电压档", "PWR_CR.VOS = 1（bit14）", "Scale 1 解锁 168MHz；F405/407 无就绪位，写入即生效",
         BLUE_D, BLUE_FILL),
        ("② Flash 等待", "FLASH_ACR.LATENCY = 5WS", "3.3V 下 168MHz 要 5WS；必须在提速之前，否则取指跑飞",
         AMBER_STROKE, AMBER_PALE),
        ("③ 开 HSE", "HSEON(bit16) → 等 HSERDY(bit17)", "晶振虚焊就不就绪——必须带超时回退 HSI，不能死等",
         GREEN_D, GREEN_FILL),
        ("④ 配 PLL 启动", "PLLCFGR = 0x07405408", "M8 N336 P/2 SRC=HSE Q7；PLLON → PLLRDY",
         BLUE_D, BLUE_FILL),
        ("⑤ 切 SYSCLK", "SW = 10b → 读 SWS 确认", "写完 SW 不等于已切换，SWS [3:2] 才是硬件回执",
         GREEN_D, GREEN_FILL),
        ("⑥ 总线分频", "HPRE /1 · PPRE1 /4 · PPRE2 /2", "PCLK1=42（上限）· PCLK2=84（上限）；APB÷≠1 时定时器 ×2",
         AMBER_STROKE, AMBER_PALE),
    ]
    pos = [(64, 156), (438, 156), (812, 156), (251, 330), (625, 330),
           (64, 504)]
    for (name, reg, note, c, fl), (x, y) in zip(steps, pos):
        f.card(x, y, 276, 156, c, fill=fl)
        f.text(x + 16, y + 32, name, size=19, color=c, weight="bold")
        f.text(x + 16, y + 62, reg, size=13.5, color=INK, font=MONO,
               weight="bold")
        wrap = note
        f.text(x + 16, y + 92, wrap[:22], size=12.5, color=MUTED)
        if len(wrap) > 22:
            f.text(x + 16, y + 112, wrap[22:44], size=12.5, color=MUTED)
        if len(wrap) > 44:
            f.text(x + 16, y + 132, wrap[44:66], size=12.5, color=MUTED)
    for x0, x1 in ((340, 438), (714, 812)):
        f.arrow(x0, 234, x1, 234, color=MUTED, sw=2.2, bend=0.0, head=8)
    f.arrow(527, 286, 560, 318, color=MUTED, sw=2.2, bend=0.0, head=8)
    f.arrow(901, 286, 780, 318, color=MUTED, sw=2.2, bend=0.0, head=8)
    f.arrow(400, 488, 332, 500, color=MUTED, sw=2.2, bend=0.0, head=8)

    # ---- HPRE caution ----
    f.panel(380, 504, 708, 100, RED_FILL, amp=1.6)
    f.rect(380, 504, 708, 100, color=RED, sw=1.8, fill=None, amp=1.6)
    f.text(404, 536, "RM0090 caution：HPRE 写入后 1~16 个 AHB 周期才生效",
           size=15, color=RED, weight="bold")
    f.text(404, 566, "升频前先把总线分频降下来，否则新频率瞬间喂给老分频总线；",
           size=14, color=INK)
    f.text(404, 590, "降频可以直接做", size=14, color=INK)

    f.htext(64, 700, "VOS 与 5WS 先行，HSERDY 要带超时回退，SWS 才是硬件回执",
            size=21, color=INK, weight="bold", hl=True)
    f.text(576, 730,
           "寄存器步骤取自本章 RM0090 §7.2.3 与探针记录；流程示意，非实测。",
           size=14, color=MUTED, anchor="middle")
    return f


PLATES = {
    "ch08-clock-tree-path": ch08_clock_tree_path,
    "ch08-six-frequency-steps": ch08_six_frequency_steps,
    "ch10-exti-nvic-path": ch10_exti_nvic_path,
    "ch10-prio-four-bit-window": ch10_prio_four_bit_window,
}


if __name__ == "__main__":
    names = sys.argv[1:] or list(PLATES)
    STAGE.mkdir(parents=True, exist_ok=True)
    for n in names:
        f = PLATES[n]()
        save(f, str(STAGE / (n + ".svg")))
        print("wrote", STAGE / (n + ".svg"))

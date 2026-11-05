#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Static key figures for the two sample chapters. No CSS animation and no SMIL."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from svgkit import Svg, T

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _credit(canvas: Svg, note: str) -> None:
    canvas.line(24, canvas.h - 36, canvas.w - 24, canvas.h - 36, stroke=T.GRID, sw=1)
    canvas.text(24, canvas.h - 16, note, size=11, fill=T.MUTED)
    canvas.text(canvas.w - 24, canvas.h - 16, "自绘 · 静态 · CC BY 4.0", size=11, fill=T.DIM, anchor="end")


def boot_state() -> Svg:
    canvas = Svg(
        960,
        620,
        "BOOT0=0 取到刚烧入的闪存；BOOT0=1 取到系统存储器",
        "STM32F103C8T6 · RM0008 Rev 21 §3.4 Table 9",
    )
    canvas.header(tag="00", tag_color=T.CYAN)
    canvas.text(40, 88, "正常路径  BOOT1=x  BOOT0=0", size=16, fill=T.GREEN, weight="700")
    steps = [
        (40, "main.c", "源文件"),
        (230, ".elf", "STM32F103C8Tx_FLASH.ld"),
        (460, "SWDIO / SWCLK", "写入 0x08000000"),
        (700, "0x00000000", "别名到主闪存"),
    ]
    for left, title, sub in steps:
        canvas.rect(left, 108, 180, 78, fill=T.PANEL, stroke=T.GREEN, rx=8)
        canvas.text(left + 12, 140, title, size=14, fill=T.TEXT, weight="700")
        canvas.text(left + 12, 164, sub, size=11, fill=T.MUTED)
    canvas.text(40, 214, "第 4 个 SYSCLK 上升沿锁存 BOOT 脚，然后 CPU 读 0x00000000 与 0x00000004", size=14, fill=T.TEXT)
    canvas.text(40, 268, "失败路径  BOOT1=0  BOOT0=1", size=16, fill=T.RED, weight="700")
    canvas.rect(40, 284, 880, 130, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(56, 316, "烧录仍然写在 0x08000000，程序还在闪存里", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 344, "CPU 从 0x00000000 取到的是系统存储器别名，不是这颗闪存", size=14, fill=T.AMBER)
    canvas.text(56, 370, "STM32F103C8T6 的系统存储器在 0x1FFFF000", size=14, fill=T.TEXT)
    canvas.text(56, 396, "互联型 0x1FFFB000 与 XL 密度 Bank2 的 0x08080000 对这颗料作废", size=13, fill=T.MUTED)
    canvas.rect(40, 434, 880, 110, fill=T.BG2, stroke=T.STROKE, rx=8)
    canvas.text(56, 466, "信号名", size=14, fill=T.CYAN, weight="700")
    canvas.text(56, 492, "SWDIO = PA13     SWCLK = PA14     BOOT0     BOOT1", size=15, fill=T.TEXT)
    canvas.text(56, 518, "退出 Standby 时 BOOT 脚会再采样一次", size=13, fill=T.MUTED)
    _credit(canvas, "自绘。地址与启动行来自 RM0008 Rev 21 第 3.4 节表 9。")
    return canvas


def gpio_led() -> Svg:
    canvas = Svg(
        960,
        660,
        "PA0 推挽可以点灯；PC13 不能当电流源",
        "STM32F103C8T6 LQFP48 · DS5319 Rev 20 Figure 8 / Table 5 / note 5",
    )
    canvas.header(tag="03", tag_color=T.AMBER)
    canvas.rect(40, 86, 420, 250, fill=T.PANEL, stroke=T.CYAN, rx=8)
    canvas.text(56, 116, "STM32F103C8T6  LQFP48", size=16, fill=T.TEXT, weight="700")
    canvas.rect(56, 140, 150, 40, fill=T.BG2, stroke=T.GREEN, rx=4)
    canvas.text(68, 166, "10   PA0-WKUP", size=14, fill=T.GREEN, weight="700")
    canvas.rect(56, 196, 190, 40, fill=T.BG2, stroke=T.RED, rx=4)
    canvas.text(68, 222, "2   PC13-TAMPER-RTC", size=14, fill=T.RED, weight="700")
    canvas.text(56, 270, "PA0 推挽写 1：电流从脚流出", size=13, fill=T.GREEN)
    canvas.text(56, 296, "PC13 走电源开关，禁止作电流源", size=13, fill=T.RED)
    canvas.text(460, 108, "正常路径", size=16, fill=T.GREEN, weight="700")
    canvas.rect(460, 124, 460, 160, fill=T.PANEL, stroke=T.GREEN, rx=8)
    canvas.text(476, 154, "PA0 第 10 脚", size=14, fill=T.TEXT, weight="700")
    canvas.text(476, 180, "3.3 V → 推挽 PMOS → 270 Ω → LED → GND", size=13, fill=T.CYAN)
    canvas.text(476, 206, "R = (3.3 − 2.0) / 0.005 = 260 Ω，取 270 Ω", size=13, fill=T.TEXT)
    canvas.text(476, 232, "高 500 ms，低 500 ms，合起来 1 Hz", size=13, fill=T.MUTED)
    canvas.text(476, 256, "周期来自 HAL_Delay(500)，不是速度位", size=12, fill=T.MUTED)
    canvas.text(460, 316, "失败路径", size=16, fill=T.RED, weight="700")
    canvas.rect(460, 332, 460, 150, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(476, 362, "PC13 第 2 脚", size=14, fill=T.TEXT, weight="700")
    canvas.text(476, 388, "把 PA0「写 1 点灯」原样搬过来", size=13, fill=T.AMBER)
    canvas.text(476, 414, "灌电流上限 3 mA，不能作电流源", size=13, fill=T.RED)
    canvas.text(476, 440, "速度 ≤ 2 MHz，负载 ≤ 30 pF", size=13, fill=T.TEXT)
    canvas.text(476, 464, "25 mA / 50 MHz 对 PC13–PC15 作废", size=12, fill=T.MUTED)
    canvas.rect(40, 360, 400, 200, fill=T.BG2, stroke=T.VIOLET, rx=8)
    canvas.text(56, 390, "GPIOx_LCKR  偏移 0x18", size=14, fill=T.VIOLET, weight="700")
    canvas.text(56, 420, "LCK[15:0] 在序列中保持不变", size=13, fill=T.TEXT)
    canvas.text(56, 446, "LCKK：写 1，写 0，写 1", size=13, fill=T.TEXT)
    canvas.text(56, 472, "读 LCKR，完成序列；再读确认 LCKK = 1", size=13, fill=T.TEXT)
    canvas.text(56, 498, "错一步，锁中止，配置仍可改", size=13, fill=T.AMBER)
    canvas.text(56, 528, "RM0008 Rev 21 §9.2.7", size=12, fill=T.MUTED)
    _credit(canvas, "自绘。脚位与 3 mA / 2 MHz / 30 pF 来自 DS5319 Rev 20。")
    return canvas


def exception_stack() -> Svg:
    canvas = Svg(
        960,
        780,
        "抢占 1 可以打断抢占 2；抢占同为 1 时后来的请求不能嵌套",
        "STM32F103C8T6 · NVIC_PRIORITYGROUP_4 · PM0056 §2.3.7",
    )
    canvas.header(tag="04", tag_color=T.CYAN)
    canvas.text(40, 86, "正常路径  GROUP_4", size=16, fill=T.GREEN, weight="700")
    canvas.rect(40, 100, 880, 250, fill=T.PANEL, stroke=T.GREEN, rx=8)
    canvas.text(56, 128, "TIM2 抢占 2 正在执行", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 154, "EXTI0  PA0 下降沿  EXTI0_IRQn  抢占 1  子优先级 0", size=14, fill=T.GREEN)
    canvas.text(56, 180, "硬件入栈 8 个寄存器，从高地址到低地址：", size=14, fill=T.TEXT)
    canvas.text(56, 206, "xPSR   PC   LR   R12   R3   R2   R1   R0", size=16, fill=T.CYAN, weight="700")
    canvas.text(56, 232, "入栈后的 SP 指向 R0", size=14, fill=T.TEXT)
    canvas.text(56, 258, "大约 12 个 HCLK，72 MHz 时 12 / 72e6 ≈ 167 ns，不含 ISR 正文", size=14, fill=T.AMBER)
    canvas.text(56, 284, "然后取向量、执行 ISR、出栈返回。清标志写 EXTI_PR", size=14, fill=T.MUTED)
    canvas.text(56, 316, "NVIC_PRIORITYGROUP_4：4 位抢占，0 位子优先级。数值越小，逻辑优先级越高。", size=13, fill=T.MUTED)
    canvas.text(56, 338, "TIM2_IRQn 抢占 2 被 EXTI0_IRQn 抢占 1 打断", size=13, fill=T.GREEN)
    canvas.text(40, 376, "失败路径  优先级写错，更高的请求进不来", size=16, fill=T.RED, weight="700")
    canvas.rect(40, 390, 880, 150, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(56, 418, "EXTI0 与 TIM2 的抢占都写成 1，子优先级仍写成 0 和 1", size=14, fill=T.TEXT, weight="700")
    canvas.text(56, 444, "子优先级不同也不嵌套。EXTI0 保持挂起，等正在执行的 ISR 退出", size=14, fill=T.AMBER)
    canvas.text(56, 470, "退出时可以尾链进去。没有发生第二次嵌套入栈", size=14, fill=T.RED)
    canvas.text(56, 496, "把 EXTI0 的抢占数值写成比 TIM2 更大，是出处卡的另一行，不在这张图上", size=13, fill=T.MUTED)
    canvas.text(56, 520, "STM32F103C8T6  ·  这一路径不是 NMI", size=13, fill=T.MUTED)
    canvas.rect(40, 560, 880, 120, fill=T.BG2, stroke=T.VIOLET, rx=8)
    canvas.text(56, 590, "PRIMASK = 1 时 EXTI0 和 TIM2 都进不来", size=15, fill=T.VIOLET, weight="700")
    canvas.text(56, 618, "NMI 仍然进入。不要把 NMI 画成被 NVIC 抢占字段挡住。", size=14, fill=T.TEXT)
    canvas.text(56, 646, "FAULTMASK 再挡住 HardFault，仍留 NMI。BASEPRI 只挡住数值大于等于阈值的那一截。", size=13, fill=T.MUTED)
    _credit(canvas, "自绘。入栈与 167 ns 沿用附录 D；寄存器名来自 PM0056 第 2.3.7 节，EXTI 来自 RM0008 Rev 21。")
    return canvas


def uart_frame() -> Svg:
    canvas = Svg(
        960,
        820,
        "停止位采到 0 就是帧错误；0x271 在 72 MHz、16 倍下误差是 0",
        "STM32F103C8T6 LQFP48 · RM0008 Rev 21 第 27 章",
    )
    canvas.header(tag="06", tag_color=T.CYAN)
    canvas.text(40, 86, "STM32F103C8T6  LQFP48  USART1  APB2  72 MHz", size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "第 30 脚 PA9 = USART1_TX     第 31 脚 PA10 = USART1_RX     空闲为高", size=14, fill=T.CYAN)
    canvas.text(40, 138, "0xA5  LSB 先发：起始位 0，数据 1 0 1 0 0 1 0 1，停止位 1", size=14, fill=T.TEXT)
    canvas.text(40, 164, "一位约 8.68 µs，10 位约 86.8 µs。BRR 0x271，16 倍，39.0625，误差 0", size=14, fill=T.AMBER)
    canvas.text(40, 190, "USART_SR 0x00    USART_DR 0x04    USART_BRR 0x08    USART_CR1 0x0C", size=14, fill=T.MUTED)
    labels = ["ST", "b0", "b1", "b2", "b3", "b4", "b5", "b6", "b7", "SP"]
    bits = ["0", "1", "0", "1", "0", "0", "1", "0", "1", "1"]
    for index, (label, bit) in enumerate(zip(labels, bits)):
        left = 40 + index * 90
        canvas.rect(left, 210, 80, 64, fill=T.PANEL, stroke=T.CYAN, rx=4)
        canvas.text(left + 8, 236, label, size=12, fill=T.MUTED)
        canvas.text(left + 8, 260, bit, size=18, fill=T.GREEN if bit == "1" else T.RED, weight="700")
    canvas.text(40, 300, "正常路径  停止位为高", size=16, fill=T.GREEN, weight="700")
    canvas.rect(40, 314, 880, 120, fill=T.PANEL, stroke=T.GREEN, rx=8)
    canvas.text(56, 344, "停止位上的第 8、第 9、第 10 个采样点表决为 1", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 370, "FE 不置位。数据位用中间那三个点。", size=14, fill=T.GREEN)
    canvas.text(56, 396, "起始位的确认序列是第 3、5、7 点和第 8、9、10 点。RM0008 27.3.3", size=13, fill=T.MUTED)
    canvas.text(40, 460, "失败路径  停止位三点采到 0", size=16, fill=T.RED, weight="700")
    canvas.rect(40, 474, 880, 130, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(56, 504, "第 8、9、10 点为 0，FE 置位，数据仍在 USART_DR", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 530, "清除顺序：先读 USART_SR，再读 USART_DR。只读 DR 清不掉。", size=14, fill=T.RED)
    canvas.text(56, 556, "中断是否到来还要看 RXNE 或 CR3 的 EIE。FE 本身不是唯一的中断源。", size=13, fill=T.AMBER)
    canvas.text(56, 582, "不要写成「FE 一定进中断服务」", size=13, fill=T.MUTED)
    canvas.rect(40, 624, 880, 100, fill=T.BG2, stroke=T.VIOLET, rx=8)
    canvas.text(56, 654, "旁注  OVER8 / 8 倍  不占帧错误那条路径", size=15, fill=T.VIOLET, weight="700")
    canvas.text(56, 680, "这颗 F103 的 USART_CR1 位 31:14 保留，没有这个位。", size=14, fill=T.TEXT)
    canvas.text(56, 706, "不在这张图上算 8 倍的 BRR。重映射的 PB6/PB7 不在正常路径上。", size=13, fill=T.MUTED)
    _credit(canvas, "自绘。脚位来自 DS5319 Rev 20 图 8；采样与 BRR 来自 RM0008 Rev 21 第 27 章。")
    return canvas


def clock_tree() -> Svg:
    canvas = Svg(
        960,
        860,
        "72 MHz 要 2 个 Flash 等待；HSE 停振后系统时钟回到 HSI 8 MHz",
        "STM32F103C8T6 LQFP48 · RM0008 Rev 21 第 7.3.2 节",
    )
    canvas.header(tag="02", tag_color=T.CYAN)
    canvas.text(40, 122, "先把树画出来，再读寄存器：每个箭头就是一个分频/倍频位", size=15, fill=T.TEXT, weight="700")

    # ---- 树主干 ----
    def node(x, y, w, h, l1, l2, c, fill=None):
        canvas.rect(x, y, w, h, fill=fill or T.BG, stroke=c, rx=4, sw=2)
        canvas.text(x + w / 2, y + 26, l1, size=14, fill=c, anchor="middle", weight="700")
        canvas.text(x + w / 2, y + 48, l2, size=11, fill=T.MUTED, anchor="middle")

    node(40, 160, 180, 62, "HSE 8 MHz", "pin 5 PD0 · pin 6 PD1", T.CYAN)
    canvas.arrow(222, 191, 262, 191, color=T.CYAN, sw=2, head=7)
    canvas.text(242, 176, "PLL ×9", size=12, fill=T.GREEN, anchor="middle", weight="700")
    canvas.text(244, 212, "0111", size=10, fill=T.MUTED, anchor="middle", mono=True)
    canvas.text(40, 240, "PLLXTPRE=0 · PLLSRC=1 · PLLMUL=0111：8 × 9 = 72 MHz，不是 8 × 8", size=12, fill=T.CYAN, mono=True)
    node(266, 160, 180, 62, "SYSCLK 72", "PLLSRC=1 HSE", T.GREEN)
    canvas.arrow(448, 191, 488, 191, color=T.GREEN, sw=2, head=7)
    node(492, 160, 170, 62, "HCLK 72", "AHB 不分频", T.GREEN)
    # Flash 等待
    canvas.rect(700, 150, 220, 84, fill=T.PANEL, stroke=T.GREEN, rx=4)
    canvas.text(810, 176, "Flash LATENCY=2", size=14, fill=T.GREEN, anchor="middle", weight="700")
    canvas.text(810, 198, "0–24:0   24–48:1", size=11, fill=T.MUTED, anchor="middle", mono=True)
    canvas.text(810, 216, "48–72:2（2.7–3.6 V）", size=11, fill=T.MUTED, anchor="middle", mono=True)
    canvas.line(662, 191, 700, 191, stroke=T.GREEN, sw=2)

    # APB1 / APB2 分支
    canvas.line(577, 222, 577, 262, stroke=T.GREEN, sw=2)
    canvas.line(577, 262, 300, 262, stroke=T.GREEN, sw=2)
    canvas.arrow(300, 262, 300, 288, color=T.GREEN, sw=2, head=7)
    canvas.line(577, 262, 850, 262, stroke=T.GREEN, sw=2)
    canvas.arrow(850, 262, 850, 288, color=T.GREEN, sw=2, head=7)
    canvas.text(430, 254, "APB1 ÷2", size=12, fill=T.MUTED, weight="700")
    canvas.text(700, 254, "APB2 不分频", size=12, fill=T.MUTED, weight="700")
    node(210, 292, 180, 62, "PCLK1 36", "APB1 外设", T.BLUE)
    node(760, 292, 180, 62, "PCLK2 72", "APB2 外设", T.GREEN)
    # TIM ×2 与 ADC/USB/MCO
    canvas.arrow(300, 354, 300, 388, color=T.BLUE, sw=2, head=7)
    canvas.text(312, 376, "TIM ×2（预分频≠1 时翻倍）", size=11, fill=T.BLUE)
    node(210, 392, 180, 56, "TIM2–7 = 72", "定时器时钟", T.BLUE)
    # 右下三路
    branches = [
        ("ADC 预分频 ÷6", "ADCCLK = 12 MHz", "ADCPRE=01 → 18 MHz，越过 14 MHz 上限", T.AMBER, 384),
        ("USBPRE=0", "USBCLK = 48 MHz", "USBPRE=1 → 72 MHz，读描述符失败", T.AMBER, 456),
        ("pin 29 PA8 · MCO", "PLL/2 = 36 MHz", "MCO=111；直送 72 MHz 越过 50 MHz 上限", T.AMBER, 528),
    ]
    for label, val, note, c, by in branches:
        canvas.arrow(577, 222, 702, by + 32, color=T.MUTED, sw=1.5, head=6, dash="4 4")
        canvas.rect(704, by, 216, 64, fill=T.BG, stroke=c, rx=4)
        canvas.text(812, by + 20, label, size=12, fill=c, anchor="middle", weight="700")
        canvas.text(812, by + 38, val, size=11, fill=T.TEXT, anchor="middle", mono=True)
        canvas.text(812, by + 55, note, size=10, fill=T.MUTED, anchor="middle")

    # ---- 失败分支：HSE 停振 ----
    canvas.rect(40, 608, 880, 116, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(56, 636, "失败路径  HSE 停振：CSS 时钟安全系统", size=15, fill=T.RED, weight="700")
    canvas.text(56, 662, "SYSCLK 立刻回到 HSI 8 MHz，PLL 关掉——USART1 的 0x271 在 8 MHz 上只剩 12800", size=13, fill=T.TEXT)
    canvas.text(56, 686, "NMI 一直进来，直到软件写 CSSC；同一棵 ×9 的树配 LATENCY=0 也取指失败", size=13, fill=T.RED)

    canvas.rect(40, 738, 880, 74, fill=T.BG2, stroke=T.VIOLET, rx=8)
    canvas.text(56, 764, "旁注  互联型（F105/F107）第 8.3.2 节在这颗 C8 上作废", size=15, fill=T.VIOLET, weight="700")
    canvas.text(56, 790, "OTGFSPRE、PLLMUL 的 000x 保留与 x6.5 都不写进这颗料；0111 仍是 ×9，0000 仍是 ×2；无源晶振不开 bypass", size=12, fill=T.TEXT)
    _credit(canvas, "自绘。树来自 RM0008 Rev 21 第 7.3.2 节与第 7.2.7 节；脚位来自 DS5319 Rev 20 图 8。")
    return canvas



def pwm_1khz() -> Svg:
    canvas = Svg(
        960,
        820,
        "72 MHz 计数时钟下这组 PSC/ARR 是 1 kHz；改用 36 MHz 去除得到 500 Hz",
        "STM32F103C8T6 LQFP48 · RM0008 Rev 21 第 15 章",
    )
    canvas.header(tag="05", tag_color=T.CYAN)
    canvas.text(40, 86, "STM32F103C8T6  LQFP48  pin 16 PA6 = TIM3_CH1", size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "计数时钟 72 MHz    PSC=71    ARR=999    CCR=500", size=14, fill=T.CYAN)
    canvas.text(40, 138, "72e6 / ((71+1) x (999+1)) = 1000 Hz    高电平 500 us", size=14, fill=T.AMBER)
    canvas.text(40, 164, "SPI1_MISO is not on this trace", size=14, fill=T.MUTED)
    canvas.text(40, 196, "正常路径  CNT 0 到 499 为高，500 到 999 为低", size=16, fill=T.GREEN, weight="700")
    canvas.rect(40, 210, 880, 140, fill=T.PANEL, stroke=T.GREEN, rx=8)
    canvas.text(56, 240, "周期 1000 us，频率 1000 Hz，占空比 50%", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 266, "PWM 模式 1：CNT < CCR 时输出为高", size=14, fill=T.GREEN)
    canvas.text(56, 292, "计数时钟先被分成 1 MHz，再数 1000 下", size=14, fill=T.TEXT)
    canvas.text(56, 318, "TIM3_REMAP=00。PB4 和 PC6 不在这条路径上", size=13, fill=T.MUTED)
    canvas.text(40, 376, "失败路径  同一组 PSC/ARR/CCR，去除时用了 36 MHz", size=16, fill=T.RED, weight="700")
    canvas.rect(40, 390, 880, 130, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(56, 420, "周期变成 2000 us，频率 500 Hz", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 446, "多出来的那一倍来自把 PCLK1 当成了定时器时钟", size=14, fill=T.RED)
    canvas.text(56, 472, "TIM3 在 APB1。预分频不是 1，计数时钟仍是 72 MHz", size=14, fill=T.AMBER)
    canvas.text(56, 498, "不要用 36 MHz 去除这组 PSC=71、ARR=999", size=13, fill=T.MUTED)
    canvas.rect(40, 540, 880, 110, fill=T.BG2, stroke=T.VIOLET, rx=8)
    canvas.text(56, 570, "旁注  16-bit 装不下 ARR=999999", size=15, fill=T.VIOLET, weight="700")
    canvas.text(56, 596, "能装下的 1 秒是 PSC=7199、ARR=9999", size=14, fill=T.TEXT)
    canvas.text(56, 622, "TIM1 的 MOE 在 TIMx_BDTR 偏移 0x44，复位值 0x0000，位 15 为 0。那是另一只定时器，不占 PA6", size=13, fill=T.MUTED)
    _credit(canvas, "自绘。时基来自 RM0008 Rev 21 第 15 章；脚位来自 DS5319 Rev 20 表 5。")
    return canvas


def spi_jedec() -> Svg:
    canvas = Svg(
        960,
        860,
        "Mode 0、除以 8 得到 9 MHz；0x9F 之后的三字节是 0xEF、0x40、0x17",
        "STM32F103C8T6 LQFP48 · RM0008 Rev 21 第 25.5.1 节",
    )
    canvas.header(tag="08", tag_color=T.CYAN)
    canvas.text(40, 86, "STM32F103C8T6  LQFP48  SPI1  APB2  72 MHz", size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "pin 14 PA4 = CS    pin 15 PA5 = SCK    pin 16 PA6 = MISO    pin 17 PA7 = MOSI", size=14, fill=T.CYAN)
    canvas.text(40, 138, "CPOL=0  CPHA=0  空闲 SCK 为低，上升沿采样    BR=010  SCK = 9 MHz", size=14, fill=T.AMBER)
    canvas.text(40, 164, "正常路径  MOSI 先送 0x9F，随后三个 0xFF", size=16, fill=T.GREEN, weight="700")
    canvas.rect(40, 178, 880, 160, fill=T.PANEL, stroke=T.GREEN, rx=8)
    canvas.text(56, 208, "rx[0] 是命令期间移入的字节，不是厂商号", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 234, "rx[1]=0xEF  rx[2]=0x40  rx[3]=0x17", size=14, fill=T.GREEN)
    canvas.text(56, 260, "拼起来是 0xEF4017。0x40 是存储器类型，不是容量", size=14, fill=T.TEXT)
    canvas.text(56, 286, "事务结束时 PA4 回到高。片选是推挽 GPIO", size=14, fill=T.AMBER)
    canvas.text(56, 312, "页大小 256 字节。不把第 14 脚画成 DAC", size=13, fill=T.MUTED)
    canvas.text(40, 364, "失败路径  PA6 与 PA7 swapped", size=16, fill=T.RED, weight="700")
    canvas.rect(40, 378, 880, 130, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(56, 408, "MISO 上读不到 0xEF 0x40 0x17", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 434, "MOSI 和 MISO 对调之后，三字节对不上", size=14, fill=T.RED)
    canvas.text(56, 460, "CPHA 配成第二沿时字节会错位。那一行不占这张失败路径", size=14, fill=T.AMBER)
    canvas.text(56, 486, "PB3/PB4/PB5 不在正常路径上", size=13, fill=T.MUTED)
    canvas.rect(40, 528, 880, 110, fill=T.BG2, stroke=T.VIOLET, rx=8)
    canvas.text(56, 558, "旁注  PA4 一直为低时两条事务粘成一条", size=15, fill=T.VIOLET, weight="700")
    canvas.text(56, 584, "BR=000 时 SCK = 36 MHz，相对这条 9 MHz 的工作点过快", size=14, fill=T.TEXT)
    canvas.text(56, 610, "不编 SPI 基址。TIM3_CH1 不画进这条 MISO 波形", size=13, fill=T.MUTED)
    _credit(canvas, "自绘。BR 来自 RM0008 Rev 21 第 25.5.1 节；脚位来自 DS5319 Rev 20 表 5。")
    return canvas


def adc_sample() -> Svg:
    canvas = Svg(
        960,
        860,
        "这颗料的 ADC 时钟是 12 MHz，最长转换 21 us；采样太短时电容上仍是上一次的电压",
        "STM32F103C8T6 LQFP48 · RM0008 Rev 21 第 11 章",
    )
    canvas.header(tag="09", tag_color=T.CYAN)
    canvas.text(40, 86, "STM32F103C8T6  LQFP48  pin 10 PA0 = ADC12_IN0", size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "pin 9 VDDA 是参考    ADCCLK = 12 MHz    分母 4096", size=14, fill=T.CYAN)
    canvas.text(40, 138, "正常路径  采样开关闭合，然后断开保持，比较器做 MSB", size=16, fill=T.GREEN, weight="700")
    canvas.rect(40, 152, 880, 170, fill=T.PANEL, stroke=T.GREEN, rx=8)
    canvas.text(56, 182, "R_AIN 给采样电容充电。开关断开后电压被保持", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 208, "MSB 那一次与 Vref/2 比较", size=14, fill=T.GREEN)
    canvas.text(56, 234, "最长一档 239.5 + 12.5 = 252 周期 = 21 us", size=14, fill=T.AMBER)
    canvas.text(56, 260, "码值 x VDDA / 4096。码 2048 在名义 3.3 V 下是 1.65 V", size=14, fill=T.TEXT)
    canvas.text(56, 286, "1.5 周期 = 125 ns。不把 LED 电阻画进这张图", size=13, fill=T.MUTED)
    canvas.text(40, 348, "失败路径  采样太短，电容上仍是 previous voltage", size=16, fill=T.RED, weight="700")
    canvas.rect(40, 362, 880, 120, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(56, 392, "这一次的码不是现在的输入", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 418, "高阻时用 239.5 周期", size=14, fill=T.RED)
    canvas.text(56, 444, "71.5 周期是 5.958 us，盖不住温度通道的 17.1 us", size=14, fill=T.AMBER)
    canvas.rect(40, 502, 880, 120, fill=T.BG2, stroke=T.VIOLET, rx=8)
    canvas.text(56, 532, "旁注  除以 4 得到 18 MHz，越过 14 MHz", size=15, fill=T.VIOLET, weight="700")
    canvas.text(56, 558, "1 us 那个例子是 14 MHz 上的，不是这颗料的工作点", size=14, fill=T.TEXT)
    canvas.text(56, 584, "第 14 脚画成 DAC 时，C8 上没有这只脚的 DAC。C8 有 ADC1 和 ADC2", size=13, fill=T.MUTED)
    canvas.text(56, 608, "不把第 03 章的 LED 电阻画进来", size=13, fill=T.MUTED)
    _credit(canvas, "自绘。Tconv 与 17.1 us 来自 RM0008 Rev 21 第 11 章；脚位来自 DS5319 Rev 20 图 8。")
    return canvas


def swd_vectors() -> Svg:
    canvas = Svg(
        960,
        980,
        "SWCLK 在第 37 脚；BOOT0=0 时第 0 字是栈、第 1 字是复位；无保护字节是 0xA5",
        "STM32F103C8T6 LQFP48 · DS5319 Rev 20 表 5",
    )
    canvas.header(tag="01", tag_color=T.CYAN)
    canvas.text(40, 86, "STM32F103C8T6  LQFP48", size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "pin 34 PA13 = SWDIO    pin 37 PA14 = SWCLK", size=14, fill=T.CYAN)
    canvas.text(40, 138, "pin 35 VSS_2    pin 36 VDD_2    pin 44 BOOT0 = 0", size=14, fill=T.AMBER)
    canvas.text(40, 164, "程序写入 0x08000000。0x00000000 别名到这块闪存", size=14, fill=T.TEXT)
    canvas.text(40, 196, "正常路径  第 0 字 MSP，第 1 字 Reset_Handler，然后才到 main", size=16, fill=T.GREEN, weight="700")
    canvas.rect(40, 210, 880, 150, fill=T.PANEL, stroke=T.GREEN, rx=8)
    canvas.text(56, 240, "读 0x00000000 得到 MSP", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 266, "读 0x00000004 得到 Reset_Handler", size=14, fill=T.GREEN)
    canvas.text(56, 292, "物理存储器是 0x08000000 起的 64 KB。SRAM 是 20 KB，从 0x20000000 起", size=14, fill=T.TEXT)
    canvas.text(56, 318, "无保护字节是 0xA5。RDP 编程回 0xA5 会先整片擦除主闪存", size=14, fill=T.AMBER)
    canvas.text(56, 344, "IRQ 入口是 VTOR + 4×(IRQn + 16)", size=13, fill=T.MUTED)
    canvas.text(40, 386, "失败路径  同一对 PA13/PA14 被配成 GPIO", size=16, fill=T.RED, weight="700")
    canvas.rect(40, 400, 880, 120, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(56, 430, "Debug 关掉之后，下一次探针在这两只脚上连不上", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 456, "pin 34 和 pin 37 不再是 SWDIO / SWCLK", size=14, fill=T.RED)
    canvas.text(56, 482, "SYS Debug 要留在 Serial Wire", size=14, fill=T.AMBER)
    canvas.rect(40, 540, 880, 150, fill=T.BG2, stroke=T.VIOLET, rx=8)
    canvas.text(56, 570, "旁注  pin 35 被当成 SWCLK 会接空", size=15, fill=T.VIOLET, weight="700")
    canvas.text(56, 596, "BOOT1=0 且 BOOT0=1 时取到 0x1FFFF000，不是 SRAM", size=14, fill=T.TEXT)
    canvas.text(56, 622, "0xAA 不是这颗料的无保护。128 KB 在 C8T6 上作废", size=14, fill=T.AMBER)
    canvas.text(56, 648, "第 39 脚 PB3 默认是 JTDO。SWO 不在正常路径上", size=13, fill=T.MUTED)
    canvas.text(56, 672, "不把第 00 章的整张启动表再画一遍", size=13, fill=T.MUTED)
    _credit(canvas, "自绘。脚位来自 DS5319 Rev 20 表 5；两字来自 PM0056；0xA5 来自 PM0075。")
    return canvas


def i2c_addr() -> Svg:
    canvas = Svg(
        960,
        920,
        "HAL 送出的写地址是 0x78；0x801E 是 36 MHz 下表 42 的 400 kHz 行；0x3C 原样送出时第 9 个时钟没有 ACK",
        "STM32F103C8T6 LQFP48 · DS5319 Rev 20 表 42",
    )
    canvas.header(tag="07", tag_color=T.CYAN)
    canvas.text(40, 86, "STM32F103C8T6  LQFP48  I2C1  APB1", size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "pin 42 PB6 = SCL    pin 43 PB7 = SDA", size=14, fill=T.CYAN)
    canvas.text(40, 138, "两只 4.7 kΩ 接到 3.3 V    PCLK1 = 36 MHz    I2C_CCR = 0x801E", size=14, fill=T.AMBER)
    canvas.text(40, 170, "正常路径  START 之后线上第一字节是 0x78", size=16, fill=T.GREEN, weight="700")
    canvas.rect(40, 184, 880, 150, fill=T.PANEL, stroke=T.GREEN, rx=8)
    canvas.text(56, 214, "第 9 个时钟 SDA 为低，ACK", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 240, "目标速率 400 kHz，旁边是表 42 的 ±2%，不是保证值", size=14, fill=T.GREEN)
    canvas.text(56, 266, "0x801E：快速模式，DUTY = 0，CCR 字段 = 30", size=14, fill=T.TEXT)
    canvas.text(56, 292, "3 × 30 / 36e6 = 2.5 µs", size=14, fill=T.AMBER)
    canvas.text(56, 316, "100 kHz 那一行是 0x00B4。PB8/PB9 不在这条路径上", size=13, fill=T.MUTED)
    canvas.text(40, 360, "失败路径  DevAddress 填了 0x3C", size=16, fill=T.RED, weight="700")
    canvas.rect(40, 374, 880, 120, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(56, 404, "线上第一字节是 0x3C，7 位地址变成 0x1E", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 430, "第 9 个时钟 SDA 仍为高，NACK", size=14, fill=T.RED)
    canvas.text(56, 456, "读方向的线上字节是 0x79，不占这条失败路径", size=14, fill=T.AMBER)
    canvas.rect(40, 514, 880, 110, fill=T.BG2, stroke=T.VIOLET, rx=8)
    canvas.text(56, 544, "旁注  只有片内上拉时，不把这张图画成 400 kHz", size=15, fill=T.VIOLET, weight="700")
    canvas.text(56, 570, "1 MHz 不在表 41、表 42 里", size=14, fill=T.TEXT)
    canvas.text(56, 596, "USART1 的重映射不是复位默认。不画推挽片选", size=13, fill=T.MUTED)
    _credit(canvas, "自绘。CCR 与脚位来自 DS5319 Rev 20 表 42 和表 5；地址字节来自 RM0008 Rev 21 第 26 章。")
    return canvas


def dma_cndtr() -> Svg:
    canvas = Svg(
        960,
        900,
        "8 个半字且 CNDTR 为 3 时已写 5 个采样、10 字节；把剩余计数当成字节会切错",
        "STM32F103C8T6 · RM0008 Rev 21 第 13 章",
    )
    canvas.header(tag="10", tag_color=T.CYAN)
    canvas.text(40, 86, "STM32F103C8T6  只有 DMA1，7 条通道", size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "USART1_TX 走 channel 4。宽度是半字。缓冲区长度 8", size=14, fill=T.CYAN)
    canvas.text(40, 138, "TX 仍从 pin 30 PA9 出去。不重画 8N1 帧", size=14, fill=T.MUTED)
    canvas.text(40, 170, "正常路径  CNDTR = 3", size=16, fill=T.GREEN, weight="700")
    canvas.rect(40, 184, 880, 150, fill=T.PANEL, stroke=T.GREEN, rx=8)
    canvas.text(56, 214, "已写 5 samples，10 bytes", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 240, "8 − 3 = 5，再乘 2 才是字节", size=14, fill=T.GREEN)
    canvas.text(56, 266, "半传输刻度在第 4 samples，8 bytes，不是 4 字节", size=14, fill=T.AMBER)
    canvas.text(56, 292, "ADC1 = channel 1。USART1_RX = channel 5", size=14, fill=T.TEXT)
    canvas.text(56, 316, "归零后硬件重装 CNDTR。长度减 CNDTR 不是累计", size=13, fill=T.MUTED)
    canvas.text(40, 360, "失败路径  同一读数被当成字节", size=16, fill=T.RED, weight="700")
    canvas.rect(40, 374, 880, 110, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(56, 404, "还剩 3 字节、已写 5 字节。后一半从错误的边界切开", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 430, "CNDTR 数的是数据项，不是字节", size=14, fill=T.RED)
    canvas.text(56, 456, "半字数组会从奇数边界切开", size=14, fill=T.AMBER)
    canvas.rect(40, 504, 880, 100, fill=T.BG2, stroke=T.VIOLET, rx=8)
    canvas.text(56, 534, "旁注  DMA2 Stream 5 在这颗 C8 上没有计数器", size=15, fill=T.VIOLET, weight="700")
    canvas.text(56, 560, "F4 的那一组号留在 F4。不画采样电容", size=14, fill=T.TEXT)
    canvas.text(56, 584, "内存到内存若占用通道 1，它和 ADC1 抢同一条通道", size=13, fill=T.MUTED)
    _credit(canvas, "自绘。CNDTR 来自 RM0008 Rev 21 第 13 章；只有 DMA1 来自 DS5319 Rev 20 第 2.3.13 节。")
    return canvas


def iwdg_1s() -> Svg:
    canvas = Svg(
        960,
        980,
        "Reload 624 在 40 kHz 典型值下是 1 秒；减到 0 才复位；LSE 要 PRL = 32767 才是 1 Hz",
        "STM32F103C8T6 · DS5319 Rev 20 表 25",
    )
    canvas.header(tag="11", tag_color=T.CYAN)
    canvas.text(40, 86, "STM32F103C8T6  IWDG  典型 40 kHz，范围 30 kHz 到 60 kHz", size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "prescaler 64    计数频率 625 Hz    Reload = 624", size=14, fill=T.CYAN)
    canvas.text(40, 138, "64 / 40000 × (624 + 1) = 1 s。这是典型值，不是保证值", size=14, fill=T.AMBER)
    canvas.text(40, 170, "正常路径  计数器还大于 0 时喂狗，不复位", size=16, fill=T.GREEN, weight="700")
    canvas.rect(40, 184, 880, 130, fill=T.PANEL, stroke=T.GREEN, rx=8)
    canvas.text(56, 214, "这一次喂狗发生在超时之前", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 240, "喂早对 IWDG 不是复位条件", size=14, fill=T.GREEN)
    canvas.text(56, 266, "30 kHz 时同一套数是 4/3 s。60 kHz 时是 2/3 s", size=14, fill=T.TEXT)
    canvas.text(56, 292, "Stop 和 Standby 里计数不停。调试时可以冻住", size=13, fill=T.MUTED)
    canvas.text(40, 340, "失败路径  同一条计数减到 0，没有喂狗，复位", size=16, fill=T.RED, weight="700")
    canvas.rect(40, 354, 880, 110, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(56, 384, "Reload = 625 会多一个计数", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 410, "(625 + 1) / 625 比 1 秒多一拍", size=14, fill=T.RED)
    canvas.text(56, 436, "不把 6.55 s 画成第二套规范", size=14, fill=T.AMBER)
    canvas.rect(40, 484, 880, 160, fill=T.BG2, stroke=T.VIOLET, rx=8)
    canvas.text(56, 514, "备份域  pin 1 VBAT    pin 3 PC14    pin 4 PC15", size=15, fill=T.VIOLET, weight="700")
    canvas.text(56, 540, "32.768 kHz，PRL = 32767，10 个 16 位寄存器，20 字节", size=14, fill=T.TEXT)
    canvas.text(56, 566, "PRL = 32768 不是 1 Hz。42 个备份寄存器在这颗料上作废", size=14, fill=T.AMBER)
    canvas.text(56, 592, "窗口看门狗：计数器大于 0x50 时喂狗会复位", size=14, fill=T.TEXT)
    canvas.text(56, 618, "超时尺度是 58.25 ms，不和 IWDG 的 1 秒画成同一种狗", size=13, fill=T.MUTED)
    canvas.text(56, 642, "不画负载电容的皮法，也不画 PC13 的 LED", size=13, fill=T.MUTED)
    _credit(canvas, "自绘。LSI 与备份寄存器来自 DS5319 Rev 20 表 25、第 2.3.14 节和第 2.3.15 节；1 秒来自 RM0008 Rev 21 第 19 章。")
    return canvas


def iap_map() -> Svg:
    canvas = Svg(
        960,
        800,
        "中容量 1 KB 页；APP 从 0x08004800 起，长度 0xB800；跳转要装入第 0 字和第 1 字",
        "STM32F103C8T6 LQFP48 · RM0008 Rev 21 chapter 3",
    )
    canvas.header(title="64 页闪存与写入顺序：解锁、半字写入、两个字跳转",
                  tag="12", tag_color=T.CYAN)

    # ① 64 页网格
    canvas.text(24, 82, "整块闪存就是 64 页：STM32F103C8T6 · medium-density · LQFP48 · 64 × 1 KB = 64 KB",
                size=12.5, fill=T.TEXT, weight="700")
    gx, gy, cw, ch2, gap = 24, 96, 46, 28, 5
    for page in range(64):
        col, row = page % 16, page // 16
        x = gx + col * (cw + gap)
        y = gy + row * (ch2 + gap)
        if page < 16:
            color, fill_ = T.GREEN, 0.22
        elif page < 18:
            color, fill_ = T.AMBER, 0.34
        else:
            color, fill_ = T.VIOLET, 0.16
        canvas.rect(x, y, cw, ch2, fill=color, rx=2, opacity=fill_)
        canvas.rect(x, y, cw, ch2, fill="none", stroke=color, sw=1, rx=2)
        if page in (0, 16, 18, 63):
            canvas.text(x + cw / 2, y + ch2 / 2 + 3.2, str(page), size=8.5,
                        anchor="middle", fill=T.TEXT, mono=True)
    legend = [(T.GREEN, "0–15 页  Bootloader 16 KB"),
              (T.AMBER, "16–17 页  参数区 2 KB"),
              (T.VIOLET, "18–63 页  APP 46 KB")]
    for i, (color, note) in enumerate(legend):
        x = 24 + i * 300
        canvas.rect(x, 246, 12, 12, fill=color, rx=2, opacity=0.35)
        canvas.rect(x, 246, 12, 12, fill="none", stroke=color, sw=1, rx=2)
        canvas.text(x + 20, 256, note, size=9.5, fill=T.MUTED)
    canvas.text(24, 276, "页边界：第 0 页 0x08000000 · 第 16 页 0x08004000 · 第 18 页 0x08004800 · 第 63 页 0x0800FC00 · 整块止于 0x08010000",
                size=9, fill=T.MUTED, mono=False)

    # ② 写入顺序
    fy = 312
    canvas.text(24, fy, "写入顺序：先解锁，再写半字，最后把两个字装进 CPU",
                size=12.5, fill=T.TEXT, weight="700")
    steps = [("KEY1", "0x45670123 → FLASH->KEYR", T.CYAN),
             ("KEY2", "0xCDEF89AB → LOCK 清零", T.CYAN),
             ("擦除", "按页擦，整页变 0xFFFF", T.AMBER),
             ("写入", "半字、偶地址，1 只能变 0", T.GREEN),
             ("校验", "读回比对，失败重擦重写", T.GREEN)]
    for i, (head, body, color) in enumerate(steps):
        x = 24 + i * 182
        canvas.rect(x, fy + 12, 168, 58, fill=T.PANEL, stroke=color, rx=8)
        canvas.text(x + 12, fy + 32, head, size=11, fill=color, weight="700")
        canvas.text(x + 12, fy + 48, body, size=8.5, fill=T.TEXT, mono=True)
        if i < 4:
            canvas.arrow(x + 170, fy + 41, x + 180, fy + 41, color=T.STROKE,
                         sw=1.5, head=4)

    # ③ 编程语义 + 失败路径
    by = 412
    canvas.rect(24, by, 448, 150, fill=T.PANEL, stroke=T.GREEN, rx=8)
    canvas.text(38, by + 24, "编程语义：擦除是 1，写只能把 1 变 0", size=11,
                fill=T.GREEN, weight="700")
    bits = [(1, 1), (1, 0), (0, 0), (1, 1)]
    canvas.text(38, by + 48, "擦除后", size=9, fill=T.MUTED)
    canvas.text(38, by + 78, "想写入", size=9, fill=T.MUTED)
    canvas.text(38, by + 108, "结果", size=9, fill=T.MUTED)
    for i, (src, dst) in enumerate(bits):
        x = 92 + i * 34
        canvas.rect(x, by + 36, 26, 20, fill=T.BG2, stroke=T.GRID, rx=2)
        canvas.text(x + 13, by + 51, str(src), size=10, anchor="middle",
                    fill=T.TEXT, mono=True)
        canvas.rect(x, by + 66, 26, 20, fill=T.BG2, stroke=T.GRID, rx=2)
        canvas.text(x + 13, by + 81, str(dst), size=10, anchor="middle",
                    fill=T.TEXT, mono=True)
        ok = src == 1 or dst == 0
        canvas.rect(x, by + 96, 26, 20, fill=T.GREEN if ok else T.RED, rx=2,
                    opacity=0.22)
        canvas.rect(x, by + 96, 26, 20, fill="none",
                    stroke=T.GREEN if ok else T.RED, sw=1, rx=2)
        canvas.text(x + 13, by + 111, str(src & dst), size=10, anchor="middle",
                    fill=T.GREEN if ok else T.RED, mono=True)
    canvas.text(250, by + 51, "0xFFFF", size=9, fill=T.MUTED, mono=True)
    canvas.text(250, by + 81, "半字值", size=9, fill=T.MUTED)
    canvas.text(250, by + 111, "按位与", size=9, fill=T.MUTED)
    canvas.text(38, by + 134, "想从 0 变 1 必须先擦整页；C8 上按字节写是无效的，只认半字",
                size=9, fill=T.TEXT)

    canvas.rect(488, by, 448, 150, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(502, by + 24, "三种失败，各有一个特征", size=11, fill=T.RED,
                weight="700")
    fails = [("KEY2 先写", "LOCK 仍置位，擦除返回错误"),
             ("末页写成 0x0801FC00", "越出这 64 KB —— 这块到 0x08010000 为止"),
             ("VTOR 留在 0", "中断仍进 Bootloader 的向量表")]
    for i, (head, body) in enumerate(fails):
        y = by + 48 + i * 34
        canvas.circle(510, y - 4, 8, fill=T.BG2, stroke=T.RED, sw=1.5)
        canvas.text(510, y - 0.5, str(i + 1), size=8.5, anchor="middle",
                    fill=T.RED, weight="700")
        canvas.text(526, y, head, size=10, fill=T.TEXT, weight="600")
        canvas.text(526, y + 15, body, size=9, fill=T.MUTED)

    # ④ 跳转
    jy = 588
    canvas.text(24, jy, "跳转只认两个地址上的两个字，外加向量表基址", size=12.5,
                fill=T.VIOLET, weight="700")
    cells = [("0x08004800", "第 0 字 = 初始 MSP", T.CYAN),
             ("0x08004804", "第 1 字 = Reset_Handler", T.CYAN),
             ("SCB->VTOR", "写 0x08004800", T.VIOLET)]
    for i, (addr, note, color) in enumerate(cells):
        x = 24 + i * 306
        canvas.rect(x, jy + 12, 292, 54, fill=T.PANEL, stroke=color, rx=8)
        canvas.text(x + 12, jy + 32, addr, size=10.5, fill=color, mono=True,
                    weight="700")
        canvas.text(x + 12, jy + 50, note, size=9.5, fill=T.TEXT)

    # ⑤ 与本章其它图的分工
    canvas.rect(24, 682, 912, 60, fill=T.BG2, stroke=T.GREEN, rx=8)
    canvas.text(40, 706, "这张图画用户闪存本身；系统存储器与两条启动路径在上一张对比图里。",
                size=10.5, fill=T.TEXT)
    canvas.text(40, 726, "串口刷写在 PA9/PA10（第 30/31 脚）；选项字节 0xA5 属于第 01 章的读保护。",
                size=10.5, fill=T.MUTED)

    _credit(canvas, "自绘。页和钥匙来自 RM0008 Rev 21 第 3 章；两字来自 PM0056。")
    return canvas


def can_bit() -> Svg:
    canvas = Svg(
        960,
        980,
        "36 MHz 下预分频 9、8 个时间份额是 500 kbit/s；预分频 8 和 10 个时间份额是 450 kbit/s；工作脚是第 45 脚和第 46 脚",
        "STM32F103C8T6 LQFP48 · RM0008 Rev 21 bxCAN",
    )
    canvas.header(title="总线上一位长什么样：帧、位填充与收发器接线",
                  tag="13", tag_color=T.ORANGE)

    # ① 标准帧
    canvas.text(24, 82, "标准数据帧按位排开：11 位 ID 在前，ACK 是一位", size=12.5,
                fill=T.TEXT, weight="700")
    fields = [("SOF", 1, T.CYAN), ("ID", 11, T.AMBER), ("RTR", 1, T.MUTED),
              ("IDE", 1, T.MUTED), ("r0", 1, T.MUTED), ("DLC", 4, T.MUTED),
              ("data", 8, T.GREEN), ("CRC", 15, T.VIOLET), ("ACK", 2, T.RED),
              ("EOF", 7, T.MUTED)]
    total = sum(n for _, n, _ in fields)
    fx, fw = 24, 900
    x = fx
    for name, n, color in fields:
        w = fw * n / total
        canvas.rect(x, 94, w - 1, 30, fill=color, rx=2, opacity=0.22)
        canvas.rect(x, 94, w - 1, 30, fill="none", stroke=color, sw=1, rx=2)
        if w > 16:
            canvas.text(x + w / 2, 113, name, size=8.5, anchor="middle",
                        fill=color, mono=True)
        x += w
    canvas.text(24, 140, "1 + 11 + 1 + 1 + 1 + 4 + 8 + 15 + 2 + 7 = 51 位，数据段按实际字节数算",
                size=9, fill=T.MUTED, mono=True)
    canvas.text(24, 158, "ACK 位由接收方拉低：没人应答就是 ACK 错误，这解释了单节点为什么发不出去",
                size=9.5, fill=T.RED)

    # ② 位填充
    canvas.text(24, 196, "位填充：连续 5 个相同位之后插一个相反的位", size=12.5,
                fill=T.TEXT, weight="700")
    pattern = [1, 0, 1, 1, 1, 1, 1, 1, 0, 0]
    stuffed = [1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 0]
    for i, bit in enumerate(stuffed):
        x = 24 + i * 34
        is_stuff = i == 7
        color = T.RED if is_stuff else T.CYAN
        canvas.rect(x, 208, 30, 26, fill=color, rx=2,
                    opacity=0.30 if is_stuff else 0.16)
        canvas.rect(x, 208, 30, 26, fill="none", stroke=color, sw=1.5, rx=2)
        canvas.text(x + 15, 226, str(bit), size=10, anchor="middle", fill=color,
                    mono=True)
    canvas.text(24, 248, "原始：1 0 1 1 1 1 1 1 0 0 —— 六个 1 之后必须插一个 0", size=9,
                fill=T.MUTED, mono=True)
    canvas.text(316, 258, "↑ 插入位", size=9.5, fill=T.RED)
    canvas.arrow(300, 250, 270, 236, color=T.RED, sw=1.5, head=5)

    # ③ 收发器与终端
    ty = 276
    canvas.text(24, ty, "MCU 的脚印不进总线：中间必须过收发器", size=12.5,
                fill=T.TEXT, weight="700")
    canvas.rect(24, ty + 12, 190, 62, fill=T.PANEL, stroke=T.CYAN, rx=8)
    canvas.text(38, ty + 32, "STM32F103C8T6", size=9.5, fill=T.MUTED)
    canvas.text(38, ty + 50, "pin 45 PB8 = CAN_RX", size=9.5, fill=T.CYAN, mono=True)
    canvas.text(38, ty + 66, "pin 46 PB9 = CAN_TX", size=9.5, fill=T.CYAN, mono=True)
    canvas.arrow(218, ty + 44, 262, ty + 44, color=T.STROKE, sw=1.5, head=6)
    canvas.rect(266, ty + 12, 150, 62, fill=T.PANEL, stroke=T.AMBER, rx=8)
    canvas.text(280, ty + 32, "收发器", size=10, fill=T.AMBER, weight="700")
    canvas.text(280, ty + 50, "TXD / RXD", size=9, fill=T.TEXT, mono=True)
    canvas.text(280, ty + 66, "CANH / CANL", size=9, fill=T.TEXT, mono=True)
    canvas.arrow(420, ty + 44, 464, ty + 44, color=T.STROKE, sw=1.5, head=6)
    # 总线
    canvas.line(470, ty + 30, 900, ty + 30, stroke=T.CYAN, sw=2)
    canvas.line(470, ty + 60, 900, ty + 60, stroke=T.CYAN, sw=2)
    canvas.text(902, ty + 34, "CANH", size=9, fill=T.CYAN, mono=True)
    canvas.text(902, ty + 64, "CANL", size=9, fill=T.CYAN, mono=True)
    for xx in (470, 880):
        canvas.rect(xx - 10, ty + 34, 20, 22, fill=T.PANEL2, stroke=T.AMBER, rx=2)
        canvas.text(xx, ty + 49, "120", size=8, anchor="middle", fill=T.AMBER,
                    mono=True)
    canvas.text(470, ty + 96, "两端各一只 120", size=9, fill=T.AMBER, mono=True)
    canvas.text(560, ty + 96, "并联 = 60 直流负载，不是电缆特性阻抗", size=9,
                fill=T.MUTED)

    # ④ 两种配置
    cy = 400
    canvas.text(24, cy, "两种配法只差三个数，速率和采样点就都变了", size=12.5,
                fill=T.TEXT, weight="700")
    cfgs = [(T.GREEN, "工作配置", [("prescaler 9", "Tq = 250 ns"), ("SYNC 1 + BS1 5 + BS2 2", "八个时间份额"),
                                    ("2 us 一位", "500 kbit/s"), ("采样点 75%", "1.5 us 处"), ("SJW = 1", "APB1 36 MHz")]),
            (T.RED, "对不上的那组", [("prescaler 8", "配十个份额"), ("36e6 / (8 x 10)", "450 kbit/s"),
                                    ("一位不是 2 us", "两端都报错"), ("采样点 70%", "BS1 6 / BS2 3"), ("10 份额要 7.2 分频", "不是整数")])]
    for i, (color, head, rows) in enumerate(cfgs):
        x = 24 + i * 462
        canvas.rect(x, cy + 12, 450, 168, fill=T.PANEL, stroke=color, rx=8)
        canvas.rect(x, cy + 12, 450, 5, fill=color, rx=2)
        canvas.text(x + 14, cy + 36, head, size=10.5, fill=T.TEXT, weight="700")
        for j, (key, val) in enumerate(rows):
            y = cy + 58 + j * 24
            canvas.text(x + 14, y, key, size=9, fill=color, mono=True)
            canvas.text(x + 230, y, val, size=9, fill=T.MUTED)

    # ⑤ 引脚
    py = 604
    canvas.text(24, py, "引脚：默认与 USB 撞，改到 PB8/PB9 用第一种重映射", size=12.5,
                fill=T.TEXT, weight="700")
    pins = [(T.MUTED, "pin 32 PA11", "CAN_RX 默认，也是 USB DM"),
            (T.MUTED, "pin 33 PA12", "CAN_TX 默认，也是 USB DP"),
            (T.RED, "pin 5 PD0", "重映射之一，会把 HSE 顶掉"),
            (T.RED, "pin 6 PD1", "同上，C8 上不要选"),
            (T.GREEN, "pin 45 PB8 / pin 46 PB9", "第一种重映射，本章用它")]
    for i, (color, head, note) in enumerate(pins):
        y = py + 14 + i * 26
        canvas.text(38, y, head, size=9.5, fill=color, mono=True)
        canvas.text(300, y, note, size=9, fill=T.MUTED)
    canvas.rect(24, 740, 912, 52, fill=T.BG2, stroke=T.CYAN, rx=8)
    canvas.text(40, 762, "这张画总线上的一位与接线；发不出、收不到、错误帧暴涨的分诊在排错三岔口那张里。",
                size=10, fill=T.TEXT)
    canvas.text(40, 780, "1 Mbit/s 与 Bus-Off 恢复的 128 × 11 个隐性位留给正文与时序表。",
                size=10, fill=T.MUTED)

    _credit(canvas, "自绘。位时间与帧格式来自 RM0008 Rev 21 bxCAN；脚位来自 DS5319 Rev 20 表 5。")
    return canvas


def usb_enum() -> Svg:
    canvas = Svg(
        960,
        980,
        "全速要 48 MHz；D+ 上拉在第 33 脚；描述符是 18 字节设备加 67 字节配置集合，VID/PID 是 0x1209/0x0001",
        "STM32F103C8T6 LQFP48 · RM0008 Rev 21 USB device",
    )
    canvas.header(tag="14", tag_color=T.CYAN)
    canvas.text(40, 122, "枚举的第一课：时钟 48 MHz、D+ 上拉、描述符长度——三样都对主机才开口", size=15, fill=T.TEXT, weight="700")

    # ---- 左：主机与设备的连接 ----
    canvas.rect(40, 152, 250, 120, fill=T.PANEL, stroke=T.CYAN, rx=8)
    canvas.text(165, 200, "主机", size=22, fill=T.CYAN, anchor="middle", weight="700")
    canvas.text(165, 232, "问描述符的是它", size=13, fill=T.MUTED, anchor="middle")
    canvas.rect(40, 392, 250, 120, fill=T.PANEL, stroke=T.GREEN, rx=8)
    canvas.text(165, 438, "设备 STM32", size=20, fill=T.GREEN, anchor="middle", weight="700")
    canvas.text(165, 468, "pin 32 PA11 = DM", size=12, fill=T.TEXT, anchor="middle", mono=True)
    canvas.text(165, 490, "pin 33 PA12 = DP", size=12, fill=T.TEXT, anchor="middle", mono=True)
    # DM / DP 两条线
    canvas.line(120, 272, 120, 392, stroke=T.MUTED, sw=2)
    canvas.text(108, 338, "DM (PA11)", size=11, fill=T.MUTED, anchor="end", mono=True)
    canvas.line(190, 272, 190, 392, stroke=T.GREEN, sw=2)
    canvas.text(178, 338, "DP (PA12)", size=11, fill=T.GREEN, anchor="end", mono=True)
    # 1.5 kΩ 上拉到 3.3 V
    canvas.line(190, 330, 232, 330, stroke=T.AMBER, sw=2)
    canvas.rect(232, 316, 56, 28, fill=T.BG, stroke=T.AMBER, rx=2)
    canvas.text(260, 335, "1.5 kΩ", size=11, fill=T.AMBER, anchor="middle", weight="700")
    canvas.line(288, 330, 316, 330, stroke=T.AMBER, sw=2)
    canvas.text(324, 335, "→ 3.3 V", size=12, fill=T.AMBER, weight="700")
    canvas.text(232, 368, "接错到 DM 会被当低速", size=11, fill=T.RED)

    # ---- 右：时钟门 ----
    canvas.rect(470, 152, 450, 360, fill=T.PANEL, stroke=T.CYAN, rx=8)
    canvas.text(486, 182, "时钟门：USBPRE 只有两档", size=15, fill=T.CYAN, weight="700")
    canvas.rect(486, 202, 170, 64, fill=T.BG, stroke=T.CYAN, rx=4)
    canvas.text(571, 230, "PLL 72 MHz", size=15, fill=T.TEXT, anchor="middle", weight="700")
    canvas.text(571, 252, "来自第 02 章", size=11, fill=T.MUTED, anchor="middle")
    canvas.arrow(658, 234, 688, 234, color=T.GREEN, sw=2, head=7)
    canvas.text(686, 218, "USBPRE = 0", size=11, fill=T.GREEN, weight="700", anchor="end")
    canvas.text(686, 262, "÷ 1.5", size=12, fill=T.GREEN, weight="700", anchor="end")
    canvas.rect(690, 202, 210, 64, fill=T.BG, stroke=T.GREEN, rx=4)
    canvas.text(795, 230, "48 MHz ✓", size=16, fill=T.GREEN, anchor="middle", weight="700")
    canvas.text(795, 252, "全速设备要的频率", size=11, fill=T.MUTED, anchor="middle")
    # 红分支
    canvas.arrow(658, 234, 688, 380, color=T.RED, sw=2, head=7, dash=None)
    canvas.text(640, 330, "USBPRE = 1：不分频", size=12, fill=T.RED, weight="700")
    canvas.rect(690, 348, 210, 64, fill=T.BG, stroke=T.RED, rx=4)
    canvas.text(795, 376, "72 MHz ✗", size=16, fill=T.RED, anchor="middle", weight="700")
    canvas.text(795, 398, "主机读描述符失败", size=11, fill=T.RED, anchor="middle")
    canvas.text(486, 448, "480 Mbit/s 在这颗料上不成立——这是全速 12 Mbit/s 的设备", size=13, fill=T.AMBER)
    canvas.text(486, 476, "bulk / interrupt 的 wMaxPacketSize 上限是 64，1023 是别的类", size=13, fill=T.MUTED)

    # ---- 下：两条描述符字节条 ----
    canvas.text(40, 590, "描述符是字节数对出来的：18 字节设备 + 67 字节配置集合", size=15, fill=T.TEXT, weight="700")
    canvas.rect(40, 606, 288, 58, fill=T.BG, stroke=T.GREEN, rx=4)
    canvas.text(184, 632, "设备描述符 18 B", size=14, fill=T.GREEN, anchor="middle", weight="700")
    canvas.text(184, 654, "VID/PID 0x1209 / 0x0001", size=11, fill=T.TEXT, anchor="middle", mono=True)
    canvas.rect(340, 606, 580, 58, fill=T.BG, stroke=T.BLUE, rx=4)
    canvas.text(630, 632, "配置集合 67 B（wTotalLength = 0x0043）", size=14, fill=T.BLUE, anchor="middle", weight="700")
    canvas.text(630, 654, "bMaxPower 0x32 = 100 mA　·　bMaxPacketSize0 = 64", size=11, fill=T.TEXT, anchor="middle", mono=True)
    canvas.text(40, 696, "总长度算错，枚举常常卡在选择配置之前——先数字节再谈驱动", size=13, fill=T.TEXT)
    canvas.text(40, 722, "0x0483/0x5740 不是本仓库的描述符；1.5 kΩ 接到 DM 也不是这台全速设备", size=13, fill=T.RED)

    canvas.rect(40, 756, 880, 116, fill=T.BG2, stroke=T.VIOLET, rx=8)
    canvas.text(56, 786, "旁注  这张图只画枚举的入场条件", size=15, fill=T.VIOLET, weight="700")
    canvas.text(56, 812, "不画 CAN 收发器与 ULPI；USB 中断与 CAN 共用向量的细节看源卡", size=13, fill=T.TEXT)
    canvas.text(56, 838, "图证明时钟/上拉/长度三道入场条件；不证明主机驱动的匹配过程", size=12, fill=T.MUTED)
    _credit(canvas, "自绘。48 MHz 来自已冻结的 USBPRE；脚位来自 DS5319 Rev 20 表 5；长度来自本仓库 usb-cdc。")
    return canvas



def rtos_prio() -> Svg:
    canvas = Svg(
        960,
        960,
        "一个 tick 是 1 ms；任务优先级 2 先于 1；128 字是 512 字节；FromISR 的数值优先级要大于等于 5",
        "STM32F103C8T6 · FreeRTOS Kernel V11.3.2",
    )
    canvas.header(tag="15", tag_color=T.CYAN)
    canvas.text(40, 122, "两把尺子别混用：NVIC 数字越小越急，FreeRTOS 任务数字越大越先跑", size=15, fill=T.TEXT, weight="700")

    # ---- 左：NVIC 尺子 ----
    canvas.rect(40, 152, 400, 380, fill=T.PANEL, stroke=T.CYAN, rx=8)
    canvas.text(240, 184, "NVIC 抢占优先级（GROUP_4）", size=16, fill=T.CYAN, anchor="middle", weight="700")
    nvic = [("0", "最急", T.RED), ("4", "也太急：FromISR 会触发 configASSERT", T.RED),
            ("5", "EXTI0 在这里：可以调 FromISR", T.GREEN), ("15", "最缓", T.MUTED)]
    y = 210
    for num, note, c in nvic:
        canvas.rect(70, y, 60, 40, fill=T.BG, stroke=c, rx=4)
        canvas.text(100, y + 26, num, size=16, fill=c, anchor="middle", weight="700")
        canvas.text(146, y + 26, note, size=12, fill=c)
        y += 56
    canvas.text(70, 448, "数字 0 的中断最急——和任务优先级正好相反", size=13, fill=T.AMBER, weight="700")
    canvas.text(70, 476, "5 << (8 - 4) = 0x50 写进 NVIC 寄存器", size=12, fill=T.MUTED, mono=True)
    canvas.arrow(220, 396, 220, 380, color=T.MUTED, sw=1.5, head=6)

    # ---- 右：任务尺子 ----
    canvas.rect(520, 152, 400, 380, fill=T.PANEL, stroke=T.GREEN, rx=8)
    canvas.text(720, 184, "FreeRTOS 任务优先级", size=16, fill=T.GREEN, anchor="middle", weight="700")
    tasks = [("2", "KEY：priority 2，先跑（数字大）", T.GREEN),
             ("1", "LED、UART：priority 1，后跑", T.AMBER)]
    y = 214
    for num, note, c in tasks:
        canvas.rect(550, y, 60, 40, fill=T.BG, stroke=c, rx=4)
        canvas.text(580, y + 26, num, size=16, fill=c, anchor="middle", weight="700")
        canvas.text(626, y + 26, note, size=12, fill=c)
        y += 56
    canvas.rect(550, 330, 340, 70, fill=T.BG, stroke=T.GREEN, rx=4)
    canvas.text(720, 356, "128 words = 512 bytes", size=14, fill=T.GREEN, anchor="middle", weight="700", mono=True)
    canvas.text(720, 380, "栈深单位是字（StackType_t），不是字节", size=12, fill=T.TEXT, anchor="middle")
    canvas.text(550, 436, "configTICK_RATE_HZ = 1000 → 一个 tick 1 ms", size=13, fill=T.TEXT)
    canvas.text(550, 462, "HAL 的时基挪到 TIM4，SysTick 留给内核", size=12, fill=T.MUTED)
    canvas.text(550, 488, "HAL 还挂在 SysTick 上，HAL_Delay 会卡死", size=12, fill=T.AMBER)

    # ---- 下：FromISR 判定 ----
    canvas.rect(40, 560, 880, 170, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(56, 590, "失败路径  EXTI0 的抢占优先级配成 0（或 4）", size=15, fill=T.RED, weight="700")
    canvas.text(56, 618, "在 ISR 里调 xQueueSendFromISR → configASSERT 停机", size=14, fill=T.RED, weight="700")
    canvas.text(56, 646, "数值优先级必须 ≥ 5（5 << 4 = 0x50 是及格线）；NVIC 的 0 是最急，不是最缓", size=13, fill=T.TEXT)
    canvas.text(56, 674, "不画 8 寄存器异常入栈的图——那是第 04 章的内容", size=12, fill=T.MUTED)
    canvas.htext = None

    canvas.rect(40, 746, 880, 116, fill=T.BG2, stroke=T.VIOLET, rx=8)
    canvas.text(56, 776, "旁注  这张图只对齐两把尺子和三条换算", size=15, fill=T.VIOLET, weight="700")
    canvas.text(56, 802, "tick = 1 ms ｜ 128 words = 512 bytes ｜ FromISR 及格线 = 数值 5", size=13, fill=T.TEXT, mono=True)
    canvas.text(56, 828, "证明对应关系与及格线；不证明调度器内部实现与具体工程的栈水位", size=12, fill=T.MUTED)
    _credit(canvas, "自绘。移位来自 FreeRTOS Kernel V11.3.2；栈和 TIM4 来自本仓库 freertos-task。")
    return canvas



def stop_wake() -> Svg:
    canvas = Svg(
        960,
        980,
        "低功耗稳压器的 Stop 典型值是 14 µA；醒来先是 HSI 8 MHz；不重配时钟时 0x271 变成 12800 bit/s",
        "STM32F103C8T6 LQFP48 · DS5319 Rev 20 Table 16 / Table 26",
    )
    canvas.header(title="进 Stop、被 EXTI 叫醒、再把时钟接回 72 MHz",
                  tag="16", tag_color=T.CYAN)

    # ① 进 Stop 需要的三个位
    canvas.text(24, 82, "进 Stop 是三个位同时成立，少一个就进错模式", size=12.5,
                fill=T.TEXT, weight="700")
    bits = [("SLEEPDEEP=1", "SCB->SCR，决定睡深不睡浅", T.GREEN),
            ("PDDS=0", "PWR->CR，0 是 Stop，1 是 Standby", T.AMBER),
            ("LPDS=1", "用低功耗稳压器，才有 14 uA", T.CYAN)]
    for i, (head, note, color) in enumerate(bits):
        x = 24 + i * 306
        canvas.rect(x, 94, 292, 52, fill=T.PANEL, stroke=color, rx=8)
        canvas.text(x + 12, 114, head, size=10.5, fill=color, weight="700",
                    mono=True)
        canvas.text(x + 12, 132, note, size=9, fill=T.MUTED)

    # ② 电流：两种稳压器
    cy = 168
    canvas.text(24, cy, "同一颗 Stop，稳压器不同差 10 uA —— 引用哪一格要看配置", size=12.5,
                fill=T.TEXT, weight="700")
    bars = [("LPDS=1 · 低功耗稳压器", 14, T.GREEN, "14 uA", "3.3 V / 25 °C / 关 IWDG"),
            ("LPDS=0 · 主稳压器", 24, T.AMBER, "24 uA", "同一个 Stop 状态，另一格数据")]
    for i, (label, ua, color, value, note) in enumerate(bars):
        y = cy + 16 + i * 40
        canvas.text(24, y + 14, label, size=9.5, fill=T.TEXT)
        w = 460 * ua / 24
        canvas.rect(250, y, w, 20, fill=color, rx=2, opacity=0.26)
        canvas.rect(250, y, w, 20, fill="none", stroke=color, sw=1.5, rx=2)
        canvas.text(250 + w + 8, y + 14, value, size=9.5, fill=color, mono=True)
        canvas.text(24, y + 34, note, size=8.5, fill=T.MUTED)
    canvas.text(700, cy + 30, "IWDG 单开一项就再 +3.4 uA", size=9, fill=T.RED)
    canvas.text(700, cy + 46, "表 16 的条件里写明关掉它", size=9, fill=T.MUTED)

    # ③ 唤醒时间轴
    ty = 286
    canvas.text(24, ty, "EXTI 叫醒之后不是立刻回到 72 MHz：先 HSI，再锁 PLL", size=12.5,
                fill=T.TEXT, weight="700")
    axis_y = ty + 78
    canvas.line(60, axis_y, 900, axis_y, stroke=T.STROKE, sw=1.5)
    segs = [("进入 Stop", 60, 200, T.MUTED, "pin 10 PA0 上的 EXTI 一直在等"),
            ("唤醒：HSI 8 MHz", 200, 400, T.GREEN, "第一条指令就跑在 8 MHz，5.4 us"),
            ("SystemClock_Config", 400, 620, T.AMBER, "重开 PLL，回 72 MHz"),
            ("PLL 锁定 ≤ 200 us", 620, 860, T.CYAN, "锁不上就超时")]
    for name, x1, x2, color, note in segs:
        canvas.rect(x1, axis_y - 26, x2 - x1 - 4, 52, fill=color, rx=4, opacity=0.22)
        canvas.rect(x1, axis_y - 26, x2 - x1 - 4, 52, fill="none", stroke=color,
                    sw=1.5, rx=4)
        canvas.text(x1 + 8, axis_y - 6, name, size=9.5, fill=color, weight="700")
        canvas.text(x1 + 8, axis_y + 12, note, size=8.5, fill=T.TEXT)
    canvas.text(200, axis_y + 44, "5.4 us", size=9, fill=T.GREEN, mono=True)
    canvas.text(620, axis_y + 44, "200 us", size=9, fill=T.CYAN, mono=True)
    canvas.text(60, axis_y + 44, "0", size=9, fill=T.MUTED, mono=True)
    canvas.text(24, axis_y + 68, "唤醒时间报 5.4 us 时，说的是到第一条指令；串口能用的时间要把 PLL 锁定的 200 us 加上。",
                size=9.5, fill=T.MUTED)

    # ④ 0x271 陷阱
    by = 470
    canvas.text(24, by, "最容易漏的一步：醒来重配时钟，否则 0x271 不是 115200", size=12.5,
                fill=T.TEXT, weight="700")
    canvas.rect(24, by + 12, 912, 150, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(38, by + 36, "USART1->BRR = 0x271 = 39.0625（16 倍过采样）", size=9.5,
                fill=T.MUTED, mono=True)
    rates = [("72 MHz: 72e6 / (16 × 39.0625)", 115200, "115200", T.GREEN, 1.0),
             ("8 MHz: 8e6 / (16 × 39.0625)", 12800, "12800", T.RED, 12800 / 115200)]
    for i, (calc, rate, value, color, frac) in enumerate(rates):
        y = by + 58 + i * 46
        canvas.text(38, y, calc, size=9, fill=T.TEXT, mono=True)
        w = 520 * frac
        canvas.rect(38, y + 8, max(w, 34), 20, fill=color, rx=2, opacity=0.24)
        canvas.rect(38, y + 8, max(w, 34), 20, fill="none", stroke=color, sw=1.5,
                    rx=2)
        canvas.text(38 + max(w, 34) + 10, y + 22, value + " bit/s", size=9.5,
                    fill=color, mono=True)
    canvas.text(700, by + 44, "主机仍是 115200", size=9.5, fill=T.TEXT)
    canvas.text(600, by + 100, "12800 × 9 = 115200", size=9.5, fill=T.RED, mono=True)
    canvas.text(600, by + 118, "差 9 倍，收到的是乱码不是短帧", size=9.5, fill=T.MUTED)
    canvas.text(600, by + 140, "先跑 SystemClock_Config()，再开 USART", size=9,
                fill=T.GREEN)

    # ⑤ 这张图不覆盖什么
    canvas.rect(24, 648, 912, 62, fill=T.BG2, stroke=T.CYAN, rx=8)
    canvas.text(40, 672, "Standby 的 2 uA 与唤醒 1.8 ms 另算一格；F4 的周期唤醒定时器在 C8 上不存在。",
                size=10.5, fill=T.TEXT)
    canvas.text(40, 692, "这里也不画第 06 章的 UART 位帧 —— 12800 与 115200 的差别在位宽，不在帧格式。",
                size=10, fill=T.MUTED)

    _credit(canvas, "自绘。电流和 5.4 us 来自 DS5319 Rev 20 表 16 与表 26。8 MHz 来自第 02 章。")
    return canvas


def cfsr_read() -> Svg:
    canvas = Svg(
        960,
        980,
        "BFAR 要 bit 15 为 1 才有效；72 MHz 下 72 个周期是 1 µs，而且要先打开 DEMCR bit 24",
        "STM32F103C8T6 · PM0056",
    )
    canvas.header(tag="17", tag_color=T.CYAN)
    canvas.text(40, 86, "STM32F103C8T6  Cortex-M3  no FPU", size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "CFSR 0xE000ED28    HFSR 0xE000ED2C    BFAR 0xE000ED38", size=14, fill=T.CYAN)
    canvas.text(40, 138, "FORCED is bit 30, value 0x40000000. PC is stacked word 6", size=14, fill=T.AMBER)
    canvas.text(40, 170, "正常路径  bit 15 is 1, and DEMCR bit 24 is already 1", size=16, fill=T.GREEN, weight="700")
    canvas.rect(40, 184, 880, 160, fill=T.PANEL, stroke=T.GREEN, rx=8)
    canvas.text(56, 214, "bit 15 = 1, so BFAR is this access", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 240, "DEMCR 0xE000EDFC bit 24, then DWT_CYCCNT 0xE0001004", size=14, fill=T.GREEN)
    canvas.text(56, 266, "72 counts at 72 MHz are 1 us", size=14, fill=T.TEXT)
    canvas.text(56, 292, "this M3 has 6 hardware breakpoints", size=14, fill=T.AMBER)
    canvas.text(56, 318, "PC is the 6th stacked word", size=13, fill=T.MUTED)
    canvas.text(40, 370, "失败路径  bit 15 is 0, or bit 24 was never set", size=16, fill=T.RED, weight="700")
    canvas.rect(40, 384, 880, 120, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(56, 414, "bit 15 = 0. The value in BFAR is not this access", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 440, "bit 24 = 0. The cycle delta is 0", size=14, fill=T.RED)
    canvas.text(56, 466, "8 hardware breakpoints are the M7 count and are void here", size=14, fill=T.AMBER)
    canvas.rect(40, 524, 880, 140, fill=T.BG2, stroke=T.VIOLET, rx=8)
    canvas.text(56, 554, "旁注  pin 39 is still JTDO after reset", size=15, fill=T.VIOLET, weight="700")
    canvas.text(56, 580, "TRACESWO is the remap column, not the power-up name", size=14, fill=T.TEXT)
    canvas.text(56, 606, "do not draw an SWO waveform on this figure", size=14, fill=T.AMBER)
    canvas.text(56, 632, "do not draw the 8-register timing waveform", size=13, fill=T.MUTED)
    _credit(canvas, "自绘。故障地址来自 PM0056。DWT 使能顺序是先 0xE000EDFC bit 24，再 0xE0001004。")
    return canvas


def boot_triage() -> Svg:
    canvas = Svg(
        960,
        960,
        "认不出芯片时先看第 34 脚、第 37 脚和第 44 脚；BOOT0 为 1 且 BOOT1 为 0 时跑的是 0x1FFFF000",
        "STM32F103C8T6 LQFP48 · DS5319 Rev 20 Figure 31 / Table 5",
    )
    canvas.header(tag="18", tag_color=T.CYAN)
    canvas.text(40, 86, "STM32F103C8T6  LQFP48  first look when the probe sees no target", size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "pin 34 PA13 = SWDIO    pin 37 PA14 = SWCLK", size=14, fill=T.CYAN)
    canvas.text(40, 138, "pin 7 NRST has 0.1 uF. pin 44 is BOOT0", size=14, fill=T.AMBER)
    canvas.text(40, 170, "正常路径  BOOT0 = 0, the CPU starts at 0x08000000", size=16, fill=T.GREEN, weight="700")
    canvas.rect(40, 184, 880, 150, fill=T.PANEL, stroke=T.GREEN, rx=8)
    canvas.text(56, 214, "probe on pin 34 and pin 37, common ground, 3.3 V", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 240, "BOOT0 = 0 selects main Flash at 0x08000000", size=14, fill=T.GREEN)
    canvas.text(56, 266, "Flash is 64 KB. SRAM is 20 KB", size=14, fill=T.TEXT)
    canvas.text(56, 292, "look at the wires before the optimizer", size=13, fill=T.MUTED)
    canvas.text(40, 360, "失败路径  BOOT0 = 1 and BOOT1 = 0", size=16, fill=T.RED, weight="700")
    canvas.rect(40, 374, 880, 120, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(56, 404, "the CPU is in system memory at 0x1FFFF000", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 430, "the image in Flash looks as if it was never programmed", size=14, fill=T.RED)
    canvas.text(56, 456, "changing -O2 before checking these pins is the other miss", size=14, fill=T.AMBER)
    canvas.rect(40, 514, 880, 140, fill=T.BG2, stroke=T.VIOLET, rx=8)
    canvas.text(56, 544, "旁注  pin 35 is VSS_2, not SWCLK", size=15, fill=T.VIOLET, weight="700")
    canvas.text(56, 570, "that mistake is already drawn in chapter 01", size=14, fill=T.TEXT)
    canvas.text(56, 596, "do not draw 38 icons on this figure", size=14, fill=T.AMBER)
    canvas.text(56, 622, "do not draw CFSR bits here", size=13, fill=T.MUTED)
    _credit(canvas, "自绘。0.1 uF 来自 DS5319 Rev 20 图 31。启动地址来自 RM0008。")
    return canvas


def flash_fit() -> Svg:
    canvas = Svg(
        960,
        980,
        "C8 只有一张 0xB800 的 APP；两张是 110 KB；65536 字节大于 20 KB SRAM",
        "STM32F103C8T6 · chapter 12 map · DS5319 64 KB / 20 KB",
    )
    canvas.header(tag="19", tag_color=T.CYAN)
    canvas.text(40, 86, "STM32F103C8T6  Flash 0x08000000 to 0x08010000  SRAM 20 KB", size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "16 KB + 2 KB + 46 KB = 64 KB. APP length 0xB800", size=14, fill=T.CYAN)
    canvas.text(40, 138, "SRAM 20 KB = 20480 bytes", size=14, fill=T.AMBER)
    canvas.text(40, 170, "正常路径  one application ends before 0x08010000", size=16, fill=T.GREEN, weight="700")
    canvas.rect(40, 184, 880, 150, fill=T.PANEL, stroke=T.GREEN, rx=8)
    canvas.text(56, 214, "bootloader 0x08000000, 16 KB, ends at 0x08004000", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 240, "parameters 0x08004000, 2 KB, ends at 0x08004800", size=14, fill=T.GREEN)
    canvas.text(56, 266, "one APP at 0x08004800, 0xB800, ends at 0x08010000", size=14, fill=T.TEXT)
    canvas.text(56, 292, "denominator 4096. Code 2048 is 1.65 V", size=13, fill=T.MUTED)
    canvas.text(40, 360, "失败路径  a second 0xB800 and a 65536-byte array", size=16, fill=T.RED, weight="700")
    canvas.rect(40, 374, 880, 130, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(56, 404, "16 + 2 + 46 + 46 = 110 KB, drawn out to 0x0801B800", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 430, "that end is outside this 64 KB", size=14, fill=T.RED)
    canvas.text(56, 456, "65536 bytes is larger than 20480 bytes of SRAM", size=14, fill=T.AMBER)
    canvas.rect(40, 524, 880, 140, fill=T.BG2, stroke=T.VIOLET, rx=8)
    canvas.text(56, 554, "旁注  denominator 4095 is the miss, not this path", size=15, fill=T.VIOLET, weight="700")
    canvas.text(56, 580, "133 bytes is an application frame, not one 64-byte USB packet", size=14, fill=T.TEXT)
    canvas.text(56, 606, "do not draw a motor pin. Do not draw a WS2812 waveform", size=14, fill=T.AMBER)
    canvas.text(56, 632, "chapter 12 does not have a second slot", size=13, fill=T.MUTED)
    _credit(canvas, "自绘。地图来自第 12 章。64 KB 与 20 KB 来自 DS5319。")
    return canvas


def main() -> None:
    out_dir = os.path.join(ROOT, "assets", "diagrams")
    os.makedirs(out_dir, exist_ok=True)
    boot_state().save(os.path.join(out_dir, "sample-00-boot-state.svg"))
    gpio_led().save(os.path.join(out_dir, "sample-03-gpio-led.svg"))
    exception_stack().save(os.path.join(out_dir, "sample-04-exception-stack.svg"))
    uart_frame().save(os.path.join(out_dir, "sample-06-uart-frame.svg"))
    clock_tree().save(os.path.join(out_dir, "sample-02-clock-tree.svg"))
    pwm_1khz().save(os.path.join(out_dir, "sample-05-pwm-1khz.svg"))
    spi_jedec().save(os.path.join(out_dir, "sample-08-spi-jedec.svg"))
    adc_sample().save(os.path.join(out_dir, "sample-09-adc-sar.svg"))
    swd_vectors().save(os.path.join(out_dir, "sample-01-swd-vectors.svg"))
    i2c_addr().save(os.path.join(out_dir, "sample-07-i2c-addr.svg"))
    dma_cndtr().save(os.path.join(out_dir, "sample-10-dma-cndtr.svg"))
    iwdg_1s().save(os.path.join(out_dir, "sample-11-iwdg-1s.svg"))
    iap_map().save(os.path.join(out_dir, "sample-12-iap-map.svg"))
    can_bit().save(os.path.join(out_dir, "sample-13-can-bit.svg"))
    usb_enum().save(os.path.join(out_dir, "sample-14-usb-enum.svg"))
    rtos_prio().save(os.path.join(out_dir, "sample-15-rtos-prio.svg"))
    stop_wake().save(os.path.join(out_dir, "sample-16-stop-wake.svg"))
    cfsr_read().save(os.path.join(out_dir, "sample-17-cfsr.svg"))
    boot_triage().save(os.path.join(out_dir, "sample-18-boot-triage.svg"))
    flash_fit().save(os.path.join(out_dir, "sample-19-flash-fit.svg"))


if __name__ == "__main__":
    main()

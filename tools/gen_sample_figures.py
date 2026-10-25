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
    canvas.rect(40, 86, 420, 250, fill=T.PANEL, stroke=T.CYAN, rx=10)
    canvas.text(56, 116, "STM32F103C8T6  LQFP48", size=16, fill=T.TEXT, weight="700")
    canvas.rect(56, 140, 150, 40, fill=T.BG2, stroke=T.GREEN, rx=6)
    canvas.text(68, 166, "10   PA0-WKUP", size=14, fill=T.GREEN, weight="700")
    canvas.rect(56, 196, 190, 40, fill=T.BG2, stroke=T.RED, rx=6)
    canvas.text(68, 222, "2   PC13-TAMPER-RTC", size=14, fill=T.RED, weight="700")
    canvas.text(56, 270, "PA0 推挽写 1：电流从脚流出", size=13, fill=T.GREEN)
    canvas.text(56, 296, "PC13 走电源开关，禁止作电流源", size=13, fill=T.RED)
    canvas.text(460, 108, "正常路径", size=16, fill=T.GREEN, weight="700")
    canvas.rect(460, 124, 460, 160, fill=T.PANEL, stroke=T.GREEN, rx=10)
    canvas.text(476, 154, "PA0 第 10 脚", size=14, fill=T.TEXT, weight="700")
    canvas.text(476, 180, "3.3 V → 推挽 PMOS → 270 Ω → LED → GND", size=13, fill=T.CYAN)
    canvas.text(476, 206, "R = (3.3 − 2.0) / 0.005 = 260 Ω，取 270 Ω", size=13, fill=T.TEXT)
    canvas.text(476, 232, "高 500 ms，低 500 ms，合起来 1 Hz", size=13, fill=T.MUTED)
    canvas.text(476, 256, "周期来自 HAL_Delay(500)，不是速度位", size=12, fill=T.MUTED)
    canvas.text(460, 316, "失败路径", size=16, fill=T.RED, weight="700")
    canvas.rect(460, 332, 460, 150, fill=T.PANEL, stroke=T.RED, rx=10)
    canvas.text(476, 362, "PC13 第 2 脚", size=14, fill=T.TEXT, weight="700")
    canvas.text(476, 388, "把 PA0「写 1 点灯」原样搬过来", size=13, fill=T.AMBER)
    canvas.text(476, 414, "灌电流上限 3 mA，不能作电流源", size=13, fill=T.RED)
    canvas.text(476, 440, "速度 ≤ 2 MHz，负载 ≤ 30 pF", size=13, fill=T.TEXT)
    canvas.text(476, 464, "25 mA / 50 MHz 对 PC13–PC15 作废", size=12, fill=T.MUTED)
    canvas.rect(40, 360, 400, 200, fill=T.BG2, stroke=T.VIOLET, rx=10)
    canvas.text(56, 390, "GPIOx_LCKR  偏移 0x18", size=14, fill=T.VIOLET, weight="700")
    canvas.text(56, 420, "LCK[15:0] 在序列中保持不变", size=13, fill=T.TEXT)
    canvas.text(56, 446, "LCKK：写 1，写 0，写 1", size=13, fill=T.TEXT)
    canvas.text(56, 472, "再读，确认读回 1，锁保持到复位", size=13, fill=T.TEXT)
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
        canvas.rect(left, 210, 80, 64, fill=T.PANEL, stroke=T.CYAN, rx=6)
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
    canvas.text(40, 86, "STM32F103C8T6  LQFP48  中密度", size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "pin 5 PD0  pin 6 PD1  HSE 8 MHz", size=14, fill=T.CYAN)
    canvas.text(40, 138, "PLLXTPRE=0  PLLSRC=1  PLLMUL=0111  8 x 9 = 72 MHz", size=14, fill=T.TEXT)
    canvas.text(40, 164, "SYSCLK = HCLK = 72 MHz    PCLK1 = 36 MHz    PCLK2 = 72 MHz", size=14, fill=T.AMBER)
    canvas.text(40, 190, "TIM2-TIM7 = 72 MHz    ADCCLK = 12 MHz    USBPRE=0  USBCLK = 48 MHz", size=14, fill=T.TEXT)
    canvas.text(40, 216, "正常路径  LATENCY=2    CSS 未触发    pin 29 PA8  MCO = PLL/2 = 36 MHz", size=15, fill=T.GREEN, weight="700")
    canvas.rect(40, 230, 880, 150, fill=T.PANEL, stroke=T.GREEN, rx=8)
    canvas.text(56, 258, "48 MHz 到 72 MHz 这一档 LATENCY=2", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 284, "0 到 24 MHz 是 0，24 到 48 MHz 是 1。电压档 2.7-3.6 V", size=14, fill=T.GREEN)
    canvas.text(56, 310, "MCO=111 送出 36 MHz，低于 50 MHz", size=14, fill=T.TEXT)
    canvas.text(56, 336, "RM0008 Rev 21 第 7.3.2 节。第 8.3.2 节在这颗料上作废", size=13, fill=T.MUTED)
    canvas.text(56, 360, "旁注：ADCPRE=01 得到 18 MHz，越过 14 MHz。MCO 直接送 72 MHz 也越过 50 MHz", size=13, fill=T.AMBER)
    canvas.text(40, 406, "失败路径  同一棵 x9 的树，LATENCY=0", size=16, fill=T.RED, weight="700")
    canvas.rect(40, 420, 880, 130, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(56, 450, "只把 PLL 改成 x9，LATENCY=0，取指失败", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 476, "HSE 停振：SYSCLK 回到 HSI 8 MHz，PLL 关掉", size=14, fill=T.RED)
    canvas.text(56, 502, "NMI 一直进来，直到软件写 CSSC", size=14, fill=T.AMBER)
    canvas.text(56, 528, "不把 18 MHz 和 72 MHz 的 MCO 再画成第三条完整的树", size=13, fill=T.MUTED)
    canvas.rect(40, 570, 880, 90, fill=T.BG2, stroke=T.VIOLET, rx=8)
    canvas.text(56, 600, "旁注  互联型第 8.3.2 节在 STM32F103C8T6 上作废", size=15, fill=T.VIOLET, weight="700")
    canvas.text(56, 626, "OTGFSPRE、PLLMUL 的 000x 保留、以及 x6.5，不写进这颗 C8", size=14, fill=T.TEXT)
    canvas.text(56, 650, "0111 仍是 x9，0000 仍是 x2。无源晶振不开 bypass", size=13, fill=T.MUTED)
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


if __name__ == "__main__":
    main()

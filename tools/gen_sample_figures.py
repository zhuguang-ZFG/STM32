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
        980,
        "中容量 1 KB 页；APP 从 0x08004800 起，长度 0xB800；跳转要装入第 0 字和第 1 字",
        "STM32F103C8T6 LQFP48 · RM0008 Rev 21 chapter 3",
    )
    canvas.header(tag="12", tag_color=T.CYAN)
    canvas.text(40, 86, "STM32F103C8T6  LQFP48  medium-density  64 KB", size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "1 KB pages. page 0 at 0x08000000. page 63 at 0x0800FC00", size=14, fill=T.CYAN)
    canvas.text(40, 138, "map ends before 0x08010000. 16 KB + 2 KB + 46 KB = 64 KB", size=14, fill=T.AMBER)
    canvas.text(40, 170, "正常路径  KEY1 then KEY2, then a half-word, then the two words", size=16, fill=T.GREEN, weight="700")
    canvas.rect(40, 184, 880, 170, fill=T.PANEL, stroke=T.GREEN, rx=8)
    canvas.text(56, 214, "write 0x45670123, then 0xCDEF89AB. LOCK clears", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 240, "program a half-word on an even address inside the APP", size=14, fill=T.GREEN)
    canvas.text(56, 266, "Bootloader 0x08000000, 16 KB, 16 pages, ends at 0x08004000", size=14, fill=T.TEXT)
    canvas.text(56, 292, "parameters 0x08004000, 2 KB, 2 pages, ends at 0x08004800", size=14, fill=T.TEXT)
    canvas.text(56, 318, "APP 0x08004800, 46 KB, 0xB800, ends at 0x08010000", size=14, fill=T.AMBER)
    canvas.text(56, 340, "MSP at 0x08004800. Reset_Handler at 0x08004804. VTOR = 0x08004800", size=13, fill=T.MUTED)
    canvas.text(40, 380, "失败路径  reversed keys, a last page past 64 KB, or VTOR left at 0", size=16, fill=T.RED, weight="700")
    canvas.rect(40, 394, 880, 130, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(56, 424, "KEY2 before KEY1 leaves LOCK set. The erase returns an error", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 450, "0x0801FC00 is outside this 64 KB", size=14, fill=T.RED)
    canvas.text(56, 476, "VTOR left at 0 still vectors interrupts into the bootloader", size=14, fill=T.AMBER)
    canvas.text(56, 502, "an erased half-word reads 0xFFFF. programming only turns 1 into 0", size=13, fill=T.MUTED)
    canvas.rect(40, 544, 880, 140, fill=T.BG2, stroke=T.VIOLET, rx=8)
    canvas.text(56, 574, "旁注  byte programming is void on this C8", size=15, fill=T.VIOLET, weight="700")
    canvas.text(56, 600, "0xA5 stays in chapter 01. This figure does not draw option bytes", size=14, fill=T.TEXT)
    canvas.text(56, 626, "USART on pin 30 PA9 and pin 31 PA10 is a side note, not a frame", size=14, fill=T.AMBER)
    canvas.text(56, 652, "do not draw system memory on this user-Flash map", size=13, fill=T.MUTED)
    _credit(canvas, "自绘。页和钥匙来自 RM0008 Rev 21 第 3 章；两字来自 PM0056。")
    return canvas


def can_bit() -> Svg:
    canvas = Svg(
        960,
        980,
        "36 MHz 下预分频 9、8 个时间份额是 500 kbit/s；预分频 8 和 10 个时间份额是 450 kbit/s；工作脚是第 45 脚和第 46 脚",
        "STM32F103C8T6 LQFP48 · RM0008 Rev 21 bxCAN",
    )
    canvas.header(tag="13", tag_color=T.CYAN)
    canvas.text(40, 86, "STM32F103C8T6  LQFP48  CAN1 on APB1  36 MHz", size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "pin 45 PB8 = CAN_RX    pin 46 PB9 = CAN_TX", size=14, fill=T.CYAN)
    canvas.text(40, 138, "MCU pins enter the transceiver. 120 ohm sits on CANH and CANL, at each end", size=14, fill=T.AMBER)
    canvas.text(40, 170, "正常路径  prescaler 9, eight quanta, 2 us, 500 kbit/s", size=16, fill=T.GREEN, weight="700")
    canvas.rect(40, 184, 880, 160, fill=T.PANEL, stroke=T.GREEN, rx=8)
    canvas.text(56, 214, "Tq = 250 ns. SYNC 1 + BS1 5 + BS2 2 = 8", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 240, "sample at 1.5 us, 75%. SJW = 1", size=14, fill=T.GREEN)
    canvas.text(56, 266, "8 x 250 ns = 2 us", size=14, fill=T.TEXT)
    canvas.text(56, 292, "the resistor is not tied to PB8 or PB9", size=14, fill=T.AMBER)
    canvas.text(56, 318, "two 120 ohm parts in parallel are a 60 ohm DC load, not a cable impedance", size=13, fill=T.MUTED)
    canvas.text(40, 370, "失败路径  prescaler 8, BS1 6, BS2 3, ten quanta, 450 kbit/s", size=16, fill=T.RED, weight="700")
    canvas.rect(40, 384, 880, 120, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(56, 414, "36e6 / (8 x 10) = 450 kbit/s. sample point 70%", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 440, "the bit is no longer 2 us", size=14, fill=T.RED)
    canvas.text(56, 466, "1 Mbit/s stays off this figure", size=14, fill=T.AMBER)
    canvas.rect(40, 524, 880, 150, fill=T.BG2, stroke=T.VIOLET, rx=8)
    canvas.text(56, 554, "旁注  pin 32 PA11 and pin 33 PA12 stay with USB", size=15, fill=T.VIOLET, weight="700")
    canvas.text(56, 580, "pin 5 PD0 and pin 6 PD1 exist. Remapping CAN there stops the HSE", size=14, fill=T.TEXT)
    canvas.text(56, 606, "pin 45 and pin 46 are not drawn as I2C at the same time", size=14, fill=T.AMBER)
    canvas.text(56, 632, "bus-off at 256 and 128 x 11 recessive bits stay in the table, not as a second waveform", size=13, fill=T.MUTED)
    canvas.text(56, 656, "do not draw the 4.7 kilohm I2C pull-ups on this figure", size=13, fill=T.MUTED)
    _credit(canvas, "自绘。位时间来自 RM0008 Rev 21 bxCAN；脚位来自 DS5319 Rev 20 表 5。")
    return canvas


def usb_enum() -> Svg:
    canvas = Svg(
        960,
        980,
        "全速要 48 MHz；D+ 上拉在第 33 脚；描述符是 18 字节设备加 67 字节配置集合，VID/PID 是 0x1209/0x0001",
        "STM32F103C8T6 LQFP48 · RM0008 Rev 21 USB device",
    )
    canvas.header(tag="14", tag_color=T.CYAN)
    canvas.text(40, 86, "STM32F103C8T6  LQFP48  USB device, not a host", size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "pin 32 PA11 = DM    pin 33 PA12 = DP", size=14, fill=T.CYAN)
    canvas.text(40, 138, "1.5 kilohm from 3.3 V to DP. USBPRE = 0. clock 48 MHz", size=14, fill=T.AMBER)
    canvas.text(40, 170, "正常路径  the host sees D+ pulled up", size=16, fill=T.GREEN, weight="700")
    canvas.rect(40, 184, 880, 170, fill=T.PANEL, stroke=T.GREEN, rx=8)
    canvas.text(56, 214, "device descriptor 18 bytes. bMaxPacketSize0 = 64", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 240, "VID/PID 0x1209/0x0001", size=14, fill=T.GREEN)
    canvas.text(56, 266, "configuration set length 67. wTotalLength 0x0043", size=14, fill=T.TEXT)
    canvas.text(56, 292, "bMaxPower 0x32 = 100 mA", size=14, fill=T.AMBER)
    canvas.text(56, 318, "full-speed bulk and interrupt ceiling is 64. notification endpoint 8 is allowed", size=13, fill=T.MUTED)
    canvas.text(40, 380, "失败路径  USBPRE = 1, the USB clock becomes 72 MHz", size=16, fill=T.RED, weight="700")
    canvas.rect(40, 394, 880, 110, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(56, 424, "the host fails while reading the descriptor", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 450, "72 / 1.5 is not applied", size=14, fill=T.RED)
    canvas.text(56, 476, "480 Mbit/s is void on this part", size=14, fill=T.AMBER)
    canvas.rect(40, 524, 880, 150, fill=T.BG2, stroke=T.VIOLET, rx=8)
    canvas.text(56, 554, "旁注  1.5 kilohm tied to DM is not this full-speed device", size=15, fill=T.VIOLET, weight="700")
    canvas.text(56, 580, "a bulk or interrupt wMaxPacketSize of 1023 is the wrong class", size=14, fill=T.TEXT)
    canvas.text(56, 606, "0x0483/0x5740 is not this repository descriptor", size=14, fill=T.AMBER)
    canvas.text(56, 632, "do not draw a CAN transceiver or ULPI on this figure", size=13, fill=T.MUTED)
    canvas.text(56, 656, "shared vector stays a side note: see the source card", size=13, fill=T.MUTED)
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
    canvas.text(40, 86, "STM32F103C8T6  Cortex-M3  no FPU  GROUP_4", size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "SysTick tick = 1 ms. HAL time base = TIM4, not SysTick", size=14, fill=T.CYAN)
    canvas.text(40, 138, "5 << 4 = 0x50. EXTI0 priority 5 may call FromISR", size=14, fill=T.AMBER)
    canvas.text(40, 170, "正常路径  task priority 2 runs, task priority 1 waits", size=16, fill=T.GREEN, weight="700")
    canvas.rect(40, 184, 880, 160, fill=T.PANEL, stroke=T.GREEN, rx=8)
    canvas.text(56, 214, "KEY is priority 2. LED and UART are priority 1", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 240, "LED stack 128 words = 512 bytes", size=14, fill=T.GREEN)
    canvas.text(56, 266, "EXTI0 preemption priority 5 may xQueueSendFromISR", size=14, fill=T.TEXT)
    canvas.text(56, 292, "the numeric task order is the opposite of NVIC", size=14, fill=T.AMBER)
    canvas.text(56, 318, "configTICK_RATE_HZ = 1000", size=13, fill=T.MUTED)
    canvas.text(40, 370, "失败路径  the same EXTI preemption priority is 0", size=16, fill=T.RED, weight="700")
    canvas.rect(40, 384, 880, 120, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(56, 414, "calling FromISR stops in configASSERT", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 440, "priority number 4 is also too urgent", size=14, fill=T.RED)
    canvas.text(56, 466, "NVIC number 0 is the most urgent interrupt", size=14, fill=T.AMBER)
    canvas.rect(40, 524, 880, 140, fill=T.BG2, stroke=T.VIOLET, rx=8)
    canvas.text(56, 554, "旁注  128 words is not 128 bytes", size=15, fill=T.VIOLET, weight="700")
    canvas.text(56, 580, "HAL left on SysTick makes HAL_Delay stick", size=14, fill=T.TEXT)
    canvas.text(56, 606, "task priority 1 is not ahead of task priority 2", size=14, fill=T.AMBER)
    canvas.text(56, 632, "do not draw the 8-register exception entry on this figure", size=13, fill=T.MUTED)
    _credit(canvas, "自绘。移位来自 FreeRTOS Kernel V11.3.2；栈和 TIM4 来自本仓库 freertos-task。")
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


if __name__ == "__main__":
    main()

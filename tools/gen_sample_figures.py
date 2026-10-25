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


def main() -> None:
    out_dir = os.path.join(ROOT, "assets", "diagrams")
    os.makedirs(out_dir, exist_ok=True)
    boot_state().save(os.path.join(out_dir, "sample-00-boot-state.svg"))
    gpio_led().save(os.path.join(out_dir, "sample-03-gpio-led.svg"))
    exception_stack().save(os.path.join(out_dir, "sample-04-exception-stack.svg"))
    uart_frame().save(os.path.join(out_dir, "sample-06-uart-frame.svg"))


if __name__ == "__main__":
    main()

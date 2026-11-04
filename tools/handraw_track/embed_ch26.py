# -*- coding: utf-8 -*-
"""Embed ch26 handraw knowledge-track PNGs (ZH+EN)."""
from embed import run

ZH = "docs/26-STM32F10x标准外设库SPL.md"
EN = "docs/en/26-spl.md"

run([
    (ZH, "spl-ownership-boundary.svg", "ch26-four-layers.png",
     "Handraw：SPL 四层边界（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。stm32f10x.h 管寄存器地址与位定义；外设头文件管结构体与声明；外设 .c 把字段写进寄存器；时钟、引脚、顺序、中断、超时、业务仍是你的工程的事；不是实拍。"),
    (ZH, "sample-26-file-matrix.svg", "ch26-defines.png",
     "Handraw：两个宏与 assert_param（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。STM32F10X_MD 按料号选密度；USE_STDPERIPH_DRIVER 引入 conf.h；assert_param 发布版通常不执行，不能替代运行时处理；不是实拍。"),
    (ZH, "spl-init-pipeline.svg", "ch26-init-steps.png",
     "Handraw：SPL 初始化四步（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。开时钟 → StructInit 默认值 → 覆盖字段 → 显式 Cmd 使能；函数名可能不同，回 RM0008 与头文件原型核对；不是实拍。"),
    (ZH, "sample-26-spl-hal-compare.svg", "ch26-spl-hal.png",
     "Handraw：HAL 与 SPL 入口对照（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。GPIO 时钟/配置、USART 收发、DMA 剩余项的 HAL 与 SPL V3.5.0 入口都落到同一组寄存器；只换函数名保留旧状态机最容易得到“能跑一会儿”的工程；不是实拍。"),
    (ZH, "sample-26-timeout-poll.svg", "ch26-timeout-poll.png",
     "Handraw：轮询自带超时（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。USART_SendData() 只写 DR，等 TXE 的循环要自己写 spin_limit 或可靠时基截止时间，并定义恢复动作；不是实拍。"),

    (EN, "spl-ownership-boundary.svg", "ch26-four-layers.png",
     "Handraw: SPL four layers (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). stm32f10x.h holds register addresses and bits; peripheral headers hold structs and declarations; peripheral .c files write registers; clock, pins, order, IRQ, timeout and business logic remain your job; not a photo."),
    (EN, "sample-26-file-matrix.svg", "ch26-defines.png",
     "Handraw: two defines and assert_param (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). STM32F10X_MD selects the density for the exact part; USE_STDPERIPH_DRIVER pulls in conf.h; assert_param is usually compiled out in release and never replaces runtime fault handling; not a photo."),
    (EN, "spl-init-pipeline.svg", "ch26-init-steps.png",
     "Handraw: SPL init four steps (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). Enable clock → StructInit defaults → overwrite fields → explicit Cmd enable; function names vary, check the header prototype and RM0008; not a photo."),
    (EN, "sample-26-spl-hal-compare.svg", "ch26-spl-hal.png",
     "Handraw: HAL vs SPL entries (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). HAL and SPL entries for GPIO clock/config, USART data, and DMA counter land on the same registers; swapping names while keeping the old state machine yields a “works for a while” project; not a photo."),
    (EN, "sample-26-timeout-poll.svg", "ch26-timeout-poll.png",
     "Handraw: polling with its own timeout (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). USART_SendData() only writes DR; the TXE wait needs your own spin limit or a solid timebase deadline plus a recovery action; not a photo."),
])

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 assets/diagrams/*.svg —— 静态框图（架构、工程结构、总线、优先级）。"""

from __future__ import annotations

from svgkit import Svg, T

W, H = 900, 560


def layers_hal_ll_reg() -> Svg:
    s = Svg(W, H, "四种代码风格的分层关系",
            "寄存器 / LL / HAL / 应用：抽象越高越通用，越低越省资源")
    s.header(tag="架构", tag_color=T.VIOLET)

    layers = [
        ("应用 / 业务逻辑", "你的 main.c、状态机、协议解析", T.PINK),
        ("HAL 库", "HAL_GPIO_Init / HAL_UART_Transmit …（可移植性最好）", T.CYAN),
        ("LL 库", "LL_GPIO_SetOutputPin / LL_TIM_EnableCounter …（轻量、贴近寄存器）", T.GREEN),
        ("寄存器", "GPIOA->BSRR = GPIO_PIN_5（CMSIS 定义，最快最省）", T.AMBER),
        ("外设硬件", "GPIO / TIM / USART / SPI / ADC … 硅片上的电路", T.RED),
    ]
    y = 92
    for name, note, color in layers:
        s.rect(40, y, 470, 62, fill=T.PANEL, stroke=color, rx=10)
        s.rect(40, y, 5, 62, fill=color, rx=3)
        s.text(60, y + 27, name, size=14, fill=T.TEXT, weight="700")
        s.text(60, y + 47, note, size=10.5, fill=T.MUTED)
        y += 72
    s.double_arrow(524, 92, 524, 452, color=T.STROKE, sw=1.6)
    s.text(540, 270, "抽象层次提高 →", size=11, fill=T.MUTED)

    s.rect(600, 92, 260, 150, fill=T.PANEL2, stroke=T.STROKE, rx=12)
    s.text(618, 118, "怎么选？", size=13, fill=T.TEXT, weight="700")
    s.code(618, 140, [
        "学习 / 做项目：HAL + CubeMX",
        "资源紧张：关键路径用 LL",
        "极致性能：直接写寄存器",
        "看懂底层：对照 RM 读寄存器",
    ], size=10, lh=18, color=T.GREEN)

    s.rect(600, 258, 260, 194, fill=T.BG2, stroke=T.STROKE, rx=12)
    s.text(618, 284, "性能对照（72 MHz 下）", size=12.5, fill=T.TEXT, weight="700")
    rows = [("HAL_GPIO_TogglePin", "≈ 40 周期"),
            ("LL_GPIO_TogglePin", "≈ 10 周期"),
            ("GPIOA->BSRR = ...", "≈ 2 周期"),
            ("中断响应（硬件）", "12 周期"),
            ("DMA 搬 1 字节", "0 周期（不占 CPU）")]
    for i, (k, v) in enumerate(rows):
        yy = 308 + i * 24
        s.text(618, yy, k, size=10.5, mono=True, fill=T.CYAN)
        s.text(842, yy, v, size=10.5, fill=T.MUTED, anchor="end")

    s.rect(40, 468, 820, 62, fill=T.BG2, stroke=T.STROKE, rx=10)
    s.text(58, 492, "三者可以混用", size=12.5, fill=T.TEXT, weight="700")
    s.text(58, 512, "CubeMX 生成的工程本身就是「HAL 初始化 + LL/寄存器加速」的混合体；"
                    "不要因为「用了库」就觉得不底层。", size=11, fill=T.MUTED)
    s.footer("结论：先用 HAL 把功能跑通，再用 DWT 测出瓶颈，最后只优化瓶颈处的几行代码")
    return s


def project_structure() -> Svg:
    s = Svg(W, H, "一个标准 STM32 工程长什么样",
            "CubeMX + Makefile / Keil / CubeIDE 生成的结构基本一致")
    s.header(tag="工程结构", tag_color=T.CYAN)

    tree = [
        (0, "MyProject/", T.TEXT, True),
        (1, "MyProject.ioc", T.AMBER, False),
        (1, "Core/", T.CYAN, True),
        (2, "Inc/  main.h · stm32f1xx_hal_conf.h · stm32f1xx_it.h", T.MUTED, False),
        (2, "Src/  main.c · stm32f1xx_it.c · stm32f1xx_hal_msp.c", T.MUTED, False),
        (1, "Drivers/", T.GREEN, True),
        (2, "STM32F1xx_HAL_Driver/  HAL 外设驱动（只读，别改）", T.MUTED, False),
        (2, "CMSIS/  Device/ 内核定义与 startup_stm32f103xb.s", T.MUTED, False),
        (1, "Middlewares/", T.VIOLET, True),
        (2, "Third_Party/FreeRTOS / FatFs / USB_Device …", T.MUTED, False),
        (1, "BSP/  （自己写）", T.PINK, True),
        (2, "led.c/.h · key.c/.h · oled.c/.h · delay.c/.h", T.MUTED, False),
        (1, "MDK-ARM/ 或 build/", T.ORANGE, True),
        (2, "链接脚本 STM32F103C8Tx_FLASH.ld、输出 .hex/.bin", T.MUTED, False),
        (1, "Makefile / CMakeLists.txt", T.RED, False),
        (1, ".mxproject · .gitignore · README.md", T.DIM, False),
    ]
    y = 92
    for depth, text_, color, bold in tree:
        x = 40 + depth * 28
        if depth:
            s.line(x - 14, y - 5, x - 14, y + 5, stroke=T.STROKE, sw=1.2)
            s.line(x - 14, y, x - 4, y, stroke=T.STROKE, sw=1.2)
        s.text(x, y, text_, size=11.5 if depth else 13, fill=color,
               mono=depth > 0, weight="700" if bold else "normal")
        y += 26

    s.rect(520, 92, 340, 210, fill=T.PANEL, stroke=T.STROKE, rx=12)
    s.text(538, 118, "四条铁律", size=13, fill=T.TEXT, weight="700")
    s.code(538, 142, [
        "1. 不要修改 Drivers/ 里的 HAL 源码",
        "   （升级 CubeMX 时会被覆盖）",
        "2. 自己的外设驱动统一放 BSP/",
        "3. 中断服务函数只写在 it.c 里",
        "4. .ioc 要提交到 Git，build/ 不要",
    ], size=10.5, lh=19, color=T.GREEN)

    s.rect(520, 316, 340, 136, fill=T.BG2, stroke=T.STROKE, rx=12)
    s.text(538, 342, "编译产物", size=13, fill=T.TEXT, weight="700")
    rows = [(".elf", "带调试信息，用于下载/仿真"),
            (".hex", "Intel HEX，文本格式，含地址"),
            (".bin", "纯二进制，用于 IAP/OTA"),
            (".map", "各段大小，排查 RAM 溢出必看")]
    for i, (k, v) in enumerate(rows):
        yy = 366 + i * 22
        s.text(538, yy, k, size=10.5, mono=True, fill=T.AMBER)
        s.text(578, yy, v, size=10.5, fill=T.MUTED)

    s.rect(40, 480, 820, 50, fill=T.BG2, stroke=T.STROKE, rx=10)
    s.text(58, 510, "小技巧：把 BSP 目录做成 Git 子模块或独立仓库，"
                    "换芯片时只需改初始化，业务代码可整体复用。", size=11,
           fill=T.MUTED)
    s.footer("完整示例见 examples/ 目录，每个示例都给出 CubeMX 配置要点与文件清单")
    return s


def peripheral_bus() -> Svg:
    s = Svg(W, H, "外设挂在哪条总线上（以 STM32F411 为例）",
            "AHB/APB 分频决定外设能跑多快，也决定波特率、PWM 频率的上限")
    s.header(tag="总线", tag_color=T.GREEN)

    s.rect(40, 88, 180, 60, fill=T.PANEL, stroke=T.CYAN, rx=10)
    s.text(130, 112, "SYSCLK", size=14, anchor="middle", fill=T.TEXT,
           weight="700")
    s.text(130, 132, "100 MHz", size=11, anchor="middle", fill=T.CYAN)

    s.arrow(222, 118, 300, 118, color=T.CYAN, sw=2.4)
    s.rect(302, 88, 200, 60, fill=T.PANEL, stroke=T.BLUE, rx=10)
    s.text(402, 112, "AHB 总线", size=14, anchor="middle", fill=T.TEXT,
           weight="700")
    s.text(402, 132, "HCLK = 100 MHz（÷1）", size=11, anchor="middle",
           fill=T.BLUE)

    s.arrow(402, 150, 402, 174, color=T.BLUE, sw=2.2)
    s.rect(302, 176, 200, 50, fill=T.PANEL2, stroke=T.BLUE, rx=10)
    s.text(402, 206, "AHB1 / AHB2", size=12.5, anchor="middle", fill=T.BLUE)
    ahb = ["GPIOA~H", "DMA1/2", "CRC / RNG", "USB OTG FS", "FSMC", "DCMI"]
    for i, n in enumerate(ahb):
        x = 40 + (i % 3) * 176
        y = 250 + (i // 3) * 38
        s.rect(x, y, 160, 30, fill=T.PANEL, stroke=T.STROKE, rx=8)
        s.text(x + 80, y + 20, n, size=11, anchor="middle", fill=T.CYAN)
    s.line(300, 202, 300, 232, stroke=T.BLUE, sw=1.6, dash="4 5")
    s.line(120, 232, 646, 232, stroke=T.BLUE, sw=1.6, dash="4 5")
    s.line(120, 232, 120, 250, stroke=T.BLUE, sw=1.6, dash="4 5")
    s.line(646, 232, 646, 250, stroke=T.BLUE, sw=1.6, dash="4 5")

    s.arrow(504, 118, 600, 118, color=T.GREEN, sw=2.4)
    s.rect(602, 88, 258, 60, fill=T.PANEL, stroke=T.GREEN, rx=10)
    s.text(731, 112, "APB1 / APB2", size=14, anchor="middle", fill=T.TEXT,
           weight="700")
    s.text(731, 132, "PCLK1 = 50 MHz · PCLK2 = 100 MHz", size=10.5,
           anchor="middle", fill=T.GREEN)

    apb1 = ["USART2/3", "I2C1/2/3", "SPI2/3", "TIM2~5", "CAN1", "USB 48M"]
    apb2 = ["USART1/6", "SPI1", "ADC1", "TIM1/9/10/11", "SDIO", "SYSCFG"]
    s.text(602, 194, "APB1（最高 50 MHz）", size=12, fill=T.VIOLET, weight="700")
    s.text(602, 338, "APB2（最高 100 MHz）", size=12, fill=T.PINK, weight="700")
    for i, n in enumerate(apb1):
        x = 602 + (i % 2) * 132
        y = 204 + (i // 2) * 34
        s.rect(x, y, 126, 28, fill=T.PANEL2, stroke=T.STROKE, rx=7)
        s.text(x + 63, y + 19, n, size=10.5, anchor="middle", fill=T.VIOLET)
    for i, n in enumerate(apb2):
        x = 602 + (i % 2) * 132
        y = 348 + (i // 2) * 34
        s.rect(x, y, 126, 28, fill=T.PANEL2, stroke=T.STROKE, rx=7)
        s.text(x + 63, y + 19, n, size=10.5, anchor="middle", fill=T.PINK)

    s.rect(40, 348, 520, 160, fill=T.BG2, stroke=T.STROKE, rx=10)
    s.text(58, 374, "为什么必须记住总线？", size=12.5, fill=T.TEXT, weight="700")
    notes = [
        "① 波特率算错：USART2 在 APB1（50 MHz），USART1 在 APB2（100 MHz）",
        "② PWM 频率上限：TIM2 挂 APB1，但定时器时钟有 ×2 倍频（50→100 MHz）",
        "③ 超频红线：APB1 不能超 50 MHz，APB2 不能超 100 MHz",
        "④ ADC 时钟：由 APB2 分频，F4 最高 36 MHz，超过则采样不准",
        "⑤ 时钟使能宏（__HAL_RCC_*_CLK_ENABLE）忘记调用 = 外设完全没反应",
    ]
    for i, n in enumerate(notes):
        s.text(58, 398 + i * 22, n, size=10.5, fill=T.MUTED)

    s.rect(560, 462, 300, 46, fill=T.PANEL, stroke=T.STROKE, rx=10)
    s.text(578, 482, "查表工具", size=11.5, fill=T.TEXT, weight="700")
    s.text(578, 500, "cheatsheets/外设总线与引脚速查表.md", size=10,
           fill=T.CYAN, mono=True)
    s.footer("数据来源：RM0383（F411 参考手册）「Reset and clock control」框图")
    return s




def interrupt_priority() -> Svg:
    s = Svg(W, H, "抢占优先级与中断嵌套",
            "同抢占优先级不能互相打断；数值越小优先级越高")
    s.header(tag="中断优先级", tag_color=T.VIOLET)

    s.axis(80, 110, 780, 200, ylabel="CPU 执行", xlabel="时间 →")
    rows = [("主循环", T.MUTED, 0), ("IRQ A（抢占 1）", T.CYAN, 1),
            ("IRQ B（抢占 2）", T.AMBER, 2)]
    for i, (name, color, _) in enumerate(rows):
        s.text(74, 152 + i * 50, name, size=11, anchor="end", fill=color)

    seg = [
        (0, 90, "主循环", T.MUTED, 0),
        (90, 60, "A", T.CYAN, 1),
        (150, 50, "B", T.AMBER, 2),
        (200, 60, "A 继续", T.CYAN, 1),
        (260, 120, "主循环", T.MUTED, 0),
        (380, 70, "B", T.AMBER, 2),
        (450, 90, "A", T.CYAN, 1),
        (540, 240, "主循环", T.MUTED, 0),
    ]
    for x, w, label, color, row in seg:
        s.rect(80 + x, 130 + row * 50, w, 32, fill=color, rx=6, opacity=0.85)
        s.text(80 + x + w / 2, 151 + row * 50, label, size=10.5,
               anchor="middle", fill="#0b1220", weight="700")
    for x, txt in ((90, "A 触发"), (150, "B 抢占 A"), (200, "B 返回"),
                   (380, "B 触发")):
        s.line(80 + x, 112, 80 + x, 330, stroke=T.STROKE, sw=1, dash="3 4")
        s.text(80 + x, 106, txt, size=9.5, anchor="middle", fill=T.DIM)

    s.rect(40, 350, 400, 156, fill=T.PANEL, stroke=T.STROKE, rx=12)
    s.text(58, 376, "优先级分组表", size=12.5, fill=T.TEXT, weight="700")
    rows2 = [("GROUP_0", "0 位抢占 / 4 位子优先级", "几乎不嵌套"),
             ("GROUP_2", "2 位抢占 / 2 位子优先级", "最常用"),
             ("GROUP_4", "4 位抢占 / 0 位子优先级", "只用抢占，最直观"),
             ("数值范围", "0（最高）~ 15（最低）", "HAL_NVIC_SetPriority")]
    for i, (k, v, note) in enumerate(rows2):
        yy = 402 + i * 26
        s.text(58, yy, k, size=10.5, mono=True, fill=T.CYAN)
        s.text(158, yy, v, size=10.5, fill=T.TEXT)
        s.text(322, yy, note, size=9.5, fill=T.MUTED)

    s.rect(460, 350, 400, 156, fill=T.BG2, stroke=T.STROKE, rx=12)
    s.text(478, 376, "常见错误", size=12.5, fill=T.TEXT, weight="700")
    errs = [
        "在 ISR 里调用 HAL_Delay（死等，因为 SysTick 优先级更低）",
        "忘记清中断标志 → 出中断立刻又进，表现为程序卡死",
        "把 EXTI 优先级设得比 DMA 低，导致数据被覆盖",
        "在 ISR 里做耗时运算（浮点、printf）导致丢中断",
        "FreeRTOS 中改优先级后忘记同步 configMAX_SYSCALL_INTERRUPT_PRIORITY",
    ]
    for i, e in enumerate(errs):
        s.text(478, 400 + i * 21, "· " + e, size=10, fill=T.MUTED)
    s.footer("抢占优先级相同的中断不能互相打断，只能排队；子优先级只决定排队顺序")
    return s


ALL = [layers_hal_ll_reg, project_structure, peripheral_bus, interrupt_priority]

NAMES = {
    "layers_hal_ll_reg": "layers-hal-ll-reg",
    "project_structure": "project-structure",
    "peripheral_bus": "peripheral-bus",
    "interrupt_priority": "interrupt-priority",
}

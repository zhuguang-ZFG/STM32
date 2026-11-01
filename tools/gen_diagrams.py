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
        s.rect(40, y, 470, 62, fill=T.PANEL, stroke=color, rx=8)
        s.rect(40, y, 5, 62, fill=color, rx=2)
        s.text(60, y + 27, name, size=14, fill=T.TEXT, weight="700")
        s.text(60, y + 47, note, size=10.5, fill=T.MUTED)
        y += 72
    s.double_arrow(524, 92, 524, 452, color=T.STROKE, sw=1.5)
    s.text(540, 270, "抽象层次提高 →", size=11, fill=T.MUTED)

    s.rect(600, 92, 260, 150, fill=T.PANEL2, stroke=T.STROKE, rx=8)
    s.text(618, 118, "怎么选？", size=13, fill=T.TEXT, weight="700")
    s.code(618, 140, [
        "学习 / 做项目：HAL + CubeMX",
        "资源紧张：关键路径用 LL",
        "极致性能：直接写寄存器",
        "看懂底层：对照 RM 读寄存器",
    ], size=10, lh=18, color=T.GREEN)

    s.rect(600, 258, 260, 194, fill=T.BG2, stroke=T.STROKE, rx=8)
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

    s.rect(40, 468, 820, 62, fill=T.BG2, stroke=T.STROKE, rx=8)
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
            s.line(x - 14, y - 5, x - 14, y + 5, stroke=T.STROKE, sw=1)
            s.line(x - 14, y, x - 4, y, stroke=T.STROKE, sw=1)
        s.text(x, y, text_, size=11.5 if depth else 13, fill=color,
               mono=depth > 0, weight="700" if bold else "normal")
        y += 26

    s.rect(520, 92, 340, 210, fill=T.PANEL, stroke=T.STROKE, rx=8)
    s.text(538, 118, "四条铁律", size=13, fill=T.TEXT, weight="700")
    s.code(538, 142, [
        "1. 不要修改 Drivers/ 里的 HAL 源码",
        "   （升级 CubeMX 时会被覆盖）",
        "2. 自己的外设驱动统一放 BSP/",
        "3. 中断服务函数只写在 it.c 里",
        "4. .ioc 要提交到 Git，build/ 不要",
    ], size=10.5, lh=19, color=T.GREEN)

    s.rect(520, 316, 340, 136, fill=T.BG2, stroke=T.STROKE, rx=8)
    s.text(538, 342, "编译产物", size=13, fill=T.TEXT, weight="700")
    rows = [(".elf", "带调试信息，用于下载/仿真"),
            (".hex", "Intel HEX，文本格式，含地址"),
            (".bin", "纯二进制，用于 IAP/OTA"),
            (".map", "各段大小，排查 RAM 溢出必看")]
    for i, (k, v) in enumerate(rows):
        yy = 366 + i * 22
        s.text(538, yy, k, size=10.5, mono=True, fill=T.AMBER)
        s.text(578, yy, v, size=10.5, fill=T.MUTED)

    s.rect(40, 480, 820, 50, fill=T.BG2, stroke=T.STROKE, rx=8)
    s.text(58, 510, "小技巧：把 BSP 目录做成 Git 子模块或独立仓库，"
                    "换芯片时只需改初始化，业务代码可整体复用。", size=11,
           fill=T.MUTED)
    s.footer("完整示例见 examples/ 目录，每个示例都给出 CubeMX 配置要点与文件清单")
    return s


def peripheral_bus() -> Svg:
    s = Svg(W, H, "外设挂在哪条总线上（以 STM32F411 为例）",
            "AHB/APB 分频决定外设能跑多快，也决定波特率、PWM 频率的上限")
    s.header(tag="总线", tag_color=T.GREEN)

    s.rect(40, 88, 180, 60, fill=T.PANEL, stroke=T.CYAN, rx=8)
    s.text(130, 112, "SYSCLK", size=14, anchor="middle", fill=T.TEXT,
           weight="700")
    s.text(130, 132, "100 MHz", size=11, anchor="middle", fill=T.CYAN)

    s.arrow(222, 118, 300, 118, color=T.CYAN, sw=2)
    s.rect(302, 88, 200, 60, fill=T.PANEL, stroke=T.BLUE, rx=8)
    s.text(402, 112, "AHB 总线", size=14, anchor="middle", fill=T.TEXT,
           weight="700")
    s.text(402, 132, "HCLK = 100 MHz（÷1）", size=11, anchor="middle",
           fill=T.BLUE)

    s.arrow(402, 150, 402, 174, color=T.BLUE, sw=2)
    s.rect(302, 176, 200, 50, fill=T.PANEL2, stroke=T.BLUE, rx=8)
    s.text(402, 206, "AHB1 / AHB2", size=12.5, anchor="middle", fill=T.BLUE)
    ahb = ["GPIOA~H", "DMA1/2", "CRC / RNG", "USB OTG FS", "FSMC", "DCMI"]
    for i, n in enumerate(ahb):
        x = 40 + (i % 3) * 176
        y = 250 + (i // 3) * 38
        s.rect(x, y, 160, 30, fill=T.PANEL, stroke=T.STROKE, rx=8)
        s.text(x + 80, y + 20, n, size=11, anchor="middle", fill=T.CYAN)
    s.line(300, 202, 300, 232, stroke=T.BLUE, sw=1.5, dash="4 5")
    s.line(120, 232, 646, 232, stroke=T.BLUE, sw=1.5, dash="4 5")
    s.line(120, 232, 120, 250, stroke=T.BLUE, sw=1.5, dash="4 5")
    s.line(646, 232, 646, 250, stroke=T.BLUE, sw=1.5, dash="4 5")

    s.arrow(504, 118, 600, 118, color=T.GREEN, sw=2)
    s.rect(602, 88, 258, 60, fill=T.PANEL, stroke=T.GREEN, rx=8)
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
        s.rect(x, y, 126, 28, fill=T.PANEL2, stroke=T.STROKE, rx=4)
        s.text(x + 63, y + 19, n, size=10.5, anchor="middle", fill=T.VIOLET)
    for i, n in enumerate(apb2):
        x = 602 + (i % 2) * 132
        y = 348 + (i // 2) * 34
        s.rect(x, y, 126, 28, fill=T.PANEL2, stroke=T.STROKE, rx=4)
        s.text(x + 63, y + 19, n, size=10.5, anchor="middle", fill=T.PINK)

    s.rect(40, 348, 520, 160, fill=T.BG2, stroke=T.STROKE, rx=8)
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

    s.rect(560, 462, 300, 46, fill=T.PANEL, stroke=T.STROKE, rx=8)
    s.text(578, 482, "查表工具", size=11.5, fill=T.TEXT, weight="700")
    s.text(578, 500, "cheatsheets/外设总线与引脚速查表.md", size=10,
           fill=T.CYAN, mono=True)
    s.footer("数据来源：RM0383（F411 参考手册）「Reset and clock control」框图")
    return s




def interrupt_priority() -> Svg:
    s = Svg(W, H, "抢占优先级与中断嵌套",
            "图中 A 的抢占号是 1，B 是 2；数字越小越先打断")
    s.header(tag="中断优先级", tag_color=T.VIOLET)

    s.axis(80, 110, 780, 200, ylabel="CPU 执行", xlabel="时间 →")
    rows = [("主循环", T.MUTED, 0), ("IRQ A", T.CYAN, 1),
            ("IRQ B", T.AMBER, 2)]
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
        s.rect(80 + x, 130 + row * 50, w, 32, fill=color, rx=4, opacity=0.85)
        s.text(80 + x + w / 2, 151 + row * 50, label, size=10.5,
               anchor="middle", fill="#fbfaf7", weight="700")
    for x, txt in ((90, "A 触发"), (150, "B 抢占 A"), (200, "B 返回"),
                   (380, "B 触发")):
        s.line(80 + x, 112, 80 + x, 330, stroke=T.STROKE, sw=1, dash="3 4")
        s.text(80 + x, 106, txt, size=9.5, anchor="middle", fill=T.DIM)

    s.rect(40, 350, 400, 156, fill=T.PANEL, stroke=T.STROKE, rx=8)
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

    s.rect(460, 350, 400, 156, fill=T.BG2, stroke=T.STROKE, rx=8)
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




def l4_idd_bench() -> Svg:
    s = Svg(W, H, "NUCLEO-L476RG：JP6 IDD 动态功耗测量接线",
            "电流通道串入 JP6；电压通道直接测 MCU 端 VDD；两条线必须同时记录")
    s.header(tag="24 L4 测量", tag_color=T.GREEN)

    # 左：电源与功耗仪
    s.rect(40, 112, 170, 126, fill=T.PANEL, stroke=T.GREEN, rx=8)
    s.text(125, 142, "动态功耗仪", size=14, anchor="middle", fill=T.TEXT, weight="700")
    s.text(125, 168, "SOURCE 3.3 V", size=11, anchor="middle", mono=True, fill=T.GREEN)
    s.text(125, 190, "I(t) 高速采样", size=11, anchor="middle", mono=True, fill=T.CYAN)
    s.text(125, 214, "记录 burden / range", size=9.5, anchor="middle", fill=T.MUTED)

    # 中：JP6 断点
    s.arrow(214, 164, 330, 164, color=T.GREEN, sw=2, head=7)
    s.text(270, 151, "电流路径", size=10, anchor="middle", fill=T.GREEN)
    s.circle(348, 164, 9, fill=T.BG2, stroke=T.AMBER, sw=2)
    s.circle(392, 164, 9, fill=T.BG2, stroke=T.AMBER, sw=2)
    s.line(357, 164, 383, 142, stroke=T.RED, sw=2)
    s.text(370, 122, "JP6 (IDD) 拔下", size=11.5, anchor="middle", fill=T.AMBER,
           weight="700")
    s.arrow(401, 164, 484, 164, color=T.GREEN, sw=2, head=7)

    # 右：Nucleo 目标区
    s.rect(486, 92, 374, 238, fill="#123a2e", stroke="#0d2b22", rx=8)
    s.rect(500, 108, 346, 68, fill="#0d2b22", stroke="#8b98b0", rx=8)
    s.text(673, 134, "ST-LINK 区", size=13, anchor="middle", fill="#dfe6f0", weight="700")
    s.text(673, 158, "功能调试可接；功耗测量需排查回灌", size=9.5,
           anchor="middle", fill="#e2b23c")
    s.rect(500, 190, 346, 122, fill="#123057", stroke="#7aa2ff", rx=8)
    s.text(673, 216, "目标 MCU 供电域", size=13, anchor="middle", fill="#dfe6f0",
           weight="700")
    s.rect(620, 236, 106, 52, fill="#151922", stroke="#808a9a", rx=4)
    s.text(673, 260, "STM32L476RG", size=10.5, anchor="middle", mono=True,
           fill="#dfe6f0", weight="700")
    s.text(673, 279, "VDD / VSS", size=9, anchor="middle", mono=True, fill="#8b98b0")

    # 电压 sense 独立通道
    s.rect(40, 278, 170, 98, fill=T.BG2, stroke=T.CYAN, rx=8)
    s.text(125, 307, "电压通道", size=13, anchor="middle", fill=T.TEXT, weight="700")
    s.text(125, 332, "VDD at MCU", size=11, anchor="middle", mono=True, fill=T.CYAN)
    s.text(125, 354, "同步观察压降/复位", size=9.5, anchor="middle", fill=T.MUTED)
    s.line(210, 326, 580, 326, stroke=T.CYAN, sw=2)
    s.arrow(580, 326, 620, 280, color=T.CYAN, sw=2, head=7)
    s.line(210, 350, 760, 350, stroke=T.MUTED, sw=2, dash="5 6")
    s.arrow(760, 350, 726, 280, color=T.MUTED, sw=2, head=6)

    s.rect(40, 404, 820, 92, fill=T.PANEL, stroke=T.STROKE, rx=8)
    s.text(58, 430, "测量前四项断言", size=12.5, fill=T.TEXT, weight="700")
    notes = [
        "① JP6 已拔：电流只经过仪器，不跨接跳线",
        "② MCU 端 VDD 在活动峰值期间仍高于允许下限",
        "③ SWD/USB/外设 GPIO 不形成旁路或反向供电",
        "④ 采样率 >= 10 / t_min，至少捕获 10 个完整周期",
    ]
    for i, note in enumerate(notes):
        x = 58 + (i % 2) * 400
        y = 454 + (i // 2) * 23
        s.text(x, y, note, size=10.2, fill=T.MUTED)
    s.footer("静态 µA 平台 + 唤醒电荷积分 + MCU 端 VDD，三项缺一不可")
    return s




def network_debug_ladder() -> Svg:
    s = Svg(W, H, "STM32 网络排错阶梯：在哪一层第一次偏离？",
            "每次只验证一层；下层证据没成立，不要继续改上层协议参数")
    s.header(tag="27 网络排错", tag_color=T.CYAN)

    rows = [
        ("L1", "PHY / RMII", "link=1 · 50 MHz REF_CLK · MDIO 可读", "示波器 + PHY BSR", T.ORANGE),
        ("L2", "Ethernet / ARP", "本机发 ARP，能收到目标 MAC", "Wireshark: arp", T.BLUE),
        ("L3", "IPv4 / ICMP", "IP/掩码/网关正确，同网段可 ping", "ipconfig · ping", T.CYAN),
        ("L4", "UDP / TCP", "端口可达；TCP 完成三次握手", "Wireshark: tcp.flags.syn", T.GREEN),
        ("L5", "DNS / TLS", "DNS 得到预期地址；证书链与主机名通过", "nslookup · TLS error", T.AMBER),
        ("L7", "HTTP / MQTT", "状态码/CONNACK/QoS 与业务序号可追踪", "curl · mosquitto_sub", T.VIOLET),
    ]
    x0, y0, row_h = 44, 94, 62
    for i, (level, name, assertion, evidence, color) in enumerate(rows):
        y = y0 + i * row_h
        s.rect(x0, y, 812, 50, fill=T.PANEL if i % 2 == 0 else T.BG2,
               stroke=color, rx=8)
        s.rect(x0, y, 54, 50, fill=color, rx=8)
        s.text(x0 + 27, y + 30, level, size=12, anchor="middle", fill=T.BG,
               weight="800", mono=True)
        s.text(116, y + 21, name, size=11.5, fill=color, weight="700")
        s.text(116, y + 40, assertion, size=9.7, fill=T.MUTED)
        s.rect(626, y + 9, 210, 32, fill=T.BG, stroke=T.STROKE, rx=4)
        s.text(731, y + 29, evidence, size=9.2, anchor="middle", mono=True,
               fill=T.TEXT)
        if i < len(rows) - 1:
            s.arrow(72, y + 52, 72, y + row_h - 2, color=T.MUTED, sw=2,
                    head=5)

    s.rect(44, 478, 812, 48, fill=T.BG2, stroke=T.RED, rx=8)
    s.text(62, 499, "止损规则", size=11.5, fill=T.RED, weight="700")
    s.text(126, 499, "第一次失败层就是当前边界：保留 PCAP、寄存器/错误码和配置快照，再改一个变量",
           size=10, fill=T.TEXT)
    s.text(126, 517, "不要用“重启后偶尔能通”替代可重复证据；不要在 ping 不通时先调 MQTT keepalive",
           size=9.4, fill=T.MUTED)
    s.footer("link → ARP → IP → TCP/UDP → DNS/TLS → 应用协议；自下而上，逐层留证据")
    return s


def spl_ownership_boundary() -> Svg:
    """SPL、HAL 与寄存器的所有权边界，而不是函数名替换表。"""
    s = Svg(W, H, "HAL 与 SPL 最终写的是同一组寄存器",
            "一条外设实例只能有一个初始化与恢复所有者；混用读接口可以，双重接管不可以")
    s.header(tag="26 SPL · IG-012", tag_color=T.CYAN)

    lanes = [
        ("HAL 路径", "Handle + 状态 + 回调", "HAL_UART_Init", T.VIOLET),
        ("SPL 路径", "InitStruct + 直接函数", "USART_Init", T.GREEN),
        ("寄存器边界", "BRR / CR1 / CR2 / CR3", "USART1", T.AMBER),
        ("真实硬件", "PA9 TX · PA10 RX · 波形", "示波器 / 逻辑分析仪", T.RED),
    ]
    y = 96
    for i, (name, contract, api, color) in enumerate(lanes):
        w = 760 - i * 100
        x = 70 + i * 50
        s.rect(x, y, w, 76, fill=T.PANEL if i % 2 == 0 else T.BG2,
               stroke=color, rx=8)
        s.rect(x, y, 7, 76, fill=color, rx=2)
        s.text(x + 24, y + 29, name, size=14, fill=color, weight="700")
        s.text(x + 170, y + 29, contract, size=10.5, fill=T.MUTED)
        s.text(x + w - 18, y + 29, api, size=10.5, fill=T.TEXT,
               anchor="end", mono=True)
        s.text(x + 24, y + 55,
               "所有权：初始化 · 中断 · DMA · 超时 · 恢复必须属于同一条路径",
               size=9.7, fill=T.DIM)
        y += 92

    s.rect(40, 474, 394, 56, fill=T.BG2, stroke=T.GREEN, rx=8)
    s.text(58, 498, "允许", size=11.5, fill=T.GREEN, weight="700")
    s.text(112, 498, "SPL 配置，调试器只读寄存器验证", size=10.5, fill=T.TEXT)
    s.text(112, 517, "迁移时一次切换一条完整外设链", size=9.7, fill=T.MUTED)
    s.rect(466, 474, 394, 56, fill=T.BG2, stroke=T.RED, rx=8)
    s.text(484, 498, "禁止", size=11.5, fill=T.RED, weight="700")
    s.text(538, 498, "先用 SPL 初始化，再让 HAL 接管同一 USART", size=10.2,
           fill=T.TEXT)
    s.text(538, 517, "两套状态互不知情，恢复路径会互相覆盖", size=9.7, fill=T.MUTED)
    s.footer("视觉规范：FA-002 概念连续线 · IG-012 分层结构 · C-03 / C-10 / C-27 / C-31",
             label="自绘矢量图 · STM32 知识库")
    return s


def network_cache_ownership() -> Svg:
    """H7 Ethernet DMA 在可缓存内存上的 TX/RX 所有权交接。"""
    s = Svg(W, H, "CPU、Cache 与 Ethernet DMA：谁看见哪一份数据？",
            "TX 在交给 DMA 前 clean；RX 在 DMA 完成且 CPU 接管后 invalidate；方向相反，顺序不能交换")
    s.header(tag="27 网络 · IG-012", tag_color=T.GREEN)

    nodes = [
        (70, 118, 180, 96, "CPU", "写 payload\n读 pbuf", T.CYAN),
        (360, 118, 180, 96, "D-Cache", "可能仍是旧副本", T.AMBER),
        (650, 118, 180, 96, "SRAM 描述符/缓冲", "DMA 与 CPU 的交接区", T.VIOLET),
        (650, 344, 180, 96, "Ethernet DMA", "读 TX · 写 RX", T.GREEN),
        (360, 344, 180, 96, "MAC / RMII", "帧与 50 MHz 接口", T.PINK),
        (70, 344, 180, 96, "PHY / 线缆", "link 只是第一层证据", T.RED),
    ]
    for x, y, w, h, title, note, color in nodes:
        s.rect(x, y, w, h, fill=T.PANEL, stroke=color, rx=8)
        s.text(x + w / 2, y + 34, title, size=13, anchor="middle",
               fill=color, weight="700")
        for i, line in enumerate(note.split("\n")):
            s.text(x + w / 2, y + 61 + i * 19, line, size=9.7,
                   anchor="middle", fill=T.MUTED)

    s.arrow(252, 146, 356, 146, color=T.CYAN, sw=2)
    s.text(304, 133, "CPU 写", size=9.5, anchor="middle", fill=T.CYAN)
    s.arrow(542, 146, 646, 146, color=T.GREEN, sw=2)
    s.text(594, 128, "TX clean", size=9.5, anchor="middle", fill=T.GREEN)
    s.text(594, 143, "发布所有权", size=9, anchor="middle", fill=T.MUTED)
    s.arrow(740, 218, 740, 340, color=T.GREEN, sw=2)
    s.text(756, 286, "DMA 取帧", size=9.5, fill=T.GREEN)
    s.arrow(646, 392, 544, 392, color=T.PINK, sw=2)
    s.arrow(356, 392, 254, 392, color=T.RED, sw=2)

    s.arrow(700, 340, 700, 218, color=T.VIOLET, sw=2, dash="6 6")
    s.text(618, 278, "RX 写 SRAM", size=9.5, fill=T.VIOLET)
    s.arrow(646, 186, 542, 186, color=T.AMBER, sw=2, dash="6 6")
    s.text(594, 204, "RX invalidate", size=9.5, anchor="middle", fill=T.AMBER)
    s.arrow(356, 186, 252, 186, color=T.CYAN, sw=2, dash="6 6")
    s.text(304, 204, "CPU 接管", size=9.5, anchor="middle", fill=T.CYAN)

    s.rect(40, 466, 820, 64, fill=T.BG2, stroke=T.RED, rx=8)
    s.text(58, 491, "最常见的错", size=11.5, fill=T.RED, weight="700")
    s.text(150, 491, "把 clean / invalidate 当作“都刷新一下”，或在 DMA 仍拥有缓冲时让 CPU 修改它。",
           size=10.4, fill=T.TEXT)
    s.text(150, 514, "验收必须同时记录：缓冲地址与对齐、Cache 操作方向、描述符状态、PCAP 中的实际帧。",
           size=9.8, fill=T.MUTED)
    s.footer("视觉规范：FA-029 几何图解叙事 · IG-012 分层结构 · C-03 / C-10 / C-27 / C-31",
             label="自绘矢量图 · STM32 知识库")
    return s


def tcp_byte_stream() -> Svg:
    """TCP 分段与应用消息边界的连续时间轴。"""
    s = Svg(W, H, "TCP 交付字节，不交付你的消息边界",
            "发送端三次 send 可能被合并或拆分；接收端只能按长度字段或分隔符重新组帧")
    s.header(tag="27 TCP · IG-009", tag_color=T.CYAN)

    s.text(42, 110, "应用写入", size=11.5, fill=T.TEXT, weight="700")
    messages = [(150, 92, 150, "A · 6 B", T.CYAN),
                (312, 92, 230, "B · 10 B", T.GREEN),
                (554, 92, 120, "C · 4 B", T.AMBER)]
    for x, y, w, label, color in messages:
        s.rect(x, y, w, 40, fill=color, rx=4, opacity=.84)
        s.text(x + w / 2, y + 25, label, size=10.5, anchor="middle",
               fill=T.BG, weight="700")

    s.arrow(420, 140, 420, 190, color=T.STROKE, sw=2)
    s.text(438, 172, "TCP 可任意分段", size=10, fill=T.MUTED)
    s.text(42, 222, "网络分段", size=11.5, fill=T.TEXT, weight="700")
    segments = [(150, 204, 92, "A0..A5+B0"), (246, 204, 184, "B1..B9+C0..C1"),
                (434, 204, 84, "C2..C3")]
    for i, (x, y, w, label) in enumerate(segments):
        s.rect(x, y, w, 40, fill=T.PANEL, stroke=T.STROKE, rx=4)
        s.text(x + w / 2, y + 25, label, size=9.4, anchor="middle",
               fill=(T.CYAN, T.GREEN, T.AMBER)[i], mono=True)

    s.arrow(420, 254, 420, 304, color=T.STROKE, sw=2)
    s.text(438, 286, "recv 也可短读", size=10, fill=T.MUTED)
    s.text(42, 338, "接收缓存", size=11.5, fill=T.TEXT, weight="700")
    chunks = [(150, 320, 70, "4 B"), (224, 320, 106, "7 B"),
              (334, 320, 54, "2 B"), (392, 320, 128, "7 B")]
    for x, y, w, label in chunks:
        s.rect(x, y, w, 40, fill=T.BG2, stroke=T.CYAN, rx=4)
        s.text(x + w / 2, y + 25, label, size=9.5, anchor="middle",
               fill=T.CYAN, mono=True)

    s.rect(586, 292, 274, 92, fill=T.PANEL, stroke=T.GREEN, rx=8)
    s.text(604, 320, "正确解析器", size=12, fill=T.GREEN, weight="700")
    s.text(604, 344, "[len][type][sequence][payload][crc]", size=9.5,
           fill=T.TEXT, mono=True)
    s.text(604, 366, "循环消费完整帧；不完整就保留", size=9.7, fill=T.MUTED)

    s.rect(40, 412, 400, 116, fill=T.BG2, stroke=T.GREEN, rx=8)
    s.text(58, 439, "必须成立", size=11.5, fill=T.GREEN, weight="700")
    for i, note in enumerate(("长度有上限，先验证再分配", "一次 recv 可含 0.5、1 或多帧",
                              "超时属于连接策略，不属于分帧规则")):
        s.text(58, 465 + i * 20, "· " + note, size=10, fill=T.MUTED)
    s.rect(460, 412, 400, 116, fill=T.BG2, stroke=T.RED, rx=8)
    s.text(478, 439, "不能假设", size=11.5, fill=T.RED, weight="700")
    for i, note in enumerate(("一次 send 对应一次 recv", "recv 返回短数据就是断线",
                              "用结构体裸发就天然跨平台")):
        s.text(478, 465 + i * 20, "· " + note, size=10, fill=T.MUTED)
    s.footer("视觉规范：FA-002 概念连续线 · IG-009 时间轴节点 · C-03 / C-10 / C-27 / C-31",
             label="自绘矢量图 · STM32 知识库")
    return s


def rtos_owner_task() -> Svg:
    """两个调用者争抢驱动与单一所有者任务的前后对比。"""
    s = Svg(W, H, "给驱动加很多锁，仍不等于拥有清楚的所有权",
            "把完整事务送给唯一所有者，片选、DMA、超时和恢复才能落在同一个状态机里")
    s.header(tag="28 RTOS · IG-011", tag_color=T.VIOLET)

    s.text(220, 100, "并发直调：锁住了函数，没锁住完整事务", size=13,
           anchor="middle", fill=T.RED, weight="700")
    callers = [(60, 134, "任务 A", T.CYAN), (280, 134, "任务 B", T.AMBER)]
    for x, y, name, color in callers:
        s.rect(x, y, 140, 56, fill=T.PANEL, stroke=color, rx=8)
        s.text(x + 70, y + 33, name, size=12, anchor="middle", fill=color,
               weight="700")
        s.arrow(x + 70, y + 60, 220, 244, color=color, sw=2)
    s.rect(120, 246, 200, 76, fill=T.BG2, stroke=T.RED, rx=8)
    s.text(220, 272, "SPI API + mutex", size=12, anchor="middle",
           fill=T.RED, weight="700")
    s.text(220, 297, "CS / DMA / timeout 分散", size=9.8, anchor="middle",
           fill=T.MUTED)
    s.arrow(220, 326, 220, 374, color=T.RED, sw=2)
    s.rect(120, 376, 200, 62, fill=T.PANEL, stroke=T.STROKE, rx=8)
    s.text(220, 403, "同一外设", size=12, anchor="middle", fill=T.TEXT,
           weight="700")
    s.text(220, 424, "交叉片选 / 恢复竞态", size=9.5, anchor="middle", fill=T.RED)

    s.text(680, 100, "所有者任务：一次只接受一笔完整事务", size=13,
           anchor="middle", fill=T.GREEN, weight="700")
    for i, (name, color) in enumerate((("任务 A", T.CYAN), ("任务 B", T.AMBER))):
        y = 134 + i * 72
        s.rect(500, y, 120, 48, fill=T.PANEL, stroke=color, rx=8)
        s.text(560, y + 29, name, size=11, anchor="middle", fill=color,
               weight="700")
        s.arrow(624, y + 24, 664, 220, color=color, sw=2)
    s.rect(646, 194, 214, 176, fill=T.BG2, stroke=T.GREEN, rx=8)
    s.text(753, 222, "SPI owner", size=12.5, anchor="middle", fill=T.GREEN,
           weight="700")
    for i, note in enumerate(("队列接收完整事务", "拉低 / 拉高 CS", "启动并等待 DMA",
                              "统一超时与恢复", "返回稳定结果码")):
        s.text(666, 250 + i * 22, "· " + note, size=9.8, fill=T.MUTED)
    s.arrow(753, 374, 753, 414, color=T.GREEN, sw=2)
    s.rect(646, 416, 214, 62, fill=T.PANEL, stroke=T.STROKE, rx=8)
    s.text(753, 442, "同一外设", size=12, anchor="middle", fill=T.TEXT,
           weight="700")
    s.text(753, 463, "串行事务 · 可审计恢复", size=9.5, anchor="middle", fill=T.GREEN)

    s.rect(370, 120, 56, 358, fill=T.PANEL, stroke=T.STROKE, rx=8)
    s.text(398, 298, "→", size=28, anchor="middle", fill=T.CYAN, weight="700")
    s.footer("视觉规范：FA-002 概念连续线 · IG-011 前后变化对比 · C-03 / C-10 / C-27 / C-31",
             label="自绘矢量图 · STM32 知识库")
    return s


def rtos_deadline_budget() -> Svg:
    """响应时间组成与 deadline 的单条可复算时间轴。"""
    s = Svg(W, H, "“实时”不是快，而是最坏响应仍早于截止点",
            "把阻塞、执行和抢占分别量出来：R = B + C + S；平均值不能替代最坏值")
    s.header(tag="28 实时 · IG-009", tag_color=T.AMBER)

    x0, y, total = 82, 220, 730
    s.line(x0, y, x0 + total, y, stroke=T.STROKE, sw=2)
    pieces = [
        (0, 120, "B 阻塞", "等资源所有者", T.RED),
        (120, 250, "C 执行", "任务自己的 WCET", T.GREEN),
        (370, 180, "S 干扰", "更高优先级任务/ISR", T.AMBER),
        (550, 110, "C 继续", "完成剩余工作", T.GREEN),
    ]
    for start, width, name, note, color in pieces:
        x = x0 + start
        s.rect(x, y - 38, width, 76, fill=color, rx=4, opacity=.84)
        s.text(x + width / 2, y - 7, name, size=11, anchor="middle",
               fill=T.BG, weight="700")
        s.text(x + width / 2, y + 18, note, size=8.8, anchor="middle", fill=T.BG)

    marks = [(x0, "release", T.CYAN), (x0 + 660, "finish", T.GREEN),
             (x0 + total, "deadline D", T.RED)]
    for x, label, color in marks:
        s.line(x, 146, x, 302, stroke=color, sw=2, dash="5 5")
        s.text(x, 132, label, size=10, anchor="middle", fill=color, weight="700")

    s.double_arrow(x0, 318, x0 + 660, 318, color=T.CYAN, sw=1.5, text_="R = B + C + S")
    s.double_arrow(x0, 354, x0 + total, 354, color=T.RED, sw=1.5, text_="D")
    s.text(450, 392, "验收条件：Rmax ≤ D", size=17, anchor="middle",
           fill=T.GREEN, weight="800", mono=True)

    s.rect(40, 426, 400, 102, fill=T.BG2, stroke=T.GREEN, rx=8)
    s.text(58, 452, "要测", size=11.5, fill=T.GREEN, weight="700")
    for i, note in enumerate(("ISR 占用与最长临界区", "mutex 最长持有时间与优先级继承",
                              "任务 WCET、周期、抖动和队列峰值")):
        s.text(112, 452 + i * 23, note, size=10, fill=T.MUTED)
    s.rect(460, 426, 400, 102, fill=T.BG2, stroke=T.RED, rx=8)
    s.text(478, 452, "不能只看", size=11.5, fill=T.RED, weight="700")
    for i, note in enumerate(("CPU 平均利用率", "一次实验里的平均延迟", "任务优先级数字看起来很高")):
        s.text(558, 452 + i * 23, note, size=10, fill=T.MUTED)
    s.footer("视觉规范：FA-002 概念连续线 · IG-009 时间轴节点 · C-03 / C-10 / C-27 / C-31",
             label="自绘矢量图 · STM32 知识库")
    return s


def rtos_config_paths() -> Svg:
    """三套系统把配置与硬件描述送入固件的不同路径。"""
    s = Svg(W, H, "三套 RTOS 生态：配置从哪里进入最终固件？",
            "函数名不是主要差异；真正影响维护的是配置入口、硬件描述、驱动模型和构建产物")
    s.header(tag="28 生态 · IG-004", tag_color=T.VIOLET)

    columns = [
        (42, "FreeRTOS", T.CYAN, [
            ("配置", "FreeRTOSConfig.h"),
            ("硬件", "CubeMX / HAL / BSP"),
            ("对象", "task / queue / timer"),
            ("构建", "工程自行组合服务"),
        ]),
        (322, "RT-Thread", T.GREEN, [
            ("配置", "menuconfig / rtconfig.h"),
            ("硬件", "BSP + device framework"),
            ("对象", "thread / IPC / device"),
            ("构建", "SCons + components"),
        ]),
        (602, "Zephyr", T.AMBER, [
            ("配置", "Kconfig / prj.conf"),
            ("硬件", "Devicetree + bindings"),
            ("对象", "kernel + device model"),
            ("构建", "west + CMake + Ninja"),
        ]),
    ]
    for x, title, color, rows in columns:
        s.rect(x, 92, 256, 360, fill=T.PANEL, stroke=color, rx=8)
        s.rect(x, 92, 256, 48, fill=color, rx=8, opacity=.86)
        s.text(x + 128, 122, title, size=14, anchor="middle", fill=T.BG,
               weight="800")
        for i, (kind, detail) in enumerate(rows):
            yy = 164 + i * 66
            s.text(x + 18, yy, kind, size=10.5, fill=color, weight="700")
            s.text(x + 76, yy, detail, size=9.8, fill=T.TEXT, mono=True)
            if i < len(rows) - 1:
                s.arrow(x + 128, yy + 16, x + 128, yy + 43,
                        color=T.STROKE, sw=1.5, head=5)
        s.rect(x + 18, 410, 220, 24, fill=T.BG2, stroke=color, rx=4)
        s.text(x + 128, 427, "→ firmware.elf", size=9.8, anchor="middle",
               fill=color, mono=True, weight="700")

    s.rect(42, 474, 816, 56, fill=T.BG2, stroke=T.RED, rx=8)
    s.text(60, 498, "迁移检查", size=11.5, fill=T.RED, weight="700")
    s.text(132, 498, "不要逐函数替换；逐项核对配置单位、设备所有权、ISR 边界、超时语义与启动顺序。",
           size=10.3, fill=T.TEXT)
    s.text(132, 518, "同一个 GPIO 闪灯能编译，不代表网络、低功耗和故障恢复已经等价。",
           size=9.7, fill=T.MUTED)
    s.footer("视觉规范：FA-029 几何图解叙事 · IG-004 双列多行对比 · C-03 / C-10 / C-27 / C-31",
             label="自绘矢量图 · STM32 知识库")
    return s


ALL = [layers_hal_ll_reg, project_structure, peripheral_bus, interrupt_priority,
       l4_idd_bench, network_debug_ladder, spl_ownership_boundary,
       network_cache_ownership, tcp_byte_stream, rtos_owner_task,
       rtos_deadline_budget, rtos_config_paths]

NAMES = {
    "layers_hal_ll_reg": "layers-hal-ll-reg",
    "project_structure": "project-structure",
    "peripheral_bus": "peripheral-bus",
    "interrupt_priority": "interrupt-priority",
    "l4_idd_bench": "l4-idd-bench",
    "network_debug_ladder": "network-debug-ladder",
    "spl_ownership_boundary": "spl-ownership-boundary",
    "network_cache_ownership": "network-cache-ownership",
    "tcp_byte_stream": "tcp-byte-stream",
    "rtos_owner_task": "rtos-owner-task",
    "rtos_deadline_budget": "rtos-deadline-budget",
    "rtos_config_paths": "rtos-config-paths",
}


def main(argv):
    import os
    import xml.dom.minidom
    here = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(os.path.dirname(here), "assets", "diagrams")
    os.makedirs(out_dir, exist_ok=True)
    only = set(argv[1:])
    for fn in ALL:
        name = NAMES[fn.__name__]
        if only and name not in only:
            continue
        path = os.path.join(out_dir, name + ".svg")
        fn().save(path)
        xml.dom.minidom.parse(path)
        print(f"[ok] {name}.svg")


if __name__ == "__main__":
    main(__import__("sys").argv)

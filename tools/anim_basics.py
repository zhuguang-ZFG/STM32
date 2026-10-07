#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""基础篇动画：工具链、启动流程、存储器映射、时钟树。"""

from __future__ import annotations

from svgkit import (Svg, T, anim_flow, anim_tx)

W, H = 900, 620


def _step_highlight(prefix: str, n: int, period=6.0, window=0.22,
                    peak=0.42, rest=0.08) -> str:
    """依次高亮。窗口内才变亮，其余时间保持很淡，避免色块盖住文字。"""
    css = []
    step = 100.0 / n
    for i in range(n):
        a = i * step
        b = min(a + step * window, 99.2)
        name = f"{prefix}{i}-flash"
        css.append(
            f"@keyframes {name}{{0%,{a:.2f}%{{opacity:{rest}}}"
            f"{a + 0.3:.2f}%,{b:.2f}%{{opacity:{peak}}}"
            f"{min(b + 0.3, 100):.2f}%,100%{{opacity:{rest}}}}}"
        )
        css.append(f".{prefix}{i}{{animation:{name} {period}s linear infinite;}}")
    return "\n".join(css)


def toolchain_flow() -> Svg:
    s = Svg(W, H, "STM32 开发工具链", "从一行 C 代码到芯片里跑起来的程序")
    s.header(tag="01 环境搭建", tag_color=T.CYAN)

    boxes = [
        ("main.c", "C 源码", T.BLUE, "你写的代码"),
        ("GCC / ARMCC", "编译", T.CYAN, "源码 → 目标文件 .o"),
        ("LD 链接器", "链接", T.VIOLET, ".o → .elf（含地址）"),
        ("objcopy", "转换", T.AMBER, ".elf → .bin / .hex"),
        ("ST-Link", "烧录", T.GREEN, "SWD 写入 Flash"),
    ]
    bw, gap, x0, y0, bh = 120, 50, 40, 120, 76
    for i, (label, sub, color, note) in enumerate(boxes):
        x = x0 + i * (bw + gap)
        s.rect(x, y0, bw, bh, fill=T.PANEL, stroke=color, rx=10)
        s.text(x + bw / 2, y0 + 30, label, size=13, anchor="middle",
               fill=T.TEXT, weight="600")
        s.text(x + bw / 2, y0 + 50, sub, size=11, anchor="middle", fill=color)
        s.text(x + bw / 2, y0 + bh + 22, note, size=11, anchor="middle",
               fill=T.MUTED)
        if i < len(boxes) - 1:
            ax1, ax2 = x + bw + 6, x + bw + gap - 6
            s.arrow(ax1, y0 + bh / 2, ax2, y0 + bh / 2, color=T.STROKE, sw=2,
                    marker=True)
            s.line(ax1, y0 + bh / 2, ax2, y0 + bh / 2, stroke=T.CYAN, sw=2.4,
                   cls=f"f{i}")
            s.circle(ax1, y0 + bh / 2, 4, fill=T.CYAN, cls=f"p{i}")

    css = []
    for i in range(len(boxes) - 1):
        css.append(anim_flow(f".f{i}", dur="1.4s", dash="6 12", shift=-18))
        css.append(anim_tx(f".p{i}", dur="1.4s", x1=0, x2=gap - 12,
                           delay=f"{i * 0.28:.2f}s"))
    s.add_style("\n".join(css))

    y1 = 260
    last_x = x0 + 4 * (bw + gap) + bw / 2
    s.arrow(last_x, y0 + bh, last_x, y1 - 6, color=T.GREEN, sw=2.4)
    s.text(last_x - 14, y0 + bh + 44, "SWD：SWCLK + SWDIO", size=11,
           anchor="end", fill=T.GREEN)

    row2 = [
        ("内部 Flash", "0x0800_0000 起", "程序常住地，掉电不丢"),
        ("复位 → 取向量表", "MSP / Reset_Handler", "启动文件 startup_xxx.s"),
        ("Cortex-M 内核", "约 1.25 DMIPS/MHz", "M3 @ 72 MHz ≈ 90 DMIPS"),
        ("外设寄存器", "0x4000_0000 起", "GPIO / TIM / USART ..."),
    ]
    bw2 = 190
    for i, (label, sub, note) in enumerate(row2):
        x = 40 + i * (bw2 + 18)
        s.rect(x, y1, bw2, 74, fill=T.PANEL2, stroke=T.STROKE, rx=10)
        s.text(x + bw2 / 2, y1 + 28, label, size=14, anchor="middle",
               fill=T.TEXT, weight="600")
        s.text(x + bw2 / 2, y1 + 48, sub, size=11, anchor="middle", fill=T.CYAN,
               mono=True)
        s.text(x + bw2 / 2, y1 + 92, note, size=11, anchor="middle", fill=T.MUTED)
        if i < len(row2) - 1:
            s.arrow(x + bw2 + 2, y1 + 37, x + bw2 + 16, y1 + 37,
                    color=T.STROKE, sw=2, head=5)
    s.add_style(_step_highlight("t", 4, period=4.0))
    for i in range(4):
        s.rect(40 + i * (bw2 + 18), y1, bw2, 74, fill=T.CYAN, rx=10,
               cls=f"t{i}", opacity=0.1)

    s.title_block(40, 420, "常见命令（命令行 + Makefile 方式）", color=T.GREEN)
    s.rect(40, 432, 820, 84, fill=T.BG2, stroke=T.STROKE, rx=10)
    s.code(56, 456, [
        "arm-none-eabi-gcc -mcpu=cortex-m3 -mthumb -O2 -c main.c -o main.o",
        "arm-none-eabi-gcc -T STM32F103C8Tx_FLASH.ld *.o -o build/app.elf",
        "arm-none-eabi-objcopy -O binary build/app.elf build/app.bin",
        "STM32_Programmer_CLI -c port=SWD -w build/app.bin 0x08000000 -rst",
    ], size=12.5, lh=19)
    s.footer("IDE（Keil / CubeIDE / PlatformIO）只是把上面 4 条命令包了一层图形界面")
    return s


def boot_sequence() -> Svg:
    s = Svg(W, H, "上电之后发生了什么", "从复位向量到 main() 的 8 个步骤")
    s.header(tag="01 启动流程", tag_color=T.VIOLET)

    steps = [
        ("① 上电/复位", "NRST 释放，CPU 复位", T.RED),
        ("② 读向量表", "从 0x0000_0000 取 MSP", T.ORANGE),
        ("③ 取复位向量", "下一字 → Reset_Handler", T.AMBER),
        ("④ SystemInit()", "配 HSE/PLL，改 VTOR", T.GREEN),
        ("⑤ 拷贝 .data", "Flash 初值 → SRAM", T.CYAN),
        ("⑥ 清零 .bss", "未初始化变量置 0", T.BLUE),
        ("⑦ 库初始化", "__libc_init_array", T.VIOLET),
        ("⑧ main()", "超级循环或启动 RTOS", T.PINK),
    ]
    x0, y0, bw, bh, gap = 40, 108, 196, 84, 18
    for i, (label, sub, color) in enumerate(steps):
        r, c = divmod(i, 4)
        x = x0 + c * (bw + gap)
        y = y0 + r * (bh + 66)
        s.rect(x, y, bw, bh, fill=T.PANEL, stroke=T.STROKE, rx=10)
        s.rect(x, y, 4, bh, fill=color, rx=2)
        s.text(x + 16, y + 30, label, size=15, fill=T.TEXT, weight="700")
        s.text(x + 16, y + 54, sub, size=11, fill=T.MUTED)
        if c < 3:
            s.arrow(x + bw + 2, y + bh / 2, x + bw + gap - 2, y + bh / 2,
                    color=T.STROKE, sw=2, head=6)
        if c == 3 and r == 0:
            s.arrow(x + bw / 2, y + bh + 2, x + bw / 2, y + bh + 44,
                    color=T.STROKE, sw=2, head=6)
            s.text(x + bw / 2 + 10, y + bh + 30, "换行继续", size=11, fill=T.DIM)
    s.add_style(_step_highlight("b", 8, period=7.2))
    for i, (label, sub, color) in enumerate(steps):
        r, c = divmod(i, 4)
        x = x0 + c * (bw + gap)
        y = y0 + r * (bh + 66)
        s.rect(x, y, bw, bh, fill=color, rx=10, cls=f"b{i}", opacity=0.12)

    s.title_block(40, 400, "向量表（前 8 个字节决定 CPU 从哪里开始）", color=T.CYAN)
    s.rect(40, 406, 470, 104, fill=T.BG2, stroke=T.STROKE, rx=10)
    s.code(56, 436, [
        "0x0000_0000  MSP 初值     ; Flash 启动时别名到 0x0800_0000",
        "0x0000_0004  Reset_Handler",
        "0x0000_0008  NMI_Handler",
        "0x0000_000C  HardFault_Handler",
        "; 外设 IRQn 的入口 = VTOR + 4×(IRQn+16)",
    ], size=12, lh=19)

    s.rect(530, 406, 330, 104, fill=T.PANEL, stroke=T.STROKE, rx=10)
    s.text(548, 428, "BOOT0 / BOOT1 决定启动映射", size=13, fill=T.TEXT,
           weight="600")
    rows = [("BOOT0=0", "主 Flash，正常运行", T.GREEN),
            ("BOOT0=1 BOOT1=0", "系统区，出厂下载", T.AMBER),
            ("BOOT0=1 BOOT1=1", "SRAM，掉电即丢", T.CYAN)]
    for i, (k, v, c) in enumerate(rows):
        s.text(548, 452 + i * 20, k, size=11, mono=True, fill=c)
        s.text(700, 452 + i * 20, v, size=11, fill=T.MUTED)
    s.footer("Cube 启动文件先 SystemInit 再搬 .data；CPU 读的是 0x0000_0000 别名，不是写死 0x0800_0000")
    return s


def memory_map() -> Svg:
    s = Svg(W, H, "Cortex-M 存储器映射", "所有 STM32 都遵循同一张地图（以 F411 为例）")
    s.header(tag="02 存储器", tag_color=T.AMBER)

    regions = [
        ("0x0000_0000", "Code / Flash 别名", "512 KB Flash（F411CE）", T.BLUE),
        ("0x1FFF_0000", "系统存储（Code 区内）", "F411 出厂 Bootloader；F1 在 0x1FFFF000", T.AMBER),
        ("0x2000_0000", "SRAM", "128 KB，栈 / 堆 / 全局变量", T.GREEN),
        ("0x4000_0000", "Peripheral", "GPIO / TIM / USART … 寄存器", T.CYAN),
        ("0xE000_0000", "Cortex-M 内部", "NVIC / SysTick / SCB / MPU", T.VIOLET),
    ]
    y = 100
    for i, (addr, name, note, color) in enumerate(regions):
        h = 62
        s.rect(40, y, 820, h, fill=T.PANEL, stroke=T.STROKE, rx=8)
        s.rect(40, y, 6, h, fill=color, rx=3)
        s.text(60, y + 26, addr, size=14, mono=True, fill=color, weight="700")
        s.text(200, y + 26, name, size=14, fill=T.TEXT, weight="600")
        s.text(200, y + 47, note, size=11.5, fill=T.MUTED)
        y += h + 10

    s.circle(872, 131, 7, fill=T.WHITE, opacity=0.85, cls="ptr")
    s.add_style(
        "@keyframes ptr-scan{0%{transform:translateY(0)}"
        "100%{transform:translateY(330px)}}"
        ".ptr{animation:ptr-scan 5s ease-in-out infinite alternate;}"
    )

    s.rect(40, 458, 400, 54, fill=T.BG2, stroke=T.STROKE, rx=10)
    s.text(58, 481, "Flash 页 / 扇区大小不一样", size=12.5, fill=T.TEXT,
           weight="600")
    s.text(58, 501, "F103 中容量 1 KB/页，大容量 2 KB/页；F4 按扇区擦", size=11.5,
           fill=T.MUTED)
    s.rect(460, 458, 400, 54, fill=T.BG2, stroke=T.STROKE, rx=10)
    s.text(478, 481, "地址 = 基址 + 偏移", size=12.5, fill=T.TEXT, weight="600")
    s.text(478, 501, "F411：GPIOA=0x40020000，ODR 在 +0x14（+0x0C 是 PUPDR）",
           size=11, fill=T.MUTED, mono=True)
    s.footer("小端模式：0x12345678 在内存里存成 78 56 34 12")
    return s



def clock_tree() -> Svg:
    s = Svg(W, H, "时钟树：8 MHz 晶振如何变成 72 MHz",
            "以 STM32F103（HSE 8 MHz × 9 = 72 MHz）为例")
    s.header(tag="02 时钟树", tag_color=T.GREEN)

    nodes = [
        ("HSE", "8 MHz 外部晶振", T.AMBER, 40, 150),
        ("PLLXTPRE", "本例 ÷1（也可 ÷2）", T.STROKE, 200, 150),
        ("PLL", "PLLMUL = ×9", T.ORANGE, 370, 140),
        ("SYSCLK", "72 MHz", T.GREEN, 560, 140),
        ("HCLK", "AHB ÷1 = 72 MHz", T.CYAN, 720, 140),
    ]
    y = 108
    for label, sub, color, x, w in nodes:
        s.rect(x, y, w, 72, fill=T.PANEL, stroke=color, rx=10)
        s.text(x + w / 2, y + 28, label, size=15, anchor="middle", fill=T.TEXT,
               weight="700")
        s.text(x + w / 2, y + 50, sub, size=11, anchor="middle", fill=color)
    gaps = ((190, 200), (350, 370), (510, 560), (700, 720))
    for i, (a, b) in enumerate(gaps):
        s.line(a, y + 36, b, y + 36, stroke=T.CYAN, sw=2.4, cls="clk")
        s.circle(a, y + 36, 4.5, fill=T.CYAN, cls=f"pulse{i}")
        s.add_style(anim_tx(f".pulse{i}", dur="1.2s", x1=0, x2=max(8, b - a - 8)))
    s.add_style(anim_flow(".clk", dur="1.2s", dash="5 11", shift=-16))

    y2 = 244
    s.line(790, y + 72, 790, y2, stroke=T.CYAN, sw=2.2)
    s.arrow(790, y2 - 34, 790, y2 - 2, color=T.CYAN, sw=2.2, head=6)
    buses = [
        ("APB2", "÷1 = 72 MHz", "GPIOA~E / USART1 / SPI1 / ADC1 / TIM1", T.VIOLET, 40),
        ("APB1", "÷2 = 36 MHz", "USART2/3 · I2C · TIM2~7 · SPI2 · CAN",
         T.PINK, 460),
    ]
    for label, sub, note, color, x in buses:
        s.rect(x, y2, 400, 92, fill=T.PANEL2, stroke=T.STROKE, rx=10)
        s.text(x + 18, y2 + 30, label, size=15, fill=color, weight="700")
        s.text(x + 96, y2 + 30, sub, size=13, fill=T.TEXT)
        s.text(x + 18, y2 + 54, note, size=11.5, fill=T.MUTED)
        extra = ("ADC 另有分频，最高 14 MHz" if label == "APB2"
                 else "TIM2~7 时钟 ×2 = 72 MHz；USB 另要 48 MHz")
        s.text(x + 18, y2 + 76, extra, size=11, fill=T.DIM)
    s.line(790, y2 + 46, 860, y2 + 46, stroke=T.CYAN, sw=1.6, dash="4 6")

    s.title_block(40, 372, "CubeMX 里对应的三处配置", color=T.AMBER)
    s.rect(40, 384, 820, 126, fill=T.BG2, stroke=T.STROKE, rx=10)
    s.code(56, 408, [
        "RCC_OscInitStruct.HSEState = RCC_HSE_ON;             // 打开 8 MHz 晶振",
        "RCC_OscInitStruct.PLL.PLLMUL = RCC_PLL_MUL9;         // 8 MHz × 9 = 72 MHz",
        "RCC_ClkInitStruct.AHBCLKDivider  = RCC_SYSCLK_DIV1;  // HCLK  = 72 MHz",
        "RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV2;    // PCLK1 = 36 MHz",
        "RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;    // PCLK2 = 72 MHz",
        "SystemCoreClockUpdate();   // 更新 SystemCoreClock，否则延时/波特率全错",
    ], size=12.5, lh=20)
    s.footer("F411 例：25 MHz ÷ 25 × 200 ÷ 2 = 100 MHz（÷25×400÷2 会得到 200 MHz，超出上限）")
    return s


ALL = [toolchain_flow, boot_sequence, memory_map, clock_tree]

NAMES = {
    "toolchain_flow": "toolchain-flow",
    "boot_sequence": "boot-sequence",
    "memory_map": "memory-map",
    "clock_tree": "clock-tree",
}


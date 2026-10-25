#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GPIO / 中断 / 调试类动画。"""

from __future__ import annotations

from svgkit import Svg, T, anim_blink, anim_fade, anim_flow, anim_tx

W, H = 900, 620


def gpio_blink() -> Svg:
    s = Svg(W, H, "GPIO 推挽输出点亮 LED", "PA5 每 500 ms 翻转一次，电流路径与波形同步演示")
    s.header(tag="03 GPIO", tag_color=T.GREEN)

    # ---------------- 左：电路 ----------------
    s.rect(40, 80, 470, 262, fill=T.PANEL, stroke=T.STROKE, rx=8)
    s.text(58, 106, "外接 LED：高电平点亮（BluePill 板载灯是 PC13，低电平才亮）",
           size=12, fill=T.TEXT, weight="600")

    # MCU
    s.rect(62, 130, 150, 150, fill=T.PANEL2, stroke=T.CYAN, rx=8)
    s.text(137, 160, "STM32", size=15, anchor="middle", fill=T.CYAN, weight="700")
    s.text(137, 182, "GPIOA", size=12, anchor="middle", fill=T.MUTED)
    s.text(137, 204, "PA5", size=16, anchor="middle", fill=T.TEXT, mono=True,
           weight="700")
    s.text(137, 226, "推挽 / 50 MHz", size=10.5, anchor="middle", fill=T.DIM)
    # 引脚
    s.text(232, 152, "PA5", size=12, mono=True, fill=T.TEXT, anchor="middle")
    s.line(212, 170, 268, 170, stroke=T.AMBER, sw=2, cls="wire")
    s.circle(212, 170, 4, fill=T.AMBER)

    # 电阻
    s.rect(268, 158, 56, 24, fill=T.BG2, stroke=T.AMBER, rx=4)
    s.text(296, 176, "330Ω", size=11, anchor="middle", fill=T.AMBER, mono=True)

    # LED
    s.line(324, 170, 352, 170, stroke=T.AMBER, sw=2)
    s.poly([(352, 158), (352, 182), (376, 170)], fill=T.RED, stroke=T.RED)
    s.line(376, 156, 376, 184, stroke=T.RED, sw=2)
    s.line(376, 170, 410, 170, stroke=T.AMBER, sw=2)
    s.led(392, 118, 13, color=T.RED, cls="led")
    s.text(392, 96, "LED 亮 / 灭", size=11, anchor="middle", fill=T.MUTED)

    # 电流箭头 + 流动动画
    s.line(392, 140, 392, 166, stroke=T.RED, sw=1.5, dash="3 3")
    for i, x in enumerate((230, 270, 320, 360)):
        s.circle(x, 170, 3.2, fill=T.RED, cls=f"dot{i}")
    # 地
    s.line(410, 170, 410, 232, stroke=T.MUTED, sw=2)
    s.line(392, 232, 428, 232, stroke=T.MUTED, sw=2)
    s.line(398, 240, 422, 240, stroke=T.MUTED, sw=2)
    s.line(404, 248, 416, 248, stroke=T.MUTED, sw=2)
    s.text(436, 236, "GND", size=11, fill=T.MUTED)

    s.text(58, 300, "电流路径：PA5 → 330Ω → LED → GND", size=12, fill=T.GREEN)
    s.text(58, 322, "R = (3.3 V − 2.0 V) / 5 mA ≈ 260 Ω，取 330 Ω 更安全",
           size=11.5, fill=T.MUTED)

    s.add_style(anim_blink(".led", dur="1s", dim=0.12))
    s.add_style(anim_flow(".wire", dur="1.4s", dash="7 9", shift=-16))
    s.add_style(
        "@keyframes dot-run{0%{transform:translateX(0);opacity:0}"
        "20%{opacity:1}80%{opacity:1}"
        "100%{transform:translateX(48px);opacity:0}}"
        ".dot0{animation:dot-run 1.4s linear infinite;}"
        ".dot1{animation:dot-run 1.4s linear infinite .35s;}"
        ".dot2{animation:dot-run 1.4s linear infinite .7s;}"
        ".dot3{animation:dot-run 1.4s linear infinite 1.05s;}"
    )

    # ---------------- 右：波形 ----------------
    s.rect(530, 80, 330, 262, fill=T.PANEL, stroke=T.STROKE, rx=8)
    s.text(548, 106, "PA5 输出电平（1 Hz）", size=13, fill=T.TEXT, weight="600")
    s.axis(568, 130, 268, 130, ylabel="3.3V", xlabel="时间")
    s.text(568, 148, "1", size=10, fill=T.DIM)
    s.text(568, 250, "0", size=10, fill=T.DIM)
    s.waveform(568, 138, 268, 118, [1, 1, 1, 1, 0, 0, 0, 0], color=T.GREEN,
               sw=2)
    for i in range(4):
        s.text(568 + 268 / 4 * i, 274, f"{i * 250}", size=10, fill=T.DIM,
               anchor="middle")
    s.text(702, 292, "ms（高 500 ms + 低 500 ms）", size=10.5, fill=T.DIM,
           anchor="middle")
    s.line(568, 130, 568, 262, stroke=T.RED, sw=1.5, cls="cursor")
    s.add_style(
        "@keyframes cur-run{0%{transform:translateX(0)}"
        "100%{transform:translateX(268px)}}"
        ".cursor{animation:cur-run 1s linear infinite;}"
    )
    s.text(548, 320, "HAL_Delay(500) 阻塞式延时；实际项目请用定时器中断",
           size=11, fill=T.AMBER)

    # ---------------- 下：代码 ----------------
    s.title_block(40, 372, "三种写法（效果相同，抽象层次不同）", color=T.CYAN)
    s.rect(40, 384, 400, 122, fill=T.BG2, stroke=T.STROKE, rx=8)
    s.code(56, 408, [
        "// 1) HAL 库",
        "HAL_GPIO_TogglePin(GPIOA, GPIO_PIN_5);",
        "HAL_Delay(500);",
        "",
        "// 2) 寄存器（BSRR 原子操作）",
        "GPIOA->BSRR = GPIO_PIN_5;      // 置 1",
        "GPIOA->BSRR = GPIO_PIN_5 << 16; // 清 0",
    ], size=11.5, lh=17)
    s.rect(460, 384, 400, 122, fill=T.BG2, stroke=T.STROKE, rx=8)
    s.code(476, 408, [
        "// 3) CubeMX 生成的初始化",
        "GPIO_InitTypeDef i = {0};",
        "i.Pin  = GPIO_PIN_5;",
        "i.Mode = GPIO_MODE_OUTPUT_PP;",
        "i.Pull = GPIO_NOPULL;",
        "i.Speed= GPIO_SPEED_FREQ_LOW;",
        "HAL_GPIO_Init(GPIOA, &i);",
    ], size=11.5, lh=17, color=T.CYAN)
    s.footer("先确认时钟已使能（__HAL_RCC_GPIOA_CLK_ENABLE()），否则写寄存器没有任何反应")
    return s


def gpio_input_interrupt() -> Svg:
    s = Svg(W, H, "按键读取：轮询 vs 中断", "同一个按键，两种 CPU 参与方式与响应延迟对比")
    s.header(tag="04 中断", tag_color=T.VIOLET)

    # 按键事件时间轴（共用）
    s.text(40, 96, "按键按下事件（t = 0）", size=12.5, fill=T.MUTED)

    # --- 方案 A：轮询 ---
    s.rect(40, 108, 820, 130, fill=T.PANEL, stroke=T.STROKE, rx=8)
    s.text(58, 134, "① 轮询（Polling）", size=14, fill=T.AMBER, weight="700")
    s.text(240, 134, "while (1) { if (HAL_GPIO_ReadPin(...) == 0) ... }",
           size=11.5, mono=True, fill=T.MUTED)
    y = 176
    s.rect(58, y - 14, 784, 40, fill=T.BG2, stroke=T.GRID, rx=8)
    for i in range(14):
        s.rect(62 + i * 56, y - 10, 52, 32, fill=T.PANEL2, stroke=T.STROKE, rx=4)
        s.text(88 + i * 56, y + 10, "读", size=11, anchor="middle", fill=T.MUTED)
    s.rect(62 + 6 * 56, y - 10, 52, 32, fill=T.AMBER, rx=4, opacity=0.85,
           cls="hit")
    s.text(88 + 6 * 56, y + 10, "命中", size=11, anchor="middle", fill="#fbfaf7",
           weight="700")
    s.text(58, 226, "缺点：CPU 全程被占用（99% 时间在空转）；按键抖动会被读成多次按下",
           size=11.5, fill=T.RED)
    s.add_style(anim_fade(".hit", dur="2s", a=0.35, b=1.0))

    # --- 方案 B：中断 ---
    s.rect(40, 252, 820, 130, fill=T.PANEL, stroke=T.STROKE, rx=8)
    s.text(58, 278, "② 外部中断（EXTI + NVIC）", size=14, fill=T.GREEN,
           weight="700")
    s.text(300, 278, "按下瞬间硬件自动打断主程序，执行 ISR", size=11.5,
           fill=T.MUTED)
    y2 = 320
    s.rect(58, y2 - 14, 784, 40, fill=T.BG2, stroke=T.GRID, rx=8)
    s.rect(62, y2 - 10, 300, 32, fill=T.PANEL2, stroke=T.STROKE, rx=4)
    s.text(212, y2 + 10, "主程序继续干别的事（低功耗、算数据…）", size=11,
           anchor="middle", fill=T.MUTED)
    s.rect(366, y2 - 10, 56, 32, fill=T.GREEN, rx=4, cls="isr")
    s.text(394, y2 + 10, "ISR", size=11, anchor="middle", fill="#fbfaf7",
           weight="700")
    s.rect(426, y2 - 10, 416, 32, fill=T.PANEL2, stroke=T.STROKE, rx=4)
    s.text(634, y2 + 10, "恢复现场，继续原来的循环", size=11, anchor="middle",
           fill=T.MUTED)
    s.text(58, 370, "优点：响应延迟只有十几个时钟周期；CPU 可进 Sleep 模式省电",
           size=11.5, fill=T.GREEN)
    s.add_style(anim_fade(".isr", dur="1.6s", a=0.4, b=1.0))

    # --- 触发方式表 ---
    s.title_block(40, 412, "EXTI 触发方式怎么选", color=T.CYAN)
    rows = [
        ("GPIO_MODE_IT_RISING", "上升沿", "按键按下接地（低有效）时，松开才触发", T.BLUE),
        ("GPIO_MODE_IT_FALLING", "下降沿", "最常用：按下瞬间触发", T.GREEN),
        ("GPIO_MODE_IT_RISING_FALLING", "双边沿", "旋转编码器、需要按下+松开都响应", T.AMBER),
        ("GPIO_MODE_EVT_*", "事件模式", "只置事件标志，不产生中断（配合 WFE）", T.VIOLET),
    ]
    y3 = 428
    for i, (macro, name, note, color) in enumerate(rows):
        yy = y3 + i * 26
        s.rect(40, yy, 820, 22, fill=T.BG2 if i % 2 else "none", rx=4)
        s.text(52, yy + 16, macro, size=11.5, mono=True, fill=color)
        s.text(300, yy + 16, name, size=11.5, fill=T.TEXT)
        s.text(380, yy + 16, note, size=11, fill=T.MUTED)
    s.footer("F1 系列必须开 AFIO 时钟：__HAL_RCC_AFIO_CLK_ENABLE()，否则 EXTI 不工作")
    return s


def nvic_interrupt_flow() -> Svg:
    s = Svg(W, H, "中断响应全流程", "从外设置标志到 ISR 返回，硬件帮你做了哪些事")
    s.header(tag="04 NVIC", tag_color=T.CYAN)

    steps = [
        ("① 外设置标志", "SR 寄存器的某位置 1", T.BLUE),
        ("② NVIC 仲裁", "比较抢占优先级，数值小者先响应", T.CYAN),
        ("③ 硬件自动入栈", "先压 xPSR，SP 停在 R0", T.VIOLET),
        ("④ 取向量表", "VTOR + 4×(IRQn+16)", T.AMBER),
        ("⑤ 执行 ISR", "清标志、处理数据、越短越好", T.GREEN),
        ("⑥ 出栈返回", "恢复现场，继续被打断的指令", T.PINK),
    ]
    x0, y0, bw, bh, gap = 40, 100, 196, 80, 18
    for i, (label, sub, color) in enumerate(steps):
        r, c = divmod(i, 3)
        x = x0 + c * (bw + 82)
        y = y0 + r * (bh + 56)
        s.rect(x, y, bw, bh, fill=T.PANEL, stroke=color, rx=8)
        s.text(x + 14, y + 28, label, size=14, fill=T.TEXT, weight="700")
        s.text(x + 14, y + 52, sub, size=10.5, fill=T.MUTED)
        if c < 2:
            s.arrow(x + bw + 4, y + bh / 2, x + bw + 78, y + bh / 2,
                    color=T.CYAN, sw=2, head=7, cls=f"fl{i}")
        if c == 2 and r == 0:
            s.arrow(x + bw / 2, y + bh + 2, x + bw / 2, y + bh + 40,
                    color=T.CYAN, sw=2, head=7)
        if r == 1 and c < 2:
            s.arrow(x + bw + 4, y + bh / 2, x + bw + 78, y + bh / 2,
                    color=T.CYAN, sw=2, head=7)
    s.add_style(anim_flow(".fl0", dur="1.2s", dash="7 10", shift=-17))
    s.add_style(anim_flow(".fl1", dur="1.2s", dash="7 10", shift=-17, ))
    s.add_style(anim_flow(".fl3", dur="1.2s", dash="7 10", shift=-17))
    s.add_style(anim_flow(".fl4", dur="1.2s", dash="7 10", shift=-17))

    # 栈帧
    s.title_block(40, 348, "硬件栈帧 32 字节：低地址在左，SP 指向 R0", color=T.VIOLET)
    regs = ["R0", "R1", "R2", "R3", "R12", "LR", "PC", "xPSR"]
    for i, r in enumerate(regs):
        x = 40 + i * 62
        s.rect(x, 360, 56, 40, fill=T.PANEL2, stroke=T.VIOLET, rx=4)
        s.text(x + 28, 385, r, size=12, anchor="middle", fill=T.TEXT, mono=True)
    s.text(548, 385, "高地址 →  硬件自动入栈，ISR 直接写 C", size=11,
           fill=T.MUTED)

    # 优先级分组
    s.title_block(40, 428, "优先级分组：谁可以打断谁", color=T.AMBER)
    rows = [("NVIC_PRIORITYGROUP_4", "4 位抢占 / 0 位子优先级", "只用抢占，最常用"),
            ("NVIC_PRIORITYGROUP_2", "2 位抢占 / 2 位子优先级", "同类外设内部排队"),
            ("同抢占优先级", "不能互相打断", "会按子优先级排队执行")]
    for i, (a, b, c) in enumerate(rows):
        yy = 444 + i * 24
        s.text(52, yy, a, size=11.5, mono=True, fill=T.CYAN)
        s.text(280, yy, b, size=11.5, fill=T.TEXT)
        s.text(500, yy, c, size=11, fill=T.MUTED)
    s.footer("ISR 里禁止 HAL_Delay / 浮点运算 / printf，必要时只置标志交给主循环处理")
    return s




def debug_swo() -> Svg:
    s = Svg(W, H, "调试与跟踪：SWD + SWO/ITM", "不用串口也能 printf，还能定位 HardFault")
    s.header(tag="17 调试", tag_color=T.ORANGE)

    # 左：连线
    s.rect(40, 82, 420, 250, fill=T.PANEL, stroke=T.STROKE, rx=8)
    s.text(58, 108, "接线（4 线 SWD + 1 线 SWO）", size=13, fill=T.TEXT,
           weight="600")
    s.rect(62, 130, 110, 170, fill=T.PANEL2, stroke=T.CYAN, rx=8)
    s.text(117, 154, "ST-Link", size=13, anchor="middle", fill=T.CYAN,
           weight="600")
    s.text(117, 174, "调试器", size=11, anchor="middle", fill=T.MUTED)
    s.rect(310, 130, 130, 170, fill=T.PANEL2, stroke=T.GREEN, rx=8)
    s.text(375, 154, "STM32", size=13, anchor="middle", fill=T.GREEN,
           weight="600")
    s.text(375, 174, "Cortex-M", size=11, anchor="middle", fill=T.MUTED)
    wires = [("SWCLK", T.BLUE, 188), ("SWDIO", T.CYAN, 210),
             ("SWO", T.AMBER, 232), ("NRST", T.RED, 254),
             ("GND", T.MUTED, 276)]
    for name, color, y in wires:
        s.line(172, y, 310, y, stroke=color, sw=2)
        s.text(241, y - 6, name, size=10.5, anchor="middle", fill=color,
               mono=True)
        s.circle(292 if name == "SWO" else 180, y, 3.4, fill=color,
                 cls=None if name == "GND" else f"w{name}")
    s.text(58, 314, "SWO=PB3，方向是 MCU → 调试器；必须共地。廉价 ST-Link 常没接 SWO",
           size=11, fill=T.AMBER)
    s.add_style(
        "@keyframes swd-run{0%{transform:translateX(0);opacity:0}"
        "15%{opacity:1}85%{opacity:1}100%{transform:translateX(110px);opacity:0}}"
        "@keyframes swo-run{0%{transform:translateX(0);opacity:0}"
        "15%{opacity:1}85%{opacity:1}100%{transform:translateX(-110px);opacity:0}}"
        ".wSWDIO{animation:swd-run 1.6s linear infinite;}"
        ".wSWCLK{animation:swd-run 1.6s linear infinite .4s;}"
        ".wSWO{animation:swo-run 1.2s linear infinite .2s;}"
        ".wNRST{animation:swd-run 2s linear infinite .8s;}"
    )

    # 右：ITM 输出
    s.rect(480, 82, 380, 250, fill=T.BG2, stroke=T.STROKE, rx=8)
    s.text(498, 108, "ITM 输出（SWV Console）", size=13, fill=T.TEXT, weight="600")
    s.code(498, 136, [
        "ITM_SendChar('T');        // 重定向 printf",
        "",
        "T=25.4C  adc=1024",
        "T=25.6C  adc=1031",
        "T=25.6C  adc=1028",
        "T=25.7C  adc=1035",
    ], size=11.5, lh=18, color=T.GREEN, cls="itm")
    s.add_style(
        "@keyframes itm-fade{0%,10%{opacity:.15}40%,100%{opacity:1}}"
        ".itm{animation:itm-fade 3s linear infinite;}"
    )
    s.text(498, 300, "异步 SWO 常见 2 MHz（约 2 Mbit/s，不是 2 MB/s）", size=11,
           fill=T.MUTED)
    s.text(498, 320, "比 UART 少占一个串口，且不干扰被测程序时序", size=11,
           fill=T.MUTED)

    # 下：HardFault 定位
    s.title_block(40, 364, "HardFault 四步定位法", color=T.RED)
    steps = [
        ("① CFSR / HFSR", "0xE000ED28 / ED2C", "总线、用法还是取指错误"),
        ("② BFAR / MMFAR", "0xE000ED38 / ED34", "非法访问落到哪个地址"),
        ("③ 反查 PC", "栈帧 PC → addr2line", "对应到哪一行 C"),
        ("④ 常见原因", "空指针 / 栈溢出", "越界、递归、中断里用浮点"),
    ]
    for i, (t, sub, note) in enumerate(steps):
        x = 40 + i * 206
        s.rect(x, 376, 196, 82, fill=T.PANEL, stroke=T.STROKE, rx=8)
        s.text(x + 14, 400, t, size=12.5, fill=T.TEXT, weight="700")
        s.text(x + 14, 420, sub, size=10.5, mono=True, fill=T.CYAN)
        s.text(x + 14, 442, note, size=10, fill=T.MUTED)
        if i < 3:
            s.arrow(x + 198, 417, x + 204, 417, color=T.STROKE, sw=2, head=5)
    s.footer("DWT->CYCCNT 可做微秒级计时：使能 DWT_CTRL 后读 CYCCNT，比 HAL_GetTick 精确 1000 倍")
    return s


ALL = [gpio_blink, gpio_input_interrupt, nvic_interrupt_flow, debug_swo]

NAMES = {
    "gpio_blink": "gpio-blink",
    "gpio_input_interrupt": "gpio-input-interrupt",
    "nvic_interrupt_flow": "nvic-interrupt-flow",
    "debug_swo": "debug-swo",
}

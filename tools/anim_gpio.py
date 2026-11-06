#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GPIO / 中断 / 调试类动画。"""

from __future__ import annotations

from svgkit import Svg, T, anim_blink, anim_fade, anim_flow, anim_tx, css_kf

W, H = 900, 620

REDUCED = "@media (prefers-reduced-motion: reduce){*{animation:none!important}}"


def _step_highlight(prefix: str, n: int, period=6.0, window=0.22,
                    peak=0.35, rest=0.06) -> str:
    css = []
    step = 100.0 / n
    for i in range(n):
        a = i * step
        b = min(a + step * window, 99.2)
        name = f"{prefix}{i}-hl"
        css.append(
            f"@keyframes {name}{{0%,{a:.2f}%{{opacity:{rest}}}"
            f"{a + 0.25:.2f}%,{b:.2f}%{{opacity:{peak}}}"
            f"{min(b + 0.25, 100):.2f}%,100%{{opacity:{rest}}}}}"
        )
        css.append(f".{prefix}{i}{{animation:{name} {period}s linear infinite;}}")
    return "\n".join(css)


def _seq_flash(prefix: str, n: int, period=5.0, window=0.55,
               peak=1.0, rest=0.22) -> str:
    css = []
    step = 100.0 / n
    for i in range(n):
        a = i * step
        b = min(a + step * window, 99.2)
        name = f"{prefix}{i}-sq"
        css.append(
            f"@keyframes {name}{{0%,{a:.2f}%{{opacity:{rest}}}"
            f"{a + 0.3:.2f}%,{b:.2f}%{{opacity:{peak}}}"
            f"{min(b + 0.3, 100):.2f}%,100%{{opacity:{rest}}}}}"
        )
        css.append(f".{prefix}{i}{{animation:{name} {period}s linear infinite;}}")
    return "\n".join(css)



def gpio_blink() -> Svg:
    s = Svg(W, H, "GPIO 推挽输出点亮 LED", "PA5 每 500 ms 翻转一次，电流路径与波形同步演示")
    s.header(tag="03 GPIO", tag_color=T.GREEN)

    # ---------------- 左：电路 ----------------
    s.rect(40, 80, 470, 262, fill=T.PANEL, stroke=T.STROKE, rx=8)
    s.text(58, 100, "外接 LED：高电平点亮",
           size=12, fill=T.TEXT, weight="600")
    s.text(58, 116, "BluePill 板载灯是 PC13，低电平才亮",
           size=11, fill=T.MUTED)

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
    hit = 6
    for i in range(14):
        s.rect(62 + i * 56, y - 10, 52, 32, fill=T.PANEL2, stroke=T.STROKE, rx=4)
        if i != hit:   # 命中的那格会被高亮块盖住，写了也看不见
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
    s = Svg(W, H, "中断响应全流程",
            "外设置位 → NVIC 仲裁 → 硬件入栈 → 取向量 → ISR → 出栈；数字来自 Cortex-M3")
    s.header(title="NVIC 响应链：从 SR 置位到 ISR 返回",
             subtitle="mechanism · FA-002 continuous-line · F103 / Cortex-M3",
             tag="04 NVIC", tag_color=T.CYAN)
    css = []
    stages = [
        ("① 外设置位", "EXTI_PR / TIMx_SR", "IRQn 例：EXTI0=6", T.BLUE),
        ("② NVIC 仲裁", "抢占优先级更小先跑", "GROUP_4：4 抢占 / 0 子", T.CYAN),
        ("③ 硬件入栈", "R0-R3,R12,LR,PC,xPSR", "固定 32 B · SP→R0", T.VIOLET),
        ("④ 取向量", "VTOR + 4×(IRQn+16)", "Reset=0，IRQ 从 16 起", T.AMBER),
        ("⑤ 执行 ISR", "清标志 · 置事件 · 快退", "禁 HAL_Delay / printf", T.GREEN),
        ("⑥ 出栈返回", "EXC_RETURN 恢复现场", "可 tail-chain 下一 IRQ", T.PINK),
    ]
    x0, y0, bw, bh, gapx, gapy = 36, 96, 200, 96, 22, 18
    for i, (title, a, b, color) in enumerate(stages):
        r, c = divmod(i, 3)
        x = x0 + c * (bw + gapx)
        y = y0 + r * (bh + gapy + 28)
        s.rect(x, y, bw, bh, fill=T.PANEL, stroke=color, rx=8)
        s.rect(x, y, bw, 5, fill=color, rx=2)
        s.text(x + 14, y + 30, title, size=13, fill=T.TEXT, weight="700")
        s.text(x + 14, y + 54, a, size=11, fill=T.MUTED, mono=True)
        s.text(x + 14, y + 76, b, size=10.5, fill=T.DIM)
        s.rect(x, y, bw, bh, fill=color, rx=8, opacity=0.12, cls=f"nv{i}")
        if c < 2:
            s.arrow(x + bw + 3, y + bh / 2, x + bw + gapx - 3, y + bh / 2,
                    color=T.CYAN, sw=2, head=7, cls="nv-flow")
        if c == 2 and r == 0:
            s.arrow(x + bw / 2, y + bh + 2, x + bw / 2, y + bh + 24,
                    color=T.CYAN, sw=2, head=7, cls="nv-flow")
    css.append(_step_highlight("nv", 6, period=7.2, window=0.14, peak=0.32))
    css.append(anim_flow(".nv-flow", dur="1.2s", dash="7 10", shift=-17))
    s.title_block(36, 360, "硬件栈帧 8×4 B（低地址在左，SP 停在 R0）", color=T.VIOLET)
    regs = ["R0", "R1", "R2", "R3", "R12", "LR", "PC", "xPSR"]
    for i, reg in enumerate(regs):
        x = 36 + i * 64
        s.rect(x, 384, 58, 44, fill=T.PANEL2, stroke=T.VIOLET, rx=4)
        s.text(x + 29, 410, reg, size=12, anchor="middle", fill=T.TEXT, mono=True)
        s.rect(x, 384, 58, 44, fill=T.VIOLET, rx=4, opacity=0.1, cls=f"sf{i}")
    css.append(_seq_flash("sf", 8, period=4.8, window=0.4, peak=0.55, rest=0.08))
    s.text(560, 410, "ISR 可直接用 C；返回靠 EXC_RETURN", size=11, fill=T.MUTED)
    s.rect(36, 450, 828, 100, fill=T.BG2, stroke=T.AMBER, rx=8)
    s.text(52, 478, "同抢占优先级不能互抢 · Tail-chaining 可省一对出入栈",
           size=13, fill=T.TEXT, weight="700")
    s.text(52, 504, "例：TIM2(IRQ=28) 跑着时 EXTI0(IRQ=6) 若抢占更高 → 打断；同级则排队。",
           size=12, fill=T.MUTED)
    s.text(52, 528, "ISR 只清 SR / 置标志；长活丢主循环。匹配 sample-04-nvic-preempt-flow。",
           size=12, fill=T.DIM)
    css.append(REDUCED)
    s.add_style("\n".join(css))
    s.footer(note="自绘矢量动画 · FA-002 · NVIC 响应链，非逻辑分析仪实拍",
             label="自绘矢量动画 · STM32 知识轨")
    return s



def debug_swo() -> Svg:
    s = Svg(W, H, "SWD 双向调试，SWO 单向跟踪",
            "STM32F103 · SWDIO 传数据，SWCLK 给时钟；跟踪字符另走 PB3")
    s.header(tag="17 调试", tag_color=T.ORANGE)

    # SWD is bidirectional data plus a probe-driven clock. Neither reset nor
    # voltage reference is a stream of debug packets.
    s.rect(40, 88, 180, 227, fill=T.PANEL2, stroke=T.BLUE, rx=4, sw=2)
    s.rect(680, 88, 180, 227, fill=T.PANEL, stroke=T.STROKE, rx=4, sw=2)
    s.text(56, 113, "STM32F103", size=17, fill=T.BLUE, weight="700")
    s.text(56, 133, "目标板 · Cortex-M3", size=12, fill=T.MUTED)
    s.text(696, 113, "调试探针", size=17, weight="700")
    s.text(696, 133, "需支持 SWO 接收", size=12, fill=T.MUTED)
    wires = [
        (167, "PA13", "SWDIO", "数据 · 双向", T.BLUE, "both"),
        (199, "PA14", "SWCLK", "时钟 · 探针输出", T.BLUE, "left"),
        (231, "NRST", "nRESET", "低有效复位 · 可选连接", T.RED, "reset"),
        (263, "VDD", "VTref", "目标电压参考 · 非探针供电输出", T.MUTED, "right"),
        (295, "GND", "GND", "共地", T.MUTED, "none"),
    ]
    for y, pin, port, role, color, direction in wires:
        s.text(204, y + 4, pin, size=14, mono=True, anchor="end", fill=color)
        s.text(696, y + 4, port, size=14, mono=True, fill=color)
        s.text(450, y - 10, role, size=13, anchor="middle", fill=color)
        if direction == "both":
            s.arrow(450, y, 222, y, color=color, sw=2)
            s.arrow(450, y, 678, y, color=color, sw=2)
        elif direction in ("left", "reset"):
            s.arrow(678, y, 222, y, color=color, sw=2,
                    dash="5 5" if direction == "reset" else None)
        elif direction == "right":
            s.arrow(222, y, 678, y, color=color, sw=1.5)
        else:
            s.line(222, y, 678, y, stroke=color, sw=1.5)
    s.text(40, 339, "SWD 调试通道与下面的 SWO 输出通道分开；SWO 不占用 USART。",
           size=14, fill=T.BLUE)

    # A software trace byte follows the same five labelled stages in every
    # frame. The moving dot denotes order, not measured link latency.
    s.line(40, 356, 860, 356, stroke=T.GRID, sw=1)
    s.text(40, 384, "一个字符怎样到达 SWV 控制台", size=17, weight="700", fill=T.GREEN)
    stages = [
        (40, 132, "固件", "写入字符 'A'"),
        (218, 132, "ITM", "Port 0"),
        (396, 132, "TPIU", "打包与串行输出"),
        (574, 132, "PB3", "TRACESWO"),
        (752, 108, "探针→主机", "SWV：'A'"),
    ]
    for i, (x, width, label, note) in enumerate(stages):
        s.rect(x, 405, width, 64, fill=T.PANEL, stroke=T.GREEN, rx=4, sw=1.5)
        s.text(x + width / 2, 432, label, size=17, anchor="middle",
               fill=T.GREEN, weight="700")
        s.text(x + width / 2, 453, note, size=12, anchor="middle", fill=T.MUTED)
        s.line(x + width / 2, 470, x + width / 2, 493, stroke=T.GREEN, sw=1)
        if i < len(stages) - 1:
            s.arrow(x + width + 4, 437, stages[i + 1][0] - 4, 437,
                    color=T.GREEN, sw=2, head=6)
    s.arrow(106, 493, 806, 493, color=T.GREEN, sw=1.5, head=6)
    s.circle(106, 493, 5, fill=T.GREEN, cls="trace-byte")
    s.text(40, 528, "先配置 ITM、异步 TRACE 与 PB3；主机接收设置须与稳定的 HCLK、SWO 分频匹配。",
           size=13, fill=T.MUTED)
    s.text(40, 552, "printf 需重定向到 ITM；写日志有开销，等待或丢弃取决于输出实现与接收状态。",
           size=13, fill=T.MUTED)
    s.add_style(
        "@keyframes trace-byte{"
        "0%,8%{transform:translateX(0);opacity:1}"
        "22%,28%{transform:translateX(178px);opacity:1}"
        "42%,48%{transform:translateX(356px);opacity:1}"
        "62%,68%{transform:translateX(534px);opacity:1}"
        "82%,92%{transform:translateX(700px);opacity:1}"
        "97%,100%{transform:translateX(700px);opacity:0}}"
        ".trace-byte{animation:trace-byte 6.4s linear infinite;}"
        "@media(prefers-reduced-motion:reduce){"
        ".trace-byte{animation:none!important;display:none}}"
        "@media print{.trace-byte{animation:none!important;display:none}}"
    )
    s.footer(note="点的移动仅表示传输顺序", label="自绘矢量动画 · 原理示意 / 非实拍")
    return s


ALL = [gpio_blink, gpio_input_interrupt, nvic_interrupt_flow, debug_swo]

NAMES = {
    "gpio_blink": "gpio-blink",
    "gpio_input_interrupt": "gpio-input-interrupt",
    "nvic_interrupt_flow": "nvic-interrupt-flow",
    "debug_swo": "debug-swo",
}

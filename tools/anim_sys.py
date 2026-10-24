#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""系统类动画：定时器/PWM、定时器模式、SAR ADC、DMA、看门狗、IAP、RTOS、低功耗。"""

from __future__ import annotations

from svgkit import Svg, T, anim_fade, anim_flow, anim_rotate, anim_tx, css_kf

W, H = 900, 620


def _seq_flash(prefix: str, n: int, period=5.0, window=0.55,
               peak=1.0, rest=0.22) -> str:
    """依次高亮：窗口内为 peak，其余时间为 rest。"""
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


# --------------------------------------------------------------------------- 定时器 PWM


def timer_pwm() -> Svg:
    s = Svg(W, H, "定时器怎么产生 PWM",
            "CNT 从 0 数到 ARR；CNT < CCR 输出高，CNT ≥ CCR 输出低")
    s.header(tag="05 定时器", tag_color=T.CYAN)

    s.text(40, 100, "CNT 计数（ARR = 999）", size=12, fill=T.MUTED)
    s.rect(40, 112, 820, 30, fill=T.BG2, stroke=T.STROKE, rx=6)
    s.rect(40, 112, 250, 30, fill=T.CYAN, rx=6, opacity=0.25)
    s.line(290, 104, 290, 148, stroke=T.AMBER, sw=2)
    s.text(290, 164, "CCR = 300（比较点）", size=11, anchor="middle",
           fill=T.AMBER)
    s.rect(44, 116, 20, 22, fill=T.CYAN, rx=4, cls="cnt")
    s.text(54, 132, "CNT", size=9, anchor="middle", fill="#0b1220", weight="700")
    s.add_style(anim_tx(".cnt", dur="3s", x1=0, x2=812))
    for i in range(6):
        s.text(40 + i * 164, 186, str(int(999 * i / 5)), size=10, fill=T.DIM,
               anchor="middle")

    s.text(40, 216, "比较结果", size=12, fill=T.MUTED)
    s.rect(40, 228, 400, 46, fill=T.PANEL, stroke=T.GREEN, rx=8)
    s.text(58, 256, "CNT < CCR → 输出高电平（点亮）", size=12, fill=T.GREEN)
    s.rect(460, 228, 400, 46, fill=T.PANEL, stroke=T.RED, rx=8)
    s.text(478, 256, "CNT ≥ CCR → 输出低电平（熄灭）", size=12, fill=T.RED)

    s.text(40, 306, "输出波形：CCR = 300 的定格（30%）", size=12, fill=T.MUTED)
    s.axis(40, 318, 560, 70)
    bits = []
    for _ in range(4):
        bits += [1] * 3 + [0] * 7
    s.waveform(40, 322, 560, 62, bits, color=T.CYAN, sw=2.4)

    s.rect(620, 318, 240, 70, fill=T.PANEL, stroke=T.STROKE, rx=10)
    s.text(638, 340, "呼吸色条（不是左边那一帧）", size=11, fill=T.MUTED)
    s.rect(638, 350, 200, 18, fill=T.BG2, stroke=T.STROKE, rx=4)
    s.rect(639, 351, 200, 16, fill=T.CYAN, rx=3, cls="duty")
    s.add_style(
        css_kf("duty-w", [("0%,100%", "transform:scaleX(0.08)"),
                          ("50%", "transform:scaleX(1)")])
        + ".duty{animation:duty-w 4s ease-in-out infinite;"
          "transform-box:fill-box;transform-origin:left center;}")
    s.text(638, 382, "色条 8%→100%：示意不断改 CCR", size=10.5, fill=T.AMBER)

    s.title_block(40, 408, "公式（72 MHz 已是定时器时钟）", color=T.GREEN)
    s.rect(40, 420, 820, 132, fill=T.BG2, stroke=T.STROKE, rx=10)
    s.code(56, 444, [
        "定时器时钟 = APB 时钟 ×2（预分频 >1 时）     // APB1=36 → 定时器 72 MHz",
        "计数时钟：fCK_CNT = 72 MHz / (PSC + 1)         // PSC = 71 → 1 MHz",
        "PWM 频率：fPWM   = fCK_CNT / (ARR + 1)         // ARR = 999 → 1 kHz",
        "占空比  ：Duty   = CCR / (ARR + 1)             // CCR = 300 → 30%",
        "溢出时间：T      = (ARR + 1)(PSC + 1) / 72 MHz // 1 ms 定时中断",
    ], size=12.5, lh=22)
    s.footer("频率与分辨率互相矛盾：ARR 越大分辨率越高但频率越低（见 05 章权衡表）")
    return s



def timer_modes() -> Svg:
    s = Svg(W, H, "定时器的四种典型用法",
            "同一个计数器，配上不同的比较/捕获通道就能干四件事")
    s.header(tag="05 定时器", tag_color=T.VIOLET)

    panels = [
        ("① 输出比较翻转", "CNT = CCR 时翻转引脚", T.CYAN,
         [0, 0, 1, 1, 0, 0, 1, 1]),
        ("② PWM 输出", "CNT < CCR 输出高", T.GREEN,
         [1, 1, 0, 0, 1, 1, 0, 0]),
        ("③ 输入捕获测脉宽", "边沿触发时把 CNT 存进 CCR", T.AMBER,
         [0, 1, 1, 1, 0, 0, 0, 0]),
        ("④ 编码器接口", "A/B 相正交自动加减计数", T.PINK,
         [1, 0, 1, 0, 1, 0, 1, 0]),
    ]
    for i, (title, sub, color, bits) in enumerate(panels):
        r, c = divmod(i, 2)
        x = 40 + c * 420
        y = 92 + r * 176
        s.rect(x, y, 400, 152, fill=T.PANEL, stroke=T.STROKE, rx=12)
        s.rect(x, y, 4, 152, fill=color, rx=2)
        s.text(x + 18, y + 26, title, size=13.5, fill=T.TEXT, weight="700")
        s.text(x + 18, y + 46, sub, size=11, fill=T.MUTED)
        if i != 3:
            s.axis(x + 18, y + 62, 364, 54)
            s.waveform(x + 18, y + 66, 364, 46, bits, color=color, sw=2.2)
        if i == 0:
            s.circle(x + 18 + 364 * 0.25, y + 92, 5, fill=color, cls="mk0")
            s.circle(x + 18 + 364 * 0.75, y + 92, 5, fill=color, cls="mk0")
            s.add_style(anim_fade(".mk0", dur="1.6s", a=0.2, b=1.0))
        elif i == 1:
            s.rect(x + 18, y + 66, 46, 22, fill=color, rx=3, opacity=0.2,
                   cls="mk1")
            s.add_style(anim_fade(".mk1", dur="2s", a=0.15, b=0.6))
        elif i == 2:
            s.line(x + 18 + 364 * 0.125, y + 58, x + 18 + 364 * 0.125,
                   y + 130, stroke=color, sw=1.4, dash="4 4")
            s.line(x + 18 + 364 * 0.5, y + 58, x + 18 + 364 * 0.5, y + 130,
                   stroke=color, sw=1.4, dash="4 4")
            s.text(x + 18, y + 146, "上升沿锁 CCR1，下降沿锁 CCR2，脉宽 = ΔCCR × tCK",
                   size=10, fill=T.AMBER)
        else:
            s.text(x + 18, y + 70, "A", size=11, fill=color, weight="700")
            s.waveform(x + 36, y + 58, 300, 22,
                       [1, 1, 0, 0, 1, 1, 0, 0], color=color, sw=2.2)
            s.text(x + 18, y + 104, "B", size=11, fill=color, weight="700")
            s.waveform(x + 36, y + 92, 300, 22,
                       [0, 1, 1, 0, 0, 1, 1, 0], color=color, sw=2.2)
            s.text(x + 18, y + 140, "B 比 A 落后 90° 为正转，超前为反转（正交两相）",
                   size=10, fill=T.PINK)

    s.title_block(40, 448, "选型速查", color=T.CYAN)
    rows = [("要固定频率的方波", "PWM 模式 1 + ARR/PSC 定时基"),
            ("要测外部脉冲宽度/频率", "输入捕获 + 从模式复位"),
            ("要读旋钮/电机转速", "编码器接口模式（TIM2/3/4 支持）"),
            ("要精确延时/定时中断", "基本定时器 TIM6/7 或 SysTick")]
    for i, (k, v) in enumerate(rows):
        x = 40 + (i % 2) * 420
        y = 462 + (i // 2) * 34
        s.rect(x, y, 400, 30, fill=T.BG2, stroke=T.STROKE, rx=8)
        s.text(x + 14, y + 20, k, size=11, fill=T.TEXT)
        s.text(x + 208, y + 20, v, size=10.5, fill=T.MUTED)
    s.footer("高级定时器 TIM1/TIM8 还要额外使能 MOE（HAL_TIM_PWM_Start 内部已处理）")
    return s


# --------------------------------------------------------------------------- SAR ADC


def adc_sar() -> Svg:
    s = Svg(W, H, "ADC 逐次逼近（SAR）到底在做什么",
            "12 位精度 = 12 次「猜一半 + 比较」，硬件在几微秒内完成")
    s.header(tag="09 ADC", tag_color=T.AMBER)

    s.text(40, 96, "12 位 SAR 寄存器：从 bit11 开始逐位试填", size=12,
           fill=T.MUTED)
    for i in range(12):
        b = 11 - i
        x = 40 + i * 68
        s.rect(x, 108, 62, 42, fill=T.PANEL, stroke=T.STROKE, rx=8)
        s.text(x + 31, 126, f"bit{b}", size=10, anchor="middle", fill=T.MUTED)
        s.text(x + 31, 142, "?", size=13, anchor="middle", fill=T.DIM, mono=True)
        s.rect(x, 108, 62, 42, fill=T.AMBER, rx=8, opacity=0.18, cls=f"s{i}")
    s.add_style(_seq_flash("s", 12, period=6.0, window=0.45, peak=0.4, rest=0.08))
    s.text(40, 172, "当前正在比较的位会被点亮；比较完就固定下来（1 或 0）",
           size=11, fill=T.DIM)

    s.rect(40, 194, 400, 150, fill=T.PANEL, stroke=T.STROKE, rx=12)
    s.text(58, 220, "比较器在比较什么", size=12.5, fill=T.TEXT, weight="700")
    s.text(58, 246, "DAC 输出（当前猜测值）", size=11, fill=T.MUTED)
    s.text(58, 266, "VIN（采样保持电容上的电压）", size=11, fill=T.MUTED)
    s.line(58, 286, 420, 286, stroke=T.GRID, sw=1)
    s.text(58, 308, "DAC > VIN → 清掉这一位", size=11.5, fill=T.RED)
    s.text(58, 328, "DAC ≤ VIN → 保留这一位", size=11.5, fill=T.GREEN)

    s.rect(460, 194, 400, 150, fill=T.BG2, stroke=T.STROKE, rx=12)
    s.text(478, 220, "例：VIN = 0.5 × VREF → 结果 0x800", size=12, fill=T.TEXT,
           weight="700")
    s.code(478, 244, [
        "bit11: 猜 2048  → 2048 <= 2048  保留 1",
        "bit10: 猜 3072  → 3072 >  2048  清零 0",
        "bit9 : 猜 2560  → 2560 >  2048  清零 0",
        "bit8 : 猜 2304  → 2304 >  2048  清零 0",
        "bit7 : 猜 2176  → 2176 >  2048  清零 0",
        "…最终 0b1000_0000_0000 = 2048",
    ], size=11, lh=17, color=T.GREEN)

    s.title_block(40, 366, "采样时间怎么定", color=T.CYAN)
    rows = [            ("源阻抗 ≤ 1 kΩ", "1.5 周期", "运放直驱 / 小电阻分压"),
            ("约 10 kΩ", "13.5 周期", "常见电位器"),
            ("约 50 kΩ", "55.5 周期", "高阻传感器"),
            ("≥ 100 kΩ", "239.5 周期", "或加跟随器，否则偏低")]
    s.rect(40, 378, 500, 116, fill=T.BG2, stroke=T.STROKE, rx=10)
    for i, (k, v, note) in enumerate(rows):
        y = 400 + i * 24
        s.text(58, y, k, size=11, fill=T.TEXT)
        s.text(216, y, v, size=11, fill=T.CYAN)
        s.text(316, y, note, size=10.5, fill=T.MUTED)

    s.rect(560, 378, 300, 116, fill=T.PANEL, stroke=T.STROKE, rx=10)
    s.text(578, 402, "误差与换算", size=12, fill=T.TEXT, weight="700")
    for i, t in enumerate(["1 LSB = VREF / 4096",
                           "量化误差是 ±0.5 LSB",
                           "电压 = 码值 × VREF / 4096",
                           "分母是 4096，不是 4095"]):
        s.text(578, 424 + i * 18, "· " + t, size=10.5, fill=T.MUTED)

    s.rect(40, 504, 820, 28, fill=T.BG2, stroke=T.STROKE, rx=8)
    s.text(58, 523, "读数跳动：去耦、加长采样、滑动平均。读 Vrefint 可反推真实 VDDA",
           size=11, fill=T.AMBER)
    s.footer("F1 的 ADC 时钟最高 14 MHz、F4 最高 36 MHz；时钟超了读数会明显失真")
    return s




# --------------------------------------------------------------------------- DMA 循环


def dma_circular() -> Svg:
    s = Svg(W, H, "DMA 循环模式：CPU 与搬运工并行工作",
            "ADC 每采一个数，DMA 写入数组；半满 HT、写满 TC，各进一次中断")
    s.header(tag="10 DMA", tag_color=T.GREEN)

    s.rect(40, 96, 150, 90, fill=T.PANEL, stroke=T.AMBER, rx=12)
    s.text(115, 124, "ADC1", size=14, anchor="middle", fill=T.AMBER,
           weight="700")
    s.text(115, 146, "CH0 · PA0", size=11, anchor="middle", fill=T.MUTED)
    s.text(115, 168, "DR 寄存器", size=11, anchor="middle", fill=T.DIM)

    s.rect(300, 96, 170, 90, fill=T.PANEL, stroke=T.CYAN, rx=12)
    s.text(385, 122, "DMA1 CH1", size=14, anchor="middle", fill=T.CYAN,
           weight="700")
    s.text(385, 144, "循环模式 / 半字", size=11, anchor="middle", fill=T.MUTED)
    s.text(385, 166, "MINC = 1（地址自增）", size=10, anchor="middle",
           fill=T.DIM)

    s.arrow(194, 141, 296, 141, color=T.AMBER, sw=2.4, cls="w1")
    s.arrow(474, 141, 636, 141, color=T.CYAN, sw=2.4, cls="w2")
    s.add_style(anim_flow(".w1", dur="1.2s", dash="7 10", shift=-17))
    s.add_style(anim_flow(".w2", dur="1.2s", dash="7 10", shift=-17))
    for i in range(3):
        s.circle(206, 141, 4.5, fill=T.CYAN, cls=f"pk{i}")
    s.add_style("\n".join(
        css_kf(f"pk{i}-mv", [("0%", "transform:translateX(0)"),
                             ("45%", "transform:translateX(420px)"),
                             ("46%,100%", "transform:translateX(420px)")])
        + f".pk{i}{{animation:pk{i}-mv 1.6s linear infinite {i * 0.5:.1f}s;}}"
        for i in range(3)))

    s.text(640, 108, "RAM 数组 buf[8]", size=12, fill=T.TEXT, weight="600")
    for i in range(8):
        x = 640 + (i % 4) * 60
        y = 120 + (i // 4) * 52
        s.rect(x, y, 52, 40, fill=T.PANEL2, stroke=T.STROKE, rx=8)
        s.text(x + 26, y + 16, f"[{i}]", size=10, anchor="middle", fill=T.MUTED)
        s.text(x + 26, y + 32, "----", size=10, anchor="middle", fill=T.DIM,
               mono=True)
        s.rect(x, y, 52, 40, fill=T.CYAN, rx=8, opacity=0.2, cls=f"b{i}")
    s.add_style(_seq_flash("b", 8, period=4.0, window=0.55, peak=0.48, rest=0.1))

    s.rect(40, 214, 820, 88, fill=T.BG2, stroke=T.STROKE, rx=10)
    s.text(58, 240, "CPU 同时在干什么？", size=12.5, fill=T.TEXT, weight="700")
    s.text(58, 262, "滤波 / 通信 / 刷屏 / 跑 PID —— 一次搬运都不参与，"
                    "总线空闲时 DMA 自动抢占一个周期", size=11, fill=T.MUTED)
    s.text(58, 284, "轮询把 CPU 绑在采样循环里；中断是每样本进一次 ISR；"
                    "DMA 只需半满、全满两次中断", size=11, fill=T.AMBER)

    s.title_block(40, 322, "DMA 使用四步走", color=T.CYAN)
    steps = [("① 使能时钟", "F1 在 AHB，F4 在 AHB1"),
             ("② 配通道映射", "F1 固定通道表，F4 用 Stream+Channel"),
             ("③ 配参数", "方向 / 宽度 / 自增 / 循环 / 优先级"),
             ("④ 开中断", "半传输 + 传输完成 + 错误")]
    for i, (k, v) in enumerate(steps):
        x = 40 + i * 208
        s.rect(x, 336, 196, 56, fill=T.PANEL, stroke=T.STROKE, rx=10)
        s.text(x + 14, 360, k, size=11.5, fill=T.CYAN, weight="600")
        s.text(x + 14, 380, v, size=10, fill=T.MUTED)

    s.rect(40, 408, 820, 132, fill=T.BG2, stroke=T.STROKE, rx=10)
    s.code(56, 432, [
        "HAL_ADC_Start_DMA(&hadc1, (uint32_t *)adc_buf, 8);   // 8 个半字，循环",
        "",
        "void HAL_ADC_ConvHalfCpltCallback(ADC_HandleTypeDef *h) { 处理前 4 个 }",
        "void HAL_ADC_ConvCpltCallback(ADC_HandleTypeDef *h)     { 处理后 4 个 }",
        "",
        "// 易错点：缓冲区要 4 字节对齐、加 volatile，H7 上还要处理 D-Cache 一致性",
    ], size=12, lh=21)
    s.footer("F1 只有 7 个 DMA 通道、没有 FIFO；F4/H7 是 Stream + FIFO + 双缓冲，映射表见 10 章")
    return s


# --------------------------------------------------------------------------- 看门狗


def iwdg_window() -> Svg:
    s = Svg(W, H, "IWDG 喂晚了复位，WWDG 喂早了也复位",
            "IWDG 走 LSI（典型 40 kHz，数据手册约 30~60 kHz）；数到 0 才复位")
    s.header(tag="11 看门狗", tag_color=T.RED)

    s.text(40, 96, "12 位递减计数器（0xFFF → 0）", size=12, fill=T.MUTED)
    s.rect(40, 108, 820, 34, fill=T.BG2, stroke=T.STROKE, rx=8)
    s.rect(41, 109, 818, 32, fill=T.RED, rx=8, opacity=0.35, cls="dec")
    s.add_style(
        css_kf("dec-w", [("0%", "transform:scaleX(1)"),
                         ("100%", "transform:scaleX(0.02)")])
        + ".dec{animation:dec-w 3s linear infinite;"
          "transform-box:fill-box;transform-origin:right center;}")
    s.text(48, 132, "0xFFF", size=10, fill=T.WHITE, mono=True)
    s.text(820, 132, "0", size=10, fill=T.WHITE, anchor="end", mono=True)

    s.rect(40, 160, 400, 110, fill=T.PANEL, stroke=T.STROKE, rx=12)
    s.text(58, 186, "正常喂狗", size=12.5, fill=T.GREEN, weight="700")
    s.text(58, 210, "在计数器归零之前重装（写 0xAAAA）", size=11, fill=T.MUTED)
    s.text(58, 232, "HAL_IWDG_Refresh(&hiwdg) 放在主循环里", size=11,
           fill=T.CYAN, mono=True)
    s.text(58, 254, "超时公式：T = (4 × 2^PR) × (RLR+1) / 40 kHz", size=10.5,
           fill=T.AMBER)

    s.rect(460, 160, 400, 110, fill=T.PANEL, stroke=T.STROKE, rx=12)
    s.text(478, 186, "WWDG 的「窗口」", size=12.5, fill=T.ORANGE, weight="700")
    s.text(478, 210, "喂太早（计数器还大于窗口值）→ 立刻复位", size=11,
           fill=T.MUTED)
    s.text(478, 232, "窗口内喂狗才有效，能发现「跑太快」的异常", size=11,
           fill=T.MUTED)
    s.text(478, 254, "WWDG 时钟来自 PCLK1，精度更高但时间更短", size=10.5,
           fill=T.AMBER)

    s.title_block(40, 292, "IWDG 与 WWDG 怎么选", color=T.CYAN)
    s.rect(40, 304, 820, 116, fill=T.BG2, stroke=T.STROKE, rx=10)
    heads = ["", "时钟源", "超时范围", "能发现「跑太快」", "适用场景"]
    for i, hd in enumerate(heads):
        s.text(60 + i * 160, 326, hd, size=11, fill=T.CYAN, weight="600")
    rows = [("IWDG", "LSI 40 kHz", "约 0.1 ms ~ 26 s", "不能",
             "主时钟挂了也能复位"),
            ("WWDG", "PCLK1/4096", "约 0.1~58 ms", "能",
             "要发现程序跑太快")]
    for r, row in enumerate(rows):
        for i, v in enumerate(row):
            s.text(60 + i * 160, 350 + r * 26, v, size=10.5,
                   fill=T.TEXT if i == 0 else T.MUTED, mono=(i == 0))
    s.text(60, 404, "单步会被 IWDG 复位：调试时打开 DBGMCU 的 IWDG_STOP / WWDG_STOP，"
                    "让计数器在 halt 时冻住", size=10.5, fill=T.AMBER)

    s.rect(40, 434, 820, 106, fill=T.BG2, stroke=T.STROKE, rx=10)
    s.code(56, 458, [
        "hiwdg.Instance       = IWDG;",
        "hiwdg.Init.Prescaler = IWDG_PRESCALER_64;   // 40 kHz / 64 = 625 Hz",
        "hiwdg.Init.Reload    = 624;                 // (624+1)/625 Hz = 1 s",
        "HAL_IWDG_Init(&hiwdg);      // 一旦启动就无法关闭（只能复位）",
        "HAL_IWDG_Refresh(&hiwdg);   // 主循环里定期喂狗",
    ], size=12, lh=19)
    s.footer("喂狗要放在「确认所有任务都跑过一圈」的位置，而不是无脑塞进定时中断里")
    return s




# --------------------------------------------------------------------------- IAP 升级


def flash_iap() -> Svg:
    s = Svg(W, H, "IAP：Bootloader + APP 双区（需要 ≥256 KB Flash）",
            "F103C8 只有 64 KB，放不下这张图；它的单区划分见第 12 章")
    s.header(tag="12 IAP", tag_color=T.VIOLET)

    blocks = [
        ("Bootloader", "0x0800_0000 ~ 0x0800_7FFF", "32 KB：只做升级与跳转", T.CYAN),
        ("APP A（旧固件）", "0x0800_8000 ~ 0x0801_FFFF", "96 KB：当前正在运行", T.GREEN),
        ("APP B（新固件）", "0x0802_0000 ~ 0x0803_7FFF", "96 KB：升级时写入这里", T.AMBER),
        ("参数区", "0x0803_8000 ~ 0x0803_87FF", "2 KB：跳转标志 / 版本 / 校验和", T.VIOLET),
    ]
    for i, (name, addr, note, color) in enumerate(blocks):
        y = 92 + i * 60
        s.rect(40, y, 500, 50, fill=T.PANEL, stroke=color, rx=10)
        s.rect(40, y, 5, 50, fill=color, rx=3)
        s.text(58, y + 22, name, size=12.5, fill=T.TEXT, weight="600")
        s.text(58, y + 40, note, size=10, fill=T.MUTED)
        s.text(352, y + 30, addr, size=9.5, mono=True, fill=color)
        s.rect(40, y, 500, 50, fill=color, rx=10, opacity=0.14, cls=f"fb{i}")
    s.add_style(_seq_flash("fb", 4, period=5.0, window=0.55, peak=0.3, rest=0.06))

    for i in range(4):
        s.circle(556, 234, 5, fill=T.AMBER, cls=f"fw{i}")
    s.add_style("\n".join(
        css_kf(f"fw{i}-mv", [("0%", "transform:translateX(0)"),
                             ("60%", "transform:translateX(92px)"),
                             ("61%,100%", "transform:translateX(92px)")])
        + f".fw{i}{{animation:fw{i}-mv 2.4s linear infinite {i * 0.6:.1f}s;}}"
        for i in range(4)))

    s.rect(560, 92, 300, 190, fill=T.PANEL, stroke=T.STROKE, rx=12)
    s.text(578, 118, "升级流程", size=12.5, fill=T.TEXT, weight="700")
    for i, t in enumerate([
        "① 收到升级指令 → 复位进 Bootloader",
        "② 擦除 APP B 区（按扇区/页）",
        "③ 分包接收，写入并累加校验",
        "④ 校验通过 → 参数区写跳转标志",
        "⑤ 软复位 → Bootloader 跳 APP B",
        "⑥ 新固件启动成功 → 标志回写有效",
    ]):
        s.text(578, 144 + i * 22, t, size=10.5, fill=T.MUTED)

    s.title_block(40, 348, "跳转前四件事（漏一件就 HardFault）", color=T.RED)
    s.rect(40, 360, 820, 118, fill=T.BG2, stroke=T.STROKE, rx=10)
    s.code(56, 382, [
        "__disable_irq();                         // 1. 关中断",
        "HAL_RCC_DeInit(); HAL_DeInit();          // 2. 外设和时钟回到默认",
        "__set_MSP(*(uint32_t *)APP_ADDR);        // 3. 栈顶改成 APP 的 MSP",
        "SCB->VTOR = APP_ADDR;                    // 4. 向量表改到 APP（APP 里再设一次）",
        "((void(*)(void))(*(uint32_t *)(APP_ADDR + 4)))();  // Reset_Handler",
    ], size=12, lh=18)

    s.rect(40, 492, 400, 82, fill=T.PANEL, stroke=T.STROKE, rx=10)
    s.text(58, 516, "Flash 擦写规则", size=12, fill=T.TEXT, weight="700")
    s.text(58, 538, "F1 中容量 1 KB/页，大容量 2 KB/页；F4 按扇区", size=10.5,
           fill=T.MUTED)
    s.text(58, 556, "先擦后写。F4 参数区必须独占一个扇区", size=10.5, fill=T.MUTED)

    s.rect(460, 492, 400, 82, fill=T.PANEL, stroke=T.STROKE, rx=10)
    s.text(478, 516, "别把砖刷出来", size=12, fill=T.TEXT, weight="700")
    s.text(478, 538, "校验通过前不要动 APP A，失败还能回滚", size=10.5,
           fill=T.MUTED)
    s.text(478, 556, "参数区先擦后写，并做双份冗余", size=10.5, fill=T.MUTED)
    s.footer("完整代码见 examples/iap-bootloader；串口升级常用 YMODEM 协议（带文件名与校验）")
    return s


# --------------------------------------------------------------------------- FreeRTOS


def freertos_scheduler() -> Svg:
    s = Svg(W, H, "FreeRTOS 任务调度：状态机 + 甘特图",
            "SysTick 每 1 ms 打断一次，调度器挑出「就绪队列里优先级最高」的任务")
    s.header(tag="15 FreeRTOS", tag_color=T.PINK)

    states = [("就绪 Ready", 80, 110, T.GREEN, "stReady", "等调度器挑选"),
              ("运行 Running", 400, 110, T.CYAN, "stRun", "正在占用 CPU"),
              ("阻塞 Blocked", 400, 226, T.AMBER, "stBlock", "等延时 / 队列 / 信号量"),
              ("挂起 Suspended", 80, 226, T.VIOLET, "stSusp", "vTaskSuspend 挂起")]
    for name, x, y, color, cls, sub in states:
        s.rect(x, y, 170, 62, fill=T.PANEL, stroke=color, rx=12)
        s.text(x + 85, y + 26, name, size=13, anchor="middle", fill=T.TEXT,
               weight="600")
        s.text(x + 85, y + 46, sub, size=9, anchor="middle", fill=T.MUTED)
        s.rect(x, y, 170, 62, fill=color, rx=12, opacity=0.15, cls=cls)
    s.add_style(anim_fade(".stReady", dur="4s", a=0.1, b=0.45))
    s.add_style(anim_fade(".stRun", dur="4s", a=0.45, b=0.1, delay="1s"))
    s.add_style(anim_fade(".stBlock", dur="4s", a=0.1, b=0.45, delay="2s"))
    s.add_style(anim_fade(".stSusp", dur="4s", a=0.1, b=0.45, delay="3s"))

    s.arrow(252, 128, 396, 128, color=T.GREEN, sw=2, dash="6 8", cls="e1")
    s.text(324, 120, "调度器选中", size=10, anchor="middle", fill=T.GREEN)
    s.arrow(568, 128, 700, 128, color=T.CYAN, sw=2, head=6)
    s.text(634, 118, "被抢占 / 时间片到", size=10, anchor="middle",
           fill=T.MUTED)
    s.line(700, 128, 700, 96, stroke=T.CYAN, sw=2)
    s.arrow(700, 96, 252, 96, color=T.CYAN, sw=2, head=6)
    s.line(252, 96, 252, 128, stroke=T.CYAN, sw=2)
    s.arrow(485, 176, 485, 222, color=T.AMBER, sw=2, head=6)
    s.text(492, 200, "vTaskDelay / 等队列", size=10, fill=T.AMBER)
    s.line(400, 257, 252, 257, stroke=T.AMBER, sw=2)
    s.arrow(252, 257, 165, 257, color=T.AMBER, sw=2, head=6)
    s.text(292, 276, "超时 / 事件到达", size=10, fill=T.AMBER)
    s.line(80, 226, 80, 176, stroke=T.VIOLET, sw=2)
    s.text(20, 205, "vTaskSuspend", size=10, fill=T.VIOLET)
    s.add_style(anim_flow(".e1", dur="1.4s", dash="6 8", shift=-14))

    s.text(40, 314, "CPU 时间轴（单核：同一时刻只有一根色条）", size=12,
           fill=T.MUTED)
    rows = [("Task1 高", T.CYAN, [(0, 8), (24, 6)]),
            ("Task2 中", T.GREEN, [(8, 8)]),
            ("Task3 低", T.AMBER, [(16, 8)]),
            ("Idle", T.DIM, [(30, 2)])]
    scale = 700 / 32
    for i, (name, color, spans) in enumerate(rows):
        y = 328 + i * 34
        s.text(40, y + 20, name, size=10.5, fill=color)
        s.rect(150, y, 700, 26, fill=T.BG2, stroke=T.GRID, rx=6)
        for x0, w in spans:
            s.rect(150 + x0 * scale, y + 2, w * scale - 1, 22, fill=color,
                   rx=4, opacity=0.85)
        for t in range(0, 33, 4):
            s.line(150 + t * scale, y, 150 + t * scale, y + 26,
                   stroke=T.GRID, sw=1)
    s.line(150, 320, 150, 468, stroke=T.RED, sw=1.6, cls="cursor")
    s.add_style(anim_tx(".cursor", dur="5s", x1=0, x2=700))
    s.text(150, 482, "0 ms", size=9, fill=T.DIM)
    s.text(850, 482, "32 ms", size=9, fill=T.DIM, anchor="end")

    s.rect(40, 496, 820, 64, fill=T.BG2, stroke=T.STROKE, rx=10)
    s.text(58, 516, "三条铁律", size=11.5, fill=T.TEXT, weight="700")
    s.text(58, 536, "① 数字越大优先级越高（和 NVIC 相反）；② 中断里只用 FromISR API",
           size=11, fill=T.MUTED)
    s.text(58, 552, "③ 栈不够会 HardFault，用 uxTaskGetStackHighWaterMark 看剩余",
           size=11, fill=T.MUTED)
    s.footer("常见坑：忘记在 vTaskStartScheduler 之前创建任务、在中断里调用阻塞 API 触发断言")
    return s




# --------------------------------------------------------------------------- 低功耗


def lowpower_wakeup() -> Svg:
    s = Svg(W, H, "三种低功耗模式与唤醒方式",
            "STM32 的低功耗只有三件事：关时钟、关电源域、留一个唤醒源")
    s.header(tag="16 低功耗", tag_color=T.CYAN)

    modes = [
        ("Sleep 睡眠", "WFI / WFE", "任意中断",
         "外设时钟还在，电流仍高（查 DS）",
         "内核停，外设继续跑。不要记成固定的 1 mA", T.GREEN),
        ("Stop 停止", "HAL_PWR_EnterSTOPMode", "EXTI / RTC / 唤醒脚",
         "主时钟停振后降到 µA 级（查 DS）",
         "SRAM 与 RTC 保持，唤醒后必须重配时钟", T.AMBER),
        ("Standby 待机", "HAL_PWR_EnterSTANDBYMode", "WKUP 脚 / RTC 闹钟",
         "F103 DS 典型值约 2 µA（非本仓库实测）",
         "只留备份域，唤醒等于复位，程序从头跑", T.RED),
    ]
    for i, (name, api, wake, cur, note, color) in enumerate(modes):
        y = 92 + i * 96
        s.rect(40, y, 820, 84, fill=T.PANEL, stroke=T.STROKE, rx=12)
        s.rect(40, y, 5, 84, fill=color, rx=3)
        s.text(60, y + 26, name, size=14, fill=T.TEXT, weight="700")
        s.text(60, y + 48, api, size=10.5, mono=True, fill=color)
        s.text(60, y + 68, note, size=10, fill=T.MUTED)
        s.text(470, y + 26, "唤醒源：" + wake, size=11, fill=T.CYAN)
        s.text(470, y + 48, "典型电流：" + cur, size=11, fill=T.AMBER)
        w = int(120 * (0.9 - i * 0.35))
        s.rect(470, y + 58, 120, 12, fill=T.BG2, stroke=T.STROKE, rx=3)
        s.rect(471, y + 59, w, 10, fill=color, rx=3, cls=f"pw{i}")
    s.add_style("\n".join(
        css_kf(f"pw{i}-f", [("0%,100%", "opacity:.35"), ("50%", "opacity:1")])
        + f".pw{i}{{animation:pw{i}-f 2.4s ease-in-out infinite {i * 0.4:.1f}s;}}"
        for i in range(3)))

    s.rect(40, 384, 400, 148, fill=T.BG2, stroke=T.STROKE, rx=10)
    s.text(58, 410, "省电的五个动作（按收益排序）", size=12.5, fill=T.TEXT,
           weight="700")
    for i, t in enumerate([
        "① 未使用的 GPIO 配成模拟输入或输出低",
        "② 关掉用不到的外设时钟（__HAL_RCC_*_CLK_DISABLE）",
        "③ 降低主频：功耗与频率基本成正比",
        "④ 用 DMA 搬数据，减少 CPU 唤醒次数",
        "⑤ 传感器分时供电（用 MOSFET 控制电源）",
    ]):
        s.text(58, 434 + i * 20, t, size=10.5, fill=T.MUTED)

    s.rect(460, 384, 400, 148, fill=T.PANEL, stroke=T.STROKE, rx=10)
    s.text(478, 410, "进入 Stop 模式的代码骨架", size=12.5, fill=T.TEXT,
           weight="700")
    s.code(478, 434, [
        "HAL_SuspendTick();          // 先停 SysTick",
        "HAL_PWR_EnterSTOPMode(PWR_LOWPOWERREGULATOR_ON,",
        "                       PWR_STOPENTRY_WFI);",
        "SystemClock_Config();       // 唤醒后必须重配时钟！",
        "HAL_ResumeTick();",
    ], size=10, lh=18, color=T.GREEN)

    s.rect(40, 534, 820, 22, fill=T.BG2, stroke=T.STROKE, rx=8)
    s.text(58, 550, "测功耗要用 µA 档万用表串在电源上；USB 调试器反向供电会污染测量结果",
           size=10.5, fill=T.AMBER)
    s.footer("F1 唤醒后 HSE 需要重新起振，务必重新调用 SystemClock_Config()，否则串口全乱码")
    return s



# --------------------------------------------------------------------------- L4 Stop2 唤醒证据


def l4_stop2_evidence() -> Svg:
    s = Svg(W, H, "L476 Stop 2：先在 IRQ 入口留证据，再让 HAL 清标志",
            "RTC/EXTI/PWR 原始位只在中断入口可靠；HAL handler 清位后从保留 SRAM 消费记录")
    s.header(tag="24 L4 Stop2", tag_color=T.CYAN)

    stages = [
        ("准备", "清旧标志 · 使能 RTC", T.GREEN),
        ("Stop 2", "WFI · SRAM 保持", T.VIOLET),
        ("IRQ 入口", "先读 3 组原始寄存器", T.AMBER),
        ("HAL handler", "清 EXTI → 清 WUTF", T.RED),
        ("回到 main", "恢复时钟 · 消费记录", T.CYAN),
    ]
    x0, y, bw, gap = 32, 102, 152, 24
    for i, (title, note, color) in enumerate(stages):
        x = x0 + i * (bw + gap)
        s.rect(x, y, bw, 92, fill=T.PANEL, stroke=color, rx=12, cls=f"ev{i}")
        s.rect(x, y, bw, 5, fill=color, rx=3)
        s.text(x + bw / 2, y + 34, title, size=14, anchor="middle",
               fill=T.TEXT, weight="700")
        s.text(x + bw / 2, y + 61, note, size=9.5, anchor="middle", fill=T.MUTED)
        if i < len(stages) - 1:
            s.arrow(x + bw + 4, y + 46, x + bw + gap - 4, y + 46,
                    color=T.CYAN, sw=2.2, head=6, cls="ev-flow")
    s.add_style(_seq_flash("ev", 5, period=6.0, window=0.78, peak=1.0, rest=0.42))
    s.add_style(anim_flow(".ev-flow", dur="1.2s", dash="5 8", shift=-13))

    s.rect(40, 226, 820, 116, fill=T.BG2, stroke=T.STROKE, rx=12)
    s.text(58, 252, "IRQ 入口写入 Stop 2 保持的 SRAM", size=13, fill=T.TEXT,
           weight="700")
    fields = [
        ("rtc_isr", "RTC->ISR", "WUTF 仍为 1", T.AMBER),
        ("exti_pr1", "EXTI->PR1", "line 20 pending", T.CYAN),
        ("pwr_sr1", "PWR->SR1", "WKUP 原始状态", T.VIOLET),
        ("sequence", "+1", "最后发布记录", T.GREEN),
    ]
    for i, (name, reg, note, color) in enumerate(fields):
        x = 58 + i * 198
        s.rect(x, 270, 182, 54, fill=T.PANEL, stroke=color, rx=8)
        s.text(x + 10, 291, name, size=10.5, mono=True, fill=color, weight="700")
        s.text(x + 172, 291, reg, size=9.5, mono=True, anchor="end", fill=T.TEXT)
        s.text(x + 10, 311, note, size=9.5, fill=T.MUTED)

    s.rect(40, 364, 388, 150, fill=T.PANEL, stroke=T.AMBER, rx=12)
    s.text(58, 390, "为什么不能在 Stop 返回后再读？", size=12.5,
           fill=T.TEXT, weight="700")
    rows = [
        ("IRQ entry", "EXTI=1 · WUTF=1", T.GREEN),
        ("HAL clear", "EXTI=0 · WUTF=0", T.RED),
        ("callback", "原始位已经消失", T.RED),
        ("main resume", "只能读 WakeEvidence", T.CYAN),
    ]
    for i, (k, v, color) in enumerate(rows):
        yy = 417 + i * 23
        s.text(58, yy, k, size=10.5, mono=True, fill=color)
        s.text(180, yy, v, size=10.5, fill=T.MUTED)

    s.rect(452, 364, 408, 150, fill=T.BG2, stroke=T.CYAN, rx=12)
    s.text(470, 390, "消费记录的顺序", size=12.5, fill=T.TEXT, weight="700")
    steps = [
        "① IRQ 入口：写 rtc_isr / exti_pr1 / pwr_sr1",
        "② __DMB() 后 sequence++，再调用 HAL handler",
        "③ Stop 返回：稳定复制 retained record",
        "④ 恢复 PLL/SYSCLK 后再打印和清软件记录",
    ]
    for i, text in enumerate(steps):
        s.text(470, 418 + i * 24, text, size=10.5, fill=T.MUTED)

    s.footer("不变量：先记录，后清硬件标志；先恢复时钟，后输出证据")
    return s



# --------------------------------------------------------------------------- RTOS 系统分层


def rtos_system_layers() -> Svg:
    s = Svg(W, H, "嵌入式系统不只是一颗 RTOS 内核",
            "从硬件、驱动和内核，到服务与应用；每层都要有所有权、超时和故障边界")
    s.header(tag="28 系统", tag_color=T.VIOLET)

    layers = [
        ("应用", "控制回路 · 数据采集 · 人机界面 · 升级策略", T.CYAN),
        ("系统服务", "网络 · 文件系统 · 日志 · Shell · 时间 · OTA", T.GREEN),
        ("OS API", "原生 API / CMSIS-RTOS2；只统一接口，不抹平语义", T.AMBER),
        ("内核", "调度 · IPC · 定时器 · 内存 · 低功耗 · 故障钩子", T.VIOLET),
        ("BSP / 设备", "HAL/LL · RT-Thread device · Zephyr device model", T.PINK),
        ("硬件", "Cortex-M · NVIC · DMA · Cache · 外设 · PHY", T.RED),
    ]
    x, y, bw, bh, gap = 42, 92, 548, 62, 12
    for i, (name, detail, color) in enumerate(layers):
        yy = y + i * (bh + gap)
        s.rect(x, yy, bw, bh, fill=T.PANEL, stroke=color, rx=11, cls=f"sl{i}")
        s.rect(x, yy, 7, bh, fill=color, rx=4)
        s.text(x + 24, yy + 27, name, size=14, fill=color, weight="700")
        s.text(x + 132, yy + 27, detail, size=10.5, fill=T.MUTED)
        s.text(x + 24, yy + 49, "入口有前置条件 · 出口有结果码 · 等待有截止点", size=9.5,
               fill=T.DIM)
        if i < len(layers) - 1:
            s.arrow(x + bw / 2, yy + bh + 3, x + bw / 2,
                    yy + bh + gap - 3, color=T.CYAN, sw=2, head=6, cls="sl-flow")
    s.add_style(_seq_flash("sl", len(layers), period=7.2, window=0.72,
                           peak=1.0, rest=0.48))
    s.add_style(anim_flow(".sl-flow", dur="1.1s", dash="4 7", shift=-11))

    s.text(626, 102, "怎么选系统", size=14, fill=T.TEXT, weight="700")
    cards = [
        ("裸机", "状态机明确\n资源极紧", T.DIM),
        ("FreeRTOS", "小内核\n自己组合服务", T.CYAN),
        ("RT-Thread", "设备框架 + 组件\n中文生态", T.GREEN),
        ("Zephyr", "Kconfig + Devicetree\n跨厂商子系统", T.AMBER),
    ]
    for i, (name, detail, color) in enumerate(cards):
        yy = 122 + i * 94
        s.rect(618, yy, 242, 76, fill=T.BG2, stroke=color, rx=10)
        s.text(634, yy + 25, name, size=13, fill=color, weight="700")
        for j, line in enumerate(detail.split("\n")):
            s.text(730, yy + 25 + j * 21, line, size=10.5, fill=T.MUTED)

    s.rect(618, 506, 242, 48, fill=T.PANEL, stroke=T.RED, rx=10)
    s.text(739, 526, "先列约束，再选生态", size=12, anchor="middle",
           fill=T.RED, weight="700")
    s.text(739, 545, "不要用 API 熟悉度代替需求", size=9.5,
           anchor="middle", fill=T.MUTED)
    s.footer("不变量：ISR 只发布事件；资源只有一个所有者；每个阻塞都有截止点；证据能定位到第一处分歧")
    return s



# --------------------------------------------------------------------------- G0 启动与 SWD 共脚


def g0_boot_swd() -> Svg:
    s = Svg(W, H, "G071：BOOT0 与 SWCLK 共脚，启动选择仍可判定",
            "先分清锁存时刻与选择来源，再用 Under Reset 恢复调试；不要靠反复断电猜")
    s.header(tag="23 G0 Boot / SWD", tag_color=T.CYAN)

    stages = [
        ("① 复位释放", "选项字节已加载", T.GREEN),
        ("② 第 4 个 SYSCLK 沿", "锁存启动配置", T.AMBER),
        ("③ nBOOT_SEL", "0=PA14 · 1=nBOOT0", T.VIOLET),
        ("④ 启动目标", "Main / System / SRAM", T.CYAN),
    ]
    x0, y, bw, gap = 35, 104, 190, 20
    for i, (title, note, color) in enumerate(stages):
        x = x0 + i * (bw + gap)
        s.rect(x, y, bw, 88, fill=T.PANEL, stroke=color, rx=12, cls=f"g0s{i}")
        s.rect(x, y, bw, 5, fill=color, rx=3)
        s.text(x + bw / 2, y + 36, title, size=13, anchor="middle",
               fill=T.TEXT, weight="700")
        s.text(x + bw / 2, y + 63, note, size=10, anchor="middle", fill=T.MUTED)
        if i < len(stages) - 1:
            s.arrow(x + bw + 3, y + 44, x + bw + gap - 3, y + 44,
                    color=T.CYAN, sw=2.2, head=6, cls="g0-flow")
    s.add_style(_seq_flash("g0s", 4, period=5.2, window=0.9, peak=1.0, rest=0.5))
    s.add_style(anim_flow(".g0-flow", dur="1.2s", dash="5 8", shift=-13))

    s.rect(40, 222, 400, 158, fill=T.PANEL, stroke=T.AMBER, rx=12)
    s.text(60, 250, "PA14-BOOT0 = SWCLK", size=16, mono=True,
           fill=T.AMBER, weight="700")
    notes = [
        ("采样窗口", "外部上拉/调试器不得干扰锁存", T.RED),
        ("启动以后", "SWCLK 翻转不会反改启动目标", T.GREEN),
        ("复位默认", "PA14 内部下拉 · PA13 内部上拉", T.CYAN),
    ]
    for i, (label, note, color) in enumerate(notes):
        yy = 278 + i * 31
        s.text(60, yy, label, size=10.5, fill=color, weight="700")
        s.text(142, yy, note, size=10.5, fill=T.MUTED)

    s.rect(460, 222, 400, 158, fill=T.BG2, stroke=T.VIOLET, rx=12)
    s.text(480, 250, "两种启动来源，不要混读", size=14,
           fill=T.TEXT, weight="700")
    s.text(480, 281, "nBOOT_SEL=0", size=11, mono=True, fill=T.VIOLET,
           weight="700")
    s.text(610, 281, "PA14 参与选择", size=11, fill=T.MUTED)
    s.text(480, 313, "nBOOT_SEL=1", size=11, mono=True, fill=T.VIOLET,
           weight="700")
    s.text(610, 313, "改看 nBOOT0 / nBOOT1", size=11, fill=T.MUTED)
    s.text(480, 350, "BOOT_LOCK=1：强制 Main Flash", size=11.5,
           fill=T.RED, weight="700")

    s.rect(40, 404, 820, 128, fill=T.PANEL, stroke=T.CYAN, rx=12)
    recovery = [
        ("1  Under Reset", "NRST 阻止应用运行"),
        ("2  读取证据", "BOOT_LOCK / nBOOT* / RDP"),
        ("3  写已知配置", "只改启动相关位"),
        ("4  复位并读回", "确认 Main Flash 与 SWD"),
    ]
    for i, (title, note) in enumerate(recovery):
        x = 60 + i * 200
        s.text(x, 442, title, size=12, fill=T.CYAN, weight="700")
        s.text(x, 470, note, size=10, fill=T.MUTED)
        if i < 3:
            s.arrow(x + 164, 456, x + 184, 456, color=T.CYAN,
                    sw=1.8, head=5, cls="g0-flow")
    s.text(60, 510, "恢复目标：让启动源可解释、可复现，而不是碰巧进入一次 Bootloader",
           size=11, fill=T.TEXT, weight="700")

    s.footer("不要为恢复盲目降低 RDP：Level 2 不可逆；Level 1 → 0 会触发整片擦除")
    return s

ALL = [timer_pwm, timer_modes, adc_sar, dma_circular, iwdg_window, flash_iap,
       freertos_scheduler, lowpower_wakeup, l4_stop2_evidence, rtos_system_layers,
       g0_boot_swd]

NAMES = {
    "timer_pwm": "timer-pwm",
    "timer_modes": "timer-modes",
    "adc_sar": "adc-sar",
    "dma_circular": "dma-circular",
    "iwdg_window": "iwdg-window",
    "flash_iap": "flash-iap",
    "freertos_scheduler": "freertos-scheduler",
    "lowpower_wakeup": "lowpower-wakeup",
    "l4_stop2_evidence": "l4-stop2-evidence",
    "rtos_system_layers": "rtos-system-layers",
    "g0_boot_swd": "g0-boot-swd",
}

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""motor 专题机制动画（VIS03/04），由 gen_animations.py 统一调度。

冻结事实来源：第 29–32 章冻结参数（PWM 72M/ARR 3599/20kHz、±50‰/10ms 斜坡、
TIM2 编码器模式 3、CPR=440、回绕判据 |Δ|<32768）。
每个动画必须有离线静态帧：颜色之外也能辨识状态。
"""

from __future__ import annotations

from svgkit import Svg, T, anim_fade, anim_flow, css_kf

W, H = 900, 620


def _step_flash(prefix: str, n: int, period: float, window: float = 0.34,
                peak: float = 0.30, rest: float = 0.05) -> str:
    """第 i 步在周期第 i/n 处短暂高亮。"""
    rules = []
    for i in range(n):
        a = i / n * 100
        b = (i + window) / n * 100
        rules.append(
            f"@keyframes {prefix}{i}{{0%,{a:.2f}%,{b:.2f}%,100%{{opacity:{rest}}}"
            f"{a + 0.01:.2f}%,{b - 0.01:.2f}%{{opacity:{peak}}}}}"
            f".{prefix}{i}{{animation:{prefix}{i} {period}s infinite}}"
        )
    return "\n".join(rules)


def motor_pwm_drive() -> Svg:
    s = Svg(W, H, "PWM 怎么变成转速——但不是线性变",
            "72 MHz / PSC=0 / ARR=3599 → 20 kHz；占空比决定平均电压，转速还受负载、VM 与电流限约束")
    s.header(tag="30 开环调速 · VIS03", tag_color=T.GREEN)

    stages = [
        ("duty 25%", "CCR = 900", [1, 0, 0, 0] * 2, T.CYAN),
        ("duty 50%", "CCR = 1800", [1, 1, 0, 0] * 2, T.GREEN),
        ("duty 100%", "CCR = 3600 > ARR", [1] * 8, T.AMBER),
    ]
    y0 = 110
    for i, (name, ccr, bits, color) in enumerate(stages):
        y = y0 + i * 110
        s.rect(40, y, 560, 96, fill=T.PANEL, stroke=color, rx=8, cls=f"d{i}",
               opacity=0.06)
        s.text(56, y + 26, name, size=13, fill=color, weight="800")
        s.text(200, y + 26, ccr, size=12, mono=True, fill=T.TEXT, weight="700")
        s.waveform(56, y + 40, 520, 40, bits, color=color, sw=2)
        s.text(604, y + 66, "50 µs" if i < 2 else "恒有效",
               size=10, fill=T.MUTED)
    s.add_style(_step_flash("d", 3, period=6.0))

    s.rect(640, 110, 220, 306, fill=T.PANEL, stroke=T.GREEN, rx=8)
    s.text(750, 140, "电机得到什么", size=12, anchor="middle", fill=T.GREEN,
           weight="800")
    s.text(750, 172, "平均电压 ↑", size=11, anchor="middle", fill=T.TEXT)
    s.text(750, 196, "电流受三档约束", size=10, anchor="middle", fill=T.RED)
    s.text(750, 220, "（连续 ≤1.0 A）", size=10, anchor="middle", fill=T.MUTED)
    s.rect(672, 244, 156, 20, fill=T.BG2, stroke=T.STROKE, rx=4)
    s.rect(672, 244, 62, 20, fill=T.GREEN, rx=4, cls="rpm")
    s.add_style(css_kf("rpm", [("0%,100%", "width:62px"),
                               ("45%", "width:118px"),
                               ("70%", "width:96px")]))
    s.text(750, 290, "rpm 响应滞后且不线性", size=10, anchor="middle", fill=T.AMBER)
    s.line(672, 310, 828, 310, stroke=T.STROKE, sw=1)
    s.text(750, 334, "斜坡 ±50‰/10 ms", size=10.5, anchor="middle", fill=T.CYAN,
           weight="700")
    s.text(750, 358, "换向从零升速", size=10, anchor="middle", fill=T.MUTED)

    s.rect(40, 460, 820, 100, fill=T.BG2, stroke=T.RED, rx=8)
    s.text(450, 490, " duty → RPM 不是无条件线性：VM 下降、负载变重、电流限顶死都会让同一条占空比曲线漂移。",
           size=11.5, anchor="middle", fill=T.TEXT, weight="700")
    s.text(450, 518, "开环只能保证「给定的占空比被忠实输出」；转速是否如愿，是第 32 章闭环才回答的问题。",
           size=10.5, anchor="middle", fill=T.MUTED)
    s.text(450, 544, "100% 端点：CCR=ARR 只有 3599/3600 ≈ 99.97% —— 恒有效必须 CCR > ARR（写 3600）。",
           size=10.5, anchor="middle", fill=T.RED)
    s.footer("视觉规范：FA-002 概念连续线 · IG-011 阶梯对比 · C-03 / C-10 / C-27 / C-31",
             label="自绘矢量动画 · STM32 知识库")
    return s


def motor_encoder_count() -> Svg:
    s = Svg(W, H, "正交编码器：四倍频怎么数、回绕怎么判",
            "TIM2 编码器模式 3：TI1/TI2 上下沿都计数；A 领先 B 加计数；有符号增量 |Δ|<32768")
    s.header(tag="31 编码器 · VIS04", tag_color=T.CYAN)

    yA, yB = 140, 230
    s.text(56, yA - 14, "A 相（PA0 / TIM2_CH1）", size=11.5, fill=T.CYAN,
           weight="700")
    s.waveform(56, yA, 520, 56, [1, 1, 0, 0] * 2, color=T.CYAN, sw=2)
    s.text(56, yB - 14, "B 相（PA1 / TIM2_CH2）", size=11.5, fill=T.AMBER,
           weight="700")
    s.waveform(56, yB, 520, 56, [0, 1, 1, 0] * 2, color=T.AMBER, sw=2)

    ticks_x = [56 + 520 * (i + 0.5) / 8 for i in range(8)]
    for i, tx in enumerate(ticks_x):
        s.line(tx, yA - 4, tx, yB + 60, stroke=T.GREEN, sw=1.5, dash="3 4",
               cls=f"t{i}")
        s.circle(tx, yB + 70, 5, fill=T.GREEN, cls=f"tk{i}")
        s.text(tx, yB + 96, "+1", size=10, anchor="middle", fill=T.GREEN,
               weight="700", cls=f"tt{i}")
    s.add_style(_step_flash("tk", 8, period=6.4, window=0.09, peak=1.0,
                            rest=0.25))
    s.add_style(_step_flash("tt", 8, period=6.4, window=0.09, peak=1.0,
                            rest=0.35))
    s.text(320, yB + 130, "一个 A/B 周期 = 4 个计数沿（四倍频）", size=12,
           anchor="middle", fill=T.GREEN, weight="800")

    s.rect(620, 110, 240, 240, fill=T.PANEL, stroke=T.VIOLET, rx=8)
    s.text(740, 140, "计数与方向", size=12, anchor="middle", fill=T.VIOLET,
           weight="800")
    s.text(740, 172, "CPR = 440", size=13, anchor="middle", mono=True,
           fill=T.TEXT, weight="800")
    s.text(740, 194, "110 PPR × 4 倍频", size=10, anchor="middle", fill=T.MUTED)
    s.text(740, 226, "A 领先 B → 加计数", size=10.5, anchor="middle", fill=T.CYAN)
    s.text(740, 250, "B 领先 A → 减计数", size=10.5, anchor="middle", fill=T.AMBER)
    s.text(740, 282, "rpm = 60×Δ / (CPR×Δt)", size=11, anchor="middle", mono=True,
           fill=T.TEXT)
    s.text(740, 306, "Δt = 10 ms · 量化下限 ≈13.6 rpm", size=9.5,
           anchor="middle", fill=T.MUTED)

    s.rect(40, 420, 820, 120, fill=T.BG2, stroke=T.RED, rx=8)
    s.text(450, 450, "回绕：16 位计数 65535 → 0 不断翻转。65530 与 100 的有符号增量 = +6，不是 −65430。",
           size=11.5, anchor="middle", fill=T.TEXT, weight="700")
    s.text(450, 478, "判据 |Δ| < 32768/2 = 16384：一次 10 ms 内 Δ 超过它就说明判据被违反，而不是电机超速。",
           size=10.5, anchor="middle", fill=T.MUTED)
    s.text(450, 504, "零计数不能单独证明断线：换向过零同样清零——结合无反馈 500 ms 计时（第 32 章 FAULT）一起判。",
           size=10.5, anchor="middle", fill=T.RED)
    s.add_style(anim_flow(".tick", dur="1.6s", dash="4 6", shift=-10)) if False else None
    s.footer("视觉规范：FA-002 概念连续线 · IG-011 相位对比 · C-03 / C-10 / C-27 / C-31",
             label="自绘矢量动画 · STM32 知识库")
    return s


ALL = [motor_pwm_drive, motor_encoder_count]

NAMES = {
    "motor_pwm_drive": "motor-pwm-drive",
    "motor_encoder_count": "motor-encoder-count",
}

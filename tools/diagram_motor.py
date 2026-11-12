#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""motor 专题静态机制图（VIS01/02/05/06），由 gen_diagrams.py 统一调度。

冻结事实来源：TB6612 p.4 真值表、RM0008 Rev 21、第 29–32 章冻结参数。
全部按 svgkit 语法生成，不得手改生成物。
"""

from __future__ import annotations

from svgkit import Svg, T

W, H = 900, 560


def motor_power_path() -> Svg:
    s = Svg(W, H, "驱动控制与电流路径",
            "小信号在 MCU 侧、大电流在 VM 侧，两路供电共地（示意，与第 29 章接线表一致）")
    s.header(tag="29 电机驱动 · VIS01", tag_color=T.BLUE)
    s.rect(30, 96, 250, 300, fill=T.PANEL, stroke=T.CYAN, rx=8)
    s.text(155, 126, "STM32F103C8T6", size=12, anchor="middle", fill=T.CYAN, weight="800")
    s.text(155, 150, "（逻辑侧 3.3 V）", size=10, anchor="middle", fill=T.MUTED)
    pins = [
        ("PA6", "TIM3_CH1 → PWM 20 kHz"),
        ("PB0", "AIN1 方向 1"),
        ("PB1", "AIN2 方向 2"),
        ("PB10", "STBY 待机使能"),
        ("PB12", "电流测量点"),
        ("PA9/PA10", "USART1 命令/遥测"),
    ]
    for i, (pin, desc) in enumerate(pins):
        yy = 182 + i * 34
        s.text(44, yy, pin, size=10.5, mono=True, fill=T.TEXT, weight="700")
        s.text(108, yy, desc, size=9.5, fill=T.MUTED)

    s.rect(360, 96, 220, 300, fill=T.PANEL, stroke=T.AMBER, rx=8)
    s.text(470, 126, "TB6612FNG", size=12, anchor="middle", fill=T.AMBER, weight="800")
    s.text(470, 150, "H 桥 · VM 侧大电流", size=10, anchor="middle", fill=T.MUTED)
    s.text(470, 190, "PWM / AIN1 / AIN2 / STBY", size=9.5, anchor="middle", fill=T.TEXT)
    s.text(470, 212, "四根逻辑线决定五态", size=9.5, anchor="middle", fill=T.MUTED)
    s.rect(392, 236, 156, 64, fill=T.BG2, stroke=T.STROKE, rx=4)
    s.text(470, 262, "H 桥开关组", size=11, anchor="middle", fill=T.TEXT, weight="700")
    s.text(470, 284, "OUT1 / OUT2", size=10, anchor="middle", mono=True, fill=T.CYAN)
    s.text(470, 330, "连续 ≤1.0 A/通道", size=10, anchor="middle", fill=T.RED)
    s.text(470, 350, "1.2 A 绝对最大 ≠ 连续", size=9.5, anchor="middle", fill=T.MUTED)
    s.text(470, 370, "3.2 A 仅脉冲档", size=9.5, anchor="middle", fill=T.MUTED)

    s.rect(660, 96, 210, 300, fill=T.PANEL, stroke=T.GREEN, rx=8)
    s.text(765, 126, "直流电机 + 电源", size=12, anchor="middle", fill=T.GREEN, weight="800")
    s.text(765, 190, "VM 6–12 V", size=13, anchor="middle", fill=T.GREEN, weight="800")
    s.text(765, 214, "电机电源（大电流）", size=9.5, anchor="middle", fill=T.MUTED)
    s.text(765, 256, "Vcc 2.7–5.5 V", size=11, anchor="middle", fill=T.CYAN, weight="700")
    s.text(765, 278, "逻辑电源（冻结 3.3 V）", size=9.5, anchor="middle", fill=T.MUTED)
    s.text(765, 320, "两路分开供电", size=10, anchor="middle", fill=T.TEXT, weight="700")
    s.text(765, 342, "GND 必须共地", size=10, anchor="middle", fill=T.RED, weight="700")

    for y in (182, 216, 250, 284):
        s.arrow(280, y, 360, y, color=T.CYAN, sw=1.5, head=5)
    s.arrow(580, 240, 660, 240, color=T.AMBER, sw=2, head=6)
    s.text(620, 228, "大电流", size=9, anchor="middle", fill=T.AMBER)
    s.rect(30, 424, 840, 76, fill=T.BG2, stroke=T.STROKE, rx=8)
    s.text(450, 452, "读图顺序：先认逻辑侧四根线 → 再看 H 桥五态 → 最后才是 VM 电流档。",
           size=11, anchor="middle", fill=T.TEXT, weight="700")
    s.text(450, 478, "电流连续预算只按 1.0 A/通道；堵转 ≤0.8 A 目标（BLK-P0-4 实测项，未实测前不得引用更大值）。",
           size=10, anchor="middle", fill=T.RED)
    s.footer("视觉规范：FA-002 概念连续线 · IG-011 前后/强弱对比 · C-03 / C-10 / C-27 / C-31",
             label="自绘矢量图 · STM32 知识库")
    return s


def motor_stop_modes() -> Svg:
    s = Svg(W, H, "滑行、制动、待机不是一回事",
            "三种「停」在输出端的行为可查来源（TB6612 p.4 真值表）")
    s.header(tag="29/30 停止语义 · VIS02", tag_color=T.AMBER)
    cols = [
        ("滑行 coast", T.GREEN, "H L L H", "输出高阻",
         ["绕组与电源断开", "自由减速，不耗能", "无回馈尖峰"]),
        ("短接制动 short brake", T.AMBER, "L X X H", "绕组两端短接",
         ["动能变电流耗掉", "减速快", "有回流尖峰"]),
        ("待机 standby", T.RED, "X X X L", "STBY=L 整体关断",
         ["默认安全态（上电即此）", "高阻 + 节电", "退出前查使能条件"]),
    ]
    cw, gap = 272, 16
    x0 = (W - (cw * 3 + gap * 2)) / 2
    for i, (name, color, pins, out, lines) in enumerate(cols):
        x = x0 + i * (cw + gap)
        s.rect(x, 100, cw, 290, fill=T.PANEL, stroke=color, rx=8)
        s.text(x + cw / 2, 130, name, size=12.5, anchor="middle", fill=color, weight="800")
        s.text(x + cw / 2, 158, "PWM AIN1 AIN2 STBY", size=9, anchor="middle", fill=T.MUTED)
        s.text(x + cw / 2, 188, pins, size=15, anchor="middle", mono=True,
               fill=T.TEXT, weight="800")
        s.rect(x + 20, 212, cw - 40, 40, fill=T.BG2, stroke=color, rx=4)
        s.text(x + cw / 2, 238, out, size=11, anchor="middle", fill=T.TEXT, weight="700")
        for j, line in enumerate(lines):
            s.text(x + 24, 288 + j * 30, "· " + line, size=10.5,
                   fill=T.MUTED if j else T.TEXT)
    s.rect(40, 424, 820, 76, fill=T.BG2, stroke=T.RED, rx=8)
    s.text(450, 452, "PWM=0 映射成「滑行」还是「短接制动」是配置项；待机永远归 STBY 管，与 PWM 无关。",
           size=11, anchor="middle", fill=T.TEXT, weight="700")
    s.text(450, 478, "换向必须走 REVERSING：斜坡归零 → 停稳（|rpm|≤5）→ 保持 100 ms → 才允许反向输出。",
           size=10, anchor="middle", fill=T.RED)
    s.footer("视觉规范：FA-002 概念连续线 · IG-011 三态对比 · C-03 / C-10 / C-27 / C-31",
             label="自绘矢量图 · STM32 知识库")
    return s


def motor_speed_loop() -> Svg:
    s = Svg(W, H, "速度闭环：限幅位置就是合同位置",
            "单位、限幅与积分条件全图一致（第 32 章冻结参数）")
    s.header(tag="32 速度闭环 · VIS05", tag_color=T.VIOLET)
    y = 130
    boxes = [
        (30, "目标 rpm", "20–300 / 冻结 300 上限", T.CYAN),
        (190, "斜坡 ramp", "±600 rpm/s · 10 ms 节拍", T.CYAN),
        (350, "求和点", "e = 目标 − 实测（带符号）", T.VIOLET),
        (510, "PI", "Kp=2.0 Ki=0.5 / i_limit=500‰", T.VIOLET),
        (670, "输出限幅", "duty_limit = 900‰", T.AMBER),
    ]
    for x, name, note, color in boxes:
        s.rect(x, y, 130, 82, fill=T.PANEL, stroke=color, rx=8)
        s.text(x + 65, y + 30, name, size=12, anchor="middle", fill=color, weight="800")
        s.text(x + 65, y + 58, note, size=8.8, anchor="middle", fill=T.MUTED)
    for i in range(4):
        s.arrow(160 + i * 160, y + 41, 190 + i * 160, y + 41,
                color=T.STROKE, sw=1.5, head=5)
    s.rect(300, 262, 300, 80, fill=T.PANEL, stroke=T.GREEN, rx=8)
    s.text(450, 292, "motor_bridge + 电机（20 kHz PWM）", size=11.5, anchor="middle",
           fill=T.GREEN, weight="800")
    s.text(450, 318, "五态真值表 · 换向走 REVERSING", size=9.5, anchor="middle", fill=T.MUTED)
    s.rect(30, 262, 220, 80, fill=T.PANEL, stroke=T.BLUE, rx=8)
    s.text(140, 292, "抗饱和（back-calc）", size=11, anchor="middle", fill=T.BLUE, weight="800")
    s.text(140, 318, "限幅时回算积分，防「憋着」", size=9.5, anchor="middle", fill=T.MUTED)
    s.rect(650, 262, 220, 80, fill=T.PANEL, stroke=T.CYAN, rx=8)
    s.text(760, 292, "编码器 → rpm", size=11, anchor="middle", fill=T.CYAN, weight="800")
    s.text(760, 316, "TIM2 模式3 · CPR=440", size=9.5, anchor="middle", fill=T.MUTED)
    s.text(760, 334, "量化下限 ≈13.6 rpm", size=9.5, anchor="middle", fill=T.MUTED)
    s.arrow(735, y + 82, 560, 262, color=T.GREEN, sw=2, head=6)
    s.arrow(650, 302, 250, 302, color=T.CYAN, sw=2, head=6)
    s.arrow(250, 302, 415, y + 82, color=T.CYAN, sw=1.5, head=5)
    s.text(440, 250, "实测 rpm 回授（10 ms 与串口分离）", size=9, anchor="middle", fill=T.CYAN)
    s.rect(40, 400, 820, 68, fill=T.BG2, stroke=T.STROKE, rx=8)
    s.text(450, 426, "先证明「看得到转速」（无反馈 500 ms 锁存 FAULT），再谈调得好不好。",
           size=11, anchor="middle", fill=T.TEXT, weight="700")
    s.text(450, 450, "限幅顺序：i_limit → duty_limit → 抗饱和回算；任何一步越界都要能说出单位。",
           size=10, anchor="middle", fill=T.MUTED)
    s.rect(40, 486, 820, 40, fill=T.PANEL2, stroke=T.VIOLET, rx=8)
    s.text(450, 511, "调参阶梯六步，每步带通过判据与回退条件；换装置从第 1 步重做。",
           size=10.5, anchor="middle", fill=T.VIOLET, weight="700")
    s.footer("视觉规范：FA-002 概念连续线 · IG-008 多路径流程 · C-03 / C-10 / C-27 / C-31",
             label="自绘矢量图 · STM32 知识库")
    return s


def motor_state_machine() -> Svg:
    s = Svg(W, H, "运行 / 反转 / 故障状态机",
            "事件与固件一致：故障 > STOP > 换向（第 32 章 control_tick.c）")
    s.header(tag="32 状态机 · VIS06", tag_color=T.RED)
    states = [
        (60, 110, "DISABLED", "上电默认 · 输出撤销", T.MUTED),
        (300, 110, "ARMED", "收到有效命令 · 使能通过", T.CYAN),
        (540, 60, "RUN", "带符号占空比 · 斜坡 ±50‰/10ms", T.GREEN),
        (540, 210, "REVERSING", "斜坡归零→停稳→保持100ms→反向", T.AMBER),
        (300, 330, "FAULT", "故障锁存 · 人工清零", T.RED),
    ]
    for x, y, name, note, color in states:
        s.rect(x, y, 180, 62, fill=T.PANEL, stroke=color, rx=8)
        s.text(x + 90, y + 26, name, size=12.5, anchor="middle", fill=color, weight="800")
        s.text(x + 90, y + 48, note, size=8.5, anchor="middle", fill=T.MUTED)
    s.arrow(240, 141, 300, 141, color=T.CYAN, sw=1.5, head=5)
    s.text(270, 130, "arm", size=9, anchor="middle", fill=T.CYAN)
    s.arrow(480, 128, 540, 100, color=T.GREEN, sw=1.5, head=5)
    s.text(510, 106, "run", size=9, anchor="middle", fill=T.GREEN)
    s.arrow(630, 122, 630, 210, color=T.AMBER, sw=1.5, head=5)
    s.text(650, 170, "换向", size=9, anchor="middle", fill=T.AMBER)
    s.arrow(540, 241, 480, 150, color=T.GREEN, sw=1.5, head=5)
    s.text(490, 208, "停稳完成", size=9, anchor="middle", fill=T.GREEN)
    s.arrow(150, 172, 330, 330, color=T.RED, sw=2, head=6)
    s.text(200, 268, "任意状态故障", size=9.5, anchor="middle", fill=T.RED)
    s.arrow(470, 361, 150, 172, color=T.MUTED, sw=1.5, head=5)
    s.text(310, 300, "人工清零（先撤销输出）", size=9.5, anchor="middle", fill=T.MUTED)
    s.rect(700, 90, 180, 240, fill=T.BG2, stroke=T.RED, rx=8)
    s.text(790, 118, "故障来源", size=12, anchor="middle", fill=T.RED, weight="800")
    faults = ["命令流断流 500 ms（F01）", "无反馈 500 ms", "全程 3 s 超时",
              "电流档越界", "参数拒绝（≥1000‰）"]
    for i, f in enumerate(faults):
        s.text(714, 152 + i * 40, "· " + f, size=9.5, fill=T.TEXT)
    s.rect(40, 420, 820, 76, fill=T.BG2, stroke=T.STROKE, rx=8)
    s.text(450, 448, "STOP 只是撤销输出；FAULT 锁存并拒绝自动恢复——先查因，再清零。",
           size=11, anchor="middle", fill=T.TEXT, weight="700")
    s.text(450, 474, "无反馈 500 ms 证明「看不到转速」立即锁存；500 ms 租约 F01 让串口拔掉不留转动的电机。",
           size=10, anchor="middle", fill=T.MUTED)
    s.footer("视觉规范：FA-002 概念连续线 · IG-008 多路径流程 · C-03 / C-10 / C-27 / C-31",
             label="自绘矢量图 · STM32 知识库")
    return s


ALL = [motor_power_path, motor_stop_modes, motor_speed_loop, motor_state_machine]

NAMES = {
    "motor_power_path": "motor-power-path",
    "motor_stop_modes": "motor-stop-modes",
    "motor_speed_loop": "motor-speed-loop",
    "motor_state_machine": "motor-state-machine",
}

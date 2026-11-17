# -*- coding: utf-8 -*-
"""ch29 knowledge-track figures (handraw grammar, frozen motor facts)."""
from hd import *


# ------------------------------------------------------------ fig 1
def five_states():
    f = Fig("ch29-five-states", "驱动桥五种状态 / five bridge states",
            title_color=BLUE_D)
    cols = [
        ("待机", "standby", MUTED, "X X X L", "默认态：桥必然关闭", True),
        ("滑行", "coast", GREEN_D, "H L L H", "高阻，不耗能", False),
        ("短接制动", "short brake", AMBER_STROKE, "L X X H", "绕组短接，快速耗能", False),
        ("正转", "CW", BLUE_D, "H H L H", "OUT1→OUT2", False),
        ("反转", "CCW", RED, "H L H H", "OUT2→OUT1", False),
    ]
    cw, gap = 200, 12
    x0 = (W - (cw * 5 + gap * 4)) / 2
    y0 = 150
    f.htext(W / 2, 122, "四根信号线 PWM/AIN1/AIN2/STBY 组合出全部状态（TB6612 p.4 逐行核验）",
            size=24, color=MUTED, anchor="middle")
    for i, (zh, en, c, pins, note, default) in enumerate(cols):
        x = x0 + i * (cw + gap)
        f.rect(x, y0, cw, 300, color=c, fill=WHITE, r=10)
        f.htext(x + cw / 2, y0 + 52, zh, size=30, color=c, anchor="middle",
                weight="bold", hl=default, hl_fill=AMBER_FILL)
        f.text(x + cw / 2, y0 + 84, en, size=20, color=MUTED, anchor="middle")
        f.text(x + cw / 2, y0 + 150, pins, size=26, color=INK, anchor="middle",
               weight="bold")
        f.multi(x + 16, y0 + 200, [note], size=22, color=INK, lh=30)
    f.multi(90, 530, [
        "三条要点：",
        "1. STBY=L 桥必然关闭 —— 上电安全的地基（GPIO 复位期高阻，靠内部 ~200 kΩ 下拉）",
        "2. 方向有效时 PWM=L 是制动不是滑行；滑行必须 IN1=IN2=L 且 PWM=H",
        "3. 方向由 AIN1/AIN2 决定，PWM 只决定给不给电",
    ], size=24, color=INK, lh=40)
    return f


# ------------------------------------------------------------ fig 2
def two_supplies():
    f = Fig("ch29-two-supplies", "两路电源不是一回事 / two supplies",
            title_color=GREEN_D)
    f.rect(80, 150, 440, 210, color=BLUE_D, fill=WHITE, r=10)
    f.htext(300, 196, "逻辑 Vcc", size=30, color=BLUE_D, anchor="middle",
            weight="bold")
    f.multi(110, 246, ["允许 2.7–5.5 V", "本工程冻结 3.3 V", "来源：MCU 板"],
            size=25, color=INK, lh=38)
    f.rect(632, 150, 440, 210, color=RED, fill=WHITE, r=10)
    f.htext(852, 196, "电机 VM", size=30, color=RED, anchor="middle",
            weight="bold")
    f.multi(662, 246, ["允许 4.5–12 V（保证至 13.5 V）", "本工程冻结 6–12 V（随电机）",
                       "来源：独立可调电源（带限流）"],
            size=25, color=INK, lh=38)
    f.arrow(300, 372, 300, 470, color=BLUE_D)
    f.arrow(852, 372, 852, 470, color=RED)
    f.rect(80, 480, 992, 96, color=MUTED, fill=WHITE, r=10)
    f.htext(W / 2, 524, "GND 必须共地 —— 否则信号没有参考电位，桥状态不可预测",
            size=27, color=INK, anchor="middle", weight="bold", hl=True)
    f.multi(90, 640, [
        "输入门限（官方值）：VIH ≥ 0.7×Vcc（3.3 V 时约 2.31 V）  VIL ≤ 0.3×Vcc",
        "PWM 频率上限 100 kHz —— 本工程冻结 20 kHz，余量充足",
    ], size=25, color=INK, lh=40)
    return f


# ------------------------------------------------------------ fig 3
def current_tiers():
    f = Fig("ch29-current-tiers", "电流三档：按哪一档留余量 / three current tiers",
            title_color=AMBER_STROKE)
    rows = [
        ("连续工作 Operating", "≤1.0 A/通道（VM ≥ 4.5 V）", GREEN_D,
         "唯一可用于连续预算的依据", True),
        ("绝对最大 Absolute Max", "1.2 A/通道", RED,
         "不许达到的边界，不是工作点", False),
        ("单脉冲 t ≤ 10 ms", "3.2 A", AMBER_STROKE,
         "短时冲击参考，不能重复", False),
    ]
    y = 150
    for name, val, c, use, hl in rows:
        f.rect(80, y, 992, 128, color=c, fill=WHITE, r=10)
        f.htext(120, y + 52, name, size=27, color=c, weight="bold", hl=hl)
        f.htext(620, y + 52, val, size=27, color=INK, anchor="middle",
                weight="bold")
        f.text(120, y + 96, use, size=23, color=MUTED)
        y += 148
    f.multi(90, 620, [
        "采购预算：堵转电流 ≤0.8 A 目标值 ÷ 1.0 A 连续上限 = 留 20% 余量",
        "芯片 PD 0.78–1.36 W（按安装降额）；模块散热 = BLK-P0-4 实测项，实测前不作承诺",
    ], size=25, color=INK, lh=40)
    return f


# ------------------------------------------------------------ fig 4 (tail)
def fault_triage():
    f = Fig("ch29-fault-triage", "桥不切换的排查序 / bridge fault triage",
            title_color=RED)
    steps = [
        ("1 测 VM", "VM 4.5–12 V", "没电 = 先查供电轨"),
        ("2 测 STBY", "默认 L（安全态）", "初始化完成且无故障才拉高"),
        ("3 看 AIN", "同低=滑行（高阻）", "PWM=L 才是短接制动"),
        ("4 示波器 PWM", "PA6 应有 20 kHz", "CCR=0 恒无效先排除"),
    ]
    y = 150
    for name, val, note in steps:
        f.rect(80, y, 992, 92, color=RED, fill=WHITE, r=8)
        f.htext(120, y + 56, name, size=27, color=RED, weight="bold")
        f.htext(460, y + 56, val, size=25, color=INK,
                weight="bold")
        f.text(780, y + 56, note, size=22, color=MUTED)
        y += 108
    f.multi(90, 640, [
        "顺序固定：先供电与待机，再逻辑输入，最后才看 PWM —— 从外到内，不回溯",
        "电流档越界（>1.0 A 连续）先降负载，排查表不治热损坏",
    ], size=24, color=INK, lh=38)
    return f


FIGS = {
    "ch29-five-states": five_states,
    "ch29-two-supplies": two_supplies,
    "ch29-current-tiers": current_tiers,
    "ch29-fault-triage": fault_triage,
}

if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        f = FIGS[n]()
        OUT.mkdir(parents=True, exist_ok=True)
        save(f, str(OUT / (n + ".svg")))
        print("wrote", OUT / (n + ".svg"))

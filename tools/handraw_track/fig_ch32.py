# -*- coding: utf-8 -*-
"""ch32 knowledge-track figures (handraw grammar, frozen motor facts)."""
from hd import *


# ------------------------------------------------------------ fig 1
def pi_step():
    f = Fig("ch32-pi-step", "PI 离散式与一步手算 / discrete PI, one tick",
            title_color=BLUE_D)
    f.rect(80, 140, 992, 200, color=BLUE_D, fill=WHITE, r=8)
    f.multi(120, 188, [
        "e(k)     = ramped_rpm(k) − rpm_filt(k)",
        "I_try    = I(k−1) + Ki × e(k) × Δt          u_try = Kp × e(k) + I_try",
        "u        = clamp(u_try, −900, +900)          I = 条件积分",
    ], size=25, color=INK, lh=46)
    f.rect(80, 380, 992, 170, color=GREEN_D, fill=WHITE, r=8)
    f.htext(120, 426, "手算一步：Δt=10 ms，e=−10 rpm，I(0)=0",
            size=26, color=GREEN_D, weight="bold")
    f.multi(120, 470, [
        "I_try = 0.5×(−10)×0.01 = −0.05‰",
        "u_try = 2×(−10) − 0.05 = −20.05‰ → 负输出 = 要求反向驱动",
    ], size=25, color=INK, lh=40)
    f.multi(90, 610, [
        "Kp=2.0 ‰/rpm · Ki=0.5 ‰/(rpm·s) · i_limit=500‰ · duty_limit=900‰ · 斜坡 600 rpm/s",
        "负目标必须能产生负输出 —— 旧实现 fabsf 会彻底失效的地方：负反馈环要有方向概念",
    ], size=24, color=INK, lh=38)
    return f


# ------------------------------------------------------------ fig 2
def state_machine():
    f = Fig("ch32-state-machine", "状态机与事件优先级 / states and priority",
            title_color=AMBER_STROKE)
    states = [
        ("DISABLED", MUTED, 100, 170),
        ("ARMED", BLUE_D, 360, 170),
        ("RUN", GREEN_D, 640, 170),
        ("REVERSING", AMBER_STROKE, 640, 400),
        ("FAULT", RED, 100, 400),
    ]
    for name, c, x, y in states:
        f.rect(x, y, 200, 90, color=c, fill=WHITE, r=10)
        f.htext(x + 100, y + 56, name, size=25, color=c, anchor="middle",
                weight="bold")
    f.arrow(300, 215, 360, 215, color=BLUE_D)      # DISABLED->ARMED
    f.arrow(560, 215, 640, 215, color=GREEN_D)     # ARMED->RUN
    f.arrow(740, 260, 740, 400, color=AMBER_STROKE)  # RUN->REVERSING
    f.arrow(640, 445, 300, 445, color=RED)         # REVERSING->FAULT
    f.arrow(200, 400, 200, 260, color=MUTED)       # FAULT->DISABLED
    f.text(310, 198, "ARM", size=21, color=MUTED)
    f.text(570, 198, "SET_*", size=21, color=MUTED)
    f.text(754, 330, "换向", size=21, color=MUTED)
    f.text(440, 432, "3s 超时 / 故障位", size=21, color=MUTED)
    f.text(216, 330, "CLEAR", size=21, color=MUTED)
    f.rect(80, 560, 992, 110, color=RED, fill=WHITE, r=8)
    f.htext(W / 2, 606, "优先级：故障（F01~F06）> STOP > 换向；故障锁存，不人工 CLEAR 不自恢复",
            size=26, color=INK, anchor="middle", weight="bold", hl=True)
    f.multi(90, 710, ["控制节拍 10 ms（TIM4 硬件时基）与串口任务分离：ISR 只写桥，主循环只收发"],
            size=24, color=INK, lh=36)
    return f


# ------------------------------------------------------------ fig 3
def tuning_ladder():
    f = Fig("ch32-tuning-ladder", "调参阶梯：每步带回退 / tuning ladder",
            title_color=GREEN_D)
    steps = [
        ("1 极性/CPR 确认", "手转方向与符号一致", "回第 31 章查接线"),
        ("2 开环扫速域", "20–400 rpm 可控", "降负载/查限流"),
        ("3 Ki=0 升 Kp", "变快不持续振荡", "振荡→Kp 减半"),
        ("4 小幅加 Ki", "静差收敛无低频摆动", "摆动→Ki 减半"),
        ("5 饱和恢复", "深阶跃退出无大超调", "调 i_limit/条件积分"),
        ("6 重做阶跃/扰动/反转", "指标与重复性达标", "回第 3 步"),
    ]
    y = 140
    for name, ok, back in steps:
        f.rect(80, y, 560, 84, color=GREEN_D, fill=WHITE, r=8)
        f.htext(110, y + 52, name, size=24, color=GREEN_D, weight="bold")
        f.rect(668, y, 180, 84, color=INK, fill=WHITE, r=8)
        f.multi(684, y + 36, [ok], size=20, color=INK, lh=26)
        f.rect(872, y, 200, 84, color=RED, fill=WHITE, r=8)
        f.multi(888, y + 36, ["回退: " + back], size=20, color=RED, lh=26)
        y += 100
    f.multi(90, 760, ["参数只适用于记录的装置 —— 换电机/电源/减速比/采样周期，从第 1 步重做"],
            size=23, color=MUTED, lh=34)
    return f


# ------------------------------------------------------------ fig 4 (tail)
def loop_fault_triage():
    f = Fig("ch32-loop-fault-triage", "闭环异常的分流 / closed-loop fault split",
            title_color=RED)
    f.rect(80, 150, 992, 90, color=MUTED, fill=WHITE, r=8)
    f.htext(W / 2, 205, "异常现象 → 先分流，再调参", size=28, color=INK,
            anchor="middle", weight="bold")
    branches = [
        ("振荡 / 啸叫", RED, ["降 Kp 一半", "仍振荡查编码器方向", "PI 输入带符号不能反"]),
        ("不响应 / 爬不动", AMBER_STROKE, ["FAULT 锁存？先清零", "duty_limit 900‰ 顶死？", "电流档越界被限流"]),
        ("超调大 / 过冲", BLUE_D, ["降 Ki", "ramp 600 rpm/s 太陡？", "i_limit 500‰ 收紧"]),
    ]
    cw, gap = 320, 16
    x0 = (W - (cw * 3 + gap * 2)) / 2
    for i, (name, c, lines) in enumerate(branches):
        x = x0 + i * (cw + gap)
        f.rect(x, 270, cw, 240, color=c, fill=WHITE, r=10)
        f.htext(x + cw / 2, 318, name, size=25, color=c, anchor="middle",
                weight="bold")
        f.multi(x + 24, 366, lines, size=23, color=INK, lh=36)
    f.multi(90, 640, [
        "每步带回退条件（调参阶梯第 1–6 步）；换装置从第 1 步重做，不继承旧参",
        "无反馈 500 ms → 故障锁存：闭环先证明「看得到转速」，再谈调得好不好",
    ], size=24, color=INK, lh=38)
    return f


FIGS = {
    "ch32-pi-step": pi_step,
    "ch32-state-machine": state_machine,
    "ch32-tuning-ladder": tuning_ladder,
    "ch32-loop-fault-triage": loop_fault_triage,
}

if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        f = FIGS[n]()
        OUT.mkdir(parents=True, exist_ok=True)
        save(f, str(OUT / (n + ".svg")))
        print("wrote", OUT / (n + ".svg"))

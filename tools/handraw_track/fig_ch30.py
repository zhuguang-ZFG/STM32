# -*- coding: utf-8 -*-
"""ch30 knowledge-track figures (handraw grammar, frozen motor facts)."""
from hd import *


# ------------------------------------------------------------ fig 1
def pwm_math():
    f = Fig("ch30-pwm-math", "可复算的 PWM 配置 / PWM you can recompute",
            title_color=BLUE_D)
    rows = [
        ("TIM3 时钟", "72 MHz（PSC=0）", "8 MHz HSE × PLL9"),
        ("ARR", "3599", "72 MHz / 20 kHz − 1"),
        ("CCR", "duty‰ × 3600 / 1000", "50% → 1800"),
        ("100% 端点", "CCR 必须 > ARR", "写 3600；=ARR 差一格 99.97%"),
    ]
    y = 150
    for name, val, note in rows:
        f.rect(80, y, 992, 96, color=BLUE_D, fill=WHITE, r=8)
        f.htext(120, y + 58, name, size=27, color=BLUE_D, weight="bold")
        f.htext(480, y + 58, val, size=27, color=INK, anchor="middle",
                weight="bold")
        f.text(760, y + 58, note, size=23, color=MUTED)
        y += 116
    f.multi(90, 640, [
        "为什么 20 kHz：高于可闻频段 · 远低于 TB6612 上限 100 kHz · ARR 仍在 16 位内",
        "CCR=0 恒无效（0%）；CCR>ARR 恒有效（100%）—— 程序用两端表达「撤销驱动」和「全压」",
    ], size=24, color=INK, lh=38)
    return f


# ------------------------------------------------------------ fig 2
def signed_duty():
    f = Fig("ch30-signed-duty", "带符号占空比 / signed duty",
            title_color=GREEN_D)
    f.rect(80, 150, 460, 200, color=GREEN_D, fill=WHITE, r=10)
    f.htext(310, 196, "符号 = 方向", size=30, color=GREEN_D, anchor="middle",
            weight="bold")
    f.multi(120, 246, ["+ 正转 AIN1 高", "− 反转 AIN2 高", "映射只有一处：motor_bridge.c"],
            size=24, color=INK, lh=36)
    f.rect(612, 150, 460, 200, color=BLUE_D, fill=WHITE, r=10)
    f.htext(842, 196, "绝对值 = 幅值", size=30, color=BLUE_D, anchor="middle",
            weight="bold")
    f.multi(652, 246, ["|u| ≤ duty_limit 900‰", "幅值决定 CCR", "拒绝 ≥1000 的配置"],
            size=24, color=INK, lh=36)
    f.arrow(310, 360, 310, 470, color=GREEN_D)
    f.arrow(842, 360, 842, 470, color=BLUE_D)
    f.rect(80, 480, 992, 110, color=MUTED, fill=WHITE, r=10)
    f.htext(W / 2, 528, "斜坡：±50‰ / 10 ms —— 受控起动、换向从零升速都靠它",
            size=27, color=INK, anchor="middle", weight="bold", hl=True)
    f.multi(90, 650, [
        "一处表示，处处使用：命令、PI 输出、斜坡全走带符号占空比",
        "避免「方向寄存器」和「幅值寄存器」两处状态不一致的经典 bug",
    ], size=24, color=INK, lh=38)
    return f


# ------------------------------------------------------------ fig 3
def stop_triage():
    f = Fig("ch30-stop-triage", "停止语义怎么选 / choosing stop semantics",
            title_color=AMBER_STROKE)
    f.htext(W / 2, 130, "PWM=0 的两种映射（配置项）+ 待机（STBY 统一负责）",
            size=24, color=MUTED, anchor="middle")
    cols = [
        ("滑行 coast", GREEN_D, ["输出高阻", "电机自由减速", "无回馈尖峰"]),
        ("短接制动 short brake", AMBER_STROKE, ["绕组短接", "减速快", "有回流尖峰"]),
        ("待机 standby", MUTED, ["STBY=L", "高阻+节电", "上电默认"]),
    ]
    cw, gap = 320, 16
    x0 = (W - (cw * 3 + gap * 2)) / 2
    for i, (name, c, lines) in enumerate(cols):
        x = x0 + i * (cw + gap)
        f.rect(x, 170, cw, 220, color=c, fill=WHITE, r=10)
        f.htext(x + cw / 2, 218, name, size=26, color=c, anchor="middle",
                weight="bold")
        f.multi(x + 26, 268, lines, size=24, color=INK, lh=36)
    f.rect(80, 440, 992, 130, color=RED, fill=WHITE, r=10)
    f.htext(120, 486, "换向必须走 REVERSING：", size=27, color=RED, weight="bold")
    f.multi(120, 528, ["斜坡降到 0 → 撤驱动等停稳（|rpm| ≤ 5）→ 保持 100 ms → 才允许反向输出"],
            size=24, color=INK, lh=34)
    f.multi(90, 640, [
        "命令流中断 500 ms（租约 F01）锁存故障停机 —— 串口拔掉不留转动的电机",
        "直翻换向 = 第 29 章回流尖峰的来源之一；全程 3 s 超时保护",
    ], size=24, color=INK, lh=38)
    return f


# ------------------------------------------------------------ fig 4 (tail)
def no_spin_triage():
    f = Fig("ch30-no-spin-triage", "电机不转的排查序 / motor won't spin triage",
            title_color=RED)
    steps = [
        ("1 状态机在哪", "DISABLED→ARMED→RUN", "故障锁存先 FAULT 清零"),
        ("2 占空比真的给了吗", "斜坡从 0 起步", "刚换向 100 ms 保持期内=0"),
        ("3 CCR 表对不对", "duty‰ × 3600 / 1000", "100% 必须写 CCR>ARR"),
        ("4 电流档剩多少", "连续 ≤1.0 A", "堵转 ≤0.8 A（BLK-P0-4）"),
    ]
    y = 150
    for name, val, note in steps:
        f.rect(80, y, 992, 92, color=RED, fill=WHITE, r=8)
        f.htext(120, y + 56, name, size=27, color=RED, weight="bold")
        f.htext(470, y + 56, val, size=26, color=INK, anchor="middle",
                weight="bold")
        f.text(740, y + 56, note, size=23, color=MUTED)
        y += 108
    f.multi(90, 640, [
        "先软件状态机，再查驱动桥 —— ch29 排查序是桥那半边的延伸",
        "遥测帧（43 B @ 100 Hz）先看状态位与 rpm 原始计数，再怀疑硬件",
    ], size=24, color=INK, lh=38)
    return f


FIGS = {
    "ch30-pwm-math": pwm_math,
    "ch30-signed-duty": signed_duty,
    "ch30-stop-triage": stop_triage,
    "ch30-no-spin-triage": no_spin_triage,
}

if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        f = FIGS[n]()
        OUT.mkdir(parents=True, exist_ok=True)
        save(f, str(OUT / (n + ".svg")))
        print("wrote", OUT / (n + ".svg"))

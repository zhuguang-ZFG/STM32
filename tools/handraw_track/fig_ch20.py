# -*- coding: utf-8 -*-
"""ch20 knowledge-track figure (facts from docs/20).

The three-step manual lookup: pick the manual (RM for registers/timing, DS
for pins/electrical, AN for methods), Ctrl+F the register or bit name, then
read the functional description for timing and formulas. Worked example 1:
TIM1 duty -> RM0008, search CCR1, ch.15, duty = CCR1/(ARR+1). Example 2:
PA11 as USB -> DS5319, search PA11, the Alternate functions column.
"""
from hd import *


def manual_route():
    f = Fig("ch20-manual-route",
            "查手册三步：先选书，再 Ctrl+F，再读上下文 / pick, search, read")

    # ---- 三步主路 ----
    steps = [("① 定手册", ["寄存器/时序 → RM", "引脚/电气 → DS", "做法 → AN"], BLUE_D),
             ("② 搜关键词", ["直接搜寄存器名 TIMx_CCR1", "或位名 CEN"], GREEN_D),
             ("③ 读上下文", ["看功能描述章的时序图", "与公式，再回位表核对"], AMBER_STROKE)]
    x = 84
    for i, (name, lines, color) in enumerate(steps):
        f.rect(x, 150, 300, 132, color=color, fill=WHITE, sw=2.4)
        f.text(x + 150, 184, name, size=22, color=color, anchor="middle",
               weight="bold")
        for j, ln in enumerate(lines):
            f.text(x + 18, 214 + j * 26, ln, size=16, color=INK)
        if i < 2:
            f.arrow(x + 306, 216, x + 342, 216, color=INK, bend=0.0, head=12)
        x += 348

    # ---- 例 1 ----
    f.rect(84, 320, 486, 264, color=GREEN_D, fill=WHITE, sw=2.4)
    f.text(100, 350, "例 1：TIM1 的占空比怎么算", size=20, color=GREEN_D,
           weight="bold")
    f.multi(100, 382, ["→ RM0008（寄存器与时序归它管）",
                       "→ Ctrl+F 搜 CCR1，落到第 15 章",
                       "→ 读 PWM mode 小节：",
                       "    占空比 = CCR1 / (ARR + 1)",
                       "    频率 = fCK_CNT / (ARR + 1)",
                       "→ 回位表核对 OC1M 选 PWM、CC1E 使能"],
            size=17, color=INK, lh=27)

    # ---- 例 2 ----
    f.rect(606, 320, 486, 264, color=BLUE_D, fill=WHITE, sw=2.4)
    f.text(622, 350, "例 2：PA11 能不能做 USB", size=20, color=BLUE_D,
           weight="bold")
    f.multi(622, 382, ["→ DS5319（引脚与电气归它管）",
                       "→ Ctrl+F 搜 PA11，落到引脚表",
                       "→ 看 Alternate functions 列：",
                       "    PA11 = USB_DM（同时也是 CAN_RX）",
                       "→ 复用冲突的细节回 RM0008 第 9 章",
                       "  看 AFIO 重映射"],
            size=17, color=INK, lh=27)

    f.htext(84, 640, "搜中文搜不到时，用英文关键词加手册编号：RM0008 TIM PWM register",
            size=21, color=INK, weight="bold", hl=True)
    f.text(84, 678, "本图只整理本章「查手册的三步」的路线，手册内容以原 PDF 为准", size=17,
           color=MUTED)
    return f


FIGS = {
    "ch20-manual-route": manual_route,
}

if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        f = FIGS[n]()
        OUT.mkdir(parents=True, exist_ok=True)
        save(f, str(OUT / (n + ".svg")))
        print("wrote", OUT / (n + ".svg"))

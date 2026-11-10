# -*- coding: utf-8 -*-
"""ch04 knowledge-track figure (facts from docs/04 section 11, PM0056 Table 7
as cited there).

The chapter covers the three master gates in one paragraph plus a table, with
no dedicated figure: PRIMASK masks every interrupt of configurable priority
(NMI and HardFault still enter), FAULTMASK also masks HardFault and leaves
only NMI, BASEPRI masks only the band whose priority number is >= threshold.
Under the HAL default GROUP_4 all 4 priority bits are preemption: 16 levels,
0 most urgent, 15 slowest. Cross references kept from the chapter text: CSS
(chapter 02) arrives as NMI so __disable_irq() cannot stop it, and FreeRTOS
requires FromISR callers to sit at a priority number no smaller than the
syscall threshold (chapter 15).
"""
from hd import *


def mask_gates():
    f = Fig("ch04-mask-gates",
            "三把总闸：挡的段落各不同 / PRIMASK, FAULTMASK, BASEPRI")

    f.text(84, 126, "GROUP_4：4 位全给抢占，16 级（0 最急、15 最缓）；NMI 和 HardFault 不排在这 16 级里",
           size=20, color=MUTED)

    x0, cw, cwid = 322, 36, 34          # 16 cells: priorities 0..15
    x_end = x0 + 15 * cw + cwid         # 896

    def chip(cy, name, verdict, col):
        f.rect(928, cy, 128, 40, color=col, fill=WHITE, sw=2.0, r=8,
               double=False)
        f.text(992, cy + 26, f"{name}：{verdict}", size=15, color=col,
               anchor="middle", weight="bold")

    def panel(py, name, api, nick, desc, col, blocked_all=False, thr=None,
              nmi="进", hf="进"):
        f.rect(84, py, 980, 170, color=col, fill=WHITE, sw=2.4)
        f.text(100, py + 32, name, size=23, color=col, weight="bold")
        f.text(100, py + 60, api, size=16, color=INK)
        f.text(100, py + 86, nick, size=15, color=MUTED)
        # scale end labels (same row as the threshold tag, far apart)
        f.text(x0, py + 88, "0 最急", size=12, color=MUTED)
        f.text(x_end, py + 88, "15 最缓", size=12, color=MUTED, anchor="end")
        # the 16-cell priority strip
        for i in range(16):
            cx = x0 + i * cw
            is_blk = blocked_all if thr is None else (i >= thr)
            f.rect(cx, py + 96, cwid, 40,
                   color=col if is_blk else MUTED,
                   fill=col if is_blk else WHITE, sw=1.6, r=3, double=False)
            # no halo here: the paper-colour halo turns digits to mush on a
            # dark fill
            f.text(cx + cwid / 2, py + 122, str(i), size=16,
                   color=WHITE if is_blk else INK, anchor="middle",
                   weight="bold", halo=False)
        if thr is not None:
            dx = x0 + thr * cw - 1
            f.line(dx, py + 92, dx, py + 142, color=RED, sw=1.8, dash="5 4")
            f.text(dx, py + 86, "阈值", size=14, color=RED, anchor="middle",
                   weight="bold")
        # verdict chips: what still gets in
        chip(py + 38, "NMI", nmi, GREEN_D if nmi == "进" else RED)
        chip(py + 92, "HardFault", hf, GREEN_D if hf == "进" else RED)
        f.text(100, py + 158, desc, size=15, color=INK)

    panel(136, "PRIMASK", "__disable_irq() / __enable_irq()", "总开关",
          "挡住数值 0–15 的全部可屏蔽中断；NMI 和 HardFault 不归它管，照样进来",
          RED, blocked_all=True, nmi="进", hf="进")

    panel(318, "FAULTMASK", "__disable_fault_irq()", "总开关 + HardFault",
          "可屏蔽的照旧全挡，再把 HardFault 一起关；全片只剩 NMI 能进来",
          AMBER_STROKE, blocked_all=True, nmi="进", hf="挡")

    panel(500, "BASEPRI", "__set_BASEPRI(…)", "阈值闸",
          "写法 __set_BASEPRI(prio << (8 - __NVIC_PRIO_BITS))：只挡数值 ≥ 阈值的一截，"
          "数值更小（更急）的照样进来",
          BLUE_D, blocked_all=False, thr=6, nmi="进", hf="进")

    f.htext(84, 714, "口诀：PRIMASK 全关可屏蔽，FAULTMASK 连 HardFault，BASEPRI 只关不够急的一截",
            size=21, color=INK, weight="bold", hl=True)
    f.text(84, 744, "第 02 章 CSS 的中断走 NMI：__disable_irq() 之后仍进 NMI 是预期，不是 PRIMASK 失效",
           size=15, color=MUTED)
    f.text(84, 768, "FreeRTOS：能调 FromISR 函数的中断，优先级数值不能小于系统调用阈值（第 15 章）",
           size=15, color=MUTED)
    return f


def preempt_timeline():
    f = Fig("ch04-preempt-timeline",
            "抢占什么时候发生：一条时间线与两个对照（167 ns 入栈）")
    # 正常时间线
    f.text(84, 132, "正常：EXTI0(抢占 1) 打断 TIM2(抢占 2) —— 12 HCLK ≈ 167 ns 入栈",
           size=21, color=MUTED)
    y = 190
    segs = [
        ("TIM2 ISR 在跑", 190, GREEN_D),
        ("入栈 ×8 寄存器", 150, AMBER_STROKE),
        ("EXTI0 取向量 + 执行", 240, RED),
        ("出栈返回 TIM2", 150, AMBER_STROKE),
        ("TIM2 继续", 128, GREEN_D),
    ]
    x = 84
    for name, w, c in segs:
        f.rect(x, y, w, 84, color=c, fill=WHITE, sw=2.6)
        f.htext(x + w / 2, y + 50, name, size=18, color=c, anchor="middle")
        x += w + 8
    # 两个对照
    f.rect(84, 330, 470, 180, color=RED, fill=WHITE, sw=2.6)
    f.text(108, 368, "失败：抢占写成同一级", size=22, color=RED, weight="bold")
    f.text(108, 404, "EXTI0 保持挂起，不发生嵌套入栈", size=18, color=INK)
    f.text(108, 436, "数字越小越急；同抢占互不打断", size=18, color=MUTED)
    f.rect(594, 330, 470, 180, color=BLUE_D, fill=WHITE, sw=2.6)
    f.text(618, 368, "PRIMASK = 1", size=22, color=BLUE_D, weight="bold")
    f.text(618, 404, "可配置中断不进入，NMI 仍进入", size=18, color=INK)
    f.text(618, 436, "临界区的门，不是关总中断", size=18, color=MUTED)
    return f


FIGS = {
    "ch04-mask-gates": mask_gates,
    "ch04-preempt-timeline": preempt_timeline,
}

if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        f = FIGS[n]()
        OUT.mkdir(parents=True, exist_ok=True)
        save(f, str(OUT / (n + ".svg")))
        print("wrote", OUT / (n + ".svg"))

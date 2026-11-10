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


def lab_evidence():
    f = Fig("ch04-lab-evidence",
            "三个实验，各留下什么证据 / what each lab leaves behind")
    f.text(84, 128, "实验不是「跑通就算」：每个 Lab 都要留下可复查的判据",
           size=20, color=MUTED)

    labs = [
        ("Lab 1", "EXTI 清标志", BLUE_D,
         ["按键一次，确认 EXTI_PR 的对应位被清掉",
          "计数 10 次有效翻转",
          "不出现「一按进十次」的连环中断"],
         "证据：标志位清零 + 稳定计数"),
        ("Lab 2", "去抖前后对比", GREEN_D,
         ["同一次按键，记录去抖前的中断次数",
          "再去抖后重复 10 次",
          "两次计数写在同一张记录里"],
         "证据：抖动被软件滤掉多少"),
        ("Lab 3", "抢占真的发生", RED,
         ["EXTI0 抢占 1，TIM2 抢占 2",
          "两个 ISR 各自翻转一路 GPIO",
          "双迹顺序：EXTI0 的进入/退出夹住 TIM2"],
         "证据：嵌套顺序，不是「感觉很快」"),
    ]
    for i, (tag, title, color, lines, evidence) in enumerate(labs):
        y = 160 + i * 182
        f.rect(84, y, 984, 166, color=color, fill=WHITE, sw=2.4)
        f.text(108, y + 38, tag, size=21, color=color, weight="bold")
        f.text(196, y + 38, title, size=20, color=INK, weight="bold")
        f.multi(108, y + 70, lines, size=16, color=INK, lh=26)
        f.text(108, y + 152, evidence, size=15, color=color, weight="bold")

    f.htext(W / 2, 724, "图给的是实验设计与判据；它不冒充已有波形",
            size=22, color=INK, weight="bold", anchor="middle", hl=True)
    f.text(84, 762, "三个 Lab 的步骤与计数取自本章「动手实验」；双迹需逻辑分析仪两路通道",
           size=15, color=MUTED)
    return f


def numbers_ledger():
    f = Fig("ch04-numbers-ledger",
            "开读之前先对表：本章的四个基准数字")
    f.text(84, 118, "全章算的都是这只 C8、这个分组；换任何一项，后面图的数字都要重查",
           size=19, color=MUTED)

    cards = [
        ("① 芯片与时钟", BLUE_D,
         ["STM32F103C8T6；SYSCLK = HCLK = 72 MHz",
          "时钟树与附录 D 一致",
          "EXTI0 用 PA0，不借第 10 脚以外的新脚"]),
        ("② 优先级分组", GREEN_D,
         ["HAL 默认 NVIC_PRIORITYGROUP_4",
          "4 位全给抢占，子优先级 0 位",
          "数值越小越优先；改分组要重新比"]),
        ("③ 入栈代价", RED,
         ["异常入口压 8 个寄存器",
          "约 12 HCLK ≈ 167 ns @ 72 MHz",
          "不含 ISR 正文与尾链的省法"]),
        ("④ 按键通道", AMBER_STROKE,
         ["PA0 → EXTI0，EXTI0_IRQn = 6",
          "F1 先开 AFIO 时钟再写 EXTICR",
          "线按脚号共用：PA0 与 PB0 抢同一根"]),
    ]
    for i, (tag, col, lines) in enumerate(cards):
        x = 84 + (i % 2) * 512
        y = 146 + (i // 2) * 268
        f.rect(x, y, 472, 244, color=col, fill=WHITE, sw=2.4)
        f.text(x + 24, y + 40, tag, size=22, color=col, weight="bold")
        f.multi(x + 24, y + 84, lines, size=17, color=INK, lh=32)

    f.htext(W / 2, 700, "图只给基准；真正的抢占与入栈过程在后面的时间线上",
            size=22, color=INK, weight="bold", anchor="middle", hl=True)
    f.text(84, 744, "四个数字取自本章「原理与适用范围」「时序与状态」「§4」；12 HCLK 见 PM0056 第 2.3.7 节",
           size=15, color=MUTED)
    return f


def event_pipeline():
    f = Fig("ch04-event-pipeline",
            "从一次按键到一个 ISR：认领、仲裁、执行、返回")
    f.text(84, 118, "五个阶段的归属不同；排错时先认出坏在哪一段",
           size=19, color=MUTED)

    stages = [
        ("① 引脚事件", BLUE_D, ["PA0 的下降沿", "电平变化先变成边沿"]),
        ("② 认领 EXTI", GREEN_D, ["边沿置 EXTI_PR 挂起位", "IMR 不开门就不往下走"]),
        ("③ 仲裁 NVIC", AMBER_STROKE, ["比抢占优先级数值", "0 最急；同抢占不嵌套"]),
        ("④ 执行 ISR", BLUE_D, ["压 8 个寄存器、取向量", "正文是用户代码"]),
        ("⑤ 返回", RED, ["有挂起就尾链", "省一次出栈再入栈"]),
    ]
    bw, gap = 176, 26
    for i, (tag, col, lines) in enumerate(stages):
        x = 84 + i * (bw + gap)
        f.rect(x, 190, bw, 196, color=col, fill=WHITE, sw=2.4)
        f.text(x + 18, 228, tag, size=20, color=col, weight="bold")
        f.multi(x + 18, 266, lines, size=15, color=INK, lh=26)
        if i < 4:
            f.arrow(x + bw + 2, 288, x + bw + gap - 2, 288, color=INK, sw=2.6)

    f.rect(84, 432, 474, 108, color=BLUE_D, fill=WHITE, sw=2.2)
    f.text(108, 466, "EXTI 决定何时被注意到", size=20, color=BLUE_D, weight="bold")
    f.multi(108, 498, ["NVIC 决定谁先跑；两件事分开查"], size=16, color=INK, lh=26)
    f.rect(594, 432, 474, 108, color=RED, fill=WHITE, sw=2.2)
    f.text(618, 466, "子优先级不产生嵌套", size=20, color=RED, weight="bold")
    f.multi(618, 498, ["只在多份请求同时挂起时排序"], size=16, color=INK, lh=26)

    f.rect(84, 576, 984, 96, color=MUTED, fill=GRAY_FILL, sw=2.0, dash="7 5")
    f.text(108, 608, "三个总闸在这条流水线外侧：", size=18, color=INK, weight="bold")
    f.text(108, 642, "PRIMASK 挡可配置中断（NMI 仍进）· FAULTMASK 再挡 HardFault · BASEPRI 只挡 ≥ 阈值的那截",
           size=16, color=INK)

    f.htext(W / 2, 726, "记住分工：EXTI 管「注意到」，NVIC 管「谁先跑」",
            size=22, color=INK, weight="bold", anchor="middle", hl=True)
    f.text(84, 762, "三个阶段名与总闸范围取自本章核心原理与 §11；尾链细节见 §10 的周期图",
           size=15, color=MUTED)
    return f


FIGS = {
    "ch04-numbers-ledger": numbers_ledger,
    "ch04-event-pipeline": event_pipeline,
    "ch04-lab-evidence": lab_evidence,
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

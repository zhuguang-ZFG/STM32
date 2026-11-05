# -*- coding: utf-8 -*-
"""ch17 knowledge-track figure (facts from docs/17, PM0056).

This Cortex-M3 has 6 hardware breakpoint comparators; a 7th breakpoint in
Flash makes the debugger report an error or simply not stop. Cortex-M7
(F7/H7) has 8, so numbers from H7 tutorials do not transfer.
"""
from hd import *


def bp_comparators():
    f = Fig("ch17-bp-comparators",
            "硬件断点：这颗 M3 只有 6 个比较器 / six comparators, no seventh")

    # ---- 左：6 个比较器槽 ----
    f.rect(84, 150, 520, 368, color=BLUE_D, fill=WHITE, sw=2.6)
    f.text(344, 182, "Cortex-M3（F103）的断点比较器", size=22, color=BLUE_D,
           anchor="middle", weight="bold")
    slots = [("比较器 0", "main 循环"), ("比较器 1", "发送函数"),
             ("比较器 2", "解析分支"), ("比较器 3", "出错处理"),
             ("比较器 4", "状态翻转"), ("比较器 5", "最后一个")]
    y = 200
    for name, what in slots:
        f.rect(140, y, 180, 38, color=BLUE_D, fill=WHITE, sw=2.0)
        f.text(230, y + 26, name, size=17, color=BLUE_D, anchor="middle",
               weight="bold")
        f.text(348, y + 26, f"← {what}", size=17, color=INK)
        y += 42
    # 第 7 个
    f.rect(140, y + 4, 180, 38, color=RED, fill=RED, sw=2.2)
    f.text(230, y + 30, "第 7 个", size=17, color=WHITE, anchor="middle",
           weight="bold", halo=False)
    f.text(348, y + 30, "✗ 没有比较器了：报错或不停", size=17, color=RED,
           weight="bold")

    # ---- 右：M3 vs M7 ----
    f.text(668, 178, "别把 H7 教程的数字抄过来", size=21, color=MUTED)
    f.rect(668, 196, 424, 92, color=GREEN_D, fill=WHITE, sw=2.4)
    f.text(684, 226, "Cortex-M3：6 个", size=22, color=GREEN_D, weight="bold")
    f.text(684, 258, "F103 上打到第 7 个就会出事", size=17, color=INK)
    f.rect(668, 306, 424, 92, color=AMBER_STROKE, fill=WHITE, sw=2.4)
    f.text(684, 336, "Cortex-M7：8 个", size=22, color=AMBER_STROKE,
           weight="bold")
    f.text(684, 368, "F7 / H7 才是这个数，不能照搬", size=17, color=INK)

    f.rect(668, 416, 424, 92, color=MUTED, fill=WHITE, sw=2.2)
    f.multi(684, 444, ["断点停在 Flash 里，不占 RAM",
                       "但比较器数量是硬上限：", "改一行试试之前，先数数用了几个"],
            size=17, color=INK, lh=25)

    # ---- 底：证据三件套 ----
    f.rect(84, 530, 1008, 96, color=GREEN_D, fill=WHITE, sw=2.4)
    f.text(100, 560, "断点只是证据三件套之一", size=21, color=GREEN_D,
           weight="bold")
    f.multi(100, 590, ["断点停在哪（6 个比较器要用在刀刃上）｜关键寄存器是多少（CFSR / BFAR）｜线上到底有没有边沿（示波器）",
                       "比较器用完就去掉一个旧断点，别指望第 7 个"],
            size=17, color=INK, lh=25)

    f.htext(84, 688, "第 7 个断点不会排队等空位——它要么报错，要么假装在工作", size=23,
            color=INK, weight="bold", hl=True)
    return f


FIGS = {
    "ch17-bp-comparators": bp_comparators,
}

if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        f = FIGS[n]()
        OUT.mkdir(parents=True, exist_ok=True)
        save(f, str(OUT / (n + ".svg")))
        print("wrote", OUT / (n + ".svg"))

# -*- coding: utf-8 -*-
"""ch15 knowledge-track figure: what priority inheritance buys (docs/15 §6).

Three tasks on one core: low holds the mutex, a mid task preempts it, a high
task then blocks on the same mutex. With inheritance the low task runs at the
high priority until it releases; without it there is no such rescue.
"""
from hd import *

T0, T1 = 150, 1060          # time axis
LANES = {"H": 236, "M": 344, "L": 452}


def prio_inherit():
    f = Fig("ch15-prio-inherit", "优先级继承在救谁 / what inheritance buys")

    # 车道与时间轴
    for name, y in LANES.items():
        f.text(96, y + 40, name, size=26, color=INK, anchor="middle",
               weight="bold")
        f.line(T0 - 10, y + 58, T1, y + 58, color=MUTED, sw=1.6, amp=1.2)
    f.text(96, 214, "优先级", size=20, color=MUTED, anchor="middle")

    def span(x0, x1, y, label, color, fill=WHITE, size=19, hatch=False):
        f.rect(x0, y, x1 - x0, 58, color=color, fill=fill, sw=2.4)
        f.text((x0 + x1) / 2, y + 38, label, size=size, color=color,
               anchor="middle", weight="bold")
        if hatch:
            for hx in range(int(x0) + 12, int(x1) - 6, 18):
                f.line(hx, y + 8, hx + 10, y + 50, color=color, sw=1.2,
                       amp=0.6)

    # 时间片
    span(T0, 300, LANES["L"], "L 拿到互斥量", GREEN_D)
    span(300, 430, LANES["M"], "M 就绪，抢占", BLUE_D)
    span(430, 560, LANES["H"], "H 等互斥量", RED, hatch=True)
    span(430, 700, LANES["L"], "L 继承 H 的优先级", AMBER_STROKE)
    span(700, 840, LANES["H"], "H 运行", RED)
    span(840, 1000, LANES["L"], "L 回到低优先级", GREEN_D)

    # 标记
    for x, label, y in ((430, "继承", 566), (700, "给还", 566)):
        f.line(x, 470, x, 512, color=MUTED, sw=1.4, dash="6 6", amp=0.8)
        f.text(x + 8, y - 44, label, size=18, color=MUTED)

    f.arrow(430, 300, 430, 470, color=AMBER_STROKE, bend=0.12)
    f.text(440, 300, "H 阻塞的一刻，L 顶上来", size=19, color=AMBER_STROKE)

    # 没有继承会怎样
    f.rect(150, 604, 420, 104, color=BLUE_D, fill=WHITE, sw=2.4)
    f.text(166, 634, "二值信号量：没有继承", size=22, color=BLUE_D,
           weight="bold")
    f.multi(166, 662, ["H 一直等锁，等待时间被 M 拖长", "可能直接错过截止点"],
            size=18, color=INK, lh=26)

    f.rect(610, 604, 450, 104, color=GREEN_D, fill=WHITE, sw=2.4)
    f.text(626, 634, "互斥量：继承把优先级借给 L", size=22, color=GREEN_D,
           weight="bold")
    f.multi(626, 662, ["M 抢不到 CPU，L 尽快跑完临界区", "等待时间 ≈ 临界区长度"],
            size=18, color=INK, lh=26)

    f.htext(560, 746, "继承只在互斥量上；信号量本身只是一面旗", size=22,
            color=INK, weight="bold", hl=True, anchor="middle")
    return f


FIGS = {
    "ch15-prio-inherit": prio_inherit,
}

if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        f = FIGS[n]()
        OUT.mkdir(parents=True, exist_ok=True)
        save(f, str(OUT / (n + ".svg")))
        print("wrote", OUT / (n + ".svg"))

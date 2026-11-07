# -*- coding: utf-8 -*-
"""ch03 knowledge-track figure (facts from docs/03, RM0008 Rev 21 sec. 9.2.7).

The chapter's LCKR lock exists only as a table and a code snippet: GPIOx_LCKR
at offset 0x18, mask LCK[15:0] held unchanged, LCKK written 1 -> 0 -> 1, then
two consecutive reads, the second must confirm LCKK = 1; locked until reset.
One broken step (mask changed, or a write/read skipped) aborts the lock and
the pin stays editable. The example code locks PA5 (LCKK | LCK5).
"""
from hd import *


def lckr_sequence():
    f = Fig("ch03-lckr-sequence",
            "LCKR 锁脚：1-0-1 再读两遍 / the LCKR lock sequence")

    # ---- 顶：为什么锁 + 寄存器 ----
    f.text(84, 140, "为什么要锁：锁定某一脚，避免后面的初始化再改它"
                    "（寄存器 GPIOx_LCKR，偏移 0x18）",
           size=19, color=MUTED)

    # ---- 掩码括线 ----
    f.text(84, 178, "五步里 LCK[15:0] 掩码保持不变（第 1 步就选定要锁的脚）",
           size=19, color=BLUE_D, weight="bold")
    f.line(84, 196, 1024, 196, color=BLUE_D, sw=1.6, amp=0.8, opacity=0.7)
    f.line(84, 190, 84, 196, color=BLUE_D, sw=1.6, amp=0.8, opacity=0.7)
    f.line(1024, 190, 1024, 196, color=BLUE_D, sw=1.6, amp=0.8, opacity=0.7)

    # ---- 中：五步协议 ----
    steps = [
        ("① 写", "LCKK 写 1", "序列开始", BLUE_D),
        ("② 写", "LCKK 写 0", "序列继续", BLUE_D),
        ("③ 写", "LCKK 写 1", "写序列完成", BLUE_D),
        ("④ 读", "第一次读", "LCKR", AMBER_STROKE),
        ("⑤ 读", "第二次读", "LCKK = 1", GREEN_D),
    ]
    bx, bw, gap, by, bh = 84, 164, 30, 210, 160
    for i, (kind, act, res, col) in enumerate(steps):
        x = bx + i * (bw + gap)
        f.rect(x, by, bw, bh, color=col, fill=WHITE, sw=2.4)
        f.text(x + bw / 2, by + 36, kind, size=20, color=col,
               anchor="middle", weight="bold")
        f.text(x + bw / 2, by + 76, act, size=16, color=INK, anchor="middle")
        f.text(x + bw / 2, by + 104, res, size=16, color=INK, anchor="middle")
        if i == 4:
            f.text(x + bw / 2, by + 138, "锁住到复位", size=16, color=GREEN_D,
                   anchor="middle", weight="bold")
        if i < 4:
            f.text(x + bw + gap / 2, by + 86, "→", size=22, color=INK,
                   anchor="middle", weight="bold")

    # ---- 失败分支 ----
    f.rect(84, 396, 980, 92, color=RED, fill=WHITE, sw=2.4)
    f.text(100, 426, "错一步，锁就中止", size=20, color=RED, weight="bold")
    f.text(100, 460, "中途改了掩码，或少了一次写/读 → 第二次读 LCKK 不是 1"
                     " → 锁中止，配置仍可改",
           size=18, color=INK)

    # ---- 代码对照 ----
    f.rect(84, 512, 980, 150, color=GREEN_D, fill=WHITE, sw=2.4)
    f.text(100, 542, "例程锁 PA5：三次写、两次读，一次都不能少", size=19,
           color=GREEN_D, weight="bold")
    f.multi(100, 574, [
        "GPIOA->LCKR = LCKK | LCK5;    ← 第 1 步：写 1",
        "GPIOA->LCKR = LCK5;           ← 第 2 步：写 0",
        "GPIOA->LCKR = LCKK | LCK5;    ← 第 3 步：再写 1",
        "(void)GPIOA->LCKR;  (void)GPIOA->LCKR;   ← 第 4、5 步：连读两次",
    ], size=16, color=INK, lh=26)

    f.text(84, 694, "少一次读，锁就不成立——第 4、5 步的读就是确认", size=18,
           color=MUTED)

    f.htext(84, 744, "口诀：掩码不动，写 1、写 0、再写 1，读两遍"
                     "——第二遍 LCKK 必须是 1",
            size=24, color=INK, weight="bold", hl=True)
    return f


FIGS = {
    "ch03-lckr-sequence": lckr_sequence,
}

if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        f = FIGS[n]()
        OUT.mkdir(parents=True, exist_ok=True)
        save(f, str(OUT / (n + ".svg")))
        print("wrote", OUT / (n + ".svg"))

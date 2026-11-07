# -*- coding: utf-8 -*-
"""ch12 knowledge-track figure (facts from docs/12, RM0008 Rev 21 ch.3).

The unlock keys and the jump words already have their own boards. What the
prose only carries as a numbered list plus a code loop is the half-word
programming rhythm: erase runs PER -> AR -> STRT -> poll BSY -> check EOP,
then programming sets PG=1, writes one 16-bit half-word at addr + i*2, waits
for BSY, and repeats until the buffer is done; a 32-bit value therefore takes
two half-word writes and the sequence ends with CR.LOCK=1.
"""
from hd import *


def halfword_loop():
    f = Fig("ch12-halfword-loop",
            "半字写入：写一个，等一个 / one half-word, one BSY wait")

    f.text(84, 130, "开锁后先擦后写：每一步都等忙标志清零再做下一步，最后记得重新上锁",
           size=21, color=MUTED)

    # ---- 第 1 步：整页擦除的五拍 ----
    f.text(84, 158, "先擦：整页擦除，五拍走完才算擦过", size=19,
           color=GREEN_D, weight="bold")
    steps = [
        ("① CR.PER=1", "置 1 选页擦除", GREEN_D),
        ("② FLASH_AR", "写入页地址", BLUE_D),
        ("③ CR.STRT=1", "启动擦除", BLUE_D),
        ("④ 轮询 SR.BSY", "等到它 =0", RED),
        ("⑤ 检查 SR.EOP", "擦除完成标志", GREEN_D),
    ]
    for i, (t, s, col) in enumerate(steps):
        x = 84 + i * 201
        f.rect(x, 172, 176, 120, color=col, fill=WHITE, sw=2.4)
        f.text(x + 88, 214, t, size=20, color=col, anchor="middle",
               weight="bold")
        f.text(x + 88, 252, s, size=17, color=INK, anchor="middle")
        if i:
            f.arrow(x - 23, 232, x - 2, 232, color=INK, sw=2.4, bend=0.0)
    f.text(84, 318, "F1 页擦除 ~20~40 ms：忙标志落下之前，别急着去读",
           size=17, color=AMBER_STROKE)

    # ---- 第 2 步：半字编程循环 ----
    f.text(84, 372, "再写：半字循环，写一个等一个", size=19,
           color=BLUE_D, weight="bold")
    boxes = [
        (84, 190, "① 置 CR.PG=1", ["进入编程模式"], BLUE_D),
        (322, 240, "② 写一个半字", ["地址 addr + i×2", "（2 字节对齐）"], GREEN_D),
        (610, 190, "③ 轮询 SR.BSY", ["等它落回 0"], RED),
        (852, 212, "④ 全部写完", ["置 CR.LOCK=1", "重新上锁"], AMBER_STROKE),
    ]
    for x, w, t, lines, col in boxes:
        f.rect(x, 388, w, 110, color=col, fill=WHITE, sw=2.4)
        f.text(x + w / 2, 420, t, size=20, color=col, anchor="middle",
               weight="bold")
        f.multi(x + w / 2, 448, lines, size=17, color=INK, anchor="middle",
                lh=25)
    f.arrow(276, 443, 320, 443, color=INK, sw=2.4, bend=0.0)
    f.arrow(564, 443, 608, 443, color=INK, sw=2.4, bend=0.0)
    f.arrow(802, 443, 850, 443, color=INK, sw=2.4, bend=0.0)
    # 循环回边：没写完就回到写半字那一步
    f.arrow(705, 502, 442, 502, color=RED, sw=2.6, bend=-0.28)
    f.text(573, 560, "没写完：i++，地址 +2，再等一次 BSY", size=17,
           color=RED, anchor="middle")

    # ---- 底：两条硬规矩 ----
    f.rect(84, 584, 480, 104, color=BLUE_D, fill=WHITE, sw=2.4)
    f.text(104, 614, "一个 32 位值 = 两次半字写", size=20, color=BLUE_D,
           weight="bold")
    f.multi(104, 642, ["data[i] → addr，data[i+1] → addr+2",
                       "F103 不能按字节编程"], size=17, color=INK, lh=25)

    f.rect(596, 584, 468, 104, color=GREEN_D, fill=WHITE, sw=2.4)
    f.text(616, 614, "擦除后读回 0xFFFF", size=20, color=GREEN_D,
           weight="bold")
    f.multi(616, 642, ["写入只能把 1 变成 0", "0 想回到 1：先擦整页"],
            size=17, color=INK, lh=25)

    f.htext(84, 726, "口诀：写一个半字，等一次 BSY；没写完地址加 2，再来一遍",
            size=23, color=INK, weight="bold", hl=True)
    return f


FIGS = {
    "ch12-halfword-loop": halfword_loop,
}

if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        f = FIGS[n]()
        OUT.mkdir(parents=True, exist_ok=True)
        save(f, str(OUT / (n + ".svg")))
        print("wrote", OUT / (n + ".svg"))

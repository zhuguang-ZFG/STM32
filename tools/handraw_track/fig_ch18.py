# -*- coding: utf-8 -*-
"""ch18 knowledge-track figure (facts from docs/18, item C5).

A definition written in a header is compiled into every .c that includes it,
so two translation units each emit the symbol and the linker reports
`multiple definition`. The fix: extern declaration in the header, one
definition in a .c.
"""
from hd import *


def multi_def():
    f = Fig("ch18-multi-def",
            "变量写进头文件：每个包含它的 .c 都定义一遍 / definition in a header")

    # ---- 上：错的写法 ----
    f.rect(84, 150, 984, 226, color=RED, fill=WHITE, sw=2.4)
    f.text(100, 180, "错的写法：头文件里写定义", size=21, color=RED,
           weight="bold")
    # 头文件
    f.rect(120, 200, 300, 82, color=RED, fill=WHITE, sw=2.2)
    f.text(270, 226, "sensor.h", size=19, color=RED, anchor="middle",
           weight="bold")
    f.text(136, 258, "int count;   ← 这是定义", size=18, color=INK)
    # 两个 .c
    f.rect(520, 176, 250, 82, color=INK, fill=WHITE, sw=2.2)
    f.text(645, 202, "main.c", size=19, color=INK, anchor="middle",
           weight="bold")
    f.text(536, 234, "#include \"sensor.h\"", size=16, color=MUTED)
    f.text(536, 250, "→ 定义了一份 count", size=16, color=INK)
    f.rect(520, 276, 250, 82, color=INK, fill=WHITE, sw=2.2)
    f.text(645, 302, "motor.c", size=19, color=INK, anchor="middle",
           weight="bold")
    f.text(536, 334, "#include \"sensor.h\"", size=16, color=MUTED)
    f.text(536, 350, "→ 又定义了一份 count", size=16, color=INK)
    f.arrow(420, 244, 512, 216, color=RED, bend=0.08)
    f.arrow(420, 260, 512, 312, color=RED, bend=-0.08)
    f.rect(836, 226, 216, 96, color=RED, fill=WHITE, sw=2.2)
    f.multi(852, 254, ["链接器：", "multiple definition", "of `count`"],
            size=18, color=RED, lh=25, weight="bold")

    # ---- 下：对的写法 ----
    f.rect(84, 404, 984, 190, color=GREEN_D, fill=WHITE, sw=2.4)
    f.text(100, 434, "对的写法：头文件只声明，定义放一个 .c", size=21,
           color=GREEN_D, weight="bold")
    f.rect(120, 454, 300, 82, color=GREEN_D, fill=WHITE, sw=2.2)
    f.text(270, 480, "sensor.h", size=19, color=GREEN_D, anchor="middle",
           weight="bold")
    f.text(136, 512, "extern int count;   ← 只声明", size=18, color=INK)
    f.rect(520, 454, 250, 82, color=GREEN_D, fill=WHITE, sw=2.2)
    f.text(645, 480, "sensor.c", size=19, color=GREEN_D, anchor="middle",
           weight="bold")
    f.text(536, 512, "int count = 0;   ← 全项目只有这一份", size=15, color=INK)
    f.text(836, 470, "main.c / motor.c", size=18, color=INK, weight="bold")
    f.text(836, 498, "拿同一份符号用，", size=16, color=MUTED)
    f.text(836, 520, "链接一次通过 ✓", size=17, color=GREEN_D, weight="bold")

    f.htext(84, 656, "extern 是「到别处找定义」，头文件里只有声明才能被随便包含", size=23,
            color=INK, weight="bold", hl=True)
    f.text(84, 694, "顺手规则：头文件只放声明、类型和宏；static 的 helper 不进头文件", size=18,
           color=MUTED)
    return f


FIGS = {
    "ch18-multi-def": multi_def,
}

if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        f = FIGS[n]()
        OUT.mkdir(parents=True, exist_ok=True)
        save(f, str(OUT / (n + ".svg")))
        print("wrote", OUT / (n + ".svg"))

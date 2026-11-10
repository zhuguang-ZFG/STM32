# ch00 knowledge-track figure (facts from docs/00 三阶段学习路线图).
# Deterministic: same input text -> same SVG bytes.
from hd import *

OUT = Path(__file__).resolve().parents[2] / "assets" / "illustrations" / "handraw"


def rtos_worth_it():
    f = Fig("ch00-rtos-worth-it",
            "什么时候才值得上 RTOS / when an RTOS is worth it")
    f.text(84, 118, "阶段三的自测题：「什么场景才值得上 RTOS？」先问裸机还剩多少余量",
           size=21, color=MUTED)
    # 左列：该上的三个信号
    f.rect(84, 150, 470, 300, color=GREEN_D, fill=WHITE, sw=2.6)
    f.text(112, 190, "该上的三个信号", size=25, color=GREEN_D, weight="bold")
    sig = [
        "任务周期各异：采样 1 ms、显示 100 ms、",
        "  通信 10 ms，一个 while 调度不过来",
        "有抢占优先级需求：按键要打断慢任务",
        "状态机已经画不下：嵌套标志位绕不回",
    ]
    y = 232
    for s in sig:
        f.text(112, y, s, size=19, color=INK)
        y += 44
    # 右列：不该上的两个信号
    f.rect(594, 150, 470, 300, color=RED, fill=WHITE, sw=2.6)
    f.text(622, 190, "不该上的两个信号", size=25, color=RED, weight="bold")
    no = [
        "只有一个 while 循环就跑得完",
        "中断 + 标志位已经够用",
        "「用了 RTOS 才显得专业」不是理由",
    ]
    y = 240
    for s in no:
        f.text(622, y, s, size=19, color=INK)
        y += 48
    # 底部结论条
    f.rect(84, 486, 980, 72, color=INK, fill=WHITE, sw=2.2)
    f.htext(W / 2, 524, "先问：裸机 + 定时器调度能不能写完？能，就不上",
            size=23, color=INK, anchor="middle", weight="bold", hl=True)
    return f


FIGS = {
    "ch00-rtos-worth-it": rtos_worth_it,
}

if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        f = FIGS[n]()
        OUT.mkdir(parents=True, exist_ok=True)
        save(f, str(OUT / (n + ".svg")))
        print("wrote", OUT / (n + ".svg"))

# -*- coding: utf-8 -*-
"""ch15 knowledge-track figure: what priority inheritance buys (docs/15 §6).

Three tasks on one core: low holds the mutex, a mid task preempts it, a high
task then blocks on the same mutex. With inheritance the low task runs at the
high priority until it releases; without it there is no such rescue.
"""
from hd import *

T0, T1 = 250, 1060
LANES = {"H": 236, "M": 344, "L": 452}


def prio_inherit():
    f = Fig("ch15-prio-inherit", "H 在等锁，为什么反而让 L 先跑？")
    f.text(84, 138, "单核、三任务、一把互斥量；H > M > L；横轴只表示先后，不表示实测时长",
           size=20, color=MUTED)
    for name, y in LANES.items():
        f.text(96, y + 36, name, size=26, color=INK, anchor="middle",
               weight="bold")
        f.text(145, y + 36, {"H": "高优先级", "M": "中优先级", "L": "低优先级"}[name],
               size=18, color=MUTED)
        f.line(T0 - 10, y + 58, T1, y + 58, color=MUTED, sw=1.6, amp=1.2)
    for x, label in ((390, "M 就绪"), (530, "H 请求锁"), (800, "L 释放锁")):
        f.line(x, 210, x, 518, color=MUTED, sw=1.4, dash="5 7", amp=0.5)
        f.text(x, 192, label, size=18, color=MUTED, anchor="middle")

    def running(x0, x1, task, label, color):
        y = LANES[task]
        f.rect(x0, y, x1 - x0, 58, color=color, fill=color, sw=2.4)
        f.text((x0 + x1) / 2, y + 37, label, size=20, color=WHITE,
               anchor="middle", weight="bold", halo=False)

    running(T0, 390, "L", "L 持锁", GREEN_D)
    running(390, 530, "M", "M 运行", BLUE_D)
    running(530, 800, "L", "L 继承 H 的优先级", AMBER_STROKE)
    running(800, T1, "H", "H 取得锁并运行", RED)
    f.rect(530, LANES["H"], 270, 58, color=RED, fill=WHITE, dash="6 5")
    f.text(665, LANES["H"] + 37, "H 阻塞，等 L 还锁", size=20,
           color=RED, anchor="middle")
    f.text(665, LANES["M"] + 36, "M 仍就绪，暂时得不到 CPU", size=18,
           color=MUTED, anchor="middle")
    f.text(812, LANES["L"] + 35, "L 优先级回落，暂不运行", size=18, color=GREEN_D)
    f.text(250, 552, "实色 = 正在运行；虚框 = 阻塞。H 等待段与 L 继承后的运行段对齐。",
           size=19, color=MUTED)

    f.rect(84, 590, 476, 118, color=BLUE_D, fill=WHITE, sw=2.4)
    f.text(100, 622, "若用二值信号量：没有继承", size=21, color=BLUE_D,
           weight="bold")
    f.multi(100, 654, ["M 可继续抢占 L，H 的等待被 M 拖长", "M 一直就绪时，L 甚至没机会释放资源"],
            size=18, color=INK, lh=26)
    f.rect(590, 590, 476, 118, color=GREEN_D, fill=WHITE, sw=2.4)
    f.text(606, 622, "用互斥量：L 暂时与 H 同优先级", size=21, color=GREEN_D,
           weight="bold")
    f.multi(606, 654, ["M 不能再抢占 L，L 得以继续释放资源", "ISR、更高优先级任务等仍会影响等待"],
            size=18, color=INK, lh=26)
    f.htext(576, 748, "继承消除 M 这一层干扰；等待上限仍要算、仍要测", size=22,
            color=INK, weight="bold", hl=True, anchor="middle")
    return f


def psp_msp():
    f = Fig("ch15-psp-msp", "任务有自己的栈，ISR 又把数据放在哪里？")
    f.text(84, 138, "STM32F103 · Cortex-M3 · FreeRTOS GCC ARM_CM3 · 任务运行用 PSP，异常处理用 MSP",
           size=20, color=MUTED)
    f.rect(84, 174, 452, 476, color=BLUE_D, fill=WHITE)
    f.rect(616, 174, 452, 476, color=GREEN_D, fill=WHITE)
    f.text(106, 210, "PSP → 当前任务的栈", size=26, color=BLUE_D, weight="bold")
    f.text(638, 210, "MSP → 主栈 / 异常栈", size=26, color=GREEN_D, weight="bold")
    f.text(106, 244, "① 任务 A 正在运行", size=21, color=INK)
    f.text(638, 244, "③ 进入 ISR 后切到 MSP", size=21, color=INK)
    for x, y, w, h, color, head, detail in (
        (106, 270, 408, 78, BLUE_D, "任务函数调用、局部变量", "随 A 的 PSP 向下增长"),
        (106, 374, 408, 92, RED, "② IRQ 到来：硬件保存 8 个寄存器", "R0–R3、R12、LR、PC、xPSR"),
        (106, 492, 408, 92, AMBER_STROKE, "若 PendSV 切换任务，再保存 R4–R11", "移植层把 A 的 PSP 存到 TCB"),
        (638, 270, 408, 92, GREEN_D, "ISR 的 C 函数调用、局部变量", "使用 MSP，不继续占用 A 的 PSP"),
        (638, 390, 408, 106, RED, "更高优先级 IRQ 嵌套到来", "被打断的 handler 也在 MSP 上入栈"),
    ):
        f.rect(x, y, w, h, color=color, fill=PAPER, sw=2.2)
        f.text(x + 15, y + 30, head, size=19, color=color, weight="bold")
        f.text(x + 15, y + 61, detail, size=18, color=INK)
    f.arrow(310, 350, 310, 369, color=BLUE_D, bend=0, head=8)
    f.arrow(310, 468, 310, 487, color=BLUE_D, bend=0, head=8)
    f.arrow(842, 364, 842, 385, color=GREEN_D, bend=0, head=8)
    f.arrow(542, 410, 610, 410, color=RED, bend=0, head=10)
    f.text(638, 536, "嵌套返回后，继续原 ISR；", size=20, color=INK)
    f.text(638, 567, "异常返回再恢复任务上下文。", size=20, color=INK)
    f.text(106, 623, "任务水位主要检查这里；异常帧也要留余量。", size=18, color=BLUE_D)
    f.text(638, 623, "MSP 单独留预算；任务水位不能代表它。", size=18, color=GREEN_D)
    f.htext(576, 696, "任务栈和 MSP 都要够，不能只盯住一个水位", size=24,
            color=INK, weight="bold", anchor="middle", hl=True)
    f.text(84, 744, "未画地址和容量比例；8 个寄存器 = 32 B，另留对齐余量。M3 无浮点扩展帧。",
           size=18, color=MUTED)
    return f


def task_states():
    f = Fig("ch15-task-states", "Ready 已经能跑，只差 CPU")
    f.text(84, 138, "单核抢占式调度；等待事件与显式挂起要分清", size=22, color=MUTED)
    f.stroke([(1068, 554), (1094, 554), (1094, 202), (284, 202), (284, 236)],
             color=AMBER_STROKE, sw=2.4, amp=0.5)
    f.arrow(284, 222, 284, 236, color=AMBER_STROKE, head=9, bend=0)
    f.text(690, 187, "事件到达 / 超时：Blocked → Ready", size=20,
           color=AMBER_STROKE, anchor="middle")
    for x, y, title, detail, color in (
        (84, 242, "就绪 Ready", "具备运行条件，等待 CPU", BLUE_D),
        (668, 242, "运行 Running", "当前占用 CPU 的任务", GREEN_D),
        (84, 490, "挂起 Suspended", "显式暂停；不因超时自动恢复", MUTED),
        (668, 490, "阻塞 Blocked", "等待队列、信号量或延时到期", AMBER_STROKE),
    ):
        f.rect(x, y, 400, 128, color=color, fill=WHITE)
        f.text(x + 200, y + 48, title, size=28, color=color,
               anchor="middle", weight="bold")
        f.text(x + 200, y + 89, detail, size=22, color=INK, anchor="middle")
    f.arrow(490, 279, 662, 279, color=BLUE_D, head=10, bend=0)
    f.text(576, 264, "被选中", size=21, color=BLUE_D, anchor="middle")
    f.arrow(662, 325, 490, 325, color=GREEN_D, head=10, bend=0)
    f.text(576, 358, "被抢占 / 轮转", size=20, color=GREEN_D, anchor="middle")
    f.arrow(184, 376, 184, 484, color=MUTED, head=10, bend=0)
    f.text(170, 432, "挂起", size=21, color=MUTED, anchor="end")
    f.arrow(384, 484, 384, 376, color=BLUE_D, head=10, bend=0)
    f.text(398, 432, "恢复", size=21, color=BLUE_D)
    f.arrow(868, 376, 868, 484, color=AMBER_STROKE, head=10, bend=0)
    f.text(892, 420, "等待事件", size=21, color=AMBER_STROKE)
    f.text(892, 450, "或延时", size=21, color=AMBER_STROKE)
    f.htext(576, 680, "事件唤醒可以发生在两个 tick 之间", size=27,
            color=INK, weight="bold", hl=True, anchor="middle")
    f.text(576, 726, "图中省略删除状态及其他 API 路径；挂起箭头以 Ready 为例。",
           size=20, color=MUTED, anchor="middle")
    return f


def stack_watermark():
    f = Fig("ch15-stack-watermark", "栈往下长：水位量余量，钩子抓现场")
    f.text(84, 140, "STM32F103 · Cortex-M3 · 任务栈用 PSP 向下增长 · 1 字 = 4 B · ISR 与嵌套用 MSP，两边分别留余量",
           size=20, color=MUTED)

    # ---- 左：一列栈，向下增长，水位线记历史最深 ----
    f.rect(84, 170, 460, 380, color=BLUE_D, fill=WHITE)
    f.text(104, 202, "LED 任务的栈：128 字 = 512 B", size=22, color=BLUE_D,
           weight="bold")
    f.text(160, 240, "栈顶 · 高地址（初始 SP）", size=17, color=MUTED)
    f.fillrect(162, 252, 116, 104, AMBER_FILL)          # 已用（历史最深）
    f.fillrect(162, 356, 116, 132, GRAY_FILL)           # 空闲（剩余）
    f.rect(160, 250, 120, 240, color=BLUE_D, sw=2.6)
    f.line(160, 356, 280, 356, color=RED, sw=2.4, dash="6 5")
    f.line(280, 356, 340, 356, color=RED, sw=1.6, dash="4 5", opacity=0.7)
    f.text(348, 362, "水位线：历史最深", size=18, color=RED, weight="bold")
    f.text(220, 314, "已用（最深时）", size=17, color=INK, anchor="middle")
    f.text(220, 428, "空闲（剩余）", size=17, color=INK, anchor="middle")
    f.text(140, 512, "栈底 · 低地址", size=17, color=MUTED)
    f.text(104, 534, "水位接近 0 就要加大；示意未按地址与容量比例绘制",
           size=17, color=MUTED)

    # ---- 右：穿到底会发生什么 ----
    f.rect(608, 170, 460, 380, color=RED, fill=WHITE)
    f.text(628, 202, "一旦穿到底，会发生什么", size=22, color=RED,
           weight="bold")
    f.rect(628, 236, 420, 64, color=RED, fill=WHITE, sw=2.2)
    f.text(644, 262, "栈太小：一路写到栈底以下", size=20, color=INK)
    f.text(644, 288, "下面就是别的任务或堆的地盘", size=18, color=MUTED)
    f.arrow(838, 306, 838, 340, color=RED, bend=0, head=9)
    f.rect(628, 348, 420, 64, color=RED, fill=PAPER, sw=2.2)
    f.text(644, 374, "表现：随机 HardFault", size=20, color=RED, weight="bold")
    f.text(644, 400, "现场不像栈问题，最难查", size=18, color=INK)
    f.rect(628, 436, 420, 94, color=AMBER_STROKE, fill=WHITE, sw=2.2)
    f.text(644, 466, "单位给错，容量只剩 1/4", size=20, color=AMBER_STROKE,
           weight="bold")
    f.text(644, 492, "把 128 字误当 128 字节 → 只分 32 字", size=18, color=INK)
    f.text(644, 516, "含 printf / 浮点：256~512 字起步", size=18, color=MUTED)

    # ---- 底：两个抓手 ----
    f.rect(84, 592, 476, 118, color=GREEN_D, fill=WHITE, sw=2.4)
    f.text(100, 624, "抓手一 · 运行期量水位", size=21, color=GREEN_D,
           weight="bold")
    f.multi(100, 656, ["uxTaskGetStackHighWaterMark()：",
                       "返回剩余最小空闲字数，接近 0 就要加大"],
            size=18, color=INK, lh=26)
    f.rect(592, 592, 476, 128, color=RED, fill=WHITE, sw=2.4)
    f.text(608, 622, "抓手二 · 出错抓现场", size=21, color=RED, weight="bold")
    f.multi(608, 654, ["configCHECK_FOR_STACK_OVERFLOW = 2",
                       "+ vApplicationStackOverflowHook()：断点里",
                       "看是哪个任务溢出"],
            size=18, color=INK, lh=26)
    f.htext(576, 748, "栈按字给；水位管平时，钩子抓现场", size=24,
            color=INK, weight="bold", anchor="middle", hl=True)
    return f


FIGS = {
    "ch15-prio-inherit": prio_inherit,
    "ch15-psp-msp": psp_msp,
    "ch15-task-states": task_states,
    "ch15-stack-watermark": stack_watermark,
}

if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        f = FIGS[n]()
        OUT.mkdir(parents=True, exist_ok=True)
        save(f, str(OUT / (n + ".svg")))
        print("wrote", OUT / (n + ".svg"))

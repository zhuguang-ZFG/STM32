# -*- coding: utf-8 -*-
"""Six deterministic chapter 17 knowledge plates.

F103 pin/FPB facts follow the chapter's RM0008 / DS5319 / PM0056 sources.
Fault semantics were checked against ARM DUI0552A pp.4-24..4-31.
No plate claims to be a measurement.
"""
from hd import *


def bp_comparators():
    f = Fig("ch17-bp-comparators", "断点打不上，先数 FPB 比较器")
    f.text(72, 145, "STM32F103 · 6 个指令地址比较器", size=25, color=BLUE_D, weight="bold")
    f.text(72, 179, "FPB 按取指地址匹配硬件代码断点", size=22, color=MUTED)
    f.line(296, 211, 296, 578, color=BLUE_D, sw=2.5)
    f.text(94, 235, "取指地址", size=26, color=INK, weight="bold")
    f.text(123, 272, "PC", size=30, color=BLUE_D, weight="bold")
    f.arrow(204, 261, 288, 261, color=BLUE_D, bend=0)
    f.line(668, 231, 668, 578, color=GREEN_D, sw=2.5)
    for i in range(6):
        y = 222 + i * 62
        f.line(296, y + 23, 338, y + 23, color=BLUE_D, sw=2)
        f.rect(338, y, 292, 46, color=BLUE_D, fill=WHITE, sw=2, double=False)
        f.text(484, y + 31, f"FP_COMP{i}", size=24, color=BLUE_D, anchor="middle")
        f.line(630, y + 23, 668, y + 23, color=GREEN_D, sw=2)
    f.text(730, 232, "任一地址匹配", size=25, color=GREEN_D, weight="bold")
    f.arrow(678, 291, 742, 291, color=GREEN_D, bend=0)
    f.rect(750, 259, 310, 93, color=GREEN_D, fill=WHITE)
    f.text(905, 297, "内核暂停", size=30, color=GREEN_D, weight="bold", anchor="middle")
    f.text(905, 332, "调试器读取现场", size=22, color=INK, anchor="middle")
    f.rect(750, 397, 310, 170, color=RED, fill=WHITE)
    f.text(772, 437, "第 7 个硬件代码断点", size=23, color=RED, weight="bold")
    f.multi(772, 479, ["六个都占用：无法再分配", "删掉旧断点，再试一次", "条件断点仍占比较器"], size=21, color=INK, lh=33)
    f.line(72, 622, 1080, 622, color=MUTED, sw=1.3)
    f.text(72, 667, "另有 2 个 literal 比较器，不增加代码断点名额。", size=23, color=INK)
    f.text(72, 710, "M7 通常有 8 个；换芯片仍要查 FPB 实现与调试器支持。", size=22, color=MUTED)
    return f


def cfsr():
    f = Fig("ch17-cfsr", "先保存现场，再判断地址是否有效")
    f.text(72, 144, "先保存 BFAR / MMFAR 与故障状态；以下解读同一份快照。", size=23, color=INK)
    f.rect(284, 177, 584, 88, color=BLUE_D, fill=WHITE)
    f.text(576, 213, "CFSR · 0xE000ED28", size=28, color=BLUE_D, anchor="middle", weight="bold")
    f.text(576, 247, "BFARVALID = bit 15", size=23, color=INK, anchor="middle")
    f.arrow(444, 273, 306, 324, color=GREEN_D, bend=0)
    f.arrow(708, 273, 846, 324, color=RED, bend=0)
    f.text(327, 301, "1", size=25, color=GREEN_D, weight="bold")
    f.text(812, 301, "0", size=25, color=RED, weight="bold")
    f.rect(72, 334, 480, 142, color=GREEN_D, fill=WHITE)
    f.rect(600, 334, 480, 142, color=RED, fill=WHITE)
    f.text(96, 373, "BFAR 保存了有效故障地址", size=25, color=GREEN_D, weight="bold")
    f.text(96, 414, "地址寄存器：0xE000ED38", size=23, color=INK)
    f.text(96, 452, "仍须结合 CFSR 故障类型判读", size=22, color=MUTED)
    f.text(624, 373, "BFAR 不能用于定位这次故障", size=25, color=RED, weight="bold")
    f.text(624, 414, "有数值，不等于有有效地址", size=23, color=INK)
    f.text(624, 452, "继续查故障类型与可用栈帧", size=22, color=MUTED)
    f.text(72, 518, "HFSR bit 30（FORCED）= 1：有故障升级；原因继续查 CFSR。", size=22, color=INK)
    f.line(72, 551, 1080, 551, color=MUTED, sw=1.3)
    f.text(72, 593, "周期计数是另一个实验", size=26, color=BLUE_D, weight="bold")
    f.text(72, 631, "DEMCR bit 24 = 1", size=23, color=INK)
    f.arrow(378, 624, 435, 624, color=BLUE_D, bend=0)
    f.text(458, 631, "DWT CTRL bit 0 = 1", size=23, color=INK)
    f.text(72, 676, "DWT_CYCCNT · 0xE0001004", size=22, color=MUTED)
    f.htext(1080, 686, "72 计数 / 72 MHz = 1 µs", size=29, color=GREEN_D, anchor="end", weight="bold", hl=True)
    f.text(72, 737, "IMPRECISERR 不更新 BFAR；栈中 PC 也未必指向最初出错的写指令。", size=22, color=MUTED)
    return f


def swd_pins():
    f = Fig("ch17-swd-pins", "探针到 F103，先把这几根线接清楚")
    f.text(72, 143, "信号名对应 MCU 引脚；连接器脚序以实际探针和板卡为准。", size=23, color=MUTED)
    f.rect(72, 186, 270, 441, color=BLUE_D, fill=WHITE)
    f.rect(792, 186, 288, 441, color=GREEN_D, fill=WHITE)
    f.text(207, 224, "调试探针", size=28, color=BLUE_D, weight="bold", anchor="middle")
    f.text(936, 224, "STM32F103", size=28, color=GREEN_D, weight="bold", anchor="middle")
    rows = [
        (274, "GND", "GND", "共同电位参考", MUTED, "wire"),
        (337, "VTref", "目标 VDD", "探针感知目标电平", MUTED, "back"),
        (400, "SWDIO", "PA13 · SWDIO", "双向数据", BLUE_D, "both"),
        (463, "SWCLK", "PA14 · SWCLK", "时钟由探针提供", BLUE_D, "forward"),
        (526, "NRST", "NRST", "连接复位，便于恢复", GREEN_D, "forward"),
        (589, "SWO 输入", "PB3 · TRACESWO", "跟踪数据返回探针", AMBER_STROKE, "back"),
    ]
    for y, probe, target, note, color, direction in rows:
        f.text(94, y + 8, probe, size=25, color=color, weight="bold")
        f.text(812, y + 8, target, size=22, color=color, weight="bold")
        f.text(567, y - 13, note, size=20, color=MUTED, anchor="middle")
        f.line(344, y + 7, 788, y + 7, color=color, sw=2.4)
        if direction in ("both", "forward"):
            f.arrowhead(785, y + 7, 1, 0, color=color, head=10)
        if direction in ("both", "back"):
            f.arrowhead(348, y + 7, -1, 0, color=color, head=10)
    f.text(72, 677, "VTref 是电平参考，不等于探针给板卡供电；供电能力要查探针。", size=22, color=INK)
    f.text(72, 719, "PB3 复位后为 JTDO；输出 SWO 还需配置跟踪功能与探针接收。", size=22, color=MUTED)
    return f


def obs_compare():
    f = Fig("ch17-obs-compare", "想看哪种现场，就选哪种观测方式")
    f.text(72, 144, "它们回答的问题不同，开销也不同。", size=23, color=MUTED)
    for y in (181, 367, 553, 739):
        f.line(72, y, 1080, y, color=MUTED, sw=1.2)
    f.text(72, 228, "断点", size=31, color=BLUE_D, weight="bold")
    f.text(72, 268, "停下来读", size=22, color=MUTED)
    f.arrow(276, 250, 564, 250, color=BLUE_D, bend=0)
    f.line(564, 219, 564, 280, color=RED, sw=4)
    f.text(420, 311, "运行 → 命中 → 暂停", size=22, color=BLUE_D, anchor="middle")
    f.text(680, 224, "此刻的 PC / 变量 / 寄存器", size=24, color=INK, weight="bold")
    f.multi(680, 268, ["会改变实时行为", "硬件代码断点受比较器数量限制"], size=21, color=MUTED, lh=33)
    f.text(72, 414, "SWO / ITM", size=28, color=GREEN_D, weight="bold")
    f.text(72, 454, "边跑边看", size=22, color=MUTED)
    f.line(276, 436, 600, 436, color=GREEN_D, sw=2)
    for x in (294, 382, 470):
        f.rect(x, 421, 56, 30, color=GREEN_D, fill=WHITE, sw=2, double=False)
    f.arrowhead(598, 436, 1, 0, color=GREEN_D)
    f.text(438, 497, "PB3 → 探针 → 主机", size=22, color=GREEN_D, anchor="middle")
    f.text(680, 410, "事件顺序与运行中的输出", size=24, color=INK, weight="bold")
    f.multi(680, 454, ["需要跟踪配置、接收端与带宽", "调用、阻塞和丢包都要评估"], size=21, color=MUTED, lh=33)
    f.text(72, 600, "故障记录", size=30, color=RED, weight="bold")
    f.text(72, 640, "留住证据", size=22, color=MUTED)
    f.text(287, 623, "异常入口", size=22, color=RED)
    f.arrow(406, 615, 454, 615, color=RED, bend=0)
    f.rect(462, 579, 150, 77, color=RED, fill=WHITE)
    f.text(537, 625, "保存快照", size=24, color=RED, anchor="middle")
    f.text(438, 683, "先记录，再决定如何恢复", size=21, color=MUTED, anchor="middle")
    f.text(680, 596, "CFSR / HFSR / PC 与有效位", size=23, color=INK, weight="bold")
    f.multi(680, 640, ["异常处理里保持记录操作简短", "复位后能否保留取决于存储策略"], size=21, color=MUTED, lh=33)
    return f


def cfsr_bits():
    f = Fig("ch17-cfsr-bits", "CFSR：先分区，再按置位标志查原因")
    f.text(72, 144, "CFSR · 0xE000ED28 · 以下位号均相对整个 32 位 CFSR", size=23, color=MUTED)
    partitions = [(72, 504, "UFSR", "[31:16] · UsageFault", BLUE_D),
                  (576, 252, "BFSR", "[15:8] · BusFault", RED),
                  (828, 252, "MMFSR", "[7:0] · MemManage", GREEN_D)]
    for x, w, name, bits, color in partitions:
        f.rect(x, 180, w, 89, color=color, fill=WHITE, sw=2.5, double=False)
        f.text(x + w / 2, 216, name, size=29, color=color, anchor="middle", weight="bold")
        f.text(x + w / 2, 249, bits, size=20, color=INK, anchor="middle")
    f.text(72, 317, "BFSR 展开", size=25, color=RED, weight="bold")
    labels = [(15, "有效位", GREEN_D), (14, "保留", MUTED), (13, "保留", MUTED),
              (12, "入栈", RED), (11, "出栈", RED), (10, "非精确", AMBER_STROKE),
              (9, "精确", BLUE_D), (8, "取指", BLUE_D)]
    for i, (bit, label, color) in enumerate(labels):
        x = 72 + i * 126
        f.rect(x, 340, 126, 89, color=color, fill=WHITE, sw=2, double=False)
        f.text(x + 63, 374, str(bit), size=28, color=color, anchor="middle", weight="bold")
        f.text(x + 63, 410, label, size=22, color=color, anchor="middle")
    rows = [
        (480, GREEN_D, "bit 15 · BFARVALID", "BFAR 内的故障地址有效；仍须查故障类型与栈帧。"),
        (539, BLUE_D, "bit 9 · PRECISERR", "精确数据总线错误：有效栈帧中的 PC 指向故障指令。"),
        (598, AMBER_STROKE, "bit 10 · IMPRECISERR", "非精确错误不更新 BFAR；栈 PC 不指向原始故障写。"),
        (657, RED, "bit 12 / bit 4", "STKERR / MSTKERR：入栈出错，栈帧可能不完整。"),
    ]
    for y, color, name, desc in rows:
        f.circle(82, y - 8, 5, color=color, fill=color)
        f.text(103, y, name, size=23, color=color, weight="bold")
        f.text(420, y, desc, size=21, color=INK)
    f.text(72, 724, "多个标志可同时置位；精确与非精确故障也可能同时被记录。", size=23, color=MUTED)
    return f


def perf_triage():
    f = Fig("ch17-perf-triage", "先把 DWT 测量窗口夹准确")
    f.text(72, 143, "使能跟踪 + 使能周期计数，缺一项都先修配置。", size=24, color=INK)
    f.rect(72, 178, 478, 91, color=BLUE_D, fill=WHITE)
    f.rect(602, 178, 478, 91, color=BLUE_D, fill=WHITE)
    f.text(311, 214, "DEMCR.TRCENA = 1", size=26, color=BLUE_D, anchor="middle", weight="bold")
    f.text(311, 249, "0xE000EDFC · bit 24", size=22, color=MUTED, anchor="middle")
    f.text(841, 214, "DWT.CTRL.CYCCNTENA = 1", size=25, color=BLUE_D, anchor="middle", weight="bold")
    f.text(841, 249, "DWT_CTRL · bit 0", size=22, color=MUTED, anchor="middle")
    f.text(72, 320, "t₀ = CYCCNT", size=25, color=BLUE_D, weight="bold")
    f.text(1080, 320, "t₁ = CYCCNT", size=25, color=BLUE_D, weight="bold", anchor="end")
    f.line(224, 362, 928, 362, color=BLUE_D, sw=3)
    f.line(224, 337, 224, 388, color=BLUE_D, sw=3)
    f.line(928, 337, 928, 388, color=BLUE_D, sw=3)
    f.rect(326, 332, 500, 61, color=GREEN_D, fill=WHITE)
    f.text(576, 373, "同一份输入 · 被测代码", size=27, color=GREEN_D, anchor="middle", weight="bold")
    f.text(576, 436, "Δcycles = (uint32_t)(t₁ − t₀)", size=29, color=BLUE_D, anchor="middle")
    f.htext(576, 493, "72 cycles / 72 MHz = 1 µs", size=32, color=GREEN_D, anchor="middle", weight="bold", hl=True)
    f.line(72, 534, 1080, 534, color=MUTED, sw=1.3)
    checks = [
        (584, "读数为 0", "查两个使能位、计数器是否递增，以及代码是否被优化掉。", RED),
        (640, "读数在变", "重复采样；记录中断影响，并用空窗口估计读数开销。", BLUE_D),
        (696, "比较优化级别", "固定时钟、输入和功能校验，再比周期数与代码大小。", GREEN_D),
    ]
    for y, title, note, color in checks:
        f.text(72, y, title, size=25, color=color, weight="bold")
        f.text(305, y, note, size=23, color=INK)
    f.text(72, 750, "时间换算使用运行时内核频率；改了时钟，就要重新换算。", size=22, color=MUTED)
    return f


def dwt_window():
    f = Fig("ch17-dwt-window", "计时窗口里，不只有被测代码")
    f.text(72, 142, "t₀、t₁ 两次读取之间发生的一切，都计入 Δcycles。", size=23, color=MUTED)

    # ---- 上：Δ 的构成 ----
    f.text(170, 214, "t₀ = CYCCNT", size=22, color=BLUE_D, weight="bold", anchor="middle")
    f.text(1010, 214, "t₁ = CYCCNT", size=22, color=BLUE_D, weight="bold", anchor="middle")
    f.line(170, 261, 1010, 261, color=BLUE_D, sw=3)
    f.line(170, 236, 170, 286, color=BLUE_D, sw=3)
    f.line(1010, 236, 1010, 286, color=BLUE_D, sw=3)
    f.rect(196, 233, 158, 56, color=AMBER_STROKE, fill=WHITE, sw=2.2, double=False)
    f.text(275, 269, "读 t₀ 开销", size=21, color=AMBER_STROKE, anchor="middle", weight="bold")
    f.rect(378, 233, 428, 56, color=GREEN_D, fill=WHITE, sw=2.6)
    f.text(592, 269, "被测代码 · 只关心这一段", size=22, color=GREEN_D, anchor="middle", weight="bold")
    f.rect(830, 233, 158, 56, color=AMBER_STROKE, fill=WHITE, sw=2.2, double=False)
    f.text(909, 269, "读 t₁ 开销", size=21, color=AMBER_STROKE, anchor="middle", weight="bold")
    f.line(170, 312, 1010, 312, color=BLUE_D, sw=2.4)
    f.line(170, 300, 170, 324, color=BLUE_D, sw=2.4)
    f.line(1010, 300, 1010, 324, color=BLUE_D, sw=2.4)
    f.text(576, 354, "Δcycles = t₁ − t₀ = 固定开销 + 被测代码（+ 窗口内的中断）",
           size=23, color=BLUE_D, anchor="middle", weight="bold")

    # ---- 中：三个可能混进窗口的东西 ----
    cards = [
        (72, "固定开销", BLUE_D,
         ["两次读取与地址计算；", "空窗口也能测出非零值。"]),
        (408, "被测代码", GREEN_D,
         ["被优化掉，Δ 只剩开销；", "反汇编确认循环还在窗口内。"]),
        (744, "窗口内中断", RED,
         ["ISR 插进来，Δ 变长；", "重复测量，写明中断条件。"]),
    ]
    for x, head, color, lines in cards:
        f.rect(x, 392, 312, 150, color=color, fill=WHITE, sw=2.4)
        f.text(x + 22, 428, head, size=24, color=color, weight="bold")
        f.multi(x + 22, 470, lines, size=19, color=INK, lh=32)

    # ---- 下：让差值可引用的三件事 ----
    f.line(72, 572, 1080, 572, color=MUTED, sw=1.3)
    f.text(72, 608, "让 Δ 能被引用，先做三件事", size=26, color=BLUE_D, weight="bold")
    rules = [
        (648, "基线", "先测一次空窗口，再解释差值。"),
        (686, "代码在不在", "反汇编里找到被测循环。"),
        (724, "同条件", "主频、输入、优化级别固定，再用运行频率换算 µs。"),
    ]
    for y, name, note in rules:
        f.text(72, y, name, size=23, color=GREEN_D, weight="bold")
        f.text(232, y, note, size=23, color=INK)
    f.htext(72, 760, "两次读取之间发生的一切，都属于这次测量。", size=23,
            color=RED, weight="bold", hl=True)
    return f


def swo_path():
    f = Fig("ch17-swo-path", "printf 上 SWO：一条链，三个参数")
    f.text(72, 138, "代码只把字符写进 ITM；字符能不能到主机，取决于后面的链路与配置。", size=22, color=MUTED)

    # ---- 上：字符路径 ----
    stages = [
        (72, "printf", "字符重定向", BLUE_D),
        (276, "ITM", "端口 0", BLUE_D),
        (480, "TPIU", "跟踪输出", BLUE_D),
        (684, "PB3", "TRACESWO", AMBER_STROKE),
        (888, "探针 · IDE", "Serial Wire", GREEN_D),
    ]
    for x, head, sub, color in stages:
        f.rect(x, 186, 176, 78, color=color, fill=WHITE, sw=2.4)
        f.text(x + 88, 222, head, size=20, color=color, anchor="middle", weight="bold")
        f.text(x + 88, 250, sub, size=17, color=INK, anchor="middle")
    for x in (248, 452, 656, 860):
        f.arrow(x, 225, x + 28, 225, color=BLUE_D, bend=0)
    f.text(72, 302, "SWO 走 PB3 的 TRACESWO，不占 USART；这段代码只负责写 ITM 端口 0。", size=21, color=MUTED)
    f.line(72, 330, 1080, 330, color=MUTED, sw=1.3)

    # ---- 中：三个独立参数 ----
    f.text(72, 366, "三个参数，缺一个就看不到字符", size=25, color=BLUE_D, weight="bold")
    cards = [
        (72, "内核时钟", BLUE_D,
         ["IDE 里填的内核频率", "要与实际 HCLK 一致。"]),
        (408, "SWO 线速", AMBER_STROKE,
         ["探针与 IDE 的速率", "要和跟踪输出匹配；", "不匹配就是乱码或无数据。"]),
        (744, "链路使能", GREEN_D,
         ["DBGMCU、ITM、TPIU", "和探针的 Serial Wire", "模式都要打开。"]),
    ]
    for x, head, color, lines in cards:
        f.rect(x, 392, 312, 150, color=color, fill=WHITE, sw=2.4)
        f.text(x + 22, 428, head, size=24, color=color, weight="bold")
        f.multi(x + 22, 470, lines, size=19, color=INK, lh=30)

    # ---- 下：看不到字符时的排查顺序 ----
    f.line(72, 572, 1080, 572, color=MUTED, sw=1.3)
    f.text(72, 608, "看不到字符时，按顺序查", size=26, color=BLUE_D, weight="bold")
    steps = [
        (72, "① 探针", "Serial Wire + 跟踪", BLUE_D),
        (350, "② ITM / TPIU", "使能", BLUE_D),
        (628, "③ 时钟与线速", "两处一致", AMBER_STROKE),
    ]
    for x, head, sub, color in steps:
        f.rect(x, 630, 230, 76, color=color, fill=WHITE, sw=2.4)
        f.text(x + 115, 664, head, size=20, color=color, anchor="middle", weight="bold")
        f.text(x + 115, 692, sub, size=18, color=INK, anchor="middle")
    for x in (306, 584):
        f.arrow(x, 668, x + 38, 668, color=INK, bend=0)
    f.arrow(862, 668, 898, 668, color=GREEN_D, bend=0)
    f.rect(902, 630, 178, 76, color=GREEN_D, fill=WHITE, sw=2.6)
    f.text(991, 664, "主机有字符", size=20, color=GREEN_D, anchor="middle", weight="bold")
    f.text(991, 692, "才算通了", size=18, color=INK, anchor="middle")
    f.htext(72, 756, "改 printf 之前，先把链路和三个参数对齐。", size=23,
            color=RED, weight="bold", hl=True)
    return f


def halt_timing():
    f = Fig("ch17-halt-timing", "断点 / 单步：停一下，时序就变一次")
    f.text(72, 128, "命中 → 内核暂停 → 主机读现场；读的是此刻的 PC / 变量 / 寄存器。", size=22, color=MUTED)

    # ---- 上：同一程序的两种时间线 ----
    f.text(72, 174, "连续运行", size=25, color=GREEN_D, weight="bold")
    f.text(216, 174, "计时区间内保持内核连续运行", size=21, color=INK)
    f.fillrect(420, 194, 400, 40, GRAY_FILL, r=4)
    f.line(150, 214, 1010, 214, color=GREEN_D, sw=3)
    for x in (220, 320, 420, 520, 620, 720, 820, 920):
        f.circle(x, 214, 6, color=GREEN_D, fill=WHITE, sw=2)
    f.text(620, 262, "浅色一段是计时窗口：里面没有人打扰，读数才属于这段代码", size=18, color=MUTED, anchor="middle")

    f.text(72, 302, "命中断点", size=25, color=RED, weight="bold")
    f.line(150, 342, 462, 342, color=BLUE_D, sw=3)
    for x in (220, 320, 420):
        f.circle(x, 342, 6, color=BLUE_D, fill=WHITE, sw=2)
    f.stroke([(452, 330), (482, 354)], color=RED, sw=3.6, amp=0.8)
    f.stroke([(452, 354), (482, 330)], color=RED, sw=3.6, amp=0.8)
    f.text(467, 314, "命中", size=19, color=RED, anchor="middle", weight="bold")
    f.rect(500, 314, 240, 56, color=RED, fill=WHITE)
    f.text(620, 349, "内核暂停 · 调试器读现场", size=19, color=RED, anchor="middle", weight="bold")
    f.line(756, 342, 1010, 342, color=BLUE_D, sw=3)
    for x in (770, 870, 970):
        f.circle(x, 342, 6, color=BLUE_D, fill=WHITE, sw=2)
    f.htext(620, 396, "恢复后程序继续，但节奏里多了一段停顿：扰动时序", size=20, color=RED, anchor="middle", weight="bold", hl=True)

    f.line(72, 432, 1080, 432, color=MUTED, sw=1.3)

    # ---- 左下：条件断点的判断链 ----
    f.text(72, 466, "条件断点：判断发生在暂停之后", size=25, color=BLUE_D, weight="bold")
    f.rect(72, 486, 250, 50, color=BLUE_D, fill=WHITE)
    f.text(197, 518, "FPB 比较指令地址", size=21, color=BLUE_D, anchor="middle", weight="bold")
    f.arrow(197, 540, 197, 562, color=INK, bend=0)
    f.rect(72, 566, 250, 50, color=RED, fill=WHITE)
    f.text(197, 598, "内核暂停", size=22, color=RED, anchor="middle", weight="bold")
    f.arrow(197, 620, 197, 642, color=INK, bend=0)
    f.rect(72, 646, 250, 50, color=AMBER_STROKE, fill=WHITE)
    f.text(197, 678, "主机判断条件", size=21, color=AMBER_STROKE, anchor="middle", weight="bold")
    f.arrow(326, 658, 392, 646, color=GREEN_D, bend=0)
    f.arrow(326, 674, 392, 708, color=BLUE_D, bend=0)
    f.rect(400, 624, 168, 44, color=GREEN_D, fill=WHITE, double=False)
    f.text(484, 653, "满足：停住读", size=19, color=GREEN_D, anchor="middle", weight="bold")
    f.rect(400, 688, 168, 44, color=BLUE_D, fill=WHITE, double=False)
    f.text(484, 717, "不满足：继续", size=19, color=BLUE_D, anchor="middle", weight="bold")
    f.text(72, 762, "条件硬件断点仍占 1 个比较器", size=20, color=INK)

    # ---- 右下：DWT 窗口最怕中途停 ----
    f.text(620, 470, "DWT 窗口：要求连续运行", size=25, color=GREEN_D, weight="bold")
    f.text(680, 500, "t0", size=19, color=BLUE_D)
    f.line(680, 510, 680, 566, color=BLUE_D, sw=1.6, dash="5 5")
    f.text(1020, 500, "t1", size=19, color=BLUE_D, anchor="end")
    f.line(1020, 510, 1020, 566, color=BLUE_D, sw=1.6, dash="5 5")
    f.rect(724, 524, 252, 50, color=GREEN_D, fill=WHITE)
    f.text(850, 556, "被测代码", size=23, color=GREEN_D, anchor="middle", weight="bold")
    f.circle(770, 614, 16, color=RED, fill=WHITE, sw=2.6)
    f.line(759, 625, 781, 603, color=RED, sw=2.6, amp=0.8)
    f.circle(770, 614, 5, color=RED, fill=RED)
    f.text(800, 621, "断点 / 单步都让内核停下来", size=21, color=RED, weight="bold")
    f.multi(620, 676, ["DWT 读数为 0 时，先查是否在单步；", "空窗口也包含读计数器的开销。"], size=20, color=INK, lh=38)
    return f


FIGS = {
    "ch17-bp-comparators": bp_comparators,
    "ch17-cfsr": cfsr,
    "ch17-swd-pins": swd_pins,
    "ch17-obs-compare": obs_compare,
    "ch17-cfsr-bits": cfsr_bits,
    "ch17-perf-triage": perf_triage,
    "ch17-halt-timing": halt_timing,
    "ch17-dwt-window": dwt_window,
    "ch17-swo-path": swo_path,
}

if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        f = FIGS[n]()
        OUT.mkdir(parents=True, exist_ok=True)
        save(f, str(OUT / (n + ".svg")))
        print("wrote", OUT / (n + ".svg"))

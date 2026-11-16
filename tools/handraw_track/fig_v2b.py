# -*- coding: utf-8 -*-
"""Hand-drawn plates for V2b (ch21 stack word ruler, ch24 queue contracts).

Facts pinned to the chapter sheets, no new measurements:
ch21 -- StackType_t = 4 B word; F103 LED/KEY/UART 128/192/256 words =
512/768/1024 B, sum 2304 B, heap 10240 B; F407 256/256/320 words =
1024/1024/1280 B, sum 3328 B, heap 16384 B; configMINIMAL_STACK_SIZE =
128 words = 512 B; failure errCOULD_NOT_ALLOCATE_REQUIRED_MEMORY (-1),
NOT pdFAIL(0); success pdPASS(1); test != pdPASS; TCB pxTopOfStack first
member; uxTaskGetStackHighWaterMark; overflow check 2 fills 0xA5;
Sigma WCET <= min(T) is 教学算术; host timings 来源说法(未复核).
ch24 -- one QueueDefinition; uxQueueType is #define pcHead (queue.c:65);
queueQUEUE_IS_MUTEX NULL (queue.c:66); discriminators uxItemSize>0 /
pcHead==NULL / uxMessagesWaiting; queue depth 10 item 16 B -> uxLength=10,
uxItemSize=16, data 160 B; ring depth 5 item 16 B: pcHead=0x2000_1000,
pcTail=0x2000_1050; binary 1/0; counting max/initial; mutex 1/1 +
xMutexHolder + uxRecursiveCallCount; semGIVE_BLOCK_TIME=0; FromISR
threshold 5<<(8-4)=0x50; wait list xItemValue=configMAX_PRIORITIES-
uxPriority; RAM 160+80+8=248 B (文档推导).

Deterministic: hd.Fig seeds its own RNG; re-running gives the same SVG.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hd import (AMBER_FILL, AMBER_PALE, AMBER_STROKE, BLUE_D,  # noqa: E402
                BLUE_FILL, GRAY_FILL, GREEN_D, GREEN_FILL, INK, MUTED, RED,
                RED_FILL, WHITE, Fig, save)

MONO = "'Consolas','Courier New',monospace"
STAGE = Path(__file__).resolve().parents[2] / ".temp" / "l0-l5-pass" / "figures"


def ch21_stack_word_ruler():
    f = Fig("ch21-stack-word-ruler", "栈的尺子：word ≠ byte",
            title_color=AMBER_STROKE, tag="CH 21 · FreeRTOS 任务与栈")
    f.text(64, 126,
           "StackType_t = 4 B word：额度按 word 计，读成 byte 箱子就小 4 倍。",
           size=19, color=MUTED)

    # (a) Baggage-allowance ruler: the scale reads words, not bytes.
    f.card(54, 150, 330, 290, AMBER_STROKE, fill=AMBER_PALE)
    f.text(74, 184, "行李额度尺", size=21, color=AMBER_STROKE, weight="bold")
    f.text(74, 212, "刻度单位 = word = 4 B", size=16, color=INK,
           weight="bold")
    f.rect(74, 228, 290, 36, color=AMBER_STROKE, sw=2.2, fill=WHITE,
           double=False)
    for i in range(9):
        tx = 74 + i * 36.25
        ln = 16 if i % 4 == 0 else 9
        f.line(tx, 228, tx, 228 + ln, color=AMBER_STROKE, sw=1.6, amp=0.2)
    f.text(74, 282, "0", size=14, color=MUTED, anchor="middle")
    f.text(364, 282, "128 words", size=14, color=MUTED, anchor="end")
    f.text(74, 318, "128 words = 512 B", size=24, color=AMBER_STROKE,
           weight="bold")
    f.stamp(219, 388, "读成 128 B = 只剩 1/4", size=16)

    # (b) Two baggage tags: same word ruler, different allowances.
    f.card(404, 150, 330, 290, BLUE_D, fill=BLUE_FILL)
    f.text(424, 184, "F103 行李牌", size=21, color=BLUE_D, weight="bold")
    f.chip(656, 166, 44, 40, BLUE_D)
    f.text(424, 224, "LED 128 words = 512 B", size=17, color=INK)
    f.text(424, 254, "KEY 192 words = 768 B", size=17, color=INK)
    f.text(424, 284, "UART 256 words = 1024 B", size=17, color=INK)
    f.line(424, 308, 714, 308, color=MUTED, sw=1.4, amp=0.4)
    f.text(424, 340, "Σ 2304 B", size=24, color=BLUE_D, weight="bold")
    f.text(424, 372, "heap 10240 B", size=17, color=INK, weight="bold")
    f.text(424, 402, "configMINIMAL_STACK_SIZE", size=14, color=MUTED)
    f.text(424, 422, "= 128 words = 512 B", size=14, color=INK)

    f.card(754, 150, 330, 290, GREEN_D, fill=GREEN_FILL)
    f.text(774, 184, "F407 行李牌", size=21, color=GREEN_D, weight="bold")
    f.chip(950, 166, 44, 40, GREEN_D)
    f.text(774, 224, "LED 256 words = 1024 B", size=17, color=INK)
    f.text(774, 254, "KEY 256 words = 1024 B", size=17, color=INK)
    f.text(774, 284, "UART 320 words = 1280 B", size=17, color=INK)
    f.line(774, 308, 1064, 308, color=MUTED, sw=1.4, amp=0.4)
    f.text(774, 340, "Σ 3328 B", size=24, color=GREEN_D, weight="bold")
    f.text(774, 372, "heap 16384 B", size=17, color=INK, weight="bold")
    f.text(774, 410, "同一把尺：word = 4 B", size=14, color=MUTED)

    # (c) Return-value contract: -1 is failure too, so test != pdPASS.
    f.card(54, 460, 560, 246, BLUE_D, fill=WHITE)
    f.text(74, 494, "返回值合同：三个数别认错", size=21, color=BLUE_D,
           weight="bold")
    f.pill(74, 510, 120, 36, "失败 −1", RED, fill=RED_FILL, size=15)
    f.text(210, 534, "errCOULD_NOT_ALLOCATE_REQUIRED_MEMORY", size=14,
           color=INK)
    f.pill(74, 554, 120, 36, "0 · pdFAIL", MUTED, fill=GRAY_FILL, size=14)
    f.text(210, 578, "失败不返回它，别拿 0 验收", size=15.5, color=INK)
    f.pill(74, 598, 120, 36, "成功 1", GREEN_D, fill=GREEN_FILL, size=15)
    f.text(210, 622, "pdPASS(1)", size=17, color=GREEN_D, weight="bold")
    f.text(74, 668, "验收：ret != pdPASS（−1 也要挡）", size=17, color=RED,
           weight="bold")

    # Stack health toolkit: TCB first member, high-water mark, 0xA5 fill.
    f.card(634, 460, 450, 246, AMBER_STROKE, fill=AMBER_PALE)
    f.text(654, 494, "栈体检三件套", size=21, color=AMBER_STROKE,
           weight="bold")
    f.magnifier(1010, 478, 40, AMBER_STROKE)
    f.text(654, 534, "TCB 首成员 = pxTopOfStack", size=16, color=INK,
           weight="bold")
    f.text(654, 562, "上下文切换靠它定位栈顶", size=14, color=MUTED)
    f.text(654, 600, "uxTaskGetStackHighWaterMark", size=15.5, color=INK,
           weight="bold")
    f.text(654, 628, "返回历史最小剩余栈（水位线）", size=14, color=MUTED)
    f.text(654, 668, "溢出检查 2：填 0xA5 查覆盖", size=16, color=INK)

    # One highlighted takeaway + evidence footer.
    f.htext(576, 738, "刻度是 word，读成 byte 箱子就小 4 倍", size=21,
            color=INK, weight="bold", anchor="middle", hl=True, pad=18)
    f.text(576, 764,
           "ΣWCET ≤ min(T)：教学算术 · Host 时序：来源说法（未复核） · 布局示意，非实测",
           size=15, color=MUTED, anchor="middle")
    return f


def ch24_queue_three_contracts():
    f = Fig("ch24-queue-three-contracts", "同一块钢柜，三份租约",
            title_color=GREEN_D, tag="CH 24 · 队列与信号量")
    f.text(64, 126,
           "同一块钢柜：货架存数据、信号灯计数、挂牌锁记名，合同不同而已。",
           size=19, color=MUTED)

    # (a) One cabinet, three lease contracts side by side.
    f.rect(54, 150, 1036, 310, color=GREEN_D, sw=3.0, fill=None)
    f.text(74, 182, "一个柜子：QueueDefinition", size=21, color=GREEN_D,
           weight="bold")
    f.pill(860, 158, 210, 36, "RAM 248 B · 文档推导", GREEN_D,
           fill=GREEN_FILL, size=14)

    # Contract 1: shelves = queue (stores items).
    f.card(74, 200, 320, 240, BLUE_D, fill=BLUE_FILL)
    f.rect(94, 216, 60, 46, color=BLUE_D, sw=2.2, fill=WHITE, double=False)
    f.line(94, 232, 154, 232, color=BLUE_D, sw=1.6, amp=0.3)
    f.line(94, 248, 154, 248, color=BLUE_D, sw=1.6, amp=0.3)
    for bx, by in ((100, 220), (124, 220), (100, 236), (124, 236),
                   (100, 250), (124, 250)):
        f.rect(bx, by, 16, 10, color=BLUE_D, sw=1.2, fill=BLUE_FILL,
               double=False, amp=0.6)
    f.text(170, 240, "货架 · 队列", size=21, color=BLUE_D, weight="bold")
    f.text(94, 288, "判别 uxItemSize > 0", size=16, color=BLUE_D,
           weight="bold")
    f.text(94, 320, "uxLength=10 · uxItemSize=16", size=14.5, color=INK)
    f.text(94, 352, "数据区 10 × 16 B = 160 B", size=15.5, color=INK,
           weight="bold")
    f.text(94, 384, "深度 × 件大小，先算再租", size=14, color=MUTED)

    # Contract 2: signal lamp = semaphore (counts, stores nothing).
    f.card(412, 200, 320, 240, AMBER_STROKE, fill=AMBER_PALE)
    f.circle(462, 230, 16, color=AMBER_STROKE, sw=2.2, fill=AMBER_FILL)
    f.rect(454, 250, 16, 12, color=AMBER_STROKE, sw=1.8, fill=WHITE,
           double=False)
    f.line(446, 262, 478, 262, color=AMBER_STROKE, sw=2.0, amp=0.3)
    f.text(508, 240, "信号灯 · 信号量", size=21, color=AMBER_STROKE,
           weight="bold")
    f.text(432, 288, "判别 pcHead == NULL", size=16, color=AMBER_STROKE,
           weight="bold")
    f.text(432, 320, "二值：1 / 0", size=15.5, color=INK)
    f.text(432, 348, "计数：max / initial", size=15.5, color=INK)
    f.text(432, 380, "uxMessagesWaiting = 当前计数", size=14, color=MUTED)

    # Contract 3: named padlock = mutex (1/1, holder, recursion).
    f.card(750, 200, 320, 240, GREEN_D, fill=GREEN_FILL)
    f.circle(790, 228, 13, color=GREEN_D, sw=2.2)
    f.rect(770, 236, 40, 28, color=GREEN_D, sw=2.2, fill=WHITE,
           double=False)
    f.circle(790, 250, 3, color=GREEN_D, sw=1.0, fill=GREEN_D)
    f.text(846, 240, "挂牌锁 · 互斥量", size=21, color=GREEN_D,
           weight="bold")
    f.text(770, 288, "初值 1 / 1 · 记名", size=16, color=GREEN_D,
           weight="bold")
    f.text(770, 320, "xMutexHolder = 持有人", size=15.5, color=INK)
    f.text(770, 348, "uxRecursiveCallCount = 层数", size=14, color=INK)
    f.text(770, 380, "判别：queueQUEUE_IS_MUTEX", size=14.5, color=GREEN_D,
           weight="bold")

    # (b) Same steel: the two #define facts, with source lines.
    f.pill(54, 478, 500, 44, "uxQueueType = #define pcHead · queue.c:65",
           BLUE_D, fill=BLUE_FILL, size=15)
    f.pill(574, 478, 510, 44, "queueQUEUE_IS_MUTEX = NULL · queue.c:66",
           GREEN_D, fill=GREEN_FILL, size=15)

    # (c) Ring buffer pointers: depth 5, item 16 B.
    f.card(54, 536, 500, 168, BLUE_D, fill=WHITE)
    f.text(74, 566, "环形货架：5 格 × 16 B", size=20, color=BLUE_D,
           weight="bold")
    for i in range(5):
        cx = 184 + i * 50
        fill = GREEN_FILL if i == 0 else (AMBER_PALE if i == 4
                                          else BLUE_FILL)
        col = GREEN_D if i == 0 else (AMBER_STROKE if i == 4 else BLUE_D)
        f.rect(cx, 586, 40, 34, color=col, sw=1.8, fill=fill,
               double=False, amp=1.0)
    f.text(74, 648, "pcHead = 0x2000_1000", size=15, color=GREEN_D,
           weight="bold")
    f.text(300, 648, "pcTail = 0x2000_1050", size=15, color=AMBER_STROKE,
           weight="bold")
    f.arrow(160, 636, 202, 622, color=GREEN_D, sw=2.0, bend=0.0, head=7)
    f.arrow(400, 636, 420, 622, color=AMBER_STROKE, sw=2.0, bend=0.0,
            head=7)
    f.text(74, 680, "0x1050 − 0x1000 = 0x50 = 80 B · 文档推导", size=14,
           color=MUTED)

    # ISR threshold, wait-list key, give never blocks.
    f.card(574, 536, 510, 168, GREEN_D, fill=WHITE)
    f.text(594, 566, "ISR 与等待名单", size=20, color=GREEN_D,
           weight="bold")
    f.text(594, 596, "FromISR 阈值：5 << (8−4) = 0x50", size=15.5,
           color=INK)
    f.text(594, 626, "等待名单排序键 xItemValue", size=15.5, color=INK)
    f.text(594, 654, "= configMAX_PRIORITIES − uxPriority", size=15,
           color=INK, weight="bold")
    f.text(594, 682, "semGIVE_BLOCK_TIME = 0：give 不等待", size=14.5,
           color=MUTED)

    # One highlighted takeaway + evidence footer.
    f.htext(576, 738, "同一块钢柜，三份租约：货架 · 信号灯 · 挂牌锁",
            size=21, color=INK, weight="bold", anchor="middle", hl=True,
            pad=18)
    f.text(576, 764,
           "RAM = 160 + 80 + 8 = 248 B（文档推导） · 布局示意，非实测",
           size=15, color=MUTED, anchor="middle")
    return f


def ch22_first_frame_18_words():
    """New task's first frame: 18 words the kernel fakes as 'just
    interrupted'. Five written slots, 13 skipped. Facts from ch22
    (port.c:92-125, F2:254-255)."""
    f = Fig("ch22-first-frame-18-words",
            "首帧 18 字：内核伪造的「刚被中断」现场",
            title_color=BLUE_D, tag="CH 22 · 任务与调度")
    f.text(64, 126,
           "任务从没运行过，硬件没替它压过栈；pxPortInitialiseStack 手工摆出一份与 PendSV 同形的帧。",
           size=19, color=MUTED)

    # ---- stack column: high address on top, low at bottom ----
    slots = [  # (label, written?)  top -> bottom = high -> low
        ("对齐空位", None, False),
        ("xPSR", "0x01000000", True),
        ("PC", "入口 & 0xFFFFFFFE", True),
        ("LR", "prvTaskExitError", True),
        ("R12", None, False),
        ("R3", None, False), ("R2", None, False), ("R1", None, False),
        ("R0", "任务参数", True),
        ("EXC_RETURN", "0xFFFFFFFD", True),
        ("R11", None, False), ("R10", None, False), ("R9", None, False),
        ("R8", None, False), ("R7", None, False), ("R6", None, False),
        ("R5", None, False), ("R4", None, False),
    ]
    top = 170
    ch = 27
    for i, (label, value, written) in enumerate(slots):
        y = top + i * ch
        c = RED if label in ("LR",) else (BLUE_D if written else MUTED)
        fill = (RED_FILL if label == "LR" else
                (BLUE_FILL if written else GRAY_FILL))
        f.panel(96, y, 210, ch - 3, fill, amp=1.2)
        f.rect(96, y, 210, ch - 3, color=c, sw=1.6, fill=None, amp=1.2)
        f.text(108, y + 18, label, size=13.5,
               color=c if written else MUTED,
               weight="bold" if written else "normal")
        if value:
            f.text(300, y + 18, value, size=12.5,
                   color=RED if label == "LR" else BLUE_D,
                   font=MONO, weight="bold")
    f.text(96, top + 18 * ch + 14, "低地址：pxTopOfStack 的落点（R4 槽）",
           size=13, color=MUTED)
    f.text(96, top - 12, "高地址：创建前的栈顶（对齐空位）", size=13,
           color=MUTED)

    # ---- right: three frame groups + the five facts ----
    f.card(560, 156, 528, 150, BLUE_D, fill=BLUE_FILL)
    f.text(580, 188, "18 字 = 72 B 的三段", size=19, color=BLUE_D,
           weight="bold")
    rows3 = [("硬件帧 8", "R0-R3 · R12 · LR · PC · xPSR", BLUE_D),
             ("软件帧 9", "R4-R11 + EXC_RETURN", GREEN_D),
             ("对齐 1", "最上面一格空位", MUTED)]
    for i, (name, detail, c) in enumerate(rows3):
        y = 220 + i * 26
        f.text(592, y, name, size=16, color=c, weight="bold")
        f.text(706, y, detail, size=13.5, color=INK)
    f.text(580, 292, "硬件 8 + 软件 9 + 对齐 1；源码从栈顶回退 17 次落脚，共 18 字",
           size=13, color=MUTED)

    f.card(560, 326, 528, 170, GREEN_D, fill=GREEN_FILL)
    f.text(580, 358, "真写进去的只有 5 个槽", size=19, color=GREEN_D,
           weight="bold")
    facts = ["xPSR = 0x01000000（T 位，Thumb 开跑）",
             "PC = 入口 & 0xFFFFFFFE（bit0 归 xPSR 管）",
             "LR = prvTaskExitError（任务 return 的陷阱）",
             "R0 = pvParameters（AAPCS 第一个整型参数）",
             "EXC_RETURN = 0xFFFFFFFD（PSP · Thread · 无 FPU）"]
    for i, ln in enumerate(facts):
        f.text(580, 386 + i * 20, ln, size=12.5, color=INK, font=MONO)
    f.text(580, 482, "其余 13 槽源码故意跳过：跑起来就被任务自己的寄存器覆盖",
           size=13, color=MUTED)

    f.card(560, 516, 528, 108, RED, fill=RED_FILL)
    f.text(580, 548, "为什么第一次切换就能跑", size=19, color=RED,
           weight="bold")
    f.text(580, 576, "弹栈按同一套偏移：ldmia r0!, {r4-r11,r14} 从低地址 R4 起，",
           size=13.5, color=INK, font=MONO)
    f.text(580, 598, "硬件帧随后弹出——任务就像「一直在这儿干活」一样开始执行。",
           size=13.5, color=INK)

    f.htext(64, 700, "TCB 的 pxTopOfStack 按偏移 0 存这个落点——第一字段是内核与 port 层的 ABI",
            size=19.5, color=INK, weight="bold", hl=True)
    f.text(576, 730,
           "布局取自本章 port.c/F2 取证记录；位置示意，非 GDB 实拍。",
           size=14, color=MUTED, anchor="middle")
    return f


def ch23_pendsv_line():
    """PendSV switch as one line: save 9 words, swap TCB, restore 9
    words. FPU baggage rides EXC_RETURN bit4. Facts from ch23
    (port.c:505-560, F2:107-207, port.c:434-435)."""
    f = Fig("ch23-pendsv-line",
            "PendSV 一条线：存 9 字，换 TCB，弹 9 字",
            title_color=BLUE_D, tag="CH 23 · 上下文切换")
    f.text(64, 126,
           "排在全系统最低优先级：所有 ISR 退场后才开始换现场，切换永远压不住中断。",
           size=19, color=MUTED)

    # ---- save side ----
    f.card(64, 156, 340, 316, BLUE_D, fill=BLUE_FILL)
    f.text(84, 188, "保存当前任务", size=19, color=BLUE_D, weight="bold")
    steps = [("mrs r0, psp", "① 栈顶拿进来"),
             ("tst r14, #0x10", "③ 行李牌 bit4"),
             ("stmdb r0!, {r4-r11,r14}", "④ 软件帧 9 字 = 36 B"),
             ("str r0, [r2]", "⑤ 写回 TCB 偏移 0")]
    for i, (code, note) in enumerate(steps):
        y = 216 + i * 62
        f.pill(84, y - 22, 300, 36, code, BLUE_D, fill=WHITE, size=14.5,
               text_color=INK)
        f.text(84, y + 30, note, size=13.5, color=MUTED)

    # ---- switch middle ----
    f.card(428, 156, 296, 316, AMBER_STROKE, fill=AMBER_PALE)
    f.text(448, 188, "换人（关窗）", size=19, color=AMBER_STROKE,
           weight="bold")
    f.pill(448, 202, 256, 38, "basepri = 0x50", RED, fill=WHITE, size=15)
    f.text(448, 268, "bl vTaskSwitchContext", size=14.5, color=INK,
           font=MONO, weight="bold")
    f.text(448, 294, "⑦ 只换 pxCurrentTCB", size=13.5, color=MUTED)
    f.pill(448, 314, 256, 38, "basepri = 0", GREEN_D, fill=WHITE,
           size=15)
    f.text(448, 380, "⑥⑧ 临界区只护就绪表", size=13.5, color=MUTED)
    f.text(448, 408, "窗口短，ISR 只被挡一小段", size=13.5, color=MUTED)
    f.text(448, 444, "r0/r3 先 stmdb 存、后 ldmia 取", size=13,
           color=MUTED)

    # ---- restore side ----
    f.card(748, 156, 340, 316, GREEN_D, fill=GREEN_FILL)
    f.text(768, 188, "恢复新任务", size=19, color=GREEN_D, weight="bold")
    rsteps = [("ldr r1, [r3]", "⑨ 新 TCB"),
              ("ldr r0, [r1]", "⑩ 新栈顶（偏移 0）"),
              ("ldmia r0!, {r4-r11,r14}", "⑪ 弹软件帧 9 字"),
              ("bx r14", "硬件弹 8 字 / 26 字")]
    for i, (code, note) in enumerate(rsteps):
        y = 216 + i * 62
        f.pill(768, y - 22, 300, 36, code, GREEN_D, fill=WHITE, size=14.5,
               text_color=INK)
        f.text(768, y + 30, note, size=13.5, color=MUTED)

    # ---- bottom: lowest priority + baggage legend ----
    f.panel(64, 500, 560, 100, RED_FILL, amp=1.6)
    f.rect(64, 500, 560, 100, color=RED, sw=1.8, fill=None, amp=1.6)
    f.text(88, 532, "为什么排最低：SHPR3 两个字节都写 0xFF", size=15.5,
           color=RED, weight="bold")
    f.text(88, 560, "（port.c:434-435，portMIN = 255）；SysTick 只置挂起位",
           size=14, color=INK)
    f.text(88, 586, "写 ICSR bit28 = 排队，不是立即切", size=14.5,
           color=INK)

    f.panel(652, 500, 436, 100, GRAY_FILL, amp=1.6)
    f.rect(652, 500, 436, 100, color=MUTED, sw=1.6, fill=None, amp=1.6)
    f.text(676, 532, "行李牌 bit4：0 = 跑过浮点", size=15.5, color=INK,
           weight="bold")
    f.text(676, 560, "vstmdbeq r0!, {s16-s31} 补存 16 字", size=14,
           color=INK, font=MONO)
    f.text(676, 586, "首帧 EXC_RETURN = 0xFFFFFFFD，bit4 = 1，无行李",
           size=13.5, color=MUTED)

    f.htext(64, 700, "软件永远补 9 字；硬件弹多少，看行李牌",
            size=22, color=INK, weight="bold", hl=True)
    f.text(576, 730,
           "步骤号取自本章 port.c/F2 的十一条语义转写；流程示意，非 GDB 实拍。",
           size=14, color=MUTED, anchor="middle")
    return f


def ch25_free_merge():
    """heap_4 free: three steps, adjacent-by-address is the only merge
    rule, no boundary tags. Facts from ch25 (heap_4.c:492)."""
    f = Fig("ch25-free-merge",
            "heap_4 释放：三步合邻居",
            title_color=GREEN_D, tag="CH 25 · 内存管理")
    f.text(64, 126,
           "链表按地址升序；释放块放回去时，前后只有地址正好接上才并——隔着一个已用块的洞永不合并。",
           size=19, color=MUTED)

    # ---- memory strip before ----
    f.text(96, 170, "释放前", size=15, color=MUTED, weight="bold")
    blocks0 = [("A 已用", 88, GRAY_FILL, MUTED), ("我 释放 248 B", 260,
               RED_FILL, RED), ("B 空闲 100 B", 150, GREEN_FILL, GREEN_D),
               ("C 已用", 100, GRAY_FILL, MUTED)]
    x = 96
    for name, w, fl, c in blocks0:
        f.panel(x, 182, w, 44, fl, amp=1.4)
        f.rect(x, 182, w, 44, color=c, sw=1.8, fill=None, amp=1.4)
        f.text(x + w / 2, 209, name, size=13.5, color=c, anchor="middle",
               weight="bold")
        x += w + 8
    f.arrow(560, 240, 560, 282, color=BLUE_D, sw=2.6, bend=0.0, head=10)
    f.text(586, 268, "prvInsertBlockIntoFreeList：后邻吞并 → 被前邻吞并",
           size=14.5, color=BLUE_D, weight="bold")

    # ---- memory strip after ----
    f.text(96, 316, "释放后", size=15, color=MUTED, weight="bold")
    blocks1 = [("A 已用", 88, GRAY_FILL, MUTED),
               ("我+B 合并 348 B", 418, GREEN_FILL, GREEN_D),
               ("C 已用", 100, GRAY_FILL, MUTED)]
    x = 96
    for name, w, fl, c in blocks1:
        f.panel(x, 328, w, 44, fl, amp=1.4)
        f.rect(x, 328, w, 44, color=c, sw=1.8, fill=None, amp=1.4)
        f.text(x + w / 2, 355, name, size=13.5, color=c, anchor="middle",
               weight="bold")
        x += w + 8
    f.text(96, 402, "块头 8 B（pxNextFreeBlock 4 + xBlockSize 4）；xBlockSize 含头自身；对齐 8",
           size=14, color=INK, font=MONO)

    # ---- three steps + verdict cards ----
    f.card(64, 436, 560, 172, BLUE_D, fill=BLUE_FILL)
    f.text(84, 468, "三步放回", size=19, color=BLUE_D, weight="bold")
    f.text(84, 500, "① 按地址走链表，找到插入点", size=15, color=INK)
    f.text(84, 528, "② 我的尾 == 后邻的头 → 吞并后邻", size=15, color=INK)
    f.text(84, 556, "③ 前邻的尾 == 我的头 → 被它吞并", size=15, color=INK)
    f.text(84, 584, "谁也不挨着，就正常插进链表", size=14, color=MUTED)

    f.card(652, 436, 436, 172, RED, fill=RED_FILL)
    f.text(672, 468, "不是边界标记法", size=19, color=RED, weight="bold")
    f.text(672, 500, "只有 8 B 头、没有 footer；前邻靠", size=14.5,
           color=INK)
    f.text(672, 526, "地址序遍历找出，合并是 O(n) 不是 O(1)", size=14.5,
           color=INK)
    f.text(672, 556, "小堆上 O(n) 开销微不足道，换来极简头部", size=14,
           color=MUTED)
    f.text(672, 584, "「边界标记法」是旧稿术语错位，别照搬", size=14,
           color=RED, weight="bold")

    f.htext(64, 700, "分配走首次适配，偏爱低地址块；相邻合并是它的搭档，不是解药",
            size=20, color=INK, weight="bold", hl=True)
    f.text(576, 730,
           "取自本章 heap_4.c:492 起的源码语义；示意布局，非内存转储。",
           size=14, color=MUTED, anchor="middle")
    return f


FIGS = {
    "ch21-stack-word-ruler": ch21_stack_word_ruler,
    "ch22-first-frame-18-words": ch22_first_frame_18_words,
    "ch23-pendsv-line": ch23_pendsv_line,
    "ch24-queue-three-contracts": ch24_queue_three_contracts,
    "ch25-free-merge": ch25_free_merge,
}


if __name__ == "__main__":
    names = sys.argv[1:] or list(FIGS)
    STAGE.mkdir(parents=True, exist_ok=True)
    for n in names:
        f = FIGS[n]()
        save(f, str(STAGE / (n + ".svg")))
        print("wrote", STAGE / (n + ".svg"))
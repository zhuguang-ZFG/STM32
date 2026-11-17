# -*- coding: utf-8 -*-
"""V2d hand-drawn plates: ch41 deadline hourglasses, ch44 error sorting bench.

Facts pinned verbatim. ch41: supervisor compares now-last_ms[id] >=
deadline_ms[id] every 50 ms; sampling 2500 ms / comm 1500 ms; startup
grace 3000 ms; progress() only refreshes timestamps (no counting);
overdue -> latch -> stop feeding -> ~2 s reset (F407 IWDG feed point in
supervisor task; S3 TWDT per-task subscription); 64 B payload -> 74 B
wire frame (64+6+2+1+1); frame_t 70 B, samples[16] = 1120 B; 100 ms
period -> 1.6 s burst; AT24C02 2x128 B, tWR~5 ms; DMA2 Stream0 IRQ56
prio6. ch44: eight specimens (manual layer 4 / discourse layer 4) with
lowest-cost actions, cost ladder 30 s grep -> 1 min chapter search ->
minute-level errata/bit-check -> minute-level run-the-phenomenon.
No board measurements; layouts are schematic.

Deterministic: hd.Fig seeds its own RNG; re-running gives the same SVG.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hd import (AMBER_FILL, AMBER_PALE, AMBER_STROKE, BLUE_D,  # noqa: E402
                BLUE_FILL, GRAY_FILL, GREEN_D, GREEN_FILL, HAND, INK, MUTED,
                RED, RED_FILL, WHITE, Fig, save)

MONO = "'Consolas','Courier New',monospace"
STAGE = Path(__file__).resolve().parents[2] / ".temp" / "l0-l5-pass" / "figures"


def hourglass(f, cx, y, color):
    """Two-bulb hourglass, 74 wide x 100 tall, sand in both bulbs."""
    f.stroke([(cx - 35, y + 2), (cx + 35, y + 2), (cx, y + 50)],
             color=color, sw=2.2, close=True, fill=AMBER_FILL)
    f.stroke([(cx, y + 50), (cx + 35, y + 98), (cx - 35, y + 98)],
             color=color, sw=2.2, close=True, fill=AMBER_FILL)
    f.line(cx - 37, y, cx + 37, y, color=color, sw=2.6)
    f.line(cx - 37, y + 100, cx + 37, y + 100, color=color, sw=2.6)
    f.line(cx, y + 50, cx, y + 72, color=color, sw=2.0)


def ch41_deadline_hourglasses():
    f = Fig("ch41-deadline-hourglasses", "期限沙漏：监督只认时间戳",
            title_color=BLUE_D, tag="CH 41 · 双板日志")
    f.text(576, 126, "一只 50 ms 的怀表盯着两只沙漏：时间戳到点，就点名。",
           size=17, color=MUTED, anchor="middle")

    # ---- row 1: supervisor pocket watch + two hourglasses ----
    f.card(54, 150, 250, 190, BLUE_D, fill=BLUE_FILL)
    f.text(70, 182, "监督怀表", size=20, color=BLUE_D, weight="bold")
    f.clockface(179, 248, 40, BLUE_D, label="每 50 ms 一拍", label_size=14)
    f.text(179, 330, "只认时间戳", size=14, color=MUTED, anchor="middle")

    f.card(330, 150, 360, 190, GREEN_D, fill=GREEN_FILL)
    f.text(346, 182, "采样沙漏", size=20, color=GREEN_D, weight="bold")
    hourglass(f, 415, 200, GREEN_D)
    f.text(478, 214, "期限到点即 overdue", size=14, color=INK)
    f.pill(478, 226, 190, 42, "采样 2500 ms", GREEN_D, fill=WHITE, size=18)
    f.text(478, 300, "只刷时间戳，不累计次数", size=14, color=INK)

    f.card(716, 150, 382, 190, BLUE_D, fill=BLUE_FILL)
    f.text(732, 182, "通信沙漏", size=20, color=BLUE_D, weight="bold")
    hourglass(f, 801, 200, BLUE_D)
    f.text(863, 214, "同表比较，各记各账", size=14, color=INK)
    f.pill(863, 226, 190, 42, "通信 1500 ms", BLUE_D, fill=WHITE, size=18)
    f.text(863, 300, "last_ms[id] 各自刷新", size=14, color=INK)

    # ---- comparison rule + progress() semantics, verbatim ----
    f.text(576, 368,
           "监督每 50 ms 比较 now−last_ms[id] ≥ deadline_ms[id]；启动宽限 3000 ms",
           size=16, color=INK, anchor="middle", weight="bold")
    f.text(576, 392,
           "progress() 只刷新时间戳，不累计次数；「活着但停滞」也要点名",
           size=16, color=INK, anchor="middle")

    # ---- row 2: overdue chain + board feed points + stamp ----
    f.card(54, 408, 760, 150, RED, fill=RED_FILL)
    f.text(70, 438, "逾期处置链", size=20, color=RED, weight="bold")
    f.pill(70, 456, 120, 44, "overdue", RED, fill=WHITE, size=17)
    f.arrow(194, 478, 210, 478, color=RED, sw=2.4, bend=0.0, head=8)
    f.pill(214, 456, 100, 44, "latch", RED, fill=WHITE, size=17)
    f.arrow(318, 478, 334, 478, color=RED, sw=2.4, bend=0.0, head=8)
    f.pill(338, 456, 120, 44, "停喂狗", RED, fill=WHITE, size=17)
    f.arrow(462, 478, 478, 478, color=RED, sw=2.4, bend=0.0, head=8)
    f.pill(482, 456, 170, 44, "约 2 s 复位", RED, fill=WHITE, size=17)
    f.text(70, 530, "F407 IWDG 喂狗点在监督任务；S3 TWDT 按任务订阅",
           size=14, color=INK)
    f.stamp(956, 480, "活着但停滞也点名", RED, size=18, angle=-7)

    # ---- row 3: byte budget + storage/transport ----
    f.card(54, 572, 600, 132, BLUE_D, fill=BLUE_FILL)
    f.text(70, 600, "字节预算", size=19, color=BLUE_D, weight="bold")
    f.text(70, 628, "64 B 载荷 → 74 B 线上帧（64+6+2+1+1）", size=15, color=INK)
    f.text(70, 656, "frame_t 70 B · samples[16] = 1120 B", size=15,
           color=INK, font=MONO)
    f.text(70, 684, "100 ms 周期 → 1.6 s burst", size=15, color=INK)

    f.card(678, 572, 420, 132, GREEN_D, fill=GREEN_FILL)
    f.text(694, 600, "存储与搬运", size=19, color=GREEN_D, weight="bold")
    f.text(694, 630, "AT24C02 2×128 B · tWR≈5 ms", size=15, color=INK)
    f.text(694, 662, "DMA2 Stream0 IRQ56 prio6", size=15, color=INK, font=MONO)

    f.htext(576, 734, "心跳只问活着，期限问做完", size=24, color=INK,
            weight="bold", anchor="middle", hl=True)
    f.text(576, 762, "pending · 预期逻辑结果(非实测) · 布局示意，非实测",
           size=13, color=MUTED, anchor="middle")
    return f


def cubby(f, x, y, name, lines, action, color, fill, mono=(), warn=()):
    """One sorting-bench cubby: specimen lines + lowest-cost action pill."""
    f.card(x, y, 246, 150, color, fill=fill)
    f.text(x + 14, y + 26, name, size=15, color=color, weight="bold")
    for i, ln in enumerate(lines):
        f.text(x + 14, y + 50 + i * 20, ln, size=14,
               color=RED if i in warn else INK,
               font=MONO if i in mono else HAND)
    f.pill(x + 14, y + 106, 218, 32, action, color, fill=WHITE, size=14)


def ch44_error_sorting_bench():
    f = Fig("ch44-error-sorting-bench", "幻觉分拣台：先存在后语义",
            title_color=RED, tag="CH 44 · 对账与幻觉")
    f.text(576, 126, "八格分拣台：先问「在不在」，再问「对不对」，每格配最低成本动作。",
           size=17, color=MUTED, anchor="middle")

    # ---- row 1: manual layer, four cubbies ----
    f.text(54, 158, "手册层 · 标本与最低成本动作", size=16, color=AMBER_STROKE,
           weight="bold")
    manuals = [
        ("① 位名张冠李戴",
         ["RCC_APB1ENR bit5 = TIM7EN", "不是 GPIOF；GPIOFEN 在",
          "RCC_AHB1ENR bit5"], "30 s grep", (0, 2), ()),
        ("② 地址错位",
         ["基址/偏移差 0x400", "偏移算错，整片错位"], "1 min 章节检索", (), ()),
        ("③ 修订版差异",
         ["Rev V 特性写成全系列", "把单修订当全系列"], "分钟级勘误", (), ()),
        ("④ 特性编造",
         ["「硬件 CRC 单元」", "其实没有"], "特性表核对", (), ()),
    ]
    for i, (name, lines, act, mono, warn) in enumerate(manuals):
        cubby(f, 54 + i * 266, 170, name, lines, act, AMBER_STROKE,
              AMBER_PALE, mono, warn)

    # ---- row 2: discourse layer, four cubbies ----
    f.text(54, 348, "话语层 · 标本与最低成本动作", size=16, color=BLUE_D,
           weight="bold")
    discourse = [
        ("⑤ 引用幻觉",
         ["引「§7.3」实际在 §2.3", "章节号对不上"], "30 s 检索", (), ()),
        ("⑥ 行号漂移",
         ["main:619 实为 631", "代码改了，行号没跟上"], "grep -n 重测", (), ()),
        ("⑦ 数字陈旧",
         ["题花 100→101、动画 109→111", "章数 94"], "重数", (), ()),
        ("⑧ 编造示例当真",
         ["假勘误四件套", "（编造示例，请勿当真）"], "看标注", (), (1,)),
    ]
    for i, (name, lines, act, mono, warn) in enumerate(discourse):
        cubby(f, 54 + i * 266, 360, name, lines, act, BLUE_D, BLUE_FILL,
              mono, warn)

    # ---- cost ladder (teaching order) ----
    f.text(54, 536, "成本序（教学口径）", size=15, color=MUTED, weight="bold")
    f.pill(54, 546, 220, 40, "30 s grep", GREEN_D, fill=GREEN_FILL, size=16)
    f.arrow(278, 566, 298, 566, color=MUTED, sw=2.4, bend=0.0, head=8)
    f.pill(302, 546, 240, 40, "1 min 章节检索", GREEN_D, fill=GREEN_FILL,
           size=16)
    f.arrow(546, 566, 566, 566, color=MUTED, sw=2.4, bend=0.0, head=8)
    f.pill(570, 546, 260, 40, "分钟级勘误/逐位", AMBER_STROKE, fill=AMBER_PALE,
           size=16)
    f.arrow(834, 566, 854, 566, color=MUTED, sw=2.4, bend=0.0, head=8)
    f.pill(858, 546, 240, 40, "分钟级跑现象", RED, fill=RED_FILL, size=16)

    # ---- verdict stamps ----
    f.stamp(330, 640, "先存在性，后语义", RED, size=20, angle=-6)
    f.stamp(820, 640, "道歉是文体，不是修正动作", RED, size=17, angle=5)

    f.htext(576, 734, "先验存在，再谈语义：道歉不是修正动作", size=24,
            color=INK, weight="bold", anchor="middle", hl=True)
    f.text(576, 762,
           "dash≤2/章 · check_pdf 13 门 / docs-check 27 CLAIMS（合并前 mcu 口径）· "
           "教学口径 · 布局示意，非实测",
           size=13, color=MUTED, anchor="middle")
    return f


def ch44_verify_decision_tree():
    """Verify decision tree: where correctness is defined picks the path.
    Facts from ch44 (AI02 caliber)."""
    f = Fig("ch44-verify-decision-tree",
            "验证决策树：一问定路径",
            title_color=GREEN_D, tag="CH 44 · 对账与幻觉")
    f.text(64, 126,
           "树分的是责任，不是难度：这条断言的正确性由谁定义，就走哪条路。",
           size=19, color=MUTED)

    # ---- root ----
    f.pill(336, 158, 480, 56, "正确性定义在公共知识，还是在你的板子与责任里？",
           BLUE_D, fill=WHITE, size=17)

    # ---- three branches ----
    f.card(64, 268, 340, 210, BLUE_D, fill=BLUE_FILL)
    f.text(84, 300, "公共知识", size=19, color=BLUE_D, weight="bold")
    f.text(84, 326, "手册可查、来源可对", size=13.5, color=MUTED)
    f.text(84, 360, "→ 三问对账", size=16, color=BLUE_D, weight="bold")
    f.text(84, 392, "名：寄存器/符号叫什么", size=14, color=INK)
    f.text(84, 418, "位：位号落在哪个寄存器", size=14, color=INK)
    f.text(84, 444, "序：先开时钟还是先配位", size=14, color=INK)

    f.card(428, 268, 296, 210, GREEN_D, fill=GREEN_FILL)
    f.text(448, 300, "板卡事实", size=19, color=GREEN_D, weight="bold")
    f.text(448, 326, "原理图、丝印、实测", size=13.5, color=MUTED)
    f.text(448, 360, "→ 实测读回", size=16, color=GREEN_D, weight="bold")
    f.text(448, 392, "引脚翻转了吗", size=14, color=INK)
    f.text(448, 418, "万用表/示波器读数", size=14, color=INK)
    f.text(448, 444, "板上的事实手册查不到", size=13.5, color=MUTED)

    f.card(748, 268, 340, 210, RED, fill=RED_FILL)
    f.text(768, 300, "你的责任", size=19, color=RED, weight="bold")
    f.text(768, 326, "安全边界、阈值、终审", size=13.5, color=MUTED)
    f.text(768, 360, "→ 不进 AI", size=16, color=RED, weight="bold")
    f.text(768, 392, "四条不许碰边界之一", size=14, color=INK)
    f.text(768, 418, "模型可以建议，不能拍板", size=14, color=INK)
    f.text(768, 444, "责任全部在你", size=14, color=RED, weight="bold")

    # ---- entry disciplines ----
    f.panel(64, 508, 1024, 104, GRAY_FILL, amp=1.6)
    f.rect(64, 508, 1024, 104, color=MUTED, sw=1.6, fill=None, amp=1.6)
    f.text(88, 540, "两条入口纪律", size=15.5, color=INK, weight="bold")
    f.text(88, 570, "① 30 秒分类：任何断言先分手册层 / 话语层 / 板卡层",
           size=14.5, color=INK)
    f.text(88, 596, "② 贴不出证据默认升级：拿不出出处与判据，按最高成本路径处理",
           size=14.5, color=INK)
    f.text(690, 570, "分级：RCC 与模式寄存器一律逐位", size=14, color=MUTED)
    f.text(690, 596, "应用层抽样 · 纯算法单测", size=14, color=MUTED)

    f.stamp(980, 668, "道歉是文体，不是修正", RED, size=16, angle=-8)

    f.htext(64, 700, "30 秒先分类再动手；回喂三元组才算修正",
            size=22, color=INK, weight="bold", hl=True)
    f.text(576, 730,
           "决策树取自本章 AI02 口径；结构示意，非实测记录。",
           size=14, color=MUTED, anchor="middle")
    return f


FIGS = {
    "ch41-deadline-hourglasses": ch41_deadline_hourglasses,
    "ch44-error-sorting-bench": ch44_error_sorting_bench,
    "ch44-verify-decision-tree": ch44_verify_decision_tree,
}


if __name__ == "__main__":
    names = sys.argv[1:] or list(FIGS)
    STAGE.mkdir(parents=True, exist_ok=True)
    for n in names:
        f = FIGS[n]()
        save(f, str(STAGE / (n + ".svg")))
        print("wrote", STAGE / (n + ".svg"))
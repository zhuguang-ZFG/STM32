# -*- coding: utf-8 -*-
"""V2c hand-drawn plates: ch33 cache/DMA open-kitchen pass, ch39 PI clamp.

Facts are pinned verbatim to the two fact sheets. ch33: H7 DTCM
0x20000000 (CPU+MDMA only, ETH DMA unreachable, AN4891), F407 CCM
0x1000_0000 (no DMA slave path), cache line 32 B, TX clean / RX
invalidate, 32 B-aligned exclusive buffers, pbuf invariant and
pbuf_free-once, IRQ must not call tcp_write/udp_send, lwIP 2.2.1 /
ST fork 07680c81, RMII REF_CLK 50 MHz. ch39: e/I_try/u_try/u clamp
chain, dt 10 ms (TIM4), worked e=-10 -> -0.05 permille -> -20.05
permille, Kp 2.0, Ki 0.5, i_limit 500, duty_limit 900, ramp 600,
alpha 1.0, CCR 3240 < 3599, ARR 3600, four anti-windup rules,
F04 deadline <=2 ms / jitter <=1 ms. No board measurements;
metrics are proposed acceptance targets. Layouts are schematic.

Deterministic: hd.Fig seeds its own RNG; re-running gives the same SVG.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hd import (AMBER_FILL, AMBER_PALE, AMBER_STROKE, BLUE_D,  # noqa: E402
                BLUE_FILL, GRAY_FILL, GREEN_D, GREEN_FILL, INK, MUTED, RED,
                RED_FILL, WHITE, Fig, save)

STAGE = Path(__file__).resolve().parents[2] / "assets" / "illustrations" / "staged" / "l0-l5-pass" / "figures"


def ch33_cache_dma_kitchen():
    f = Fig("ch33-cache-dma-kitchen", "明档：便签、台面与跑菜员",
            title_color=BLUE_D, tag="CH 33 · 网络与 DMA 可见性")
    f.text(64, 126,
           "Cache 是厨师便签，SRAM 是台面，DMA 是跑菜员：32 B 一盘整换，不递半盘。",
           size=19, color=MUTED)

    # ---- (a) the pass: three stations, two gaps ----
    f.card(54, 160, 260, 176, AMBER_STROKE, fill=AMBER_PALE)
    f.text(70, 194, "便签 = Cache", size=21, color=AMBER_STROKE, weight="bold")
    f.doc(70, 212, 64, 74, AMBER_STROKE)
    f.text(150, 238, "CPU 的草稿", size=16, color=INK)
    f.text(150, 264, "脏行未落台面", size=16, color=INK)
    f.text(70, 316, "line = 32 B", size=16, color=INK, weight="bold")

    f.card(446, 160, 260, 176, GREEN_D, fill=GREEN_FILL)
    f.text(462, 194, "台面 = SRAM", size=21, color=GREEN_D, weight="bold")
    f.rect(486, 200, 52, 14, color=AMBER_STROKE, sw=1.6, fill=AMBER_FILL,
           double=False)
    f.rect(462, 214, 110, 22, color=GREEN_D, sw=2.2, fill=WHITE, double=False)
    f.line(470, 236, 470, 258, color=GREEN_D, sw=2.2)
    f.line(564, 236, 564, 258, color=GREEN_D, sw=2.2)
    f.text(462, 290, "DMA 只认台面地址", size=16, color=INK)
    f.text(462, 318, "缓冲 32 B 对齐独占", size=16, color=INK)

    f.card(838, 160, 260, 176, BLUE_D, fill=BLUE_FILL)
    f.text(854, 194, "跑菜 = DMA", size=21, color=BLUE_D, weight="bold")
    f.chip(854, 214, 70, 56, BLUE_D, label="DMA", size=15)
    f.text(940, 238, "RMII", size=17, color=BLUE_D, weight="bold")
    f.text(940, 264, "50 MHz", size=17, color=INK)
    f.text(854, 316, "只搬整盘 32 B", size=16, color=INK)

    # gap 1: notepad <-> counter, the two cache maintenance directions
    f.arrow(318, 225, 442, 225, color=AMBER_STROKE, sw=2.6, bend=0.0)
    f.text(380, 208, "TX clean", size=15, color=AMBER_STROKE, anchor="middle",
           weight="bold")
    f.arrow(442, 285, 318, 285, color=BLUE_D, sw=2.6, bend=0.0)
    f.text(380, 310, "RX invalidate", size=15, color=BLUE_D, anchor="middle",
           weight="bold")

    # gap 2: counter <-> runner, one whole 32 B tray
    f.arrow(710, 210, 834, 210, color=GREEN_D, sw=2.6, bend=0.0)
    f.text(772, 196, "TX 交整盘", size=15, color=GREEN_D, anchor="middle",
           weight="bold")
    f.rect(727, 236, 90, 30, color=AMBER_STROKE, sw=2.2, fill=AMBER_FILL,
           double=False)
    f.text(772, 257, "32 B", size=16, color=AMBER_STROKE, anchor="middle",
           weight="bold")
    f.text(772, 284, "只整盘", size=14, color=MUTED, anchor="middle")
    f.arrow(834, 300, 710, 300, color=GREEN_D, sw=2.6, bend=0.0)
    f.text(772, 322, "RX 收整盘", size=15, color=GREEN_D, anchor="middle",
           weight="bold")

    # ---- (b) reachability + alignment rules ----
    f.card(54, 350, 500, 230, RED, fill=WHITE)
    f.text(70, 382, "哪些内存 DMA 够得着", size=21, color=RED, weight="bold")
    f.text(70, 412, "H7 DTCM 0x20000000", size=17, color=INK, weight="bold")
    f.text(70, 436, "仅 CPU + MDMA；ETH DMA 不可达（AN4891）", size=15,
           color=INK)
    f.text(70, 462, "F407 CCM 0x1000_0000", size=17, color=INK, weight="bold")
    f.text(70, 486, "无 DMA 从机路径；「DTCM 不可达」不属于 F407", size=15,
           color=INK)
    f.magnifier(70, 514, 28, RED)
    f.text(104, 545, "查 link map", size=15, color=RED, weight="bold")
    f.stamp(330, 538, "DTCM 不可达 ≠ F407", size=18, angle=-6)

    f.card(578, 350, 520, 230, AMBER_STROKE, fill=AMBER_PALE)
    f.text(594, 382, "对齐与独占：整盘规矩", size=21, color=AMBER_STROKE,
           weight="bold")
    f.pill(594, 404, 150, 40, "32 B 对齐", AMBER_STROKE, fill=WHITE, size=17)
    f.pill(760, 404, 150, 40, "缓冲独占", AMBER_STROKE, fill=WHITE, size=17)
    f.pill(926, 404, 156, 40, "整盘 32 B", AMBER_STROKE, fill=WHITE, size=17)
    f.text(594, 478, "TX 前 clean：把便签压回台面", size=16, color=INK)
    f.text(594, 506, "RX 后 invalidate：便签作废重读", size=16, color=INK)
    f.text(594, 540, "禁止：未对齐窄范围 invalidate", size=16, color=RED,
           weight="bold")
    f.text(594, 566, "整盘换，不撕半盘", size=14, color=MUTED)

    # ---- (c) pbuf chain + IRQ discipline ----
    f.card(54, 592, 1044, 116, GREEN_D, fill=GREEN_FILL)
    f.text(70, 620, "pbuf 链与中断纪律", size=20, color=GREEN_D, weight="bold")
    f.text(70, 650, "tot_len == len + (next ? next->tot_len : 0)", size=17,
           color=INK, weight="bold")
    f.pill(70, 666, 230, 34, "pbuf_free 恰好一次", GREEN_D, fill=WHITE, size=16)
    f.pill(320, 666, 340, 34, "IRQ 禁调 tcp_write / udp_send", RED,
           fill=RED_FILL, size=16)
    f.text(680, 688, "字段 next / payload / tot_len / len", size=15, color=INK)

    f.htext(576, 736, "台面才是 DMA 的地址：整盘 32 B，TX clean / RX invalidate",
            size=24, color=INK, weight="bold", anchor="middle", hl=True)
    f.text(576, 764,
           "lwIP 2.2.1 · ST fork 07680c81 · RMII REF_CLK 50 MHz · "
           "手册级；实验未实测 · 布局示意，非实测",
           size=15, color=MUTED, anchor="middle")
    return f


def ch39_pi_saturation_clamp():
    f = Fig("ch39-pi-saturation-clamp", "油门钢限位与积分棘轮锁",
            title_color=RED, tag="CH 39 · PI 与抗饱和")
    f.text(64, 126,
           "踏板有钢限位 ±900‰，积分账本另有一把 ±500‰ 的棘轮锁：夹钳管现在，锁管历史。",
           size=19, color=MUTED)

    # ---- (a) pedal between two steel stops + clamp chain ----
    f.card(54, 150, 520, 330, RED, fill=RED_FILL)
    f.text(70, 182, "踏板：钢限位 ±900‰", size=21, color=RED, weight="bold")
    f.text(70, 214, "e = ramped_rpm − rpm_filt", size=15, color=INK)
    f.text(70, 242, "I_try = I + Ki×e×Δt", size=15, color=INK)
    f.text(70, 270, "u_try = Kp×e + I_try", size=15, color=INK)
    f.text(70, 298, "u = clamp(u_try, ±duty_limit)", size=15, color=INK,
           weight="bold")
    f.wave(392, 200, 150, 22, RED, kind="pwm", cycles=3, duty=0.9)
    f.rect(392, 240, 16, 80, color=INK, sw=2.2, fill=GRAY_FILL, double=False)
    f.rect(526, 240, 16, 80, color=INK, sw=2.2, fill=GRAY_FILL, double=False)
    f.line(408, 280, 526, 280, color=INK, sw=3.0)
    f.rect(442, 268, 50, 24, color=RED, sw=2.2, fill=WHITE, double=False)
    f.arrow(438, 256, 414, 256, color=RED, sw=2.2, bend=0.0, head=7)
    f.arrow(496, 256, 520, 256, color=RED, sw=2.2, bend=0.0, head=7)
    f.text(400, 338, "−900‰", size=14, color=RED, anchor="middle",
           weight="bold")
    f.text(534, 338, "+900‰", size=14, color=RED, anchor="middle",
           weight="bold")
    f.pill(70, 350, 46, 36, "e", RED, fill=WHITE, size=16)
    f.arrow(120, 368, 132, 368, color=RED, sw=2.0, bend=0.0, head=7)
    f.pill(136, 350, 86, 36, "I_try", RED, fill=WHITE, size=16)
    f.arrow(226, 368, 238, 368, color=RED, sw=2.0, bend=0.0, head=7)
    f.pill(242, 350, 86, 36, "u_try", RED, fill=WHITE, size=16)
    f.arrow(332, 368, 344, 368, color=RED, sw=2.0, bend=0.0, head=7)
    f.pill(348, 350, 120, 36, "u = clamp", RED, fill=WHITE, size=16)
    f.text(70, 412, "duty_limit = 900‰：钢限位", size=16, color=INK,
           weight="bold")
    f.text(70, 440, "Kp 2.0 ‰/rpm · Ki 0.5 ‰/(rpm·s)", size=15, color=INK)
    f.text(70, 464, "ramp 600 rpm/s · α=1.0（起步值）", size=14, color=MUTED)

    # ---- (b) credit ledger with the four accept/reject rules ----
    f.card(598, 150, 500, 330, GREEN_D, fill=GREEN_FILL)
    f.text(614, 182, "积分账本：棘轮锁 ±500‰", size=21, color=GREEN_D,
           weight="bold")
    f.doc(614, 200, 70, 80, GREEN_D, label="I", size=20)
    f.text(700, 224, "i_limit = 500‰", size=17, color=GREEN_D, weight="bold")
    f.text(700, 252, "账本记历史，夹钳管现在", size=15, color=INK)
    f.pill(614, 292, 228, 44, "未饱和 → 收", GREEN_D, fill=WHITE, size=16)
    f.pill(854, 292, 228, 44, "上饱和 & e<0 → 收", GREEN_D, fill=WHITE,
           size=16)
    f.pill(614, 348, 228, 44, "下饱和 & e>0 → 收", GREEN_D, fill=WHITE,
           size=16)
    f.pill(854, 348, 228, 44, "否则 → 拒（锁历史）", RED, fill=RED_FILL,
           size=16)
    f.text(614, 420, "拒 = 这一拍 I 不再长大", size=16, color=INK)
    f.text(614, 448, "棘轮只锁历史，不夹当前输出", size=15, color=MUTED)

    # ---- (c) worked negative example + timer landing ----
    f.card(54, 494, 620, 212, RED, fill=WHITE)
    f.text(70, 526, "负号算例：e = −10 的一拍", size=20, color=RED,
           weight="bold")
    f.pill(70, 546, 120, 40, "e = −10", RED, fill=RED_FILL, size=17)
    f.arrow(194, 566, 214, 566, color=RED, sw=2.2, bend=0.0, head=8)
    f.pill(218, 546, 160, 40, "I_try = −0.05‰", RED, fill=RED_FILL, size=17)
    f.arrow(382, 566, 402, 566, color=RED, sw=2.2, bend=0.0, head=8)
    f.pill(406, 546, 180, 40, "u_try = −20.05‰", RED, fill=RED_FILL, size=17)
    f.text(70, 616, "负号必须留下", size=17, color=RED, weight="bold")
    f.text(70, 646, "u_try 原样进 clamp", size=16, color=INK)
    f.text(70, 674, "旧代码 fabsf 取绝对值毁回路", size=15, color=MUTED)
    f.stamp(480, 650, "fabsf 曾毁掉回路", size=19, angle=-8)

    f.card(698, 494, 400, 212, BLUE_D, fill=BLUE_FILL)
    f.text(714, 526, "落到定时器", size=20, color=BLUE_D, weight="bold")
    f.metric(714, 566, "3240", "CCR = 900×3600/1000", BLUE_D, value_size=28,
             label_size=15)
    f.metric(916, 566, "3599", "ARR 3600 → 3599", BLUE_D, value_size=28,
             label_size=15)
    f.text(714, 624, "3240 < 3599：不顶格", size=17, color=GREEN_D,
           weight="bold")
    f.text(714, 652, "Δt = 10 ms（TIM4）", size=16, color=INK)
    f.text(714, 680, "F04 deadline ≤2 ms · jitter ≤1 ms", size=15, color=MUTED)
    f.clockface(1032, 652, 24, BLUE_D)

    f.htext(576, 736, "夹钳管现在，棘轮锁历史：负号留下，账本不疯长",
            size=24, color=INK, weight="bold", anchor="middle", hl=True)
    f.text(576, 764,
           "Kp/Ki/α 为起步值非验收值 · F04 指标为拟定验收目标 · "
           "无板上测量，未实测 · 布局示意，非实测",
           size=15, color=MUTED, anchor="middle")
    return f


FIGS = {
    "ch33-cache-dma-kitchen": ch33_cache_dma_kitchen,
    "ch39-pi-saturation-clamp": ch39_pi_saturation_clamp,
}


if __name__ == "__main__":
    names = sys.argv[1:] or list(FIGS)
    STAGE.mkdir(parents=True, exist_ok=True)
    for n in names:
        f = FIGS[n]()
        save(f, str(STAGE / (n + ".svg")))
        print("wrote", STAGE / (n + ".svg"))
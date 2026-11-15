# -*- coding: utf-8 -*-
"""V1b knowledge-track plates: ch11 three timebases, ch14 DMA ownership.

Facts are limited to docs/v1-drivers/11 and docs/v1-drivers/14. Deterministic:
same code -> same SVG bytes -> same PNG pixels.
"""
from pathlib import Path

from hd import (AMBER_FILL, AMBER_STROKE, BLUE_D, GRAY_FILL, GREEN_D, INK,
                MUTED, RED, WHITE, Fig, save)

FIG_DIR = (Path(__file__).resolve().parents[2] / ".temp" / "l0-l5-pass"
           / "figures")


def ch11_three_timebases():
    """SysTick, RTC and the low-power wake timebase: roles and timeline."""
    f = Fig("ch11-three-timebases", "三个时基：心跳、日历与唤醒")
    f.text(64, 122,
           "SysTick 量经过时间，RTC 记日历时间，唤醒时基只负责把芯片从低功耗里叫醒。",
           size=16, color=MUTED)

    cards = [
        (64, BLUE_D, "SysTick（内核）",
         ["24 位递减计数器",
          "168MHz 下 1ms → LOAD=167999",
          "单次最长 99.86ms",
          "掉电重来：延时、超时、RTOS tick"]),
        (400, GREEN_D, "RTC（备份域）",
         ["LSE 32.768kHz，PRL=32767 → 1Hz",
          "VBAT 续电，主电源断了也走",
          "F1 秒计数器 / F4 BCD 日历",
          "闹钟、周期唤醒、时间戳（F4）"]),
        (736, AMBER_STROKE, "唤醒时基（低功耗）",
         ["F4 的 RTC_WUTR：按固定周期自动唤醒",
          "配合 STOP 模式省电",
          "醒来后的时基与时钟见第 18 章"]),
    ]
    for x, color, head, lines in cards:
        f.rect(x, 148, 352, 206, color=color, fill=WHITE, sw=2.3,
               double=False)
        f.text(x + 20, 182, head, size=20, color=color, weight="bold")
        f.multi(x + 20, 216, lines, size=15, color=INK, lh=26)

    f.rect(64, 382, 1024, 250, color=INK, fill=WHITE, sw=2.2, double=False)
    axis_x0, axis_x1 = 262, 1076

    # SysTick lane: 1 ms ticks, 49.7-day wrap.
    f.text(80, 424, "SysTick", size=20, color=BLUE_D, weight="bold")
    f.text(80, 448, "1ms tick", size=15, color=MUTED)
    f.text(axis_x0, 410,
           "LOAD=167999：1ms = 168000 个时钟", size=14.5, color=INK)
    f.text(780, 410, "49.7 天回绕（32 位毫秒计数）", size=14.5, color=RED)
    f.line(axis_x0, 430, axis_x1, 430, color=INK, sw=2.0, amp=0.4)
    for i in range(13):
        x = axis_x0 + i * 66
        f.line(x, 422, x, 438, color=BLUE_D, sw=1.8, amp=0.2)
    f.text(axis_x0, 460, "0", size=13, color=MUTED, anchor="middle")
    f.text(axis_x0 + 66, 460, "1ms", size=13, color=MUTED, anchor="middle")
    f.text(axis_x0 + 132, 460, "2ms", size=13, color=MUTED, anchor="middle")

    # RTC lane: one pulse per second, VBAT keeps it alive.
    f.text(80, 496, "RTC", size=20, color=GREEN_D, weight="bold")
    f.text(80, 520, "1s 分辨率", size=15, color=MUTED)
    f.text(axis_x0, 482,
           "PRL=32767 → 1Hz；读时间按锁存规则", size=14.5, color=INK)
    f.text(780, 482, "VBAT 续电：掉主电也走", size=14.5, color=GREEN_D)
    f.line(axis_x0, 502, axis_x1, 502, color=INK, sw=2.0, amp=0.4)
    for i in range(6):
        x = axis_x0 + i * 162
        f.line(x, 494, x, 510, color=GREEN_D, sw=1.8, amp=0.2)
    f.text(axis_x0 + 162, 532, "每格 1s", size=13, color=MUTED,
           anchor="middle")

    # Wake lane: STOP wait, one wake event, then recheck the clock.
    f.text(80, 568, "唤醒", size=20, color=AMBER_STROKE, weight="bold")
    f.text(80, 592, "低功耗等待", size=15, color=MUTED)
    f.panel(axis_x0, 556, 638, 28, GRAY_FILL, amp=1.2)
    f.text(axis_x0 + 18, 577, "低功耗等待（STOP）", size=14, color=MUTED)
    f.arrow(900, 596, 900, 570, color=AMBER_STROKE, sw=2.8, bend=0.0)
    f.text(916, 574, "RTC 周期唤醒", size=14.5, color=AMBER_STROKE,
           weight="bold")
    f.text(916, 594, "醒来重查时钟", size=13, color=MUTED)
    f.text(axis_x1, 612, "时间 →", size=13, color=MUTED, anchor="end")

    f.htext(84, 682,
            "按问题选：经过时间、日历时间、醒来时刻，各用各的计数器",
            size=21, weight="bold", hl=True)
    f.text(84, 714,
           "SysTick 的 24 位与回绕、RTC 的秒分辨率与 VBAT、唤醒后的时钟，分别对账。",
           size=16, color=MUTED)
    return f


def ch14_dma_buffer_ownership():
    """Half-full / full ownership of a 64-byte DMA ring buffer."""
    f = Fig("ch14-dma-buffer-ownership", "缓冲区归谁：DMA 半满与全满")
    f.text(64, 122,
           "64 字节环形缓冲一分为二：HT 交出前半区，TC 交出后半区；DMA 不停，CPU 要赶在下一圈之前读完。",
           size=16, color=MUTED)

    # The whole buffer, drawn flat as two halves.
    f.text(120, 154, "64 字节环形缓冲（展开成两半）", size=15, color=MUTED)
    f.rect(120, 168, 456, 72, color=BLUE_D, fill=WHITE, sw=2.4,
           double=False)
    f.rect(576, 168, 456, 72, color=GREEN_D, fill=WHITE, sw=2.4,
           double=False)
    f.text(348, 202, "前半区 32 字节", size=19, color=BLUE_D,
           anchor="middle", weight="bold")
    f.text(804, 202, "后半区 32 字节", size=19, color=GREEN_D,
           anchor="middle", weight="bold")
    f.line(576, 158, 576, 250, color=MUTED, sw=1.8, dash="6 6", amp=0.4)
    f.text(576, 266, "半满点：HT", size=14, color=MUTED, anchor="middle")

    # Timeline: who writes and who reads in three moments.
    f.arrow(250, 300, 250, 574, color=MUTED, sw=2.0, bend=0.0)
    f.text(250, 290, "时间", size=13, color=MUTED, anchor="middle")

    rows = [
        (296, "① 起始", BLUE_D,
         ("DMA 正在写", "前半区：DMA 写入", AMBER_FILL, AMBER_STROKE),
         ("CPU 可读", "还没有已交出的半区", WHITE, MUTED)),
        (402, "② HT 后", GREEN_D,
         ("CPU 可读", "前半区已满：CPU 读", WHITE, BLUE_D),
         ("DMA 正在写", "后半区：DMA 写入", AMBER_FILL, AMBER_STROKE)),
        (508, "③ TC 后", RED,
         ("DMA 回卷", "前半区：未读则被覆盖", WHITE, RED),
         ("CPU 可读", "后半区已满：CPU 读", WHITE, GREEN_D)),
    ]
    for y, tag, tag_color, left, right in rows:
        f.text(64, y + 28, tag, size=17, color=tag_color, weight="bold")
        f.text(64, y + 50, "DMA 写 / CPU 读", size=12.5, color=MUTED)
        for x, (head, body, fill, color) in (
                (300, left), (666, right)):
            f.rect(x, y, 360, 64, color=color, fill=fill, sw=2.2,
                   double=False)
            f.text(x + 14, y + 26, head, size=14, color=color, weight="bold")
            f.text(x + 14, y + 49, body, size=15, color=INK)

    # Deadlines and double buffering.
    f.rect(64, 616, 500, 106, color=AMBER_STROKE, fill=WHITE, sw=2.3)
    f.text(84, 646, "期限：115200 8N1 下 32 字节 ≈ 2.78ms", size=17,
           color=AMBER_STROKE, weight="bold")
    f.multi(84, 676, ["从 HT 到 TC 必须处理完半区；",
                      "慢过它，DMA 下一圈直接覆盖。"],
            size=14.5, color=INK, lh=22)

    f.rect(588, 616, 500, 106, color=GREEN_D, fill=WHITE, sw=2.3)
    f.text(608, 646, "双缓冲 DBM/CT：换块，不延长期限", size=17,
           color=GREEN_D, weight="bold")
    f.multi(608, 676, ["F103 没有 DBM，HT/TC 半区只是模拟；",
                       "CPU 超期，整块照样被覆盖。"],
            size=14.5, color=INK, lh=22)

    f.htext(84, 756,
            "NDTR 是写指针的反推，不是帧长；半区交出后，归属才轮到 CPU。",
            size=19, weight="bold", hl=True)
    return f


FIGS = {
    "ch11-three-timebases": ch11_three_timebases,
    "ch14-dma-buffer-ownership": ch14_dma_buffer_ownership,
}

if __name__ == "__main__":
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    for name, fn in FIGS.items():
        f = fn()
        path = FIG_DIR / (name + ".svg")
        save(f, str(path))
        print("wrote", path)

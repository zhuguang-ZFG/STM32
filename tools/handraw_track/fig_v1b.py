# -*- coding: utf-8 -*-
"""V1b knowledge-track plates: ch11 three timebases, ch14 DMA ownership.

Facts are limited to docs/v1-drivers/11 and docs/v1-drivers/14. Deterministic:
same code -> same SVG bytes -> same PNG pixels.
"""
from pathlib import Path

from hd import (AMBER_PALE, AMBER_STROKE, BLUE_D, BLUE_FILL, GRAY_FILL,
                GREEN_D, GREEN_FILL, INK, MUTED, RED, RED_FILL, WHITE, Fig,
                save)

FIG_DIR = (Path(__file__).resolve().parents[2] / ".temp" / "l0-l5-pass"
           / "figures")
MONO = "'Consolas','Courier New',monospace"


def ch11_three_timebases():
    """SysTick, RTC and the low-power wake timebase: roles and timeline."""
    f = Fig("ch11-three-timebases", "三个时基：心跳、日历与唤醒",
            title_color=BLUE_D, tag="CH 11 · 时基与低功耗")
    f.text(64, 126,
           "SysTick 量经过时间，RTC 记日历时间，唤醒时基只负责把芯片从低功耗里叫醒。",
           size=19, color=MUTED)

    cards = [
        (64, BLUE_D, BLUE_FILL, "SysTick（内核）",
         ["24 位递减计数器",
          "168MHz 下 1ms → LOAD=167999",
          "单次最长 99.86ms",
          "掉电重来：延时、超时、RTOS tick"]),
        (416, GREEN_D, GREEN_FILL, "RTC（备份域）",
         ["LSE 32.768kHz，PRL=32767 → 1Hz",
          "VBAT 续电，主电源断了也走",
          "F1 秒计数器 / F4 BCD 日历",
          "闹钟、周期唤醒、时间戳（F4）"]),
        (768, AMBER_STROKE, AMBER_PALE, "唤醒时基",
         ["F4 的 RTC_WUTR：按固定周期自动唤醒",
          "配合 STOP 模式省电",
          "醒来后的时基与时钟见第 18 章"]),
    ]
    for x, color, fill, head, lines in cards:
        f.card(x, 160, 336 if x < 768 else 320, 210, color, fill=fill)
        f.clockface(x + 46, 205, 26, color)
        f.text(x + 86, 200, head, size=20, color=color, weight="bold")
        f.multi(x + 20, 240, lines, size=15, color=INK, lh=26)

    f.card(64, 392, 1024, 250, BLUE_D, fill=WHITE)
    axis_x0, axis_x1 = 262, 1076

    # SysTick lane: 1 ms ticks, 49.7-day wrap.
    f.text(84, 432, "SysTick", size=20, color=BLUE_D, weight="bold")
    f.text(84, 456, "1ms tick", size=14, color=MUTED)
    f.text(axis_x0, 414,
           "LOAD=167999：1ms = 168000 个时钟", size=14.5, color=INK)
    f.text(780, 414, "49.7 天回绕（32 位毫秒计数）", size=14.5, color=RED)
    f.line(axis_x0, 436, axis_x1, 436, color=INK, sw=2.0, amp=0.4)
    for i in range(13):
        x = axis_x0 + i * 66
        f.line(x, 428, x, 444, color=BLUE_D, sw=1.8, amp=0.2)
    f.text(axis_x0, 462, "0", size=13, color=MUTED, anchor="middle")
    f.text(axis_x0 + 66, 462, "1ms", size=13, color=MUTED, anchor="middle")
    f.text(axis_x0 + 132, 462, "2ms", size=13, color=MUTED, anchor="middle")

    # RTC lane: one pulse per second, VBAT keeps it alive.
    f.text(84, 504, "RTC", size=20, color=GREEN_D, weight="bold")
    f.text(84, 528, "1s 分辨率", size=14, color=MUTED)
    f.text(axis_x0, 486,
           "PRL=32767 → 1Hz；读时间按锁存规则", size=14.5, color=INK)
    f.text(780, 486, "VBAT 续电：掉主电也走", size=14.5, color=GREEN_D)
    f.line(axis_x0, 508, axis_x1, 508, color=INK, sw=2.0, amp=0.4)
    for i in range(6):
        x = axis_x0 + i * 162
        f.line(x, 500, x, 516, color=GREEN_D, sw=1.8, amp=0.2)
    f.text(axis_x0 + 162, 538, "每格 1s", size=13, color=MUTED,
           anchor="middle")

    # Wake lane: STOP wait, one wake event, then recheck the clock.
    f.text(84, 576, "唤醒", size=20, color=AMBER_STROKE, weight="bold")
    f.text(84, 600, "低功耗等待", size=14, color=MUTED)
    f.panel(axis_x0, 562, 638, 28, GRAY_FILL, amp=1.2)
    f.text(axis_x0 + 18, 583, "低功耗等待（STOP）", size=14, color=MUTED)
    f.arrow(900, 602, 900, 576, color=AMBER_STROKE, sw=2.8, bend=0.0)
    f.text(916, 580, "RTC 周期唤醒", size=14.5, color=AMBER_STROKE,
           weight="bold")
    f.text(916, 600, "醒来重查时钟", size=13, color=MUTED)
    f.text(axis_x1, 620, "时间 →", size=13, color=MUTED, anchor="end")

    f.htext(576, 690,
            "按问题选：经过时间、日历时间、醒来时刻，各用各的计数器",
            size=22, color=INK, weight="bold", anchor="middle", hl=True)
    f.text(576, 724,
           "SysTick 的 24 位与回绕、RTC 的秒分辨率与 VBAT、唤醒后的时钟，分别对账；布局示意，非实测。",
           size=15, color=MUTED, anchor="middle")
    return f


def ch14_dma_buffer_ownership():
    """Half-full / full ownership of a 64-byte DMA ring buffer."""
    f = Fig("ch14-dma-buffer-ownership", "缓冲区归谁：DMA 半满与全满",
            title_color=GREEN_D, tag="CH 14 · DMA 与缓冲")
    f.text(64, 126,
           "64 字节环形缓冲一分为二：HT 交出前半区，TC 交出后半区；DMA 不停，CPU 要赶在下一圈之前读完。",
           size=19, color=MUTED)

    # The whole buffer, drawn flat as two halves.
    f.text(120, 158, "64 字节环形缓冲（展开成两半）", size=15, color=MUTED)
    f.rect(120, 172, 456, 72, color=BLUE_D, fill=BLUE_FILL, sw=2.4,
           double=False)
    f.rect(576, 172, 456, 72, color=GREEN_D, fill=GREEN_FILL, sw=2.4,
           double=False)
    f.text(348, 206, "前半区 32 字节", size=19, color=BLUE_D,
           anchor="middle", weight="bold")
    f.text(804, 206, "后半区 32 字节", size=19, color=GREEN_D,
           anchor="middle", weight="bold")
    f.line(576, 162, 576, 254, color=MUTED, sw=1.8, dash="6 6", amp=0.4)
    f.text(576, 270, "半满点：HT", size=14, color=MUTED, anchor="middle")

    # Timeline: who writes and who reads in three moments.
    f.arrow(250, 304, 250, 578, color=MUTED, sw=2.0, bend=0.0)
    f.text(250, 294, "时间", size=13, color=MUTED, anchor="middle")

    rows = [
        (300, "① 起始", BLUE_D,
         ("DMA 正在写", "前半区：DMA 写入", AMBER_PALE, AMBER_STROKE),
         ("CPU 可读", "还没有已交出的半区", WHITE, MUTED)),
        (406, "② HT 后", GREEN_D,
         ("CPU 可读", "前半区已满：CPU 读", WHITE, BLUE_D),
         ("DMA 正在写", "后半区：DMA 写入", AMBER_PALE, AMBER_STROKE)),
        (512, "③ TC 后", RED,
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
    f.card(64, 616, 500, 106, AMBER_STROKE, fill=AMBER_PALE)
    f.text(84, 646, "期限：115200 8N1 下 32 字节 ≈ 2.78ms", size=17,
           color=AMBER_STROKE, weight="bold")
    f.multi(84, 676, ["从 HT 到 TC 必须处理完半区；",
                      "慢过它，DMA 下一圈直接覆盖。"],
            size=14.5, color=INK, lh=22)

    f.card(588, 616, 500, 106, GREEN_D, fill=GREEN_FILL)
    f.text(608, 646, "双缓冲 DBM/CT：换块，不延长期限", size=17,
           color=GREEN_D, weight="bold")
    f.multi(608, 676, ["F103 没有 DBM，HT/TC 半区只是模拟；",
                       "CPU 超期，整块照样被覆盖。"],
            size=14.5, color=INK, lh=22)

    f.htext(576, 756,
            "NDTR 是写指针的反推，不是帧长；半区交出后，归属才轮到 CPU。",
            size=20, color=INK, weight="bold", anchor="middle", hl=True)
    return f


def ch14_ndtr_units():
    """NDTR counts items, not bytes: '3 left' means 61 bytes (8-bit) or
    122 bytes (halfword). Facts from ch14 opening table."""
    f = Fig("ch14-ndtr-units",
            "NDTR 数的是项，不是字节：还剩 3 是多少？",
            title_color=BLUE_D, tag="CH 14 · DMA 与缓冲")
    f.text(64, 126,
           "同一个「还剩 3」，字节宽度下是已写 61 字节，半字宽度下是已写 122 字节——读 NDTR 先问宽度。",
           size=19, color=MUTED)

    # ---- left: byte items ----
    f.card(64, 156, 500, 300, BLUE_D, fill=BLUE_FILL)
    f.text(84, 190, "F103 USART1_RX · 8 位环形", size=19, color=BLUE_D,
           weight="bold")
    f.text(84, 216, "每项 1 字节 · 64 字节环 · NDTR 初值 64", size=14,
           color=MUTED)
    f.metric(96, 268, "已写 61 字节", "64 − 3 = 61 项 × 1 B", BLUE_D)
    f.text(84, 322, "半满点：32 字节 · 115200 8N1 下 ≈ 2.78 ms", size=15,
           color=INK)
    f.text(84, 352, "模差位置：(64 − 3) mod 64 = 61", size=14.5,
           color=INK, font=MONO)
    f.text(84, 382, "下一圈要从 61 跳回 0——", size=14, color=MUTED)
    f.text(84, 408, "模差不是累计进度", size=14.5, color=RED,
           weight="bold")

    # ---- right: halfword items ----
    f.card(588, 156, 500, 300, GREEN_D, fill=GREEN_FILL)
    f.text(608, 190, "F407 ADC 环形 · 16 位", size=19, color=GREEN_D,
           weight="bold")
    f.text(608, 216, "每项 2 字节 · 64 个采样 · NDTR 初值 64", size=14,
           color=MUTED)
    f.metric(620, 268, "已写 122 字节", "64 − 3 = 61 采样 × 2 B", GREEN_D)
    f.text(608, 322, "半满点：32 采样 = 64 字节", size=15, color=INK)
    f.text(608, 352, "同一个 NDTR 读数，翻倍的字节", size=14.5, color=INK)
    f.text(608, 382, "把 NDTR 当字节的下场：", size=14, color=MUTED)
    f.text(608, 408, "后半段从奇数地址开始切，整体错位", size=14.5,
           color=RED, weight="bold")

    # ---- bottom: increments + ceiling ----
    f.panel(64, 486, 1024, 110, AMBER_PALE, amp=1.6)
    f.rect(64, 486, 1024, 110, color=AMBER_STROKE, sw=1.8, fill=None,
           amp=1.6)
    f.text(88, 518, "两次快照之间可能转了不止一圈：增量 = (新位置 − 上次位置 + 长度) mod 长度",
           size=15.5, color=INK)
    f.text(88, 546, "整圈丢失模差看不见——错误标志、HT+TC 积压、位置不动却报 TC，宁可丢弃计数，不猜增量",
           size=14.5, color=MUTED)
    f.text(88, 576, "NDTR 只有 16 位：一轮最多 65535 项（8 位 65535 B，半字 131070 B），更大的块分段装填",
           size=14.5, color=MUTED)

    f.htext(64, 700, "项数 × 每项字节 = 已写字节；NDTR 自己不报单位",
            size=22, color=INK, weight="bold", hl=True)
    f.text(576, 730,
           "数字取自本章开头换算表与 dma_consume() 判据；推导口径，非实测。",
           size=14, color=MUTED, anchor="middle")
    return f


def ch11_load_plus_one():
    """Period = LOAD + 1: forget the minus one and the day drifts 514 ms;
    24-bit ceiling. Facts from ch11 (probe.c:45-48, 128-186)."""
    f = Fig("ch11-load-plus-one",
            "周期 = LOAD + 1：忘减一，日漂 514 ms",
            title_color=AMBER_STROKE, tag="CH 11 · SysTick")
    f.text(64, 126,
           "次数一样，相位不对：短延时看不出，长期计时才会暴露——这正是忘减一不易察觉的原因。",
           size=19, color=MUTED)

    # ---- left: correct config ----
    f.card(64, 156, 500, 300, GREEN_D, fill=GREEN_FILL)
    f.text(84, 190, "LOAD = 167999", size=22, color=GREEN_D, weight="bold",
           font=MONO)
    f.text(84, 216, "168 MHz 要 1 ms：168000 个时钟，减一落笔", size=14,
           color=MUTED)
    f.metric(96, 268, "1.000000 ms", "重载周期 = LOAD + 1 = 168000", GREEN_D)
    f.text(84, 322, "倒数到 0，下一个周期才重载并置 COUNTFLAG", size=15,
           color=INK)
    f.text(84, 352, "probe：1680000 周期恰好归零重载 10 次", size=14.5,
           color=INK, font=MONO)
    f.text(84, 386, "第 10 次重载落在第 1512001 个时钟", size=14.5,
           color=MUTED, font=MONO)
    f.text(84, 424, "「减一」来自重载时序，可以逐拍数出来", size=14,
           color=MUTED)

    # ---- right: forgot the minus one ----
    f.card(588, 156, 500, 300, RED, fill=RED_FILL)
    f.text(608, 190, "LOAD = 168000（忘减一）", size=20, color=RED,
           weight="bold", font=MONO)
    f.text(608, 216, "同样跑 1680000 周期，照样重载 10 次", size=14,
           color=MUTED)
    f.metric(620, 268, "5.95 ppm", "每 tick 慢 1/168000", RED)
    f.metric(850, 268, "514 ms/天", "86400 s × 1000 ÷ 168000", RED)
    f.text(608, 322, "第 10 次重载落在第 1512010 个时钟：差 9 拍", size=14.5,
           color=INK, font=MONO)
    f.text(608, 356, "1 ms 短延时看不出；数据记录器、日历时基", size=14.5,
           color=INK)
    f.text(608, 384, "才会把它暴露成漂移", size=14.5, color=INK)
    f.text(608, 424, "次数一样 → 测试测不出，只能靠周期对账", size=14,
           color=MUTED)

    # ---- bottom: 24-bit ceiling ----
    f.panel(64, 486, 1024, 110, GRAY_FILL, amp=1.6)
    f.rect(64, 486, 1024, 110, color=MUTED, sw=1.6, fill=None, amp=1.6)
    f.text(88, 518, "24 位上限：LOAD_MAX = 16777215 → 168 MHz 下最长单次 ≈ 99.86 ms",
           size=15.5, color=INK, weight="bold")
    f.text(88, 548, "请求 100 ms：SysTick_Config 返回 1 拒配，寄存器一个没动——所以要查返回值",
           size=14.5, color=INK)
    f.text(88, 576, "不查、强写 & 0xFFFFFF → LOAD=22783，tick 135.6 µs，ISR 以 737 倍速狂跳",
           size=14.5, color=RED, weight="bold")

    f.htext(64, 700, "要 168000 个时钟就写 167999；更长周期换 HCLK/8 或 32 位 TIM",
            size=21, color=INK, weight="bold", hl=True)
    f.text(576, 730,
           "读数取自本章 probe 模型实测（probe.c:128-186）；推导口径，非示波器波形。",
           size=14, color=MUTED, anchor="middle")
    return f


FIGS = {
    "ch11-three-timebases": ch11_three_timebases,
    "ch11-load-plus-one": ch11_load_plus_one,
    "ch14-dma-buffer-ownership": ch14_dma_buffer_ownership,
    "ch14-ndtr-units": ch14_ndtr_units,
}

if __name__ == "__main__":
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    for name, fn in FIGS.items():
        f = fn()
        path = FIG_DIR / (name + ".svg")
        save(f, str(path))
        print("wrote", path)
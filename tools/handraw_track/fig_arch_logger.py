# -*- coding: utf-8 -*-
"""Logger data-flow plate (ch41).

Facts pinned to the chapter and common core: SAMPLE is 64 B little-endian;
the queue is 16 x 64 B = 1 KB, which buffers 1.6 s at the 100 ms period.
When full, the new sample is rejected (``dropped`` grows) while the 16
already queued samples stay; the sequence number is consumed before the
capacity check, so the host sees a sequence gap. The supervisor compares
now - last_ms against 2500/1500 ms every 50 ms after a 3000 ms startup
grace and owns the watchdog feed; communication progress is recorded
before TX and does not require a successful send. UART has no hardware
flow control.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hd import *  # noqa: E402,F401,F403


def _source(f, y, title, l1, l2, color):
    x, w, h = 40, 230, 84
    f.rect(x, y, w, h, color=color, fill=WHITE, sw=2.4)
    f.text(x + 12, y + 22, title, size=18, color=color, weight="bold")
    f.text(x + 12, y + 49, l1, size=13, color=INK)
    f.text(x + 12, y + 71, l2, size=13, color=MUTED)


def _slot(f, x, y, w, h, label, color=GREEN, fill=WHITE, dash=None):
    f.rect(x, y, w, h, color=color, fill=fill, sw=1.8, r=5, amp=1.2,
           dash=dash, double=False)
    f.text(x + w / 2, y + 23, label, size=11, color=MUTED, anchor="middle")


def logger_flow():
    f = Fig("arch-logger-flow", "记录器数据流：64 B 一帧，满则丢新")
    f.text(576, 122, "两板共用任务层与核心；端口只换传感器与串口",
           size=17, color=MUTED, anchor="middle")

    # -- producers ------------------------------------------------------
    _source(f, 140, "F407 采样输入", "ADC PA0 · TIM2 TRGO",
            "DMA2 Stream0 · IRQ56", BLUE_D)
    _source(f, 232, "S3 采样输入", "QMI8658 · I2C", "GPIO1/2", GREEN_D)
    f.arrow(272, 182, 296, 220, color=BLUE_D, sw=2.4, bend=0.10)
    f.arrow(272, 274, 296, 220, color=GREEN_D, sw=2.4, bend=-0.10)

    # -- tasks ----------------------------------------------------------
    f.rect(300, 155, 190, 130, color=BLUE_D, fill=WHITE, sw=2.5)
    f.text(314, 184, "sample 任务", size=19, color=BLUE_D, weight="bold")
    f.text(314, 214, "100 ms 周期", size=15, color=INK)
    f.text(314, 240, "取传感器快照", size=14, color=INK)
    f.text(314, 264, "超期由监督点名", size=13, color=MUTED)

    f.rect(510, 155, 200, 130, color=GREEN_D, fill=WHITE, sw=2.5)
    f.text(524, 184, "滤波 + 封帧", size=19, color=GREEN_D, weight="bold")
    f.text(524, 214, "整数 IIR", size=15, color=INK)
    f.text(524, 240, "SAMPLE 64 B", size=15, color=GREEN_D, weight="bold")
    f.text(524, 264, "序号在这里消耗", size=13, color=MUTED)
    f.arrow(492, 220, 508, 220, color=BLUE_D, sw=2.4, bend=0.0)

    # -- queue ----------------------------------------------------------
    f.rect(745, 120, 367, 252, color=AMBER_STROKE, fill=WHITE, sw=2.6)
    f.text(763, 148, "队列 16 槽 × 64 B = 1 KB", size=17, color=AMBER_STROKE,
           weight="bold")
    f.text(1092, 148, "满", size=17, color=RED, anchor="end", weight="bold")
    for row in range(4):
        for col in range(4):
            _slot(f, 786 + col * 74, 165 + row * 44, 64, 36, "64B")
    f.text(763, 358, "满：dropped +1，已入队的 16 条不动", size=13, color=RED,
           weight="bold")

    # full queue rejects the new sample; consumer still drains the head
    f.arrow(712, 220, 742, 220, color=RED, sw=3.0, bend=0.0)
    f.line(721, 214, 733, 226, color=RED, sw=2.6)
    f.line(733, 214, 721, 226, color=RED, sw=2.6)

    # -- consumer / host ------------------------------------------------
    f.rect(745, 392, 367, 80, color=BLUE_D, fill=WHITE, sw=2.4)
    f.text(761, 416, "comm 任务", size=18, color=BLUE_D, weight="bold")
    f.text(761, 445, "取队首，发 SAMPLE + STATUS", size=14, color=INK)
    f.text(761, 466, "STATUS 带 dropped 与 high_water", size=12, color=MUTED)
    f.arrow(900, 374, 900, 390, color=GREEN_D, sw=2.4, bend=0.0)

    f.rect(745, 487, 367, 188, color=GREEN_D, fill=WHITE, sw=2.4)
    f.text(761, 510, "UART → 主机", size=18, color=GREEN_D, weight="bold")
    f.text(761, 540, "无硬件流控：发送成功 ≠ 收到", size=14, color=RED)
    f.text(761, 565, "主机按 sequence 查缺口", size=14, color=INK)
    for i, (lab, ok) in enumerate([("37", True), ("38", True),
                                   ("39", False), ("40", True)]):
        x = 761 + i * 64
        _slot(f, x, 578, 56, 32, lab, color=RED if not ok else GREEN,
              fill=WHITE, dash="5 4" if not ok else None)
        if not ok:
            f.line(x + 10, 584, x + 46, 604, color=RED, sw=2.4)
            f.line(x + 46, 584, x + 10, 604, color=RED, sw=2.4)
    f.text(761, 633, "39 缺：新样本被拒，序号已消耗", size=13, color=MUTED)
    f.text(761, 662, "缺口 = 丢帧，不是解析错误", size=15, color=RED,
           weight="bold")

    # -- byte account ---------------------------------------------------
    f.rect(40, 320, 680, 92, color=BLUE_D, fill=WHITE, sw=2.3)
    f.text(60, 346, "SAMPLE 64 B（小端）", size=17, color=BLUE_D, weight="bold")
    f.text(60, 372,
           "seq 4 + ts 4 + gen 4 + type 1 + valid 1 + status 2 + raw 24 + filt 24",
           size=13, color=INK)
    f.text(60, 398, "= 64 B；16 条 = 1 KB；100 ms 周期下缓冲 1.6 s", size=14,
           color=GREEN_D, weight="bold")

    # -- supervisor -----------------------------------------------------
    f.rect(40, 427, 680, 110, color=AMBER_STROKE, fill=WHITE, sw=2.3)
    f.text(60, 453, "supervisor：每 50 ms 查 last_ms", size=17,
           color=AMBER_STROKE, weight="bold")
    f.text(60, 479, "sample：now − last <2500 ms；comm：<1500 ms",
           size=14, color=INK)
    f.text(60, 503, "50 ms 轮询；宽限 3000 ms；2500/100=25 周期，不数次数",
           size=14, color=INK)
    f.text(60, 526, "喂狗：F407 IWDG / S3 TWDT；comm 进度不要求发送成功",
           size=13, color=MUTED)

    # -- drop policy ----------------------------------------------------
    f.rect(40, 547, 680, 113, color=RED, fill=WHITE, sw=2.3)
    f.text(60, 573, "为什么丢新，不丢旧", size=17, color=RED, weight="bold")
    f.text(60, 599, "已入队的 16 条按序保留；新样本被拒，丢弃计数 +1",
           size=14, color=INK)
    f.text(60, 623, "队列满 = 产量 > 消费能力；先看 dropped 与 high_water",
           size=14, color=INK)
    f.text(60, 647, "两个计数都进 STATUS，积压对主机可见", size=13,
           color=MUTED)

    f.htext(576, 736,
            "64 B 进队，16 槽封顶；满则丢新并计数，主机靠序号缺口发现。",
            size=19, color=AMBER_STROKE, anchor="middle", weight="bold",
            hl=True, hl_fill=AMBER_FILL)
    return f


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[2] / "assets" / "illustrations" / "handraw"
    save(logger_flow(), str(out / "arch-logger-flow.svg"))
    print("wrote arch-logger-flow.svg")

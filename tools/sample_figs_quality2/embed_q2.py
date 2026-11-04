#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Embed ch04/05/07/08 quality figures into zh+en chapters."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

BLOCK = """
<p align="center">
  <img src="{src}" width="{width}" alt="{alt}">
  <br><sub>{cap}</sub>
</p>
"""


def _insert_before(path: Path, marker: str, needle: str, block: str) -> bool:
    text = path.read_text(encoding="utf-8")
    if needle in text:
        print("skip", path.name, needle)
        return False
    if marker not in text:
        raise SystemExit(f"marker missing in {path}: {marker!r}")
    # insert immediately BEFORE the marker heading (so figure sits above next section)
    # Actually pilot used insert before marker content - place figure after the heading line.
    idx = text.index(marker)
    # find end of heading line
    nl = text.find("\n", idx)
    if nl < 0:
        raise SystemExit(f"no newline after marker in {path}")
    insert_at = nl + 1
    text = text[:insert_at] + "\n" + block + "\n" + text[insert_at:]
    path.write_text(text, encoding="utf-8")
    print("+", path.parent.name, path.name, "<-", needle)
    return True


EMBEDS = [
    # ---- ch04 ----
    {
        "zh": ROOT / "docs" / "04-中断与NVIC.md",
        "en": ROOT / "docs" / "en" / "04-interrupts-nvic.md",
        "marker_zh": "### 2. NVIC 优先级机制",
        "marker_en": "### 2. How NVIC priority works",
        "needle": "sample-04-priority-group.svg",
        "src_zh": "../assets/diagrams/sample-04-priority-group.svg",
        "src_en": "../../assets/diagrams/sample-04-priority-group.svg",
        "width": 760,
        "alt_zh": "NVIC 抢占位与亚优先级分组",
        "alt_en": "NVIC preempt versus subpriority grouping",
        "cap_zh": "▲ 自绘。AIRCR PRIGROUP 切分 4 个优先级位；同抢占互不打断。",
        "cap_en": "▲ Drawn for this book. AIRCR PRIGROUP splits four priority bits; equal preempt does not nest.",
    },
    {
        "zh": ROOT / "docs" / "04-中断与NVIC.md",
        "en": ROOT / "docs" / "en" / "04-interrupts-nvic.md",
        "marker_zh": "### 10. 中断响应开销与优化机制",
        "marker_en": "### 10. Interrupt overhead, and the hardware shortcuts",
        "needle": "sample-04-tail-chaining.svg",
        "src_zh": "../assets/diagrams/sample-04-tail-chaining.svg",
        "src_en": "../../assets/diagrams/sample-04-tail-chaining.svg",
        "width": 760,
        "alt_zh": "Cortex-M3 入栈出栈与尾链周期",
        "alt_en": "Cortex-M3 entry, exit, and tail-chaining cycles",
        "cap_zh": "▲ 自绘。入栈约 12 周期；尾链约 6。别空谈“6 周期 ISR”。",
        "cap_en": "▲ Drawn for this book. ~12-cycle entry; ~6-cycle tail-chain. The 6-cycle figure is for tail-chain only, not the ISR body.",
    },
    {
        "zh": ROOT / "docs" / "04-中断与NVIC.md",
        "en": ROOT / "docs" / "en" / "04-interrupts-nvic.md",
        "marker_zh": "### 4. EXTI 外部中断",
        "marker_en": "### 4. EXTI external interrupts",
        "needle": "sample-04-exti-line-map.svg",
        "src_zh": "../assets/diagrams/sample-04-exti-line-map.svg",
        "src_en": "../../assets/diagrams/sample-04-exti-line-map.svg",
        "width": 760,
        "alt_zh": "EXTI 线经 AFIO 选择 GPIO 端口",
        "alt_en": "EXTI line mux through AFIO to one GPIO port",
        "cap_zh": "▲ 自绘。每条 EXTI 线只选一个端口；5–9 / 10–15 共用 IRQ。",
        "cap_en": "▲ Drawn for this book. One port per EXTI line; EXTI5-9 and 10-15 share IRQs.",
    },
    {
        "zh": ROOT / "docs" / "04-中断与NVIC.md",
        "en": ROOT / "docs" / "en" / "04-interrupts-nvic.md",
        "marker_zh": "## 关键插图",
        "marker_en": "## Key figures",
        "needle": "sample-04-nvic-preempt-flow.svg",
        "src_zh": "../assets/animations/sample-04-nvic-preempt-flow.svg",
        "src_en": "../../assets/animations/sample-04-nvic-preempt-flow.svg",
        "width": 720,
        "alt_zh": "NVIC 抢占：EXTI0 打断 TIM2 再返回",
        "alt_en": "NVIC preemption: EXTI0 interrupts TIM2 then returns",
        "cap_zh": "▲ 自绘矢量动画（FA-002）。TIM2→EXTI0→入栈→ISR→返回。",
        "cap_en": "▲ Hand-drawn CSS animation (FA-002). TIM2→EXTI0→stack→ISR→return.",
    },
    # ---- ch05 ----
    {
        "zh": ROOT / "docs" / "05-定时器与PWM.md",
        "en": ROOT / "docs" / "en" / "05-timer-pwm.md",
        "marker_zh": "### 2. 时基公式",
        "marker_en": "### 2. Time-base formulas",
        "needle": "sample-05-timebase-math.svg",
        "src_zh": "../assets/diagrams/sample-05-timebase-math.svg",
        "src_en": "../../assets/diagrams/sample-05-timebase-math.svg",
        "width": 760,
        "alt_zh": "72 MHz 经 PSC/ARR 得到 1 kHz PWM",
        "alt_en": "72 MHz through PSC/ARR to 1 kHz PWM",
        "cap_zh": "▲ 自绘。PSC=71 ARR=999 CCR=500 与章内宏一致。",
        "cap_en": "▲ Drawn for this book. PSC=71 ARR=999 CCR=500 matches the chapter macros.",
    },
    {
        "zh": ROOT / "docs" / "05-定时器与PWM.md",
        "en": ROOT / "docs" / "en" / "05-timer-pwm.md",
        "marker_zh": "### 3. 计数模式与影子寄存器",
        "marker_en": "### 3. Count modes and shadow registers",
        "needle": "sample-05-shadow-regs.svg",
        "src_zh": "../assets/diagrams/sample-05-shadow-regs.svg",
        "src_en": "../../assets/diagrams/sample-05-shadow-regs.svg",
        "width": 760,
        "alt_zh": "ARR/CCR 预装载与更新事件",
        "alt_en": "ARR/CCR preload and the update event",
        "cap_zh": "▲ 自绘。ARPE/OCxPE：写预装载，UE 才锁进影子。",
        "cap_en": "▲ Drawn for this book. ARPE/OCxPE: write preload; latch on update event.",
    },
    {
        "zh": ROOT / "docs" / "05-定时器与PWM.md",
        "en": ROOT / "docs" / "en" / "05-timer-pwm.md",
        "marker_zh": "### 6. 互补输出与死区（高级定时器）",
        "marker_en": "### 6. Complementary outputs and dead time (advanced timers)",
        "needle": "sample-05-deadtime.svg",
        "src_zh": "../assets/diagrams/sample-05-deadtime.svg",
        "src_en": "../../assets/diagrams/sample-05-deadtime.svg",
        "width": 760,
        "alt_zh": "互补 PWM 与死区避免直通",
        "alt_en": "Complementary PWM with dead time against shoot-through",
        "cap_zh": "▲ 自绘。BDTR DTG + MOE；半桥实验才需要。",
        "cap_en": "▲ Drawn for this book. BDTR DTG + MOE; for half-bridge labs only.",
    },
    {
        "zh": ROOT / "docs" / "05-定时器与PWM.md",
        "en": ROOT / "docs" / "en" / "05-timer-pwm.md",
        "marker_zh": "## 关键插图",
        "marker_en": "## Key figures",
        "needle": "sample-05-pwm-edge-flow.svg",
        "src_zh": "../assets/animations/sample-05-pwm-edge-flow.svg",
        "src_en": "../../assets/animations/sample-05-pwm-edge-flow.svg",
        "width": 720,
        "alt_zh": "PWM：CNT 走到 CCR=500 翻电平",
        "alt_en": "PWM: CNT reaches CCR=500 and the level flips",
        "cap_zh": "▲ 自绘矢量动画（FA-002）。1 kHz、50% 高电平 500 µs。",
        "cap_en": "▲ Hand-drawn CSS animation (FA-002). 1 kHz, 50% high for 500 µs.",
    },
    # ---- ch07 ----
    {
        "zh": ROOT / "docs" / "07-I2C总线.md",
        "en": ROOT / "docs" / "en" / "07-i2c.md",
        "marker_zh": "### 2. 时序与协议",
        "marker_en": "### 2. Timing and the protocol",
        "needle": "sample-07-start-ack.svg",
        "src_zh": "../assets/diagrams/sample-07-start-ack.svg",
        "src_en": "../../assets/diagrams/sample-07-start-ack.svg",
        "width": 760,
        "alt_zh": "I2C START、0x78 寻址与 ACK",
        "alt_en": "I2C START, 0x78 address, and ACK",
        "cap_zh": "▲ 自绘。HAL 0x3C<<1=0x78；第 9 拍从机拉低 ACK。",
        "cap_en": "▲ Drawn for this book. HAL 0x3C<<1=0x78; slave ACK on the 9th clock.",
    },
    {
        "zh": ROOT / "docs" / "07-I2C总线.md",
        "en": ROOT / "docs" / "en" / "07-i2c.md",
        "marker_zh": "### 1. 电气特性",
        "marker_en": "### 1. Electrical behavior",
        "needle": "sample-07-pullup-cap.svg",
        "src_zh": "../assets/diagrams/sample-07-pullup-cap.svg",
        "src_en": "../../assets/diagrams/sample-07-pullup-cap.svg",
        "width": 760,
        "alt_zh": "上拉电阻与总线电容对照",
        "alt_en": "Pull-up resistance versus bus capacitance",
        "cap_zh": "▲ 自绘。4.7 k 是起点；长线/多从机要加测量。",
        "cap_en": "▲ Drawn for this book. 4.7 k is a starting point; long buses need measurement.",
    },
    {
        "zh": ROOT / "docs" / "07-I2C总线.md",
        "en": ROOT / "docs" / "en" / "07-i2c.md",
        "marker_zh": "### 10. 重复起始（Sr）",
        "marker_en": "### 10. Repeated start (Sr)",
        "needle": "sample-07-sr-restart.svg",
        "src_zh": "../assets/diagrams/sample-07-sr-restart.svg",
        "src_en": "../../assets/diagrams/sample-07-sr-restart.svg",
        "width": 760,
        "alt_zh": "写寄存器后 Sr 再读，中间无 STOP",
        "alt_en": "Write register, Sr, then read — no STOP in between",
        "cap_zh": "▲ 自绘。MPU6050/EEPROM 典型：写指针 → Sr → 读。",
        "cap_en": "▲ Drawn for this book. MPU6050/EEPROM pattern: write pointer → Sr → read.",
    },
    {
        "zh": ROOT / "docs" / "07-I2C总线.md",
        "en": ROOT / "docs" / "en" / "07-i2c.md",
        "marker_zh": "## 关键插图",
        "marker_en": "## Key figures",
        "needle": "sample-07-i2c-ack-flow.svg",
        "src_zh": "../assets/animations/sample-07-i2c-ack-flow.svg",
        "src_en": "../../assets/animations/sample-07-i2c-ack-flow.svg",
        "width": 720,
        "alt_zh": "I2C 寻址应答动画：START 到 ACK",
        "alt_en": "I2C address ACK animation: START through ACK",
        "cap_zh": "▲ 自绘矢量动画（FA-002）。0x78 → 第 9 拍 ACK；NACK 见排查卡。",
        "cap_en": "▲ Hand-drawn CSS animation (FA-002). 0x78 → 9th-clock ACK; NACK stays on the triage card.",
    },
    # ---- ch08 ----
    {
        "zh": ROOT / "docs" / "08-SPI总线.md",
        "en": ROOT / "docs" / "en" / "08-spi.md",
        "marker_zh": "### 2. CPOL/CPHA 四种模式",
        "marker_en": "### 2. The four CPOL/CPHA modes",
        "needle": "sample-08-mode0-edges.svg",
        "src_zh": "../assets/diagrams/sample-08-mode0-edges.svg",
        "src_en": "../../assets/diagrams/sample-08-mode0-edges.svg",
        "width": 760,
        "alt_zh": "SPI Mode0 采样边沿与 Flash 默认",
        "alt_en": "SPI Mode0 sampling edges and flash default",
        "cap_zh": "▲ 自绘。CPOL0 CPHA0：第一个上升沿采样；JEDEC Flash 常用。",
        "cap_en": "▲ Drawn for this book. CPOL0 CPHA0: sample on first rising edge; common JEDEC flash default.",
    },
    {
        "zh": ROOT / "docs" / "08-SPI总线.md",
        "en": ROOT / "docs" / "en" / "08-spi.md",
        "marker_zh": "### 3. 速率与分频",
        "marker_en": "### 3. Rate and the divider",
        "needle": "sample-08-br-table.svg",
        "src_zh": "../assets/diagrams/sample-08-br-table.svg",
        "src_en": "../../assets/diagrams/sample-08-br-table.svg",
        "width": 760,
        "alt_zh": "SPI BR 分频到 9 MHz 实验点",
        "alt_en": "SPI BR divider table down to the 9 MHz lab point",
        "cap_zh": "▲ 自绘。SPI1@72 MHz，BR=010 → 9 MHz，与 JEDEC GIF 一致。",
        "cap_en": "▲ Drawn for this book. SPI1@72 MHz, BR=010 → 9 MHz, matches the JEDEC GIF.",
    },
    {
        "zh": ROOT / "docs" / "08-SPI总线.md",
        "en": ROOT / "docs" / "en" / "08-spi.md",
        "marker_zh": "### 4. NSS 管理与多从机",
        "marker_en": "### 4. NSS, and more than one slave",
        "needle": "sample-08-nss-multi.svg",
        "src_zh": "../assets/diagrams/sample-08-nss-multi.svg",
        "src_en": "../../assets/diagrams/sample-08-nss-multi.svg",
        "width": 760,
        "alt_zh": "多从机独立 CS 拓扑",
        "alt_en": "Multi-slave topology with independent chip-selects",
        "cap_zh": "▲ 自绘。共用 SCK/MOSI/MISO；同时拉低两个 CS 会顶总线。",
        "cap_en": "▲ Drawn for this book. Shared SCK/MOSI/MISO; two CS low fights the bus.",
    },
    {
        "zh": ROOT / "docs" / "08-SPI总线.md",
        "en": ROOT / "docs" / "en" / "08-spi.md",
        "marker_zh": "## 关键插图",
        "marker_en": "## Key figures",
        "needle": "sample-08-spi-jedec-flow.svg",
        "src_zh": "../assets/animations/sample-08-spi-jedec-flow.svg",
        "src_en": "../../assets/animations/sample-08-spi-jedec-flow.svg",
        "width": 720,
        "alt_zh": "SPI JEDEC 读 ID：0x9F 到 EF 40 17",
        "alt_en": "SPI JEDEC ID read: 0x9F through EF 40 17",
        "cap_zh": "▲ 自绘矢量动画（FA-002）。CS↓ 0x9F → EF 40 17 @ 9 MHz。",
        "cap_en": "▲ Hand-drawn CSS animation (FA-002). CS↓ 0x9F → EF 40 17 @ 9 MHz.",
    },
]


def main() -> None:
    n = 0
    for job in EMBEDS:
        block_zh = BLOCK.format(
            src=job["src_zh"], width=job["width"], alt=job["alt_zh"], cap=job["cap_zh"]
        )
        block_en = BLOCK.format(
            src=job["src_en"], width=job["width"], alt=job["alt_en"], cap=job["cap_en"]
        )
        if _insert_before(job["zh"], job["marker_zh"], job["needle"], block_zh):
            n += 1
        if _insert_before(job["en"], job["marker_en"], job["needle"], block_en):
            n += 1
    print("embeds applied:", n)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Embed quality-uplift figures/animations into zh/en pilot chapters (idempotent)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

BLOCK = """
<p align="center">
  <img src="{src}" width="{width}" alt="{alt}">
  <br><sub>{caption}</sub>
</p>

"""

EMBEDS = [
    # ch02
    {
        "zh": ROOT / "docs" / "02-芯片选型与存储器时钟.md",
        "en": ROOT / "docs" / "en" / "02-part-and-clock.md",
        "marker_zh": "### 6. 时钟树与分频",
        "marker_en": "### 6. Clock tree and dividers",
        "needle": "sample-02-pll-lock.svg",
        "src_zh": "../assets/diagrams/sample-02-pll-lock.svg",
        "src_en": "../../assets/diagrams/sample-02-pll-lock.svg",
        "width": 760,
        "alt_zh": "HSE 就绪、PLL 倍频、SWS 切到 PLL、LATENCY=2 四步上锁台账",
        "alt_en": "Four-step PLL lock ledger: HSE ready, multiply, SWS=PLL, LATENCY=2",
        "cap_zh": "▲ 自绘。PLL 上锁台账：HSERDY → PLLMUL×9 → SWS=10 → LATENCY=2。知识轨，非示波器实拍。",
        "cap_en": "▲ Drawn for this book. PLL lock ledger: HSERDY → PLLMUL×9 → SWS=10 → LATENCY=2. Knowledge track, not a scope photo.",
    },
    {
        "zh": ROOT / "docs" / "02-芯片选型与存储器时钟.md",
        "en": ROOT / "docs" / "en" / "02-part-and-clock.md",
        "marker_zh": "### 7. Flash 等待周期与主频",
        "marker_en": "### 7. Flash wait states and core clock",
        "needle": "sample-02-flash-latency.svg",
        "src_zh": "../assets/diagrams/sample-02-flash-latency.svg",
        "src_en": "../../assets/diagrams/sample-02-flash-latency.svg",
        "width": 760,
        "alt_zh": "Flash LATENCY 与 SYSCLK 频段对照：0/1/2 等待周期",
        "alt_en": "FLASH_ACR LATENCY bands versus SYSCLK",
        "cap_zh": "▲ 自绘。等待周期频段：升频先加 LATENCY，降频后减。知识轨。",
        "cap_en": "▲ Drawn for this book. Raise LATENCY before raising SYSCLK; reverse when lowering.",
    },
    {
        "zh": ROOT / "docs" / "02-芯片选型与存储器时钟.md",
        "en": ROOT / "docs" / "en" / "02-part-and-clock.md",
        "marker_zh": "### 1. 命名规则逐段拆解",
        "marker_en": "### 1. The name, piece by piece",
        "needle": "sample-02-bus-matrix.svg",
        "src_zh": "../assets/diagrams/sample-02-bus-matrix.svg",
        "src_en": "../../assets/diagrams/sample-02-bus-matrix.svg",
        "width": 760,
        "alt_zh": "F103 满速下 AHB/APB1/APB2 挂载与时钟",
        "alt_en": "AHB/APB1/APB2 attachment map at full-speed F103",
        "cap_zh": "▲ 自绘。总线挂载图：算波特率/定时器前先问外设在哪条总线。",
        "cap_en": "▲ Drawn for this book. Ask which bus a peripheral sits on before baud/timer math.",
    },
    {
        "zh": ROOT / "docs" / "02-芯片选型与存储器时钟.md",
        "en": ROOT / "docs" / "en" / "02-part-and-clock.md",
        "marker_zh": "## 关键插图",
        "marker_en": "## Key figures",
        "needle": "sample-02-pll-lock-flow.svg",
        "src_zh": "../assets/animations/sample-02-pll-lock-flow.svg",
        "src_en": "../../assets/animations/sample-02-pll-lock-flow.svg",
        "width": 720,
        "alt_zh": "PLL 上锁机制动画：高亮沿 HSE→PLL→SWS 前进",
        "alt_en": "PLL lock mechanism animation: highlight advances HSE→PLL→SWS",
        "cap_zh": "▲ 自绘矢量动画（FA-002）。上锁步骤推进；失败回落见 clock-css GIF / HSE-fail 静图。",
        "cap_en": "▲ Hand-drawn CSS animation (FA-002). Lock steps advance; fail path on clock-css GIF / HSE-fail SVG.",
    },
    # ch03
    {
        "zh": ROOT / "docs" / "03-GPIO与LED.md",
        "en": ROOT / "docs" / "en" / "03-gpio-and-led.md",
        "marker_zh": "### 5. GPIO 寄存器（F1）",
        "marker_en": "### 5. GPIO registers (F1)",
        "needle": "sample-03-moder-map.svg",
        "src_zh": "../assets/diagrams/sample-03-moder-map.svg",
        "src_en": "../../assets/diagrams/sample-03-moder-map.svg",
        "width": 760,
        "alt_zh": "PC13 LED 的 MODER/OTYPER/PUPDR/OSPEEDR 与 BSRR 台账",
        "alt_en": "PC13 LED register map: MODER/OTYPER/PUPDR/OSPEEDR + BSRR",
        "cap_zh": "▲ 自绘。四寄存器配置 + BSRR 原子写；禁止 ODR 读改写。",
        "cap_en": "▲ Drawn for this book. Four-register setup + atomic BSRR; never ODR RMW.",
    },
    {
        "zh": ROOT / "docs" / "03-GPIO与LED.md",
        "en": ROOT / "docs" / "en" / "03-gpio-and-led.md",
        "marker_zh": "### 4. LED 限流电阻计算",
        "marker_en": "### 4. LED series resistor",
        "needle": "sample-03-current-path.svg",
        "src_zh": "../assets/diagrams/sample-03-current-path.svg",
        "src_en": "../../assets/diagrams/sample-03-current-path.svg",
        "width": 760,
        "alt_zh": "3V3→R→LED→PC13 电流路径估算（标 EST）",
        "alt_en": "3V3→R→LED→PC13 current-path estimate (marked EST)",
        "cap_zh": "▲ 自绘估算（EST）。2.2k≈0.59 mA；330≈3.9 mA。不是实验室读数。",
        "cap_en": "▲ Hand-drawn EST. ~0.59 mA @ 2.2k; ~3.9 mA @ 330. Not a lab reading.",
    },
    {
        "zh": ROOT / "docs" / "03-GPIO与LED.md",
        "en": ROOT / "docs" / "en" / "03-gpio-and-led.md",
        "marker_zh": "### 6. 按键电路与消抖",
        "marker_en": "### 6. Button circuits and debounce",
        "needle": "sample-03-exti-vs-poll.svg",
        "src_zh": "../assets/diagrams/sample-03-exti-vs-poll.svg",
        "src_en": "../../assets/diagrams/sample-03-exti-vs-poll.svg",
        "width": 760,
        "alt_zh": "轮询按键 vs EXTI 边沿：主循环占用与低功耗对照",
        "alt_en": "Polling versus EXTI edges for buttons",
        "cap_zh": "▲ 自绘对照。GPIO 章先点灯；事件输入在 NVIC/EXTI 章继续。",
        "cap_en": "▲ Drawn compare. Light the pin here; continue events in the NVIC/EXTI chapter.",
    },
    {
        "zh": ROOT / "docs" / "03-GPIO与LED.md",
        "en": ROOT / "docs" / "en" / "03-gpio-and-led.md",
        "marker_zh": "## 关键插图",
        "marker_en": "## Key figures",
        "needle": "sample-03-gpio-bsrr-flow.svg",
        "src_zh": "../assets/animations/sample-03-gpio-bsrr-flow.svg",
        "src_en": "../../assets/animations/sample-03-gpio-bsrr-flow.svg",
        "width": 720,
        "alt_zh": "BSRR 原子写与 PC13 低有效点灯机制动画",
        "alt_en": "BSRR atomic write and PC13 active-low LED mechanism",
        "cap_zh": "▲ 自绘矢量动画（FA-002）。模式→类型→BSRR→引脚；极性跟原理图。",
        "cap_en": "▲ Hand-drawn CSS animation (FA-002). Mode→type→BSRR→pin; polarity follows the schematic.",
    },
    # ch06
    {
        "zh": ROOT / "docs" / "06-串口UART.md",
        "en": ROOT / "docs" / "en" / "06-uart.md",
        "marker_zh": "### 2. 波特率与误差",
        "marker_en": "### 2. Baud rate and error",
        "needle": "sample-06-baud-formula.svg",
        "src_zh": "../assets/diagrams/sample-06-baud-formula.svg",
        "src_en": "../../assets/diagrams/sample-06-baud-formula.svg",
        "width": 760,
        "alt_zh": "USART1/2 在 72/36 MHz 下的 BRR 算例",
        "alt_en": "USART1/2 BRR examples at 72/36 MHz",
        "cap_zh": "▲ 自绘。同一波特率字符串，PCLK 不同则 BRR 不同。",
        "cap_en": "▲ Drawn for this book. Same baud string, different PCLK → different BRR.",
    },
    {
        "zh": ROOT / "docs" / "06-串口UART.md",
        "en": ROOT / "docs" / "en" / "06-uart.md",
        "marker_zh": "### 1. 帧格式详解",
        "marker_en": "### 1. The frame",
        "needle": "sample-06-frame-annotated.svg",
        "src_zh": "../assets/diagrams/sample-06-frame-annotated.svg",
        "src_en": "../../assets/diagrams/sample-06-frame-annotated.svg",
        "width": 760,
        "alt_zh": "0xA5 的 8N1 帧位注释：空闲/起始/数据/停止",
        "alt_en": "Annotated 8N1 frame for byte 0xA5",
        "cap_zh": "▲ 自绘。LSB first；115200 位宽≈8.68 µs。知识轨线语法。",
        "cap_en": "▲ Drawn for this book. LSB first; ~8.68 µs/bit at 115200. Wire grammar, knowledge track.",
    },
    {
        "zh": ROOT / "docs" / "06-串口UART.md",
        "en": ROOT / "docs" / "en" / "06-uart.md",
        "marker_zh": "## 硬件与接线",
        "marker_en": "## Hardware and wiring",
        "needle": "sample-06-tx-rx-crossover.svg",
        "src_zh": "../assets/diagrams/sample-06-tx-rx-crossover.svg",
        "src_en": "../../assets/diagrams/sample-06-tx-rx-crossover.svg",
        "width": 760,
        "alt_zh": "MCU TX→适配器 RX 交叉与共地、仅 3V3",
        "alt_en": "MCU TX→adapter RX crossover, common GND, 3V3 only",
        "cap_zh": "▲ 自绘接线规则。TX-TX 会永远沉默；5V TTL 进 3V3 有风险。",
        "cap_en": "▲ Drawn wiring rule. TX-TX stays silent; 5V TTL into 3V3 risks damage.",
    },
    {
        "zh": ROOT / "docs" / "06-串口UART.md",
        "en": ROOT / "docs" / "en" / "06-uart.md",
        "marker_zh": "## 关键插图",
        "marker_en": "## Key figures",
        "needle": "sample-06-uart-baud-wire.svg",
        "src_zh": "../assets/animations/sample-06-uart-baud-wire.svg",
        "src_en": "../../assets/animations/sample-06-uart-baud-wire.svg",
        "width": 720,
        "alt_zh": "波特率公式与 TX/RX 交叉、8N1 位序机制动画",
        "alt_en": "Baud formula, TX/RX crossover, and 8N1 bit-order mechanism",
        "cap_zh": "▲ 自绘矢量动画（FA-002）。公式台账 + 交叉流动 + 位高亮。",
        "cap_en": "▲ Hand-drawn CSS animation (FA-002). Math ledger + crossover flow + bit highlight.",
    },
    # ch09
    {
        "zh": ROOT / "docs" / "09-ADC与DAC.md",
        "en": ROOT / "docs" / "en" / "09-adc-dac.md",
        "marker_zh": "### 2. 逐次逼近（SAR）原理：采样保持 + 二分比较",
        "marker_en": "### 2. Successive approximation (SAR): sample-and-hold plus binary compare",
        "needle": "sample-09-sar-ladder.svg",
        "src_zh": "../assets/diagrams/sample-09-sar-ladder.svg",
        "src_en": "../../assets/diagrams/sample-09-sar-ladder.svg",
        "width": 760,
        "alt_zh": "12 位 SAR 权重台阶与比较动作",
        "alt_en": "12-bit SAR weight ladder and compare actions",
        "cap_zh": "▲ 自绘。MSB→LSB 权重；EOC 后读 DR。动画见 sample-09-adc-sar-weights。",
        "cap_en": "▲ Drawn for this book. MSB→LSB weights; read DR after EOC.",
    },
    {
        "zh": ROOT / "docs" / "09-ADC与DAC.md",
        "en": ROOT / "docs" / "en" / "09-adc-dac.md",
        "marker_zh": "### 1. 分辨率、参考电压与量化误差",
        "marker_en": "### 1. Resolution, reference voltage, and quantization error",
        "needle": "sample-09-vref-rails.svg",
        "src_zh": "../assets/diagrams/sample-09-vref-rails.svg",
        "src_en": "../../assets/diagrams/sample-09-vref-rails.svg",
        "width": 760,
        "alt_zh": "码值换算电压与 Vref+/Vrefint 注意点",
        "alt_en": "Code-to-volt math and Vref+/Vrefint caveats",
        "cap_zh": "▲ 自绘。Code/4095×Vref+；绝对伏特先标 EST。",
        "cap_en": "▲ Drawn for this book. Code/4095×Vref+; mark absolute volts EST.",
    },
    {
        "zh": ROOT / "docs" / "09-ADC与DAC.md",
        "en": ROOT / "docs" / "en" / "09-adc-dac.md",
        "marker_zh": "### 7. 校准、模拟看门狗、注入通道",
        "marker_en": "### 7. Calibration, the analog watchdog, and injected channels",
        "needle": "sample-09-sample-time.svg",
        "src_zh": "../assets/diagrams/sample-09-sample-time.svg",
        "src_en": "../../assets/diagrams/sample-09-sample-time.svg",
        "width": 760,
        "alt_zh": "ADC 采样时间 SMPR 与源阻抗预算",
        "alt_en": "ADC sample-time budget versus source impedance",
        "cap_zh": "▲ 自绘。ADCCLK≤14 MHz；软源拉长 SMP。",
        "cap_en": "▲ Drawn for this book. ADCCLK≤14 MHz; lengthen SMP for soft sources.",
    },
    {
        "zh": ROOT / "docs" / "09-ADC与DAC.md",
        "en": ROOT / "docs" / "en" / "09-adc-dac.md",
        "marker_zh": "## 关键插图",
        "marker_en": "## Key figures",
        "needle": "sample-09-adc-sar-weights.svg",
        "src_zh": "../assets/animations/sample-09-adc-sar-weights.svg",
        "src_en": "../../assets/animations/sample-09-adc-sar-weights.svg",
        "width": 720,
        "alt_zh": "SAR 权重行走与采样时间预算机制动画",
        "alt_en": "SAR weight walk and sample-time budget mechanism",
        "cap_zh": "▲ 自绘矢量动画（FA-002）。权重高亮 MSB→LSB，不是空转弹跳。",
        "cap_en": "▲ Hand-drawn CSS animation (FA-002). Weight highlight MSB→LSB, not empty bounce.",
    },
    # ch10
    {
        "zh": ROOT / "docs" / "10-DMA.md",
        "en": ROOT / "docs" / "en" / "10-dma.md",
        "marker_zh": "### 3. 传输方向与工作模式",
        "marker_en": "### 3. Transfer direction and operating modes",
        "needle": "sample-10-dma-phases.svg",
        "src_zh": "../assets/diagrams/sample-10-dma-phases.svg",
        "src_en": "../../assets/diagrams/sample-10-dma-phases.svg",
        "width": 760,
        "alt_zh": "DMA 请求→仲裁→搬运→CNDTR 四阶段",
        "alt_en": "DMA request→grant→transfer→CNDTR phases",
        "cap_zh": "▲ 自绘。环形模式 HT/TC；普通模式数到 0 停。",
        "cap_en": "▲ Drawn for this book. Circular HT/TC; normal stops at zero.",
    },
    {
        "zh": ROOT / "docs" / "10-DMA.md",
        "en": ROOT / "docs" / "en" / "10-dma.md",
        "marker_zh": "### 6. 还剩多少没搬：看 NDTR",
        "marker_en": "### 6. How much is left: read NDTR",
        "needle": "sample-10-cndtr-ledger.svg",
        "src_zh": "../assets/diagrams/sample-10-cndtr-ledger.svg",
        "src_en": "../../assets/diagrams/sample-10-cndtr-ledger.svg",
        "width": 760,
        "alt_zh": "环形 ADC 缓冲的 CNDTR 现场台账",
        "alt_en": "Live CNDTR ledger for a circular ADC buffer",
        "cap_zh": "▲ 自绘。HT/TC 半区所有权；ISR 只置标志。",
        "cap_en": "▲ Drawn for this book. HT/TC half ownership; ISR only sets a flag.",
    },
    {
        "zh": ROOT / "docs" / "10-DMA.md",
        "en": ROOT / "docs" / "en" / "10-dma.md",
        "marker_zh": "### 1. 控制器结构：F1 的「通道」 vs F4 的「流×通道」",
        "marker_en": '### 1. Controller layout: F1 "channels" vs F4 "stream × channel"',
        "needle": "sample-10-mem2mem-vs-peri.svg",
        "src_zh": "../assets/diagrams/sample-10-mem2mem-vs-peri.svg",
        "src_en": "../../assets/diagrams/sample-10-mem2mem-vs-peri.svg",
        "width": 760,
        "alt_zh": "外设请求 DMA 与内存到内存对照",
        "alt_en": "Peripheral-request DMA versus memory-to-memory",
        "cap_zh": "▲ 自绘决策表。流式外设用 peri；块拷贝用 mem2mem。",
        "cap_en": "▲ Drawn decision table. Streaming peripherals vs one-shot mem2mem.",
    },
    {
        "zh": ROOT / "docs" / "10-DMA.md",
        "en": ROOT / "docs" / "en" / "10-dma.md",
        "marker_zh": "## 关键插图",
        "marker_en": "## Key figures",
        "needle": "sample-10-dma-circular-ht.svg",
        "src_zh": "../assets/animations/sample-10-dma-circular-ht.svg",
        "src_en": "../../assets/animations/sample-10-dma-circular-ht.svg",
        "width": 720,
        "alt_zh": "环形 DMA 半区所有权与 CNDTR 倒数机制动画",
        "alt_en": "Circular DMA half ownership and CNDTR countdown mechanism",
        "cap_zh": "▲ 自绘矢量动画（FA-002）。A/B 半区交替可读；请求线流动。",
        "cap_en": "▲ Hand-drawn CSS animation (FA-002). Alternating A/B ownership; request flow.",
    },
]


def _insert_before(path: Path, marker: str, needle: str, block: str) -> bool:
    text = path.read_text(encoding="utf-8")
    if needle in text:
        return False
    if marker not in text:
        raise SystemExit(f"marker missing in {path}: {marker!r}")
    # insert immediately AFTER the marker line
    lines = text.splitlines(keepends=True)
    out = []
    done = False
    for line in lines:
        out.append(line)
        if (not done) and (line.startswith(marker) or line.strip() == marker.strip()):
            out.append("\n")
            out.append(block)
            done = True
    if not done:
        raise SystemExit(f"failed to insert into {path}")
    path.write_text("".join(out), encoding="utf-8")
    return True


def main() -> None:
    n = 0
    for e in EMBEDS:
        for lang, path, marker, src, alt, cap in (
            ("zh", e["zh"], e["marker_zh"], e["src_zh"], e["alt_zh"], e["cap_zh"]),
            ("en", e["en"], e["marker_en"], e["src_en"], e["alt_en"], e["cap_en"]),
        ):
            block = BLOCK.format(src=src, width=e["width"], alt=alt, caption=cap)
            if _insert_before(path, marker, e["needle"], block):
                print(f"+ {lang} {path.name} <- {e['needle']}")
                n += 1
            else:
                print(f"= {lang} {path.name} already has {e['needle']}")
    print(f"embeds applied: {n}")


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""B56: embed the eight plates into the zh/en chapters of 02/03/07/24/27."""
from embed import embed_after_text

SPECS = [
    # ---- ch02 A: part funnel after the ADC pitfall row ----
    ("docs/02-芯片选型与存储器时钟.md",
     "ADC 为了更快选了 ÷4",
     "ch02-part-funnel.png",
     "Handraw：选型先过筛，再查完整订货号（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。看哪里：左侧把需求写成引脚、Flash/RAM、外设、主频、温度五问；中间三把筛子按封装 T=36 · C=48 · R=64 · V=100 · Z=144、存储器 4=16K … G=1M、外设与主频逐层排除；右侧只剩 C8T6 这样的候选，最后才逐字对订货号。证明什么：筛子问「够不够用」，数据手册才回答「到底是哪一颗」；不能证明什么：不替代数据手册的订购信息与引脚复用表，也不是实物丝印。出处：[DS5319](#source-ds5319-clock)、[RM0008](#source-rm0008-rcc)。"),
    ("docs/en/02-part-and-clock.md",
     "ADC was set to ÷4 to go faster",
     "ch02-part-funnel.png",
     "Handraw: filter first, look up the order code last (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). Where to look: five requirements on the left (pins, Flash/RAM, peripherals, clock, temperature); three sieves in the middle — package T=36 · C=48 · R=64 · V=100 · Z=144, Flash 4=16K … G=1M, peripherals and clock; only the surviving C8T6 on the right before the full order code is checked; Proves the sieves answer “is it enough?” while the datasheet answers “which one”; Cannot show the datasheet's ordering or pinout tables, and it is not a photo. See [DS5319](#source-ds5319-clock), [RM0008](#source-rm0008-rcc)."),

    # ---- ch02 B: clock gate after the CLK_ENABLE paragraph ----
    ("docs/02-芯片选型与存储器时钟.md",
     "任何外设在第一次写寄存器之前",
     "ch02-clock-gate.png",
     "Handraw：先开时钟，再摸寄存器（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。看哪里：左侧门关——外设写进去读回 0；门开——读写才有意义；右侧上电顺序 ① __HAL_RCC_*_CLK_ENABLE() ② HAL_xxx_Init() ③ 读写寄存器，顺序反了就是给关着的门做初始化。证明什么：任何外设第一次写寄存器之前先开时钟；不能证明什么：不展开 SystemClock_Config() 内部与各外设的时钟树配置，也不是实测波形。出处：[RM0008](#source-rm0008-rcc)、[DS5319](#source-ds5319-clock)。"),
    ("docs/en/02-part-and-clock.md",
     "Before the first write to a peripheral",
     "ch02-clock-gate.png",
     "Handraw: open the clock gate before touching registers (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). Where to look: gate closed on the left — writes read back 0; gate open — reads and writes mean something; power-up order on the right (① __HAL_RCC_*_CLK_ENABLE() ② HAL_xxx_Init() ③ touch registers) — reversed, it initializes a closed gate; Proves the gate must be open before a peripheral's first register write; Cannot show what SystemClock_Config() does inside or each peripheral's clock-tree settings, and it is not a measured waveform. See [RM0008](#source-rm0008-rcc), [DS5319](#source-ds5319-clock)."),

    # ---- ch03: debounce re-check after the debounce table ----
    ("docs/03-GPIO与LED.md",
     "| 施密特触发器 | 硬件整形 |",
     "ch03-debounce-recheck.png",
     "Handraw：软件消抖的 20 ms 复查与边界（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。看哪里：左侧三步——读到低先当毛刺、等 10–20 ms（代码里就是 HAL_Delay(20)）、再读一次；仍为低才判定按下，回到高就丢弃。右侧是边界——每轮塞 100 ms 阻塞任务会吞掉短按，所以第 04 章改用 EXTI；硬件路线可以上 RC（0.1 µF）或施密特触发器。证明什么：软件消抖就是「看见低不算数，20 ms 后还低才算按下」；不能证明什么：不含按键抖动的实际波形，也不是示波器实测。出处：[RM0008 第 9.2.7 节](#source-rm0008-gpio)。"),
    ("docs/en/03-gpio-and-led.md",
     "| Schmitt trigger | Shape it in hardware |",
     "ch03-debounce-recheck.png",
     "Handraw: the 20 ms re-check and its boundary (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). Where to look: three steps on the left — treat a low as a possible glitch, wait 10–20 ms (`HAL_Delay(20)`), read again; still low means pressed, back high means discard. The right side gives the boundary — a 100 ms blocking task per loop swallows short presses, so chapter 04 moves to EXTI; hardware can use an RC filter (0.1 µF) or a Schmitt trigger; Proves software debounce is “a low does not count until it is still low after 20 ms”; Cannot show the real bounce waveform on your button, and it is not an oscilloscope measurement. See [RM0008 section 9.2.7](#source-rm0008-gpio)."),

    # ---- ch07 A: pin ownership after the PB8/PB9 pitfall row ----
    ("docs/07-I2C总线.md",
     "波形跑到 PB8/PB9，或者串口占了 PB6",
     "ch07-pin-owner.png",
     "Handraw：PB6/PB7 与 PB8/PB9 的归属（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。看哪里：左边复位默认 I2C1 在 PB6/PB7（第 42、43 脚），右边重映射后到 PB8/PB9（第 45、46 脚）；下面写明 USART1_TX/RX 也能映射到 PB6/PB7，但要开重映射，而且同一时间这两只脚只能给一个外设。证明什么：波形跑到 PB8/PB9 或串口占了 PB6，先查重映射与 USART1 的脚位，再谈波形；不能证明什么：不涉及外部上拉与从机地址，也不是实测波形。出处：[DS5319 Rev 20 表 5](#source-ds5319-i2c)。"),
    ("docs/en/07-i2c.md",
     "The waveform is on PB8/PB9",
     "ch07-pin-owner.png",
     "Handraw: who owns PB6/PB7 versus PB8/PB9 (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). Where to look: reset default I2C1 sits on PB6/PB7 (pins 42/43); after remap it moves to PB8/PB9 (pins 45/46); below, USART1_TX/RX can also map onto PB6/PB7, but only with remap enabled, and those two pins serve one peripheral at a time; Proves when the waveform appears on PB8/PB9 or the UART took PB6, check the remap and the USART1 pin assignment before the waveform; Cannot show the external pull-ups or the slave address, and it is not a captured waveform. See [DS5319 Rev 20 Table 5](#source-ds5319-i2c)."),

    # ---- ch07 B: bit-bang vs hardware after the speed row ----
    ("docs/07-I2C总线.md",
     "快速模式目标 400 kHz。STM32F103C8T6 不支持 1 MHz",
     "ch07-two-owners.png",
     "Handraw：软件模拟与硬件 I2C 的两条路线（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。看哪里：左边软件模拟——两只普通引脚、一位一位翻转，慢但每步在手里、哪个脚都能用；右边硬件 I2C——时序交给外设、CPU 省事，但从机拉住 SDA 时 F1 外设容易卡忙；下面给出恢复路径：SCL 配成开漏 GPIO 手动翻转 9 次、发 STOP，再 HAL_I2C_Init。证明什么：时序在谁手里，卡住就找谁；不能证明什么：不涵盖具体从机的 SDA 保持时间，也不是实测总线波形。出处：[RM0008 第 26 章](#source-rm0008-i2c)、[DS5319 表 42](#source-ds5319-i2c)。"),
    ("docs/en/07-i2c.md",
     "Fast mode targets 400 kHz. The STM32F103C8T6 does not support 1 MHz",
     "ch07-two-owners.png",
     "Handraw: bit-bang versus hardware I2C (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). Where to look: bit-bang on the left — two ordinary pins, one bit at a time, slower but every step is yours, any pin works; hardware I2C on the right — the peripheral runs the timing and frees the CPU, but on the F1 it sticks busy when a slave holds SDA; the recovery path is below — configure SCL as open-drain GPIO, toggle it 9 times, send STOP, then `HAL_I2C_Init`; Proves whoever owns the timing owns the recovery; Cannot show a specific slave's SDA hold time, and it is not a captured bus waveform. See [RM0008 chapter 26](#source-rm0008-i2c), [DS5319 Table 42](#source-ds5319-i2c)."),

    # ---- ch24 A: migration boundaries after the last pitfall row ----
    ("docs/24-STM32L4引脚.md",
     "把封面 1.1 µA 当成验收上限",
     "ch24-migrate-boundary.png",
     "Handraw：抄 F1 工程的四个第一分歧边界（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。看哪里：四组边界——引脚与供电（PD0/PD1 对 PH0/PH1、脚 48 VDDUSB）、唤醒与时钟（SysTick 与旧标志、PLL 未恢复）、负载与调试（调试器、GPIO、LED、回灌、仪表负担电压）、测量与账本（漏掉唤醒电荷、1.1 µA 当上限）。证明什么：同一个症状先分边界，再一次只改一处；不能证明什么：不是 F1→L4 迁移的完整检查表，也不能替代 DS10198 与 RM0351 的逐项条件。出处：[DS10198](#source-ds10198)、[RM0351](#source-rm0351)。"),
    ("docs/en/24-stm32l4-pins.md",
     "The cover's 1.1 µA is treated as an acceptance limit",
     "ch24-migrate-boundary.png",
     "Handraw: four first boundaries when copying an F1 project (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). Where to look: four boundary groups — pins and supply (PD0/PD1 versus PH0/PH1, pin 48 VDDUSB), wake-up and clocks (SysTick and stale flags, PLL not restored), load and debug (debugger, GPIO, LEDs, back-feed, meter burden voltage), and measurement and ledger (missing wake-up charge, 1.1 µA as a limit); Proves classify the boundary first, then change one thing at a time; Cannot serve as a complete F1-to-L4 checklist, and does not replace the item-by-item conditions in DS10198 and RM0351. See [DS10198](#source-ds10198), [RM0351](#source-rm0351)."),

    # ---- ch24 B: slow meter after Lab B item 4 ----
    ("docs/24-STM32L4引脚.md",
     "保存原始波形和脚本",
     "ch24-slow-meter.png",
     "Handraw：慢表漏掉 8 ms 尖峰，只读到 2 µA（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。看哪里：1 s 轴上 8 ms 尖峰按比例只有约 7 px 宽，慢表的采样点全落在睡眠平台；表读出约 2 µA，整周期积分是 0.041984 mA·s ≈ 42 µA；下方给出 f_s ≥ 10/t_min（t_min = 8 ms → ≥ 1.25 kHz）与验收页三行（模式、电流、条件）。证明什么：漏掉尖峰，42 µA 会被读成 2 µA；不能证明什么：不涵盖你板子的波形、仪器带宽与板级负载，也不是实测。出处：[DS10198](#source-ds10198)、[AN4746](#source-an4746)。"),
    ("docs/en/24-stm32l4-pins.md",
     "Save the raw waveform and calculation script",
     "ch24-slow-meter.png",
     "Handraw: a slow meter misses the 8 ms spike and reads 2 µA (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). Where to look: the 8 ms spike is only about 7 px wide on the 1 s axis, and the slow meter's samples all land on the sleep plateau; the meter reads about 2 µA while the full-cycle integral is 0.041984 mA·s ≈ 42 µA; below sit f_s ≥ 10/t_min (t_min = 8 ms → ≥ 1.25 kHz) and the three-line acceptance page (mode, current, conditions); Proves a missed spike turns 42 µA into 2 µA; Cannot show your board's waveform, instrument bandwidth, or board loads, and it is not measured. See [DS10198](#source-ds10198), [AN4746](#source-an4746)."),

    # ---- ch27: UDP vs TCP after the UDP paragraph ----
    ("docs/27-网络与协议栈.md",
     "UDP 不是“更实时的 TCP”",
     "ch27-udp-tcp-contract.png",
     "Handraw：UDP 与 TCP 两份运输合同（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。看哪里：左边 UDP——datagram 自带边界、丢失/乱序/重复与拥塞由应用负责、支持多播/广播；右边 TCP——字节流没有边界、必须自行分帧、连接内重传排序去重、拥塞控制内置、不支持多播；下面两条边界——UDP 不是「更实时的 TCP」，周期数据允许下一帧覆盖上一帧时 UDP 可减少队头阻塞，但仍要序号和时间戳。证明什么：先选合同（边界归谁、可靠归谁），再谈协议和端口；不能证明什么：不展开 MQTT QoS、TLS 与具体实现性能，也不是实测吞吐。出处：[lwIP pitfalls](#source-lwip-pitfalls)、[RM0433](#source-rm0433)。"),
    ("docs/en/27-network.md",
     "UDP is not “more real-time TCP.”",
     "ch27-udp-tcp-contract.png",
     "Handraw: two transport contracts, UDP and TCP (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). Where to look: UDP on the left — datagrams keep boundaries, loss/reorder/duplicates and congestion belong to the application, multicast is supported; TCP on the right — a byte stream with no boundaries, you must frame it, retransmission/ordering/deduplication inside the connection, congestion control built in, no multicast; below, two boundaries — UDP is not “more real-time TCP,” and periodic data whose next frame may replace the previous one can avoid head-of-line blocking but still needs sequence and time; Proves choose the contract first (who owns boundaries, who owns reliability), then the protocol and port; Cannot cover MQTT QoS, TLS, or implementation performance, and it is not measured throughput. See [lwIP pitfalls](#source-lwip-pitfalls), [RM0433](#source-rm0433)."),
]

if __name__ == "__main__":
    bad = 0
    for spec in SPECS:
        if not embed_after_text(*spec):
            bad += 1
    if bad:
        raise SystemExit(f"{bad} embed(s) failed")

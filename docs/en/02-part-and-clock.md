# 02 Choosing a Part, Memory, and Clocks
> 中文：[芯片选型与存储器时钟](../02-芯片选型与存储器时钟.md)

> Reading the STM32 name, where a family sits, the memory map, and the clock tree is the base for picking a part and setting the frequency.

<p align="center">
  <img src="../../assets/animations/clock-tree.svg" width="760" alt="Clock-tree multiply from HSE to SYSCLK">
  <br><sub>▲ Animation: HSE 8 MHz → PLL ×9 → 72 MHz on the clock tree (vector drawing by the author)</sub>
</p>

<!-- video:ch02 -->
<p align="center">
  <video width="640" controls poster="../../assets/video/ch02-clock.png">
    <source src="../../assets/video/ch02-clock.mp4" type="video/mp4">
  </video>
  <br><sub>▲ Chapter video with Chinese voice-over (2.5 min). <a href="../../assets/video/ch02-clock.mp4">MP4</a> · <a href="../../assets/video/ch02-clock.srt">subtitles</a></sub>
</p>

<details>
<summary>Narration script (Chinese, same text as the subtitles)</summary>

1. 型号上的字母不是玄学。F103 告诉你系列，C8 这类字母看闪存容量，T6 这类看封装。先读数据手册封面和订购信息，再去数引脚。
2. 存储器地图把闪存、内存和外设分成几段。外设的本质，就是固定地址上的一排寄存器。地址抄错系列，写进去的就不是你要的那个外设。
3. F103 常见的一条路：外部 8 兆进 PLL，乘 9，系统时钟 72 兆。APB1 最高 36 兆，所以再除以 2。这条路径后面串口和 CAN 的波特率都靠它。
4. 这一帧是仓库画的时钟树。口诀你要刻进手上：先开时钟，再摸寄存器。时钟没开，写入就像写进虚空，调试器里看起来还像成功了。
5. 主频拉到 72 兆时，闪存要加等待。这一章写的是 48 到 72 兆用两个等待周期。只改 PLL、不改等待，常见的下场就是一跑就死。
6. APB 分频大于 1 的时候，定时器时钟还会再乘 2。算 PWM 前先问 HAL 要到的 PCLK，不要把 36 兆当成定时器的输入。差一倍，频率就差一倍。
7. 外部晶振起不来时，先退回内部时钟，证明芯片还活着，再查负载电容和焊点。一上来就把 PLL 乘到很高，是在用死机练习耐心。
8. 口诀再念一遍：先开时钟再摸寄存器。HSE 掉了靠时钟安全系统，想看频率可以走到时钟输出脚。别用Delay 的感觉去猜主频。
9. 动手时让串口打出主频、闪存容量和两条 APB。BluePill 上常见的是 72 兆和 64 KB 闪存。对不上，先别做后面的外设实验。
10. 合上书，三问。72 兆时闪存要几个等待？AHB 和 APB1 谁更慢？外设时钟门控没开时，写入会发生什么？

</details>
<!-- /video:ch02 -->

## Learning goals

Before this chapter: you have read chapter 01 and can generate a project in STM32CubeMX and download it to the BluePill; you can read binary and hexadecimal and follow bit operations such as `|=` and `&= ~` (if not, read "Zero-background primer" in chapter 00 first). For the labs, have a USB-to-serial adapter with 3.3 V logic levels at hand; an oscilloscope helps.

- [ ] Read the order code STM32F103C8T6 field by field, and check each field against the ordering information in the datasheet
- [ ] Choose a part that is good enough from the common families, by core, clock speed, and peripherals
- [ ] Point to where Flash, SRAM, peripheral registers, and core peripherals sit on the memory map, and look up the base addresses of RCC and GPIOA
- [ ] Work out SYSCLK, HCLK, PCLK1, PCLK2, the timer clocks, the ADC clock, and the USB clock from the 8 MHz crystal
- [ ] Say how many Flash wait states 72 MHz needs, and why the wait states go in before the clock switch
- [ ] Print every clock over the serial port and measure the real frequency on PA8 with MCO, to confirm that the clock setup really took effect

## Core ideas

**In one sentence: to choose a chip, read the order code and the peripheral table in the datasheet; to set up the clock, remember one path: the 8 MHz crystal goes through PLL ×9 to 72 MHz, APB1 divides that by 2 to 36 MHz, Flash gets 2 wait states, and every peripheral's clock is switched on before the peripheral is touched.**

### An analogy first

Think of the clocks in a chip as the water supply of a building.

- **Clock sources** are where the water comes from. The internal HSI is the tank on the roof: always there, but the pressure wanders. The external crystal, HSE, is the city main: you have to connect it and wait for the pressure to settle, but it is accurate.
- **The PLL (phase-locked loop)** is a booster pump. It raises the 8 MHz "pressure" to 72 MHz.
- **Prescalers** are the pressure-reducing valves on each floor. AHB, APB1, and APB2 each have one. The APB1 pipe is the thinnest: its pressure must not exceed 36 MHz.
- **Peripheral clock gates** are the taps in each flat. At power-up they are all shut, to save power; to use a peripheral, open its tap first.

The analogy stops here. Water pressure can be set to any value, but a clock can only take the multipliers and dividers the registers offer. Higher water pressure only means faster flow; a faster clock also needs Flash reads to keep up, which is what the wait states in section 8 are about.

### 1. What is in the order code

Conclusion: every field of the order code can be looked up in the datasheet's ordering information. The table below takes STM32F103C8T6 apart field by field, following section 7 of [DS5319 Rev 20](#source-ds5319); read it left to right:

| Field | This part | Meaning in DS5319 section 7 |
| --- | --- | --- |
| Device family | STM32 | 32-bit microcontroller based on an Arm core |
| Product type | F | General-purpose |
| Device subfamily | 103 | Performance line |
| Pin count | C | 48 pins; the same datasheet also has T = 36, R = 64, V = 100 |
| Flash size | 8 | 64 KB; B = 128 KB |
| Package | T | LQFP; H = BGA, I = UFBGA, U = VFQFPN or UFQFPN |
| Temperature range | 6 | Industrial, −40 to 85 °C; 7 = −40 to 105 °C |
| Options | (blank) | Blank = standard product, R = customer-dedicated code; there are also codes for programmed parts and TR (tape and reel) |

So **STM32F103C8T6 = general-purpose, performance-line F103, 48 pins, 64 KB Flash, LQFP package, −40 to 85 °C**.

DS5319 covers only the 64 KB and 128 KB sizes. Other sizes and pin counts are in their own datasheets; the high-density F103 datasheet, DS5792, for example, has Z = 144 pins, C = 256 KB, and E = 512 KB. The same letter does not always mean the same number in another family, so when you change family, look up that chip's ordering information again.

### 2. Choosing a family

Conclusion: settle the tier by core and clock speed first, then pick a part in that family with enough Flash, pins, and peripherals. The table below is a rough comparison of ST's mainstream families, with the highest clock in each family; strike out the rows whose clock or core is not enough, then compare the price column.

| Family | Core | Max clock | Typical use | Price (CNY each) |
| --- | --- | --- | --- | --- |
| F0 | Cortex-M0 | 48 MHz | Replacing 8-bit microcontrollers | 4–10 |
| F1 | Cortex-M3 | 72 MHz | The long-standing choice for teaching and industrial control | 8–20 |
| F3 | Cortex-M4 with FPU | 72 MHz | Mixed-signal work with on-chip op-amps and comparators | 15–30 |
| F4 | Cortex-M4 with FPU | 84–180 MHz | Floating-point and DSP work | 25–70 |
| F7 | Cortex-M7 | 216 MHz | Graphics, audio | 60–150 |
| G0 | Cortex-M0+ | 64 MHz | Low-cost new designs | 6–15 |
| G4 | Cortex-M4 with FPU | 170 MHz | Motor control, digital power | 20–45 |
| H7 | Cortex-M7 | 480 MHz (H743 revision V) | High-end graphics, heavy computation | 80–200 |
| L0 | Cortex-M0+ | 32 MHz | Battery-powered, ultra-low power | 5–12 |
| L4 | Cortex-M4 with FPU | 80 MHz | Low power with some computing headroom | 20–50 |

Where the clocks come from: F1 from [DS5319](#source-ds5319); the F4 168 MHz and 180 MHz from [RM0090](#source-rm0090) section 3.5.1 (180 MHz needs over-drive); G0 from [DS12232](#source-ds12232); H743 from [DS12110](#source-ds12110); the other families from ST's product pages. Flash, pin count, and package span a wide range inside every family, so filter on the product selector first and then read that chip's datasheet.

> [!NOTE]
> The price column is a rule of thumb for comparing tiers only; these are not numbers from DS5319 or RM0008, which list no prices. Real prices vary widely with the channel, the batch, and the year.

### 3. How the cores differ

Conclusion: the F103's Cortex-M3 has a hardware divider but no floating-point unit. For heavy floating-point work, move to an M4 or M7 family. Lower rows in the table below are features that only the higher-end cores have; "optional" means Arm lets the chip vendor decide whether to include it, so whether a given chip has it is in that chip's datasheet.

| Feature | Cortex-M0 / M0+ | Cortex-M3 | Cortex-M4 | Cortex-M7 |
| --- | --- | --- | --- | --- |
| Architecture | Armv6-M | Armv7-M | Armv7E-M | Armv7E-M |
| Hardware divide | No | Yes | Yes | Yes |
| DSP extension (SIMD, saturating arithmetic) | No | No | Yes | Yes |
| Floating-point unit (FPU) | No | No | Optional, single precision | Optional, single or double precision |
| MPU (memory protection unit) | None on M0, optional on M0+ | Optional | Optional | Optional |
| Cache | No | No | No | Optional, instruction and data caches |
| Tightly coupled memory (TCM) | No | No | No | Optional |
| STM32 examples | F0, G0, L0 | F1, F2, L1 | F3, F4, G4, L4 | F7, H7 |

The M3 column rests on [PM0056](#source-pm0056) section 1.3: single-cycle 32×32 multiply and a dedicated hardware divider. Whether the F103C8 has an MPU, PM0056 section 4.2 leaves to the datasheet, and DS5319 lists no MPU. The rows for the other cores come from Arm's technical reference manual for each core. The M3 does all `float` arithmetic in a software library, much slower than an M4 with an FPU (rule of thumb); on the F103, use integers wherever integers will do.

### 4. The memory map: an address is a location

**Conclusion: Cortex-M3 cuts the 4 GB address space into a few fixed regions, and the chip vendor can only place things inside them. A peripheral is a row of registers at fixed addresses.**

A register is a storage cell in the chip with a fixed address. Writing some of its bits changes how a piece of hardware behaves; reading it tells you what the hardware is doing now. Configuring a peripheral comes down to writing numbers to these addresses.

In the table below, the left two columns are the regions the core defines ([PM0056](#source-pm0056) section 2.2, Figure 9), and the right column is what the F103C8 actually puts in each one ([RM0008 Rev 21](#source-rm0008) section 3.3, Table 3, and section 3.3.3, Table 5). To place an address, find its region first, then read the right column:

| Address range | Region | What the F103C8 puts here |
| --- | --- | --- |
| 0x0000_0000–0x1FFF_FFFF | Code, 0.5 GB | Flash, 64 KB from 0x0800_0000; system memory, 2 KB from 0x1FFF_F000 (factory bootloader); option bytes, 16 bytes from 0x1FFF_F800; from 0x0000_0000, the boot alias (chapter 01, section 7) |
| 0x2000_0000–0x3FFF_FFFF | SRAM, 0.5 GB | On-chip SRAM, 20 KB from 0x2000_0000 |
| 0x4000_0000–0x5FFF_FFFF | Peripheral, 0.5 GB | Peripheral registers: APB1 from 0x4000_0000, APB2 from 0x4001_0000, and DMA1, RCC, and the Flash interface on AHB from 0x4002_0000 |
| 0x6000_0000–0x9FFF_FFFF | External RAM, 1 GB | Empty; this C8 has no FSMC |
| 0xA000_0000–0xDFFF_FFFF | External device, 1 GB | Empty |
| 0xE000_0000–0xE00F_FFFF | Private peripheral bus (PPB), 1 MB | Core peripherals: NVIC, SysTick, SCB, and the debug units |
| 0xE010_0000–0xFFFF_FFFF | Vendor-specific, 511 MB | — |

The first 1 MB of the SRAM region and of the peripheral region supports bit-banding, so a single bit can be read or written on its own; chapter 03, section 8 covers it.

<p align="center">
  <img src="../../assets/animations/memory-map.svg" width="760" alt="Cortex-M memory map">
  <br><sub>▲ Animation: Cortex-M memory map (Flash / SRAM / peripherals / system region) (vector drawing by the author)</sub>
</p>

Base addresses and buses of the common peripherals ([RM0008 Rev 21](#source-rm0008) section 3.3, Table 3) are below. A register's address is the base address plus an offset; RCC_CFGR, for example, has offset 0x04 (section 7.3.2), so its address is 0x40021004:

| Peripheral | Base address | Bus |
| --- | --- | --- |
| GPIOA | 0x40010800 | APB2 |
| GPIOB | 0x40010C00 | APB2 |
| GPIOC | 0x40011000 | APB2 |
| USART1 | 0x40013800 | APB2 |
| TIM2 | 0x40000000 | APB1 |
| RCC | 0x40021000 | AHB |
| FLASH (Flash interface) | 0x40022000 | AHB |

The CMSIS headers define macros for all of these addresses (such as `GPIOA_BASE`) and structures (such as `RCC->CFGR`); use the macros in code and do not hard-code addresses. Addresses change between families: F1 GPIO sits on APB2, F4 GPIO sits on AHB1, and the clock-enable macros change with them.

### 5. Boot modes: BOOT0 / BOOT1

Conclusion: in normal use BOOT0 is tied to 0 and the chip boots from Flash. Chapter 01, section 7 covers the three boot modes in detail; only the result is listed here, from [RM0008 Rev 21 section 3.4, Table 9](#source-rm0008-boot):

| BOOT1 | BOOT0 | Boot space | Use |
| --- | --- | --- | --- |
| Any | 0 | Main Flash (0x0800_0000) | Normal operation |
| 0 | 1 | System memory (0x1FFF_F000) | Factory bootloader, download over USART1 |
| 1 | 1 | On-chip SRAM (0x2000_0000) | Debugging a program held in SRAM; lost at power-off, and the program must move the vector table to SRAM itself |

### 6. Where the clock comes from: four sources and a PLL

**Conclusion: the F103 has two high-speed clock sources (HSI, HSE) and two low-speed ones (LSI, LSE). The system clock SYSCLK is one of HSI, HSE, or the PLL; after reset it is HSI at 8 MHz ([RM0008 Rev 21 section 7.2.6](#source-rm0008-rcc)).**

A few terms first:

- **Clock**: a square wave; digital logic takes one step on each rising edge. The higher the frequency, the more steps per second.
- **Crystal**: a piece of quartz that, connected to an oscillator circuit in the chip, oscillates at a very accurate frequency. The small silver part on the BluePill is the 8 MHz crystal.
- **RC oscillator**: an oscillator built inside the chip from resistors and capacitors. It needs no external parts, but its frequency drifts with temperature and voltage.
- **PLL (phase-locked loop)**: a circuit that multiplies its input clock by a factor. The F103 PLL multiplies by whole numbers only, ×2 to ×16.

The table below lists the four sources. The numbers in the frequency and accuracy columns come from the electrical characteristics tables of [DS5319 Rev 20](#source-ds5319); use the last column to find the one you need:

| Source | What it is | Frequency | Accuracy and notes | Main use |
| --- | --- | --- | --- | --- |
| HSI | Internal high-speed RC oscillator | 8 MHz | Factory-calibrated; −2% to +2.5% over −40 to 105 °C (Table 24); starts in 1–2 µs | System clock after reset; fallback when HSE fails |
| HSE | External high-speed crystal, or a clock fed in from outside | Crystal 4–16 MHz (Table 22), external clock 1–25 MHz (Table 20) | Accurate, set by the crystal; a crystal typically starts in 2 ms (Table 22) | 72 MHz through the PLL |
| LSI | Internal low-speed RC oscillator | About 40 kHz, between 30 and 60 kHz (RM0008 section 7.2.5) | Very inaccurate | Independent watchdog; can also clock the RTC |
| LSE | External low-speed crystal | 32.768 kHz | Accurate | RTC timekeeping (chapter 11) |

The PLL has four rules:

- The input must be 1–25 MHz, the output 16–72 MHz, and lock takes at most 200 µs (DS5319 Table 27).
- The input is HSE (optionally divided by 2 first) or HSI÷2.
- With HSI as the input there is only 8 / 2 = 4 MHz, so the most you can reach is 64 MHz (RM0008 Rev 21 section 7.2, note 1 of Figure 8).
- The factor and the input must be set before the PLL is switched on; they cannot be written while it runs (RM0008 sections 7.2.3 and 7.3.2).

> [!WARNING]
> HAL does not measure the crystal. It works out every clock from `HSE_VALUE` in `stm32f1xx_hal_conf.h` (8000000 by default in CubeMX). If the board carries a 12 MHz crystal while `HSE_VALUE` is still 8 MHz, ×9 really gives 108 MHz, well past 72 MHz, yet HAL still reports 72 MHz. Read the frequency printed on the crystal can first.

### 7. Clock tree and dividers: from SYSCLK down

Conclusion: SYSCLK passes the AHB prescaler to become HCLK, and HCLK splits into APB1 and APB2; every branch has a ceiling. The sketch shows the settings this book uses throughout:

```text
HSE 8 MHz ─► PLL ×9 ─► SYSCLK 72 MHz ─► AHB ÷1 ─► HCLK 72 MHz (core, DMA, memory)
               │                                   ├─► APB1 ÷2 ─► PCLK1 36 MHz ─► TIM2–TIM4 clock ×2 = 72 MHz
               │                                   └─► APB2 ÷1 ─► PCLK2 72 MHz ─► TIM1 72 MHz
               │                                                       └─► ADC ÷6 ─► ADCCLK 12 MHz
               └─► USB ÷1.5 ─► USBCLK 48 MHz
```

The table puts each branch's source, setting, and ceiling side by side. Each row is the row it comes from, multiplied or divided by one factor; no value may cross the number in the "Ceiling or requirement" column. USB needs not a ceiling but exactly 48 MHz, so with USB the PLL can only output 48 MHz or 72 MHz ([RM0008 Rev 21 section 7.2.3](#source-rm0008-rcc)).

| Clock | Comes from | Book setting | Result | Ceiling or requirement | Source |
| --- | --- | --- | --- | --- | --- |
| SYSCLK | PLL | ×9 | 72 MHz | 72 MHz | RM0008 section 7.3.2 |
| HCLK (AHB) | SYSCLK | ÷1 | 72 MHz | 72 MHz | DS5319 Table 9 |
| PCLK1 (APB1) | HCLK | ÷2 | 36 MHz | 36 MHz | DS5319 Table 9 |
| PCLK2 (APB2) | HCLK | ÷1 | 72 MHz | 72 MHz | DS5319 Table 9 |
| TIM2–TIM4 | PCLK1 | APB1 prescaler is not 1, so ×2 | 72 MHz | — | RM0008 section 7.2 |
| TIM1 | PCLK2 | APB2 prescaler is 1, so ×1 | 72 MHz | — | RM0008 section 7.2 |
| ADCCLK | PCLK2 | ÷6 | 12 MHz | 14 MHz | RM0008 section 11.1, DS5319 Table 47 |
| USBCLK | PLL | ÷1.5 | 48 MHz | Must be 48 MHz | RM0008 section 7.2.3 |

> [!WARNING]
> When an APB prescaler is not 1, the timers on that bus run at twice PCLK. With APB1 at 36 MHz, TIM2–TIM4 count at 72 MHz, not 36 MHz (RM0008 Rev 21 section 7.2). This C8 has only TIM2–TIM4 as general-purpose timers (DS5319 Table 2); the TIM5–TIM7 that appear in RM0008 do not exist on this chip.

The bus a peripheral sits on decides which clock it uses and which macro enables it. USART1 is on APB2 and runs from PCLK2; USART2 is on APB1 and runs from PCLK1 ([RM0008 Rev 21](#source-rm0008) section 3.3, Table 3). The figure below sorts the F1 peripherals by bus:

<p align="center">
  <img src="../../assets/diagrams/peripheral-bus.svg" width="760" alt="Which bus each peripheral hangs on">
  <br><sub>▲ Figure: which peripherals hang on AHB, APB1, and APB2 (vector drawing by the author)</sub>
</p>

### 8. Flash wait states

**Conclusion: Flash cannot be read as fast as the CPU runs. The higher the clock, the more clock cycles each Flash read has to wait; 72 MHz needs 2.**

A wait state is one extra clock cycle the CPU idles through when it reads Flash. The count goes in the LATENCY bits of FLASH_ACR, the Flash interface register at 0x40022000. Pick the row your target clock falls in ([RM0008 Rev 21](#source-rm0008) section 3.3.3):

| SYSCLK | LATENCY | Wait states |
| --- | --- | --- |
| 0 < SYSCLK ≤ 24 MHz | 000 | 0 |
| 24 MHz < SYSCLK ≤ 48 MHz | 001 | 1 |
| 48 MHz < SYSCLK ≤ 72 MHz | 010 | 2 |

The steps depend on SYSCLK only, not on the supply voltage. Voltage-dependent tables like the F4's (RM0090 section 3.5.1) do not apply to the F1.

- **Order**: when speeding up, add wait states first, then switch the clock; when slowing down, switch the clock first, then remove wait states. `HAL_RCC_ClockConfig()` follows this order.
- **Prefetch buffer**: two 64-bit buffers, on from reset, so the next instruction is usually already waiting in a buffer when the CPU fetches it. It must stay on whenever the AHB prescaler is not 1 (section 7.3.2, note on HPRE).
- **Getting it wrong**: set the PLL to ×9 and leave LATENCY at 0, and the CPU gives Flash less time to answer than its access time needs. Instruction fetch can go wrong, and the program runs off into the weeds or lands in HardFault, possibly only some of the time.

### 9. Enable the clock before touching registers, plus CSS and MCO

**Conclusion: switch on a peripheral's clock before its first register read or write. The system clock after power-up is HSI at 8 MHz, not the 72 MHz you entered in Cube; until `SystemClock_Config()` has run, any baud rate worked out for 72 MHz is wrong.**

While a peripheral's clock is off, software may not be able to read its registers, and reads always return 0 ([RM0008 Rev 21](#source-rm0008) section 7.3.7, note under RCC_APB2ENR). GPIOA's CRL, for example, resets to 0x4444 4444 (section 9.2.1); read it with the GPIOA clock off and you get 0.

The table gives one line each to three mechanisms, gating, CSS, and MCO; the last column is the HAL call for each:

| Mechanism | What it does | How to use it |
| --- | --- | --- |
| Peripheral clock gate | Until it is opened, the peripheral does not work and its registers read 0 | `__HAL_RCC_xxx_CLK_ENABLE()` first, then `HAL_xxx_Init()` |
| CSS (Clock Security System) | Falls back to HSI when HSE stops, and raises an NMI | `HAL_RCC_EnableCSS()`; call `HAL_RCC_NMI_IRQHandler()` in the NMI handler |
| MCO (microcontroller clock output) | Sends an internal clock out on PA8 for a scope | `HAL_RCC_MCOConfig()` |

**CSS in detail.** Once CSS is enabled, the detector starts only after HSE has started up. If HSE stops while running, hardware turns HSE off; if HSE was the system clock, directly or through the PLL, the system clock switches to HSI and the PLL is turned off too. At the same time an NMI (non-maskable interrupt) fires. The NMI handler must write the CSSC bit in RCC_CIR to clear the flag, or the NMI keeps coming back ([RM0008 Rev 21 section 7.2.7](#source-rm0008-rcc)). The same event also goes to the break input of the advanced-control timers, which on this C8 means TIM1 only. If the crystal never starts at all, CSS cannot help: the detector has not started yet, and `HAL_RCC_OscConfig()` times out waiting for HSE to become ready.

**MCO in detail.** MCO can output four clocks: SYSCLK, HSI, HSE, and PLL÷2, chosen by the MCO bits in RCC_CFGR (section 7.2.10). When SYSCLK is output, the manual requires it to stay at or below 50 MHz, the maximum I/O speed, so do not send the 72 MHz SYSCLK out directly; send PLL÷2 at 36 MHz instead. In HAL, `RCC_MCO1SOURCE_PLLCLK` on the F1 is PLL÷2, even though the name does not show the divide-by-2.

Motto: **enable the clock before touching a register; if HSE drops, CSS catches it; to see a frequency, use MCO.**

### 10. RCC_CFGR: the register bits behind the clock tree

Every setting above lands in RCC_CFGR, at 0x40021004, reset value 0x0000 0000. The table lists its fields from the high bits down ([RM0008 Rev 21 section 7.3.2](#source-rm0008-rcc)); the last column is this book's setting, so you can match each macro in the code to the bits it writes:

| Bits | Name | Values | Book setting |
| --- | --- | --- | --- |
| 26:24 | MCO | 0xx no output; 100 SYSCLK; 101 HSI; 110 HSE; 111 PLL÷2 | 111 (lab 2) |
| 22 | USBPRE | 0: PLL÷1.5; 1: not divided | 0 |
| 21:18 | PLLMUL | 0000 = ×2, 0001 = ×3, …, 0111 = ×9, …, 1110 = ×16, and 1111 is also ×16 | 0111 |
| 17 | PLLXTPRE | 0: HSE not divided; 1: HSE÷2 | 0 |
| 16 | PLLSRC | 0: HSI÷2; 1: HSE | 1 |
| 15:14 | ADCPRE | PCLK2 divided by: 00 ÷2, 01 ÷4, 10 ÷6, 11 ÷8 | 10 |
| 13:11 | PPRE2 | 0xx not divided; 100 ÷2; 101 ÷4; 110 ÷8; 111 ÷16 | 0xx |
| 10:8 | PPRE1 | Same encoding as PPRE2; software must keep PCLK1 at or below 36 MHz | 100 |
| 7:4 | HPRE | 0xxx not divided; 1000 ÷2, 1001 ÷4, 1010 ÷8, 1011 ÷16, 1100 ÷64 … 1111 ÷512; there is no ÷32 | 0xxx |
| 3:2 | SWS | Read-only: 00 HSI; 01 HSE; 10 PLL | Reads back 10 |
| 1:0 | SW | 00 HSI; 01 HSE; 10 PLL; 11 not allowed | 10 |

PLLSRC, PLLXTPRE, and PLLMUL can only be written while the PLL is off. SW is not only written by software: hardware forces it back to HSI on leaving Stop or Standby mode, or when CSS detects an HSE failure.

This table comes from section 7.3.2, which the low-, medium-, high-density and XL devices share. The connectivity line (F105/F107) has its RCC_CFGR in chapter 8, section 8.3.2, where PLLMUL is encoded differently; that section is void on STM32F103C8T6.

### 11. What changes when you change family

Conclusion: the F1 clock tree is one of the simplest. In another family, recheck the PLL structure, the top clock, and the wait-state steps. The table lists only what differs from the F1:

| Family | Max SYSCLK | PLL structure | Biggest difference from the F1 |
| --- | --- | --- | --- |
| F1 | 72 MHz | HSE or HSI÷2, then ×2 to ×16 | No PLLM, PLLN, or PLLP dividers |
| F4 | 168 MHz on F405/F407; 180 MHz on F42x/F43x with over-drive | M divider, N multiplier, P and Q outputs | The Q output gives 48 MHz for USB and other peripherals; Flash wait states step with voltage (RM0090 section 3.5.1) |
| G0 | 64 MHz | M divider, N multiplier, P, Q, and R outputs | The system clock comes from the R output ([RM0444](#source-rm0444)) |
| H7 | 480 MHz (H743 revision V) | Up to 3 PLLs | The clock steps are tied to the core voltage scale ([DS12110](#source-ds12110)) |

MCO differs too: the F1 has one output, on PA8; the F4 has two, MCO1 (PA8) and MCO2 (PC9) (RM0090).

## Hardware and wiring

This chapter's labs use only three things: the crystal already soldered on the board, a USB-to-serial adapter for printing, and an oscilloscope for MCO. Pin numbers are for LQFP48, from [DS5319 Rev 20](#source-ds5319) Table 5:

| Board | Peripheral/signal | Pin | Notes |
| --- | --- | --- | --- |
| BluePill | HSE crystal, 8 MHz | Pin 5 PD0-OSC_IN, pin 6 PD1-OSC_OUT | Already soldered; read the frequency printed on the crystal can first |
| BluePill | LSE crystal, 32.768 kHz | Pin 3 PC14-OSC32_IN, pin 4 PC15-OSC32_OUT | For the RTC; not used in this chapter |
| BluePill | BOOT0 jumper | Pin 44 BOOT0 | Keep at 0 to boot from Flash |
| USB-to-serial | USART1_TX → adapter RXD | Pin 30 PA9 | For printing in labs 1 and 3; 115200 8N1 (example setting) |
| USB-to-serial | USART1_RX ← adapter TXD | Pin 31 PA10 | This chapter only transmits, so this wire is optional |
| Oscilloscope | MCO output | Pin 29 PA8 | Frequency measurement in lab 2 |
| All | GND | GND | The adapter and the scope must share ground with the board |

```text
BluePill                              USB-to-serial adapter (3.3 V levels)
  PA9  (USART1_TX, pin 30) ────────►  RXD
  PA10 (USART1_RX, pin 31) ◄────────  TXD (optional)
  GND  ─────────────────────────────  GND

BluePill                              Oscilloscope
  PA8  (MCO, pin 29) ───────────────  probe tip
  GND  ─────────────────────────────  probe ground lead (as short as possible)

Already on the board: 8 MHz crystal on pins 5 and 6 (PD0/PD1); BOOT0 jumper at 0
```

Cross the serial lines: the board's TX goes to the adapter's RX. Wire TX to TX and the PC receives nothing at all.

## Code

The `main.c` below sets the clock to 72 MHz and then prints every clock, the Flash size, and the unique ID over USART1. It goes in the CubeMX project from chapter 01. First enable USART1 in CubeMX (Mode: Asynchronous, 115200 8N1, pins PA9/PA10), and keep the option from chapter 01 that generates a separate .c/.h pair per peripheral, so that `usart.c` provides `huart1` and `MX_USART1_UART_Init()`.

```c
/* main.c: print every clock, the Flash size, and the unique ID (STM32F103C8T6, HSE 8 MHz) */
#include "main.h"
#include "usart.h"
#include <stdio.h>

#define UART_TX_TIMEOUT_MS  100U    /* transmit timeout (example setting) */

void SystemClock_Config(void);

/* GCC's printf ends up in _write(); hand the characters to USART1 here */
int _write(int fd, char *ptr, int len)
{
    (void)fd;
    HAL_UART_Transmit(&huart1, (uint8_t *)ptr, (uint16_t)len, UART_TX_TIMEOUT_MS);
    return len;
}

int main(void)
{
    HAL_Init();
    SystemClock_Config();
    MX_USART1_UART_Init();

    /* device electronic signature (RM0008 chapter 30); both address macros come from the CMSIS header stm32f103xb.h */
    uint16_t flash_kb = *(const volatile uint16_t *)FLASHSIZE_BASE;      /* 0x1FFFF7E0 */
    const volatile uint32_t *uid = (const volatile uint32_t *)UID_BASE;  /* 0x1FFFF7E8 */

    printf("SYSCLK=%lu Hz, HCLK=%lu Hz\r\n",
           (unsigned long)HAL_RCC_GetSysClockFreq(), (unsigned long)HAL_RCC_GetHCLKFreq());
    printf("PCLK1=%lu Hz, PCLK2=%lu Hz\r\n",
           (unsigned long)HAL_RCC_GetPCLK1Freq(), (unsigned long)HAL_RCC_GetPCLK2Freq());
    printf("Flash=%u KB\r\n", (unsigned)flash_kb);
    printf("UID=%08lX-%08lX-%08lX\r\n",
           (unsigned long)uid[0], (unsigned long)uid[1], (unsigned long)uid[2]);

    while (1)
    {
    }
}

void SystemClock_Config(void)
{
    RCC_OscInitTypeDef       osc    = {0};
    RCC_ClkInitTypeDef       clk    = {0};
    RCC_PeriphCLKInitTypeDef periph = {0};

    osc.OscillatorType = RCC_OSCILLATORTYPE_HSE;
    osc.HSEState       = RCC_HSE_ON;
    osc.HSEPredivValue = RCC_HSE_PREDIV_DIV1;     /* PLLXTPRE = 0 */
    osc.HSIState       = RCC_HSI_ON;
    osc.PLL.PLLState   = RCC_PLL_ON;
    osc.PLL.PLLSource  = RCC_PLLSOURCE_HSE;       /* PLLSRC = 1 */
    osc.PLL.PLLMUL     = RCC_PLL_MUL9;            /* PLLMUL = 0111: 8 MHz × 9 = 72 MHz */
    if (HAL_RCC_OscConfig(&osc) != HAL_OK)
    {
        Error_Handler();                          /* a crystal that does not start ends up here */
    }

    clk.ClockType      = RCC_CLOCKTYPE_HCLK | RCC_CLOCKTYPE_SYSCLK
                       | RCC_CLOCKTYPE_PCLK1 | RCC_CLOCKTYPE_PCLK2;
    clk.SYSCLKSource   = RCC_SYSCLKSOURCE_PLLCLK; /* SW = 10 */
    clk.AHBCLKDivider  = RCC_SYSCLK_DIV1;         /* HCLK 72 MHz */
    clk.APB1CLKDivider = RCC_HCLK_DIV2;           /* PCLK1 36 MHz */
    clk.APB2CLKDivider = RCC_HCLK_DIV1;           /* PCLK2 72 MHz */
    if (HAL_RCC_ClockConfig(&clk, FLASH_LATENCY_2) != HAL_OK)   /* LATENCY = 010 */
    {
        Error_Handler();
    }

    periph.PeriphClockSelection = RCC_PERIPHCLK_ADC | RCC_PERIPHCLK_USB;
    periph.AdcClockSelection    = RCC_ADCPCLK2_DIV6;            /* ADCPRE = 10: 72 / 6 = 12 MHz */
    periph.UsbClockSelection    = RCC_USBCLKSOURCE_PLL_DIV1_5;  /* USBPRE = 0: 72 / 1.5 = 48 MHz */
    if (HAL_RCCEx_PeriphCLKConfig(&periph) != HAL_OK)
    {
        Error_Handler();
    }
}

void Error_Handler(void)
{
    __disable_irq();          /* park here; pause in the debugger to see where it stopped */
    while (1)
    {
    }
}
```

Piece by piece:

- `HAL_RCC_GetSysClockFreq()` and the functions next to it do not measure anything; they work the numbers out from the RCC register settings and `HSE_VALUE`. To know the real frequency, measure it with MCO in lab 2.
- `HAL_RCC_OscConfig()` starts HSE and waits for it to become ready, then configures the PLL and waits for it to lock, with a timeout at each step. If the crystal does not start, it returns a timeout, the program parks in `Error_Handler()`, and the system clock stays on HSI.
- `HAL_RCC_ClockConfig(&clk, FLASH_LATENCY_2)` writes the wait states first, then switches to the PLL, and finally updates the global `SystemCoreClock` and reprograms the 1 ms SysTick for the new clock.
- `HAL_RCCEx_PeriphCLKConfig()` writes ADCPRE and USBPRE. CubeMX generates this part only once you enable the ADC or USB; it is written out here so that every branch of the clock tree has a value.
- The 16-bit number at `FLASHSIZE_BASE` is the Flash size in KB (RM0008 section 30.1.1). The 96 bits from `UID_BASE` are the unique ID, different on every chip and often used as a serial number (section 30.2).
- `_write()` only works with GCC. Keil's C library does not go through `_write()`; override `fputc()` there instead.

The same job in registers follows this order: start HSE, add wait states, set the PLL and the three prescalers, start the PLL, switch SW.

```c
/* register version: from HSI after reset to 72 MHz, the same job as SystemClock_Config() above */
#include "stm32f1xx.h"

#define HSE_WAIT_LOOPS  0x5000U   /* polling limit while waiting for HSE (example setting) */

static int clock_to_72mhz(void)
{
    uint32_t n = 0U;

    RCC->CR |= RCC_CR_HSEON;                                   /* 1. start HSE */
    while ((RCC->CR & RCC_CR_HSERDY) == 0U)
    {
        if (++n > HSE_WAIT_LOOPS)
        {
            return -1;                                         /* crystal did not start: stay on HSI */
        }
    }

    FLASH->ACR = FLASH_ACR_PRFTBE                              /* 2. prefetch stays on */
               | (2U << FLASH_ACR_LATENCY_Pos);                /*    LATENCY = 010, wait states first */

    RCC->CFGR = (RCC->CFGR & ~(RCC_CFGR_HPRE | RCC_CFGR_PPRE1 | RCC_CFGR_PPRE2
                               | RCC_CFGR_ADCPRE | RCC_CFGR_USBPRE
                               | RCC_CFGR_PLLSRC | RCC_CFGR_PLLXTPRE | RCC_CFGR_PLLMULL))
              | RCC_CFGR_HPRE_DIV1                             /* 3. HCLK = 72 MHz */
              | RCC_CFGR_PPRE1_DIV2                            /*    PCLK1 = 36 MHz */
              | RCC_CFGR_PPRE2_DIV1                            /*    PCLK2 = 72 MHz */
              | RCC_CFGR_ADCPRE_DIV6                           /*    ADCCLK = 12 MHz; USBPRE cleared gives 48 MHz */
              | RCC_CFGR_PLLSRC                                /*    PLLSRC = 1: HSE */
              | RCC_CFGR_PLLMULL9;                             /*    PLLMUL = 0111: ×9 */

    RCC->CR |= RCC_CR_PLLON;                                   /* 4. start the PLL and wait for lock */
    while ((RCC->CR & RCC_CR_PLLRDY) == 0U)
    {
    }

    RCC->CFGR = (RCC->CFGR & ~RCC_CFGR_SW) | RCC_CFGR_SW_PLL;  /* 5. switch to the PLL */
    while ((RCC->CFGR & RCC_CFGR_SWS) != RCC_CFGR_SWS_PLL)
    {
    }

    SystemCoreClockUpdate();                                   /* bring SystemCoreClock up to date */
    return 0;
}
```

- Step 2 does not use `FLASH_ACR_LATENCY_2`. In the STM32CubeF1 CMSIS header `stm32f103xb.h`, that macro names bit 2 of the LATENCY field (0x4), so writing it gives 100, not "2 wait states". Write `2U << FLASH_ACR_LATENCY_Pos`, or use HAL's `FLASH_LATENCY_2`, which `stm32f1xx_hal_flash.h` defines as `FLASH_ACR_LATENCY_1`, value 0x2.
- Step 3 writes all the PLL and prescaler bits of RCC_CFGR at once. PLLSRC, PLLXTPRE, and PLLMUL only take the write because the PLL is still off.
- `SystemCoreClockUpdate()` is a CMSIS function that recomputes `SystemCoreClock` from the registers. If the project also uses HAL, call `HAL_InitTick(TICK_INT_PRIORITY)` next, or `HAL_Delay()` keeps timing as if the clock were 8 MHz.

The MCO output for lab 2 is one line, placed after `MX_USART1_UART_Init()`:

```c
HAL_RCC_MCOConfig(RCC_MCO1, RCC_MCO1SOURCE_HSE, RCC_MCODIV_1);       /* PA8 outputs HSE: 8 MHz */
/* use this line instead and PA8 outputs PLL÷2: 36 MHz
HAL_RCC_MCOConfig(RCC_MCO1, RCC_MCO1SOURCE_PLLCLK, RCC_MCODIV_1); */
```

`HAL_RCC_MCOConfig()` enables the GPIOA clock itself and sets PA8 to alternate-function push-pull at the 50 MHz speed setting.

For lab 3, replace the oscillator part of `SystemClock_Config()` with the lines below; no crystal is needed:

```c
osc.OscillatorType      = RCC_OSCILLATORTYPE_HSI;
osc.HSIState            = RCC_HSI_ON;
osc.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;   /* HSITRIM at its default, 16 */
osc.PLL.PLLState        = RCC_PLL_ON;
osc.PLL.PLLSource       = RCC_PLLSOURCE_HSI_DIV2;       /* PLLSRC = 0: 8 / 2 = 4 MHz */
osc.PLL.PLLMUL          = RCC_PLL_MUL16;                /* PLLMUL = 1110: 4 × 16 = 64 MHz */
```

## Hands-on labs

1. **Lab 1: print every clock.** Build and download the `main.c` above, open the adapter's serial port on the PC in a terminal at 115200 8N1, and press reset.
   - Expected: the port prints `SYSCLK=72000000 Hz, HCLK=72000000 Hz`, `PCLK1=36000000 Hz, PCLK2=72000000 Hz`, `Flash=64 KB`, and a UID line.
   - How to check: compare each value with the clock table in section 7; run it on a second board and the UID should differ.
   - If it fails, check first: if nothing arrives, check that TX and RX are crossed and that ground is connected; if you see garbage, check that `HSE_VALUE` matches the crystal on the board; if the Flash size is not 64 KB, read the chip marking first, because compatible chips from other vendors may carry a different electronic signature (rule of thumb).
2. **Lab 2: measure the real frequency with MCO.** Add the MCO line, put the scope probe on PA8 and its ground lead on GND.
   - Expected: first an 8 MHz square wave; after switching to the PLL÷2 line, 36 MHz.
   - How to check: read the scope's frequency measurement; the 8 MHz output should be off by no more than the crystal's rated tolerance. To see the 36 MHz output as a square wave, the scope needs 100 MHz of bandwidth or more (rule of thumb); with less, the waveform looks close to a sine, but the frequency reading is still valid.
   - If it fails, check first: if PA8 shows nothing, confirm that `HAL_RCC_MCOConfig()` actually runs; a cheap logic analyzer sampling at 24 MHz cannot measure 36 MHz, and on the 8 MHz output it gets only 3 samples per period, so the reading jumps (rule of thumb).
3. **Lab 3: run without the crystal.** Swap in the HSI oscillator lines, leave everything else alone, and download again.
   - Expected: the port prints `SYSCLK=64000000 Hz, HCLK=64000000 Hz` and `PCLK1=32000000 Hz, PCLK2=64000000 Hz`, and the serial port still works.
   - How to check: `8 / 2 × 16 = 64` MHz; 64 MHz is still in the 48–72 MHz step, so `FLASH_LATENCY_2` stays. When the crystal will not start, use this setup to prove the chip itself is fine before you go after the crystal and its solder joints.
   - If it fails, check first: whether `PLLSource` was changed to `RCC_PLLSOURCE_HSI_DIV2`. USB cannot be used in this setup, because 64 MHz is neither 48 nor 72 MHz.

## Self-test

1. HSE is 8 MHz, PLLXTPRE = 1, PLLMUL = 1110. What is SYSCLK? What should LATENCY be?
2. HCLK = 72 MHz and PPRE1 is set to 101. What is PCLK1? What is TIM2's counter clock?
3. You need USB but want to lower the clock to 48 MHz. How do you set PLLMUL, USBPRE, LATENCY, and the APB1 prescaler?
4. You wrote `GPIOA->CRL` but forgot to enable the GPIOA clock, and it reads back 0. Why? With the clock on, right after reset, what should it read?
5. The 16-bit value at address 0x1FFFF7E0 reads 0x0040. How much Flash does this chip have?

Answers:

1. PLL input = 8 / 2 = 4 MHz (inside 1–25 MHz), ×16 = 64 MHz. 48 < 64 ≤ 72, so LATENCY = 010, which is 2 wait states.
2. 101 is ÷4, so PCLK1 = 72 / 4 = 18 MHz. The APB1 prescaler is not 1, so the timer clock is doubled: TIM2 = 36 MHz.
3. 8 × 6 = 48 MHz, so PLLMUL = 0100; USBPRE = 1 (not divided), so USBCLK = 48 MHz. 24 < 48 ≤ 48, so LATENCY = 001, which is 1 wait state. APB1 undivided would be 48 MHz, over 36 MHz, so PPRE1 = 100 (÷2) and PCLK1 = 24 MHz.
4. The note in RM0008 section 7.3.7: while a peripheral's clock is off, software may not be able to read its registers, and reads always return 0. With the clock on, right after reset, CRL reads its reset value, 0x4444 4444 (section 9.2.1).
5. 0x0040 = 64, in KB, so 64 KB (RM0008 section 30.1.1).

## Principle and scope

> [!NOTE]
> From this section to "Pitfalls and sources" is the deep part. It pins the conclusions above to one part number, one manual section, and numbers you can recompute. On a first read you can skip it and come back after the labs.

The clock conclusions in this chapter are pinned to order code STM32F103C8T6 in LQFP48.

**Clock source and multiplier.** HSE enters on pin 5 PD0-OSC_IN and pin 6 PD1-OSC_OUT at 8 MHz. `PLLXTPRE=0` (HSE is not prescaled), `PLLSRC=1` (the PLL input is HSE), `PLLMUL=0111` (×9), and `8 × 9 = 72` MHz. With `SW=10`, SYSCLK uses the PLL. Source: [RM0008 Rev 21 section 7.3.2](#source-rm0008-rcc).

**The three buses.** HPRE divides by 1, so HCLK = 72 MHz. PPRE1 = `100` (÷2), so PCLK1 = 36 MHz, and it must not exceed 36 MHz. PPRE2 divides by 1, so PCLK2 = 72 MHz.

**Timer clocks.** When an APB prescaler is not 1, the timers on that bus run at twice PCLK, so TIM2–TIM4 run at 72 MHz. TIM1 is on APB2 with a prescaler of 1, so it is not doubled and also runs at 72 MHz. On this C8, APB1 carries only three general-purpose timers, TIM2–TIM4 (DS5319 Table 2).

**Flash wait states.** `FLASH_ACR` is at base `0x40022000`, offset `0x00`. LATENCY for the 48 MHz to 72 MHz step is `010`, which is 2; from 0 to 24 MHz it is 0, and from 24 to 48 MHz it is 1. The F1 steps by SYSCLK only, with no voltage steps, and the table holds over the whole 2.0–3.6 V operating range (DS5319 Table 9). Setting the PLL to ×9 while LATENCY stays at 0 makes instruction fetch fail; that is the failure path on the key figure.

**USB and ADC.** With `USBPRE=0`, the 72 MHz PLL is divided by 1.5, giving 48 MHz. `USBPRE=1` does not divide, giving 72 MHz, which is not 48 MHz. `ADCPRE=10` is PCLK2÷6, and `72 / 6 = 12` MHz. `ADCPRE=01` is ÷4, which gives 18 MHz and crosses the RM0008 ceiling of 14 MHz. Sample time and successive approximation stay in chapter 09; this chapter does not cover them.

**CSS.** When HSE stops and CSS is on, if HSE is the system clock directly or through the PLL, hardware switches to HSI and turns HSE off; if HSE was the PLL input, the PLL turns off too. The CSS interrupt is wired to the NMI. The NMI handler writes CSSC in `RCC_CIR`, or the NMI keeps coming back. The same event also reaches the break input of the advanced-control timers, which on this C8 means TIM1 only. After power-up the system clock is HSI at 8 MHz, not the 72 MHz entered in Cube. How the NMI preempts other interrupts is in chapter 04 and is not repeated here.

**MCO.** Pin 29 PA8 includes MCO among its alternate functions; the pin is in [DS5319 Rev 20 Figure 8](#source-ds5319-clock). `MCO=111` outputs PLL÷2, which is 36 MHz, under the 50 MHz I/O limit in the manual. `MCO=100` outputs SYSCLK, and 72 MHz crosses that 50 MHz limit. The normal path is 36 MHz. HSE bypass is only for a clock fed in from outside (up to 25 MHz); a passive crystal does not use bypass.

**The connectivity-line section is void.** Section 8.3.2's `OTGFSPRE`, its reserved `PLLMUL` encoding `000x`, and its ×6.5 are void on STM32F103C8T6. This C8 uses section 7.3.2 for `RCC_CFGR`: `0111` is still ×9, and `0000` is ×2.

**When you change chips.** On a connectivity-line F105/F107, the section 7.3.2 statements above are void; read section 8.3.2 instead. On an F4, recheck the wait states against its voltage steps (RM0090 section 3.5.1), and the PLL becomes the M/N/P/Q structure.

## Key figures

<p align="center">
  <img src="../../assets/diagrams/sample-02-clock-tree.svg" width="760" alt="72 MHz needs two Flash wait states; after HSE stops, the system clock returns to HSI at 8 MHz">
  <br><sub>▲ Drawn for this book. STM32F103C8T6, LQFP48. Pin 5 PD0 and pin 6 PD1 bring in 8 MHz; PLLMUL=0111, PLLSRC=1, and PLLXTPRE=0 produce 72 MHz. PCLK1 = 36 MHz, PCLK2 = 72 MHz, the APB1 timers = 72 MHz, ADCCLK = 12 MHz, and USBPRE=0 produces 48 MHz. The normal path has LATENCY = 2, and MCO on pin 29 PA8 is 36 MHz. The failure path is the same tree with LATENCY still 0. After HSE stops, SYSCLK returns to HSI at 8 MHz and the NMI handler writes CSSC. 18 MHz crosses 14 MHz, and driving 72 MHz straight out of MCO crosses 50 MHz; those two statements stay in the margin notes. Sources: [RM0008 Rev 21 sections 7.3.2 and 7.2.7](#source-rm0008-rcc) and [DS5319 Rev 20 Figure 8](#source-ds5319-clock).</sub>
</p>

<p align="center">
  <img src="../../assets/gif/clock-css.gif" width="640" alt="After HSE disappears, the system clock falls from 72 MHz back to HSI at 8 MHz">
  <br><sub>▲ Auxiliary figure for the web and the article channel. It only plays the CSS return to HSI. Print uses the static figure. The fetch failure with LATENCY still 0 is not on this GIF.</sub>
</p>

Read the main figure in three layers. The top layer is the normal path: 8 MHz comes in on pins 5 and 6, goes through PLL ×9 to 72 MHz, and splits to the three buses, the timers, the ADC, and USB, with LATENCY = 2 and 36 MHz measurable on PA8. The middle layer is the failure path: the same tree with LATENCY left at 0, so instruction fetch fails. The bottom layer is CSS: after HSE stops, the system clock returns to HSI at 8 MHz, and the NMI keeps coming until software writes CSSC.

Two labels on the figure need the text beside them. "TIM2-TIM7" follows RM0008 Figure 8: that clock tree is shared by the whole F1 series, and its APB1 branch lists TIM2–TIM7 and TIM12–TIM14; this C8 has only TIM2–TIM4 (DS5319 Table 2). "电压档 2.7-3.6 V" (voltage range 2.7–3.6 V) is how F4-class parts describe wait states; F1 wait states have no voltage steps and depend on SYSCLK only (RM0008 section 3.3.3).

The opening `clock-tree.svg` stays a side figure. You do not need to play it: 72 MHz, LATENCY, and the CSS return to HSI are all on this static figure.

## Timing and state

The table runs top to bottom through one clock setup after power-up. The row marked "Failure" is the branch taken when LATENCY was not raised; the CSS and Stop rows are cases where hardware changes the clock while running; the last row is the ADC clock. The register bits come from [RM0008 Rev 21 sections 7.3.1 and 7.3.2](#source-rm0008-rcc), and the start-up and lock times from DS5319 Rev 20 Tables 22 and 27.

| Phase | SWS / switch | Clock | State |
| --- | --- | --- | --- |
| Reset | SWS = 00, HSI | HSI 8 MHz | The system clock is not yet the 72 MHz entered in Cube |
| Start HSE | HSEON = 1, wait for HSERDY | 8 MHz, in on pins 5 and 6 | A crystal typically starts in 2 ms; the PLL is not on yet |
| Set up the PLL | PLLMUL=0111, PLLSRC=1, PLLXTPRE=0, then PLLON = 1, wait for PLLRDY | PLL output 72 MHz | Lock takes at most 200 µs; those three fields can only be written while the PLL is off |
| Write the wait states | LATENCY = 2 | SYSCLK still HSI 8 MHz | Wait states first, then switch SW |
| Switch to the PLL | SW=10, SWS reads back 10 | SYSCLK = HCLK = 72 MHz | PCLK1 = 36 MHz, PCLK2 = 72 MHz, USBPRE=0 produces 48 MHz |
| Failure: wait states still 0 | LATENCY = 0 | 72 MHz | Instruction fetch fails |
| CSS | HSE fails, CSSON = 1 | SYSCLK returns to HSI 8 MHz | HSE and the PLL are off. The NMI stays pending until software writes CSSC |
| Stop, then wake-up | On entry, hardware clears PLLON and HSEON; on wake-up, SW returns to HSI | HSI 8 MHz | After wake-up, HSE and the PLL must be started again (chapter 16) |
| ADC | ADCPRE=10 | 12 MHz | ADCPRE=01 produces 18 MHz and crosses 14 MHz |

This table does not include the ADC sample time.

## Pitfalls and sources

| Symptom | Cause | What to do | Source | What the source supports |
| --- | --- | --- | --- | --- |
| The core stops as soon as the PLL is set to ×9 | LATENCY is still 0 | Write LATENCY = 2 before switching SYSCLK | [RM0008](#source-rm0008-rcc) | The 48–72 MHz step is 2 wait states |
| PWM frequency is off by 2× | The calculation used PCLK1, 36 MHz | Use the 72 MHz timer clock | [RM0008](#source-rm0008-rcc) | When the APB prescaler is not 1, the timer clock is doubled. TIM1 on APB2 with prescaler 1 is not doubled |
| Touching the crystal while running leaves the program stuck in the NMI | CSS is on and the NMI handler does not write CSSC | Call `HAL_RCC_NMI_IRQHandler()` in the NMI handler to write CSSC, then set the clock up again from HSI | [RM0008](#source-rm0008-rcc) | On an HSE failure SYSCLK switches to HSI; if HSE fed the PLL, the PLL turns off too; without CSSC the NMI keeps coming back |
| PLLMUL was filled in from section 8.3.2 | That section is the connectivity line | This C8 uses section 7.3.2. 0111 is still ×9 and 0000 is ×2 | [RM0008](#source-rm0008-rcc) | The connectivity-line reserved encoding 000x and OTGFSPRE are void on STM32F103C8T6 |
| The waveform on MCO is too fast for the pin | SYSCLK at 72 MHz was driven straight onto PA8 | Output PLL÷2, which is 36 MHz | [RM0008](#source-rm0008-rcc) | SYSCLK sent to the MCO pin must not exceed 50 MHz |
| The ADC was set to ÷4 to go faster | ADCPRE=01 produces 18 MHz | Go back to ÷6, which gives 12 MHz | [RM0008](#source-rm0008-rcc) | 14 MHz is the ceiling. ÷4 gives 18 MHz. Sample time stays in chapter 09 |
| A peripheral's registers read 0 whatever you write | That peripheral's clock is not enabled | `__HAL_RCC_xxx_CLK_ENABLE()` first, then configure | [RM0008](#source-rm0008) | The note in section 7.3.7: while the peripheral clock is off, register reads always return 0 |
| Register code meant for 72 MHz wrote 100 into the wait states | CMSIS `FLASH_ACR_LATENCY_2` was taken to mean "2 wait states" | Write `2U << FLASH_ACR_LATENCY_Pos`, or use HAL's `FLASH_LATENCY_2` | [RM0008](#source-rm0008) | Section 3.3.3 defines only three LATENCY values: 000, 001, and 010 |

## Related resources

- Official manuals: **RM0008** (chapter 2 memory map, chapter 8 RCC, chapter 30 device electronic signature); **DS5319** (F103C8 datasheet)
- Previous: [01 Setting Up the Development Environment](01-dev-environment.md) | Next: [03 GPIO and LEDs](03-gpio-and-led.md)
- Figures: [`assets/animations/clock-tree.svg`](../../assets/animations/clock-tree.svg), [`assets/animations/memory-map.svg`](../../assets/animations/memory-map.svg), [`assets/diagrams/peripheral-bus.svg`](../../assets/diagrams/peripheral-bus.svg)
- Hardware and documents: the product-selector pages for each family on ST's website
- Disclaimer: every illustration in this repo is a vector drawing or a program-generated animation by the author, not a manufacturer's photograph.

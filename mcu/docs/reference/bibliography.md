---
title: 参考文献
description: 全站引证的一手资料总表：芯片手册与内核文档的版本号、总线协议规范、C 标准与 ABI、经典论文（带 DOI）、书、以及被逐行引用的上游代码基准。章节里的 [D2] 这类标签都指到这里。
---

# 参考文献

> 🎯 教程里每一句"手册说""标准规定""论文证明过"，都该能翻到原文。这页是全站的脚注总表：**版本号写死、DOI 可点、没核过的就明说没核过。**

## 怎么用这页

- 章节末尾的"延伸阅读"用 `[D2]` 这样的标签指向本页对应条目；标签前的字母就是下面的分区（A 芯片 · B 总线 · C 语言与工具链 · D 论文 · E 书 · F 代码）。
- **版本号是口径的一部分。** 寄存器位、行号、API 名都对着表里那一版说话；你手里若是别的版本，先对一下，再决定要不要信这页。
- 标注"**未核版本**"的条目，是本站引用过内容但没把 PDF 的修订号核进来的：读者以官网当前版为准，别把这页当权威。
- 论文都给了 DOI（`https://doi.org/<DOI>`），经 Crossref 核对过题名、期刊/会议、年份与页码；大多数在 ACM/IEEE 付费墙后，作者主页或学校仓库常有预印本。

## A　芯片与内核官方文档 {#chips}

| 标签 | 资料 | 版本 / 日期 | 本站用在 |
|---|---|---|---|
| A1 | ST **RM0090** *STM32F405/415, F407/417, F427/437, F429/439 Reference Manual* | Rev 22，2026-05 | S 篇全部寄存器口径；[S2](../stm32/02-rcc-clock.md) 时钟树、[S8](../stm32/08-dma.md) DMA 请求映射表、[S14](../stm32/14-pwr.md) 三档低功耗 |
| A2 | ST **DS8626** *STM32F405xx/407xx Datasheet* | Rev 12，2026-03 | 引脚复用表、电气参数、[S9](../stm32/09-adc.md) 采样时间 |
| A3 | ST **PM0214** *STM32 Cortex-M4 Programming Manual* | 未核版本 | [S4](../stm32/04-nvic-exti.md) NVIC/SCB、[S16](../stm32/16-debug-hardfault.md) 故障寄存器 |
| A4 | ST **CMSIS 器件头文件** `stm32f407xx.h` | [STMicroelectronics/cmsis_device_f4](https://github.com/STMicroelectronics/cmsis_device_f4) | 基址与位域的第二来源（GPIOF=0x40021400、RCC=0x40023800、AHB1ENR=0x30 …） |
| A5 | Arm **Cortex-M4 Technical Reference Manual**（DDI 0439） | 未核版本 | [S1](../stm32/01-arch.md) 内核框图、[S5](../stm32/05-systick.md) SysTick |
| A6 | Arm **ARMv7-M Architecture Reference Manual**（DDI 0403E.e） | E.e | 异常入栈帧、EXC_RETURN、懒堆叠的权威定义（[F2](../rtos/freertos/02-context-switch.md)） |
| A7 | Espressif **ESP32-S3 Technical Reference Manual** | 未核版本 | P 篇 GPIO 矩阵、LEDC、I2S、看门狗寄存器 |
| A8 | Espressif **ESP32-S3 Series Datasheet** | 未核版本 | 引脚、电气、模组 N16R8 的 PSRAM 占用（IO35/36/37） |
| A9 | Espressif **ESP-IDF Programming Guide** | v5.5.2（与代码基准同版） | P 篇全部 API；网页右上角务必选 v5.5 |
| A10 | GigaDevice **GD32F4xx User Manual** | Rev 3.0，2024-01 | [G1](../gd32/01-rcu-clock.md)–[G4](../gd32/04-periph-diff.md) 逐字段对照 |
| A11 | GigaDevice **GD32F407xx Datasheet** | Rev 2.7 | G 篇引脚与 AF 表 |
| A12 | GigaDevice **GD32F470 Product Brief** | — | [G0](../gd32/00-env.md) 选型对比 |
| A13 | GigaDevice **GD32VF103 User Manual** | Rev 1.0，2019-06 | V 篇外设（RCU/GPIO/USART） |
| A14 | Nuclei **Bumblebee Core Datasheet** | Rev 1.0，2019-08-28 | [V1](../gd32/06-clic-irq.md) ECLIC、[V3](../gd32/08-mtime-delay.md) MTIME/MTIMECMP 与 1/4 主频 |

## B　总线与协议规范 {#buses}

| 标签 | 资料 | 版本 / 日期 | 本站用在 |
|---|---|---|---|
| B1 | NXP **UM10204** *I²C-bus specification and user manual* | Rev. 7，2021-10 | [S11](../stm32/11-i2c.md) 起始/停止/ACK 时序、[E05](../lab/e05-i2c-eeprom.md) 抓包判读 |
| B2 | Motorola/Freescale **SPI Block Guide**（S12SPIV3） | V03.06 | [S12](../stm32/12-spi.md) CPOL/CPHA 四模式的出处——SPI 没有正式标准，这份就是"事实标准" |
| B3 | Philips **I²S bus specification** | 1986-02，1996-06-05 修订 | [P12](../esp32/12-audio-path.md) 左右声道/WS 时序 |
| B4 | USB-IF **Universal Serial Bus Specification** | Revision 2.0，2000-04-27 | [G4](../gd32/04-periph-diff.md) USBHS 背景 |
| B5 | **UTMI+ Low Pin Interface (ULPI) Specification** | Revision 1.1，2004-10-20 | [G4](../gd32/04-periph-diff.md)：GD32F4 与 F407 的 ULPI 12 根信号同脚同 AF |
| B6 | Robert Bosch GmbH **CAN Specification** · ISO **11898-1:2015** | Version 2.0，1991 · 2015 | [G4](../gd32/04-periph-diff.md) bxCAN 位时序逐位对照 |

## C　语言、ABI 与工具链 {#toolchain}

| 标签 | 资料 | 版本 / 日期 | 本站用在 |
|---|---|---|---|
| C1 | ISO/IEC **9899:2011**（C11）；免费草案 WG14 **N1570** | 2011-04-12 | [C3](../c/03-volatile.md) §5.1.2.3 as-if 与 volatile、[C7](../c/07-ub-misra.md) 附录 J.2 未定义行为清单 |
| C2 | MISRA **C:2012**（含 Amendment）· MISRA **C:2023** | 2013 · 2023 | [C7](../c/07-ub-misra.md) 规则取舍 |
| C3 | TIS **Executable and Linking Format (ELF) Specification** | Version 1.2，1995-05 | [B2](../build/02-elf.md) 文件视图/段视图两副目录 |
| C4 | Arm **Procedure Call Standard for the Arm Architecture**（AAPCS32，IHI 0042） | [ARM-software/abi-aa](https://github.com/ARM-software/abi-aa) 当前版 | [C4](../c/04-struct-abi.md) 对齐与填充、[C6](../c/06-abi-stack.md) r0–r3/栈传参/偶奇寄存器对 |
| C5 | Arm **AN298** *Cortex-M4(F) Lazy Stacking and Context Switching*（DAI0298A） | 2012-03 | [F2](../rtos/freertos/02-context-switch.md) 为什么大多数中断不付 FPU 帧的钱 |
| C6 | Arm **Cortex-M4 Devices Generic User Guide**（DUI 0553） | 未核版本 | S 篇 CMSIS 内核函数（`__WFI`、`NVIC_*`）口径 |
| C7 | **GNU ld** 手册（binutils） | [sourceware.org/binutils/docs/ld](https://sourceware.org/binutils/docs/ld/) | [B3](../build/03-linker-script.md) MEMORY/SECTIONS 语法；区域属性只认 r/w/x/a/i/l |
| C8 | **RISC-V ISA**：Vol. I Unprivileged · Vol. II Privileged | 20191213 · 20211203 | [V0](../gd32/05-riscv-toolchain.md) 指令集、[V3](../gd32/08-mtime-delay.md) mtime/mtimecmp 语义、CSR 编号 |
| C9 | RISC-V **Core-Local Interrupt Controller (CLIC)** 规范草案 | [riscv/riscv-fast-interrupt](https://github.com/riscv/riscv-fast-interrupt) | [V1](../gd32/06-clic-irq.md)：Bumblebee 的 ECLIC 是它的增强实现 |

## D　经典论文 {#papers}

| 标签 | 文献 | 本站用在 |
|---|---|---|
| D1 | C. L. Liu, J. W. Layland. **Scheduling Algorithms for Multiprogramming in a Hard-Real-Time Environment.** *J. ACM* 20(1): 46–61, 1973. DOI [10.1145/321738.321743](https://doi.org/10.1145/321738.321743) | [F3](../rtos/freertos/03-scheduler.md)：固定优先级抢占式调度为什么成立，速率单调怎么排优先级、69.3% 利用率上界从何而来 |
| D2 | L. Sha, R. Rajkumar, J. P. Lehoczky. **Priority Inheritance Protocols: An Approach to Real-Time Synchronization.** *IEEE Trans. Computers* 39(9): 1175–1185, 1990. DOI [10.1109/12.57058](https://doi.org/10.1109/12.57058) | [F5](../rtos/freertos/05-sem-mutex.md) 互斥量的优先级继承、[R2](../rtos/rtthread/02-ipc.md)、[E04](../lab/e04-priority-inversion.md) |
| D3 | M. Masmano, I. Ripoll, A. Crespo, J. Real. **TLSF: a New Dynamic Memory Allocator for Real-Time Systems.** *Proc. ECRTS 2004*, pp. 79–88. DOI [10.1109/EMRTS.2004.1311009](https://doi.org/10.1109/EMRTS.2004.1311009) | [R3](../rtos/rtthread/03-mem.md) 两级隔离适配 O(1) 分配的原始出处、[对照篇](../rtos/compare/00-side-by-side.md) |
| D4 | P. R. Wilson, M. S. Johnstone, M. Neely, D. Boles. **Dynamic Storage Allocation: A Survey and Critical Review.** *IWMM 1995*, LNCS 986, pp. 1–116. DOI [10.1007/3-540-60368-9_19](https://doi.org/10.1007/3-540-60368-9_19) | [F7](../rtos/freertos/07-heap.md)、[R3](../rtos/rtthread/03-mem.md)：碎片到底是什么、首次适配/最佳适配/隔离适配各自的代价 |
| D5 | L. Lamport. **Proving the Correctness of Multiprocess Programs.** *IEEE Trans. Software Eng.* SE-3(2): 125–143, 1977. DOI [10.1109/TSE.1977.229904](https://doi.org/10.1109/TSE.1977.229904) | [C5](../c/05-func-pointer.md)：单生产者单消费者环形缓冲不加锁为什么是对的 |
| D6 | J. L. McCreary, P. R. Gray. **All-MOS Charge Redistribution Analog-to-Digital Conversion Techniques — Part I.** *IEEE J. Solid-State Circuits* 10(6): 371–379, 1975. DOI [10.1109/JSSC.1975.1050629](https://doi.org/10.1109/JSSC.1975.1050629) | [S9](../stm32/09-adc.md)：片上 SAR ADC 的电容阵列电荷再分配，就是这篇定下来的 |
| D7 | E. Eide, J. Regehr. **Volatiles Are Miscompiled, and What to Do About It.** *Proc. EMSOFT 2008*, pp. 255–264. DOI [10.1145/1450058.1450093](https://doi.org/10.1145/1450058.1450093) | [C3](../c/03-volatile.md)：十三款编译器里 volatile 被错编的实测，以及"用访问函数包一层"的对策 |
| D8 | X. Wang, N. Zeldovich, M. F. Kaashoek, A. Solar-Lezama. **Towards Optimization-Safe Systems: Analyzing the Impact of Undefined Behavior.** *Proc. SOSP 2013*, pp. 260–275. DOI [10.1145/2517349.2522728](https://doi.org/10.1145/2517349.2522728) | [C7](../c/07-ub-misra.md)：优化器利用 UB 删掉你的安全检查的真实案例集 |
| D9 | P. Koopman, T. Chakravarty. **Cyclic Redundancy Code (CRC) Polynomial Selection for Embedded Networks.** *Proc. DSN 2004*, pp. 145–154. DOI [10.1109/DSN.2004.1311885](https://doi.org/10.1109/DSN.2004.1311885) | [C8](../c/08-framed-protocol.md) 为什么选 CRC-16/CCITT 而不是随手挑一个多项式、[P10](../esp32/10-flash-nvs-ota.md) NVS 的 CRC32 |
| D10 | E. W. Dijkstra. **Solution of a Problem in Concurrent Programming Control.** *Commun. ACM* 8(9): 569, 1965. DOI [10.1145/365559.365617](https://doi.org/10.1145/365559.365617) | [F5](../rtos/freertos/05-sem-mutex.md)、[C5](../c/05-func-pointer.md)：互斥这件事的起点，一页纸 |
| D11 | G. Reeves. **What Really Happened on Mars?** *RISKS Digest* 19.49, 1997-12. | [F5](../rtos/freertos/05-sem-mutex.md)、[E04](../lab/e04-priority-inversion.md)：火星探路者优先级反转事故的一手复盘（JPL 工程师原文） |
| D12 | J. Ganssle. **Great Watchdog Timers for Embedded Systems.** [ganssle.com（Wayback 存档）](https://web.archive.org/web/20241214122124/https://www.ganssle.com/watchdogs.htm) | [S17](../stm32/17-watchdog-reset.md)、[P13](../esp32/13-watchdog-health.md)：窗口看门狗为什么比"定时喂狗"可靠 |
| D13 | S. Cheshire, M. Baker. **Consistent Overhead Byte Stuffing.** *IEEE/ACM Trans. Networking* 7(2): 159–172, 1999. DOI [10.1109/90.769765](https://doi.org/10.1109/90.769765) | [C8](../c/08-framed-protocol.md)：0x00 只当帧尾、开销有固定上限——帧协议选 COBS 而不是转义或长度前缀的理由 |

## E　书 {#books}

| 标签 | 书 | 本站用在 |
|---|---|---|
| E1 | Joseph Yiu. *The Definitive Guide to ARM Cortex-M3 and Cortex-M4 Processors*, 3rd ed. Newnes, 2013. ISBN 978-0-12-408082-9 | S1/S4/S16、F2：异常模型、双栈指针、懒堆叠的教科书级讲法 |
| E2 | John R. Levine. *Linkers and Loaders*. Morgan Kaufmann, 2000. ISBN 1-55860-496-0 | [B2](../build/02-elf.md)–[B4](../build/04-startup.md)：符号决议与重定位的通史 |
| E3 | 俞甲子、石凡、潘爱民.《程序员的自我修养——链接、装载与库》. 电子工业出版社, 2009. ISBN 978-7-121-08511-9 | B 篇最佳中文伴侣书 |
| E4 | Richard Barry. *Mastering the FreeRTOS Real Time Kernel — A Hands-On Tutorial Guide*, v1.1.0. [FreeRTOS/FreeRTOS-Kernel-Book](https://github.com/FreeRTOS/FreeRTOS-Kernel-Book) | F 篇 API 口径（本站讲内核源码，它讲怎么用） |
| E5 | Donald E. Knuth. *The Art of Computer Programming, Vol. 1*, 3rd ed., §2.5 Dynamic Storage Allocation. Addison-Wesley, 1997 | [F7](../rtos/freertos/07-heap.md)：边界标记法与伙伴系统——heap_4 合并相邻空闲块的祖师爷 |
| E6 | Brian W. Kernighan, Dennis M. Ritchie. *The C Programming Language*, 2nd ed. Prentice Hall, 1988. ISBN 0-13-110362-8 | C 篇默认先修 |
| E7 | 刘火良、杨森.《RT-Thread 内核实现与应用开发实战指南——基于 STM32》. 机械工业出版社, 2019 | R 篇伴侣书（从零手写内核的路线） |

## F　被逐行引用的代码基准 {#code}

本站 F/R/P/G/V 篇里的"第 N 行"全部对着下面这些版本说话；CI 也按同一版本拉取、编译（`.github/workflows/quality.yml`）。

| 标签 | 仓库 | 固定版本 | 说明 |
|---|---|---|---|
| F1 | [FreeRTOS/FreeRTOS-Kernel](https://github.com/FreeRTOS/FreeRTOS-Kernel) | **V11.1.0**，`portable/GCC/ARM_CM4F` | F 篇全部行号；ESP-IDF 内置的是 V10.5.1 SMP 改版，行号/结论不混读 |
| F2 | [espressif/esp-idf](https://github.com/espressif/esp-idf) | **v5.5.2** | P 篇驱动框架、`soc_caps.h` 结论；CI 用 `espressif/idf:v5.5.2` 容器干净构建 |
| F3 | [STMicroelectronics/cmsis_device_f4](https://github.com/STMicroelectronics/cmsis_device_f4) | **v2.6.11**（`stm32f407xx.h`，sha256 `bd21220e…`）+ [ARM-software/CMSIS_5](https://github.com/ARM-software/CMSIS_5) **5.9.0** 的 `core_cm4.h`（sha256 `f5b63d52…`） | 寄存器基址/位域第二来源；CI 的 `arm-host` job 按这两个版本拉取并逐字节校验，`probe.sh` 的位号与地址对账吃的就是它 |
| F4 | [STMicroelectronics/stm32f4xx_hal_driver](https://github.com/STMicroelectronics/stm32f4xx_hal_driver) | `@ 1f6451c` | S2/S7 的上游对照 |
| F5 | STM32F4 **StdPeriph（SPL）** | V1.8.0（官方未随 GitHub 分发，取自板卡资料盘） | [S11](../stm32/11-i2c.md)、[S15](../stm32/15-spl-anatomy.md) |
| F6 | GigaDevice **GD32F4xx Firmware Library** | V3.3.3 `@ 10d02f4` | G 篇 RCU/FMC 逐字段对照 |
| F7 | GigaDevice **GD32VF103 Firmware Library** | `@ 7ab0521` | V 篇 |
| F8 | [RT-Thread/rt-thread](https://github.com/RT-Thread/rt-thread) | **未固定**：CI 稀疏检出 `master`（`src`、`include`、`libcpu/arm/cortex-m4`） | R 篇行号可能随上游漂移——这是本站已知的可复现性缺口，固定到某个 tag 是待办 |

## 记忆锚点

::: tip 一句话记住
**版本号是结论的一部分。** 寄存器位看 Rev、行号看 tag、API 看文档版本；三样对不上，先怀疑口径，再怀疑教程，最后才怀疑芯片。
:::

## 常见坑

- **拿错代的手册**：RM0090 管 F405/407/415/417/427/437/429/439；F103 是 RM0008，F7 是 RM0385。位定义能对上才怪。
- **IDF 文档读成 latest**：网页默认跳最新版，本站基准 v5.5.2；URL 里带 `v5.5` 才是同一本书。
- **论文只读摘要**：D1 的 69.3% 是 n→∞ 的下界、D2 的继承协议不防死锁（天花板协议才防）、D7 的结论是"别信 volatile 一个人"——这三条都在正文而不在摘要里。
- **把 ganssle.com 这类工程随笔当规范引**：它们是经验，不是标准；本页标在 D 区是因为被频繁引用，不是因为它有审稿。

## 你做到了

- 读到章节里的 `[D2]` 能翻到原文，知道它哪一版、从哪下载；
- 知道本站哪些口径是**核过版本**的、哪些**未核**，不把后者当权威转述。

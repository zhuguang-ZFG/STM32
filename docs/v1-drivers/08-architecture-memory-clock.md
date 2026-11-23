---
title: "架构、存储器地图与时钟树"
platforms: [f407, f103, gd32]
---

# 架构、存储器地图与时钟树

> 外设寄存器写进去没反应时，先检查时钟；地址算错一个段，写进去的就不是目标外设。把存储器映射、总线、位带与时钟树连起来，后面各章的“先开时钟、再写寄存器”才有依据。

## 本章罗盘

- **问题**：为什么 GPIOA 的地址是 `0x4002_0000`，而不是别的数？一次取指、一次外设寄存器读、一次 DMA 搬运，在总线矩阵上各走哪条线，为什么 CCM 那条路走不通？位带为什么能把一个位变成一个字的原子写？HSI、HSE、LSI、LSE 四个时钟源各管什么？8MHz 晶振怎样手算出 M/N/P/Q 并落到 168MHz？提频六步为什么必须按这个顺序执行？F103 的 8MHz 到 72MHz 又为什么是另一套乘法？
- **交付**：能从段基址推出任意外设地址并说出它挂在哪条总线；能用公式算出任意位的位带别名；能为一颗晶振手算一组合法 M/N/P/Q，并用回读与 MCO 两条证据对账；能按六步顺序配置 F407 时钟并说出每步失败的样子；能读 F103 的 `RCC_CFGR` 复算 72MHz、36MHz 与定时器时钟。
- **级别**：L0 起步。证据位置：「测量与证据」与「离开检查」；读完留下地址推导、位带换算与 M/N/P/Q 回读对账的记录。
- **旅程导航**：上一章（[第 7 章](../v0-foundations/07-build-systems-legacy.md)）你手里有 `GPIO_Init` 的逐行位操作对账和一份 CMake 生成日志；本章结束多了从段基址推出外设地址、位带别名换算与 M/N/P/Q 回读对账的记录（宿主机 probe 实跑断言与反汇编；HSE 晶振值与 MCO 引脚读数来源未记录，标未跑）——L0 的「跑通」升到「为什么这样配能查到手册」：段基址与总线矩阵、位带别名、四个时钟源与 8MHz→168MHz 的手算、提频六步的顺序，这些是地址推导与对账判据不是已量引脚频率。
- **开源读法**：对照 `libopencm3` 的 `include/libopencm3/stm32/f4/memorymap.h`，看手册里的段基址怎样被写成宏；寄存器语义仍回 RM0090。
- **边界**：三平台章。F407 的地址、寄存器位、探针读数来自 S1、S2 与 RM0090 Rev 18；F103 的 72MHz 配置来自根书第 02 章与 RM0008 Rev 21；GD32 只在“跨平台边界”里指路，不写未经来源支持的差异。DMA 通道与数据搬运留给[第 14 章](./14-dma.md)，GPIO 寄存器逐位拆解留给[第 9 章](./09-gpio.md)，定时器与 PWM 留给[第 12 章](./12-timers-pwm.md)，UART 波特率留给[第 13 章](./13-uart-framed-protocol.md)，HardFault 现场留给[第 19 章](../v2-reliability/19-watchdog-reset-hardfault.md)，低功耗与时钟门控留给[第 18 章](../v2-reliability/18-low-power.md)，SWD 与性能测量留给[第 20 章](../v2-reliability/20-debug-performance.md)。来源没有记录作者上板复跑 HSE 与 MCO，这里把板上读数标为未跑。
- **依据锚点**：S1《F407 架构总览：地址背后的故事》（`mcu/docs/stm32/01-arch.md`）、S2《RCC 时钟树：168MHz 是怎么算出来的》（`mcu/docs/stm32/02-rcc-clock.md`）；根书第 02 章《芯片选型与存储器时钟》的时钟树、Flash 等待与 CSS/MCO 段（`docs/02-芯片选型与存储器时钟.md` 第 6、7、10 节）；[第 6 章](../v0-foundations/06-linker-startup-map.md)的 CCM 与启动映射、[第 1 章](../v0-foundations/01-c-memory-model.md)的统一编址。RM0090、RM0008、PM0214 与 DS8626 的条文均转引自上述来源。

## 先做出来

先确认能读懂[第 3 章](../v0-foundations/03-struct-abi-registers.md)的寄存器映射与[第 6 章](../v0-foundations/06-linker-startup-map.md)的启动/链接边界，再做地址推导与时钟复算。板上读地址属于后续取证，本轮没有执行。

GDB 连上 F407，依次读三个地址：

```console
(gdb) x/wx 0x40020000
(gdb) x/wx 0x40021400
(gdb) x/wx 0xE000ED00
```

三个地址分别是 GPIOA 的 `MODER`、GPIOF 的 `MODER` 与内核的 `CPUID`。读之前先做个判断：三个地址里，哪一个不在外设区？判断完再往下读。

没有板子也能把时钟计算跑完。进来源工程 `mcu/code/stm32/01-rcc-clock`：

```bash
cd mcu/code/stm32/01-rcc-clock
sh probe.sh
```

来源记录里，这个脚本做三步：宿主跑固件自己的函数、错宏对照、交叉链 `-O2` 反汇编对账。第 1 步把 `RCC_PLLCFGR`/`RCC_CFGR` 两个宏改指一对假寄存器后 `#include "main.c"`，所以断言跑的是固件本体，不是另抄一遍算术。

8、25、16、12、6、4MHz 六种晶振的 M/N/P/Q、`0x07405408` 的位段结构、Flash 等待周期十个边界、时钟树回读解出的 `{168e6, 168e6, 42e6, 84e6, 84e6}`，几十条断言全绿。有板再加一步：构建默认版本（留在 HSI 16MHz，不碰晶振）后读 `g_clock_tree[]`，来源记录是五行 `16000000`。芯片复位后默认运行内部时钟，PLL 还没有启用。

## 机制

### 4GB 存储器映射：先分区，再定位外设

Cortex-M4 是 32 位机，地址空间正好 4GB。ARM 把这 4GB 按 512MB 一段切成固定八段，芯片厂商只能在自己的段里再划小房间：

| 区段 | 地址范围 | 放什么 |
| --- | --- | --- |
| Code | `0x0000_0000`–`0x1FFF_FFFF` | Flash 与其别名、系统存储区 |
| SRAM | `0x2000_0000`–`0x3FFF_FFFF` | 片上 SRAM |
| Peripheral | `0x4000_0000`–`0x5FFF_FFFF` | 全部外设寄存器 |
| RAM | `0x6000_0000`–`0x7FFF_FFFF` | 外部 RAM（经 FSMC/FMC） |
| Device | `0x8000_0000`–`0x9FFF_FFFF` | 外部设备 |
| 保留 | `0xA000_0000`–`0xDFFF_FFFF` | — |
| PPB | `0xE000_0000`–`0xFFFF_FFFF` | 内核私有外设（NVIC/SysTick/SCB） |

保留段跨两个 512MB 区块，表里并成一行。F407 在这张图上的落位（RM0090 §2.3 表 1）：

- `0x0800_0000`：主 Flash 1MB。同一块 Flash 在 `0x0000_0000` 还有个别名，上电从哪取指由 BOOT 引脚决定。
- `0x1FFF_0000`：系统存储区，出厂固化的 bootloader 住这。
- `0x2000_0000`：SRAM1 112KB 紧接 SRAM2 16KB，共 128KB 连续。
- `0x1000_0000`：CCM RAM 64KB，只挂在 CPU 的数据总线上，DMA 够不着。
- `0x4000_0000` 起：外设；`0xE000_0000` 起：PPB，`CPUID` 就在 `0xE000_ED00`。

“192KB RAM”的数字就是这么来的：128KB 通用 SRAM 加 64KB CCM。但这两块地的可达性不同：前 128KB 挂在总线矩阵上，DMA 能进出；CCM 只有 CPU 一条路，DMA 缓冲区不能放进 CCM；不能只等完成通知而不检查地址与错误状态。

![Cortex-M 的 4GB 存储器地图：Code、SRAM、外设、外部 RAM/设备、保留与 PPB；F407 的 Flash、SRAM、CCM 与 CPUID 落位](/arch/cortex-m-4gb-map.png)

### 总线矩阵：三个端口与五条访问路线

内核不只有一根总线。Cortex-M4 有三个出口：**I-Code** 取指令、**D-Code** 取数据/常量，两者只覆盖 Code 区；**System** 管其余一切，包括外设、SRAM 与 PPB。F407 把这三个口和 DMA1、DMA2、以太网 MAC、USB HS 一起接到一张多层 AHB 总线矩阵上，再连向 Flash 接口、SRAM、AHB1/AHB2 外设与 FSMC。

![Cortex-M4 内核的 I-Code、D-Code、System 三个总线出口与 FPU/MPU/NVIC](/figures/stm32-01-m4-core.svg)

把一次典型运行拆成五条访问路线，矩阵的作用就具体了：

| 访问 | 主设备 | 路线 | 结果 |
| --- | --- | --- | --- |
| 取指 | CPU I-Code | I-Code → Flash 接口 | 168MHz 下 5 个等待周期，靠 ART 加速器与预取缓冲填坑 |
| 取常量 | CPU D-Code | D-Code → Flash 接口 | 常量与指令同在 Code 区，走另一条口，不与取指抢同一条 |
| 读 `USART1->SR` | CPU System | System → AHB → APB2 桥 | 要穿过两个时钟域，桥里还有同步 |
| 搬 SRAM 缓冲 | DMA | DMA → 矩阵 → SRAM | 不占指令周期，但要跟 CPU 抢同一块 SRAM |
| 访问 CCM | DMA | 无路 | CCM 只接 CPU，DMA 看不到这段地址，该地址不能作为 DMA 缓冲区 |

关键在“同时”两个字：这张矩阵是**并发**的。DMA 搬 SRAM 的时候，CPU 还能从 Flash 取指——两件事走不同的线，各走各的。这正是[第 14 章](./14-dma.md)敢说 DMA“不占指令周期”的硬件底气：它不抢 CPU 的取指口，只在某些地方跟 CPU 抢同一块 SRAM。CCM 那条路也要放到这张图里看才明白——它只接 CPU，DMA 根本看不到，所以那块地址永远当不了 DMA 缓冲区。

![总线矩阵动画：CPU 三个端口与 DMA 争用同一条 AHB 矩阵](/anim/bus-matrix.svg)

F407 的总线时钟分三档：

| 总线 | 频率 | 说明 |
| --- | --- | --- |
| AHB1/AHB2（HCLK） | 168MHz | GPIO、DMA、RCC 等 |
| APB1 | 42MHz | HCLK/4，硬件上限 42MHz |
| APB2 | 84MHz | HCLK/2，硬件上限 84MHz |

APB 分频不为 1 时，挂在 APB 上的定时器拿到的是 `APB×2` 的时钟；这条规则的出处与待复核状态在[第 12 章](./12-timers-pwm.md)交代。

### 位带：把一位映射为一个字

位带（PM0214 §2.2.5）给两个区各开了一片“影子地址”：

| 位带区 | 地址范围 | 别名区 |
| --- | --- | --- |
| SRAM | `0x2000_0000`–`0x200F_FFFF` | `0x2200_0000`–`0x23FF_FFFF` |
| 外设 | `0x4000_0000`–`0x400F_FFFF` | `0x4200_0000`–`0x43FF_FFFF` |

换算公式：

```text
别名地址 = 别名区基址 + (字节地址 − 位带区基址) × 32 + 位号 × 4
```

原位带区的一个**位**，在别名区占一个**字**（32 位）；1MB 位带区于是撑出 32MB 别名区。写别名地址等于硬件替你完成“读—改—写”，一条 `str` 原子改一位。

实例：`GPIOF->ODR` 的字节地址是 `0x4002_1414`，它的 bit6 别名是

```text
0x4200_0000 + (0x4002_1414 − 0x4000_0000) × 32 + 6 × 4 = 0x4242_8298
```

来源工程 `probe.sh` 里三条 `_Static_assert` 固定了 `ODR` 地址、PF6 别名 `0x42428298`、别名区跨度，算错一个数就编不过。同一份 `-O2` 反汇编还并排摆出两种写法的差别：`GPIOF->ODR |= 1u<<6` 编成 `ldr / orr.w / str` 三条，读与写之间开着窗口；写别名只剩 `movs #1` 加 `str.w`，`BSRR` 同样只需一条 `str`。

![位带别名动画：GPIOF ODR 的 bit6 映射到别名区的一个字](/anim/bitband-alias.svg)

位带有两条硬边界：它只覆盖两个位带区的前 1MB，区外的地址没有别名；一次只能改一位，多比特字段回 `BSRR` 或读改写掩码。

### 外设地址：基址是推出来的

外设地址不是背出来的，是从段基址推出来的。以 RM0090 存储器映射表为底：

| 总线 | 段基址 | 外设示例 |
| --- | --- | --- |
| AHB1 | `0x4002_0000` | GPIOA `0x4002_0000`、每口隔 `0x400`（GPIOF `0x4002_1400`）、RCC `0x4002_3800`、DMA1 `0x4002_6000`、DMA2 `0x4002_6400` |
| APB1 | `0x4000_0000` | USART2 `0x4000_4400`、USART3 `0x4000_4800`、UART4 `0x4000_4C00`、UART5 `0x4000_5000` |
| APB2 | `0x4001_0000` | USART1 `0x4001_1000`、USART6 `0x4001_1400`、SPI1 `0x4001_3000` |

记住归属比记住地址更重要：USART1 在 APB2（上限 84MHz）、USART2 在 APB1（上限 42MHz），波特率算错的头号原因就是把总线段记反了。拿到任意外设名，先问它在哪条总线、那段基址是多少，再谈寄存器偏移。

### 四个时钟源：复位从哪来，什么时候换

F407 有四个时钟源：

| 源 | 精度 | 何时用 |
| --- | --- | --- |
| HSI（内部 RC，16MHz） | ±1% 量级 | 复位默认、调试用、没有晶振时的后备 |
| HSE（外部晶振，4~26MHz） | 取决于晶振 | 精度预算需要时选用；不是所有 UART/定时任务的必选项 |
| LSI（内部低速 RC，约 32kHz） | 差 | 独立看门狗 |
| LSE（外部 32.768kHz 晶振） | 好 | RTC |

复位之后芯片只用 HSI 16MHz。这意味着两件事：什么都不配也能跑；**只要想用更高的频率，就得亲手走一遍提频流程**。F103 的复位时钟是 HSI 8MHz，数字不同，规矩一样：上电默认不是 Cube 配置页上的 72MHz。

![RCC 时钟树动画：HSE/HSI、PLL、SW 总闸与 AHB/APB 输电线](/anim/rcc-clock-tree.svg)

### PLL 手算：M/N/P/Q 一个都不能猜

F407 的 PLL 公式（RM0090 Rev 18 §7.2.3）：

```text
f(VCO)    = f(PLL 输入) × PLLN / PLLM
f(SYSCLK) = f(VCO) / PLLP
f(48MHz)  = f(VCO) / PLLQ
```

约束同在这节：PLLM 取 2~63，且必须让 VCO 输入落在 1~2MHz（原文推荐 2MHz 以限制抖动）；PLLN 取 50~432，且 VCO 输出必须在 100~432MHz；PLLP 可取 /2、/4、/6、/8；PLLQ 取 2~15，且 USB OTG FS 要正好 48MHz。

| 晶振 | M | N | P | Q | VCO 输入 | VCO | SYSCLK | USB |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 8MHz | 8 | 336 | 2 | 7 | 1MHz | 336MHz | 168MHz | 48MHz |
| 8MHz | 4 | 168 | 2 | 7 | 2MHz | 336MHz | 168MHz | 48MHz |
| 25MHz | 25 | 336 | 2 | 7 | 1MHz | 336MHz | 168MHz | 48MHz |

M 的职责就是把晶振归一化到 1MHz 或 2MHz，不是越大越好。教程里常见的 M=8/N=336 只是最常抄的解；RM0090 推荐 2MHz 输入，第二组更干净，SYSCLK 与 USB 结果不变。25MHz 板子改的是 M，N/P/Q 不动。

这组参数打包进 `RCC_PLLCFGR` 是 `0x07405408`：`M[5:0]=8`、`N[14:6]=336`、`P[17:16]=00`（/2）、`SRC[22]=1`（HSE）、`Q[27:24]=7`。来源探针把源码算出的这个字与 `-O2` 字面量池里的 `.word 0x07405408` 对了同字。探针还展示了参数助手的拒绝分支：11.0592MHz 不满足这个助手归一化到整 1MHz 的策略，返回 `−2`；64MHz 让该策略的 M 溢出 6 位，返回 `−1`。这不是“所有被拒绝的频率都不是合法 HSE”的硬件结论。PLLP 的四种硬件取值也不等于该助手已覆盖全部配置，官方 `stm32f4xx_hal_rcc.h` 的 `RCC_PLLP_DIV2/4/6/8` 可用于对照。

### 提频六步：六步的顺序

以下只讨论冷复位 HSI 16MHz、VDD=2.7–3.6V，升到 F407 的 168MHz；运行中重配正在使用的 PLL 还需先切安全时钟源。升频前要同时准备 Flash 与总线，不能只检查最终频率。

1. **电压档**：先使能并读回 PWR 时钟门，再配 `PWR_CR.VOS = 1`（bit14，Scale 1，解锁 168MHz）。F405/407 没有 VOSRDY 就绪位，写入即生效，不存在可等待的硬件回执。
2. **Flash 等待周期**：`FLASH_ACR.LATENCY = 5WS`（[2:0]），并开预取 `PRFTEN`（bit8）。这一步必须在提速之前，否则 CPU 去 Flash 取指会超时跑飞。
3. **开 HSE 并等就绪**：`RCC_CR.HSEON = 1`（bit16），轮询 `HSERDY`（bit17）。晶振虚焊或负载电容不对时 HSERDY 不会置位，**必须带超时回退 HSI**，不能无限等待。
4. **配 PLL 并启动**：`RCC_PLLCFGR` 写 M/N/P/Q/SRC（M[5:0]、N[14:6]、P[17:16]、SRC[22]、Q[27:24]），然后 `RCC_CR.PLLON = 1`（bit24），轮询 `PLLRDY`（bit25）。
5. **先配安全总线分频**：仍在 HSI 时写 `RCC_CFGR.HPRE/PPRE1/PPRE2`：AHB=/1、APB1=/4、APB2=/2，按手册要求等待生效，保证切到 168MHz 的瞬间也不超过 APB1 42MHz、APB2 84MHz。
6. **再切 SYSCLK 并确认**：`RCC_CFGR.SW = 10b`（[1:0]），轮询 `SWS`（[3:2]）确认已切换并设超时失败分支；最终复算 HCLK/PCLK，不能用“SW 已写”代替切换完成。

![提频节点示意；旧图的末两项不可直接当执行顺序，必须先配安全分频、再切 SYSCLK](/anim/rcc-six-gates.svg)

RM0090 对 HPRE 还有一条容易忽略的 caution：“分频值在写入 HPRE 后的 1~16 个 AHB 周期内才生效”。因此**升频前先增大必要的分频比、降低 APB 时钟，再切高频源**；降频时也要先降实际时钟，再按新频率减少 Flash 等待。官方 `stm32f4xx_hal_rcc.c` 的 `HAL_RCC_ClockConfig()` 在切源前先把待配置 APB 分频设为 /16 保护，最后才落目标分频。图中节点的位置不能代替这条执行条件。

![手绘板：提频六步——VOS=1、5WS 先行，HSEON 等 HSERDY 带超时回退，PLLCFGR=0x07405408，SW 切换后读 SWS 确认，HPRE/PPRE 落分频；HPRE 写入后 1~16 周期生效，升频前先降分频（原理示意，非实拍）](/images/ch08-six-frequency-steps.png)

![手绘板：8MHz 晶振或 HSI 16MHz 经 PLL 与 AHB/APB 分频，落到 GPIOA 的寄存器地址（原理示意，非实拍）](/images/ch08-clock-tree-path.png)

### 总线分频与定时器 ×2

AHB 上挂着 CPU、内存、DMA、GPIO；APB1/APB2 上挂着外设，所以总线分频决定每个外设能拿到多快的时钟。还有一条不在框图里、但在寄存器说明里的规则：**当 APBx 预分频不等于 1 时，挂在这条 APB 上的定时器时钟等于 PCLK×2**。在 168MHz、APB1=/4 的配置下，PCLK1 是 42MHz，而 TIM2 的时钟是 84MHz。只记 42MHz 会把所有定时器算慢一半；这条规则的出处与待复核状态由[第 12 章](./12-timers-pwm.md)交代。

### Flash 等待周期与电压档

等待周期按 VDD 电压范围分列（RM0090 Rev 18 Table 10，单位 MHz）：

| VDD | 0WS | 1WS | 2WS | 3WS | 4WS | 5WS | 6WS | 7WS |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2.7~3.6V | ≤30 | ≤60 | ≤90 | ≤120 | ≤150 | ≤168 | — | — |
| 2.4~2.7V | ≤24 | ≤48 | ≤72 | ≤96 | ≤120 | ≤144 | ≤168 | — |
| 2.1~2.4V | ≤22 | ≤44 | ≤66 | ≤88 | ≤110 | ≤132 | ≤154 | ≤168 |
| 1.8~2.1V（预取关） | ≤20 | ≤40 | ≤60 | ≤80 | ≤100 | ≤120 | ≤140 | ≤160 |

VOS 不在这张表里，它只决定频率上限：F405/407 在 VOS=0 时 fHCLK 上限 144MHz，VOS=1 时才允许 168MHz。所以“能不能跑 168MHz”是两步检查：先过电压档，再过等待周期；3.3V 供电下 168MHz 要 5WS。

### 回读与 MCO：把内部时钟引出来

程序以为的时钟必须与引脚上的时钟对账。`clock_tree_readback()` 从 `CFGR` 反推真实时钟树，来源探针喂 `SWS=PLL, PPRE1=0b101, PPRE2=0b100`，读出 `{168000000, 168000000, 42000000, 84000000, 84000000}`，并带上“APB 分频不等于 1 时定时器 ×2”这条隐藏规则。

MCO1 可把选定时钟送到 PA8，必须同时配置 `MODER8=10`、AF0、`RCC_CFGR.MCO1` 的源选择及 `MCO1PRE`（[26:24]）的分频。MCO1 可选 HSI/LSE/HSE/PLL，并不直接选择 SYSCLK；只有 SYSCLK 确认来自同一 PLL、MCO1 也选 PLL 且 /4 时，理论上才是 168/4=42MHz，测得频率乘 4 才能与 SYSCLK 对账。编码是 `0xx=不分频、100=/2、101=/3、110=/4、111=/5`，不是“分频比减一”。按减一写 /4 会落到“不分频”区，分频逻辑选的是PLL/1，即理论源168MHz；这不保证PA8能在具体负载下合规输出168MHz，仍须核引脚电气上限。再误按/4乘回去会推得672MHz，这是错误换算值，不是引脚可测目标。

`01-rcc-clock/main.c` 已把PA8配为AF0推挽/高速档，并按SWS显式选择同一HSI/HSE/PLL源和MCO1分频；默认名义HSI16MHz为/1，PLL168MHz为/4、理论42MHz。冷复位升频路径先开PWR并配Flash等待/回读，再等HSE/PLL，先设安全APB分频才请求切源；等待失败有界返回并读回实际时钟，不凭失败状态宣称已经回退。生产C函数宿主回归与现有工程纯编译已验证这些代码路径，晶振值、起振、真实频率、过渡过程及引脚电气仍未实测。

### 根书 F103：8MHz 到 72MHz 的配置

换到 F103C8T6，时钟树是另一套乘法。HSE 8MHz 从第 5 脚 PD0 与第 6 脚 PD1 进来，`PLLXTPRE=0`（HSE 不预分频）、`PLLSRC=1`（PLL 入口是 HSE）、`PLLMUL=0111`（×9），于是 `8 × 9 = 72` MHz；`SW=10` 时 SYSCLK 用 PLL。F1 没有 PLLM/PLLN/PLLP，结构是 HSE 或 HSI/2 再乘 N，这一点与 F4 的 M/N/P/Q 不能混用。

| 时钟 | 来源 | 分频 | 频率 | 上限 |
| --- | --- | --- | --- | --- |
| SYSCLK | PLL | — | 72MHz | 72MHz |
| AHB（HCLK） | SYSCLK | ÷1 | 72MHz | 72MHz |
| APB1（PCLK1） | AHB | ÷2 | 36MHz | 36MHz |
| APB2（PCLK2） | AHB | ÷1 | 72MHz | 72MHz |
| ADC | APB2 ÷6 | — | 12MHz | 14MHz |
| USB | PLL ÷1.5 | — | 48MHz | 48MHz |

`PPRE1=100`（÷2）时 PCLK1=36MHz；APB 预分频不是 1，挂在那条总线上的定时器时钟再 ×2，所以 TIM2~TIM7 仍是 72MHz；TIM1 在 APB2，预分频为 1，不再 ×2。`USBPRE=0` 时 72MHz 的 PLL 再 ÷1.5 得到 48MHz；`ADCPRE=10` 是 PCLK2÷6，得到 12MHz，而 `ADCPRE=01` 的 ÷4 得到 18MHz，越过 RM0008 的 14MHz 上限。

Flash 等待同样按 2.7~3.6V 供电给出：0~24MHz 用 0，24~48MHz 用 1，48~72MHz 用 2（`FLASH_ACR.LATENCY=010`）。只把 PLL 改成 ×9、LATENCY 还留在 0，CPU 会读到错的指令，程序跑飞或进 HardFault。

`RCC_CFGR` 的关键位（RM0008 Rev 21 中密度第 7.3.2 节）：

| 位域 | 名称 | 说明 |
| --- | --- | --- |
| [1:0] | SW | 系统时钟源：00=HSI，01=HSE，10=PLL |
| [3:2] | SWS | 当前系统时钟源（只读） |
| [7:4] | HPRE | AHB 分频 |
| [10:8] | PPRE1 | APB1 分频 |
| [13:11] | PPRE2 | APB2 分频 |
| [21:18] | PLLMUL | PLL 倍频（×2~×16） |
| [16] | PLLSRC | PLL 输入源：0=HSI/2，1=HSE |
| [17] | PLLXTPRE | HSE 预分频 |

两条 F103 专属的失败分支要单独记。第一，HSE 停振且 CSS 已开时，若 HSE 直接或经 PLL 当系统时钟，硬件改用 HSI 并关掉 HSE；若 HSE 是 PLL 入口，PLL 也关掉。CSS 中断接在 NMI 上，NMI 里要写 `RCC_CIR` 的 CSSC，否则 NMI 会一直进来。第二，MCO 在 PA8（第 29 脚）：`MCO=111` 送 PLL÷2 的 36MHz，低于手册写的 50MHz I/O 上限；`MCO=100` 把 72MHz 的 SYSCLK 直接送出去，超过这个上限，示波器上量到的幅度和频率都不能当读数。

网上不少资料混用了第 8.3.2 节（互联型）的内容：`OTGFSPRE` 位、`PLLMUL` 的 `000x` 保留编码、×6.5 倍频，这些在 STM32F103C8T6 上都不存在，照抄过来会配错。C8 的 `RCC_CFGR` 看第 7.3.2 节，`0111` 仍是 ×9，`0000` 是 ×2。

## 测量与证据

读数分两类：来源工程在宿主机上实跑的断言与反汇编，以及来源没有记录上板读数的引脚测量。

| 取证项 | 来源命令或位置 | 来源记录里的读数 |
| --- | --- | --- |
| 三个地址 | GDB `x/wx 0x40020000`、`0x40021400`、`0xE000ED00` | 依次是 GPIOA_MODER、GPIOF_MODER、CPUID；具体读值来源未记录 |
| 六种晶振 | `sh probe.sh` 第 1 步，probe 输出第 1 节 | 8/25/16/12/6/4MHz 全部 M=晶振/1MHz、N=336、P=/2、Q=7，SYSCLK 168000000、USB 48000000 |
| 参数助手拒绝用例 | 同上 | 11.0592MHz 返回 `−2`；64MHz 返回 `−1`（M 溢出 6 位） |
| 位段打包 | probe 输出第 2 节 | `M=8 N=336 P=/2 SRC=HSE Q=7 → 0x07405408`，与 `-O2` 字面量池同字 |
| 等待周期边界 | probe 输出第 3 节 | 16→0、30→0、31→1、60→1、61→2、90→2、120→3、150→4、151→5、168→5 WS |
| 时钟树回读 | probe 输出第 4 节 | `{168000000, 168000000, 42000000, 84000000, 84000000}`；PPRE1=/1 时 PCLK1=TIM2CLK=168000000 |
| MCO1 对账 | probe 输出第 5 节，分频算术 | 若已正确选择 PLL 并配置 AF，168MHz /4 理论为 42MHz；pre=011 实为 /1，误乘 4 会推得 672MHz，不是引脚实测值 |
| 错宏对照 | `sh probe.sh` 第 2 步（probe 输出第 6 节） | 写入 `0x07405419`（M=25）；程序以为 168000000，按宏/晶振差异推得 SYSCLK 53760000、USB 15360000（非引脚测量），差 114240000Hz，函数返回 0 |
| PPRE 表长 | probe 输出第 4b 节 | 16 格表让 `/2 /4 /8 /16` 全读成 /1；套上定时器 ×2 后出现 336MHz |
| 提频顺序 | `-O2` 反汇编 | `orr #16384`(VOS) → `bic #7 / orr #5 / orr #256`(LATENCY+预取) → `orr #65536`(HSEON) → `lsls #14 / bpl`(等 HSERDY) → `str [r2,#2052]`(PLLCFGR) → `orr #16777216`(PLLON) → `bic #3 / orr #2`(SW) → `and #12 / cmp #8`(读 SWS) |
| 常量折叠 | 同上 | M/N/P/Q 被压成 `movs r2,#8 / mov.w r3,#336 / movs r2,#2 / movs r3,#7`，一条除法都没有 |
| F103 的 72MHz 数据 | 根书第 02 章 | PLLMUL=0111、PPRE1=100；HCLK 72、PCLK1 36、PCLK2 72、TIM2~7 72、USB 48、ADC 12 |
| F103 等待周期 | 根书第 02 章 | 0~24MHz 0、24~48MHz 1、48~72MHz 2（2.7~3.6V） |
| 板上 HSE/MCO | 来源标注 | 未实测；HSE 晶振值与 PA8 读数待上板回填 |

这些读数的共同结论只有一条：**源码算出的字、写进寄存器的位、引脚上量到的频率，三样必须能互相对上**。回读只证明“你写的位和你的宏自洽”，不证明晶振为真；MCO 才是把内部时钟拉到引脚上的那一步。反过来，位段字对上了也不代表总线分频对：PPRE 表长错一格，APB1 就会被算成 168MHz。

```bash
cd mcu/code/stm32/01-rcc-clock
sh probe.sh          # 宿主机跑断言 + 交叉链 -O2 反汇编对账
```

<QuizBank chapter="s02-rcc-clock" />

## 失败分支

| 现象 | 原因 | 区分证据 | 下一动作 |
| --- | --- | --- | --- |
| 外设寄存器写进去读回 0 | 该外设时钟没开 | 读回值与写入值无关；使能时钟后恢复 | 先开 `RCC` 门控，再初始化；见[第 9 章](./09-gpio.md) |
| 串口波特率差一倍 | 把 APB1 的 USART2 当成 APB2 的 84MHz | 地址落在 `0x4000_xxxx` 而不是 `0x4001_xxxx` | 按总线归属重算 PCLK，再算 BRR |
| HSE 起振失败，程序卡死 | 轮询 `HSERDY` 没有超时 | `RCC_CR` bit17 永远不置位 | 加超时回退 HSI，并把状态标志置位 |
| 切 168MHz 后 HardFault 或取指错 | Flash 等待周期没加够 | `FLASH_ACR.LATENCY` 仍是 0 | 先写 LATENCY=5WS 与预取，再切 SYSCLK |
| 写完 SW 没换钟 | 没等 `SWS` 回执 | `SWS` 仍是旧源 | 轮询 SWS 并加超时；读不到回执按失败处理 |
| 调完分频立刻读到旧频率 | `HPRE` 有 1~16 个 AHB 周期的生效窗口 | 读回分频与刚写的不一致 | 升频前先把总线分频降下来，等生效再继续 |
| DMA 缓冲区数据莫名丢失 | 缓冲区放进了 CCM | 地址在 `0x1000_xxxx`；DMA 无路可达 | 搬到 `0x2000_0000` 的通用 SRAM |
| 想用位带改两位字段，结果只动了一位 | 位带一次只映射一位 | 别名地址只对应一个位号 | 多比特字段回 `BSRR` 或读改写掩码 |
| 程序以为 168MHz，引脚只有 53.76MHz | `HSE_VALUE_HZ` 宏与板上晶振不符 | `PLLCFGR=0x07405419`；`pll_params_from_hse()` 返回 0 | 用 MCO1 实测对账，改回真实晶振值 |
| MCO1 分频或换算与预期不符 | 按“分频比减一”写了 `MCO1PRE` | `pre=0b011` 落在不分频区 | 按 `0xx/100/101/110/111` 编码表写 |
| 回读出现 336MHz 这种给不出的频率 | PPRE 用了 16 格表，3 位索引只到 7 | `/2 /4 /8 /16` 全读成 /1 | 表长按字段位宽开，用 `{1,1,1,1,2,4,8,16}` 八格 |
| GDB 读某个地址直接 HardFault | 访问了未实现的地址段 | 读操作本身触发异常 | 先对 RM0090 存储器映射表，确认地址对应已实现的外设或存储区 |
| F103 的 ADC 时钟 18MHz，超过 14MHz 上限 | `ADCPRE=01` 选了 ÷4 | 读 `RCC_CFGR.ADCPRE` | 改回 `ADCPRE=10` 的 ÷6，得到 12MHz |
| F103 的 MCO 波形不可信 | 把 72MHz SYSCLK 直接送 PA8 | 超过手册 50MHz I/O 上限 | 改送 PLL÷2 的 36MHz，再乘回去 |
| F103 的 NMI 反复进入 | CSS 触发后没写 `RCC_CIR.CSSC` | NMI 持续挂起 | 在 NMI 里清 CSSC，再处理停振 |
| F103 按第 8.3.2 节填 `PLLMUL` | 那是互联型手册章节 | 出现 `OTGFSPRE`、×6.5 等 C8 上不存在的编码 | 改看第 7.3.2 节，`0111` 是 ×9 |

## 跨平台边界

F407 与 F405 共享这套 RCC 位定义与 VOS 上限，但 F405/407 没有 VOSRDY 就绪位，这是与 F42x/43x 的分界；换到别的 STM32 系列，寄存器名、PLL 结构与 Flash 等待表都要重查，不能把 `0x07405408` 或 5WS 直接搬过去。

F103 一侧，4GB 地图与统一编址同样成立，但时钟树是“HSE 或 HSI/2 再乘 N”的结构：没有 PLLM/PLLN/PLLP，PLLMUL 只有 ×2~×16，SYSCLK 上限 72MHz；APB1 上限 36MHz、APB2 上限 72MHz；Flash 等待按 0/1/2 三档；MCO 可用 PLL÷2 送出 36MHz；CSS 走 NMI，要写 CSSC。F103 的外设基址也与 F407 不同（例如 GPIOA 在 `0x4001_0800`、RCC 在 `0x4002_1000`），地址不能跨系列照抄。F1 的 `RCC_CFGR` 还要认准中密度第 7.3.2 节，互联型第 8.3.2 节的编码不适用。

GD32 只划边界。来源在延伸里留的指针是“GD32 的 RCU 与 RCC 对照”，这里不展开它的时钟源、PLL 字段与寄存器布局，也不把 F407 的位段名当成 GD32 的名字。芯片迁移的方法论与引脚/外设差异见[第 28 章](../v4-platforms/28-chip-migration-differences.md)，GD32 系列（ARM 与 RISC-V）的对照见[第 29 章](../v4-platforms/29-gd32-arm-riscv.md)。ESP32 不在平台范围内，其架构与启动见[第 30 章](../v4-platforms/30-esp32s3-architecture-boot.md)。

## 社区开源实现

本章的坑（时钟没开、切换次序、HSERDY 死等、基址判错总线）在开源代码里都有现成的对照位置：

| 仓库 | 文件 | 看什么 |
| --- | --- | --- |
| [libopencm3/libopencm3](https://github.com/libopencm3/libopencm3) | `include/libopencm3/stm32/f4/memorymap.h` | `PERIPH_BASE` 与 APB1/APB2/AHB1 分层基址宏（`memorymap.h:29-32`）：本章「从段基址推外设地址」的落地形态——手册的表被一行行写回宏，地址推导可以逐条对着核 |
| [STMicroelectronics/stm32f4xx-hal-driver](https://github.com/STMicroelectronics/stm32f4xx-hal-driver) | `Src/stm32f4xx_hal_rcc.c` | `HAL_RCC_ClockConfig`（`stm32f4xx_hal_rcc.c:591`）**先**升 Flash 等待并读回校验（`:608-:617`）**再**切 SYSCLK——「切 168MHz 后 HardFault」分支的官方次序；`HAL_RCC_OscConfig`（`:219`）轮询 HSERDY 带 `HAL_GetTick` 超时（`:259/:273`）——「起振卡死」的库侧答案是有超时，回退 HSI 仍要你自己写 |
| [STMicroelectronics/cmsis-device-f4](https://github.com/STMicroelectronics/cmsis-device-f4) | `Include/stm32f407xx.h` | 各外设基址宏：USART2 落在 APB1 段、USART1 落在 APB2 段——「波特率差一倍」那条分支，先在这里核对基址归属再算 PCLK |

共性归纳：时钟树的「先等待、再切换、后读回」次序在 HAL 里是显式代码（读回校验失败直接 `HAL_ERROR`），而 libopencm3 的 `rcc_wait_for_osc_ready`（`lib/stm32/f4/rcc.c:535`）对就绪位与 SWS 就是裸 `while`——本章「轮询 HSERDY 没有超时，程序卡死」那条分支，是开源代码里现成的实例：HAL 的超时返回 `HAL_TIMEOUT`，卡死还是成功回退 HSI，永远是调用者的纪律。外设基址宏在 libopencm3 与 cmsis-device 两套头文件里值相同而写法不同，判定「这颗外设挂在哪条总线」永远回到基址段位，而不是猜 84 还是 72。

## 离开检查

1. `0x4002_0000` 为什么是 GPIOA？F407 的 192KB RAM 怎么分？CCM 为什么不能给 DMA 用？
2. 总线矩阵上的五条访问路线各是什么？为什么 DMA 搬 SRAM 不占指令周期？CCM 那条为什么走不通？
3. 位带别名公式是什么？`GPIOF->ODR` 的 bit6 别名是多少？为什么 1MB 位带区要撑出 32MB 别名区？什么时候不能用位带？
4. HSI、HSE、LSI、LSE 各管什么？F407 与 F103 复位后各跑哪个时钟、多少 MHz？
5. 8MHz 晶振给出两组合法 M/N/P/Q，并说明哪一组更干净；25MHz 晶振改哪个参数？`0x07405408` 里各字段是什么？
6. 冷复位 HSI 16MHz、VDD=3.3V，要升到 SYSCLK=168MHz、AHB=/1、APB1=/4、APB2=/2：若先切源而 APB 仍为 /1，中间两条 APB 各是多少、是否超限？写出安全顺序与应保留的寄存器/失败状态；只做纸面审查，不运行当前 PLL 路径。
7. Flash 等待周期与 VOS 各管什么？3.3V 下 168MHz 要几个等待周期？F103 的 72MHz 呢？
8. F103 从 8MHz 到 72MHz 怎么算？PCLK1、TIM2、USB、ADC 各是多少？

<details>
<summary>对照答案</summary>

1. AHB1 段基址是 `0x4002_0000`，GPIOA 占第一格，于是它的地址就是 `0x4002_0000`；GPIO 每端口隔 `0x400`，GPIOF 是 `0x4002_1400`。192KB 是 SRAM1 112KB 加 SRAM2 16KB 的 128KB 连续区，再加 64KB CCM。CCM 只挂在 CPU 数据总线上，不在 AHB 矩阵上，DMA 看不到这段地址，放进去的缓冲区会静默丢数据。
2. 取指走 I-Code 到 Flash 接口；取常量走 D-Code 到 Flash；读 `USART1->SR` 走 System → AHB → APB2 桥；DMA 搬 SRAM 走矩阵的第二主机路径；DMA 访问 CCM 无路可走。DMA 搬运由矩阵独立完成，不占 CPU 指令周期，但要与 CPU 抢同一块 SRAM。CCM 只接 CPU，DMA 没有到它的总线。
3. `别名 = 别名区基址 + (字节地址 − 位带区基址) × 32 + 位号 × 4`。`0x4200_0000 + (0x4002_1414 − 0x4000_0000) × 32 + 6 × 4 = 0x4242_8298`。一个位在别名区占一个 32 位字，1 位换 32 位，所以 1MB × 32 = 32MB。位带只覆盖两个位带区的前 1MB，且一次只能改一位；多比特字段或区外地址要回 `BSRR` 或掩码操作。
4. HSI 是内部 16MHz RC，是复位后的默认时钟，也是 HSE 失效时的后备；HSE 是 4~26MHz 外部晶振，是否需要由误差预算决定，不能说所有 UART/定时任务都必选；LSI 约 32kHz，给独立看门狗；LSE 是 32.768kHz 晶振，给 RTC。F407 复位后跑 HSI 16MHz；F103 复位后跑 HSI 8MHz，都不是配置页上的高频。
5. VCO 输入 1MHz：M=8、N=336、P=2、Q=7；VCO 输入 2MHz：M=4、N=168、P=2、Q=7。两组都得到 SYSCLK 168MHz、USB 48MHz；RM0090 推荐 2MHz 输入以限制抖动，第二组更干净。25MHz 晶振改 M=25，N/P/Q 不变。`0x07405408` 中 M=8、N=336、P=/2、SRC=HSE、Q=7。
6. 先切到 168MHz 而 PPRE 仍为 /1，会暂时令 PCLK1/PCLK2 都为 168MHz，超过 42/84MHz 上限，即使最终分频正确也不合格。冷复位方案：使能 PWR 并配 VOS、先加 Flash 等待并读回、HSE/PLL 就绪且带超时、在旧低频上先配安全 HPRE/PPRE 并等待生效，最后切 SW、读 SWS 与最终分频。记录 CR/PLLCFGR/CFGR/FLASH_ACR 与失败状态；当前源码的反汇编只能证明它执行了什么，不能证明次序安全。
7. VOS 决定 HCLK 上限：VOS=0 是 144MHz，VOS=1 才是 168MHz；LATENCY 决定 Flash 取指等几拍，按 VDD 分列。3.3V、168MHz 要 5WS；F103 在 2.7~3.6V、72MHz 要 LATENCY=2。
8. HSE 8MHz 经 `PLLXTPRE=0`、`PLLSRC=1`、`PLLMUL=0111` 乘 9 得 72MHz；HPRE=/1 得 HCLK 72MHz；PPRE1=/2 得 PCLK1 36MHz；APB1 分频不为 1，TIM2~TIM7 时钟 ×2 得 72MHz；USBPRE=0 让 PLL ÷1.5 得 48MHz；ADCPRE=10 让 PCLK2 ÷6 得 12MHz。Flash 等待用 2，顺序是先写 LATENCY 再切 SW。

</details>


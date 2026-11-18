---
title: "DMA"
platforms: [f407, f103]
---

# DMA

> 中断方式收 1KB，CPU 要被打断一千次；DMA 只打断一次，代价是把“从哪搬到哪、搬多少、已经搬到哪”全部写进寄存器。下面先拆 F4 的控制器→流→通道路径和 F1 的固定通道，再把 PAR、M0AR、NDTR 三个寄存器与 DIR 的两位方向对齐；循环模式与双缓冲各讲清“保证什么、不保证什么”，最后把 HAL 的 EN 窗口、UART 的 TC 边界和 ADC 的半字传输逐项对齐。两个来源都没有留下上板读数，正文把手册规则、公式推导与预期现象分开写。

## 本章罗盘

- **问题**：F407 上 USART1 的接收请求为什么必须落在 DMA2，F103 上同一个 USART1 却落在 DMA1 通道 5？F4 的“流 × 通道”两级选择与 F1 的“一条通道固定接一组请求”差在哪，CHSEL 到底选了什么？PAR、M0AR、NDTR 各是什么，为什么“三地址一长度”严格讲只有两个地址，NDTR 数的是字节还是数据项，半字缓冲区里 NDTR 读回 3 又表示已经搬了多少？方向与模式这几处最容易混：DIR 为什么占两位、00/01/10 各是什么方向，为什么内存到内存只有 DMA2 能做；循环模式下 NDTR 归零后发生什么，`长度 − NDTR` 为什么不是累计进度；双缓冲换的是哪一块，为什么它也不保证 CPU 来得及？还有时序与寄存器窗口：HT 与 TC 各在什么时候响，处理期限为什么是硬约束，CHSEL/CIRC/MINC 为什么必须在 EN=0 时改，HAL 的 Init 与 Start 各落哪些寄存器？最后把三个边界对上：DMA 的 TC 与 USART 的 TC 差在哪，IDLE 为什么不是帧边界，ADC 的 NDTR 为什么按半字算，F407 的 CCM 为什么 DMA 不能访问，两个来源又留下了哪些读数、哪些只是预期。
- **交付**：能按“控制器→流→通道”写出 F4 的 USART1_RX 落位并说明每一级的选择依据；能在 F103 上把 USART1_TX/RX 落到 DMA1 的固定通道；能手算 NDTR 与字节数的换算并处理环形回绕；能写出循环模式的位置公式与半区消费的丢弃判据；能解释 DBM/CT 与 HT/TC 半区的差别和共同期限；能把 HAL 的 `HAL_DMA_Init`、`HAL_DMA_Start` 对回手写寄存器；能说清 UART 的 DMAT/DMAR、TC 边界和 ADC 的半字宽度；能按台架步骤留下 NDTR 轨迹与缓冲区比对记录。
- **级别**：L2 数据。证据位置：「测量与证据」与「离开检查」；读完留下 NDTR 换算、半区期限与台架轨迹的对账。
- **旅程导航**：上一章（[第 13 章](./13-uart-framed-protocol.md)）你手里有 BRR 复算、一帧位宽与 e02 的解码判据；本章结束多了 NDTR 换算、半区期限与台架轨迹的记录模板（两个来源都没有留下上板读数；`03-uart-dma` 的流/通道取值标着待上板自检）——L2 的「CPU 一字节一字节搬」升到「外设自己搬」：控制器→流→通道与固定通道、PAR/M0AR/NDTR 与两位 DIR、循环与双缓冲各保证什么、CHSEL/CIRC/MINC 必须在 EN=0 时改，这些是寄存器对齐与记录模板不是已量搬运轨迹。
- **开源读法**：对照 `STM32CubeF4` 的 `Drivers/STM32F4xx_HAL_Driver/Src/stm32f4xx_hal_dma.c`，看 `HAL_DMA_Init` 与 `HAL_DMA_Start` 怎样先关 EN、再落流属性与传输参数；寄存器语义仍回 RM0090 §10.3。
- **边界**：两平台章。F407 的 8 流 × 8 通道、SxCR 位号、FIFO、DBM、CCM 与 HAL 行号来自 S8《S8 DMA：让数据自己搬家》与根书第 10 章，并按 RM0090 §10.3.3 的语义复核；F103 的 7 通道、固定请求映射、CCR/CNDTR/CPAR/CMAR 与 C8 只有 DMA1 来自根书第 10 章、RM0008 第 13 章与 DS5319。两个来源都没有留下上板读数：S8 的“GDB 里看 NDTR 倒数”是操作指令与预期，根书第 10 章的“动手实验”是待做清单，`03-uart-dma` 的注释也把流/通道取值标成待上板自检。F4 的 USART1_RX = DMA2 Stream5 Channel4（或 Stream2 Channel4）因来源自注未取得 RM0090 请求表正文，标为待复核；F1 的通道号按 RM0008 表 78 的映射使用。RM0090 的章号在不同修订版里会移动（S8 引 §10.3.3，根书第 10 章写“第 9 章”），这里引小节号 §10.3.3，不引用表号。GD32 与 ESP32 不在平台列表，只在“跨平台边界”里指路。
- **依据锚点**：S8（`mcu/docs/stm32/08-dma.md`）、根书第 10 章（`docs/10-DMA.md`）、工程 `mcu/code/stm32/03-uart-dma/main.c` 与 `mcu/code/common/behavior/circular.h`（只读静态阅读）；[第 8 章](./08-architecture-memory-clock.md)的总线矩阵、CCM 与外设基址，RM0008/RM0090 的定时器 DMA 请求位（`UDE/CCxDE`，第 12 章不展开），[第 13 章](./13-uart-framed-protocol.md)的 DMAT/DMAR 与 TC 边界、[第 2 章](../v0-foundations/02-c-volatile-ub.md)的 volatile 合同、[第 3 章](../v0-foundations/03-struct-abi-registers.md)的寄存器结构体。RM0090 §10.3.3、RM0008 第 13 章表 78/79、DS5319 与 HAL 源码行号均转引自上述来源。

## 先做出来

不接板子也能完成最小胜利：把“剩余项数”翻译成“已写字节数”。三条公式：

```text
已写项数 = NDTR 初值 − 当前 NDTR
已写字节 = 已写项数 × 每项字节数
环形位置 = (NDTR 初值 − 当前 NDTR) mod NDTR 初值
```

表里限定首次传输尚未回装、PSIZE=MSIZE且数组仍归DMA写，剩余NDTR都取3；若已经循环过，不能由这个数推累计总量：

| 场景 | 缓冲区 | 每项宽度 | NDTR 初值 | 当前 NDTR | 已写 | 半满位置 |
| --- | --- | --- | --- | --- | --- | --- |
| F103 USART1_RX 环形 | 64 字节 | 8 位 = 1 字节 | 64 | 3 | 61 字节 | 32 字节 |
| F407 ADC 环形 | 64 个采样 | 16 位 = 2 字节 | 64 | 3 | 61 个采样 = 122 字节 | 32 个采样 = 64 字节 |

同一句“还剩 3”，在字节宽度下是已写 61 字节，在半字宽度下是已写 122 字节。把 NDTR 当字节，后半段就会从奇数地址开始切，读出来整体错位。

![手绘板：NDTR 数的是项不是字节——同一个「还剩 3」，8 位环已写 61 字节，16 位环已写 122 字节；模差不是累计进度，16 位一轮最多 65535 项（原理示意，非实拍）](/images/ch14-ndtr-units.png)

![DMA 两级选路与 NDTR 计数：F407 的 USART1→DMA2→Stream5→CHSEL=4（待复核），F103 固定 CH5/CH4；PAR 固定、M0AR 递增、NDTR 按项递减；ADC 64 个半字、NDTR=3 即 122 字节；UART 64 字节环半满 32 字节约 2.78ms](/arch/dma-paths.png)

押一题再往下读：F407 上把 USART1_RX 配到 DMA1 的 Stream5、Channel4，时钟开了、流也置了 EN，数据会不会来？基本不会：USART1 挂在 APB2，F4 的 APB2 请求归 DMA2，控制器选错时流配置全部正确、NDTR 也一动不动，而且不报错。同一个 USART1，在 F103 上却必须走 DMA1 通道 5，因为 C8 根本没有 DMA2。这个对照是后面所有讨论的起点。

时间上的最小预算也能先算：115200 8N1 一个字节 10 位，约 86.8µs；64 字节环形缓冲的半满点是 32 字节，32 × 10 / 115200 ≈ 2.78ms。也就是说，半区消费者须在HT交出前半区到TC再次回写之间完成消费，延迟和复制总预算约2.78ms；当前03-uart-dma的consume_rx在DMA/USART ISR内运行，主循环负责排空发送队列，不是靠主循环定期扫描NDTR。这个数字是公式算出的期限，不是上板测得的中断间隔。

## 机制

### 一、二级选择：F4 是控制器→流→通道，F1 只有固定通道

F407 的 DMA 请求要走三层：先选控制器（DMA1 或 DMA2），再选控制器里的某条流（8 条之一），最后由该流的 `CHSEL[2:0]` 在 8 个通道里选一个。S8 把“流 × 通道”叫二级选择，控制器算作外面前提；落到寄存器上，流是“你写哪一组 `SxCR/NDTR/PAR/M0AR`”，通道是 `SxCR` 的 bit27:25。通道不是一根物理线，而是“这条流接哪根请求线”的选择码。

F103 只有一级：DMA1 的 7 条通道各自固定接一组外设请求，`CCR` 里没有 CHSEL 位。USART1_RX 的请求线只接在通道 5 上，配到通道 4 就一直等不到；通道 4 接的是 USART1_TX。大容量型号有 DMA2 的 5 条通道，但 C8 是中密度，只有 DMA1。

| 项 | F407 | F103（C8） |
| --- | --- | --- |
| 控制器 | DMA1 + DMA2 | 只有 DMA1 |
| 规模 | 每个控制器 8 条流，每条流 8 个通道 | 7 条通道，请求固定 |
| 选择方式 | 控制器 → 流 → `CHSEL` | 通道即外设槽位 |
| 请求映射 | RM0090 §10.3.3（S8 记为表 42/43；工程注为 Rev 18 Table 43） | RM0008 第 13 章表 78（表 79 是 DMA2） |
| 主要寄存器 | `SxCR/NDTR/PAR/M0AR/M1AR/FCR` | `CCR/CNDTR/CPAR/CMAR` |
| FIFO | 每流 4 × 32 位 | 无 |
| 硬件双缓冲 | `DBM` + `M1AR` + `CT` | 无，只能用 HT/TC 分半区 |
| 内存到内存 | 只有 DMA2 支持 | DMA1 用 `CCR.MEM2MEM` 支持 |
| 数据宽度 | 8/16/32 位 | 8/16/32 位 |

![F4 的二级选择：控制器、流、通道逐级选定，CHSEL 决定这条流接哪个外设请求](/figures/stm32-08-dma-stream.svg)

F4 的请求归属大体按总线划：APB1 外设进 DMA1，APB2 外设进 DMA2，另有 SDIO、DCMI 这类 AHB 请求也挂在 DMA2。USART1 在 APB2 上，所以它的请求在 DMA2，这是“数字小的外设配数字小的 DMA”这条直觉最容易出错的地方。F1 不适用这条规则：C8 只有 DMA1，APB2 上的 USART1、SPI1、TIM1 请求也全落在 DMA1 的固定通道上。同一个外设跨系列移植，先问“这个系列有几个控制器”，再问“请求映射表怎么写”。F1同一通道上列出的多个请求不是可并行独立使用的多条通道；要排查同通道资源冲突，不能同时使能互相冲突的外设请求。

F103 的 DMA1 请求映射（节选，完整见 RM0008 表 78）：

| 通道 | 主要请求（节选） |
| --- | --- |
| CH1 | ADC1、TIM2_CH3、TIM4_CH1 |
| CH2 | SPI1_RX、USART3_TX、TIM1_CH1、TIM3_CH3 |
| CH3 | SPI1_TX、USART3_RX、TIM3_CH4、TIM3_UP |
| CH4 | SPI2/I2S2_RX、USART1_TX、I2C2_TX、TIM1_CH4 |
| CH5 | SPI2/I2S2_TX、USART1_RX、I2C2_RX、TIM1_UP |
| CH6 | USART2_RX、I2C1_TX、TIM1_CH3、TIM3_CH1 |
| CH7 | USART2_TX、I2C1_RX、TIM2_CH2、TIM2_CH4、TIM4_UP |

F407 的请求表不整表复述。S8 与工程 `03-uart-dma/main.c` 都注明没有取得 RM0090 请求映射表的正文，USART1_RX 的 DMA2 Stream5 Channel4（也可走 Stream2 Channel4）与 USART1_TX 的 DMA2 Stream7 Channel4 是按常用映射写的，工程要求上板自检才能坐实。这里沿用这组取值，但在正文与读数来路表里都标为待复核；换芯片或换库时以 RM0090 §10.3.3 的表为准，别背编号。

### 二、两个地址一个长度：PAR、M0AR、NDTR

DMA 一次传输要告诉硬件三样东西：外设地址、内存地址、搬多少项。S8 把它叫“三个地址一个长度”，严格说前两个是地址，NDTR 是长度。F4 的寄存器名是 `PAR/M0AR/NDTR`（双缓冲再加 `M1AR`），F1 是 `CPAR/CMAR/CNDTR`。名字不同，分工相同。

| 寄存器 | F407 | F103 | 作用 |
| --- | --- | --- | --- |
| 外设地址 | `PAR` | `CPAR` | 外设数据寄存器地址，通常固定，`PINC=0` |
| 内存地址 | `M0AR` | `CMAR` | 缓冲区基址，通常递增，`MINC=1` |
| 第二内存地址 | `M1AR` | 无 | 仅双缓冲模式使用 |
| 剩余项数 | `NDTR` | `CNDTR` | 16 位，每搬一项减 1，到 0 表示本轮结束 |

NDTR 数的是数据项，不是字节。半字宽度下 `NDTR = 64` 表示 64 个半字 = 128 字节；`NDTR` 读回 3 表示还剩 3 个半字。NDTR 只有 16 位，一轮最多 65535 项；8 位下是 65535 字节，半字下是 131070 字节，更大的块要分段或重新装填。两条示例链路都让 `PSIZE = MSIZE`，NDTR 就是这一侧的项数；宽度不同时 NDTR 数的是传输拍数，还要叠加 FIFO 的打包规则，不能直接把字节数写进去。

F4 的方向由 `SxCR.DIR[1:0]`（bit7:6）决定：`00` 外设到内存、`01` 内存到外设、`10` 内存到内存、`11` 保留。这是个“看起来是一位其实是两位”的典型陷阱，CMSIS 头文件里 `DMA_SxCR_DIR_Pos = 6`、掩码 `0x3 << 6`。F1 的 `CCR.DIR` 只有 bit4 一位（0 外设到内存，1 内存到外设），内存到内存另由 `CCR.MEM2MEM`（bit14）打开，源地址放 `CPAR`、目的地址放 `CMAR`。F4 的内存到内存只有 DMA2 支持；在 DMA1 上写 `DIR=10` 不会搬数据，这一点在 RM0090 与 AN4031 的说明里都有。

地址增减与宽度是两组独立位。F4 的 `PINC` 在 bit9、`MINC` 在 bit10、`PSIZE[1:0]` 在 bit12:11、`MSIZE[1:0]` 在 bit14:13；F1 的 `PINC` 在 bit6、`MINC` 在 bit7、`PSIZE` 在 bit9:8、`MSIZE` 在 bit11:10。宽度编码两边相同：`00` 字节、`01` 半字、`10` 字。外设数据寄存器只有一个地址，所以外设侧 `PINC=0`；内存数组要往后走，所以 `MINC=1`。F4 走直接模式（`FCR.DMDIS=0`）时源与目的宽度必须相同；要按不同宽度打包，得开 FIFO 模式并设阈值。

F407 的 USART1_RX 落位（寄存器写法按 `03-uart-dma/main.c` 归并，流与通道待复核）：

```c
/* F407 USART1_RX：DMA2 Stream5，通道 4（待复核），8 位环形 */
DMA2_Stream5->CR  &= ~1U;                  /* EN=0，先关流 */
while (DMA2_Stream5->CR & 1U) { }          /* 等 EN 真正落下 */
DMA2_Stream5->PAR  = (uint32_t)&USART1->DR;
DMA2_Stream5->M0AR = (uint32_t)rx_buf;
DMA2_Stream5->NDTR = sizeof rx_buf;        /* 64 个数据项，8 位下就是 64 字节 */
DMA2_Stream5->FCR  = 0;                    /* 直接模式，PSIZE=MSIZE=8 位 */
DMA2_Stream5->CR   = (0U << 6)             /* DIR=00：外设→内存 */
                   | (1U << 2)             /* TEIE */
                   | (1U << 3)             /* HTIE */
                   | (1U << 4)             /* TCIE */
                   | (1U << 8)             /* CIRC=1 */
                   | (1U << 10)            /* MINC=1 */
                   | (4U << 25);           /* CHSEL=4 */
DMA2_Stream5->CR  |= 1U;                   /* EN=1 最后开 */
USART1->CR3       |= (1U << 6);            /* DMAR=1：RXNE 交给 DMA */
```

F103 的同一件事换成通道模型，`CCR` 的位号与 F4 完全不同：

```c
/* F103 USART1_RX：DMA1 通道 5，8 位环形 */
DMA1_Channel5->CCR   = 0;                  /* EN=0 */
DMA1_Channel5->CPAR  = (uint32_t)&USART1->DR;
DMA1_Channel5->CMAR  = (uint32_t)rx_buf;
DMA1_Channel5->CNDTR = sizeof rx_buf;
DMA1->IFCR           = 0x000F0000U;        /* 清通道 5 的四个标志（CGIF5..CTEIF5） */
DMA1_Channel5->CCR   = (1U << 5)           /* CIRC */
                     | (1U << 7)           /* MINC */
                     | (1U << 1);          /* TCIE */
DMA1_Channel5->CCR  |= 1U;                 /* EN */
USART1->CR3         |= (1U << 6);          /* DMAR */
```

两段代码只差“通道怎么选”和“寄存器叫什么”；UART 侧都只做一件事：置 `CR3.DMAR`，告诉 USART 收到的字节不要再等 CPU 读 `DR`，改成给 DMA 发请求。

### 三、循环模式：NDTR 回装，位置靠模差

普通模式下 `NDTR` 数到 0，传输结束，硬件清 `EN`，要再启动得重新配置。循环模式把 `CIRC` 置 1（F4 `SxCR` bit8，F1 `CCR` bit5）后，`NDTR` 归零时自动回装成初值，内部当前地址回到缓冲区起点，传输不停。`M0AR`/`CMAR` 里保存的仍是基址，实际写指针在硬件内部移动；要知道写到哪里，只能读 `NDTR` 反推。HT/TC 标志在循环模式下照常每半圈、每圈各置一次。

循环模式保证“不停”，不保证“不丢”。CPU 处理得比数据来得慢，旧数据就会被新数据盖上；这也意味着 `长度 − NDTR` 只是本圈的位置，不是累计进度。累计进度要么在每次服务时把增量加起来，要么在软件里单独计数；直接拿 `长度 − NDTR` 当总数，下一圈就会从最大值跳回 0。

![DMA 环形缓冲：写指针由 DMA 推进，读指针由 CPU 消费，半满 HT 与全满 TC 各触发一次中断](/figures/stm32-08-dma.svg)

位置算法在环形缓冲里必须带模：

```text
位置 = (NDTR 初值 − 当前 NDTR) mod NDTR 初值
增量 = (新位置 − 上次位置 + 缓冲区长度) mod 缓冲区长度
```

模差只能回答“转了一圈以内走了多少”。如果两次服务间已经跨过一整圈或更多，仅位置模差就不能恢复圈数；正好一圈时还可能看起来完全没动。

工程里的 `dma_consume()` 用事件位补其中一部分洞：先读一次状态标志，再读 `NDTR` 算位置，然后补读一次状态标志，把采样 `NDTR` 期间越过的边界也算进来；如果错误标志置位、HT 与 TC 同时积压，或者位置没动却报了 TC，就判定这段数据不可信（无法排除整圈丢失），丢弃并把 `lost` 加一，而不是猜一个增量。

它不覆盖“TC 置位且位置也变了”的情形：那时仍按模差返回最新一段，整圈丢失不会计入 `lost`，所以服务必须赶在边界积压之前。

标志的清除要走另一组寄存器。F4 的 `LISR/HISR` 是只读状态，`LIFCR/HIFCR` 才是写 1 清除；每条流占 6 位，流 5 在 `HISR` 里是 bit6 起的 `FEIF5/DMEIF5/TEIF5/HTIF5/TCIF5`，`TCIF5` 在 bit11。F1 的 `ISR` 同样只读，清标志写 `IFCR`，每条通道占 4 位，通道 5 的 `CTCIF5` 在 bit17。往状态寄存器写 1 什么都不会清，中断会反复进，这是 DMA 与 EXTI“写 1 清 pending”最容易混的一处。

![环形缓冲动画：NDTR 从 64 倒数到 0 又回装，CPU 读取速度慢于 DMA 时旧数据被覆盖](/anim/dma-circular-buffer.svg)

处理期限可以直接算：64 字节缓冲在半满点交出 32 字节，115200 8N1 下 32 × 10 / 115200 ≈ 2.78ms。这是“从 HT 到 TC”的预算，不是“一帧”的预算；实际半区消费者（当前工程为DMA/USART ISR中的consume_rx）须在这段时间里完成读取/复制，否则 TC 之后 DMA 就从缓冲区开头写起，把还没处理的数据覆盖掉。

![手绘板：CPU 与 DMA 的半满、全满缓冲区归属（原理示意，非实拍）](/images/ch14-dma-buffer-ownership.png)

### 四、乒乓/双缓冲：换的是块，不是期限

![双缓冲与期限：F407 DBM=1 时 M0AR/M1AR 轮换，CT 选当前写入块；ADC 1 Msps×64 半字=64 µs 期限，UART 半满 32 B≈2.78 ms；F103 无 DBM，半区所有权只是模拟；CCM 不可达](/arch/dma-deadline.png)

F4 的硬件双缓冲（`DBM=1`，`SxCR` bit18）给一条流两个内存区：`M0AR` 与 `M1AR`。DMA 写其中一块时，CPU 可以读另一块；一块填满后硬件自动切换，置一次 TC，`CT`（bit19）指示当前正在使用哪一块。软件在 TC 中断里读 `CT`，处理刚交出的那一块，不要碰 `CT` 指向的块。

双缓冲解决的是“写和读撞在同一块上”，没有解决“CPU 来不及”。CPU 必须在 DMA 把下一块也填满之前处理完当前块；超期后新数据会在切回该块后逐项覆盖旧数据，不能把所有权通知当成原子快照。举例：ADC 以 1Msps 连续采样，每块 64 个半字，一块的填充时间是 64µs；处理延迟加处理时间若超过64µs，DMA切回时就会从上一块的首项开始覆盖；不是TC瞬间原子覆盖整块。这个 64µs 是按输入数算出来的期限，不是某块板的实测值。

F103 没有 `DBM`，只能用“半区所有权”模拟乒乓：DMA 填前半区时 CPU 处理后半区，HT 与 TC 各交出一半。这个做法与硬件双缓冲有一个关键差别：DMA 不会在半区边界停下来等你，HT/TC 只是通知；如果你把通知当成分界，处理慢一拍，DMA 已经写进你正在读的半区。

![双缓冲乒乓动画：DMA 写一块、CPU 读另一块，CT 指示当前写入块，超期则整块被覆盖](/anim/dma-pingpong.svg)

### 五、HAL 使能窗口：先关 EN，再落位，最后开

`CHSEL`、`CIRC`、`MINC`、`DIR`、`PSIZE`、`MSIZE` 这些流属性只在 `EN=0` 时可写；`EN=1` 时写入不生效，硬件也不会替你停流。普通模式改 `NDTR/PAR/M0AR` 与受保护的FIFO配置也要先关EN。DBM有专门例外：运行时可更新当前未使用的M0AR或M1AR，不能改CT指向的活动块；本轮打开的官方 HAL_DMAEx_ChangeMemory 注释明确了这个条件，不能把“EN=1时所有地址都不可改”讲成通则。要改配置，先清 `EN`，再轮询读回 0，等当前这一拍真正结束；然后落位，最后把 `EN` 置 1。这个“EN 可改窗口”是 DMA 初始化顺序的硬约束，和 USART 先关 `UE` 再改 `BRR` 是同一类规矩。

HAL 把同一组动作拆成两段。`HAL_DMA_Init()` 管流属性：先 `__HAL_DMA_DISABLE()` 并轮询 `CR.EN`，等不到就按 `HAL_GetTick` 超时返回；再把 `CHSEL`、优先级、宽度、增量、循环、方向、`CT`、`DBM` 等配置位清掉，按 `Init` 各字段拼成一笔写回 `CR`，FIFO 的 `DMDIS/FTH` 另写 `FCR`。

`HAL_DMA_Start()` 管本次传输参数：调用 `DMA_SetConfig()` 先清 `DBM`，再写 `NDTR`，按方向写 `PAR` 与 `M0AR`，最后开 `EN`；双缓冲不走这条路径，要用 `stm32f4xx_hal_dma_ex.c` 里的 `HAL_DMAEx_MultiBufferStart()`（或手写 `M1AR` 与 `DBM`）。

中断版 `HAL_DMA_Start_IT()` 打开 TC/TE/DME，有半传输回调时再加 HT，不打开 FE。行号来自 S8 对 ST 官方 `stm32f4xx_hal_driver` master@1f6451c 的记录；`DMA_SetConfig()` 与 `HAL_DMA_Start_IT()` 的行为已按 1f6451c 原文核对，行号未逐条复核：

| 手写落位（`03-uart-dma/main.c`） | HAL 对应（`stm32f4xx_hal_dma.c` @ 1f6451c） | 对照结论 |
| --- | --- | --- |
| 配置前先 `CR=0`、等 EN 落下 | `HAL_DMA_Init()`（L170）先禁用再轮询，超时返回 `HAL_TIMEOUT`（L208-227） | 同一个窗口：EN=1 时改 CHSEL/CIRC 无效 |
| CHSEL/CIRC/MINC/PSIZE 逐位拼 CR | 同函数把 CHSEL、优先级、宽度、增量、循环、方向、CT、DBM 等配置位清掉（L231-237），再一笔写回（L250）；FIFO 另写 FCR（L285） | 手写掩码等于 HAL 的读-改-写 |
| 自己写 NDTR/PAR/M0AR | 留到 `HAL_DMA_Start()` 的 `DMA_SetConfig()`：先清 DBM，再写 NDTR（L1157）、PAR/M0AR 按方向（L1163-1175） | HAL 把流属性与本次传输分两步；DBM 不能经 Start 保持 |
| `DMA2_Stream5_IRQHandler()` 管 HT/TC、写 HIFCR 清标志 | `HAL_DMA_IRQHandler()` 按 HISR 分发回调，清标志回写 IFCR（L708） | 清标志只写 IFCR 系列，不碰只读状态 |

对应的 HAL 序列（F407 的 USART1_RX，通道与流取工程值，待复核）：

```c
hdma_usart1_rx.Instance                 = DMA2_Stream5;
hdma_usart1_rx.Init.Channel             = DMA_CHANNEL_4;
hdma_usart1_rx.Init.Direction           = DMA_PERIPH_TO_MEMORY;
hdma_usart1_rx.Init.PeriphInc           = DMA_PINC_DISABLE;
hdma_usart1_rx.Init.MemInc              = DMA_MINC_ENABLE;
hdma_usart1_rx.Init.PeriphDataAlignment = DMA_PDATAALIGN_BYTE;
hdma_usart1_rx.Init.MemDataAlignment    = DMA_MDATAALIGN_BYTE;
hdma_usart1_rx.Init.Mode                = DMA_CIRCULAR;
hdma_usart1_rx.Init.Priority            = DMA_PRIORITY_LOW;
HAL_DMA_Init(&hdma_usart1_rx);          /* 流属性：CR/FCR */
__HAL_LINKDMA(&huart1, hdmarx, hdma_usart1_rx);
HAL_UART_Receive_DMA(&huart1, rx_buf, sizeof rx_buf);
```

`HAL_UART_Receive_DMA()` 内部再调 `HAL_DMA_Start_IT()` 落 `NDTR/PAR/M0AR` 并开 `EN`，同时置 USART 的 `CR3.DMAR`。这与手写的“先关、再配、最后开”是同一个顺序，只是 HAL 多了超时保护与句柄状态检查。F103 的窗口相同，位号不同：`CCR.EN` 是 bit0，`CHSEL` 不存在，通道由你选的外设实例决定；配置前若开中断，先把 `IFCR` 里该通道的四个标志清零。

![EN 可改窗口：只有 EN=0 时能改 CHSEL/CIRC/MINC，HAL 的初始化与启动分两段落位](/anim/dma-hal-en-window.svg)

### 六、与 UART、ADC 的分工：DMA 只搬，边界归别人

UART 侧的握手只有两个使能位：发送 `CR3.DMAT`（bit7），接收 `CR3.DMAR`（bit6）。置位后，发送数据寄存器空（TXE）或收到一个字节（RXNE）时，外设向 DMA 发请求；DMA 搬完自己那一项，请求线落下，等下一次。DMA 不理解“帧”，也不理解“包头”，它只认 NDTR 数完没有。

发送侧最容易混的是两个 TC。DMA 的 TC 只说明最后一个字节已经写进 USART 的 `DR`，此时移位寄存器可能还在把停止位往外送。

USART 的 TC 才说明包括停止位在内的整个字节已经发完。RS-485 切方向、断电、进低功耗之前等的是后者，不是前者。接收侧的 IDLE 只是“线空了一个帧时间”的通知，不是协议帧边界；把 IDLE 次数当帧数，主机两条命令之间稍一停顿就会多计一帧。这两条边界在[第 13 章](./13-uart-framed-protocol.md)里已经拆过，DMA 只是把“每字节一次中断”换成“每半圈/每圈一次中断”。

ADC 侧的关键在宽度上：转换结果是一个半字，NDTR 数的是采样个数，不是字节数。ADC 连续转换加 DMA 循环模式，HT/TC 把缓冲区切成两个半区；CPU 处理一个半区时，DMA 填另一个。定时器触发 ADC、ADC 再请求 DMA 的链路里，DMA 只负责搬结果，不负责启动转换；触发源与采样时间在[第 15 章](./15-adc-dac-sampling.md)；定时器的 `UDE/CCxDE` 请求位定义查 RM0008 与 RM0090，[第 12 章](./12-timers-pwm.md)只把 DMA 交给这里，不展开这两位。

UART 接收的环形缓冲还有一条软件边界：`NDTR` 给出的是“已经写到哪里”，不是“这次新收到多少字节”。两次快照之间若 DMA 转了一圈，模差会失真；要么按半区服务，要么像 `dma_consume()` 那样在边界事件积压时丢弃并计数。把 `Size` 或 `NDTR` 直接当帧长，等于让搬运进度冒充协议长度。

### 七、总线仲裁与够不着的地方

DMA 是 AHB 上的总线主人，和 CPU、以太网 MAC 等一起挂在总线矩阵上。DMA 搬运不占 CPU 的指令周期，但要与 CPU 争总线；[第 8 章](./08-architecture-memory-clock.md)的访问路线表把这两面并排放：DMA 搬 SRAM 时 CPU 可以同时从 Flash 取指，抢的是同一块 SRAM。DMA 搬运密集时，CPU 取指与访存会排队，跑分变慢不是错觉，是仲裁；F4 的 FIFO 与突发能把多次小传输合并，减少占用，但不能让 DMA 消失。本章F103/F407没有D-Cache，这只免除了D-Cache清理/失效，并不自动解决编译器复用旧值、并发访问和缓冲区归属；CPU应在数据已完成且归自己消费的窗口读取，按实际实现使用volatile/内存屏障或受控快照。当前03工程的数组和队列使用volatile及MCU_DMB，不能据“无Cache”删掉这些同步。带 Cache 的 H7/F7 才有维护问题，不在讨论范围。

F407 有一块 DMA 够不着的地方：CCM 在 `0x1000_0000`，64KB，只挂 CPU 的数据总线，不在总线矩阵上。

把接收数组放进 CCM，DMA 访问就没有从机通路可走：这一拍不是搬成功，而是传输出错，`TEIF` 置位、`NDTR` 停在原地。程序若不查 TE、只等 HT/TC，看起来才像“什么都没报、数据静默丢失”；来源的写法只到“静默丢数据”，出错位这一层是这里按总线结构推的，标为待复核。

对当前F407工程，DMA接收缓冲应位于普通SRAM的0x20000000–0x2001FFFF；F103C8片内SRAM是0x20000000–0x20004FFF，不能照搬F407的128KB范围。仅给对象加名为.ccmram的section属性不证明它落在CCM，必须看链接脚本与map中的实际地址/长度。

真正要求是缓冲生命周期覆盖整个DMA使用期、地址可达且满足对齐/归属；静态或全局数组是常用做法，不是C语法上的唯一合法方式。局部数组只有在函数退出/复用栈之前DMA已停止且无待消费访问时才安全，不能把失效栈地址交给后台DMA。

## 测量与证据

这里没有板上读数。S8 的“烧录后……在 GDB 里读 `g_rx_bytes` 和 `g_frames`”是操作指令与预期，正文的“亲眼看到 NDTR 在倒数”没有对应的日志或截图；根书第 10 章的“动手实验”列了四步，没有结果表；`03-uart-dma` 的模块注释把 Stream/Channel 标成“待上板实测确认”。能拿出来的证据分五类：手册位与规则、按公式算出的数值、源码静态事实、来源自述与记录、待做的实验设计。

### 台架：NDTR 轨迹与半区（来源实验设计，记录待做）

装备照 S8 与根书第 10 章：F407 板一块、ST-Link、USB-TTL、杜邦线、串口助手；F103 一侧用 BluePill 与 ST-Link。以下为后续取证方案，本轮不连接、烧录或注入故障；第4–5项并非已存在的完整可运行实验，须先单独设计：

1. 进入 `mcu/code/stm32/03-uart-dma`，`make` 后 `make flash`；USB-TTL 接 PA9/PA10，115200 8N1，两边共地。
2. 串口助手连发一长串字符（例如 200 字节），观察 `g_rx_bytes` 与 `g_frames` 是否增长。`g_frames` 数的是 IDLE 通知次数，不是协议帧数，这个命名在工程里是历史遗留。
3. 采集运行中的NDTR与HT/TC、消费位置快照，预期有递减与回装；0可能只瞬间出现，没读到0不算失败。断点暂停CPU时DMA未必暂停，必须登记调试冻结条件，不能把断点下积压冒充正常轨迹。
4. F103的4KB内存搬运是来源实验设计；仓库现有examples与mcu/code未找到DMA_MemCopy函数/完整入口，不能照函数名当现成命令执行。后续需先设计源/目的两个4KB数组、栈及其它对象的总SRAM预算，再实现并逐字节比较、记录TC/TE；本轮不新增实现。
5. CCM不可达故障只保留为设计：需要单独修改链接布局、核实map地址并制定错误/重启观测，不能只加section属性就宣称构成CCM实验。当前消费层会把部分错误/积压计入g_overruns并丢弃，但未实现本故障注入所需的完整恢复；调试暂停前标志也可能已被ISR处理，须先设计取证，再另行授权实施。

预期现象（来源写的是预期，不是读数）：NDTR 递减到 0 后回装；`g_rx_bytes` 持续增长；`g_frames` 随 IDLE 增加；4KB 内存搬运转发后逐字节相等、TC 置位；缓冲区挪进 CCM 后预期是 `TEIF` 置位、`NDTR` 停在原地，只有程序不查 TE 时才表现为数据静默丢失。最后一条尤其要说清：“静默”只说明没人查 TE，不证明 DMA 写对了地方；反过来，NDTR 在动也只证明“有请求、流使能了”，不证明“字节写对了地方”。

记录表至少要有这些列；S8 与根书第 10 章都没有留下已填的记录：

| 日期 | 板子 | 工程/固件 | 观测手段 | NDTR 轨迹 | 缓冲区比对 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| | | | | | | |

一次完整记录还要留下 GDB 输出或串口日志、缓冲区比对结果、读回的 `CR/NDTR/PAR/M0AR` 值。只有“灯在闪”不算 DMA 证据：灯可能只是主循环在跑，NDTR 是否递减、缓冲区内容是否正确才是两条独立判据。

### 读数来路表

| 取证项 | 来路 | 读数或结论 | 性质 |
| --- | --- | --- | --- |
| F4 的 DMA 结构 | RM0090 §10.3，转引 S8 | DMA1/DMA2 各 8 条流，每流 8 个通道 | 手册规则 |
| F1 的 DMA 结构 | RM0008 第 13 章、DS5319 §2.3.13，转引根书第 10 章 | DMA1 7 通道；C8 中密度没有 DMA2，大容量才有 5 通道 DMA2 | 手册规则（DS 未核原件） |
| F103 的 USART1/ADC1 请求 | RM0008 表 78，转引根书第 10 章 | ADC1→CH1，USART1_TX→CH4，USART1_RX→CH5 | 手册规则（转引） |
| F407 的 USART1 请求 | S8、`03-uart-dma/main.c`、根书第 10 章 | RX→DMA2 Stream5/2 Channel4，TX→DMA2 Stream7 Channel4；来源自注未取得表正文 | 来源说法，待复核 |
| F4 内存到内存仅 DMA2 | RM0090 与 AN4031 的说明，外部交叉核对 | DMA1 上 DIR=10 不搬；DMA2 的 DIR=10 以 PAR 为源、M0AR 为目的 | 手册规则 |
| DIR 两位与三种组合 | CMSIS 头记录（S8 研究基线直读）、RM0090 | `DIR_Pos=6`、掩码 `0x3<<6`；00=P→M，01=M→P，10=M→M | 手册规则（源码互证） |
| NDTR 的位宽与单位 | RM0008/RM0090 寄存器语义、根书第 10 章 | 16 位；按数据项计数；64 个半字 = 128 字节 | 手册规则 |
| NDTR=3 的半字数据 | 这里按公式算 | 8 个半字中已写 5 个采样 = 10 字节；HT 在第 4 个采样 = 8 字节 | 推导 |
| 64 字节环的半满期限 | 这里按公式算 | 32 × 10 / 115200 ≈ 2.78ms | 推导 |
| 循环模式的回装与覆盖 | RM0008/RM0090、S8、根书第 10 章 | NDTR 归零回装；地址回卷；不保证 CPU 来得及 | 手册规则 |
| F4 的 DBM/CT/M1AR | CMSIS 头记录（S8 研究基线直读）、S8 | DBM=bit18，CT=bit19，M1AR 为第二缓冲区 | 手册规则（源码记录） |
| F4 的 SxCR 位图 | RM0090、`main.c` 宏 | EN0、DIR7:6、CIRC8、PINC9、MINC10、PSIZE12:11、MSIZE14:13、CHSEL27:25 | 手册规则（源码互证） |
| F1 的 CCR 位图 | RM0008 第 13 章 | EN0、TCIE1、HTIE2、TEIE3、DIR4、CIRC5、PINC6、MINC7、PSIZE9:8、MSIZE11:10、MEM2MEM14 | 手册规则 |
| F1 的 IFCR 通道 5 位 | RM0008 第 13 章 | CGIF5=16、CTCIF5=17、CHTIF5=18、CTEIF5=19 | 手册规则 |
| DMA 时钟门 | RM0090/RM0008、仓库速查表 | F4：`RCC_AHB1ENR` bit21/22；F1：`RCC_AHBENR` bit0/1 | 手册规则 |
| DMA 基址与流偏移 | [第 8 章](./08-architecture-memory-clock.md)、RM0090 | F4：DMA1 `0x4002_6000`、DMA2 `0x4002_6400`，流 5 基址 +0x88；F1：DMA1 `0x4002_0000` | 手册规则（源码互证） |
| F4 的 FIFO 与直接模式 | RM0090/AN4031 | 每流 4×32 位；直接模式下 PSIZE 必须等于 MSIZE | 手册规则 |
| CCM 与 DMA 的失败症状 | S8、根书第 10 章、[第 8 章](./08-architecture-memory-clock.md)；TE 推断来自正文 | 来源只写“静默丢数据”；这里推断：DMA 访问 CCM 没有从机通路，应置 `TEIF`、`NDTR` 停在原地，不查 TE 时才像静默丢失 | 来源说法 + 这里推断，未上板，待复核 |
| HAL 行号与行为 | S8 对 1f6451c 的行号记录；`DMA_SetConfig`/`Start_IT` 行为按 1f6451c 原文核对 | 行号见 S8 记录（L170/L208-227/L231-237/L250/L285/L1157/L1163-1175/L708）；`DMA_SetConfig` 先清 DBM，再写 NDTR/PAR/M0AR；`Start_IT` 开 TC/TE/DME，有半传输回调时加 HT | 行号来源记录，未逐条复核；行为已核原文 |
| “清标志已在坑里验证过” | S8 正文与 `s08-dma` 题库 | 没有波形、日志或截图 | 来源说法，待复核 |
| `dma_consume()` 的丢弃判据 | `mcu/code/common/behavior/circular.h` 静态阅读 | 错误、HT+TC 同时积压、位置不动却报 TC 时丢弃并计 `lost` | 源码静态，未复跑 |
| 上板读数 | S8、根书第 10 章 | 两边都没有记录；实验待做 | 待做实验 |

这些数能互相对上的只有公式、位定义与源码常量：公式能证明 64 字节环的半满预算是 2.78ms，不能证明某块板上的主循环真的在 2.78ms 内处理完；位定义能证明 `CHSEL=4` 选的是通道 4，不能证明 USART1_RX 的请求线真的接在 DMA2 Stream5 上。要补上后者，得按台架留下 NDTR 轨迹与缓冲区比对。

测验题原样复制自 MCU 书的 `s08-dma` 题库；其中“这条已经在坑里验证过”是来源叙述，这里没有找到对应的日志或波形，按待复核处理。

<QuizBank chapter="s08-dma" />

## 失败分支

| 现象 | 原因 | 区分证据 | 下一动作 |
| --- | --- | --- | --- |
| DMA 完全不动，NDTR 保持初值 | 控制器选错（F4 的 USART1 配到了 DMA1），或外设请求没使能 | 读 `RCC_AHB1ENR` 的 DMA2EN；读 USART `CR3.DMAR/DMAT`；NDTR 是否在动 | 先把控制器换到 DMA2，再置 DMAR/DMAT |
| 流配置写了没反应 | DMA 时钟没开，或 `EN=1` 时改 CHSEL/CIRC | 读 `RCC_AHB1ENR` 对应位；读回 `CR.EN` | 先开时钟，清 EN 并等 0 再改 |
| 数据只来一批就停 | 该用循环却配了普通模式 | 读 `CR.CIRC`；NDTR 到 0 后是否回装 | 置 `CIRC=1` |
| 数据整体错位或后半段从奇数地址开始 | PSIZE/MSIZE 不一致，或把 NDTR 当字节 | 读 `CR` 的 PSIZE/MSIZE；半字缓冲区地址是否 2 字节对齐 | 统一宽度，按项数换算字节 |
| 每个字节都写进缓冲区首地址 | `MINC=0` | 读 `CR.MINC`；数组是否只有第一个字节在变 | 置 `MINC=1` |
| 外设侧地址乱跑 | `PINC=1` 配到了固定数据寄存器 | 读 `CR.PINC`；CPAR 是否在变 | 外设侧置 `PINC=0` |
| 中断进一次就风暴 | 清标志写到了只读的 `HISR/LISR` 或 `ISR` | 读代码里的清除语句；标志是否一直置位 | 改写 `HIFCR/LIFCR`（F4）或 `IFCR`（F1） |
| F103 上照搬 F4 的 Stream 配置 | C8 没有 DMA2，也没有流 | 读 `RCC_AHBENR` bit1；写 `DMA2` 地址是否 HardFault | 改用 DMA1 的固定通道 |
| USART1_RX 配到 DMA1 通道 4 | 通道 4 是 TX，RX 在通道 5 | 对照 RM0008 表 78；TX 能发、RX 不动 | 把 RX 改到通道 5 |
| 数据静默丢失，查 TE 才见错 | 缓冲区放进了 CCM（F407），DMA 访问没有从机通路 | 地址在 `0x1000_xxxx`；`HISR` 的 `TEIF5` 是否置位；`NDTR` 是否停在原地 | 搬到 `0x2000_0000` 的通用 SRAM |
| 半区处理切错位置 | 把 HT 当成固定 4 字节，而不是“缓冲区一半的项数” | 读 NDTR；8 个半字的缓冲区在 HT 时应已写 4 个采样 = 8 字节 | 按项数×宽度换算 |
| 循环模式下进度越算越大或跳回 0 | 用 `长度 − NDTR` 当累计进度 | 下一圈开始位置从 64 跳回 0 | 累计增量，或按半区服务 |
| 双缓冲整块丢数据 | CPU 处理时间超过一块的填充时间 | `CT` 是否已切换；丢的是整块而不是零散字节 | 缩短处理，或加缓冲深度 |
| UART 最后一字节被截 | 等 DMA 的 TC 就切了 RS-485 方向 | DMA TC 已置、USART TC 还没置 | 等 USART 的 TC 再切向 |
| 把 IDLE 次数当帧数 | IDLE 只是线路空闲通知 | 两条命令之间停顿超过一个帧时间就多计 | 用协议定界，IDLE 只当通知 |
| ADC 数据长度差一倍 | NDTR 按半字算，却被当成字节 | 读 NDTR 与缓冲区类型；`uint16_t` 数组 | 按采样个数×2 换算字节 |
| CPU 在 DMA 期间明显变慢 | 总线仲裁，不是 bug | 关掉 DMA 复测同一段代码；FIFO/突发是否开启 | 接受仲裁，优化搬运密度 |

## 跨平台边界

F407 一侧：DMA1 与 DMA2 都挂在 AHB1，基址分别是 `0x4002_6000` 与 `0x4002_6400`；每个控制器 8 条流，流 0 的寄存器从 `0x10` 开始，每条流隔 `0x18`，流 5 的基址是 `+0x88`。公共寄存器是 `LISR 0x00`、`HISR 0x04`、`LIFCR 0x08`、`HIFCR 0x0C`。时钟门是 `RCC_AHB1ENR` 的 bit21/22。

每条流有 4×32 位 FIFO，支持双缓冲 `DBM/M1AR/CT`；内存到内存只有 DMA2 能做。USART1 在 APB2，请求归 DMA2，RX 常用 Stream5 Channel4（或 Stream2 Channel4），TX 常用 Stream7 Channel4，这两个编号待复核。CCM 在 `0x1000_0000`，DMA 无路可达。F4 没有 D-Cache；HAL 行号与行为绑定 `1f6451c` 版本，换库先核对。

F103 一侧：DMA1 在 `0x4002_0000`，7 条通道；C8 只有 DMA1，没有 DMA2。通道寄存器从 `0x08` 开始，每条隔 `0x14`，顺序是 `CCR/CNDTR/CPAR/CMAR`；公共寄存器是 `ISR 0x00`、`IFCR 0x04`。时钟门是 `RCC_AHBENR` bit0。

通道与外设请求固定绑定：ADC1→CH1、USART1_TX→CH4、USART1_RX→CH5，其余查 RM0008 表 78。`CCR` 的 `MEM2MEM`（bit14）支持内存到内存，`PSIZE/MSIZE` 与 `PINC/MINC` 位号都和 F4 不同；没有 FIFO、没有 DBM，乒乓只能用 HT/TC 半区模拟。DMA1 是 AHB 主设备，外设寄存器在 APB 上，搬运要过桥。F103 没有 CCM，也没有 D-Cache；4KB 内存搬运实验能放进 20KB SRAM。

GD32 与 ESP32 不在平台列表。GD32 的 DMA 控制器命名、通道数与请求映射和 STM32 不是一套，完整对照见[第 29 章](../v4-platforms/29-gd32-arm-riscv.md)；ESP32-S3 的 DMA 由 ESP-IDF 的驱动与描述符管理，寄存器名字一个都不要带过去，外设与驱动框架见[第 31 章](../v4-platforms/31-esp32-drivers-audio.md)。多核与 Cache 一致性见[第 34 章](../v4-platforms/34-multicore-cache.md)；仪器与证据方法见[第 40 章](../v6-labs-projects/40-lab-method-instruments.md)。

## 社区开源实现

前面列的坑（CCM 不可达、对齐、半区换算、标志清除）在开源代码里都有现成的防御写法。几个可对照的位置：

| 仓库 | 文件 | 看什么 |
| --- | --- | --- |
| [STMicroelectronics/STM32CubeF4](https://github.com/STMicroelectronics/STM32CubeF4) | `Drivers/STM32F4xx_HAL_Driver/Src/stm32f4xx_hal_dma.c` | HAL 的流状态机：`HAL_DMA_Start` 先清 EN 再改 CR 的顺序、`HAL_DMA_PollForUpdate` 的标志等待；对照正文"EN=1 时不能改 CHSEL"的失败分支 |
| [STMicroelectronics/STM32CubeF4](https://github.com/STMicroelectronics/STM32CubeF4) | `Projects/STM32F4-Discovery/Examples/USART/USART_DMA/` | 官方 USART+DMA 收发样例：请求映射、NDTR 按项数计、TC 中断里等 USART TC；对照正文"最后一字节被截"那条 |
| [STMicroelectronics/STM32CubeF4](https://github.com/STMicroelectronics/STM32CubeF4) | `Drivers/CMSIS/Device/ST/STM32F4xx/Include/stm32f407xx.h` | DMA_Stream_TypeDef 结构体与各流基址宏；这里讲的 `0x18` 步进、`+0x88` 流 5 偏移可以直接在里面验证 |
| [STMicroelectronics/STM32CubeF4](https://github.com/STMicroelectronics/STM32CubeF4) | `Drivers/STM32F4xx_HAL_Driver/Src/stm32f4xx_hal_dma_ex.c` + 各例程的缓冲区声明 | 带缓存系列（F7/H7）的传输包装如何用 `SCB_CleanDCache_by_Addr`/`InvalidateDCache_by_Addr` 包住每次搬运；ST [AN4838](https://www.st.com/resource/en/application_note/dm00272913-level-1-cache-on-stm32f7-series-and-stm32h7-series-stmicroelectronics.pdf) 的结论：缓冲区对齐到 32 字节 cache line、必要时显式维护缓存，否则就是这里说的"数据静默丢失" |

F407 本身没有 D-Cache，所以这里的实验踩不到 cache 一致性；但社区在 F7/H7 上踩过之后总结的规则（缓冲区 32 字节对齐、不要把 DMA 缓冲区放进栈上的局部变量、非对齐访问在地址对齐检查里直接 Fault）值得在写代码时就遵守；迁移到第 34 章的双核平台时这些规则立刻生效。另一个社区共识：读标志一律用 `ISR/HISR`，清标志一律写 `IFCR/HIFCR`。libopencm3 的 [dma.c](https://github.com/libopencm3/libopencm3) 对每个标志都有 `DMA_IFCR_Cxx` 专用宏，就是防有人直接写 ISR。

## 离开检查

1. F4 的二级选择是什么？控制器、流、通道各由什么决定？
2. F103 的 USART1_TX/RX 分别在哪条通道？为什么 C8 上没有 DMA2？
3. PAR、M0AR、NDTR 各是什么？为什么 NDTR 不是字节数？
4. DIR 为什么占两位？00/01/10 各是什么方向？为什么内存到内存只有 DMA2 能做？
5. 循环模式下 NDTR 归零后发生什么？为什么 `长度 − NDTR` 不是累计进度？ 给定64项8位环、旧位置60/新位置4，先算模差；若两次服务间隔已超过一个满速整圈，还能断言只新增这些字节吗？
6. HT/TC 各在什么时候响？处理期限怎么算？双缓冲为什么不改变期限？
7. 为什么 CHSEL/CIRC/MINC 必须在 EN=0 时改？HAL 的 Init 与 Start 各落什么？
8. DMA 的 TC 与 USART 的 TC 差在哪？IDLE 为什么不是帧边界？ADC 的 NDTR 为什么按半字算？

<details>
<summary>对照答案</summary>

1. 指“流 × 通道”两级：控制器由请求所属的总线决定（F4 的 USART1 在 APB2，请求归 DMA2），软件用基址与时钟门访问它；流由你写哪一组 `SxCR/NDTR/PAR/M0AR` 决定（8 选 1），通道由该流 `SxCR.CHSEL[2:0]`（bit27:25）在 8 个请求里选。F1 没有 CHSEL，通道就是固定外设槽位。
2. USART1_TX 在 DMA1 通道 4，USART1_RX 在 DMA1 通道 5。C8 是中密度，只有 7 通道的 DMA1；大容量型号才有 5 通道的 DMA2，表 79 不适用于 C8。
3. `PAR/CPAR` 是外设数据寄存器地址，通常固定；`M0AR/CMAR` 是内存缓冲区基址，通常递增；`NDTR/CNDTR` 是剩余数据项数，16 位，每搬一项减 1。NDTR 的单位是配置的数据宽度，不是字节；半字时 64 项是 128 字节。
4. F4 的 `DIR` 是 bit7:6 两位：00 外设到内存、01 内存到外设、10 内存到内存、11 保留。把它当一位，遇到内存到外设（01）就会读错寄存器。F4 的内存到内存只有 DMA2 支持，DMA1 上写 10 不会搬；F1 则用单独的 `CCR.MEM2MEM`（bit14）。
5. 循环模式下NDTR归零后回装、内部地址回卷；位置60→4在64项缓冲中模差为8，但只有能排除整圈丢失才可说新增8。满速115200 8N1一圈理论约5.556ms，间隔已达一圈时不能据位置证明未丢；HT/TC积压/错误须按源码丢弃判据处理。`长度 − NDTR` 只是本圈内已经写了一部分的位置，下一圈从头开始时它会从最大值跳回 0，所以不是累计进度；累计要在每次服务时加增量或在软件里单独计数。
6. HT 在半数搬完时置位，TC 在全部搬完（或双缓冲的一块搬完）时置位。处理期限 = 半区字节数 × 每字节位数 / 波特率，例如 64 字节环在 115200 8N1 下半满约 2.78ms。双缓冲只是把读块与写块分开，不延长一块的填充时间；CPU 超期，整块照样被覆盖。
7. 这些流属性只在 `EN=0` 时可写；`EN=1` 时写入无效，硬件也不会自动停流，必须先清 EN 并等它读回 0。HAL 的 `HAL_DMA_Init` 落 `CR/FCR` 的流属性（含 CHSEL/CIRC/MINC/PSIZE/MSIZE），`HAL_DMA_Start` 先清 DBM，再落 `NDTR/PAR/M0AR` 并最后开 EN；中断版再开 TC/TE/DME，有半传输回调时再加 HT。
8. DMA 的 TC 只说明最后一个字节已写进 USART 的 `DR`，移位寄存器可能还在发；USART 的 TC 才说明停止位已发完，RS-485 切向要等它。IDLE 只说明线空了一个帧时间，不说明对方协议的一包结束。ADC 结果是半字，NDTR 按采样个数计，`NDTR=3` 是还剩 3 个采样（6 字节），不是 3 字节。

</details>


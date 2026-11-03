---
title: S8 DMA：让数据自己搬家
status: done
difficulty: 3
minutes: 30
---

# S8 DMA：让数据自己搬家

> 🎯 串口收 1KB 数据，中断方式要打断 CPU 一千次；DMA 方式：CPU 说一句"把串口数据搬到这个数组，搬完叫我"，然后该干嘛干嘛——搬完一次中断。这就是 DMA 存在的全部理由。

## 本章精髓

1. **DMA 是"第二总线主人"**：它和 CPU 共享总线矩阵（回 [S1](01-arch.md)），谁用谁让路，所以 DMA 传输时 CPU 变慢不是错觉，是仲裁。
2. **三个地址一个长度**：外设地址（固定，PAR）、内存地址（自增，M0AR）、剩余个数（NDTR 倒数）：外设↔内存、内存↔内存三种组合，方向寄存器 `DMA_SxCR.DIR` **占两位**（bit7:6），不是一位。
3. **环形/双缓冲不自动防丢**：环形模式 NDTR 数到 0 自动回装、接着写开头。**CPU 处理得比数据来得慢，旧数据就会被新数据盖上**。双缓冲（乒乓）同理：它只保证"DMA 写和 CPU 读不在同一块"，不保证"CPU 一定来得及"。处理期限是硬约束，不是风格建议。

- **能理解**：为什么方向位是两位；为什么 NDTR 是"个数"不是"字节数"；为什么环形缓冲会静默覆盖。
- **能用**：给 USART1 配上 DMA2 环形接收，用 IDLE 判帧边界，亲手看到 `NDTR` 在倒数。

## 先修

- [S7 USART](07-usart.md)、[S1 总线](01-arch.md)、[S4 中断](04-nvic-exti.md)。

## 先跑起来（10 分钟 quick win）

`code/stm32/03-uart-dma`：烧录后串口助手连发一长串，GDB 里读 `g_rx_bytes` 和 `g_frames` 在动，数据真的在自己搬家。再加一步：主循环打印 `DMA2_S5_NDTR` 的倒数，看它从 64 一路减到 0 又跳回 64。

连上调试器之前，先押个现场：DMA 自己搬家的证据，是那个剩余长度计数器一动不动、减到零就停、还是减到零自己跳回去接着来？盯住它几秒，答案比讲解直观。

## 动画：环形缓冲的水位

环形缓冲像一圈跑道：DMA 是生产者（往跑道里放数据），CPU 是消费者（从跑道里取数据）。NDTR 是"还剩多少空位"。盯住两件事：生产者追上消费者会发生什么（覆盖），以及 NDTR 数到 0 时的"回装"动作。

![DMA 环形缓冲动画](/anim/dma-circular-buffer.svg)

再对照老的乒乓图（已修订）：双缓冲把"写"和"读"分到两块地上，**但 CPU 必须在 DMA 把下一块也填满之前处理完**，超期就覆盖，这不是理论风险，是真实坑。

![DMA 双缓冲乒乓动画](/anim/dma-pingpong.svg)

## 板卡与版本前提

- DMA 有两条控制器：**DMA1 管 APB1 上的外设请求，DMA2 管 APB2 上的外设请求**。USART1 在 APB2 上，所以它的 DMA 请求归 DMA2（这是常见选错点）。
- 请求映射表：RM0090 §10.3.3，Table 42（DMA1）/ Table 43（DMA2）。本轮未取得表正文（见研究记录），工程里的取值以常用映射给出并显式标注"待上板实测确认"。
- F4 的 DMA 有 FIFO（`FCR`），本工程走直接模式（FIFO 关），先讲清主链路再谈 FIFO。

## 小节结构

| 小节 | 内容 | 四件套 |
|---|---|---|
| 一、流与通道 | 二级选择的含义；DMA1/DMA2 分工；映射表去哪查 | 配置 |
| 二、三地址一长度 | PAR/M0AR/NDTR；方向位是两位；宽度与对齐 | 配置 |
| 三、环形 vs 正常 | CIRC 位；NDTR 自动回装；环形不防覆盖 | 代码分析 |
| 四、半满/全满中断 | HTIF/TCIF 的节奏；与 IDLE 判帧配合 | 代码分析 |
| 五、双缓冲（乒乓） | DBM/CT 位；处理期限是硬约束 | 代码分析 |
| 六、总线仲裁 | DMA 与 CPU 抢总线；为什么"变慢"是正常 | 库解析 |
| 七、代码分析 | `03-uart-dma/main.c` 的 `dma2_stream5_rx_init()` 逐位落位 | 代码分析 |
| 八、库解析对照 | HAL Init/Start 逐行对照（hal_dma.c @ 1f6451c）；SPL 一手源码仍缺 | 库解析 |

## 一、流与通道：二级选择是什么

转运全程先收进一张图：请求从外设出发，流×通道选定路径，NDTR 倒数完敲铃收工。

![DMA 转运通路：外设固定、流通道选择、NDTR 计数、内存自增](/arch/dma-paths.png)

F4 的每个 DMA 控制器有 8 条**流（Stream）**，每条流可以接 8 个**通道（Channel）**里的一个。所以一个 DMA 请求要选对两样东西：流 × 通道。

- **DMA1**：APB1 上的外设（USART2/3、I2C、SPI2/3、TIM2~7 等）。
- **DMA2**：APB2 上的外设（USART1/6、SPI1、ADC3、TIM1/8 等）以及 SDIO、DCMI。

**选错控制器是最常见的"配置都对但数据不来"**：时钟开了、引脚对了、流也配了，就是控制器选成了 DMA1。USART1_RX 的常用取值是 **DMA2 Stream5 Channel4**（也可走 Stream2 Channel4）。以 RM0090 Table 43 为准，别背。

## 二、三地址一长度：PAR、M0AR、NDTR

一次 DMA 传输要告诉硬件三件事：

| 寄存器 | 干什么 |
|---|---|
| `PAR` | 外设地址（如 USART1 的 DR），通常**固定** |
| `M0AR` | 内存地址，通常**自增**（`MINC=1`） |
| `NDTR` | 还要搬几个"数据项" |

**方向寄存器 `DMA_SxCR.DIR` 占两位（bit7:6）**，三种组合：00=外设到内存、01=内存到外设、10=内存到内存。这是个"看起来是一位其实是两位"的典型陷阱（原文档写"DIR 是一位"就是错的，CMSIS 头文件里 `DMA_SxCR_DIR_Pos=6`、掩码 `0x3<<6`）。

**NDTR 是"个数"不是"字节数"**：数据宽度 16 位时，NDTR=64 表示 64 个半字 = 128 字节。宽度和长度对不上，差两倍的经典错。

## 三、环形 vs 正常：CIRC 位与自动回装

- **正常模式**：NDTR 数到 0，传输结束，要再启动得重新配置。
- **环形模式**（`CIRC=1`）：NDTR 数到 0 自动回装成初始值，接着写开头，**永远不停**。

环形模式是流式数据的灵魂（串口接收、ADC 连续采样）。但它有个必须直面的性质：**CPU 处理得比数据来得慢，旧数据就会被新数据盖上**。环形缓冲不会等你，它只会绕圈。

所以"消费速度 ≥ 生产速度"不是风格建议，是硬约束。判断方法很简单：跟踪"已读位置"和"DMA 写位置"的差，如果差值在涨，你就在欠债。

## 四、半满/全满中断：HTIF 与 TCIF 的节奏

环形模式下，DMA 会在两个固定点敲铃：

- **HTIF**（半传输）：搬到一半时置位，意思是"前半圈满了，可以开始读了"。
- **TCIF**（全传输）：搬完一圈时置位，意思是"后半圈也满了，再不读就回绕了"。

这两个中断把"处理期限"变成了具体数字：从 HTIF 到 TCIF 之间的时间，就是你处理前半圈的全部预算。处理不完，TCIF 之后数据就被覆盖了。

**清标志要写 `HIFCR`/`LIFCR` 不是 `HISR`/`LISR`**：状态寄存器是只读的，往它写 1 不会清任何东西，这是和中断标志打交道时最容易栽的坑（EXTI 的清 pending 是写 1，DMA 是写另一个寄存器，别混）。

## 五、双缓冲（乒乓）：DBM 与 CT，以及"处理期限"

双缓冲模式（`DBM=1`）给 DMA 两块内存（M0AR/M1AR）：DMA 写 A 时 CPU 读 B，A 满了自动切 B（`CT` 位告诉你当前在写哪块），同时敲一次 TCIF。

它解决的问题是"写和读不打架"，**没解决的问题是"CPU 来不及"**：CPU 必须在 DMA 把下一块也填满之前处理完当前这块。超期了？新数据盖上旧数据，而且是整块整块地丢，比环形模式丢得还整齐。

所以乒乓图里必须画出"CPU 的完成期限"那条线。本章的修订版动画（`dma-pingpong.svg`）补上了这个此前被遗漏的元素。

## 六、总线仲裁：DMA 和 CPU 抢总线

DMA 和 CPU 共享 AHB 总线矩阵（回 [S1](01-arch.md)）。传输密集时 CPU 取指/访存会等 DMA，这不是 bug，是设计如此。理解这一点的实际意义：性能敏感代码不要把大数组放在 DMA 正在写的内存旁边，也别在 DMA 高负载时测代码执行时间然后以为代码变慢了。

另一个边界：**DMA 够不着 CCM**（0x10000000 的 64KB 是 CPU 直连）。把接收数组放 CCM，DMA 写不进去，数据静悄悄丢失。链接脚本默认不放，但如果你手动加了 `__attribute__((section(".ccmram")))`，就要自己扛这个后果。

## 七、代码分析：`03-uart-dma/main.c`

`dma2_stream5_rx_init()` 逐位落位：

- 先开 DMA2 时钟（`RCC_AHB1ENR.DMA2EN`），不开时钟，流配置写了也白写；
- 先关流再配（`EN=0` 时才能改 CHSEL/DIR/CIRC）；
- `PAR = USART1 DR`、`M0AR = 我们的环形数组`、`NDTR = 64`；
- `CIRC=1`、`MINC=1`、`PS=MSIZE=字节`、`CHSEL=4`；
- 最后 `USART1_CR3.DMAR=1` 告诉 USART：RXNE 由 DMA 来取。

`USART1_IRQHandler()` 用 IDLE 判帧边界；`DMA2_Stream5_IRQHandler()` 用 HTIF/TCIF 跟踪水位。两者配合，正好把"帧边界"和"水位"两个问题分开处理。

## 八、库解析对照：SPL/HAL 同名初始化

ST 官方仓库 [`STMicroelectronics/stm32f4xx_hal_driver`](https://github.com/STMicroelectronics/stm32f4xx_hal_driver)（master @ `1f6451c`）的 `HAL_DMA_Init()` 把流属性一次落位、`HAL_DMA_Start()` 把本次传输参数落位。逐条对标本工程：

| 本工程 `dma2_stream5_rx_init()` | HAL 对应（hal_dma.c 行号 @ 1f6451c） | 对照结论 |
|---|---|---|
| 配置前先 `CR=0`、等 EN 落下 | `HAL_DMA_Init()`（L170）先 `__HAL_DMA_DISABLE()` 再轮询 `CR.EN`，等不到就按 `HAL_GetTick` 超时返回 `HAL_TIMEOUT`（L208-227） | 同一硬约束：**EN=1 时改 CHSEL/CIRC 无效**；HAL 多给超时兜底，不会死锁在 while |
| CHSEL/CIRC/MINC/PSIZE 逐位拼 CR | 同函数：把 CHSEL 到 DBM 一整段位一次清掉（L231-237），`Init` 各字段或成一笔写回 CR（L250）；FIFO 的 DMDIS/FTH 另写 FCR（L285） | 你手工拼的那串掩码 = HAL 的 tmp 读-改-写；直接模式就是 FCR 不置 DMDIS |
| 自己写 NDTR/PAR/M0AR | 留到 `HAL_DMA_Start()` 里的 `DMA_SetConfig()`：NDTR（L1157）、PAR/M0AR 按 DIR 定向（L1163-1175） | HAL 把"流属性"与"本次传输参数"分两步；环形重满时 NDTR 由硬件自动重装 |
| `DMA2_Stream5_IRQHandler()` 管 HT/TC、写 IFCR 清标志 | `HAL_DMA_IRQHandler()` 按 HISR 调半传输/完成/错误回调，清标志同样回写 IFCR（如 L708 `IFCR = (HTIF\|TCIF) << StreamIndex`） | 同构：清标志写 HIFCR/LIFCR、绝不碰只读的 HISR/LISR——这条你已经在坑里验证过 |

SPL 的 `DMA_Init()` 做的是同一组落位，但 StdPeriph 未随 ST 官方 GitHub 分发，一手源码仍缺；位定义以 RM0090 为准。

![EN 可改窗口与 HAL 两段式初始化](/anim/dma-hal-en-window.svg)

## 附录：工程完整源码

<<< ../../code/stm32/03-uart-dma/main.c

## 记忆锚点

::: tip 一句话记住
**选定流和通道，外设固定内存自增，NDTR 倒数到零敲个铃；循环搬流水，双缓冲不停机，但都不替你还债；清标志写 HIFCR/LIFCR，别碰 HISR/LISR。**
:::

**延伸**：DMA 环形缓冲与 FreeRTOS 队列（[F4](../rtos/freertos/04-queue.md)）是同构的生产-消费模式；DMA 总线仲裁与地址空间布局（[S1](01-arch.md)）相关。

## 实物实验

- UART DMA 环形接收 + GDB 观察 `g_rx_bytes`/`g_frames`/`g_half_events`/`g_full_events` 的增长节奏；
- 对比实验：同一 1KB 数据，中断版 vs DMA 版的 CPU 占用（用 [S5](05-systick.md) 时基粗测）；
- 翻车实验（选做）：把 `g_rx_buf` 挪到 CCM（链接脚本加 `.ccmram` 段或 `__attribute__`），看 DMA 静默丢数据；
- 翻车实验（选做）：把 IDLE 的处理从"读 SR 再读 DR"改成"只读 SR"，看中断风暴。

## 常见坑

- **控制器选错**：USART1 的 DMA 请求在 DMA2，不在 DMA1，配置都对但数据不来，先查这个；
- **忘开 DMA 时钟**：`RCC_AHB1ENR.DMA2EN` 没开，流配置写了也白写；
- **清标志写错寄存器**：HISR/LISR 是只读状态，清标志要写 HIFCR/LIFCR；
- **流/通道选错**：映射表查错一格，数据永远不来，以 RM0090 Table 42/43 为准，别背；
- **缓冲区放 CCM**：DMA 写不进 CCM，数据静悄悄丢失；
- **NDTR 与数据宽度不匹配**：宽度 16 位时 NDTR 是"个数"不是"字节数"；
- **以为环形/双缓冲不会丢数据**：CPU 处理慢了就覆盖，处理期限是硬约束。

## 短自测

1. `DMA_SxCR.DIR` 占几位？为什么"外设到内存"写成 0 时不要以为它只是一位？
<details><summary>参考答案</summary>占两位（bit7:6），CMSIS 头文件 `DMA_SxCR_DIR_Pos=6`、掩码 `0x3<<6`。三种组合 00/01/10。把它当一位来理解，遇到"内存到外设"（01）时就会以为自己看错了寄存器。</details>

2. USART1_RX 的 DMA 请求在哪个控制器上？为什么容易选错？
<details><summary>参考答案</summary>DMA2（Table 43），Stream5 Channel4（或 Stream2 Channel4）。容易选错是因为直觉上"数字小的外设配数字小的 DMA"，但 F4 的分工是按 APB 总线划的：APB1 外设→DMA1，APB2 外设→DMA2，USART1 在 APB2 上。</details>

3. 环形模式下 NDTR 数到 0 会发生什么？为什么这不等于"数据不会丢"？
<details><summary>参考答案</summary>NDTR 自动回装成初始值，DMA 接着从缓冲区开头写，传输永不停。但如果 CPU 还没来得及读走旧数据，新数据就会把它盖上。环形模式保证"不停"，不保证"不丢"。</details>

4. 清 DMA 中断标志要写哪个寄存器？写 HISR 会发生什么？
<details><summary>参考答案</summary>写 HIFCR（或 LIFCR，取决于流在 0~3 还是 4~7）。HISR/LISR 是只读状态寄存器，往它写 1 什么都不会清，中断会无限进。</details>

<QuizBank chapter="s08-dma" />

## 对照表：本章概念 → 仓库与上游落点

| 概念 | 落点 |
|---|---|
| DIR/CHSEL/CIRC/MINC 位定义 | ST CMSIS `stm32f407xx.h`（DMA_SxCR 段） |
| USART1_RX → DMA2 Stream5 Ch4 | [code/stm32/03-uart-dma/main.c](https://github.com/zhuguang-ZFG/mcu/blob/main/code/stm32/03-uart-dma/main.c)（取值依据与自检步骤见工程 README） |
| HIFCR/LIFCR 清标志 | 同上 `DMA2_Stream5_IRQHandler()` |
| 环形缓冲水位实验 | 同上 `g_rx_buf` + `g_half_events`/`g_full_events` |
| 动画 | [dma-circular-buffer.svg](/anim/dma-circular-buffer.svg)、[dma-pingpong.svg](/anim/dma-pingpong.svg)（已修订）、[dma-hal-en-window.svg](/anim/dma-hal-en-window.svg)（§八对账） |
| HAL 同名初始化逐行对照 | ST 官方仓库 [stm32f4xx_hal_driver](https://github.com/STMicroelectronics/stm32f4xx_hal_driver) @ `1f6451c` `Src/stm32f4xx_hal_dma.c`（见 §八）；SPL 未随官方 GitHub 分发，一手源码仍缺 |

## 你做到了

- "数据自己搬家"从口号变成可调可测的机制；
- UART+DMA 组合成型，ADC 扫描（[S9](09-adc.md)）、DAC 波形（[S10](10-dac.md)）直接复用这套范式；
- "处理期限是硬约束"这件事，从环形缓冲和乒乓图里都亲眼看到了。

现场你看到了：减到零、翻满格、接着搬，周而复始。你盯着的每一秒，CPU 都在干别的。

<div class="achievement">
✅ 下一站：<a href="09-adc.html">S9 ADC</a>：把旋钮/光线变成数字，采样定理眼见为实。
</div>

## 接收边界与验证更新

IDLE 是服务通知，不是应用帧边界。消费者从上次已消费位置读到新的 DMA 写位置；HT/TC 也推动消费。两种边界标志同时积压时丢弃不可信片段并计数，不能从相同位置猜测漏了几圈。ISR 只做有界搬运，主循环非阻塞回显。64 字节环形缓冲在 115200 8N1 下半缓冲约 2.78ms，服务期限必须留余量。宿主行为测试覆盖首次单字节、连续短块、跨圈与积压；这不是无限吞吐或上板实测证明。

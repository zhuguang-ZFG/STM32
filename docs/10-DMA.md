# 10 DMA

> DMA（直接存储器访问）让外设与内存之间的数据自动搬运，CPU 不必逐字节参与，从而把算力留给计算本身。

<p align="center">
  <img src="../assets/animations/dma-circular.svg" width="760" alt="DMA 循环模式：CPU 与 DMA 并行搬运数据">
  <br><sub>▲ 动画：DMA 循环模式搬运 ADC 数据，CPU 同时执行其他任务（作者自绘矢量动画，非实拍）</sub>
</p>

## 📌 学习目标

- [ ] 说清 DMA 控制器结构：F1 的「通道」模型与 F4 的「流（Stream）× 通道（Channel）」模型。
- [ ] 会查请求映射表，把外设请求接到正确的通道/流。
- [ ] 掌握外设↔内存、内存↔内存、普通/循环、FIFO（F4）、双缓冲。
- [ ] 会用传输完成（TC）/半传输（HT）中断实现「边收边处理」。
- [ ] 理解 DMA 与 CPU 的总线争抢，以及 H7/F7 的 Cache 一致性问题。

## 🧠 核心原理

### 1. 控制器结构：F1 的「通道」 vs F4 的「流×通道」

**结论**：F1 一个外设请求固定绑到某条 DMA 通道；F4 先把请求绑到「流」，再用 `CHSEL` 选通道，灵活性更高。

| 项 | STM32F1（RM0008 第 10 章 DMA 控制器） | STM32F4（RM0090 第 9 章 DMA 控制器） |
| --- | --- | --- |
| 控制器 | DMA1（7 通道）、DMA2（5 通道，大容量） | DMA1/DMA2 各 8 个 Stream |
| 请求绑定 | 每通道固定服务若干外设（查映射表） | 每个 Stream 有 8 个 Channel，`SxCR.CHSEL` 选择 |
| 优先级 | 通道间固定优先级 + 软件优先级 | 软件优先级 4 级 + 流编号仲裁 |
| FIFO | 无 | 有（4×32 位），支持突发（burst） |
| 双缓冲 | 无 | 有（Double Buffer Mode） |
| 数据宽度 | 8/16/32 位 | 8/16/32 位 |
| 内存↔内存 | 支持（`CCR.MEM2MEM`） | 支持 |

### 2. 请求映射表（选对通道/流是关键）

**F1 DMA1 请求映射（节选，完整见 RM0008 表 78 / 表 79）**：

| 通道 | 主要请求（节选） |
| --- | --- |
| CH1 | ADC1、TIM2_CH3、TIM4_CH1 |
| CH2 | SPI1_RX、USART3_TX、TIM1_CH1、TIM3_CH3 |
| CH3 | SPI1_TX、USART3_RX、TIM1_CH2、TIM3_CH4 |
| CH4 | SPI2/I2S2_RX、USART1_TX、I2C2_TX、TIM1_CH4 |
| CH5 | SPI2/I2S2_TX、USART1_RX、I2C2_RX、TIM1_UP |
| CH6 | USART2_RX、I2C1_TX、TIM1_CH3、TIM3_CH1 |
| CH7 | USART2_TX、I2C1_RX、TIM2_UP、TIM4_CH2 |

**F4 典型请求（RM0090 表 42 / 表 43）**：

| 外设请求 | 控制器/流 | Channel |
| --- | --- | --- |
| ADC1 | DMA2 Stream0/4 | CH0 |
| SPI1_RX | DMA2 Stream0/2 | CH3 |
| SPI1_TX | DMA2 Stream3/5 | CH3 |
| USART1_TX | DMA2 Stream7 | CH4 |
| USART1_RX | DMA2 Stream5 | CH4 |
| TIM1_CH1 | DMA2 Stream1/5 | CH6 |

> 记忆技巧：**F4 里同一外设 TX/RX 往往用不同 Stream，但同一 Channel**；查表时先定 Stream 再定 Channel。

### 3. 传输方向与工作模式

| 模式/配置 | 关键位 | 说明 |
| --- | --- | --- |
| 外设→内存 | `DIR=0`（F4）/ `CCR.DIR` | ADC/UART_RX 到数组 |
| 内存→外设 | `DIR=1` | 数组到 UART_TX/DAC |
| 内存→内存 | `MEM2MEM=1` | 快速 memcpy（F1 也支持） |
| 普通模式 | `CIRC=0` | 搬完 N 个就停（产生 TC 中断） |
| 循环模式 | `CIRC=1` | 搬完自动回卷，持续刷新 |
| 指针增量 | `PINC`/`MINC` | 内存一般增，外设寄存器不增 |
| 数据宽度 | `PSIZE`/`MSIZE` | 源/目标可不同宽，DMA 自动打包 |
| 优先级 | `PL` | 低 / 中 / 高 / 最高 |
| FIFO / 突发 | `FCR`（F4） | 攒够再走总线，减少占用 |
| 双缓冲 | `DBM`（F4） | 两个内存区交替，处理与搬运并行 |

### 4. 中断

| 中断 | 触发时机 | 用途 |
| --- | --- | --- |
| TC（传输完成） | 搬完全部 N 个 | 数据处理完毕 |
| HT（半传输） | 搬完 N/2 个 | 双缓冲「前半满」处理 |
| TE（传输错误） | 总线错误 | 排查配置 |
| DME / FE（F4） | 直接模式错误 / FIFO 错误 | 高级排查 |

「半传输 + 循环模式」是经典组合：DMA 填前半区时 CPU 处理后半区，反之亦然，实现无缝流式处理。

### 5. 总线争抢与 Cache 一致性

- **总线争抢**：DMA 与 CPU 共享总线矩阵。DMA 搬运时会周期性占用总线，极端情况下拖慢 CPU。F4 的 FIFO/突发模式能把多次小传输合并，减少总线占用。
- **Cache 一致性（H7/F7）**：若内存开了 D-Cache，DMA 直接写内存可能绕过 Cache，导致 CPU 读到旧值；CPU 写内存也可能还停在 Cache 里没落到 RAM，DMA 读到旧值。解决办法：把 DMA 缓冲区放到 **非 Cache 区（MPU 配 Non-Cacheable）**，或搬运前后调用 `SCB_CleanDCache_by_Addr` / `SCB_InvalidateDCache_by_Addr`。**F1/F4 无 D-Cache，不存在此问题。**

<!--APPEND-->
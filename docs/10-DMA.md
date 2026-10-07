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

## 🛠️ 硬件与接线

DMA 是纯片内功能，不需要额外接线；它的价值体现在「驱动外设」上。下表给出典型用例的引脚：

| 开发板 | 用途 | 外设/引脚 | 备注 |
| --- | --- | --- | --- |
| BluePill (F103) | 串口 DMA 发送 | USART1_TX=PA9 → DMA1_CH4 | 接 USB-TTL |
| BluePill | ADC 多通道 | PA0/PA1/PA4 → DMA1_CH1 | 见第 09 章 |
| Nucleo-F411RE | 串口 DMA | USART2_TX=PA2 → DMA1_Stream6_CH4 | ST-Link 虚拟串口 |
| 任意 | 内存→内存搬运 | 无需引脚 | 测吞吐用 |

## 💻 代码实现

**① 串口 DMA 发送（内存→外设，普通模式）**

```c
#include "stm32f1xx_hal.h"

UART_HandleTypeDef huart1;
DMA_HandleTypeDef  hdma_usart1_tx;

static void MX_DMA_Init(void)
{
    __HAL_RCC_DMA1_CLK_ENABLE();
    HAL_NVIC_SetPriority(DMA1_Channel4_IRQn, 0, 0);   /* USART1_TX = DMA1_CH4 */
    HAL_NVIC_EnableIRQ(DMA1_Channel4_IRQn);
}

static void MX_USART1_DMA_Init(void)
{
    /* USART1 基础初始化略（PA9=TX, PA10=RX, 115200-8-N-1） */
    hdma_usart1_tx.Instance                 = DMA1_Channel4;
    hdma_usart1_tx.Init.Direction           = DMA_MEMORY_TO_PERIPH;
    hdma_usart1_tx.Init.PeriphInc           = DMA_PINC_DISABLE;  /* 外设地址不增 */
    hdma_usart1_tx.Init.MemInc              = DMA_MINC_ENABLE;   /* 内存地址递增 */
    hdma_usart1_tx.Init.PeriphDataAlignment = DMA_PDATAALIGN_BYTE;
    hdma_usart1_tx.Init.MemDataAlignment    = DMA_MDATAALIGN_BYTE;
    hdma_usart1_tx.Init.Mode                = DMA_NORMAL;
    hdma_usart1_tx.Init.Priority            = DMA_PRIORITY_LOW;
    HAL_DMA_Init(&hdma_usart1_tx);
    __HAL_LINKDMA(&huart1, hdmatx, hdma_usart1_tx);
}

void Uart_Dma_Send(const uint8_t *buf, uint16_t len)
{
    HAL_UART_Transmit_DMA(&huart1, (uint8_t *)buf, len);   /* 立即返回，后台搬运 */
}
```

**② 内存→内存搬运（MEM2MEM）**

```c
static void DMA_MemCopy(const uint8_t *src, uint8_t *dst, uint16_t len)
{
    DMA_HandleTypeDef hdma = {0};
    hdma.Instance                 = DMA1_Channel1;
    hdma.Init.Direction           = DMA_MEMORY_TO_MEMORY;
    hdma.Init.PeriphInc           = DMA_PINC_ENABLE;
    hdma.Init.MemInc              = DMA_MINC_ENABLE;
    hdma.Init.PeriphDataAlignment = DMA_PDATAALIGN_BYTE;
    hdma.Init.MemDataAlignment    = DMA_MDATAALIGN_BYTE;
    hdma.Init.Mode                = DMA_NORMAL;
    hdma.Init.Priority            = DMA_PRIORITY_HIGH;
    HAL_DMA_Init(&hdma);
    HAL_DMA_Start(&hdma, (uint32_t)src, (uint32_t)dst, len);
    HAL_DMA_PollForTransfer(&hdma, HAL_DMA_FULL_TRANSFER, 100);
    HAL_DMA_DeInit(&hdma);
}
```

**③ 半传输 + 循环（双缓冲思想，F1）**

```c
#define BUF_LEN  64
uint8_t rx_buf[BUF_LEN];

/* DMA 循环模式 + HT/TC 中断；在回调里处理对应半区 */
void HAL_UART_RxHalfCpltCallback(UART_HandleTypeDef *huart)  /* 前半满 */
{
    ProcessData(&rx_buf[0], BUF_LEN / 2);
}
void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart)      /* 后半满 */
{
    ProcessData(&rx_buf[BUF_LEN / 2], BUF_LEN / 2);
}
```

> F4 还可直接用硬件**双缓冲模式**（`DBM`），两个内存指针 `M0AR`/`M1AR` 由硬件自动切换，`CT` 位指示当前使用哪块。

## ⚠️ 常见坑与排查

| 现象 | 原因 | 解决 |
| --- | --- | --- |
| DMA 完全不搬 | 请求映射选错通道/流 | 查映射表；F4 还要对 `CHSEL` |
| 只搬一次就停 | 需要循环却配了普通模式 | 改 `DMA_CIRCULAR` |
| 搬的数据错位/乱序 | 地址未递增或宽度不匹配 | 检查 `MINC`/`PINC` 与 `PSIZE`/`MSIZE` |
| 数据宽度不一致时高字节丢 | 源/目标宽度不同但未对齐 | 统一宽度或用 FIFO |
| 进不了中断 | 没使能 DMA 通道中断 / NVIC 未开 | 使能 TC/HT 中断 + `HAL_NVIC_EnableIRQ` |
| 串口发一半就卡 | 缓冲区是局部变量，函数返回后失效 | 用 `static`/全局缓冲区 |
| F4 上偶发数据错 | FIFO 未配置或突发不匹配 | 设 FIFO 阈值、突发大小 |
| H7 上 DMA 数据不更新 | D-Cache 未维护 | MPU 非 Cache 区或 clean/invalidate |
| 传输错误中断 | 访问了未使能时钟的外设 | 先 `__HAL_RCC_xxx_CLK_ENABLE` |

## 🧪 动手实验

1. **串口 DMA 回环打印**：用 `HAL_UART_Transmit_DMA` 发送一段长字符串，同时主循环翻转 LED。预期：LED 正常闪烁（说明发送不阻塞 CPU），串口数据完整。
2. **内存→内存吞吐测试**：用 `DMA_MemCopy` 搬运 64 KB 数据，用 DWT 计时对比 `memcpy`。预期：DMA 版本 CPU 占用更低（详见第 17 章 DWT 计时）。
3. **UART 空闲中断 + DMA 不定长接收**：DMA 循环收数据，`USART_IDLE` 中断触发时计算已收长度。预期：能稳定接收不定长数据帧，不丢包。
4. **（进阶）双缓冲乒乓**：F4 上开启 `DBM`，两个缓冲区交替，`CT` 位指示当前块，实现零拷贝流式处理。

## 🔗 相关资源

- RM0008《STM32F10xxx 参考手册》第 10 章 DMA 控制器（含请求映射表 78/79）。
- RM0090《STM32F4 参考手册》第 9 章 DMA 控制器（Stream/Channel、FIFO、双缓冲）。
- 应用笔记 AN4031《Using the STM32F2/F4 DMA controller》。
- 本仓库相关章节：第 09 章 ADC+DMA、第 17 章 DWT 计时。
- 配图：`../assets/animations/dma-circular.svg`、`../assets/gif/dma-ring.gif`（均为作者自绘/程序生成）。
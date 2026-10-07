# 06 串口 UART

> English: [UART](en/06-uart.md)

> UART 是最常用的异步串行通信接口，用于打印日志、连接模块与上位机。

<p align="center">
  <img src="../assets/animations/uart-frame.svg" width="760" alt="UART 帧结构逐位时序">
  <br><sub>▲ 动画：UART 帧结构逐位时序（起始位/数据位/校验/停止位，作者自绘矢量图）</sub>
</p>

<!-- video:ch06 -->
<p align="center">
  <img src="../assets/video/ch06-uart.gif" width="640" alt="第 06 章讲解幻灯">
  <br><sub>▲ 本章讲解幻灯：程序生成的 GIF（tools/gen_videos.py，可复现，不是实拍）。旁白与五帧一一对应。</sub>
</p>

**旁白（跟着画面读，大约一分钟）**

1. UART 一帧从起始位的下降沿开始，接着 8 位数据，可选校验，最后停止位。
2. 波特率是双方约好的步点。误差大了，采样点会滑出数据位。
3. 空闲中断加 DMA，适合一帧不定长。ORE 要先读 SR 再读 DR。
4. RS485 换方向要等 TC，不能等 TXE。TXE 只表示数据进了移位寄存器。
5. 口诀：ORE 先 SR 后 DR。自测：115200 8N1 的 8 是什么？
<!-- /video:ch06 -->


## 📌 学习目标
- [ ] 说清 UART 帧格式（起始/数据/校验/停止位）
- [ ] 会算波特率误差，理解 BRR 与 OVER8
- [ ] 掌握阻塞/中断/DMA 三种收发方式取舍
- [ ] 会重定向 printf 并规避半主机模式坑
- [ ] 理解环形缓冲区与 DMA+IDLE 不定长接收

## 🧠 核心原理

**结论先行：UART 是「异步」通信，收发双方只靠约定的波特率对齐，因此帧格式与波特率误差是理解 UART 的两把钥匙。**

### 1. 帧格式详解

一帧 = 1 起始位 + 8/9 数据位（LSB 先发）+ 可选校验位 + 0.5/1/1.5/2 停止位

| 组成 | 取值 | 说明 |
| --- | --- | --- |
| 起始位 | 1 位（低） | 标志一帧开始 |
| 数据位 | 8 或 9 位 | LSB first |
| 校验位 | 无/奇/偶 | 简单检错 |
| 停止位 | 0.5/1/1.5/2 位（高） | 标志一帧结束 |
| 空闲 | 高电平 | 帧间默认 |

<p align="center">
  <img src="../assets/gif/uart-bits.gif" width="640" alt="UART 逐位发送与波特率时间轴">
  <br><sub>▲ 动画：UART 逐位发送（含波特率时间轴，程序生成 GIF）</sub>
</p>

### 2. 波特率与误差

- 波特率 = 每秒传输的位数（bit/s）。常见 9600、115200。
- 每比特时间 = 1/波特率。115200 → 约 8.68µs。
- **误差容限**：收发累计误差需 < 约 ±2%~3%（10 位帧、在中间 3 点采样）。
- 误差公式：`误差 = (实际波特率 − 目标波特率) / 目标波特率 × 100%`

BRR 计算（F1，16 倍过采样）：`USARTDIV = fPCLK / (16 × 波特率)`，BRR = 整数部分 << 4 | 小数部分 × 16

| 目标波特率 | PCLK | USARTDIV | BRR（十六进制） | 误差 |
| --- | --- | --- | --- | --- |
| 9600 | 72MHz | 468.75 | 0x1D4C | 0% |
| 115200 | 72MHz | 39.0625 | 0x271 | 0.16% |
| 115200 | 36MHz | 19.531 | 0x138 | 0.16% |

> F1/F4 支持 OVER8 位（8 倍过采样），可提高高频下分频精度；HAL 里由 `HAL_UART_Init` 自动算 BRR。

### 3. 三种收发方式对比

| 维度 | 阻塞（Polling） | 中断（IT） | DMA |
| --- | --- | --- | --- |
| CPU 占用 | 高（死等） | 中（每字节进中断） | 低（搬完才中断） |
| 吞吐 | 低 | 中 | 高 |
| 代码复杂度 | 低 | 中 | 中高 |
| 适用 | 简单调试 | 少量不定长数据 | 大量/连续数据、不定长收包 |

## 🛠️ 硬件与接线

| 开发板 | 外设 | 引脚 | 备注 |
| --- | --- | --- | --- |
| BluePill | USART1 TX | PA9 | 接 USB-TTL 的 RX |
| BluePill | USART1 RX | PA10 | 接 USB-TTL 的 TX |
| BluePill | GND | GND | 与 USB-TTL 共地 |

> ⚠️ TX/RX 必须交叉接；USB-TTL 电平选 3.3V；USB-TTL 与 ST-Link 不要同时给板子供电冲突。

## 💻 代码实现

阻塞收发：

```c
/* uart_blocking.c —— USART1 回显（阻塞方式） */
#include "stm32f1xx_hal.h"

UART_HandleTypeDef huart1;

void SystemClock_Config(void);

static void uart_init(void)
{
    __HAL_RCC_USART1_CLK_ENABLE();
    __HAL_RCC_GPIOA_CLK_ENABLE();

    /* PA9=TX 复用推挽，PA10=RX 上拉输入 */
    GPIO_InitTypeDef io = {0};
    io.Pin = GPIO_PIN_9; io.Mode = GPIO_MODE_AF_PP; io.Speed = GPIO_SPEED_FREQ_HIGH;
    HAL_GPIO_Init(GPIOA, &io);
    io.Pin = GPIO_PIN_10; io.Mode = GPIO_MODE_INPUT; io.Pull = GPIO_PULLUP;
    HAL_GPIO_Init(GPIOA, &io);

    huart1.Instance          = USART1;
    huart1.Init.BaudRate     = 115200;
    huart1.Init.WordLength   = UART_WORDLENGTH_8B;
    huart1.Init.StopBits     = UART_STOPBITS_1;
    huart1.Init.Parity       = UART_PARITY_NONE;
    huart1.Init.Mode         = UART_MODE_TX_RX;
    huart1.Init.HwFlowCtl    = UART_HWCONTROL_NONE;
    huart1.Init.OverSampling = UART_OVERSAMPLING_16;
    HAL_UART_Init(&huart1);
}

int main(void)
{
    HAL_Init();
    SystemClock_Config();
    uart_init();

    uint8_t ch;
    while (1)
    {
        if (HAL_UART_Receive(&huart1, &ch, 1, 1000) == HAL_OK)
        {
            HAL_UART_Transmit(&huart1, &ch, 1, 1000);   /* 回显 */
        }
    }
}
```

重定向 printf（方式一：fputc/`_write`）：

```c
#include <stdio.h>

/* Keil 用 fputc；GCC 用 _write。二者选一。 */
#ifdef __GNUC__
int _write(int fd, char *ptr, int len)
{
    HAL_UART_Transmit(&huart1, (uint8_t *)ptr, len, HAL_MAX_DELAY);
    return len;
}
#else
int fputc(int ch, FILE *f)
{
    HAL_UART_Transmit(&huart1, (uint8_t *)&ch, 1, HAL_MAX_DELAY);
    return ch;
}
#endif
```

> ⚠️ Keil 需勾选「Use MicroLIB」，否则可能卡在半主机模式（Semihosting）。

方式二（推荐，无半主机依赖）：

```c
#include <stdarg.h>
#include <stdio.h>

void log_printf(const char *fmt, ...)
{
    char buf[128];
    va_list ap;
    va_start(ap, fmt);
    int n = vsnprintf(buf, sizeof(buf), fmt, ap);
    va_end(ap);
    if (n > 0) HAL_UART_Transmit(&huart1, (uint8_t *)buf, (uint16_t)n, HAL_MAX_DELAY);
}
```

DMA + IDLE 不定长接收：

```c
/* 原理：DMA 循环接收填充缓冲区；总线空闲(IDLE)触发中断，
   用 Size 参数得到已收字节数，交给应用解析。 */
#define RX_BUF_SIZE 128
uint8_t rx_buf[RX_BUF_SIZE];
volatile uint16_t rx_len = 0;

void uart_dma_idle_start(void)
{
    HAL_UARTEx_ReceiveToIdle_DMA(&huart1, rx_buf, RX_BUF_SIZE);
    __HAL_DMA_DISABLE_IT(huart1.hdmarx, DMA_IT_HT);   /* 关半传输中断，只用 IDLE 回调 */
}

/* 回调：IDLE 或缓冲区满时触发 */
void HAL_UARTEx_RxEventCallback(UART_HandleTypeDef *huart, uint16_t Size)
{
    if (huart->Instance == USART1)
    {
        rx_len = Size;                                 /* Size = 已接收字节数 */
        HAL_UARTEx_ReceiveToIdle_DMA(&huart1, rx_buf, RX_BUF_SIZE);  /* 重启接收 */
    }
}
```

环形缓冲区思路（中断只入队，主循环出队处理）：

```c
/* 写指针由 ISR 前进，读指针由主循环前进；用计数或留一空位判断满/空 */
static volatile uint16_t head, tail;
static uint8_t ring[256];
/* ISR: ring[head++ & 255] = ch;  主循环: ch = ring[tail++ & 255]; */
```

完整工程见 [`examples/uart-dma-idle/`](../examples/uart-dma-idle/)。

## ⚠️ 常见坑与排查

| 现象 | 原因 | 解决 |
| --- | --- | --- |
| 全是乱码 | 波特率不匹配 | 双方统一波特率；核对晶振频率 |
| 收不到任何数据 | TX/RX 接反 | 交叉接：板 TX→模块 RX |
| 电平不对/损坏 | USB-TTL 用了 5V 电平 | 选 3.3V 电平（或加电平转换） |
| 中文乱码 | 编码/字库不一致 | 统一 UTF-8 或 GBK，或用点阵字库 |
| DMA 收数偶发错乱 | 缓冲区没加 volatile / 未对齐 | 缓冲区加 `volatile`，4 字节对齐 |
| printf 无输出 | Keil 没开 MicroLIB（半主机） | 勾 MicroLIB 或用方式二 log 函数 |
| 高频波特率误码 | 时钟误差大 | 用 OVER8、核对 BRR，降低波特率 |

## 🧪 动手实验

1. **实验一（回显）**：USART1 115200 回显，串口助手发什么收什么。
2. **实验二（printf）**：重定向 printf，每秒打印一次主频与计数器值。
3. **实验三（DMA+IDLE）**：实现不定长接收，串口助手发任意长度字符串，MCU 整帧回显（对照 `uart-bits.gif` 的逐位时序）。

### 4. USART 关键寄存器（F1）

| 寄存器 | 作用 |
| --- | --- |
| SR | 状态寄存器（TXE/RXNE/TC/IDLE/ORE） |
| DR | 数据寄存器 |
| BRR | 波特率寄存器 |
| CR1 | 使能、字长、校验、中断 |
| CR2 | 停止位 |
| CR3 | DMA 使能、流控 |

### 5. 串口 DMA 发送

```c
/* 启动 DMA 发送（TX 端） */
extern uint8_t msg[];            /* 待发数据缓冲区 */
uint16_t msg_len = 10;
HAL_UART_Transmit_DMA(&huart1, msg, msg_len);

/* 发送完成回调 */
void HAL_UART_TxCpltCallback(UART_HandleTypeDef *huart)
{
    if (huart->Instance == USART1)
    {
        /* 可在此启动下一帧或置标志 */
    }
}
```

### 6. 串口助手常见设置

| 设置项 | 常见值 |
| --- | --- |
| 波特率 | 115200 |
| 数据位/停止位/校验 | 8/1/无 |
| 流控 | 无 |
| 发送新行 | 视协议加 CRLF |
| 编码 | 与 MCU 端一致 |

### 7. 溢出错误，和 RS485 的方向脚

**结论**：ORE 置位之后，新字节不再进 DR，直到你**先读 SR 再读 DR**。只读 DR 清不掉 ORE，接收就这么停死。

| 标志 | 含义 | 怎么清 |
| --- | --- | --- |
| ORE | 上一字节还没读，下一字节又到了 | 读 SR，再读 DR |
| FE | 停止位不是 1，通常是波特率错 | 读 SR，再读 DR |
| NE | 采样窗口里电平不干净 | 读 SR，再读 DR |
| PE | 校验位不符 | 读 SR，再读 DR |

RS485 的方向脚（DE）在发送期间为高。`TXE` 只说明数据进了移位寄存器，线上还在发。切回接收必须等 `TC`：

```c
HAL_GPIO_WritePin(DE_PORT, DE_PIN, GPIO_PIN_SET);
HAL_UART_Transmit(&huart1, buf, len, 20);
while (__HAL_UART_GET_FLAG(&huart1, UART_FLAG_TC) == RESET) { }
HAL_GPIO_WritePin(DE_PORT, DE_PIN, GPIO_PIN_RESET);
```

口诀：**ORE 要先 SR 后 DR；RS485 等 TC 再转身。**

自测：

1. 中断里只读了 DR，ORE 还会不会留着？
2. `TXE` 已经是 1，为什么示波器上还看得到最后几位？
3. 8N1 的停止位在图上为什么标 SP，不标 P？

## 🔗 相关资源

- 官方手册：**RM0008** 第 27 章（USART）；**DS5319** USART 引脚复用表
- 上一篇：[05 定时器与PWM](05-定时器与PWM.md)｜下一篇：[07 I2C总线](07-I2C总线.md)
- 相关图：[`assets/animations/uart-frame.svg`](../assets/animations/uart-frame.svg)、[`assets/gif/uart-bits.gif`](../assets/gif/uart-bits.gif)
- 免责声明：本仓库插画均为作者自绘矢量图/程序生成动画，非厂商实拍照片。


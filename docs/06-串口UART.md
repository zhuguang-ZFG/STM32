# 06 串口 UART

> English: [UART](en/06-uart.md)

> UART 是最常用的异步串行通信接口，用于打印日志、连接模块与上位机。

<p align="center">
  <img src="../assets/animations/uart-frame.svg" width="760" alt="UART 帧结构逐位时序">
  <br><sub>▲ 动画：UART 帧结构逐位时序（起始位/数据位/校验/停止位，作者自绘矢量图）</sub>
</p>

<!-- video:ch06 -->
<p align="center">
  <video width="640" controls poster="../assets/video/ch06-uart.png">
    <source src="../assets/video/ch06-uart.mp4" type="video/mp4">
  </video>
  <br><sub>▲ 本章讲解 2.6 分钟。配音是微软 Edge 在线神经语音「晓晓」（zh-CN-XiaoxiaoNeural），经 edge-tts 调用。edge-tts 大部分源码为 LGPLv3，srt_composer.py 为 MIT；声线模型是微软在线服务，不是开放模型。这里提交的是合成后的 MP4，离线可看。重新生成需要联网。画面由脚本和本仓库 SVG 生成，不是实拍。 视频：<a href="../assets/video/ch06-uart.mp4">MP4</a> · 字幕：<a href="../assets/video/ch06-uart.srt">SRT</a>。由 <code>python3 tools/gen_narrated.py --speak</code> 用 ffmpeg 合成。</sub>
</p>

**旁白（与字幕、配音同一份稿）**

1. 115200 8N1 里的 8，是数据位，不是波特率的一部分。一帧通常是起始位、八位数据、没有校验、一位停止。位数说错，对方会一直解出错帧。
2. 波特率是双方约好的速度，由总线时钟分频得到。F103 上 APB 时钟不对，分频再准也会偏。一边 115200，另一边 9600，你只能看到乱码。
3. 溢出错误 ORE 表示你来不及把数据取走。清除时要先读状态寄存器，再读数据寄存器。顺序反了，标志清不掉，后面的字节会全部卡住。
4. 这一帧是仓库画的串口帧，一位一位排开。看图时对照你的初始化：数据位、停止位、校验，要和上位机软件里的设置逐项相同。差一项就乱码。
5. 不定长的一包数据，可以用 DMA 接着收，再用空闲线判断对方说完了。别在中断里一个字节一个字节地阻塞等待。Wokwi 里这套 DMA 目前对不上，接线可以看，收包要上真板。
6. RS485 要控制收发方向。最后一个字节离开移位寄存器，发送完成标志才会起来。标志没起来就转身去收，最后一个字节会被你自己截掉。
7. TX 接对方的 RX，RX 接对方的 TX，地必须连在一起。只接两根信号、不共地，电平没有参考，有时能蒙对，有时完全没字。先共地，再谈波特率。
8. 口诀：ORE 要先读状态再读数据；RS485 等发送完成再转身。这两句能省掉一半「串口偶发丢字」的下午。
9. 实验可以先把 TX 和 RX 短接，确认自己能收到自己发出的字，再接到电脑。短接都收不到，就先别怀疑 USB 转串口线。
10. 合上书，三问。8N1 的 8 是什么？清除溢出时先读哪个寄存器？RS485 为什么要等发送完成才能转换方向？
<!-- /video:ch06 -->
## 原理与边界

这一章的帧只钉在订货号 STM32F103C8T6、封装 LQFP48 上。USART1 在 APB2。内核时钟 72 MHz 时 PCLK2 是 72 MHz，外设基址 `0x40013800`。默认脚是 PA9 = USART1_TX = 第 30 脚，PA10 = USART1_RX = 第 31 脚，来自 [DS5319 Rev 20 图 8](#source-ds5319-usart)。复位后不是 PB6/PB7。重映射要另开 AFIO，不把重映射脚写进正常路径。

这颗料的接收器用 16 倍波特率时钟采样。1 位停止位在第 8、第 9、第 10 个采样点上表决。起始位的确认序列是第 3、5、7 点和第 8、9、10 点，写在 [RM0008 27.3.3](#source-rm0008-usart)。数据位用中间那三个点。

16 倍时 `USARTDIV = fPCLK / (16 × 波特率)`。72 MHz、115200：`72e6 / (16 × 115200) = 39.0625`，小数 `0.0625 × 16 = 1`，BRR = `0x271`，`72e6 / (16 × 39.0625) = 115200`，分频误差是 0。`USART_BRR` 偏移 `0x08`，低 4 位是小数。这格从附录 D 照抄。72 MHz 那一行的误差是 0%。大约 0.16% 留在 36 MHz、BRR `0x138` 那一行，那是 APB1 上的 USART2，不是这只 USART1。丢掉小数、只用尾数 39，也会得到大约 0.16%，但那不是写进 `0x271` 的结果。不编辑附录 A 或附录 D。

8 倍过采样在这颗 F103 上作废。`USART_CR1` 偏移 `0x0C`，位 31:14 保留，没有 OVER8。F103 只有 16 倍；8 倍要换到带 OVER8 的系列。这里不编一个 8 倍的 BRR，也不追加 `rm0090-usart-over8`。

115200、8N1 时一位约 8.68 µs，一帧 10 位约 86.8 µs。RM0008 里空闲线是一整帧的高电平。一次 IDLE 表示线已经空了大约一个帧时间，不表示对方协议里的长度字段到了。循环 DMA 的 `Size` 仍是写位置，不是这一次的增量。

停止位在预期的采样点上不是高，硬件置 `USART_SR.FE`。无效数据仍然进 `USART_DR`。清除是先读 SR 再读 DR。只读 DR 清不掉。中断是否到来还要看 RXNE 或 CR3 的 EIE。单字节通信时 FE 本身不单独成为唯一的中断源。不要写成「FE 一定进中断服务」。

## 关键插图

<p align="center">
  <img src="../assets/diagrams/sample-06-uart-frame.svg" width="760" alt="停止位采到 0 就是帧错误，0x271 在 72 MHz、16 倍下误差是 0">
  <br><sub>▲ 自绘。STM32F103C8T6，LQFP48 第 30 脚 PA9 = USART1_TX，第 31 脚 PA10 = USART1_RX。帧是 0xA5，LSB 先发。一位约 8.68 µs，10 位约 86.8 µs。BRR `0x271`，39.0625，16 倍，误差 0。寄存器偏移 USART_SR 0x00、USART_DR 0x04、USART_BRR 0x08、USART_CR1 0x0C。正常路径：停止位第 8、9、10 点为 1，FE 不置位。失败路径：这三点为 0，FE 置位，数据仍在 DR，清除是先读 SR 再读 DR。旁注：这颗 F103 的 CR1 位 31:14 保留，没有 OVER8，图上不算 8 倍 BRR。脚位来自 [DS5319 Rev 20 图 8](#source-ds5319-usart)。采样与 BRR 来自 [RM0008 Rev 21 第 27 章](#source-rm0008-usart)。</sub>
</p>

<p align="center">
  <img src="../assets/gif/uart-idle.gif" width="640" alt="一帧结束后 RX 保持高，满一个帧时间后标出 IDLE 和 86.8 微秒">
  <br><sub>▲ 网页和公众号辅图。只标空闲线和 86.8 µs。印刷以静态主图为准。帧错误的三点采样不在这条 GIF 上。</sub>
</p>

`uart-frame.svg` 和 `uart-bits.gif` 留在原来的帧格式小节，标成辅图。PDF 不播放 GIF 时，起始位、停止位、第 8、9、10 个采样点和 FE 路径都在静态主图上。

## 时序或状态

| 阶段 | 线上电平 | 0xA5 的位 | 第 8、9、10 点 | FE | 时间 | BRR |
| --- | --- | --- | --- | --- | --- | --- |
| 空闲 | 高 | — | — | 0 | — | — |
| 起始位 | 0 | — | 起始位另用第 3、5、7 点确认 | 0 | 约 8.68 µs | — |
| 数据，LSB 先 | 1 0 1 0 0 1 0 1 | 0xA5 | 数据位用中间三点 | 0 | 8 位 | — |
| 正常停止位 | 1 | 停止位 | 表决为 1 | 0 | 约 8.68 µs | USART1，72 MHz，`0x271`，误差 0% |
| 失败停止位 | 0 | 停止位 | 三点为 0 | 1 | 约 8.68 µs | 清除是读 SR 再读 DR |
| 一帧合计 | — | 10 位 | — | — | 约 86.8 µs | 39.0625 |
| USART2 对照 | — | — | — | — | — | APB1，36 MHz，`0x138`，约 0.16%。不是这只 USART1 |
| IDLE | 停止位之后保持高 | — | — | 0 | 满一个帧时间，约 86.8 µs | 不是协议帧结束 |

不把 0.16% 放回 `0x271` 那一格。出处是 [RM0008 第 27.3.3 节](#source-rm0008-usart)。

## 坑与出处卡

| 现象 | 原因 | 处理 | 出处 | 该来源允许支持的主张 |
| --- | --- | --- | --- | --- |
| 表上 USART1 的 `0x271` 被说成已经偏了 | 那一格把小数位丢掉了，或者把 USART2 的行抄过来了 | 72 MHz、16 倍、带上小数位，误差是 0% | [RM0008 BRR](#source-rm0008-usart) | `0x271` 的分频结果是 115200。这一格的误差是 0% |
| 停止位错了仍读到一个字节，接着卡死 | FE 置位时数据仍进 DR，只读 DR 不清标志 | 先读 SR 再读 DR 清 FE | [RM0008 27.3.3](#source-rm0008-usart) | FE 置位时数据仍进 DR；只读 DR 不清标志 |
| 把 IDLE 当成对方一包已经结束 | 空闲线只表示线路空闲 | 用长度或协议，不用 86.8 µs 当帧界 | [RM0008](#source-rm0008-usart) | IDLE 是线路空闲满一个帧时间 |
| F103 上打开 OVER8 来修高频误码 | 这颗料没有该位 | 先核对 72 MHz 和 `0x271`，误差是 0% | [RM0008 CR1](#source-rm0008-usart) | CR1 位 31:14 保留 |
| 循环 DMA 把 `Size` 当成这一次新增的字节数 | `Size` 是写位置 | 自己保存上次位置再相减，注意绕回 | [STM32CubeF4 v1.28.3](#source-stm32cube-f4) | 只支持 v1.28.3 那个例程里 Size 是写位置。不是 F103 的引脚证明 |
| 应用一次把 DMA 缓冲区当完整线性帧读完 | 缓冲区不是一条拍平的帧 | 读到 DMA 写位置为止 | [MaJerle USART DMA](#source-majerle-uart) | 改写后的环位置边界。不支持新的波特率或脚位 |
| 半传输和 IDLE 好像总会成对出现 | 帖子里的时序没有升格成手册数字 | 不把帖子里的时序写成手册数字；空闲长度仍用 86.8 µs 那一格 | [ST 社区帖](#source-st-uart-idle) | 经验线索，未升格为规范。不支持新的寄存器值 |

## 📌 学习目标
- [ ] 说清 UART 帧格式（起始/数据/校验/停止位）
- [ ] 会算这颗 F103 上 16 倍过采样的 BRR。这颗料没有 OVER8
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

| USART | 目标波特率 | 总线 | PCLK | USARTDIV | BRR（十六进制） | 误差 |
| --- | --- | --- | --- | --- | --- | --- |
| USART1 | 9600 | APB2 | 72 MHz | 468.75 | 0x1D4C | 0% |
| USART1 | 115200 | APB2 | 72 MHz | 39.0625 | 0x271 | 0% |
| USART2 | 115200 | APB1 | 36 MHz | 19.531 | 0x138 | 约 0.16% |

> 这颗 STM32F103C8T6 的 USART_CR1 位 31:14 保留，没有 OVER8。8 倍过采样要换到带这个位的系列。F103 上不要为了高频误码去开 OVER8，先核对 72 MHz 和 BRR `0x271`。`HAL_UART_Init` 仍按 16 倍算 BRR。

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
/* 循环 DMA 时，回调里的 Size 是写位置，不是这一次新增的字节数。
   下面把接收重新启动。位置差写在「坑与出处卡」。 */
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
        rx_len = Size;                                 /* 写位置。循环缓冲要和上次位置相减，并处理绕回 */
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
- 📱 手机阅读版：[第 06 章 · 串口UART（公众号图文）](https://mp.weixin.qq.com/s/_hR9mWbVJJp8_d05jBnA9w)
- 相关图：[`assets/animations/uart-frame.svg`](../assets/animations/uart-frame.svg)、[`assets/gif/uart-bits.gif`](../assets/gif/uart-bits.gif)
- 免责声明：本仓库插画均为作者自绘矢量图/程序生成动画，非厂商实拍照片。


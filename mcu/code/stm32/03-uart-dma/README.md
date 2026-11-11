# 03-uart-dma：串口收发的两级缓冲，和"可写 ≠ 发完"

配套章节：[S7 USART](../../docs/stm32/07-usart.md)、[S8 DMA](../../docs/stm32/08-dma.md)

## 这个工程讲清三件事

1. **波特率是算出来的，不是填出来的。** 默认 16 倍过采样（OVER8=0）时 `baud = f_PCLK2 / BRR`。
   时钟一变波特率就跟着变，所以 `BRR` 由回读出来的 PCLK2 计算。
   反例：1MHz（PLL 参考频率那一档）下 `BRR = 9`，实际 111111，误差 −3.549%，通信就已经不可靠。
2. **接收有两级缓冲**：串口移位寄存器/FIFO，DMA 搬进环形数组。
   DMA 不理解"帧"，它只理解"搬够 N 个字节"；帧边界靠 USART 的 **IDLE** 标志判断
   （总线空闲一个帧时间就置位）。
3. **TXE ≠ TC**。TXE 只说明数据寄存器空出来了，TC 才说明停止位已经发完。
   在 RS-485 这类需要切方向的场合，漏掉 TC 就会把最后一位切掉。

## 硬件前提

| 项 | 说明 |
|---|---|
| 串口 | USB-TTL 接 PA9(TX)/PA10(RX)，共地，3.3V 电平 |
| 波特率 | 115200 8N1，8 位字长，1 停止位，无校验，无流控 |
| 其他 | 无 |

引脚依据 DS8626 Table 9：PA9 = USART1_TX (AF7)、PA10 = USART1_RX (AF7)。

## ⚠ DMA stream/channel 的取值

```c
#define USART1_RX_STREAM   5U
#define USART1_RX_CHANNEL  4U
```

权威来源是 RM0090 的 **DMA2 request mapping** 表（Rev 18 Table 43）——
USART1 挂在 APB2 上，它的 DMA 请求归 DMA2 管；常见取值 RX = DMA2 Stream5 Channel4、
TX = DMA2 Stream6 Channel4。本次实施未能取得该表正文（st.com 返回 HTTP 567，
各镜像的文本层只覆盖到约 229 页，而该表在 307/308 页），因此这里不把它当作
"板上事实"，而是集中成两个宏，方便你按自己的资料核对后修改。
详见任务研究记录 `.trellis/tasks/10-06-stm32-depth-animations/research/baseline-and-sources.md`。

## 构建

PATH 需要 `arm-none-eabi-gcc`、`mingw32-make`，以及 Git 的 `usr\bin`。

```bash
make
make flash
make clean
```

## 上板自检

1. 烧录后串口应立刻打印 `uart-dma ready`；
2. 电脑上发任意字符串 → 板子原样回显；
3. GDB 里对照两个计数：

   | 变量 | 含义 |
   |---|---|
   | `g_rx_bytes` | DMA 搬进环形数组的字节总数 |
   | `g_frames` | IDLE 判出的帧数 |
   | `g_overruns` | ORE/FE/NE 错误计数，应为 0 |
   | `g_half_events` / `g_full_events` | 半缓冲 / 整缓冲中断次数 |
   | `g_brr` | 由 PCLK2 算出的 BRR，应接近 139（HSI 16MHz 下 16000000/115200=138.9→138/139） |
   | `g_pclk2` | 回读到的 APB2 时钟 |

4. 若 `g_rx_bytes` 一直是 0 而回显也没有 → stream/channel 配错，回查 RM0090 映射表改上面两个宏。

## 失败排查

| 现象 | 多半是 |
|---|---|
| 完全没有输出 | 没共地；PA9/PA10 接反；USB-TTL 电平不是 3.3V |
| 输出是乱码 | 波特率算错（`g_brr` 与实际 PCLK2 不匹配）；或对端用了 7 数据位/2 停止位 |
| 收不到数据 | `USART_CR3.DMAR` 没开；或 PA10 没配成 AF7 复用；或 GPIOA 时钟没开 |
| 数据量对但分帧不对 | IDLE 标志没清干净（必须"读 SR 再读 DR"），或主机发送间隔小于一个帧时间 |
| 偶发丢字节 | `g_overruns` 不为 0：CPU 处理不及时，或没有环形缓冲 |
## 接收边界与验证更新

IDLE 是服务通知，不是应用帧边界。消费者从上次已消费位置读到新的 DMA 写位置；HT/TC 也推动消费。两种边界标志同时积压时丢弃不可信片段并计数，不能从相同位置猜测漏了几圈。ISR 只做有界搬运，主循环非阻塞回显。64 字节环形缓冲在 115200 8N1 下半缓冲约 2.78ms，服务期限必须留余量。宿主行为测试覆盖首次单字节、连续短块、跨圈与积压；这不是无限吞吐或上板实测证明。

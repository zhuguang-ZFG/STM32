---
title: S7 USART：让芯片开口说话
status: done
difficulty: 3
minutes: 30
---

# S7 USART：让芯片开口说话

> 🎯 串口是单片机的"嘴巴"和"耳朵"。它不讲道理，只认节拍：双方约定好波特率，然后一位一位地数。你发 0x41，对方收到 0x41，前提是两边数拍子的速度不能差太多——差 2% 还能凑合，差 3.549%（1MHz 喂 115200 正是这个数）就开始丢帧，差 10% 就只剩乱码。

## 本章精髓

1. **一帧的结构是固定的**：空闲高 → 起始位（拉低）→ 8 个数据位（LSB 先发）→ 停止位（拉高）。在逻辑分析仪上认出一帧，就是认出这个节奏。
2. **波特率是算出来的，不是填出来的**：默认 16 倍过采样（OVER8=0）时 `baud = f_PCLK / BRR`。时钟一变，波特率跟着变，这就是"改了时钟树、串口就乱码"的原因。
3. **TXE ≠ TC**：TXE 只说"数据寄存器空了，可以塞下一个"；TC 才说"停止位已经发出去"。在 RS-485 这类需要切方向的场合，漏掉 TC 会把最后一位切掉。

- **能理解**：为什么 1MHz 不能当 115200 的时钟；为什么 IDLE 标志必须"读 SR 再读 DR"才清；为什么 DMA 不理解"帧"。
- **能用**：寄存器级把 USART1 跑起来回显；用逻辑分析仪在 PA9 上认出 0x41 的每一位。

## 先修

- [S2 时钟](02-rcc-clock.md)（PCLK2 怎么来）、[S3 GPIO](03-gpio.md)（复用 AF7）、[S4 中断](04-nvic-exti.md)。

## 先跑起来（10 分钟 quick win）

`code/stm32/03-uart-dma`：烧录后 USB-TTL 接 PA9/PA10，115200 8N1，电脑上发任意字符串，板子原样回显，这就是最小可跑通的串口。

连串口之前，先押个结局：如果波特率算错了一点点，回显会变成原样一句、一堆乱码、还是彻底安静？押完把 BRR 故意拨错一格，眼睛当场收账。

## 动画：一帧的解剖

0x41 是怎么一位一位飞出去的：起始位把线拉低、然后 LSB 先发、八位走完、停止位拉高。对照 0x55（0101 0101）看会更清楚：同一波特率下，0x41 和 0x55 的波形完全不同，但帧结构一模一样。

![USART 帧动画](/anim/uart-frame.svg)

## 板卡与版本前提

- USART1 在 APB2 上，PA9=TX、PA10=RX（AF7，DS8626 Table 9）。8 位字长、1 停止位、无校验、无流控是默认也最常用的配置。
- 波特率误差的可接受范围不是"经验上 ±2%"这么含糊：8N1 一帧最危险的采样点是最后一个数据位的中点（8.5 位时刻），倒推总容差 ≈5.882%，再由收发两端对半分成每端 2.941%（推导见第二节）。这也是为什么不能用 1MHz 喂 115200（实测误差 -3.549%，见下一节那张表）。

## 小节结构

| 小节 | 内容 | 四件套 |
|---|---|---|
| 一、一帧的结构 | 起始/数据/停止/LSB；0x41 与 0x55 对照 | 引脚 |
| 二、波特率 | `baud = PCLK/BRR`；误差表；1MHz 反例 | 配置 |
| 三、发送 | TXE/TC 两级；"可写"不等于"发完" | 代码分析 |
| 四、接收 | RXNE、IDLE、错误位；DMA 环形 + IDLE 帧边界 | 代码分析 |
| 五、printf 与日志 | retarget 与代价 | 库解析 |
| 六、代码分析 | `03-uart-dma/main.c` 逐段对表 | 代码分析 |
| 七、库解析对照 | HAL Init/Transmit 逐行对照（hal_uart.c @ 1f6451c）；SPL 一手源码仍缺 | 库解析 |

## 一、一帧的结构：起始、数据、停止

空闲时线是**高电平**。一帧从这里开始：

1. **起始位**：拉低一位的时间，意思是"注意，数据来了"。
2. **数据位**：8 位（可配 7 或 9），**LSB 先发**，0x41 = `0100 0001`，上线顺序是 `1,0,0,0,0,0,1,0`。
3. **停止位**：拉高一位（可配 0.5/1/1.5/2），意思是"我说完了"。

用逻辑分析仪看 0x41 和 0x55（`0101 0101`）：数据位波形完全不同，但起始/停止的节奏一模一样。**帧结构是协议的骨架，数据只是填进去的肉。**

![UART 一帧：空闲高、起始位拉低、8 个数据位低位在前、停止位拉高；波特率由 PCLK/BRR 决定](/figures/stm32-07-usart.svg)

## 二、波特率：`baud = PCLK / BRR`

默认 **16 倍过采样**（OVER8=0）时：

```
BRR = f_PCLK / baud
baud = f_PCLK / BRR
```

> **【注】** OVER8=1 时是 8 倍过采样，公式变成 `baud = 2 × f_PCLK / BRR`：同样的 BRR，波特率翻倍。高速率场合用得上，代价是每个位只采 8 次，抗噪变差。本工程保持默认 16 倍。

所以 BRR 必须由**实际的** PCLK 算出来，不能写死。PCLK 变了，BRR 就得跟着变，改了时钟树、串口就乱码，根子在这里。

![BRR 的来历：PCLK 与 baud 相除后拆成整数 Mantissa 与小数 Fraction 两个字段](/figures/stm32-07-usart-brr.svg)

> **【注 2】** 上面那两条公式看起来把 BRR 当纯整数分母，而 RM0090 把它拆成 `DIV_Mantissa[15:4]` + `DIV_Fraction[3:0]`，写法是 `USARTDIV = Mantissa + Fraction/16`、`baud = f_PCLK/(16 × USARTDIV)`。把 16 乘进去：`16 × USARTDIV = 16 × Mantissa + Fraction`，右边正好就是寄存器里那 16 位，**整个寄存器的值就是分母**。所以固件直接写一个整数（139 = 0x8B → Mantissa 8、Fraction 11），不需要先算小数再拼字段；寄存器的 1 位粒度已经是硬件能给的最细分频，不存在"小数位还没用上"。

误差表（`code/stm32/03-uart-dma/probe.sh` 第 1 步本机实跑打印的那八行，逐行由 `BAUD_FROM_PCLK` / `PCLK_OF_BRR` 这两个固件宏算出；第 2 步再拿这张表与正文逐行 diff，改一个数就红）：

| PCLK2 | 目标波特率 | BRR | 实际波特率 | 误差 |
|---|---|---|---|---|
| 1 MHz | 115200 | 9 | 111111 | -3.549% |
| 8 MHz | 115200 | 69 | 115942 | +0.644% |
| 16 MHz | 9600 | 1667 | 9598 | -0.020% |
| 16 MHz | 115200 | 139 | 115108 | -0.080% |
| 16 MHz | 460800 | 35 | 457143 | -0.794% |
| 16 MHz | 921600 | 17 | 941176 | +2.124% |
| 42 MHz | 115200 | 365 | 115068 | -0.114% |
| 84 MHz | 115200 | 729 | 115226 | +0.023% |

第三列不是查表来的，是 `BRR = round(PCLK2 / baud)` 那一次四舍五入的结果；第四列再拿这个整数除回去。所以**误差的上界就是半个量化格**：16 MHz / 115200 那一格宽 822.2 baud（0.714%），半格 0.357%。探针在 1..65535 里穷举过最优 BRR，这八档的最优解与固件的四舍五入**完全一致**，这个误差不是实现瑕疵，是整数 BRR 的物理下限。

量化误差本身往往很小，但**误差是沿整帧累积的**：接收端在每个位的中点重采样，最危险的时刻是最后一个数据位的中点，8N1 帧里就是 8.5 位时刻。从这里倒推预算：`|ε| × 8.5 < 0.5` → 总容差 ≈ **5.882%**，还要由收发两端的时钟**对半分**，这才是"±2% 经验值"的完整来历。帧越长（8E2 有 12 位，预算收到 4.762%）、时钟源越差（HSI ±1%），预算越紧。

<BaudCalc />

反例：**1MHz 的时钟下配 115200**，BRR = 1e6/115200 ≈ 8.68 → 取 9 → 实际 111111.1，误差 **-3.549%**，单这一项就吃掉 5.882% 预算的六成，剩下每端只有 1.166%，刚够 HSI 自己的 ±1%，一点余量都不剩；两端再各带一点时钟源容差，通信必然不可靠。这就是原文档里"115200×16=1843200，1MHz 不满足该文同句给定条件"这句话的根源：**1MHz 是 PLL 的 VCO 参考输入，不是能直接喂 USART 的外设时钟**（回 [S2](02-rcc-clock.md)）。

同理，16 MHz 下想要 **921600**：OVER8=0 只能取 BRR=17，实际 941176，量化误差 **+2.124%** 单项就超过每端 2.941% 的一半额度：要么按注里说的改 OVER8=1（等价于把时钟当 32 MHz 算，BRR=35，误差回到 -0.794%），要么把 PCLK2 提上去。这一格是"高速率不是想要就要"的硬边界。

## 三、发送：TXE 与 TC 是两级

- `USART_SR.TXE`（bit7）：**数据寄存器 DR 空了**，可以塞下一个字节。此时数据可能还在移位寄存器里往外蹦。
- `USART_SR.TC`（bit6）：**整个字节（含停止位）已经发完**。只有 TC 置位，才能安全地切 RS-485 方向、断电、进低功耗。

发送函数的正确姿势：

```c
/* 塞数据只看 TXE，全部塞完再等 TC */
while ((USART1_SR & USART_SR_TXE) == 0) { }
USART1_DR = byte;
/* ... 循环 ... */
while ((USART1_SR & USART_SR_TC) == 0) { }   /* 最后必须等这个 */
```

漏掉最后的 TC 等待，在 RS-485 上会切方向太早，把最后一位切掉一半，对方收到的是"半个字节"，帧校验直接挂。

![TXE vs TC：数据寄存器空 ≠ 移位寄存器发完](/anim/usart-txe-tc.svg)

## 四、接收：RXNE、IDLE 与 DMA 环形缓冲

接收有两个问题：**字节级**和**帧级**。

- **字节级**：`USART_SR.RXNE`（bit5）置位 = 收到一个字节，读 `DR` 取走。
- **帧级**：数据是一串一串来的，怎么知道"这一串到哪儿结束"？答案是 **IDLE**（bit4）：总线空闲一个帧时间，IDLE 就置位。

IDLE 标志有个坑：**它不是靠写 0 清的，必须"先读 SR、再读 DR"这个序列才清**。少一步，IDLE 一直挂着，中断风暴。
（旧答案："IDLE 标志必须先读 SR 再读 DR 才清，否则中断风暴"）

配 DMA 之后的经典结构：

```
串口移位寄存器 → (RXNE 触发 DMA) → 环形数组（我们的内存）
                ↑ IDLE 置位时，DMA 指针位置就是帧边界
```

DMA 不理解"帧"，它只理解"搬够 N 个字节"；帧边界由 IDLE 标志告诉你。`03-uart-dma` 用 DMA2 Stream5 环形接收，每收到一帧就 IDLE 中断一次、把这一帧回显。

**接收错误**：`ORE`（溢出：CPU/DMA 没来得及取，新字节盖掉旧字节）、`FE`（帧错误：没等到停止位）、`NE`（噪声）。这三个位也必须"读 SR 再读 DR"清。

## 五、printf 与日志：retarget 的代价

`printf` 好用，但它是 newlib 的，默认往 stdout 写。嵌入式上没有 stdout，需要 retarget：实现 `_write()` 把字节送进 USART。代价不小：newlib 的 printf 会把几百字节到几 KB 的代码拉进来，还会用到堆。

本仓库的工程**不用 printf**，用一个手写的 `uart_write_blocking()`，几十字节，行为完全可控。等你真的需要格式化输出时，再决定要不要为 printf 付这个代价。

## 六、代码分析：`03-uart-dma/main.c`

- `clocks_read()`：从 CFGR 反推 HCLK/PCLK2，BRR 由真实 PCLK2 算出来；
- `usart1_init()`：UE/TE/RE/IDLEIE 四个位，BRR = PCLK2/115200；
- `uart_write_blocking()`：塞数据看 TXE，收尾等 TC；
- `dma2_stream5_rx_init()`：环形、8 位、内存递增、DMA2 Stream5 Channel4（取值依据见工程 README 的说明，为什么不是 DMA1 见 [S8](08-dma.md) 的总线分工）；
- `USART1_IRQHandler()`：错误位计数、IDLE 判帧边界、回显。

## 七、库解析对照：SPL/HAL 同名初始化

ST 官方仓库 [`STMicroelectronics/stm32f4xx_hal_driver`](https://github.com/STMicroelectronics/stm32f4xx_hal_driver)（master @ `1f6451c`）的 `HAL_UART_Init()` / `HAL_UART_Transmit()` 做的是同一组寄存器落位，逐条对标本工程：

| 本工程 | HAL 对应（hal_uart.c 行号 @ 1f6451c） | 对照结论 |
|---|---|---|
| `usart1_init()`：开时钟、配引脚、写 CR1/BRR | `HAL_UART_Init()`（L357）先调 `HAL_UART_MspInit()`（时钟与引脚归板级回调），关掉外设再 `UART_SetConfig()`（L3731）一次落 CR1/CR2/CR3——**OVER8 位同批写入**（L3752-3756） | 你的初始化顺序 = MspInit + SetConfig 两段，HAL 只是把它们拆进两层回调 |
| `baud = PCLK/BRR` 手算 | `UART_SetConfig()` 尾部按过采样选 `UART_BRR_SAMPLING8/16` 宏算 BRR（L3787/L3791），最后 `__HAL_UART_ENABLE()`（L417） | 同一个公式：OVER8 只是换分频宏，HAL 不多写一个寄存器 |
| `uart_write_blocking()`：TXE 塞字节、收尾等 TC | `HAL_UART_Transmit()`：每字节前 `UART_WaitOnFlagUntilTimeout(TXE)`（L1172），结束再等一次 TC（L1191），全程 `HAL_GetTick` 计时超时 | 你总结的"TXE 只管塞、TC 才管完"就是 HAL 的实现；死等被超时兜底 |
| `USART1_IRQHandler()`：IDLE 判帧、错误位计数 | `HAL_UART_IRQHandler()`（L2355）按"**SR 标志 & 对应 CR 使能位**"的组合分发处理（如 L2599 TXE 要 TXEIE 开着才走发送分支） | 结构同构：先取标志与使能的交集再分支，不是见标志就处理 |

SPL 的 `USART_Init()` 计算 BRR 用 `DIV_Mantissa/DIV_Fraction` 一对字段，公式同构；但 StdPeriph 未随 ST 官方 GitHub 分发，一手源码仍缺，位定义以 RM0090/CMSIS 为准。

![HAL UART 初始化与手写落位的对账图](/anim/uart-hal-init-path.svg)

## 附录：工程完整源码

<<< ../../code/stm32/03-uart-dma/main.c

## 记忆锚点

::: tip 一句话记住
**起始拉低、数据八位、低位先发、停止拉高；波特率跟着 PCLK 走；TXE 只管塞、TC 才管完；IDLE 读 SR 再读 DR。**
:::

**延伸**：UART+DMA 环形缓冲是经典生产-消费模式，与 FreeRTOS 队列（[F4](../rtos/freertos/04-queue.md)）同构；DMA 原理见 [S8](08-dma.md)。

## 实物实验

- [E02 逻辑分析仪看串口](../lab/e02-logic-uart.md)：抓 0x41 与 0x55 各一帧，逐位对表；
- 对比实验：改 BRR 偏 5%，看什么时候开始丢帧，亲手感受误差的边界；
- DMA 环形缓冲：连发一长串（超过 64 字节），看 `g_half_events` / `g_full_events` 增长，理解"半满/全满中断"的节奏。

## 常见坑

- **TXE/TC 不分**：RS-485 切方向太早，最后一位被切掉；
- **IDLE 不清**：少了"读 SR 再读 DR"，中断风暴；
- **BRR 写死**：时钟树一改，串口乱码；
- **用 1MHz 配 115200**：BRR 只能取 9，实际 111111，误差 -3.549%，单这一项就吃掉 5.882% 总预算的六成；
- **ORE 溢出**：中断/DMA 处理不及时，新字节盖掉旧字节，数据悄悄丢。

## 短自测

1. 0x41 在串口线上的位序是什么样的？为什么 LSB 先发？
<details><summary>参考答案</summary>空闲高 → 起始位低 → 1,0,0,0,0,0,1,0（LSB 先发）→ 停止位高。LSB 先发是 UART 的协议规定，双方约定俗成；逻辑分析仪解码时按这个顺序读就对了。</details>

2. PCLK2 = 16MHz，要 115200，BRR 是多少？误差多少？
<details><summary>参考答案</summary>BRR = 16000000/115200 ≈ 138.9 → 取 139。实际波特率 = 16000000/139 ≈ 115108，误差 -0.08%，完全可用。</details>

3. TXE 和 TC 的区别是什么？什么时候必须等 TC？
<details><summary>参考答案</summary>TXE = 数据寄存器空了可以塞下一个；TC = 移位寄存器也空了、停止位已经发完。RS-485 切方向、断电、进低功耗之前必须等 TC，否则最后一位被切掉。</details>

4. IDLE 标志怎么清？为什么？
<details><summary>参考答案</summary>读 SR 再读 DR。硬件规定了这个清除序列：光写 SR 没用，不把 DR 里的字节取走，IDLE 就一直挂着，中断会一直触发。</details>

<QuizBank chapter="s07-usart" />

## 对照表：本章概念 → 仓库与上游落点

| 概念 | 落点 |
|---|---|
| TXE/TC/RXNE/IDLE/ORE 位定义 | ST CMSIS `stm32f407xx.h`（USART_SR 段） |
| `baud = PCLK/BRR` 实算 | [code/stm32/03-uart-dma/main.c](https://github.com/zhuguang-ZFG/STM32/blob/main/mcu/code/stm32/03-uart-dma/main.c) `usart1_init()` |
| IDLE 判帧 + DMA 环形 | 同上 `USART1_IRQHandler()` 与 `dma2_stream5_rx_init()` |
| PA9/PA10 AF7 | DS8626 Rev 9 Table 9 |
| 第二节那张误差表的八行 | `BAUD_FROM_PCLK` / `PCLK_OF_BRR`（`main.c`）→ `probe.c` §1/§6 → `probe.sh` 第 2c 步与正文逐行 diff，改一个数就红 |
| 33 条位号、25 个寄存器地址 | CMSIS `stm32f407xx.h` + `core_cm4.h`（本站 `.trellis/ref/cmsis/`）；`probe.c` §2/§11 现挖，`probe.sh` 第 2a/2b 步逐条 diff |
| 机身里的 magic 乘法、`/1000`、BRR 落寄存器、DMA 那六个字、`-O0` 与 `-O2` 的形状差 | `probe.sh` 第 3 步（`arm-none-eabi-gcc -O2/-O0 -c main.c` + `objdump -d`） |
| 动画 | [uart-frame.svg](/anim/uart-frame.svg)、[usart-txe-tc.svg](/anim/usart-txe-tc.svg)、[uart-hal-init-path.svg](/anim/uart-hal-init-path.svg)（§七对账） |
| HAL 同名初始化逐行对照 | ST 官方仓库 [stm32f4xx_hal_driver](https://github.com/STMicroelectronics/stm32f4xx_hal_driver) @ `1f6451c` `Src/stm32f4xx_hal_uart.c`（见 §七）；SPL 未随官方 GitHub 分发，一手源码仍缺 |

## 你做到了

- 串口从"黑盒外设"变成"节拍+寄存器"的组合；
- 亲手算过一次波特率，知道误差怎么来、多少算多；
- IDLE + DMA 环形的组合拳，是后面所有"不定长接收"的模板。

乱码的账现在能算了：波特率差上百分之三点几，采样点滑出最后一位的中点，一帧错一位满屏皆花。

<div class="achievement">
✅ 下一站：<a href="08-dma.html">S8 DMA</a>：数据自己搬家，CPU 只等敲门声。
</div>

## 接收边界与验证更新

IDLE 是服务通知，不是应用帧边界。消费者从上次已消费位置读到新的 DMA 写位置；HT/TC 也推动消费。两种边界标志同时积压时丢弃不可信片段并计数，不能从相同位置猜测漏了几圈。ISR 只做有界搬运，主循环非阻塞回显。64 字节环形缓冲在 115200 8N1 下半缓冲约 2.78ms，服务期限必须留余量。宿主行为测试覆盖首次单字节、连续短块、跨圈与积压；这不是无限吞吐或上板实测证明。

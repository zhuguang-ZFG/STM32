---
title: G3 USART 增强点：从命名到数量的差异清单
status: done
difficulty: 2
minutes: 30
---

# G3 USART 增强点：从命名到数量的差异清单

> 🎯 STM32F407 有 6 个串口（USART1/2/3/6 + UART4/5），GD32F4xx 有 **8 个**（USART0/1/2/5 + UART3/4/6/7）——多出来的不只是数量，寄存器命名也从 CR1/CR2/CR3 换成了 CTL0/CTL1/CTL2。本章把差异逐项点名，迁移时按表翻译。

## 本章精髓

1. 数量差异：GD32F4xx 有 **8 个串口**（USART0/1/2/5 + UART3/4/6/7），比 STM32F407 的 6 个多两个；命名从"USART1~6 + UART4/5"变成"USART0~5 + UART3/4/6/7"，**编号从 0 起不是从 1 起**。
2. 寄存器命名大换血：STM32 的 CR1/CR2/CR3 → GD32 的 **CTL0/CTL1/CTL2**；BRR → **BAUD**；GTPR → **GP**；SR/DR → **STAT/DATA**：功能等价，名字全变。
3. GD32 USART 有"不连续时钟"（CTL1.CLEN）与"智能卡"（CTL2.SCEN/NKEN）模式的增强（位级事实已按 `gd32f4xx_usart.h` V3.3.3 核验，见第四节）。

- **能理解**：为什么 GD32 从 0 起编号（与中断号对齐，USART0_IRQn=37）；为什么命名从 CR 改 CTL（GD32 库的统一风格，所有外设控制寄存器都叫 CTL）。
- **能用**：拿到 GD32 USART 工程，把 STM32 肌肉记忆的 CR1/CR2/CR3 翻译成 CTL0/1/2，把 BRR 翻译成 BAUD。

## 先修

- [G1 RCU 时钟树](01-rcu-clock.md)、[S7 USART](../stm32/07-usart.md)（对照锚点）。

## 先跑起来（10 分钟 quick win）

用 `gd32f4xx.h` 查 USART0 基址（APB1 + 0x4400），对照 [S7](../stm32/07-usart.md) 的 USART1 基址（APB2 + 0x1000）：**总线不同、基址不同、但偏移布局神似**。

先押排门牌：串口数量 8 对 6，GD32 独有的是哪三个名字？这八路各自挂哪条总线，有没有跟大部队分开走的？押完看中断号地图。

## 小节结构

| 小节 | 内容 | 四件套 |
|---|---|---|
| 数量与编号 | 8 个串口 vs 6 个，0 起编号 | 配置 |
| 寄存器命名 | CR1/2/3→CTL0/1/2，BRR→BAUD 全表 | 库解析 |
| 中断号地图 | 8 个 USART_IRQn 与总线归属 | 配置 |
| 增强点 | GD32 独有功能（已核验） | 库解析 |
| 库函数对照 | gd32 USART 配置 API 与 SPL 对照 | 库解析 |

## 一、数量与编号：8 个串口，0 起编号

先讲清楚"为什么从 0 起"，后面那张表就不用背了。

GD32F4 是 ARM Cortex-M4F 内核（和 STM32F4 同门），中断控制器仍是 NVIC。它没有另起一套向量表：**中断号布局沿用 STM32F4**，改的只是外设命名——第一个串口从 USART1 叫成了 USART0，中断号 37 原地不动。

打个比方：小区的门牌号没换（37 号还是 37 号），只是楼名从"1 号楼"改叫"0 号楼"。

迁移时的实用推论只有一条：**别按编号找对应**。看到 GD32 的 USART0，先看它在哪条总线（APB2）、中断号多少（37），再回 STM32 表里找"同总线 + 同中断号"的那个，答案自然是 USART1。

GD32F4xx 串口全家福（中断号已在 `gd32f4xx.h` 核对）：

| 串口 | 类型 | 总线 | 中断号 | STM32 对应 |
|---|---|---|---|---|
| USART0 | 同步/异步 | APB2 | 37 | USART1（APB2） |
| USART1 | 同步/异步 | APB1 | 38 | USART2（APB1） |
| USART2 | 同步/异步 | APB1 | 39 | USART3（APB1） |
| USART5 | 同步/异步 | APB2 | 71 | **STM32F407 无** |
| UART3 | 异步 | APB1 | 52 | UART4（APB1） |
| UART4 | 异步 | APB1 | 53 | UART5（APB1） |
| UART6 | 异步 | APB1 | 82 | **STM32F407 无** |
| UART7 | 异步 | APB1 | 83 | **STM32F407 无** |

三条差异一眼看出：

1. **编号从 0 起**：GD32 的 USART0 对应 STM32 的 USART1，迁移时别按编号找对应。
2. **多 3 个串口**：USART5（APB2）、UART6/7（APB1）是 GD32 独有，STM32F407 没有。
3. **USART5 挂 APB2**：与其他 USART 的 APB1 归属不同，时钟使能位在 RCU_APB2EN，别找错。

> **【注】** GD32 的 USART0/1/2/5 是"同步/异步"（带 SCK 引脚，可做 SPI 主从），UART3/4/6/7 是"纯异步"（无 SCK），对应 STM32 的 USART vs UART 区分。

## 二、寄存器命名：CR1/2/3 → CTL0/1/2

改名的动机不是"换个花样"，而是 GD32 全系统一的命名纪律：**每一个外设的控制寄存器都叫 CTL，状态寄存器都叫 STAT，数据寄存器都叫 DATA**。

把它想成物业公司换门禁面板：以前每栋楼一个牌子（CR1/CR2/CR3、SR、DR），电工上门要背三套；现在全小区统一面板（CTL0/CTL1/CTL2、STAT、DATA），新来的电工看一次就懂。

代价是"肌肉记忆失效"：你写惯的 `USART_CR1` 在 GD32 里编译不过，得换成 `USART_CTL0`。收益是"一个规律管八个串口"：`USART_CTL0`、`UART_CTL0` 写法一致，换外设不用重新记名字。

改名纪律落到 USART 是七条偏移轨：上排是 STM32 的名字，下排是 GD32 的名字，同一列就是同一个偏移。

![USART 寄存器改名对照：CR1/CR2/CR3/BRR/GTPR/SR/DR 与 CTL0/CTL1/CTL2/BAUD/GP/STAT/DATA 逐偏移对齐](/arch/usart-rename-map.png)

GD32 库的统一命名风格：所有外设的控制寄存器都叫 **CTL**（Control），STM32 叫 **CR**（Control Register）。USART 的三组控制寄存器命名映射：

| STM32 | GD32 | 偏移 | 功能 |
|---|---|---|---|
| CR1 | **CTL0** | 0x00 | 使能/帧格式/中断使能 |
| CR2 | **CTL1** | 0x04 | 时钟/停止位/地址 |
| CR3 | **CTL2** | 0x08 | 流控/DMA/智能卡 |
| BRR | **BAUD** | 0x0C | 波特率分频 |
| GTPR | **GP** | 0x10 | 保护时间/预分频 |
| SR | **STAT** | 0x14 | 状态标志 |
| DR | **DATA** | 0x18 | 数据读写 |

偏移布局与 STM32 **完全一致**（0x00~0x18 逐行对齐）：功能等价，只是名字换了。迁移纪律：**按偏移不按名字**，0x00 永远是主控制寄存器，0x0C 永远是波特率。

位级命名差异（已知方向，具体位号以 `gd32f4xx_usart.h` 为准）：

| STM32 CR1 位 | GD32 CTL0 位（方向） | 说明 |
|---|---|---|
| UE（bit13） | **UEN**（使能） | 名字加 EN 后缀 |
| RE/TE | **REN/TEN** | 同上加 EN |
| RXNE/TXE | **RBNE/TBE** | 接收缓冲/发送缓冲，命名更直白 |
| TC | **TC**（不变） | 传输完成 |
| IDLE | **IDLE**（不变） | 空闲 |

GD32 的位命名风格有两条规律。**动作位加 EN 后缀**（UEN/REN/TEN）；**状态位用 B（Buffer）替代 X**（RBNE vs RXNE = Receive Buffer Not Empty vs Receive Not Empty）。

## 三、中断号地图：8 个 IRQn

GD32F4xx 的 USART 中断号已在 `gd32f4xx.h` 的 IRQn_Type 枚举核对（非连续编号）：

```c
USART0_IRQn = 37,    // APB2，对应 STM32 USART1
USART1_IRQn = 38,    // APB1，对应 STM32 USART2
USART2_IRQn = 39,    // APB1，对应 STM32 USART3
UART3_IRQn  = 52,    // APB1，对应 STM32 UART4
UART4_IRQn  = 53,    // APB1，对应 STM32 UART5
USART5_IRQn = 71,    // APB2，GD32 独有
UART6_IRQn  = 82,    // APB1，GD32 独有
UART7_IRQn  = 83,    // APB1，GD32 独有
```

中断号不连续：39→52 跳了 13，53→71 跳了 18。GD32 的中断向量表布局与 STM32 不同。迁移时**不要按 STM32 的中断号找 GD32 的**，按上表对照。

## 四、增强点：GD32 独有功能（已按 V3.3.3 头文件核验）

GD32F4xx 的 USART 相比 STM32F407 的增强点，位级事实已对照 `gd32f4xx_usart.h`（V3.3.3，本地 .trellis/ref/gd32/fw）核验：

1. **USART5 的存在**：多一个同步/异步串口（APB2），STM32F407 没有对应（gd32f4xx_usart.h:47），可用于额外的高速同步通信。
2. **UART6/7 的存在**：多两个异步串口（APB1，gd32f4xx_usart.h:45-46），多串口产品（如 8 通道数据采集）的直接收益。
3. **不连续时钟（CLEN）**：`USART_CTL1_CLEN` BIT(8)（gd32f4xx_usart.h:104）：CTL1 的 CK 长度位，控制 8 位帧出 7/8 个 CK 脉冲（`USART_CLEN_NONE`）还是 8/9 个（`USART_CLEN_EN`，:290-292）。STM32F407 无此位。
4. **智能卡增强（SCEN/NKEN）**：`USART_CTL2_SCEN` BIT(5) 开智能卡模式（:117）、`USART_CTL2_NKEN` BIT(4) 选 NACK 使能（:116），都在 CTL2，对应 STM32 CR3 的位置但字段不同。
5. **IrDA 模式（IREN）**：`USART_CTL2_IREN` BIT(1)（:113），与 STM32 的 CR3.IREN 同语义。

> **【注】** 以上位级事实已对照 `gd32f4xx_usart.h`（V3.3.3）逐一核验并标注行号；与用户手册的语义一致性（如时序细节）仍以上板实测为准。

## 五、库函数对照：GD32 与 SPL

GD32 标准外设库的 USART API 与 STM32 SPL 的对照（函数名风格不同但参数对应）：

| SPL（STM32） | GD32 库 | 说明 |
|---|---|---|
| `USART_Init(USART1, &cfg)` | `usart_init(USART0, baud, word_len, stop, parity, mode)` | GD32 拆成参数不传结构体 |
| `USART_Cmd(USART1, ENABLE)` | `usart_enable(USART0)` | 名字加 enable/disable |
| `USART_SendData(USART1, b)` | `usart_data_transmit(USART0, b)` | 动词更明确 |
| `USART_ReceiveData(USART1)` | `usart_data_receive(USART0)` | 同上 |
| `USART_GetFlagStatus(USART1, TXE)` | `usart_flag_get(USART0, USART_FLAG_TBE)` | TBE 替代 TXE |
| `USART_ITConfig(USART1, RXNE, ENABLE)` | `usart_interrupt_enable(USART0, USART_INT_RBNE)` | RBNE 替代 RXNE |

GD32 库的风格：**函数名小写下划线**（`usart_init` vs `USART_Init`）；**参数不打包结构体**（直接传 baud/word_len 等）；**宏名加 FLAG/INT 前缀**。读库姿势照旧（[S15 SPL 解剖](../stm32/15-spl-anatomy.md)）：拿到 `usart_init` 先问"它动了 CTL0/1/2 的哪几位"，按偏移对答案。

## 记忆锚点

::: tip 一句话记住
**8 个串口 0 起编号，CTL0/1/2 替代 CR1/2/3；BAUD 替代 BRR，STAT/DATA 替代 SR/DR：偏移不变名字变，迁移按偏移不按名。**
:::

**延伸**：STM32 USART 对照见 [S7](../stm32/07-usart.md)；USART 帧波形动画见 [S7 动画](/anim/uart-frame.svg)；GD32 外设编号差异总览见 [G4](04-periph-diff.md)。

## 实物实验

- 在 `code/gd32/01-rcu-clock` 工程上加 USART0 初始化（APB2 时钟使能），串口打印"GD32 USART0"，验证基址与命名翻译。

## 常见坑

- **按 STM32 编号找 GD32 串口**：USART1 在 GD32 是 USART0，编号差 1，找错基址全乱。
- **USART5 时钟在 APB2**：其他 USART 在 APB1，USART5 单独在 APB2，时钟使能位找错不工作。
- **中断号不连续**：39→52 跳 13，53→71 跳 18，按 STM32 中断号填 GD32 向量表会越界。
- **位名肌肉记忆**：RXNE→RBNE、TXE→TBE：写 `USART_FLAG_RXNE` 在 GD32 编不过，要用 `USART_FLAG_RBNE`。
- **多出来的串口未查手册**：USART5/UART6/7 是 GD32 独有，引脚分配以 GD32 datasheet 为准，别套 STM32 引脚表。

## 短自测

1. GD32F4xx 有几个串口？STM32F407 有几个？多出来的是哪几个？
<details><summary>看答案</summary>GD32F4xx 有 8 个（USART0/1/2/5 + UART3/4/6/7），STM32F407 有 6 个（USART1/2/3/6 + UART4/5）。GD32 多 3 个：USART5（APB2 同步/异步）、UART6（APB1 异步）、UART7（APB1 异步）。</details>

2. STM32 的 CR1/CR2/CR3/BRR 在 GD32 里叫什么？偏移布局是否一致？
<details><summary>看答案</summary>GD32 叫 CTL0/CTL1/CTL2/BAUD。偏移布局完全一致：0x00 主控制、0x04 时钟/停止位、0x08 流控/DMA、0x0C 波特率。迁移纪律：按偏移不按名字，0x00 永远是主控制寄存器。</details>

3. GD32 USART0 的中断号是多少？对应 STM32 的哪个串口？为什么总线不同？
<details><summary>看答案</summary>GD32 USART0_IRQn=37，对应 STM32 的 USART1（STM32 USART1 也在 APB2）。两者都挂 APB2（高速总线），因为 USART0/1 在 GD32 是同步/异步串口需要较高时钟，APB2 比 APB1 快。</details>

4. RXNE 和 TXE 在 GD32 里叫什么？这种命名变化的规律是什么？
<details><summary>看答案</summary>GD32 叫 RBNE（Receive Buffer Not Empty）和 TBE（Transmit Buffer Empty）。规律：状态位用 B（Buffer）替代 X（STM32 的 RXNE = Receive Not Empty，GD32 加了 Buffer 更直白）；动作位加 EN 后缀（UEN/REN/TEN）。迁移时把 STM32 的 RXNE/TXE 宏名换成 RBNE/TBE。</details>

5. GD32 库的 `usart_init` 与 STM32 SPL 的 `USART_Init` 在 API 风格上有什么差异？
<details><summary>看答案</summary>STM32 SPL 用结构体打包（USART_InitTypeDef 含 baud/word_len/stop/parity/mode 传给 USART_Init），GD32 库直接传参数（usart_init(USART0, baud, word_len, stop, parity, mode) 不打包）。命名风格：STM32 驼峰大写（USART_Init），GD32 小写下划线（usart_init）。功能等价，代码风格不同。</details>

## 对照表：本章概念 → 仓库与上游落点

| 概念 | 落点 |
|---|---|
| 8 个串口中断号 | `gd32f4xx.h` IRQn_Type 枚举（USART0_IRQn=37 等） |
| 寄存器命名映射 | `gd32f4xx_usart.h`（V3.3.3，本地已缓存核验）；偏移对照 STM32 RM0090 |
| USART0 基址 | `gd32f4xx.h` USART_BASE = APB1 + 0x4400 |
| 库函数对照 | GD32 V3.3.3 库 `usart_init`/`usart_enable` vs STM32 SPL `USART_Init`/`USART_Cmd` |
| STM32 对照锚点 | [S7 USART](../stm32/07-usart.md) 全章 |
| 增强点（CLEN/SCEN/NKEN/IREN） | `gd32f4xx_usart.h`（V3.3.3 已核验：CLEN=CTL1:8、SCEN=CTL2:5、NKEN=CTL2:4、IREN=CTL2:1） |

## 你做到了

- GD32 USART 从"换个名字的 STM32"变成"有明确差异清单的独立芯片"；
- 迁移时按偏移不按名字的纪律到手，这套方法在 G4 外设差异上直接复用。

门牌对上：GD32 独有 USART5、UART6、UART7；USART0 与 USART5 挂 APB2，其余六路 APB1，找对应按总线加中断号，别按编号，起跑线挪到 0 为的也是跟中断号对齐。CR1/CR2/CR3 改姓 CTL0/CTL1/CTL2，BRR 换 BAUD、SR/DR 换 STAT/DATA，偏移布局神似，迁移按偏移不按名字。

<div class="achievement">
✅ 下一站：<a href="04-periph-diff.html">G4 GD32 外设差异</a>：USBHS/EXMC/CAN 逐项过堂，看"有没有、一不一样"。
</div>

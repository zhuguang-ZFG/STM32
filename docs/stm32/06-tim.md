---
title: S6 定时器 TIM：一器多用的瑞士军刀
status: done
difficulty: 3
minutes: 25
---

# S6 定时器 TIM：一器多用的瑞士军刀

> 🎯 TIM 是 STM32 最全能的外设：本质只是一个"会数数的计数器"，但配上预分频、自动重载、比较/捕获单元，它就能延时、发 PWM、测频率、读编码器——一招"计数"，十般变化。

## 本章精髓

1. **时基三件套**：PSC（预分频，先把时钟降下来）、CNT（计数器本体）、ARR（数到几归零）：更新频率 = TIMclk / (PSC+1) / (ARR+1)，两个"+1"是新手必考题。TIMclk 本身还有一条隐藏规则：**APB 分频 ≠ 1 时定时器时钟 ×2**（APB1=/4 时 TIM 是 84MHz 不是 42MHz），本章用 `02-tim-pwm` 实测出来。
2. **PWM 的本质是"比较"**：CNT 与 CCR 比较，小了输出高、大了输出低（极性可配）：占空比 = CCR/(ARR+1)，改 CCR 就改占空比，频率纹丝不动。这条"占空比和频率分家"的性质，是本章实验的核心观察点。
3. **输入捕获是"拍照"**：引脚边沿一到，硬件把当时的 CNT 拍进 CCR：两次拍照的差值×计数周期 = 脉宽/频率，全程不用 CPU 掐表。回绕必须满足计数位宽和无丢边沿前提。

- **能理解**：为什么改 CCR 不改频率；为什么 APB 分频 ≠ 1 时定时器时钟 ×2；无符号模差在哪些前提下才正确。
- **能用**：手算任意目标的 PSC/ARR；把 PWM 输出和捕获接成自测闭环，用硬件验证硬件。

## 先修

- [S2 时钟](02-rcc-clock.md)（APB 倍频）、[S3 GPIO](03-gpio.md)（复用 AF）、[S4 中断](04-nvic-exti.md)。

## 先跑起来（10 分钟 quick win）

TIM3 CH1 输出 1kHz/50% PWM 到 **PA6**（AF2，见 DS8626 Table 9），红灯立刻"半亮"，这就是 PWM 调光的直观体感。

> 原文档曾写"TIM3 CH1 输出到 PF6，若复用表无 TIM 通道则换脚"。这不对：F407 的 **Port F 上根本没有 TIM3 通道**（PF6/PF7/PF8 在 AF3 上分别是 TIM10_CH1 / TIM11_CH1 / TIM13_CH1，见 DS8626 Table 9 的 Port F 段）。正确的做法不是"换个脚试试"，而是回查复用表：TIM3_CH1 在 PA6、PB4、PC6 上都有（AF2）。本工程选 PA6。

先别急着烧，三个答案里押一个：想让 PWM 变亮变暗，该动的是 PSC、ARR、还是 CCR？动错一个，频率跟着跑；动对一个，节拍纹丝不动只有亮度变。

## 动画：计数器怎么变成 PWM

CNT 往上涨、ARR 给它设了终点、CCR 在中间设了一个"开关点"，三段分立，改 CCR 只动开关点。看下面这张图时盯住三件事：CNT 的斜率（频率由 PSC/ARR 定）、OC 输出的高低翻转点（由 CCR 定）、以及"改 CCR 后频率纹丝不动"。

![TIM PWM 计数器动画](/anim/tim-pwm-counter.svg)

## 板卡与版本前提

- 定时器归属：TIM2–5/12–14 在 APB1，TIM1/8–11 在 APB2（RM0090 §2/§7）。APB1=/4 时 PCLK1=42MHz，TIM 时钟 ×2 = 84MHz。
- 引脚-通道映射以 **F407ZGT6 datasheet 复用表**为准。本工程固定用 PA6（TIM3_CH1，AF2）与 PA7（TIM3_CH2，AF2）。
- 板载 RGB 红灯在 PF6（共阳、低电平点亮），与 TIM3 不冲突，这正是我们不用 PF6 的原因。

## 小节结构

| 小节 | 内容 | 四件套 |
|---|---|---|
| 一、时基三件套 | PSC/CNT/ARR 与更新事件；频率公式推导 | 配置 |
| 二、定时中断 | 1s 定时翻转 LED；与 SysTick 分工对比 | 代码分析 |
| 三、PWM 输出 | OC 模式/极性/CCR；ARR 与分辨率的取舍 | 配置 |
| 四、呼吸灯 | 渐变改 CCR；伽马校正的直觉版 | 引脚 |
| 五、输入捕获 | 边沿拍照测频率；独立 32 位时基与失效检测 | 代码分析 |
| 六、编码器接口 | TI1/TI2 正交解码的硬件实现（概念+场景） | 配置 |
| 七、代码分析 | `02-tim-pwm/main.c` 逐段对表 | 代码分析 |
| 八、库解析对照 | HAL 三函数逐行对照（hal_tim.c @ 1f6451c）；SPL 一手源码仍缺 | 库解析 |

## 一、时基三件套：PSC、CNT、ARR

更新事件频率的公式：**f = TIMclk / (PSC+1) / (ARR+1)**。两个"+1"来自硬件的分频语义：PSC 是"每多少个时钟打一拍"，ARR 是"数到几归零"，两个都从 0 开始数。

例子：TIM3 时钟 84MHz，要 1kHz 更新：

- 选 PSC = 83 → 计数时钟 84MHz/84 = 1MHz；
- 选 ARR = 999 → 1000 拍一个周期 → 1kHz。

为什么是 83 和 999 而不是 84 和 1000？因为硬件数的是"0 到 PSC"和"0 到 ARR"，写进去的数比你想的少 1。**漏掉这个"+1"，1kHz 会配成 999Hz 或 1001Hz**，示波器上才发现。

## 二、定时中断：1 秒翻灯，和 SysTick 分工

定时中断是最简单的用法：配置 PSC/ARR，开 `DIER.UIE`，在 `TIMx_IRQHandler` 里清 `SR.UIF` 再翻灯。

和 SysTick 的分工：**SysTick 归内核**，管"毫秒级心跳"（延时、RTOS 节拍）；**TIM 归外设**，管"这件事要精确到多少个时钟"。SysTick 不要用来做 PWM，TIM 不要用来做系统延时。两个都能用，但放错位置会很别扭。

## 三、PWM 输出：OC 模式、极性、CCR

PWM 模式 1（`CCMR1.OC1M = 110`）的规则：CNT < CCR 时输出有效电平，否则无效电平。配上极性位（`CCER.CCxP`）就得到"高电平有效"或"低电平有效"两种 PWM。

三个关键位，一个都不能少：

| 位 | 干什么 |
|---|---|
| `CCMR1.OC1M = 110` | 选 PWM 模式 1 |
| `CCMR1.OC1PE = 1` | CCR 预装载：改 CCR 在**下一个周期整点**生效，不会在半中间突然变 |
| `CCER.CCxE = 1` | 输出使能：不开这个，引脚永远没有波形——新手第一大坑 |

占空比 = CCR/(ARR+1)。ARR=999 时 CCR=500 是 50%，CCR=250 是 25%。**分辨率由 ARR 决定**：ARR 越大，占空比可调的最小步进越小，代价是频率上限变低（f = 计数时钟/(ARR+1)）。

## 四、呼吸灯：只改 CCR 的渐变

呼吸灯 = 周期性把 CCR 从 0 扫到 ARR 再扫回来。本工程用三角形扫描（每 20ms 一步，约 4 秒一个来回）。**关键观察：扫 CCR 的过程中频率始终是 1kHz**，变的只是占空比。这就是"占空比和频率分家"的直观演示。

想更像人眼感受的"呼吸"，把线性扫描换成对数/伽马曲线：数字上非线性，视觉上才线性。

## 五、输入捕获：独立时基与回绕前提

PWM 的 TIM3 每 1000 tick 重载，不能拿它测量自己的完整周期：每次同相位边沿都可能得到同一个 CNT，差值为零。现在 PA6 输出，跳线接 **PA0（TIM2_CH1 AF1）**，TIM2 以 1MHz 自由计数、ARR=0xffffffff，捕获 ISR 及时读取时间戳。

只有计数模数与运算位宽一致、间隔小于一整圈且没有丢边沿时，uint32_t 无符号相减才正确处理回绕。ARR=999 时 last=990、now=10，真实差为 20；uint32_t 相减却得 4294966316。即使改为模 1000，也不能区分经过了零圈还是一整圈。

本例接受 100us–500ms 的边沿间隔；首次捕获建立基准，过捕获后重新建立基准，无信号超过 1 秒清除频率。TIM2 的约 4294 秒硬件回绕不是本例的测频承诺。主循环只读取受短临界区保护的快照，不每 20ms 才消费 1kHz 捕获。

共享判定函数在 code/common/behavior/capture.h，宿主测试覆盖跨 0xffffffff 回绕、首拍、丢边沿、超量程与超时。板上测频仍待实测。

![输入捕获：边沿拍照 → CNT 差值 → 脉宽/频率](/anim/tim-input-capture.svg)

## 六、编码器接口：正交解码的硬件状态机

TIM 的编码器接口模式（`SMCR.SMS = 0b001/010/011`）让 CNT 直接跟着正交编码器走：TI1 和 TI2 两路信号的**边沿顺序**决定加减，硬件自己算方向，CPU 只要定期读 CNT。这是"硬件做状态机"的极致例子。

### 正交信号：两路方波，90° 相差

旋转编码器输出两路方波 A/B，相位差 90°。正转时 A 领先 B，反转时 B 领先 A：

```
正转 (CW):  A ──┐  ┌──┐  ┌──
               └──┘  └──┘
               ┌──┐  ┌──┐
B:          ──┘  └──┘  └──    (A 领先 B 90°)

反转 (CCW): B 领先 A 90°，方向相反
```

### SMCR.SMS：三档编码模式

| SMS 值 | 模式 | 计数的边沿 | 分辨率 |
|---|---|---|---|
| `001` | 编码器模式 1 | 只计 TI1 边沿 | 1x |
| `010` | 编码器模式 2 | 只计 TI2 边沿 | 1x |
| `011` | 编码器模式 3 | TI1 + TI2 **双沿** | **4x** |

模式 3 最常用：两路信号各有上升/下降两个边沿，每个边沿都计数，分辨率 = 编码器线数 × 4。

### 硬件状态机：4 态决定加减

TIM 内部有一个 2-bit 状态机，跟踪 A/B 的当前电平组合：

| 当前状态 | 下一状态 | CNT 动作 |
|---|---|---|
| A=0, B=0 | A=1, B=0 | +1（正转） |
| A=1, B=0 | A=1, B=1 | +1 |
| A=1, B=1 | A=0, B=1 | +1 |
| A=0, B=1 | A=0, B=0 | +1 |
| 反向序列 | — | -1 |

硬件在每个边沿自动判断"这是正转的第几步还是反转的第几步"，CNT 跟着加减。CPU 完全不需要参与方向判断。

### 配置步骤

```c
/* TIM2 编码器模式 3：TI1 + TI2 双沿计数 */
RCC->APB1ENR |= RCC_APB1ENR_TIM2EN;
RCC->AHB1ENR |= RCC_AHB1ENR_GPIOAEN;

/* PA0=TI1, PA1=TI2 → AF1 (TIM2) */
GPIOA->MODER  |= (2 << 0) | (2 << 2);   // 复用模式
GPIOA->AFR[0] |= (1 << 0) | (1 << 4);   // AF1

TIM2->SMCR  &= ~TIM_SMCR_SMS;
TIM2->SMCR  |= 0b011;                    // SMS=011: 编码器模式 3
TIM2->CCMR1  = 0;                        // CC1S=01 (TI1), CC2S=01 (TI2)
TIM2->CCMR1 |= (1 << 0) | (1 << 8);     // IC1F=0000 (无滤波)
TIM2->CCER   = 0;                        // 不反相
TIM2->ARR    = 0xFFFFFFFF;               // 32 位满量程
TIM2->CR1   |= TIM_CR1_CEN;

/* 读位置：直接读 CNT */
int32_t position = (int32_t)TIM2->CNT;   // 有符号，正反转自动区分
```

### 分辨率计算

编码器标称 500 线/圈（每圈 500 个 A 脉冲），用模式 3 双沿计数：

```
实际分辨率 = 500 × 4 = 2000 计数/圈
角度精度   = 360° / 2000 = 0.18°
```

如果用 16-bit 定时器（ARR=65535），最大计数 65535，超过需要软件溢出计数。TIM2 是 32-bit，直接 `CNT` 就是有符号位置。

### 滤波与噪声

实际编码器信号有抖动。`CCMR1.IC1F` 设置输入滤波：

| IC1F | 滤波 | 效果 |
|---|---|---|
| `0000` | 无 | 最快，噪声敏感 |
| `0010` | f_CLK/4 × N=6 | 推荐起点 |
| `1000` | f_DTS/8 × N=6 | 强滤波，延迟增大 |

滤波本质是"连续 N 次采样一致才认可边沿"，和消抖开关的原理一样。

## 七、代码分析：`02-tim-pwm/main.c`

- `clocks_read()`：从 CFGR 反推 HCLK/PCLK1，HPRE/PPRE 的编码表直接按 RM0090 写（注意 AHB 没有 /32 这一档）。
- `timer_clock()`：APB 分频≠1 时 ×2，一行代码。
- `tim3_pwm_init()`：PSC/ARR/CCMR1/CCER 按上面第三、五节逐位落位；`EGR.UG` 让 PSC/ARR 立刻生效而不是等第一个更新事件。
- 捕获 ISR：读取 TIM2 时间戳；主循环只读一致快照，过捕获/超时不输出可信频率。
- 两个对照实验（改 APB1 分频前后读定时器时钟）实测 ×2 规则。

## 八、库解析对照：SPL/HAL 同名初始化

ST 官方仓库 [`STMicroelectronics/stm32f4xx_hal_driver`](https://github.com/STMicroelectronics/stm32f4xx_hal_driver)（master @ `1f6451c`）把本章寄存器动作拆成三个函数：`HAL_TIM_PWM_Init()` 定时基、`HAL_TIM_PWM_ConfigChannel()` 输出通道、`HAL_TIM_PWM_Start()` 放行。逐条对标本工程 `tim3_pwm_init()`：

| 本工程 `tim3_pwm_init()` | HAL 对应（hal_tim.c 行号 @ 1f6451c） | 对照结论 |
|---|---|---|
| PSC/ARR 直接写、`EGR.UG` 立刻生效 | `TIM_Base_SetConfig()`（L6776）：先 ARR（L6800）后 PSC（L6803），收尾 `EGR = UG`（L6817） | 同一招：UG 把影子值立刻装进来，不等第一个更新事件 |
| CCMR1 放 OC 模式、使能预装载 | `HAL_TIM_PWM_ConfigChannel()`（L4219）→ `TIM_OC1_SetConfig()`（L6828）：**先清 CCER.CC1E** 再改模式，OC1PE 单独置位（L4245），CCR1 初值写入（L6893） | HAL 改参数前先关通道——防止中途输出毛刺波形 |
| 最后 CCER 使能 + CR1.CEN | `HAL_TIM_PWM_Start()`（L1454）：`TIM_CCxChannelCmd()` 移位置 CCxE（L7626）；带 BKIN 的定时器（TIM1/8）才额外开 BDTR.MOE，从机触发模式不抢 CEN | 你的两步 = HAL 一步；TIM1/8 还多一个主输出开关 |
| 自己开 APB 时钟、配 GPIO | 放进 `HAL_TIM_PWM_MspInit()` 回调，仅句柄状态 RESET 时被调 | HAL 把"芯片初始化"与"板级初始化"分成两层 |

SPL 的 `TIM_TimeBaseInit()`/`TIM_OC1Init()` 做的是同一组落位，但 StdPeriph 未随 ST 官方 GitHub 分发，一手源码仍缺；位定义以 RM0090 为准。

![HAL 三段初始化与手写落位的对账图](/anim/tim-hal-init-path.svg)

## 附录：工程完整源码

<<< ../../code/stm32/02-tim-pwm/main.c

## 记忆锚点

::: tip 一句话记住
**PSC 除一除，ARR 数一数，频率=(时钟÷俩加一)；PWM 靠 CCR 比一比，捕获靠边沿拍一拍；回绕先看模数与丢边沿。**
:::

**延伸**：TIM TRGO 可触发 ADC 采样（[S9](09-adc.md)）；硬件 TIM 与 RTOS 软件定时器的分工见 [F6](../rtos/freertos/06-notify-event-timer.md)。

## 实物实验

- [E03 示波器看 PWM](../lab/e03-scope-pwm.md)：改 CCR 看占空比、改 ARR 看频率、逻辑分析仪读数与手算对表；
- 呼吸灯：CCR 三角渐变，肉眼验证"数字调光"；
- 自测闭环：PA6 接 PA0，捕获实测频率应与设定一致；
- 对照实验：把 APB1 从 /1 切到 /2，读 `g_tim_clk_before/after`：定时器时钟纹丝不动。

## 常见坑

- **两个"+1"漏算**：1kHz 配成 999Hz 的隐形误差；
- **忘开 GPIO 复用 + CC 通道使能**：CCxE 位不开，引脚永远没波形（输出使能是独立一步）；
- **APB 倍频规则记错**：APB1 分频≠1 时 TIM 时钟×2，TIM2 按 42MHz 算全错，它是 84MHz；
- **ARR=65535 溢出盲区**：测低频时 CNT 溢出忘计，结果差一整圈。必须使用溢出计数或独立宽计数器，不能只靠 uint32_t 强转；
- **改 CCR 没开预装载**：占空比在周期中间突然变，波形上出现一个"半边高半边低"的怪周期。

## 短自测

1. 为什么改 CCR 不会改 PWM 的频率？
<details><summary>参考答案</summary>频率由 PSC 和 ARR 决定（计数周期）；CCR 只决定"在一个周期里的哪一拍翻转电平"。改 CCR 只是移动开关点，不改周期的总长度。</details>

2. TIM3 挂在 APB1 上，APB1 分频 /4，PCLK1=42MHz，TIM3 的时钟是多少？
<details><summary>参考答案</summary>84MHz。规则：APB 分频 ≠ 1 时定时器时钟 = PCLK × 2。只记 42MHz 会把所有定时器算慢一半。</details>

3. 用 PSC=83、ARR=999 配 1kHz，为什么写成 PSC=84、ARR=1000 是错的？
<details><summary>参考答案</summary>硬件数的是"0 到 PSC"和"0 到 ARR"：84 对应分频 85，1000 对应周期 1001。更新频率 = 84MHz/85/1001 ≈ 987Hz，差一个"%"级。</details>

4. 输入捕获里"相邻两个上升沿的 CCR 差值"在 CNT 回绕时怎么算才对？
<details><summary>参考答案</summary>先确认计数模数等于 2^32、间隔小于整圈且未丢边沿，本例 TIM2 才可用 uint32_t 模差；ARR=999 的 TIM3 不能套用。</details>

<QuizBank chapter="s06-tim" />

## 对照表：本章概念 → 仓库与上游落点

| 概念 | 落点 |
|---|---|
| PSC/ARR/CCR/CCMR1/CCER 位定义 | ST CMSIS `stm32f407xx.h`（TIM_* 段） |
| APB ×2 规则实测 | [code/stm32/02-tim-pwm/main.c](https://github.com/zhuguang-ZFG/mcu/blob/main/code/stm32/02-tim-pwm/main.c) `timer_clock()` 与对照实验 |
| 无符号差值处理回绕 | 同上捕获循环 |
| 引脚复用 | DS8626 Rev 9 Table 9（PA6/PA7 AF2） |
| 动画 | [tim-pwm-counter.svg](/anim/tim-pwm-counter.svg)、[tim-input-capture.svg](/anim/tim-input-capture.svg)、[tim-hal-init-path.svg](/anim/tim-hal-init-path.svg)（§八对账） |
| HAL 同名初始化逐行对照 | ST 官方仓库 [stm32f4xx_hal_driver](https://github.com/STMicroelectronics/stm32f4xx_hal_driver) @ `1f6451c` `Src/stm32f4xx_hal_tim.c`（见 §八）；SPL 未随官方 GitHub 分发，一手源码仍缺 |

## 你做到了

- 时基/PWM/捕获三大件各自跑通，且有一个自测闭环可以验证；
- "计数器+比较器"的组合思维建立，后面 DAC 触发、编码器都是它的变体；
- 亲手实测了"APB 分频≠1 时定时器×2"这条不在框图里的规则。

押 CCR 的那把，中的其实是整章地基：开关点挪了，斜率没动，呼吸灯怎么喘都不跑调。

<div class="achievement">
✅ 下一站：<a href="07-usart.html">S7 USART</a>：让芯片开口说话，波特率怎么算、printf 怎么接、数据怎么一位位飞出去。
</div>

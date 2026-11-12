---
title: "定时器与 PWM"
platforms: [f407, f103, esp32]
---

# 定时器与 PWM

> 定时器的全部零件只有一个计数器：时钟推着 CNT 往上走，PSC 决定走多快，ARR 决定走到哪里回头，CCR 决定一圈里在哪一拍翻电平。这三个数拧对，1kHz 的方波就从 PA6 出来；把同一个计数器反过来用，边沿一到，硬件把 CNT 拍进 CCR，就成了输入捕获。这一章把 F407 的 84MHz 与 F103 的 72MHz 两套账并排算，把 PWM、定时中断、捕获与编码器接到同一张时基图上，再用 HAL 的三段初始化与手写落位对账。ESP32 只划边界：它的 timer group 与 LEDC 不是这套寄存器，完整内容在[第 31 章][ch31]。

## 本章罗盘

- **问题**：F407 的 TIM3 挂在 APB1，PCLK1=42MHz，为什么定时器时钟是 84MHz，1kHz 要写 PSC=83、ARR=999？两个“+1”各来自哪一段计数？改 CCR 为什么只动占空比、不动频率？TIM 中断和 SysTick 都数数，什么时候该用哪一个？PWM 的 TIM3 为什么不能拿同一个定时器测自己的周期，输入捕获的 `uint32_t` 差值在什么前提下才跨得过回绕？HAL 的 `HAL_TIM_PWM_Init`、`ConfigChannel`、`Start` 与手写寄存器落位怎么一一对上，TIM1 为什么还多一个 MOE？e03 的示波器探头该接哪里、记录什么，来源又到底留下了哪些读数？
- **交付**：能从真实的 TIMclk 算出任意目标频率的 PSC/ARR，并先检查它装不装得进 16 位或 32 位；能配出 PWM 模式 1 的 OC1M、OC1PE、CC1E 三位并算占空比；能按“内核心跳还是外设事件”给 TIM 与 SysTick 分工；能设计输入捕获的回绕判据，读懂 `capture.h` 的接受范围与过捕获处理；能配编码器模式 3 的 4 倍频并算出每计数多少度；能把 HAL 三段初始化对回手写寄存器；能按 e03 接线、读波形并留下可复现的记录。
- **边界**：三平台章。F407 的 84MHz、PA6/AF2、TIM2 的 32 位与 HAL 行号来自 S6《定时器 TIM》及 RM0090、DS8626；F103 的 72MHz、16 位定时器、PA6 默认复用与 TIM1 的 MOE 来自根书第 05 章及 RM0008、DS5319；ESP32 只写 timer group 与 LEDC 的边界，细节指向[第 31 章][ch31]。SysTick 的 24 位上限与 RTC 留给[第 11 章](./11-systick-timebase-rtc.md)，DMA 留给[第 14 章][ch14]，ADC 触发留给[第 15 章][ch15]，电机编码器测速留给[第 38 章][ch38]，仪器证据方法留给[第 40 章][ch40]。三个来源都没有留下本章的上板读数：S6 把捕获测频标成待实测，e03 的记录表是空的；S6 又说 APB ×2 由 `02-tim-pwm` 实测得出，同一工程的 README 与 `main.c` 却标着待上板实测，两处说法不一致。本章不把预期现象写成已经量到的结果。
- **依据锚点**：S6《S6 定时器 TIM：一器多用的瑞士军刀》（`mcu/docs/stm32/06-tim.md`）、根书第 05 章《定时器与 PWM》（`docs/05-定时器与PWM.md`）的时基与 PWM 部分、E03《实验 E03 示波器看 PWM》（`mcu/docs/lab/e03-scope-pwm.md`）；[第 8 章](./08-architecture-memory-clock.md)的 APB 分频与定时器时钟、[第 9 章](./09-gpio.md)的复用配置与 PC13 灌电流、[第 10 章](./10-interrupts-nvic-exti.md)的 NVIC 使能、[第 11 章](./11-systick-timebase-rtc.md)的 SysTick 24 位上限、[第 2 章](../v0-foundations/02-c-volatile-ub.md)的 volatile 合同、[第 3 章](../v0-foundations/03-struct-abi-registers.md)的寄存器结构体。RM0090、RM0008、DS8626、DS5319 与 HAL 源码行号均转引自上述来源。

## 先做出来

不接板子也能完成最小胜利：把两套 1kHz 的账算出来。公式只有一行：

```text
f = TIMclk / ((PSC + 1) × (ARR + 1))
```

表里两行是本章后面所有例子的基准，输入写在第一列：

| 平台 | TIMclk（输入） | PSC | 计数时钟 | ARR | 更新频率 | 周期 |
| --- | --- | --- | --- | --- | --- | --- |
| F407 | 84MHz（APB1=42MHz，×2） | 83 | 84MHz/84 = 1MHz | 999 | 1MHz/1000 = 1kHz | 1ms |
| F103 | 72MHz（PCLK1=36MHz，×2） | 71 | 72MHz/72 = 1MHz | 999 | 1MHz/1000 = 1kHz | 1ms |

押一题再往下读：ARR=999、CCR=500 时占空比是 50%。只把 CCR 改成 250，频率变不变、占空比是多少？再把 ARR 改成 499（CCR 保持 250），频率和占空比又各是多少？答案分别是“频率不变、25%”和“2kHz、50%”。算的时候频率只看 PSC/ARR，占空比只看 CCR/(ARR+1)；ARR 从 999 改成 499，计数时钟仍是 1MHz，周期从 1000 个计数缩到 500 个。如果只改 ARR=499 而 CCR 仍是 500，占空比会变成 100%，因为 CNT 到不了 500；这是“CCR 超过 ARR”的边界。

有板的人把 `mcu/code/stm32/02-tim-pwm` 烧进 F407：PA6 输出 1kHz 方波，主循环每 20ms 改一次 CCR，做呼吸。工程 README 把这一步写成待上板实测，本章不把预期现象当成已记录读数。探头怎么接、记录什么，见“测量与证据”的 e03。

![E03 探头接法与读图：CNT 锯齿与 CCR 比较得到 PA6 方波，周期 1ms、高电平 0.5ms](/images/labs/e03-pwm-probe.svg)

## 机制

### 先问真实的 TIMclk：APB 分频不等于 1 就乘 2

定时器的分母不是 PCLK，而是 TIMxCLK。RM0090 与 RM0008 写同一条规则：APB 预分频为 1 时 TIMxCLK = PCLK；不为 1 时 TIMxCLK = PCLK × 2。F407 的 TIM3 挂在 APB1，168MHz 主频下 PCLK1=42MHz、APB1 分频 /4，所以 TIM3 按 84MHz 计数；F103 的 TIM3 同样挂 APB1，72MHz 主频下 PCLK1=36MHz、APB1 分频 /2，TIM3 按 72MHz 计数。按 42MHz 或 36MHz 去算，得到的频率正好差一倍。

这条 ×2 规则来自用户手册，不是从某次波形里读出来的。S6 正文说它由 `02-tim-pwm` 的对照实验实测得出；同一个工程的 `README.md` 末尾却写“待上板实测”，`main.c` 头注释也写 `Hardware measurements pending`，工程里没有留下波形或日志。两处说法不一致，本章把 ×2 当作手册规则使用，把“实测”当作待复核的来源说法；要把它变成板上证据，得在 APB1=/1 与 /2 下各读一次定时器时钟，并把两次读数记下来。

计数时钟 = TIMclk/(PSC+1)，更新频率 = 计数时钟/(ARR+1)。两个 +1 是因为硬件从 0 数到 PSC、从 0 数到 ARR。F407 的 1kHz：84MHz/84 = 1MHz，1MHz/1000 = 1kHz，PSC=83、ARR=999；F103 的 1kHz：72MHz/72 = 1MHz，同样 PSC=71、ARR=999。两套账都先把计数时钟压到 1MHz，再数 1000 下，周期 1ms。

计数模式有向上、向下、中央对齐三种，最常用的是向上计数：CNT 从 0 到 ARR 产生更新事件。ARR 与 CCR 都有预装载：置 ARPE 或 OCxPE 后，新值先写进预装载寄存器，等更新事件才装进影子寄存器参与比较。代价是新值晚一圈生效，换来的是周期中途不出现半新半旧的怪波形。

![定时器时基：PSC 分频后的计数时钟推动 CNT 从 0 数到 ARR，CNT 小于 CCR 时 PWM 为高](/figures/stm32-06-tim.svg)

### PWM：CCR 在周期里画一条开关线

PWM 模式 1 的规则一句话：CNT < CCR 时输出有效电平，否则输出无效电平。有效电平由极性位 CCxP 决定，所以同一组数可以输出高有效或低有效。占空比 = CCR/(ARR+1)，频率只由 PSC/ARR 决定。ARR=999 时，CCR=250 是 25%，CCR=500 是 50%，CCR=750 是 75%，每一步 1/1000 = 0.1%，对应 1µs 的高电平步进。

三个位一个都不能少：`CCMR1.OC1M=110` 选 PWM 模式 1；`CCMR1.OC1PE=1` 让 CCR 预装载；`CCER.CC1E=1` 打开通道输出。少了 CC1E，定时器照跑、中断照进，引脚上却永远没有波形，这是新手第一大坑。极性配反，占空比会从 25% 变成 75%。

改 CCR 不改频率，是因为频率的账里没有 CCR：PSC 和 ARR 没动，周期就没动；CCR 只移动一圈里的翻点。呼吸灯就是周期性把 CCR 从 0 扫到 ARR 再扫回来：`02-tim-pwm` 的主循环每 20ms 走一步，200 步一个来回，约 4 秒。频率始终 1kHz 是公式的直接结果；要把“频率纹丝不动”变成板上证据，仍需示波器同时看周期与高电平。

分辨率与频率是一对矛盾：一圈只有 ARR+1 格，格数就是占空比档位数。根书第 05 章给过一张 72MHz 的表，输入都写在表里：

| 目标 | PSC | ARR+1 | 占空比分辨率 | 说明 |
| --- | --- | --- | --- | --- |
| 1kHz | 1 | 36000 | 1/36000 | PSC=0 时 ARR+1 要 72000，超过 16 位上限 65536，所以 PSC 取 1 |
| 10kHz | 0 | 7200 | 1/7200 | 常用电机 PWM |
| 20kHz | 0 | 3600 | 1/3600 | 把开关声移出主要可听范围；仍要实测电机与驱动器 |
| 50Hz（舵机） | 71 | 20000 | 1/20000 | 1µs 一格、20ms 一圈，1–2ms 脉宽对应 CCR=1000–2000 |

频率越高，一圈的格子越少，能切的占空比档位越少；要高频又要细调，就得提高 TIMclk 或换更高位宽的定时器。

![TIM PWM 计数器动画：CNT 往上涨、ARR 定终点、CCR 定开关点，改 CCR 只移动翻点](/anim/tim-pwm-counter.svg)

### 定时中断：TIM 管精确，SysTick 管心跳

定时中断的配置只有三步：时基给出更新频率，`DIER.UIE=1` 打开更新中断，NVIC 里放行 `TIMx_IRQn`；ISR 进门先清 `SR.UIF`，再做事。S6 的例子是 1Hz 翻灯；根书第 05 章的 HAL 版本用 `HAL_TIM_Base_Start_IT(&htim2)` 启动，在 `HAL_TIM_PeriodElapsedCallback` 里判断 `htim->Instance == TIM2` 后翻 PC13。

和 SysTick 的分工按归属划：SysTick 是 Cortex-M 内核的 24 位倒数秒表，回答“过了多久”，用于毫秒心跳、延时和 RTOS 节拍；TIM 是芯片外设，回答“精确到多少个计数”，能出引脚、能触发 ADC、能捕获边沿。SysTick 不要拿来做 PWM，TIM 不要拿来做系统延时。

| 维度 | SysTick | TIMx |
| --- | --- | --- |
| 归属 | Cortex-M 内核 | 芯片外设 |
| 计数宽度 | 24 位 | 16 位或 32 位 |
| 典型用途 | 毫秒心跳、延时、RTOS tick | 精确定时、PWM、捕获、编码器、TRGO |
| 引脚输出 | 无 | 有通道引脚 |
| 放错位置 | 拿来做 PWM | 拿来做系统延时 |

F103 想要 1 秒中断，`SysTick_Config(72000000)` 会被 24 位上限拒绝（[第 11 章](./11-systick-timebase-rtc.md)算过这笔账）；TIM2 用 PSC=7199、ARR=9999，72MHz/(7200×10000) = 1Hz。这就是“需要长周期时换 TIM”的具体理由。

ISR 的频率也要算账：1kHz 更新中断每秒进 1000 次，每次几十条指令，CPU 还扛得住；要 100kHz 的方波就别让 ISR 去翻引脚，直接让 PWM 硬件输出。中断只适合“每个周期做一件轻活”，重活留给主循环或 DMA（[第 14 章][ch14]）。

### 输入捕获：让硬件给 CNT 拍照

输入捕获把方向反过来：引脚上的边沿一到，硬件把当时的 CNT 抄进 CCR，CPU 不用掐表。两次捕获的差值乘计数周期，就是脉宽或周期。TIM2 以 1MHz 自由计数、ARR=0xFFFFFFFF 时，1 个计数 = 1µs；相邻两个上升沿的差值直接读成微秒数，频率 = 1e6/差值。

第一个坑是拿 PWM 自己的定时器测自己：TIM3 的 ARR=999，PWM 周期正好 1000 个计数，同相位的边沿每个周期都落在同一个 CNT 上，读到的差值恒为 0，分不出经过了几圈，读不出周期。所以 `02-tim-pwm` 用独立的 TIM2 捕获 PA6，PA6 跳线到 PA0（TIM2_CH1，AF1）。

第二个坑是回绕。只有计数模数等于运算位宽（这里是 2^32）、两次边沿间隔小于一整圈、且没有丢边沿时，`uint32_t` 的无符号相减才正确处理回绕。反例：ARR=999 的 TIM3，last=990、now=10，真实差是 20，`uint32_t` 相减却得到 4294966316；就算改成模 1000，也分不清经过了零圈还是一整圈。S6 因此把捕获时基换成 32 位自由计数，并给捕获判定加了范围：只接受 100µs–500ms 的间隔，首次捕获只建立基准，过捕获（overcapture）重新建立基准，超过 1 秒没有新边沿就清掉频率。

共享判定函数在 `mcu/code/common/behavior/capture.h`：`delta = now - previous`，只有见过上一拍且 `100 <= delta <= 500000` 才输出 `1000000/delta`；`overcapture` 把频率清零并记一次丢失。`tests.c` 里写着对应的断言：`UINT32_MAX-499` 之后接 `500` 得到 1000Hz，`overcapture=true` 后频率为 0、`lost=1`，超时后清零。主循环不直接读捕获结构体，而是用 `lock()`/`unlock()` 的 PRIMASK 短临界区复制一份快照，再在临界区外使用；跨 ISR 与主循环的变量按[第 2 章](../v0-foundations/02-c-volatile-ub.md)的 volatile 合同声明。这些是源码里的断言与写法，不是本章跑出来的板上读数；板上测频在 S6 里仍标着待实测。

![输入捕获：边沿拍照 → CNT 差值 → 脉宽与频率](/anim/tim-input-capture.svg)

### 编码器接口：方向由边沿顺序决定

正交编码器输出 A/B 两路方波，相位差 90°。正转 A 领先 B，反转 B 领先 A。TIM 的编码器接口（`SMCR.SMS=001/010/011`）让硬件盯着两路边沿：模式 1 只计 TI1 边沿，模式 2 只计 TI2，模式 3 双沿都计，分辨率 ×4。CPU 不参与方向判断，定期读 CNT 就是位置。

| SMS | 模式 | 计数的边沿 | 分辨率 |
| --- | --- | --- | --- |
| `001` | 编码器模式 1 | 只计 TI1 边沿 | 1x |
| `010` | 编码器模式 2 | 只计 TI2 边沿 | 1x |
| `011` | 编码器模式 3 | TI1 + TI2 双沿 | 4x |

硬件内部是一个 2 位状态机，跟踪 A/B 当前电平组合；正转序列让 CNT +1，反转序列让 CNT −1：

| 当前 A/B | 下一 A/B | CNT 动作 |
| --- | --- | --- |
| 00 | 10 | +1 |
| 10 | 11 | +1 |
| 11 | 01 | +1 |
| 01 | 00 | +1 |
| 反向序列 | — | −1 |

500 线/圈的编码器在模式 3 下是 500×4 = 2000 计数/圈，360°/2000 = 0.18°/计数。换编码器线数就重算这两个数。配置片段（S6，F407 的 TIM2）：

```c
/* PA0=TI1, PA1=TI2 → AF1 (TIM2) */
GPIOA->MODER  |= (2 << 0) | (2 << 2);
GPIOA->AFR[0] |= (1 << 0) | (1 << 4);
TIM2->SMCR  &= ~TIM_SMCR_SMS;
TIM2->SMCR  |= 0b011;               /* 编码器模式 3：TI1+TI2 双沿 */
TIM2->CCMR1  = 0;
TIM2->CCMR1 |= (1 << 0) | (1 << 8); /* CC1S=01, CC2S=01 */
TIM2->CCER   = 0;
TIM2->ARR    = 0xFFFFFFFF;
TIM2->CR1   |= TIM_CR1_CEN;
int32_t position = (int32_t)TIM2->CNT;  /* 有符号，正反转自动区分 */
```

滤波用 `CCMR1.IC1F`：0000 无滤波；0010 是 f_CLK/4、N=6 的推荐起点；1000 是 f_DTS/8、N=6 的强滤波，延迟更大。滤波本质是连续 N 次采样一致才认可边沿，和消抖开关的原理一样。

F103 的 TIM2–TIM5 是 16 位，ARR 最多 65535，模式 3 下超过 65535 的计数要靠软件溢出；读 CNT 用 `int16_t` 才有正负。F407 的 TIM2/TIM5 是 32 位，才能直接 `int32_t` 读满量程。电机测速与闭环在[第 38 章][ch38]。

![正交编码器：A/B 边沿顺序定方向，模式 3 双沿计数得 4 倍频](/figures/stm32-06-encoder.svg)

### HAL 三段初始化：把同一组落位拆成三层

手写寄存器的时候，初始化是一口气写完的：开时钟、配 GPIO、写 PSC/ARR、写 CCMR1/CCER、最后 CR1.CEN。HAL 把同一组动作拆成三层：`HAL_TIM_PWM_Init()` 管时基，`HAL_TIM_PWM_ConfigChannel()` 管通道，`HAL_TIM_PWM_Start()` 放行；板级时钟与 GPIO 放在 `HAL_TIM_PWM_MspInit()` 回调里，只有句柄状态是 RESET 时才被调用。

对账表（HAL 行号来自 S6 对 ST 官方 `stm32f4xx_hal_driver` master@1f6451c 的记录，本章没有重跑该仓库）：

| 手写落位（`02-tim-pwm/main.c`） | HAL 对应（`stm32f4xx_hal_tim.c` @ 1f6451c） | 对照结论 |
| --- | --- | --- |
| PSC/ARR 直接写、`EGR.UG` 立刻生效 | `TIM_Base_SetConfig()`（L6776）：先 ARR（L6800）后 PSC（L6803），收尾 `EGR = UG`（L6817） | 同一招：UG 把影子值立刻装进来，不等第一个更新事件 |
| CCMR1 放 OC 模式、使能预装载 | `HAL_TIM_PWM_ConfigChannel()`（L4219）→ `TIM_OC1_SetConfig()`（L6828）：先清 `CCER.CC1E` 再改模式，OC1PE 单独置位（L4245），CCR1 初值写入（L6893） | HAL 改参数前先关通道，防止中途输出毛刺波形 |
| 最后 CCER 使能 + CR1.CEN | `HAL_TIM_PWM_Start()`（L1454）：`TIM_CCxChannelCmd()` 置 CCxE（L7626）；带 BKIN 的定时器（TIM1/8）才额外开 `BDTR.MOE`，从机触发模式不抢 CEN | 手写两步等于 HAL 一步；TIM1/8 还多一个主输出开关 |
| 自己开 APB 时钟、配 GPIO | 放进 `HAL_TIM_PWM_MspInit()` 回调，仅句柄状态 RESET 时被调 | HAL 把芯片初始化与板级初始化分成两层 |

手写片段摘自 `02-tim-pwm/main.c`，按寄存器名改写，偏移与位值不变：

```c
/* F407 TIM3_CH1：84MHz → 1MHz → 1kHz */
TIM3->PSC   = 83;                     /* 84MHz / 84 = 1MHz */
TIM3->ARR   = 999;                    /* 1MHz / 1000 = 1kHz */
TIM3->CCMR1 = (6U << 4) | (1U << 3);  /* OC1M=110 PWM1, OC1PE=1 */
TIM3->CCR1  = 500;                    /* 500/1000 = 50% */
TIM3->CCER  = 1;                      /* CC1E=1 */
TIM3->EGR   = 1;                      /* UG：PSC/ARR 立即生效 */
TIM3->CR1   = 0x81;                   /* CEN=1, ARPE=1 */
```

对应的 HAL 序列（根书第 05 章，F103 的 72MHz 参数）：

```c
TIM_OC_InitTypeDef oc = {0};
htim3.Instance = TIM3;
htim3.Init.Prescaler = 71;            /* 72MHz / 72 = 1MHz */
htim3.Init.CounterMode = TIM_COUNTERMODE_UP;
htim3.Init.Period = 999;              /* 1MHz / 1000 = 1kHz */
htim3.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
htim3.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_ENABLE;
HAL_TIM_PWM_Init(&htim3);             /* 时基；内部会调 MspInit */

oc.OCMode = TIM_OCMODE_PWM1;
oc.Pulse = 500;                       /* CCR=500 → 50% */
oc.OCPolarity = TIM_OCPOLARITY_HIGH;
oc.OCFastMode = TIM_OCFAST_DISABLE;
HAL_TIM_PWM_ConfigChannel(&htim3, &oc, TIM_CHANNEL_1);
HAL_TIM_PWM_Start(&htim3, TIM_CHANNEL_1);
```

几个容易对不上的点：`TIM_Base_SetConfig()` 先写 ARR 再写 PSC，收尾统一 `EGR = UG`，和手写的顺序不同但效果一样；`ConfigChannel` 进 `TIM_OC1_SetConfig()` 前先清 `CCER.CC1E`，再改模式和预装载；`Start` 里 `TIM_CCxChannelCmd()` 置 CCxE，TIM1/TIM8 还要额外开 `BDTR.MOE`。SPL 的 `TIM_TimeBaseInit()`/`TIM_OC1Init()` 做同一组落位，但 SPL 没随 ST 官方 GitHub 分发，一手源码仍缺，位定义以 RM0090 为准。

TIM1 没有波形，先查 `BDTR` 的 MOE：偏移 0x44、复位值 0x0000，bit15 为 0 时主输出关闭；HAL 的 `HAL_TIM_PWM_Start` 会替你置上，自己写寄存器容易漏。TIM3 没有这一位。

![HAL 三段初始化与手写落位的对账图：Init 管时基、ConfigChannel 管通道、Start 放行，MspInit 管板级](/anim/tim-hal-init-path.svg)

## 测量与证据

本章没有板上读数：三个来源都没有留下波形或日志，e03 的记录表是空的。能拿出来的证据分三类：手册与源码里的位、按公式算出的账、待做的实验设计。

### e03：示波器看 PWM（来源实验设计，记录待做）

接线只有两根：探头尖端接 F407 的 PA6（TIM3_CH1，AF2），地夹接板子地；S3 一侧接 GPIO10（LEDC 低速通道 0）。探头上的 ×1/×10 开关要和示波器通道设置一致，否则幅值差 10 倍。

步骤照 e03 的顺序：

1. 进入 `mcu/code/stm32/02-tim-pwm`，`make` 后 `make flash`；默认 PA6 输出 1kHz，主循环让占空比在 0–100% 之间呼吸。S3 进入 `mcu/code/esp32/03-ledc-fade`，`idf.py set-target esp32s3`、`idf.py build`、`idf.py -p COMx flash monitor`；默认 GPIO10 输出 5kHz fade。
2. F407 固定 25%：把主循环里的 CCR 改成 `(PWM_PERIOD_TICKS + 1U) / 4U` = 250，重新构建烧录。
3. 把 `PWM_PERIOD_TICKS` 从 999 改成 499，计数时钟不变，频率应翻倍到 2kHz。
4. S3 记录 0→1023/1024 的渐变时间，目标约 2 秒，最大值不是精确 100%。
5. 进阶：PA6 经 10kΩ+100nF 低通，示波器看平均电压约 VCC×占空比，纹波随 PWM 频率变。

预期现象（来源写的是预期，不是读数）：占空比跟手算走；改 ARR 频率变；呼吸灯渐变呈阶梯。来源还要求比较测量值与手算结果，记录时钟源与仪器误差，不预填未测得的误差范围。

记录表至少要有这些列；e03 来源里的表是空的，`hardware_status` 还是 pending：

| 日期 | 板子 | 观测手段 | 设定 PSC/ARR/CCR | 测得周期 | 测得高电平 | 测得占空比 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| | | | | | | | |

一次完整记录还要留下波形截图或屏幕照片，能看见时基、幅值、探头衰减；再加一组寄存器读回（PSC/ARR/CCR/CC1E）。只有“灯亮/灯暗”不算 PWM 证据：亮度是平均电流的现象，周期和占空比要靠仪器读。

![RIGOL DS1054Z 四通道数字示波器，屏幕显示一条正弦波](/images/tools/oscilloscope-ds1054z.jpg)

仪器形态参考（资料参考图，不是上板验证证据）：RIGOL DS1054Z。图源 Wikimedia Commons，CC BY-SA 4.0，作者 Draconichiaro；探头档位要与示波器设置一致。

### 读数来路表

| 取证项 | 来路 | 读数或结论 | 性质 |
| --- | --- | --- | --- |
| F407 TIM3 的 84MHz | RM0090 的 APB 规则，转引自 S6 | 168MHz、PCLK1=42MHz、APB1=/4，TIMclk=42×2=84MHz | 手册规则 |
| F103 TIM3 的 72MHz | RM0008，转引自根书第 05 章 | 72MHz、PCLK1=36MHz、APB1=/2，TIMclk=36×2=72MHz | 手册规则 |
| F407 的 1kHz 参数 | 本章按公式算 | 输入 84MHz、PSC=83、ARR=999：84e6/84/1000 = 1000Hz，T=1ms | 推导 |
| F103 的 1kHz 参数 | 本章按公式算 | 输入 72MHz、PSC=71、ARR=999：72e6/72/1000 = 1000Hz，T=1ms | 推导 |
| 50% 占空比 | 本章按公式算 | 输入 ARR=999、CCR=500：500/1000 = 50% | 推导 |
| F103 的 1 秒定时 | 根书第 05 章的表，本章复算 | 输入 72MHz、PSC=7199、ARR=9999：72e6/7200/10000 = 1Hz；999999 超出 16 位 | 推导/手册 |
| 编码器 4 倍频 | S6 | 500 线×4 = 2000 计数/圈；360/2000 = 0.18°/计数 | 推导（输入来自来源） |
| APB ×2 的“实测” | S6 正文；同工程 README 与 `main.c` | S6 说实测；README 写“待上板实测”，`main.c` 写 `Hardware measurements pending`，无波形/日志 | 来源说法，待复核 |
| 捕获判定与范围 | `capture.h`、`tests.c` | 1MHz 自由计数、100µs–500ms；tests.c 有跨回绕、首拍、丢边沿、超时断言 | 源码，本章未复跑 |
| 板上测频 | S6 | 明确写“板上测频仍待实测” | 待做实验 |
| e03 读数 | E03 | `hardware_status: pending`，实测记录表为空 | 待做实验 |
| HAL 行号 | S6 对 1f6451c 的记录 | L6776/L6800/L6803/L6817/L4219/L6828/L4245/L6893/L1454/L7626 | 来源记录，未复核 |
| 示波器照片 | Wikimedia Commons | 资料参考图，不是上板证据 | 参考图 |

这些数能互相对上的只有公式与位定义：公式能证明 1kHz 该写 83/999，不能证明板上的 PA6 真的输出了 1kHz；读回能证明你写的位与你的宏一致，不能证明引脚上有波形。要补上后者，得按 e03 的记录表留下仪器读数。

<QuizBank chapter="s06-tim" />

## 失败分支

| 现象 | 原因 | 区分证据 | 下一动作 |
| --- | --- | --- | --- |
| PA6 上没有波形 | CC1E 没置位、GPIOA 没配 AF2、或 GPIOA 时钟没开 | 读 TIM3_CCER 的 bit0、GPIOA_AFRL[27:24]、RCC_AHB1ENR 的 bit0 | 先开时钟，再配 AF2，最后置 CC1E |
| 频率正好差一倍 | 把 PCLK 当成 TIMclk（F407 42 对 84，F103 36 对 72） | 读回 PSC/ARR，用 84MHz 或 72MHz 重算；PSC 没动却差一倍 | 按 TIMclk 重算 PSC/ARR |
| 频率是设定值的 1/10 或 10 倍 | 漏了 +1，或 PSC 少写一位 | 读回 PSC/ARR，按 (PSC+1)(ARR+1) 复算 | 补 +1，重写 |
| 占空比反了 | 极性 CCxP 配反 | 读 CCER 的 CC1P；25% 变 75% | 改极性或改 CCR |
| 占空比在周期中途跳变 | OC1PE 没开 | 读 CCMR1 的 OC1PE；波形出现半边高半边低 | 置 OC1PE，或等更新事件再改 CCR |
| TIM1 完全没波形 | BDTR.MOE=0 | 读 BDTR 的 bit15；TIM3 没有这一位 | `HAL_TIM_PWM_Start` 或置 MOE |
| 捕获一直为 0 | 跳线没接、CC2E 没开、或 CC1IF 没清 | 读 TIM2_CCER、TIM2_SR；PA6→PA0 是否接上 | 接跳线、开通道、清标志 |
| 捕获频率在回绕时离谱 | 用了 ARR=999 的定时器做 32 位模差 | 读 ARR；差值出现 4294966xxx | 换 32 位自由计数，或按模数补偿 |
| 捕获偶尔跳变 | 过捕获或丢边沿没处理 | 读 SR 的 CC1OF；`capture.lost` 增加 | 清 CC1OF，丢弃该次，重建基准 |
| 编码器只往一个方向数 | 只接了一相，或另一相的 AF 没配 | CNT 在两个方向都只增或只减 | 检查 TI1/TI2 两脚与 AF |
| 编码器计数抖动 | IC1F 滤波太弱或太强 | 静止时 CNT 是否自己跳；动态时是否丢步 | 从 0010 起调，权衡延迟 |
| F103 上 1 秒定时装不下 | ARR=999999 超过 16 位 | 读回 ARR 被截断 | PSC=7199、ARR=9999 |
| F407 把 TIM3 通道配到 PF6 | Port F 没有 TIM3 通道 | 查 DS8626 Table 9：PF6 的 AF3 是 TIM10_CH1 | 改用 PA6/PB4/PC6（AF2） |
| 示波器幅值差 10 倍 | 探头 ×1/×10 与通道设置不一致 | 看探头开关与屏幕上的衰减读数 | 两边统一 |
| F103 示波器读到 500Hz | 按 36MHz 算了 72MHz 的定时器 | 用 72MHz 复算，500Hz 正好是一半 | 改 PSC=71/ARR=999，或按 72MHz 重算 |

## 跨平台边界

F407 一侧：TIM3 在 APB1，168MHz 主频、APB1=/4 时 TIM3=84MHz；1kHz 用 PSC=83、ARR=999。PA6 是 TIM3_CH1 AF2，TIM3_CH2 在 PA7 AF2；TIM3_CH1 还可到 PB4/PC6，换脚查 DS8626 Table 9。Port F 没有 TIM3 通道，PF6/PF7/PF8 的 AF3 是 TIM10_CH1/TIM11_CH1/TIM13_CH1。TIM2/TIM5 是 32 位，TIM3 是 16 位；TIM1/TIM8 是高级定时器，输出前要开 `BDTR.MOE`。HAL 的行号与 MspInit 行为绑定 F4 HAL 的 1f6451c 版本，换库先核对。

F103 一侧：TIM3 同样在 APB1，72MHz 主频、PCLK1=36MHz 时 TIM3=72MHz；1kHz 用 PSC=71、ARR=999。C8 的 TIM2–TIM5 都是 16 位，ARR 最大 65535，1 秒要 PSC=7199、ARR=9999；32 位定时器是 F4 等系列的事。PA6 是 LQFP48 第 16 脚的默认 TIM3_CH1，同一脚还列着 SPI1_MISO，同一时间只能用一个功能；保持 TIM3_REMAP=00 才留在 PA6，重映射到 PB4/PC6 要经 AFIO。F1 没有逐脚 AF 号，别把 F4 的 AF2 写法搬过去。PC13 当翻灯脚时只能灌电流，规则见[第 9 章](./09-gpio.md)。SPL 的 `TIM_TimeBaseInit()`/`TIM_OC1Init()` 与 HAL 落位相同，但一手源码仍缺。

ESP32 一侧只划边界：ESP32-S3 的定时器是 timer group，PWM 是 LEDC；LEDC 的占空比按 `duty/2^bits` 算，和 STM32 的 `CCR/(ARR+1)` 不是同一套参数，PSC/ARR/CCR 的名字与位定义都不要带过去。e03 的 S3 分支用 GPIO10、LEDC 低速通道 0、5kHz fade，只作为实验对照。ESP32 外设、驱动框架与音频链路见[第 31 章][ch31]，架构与启动见[第 30 章][ch30]，多核与 Cache 见[第 34 章][ch34]。

其它分工：SysTick 的 24 位上限与 RTC 在[第 11 章](./11-systick-timebase-rtc.md)；DMA 搬运捕获数据在[第 14 章][ch14]；TIM TRGO 触发 ADC 在[第 15 章][ch15]；编码器测速与闭环在[第 38 章][ch38]；仪器与证据方法在[第 40 章][ch40]。

## 离开检查

1. F407 的 TIM3 时钟是多少？要 1kHz，PSC/ARR 为什么是 83/999？
2. F103 的 1kHz 为什么是 71/999？要 1 秒，为什么不能写 ARR=999999？
3. 改 CCR 为什么不动频率？OC1PE 开与不开，改 CCR 的波形差在哪？
4. TIM 中断和 SysTick 各管什么？F103 上为什么 1 秒定时要用 TIM？
5. 输入捕获为什么不能拿 PWM 自己的 TIM3 测自己？`uint32_t` 模差在什么前提下成立？
6. 编码器模式 3 的 4 倍频怎么来的？500 线编码器每计数多少度？
7. HAL 的 Init/ConfigChannel/Start 与手写 PSC/ARR/CCMR1/CCER/CR1 怎么对上？TIM1 为什么多一个 MOE？
8. e03 的探头接哪里、记录哪几项？只有“灯变亮”为什么不算 PWM 证据？

<details>
<summary>对照答案</summary>

1. TIM3 在 APB1，APB1=/4、PCLK1=42MHz，TIMclk=84MHz。84MHz/(83+1)=1MHz，1MHz/(999+1)=1kHz，周期 1ms。输入是 84MHz、PSC=83、ARR=999。
2. TIMclk=72MHz，72MHz/(71+1)=1MHz，再除以 1000 得 1kHz。要 1 秒，ARR+1 需要 72e6/(PSC+1)；PSC=7199 时 ARR+1=10000，即 ARR=9999。C8 的 TIM2–TIM5 是 16 位，ARR=999999 装不下，会被截断。
3. 频率 = TIMclk/((PSC+1)(ARR+1))，账里没有 CCR；CCR 只决定一圈里哪一拍翻电平。OC1PE=1 时，新 CCR 在下一个更新事件才生效；不开预装载，周期中途改 CCR 会出现一个高电平或低电平明显变长/变短的怪周期。
4. SysTick 是内核的 24 位秒表，管毫秒心跳、延时与 RTOS 节拍；TIM 是外设，管精确事件、引脚波形、捕获与触发。F103 要 1 秒，72e6 个时钟超过 24 位上限，`SysTick_Config(72000000)` 返回 1 拒配；TIM2 用 PSC=7199、ARR=9999 从 72MHz 得到 1Hz。
5. 同一个 TIM3 的 ARR=999，PWM 周期就是 1000 个计数，同相位边沿每个周期落在同一个 CNT 上，读到的差值恒为 0，分不出经过了几圈。换独立的 32 位 TIM2 自由计数才行。无符号模差成立的前提：计数模数等于 2^32、间隔小于一整圈、没有丢边沿；ARR=999 的定时器不满足模数条件，last=990、now=10 会算成 4294966316，而不是 20。
6. 模式 3 同时计 TI1 和 TI2 的上升沿与下降沿，一路方波一圈有 2 个边沿，两路就是 4 个计数，所以 500 线×4 = 2000 计数/圈；360°/2000 = 0.18°/计数。
7. `HAL_TIM_PWM_Init` 对应 PSC/ARR 与 `EGR.UG`（`TIM_Base_SetConfig`）；`ConfigChannel` 对应 CCMR1 的 OC1M/OC1PE、CCR1，并在改参数前先清 CC1E；`Start` 对应 CCER.CC1E 与 CR1.CEN。MspInit 管时钟与 GPIO。TIM1/TIM8 是高级定时器，除了 CCxE 还要置 `BDTR.MOE`（bit15），否则主输出关闭，引脚没有波形。
8. F407 探头接 PA6（TIM3_CH1 AF2），地夹共地；S3 接 GPIO10。记录要有时基、周期、高电平时间、占空比、幅值、探头衰减与寄存器读回。灯变亮只说明平均电流变了，频率错、极性反、占空比偏都能让灯亮，必须用仪器读周期与高电平才能证明 PWM 参数正确。

</details>

[ch14]: ./14-dma.md
[ch15]: ./15-adc-dac-sampling.md
[ch30]: ../v4-platforms/30-esp32s3-architecture-boot.md
[ch31]: ../v4-platforms/31-esp32-drivers-audio.md
[ch34]: ../v4-platforms/34-multicore-cache.md
[ch38]: ../v5-motion/38-encoder-speed-measurement.md
[ch40]: ../v6-labs-projects/40-lab-method-instruments.md

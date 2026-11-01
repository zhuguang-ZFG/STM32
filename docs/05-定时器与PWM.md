# 05 定时器与 PWM

> English: [Timers and PWM](en/05-timer-pwm.md)

> 定时器负责精确计时、产生 PWM 和捕获外部信号，是控制类应用的心脏。

<p align="center">
  <img src="../assets/animations/timer-pwm.svg" width="760" alt="定时器计数与 PWM 占空比">
  <br><sub>▲ 动画：定时器计数、比较匹配与 PWM 占空比（呼吸灯，作者自绘矢量图）</sub>
</p>

<!-- video:ch05 -->
<p align="center">
  <video width="640" controls poster="../assets/video/ch05-tim.png">
    <source src="../assets/video/ch05-tim.mp4" type="video/mp4">
  </video>
  <br><sub>▲ 本章讲解视频（2.6 分钟）。<a href="../assets/video/ch05-tim.mp4">MP4</a> · <a href="../assets/video/ch05-tim.srt">字幕</a></sub>
</p>

<details>
<summary>旁白文字稿</summary>

1. 定时器不是魔法，就是一个被时钟推着走的计数器。CNT 加到 ARR 就回头，这一圈就是周期。先把这句话讲顺，再去看 PWM。
2. 三个数各管一件事。PSC 把时钟变慢，ARR 决定一圈多长，CCR 决定方波在哪里翻。频率不对先看前两个，亮度不对再看 CCR。
3. 频率等于定时器时钟，除以 ARR 加 1，再除以 PSC 加 1。想要 1 千赫，先选定分频后的计数时钟，再反推 ARR。不要三个数一起瞎试。
4. 这一帧是仓库画的 PWM。计数器一边跑，一边和 CCR 比。低于和高于可以是两种电平，占空比就出来了。示波器上的高电平宽度，应该和你算的 CCR 一致。
5. 想要 1 千赫，你先定谁？先定 PSC，让计数时钟变成好算的整数，再定 ARR 加 1。CCR 最后填，因为它不改变频率，只改变占空比。
6. 输入捕获不是去量电压。边沿到来时，硬件把当时的 CNT 锁进捕获寄存器。两个边沿相减，再乘上计数周期，就是脉宽。口诀：捕获锁的是 CNT。
7. 回到时钟那一章：APB 分频大于 1 时，定时器时钟常常还要乘 2。公式里的时钟用错，你算的 1 千赫会变成 2 千赫或 500 赫。先问到真实的定时器时钟。
8. 口诀：捕获锁的是 CNT。想要某个频率，先定 PSC，再定 ARR。三个数不要一起拧，拧乱了就不知道是谁的错。
9. 实验输出大约 1 千赫、占空比三成的 PWM。用逻辑分析仪或示波器对一下。对不上时，先核对定时器时钟，再核对 ARR 和 CCR，别先怀疑探头。
10. 合上书，三问。PSC 和 ARR 谁决定频率？CCR 决定什么？输入捕获锁进去的是电压，还是当时的 CNT？

</details>
<!-- /video:ch05 -->

## 学习目标

读这一章之前：读完第 02 章（72 MHz 系统时钟和 APB1 的 36 MHz 是怎么配出来的）、第 03 章（把引脚配成复用推挽，算 LED 的限流电阻）和第 04 章（ISR 和 NVIC 优先级）；会做十进制和十六进制的换算，知道 16 位二进制最大是 65535（不熟的话先读第 00 章的「零基础预备」）。

- [ ] 说清 PSC、ARR、CCR 各管什么，并从 72 MHz 的定时器时钟算出一组 1 kHz 的 PSC 和 ARR
- [ ] 解释 APB1 只有 36 MHz、TIM3 却按 72 MHz 计算的原因，并说出用错时钟会算出多少 Hz
- [ ] 在 PA6 上输出 1 kHz 的 PWM，用逻辑分析仪量出周期 1 ms、高电平 500 µs，再把占空比改成 30%
- [ ] 说出改 ARR 或 CCR 时为什么要开预装载，新值在什么时刻生效
- [ ] 用输入捕获在 PA0 上量出一路 PWM 的周期和高电平宽度
- [ ] 说出 STM32F103C8T6 上有哪几个定时器，哪一个能出互补 PWM，以及它为什么要先置 MOE
- [ ] 说出编码器为什么必须接 A、B 两相，TRGO 怎样让 ADC 按固定间隔采样

## 核心原理

**一句话结论：定时器是一个被时钟推着走的计数器。PSC 决定它数得多快，ARR 决定数到几就回头，CCR 决定输出在一圈里的哪一刻翻转。周期由前两个数定，占空比由第三个数定。**

### 先打个比方

把定时器想成操场上一个踩着节拍器迈步的人。

- **时钟**是节拍器，每秒响 7200 万下。
- **PSC** 规定节拍器响几下才迈一步。PSC = 71，就是响 72 下迈一步，一秒走 100 万步。
- **ARR** 是一圈的步数。ARR = 999，走完第 999 步就回到起点，一圈正好 1000 步，用时 1 毫秒。
- **CCR** 是跑道边插的一面旗。人在旗子前面时灯亮，过了旗子灯灭。旗插在第 500 步，一圈里一半时间亮。
- **输入捕获**是一个看哨声的记录员：哨声一响（引脚上来一个边沿），他就记下这个人此刻走到了第几步。

比方到这里为止。真实的计数器只会整步地数，一圈最多 65536 步（16 位）；改 PSC、ARR、CCR 通常不会马上生效，要等这一圈走完（第 5 节）；旗子插到终点之后（CCR 大于 ARR），灯就一直亮（第 6 节）。

### 1. 定时器是什么：一个自己会数数的计数器

**定时器**（timer）是芯片里一个会自己数数的电路。它的核心是计数器 **CNT**（counter）：每来一个时钟脉冲就加 1，数到上限回到 0 重来。数一圈花的时间是固定的，所以它能计时；在一圈里的某个位置让引脚翻转，就能输出方波。

**时钟**（clock）是一串频率固定的方波，像节拍器，芯片里的数字电路都踩着它工作。定时器用的时钟由 RCC（第 02 章的复位和时钟控制器）送来。

管住这个计数器的是三个寄存器。第 03 章讲过，寄存器是外设里的一格存储，写进去的数决定外设怎么工作：

| 寄存器 | 全称 | 管什么 | 本章的例子 |
| --- | --- | --- | --- |
| PSC | Prescaler，预分频器 | 把定时器时钟除以 PSC + 1，得到计数时钟 | 71：72 MHz ÷ 72 = 1 MHz |
| ARR | Auto-reload register，自动重装载寄存器 | CNT 数到 ARR 就回到 0，一圈是 ARR + 1 拍 | 999：一圈 1000 拍，1 ms |
| CCR | Capture/compare register，捕获/比较寄存器 | 输出 PWM 时是「旗子」的位置；做输入捕获时用来存 CNT | 500：一圈里一半时间是高电平 |

前两行决定频率，第三行只决定占空比。频率不对先查 PSC 和 ARR，亮度不对再查 CCR。注意两个「加 1」：PSC 写的是除数减 1，ARR 写的是一圈拍数减 1。

CNT 从 ARR 回到 0 的那一刻叫**更新事件**（update event，UEV），也常叫溢出。它可以触发中断（第 04 章），也可以触发 DMA（第 10 章），还可以给 ADC 送一拍（第 10 节）。

```text
定时器时钟 72 MHz ──▶ PSC = 71（÷72）──▶ 计数时钟 1 MHz ──▶ CNT：0, 1, 2 … 999, 0, 1 …
                                                                  │
                                            每次从 999 回到 0 ──▶ 更新事件，1 ms 一次

CNT
999 |      /|      /|      /|
    |    /  |    /  |    /  |
    |  /    |  /    |  /    |
  0 +-/-----+-/-----+-/-----+----▶ 时间
      |<- 1 ms ->|
```

### 2. 这颗芯片上有哪些定时器

**结论：STM32F103C8T6 能输出 PWM 的定时器只有四个：高级定时器 TIM1，通用定时器 TIM2、TIM3、TIM4，全是 16 位。**

DS5319 Rev 20 第 2.3.15 节和表 4（第 17 页）列出了这颗料的全部定时器：

| 类别 | C8 上有 | 位宽 | 特点 | 典型用途 |
| --- | --- | --- | --- | --- |
| 高级定时器 | TIM1 | 16 位 | 4 个通道，其中 3 对带互补输出；有死区和刹车；输出前要置 MOE | 电机、半桥和全桥驱动 |
| 通用定时器 | TIM2、TIM3、TIM4 | 16 位 | 每个 4 个通道：PWM、输入捕获、编码器 | PWM 调光、测频、读编码器、定时中断 |
| 看门狗 | IWDG、WWDG | 12 位、7 位 | 程序跑飞时复位芯片，第 11 章细讲 | 防止死机 |
| 系统定时器 | SysTick | 24 位 | Cortex-M3 内核自带 | HAL 的 1 ms 节拍、RTOS 的节拍 |

这张表从上往下看：要互补 PWM 只能用第一行的 TIM1；普通 PWM、测频、编码器用第二行；后两行不往引脚上输出波形。表里的位宽说的是计数器，TIM1–TIM4 的预分频器也是 16 位，可以除以 1 到 65536 之间的任意整数（同一张表）。

别的教程里常见的 TIM5–TIM8 在容量更大的 F103 上才有（RM0008 把它们和 TIM1–TIM4 写在同一本手册里）：TIM6、TIM7 是只会计数、不接引脚的**基本定时器**，TIM8 是第二个高级定时器。C8 上一个都没有，照抄大容量型号的例程去用 TIM6 是行不通的。32 位的 TIM2、TIM5 出现在 STM32F4 等系列上（RM0090 Rev 22 第 18.2 节）；换到那些系列时，「这颗料的定时器都是 16 位」这一句作废。

按需求挑定时器，在 C8 上可以这样分：

| 需求 | 在 C8 上用 |
| --- | --- |
| 普通 PWM、定时中断 | TIM2–TIM4 |
| 互补 PWM、带死区 | TIM1 |
| 只要一个时基 | TIM2–TIM4 里空着的那一个，或者 SysTick |
| 很长的定时 | 没有 32 位定时器：PSC 和 ARR 配合最长约 59.65 s（第 4 节），再长就在更新中断里数圈 |
| 系统节拍 | SysTick |

同一个定时器同一时刻只有一套 PSC 和 ARR。本章 TIM3 出 PWM，TIM2 做输入捕获，TIM4 做 1 秒的定时中断，三个各干一件事。

### 3. 定时器时钟：APB1 只有 36 MHz，TIM3 却拿到 72 MHz

**结论：APB 总线的预分频不是 1 时，挂在这条总线上的定时器，时钟自动乘 2。按附录 D 的设定，TIM1–TIM4 的定时器时钟都是 72 MHz。**

STM32F103 有两条外设总线：APB1 最高 36 MHz，APB2 最高 72 MHz（DS5319 Rev 20 第 2.3.7 节）。附录 D 把系统时钟配成 72 MHz，APB1 二分频得到 PCLK1 = 36 MHz，APB2 不分频，PCLK2 = 72 MHz。RM0008 Rev 21 第 7.2 节（第 94 页）规定：APB 预分频是 1 时，定时器时钟等于这条总线的时钟；不是 1 时，定时器时钟是总线时钟的 2 倍。

| 定时器 | 挂在哪条总线 | 总线时钟（附录 D） | 总线预分频 | 定时器时钟 |
| --- | --- | --- | --- | --- |
| TIM2、TIM3、TIM4 | APB1 | PCLK1 = 36 MHz | 2 | 36 × 2 = 72 MHz |
| TIM1 | APB2 | PCLK2 = 72 MHz | 1 | 72 MHz，不乘 2 |

这张表按行读：先看定时器挂在哪条总线上（RM0008 Rev 21 第 7.3.7、7.3.8 节，TIM1 的时钟开关在 RCC_APB2ENR，TIM2–TIM4 的在 RCC_APB1ENR），再看那条总线的预分频是不是 1。

两个叫法要分清。**定时器时钟**是 RCC 送进定时器的时钟，RM0008 的时钟树里叫 TIMxCLK，也就是预分频器的输入 CK_PSC，本章是 72 MHz。**计数时钟** CK_CNT 是 PSC 分频之后、真正推着 CNT 加 1 的时钟，PSC = 71 时是 1 MHz（RM0008 Rev 21 第 15.4.11 节）。

时钟弄错，算出来的频率会差整数倍。PSC = 71、ARR = 999 这一组数：

- 拿 PCLK1 的 36 MHz 去算，纸面上是 500 Hz，示波器上却是 1000 Hz。
- 反过来按 36 MHz 选参数：想要 1 kHz 就选了 PSC = 35，示波器上是 2000 Hz。
- 忘了调用 `SystemClock_Config()`：芯片停在复位后的 8 MHz 内部 RC 振荡器（HSI）上（DS5319 Rev 20 第 2.3.7 节），APB1 不分频、定时器不乘 2，定时器时钟只有 8 MHz，同一组数输出约 111 Hz。

所以算 PWM 之前，先问清楚定时器时钟是多少。

### 4. 时基公式：先定 PSC，再定 ARR

**结论：先挑一个好算的计数时钟（选 PSC），再用「周期 × 计数时钟」算出一圈要多少拍（得到 ARR + 1）。两个数都不能超过 16 位。**

三条公式，`fCK_PSC` 是定时器时钟（本章 72 MHz），`fCK_CNT` 是计数时钟：

```text
计数时钟    fCK_CNT = fCK_PSC / (PSC + 1)
一圈的时间  T       = (PSC + 1) × (ARR + 1) / fCK_PSC
频率        f       = fCK_PSC / ((PSC + 1) × (ARR + 1))
```

第一条出自 RM0008 Rev 21 第 15.4.11 节；后两条是在它的基础上再数 ARR + 1 拍（第 15.3.2 节：向上计数时 CNT 从 0 数到 ARR 再回到 0）。

动手算一遍 1 ms：

1. 选 PSC = 71，计数时钟 `72 MHz / 72 = 1 MHz`，CNT 每 1 µs 加 1。
2. 一圈要 `1 ms × 1 MHz = 1000` 拍，ARR + 1 = 1000，ARR = 999。
3. 检查：71 和 999 都没超过 65535，能装下。

72 MHz 下常用的几组数：

| 目标周期 | PSC | ARR | 计数时钟 | 实际周期 | 频率 |
| --- | --- | --- | --- | --- | --- |
| 1 ms | 71 | 999 | 1 MHz | 1.000 ms | 1 kHz |
| 10 ms | 7199 | 99 | 10 kHz | 10.00 ms | 100 Hz |
| 100 ms | 7199 | 999 | 10 kHz | 100.0 ms | 10 Hz |
| 1 s | 7199 | 9999 | 10 kHz | 1.000 s | 1 Hz |
| 1 s（大 ARR） | 71 | 999999 | 1 MHz | 装不下 | 这颗料的 TIM2–TIM4 是 16 位，ARR 最大 65535，装不下 999999。能装下的 1 秒是上一行 PSC = 7199、ARR = 9999 |

每一行都能用 `72e6 / ((PSC + 1) × (ARR + 1))` 复算。前四行可以直接抄；最后一行是反面例子：计数时钟选得太快，一秒要数一百万拍，16 位的 ARR 装不下。

PSC 和 ARR 都拉满时，一圈最长是 `65536 × 65536 / 72e6 ≈ 59.65 s`。再长的时间，就在更新中断里数圈。

### 5. 计数模式与影子寄存器

**结论：本章只用向上计数。PSC、ARR、CCR 写进去之后，默认要等这一圈走完（更新事件）才生效，这样波形不会在半圈里变形。**

CNT 有三种走法（RM0008 Rev 21 第 15.3.2 节）：

| 模式 | CNT 怎么走 | 一圈多少拍 | 更新事件在哪 |
| --- | --- | --- | --- |
| 向上计数 | 0 → ARR，再从 0 开始 | ARR + 1 | 从 ARR 回到 0（上溢） |
| 向下计数 | ARR → 0，再从 ARR 开始 | ARR + 1 | 从 0 回到 ARR（下溢） |
| 中央对齐 | 0 → ARR − 1 后上溢，ARR → 1 后下溢，再从 0 开始 | 2 × ARR | 上溢和下溢都有 |

前两种的一圈都是 ARR + 1 拍，第 4 节的公式直接能用。中央对齐让 PWM 的高电平落在一圈的正中间，电机控制常用；它一圈是 2 × ARR 拍，频率要按 `fCK_CNT / (2 × ARR)` 算。同样是 PSC = 71、ARR = 999，中央对齐只有 `1e6 / 1998 ≈ 500.5` Hz。

再说「什么时候生效」。PSC、ARR、CCR 各有两层：你读写的是**预装载寄存器**（preload register），真正参与计数和比较的是背后的**影子寄存器**（shadow register）。更新事件到来时，硬件把预装载的值搬进影子寄存器：

| 寄存器 | 新值什么时候生效 | 由哪一位控制 | 出处（RM0008 Rev 21） |
| --- | --- | --- | --- |
| PSC | 总是等下一次更新事件 | 没有开关，固定带缓冲 | 第 15.3.1 节 |
| ARR | ARPE = 1：等更新事件；ARPE = 0：立刻 | TIMx_CR1 的 ARPE | 第 15.4.1 节 |
| CCRx | OCxPE = 1：等更新事件；OCxPE = 0：立刻 | TIMx_CCMRx 的 OCxPE | 第 15.4.7 节 |

这张表告诉你改数之后多久能在示波器上看到变化：开着预装载，最多等一圈。为什么要等：假设 CNT 正走到 400，你把 CCR 从 300 改成 500。不等的话，比较结果立刻从「CNT ≥ CCR」变回「CNT < CCR」，这一圈里会多出一个 100 µs 的窄脉冲。第 15.4.7 节说得更硬：除了单脉冲模式，PWM 不开 CCR 预装载时，行为没有保证。

刚初始化完，影子寄存器里还是复位值。往 TIMx_EGR 的 UG 位写 1，可以手动产生一次更新事件，把新值一次搬进去（第 15.3.9 节要求启动计数器前这样做）。用 HAL 时，`HAL_TIM_PWM_Init()` 替你写了 UG，`HAL_TIM_PWM_ConfigChannel()` 替你置了 OCxPE；这两点出自 STM32CubeF1 的 HAL 源码，手册里没有。

### 6. PWM 模式：CCR 决定在哪里翻

**结论：PWM 模式 1 下，CNT 比 CCR 小时输出有效电平，否则输出无效电平。有效电平设成高时，占空比 = CCR / (ARR + 1)。**

**PWM**（pulse width modulation，脉宽调制）是频率不变、只改高电平宽度的方波。一圈里高电平占的比例叫**占空比**（duty cycle）。LED 亮度、电机转速都可以用占空比来调。

每个通道里有一个比较器，一直拿 CNT 和 CCR 比，比较结果变成芯片内部的参考信号 OCxREF。TIMx_CCMRx 的 OCxM 位选比较的规则（RM0008 Rev 21 第 15.4.7 节）：

| 模式 | OCxM | 向上计数时 OCxREF | CCR = 300、ARR = 999 时的高电平 |
| --- | --- | --- | --- |
| PWM 模式 1 | 110 | CNT < CCR 时为 1，否则为 0 | CNT 0 到 299，共 300 µs，30% |
| PWM 模式 2 | 111 | CNT < CCR 时为 0，否则为 1 | CNT 300 到 999，共 700 µs，70% |

两种模式互为反相，同一个 CCR 在模式 2 下得到的是「1 减去模式 1 的占空比」。本章都用模式 1。

OCxREF 送到引脚前还要过一道极性选择：TIMx_CCER 的 CCxP = 0 原样输出（HAL 的 `TIM_OCPOLARITY_HIGH`），CCxP = 1 反相输出；CCxE = 1 才真正把波形送到脚上。所以「模式 2」和「模式 1 加反相」在引脚上是同一个波形。

```text
fPWM  = fCK_PSC / ((PSC + 1) × (ARR + 1))
Duty  = CCR / (ARR + 1)           （PWM 模式 1，向上计数，CCxP = 0）
高电平时间 = CCR / fCK_CNT
```

两个端点要记住（第 15.3.9 节，第 388 页的图 130 用 ARR = 8 画了这几种情况）：CCR = 0 时输出一直是低，占空比 0%；CCR 大于 ARR 时输出一直是高，占空比 100%。ARR = 999 时，CCR 从 0 走到 1000，占空比从 0% 走到 100%，一共 1001 档。

### 7. 频率和分辨率：不能两头都要

**结论：定时器时钟固定时，PWM 频率越高，一圈里的拍数（ARR + 1）越少，占空比能调的档位就越少。**

一圈有多少拍，占空比就有多少档，所以分辨率是 `1 / (ARR + 1)`。下表的定时器时钟都是 72 MHz：

| 目标 PWM 频率 | PSC | ARR + 1 | 占空比分辨率 | 说明 |
| --- | --- | --- | --- | --- |
| 1 kHz | 1 | 36000 | 1/36000 | 另一组高分辨率参数（PSC = 1 时 ARR + 1 = 36000，ARR = 35999）。不是附录 D 的 1 kHz 格子（PSC = 71，ARR = 999），那一格的分辨率是 1/1000 |
| 10 kHz | 0 | 7200 | 1/7200 | 常见的电机 PWM 频率（经验值） |
| 20 kHz | 0 | 3600 | 1/3600 | 多数人听不到 20 kHz 以上的声音（经验值），电机不再发出尖叫 |
| 50 Hz（舵机） | 71 | 20000 | 1/20000，每档 1 µs | ARR = 19999；舵机常用 1–2 ms 的高电平（经验值），对应 CCR = 1000–2000 |

看第二、三列：`(PSC + 1) × (ARR + 1)` 总是等于 `72e6 / f`。PSC 越小，留给 ARR 的拍数越多，档位越细。

1 kHz 那一行为什么不用 PSC = 0：那样 ARR + 1 要等于 72000，超过了 16 位能装的 65536。PSC = 0 时一圈最多 65536 拍，频率最低只能到 `72e6 / 65536 ≈ 1099` Hz，所以要 1 kHz，PSC 最小是 1。

### 8. 输入捕获：把边沿那一刻的 CNT 记下来

**结论：输入捕获不量电压。引脚上来一个边沿，硬件把那一刻的 CNT 抄进 CCRx。两次抄下的数相减，就是两个边沿之间隔了多少拍。**

通道配成输入时，CCRx 就变成只读的「记录本」（RM0008 Rev 21 第 15.3.5 节，第 384 页）：

- 选定的边沿到来时，CCRx 存下当时的 CNT，标志位 CCxIF 置 1，开了中断就进 ISR。
- 读一次 CCRx，CCxIF 就自动清零。
- 上一次的值还没读走，又来了一次捕获，过捕获标志 CCxOF 置 1，说明中间丢了一次。

量一路 PWM 要两个时刻：上升沿量周期，下降沿量高电平。一只引脚可以同时喂给两个通道：CH1 直接接 TI1（PA0），抓上升沿；CH2 把 CC2S 设成 10，也接 TI1，抓下降沿（第 15.4.7 节）。这就是第 15.3.6 节「PWM 输入模式」的前一半，只是不让计数器在上升沿清零，改用减法。

```text
PA0   ___|‾‾‾‾‾‾‾|____________|‾‾‾‾‾‾‾|______
         ↑       ↓            ↑
CNT     1200    1500         2200
        CH1     CH2          CH1

周期   = 2200 − 1200 = 1000 拍 = 1000 µs（计数时钟 1 MHz）
高电平 = 1500 − 1200 =  300 拍 =  300 µs，占空比 30%
```

CNT 是 16 位的，到 65535 会回到 0。用 16 位无符号减法，回零一次也能算对：上升沿分别在 65000 和 464 时，`(uint16_t)(464 − 65000) = 1000`。回零两次就算错了，所以计数时钟 1 MHz 时，被测的间隔要短于 65536 µs，约 65.5 ms。要量更慢的信号，加大 PSC，或者在更新中断里数回零的次数。

### 9. 编码器接口：A、B 两相数位置

**结论：编码器模式让计数器跟着 A、B 两相的边沿自己加减，CNT 就是位置。两相必须都接，硬件靠 A、B 谁先谁后判断方向。**

**增量式编码器**（incremental encoder）转动时输出两路方波，A 相和 B 相错开四分之一个周期。正交编码看两相：B 比 A 落后约 90° 是一个方向，超前是另一个方向。只有一路方波时，硬件分不清正反转。

```text
A   __|‾‾‾‾|____|‾‾‾‾|____
B   ____|‾‾‾‾|____|‾‾‾‾|__     B 落后 A 四分之一周期：一个方向
CNT   每个边沿加 1，A 的一个周期里加 4（SMS = 011）
```

TIMx_SMCR 的 SMS 设成 011，计数器在 TI1、TI2 两路的上升沿和下降沿都计数，A 的一个周期计 4 次；方向由 TIMx_CR1 的 DIR 位给出（RM0008 Rev 21 第 15.3.12 节，第 392 页）。C8 上 TIM1–TIM4 都能做编码器，比如 TIM2 用 PA0、PA1（LQFP48 第 10、11 脚），TIM4 用 PB6、PB7（第 42、43 脚）（DS5319 Rev 20 第 2.3.15 节和表 5；TIM1 见 RM0008 Rev 21 第 14.3.16 节）。

只接 A 相会怎样，第 15.3.12 节的表 85 给了答案：B 相停在一个固定电平时，A 的上升沿和下降沿一个让 CNT 加 1、一个让它减 1，计数只在两个相邻的数之间来回跳，不累加，正转反转看起来一样。

### 10. 主模式与 TRGO：给 ADC 打拍子

**结论：TRGO（trigger output，触发输出）是定时器往外送的一根内部信号线。把「更新事件」选作 TRGO，定时器每转一圈就给 ADC 或另一个定时器送一拍，采样间隔由硬件保证，和主循环忙不忙无关。**

TIMx_CR2 的 MMS 位选 TRGO 送什么，010 是更新事件（RM0008 Rev 21 第 15.4.2 节，第 406 页）。ADC1 的外部触发 EXTSEL 选 100，就是 TIM3 的 TRGO（第 11.12.3 节，第 240 页）。TIM3 用 PSC = 71、ARR = 999 时每 1 ms 更新一次，ADC 就每 1 ms 转换一次；PA6 上的 1 kHz PWM 照样输出，两件事用的是同一个计数器。

```c
/* TIM3 每次更新都从 TRGO 送出一拍；第 09 章把 ADC1 的外部触发选成 TIM3_TRGO */
TIM_MasterConfigTypeDef mst = {0};
mst.MasterOutputTrigger = TIM_TRGO_UPDATE;          /* MMS = 010：更新事件当 TRGO */
mst.MasterSlaveMode     = TIM_MASTERSLAVEMODE_DISABLE;
HAL_TIMEx_MasterConfigSynchronization(&htim3, &mst);
```

ADC 那一边在第 09 章配：外部触发选 `ADC_EXTERNALTRIGCONV_T3_TRGO`。不要在主循环里用软件一次次启动转换，主循环一忙，采样间隔就跟着抖。

反过来，定时器也可以当**从机**：从模式控制器按外部信号或别的定时器的 TRGO，把计数器清零、门控或启动（第 15.3.14、15.3.15 节）。测周期、多个定时器同步启动都靠它。

口诀：**捕获锁的是 CNT，TRGO 送的是节拍；编码器必须有 A 和 B。**

### 11. 互补输出与死区：只有 TIM1 有

**结论：互补输出是一对反相的 PWM，分别驱动半桥的上管和下管；死区是两管换班时故意留出的「两个都关」的空档，防止上下管同时导通把电源短路。这一套在 C8 上只有 TIM1 有，而且 TIM1 不置 MOE 就没有任何输出。**

**半桥**是两个开关管串在电源和地之间，中点接负载。上管导通时中点接电源，下管导通时中点接地。两个管子同时导通，电源就被直接短路，这叫**直通**。

| 概念 | 说明 | 出处 |
| --- | --- | --- |
| 互补输出 | CH1 和 CH1N 一对，一个高时另一个低；TIM1 有 3 对（CH1–CH3），CH4 没有互补 | DS5319 Rev 20 第 2.3.15 节 |
| 死区 | 一路关断后等一小段时间，再打开另一路；长度由 TIMx_BDTR 的 DTG[7:0] 设定 | RM0008 Rev 21 第 14.4.18 节 |
| 刹车 | BKIN 脚一有效，硬件立刻把 MOE 清零，输出关断或回到设定的空闲电平 | 同上 |
| MOE | TIMx_BDTR 位 15，主输出使能；寄存器偏移 0x44，复位值 0x0000，不置 1 就没有输出 | 同上 |

这张表从上往下是一条因果链：互补输出带来了直通的风险，死区和刹车用来防它，MOE 是这一切的总开关。C8 上 TIM1_CH1 在 PA8（LQFP48 第 29 脚），TIM1_CH1N 在 PB13（第 26 脚），TIM1_BKIN 在 PB12（第 25 脚）（DS5319 Rev 20 表 5）。

TIM1 的额外一步：

```c
/* TIM1 是高级定时器：BDTR 里的 MOE 不置 1，CH1（PA8）上就没有波形 */
HAL_TIM_PWM_Start(&htim1, TIM_CHANNEL_1);   /* HAL 在这里顺手置了 MOE */
/* 寄存器写法：TIM1->BDTR |= TIM_BDTR_MOE; */
/* HAL 另有一个宏做同一件事：__HAL_TIM_MOE_ENABLE(&htim1); */
```

配死区和互补输出：

```c
/* TIM1 的死区与刹车，数值是例程设定 */
TIM_BreakDeadTimeConfigTypeDef bd = {0};
bd.OffStateRunMode  = TIM_OSSR_ENABLE;
bd.OffStateIDLEMode = TIM_OSSI_ENABLE;
bd.LockLevel        = TIM_LOCKLEVEL_OFF;
bd.DeadTime         = 0x10;                     /* 写进 BDTR 的 DTG[7:0]，例程设定 */
bd.BreakState       = TIM_BREAK_DISABLE;
bd.BreakPolarity    = TIM_BREAKPOLARITY_HIGH;
bd.AutomaticOutput  = TIM_AUTOMATICOUTPUT_DISABLE;
HAL_TIMEx_ConfigBreakDeadTime(&htim1, &bd);
HAL_TIM_PWM_Start(&htim1, TIM_CHANNEL_1);       /* CH1：PA8 */
HAL_TIMEx_PWMN_Start(&htim1, TIM_CHANNEL_1);    /* CH1N：PB13 */
```

DTG 换算成时间是分段的，第 14.4.18 节给了四段公式，结果还和 TIMx_CR1 的 CKD 位有关。上面的 0x10 只是例程设定，本书不把它换成纳秒。接真实的桥之前，按 MOSFET 驱动器的数据手册定死区，再用示波器量两路的间隔。

## 硬件与接线

| 开发板 | 外设 | 引脚 | 备注 |
| --- | --- | --- | --- |
| BluePill | LED（PWM 调光） | PA6（TIM3_CH1，LQFP48 第 16 脚） | PA6 串 270 Ω（例程设定）到 LED 正极，负极接 GND；高电平点亮 |
| BluePill | 输入捕获 | PA0（TIM2_CH1，LQFP48 第 10 脚） | 实验三用杜邦线把 PA6 接到 PA0；也可以接信号发生器 |
| BluePill | 板载 LED | PC13 | 1 秒定时中断的例子用，低电平点亮（第 03 章） |
| 逻辑分析仪或示波器 | 测量 | 通道 0 接 PA6，通道 1 接 PA0，地线接 GND | 采样率 1 MHz 以上就能看清 1 kHz 的波形（经验值） |

```text
PWM 调光：PA6 ──[270 Ω]──▶|── GND        高电平点亮，占空比越大越亮
输入捕获：PA6 ──────────────── PA0        实验三的跳线，两只脚都在同一块板上
测量：    逻辑分析仪 CH0 ── PA6，CH1 ── PA0，GND ── GND
```

脚号出自 DS5319 Rev 20 表 5。按第 03 章第 4 节的算法，红色 LED 的 Vf 按 2.0 V 估（经验值），电流约 `(3.3 − 2.0) / 270 ≈ 4.8 mA`。接信号发生器时，幅度设成 0 到 3.3 V：PA0 和 PA6 都不是 5 V 容忍脚，表 5 里它们的类型是 I/O，不是 FT。

## 代码实现

下面的 `timer_pwm.c` 对应实验一和实验二：TIM3_CH1（PA6）输出 1 kHz 的 PWM，把 `LAB_BREATHE` 改成 1 就变成呼吸灯。

```c
/* timer_pwm.c —— TIM3_CH1（PA6）输出 1 kHz PWM；LAB_BREATHE = 1 时做呼吸灯 */
#include "stm32f1xx_hal.h"

#define LAB_BREATHE  0           /* 0：实验一，固定占空比；1：实验二，呼吸灯 */

#define PWM_TIM      TIM3
#define PWM_CH       TIM_CHANNEL_1
#define PWM_PSC      71          /* 72 MHz / (71 + 1) = 1 MHz 计数时钟 */
#define PWM_ARR      999         /* 1 MHz / (999 + 1) = 1 kHz PWM */

TIM_HandleTypeDef htim3;

void SystemClock_Config(void);

static void pwm_init(void)
{
    __HAL_RCC_TIM3_CLK_ENABLE();
    __HAL_RCC_GPIOA_CLK_ENABLE();

    /* PA6 复用推挽（TIM3_CH1） */
    GPIO_InitTypeDef io = {0};
    io.Pin   = GPIO_PIN_6;
    io.Mode  = GPIO_MODE_AF_PP;
    io.Speed = GPIO_SPEED_FREQ_HIGH;
    HAL_GPIO_Init(GPIOA, &io);

    htim3.Instance               = PWM_TIM;
    htim3.Init.Prescaler         = PWM_PSC;
    htim3.Init.CounterMode       = TIM_COUNTERMODE_UP;
    htim3.Init.Period            = PWM_ARR;          /* Period 就是 ARR */
    htim3.Init.ClockDivision     = TIM_CLOCKDIVISION_DIV1;
    htim3.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_ENABLE;
    HAL_TIM_PWM_Init(&htim3);

    TIM_OC_InitTypeDef oc = {0};
    oc.OCMode     = TIM_OCMODE_PWM1;
    oc.Pulse      = 500;                             /* CCR = 500。500 / (ARR + 1) = 50%，高电平 500 µs */
    oc.OCPolarity = TIM_OCPOLARITY_HIGH;
    oc.OCFastMode = TIM_OCFAST_DISABLE;
    HAL_TIM_PWM_ConfigChannel(&htim3, &oc, PWM_CH);

    HAL_TIM_PWM_Start(&htim3, PWM_CH);               /* 启动 PWM 输出 */
}

int main(void)
{
    HAL_Init();
    SystemClock_Config();
    pwm_init();                                      /* 从这一刻起，PA6 上是 1 kHz、50% */

#if LAB_BREATHE
    int16_t duty = 0;
    int16_t step = 10;
#endif

    while (1)
    {
#if LAB_BREATHE
        duty += step;
        if (duty >= PWM_ARR || duty <= 0) step = -step;           /* 0→100% 往返 */
        __HAL_TIM_SET_COMPARE(&htim3, PWM_CH, (uint32_t)duty);    /* 改 CCR，下一圈生效 */
        HAL_Delay(10);
#endif
    }
}
```

逐段看：

- `PWM_PSC 71`：72 MHz ÷ (71 + 1) = 1 MHz，CNT 每 1 µs 加 1。PSC 写的是除数减 1，这是最常见的差一错误。
- `PWM_ARR 999`：一圈 1000 拍，1 ms，1 kHz。`htim3.Init.Period` 就是 ARR，HAL 换了个名字。
- `GPIO_MODE_AF_PP`：PA6 交给定时器驱动，要配成复用推挽（RM0008 Rev 21 表 23：定时器的输出比较通道用复用推挽）。配成普通推挽输出，引脚只听 ODR 的，看不到 PWM。
- `AutoReloadPreload = ENABLE`：ARPE = 1，改 ARR 要等这一圈走完才生效（第 5 节）。
- `oc.Pulse = 500`：CCR = 500，占空比 50%。`TIM_OCPOLARITY_HIGH` 是 CC1P = 0，有效电平为高。
- `HAL_TIM_PWM_ConfigChannel()` 写 OC1M = 110（PWM 模式 1）并置 OC1PE；`HAL_TIM_PWM_Start()` 置 CC1E 把波形送到脚上，再置 CEN 开始计数。这两点出自 HAL 源码。
- `__HAL_TIM_SET_COMPARE()` 直接写 CCR1。开着预装载，新值在下一次更新事件生效，正在走的这一圈不会被切坏。
- 呼吸循环每 10 ms 把 CCR 加减 10（例程设定）：100 步从 0 走到 1000，变亮、变暗各用 1 s。CCR 走到 1000，也就是 ARR + 1 时，占空比是 100%。
- `SystemClock_Config()` 用第 02 章写好的那一份，配出来的数值和附录 D「时钟树」一行相同：HSE 8 MHz，PLL ×9 得到 72 MHz，APB1 二分频。漏掉它，定时器只拿到 8 MHz，频率变成约 111 Hz。

同一件事的寄存器写法，把 HAL 替你做的事摊开（位名出自 RM0008 Rev 21 第 15.4 节）：

```c
/* TIM3_CH1 在 PA6 上输出 1 kHz、50% 的 PWM，寄存器写法 */
RCC->APB1ENR |= RCC_APB1ENR_TIM3EN;
RCC->APB2ENR |= RCC_APB2ENR_IOPAEN;
GPIOA->CRL = (GPIOA->CRL & ~(0xFU << 24)) | (0xBU << 24);  /* PA6：MODE = 11，CNF = 10，复用推挽 */
TIM3->PSC   = 71;                                          /* 72 MHz / 72 = 1 MHz */
TIM3->ARR   = 999;                                         /* 一圈 1000 拍 = 1 kHz */
TIM3->CCR1  = 500;                                         /* 50% */
TIM3->CCMR1 = TIM_CCMR1_OC1M_2 | TIM_CCMR1_OC1M_1          /* OC1M = 110：PWM 模式 1 */
            | TIM_CCMR1_OC1PE;                             /* 打开 CCR1 预装载 */
TIM3->CCER  = TIM_CCER_CC1E;                               /* CC1P = 0 高电平有效；CC1E = 1 输出到脚 */
TIM3->CR1   = TIM_CR1_ARPE;                                /* ARR 也走预装载 */
TIM3->EGR   = TIM_EGR_UG;                                  /* 手动产生一次更新，把新值搬进影子寄存器 */
TIM3->CR1  |= TIM_CR1_CEN;                                 /* 开始计数 */
```

最容易漏的是最后三步里的 UG。不写它，PSC、ARR 和 CCR1 的影子寄存器都还是复位值，要等第一次溢出才换成新值，第一圈的波形是错的。

实验三要用的输入捕获放在单独的 `capture.c` 里：TIM2 在 PA0 上同时抓上升沿和下降沿。

```c
/* capture.c —— TIM2 在 PA0 上量一路 PWM：CH1 抓上升沿，CH2 抓同一只脚的下降沿 */
#include "stm32f1xx_hal.h"

TIM_HandleTypeDef htim2;

volatile uint16_t g_period;            /* 周期，单位 µs（计数时钟 1 MHz，1 拍 = 1 µs） */
volatile uint16_t g_high;              /* 高电平宽度，单位 µs */
static volatile uint16_t s_rise;       /* 最近一次上升沿时的 CNT */

void capture_init(void)
{
    __HAL_RCC_TIM2_CLK_ENABLE();
    __HAL_RCC_GPIOA_CLK_ENABLE();

    GPIO_InitTypeDef io = {0};
    io.Pin  = GPIO_PIN_0;              /* PA0 = TIM2_CH1，浮空输入 */
    io.Mode = GPIO_MODE_INPUT;
    io.Pull = GPIO_NOPULL;
    HAL_GPIO_Init(GPIOA, &io);

    htim2.Instance           = TIM2;
    htim2.Init.Prescaler     = 71;     /* 72 MHz / 72 = 1 MHz，1 拍 1 µs */
    htim2.Init.CounterMode   = TIM_COUNTERMODE_UP;
    htim2.Init.Period        = 0xFFFF; /* CNT 走满 16 位，65.536 ms 回一次 0 */
    htim2.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
    HAL_TIM_IC_Init(&htim2);

    TIM_IC_InitTypeDef ic = {0};
    ic.ICPrescaler = TIM_ICPSC_DIV1;   /* 每个边沿都捕获 */
    ic.ICFilter    = 0;                /* 不滤波 */

    ic.ICPolarity  = TIM_INPUTCHANNELPOLARITY_RISING;
    ic.ICSelection = TIM_ICSELECTION_DIRECTTI;      /* CH1 看 TI1，也就是 PA0 */
    HAL_TIM_IC_ConfigChannel(&htim2, &ic, TIM_CHANNEL_1);

    ic.ICPolarity  = TIM_INPUTCHANNELPOLARITY_FALLING;
    ic.ICSelection = TIM_ICSELECTION_INDIRECTTI;    /* CH2 也看 TI1：同一只脚的下降沿 */
    HAL_TIM_IC_ConfigChannel(&htim2, &ic, TIM_CHANNEL_2);

    HAL_NVIC_SetPriority(TIM2_IRQn, 2, 0);          /* 抢占 2，例程设定 */
    HAL_NVIC_EnableIRQ(TIM2_IRQn);
    HAL_TIM_IC_Start_IT(&htim2, TIM_CHANNEL_1);
    HAL_TIM_IC_Start_IT(&htim2, TIM_CHANNEL_2);
}

void TIM2_IRQHandler(void)
{
    HAL_TIM_IRQHandler(&htim2);
}

void HAL_TIM_IC_CaptureCallback(TIM_HandleTypeDef *htim)
{
    if (htim->Instance != TIM2)
    {
        return;
    }
    if (htim->Channel == HAL_TIM_ACTIVE_CHANNEL_1)          /* 上升沿 */
    {
        uint16_t now = (uint16_t)HAL_TIM_ReadCapturedValue(htim, TIM_CHANNEL_1);
        g_period = (uint16_t)(now - s_rise);   /* 16 位减法：CNT 回零一次也算得对 */
        s_rise   = now;
    }
    else if (htim->Channel == HAL_TIM_ACTIVE_CHANNEL_2)     /* 下降沿 */
    {
        uint16_t now = (uint16_t)HAL_TIM_ReadCapturedValue(htim, TIM_CHANNEL_2);
        g_high = (uint16_t)(now - s_rise);
    }
}
```

实验三把 `timer_pwm.c` 的 `main()` 换成下面这一版，再把 `capture.c` 加进工程：

```c
/* 实验三：PA6 输出 30% 的 1 kHz PWM，PA0 量它 */
void capture_init(void);

int main(void)
{
    HAL_Init();
    SystemClock_Config();
    pwm_init();                                      /* PA6：1 kHz */
    __HAL_TIM_SET_COMPARE(&htim3, PWM_CH, 300);      /* 占空比改成 30%，下一圈生效 */
    capture_init();                                  /* PA0：量它 */

    while (1)
    {
        /* 暂停程序，在调试器里看 g_period 和 g_high */
    }
}
```

逐段看：

- PA0 配成浮空输入：RM0008 Rev 21 表 23 规定，定时器的输入捕获通道用浮空输入。
- PSC = 71，1 拍 1 µs，读出来的差值直接就是微秒。`Period = 0xFFFF` 让 CNT 走满 16 位，65.536 ms 回一次 0。
- CH1 用 `TIM_ICSELECTION_DIRECTTI` 看 TI1 的上升沿；CH2 用 `TIM_ICSELECTION_INDIRECTTI` 也看 TI1，抓下降沿（CC2S = 10）。一只脚，两个通道，两种边沿。
- 回调里的 `(uint16_t)(now - s_rise)` 是 16 位减法，两次边沿之间 CNT 回零一次，结果照样对（第 8 节）。
- `htim->Channel` 告诉你这次是哪个通道触发的；HAL 在调用回调之前填好它。
- 主循环里一起读 `g_period` 和 `g_high` 时，两个数可能分属相邻的两圈。拿来显示够用；拿来做控制，要像第 04 章第 7 节那样关中断再一起读。

最后是一个定时中断：TIM4 每秒进一次更新中断，翻转 PC13。PC13 按第 03 章配成推挽输出。

```c
/* tim4_1hz.c —— TIM4 每 1 s 产生一次更新中断，翻转 PC13 */
#include "stm32f1xx_hal.h"

TIM_HandleTypeDef htim4;

void tim4_1hz_init(void)
{
    __HAL_RCC_TIM4_CLK_ENABLE();

    htim4.Instance               = TIM4;
    htim4.Init.Prescaler         = 7199;       /* 72 MHz / 7200 = 10 kHz */
    htim4.Init.CounterMode       = TIM_COUNTERMODE_UP;
    htim4.Init.Period            = 9999;       /* 10 kHz / 10000 = 1 Hz */
    htim4.Init.ClockDivision     = TIM_CLOCKDIVISION_DIV1;
    htim4.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_DISABLE;
    HAL_TIM_Base_Init(&htim4);

    HAL_NVIC_SetPriority(TIM4_IRQn, 3, 0);     /* 抢占 3，例程设定 */
    HAL_NVIC_EnableIRQ(TIM4_IRQn);
    HAL_TIM_Base_Start_IT(&htim4);             /* 带 _IT 才会打开更新中断 */
}

void TIM4_IRQHandler(void)
{
    HAL_TIM_IRQHandler(&htim4);
}

void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim)
{
    if (htim->Instance == TIM4)
    {
        HAL_GPIO_TogglePin(GPIOC, GPIO_PIN_13);
    }
}
```

- 为什么用 TIM4：TIM3 在出 PWM，TIM2 在做输入捕获，一个定时器同一时刻只有一套 PSC 和 ARR。
- `HAL_TIM_Base_Start_IT()` 带 `_IT`，会打开 TIMx_DIER 的更新中断使能位 UIE（RM0008 Rev 21 第 15.4.4 节）。换成 `HAL_TIM_Base_Start()`，计数器照样跑，但不会进中断。
- 回调先看 `htim->Instance`：一个工程里所有定时器的更新中断共用这一个回调函数。

完整工程见 [`examples/timer-pwm/`](../examples/timer-pwm/)。

## 动手实验

1. **实验一：1 kHz 方波，先 50% 再 30%。** 保持 `LAB_BREATHE` 为 0，烧录程序，逻辑分析仪接 PA6。量完以后把 `oc.Pulse` 改成 300 重新烧录，或者暂停程序，在调试器的寄存器窗口里把 TIM3_CCR1 改成 300。
   - 预期现象：先是频率 1000 Hz、高电平 500 µs 的方波；改成 300 后，频率不变，高电平变成 300 µs，占空比 30%。LED 的亮度跟着变暗一些。
   - 怎么确认：在逻辑分析仪上量相邻两个上升沿的间隔，应是 1.000 ms；量高电平宽度，应是 500 µs，改后是 300 µs。两个数都能用第 4 节和第 6 节的公式复算。
   - 没成功先查：一点波形都没有，先查 GPIOA 和 TIM3 的时钟、PA6 是不是复用推挽、有没有调用 `HAL_TIM_PWM_Start()`；频率约 111 Hz，是 `SystemClock_Config()` 没跑；频率是 2000 Hz，是 PSC 按 36 MHz 选成了 35。
2. **实验二：呼吸灯。** 把 `LAB_BREATHE` 改成 1，重新烧录。
   - 预期现象：LED 用 1 s 慢慢变亮，再用 1 s 慢慢变暗，循环往复。效果可以对照 `pwm-breath.gif`。
   - 怎么确认：逻辑分析仪上频率一直是 1000 Hz，只有高电平宽度在变，每 10 ms 变 10 µs。
   - 没成功先查：LED 一直亮或一直灭，先查 LED 的正负极和 270 Ω 电阻；能看到明显的闪烁，说明频率掉得太低，回去查定时器时钟。亮度变化看起来不均匀是正常的：人眼对暗处的变化更敏感，0% 到 10% 的变化比 50% 到 60% 明显得多（经验值）。
3. **实验三：用输入捕获量实验一的波形。** 按「代码实现」换好 `main()`，把 `capture.c` 加进工程，用杜邦线把 PA6 接到 PA0。
   - 预期现象：`g_period` 是 1000，`g_high` 是 300，也就是 1 kHz、30%。
   - 怎么确认：暂停程序，在调试器里看这两个变量。两个定时器吃的是同一个 72 MHz，PSC 也一样，读数应该就是 1000 和 300；换成信号发生器，两边时钟不同源，会差一两拍（经验值）。把 CCR 改成 500 再跑一次，`g_high` 应变成 500。
   - 没成功先查：两个数都是 0，先查跳线、`TIM2_IRQHandler` 的拼写和 `HAL_NVIC_EnableIRQ(TIM2_IRQn)`；`g_high` 是 700 左右，是两个通道的边沿配反了；`g_period` 不是 1000 左右，比较 TIM2 和 TIM3 的 PSC，两者都应是 71。

## 自测

1. 用 TIM4 每 0.5 s 进一次更新中断，PSC 取 7199，ARR 该填多少？
2. 一路 25 kHz 的电机 PWM，PSC = 0。ARR 填多少？占空比能分多少档？要 37.5% 时 CCR 填多少？
3. 只捕获了上升沿，能不能算出占空比？能算出什么？
4. ADC 想每 1 ms 转换一次，TIM3 的 TRGO 该选什么事件？PSC 和 ARR 怎么填？ADC 那边选哪个触发源？
5. 编码器只接了 A 相，B 相那只脚开了上拉，一直是高电平。转动转轴时，计数会怎样？

参考答案：

1. 计数时钟 `72e6 / (7199 + 1) = 10 kHz`；0.5 s 要 `0.5 × 10000 = 5000` 拍，ARR = 4999。
2. ARR + 1 = `72e6 / 25e3 = 2880`，ARR = 2879；占空比有 2880 档，分辨率 1/2880；CCR = `0.375 × 2880 = 1080`。
3. 不能。相邻两个上升沿的差只给出周期，也就能算出频率；占空比还要知道下降沿的时刻。实验三用 CH2 抓同一只脚的下降沿，补的就是这一半。
4. 选更新事件（MMS = 010）。PSC = 71、ARR = 999，每 1 ms 更新一次。ADC1 的外部触发选 TIM3 的 TRGO（EXTSEL = 100，HAL 写作 `ADC_EXTERNALTRIGCONV_T3_TRGO`）。
5. 计数只在两个相邻的数之间来回跳，不累加，正转反转看起来一样。按 RM0008 Rev 21 表 85，B 相电平不变时，A 的上升沿和下降沿一个让 CNT 减 1、一个让它加 1，一圈下来互相抵消。

## 原理与适用范围

> [!NOTE]
> 从这一节到「常见坑与出处」是深入部分，把前面的结论落到具体订货号、手册章节和能复算的数字上。第一次读可以先跳过，做完动手实验再回来对照。

**订货号和时钟。**这一章的波形结论只钉在订货号 STM32F103C8T6 上。时钟按附录 D：SYSCLK = 72 MHz，PCLK1 = 36 MHz，PCLK2 = 72 MHz。TIM3 在 APB1，APB1 的预分频是 2，不是 1，所以 TIM3 的定时器时钟是 36 MHz 的 2 倍，也就是 72 MHz（[RM0008 Rev 21](#source-rm0008) 第 7.2 节，第 94 页）。本书算 PWM 一律用 72 MHz 去除，不用 36 MHz。

**1000 Hz 这笔账。**PSC = 71，ARR = 999。`72e6 / ((71+1) × (999+1)) = 1000` Hz。72 MHz 先被 PSC 分成 1 MHz 的计数时钟，CNT 再数 1000 下，一圈 1 ms。同一组 PSC、ARR 拿 36 MHz 去除，算出来是 500 Hz，这就是主图上的失败路径：账算错了，板子上的波形仍是 1000 Hz。只有定时器真的只拿到 36 MHz 时（时钟没有按附录 D 配），示波器上才会是 500 Hz。计数时钟的公式在 [RM0008 Rev 21 第 15 章](#source-rm0008-tim) 的第 15.4.11 节。

**占空比。**同一章第 15.3.9 节：PWM 模式 1、向上计数时，CNT < CCR 输出有效电平。CCR = 500 时，`500 / (999+1) = 50%`，高电平 500 µs。CCR 大于 ARR 时输出一直有效，占空比 100%；CCR = 0 时一直无效，占空比 0%。第 388 页的图 130 用 ARR = 8 画了这几种情况。

**16 位的边界。**这颗料只有 TIM2–TIM4 三个通用定时器，加上高级定时器 TIM1，计数器和预分频器都是 16 位（DS5319 Rev 20 第 2.3.15 节表 4）。PSC = 71、ARR = 999999 装不下：999999 超过 65535，写进去只剩低 16 位。能装下的 1 秒是 PSC = 7199、ARR = 9999，`72e6 / (7200 × 10000) = 1` Hz。32 位的 TIM2、TIM5 是别的系列上的句子（STM32F4 见 RM0090 Rev 22 第 18.2 节）；换到那些系列时，「这颗料是 16 位」这一句作废。

**引脚。**默认不重映射时 TIM3_CH1 在 PA6。DS5319 Rev 20 表 5：LQFP48 第 16 脚是 PA6，默认复用含 TIM3_CH1，同一格也含 SPI1_MISO。本章的图只画定时器；SPI 对这只脚的用法在第 08 章，两章的主图不把两种功能画成同时有效。重映射要另写 AFIO_MAPR 的 `TIM3_REMAP`：部分重映射把 CH1 移到 PB4（第 40 脚，复位后是 JTAG 的 NJTRST）；完全重映射移到 PC6，但 RM0008 Rev 21 表 44（第 178 页）注明完全重映射只在 64 脚及以上的封装上有，LQFP48 没有 PC6。两种都不画进正常路径。出处是 [DS5319 Rev 20 表 5](#source-ds5319-tim)。

**MOE 只属于 TIM1。**TIM1 的 `TIMx_BDTR` 偏移 `0x44`，复位值 `0x0000`；位 15 MOE 为 0 时主输出关着，OC 和 OCN 都不出波形（[RM0008 Rev 21](#source-rm0008-tim) 第 14.4.18 节，手册里 TIM1 和 TIM8 共用这一节）。刹车输入一有效，硬件立刻把 MOE 清零。`HAL_TIM_PWM_Start` 会置 MOE，这一点出自 STM32CubeF1 的 HAL 源码。通用定时器 TIM3 没有这个寄存器，PA6 上的波形和 MOE 无关。

**改数什么时候生效。**PSC 一直带缓冲，新值等下一次更新事件才生效（第 15.3.1 节）；ARR 在 ARPE = 1 时、CCR 在 OCxPE = 1 时也一样（第 15.4.1 节、第 15.4.7 节）。第 15.4.7 节还写明：除了单脉冲模式，PWM 不开 CCR 预装载时，行为没有保证。

## 关键插图

<p align="center">
  <img src="../assets/diagrams/sample-05-pwm-1khz.svg" width="760" alt="定时器时钟 72 MHz 时这组 PSC/ARR 是 1 kHz；改用 36 MHz 去除得到 500 Hz">
  <br><sub>▲ 自绘。STM32F103C8T6，LQFP48 第 16 脚 PA6 = TIM3_CH1。定时器时钟 72 MHz（图中写作「计数时钟」），PSC = 71，ARR = 999，CCR = 500。正常路径周期 1 ms，高电平 500 µs，频率 1000 Hz。失败路径拿 36 MHz 去除，算出周期 2 ms、频率 500 Hz。ARR = 999999 在 16 位计数器里装不下。TIM1 的 MOE 在偏移 0x44，复位值 0x0000，不占这条波形。SPI1_MISO 不画进这条波形。出处是 [RM0008 Rev 21 第 15 章](#source-rm0008-tim) 和 [DS5319 Rev 20 表 5](#source-ds5319-tim)。</sub>
</p>

**怎么读这张图。**图上有三段。正常路径：CNT 从 0 数到 499 时输出高，500 到 999 时输出低，一圈 1000 µs，频率 1000 Hz。失败路径：同一组 PSC、ARR、CCR，拿 36 MHz 去除，算出 2000 µs、500 Hz，多出来的那一倍来自把 PCLK1 当成了定时器时钟。旁注：16 位装不下 999999，能装下的 1 秒是 PSC = 7199、ARR = 9999；TIM1 的 MOE 是另一个定时器的事，不占 PA6。图里的「计数时钟 72 MHz」指的是 PSC 之前的定时器时钟；按 RM0008 的叫法，计数时钟是分频后的 1 MHz，图里「计数时钟先被分成 1 MHz」这一句也按这个意思读。

<p align="center">
  <img src="../assets/gif/pwm-1khz.gif" width="640" alt="CNT 走到 CCR = 500 时电平翻转，频率 1000 Hz">
  <br><sub>▲ 网页和公众号辅图。只播放 1000 Hz 和 500 µs 的正常路径。印刷以静态主图为准。500 Hz 的失败不在这条 GIF 上。</sub>
</p>

章首的 `timer-pwm.svg` 是辅图：它用 CCR = 300 画了 30% 的定格，和实验一第二步的数一样，也把 72 MHz 叫作定时器时钟。呼吸灯的 `pwm-breath.gif` 只在「相关资源」里给链接。1 kHz 和 500 Hz 两条路径以静态主图为准。

## 时序与状态

下表把主图拆成几行，每一行都能用 [RM0008 Rev 21 第 15 章](#source-rm0008-tim) 的公式复算。「定时器时钟」一栏是 PSC 之前的时钟。

| 行 | 定时器时钟 | PSC | ARR | CCR | CNT | 输出 | 时间 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 正常，高 | 72 MHz | 71 | 999 | 500 | 0 到 499 | 高 | 500 µs |
| 正常，低 | 72 MHz | 71 | 999 | 500 | 500 到 999 | 低 | 再 500 µs，周期 1000 µs，1000 Hz |
| 实验一第二步 | 72 MHz | 71 | 999 | 300 | 0 到 299 高，300 到 999 低 | 高 300 µs | 周期仍是 1000 µs，30% |
| 失败（算错） | 拿 36 MHz 去除 | 71 | 999 | 500 | 0 到 999 | 同一比较 | 算出周期 2000 µs、500 Hz；板子上仍是 1000 Hz |
| 装不下 | 72 MHz | 71 | 999999 | — | — | 不作为 1 秒 | 16 位截断，只剩低 16 位 16959，一圈 16.96 ms，不算成 1 秒 |
| 1 秒 | 72 MHz | 7199 | 9999 | — | 0 到 9999 | — | 1 Hz |

算式：`72e6 / (72 × 1000) = 1000` Hz；`36e6 / (72 × 1000) = 500` Hz；`999999 − 15 × 65536 = 16959`，`(16959 + 1) × 1 µs = 16.96 ms`。

## 常见坑与出处

| 现象 | 原因 | 处理 | 出处 | 出处能证明的部分 |
| --- | --- | --- | --- | --- |
| 算出来是 500 Hz，示波器上却是 1000 Hz | 拿 PCLK1 的 36 MHz 去除了 | 用 72 MHz 去除，PSC = 71，ARR = 999 | [RM0008 第 15 章](#source-rm0008-tim) | 这组数在 72 MHz 下是 1000 Hz。36 MHz 去除得到 500 Hz |
| 照 36 MHz 选了 PSC = 35，示波器上是 2000 Hz | 同一个错误，反过来算 | 按 72 MHz 选 PSC = 71 | [RM0008 第 7.2 节](#source-rm0008) | APB 预分频不是 1 时，定时器时钟是总线时钟的 2 倍 |
| 频率约 111 Hz | `SystemClock_Config()` 没跑，芯片还在 8 MHz 的 HSI 上，APB1 不分频，定时器时钟也是 8 MHz | 先调用 `SystemClock_Config()` | [RM0008 第 7.2 节](#source-rm0008) | APB 预分频为 1 时，定时器时钟等于总线时钟 |
| 想要 1 秒，ARR 写成 999999 | 16 位装不下，只剩低 16 位 | 改成 PSC = 7199、ARR = 9999 | [RM0008 第 15 章](#source-rm0008-tim) | 这颗料的通用定时器是 16 位，装不下 999999 |
| TIM1 完全没有波形 | BDTR 位 15 的 MOE 还是 0 | 置上 MOE | [RM0008 第 14.4.18 节](#source-rm0008-tim) | 复位值 0x0000，MOE 为 0 时主输出关闭。偏移 0x44。TIM3 没有这一位 |
| PWM 出现在别的脚上 | TIM3_REMAP 不是 00 | 保持 TIM3_REMAP=00，用 PA6 | [DS5319 表 5](#source-ds5319-tim) | LQFP48 第 16 脚是 PA6，默认复用含 TIM3_CH1 |
| 改 CCR 时偶尔多出一个窄脉冲 | OC1PE = 0，新值立刻参与比较 | 打开 CCR 预装载（OCxPE = 1） | [RM0008 第 15.4.7 节](#source-rm0008-tim) | OCxPE = 1 时新值在更新事件装入；除单脉冲模式外，PWM 不开预装载时行为没有保证 |
| 输入捕获量出的周期比实际短很多 | 被测间隔超过 65536 拍，CNT 在两次捕获之间回零不止一次 | 加大 PSC，或在更新中断里数回零次数 | [RM0008 第 15.3.5 节](#source-rm0008-tim) | 捕获时 CCRx 存下当时的 CNT；CNT 是 16 位 |
| 编码器的计数只在两个数之间来回跳 | 只接了 A 相，B 相是固定电平 | 把 B 相接到 CH2 | [RM0008 表 85](#source-rm0008-tim) | B 相电平不变时，A 的上升沿和下降沿一个加 1、一个减 1 |

## 相关资源

- 官方手册：**RM0008** 第 14 章（高级定时器 TIM1/8）、第 15 章（通用定时器 TIM2~5）、第 16 章（基本定时器 TIM6/7）
- 上一篇：[04 中断与NVIC](04-中断与NVIC.md)｜下一篇：[06 串口UART](06-串口UART.md)
- 手机阅读版：[第 05 章 · 定时器与PWM（公众号图文）](https://mp.weixin.qq.com/s/Jutp6HD4eo8bV0QcXWJ_pw)
- 相关图：[`assets/animations/timer-pwm.svg`](../assets/animations/timer-pwm.svg)、[`assets/animations/timer-modes.svg`](../assets/animations/timer-modes.svg)、[`assets/gif/pwm-breath.gif`](../assets/gif/pwm-breath.gif)
- 免责声明：本仓库插画均为作者自绘矢量图/程序生成动画，非厂商实拍照片。

# 04 中断与 NVIC

> English: [Interrupts and the NVIC](en/04-interrupts-nvic.md)

> 中断让 CPU 不必死等外设，事件到来时自动跳转处理，是实时系统的核心机制。

<p align="center">
  <img src="../assets/animations/nvic-interrupt-flow.svg" width="760" alt="中断响应全流程">
  <br><sub>▲ 动画：中断响应全流程（入栈现场 → 取向量 → ISR → 出栈，作者自绘矢量图）</sub>
</p>

<!-- video:ch04 -->
<p align="center">
  <video width="640" controls poster="../assets/video/ch04-nvic.png">
    <source src="../assets/video/ch04-nvic.mp4" type="video/mp4">
  </video>
  <br><sub>▲ 本章讲解视频（2.5 分钟）。<a href="../assets/video/ch04-nvic.mp4">MP4</a> · <a href="../assets/video/ch04-nvic.srt">字幕</a></sub>
</p>

<details>
<summary>旁白文字稿</summary>

1. 轮询是你不停去问，中断是事情来了敲你的门。主程序可以继续干别的。进了中断服务，办完要清标志，不然门会一直响。
2. NVIC 这道总闸可以分成三档来记：这路中断开了没有，优先级谁高，有没有挂起还没处理。三档看全，才不会觉得中断时灵时不灵。
3. EXTI 的编号就是引脚号。EXTI0 同时只能留给一个端口。PA0 和 PB0 不能一起拿这条线。要两只按键，就换不同的脚号。
4. 这一帧是仓库画的中断路径。引脚边沿先进 EXTI，再由 NVIC 决定要不要打断当前程序，最后才进你写的服务函数。路径上任何一扇门关着，回调都不会来。
5. 优先级不是数字越大越急。F1 上要先看优先级分组切成什么样，才知道哪些位是抢占、哪些是子优先级。抄例程时把分组改了，顺序会整个翻掉。
6. 中断服务要短。别在里面调用会阻塞的延时，也别做很重的打印。置一个标志，或者塞进缓冲区，把慢活交回主循环。服务函数一长，别的中断就饿着。
7. 主循环和中断一起碰的变量，编译器可能会缓存。单字节标志加 volatile。超过一个字的数据，读的时候还得短暂关中断，否则会撕成两半。
8. 口诀：总闸分三档；同一编号的脚，EXTI 只能留一个端口。记住这两句，按键中断的大多数玄学都会消失。
9. 实验用一只按键走下降沿，服务函数里只翻转 PC13。按下能亮、松开不连翻，说明边沿和清标志都做对了。连翻多半是没清，或者抖动没处理。
10. 合上书，三问。EXTI0 能同时留给 PA0 和 PB0 吗？服务函数里为什么别写阻塞延时？总闸那三档各管什么？

</details>
<!-- /video:ch04 -->

## 学习目标

读这一章之前：读完第 03 章，会把一只脚配成上拉输入，会控制 PC13 的灯；知道二进制、十六进制和「只改一个位」的位运算，知道 C 语言里 `volatile` 是什么意思（不熟的话先读第 00 章的「零基础预备」）。

- [ ] 用一句话说清轮询和中断的区别，并各举一个适合的场景
- [ ] 把 PA0 配成下降沿外部中断，做到按一次键、PC13 的灯翻转一次
- [ ] 按顺序说出一路中断要过的三道门：EXTI、NVIC、CPU 的屏蔽寄存器
- [ ] 在 `NVIC_PRIORITYGROUP_4` 下给两路中断填优先级，并判断谁能打断谁
- [ ] 解释 ISR 里为什么要清 `EXTI_PR`、为什么不能调用 `HAL_Delay()`
- [ ] 用 `volatile` 和临界区保护主循环与 ISR 共用的变量
- [ ] 说出 PA0 和 PB0 为什么不能同时做外部中断，以及 PB0 为什么离不开 AFIO 时钟

## 核心原理

**一句话结论：中断（interrupt）是外设在事件发生时主动叫 CPU。CPU 放下手里的程序，跳去执行一段专门的函数，办完再回来接着干。用好它要管三件事：清标志、排优先级、保护共用的变量。**

### 先打个比方

把 CPU 想成在家写作业的人，外设是送快递的。

- **轮询**：每隔几分钟放下笔，去门口看一眼。快递没来也得跑一趟；快递来了，也要等下一趟才发现。
- **中断**：门口装一个门铃。快递员一按，你在作业本上夹个书签，去开门，签收完回来，从书签那一页接着写。
- **优先级**：几个门铃同时响，先开哪扇门，看一张事先排好的名单，名单上的号码越小越先开。
- **清标志**：签收完要把门铃复位。不复位，门铃一直响，你刚坐下又得起来。

比方到这里为止。真实的「书签」是硬件自动压进栈里的 8 个寄存器，要花十几个时钟周期；名单上的号码只有 0–15 这 16 个；门铃不复位时，CPU 一退出服务函数就立刻再进去，主循环一行都跑不到。第 3 到第 6 节给出这些规则的出处。

### 1. 轮询和中断：两种等事件的办法

**轮询**（polling）是主循环一遍遍去读引脚：`while (1) { if (HAL_GPIO_ReadPin(...) == GPIO_PIN_RESET) { ... } }`。**中断**是让硬件盯着引脚，事件一来，CPU 自动跳进一段固定名字的函数，这段函数叫**中断服务函数**（Interrupt Service Routine，ISR），比如按键用的 `EXTI0_IRQHandler`。

| 对比 | 轮询 | 中断 |
| --- | --- | --- |
| CPU 平时在干什么 | 一直在查，没事也在跑 | 做别的事，或者睡眠省电 |
| 多久能发现事件 | 最坏要等一整个轮询周期 | 入栈约 167 ns 后进入 ISR（第 6 节），前提是没有更急的 ISR 在跑 |
| 短脉冲会不会漏 | 两次查询之间来了又走的脉冲会漏 | EXTI 的挂起位会记住它 |
| 代码难度 | 低 | 中：要管标志、优先级和共用变量 |
| 适合 | 事件少、变化慢，或者本来就要定时去看 | 事件随时会来、来了要快速反应 |

选哪一种，先问两件事：事件多久来一次，晚多久处理还能接受。按键这种「随时会来、来了要快」的事件用中断；温度这种「每秒看一眼就够」的数据用轮询，或者用第 05 章的定时器定时去读。

<p align="center">
  <img src="../assets/animations/gpio-input-interrupt.svg" width="760" alt="同一只按键，用轮询读和用 EXTI 中断读的对比">
  <br><sub>▲ 动画：同一只按键，轮询与 EXTI 中断两种读法的对比，以及三种触发边沿怎么选（作者自绘矢量图）。图里「必须开 AFIO 时钟」是稳妥的习惯，严格的条件见第 3 节。</sub>
</p>

### 2. 一路中断要过三道门

按键的下降沿要变成一次 ISR，路上有三道门，任何一道关着，ISR 都不会运行：

```text
PA0 下降沿 ──▶ EXTI0：认出边沿，置挂起位 EXTI_PR
           ──▶ NVIC：这一路开了吗？优先级够高吗？先挂起排队
           ──▶ CPU：PRIMASK 等屏蔽寄存器关着吗？
           ──▶ 执行 EXTI0_IRQHandler
```

- **EXTI**（External interrupt/event controller，外部中断/事件控制器）：芯片里专门盯引脚边沿的电路。它发现边沿，就在自己的挂起寄存器 `EXTI_PR` 里把对应位置 1，再把请求送给 NVIC。
- **NVIC**（Nested Vectored Interrupt Controller，嵌套向量中断控制器）：Cortex-M3 内核里的中断调度员。它对每一路中断管三件事：开没开（使能）、谁优先（优先级）、有没有在排队（挂起）。
- **CPU 的屏蔽寄存器**：PRIMASK 等几个寄存器能一下子挡住一大批中断，第 10 节细讲。

CPU 怎么知道该跳到哪个函数：Flash 开头有一张**向量表**（vector table），每一路中断占一格，格子里放着它的 ISR 地址。按 RM0008 Rev 21 表 63，EXTI0 在第 6 号位置，地址 0x0000_0058。启动文件把 `EXTI0_IRQHandler` 这个名字填进了这一格，所以你的函数名必须一字不差。

16 条 GPIO 线并不是每条都有自己的格子（RM0008 Rev 21 表 63）：

| EXTI 线 | ISR 名字 | 说明 |
| --- | --- | --- |
| EXTI0–EXTI4 | `EXTI0_IRQHandler` … `EXTI4_IRQHandler` | 每条线独占一个 |
| EXTI5–EXTI9 | `EXTI9_5_IRQHandler` | 5 条线共用一个 |
| EXTI10–EXTI15 | `EXTI15_10_IRQHandler` | 6 条线共用一个 |

用到共用的那两个时，ISR 里要先读 `EXTI_PR`，看是哪一条线来的，再分别处理、分别清零。

### 3. EXTI 外部中断：脚号就是线号

**结论：EXTIn 只能接某一个端口的第 n 只脚。PA0、PB0、PC0 都想用 EXTI0，只能选一个。**

配一条 EXTI 线，就是把下表从上到下填一遍。HAL 的 `HAL_GPIO_Init()` 替你填好了前五行，最后一行要在 ISR 里自己做。出处都是 RM0008 Rev 21：

| 项目 | 说明 | 出处 |
| --- | --- | --- |
| EXTI 线 | F103 有 19 条：EXTI0–EXTI15 接 GPIO，EXTI16 接 PVD，EXTI17 接 RTC 闹钟，EXTI18 接 USB 唤醒 | 第 10.2 节、第 10.2.5 节 |
| 选端口 | AFIO_EXTICR1–AFIO_EXTICR4，每条线 4 位：0000 是 A 口，0001 是 B 口，0010 是 C 口；复位值 0x0000 | 第 9.4.3–9.4.6 节 |
| 上升沿 | EXTI_RTSR 对应位写 1 | 第 10.3.3 节 |
| 下降沿 | EXTI_FTSR 对应位写 1；两个都写 1 就是双边沿 | 第 10.3.4 节 |
| 放行请求 | EXTI_IMR 对应位写 1，请求才送往 NVIC | 第 10.3.1 节 |
| 挂起位 | 边沿到来时 EXTI_PR 对应位置 1；往这一位写 1 才清零（rc_w1） | 第 10.3.6 节 |

AFIO 有一个容易绕晕的细节。复位后 EXTICR 全是 0，16 条线都连在 A 口上，所以 PA0 不开 AFIO 时钟也能触发。换到 PB0 就不行：要把 EXTI0 的 4 位改成 0001，手册要求先打开 AFIO 时钟（第 10.2.5 节图 21 的注）。实际不开时，这次写入不会生效，EXTI0 还连在 A 口上；这是常见的实际现象，手册的原话只有「要先开 AFIO 时钟」。很多人「PA 口好好的，换到 PB 就不灵」，就是这个原因。养成先开 AFIO 时钟的习惯，就不用记这个例外。

挂起位为什么一定要清：按 PM0056 Rev 7 第 4.3.9 节，这类请求在 ISR 返回前没有撤掉，返回后会再次挂起，CPU 马上又进同一个 ISR。表现是主循环一行都不跑，看上去像死机。

边沿怎么选：按第 03 章第 6 节的接法，按键一端接 GND、引脚开上拉，按下的那一刻是下降沿，所以写 EXTI_FTSR。

### 4. NVIC 优先级：数值越小越急

**结论：数值越小，优先级越高；能不能打断正在跑的 ISR，只看抢占优先级。**

F103 给每一路中断一个 8 位的优先级字段，只用其中高 4 位，所以只有 0–15 这 16 级（RM0008 Rev 21 第 10.1 节；PM0056 Rev 7 第 4.3.7 节表 42）。这 4 位再按**分组**切成两段：前一段是**抢占优先级**（preemption priority，PM0056 叫 group priority），后一段是**子优先级**（subpriority）。规则只有三条（PM0056 Rev 7 第 2.3.6 节）：

- 抢占数值更小的，可以打断抢占数值更大的 ISR。一个 ISR 被另一个打断，叫**嵌套**。
- 抢占数值相同的，谁也打断不了谁，后来的只能挂起排队。子优先级不同也一样。
- 几个请求同时在排队，先比抢占，再比子优先级，都相同就比 IRQ 编号，编号小的先。

### 5. 优先级分组：4 位怎么切

**结论：HAL 默认用 GROUP_4，4 位全给抢占。分组全工程只有一份，在开头设一次就不要再动。**

切法由内核寄存器 SCB_AIRCR 里的 PRIGROUP 字段决定（PM0056 Rev 7 第 4.4.5 节表 45）。HAL 用宏来写：

| HAL 分组宏 | PRIGROUP | 抢占位数 | 子优先级位数 | 抢占可分几级 |
| --- | --- | --- | --- | --- |
| `NVIC_PRIORITYGROUP_0` | 0b111 | 0 | 4 | 1 级，互相都打断不了 |
| `NVIC_PRIORITYGROUP_1` | 0b110 | 1 | 3 | 2 |
| `NVIC_PRIORITYGROUP_2` | 0b101 | 2 | 2 | 4 |
| `NVIC_PRIORITYGROUP_3` | 0b100 | 3 | 1 | 8 |
| `NVIC_PRIORITYGROUP_4` | 0b011 | 4 | 0 | 16，`HAL_Init()` 的默认 |

从上往下，抢占位越来越多。HAL 默认是最后一行：4 位全给抢占，`HAL_NVIC_SetPriority()` 的第三个参数（子优先级）没有位可放，写 0。

举个例子：GROUP_4 下，EXTI0 设成抢占 1，TIM2 设成抢占 2。TIM2 的 ISR 正在跑时按下按键，1 比 2 小，EXTI0 打断 TIM2，办完再回到 TIM2。两者都设成 1，EXTI0 只能挂起，等 TIM2 返回后才进去。「关键插图」画的就是这两条路。

分组一改，所有中断的数字含义都会跟着变。下表是选分组的建议：

| 场景 | 分组 | 理由 |
| --- | --- | --- |
| 不用 RTOS | GROUP_4 | 只比一个数，最直观 |
| 用 FreeRTOS | GROUP_4 | [FreeRTOS 的 Cortex-M 说明](#source-freertos-priority)建议优先级位全给抢占，第 15 章细讲 |
| 确实需要同级之间的先后 | GROUP_2 或 GROUP_3 | 抢占级变少，换来子优先级 |

### 6. 进出中断：硬件替你做了什么

**栈**（stack）是 RAM 里一块后进先出的区域，栈指针 SP 指着最上面那一格。**入栈**就是把寄存器的值抄进去，**出栈**是再抄回来。CPU 被打断时，硬件自动做下表里的大部分事：

| 步骤 | 谁做 | 做什么 |
| --- | --- | --- |
| 1 | EXTI | PA0 出现下降沿，EXTI_PR 的位 0 置 1，请求送往 NVIC |
| 2 | NVIC | EXTI0 开着、优先级够高，于是挂起它并通知 CPU |
| 3 | CPU | 比较优先级，决定在当前指令之后响应 |
| 4 | 硬件 | 把 8 个寄存器压栈：xPSR, PC, LR, R12, R3, R2, R1, R0；同时从向量表取出 `EXTI0_IRQHandler` 的地址 |
| 5 | 硬件 | 往 LR 写一个特殊的返回值（EXC_RETURN），跳进 ISR |
| 6 | 你的代码 | 清 EXTI_PR，做最少的事 |
| 7 | 硬件 | ISR 返回时认出 EXC_RETURN，出栈，回到被打断的地方 |

第 4、5、7 步是硬件做的，所以 ISR 可以写成普通的 C 函数，不用自己保存寄存器，你只负责第 6 步。这三步出自 PM0056 Rev 7 第 2.3.7 节。

8 个寄存器是 32 字节。Arm 给 Cortex-M3 的标称中断延迟约为 12 个时钟周期，按 72 MHz 算是 `12 / 72e6 ≈ 167 ns`。这个数的前提和出处放在「原理与适用范围」。

退出 ISR 时，硬件还有两个省时间的办法：

| 机制 | 什么时候发生 | 省了什么 |
| --- | --- | --- |
| 尾链（tail-chaining） | 一个 ISR 结束时，另一个已经在排队 | 省掉一次出栈和紧接着的入栈，直接进下一个 ISR |
| 晚到（late arrival） | 正在入栈时，又来了一个抢占更高的请求 | 入栈不重做，先进更急的那个 ISR |

两者都只省时间，不改变谁能打断谁。真正的大头是 ISR 自己有多长：ISR 越短，别的中断等得越少。

### 7. 主循环和 ISR 共用变量

**结论：ISR 和主循环都要用的变量加 `volatile`；超过一个字的数据，主循环读的时候要短暂关中断。**

`volatile` 告诉编译器：这个变量随时可能被别人改，每次用都要真的去内存里读，不能把旧值留在寄存器里反复用。少了它，下面这句在开了优化以后可能变成死循环，因为编译器只读一次 `g_flag`：

```c
static uint8_t g_flag;        /* 少了 volatile */
while (g_flag == 0) { }       /* ISR 把它改成 1，这里也看不见 */
```

单字节标志和 32 位变量，CPU 一条指令就读完了。`uint64_t` 这种超过一个字的变量，编译器要拆成两次读；如果 ISR 正好插在两次之间改了它，读到的高 32 位和低 32 位就来自两个不同的时刻，这叫数据被「撕开」。办法是**临界区**（critical section）：一小段不许中断插进来的代码。

| 写法 | 作用 | 什么时候用 |
| --- | --- | --- |
| `volatile` | 每次都真的读写内存 | ISR 和主循环共用的变量 |
| `__disable_irq()` / `__enable_irq()` | 把 PRIMASK 置 1 / 清 0，关上 / 打开所有可配置优先级的中断 | 很短的临界区 |
| `__get_PRIMASK()` / `__set_PRIMASK()` | 读出、写回 PRIMASK | 临界区结束时恢复原状，不误开中断 |
| `__DSB()` | 前面的读写全部完成，才执行后面的指令 | 清完外设标志、紧接着就要退出 ISR 时 |

这几个函数和对应的指令见 PM0056 Rev 7 第 3.2 节表 21、表 22，`__DSB()` 的含义见第 3.9.4 节。临界区要短：关中断的这段时间里，所有可配置优先级的中断都只能排队。

清外设标志有一个经验做法：放在 ISR 的开头，不要放在最后一句。放在最后时，写操作可能还没真正到达外设，ISR 就已经返回，结果又多进一次。

### 8. SysTick 与 HAL 的延时：ISR 里不要做的事

> [!WARNING]
> 不要在 ISR 里调用 `HAL_Delay()`。它靠 SysTick 中断每 1 ms 加一次的计数来等。当前 ISR 的优先级数值不大于 SysTick 的数值时，SysTick 打断不进来，计数不走，程序就停在这里。

| 别做 | 为什么 | 改成 |
| --- | --- | --- |
| `HAL_Delay()` | 上面那条警告 | ISR 里置标志，主循环里等 |
| `printf()` 到串口 | 115200 波特率、8N1 格式下，一个字节连起始位和停止位共 10 位，要 `10 / 115200 ≈ 87 µs`（第 06 章），几十个字就是几毫秒 | 把数据放进缓冲区，主循环再发 |
| 浮点运算、长循环 | Cortex-M3 没有浮点单元，浮点要用软件模拟 | ISR 只记原始数据，主循环再算 |

SysTick 的优先级由工程里 `stm32f1xx_hal_conf.h` 的 `TICK_INT_PRIORITY` 决定，打开文件看一眼就知道。ISR 里该做的只有三类事：清标志、搬走数据、置一个标志。

### 9. NVIC 的寄存器

HAL 的 `HAL_NVIC_EnableIRQ()`、`HAL_NVIC_SetPriority()`、`HAL_NVIC_SetPriorityGrouping()` 最后写的就是下表这几个内核寄存器。EXTI0 的 IRQ 编号是 6，下表最后一列以它为例。出处是 PM0056 Rev 7 第 4.3.2 到 4.3.7 节和第 4.4.5 节：

| 寄存器（CMSIS 写法） | 作用 | EXTI0 在哪里 |
| --- | --- | --- |
| ISER（`NVIC->ISER[0]`） | 对应位写 1，打开这一路；写 0 没有作用 | `ISER[0]` 的位 6 |
| ICER（`NVIC->ICER[0]`） | 对应位写 1，关掉这一路 | `ICER[0]` 的位 6 |
| ISPR / ICPR | 写 1 置挂起 / 清挂起 | 位 6 |
| IABR | 只读，1 表示这一路正在服务 | 位 6 |
| IPR（`NVIC->IP[6]`） | 每路 8 位，只用高 4 位 [7:4]，低 4 位读出为 0 | `IP[6]` |
| SCB_AIRCR 的 PRIGROUP（位 10:8） | 决定 4 位怎么切成抢占和子优先级；写这个寄存器时高 16 位要带钥匙 0x5FA，否则写入被忽略 | 全局一份 |

一个 ISER 管 32 路中断：`ISER[0]` 管 IRQ 0–31，`ISER[1]` 管 32–63（PM0056 Rev 7 表 41）。即使一路中断没打开，它的挂起位照样会被置上（PM0056 Rev 7 第 4.3.10 节）；所以先清挂起、再打开，可以避免一打开就冲进一次旧请求。

### 10. 三个屏蔽寄存器：PRIMASK、FAULTMASK、BASEPRI

**结论：PRIMASK 挡住所有可配置优先级的中断；FAULTMASK 再加上 HardFault，只留 NMI；BASEPRI 只挡优先级数值大于等于它的那一截。**

NMI（Non-Maskable Interrupt，不可屏蔽中断）和 HardFault（硬错误）的优先级是固定的负数，NMI 是 −2，HardFault 是 −1，比所有可配置的都高（PM0056 Rev 7 第 2.3.2 节表 16）。下表出自同一份手册第 2.1.3 节的表 7、表 8、表 9：

| 寄存器 | 置 1 或写非零值后挡住谁 | 谁还能进来 | 常见写法 |
| --- | --- | --- | --- |
| PRIMASK | 所有可配置优先级的异常 | NMI、HardFault | `__disable_irq()` / `__enable_irq()` |
| FAULTMASK | 除 NMI 外的所有异常 | NMI | `__disable_fault_irq()` / `__enable_fault_irq()` |
| BASEPRI | 优先级数值大于等于 BASEPRI 的异常 | 数值更小、更急的那些 | `__set_BASEPRI(prio << (8 - __NVIC_PRIO_BITS))` |

BASEPRI 和优先级字段一样只用高 4 位，所以 0–15 的优先级要左移 4 位再写进去；`__NVIC_PRIO_BITS` 在 F103 的头文件里是 4。BASEPRI 写 0 表示什么都不挡。RTOS 用它只关「一部分」中断，第 15 章会用到。

最后回到 EXTI：线是按脚号共用的。PA0 和 PB0 都在 EXTI0 上，不能同时做外部中断；第二只按键要换一个脚号，比如 PA1。要换端口，F1 改 `AFIO->EXTICR`，F4 改 `SYSCFG->EXTICR`，都不是多开一条线。

口诀：**总闸分三档；同一编号的脚，EXTI 只能留一个端口。**「三档」就是 NVIC 对每一路中断管的三件事：开没开、谁优先、有没有挂起。

## 硬件与接线

| 开发板 | 外设 | 引脚 | 备注 |
| --- | --- | --- | --- |
| BluePill | 按键（EXTI0） | PA0（LQFP48 第 10 脚） | 另一端接 GND，开内部上拉，按下产生下降沿 |
| BluePill | 板载 LED | PC13 | 低电平点亮（第 03 章） |
| BluePill | 按键挪到 PB0（自测题和寄存器写法用） | PB0（LQFP48 第 18 脚） | 同样接 GND；要先开 AFIO 时钟再写 EXTICR |

```text
按键（按下读 0）：PA0 ──[按键]── GND        PA0 开内部上拉，松开读 1，按下的瞬间是下降沿
板载灯（写 0 亮）：3.3 V ──[电阻]──▶|── PC13  第 03 章的接法，不用另接
```

脚号出自 DS5319 Rev 20 表 5。按键不需要外接电阻，片内上拉就够；千万别把按键接到 3.3 V 再配上拉，那样按下和松开都是高电平，永远没有边沿。

## 代码实现

下面这段程序对应实验一和实验二：按一次 PA0，PC13 的灯翻转一次；ISR 同时数下降沿，用来看一次按键抖出几个边沿。

```c
/* exti_key.c —— PA0 按键下降沿中断：ISR 只记账，主循环确认后翻转 PC13 */
#include "stm32f1xx_hal.h"

#define LED_PIN       GPIO_PIN_13
#define LED_PORT      GPIOC
#define KEY_PIN       GPIO_PIN_0
#define KEY_PORT      GPIOA
#define KEY_PREEMPT   1U     /* 抢占优先级（例程设定） */
#define KEY_SUB       0U     /* 子优先级：GROUP_4 下没有子优先级位，写 0 */
#define DEBOUNCE_MS   20U    /* 等弹跳过去的时间（经验值） */

static volatile uint8_t  g_key_flag  = 0;   /* ISR 置 1，主循环清 0 */
static volatile uint64_t g_key_edges = 0;   /* ISR 数到的下降沿，64 位，读时要关中断 */
uint64_t g_edges_seen = 0;                  /* 主循环最近一次读到的边沿数（调试器里看） */
uint32_t g_presses    = 0;                  /* 主循环确认的按键次数（调试器里看） */

void SystemClock_Config(void);

/* 读 64 位计数：要读两次内存，中间不能让 ISR 插进来 */
static uint64_t read_edges(void)
{
    uint32_t primask = __get_PRIMASK();   /* 记下原来的开关状态 */
    __disable_irq();                      /* PRIMASK = 1 */
    uint64_t n = g_key_edges;
    __set_PRIMASK(primask);               /* 原来开着才重新打开 */
    return n;
}

int main(void)
{
    HAL_Init();                    /* 分组设为 NVIC_PRIORITYGROUP_4，SysTick 每 1 ms 一次 */
    SystemClock_Config();          /* 72 MHz，见第 02 章 */

    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_GPIOC_CLK_ENABLE();
    __HAL_RCC_AFIO_CLK_ENABLE();   /* F1：写 AFIO_EXTICR 之前先开 AFIO 时钟 */

    GPIO_InitTypeDef io = {0};

    io.Pin   = LED_PIN;            /* PC13 推挽输出，板载灯低电平亮 */
    io.Mode  = GPIO_MODE_OUTPUT_PP;
    io.Pull  = GPIO_NOPULL;
    io.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(LED_PORT, &io);

    io.Pin  = KEY_PIN;             /* PA0：上拉输入，下降沿触发 EXTI0 */
    io.Mode = GPIO_MODE_IT_FALLING;
    io.Pull = GPIO_PULLUP;
    HAL_GPIO_Init(KEY_PORT, &io);  /* 顺带写好 EXTICR、EXTI_FTSR、EXTI_IMR */

    HAL_NVIC_SetPriority(EXTI0_IRQn, KEY_PREEMPT, KEY_SUB);
    HAL_NVIC_EnableIRQ(EXTI0_IRQn);

    while (1)
    {
        if (g_key_flag)
        {
            HAL_Delay(DEBOUNCE_MS);                                     /* 主循环里等待是安全的 */
            if (HAL_GPIO_ReadPin(KEY_PORT, KEY_PIN) == GPIO_PIN_RESET)  /* 还是低电平：真按下 */
            {
                HAL_GPIO_TogglePin(LED_PORT, LED_PIN);
                g_presses++;
                g_edges_seen = read_edges();
            }
            g_key_flag = 0;   /* 等待期间弹跳又置上的标志，一并清掉 */
        }
    }
}

/* 名字要和启动文件向量表里的一字不差 */
void EXTI0_IRQHandler(void)
{
    if (__HAL_GPIO_EXTI_GET_IT(KEY_PIN) != RESET)
    {
        __HAL_GPIO_EXTI_CLEAR_IT(KEY_PIN);   /* 往 EXTI_PR 的位 0 写 1，清掉挂起位 */
        g_key_edges++;
        g_key_flag = 1;                      /* 只记账，慢活交给主循环 */
    }
}
```

逐段看：

- `HAL_Init()` 把分组设成 `NVIC_PRIORITYGROUP_4`，并让 SysTick 每 1 ms 中断一次，`HAL_Delay()` 靠它计时。
- `__HAL_RCC_AFIO_CLK_ENABLE()`：PA0 不开它也能触发，因为 EXTICR 复位后选的就是 A 口；换到 PB0 就必须开（第 3 节）。有些版本的 HAL 会在 `HAL_GPIO_Init()` 里替你开，自己写一行，换库也不会漏。
- `GPIO_MODE_IT_FALLING` 加 `GPIO_PULLUP`：松开时被上拉成高，按下接地变低，变低的那一刻就是下降沿。
- `HAL_NVIC_SetPriority(EXTI0_IRQn, 1, 0)`：抢占 1、子优先级 0。第三个参数在 GROUP_4 下没有位可放，写 0。
- `EXTI0_IRQHandler` 第一件事是清挂起位，然后只做两件很快的事：计数、置标志。
- 主循环先等 `DEBOUNCE_MS` 再读一次，两次都是低电平才算真按下。`g_key_flag = 0` 放在最后，把等待期间弹跳置上的标志一起清掉。
- `read_edges()` 先用 `__get_PRIMASK()` 记下原状态，读完用 `__set_PRIMASK()` 还原。如果直接用 `__enable_irq()` 收尾，调用前中断本来就关着时，这里会把它误开。
- `g_edges_seen` 和 `g_presses` 不加 `static`，是为了不让编译器把这两个「只写不读」的变量优化掉，调试器才看得到。

同样的配置用寄存器写，并把按键挪到 PB0。这一段能看清 HAL 替你写了哪几个寄存器，以及 AFIO 时钟管的是哪一步：

```c
/* 寄存器写法：EXTI0 改接 PB0，下降沿触发 */
RCC->APB2ENR |= RCC_APB2ENR_IOPBEN | RCC_APB2ENR_AFIOEN;   /* B 口和 AFIO 的时钟 */

GPIOB->CRL &= ~(GPIO_CRL_MODE0 | GPIO_CRL_CNF0);           /* PB0 的 4 位先清零 */
GPIOB->CRL |= GPIO_CRL_CNF0_1;                             /* MODE = 00、CNF = 10：上拉/下拉输入 */
GPIOB->BSRR = GPIO_BSRR_BS0;                               /* ODR0 = 1：选上拉 */

AFIO->EXTICR[0] &= ~AFIO_EXTICR1_EXTI0;                    /* EXTI0 的 4 位先清零 */
AFIO->EXTICR[0] |= AFIO_EXTICR1_EXTI0_PB;                  /* 0001：EXTI0 接 PB0，没开 AFIO 时钟这句无效 */

EXTI->FTSR |= EXTI_FTSR_TR0;                               /* 下降沿触发 */
EXTI->RTSR &= ~EXTI_RTSR_TR0;                              /* 不要上升沿 */
EXTI->PR    = EXTI_PR_PR0;                                 /* 写 1 清掉可能残留的挂起位 */
EXTI->IMR  |= EXTI_IMR_MR0;                                /* 放行这一路请求 */

NVIC_SetPriority(EXTI0_IRQn, NVIC_EncodePriority(NVIC_GetPriorityGrouping(), 1, 0));
NVIC_EnableIRQ(EXTI0_IRQn);                                /* 写 NVIC->ISER[0] 的位 6 */
```

- `EXTI->PR = EXTI_PR_PR0;` 用的是等号，不是 `|=`。这个寄存器写 1 清零、写 0 没有作用，用 `|=` 会把其他已经挂起的位读出来再写 1，一起清掉。
- `NVIC_EncodePriority()` 按当前分组把「抢占 1、子优先级 0」拼成一个数，HAL 的 `HAL_NVIC_SetPriority()` 里面做的就是这一步。

实验三要第二路中断。把下面几段加进 `exti_key.c`，在 `while (1)` 之前调用 `tim2_init()`，并删掉主循环里那行 `HAL_GPIO_TogglePin()`，让灯只听两个 ISR 的。TIM2 的 PSC、ARR 怎么算，第 05 章细讲：

```c
/* 实验三：TIM2 每秒进一次中断，在 ISR 里故意忙等，留出被 EXTI0 打断的窗口 */
#define TIM2_PREEMPT  2U          /* 先用 2，再改成 1 对比 */
#define BUSY_LOOPS    3000000U    /* 例程设定：让 TIM2 的 ISR 忙几百毫秒，按实际调整 */

TIM_HandleTypeDef htim2;

static void tim2_init(void)
{
    __HAL_RCC_TIM2_CLK_ENABLE();
    htim2.Instance           = TIM2;
    htim2.Init.Prescaler     = 7199;                /* 72 MHz / 7200 = 10 kHz */
    htim2.Init.CounterMode   = TIM_COUNTERMODE_UP;
    htim2.Init.Period        = 9999;                /* 10 kHz / 10000 = 1 Hz */
    htim2.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
    HAL_TIM_Base_Init(&htim2);
    HAL_NVIC_SetPriority(TIM2_IRQn, TIM2_PREEMPT, 0);
    HAL_NVIC_EnableIRQ(TIM2_IRQn);
    HAL_TIM_Base_Start_IT(&htim2);
}

void TIM2_IRQHandler(void)
{
    HAL_TIM_IRQHandler(&htim2);
}

void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim)
{
    if (htim->Instance == TIM2)
    {
        HAL_GPIO_WritePin(LED_PORT, LED_PIN, GPIO_PIN_RESET);    /* 亮灯：忙等开始 */
        for (volatile uint32_t i = 0; i < BUSY_LOOPS; i++) { }   /* 只为实验，正式代码别在 ISR 里忙等 */
        HAL_GPIO_WritePin(LED_PORT, LED_PIN, GPIO_PIN_SET);      /* 灭灯：忙等结束 */
    }
}

/* 用这一版替换上面的 EXTI0_IRQHandler */
void EXTI0_IRQHandler(void)
{
    if (__HAL_GPIO_EXTI_GET_IT(KEY_PIN) != RESET)
    {
        __HAL_GPIO_EXTI_CLEAR_IT(KEY_PIN);
        HAL_GPIO_WritePin(LED_PORT, LED_PIN, GPIO_PIN_SET);      /* 灭灯：EXTI0 的 ISR 跑到了 */
        g_key_edges++;
        g_key_flag = 1;
    }
}
```

灯亮着的那一段，就是 TIM2 的 ISR 在忙等；EXTI0 的 ISR 一运行就灭灯。按下按键之后灯多久才灭，EXTI0 就等了多久。

完整工程见 [`examples/exti-key/`](../examples/exti-key/)。那里用的是 HAL 的回调写法：`EXTI0_IRQHandler()` 只调用 `HAL_GPIO_EXTI_IRQHandler()`，由它清挂起位，再调用你写的 `HAL_GPIO_EXTI_Callback()`。

## 动手实验

1. **实验一：按一次，翻一次。** 烧录上面的程序，按 PA0 的按键。
   - 预期现象：每按一次，PC13 的灯亮灭换一次；按住不放，灯不会连续闪。
   - 怎么确认：慢慢按 10 次，灯换 10 次状态；暂停程序，在调试器里看 `g_presses`，应是 10。
   - 没成功先查：一次都不翻，先查 GPIOA 的时钟和 `EXTI0_IRQHandler` 的拼写；程序卡住不动，查 ISR 里有没有清挂起位；偶尔按一次翻两次，把 `DEBOUNCE_MS` 加大一点。
2. **实验二：数一数抖动。** 按 10 次后暂停程序，比较 `g_presses` 和 `g_edges_seen`。
   - 预期现象：`g_edges_seen` 往往比 `g_presses` 大，多出来的是按键弹跳产生的下降沿。多几个到十几个都常见，取决于按键（经验值）。
   - 怎么确认：用逻辑分析仪接 PA0，放大按下的那一刻，能看到几毫秒里电平来回跳了几次，次数和计数差不多。
   - 没成功先查：两个数完全相等，可能是按键很好，也可能计数没进 ISR。在 `g_key_edges++` 那一行打断点确认。
3. **实验三：让 EXTI0 打断 TIM2。** 按「代码实现」最后一段改好程序。PC13 每秒亮一段，亮着的时候就是 TIM2 的 ISR 在忙等。
   - 预期现象：`TIM2_PREEMPT` 为 2 时，趁灯亮着按键，灯立刻熄灭；改成 1（和 EXTI0 一样），同样趁灯亮着按键，灯要亮满这一段才灭。
   - 怎么确认：用逻辑分析仪同时接 PA0 和 PC13。抢占 1 对 2 时，PA0 的下降沿之后，PC13 几乎同时变高（灭灯）；1 对 1 时，PC13 要等这一段忙等结束才变高。
   - 没成功先查：两种设置看不出区别，先确认 `HAL_Init()` 之后没有别的代码改了分组；再把 `BUSY_LOOPS` 加大，让亮灯的一段长到肉眼能分辨。

## 自测

1. 调用 `__disable_irq()` 之后，HardFault 还能进来吗？NMI 呢？
2. 分组是 GROUP_4。TIM2 设成 `HAL_NVIC_SetPriority(TIM2_IRQn, 2, 0)`，它的 ISR 正在跑。EXTI0 设成 `(2, 1)`，能打断吗？改成 `(1, 0)` 呢？
3. BASEPRI 写成 `5 << 4`（优先级 5 左移 4 位）之后，优先级数值为 3 和 7 的两路中断，哪一路还能进来？
4. 72 MHz 下按 12 个时钟周期算，入栈要多少纳秒？假设 Flash 等待让它变成 14 个周期，又是多少？
5. 用寄存器写法把按键挪到 PB0，却漏了 `RCC_APB2ENR_AFIOEN`。按 PB0 的按键会怎样？此时 EXTI0 在听哪只脚？

参考答案：

1. 都能进来。PRIMASK 只挡可配置优先级的异常；HardFault 和 NMI 的优先级是固定的，不在其中（PM0056 Rev 7 表 7）。
2. `(2, 1)` 不能。抢占都是 2，相同的抢占不能嵌套；而且 GROUP_4 没有子优先级位，那个 1 根本没处放。EXTI0 只能挂起，等 TIM2 返回后再进去。`(1, 0)` 能，1 比 2 小。
3. 3 能进来，7 不能。BASEPRI 挡住优先级数值大于等于 5 的异常，7 ≥ 5 被挡，3 < 5 放行（PM0056 Rev 7 表 9）。
4. `12 / 72e6 ≈ 1.67e-7 s ≈ 167 ns`；`14 / 72e6 ≈ 1.94e-7 s ≈ 194 ns`。两个数都只是进门的时间，不含 ISR 正文。
5. PB0 没有反应。手册要求写 EXTICR 前先开 AFIO 时钟；没开时这次写入不会生效，EXTI0 的 4 位仍是复位值 0000，也就是 A 口，EXTI0 还在听 PA0（RM0008 Rev 21 第 9.4.3 节、第 10.2.5 节）。

## 原理与适用范围

> [!NOTE]
> 从这一节到「常见坑与出处」是深入部分，把前面的结论落到具体订货号、手册章节和能复算的数字上。第一次读可以先跳过，做完动手实验再回来对照。

**订货号、时钟和分组。**本章的数字都落在 STM32F103C8T6 上。系统时钟按附录 D 的设定：SYSCLK = HCLK = 72 MHz。分组用 HAL 的默认值 `NVIC_PRIORITYGROUP_4`：4 位抢占、0 位子优先级，数值越小，逻辑优先级越高。这个默认值是 STM32CubeF1 的 `HAL_Init()` 写进去的，出自 HAL 源码，不是手册。

**谁能打断谁。**[PM0056 Rev 7](#source-pm0056-nvic) 第 2.3.6 节规定：能不能打断只看抢占（手册叫组优先级）；子优先级只给已经挂起的请求排先后；两者都相同时，IRQ 编号小的先。`GROUP_4` 没有子优先级位，所以 `HAL_NVIC_SetPriority()` 的子优先级参数在这个分组下不产生任何先后。分组一改，同一个数字代表的抢占级就变了，要按新分组重新比较，不能拿旧数字比谁能嵌套。

**入栈的账。**同一份手册第 2.3.7 节：进入异常时硬件压 8 个字，按地址从高到低是 xPSR, PC, LR, R12, R3, R2, R1, R0，SP 停在 R0；取向量和入栈同时进行。PM0056 没有给周期数。约 12 个 HCLK 是 Arm 在 Cortex-M3 技术参考手册（Arm Cortex-M3 Technical Reference Manual r1p1，中断延迟一节）里给的标称值，前提是存储器零等待。72 MHz 时 F103 的 Flash 要插 2 个等待周期（RM0008 Rev 21 第 3.3.3 节），实测可能多几个周期。按 12 个算，`12 / 72e6 ≈ 167 ns`。这 167 ns 只是进门的时间，不含 ISR 正文，不能拿来当 ISR 的时间预算。

**尾链和晚到。**同一节还写了两个省时间的办法：尾链在一个 ISR 退出时跳过「出栈再入栈」，直接进下一个已挂起的 ISR；晚到让入栈途中到来的更高抢占请求先进。两者都不改变谁有权打断谁，低优先级不会因为尾链插进高优先级的 ISR。PM0056 没有印尾链的周期数，本书也不给。

**三个屏蔽寄存器。**[PM0056 Rev 7](#source-pm0056-nvic) 第 2.1.3 节的表 7、表 8、表 9：PRIMASK = 1 挡住所有可配置优先级的异常，NMI 和 HardFault 仍能进入；FAULTMASK = 1 再挡住 HardFault，只留 NMI，而且除 NMI 外的任何异常返回时，硬件会把它清零；BASEPRI 写非零值时，挡住优先级数值大于等于它的异常。NMI 不参加 EXTI0 和 TIM2 之间的抢占比较。F103 上 NMI 的常见来源是时钟安全系统（CSS），见第 02 章。

**和 RTOS 的边界。**裸机这套配置不自动满足第 15 章的 FromISR 规则。FreeRTOS 要求：会调用 FromISR 函数的中断，逻辑优先级不能高于 `configMAX_SYSCALL_INTERRUPT_PRIORITY` 设的那一级，换成数值就是不能比它小（[FreeRTOS 的说明](#source-freertos-priority)）。具体数字留在第 15 章。

**EXTI 这一套只在 F1 成立。**[RM0008 Rev 21](#source-rm0008-exti)：EXTI 线按脚号共用，PA0 和 PB0 都在 EXTI0 上，同一时刻只能选一个。选择写在 AFIO_EXTICR1 到 AFIO_EXTICR4，在第 9.4.3 到 9.4.6 节，每条线 4 位，复位值 0x0000，也就是全部选 A 口。写 EXTICR 之前要先开 AFIO 时钟（第 10.2.5 节图 21 的注）。挂起位在 EXTI_PR（第 10.3.6 节），写 1 清零。第 9.2.7 节是 `GPIOx_LCKR`，不要写成 EXTICR。F4 等系列把这组选择寄存器放进了 SYSCFG（SYSCFG_EXTICR，见 RM0090 Rev 22），「先开 AFIO 时钟」这一句在那些系列上不适用。

## 关键插图

<p align="center">
  <img src="../assets/diagrams/sample-04-exception-stack.svg" width="760" alt="抢占 1 可以打断抢占 2；抢占同为 1 时后来的请求不能嵌套">
  <br><sub>▲ 自绘。STM32F103C8T6，NVIC_PRIORITYGROUP_4。正常路径：TIM2 以抢占 2 运行，EXTI0（PA0，EXTI0_IRQn）以抢占 1、子优先级 0 打断它；入栈 8 个寄存器，从高地址到低地址是 xPSR, PC, LR, R12, R3, R2, R1, R0，SP 指向 R0；约 12 个 HCLK，72 MHz 时 167 ns，不含 ISR 正文。失败路径：两者抢占都写成 1，子优先级 0 和 1 也不能嵌套，退出后可以尾链，没有第二次嵌套入栈。PRIMASK = 1 时 EXTI0 和 TIM2 都进不来，NMI 仍能进入。出处：[PM0056 第 2.3.7 节](#source-pm0056-nvic)、[RM0008 Rev 21 的 EXTICR 与 EXTI_PR](#source-rm0008-exti)。</sub>
</p>

**怎么读这张图。**图分上、中、下三块，从上往下读。上面一块是正常路径：TIM2 的 ISR 正在跑，PA0 的下降沿到来，EXTI0 的抢占数值更小，硬件压 8 个寄存器后进入 EXTI0 的 ISR，清掉 EXTI_PR 再回到 TIM2。中间一块是失败路径：两路抢占写成同一级，子优先级不同也没用，EXTI0 只能挂起，等 TIM2 退出后经尾链进去。下面一块是屏蔽寄存器：PRIMASK 关着时两路都进不来，NMI 照样进入。

<p align="center">
  <img src="../assets/gif/nvic-preempt.gif" width="640" alt="TIM2 正在执行时，EXTI0 以更高抢占打断，然后返回">
  <br><sub>▲ 网页和公众号用的动图，只播放抢占成功的那一条路。印刷以上面的静态主图为准；同抢占不能嵌套的失败路径不在这张动图里。</sub>
</p>

章首的 `nvic-interrupt-flow.svg` 把同一个过程画成了六步流程，并标出向量地址的算法 `VTOR + 4 × (IRQn + 16)`：EXTI0 的 IRQn 是 6，`4 × (6 + 16) = 88 = 0x58`，正好对上第 2 节的 0x0000_0058。

## 时序与状态

下表把关键插图拆成几个时刻，每一行都能对回 [PM0056 Rev 7 第 2.3.6、2.3.7 节](#source-pm0056-nvic)。分组都是 GROUP_4，时间按 72 MHz、12 个 HCLK 算。

| 时刻 | 分组 | EXTI0 抢占 | TIM2 抢占 | 发生了什么 | 时间 |
| --- | --- | --- | --- | --- | --- |
| 正常：TIM2 的 ISR 在跑 | GROUP_4 | — | 2 | 主循环已被 TIM2 打断 | — |
| 正常：PA0 来了下降沿 | GROUP_4 | 1 | 2 | 1 比 2 小，EXTI0 打断 TIM2；硬件压 xPSR, PC, LR, R12, R3, R2, R1, R0 | 约 12 HCLK，约 167 ns |
| 正常：EXTI0 办完 | GROUP_4 | 1 | 2 | 清 EXTI_PR，出栈，回到 TIM2 的 ISR | 167 ns 不含 ISR 正文 |
| 失败：两者都写成 1 | GROUP_4 | 1 | 1 | EXTI0 挂起，等 TIM2 返回后经尾链进入；没有第二次嵌套入栈 | 手册没给尾链周期数 |
| PRIMASK = 1 | GROUP_4 | 1 | 2 | 两路都进不来，只在挂起位里排队；NMI 仍能进入 | — |

算式：`12 / 72e6 = 1.67e-7 s ≈ 167 ns`，和附录 D 那一格是同一笔账。EXTI_PR 的写 1 清零见 [RM0008 Rev 21 第 10.3.6 节](#source-rm0008-exti)。

## 常见坑与出处

| 现象 | 原因 | 处理 | 出处 | 出处能证明的部分 |
| --- | --- | --- | --- | --- |
| 子优先级写得更小，还是打断不了正在跑的 ISR | 抢占相同，子优先级不产生嵌套 | 改抢占数值，不要靠子优先级嵌套 | [PM0056 第 2.3.6 节](#source-pm0056-nvic) | 只有组优先级决定抢占；子优先级只排挂起请求的先后 |
| 按键中断打不断定时器中断 | EXTI0 的抢占数值没有比 TIM2 小 | 把 EXTI0 的抢占数值设得比 TIM2 小 | [PM0056 第 2.3.6 节](#source-pm0056-nvic) | 数值越小，优先级越高 |
| 以为打开尾链后，低优先级能插进高优先级 | 尾链只省掉一次出栈和入栈 | 按抢占级判断谁能打断谁 | [PM0056 第 2.3.7 节](#source-pm0056-nvic) | 尾链发生在 ISR 退出时，不改变谁能抢占 |
| `__disable_irq()` 之后仍进了 NMI | PRIMASK 不管 NMI 和 HardFault | 这是正常行为，不是 PRIMASK 失效 | [PM0056 表 7](#source-pm0056-nvic) | PRIMASK 只挡可配置优先级的异常 |
| 在 ISR 里调用 `HAL_Delay()`，程序停住 | SysTick 的抢占数值不比当前 ISR 小，打断不进来，节拍不走 | ISR 里不等待，置标志交给主循环 | [PM0056 第 2.3.6 节](#source-pm0056-nvic) | 抢占数值相同或更大的异常不能打断正在运行的 ISR |
| 一按键就卡在 EXTI0 的 ISR 里，主循环不再运行 | ISR 没清 EXTI_PR，返回后请求又挂起 | 在 ISR 开头往 EXTI_PR 对应位写 1 | [RM0008 第 10.3.6 节](#source-rm0008-exti)、[PM0056 第 4.3.9 节](#source-pm0056) | 前者：EXTI_PR 写 1 清零；后者：请求没撤掉，返回后会再次挂起 |
| PA0 已经占了 EXTI0，PB0 再配成中断就不触发 | 同一脚号共用一条 EXTI 线 | 第二只按键换一个脚号，比如 PA1 | [RM0008 第 9.4.3 节](#source-rm0008-exti) | EXTI0 的 4 位一次只能选一个端口 |
| 按键挪到 PB0 后不进中断，PA0 碰一下 GND 反而能进 | 没开 AFIO 时钟，EXTICR 写不进去，仍是复位值 0000（A 口） | 先开 AFIO 时钟，再写 EXTICR | [RM0008 第 10.2.5 节](#source-rm0008-exti) | 写 EXTICR 前要先开 AFIO 时钟；这句只在 F1 成立 |

## 相关资源

- 官方手册：**RM0008** 第 10 章（中断与事件 EXTI）、第 9.4.3 到 9.4.6 节（AFIO_EXTICR）。第 9.2.7 节是 GPIOx_LCKR，不是 EXTICR。入栈见 [PM0056 第 2.3.7 节](#source-pm0056-nvic)
- 上一篇：[03 GPIO与LED](03-GPIO与LED.md)｜下一篇：[05 定时器与PWM](05-定时器与PWM.md)
- 手机阅读版：[第 04 章 · 中断与NVIC（公众号图文）](https://mp.weixin.qq.com/s/zxETginoI0WV0MEgcGVrSA)
- 相关图：[`assets/animations/nvic-interrupt-flow.svg`](../assets/animations/nvic-interrupt-flow.svg)、[`assets/animations/gpio-input-interrupt.svg`](../assets/animations/gpio-input-interrupt.svg)、[`assets/diagrams/interrupt-priority.svg`](../assets/diagrams/interrupt-priority.svg)
- 免责声明：本仓库插画均为作者自绘矢量图/程序生成动画，非厂商实拍照片。

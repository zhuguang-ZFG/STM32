---
title: "中断、NVIC/EXTI、CLIC 与双核"
platforms: [f407, f103, gd32, esp32]
---

# 中断、NVIC/EXTI、CLIC 与双核

> 轮询是隔一会儿去门口看有没有快递，中断是快递按门铃。门铃响之后，CPU 不是直接跳进你写的函数：引脚边沿先在 EXTI 变成请求，NVIC 按优先级决定放不放行，内核再从向量表取出地址跳进 ISR。这一章把 F407 的三层链路拆成可复算的地址与位段，用 F103 的 AFIO 与分组对照，最后看 ESP32-S3 的中断分配器、IRAM 纪律与双核分工。标题里的 CLIC 属于 GD32 的 RISC-V 一侧，本章只在跨平台边界指路。

## 本章罗盘

- **问题**：按一下 PF6 的按键，为什么要在 SYSCFG、EXTI、NVIC 和 ISR 里各过一道门？`IRQn = 6` 怎样变成向量槽 22、`ISER[0]` 的 bit6 与 IP 字节 `0xE000E406`？逻辑优先级 5 为什么存成 `0x50`，写成 16 又为什么静默变成最高优先级 0？写 `SCB->AIRCR` 为什么必须带 `0x5FA`？把 `EXTI0_IRQHandler` 名字拼错，为什么中断会永远停在死循环里？ESP32-S3 的中断为什么不是固定向量，`IRAM_ATTR` 与双核分工又在守什么边界？
- **交付**：能从 `IRQn` 推出 ISER 下标、位号与 IP 字节地址；能按 PRIGROUP 表说清抢占与子优先级的切分，并写出带 `0x5FA` 的 AIRCR 值；能用槽号 `IRQn + 16` 与 weak 顶替的 objdump 证据解释 ISR 的落点；能照六步清单配通一条外部中断；能读懂 `esp_intr_alloc` 的源、级、核与 IRAM 标志，并在双核共享数据时选对锁。
- **边界**：四平台章。F407 的地址、位段、probe 读数来自 S4《NVIC 与 EXTI》与 RM0090、PM0214；F103 的 AFIO、HAL 分组与三把总闸来自根书第 04 章与 RM0008、PM0056；ESP32-S3 的中断分配器、IRAM 纪律与双核分工来自 P4《中断与双核》，Cache 一致性与多核内存模型留给[第 34 章](../v4-platforms/34-multicore-cache.md)；GD32 只写边界，CLIC/ECLIC 的完整对照见[第 29 章](../v4-platforms/29-gd32-arm-riscv.md)。SysTick 时基留给[第 11 章](./11-systick-timebase-rtc.md)，UART 中断留给[第 13 章](./13-uart-framed-protocol.md)，RTOS 上下文切换与 FromISR 约束留给[第 23 章](../v3-rtos/23-context-switch-porting.md)、[第 24 章](../v3-rtos/24-queue-semaphore-notification.md)，HardFault 现场留给[第 19 章](../v2-reliability/19-watchdog-reset-hardfault.md)。来源没有记录本章的上板读数，本章不把实验步骤写成已经量到的结果。
- **依据锚点**：S4《S4 NVIC 与 EXTI：打断的艺术》（`mcu/docs/stm32/04-nvic-exti.md`）、根书第 04 章《中断与 NVIC》（`docs/04-中断与NVIC.md`）、P4《P4 中断与双核：IRAM 纪律与核间分工》（`mcu/docs/esp32/04-irq-dualcore.md`）；[第 8 章](./08-architecture-memory-clock.md)的 PPB 与时钟门控、[第 9 章](./09-gpio.md)的引脚配置、[第 2 章](../v0-foundations/02-c-volatile-ub.md)的 volatile 合同、[第 3 章](../v0-foundations/03-struct-abi-registers.md)的寄存器结构体、[第 4 章](../v0-foundations/04-function-pointer-state-machine.md)的函数指针数组。PM0214、RM0090、RM0008、PM0056 与 ESP-IDF v5.5.2 的条文均转引自上述来源。

## 先做出来

开局不烧板，先在宿主机上把 F407 的中断账跑一遍。来源工程把 52 条断言、头文件常数与交叉链接的 objdump 证据收在一个脚本里：

```bash
cd mcu/code/stm32/04-nvic-exti
sh probe.sh
```

输出里先找这三行，它们是本章的骨架：

```text
EXTI0_IRQn = 6    <- stm32f407xx.h:83
EXTI0          6     22 0x0058        0     6 0xE000E100 0xE000E406
== 断言通过 52/52 ==
```

第一行说明门牌号来自头文件，第二行把向量槽、ISER 下标、位号与 IP 字节排成一排，第三行说明宿主机的断言全绿。读之前先押一题：按键走的那条中断线，搬进 NVIC 后的槽号是小于 5、5 到 10 之间，还是大于 10？押完再往下看，猜错不丢分，丢了“地址是推出来的”这个直觉才丢分。

有板的人再加一步：在调试器里读 `NVIC->ISER[0]` 与 `EXTI->PR`，按一次键，看哪一位从 0 变 1、又在你清掉之后回到 0。来源没有记录这一步的板上读数，本章把它留作实验，不写成已跑结果。

## 机制

### 三层链路：EXTI 举旗，NVIC 仲裁，向量表带路

中断不是“一个开关”，而是三个硬件模块接力。S4 的 probe 第 0 段直接从 CMSIS 头文件把这条链挖了出来，每行自带行号引证：

```text
  PERIPH_BASE = 0x40000000    <- stm32f407xx.h:910
  APB2_OFFSET = 0x00010000    <- stm32f407xx.h:928
  SYSCFG_OFFSET = 0x3800      <- stm32f407xx.h:974
  EXTI_OFFSET   = 0x3C00      <- stm32f407xx.h:975
  SCS_BASE      = 0xE000E000  <- core_cm4.h:1550
  NVIC_OFFSET   = 0x0100      <- core_cm4.h:1556
  SCB_OFFSET    = 0x0D00      <- core_cm4.h:1557
```

于是两条例链一目了然：

```text
外设链：PERIPH 0x40000000 -> APB2 +0x10000 -> SYSCFG +0x3800 / EXTI +0x3C00
内核链：SCS 0xE000E000 -> SysTick +0x0010 / NVIC +0x0100 / SCB +0x0D00
```

- **EXTI 在 `0x40013C00`**（APB2 上）：检测边沿、举起请求；
- **SYSCFG 在 `0x40013800`**（APB2 上）：决定 EXTI 线接哪个端口的同号引脚；
- **NVIC 在 `0xE000E100`、SCB 在 `0xE000ED00`**（内核私有外设区 SCS 内）：负责仲裁、呈递与优先级分组。

为什么 NVIC/SCB 的地址在 `core_cm4.h`，而 EXTI/SYSCFG 在 `stm32f407xx.h`？前者是 ARM 定义的 Cortex-M4 内核标配，所有 M4 芯片都一样；后者是 ST 加的外设，各家不同。查手册时，内核问题翻 PM0214，外设问题翻 RM0090。

![PF6 到 ISR 的四层关卡：EXTICR2 选门、EXTI6 设沿、NVIC bit23 放行、EXTI9_5 清 PR bit6](/arch/exti-chain.png)

图上四道门缺一不可：前三个决定请求能不能进 NVIC 并跳到 ISR，最后一个决定这次 ISR 结束后会不会立刻再进。只选门、设沿、放行而忘了清挂起，回调不是不来，而是反复来。

### 三条地址公式：IRQn/32、IRQn%32 与 IP 字节

NVIC 有六组寄存器，前五组是“一位管一个中断”的位图，最后一组是“一个字节管一个中断”的优先级表：

| 寄存器 | 作用 |
| --- | --- |
| ISER | 置位使能（写 1 开中断） |
| ICER | 清除使能（写 1 关中断） |
| ISPR / ICPR | 手工挂起 / 清挂起 |
| IABR | 只读，看哪个中断正在活跃 |
| IPR | 优先级，一个字节管一个中断 |

中断数量超过 32，所以位图是数组，寻址公式就两条：

- 数组下标 = `IRQn / 32`，位号 = `IRQn % 32`（对 ISER/ICER/ISPR/ICPR/IABR）；
- IP 字节地址 = `0xE000E400 + IRQn`（对 IPR）。

![NVIC 地址公式：IRQn 6 推出向量槽 22、ISER 第 0 组 bit 6 与 IP 字节 0xE000E406](/figures/stm32-04-nvic-addr.svg)

拿 USART1 验算：`IRQn = 37`，37 / 32 = **1**、37 % 32 = **5**，所以使能位在 `ISER[1]` 的 bit5，地址 `0xE000E100 + 1×4 = 0xE000E104`；IP 字节是 `0xE000E400 + 37 = 0xE000E425`。S4 的七中断映射表里，这两列都与公式一致：

| 中断 | IRQn | 槽 | 槽偏移 | ISER 下标 | 位 | ISER 地址 | IP 字节地址 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SysTick | -1 | 15 | 0x003C | — | — | （SHP）`0xE000ED23` | — |
| EXTI0 | 6 | 22 | 0x0058 | 0 | 6 | `0xE000E100` | `0xE000E406` |
| EXTI1 | 7 | 23 | 0x005C | 0 | 7 | `0xE000E100` | `0xE000E407` |
| EXTI9_5 | 23 | 39 | 0x009C | 0 | 23 | `0xE000E100` | `0xE000E417` |
| TIM2 | 28 | 44 | 0x00B0 | 0 | 28 | `0xE000E100` | `0xE000E41C` |
| USART1 | 37 | 53 | 0x00D4 | 1 | 5 | `0xE000E104` | `0xE000E425` |
| EXTI15_10 | 40 | 56 | 0x00E0 | 1 | 8 | `0xE000E104` | `0xE000E428` |

第一行的 SysTick 要单独看：`IRQn` 是 **-1**，它是内核异常，优先级不在 NVIC 的 IPR 里，而在 SCB 的 SHP 寄存器 `0xE000ED23`。**NVIC 的位图只服务 `IRQn ≥ 0` 的外设中断**。

### 优先级：4 位字段、左移 4 位、分组与 0x5FA

F407 的优先级寄存器每中断一个字节，但只实现了高 4 位：

```text
  NVIC_PRIO_BITS = 4    <- stm32f407xx.h:49
```

所以 `NVIC_SetPriority()` 写进 IP 字节的值是**逻辑优先级左移 4 位**，低 4 位永远是 0。S4 的编码表：

| 逻辑优先级 | 存入 IP 字节 |
| --- | --- |
| 0 | `0x00` |
| 1 | `0x10` |
| 5 | `0x50` |
| 10 | `0xA0` |
| 15 | `0xF0` |

推论：F407 上逻辑优先级只有 0~15 这 16 档。往 16 以上写不会报错，也不会进下一个中断的字节，只在本字节里截断：

| 写入 | 存入字节 | 读回来当作 |
| --- | --- | --- |
| 16 | `0x00` | 0（最高） |
| 17 | `0x10` | 1 |
| 20 | `0x40` | 4 |
| 255 | `0xF0` | 15 |
| 256 | `0x00` | 0 |

危险的地方在于：越界的数会被静默改写成另一个合法优先级。你想给 16（本该最低），芯片收到 0（最高）；想给 17，收到 1。程序照跑，只有嵌套关系悄悄反了。

`SCB->AIRCR` 的 PRIGROUP 字段（位 [10:8]）决定这 4 位里几位管抢占、几位管子优先级。S4 的分组表：

| PRIGROUP | 抢占位 | 子优先级位 | 写入 AIRCR 的值 |
| --- | --- | --- | --- |
| 0 | 4 | 0 | `0x05FA0000` |
| 1 | 4 | 0 | `0x05FA0100` |
| 2 | 4 | 0 | `0x05FA0200` |
| 3 | 4 | 0 | `0x05FA0300` |
| 4 | 3 | 1 | `0x05FA0400` |
| 5 | 2 | 2 | `0x05FA0500` |
| 6 | 1 | 3 | `0x05FA0600` |
| 7 | 0 | 4 | `0x05FA0700` |

抢占优先级决定能不能打断正在执行的 ISR，数值越小越横；子优先级只在两份请求**同时挂起**时决定谁先上，它没有打断能力。上表第一列的 PRIGROUP 0~3 在 4 位实现下效果相同（4 抢占 + 0 子）。FreeRTOS 要 4 位全给抢占，落在 PRIGROUP 0~3 这一档；SPL/HAL 老代码常见的“组 2”是另一套编号：SPL/HAL 组 2 = 2 抢占 + 2 子（`0x05FA0500`），而 PRIGROUP=2 才是 4+0（`0x05FA0200`）。根书按 HAL 的 `NVIC_PRIORITYGROUP_x` 编号，那张表里的 `GROUP_4` 指“4 位抢占”，与这里的 PRIGROUP 值不是同一套编号；移植时先看位宽，再对名字。

AIRCR 是带锁寄存器：写入时高 16 位必须是 VECTKEY = `0x5FA`，否则写操作被无视。上表第四列的每个值都是钥匙 `0x05FA0000` 再加 PRIGROUP 值左移 8 位拼出来的形状（PRIGROUP=5 即 `0x05FA0500`），出处是 `core_cm4.h:1661` 的 `0x5FAUL << SCB_AIRCR_VECTKEY_Pos`。`NVIC_SetPriorityGrouping()` 内部就是“读 AIRCR、改 [10:8]、带钥匙写回”。

还有一条不能设的优先级：HardFault。打开 `stm32f407xx.h:68-69` 的 `IRQn_Type` 枚举，`NonMaskableInt_IRQn = -14` 之后直接跳到 `MemoryManagement_IRQn = -12`，**-13 被故意跳过**。Reset、NMI、HardFault 的优先级硬件固定：Reset 最高（-3）、NMI 次之（-2）、HardFault 最低（-1），数值从 -3 到 -1 递增、优先级正好递减，与“数值越小越横”一致。这三个不在 SHP 里、不可编程。能设的只有 `IRQn` -12 到 -1 的内核异常（走 SHP）和全部 `IRQn ≥ 0` 的外设中断（走 IPR）。

把“谁能打断谁”演成五幕的是下面这张动画：EXTI0（抢占 2）在跑 ISR 时，同抢占级的 EXTI9 只能挂起排队；抢占号更小的 EXTI1 一到，硬件立刻压栈换人；ISR1 退出后回到 ISR0 的断点，ISR0 再退出才轮到 EXTI9 补位。

![NVIC 抢占判定：谁能打断谁](/anim/nvic-preempt-arbitration.svg)

### 向量表：槽号 IRQn + 16，weak 的位子谁来坐

向量表就是 Flash 起始处的一个 `const` 函数指针数组（[第 4 章](../v0-foundations/04-function-pointer-state-machine.md)讲过函数指针数组）。前 16 项是内核异常，含初始 MSP 与 `Reset_Handler`；外设中断从槽 16 开始排，所以：

- 槽号 = `IRQn + 16`；字节偏移 = 槽号 × 4。

例：`EXTI0_IRQn = 6` → 槽 **22** → 偏移 22 × 4 = **0x58**，正是上一节表格里那一列。S4 的 probe 直接数 `startup_stm32f407xx.s` 的 `.word` 行做交叉核对：

```text
  向量表总项数 = 98（16 内核 + 82 外设，应为 98）
  IRQn -1 -> 向量槽 15 = SysTick_Handler  ✓
  IRQn 6 -> 向量槽 22 = EXTI0_IRQHandler  ✓
  IRQn 23 -> 向量槽 39 = EXTI9_5_IRQHandler  ✓
  IRQn 40 -> 向量槽 56 = EXTI15_10_IRQHandler  ✓
```

第 3 段用交叉工具链真链了一次，objdump 给出三重实证：

```text
Idx Name          Size      VMA       LMA       File off  Algn
  0 .isr_vector   00000188  08000000  08000000  00010000  2**0
08000188 g     F .text	0000001c EXTI0_IRQHandler
  槽22（EXTI0）内容 = 08000189
```

- `.isr_vector` 落在 **0x08000000**（Flash 起始），大小 `0x188` = 392 字节 = 98 × 4，与项数吻合；
- 你在 C 文件里定义 `EXTI0_IRQHandler`，它就是**强符号**，把启动文件里的 weak 默认（`Default_Handler` 死循环）顶替掉。函数名拼错，等于中断永远进死循环；
- 槽里装的是 `0x08000189` = 函数地址 `| 1`，最低位是 Thumb 状态位，向量跳转时靠它保持 Thumb 模式。

### EXTI：选门、设沿、清挂起，六步一条不少

EXTI 寄存器块只有六个，偏移与头文件行号一起列在 S4 的 probe 记录里（基址 `0x40013C00`）：

```text
EXTI_IMR偏移   = 0x00    <- stm32f407xx.h:444    中断屏蔽（1=放行）
EXTI_EMR偏移   = 0x04    <- stm32f407xx.h:445    事件屏蔽
EXTI_RTSR偏移  = 0x08    <- stm32f407xx.h:446    上升沿触发使能
EXTI_FTSR偏移  = 0x0C    <- stm32f407xx.h:447    下降沿触发使能
EXTI_SWIER偏移 = 0x10    <- stm32f407xx.h:448    软件触发
EXTI_PR偏移    = 0x14    <- stm32f407xx.h:449    挂起标志，写 1 清除
```

每个寄存器的 bit N 对应 EXTI 线 N：0~15 接 GPIO，16 以上接 PVD、RTC 等内部源。线 0~15 是逻辑线，同一时刻每条线只能接一个端口的同号引脚：PA6、PB6、PC6 抢 EXTI6 这一条线。选择开关在 SYSCFG_EXTICR：

- EXTICR 起始偏移 `0x08`，绝对地址 `0x40013808`；
- 共 EXTICR1~4 四个寄存器，每个管 4 条线，每条线 4 bit；
- 选择公式：寄存器编号 = 线号 / 4（EXTICR1 管 0~3），字段起始位 = (线号 % 4) × 4；
- 选 F 口写编码 `0x5`（`EXTICR_EXTI0_PF = 0x0005`），选 G 口写 `0x6`。

例：EXTI6 → EXTICR2 的 [11:8]，写 `0x5 << 8 = 0x500`；EXTI10 → EXTICR3 的 [11:8]，同样写 `0x500`。**别忘了开 SYSCFG 时钟**：`RCC_APB2ENR` 的 bit14。不开时钟写 EXTICR 等于往空气里写。

边沿到来 → `EXTI_PR` 置 1 → NVIC 呈递 → 进 ISR。**PR 不会自己清**，你不清它，出 ISR 的瞬间请求又成立，主循环会停摆。清法是往对应位写 1（W1C）。S4 的反汇编里能直接看到这条指令的绝对地址：

```text
08000188 <EXTI0_IRQHandler>:
 800018c:	2101      	movs	r1, #1
 800018e:	f8c3 1c14 	str.w	r1, [r3, #3092]	; 0xc14
```

`0x40013000 + 0xC14 = 0x40013C14`，正是 `EXTI->PR` 的地址。

以 PF6 → EXTI6 为例，六步清单一步都不能少：

| # | 动作 | 关键寄存器 | 漏了会怎样 |
| --- | --- | --- | --- |
| 1 | 开 GPIOF 时钟 | `RCC_AHB1ENR` | 引脚配置写不进 |
| 2 | PF6 配成输入（带上/下拉） | GPIOF `MODER`/`PUPDR` | 电平悬空乱触发 |
| 3 | 开 SYSCFG 时钟 | `RCC_APB2ENR` bit14 | EXTICR 写了不生效 |
| 4 | SYSCFG 选门：EXTI6 接 PF6 | EXTICR2[11:8] = `0x5` | 边沿根本到不了 EXTI |
| 5 | EXTI 设沿放行 | IMR/RTSR/FTSR 的 bit6 | 请求被屏蔽 |
| 6 | NVIC 放行 | `NVIC_SetPriority` + `EnableIRQ` | 中断进不了内核 |

最后写 ISR。注意 EXTI6 没有专属向量：5~9 号线共用 `EXTI9_5_IRQn`（= 23，槽 39），ISR 里要按 PR 的位分辨是谁触发的；0~4 号线才有专属向量。

```c
void EXTI9_5_IRQHandler(void)          /* 强符号顶替 weak 默认 */
{
    EXTI->PR = (1UL << 6);             /* 第一件事：清挂起 */
    /* 只置标志、搬数据，快进快出 */
}
```

### 进出现场：八个字、一个魔法值

![中断现场动画：硬件压栈、取向量、ISR、EXC_RETURN 弹栈](/anim/irq-entry.svg)

进异常的那一刻，内核硬件自动把 **8 个字**压进当前栈：xPSR、PC（返回地址）、LR、R12、R3~R0，正好是 AAPCS 里“调用者可破坏”的那批。ISR 如果还要用 R4~R11，由编译器在 prologue 里补压，所以 ISR 的机器码开头常有一串 `push`。这也是“ISR 要短”的硬约束，不只是风格建议。

进去时 LR 被硬件换成魔法值 **EXC_RETURN**：裸机主循环用 MSP，值是 `0xFFFFFFF9`；若被打断的是跑在 PSP 上的任务（如 RTOS 线程），则是 `0xFFFFFFFD`，两者只差 bit2 的 SPSEL 位（返回 Thread 模式时用 MSP 还是 PSP 弹栈，PM0214）。ISR 末尾一条普通的 `bx lr` 就完成异常返回：硬件认出 LR 里的魔法值，不做普通跳转，而是把之前压栈的 8 个字弹回去，主循环从断点处继续。被打断的代码毫无知觉，这正是共享变量要 `volatile` 的原因（[第 2 章](../v0-foundations/02-c-volatile-ub.md)）。

### F103：同一件事的另一套账

F103 的 EXTI 同样按脚号分 16 条线：PA0、PB0、PC0 共用 EXTI0，不能同时做外部中断。换端口要先开 **AFIO 时钟**，再写 `AFIO->EXTICR`。这是 F1 的做法；F4、L4、H7 把这组寄存器放进 SYSCFG，G0 又挪进 EXTI 自己（`EXTI_EXTICR`）。同一套“选门”概念，三个位置，名字不能照抄。

优先级分组在根书里用 HAL 的宏表示，默认是 `NVIC_PRIORITYGROUP_4`：

| HAL 宏 | 抢占位 | 子优先级位 |
| --- | --- | --- |
| `NVIC_PRIORITYGROUP_0` | 0 | 4 |
| `NVIC_PRIORITYGROUP_1` | 1 | 3 |
| `NVIC_PRIORITYGROUP_2` | 2 | 2 |
| `NVIC_PRIORITYGROUP_3` | 3 | 1 |
| `NVIC_PRIORITYGROUP_4` | 4 | 0（HAL 默认） |

这套编号按“抢占位数”命名，和 S4 的 PRIGROUP 值不是一套编号。移植代码时先确认工程用的是哪套 API，再谈数值。

三把总闸各挡一段：`PRIMASK` 关掉可配置优先级的中断，NMI 和 HardFault 仍能进入；`FAULTMASK` 再挡住 HardFault，仍留 NMI；`BASEPRI` 只挡住优先级数值大于等于阈值的那一截。NMI 不参加 EXTI0 和 TIM2 那种抢占比较。第 8 章讲过 F103 的 CSS 中断走 NMI，所以关中断也挡不住它。

尾链（tail-chaining）在退出时若已有挂起异常，可以省掉一部分出栈再入栈，但它不改变谁有权抢占。低优先级不会因为尾链插进高优先级的 ISR；PM0056 第 2.3.7 节没有给出尾链省下多少周期，本章也不给具体数字。入栈约 12 个 HCLK，72MHz 下约 167ns，不含 ISR 正文。

`HAL_Delay()` 依赖 SysTick 中断。若在 ISR 里调用它，而该 ISR 的优先级又高于 SysTick，计数不前进，就会死等。ISR 里只置标志或塞缓冲区，慢活交回主循环。FreeRTOS 的 FromISR 优先级数值约束另有一套，见[第 24 章](../v3-rtos/24-queue-semaphore-notification.md)。

根书给的按键实验是 PA0 下降沿进 EXTI0，ISR 里只置 `volatile` 标志，主循环消抖后翻转 PC13；连续按 10 次，记录 10 次有效翻转，并在调试器里确认 `EXTI_PR` 已清零。来源只给了步骤与判据，没有记录读数，本章照录为实验设计。

### ESP32-S3：分配器、IRAM 纪律与双核

![中断分配器：99 条源编号分到 CPU0/CPU1 的 7 级中断](/figures/esp32-04-int-alloc.svg)

STM32 上中断与向量一一对应，`EXTI0_IRQn = 6` 永远落到槽 22。ESP32-S3 是**中断矩阵**：外设的中断源可以路由到某个核的某个中断级，分配发生在运行时。

P4 的探针记录：

- `components/soc/esp32s3/include/soc/interrupts.h` 的枚举从 `ETS_WIFI_MAC_INTR_SOURCE = 0` 排到 `ETS_DMA_EXTMEM_REJECT_SOURCE = 98`，随后 `ETS_MAX_INTR_SOURCE` 被编译器打印为 **99**。99 是编号槽位的数量，不是 99 个不同的名字：98 个名字只覆盖 95 个不同编号，23、33、34、46 是保留位，57/58/59 各被两个名字占用（三条 EDGE 与 TARGET 同值）。
- 中断级有 **7 级**：`ESP_INTR_FLAG_LEVEL1..LEVEL6`（`1<<1`..`1<<6`）加 `ESP_INTR_FLAG_NMI`（`1<<7`）。位号就是级别号，源码注释明确要求 `LEVELx` 的值与 `(1<<level)` 对齐。
- `esp_intr_alloc(source, flags, handler, arg, ret_handle)` 一次把外设源、优先级与所属核绑在一起；`flags` 里还可以加 `ESP_INTR_FLAG_SHARED`、`ESP_INTR_FLAG_EDGE`、`ESP_INTR_FLAG_IRAM`、`ESP_INTR_FLAG_INTRDISABLED`。

![IRAM 纪律：ISR 本体、它调用的函数与它读的常量都要在 Cache 关闭时可达](/anim/iram-discipline.svg)

`IRAM_ATTR` 的定义只有一行（`components/esp_common/include/esp_attr.h:23`）：

```c
#define IRAM_ATTR _SECTION_ATTR_IMPL(".iram1", __COUNTER__)
```

它把代码放进 `.iram1` 段，由链接脚本安排到内部 SRAM 的可执行区。它不是“加速”，是“改变落址”。把 `IRAM_ATTR` 加在 ISR 函数上只是第一步，真正的约束是整条执行链都要可达：ISR 本体、它调用的所有非内联函数、它读到的 rodata（字符串常量、查表、`const` 数组）都要在 IRAM 或 DRAM；不要在里面调 `printf`、`malloc` 或任何可能碰 Flash 的 API，跨 ISR/任务传数据用 `...FromISR` API。

`ESP_INTR_FLAG_IRAM`（`1<<10`）是声明侧的开关，语义是一句承诺：我保证这个 ISR 在 Cache 关闭时也能跑。系统的回应是“那就不推迟它”。不标这个标志，系统会在 Flash 操作期间推迟该中断，安全但有延迟；标了却有一条链落在 Flash 里，就是直接崩。P4 的 nm 取证把两种命摆在同一张表上：

```text
0x42008f08  isr_plain    → iram0_2_seg     # 没标 IRAM_ATTR，留在 Flash
0x42008f1c  helper_far   → iram0_2_seg     # 被 IRAM 里的 ISR 调用，却没标
0x4037668c  isr_leaky    → iram0_0_seg     # 标了，本体确实在 IRAM
0x40376698  helper_near  → iram0_0_seg
0x403766ac  isr_tight    → iram0_0_seg     # 整条链都标
0x40376668  isr_rodata   → iram0_0_seg
0x3c028810  k_table      → drom0_0_seg     # 常量还在 Flash
```

`isr_leaky` 的每一条指令都在 IRAM，可它 `callx8` 过去的 `helper_far` 落在 Flash 映射段 `0x42008f1c`；Cache 一关，取指就断在半路。`isr_tight` 的 `call8` 目标 `helper_near` 还在 IRAM 区间内，这才是真的 IRAM-safe。esp32s3 的 IRAM 取指窗口起点是 `0x40374000`，Flash 映射是 `0x42xxxxxx`，常量映射是 `0x3Cxxxxxx`；初代 ESP32 是 `0x400xxxxx` 一片，两代数字不能互抄。P4 还记了一个链接器的坑：IDF 默认带 `-Wl,--gc-sections`，没人引用的 ISR 会被整段收掉，第一版探针的 nm 里只剩 `app_main` 和 `g_hits`，后来用 `g_isr_table` 钉住符号才保住七个。

Cache 关闭窗口的完整机制与多核 Cache 一致性属于[第 34 章](../v4-platforms/34-multicore-cache.md)；本章只记落址判据：ISR 要么整条链进 IRAM，要么老实被推迟。

双核一侧，S3 的 `SOC_CPU_CORES_NUM = 2`，FreeRTOS 跑 SMP，任务默认可以调度到任意核。需要控制核归属时用 `xTaskCreatePinnedToCore(..., xCoreID)`：`0`/`1` 钉到 PRO_CPU/APP_CPU，`tskNO_AFFINITY` 不钉核。`tskNO_AFFINITY` 实测是 `0x7FFFFFFF`，不是 -1；`xTaskCreate` 的函数体只是转调钉核版。能不钉就不钉，钉核会降低调度器灵活性。

双核与中断共享数据时，`volatile` 只阻止编译器优化掉访问，保证不了原子性，也保证不了核间可见性。读-改-写要用 `portMUX` 自旋锁或临界区，临界区要尽可能短；ISR 到任务用队列/通知的 `...FromISR` 版本。线程与锁的细节见[第 23 章](../v3-rtos/23-context-switch-porting.md)与[第 24 章](../v3-rtos/24-queue-semaphore-notification.md)。

## 测量与证据

本章的读数分两类：来源工程在宿主机上实跑的断言与反汇编，以及来源没有记录上板读数的实验。下表把两类分开记。

| 取证项 | 来源命令或位置 | 来源记录里的读数 |
| --- | --- | --- |
| 基址链 | S4 probe 第 0 段 | `SYSCFG 0x40013800`、`EXTI 0x40013C00`、`NVIC 0xE000E100`、`SCB 0xE000ED00`，逐行引 `stm32f407xx.h`/`core_cm4.h` |
| IRQn 枚举 | `stm32f407xx.h:75/83/84/100/105/114/117` | SysTick -1、EXTI0 6、EXTI1 7、EXTI9_5 23、TIM2 28、USART1 37、EXTI15_10 40 |
| 七中断映射表 | S4 `probe.c` 的 `print_irq_table` | EXTI0：槽 22/偏移 `0x0058`/ISER[0] bit6/`0xE000E406`；USART1：槽 53/`0x00D4`/ISER[1] bit5/`0xE000E425` |
| 优先级编码 | S4 `probe.c` 的 `print_prio_encoding` | 0→`0x00`、1→`0x10`、5→`0x50`、10→`0xA0`、15→`0xF0` |
| 越界优先级 | 同上 | 16→`0x00`、17→`0x10`、20→`0x40`、255→`0xF0`、256→`0x00` |
| PRIGROUP 分组 | S4 `probe.c` 的 `print_prigroup_table` | 0~3→4+0、4→3+1、5→2+2、6→1+3、7→0+4；写法 `0x05FA0000` 加 PRIGROUP 左移 8 位 |
| VECTKEY | `core_cm4.h:1661` | `0x5FAUL << SCB_AIRCR_VECTKEY_Pos` |
| 向量表项数 | S4 probe 第 2 段 | 98 项（16 内核 + 82 外设）；-1→15、6→22、23→39、40→56 全对 |
| weak 顶替 | S4 probe 第 3 段 objdump | `.isr_vector` 在 `0x08000000`，大小 `0x188` = 98 × 4；`EXTI0_IRQHandler` 在 `0x08000188`；槽 22 内容 `0x08000189` = 地址 \| 1 |
| 清挂起 | S4 probe 第 3 段反汇编 | `str.w r1, [r3, #3092]` → `0x40013000 + 0xC14 = 0x40013C14` |
| 断言总数 | `sh probe.sh` | 52/52 通过（宿主 gcc） |
| F103 入栈开销 | 根书第 04 章引 PM0056 第 2.3.7 节 | 8 个寄存器、约 12 HCLK、72MHz 下约 167ns；不含 ISR 正文，非示波器实测 |
| F103 按键实验 | 根书第 04 章 | 步骤与判据：按 10 次、10 次翻转、`EXTI_PR` 清零；来源未记录读数 |
| ESP32 中断源 | P4 probe 第 1 段 | `ETS_MAX_INTR_SOURCE = 99`（编号 0~98）；98 个名字覆盖 95 个不同编号 |
| ESP32 中断级 | P4 probe 第 8 段 | `LEVEL1..6` = `1<<1`..`1<<6`，`NMI` = `1<<7` |
| ESP32 IRAM 落址 | `code/esp32/09-iram-discipline` 的 `probe.sh` 第 3/4/6 段 | `isr_leaky 0x4037668c` 调用 `helper_far 0x42008f1c`；`isr_tight 0x403766ac` 调用 `helper_near 0x40376698`；`k_table 0x3c028810` |
| ESP32 双核 | P4 来源 | `SOC_CPU_CORES_NUM = 2`；`tskNO_AFFINITY = 0x7FFFFFFF`；`xTaskCreate` 转调钉核版 |
| ESP32 上板实验 | P4 来源 | “真的关一次 Cache”“ISR 里故意调 printf”“三种核参数打印 `xPortGetCoreID()`”均标“待上机回填”，本章不写成已跑 |

宿主机复跑命令：

```bash
cd mcu/code/stm32/04-nvic-exti
sh probe.sh          # 52 条断言 + 向量表/objdump 取证

cd mcu/code/esp32/09-iram-discipline
sh probe.sh          # 构建后用 nm/.map 给七条链归类（需 ESP-IDF v5.5.2）
```

这些读数的共同结论只有一条：**头文件里算出的地址、写进寄存器的位、反汇编里出现的指令，三样必须能互相对上**。回读只证明“你写的位和你的宏自洽”，不证明向量表真的跳到了你的函数；objdump 里的槽内容才是最终判决。

<QuizBank chapter="s04-nvic" />

## 失败分支

| 现象 | 原因 | 区分证据 | 下一动作 |
| --- | --- | --- | --- |
| 进了 ISR 就再也出不来，主循环停摆 | 没清 `EXTI_PR`，出 ISR 瞬间请求又成立 | `EXTI->PR` 对应位一直为 1 | ISR 第一行写 1 清挂起（W1C） |
| 边沿到了，EXTI 没反应 | SYSCFG 时钟没开，EXTICR 写了不生效 | 读回 EXTICR 与写入不符；`RCC_APB2ENR` bit14 为 0 | 先开 SYSCFG 时钟再选门 |
| 换了端口，按键还是旧端口触发 | 同一编号引脚共用一条 EXTI 线，PA6 与 PB6 抢 EXTI6 | 改 EXTICR 后旧端口仍触发 | 换一个脚号，或只保留一个端口 |
| 中断进不了内核 | NVIC 没使能，或优先级分组与预期不符 | `ISER` 对应位为 0；AIRCR PRIGROUP 被别处改过 | 用 `NVIC_EnableIRQ` 并核对分组 |
| 想把 16 当最低优先级，结果它最横 | `(priority << 4) & 0xFF` 在本字节截断，16→`0x00` | 读回 IP 字节是 `0x00` | 逻辑优先级限制在 0~15 |
| 调 HardFault 优先级没有效果 | HardFault 优先级硬件固定，`IRQn` 枚举里 -13 被跳过 | `IRQn_Type` 中没有 `HardFault_IRQn` | 不设；查 HardFault 现场见[第 19 章](../v2-reliability/19-watchdog-reset-hardfault.md) |
| 中断永远停在死循环 | ISR 函数名拼错，weak 默认 `Default_Handler` 没被顶替 | objdump 的槽内容仍指向默认处理函数 | 对照启动文件的 `.word` 行核对函数名 |
| EXTI9_5 里分不清是谁触发 | 5~9 号线共用向量，ISR 没查 PR | PR 的 bit5~9 哪一个为 1 | ISR 里按 PR 位分支，再逐位清 |
| 尾链打开后低优先级插进了高优先级 | 尾链不改变谁有权抢占 | 抢占级数值没有变小 | 改抢占级，不要指望尾链 |
| `__disable_irq()` 之后仍进了 NMI | PRIMASK 不管 NMI | NMI 是硬件固定优先级 | 这是预期；CSS 的 NMI 要清 CSSC |
| F1 上 EXTI 不进中断 | 没开 AFIO 时钟，或没写 `AFIO->EXTICR` | `AFIO->EXTICR` 读回不是目标编码 | 开 AFIO 时钟、写 EXTICR、清 PR |
| ISR 里 `HAL_Delay()` 死等 | 它依赖 SysTick，而 ISR 优先级高于 SysTick | SysTick 计数不前进 | ISR 只置标志，延时回主循环 |
| ESP32 关 Cache 时 ISR 崩 | 只给本体标了 `IRAM_ATTR`，调用链或 rodata 还在 Flash | nm 地址落在 `0x42xxxxxx`/`0x3Cxxxxxx` | 整条链进 IRAM，或不要声明 `ESP_INTR_FLAG_IRAM` |
| 声明了 IRAM 却仍然崩 | 声明是承诺，系统不再推迟该中断 | 反汇编的 `callx8` 目标在 Flash 映射段 | 整条链排查，别只标本体 |
| 双核共享计数器偶尔少 1 | `volatile` 不保证原子性，也不保证核间可见性 | 读-改-写被另一个核插队 | 用 `portMUX` 或内核对象，临界区尽量短 |
| 任务莫名跑到另一个核 | 没钉核，SMP 调度器自由安排 | 打印 `xPortGetCoreID()` 与预期不符 | 有理由时用 `xTaskCreatePinnedToCore`，否则接受调度 |

## 跨平台边界

F407 这一侧，`IRQn / 32`、`IRQn % 32`、`IP 字节 = 0xE000E400 + IRQn` 与槽号 `IRQn + 16` 都是 Cortex-M4 的内核约定；但 IRQn 的编号、EXTI 线数、SYSCFG 与 EXTI 的偏移是 F407 头文件里的具体值。换同系列型号时，先按对应的 `stm32fxxx.h` 与参考手册重查，不能凭“都是 F4”补一个没读过的位。

F103 一侧，NVIC 与向量表的结构相同，差异在“选门”的位置：F1 用 AFIO 的 `EXTICR`，F4/L4/H7 用 SYSCFG 的 `SYSCFG_EXTICR`，G0 用 EXTI 自己的 `EXTI_EXTICR`。分组还要认准 API 的编号体系：HAL 的 `NVIC_PRIORITYGROUP_x` 按抢占位数命名，SCB 的 PRIGROUP 按 0~7 的值命名，两套名字不能互相套。F103 的入栈开销按 PM0056 的 12 HCLK 计，尾链的具体周期数手册没有给，本章不补。

GD32 只划边界。GD32 的 ARM 型号沿用 Cortex-M 的 NVIC 体系；RISC-V 型号（如 GD32VF103）改用 ECLIC/CLIC，术语、优先级模型与向量方式都换了名字，本章不把 NVIC 的寄存器名带过去。CLIC/ECLIC 的完整对照、中断号地图与向量直跳见[第 29 章](../v4-platforms/29-gd32-arm-riscv.md)；芯片迁移的通用检查表见[第 28 章](../v4-platforms/28-chip-migration-differences.md)。

ESP32 这一侧，没有 NVIC 与固定向量表，中断由分配器在运行时绑定到核与级。P4 的 99 个源编号与 7 级是 ESP32-S3 的具体账，换型号要按对应的 `soc/interrupts.h` 与 `soc_caps.h` 重查；IRAM 取指窗口两代也不同（S3 是 `0x40374000` 起，初代 ESP32 是 `0x400xxxxx` 起）。Cache 映射、Cache 关闭窗口与多核一致性见[第 34 章](../v4-platforms/34-multicore-cache.md)；架构与启动见[第 30 章](../v4-platforms/30-esp32s3-architecture-boot.md)；外设驱动框架见[第 31 章](../v4-platforms/31-esp32-drivers-audio.md)。

## 离开检查

1. 按一下 PF6 的按键，请求从引脚到 ISR 要经过哪三层硬件？SYSCFG 在其中做什么？每一层各负责什么？
2. `USART1_IRQn = 37` 的使能位在 `ISER` 的哪个下标、哪一位？IP 字节地址是多少？SysTick 的 `IRQn = -1` 为什么不在 IPR 里？
3. `NVIC_SetPriority(EXTI0_IRQn, 5)` 实际写进 IP 字节的值是多少？写 16 会变成什么？为什么这是危险而不是报错？
4. PRIGROUP = 5 时，4 位优先级怎样切分？往 `SCB->AIRCR` 写这个分组的完整 32 位值是多少？少了哪一部分会被无视？
5. 向量槽号与 `IRQn` 的关系是什么？`EXTI0_IRQn = 6` 的槽号、字节偏移各是多少？weak 默认处理函数在什么条件下被顶替？
6. 配通 PF6 → EXTI6 的六步是什么？EXTI6 为什么没有自己的向量？ISR 进门第一件事是什么？
7. F103 的 EXTICR 在哪个外设里？HAL 的 `NVIC_PRIORITYGROUP_4` 与 S4 的 PRIGROUP 值为什么不混用？`PRIMASK` 挡不住谁？
8. ESP32-S3 的中断为什么不走固定向量？`IRAM_ATTR` 只标 ISR 本体为什么不够？双核共享计数器为什么不能用 `volatile` 代替锁？

<details>
<summary>对照答案</summary>

1. EXTI 负责把引脚边沿变成中断请求，NVIC 负责按优先级仲裁并呈递，内核再按向量表取地址跳进 ISR。SYSCFG 是 EXTI 前面的选门开关，决定这条线接哪个端口的同号引脚。加上 ISR 清挂起，就是选门、设沿、放行、清挂起四道门。
2. 37 / 32 = 1、37 % 32 = 5，使能位在 `ISER[1]` 的 bit5，地址 `0xE000E104`；IP 字节是 `0xE000E400 + 37 = 0xE000E425`。SysTick 是内核异常（`IRQn = -1`），优先级走 SCB 的 SHP 寄存器，不在 NVIC 的 IPR 里。
3. 5 << 4 = `0x50`，低 4 位永远为 0。写 16 时 `(16 << 4) & 0xFF = 0x00`，读回来当作优先级 0（最高）。越界不报错、不换字节，只在本字节里截断，嵌套关系会悄悄反掉。
4. PRIGROUP = 5 是 2 位抢占 + 2 位子优先级；写入值 `0x05FA0500`。高 16 位必须带 VECTKEY `0x5FA`，少了它整个写操作被硬件无视；组值 5 放 [10:8]，即 `5 << 8 = 0x500`。
5. 槽号 = `IRQn + 16`；`EXTI0_IRQn = 6` → 槽 22 → 偏移 `22 × 4 = 0x58`。启动文件的 weak 默认处理函数会被同名的强符号顶替；函数名拼错，强符号不存在，槽里仍是 `Default_Handler`。
6. 六步：开 GPIOF 时钟、PF6 配输入、开 SYSCFG 时钟、EXTICR2[11:8] = `0x5`、EXTI 的 IMR/RTSR/FTSR bit6、NVIC 设优先级并 `EnableIRQ`。EXTI6 与 5~9 号线共用 `EXTI9_5_IRQn`（槽 39），没有专属向量。ISR 进门第一件事是写 1 清 `EXTI_PR`。
7. F103 的 EXTICR 在 AFIO 里，换端口前要先开 AFIO 时钟。HAL 的 `NVIC_PRIORITYGROUP_x` 按抢占位数命名；S4 的 PRIGROUP 是按 0~7 的值命名，两者不是同一套编号。`PRIMASK` 关可配置优先级中断，挡不住 NMI 与 HardFault；`FAULTMASK` 再挡 HardFault，仍留 NMI。
8. ESP32-S3 用中断矩阵，源、级、核在运行时由 `esp_intr_alloc` 绑定，没有固定向量槽。`IRAM_ATTR` 只改变本体落址，ISR 调用的非内联函数与读的 rodata 仍可能在 Flash，Cache 关闭时取指断在半路。双核共享计数器的 `++` 是读-改-写，`volatile` 既不原子也不提供核间可见性，要用 `portMUX` 或内核对象。

</details>


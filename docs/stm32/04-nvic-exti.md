---
title: S4 NVIC 与 EXTI：打断的艺术
status: done
difficulty: 3
minutes: 40
---

# S4 NVIC 与 EXTI：让按键来"打断"你

> 🎯 轮询是"每隔一会儿跑去门口看有没有快递"，中断是"快递按门铃"。门铃响了之后 CPU 做了什么：怎么去的、怎么回的、两个快递同时按铃谁先，这一章全部讲透。

## 本章精髓

1. 三层链路：**EXTI**（把引脚边沿变成中断请求）→ **NVIC**（按优先级仲裁、呈递给内核）→ **内核**（硬件压栈、取向量表跳转），每一层都要单独配置，漏一层铃就不响。
2. 地址全是公式：**槽号 = IRQn + 16**，**ISER 下标 = IRQn / 32、位号 = IRQn % 32**，**IP 字节 = 逻辑优先级 << 4**。本章每个数字都能在 CMSIS 头文件里找到行号，probe 用 52 条断言把它们全部对撞过一遍。
3. 优先级两组数：抢占优先级（能不能打断别人）与子优先级（同时挂起谁先上）：AIRCR.PRIGROUP 把 4 位优先级切成两份，写 AIRCR 必须带钥匙 0x5FA，全家要用同一把尺子。

- **能理解**：IRQn 6（EXTI0）是怎么变成向量槽 22、ISER[0] bit 6、IP 字节地址 0xE000E406 的，三条公式各推一遍。
- **能用**：照第六节清单给任意一个引脚配通外部中断，并能用 NVIC_SetPriorityGrouping 说清自己的工程用的是哪把"尺子"。

## 先修

- [S3 GPIO](03-gpio.md)；[C5 函数指针](../c/05-func-pointer.md)（向量表就是函数指针数组）、[C6 栈帧](../c/06-abi-stack.md)（硬件压栈的另一半）。

## 先跑起来（10 分钟 quick win）

```bash
cd code/stm32/04-nvic-exti
sh probe.sh   # 宿主 gcc 跑 52 条断言；PATH 里有交叉工具链时附送向量表/objdump 取证
```

输出里找这三行，它们是本章的骨架：

```text
EXTI0_IRQn = 6    <- stm32f407xx.h:83
EXTI0          6     22 0x0058        0     6 0xE000E100 0xE000E406
== 断言通过 52/52 ==
```

读完本章再回头看这张表，每个数字你都能亲手推出来。

敲回车之前，先猜一把：按键走的那条中断线，搬进 NVIC 大楼后的门牌号是小于五、五到十之间、还是大于十？跑完看头文件行号那一栏，猜错了不丢分，丢了直觉才丢分。

## 小节结构

| 小节 | 内容 | 四件套 |
|---|---|---|
| 一、三层链路 | EXTI/SYSCFG/NVIC/SCB 的基址地图，全部来自头文件行号 | 配置 |
| 二、NVIC 寄存器块 | ISER/ICER/ISPR/ICPR/IABR/IPR：IRQn/32 与 IRQn%32 寻址公式 | 配置 |
| 三、优先级 | 4 位字段、<<4 编码、PRIGROUP 分组表、0x5FA 钥匙 | 配置 |
| 四、向量表 | 槽号 = IRQn+16；objdump 实证 weak 默认被强符号顶替 | 代码分析 |
| 五、EXTI 与 SYSCFG | 六个寄存器偏移 + EXTICR 选门公式 | 配置 |
| 六、落地清单 | 六步配通一条外部中断，一步都不能少 | 配置 |
| 七、ISR 现场 | 动画逐帧：硬件压栈 8 字、取向量、EXC_RETURN 弹栈 | 代码分析 |

## 一、三层链路：先把地址地图画出来

四层关卡先收进一张图：选门、设沿、放行、清挂起，顺序就画在实线上。

![按键到 ISR 的四层关卡：SYSCFG 选门、EXTI 设沿、NVIC 放行、ISR 清挂起](/arch/exti-chain.png)

中断不是"一个开关"，而是**三个硬件模块接力**。probe.sh 第 0 段直接从 CMSIS 头文件把这条链挖了出来（每行自带行号引证）：

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

- **EXTI 在 0x40013C00**（APB2 上），负责"检测边沿、举起请求"；
- **SYSCFG 在 0x40013800**（APB2 上），负责"EXTI 线接哪个端口"的多路选择；
- **NVIC 在 0xE000E100、SCB 在 0xE000ED00**（内核私有外设区 SCS 内），负责"仲裁、呈递、分组"。

为什么 NVIC/SCB 的地址在 `core_cm4.h` 而 EXTI/SYSCFG 在 `stm32f407xx.h`？因为前者是 **ARM 定义的 Cortex-M4 内核标配**（所有 M4 芯片都一样），后者是 **ST 加的外设**（各家不同）。这个归属差异记牢，查手册时就知道该翻 PM0214（内核）还是 RM0090（外设）。

## 二、NVIC 寄存器块：IRQn/32 与 IRQn%32 的寻址公式

NVIC 有六组寄存器，每组都是"一位管一个中断"的位图：

| 寄存器 | 作用 |
|---|---|
| ISER | 置位使能（写 1 开中断） |
| ICER | 清除使能（写 1 关中断） |
| ISPR / ICPR | 手工挂起 / 清挂起 |
| IABR | 只读，看哪个中断正在活跃 |
| IPR | 优先级，**一个字节管一个中断**（注意：不是一位） |

中断数量超过 32，所以位图是数组，寻址公式就两条：

- **数组下标 = IRQn / 32**，**位号 = IRQn % 32**（对 ISER/ICER/ISPR/ICPR/IABR）；
- **IP 字节地址 = 0xE000E400 + IRQn**（对 IPR）。

![NVIC 地址公式：IRQn 6 推出向量槽 22（偏移 0x0058）、ISER 第 0 组 bit 6 与 IP 字节 0xE000E406](/figures/stm32-04-nvic-addr.svg)

probe 把七个代表性中断整张表打了出来（宿主编译期 `_Static_assert` 已逐格核对，见 `probe.c:38-79`）：

```text
中断      IRQn    槽 槽偏移 ISER下标   位   ISER地址 IP字节地址
SysTick       -1     15 0x003c        -     -        (SHP) 0xE000ED23
EXTI0          6     22 0x0058        0     6 0xE000E100 0xE000E406
EXTI1          7     23 0x005c        0     7 0xE000E100 0xE000E407
EXTI9_5       23     39 0x009c        0    23 0xE000E100 0xE000E417
TIM2          28     44 0x00b0        0    28 0xE000E100 0xE000E41C
USART1        37     53 0x00d4        1     5 0xE000E104 0xE000E425
EXTI15_10     40     56 0x00e0        1     8 0xE000E104 0xE000E428
```

拿 USART1 验算：IRQn = 37（`stm32f407xx.h:114`），37 / 32 = **1**、37 % 32 = **5**，所以使能位在 `ISER[1]` 的 bit 5，地址 0xE000E100 + 1×4 = **0xE000E104**；IP 字节 0xE000E400 + 37 = **0xE000E425**。两列全中。

注意第一行 SysTick：IRQn 是**负数**（-1，`stm32f407xx.h:75`），它是内核异常，优先级不在 NVIC 的 IPR 里，而在 SCB 的 SHP 寄存器（0xE000ED23）。**NVIC 的位图只服务 IRQn ≥ 0 的外设中断**。

## 三、优先级：4 位字段、左移 4 位、分组表与 0x5FA 钥匙

### 3.1 F407 只实现了高 4 位

```text
  NVIC_PRIO_BITS = 4    <- stm32f407xx.h:49
```

Cortex-M4 的 IP 寄存器是**每中断一个字节**（0~255），但 F407 只实现了高 4 位（`__NVIC_PRIO_BITS = 4`）。所以 `NVIC_SetPriority()` 写入 IP 字节的值 = **逻辑优先级 << 4**，probe 实测编码：

```text
逻辑优先级 存入 0xE000E4xx 的字节
0          0x00
1          0x10
5          0x50
10         0xA0
15         0xF0
```

低 4 位永远是 0，读回来也永远是 0。推论：F407 上**逻辑优先级只有 0~15 这 16 档**。

那写 16 会怎样？把 `core_cm4.h:1818` 那行原话搬过来跑一遍就知道，它既不会报错、也不会进下一个中断的字节：`(priority << 4) & 0xFF` 是**在本字节里截断**，probe 实测（`probe.c` 越界编码表）：

```text
逻辑优先级 存入字节 读回来当作
16         0x00     0
17         0x10     1
20         0x40     4
255        0xF0     15
256        0x00     0
```

真正危险的地方在这儿：**越界的数会被静默改写成另一个合法优先级**。你想给 16（本该最低），芯片收到的是 0（最高）；想给 17，收到的是 1。等号两边都成立，程序照跑，只有嵌套关系悄悄反了，这是真 bug 的高发区，而且它不发警报。

### 3.2 PRIGROUP：把 4 位切成"抢占 + 子"两份

SCB->AIRCR 的 PRIGROUP 字段（位 [10:8]，`core_cm4.h:531`）决定这 4 位里**几位管抢占、几位管子优先级**。probe 打印的分组表：

```text
PRIGROUP  抢占位数 子优先级位 写法（VECTKEY|组值<<8）
0         4          0          0x05FA0000
1         4          0          0x05FA0100
2         4          0          0x05FA0200
3         4          0          0x05FA0300
4         3          1          0x05FA0400
5         2          2          0x05FA0500
6         1          3          0x05FA0600
7         0          4          0x05FA0700
```

- **抢占优先级**：能不能打断正在执行的 ISR（数值越小越横）；
- **子优先级**：两个中断**同时挂起**时谁先上。注意它**没有打断能力**，同抢占级的中断永远互不嵌套。

组 0~3 在 4 位实现下效果相同（4 抢占 + 0 子），表里清清楚楚。FreeRTOS 要求全抢占位（组 4 的反面：它要 4 位全给抢占，即组 0~3 这种 4+0 切法），RT-Thread 同理；而 SPL 老代码常见组 2。**移植 RTOS 时"优先级数值没变、行为全变"的灵异事件，九成是分组尺子换了**。

把"谁能打断谁"演成五幕的，是下面这张动画：EXTI0（抢占 2）在跑 ISR 时，同抢占级的 EXTI9 只能挂起排队，子优先级没有打断能力；而抢占号更小的 EXTI1 一到，硬件立刻压栈换人，ISR1 退出后回到 ISR0 断点，ISR0 再退出才轮到 EXTI9 补位。"实物实验"那一节的按键嵌套实验，验的就是这条时间轴。

![NVIC 抢占判定：谁能打断谁](/anim/nvic-preempt-arbitration.svg)

### 3.3 写 AIRCR 必须带钥匙 0x5FA

AIRCR 是个"带锁"的寄存器：写入时高 16 位必须是 VECTKEY = **0x5FA**，否则写操作被无视。出处在 `core_cm4.h:1661` 的魔数 `0x5FAUL << SCB_AIRCR_VECTKEY_Pos`，所以上表第三列每个写法都是 `0x05FA0g00` 的形状。`NVIC_SetPriorityGrouping()` 内部就是"读 AIRCR、改 [10:8]、带钥匙写回"。

### 3.4 禁转辟谣：HardFault 的优先级**不能**设

打开 `stm32f407xx.h:68-69` 看 IRQn_Type 枚举：

```c
  NonMaskableInt_IRQn         = -14,    /*!< 2 Non Maskable Interrupt   */
  MemoryManagement_IRQn       = -12,    /*!< 4 Cortex-M4 Memory Management Interrupt */
```

**-13 被故意跳过了**：HardFault_IRQn 根本不在枚举里。Reset、NMI、HardFault 的优先级是硬件固定的（-3/-2/-1，越来越高），不在 SHP 里、不可编程。能设优先级的是 IRQn -12（MemManage）起到 -1（SysTick）这段内核异常（走 SHP），外加全部 IRQn ≥ 0 的外设中断（走 IPR）。再看到"把 HardFault 优先级调低"的说法，直接判错。

## 四、向量表：槽号 = IRQn + 16，weak 被顶替的实证

C5 讲过：向量表就是 **Flash 起始处的一个 `const` 函数指针数组**。前 16 项是内核异常（含初始 MSP 与 Reset_Handler），外设中断从槽 16 开始排，所以：

- **槽号 = IRQn + 16**；**字节偏移 = 异常号 × 4**（异常号 = 槽号）。

例：EXTI0_IRQn = 6 → 槽 **22** → 偏移 22 × 4 = **0x58**，正是第二节表格里那一列。probe.sh 第 2 段直接数 `startup_stm32f407xx.s` 的 `.word` 行做了交叉核对：

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

- `.isr_vector` 落在 **0x08000000**（Flash 起始），大小 0x188 = 392 字节 = 98 × 4，与项数吻合；
- 你在 C 文件里定义了 `EXTI0_IRQHandler`，它就是**强符号**，把启动文件里的 weak 默认（Default_Handler 死循环）顶替掉。函数名拼错，等于中断永远进死循环；
- 槽里装的是 `0x08000189` = 函数地址 `| 1`，**最低位是 Thumb 状态位**，向量跳转播 `bx`/`ldr pc` 时靠它保持 Thumb 模式。

## 五、EXTI 与 SYSCFG：选门、设沿、清挂起

### 5.1 EXTI 寄存器块只有六个

probe 连偏移带头文件行号全部挖出（`stm32f407xx.h:444-449`），基址 0x40013C00：

```text
EXTI_IMR偏移   = 0x00    <- stm32f407xx.h:444    中断屏蔽（1=放行）
EXTI_EMR偏移   = 0x04    <- stm32f407xx.h:445    事件屏蔽
EXTI_RTSR偏移  = 0x08    <- stm32f407xx.h:446    上升沿触发使能
EXTI_FTSR偏移  = 0x0C    <- stm32f407xx.h:447    下降沿触发使能
EXTI_SWIER偏移 = 0x10    <- stm32f407xx.h:448    软件触发
EXTI_PR偏移    = 0x14    <- stm32f407xx.h:449    挂起标志，写 1 清除
```

展开成绝对地址：`IMR=0x40013C00 EMR=0x40013C04 RTSR=0x40013C08 FTSR=0x40013C0C SWIER=0x40013C10 PR=0x40013C14`。每个寄存器的 bit N 对应 EXTI 线 N（0~15 接 GPIO，16 以上接 PVD/RTC 等内部源）。

### 5.2 SYSCFG_EXTICR：EXTI 线接哪个端口，这里说了算

EXTI 线 0~15 是"逻辑线"，同一时刻每条线只能接**一个端口**的对应号引脚（PA6/PB6/PC6… 抢 EXTI6 这一条线）。选择开关在 SYSCFG：

- EXTICR 起始偏移 **0x08**（`stm32f407xx.h:547`），绝对地址 **0x40013808**；
- 共 EXTICR1~4 四个寄存器，**每个管 4 条线，每条线 4 bit**；
- 选 F 口写的编码是 0x5（probe 引证 `EXTICR_EXTI0_PF = 0x0005`，`stm32f407xx.h:11662`）。

probe 实测的多路选择表（选 F 口）：

```text
EXTI线  寄存器 字段位    选 F 口要写的值
0        EXTICR1  [ 3: 0]   0x00000005
1        EXTICR1  [ 7: 4]   0x00000050
6        EXTICR2  [11: 8]   0x00000500
10       EXTICR3  [11: 8]   0x00000500
```

公式自己推一遍：寄存器编号 = 线号 / 4，字段起始位 = (线号 % 4) × 4。EXTI6：6/4 → EXTICR2，(6%4)×4 = 8 → [11:8]，0x5 << 8 = 0x500；EXTI10：10/4 → EXTICR3，(10%4)×4 = 8 → [11:8]。全中。

**别忘了开 SYSCFG 时钟**：RCC_APB2ENR 的 bit 14（probe 引证 `stm32f407xx.h:10076`）。不开时钟写 EXTICR 等于往空气里写。

### 5.3 PR 挂起位：写 1 清除，ISR 进门第一件事

边沿到来 → PR 置 1 → NVIC 呈递 → 进 ISR。**PR 不会自己清**，你不清它，出 ISR 的瞬间请求又成立，"无限中断、主循环停摆"就这么来的。清法是**往对应位写 1**（写 0 无效，这是 W1C 语义）。

这不是嘴上说说，probe 第 3 段的反汇编里能直接看到这条清挂起指令的绝对地址：

```text
08000188 <EXTI0_IRQHandler>:
 800018c:	2101      	movs	r1, #1
 800018e:	f8c3 1c14 	str.w	r1, [r3, #3092]	; 0xc14
 ...
 800019c:	40013000 	.word	0x40013000
```

`0x40013000 + 0xC14 = 0x40013C14`，正是 EXTI->PR 的绝对地址（5.1 的表）。ISR 把常数 1 存进去，挂起清掉，门才不堵。

## 六、落地清单：六步把一条外部中断配通

以 PF6 → EXTI6 为例，一步都不能少（缺哪一步，对应的症状也写上了）：

| # | 动作 | 关键寄存器 | 漏了会怎样 |
|---|---|---|---|
| 1 | 开 GPIOF 时钟 | RCC_AHB1ENR | 引脚配置写不进 |
| 2 | PF6 配成输入（带上/下拉） | GPIOF MODER/PUPDR | 电平悬空乱触发 |
| 3 | 开 SYSCFG 时钟 | RCC_APB2ENR bit14（`stm32f407xx.h:10076`） | EXTICR 写了不生效 |
| 4 | SYSCFG 选门：EXTI6 接 PF6 | EXTICR2[11:8] = 0x5（见 5.2 表） | 边沿根本到不了 EXTI |
| 5 | EXTI 设沿放行：IMR bit6=1，FTSR/RTSR bit6=1 | EXTI 0x40013C00 起（见 5.1） | 请求被屏蔽 |
| 6 | NVIC 放行：NVIC_SetPriority(EXTI9_5_IRQn, p) + EnableIRQ | ISER[0] bit23 = 0xE000E100（第二节表） | 中断进不了内核 |

最后写 ISR：

```c
void EXTI9_5_IRQHandler(void)          /* 强符号顶替 weak 默认（第四节） */
{
    EXTI->PR = (1UL << 6);             /* 第一件事：清挂起（5.3 的反汇编实证） */
    /* ... 记账式干活：置标志、搬数据，快进快出 ... */
}
```

注意 EXTI6 没有自己的专属向量：5~9 号线**共用** EXTI9_5_IRQn（=23，槽 39），ISR 里要按 PR 的位分辨到底是哪条线。0~4 号线才有专属向量（EXTI0_IRQn=6 → 槽 22，偏移 0x58）。

## 七、ISR 现场：硬件压栈 8 字与 EXC_RETURN 的归途

![中断现场动画](/anim/irq-entry.svg)

进异常的那一刻，内核硬件自动把 **8 个字**压进当前栈：xPSR、PC（返回地址）、LR、R12、R3~R0，正好是 AAPCS 里"调用者可破坏"的那批（C6 的栈帧知识在这里闭环）。ISR 如果还要用 R4~R11，由编译器在 prologue 里补压。所以 ISR 的机器码开头常有一串 `push`，"ISR 要短"也是硬约束而非风格建议。

进去时 LR 被硬件换成魔法值 **EXC_RETURN = 0xFFFFFFFD**（表示"返回 Thread 模式、用 PSP/MSP 弹栈"的组合编码，PM0214）。ISR 末尾一条普通的 `bx lr` 就完成异常返回，probe 反汇编里 EXTI0_IRQHandler 的最后一条正是 `8000198: 4770 bx lr`。硬件认出 LR 里的魔法值，不做普通跳转，而是把之前压栈的 8 个字弹回去，主循环从断点处无缝继续。被打断的代码**毫无知觉**，这正是 `volatile` 存在的原因（[C3](../c/03-volatile.md)）。

## 附录：工程完整源码

本章取证工程：`code/stm32/04-nvic-exti/`（`sh probe.sh` 一条命令跑完，52/52 断言通过，无需开发板）。

**probe.c**（_Static_assert 对撞头文件 + 四张映射表打印）：

<<< ../../code/stm32/04-nvic-exti/probe.c

**probe.sh**（头文件现挖常数 + 宿主编译运行 + 交叉链接 objdump 取证）：

<<< ../../code/stm32/04-nvic-exti/probe.sh

## 记忆锚点

::: tip 一句话记住
**先 SYSCFG 选门，再 EXTI 设沿，后 NVIC 放行，ISR 进门先清挂起**。四层口诀，中断永不丢。
:::

**延伸**：中断现场压栈与调用约定（[C6](../c/06-abi-stack.md)）直接相关；RTOS 下中断管理见 [F2 上下文切换](../rtos/freertos/02-context-switch.md) 与 [S16 HardFault](16-debug-hardfault.md)。

## 实物实验

- 基础：按键中断点灯，按第六节清单配 PF6 → EXTI6，ISR 里翻转 LED（quick win 完整版）。
- 进阶（抢占眼见为实）：EXTI0 配低抢占优先级、ISR 里 delay 约 1 秒；EXTI1 配高抢占优先级、ISR 翻转另一颗灯。按住键 0 再按键 1，灯 2 **立刻**响应——高优先级打断了低优先级 ISR。把两个优先级调成同抢占级再做一遍：灯 2 要等 1 秒，子优先级没有嵌套能力（第三节）。
- 观察（可选）：逻辑分析仪夹两颗灯，对比两组的波形时序，把"抢占"两个字变成屏幕上的图。

## 常见坑

- **忘清 EXTI_PR 挂起位**：进 ISR 就再也出不来，主循环彻底停摆，ISR 第一行就该清（5.3，反汇编里那条 `str.w` 就是干这个的）。
- **SYSCFG 时钟没开**：RCC_APB2ENR bit14 漏置位，EXTICR 写了不生效，EXTI 死活不触发（清单第 3 步）。
- **优先级分组混用**：SPL 默认组 2、RTOS 要求 4 位全抢占，移植 RTOS 后中断优先级"数值一样行为不同"多源于此（3.2 分组表，F8/R7 联动）。
- **优先级写出 15 以上**：不报错、不拒绝写，`(prio << 4) & 0xFF` 只在**本字节里**截断：16 存成 0x00（变成最高优先级），17 存成 0x10（变成 1）。见 3.1 的实测越界表，四条断言就在 probe 里。
- **想给 HardFault 设优先级**：设不了：`stm32f407xx.h:68-69` 的枚举里 HardFault_IRQn 被故意跳过，它的优先级硬件固定（3.4）。
- **ISR 里调用不可重入函数**：printf/malloc 在中断里用，等着偶发死机（[S7](07-usart.md)/[F4](../rtos/freertos/04-queue.md) 给出正确姿势）。
- **共用向量不分辨线号**：EXTI9_5 / EXTI15_10 是多线共用的，ISR 里不查 PR 就分不清是谁触发的（第六节）。

## 短自测

**1. USART1_IRQn = 37，它的使能位在 ISER 哪个下标、哪一位？IP 字节地址是多少？**

<details><summary>看答案</summary>

下标 = 37 / 32 = **1**，位号 = 37 % 32 = **5**，使能位在 `ISER[1]` 的 bit 5，地址 0xE000E100 + 4 = **0xE000E104**；IP 字节 = 0xE000E400 + 37 = **0xE000E425**。与 probe 打印的映射表一致（该表已过 `_Static_assert` 对撞）。

</details>

**2. `NVIC_SetPriority(EXTI0_IRQn, 5)` 实际写进 IP 字节的值是多少？为什么？**

<details><summary>看答案</summary>

**0x50**。F407 的 `__NVIC_PRIO_BITS = 4`（`stm32f407xx.h:49`），IP 字节只有高 4 位有效，逻辑优先级要左移 4 位：5 << 4 = 0x50。probe 的编码表实测 5 → 0x50。

</details>

**3. 往 SCB->AIRCR 写分组值 5，正确的 32 位写入值是多少？少了哪一部分会被无视？**

<details><summary>看答案</summary>

**0x05FA0500**。高 16 位必须带钥匙 VECTKEY = 0x5FA（`core_cm4.h:1661`），组值 5 放在 PRIGROUP 位 [10:8]（`core_cm4.h:531`），即 5 << 8 = 0x500。少了钥匙，写操作被硬件无视。probe 分组表第三列可直接查到这一行。

</details>

**4. EXTI10 接 PG10，该写哪个 EXTICR 寄存器的哪几位，写什么值？**

<details><summary>看答案</summary>

寄存器 = 10 / 4 → **EXTICR2**……不对，10 / 4 = 2（整数除法）对应 EXTICR**3**（EXTICR1 管 0~3、EXTICR2 管 4~7、EXTICR3 管 8~11）；字段 = (10 % 4) × 4 = 8 → **[11:8]**；选 G 口编码是 0x6（A=0…F=5、G=6），写入值 0x6 << 8 = **0x00000600**。probe 实测表里有同字段的 F 口版本（EXTI10 → EXTICR3[11:8] = 0x500）可对拍。

</details>

**5. 为什么"HardFault 优先级调低一点方便调试"这句话是错的？**

<details><summary>看答案</summary>

HardFault 的优先级是硬件固定值 -1（仅次于 Reset -3、NMI -2），**不可编程**：`stm32f407xx.h:68-69` 的 IRQn_Type 枚举里 NonMaskableInt=-14 之后直接跳到 MemoryManagement=-12，HardFault_IRQn（-13）被故意省略；SHP 寄存器里也没有它的字节。能调的只有 MemManage/BusFault/UsageFault/SVCall/PendSV/SysTick（走 SHP）和全部外设中断（走 IPR）。

</details>

<QuizBank chapter="s04-nvic" />

## 对照表：本章概念 → 仓库落点

| 概念 | 仓库落点 |
|---|---|
| 基址链 PERIPH/APB2/SYSCFG/EXTI | probe.sh 第 0 段输出，引 `stm32f407xx.h:910/928/974/975` |
| 内核链 SCS/NVIC/SCB 基址 | probe.sh 第 0 段输出，引 `core_cm4.h:1550/1556/1557` |
| IRQn 枚举值（含 SysTick=-1） | `stm32f407xx.h:75/83/84/100/105/114/117`，对撞断言 `probe.c:53-59` |
| HardFault 被省略的枚举空洞 | `stm32f407xx.h:68-69` |
| ISER/IPR 寻址公式与七中断映射表 | `probe.c:97-148`（`print_irq_table`） |
| `__NVIC_PRIO_BITS = 4` | `stm32f407xx.h:49`，对撞断言 `probe.c:46` |
| 逻辑优先级 << 4 编码表 | `probe.c:186-213`（`print_prio_encoding`） |
| 越界优先级实测（16→0x00、17→0x10、20→0x40、256→0x00） | 同一函数下半段，四条 `CHECK` 在 `probe.c:196-212` |
| PRIGROUP 位 [10:8] 与分组表 | `core_cm4.h:531-532`，`probe.c:157-178`（`print_prigroup_table`） |
| VECTKEY = 0x5FA 写入钥匙 | `core_cm4.h:1661`，对撞断言 `probe.c:48` |
| 向量槽 = IRQn+16、98 项核对 | probe.sh 第 2 段输出（`probe.sh:113` 起） |
| weak 被强符号顶替、槽内容 \|1 | probe.sh 第 3 段 objdump 输出（`probe.sh:139-189`） |
| EXTI 六寄存器偏移 | `stm32f407xx.h:444-449`，对撞断言 `probe.c:73-79`，打印 `probe.c:226-239` |
| EXTICR 选门公式与实测值 | `stm32f407xx.h:547/11662`，`probe.c:204-224`（`print_exticr_mux`） |
| SYSCFG 时钟使能位 | RCC_APB2ENR bit14，`stm32f407xx.h:10076` |
| ISR 清挂起的反汇编实证 | probe.sh 第 3 段：`str.w r1, [r3, #3092]` → 0x40013C14 |

## 你做到了

- 中断从"会自动跳的函数"还原成"三层配置 + 三条寻址公式 + 两段压栈"的机制，每个数字都能在头文件里指到行号；
- 优先级与嵌套有了肌肉记忆：4 位字段、<<4 编码、分组尺子、0x5FA 钥匙，一个都绕不开，这是 RTOS 章节的地基之一；
- 手握六步清单，能配通任意引脚的外部中断，也知道每一步漏掉的典型死法。

门牌是六，押在五到十之间就算中。这一章的每个数字你都不是背的，是顺着头文件行号现推的。

<div class="achievement">
✅ 下一站：<a href="05-systick.html">S5 SysTick</a>：内核自带的"心跳发生器"，也是 RTOS tick 的真身。
</div>

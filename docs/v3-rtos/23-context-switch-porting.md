---
title: "上下文切换与移植"
platforms: [f407]
---

# 上下文切换与移植

任务 A 和任务 B 各有一个栈，CPU 只有一个。把 A 的 R4–R11 压进 A 的栈、把栈顶写进 A 的 TCB，再从 B 的 TCB 取出栈顶、把 B 的寄存器弹回来——这套动作发生在 PendSV 里。FreeRTOS 把「谁上 CPU」拆成三个异常：SVC 把第一个任务送上去，PendSV 换现场，SysTick 报时。移植一个 Cortex-M4F 工程，核心就是让这三个名字接上向量表，再选对 port 目录。

证据先说清：本章没有新的上板读数。F2 的五步 probe、GDB 软件帧，F8 的 `size`/`nm` 与上板状态表，都没有在本仓库留下原始日志或产物：probe 与 `size`/`nm` 标「来源说法(未复核)」，GDB 与上板现象标「未实测」。18 字 = 72 B、26 字 = 104 B、软件帧 9 字、SHPR3 里的 0xFF 与 `0x50 < 0xFF`，由源码与算术得到，标「文档推导」。

> 版本口径：本章的 `port.c`、`portmacro.h`、`tasks.c` 行号与宏语义按 FreeRTOS-Kernel V11.1.0 的 GCC/ARM_CM4F 端口对账；根书第 15 章引 V11.3.2，两版行号不混排。F103 的 `ARM_CM3` 只讲机制差异，不把 V11.1.0 的行号套过去。

## 本章罗盘

- **问题**：SVC、PendSV、SysTick 三个异常各由哪个函数接管，向量表和 `#define` 怎么对上？PendSV 为什么必须最低，`configKERNEL_INTERRUPT_PRIORITY` 为什么已经是不被读取的死宏？挂起位在哪个寄存器、`portYIELD` 到底做了什么？硬件压哪 8 个字、软件补哪 9 个字，恢复时为什么最后一条是 `bx r14`？FPU 行李凭什么用 EXC_RETURN bit4 判断，s0–s15 与 s16–s31 分别归谁？PendSV 的十一条语义步骤是什么，`vTaskSwitchContext` 改了哪个变量？F407 为什么用 `ARM_CM4F`、F103 为什么用 `ARM_CM3`？`0x50` 与 `0xFF` 谁更急，FromISR 的逻辑阈值是 5 还是 80？`xTaskCreate` 堆尽返回什么？奇数优先级断言为什么在 F407 不执行？HardFault 归 FreeRTOS 还是归应用？RT-Thread Nano 的切换文件、异常符号和堆边界符号各是什么？
- **交付**：能在纸上画出无 FPU 的 8 + 9 字现场与有 FPU 的 26 + 25 字现场；能把三个异常、三个源码名、三个向量名和三行 `#define` 对上号；能算出 SHPR3 的 PendSV/SysTick 两个字节都是 0xFF，并说清 `0x50 < 0xFF` 的方向；能按内核和 FPU 选出 `ARM_CM4F` 或 `ARM_CM3`；能把 RT-Thread Nano 的 `context_gcc.S`、`PendSV_Handler`/`HardFault_Handler`、`SysTick_Handler` 与 `&__bss_end__`→`&_estack` 讲对。
- **边界**：单平台 F407（Cortex-M4F、`ARM_CM4F`、lab 跑 HSI 16 MHz）；F103 只在「跨平台边界」做机制对照。SysTick 的 LOAD 与寄存器细节在第 11 章，异常进出与 EXC_RETURN 的 8 字帧在第 10 章；队列、信号量与通知留给第 24 章，双 OS 选型留给第 27 章。RT-Thread 部分按 lab 的 Nano 工程写，不把标准版 BSP 的 25 MHz 晶振当本工程事实。
- **依据锚点**：F2《上下文切换》（`mcu/docs/rtos/freertos/02-context-switch.md`）、F8《移植 FreeRTOS 到霸天虎》（`mcu/docs/rtos/freertos/08-port-f407.md`）、R7《移植 RT-Thread 到霸天虎》（`mcu/docs/rtos/rtthread/07-port-f407.md`）；配置见 `mcu/code/rtos/01-freertos-lab/FreeRTOSConfig.h`，板级见 `mcu/code/rtos/02-rt-thread-lab/board/board.c`，端口选择见 `mcu/code/rtos/01-freertos-lab/Makefile`，向量槽见 `mcu/code/rtos/01-freertos-lab/startup_stm32f407xx.s`。异常进出的 8 字帧见 [v1 第 10 章](../v1-drivers/10-interrupts-nvic-exti.md)；TCB 偏移 0 与首帧 18 字见 [第 22 章](./22-tasks-tcb-scheduler.md)。

## 先做出来

不接板，先把四笔账算在纸上。它们决定你上板后看到的是「切换真的没发生」，还是「名字根本没接上」。

1. **三异常账**：FreeRTOS 的 port 层给出三个函数，启动文件的向量表认三个 CMSIS 名，中间靠三行 `#define` 对上。把这张表抄一遍，再数一遍行号：

   | 异常 | 干什么 | 源码函数（`port.c`） | 向量槽（`startup_stm32f407xx.s`） | CMSIS 名 |
   | --- | --- | --- | --- | --- |
   | SVC（异常号 11） | 启动第一个任务 | `vPortSVCHandler`（`:260`） | `:108` | `SVC_Handler` |
   | PendSV（异常号 14） | 保存当前、恢复下一个 | `xPortPendSVHandler`（`:505`） | `:111` | `PendSV_Handler` |
   | SysTick（异常号 15） | 报时，必要时挂 PendSV | `xPortSysTickHandler`（`:562`） | `:112` | `SysTick_Handler` |

   三行映射在 `FreeRTOSConfig.h:75-77`。F8:116,268 写的是 `74-77`，但 `:74` 是注释行「端口映射」，不是 `#define`；差一行，改配置时容易把注释当宏。

2. **帧长账**：一次切换保存多少字，取决于这趟有没有 FPU 行李。先把无 FPU 的账算死，再把 FPU 那一列加上：

   | 现场 | 硬件帧 | 软件帧 | 合计 |
   | --- | --- | --- | --- |
   | 无 FPU，运行中保存 | 8 字 = 32 B（R0–R3、R12、LR、PC、xPSR） | 9 字 = 36 B（R4–R11 + EXC_RETURN） | 17 字 = 68 B |
   | 无 FPU，新任务首帧 | 8 字 | 9 字 | 18 字 = 72 B（多 1 个对齐字，见第 22 章） |
   | 有 FPU，运行中保存 | 26 字 = 104 B（8 核心字 + s0–s15 + FPSCR + 1 对齐） | 25 字 = 100 B（9 字 + s16–s31） | 51 字 = 204 B |

   新任务首帧的 `EXC_RETURN` 固定为 `0xFFFFFFFD`，bit4 = 1，所以没有 FPU 扩展帧，是 18 字而不是 26 字；26 字是任务跑过浮点、被切走时硬件扩展帧的长度，不是首帧。

3. **优先级账**：PendSV 与 SysTick 的槽位都在 SHPR3，port 启动时把两个字节都写成 0xFF；`configMAX_SYSCALL_INTERRUPT_PRIORITY` 是 `0x50`，逻辑 5。把三个表示放在一张表里，别把原始值当逻辑值：

   | 项 | 原始值 | 逻辑优先级 | 方向 |
   | --- | --- | --- | --- |
   | PendSV（SHPR3 `[23:16]`） | `0xFF` | 15 | 最低 |
   | SysTick（SHPR3 `[31:24]`） | `0xFF` | 15 | 最低 |
   | `configMAX_SYSCALL_INTERRUPT_PRIORITY` | `0x50` | 5 | 比内核急 |

   `0x50 < 0xFF` 才是正确的大小关系：数值更小的 syscall 阈值更急。能调 `...FromISR()` 的是逻辑优先级 ≥ 5（原始值 ≥ `0x50`）的中断；逻辑 0–4 的中断不受 `BASEPRI` 屏蔽，不许碰 FreeRTOS API。

4. **port 选型账**：F407 用 `ARM_CM4F`，F103 用 `ARM_CM3`。MCU 参数、FPU 开关与 port 目录是一组绑定关系，改一个就要改另一个：

   | 目标 | 内核 | FPU | port 目录 | 编译参数 | 选错的后果 |
   | --- | --- | --- | --- | --- | --- |
   | F407 | Cortex-M4F | 单精度 | `portable/GCC/ARM_CM4F` | `-mfpu=fpv4-sp-d16 -mfloat-abi=hard` | 拿 `ARM_CM4`：编译过，切换不保存浮点寄存器，任务间互相踩 |
   | F103 | Cortex-M3 | 无 | `portable/GCC/ARM_CM3` | `-mcpu=cortex-m3 -mthumb` | 拿 `ARM_CM4F`：编译过，调度器启动进 HardFault |

   这四笔账只需要源码、启动文件与算术，不需要板子；后面每个机制都可以回到这四行对账。

## 机制

### 一、三异常接管：SVC 起第一个任务，PendSV 换现场，SysTick 报时

FreeRTOS 的移植层把三个动作分别挂到 Cortex-M 的三个异常上，分工固定（F8:88-136 把这三件事写成一张接管表）：

- **SVC**：调度器启动时，`vPortStartFirstTask` 执行一条 `svc 0`；`vPortSVCHandler`（`port.c:260`）从 `pxCurrentTCB->pxTopOfStack` 弹出 9 字软件帧，写 PSP，清零 BASEPRI，最后 `bx r14`。异常返回时硬件按 `EXC_RETURN` 弹出 8 字硬件帧，第一个任务从入口开始跑，handler 自己不再返回。
- **PendSV**：任务主动让出、SysTick 发现该换人、中断里置了挂起位，最终都落到 `xPortPendSVHandler`（`port.c:505`）。它保存当前现场、调用 `vTaskSwitchContext`、恢复下一个现场，细节在第六节。
- **SysTick**：`xPortSysTickHandler`（`port.c:562`）在临界区里调 `xTaskIncrementTick`；返回值是 `pdTRUE` 时，置 PendSV 挂起位，然后退出。它只报案，不换人。

启动文件里三个槽位是标准 CMSIS 名（`startup_stm32f407xx.s:108,111,112`）；port 源码里是 FreeRTOS 名。接法有两种：改启动文件，把 `SVC_Handler` 等直接改成 `vPortSVCHandler`，侵入启动文件；或者保留启动文件不动，在 `FreeRTOSConfig.h:75-77` 用三行 `#define` 在预处理阶段改名。lab 走第二种：

```c
/* FreeRTOSConfig.h:75-77；:74 是“端口映射”注释，不是宏 */
#define vPortSVCHandler     SVC_Handler
#define xPortPendSVHandler  PendSV_Handler
#define xPortSysTickHandler SysTick_Handler
```

改名之后，目标文件里只剩 `SVC_Handler`、`PendSV_Handler`、`SysTick_Handler` 三个符号；`xPortPendSVHandler` 在 ELF 里不存在，GDB 断前者断不上。F8:131-136 的 `nm` 地址与三个 `T` 是构建时的来源说法(未复核)，本仓库没有保存那次 `nm` 的输出。

SVC 启动的第一个任务，用的就是第 22 章那套伪造首帧：`pxPortInitialiseStack` 在任务栈里摆好 18 字，`pxTopOfStack` 指向最低的 R4 槽位；SVC 的 `ldmia r0!, {r4-r11, r14}` 把它弹回，`bx r14` 再让硬件弹 8 字。第一个任务没有「上一次被切走」的现场，这份现场是创建任务时手工写的。

![伪造首帧：pxPortInitialiseStack 手工造 18 字栈帧](/figures/rtos-02-fake-frame.svg)

图里写明硬件帧 8 字、软件帧 9 字、对齐 1 字，共 18 字 = 72 B；真正被写入的是 xPSR、PC、EXC_RETURN 等少数槽位。SVC 恢复的就是这份帧，不是运行中被 PendSV 保存的帧。

![FreeRTOS 三异常接管：port.c 的三个处理器经 #define 改名接到向量表 CMSIS 名](/anim/freertos-port.svg)

图的主线是三个源码名到三个向量名的改名，后半还画了 port 选型、两份优先级与 RAM 两套账。图里沿用旧来源口径的两句——「≥80 才许调 FromISR」与「池尽时 xTaskCreate 返回 pdFAIL」——与正文按 V11.1.0 的更正相抵：`0x50` 是 8 位原始值，逻辑阈值是 5；`xTaskCreate` 堆尽返回负的错误码，不是 0。以正文为准。

### 二、PendSV 为什么必须最低，配置宏为什么不再是活宏

ARM_CM4F 的 port 在启动时做两件事（`port.c:434-435`）：

```c
portNVIC_SHPR3_REG |= portNVIC_PENDSV_PRI;    /* portNVIC_PENDSV_PRI  = portMIN_INTERRUPT_PRIORITY << 16 */
portNVIC_SHPR3_REG |= portNVIC_SYSTICK_PRI;   /* portNVIC_SYSTICK_PRI = portMIN_INTERRUPT_PRIORITY << 24 */
```

`portMIN_INTERRUPT_PRIORITY` 在 `port.c:65` 定义成 `255UL`，所以 SHPR3 的 `[23:16]`（PendSV）与 `[31:24]`（SysTick）两个字节都写成 `0xFF`，逻辑 15，全系统最低。V11.1.0 的 ARM_CM4F port **不再读 `configKERNEL_INTERRUPT_PRIORITY`**；配置里那行 255 留着无害，改它不影响行为，删掉也不会改变 SHPR3 的写入值。F2:81,303 已经把这条说对。

F8:15,149,154 把 `configKERNEL_INTERRUPT_PRIORITY` 当成「必须配置」的活宏，是来源说法有误，已按 `port.c:65,434-435` 更正。F2:77 写「`portMIN_INTERRUPT_PRIORITY` 就是 `configKERNEL_INTERRUPT_PRIORITY`」也容易读成活宏：两者数值同为 255，但 port 用的是自己的常量，不读配置。F2:79 的「SysTick 优先级高」与同页「两者都填 0xFF」自相矛盾；按 ARM_CM4F port，PendSV 与 SysTick 都是最低，SysTick 不高于 PendSV。

为什么两个都要最低？切换要等所有 ISR 服完役。SysTick 在中断里只置 PendSV 挂起位；如果它在自己的 ISR 里直接换现场，一个更高优先级的中断晚到，就会把换到一半的现场打断。PendSV 排在最低，所有更高优先级异常处理完、异常返回时 NVIC 才把它排上来（尾链），这时换现场不会压住任何 ISR。`vTaskSwitchContext` 前后再用 `BASEPRI` 关一小段临界区，保护就绪表。

### 三、挂起位：ICSR 的 bit28

PendSV 的「请求」不是函数调用，是一个挂起位。`portmacro.h:99-100` 给出地址与位号：

```c
#define portNVIC_INT_CTRL_REG   ( *( ( volatile uint32_t * ) 0xe000ed04 ) )
#define portNVIC_PENDSVSET_BIT  ( 1UL << 28UL )
```

`portYIELD_WITHIN_API()` 的全部动作就是写这一位：`portNVIC_INT_CTRL_REG = portNVIC_PENDSVSET_BIT;`（`portmacro.h:91`；F2:54,61-62）。`taskYIELD()` 走 `portYIELD()`，中断里走 `portYIELD_FROM_ISR(x)`（`x` 为真才置位）。置位之后当前异常继续返回；等所有更高优先级异常退场，PendSV 才以最低优先级执行。挂起位是「排队」，不是「立即切」——这一点在第 22 章的 tick 三段里已经埋下，本章只补上最后一步。

### 四、软硬分工：硬件 8 字，软件 9 字

异常入场时，硬件自动把 8 个字压进当前任务的栈（若用 PSP）：R0、R1、R2、R3、R12、LR、PC、xPSR。其中 R0–R3 与 R12 是 AAPCS 的调用者保存寄存器，硬件替你管；LR、PC、xPSR 是异常现场字，也一并压进去。R4–R11 是「被调者保存」：函数要用就自己存，硬件不认识这个约定，所以 PendSV 里软件手工补压。恢复时顺序相反：软件先弹 R4–R11 与 EXC_RETURN，写回 PSP，最后 `bx r14`，硬件再按 EXC_RETURN 弹 8 字（有 FPU 时 26 字）。

```asm
stmdb r0!, {r4-r11, r14}   ; 一条指令写 9 个字 = 36 B：R4–R11 + EXC_RETURN
str   r0, [r2]             ; 新栈顶写进 TCB 偏移 0
```

软件帧为什么是 9 字而不是 8 字？多出来的是 EXC_RETURN。异常入场时它装在 LR 里，但 LR 也会被硬件压进硬件帧；软件再把它存进软件帧，恢复时才能先弹回 r14，用 `bx r14` 让硬件知道该用哪个栈、这趟有没有 FPU 帧。少了这 9 字里的任何一个，`ldmia` 的偏移就会整体错位。

![PendSV 软硬分工：硬件压 8 字，软件补 R4–R11 与 EXC_RETURN 共 9 字；换 TCB 后先弹 9 字、写 PSP，再 bx r14，首帧 18 字](/arch/context-switch.png)

图把硬件侧写成「免费」：8 个寄存器压栈由异常入场完成；返回时由 EXC_RETURN 决定用哪个栈。软件侧一条 `stmdb r0!, {r4-r11, r14}` 存 9 字，末尾的 `r14` 就是 EXC_RETURN；恢复时先弹 9 字、把新栈顶写回 PSP，再 `bx r14`。图里也画了 TCB 换指针、`msr psp, r0` 与首帧 18 字的账。

`str r0, [r2]` 为什么敢按偏移 0 写？因为 `pxTopOfStack` 必须是 TCB 的第一个成员，这是第 22 章讲过的 ABI 硬约束；恢复时 `ldr r0, [r1]` 也从偏移 0 取新栈顶。硬件帧的 8 字布局与 [v1 第 10 章](../v1-drivers/10-interrupts-nvic-exti.md) 的异常入场动画是同一份账，本章不重画。

### 五、FPU 行李：EXC_RETURN bit4 是行李牌

Cortex-M4F 的异常帧有两档：任务没跑过浮点，EXC_RETURN bit4 = 1，硬件只压 8 字核心帧；任务跑过浮点，bit4 = 0，硬件扩展帧带 s0–s15 与 FPSCR，共 26 字。软件这边，PendSV 先用 `tst r14, #0x10` 看 bit4，再用 `it eq` + `vstmdbeq r0!, {s16-s31}` 补存 s16–s31（16 字 = 64 B）；bit4 = 1 时两条条件指令直接跳过。恢复时同样：`vldmiaeq r0!, {s16-s31}` 只在有行李时执行。

分工的根是 AAPCS：s0–s15 是调用者保存，硬件顺手压；s16–s31 是被调者保存，软件补。完整的 FPU 现场是硬件 26 字扩展帧加软件 25 字（9 字核心帧 + 16 字 s16–s31），共 51 字。新任务首帧的 EXC_RETURN 是 `0xFFFFFFFD`，bit4 = 1，所以首帧没有 FPU 行李，是 18 字；等它第一次真正用浮点、再被切走，才会出现 26 + 25 字的那笔账。

M4F 还有懒堆叠：FPCCR 的 LSPEN 默认开，异常入场时硬件先给 FPU 帧**预留空间**，真用到浮点才写数，不用浮点的中断省下这笔开销。这就是「先占座、后写真」；EXC_RETURN bit4 是这趟有没有行李的牌子（`F2:103-105,116-119,264`）。图与文字都是原理示意，没有示波器或 GDB 读数。

### 六、PendSV 的十一条语义步骤

V11.1.0 ARM_CM4F 的 `xPortPendSVHandler`（`port.c:505-560`）是 naked 内联汇编。下面按 F2:107-207 的语义转写，② 与 ⑥ 是教学写法：源码 ② 写 `ldr r3, pxCurrentTCBConst`，⑥ 写 `mov r0, %0` 并在操作数里代入 `configMAX_SYSCALL_INTERRUPT_PRIORITY`，编出来是 `#80`（即 `0x50`）。字节账不要按这段转写算。

```asm
mrs   r0, psp                  ; ① 当前任务的栈顶
isb
ldr   r3, =pxCurrentTCB        ; ② &pxCurrentTCB
ldr   r2, [r3]                 ;    当前 TCB
tst   r14, #0x10               ; ③ EXC_RETURN bit4 = 0？有 FPU 行李
it    eq
vstmdbeq r0!, {s16-s31}        ;    软件补存 s16–s31
stmdb r0!, {r4-r11, r14}       ; ④ 软件帧 9 字
str   r0, [r2]                 ; ⑤ 新栈顶写回 TCB 偏移 0
stmdb sp!, {r0, r3}            ;    进临界区前保存 r0/r3
mov   r0, #0x50                ; ⑥ = configMAX_SYSCALL_INTERRUPT_PRIORITY
msr   basepri, r0
dsb
isb
bl    vTaskSwitchContext       ; ⑦ 只换 pxCurrentTCB
mov   r0, #0
msr   basepri, r0              ; ⑧ 出临界区
ldmia sp!, {r0, r3}
ldr   r1, [r3]                 ; ⑨ 新 TCB
ldr   r0, [r1]                 ;    新栈顶
ldmia r0!, {r4-r11, r14}       ; ⑩ 弹软件帧 9 字
tst   r14, #0x10
it    eq
vldmiaeq r0!, {s16-s31}        ;    有行李就领回
msr   psp, r0                  ; ⑪ 写 PSP
isb
bx    r14                      ;    异常返回，硬件弹硬件帧
```

| 步 | 动作 | 关键点 |
| --- | --- | --- |
| ① | `mrs r0, psp` | 线程用 PSP，不用 MSP |
| ② | 取当前 TCB | `pxCurrentTCB` 是全局指针 |
| ③ | 条件存 s16–s31 | `tst r14,#0x10` + `it eq` |
| ④ | 存 9 字软件帧 | R4–R11 + EXC_RETURN |
| ⑤ | 写回栈顶 | `str r0,[r2]` 偏移 0 |
| ⑥ | BASEPRI 临界 | `0x50` 屏蔽逻辑 5–15 |
| ⑦ | `vTaskSwitchContext` | 换人就落在 `pxCurrentTCB`（`tasks.c:5056`） |
| ⑧ | 恢复 BASEPRI | 0 表示不屏蔽 |
| ⑨ | 取新 TCB 与栈顶 | 仍从偏移 0 取 |
| ⑩ | 弹 9 字 + 条件弹 FPU | 与 ③④ 相反的顺序 |
| ⑪ | 写 PSP + `bx r14` | 硬件按 EXC_RETURN 弹 8 或 26 字 |

`vTaskSwitchContext` 的 C 侧核心动作只有一步：把 `pxCurrentTCB` 指向最高优先级就绪任务的 TCB（选最高的位图与 CLZ 在第 22 章）。挂起计数、追踪钩子不改变「下一个是谁」；换指针是决策，PendSV 后面的九步是执行。

![上下文切换动画：TaskA 的硬件帧与 R4–R11 压进自己的栈，栈顶藏进 TCB，换到 TaskB 的栈再弹回](/anim/context-switch.svg)

图里两个任务栈此消彼长，TCB 的 `pxTopOfStack` 各指自己的栈顶，PendSV 标为全系统最低。动画把软件帧画成 R4–R11 八个字，没画第 9 个 EXC_RETURN；完整布局以本节的 9 字账为准。

F2:158-178,337 还给过一笔「27 条指令、正文 90 B + 两条 nop 6 B + 字面量 4 B + 两条 nop 4 B = 104 B」的字节账。仓库里没有那段 `objdump` 原文，这条 NOP=6 字节的账只能标「来源说法(未复核)」，待拿到反汇编原文再核；能确认的只有一条：一次切换走一段直线代码，没有循环，`tst/it` 是条件执行，不改变控制流。

### 七、port 选型：`ARM_CM4F` 与 `ARM_CM3`

F407 用 `portable/GCC/ARM_CM4F`，F103 用 `portable/GCC/ARM_CM3`。`F` 是 FPU：Cortex-M4F 带单精度硬件浮点，任务切换要额外保存 s0–s31；Cortex-M3 没有 FPU，port 里没有这段行李。lab 的 Makefile 把这件事写死在三处（`Makefile:34,36-37,57`）：

```makefile
MCU := -mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard
INC := -I. -I$(FREERTOS_KERNEL)/include \
       -I$(FREERTOS_KERNEL)/portable/GCC/ARM_CM4F
```

`-mfloat-abi=hard` 与 `ARM_CM4F` 是一对：编译器按硬浮点 ABI 生成 `s0`/`s1` 参数传递，port 必须保存这些寄存器。F407 上若拿不带 `F` 的 `ARM_CM4`，编译照过，切换时不存浮点寄存器，两个任务的浮点值互相踩；F103 上若拿 `ARM_CM4F`，编译也能过，但 M3 不认 FPU 指令与扩展帧，调度器一启动就进 HardFault（`F8:65-86`；`R15:187`）。判断方法只有一条：看 `-mfpu` 与 `-mfloat-abi`，再看 `INC` 里的 port 目录，两边必须同档。

### 八、两份优先级：0xFF 与 0x50

`FreeRTOSConfig.h:61-62` 有两行：

```c
#define configKERNEL_INTERRUPT_PRIORITY         255  /* 不再被 ARM_CM4F port 读取 */
#define configMAX_SYSCALL_INTERRUPT_PRIORITY    (5 << (8 - configPRIO_BITS))  /* 0x50 */
```

第一行是死宏（第二节）；真正参与中断屏蔽的是第二行。`configPRIO_BITS = 4`，`5 << (8 - 4) = 0x50`。三个表示要分清：

| 写法 | 数值 | 说明 |
| --- | --- | --- |
| 逻辑优先级 | 5 | 0 最急，15 最缓 |
| IP/SHPR 原始值 | `0x50` | 高 4 位有效，5 左移 4 位 |
| 十进制打印 | 80 | 只是 `0x50` 的十进制，不是逻辑 80 |

正确的大小关系是 `0x50 < 0xFF`：syscall 阈值数值更小、urgency 更高。能调 `...FromISR()` 的中断，逻辑优先级必须 ≥ 5（原始值 ≥ `0x50`）；逻辑 0–4 比阈值更急，`BASEPRI = 0x50` 盖不住它们，不许调 FreeRTOS API。`R15:46` 与 `CFG:61-62` 是这条账的锚点。

F8 在这一节有三处说法互相打架，全部不能照抄：

| 来源位置 | 原文说法 | 问题 | 本章写法 |
| --- | --- | --- | --- |
| F8:160,296 | 优先级数值 ≥ 80 才允许调 FromISR | 把 8 位原始值 80 当逻辑优先级 | 逻辑阈值 5，原始阈值 `0x50` |
| F8:164 | 配成比内核「高」（数值更小）是错的 | 与正确关系相反 | `0x50 < 0xFF` 才是对的 |
| F8:274 | 数值大于才对，却给出 `0x50 < 255` | 一句话内自相矛盾 | 以 `0x50 < 0xFF` 为准 |

三处禁抄的理由不是措辞，而是比较对象不同：逻辑值跟逻辑值比，原始值跟原始值比；把 `0x50` 的十进制 80 当逻辑值，就会写出无法配置的阈值。

### 九、堆尽返回值与奇数优先级断言

`xTaskCreate` 在堆池不够时返回 `errCOULD_NOT_ALLOCATE_REQUIRED_MEMORY`，这是一个负值；`pdPASS` 是 1，`pdFAIL` 是 0。F8:214 写「返回失败（`pdFAIL`）」是来源说法有误，已按 V11.1.0 `tasks.c` 更正。判断要写 `!= pdPASS`，不要写 `== pdFAIL`：

```c
if( xTaskCreate( task, "name", 256, NULL, 2, NULL ) != pdPASS )
{
    /* 失败：errCOULD_NOT_ALLOCATE_REQUIRED_MEMORY（负值），不是 0 */
}
```

写成 `== pdFAIL` 的代码永远不进失败分支，因为 −1 不等于 0；随后任务没建出来，程序却以为成功，现象是「高优先级任务一直不跑」。

`port.c:405-415` 的优先级断言也要分清分支：`configASSERT( ucMaxSysCallPriority )` 与「阈值不能超出实现的优先级位宽」这两条在 F407 上会执行；「阈值必须为偶数」的那条只在 `ulImplementedPrioBits == 8` 的分支里执行。F407 只实现 4 个优先级位（`configPRIO_BITS = 4`，`CFG:18`），不走 8 位分支。F2:89,305 把三条并列成「F407 通用三连断言」，是来源说法有误，已按 `port.c:405-415` 更正；不要写成 F407 开机一定查奇数。

### 十、HardFault 不属于 port：任务 return 才有 `prvTaskExitError`

ARM_CM4F 的 port **不实现** `HardFault_Handler`。启动文件 `startup_stm32f407xx.s:100` 的向量槽指向 `HardFault_Handler`，而 `:208` 把它做成 weak 别名，默认落到 `Default_Handler` 的死循环；应用不写自己的强符号，HardFault 就停在默认死循环里，没有任何打印。

FreeRTOS 只提供任务函数 `return` 的陷阱：`portTASK_RETURN_ADDRESS` 在 `port.c:125` 指向 `prvTaskExitError`（`port.c:234`），任务函数真返回了就触发 `configASSERT`、关中断、死循环。这是「任务不许 return」的物理来源，不是 HardFault 处理器。R7:145 说「F8 那套 HardFault 是 FreeRTOS 自带（V11 默认关，靠 configASSERT）」是来源说法有误，已按启动文件与 `port.c` 更正：FreeRTOS 不自带 HardFault，要取证就自己写 `HardFault_Handler`，方法在第 19 章。

| 符号 | 谁提供 | 作用 |
| --- | --- | --- |
| `HardFault_Handler` | 启动文件 weak → `Default_Handler` | 默认死循环；应用写强符号顶替 |
| `prvTaskExitError` | `port.c:234` | 任务 `return` 的陷阱，不是 HardFault |

### 十一、RT-Thread Nano 对照：四件套与三处符号更正

RT-Thread Nano 手动移植是四件套：内核源码（`src/` + `libcpu/arm/cortex-m4`）、`rtconfig.h`（裁剪配置）、`board.c`（`rt_hw_board_init`：时钟/SysTick/堆）、异常接管。四件套的分法见 R7:14,59-68,75；lab 的落点如下：

| 件 | 内容 | lab 落点 |
| --- | --- | --- |
| 内核源码 | `src/` + `libcpu/arm/cortex-m4` | `Makefile:60-70,126-128` |
| `rtconfig.h` | 裁剪配置；`RT_THREAD_PRIORITY_MAX=32`、`RT_TICK_PER_SECOND=1000` | `rtconfig.h:16-18` |
| `board.c` | `rt_hw_board_init`、`SysTick_Handler`、控制台与堆 | `board.c:61-95` |
| 异常接管 | `PendSV_Handler`/`HardFault_Handler` + `SysTick_Handler` | `context_gcc.S` + `board.c:73-78` |

三处符号必须按 lab 源码写，不能照 R7 的旧表：

- 切换文件是 **`context_gcc.S`**，不是 `context_rvds.S`；Makefile 编的是 `context_gcc.o`（`Makefile:75,128`）。`context_rvds.S` 是 ARMCC 版本，GCC 工程不会编它。
- 切换与故障符号是 **`PendSV_Handler`**、**`HardFault_Handler`**（在 `context_gcc.S` 里）；`SysTick_Handler` 在 `board.c:73-78`。R7:125-127 表里的 `rt_hw_pendsv`、`rt_hw_systick`、`rt_hw_hard_fault` 在本工程源码里不存在，是虚构符号，来源说法有误，已按 libcpu 与 board.c 更正。
- 堆边界符号是 **`&__bss_end__` → `&_estack`**（`board.c:38-40,94`），不是 `HEAP_BEGIN`/`HEAP_END`。R7:103,115,200 的 `HEAP_BEGIN/HEAP_END` 是示意名，lab 的 `rt_system_heap_init((void *)&__bss_end__, (void *)&_estack)` 才是实际参数。

RT-Thread 不用 SVC 启动第一个线程：`rt_thread_startup` 只把线程挂进就绪表；`rt_system_scheduler_start` 选出最高优先级线程，调 `rt_hw_context_switch_to`，后者把 `from` 记为 0、置 PendSV 挂起位，开中断后 PendSV 自然进来恢复目标线程现场（`R7:103-147`；`context_gcc.S`）。FreeRTOS 靠 SVC 异常跳进第一个任务，RT-Thread 靠 PendSV 自然滑进去，这是两个内核启动模型的差别。

lab 的板级事实也要按 `board.c` 写：HSI 16 MHz，不走 PLL（`board.c:5`）；SysTick 直接写 `LOAD = 16000000 / 1000 - 1 = 15999`、`VAL = 0`、`CTRL = 0x7`（`board.c:90-92`）。R7:163,220 的 25 MHz 是标准版母本 BSP 的晶振，不是本 lab 的时钟；把 25 MHz 套进来，tick 会差 1.5625 倍。R7:10,59 的「Nano 约 3KB」是来源说法(未复核)，不是固定值：代码体积随编译器、优化档与裁剪变化，本仓库没有量过。

| 维度 | FreeRTOS ARM_CM4F | RT-Thread Nano（lab） |
| --- | --- | --- |
| 切换文件 | `port.c` | `context_gcc.S` |
| 切换符号 | `PendSV_Handler`（`xPortPendSVHandler` 改名） | `PendSV_Handler` |
| 报时 | `SysTick_Handler`（`xPortSysTickHandler` 改名） | `SysTick_Handler`（`board.c`） |
| 启动 | SVC → `vPortSVCHandler` | 不用 SVC；`rt_hw_context_switch_to` 置 PendSV |
| 故障 | 不自带 `HardFault_Handler` | `HardFault_Handler` 在 `context_gcc.S` |
| 堆 | `configTOTAL_HEAP_SIZE` 定长数组 | `&__bss_end__` → `&_estack` |
| tick | `configTICK_RATE_HZ = 1000` | `RT_TICK_PER_SECOND = 1000`，`LOAD = 15999` |

## 测量与证据

本章能复算的只有源码结构与算术；没有一条是本仓库的上板读数。读数按来路分四类：实测记录、来源说法(未复核)、文档推导、未实测。下表逐项标出来路。

### 读数来路表

| 取证项 | 来路 | 读数或结论 | 性质 |
| --- | --- | --- | --- |
| 三异常槽位与改名 | `FreeRTOSConfig.h:75-77`；`startup_stm32f407xx.s:108,111,112`；`port.c:260,505,562` | SVC/PendSV/SysTick 三个向量；`:74` 是注释，F8 的 74-77 多算一行 | 文档推导 |
| SHPR3 写入 | `port.c:65,434-435`；`F2:70-81` | PendSV/SysTick 两个字节都 0xFF；`configKERNEL_INTERRUPT_PRIORITY` 不被读取 | 文档推导 |
| PendSV 挂起位 | `portmacro.h:91,99-100`；`F2:54,61-62` | ICSR `0xE000ED04` bit28；`portYIELD` 只写这一位 | 文档推导 |
| 软硬帧 | `F2:95-101,119,233,242`；`port.c:505-560` | 硬件 8 字 + 软件 9 字；恢复相反；最后 `bx r14` | 文档推导 |
| FPU 帧 | `F2:103-105,116-119,264` | bit4=0 走 26 字扩展帧，软件再存 s16–s31；bit4=1 跳过；懒堆叠先占座后写真 | 文档推导 |
| 两份优先级 | `CFG:61-62`；`port.c:434-435`；`R15:46` | 0xFF 对 0x50；逻辑 15 对 5；`0x50 < 0xFF` | 文档推导 |
| 堆尽返回值 | `F8:206-214`；V11.1.0 `tasks.c` | `errCOULD_NOT_ALLOCATE_REQUIRED_MEMORY` 负值；F8 的 `pdFAIL` 是错的 | 文档推导 |
| 奇数优先级断言 | `port.c:405-415`；`CFG:18`；`F2:89,305` | 只在 `ulImplementedPrioBits == 8` 分支；F407 4 位不走 | 文档推导 |
| HardFault 归属 | `startup_stm32f407xx.s:100,208`；`port.c:125,234`；`R7:145` | port 不实现 HardFault；启动文件 weak；只有任务 return 的 `prvTaskExitError` | 文档推导 |
| RT-Thread 符号与堆边界 | `Makefile:75,128`；`board.c:10-11,38-40,73-78,94` | `context_gcc.S`；`PendSV_Handler`/`HardFault_Handler`；`SysTick_Handler`；`&__bss_end__`→`&_estack` | 文档推导 |
| RT-Thread lab 时钟与 tick | `board.c:5,90-92`；`rtconfig.h:18` | HSI 16 MHz；LOAD 15999；VAL 0；CTRL 0x7 | 文档推导 |
| F2 五步 probe | `F2:153-178,337`；`probe.sh` | 27 条指令 / 104 B / 两条 nop 6 B 的字节账；仓库无反汇编原文 | 来源说法(未复核) |
| F2 GDB 软件帧 | `F2:226-243` | `stepi`、`x/9xw`、`$r0+36 == $psp` 的目击清单；无 GDB 日志 | 未实测 |
| F8 `size`/`nm` | `F8:41,131-136,199,204-206` | 43156/2168/19208 = 64532；三个 `T` 符号地址；无构建产物 | 来源说法(未复核) |
| F8 上板状态表 | `F8:244` | `make flash` 后串口 `vTaskList`；待回填 | 未实测 |
| 本章板级实验 | 未执行 | 待实测 | 未实测 |

`size` 的三段 43156/2168/19208 合计 64532 是构建产物（来源说法(未复核)），不是板上读数；`bss 19208` 也不是 F407 的总 RAM。F407 的 192 KB RAM 由 128 KB SRAM 与 64 KB CCM 组成，19208 B 只是零初始化段，`data 2168` 还要从 Flash 拷进 RAM，MSP 栈另有预算（`F8:41,199,204-206`）。把 `bss` 当「FreeRTOS 占了 19 KB」或当「总 RAM」都会把账算错。

F2 的 NOP=6 字节账同样缺原文：`90 + 6 + 4 + 4 = 104` 里的 6 B 来自两条 nop，`4 B` 是 `pxCurrentTCBConst` 字面量，最后的 `4 B` 是补齐对齐；没有 `objdump` 原文，这条账只能标「来源说法(未复核)」，不能当校验过的字节账（`F2:158-178,337`）。

### 待做台架

| 日期 | 平台/板卡 | 实验 | 原始结果 | 结论 |
| --- | --- | --- | --- | --- |
| 待实测 | F407 lab | GDB 断 `PendSV_Handler`，在无浮点任务上 `stepi 8`，读 `$r0` 的 9 字软件帧与 `$r0+36 == $psp` | | |
| 待实测 | F407 lab | 任务加浮点运算后重跑，确认 `tst r14,#0x10` 走 `eq` 分支，`$r0` 比无 FPU 时低 64 B | | |
| 待实测 | F407 lab | `nm` 三个异常符号与 `size` 三段，和 F8 的 43156/2168/19208 对账 | | |
| 待实测 | F407 lab | 注释 `FreeRTOSConfig.h:75-77` 三行 `#define` 再编译，确认向量仍指向 weak 的 `Default_Handler`，第一次 SVC 死在默认死循环 | | |
| 待实测 | F103 板 | 用 `ARM_CM3` 跑同一套三异常接管；再故意换 `ARM_CM4F`，记录调度器启动时的 HardFault | | |
| 待实测 | F407 lab | 用 `objdump` 保存 PendSV 的反汇编，核对 27 条、90 B 正文与两处 nop 填充 | | |
| 待实测 | F407 lab | RT-Thread Nano：`nm` 查 `PendSV_Handler`/`HardFault_Handler`，`list_thread` 看线程表，核对 LOAD=15999 | | |

这些台架都还没做。没有原始输出之前，本章只给源码结构与算术；表中的空白不是「通过」，是「未测」。

## 失败分支

| 现象 | 原因 | 区分证据 | 下一动作 |
| --- | --- | --- | --- |
| 新任务一跑就停在 `prvTaskExitError` 的断言或死循环 | 任务函数执行了 `return` | 断点 `prvTaskExitError`（`port.c:234`）命中 | 任务函数改成 `for (;;)`，或结尾 `vTaskDelete(NULL)` |
| 改了 TCB 字段顺序后，调度一跑就 HardFault 或栈顶乱 | 在 `pxTopOfStack` 前加了字段，PendSV 仍按偏移 0 写 | 对照 `tasks.c:358,360` 与 `str r0,[r2]` 的偏移 | 恢复 `pxTopOfStack` 为首成员 |
| F407 上浮点值在任务间互相踩 | 选了不带 `F` 的 `ARM_CM4`，切换不保存 s0–s31 | 看 Makefile 的 `-mfpu` 与 `INC` 的 port 目录是否同档 | 换 `ARM_CM4F`，保留 `-mfloat-abi=hard` |
| F103 上调度器一启动就 HardFault | 选了 `ARM_CM4F`，M3 不认 FPU 指令与扩展帧 | 看 port 目录与内核型号；HardFault 落在启动调度器之后 | 换 `ARM_CM3`，去掉 `-mfpu`/`-mfloat-abi` |
| 改了 `configKERNEL_INTERRUPT_PRIORITY` 没有任何效果 | V11.1.0 ARM_CM4F 不读这个宏，SHPR3 由 port 常量写死 | 看 `port.c:65,434-435`；宏在 port 源码里出现 0 次 | 不用改它；要改内核优先级得直接改 SHPR3 并有理由 |
| 在逻辑优先级 0–4 的中断里调 FromISR API，偶发死机 | 这些中断比 `BASEPRI = 0x50` 更急，临界区盖不住 | 看中断优先级配置与 `configMAX_SYSCALL_INTERRUPT_PRIORITY` | 把能调 API 的中断降到逻辑 ≥5，或把 API 移出 ISR |
| `xTaskCreate` 返回负值，代码却当成功 | 判断写成 `== pdFAIL`（0），负值不等于 0 | 打印返回值；看是否 `!= pdPASS` | 改成 `!= pdPASS`，加大 heap 或减小栈 |
| 以为 FreeRTOS 会打印 HardFault 现场 | ARM_CM4F port 不实现 `HardFault_Handler`，启动文件是 weak | 看 `startup_stm32f407xx.s:100,208` 与 `port.c` 符号表 | 自己写 `HardFault_Handler`，按第 19 章取证 |
| 三行 `#define` 注释后编译通过，但系统一启动就死 | 向量仍指向 weak 的 `Default_Handler`，SVC 进默认死循环 | `nm` 看 `SVC_Handler` 是 `T` 还是 `W` | 恢复三行映射，或改启动文件向量名 |
| RT-Thread 用 `HEAP_BEGIN`/`HEAP_END` 编译或链接失败 | lab 的堆边界是 `&__bss_end__` 与 `&_estack` | 看 `board.c:38-40,94` | 改用链接脚本符号 |
| RT-Thread 线程切换不执行 | 拿 `context_rvds.S` 给 GCC 工程，或符号名写成 `rt_hw_pendsv` | 看 Makefile 是否编 `context_gcc.o`；`nm` 查 `PendSV_Handler` | 用 `context_gcc.S` 与 `PendSV_Handler` |
| RT-Thread tick 快 1.5625 倍或慢 | 把标准版 BSP 的 25 MHz 晶振套到 lab 的 HSI 16 MHz | 看 `board.c:5,90-92` 的 LOAD 算术 | 按 16000000 重算 LOAD |

## 跨平台边界

F103 与 F407 的三异常接管是同一套机制：SVC 启动第一个任务、PendSV 切换、SysTick 报时，向量名与 `#define` 映射的形状相同。差别在 port：F103 是 Cortex-M3，用 `ARM_CM3`，没有 FPU，异常帧永远只有 8 字核心帧，软件帧仍是 9 字，没有 s16–s31 的 16 字行李；F407 是 Cortex-M4F，用 `ARM_CM4F`，硬浮点 ABI，任务跑过浮点后切换要保存 26 字硬件扩展帧与 25 字软件帧。

| 维度 | F103 | F407 |
| --- | --- | --- |
| 内核 | Cortex-M3 | Cortex-M4F |
| FPU | 无 | 单精度 |
| port | `ARM_CM3` | `ARM_CM4F` |
| 编译 | `-mcpu=cortex-m3 -mthumb` | `-mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard` |
| 异常接管 | SVC/PendSV/SysTick 同机制 | SVC/PendSV/SysTick 同机制 |
| 现场 | 8 字硬件 + 9 字软件，无 FPU 行李 | 8 或 26 字硬件 + 9 或 25 字软件 |
| 选错 port | 用 `ARM_CM4F`：调度器启动进 HardFault | 用 `ARM_CM4`：切换丢浮点寄存器 |

![F103/Cortex-M3 的 PSP 与 MSP：任务栈用 PSP，异常用 MSP；硬件压 8 个寄存器 = 32 B，M3 无浮点扩展帧（原理示意，非实拍）](/images/ch15-psp-msp.png)

图是根书 F103/M3 的原理示意：任务 A 的 PSP 指向自己的栈，IRQ 入场时硬件在 A 的栈里压 R0–R3、R12、LR、PC、xPSR 共 8 字 = 32 B；进入 ISR 后用 MSP，PendSV 若接着切换，再保存 R4–R11 并把 PSP 存进 TCB。M3 没有 FPU 扩展帧，图下的「8 个寄存器 = 32 B」只适用于这一档；F407 跑过浮点后要按 26 字扩展帧算。图没有按地址或容量比例画，是原理示意，不是实拍。

根书 F103 例程用的是 `ARM_CM3` 与 V11.3.2，栈深是 128/192/256 字，与 F407 lab 的 256/256/320 字、V11.1.0 行号不互通。本章的 F103 结论只到「同机制、无 FPU 行李、port 换 `ARM_CM3`」这一层，不把 F407 的行号套过去。

## 离开检查

1. 三个异常各由哪个函数接管？源码名、向量名与三行 `#define` 分别是什么？
2. `FreeRTOSConfig.h:74-77` 与 `75-77` 差在哪？F8 为什么多算一行？
3. PendSV 与 SysTick 的优先级各是多少？`configKERNEL_INTERRUPT_PRIORITY` 还读吗？
4. F2:79 说「SysTick 优先级高」，为什么不能照抄？
5. PendSV 的挂起位在哪个寄存器、哪一位？`portYIELD` 做了什么？
6. 硬件帧 8 字是哪几个？软件帧 9 字为什么多一个 EXC_RETURN？
7. FPU 行李凭什么判断？s0–s15、s16–s31 分别由谁保存？懒堆叠是什么？
8. PendSV 的十一条语义步骤是什么？`vTaskSwitchContext` 改了哪个变量？
9. 无 FPU 的运行现场与首帧各多少字？有 FPU 的运行现场多少字？
10. F407 与 F103 各用哪个 port？选错会怎样？
11. `0x50` 与 `0xFF` 谁更急？FromISR 的逻辑阈值是多少？F8 哪三处不能抄？
12. `xTaskCreate` 堆尽返回什么？为什么不能写 `== pdFAIL`？
13. 奇数优先级断言为什么在 F407 不执行？F2:89,305 错在哪？
14. `HardFault_Handler` 谁负责？`prvTaskExitError` 是干什么的？
15. RT-Thread Nano 的四件套是什么？切换文件、切换符号、SysTick 符号、堆边界符号各是什么？
16. RT-Thread lab 的时钟与 SysTick LOAD 是多少？「Nano 约 3KB」是什么性质的说法？
17. `size` 三段 43156/2168/19208 说明什么？`bss 19208` 是总 RAM 吗？
18. 本章哪些读数是「来源说法(未复核)」或「未实测」？为什么不能写成板上实测？

<details>
<summary>对照答案</summary>

1. SVC 由 `vPortSVCHandler`（`port.c:260`）接管，向量名 `SVC_Handler`（`startup_stm32f407xx.s:108`）；PendSV 由 `xPortPendSVHandler`（`:505`）接管，向量名 `PendSV_Handler`（`:111`）；SysTick 由 `xPortSysTickHandler`（`:562`）接管，向量名 `SysTick_Handler`（`:112`）。三行 `#define` 在 `FreeRTOSConfig.h:75-77`。
2. `:74` 是「端口映射」注释，`:75-77` 才是三行 `#define`；F8:116,268 写 74-77，多算了注释行。改配置时只改 75-77。
3. 两个都写 0xFF（逻辑 15，最低）。V11.1.0 ARM_CM4F 的 port 用 `portMIN_INTERRUPT_PRIORITY = 255UL` 直接写 SHPR3（`port.c:65,434-435`），不再读 `configKERNEL_INTERRUPT_PRIORITY`；配置里那行留着无害，改它不影响行为。
4. 因为同页 F2:77 已经说 PendSV 与 SysTick 两个槽都填 0xFF；按 `port.c:434-435`，SysTick 也是最低，不比 PendSV 高。F2:79 与同页自相矛盾，来源说法有误。
5. ICSR = `0xE000ED04`，bit28 是 `PENDSVSET`（`portmacro.h:99-100`）。`portYIELD`（任务里）或 `portYIELD_FROM_ISR(x)`（中断里）写这一位，PendSV 在当前异常返回后按最低优先级排队执行。
6. 硬件帧 8 字：R0–R3、R12、LR、PC、xPSR。软件帧 9 字：R4–R11 + EXC_RETURN；EXC_RETURN 让恢复时的 `bx r14` 知道用哪个栈、有没有 FPU 帧，所以必须和 R4–R11 一起存。
7. 看 EXC_RETURN bit4：bit4=0 表示硬件扩展帧带 s0–s15 与 FPSCR，软件再存 s16–s31；bit4=1 表示没有 FPU 行李，两条条件指令跳过。s0–s15 是调用者保存，硬件压；s16–s31 是被调者保存，软件补。懒堆叠是硬件先给 FPU 帧预留空间、真用到浮点才写数（先占座、后写真）。
8. ① 读 PSP；② 取当前 TCB；③ 条件存 s16–s31；④ 存 9 字软件帧；⑤ 写回栈顶；⑥ 进 BASEPRI 临界区；⑦ `vTaskSwitchContext`；⑧ 恢复 BASEPRI；⑨ 取新 TCB 与栈顶；⑩ 弹 9 字并按需弹 FPU；⑪ 写 PSP、`bx r14`。`vTaskSwitchContext` 换的是 `pxCurrentTCB`（`tasks.c:5056`），不搬寄存器。
9. 无 FPU 运行现场 8 + 9 = 17 字 = 68 B；新任务首帧多 1 个对齐字，18 字 = 72 B。有 FPU 的运行现场 26 字硬件 + 25 字软件 = 51 字 = 204 B。
10. F407 用 `ARM_CM4F`，F103 用 `ARM_CM3`。F407 拿 `ARM_CM4` 会丢浮点寄存器；F103 拿 `ARM_CM4F` 编译过、调度器启动进 HardFault。
11. `0x50` 更急，逻辑 5 对逻辑 15；`0x50 < 0xFF`。能调 `...FromISR()` 的逻辑阈值是 5（原始值 `0x50`）。F8:160,296 的「≥80」、F8:164 的「更小是错的」、F8:274 的「大于才对却给 0x50<255」三处互相打架，全部不能照抄。
12. 返回 `errCOULD_NOT_ALLOCATE_REQUIRED_MEMORY`（负值）。`pdFAIL` 是 0，负值不等于 0，写 `== pdFAIL` 永远不进失败分支；要写 `!= pdPASS`。
13. 奇数检查在 `port.c:405-415` 里只处于 `ulImplementedPrioBits == 8` 的分支；F407 只实现 4 个优先级位（`configPRIO_BITS = 4`），不走该分支。F2:89,305 把三条断言并列成 F407 通用三连，来源说法有误；阈值非 0 与不超出位宽这两条仍会执行。
14. `HardFault_Handler` 归应用：ARM_CM4F port 不实现它，启动文件 `:100` 的槽位在 `:208` 是 weak 别名，默认落到 `Default_Handler` 死循环。FreeRTOS 只提供任务 `return` 的 `prvTaskExitError`（`port.c:234`），那不是 HardFault 处理器。
15. 四件套：内核源码（`src/` + `libcpu/arm/cortex-m4`）、`rtconfig.h`、`board.c`、异常接管。切换文件是 `context_gcc.S`（不是 `context_rvds.S`）；切换符号是 `PendSV_Handler`、`HardFault_Handler`；SysTick 符号是 `board.c` 里的 `SysTick_Handler`；堆边界是 `&__bss_end__` → `&_estack`（不是 `HEAP_BEGIN`/`HEAP_END`）。
16. HSI 16 MHz（`board.c:5`）；`LOAD = 16000000 / 1000 - 1 = 15999`，`VAL = 0`，`CTRL = 0x7`（`board.c:90-92`）。「Nano 约 3KB」是来源说法(未复核)，不是固定值；25 MHz 是标准版母本 BSP 的晶振，不是本 lab。
17. 43156/2168/19208 合计 64532 是构建产物的三段（来源说法(未复核)），不是板上读数；`bss 19208` 只是零初始化段，不是 F407 的总 RAM。F407 的 192 KB = 128 KB SRAM + 64 KB CCM，`data 2168` 还要占 RAM，MSP 栈另有预算。
18. F2 五步 probe 与 F8 的 `size`/`nm` 是「来源说法(未复核)」；F2 GDB 软件帧与 F8 上板状态表是「未实测」；本章没有新的板级实验。仓库里没有这些实验的原始日志或产物，不能写成 F407 板上实测。

</details>

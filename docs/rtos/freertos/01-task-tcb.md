---
title: F1 任务与 TCB：xTaskCreate 逐行走查
status: done
difficulty: 3
minutes: 30
---

# F1 任务与 TCB：xTaskCreate 逐行走查

> 🎯 创建任务像"克隆一个你"去平行世界：克隆体醒来时要以为自己一直在那儿干活，所以 FreeRTOS 把它的栈**伪装成"刚被中断打断"的样子**。看懂这个伪装，就懂了任务的一半。

## 本章精髓

1. **TCB（tskTCB）是任务户口本**：栈顶指针 `pxTopOfStack` 永远排第一（上下文切换直接按 TCB 地址取栈）、栈底 `pxStack`、优先级、状态列表项、任务名，`tasks.c` 里逐字段看得完（V11.1.0 `tasks.c:358`）。
2. **栈初始化是一场"化妆"**：`pxPortInitialiseStack`（`portable/GCC/ARM_CM4F/port.c:202`）按异常帧格式把 xPSR/PC(=任务函数)/LR/参数 r0 摆进新栈：第一次切换时，弹栈弹出来的就是"任务开始跑"。初始 xPSR = `0x01000000`（`port.c:92` 的 `portINITIAL_XPSR`，Thumb 位）。
3. **就绪列表按优先级分数组**：`pxReadyTasksLists[prio]` 是链表数组，创建任务 = 挂进对应优先级的链表尾巴（[F3 调度器](03-scheduler.md)的货架）。

- **能理解**：为什么 `pxTopOfStack` 必须排第一；为什么任务函数不许 return；为什么 INCLUDE_* 宏会让老工程升级后链接失败。
- **能用**：对照源码讲出 xTaskCreate 的六步；用 GDB 指认新任务栈里的 xPSR/PC/r0。

## 先修

- [F0 为什么需要 RTOS](00-why-rtos.md)、[C6 栈帧](../../c/06-abi-stack.md)、[B4 启动](../../build/04-startup.md)。

## 先跑起来（10 分钟 quick win）

`code/rtos/01-freertos-lab` 场景 1（默认）：

```bash
make
make flash
```

串口 115200 看日志：`high` 每 100ms 一行、`low` 每 300ms 一行：**先建低优先级、再建高优先级，high 一建好就抢占**，抢占式调度直接上演。每 2 秒还会打一张 `vTaskList` 任务状态表（R/B 状态列 + 剩余栈高水位）。

烧录前先押个头一行：low 先创建、high 后创建，串口打出的第一行日志，落款是谁？押完再看 115200 的输出。

## 动画：新任务的第一口栈

栈顶压入的不是"参数"，是一套**完整的异常现场**：xPSR、PC（指向任务函数）、LR、r12、r3~r0（r0 是任务参数），然后 SP 退到最低。第一次 PendSV 弹栈时，弹出来的就是"任务函数开始跑"。

![任务创建与栈初始化动画](/anim/task-create-stack.svg)

## 版本与配置前提

- 内核：上游 **FreeRTOS-Kernel V11.1.0**，ARM_CM4F 单核端口（`portable/GCC/ARM_CM4F/port.c`）。
- 配置：本工程 `FreeRTOSConfig.h`，`configTICK_RATE_HZ=1000`、`configMAX_PRIORITIES=5`、`configMINIMAL_STACK_SIZE=128`（单位是**字**）。
- 与 ESP-IDF 内置的 V10.5.1 SMP 修改版不同源，行号与结论不混读。

## 小节结构

| 小节 | 内容 | 四件套 |
|---|---|---|
| 一、TCB 逐字段 | pxTopOfStack 必须第一的汇编级原因 | 库解析 |
| 二、栈的化妆术 | pxPortInitialiseStack 逐行；初始 xPSR 为什么是 0x01000000 | 库解析 |
| 三、创建六步 | xTaskCreate 源码走查 | 库解析 |
| 四、就绪货架 | 链表数组结构；同级任务的轮转 | 配置 |
| 五、RAM 账单 | 栈怎么估（调用深度×帧+余量）；水位标记实测 | 代码分析 |
| 六、代码分析 | `01-freertos-lab` 场景 1 的日志对照 | 代码分析 |

## 一、TCB 逐字段：户口本的第一行

`tskTaskControlBlock`（V11.1.0 `tasks.c:358`）开头几个字段：

```c
typedef struct tskTaskControlBlock
{
    volatile StackType_t * pxTopOfStack;   /* 当前栈顶：切换时的存取锚点 */
    ListItem_t xStateListItem;             /* 挂在哪个状态链表上 */
    ListItem_t xEventListItem;             /* 等哪个事件（队列/信号量/…） */
    UBaseType_t uxPriority;                /* 数值越大优先级越高 */
    StackType_t * pxStack;                 /* 栈底（溢出检查用） */
    char pcTaskName[ configMAX_TASK_NAME_LEN ];
    ...
} tskTCB;
```

`pxTopOfStack` 排第一不是排版习惯，是**汇编级的硬约定**：上下文切换的 PendSV 处理器拿到 TCB 地址后，第一个字就是"当前栈顶"，不用知道结构体其余部分的布局就能完成存取。这个顺序写死了，改不得。

## 二、栈的化妆术：`pxPortInitialiseStack`

`port.c:202` 的 `pxPortInitialiseStack()` 把一个新栈伪装成"刚被中断打断"的现场：

```c
*pxTopOfStack = portINITIAL_XPSR;        /* 0x01000000：Thumb 位，必须是 1 */
pxTopOfStack--;
*pxTopOfStack = ( StackType_t ) pxCode;  /* PC：任务函数入口 */
pxTopOfStack--;
*pxTopOfStack = ( StackType_t ) prvTaskExitError; /* LR：任务不许 return，
                                                     返回就掉这里 */
pxTopOfStack -= 5;                        /* r12, r3, r2, r1 留白 */
*pxTopOfStack = ( StackType_t ) pvParameters;     /* r0：任务参数 */
pxTopOfStack -= 8;                        /* r11~r4 留白 */
```

解读三个关键选择：

1. **xPSR = 0x01000000**：Thumb 位（bit24）。Cortex-M 只支持 Thumb 指令集，弹栈恢复时若这一位是 0 直接 UsageFault，所以初始值必须硬编码成 0x01000000。
2. **PC = 任务函数**：弹栈完成后，处理器"接着执行"的就是任务函数：任务就这样出生了。
3. **LR = `prvTaskExitError`**：任务函数的"返回地址"指向一个死循环断言。**任务不许 return**：这是这条规则的物理来源。

## 三、创建六步：`xTaskCreate`

`tasks.c:1718`（V11.1.0）的 `xTaskCreate` 干六件事：

1. **分栈**：`pvPortMalloc( uxStackDepth × sizeof(StackType_t) )`，注意单位是**字**（`StackType_t` = `uint32_t`，`portmacro.h:55`），传 128 就是 512 字节，不是 128 字节；
2. **分 TCB**：`pvPortMalloc( sizeof(TCB_t) )`；
3. **初始化栈**：`prvInitialiseNewTask` → `pxPortInitialiseStack`（上节那场化妆）；
4. **初始化 TCB**：名字、优先级、列表项、栈底；
5. **挂就绪表**：`prvAddTaskToReadyList` 挂进 `pxReadyTasksLists[prio]` 的尾巴；
6. **触发调度**：新任务优先级高于当前任务就 `taskYIELD`："先建低优先级、再建高优先级，high 一建好就抢占"就是这一步。

## 四、就绪货架：链表数组

就绪列表不是一条大链表，是**按优先级分格的链表数组** `pxReadyTasksLists[0..configMAX_PRIORITIES-1]`：

- 同优先级的任务在同一格里轮转（时间片，`configUSE_TIME_SLICING=1`）；
- 调度器从高往低扫，第一个非空格的链表头就是下一个跑的，**O(1) 找到最高优先级就绪任务**，与任务总数无关。

## 五、RAM 账单：栈怎么估

每个任务的 RAM 账单 = TCB（几十字节）+ 栈（`uxStackDepth` 字）。栈怎么估：

- **下限**：调用链最深处的帧深 × 每层帧大小 + 中断嵌套余量；
- **实测**：FreeRTOS 建任务时把栈填 0xA5 水位线，运行后 `uxTaskGetStackHighWaterMark()` 读"历史最低剩余"，用真实水位把栈预算从玄学变工程；
- **护栏**：`configCHECK_FOR_STACK_OVERFLOW=2` 开满，溢出会触发 `vApplicationStackOverflowHook`（本工程打印任务名后停住）。

## 六、代码分析：`01-freertos-lab` 场景 1

`scene_start()` 里三个任务：`low`(prio 1)、`high`(prio 2)、`rpt`(prio 1)。日志里能看到：

- `high` 的 tick 间隔稳定 100ms，`low` 稳定 300ms：优先级决定的是"谁先跑"，不是"谁跑得快"；
- `vTaskList` 表里的 `R`（运行）/`B`（阻塞）状态列与剩余栈高水位；
- 把 `high` 的 delay 改成忙等，`low` 就再也跑不到，这是**抢占式 + 无时间片让出**的直接证据。

## 七、任务状态机：五个状态与两条路

任务在五个状态间流转：**就绪（Ready）→ 运行（Running）→ 阻塞（Blocked）→ 挂起（Suspended）→ 删除（Deleted）**。

```
         xTaskCreate
             ↓
[Ready] ←→ [Running] → vTaskDelay/xQueueReceive → [Blocked]
   ↑           ↓                                      ↓
   └───────────┘ ← 调度器切换                     xEventGroupSetBits/
                                                    xQueueSend 到期
                                                         ↓
                                                    [Ready]
```

两条创建路径：

| 路径 | API | 栈/TCB 来源 | 适合 |
|---|---|---|---|
| 动态 | `xTaskCreate` | `pvPortMalloc`（[F7](07-heap.md)） | 运行时决定任务数、栈深 |
| 静态 | `xTaskCreateStatic` | 调用者提供 `StaticTask_t` + 栈数组 | 安全关键、禁止动态分配 |

静态创建的 TCB 和栈在编译期确定位置，**不会分配失败**：医疗/汽车产品常用。代价是每个任务的 `StaticTask_t` 和栈数组要显式声明，代码量更大。

## 八、GDB 实战：指认新任务的第一口栈

![FreeRTOS GDB 调试实战](/anim/freertos-gdb-debug.svg)

```bash
arm-none-eabi-gdb build/firmware.elf
(gdb) break vTaskStartScheduler
(gdb) continue
(gdb) p pxCurrentTCB->pxTopOfStack
$1 = (StackType_t *) 0x20001a80
(gdb) x/16xw $1
  0x20001a80: 0x01000000  ← xPSR (Thumb 位)
  0x20001a84: 0x08000189  ← PC (任务入口)
  0x20001a88: 0x080002a1  ← LR (prvTaskExitError)
  0x20001a8c: 0x00000000
  0x20001a90: 0x00000000  ← r0 (任务参数)
```

对照 `port.c:202` 的 `pxPortInitialiseStack`：**每行代码都能在栈里找到对应的字**。这就是"化妆术"的物理证据。

## 附录：工程完整源码

<<< ../../../code/rtos/01-freertos-lab/main.c

## 记忆锚点

::: tip 一句话记住
**TCB 是户口本，栈顶指针写第一行；新栈化个"中断妆"，一弹栈任务就出生；栈深按字不按字节，INCLUDE 宏默认全关。**
:::

**延伸**：任务栈与内存模型（[C1](../../c/01-memory-model.md)）直接相关；TCB 结构体与 ABI 对齐（[C4](../../c/04-struct-abi.md)）影响布局；GDB 查看 TCB 实战见 [B6](../../build/06-flash-debug.md)。

## 实物实验

- 场景 1 日志对照：`high`/`low` 的 tick 间隔与 `vTaskList` 表；
- GDB 现场：`p pxCurrentTCB`、`x/16xw pxCurrentTCB->pxTopOfStack`，指认 xPSR(0x01000000)/PC/r0；
- 翻车实验（选做）：把某个任务的栈深从 256 改到 64，看 `vApplicationStackOverflowHook` 抓到谁。

## 常见坑

- **栈给太小**：不报错，悄悄踩到隔壁任务/堆，症状是"莫名其妙 HardFault"（[S16](../../stm32/16-debug-hardfault.md) 取证）；
- **任务函数返回**：返回地址指向 `prvTaskExitError` 死循环断言：结尾必须 `vTaskDelete(NULL)` 或永远不返回；
- **优先级乱排**：数值越大优先级越高（与 NVIC 中断优先级"数值越小越高"相反！），两套规则混用是经典翻车；
- **INCLUDE_* 默认关**：V11 内核默认 `INCLUDE_vTaskDelay=0` 等，老工程升级后链接报 `undefined reference to vTaskDelay`，不是代码坏了，是宏没开；
- **栈深单位是字**：传 128 是 512 字节，不是 128 字节，`configMINIMAL_STACK_SIZE` 同理。

## 短自测

1. 为什么 `pxTopOfStack` 必须是 TCB 的第一个字段？
<details><summary>参考答案</summary>上下文切换的 PendSV 处理器拿到 TCB 地址后，第一个字就是"当前栈顶"，不用知道结构体其余布局就能完成存取。这个顺序是汇编级的硬约定。</details>

2. 新任务的初始栈里 xPSR 为什么是 0x01000000？
<details><summary>参考答案</summary>那是 Thumb 位（bit24）。Cortex-M 只支持 Thumb 指令集，异常返回弹栈时若这一位是 0 就 UsageFault，所以 `portINITIAL_XPSR` 硬编码为 0x01000000（port.c:92）。</details>

3. 任务函数的"返回地址"指向哪里？为什么任务不许 return？
<details><summary>参考答案</summary>指向 `prvTaskExitError`，一个死循环断言。任务函数 return 就会掉进去；正确写法是 `vTaskDelete(NULL)` 或永远循环。</details>

4. `xTaskCreate` 的栈深参数单位是什么？传 128 实际占多少字节？
<details><summary>参考答案</summary>单位是 `StackType_t`（字），ARM_CM4F 上是 `uint32_t`（portmacro.h:55）。传 128 = 512 字节，不是 128 字节。</details>

## 对照表：本章概念 → 仓库与上游落点

| 概念 | 落点 |
|---|---|
| TCB 结构体 | 上游 V11.1.0 `tasks.c:358`（tskTaskControlBlock） |
| 栈初始化化妆术 | 上游 V11.1.0 `portable/GCC/ARM_CM4F/port.c:202`（pxPortInitialiseStack）、`port.c:92`（portINITIAL_XPSR） |
| 创建六步 | 上游 V11.1.0 `tasks.c:1718`（xTaskCreate）→ `tasks.c:1793`（prvInitialiseNewTask） |
| 就绪链表数组 | 上游 V11.1.0 `tasks.c`（pxReadyTasksLists） |
| 场景实验 | [code/rtos/01-freertos-lab](https://github.com/zhuguang-ZFG/mcu/tree/main/code/rtos/01-freertos-lab) 场景 1 |
| 动画 | [task-create-stack.svg](/anim/task-create-stack.svg) |

## 你做到了

- 任务的"出生"在你眼里是透明的六步；
- 栈与 TCB 不再抽象：你会算、会看、会量；
- V11 内核的 INCLUDE_* 门控陷阱，你以后不会再踩。

头一行判给了 high：出生顺序说了不算，优先级说了算。low 先出生，也只是在就绪链表里排了个队；读内核先看结构再排队形，比背 API 口诀可靠。

<div class="achievement">
✅ 下一站：<a href="02-context-switch.html">F2 上下文切换</a>：PendSV 逐汇编指令，换魂术全公开（动画）。
</div>

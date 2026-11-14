---
title: "任务、TCB 与调度"
platforms: [f407]
---

# 任务、TCB 与调度

一个任务从 `xTaskCreate` 返回到第一次拿到 CPU，中间没有一行代码是它自己执行的。内核替它分好栈、填好 TCB，在栈里伪造一套「刚被中断打断」的现场，再把 TCB 挂进就绪表；调度器只在这张表和 tick 之间做选择。本章拆开这三件事：TCB 的第一字段、首帧的 18 个字、以及「谁下一个跑」的两套选法。

证据先说清：F1 的 GDB 首帧、F3 的七步 probe、F1 的串口日志、R1 的 `list_thread` 都没有在本仓库留下可复核的日志或产物，正文按「来源说法(未复核)」或「未实测」标注；首帧 18 字 = 72 B、栈深 128 字 = 512 B、`List_t` 20 B 是由源码与算术得到的「文档推导」。本章没有新的上板读数，待做台架留在「测量与证据」末尾。

> 版本口径：本章全部 FreeRTOS 行号与宏语义按 V11.1.0（`01-freertos-lab` 所用内核与 ARM_CM4F 端口）对账；根书第 15 章引 V11.3.2，两版行号不混排。

## 本章罗盘

- **问题**：新任务第一次上 CPU 时，栈里凭什么已经有一套「被中断过」的现场？`pxTopOfStack` 为什么必须是 TCB 的第一个字段，在前面加一个字段会坏在哪条指令上？`xTaskCreate` 到底做了几步，第六步是不是「立即切换」？栈深 128 是字节还是字？同优先级任务凭什么轮转？`configMAX_PRIORITIES ≤ 32` 到底约束谁？tick 凭什么每拍只看一眼延时表队首？`vTaskDelay` 为什么不是「等」？RT-Thread 的 `rt_thread` 与 FreeRTOS 的 TCB 怎么对应，选最高优先级的方向为什么相反？
- **交付**：能在纸上画出 TCB 前几个字段与首帧 18 字布局，算出 72 B；能逐条讲出 `xTaskCreate` 六步与第六步的条件；能在位图上手算 `31 − CLZ` 与标量扫描；能解释 `vTaskDelay(1)` 的 (0,1] tick；能把 RT-Thread 的 `rt_thread`、32 级单组位图与 `__rt_ffs` 方向讲对。
- **边界**：单平台 F407（Cortex-M4F，`ARM_CM4F` 端口，lab 跑 HSI 16 MHz）。全部 FreeRTOS 行号与宏语义按 V11.1.0；根书 F103 例程的 128/192/256 字栈、10240 B heap 与 F407 lab 的 256/256/320 字、16 KiB heap 不可互换。PendSV 的软硬栈帧与移植留给第 23 章；队列、信号量与通知留给第 24 章。RT-Thread 部分按 lab 的 `RT_THREAD_PRIORITY_MAX = 32` 写，不把 256 级当本工程事实。
- **依据锚点**：F1《任务与 TCB》（`mcu/docs/rtos/freertos/01-task-tcb.md`）、F3《调度器》（`mcu/docs/rtos/freertos/03-scheduler.md`）、R1《线程与调度》（`mcu/docs/rtos/rtthread/01-thread-sched.md`）；首帧形状与 TCB 偏移见 F2（`mcu/docs/rtos/freertos/02-context-switch.md`）。lab 配置见 `mcu/code/rtos/01-freertos-lab/FreeRTOSConfig.h` 与 `mcu/code/rtos/02-rt-thread-lab/rtconfig.h`，板级报时见 `mcu/code/rtos/02-rt-thread-lab/board/board.c`。优先级方向与延时语义在 [第 21 章](./21-why-rtos.md) 已建立；SysTick 的 LOAD 算术见 [v1 第 11 章](../v1-drivers/11-systick-timebase-rtc.md)，本章不重列寄存器。

## 先做出来

不接板，先在纸上把三个任务和两套选位算一遍。数字都对上，再上板看现象。

1. **栈账**：`xTaskCreate` 的第四个参数是栈深，单位是 `StackType_t`，Cortex-M 上是 4 B。F407 lab 场景 1 创建 `low`、`high`、`rpt` 三个任务，栈深分别是 256、256、320 字：

   | 任务 | 栈深（字） | 折算（B） |
   | --- | --- | --- |
   | `low` | 256 | 1024 |
   | `high` | 256 | 1024 |
   | `rpt` | 320 | 1280 |
   | 合计 | 832 | 3328 |

   `configMINIMAL_STACK_SIZE = 128` 字 = 512 B，是空闲任务/最小任务的栈下限，不是这三个业务任务的栈（`FreeRTOSConfig.h:27`）。`configTOTAL_HEAP_SIZE = 16 * 1024 = 16384 B`（`:36`），要同时覆盖这三个栈、三个 TCB、定时器任务，以及工程里其它队列、信号量；池尽时 `xTaskCreate` 返回负的错误码，不是静默截断。

   ![栈向下生长：水位线量余量，钩子抓现场（根书 F103 原理示意）](/images/ch15-stack-watermark.png)

   图是根书 F103/M3 的原理示意，讲的是读法：栈按字算、深水位看历史最深处、溢出用钩子抓现场；图中的 128 字与 F407 lab 的 256/256/320 字不是同一组数字，不能直接搬。运行期看水位用 `uxTaskGetStackHighWaterMark()`，读的是历史最低剩余字；lab 把 `configCHECK_FOR_STACK_OVERFLOW = 2`（`FreeRTOSConfig.h:31`）开满，切换时检查栈末尾的 `0xA5` 填充，命中就进 `vApplicationStackOverflowHook`。

2. **首帧账**：新任务的栈里先摆好五个值，第一次切换弹栈时它们会「变成」任务的初始寄存器。把这张表抄下来，再数一遍槽位：

   | 写进帧的值 | 来自 | 作用 |
   | --- | --- | --- |
   | xPSR `0x01000000` | `portINITIAL_XPSR`（`port.c:92`） | bit24 T 位 = 1，任务以 Thumb 状态开跑 |
   | PC = 入口 & `0xFFFFFFFE` | `portSTART_ADDRESS_MASK`（`port.c:100`） | 清 bit0；Thumb 状态由 xPSR 说，不由 PC 说 |
   | LR = `prvTaskExitError` | `portTASK_RETURN_ADDRESS`（`port.c:125` → `:234`） | 任务 `return` 的陷阱 |
   | R0 = 参数 | `pxPortInitialiseStack(..., pvParameters)` | AAPCS 第一个整型参数 |
   | EXC_RETURN = `0xFFFFFFFD` | `portINITIAL_EXC_RETURN`（`port.c:93`） | PSP + Thread 模式 + 无 FPU 帧 |

   首帧一共 18 个字 = 72 B：硬件帧 8 + 软件帧 9 + 对齐 1。下一节把布局画开。

3. **选位账**：同一个位图 `0x00200008`（bit 3 与 bit 21），FreeRTOS 与 RT-Thread 会挑出不同的答案：

   | 内核 | 选位规则 | 手算 | 结果 |
   | --- | --- | --- | --- |
   | FreeRTOS 优化路径 | `31 − CLZ(bitmap)` | `31 − 10` | 优先级 21 |
   | RT-Thread 32 级 | `__rt_ffs(bitmap) − 1` | `4 − 1` | 优先级 3 |

   不是哪个内核算错了，是优先级方向相反：FreeRTOS 数值大者先，RT-Thread 数值小者先。同一个位图，一个从最高置位取，一个从最低置位取。

4. **轮转账**：两个同优先级任务 A、B，先 A 后 B。挂表时 A、B 依次进同一格的队尾；选择时 `listGET_OWNER_OF_NEXT_ENTRY` 从上次位置的下一个取。两次选择会各取到一次，谁先跑由插入时的索引位置决定，但「轮转」这个关系不变。

这四笔账只需要源码和算术，不需要板子；后面每个机制都可以回到这四行对账。

## 机制

### 一、TCB 的第一字段是栈顶

`tskTaskControlBlock` 在 V11.1.0 的 `tasks.c:358` 定义，第一个成员是 `pxTopOfStack`；源码在 `tasks.c:360` 的成员注释里把话说死：这一项必须是 TCB 的第一个成员。`pxTopOfStack` 不是栈底，是当前栈顶——每次切换后，它指向该任务最后一次压栈的位置；栈底是另一个字段 `pxStack`，留给溢出检查。

```c
typedef struct tskTaskControlBlock
{
    volatile StackType_t * pxTopOfStack;   /* 当前栈顶；必须是第一个成员 */
    ListItem_t xStateListItem;             /* 挂在就绪/阻塞/挂起链表上 */
    ListItem_t xEventListItem;             /* 等哪个事件 */
    UBaseType_t uxPriority;                /* 数值越大优先级越高 */
    StackType_t * pxStack;                 /* 栈底，溢出检查用 */
    char pcTaskName[ configMAX_TASK_NAME_LEN ];
    /* ... */
} tskTCB;
```

| 字段 | 作用 | 备注 |
| --- | --- | --- |
| `pxTopOfStack` | 当前栈顶 | 偏移 0；PendSV 的存取锚点 |
| `xStateListItem` | 状态链表项 | 就绪、阻塞、挂起都靠它挂表 |
| `xEventListItem` | 事件链表项 | 队列、信号量等等待用 |
| `uxPriority` | 任务优先级 | 数值大者先 |
| `pxStack` | 栈底 | 溢出检查与栈水位用 |
| `pcTaskName` | 任务名 | 长度由 `configMAX_TASK_NAME_LEN` 决定 |

这个顺序不是排版习惯，是汇编级的硬约束。PendSV 里 `ldr r2, [r3]` 取到当前 TCB 后，`stmdb r0!, {r4-r11, r14}` 把软件帧压进任务栈，最后 `str r0, [r2]` 把新栈顶写回 TCB。这里的 `[r2]` 没有字段名，只有偏移 0；恢复时 `ldr r0, [r1]` 也从偏移 0 取新栈顶（`F2:196`）。只要在 `pxTopOfStack` 前面加一个字段，写回就会落进那个字段，恢复时又把字段值当成栈顶指针——第一次切换就会把 PSP 指向错误的位置。TCB 的布局是内核与 port 层之间的 ABI，不是可以随手调整的普通结构体。

顺带一个同名陷阱：`include/task.h:171` 的 `pxTopOfStack` 属于 `TaskStatus_t`，是 `uxTaskGetSystemState()`（填数组）或 `vTaskGetInfo()`（单任务）给外部看的快照（`task.h:158,1139`），不是 TCB；移植层说的偏移 0 永远指 `tasks.c` 里的那个。

### 二、首帧是「化妆」：18 个字装成「刚被中断」

新建的任务从没运行过，硬件没有替它压过异常帧。`pxPortInitialiseStack`（`port.c:202-231`）手工造出一份与 PendSV 保存的现场同形的栈帧；第一次切换恢复时，硬件与软件按同一套偏移弹栈，任务就像「一直在这儿干活」一样开始执行。

五个被写死的值各有理由：

- **xPSR = `0x01000000`**：bit24 是 T 位。Cortex-M 只支持 Thumb 指令集，异常返回时这一位为 0 会触发 UsageFault，所以初始值必须硬编码成 `0x01000000`（`port.c:92`）。
- **PC = 入口 & `0xFFFFFFFE`**：`portSTART_ADDRESS_MASK` 清掉函数指针的 bit0。Thumb 状态由 xPSR 的 T 位说明，不允许 PC 的 bit0 越权（`port.c:100`）。
- **LR = `prvTaskExitError`**：任务函数的「返回地址」指向 `port.c:234` 的陷阱函数：触发 `configASSERT`、关中断、死循环。任务函数不许 `return`，这是这条规则的物理来源；要退出任务就调 `vTaskDelete(NULL)`。
- **R0 = `pvParameters`**：新任务第一次拿到的实参。AAPCS 规定第一个整型参数走 r0。
- **EXC_RETURN = `0xFFFFFFFD`**：bit2 = 1 表示异常返回用 PSP，bit3 = 1 表示回 Thread 模式，bit4 = 1 表示这趟没有 FPU 行李，所以首帧是 18 个字而不是 26 个（`port.c:93`）。

这 18 个字可以按地址从低到高画出来：

```text
低地址（pxTopOfStack 返回的落点）
  R4 R5 R6 R7 R8 R9 R10 R11 | EXC_RETURN | R0 | R1 R2 R3 R12 LR PC xPSR | 对齐空位
  └───────── 软件帧 9 ─────────┘             └──────── 硬件帧 8 ────────┘   └ 1 ┘
高地址（创建前的栈顶）
```

软件帧 9 = R4–R11 + EXC_RETURN；硬件帧 8 = R0–R3、R12、LR、PC、xPSR；最上面一格是对齐空位。源码从初始栈顶回退 17 次，加上最后停住的落点，一共 18 个字 = 72 B（`F2:254-255,328`）。真正写入的只有 5 个槽：xPSR、PC、LR、R0、EXC_RETURN；其余 13 个槽（对齐 1 + R12/R3/R2/R1 + R4–R11）源码故意跳过初始化，运行后会被任务自己的寄存器覆盖。

F1:164-176 的 GDB 记录把 xPSR 放在 `pxTopOfStack` 指向的第一个字；按 `pxPortInitialiseStack` 的返回值和 `stmdb` 的压栈顺序，`pxTopOfStack` 应指向 R4 的槽位（源码未初始化），不是 xPSR。两者不一致，仓库里也没有 GDB 原始日志；这里以源码与 F2 的 18 字账为准，GDB 记录只标「来源说法(未复核)」。

![新任务首帧：xPSR、PC、LR、R0 与 EXC_RETURN 被写进任务栈](/anim/task-create-stack.svg)

图中按高地址到低地址摆出 xPSR、PC、LR、跳过的 r12/r3–r1、r0 与 r4–r11；画面省略了 r0 下方的 EXC_RETURN 槽与对齐空位，完整 18 字布局以上一段为准。弹栈顺序以正文/源码为准（`ldmia r0!, {r4-r11,r14}` 从低地址 r4 开始）；动画是原理示意，不是 GDB 实拍；首帧的逐字核对属于待做台架。

### 三、xTaskCreate 的六步：第六步有条件

`xTaskCreate` 在 V11.1.0 的 `tasks.c:1718`，初始化细节在 `tasks.c:1793` 的 `prvInitialiseNewTask`。六步如下：

| 步 | 动作 | 关键点 |
| --- | --- | --- |
| 1 | 分栈 | `pvPortMalloc(uxStackDepth * sizeof(StackType_t))`；单位是字，128 字 = 512 B |
| 2 | 分 TCB | `pvPortMalloc(sizeof(TCB_t))` |
| 3 | 初始化栈 | `prvInitialiseNewTask` → `pxPortInitialiseStack`，写首帧 |
| 4 | 初始化 TCB | 名字、优先级、列表项、栈底 |
| 5 | 挂就绪表 | `prvAddTaskToReadyList`，挂进 `pxReadyTasksLists[prio]` 的队尾 |
| 6 | 条件触发调度 | `taskYIELD_ANY_CORE_IF_USING_PREEMPTION( pxNewTCB )`（`tasks.c:87-97,2083-2088`）；只在抢占开启且新任务优先级更高时让出 |

第六步不是无条件立即切换。`taskYIELD_ANY_CORE_IF_USING_PREEMPTION( pxNewTCB )`（`tasks.c:87-97,2083-2088`）在抢占关闭时展开为空；抢占开启时也只在 `pxNewTCB->uxPriority > pxCurrentTCB->uxPriority` 的分支里调用；调用点还在 `if( xSchedulerRunning != pdFALSE )` 之内，调度器没启动时这一步根本不执行。更要注意调用时机：F407 lab 场景 1 的 `scene_start()` 在 `vTaskStartScheduler()` 之前运行（`mcu/code/rtos/01-freertos-lab/main.c:381-382`），这时调度器还没开跑，`xTaskCreate` 不会真正换人。调度器启动时还会创建空闲任务和优先级 4 的定时器任务；定时器任务先跑、随即阻塞在定时器队列上，之后才轮到优先级 2 的 `high`。所以按启动顺序推导，预期串口第一行是 `high` 的日志，这是启动顺序与阻塞关系的结果，不是第六步在创建 `high` 时抢占的功劳。要观察第六步，得在调度器运行后从某个任务里再创建更高优先级的任务。F1:104-111 把这一步写成「high 一建好就抢占」，跳过了「调度器已在跑」这个前提，来源说法(未复核)，不能照搬。

栈深单位是 `StackType_t`，Cortex-M 上 4 B：128 字 = 512 B，不是 128 B。V11.1.0 ARM_CM4F 的 `typedef portSTACK_TYPE StackType_t` 在 `portmacro.h:58`；F1:106,218 写的是 `:55`，那一行是 `portSTACK_TYPE`。来源说法有误，已按 V11.1.0 源码更正。把 128 字误当 128 B、只分 32 字，栈容量就只剩四分之一。

动态与静态两条创建路径的内存来源不同：

| 路径 | API | 栈与 TCB 来源 | 说明 |
| --- | --- | --- | --- |
| 动态 | `xTaskCreate` | `pvPortMalloc` | 运行时决定任务数与栈深；堆尽返回负的错误码 |
| 静态 | `xTaskCreateStatic` | 调用者提供 `StaticTask_t` + 栈数组 | 不依赖 heap；lab 的 `configSUPPORT_STATIC_ALLOCATION = 0`（`FreeRTOSConfig.h:35`），此工程不编译该 API |

`xTaskCreate` 成功返回 `pdPASS`（1），失败返回 `errCOULD_NOT_ALLOCATE_REQUIRED_MEMORY`（-1）；判断写成 `!= pdPASS`，不要写成 `== 0`，`pdFAIL` 是 0，不是错误码。静态创建不依赖堆，只要传入的 `StaticTask_t` 与栈数组有效，就不会因堆不足失败；代价是每个任务的两块内存要显式声明。

`INCLUDE_*` 门控也不是「默认全关」。F1:203 的「V11 默认全关」是过头话（来源说法(未复核)）；按 V11.1.0 的 `FreeRTOS.h`，`INCLUDE_vTaskDelay` 与 `INCLUDE_vTaskSuspend` 默认 0，但 `INCLUDE_xTaskGetCurrentTaskHandle` 默认 1。正确的说法是「部分默认 0，按 API 开启」：老工程升级后出现 `undefined reference to vTaskDelay`，不是代码坏了，是宏没开。lab 在 `FreeRTOSConfig.h:68-72` 显式打开了 `vTaskDelay`、`vTaskSuspend`、`xTaskGetTickCount`、`uxTaskGetNumberOfTasks` 与 `xTaskGetCurrentTaskHandle`。

### 四、就绪表：按优先级分格的链表数组

`pxReadyTasksLists[configMAX_PRIORITIES]` 是一个 `List_t` 数组，每个下标对应一个优先级。任务就绪时走 `prvAddTaskToReadyList`，做两件事：

```c
#define prvAddTaskToReadyList( pxTCB ) \
do { \
    taskRECORD_READY_PRIORITY( ( pxTCB )->uxPriority ); \
    listINSERT_END( &( pxReadyTasksLists[ ( pxTCB )->uxPriority ] ), \
                    &( ( pxTCB )->xStateListItem ) ); \
} while( 0 )
```

第一步更新最高就绪速查器；第二步把任务的 `xStateListItem` 挂到对应优先级的队尾。

`list.c` 里有两个插入函数，分工明确：`vListInsertEnd` 不排序，插到索引位置之前，就绪表用它；`vListInsert` 按 `xItemValue` 升序找位插入，延时表用它。延时项的 `xItemValue` 是唤醒时刻，所以延时表队首永远是最早该醒的任务。选择时 `listGET_OWNER_OF_NEXT_ENTRY` 从上次位置的下一个取；队尾插入 + 循环取头 = 同优先级的任务天然轮转，时间片不需要额外数据结构。`configUSE_TIME_SLICING = 1` 时，tick 也会给同优先级任务一次轮转机会（`F3:100-112,140-170`）。

每个优先级一条 `List_t`，这是实打实的 RAM。F3 用 `configMAX_PRIORITIES = 5` 与 `= 33` 两次 `sizeof` 测量反推 `(660 − 100) ÷ (33 − 5) = 20 B`（`F3:210`）；这是文档推导，默认没有开 list integrity 检查。lab 的 5 级就绪表骨架约 100 B，不含任务自己的 `ListItem_t`。F1:118 的「O(1)」要加限定：优化路径选最高是 O(1)；通用路径最坏要扫过所有非空优先级，最多 `configMAX_PRIORITIES` 次。lab 只有 5 级，扫描很短；级数大时这个差别才明显。

![就绪链表与延时链表：挂表只改指针，tick 从队首搬家](/anim/list-insert.svg)

图把就绪链表与延时链表画在一起，容易让人以为就绪表也按值排序；实际就绪表用 `vListInsertEnd` 挂队尾，按值排序的是延时表。图里「就绪链表按值排队」「xItemValue 兼作轮转计数」是动画简化，不能当源码结论；以本节和 F3 的 `vListInsertEnd`、`xNextTaskUnblockTime` 为准。动画是原理示意，不是逻辑分析仪波形；同优先级轮转的实测属于待做台架。

### 五、选最高就绪：标量扫描与位图 CLZ

`uxTopReadyPriority` 有两副面孔，由 `configUSE_PORT_OPTIMISED_TASK_SELECTION` 切换。

**通用路径（= 0）：标量 + 递减扫描。** `taskRECORD_READY_PRIORITY` 只在优先级更大时更新标量；选择时从标量开始，逐级检查 `pxReadyTasksLists[prio]` 是否为空，空就减一，直到非空（`tasks.c:160-200`）。最坏扫过 `configMAX_PRIORITIES` 级。

**优化路径（= 1，ARM_CM4F 默认）：32 位位图 + CLZ。** 每个优先级占一位；`portRECORD_READY_PRIORITY` 置位，`portGET_HIGHEST_PRIORITY` 用 `31 − CLZ(bitmap)` 取最高置位。M4F 上 `CLZ` 是一条指令，选最高与任务数无关。

配置陷阱在这里：`FreeRTOS.h` 里这个宏的通用默认是 0，但 `portmacro.h:144-145` 在 ARM_CM4F 上用 `#ifndef` 把它设成 1。只看 `FreeRTOS.h` 会以为 lab 走标量扫描，实际走位图。位图路径硬性要求 `configMAX_PRIORITIES ≤ 32`；优化路径开启时，`portmacro.h:161-162` 用 `#error` 拦住 33 级。关掉优化路径后，通用路径没有这个上限，代价是更多 `List_t` 与更长扫描。R1:89 写「FreeRTOS 最大优先级数 32」，只对优化路径成立；来源说法有误（范围错位），已按两条路径更正。

算例：位图 `0x00200008` 的置位是 bit 3 与 bit 21。最高置位是 21，`CLZ` 数出 31 − 21 = 10 个前导零，`31 − 10 = 21`，所以 FreeRTOS 选优先级 21（lab 只到 4，这里只是算术）。位图只记录哪些级有就绪任务；bit 21 为 1 就说明 21 级链表非空，具体是哪个任务由 `listGET_OWNER_OF_NEXT_ENTRY` 取。

![调度器结构：就绪链表数组、延时链表与最高优先级速查器](/arch/scheduler-structs.png)

图中速查器有两副面孔，链表有两兄弟：就绪表用队尾插入管轮转，延时表用排序插入管守时。图是原理示意，不是内存转储。

![8 位简化示意（优先级 7..0）：CLZ 找最高置位，32 位路径同理用 31 减 CLZ](/figures/rtos-03-scheduler.svg)

图是 8 位简化示意（优先级 7..0），图内最高置位画的是 5；32 位路径同理，`31 − CLZ` 把最高置位换算成优先级编号。第 N 位为 1 表示优先级 N 有就绪任务；位图路径只支持 32 级，lab 的 5 级只用最低 5 位。

### 六、tick 三段与 vTaskDelay 的「搬家」

`xTaskIncrementTick`（`tasks.c`，`F3:140-170`）在 tick 中断里只做三件事：

1. 节拍加一：`xTickCount` 增加。
2. 剪枝后看队首：新节拍还没到 `xNextTaskUnblockTime`，整个延时检查跳过；到了才进延时表，只看队首。
3. 必要时请求切换：如果醒来的任务优先级高于当前，或同优先级需要轮转，返回 `pdTRUE`；port 层据此挂 PendSV（第 23 章展开）。

```text
xConstTickCount = xTickCount + 1
xTickCount = xConstTickCount                    /* ① 节拍++ */

if xConstTickCount >= xNextTaskUnblockTime:     /* ② 剪枝 */
    loop:
        if 延时表为空:
            xNextTaskUnblockTime = portMAX_DELAY
            break
        if 队首的唤醒时刻 > xConstTickCount:
            xNextTaskUnblockTime = 队首的唤醒时刻
            break
        摘下队首 → prvAddTaskToReadyList(队首)

return 需要切换 ? pdTRUE : pdFALSE              /* ③ 请求切换 */
```

延时表由 `vListInsert` 按 `xItemValue` 升序维护，队首就是最早醒的任务；`xNextTaskUnblockTime` 记住这个时刻。没到点，tick 只做一次比较；到点才进循环，把到期的队首逐个摘下、挂回就绪表，再把 `xNextTaskUnblockTime` 更新为下一个队首的值（空表则 `portMAX_DELAY`）。1 kHz 下常态每拍一次比较，这是 tick 频率能拉高的原因之一。

`vTaskDelay` 不是原地等，是搬家：暂停调度器 → 把当前任务从就绪表摘下，按 `now + n` 挂进延时表 → 恢复调度器 → 如果恢复时没有触发切换，主动 `taskYIELD_WITHIN_API()` 让出 CPU。

```c
vTaskSuspendAll();
prvAddCurrentTaskToDelayedList( xTicksToDelay, pdFALSE );
xAlreadyYielded = xTaskResumeAll();
if( xAlreadyYielded == pdFALSE )
{
    taskYIELD_WITHIN_API();
}
```

片段只展示 n ≥ 1 的路径：V11.1.0 `tasks.c:2442` 用 `if( xTicksToDelay > 0U )` 包住挂延时表这一段；`vTaskDelay(0)` 不挂延时表，只强制一次重调度。

此后就绪表里没有这个任务，CPU 去跑别人；tick 到点再把它搬回就绪表。`vTaskDelay(n)` 的等待区间是 (n−1, n] tick：调用落在两拍之间，唤醒对齐到第 n 个拍边界。1 kHz 下 `vTaskDelay(1)` 是 (0,1] ms，不是精确 1 ms。固定周期用 `vTaskDelayUntil`，以上次计划唤醒点为锚；实际入口仍有抖动，`do_work()` 超过周期时下一次会立即返回，周期追不回来，该减 WCET 或加长周期。SysTick 的 LOAD 与寄存器细节见 [v1 第 11 章](../v1-drivers/11-systick-timebase-rtc.md)，本章不重列。

### 七、RT-Thread 的 rt_thread：对象头、内嵌定时器、两步启动

RT-Thread 的 `struct rt_thread`（RT-Thread 5.x `include/rtdef.h`）与 `tskTCB` 的对应关系（`R1:50-61`）：

| `rt_thread` 字段 | 含义 | `tskTCB` 对照 |
| --- | --- | --- |
| `parent`（`rt_object`） | 对象头：名字、类型、标志、容器链表 | 无直接对应 |
| `sp` | 当前栈顶 | `pxTopOfStack` |
| `current_priority` | 当前优先级，数值越小越高 | `uxPriority`，数值越大越高 |
| `stat` | 线程状态 | `eCurrentState` |
| `remaining_tick` | 剩余时间片 | 没有同名字段；延时场景由 `xStateListItem.xItemValue` 存唤醒时刻 |
| `thread_timer`（`rt_timer`） | 线程内嵌定时器 | 无内嵌，延时挂全局延时表 |
| `stack_addr` / `stack_size` | 栈底地址 / 栈大小 | `pxStack` / 栈深 |
| `entry` / `parameter` | 入口函数 / 参数 | 任务函数 / 参数 |

两处结构差异最值得记：`parent` 是 `rt_object` 对象头，带来名字、类型与对象容器，`list_thread` 能直接打印线程表；`thread_timer` 是线程内嵌的 `rt_timer`，线程延时把定时器挂到系统定时器链，而不是像 FreeRTOS 那样把任务挂进全局延时表。R1:59 的源表把该字段写成 `timer`，以 RT-Thread 5.x `rtdef.h` 的 `thread_timer` 为准。

`rt_thread_create` 从堆上分配 TCB 与栈，`rt_thread_init` 用调用者提供的静态内存；两者都只把线程建到 INIT 态，不进就绪表，必须再调 `rt_thread_startup`。lab 的 `spawn` 就是 create + startup 两步（`mcu/code/rtos/02-rt-thread-lab/applications/main.c:28-33`）：

```c
rt_thread_t t = rt_thread_create(name, entry, RT_NULL, 512, prio, 20);
RT_ASSERT(t != RT_NULL);   /* 堆不够时 create 返回 RT_NULL */
rt_thread_startup(t);
```

漏掉 `startup` 的症状是编译链接全过，上板只有 idle 在跑，串口没有线程输出。`rt_thread_create` 的栈大小单位是字节（512 就是 512 B），不是 FreeRTOS 的字；`RT_THREAD_PRIORITY_MAX = 32`（`rtconfig.h:17`），`RT_TICK_PER_SECOND = 1000`（`:18`）。lab 场景 1 的 `fast` 优先级 8、`slow` 优先级 9：RT-Thread 数值越小越高，所以 8 先于 9；同样两个数字放到 FreeRTOS，先跑的会是 9。

### 八、RT-Thread 的选位与 tick：最低置位，不是 CLZ 最高位

lab 的 `RT_THREAD_PRIORITY_MAX = 32`（`rtconfig.h:17`），并且定义了 `RT_THREAD_PRIORITY_32`（`:16`），所以就绪表是一个 32 位组：`rt_thread_ready_priority_group` 的每一位对应一个优先级。RT-Thread 的 0 最高，选最高就是找最低置位。

实现用 `__rt_ffs`（FFS/CTZ 语义；ARM 上可用 RBIT+CLZ 实现）：`__rt_ffs(bitmap) - 1` 就是最高优先级。`R1:15,79,180,188` 反复写「CLZ 找最低置位/第一个非空字节」，方向反了：CLZ 找最高置位。来源说法有误，已按 RT-Thread 调度源码方向更正。

算例：同一个 `0x00200008`（bit 3 与 bit 21）。`__rt_ffs` 返回 4（1 基），减一得 3，所以 RT-Thread 选优先级 3；FreeRTOS 选 21。两个内核的位图一样，挑的是相反的一端，原因只有一条：优先级方向相反。

`rt_thread_ready_table[32]` 的二级位图只在 `RT_THREAD_PRIORITY_MAX > 32` 时启用；lab 是 32，单级 32 位组，不建那张表。`R1:10,77,89` 把 256 级当成本工程事实，是范围错位；来源说法有误，已按 lab 配置更正。

tick 侧：`SysTick_Handler` 调 `rt_interrupt_enter()` → `rt_tick_increase()` → `rt_interrupt_leave()`（`board/board.c:73-78`），`rt_hw_board_init` 把 SysTick 装成 1 kHz（`board/board.c:90-92`）。`rt_tick_increase` 做三件事：`rt_tick` 加一；递减当前线程的 `remaining_tick`，时间片到期就让出；`rt_timer_check()` 检查内嵌定时器，到点的线程被唤醒，必要时进入 `rt_schedule`（`R1:117-141`）。线程延时不是全局延时表，而是线程自带的 `rt_timer`；这是两个内核在数据结构上的关键差别。

| 维度 | FreeRTOS lab | RT-Thread lab |
| --- | --- | --- |
| TCB 首字段 | `pxTopOfStack` | `parent`（`rt_object`） |
| 栈顶 | `pxTopOfStack` | `sp` |
| 优先级方向 | 数值大者先 | 数值小者先 |
| 级数 | 5（0..4） | 32（0..31） |
| 选最高 | 32 位位图 `31 − CLZ` | 32 位组 `__rt_ffs`（最低置位） |
| 延时存放 | 全局延时表 | 线程内嵌 `rt_timer` |
| 创建 | 直接挂就绪，条件让出 | create/init 后必须 startup |
| 栈单位 | `StackType_t`（4 B） | 字节 |

## 测量与证据

本章能复算的只有源码结构与算术；没有一条是本仓库的上板读数。读数按来路分四类：实测记录、来源说法(未复核)、文档推导、未实测。下表逐项标出来路。

### 读数来路表

| 取证项 | 来路 | 读数或结论 | 性质 |
| --- | --- | --- | --- |
| TCB 偏移 0 | `tasks.c:358,360`；`F1:63-78`；`F2:196` | `pxTopOfStack` 是首成员；PendSV 用 `str r0,[r2]` 按偏移 0 写栈顶 | 文档推导 |
| 首帧五个值 | `port.c:92-125,202-231`；`F1:82-100` | xPSR `0x01000000`、PC = 入口、LR = `prvTaskExitError`、R0 = 参数、EXC_RETURN = `0xFFFFFFFD` | 文档推导 |
| 首帧长度 | `port.c:202-231`；`F2:254-255,328` | 18 字 = 72 B = 硬件 8 + 软件 9 + 对齐 1；源码回退 17 次后落脚，共 18 字 | 文档推导 |
| `xTaskCreate` 第六步 | `F1:104-111`；V11.1.0 `tasks.c:87-97,2083-2088` | `taskYIELD_ANY_CORE_IF_USING_PREEMPTION( pxNewTCB )`；只在抢占开启且新任务优先级更高时让出 | 文档推导 |
| 栈深单位 | `portmacro.h:58`；`F1:106,218` | `StackType_t` 4 B；128 字 = 512 B；来源写 `:55` 是错的 | 文档推导 |
| `List_t` 大小 | `F3:210`；`(660 − 100) ÷ (33 − 5)` | 20 B/级 | 文档推导 |
| `vTaskDelay(1)` 区间 | `F3:162-194,217,230-231` | (0,1] tick；1 kHz 下 (0,1] ms | 文档推导 |
| `INCLUDE_*` 默认 | `F1:203`；V11.1.0 `FreeRTOS.h` | `INCLUDE_vTaskDelay`/`vTaskSuspend` 默认 0，`INCLUDE_xTaskGetCurrentTaskHandle` 默认 1；F1 的「全关」过头 | 文档推导 |
| GDB 首帧 | `F1:160-178` | F1 记录 `pxCurrentTCB->pxTopOfStack = 0x20001a80`，但把 xPSR 放在该地址；按 V11.1.0 `pxPortInitialiseStack` 该地址应是 R4 槽位，记录与源码布局不一致；仓库无 GDB 日志 | 来源说法(未复核) |
| 串口日志 | `F1:34-36,128-134` | high 100 ms、low 300 ms、每 2 s `vTaskList`；无板上输出 | 未实测 |
| F3 七步 probe | `F3:210` | 140/160 B、58/70 条、21/10 次比较、`#error`；无产物 | 来源说法(未复核) |
| 逻辑分析仪轮转 | `F3:34` | 两同优先级任务 `vTaskDelay(1)`，1 ms 交替；未执行 | 未实测 |
| RT-Thread `list_thread` | `R1:27,143-148` | 栈 size/used/max 列；无 finsh 输出 | 未实测 |
| 双 OS 内存布局 | `R1:159` | R1 的「单级对二级」对照需要 RT-Thread >32；lab 当前 32 级，两边都是单级，照做看不到二级表；未执行 | 未实测 |
| lab 配置 | `FreeRTOSConfig.h:17,23,27,36`；`rtconfig.h:16-18`；`board/board.c:73-78,90-92` | 1 kHz、5 级、128 字最小栈、16 KiB heap；RT-Thread 32 级、1 kHz | 文档推导 |
| 本章板级实验 | 未执行 | 待实测 | 未实测 |

能互相对上的只有源码结构与算术：18 × 4 = 72、128 × 4 = 512、(660 − 100) ÷ (33 − 5) = 20、`31 − CLZ(0x00200008) = 21`、`__rt_ffs(0x00200008) − 1 = 3`。GDB 首帧、串口日志、七步 probe、逻辑分析仪与 `list_thread` 都没有本仓库的日志或产物，不能写成板上实测。

### 待做台架

| 日期 | 平台/板卡 | 实验 | 原始结果 | 结论 |
| --- | --- | --- | --- | --- |
| 待实测 | F407 lab | 在 `vTaskStartScheduler` 前用 GDB 打印 `pxCurrentTCB->pxTopOfStack`，`x/18xw` 逐字核对 xPSR/PC/LR/R0/EXC_RETURN | | |
| 待实测 | F407 lab | 两任务同优先级各 `vTaskDelay(1)`，逻辑分析仪测 LED 交替 | | |
| 待实测 | F407 lab | 把某任务栈从 256 字改到 64 字，触发 `configCHECK_FOR_STACK_OVERFLOW = 2` 与钩子，记录水位 | | |
| 待实测 | F407 lab | 运行 `mcu/code/rtos/03-scheduler/probe.sh` 七步，保存日志与反汇编 | | |
| 待实测 | F407 lab | RT-Thread `list_thread` 看栈水位；对照 `rt_thread` 字段与就绪组 | | |
| 待实测 | F407 | 同一板刷 FreeRTOS 与 RT-Thread，GDB 对照两边的就绪组；要观察二级表，另把 RT-Thread 配到 >32 | | |

这些台架都还没做。没有原始输出之前，本章只给源码结构与算术；表中的空白不是「通过」，是「未测」。

## 失败分支

| 现象 | 原因 | 区分证据 | 下一动作 |
| --- | --- | --- | --- |
| 新任务第一次运行就停在 `prvTaskExitError` 的断言或死循环 | 任务函数执行了 `return` | 断点 `prvTaskExitError`（`port.c:234`）命中；调用栈显示任务入口已返回 | 任务函数改成 `for (;;)`，或结尾 `vTaskDelete(NULL)` |
| 改了 TCB 字段顺序后，调度一跑就 HardFault 或栈顶乱 | 在 `pxTopOfStack` 前加了字段，PendSV 仍按偏移 0 写 | 对照 `tasks.c:358,360` 与 `F2:196`；看 `str r0,[r2]` 的偏移 | 恢复 `pxTopOfStack` 为首成员；要扩展就把字段放后面 |
| `xTaskCreate` 返回负值 | heap 池子不够，栈或 TCB 分配失败 | 返回值不是 `pdPASS`；剩余 heap 接近 0 | 加大 `configTOTAL_HEAP_SIZE`，减小栈，或改静态创建 |
| 高优先级任务建好后没有立即跑 | 调度器还没启动；抢占关闭；或新任务优先级不高于当前 | 查 `vTaskStartScheduler` 是否已调用、`configUSE_PREEMPTION` 与 `uxPriority`；就绪表里有它，当前仍在跑 | 先启动调度器；开抢占或提高优先级；不要在中断里直接 create |
| 同优先级两个任务一个长期不跑 | 时间片关闭，或任务不阻塞 | 查 `configUSE_TIME_SLICING`；看任务是否一直 Ready | 开时间片，或加 `vTaskDelay` / `taskYIELD` |
| `vTaskDelay(1)` 实测不是 1 ms | 相对延时，唤醒对齐到下一拍，区间 (0,1] tick | GPIO 翻转测间隔，随调用相位变化 | 不要拿它当精确计时；固定周期用 `vTaskDelayUntil` |
| 周期越来越长 | `vTaskDelay` 是相对延时，工作时间累进 | 记录每次唤醒时刻，周期约等于工作加延时 | 改用 `vTaskDelayUntil`，减小 WCET |
| 优先级设到 33 编译报 `#error` | 位图优化路径只支持 ≤32 | 看 `portmacro.h:161-162`；当前 `configUSE_PORT_OPTIMISED_TASK_SELECTION` | 降到 ≤32，或关掉优化路径走标量扫描 |
| `configMAX_PRIORITIES` 调大后 RAM 吃紧 | 每个优先级一条 `List_t`，约 20 B/级 | 看 map 文件里 `pxReadyTasksLists` 的大小；算 20 × 级数 | 合并优先级，或确认是否真需要那么多级 |
| RT-Thread 线程创建后不运行 | `rt_thread_create` / `rt_thread_init` 只到 INIT，没 `rt_thread_startup` | `list_thread` 看到线程在 INIT；串口没有线程输出 | 补 `rt_thread_startup(t)` |
| RT-Thread 高优先级线程不抢占 | 优先级数值越大反而越低，写反了 | 看 `current_priority` 与线程表；确认 0 最高 | 把高优先级线程的数值改小 |
| RT-Thread 选错线程 | 以为 CLZ 找最低置位，方向写反 | 对照 `__rt_ffs` 结果与位图；0 最高 | 用 `__rt_ffs` / CTZ 找最低置位，不要用裸 CLZ |
| 任务打印后 HardFault，水位接近 0 | 栈按字/字节混淆，或局部大数组占栈 | `uxTaskGetStackHighWaterMark` 接近 0；`0xA5` 溢出钩子命中 | 按字算栈，加大栈，把大数组移出栈 |

## 社区开源实现

本章的概念——TCB、就绪表、优先级位图、上下文切换——在两个最常用的开源内核里就是主干源码文件，值得按章对照读：

| 仓库 | 文件 | 看什么 |
| --- | --- | --- |
| [FreeRTOS/FreeRTOS-Kernel](https://github.com/FreeRTOS/FreeRTOS-Kernel) | `tasks.c` | 本章所有抽象的工业实现：`tskTCB` 结构体、`pxReadyTasksLists[]` 每优先级一条链表（对应"约 20 B/级"的 RAM 账）、`xTaskCreate` 先分配栈+TCB 再挂就绪表、`prvAddTaskToReadyList` 是宏而非函数——位图优化路径就在这个宏里 |
| [FreeRTOS/FreeRTOS-Kernel](https://github.com/FreeRTOS/FreeRTOS-Kernel) | `list.c` | `List_t`/`ListItem_t` 的环形双向链表与 `listGET_OWNER_OF_NEXT_ENTRY`——同优先级时间片轮转就是"游标下移一格"，代码只有几行 |
| [RT-Thread/rt-thread](https://github.com/RT-Thread/rt-thread) | `src/scheduler_up.c`（v5.0 起由旧 `scheduler.c` 拆分） | RT-Thread 的单核调度器：`rt_schedule()` 取最高优先级线程、就绪表位图用 `__rt_ffs`（CTZ 找最低置位，0 最高——对照失败分支里"方向写反"那条） |
| [RT-Thread/rt-thread](https://github.com/RT-Thread/rt-thread) | `src/thread.c` | `rt_thread_create`/`rt_thread_init` 只把线程放进 INIT 态，必须 `rt_thread_startup` 才进调度——对照失败分支"创建后不运行" |

两个内核值得对着读同一处：FreeRTOS 的 `configUSE_PORT_OPTIMISED_TASK_SELECTION`（CLZ，≤32 级，失败分支里 `#error` 的来源）与 RT-Thread 的 `__rt_ffs`（标量+位图混合）是同一个问题——"O(1) 找最高优先级"——的两份答案。读完再回看本章机制一节，抽象名词就都有了出处。版本口径：本书取证绑 FreeRTOS V11.x 与 RT-Thread v5.3.0，读源码时选对应 tag。

## 离开检查

1. TCB 的第一个字段是什么？为什么不能在前面加字段？
2. 新任务首帧的五个真值各是什么？任务函数为什么不能 `return`？
3. 首帧为什么是 18 字 = 72 B？硬件帧、软件帧、对齐各多少？
4. `xTaskCreate` 六步是什么？第六步在什么条件下才切换？
5. 栈深 128 是多少字节？`StackType_t` 在 V11.1.0 ARM_CM4F 的哪一行？来源写错了什么？
6. 同优先级轮转靠哪两个动作？`vListInsertEnd` 与 `vListInsert` 各管什么？
7. `uxTopReadyPriority` 的两副面孔是什么？`31 − CLZ` 怎么算？
8. `configMAX_PRIORITIES ≤ 32` 约束谁？只看 `FreeRTOS.h` 为什么会误判？
9. tick 三段是什么？`xNextTaskUnblockTime` 剪枝省了什么？
10. `vTaskDelay` 为什么是搬家不是等待？`vTaskDelay(1)` 的区间是多少？
11. 动态与静态创建的内存来源各是什么？`INCLUDE_*` 的默认是什么？
12. RT-Thread 的 `rt_thread` 首成员、`sp`、优先级方向、内嵌定时器各是什么？
13. RT-Thread lab 是 32 级还是 256 级？二级位图何时启用？
14. RT-Thread 找最高优先级为什么用 `__rt_ffs` 而不是 CLZ？给一个位图例子。
15. 本章哪些读数是「来源说法(未复核)」或「未实测」？为什么不能写成板上实测？
16. 第 23 章接手什么？本章为什么停在这里？

<details>
<summary>对照答案</summary>

1. 第一个字段是 `pxTopOfStack`。PendSV 的 `str r0, [r2]` 按 TCB 地址的偏移 0 写栈顶，恢复时也从偏移 0 取；在前面加字段会让写回落进新字段，恢复时把字段值当栈顶，第一次切换就坏。TCB 布局是内核与 port 层之间的 ABI。
2. xPSR = `0x01000000`（Thumb 位）；PC = 任务入口 & `0xFFFFFFFE`；LR = `prvTaskExitError`；R0 = 任务参数；EXC_RETURN = `0xFFFFFFFD`。LR 指向陷阱函数，任务 `return` 会落进断言关中断死循环；要退出用 `vTaskDelete(NULL)`。
3. 18 个字：硬件帧 8（R0–R3、R12、LR、PC、xPSR）+ 软件帧 9（R4–R11 + EXC_RETURN）+ 对齐 1。源码从初始栈顶回退 17 次，加上最后停住的落点，共 18 字 = 72 B；最上面一格是对齐空位。
4. 分栈、分 TCB、初始化栈、初始化 TCB、挂就绪表、条件触发调度。第六步只在 `configUSE_PREEMPTION = 1` 且新任务优先级高于当前任务时让出；否则任务留在就绪表里等。
5. 128 字 × 4 B = 512 B。`StackType_t` 在 V11.1.0 ARM_CM4F 的 `portmacro.h:58`；F1:106,218 写的 `:55` 是 `portSTACK_TYPE`。来源说法有误，已按 V11.1.0 源码更正。
6. 靠 `vListInsertEnd` 把任务挂到就绪格队尾，靠 `listGET_OWNER_OF_NEXT_ENTRY` 从上次位置的下一个取。前者用于就绪表的轮转，后者用于选择；`vListInsert` 按 `xItemValue` 排序，用于延时表，不管轮转。
7. 通用路径是标量 `uxTopReadyPriority` 取最大、选择时递减扫描；优化路径是 32 位位图，`31 − CLZ(bitmap)` 取最高置位。位图 `0x00200008` 的最高置位是 21，`CLZ` 为 10，`31 − 10 = 21`。
8. 只约束 `configUSE_PORT_OPTIMISED_TASK_SELECTION = 1` 的位图路径；通用路径可以超过 32，代价是更多 `List_t` 与更长扫描。`FreeRTOS.h` 的通用默认是 0，但 `portmacro.h:144-145` 在 ARM_CM4F 上用 `#ifndef` 设成 1；只看前者会误以为走标量扫描。
9. 节拍加一；用 `xNextTaskUnblockTime` 剪枝，没到点就跳过延时检查，到了才看延时表队首并把到期的任务挂回就绪表；必要时返回 `pdTRUE` 请求切换。剪枝让常态每拍只做一次比较，而不是遍历整张延时表。
10. `vTaskDelay` 把当前任务从就绪表摘下、按唤醒时刻挂进延时表，再恢复调度并让出 CPU；任务在延时期间不在就绪表里，CPU 去跑别人。`vTaskDelay(1)` 的区间是 (0,1] tick；1 kHz 下是 (0,1] ms，不是精确 1 ms。
11. 动态 `xTaskCreate` 用 `pvPortMalloc` 分配栈与 TCB；静态 `xTaskCreateStatic` 由调用者提供 `StaticTask_t` 与栈数组，不依赖 heap。`INCLUDE_*` 部分默认 0：`INCLUDE_vTaskDelay` / `INCLUDE_vTaskSuspend` 默认 0，`INCLUDE_xTaskGetCurrentTaskHandle` 默认 1；用哪个开哪个。
12. `rt_thread` 首成员是 `parent`（`rt_object` 对象头）；`sp` 对应 `pxTopOfStack`；`current_priority` 数值越小越高；线程内嵌 `rt_timer`，延时把定时器挂到系统定时器链。`rt_thread_create` / `rt_thread_init` 之后必须 `rt_thread_startup`。
13. lab 是 32 级（`RT_THREAD_PRIORITY_MAX = 32`，`RT_THREAD_PRIORITY_32`），单级 32 位组。`rt_thread_ready_table[32]` 二级位图只在 `RT_THREAD_PRIORITY_MAX > 32` 时启用；把 256 级当本工程事实是范围错位。
14. 因为 RT-Thread 的 0 最高，要从最低置位找；`__rt_ffs` 是 FFS/CTZ 语义（ARM 上可用 RBIT+CLZ 实现），`__rt_ffs(bitmap) − 1` 就是最高优先级。位图 `0x00200008` 的 bit 3 与 bit 21 中，`__rt_ffs` 返回 4，减一得 3；裸 CLZ 会选 21，方向就反了。
15. GDB 首帧与 F3 七步 probe 是「来源说法(未复核)」；串口日志、逻辑分析仪轮转、RT-Thread `list_thread` 与双 OS 内存布局是「未实测」。仓库里没有这些实验的日志或产物，不能写成 F407 板上实测。
16. 第 23 章接手 PendSV 汇编、软硬栈帧、FPU 懒堆叠与 `ARM_CM3` / `ARM_CM4F` 移植；本章只到任务、TCB、就绪表、tick 与 RT-Thread 对照，不展开切换的寄存器搬运。

</details>

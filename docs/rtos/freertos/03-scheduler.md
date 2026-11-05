---
title: F3 调度器：一条 CLZ 选出下一个任务
status: done
difficulty: 3
minutes: 50
---

# F3 调度器：位图、tick 与阻塞延时

> 🎯 现在冻结一个 tick：当前任务刚调用 `vTaskDelay`，另一个同优先级任务在就绪表里，更高优先级任务还没到唤醒时刻。下一位是谁？别凭“优先级高就先跑”的口号猜，真正答案藏在三样东西里：就绪速查器、两条链表和下一次唤醒时间。调度器不是黑箱，它是一场可以逐帧判案的搬家游戏。

## 本章精髓

1. **就绪表 = 链表数组 + 一个"最高非空"速查器**：`pxReadyTasksLists[configMAX_PRIORITIES]` 是货架（F1），`uxTopReadyPriority` 是速查器：通用路径里是标量（递减扫描），M4F 移植优化路径里是 **32 位位图**（CLZ 一把出最高位）。
2. **tick 中断干三件事**：节拍++、查延时列表队首谁该醒了、（必要时）请求切换，`xTaskIncrementTick` 就读这三段。
3. **`vTaskDelay` 不是"等"，是"搬"**：把自己挂进按唤醒时间排序的延时链表，然后让出 CPU：任务真的"不在"了，这是 RTOS 延时与裸机死等的本质区别。

<details>
<summary>🌐 English Abstract</summary>

**Ready list = array of linked lists + a "highest non-empty" lookup**. `pxReadyTasksLists[configMAX_PRIORITIES]` is the shelf; `uxTopReadyPriority` is the lookup—scalar in generic path (linear scan), **32-bit bitmap** in M4F optimized path (CLZ instruction finds highest set bit in O(1)). **Tick interrupt does three things**: increment tick count, check delay list head for tasks to wake, request context switch if needed. **`vTaskDelay` is not "wait", it's "move"**: task moves to delay list (sorted by wake time), then yields CPU—task is truly "gone", the fundamental difference between RTOS delay and bare-metal busy-wait.

</details>

- **能理解**：为什么 tick 只查延时表**队首**（O(1) 的秘密）；为什么位图路径要求优先级 ≤32；为什么 `vTaskDelay(1)` 不能当精确 1ms 用。
- **能用**：RunTimeStats 实测任务占比验证调度行为；按场景选 vTaskDelay / vTaskDelayUntil。

## 先修

- [F1 任务与 TCB](01-task-tcb.md)、[F2 上下文切换](02-context-switch.md)、[S5 SysTick](../../stm32/05-systick.md)。

## 先跑起来（10 分钟 quick win）

两任务同优先级各 `vTaskDelay(1)`：逻辑分析仪测两个 LED 翻转时刻，1ms 交替出现，时间片轮转眼见为实。

接线前先画一条只有“运行、延时、就绪”的时间线，押下一次亮灯属于谁，再看逻辑分析仪。若实测与你的图不一致，不要先怪时间片：先问当前任务被搬进了哪条链表、延时队首是否到点、同优先级就绪表的索引停在哪里。每一次翻转都能在数据结构里找到座位。

## 动画：一条链表撑起整个调度

新任务按值找位插入（只改 4 根指针）；tick 到点，延时链表队首搬家到就绪链表：**vTaskDelay 没有魔法，就是挂进延时链表睡 N 拍**。

![就绪链表插入动画](/anim/list-insert.svg)

## 小节结构

| 小节 | 内容 | 四件套 |
|---|---|---|
| 一、速查器双实现 | 通用扫描 vs 位图 CLZ（两版宏原文对照） | 库解析 |
| 二、入库动作 | `prvAddTaskToReadyList` 两步走 | 库解析 |
| 三、链表两兄弟 | `vListInsertEnd` 轮转 vs `vListInsert` 排序 | 代码分析 |
| 四、tick 三段 | `xTaskIncrementTick` 走查 + 队首剪枝 | 库解析 |
| 五、vTaskDelay 真相 | 挂延时表原文；抢占点全集 | 代码分析 |
| 六、CPU 统计 | RunTimeStats 配置与解读 | 配置 |

## 一、速查器双实现：通用扫描 vs 一条 CLZ

调度器的家当先看图：速查器两副面孔、链表两兄弟、tick 居中调度。

![调度器结构：速查器双实现、就绪与延时链表、tick 到期唤醒](/arch/scheduler-structs.png)

选下一个任务 = 找"最高的非空就绪链表"。tasks.c（V11.1.0）里这条宏有**两副面孔**，由 `configUSE_PORT_OPTIMISED_TASK_SELECTION` 切换。

**通用路径（=0）：标量 + 递减扫描。** `uxTopReadyPriority` 只是个数：

```c
#define taskRECORD_READY_PRIORITY( uxPriority ) \
do {                                            \
    if( ( uxPriority ) > uxTopReadyPriority )   \
    {                                           \
        uxTopReadyPriority = ( uxPriority );    \
    }                                           \
} while( 0 )
```

选择时从它开始往下找非空链表：

```c
while( listLIST_IS_EMPTY( &( pxReadyTasksLists[ uxTopPriority ] ) ) != pdFALSE )
{
    configASSERT( uxTopPriority );
    --uxTopPriority;                       /* 一层层往下摸 */
}
listGET_OWNER_OF_NEXT_ENTRY( pxCurrentTCB, &( pxReadyTasksLists[ uxTopPriority ] ) );
```

**移植优化路径（=1，M4F 默认）：位图 + CLZ。** 同一个变量摇身变成位图。portmacro.h（ARM_CM4F）原文：

```c
#define portRECORD_READY_PRIORITY( uxPriority, uxReadyPriorities )  ( uxReadyPriorities ) |= ( 1UL << ( uxPriority ) )
#define portRESET_READY_PRIORITY( uxPriority, uxReadyPriorities )   ( uxReadyPriorities ) &= ~( 1UL << ( uxPriority ) )
#define portGET_HIGHEST_PRIORITY( uxTopPriority, uxReadyPriorities ) uxTopPriority = ( 31UL - ( uint32_t ) ucPortCountLeadingZeros( ( uxReadyPriorities ) ) )
```

第 N 位=1 ⟺ 优先级 N 有就绪任务。`ucPortCountLeadingZeros` 在 M4F 上就是一条 `CLZ` 汇编：**32 位里找最高置位，一条指令，O(1)，与任务数无关**。代价：位图 32 位，所以此路径要求 `configMAX_PRIORITIES ≤ 32`。

> **【注】** 网上很多文章说"`uxTopReadyPriority` 是位图"，只对了一半：位图是**移植优化路径**的形态；通用路径里它是标量。读源码先看 `configUSE_PORT_OPTIMISED_TASK_SELECTION` 是哪条路，再谈语义。这也是读 FreeRTOS 的通用方法论：**一切结论先问配置宏**。

## 二、入库动作：两步走

任务就绪时（新建/解除阻塞/延时到期），走同一个宏（tasks.c）：

```c
#define prvAddTaskToReadyList( pxTCB )                                                              \
do {                                                                                                \
    taskRECORD_READY_PRIORITY( ( pxTCB )->uxPriority );              /* ① 速查器记账 */             \
    listINSERT_END( &( pxReadyTasksLists[ ( pxTCB )->uxPriority ] ), &( ( pxTCB )->xStateListItem ) ); /* ② 挂到货架队尾 */ \
} while( 0 )
```

①记账（标量取大 / 位图置位）②挂队尾。为什么队尾不是队首？因为 `listGET_OWNER_OF_NEXT_ENTRY` 从"上次的下一个"继续取：**队尾插入 + 循环取头 = 同优先级天然轮转**，时间片不需要额外数据结构。

## 三、链表两兄弟：一个管轮转，一个管守时

list.c 全文件只有两个插入函数，分工明确（V11.1.0 原文节选）：

`vListInsertEnd`：不排序，插到"索引位置之前"（即下一个被取走的队尾）：

```c
pxNewListItem->pxNext = pxIndex;
pxNewListItem->pxPrevious = pxIndex->pxPrevious;
pxIndex->pxPrevious->pxNext = pxNewListItem;
pxIndex->pxPrevious = pxNewListItem;
```

`vListInsert` 则**按 xItemValue 升序**找位插入：

```c
for( pxIterator = ( ListItem_t * ) &( pxList->xListEnd );
     pxIterator->pxNext->xItemValue <= xValueOfInsertion;
     pxIterator = pxIterator->pxNext )
{
    /* 空循环体:纯粹迭代到插入点 */
}
```

延时列表用后者，链表项的值 = **唤醒时刻**，于是队首永远是"最早该醒的"。这就是下一节 O(1) 剪枝的地基。四根指针改完收工，插入动画里看得清清楚楚。

## 四、tick 三段：醒人、换片、（必要时）换片场

SysTick 每拍调用一次 `xTaskIncrementTick`（tasks.c 节选）：

```c
const TickType_t xConstTickCount = xTickCount + ( TickType_t ) 1;
xTickCount = xConstTickCount;                 /* ① 节拍++ */

if( xConstTickCount >= xNextTaskUnblockTime ) /* ② 剪枝:队首都没到点就整个跳过 */
{
    for( ; ; )
    {
        if( listLIST_IS_EMPTY( pxDelayedTaskList ) != pdFALSE )
        {
            xNextTaskUnblockTime = portMAX_DELAY;
            break;
        }
        else
        {
            /* 只看队首:它的 xItemValue 就是最早唤醒时刻 */
            ...
        }
    }
}
```

注意那行剪枝：`xNextTaskUnblockTime` 记着"下一个该醒的时刻"，tick 值没追上它，整个延时检查**一行比较就跳过**：1kHz 下每拍 1 次比较，这就是 FreeRTOS 敢让 tick 跑高频率的底气。追上了才进循环：队首到点→摘出→`prvAddTaskToReadyList`→看下一个队首，直到队首未到点。

现在重判开场题：更高优先级任务“存在”不等于它“就绪”。只要唤醒时刻没到，它仍在延时表里，速查器根本看不见它；调度器会从当前可见的最高非空就绪链表选人。优先级决定就绪任务之间谁先跑，链表状态决定谁有资格参选。

第三件事在函数尾部（configUSE_PREEMPTION + configUSE_TIME_SLICING 时）：若有同优先级就绪任务等着轮转，返回 `pdTRUE`，port 层据此**挂起 PendSV**。至于 PendSV 怎么换魂，[F2](02-context-switch.md) 的十一条汇编已经讲透，调度器只管"发信号"，搬寄存器是 PendSV 的活。

## 五、vTaskDelay 真相：挂表、让出、不等任何人

```c
void vTaskDelay( const TickType_t xTicksToDelay )
{
    if( xTicksToDelay > ( TickType_t ) 0U )
    {
        vTaskSuspendAll();                                        /* 调度器暂停,搬家期间不许捣乱 */
        prvAddCurrentTaskToDelayedList( xTicksToDelay, pdFALSE ); /* 挂进延时链表,值=唤醒时刻 */
        xAlreadyYielded = xTaskResumeAll();
    }
    if( xAlreadyYielded == pdFALSE )
    {
        taskYIELD_WITHIN_API();                                   /* 主动让出 → PendSV */
    }
}
```

三行核心：**挂表 → 恢复调度 → 让出 CPU**。没有任何"等"：此刻起这个任务在就绪表里查无此人，直到 tick 把它搬回来。裸机的 `delay_ms()` 是原地空转烧 CPU，`vTaskDelay` 是"挂牌睡觉"，CPU 转头去伺候别人。

由此推出**抢占点全集**：任务只在三处可能被换下：① tick 中断（醒人/轮转触发 PendSV）② 任务自己调 API（delay/队列/信号量内部 YIELD）③ 中断退出（FromISR 系列置了 xHigherPriorityTaskWoken）。

> **【注】** `vTaskDelay(1)` 的延时区间是 (0, 1] 拍：你在拍中任何时刻调用，都睡到**下一拍**边界。想要严格周期（如 10ms 整的采样环），用 `vTaskDelayUntil`（它以上次唤醒点为锚，消除抖动累积）。

## 六、CPU 统计：用数据证明调度

`configGENERATE_RUN_TIME_STATS=1` + 一个高精度定时器（如 TIM2 跑 10kHz+），`vTaskGetRunTimeStats` 打印各任务绝对/相对占用。实验要求：两同优先级任务 ≈50/50；其中一个 +1 优先级 → 100/0。**调度行为是可测量的事实，不是信仰**，这也是全站"眼见为实"的落脚点。

## 记忆锚点

::: tip 一句话记住
**位图置位 CLZ 秒选（优化路径），标量递减慢扫（通用路径）；tick 三事：醒人、轮转、换片场；vTaskDelay 是挂表睡觉，不是原地死等。**
:::

**延伸**：SysTick 与硬件 TIM 分工，SysTick 管调度节拍，TIM 管外设时基（[S6](../../stm32/06-tim.md)）；软件定时器依赖 tick，见 [F6](06-notify-event-timer.md)。

## 实物实验

- **不用板子也能把本章每一个数字打出来**：`cd code/rtos/03-scheduler && sh probe.sh`。七步一条命令跑完：把 `configUSE_PORT_OPTIMISED_TASK_SELECTION` 掰成不写 / 1 / 0 编三份 `tasks.o` 逐字节对照（实测：不写与写 1 的两份**逐字节相同**，`.text.vTaskSwitchContext` 都是 140 字节，写 0 那份 160 字节）；数两条路的指令（58 条无后向跳转 vs 70 条含一个循环）；跑一遍把两条规则抄成的宿主机模拟器（同一张 10 次选择的事件表：通用路累计判空 21 次、平均 2.10、最坏 5；位图路 10 次、平均 1.00、最坏 1）；用 `configMAX_PRIORITIES=5` 与 `=33` 两个测量反推 `sizeof(List_t) = (660−100)÷(33−5) = 20` 字节；再把 `NPRIO=33` 交给位图路径，看 `portmacro.h:162` 那条 `#error` 原文。需要交叉工具链与 V11.1.0 内核（CI 的 arm-host 作业两样都装）。
- quick win 轮转证据 + RunTimeStats 占比实验（本章目标三）；
- 进阶：逻辑分析仪夹 LED，把 `configTICK_RATE_HZ` 从 1000 改 100 再测，看交替周期跟着变，tick 频率物理化。

## 常见坑

- **高优先级任务不延时**：永不放弃 CPU，低优先级全体饿死，`vTaskDelay` 是基本教养；
- **`vTaskDelay(1)` 当精确 1ms**：实际 (0,1] 拍区间，周期任务请用 `vTaskDelayUntil`；
- **`configTICK_RATE_HZ` 盲目拉 10k**：每拍都有醒人检查开销，1kHz 是通用甜点；
- **优先级开几十上百**：每个优先级一条链表，RAM 按条收租；位图路径还硬性 ≤32；
- **中断里调非 FromISR API**：list.c 注释里的崩溃清单第二名，`configMAX_SYSCALL_INTERRUPT_PRIORITY` 不是摆设。

## 短自测

1. 位图路径下 `uxTopReadyPriority` 第 12 位为 1 表示什么？选最高优先级要走几条指令？
<details><summary>参考答案</summary>优先级 12 至少有一个就绪任务。选优 = 一次 CLZ 加一次减法（31-CLZ），M4F 上两条指令，O(1)。</details>

2. tick 中断为什么敢只查延时链表队首？
<details><summary>参考答案</summary>延时链表用 vListInsert 按唤醒时刻升序排列，队首即最早该醒者；队首未到点则全员未到点，直接 break。配合 xNextTaskUnblockTime 剪枝，常态每拍只需一次比较。</details>

3. `vTaskDelay(10)` 在 tick=1kHz 时实际睡多久？为什么不是精确 10ms？
<details><summary>参考答案</summary>(9, 10] ms。调用时刻落在拍内任意位置，唤醒对齐到第 10 个拍边界，不足一拍的部分被"抹零"。要精确周期用 vTaskDelayUntil（以唤醒点为锚）。</details>

4. 同优先级轮转不需要额外数据结构，靠哪两个配合实现？
<details><summary>参考答案</summary>prvAddTaskToReadyList 把任务插到就绪链表队尾（listINSERT_END），taskSELECT_HIGHEST_PRIORITY_TASK 用 listGET_OWNER_OF_NEXT_ENTRY 循环取"下一个"：队尾进、循环出，天然 Round-Robin。</details>

## 对照表：本章概念 → 源码落点

| 概念 | 落点（FreeRTOS-Kernel V11.1.0） |
|---|---|
| 速查器双实现 | `tasks.c` taskRECORD/SELECT_HIGHEST_PRIORITY_TASK 两组宏（configUSE_PORT_OPTIMISED_TASK_SELECTION 分路） |
| 位图+CLZ | `portable/GCC/ARM_CM4F/portmacro.h` portRECORD/GET_HIGHEST_PRIORITY |
| 入库两步 | `tasks.c` prvAddTaskToReadyList |
| 排序/队尾插入 | `list.c` vListInsert / vListInsertEnd |
| tick 醒人剪枝 | `tasks.c` xTaskIncrementTick（xNextTaskUnblockTime 比较+队首循环） |
| 延时挂表 | `tasks.c` vTaskDelay → prvAddCurrentTaskToDelayedList |
| 本章所有数字怎么复核 | `code/rtos/03-scheduler/probe.sh` 七步一条命令跑完（三份 `tasks.o` 逐字节对照 / 两条路指令数 / 模拟器判空次数 / 20 字节每级 / 33 级被 `#error` 拦下 / tick 三段 / 链表两兄弟） |

## 延伸阅读

本章讲"高优先级先跑"这台机器怎么造；优先级该怎么分才能保证期限，是另一篇文章：

- **[\[D1\]](../../reference/bibliography.md#papers)** Liu & Layland 1973 — 速率单调（周期越短优先级越高）与 69.3% 利用率上界都出自这里；读完你会知道 `configMAX_PRIORITIES` 里的数字不该拍脑袋。

## 你做到了

- 调度器从"魔法"变成"速查器+链表+三条抢占路径"；
- 网上"位图"说法的适用边界被你亲手钉死（配置宏分路）；
- 调度行为可测量，RunTimeStats 是你的测谎仪。

回到那帧被冻结的 tick：你已经不需要背“调度器会选最高优先级”这句半真话。先看任务在哪张表里，再看速查器指向哪里，最后看这一拍是否请求切换，下一位运行者就能被你逐步推出来。

<div class="achievement">
✅ 下一站：<a href="04-queue.html">F4 队列</a>：任务间的"传送带"，环形存储+两个阻塞列表的源码级解剖。
</div>

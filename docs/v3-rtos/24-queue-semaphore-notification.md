---
title: "队列、信号量与通知"
platforms: [f407]
---

# 队列、信号量与通知

按键中断把键值送进队列，一个任务在 `xQueueReceive` 上等；按键不来，任务睡在队列的接收名单上，CPU 去跑别人。队列、二值信号量、计数信号量、互斥锁、递归互斥锁，在 FreeRTOS 里都是同一个 `QueueDefinition` 的不同配置；任务通知把这条通路缩成 TCB 里的两个数组。本章把这些结构拆到源码行，再算清 E04 的 6000/2500 与三笔 RAM 账。

证据先说清：本章没有新的上板读数。E04 的 `hardware_status` 是 `pending`，实测表全空；F6 的五幕模拟与 1312/56/616 是来源说法(未复核)；源码摘录与算术是文档推导。`Queue_t=80` 是本仓库 probe 声明的值，不是跨工程常数。

> 版本口径：FreeRTOS 的 `queue.c`、`tasks.c`、`semphr.h`、`event_groups.h` 行号与语义按 FreeRTOS-Kernel V11.1.0 对账；RT-Thread 的字段与函数名按 v5.3.0 的 `rtdef.h`、`ipc.c` 对账。根书 F103 例程按 V11.3.2，行号不与本章混排。

## 本章罗盘

- **问题**：一个 `QueueDefinition` 怎么同时当队列、二值信号量、计数信号量、互斥锁与递归互斥锁？`uxQueueType` 是字段还是宏？`prvCopyDataToQueue` 在 `uxItemSize=0` 时做什么，数据项写到 `pcTail` 会不会拆两段？`xQueueGenericSend` 的三条分支各做什么，`queueOVERWRITE` 为什么要求 `uxLength==1`？等待名单按什么叫号，同优先级谁先醒？唤醒更高优先级任务后，为什么不是立刻切？FromISR 为什么只能延迟让出，`pxHigherPriorityTaskWoken` 与 `portYIELD_FROM_ISR` 怎么配合，ISR 优先级阈值是多少？`xSemaphoreGive`/`xSemaphoreTake`/`xSemaphoreCreateMutex` 展开成什么，互斥锁为什么出生就 give 一次？优先级继承的三步是什么，还锁怎么回落，二值信号量为什么没有，ISR 里 take 互斥锁为什么是禁区？任务通知写 TCB 哪两个字段？事件组在 lab 为什么只有 24 位？软件定时器为什么只有一个守护任务？通知比队列快多少，为什么只写定性结论、要同板基准？深度 10、项 16 B 的队列占多少 RAM？1312/56/616/269 各是什么身份？RT-Thread 的 `suspend_thread`、`rt_mutex` 字段、邮箱与消息队列的真实口径是什么？E04 的 6000/2500 怎么算，F5 的「跑满 3000ms」为什么错，继承数值为什么是 22→20 而不是 1→3？
- **交付**：能在纸上画出 `QueueDefinition` 的字段分区，说出三种人生靠哪几个字段区分；能逐行读 `prvCopyDataToQueue`，指出单次 memcpy 与指针回绕，纠正「两段拷贝」；能写出 `xQueueGenericSend` 的三分支与 overwrite 断言；能写 FromISR 的标准中断骨架与优先级约束；能写出互斥锁继承三步与回落，说明 ISR 禁区；能算 248 B 与 1312/56/616/269；能按 E04 时间线算出 6000/2500，指出 6500 与 1→3 的错；能按 v5.3.0 说出 RT-Thread 的真实字段与函数名。
- **边界**：单平台 F407（Cortex-M4F、`ARM_CM4F`、lab 跑 HSI 16 MHz、`configMAX_PRIORITIES=5`、heap 16 KiB）。FreeRTOS 结论按 V11.1.0；根书 F103 例程按 V11.3.2，行号不混排。不展开队列集（queue set）、多通知槽与 8/56 位事件组的具体行为，只在位宽表里点名条件。E04 只写理论、模型与待实测，完整仪器实验归第 40 章。RT-Thread 只按 v5.3.0 的 IPC 字段与函数名，不把标准版 BSP 的配置与优先级级数当 lab 事实。通知速度只写定性结论：更快，幅度依配置，需同板基准；来源中的具体百分比/倍数没有版本、配置与引用，本章不采用。
- **依据锚点**：F4《队列》（`mcu/docs/rtos/freertos/04-queue.md`）、F5《信号量与互斥量》（`mcu/docs/rtos/freertos/05-sem-mutex.md`）、F6《任务通知、事件组与软件定时器》（`mcu/docs/rtos/freertos/06-notify-event-timer.md`）、R2《IPC 全家桶》（`mcu/docs/rtos/rtthread/02-ipc.md`）、E04《优先级反转复现》（`mcu/docs/lab/e04-priority-inversion.md`）。配置见 `mcu/code/rtos/01-freertos-lab/FreeRTOSConfig.h`（`:41-47`、`:62`），lab 场景见 `mcu/code/rtos/01-freertos-lab/main.c`（场景 2/3/4/6）。上游对账：FreeRTOS-Kernel V11.1.0 的 [queue.c](https://github.com/FreeRTOS/FreeRTOS-Kernel/blob/V11.1.0/queue.c)、[queue.h](https://github.com/FreeRTOS/FreeRTOS-Kernel/blob/V11.1.0/include/queue.h)、[semphr.h](https://github.com/FreeRTOS/FreeRTOS-Kernel/blob/V11.1.0/include/semphr.h)、[event_groups.h](https://github.com/FreeRTOS/FreeRTOS-Kernel/blob/V11.1.0/include/event_groups.h)、[tasks.c](https://github.com/FreeRTOS/FreeRTOS-Kernel/blob/V11.1.0/tasks.c)；RT-Thread v5.3.0 的 [ipc.c](https://github.com/RT-Thread/rt-thread/blob/v5.3.0/src/ipc.c)、[rtdef.h](https://github.com/RT-Thread/rt-thread/blob/v5.3.0/include/rtdef.h)。异常帧与 PendSV 让出见 [v1 第 10 章](../v1-drivers/10-interrupts-nvic-exti.md) 与 [第 23 章](./23-context-switch-porting.md)；tick 时基见 [v1 第 11 章](../v1-drivers/11-systick-timebase-rtc.md)。

## 先做出来

不接板，先把四笔账算在纸上。它们决定你上板后看到的是「队列真的没空间」，还是「名字根本没接上」。

### 1. 三种人生，一张字段表

`QueueDefinition` 在同一块内存上解释出队列、信号量与互斥锁。先按用途把字段分三列，再看哪些字段只对某一种人生有意义：

| 字段 | 普通队列 | 二值/计数信号量 | 互斥锁/递归互斥锁 |
| --- | --- | --- | --- |
| `pcHead` / `uxQueueType` | 存储区起点 | 指向 `Queue_t` 自身（非 NULL） | `NULL`（`queueQUEUE_IS_MUTEX`） |
| `pcWriteTo` | 下一个可写位置 | 不使用 | 不使用 |
| `u.xQueue.pcTail` | 尾后标记 | 不使用 | 不使用 |
| `u.xQueue.pcReadFrom` | 上一次读出的位置 | 不使用 | 不使用 |
| `u.xSemaphore.xMutexHolder` | 不使用 | 不使用 | 当前持有者 |
| `u.xSemaphore.uxRecursiveCallCount` | 不使用 | 不使用 | 递归层数 |
| `uxMessagesWaiting` | 当前项数 | 当前计数 | 0 或 1 |
| `uxLength` | 容量（项数） | 最大计数 | 1 |
| `uxItemSize` | 每项字节数 | 0 | 0 |
| 两条等待名单 | 收发都用 | 只用接收名单 | 只用接收名单 |

这张表的核心不是背字段，而是三个判断：`uxItemSize` 是否为 0、`uxQueueType` 是否为 NULL、`uxMessagesWaiting` 当前是多少。三件事一组合，五种 API 的行为就出来了。

### 2. 环形账：回绕的是指针，不是数据

设深度 5、项 16 B，存储区从 `0x2000_1000` 开始：

```text
pcHead   = 0x2000_1000
pcTail   = pcHead + 5 × 16 = 0x2000_1050   （尾后标记，不存数据）
槽位      = 0x1000, 0x1010, 0x1020, 0x1030, 0x1040
pcWriteTo 初值 = pcHead = 0x1000
pcReadFrom 初值 = pcHead + (5-1) × 16 = 0x1040
```

连续入队 A、B、C、D、E：A 写到 `0x1000`，写指针变 `0x1010`；……；E 写到 `0x1040`，写指针变 `0x1050`，`0x1050 >= pcTail`，于是回绕到 `0x1000`。单条 16 B 的 E 始终落在 `0x1040`–`0x104F` 这一段连续存储里，没有被拆成「尾部 0 B + 头部 16 B」之类的两段。出队时 `pcReadFrom` 先加 16，若越过 `pcTail` 再回到 `pcHead`，然后从新位置拷出。初始读指针故意放在最后一个槽位，第一次读先回绕，正好读到 A。

### 3. 发送真值表

`xQueueGenericSend(queue, item, timeout, position)` 只有四条出口：

| 条件 | 动作 | 返回 |
| --- | --- | --- |
| `uxMessagesWaiting < uxLength` | 按 `position` 拷贝，叫醒接收名单上的第一个 | `pdPASS` |
| `position == queueOVERWRITE` | 覆盖唯一槽位，叫醒接收者；上游要求 `uxLength==1` | `pdPASS` |
| 满、非覆盖、`timeout == 0` | 不拷贝，立即退出 | `errQUEUE_FULL` |
| 满、非覆盖、`timeout > 0` | 挂进 `xTasksWaitingToSend`，等空位或超时 | 有空位 `pdPASS`；超时 `errQUEUE_FULL` |

第三条和第四条常被合成一句「满了就阻塞」。不对：`timeout=0` 的发送根本不进名单，它立即返回错误。只有给了正超时，任务才有资格睡在发送名单上。

### 4. E04 时间线账

三任务：L 优先级 1，t=0 拿锁后做 3000 ms 的真 CPU 工作；M 优先级 2，t=500 起连续占 CPU 到 t=4500；H 优先级 3，t=1000 要同一把锁。

- 二值信号量版：L 在 t=0 到 t=500 已做 500 ms，被 M 抢占后停住。H 在 t=1000 阻塞，但二值信号量没有持有者，L 不会继承。M 跑到 t=4500，L 才继续做**剩余 2500 ms**，t=7000 还锁。H 从 t=1000 等到 t=7000，等待 6000 ms。
- 互斥锁版：H 在 t=1000 阻塞的同一刻，L 被抬到优先级 3，抢回 CPU，做完剩余 2500 ms，t=3500 还锁。H 等待 2500 ms。M 在 t=4500 跑完。

把 L 的剩余工作写成「3000 ms」会把 L 的完成时刻算到 7500 ms，进而把 H 的等待算成 6500 ms；这两个数都不对。L 不是从 t=4500 重新开始 3000 ms，它在被抢占前已经消耗了 500 ms。

![队列传值动画：生产者把数据拷贝进环形槽位，满时生产者睡、空时消费者睡](/anim/queue-passing.svg)

## 机制

### 一、一个结构体三种人生

`queue.c` 的 `QueueDefinition` 原文是下面这些字段。注意最后两行是宏，不是结构体成员：`uxQueueType` 只是 `pcHead` 的别名，`queueQUEUE_IS_MUTEX` 只是 `NULL`。

```c
/* queue.c V11.1.0，节选。uxQueueType 不是结构体成员，而是 pcHead 的别名宏；
   这里把它列在字段之后，是为了看清同一块内存的第二种解释。 */
typedef struct QueueDefinition
{
    int8_t * pcHead;           /* 存储区起点；互斥锁时被别名写成 NULL */
    int8_t * pcWriteTo;        /* 下一个可写位置 */

    union
    {
        QueuePointers_t xQueue;     /* pcTail：尾后标记；pcReadFrom：上次读出的位置 */
        SemaphoreData_t xSemaphore; /* xMutexHolder：持有者；uxRecursiveCallCount：递归层数 */
    } u;

    List_t xTasksWaitingToSend;     /* 写满时挂在这里，按优先级排序 */
    List_t xTasksWaitingToReceive;  /* 读空时挂在这里，按优先级排序 */

    volatile UBaseType_t uxMessagesWaiting; /* 当前项数 / 信号量计数 */
    UBaseType_t uxLength;                   /* 容量，单位是项，不是字节 */
    UBaseType_t uxItemSize;                 /* 每项字节数；信号量与互斥锁为 0 */

    volatile int8_t cRxLock;
    volatile int8_t cTxLock;
} xQUEUE;

#define uxQueueType         pcHead          /* queue.c:65 */
#define queueQUEUE_IS_MUTEX NULL            /* queue.c:66 */
```

`uxItemSize=0` 时，`xQueueGenericCreate` 不分配数据区，但 `prvInitialiseNewQueue` 不能把 `pcHead` 留成 NULL，因为 NULL 被保留作「这是互斥锁」的标记。源码的处理是 `pxNewQueue->pcHead = ( int8_t * ) pxNewQueue;`（`queue.c:578-583`），让 `pcHead` 指向结构体自身，作为一个合法的非 NULL 值。互斥锁随后在 `prvInitialiseMutex` 里执行 `pxNewQueue->uxQueueType = queueQUEUE_IS_MUTEX;`（`queue.c:623`），也就是把 `pcHead` 写成 NULL。

所以判断「这是不是互斥锁」的表达式 `uxQueueType == queueQUEUE_IS_MUTEX`，展开后就是 `pcHead == NULL`。二值信号量虽然也不存数据，但 `pcHead` 指向自身，不会被误判成互斥锁。这个细节解释了为什么 `uxQueueType` 不需要单独占一个结构体字段：它借用了 `pcHead` 的位子。

三种人生的分工：

- **普通队列**：`uxItemSize > 0`，`pcHead` 指向数据区，`pcWriteTo` 与 `pcReadFrom` 维护环形位置，两条等待名单都可能非空。
- **二值/计数信号量**：`uxItemSize == 0`，`pcHead` 非 NULL，`uxMessagesWaiting` 就是计数，`uxLength` 是最大计数。没有数据拷贝，也没有持有者。
- **互斥锁**：`uxItemSize == 0`，`pcHead == NULL`，`uxLength == 1`，`u.xSemaphore.xMutexHolder` 记录持有者。递归互斥锁只是在这个基础上多一个 `uxRecursiveCallCount`。

`uxLength` 是「能装几项」，不是「几字节」。深度 10、项 16 B 的队列，`uxLength=10`、`uxItemSize=16`，数据区 160 B。把 `uxLength` 当字节数是读源码时最常见的一处误读。

`cRxLock`/`cTxLock` 不是任务计数，而是「队列被锁住期间，ISR 取走/塞进了几项」的欠账。调度器挂起时，任务侧会锁队列；此时 ISR 不能直接改等待名单，只能把 `cRxLock`/`cTxLock` 加一。解锁时再按欠账补做 `xTaskRemoveFromEventList`。这两个字段是队列与 ISR 共存的缓冲区，不是给应用读的计数器。

### 二、prvCopyDataToQueue：整项拷贝，指针回绕

发送路径真正搬数据的函数是 `prvCopyDataToQueue`。它只做三件事，按 `uxItemSize` 分成三个分支：

```c
/* queue.c V11.1.0；省略 configUSE_MUTEXES 条件编译与 mtCOVERAGE_TEST_MARKER 探针 */
static BaseType_t prvCopyDataToQueue( Queue_t * const pxQueue,
                                      const void * pvItemToQueue,
                                      const BaseType_t xPosition )
{
    BaseType_t xReturn = pdFALSE;
    UBaseType_t uxMessagesWaiting;

    /* 本函数在临界区内被调用，先把当前计数读进局部变量 */
    uxMessagesWaiting = pxQueue->uxMessagesWaiting;

    if( pxQueue->uxItemSize == 0 )
    {
        if( pxQueue->uxQueueType == queueQUEUE_IS_MUTEX )
        {
            /* 先按旧持有者去继承，再清持有者 */
            xReturn = xTaskPriorityDisinherit( pxQueue->u.xSemaphore.xMutexHolder );
            pxQueue->u.xSemaphore.xMutexHolder = NULL;
        }
    }
    else if( xPosition == queueSEND_TO_BACK )
    {
        /* 整项一次 memcpy，不拆两段（queue.c:2420-2425） */
        ( void ) memcpy( ( void * ) pxQueue->pcWriteTo,
                         pvItemToQueue,
                         ( size_t ) pxQueue->uxItemSize );
        pxQueue->pcWriteTo += pxQueue->uxItemSize;
        if( pxQueue->pcWriteTo >= pxQueue->u.xQueue.pcTail )
        {
            pxQueue->pcWriteTo = pxQueue->pcHead;   /* 回绕的是指针 */
        }
    }
    else  /* queueSEND_TO_FRONT 或 queueOVERWRITE */
    {
        ( void ) memcpy( ( void * ) pxQueue->u.xQueue.pcReadFrom,
                         pvItemToQueue,
                         ( size_t ) pxQueue->uxItemSize );
        pxQueue->u.xQueue.pcReadFrom -= pxQueue->uxItemSize;
        if( pxQueue->u.xQueue.pcReadFrom < pxQueue->pcHead )
        {
            pxQueue->u.xQueue.pcReadFrom =
                ( pxQueue->u.xQueue.pcTail - pxQueue->uxItemSize );
        }

        if( xPosition == queueOVERWRITE )
        {
            if( uxMessagesWaiting > ( UBaseType_t ) 0 )
            {
                /* 覆盖不是新增：先减一，函数末尾统一加一，计数净不变 */
                --uxMessagesWaiting;
            }
        }
    }

    pxQueue->uxMessagesWaiting = ( UBaseType_t ) ( uxMessagesWaiting + 1 );
    return xReturn;
}
```

第一件：`uxItemSize == 0` 时没有数据可拷，只处理计数与互斥锁的持有者。互斥锁分支先调 `xTaskPriorityDisinherit`，再清 `xMutexHolder`。顺序不能反：去继承函数要拿旧持有者的 TCB 指针回落优先级；先把指针清成 NULL，就找不到该回落给谁了。

第二件：普通入队是**单次 memcpy 整项**。`pcWriteTo` 加上 `uxItemSize` 后，只有越过 `pcTail` 才回到 `pcHead`。`pcTail` 是「最后一项之后」的标记，不指向可写数据，也不参与 memcpy。单条数据永远落在一段连续的 `uxItemSize` 字节里，不存在「先写尾部、再写头部」的分段拷贝。F4 的正文写对了；旧测验里的「分两段 memcpy」是错的。

第三件：`queueSEND_TO_FRONT` 与 `queueOVERWRITE` 走同一个 else 分支，写的是 `pcReadFrom` 指向的位置，然后把读指针向前移。普通队列用 `xQueueSendToFront` 时，这是「插到队头」；`xQueueOverwrite` 只允许长度 1，此时 `pcReadFrom == pcHead`，写进去的就是唯一槽位。覆盖分支还会先把局部变量 `uxMessagesWaiting` 减一，再在函数末尾统一加一，净效果是计数不变——覆盖是替换，不是新增。少了这一步，长度 1 的队列覆盖一次，计数就会从 1 变成 2，和「唯一槽位」的语义直接矛盾。

补一个出队侧的对称细节：`prvCopyDataFromQueue` 先 `pcReadFrom += uxItemSize`，越过 `pcTail` 就回绕到 `pcHead`，然后才 memcpy 到调用者的缓冲区。初始 `pcReadFrom` 在最后一个槽位，所以第一次读先回绕到 0 号槽。读指针的「上一次读出的位置」这个语义，配上「先移后读」，才凑成先进先出。

互斥锁的还给路径也在 `prvCopyDataToQueue` 里，但递归互斥锁不是每层都走这里。`xQueueGiveMutexRecursive` 先把 `uxRecursiveCallCount` 减一，只有减到 0 才调用 `xQueueGenericSend`；没到 0 就只更新计数，不碰等待名单。这样外层一次 give 才真正释放锁，内层 give 只是退掉嵌套。

![队列环形缓冲：A–H 依次入队，写指针越过末尾后回绕到 0，memcpy 按整项写入](/figures/rtos-04-queue.svg)

### 三、发送三分支与 queueOVERWRITE 的硬约束

`xQueueGenericSend` 的主循环先判断有没有空间：

```c
if( ( pxQueue->uxMessagesWaiting < pxQueue->uxLength )
    || ( xCopyPosition == queueOVERWRITE ) )
{
    xYieldRequired = prvCopyDataToQueue( pxQueue, pvItemToQueue, xCopyPosition );
    /* 接收名单非空就叫醒第一个 */
    ...
    return pdPASS;
}
else
{
    if( xTicksToWait == 0 )
    {
        return errQUEUE_FULL;       /* 不阻塞的失败出口 */
    }
    /* 有超时：挂进 xTasksWaitingToSend */
}
```

第一条分支是「有空位」：拷贝、`uxMessagesWaiting++`、叫醒接收名单上的第一个。叫醒之后要不要让出，不由这里直接决定，而是看 `xTaskRemoveFromEventList` 的返回值，下一节展开。

第二条分支是「覆盖写」：`queueOVERWRITE` 让条件直接成立，即使队列已满也进入拷贝。`xQueueOverwrite` 宏固定传 `timeout=0` 与 `queueOVERWRITE`，所以它永不阻塞，返回值只有 `pdPASS`。它适合「只要最新值」的心跳、状态广播，不适合「一条都不能丢」的命令流。

`queueOVERWRITE` 的长度约束是硬约束：`queue.c:952` 与 `:1170` 都有

```c
configASSERT( !( ( xCopyPosition == queueOVERWRITE ) && ( pxQueue->uxLength != 1 ) ) );
```

为什么必须是 1？覆盖写走的不是 `pcWriteTo`，而是 `pcReadFrom`。长度为 1 时读写指针重合，覆盖的就是唯一槽位，语义干净。长度大于 1 时，覆盖写会改掉队头位置并把读指针前移，队列里其它项的先进先出顺序和 `uxMessagesWaiting` 的计数就对不上了。上游干脆把「长度必须为 1」写成断言。

这里有一个 lab 相关的细节：`mcu/code/rtos/01-freertos-lab/FreeRTOSConfig.h` 没有定义 `configASSERT`，FreeRTOS 默认把它展开成空语句。也就是说，这条断言在本 lab 的编译里不产生运行时检查。违反约束不会保证当场停机，可能只是静默写坏队列。到了打开断言的工程，它才会 halt。API 契约仍然是硬约束，只是 lab 没装护栏。

第三条分支是「满且非覆盖」：`timeout=0` 立即返回 `errQUEUE_FULL`；`timeout>0` 则挂进 `xTasksWaitingToSend`。挂起前要先 `vTaskSuspendAll()` 并锁队列，防止在「判断满」和「挂名单」之间被 ISR 插入；挂好后解锁并恢复调度器。空位出现时，接收侧会把发送名单上的第一个移到就绪表；超时则由 tick 把任务从延迟名单唤醒，返回 `errQUEUE_FULL`。

接收侧是镜像：`xQueueReceive` 有数据就拷出并叫醒发送名单；空且超时为 0 返回 `errQUEUE_EMPTY`；空且超时为正则挂进 `xTasksWaitingToReceive`。`xQueuePeek` 只拷出不移除。`uxQueueMessagesWaiting` 与 `uxQueueSpacesAvailable` 读的就是 `uxMessagesWaiting` 与 `uxLength - uxMessagesWaiting`，适合在调试时看水位。

### 四、叫号：按优先级，不按到达顺序

等待名单是按优先级排序的链表，不是先进先出队列。任务挂上去时，它的 TCB 里那个 `xEventListItem` 的值被写成

```c
xItemValue = configMAX_PRIORITIES - uxPriority;
```

链表按 `xItemValue` 升序插入，于是数值越小（优先级越高）越靠前，`listGET_OWNER_OF_HEAD_ENTRY` 取到的就是最高优先级的等待者。`vListInsert` 的插入循环用的是 `<=`：

```c
for( pxIterator = ( ListItem_t * ) &( pxList->xListEnd );
     pxIterator->pxNext->xItemValue <= xValueOfInsertion;
     pxIterator = pxIterator->pxNext )
{
    /* 等于时继续往后走 */
}
```

等值时继续往后，所以同优先级的新来者排在已有同优先级项之后。结果就是：不同优先级按优先级叫号，同优先级按到达顺序叫号。这是「RTOS 的公平是重要的先来」这句话的源码依据，不是口号。

`xTaskRemoveFromEventList` 摘下名单头部，把任务从事件项上移除、放进就绪表，然后比较：

```c
if( pxUnblockedTCB->uxPriority > pxCurrentTCB->uxPriority )
{
    xReturn = pdTRUE;       /* 叫醒的比我高 */
    xYieldPendings[ 0 ] = pdTRUE;
}
else
{
    xReturn = pdFALSE;
}
```

发送路径拿到 `pdTRUE` 后执行 `queueYIELD_IF_USING_PREEMPTION()`；在 `configUSE_PREEMPTION=1` 的 lab 里，它展开成 `portYIELD_WITHIN_API()`，把 PendSV 挂起。真正切上下文要等临界区退出、PendSV 得到执行，不是 `memcpy` 一结束就换栈。PendSV 的现场保存与恢复见 [第 23 章](./23-context-switch-porting.md)。

同优先级不触发 `pdTRUE`，因为比较是严格的 `>`。发送者继续跑，被叫醒的同级任务在就绪表里等下一次调度。这也解释了为什么「发送完立刻打印」有时会看到消费者还没跑：不是没叫醒，是没到切换点。

如果调度器被挂起，`xTaskRemoveFromEventList` 不会把任务直接放进就绪表，而是挂到 `xPendingReadyList`；等 `xTaskResumeAll` 再搬。队列的 `cRxLock`/`cTxLock` 欠账机制也在这个窗口里生效。看源码时不要把「叫醒」等同于「立刻运行」，中间隔着调度器和 PendSV。

### 五、FromISR：只延迟让出

中断里不能调用普通发送/接收，原因不是「函数更长」，而是两件事做不到：中断上下文没有任务可以挂起，中断中途也不能切换上下文。FromISR 版本把这两件事都改成「记账，出去再结算」。

`xQueueGenericSendFromISR` 没有 timeout 参数。队列满时它不等待，直接返回 `errQUEUE_FULL`，丢不丢由调用者决定。队列空时 `xQueueReceiveFromISR` 返回 `pdFALSE`。两者都在 `taskENTER_CRITICAL_FROM_ISR` 里改计数和等待名单，不调用任何可能阻塞的函数。

如果这次操作叫醒了更高优先级的任务，FromISR 不当场 `portYIELD`，而是把输出参数写成 `pdTRUE`：

```c
if( xTaskRemoveFromEventList( &( pxQueue->xTasksWaitingToReceive ) ) != pdFALSE )
{
    if( pxHigherPriorityTaskWoken != NULL )
    {
        *pxHigherPriorityTaskWoken = pdTRUE;
    }
}
```

调用者在中断末尾统一结算一次：

```c
void EXTI0_IRQHandler( void )
{
    BaseType_t xHigherPriorityTaskWoken = pdFALSE;
    uint8_t key = 0x01;

    xQueueSendFromISR( xKeyQueue, &key, &xHigherPriorityTaskWoken );
    portYIELD_FROM_ISR( xHigherPriorityTaskWoken );  /* 只在这里切 */
}
```

`portYIELD_FROM_ISR` 在 Cortex-M4F 上检查参数，为真才挂 PendSV；为假什么也不做。一个中断里可以调多个 FromISR API，每个都往同一个 flag 上写，最后只调用一次 `portYIELD_FROM_ISR`。不要在中途调用，也不要在每个 API 后面各调一次。

ISR 优先级约束与 ch10 的 NVIC 配置是同一件事。lab 的 `configPRIO_BITS=4`，`configMAX_SYSCALL_INTERRUPT_PRIORITY` 定义为 `5 << (8 - 4)`，即原始值 `0x50`。逻辑优先级 5 对应原始 `0x50`，逻辑 0–4 对应 `0x00`–`0x40`。能调 FromISR 的中断，逻辑优先级必须 **≥ 5**（数值不小于 0x50）；逻辑 0–4 的中断高于 syscall 阈值，内核临界区盖不住它，调 FromISR 会让链表在临界区外被改。`portASSERT_IF_INTERRUPT_PRIORITY_INVALID()` 在调试版会抓这种调用，但前提是 `configASSERT` 有定义。异常进入、BASEPRI 与 NVIC 优先级分组见 [v1 第 10 章](../v1-drivers/10-interrupts-nvic-exti.md)。

`xQueueSendFromISR`/`xQueueReceiveFromISR` 之外，`xSemaphoreGiveFromISR` 也走同一条延迟让出路径；任务通知的 `vTaskNotifyGiveFromISR`、`xTaskNotifyFromISR` 也一样带 `pxHigherPriorityTaskWoken`。规则统一：ISR 只记账，出口只切一次。

### 六、宏血缘：信号量与互斥锁都是队列

`semphr.h` 里没有独立的信号量实现，只有三行宏：

```c
#define xSemaphoreTake( xSemaphore, xBlockTime ) \
    xQueueSemaphoreTake( ( xSemaphore ), ( xBlockTime ) )

#define xSemaphoreGive( xSemaphore ) \
    xQueueGenericSend( ( QueueHandle_t ) ( xSemaphore ), NULL, \
                       semGIVE_BLOCK_TIME, queueSEND_TO_BACK )

#define xSemaphoreCreateMutex() \
    xQueueCreateMutex( queueQUEUE_TYPE_MUTEX )
```

`xSemaphoreGive` 的等待时间是 `semGIVE_BLOCK_TIME`，值为 0。它发的是 `NULL`，项大小为 0，所以不拷贝数据，只把计数加一。计数已到 `uxLength` 时，它不阻塞，直接返回失败。这就是「give 永不阻塞」的源码依据：不是信号量特殊，而是宏把 timeout 写死成 0 了。

`xSemaphoreTake` 展开成 `xQueueSemaphoreTake`。后者先断言 `uxItemSize == 0`，再读 `uxMessagesWaiting`：大于 0 就减一返回；如果 `uxQueueType == NULL`（互斥锁），这条成功路径还会把 `xMutexHolder` 记为当前任务（`pvTaskIncrementMutexHeldCount()`），二值信号量不做这一步。计数等于 0 且是互斥锁时，先做优先级继承，然后挂进接收名单。二值信号量的 `pcHead` 非 NULL，不会走继承分支。

创建侧的初始计数：

| API | 底层 | `uxLength` | 初始 `uxMessagesWaiting` | 说明 |
| --- | --- | --- | --- | --- |
| `xSemaphoreCreateBinary` | `xQueueGenericCreate(1, 0, ...)` | 1 | 0 | 创建后为空，第一次 take 前要先 give |
| `xSemaphoreCreateCounting(max, initial)` | `xQueueCreateCountingSemaphore` | `max` | `initial` | 资源池；initial 可以是 0 到 max |
| `xSemaphoreCreateMutex` | `xQueueCreateMutex(MUTEX)` | 1 | 1 | 出生即 give 一次，钥匙挂在门上 |
| `xSemaphoreCreateRecursiveMutex` | `xQueueCreateMutex(RECURSIVE_MUTEX)` | 1 | 1 | 同一结构，多一个递归层数 |

互斥锁出生即 give，是 `prvInitialiseMutex` 的最后一行：

```c
pxNewQueue->u.xSemaphore.xMutexHolder = NULL;
pxNewQueue->uxQueueType = queueQUEUE_IS_MUTEX;   /* pcHead = NULL */
pxNewQueue->u.xSemaphore.uxRecursiveCallCount = 0;
( void ) xQueueGenericSend( pxNewQueue, NULL, 0, queueSEND_TO_BACK );
```

二值信号量不送这一次，所以初始计数是 0；计数信号量按 `initial` 送。三种人生在创建函数里就分开了，后面的 take/give 只是沿着各自的计数与持有者字段走。

递归互斥锁的 API 是 `xSemaphoreTakeRecursive` / `xSemaphoreGiveRecursive`，不是普通的 take/give。拿锁时如果持有者就是当前任务，`uxRecursiveCallCount++` 后直接返回，不再进队列；给锁时先减层数，只有减到 0 才真正走 `xQueueGenericSend`。lab 的 `FreeRTOSConfig.h` 没有打开 `configUSE_RECURSIVE_MUTEXES`，默认为 0，所以递归互斥锁的宏在这个工程里不编译。要用就显式打开，并且 take/give 成对。

互斥锁只能由持有者 give。`xTaskPriorityDisinherit` 里有一条 `configASSERT( pxTCB == pxCurrentTCB )`，非持有者调用会在断言版直接停住；断言关掉时，计数可能被改对，但持有者指针和继承状态已经不可信。二值信号量没有这个限制，因为它的模型里根本没有「持有者」。

### 七、优先级继承：三步、回落与 ISR 禁区

H 任务 take 互斥锁失败时，`xQueueSemaphoreTake` 在挂起自己之前做一次继承：

```c
if( pxQueue->uxQueueType == queueQUEUE_IS_MUTEX )
{
    xInheritanceOccurred = xTaskPriorityInherit( pxQueue->u.xSemaphore.xMutexHolder );
}
vTaskPlaceOnEventList( &( pxQueue->xTasksWaitingToReceive ), xTicksToWait );
```

`xTaskPriorityInherit` 的三步是：

1. **判**：持有者的当前优先级是否低于等待者。不低于就不继承。
2. **改**：把持有者的 `uxPriority` 改成等待者的优先级，同时把它的 `xEventListItem` 值改成新优先级的编码，保证它在事件名单里也按新身份排序。
3. **搬**：如果持有者正在就绪表里，先按旧优先级把它摘出来，重置旧优先级的就绪位图，再按新优先级挂进就绪表。如果它正在阻塞，只改数，等它醒来时自然按新优先级入表。

三步里最容易漏的是「搬」。只改 `uxPriority` 不搬链表，调度器仍然在旧优先级的链表和位图里找它，改了也轮不到它跑，继承等于没做。第 22 章的位图与就绪表在这里直接接上。

还锁时的回落是镜像。`prvCopyDataToQueue` 的互斥锁分支调用 `xTaskPriorityDisinherit(holder)`。后者先 `uxMutexesHeld--`，只有减到 0 才回落：

```c
if( pxTCB->uxPriority != pxTCB->uxBasePriority )
{
    if( pxTCB->uxMutexesHeld == 0 )
    {
        uxListRemove( &( pxTCB->xStateListItem ) );
        pxTCB->uxPriority = pxTCB->uxBasePriority;
        listSET_LIST_ITEM_VALUE( ..., configMAX_PRIORITIES - pxTCB->uxPriority );
        prvAddTaskToReadyList( pxTCB );
        xReturn = pdTRUE;   /* 需要重新调度 */
    }
}
```

`uxBasePriority` 是任务创建时的原始优先级，不会因为继承而丢失。一个任务同时持有两把互斥锁、两把都被继承时，还第一把不回落，还最后一把才回落。否则它会在还锁的瞬间被中优先级任务插进来，另一把锁的等待者又陷入反转。

二值信号量没有这套逻辑。它的 `pcHead` 非 NULL，`xQueueSemaphoreTake` 不会进继承分支，也没有 `uxBasePriority` 可回落。拿它保护共享数据，H 等、L 持、M 插队的反转会完整上演。选型上，互斥锁是「带继承的钥匙」，二值信号量是「发令枪」，两者不能互换。

ISR 里 take 互斥锁是禁止用法，不是「不推荐」。`xSemaphoreTakeFromISR` 展开成 `xQueueReceiveFromISR(..., NULL, ...)`。后者只检查计数、拷数据（项大小为 0 时什么也不拷）、叫醒发送者，整个函数体不读 `uxQueueType`、不写 `xMutexHolder`、不调用 `xTaskPriorityInherit`。于是：

- 中断「取到」锁时，计数减了，但持有者仍是 NULL 或上一个任务，所有权没有登记。
- 后续任务还锁时，`xTaskPriorityDisinherit` 拿不到正确的持有者，继承与回落都失效。
- 若中断想阻塞等锁，它根本没有任务上下文，只能立即返回失败。

ISR 能安全使用的是二值/计数信号量的 give 和任务通知；互斥锁的 take 与 give 都不属于 ISR 可用路径。把这条纪律和第 10 章的 NVIC 约束放在一起记：中断里只做短的、非阻塞的、可记账的操作。

![信号量与互斥锁动画：计数信号量像剩余车位，互斥锁像有主的钥匙；L 持锁、H 抢锁失败后继承发生](/anim/semaphore-mutex.svg)

![优先级反转与继承：H 等锁、M 抢占、L 持锁；继承后 L 临时升到 H 级](/figures/rtos-freertos-05-sem-mutex.svg)

### 八、E04：反转的理论账

E04 的 FreeRTOS 剧本在 `mcu/code/rtos/01-freertos-lab/main.c` 的场景 6，优先级 1/2/3；RT-Thread 版优先级是 22/21/20，数值越小越高。两版都用 `cpu_work_ms(3000)` 让 L 真占 CPU，M 用 `busy_until(4500)` 连续忙等，不用 `vTaskDelay`。这一点是实验成立的前提：如果 L 在临界区里 `vTaskDelay(3000)`，它是睡着的，M 抢不抢都不影响它 3 秒后醒来，两版 H 的等待会一样长，什么也证明不了。

理论时间线：

| 时刻（ms） | 二值信号量版 | 互斥锁版 |
| --- | --- | --- |
| 0 | L 拿锁，开始 3000 ms CPU 工作 | 同左 |
| 500 | M 醒来抢占 L，L 已做 500 ms | 同左 |
| 1000 | H 要锁被挡；L 仍是优先级 1，M 继续跑 | H 要锁被挡；L 继承到优先级 3，抢回 CPU |
| 3500 | M 还在跑，L 一动不动 | L 做完剩余 2500 ms 并还锁，H 拿到锁，等待约 2500 ms |
| 4500 | M 跑完，L 才继续剩余 2500 ms | M 跑完 |
| 7000 | L 还锁，H 拿到锁，等待约 6000 ms | — |

二值版的 6000 ms 来自 H 从 1000 等到 7000；互斥版的 2500 ms 来自 L 在 1000 时还剩 2500 ms 的工作。F5 原文写「L 才轮到跑满 3000ms」，按字面会把 L 的完成时刻算到 7500 ms，H 的等待算成 6500 ms，与同一份 E04 时间线的「剩余 2500 ms」矛盾。正确说法是：L 在 0–500 ms 已经做了 500 ms，被 M 抢占后停住，恢复时只需再做 2500 ms。

继承只把 H 的等待封顶在「L 把临界区做完」，并不让 H 免等。L 的临界区越长，H 的下限越高；继承不防死锁，优先级天花板才防。这是 E04 思考题的第一问，也是「继承是安全带，不是油门」的准确含义。

RT-Thread 版同剧本：L=22、M=21、H=20，0 最高。H 等锁时，`_rt_mutex_take` 把 owner 的当前优先级从 22 抬到 20；`list_thread` 里能看到 L 的 priority 列变成 20，还锁后回到 22。R2 写的「1 变 3」方向与数值都错：RT-Thread 是数值小者优先，lab 的基数是 22/21/20，不是 1/2/3。继承的数值是 22→20，回落是 20→22。

E04 的证据状态：`hardware_status: pending`，实测记录表全空。上面两个数都是剧本参数推出的理论值，不是串口日志。完整的上板测量、逻辑分析仪打点与双 OS 日志并排，归第 40 章。本章只把账算对，不替 E04 宣布实测。

![优先级反转与继承动画：三泳道时间线，二值版 H 被 M 间接阻塞，互斥版 L 被抬级后 M 插不进](/anim/priority-inversion.svg)

![E04 理论时间线（非实测）：二值版 H 等约 6000 ms，互斥版约 2500 ms，L 在 500 ms 已做 500 ms、剩余 2500 ms](/images/labs/e04-timeline.svg)

### 九、通知、事件组、软件定时器：三条更轻的路

**任务通知**把「等」缩到 TCB 里。每个任务有两个数组（`tasks.c:419-420`）：

```c
volatile uint32_t ulNotifiedValue[ configTASK_NOTIFICATION_ARRAY_ENTRIES ];
volatile uint8_t  ucNotifyState[ configTASK_NOTIFICATION_ARRAY_ENTRIES ];
```

lab 的 `configTASK_NOTIFICATION_ARRAY_ENTRIES=1`，所以每个任务只有一个通知槽。`xTaskNotifyGive(x)` 把目标任务的 `ulNotifiedValue[0]` 加一，属于计数语义；`xTaskNotify(x, v, eSetValueWithOverwrite)` 直接覆盖，属于覆盖语义；`eSetValueWithoutOverwrite` 在旧值还没被取走时返回 `pdFAIL`；`eSetBits` 按位或。接收侧 `ulTaskNotifyTake(xClearCountOnExit, timeout)` 在计数非零时返回，`pdTRUE` 把计数清零，`pdFALSE` 只减一。

通知快的原因很具体：没有队列对象、没有 memcpy、没有额外的等待链表项，发送就是写目标 TCB 的两个字段。但它只适合一对一：通知的目标必须是一个确定的任务，不能多播，也不能像队列那样缓存任意长度的数据。`configTASK_NOTIFICATION_ARRAY_ENTRIES` 大于 1 只是给同一个任务多加几个槽，不是多生产者队列。

通知到底快多少？来源中的具体百分比/倍数没有版本、配置与引用，本章不采用。只保留定性判断：少了对象、拷贝与链表操作，通常更快；幅度依配置，取决于队列深度、发送发生在任务还是 ISR、当时是否触发调度。要写数字，就在同一块板上用同一版内核做基准，把配置与测量方法一起写出来。

**事件组**是位公告栏。`EventBits_t` 就是 `TickType_t`，但高 8 位被内核的控制位占用，可用位数随 tick 宽度变：

| `configTICK_TYPE_WIDTH_IN_BITS` | `EventBits_t` 宽度 | 可用事件位 | 控制位掩码 |
| --- | --- | --- | --- |
| 16 | 16 | bit0–bit7（8 位） | `0xff00` |
| 32 | 32 | bit0–bit23（24 位） | `0xff000000` |
| 64 | 64 | bit0–bit55（56 位） | 高 8 位 |

lab 的 `configUSE_16_BIT_TICKS=0`（`FreeRTOSConfig.h:42`），`TickType_t` 是 32 位，所以事件组是 24 位，不是「32 位随便用」。`xEventGroupWaitBits(group, mask, clearOnExit, waitForAllBits, timeout)` 的 `waitForAllBits=pdFALSE` 是 ANY，只要掩码里任一位满足就醒；`pdTRUE` 是 ALL，掩码里所有位都满足才醒。

清位不是「先醒者独占」。`xEventGroupSetBits` 把整个等待名单走一遍，所有满足条件的任务都唤醒；带 `clearOnExit` 的等待者把各自等的位并进 `uxBitsToClear`，名单走完后统一执行一次 `uxEventBits &= ~uxBitsToClear`（`event_groups.c:614`、`:637`）。同一次 SetBits 里，所有满足条件的等待者都能看到置位；清位发生在他们都被唤醒之后。若想让下一批任务也看到这些位，就不要开 `clearOnExit`，或者用 `xEventGroupClearBits` 显式清。

**软件定时器**只有一个守护任务。`xTimerCreate` 创建一个 `Timer_t`，`xTimerStart` 把命令送进定时器命令队列，守护任务 `prvTimerTask` 取出命令、按到期时间排序、到期后调用回调。所有定时器的回调都在这个守护任务里**串行**执行，所以回调里不能 `vTaskDelay`、不能等队列/信号量；一堵，所有定时器一起停摆。回调里适合置标志、发通知、写不带阻塞的队列、翻 GPIO。tick 时基与 SysTick 的中断配置见 [v1 第 11 章](../v1-drivers/11-systick-timebase-rtc.md)。

三者选型：

| 需求 | 首选 | 理由 |
| --- | --- | --- |
| 一对一、只传信号或 ≤32 位最新值 | 通知 | 无队列对象、无拷贝；覆盖/计数两种语义 |
| 一对一、要攒欠账 | 通知 `xTaskNotifyGive` + `ulTaskNotifyTake(pdTRUE/FALSE)` | 计数语义 |
| 多对一、一对多、任意长度数据 | 队列 | 有存储区与两条等待名单 |
| 多个条件都齐才继续 | 事件组 | ANY/ALL，24 位（lab） |
| 周期杂务、回调不阻塞 | 软件定时器 | 单守护任务，省每任务栈 |
| 共享数据排他 | 互斥锁 | 带持有者与继承 |
| 事件发生通知 | 二值信号量 | 无数据，只发令 |

### 十、RAM 账：248 B 与 1312 B

先算队列。深度 10、项 16 B：

```text
数据区       10 × 16 = 160 B
Queue_t                80 B   （本源 probe 声称值，未复核）
heap_4 块头             8 B   （每笔 malloc 的抽头）
总计                  248 B
```

160 B 是算术，确定。80 B 与 8 B 是「本仓库 probe 声称值」，标来源说法(未复核)，不是跨工程常数。`Queue_t` 的大小会随 `configUSE_TRACE_FACILITY`、`configUSE_QUEUE_SETS`、静态分配等配置变化；换一个工程，80 可能变成别的数。248 B 是在「Queue_t=80、heap_4 块头 8 B」这两个前提下推出的文档推导值，不是所有 FreeRTOS 工程的队列开销。

再算定时器。F6 的 probe 声称（未复核）：

```text
configUSE_TIMERS=1，固定那笔：
  守护任务 TCB      96 B
  守护任务栈       1032 B   （256 字 × 4，含 heap_4 抽头）
  命令队列          184 B
  ─────────────────────
  合计             1312 B   （一个定时器都没建就要付）

每建一个定时器     56 B
每开一个最小任务  616 B   （栈 128 字 + TCB）
(16384 - 1312) ÷ 56 = 269.14 → 269
```

269 是「整个 16 KiB 池只塞定时器」的上界，不是预算。真实工程还要给任务、栈、队列留空间。1312 B 是固定首付，只用一两个定时器时最不划算；每个定时器 56 B 才是边际成本。另有约 60 B 落在 `.bss`（两条到期表、四个指针、`xLastTime`），不受 `configTOTAL_HEAP_SIZE` 管，这一项同样是来源说法(未复核)。

### 十一、RT-Thread IPC 对照：一副骨架，五处改名

RT-Thread v5.3.0 的 IPC 也是「对象头 + 计数/存储 + 挂起名单」，但字段名与方向都和 FreeRTOS 不同：

| 维度 | FreeRTOS V11.1.0 | RT-Thread v5.3.0 |
| --- | --- | --- |
| 公共对象 | `QueueDefinition` | `rt_ipc_object { rt_object parent; rt_list_t suspend_thread; }` |
| 等待名单 | `xTasksWaitingToSend` / `xTasksWaitingToReceive` | `suspend_thread`（邮箱/消息队列另有 `suspend_sender_thread`） |
| 唤醒 | `xTaskRemoveFromEventList` | `rt_susp_list_dequeue` / `rt_susp_list_resume_all` |
| 优先级方向 | 数值大者高 | 0 最高，数值小者高 |
| 互斥持有者 | `u.xSemaphore.xMutexHolder` | `rt_mutex.owner` |
| 互斥优先级字段 | `uxBasePriority` | `rt_mutex.priority`（等待者中数值最小的优先级，0xFF 表示无） |
| 继承 | `xTaskPriorityInherit` | `_thread_update_priority`（由 `_rt_mutex_take` 调用） |
| 邮箱 | 无独立类型，用项大小 4 的队列 | `rt_mailbox`，每格 `rt_ubase_t`，32 位平台 4 B |
| 消息队列 | `uxItemSize` 固定 | `msg_size` 固定，每条带 `rt_mq_message` 头 |
| 事件 | 事件组，lab 24 位可用 | `rt_event`，32 位 `set` |

R2 里有几处名字与口径要按 v5.3.0 改写：

1. `rt_ipc_object` 的字段是 `suspend_thread`，不是 `suspend_list`。`suspend_list` 不是 v5.3.0 的字段，也不是旧版的正式字段名（v3.1.5 与 v4.0.0 同样用 `suspend_thread`）；`rtdef.h:985-990` 的原文是 `rt_list_t suspend_thread;`。
2. `rt_ipc_resume` 这个函数不存在。`rt_ipc_list_resume` 也不是 v5.3.0 的定义，只在 `ipc.c:157` 与 `:195` 的注释里作为对比出现。真正执行挂起的是 `rt_thread_suspend_to_list`（内部用 `rt_susp_list_enqueue` 按 PRIO/FIFO 插入），恢复是 `rt_susp_list_dequeue` 与 `rt_susp_list_resume_all`（`ipc.c:105`、`:168`）。`rt_ipc_list_suspend` 同样不是可调用函数。
3. `rt_mutex` 没有 `original_priority` 字段；它是旧版互斥锁结构里的字段，v5.x 已移除。`rtdef.h:1023-1035` 的字段是 `owner`、`hold`、`priority`、`ceiling_priority`、`taken_list`。`priority` 是「等待这把锁的线程里数值最小的优先级」，不是持有者的原优先级；原优先级在 TCB 的 `init_priority` 里，还锁时 `_check_and_update_prio` 用 `_thread_get_mutex_priority` 在 `init_priority` 与手上各 mutex 的等待优先级之间取最小，只有一个锁时就回到 `init_priority`。
4. RT-Thread 是 0 最高。E04 的 lab 数是 L=22、M=21、H=20；继承发生时 owner 的当前优先级从 22 抬到 20，还锁后回到 22。`1 变 3` 既把方向写反，也不是 lab 的数值。
5. 邮箱 4 B 的说法正确：`rt_mb_create` 按 `size * sizeof(rt_ubase_t)` 申请，32 位平台 `rt_ubase_t` 是 4 B。消息队列不是「变长队列」：`msg_size` 在创建时固定，`rt_mq_send` 在 `size > mq->msg_size` 时直接返回 `-RT_ERROR`（`ipc.c:3432`），每条消息还要带 `struct rt_mq_message` 头（至少 `next` 指针 4 B，v5.3.0 还有 `length` 字段）。所以「size × msg_size」低估了消息队列的 RAM，至少要再加每条的头。
6. FreeRTOS 的队列也是固定 `uxItemSize`，不是「变长队列」。R2 把 FreeRTOS 队列说成变长、把 RT-Thread 消息队列说成变长，两处都要改。要传不同长度的数据，通用做法是固定槽宽 + 长度字段，或者传指针，而不是让内核队列本身变长。

`rt_ipc_object` 的骨架确实统一了信号量、互斥量、事件集、邮箱与消息队列的「等」：接收方的等待挂到 `suspend_thread`；邮箱与消息队列的发送方另用 `suspend_sender_thread`（独立发送者名单）。差别只在「等什么、醒来怎么判断」。但名字与字段必须按 v5.3.0 写：`suspend_list` 不是 v5.3.0 的字段；`original_priority` 是旧版互斥锁结构里的字段、v5.x 已移除，也不能当 v5.3.0 的源码讲。

## 测量与证据

本章的读数分四类，逐条标在表里。没有上板，就没有「实测记录」。

| 取证项 | 来路 | 读数或结论 | 性质 |
| --- | --- | --- | --- |
| `QueueDefinition` 字段与 `uxQueueType` 别名 | `queue.c:65-66,103-136`；F4:53-73,88 | `uxQueueType` 是 `pcHead` 宏，`queueQUEUE_IS_MUTEX` 是 NULL | 文档推导 |
| 信号量的 `pcHead` 指向自身 | `queue.c:578-583` | 项大小为 0 时不能留 NULL，否则会被当成互斥锁 | 文档推导 |
| 整项 memcpy 与指针回绕 | `queue.c:2420-2425`；F4:85-111 | 单条数据不跨尾拆分；`pcTail` 是尾后标记 | 文档推导 |
| 发送三分支与 overwrite 断言 | `queue.c:952,967,1170`；F4:119-146 | 长度必须为 1；满且超时 0 返回 `errQUEUE_FULL` | 文档推导 |
| lab 未定义 `configASSERT` | `FreeRTOSConfig.h`；`FreeRTOS.h:367-372` | 断言在本 lab 展开为空，overwrite 长度约束无运行时检查 | 文档推导 |
| 优先级叫号与让出 | `tasks.c:5243,5341,5396,5405,7579`；`list.c:192`；F4:148-152 | 名单按优先级；同优先级 FIFO；更高则返回 `pdTRUE` 并置 `xYieldPendings[0]` | 文档推导 |
| FromISR 语义与优先级阈值 | F4:154-173；`FreeRTOSConfig.h:62`；ch10 | 不阻塞；`errQUEUE_FULL`；逻辑 ≥5 / 原始 0x50 | 文档推导 |
| 宏血缘与互斥锁出生 | `semphr.h:298,460,735,868`；`queue.c:614-634`；F5:61-131 | take/give/create 都是队列；出生 give 一次 | 文档推导 |
| 继承三步与回落 | `queue.c:1788,2405-2411`；`tasks.c:6580,6683`；F5:104-131 | 判→改→搬；最后一把锁才回落 `uxBasePriority`；二值无继承 | 文档推导 |
| ISR take 互斥锁 | `semphr.h:675`；`queue.c:2035-2132`；`tasks.c:6696` | 不写 holder、不继承；禁止用法 | 文档推导 |
| 通知 TCB 字段 | `tasks.c:419-420`；`task.h:2611,2984,3177`；F6:71-84 | `ulNotifiedValue[]`/`ucNotifyState[]`；计数/覆盖两种语义 | 文档推导 |
| 事件组位宽条件 | `event_groups.h:42-52`；`event_groups.c:547,614,637`；`FreeRTOSConfig.h:42` | 8/24/56 位；lab 24 位；汇总清位 | 文档推导 |
| 软件定时器守护任务 | F6:111-123,201-210,274 | 单守护任务、回调串行、禁阻塞 | 来源说法(未复核) |
| `Queue_t=80` 与 heap_4 8 B 头 | F6:201-210,274 | 本源 probe 声称值，不是跨工程常数 | 来源说法(未复核) |
| 队列 248 B | 上两行 + 算术 | 160 + 80 + 8 = 248 B；前提是 80/8 成立 | 文档推导 |
| 定时器 1312/56/616/269 | F6:201-210,274 | 固定 1312、每定时器 56、最小任务 616、上界 269 | 来源说法(未复核) |
| F6 五幕模拟 | F6:136-152,274 | Σ<1 有界、≥1 发散补拍 | 来源说法(未复核) |
| E04 理论 6000/2500 | E04:78-93；F5:135-145 | L 已做 500 ms，恢复只需剩余 2500 ms | 文档推导 |
| E04 实测与 lab 场景 | E04:3-9,101-108；`main.c` 场景 2/3/4/6 | 实测表全空，`hardware_status: pending`；串口日志未采集 | 未实测 |
| 通知速度的定性结论 | F6:88 | 只写「更快，幅度依配置，需同板基准」；来源中的具体百分比/倍数没有版本、配置与引用，本章不采用 | 来源说法(未复核) |
| RT-Thread 名字与字段 | `rtdef.h:985-990,1023-1035`；`ipc.c:105,168,3432` | `suspend_thread`；无 `original_priority`；定长 `msg_size` | 文档推导 |

待做台架：

| 日期 | 平台/板卡 | 实验 | 原始结果 | 结论 |
| --- | --- | --- | --- | --- |
| 待实测 | F407 lab | 场景 2 通知计数：生产 50 ms → 10 ms，看 `took` | | |
| 待实测 | F407 lab | 场景 3 事件组：ANY/ALL 与汇总清位 | | |
| 待实测 | F407 lab | 场景 4 定时器：slow cb 50 ms → 200 ms，看 fast cb 迟到 | | |
| 待实测 | F407 lab | 场景 6 二值与互斥，记录 H 的 `waited` | | |
| 待实测 | F407 lab | RT-Thread E04：`list_thread` 看 L 的 22→20→22 | | |
| 待实测 | F407 lab | `nm`/map 看 `Queue_t` 与队列实际 RAM，核对 248 B | | |
| 待实测 | F407 lab | GDB `watch ulNotifiedValue[0]`，看通知到达与消费 | | |

行号对账口径：本章引用的本地 `mcu/...` 行号是主要锚点；GitHub 链接只给到 tag，不给具体行号，避免上游小版本移动后链接指错。`queue.c`、`tasks.c`、`semphr.h`、`event_groups.h` 的数字都按 V11.1.0 对过；RT-Thread 的 `ipc.c`、`rtdef.h` 按 v5.3.0 对过。若读者在别的版本上看到行号偏移，以函数名和语义为准，不要拿旧行号硬套。

## 失败分支

| 现象 | 最可能的原因 | 区分证据 | 下一动作 |
| --- | --- | --- | --- |
| 队列满后发送任务永久不跑 | `portMAX_DELAY` + 消费者不取 | `uxMessagesWaiting` 到顶、发送任务在 `xTasksWaitingToSend` | 改有限超时或加大深度 |
| `xQueueOverwrite` 后数据顺序乱了 | 队列长度大于 1 | 创建参数 `uxLength`；断言是否打开 | 长度改成 1，或换普通发送 |
| 队列里出现「半条数据」的错觉 | 误以为跨尾要分两段拷贝 | `prvCopyDataToQueue` 只有一次 memcpy | 按整项拷贝，检查自定义拷贝代码 |
| 中断里调 `xQueueSend` 死机或断言 | 用了非 FromISR 版本 | 调用点、ISR 优先级 | 换 `xQueueSendFromISR` |
| FromISR 唤醒后高优先级任务晚一拍 | 没传 flag 或没调 `portYIELD_FROM_ISR` | 中断末尾是否有一次结算 | 统一在出口 `portYIELD_FROM_ISR(flag)` |
| 逻辑优先级 0–4 的 ISR 调 FromISR 偶发死机 | 中断高于 syscall 阈值，临界区盖不住 | NVIC 优先级与 `0x50` | 降到逻辑 ≥5 |
| ISR 里 take 互斥锁，之后继承不生效 | `xQueueReceiveFromISR` 不写 holder | `xMutexHolder` 为 NULL 或旧值 | 移出 ISR；中断只 give 信号量/通知 |
| 二值信号量护共享数据，反转照旧 | 没有持有者与继承 | 创建宏是 Binary 还是 Mutex | 换 `xSemaphoreCreateMutex` |
| 递归互斥锁 take 两次后死锁/断言 | 用了 `xSemaphoreCreateMutex` 或普通 take/give | 创建宏与 take/give 宏 | 换 Recursive 版本并成对调用 |
| 通知丢事件 | 用了覆盖语义 | `xTaskNotify` 的 action 与 `ulNotifiedValue` | 要攒欠账改 `xTaskNotifyGive` |
| 等 bit24 永远等不到 | 事件组位宽条件，lab 只有 bit0–23 | `configUSE_16_BIT_TICKS` 与掩码 | 改用 bit0–23 |
| 定时器回调里 `vTaskDelay`，所有定时器停摆 | 守护任务被堵 | 其它定时器是否集体迟到 | 回调只发通知/置标志 |
| 以为软件定时器零 RAM | `configUSE_TIMERS=1` 固定 1312 B | map/heap 账 | 按固定首付预算 |
| RT-Thread 找不到 `original_priority` | 字段名与模型记错 | `rtdef.h` 的 `rt_mutex` | 用 `owner/hold/priority/ceiling_priority/taken_list` |
| RT-Thread 按「1 变 3」解释继承 | 方向与 lab 数值都错 | `list_thread` 的 22/21/20 | 记 0 最高，22→20→22 |
| E04 二值版把 H 等待算成 6500 ms | 把 L 的剩余工作当成 3000 ms | 时间线 500 ms 已做 | 剩余 2500 ms，等待 6000 ms |
| E04 两版等待一样长 | L 的临界区写成 `vTaskDelay`，睡着不占 CPU | L 是否用 `cpu_work_ms` | 改真占 CPU 的忙等 |

## 离开检查

1. `QueueDefinition` 的三种人生靠哪几个字段区分？`uxQueueType` 是什么？
<details><summary>参考答案</summary>`uxItemSize` 是否为 0、`uxQueueType`（即 `pcHead`）是否为 NULL、`uxMessagesWaiting` 当前计数。队列 `uxItemSize>0`；二值/计数信号量 `uxItemSize=0` 且 `pcHead` 非 NULL；互斥锁 `uxItemSize=0` 且 `pcHead=NULL`。`uxQueueType` 不是结构体成员，是 `#define uxQueueType pcHead`。</details>

2. 数据项写到尾端时会不会拆两段？源码怎么回绕？
<details><summary>参考答案</summary>不会。`prvCopyDataToQueue` 对整项做一次 memcpy 到 `pcWriteTo`，然后 `pcWriteTo += uxItemSize`；只有越过 `pcTail` 才把指针赋回 `pcHead`。`pcTail` 是尾后标记，不存数据。回绕的是指针，不是数据。</details>

3. `prvCopyDataToQueue` 的 `uxItemSize=0` 分支做哪两件事？顺序为什么不能反？
<details><summary>参考答案</summary>互斥锁时先 `xTaskPriorityDisinherit(xMutexHolder)`，再 `xMutexHolder = NULL`；非互斥锁信号量只加计数。顺序反了会先丢掉旧持有者指针，去继承函数找不到该回落优先级的 TCB。</details>

4. 发送三分支的条件、动作与返回？
<details><summary>参考答案</summary>有空位：拷贝并叫醒接收者，`pdPASS`；`queueOVERWRITE`：覆盖唯一槽位，`pdPASS`；满且非覆盖、超时 0：不拷贝，`errQUEUE_FULL`；满且非覆盖、超时 >0：挂 `xTasksWaitingToSend`，有空位 `pdPASS`，超时 `errQUEUE_FULL`。</details>

5. `queueOVERWRITE` 的长度约束是什么？违反了会怎样？
<details><summary>参考答案</summary>上游 `configASSERT(uxLength==1)`（`queue.c:952`、`:1170`）。覆盖写走 `pcReadFrom`，长度为 1 时读写指针重合，才是唯一槽位；大于 1 会破坏 FIFO 顺序与计数。lab 没定义 `configASSERT`，断言展开为空，违反后可能静默写坏数据，不保证当场停机。</details>

6. 等待名单按什么排序？同优先级呢？唤醒后谁决定让出？
<details><summary>参考答案</summary>按 `configMAX_PRIORITIES - uxPriority` 升序，数值小的高优先级在前。同优先级因 `vListInsert` 的 `<=` 插到已有项之后，呈 FIFO。`xTaskRemoveFromEventList` 返回 `pdTRUE`（被叫醒者优先级严格高于当前任务）时，`queueYIELD_IF_USING_PREEMPTION` 挂 PendSV；同优先级不让出。</details>

7. FromISR 为什么不能阻塞？`pxHigherPriorityTaskWoken` 与 `portYIELD_FROM_ISR` 各做什么？
<details><summary>参考答案</summary>中断上下文没有任务可挂起，也不能在中途切上下文。FromISR 满/空直接返回错误；若叫醒更高优先级任务，就把输出参数写 `pdTRUE`。调用者在中断末尾用一次 `portYIELD_FROM_ISR(flag)` 决定是否挂 PendSV，让出时机合法且只切一次。</details>

8. 能调 FromISR 的中断优先级范围？逻辑 0–4 为什么不行？
<details><summary>参考答案</summary>逻辑优先级 ≥5，原始值 ≥0x50。lab 的 syscall 阈值是 `5 << 4 = 0x50`；逻辑 0–4 的中断高于阈值，内核临界区（BASEPRI）盖不住它，它调 FromISR 会在临界区外改链表，造成竞态。调试版由 `portASSERT_IF_INTERRUPT_PRIORITY_INVALID` 抓，前提是 `configASSERT` 有定义。</details>

9. `xSemaphoreGive` 展开成什么？为什么它不阻塞？
<details><summary>参考答案</summary>`xQueueGenericSend(queue, NULL, semGIVE_BLOCK_TIME, queueSEND_TO_BACK)`，`semGIVE_BLOCK_TIME=0`。项大小为 0，不拷贝数据，只把计数加一；计数已满时立即返回失败，不进入等待名单。所以「give 不阻塞」是宏把 timeout 写死为 0 的结果。</details>

10. 互斥锁出生为什么要 give 一次？二值/计数/互斥的初始计数？
<details><summary>参考答案</summary>让互斥锁创建后计数为 1，第一个 take 者直接拿到，语义是「钥匙挂在门上」。二值信号量初始 0（事件未发生）；计数信号量初始 `initial`（资源池）；互斥锁初始 1。</details>

11. 继承三步是什么？还锁时怎么回落？二值为什么没有？
<details><summary>参考答案</summary>判（持有者优先级更低）、改（`uxPriority` 改成等待者优先级并更新事件项值）、搬（从旧就绪链表摘出、重置位图、按新优先级挂入）。还锁时 `xTaskPriorityDisinherit` 在最后一把锁释放后把 `uxPriority` 恢复为 `uxBasePriority` 并搬回就绪表。二值信号量 `pcHead` 非 NULL，`xQueueSemaphoreTake` 不进继承分支，也没有 holder/base priority。</details>

12. ISR 里 take 互斥锁会怎样？为什么禁止？
<details><summary>参考答案</summary>`xSemaphoreTakeFromISR` → `xQueueReceiveFromISR`，后者不读 `uxQueueType`、不写 `xMutexHolder`、不调继承。计数可能减了，但所有权没登记，后续还锁时继承与回落都失效。ISR 没有任务上下文，不能阻塞；互斥锁的 take/give 都不属于 ISR 可用路径。</details>

13. 通知写 TCB 哪两个字段？计数/覆盖分别用哪个 API？
<details><summary>参考答案</summary>`ulNotifiedValue[]` 与 `ucNotifyState[]`（`tasks.c:419-420`），长度由 `configTASK_NOTIFICATION_ARRAY_ENTRIES` 决定，lab 为 1。计数语义用 `xTaskNotifyGive`（eIncrement）；覆盖用 `xTaskNotify(..., eSetValueWithOverwrite)`；`eSetValueWithoutOverwrite` 在旧值未取走时失败。</details>

14. 事件组在 lab 有多少位？位宽由什么决定？SetBits 怎么清位？
<details><summary>参考答案</summary>lab 是 24 位（bit0–23）。`EventBits_t` 等于 `TickType_t`，高 8 位是控制位；16 位 tick 剩 8 位、32 位剩 24 位、64 位剩 56 位。`xEventGroupSetBits` 走完整个等待名单，所有满足条件的等待者都唤醒，把 `clearOnExit` 的位并进 `uxBitsToClear`，最后统一清一次。</details>

15. 软件定时器为什么不能阻塞？固定 RAM 与每定时器 RAM 各多少？269 是什么？
<details><summary>参考答案</summary>所有回调都在唯一的守护任务里串行执行；回调阻塞就是守护任务阻塞，所有定时器停摆。F6 probe 声称固定 1312 B（一个定时器都没建）、每定时器 56 B；269 是 `(16384-1312)/56` 的上界，不是预算。</details>

16. 通知比队列快在哪？为什么只写定性结论？
<details><summary>参考答案</summary>快在没有队列对象、没有 memcpy、没有额外等待链表项，发送就是写目标 TCB 的字段。但幅度依配置，取决于队列深度、任务/ISR 上下文、是否触发调度；来源中的具体百分比/倍数没有版本、配置与引用，本章不采用，只写「更快，幅度依配置，需同板基准」。要数字就同板同配置做基准。</details>

17. RT-Thread 的 `rt_ipc_object` 字段、互斥字段、邮箱与消息队列的真实口径？
<details><summary>参考答案</summary>`rt_ipc_object` 是 `parent` + `suspend_thread`，不是 `suspend_list`。`rt_mutex` 有 `owner/hold/priority/ceiling_priority/taken_list`，没有 `original_priority`；`priority` 是等待者中数值最小的优先级，0xFF 表示无。邮箱每格 4 B（`rt_ubase_t`）；消息队列 `msg_size` 固定，`rt_mq_send` 在 `size > msg_size` 时返回 `-RT_ERROR`，每条另有 `rt_mq_message` 头，不是变长队列。</details>

18. E04 的 6000/2500 怎么算？为什么 6500 是错的？继承数值 22→20 怎么来？
<details><summary>参考答案</summary>二值版：H 在 1000 ms 等，L 被 M 压到 4500 ms 才恢复，已做 500 ms，剩余 2500 ms，7000 ms 还锁，H 等 6000 ms。互斥版：L 在 1000 ms 继承到 H 级，做完剩余 2500 ms，3500 ms 还锁，H 等 2500 ms。6500 错在把 L 恢复后的工作当成 3000 ms，忽略了 0–500 ms 已做的 500 ms。RT-Thread 是 0 最高，lab 为 L=22/M=21/H=20，H 等待时 owner 从 22 抬到 20，还锁回 22。</details>

19. 本章哪些读数是来源说法、哪些是未实测？
<details><summary>参考答案</summary>来源说法(未复核)：F6 的五幕模拟、定时器 1312/56/616/269、`Queue_t=80` 与 heap_4 8 B 头、60 B `.bss`、通知速度的具体百分比/倍数（本章不采用）。未实测：E04 全部实测表与 lab 场景 2/3/4/6 的串口日志。文档推导：源码字段、memcpy/回绕、发送分支、叫号、继承、事件组位宽、RT-Thread 字段与 248 B 的算术。</details>

<QuizBank chapter="f4-queue" />

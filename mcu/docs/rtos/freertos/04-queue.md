---
title: F4 队列：传送带的源码解剖
status: done
difficulty: 3
minutes: 45
---

# F4 队列：环形存储 + 两个阻塞列表

> 🎯 队列是 RTOS 里最忙碌的传送带：数据从这头进那头出，满了送件人排队，空了取件人排队。FreeRTOS 用一个结构体装下全部：一段环形存储 + 两张"排队名单"。本章把 `xQueueGenericSend` 拆开看，你会发现**信号量、互斥锁、队列全是这一个结构体的不同用法**。

## 本章精髓

1. **Queue_t 五要素**：`pcHead/pcWriteTo/pcReadFrom` 环形存储 + `xTasksWaitingToSend/xTasksWaitingToReceive` 两张阻塞名单，一切队列行为都是这五样的组合。
2. **发送是"拷贝"不是"传指针"**：`memcpy` 按值进环形区，简单安全，代价是大数据拷贝慢（大对象传指针，这是设计决策不是偷懒）。
3. **阻塞有公平也有超时**：等待者按**优先级**挂名单，唤醒时高优先级先拿；超时到点自动复活带错误码，永不死等（除非你坚持 `portMAX_DELAY`）。

- **能理解**：为什么写满阻塞和读空阻塞是**两张**名单而不是一张；为什么 `xQueueOverwrite` 适合"最新值"场景；为什么 FromISR 版本不能阻塞。
- **能用**：串口中断→队列→任务的标准管道；会算队列 RAM 账（深度×项大小）。

## 先修

- [F3 调度](03-scheduler.md)、[S7 USART](../../stm32/07-usart.md)。

## 先跑起来（10 分钟 quick win）

按键中断里 `xQueueSendFromISR` 发按键值，任务里 `xQueueReceive(..., portMAX_DELAY)` 收到就翻灯，第一个"中断→任务"标准管道，睡觉不耗 CPU。

按键不来的时候，收件任务在干嘛：原地空转数羊，还是干脆睡死让出 CPU？先押个睡法，押完看它睡在队列的哪张名单上。

## 动画：传值不传址的传送带

生产者拷贝进 tail、消费者从 head 取走，head/tail 指针此消彼长；取空就睡、放满也睡——**睡觉不耗 CPU** 是 RTOS 通信和 while 轮询的本质区别。

![队列传送动画](/anim/queue-passing.svg)

## 小节结构

| 小节 | 内容 | 四件套 |
|---|---|---|
| 一、结构体五要素 | QueueDefinition 逐字段（含 cRxLock/cTxLock 锁计数） | 库解析 |
| 二、拷贝入队 | `prvCopyDataToQueue`：memcpy+指针回绕，互斥锁彩蛋 | 库解析 |
| 三、发送三分支 | 空位/覆盖/阻塞——`xQueueGenericSend` 走查 | 库解析 |
| 四、唤醒与公平 | `xTaskRemoveFromEventList`：按优先级叫号 | 代码分析 |
| 五、FromISR 家族 | 为什么不能阻塞；`pxHigherPriorityTaskWoken` 延迟让出 | 代码分析 |
| 六、RAM 账与设计 | 深度×项大小；水位查询；队列集预告 | 配置 |

## 一、结构体五要素：一个结构体三种人生

queue.c（V11.1.0）的 `QueueDefinition`，关键字段原文：

```c
typedef struct QueueDefinition
{
    int8_t * pcHead;     /* 存储区起点 */
    int8_t * pcWriteTo;  /* 下一个可写位置 */

    union
    {
        QueuePointers_t xQueue;     /* 当队列用时:pcReadFrom/pcTail */
        SemaphoreData_t xSemaphore; /* 当信号量/互斥锁用时:持有者等 */
    } u;

    List_t xTasksWaitingToSend;     /* 写满阻塞的送件人名单(按优先级排) */
    List_t xTasksWaitingToReceive;  /* 读空阻塞的取件人名单(按优先级排) */

    volatile UBaseType_t uxMessagesWaiting; /* 当前存货数 */
    UBaseType_t uxLength;                   /* 容量:能装几项(不是几字节) */
    UBaseType_t uxItemSize;                 /* 每项几字节 */

    volatile int8_t cRxLock;  /* 队列锁定期间被取走的项数 */
    volatile int8_t cTxLock;  /* 队列锁定期间被塞进的项数 */
} xQUEUE;
```

读三遍那个 `union`：**队列和信号量共享同一个结构体**，信号量就是 `uxItemSize=0` 的队列（没有数据只有计数），互斥锁再多带一个持有者指针。所以 F5 的信号量 API 全是 `xQueueGenericSend/Receive` 的马甲。`uxItemSize=0` 这个分支马上在下一节现身。

![FreeRTOS 队列环形缓冲：入队 memcpy 到队尾、出队 memcpy 到局部变量；指针回绕，传值不传址](/figures/rtos-04-queue.svg)

## 二、拷贝入队：memcpy + 指针回绕

真正搬数据的 `prvCopyDataToQueue`（节选）：

```c
if( pxQueue->uxItemSize == ( UBaseType_t ) 0 )
{
    /* 信号量/互斥锁:没有数据可拷 */
    if( pxQueue->uxQueueType == queueQUEUE_IS_MUTEX )
    {
        xReturn = xTaskPriorityDisinherit( pxQueue->u.xSemaphore.xMutexHolder ); /* 还锁→去继承 */
        pxQueue->u.xSemaphore.xMutexHolder = NULL;
    }
}
else if( xPosition == queueSEND_TO_BACK )
{
    ( void ) memcpy( ( void * ) pxQueue->pcWriteTo, pvItemToQueue, ( size_t ) pxQueue->uxItemSize );
    pxQueue->pcWriteTo += pxQueue->uxItemSize;
    if( pxQueue->pcWriteTo >= pxQueue->u.xQueue.pcTail )
    {
        pxQueue->pcWriteTo = pxQueue->pcHead;   /* 到尾回绕:环形 */
    }
}
else  /* queueSEND_TO_FRONT */
{
    ( void ) memcpy( ( void * ) pxQueue->u.xQueue.pcReadFrom, pvItemToQueue, ... );
    pxQueue->u.xQueue.pcReadFrom -= pxQueue->uxItemSize;
    ...
}
```

三行看清全部本质：**memcpy 按值拷贝、写指针前进、到尾回绕**。`uxItemSize==0` 分支就是互斥锁"还钥匙"的现场，还锁时顺手做**优先级去继承**（F5 的重头戏，先记住这行 `xTaskPriorityDisinherit`）。

> **【注】** "按值拷贝"是 FreeRTOS 的标志性取舍：小数据（结构体、传感器读数）直接拷，安全无脑；大对象（帧缓冲）改为**传指针**：队列里装的是地址，所有权归你自己管。拷指针时记得指向的生命周期必须长过消费时刻，栈变量地址是头号翻车素材。

## 三、发送三分支：`xQueueGenericSend` 走查

主循环的判别式（节选）：

```c
taskENTER_CRITICAL();
{
    if( ( pxQueue->uxMessagesWaiting < pxQueue->uxLength ) || ( xCopyPosition == queueOVERWRITE ) )
    {
        xYieldRequired = prvCopyDataToQueue( pxQueue, pvItemToQueue, xCopyPosition );

        /* 有取件人在等? 立刻叫醒 */
        if( listLIST_IS_EMPTY( &( pxQueue->xTasksWaitingToReceive ) ) == pdFALSE )
        {
            if( xTaskRemoveFromEventList( &( pxQueue->xTasksWaitingToReceive ) ) != pdFALSE )
            {
                queueYIELD_IF_USING_PREEMPTION();  /* 叫醒的比我优先级高→当场让出 */
            }
        }
        ...
        taskEXIT_CRITICAL();
        return pdPASS;
    }
    else  /* 满了且不是覆盖写 */
    {
        vTaskPlaceOnEventList( &( pxQueue->xTasksWaitingToSend ), xTicksToWait ); /* 送件人排队 */
        ...
    }
}
```

三分支一目了然：**有空位→拷贝+叫醒取件人；覆盖写→照样拷（`queueOVERWRITE` 直接放行，长度 1 的队列专用，"只要最新值"场景如心跳/状态）；满了→自己挂上 `xTasksWaitingToSend` 名单睡觉**。注意让出发生在**叫醒的取件人比自己优先级高**时，公平就藏在这行 `xTaskRemoveFromEventList` 的返回值里。

## 四、唤醒与公平：按优先级叫号

`xTaskRemoveFromEventList` 从名单上摘下的是**优先级最高**的等待者（名单按优先级排序插入，F3 的 `vListInsert` 老熟人），而不是来得最早的。设计哲学：**RTOS 的公平是"重要的先来"，不是"先来的先来"**。被叫醒的任务从事件名单搬家到就绪表，如果它优先级压过当前任务，立刻 YIELD，数据还没到手的任务就已经被调度去取数据了，这就是"叫醒"与"交接"一气呵成的流水线。

接收侧 `xQueueGenericReceive` 是它的镜像：有货→拷出+叫醒送件人；没货→挂 `xTasksWaitingToReceive`。对称结构，读源码时对照看事半功倍。

## 五、FromISR 家族：中断里的单行桥

中断里为什么不能调普通版？两个死穴：**不能阻塞**（中断没有"任务"可挂）、**不能当场切上下文**（中断里 YIELD 时机非法）。FromISR 版的做法：

1. 永远不等：满了直接返回 `errQUEUE_FULL`，丢不丢由你决定；
2. 让出延迟：把"要不要换任务"写进 `pxHigherPriorityTaskWoken` 输出参数，由你在中断末尾调 `portYIELD_FROM_ISR(xHigherPriorityTaskWoken)` 统一结算。

标准姿势：

```c
void EXTI0_IRQHandler( void )
{
    BaseType_t xHigherPriorityTaskWoken = pdFALSE;
    uint8_t key = 0x01;
    xQueueSendFromISR( xKeyQueue, &key, &xHigherPriorityTaskWoken );
    portYIELD_FROM_ISR( xHigherPriorityTaskWoken );  /* 需要才切,一次结清 */
}
```

> **【注】** 中断优先级必须 ≥ `configMAX_SYSCALL_INTERRUPT_PRIORITY`（数值上 ≥，Cortex-M 数值越大优先级越低，F3 常见坑清单的崩溃第二名），否则 FromISR 在临界区里"裸奔"，list.c 注释里那份崩溃清单就是给你准备的。

## 六、RAM 账与设计：传送带要多长

- **RAM = uxLength × uxItemSize + 结构体本身**，深度 10、项 16 字节的队列 ≈ 160B+结构体，开队列前先算账；
- **深度设计**：按"生产-消费速度差×最长延迟"估，再用水位 API `uxQueueSpacesAvailable` / `uxQueueMessagesWaiting` 实测修正：**先估后测**，别拍脑袋；
- **队列集**（Queue Set）：一个任务同时等多路来源时用 `xQueueSelectFromSet`，F6 事件组章会对比选型。

## 记忆锚点

::: tip 一句话记住
**队列=环形仓库+两张候客名单；发送按值 memcpy，满则睡空则睡；ISR 走专用通道延迟让出；信号量就是 uxItemSize=0 的队列。**
:::

**延伸**：队列的生产-消费模式与 DMA 环形缓冲（[S8](../../stm32/08-dma.md)）同构；1:1 通知场景可用任务通知（[F6](06-notify-event-timer.md)）替代队列，更轻量。

## 实物实验

- quick win 按键管道 + 串口打印队列水位：连按 20 次看 `uxQueueMessagesWaiting` 涨到满；
- 翻车实验（选做）：中断里故意调普通版 `xQueueSend`，观察断言/HardFault，再读 list.c 崩溃清单对号。

## 常见坑

- **大结构体直接拷**：队列深度 5 × 结构体 1KB = 5KB RAM 蒸发，传指针；
- **传了栈变量地址**：函数返回后指针成野指针，所有权纪律；
- **FromISR 忘了结算让出**：高优先级任务明明醒了却跑到下一拍才执行，延迟一拍在电机控制里就是事故；
- **`portMAX_DELAY` 当默认值用**：队列一满/一空任务永久失踪，调试先给有限超时，上线再放宽；
- **中断优先级撞 configMAX_SYSCALL**：见第五节注。

## 短自测

1. 为什么说"信号量就是队列"？源码依据是什么？
<details><summary>参考答案</summary>QueueDefinition 里用 union 复用存储：uxItemSize=0 时 prvCopyDataToQueue 不做 memcpy 只维护计数/持有者：信号量=无数据的队列，互斥锁再带持有者指针和继承逻辑。F5 会看到 xSemaphoreGive 直接展开成 xQueueGenericSend。</details>

2. `xQueueOverwrite` 和普通发送在"队列满"时行为有何不同？各自适合什么场景？
<details><summary>参考答案</summary>普通发送：满了→调用者阻塞挂 xTasksWaitingToSend;Overwrite:直接覆盖队首旧值永远成功。长度 1+Overwrite 适合"只要最新值"(心跳/状态广播),普通阻塞适合"一个都不能丢"(命令/数据流)。</details>

3. FromISR 版本为什么不能阻塞？`pxHigherPriorityTaskWoken` 解决了什么？
<details><summary>参考答案</summary>中断上下文没有"任务"可挂起，也不能在中断中途切换上下文。pxHigherPriorityTaskWoken 把"是否需要切换"作为输出参数带回，由代码在中断末尾调 portYIELD_FROM_ISR 统一结算，让出时机合法且只切一次。</details>

4. 发送方拷贝完数据后，为什么可能立刻 YIELD？依据什么判断？
<details><summary>参考答案</summary>若 xTasksWaitingToReceive 非空，xTaskRemoveFromEventList 叫醒等待者；该函数在被叫醒者优先级高于当前任务时返回 pdTRUE,于是 queueYIELD_IF_USING_PREEMPTION 当场让出，数据一到，最高优先级的消费者立刻接手。</details>

<QuizBank chapter="f4-queue" />

## 对照表：本章概念 → 源码落点

| 概念 | 落点（FreeRTOS-Kernel V11.1.0） |
|---|---|
| 五要素结构体 | `queue.c` QueueDefinition（union 队列/信号量双生） |
| 按值拷贝+回绕 | `queue.c` prvCopyDataToQueue（memcpy/pcWriteTo 回绕/互斥锁去继承彩蛋） |
| 发送三分支 | `queue.c` xQueueGenericSend（空位/覆盖/阻塞+唤醒取件人） |
| 优先级叫号 | `tasks.c` xTaskRemoveFromEventList（名单按优先级排序） |
| ISR 通道 | `queue.c` xQueueSendFromISR（不阻塞+pxHigherPriorityTaskWoken） |

## 你做到了

- 队列从黑盒 API 变成"环形存储+两张名单"的可推理机器；
- 信号量/互斥锁的血缘被提前揭穿，F5 只剩继承逻辑可讲；
- ISR→任务管道成为你的通信肌肉记忆。

它真睡了，睡在名单上：按键不来，收件任务挂进队列的阻塞名单，CPU 转身去喂别的任务。轮询是站着等，阻塞是躺下睡，这一觉就是 RTOS 通信和裸机轮询的分界线。

<div class="achievement">
✅ 下一站：<a href="05-sem-mutex.html">F5 信号量与互斥锁</a>：计数牌与钥匙，以及优先级继承怎么把 H 从死亡螺旋里捞出来。
</div>

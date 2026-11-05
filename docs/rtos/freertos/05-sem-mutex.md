---
title: F5 信号量与互斥量：优先级反转事件
status: done
difficulty: 2
minutes: 40
---

# F5 信号量与互斥量：复现 RTOS 最著名的灵异事件

> 🎯 1997 年火星探路者在火星上神秘重启——元凶是地球上的经典 bug：**优先级反转**。高优先级任务等资源、资源在低优先级手里、中优先级任务疯狂插队。本章在你的霸天虎上复现它，再用互斥量的"优先级继承"破解它——源码级别，逐行看清。

## 本章精髓

1. **二值信号量管"同步"，计数信号量管"几个"**：车位牌（一手交一手接）与车位池（N 个资源），它们**不保护数据**，只是发令枪。
2. **互斥量是"带继承的钥匙"**：低优先级持锁被高优先级等时，**临时继承高优先级**（`xTaskPriorityInherit`），中优先级插不进来；还锁时 `xTaskPriorityDisinherit` 回落。
3. **血缘关系**：信号量/互斥锁全是 F4 那个队列结构体的马甲：`xSemaphoreGive` 展开就是 `xQueueGenericSend`，互斥锁 = 长度 1、项大小 0 的队列 + 持有者指针 + 继承逻辑。

- **能理解**：为什么互斥锁创建时要先"白送一次"；继承发生在哪一行代码；为什么二值信号量**不能**当互斥锁用（无继承）。
- **能用**：E04 复现反转→换互斥锁破解；多锁场景定死获取顺序。

## 先修

- [F4 队列](04-queue.md)（信号量基于队列实现）、[F3 调度](03-scheduler.md)。

## 先跑起来（10 分钟 quick win）

[E04 优先级反转实验](../../lab/e04-priority-inversion.md)：把 `DEMO_SCENE=6` 烧上板子，串口日志就打出三任务执行序："H 等锁，M 狂跑，L 没机会还锁"的死亡螺旋。注意 E04 的"实测记录"那张表至今是空的，所以这一集里那两个数都还不来自板子（见第四节末尾的注）。

死亡螺旋先看清，解药先押下：把二值信号量换成互斥量，M 还狂跑得起来吗？L 又靠什么突然腿快了？押完往下读，破解现场见真章。

## 动画：计数牌与钥匙

左边停车场计数（信号量管"几个"），右边厕所钥匙（互斥锁管"谁的"）。第四帧看**优先级继承**现场：L 持锁被 H 等，L 临时升到 H 的优先级快进快出。

![信号量与互斥锁动画](/anim/semaphore-mutex.svg)

## 动画：反转现场与继承救命

三条泳道看完整悬案：L 持锁 → H 抢锁阻塞 → M 把 L 挤下台（**反转**：H 实际垫底）→ 继承把 L 抬到 H 级 → 还锁回落，H 终于开跑。游标六拍走完，你就记住了"为什么互斥锁要带继承"。

![优先级反转与继承动画](/anim/priority-inversion.svg)

## 小节结构

| 小节 | 内容 | 四件套 |
|---|---|---|
| 一、宏的血缘 | semphr.h 三个宏展开：全是 queue.c 马甲 | 库解析 |
| 二、互斥锁出生证 | `prvInitialiseMutex`：为什么创建即"白送" | 库解析 |
| 三、继承逐行 | `xTaskPriorityInherit` 搬表现场 | 库解析 |
| 四、反转实验 | E04 三任务配置；≈6000/≈2500 那两个数是什么身份 | 代码分析 |
| 五、选型与纪律 | 四种选型；递归配对；多锁顺序 | 代码分析 |

## 一、宏的血缘：semphr.h 没有函数，只有马甲

马甲家族先看图：两大家族四件马甲，底座是同一个 Queue。

![信号量与互斥量马甲家族：信号量无继承、互斥有优先级继承，底座同为 Queue](/arch/sem-mutex.png)

semphr.h（V11.1.0）里最常用的三个 API，原文就是三行宏：

```c
#define semGIVE_BLOCK_TIME  ( ( TickType_t ) 0U )

#define xSemaphoreTake( xSemaphore, xBlockTime )  xQueueSemaphoreTake( ( xSemaphore ), ( xBlockTime ) )
#define xSemaphoreGive( xSemaphore )              xQueueGenericSend( ( QueueHandle_t ) ( xSemaphore ), NULL, semGIVE_BLOCK_TIME, queueSEND_TO_BACK )
#define xSemaphoreCreateMutex()                   xQueueCreateMutex( queueQUEUE_TYPE_MUTEX )
```

**give = 往队列发 NULL、不等、发队尾**，就是 F4 的 `xQueueGenericSend` 换件外套。所以"信号量是 uxItemSize=0 的队列"不是比喻，是编译后的事实：give 时 `prvCopyDataToQueue` 走 `uxItemSize==0` 分支，不拷数据只加计数。这也解释了为什么 give 永不阻塞（`semGIVE_BLOCK_TIME=0`）：发令枪不需要排队。

选型由此自然分化：

| 类型 | 管什么 | 初始计数 | 带继承 |
|---|---|---|---|
| 二值信号量 | 同步（一件事发生了） | 0（空） | 否 |
| 计数信号量 | 资源池（N 个同类资源） | N（满） | 否 |
| 互斥锁 | 共享数据排他访问 | 1（空着可用） | **是** |
| 递归互斥锁 | 同一任务嵌套加锁 | 1 | 是 |

![优先级反转与继承：高优先级任务等锁、中优先级任务抢占、持锁的低优先级任务临时继承高优先级](/figures/rtos-freertos-05-sem-mutex.svg)

## 二、互斥锁出生证：创建即"白送"一次

`xQueueCreateMutex`（queue.c）先建一个**长度 1、项大小 0** 的队列，再调 `prvInitialiseMutex`：

```c
static void prvInitialiseMutex( Queue_t * pxNewQueue )
{
    pxNewQueue->u.xSemaphore.xMutexHolder = NULL;        /* 尚无持有者 */
    pxNewQueue->uxQueueType = queueQUEUE_IS_MUTEX;
    pxNewQueue->u.xSemaphore.uxRecursiveCallCount = 0;   /* 递归计数归零 */

    /* Start with the semaphore in the expected state. */
    ( void ) xQueueGenericSend( pxNewQueue, NULL, ( TickType_t ) 0U, queueSEND_TO_BACK );
}
```

注意最后一行：**创建时立刻 give 一次**，互斥锁出生就"钥匙挂在门上"（计数=1，可用）。谁第一个 take 谁拿到。对照：二值信号量创建后是 0（事件发生前没牌可拿），计数信号量是 N。同一个 `xQueueGenericCreate`，初始计数不同，三种人生由此分开。

## 三、继承逐行：`xTaskPriorityInherit` 的搬表现场

H 任务 take 互斥锁失败、持有者 L 优先级比自己低时，`xQueueSemaphoreTake` 内部调 `xTaskPriorityInherit`（tasks.c 节选）：

```c
if( pxMutexHolderTCB->uxPriority < pxCurrentTCB->uxPriority )  /* 持锁者比我低才继承 */
{
    /* 事件列表项的值改成"新优先级"的编码,保证在事件名单里按新身份排序 */
    listSET_LIST_ITEM_VALUE( &( pxMutexHolderTCB->xEventListItem ),
        ( TickType_t ) configMAX_PRIORITIES - ( TickType_t ) pxCurrentTCB->uxPriority );

    /* 若持锁者在就绪表里:先摘出来 */
    if( listIS_CONTAINED_WITHIN( &( pxReadyTasksLists[ pxMutexHolderTCB->uxPriority ] ),
                                 &( pxMutexHolderTCB->xStateListItem ) ) != pdFALSE )
    {
        if( uxListRemove( &( pxMutexHolderTCB->xStateListItem ) ) == ( UBaseType_t ) 0 )
        {
            portRESET_READY_PRIORITY( pxMutexHolderTCB->uxPriority, uxTopReadyPriority );
        }
        pxMutexHolderTCB->uxPriority = pxCurrentTCB->uxPriority;  /* ★ 继承:升级 */
        prvAddTaskToReadyList( pxMutexHolderTCB );                /* 挂进新优先级的就绪表 */
    }
    else
    {
        pxMutexHolderTCB->uxPriority = pxCurrentTCB->uxPriority;  /* 阻塞中:只改数不搬表 */
    }
}
```

流程三步：**判（持锁者更低）→ 改（优先级=等待者的）→ 搬（从旧就绪链表摘出、挂进新链表）**。`portRESET_READY_PRIORITY` + `prvAddTaskToReadyList` 正是 F3 位图/速查器那套记账，升级后 L 立刻具备和 H 同级的调度地位，**M 再也插不进来**。还锁时走镜像路径 `xTaskPriorityDisinherit`（F4 第二节那行彩蛋）：优先级回落原值，若回落后低于新就绪任务，立刻让出。

> **【注】** 继承只解"中优先级插队"，不解"持锁者自己磨蹭"。临界区还是要快进快出：继承是安全带，不是油门。另外二值信号量**没有**这套逻辑：拿它保护共享数据，反转照样发生，这是选型错误最隐蔽的形态。

## 四、反转实验：E04 的死亡螺旋判读

三任务配置（`code/rtos/01-freertos-lab/main.c:309-358`，`DEMO_SCENE=6`，`USE_MUTEX` 编译期二选一把锁换成互斥量）：

| 任务 | 优先级 | 行为 |
|---|---|---|
| L | 1 | t=0 拿"锁"→ 临界区 `cpu_work_ms(3000)` → 还锁 → 长眠 |
| M | 2 | t=500ms 起 `busy_until(4500)`：不碰锁、不阻塞，连续占 CPU 到 t=4500ms |
| H | 3 | t=1000ms 要同一把"锁"，拿到后打印 `waited` |

台词全在 `waited` 这一个数上。二值信号量没有持有者，H 在 t=1000ms 就挂住了，可 CPU 归 M 一路霸占到 4500ms，L 才轮到跑满 3000ms，按剧本参数推出的 `waited ≈ 6000ms`。换互斥量，H 挂下的同一刻 L 被抬到 3 级，M 抢不动它，L 跑完 3000ms 就还锁，`waited ≈ 2500ms`。

> **【注】** 这两个数是**理论值，不是实测**。E04 文档里"实测记录"那张表到今天还是空的，谁在屏上把它们说成板子上串口打出来的毫秒，就是替 E04 撒谎。`code/rtos/05-sem-mutex/sim_invert.c` 跑出来的是同一对数，身份也只到**模型值**为止（日志判读细节见 [E04](../../lab/e04-priority-inversion.md)）。

## 五、选型与纪律：剩下的都是工程规矩

- **同步选二值**：ISR give → 任务 take 是标准范式（比队列轻，无数据）；
- **资源池选计数**：如"同时只允许 3 个连接"，创建计数=3；
- **共享数据选互斥**：带上继承保险；**递归互斥**用于同一任务嵌套调用（take 几次 give 几次，`uxRecursiveCallCount` 就是出生证里那个字段）；
- **多锁定序**：全系统约定统一的加锁顺序（如永远先 A 后 B），破坏者死锁，这是防死锁的**唯一**纪律，没有银弹；
- **临界区纪律**：不调用可能阻塞的 API、不做长计算，继承救不了磨蹭。

## 记忆锚点

::: tip 一句话记住
**同步二值、资源计数、保护互斥、嵌套递归；互斥锁出生带钥匙、被等就继承、还锁即回落；二值信号量没有继承，拿它护数据等于裸奔。**
:::

**延伸**：I2C/SPI 总线共享需互斥锁保护（[S11](../../stm32/11-i2c.md)、[S12](../../stm32/12-spi.md)）；简单同步场景可用任务通知（[F6](06-notify-event-timer.md)）替代信号量。

## 实物实验

- [E04 优先级反转实验](../../lab/e04-priority-inversion.md)：二值版死亡螺旋 + 互斥锁版起死回生，两份日志贴进实验报告；
- 进阶：把 L 的临界区从 `cpu_work_ms(3000)` 改小（如 200ms）再跑二值信号量版，反转窗口变窄但**依然存在**，理解"窗口大小≠有无"。

## 常见坑

- **二值信号量当互斥锁**：无继承，反转照常，选型第一坑；
- **take/give 不配对**：递归锁少 give 一次，其他任务永久等锁；
- **ISR 里 take 互斥锁**：`xSemaphoreTakeFromISR` 展开为 `xQueueReceiveFromISR`（semphr.h:675 → queue.c:2035），那条路上不写 `xMutexHolder`、不比 `uxQueueType`、也不调 `xTaskPriorityInherit`（`queue.c:2035-2132` 整个函数体里这三样各命中 0 处）：中断里就算"取到"也不会登记持有者，于是既没有继承也没有回落；所有权是任务之间才谈得成的事；
- **临界区里 vTaskDelay**：持锁睡觉，把继承机制变成全系统的瓶颈放大器；
- **多锁乱序**：A→B 与 B→A 两条路径并存，死锁迟早登门。

## 短自测

1. `xSemaphoreGive` 为什么不阻塞？从宏展开回答。
<details><summary>参考答案</summary>它展开为 xQueueGenericSend(队列， NULL, semGIVE_BLOCK_TIME, queueSEND_TO_BACK),而 semGIVE_BLOCK_TIME=0,等待时间为零，满了立刻返回错误，不存在挂起。</details>

2. 互斥锁创建时为什么要调一次 xQueueGenericSend？
<details><summary>参考答案</summary>让计数初始为 1="钥匙挂在门上",第一个 take 者直接拿到。二值信号量不送(初始 0=事件未发生),计数信号量送满 N 次，初始计数区分三种选型。</details>

3. `xTaskPriorityInherit` 的三步是什么？为什么必须"搬表"？
<details><summary>参考答案</summary>判(持锁者更低)→改(uxPriority=等待者优先级)→搬(从旧就绪链表摘除、portRESET 记账、挂进新链表)。不搬表则调度器仍在旧链表/旧位图位里找它，改了优先级也轮不到它跑，继承失效。</details>

4. 为什么二值信号量不能替代互斥锁保护共享数据？
<details><summary>参考答案</summary>二值信号量没有持有者与继承逻辑(xTaskPriorityInherit 只在互斥锁 take 失败路径被调用)。用它护数据时，H 等、L 持、M 插队，反转完整上演，`DEMO_SCENE=6` 那出不带 `USE_MUTEX=1` 的剧本就是演这件事的。</details>

## 对照表：本章概念 → 源码落点

| 概念 | 落点（FreeRTOS-Kernel V11.1.0） |
|---|---|
| 信号量=队列马甲 | `semphr.h` xSemaphoreGive/Take/CreateMutex 宏定义 |
| 互斥锁出生证 | `queue.c` xQueueCreateMutex → prvInitialiseMutex（创建即 give） |
| 继承搬表 | `tasks.c` xTaskPriorityInherit（判→改→搬三步） |
| 还锁回落 | `queue.c` prvCopyDataToQueue 互斥锁分支 → xTaskPriorityDisinherit |
| 反转实验 | 板子：[E04](../../lab/e04-priority-inversion.md)（`DEMO_SCENE=6`）＋动画 [priority-inversion.svg](/anim/priority-inversion.svg)；不要板子：`code/rtos/05-sem-mutex/probe.sh` 静态血缘＋`sim_invert.c` 反转模型 |

## 延伸阅读

优先级继承的理论与那次著名事故：

- **[\[D2\]](../../reference/bibliography.md#papers)** Sha, Rajkumar, Lehoczky 1990 — 优先级继承协议的原始论文，也证明了它**不防死锁**（优先级天花板才防）；`xSemaphoreCreateMutex` 继承逻辑的理论出处。
- **[\[D11\]](../../reference/bibliography.md#papers)** Reeves 1997 — 火星探路者优先级反转事故的 JPL 一手复盘，`configUSE_MUTEXES` 这一行的历史重量。
- **[\[D10\]](../../reference/bibliography.md#papers)** Dijkstra 1965 — 信号量的起点。

## 你做到了

- RTOS 最著名的灵异事件在你板子上复现并被你亲手破解；
- "信号量 vs 互斥锁"从背题变成"看宏展开就知道"；
- 继承机制三步刻进脑子，面试白板题变成默写题。

解药的名字叫继承：L 不是变强了，是临时借了 H 的优先级，M 从此插不进队，锁准时归还。优先级反转不是灵异，是调度器没被递过话；递上话，同一块板子立刻讲道理。

<div class="achievement">
✅ 下一站：<a href="06-notify-event-timer.html">F6 任务通知与事件组</a>：比队列更快的"直达电报"。
</div>

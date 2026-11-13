---
title: "内存管理"
platforms: [f407]
---

# 内存管理

`configTOTAL_HEAP_SIZE` 把 16 KiB 池子交给 heap_4 管。你问它「还剩多少」它能答，问它「最大还能一次分出多大」它得想了想才答得对——总空闲与最大连续块是两个数，前一个涨了后一个不一定涨。这一章把 heap_1 到 heap_5 的能力阶梯讲清，把 heap_4 的合并算法拆到源码行，把「碎片只能试探」升级成「可观测加试探兜底」，再对照 RT-Thread 的堆家族把两边的差异收进一张表。

证据先说清：本章没有新的上板读数。场景 5 的代码真实存在（`mcu/code/rtos/01-freertos-lab/main.c:249-264`），但仓库里没有落盘串口日志，实验表只给操作与预期；probe 量出的 TCB 88 B 与固定账 1312 B 是来源说法（未复核）；上游行号是文档核对，不是本地编译证据。能亲手跑的只有场景 5 本身。

> 版本口径：FreeRTOS 的 `heap_1.c`、`heap_2.c`、`heap_3.c`、`heap_4.c`、`heap_5.c` 与 `tasks.c` 行号按 FreeRTOS-Kernel V11.1.0 对账；RT-Thread 的堆文件清单与命令名按 v5.3.0 的 `src/` 树对账（调研取件为 master 分支，若版本间有出入以你手上的源码为准）。根书 F103 例程按 V11.3.2，行号不与本章混排。

## 本章罗盘

- **问题**：heap_1 为什么敢把 `vPortFree` 留在文件里却让它只能断言失败？heap_2 的空闲表按什么排序、为什么不合并？heap_3 为什么连 `xPortGetFreeHeapSize` 都没有？heap_4 释放一块内存时靠什么找到前邻块——「边界标记法」这个说法错在哪？分配为什么要按 8 B 对齐、每次分配暗收多少 overhead？总空闲与历史最低水位是两个什么问题、`vPortGetHeapStats` 又多给了什么？`xTaskCreateStatic` 的「不会失败」边界在哪，Idle/Timer 钩子真实签名是几个参数？`configCHECK_FOR_STACK_OVERFLOW=2` 检查什么、在哪一刻检查？heap_5 的区域表有什么调用顺序约束，CCM 能不能放 DMA 缓冲？16 KiB 池怎么算预算，TCB 到底按 88 B 还是 400 B？RT-Thread 的 `src/` 里到底有哪几件堆实现，`tlsf.c` 存不存在，slab 的「碎片免疫」过头在哪，`rt_mp` 的 O(1) 怎么来的，`RT_USING_HEAP` 关掉后固件长什么样，finsh 的堆监控命令真实名字是什么？
- **交付**：能按「能否释放、合并、多区」给五个 heap 各一句话定位；能走读 `prvInsertBlockIntoFreeList` 的三步合并，纠正「边界标记法」的说法，算出块头 8 B 的对齐账；能分清当前空闲与历史最低水位，知道 heap_4 能直读最大连续块而 heap_5 不能；能复述场景 5 的六步操作与每步预期，指出「总空闲够、最大连续块不够」的判定时刻；能写出三参数的 Idle/Timer 静态钩子，说清静态创建的真实失败条件；能写出 heap_5 的区域表并把 CCM 的 DMA 禁区说对；能用 88 B TCB 加 8 B 头算一笔 16 KiB 预算；能按真实源码讲 RT-Thread 的四件堆实现、TLSF 的选档方向、内存池的 O(1) 与零堆固件。
- **边界**：单平台 F407（Cortex-M4F、`ARM_CM4F`、heap 16 KiB、`configSUPPORT_DYNAMIC_ALLOCATION=1`、`configSUPPORT_STATIC_ALLOCATION=0`）。FreeRTOS 结论按 V11.1.0；引用行号时区分「FreeHeapSize」「MinimumEver」「HeapStats」三个函数的落点，不混排。RT-Thread 只按 v5.3.0 的 `src/` 文件清单与 finsh 命令名讲，TLSF 只作论文与软件包对照，不写成内核自带。本章不展开 Mallock/伙伴系统/Slab 的论文细节，不重教队列与任务创建的 RAM 账（[ch24](./24-queue-semaphore-notification.md) 已算过 248 B 与 269），不写 Flash/IAP（那是 [v1 第 17 章](../v1-drivers/17-flash-iap-ota.md) 的领地）。参数区与掉电保存只回链不展开。
- **依据锚点**：F7《heap_1 到 heap_5》（`mcu/docs/rtos/freertos/07-heap.md`）、R3《RT-Thread 内存管理》（`mcu/docs/rtos/rtthread/03-mem.md`）、测验 `f7-heap`。配置见 `mcu/code/rtos/01-freertos-lab/FreeRTOSConfig.h`（`:31`、`:36`），场景 5 见 `mcu/code/rtos/01-freertos-lab/main.c:249-264`，内存地图见 `mcu/code/rtos/01-freertos-lab/stm32f407xx.ld:5-7` 与 [v1 第 8 章](../v1-drivers/08-architecture-memory-clock.md)。上游对账：FreeRTOS-Kernel V11.1.0 的 [heap_1.c](https://github.com/FreeRTOS/FreeRTOS-Kernel/blob/V11.1.0/portable/MemMang/heap_1.c)、[heap_2.c](https://github.com/FreeRTOS/FreeRTOS-Kernel/blob/V11.1.0/portable/MemMang/heap_2.c)、[heap_3.c](https://github.com/FreeRTOS/FreeRTOS-Kernel/blob/V11.1.0/portable/MemMang/heap_3.c)、[heap_4.c](https://github.com/FreeRTOS/FreeRTOS-Kernel/blob/V11.1.0/portable/MemMang/heap_4.c)、[heap_5.c](https://github.com/FreeRTOS/FreeRTOS-Kernel/blob/V11.1.0/portable/MemMang/heap_5.c)、[tasks.c](https://github.com/FreeRTOS/FreeRTOS-Kernel/blob/V11.1.0/tasks.c)；RT-Thread v5.3.0 的 [mem.c](https://github.com/RT-Thread/rt-thread/blob/v5.3.0/src/mem.c)、[memheap.c](https://github.com/RT-Thread/rt-thread/blob/v5.3.0/src/memheap.c)、[slab.c](https://github.com/RT-Thread/rt-thread/blob/v5.3.0/src/slab.c)、[mempool.c](https://github.com/RT-Thread/rt-thread/blob/v5.3.0/src/mempool.c)。任务栈水位与 TCB 结构见 [第 22 章](./22-tasks-tcb-scheduler.md)；队列的 RAM 账见 [第 24 章](./24-queue-semaphore-notification.md)。

## 先做出来

不接板，先把两笔账算在纸上。第一笔决定你给 heap_4 留多大家底，第二笔决定你什么时候第一次见到「总空闲够、请求失败」。

### 1. 一笔 16 KiB 的账

lab 的堆是 `configTOTAL_HEAP_SIZE = 16 * 1024`（`FreeRTOSConfig.h:36`）。启动后的固定开销按 probe 说法是 1312 B——内核对象、调度器自用的队列与定时器对象都从这里出（未复核，见 [第 24 章](./24-queue-semaphore-notification.md) 的同源数字）。一个深度 10、项 16 B 的队列是 160 + 80 + 8 = 248 B：160 是数据区，80 是 `Queue_t` 本体，8 是 heap_4 的块头。两项都建完，池子还剩 16384 − 1312 − 248 ≈ 14.8 KiB。

`(16384 − 1312) / 56 ≈ 269` 是「每定时器 56 B」成立时的上界，不是预算——把它当预算，池子会在第 200 个定时器附近碎掉。预算的正确算法在「堆预算」一节。

### 2. 两个数：总空闲与最大连续块

场景 5 的动作顺序是 A、B、C 各分 1 KB，释放中间的 B，试着要一块 2 KB，失败；再释放 A，再要 2 KB，成功。纸上推演：

| 步骤 | 池子布局 | 总空闲 | 最大连续块 | 要 2 KB |
| --- | --- | --- | --- | --- |
| 分 A/B/C | `AAA BBB CCC | 空` | ≈13 KB | ≈13 KB | 能 |
| 释放 B | `AAA ... CCC | 空` | ≈14 KB | ≈13 KB | **不能** |
| 释放 A | `...... CCC | 空` | ≈15 KB | ≈14 KB（A+B 已并） | 能 |

释放 B 之后总空闲涨到 14 KB，但那 1 KB 洞被 A、C 夹在中间，最大连续块还是 13 KB——2 KB 请求失败。释放 A 后，A 的洞和 B 的洞在地址上相邻，heap_4 把它们并成 2 KB，请求成功。这两个数什么时候分道扬镳，场景 5 给的是最干净的例子。

heap_4 凭什么知道 A、B 该不该并？往下看合并算法。

## 五版能力阶梯

FreeRTOS 的内存分配不是五个开关，是一条能力阶梯——你放弃什么，换回什么：

| 版本 | 分配 | 释放 | 合并 | 统计 API | 适合 |
| --- | --- | --- | --- | --- | --- |
| heap_1 | 有 | 无（断言失败） | — | 当前空闲 | 只在初始化时分配的固件 |
| heap_2 | 有 | 有 | 无（best fit 不合并） | 当前空闲 | 短期演示，长期产品禁用 |
| heap_3 | 包 libc | 有 | 看 libc | 无 | 快速原型、与现有 malloc 生态对接 |
| heap_4 | 有 | 有 | 相邻合并 | 当前空闲 + 水位 + 堆统计 | **嵌入式默认答案** |
| heap_5 | 有 | 有 | 相邻合并（多区） | 当前空闲 + 水位 | SRAM+CCM 多区域 |

逐条说清来源，免得「我记得 heap_2 也挺好」：

- **heap_1**：`vPortFree` 还在文件里，函数体第一行就是 `configASSERT( pv == NULL )`（V11.1.0 `heap_1.c:130-136`）——释放任何非空指针都会断言。它换来的确定性是每次分配都从递增指针切下来，没有搜索、没有碎片，代价是永远拿不回来。
- **heap_2**：空闲链表**按大小排序**，分配取第一个够大的块（best fit，`heap_2.c:130-155`）。可释放，但释放的块只按大小插回去，从不看邻居——交替分配释放几轮，池子就碎成满地小洞。它也没有 `xPortGetMinimumEverFreeHeapSize`，换用它，引用水位 API 的代码直接链接失败。
- **heap_3**：`pvPortMalloc` 包 `malloc`、`vPortFree` 包 `free`（`heap_3.c:65`、`:89`）。线程安全交给 libc 的锁，尺寸交给 libc 的堆。它**没有任何 `xPortGet` 统计**——总量、水位、统计都没有，用它就别想监控堆。
- **heap_4**：空闲链表按**地址**排序，释放时相邻就合并。首次适配，代价可控，指标齐全，是大多数产品的落点。
- **heap_5**：heap_4 的算法搬进「区域表」里跑，堆不再是一整块连续内存。其余能力与 heap_4 相同。

选型不是「heap_4 永远对」。只在启动时分配、固件跑一辈子不动的产品，heap_1 的确定性最高；只有快速原型要接 libc 生态，heap_3 才进场。heap_4 是「既要释放又要可控」这个最常见组合的答案，不是唯一答案。

## heap_4 的账本：地址序、首次适配、相邻合并

先看动画建立直觉：链表按地址排，隔着已用块的两个洞拼不上，前后邻上的才焊得成一块；盯住「总空闲」和「最大连续块」两个数字——它们经常不一样大。

![heap_4 合并动画：A/B/C 逐块长出，释放 B 中间留洞总空闲涨但最大连续块不够，释放 A 后相邻合并成 2KB](/anim/heap4-coalesce.svg)

![heap_4 空闲链表：ucHeap 里已用块与空闲块交替，xFreeList 按地址排序，相邻空闲块合并，两个指标都从这条链表读](/arch/heap-free-list.png)

### 块头：每次分配的 8 B 暗税

heap_4 的块只有**头**没有**尾**：

```c
typedef struct BLOCK_LINK_STRUCT
{
    struct BLOCK_LINK_STRUCT * pxNextFreeBlock; /* 空闲时指向下一个空闲块 */
    size_t xBlockSize;                          /* 含头部自身的总大小 */
} BlockLink_t;
```

32 位指针加 4 B `size_t`，`BlockLink_t` 本体 8 B。对齐处理在 `xHeapStructSize`：

```c
static size_t xHeapStructSize =
    ( sizeof( BlockLink_t ) + ( ( size_t ) portBYTE_ALIGNMENT - 1U ) ) &
    ~( ( size_t ) portBYTE_ALIGNMENT_MASK );
```

`ARM_CM4F` 端口的 `portBYTE_ALIGNMENT` 是 8，公式把 8 B 结构体再按 8 对齐——结果就是 8。每笔分配的账目：8 B 头 + 用户要的字节 +（请求尺寸不满足 8 对齐时）少量对齐余量。第 22 章的 TCB 88 B、第 24 章的队列 248 B，都含这 8 B。

### 分配：首次适配

`pvPortMalloc` 从 `xStart` 开始沿空闲链表走，取**第一个**装得下的块（`heap_4.c:247` 附近）。块太大就切走要的部分，剩下的小尾巴留在链表里；正好装下就把整块摘走。首次适配快、实现短，代价是偏爱链表前端的低地址块——同尺寸请求反复来，低地址区先被切碎。这个倾向配合「相邻合并」，多数场景可接受；极端交替负载下它就是碎片来源之一。

### 释放：`prvInsertBlockIntoFreeList` 的三步

释放的核心（V11.1.0 `heap_4.c:492` 起）用三步把刚释放的块放回链表：

```c
/* 1. 按地址找插入位置：走链表直到下一块地址超过我 */
pxIterator = &xStart;
while ( pxIterator->pxNextFreeBlock < pxBlockToInsert ) { ... }

/* 2. 后邻：我（含头）的尾正好接到下一个空闲块的头 → 吞并它 */
pxNextBlock = ( uint8_t * ) pxBlockToInsert + pxBlockToInsert->xBlockSize;
if ( ( uint8_t * ) pxIterator->pxNextFreeBlock == pxNextBlock ) {
    pxBlockToInsert->xBlockSize += pxIterator->pxNextFreeBlock->xBlockSize;
    pxIterator->pxNextFreeBlock = pxIterator->pxNextFreeBlock->pxNextFreeBlock;
}

/* 3. 前邻：插入点（前一个空闲块）的尾正好接到我的头 → 被它吞并 */
pxPrevBlock = ( uint8_t * ) pxIterator + pxIterator->xBlockSize;
if ( ( uint8_t * ) pxPrevBlock == ( uint8_t * ) pxBlockToInsert ) {
    pxIterator->xBlockSize += pxBlockToInsert->xBlockSize;
} else {
    /* 谁也不挨着，正常插进链表 */
    pxBlockToInsert->pxNextFreeBlock = pxIterator->pxNextFreeBlock;
    pxIterator->pxNextFreeBlock = pxBlockToInsert;
}
```

三个要点，其中第三个是本章最容易被教错的：

1. **合并只有「地址相邻」这一种判据**。前邻块的尾地址正好等于我的起始地址，或我的尾地址正好等于后邻块的起始地址，才并。隔着一块已用内存的两个洞，永远各留各的——这就是碎片的物理来源。
2. **链表按地址升序**，所以插入点是按地址遍历找到的，合并判断只需要两次指针比较。
3. **heap_4 不是「边界标记法」**。边界标记法要求每块带 footer，靠「前块地址 + 前块大小」从当前块反推前邻块，前后两个方向 O(1) 探邻居。heap_4 只有 8 B 头、没有 footer，前邻块是靠**地址序空闲表遍历**找出来的——`pxIterator` 停在插入位置，它就是地址上最大的那个前空闲块。merge 是 O(n) 的，不是 O(1)。旧的 F7 章把这条写成「边界标记法」，术语用错，机制也对不上，别照搬。

对几 KB 到几十 KB 的嵌入式小堆，O(n) 遍历的绝对开销微不足道，换来的是 8 B 头的极简实现。这是工程取舍，不是理论缺陷。

![heap_4 空闲链表手绘图：按地址排序，释放时只有相邻空闲块才合并，不相邻的洞保留](/figures/rtos-freertos-07-heap.svg)

## 两个指标与一个被漏掉的读数

逐文件核对后的可用性（V11.1.0）：

| API | heap_1 | heap_2 | heap_3 | heap_4 | heap_5 |
| --- | --- | --- | --- | --- | --- |
| `xPortGetFreeHeapSize` | 有 `:149` | 有 `:334` | 无 | 有 `:407` | 有 `:435` |
| `xPortGetMinimumEverFreeHeapSize` | 无 | 无 | 无 | 有 `:413` | 有 `:441` |
| `vPortGetHeapStats` | 无 | 无 | 无 | 有 `:560` | 无 |

三个 API 回答三个不同的问题：

- **当前空闲**（`xPortGetFreeHeapSize`）：这一刻还剩多少。瞬时值，回收一块就涨，多分一块就跌。
- **历史最低水位**（`xPortGetMinimumEverFreeHeapSize`）：开机以来最紧张的时刻还剩多少。它回答「峰值压力有多大」，**不是碎片率**——碎片再严重，水位也可能好看，因为水位只看总量。
- **堆统计**（`vPortGetHeapStats`，仅 heap_4）：一次拿到分配/释放次数、当前空闲块数，还有 `xSizeOfLargestFreeBlockInBytes`（`heap_4.c:597`）——**最大连续块可以直读**。

第三行补上了旧资料常漏的一课：判断「碎没碎」不必只靠试探分配。heap_4 上读一次 stats，用「最大连续块 / 总空闲」就是碎片度的直接读数；heap_5 没有这个 API，才退回试探法——`pvPortMalloc(4096)` 失败但总空闲充足，就是碎片在说话，分完记得 `vPortFree` 还回去。

产品级兜底三选一：分配失败进安全态（关外设、置故障标志、等看门狗复位）；或记日志告警后降级运行；或直接复位重来。唯一不可接受的是静默续跑——失败那一刻起，后面所有输出都不可信。

## 场景 5：碎片实验的六步

代码在 `mcu/code/rtos/01-freertos-lab/main.c:249-264`，动作与预期：

| 步骤 | 操作 | 预期输出 | 判读 |
| --- | --- | --- | --- |
| 1 | 启动 | `boot free` ≈ 15 KB | 16 KiB 减掉内核固定开销 |
| 2 | A/B/C 各分 1 KB | `after ABC` 掉 ~3 KB | 每块含 8 B 头 |
| 3 | 释放 B | `after free B` 涨 ~1 KB | 总空闲涨，最大连续块没涨 |
| 4 | 要 2 KB | `big ok?=0` | **判定时刻**：账面够，连续块不够 |
| 5 | 释放 A | `after free A` | A、B 在地址上相邻，并成 2 KB |
| 6 | 再要 2 KB | `big ok?2=1` | 合并生效 |

证据口径：代码存在、可复跑；仓库没有落盘串口日志，`big ok?=0/1` 的读数是实验设计里的预期值，不是已复核的板级记录。上板跑一遍把日志抄进实验记录，这一章的「两个数」才算亲手见过。

换用 heap_2 重跑是很好的对照实验：把构建里的 `heap_4.c` 换成 `heap_2.c`，`xPortGetMinimumEverFreeHeapSize` 直接编译失败——heap_2 没有这个符号（`heap_2.c` 全文只有 `xPortGetFreeHeapSize`，在 `:334`）。指标 API 要逐文件核对，这就是现场教学。

## 静态分配：把失败搬到编译期

安全关键系统不允许运行时分配失败。`xTaskCreateStatic` 让调用方交出全部存储，内核零 malloc：

```c
static StaticTask_t sensorTCB;
static StackType_t  sensorStack[256];   /* 栈深 256 字 = 1024 B */

TaskHandle_t handle = xTaskCreateStatic(
    sensor_task, "sensor", 256, NULL, 2,
    sensorStack, &sensorTCB );
configASSERT( handle != NULL );
```

`configASSERT(handle != NULL)` 不能读成「永远成功」。传 `NULL` 栈数组、`StaticTask_t` 指针为空、栈数组小于栈深，一样断言或返回 `NULL`。静态分配换掉的只是**一种**失败：堆耗尽。参数错误这种失败，搬到哪个 API 都还在。它真正的卖点是：TCB 与栈在编译期占定 RAM，`vTaskDelete` 也不归还——运行期增减任务的自由没有了。

开 `configSUPPORT_STATIC_ALLOCATION=1` 之后，内核还会问你要两份存储：Idle 任务与 Timer 任务的 TCB 和栈。真实签名是**三参数**（V11.1.0 `tasks.c:8584-8586`）：

```c
void vApplicationGetIdleTaskMemory(
    StaticTask_t **ppxIdleTaskTCBBuffer,
    StackType_t **ppxIdleTaskStackBuffer,
    configSTACK_DEPTH_TYPE *pulIdleTaskStackSize )
{
    static StaticTask_t idleTCB;
    static StackType_t idleStack[configMINIMAL_STACK_SIZE];
    *ppxIdleTaskTCBBuffer   = &idleTCB;
    *ppxIdleTaskStackBuffer = idleStack;
    *pulIdleTaskStackSize   = configMINIMAL_STACK_SIZE;
}
```

第三个参数让内核反过来告诉你 Idle 栈要多深。Timer 任务的同名钩子 `vApplicationGetTimerTaskMemory` 同样三参数，栈深给出 `configTIMER_TASK_STACK_DEPTH`。旧资料里的两参数版本编译不过，照抄前先对一眼你手上的 `tasks.c`。

lab 的 `configSUPPORT_STATIC_ALLOCATION=0`（`FreeRTOSConfig.h`），本工程用不到这两个钩子；示例只在打开该配置的工程里可编译。动态与静态怎么选：长期运行产品、认证审查、不允许运行期失败的——静态；原型期、任务数随配置变的——动态加监控。两边的失败形态都要进预算，不能只算一边。

## 栈哨兵：canary 在切换瞬间点名

`configCHECK_FOR_STACK_OVERFLOW = 2`（`FreeRTOSConfig.h:31`）开启后，内核在**每次上下文切换**时检查任务的栈底填充——栈按 0xA5 预填，切换时看栈底那几个字节还是不是 0xA5。被踩了就调 `vApplicationStackOverflowHook( xTask, pcTaskName )`，lab 的实现打印任务名后停机。

为什么它值这点开销：爆栈的第一现场多数不是 HardFault，而是**悄悄踩了邻居**。相邻的 TCB、别的任务栈、某个全局数组，被踩后系统还能跑——只是某天某个值莫名其妙错了，通信偶尔丢包，日志里出现乱码。等 HardFault 再查，现场早被踩得面目全非。canary 把抓捕提前到踩线的那一次切换。配置 1 只检查栈指针越界（更便宜、更迟钝），配置 2 连填充一起查。栈水位的原理与测量见 [第 22 章](./22-tasks-tcb-scheduler.md) 的栈水位一节。

它也有盲区：检查只在切换时发生，踩了栈又自己改回去的路径抓不到；栈数组与被踩邻居的相对位置也影响检出顺序。canary 是哨兵，不是保险柜——预算阶段把栈深算对，比事后抓人便宜得多。

## heap_5：把堆拆到 CCM 与 SRAM

F407 的 RAM 是两块：128 KiB SRAM（SRAM1 112 KiB + SRAM2 16 KiB，`0x20000000` 起）加 64 KiB CCM（`0x10000000`，CPU 直连，**DMA 到不了**）。heap_4 只能管连续一整块；想把 CCM 也用起来，换 heap_5：

```c
static HeapRegion_t xHeapRegions[] = {
    { ( uint8_t * ) 0x10000000, 64 * 1024 },  /* CCM：地址低，排前面 */
    { ( uint8_t * ) 0x20000000, 128 * 1024 }, /* SRAM1+2 */
    { NULL, 0 }                               /* 终止行 */
};
vPortDefineHeapRegions( xHeapRegions );
```

三条硬规矩（V11.1.0 `heap_5.c:40-66`）：

1. `vPortDefineHeapRegions()` 必须在**任何** `pvPortMalloc` 之前调用——区域表一确定，链表就按它初始化，之后不可增删。
2. 区域数组**按起始地址从低到高**排，CCM 的 `0x10000000` 排在 SRAM 的 `0x20000000` 前面，最后以 `{ NULL, 0 }` 结尾。
3. 区域可以混搭：普通 SRAM 与 CCM 都能进表。但 **CCM 不能放 DMA 缓冲**——DMA 控制器够不着 CCM，外设收发会静默丢数据。这句话的主语是 CCM，不是 heap_5；heap_5 完全可以包含 DMA 可达的普通 SRAM 区域，「前提是区域 DMA 够不着」是把 CCM 的属性错记成 heap_5 的前提。

分区怎么用：UART/DMA 缓冲、IP 帧缓冲放 SRAM 区；只被 CPU 访问的表、日志缓冲放 CCM 区。heap_5 的分配/合并算法与 heap_4 同源，差异只在区域表；CCM 区满了分配会自动落到下一个区域（或者失败，取决于请求尺寸），碎片问题在两个区里各自独立存在，heap_5 又没有 `vPortGetHeapStats`，监控靠两个区的 `xPortGetFreeHeapSize` 与水位 API。

## 堆预算：从拍脑袋到工程账

`configTOTAL_HEAP_SIZE` 的预算公式，按本工程口径：

```text
总堆 = Σ(任务栈深 × 4 B) + Σ(TCB 88 B) + Σ(队列账) + 信号量/事件组 + 30% 余量
```

逐项校准：

- **栈**按字数给，一字 4 B（`StackType_t`）。深度别猜，用 `uxTaskGetStackHighWaterMark` 实测再加余量，见 [第 22 章](./22-tasks-tcb-scheduler.md)。
- **TCB** 按 probe 说法是本工程 88 B，加 heap_4 的 8 B 头（未复核的来源说法）。旧章写「~400 B」，与本仓库同配置的其他章冲突；400 B 只能当「开了 trace 或 MPU 扩展的其他配置的粗值」，别混进本工程的账。
- **队列账**沿用 [第 24 章](./24-queue-semaphore-notification.md)：`深度 × 项大小 + Queue_t 80 B + 头 8 B`。
- **余量**按 30% 起：给碎片（合并救不了跨已用块的那部分）、给未来加对象、给「实测时还没开全部功能」的误差。

算完和 SRAM 对账：F407 全部 RAM 是 128 KiB SRAM 加 64 KiB CCM，共 192 KiB。heap_4 的池子本体 `ucHeap` 是一个 16 KiB 的静态数组，落在 `.bss`——堆和你的全局变量抢同一块 SRAM，和 Flash 容量无关。「Flash 还有 1 MB，堆开 64 KB 都行」是把两种存储混为一谈的反模式：Flash 再大，SRAM 里挤不下 `.bss` 加栈，链接器照样报错。链接脚本的 MEMORY 布局见 [v1 第 8 章](../v1-drivers/08-architecture-memory-clock.md) 与 lab 的 `stm32f407xx.ld`。

RAM 的四类住客——线程栈、内核对象池（RTOS 堆）、C 库堆、以及它们各自的验证手段——收在一张手绘图里：

![手绘板：F407 RAM 的三类住客与验证手段——线程栈（水位与溢出钩子）、内核对象池/堆（启动前预算、最小空闲记录）、C 库堆（唯一分配器与锁策略）](/images/ch28-memory-regions.png)

## RT-Thread 对照：四件套与一个不在内核里的 TLSF

FreeRTOS 让你「编译期选一个 heap_x」；RT-Thread 的 `src/` 里同时住着**四件**分配器，可按对象选：

| 实现 | 覆盖 | 确定性 | 碎片 | 典型用途 |
| --- | --- | --- | --- | --- |
| `mem.c`（small memory） | 通用小堆 | 中 | 中 | 默认小内存管理，链表管理 |
| `memheap.c` | 多地址段拼接 | 中 | 中 | 多段物理内存统一成一个逻辑堆 |
| `slab.c` | 内核小对象 | 高（定长类） | 类内无外部碎片 | 内核对象高速缓存 |
| `mempool.c`（`rt_mp`） | 固定块池 | O(1) | 无 | 实时路径、DMA 缓冲 |

先纠一个流传很广的错误：**`src/tlsf.c` 不存在**。TLSF（Two-Level Segregated Fit）是 2004 年的论文算法，在 RT-Thread 里以软件包或第三方实现的形式提供，不在 5.x 内核源码树里。旧章把它写成内核三套堆之一，源码清单要按 `src/` 实际文件改写：mem、memheap、slab、mempool 四件。

![RT-Thread 内存池动画：块大小一刀切，alloc 摘空闲链表头、free 挂回链表头，无搜索无合并，O(1) 从结构里长出来](/anim/rtt-mem-alloc.svg)

四件之外再校三处旧章的说法：

- **TLSF 的选档方向**。两级位图找块：`fls`/CLZ 只负责「请求尺寸 → 第一级档位」的粗定位；选定可用块要用 `ffs`/CTZ 在位图里找**最低**有效位——方向是从「刚好够用的最小档」往下取。写成「CLZ 找最小够用档」把两级分工搞反了。
- **slab 的「碎片免疫」过头**。同一尺寸类内部确实不产生外部碎片——归还的块和请求的块必然同尺寸。但固定尺寸类本身带来**内部碎片**（大对象塞进大一号的类，尾部浪费），zone 扩张还可能失败。正确说法是「类内无外部碎片」，不是「免疫」。
- **finsh 的堆监控命令名**。真实导出的命令是 `memheapcheck`/`memheaptrace`（`memheap.c:959`/`:1039`）与 `memcheck`/`memtrace`（`mem.c:640`/`:711`）；`list_memheap` 只是 `msh.c` 内部函数，不是可敲的命令。旧章的 `list_memp` 在内核源码里没有对应导出。

两边的结构对照：

| 维度 | FreeRTOS | RT-Thread |
| --- | --- | --- |
| 分配器形态 | 编译期选一个 heap_x | 四件并存，按对象选 |
| 释放 | heap_4 起支持 | mem/memheap/slab 都支持 |
| 合并 | heap_4 相邻合并 | mem/memheap 相邻合并；池与 slab 定长无碎片 |
| 最大连续块 | heap_4 `vPortGetHeapStats` 直读；heap_5 无 | `memcheck`/`memheapcheck` 看 stats，无直读 API 的版本自己估 |
| 固定块池 | 无内置，自己拼 | `rt_mp` 一等公民 |
| 关堆 | `configSUPPORT_DYNAMIC_ALLOCATION=0` | `RT_USING_HEAP` 关闭 |
| 静态创建 | `xTaskCreateStatic` 等 | `*_init` 系列（调用方自备内存） |

`rt_mp` 值得多说一句：固定块池把一块连续内存切成 N 个等大块，空闲块串成单链表，`rt_mp_alloc` 摘表头、`rt_mp_free` 挂回表头——没有搜索、没有分裂、没有合并，O(1) 是从**等大**这个前提里长出来的。代价是块大小一刀切：按最大成员加对齐定，宁大勿小。`rt_mp_alloc` 的 timeout 参数让块用尽时可以挂起等待，把内存池变成了能排队的资源——这是 FreeRTOS 没有的内置形态。

`RT_USING_HEAP` 关掉后，`*_create` 系列编译不进来，`*_init` 系列照常可用：对象全静态、栈全静态，固件变成「零堆」形态。与 FreeRTOS 的 `configSUPPORT_DYNAMIC_ALLOCATION=0` 是同一条路：动态分配的便利与静态分配的确定性是产品形态的二选一，不是谁永远更好。

## 短自测

1. heap_1 的 `vPortFree` 为什么还在文件里？
<details><summary>参考答案</summary>接口完整性：五个 heap 导出同一组符号，工程换版本不用改调用方。`heap_1.c:130-136` 的实现体只有 `configASSERT( pv == NULL )`——释放任何非空指针都断言失败。「函数在」不等于「功能在」。</details>

2. 「边界标记法」为什么套不到 heap_4 上？
<details><summary>参考答案</summary>边界标记法要求每块带 footer，用「前块地址 + 前块大小」从当前块反推前邻块，前后两个方向 O(1) 探邻居。heap_4 只有 8 B 块头（`pxNextFreeBlock` + `xBlockSize`），没有 footer；前邻块靠地址序空闲表遍历找（`pxIterator` 停在插入位置），释放是 O(n)。术语错了，机制也对不上。</details>

3. 每次分配的 overhead 是多少？由哪两行算出来？
<details><summary>参考答案</summary>本工程 8 B：`BlockLink_t` 是 32 位指针 + 4 B size_t 共 8 B，`xHeapStructSize = ( sizeof( BlockLink_t ) + portBYTE_ALIGNMENT - 1 ) & ~portBYTE_ALIGNMENT_MASK`（`heap_4.c:158`），`ARM_CM4F` 的 `portBYTE_ALIGNMENT=8` 对齐后还是 8。请求尺寸不满足 8 对齐时另收对齐余量。</details>

4. 总空闲 14 KB 为什么分不出 2 KB？什么时候能分出？
<details><summary>参考答案</summary>空闲碎成不连续小块：1 KB 洞被已用的 A、C 夹住，最大连续块还是 13 KB。分配器要的是连续空间，不是账面总和。释放 A 之后 A、B 两洞在地址上相邻，`prvInsertBlockIntoFreeList` 把它们并成 2 KB，请求成功——场景 5 的第 4、6 步。</details>

5. 当前空闲与历史最低水位分别回答什么？谁「不是碎片率」？
<details><summary>参考答案</summary>当前空闲是瞬时值；历史最低水位（`xPortGetMinimumEverFreeHeapSize`）回答「开机以来最紧张的时刻剩多少」，是峰值压力指标。水位不是碎片率——总量与连续块是两个数。碎片度看「最大连续块 / 总空闲」，heap_4 用 `vPortGetHeapStats` 的 `xSizeOfLargestFreeBlockInBytes` 直读。</details>

6. 静态创建真的「不会失败」吗？
<details><summary>参考答案</summary>只消灭堆耗尽这一种失败。传 `NULL` 缓冲、栈数组小于栈深、`StaticTask_t` 指针为空，照样断言或返回 `NULL`。`configASSERT(handle != NULL)` 是调试期检查，不是「任何参数都成功」的承诺。它真正的卖点是 TCB 与栈编译期占定 RAM、不受碎片影响。</details>

7. Idle/Timer 静态钩子的真实签名是几个参数？照抄两参数版会怎样？
<details><summary>参考答案</summary>三参数：TCB 指针、栈指针、`configSTACK_DEPTH_TYPE *` 指向栈深（`tasks.c:8584-8586`）。两参数版编译不过——函数签名对不上，链接期就报错。</details>

8. canary 在什么时刻检查什么？抓不到什么？
<details><summary>参考答案</summary>`configCHECK_FOR_STACK_OVERFLOW=2` 在每次上下文切换时检查任务栈底的 0xA5 填充，被踩就调 `vApplicationStackOverflowHook`。盲区：只在切换时查，踩完又改回去的路径抓不到；也不防止这次踩线造成的既成事实。</details>

9. heap_5 的区域表有哪三条硬规矩？CCM 那句话怎么说才是对的？
<details><summary>参考答案</summary>`vPortDefineHeapRegions` 必须先于任何 `pvPortMalloc`；区域按起始地址从低到高排；以 `{NULL,0}` 结尾。对的话是「CCM 不能放 DMA 缓冲」——主语是 CCM（DMA 够不着 `0x10000000`），不是「heap_5 的前提是区域 DMA 够不着」，heap_5 完全可以含普通 SRAM 区域。</details>

10. 16 KiB 池的预算怎么算？269 是什么身份？
<details><summary>参考答案</summary>预算 = Σ(栈深×4) + Σ(TCB 88 B + 8 B 头) + Σ(队列账，如 248 B) + 信号量/事件组 + 30% 余量。269 = (16384−1312)/56，是「每定时器 56 B」成立时定时器个数的上界，不是预算。TCB 不按 400 B 算——那是其他 trace/MPU 配置的粗值，与本工程 probe 口径冲突。</details>

11. 堆和 Flash、`.bss` 什么关系？
<details><summary>参考答案</summary>heap_4 的池子 `ucHeap` 是静态数组，落在 `.bss`，和全局变量抢 SRAM；与 Flash 容量无关。「Flash 大所以堆可以大」是混淆两种存储的反模式。F407 全部 RAM 是 128 KiB SRAM + 64 KiB CCM 共 192 KiB，堆开多大要看 `.bss` 加栈还剩多少。</details>

12. RT-Thread 的 `src/` 里有哪几件分配器？`src/tlsf.c` 存在吗？
<details><summary>参考答案</summary>四件：`mem.c`（small memory）、`memheap.c`（多段拼接）、`slab.c`（内核小对象定长类）、`mempool.c`（`rt_mp` 固定块池）。`src/tlsf.c` 不存在——TLSF 是论文算法与软件包，不在 5.x 内核源码树。</details>

13. TLSF 找块的位图方向是什么？slab「碎片免疫」怎么修正？
<details><summary>参考答案</summary>`fls`/CLZ 只做「请求尺寸 → 第一级档位」的粗定位，选定可用块用 `ffs`/CTZ 找位图最低有效位——从刚好够用的最小档往下取。slab 的准确说法是「同尺寸类内不产生外部碎片」；固定尺寸类带来内部碎片，zone 扩张可能失败，「免疫」过强。</details>

14. `rt_mp` 的 O(1) 从哪来？代价是什么？
<details><summary>参考答案</summary>从「等大」来：块等大，空闲链表摘头即分配、挂头即归还，无搜索、无分裂、无合并。代价是块大小一刀切——按最大成员加对齐定，宁大勿小；块用尽时 `rt_mp_alloc` 按 timeout 参数挂起等待，把内存池变成能排队的资源。</details>

15. `RT_USING_HEAP` 关掉后固件长什么样？FreeRTOS 的等价开关是什么？
<details><summary>参考答案</summary>`*_create` 系列编译不进来，`*_init` 系列照常：对象全静态、栈全静态，零堆形态，适合安全关键场景。FreeRTOS 等价开关是 `configSUPPORT_DYNAMIC_ALLOCATION=0`；两条路共同点是把「分配失败」这个类别整个移出运行期。</details>

16. finsh 的堆监控命令真实叫什么？
<details><summary>参考答案</summary>`memheapcheck`/`memheaptrace`（`memheap.c:959`/`:1039`）与 `memcheck`/`memtrace`（`mem.c:640`/`：711`）。`list_memheap` 只是 `msh.c` 内部函数，不是可敲的命令。</details>

17. 本章哪些数是来源说法、哪些未实测？
<details><summary>参考答案</summary>来源说法（未复核）：probe 的 TCB 88 B 与固定账 1312 B、每定时器 56 B、269 上界。未实测：场景 5 的 `big ok?=0/1` 板级读数（代码在 `main.c:249-264`，仓库无落盘日志）、爆栈触发 OverflowHook 的实验、RT-Thread 的分配耗时对比。文档推导：五版能力表、合并三步、8 B 头、指标 API 落点、heap_5 三规矩、RT-Thread 文件清单与命令名。</details>

<QuizBank chapter="f7-heap" />

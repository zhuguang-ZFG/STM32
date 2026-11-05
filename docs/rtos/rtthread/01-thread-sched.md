---
title: R1 线程与调度：256 级位图的另一种写法
status: done
difficulty: 2
minutes: 35
---

# R1 线程与调度：rt_thread 解剖

> 🎯 FreeRTOS 用 32 位位图管 32 个优先级；RT-Thread 说 32 个不够，上 256 级——位图还是那张位图，只是升级成"二级位图"（32×8）。同样的 CLZ，加一层索引，调度依然是 O(1)。

## 本章精髓

1. `struct rt_thread` 与 TCB 对照：对象头（R0 的继承）+ `sp`（栈顶）+ 优先级 + 状态 + 剩余 tick + 定时器（线程自带 `rt_timer`！）。功能等价物都能找到，结构风格更"面向对象"。
2. 二级位图：`rt_thread_ready_table[32]` 每字节管 8 个优先级，`rt_thread_ready_priority_group` 管哪字节非空：两次 CLZ/查表定位最高优先级（源码 `rt_schedule` + `_get_highest_priority_thread`）。
3. 调度点的同与不同：同样有 tick（`rt_tick_increase`）、有抢占；不同的是 RT-Thread 把"线程延时"挂在**线程自带的定时器**上，定时器子系统是全家共享的基础设施。

- **能理解**：为什么二级位图能 O(1) 定位 256 级（两步查表）；为什么 `rt_thread_create` 之后还要 `rt_thread_startup`；为什么删除线程要"排队死"；优先级数值方向三家怎么背。
- **能用**：`list_thread` 看栈水位；`rt_thread_create`/`rt_thread_init` 各建一线程并说清内存来源；用 GDB 对照 RTT 与 FreeRTOS 的就绪表内存布局。

## 先修

- [R0](00-arch.md)、[F1](../freertos/01-task-tcb.md)~[F3](../freertos/03-scheduler.md)。

## 先跑起来（10 分钟 quick win）

finsh 里 `list_thread` 看自家线程表：名称/优先级/状态/栈用量一屏出，RT-Thread 的"可观测性"开箱即用。

list_thread 之前先押个嫁妆：rt_thread 出门自带一件东西，FreeRTOS 的延时要把任务挂进全局的阻塞列表统一管；是哪件？押完对照 rtdef.h 与 F1 的 TCB 看答案。

## 动画：二级位图 256 级选优

先在 32 位组选字上定位第一个非空字节，再在该字节上定位第一个非空位，两次固定步数查表，256 级优先级的 O(1) 选优全程可见。

![R1 二级位图：32×8 实现 256 级优先级选优](/anim/rtt-bitmap-256.svg)

## 小节结构

| 小节 | 内容 | 四件套 |
|---|---|---|
| rt_thread 解剖 | 字段逐一对照 tskTCB | 库解析 |
| 二级位图 | 256 级选优的两步查表；与 32 级的取舍 | 库解析 |
| 动态 vs 静态 | rt_thread_create vs rt_thread_init 的内存来源 | 配置 |
| tick 与定时器 | rt_tick_increase 与线程内嵌 rt_timer | 库解析 |
| 调度点 | rt_schedule 的进入路径（API/中断退出/tick） | 代码分析 |
| 栈与水位 | list_thread 的栈用量列；与 F 篇水位线对照 | 代码分析 |

## 一、rt_thread 解剖：字段逐一对照 tskTCB

`struct rt_thread`（以 RT-Thread 官方源码 `rt-thread/include/rtdef.h` 为准）的核心字段，与 FreeRTOS `tskTCB`（[F1](../freertos/01-task-tcb.md)）逐项对照：

| rt_thread 字段 | 含义 | tskTCB 对照 | 备注 |
|---|---|---|---|
| `parent`（`rt_object`） | 对象头：名字+类型+标志+容器链表 | 无直接对应 | RTT 的"继承"，FreeRTOS 没有 |
| `sp` | 当前栈顶 | `pxTopOfStack` | 同为切换锚点 |
| `current_priority` | 当前优先级（数值越小越高） | `uxPriority`（越大越高） | **方向相反** |
| `stat` | 状态（就绪/挂起/阻塞/…） | `eCurrentState` | |
| `remaining_tick` | 剩余时间片/延时 tick | `xItemValue`（延时列表项值） | RTT 独立字段 |
| `timer`（`rt_timer`） | **线程内嵌定时器** | 无内嵌，延时挂阻塞列表 | RTT 特色 |
| `stack_addr`/`stack_size` | 栈底地址/栈大小 | `pxStack`/栈深 | |
| `entry`/`parameter` | 入口函数/参数 | 任务函数/参数 | |

最显著的两处差异：

1. **对象头 `parent`**：FreeRTOS 的 TCB 是个"光杆"结构体，RTT 的线程一上来先继承 `rt_object`，所以它有名字、有类型、自动进容器，`list_thread` 才能打印。这是 R0"万物皆对象"在 TCB 上的具体落地。
2. **内嵌 `rt_timer`**：FreeRTOS 的延时靠"阻塞列表 + 列表项的 `xItemValue`"，没有"每个任务一个定时器"的概念；RTT 直接给每个线程塞一个 `rt_timer`，线程延时就把这个定时器挂到系统定时器链上，到点了回调唤醒，**定时器子系统是全家共享的基础设施**，连线程延时都用它。

> 看字段名记风格：FreeRTOS 偏"裸数据 + 链表项"组合，RTT 偏"面向对象 + 自带定时器"。

## 二、二级位图：256 级选优的两步查表

RT-Thread 的就绪表是"二级位图"（以 RT-Thread 官方源码 `rt-thread/src/scheduler.c` 为准，看 `_get_highest_priority_thread` 与 `rt_schedule`）：

- `rt_thread_ready_priority_group`：一个 32 位字，bit i 表示"第 i 个字节是否有就绪线程"；
- `rt_thread_ready_table[32]`：32 字节数组，每个字节 8 位，bit j 表示"优先级 i×8+j 是否就绪"。

两层加起来 = 32×8 = **256 级优先级**。选优分两步：

1. 在 `rt_thread_ready_priority_group` 上做 CLZ（或查 `rt_lowest_bitmap` 表）找到**第一个非空字节**的索引 `i`；
2. 在 `rt_thread_ready_table[i]` 那个字节上再做一次 CLZ/查表，找到**该字节内第一个非空位** `j`；
3. 最高优先级 = `i×8 + j`。

两次查表，固定步数，与任务总数无关，**O(1)**。

对照 FreeRTOS（[F3](../freertos/03-scheduler.md)）：它用一个 32 位字，每个 bit 一个优先级，最多 32 级，一次 CLZ 完事。取舍：

| | FreeRTOS | RT-Thread |
|---|---|---|
| 最大优先级数 | 32（`configMAX_PRIORITIES` 上限 32） | 256 |
| 查询步数 | 1 次 CLZ | 2 次查表/CLZ |
| RAM 开销 | 1 个 32 位字 | 1 个 32 位字 + 32 字节 |
| 适合场景 | 优先级少、极致精简 | 优先级多、要细分 |

RTT 多花一丁点 RAM 和一次查表，换来 8 倍的优先级粒度，这是"位图位图，多一层索引"的代价与收益。

> 口诀：`rt_thread_ready_priority_group` 选字节，`rt_thread_ready_table[i]` 选位，两次定位 256 级。

## 三、动态 vs 静态：两种创建的内存来源

RT-Thread 给线程两种创建方式，内存来源不同（以 RT-Thread 官方源码 `rt-thread/src/thread.c` 为准）：

| | `rt_thread_create` | `rt_thread_init` |
|---|---|---|
| TCB 来源 | 堆 `rt_malloc` | 用户提供（静态） |
| 栈来源 | 堆 `rt_malloc` | 用户提供（静态） |
| 返回 | 句柄（指针） | `rt_err_t`（错误码），句柄即传入指针 |
| 释放 | `rt_thread_delete`（堆上回收） | `rt_thread_detach`（不释放内存，自管） |
| FreeRTOS 对照 | `xTaskCreate`（动态） | `xTaskCreateStatic`（静态） |

两者都**只造好线程、不挂就绪**，必须再调一次 `rt_thread_startup` 才把它放进就绪表、可能立即抢占当前线程。这是和 FreeRTOS `xTaskCreate` 最大的行为差：FreeRTOS 的 `xTaskCreate` 一步到位（造好 + 挂就绪 + 可能立即抢占），RTT 把"造"和"启动"拆成两步，少了 `startup` 线程永远不动（见常见坑）。

选哪种：

- **动态**：栈大小运行时才定、用完能 `delete` 回收，灵活，但依赖堆、有碎片风险；
- **静态**：栈和 TCB 全在编译期定好地址，不依赖堆、不怕碎片，安全核查/功能安全场景首选。

## 四、tick 与定时器：rt_tick_increase 与线程内嵌 rt_timer

时钟节拍由 `rt_tick_increase` 驱动（以 RT-Thread 官方源码 `rt-thread/src/clock.c` 为准）：每个 SysTick 中断调用它，做两件事：

1. 系统时钟 `rt_tick` 加 1；
2. 遍历定时器链表，把到点的定时器摘下来、执行回调。

线程延时的实现（`rt_thread_delay`/`rt_thread_mdelay` → `rt_thread_sleep`）：把当前线程从就绪表摘下，给它**自带的 `rt_timer`** 设上延时值，挂进系统定时器链，然后触发调度。到点了定时器回调把线程重新挂回就绪表，延时就这样完成。

这是 RTT 和 FreeRTOS 的关键架构差：

- **FreeRTOS**：延时靠"延时列表 + 列表项的 `xItemValue`（唤醒 tick）"，每个任务没有"自己的定时器对象"，调度器在 tick 里扫延时列表；
- **RT-Thread**：延时直接借用"线程内嵌的 `rt_timer`"，定时器子系统是共享的，线程延时、软件定时器、超时 watchdog 都走同一套机制。

> 对照着看：FreeRTOS 把延时塞进调度器的列表，RTT 把延时挂到线程肚里的定时器，基础设施复用，概念上 RTT 更"对象化"。

## 五、调度点：rt_schedule 的进入路径

`rt_schedule` 是 RTT 的调度入口（以 RT-Thread 官方源码 `rt-thread/src/scheduler.c` 为准），三种典型进入路径：

1. **API 主动让出**：`rt_thread_yield`（同优先级轮转）、`rt_thread_delay`/`rt_thread_mdelay`（延时阻塞自己），这些 API 内部调 `rt_schedule`；
2. **中断退出**：PendSV/上下文切换路径里，如果标记了"需要切换"，在中断退出时跑调度（libcpu 层）；
3. **tick 到点**：`rt_tick_increase` 里，如果时间片用完或延时到点，触发 `rt_schedule`。

`rt_schedule` 干的活：用二级位图找出当前最高优先级就绪线程，与当前线程比较，不一样就调 `rt_hw_context_switch` 换栈（PendSV）。这与 FreeRTOS 的"找最高就绪 → PendSV 切换"骨架一致，差别只在"怎么找最高优先级"（位图实现不同，见第二节）。

## 六、栈与水位：list_thread 的栈用量列

finsh 的 `list_thread` 输出列大致是：`name / pri / status / sp / stack size / stack used / max used`。其中：

- **stack size**：建线程时给的栈大小（字节，RTT 这里直接是字节不是字）；
- **max used / 栈水位**：历史最大使用深度，原理同 FreeRTOS 的 `uxTaskGetStackHighWaterMark`（[F1](../freertos/01-task-tcb.md) 第五节）：建栈时把空闲区填一个魔数（RTT 默认 `'#'`），运行后扫到底部往上第一个非魔数的位置，就知道"最深用到哪"。

对照 F 篇水位线：

| | FreeRTOS | RT-Thread |
|---|---|---|
| 魔数 | `0xA5`（`tskSTACK_FILL_BYTE`） | `'#'` |
| 查询 API | `uxTaskGetStackHighWaterMark` | `list_thread` 内置列 / 扫栈 |
| 单位 | 字（`StackType_t`） | 字节 |
| 溢出钩子 | `vApplicationStackOverflowHook` | `rt_thread_stack_overflow_hook` |

**对照学习的硬证据**：同一台板子分别刷 FreeRTOS 与 RTT 两份固件，GDB 看 `pxCurrentTCB`/`rt_current_thread` 的就绪表内存布局：单级位图（一个 32 位字）vs 二级位图（一字 + 32 字节数组），一眼看清"两种解法"。

## 记忆锚点

::: tip 一句话记住
**对象打头 sp 记账，256 级两查表；动态堆上请，静态自家造；线程肚里还揣着定时器。**
:::

**延伸**：RTT 二级位图动画见 [R1 动画](/anim/rtt-bitmap-256.svg)；FreeRTOS 调度对照见 [F3](../freertos/03-scheduler.md)；任务创建与 TCB 在 [F1](../freertos/01-task-tcb.md) 详解。

## 实物实验

- 双线程异频闪灯 + `list_thread` 观测栈水位；
- GDB 对照两 OS 的"就绪表"内存布局（同一台板子两份固件），对照学习的第一个硬证据。

## 常见坑

- **静态线程忘了栈对齐**：自供栈必须 8 字节对齐（RT_ALIGN），不对齐下场同 F2。
- **删除线程在自身上下文**：自杀用 `rt_thread_delete(rt_thread_self())` 并在调度中清理，理解"死亡也要排队"。
- **优先级习惯沿用 FreeRTOS 数值感**：RT-Thread 数值越小优先级越高（0 最高），与 NVIC 同向、与 FreeRTOS 反向，三家对照背熟。
- **启动线程忘 rt_thread_startup**：create 只是造好，startup 才挂就绪，少一步永远不动。
- **二级位图查表方向记反**：`rt_thread_ready_priority_group` 用 CLZ 找最低置位（=最高优先级），不是从高位往低扫，记住"数值小先跑"，与 NVIC 同向。

## 短自测

1. `rt_thread` 结构体的第一个成员是什么？它带来了什么能力？
<details><summary>看答案</summary>第一个成员是 rt_object（对象头）。它让线程继承"对象"，有名字、有类型、自动进对象容器，所以 list_thread 才能一把梭打印。这是 C 结构体嵌套模拟继承（回 C4）。</details>

2. 二级位图怎么用两次查表/CLZ 定位 256 级中的最高优先级？
<details><summary>看答案</summary>第一步在 rt_thread_ready_priority_group（32 位字）上 CLZ 找第一个非空字节的索引 i；第二步在 rt_thread_ready_table[i]（那个字节）上再 CLZ 找第一个非空位 j；最高优先级 = i×8 + j。两次查表固定步数，O(1)。</details>

3. `rt_thread_create` 和 `rt_thread_init` 的内存来源有何不同？各自对应 FreeRTOS 的哪个 API？
<details><summary>看答案</summary>create 从堆 rt_malloc 分配 TCB 和栈（动态），对应 FreeRTOS 的 xTaskCreate；init 用用户自备的 TCB 和栈（静态），对应 xTaskCreateStatic。两者都还要再调 rt_thread_startup 才挂就绪，这点和 xTaskCreate 一步到位不同。</details>

4. RT-Thread 的线程延时挂在哪个数据结构上？这和 FreeRTOS 有什么不同？
<details><summary>看答案</summary>挂在线程内嵌的 rt_timer 上，延时 = 摘下就绪 + 给自带定时器设值 + 挂系统定时器链，到点回调唤醒。FreeRTOS 没有内嵌定时器，延时靠"延时列表 + 列表项 xItemValue"。RTT 把定时器作为全家共享基础设施。</details>

5. RT-Thread 的优先级数值方向如何？与 FreeRTOS、NVIC 各是什么关系？
<details><summary>看答案</summary>RT-Thread 数值越小优先级越高（0 最高），与 NVIC 中断优先级同向，与 FreeRTOS（数值越大越高）反向。三家对照背熟：RTT/NVIC 数小高、FreeRTOS 数大高。</details>

## 对照表：本章概念 → 仓库与上游落点

| 概念 | 落点 |
|---|---|
| `struct rt_thread` | 以 RT-Thread 官方源码（`rt-thread/include/rtdef.h`）为准（`struct rt_thread`，首成员 `parent`） |
| 二级位图 | 以 RT-Thread 官方源码（`rt-thread/src/scheduler.c`）为准（`rt_thread_ready_table` / `rt_thread_ready_priority_group` / `_get_highest_priority_thread`） |
| `rt_thread_create` / `rt_thread_init` | 以 RT-Thread 官方源码（`rt-thread/src/thread.c`）为准 |
| `rt_tick_increase` | 以 RT-Thread 官方源码（`rt-thread/src/clock.c`）为准 |
| `rt_schedule` | 以 RT-Thread 官方源码（`rt-thread/src/scheduler.c`）为准 |
| `list_thread` | 以 RT-Thread 官方源码（`rt-thread/components/finsh/`）为准 |
| 对照锚点 | [F1](../freertos/01-task-tcb.md) tskTCB / [F3](../freertos/03-scheduler.md) 单级位图 |

## 你做到了

- 第二个内核的线程/调度机制打通；
- "同一问题两种解法"的对照眼练成。

嫁妆是定时器：FreeRTOS 把延时挂进全局的阻塞列表，RT-Thread 让每个线程自带 rt_timer 出门。同一件事两种记法，你的双 OS 对照表又添一行。

<div class="achievement">
✅ 下一站：<a href="02-ipc.html">R2 IPC 全家桶</a>：信号量/互斥量/事件/邮箱/消息队列，一套范式五种武器。
</div>

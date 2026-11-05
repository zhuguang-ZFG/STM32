---
title: R3 RT-Thread 内存管理：确定性之美
status: done
difficulty: 3
minutes: 35
---

# R3 内存管理：memheap、slab、TLSF 与内存池

> 🎯 FreeRTOS 问你"选 heap 几"，RT-Thread 问得更细：通用堆要确定性（TLSF）还是要简单（memheap）？内核小对象要不要专用快车道（slab）？实时路径上干脆别用堆，用**内存池**（分配时间是常数）。

## 本章精髓

1. 三套堆策略的场景分治：memheap（多地址段拼接，简单够用）、slab（内核对象的小块高速缓存，碎片免疫）、TLSF（Two-Level Segregated Fit，分配/释放都近 O(1)，大内存与实时性的双优生）。
2. 内存池（rt_mp）是实时的答案：固定块大小+空闲链表，分配=摘链表头，O(1) 且无碎片；代价是块大小一刀切（大材小用浪费，小了装不下）。
3. 静态内存潮：RT-Thread 与 FreeRTOS 一样支持"全静态创建"，安全关键场景连堆都可以不要（RT_USING_HEAP 关掉）。

- **能理解**：为什么 TLSF 近 O(1) 而不是绝对 O(1)；为什么 slab "碎片免疫"；为什么内存池没有碎片但块大小一刀切；为什么 RT_USING_HEAP 可关。
- **能用**：给"内核对象/通用大块/实时路径"三类场景各选一套；用 rt_mp_alloc vs rt_malloc 的耗时差把"确定性"量化成数字。

## 先修

- [F7 heap](../freertos/07-heap.md)（对照锚点）、[C1](../../c/01-memory-model.md)。

## 先跑起来（10 分钟 quick win）

同一申请量分别用 `rt_malloc` 与 `rt_mp_alloc` 各跑 1 万次，rt_tick 差打印：内存池的确定性，数字自己会说话。

烧板之前先押个平不平：同样的申请量各跑一万次，rt_malloc 和 rt_mp_alloc 的耗时线，哪条平得像尺子？押完看 rt_tick 差，数字自己作证。

## 动画：内存池的确定性

块大小一刀切，空闲链表串起；alloc 摘链头、free 挂链头，没有搜索没有分裂，O(1) 从结构里长出来。右上的耗时形态对照把"恒定 vs 波动"演成两根柱子。

![RT-Thread 内存池：块大小一刀切，换 O(1) 的确定性](/anim/rtt-mem-alloc.svg)

## 小节结构

| 小节 | 内容 | 四件套 |
|---|---|---|
| 三套堆 | memheap/slab/TLSF 场景分治表 | 库解析 |
| TLSF 直觉 | 两级位图怎么做到近 O(1)（与 RTT 调度二级位图同源思想！） | 库解析 |
| 内存池 | 固定块池的结构与 O(1) 证明；块大小设计 | 代码分析 |
| 静态创建 | object init 系列 API；关 HEAP 的固件形态 | 配置 |
| 泄漏与监控 | list_memheap/rt_memory_info；与 F7 监控法对照 | 代码分析 |

## 一、三套堆：场景分治表

| 堆 | 适用内存规模 | 确定性 | 碎片 | 典型用途 |
|---|---|---|---|---|
| memheap | 多地址段拼接 | 中（链表管理） | 中 | 多段物理内存的统一管理，简单够用 |
| slab | 内核小对象 | 高（定长块） | **免疫** | 内核对象（thread/timer/sem）高速缓存 |
| TLSF | 大内存 | **近 O(1)** | 低（按大小分级，合并友好） | 通用大块分配，实时性双优 |

三者可同时存在，各管各的"小地盘"：memheap 管拼接的多段物理内存，slab 在其上为内核常用小对象开"快车道"，TLSF 面向应用的大块通用堆。

> **【对照 F7】** FreeRTOS 给你五份简历（heap_1~5），按"释放/合并/多区"递进（[F7](../freertos/07-heap.md)）；RT-Thread 给你三套**正交**的策略，按"用途"分治：一个走阶梯，一个走分治。

## 二、TLSF 直觉：两级位图怎么做到近 O(1)

TLSF = **Two-Level Segregated Fit**（两级分离适配）。第一级按 2 的幂划大块区间（如 16/32/64/128...），第二级在每个大区间内再细分子档位。

- **第一级位图**：一串 bit 标记"哪些大小档有空闲块"，查 CLZ 一次定位到最小够用的档；
- **第二级位图**：在该档内再细分几档，再查一次位图锁定具体子档；
- **取块**：摘下该子档链表头，O(1)；**释放**：检查前后邻块是否空闲，空闲就合并，合并代价也近 O(1)。

为什么是"近 O(1)"而不是绝对 O(1)：合并时查邻块状态需要 O(1)，但极端情况下位图扫描的常数较大；TLSF 的工程价值在于**最坏情况下的常数上界被压住**，对实时系统这就是"足够好的确定性"。

> **【同源】** RT-Thread 调度的二级位图（`rt_thread_ready_priority_group` + `rt_thread_ready_table[32]`，见 [R1](01-thread-sched.md)）和 TLSF 的两级位图是同一个思想的两副面孔：**位图+CLZ 把"找最值"压成常数级**。调度器用它找"最高优先级就绪线程"，TLSF 用它找"最小够用的空闲块"。同一个工程美学，读 R1 的位图再回来看 TLSF，你会感觉到"这套招式我见过"。

## 三、内存池：固定块池与 O(1) 证明

`rt_mp`（memory pool）是实时的答案。结构上：

- 一段连续内存被切成 N 个**等大**的块；
- 空闲块串成一条空闲链表；
- `rt_mp_alloc`：摘链表头，O(1)，**没有查表、没有合并、没有位图扫描**；
- `rt_mp_free`：放回链表头，O(1)。

**碎片免疫的来源**：所有块同样大，归还的块和被请求的块必然同尺寸，不存在"小请求塞不进大洞"或"大请求拼不上小洞"的问题。代价就是**块大小一刀切**：池块按"最大成员+对齐"定，宁大勿小，放不下时 alloc 直接失败或挂起等待（看 timeout 参数）。

`rt_mp_alloc` 的 timeout 参数：池块用尽时**可以挂起等待**（不像 rt_malloc 直接返回 NULL）。这把内存池变成了"资源排队"的 IPC 化形态。挂起同样走 `rt_ipc_list_suspend`，与 [R2](02-ipc.md) 的 IPC 骨架同源。

> **【对照 FreeRTOS】** FreeRTOS 没有内置内存池，你得自己用 `pvPortMalloc` 拼一个。RT-Thread 把内存池做成内核一等公民，是因为实时路径（中断下半部、DMA 缓冲）对"分配时间必须确定"的要求比"省内存"更高。

## 四、静态创建：object init 系列

RT-Thread 与 FreeRTOS 一样支持"全静态创建"：

- 动态版：`rt_sem_create`/`rt_thread_create`/`rt_mp_create`，内核向堆要内存；
- 静态版：`rt_sem_init`/`rt_thread_init`/`rt_mp_init`，调用方自备内存（静态数组），内核只填字段。

`RT_USING_HEAP` 这个 Kconfig 选项一关，动态创建路径直接编译不进来，固件变成"零堆"形态，安全关键场景（IEC 61508/SIL）的标配。**整个应用用静态创建 + 静态任务栈**，堆的痕迹从你的固件里消失。

> **【对照 F7】** FreeRTOS 的 `configSUPPORT_DYNAMIC_ALLOCATION=0` 走同一条路（[F7](../freertos/07-heap.md)）。两套 OS 都承认"动态分配的便利"和"静态分配的确定性"是产品形态的二选一，而不是某个永远更好。

## 五、泄漏与监控：list_memheap 与两个指标

finsh 提供：

- `list_memheap`：列出所有 memheap 段的总量/已用/最大连续块；
- `list_memp`（或等价命令，**以 RT-Thread 官方源码为准**）：内存池的总量/空闲块数；
- `rt_memory_info` 系列：更细的堆统计。

监控的两个指标要分清（与 F7 同名同义）：

- **当前空闲**：现在还剩多少；
- **历史最低水位**：最紧张时刻还剩多少，回答"最坏多紧张"，**不是碎片率**。

碎片率要自己估：把"最大连续块 / 总空闲"当近似指标，长期产品跑下来这个比值持续走低，说明堆在变碎，这是"产品寿命"的预警线。

> **【对照 F7 监控法】** `xPortGetMinimumEverFreeHeapSize`（heap_4/5）等价于 RT-Thread 的历史最低水位；`xPortGetFreeHeapSize` 等价于当前空闲。指标含义一致，API 名不同，逐项对照见下方对照表。

## 记忆锚点

::: tip 一句话记住
**通用堆选 TLSF，内核小块走 slab，实时路径上内存池；池子 O(1) 无碎片，就是块大不能挑。**
:::

## 实物实验

- quick win 耗时对比 + 故意把池块用尽看 `rt_mp_alloc` 挂起等待的行为（超时参数），资源池排队的真实体感。

## 常见坑

- **块大小拍脑袋**：池块按"最大成员+对齐"定，宁大勿小，放不下时 alloc 直接失败。
- **内存池里放变长数据**：变长需求回 TLSF，别硬塞池子。
- **混用 alloc/free 家族**：rt_malloc 与 rt_mp_free 交叉释放=内存灾难，谁家的孩子谁领走。
- **TLSF 当万能药**：小内存（<几 KB）场景它的元数据占比过高，小堆 memheap 更划算。
- **slab 当通用堆用**：slab 是内核小对象的快车道，应用大块请走 TLSF/memheap，硬塞变长数据会让 slab 的"碎片免疫"失效。

## 短自测

1. 为什么说 slab 是"碎片免疫"？
<details><summary>参考答案</summary>slab 为每种固定尺寸的对象开独立"快车道"：同尺寸块归还后和被请求尺寸完全匹配，不存在"小请求塞不进大洞"或"大请求拼不上小洞"。外部碎片不会产生，内部碎片被"同尺寸群体"摊薄。</details>

2. TLSF 的"近 O(1)"为什么不是绝对 O(1)？
<details><summary>参考答案</summary>位图扫描和邻块合并都是常数级操作，但常数较大且边界情况下位图扫描的步数不是严格固定。TLSF 的工程价值是"最坏情况常数上界被压住"，对实时系统这就足够当成"确定性"用。</details>

3. 内存池的 O(1) 是怎么做到的？代价是什么？
<details><summary>参考答案</summary>alloc 摘空闲链表头、free 放回链表头，无查表无合并无位图扫描，所以 O(1)。代价是块大小一刀切：按"最大成员+对齐"定，宁大勿小，放不下 alloc 直接失败或挂起等待。变长需求回 TLSF。</details>

4. `RT_USING_HEAP` 关掉后，哪些 API 不能再调用？固件怎么写？
<details><summary>参考答案</summary>所有 *_create 系列动态创建路径（rt_sem_create/rt_thread_create/rt_mp_create 等）编译不进来。固件要全静态：用 *_init 系列自备内存创建对象，任务栈用静态数组，零堆形态适合安全关键场景。</details>

5. RT-Thread 的 TLSF 与调度器的二级位图有什么思想上的同源？
<details><summary>参考答案</summary>两者都用"位图+CLZ 把'找最值'压成常数级"：调度器用二级位图找最高优先级就绪线程（rt_thread_ready_priority_group + rt_thread_ready_table），TLSF 用两级位图找最小够用的空闲块。同一个工程美学，两副面孔。</details>

## 对照表：本章概念 → 源码落点

| 概念 | 落点（以 RT-Thread 5.x 官方源码为准） |
|---|---|
| memheap 多段拼接 | `src/memheap.c` |
| slab 内核小对象 | `src/slab.c`（按对象类型分快车道） |
| TLSF 两级位图 | `src/tlsf.c`（TLSF 算法实现） |
| 内存池 rt_mp | `src/mempool.c`（rt_mp_create/init/alloc/free） |
| 静态创建 | `*_init` 系列 API（rt_sem_init/rt_thread_init/rt_mp_init） |
| RT_USING_HEAP 关堆 | Kconfig 选项；关掉后 *_create 不可用 |
| 监控命令 | finsh list_memheap/list_memp/rt_memory_info |
| 二级位图同源 | TLSF 两级位图 vs [R1](01-thread-sched.md) 调度二级位图 |
| 对照 FreeRTOS | [F7](../freertos/07-heap.md) heap_1~5 vs 三套分治 |

## 延伸阅读

三套策略背后的论文：

- **[\[D3\]](../../reference/bibliography.md#papers)** Masmano et al. 2004 — TLSF 原始论文：两级位图索引、O(1) 分配/释放、碎片有界的证明。
- **[\[D4\]](../../reference/bibliography.md#papers)** Wilson et al. 1995 — 小内存堆、slab、memheap 三套策略背后的通用权衡。

## 你做到了

- 内存管理的"确定性"维度被量化；
- 两套 OS 的内存哲学在你脑中完成对照。

平的那条线姓 mp：固定块、空闲链表，摘头就走，一万次一个价。抖的那条不是坏，是通用堆在替灵活性付账；确定性，是要用一刀切的块大小换的。

<div class="achievement">
✅ 下一站：<a href="04-device.html">R4 设备框架</a>，RT-Thread 最灵魂的一章：驱动与应用如何解耦。
</div>

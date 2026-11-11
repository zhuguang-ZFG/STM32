---
title: F7 内存管理：heap_1 到 heap_5 的人生选择
status: done
difficulty: 3
minutes: 50
---

# F7 内存管理：heap_1 到 heap_5 的人生选择

> 🎯 FreeRTOS 给了你五份"内存管理员"简历：从"只进不出的守财奴"（heap_1）到"会拼碎片的清洁工"（heap_4）再到"跨区调度的大管家"（heap_5）。选谁，取决于你的产品敢不敢承受"分配失败"与"碎片"这两件事。

## 本章精髓

1. **heap_1→heap_5 的能力阶梯**：只分配不释放（确定性无敌）→ 可释放不合并（碎片制造机）→ 包 libc 的 malloc（线程安全包装）→ 释放+相邻合并（碎片可控，嵌入式默认答案）→ 多区域堆（SRAM+CCM 分而治之）。
2. **碎片是时间的敌人**：长期运行产品里，"现在够用"不等于"一年后还够"。监控有两个指标要分清：**剩余总量**（`xPortGetFreeHeapSize`）和**历史最小剩余**（`xPortGetMinimumEverFreeHeapSize`），后者只在 heap_4/heap_5 上有，而且它是"水位最低点"，不是"碎片率"。
3. **动态任务的栈就是从堆里来的**：`xTaskCreate` 内部 `pvPortMalloc` 栈和 TCB（[F1](01-task-tcb.md) 创建六步的第 1、2 步）。"栈不在堆里"的说法只适用于**静态分配**的任务栈和 MSP 主栈，别把两种栈混为一谈。

- **能理解**：为什么"总空闲够"不等于"能分出大块"；为什么历史最小剩余量不是碎片率；为什么 heap_2 没有那个指标 API。
- **能用**：给"参数表/任务创建/图形缓冲"三个场景各选一版 heap；用场景 5 亲手看到碎片与合并。

## 先修

- [F1 任务栈](01-task-tcb.md)、[C1 内存模型](../../c/01-memory-model.md)、[B3 链接脚本](../../build/03-linker-script.md)。

## 先跑起来（10 分钟 quick win）

`code/rtos/01-freertos-lab` 场景 5：

```bash
make DEMO_SCENE=5 flash
```

串口日志就是证据链：`boot free` → `after ABC` → `after free B`（总空闲涨了，但 `big ok?=0`，最大连续块不够）→ `after free A`（A 与 B 相邻，heap_4 合并）→ `big ok?2=1`。

先押个接头：heap_4 凭什么知道 A、B 该不该焊成一块？释放的块按什么规矩找邻居？押完看第二节的合并算法。

## 动画：相邻块合并，不相邻块留洞

heap_4 的空闲链表**按地址排序**，释放时插回去：前后相邻就合并成一块，不相邻就留洞。盯住"总空闲"和"最大连续块"两个数字，它们经常不一样大。

![heap_4 合并动画](/anim/heap4-coalesce.svg)

## 版本与配置前提

- 内核：上游 **FreeRTOS-Kernel V11.1.0**，内存分配 `portable/MemMang/heap_4.c`。
- 本工程 `configTOTAL_HEAP_SIZE = 16KB`，`configSUPPORT_DYNAMIC_ALLOCATION=1`。
- 指标 API 按实际文件核对（见对照表），不凭印象书写。

## 小节结构

| 小节 | 内容 | 四件套 |
|---|---|---|
| 一、五版简历 | 能力/确定性/碎片三轴对照表 | 配置 |
| 二、heap_4 合并算法 | 空闲链表按地址排序 + 相邻合并源码逻辑 | 库解析 |
| 三、碎片实验 | 场景 5 的分配/释放/合并证据链 | 代码分析 |
| 四、栈溢出检测 | canary 原理；hook 函数与 S16 联动取证 | 代码分析 |
| 五、heap_5 多区 | SRAM+CCM 双区配置；哪类数据放哪区 | 配置 |
| 六、监控与兜底 | 两个指标的区别；分配失败时的产品级处理 | 代码分析 |

## 一、五版简历：能力阶梯

| 版本 | 分配 | 释放 | 合并 | 确定性 | 碎片 | 适合 |
|---|---|---|---|---|---|---|
| heap_1 | ✅ | ❌ | — | 无敌 | 不产生（也没法用） | 一次性分配的初始化 |
| heap_2 | ✅ | ✅ | ❌ | 好 | 制造机 | 短期演示，别上长期产品 |
| heap_3 | 包 libc malloc | ✅ | 看 libc | 看 libc | 看 libc | 快速原型 |
| heap_4 | ✅ | ✅ | ✅ 相邻合并 | 好 | 可控 | **嵌入式默认答案** |
| heap_5 | ✅ | ✅ | ✅ | 好 | 可控 | 多区域（SRAM+CCM） |

## 二、heap_4 合并算法：按地址排序 + 相邻就拼

地契先看图：链表按地址排，隔着已用块的两洞拼不上，前后邻上的才焊得成一块。

![heap_4 空闲链表：ucHeap 里已用块与空闲块交替，xFreeList 按地址排序，相邻空闲块合并，两个指标都从这条链表读](/arch/heap-free-list.png)

heap_4 的空闲链表**按地址从小到大排序**（不是按大小）。释放时 `prvInsertBlockIntoFreeList`（V11.1.0 `heap_4.c:492`）做三件事：

1. 找到插入位置（按地址）；
2. **前邻块**的尾地址若正好接上我，就并进前邻块；
3. **后邻块**的首地址若正好接上我，就把它也并进来。

推论：**只有相邻的空闲块才会合并**。交替分配释放留下的"洞"，永远不会自动拼成大块，这就是碎片的物理来源。

### heap_4 源码走读：prvInsertBlockIntoFreeList

释放时的合并逻辑（`heap_4.c:492`）用三行 C 完成：

```c
/* 空闲链表按地址排序。pxBlockToInsert 是刚释放的块。*/

/* 1. 找到插入位置：遍历链表，找到第一个地址比我大的块 */
pxIterator = (BlockLink_t*)&xStart;
while (pxIterator->pxNextFreeBlock < pxBlockToInsert) {
    pxIterator = pxIterator->pxNextFreeBlock;
}

/* 2. 后邻块：我后面那块如果是空闲的，且紧挨着我 → 合并 */
pxNextBlock = (uint8_t*)pxBlockToInsert + pxBlockToInsert->xBlockSize;
if ((uint8_t*)pxIterator->pxNextFreeBlock == pxNextBlock) {
    /* 把后邻块从链表摘除，大小加到我头上 */
    pxBlockToInsert->xBlockSize += pxIterator->pxNextFreeBlock->xBlockSize;
    pxIterator->pxNextFreeBlock = pxIterator->pxNextFreeBlock->pxNextFreeBlock;
}

/* 3. 前邻块：我前面那块如果是空闲的，且紧挨着我 → 合并 */
pxPrevBlock = (uint8_t*)pxIterator + pxIterator->xBlockSize;
if ((uint8_t*)pxPrevBlock == (uint8_t*)pxBlockToInsert) {
    /* 把我加到前邻块头上 */
    pxIterator->xBlockSize += pxBlockToInsert->xBlockSize;
} else {
    /* 不邻接，正常插入链表 */
    pxBlockToInsert->pxNextFreeBlock = pxIterator->pxNextFreeBlock;
    pxIterator->pxNextFreeBlock = pxBlockToInsert;
}
```

**关键设计**：
- **边界标记法**：每个块的头部存 `xBlockSize`（含头部自身大小），通过"前块地址 + 前块大小"就能找到当前块的起始位置，不需要双向链表。
- **首次适配**：分配时从链表头开始找，第一个够大的就用。简单、快，但容易产生碎片。
- **O(n) 遍历**：释放和分配都要遍历链表。对于嵌入式的小堆（几 KB 到几十 KB），这比复杂数据结构的开销更划算。

## 静态分配：xTaskCreateStatic —— 零动态分配的安全答案

安全关键系统（汽车、医疗、航空）不允许运行时分配失败。FreeRTOS 提供**静态创建 API**：调用方自己提供 TCB 和栈的存储，内核零 malloc。

```c
/* 静态分配：调用方提供所有存储 */
static StaticTask_t taskTCB;                    // TCB 结构体
static StackType_t taskStack[256];              // 栈数组（256 × 4 = 1024 字节）

TaskHandle_t handle = xTaskCreateStatic(
    sensor_task,        // 函数
    "sensor",           // 名字
    256,                // 栈深（字数，不是字节）
    NULL,               // 参数
    2,                  // 优先级
    taskStack,          // ← 栈数组
    &taskTCB            // ← TCB 存储
);
configASSERT(handle != NULL);                   // 永远成功，不会返回 NULL
```

**与动态创建的对比**：

| | xTaskCreate（动态） | xTaskCreateStatic（静态） |
|---|---|---|
| TCB 来源 | `pvPortMalloc` 从堆分配 | 调用方提供 `StaticTask_t` |
| 栈来源 | `pvPortMalloc` 从堆分配 | 调用方提供 `StackType_t[]` |
| 分配失败 | 可能（堆不够） | **不可能**（编译期确定） |
| 内存释放 | `vTaskDelete` 归还堆 | 不释放（静态生命周期） |
| 配置宏 | `configSUPPORT_DYNAMIC_ALLOCATION=1` | `configSUPPORT_STATIC_ALLOCATION=1` |
| 适合 | 原型开发、非关键任务 | 安全关键、长期运行产品 |

**静态分配的代价**：
- 每个任务的 TCB + 栈在编译期就占好 RAM，不能运行时增减任务。
- 需要实现 `vApplicationGetIdleTaskMemory` 和 `vApplicationGetTimerTaskMemory`，为内核的 Idle 和 Timer 任务提供静态存储。

```c
/* 必须实现：为 Idle 任务提供静态存储 */
void vApplicationGetIdleTaskMemory(StaticTask_t **ppxIdleTaskTCB,
                                    StackType_t **ppxIdleTaskStack)
{
    static StaticTask_t idleTCB;
    static StackType_t idleStack[configMINIMAL_STACK_SIZE];
    *ppxIdleTaskTCB = &idleTCB;
    *ppxIdleTaskStack = idleStack;
}
```

**选型建议**：长期产品优先静态分配（零失败风险）。如果必须动态创建任务（如运行时加载插件），用 heap_4 + 严格的 `configTOTAL_HEAP_SIZE` 计算 + `xPortGetMinimumEverFreeHeapSize` 监控。

![heap_4 空闲链表：按地址排序，释放时只有相邻空闲块才合并；不相邻的洞保留](/figures/rtos-freertos-07-heap.svg)

## 三、碎片实验：总空闲 ≠ 最大连续块

场景 5 的完整证据链（串口日志）：

| 步骤 | 操作 | 观察 |
|---|---|---|
| 1 | 启动 | `boot free` ≈ 16KB（减去 TCB/栈等内核开销） |
| 2 | 连续分配 A/B/C 各 1KB | `after ABC` 掉了 ~3KB |
| 3 | 释放 B（中间那块） | `after free B` 涨了 ~1KB，但**总空闲够 2KB，最大连续块不够** |
| 4 | 要一块 2KB | `big ok?=0` —— 失败 |
| 5 | 释放 A（与 B 相邻） | heap_4 合并 A+B |
| 6 | 再要 2KB | `big ok?2=1` —— 合并后成了 |

**这就是"总空闲 ≠ 最大可分配块"的实验证据**。原文档里"动态任务栈来自堆"与"不在堆里"自相矛盾的表述，根子也在这里：动态任务的栈确实从 heap_4 的池子里 `pvPortMalloc` 出来（[F1](01-task-tcb.md)），碎片化直接影响你能不能建新任务。

## 四、栈溢出检测：canary 是更早的哨兵

`configCHECK_FOR_STACK_OVERFLOW=2` 开满后，每次上下文切换时内核检查栈底附近的 0xA5 水位线是否被踩。踩了就调 `vApplicationStackOverflowHook(任务句柄, 任务名)`，本工程打印任务名后停住。

为什么需要它：**爆栈的第一现场往往不是 HardFault，而是"悄悄踩了邻居的数据"**：任务函数读到一个莫名其妙的值、通信偶尔丢包、日志里出现乱码。等 HardFault 再查，现场已经被踩得面目全非。canary 在踩的那一瞬间就抓人。

## 五、heap_5 多区：SRAM 和 CCM 分而治之

heap_5 允许把堆拆成多个区域（HeapRegion 表）：比如 SRAM 放常规分配，CCM（0x10000000 的 64KB，CPU 直连）放实时性敏感的数据。前提是**这些区域 DMA 够不着**（回 [S8](../../stm32/08-dma.md) 的 CCM 禁区），所以 CCM 里绝对不能放 DMA 缓冲区。

## 六、监控与兜底：指标 API 不是每个版本都有

逐文件核对后的可用性（V11.1.0）：

| 指标 | heap_1 | heap_2 | heap_4 | heap_5 |
|---|---|---|---|---|
| `xPortGetFreeHeapSize` | ✅ | ✅ `:334` | ✅ | ✅ `:435` |
| `xPortGetMinimumEverFreeHeapSize` | ❌ | ❌ | ✅ `:413` | ✅ `:441` |

两个指标的区别：

- **FreeHeapSize**：现在还剩多少（瞬时值）；
- **MinimumEverFreeHeapSize**：历史最低水位（峰值压力），它回答的是"最坏的时候有多紧张"，**不是碎片率**。碎片率要自己用"最大连续块/总空闲"估。

产品级兜底：分配失败不许静默。要么进安全态，要么记日志告警，要么重启看门狗。静默往下跑，后面全是玄学。

## 七、堆大小怎么算：从拍脑袋到工程预算

`configTOTAL_HEAP_SIZE` 的预算公式：

```
总堆 = Σ(任务栈 × 字数 × 4) + Σ(TCB × ~400B) + Σ(队列深度 × 项大小) + 信号量/事件组 + 安全余量(30%)
```

**实操步骤**：

1. **列任务清单**：每个任务的栈深（用 `uxTaskGetStackHighWaterMark` 实测，不是猜）；
2. **列通信对象**：队列深度 × 项大小、信号量数量、事件组数量；
3. **加安全余量**：总需求 × 1.3，留给付给碎片和未来扩展；
4. **检查 .bss 冲突**：堆和 .bss 共享 SRAM，堆太大会挤占全局变量空间，看链接脚本的 MEMORY 定义。

**反模式**：`configTOTAL_HEAP_SIZE = 64KB`，理由是"反正 Flash 够大"。SRAM 只有 128KB（F407），堆占一半，.bss 和栈就没地方了。

## 八、长期运行产品的堆监控策略

产品上线后，堆的健康度要持续监控，不是开发时看一眼就完事：

**周期性巡检**（每 10 分钟或每小时）：

```c
void heap_health_check(void) {
    size_t free_now = xPortGetFreeHeapSize();
    size_t free_min = xPortGetMinimumEverFreeHeapSize();
    
    // 趋势告警：当前值逼近历史最低
    if (free_now < free_min * 1.2) {
        LOG_WARN("heap tension: %u free, %u min-ever", free_now, free_min);
    }
    
    // 绝对告警：低于安全阈值
    if (free_now < 1024) {  // 1KB 安全线，按产品调整
        LOG_ERROR("heap critical: %u bytes left", free_now);
    }
}
```

**碎片率估算**（heap_4/heap_5 才有意义）：

```c
// 分配一块测试内存，看实际能拿到多大
void* test = pvPortMalloc(4096);
if (!test) {
    LOG_WARN("fragmentation: can't alloc 4KB, but free=%u", xPortGetFreeHeapSize());
}
vPortFree(test);
```

**数据记录**：把 `free_now` 和 `free_min` 写进 NVS 或日志，跑一周看曲线；如果 `free_now` 持续下降不回升，说明有内存泄漏。

## 九、GDB 调试堆与栈溢出

堆和栈的问题在 GDB 里能直接看到证据：

```bash
# 查看堆的当前状态
(gdb) p xPortGetFreeHeapSize()
$1 = 12480    # 还剩 12KB

(gdb) p xPortGetMinimumEverFreeHeapSize()
$2 = 8192     # 历史最低 8KB

# 查看堆池起始地址（heap_4）
(gdb) p ucHeap
$3 = (uint8_t[16384]) @ 0x20004000

# 查看任务的栈底（溢出检查用）
(gdb) p pxCurrentTCB->pxStack
$4 = (StackType_t *) 0x20001800    # 栈底

# 看栈里有没有被踩（正常应该填 0xA5）
(gdb) x/32xb 0x20001800
0x20001800: 0xa5 0xa5 0xa5 0xa5 0xa5 0xa5 0xa5 0xa5
0x20001808: 0xa5 0xa5 0xa5 0xa5 0x48 0x65 0x6c 0x6f  ← 被踩了！
```

**栈溢出取证**：如果 `vApplicationStackOverflowHook` 被触发，GDB 里看调用栈：

```bash
(gdb) break vApplicationStackOverflowHook
(gdb) continue
# 触发后
(gdb) bt
#0  vApplicationStackOverflowHook
#1  vTaskSwitchContext
#2  PendSV_Handler    ← 上下文切换时发现的
(gdb) p pxCurrentTCB->pcTaskName
$5 = "sensor_task\000..."    ← 肇事者
```

**调试纪律**：栈溢出第一现场往往不是 HardFault，而是"数据莫名其妙错了"。看到灵异现象，先用 GDB 查栈底有没有被踩。

## 附录：工程完整源码

<<< ../../../code/rtos/01-freertos-lab/main.c

## 记忆锚点

::: tip 一句话记住
**heap_1 只进不出，heap_4 会合并，heap_5 跨区管；碎片看曲线，爆栈靠哨兵，剩多少问 FreeHeapSize，最坏多紧张问 MinimumEver。**
:::

**延伸**：堆管理与链接脚本的堆区预留（[B3](../../build/03-linker-script.md)）相关；嵌入式慎用 malloc 的原因见 [C0](../../c/00-c-in-mcu.md)；内存池的确定性替代方案见 RT-Thread（[R3](../rtthread/03-mem.md)）。

## 实物实验

- 场景 5 完整跑一遍，把日志抄进实验记录；
- 对比实验：把 Makefile 里 `heap_4.c` 换成 `heap_2.c` 再跑，`xPortGetMinimumEverFreeHeapSize` 直接编译不过（heap_2 没有这个 API），这就是"指标 API 要逐文件核对"的现场教学；
- 爆栈捕获：把某任务的栈深从 256 改到 64，看 OverflowHook 抓到谁。

## 常见坑

- **heap_2 用于长期运行产品**：碎片无解，跑着跑着分配失败，长期产品直接 heap_4；
- **configTOTAL_HEAP_SIZE 拍脑袋**：按"任务栈总和 + 队列 + 余量 30%"算，不是越大越好（挤占 .bss）；
- **把历史最小剩余当碎片率**：它是"最坏水位"，不是"碎片程度"，两者都要看；
- **栈溢出只信 HardFault**：很多时候爆栈先踩邻居数据，静默错乱，canary 是更早的哨兵；
- **中断里 pvPortMalloc**：堆分配非原子且可能耗时，ISR 禁地，预先静态分配；
- **CCM 里放 DMA 缓冲区**：DMA 够不着 CCM，数据静悄悄丢失。

## 短自测

1. heap_4 释放一块内存时，什么情况下会合并？
<details><summary>参考答案</summary>只有当被释放的块与空闲链表中的块**地址相邻**时才合并（前邻接尾或后邻接头）。不相邻就留洞，这就是碎片的物理来源。落点：heap_4.c 的 prvInsertBlockIntoFreeList。</details>

2. "总空闲还有 4KB"为什么不能保证能分出 2KB？
<details><summary>参考答案</summary>空闲可能碎成多块不连续的小块。分配器要的是**最大连续块**，不是总空闲。场景 5 的第 3、4 步就是证据。</details>

3. `xPortGetMinimumEverFreeHeapSize` 在哪些 heap 版本上有？它回答的是什么问题？
<details><summary>参考答案</summary>只有 heap_4 和 heap_5 有（V11.1.0 逐文件核对）。它回答"历史最低水位是多少"，峰值压力有多大，不是碎片率。</details>

4. 动态创建的任务，它的栈存在哪里？静态创建的呢？
<details><summary>参考答案</summary>动态创建（xTaskCreate）的栈由内核 pvPortMalloc 从 heap_4 的池子里分；静态创建（xTaskCreateStatic）的栈由调用方提供的静态数组给。MSP 主栈（中断用）在链接脚本里，与堆无关。"栈不在堆里"只对后两种成立。</details>

<QuizBank chapter="f7-heap" />

## 对照表：本章概念 → 仓库与上游落点

| 概念 | 落点 |
|---|---|
| heap_4 相邻合并 | 上游 V11.1.0 `portable/MemMang/heap_4.c:492`（prvInsertBlockIntoFreeList） |
| 指标 API 可用性 | 同上逐文件核对：heap_1:149、heap_2:334、heap_4:413、heap_5:435/441 |
| 动态任务栈来自堆 | 上游 V11.1.0 `tasks.c:1718`（xTaskCreate → pvPortMalloc） |
| 碎片实验 | [code/rtos/01-freertos-lab](https://github.com/zhuguang-ZFG/STM32/tree/main/mcu/code/rtos/01-freertos-lab) 场景 5 |
| 动画 | [heap4-coalesce.svg](/anim/heap4-coalesce.svg) |

## 延伸阅读

五份简历背后的分配器理论：

- **[\[D4\]](../../reference/bibliography.md#papers)** Wilson et al. 1995 — 分配器综述：首次适配/最佳适配/隔离适配各自的碎片代价，heap_4 为什么选"首次适配 + 相邻合并"。
- **[\[E5\]](../../reference/bibliography.md#books)** Knuth TAOCP Vol.1 §2.5 — 边界标记法与伙伴系统，heap_4 合并相邻空闲块的祖师爷。
- **[\[D3\]](../../reference/bibliography.md#papers)** Masmano et al. 2004 — TLSF：RT-Thread 走的另一条路（O(1)、碎片有界），与 heap_4 对照着看。

## 你做到了

- 内存从"够不够"的焦虑变成"可测可控"的工程；
- "总空闲 ≠ 最大连续块"亲手见过一次；
- FreeRTOS 内核篇收官，你已经读完一个真实 RTOS 的全部核心机制。

接头在空闲链表：释放的块按地址排进去，前后一探，门对门就焊成一整块，隔一个邻居就留洞。总空闲是账面，最大连续块才是能住人的房。

<div class="achievement">
✅ 下一站：<a href="08-port-f407.html">F8 移植到霸天虎</a>：把前面所有机制在你的板上拼起来跑。
</div>

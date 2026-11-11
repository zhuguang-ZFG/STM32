# F3 调度器：一条 CLZ 选出下一个任务 — 视频脚本分镜

> 目标时长：12–15 分钟 | 平台：B站 | 受众：学过 FreeRTOS 但没读过源码的人
> 核心卖点：**"32 个优先级挑最高的，要遍历几遍？"**——通用版 O(n) vs M4F 版 O(1)，一条 CLZ 指令的魔法

---

::: warning 本页是旧产线留下的分镜，成片已经不按它走
这一集的现行事实源是 [`video/episodes/f3-scheduler/episode.json`](https://github.com/zhuguang-ZFG/mcu/blob/main/video/episodes/f3-scheduler/episode.json)，取证是 [`code/rtos/03-scheduler/probe.sh`](https://github.com/zhuguang-ZFG/mcu/blob/main/code/rtos/03-scheduler/probe.sh)（`sh probe.sh`，不需要开发板，只要交叉编译器加一份上游 FreeRTOS-Kernel V11.1.0）。页内四处与本机实测不符，留档不照做：

- **`__CLZ` 不是这个端口里的名字**：GCC 的 ARM_CM4F 端口用的是 `ucPortCountLeadingZeros`（`portmacro.h:151`，函数体里一条 `clz %0, %1` 在 `:155`），选优宏 `portGET_HIGHEST_PRIORITY` 在 `:171`；
- **附录那三条命令跑不通**：`code/rtos/freertos/03-scheduler/` 这个目录和里面的 `generic.c` / `m4f.c` / `tick.c` 都不存在。真办法不是手写三份等价 C，而是把内核的 `tasks.c` 按 `configUSE_PORT_OPTIMISED_TASK_SELECTION` 取 0 和 1 各编一遍，再逐条对照两份 `tasks.o`；
- **`scheduler-ready-list.svg` / `scheduler-tick.svg` 两张图站内不存在**，这一集实际用的动画是 `systick-tick`、`list-insert`、`rtt-bitmap-256`、`vtaskdelay-lifecycle`；
- **「遍历几遍」这个问法要换成实测**：两条路径的选优函数 `.text.vTaskSwitchContext` 分别是 140 / 160 字节，机身 58 条指令零回边 / 70 条指令一条回边；同一个 5 级事件表，通用路径平均摸 2.10 下、最坏 5 下，32 级最坏摸 31 下，位图路径永远 1 下。
:::

## 片头（0:00–0:50）—— 钩子

**画面**：黑屏，一行白字逐字打出：

```c
while (listLIST_IS_EMPTY(&pxReadyTasksLists[uxTopPriority])) {
    --uxTopPriority;
}
```

**旁白**：
"FreeRTOS 选下一个任务，就是找'最高的非空就绪链表'。这段代码，从 uxTopPriority 开始往下找，最坏要遍历 32 次。"

**画面**：代码高亮，uxTopPriority 从 31 递减到 0，每次检查链表是否为空。

**旁白**：
"但如果你用 Cortex-M4，FreeRTOS 给了另一个答案——一条 CLZ 指令，O(1)，与任务数无关。"

**画面**：代码切换成 M4F 版本：

```c
uxTopPriority = 31UL - __CLZ(uxReadyPriorities);
```

**旁白**：
"今天这期，我们把调度器的双实现拆开看，用源码和汇编取证，把位图 + CLZ 的魔法讲透。"

**[片头动画 / LOGO]**

---

## 第一幕（0:50–3:30）—— 就绪表 = 链表数组 + 速查器

**画面**：`scheduler-ready-list.svg` 动画——32 个链表并排，每个链表是一个就绪队列。

**旁白**：
"FreeRTOS 的就绪表，本质是一个链表数组——`pxReadyTasksLists[configMAX_PRIORITIES]`。优先级 0 的链表在最下面，优先级 31 的在最上面。"

**画面**：动画里每个链表里挂着几个任务（TCB 方块），优先级越高位置越高。

**旁白**：
"调度器要做的，就是找'最高的非空链表'。这个'找'的动作，有两种实现。"

**画面**：动画分成左右两半，左边标"通用版"，右边标"M4F 版"。

**旁白**：
"通用版用一个标量 uxTopReadyPriority 记录当前最高优先级，每次从它开始往下找。"

**画面**：左边动画里，uxTopReadyPriority 是一个数字 31，箭头从 31 开始往下扫描。

**旁白**：
"M4F 版用一个 32 位位图 uxReadyPriorities，第 N 位 = 1 表示优先级 N 有任务。找最高优先级，就是一条 CLZ 指令。"

**画面**：右边动画里，uxReadyPriorities 是一个 32 位二进制数，某些位是 1。CLZ 指令从高位开始数 0，找到第一个 1。

---

## 第二幕（3:30–6:30）—— 通用版：标量 + 递减扫描

**画面**：切到 FreeRTOS 源码（tasks.c），展示通用版的宏定义。

```c
#define taskRECORD_READY_PRIORITY( uxPriority ) \
do {                                            \
    if( ( uxPriority ) > uxTopReadyPriority )   \
    {                                           \
        uxTopReadyPriority = ( uxPriority );    \
    }                                           \
} while( 0 )
```

**旁白**：
"通用版里，uxTopReadyPriority 只是一个标量。每当有任务就绪，这个宏会比较并更新最高优先级。"

**画面**：代码高亮，动画展示 uxTopReadyPriority 从 5 更新到 7。

**旁白**：
"调度时，从 uxTopReadyPriority 开始往下找非空链表——"

**画面**：切到调度代码：

```c
while (listLIST_IS_EMPTY(&pxReadyTasksLists[uxTopPriority])) {
    --uxTopPriority;
}
```

**旁白**：
"如果优先级 7 的链表是空的，就找 6；6 也是空的，就找 5……最坏情况要遍历 32 次。"

**画面**：动画展示扫描过程，uxTopPriority 从 31 递减，每次检查链表是否为空。

**旁白**：
"这是 O(n) 的算法，n = configMAX_PRIORITIES。任务数少的时候没问题，但优先级多了，性能就会下降。"

**[取证环节]**

**画面**：切到终端，`arm-none-eabi-gcc -O2 -S` 编译通用版调度代码。

**旁白**：
"我们看汇编——这是一个循环，每次检查链表是否为空，不是就递减。最坏情况 32 次循环。"

**画面**：汇编代码高亮，循环体用红色框标出。

---

## 第三幕（6:30–10:00）—— M4F 版：位图 + CLZ 一条指令

**画面**：切到 FreeRTOS 源码（portmacro.h），展示 M4F 版的宏定义。

```c
#define portRECORD_READY_PRIORITY( uxPriority, uxReadyPriorities )  \
    ( uxReadyPriorities ) |= ( 1UL << ( uxPriority ) )
```

**旁白**：
"M4F 版里，uxReadyPriorities 是一个 32 位位图。每当有任务就绪，就把对应的位设 1。"

**画面**：代码高亮，动画展示位图的变化——优先级 7 就绪，bit 7 置 1；优先级 3 就绪，bit 3 置 1。

**旁白**：
"调度时，找最高优先级，就是一条 CLZ 指令——"

**画面**：切到调度代码：

```c
uxTopPriority = 31UL - __CLZ(uxReadyPriorities);
```

**旁白**：
"CLZ 是 Count Leading Zeros，数前导零。31 减去前导零个数，就是最高置位的位置。"

**画面**：动画展示 CLZ 的过程——位图 0b10000000...10001000，从高位开始数 0，数了 0 个 0 就遇到 1，所以 CLZ = 0，最高优先级 = 31 - 0 = 31。

**旁白**：
"这是一条硬件指令，O(1)，与任务数无关。代价是位图只有 32 位，所以此路径要求 configMAX_PRIORITIES ≤ 32。"

**[取证环节]**

**画面**：切到终端，`arm-none-eabi-gcc -O2 -S -mcpu=cortex-m4` 编译 M4F 版调度代码。

**旁白**：
"我们看汇编——就是一条 CLZ 指令，没有循环。"

**画面**：汇编代码高亮，CLZ 指令用绿色框标出。

**旁白**：
"这就是'把活推给硬件'的设计哲学——能用一条指令解决的，绝不写循环。"

---

## 第四幕（10:00–12:30）—— tick 中断：三件事

**画面**：`scheduler-tick.svg` 动画——SysTick 中断触发，xTaskIncrementTick 函数执行。

**旁白**：
"调度器的另一件大事，是 tick 中断。每次 SysTick 触发，xTaskIncrementTick 做三件事——"

**画面**：动画分三步展示：
1. tick 计数器++
2. 查延时链表队首，谁该醒了
3. 必要时请求上下文切换

**旁白**：
"第一件，节拍计数器++。这个简单。"

**画面**：动画里 xTickCount 从 100 变成 101。

**旁白**：
"第二件，查延时链表队首，看谁该醒了。延时链表按唤醒时间排序，队首是最早该醒的。"

**画面**：动画里延时链表，队首任务的唤醒时间 = 101，当前 tick = 101，所以该醒了。

**旁白**：
"如果队首的唤醒时间 > 当前 tick，就不用查了——这是 O(1) 的秘密。"

**画面**：代码高亮：

```c
if (xNextTaskUnblockTime <= xTickCount) {
    // 查延时链表
}
```

**旁白**：
"第三件，如果有任务被唤醒，或者时间片轮转，就请求上下文切换。"

**画面**：动画里 PendSV 中断被触发，上下文切换开始。

**旁白**：
"这就是调度器的全部——位图选最高优先级，tick 中断醒人、轮转、换片场。"

---

## 第五幕（12:30–14:00）—— vTaskDelay 的真相

**画面**：切到 vTaskDelay 源码。

```c
void vTaskDelay( const TickType_t xTicksToDelay ) {
    // 挂进延时链表
    vListInsert(pxDelayedTaskList, &(pxCurrentTCB->xStateListItem));
    // 让出 CPU
    taskYIELD();
}
```

**旁白**：
"vTaskDelay 不是'等'，是'搬'——把自己挂进延时链表，然后让出 CPU。"

**画面**：动画展示任务从就绪链表移动到延时链表，然后 CPU 切换到其他任务。

**旁白**：
"任务真的'不在'了，这是 RTOS 延时与裸机死等的本质区别。"

**画面**：对比动画——左边裸机延时，CPU 在空转；右边 RTOS 延时，CPU 在做其他任务。

**旁白**：
"裸机的 `for` 循环延时，CPU 在空转，什么都干不了。RTOS 的 vTaskDelay，CPU 去跑其他任务，效率翻倍。"

---

## 片尾（14:00–15:00）—— 总结

**画面**：三个盒子并排：位图 + CLZ（O(1) 选最高）、tick 三件事（醒人、轮转、换片场）、vTaskDelay（搬，不是等）。

**旁白**：
"调度器的聪明，全在'把活推给硬件'的设计里——位图 + CLZ，一条指令选最高优先级。"

**画面**：大字浮现：**"位图置位 CLZ 秒选，tick 三事：醒人、轮转、换片场"**

**旁白**：
"记住这句口诀，你就能看懂 FreeRTOS 调度器的全部源码。"

**旁白**：
"所有源码和汇编取证，都在本站的 F3 章节，你可以自己复现。我们下期见。"

**[片尾动画 / LOGO]**

---

## 附录：取证命令

```bash
# 通用版调度取证
cd code/rtos/freertos/03-scheduler
arm-none-eabi-gcc -std=c11 -O2 -S -o generic.O2.s generic.c

# M4F 版调度取证
arm-none-eabi-gcc -std=c11 -O2 -mcpu=cortex-m4 -S -o m4f.O2.s m4f.c

# tick 中断取证
arm-none-eabi-gcc -std=c11 -O2 -S -o tick.O2.s tick.c
```

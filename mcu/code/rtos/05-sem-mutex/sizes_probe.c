/* sizes_probe.c —— 把 Queue_t / TCB_t 的形状逼成符号表里的数字
 *
 * 为什么要这个文件：这一集最核心的一句话是「互斥量和二值信号量不是两个结构体，
 * 是同一个 Queue_t 里同一个指针槽的两种用法」。这句话不能靠我念，得量。
 *
 * 量法沿用 06-timers 的仪器：Queue_t / TCB_t 都是 .c 文件内部的类型（queue.h 里
 * 只有 `struct QueueDefinition;` 一个前置声明），从外面看不见，所以只能把内核 .c
 * 原文 include 进来，再声明
 *     char probe_x[ 1 + __builtin_offsetof( Queue_t, 成员 ) ];
 * 数组的【符号大小】就是那个偏移 +1。+1 是因为 0 长度的数组编不过，而 pcHead 的
 * 偏移恰好是 0——probe.sh 读数时统一减 1，这个约定写死在这里。
 *
 *   - 为什么按 Cortex-M4 编：偏移和 sizeof 都是目标 ABI 的函数（指针 4 字节、
 *     UBaseType_t 4 字节），宿主机上量出来的偏移跟板子上花的不是同一张图；
 *   - 为什么 -O0：这些数与优化无关，用 -O0 只为和 probe.sh 其余机身同一把尺子；
 *   - 这些数组全落在 .bss，本文件永不参与链接，所以板子上一个字节都不占。
 *
 * 交叉核对（probe.sh 第 4、6 步）：nm 量到的偏移，要和 objdump 反汇编里那句
 * `str r?, [r?]`（偏移 0，无立即数）对上；sizeof(Queue_t) 要和 pvPortMalloc
 * 调用点的那个立即数对上。两条独立路子给同一个数，才算量的是内核，不是量自己。
 *
 * 事实基准：上游 FreeRTOS-Kernel tag V11.1.0。
 */

#include "queue.c"
#include "tasks.c"

/* ---- 主角的整体大小 ---- */
char probe_sizeof_Queue_t    [sizeof(Queue_t)];
char probe_sizeof_StaticQueue_t [sizeof(StaticQueue_t)];
char probe_sizeof_TCB_t      [sizeof(TCB_t)];
char probe_sizeof_SemaphoreData_t [sizeof(SemaphoreData_t)];
char probe_sizeof_QueuePointers_t [sizeof(QueuePointers_t)];

/* ---- Queue_t 前三个槽的偏移：pcHead / pcWriteTo / union u ---- */
char probe_off_pcHead      [1 + __builtin_offsetof(Queue_t, pcHead)];
char probe_off_pcWriteTo   [1 + __builtin_offsetof(Queue_t, pcWriteTo)];
char probe_off_u           [1 + __builtin_offsetof(Queue_t, u)];

/* ---- 联合体重叠本体：队尾指针与互斥量持有者是不是同一个 4 字节 ---- */
char probe_off_u_pcTail        [1 + __builtin_offsetof(Queue_t, u.xQueue.pcTail)];
char probe_off_u_xMutexHolder  [1 + __builtin_offsetof(Queue_t, u.xSemaphore.xMutexHolder)];
char probe_off_u_pcReadFrom    [1 + __builtin_offsetof(Queue_t, u.xQueue.pcReadFrom)];
char probe_off_u_uxRecursive   [1 + __builtin_offsetof(Queue_t, u.xSemaphore.uxRecursiveCallCount)];

/* ---- 决定"这是不是队列存储区"的两个数 ---- */
char probe_off_uxMessagesWaiting [1 + __builtin_offsetof(Queue_t, uxMessagesWaiting)];
char probe_off_uxLength          [1 + __builtin_offsetof(Queue_t, uxLength)];
char probe_off_uxItemSize        [1 + __builtin_offsetof(Queue_t, uxItemSize)];
char probe_off_xTasksWaitingToReceive [1 + __builtin_offsetof(Queue_t, xTasksWaitingToReceive)];

/* ---- TCB 里被继承机制摸到的那几个槽 ---- */
char probe_off_T_uxPriority       [1 + __builtin_offsetof(TCB_t, uxPriority)];
char probe_off_T_uxBasePriority   [1 + __builtin_offsetof(TCB_t, uxBasePriority)];
char probe_off_T_xStateListItem   [1 + __builtin_offsetof(TCB_t, xStateListItem)];
char probe_off_T_xEventListItem   [1 + __builtin_offsetof(TCB_t, xEventListItem)];
char probe_off_T_uxMutexesHeld    [1 + __builtin_offsetof(TCB_t, uxMutexesHeld)];

/* ---- ListItem_t 内部：搬表时改写的就是这几个字节（xStateListItem 起算的相对偏移）---- */
char probe_off_L_xItemValue   [1 + __builtin_offsetof(ListItem_t, xItemValue)];
char probe_off_L_pxNext       [1 + __builtin_offsetof(ListItem_t, pxNext)];
char probe_off_L_pxPrevious   [1 + __builtin_offsetof(ListItem_t, pxPrevious)];
char probe_off_L_pvOwner      [1 + __builtin_offsetof(ListItem_t, pvOwner)];
char probe_off_L_pvContainer  [1 + __builtin_offsetof(ListItem_t, pxContainer)];

/* ---- R4 那句 configMAX_PRIORITIES - 优先级：机身里那个 rsb #5 的 5 从哪来，量 ---- */
char probe_configMAX_PRIORITIES [1 + configMAX_PRIORITIES];

/* ---- 这颗旋钮本集唯一有意偏离 lab 的地方（lab 开定时器、这里关）。
      第 4 步拿 lab 的原样配置重编同一件仪器，先要证明那份配置【真的被吃进去了】，
      否则整条对照就是自我安慰。读数 = configUSE_TIMERS 本身。 ---- */
char probe_configUSE_TIMERS     [1 + configUSE_TIMERS];

/* ---- TRACE 门控的标签槽：TRACE=0 时这个成员根本不存在，所以整条包起来 ---- */
#if ( configUSE_TRACE_FACILITY == 1 )
    char probe_off_ucQueueType   [1 + __builtin_offsetof(Queue_t, ucQueueType)];
    char probe_off_uxQueueNumber [1 + __builtin_offsetof(Queue_t, uxQueueNumber)];
#endif

/* ---- 两条链表的形状：搬表搬的就是这两个字节数 ---- */
char probe_sizeof_List_t     [sizeof(List_t)];
char probe_sizeof_ListItem_t [sizeof(ListItem_t)];

/* ---- 宽度基准：指针和 UBaseType_t 在这颗核上各多大，量，不假定 ---- */
char probe_sizeof_ptr        [sizeof(void *)];
char probe_sizeof_UBaseType_t [sizeof(UBaseType_t)];

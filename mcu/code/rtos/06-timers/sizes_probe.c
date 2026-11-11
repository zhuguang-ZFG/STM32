/* sizes_probe.c —— 把内核自己知道的 sizeof 逼成符号表里的一个数字
 *
 * 为什么要这个文件：这一集要算"打开软件定时器到底花多少字节"。查文档、数结构体
 * 成员、按 AAPCS 手推对齐，都是"二手结论"。这里要的是一个字：量出来的。
 *
 * 量法：把内核的 .c 原文 include 进来（Timer_t / TCB_t / Queue_t / BlockLink_t
 * 都是 .c 内部的 static 类型，从外面看不见），然后声明一个
 *     char probe_sizeof_Xxx[ sizeof( Xxx ) ];
 * 这个数组的【符号大小】就等于 sizeof。arm-none-eabi-nm --print-size 直接读出来，
 * 不依赖 DWARF、不依赖优化等级、不依赖反汇编里的立即数落在哪个寄存器上。
 *
 *   - 为什么必须 include 内核 .c：这些类型是文件内 static，没有公开头文件；
 *   - 为什么按 Cortex-M4 编：sizeof 是目标 ABI 的函数（指针 4 字节、对齐 8），
 *     宿主机 x86-64 上量出来的数与板子上花的数不是一回事；
 *   - 为什么 -O0：这里的数与优化无关，用 -O0 只是和 probe.sh 的其余机身对照保持
 *     同一把尺子；
 *   - 这些数组全都落在 .bss，本文件永远不参与链接，所以它们不占板子一个字节——
 *     它是一台纯编译期的测量仪器，产物只是 nm 输出里的那一行。
 *
 * 交叉核对（probe.sh 第 3 步）：同一个 sizeof(Timer_t) 再用另一条独立路子量一遍——
 * objdump 反汇编 timers.c 里 pvPortMalloc( sizeof( Timer_t ) ) 那句的立即数。
 * 两条路子必须给出同一个数，否则就是我们在量自己的错觉。
 *
 * 事实基准：上游 FreeRTOS-Kernel tag V11.1.0。
 */

#include "timers.c"
#include "queue.c"
#include "tasks.c"
#include "portable/MemMang/heap_4.c"

/* ---- 定时器自己的三笔 ---- */
char probe_sizeof_Timer_t             [sizeof(Timer_t)];
char probe_sizeof_DaemonTaskMessage_t [sizeof(DaemonTaskMessage_t)];
char probe_sizeof_StaticTimer_t       [sizeof(StaticTimer_t)];

/* ---- 就绪/到期表的形状：守护任务手里那两条链表 ---- */
char probe_sizeof_List_t              [sizeof(List_t)];
char probe_sizeof_ListItem_t          [sizeof(ListItem_t)];

/* ---- 命令队列本体（不含 8 条消息的载荷）---- */
char probe_sizeof_Queue_t             [sizeof(Queue_t)];
char probe_sizeof_StaticQueue_t       [sizeof(StaticQueue_t)];

/* ---- 拿它跟"一个真任务"比价的基准 ---- */
char probe_sizeof_TCB_t               [sizeof(TCB_t)];

/* ---- 栈的深度单位是"字"，一个字多大必须量，不能假定是 4 ---- */
char probe_sizeof_StackType_t         [sizeof(StackType_t)];
/* ---- 到期时刻的类型：xLastTime 那 4 个字节归它，不能拿 StackType_t 顶替 ---- */
char probe_sizeof_TickType_t          [sizeof(TickType_t)];
/* ---- 指针宽度：.bss 那笔账里有四个 static 指针，宽度也得量 ---- */
char probe_sizeof_ptr                 [sizeof(void *)];

/* ---- Timer_t 逐成员拆开：第 6 步要把这笔账加回到 44 上 ----
 * 写法用 sizeof(((T *)0)->成员)：不需要真对象，编译期就出数。
 * uxTimerNumber 是 TRACE 门控的，所以它只在 TRACE=1 的档里存在——
 * 两个档各跑一次，差值就是"编号税"本体。 */
char probe_field_Timer_name           [sizeof(((Timer_t *) 0)->pcTimerName)];
char probe_field_Timer_item           [sizeof(((Timer_t *) 0)->xTimerListItem)];
char probe_field_Timer_period         [sizeof(((Timer_t *) 0)->xTimerPeriodInTicks)];
char probe_field_Timer_id             [sizeof(((Timer_t *) 0)->pvTimerID)];
char probe_field_Timer_cb             [sizeof(((Timer_t *) 0)->pxCallbackFunction)];
char probe_field_Timer_status         [sizeof(((Timer_t *) 0)->ucStatus)];
#if ( configUSE_TRACE_FACILITY == 1 )
    char probe_field_Timer_number     [sizeof(((Timer_t *) 0)->uxTimerNumber)];
#endif

/* ---- heap_4 每笔 malloc 的抽头 ---- */
char probe_sizeof_BlockLink_t         [sizeof(BlockLink_t)];
char probe_portBYTE_ALIGNMENT         [portBYTE_ALIGNMENT];

/* ---- 配置里的这几个数也走同一条路子：不抄 FreeRTOSConfig.h，让编译器报数 ---- */
char probe_configTIMER_QUEUE_LENGTH   [configTIMER_QUEUE_LENGTH];
char probe_configTIMER_TASK_STACK_DEPTH [configTIMER_TASK_STACK_DEPTH];
char probe_configMINIMAL_STACK_SIZE   [configMINIMAL_STACK_SIZE];
char probe_configMAX_TASK_NAME_LEN    [configMAX_TASK_NAME_LEN + 1]; /* pcTaskName 是 +1 */
/* 池子总额也从这里问，不从 FreeRTOSConfig.h 抄：分母错则百分比全错。
 * 这个数组只在编译期存在、永不链接，所以它占 16K 的"编译期地址空间"而不占板子。 */
char probe_configTOTAL_HEAP_SIZE      [configTOTAL_HEAP_SIZE];

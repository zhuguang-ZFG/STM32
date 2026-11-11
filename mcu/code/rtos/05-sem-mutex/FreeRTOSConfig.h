/**
 * FreeRTOSConfig.h —— 05-sem-mutex：只为取证而存在的配置，不烧板子
 *
 * 这一集要钉死的是两件事：
 *   (1) 信号量与互斥量到底是两个东西，还是同一个 Queue_t 换了个说法；
 *   (2) 优先级继承这段控制流在机身里是不是真的「判 → 改 → 搬」。
 * 两件事都在编译期和反汇编期能验完，所以这里只编 queue.c / tasks.c / list.c，
 * 不链、不启动、不要开发板。第 8 步的动态数另跑宿主机模型（sim_invert.c）。
 *
 * 取值一律照抄 01-freertos-lab/FreeRTOSConfig.h（见每行注释），因为读者是那个工程
 * 的读者：数字必须能对上他板子上的配置。lab 里没写的宏这里也刻意不写。
 *
 * 旋钮（都用 -D 传，不在这里改）：
 *   -DMUTEX=0|1   → configUSE_MUTEXES（第 7 步拿它验「继承是编译期的事，不是运行时的开关」）
 *   -DTRACE=0|1   → configUSE_TRACE_FACILITY（第 6 步用它验 ucQueueType 只是个标签）
 *
 * 与 lab 的唯一有意偏离：configUSE_TIMERS 这里给 0。lab 开着定时器，
 * 而这一集不想让守护任务那条队列混进账里——本集的结构体账只有 Queue_t 一个主角。
 *
 * 事实基准：上游 FreeRTOS-Kernel tag V11.1.0。
 */

#ifndef FREERTOS_CONFIG_H
#define FREERTOS_CONFIG_H

/* ---- 硬件：只是让宏有值可算，本工程不碰任何外设 ---- */
#define configCPU_CLOCK_HZ              16000000UL   /* lab：HSI 16MHz */
#define configTICK_RATE_HZ              1000UL       /* lab：1ms 节拍，一拍就是一毫秒 */
#define configPRIO_BITS                 4            /* lab：F407 有 4 位 */

/* ---- 调度：照抄 lab ---- */
#define configUSE_PREEMPTION            1
#define configUSE_TIME_SLICING          1
#define configMAX_PRIORITIES            5            /* lab：0..4，数字越大越高；sim 的 R4 用得上 */
#define configIDLE_SHOULD_YIELD         1

/* ---- 任务与栈：照抄 lab ---- */
#define configMINIMAL_STACK_SIZE        128
#define configMAX_TASK_NAME_LEN         12
#define configUSE_IDLE_HOOK             0
#define configUSE_TICK_HOOK             0
#define configCHECK_FOR_STACK_OVERFLOW  2
#define configUSE_MALLOC_FAILED_HOOK    0

/* ---- 内存：照抄 lab ---- */
#define configSUPPORT_DYNAMIC_ALLOCATION    1
#define configSUPPORT_STATIC_ALLOCATION     0
#define configTOTAL_HEAP_SIZE               (16 * 1024)
#define configAPPLICATION_ALLOCATED_HEAP    0

/* ---- 通知：照抄 lab（信号量的另一条实现路，本集不动它，但要给值）---- */
#define configUSE_TASK_NOTIFICATIONS            1
#define configTASK_NOTIFICATION_ARRAY_ENTRIES   1
#define configUSE_16_BIT_TICKS                  0

/* ---- 这一集的两个主角开关 ---- */
#ifndef MUTEX
    #define MUTEX                       1   /* lab：configUSE_MUTEXES=1 */
#endif
#define configUSE_MUTEXES                   MUTEX
#define configUSE_RECURSIVE_MUTEXES         0    /* lab 没开递归，本集也不碰 */
#define configUSE_COUNTING_SEMAPHORES       1    /* lab：计数信号量开着 */
#define configUSE_QUEUE_SETS                0
#define configUSE_TIMERS                    0    /* 见文件头：本集唯一有意偏离 lab 的一处 */
#ifndef TRACE
    #define TRACE                       1   /* lab：configUSE_TRACE_FACILITY=1 */
#endif
#define configUSE_TRACE_FACILITY            TRACE
#define configUSE_STATS_FORMATTING_FUNCTIONS 0
#define configQUEUE_REGISTRY_SIZE           8

/* ---- INCLUDE_* 门控：照抄 lab ---- */
#define INCLUDE_vTaskDelay                  1
#define INCLUDE_vTaskSuspend                1
#define INCLUDE_xTaskGetTickCount           1
#define INCLUDE_uxTaskGetNumberOfTasks      1
#define INCLUDE_xTaskGetCurrentTaskHandle   1

/* ---- 中断优先级：portmacro.h 里有 configASSERT 会读这两个值 ---- */
#define configKERNEL_INTERRUPT_PRIORITY         255
#define configMAX_SYSCALL_INTERRUPT_PRIORITY    (5 << (8 - configPRIO_BITS))

#endif /* FREERTOS_CONFIG_H */

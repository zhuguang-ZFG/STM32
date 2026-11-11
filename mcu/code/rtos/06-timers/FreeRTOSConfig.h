/**
 * FreeRTOSConfig.h —— 06-timers：只为取证而存在的配置，不烧板子
 *
 * 这一集要算的是"打开软件定时器到底花多少 RAM、回调为什么必然串行"。
 * 所以这里只编内核的四个文件（timers.c / tasks.c / queue.c / list.c）外加
 * heap_4.c，不链、不启动、不要开发板。
 *
 * 取值一律照抄 01-freertos-lab/FreeRTOSConfig.h（见下面每行的注释），
 * 因为这一账的读者是那个工程的读者：数字必须能对上他板子上的配置。
 * lab 里没写的宏，这里也刻意不写，交给内核自己决定（见 PEND 那条）。
 *
 * 旋钮（都用 -D 传，不在这里改）：
 *   -DPEND=0|1      → INCLUDE_xTimerPendFunctionCall
 *                     不传这个 -D，就让内核自己决定（probe.sh 第 4 步拿它做
 *                     逐字节对照，验 lab 那条"没写"的路到底落在哪）
 *   -DTRACE=n       → configUSE_TRACE_FACILITY
 *   -DSTATS=n       → configUSE_STATS_FORMATTING_FUNCTIONS（默认跟着 TRACE 走）
 *   -DQLEN=n        → configTIMER_QUEUE_LENGTH
 *   -DSTACKW=n      → configTIMER_TASK_STACK_DEPTH（单位是字）
 *
 * 事实基准：上游 FreeRTOS-Kernel tag V11.1.0。
 */

#ifndef FREERTOS_CONFIG_H
#define FREERTOS_CONFIG_H

/* ---- 硬件：只是让宏有值可算，本工程不碰任何外设 ---- */
#define configCPU_CLOCK_HZ              16000000UL   /* lab：HSI 16MHz */
#define configTICK_RATE_HZ              1000UL       /* lab：1ms 节拍 */
#define configPRIO_BITS                 4            /* lab：F407 有 4 位 */

/* ---- 调度：照抄 lab ---- */
#define configUSE_PREEMPTION            1
#define configUSE_TIME_SLICING          1
#define configMAX_PRIORITIES            5
#define configIDLE_SHOULD_YIELD         1

/* ---- 任务与栈：照抄 lab ---- */
#define configMINIMAL_STACK_SIZE        128
#define configMAX_TASK_NAME_LEN         12
#define configUSE_IDLE_HOOK             0
#define configUSE_TICK_HOOK             0
#define configCHECK_FOR_STACK_OVERFLOW  2
#define configUSE_MALLOC_FAILED_HOOK    0

/* ---- 内存：照抄 lab —— 这笔账的总额就是这里的 16K ---- */
#define configSUPPORT_DYNAMIC_ALLOCATION    1
#define configSUPPORT_STATIC_ALLOCATION     0
#define configTOTAL_HEAP_SIZE               (16 * 1024)
#define configAPPLICATION_ALLOCATED_HEAP    0

/* ---- 通知：照抄 lab ---- */
#define configUSE_TASK_NOTIFICATIONS            1
#define configTASK_NOTIFICATION_ARRAY_ENTRIES   1
#define configUSE_16_BIT_TICKS                  0

/* ---- 其余特性：lab 用哪些就开哪些，否则 sizeof 对不上 ---- */
#define configUSE_MUTEXES                   1
#define configUSE_COUNTING_SEMAPHORES       1
#define configUSE_RECURSIVE_MUTEXES         0
#define configUSE_QUEUE_SETS                0
#define configUSE_TIMERS                    1
#ifndef TRACE
    #define TRACE                           1   /* lab：configUSE_TRACE_FACILITY=1 */
#endif
#define configUSE_TRACE_FACILITY            TRACE
/* 这两个宏是一对：FreeRTOS.h 里有一条 #error 专门盯着"TRACE=0 却还开着
   STATS_FORMATTING"那种配置。默认让 STATS 跟着 TRACE 走，所以第 6 步要另造一个
   -DTRACE=0 -DSTATS=1 的不一致构建，专门去撞那条 #error，把这句话钉成实测。 */
#ifndef STATS
    #define STATS                       TRACE
#endif
#define configUSE_STATS_FORMATTING_FUNCTIONS STATS
#define configQUEUE_REGISTRY_SIZE           8

/* ---- 软件定时器：三个数决定这一集的账，全部照抄 lab ---- */
#define configTIMER_TASK_PRIORITY       (configMAX_PRIORITIES - 1) /* lab：4，跑最高 */
#ifndef QLEN
    #define QLEN                        8   /* lab：configTIMER_QUEUE_LENGTH=8 */
#endif
#define configTIMER_QUEUE_LENGTH        QLEN
#ifndef STACKW
    #define STACKW                      (configMINIMAL_STACK_SIZE * 2) /* lab：256 字 */
#endif
#define configTIMER_TASK_STACK_DEPTH    STACKW

/* INCLUDE_xTimerPendFunctionCall：lab 一个字都没写，所以这里也不写。
   这不是偷懒——V11.1.0 的 FreeRTOS.h:283-285 替它留了默认值，
   probe.sh 第 4 步要拿"没写"的构建去逐字节比对"写 0"的构建，
   验证默认值到底落在哪条路上；然后再掰成 1 看那条消息变大多少。 */
#if defined( PEND )
    #define INCLUDE_xTimerPendFunctionCall    PEND
#endif

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

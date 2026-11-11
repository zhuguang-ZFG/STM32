/**
 * FreeRTOSConfig.h —— 03-scheduler：只为取证而存在的配置，不烧板子
 *
 * 这一集要对照的是"选下一个任务"的两副面孔。所以这里只编内核的两个文件
 * （tasks.c 与 list.c），不链、不启动、不要开发板；两个旋钮：
 *
 *   -DSCHED_SEL=0|1   → configUSE_PORT_OPTIMISED_TASK_SELECTION
 *                        不传这个 -D，就让端口自己决定（见 probe.sh 第 1 步）
 *   -DNPRIO=n         → configMAX_PRIORITIES
 *
 * 事实基准：上游 FreeRTOS-Kernel tag V11.1.0。
 */

#ifndef FREERTOS_CONFIG_H
#define FREERTOS_CONFIG_H

/* ---- 硬件：只是让宏有值可算，本工程不碰任何外设 ---- */
#define configCPU_CLOCK_HZ              16000000UL
#define configTICK_RATE_HZ              1000UL
#define configPRIO_BITS                 4

/* ---- 调度：两个旋钮 ---- */
#define configUSE_PREEMPTION            1
#define configUSE_TIME_SLICING          1
#ifndef NPRIO
    #define NPRIO                        5
#endif
#define configMAX_PRIORITIES            NPRIO
#define configIDLE_SHOULD_YIELD         1

/* 不传 -DSCHED_SEL 时，这里一个字的配置都不写，交给 portmacro.h 的 #ifndef。
   这不是偷懒：probe.sh 第 1 步要拿这个"什么都没写"的构建，去逐字节比对
   显式写 1 的构建，验证默认值到底落在哪条路上。 */
#if defined( SCHED_SEL )
    #define configUSE_PORT_OPTIMISED_TASK_SELECTION    SCHED_SEL
#endif

/* ---- 任务与栈 ---- */
#define configMINIMAL_STACK_SIZE        128
#define configMAX_TASK_NAME_LEN         12
#define configUSE_IDLE_HOOK             0
#define configUSE_TICK_HOOK             0
#define configCHECK_FOR_STACK_OVERFLOW  0
#define configUSE_MALLOC_FAILED_HOOK    0

/* ---- 内存 ---- */
#define configSUPPORT_DYNAMIC_ALLOCATION    1
#define configSUPPORT_STATIC_ALLOCATION     0
#define configTOTAL_HEAP_SIZE               (16 * 1024)

/* ---- 其余特性全关：本取证只需要就绪表、延时表和 tick 这三段 ---- */
#define configUSE_TASK_NOTIFICATIONS        1
#define configTASK_NOTIFICATION_ARRAY_ENTRIES 1
#define configUSE_16_BIT_TICKS              0
#define configUSE_MUTEXES                   0
#define configUSE_COUNTING_SEMAPHORES       0
#define configUSE_RECURSIVE_MUTEXES         0
#define configUSE_QUEUE_SETS                0
#define configUSE_TIMERS                    0
#define configUSE_TRACE_FACILITY            0
#define configQUEUE_REGISTRY_SIZE           0

#define INCLUDE_vTaskDelay                  1
#define INCLUDE_vTaskSuspend                1
#define INCLUDE_xTaskGetTickCount           1

/* ---- 中断优先级：portmacro.h 里有 configASSERT 会读这两个值 ---- */
#define configKERNEL_INTERRUPT_PRIORITY         255
#define configMAX_SYSCALL_INTERRUPT_PRIORITY    (5 << (8 - configPRIO_BITS))

#endif /* FREERTOS_CONFIG_H */

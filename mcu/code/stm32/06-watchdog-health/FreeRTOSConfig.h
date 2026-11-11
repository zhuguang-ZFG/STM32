/**
 * FreeRTOSConfig.h —— 01-freertos-lab：上游 V11.1.0 + ARM_CM4F 单核端口
 *
 * 这份配置的每一行都会改变内核的行为，正文里引用的结论都以这里的值为准。
 * 改任何一个值，章节的数字都要重核——配置与正文是一体的。
 *
 * 事实基准：上游 FreeRTOS-Kernel tag V11.1.0（.trellis/ref/freertos-v11/kernel，
 *           含 tskKERNEL_VERSION_NUMBER "V11.1.0"）。
 *           与 ESP-IDF 内置的 V10.5.1 SMP 修改版不同源，不能混读。
 */

#ifndef FREERTOS_CONFIG_H
#define FREERTOS_CONFIG_H

/* ---- 硬件 ---- */
#define configCPU_CLOCK_HZ              16000000UL   /* 本工程跑 HSI 16MHz，不走 PLL */
#define configTICK_RATE_HZ              1000UL       /* 1ms 节拍 */
#define configPRIO_BITS                 4            /* F407 NVIC 有 4 个优先级位 */

/* ---- 调度 ---- */
#define configUSE_PREEMPTION            1
#define configUSE_TIME_SLICING          1
#define configMAX_PRIORITIES            5            /* 0..4，数字越大优先级越高 */
#define configIDLE_SHOULD_YIELD         1

/* ---- 任务与栈 ---- */
#define configMINIMAL_STACK_SIZE        128          /* 单位是字（4 字节），不是字节 */
#define configMAX_TASK_NAME_LEN         12
#define configUSE_IDLE_HOOK             0
#define configUSE_TICK_HOOK             0
#define configCHECK_FOR_STACK_OVERFLOW  2            /* 栈溢出检查开满 */

/* ---- 内存 ---- */
#define configSUPPORT_DYNAMIC_ALLOCATION 1
#define configSUPPORT_STATIC_ALLOCATION  0
#define configTOTAL_HEAP_SIZE           (16 * 1024)  /* heap_4 的池子 */
#define configAPPLICATION_ALLOCATED_HEAP 0

/* ---- 通知 / 事件组 / 定时器 ---- */
#define configUSE_TASK_NOTIFICATIONS        1
#define configTASK_NOTIFICATION_ARRAY_ENTRIES 1    /* 每任务 1 个通知槽：通知"容量一"由此而来 */
#define configUSE_16_BIT_TICKS                0    /* TickType_t 是 32 位 */

#define configUSE_TIMERS                1
#define configTIMER_TASK_PRIORITY       (configMAX_PRIORITIES - 1) /* 守护任务跑最高 */
#define configTIMER_QUEUE_LENGTH        8
#define configTIMER_TASK_STACK_DEPTH    (configMINIMAL_STACK_SIZE * 2)

/* ---- 事件组位数：F4 上是 24 位（TickType_t 32 位，扣掉 8 个控制位） ---- */
/* 不需要显式配置，由 configUSE_16_BIT_TICKS=0 决定；正文引用时按此口径。 */

/* ---- 统计与调试 ---- */
#define configUSE_TRACE_FACILITY        1            /* vTaskList 等可用 */
#define configUSE_STATS_FORMATTING_FUNCTIONS 0
#define configUSE_MUTEXES               1
#define configUSE_COUNTING_SEMAPHORES   1
#define configQUEUE_REGISTRY_SIZE       8

/* ---- 中断优先级 ---- */
/* 内核中断跑最低优先级；能调用 FromISR 的中断不得高于 MAX_SYSCALL */
#define configKERNEL_INTERRUPT_PRIORITY         255  /* 最低（4 位域全 1） */
#define configMAX_SYSCALL_INTERRUPT_PRIORITY    (5 << (8 - configPRIO_BITS))  /* 0x50 */
#define configMAX_API_CALL_INTERRUPT_PRIORITY   configMAX_SYSCALL_INTERRUPT_PRIORITY

/* ---- INCLUDE_* 门控：V11 内核默认把这些 API 全关掉 ----
 * 从老版本升级最容易踩的坑：升级后 vTaskDelay 链接不上，
 * 不是代码坏了，是这些宏默认 0。用哪个开哪个。 */
#define INCLUDE_vTaskDelay              1
#define INCLUDE_xTaskDelayUntil         1
#define INCLUDE_vTaskSuspend            1
#define INCLUDE_xTaskGetTickCount       1
#define INCLUDE_uxTaskGetNumberOfTasks  1
#define INCLUDE_xTaskGetCurrentTaskHandle 1

/* ---- 端口映射：把内核的 SVC/PendSV/SysTick 接到我们的向量名上 ---- */
#define vPortSVCHandler     SVC_Handler
#define xPortPendSVHandler  PendSV_Handler
#define xPortSysTickHandler SysTick_Handler

#endif /* FREERTOS_CONFIG_H */
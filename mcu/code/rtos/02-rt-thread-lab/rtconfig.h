/*
 * rtconfig.h —— 02-rt-thread-lab：RT-Thread Nano 式手动移植（R7 路线）
 *
 * 裁剪原则：只要内核（线程/IPC/内存/tick），不要标准版组件
 * （设备框架/finsh/DFS/软件包）——对应 R7 的 "Nano 四件套" 路线。
 * 配置项名以 .trellis/ref/rt-thread（RT-Thread 5.x）为准，从官方
 * BSP rtconfig 裁剪而来，不抄旧文。
 */
#ifndef RT_CONFIG_H__
#define RT_CONFIG_H__

/* ---------- 基础 ---------- */
#define RT_NAME_MAX 8
#define RT_CPUS_NR 1
#define RT_ALIGN_SIZE 8
#define RT_THREAD_PRIORITY_32
#define RT_THREAD_PRIORITY_MAX 32
#define RT_TICK_PER_SECOND 1000

/* ---------- 调试/钩子 ---------- */
#define RT_USING_OVERFLOW_CHECK
#define RT_USING_HOOK
#define RT_HOOK_USING_FUNC_PTR
#define RT_USING_IDLE_HOOK
#define RT_IDLE_HOOK_LIST_SIZE 4
#define RT_DEBUGING_ASSERT
#define RT_DEBUGING_COLOR

/* ---------- IPC：场景 6 需要信号量与互斥量 ---------- */
#define RT_USING_SEMAPHORE
#define RT_USING_MUTEX
#define RT_USING_EVENT
#define RT_USING_MAILBOX
#define RT_USING_MESSAGEQUEUE

/* ---------- 内存：小内存堆（Nano 默认） ---------- */
#define RT_USING_SMALL_MEM
#define RT_USING_SMALL_MEM_AS_HEAP
#define RT_USING_HEAP

/* ---------- 控制台（rt_kprintf） ---------- */
#define RT_USING_CONSOLE
#define RT_CONSOLEBUF_SIZE 128

/* ---------- libc：rt_memset/rt_strlen 等走 newlib（syscalls.c 兜底） ---------- */
#define RT_USING_LIBC

/* ---------- 原子操作：不开硬件原子（cortex-m4 无 LDREX 包装），用软件关中断实现 ---------- */
/* #define RT_USING_HW_ATOMIC */

#define RT_VER_NUM 0x50300
#define RT_BACKTRACE_LEVEL_MAX_NR 32

#endif /* RT_CONFIG_H__ */
/**
 * opt_probe.c —— volatile 的四个现场，不需要开发板
 *
 * C3 章的主工程：用宿主 gcc 把"少了 volatile 会被优化成什么"直接印在屏幕上。
 * 每一段都能在 30 秒内自己复现：make asm O=2 看汇编，make run 看可执行部分的行为。
 *
 * 与单片机的关系：这里演示的是同一条 as-if 规则（C 标准 §6.7.3 对 volatile 的要求
 * 与 -O 级别无关）。本工程已在宿主 gcc 与 arm-none-eabi-gcc（Cortex-M4）两套工具链上
 * 各跑一遍，两边的取证结果都列在下面——优化决策完全一致，只是指令形式不同。
 *
 * 取证结果 A：gcc 16.1.0 x86_64（MinGW-Builds），-std=c11 -Wall -Wextra -O2，2026-10-06 本机实测
 *   poll_plain        → 只读一次，随后 .L3: jmp .L3        （死转，硬件置位也看不见）
 *   poll_volatile     → .L6: testb / je .L6                 （每轮真访存）
 *   delay_plain       → 整条只剩 ret                         （空循环被删）
 *   delay_volatile    → 每轮 load / dec / store              （循环留得住）
 *   cfg_plain         → 三次 |= 合成一条 orl $7             （三次写变一次写）
 *   cfg_volatile      → orl $1 / orl $2 / orl $4 三条         （写次数=源码次数）
 *   isr_toggle        → xorl $1, shared_flag(%rip) 一条读-改-写（访存一次，但不原子）
 *
 * 取证结果 B：xPack arm-none-eabi-gcc 15.2.1，-mcpu=cortex-m4 -mthumb -O2，同日实测
 *   poll_plain        → ldr r3,[r3] 读一次；未置位则 .L3: b .L3 原地死转
 *   poll_volatile     → .L8: ldr r3,[r2,#4] / lsls / bpl .L8 每圈真读
 *   delay_plain       → 整个函数只剩 bx lr                    （延时直接不存在）
 *   delay_volatile    → 计数落 [sp,#4]，每圈 ldr/subs/str/cmp/bne
 *   cfg_plain         → ldr / orr r3,r3,#7 / str             （三次并一次，只访存一次）
 *   cfg_volatile      → 三组 ldr/orr/str 共 9 条              （六次访存）
 *   isr_toggle        → ldr / eor #1 / str 三条               （M4 上连"一条指令"的假象都没有）
 */

#include <stdio.h>

/* ========== 现场 1：把变量当状态寄存器轮询 ========== */
/* 真实写法是 while (!(USART1->SR & USART_SR_RXNE)); —— SR 通过 CMSIS 的 __IO 带 volatile */
unsigned int g_status;

int poll_plain(void)
{
    while (!(g_status & 1u)) {
        /* 等硬件把 bit0 置 1 */
    }
    return 42;                      /* -O2 下这一句未必到得了 */
}

volatile unsigned int v_status;

int poll_volatile(void)
{
    while (!(v_status & 1u)) {
        /* 与上面唯一的区别：声明加了 volatile */
    }
    return 42;
}

/* ========== 现场 2：软件延时循环 ========== */
void delay_plain(unsigned int n)
{
    while (n--) {
        /* 什么都不做：没有副作用的空循环，C 标准允许优化器假定它不会无限跑 */
    }
}

void delay_volatile(volatile unsigned int n)
{
    while (n--) {
    }
}

/* ========== 现场 3：配置序列被"合并成一次写" ========== */
typedef struct {
    unsigned int cr;
} plain_reg_t;

void cfg_plain(plain_reg_t *p)
{
    p->cr |= 1u;                    /* 使能位 0 */
    p->cr |= 2u;                    /* 使能位 1 */
    p->cr |= 4u;                    /* 使能位 2 —— 无 volatile：三次并成一次 or 7 */
}

typedef struct {
    volatile unsigned int cr;
} iom_reg_t;                        /* CMSIS GPIO_TypeDef 的 __IO 就是这个写法 */

void cfg_volatile(iom_reg_t *p)
{
    p->cr |= 1u;
    p->cr |= 2u;
    p->cr |= 4u;                    /* volatile：三条独立读-改-写，一条不少 */
}

/* ========== 现场 4：volatile 保证访存，不保证原子 ========== */
volatile unsigned int shared_flag;

void isr_toggle(void)
{
    shared_flag ^= 1u;              /* 读-改-写三步：都在访存，三步之间仍能被中断插队 */
}

/* ========== 只跑"敢执行"的部分 ========== */
/* poll_* 会死等，MMIO 版会段错误，所以这里只验证现场 4 与延时的行为差异 */
int main(void)
{
    shared_flag = 0u;
    for (int i = 0; i < 4; i++) {
        isr_toggle();
    }
    printf("现场4：4 次 xor 之后 shared_flag = %u（值对，但每一步都不是原子的）\n", shared_flag);

    delay_volatile(1000000u);
    puts("现场2：delay_volatile(1000000) 真的耗了时间");

    puts("现场3：cfg_plain 与 cfg_volatile 的差别只能从汇编看——make asm O=2");
    (void)poll_plain;
    (void)poll_volatile;
    (void)delay_plain;
    (void)cfg_plain;
    (void)cfg_volatile;
    return 0;
}

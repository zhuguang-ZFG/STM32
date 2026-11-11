/*
 * board/board.c —— 02-rt-thread-lab：Nano 移植的"板卡知识全集"（R7 第二节）
 *
 * 与 R7 一致：内核无关板卡，板卡知识全收进这一个文件——
 *  1) 时钟：HSI 16MHz（不走 PLL，与 01-freertos-lab 同口径）
 *  2) SysTick：1ms tick，ISR 里调 rt_tick_increase()（内核报时员）
 *  3) 堆：把链接脚本划出的区间交给 rt_system_heap_init
 *  4) 控制台：rt_hw_console_output → USART1 PA9/PA10 寄存器级驱动
 *
 * 异常接管：PendSV/HardFault 由 libcpu 的 context_gcc.S 接管，
 * 本文件只需提供 SysTick_Handler（R7 第三节的对照表）。
 */

#include <rtthread.h>
#include <rthw.h>

/* ==================== 寄存器级外设（S7 USART 复用） ==================== */

#define RCC_BASE    0x40023800UL
#define RCC_AHB1ENR (*(volatile uint32_t *)(RCC_BASE + 0x30UL))
#define RCC_APB2ENR (*(volatile uint32_t *)(RCC_BASE + 0x44UL))

#define GPIOA_BASE 0x40020000UL
#define GPIOA_MODER (*(volatile uint32_t *)(GPIOA_BASE + 0x00UL))
#define GPIOA_AFRL  (*(volatile uint32_t *)(GPIOA_BASE + 0x20UL))

#define USART1_BASE 0x40011000UL
#define USART1_SR   (*(volatile uint32_t *)(USART1_BASE + 0x00UL))
#define USART1_DR   (*(volatile uint32_t *)(USART1_BASE + 0x04UL))
#define USART1_BRR  (*(volatile uint32_t *)(USART1_BASE + 0x08UL))
#define USART1_CR1  (*(volatile uint32_t *)(USART1_BASE + 0x0CUL))

/* SysTick（内核外设，ARM 架构定义） */
#define SYSTICK_CTRL  (*(volatile uint32_t *)0xE000E010UL)
#define SYSTICK_LOAD  (*(volatile uint32_t *)0xE000E014UL)
#define SYSTICK_VAL   (*(volatile uint32_t *)0xE000E018UL)

/* 链接脚本符号：__bss_end__（堆起点）与 _estack（RAM 尾=栈顶） */
extern unsigned char __bss_end__;
extern unsigned char _estack;

static void uart1_init(void)
{
    RCC_AHB1ENR |= (1UL << 0);               /* GPIOA 时钟 */
    RCC_APB2ENR |= (1UL << 4);               /* USART1 时钟 */

    /* PA9=TX、PA10=RX 复用为 USART1（AF7），低速档 */
    GPIOA_MODER = (GPIOA_MODER & ~(3UL << 18)) | (2UL << 18);
    GPIOA_MODER = (GPIOA_MODER & ~(3UL << 20)) | (2UL << 20);
    GPIOA_AFRL  = (GPIOA_AFRL  & ~(0xFFUL << 4)) | (0x77UL << 4);

    USART1_BRR = 16000000UL / 115200UL;   /* HSI 16MHz / 115200 = 139，误差 -0.08% */
    USART1_CR1 = (1UL << 13) | (1UL << 3) | (1UL << 2);  /* UE | TE | RE */
}

/* ==================== 内核要求的硬件接口 ==================== */

/**
 * rt_hw_console_output：rt_kprintf 的最终落点（R5 finsh/console 下层）。
 */
void rt_hw_console_output(const char *item)
{
    while (*item) {
        while (!(USART1_SR & (1UL << 7))) { }   /* TXE 等待 */
        USART1_DR = (uint32_t)(uint8_t)*item++;
    }
}

/**
 * SysTick_Handler：1ms 报时。进/出中断钩子 + rt_tick_increase，
 * 与 FreeRTOS 的 xPortSysTickHandler 异曲同工（R7 第三节对照表）。
 */
void SysTick_Handler(void)
{
    rt_interrupt_enter();
    rt_tick_increase();
    rt_interrupt_leave();
}

/**
 * rt_hw_board_init：Nano 四件套的第三件。
 * 1) 串口（日志）+ 时钟（HSI 16MHz）
 * 2) SysTick 配 1ms tick
 * 3) 堆：__bss_end__ → _estack（B3 链接脚本符号复训）
 */
void rt_hw_board_init(void)
{
    uart1_init();

    SYSTICK_LOAD = 16000000UL / RT_TICK_PER_SECOND - 1UL;
    SYSTICK_VAL  = 0UL;
    SYSTICK_CTRL = 0x7UL;   /* ENABLE | TICKINT | CLKSOURCE */

    rt_system_heap_init((void *)&__bss_end__, (void *)&_estack);
}
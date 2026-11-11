/*
 * superloop.h —— F0 唯一的一份"三任务超级循环"
 *
 * 同一份 superloop.c 在两边编译：
 *   宿主机（mingw gcc）  → board_host.c 给时钟/串口/按键，跑起来量时间
 *   Cortex-M4（交叉链）  → board_arm.h 给真寄存器实现，只出反汇编数指令
 * 两边看到的任务代码一字不差，所以宿主机上量到的"谁等谁"结构，就是芯片上的结构。
 */
#ifndef F0_SUPERLOOP_H
#define F0_SUPERLOOP_H

#include <stdint.h>

/* ---- 板级那一层：唯一随平台变化的东西 ---- */
#if defined(BOARD_ARM)
#  include "board_arm.h"   /* 交叉编：static inline 的真寄存器实现，直接内联进任务体 */
#else
uint32_t board_tick_ms(void);            /* SysTick 1 ms 节拍的读数（S5 那本账） */
int      board_uart_rx_ready(void);      /* 查一眼 USART_SR 的 RXNE，立刻返回 */
char     board_uart_getc(void);          /* 死等 RXNE —— 章里点名的元凶 */
char     board_uart_read_byte(void);     /* 已确认 RXNE 之后取 DR */
void     board_uart_write(const char *s, uint16_t n);
int      board_key_down(void);           /* 按键电平，只读不判边沿 */
void     board_led_set(int on);          /* 主灯：led_tick 每 500 ms 翻一次 */
void     board_led2_toggle(void);        /* 另一颗灯：key_scan 按下沿翻它 */
#endif

/* ---- 三个任务 + 两种超级循环 ---- */
void led_tick(void);
void key_scan(void);
void uart_echo(void);                    /* 第二节：收满一个字符才返回 */
void uart_poll(void);                    /* 第三节：查一眼就走 */
void superloop_block(void);
void superloop_poll(void);

#endif /* F0_SUPERLOOP_H */

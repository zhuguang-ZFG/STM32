/*
 * board/board.h —— 02-rt-thread-lab：板卡接口声明（R7 "board.c 是板卡知识全集"）
 *
 * 对外只暴露两个接口：
 *   rt_hw_board_init()   板卡初始化（时钟/SysTick/堆），main 在启动调度器前调用
 *   rt_hw_console_output() rt_kprintf 输出（内核要求，已实现于 board.c）
 */
#ifndef BOARD_H__
#define BOARD_H__

void rt_hw_board_init(void);

#endif /* BOARD_H__ */
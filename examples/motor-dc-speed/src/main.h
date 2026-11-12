/* 板级公共头：全局外设句柄（Cube 惯例 extern）+ 初始化原型。
 * 全部配置为 CANDIDATE，P2 上板核验后冻结（见 boards/f103c8-tb6612/hardware.md）。
 */
#ifndef MOTOR_MAIN_H
#define MOTOR_MAIN_H

#include "stm32f1xx_hal.h"

extern TIM_HandleTypeDef htim2;   /* 编码器（TIM2 编码器模式 3） */
extern TIM_HandleTypeDef htim3;   /* PWM（TIM3_CH1，20 kHz 候选） */
extern TIM_HandleTypeDef htim4;   /* 控制周期（10 ms 候选） */
extern UART_HandleTypeDef huart1; /* 命令/遥测（115200 8N1 候选） */

void board_clock_init(void);
void board_gpio_init(void);
void board_tim_init(void);
void board_uart_init(void);
uint32_t board_micros(void);
uint8_t *board_uart_rx_buf(void);

void board_uart_rx_byte(uint8_t b);   /* 由 UART 接收完成回调喂入 */
void board_control_isr(void);         /* TIM4 更新中断体 */

#endif

/*
 * board_arm.h —— 同一份 superloop.c 落到 STM32F407 真寄存器上
 *
 * 这份不链接、不烧写，只用来出反汇编：probe.sh 用
 *   arm-none-eabi-gcc -mcpu=cortex-m4 -mthumb -O2 -DBOARD_ARM -c superloop.c
 * 编一个目标文件，再 objdump 出来数每个任务本体的指令条数。
 * 全部 static inline，所以内联进任务体之后，屏上看到的就是芯片真正会跑的形状。
 *
 * 地址取自 STM32F407 数据手册；Discovery 板 LED2=PD12、LED3=PD13、USER 键=PA0。
 */
#ifndef F0_BOARD_ARM_H
#define F0_BOARD_ARM_H

#include <stdint.h>

#define USART2_SR   (*(volatile uint32_t *)0x40004400u)   /* 0x40004400 + 0x00 */
#define USART2_DR   (*(volatile uint32_t *)0x40004404u)   /* 0x40004400 + 0x04 */
#define USART_SR_RXNE (1u << 5)
#define USART_SR_TXE  (1u << 7)

#define GPIOA_IDR   (*(volatile uint32_t *)0x40020010u)   /* 0x40020000 + 0x10 */
#define GPIOD_ODR   (*(volatile uint32_t *)0x40020C14u)   /* 0x40020C00 + 0x14 */
#define GPIOD_BSRR  (*(volatile uint32_t *)0x40020C18u)   /* 0x40020C00 + 0x18 */

#define LED_PIN     12u   /* PD12 */
#define LED2_PIN    13u   /* PD13 */
#define KEY_PIN     0u    /* PA0  */

/* SysTick_Handler 里自增的那个变量，S5 的账本；这里只读 */
extern volatile uint32_t g_tick_ms;

static inline uint32_t board_tick_ms(void)
{
    return g_tick_ms;
}

static inline int board_uart_rx_ready(void)
{
    return (int)((USART2_SR & USART_SR_RXNE) != 0u);
}

static inline char board_uart_read_byte(void)
{
    return (char)(USART2_DR & 0xFFu);
}

static inline char board_uart_getc(void)
{
    while (!(USART2_SR & USART_SR_RXNE)) {
        /* 章里那句 while：一根轴上所有人的时间都堵在这儿 */
    }
    return (char)(USART2_DR & 0xFFu);
}

static inline void board_uart_write(const char *s, uint16_t n)
{
    for (uint16_t i = 0u; i < n; i++) {
        while (!(USART2_SR & USART_SR_TXE)) {
            /* 发送寄存器满：115200 8N1 一个字符 86.8 µs，谁也动不了 */
        }
        USART2_DR = (uint32_t)(unsigned char)s[i];
    }
}

static inline int board_key_down(void)
{
    return (int)((GPIOA_IDR >> KEY_PIN) & 1u);
}

static inline void board_led_set(int on)
{
    GPIOD_BSRR = on ? (1u << LED_PIN) : (1u << (LED_PIN + 16u));
}

static inline void board_led2_toggle(void)
{
    GPIOD_ODR ^= (1u << LED2_PIN);
}

#endif /* F0_BOARD_ARM_H */

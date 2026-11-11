/*
 * superloop.c —— F0 的主角：三个任务挤一根时间轴
 *
 * 这份代码就是章里那三行 for(;;)，一行不美化：led_tick 数 SysTick 到 500 翻灯，
 * key_scan 每次都查电平，uart_echo 收满一个字符才返回。
 * 宿主机与 Cortex-M4 交叉编译共用这一份，区别只在 board 那一层。
 */
#include "superloop.h"

#define LED_PERIOD_MS 500u

static uint32_t s_last_flip;
static int      s_led_on;
static int      s_key_prev;

static char     s_line[64];
static uint16_t s_line_len;

static void consume(char c)
{
    if (c == '\n') {
        board_uart_write(s_line, s_line_len);
        s_line_len = 0;
    } else if (c != '\0' && s_line_len + 1u < sizeof s_line) {
        s_line[s_line_len++] = c;
    }
}

void led_tick(void)
{
    uint32_t now = board_tick_ms();

    if (now - s_last_flip >= LED_PERIOD_MS) {
        s_last_flip = now;
        s_led_on = !s_led_on;
        board_led_set(s_led_on);
    }
}

void key_scan(void)
{
    int down = board_key_down();

    if (down && !s_key_prev) {
        board_led2_toggle();
    }
    s_key_prev = down;
}

void uart_echo(void)
{
    consume(board_uart_getc());   /* 死等：下一个字节不来，这一行不返回 */
}

void uart_poll(void)
{
    if (!board_uart_rx_ready()) {
        return;
    }
    consume(board_uart_read_byte());
}

void superloop_block(void)
{
    for (;;) {
        led_tick();
        key_scan();
        uart_echo();
    }
}

void superloop_poll(void)
{
    for (;;) {
        led_tick();
        key_scan();
        uart_poll();
    }
}

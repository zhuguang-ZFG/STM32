#include <assert.h>
#include <setjmp.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "stm32f1xx_hal.h"

#define main firmware_main
#include "../main.c"
#undef main
#include "../stm32f1xx_it.c"

GPIO_TypeDef test_gpioa;
GPIO_TypeDef test_gpioc;
USART_TypeDef test_usart1;
DMA_Channel_TypeDef test_dma1_ch5;

static jmp_buf firmware_exit;
static uint32_t tick;
static uint32_t clock_flags;
static uint32_t delay_ms;
static bool exit_on_receive;
static bool reset_called;
static bool ore_cleared;
static bool fe_cleared;
static unsigned receive_calls;
static unsigned transmit_calls;
static uint8_t *rx_buffer;
static uint16_t rx_size;
static char tx_capture[2048];
static size_t tx_len;
static GPIO_InitTypeDef gpioa_config[16];
static GPIO_InitTypeDef gpioc_config[16];
static UART_InitTypeDef uart_config;
static DMA_InitTypeDef dma_config;
static RCC_OscInitTypeDef osc_config;
static RCC_ClkInitTypeDef clk_config;
static uint32_t flash_latency;
static uint32_t irq_preempt[64];
static uint32_t irq_sub[64];
static bool irq_enabled[64];
static HAL_StatusTypeDef oscillator_status;
static HAL_StatusTypeDef clock_status;
static HAL_StatusTypeDef uart_status;
static HAL_StatusTypeDef dma_status;
static HAL_StatusTypeDef receive_status;
static HAL_StatusTypeDef transmit_status;

void test_enable_clock(uint32_t mask) { clock_flags |= mask; }

void test_clear_uart_flag(UART_HandleTypeDef *huart, uint32_t flag)
{
    assert(huart == &huart1);
    test_usart1.SR &= ~flag;
    if (flag == UART_FLAG_ORE) { ore_cleared = true; }
    if (flag == UART_FLAG_FE) { fe_cleared = true; }
}

void test_disable_irq(void) { longjmp(firmware_exit, 2); }
void HAL_Init(void) { tick = 0U; }
uint32_t HAL_GetTick(void) { return tick; }
void HAL_IncTick(void) { tick++; }
void HAL_Delay(uint32_t value) { delay_ms = value; }

void HAL_GPIO_Init(GPIO_TypeDef *port, GPIO_InitTypeDef *config)
{
    unsigned index = 0U;
    while ((index < 16U) && (config->Pin != (1U << index))) { index++; }
    assert(index < 16U);
    if (port == GPIOA) { gpioa_config[index] = *config; }
    else { assert(port == GPIOC); gpioc_config[index] = *config; }
}

void HAL_GPIO_WritePin(GPIO_TypeDef *port, uint16_t pin, GPIO_PinState state)
{
    if (state == GPIO_PIN_SET) { port->ODR |= pin; }
    else { port->ODR &= ~(uint32_t)pin; }
}

HAL_StatusTypeDef HAL_RCC_OscConfig(RCC_OscInitTypeDef *config)
{
    osc_config = *config;
    return oscillator_status;
}

HAL_StatusTypeDef HAL_RCC_ClockConfig(RCC_ClkInitTypeDef *config, uint32_t latency)
{
    clk_config = *config;
    flash_latency = latency;
    return clock_status;
}

HAL_StatusTypeDef HAL_UART_Init(UART_HandleTypeDef *huart)
{
    assert(huart == &huart1);
    uart_config = huart->Init;
    return uart_status;
}

HAL_StatusTypeDef HAL_UART_Transmit(UART_HandleTypeDef *huart, uint8_t *data, uint16_t size, uint32_t timeout)
{
    assert(huart == &huart1);
    assert(timeout == 100U);
    assert(tx_len + size < sizeof(tx_capture));
    memcpy(&tx_capture[tx_len], data, size);
    tx_len += size;
    tx_capture[tx_len] = '\0';
    transmit_calls++;
    return transmit_status;
}

HAL_StatusTypeDef HAL_UARTEx_ReceiveToIdle_DMA(UART_HandleTypeDef *huart, uint8_t *data, uint16_t size)
{
    assert(huart == &huart1);
    if (exit_on_receive) { longjmp(firmware_exit, 1); }
    if (receive_status != HAL_OK) { return receive_status; }
    huart->RxState = HAL_UART_STATE_BUSY;
    huart->ReceptionType = HAL_UART_RECEPTION_TOIDLE;
    rx_buffer = data;
    rx_size = size;
    receive_calls++;
    return HAL_OK;
}

HAL_UART_RxEventTypeTypeDef HAL_UARTEx_GetRxEventType(UART_HandleTypeDef *huart)
{
    assert(huart == &huart1);
    return (HAL_UART_RxEventTypeTypeDef)huart->RxEventType;
}

void HAL_UART_IRQHandler(UART_HandleTypeDef *huart) { assert(huart == &huart1); }

HAL_StatusTypeDef HAL_DMA_Init(DMA_HandleTypeDef *hdma)
{
    assert(hdma == &hdma_usart1_rx);
    dma_config = hdma->Init;
    return dma_status;
}

void HAL_DMA_IRQHandler(DMA_HandleTypeDef *hdma) { assert(hdma == &hdma_usart1_rx); }

void HAL_NVIC_SetPriority(int irq, uint32_t preempt, uint32_t sub)
{
    assert(irq >= 0 && irq < 64);
    irq_preempt[irq] = preempt;
    irq_sub[irq] = sub;
}

void HAL_NVIC_EnableIRQ(int irq)
{
    assert(irq >= 0 && irq < 64);
    irq_enabled[irq] = true;
}

void NVIC_SystemReset(void)
{
    reset_called = true;
    longjmp(firmware_exit, 3);
}

static void reset_state(void)
{
    memset(&test_gpioa, 0, sizeof(test_gpioa));
    memset(&test_gpioc, 0, sizeof(test_gpioc));
    memset(&test_usart1, 0, sizeof(test_usart1));
    memset(&test_dma1_ch5, 0, sizeof(test_dma1_ch5));
    test_gpioc.ODR = 0xFFFFFFFFU;
    memset(&huart1, 0, sizeof(huart1));
    memset(&hdma_usart1_rx, 0, sizeof(hdma_usart1_rx));
    memset(&g_rb, 0, sizeof(g_rb));
    memset(g_dma_rx_buf, 0, sizeof(g_dma_rx_buf));
    memset(g_line, 0, sizeof(g_line));
    g_line_len = 0U;
    g_echo_on = 1U;
    g_led_state = 0U;
    tick = 0U;
    clock_flags = 0U;
    delay_ms = 0U;
    exit_on_receive = false;
    reset_called = false;
    ore_cleared = false;
    fe_cleared = false;
    receive_calls = 0U;
    transmit_calls = 0U;
    rx_buffer = NULL;
    rx_size = 0U;
    tx_len = 0U;
    tx_capture[0] = '\0';
    memset(gpioa_config, 0, sizeof(gpioa_config));
    memset(gpioc_config, 0, sizeof(gpioc_config));
    memset(&uart_config, 0, sizeof(uart_config));
    memset(&dma_config, 0, sizeof(dma_config));
    memset(&osc_config, 0, sizeof(osc_config));
    memset(&clk_config, 0, sizeof(clk_config));
    memset(irq_preempt, 0, sizeof(irq_preempt));
    memset(irq_sub, 0, sizeof(irq_sub));
    memset(irq_enabled, 0, sizeof(irq_enabled));
    flash_latency = 0U;
    oscillator_status = HAL_OK;
    clock_status = HAL_OK;
    uart_status = HAL_OK;
    dma_status = HAL_OK;
    receive_status = HAL_OK;
    transmit_status = HAL_OK;
}

static void push_byte(ring_buf_t *rb, uint8_t value)
{
    rb_push(rb, &value, 1U);
}

static int pop_byte(ring_buf_t *rb, uint8_t *value)
{
    return rb_pop(rb, value);
}

static void feed_line(const char *line)
{
    for (const char *p = line; *p != '\0'; ++p) { cmd_process_char(*p); }
    cmd_process_char('\r');
    cmd_process_char('\n');
}

static void test_ring_buffer_wrap_and_full(void)
{
    ring_buf_t rb;
    uint8_t value = 0U;
    rb_init(&rb);
    for (unsigned i = 0U; i < RING_BUF_SIZE - 1U; ++i) { push_byte(&rb, (uint8_t)i); }
    assert(rb.head == RING_BUF_SIZE - 1U);
    push_byte(&rb, 0xFFU);
    assert(rb.head == RING_BUF_SIZE - 1U);
    for (unsigned i = 0U; i < RING_BUF_SIZE - 1U; ++i) {
        assert(pop_byte(&rb, &value) == 0);
        assert(value == (uint8_t)i);
    }
    assert(pop_byte(&rb, &value) == -1);

    rb_init(&rb);
    for (unsigned i = 0U; i < 500U; ++i) { push_byte(&rb, (uint8_t)i); }
    for (unsigned i = 0U; i < 400U; ++i) { assert(pop_byte(&rb, &value) == 0); }
    for (unsigned i = 500U; i < 900U; ++i) { push_byte(&rb, (uint8_t)i); }
    for (unsigned i = 400U; i < 500U; ++i) {
        assert(pop_byte(&rb, &value) == 0);
        assert(value == (uint8_t)i);
    }
    for (unsigned i = 500U; i < 900U; ++i) {
        assert(pop_byte(&rb, &value) == 0);
        assert(value == (uint8_t)i);
    }
    assert(pop_byte(&rb, &value) == -1);
}

static void test_command_parser(void)
{
    uint8_t value = 0U;
    int reason;
    reset_state();
    feed_line("AT");
    assert(strcmp(tx_capture, "> AT\r\nOK\r\n") == 0);

    tx_len = 0U; tx_capture[0] = '\0';
    feed_line("AT+LED=0");
    assert(strcmp(tx_capture, "> AT+LED=0\r\nOK\r\n") == 0);
    assert(g_led_state == 0U);
    assert((GPIOC->ODR & GPIO_PIN_13) == 0U);

    tx_len = 0U; tx_capture[0] = '\0';
    feed_line("AT+LED?");
    assert(strcmp(tx_capture, "> AT+LED?\r\n+LED:0\r\nOK\r\n") == 0);

    tx_len = 0U; tx_capture[0] = '\0';
    feed_line("AT+ECHO=0");
    feed_line("AT");
    assert(strcmp(tx_capture, "> AT+ECHO=0\r\nOK\r\nOK\r\n") == 0);

    g_echo_on = 1U;

    tx_len = 0U; tx_capture[0] = '\0';
    feed_line("AT+NOPE");
    assert(strcmp(tx_capture, "> AT+NOPE\r\nERROR: unknown command\r\n") == 0);

    tx_len = 0U; tx_capture[0] = '\0';
    for (unsigned i = 0U; i < CMD_LINE_MAX; ++i) { cmd_process_char('A'); }
    cmd_process_char('\r');
    assert(strcmp(tx_capture, "ERROR: line too long\r\n") == 0);
    assert(g_line_len == 0U);

    reset_state();
    g_echo_on = 0U;
    reason = setjmp(firmware_exit);
    if (reason == 0) { feed_line("AT+RESET"); }
    assert(reason == 3);
    assert(reset_called);
    assert(delay_ms == 50U);
    assert(strcmp(tx_capture, "OK\r\nrebooting...\r\n") == 0);
    assert(pop_byte(&g_rb, &value) == -1);
}

static void test_rx_event_callback(void)
{
    uint8_t value = 0U;
    int reason;
    reset_state();
    huart1.Instance = USART1;
    for (unsigned i = 0U; i < DMA_RX_BUF_SIZE; ++i) { g_dma_rx_buf[i] = (uint8_t)(0xA0U + i); }

    huart1.RxState = HAL_UART_STATE_BUSY;
    huart1.RxEventType = HAL_UART_RXEVENT_HT;
    HAL_UARTEx_RxEventCallback(&huart1, DMA_RX_BUF_SIZE / 2U);
    assert(receive_calls == 0U);
    assert(g_rb.head == g_rb.tail);

    huart1.RxState = HAL_UART_STATE_READY;
    huart1.RxEventType = HAL_UART_RXEVENT_IDLE;
    HAL_UARTEx_RxEventCallback(&huart1, 40U);
    assert(receive_calls == 1U);
    assert(rx_buffer == g_dma_rx_buf);
    assert(rx_size == DMA_RX_BUF_SIZE);
    for (unsigned i = 0U; i < 40U; ++i) {
        assert(pop_byte(&g_rb, &value) == 0);
        assert(value == (uint8_t)(0xA0U + i));
    }

    huart1.RxState = HAL_UART_STATE_READY;
    huart1.RxEventType = HAL_UART_RXEVENT_TC;
    HAL_UARTEx_RxEventCallback(&huart1, DMA_RX_BUF_SIZE);
    assert(receive_calls == 2U);
    for (unsigned i = 0U; i < DMA_RX_BUF_SIZE; ++i) {
        assert(pop_byte(&g_rb, &value) == 0);
        assert(value == (uint8_t)(0xA0U + i));
    }

    receive_status = HAL_BUSY;
    huart1.RxState = HAL_UART_STATE_READY;
    huart1.RxEventType = HAL_UART_RXEVENT_IDLE;
    reason = setjmp(firmware_exit);
    if (reason == 0) { HAL_UARTEx_RxEventCallback(&huart1, 1U); }
    assert(reason == 2);
}

static void test_error_callback(void)
{
    int reason;
    reset_state();
    huart1.Instance = USART1;
    huart1.RxState = HAL_UART_STATE_READY;
    test_usart1.SR = UART_FLAG_ORE | UART_FLAG_FE;
    HAL_UART_ErrorCallback(&huart1);
    assert(ore_cleared && fe_cleared);
    assert((test_usart1.SR & (UART_FLAG_ORE | UART_FLAG_FE)) == 0U);
    assert(receive_calls == 1U);

    receive_status = HAL_ERROR;
    reason = setjmp(firmware_exit);
    if (reason == 0) { HAL_UART_ErrorCallback(&huart1); }
    assert(reason == 2);
}

static void test_uart_dma_init(void)
{
    int reason;
    reset_state();
    uart_dma_init();
    assert(clock_flags == 0x0FU);
    assert((GPIOC->ODR & GPIO_PIN_13) == 0U);
    assert(gpioa_config[9].Mode == GPIO_MODE_AF_PP);
    assert(gpioa_config[9].Speed == GPIO_SPEED_FREQ_HIGH);
    assert(gpioa_config[10].Mode == GPIO_MODE_INPUT);
    assert(gpioa_config[10].Pull == GPIO_PULLUP);
    assert(gpioc_config[13].Mode == GPIO_MODE_OUTPUT_PP);
    assert(uart_config.BaudRate == UART_BAUDRATE);
    assert(uart_config.WordLength == UART_WORDLENGTH_8B);
    assert(uart_config.StopBits == UART_STOPBITS_1);
    assert(uart_config.Parity == UART_PARITY_NONE);
    assert(uart_config.Mode == UART_MODE_TX_RX);
    assert(uart_config.HwFlowCtl == UART_HWCONTROL_NONE);
    assert(uart_config.OverSampling == UART_OVERSAMPLING_16);
    assert(hdma_usart1_rx.Instance == DMA1_Channel5);
    assert(dma_config.Direction == DMA_PERIPH_TO_MEMORY);
    assert(dma_config.PeriphInc == DMA_PINC_DISABLE);
    assert(dma_config.MemInc == DMA_MINC_ENABLE);
    assert(dma_config.PeriphDataAlignment == DMA_PDATAALIGN_BYTE);
    assert(dma_config.MemDataAlignment == DMA_MDATAALIGN_BYTE);
    assert(dma_config.Mode == DMA_NORMAL);
    assert(huart1.hdmarx == &hdma_usart1_rx);
    assert(irq_preempt[USART1_IRQn] == 1U && irq_sub[USART1_IRQn] == 0U);
    assert(irq_preempt[DMA1_Channel5_IRQn] == 1U && irq_sub[DMA1_Channel5_IRQn] == 1U);
    assert(irq_enabled[USART1_IRQn] && irq_enabled[DMA1_Channel5_IRQn]);

    reset_state();
    uart_status = HAL_ERROR;
    reason = setjmp(firmware_exit);
    if (reason == 0) { uart_dma_init(); }
    assert(reason == 2);

    reset_state();
    dma_status = HAL_ERROR;
    reason = setjmp(firmware_exit);
    if (reason == 0) { uart_dma_init(); }
    assert(reason == 2);
}

static void test_clock_and_startup(void)
{
    int reason;
    reset_state();
    SystemClock_Config();
    assert(osc_config.OscillatorType == RCC_OSCILLATORTYPE_HSE);
    assert(osc_config.HSEState == RCC_HSE_ON);
    assert(osc_config.PLL.PLLState == RCC_PLL_ON);
    assert(osc_config.PLL.PLLSource == RCC_PLLSOURCE_HSE);
    assert(osc_config.PLL.PLLMUL == RCC_PLL_MUL9);
    assert(clk_config.SYSCLKSource == RCC_SYSCLKSOURCE_PLLCLK);
    assert(clk_config.AHBCLKDivider == RCC_HCLK_DIV1);
    assert(clk_config.APB1CLKDivider == RCC_HCLK_DIV2);
    assert(clk_config.APB2CLKDivider == RCC_HCLK_DIV1);
    assert(flash_latency == FLASH_LATENCY_2);

    oscillator_status = HAL_ERROR;
    reason = setjmp(firmware_exit);
    if (reason == 0) { SystemClock_Config(); }
    assert(reason == 2);

    reset_state();
    clock_status = HAL_ERROR;
    reason = setjmp(firmware_exit);
    if (reason == 0) { SystemClock_Config(); }
    assert(reason == 2);

    reset_state();
    receive_status = HAL_ERROR;
    reason = setjmp(firmware_exit);
    if (reason == 0) { firmware_main(); }
    assert(reason == 2);
    assert(transmit_calls == 1U);

    reset_state();
    exit_on_receive = true;
    reason = setjmp(firmware_exit);
    if (reason == 0) { firmware_main(); }
    assert(reason == 1);
    assert(strcmp(tx_capture, "\r\n[BOOT] uart-dma-idle ready. type 'AT' for help\r\n") == 0);
    assert(transmit_calls == 1U);
    assert(receive_calls == 0U);
    assert(rx_buffer == NULL);
    assert(clock_flags == 0x0FU);
    assert((GPIOC->ODR & GPIO_PIN_13) == 0U);

    tick = 41U;
    SysTick_Handler();
    assert(tick == 42U);
}

int main(void)
{
    test_ring_buffer_wrap_and_full();
    test_command_parser();
    test_rx_event_callback();
    test_error_callback();
    test_uart_dma_init();
    test_clock_and_startup();
    puts("PASS: ring wrap/full, AT parser, HT/IDLE/TC rearm, error paths, UART/DMA init, clock, startup, SysTick");
    return 0;
}

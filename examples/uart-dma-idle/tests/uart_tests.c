#ifdef NDEBUG
#undef NDEBUG
#endif
#include <assert.h>
#include <setjmp.h>
#include <stdbool.h>
#include <stdlib.h>
#include "stm32f1xx_hal.h"

#define main firmware_main
#include "../main.c"
#undef main
#include "../stm32f1xx_it.c"

GPIO_TypeDef test_gpioa;
GPIO_TypeDef test_gpioc;
USART_TypeDef test_usart1;
DMA_Channel_TypeDef test_dma_channel5;
static jmp_buf stop_context;
static char transmitted[32768];
static unsigned starts;
static unsigned aborts;
static unsigned clears;
static unsigned resets;
static unsigned led_writes;
static unsigned uart_irqs;
static unsigned dma_irqs;
static unsigned enabled_irqs;
static uint32_t tick;
static bool first_start_stops;
static HAL_StatusTypeDef restart_result;
static HAL_StatusTypeDef abort_result;
static HAL_StatusTypeDef transmit_result;
static HAL_UART_RxEventTypeTypeDef event_type;

void test_enable_clock(GPIO_TypeDef *port) { (void)port; }
void test_disable_irq(void) { longjmp(stop_context, 2); }
void HAL_Init(void) { tick = 0U; }
uint32_t HAL_GetTick(void) { return tick; }
void HAL_IncTick(void) { tick++; }
void HAL_Delay(uint32_t delay_ms) { tick += delay_ms; }
void NVIC_SystemReset(void) { resets++; }

void HAL_GPIO_WritePin(GPIO_TypeDef *port, uint16_t pin, GPIO_PinState state)
{
    if (state == GPIO_PIN_SET) { port->ODR |= pin; }
    else { port->ODR &= ~(uint32_t)pin; }
    led_writes++;
}

void HAL_GPIO_Init(GPIO_TypeDef *port, GPIO_InitTypeDef *config)
{
    if (port == GPIOC) { assert((port->ODR & GPIO_PIN_13) == 0U); }
    else { assert(config->Pin == GPIO_PIN_9 || config->Pin == GPIO_PIN_10); }
}

HAL_StatusTypeDef HAL_RCC_OscConfig(RCC_OscInitTypeDef *config)
{
    assert(config->PLL.PLLMUL == RCC_PLL_MUL9);
    return HAL_OK;
}

HAL_StatusTypeDef HAL_RCC_ClockConfig(RCC_ClkInitTypeDef *config, uint32_t latency)
{
    assert(config->APB1CLKDivider == RCC_HCLK_DIV2);
    assert(config->APB2CLKDivider == RCC_HCLK_DIV1);
    assert(latency == FLASH_LATENCY_2);
    return HAL_OK;
}

HAL_StatusTypeDef HAL_UART_Init(UART_HandleTypeDef *handle)
{
    assert(handle->Instance == USART1);
    assert(handle->Init.BaudRate == 115200U);
    handle->RxState = HAL_UART_STATE_READY;
    return HAL_OK;
}

HAL_StatusTypeDef HAL_DMA_Init(DMA_HandleTypeDef *handle)
{
    assert(handle->Instance == DMA1_Channel5);
    assert(handle->Init.Mode == DMA_NORMAL);
    return HAL_OK;
}

void HAL_NVIC_SetPriority(uint32_t irq, uint32_t preemption, uint32_t subpriority)
{
    assert(irq == USART1_IRQn || irq == DMA1_Channel5_IRQn);
    assert(preemption == 1U && subpriority == 0U);
}

void HAL_NVIC_EnableIRQ(uint32_t irq)
{
    assert(irq == USART1_IRQn || irq == DMA1_Channel5_IRQn);
    enabled_irqs++;
}

void HAL_UART_IRQHandler(UART_HandleTypeDef *handle) { assert(handle == &huart1); uart_irqs++; }
void HAL_DMA_IRQHandler(DMA_HandleTypeDef *handle) { assert(handle == &hdma_usart1_rx); dma_irqs++; }

HAL_StatusTypeDef HAL_UARTEx_ReceiveToIdle_DMA(UART_HandleTypeDef *handle, uint8_t *buffer, uint16_t length)
{
    assert(handle == &huart1);
    assert(buffer == g_dma_rx_buf && length == DMA_RX_BUF_SIZE);
    assert(handle->RxState == HAL_UART_STATE_READY);
    starts++;
    if (first_start_stops) { longjmp(stop_context, 1); }
    if (restart_result == HAL_OK) { handle->RxState = HAL_UART_STATE_BUSY_RX; }
    return restart_result;
}

HAL_UART_RxEventTypeTypeDef HAL_UARTEx_GetRxEventType(UART_HandleTypeDef *handle)
{
    assert(handle == &huart1);
    return event_type;
}

HAL_StatusTypeDef HAL_UART_AbortReceive(UART_HandleTypeDef *handle)
{
    assert(handle == &huart1);
    aborts++;
    if (abort_result == HAL_OK) { handle->RxState = HAL_UART_STATE_READY; handle->ErrorCode = 0U; }
    return abort_result;
}

void test_clear_rx_error(UART_HandleTypeDef *handle) { assert(handle == &huart1); clears++; }

HAL_StatusTypeDef HAL_UART_Transmit(UART_HandleTypeDef *handle, uint8_t *buffer, uint16_t length, uint32_t timeout)
{
    assert(handle == &huart1 && timeout == 100U);
    size_t used = strlen(transmitted);
    assert(used + length < sizeof(transmitted));
    memcpy(transmitted + used, buffer, length);
    transmitted[used + length] = '\0';
    return transmit_result;
}

static void reset_fixture(void)
{
    memset(&test_gpioa, 0, sizeof(test_gpioa));
    memset(&test_gpioc, 0, sizeof(test_gpioc));
    memset(transmitted, 0, sizeof(transmitted));
    g_stats = (uart_stats_t){0};
    huart1 = (UART_HandleTypeDef){0};
    huart1.Instance = USART1;
    rb_init(&g_rb);
    g_line_len = g_line_discard = 0U;
    g_echo_on = 0U;
    g_led_state = 0U;
    starts = aborts = clears = resets = led_writes = uart_irqs = dma_irqs = enabled_irqs = 0U;
    first_start_stops = false;
    restart_result = abort_result = transmit_result = HAL_OK;
}

static void feed(const char *text)
{
    while (*text != '\0') { cmd_process_char(*text++); }
}

static void drain(void)
{
    uint16_t value;
    while (rb_pop(&g_rb, &value) == 0) { stream_process(value); }
}

static void deliver(const uint8_t *bytes, uint16_t length, HAL_UART_RxEventTypeTypeDef event)
{
    assert(length <= DMA_RX_BUF_SIZE);
    memcpy(g_dma_rx_buf, bytes, length);
    event_type = event;
    huart1.RxState = event == HAL_UART_RXEVENT_HT ? HAL_UART_STATE_BUSY_RX : HAL_UART_STATE_READY;
    HAL_UARTEx_RxEventCallback(&huart1, length);
}

static void test_ht(void)
{
    uint8_t bytes[DMA_RX_BUF_SIZE];
    for (unsigned index = 0; index < sizeof(bytes); index++) { bytes[index] = (uint8_t)index; }
    deliver(bytes, 32U, HAL_UART_RXEVENT_HT);
    assert(atomic_load(&g_rb.head) == 0U && starts == 0U && g_stats.rx_bytes == 0U);
    deliver(bytes, 40U, HAL_UART_RXEVENT_IDLE);
    assert(atomic_load(&g_rb.head) == 40U && starts == 1U && g_stats.rx_bytes == 40U);
    deliver(bytes, 64U, HAL_UART_RXEVENT_HT);
    deliver(bytes, 64U, HAL_UART_RXEVENT_TC);
    assert(atomic_load(&g_rb.head) == 104U && starts == 2U && g_stats.rx_bytes == 104U);
    for (unsigned index = 0; index < 104U; index++)
    {
        uint16_t value;
        assert(rb_pop(&g_rb, &value) == 0);
        assert(value == (index < 40U ? index : index - 40U));
    }
    UART_HandleTypeDef other = {0};
    HAL_UARTEx_RxEventCallback(&other, 4U);
    HAL_UART_ErrorCallback(&other);
    assert(starts == 2U && aborts == 0U);
    deliver(bytes, 0U, HAL_UART_RXEVENT_IDLE);
    assert(starts == 3U && atomic_load(&g_rb.head) == atomic_load(&g_rb.tail));
}

static void test_failure(unsigned failure)
{
    int reason = setjmp(stop_context);
    if (reason == 0)
    {
        if (failure == 0U)
        {
            restart_result = HAL_ERROR;
            deliver((const uint8_t *)"AT\r", 3U, HAL_UART_RXEVENT_IDLE);
        }
        else
        {
            if (failure == 1U) { restart_result = HAL_BUSY; }
            if (failure == 2U) { abort_result = HAL_TIMEOUT; }
            huart1.ErrorCode = HAL_UART_ERROR_ORE;
            HAL_UART_ErrorCallback(&huart1);
        }
        assert(!"failure did not stop");
    }
    assert(reason == 2 && g_stats.rearm_failures == 1U);
    if (failure == 2U) { assert(starts == 0U && clears == 0U); }
    else { assert(starts == 1U); }
}

static void test_error(void)
{
    feed("AT+LED=");
    huart1.RxState = HAL_UART_STATE_BUSY_RX;
    huart1.ErrorCode = HAL_UART_ERROR_ORE | HAL_UART_ERROR_FE;
    HAL_UART_ErrorCallback(&huart1);
    assert(aborts == 1U && clears == 1U && starts == 1U);
    assert(g_stats.last_uart_error == (HAL_UART_ERROR_ORE | HAL_UART_ERROR_FE));
    assert(g_stats.uart_errors == 1U && g_rb.gap_pending == 1U);
    const char *suffix = "1\rAT\r";
    rb_push(&g_rb, (const uint8_t *)suffix, (uint16_t)strlen(suffix));
    drain();
    assert(led_writes == 0U && strstr(transmitted, "rx gap") != NULL);
    assert(strstr(transmitted, "OK\r\n") != NULL);
    reset_fixture();
    test_failure(1U);
    reset_fixture();
    test_failure(2U);
}

static void test_ring(void)
{
    uint8_t bytes[RING_BUF_SIZE];
    for (unsigned index = 0; index < sizeof(bytes); index++) { bytes[index] = (uint8_t)index; }
    for (unsigned round = 0; round < 4U; round++)
    {
        rb_push(&g_rb, bytes, RING_BUF_SIZE - 1U);
        for (unsigned index = 0; index < RING_BUF_SIZE - 1U; index++)
        {
            uint16_t value;
            assert(rb_pop(&g_rb, &value) == 0 && value == bytes[index]);
        }
    }
    uint16_t value;
    assert(rb_pop(&g_rb, &value) == -1 && g_stats.dropped_bytes == 0U);
    rb_push(&g_rb, bytes, RING_BUF_SIZE);
    assert(g_stats.dropped_bytes == 1U && g_rb.gap_pending == 1U);
    assert(rb_pop(&g_rb, &value) == 0);
    rb_push(&g_rb, bytes, 1U);
    assert(g_stats.dropped_bytes == 2U && g_rb.gap_pending == 1U);
    unsigned markers = 0U;
    while (rb_pop(&g_rb, &value) == 0) { if (value == RX_GAP) { markers++; } }
    assert(markers == 1U);
    rb_push(&g_rb, (const uint8_t *)"\nAT\n", 4U);
    drain();
    assert(g_rb.gap_pending == 0U && strstr(transmitted, "OK\r\n") != NULL);
}

static void test_stream(void)
{
    deliver((const uint8_t *)"AT+LE", 5U, HAL_UART_RXEVENT_IDLE);
    drain();
    assert(led_writes == 0U);
    deliver((const uint8_t *)"D=1\r\n", 5U, HAL_UART_RXEVENT_IDLE);
    drain();
    assert(led_writes == 1U && g_led_state == 1U);
    uint8_t bytes[64];
    memset(bytes, '\n', sizeof(bytes));
    bytes[63] = 'A';
    deliver(bytes, 32U, HAL_UART_RXEVENT_HT);
    deliver(bytes, 64U, HAL_UART_RXEVENT_TC);
    drain();
    deliver((const uint8_t *)"T\r\n", 3U, HAL_UART_RXEVENT_IDLE);
    drain();
    assert(strcmp(transmitted, "OK\r\nOK\r\n") == 0);
}

static void test_parser(void)
{
    feed("AT\r\n\nAT+LED=1\rAT+LED?\nAT+ECHO=1\nAT+INFO\rAT+RESET\n");
    assert(led_writes == 1U && g_led_state == 1U && g_echo_on == 1U && resets == 1U);
    assert(strstr(transmitted, "+LED:1\r\nOK") != NULL);
    assert(strstr(transmitted, "> AT+INFO\r\n") != NULL);
    assert(strstr(transmitted, "v1.1") != NULL);
    reset_fixture();
    for (unsigned index = 0; index < CMD_LINE_MAX - 1U; index++) { cmd_process_char('X'); }
    assert(g_line_discard == 0U);
    feed("\n");
    assert(strstr(transmitted, "unknown command") != NULL && strstr(transmitted, "line too long") == NULL);
    reset_fixture();
    for (unsigned index = 0; index < CMD_LINE_MAX; index++) { cmd_process_char('X'); }
    feed("AT+RESET\rAT+LED=1\n");
    assert(resets == 0U && led_writes == 1U && g_led_state == 1U);
    assert(strstr(transmitted, "ERROR: line too long\r\n") == transmitted);
}

static void test_overflow(void)
{
    uint8_t bytes[RING_BUF_SIZE - 1U];
    memset(bytes, '\n', sizeof(bytes));
    memcpy(bytes + sizeof(bytes) - 7U, "AT+LED=", 7U);
    rb_push(&g_rb, bytes, sizeof(bytes));
    rb_push(&g_rb, (const uint8_t *)"0", 1U);
    assert(g_stats.dropped_bytes == 1U && g_stats.stream_gaps == 1U);
    drain();
    assert(g_line_len == 7U && led_writes == 0U);
    rb_push(&g_rb, (const uint8_t *)"1\rAT+LED=1\n", 11U);
    drain();
    assert(led_writes == 1U && g_led_state == 1U);
    assert(strcmp(transmitted, "ERROR: rx gap, discard until newline\r\nOK\r\n") == 0);
}

static void test_invalid(void)
{
    feed("AT+LED=\nAT+LED=2\nAT+LED=1x\nAT+ECHO=\nAT+ECHO=2\nAT+ECHO=0x\n");
    assert(led_writes == 0U && g_echo_on == 0U && strstr(transmitted, "OK") == NULL);
    feed("AT+RESET");
    cmd_process_char('\0');
    feed("AT+RESET\nAT\n");
    assert(resets == 0U && strstr(transmitted, "invalid character") != NULL);
    assert(strstr(transmitted, "OK\r\n") != NULL);
}

static void test_startup(void)
{
    first_start_stops = true;
    int reason = setjmp(stop_context);
    if (reason == 0) { firmware_main(); }
    assert(reason == 1 && starts == 1U && enabled_irqs == 2U);
    assert(huart1.hdmarx == &hdma_usart1_rx);
    assert(strstr(transmitted, "[BOOT]") != NULL);
    SysTick_Handler();
    assert(tick == 1U);
    USART1_IRQHandler();
    DMA1_Channel5_IRQHandler();
    assert(uart_irqs == 1U && dma_irqs == 1U);
}

static void test_stats(void)
{
    g_stats.rx_bytes = 123U;
    g_stats.dropped_bytes = 4U;
    g_stats.uart_errors = 2U;
    feed("AT+STATS\r");
    assert(strstr(transmitted, "+STATS:rx=123,drop=4,gaps=0,errors=2") != NULL);
    transmit_result = HAL_TIMEOUT;
    uart_send("timeout");
    assert(g_stats.tx_failures == 1U);
}

int main(int argc, char **argv)
{
    assert(argc == 2);
    reset_fixture();
    if (strcmp(argv[1], "uart-ht") == 0) { test_ht(); }
    else if (strcmp(argv[1], "uart-rearm") == 0) { test_failure(0U); }
    else if (strcmp(argv[1], "uart-error") == 0) { test_error(); }
    else if (strcmp(argv[1], "ring") == 0) { test_ring(); }
    else if (strcmp(argv[1], "stream") == 0) { test_stream(); }
    else if (strcmp(argv[1], "parser") == 0) { test_parser(); }
    else if (strcmp(argv[1], "overflow") == 0) { test_overflow(); }
    else if (strcmp(argv[1], "invalid") == 0) { test_invalid(); }
    else if (strcmp(argv[1], "startup") == 0) { test_startup(); }
    else if (strcmp(argv[1], "stats") == 0) { test_stats(); }
    else { fprintf(stderr, "Unknown case: %s\n", argv[1]); return 1; }
    printf("PASS %s: actual firmware with simulated HAL; hardware unverified\n", argv[1]);
    return 0;
}

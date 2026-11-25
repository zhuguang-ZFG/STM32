#include <assert.h>
#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
#include "stm32f1xx_hal.h"

#define main firmware_main
#include "../main.c"
#undef main
#include "../stm32f1xx_it.c"

GPIO_TypeDef test_gpioc;
DMA_Channel_TypeDef test_dma1_ch1;

typedef enum {
    TEST_DMA_COPY_OK,
    TEST_DMA_COPY_CORRUPT,
    TEST_DMA_ERROR,
    TEST_DMA_NO_COMPLETE,
    TEST_DMA_START_FAIL
} test_dma_mode_t;

static test_dma_mode_t dma_mode;
static uint32_t tick;
static uint32_t clock_flags;
static uint32_t dma_init_calls;
static uint32_t dma_start_calls;
static uint32_t dma_src;
static uint32_t dma_dst;
static uint32_t dma_length;
static uint32_t dma_callback_id;
static pDMA_CallbackTypeDef dma_callback;
static HAL_StatusTypeDef init_status;
static HAL_StatusTypeDef start_status;
static GPIO_InitTypeDef gpio_config;
static uint32_t irq_preempt[64];
static uint32_t irq_sub[64];
static bool irq_enabled[64];

void test_enable_clock(uint32_t mask) { clock_flags |= mask; }
void HAL_Init(void) { }
uint32_t HAL_GetTick(void) { return tick++; }
void HAL_IncTick(void) { tick++; }
void HAL_Delay(uint32_t delay_ms) { (void)delay_ms; }

void HAL_GPIO_Init(GPIO_TypeDef *port, GPIO_InitTypeDef *config)
{
    assert(port == GPIOC);
    gpio_config = *config;
}

void HAL_GPIO_WritePin(GPIO_TypeDef *port, uint16_t pin, GPIO_PinState state)
{
    assert(port == GPIOC);
    assert(pin == GPIO_PIN_13);
    if (state == GPIO_PIN_SET) { port->ODR |= pin; }
    else { port->ODR &= ~(uint32_t)pin; }
}

HAL_StatusTypeDef HAL_RCC_OscConfig(RCC_OscInitTypeDef *config) { (void)config; return HAL_OK; }
HAL_StatusTypeDef HAL_RCC_ClockConfig(RCC_ClkInitTypeDef *config, uint32_t latency)
{
    (void)config; (void)latency; return HAL_OK;
}

HAL_StatusTypeDef HAL_DMA_Init(DMA_HandleTypeDef *hdma)
{
    assert(hdma == &hdma_memcopy);
    dma_init_calls++;
    return init_status;
}

HAL_StatusTypeDef HAL_DMA_RegisterCallback(DMA_HandleTypeDef *hdma, uint32_t callback_id, pDMA_CallbackTypeDef callback)
{
    assert(hdma == &hdma_memcopy);
    if (callback_id == HAL_DMA_XFER_CPLT_CB_ID) { hdma->XferCpltCallback = callback; }
    else { hdma->XferErrorCallback = callback; }
    return HAL_OK;
}

HAL_StatusTypeDef HAL_DMA_Start_IT(DMA_HandleTypeDef *hdma, uint32_t src, uint32_t dst, uint32_t length)
{
    assert(hdma == &hdma_memcopy);
    dma_start_calls++;
    dma_src = src;
    dma_dst = dst;
    dma_length = length;
    if (dma_mode == TEST_DMA_START_FAIL) { return HAL_ERROR; }
    if (dma_mode == TEST_DMA_COPY_OK || dma_mode == TEST_DMA_COPY_CORRUPT) {
        memcpy(g_dma_dst, g_dma_src, length * sizeof(uint32_t));
        if (dma_mode == TEST_DMA_COPY_CORRUPT) { g_dma_dst[0] ^= 1U; }
        hdma->State = 0U;
        if (hdma->XferCpltCallback != NULL) { hdma->XferCpltCallback(hdma); }
    } else if (dma_mode == TEST_DMA_ERROR) {
        hdma->State = 0U;
        hdma->ErrorCode = 1U;
        if (hdma->XferErrorCallback != NULL) { hdma->XferErrorCallback(hdma); }
    }
    return HAL_OK;
}

void HAL_DMA_IRQHandler(DMA_HandleTypeDef *hdma) { assert(hdma == &hdma_memcopy); }
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

static void reset_state(void)
{
    memset(&test_gpioc, 0, sizeof(test_gpioc));
    memset(&test_dma1_ch1, 0, sizeof(test_dma1_ch1));
    test_gpioc.ODR = 0xFFFFFFFFU;
    memset(&hdma_memcopy, 0, sizeof(hdma_memcopy));
    memset(g_dma_src, 0, sizeof(g_dma_src));
    memset(g_dma_dst, 0, sizeof(g_dma_dst));
    dma_mode = TEST_DMA_COPY_OK;
    tick = 0U;
    clock_flags = 0U;
    dma_init_calls = 0U;
    dma_start_calls = 0U;
    dma_src = 0U;
    dma_dst = 0U;
    dma_length = 0U;
    dma_callback_id = 0U;
    dma_callback = NULL;
    init_status = HAL_OK;
    start_status = HAL_OK;
    memset(&gpio_config, 0, sizeof(gpio_config));
    memset(irq_preempt, 0, sizeof(irq_preempt));
    memset(irq_sub, 0, sizeof(irq_sub));
    memset(irq_enabled, 0, sizeof(irq_enabled));
}

static void test_success_copies_1024_words(void)
{
    reset_state();
    assert(dma_memcopy_run() == DMA_MEMCOPY_SUCCESS);
    assert(dma_init_calls == 1U);
    assert(dma_start_calls == 1U);
    assert(dma_src == (uint32_t)(uintptr_t)g_dma_src);
    assert(dma_dst == (uint32_t)(uintptr_t)g_dma_dst);
    assert(dma_length == 1024U);
    assert(memcmp(g_dma_src, g_dma_dst, sizeof(g_dma_src)) == 0);
    assert(hdma_memcopy.Instance == DMA1_Channel1);
    assert(hdma_memcopy.Init.Direction == DMA_MEMORY_TO_MEMORY);
    assert(hdma_memcopy.Init.PeriphInc == DMA_PINC_ENABLE);
    assert(hdma_memcopy.Init.MemInc == DMA_MINC_ENABLE);
    assert(hdma_memcopy.Init.PeriphDataAlignment == DMA_PDATAALIGN_WORD);
    assert(hdma_memcopy.Init.MemDataAlignment == DMA_MDATAALIGN_WORD);
    assert(hdma_memcopy.Init.Mode == DMA_NORMAL);
    assert(hdma_memcopy.Init.Priority == DMA_PRIORITY_HIGH);
    assert(clock_flags == 3U);
    assert(irq_enabled[DMA1_Channel1_IRQn]);
}

static void test_mismatch_is_not_success(void)
{
    reset_state();
    dma_mode = TEST_DMA_COPY_CORRUPT;
    assert(dma_memcopy_run() == DMA_MEMCOPY_MISMATCH);
}

static void test_dma_error_is_reported(void)
{
    reset_state();
    dma_mode = TEST_DMA_ERROR;
    assert(dma_memcopy_run() == DMA_MEMCOPY_DMA_ERROR);
}

static void test_timeout_is_reported(void)
{
    reset_state();
    dma_mode = TEST_DMA_NO_COMPLETE;
    assert(dma_memcopy_run() == DMA_MEMCOPY_TIMEOUT);
}

static void test_start_failure_is_reported(void)
{
    reset_state();
    dma_mode = TEST_DMA_START_FAIL;
    assert(dma_memcopy_run() == DMA_MEMCOPY_START_ERROR);
}

static void test_init_failure_is_reported(void)
{
    reset_state();
    init_status = HAL_ERROR;
    assert(dma_memcopy_run() == DMA_MEMCOPY_CONFIG_ERROR);
    assert(dma_start_calls == 0U);
}

static void test_timeout_survives_tick_wrap(void)
{
    reset_state();
    dma_mode = TEST_DMA_NO_COMPLETE;
    tick = UINT32_MAX - 3U;
    assert(dma_memcopy_run() == DMA_MEMCOPY_TIMEOUT);
}

static void test_failure_blink_codes_are_distinct(void)
{
    assert(result_blink_code(DMA_MEMCOPY_SUCCESS) == 0U);
    assert(result_blink_code(DMA_MEMCOPY_CONFIG_ERROR) == 1U);
    assert(result_blink_code(DMA_MEMCOPY_START_ERROR) == 2U);
    assert(result_blink_code(DMA_MEMCOPY_DMA_ERROR) == 3U);
    assert(result_blink_code(DMA_MEMCOPY_TIMEOUT) == 4U);
    assert(result_blink_code(DMA_MEMCOPY_MISMATCH) == 5U);
}

int main(void)
{
    test_success_copies_1024_words();
    test_mismatch_is_not_success();
    test_dma_error_is_reported();
    test_timeout_is_reported();
    test_start_failure_is_reported();
    test_init_failure_is_reported();
    test_timeout_survives_tick_wrap();
    test_failure_blink_codes_are_distinct();
    puts("PASS: dma-memcopy production-flow regressions");
    return 0;
}

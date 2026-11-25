#include "stm32f1xx_hal.h"
#include <stdbool.h>
#include <stdint.h>
#include <string.h>

#define DMA_WORD_COUNT       1024U
#define DMA_TRANSFER_BYTES   (DMA_WORD_COUNT * sizeof(uint32_t))
#define DMA_TIMEOUT_MS       1000U
#define LED_PORT             GPIOC
#define LED_PIN              GPIO_PIN_13

typedef enum
{
    DMA_MEMCOPY_SUCCESS = 0,
    DMA_MEMCOPY_CONFIG_ERROR,
    DMA_MEMCOPY_START_ERROR,
    DMA_MEMCOPY_DMA_ERROR,
    DMA_MEMCOPY_TIMEOUT,
    DMA_MEMCOPY_MISMATCH
} dma_memcopy_result_t;

typedef enum
{
    DMA_WAIT_DONE = 0,
    DMA_WAIT_ERROR,
    DMA_WAIT_TIMEOUT
} dma_wait_result_t;

DMA_HandleTypeDef hdma_memcopy;
uint32_t g_dma_src[DMA_WORD_COUNT];
uint32_t g_dma_dst[DMA_WORD_COUNT];

static volatile uint8_t g_dma_done;
static volatile uint8_t g_dma_error;

_Static_assert(sizeof(g_dma_src) == 4096U, "DMA source must be exactly 4 KiB");
_Static_assert(sizeof(g_dma_dst) == 4096U, "DMA destination must be exactly 4 KiB");

void HAL_DMA_XferCpltCallback(DMA_HandleTypeDef *hdma);
void HAL_DMA_XferErrorCallback(DMA_HandleTypeDef *hdma);

static void SystemClock_Config(void);
static void Error_Handler(void);
static void led_init(void);
static HAL_StatusTypeDef dma_memcopy_init(void);
static dma_memcopy_result_t dma_memcopy_run(void);
static void fill_source(void);
static bool buffers_equal(void);
static dma_wait_result_t wait_for_dma(uint32_t timeout_ms);
static uint8_t result_blink_code(dma_memcopy_result_t result);
static void indicate_result(dma_memcopy_result_t result);

int main(void)
{
    HAL_Init();
    led_init();
    SystemClock_Config();

    dma_memcopy_result_t result = dma_memcopy_run();
    indicate_result(result);
    while (1)
    {
        /* The result is latched on PC13; no further DMA work is started. */
    }
}

static void SystemClock_Config(void)
{
    RCC_OscInitTypeDef osc = {0};
    RCC_ClkInitTypeDef clk = {0};

    osc.OscillatorType = RCC_OSCILLATORTYPE_HSE;
    osc.HSEState = RCC_HSE_ON;
    osc.HSEPredivValue = RCC_HSE_PREDIV_DIV1;
    osc.PLL.PLLState = RCC_PLL_ON;
    osc.PLL.PLLSource = RCC_PLLSOURCE_HSE;
    osc.PLL.PLLMUL = RCC_PLL_MUL9;
    if (HAL_RCC_OscConfig(&osc) != HAL_OK)
    {
        Error_Handler();
    }

    clk.ClockType = RCC_CLOCKTYPE_SYSCLK | RCC_CLOCKTYPE_HCLK |
                    RCC_CLOCKTYPE_PCLK1 | RCC_CLOCKTYPE_PCLK2;
    clk.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
    clk.AHBCLKDivider = RCC_SYSCLK_DIV1;
    clk.APB1CLKDivider = RCC_HCLK_DIV2;
    clk.APB2CLKDivider = RCC_HCLK_DIV1;
    if (HAL_RCC_ClockConfig(&clk, FLASH_LATENCY_2) != HAL_OK)
    {
        Error_Handler();
    }
}

static void Error_Handler(void)
{
    __disable_irq();
    while (1)
    {
        HAL_GPIO_WritePin(LED_PORT, LED_PIN, GPIO_PIN_RESET);
        HAL_Delay(100U);
        HAL_GPIO_WritePin(LED_PORT, LED_PIN, GPIO_PIN_SET);
        HAL_Delay(400U);
    }
}

static void led_init(void)
{
    GPIO_InitTypeDef gpio = {0};

    __HAL_RCC_GPIOC_CLK_ENABLE();
    gpio.Pin = LED_PIN;
    gpio.Mode = GPIO_MODE_OUTPUT_PP;
    gpio.Pull = GPIO_NOPULL;
    gpio.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(LED_PORT, &gpio);
    HAL_GPIO_WritePin(LED_PORT, LED_PIN, GPIO_PIN_SET);
}

static HAL_StatusTypeDef dma_memcopy_init(void)
{
    __HAL_RCC_DMA1_CLK_ENABLE();

    hdma_memcopy.Instance = DMA1_Channel1;
    hdma_memcopy.Init.Direction = DMA_MEMORY_TO_MEMORY;
    hdma_memcopy.Init.PeriphInc = DMA_PINC_ENABLE;
    hdma_memcopy.Init.MemInc = DMA_MINC_ENABLE;
    hdma_memcopy.Init.PeriphDataAlignment = DMA_PDATAALIGN_WORD;
    hdma_memcopy.Init.MemDataAlignment = DMA_MDATAALIGN_WORD;
    hdma_memcopy.Init.Mode = DMA_NORMAL;
    hdma_memcopy.Init.Priority = DMA_PRIORITY_HIGH;

    if (HAL_DMA_Init(&hdma_memcopy) != HAL_OK)
    {
        return HAL_ERROR;
    }
    if (HAL_DMA_RegisterCallback(&hdma_memcopy, HAL_DMA_XFER_CPLT_CB_ID,
                                 HAL_DMA_XferCpltCallback) != HAL_OK)
    {
        return HAL_ERROR;
    }
    if (HAL_DMA_RegisterCallback(&hdma_memcopy, HAL_DMA_XFER_ERROR_CB_ID,
                                 HAL_DMA_XferErrorCallback) != HAL_OK)
    {
        return HAL_ERROR;
    }

    HAL_NVIC_SetPriority(DMA1_Channel1_IRQn, 0U, 0U);
    HAL_NVIC_EnableIRQ(DMA1_Channel1_IRQn);
    return HAL_OK;
}

static void fill_source(void)
{
    uint32_t state = 0x12345678U;
    for (uint32_t i = 0U; i < DMA_WORD_COUNT; ++i)
    {
        state ^= state << 13;
        state ^= state >> 17;
        state ^= state << 5;
        g_dma_src[i] = state;
    }
}

static bool buffers_equal(void)
{
    return memcmp(g_dma_src, g_dma_dst, DMA_TRANSFER_BYTES) == 0;
}

static dma_wait_result_t wait_for_dma(uint32_t timeout_ms)
{
    uint32_t start = HAL_GetTick();
    while ((g_dma_done == 0U) && (g_dma_error == 0U))
    {
        if ((uint32_t)(HAL_GetTick() - start) >= timeout_ms)
        {
            return DMA_WAIT_TIMEOUT;
        }
    }
    return g_dma_error != 0U ? DMA_WAIT_ERROR : DMA_WAIT_DONE;
}

static dma_memcopy_result_t dma_memcopy_run(void)
{
    g_dma_done = 0U;
    g_dma_error = 0U;

    led_init();
    if (dma_memcopy_init() != HAL_OK)
    {
        return DMA_MEMCOPY_CONFIG_ERROR;
    }

    fill_source();
    memset(g_dma_dst, 0xA5, DMA_TRANSFER_BYTES);

    if (HAL_DMA_Start_IT(&hdma_memcopy,
                         (uint32_t)(uintptr_t)g_dma_src,
                         (uint32_t)(uintptr_t)g_dma_dst,
                         DMA_WORD_COUNT) != HAL_OK)
    {
        return DMA_MEMCOPY_START_ERROR;
    }

    dma_wait_result_t wait = wait_for_dma(DMA_TIMEOUT_MS);
    if (wait == DMA_WAIT_ERROR)
    {
        return DMA_MEMCOPY_DMA_ERROR;
    }
    if (wait == DMA_WAIT_TIMEOUT)
    {
        return DMA_MEMCOPY_TIMEOUT;
    }
    return buffers_equal() ? DMA_MEMCOPY_SUCCESS : DMA_MEMCOPY_MISMATCH;
}

static uint8_t result_blink_code(dma_memcopy_result_t result)
{
    switch (result)
    {
        case DMA_MEMCOPY_SUCCESS:        return 0U;
        case DMA_MEMCOPY_CONFIG_ERROR:   return 1U;
        case DMA_MEMCOPY_START_ERROR:    return 2U;
        case DMA_MEMCOPY_DMA_ERROR:      return 3U;
        case DMA_MEMCOPY_TIMEOUT:        return 4U;
        case DMA_MEMCOPY_MISMATCH:       return 5U;
        default:                         return 5U;
    }
}

static void indicate_result(dma_memcopy_result_t result)
{
    uint8_t blinks = result_blink_code(result);
    if (blinks == 0U)
    {
        HAL_GPIO_WritePin(LED_PORT, LED_PIN, GPIO_PIN_RESET);
        return;
    }

    while (1)
    {
        for (uint8_t i = 0U; i < blinks; ++i)
        {
            HAL_GPIO_WritePin(LED_PORT, LED_PIN, GPIO_PIN_RESET);
            HAL_Delay(120U);
            HAL_GPIO_WritePin(LED_PORT, LED_PIN, GPIO_PIN_SET);
            HAL_Delay(120U);
        }
        HAL_Delay(800U);
    }
}

void HAL_DMA_XferCpltCallback(DMA_HandleTypeDef *hdma)
{
    if (hdma == &hdma_memcopy)
    {
        g_dma_done = 1U;
    }
}

void HAL_DMA_XferErrorCallback(DMA_HandleTypeDef *hdma)
{
    if (hdma == &hdma_memcopy)
    {
        g_dma_error = 1U;
    }
}

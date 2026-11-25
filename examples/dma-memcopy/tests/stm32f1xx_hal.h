#ifndef TEST_STM32F1XX_HAL_H
#define TEST_STM32F1XX_HAL_H

#include <stdint.h>

typedef struct { uint32_t ODR; } GPIO_TypeDef;
typedef struct { uint32_t Pin; uint32_t Mode; uint32_t Pull; uint32_t Speed; } GPIO_InitTypeDef;
typedef struct {
    uint32_t OscillatorType; uint32_t HSEState; uint32_t HSEPredivValue; uint32_t HSIState;
    struct { uint32_t PLLState; uint32_t PLLSource; uint32_t PLLMUL; } PLL;
} RCC_OscInitTypeDef;
typedef struct {
    uint32_t ClockType; uint32_t SYSCLKSource; uint32_t AHBCLKDivider;
    uint32_t APB1CLKDivider; uint32_t APB2CLKDivider;
} RCC_ClkInitTypeDef;
typedef struct { uint32_t CCR; uint32_t CNDTR; uint32_t CPAR; uint32_t CMAR; } DMA_Channel_TypeDef;
typedef struct {
    uint32_t Direction; uint32_t PeriphInc; uint32_t MemInc;
    uint32_t PeriphDataAlignment; uint32_t MemDataAlignment; uint32_t Mode; uint32_t Priority;
} DMA_InitTypeDef;
typedef struct DMA_HandleTypeDef DMA_HandleTypeDef;
struct DMA_HandleTypeDef {
    DMA_Channel_TypeDef *Instance;
    DMA_InitTypeDef Init;
    uint32_t State;
    uint32_t ErrorCode;
    void (*XferCpltCallback)(DMA_HandleTypeDef *hdma);
    void (*XferErrorCallback)(DMA_HandleTypeDef *hdma);
};

typedef enum { HAL_OK = 0, HAL_ERROR = 1, HAL_BUSY = 2 } HAL_StatusTypeDef;
typedef enum { GPIO_PIN_RESET = 0, GPIO_PIN_SET = 1 } GPIO_PinState;
typedef void (*pDMA_CallbackTypeDef)(DMA_HandleTypeDef *hdma);

extern GPIO_TypeDef test_gpioc;
extern DMA_Channel_TypeDef test_dma1_ch1;
#define GPIOC (&test_gpioc)
#define DMA1_Channel1 (&test_dma1_ch1)

#define GPIO_PIN_13 (1U << 13)
#define GPIO_MODE_OUTPUT_PP 1U
#define GPIO_NOPULL 0U
#define GPIO_SPEED_FREQ_LOW 2U

#define DMA_MEMORY_TO_MEMORY 1U
#define DMA_PINC_ENABLE 1U
#define DMA_MINC_ENABLE 1U
#define DMA_PDATAALIGN_WORD 2U
#define DMA_MDATAALIGN_WORD 2U
#define DMA_NORMAL 0U
#define DMA_PRIORITY_HIGH 2U
#define HAL_DMA_XFER_CPLT_CB_ID 0U
#define HAL_DMA_XFER_ERROR_CB_ID 1U

#define RCC_OSCILLATORTYPE_HSE 1U
#define RCC_HSE_ON 1U
#define RCC_HSE_PREDIV_DIV1 1U
#define RCC_HSI_ON 1U
#define RCC_PLL_ON 1U
#define RCC_PLLSOURCE_HSE 1U
#define RCC_PLL_MUL9 9U
#define RCC_CLOCKTYPE_HCLK 1U
#define RCC_CLOCKTYPE_SYSCLK 2U
#define RCC_CLOCKTYPE_PCLK1 4U
#define RCC_CLOCKTYPE_PCLK2 8U
#define RCC_SYSCLKSOURCE_PLLCLK 1U
#define RCC_SYSCLK_DIV1 1U
#define RCC_HCLK_DIV1 1U
#define RCC_HCLK_DIV2 2U
#define FLASH_LATENCY_2 2U

#define DMA1_Channel1_IRQn 11
#define __HAL_RCC_GPIOC_CLK_ENABLE() test_enable_clock(1U)
#define __HAL_RCC_DMA1_CLK_ENABLE() test_enable_clock(2U)
#define __disable_irq() ((void)0U)

void test_enable_clock(uint32_t mask);
void HAL_Init(void);
uint32_t HAL_GetTick(void);
void HAL_IncTick(void);
void HAL_Delay(uint32_t delay_ms);
void HAL_GPIO_Init(GPIO_TypeDef *port, GPIO_InitTypeDef *config);
void HAL_GPIO_WritePin(GPIO_TypeDef *port, uint16_t pin, GPIO_PinState state);
HAL_StatusTypeDef HAL_RCC_OscConfig(RCC_OscInitTypeDef *config);
HAL_StatusTypeDef HAL_RCC_ClockConfig(RCC_ClkInitTypeDef *config, uint32_t latency);
HAL_StatusTypeDef HAL_DMA_Init(DMA_HandleTypeDef *hdma);
HAL_StatusTypeDef HAL_DMA_Start_IT(DMA_HandleTypeDef *hdma, uint32_t src, uint32_t dst, uint32_t length);
HAL_StatusTypeDef HAL_DMA_RegisterCallback(DMA_HandleTypeDef *hdma, uint32_t callback_id, pDMA_CallbackTypeDef callback);
void HAL_DMA_IRQHandler(DMA_HandleTypeDef *hdma);
void HAL_NVIC_SetPriority(int irq, uint32_t preempt, uint32_t sub);
void HAL_NVIC_EnableIRQ(int irq);

#endif

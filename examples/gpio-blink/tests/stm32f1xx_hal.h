#ifndef TEST_STM32F1XX_HAL_H
#define TEST_STM32F1XX_HAL_H

#include <stdint.h>

typedef struct { uint32_t ODR; uint32_t BSRR; } GPIO_TypeDef;
typedef struct { uint32_t Pin; uint32_t Mode; uint32_t Pull; uint32_t Speed; } GPIO_InitTypeDef;
typedef struct {
    uint32_t OscillatorType; uint32_t HSEState; uint32_t HSEPredivValue; uint32_t HSIState;
    struct { uint32_t PLLState; uint32_t PLLSource; uint32_t PLLMUL; } PLL;
} RCC_OscInitTypeDef;
typedef struct {
    uint32_t ClockType; uint32_t SYSCLKSource; uint32_t AHBCLKDivider;
    uint32_t APB1CLKDivider; uint32_t APB2CLKDivider;
} RCC_ClkInitTypeDef;
typedef enum { GPIO_PIN_RESET = 0, GPIO_PIN_SET = 1 } GPIO_PinState;
typedef enum { HAL_OK = 0, HAL_ERROR = 1 } HAL_StatusTypeDef;

extern GPIO_TypeDef test_gpioa;
extern GPIO_TypeDef test_gpioc;
#define GPIOA (&test_gpioa)
#define GPIOC (&test_gpioc)
#define GPIO_PIN_0 1U
#define GPIO_PIN_13 (1U << 13)
#define GPIO_MODE_OUTPUT_PP 1U
#define GPIO_NOPULL 0U
#define GPIO_SPEED_FREQ_LOW 2U
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
#define __HAL_RCC_GPIOA_CLK_ENABLE() test_enable_clock(GPIOA)
#define __HAL_RCC_GPIOC_CLK_ENABLE() test_enable_clock(GPIOC)
#define __NOP() ((void)0)
#define __disable_irq() test_disable_irq()

void test_enable_clock(GPIO_TypeDef *port);
void test_disable_irq(void);
void HAL_Init(void);
uint32_t HAL_GetTick(void);
void HAL_IncTick(void);
void HAL_Delay(uint32_t delay_ms);
void HAL_GPIO_WritePin(GPIO_TypeDef *port, uint16_t pin, GPIO_PinState state);
void HAL_GPIO_TogglePin(GPIO_TypeDef *port, uint16_t pin);
GPIO_PinState HAL_GPIO_ReadPin(GPIO_TypeDef *port, uint16_t pin);
void HAL_GPIO_Init(GPIO_TypeDef *port, GPIO_InitTypeDef *config);
HAL_StatusTypeDef HAL_RCC_OscConfig(RCC_OscInitTypeDef *config);
HAL_StatusTypeDef HAL_RCC_ClockConfig(RCC_ClkInitTypeDef *config, uint32_t latency);

#endif

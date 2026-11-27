#ifndef TEST_TIMER_PWM_STM32F1XX_HAL_H
#define TEST_TIMER_PWM_STM32F1XX_HAL_H

#include <stdint.h>

typedef struct {
    uint32_t ODR;
} GPIO_TypeDef;

typedef struct {
    uint32_t CCR1;
} TIM_TypeDef;

typedef struct {
    uint32_t Pin;
    uint32_t Mode;
    uint32_t Pull;
    uint32_t Speed;
} GPIO_InitTypeDef;

typedef struct {
    uint32_t Prescaler;
    uint32_t CounterMode;
    uint32_t Period;
    uint32_t ClockDivision;
    uint32_t AutoReloadPreload;
} TIM_Base_InitTypeDef;

typedef struct {
    TIM_TypeDef *Instance;
    TIM_Base_InitTypeDef Init;
    uint32_t State;
} TIM_HandleTypeDef;

typedef struct {
    uint32_t OCMode;
    uint32_t Pulse;
    uint32_t OCPolarity;
    uint32_t OCFastMode;
    uint32_t OCIdleState;
} TIM_OC_InitTypeDef;

typedef struct {
    uint32_t OscillatorType;
    uint32_t HSEState;
    uint32_t HSEPredivValue;
    uint32_t HSIState;
    struct {
        uint32_t PLLState;
        uint32_t PLLSource;
        uint32_t PLLMUL;
    } PLL;
} RCC_OscInitTypeDef;

typedef struct {
    uint32_t ClockType;
    uint32_t SYSCLKSource;
    uint32_t AHBCLKDivider;
    uint32_t APB1CLKDivider;
    uint32_t APB2CLKDivider;
} RCC_ClkInitTypeDef;

typedef enum { HAL_OK = 0, HAL_ERROR = 1, HAL_BUSY = 2 } HAL_StatusTypeDef;
typedef enum { GPIO_PIN_RESET = 0, GPIO_PIN_SET = 1 } GPIO_PinState;

extern GPIO_TypeDef test_gpioa;
extern TIM_TypeDef test_tim3;
#define GPIOA (&test_gpioa)
#define TIM3 (&test_tim3)

#define GPIO_PIN_6 (1U << 6)
#define GPIO_MODE_AF_PP 2U
#define GPIO_NOPULL 0U
#define GPIO_SPEED_FREQ_HIGH 3U

#define TIM_CHANNEL_1 1U
#define TIM_COUNTERMODE_UP 0U
#define TIM_CLOCKDIVISION_DIV1 0U
#define TIM_AUTORELOAD_PRELOAD_ENABLE 1U
#define TIM_OCMODE_PWM1 1U
#define TIM_OCPOLARITY_HIGH 0U
#define TIM_OCFAST_DISABLE 0U
#define TIM_OCIDLESTATE_RESET 0U

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

#define __HAL_RCC_TIM3_CLK_ENABLE() test_enable_clock(1U)
#define __HAL_RCC_GPIOA_CLK_ENABLE() test_enable_clock(2U)
#define __HAL_TIM_SET_COMPARE(htim, channel, compare) \
    test_set_compare((htim), (channel), (compare))
#define __disable_irq() test_disable_irq()

void test_enable_clock(uint32_t mask);
void test_set_compare(TIM_HandleTypeDef *htim, uint32_t channel, uint32_t compare);
void test_disable_irq(void);
void HAL_Init(void);
uint32_t HAL_GetTick(void);
void HAL_IncTick(void);
void HAL_Delay(uint32_t delay_ms);
void HAL_GPIO_Init(GPIO_TypeDef *port, GPIO_InitTypeDef *config);
HAL_StatusTypeDef HAL_RCC_OscConfig(RCC_OscInitTypeDef *config);
HAL_StatusTypeDef HAL_RCC_ClockConfig(RCC_ClkInitTypeDef *config, uint32_t latency);
HAL_StatusTypeDef HAL_TIM_PWM_Init(TIM_HandleTypeDef *htim);
HAL_StatusTypeDef HAL_TIM_PWM_ConfigChannel(TIM_HandleTypeDef *htim,
                                            TIM_OC_InitTypeDef *config,
                                            uint32_t channel);
HAL_StatusTypeDef HAL_TIM_PWM_Start(TIM_HandleTypeDef *htim, uint32_t channel);

#endif

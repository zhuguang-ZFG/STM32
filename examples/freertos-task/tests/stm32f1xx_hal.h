#ifndef TEST_STM32F1XX_HAL_H
#define TEST_STM32F1XX_HAL_H
#include <stdint.h>
typedef struct { uint32_t ODR; } GPIO_TypeDef;
typedef struct { uint32_t Pin, Mode, Pull, Speed; } GPIO_InitTypeDef;
typedef struct {
    uint32_t OscillatorType, HSEState, HSEPredivValue, HSIState;
    struct { uint32_t PLLState, PLLSource, PLLMUL; } PLL;
} RCC_OscInitTypeDef;
typedef struct {
    uint32_t ClockType, SYSCLKSource, AHBCLKDivider, APB1CLKDivider, APB2CLKDivider;
} RCC_ClkInitTypeDef;
typedef struct { uint32_t unused; } USART_TypeDef;
typedef struct {
    USART_TypeDef *Instance;
    struct {
        uint32_t BaudRate, WordLength, StopBits, Parity, Mode, HwFlowCtl, OverSampling;
    } Init;
} UART_HandleTypeDef;
typedef enum { HAL_OK, HAL_ERROR } HAL_StatusTypeDef;
typedef enum { GPIO_PIN_RESET, GPIO_PIN_SET } GPIO_PinState;
extern GPIO_TypeDef test_gpioa, test_gpioc;
extern USART_TypeDef test_usart1;
#define GPIOA (&test_gpioa)
#define GPIOC (&test_gpioc)
#define USART1 (&test_usart1)
#define GPIO_PIN_0 1U
#define GPIO_PIN_9 (1U << 9)
#define GPIO_PIN_10 (1U << 10)
#define GPIO_PIN_13 (1U << 13)
#define GPIO_MODE_OUTPUT_PP 1U
#define GPIO_MODE_IT_FALLING 2U
#define GPIO_MODE_AF_PP 3U
#define GPIO_MODE_INPUT 4U
#define GPIO_NOPULL 0U
#define GPIO_PULLUP 1U
#define GPIO_SPEED_FREQ_LOW 1U
#define GPIO_SPEED_FREQ_HIGH 3U
#define __NVIC_PRIO_BITS 4U
#define NVIC_PRIORITYGROUP_4 3U
#define EXTI0_IRQn 6U
#define UART_WORDLENGTH_8B 0U
#define UART_STOPBITS_1 0U
#define UART_PARITY_NONE 0U
#define UART_MODE_TX_RX 3U
#define UART_HWCONTROL_NONE 0U
#define UART_OVERSAMPLING_16 0U
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
#define __HAL_RCC_GPIOA_CLK_ENABLE() ((void)0)
#define __HAL_RCC_GPIOC_CLK_ENABLE() ((void)0)
#define __HAL_RCC_AFIO_CLK_ENABLE() ((void)0)
#define __HAL_RCC_USART1_CLK_ENABLE() ((void)0)
#define __HAL_GPIO_EXTI_CLEAR_IT(pin) test_clear_exti(pin)
#define __disable_irq() test_disable_irq()
void test_disable_irq(void);
void test_clear_exti(uint16_t pin);
void HAL_Init(void);
void HAL_GPIO_Init(GPIO_TypeDef *port, GPIO_InitTypeDef *config);
void HAL_GPIO_WritePin(GPIO_TypeDef *port, uint16_t pin, GPIO_PinState state);
void HAL_GPIO_TogglePin(GPIO_TypeDef *port, uint16_t pin);
void HAL_GPIO_EXTI_IRQHandler(uint16_t pin);
void HAL_GPIO_EXTI_Callback(uint16_t pin);
void HAL_NVIC_SetPriorityGrouping(uint32_t group);
void HAL_NVIC_SetPriority(uint32_t irq, uint32_t priority, uint32_t subpriority);
void HAL_NVIC_EnableIRQ(uint32_t irq);
void HAL_NVIC_DisableIRQ(uint32_t irq);
void HAL_NVIC_ClearPendingIRQ(uint32_t irq);
HAL_StatusTypeDef HAL_RCC_OscConfig(RCC_OscInitTypeDef *config);
HAL_StatusTypeDef HAL_RCC_ClockConfig(RCC_ClkInitTypeDef *config, uint32_t latency);
HAL_StatusTypeDef HAL_UART_Init(UART_HandleTypeDef *handle);
HAL_StatusTypeDef HAL_UART_Transmit(UART_HandleTypeDef *handle, uint8_t *data,
                                    uint16_t length, uint32_t timeout);
#endif

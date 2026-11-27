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
typedef enum { HAL_OK = 0, HAL_ERROR = 1, HAL_BUSY = 2, HAL_TIMEOUT = 3 } HAL_StatusTypeDef;

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


typedef struct { uint32_t unused; } USART_TypeDef;
typedef struct { uint32_t unused; } DMA_Channel_TypeDef;
typedef struct {
    DMA_Channel_TypeDef *Instance;
    struct {
        uint32_t Direction; uint32_t PeriphInc; uint32_t MemInc;
        uint32_t PeriphDataAlignment; uint32_t MemDataAlignment;
        uint32_t Mode; uint32_t Priority;
    } Init;
} DMA_HandleTypeDef;
typedef struct {
    USART_TypeDef *Instance;
    struct {
        uint32_t BaudRate; uint32_t WordLength; uint32_t StopBits; uint32_t Parity;
        uint32_t Mode; uint32_t HwFlowCtl; uint32_t OverSampling;
    } Init;
    DMA_HandleTypeDef *hdmarx;
    uint32_t ErrorCode;
    uint32_t RxState;
} UART_HandleTypeDef;
typedef enum { HAL_UART_RXEVENT_TC, HAL_UART_RXEVENT_HT, HAL_UART_RXEVENT_IDLE } HAL_UART_RxEventTypeTypeDef;
extern USART_TypeDef test_usart1;
extern DMA_Channel_TypeDef test_dma_channel5;
#define USART1 (&test_usart1)
#define DMA1_Channel5 (&test_dma_channel5)
#define GPIO_PIN_9 (1U << 9)
#define GPIO_PIN_10 (1U << 10)
#define GPIO_MODE_AF_PP 2U
#define GPIO_MODE_INPUT 3U
#define GPIO_PULLUP 1U
#define GPIO_SPEED_FREQ_HIGH 3U
#define UART_WORDLENGTH_8B 8U
#define UART_STOPBITS_1 1U
#define UART_PARITY_NONE 0U
#define UART_MODE_TX_RX 3U
#define UART_HWCONTROL_NONE 0U
#define UART_OVERSAMPLING_16 16U
#define DMA_PERIPH_TO_MEMORY 0U
#define DMA_PINC_DISABLE 0U
#define DMA_MINC_ENABLE 1U
#define DMA_PDATAALIGN_BYTE 0U
#define DMA_MDATAALIGN_BYTE 0U
#define DMA_NORMAL 0U
#define DMA_PRIORITY_HIGH 2U
#define USART1_IRQn 37U
#define DMA1_Channel5_IRQn 15U
#define HAL_UART_ERROR_ORE 8U
#define HAL_UART_ERROR_FE 4U
#define HAL_UART_STATE_READY 0U
#define HAL_UART_STATE_BUSY_RX 1U
#define __HAL_LINKDMA(handle, field, dma) ((handle)->field = &(dma))
#define __HAL_RCC_USART1_CLK_ENABLE() ((void)0)
#define __HAL_RCC_DMA1_CLK_ENABLE() ((void)0)
#define __HAL_UART_CLEAR_OREFLAG(handle) test_clear_rx_error(handle)
void test_clear_rx_error(UART_HandleTypeDef *handle);
HAL_StatusTypeDef HAL_UART_Init(UART_HandleTypeDef *handle);
HAL_StatusTypeDef HAL_DMA_Init(DMA_HandleTypeDef *handle);
HAL_StatusTypeDef HAL_UARTEx_ReceiveToIdle_DMA(UART_HandleTypeDef *handle, uint8_t *buffer, uint16_t length);
HAL_UART_RxEventTypeTypeDef HAL_UARTEx_GetRxEventType(UART_HandleTypeDef *handle);
HAL_StatusTypeDef HAL_UART_AbortReceive(UART_HandleTypeDef *handle);
HAL_StatusTypeDef HAL_UART_Transmit(UART_HandleTypeDef *handle, uint8_t *buffer, uint16_t length, uint32_t timeout);
void HAL_UART_IRQHandler(UART_HandleTypeDef *handle);
void HAL_DMA_IRQHandler(DMA_HandleTypeDef *handle);
void HAL_NVIC_SetPriority(uint32_t irq, uint32_t preemption, uint32_t subpriority);
void HAL_NVIC_EnableIRQ(uint32_t irq);
void NVIC_SystemReset(void);

#endif

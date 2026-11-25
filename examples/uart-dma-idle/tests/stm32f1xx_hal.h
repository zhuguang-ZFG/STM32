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
typedef struct {
    uint32_t BaudRate; uint32_t WordLength; uint32_t StopBits; uint32_t Parity;
    uint32_t Mode; uint32_t HwFlowCtl; uint32_t OverSampling;
} UART_InitTypeDef;
typedef struct { uint32_t SR; uint32_t DR; uint32_t BRR; uint32_t CR1; uint32_t CR2; uint32_t CR3; } USART_TypeDef;
typedef struct { uint32_t CCR; } DMA_Channel_TypeDef;
typedef struct {
    uint32_t Direction; uint32_t PeriphInc; uint32_t MemInc;
    uint32_t PeriphDataAlignment; uint32_t MemDataAlignment; uint32_t Mode; uint32_t Priority;
} DMA_InitTypeDef;
typedef struct DMA_HandleTypeDef DMA_HandleTypeDef;
typedef struct {
    USART_TypeDef *Instance;
    UART_InitTypeDef Init;
    DMA_HandleTypeDef *hdmarx;
    uint32_t RxState;
    uint32_t ReceptionType;
    uint32_t RxEventType;
} UART_HandleTypeDef;
struct DMA_HandleTypeDef {
    DMA_Channel_TypeDef *Instance;
    DMA_InitTypeDef Init;
    UART_HandleTypeDef *Parent;
};

typedef enum { HAL_OK = 0, HAL_ERROR = 1, HAL_BUSY = 2 } HAL_StatusTypeDef;
typedef enum { GPIO_PIN_RESET = 0, GPIO_PIN_SET = 1 } GPIO_PinState;
typedef enum { HAL_UART_RXEVENT_HT = 0, HAL_UART_RXEVENT_TC = 1, HAL_UART_RXEVENT_IDLE = 2 } HAL_UART_RxEventTypeTypeDef;

extern GPIO_TypeDef test_gpioa;
extern GPIO_TypeDef test_gpioc;
extern USART_TypeDef test_usart1;
extern DMA_Channel_TypeDef test_dma1_ch5;
#define GPIOA (&test_gpioa)
#define GPIOC (&test_gpioc)
#define USART1 (&test_usart1)
#define DMA1_Channel5 (&test_dma1_ch5)

#define GPIO_PIN_0 (1U << 0)
#define GPIO_PIN_9 (1U << 9)
#define GPIO_PIN_10 (1U << 10)
#define GPIO_PIN_13 (1U << 13)
#define GPIO_MODE_OUTPUT_PP 1U
#define GPIO_MODE_AF_PP 2U
#define GPIO_MODE_INPUT 3U
#define GPIO_NOPULL 0U
#define GPIO_PULLUP 1U
#define GPIO_SPEED_FREQ_LOW 2U
#define GPIO_SPEED_FREQ_HIGH 3U

#define UART_WORDLENGTH_8B 0U
#define UART_STOPBITS_1 0U
#define UART_PARITY_NONE 0U
#define UART_MODE_TX_RX 3U
#define UART_HWCONTROL_NONE 0U
#define UART_OVERSAMPLING_16 0U
#define UART_FLAG_ORE (1U << 3)
#define UART_FLAG_FE (1U << 1)
#define HAL_UART_STATE_READY 0U
#define HAL_UART_STATE_BUSY 1U
#define HAL_UART_RECEPTION_STANDARD 0U
#define HAL_UART_RECEPTION_TOIDLE 1U

#define DMA_PERIPH_TO_MEMORY 0U
#define DMA_PINC_DISABLE 0U
#define DMA_MINC_ENABLE 1U
#define DMA_PDATAALIGN_BYTE 0U
#define DMA_MDATAALIGN_BYTE 0U
#define DMA_NORMAL 0U
#define DMA_PRIORITY_HIGH 2U

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

#define USART1_IRQn 37
#define DMA1_Channel5_IRQn 15

#define __HAL_RCC_GPIOA_CLK_ENABLE() test_enable_clock(1U)
#define __HAL_RCC_GPIOC_CLK_ENABLE() test_enable_clock(2U)
#define __HAL_RCC_USART1_CLK_ENABLE() test_enable_clock(4U)
#define __HAL_RCC_DMA1_CLK_ENABLE() test_enable_clock(8U)
#define __HAL_LINKDMA(handle, field, dma_handle) ((handle)->field = &(dma_handle))
#define __HAL_UART_CLEAR_OREFLAG(huart) test_clear_uart_flag((huart), UART_FLAG_ORE)
#define __HAL_UART_CLEAR_FEFLAG(huart) test_clear_uart_flag((huart), UART_FLAG_FE)
#define __disable_irq() test_disable_irq()

void test_enable_clock(uint32_t mask);
void test_clear_uart_flag(UART_HandleTypeDef *huart, uint32_t flag);
void test_disable_irq(void);
void HAL_Init(void);
uint32_t HAL_GetTick(void);
void HAL_IncTick(void);
void HAL_Delay(uint32_t delay_ms);
void HAL_GPIO_Init(GPIO_TypeDef *port, GPIO_InitTypeDef *config);
void HAL_GPIO_WritePin(GPIO_TypeDef *port, uint16_t pin, GPIO_PinState state);
HAL_StatusTypeDef HAL_RCC_OscConfig(RCC_OscInitTypeDef *config);
HAL_StatusTypeDef HAL_RCC_ClockConfig(RCC_ClkInitTypeDef *config, uint32_t latency);
HAL_StatusTypeDef HAL_UART_Init(UART_HandleTypeDef *huart);
HAL_StatusTypeDef HAL_UART_Transmit(UART_HandleTypeDef *huart, uint8_t *data, uint16_t size, uint32_t timeout);
HAL_StatusTypeDef HAL_UARTEx_ReceiveToIdle_DMA(UART_HandleTypeDef *huart, uint8_t *data, uint16_t size);
HAL_UART_RxEventTypeTypeDef HAL_UARTEx_GetRxEventType(UART_HandleTypeDef *huart);
void HAL_UART_IRQHandler(UART_HandleTypeDef *huart);
HAL_StatusTypeDef HAL_DMA_Init(DMA_HandleTypeDef *hdma);
void HAL_DMA_IRQHandler(DMA_HandleTypeDef *hdma);
void HAL_NVIC_SetPriority(int irq, uint32_t preempt, uint32_t sub);
void HAL_NVIC_EnableIRQ(int irq);
void NVIC_SystemReset(void);

#endif

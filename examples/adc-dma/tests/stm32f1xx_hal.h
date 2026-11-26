#ifndef TEST_ADC_DMA_STM32F1XX_HAL_H
#define TEST_ADC_DMA_STM32F1XX_HAL_H

#include <stdint.h>

typedef struct {
    uint32_t ODR;
} GPIO_TypeDef;

typedef struct {
    uint32_t Pin;
    uint32_t Mode;
    uint32_t Pull;
    uint32_t Speed;
} GPIO_InitTypeDef;

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

typedef struct {
    uint32_t PeriphClockSelection;
    uint32_t AdcClockSelection;
} RCC_PeriphCLKInitTypeDef;

typedef struct {
    uint32_t Direction;
    uint32_t PeriphInc;
    uint32_t MemInc;
    uint32_t PeriphDataAlignment;
    uint32_t MemDataAlignment;
    uint32_t Mode;
    uint32_t Priority;
} DMA_InitTypeDef;

typedef struct {
    uint32_t Instance;
} DMA_Channel_TypeDef;

typedef struct __DMA_HandleTypeDef {
    DMA_Channel_TypeDef *Instance;
    DMA_InitTypeDef Init;
    void *Parent;
} DMA_HandleTypeDef;

typedef struct {
    uint32_t ScanConvMode;
    uint32_t ContinuousConvMode;
    uint32_t DiscontinuousConvMode;
    uint32_t ExternalTrigConv;
    uint32_t DataAlign;
    uint32_t NbrOfConversion;
} ADC_InitTypeDef;

typedef struct {
    uint32_t Channel;
    uint32_t Rank;
    uint32_t SamplingTime;
} ADC_ChannelConfTypeDef;

typedef struct __ADC_HandleTypeDef {
    uint32_t Instance;
    ADC_InitTypeDef Init;
    DMA_HandleTypeDef *DMA_Handle;
} ADC_HandleTypeDef;

typedef enum { HAL_OK = 0, HAL_ERROR = 1, HAL_BUSY = 2 } HAL_StatusTypeDef;
typedef enum { GPIO_PIN_RESET = 0, GPIO_PIN_SET = 1 } GPIO_PinState;

extern GPIO_TypeDef test_gpioa;
extern GPIO_TypeDef test_gpioc;
#define GPIOA (&test_gpioa)
#define GPIOC (&test_gpioc)

extern DMA_Channel_TypeDef test_dma1_channel1;
#define DMA1_Channel1 (&test_dma1_channel1)

#define ADC1 ((uint32_t)0x40012400U)

#define GPIO_PIN_0 (1U << 0)
#define GPIO_PIN_1 (1U << 1)
#define GPIO_PIN_4 (1U << 4)
#define GPIO_PIN_13 (1U << 13)
#define GPIO_MODE_OUTPUT_PP 0x00000001U
#define GPIO_MODE_ANALOG 0x00000003U
#define GPIO_NOPULL 0x00000000U
#define GPIO_SPEED_FREQ_LOW 0x00000002U

#define ENABLE 1U
#define DISABLE 0U

#define ADC_SCAN_ENABLE 1U
#define ADC_SOFTWARE_START 0x000E0000U
#define ADC_DATAALIGN_RIGHT 0x00000000U
#define ADC_SAMPLETIME_55CYCLES_5 0x00000005U
#define ADC_CHANNEL_0 0x00000000U
#define ADC_CHANNEL_1 0x00000001U
#define ADC_CHANNEL_4 0x00000004U

#define DMA_PERIPH_TO_MEMORY 0x00000000U
#define DMA_PINC_DISABLE 0x00000000U
#define DMA_MINC_ENABLE 0x00000040U
#define DMA_PDATAALIGN_HALFWORD 0x00000100U
#define DMA_MDATAALIGN_HALFWORD 0x00000400U
#define DMA_CIRCULAR 0x00000020U
#define DMA_PRIORITY_HIGH 0x00002000U

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
#define RCC_PERIPHCLK_ADC 0x00000001U
#define RCC_ADCPCLK2_DIV6 0x00008000U
#define FLASH_LATENCY_2 2U

#define __HAL_RCC_GPIOA_CLK_ENABLE() test_enable_clock(1U)
#define __HAL_RCC_GPIOC_CLK_ENABLE() test_enable_clock(2U)
#define __HAL_RCC_ADC1_CLK_ENABLE() test_enable_clock(4U)
#define __HAL_RCC_DMA1_CLK_ENABLE() test_enable_clock(8U)
#define __HAL_LINKDMA(__HANDLE__, __PPP_DMA_FIELD__, __DMA_HANDLE__) \
    do {                                                             \
        (__HANDLE__)->__PPP_DMA_FIELD__ = &(__DMA_HANDLE__);         \
        (__DMA_HANDLE__).Parent = (__HANDLE__);                      \
    } while (0)
#define __disable_irq() test_disable_irq()
#define __enable_irq() test_enable_irq()

void test_enable_clock(uint32_t mask);
void test_disable_irq(void);
void test_enable_irq(void);
void HAL_Init(void);
uint32_t HAL_GetTick(void);
void HAL_GPIO_Init(GPIO_TypeDef *port, GPIO_InitTypeDef *config);
void HAL_GPIO_WritePin(GPIO_TypeDef *port, uint16_t pin, GPIO_PinState state);
void HAL_GPIO_TogglePin(GPIO_TypeDef *port, uint16_t pin);
HAL_StatusTypeDef HAL_RCC_OscConfig(RCC_OscInitTypeDef *config);
HAL_StatusTypeDef HAL_RCC_ClockConfig(RCC_ClkInitTypeDef *config, uint32_t latency);
HAL_StatusTypeDef HAL_RCCEx_PeriphCLKConfig(RCC_PeriphCLKInitTypeDef *config);
HAL_StatusTypeDef HAL_DMA_Init(DMA_HandleTypeDef *handle);
HAL_StatusTypeDef HAL_ADC_Init(ADC_HandleTypeDef *handle);
HAL_StatusTypeDef HAL_ADC_ConfigChannel(ADC_HandleTypeDef *handle, ADC_ChannelConfTypeDef *config);
HAL_StatusTypeDef HAL_ADCEx_Calibration_Start(ADC_HandleTypeDef *handle);
HAL_StatusTypeDef HAL_ADC_Start_DMA(ADC_HandleTypeDef *handle, uint32_t *buffer, uint32_t length);

#endif

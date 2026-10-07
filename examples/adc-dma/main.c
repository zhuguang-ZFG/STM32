/**
 * @file    main.c
 * @brief   adc-dma —— ADC 多通道 + DMA 循环采集 + 滑动平均滤波 + 电压换算
 *          （STM32F103C8T6 / BluePill）
 *
 * 功能：
 *   1) ADC1 扫描 3 个通道（PA0=CH0、PA1=CH1、PA4=CH4），连续转换；
 *   2) DMA1_CH1 循环搬运到内存数组，CPU 不参与采样；
 *   3) 主循环按通道求平均，再对「块平均」做滑动平均（低通滤波）；
 *   4) 按 V = ADC_Code × Vref / 4096 换算电压（Vref=VDDA=3.3V）；
 *   5) 用板载 LED 心跳指示采集在运行。
 *
 * 目标芯片：STM32F103C8T6，系统时钟 72MHz，ADCCLK=12MHz（PCLK2/6）。
 */

#include "stm32f1xx_hal.h"

/* ------------------------------------------------------------------ 宏定义 */

#define ADC_INSTANCE        ADC1
#define ADC_NUM_CH          3U              /* 采样通道数 */
#define ADC_SAMPLES         16U             /* 每通道采样点数（块平均） */
#define ADC_BUF_SIZE        (ADC_NUM_CH * ADC_SAMPLES)

#define ADC_CH0_PIN         GPIO_PIN_0      /* PA0 = ADC1_IN0 */
#define ADC_CH1_PIN         GPIO_PIN_1      /* PA1 = ADC1_IN1 */
#define ADC_CH4_PIN         GPIO_PIN_4      /* PA4 = ADC1_IN4 */
#define ADC_GPIO_PORT       GPIOA

#define ADC_CH0_RANK        1U              /* 转换序列位置 */
#define ADC_CH1_RANK        2U
#define ADC_CH4_RANK        3U
#define ADC_CH0_INDEX       0U              /* 在缓冲区中的通道下标 */
#define ADC_CH1_INDEX       1U
#define ADC_CH4_INDEX       2U

#define MA_WINDOW           8U              /* 滑动平均窗口长度 */

#define LED_PORT            GPIOC
#define LED_PIN             GPIO_PIN_13     /* 板载 LED，低电平点亮 */

#define VREF_VOLT           3.3f            /* 参考电压 = VDDA */
#define ADC_FULL_SCALE      4096.0f         /* 12 位：2^12 */

#define SAMPLE_PERIOD_MS    100U            /* 每次处理间隔 */

/* ---------------------------------------------------------------- 全局句柄 */

ADC_HandleTypeDef hadc1;
DMA_HandleTypeDef hdma_adc1;

/* DMA 目标缓冲区：volatile，因为由 DMA 硬件在后台写入 */
static volatile uint16_t g_adc_buf[ADC_BUF_SIZE];

/* 每通道的滑动平均状态 */
static float g_ma_buf[ADC_NUM_CH][MA_WINDOW];
static uint8_t g_ma_idx = 0U;
static uint8_t g_ma_filled = 0U;

/* ----------------------------------------------------------------- 私有函数 */

static void SystemClock_Config(void);
static void adc_dma_init(void);
static void error_handler(void);

static uint32_t adc_channel_avg(uint8_t ch_index);
static float    adc_to_volt(uint32_t code);
static float    moving_average(uint8_t ch_index, float new_val);

/* ---------------------------------------------------------------- 主函数 */

int main(void)
{
    HAL_Init();
    SystemClock_Config();
    adc_dma_init();

    /* 启动 ADC + DMA 循环采集（后台自动搬运，函数立即返回） */
    if (HAL_ADC_Start_DMA(&hadc1, (uint32_t *)g_adc_buf, ADC_BUF_SIZE) != HAL_OK)
    {
        error_handler();
    }

    uint32_t last = 0U;

    while (1)
    {
        if ((HAL_GetTick() - last) >= SAMPLE_PERIOD_MS)
        {
            last = HAL_GetTick();

            /* 逐通道：块平均 → 滑动平均 → 电压 */
            for (uint8_t ch = 0; ch < ADC_NUM_CH; ch++)
            {
                uint32_t avg_code = adc_channel_avg(ch);
                float    volt_raw = adc_to_volt(avg_code);
                float    volt_flt = moving_average(ch, volt_raw);

                /* 演示：把滤波后的电压用在业务里（这里仅保留，实际可打印/上报） */
                (void)volt_flt;
            }

            /* LED 心跳：每次处理翻转一次 */
            HAL_GPIO_TogglePin(LED_PORT, LED_PIN);
        }
    }
}

/* ------------------------------------------------------- 数据处理实现 */

/**
 * @brief  求某通道在一整块缓冲区里的平均值
 * @note   DMA 按转换顺序（CH0,CH1,CH4,CH0,...）循环填充，
 *         故通道 ch 的数据位于下标 ch, ch+3, ch+6, ...
 */
static uint32_t adc_channel_avg(uint8_t ch_index)
{
    uint32_t sum = 0U;
    for (uint16_t s = 0; s < ADC_SAMPLES; s++)
    {
        sum += g_adc_buf[s * ADC_NUM_CH + ch_index];
    }
    return sum / ADC_SAMPLES;
}

/**
 * @brief  12 位 ADC 码值 → 电压
 */
static float adc_to_volt(uint32_t code)
{
    return ((float)code * VREF_VOLT) / ADC_FULL_SCALE;
}

/**
 * @brief  滑动平均滤波：维护每通道最近 MA_WINDOW 个值的平均
 * @param  ch_index 通道下标
 * @param  new_val  新采样值
 * @return 滤波后的值
 */
static float moving_average(uint8_t ch_index, float new_val)
{
    g_ma_buf[ch_index][g_ma_idx] = new_val;

    /* 主循环单线程访问，这里无需临界区；但若在中断里调用需保护 */
    uint8_t count = g_ma_filled ? MA_WINDOW : (uint8_t)(g_ma_idx + 1U);
    float   sum = 0.0f;
    for (uint8_t i = 0; i < count; i++)
    {
        sum += g_ma_buf[ch_index][i];
    }

    if (ch_index == (ADC_NUM_CH - 1U))      /* 最后一个通道处理完再推进索引 */
    {
        g_ma_idx = (uint8_t)((g_ma_idx + 1U) % MA_WINDOW);
        if (g_ma_idx == 0U)
        {
            g_ma_filled = 1U;
        }
    }
    return sum / (float)count;
}

/* ------------------------------------------------------- 外设初始化实现 */

/**
 * @brief  初始化 ADC1（扫描 + 连续 + DMA）与 DMA1_CH1
 */
static void adc_dma_init(void)
{
    GPIO_InitTypeDef io = {0};

    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_GPIOC_CLK_ENABLE();
    __HAL_RCC_ADC1_CLK_ENABLE();
    __HAL_RCC_DMA1_CLK_ENABLE();

    /* LED 输出 */
    io.Pin   = LED_PIN;
    io.Mode  = GPIO_MODE_OUTPUT_PP;
    io.Pull  = GPIO_NOPULL;
    io.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(LED_PORT, &io);
    HAL_GPIO_WritePin(LED_PORT, LED_PIN, GPIO_PIN_SET);

    /* 模拟输入引脚：ADC 通道必须配成 GPIO_MODE_ANALOG */
    io.Pin  = ADC_CH0_PIN | ADC_CH1_PIN | ADC_CH4_PIN;
    io.Mode = GPIO_MODE_ANALOG;
    io.Pull = GPIO_NOPULL;
    HAL_GPIO_Init(ADC_GPIO_PORT, &io);

    /* DMA1 通道 1（F1 固定：ADC1 → DMA1_CH1），循环模式 */
    hdma_adc1.Instance                 = DMA1_Channel1;
    hdma_adc1.Init.Direction           = DMA_PERIPH_TO_MEMORY;
    hdma_adc1.Init.PeriphInc           = DMA_PINC_DISABLE;
    hdma_adc1.Init.MemInc              = DMA_MINC_ENABLE;
    hdma_adc1.Init.PeriphDataAlignment = DMA_PDATAALIGN_HALFWORD;
    hdma_adc1.Init.MemDataAlignment    = DMA_MDATAALIGN_HALFWORD;
    hdma_adc1.Init.Mode                = DMA_CIRCULAR;      /* 循环，自动回卷 */
    hdma_adc1.Init.Priority            = DMA_PRIORITY_HIGH;
    if (HAL_DMA_Init(&hdma_adc1) != HAL_OK)
    {
        error_handler();
    }
    __HAL_LINKDMA(&hadc1, DMA_Handle, hdma_adc1);

    /* ADC1 基础配置 */
    hadc1.Instance                   = ADC_INSTANCE;
    hadc1.Init.ScanConvMode          = ADC_SCAN_ENABLE;     /* 多通道扫描 */
    hadc1.Init.ContinuousConvMode    = ENABLE;              /* 连续转换 */
    hadc1.Init.DiscontinuousConvMode = DISABLE;
    hadc1.Init.ExternalTrigConv      = ADC_SOFTWARE_START;  /* 软件启动 */
    hadc1.Init.DataAlign             = ADC_DATAALIGN_RIGHT; /* 右对齐 */
    hadc1.Init.NbrOfConversion       = ADC_NUM_CH;          /* 3 个转换 */
    if (HAL_ADC_Init(&hadc1) != HAL_OK)
    {
        error_handler();
    }

    /* 规则组通道配置：采样时间设长一些以适配高阻信号源 */
    ADC_ChannelConfTypeDef cfg = {0};
    cfg.SamplingTime = ADC_SAMPLETIME_55CYCLES_5;          /* ≈4.6us @12MHz */

    cfg.Channel = ADC_CHANNEL_0; cfg.Rank = ADC_CH0_RANK;
    if (HAL_ADC_ConfigChannel(&hadc1, &cfg) != HAL_OK) { error_handler(); }

    cfg.Channel = ADC_CHANNEL_1; cfg.Rank = ADC_CH1_RANK;
    if (HAL_ADC_ConfigChannel(&hadc1, &cfg) != HAL_OK) { error_handler(); }

    cfg.Channel = ADC_CHANNEL_4; cfg.Rank = ADC_CH4_RANK;
    if (HAL_ADC_ConfigChannel(&hadc1, &cfg) != HAL_OK) { error_handler(); }

    /* ADC 校准（提高精度，上电后必须做一次） */
    if (HAL_ADCEx_Calibration_Start(&hadc1) != HAL_OK)
    {
        error_handler();
    }
}

/**
 * @brief  系统时钟配置：HSE 8MHz → PLL ×9 → 72MHz
 * @note   ADCCLK = PCLK2 / ADC 预分频；F1 要求 ADCCLK ≤ 14MHz。
 *         HAL 默认 PCLK2=72MHz、/6 = 12MHz。
 */
static void SystemClock_Config(void)
{
    RCC_OscInitTypeDef osc = {0};
    RCC_ClkInitTypeDef clk = {0};
    RCC_PeriphCLKInitTypeDef pclk = {0};

    osc.OscillatorType = RCC_OSCILLATORTYPE_HSE;
    osc.HSEState       = RCC_HSE_ON;
    osc.HSEPredivValue = RCC_HSE_PREDIV_DIV1;
    osc.HSIState       = RCC_HSI_ON;
    osc.PLL.PLLState   = RCC_PLL_ON;
    osc.PLL.PLLSource  = RCC_PLLSOURCE_HSE;
    osc.PLL.PLLMUL     = RCC_PLL_MUL9;
    if (HAL_RCC_OscConfig(&osc) != HAL_OK)
    {
        error_handler();
    }

    clk.ClockType      = RCC_CLOCKTYPE_HCLK | RCC_CLOCKTYPE_SYSCLK |
                         RCC_CLOCKTYPE_PCLK1 | RCC_CLOCKTYPE_PCLK2;
    clk.SYSCLKSource   = RCC_SYSCLKSOURCE_PLLCLK;
    clk.AHBCLKDivider  = RCC_SYSCLK_DIV1;
    clk.APB1CLKDivider = RCC_HCLK_DIV2;
    clk.APB2CLKDivider = RCC_HCLK_DIV1;         /* PCLK2 = 72MHz */
    if (HAL_RCC_ClockConfig(&clk, FLASH_LATENCY_2) != HAL_OK)
    {
        error_handler();
    }

    /* ADC 时钟 = PCLK2 / 6 = 12MHz（≤14MHz，保证 1MSPS 内的精度） */
    pclk.PeriphClockSelection = RCC_PERIPHCLK_ADC;
    pclk.AdcClockSelection    = RCC_ADCPCLK2_DIV6;
    if (HAL_RCCEx_PeriphCLKConfig(&pclk) != HAL_OK)
    {
        error_handler();
    }
}

static void error_handler(void)
{
    __disable_irq();
    while (1)
    {
    }
}


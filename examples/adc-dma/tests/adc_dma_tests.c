/* Host regression: run the production ADC1/DMA sampling code against explicit
 * HAL doubles. Not a full firmware build and not board evidence. */
#undef NDEBUG
#include <assert.h>
#include <setjmp.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "stm32f1xx_hal.h"

#define main firmware_main
#include "../main.c"
#undef main

GPIO_TypeDef test_gpioa;
GPIO_TypeDef test_gpioc;
DMA_Channel_TypeDef test_dma1_channel1;

enum { FAIL_NONE = 0, FAIL_DMA, FAIL_ADC, FAIL_CHANNEL, FAIL_CALIB, FAIL_START };

static jmp_buf test_exit;
static uint32_t clock_flags;
static uint32_t init_calls;
static uint32_t gpio_init_count;
static GPIO_TypeDef *gpio_init_ports[4];
static GPIO_InitTypeDef gpio_init_configs[4];
static uint32_t write_count;
static GPIO_TypeDef *write_port;
static uint16_t write_pin;
static GPIO_PinState write_state;
static uint32_t toggle_count;
static uint32_t dma_init_calls;
static DMA_HandleTypeDef captured_dma;
static uint32_t adc_init_calls;
static ADC_HandleTypeDef captured_adc;
static uint32_t channel_cfg_calls;
static ADC_ChannelConfTypeDef captured_channels[4];
static uint32_t calibration_calls;
static uint32_t channel_cfg_at_calibration;
static uint32_t start_dma_calls;
static uint32_t *start_dma_buffer;
static uint32_t start_dma_length;
static uint32_t periph_clk_calls;
static RCC_PeriphCLKInitTypeDef captured_pclk;
static RCC_OscInitTypeDef captured_osc;
static RCC_ClkInitTypeDef captured_clk;
static uint32_t captured_latency;
static uint32_t irq_disable_calls;
static uint32_t irq_enable_calls;
static int fail_call;
static uint32_t tick_calls;
static uint32_t tick_script[8];
static uint32_t tick_script_len;
static const uint32_t tick_hold = 4U;   /* HAL_GetTick calls per scripted tick */

void test_enable_clock(uint32_t mask) { clock_flags |= mask; }

void test_disable_irq(void) { irq_disable_calls++; longjmp(test_exit, 2); }

void test_enable_irq(void) { irq_enable_calls++; }

void HAL_Init(void) { init_calls++; }

/* The loop polls the tick; hold each scripted value long enough for the loop to
 * reach the next one, then stop the firmware by unwinding out of the double. */
uint32_t HAL_GetTick(void)
{
    uint32_t index = tick_calls / tick_hold;
    if (index >= tick_script_len)
    {
        longjmp(test_exit, 1);
    }
    tick_calls++;
    return tick_script[index];
}

void HAL_GPIO_Init(GPIO_TypeDef *port, GPIO_InitTypeDef *config)
{
    assert(gpio_init_count < 4U);
    gpio_init_ports[gpio_init_count] = port;
    gpio_init_configs[gpio_init_count] = *config;
    gpio_init_count++;
}

void HAL_GPIO_WritePin(GPIO_TypeDef *port, uint16_t pin, GPIO_PinState state)
{
    write_count++;
    write_port = port;
    write_pin = pin;
    write_state = state;
}

void HAL_GPIO_TogglePin(GPIO_TypeDef *port, uint16_t pin)
{
    (void)port;
    (void)pin;
    toggle_count++;
}

HAL_StatusTypeDef HAL_RCC_OscConfig(RCC_OscInitTypeDef *config)
{
    captured_osc = *config;
    return HAL_OK;
}

HAL_StatusTypeDef HAL_RCC_ClockConfig(RCC_ClkInitTypeDef *config, uint32_t latency)
{
    captured_clk = *config;
    captured_latency = latency;
    return HAL_OK;
}

HAL_StatusTypeDef HAL_RCCEx_PeriphCLKConfig(RCC_PeriphCLKInitTypeDef *config)
{
    periph_clk_calls++;
    captured_pclk = *config;
    return HAL_OK;
}

HAL_StatusTypeDef HAL_DMA_Init(DMA_HandleTypeDef *handle)
{
    dma_init_calls++;
    captured_dma = *handle;
    return (fail_call == FAIL_DMA) ? HAL_ERROR : HAL_OK;
}

HAL_StatusTypeDef HAL_ADC_Init(ADC_HandleTypeDef *handle)
{
    adc_init_calls++;
    captured_adc = *handle;
    return (fail_call == FAIL_ADC) ? HAL_ERROR : HAL_OK;
}

HAL_StatusTypeDef HAL_ADC_ConfigChannel(ADC_HandleTypeDef *handle, ADC_ChannelConfTypeDef *config)
{
    (void)handle;
    assert(channel_cfg_calls < 4U);
    captured_channels[channel_cfg_calls] = *config;
    channel_cfg_calls++;
    return (fail_call == FAIL_CHANNEL) ? HAL_ERROR : HAL_OK;
}

HAL_StatusTypeDef HAL_ADCEx_Calibration_Start(ADC_HandleTypeDef *handle)
{
    (void)handle;
    calibration_calls++;
    channel_cfg_at_calibration = channel_cfg_calls;
    return (fail_call == FAIL_CALIB) ? HAL_ERROR : HAL_OK;
}

HAL_StatusTypeDef HAL_ADC_Start_DMA(ADC_HandleTypeDef *handle, uint32_t *buffer, uint32_t length)
{
    (void)handle;
    start_dma_calls++;
    start_dma_buffer = buffer;
    start_dma_length = length;
    return (fail_call == FAIL_START) ? HAL_ERROR : HAL_OK;
}

static void reset_state(void)
{
    memset(&test_gpioa, 0, sizeof(test_gpioa));
    memset(&test_gpioc, 0, sizeof(test_gpioc));
    memset(&hadc1, 0, sizeof(hadc1));
    memset(&hdma_adc1, 0, sizeof(hdma_adc1));
    memset((void *)g_adc_buf, 0, sizeof(g_adc_buf));
    memset(g_ma_buf, 0, sizeof(g_ma_buf));
    g_ma_idx = 0U;
    g_ma_filled = 0U;

    clock_flags = 0U;
    init_calls = 0U;
    gpio_init_count = 0U;
    memset(gpio_init_ports, 0, sizeof(gpio_init_ports));
    memset(gpio_init_configs, 0, sizeof(gpio_init_configs));
    write_count = 0U;
    write_port = NULL;
    write_pin = 0U;
    write_state = GPIO_PIN_RESET;
    toggle_count = 0U;
    dma_init_calls = 0U;
    memset(&captured_dma, 0, sizeof(captured_dma));
    adc_init_calls = 0U;
    memset(&captured_adc, 0, sizeof(captured_adc));
    channel_cfg_calls = 0U;
    memset(captured_channels, 0, sizeof(captured_channels));
    calibration_calls = 0U;
    channel_cfg_at_calibration = 0U;
    start_dma_calls = 0U;
    start_dma_buffer = NULL;
    start_dma_length = 0U;
    periph_clk_calls = 0U;
    memset(&captured_pclk, 0, sizeof(captured_pclk));
    memset(&captured_osc, 0, sizeof(captured_osc));
    memset(&captured_clk, 0, sizeof(captured_clk));
    captured_latency = 0U;
    irq_disable_calls = 0U;
    irq_enable_calls = 0U;
    fail_call = FAIL_NONE;
    tick_calls = 0U;
    memset(tick_script, 0, sizeof(tick_script));
    tick_script_len = 0U;
}

static void set_tick_script(const uint32_t *values, uint32_t count)
{
    assert(count <= sizeof(tick_script) / sizeof(tick_script[0]));
    memcpy(tick_script, values, count * sizeof(values[0]));
    tick_script_len = count;
}

/* Run the firmware until the tick double or error_handler unwinds it.
 * Returns the jump code: 1 = scripted tick exhausted, 2 = error_handler. */
static int run_firmware(void)
{
    int jump = setjmp(test_exit);
    if (jump == 0)
    {
        firmware_main();
    }
    return jump;
}

/* One processing pass over all three channels, as the main loop does.
 * Returns the filtered value of rank 0 so the window can be asserted. */
static float process_one_pass(float v0, float v1, float v2)
{
    float filtered = moving_average(ADC_CH0_INDEX, v0);
    (void)moving_average(ADC_CH1_INDEX, v1);
    (void)moving_average(ADC_CH4_INDEX, v2);
    return filtered;
}

static int near(float actual, float expected)
{
    float diff = actual - expected;
    return (diff > -1e-5f) && (diff < 1e-5f);
}

static void fill_buffer(uint16_t v0, uint16_t v1, uint16_t v4)
{
    for (uint16_t s = 0U; s < ADC_SAMPLES; s++)
    {
        g_adc_buf[s * ADC_NUM_CH + ADC_CH0_INDEX] = v0;
        g_adc_buf[s * ADC_NUM_CH + ADC_CH1_INDEX] = v1;
        g_adc_buf[s * ADC_NUM_CH + ADC_CH4_INDEX] = v4;
    }
}

/* Boot must leave ADC1 scanning three ranks, DMA1_CH1 in circular halfword
 * mode, the handles cross-linked, and sampling started on the real buffer. */
static void test_boot_configures_sampling_chain(void)
{
    static const uint32_t script[] = { 0U, 100U };
    reset_state();
    set_tick_script(script, 2U);

    assert(run_firmware() == 1);

    assert(init_calls == 1U);
    assert(clock_flags == (1U | 2U | 4U | 8U));

    assert(captured_osc.OscillatorType == RCC_OSCILLATORTYPE_HSE);
    assert(captured_osc.HSEState == RCC_HSE_ON);
    assert(captured_osc.PLL.PLLState == RCC_PLL_ON);
    assert(captured_osc.PLL.PLLSource == RCC_PLLSOURCE_HSE);
    assert(captured_osc.PLL.PLLMUL == RCC_PLL_MUL9);
    assert(captured_clk.SYSCLKSource == RCC_SYSCLKSOURCE_PLLCLK);
    assert(captured_clk.APB1CLKDivider == RCC_HCLK_DIV2);
    assert(captured_clk.APB2CLKDivider == RCC_HCLK_DIV1);
    assert(captured_latency == FLASH_LATENCY_2);

    assert(periph_clk_calls == 1U);
    assert(captured_pclk.PeriphClockSelection == RCC_PERIPHCLK_ADC);
    assert(captured_pclk.AdcClockSelection == RCC_ADCPCLK2_DIV6);   /* 12 MHz ≤ 14 MHz */

    assert(gpio_init_count == 2U);
    assert(gpio_init_ports[0] == GPIOC);
    assert(gpio_init_configs[0].Pin == LED_PIN);
    assert(gpio_init_configs[0].Mode == GPIO_MODE_OUTPUT_PP);
    assert(write_count == 1U && write_port == GPIOC && write_pin == LED_PIN);
    assert(write_state == GPIO_PIN_SET);                            /* LED off after boot */
    assert(gpio_init_ports[1] == GPIOA);
    assert(gpio_init_configs[1].Pin == (GPIO_PIN_0 | GPIO_PIN_1 | GPIO_PIN_4));
    assert(gpio_init_configs[1].Mode == GPIO_MODE_ANALOG);

    assert(dma_init_calls == 1U);
    assert(captured_dma.Instance == DMA1_Channel1);
    assert(captured_dma.Init.Direction == DMA_PERIPH_TO_MEMORY);
    assert(captured_dma.Init.PeriphInc == DMA_PINC_DISABLE);
    assert(captured_dma.Init.MemInc == DMA_MINC_ENABLE);
    assert(captured_dma.Init.PeriphDataAlignment == DMA_PDATAALIGN_HALFWORD);
    assert(captured_dma.Init.MemDataAlignment == DMA_MDATAALIGN_HALFWORD);
    assert(captured_dma.Init.Mode == DMA_CIRCULAR);
    assert(captured_dma.Init.Priority == DMA_PRIORITY_HIGH);

    assert(adc_init_calls == 1U);
    assert(captured_adc.Instance == ADC1);
    assert(captured_adc.Init.ScanConvMode == ADC_SCAN_ENABLE);
    assert(captured_adc.Init.ContinuousConvMode == ENABLE);
    assert(captured_adc.Init.DiscontinuousConvMode == DISABLE);
    assert(captured_adc.Init.ExternalTrigConv == ADC_SOFTWARE_START);
    assert(captured_adc.Init.DataAlign == ADC_DATAALIGN_RIGHT);
    assert(captured_adc.Init.NbrOfConversion == ADC_NUM_CH);

    assert(hadc1.DMA_Handle == &hdma_adc1);                         /* __HAL_LINKDMA */
    assert(hdma_adc1.Parent == &hadc1);

    assert(channel_cfg_calls == 3U);
    assert(captured_channels[0].Channel == ADC_CHANNEL_0);
    assert(captured_channels[0].Rank == 1U);
    assert(captured_channels[1].Channel == ADC_CHANNEL_1);
    assert(captured_channels[1].Rank == 2U);
    assert(captured_channels[2].Channel == ADC_CHANNEL_4);
    assert(captured_channels[2].Rank == 3U);
    for (uint32_t i = 0U; i < 3U; i++)
    {
        assert(captured_channels[i].SamplingTime == ADC_SAMPLETIME_55CYCLES_5);
    }

    assert(calibration_calls == 1U);
    assert(channel_cfg_at_calibration == 3U);                       /* calibrated after the ranks */

    assert(start_dma_calls == 1U);
    assert(start_dma_buffer == (uint32_t *)g_adc_buf);
    assert(start_dma_length == ADC_BUF_SIZE);                       /* 3 ranks × 16 samples */
    assert(irq_disable_calls == 0U);
}

/* DMA interleaves ranks: sample s of rank r sits at s*3 + r. */
static void test_channel_average_deinterleaves_ranks(void)
{
    reset_state();
    fill_buffer(100U, 200U, 300U);
    assert(adc_channel_avg(ADC_CH0_INDEX) == 100U);
    assert(adc_channel_avg(ADC_CH1_INDEX) == 200U);
    assert(adc_channel_avg(ADC_CH4_INDEX) == 300U);

    for (uint16_t s = 0U; s < ADC_SAMPLES; s++)
    {
        for (uint16_t r = 0U; r < ADC_NUM_CH; r++)
        {
            g_adc_buf[s * ADC_NUM_CH + r] = (uint16_t)(s * 10U + r);
        }
    }
    /* rank 0: 0,10,…,150 → 1200/16 = 75; rank 1 and 2 shift by +1 and +2 */
    assert(adc_channel_avg(ADC_CH0_INDEX) == 75U);
    assert(adc_channel_avg(ADC_CH1_INDEX) == 76U);
    assert(adc_channel_avg(ADC_CH4_INDEX) == 77U);
}

static void test_voltage_scaling(void)
{
    assert(adc_to_volt(0U) == 0.0f);
    float half = adc_to_volt(2048U);
    assert(half > 1.6499f && half < 1.6501f);
    float full = adc_to_volt(4095U);
    assert(full > 3.2991f && full < 3.2993f);
    assert(full < VREF_VOLT);                                       /* 4095 不是满量程 */
}

/* The ring fills one slot per pass, then averages the last MA_WINDOW values. */
static void test_moving_average_window(void)
{
    reset_state();

    assert(near(process_one_pass(1.0f, 0.0f, 0.0f), 1.0f));
    assert(g_ma_idx == 1U && g_ma_filled == 0U);
    assert(near(process_one_pass(2.0f, 0.0f, 0.0f), 1.5f));          /* (1+2)/2 */

    for (uint32_t k = 3U; k <= 8U; k++)
    {
        (void)process_one_pass((float)k, 0.0f, 0.0f);
    }
    /* Window is full: mean(1…8) = 4.5, ring wraps back to slot 0. */
    assert(g_ma_filled == 1U && g_ma_idx == 0U);
    assert(near(process_one_pass(9.0f, 0.0f, 0.0f), 5.5f));          /* 9,2…8 */
    assert(near(process_one_pass(10.0f, 0.0f, 0.0f), 6.5f));         /* 9,10,3…8 */
    assert(g_ma_buf[ADC_CH1_INDEX][0] == 0.0f);                      /* channels independent */
    assert(g_ma_buf[ADC_CH4_INDEX][0] == 0.0f);
}

static void test_led_heartbeat_period(void)
{
    static const uint32_t before[] = { 0U, 99U };
    static const uint32_t at[]     = { 0U, 100U };
    static const uint32_t early[]  = { 0U, 100U, 199U };
    static const uint32_t twice[]  = { 0U, 100U, 200U };

    reset_state();
    set_tick_script(before, 2U);
    assert(run_firmware() == 1);
    assert(toggle_count == 0U);                                      /* 99 ms is not a period */
    assert(g_ma_idx == 0U);

    reset_state();
    set_tick_script(at, 2U);
    assert(run_firmware() == 1);
    assert(toggle_count == 1U);
    assert(g_ma_idx == 1U);                                          /* one pass per period */

    reset_state();
    set_tick_script(early, 3U);
    assert(run_firmware() == 1);
    assert(toggle_count == 1U);

    reset_state();
    set_tick_script(twice, 3U);
    assert(run_firmware() == 1);
    assert(toggle_count == 2U);
    assert(g_ma_idx == 2U);
}

/* End to end: the loop must average the DMA buffer, convert, and feed the
 * filter — not just call the pieces in isolation. */
static void test_loop_feeds_averaged_voltage_into_filter(void)
{
    static const uint32_t script[] = { 0U, 100U };
    reset_state();
    fill_buffer(0x0FFFU, 0x0800U, 0x0400U);
    set_tick_script(script, 2U);

    assert(run_firmware() == 1);
    assert(toggle_count == 1U);

    float v0 = adc_to_volt(0x0FFFU);
    float v1 = adc_to_volt(0x0800U);
    float v4 = adc_to_volt(0x0400U);
    assert(g_ma_buf[ADC_CH0_INDEX][0] > v0 - 1e-5f && g_ma_buf[ADC_CH0_INDEX][0] < v0 + 1e-5f);
    assert(g_ma_buf[ADC_CH1_INDEX][0] > v1 - 1e-5f && g_ma_buf[ADC_CH1_INDEX][0] < v1 + 1e-5f);
    assert(g_ma_buf[ADC_CH4_INDEX][0] > v4 - 1e-5f && g_ma_buf[ADC_CH4_INDEX][0] < v4 + 1e-5f);
}

/* A failed HAL call must stop before the DMA sampling is armed. */
static void test_failure_path_skips_start(void)
{
    static const uint32_t script[] = { 0U, 100U };

    reset_state();
    set_tick_script(script, 2U);
    fail_call = FAIL_ADC;
    assert(run_firmware() == 2);                                     /* error_handler */
    assert(irq_disable_calls == 1U);
    assert(adc_init_calls == 1U);
    assert(channel_cfg_calls == 0U);
    assert(calibration_calls == 0U);
    assert(start_dma_calls == 0U);

    reset_state();
    set_tick_script(script, 2U);
    fail_call = FAIL_CALIB;
    assert(run_firmware() == 2);
    assert(calibration_calls == 1U);
    assert(start_dma_calls == 0U);

    reset_state();
    set_tick_script(script, 2U);
    fail_call = FAIL_START;
    assert(run_firmware() == 2);
    assert(start_dma_calls == 1U);
    assert(toggle_count == 0U);                                      /* loop never ran */
}

int main(void)
{
    test_boot_configures_sampling_chain();
    test_channel_average_deinterleaves_ranks();
    test_voltage_scaling();
    test_moving_average_window();
    test_led_heartbeat_period();
    test_loop_feeds_averaged_voltage_into_filter();
    test_failure_path_skips_start();

    puts("PASS adc-dma: production ADC1/DMA/filter code with HAL boundary doubles; "
         "not full firmware, no board evidence");
    return 0;
}

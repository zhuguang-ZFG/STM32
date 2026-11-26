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
TIM_TypeDef test_tim3;

static jmp_buf test_exit;
static uint32_t exit_cause;
static uint32_t delay_limit;
static uint32_t delay_calls;
static uint32_t total_delay_ms;
static uint32_t clock_flags;
static uint32_t init_calls;
static uint32_t config_calls;
static uint32_t start_calls;
static uint32_t ccr_count;
static uint32_t ccr_values[256];
static HAL_StatusTypeDef injected_init_status;
static uint32_t captured_latency;
static GPIO_InitTypeDef captured_gpio;
static TIM_HandleTypeDef captured_tim;
static TIM_OC_InitTypeDef captured_oc;
static uint32_t captured_channel;
static uint32_t started_channel;
static RCC_OscInitTypeDef captured_osc;
static RCC_ClkInitTypeDef captured_clk;

void test_enable_clock(uint32_t mask) { clock_flags |= mask; }

void test_set_compare(TIM_HandleTypeDef *htim, uint32_t channel, uint32_t compare)
{
    assert(htim == &htim3);
    assert(channel == TIM_CHANNEL_1);
    assert(ccr_count < sizeof(ccr_values) / sizeof(ccr_values[0]));
    htim->Instance->CCR1 = compare;
    ccr_values[ccr_count++] = compare;
}

void test_disable_irq(void)
{
    longjmp(test_exit, 2U);
}

void HAL_Init(void) { }
uint32_t HAL_GetTick(void) { return 0U; }
void HAL_IncTick(void) { }

void HAL_Delay(uint32_t delay_ms)
{
    delay_calls++;
    total_delay_ms += delay_ms;
    if (delay_calls >= delay_limit) { longjmp(test_exit, 1U); }
}

void HAL_GPIO_Init(GPIO_TypeDef *port, GPIO_InitTypeDef *config)
{
    assert(port == GPIOA);
    captured_gpio = *config;
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

HAL_StatusTypeDef HAL_TIM_PWM_Init(TIM_HandleTypeDef *htim)
{
    assert(htim == &htim3);
    init_calls++;
    captured_tim = *htim;
    return injected_init_status;
}

HAL_StatusTypeDef HAL_TIM_PWM_ConfigChannel(TIM_HandleTypeDef *htim,
                                            TIM_OC_InitTypeDef *config,
                                            uint32_t channel)
{
    assert(htim == &htim3);
    config_calls++;
    captured_oc = *config;
    captured_channel = channel;
    htim->Instance->CCR1 = config->Pulse;
    return HAL_OK;
}

HAL_StatusTypeDef HAL_TIM_PWM_Start(TIM_HandleTypeDef *htim, uint32_t channel)
{
    assert(htim == &htim3);
    start_calls++;
    started_channel = channel;
    return HAL_OK;
}

static void reset_state(void)
{
    memset(&test_gpioa, 0, sizeof(test_gpioa));
    memset(&test_tim3, 0, sizeof(test_tim3));
    memset(&captured_gpio, 0, sizeof(captured_gpio));
    memset(&captured_tim, 0, sizeof(captured_tim));
    memset(&captured_oc, 0, sizeof(captured_oc));
    memset(&captured_osc, 0, sizeof(captured_osc));
    memset(&captured_clk, 0, sizeof(captured_clk));
    memset(ccr_values, 0, sizeof(ccr_values));
    exit_cause = 0U;
    delay_calls = 0U;
    total_delay_ms = 0U;
    clock_flags = 0U;
    init_calls = 0U;
    config_calls = 0U;
    start_calls = 0U;
    ccr_count = 0U;
    captured_latency = 0U;
    captured_channel = 0U;
    started_channel = 0U;
    injected_init_status = HAL_OK;
}

static uint32_t run_firmware(uint32_t limit, HAL_StatusTypeDef init_status)
{
    uint32_t cause;
    reset_state();
    delay_limit = limit;
    injected_init_status = init_status;
    cause = (uint32_t)setjmp(test_exit);
    if (cause == 0U) { firmware_main(); }
    exit_cause = cause;
    return cause;
}

static void test_clock_and_pin_configuration(void)
{
    assert(run_firmware(1U, HAL_OK) == 1U);
    assert(captured_osc.OscillatorType == RCC_OSCILLATORTYPE_HSE);
    assert(captured_osc.HSEState == RCC_HSE_ON);
    assert(captured_osc.HSEPredivValue == RCC_HSE_PREDIV_DIV1);
    assert(captured_osc.PLL.PLLState == RCC_PLL_ON);
    assert(captured_osc.PLL.PLLSource == RCC_PLLSOURCE_HSE);
    assert(captured_osc.PLL.PLLMUL == RCC_PLL_MUL9);
    assert(captured_clk.SYSCLKSource == RCC_SYSCLKSOURCE_PLLCLK);
    assert(captured_clk.AHBCLKDivider == RCC_SYSCLK_DIV1);
    assert(captured_clk.APB1CLKDivider == RCC_HCLK_DIV2);
    assert(captured_clk.APB2CLKDivider == RCC_HCLK_DIV1);
    assert(captured_latency == FLASH_LATENCY_2);
    assert(clock_flags == 3U);
    assert(captured_gpio.Pin == GPIO_PIN_6);
    assert(captured_gpio.Mode == GPIO_MODE_AF_PP);
    assert(captured_gpio.Pull == GPIO_NOPULL);
    assert(captured_gpio.Speed == GPIO_SPEED_FREQ_HIGH);
}

static void test_pwm_timebase_and_channel(void)
{
    uint32_t sysclk_hz;
    uint32_t tim_clk_hz;
    uint32_t pwm_hz;

    assert(run_firmware(1U, HAL_OK) == 1U);
    assert(init_calls == 1U);
    assert(config_calls == 1U);
    assert(start_calls == 1U);
    assert(captured_tim.Instance == TIM3);
    assert(captured_tim.Init.Prescaler == 71U);
    assert(captured_tim.Init.Period == 999U);
    assert(captured_tim.Init.CounterMode == TIM_COUNTERMODE_UP);
    assert(captured_tim.Init.ClockDivision == TIM_CLOCKDIVISION_DIV1);
    assert(captured_tim.Init.AutoReloadPreload == TIM_AUTORELOAD_PRELOAD_ENABLE);

    sysclk_hz = 8000000U * captured_osc.PLL.PLLMUL;
    assert(sysclk_hz == 72000000U);
    assert(captured_clk.APB1CLKDivider != RCC_HCLK_DIV1);
    tim_clk_hz = (sysclk_hz / captured_clk.APB1CLKDivider) * 2U;
    assert(tim_clk_hz == 72000000U);
    pwm_hz = tim_clk_hz / ((captured_tim.Init.Period + 1U) *
                           (captured_tim.Init.Prescaler + 1U));
    assert(pwm_hz == 1000U);

    assert(captured_channel == TIM_CHANNEL_1);
    assert(started_channel == TIM_CHANNEL_1);
    assert(captured_oc.OCMode == TIM_OCMODE_PWM1);
    assert(captured_oc.Pulse == 499U);
    assert(captured_oc.OCPolarity == TIM_OCPOLARITY_HIGH);
    assert(captured_oc.OCFastMode == TIM_OCFAST_DISABLE);
    assert(captured_oc.OCIdleState == TIM_OCIDLESTATE_RESET);
}

static void test_ccr_sweep_stays_inside_arr(void)
{
    uint32_t i;
    uint32_t min_ccr = UINT32_MAX;
    uint32_t max_ccr = 0U;
    uint32_t saw_zero = 0U;

    assert(run_firmware(220U, HAL_OK) == 1U);
    assert(ccr_count == 220U);
    assert(ccr_values[0U] == 10U);
    assert(ccr_values[99U] == 999U);
    assert(ccr_values[199U] == 0U);
    for (i = 0U; i < ccr_count; i++)
    {
        assert(ccr_values[i] <= 999U);
        if (ccr_values[i] < min_ccr) { min_ccr = ccr_values[i]; }
        if (ccr_values[i] > max_ccr) { max_ccr = ccr_values[i]; }
        if (ccr_values[i] == 0U) { saw_zero = 1U; }
    }
    assert(min_ccr == 0U);
    assert(max_ccr == 999U);
    assert(saw_zero == 1U);
    assert(total_delay_ms == 2200U);
}

static void test_init_failure_stops_before_start(void)
{
    assert(run_firmware(1U, HAL_ERROR) == 2U);
    assert(init_calls == 1U);
    assert(config_calls == 0U);
    assert(start_calls == 0U);
    assert(ccr_count == 0U);
}

int main(void)
{
    test_clock_and_pin_configuration();
    test_pwm_timebase_and_channel();
    test_ccr_sweep_stays_inside_arr();
    test_init_failure_stops_before_start();
    puts("PASS: timer-pwm production-flow regressions");
    return 0;
}

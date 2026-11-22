#include <assert.h>
#include <setjmp.h>
#include <stdbool.h>
#include <stdio.h>
#include "stm32f1xx_hal.h"

#define main firmware_main
#include "../main.c"
#undef main
#include "../stm32f1xx_it.c"

GPIO_TypeDef test_gpioa;
GPIO_TypeDef test_gpioc;
static jmp_buf firmware_exit;
static uint32_t tick;
static bool advance_tick;
static bool clock_a_enabled;
static bool clock_c_enabled;
static bool pin_a_preloaded;
static bool pin_c_preloaded;
static unsigned initialized_ports;
static HAL_StatusTypeDef oscillator_status;

void test_enable_clock(GPIO_TypeDef *port)
{
    if (port == GPIOA) { clock_a_enabled = true; }
    if (port == GPIOC) { clock_c_enabled = true; }
}

void test_disable_irq(void) { longjmp(firmware_exit, 2); }
void HAL_Init(void) { tick = 0U; }
uint32_t HAL_GetTick(void) { return advance_tick ? tick++ : tick; }
void HAL_IncTick(void) { tick++; }

void HAL_Delay(uint32_t delay_ms)
{
    assert(delay_ms == 500U);
    assert(tick == 0U);
    assert(initialized_ports == 2U);
    longjmp(firmware_exit, 1);
}

void HAL_GPIO_WritePin(GPIO_TypeDef *port, uint16_t pin, GPIO_PinState state)
{
    if (port == GPIOA) { assert(clock_a_enabled); pin_a_preloaded = true; }
    if (port == GPIOC) { assert(clock_c_enabled); pin_c_preloaded = true; }
    if (state == GPIO_PIN_SET) { port->ODR |= pin; }
    else { port->ODR &= ~(uint32_t)pin; }
}

void HAL_GPIO_TogglePin(GPIO_TypeDef *port, uint16_t pin) { port->ODR ^= pin; }
GPIO_PinState HAL_GPIO_ReadPin(GPIO_TypeDef *port, uint16_t pin)
{
    return (port->ODR & pin) ? GPIO_PIN_SET : GPIO_PIN_RESET;
}

void HAL_GPIO_Init(GPIO_TypeDef *port, GPIO_InitTypeDef *config)
{
    assert(config->Mode == GPIO_MODE_OUTPUT_PP);
    if (port == GPIOC) { assert(pin_c_preloaded); assert((port->ODR & GPIO_PIN_13) != 0U); }
    if (port == GPIOA) { assert(pin_a_preloaded); assert((port->ODR & GPIO_PIN_0) == 0U); }
    initialized_ports++;
}

HAL_StatusTypeDef HAL_RCC_OscConfig(RCC_OscInitTypeDef *config)
{
    assert(config->PLL.PLLMUL == RCC_PLL_MUL9);
    return oscillator_status;
}

HAL_StatusTypeDef HAL_RCC_ClockConfig(RCC_ClkInitTypeDef *config, uint32_t latency)
{
    assert(config->APB1CLKDivider == RCC_HCLK_DIV2);
    assert(latency == FLASH_LATENCY_2);
    return HAL_OK;
}

int main(void)
{
    int exit_reason = setjmp(firmware_exit);
    if (exit_reason == 0) { firmware_main(); }
    assert(exit_reason == 1);
    assert((GPIOC->ODR & GPIO_PIN_13) == 0U);

    tick = 41U;
    SysTick_Handler();
    assert(tick == 42U);

    tick = UINT32_MAX - 2U;
    advance_tick = true;
    delay_poll_tick(5U);
    assert(tick == 3U);
    advance_tick = false;

    oscillator_status = HAL_ERROR;
    exit_reason = setjmp(firmware_exit);
    if (exit_reason == 0) { SystemClock_Config(); }
    assert(exit_reason == 2);
    puts("PASS: zero-tick startup, inactive preload, SysTick, wraparound, HSE failure");
    return 0;
}

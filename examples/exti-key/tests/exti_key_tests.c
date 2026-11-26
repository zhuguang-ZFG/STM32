/* Host regression: run the production EXTI0/key code against explicit HAL doubles.
 * Not a full firmware build and not board evidence. */
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
static uint32_t exti_handler_calls;
static uint16_t exti_handler_pin;
static uint32_t nvic_priority_calls;
static uint32_t nvic_priority_irq;
static uint32_t nvic_priority_preempt;
static uint32_t nvic_priority_sub;
static uint32_t nvic_enable_calls;
static uint32_t nvic_enabled_irq;
static uint32_t delay_calls;
static uint32_t total_delay_ms;
static uint32_t delay_limit;
static uint32_t bounce_during_delay;
static uint32_t irq_disable_calls;
static uint32_t irq_enable_calls;
static GPIO_PinState key_level;
static RCC_OscInitTypeDef captured_osc;
static RCC_ClkInitTypeDef captured_clk;
static uint32_t captured_latency;

void test_enable_clock(uint32_t mask) { clock_flags |= mask; }

void test_disable_irq(void) { irq_disable_calls++; }

void test_enable_irq(void) { irq_enable_calls++; }

void HAL_Init(void) { init_calls++; }

void HAL_Delay(uint32_t delay_ms)
{
    delay_calls++;
    total_delay_ms += delay_ms;
    if (bounce_during_delay > 0U)
    {
        bounce_during_delay--;
        HAL_GPIO_EXTI_Callback(KEY_PIN);   /* a bounce edge inside the window */
    }
    if (delay_calls >= delay_limit) { longjmp(test_exit, 1); }
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
    if (state == GPIO_PIN_SET) { port->ODR |= pin; }
    else { port->ODR &= ~(uint32_t)pin; }
}

GPIO_PinState HAL_GPIO_ReadPin(GPIO_TypeDef *port, uint16_t pin)
{
    assert(port == GPIOA);
    assert(pin == GPIO_PIN_0);
    return key_level;
}

void HAL_GPIO_TogglePin(GPIO_TypeDef *port, uint16_t pin)
{
    assert(port == GPIOC);
    assert(pin == GPIO_PIN_13);
    toggle_count++;
    port->ODR ^= pin;
}

/* The locked HAL clears the EXTI pending bit and then calls the user callback. */
void HAL_GPIO_EXTI_IRQHandler(uint16_t pin)
{
    exti_handler_calls++;
    exti_handler_pin = pin;
    HAL_GPIO_EXTI_Callback(pin);
}

void HAL_NVIC_SetPriority(uint32_t irqn, uint32_t preempt, uint32_t sub)
{
    nvic_priority_calls++;
    nvic_priority_irq = irqn;
    nvic_priority_preempt = preempt;
    nvic_priority_sub = sub;
}

void HAL_NVIC_EnableIRQ(uint32_t irqn)
{
    nvic_enable_calls++;
    nvic_enabled_irq = irqn;
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

static void reset_state(void)
{
    memset(&test_gpioa, 0, sizeof(test_gpioa));
    memset(&test_gpioc, 0, sizeof(test_gpioc));
    memset(&captured_osc, 0, sizeof(captured_osc));
    memset(&captured_clk, 0, sizeof(captured_clk));
    memset(gpio_init_ports, 0, sizeof(gpio_init_ports));
    memset(gpio_init_configs, 0, sizeof(gpio_init_configs));
    clock_flags = 0;
    init_calls = 0;
    gpio_init_count = 0;
    write_count = 0;
    write_port = NULL;
    write_pin = 0;
    write_state = GPIO_PIN_RESET;
    toggle_count = 0;
    exti_handler_calls = 0;
    exti_handler_pin = 0;
    nvic_priority_calls = 0;
    nvic_priority_irq = 0;
    nvic_priority_preempt = 0;
    nvic_priority_sub = 0;
    nvic_enable_calls = 0;
    nvic_enabled_irq = 0;
    delay_calls = 0;
    total_delay_ms = 0;
    delay_limit = 1000U;
    bounce_during_delay = 0;
    irq_disable_calls = 0;
    irq_enable_calls = 0;
    key_level = GPIO_PIN_RESET;
    captured_latency = 0;
    g_key_event = 0;
    g_key_count = 0;
}

/* Full boot: HAL_Init → clock → GPIO → EXTI → main loop, stopped at the first
 * debounce delay by the delay double. */
static void test_boot_sequence(void)
{
    reset_state();
    g_key_event = 1;        /* one event already pending when the loop starts */
    delay_limit = 1;

    if (setjmp(test_exit) == 0)
    {
        firmware_main();
        assert(0 && "main loop returned");
    }

    assert(init_calls == 1U);
    assert(captured_osc.OscillatorType == RCC_OSCILLATORTYPE_HSE);
    assert(captured_osc.HSEState == RCC_HSE_ON);
    assert(captured_osc.PLL.PLLSource == RCC_PLLSOURCE_HSE);
    assert(captured_osc.PLL.PLLMUL == RCC_PLL_MUL9);
    assert(captured_clk.SYSCLKSource == RCC_SYSCLKSOURCE_PLLCLK);
    assert(captured_clk.APB1CLKDivider == RCC_HCLK_DIV2);
    assert(captured_latency == FLASH_LATENCY_2);

    assert(clock_flags == (1U | 2U | 4U));   /* GPIOA, GPIOC, AFIO */

    assert(gpio_init_count == 2U);
    assert(gpio_init_ports[0] == GPIOC);
    assert(gpio_init_configs[0].Pin == GPIO_PIN_13);
    assert(gpio_init_configs[0].Mode == GPIO_MODE_OUTPUT_PP);
    assert(gpio_init_configs[0].Pull == GPIO_NOPULL);
    assert(gpio_init_ports[1] == GPIOA);
    assert(gpio_init_configs[1].Pin == GPIO_PIN_0);
    assert(gpio_init_configs[1].Mode == GPIO_MODE_IT_FALLING);
    assert(gpio_init_configs[1].Pull == GPIO_PULLUP);

    assert(write_count == 1U);               /* initial off level, before any toggle */
    assert(write_port == GPIOC);
    assert(write_pin == GPIO_PIN_13);
    assert(write_state == GPIO_PIN_SET);

    assert(nvic_priority_calls == 1U);
    assert(nvic_priority_irq == EXTI0_IRQn);
    assert(nvic_priority_preempt == 1U);
    assert(nvic_priority_sub == 0U);
    assert(nvic_enable_calls == 1U);
    assert(nvic_enabled_irq == EXTI0_IRQn);

    assert(exti_handler_calls == 0U);        /* no interrupt while booting */
    assert(delay_calls == 1U);               /* first loop pass reaches debounce */
    assert(total_delay_ms == KEY_DEBOUNCE_MS);
    assert(irq_disable_calls == 0U);         /* stopped inside the delay */
    assert(irq_enable_calls == 0U);
    assert(g_key_event == 1U);               /* flag is cleared only after the delay */
}

static void test_vector_reaches_callback(void)
{
    reset_state();
    EXTI0_IRQHandler();
    assert(exti_handler_calls == 1U);
    assert(exti_handler_pin == KEY_PIN);
    assert(g_key_event == 1U);
    assert(g_key_count == 1U);

    g_key_event = 0;
    HAL_GPIO_EXTI_Callback(GPIO_PIN_13);     /* a different pin must not count */
    assert(g_key_event == 0U);
    assert(g_key_count == 1U);
}

static void test_pressed_key_toggles_once(void)
{
    reset_state();
    g_key_event = 1;
    key_level = GPIO_PIN_RESET;

    key_process();

    assert(toggle_count == 1U);
    assert((test_gpioc.ODR & GPIO_PIN_13) != 0U);
    assert(write_count == 0U);               /* never force the level after an event */
    assert(g_key_event == 0U);
    assert(delay_calls == 1U);
    assert(total_delay_ms == KEY_DEBOUNCE_MS);
    assert(irq_disable_calls == 1U);
    assert(irq_enable_calls == 1U);
}

static void test_released_key_is_rejected(void)
{
    reset_state();
    g_key_event = 1;
    key_level = GPIO_PIN_SET;                /* bounce or release during the delay */

    key_process();

    assert(toggle_count == 0U);
    assert(write_count == 0U);
    assert(g_key_event == 0U);
    assert(delay_calls == 1U);
}

static void test_no_event_does_nothing(void)
{
    reset_state();

    key_process();

    assert(delay_calls == 0U);
    assert(toggle_count == 0U);
    assert(irq_disable_calls == 0U);
}

static void test_irq_burst_coalesces_to_one_toggle(void)
{
    reset_state();
    EXTI0_IRQHandler();
    EXTI0_IRQHandler();
    EXTI0_IRQHandler();
    assert(g_key_count == 3U);               /* raw IRQ count stays visible */

    key_process();

    assert(toggle_count == 1U);              /* the flag is one bit, not a queue */
    assert(g_key_event == 0U);
}

/* The debounce window must absorb edges of the same press. Clearing the flag
 * before HAL_Delay() lets a bounce re-arm it and toggle twice for one press. */
static void test_bounce_inside_debounce_window_is_absorbed(void)
{
    reset_state();
    key_level = GPIO_PIN_RESET;
    EXTI0_IRQHandler();                      /* real vector → callback: event set */
    assert(g_key_count == 1U);

    bounce_during_delay = 1;                 /* second edge lands inside the 20 ms window */
    key_process();

    assert(toggle_count == 1U);              /* one press, one toggle */
    assert(g_key_count == 2U);               /* raw IRQ count still visible */
    assert(g_key_event == 0U);               /* the bounce edge was consumed, not queued */
    assert(delay_calls == 1U);
    assert(total_delay_ms == KEY_DEBOUNCE_MS);

    key_process();                           /* no new edge, key still held low */
    assert(toggle_count == 1U);
    assert(delay_calls == 1U);
}

static void test_toggles_alternate(void)
{
    reset_state();
    for (uint32_t i = 0U; i < 4U; i++)
    {
        g_key_event = 1;
        key_level = GPIO_PIN_RESET;
        key_process();
    }

    assert(toggle_count == 4U);
    assert((test_gpioc.ODR & GPIO_PIN_13) == 0U);
}

int main(void)
{
    test_boot_sequence();
    test_vector_reaches_callback();
    test_pressed_key_toggles_once();
    test_released_key_is_rejected();
    test_no_event_does_nothing();
    test_irq_burst_coalesces_to_one_toggle();
    test_bounce_inside_debounce_window_is_absorbed();
    test_toggles_alternate();

    puts("PASS exti-key: production EXTI0/key code with HAL boundary doubles; "
         "not full firmware, not board evidence");
    return 0;
}

/* Production paths with explicit HAL/RTOS boundaries; no kernel/hardware linked. */
#ifdef NDEBUG
#undef NDEBUG
#endif
#include <assert.h>
#include <setjmp.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
#define main firmware_main
#include "../main.c"
#undef main

GPIO_TypeDef test_gpioa, test_gpioc;
USART_TypeDef test_usart1;
static jmp_buf stop;
enum { STOP_TASK = 1, STOP_ERROR = 2, STOP_DELAY = 3 };
static int queue_token, mutex_token;
static bool irq_enabled, exti_pending, nvic_pending, scheduler_running;
static bool scheduler_returns, fail_queue, fail_mutex;
static unsigned task_count, fail_task, irq_enables, receives, sends, yields;
static unsigned mutex_gives, transmissions, clear_step, gpio_toggles;
static uint32_t irq_priority, grouping;
static TickType_t delay_ticks;
static TaskFunction_t task_functions[3];
static BaseType_t send_result, wake_result, take_result;
static char output[128];

void HAL_Init(void) {}
void test_disable_irq(void) { longjmp(stop, STOP_ERROR); }
void HAL_GPIO_Init(GPIO_TypeDef *port, GPIO_InitTypeDef *config) { (void)port; (void)config; }
void HAL_GPIO_WritePin(GPIO_TypeDef *port, uint16_t pin, GPIO_PinState state)
{ assert(port == GPIOC && pin == GPIO_PIN_13 && state == GPIO_PIN_SET); }
void HAL_GPIO_TogglePin(GPIO_TypeDef *port, uint16_t pin)
{ assert(port == GPIOC && pin == GPIO_PIN_13); gpio_toggles++; }
void HAL_NVIC_DisableIRQ(uint32_t irq) { assert(irq == EXTI0_IRQn); irq_enabled = false; }
void HAL_NVIC_SetPriorityGrouping(uint32_t group) { grouping = group; }
void HAL_NVIC_SetPriority(uint32_t irq, uint32_t priority, uint32_t subpriority)
{ assert(irq == EXTI0_IRQn && subpriority == 0U); irq_priority = priority; }
void test_clear_exti(uint16_t pin)
{ assert(pin == GPIO_PIN_0); exti_pending = false; clear_step = 1U; }
void HAL_NVIC_ClearPendingIRQ(uint32_t irq)
{ assert(irq == EXTI0_IRQn && clear_step == 1U); nvic_pending = false; clear_step = 2U; }
void HAL_NVIC_EnableIRQ(uint32_t irq)
{
    assert(irq == EXTI0_IRQn);
    /* Break caught: enabling EXTI before objects or scheduler are ready. */
    assert(scheduler_running && g_key_queue != NULL && g_uart_mutex != NULL);
    assert(task_count == 3U);
    assert(clear_step == 2U && !exti_pending && !nvic_pending);
    assert(grouping == NVIC_PRIORITYGROUP_4);
    irq_enabled = true;
    irq_enables++;
}
void HAL_GPIO_EXTI_IRQHandler(uint16_t pin)
{
    if (exti_pending) {
        exti_pending = false;
        HAL_GPIO_EXTI_Callback(pin);
    }
}
HAL_StatusTypeDef HAL_RCC_OscConfig(RCC_OscInitTypeDef *config)
{ assert(config->PLL.PLLMUL == RCC_PLL_MUL9); return HAL_OK; }
HAL_StatusTypeDef HAL_RCC_ClockConfig(RCC_ClkInitTypeDef *config, uint32_t latency)
{ assert(config->APB1CLKDivider == RCC_HCLK_DIV2 && latency == FLASH_LATENCY_2); return HAL_OK; }
HAL_StatusTypeDef HAL_UART_Init(UART_HandleTypeDef *handle)
{ assert(handle->Instance == USART1 && handle->Init.BaudRate == 115200U); return HAL_OK; }
HAL_StatusTypeDef HAL_UART_Transmit(UART_HandleTypeDef *handle, uint8_t *data,
                                    uint16_t length, uint32_t timeout)
{
    assert(handle == &huart1 && timeout == 100U);
    assert(length < sizeof(output));
    memcpy(output, data, length);
    output[length] = '\0';
    transmissions++;
    return HAL_OK;
}
QueueHandle_t xQueueCreate(UBaseType_t length, UBaseType_t item_size)
{
    assert(!irq_enabled && !scheduler_running);
    assert(length == 8U && item_size == 1U);
    return fail_queue ? NULL : &queue_token;
}
SemaphoreHandle_t xSemaphoreCreateMutex(void)
{
    assert(!irq_enabled && !scheduler_running);
    return fail_mutex ? NULL : &mutex_token;
}
BaseType_t xTaskCreate(TaskFunction_t task, const char *name, uint16_t depth,
                       void *argument, UBaseType_t priority, TaskHandle_t *handle)
{
    static const char *const names[] = {"LED", "KEY", "UART"};
    static const unsigned depths[] = {128U, 192U, 256U};
    static const unsigned priorities[] = {1U, 2U, 1U};
    assert(task_count < 3U && !irq_enabled && !scheduler_running);
    assert(g_key_queue != NULL && g_uart_mutex != NULL);
    assert(strcmp(name, names[task_count]) == 0);
    assert(depth == depths[task_count] && sizeof(StackType_t) == 4U);
    assert(priority == priorities[task_count] && argument == NULL && handle == NULL);
    task_functions[task_count++] = task;
    return task_count == fail_task ? -1 : pdPASS; /* FreeRTOS allocation error, not pdFAIL=0 */
}
void vTaskStartScheduler(void)
{
    assert(task_count == 3U && !irq_enabled);
    if (scheduler_returns) { return; }
    scheduler_running = true;
    /* Boot-time edges are discarded when the consumer starts. */
    exti_pending = nvic_pending = true;
    task_functions[1](NULL);
    assert(false);
}
BaseType_t xQueueReceive(QueueHandle_t queue, void *item, TickType_t wait)
{
    assert(queue == &queue_token && wait == portMAX_DELAY);
    assert(scheduler_running && irq_enabled && irq_enables == 1U);
    if (receives++ != 0U) { longjmp(stop, STOP_TASK); }
    *(uint8_t *)item = 1U;
    return pdTRUE;
}
BaseType_t xQueueSendFromISR(QueueHandle_t queue, const void *item, BaseType_t *woken)
{
    assert(scheduler_running && queue == &queue_token);
    assert(*(const uint8_t *)item == 1U && *woken == pdFALSE);
    if (send_result == pdPASS) { *woken = wake_result; }
    sends++;
    return send_result;
}
void test_yield_from_isr(BaseType_t woken) { if (woken != pdFALSE) { yields++; } }
BaseType_t xSemaphoreTake(SemaphoreHandle_t mutex, TickType_t wait)
{ assert(mutex == &mutex_token && wait == 100U); return take_result; }
BaseType_t xSemaphoreGive(SemaphoreHandle_t mutex)
{ assert(mutex == &mutex_token); mutex_gives++; return pdTRUE; }
void vTaskDelay(TickType_t ticks) { delay_ticks = ticks; longjmp(stop, STOP_DELAY); }
TickType_t xTaskGetTickCount(void) { return 123U; }

static void reset_fixture(void)
{
    g_key_queue = g_uart_mutex = NULL;
    huart1 = (UART_HandleTypeDef){0};
    irq_enabled = exti_pending = nvic_pending = scheduler_running = false;
    scheduler_returns = fail_queue = fail_mutex = false;
    task_count = fail_task = irq_enables = receives = sends = yields = 0U;
    mutex_gives = transmissions = clear_step = gpio_toggles = 0U;
    grouping = irq_priority = UINT32_MAX;
    delay_ticks = 0U;
    send_result = take_result = pdPASS;
    wake_result = pdFALSE;
    output[0] = '\0';
}
static void boot(void)
{
    int reason = setjmp(stop);
    if (reason == 0) { firmware_main(); assert(false); }
    assert(reason == STOP_TASK);
    assert(strcmp(output, "KEY 1 pressed @123 ms\r\n") == 0);
    assert(transmissions == 1U && mutex_gives == 1U && irq_enables == 1U);
    if (TEST_SYSCALL_RAW == 0x60U) { assert(irq_priority == 6U); }
    else { assert(irq_priority == 5U); }
}
static void test_startup_and_isr(void)
{
    reset_fixture();
    irq_enabled = true; /* BSP must also close an IRQ left enabled by earlier code. */
    boot();
    HAL_GPIO_EXTI_Callback(GPIO_PIN_9);
    assert(sends == 0U && yields == 0U);
    exti_pending = true;
    EXTI0_IRQHandler();
    assert(sends == 1U && yields == 0U && !exti_pending);
    wake_result = pdTRUE;
    exti_pending = true;
    EXTI0_IRQHandler();
    assert(sends == 2U && yields == 1U);
    send_result = pdFAIL;
    exti_pending = true;
    EXTI0_IRQHandler();
    assert(sends == 3U && yields == 1U);
}
static void test_initialization_failure(unsigned failure)
{
    reset_fixture();
    fail_queue = failure == 0U;
    fail_mutex = failure == 1U;
    if (failure >= 2U && failure <= 4U) { fail_task = failure - 1U; }
    scheduler_returns = failure == 5U;
    int reason = setjmp(stop);
    if (reason == 0) { firmware_main(); assert(false); }
    assert(reason == STOP_ERROR && !irq_enabled && irq_enables == 0U);
    if (failure < 2U) { assert(task_count == 0U); }
    else if (failure < 5U) { assert(task_count == failure - 1U); }
    assert(!scheduler_running);
}
static void test_initialization_failures(void)
{
    for (unsigned failure = 0U; failure < 6U; failure++) {
        test_initialization_failure(failure);
    }
}
static void test_tasks_and_mutex(void)
{
    reset_fixture();
    boot();
    int reason = setjmp(stop);
    if (reason == 0) { task_functions[0](NULL); assert(false); }
    assert(reason == STOP_DELAY && gpio_toggles == 1U && delay_ticks == 500U);
    reason = setjmp(stop);
    if (reason == 0) { task_functions[2](NULL); assert(false); }
    assert(reason == STOP_DELAY && delay_ticks == 1000U);
    assert(strcmp(output, "heartbeat 0, tick=123\r\n") == 0);
    take_result = pdFALSE;
    unsigned previous_transmissions = transmissions, previous_gives = mutex_gives;
    uart_print("must not transmit without ownership");
    assert(transmissions == previous_transmissions && mutex_gives == previous_gives);
}
int main(void)
{
    test_startup_and_isr();
    test_initialization_failures();
    test_tasks_and_mutex();
    puts("PASS: production startup/allocations, task arguments, IRQ order/priority, FromISR, delays and mutex paths; kernel/hardware unverified");
    return 0;
}

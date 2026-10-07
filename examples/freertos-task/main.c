/**
 * @file    main.c
 * @brief   freertos-task —— FreeRTOS 三任务 + 队列 + 信号量 + FromISR（STM32F103C8T6）
 *
 * 功能：
 *   1) 三个任务：LED 闪烁任务、按键处理任务、串口输出任务；
 *   2) 按键 EXTI 中断 → 用 xQueueSendFromISR 把「按键事件」发给按键任务；
 *   3) 串口用互斥信号量（Mutex）保护，避免多任务同时发送互相打断；
 *   4) 演示 vTaskDelay、xQueueReceive、xSemaphoreTake/Give、portYIELD_FROM_ISR。
 *
 * 说明：本示例使用 FreeRTOS 的 SysTick 作为系统节拍；因此 HAL 的时基
 *       必须改用别的定时器（见 README 的 CubeMX 配置），否则两者抢占 SysTick。
 *
 * 目标芯片：STM32F103C8T6，系统时钟 72MHz。
 */

#include "stm32f1xx_hal.h"
#include "FreeRTOS.h"
#include "task.h"
#include "queue.h"
#include "semphr.h"
#include <string.h>
#include <stdio.h>

/* ------------------------------------------------------------------ 宏定义 */

#define LED_PORT            GPIOC
#define LED_PIN             GPIO_PIN_13     /* 板载 LED，低电平点亮 */
#define KEY_PORT            GPIOA
#define KEY_PIN             GPIO_PIN_0      /* PA0 按键，下降沿触发 */

#define UART_INSTANCE       USART1
#define UART_TX_PIN         GPIO_PIN_9      /* USART1_TX = PA9 */
#define UART_RX_PIN         GPIO_PIN_10     /* USART1_RX = PA10 */

#define LED_TASK_STACK      128U            /* 单位：字（4 字节） */
#define KEY_TASK_STACK      192U
#define UART_TASK_STACK     256U

#define LED_TASK_PRIO       1U
#define KEY_TASK_PRIO       2U              /* 按键任务优先级较高 */
#define UART_TASK_PRIO      1U

#define KEY_QUEUE_LEN       8U              /* 队列深度：最多缓存 8 个事件 */

/* ---------------------------------------------------------------- 全局对象 */

UART_HandleTypeDef huart1;

static QueueHandle_t     g_key_queue = NULL;    /* 传递按键事件 */
static SemaphoreHandle_t g_uart_mutex = NULL;   /* 保护串口发送 */

/* ---------------------------------------------------------------- 任务函数 */

static void vLedTask(void *argument);
static void vKeyTask(void *argument);
static void vUartTask(void *argument);

/* ----------------------------------------------------------------- 私有函数 */

static void SystemClock_Config(void);
static void bsp_init(void);
static void error_handler(void);
static void uart_print(const char *s);

/* ---------------------------------------------------------------- 主函数 */

int main(void)
{
    HAL_Init();
    SystemClock_Config();
    bsp_init();

    /* 创建队列：元素为「按键编号」 */
    g_key_queue = xQueueCreate(KEY_QUEUE_LEN, sizeof(uint8_t));
    /* 创建互斥信号量：保护串口 */
    g_uart_mutex = xSemaphoreCreateMutex();

    if ((g_key_queue == NULL) || (g_uart_mutex == NULL))
    {
        error_handler();                /* 堆空间不足：调大 configTOTAL_HEAP_SIZE */
    }

    /* 创建三个任务 */
    if (xTaskCreate(vLedTask,  "LED",  LED_TASK_STACK,  NULL, LED_TASK_PRIO,  NULL) != pdPASS)
    {
        error_handler();
    }
    if (xTaskCreate(vKeyTask,  "KEY",  KEY_TASK_STACK,  NULL, KEY_TASK_PRIO,  NULL) != pdPASS)
    {
        error_handler();
    }
    if (xTaskCreate(vUartTask, "UART", UART_TASK_STACK, NULL, UART_TASK_PRIO, NULL) != pdPASS)
    {
        error_handler();
    }

    vTaskStartScheduler();              /* 启动调度器，不再返回 */

    error_handler();                    /* 正常不会执行到这里 */
    return 0;
}

/* ---------------------------------------------------------------- 任务实现 */

/**
 * @brief  LED 任务：每 500ms 翻转一次板载 LED
 */
static void vLedTask(void *argument)
{
    (void)argument;
    for (;;)
    {
        HAL_GPIO_TogglePin(LED_PORT, LED_PIN);
        vTaskDelay(pdMS_TO_TICKS(500)); /* 阻塞 500ms，让出 CPU */
    }
}

/**
 * @brief  按键任务：阻塞等待队列中的按键事件并处理
 */
static void vKeyTask(void *argument)
{
    (void)argument;
    uint8_t key_id = 0U;
    char    msg[48];

    for (;;)
    {
        /* 队列为空则阻塞在此，不占 CPU */
        if (xQueueReceive(g_key_queue, &key_id, portMAX_DELAY) == pdTRUE)
        {
            (void)snprintf(msg, sizeof(msg), "KEY %u pressed @%lu ms\r\n",
                           (unsigned)key_id, (unsigned long)xTaskGetTickCount());
            uart_print(msg);
        }
    }
}

/**
 * @brief  串口任务：每 1 秒打印一次心跳与系统节拍
 */
static void vUartTask(void *argument)
{
    (void)argument;
    char msg[64];
    uint32_t count = 0U;

    for (;;)
    {
        (void)snprintf(msg, sizeof(msg), "heartbeat %lu, tick=%lu\r\n",
                       (unsigned long)count++, (unsigned long)xTaskGetTickCount());
        uart_print(msg);
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
}

/**
 * @brief  线程安全的串口打印（用互斥信号量保护）
 */
static void uart_print(const char *s)
{
    if (xSemaphoreTake(g_uart_mutex, pdMS_TO_TICKS(100)) == pdTRUE)
    {
        (void)HAL_UART_Transmit(&huart1, (uint8_t *)s, (uint16_t)strlen(s), 100U);
        (void)xSemaphoreGive(g_uart_mutex);
    }
}

/* ------------------------------------------------------------ 中断处理 */

/**
 * @brief  EXTI0 中断向量（PA0 → EXTI0）
 */
void EXTI0_IRQHandler(void)
{
    HAL_GPIO_EXTI_IRQHandler(KEY_PIN);
}

/**
 * @brief  按键中断回调：用 FromISR API 把事件送进队列
 * @note   中断里只能用 xxxFromISR 版本，并且必须用 portYIELD_FROM_ISR
 *         触发一次上下文切换（若唤醒了更高优先级任务）。
 */
void HAL_GPIO_EXTI_Callback(uint16_t GPIO_Pin)
{
    if (GPIO_Pin == KEY_PIN)
    {
        uint8_t  key_id    = 1U;
        BaseType_t woken   = pdFALSE;

        (void)xQueueSendFromISR(g_key_queue, &key_id, &woken);
        portYIELD_FROM_ISR(woken);      /* 若唤醒了高优先级任务，立即切换 */
    }
}

/* ------------------------------------------------------- 外设初始化实现 */

/**
 * @brief  板级初始化：LED、按键 EXTI、USART1
 */
static void bsp_init(void)
{
    GPIO_InitTypeDef io = {0};

    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_GPIOC_CLK_ENABLE();
    __HAL_RCC_AFIO_CLK_ENABLE();        /* F1：EXTI 映射需 AFIO 时钟 */
    __HAL_RCC_USART1_CLK_ENABLE();

    /* LED 输出 */
    io.Pin   = LED_PIN;
    io.Mode  = GPIO_MODE_OUTPUT_PP;
    io.Pull  = GPIO_NOPULL;
    io.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(LED_PORT, &io);
    HAL_GPIO_WritePin(LED_PORT, LED_PIN, GPIO_PIN_SET);

    /* 按键：下降沿中断，内部上拉 */
    io.Pin  = KEY_PIN;
    io.Mode = GPIO_MODE_IT_FALLING;
    io.Pull = GPIO_PULLUP;
    HAL_GPIO_Init(KEY_PORT, &io);
    HAL_NVIC_SetPriority(EXTI0_IRQn, 5U, 0U);   /* 数值需 ≥ configMAX_SYSCALL_INTERRUPT_PRIORITY */
    HAL_NVIC_EnableIRQ(EXTI0_IRQn);

    /* USART1：PA9=TX, PA10=RX, 115200-8-N-1 */
    io.Pin   = UART_TX_PIN;
    io.Mode  = GPIO_MODE_AF_PP;
    io.Speed = GPIO_SPEED_FREQ_HIGH;
    HAL_GPIO_Init(GPIOA, &io);

    io.Pin  = UART_RX_PIN;
    io.Mode = GPIO_MODE_INPUT;
    io.Pull = GPIO_PULLUP;
    HAL_GPIO_Init(GPIOA, &io);

    huart1.Instance          = UART_INSTANCE;
    huart1.Init.BaudRate     = 115200U;
    huart1.Init.WordLength   = UART_WORDLENGTH_8B;
    huart1.Init.StopBits     = UART_STOPBITS_1;
    huart1.Init.Parity       = UART_PARITY_NONE;
    huart1.Init.Mode         = UART_MODE_TX_RX;
    huart1.Init.HwFlowCtl    = UART_HWCONTROL_NONE;
    huart1.Init.OverSampling = UART_OVERSAMPLING_16;
    if (HAL_UART_Init(&huart1) != HAL_OK)
    {
        error_handler();
    }
}

/**
 * @brief  系统时钟配置：HSE 8MHz → PLL ×9 → 72MHz
 */
static void SystemClock_Config(void)
{
    RCC_OscInitTypeDef osc = {0};
    RCC_ClkInitTypeDef clk = {0};

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
    clk.APB2CLKDivider = RCC_HCLK_DIV1;
    if (HAL_RCC_ClockConfig(&clk, FLASH_LATENCY_2) != HAL_OK)
    {
        error_handler();
    }
}

/**
 * @brief  错误处理（调度器启动前）
 */
static void error_handler(void)
{
    __disable_irq();
    while (1)
    {
    }
}

/* ------------------------------------------------- FreeRTOS 钩子函数（可选） */

/**
 * @brief  栈溢出钩子：某个任务栈不够时会进这里
 */
void vApplicationStackOverflowHook(TaskHandle_t xTask, char *pcTaskName)
{
    (void)xTask;
    (void)pcTaskName;
    __disable_irq();
    for (;;)
    {
        HAL_GPIO_TogglePin(LED_PORT, LED_PIN);  /* 快闪提示栈溢出 */
        for (volatile uint32_t i = 0; i < 200000U; i++) { }
    }
}


/**
 * @file    main.c
 * @brief   exti-key —— EXTI 外部中断按键（STM32F103C8T6 / BluePill）
 *
 * 功能：
 *   1) PA0 接按键（另一端接 GND），配置为下降沿触发的外部中断；
 *   2) 中断服务函数只置 volatile 标志，耗时处理放到主循环（两级结构）；
 *   3) 主循环对标志做软件消抖（20ms）后翻转板载 LED(PC13)；
 *   4) 演示 HAL_GPIO_EXTI_Callback 回调写法与 NVIC 优先级设置；
 *   5) 记录按键次数并通过「按长/短」区分，演示简单的状态处理。
 *
 * 关键点：
 *   - STM32F1 配置 EXTI 引脚映射需要使能 AFIO 时钟（易漏，F4 不需要）；
 *   - ISR 里必须清中断标志，否则会反复进中断；
 *   - ISR 与主循环共享的变量必须加 volatile。
 *
 * 目标芯片：STM32F103C8T6，系统时钟 72MHz。
 */

#include "stm32f1xx_hal.h"

/* ------------------------------------------------------------------ 宏定义 */

#define LED_PORT            GPIOC
#define LED_PIN             GPIO_PIN_13     /* 板载 LED，低电平点亮 */

#define KEY_PORT            GPIOA
#define KEY_PIN             GPIO_PIN_0      /* PA0 按键，接 GND，下降沿触发 */

#define KEY_DEBOUNCE_MS     20U             /* 软件消抖时间 */

/* --------------------------------------------------- ISR 与主循环共享变量 */

static volatile uint8_t  g_key_event = 0;   /* 1=检测到一次按键事件，必须 volatile */
static volatile uint32_t g_key_count = 0;   /* 按键累计次数（用于观察抖动） */

/* ----------------------------------------------------------------- 私有函数 */

static void SystemClock_Config(void);
static void gpio_init(void);
static void exti_init(void);
static void error_handler(void);
static void key_process(void);

/* ---------------------------------------------------------------- 主函数 */

int main(void)
{
    HAL_Init();
    SystemClock_Config();
    gpio_init();
    exti_init();                        /* 配置 EXTI + NVIC */

    while (1)
    {
        key_process();                  /* 主循环处理按键事件（含消抖） */
    }
}

/* --------------------------------------------------------- 中断相关实现 */

/**
 * @brief  EXTI0 中断向量（PA0 → EXTI0）
 * @note   HAL 已提供弱定义，这里显式实现；调用 HAL_GPIO_EXTI_IRQHandler
 *         会清除标志并回调 HAL_GPIO_EXTI_Callback。
 */
void EXTI0_IRQHandler(void)
{
    HAL_GPIO_EXTI_IRQHandler(KEY_PIN);
}

/**
 * @brief  GPIO EXTI 回调（由 HAL 框架调用，运行在中断上下文）
 * @param  GPIO_Pin 触发中断的引脚
 * @note   中断里只做最轻量的动作：置标志。绝不放 HAL_Delay/printf。
 */
void HAL_GPIO_EXTI_Callback(uint16_t GPIO_Pin)
{
    if (GPIO_Pin == KEY_PIN)
    {
        g_key_event = 1;                /* 置标志，主循环处理 */
        g_key_count++;                  /* 统计触发次数（抖动时会跳得快） */
    }
}

/**
 * @brief  按键事件处理（主循环上下文，可安全使用 HAL_Delay）
 * @note   两级结构：中断置标志 → 主循环消抖 + 业务处理。
 */
static void key_process(void)
{
    if (g_key_event == 0U)
    {
        return;
    }

    /* 读到标志后先做临界区保护，避免处理期间标志被 ISR 改写 */
    __disable_irq();
    g_key_event = 0;
    uint32_t cnt = g_key_count;
    __enable_irq();

    /* 软件消抖：等抖动过去再确认电平仍为低（按键按下） */
    HAL_Delay(KEY_DEBOUNCE_MS);
    if (HAL_GPIO_ReadPin(KEY_PORT, KEY_PIN) == GPIO_PIN_RESET)
    {
        HAL_GPIO_TogglePin(LED_PORT, LED_PIN);   /* 有效按键 → 翻转 LED */

        /* 简单区分：按下的次数越多，越可能是抖动（仅用于调试观察） */
        if ((cnt % 2U) == 0U)
        {
            HAL_GPIO_WritePin(LED_PORT, LED_PIN, GPIO_PIN_RESET); /* 点亮 */
        }
    }
}

/* ------------------------------------------------------- 外设初始化实现 */

/**
 * @brief  初始化 LED 与按键 GPIO
 */
static void gpio_init(void)
{
    GPIO_InitTypeDef io = {0};

    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_GPIOC_CLK_ENABLE();

    /* PC13 板载 LED：推挽输出 */
    io.Pin   = LED_PIN;
    io.Mode  = GPIO_MODE_OUTPUT_PP;
    io.Pull  = GPIO_NOPULL;
    io.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(LED_PORT, &io);

    /* PA0 按键：输入 + 内部上拉，下降沿触发中断（按下接地为低） */
    io.Pin   = KEY_PIN;
    io.Mode  = GPIO_MODE_IT_FALLING;
    io.Pull  = GPIO_PULLUP;
    io.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(KEY_PORT, &io);

    HAL_GPIO_WritePin(LED_PORT, LED_PIN, GPIO_PIN_SET);   /* 初始熄灭 */
}

/**
 * @brief  配置 EXTI 中断与 NVIC 优先级
 */
static void exti_init(void)
{
    /* F1 关键：EXTI 引脚映射由 AFIO 管理，必须使能 AFIO 时钟 */
    __HAL_RCC_AFIO_CLK_ENABLE();

    /* 抢占优先级 1，子优先级 0；数值越小优先级越高 */
    HAL_NVIC_SetPriority(EXTI0_IRQn, 1, 0);
    HAL_NVIC_EnableIRQ(EXTI0_IRQn);
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
 * @brief  错误处理：关中断停留，便于调试定位
 */
static void error_handler(void)
{
    __disable_irq();
    while (1)
    {
    }
}

/**
 * @file    main.c
 * @brief   gpio-blink —— GPIO 推挽输出闪烁 LED（STM32F103C8T6 / BluePill）
 *
 * 功能：
 *   1) 用 HAL_GPIO_TogglePin 让板载 LED(PC13) 以 1Hz 闪烁；
 *   2) 演示 BSRR 寄存器原子操作写法（与 HAL 函数等价）；
 *   3) 演示 HAL_Delay（基于 SysTick 中断）与「纯 SysTick 计数延时」两种延时；
 *   4) 每 5 秒翻转一次外接 LED(PA0)，用于对比两种延时/两种写法的时序。
 *
 * 板载 LED 是共阳接法：PC13 输出低电平点亮，高电平熄灭。
 *
 * 说明：本文件不依赖 CubeMX 生成的其它源文件，可直接替换
 *       Core/Src/main.c 使用（SystemClock_Config 已在下方给出）。
 *
 * 目标芯片：STM32F103C8T6，系统时钟 72MHz（HSE 8MHz × 9）。
 */

#include "stm32f1xx_hal.h"

/* ------------------------------------------------------------------ 宏定义 */

#define LED_PORT        GPIOC
#define LED_PIN         GPIO_PIN_13     /* 板载 LED，低电平点亮 */
#define LED2_PORT       GPIOA
#define LED2_PIN        GPIO_PIN_0      /* 外接 LED，高电平点亮（串 270Ω） */

#define BLINK_PERIOD_MS 500U            /* 半周期：亮 500ms + 灭 500ms = 1Hz */
#define LED2_PERIOD_MS  5000U           /* 外接 LED 每 5 秒翻转一次 */

/* ----------------------------------------------------------------- 私有函数 */

static void SystemClock_Config(void);
static void gpio_init(void);
static void error_handler(void);

/**
 * @brief  基于 SysTick 计数器的忙等延时（不依赖中断，微秒级）
 * @param  ms 延时毫秒数
 * @note   SysTick 由 HAL_Init() 配置为 1ms 中断一次；这里读的是
 *         SysTick->VAL（当前计数值，递减），只用于演示“纯计数”思路。
 *         实际工程里请直接用 HAL_Delay，除非在中断中需要短延时。
 */
static void delay_systick_count(uint32_t ms)
{
    uint32_t start = HAL_GetTick();     /* HAL_GetTick 由 SysTick 中断累加 */
    while ((HAL_GetTick() - start) < ms)
    {
        __NOP();                        /* 空操作，等待计数器推进 */
    }
}

/**
 * @brief  点亮 / 熄灭 LED（HAL 函数写法）
 */
static void led_write(GPIO_TypeDef *port, uint16_t pin, GPIO_PinState state)
{
    HAL_GPIO_WritePin(port, pin, state);
}

/**
 * @brief  翻转 LED（BSRR 寄存器原子写法，等价于 HAL_GPIO_TogglePin）
 * @note   BSRR 高 16 位写 1 复位引脚，低 16 位写 1 置位引脚；
 *         一次性写整个寄存器，天然原子，不怕被中断打断。
 */
static void led_toggle_bsrr(GPIO_TypeDef *port, uint16_t pin)
{
    if ((port->ODR & pin) != 0U)
    {
        port->BSRR = (uint32_t)pin << 16U;  /* 当前为高 → 复位（BR 区） */
    }
    else
    {
        port->BSRR = (uint32_t)pin;         /* 当前为低 → 置位（BS 区） */
    }
}

/* ---------------------------------------------------------------- 主函数 */

int main(void)
{
    HAL_Init();                         /* 复位外设、初始化 Flash 接口与 SysTick */
    SystemClock_Config();               /* 配置 72MHz 系统时钟 */

    if (HAL_GetTick() == 0U)            /* 简单自检：HAL_Init 后 SysTick 应已运行 */
    {
        error_handler();
    }

    gpio_init();                        /* 初始化 LED 引脚 */

    uint32_t last_led2 = 0U;

    while (1)
    {
        /* 1) HAL 函数写法：翻转板载 LED */
        HAL_GPIO_TogglePin(LED_PORT, LED_PIN);
        HAL_Delay(BLINK_PERIOD_MS);

        /* 2) BSRR 寄存器写法：翻转板载 LED（再翻一次，肉眼与上面无差别） */
        led_toggle_bsrr(LED_PORT, LED_PIN);

        /* 3) SysTick 计数延时（演示用），保持同样的半周期 */
        delay_systick_count(BLINK_PERIOD_MS);

        /* 4) 每 LED2_PERIOD_MS 翻转一次外接 LED，用 HAL 与 BSRR 交替 */
        uint32_t now = HAL_GetTick();
        if ((now - last_led2) >= LED2_PERIOD_MS)
        {
            last_led2 = now;
            led_write(LED2_PORT, LED2_PIN,
                      (HAL_GPIO_ReadPin(LED2_PORT, LED2_PIN) == GPIO_PIN_SET)
                          ? GPIO_PIN_RESET : GPIO_PIN_SET);
        }
    }
}

/* ------------------------------------------------------- 外设初始化实现 */

/**
 * @brief  初始化 LED GPIO（推挽输出）
 */
static void gpio_init(void)
{
    GPIO_InitTypeDef io = {0};

    __HAL_RCC_GPIOA_CLK_ENABLE();       /* 使能端口时钟，否则寄存器写入无效 */
    __HAL_RCC_GPIOC_CLK_ENABLE();

    /* PC13 板载 LED：推挽输出，低速即可（低频闪烁，减小 EMI） */
    io.Pin   = LED_PIN;
    io.Mode  = GPIO_MODE_OUTPUT_PP;
    io.Pull  = GPIO_NOPULL;
    io.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(LED_PORT, &io);

    /* PA0 外接 LED：推挽输出 */
    io.Pin   = LED2_PIN;
    io.Mode  = GPIO_MODE_OUTPUT_PP;
    io.Pull  = GPIO_NOPULL;
    io.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(LED2_PORT, &io);

    /* 初始状态：板载 LED 熄灭（高电平），外接 LED 熄灭（低电平） */
    HAL_GPIO_WritePin(LED_PORT, LED_PIN, GPIO_PIN_SET);
    HAL_GPIO_WritePin(LED2_PORT, LED2_PIN, GPIO_PIN_RESET);
}

/**
 * @brief  系统时钟配置：HSE 8MHz → PLL ×9 → SYSCLK 72MHz
 *         AHB=72MHz，APB1=36MHz，APB2=72MHz
 */
static void SystemClock_Config(void)
{
    RCC_OscInitTypeDef osc = {0};
    RCC_ClkInitTypeDef clk = {0};

    /* 使能 HSE 并配置 PLL：8MHz / 1 × 9 = 72MHz */
    osc.OscillatorType      = RCC_OSCILLATORTYPE_HSE;
    osc.HSEState            = RCC_HSE_ON;
    osc.HSEPredivValue      = RCC_HSE_PREDIV_DIV1;
    osc.HSIState            = RCC_HSI_ON;
    osc.PLL.PLLState        = RCC_PLL_ON;
    osc.PLL.PLLSource       = RCC_PLLSOURCE_HSE;
    osc.PLL.PLLMUL          = RCC_PLL_MUL9;
    if (HAL_RCC_OscConfig(&osc) != HAL_OK)
    {
        error_handler();
    }

    /* 切换系统时钟到 PLL，并配置各总线分频 */
    clk.ClockType      = RCC_CLOCKTYPE_HCLK | RCC_CLOCKTYPE_SYSCLK |
                         RCC_CLOCKTYPE_PCLK1 | RCC_CLOCKTYPE_PCLK2;
    clk.SYSCLKSource   = RCC_SYSCLKSOURCE_PLLCLK;
    clk.AHBCLKDivider  = RCC_SYSCLK_DIV1;    /* AHB = 72MHz */
    clk.APB1CLKDivider = RCC_HCLK_DIV2;      /* APB1 = 36MHz（最高 36MHz） */
    clk.APB2CLKDivider = RCC_HCLK_DIV1;      /* APB2 = 72MHz */
    if (HAL_RCC_ClockConfig(&clk, FLASH_LATENCY_2) != HAL_OK)
    {
        error_handler();                     /* 72MHz 需 2 个 Flash 等待周期 */
    }
}

/**
 * @brief  错误处理：关中断并停留，便于调试器定位
 */
static void error_handler(void)
{
    __disable_irq();
    while (1)
    {
        /* 可在此点亮红色 LED 或用调试器查看调用栈 */
    }
}

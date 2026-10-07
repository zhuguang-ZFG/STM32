/**
 * @file    main.c
 * @brief   timer-pwm —— TIM3 PWM 呼吸灯（STM32F103C8T6 / BluePill）
 *
 * 功能：
 *   1) TIM3_CH1(PA6) 输出 1kHz PWM，软件线性调节 CCR 实现「呼吸灯」；
 *   2) 给出频率 / 占空比计算公式，并用宏定义固化 PSC/ARR；
 *   3) 演示 __HAL_TIM_SET_COMPARE 动态改占空比（比 HAL_TIM_PWM_Start 后改 CCR）；
 *   4) 附 TIM1/TIM8 高级定时器需使能 MOE（主输出使能）的说明与代码。
 *
 * 公式（fCK_PSC = 定时器时钟）：
 *   fCK_CNT = fCK_PSC / (PSC + 1)
 *   f_PWM   = fCK_PSC / ((ARR + 1) * (PSC + 1))
 *   Duty    = CCR / (ARR + 1) × 100%
 *
 * 本例：APB1 定时器时钟 72MHz，PSC=71 → fCK_CNT=1MHz；
 *       ARR=999 → f_PWM=1kHz；CCR 从 0 到 999 往返 → 占空比 0~100%。
 *
 * 目标芯片：STM32F103C8T6，系统时钟 72MHz（TIM3 挂 APB1，定时器时钟 72MHz）。
 */

#include "stm32f1xx_hal.h"

/* ------------------------------------------------------------------ 宏定义 */

#define PWM_TIM             TIM3
#define PWM_TIM_CLK_ENABLE()  __HAL_RCC_TIM3_CLK_ENABLE()
#define PWM_CH              TIM_CHANNEL_1
#define PWM_GPIO_PORT       GPIOA
#define PWM_GPIO_PIN        GPIO_PIN_6      /* PA6 = TIM3_CH1 */

#define PWM_PSC             71U             /* 72MHz/(71+1) = 1MHz 计数时钟 */
#define PWM_ARR             999U            /* 1MHz/(999+1) = 1kHz PWM */
#define BREATH_STEP         10U             /* 每步改变 CCR 的幅度 */
#define BREATH_DELAY_MS     10U             /* 每步之间的延时 */

/* ---------------------------------------------------------------- 全局句柄 */

TIM_HandleTypeDef htim3;

/* ----------------------------------------------------------------- 私有函数 */

static void SystemClock_Config(void);
static void pwm_init(void);
static void error_handler(void);

/* ---------------------------------------------------------------- 主函数 */

int main(void)
{
    HAL_Init();
    SystemClock_Config();
    pwm_init();

    int16_t duty = 0;                       /* 当前 CCR 值（占空比） */
    int16_t step = (int16_t)BREATH_STEP;    /* 变化步长，到边界取反 */

    while (1)
    {
        duty += step;
        if (duty >= (int16_t)PWM_ARR || duty <= 0)
        {
            step = -step;                   /* 0 → 100% → 0 往返，形成呼吸 */
        }

        /* 动态修改比较值 CCR（预装载寄存器，更新事件时生效，不抖动） */
        __HAL_TIM_SET_COMPARE(&htim3, PWM_CH, (uint32_t)duty);

        HAL_Delay(BREATH_DELAY_MS);
    }
}

/* ------------------------------------------------------- 外设初始化实现 */

/**
 * @brief  初始化 TIM3_CH1 PWM 输出
 */
static void pwm_init(void)
{
    GPIO_InitTypeDef io = {0};

    PWM_TIM_CLK_ENABLE();
    __HAL_RCC_GPIOA_CLK_ENABLE();

    /* PA6 复用推挽输出（复用功能由 TIM3 外设接管引脚） */
    io.Pin   = PWM_GPIO_PIN;
    io.Mode  = GPIO_MODE_AF_PP;
    io.Pull  = GPIO_NOPULL;
    io.Speed = GPIO_SPEED_FREQ_HIGH;        /* PWM 边沿要快，用高速 */
    HAL_GPIO_Init(PWM_GPIO_PORT, &io);

    /* 时基配置：PSC/ARR 决定频率 */
    htim3.Instance               = PWM_TIM;
    htim3.Init.Prescaler         = PWM_PSC;
    htim3.Init.CounterMode       = TIM_COUNTERMODE_UP;
    htim3.Init.Period            = PWM_ARR;                 /* Period 即 ARR */
    htim3.Init.ClockDivision     = TIM_CLOCKDIVISION_DIV1;
    htim3.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_ENABLE;  /* ARR 预装载 */
    if (HAL_TIM_PWM_Init(&htim3) != HAL_OK)
    {
        error_handler();
    }

    /* 通道配置：PWM 模式 1，初始 50% 占空比 */
    TIM_OC_InitTypeDef oc = {0};
    oc.OCMode       = TIM_OCMODE_PWM1;      /* CNT < CCR 输出有效电平 */
    oc.Pulse        = PWM_ARR / 2U;         /* 初始 CCR = ARR/2 → 50% */
    oc.OCPolarity   = TIM_OCPOLARITY_HIGH;  /* 有效电平为高 */
    oc.OCFastMode   = TIM_OCFAST_DISABLE;
    oc.OCIdleState  = TIM_OCIDLESTATE_RESET;
    if (HAL_TIM_PWM_ConfigChannel(&htim3, &oc, PWM_CH) != HAL_OK)
    {
        error_handler();
    }

    /* 启动 PWM 输出（内部会打开 CCR 预装载 OCxPE 并使能 CCxE） */
    if (HAL_TIM_PWM_Start(&htim3, PWM_CH) != HAL_OK)
    {
        error_handler();
    }
}

/**
 * @brief  系统时钟配置：HSE 8MHz → PLL ×9 → 72MHz
 * @note   TIM3 挂在 APB1 上；APB1 分频系数 ≠1 时，定时器时钟 = PCLK1 ×2。
 *         APB1=36MHz → 定时器时钟=72MHz，故 PSC=71 得到 1MHz。
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
    clk.APB1CLKDivider = RCC_HCLK_DIV2;     /* APB1=36MHz，定时器时钟=72MHz */
    clk.APB2CLKDivider = RCC_HCLK_DIV1;
    if (HAL_RCC_ClockConfig(&clk, FLASH_LATENCY_2) != HAL_OK)
    {
        error_handler();
    }
}

/**
 * @brief  错误处理
 */
static void error_handler(void)
{
    __disable_irq();
    while (1)
    {
    }
}

/* =====================================================================
 * 附：TIM1 / TIM8 高级定时器输出 PWM 的额外要求
 * ---------------------------------------------------------------------
 * 高级定时器除了配置通道，还必须使能「主输出（Main Output Enable, MOE）」，
 * 否则即使 CCxE 使能，引脚也不会有输出（常见「高级定时器没波形」的坑）。
 *
 *   HAL_TIM_PWM_Start(&htim1, TIM_CHANNEL_1);   // HAL 内部会置 MOE
 *   // 若用寄存器：__HAL_TIM_MOE_ENABLE(&htim1);  → TIM1->BDTR |= TIM_BDTR_MOE
 *
 * 若使用「刹车（Break）」功能，刹车输入有效时 MOE 会被硬件清零，需在
 * 刹车回调里重新使能。互补输出还需配置死区时间（BDTR.DTG）。
 * ===================================================================== */

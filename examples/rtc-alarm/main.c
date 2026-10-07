/**
 * @file    main.c
 * @brief   rtc-alarm —— RTC 闹钟 + 唤醒中断 + 时间戳记录（STM32F103C8T6 / BluePill）
 *
 * 功能：
 *   1) 配置 LSE(32.768kHz) 作为 RTC 时钟源，解锁备份域并初始化 RTC；
 *   2) 用 BKP_DR1 保存「魔法值」，判断是否首次上电，避免每次复位都重设时间；
 *   3) 设置周期闹钟（每 10 秒触发一次），闹钟中断作为「唤醒源」；
 *   4) 主循环进入 STOP 低功耗模式，闹钟中断把 MCU 唤醒；
 *   5) 每次唤醒记录一条时间戳到环形日志，并翻转板载 LED 指示。
 *
 * 硬件：PC14/PC15 焊 32.768kHz 晶振（+负载电容），VBAT 接纽扣电池可掉电走时。
 *
 * 目标芯片：STM32F103C8T6，系统时钟 72MHz。
 */

#include "stm32f1xx_hal.h"

/* ------------------------------------------------------------------ 宏定义 */

#define RTC_MAGIC           0xA5A5U         /* 备份寄存器魔法值，标识已初始化 */
#define RTC_BKP_MAGIC_REG   RTC_BKP_DR1     /* 存放魔法值的备份寄存器 */
#define ALARM_PERIOD_S      10U             /* 闹钟周期（秒） */

#define LED_PORT            GPIOC
#define LED_PIN             GPIO_PIN_13     /* 板载 LED，低电平点亮 */

#define LOG_DEPTH           16U             /* 时间戳日志深度 */

/* ---------------------------------------------------------------- 全局句柄 */

RTC_HandleTypeDef hrtc;

/* 时间戳日志（环形） */
typedef struct
{
    RTC_TimeTypeDef time;
    RTC_DateTypeDef date;
} rtc_stamp_t;

static rtc_stamp_t g_log[LOG_DEPTH];
static uint8_t     g_log_idx   = 0U;
static uint8_t     g_log_count = 0U;

static volatile uint8_t g_alarm_flag = 0U;  /* 闹钟中断置位，主循环消费 */

/* ----------------------------------------------------------------- 私有函数 */

static void SystemClock_Config(void);
static void rtc_init(void);
static void rtc_set_alarm(uint32_t seconds_from_now);
static void rtc_record_stamp(void);
static void error_handler(void);

/* ---------------------------------------------------------------- 主函数 */

int main(void)
{
    HAL_Init();
    SystemClock_Config();

    /* LED 输出 */
    GPIO_InitTypeDef io = {0};
    __HAL_RCC_GPIOC_CLK_ENABLE();
    io.Pin = LED_PIN; io.Mode = GPIO_MODE_OUTPUT_PP;
    io.Pull = GPIO_NOPULL; io.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(LED_PORT, &io);
    HAL_GPIO_WritePin(LED_PORT, LED_PIN, GPIO_PIN_SET);     /* 熄灭 */

    rtc_init();

    while (1)
    {
        /* 取当前时间，设置「10 秒后」的闹钟 */
        rtc_set_alarm(ALARM_PERIOD_S);

        /* 进入 STOP 模式：CPU 停摆，等待闹钟中断唤醒（典型功耗 µA 级） */
        HAL_SuspendTick();                          /* 挂起 SysTick，避免其唤醒 */
        HAL_PWR_EnterSTOPMode(PWR_LOWPOWERREGULATOR_ON, PWR_STOPENTRY_WFI);
        /* —— 被闹钟唤醒后从这里继续 —— */
        HAL_ResumeTick();

        /* STOP 唤醒后系统时钟会切回 HSI，需重新配置回 72MHz */
        SystemClock_Config();

        if (g_alarm_flag)
        {
            g_alarm_flag = 0U;
            rtc_record_stamp();                     /* 记录一条时间戳 */
            HAL_GPIO_TogglePin(LED_PORT, LED_PIN);  /* LED 翻转指示 */
        }
    }
}

/* ------------------------------------------------------- RTC 初始化实现 */

/**
 * @brief  初始化 RTC（LSE 时钟源 + 备份域解锁 + 首次上电设时间 + 闹钟中断）
 */
static void rtc_init(void)
{
    RCC_OscInitTypeDef       osc  = {0};
    RCC_PeriphCLKInitTypeDef pclk = {0};

    /* 使能 PWR、BKP 时钟并解锁备份域（F1 写备份寄存器/RTC 前必须解锁） */
    __HAL_RCC_PWR_CLK_ENABLE();
    __HAL_RCC_BKP_CLK_ENABLE();
    HAL_PWR_EnableBkUpAccess();

    /* 配置 LSE：外部 32.768kHz 晶振（PC14/PC15） */
    osc.OscillatorType = RCC_OSCILLATORTYPE_LSE;
    osc.LSEState       = RCC_LSE_ON;
    if (HAL_RCC_OscConfig(&osc) != HAL_OK)
    {
        error_handler();                /* LSE 不起振：检查晶振与负载电容 */
    }

    /* 选择 RTC 时钟源为 LSE */
    pclk.PeriphClockSelection = RCC_PERIPHCLK_RTC;
    pclk.RtcClockSelection    = RCC_RTCCLKSOURCE_LSE;
    if (HAL_RCCEx_PeriphCLKConfig(&pclk) != HAL_OK)
    {
        error_handler();
    }

    __HAL_RCC_RTC_ENABLE();

    /* RTC 配置：F1 为 32 位秒计数器，预分频到 1Hz */
    hrtc.Instance          = RTC;
    hrtc.Init.AsynchPrediv = RTC_AUTO_1_SECOND;   /* 自动分频到 1 秒 */
    hrtc.Init.OutPut       = RTC_OUTPUTSOURCE_NONE;
    if (HAL_RTC_Init(&hrtc) != HAL_OK)
    {
        error_handler();
    }

    /* 首次上电（备份寄存器无魔法值）才设置初始时间，避免复位后时间被重置 */
    if (HAL_RTCEx_BKUPRead(&hrtc, RTC_BKP_MAGIC_REG) != RTC_MAGIC)
    {
        RTC_TimeTypeDef t = {0};
        RTC_DateTypeDef d = {0};
        t.Hours = 12U; t.Minutes = 0U; t.Seconds = 0U;
        d.Year = 26U; d.Month = RTC_MONTH_JANUARY;
        d.Date = 7U;  d.WeekDay = RTC_WEEKDAY_WEDNESDAY;

        (void)HAL_RTC_SetTime(&hrtc, &t, RTC_FORMAT_BIN);
        (void)HAL_RTC_SetDate(&hrtc, &d, RTC_FORMAT_BIN);
        HAL_RTCEx_BKUPWrite(&hrtc, RTC_BKP_MAGIC_REG, RTC_MAGIC);
    }

    /* 闹钟中断：作为 STOP 模式的唤醒源（F1 经 EXTI17 连到 NVIC） */
    HAL_NVIC_SetPriority(RTCAlarm_IRQn, 0U, 0U);
    HAL_NVIC_EnableIRQ(RTCAlarm_IRQn);
}

/**
 * @brief  设置「当前时间 + seconds_from_now 秒」的闹钟
 * @param  seconds_from_now 从现在起多少秒后触发
 * @note   屏蔽日期字段（RTC_ALARMMASK_DATEWEEKDAY），比较时/分/秒。
 */
static void rtc_set_alarm(uint32_t seconds_from_now)
{
    RTC_TimeTypeDef t = {0};
    RTC_DateTypeDef d = {0};
    (void)HAL_RTC_GetTime(&hrtc, &t, RTC_FORMAT_BIN);
    (void)HAL_RTC_GetDate(&hrtc, &d, RTC_FORMAT_BIN);   /* 读日期会锁存时间寄存器 */

    uint32_t secs = (uint32_t)t.Hours * 3600U
                  + (uint32_t)t.Minutes * 60U
                  + (uint32_t)t.Seconds;
    secs = (secs + seconds_from_now) % 86400U;          /* 当天内取模 */

    RTC_AlarmTypeDef alarm = {0};
    alarm.AlarmTime.Hours   = (uint8_t)(secs / 3600U);
    alarm.AlarmTime.Minutes = (uint8_t)((secs % 3600U) / 60U);
    alarm.AlarmTime.Seconds = (uint8_t)(secs % 60U);
    alarm.AlarmMask         = RTC_ALARMMASK_DATEWEEKDAY;  /* 忽略日期，每天匹配 */

    if (HAL_RTC_SetAlarm_IT(&hrtc, &alarm, RTC_FORMAT_BIN) != HAL_OK)
    {
        error_handler();
    }
}

/**
 * @brief  记录一条时间戳到环形日志
 */
static void rtc_record_stamp(void)
{
    (void)HAL_RTC_GetTime(&hrtc, &g_log[g_log_idx].time, RTC_FORMAT_BIN);
    (void)HAL_RTC_GetDate(&hrtc, &g_log[g_log_idx].date, RTC_FORMAT_BIN);

    g_log_idx = (uint8_t)((g_log_idx + 1U) % LOG_DEPTH);
    if (g_log_count < LOG_DEPTH)
    {
        g_log_count++;
    }
}

/* ------------------------------------------------------------ 中断处理 */

/**
 * @brief  闹钟中断向量（F1：RTC 闹钟经 EXTI17）
 */
void RTCAlarm_IRQHandler(void)
{
    HAL_RTC_AlarmIRQHandler(&hrtc);
}

/**
 * @brief  闹钟 A 事件回调（中断上下文，只置标志）
 */
void HAL_RTC_AlarmAEventCallback(RTC_HandleTypeDef *hrtc_arg)
{
    (void)hrtc_arg;
    g_alarm_flag = 1U;
}

/**
 * @brief  系统时钟配置：HSE 8MHz → PLL ×9 → 72MHz
 * @note   STOP 唤醒后需重新调用本函数恢复 72MHz 主频。
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

static void error_handler(void)
{
    __disable_irq();
    while (1)
    {
    }
}


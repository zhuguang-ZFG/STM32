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

/**
 * main.c —— 03-ledc-fade：timer 定频率/分辨率，channel 定 GPIO/占空比
 *
 * 教学点：S3 的 LEDC 只有低速模式、8 通道、14 位定时器位宽
 * （soc_caps.h: SOC_LEDC_CHANNEL_NUM=8, SOC_LEDC_TIMER_BIT_WIDTH=14）——
 * 不能套经典 ESP32 的 16 通道/高速模式结论。
 *
 * 分工：timer 管"多快、多细"（频率 + 分辨率），channel 管"从哪个脚出、占空比多少"。
 * fade（渐变）本质是硬件/驱动按步进改比较值——CPU 不逐点干预。
 *
 * 板卡：立创·实战派 ESP32-S3；PWM 从 GPIO10（多功能扩展接口）输出。
 */

#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/ledc.h"
#include "esp_log.h"
#include "soc/soc_caps.h"

static const char *TAG = "ledc-fade";

#define PWM_GPIO    GPIO_NUM_10
#define PWM_FREQ    5000
#define PWM_RES     LEDC_TIMER_10_BIT      /* 占空比范围 0..1023 */
#define PWM_MAX     ((1 << 10) - 1)
#define FADE_MS     2000

void app_main(void)
{
    ESP_LOGI(TAG, "S3 LEDC: %d channels, %d-bit timer, low-speed only",
             SOC_LEDC_CHANNEL_NUM, SOC_LEDC_TIMER_BIT_WIDTH);

    /* timer：定频率与分辨率（分辨率越高，同频率下可调步进越细） */
    ledc_timer_config_t timer = {
        .speed_mode      = LEDC_LOW_SPEED_MODE,
        .duty_resolution = PWM_RES,
        .timer_num       = LEDC_TIMER_0,
        .freq_hz         = PWM_FREQ,
        .clk_cfg         = LEDC_AUTO_CLK,
    };
    ESP_ERROR_CHECK(ledc_timer_config(&timer));

    /* channel：定 GPIO 与初始占空比，绑到 timer 上 */
    ledc_channel_config_t ch = {
        .gpio_num   = PWM_GPIO,
        .speed_mode = LEDC_LOW_SPEED_MODE,
        .channel    = LEDC_CHANNEL_0,
        .timer_sel  = LEDC_TIMER_0,
        .duty       = 0,
        .hpoint     = 0,
    };
    ESP_ERROR_CHECK(ledc_channel_config(&ch));

    uint32_t actual = ledc_get_freq(LEDC_LOW_SPEED_MODE, LEDC_TIMER_0);
    ESP_LOGI(TAG, "requested %d Hz, actual %lu Hz (timer clock / divider rounding)",
             PWM_FREQ, (unsigned long)actual);

    /* fade：装好渐变引擎，然后告诉它目标占空比和用时 */
    ESP_ERROR_CHECK(ledc_fade_func_install(0));

    while (true) {
        /* 0 → 满占空比，2 秒渐变完；fade 期间 CPU 去干别的 */
        ESP_ERROR_CHECK(ledc_set_fade_with_time(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0,
                                                PWM_MAX, FADE_MS));
        ESP_ERROR_CHECK(ledc_fade_start(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0,
                                        LEDC_FADE_NO_WAIT));
        ESP_LOGI(TAG, "fade up over %d ms", FADE_MS);
        vTaskDelay(pdMS_TO_TICKS(FADE_MS + 200));

        ESP_ERROR_CHECK(ledc_set_fade_with_time(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0,
                                                0, FADE_MS));
        ESP_ERROR_CHECK(ledc_fade_start(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0,
                                        LEDC_FADE_NO_WAIT));
        ESP_LOGI(TAG, "fade down over %d ms", FADE_MS);
        vTaskDelay(pdMS_TO_TICKS(FADE_MS + 200));
    }
}
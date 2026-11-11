/**
 * main.c —— 01-gpio-matrix：同一个外设信号，两个焊盘之间"搬线"
 *
 * 教学点：ESP32-S3 的外设信号不钉死在引脚上——
 *   外设信号 → GPIO 交换矩阵（GPIO Matrix）→ 有效焊盘
 *   （部分信号还能走 IO_MUX 直达，更快但只能到固定脚）
 *
 * 本工程只在扩展口 GPIO10/11 之间切换，每次先断开旧输出。
 * N16R8 模组占用的 GPIO35/36/37 只作资料核对，不输出测试信号。
 *
 * 板卡：立创·实战派 ESP32-S3（ESP32-S3-WROOM-1-N16R8）。
 * 引脚依据：立创 wiki——多功能扩展接口引出 GPIO10/GPIO11；
 *           IO35/36/37 被八线 PSRAM 占用，不可用。
 */

#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/ledc.h"
#include "driver/gpio.h"
#include "esp_log.h"
#include "esp_check.h"
#include "soc/soc_caps.h"

static const char *TAG = "gpio-matrix";

#define PWM_FREQ_HZ   1000
#define PWM_RES_BITS  LEDC_TIMER_10_BIT
#define PWM_DUTY      512          /* 50% */

/* 立创实战派多功能扩展接口引出的两个脚 */
#define PAD_A GPIO_NUM_10
#define PAD_B GPIO_NUM_11

static void ledc_setup(void)
{
    ledc_timer_config_t timer = {
        .speed_mode      = LEDC_LOW_SPEED_MODE,   /* S3 只有低速模式 */
        .duty_resolution = PWM_RES_BITS,
        .timer_num       = LEDC_TIMER_0,
        .freq_hz         = PWM_FREQ_HZ,
        .clk_cfg         = LEDC_AUTO_CLK,
    };
    ESP_ERROR_CHECK(ledc_timer_config(&timer));

    ledc_channel_config_t ch = {
        .gpio_num   = PAD_A,
        .speed_mode = LEDC_LOW_SPEED_MODE,
        .channel    = LEDC_CHANNEL_0,
        .timer_sel  = LEDC_TIMER_0,
        .duty       = PWM_DUTY,
        .hpoint     = 0,
    };
    ESP_ERROR_CHECK(ledc_channel_config(&ch));
}

void app_main(void)
{
    ESP_LOGI(TAG, "LEDC channels on S3: %d, timer bit width: %d",
             SOC_LEDC_CHANNEL_NUM, SOC_LEDC_TIMER_BIT_WIDTH);

    ledc_setup();
    ESP_LOGI(TAG, "PWM on GPIO%d first", PAD_A);
    vTaskDelay(pdMS_TO_TICKS(3000));

    /* 同一信号换脚：ledc_set_pin 内部走 GPIO Matrix 重新路由 */
    ESP_ERROR_CHECK(gpio_reset_pin(PAD_A));
    ESP_ERROR_CHECK(ledc_set_pin(PAD_B, LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0));
    ESP_LOGI(TAG, "same PWM re-routed to GPIO%d", PAD_B);
    vTaskDelay(pdMS_TO_TICKS(3000));

    /* 回 GPIO10，循环演示 */
    while (true) {
        ESP_ERROR_CHECK(gpio_reset_pin(PAD_B));
        ESP_ERROR_CHECK(ledc_set_pin(PAD_A, LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0));
        ESP_LOGI(TAG, "PWM on GPIO%d", PAD_A);
        vTaskDelay(pdMS_TO_TICKS(3000));
        ESP_ERROR_CHECK(gpio_reset_pin(PAD_A));
        ESP_ERROR_CHECK(ledc_set_pin(PAD_B, LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0));
        ESP_LOGI(TAG, "PWM on GPIO%d", PAD_B);
        vTaskDelay(pdMS_TO_TICKS(3000));
    }
}
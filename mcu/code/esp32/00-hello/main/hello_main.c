/**
 * hello_main.c —— ESP32-S3 的 Hello World（逐行注释版）
 *
 * 与 STM32 裸机最大的不同：你一出生就在 FreeRTOS 里。
 * app_main 本身就是 IDF 启动代码创建的一个任务（main task），
 * 它返回后任务销毁，但系统里还有一堆任务在跑（IDF/协议栈自己的）。
 */

#include <stdio.h>
#include "freertos/FreeRTOS.h"   /* vTaskDelay、pdMS_TO_TICKS */
#include "freertos/task.h"
#include "esp_chip_info.h"       /* esp_chip_info：读芯片型号/核数/特性 */
#include "esp_flash.h"           /* esp_flash_get_size：读外挂 Flash 容量 */
#include "esp_system.h"          /* esp_restart */
#include "esp_heap_caps.h"       /* heap_caps_get_free_size：看剩余内存 */

void app_main(void)
{
    /* ---- 1. 你是谁：芯片身份证 ---- */
    esp_chip_info_t chip_info;
    uint32_t flash_size = 0;
    esp_chip_info(&chip_info);

    printf("Hello! 这颗芯片是 ESP32-%s，%d 核，%d MB 外挂 Flash\n",
           CONFIG_IDF_TARGET_ESP32S3 ? "S3" : "?",
           chip_info.cores,
           (int)(flash_size / (1024 * 1024)));

    /* 特性位：Wi-Fi / 蓝牙经典 / BLE，按位与出来 */
    printf("无线能力:%s%s%s\n",
           (chip_info.features & CHIP_FEATURE_WIFI_BGN) ? " Wi-Fi" : "",
           (chip_info.features & CHIP_FEATURE_BT) ? " BT经典" : "",
           (chip_info.features & CHIP_FEATURE_BLE) ? " BLE" : "");

    /* ---- 2. 你有多少家底：内存 ---- */
    printf("SRAM 剩余：%u 字节；PSRAM 剩余：%u 字节\n",
           heap_caps_get_free_size(MALLOC_CAP_INTERNAL),
           heap_caps_get_free_size(MALLOC_CAP_SPIRAM));

    /* ---- 3. 呼吸十次，然后重启（演示 vTaskDelay 与 esp_restart） ---- */
    for (int i = 10; i >= 0; i--) {
        printf("%d 秒后重启……\n", i);
        vTaskDelay(pdMS_TO_TICKS(1000));  /* 让出 CPU，不是死等——RTOS 的基本礼仪 */
    }

    printf("重启！\n");
    fflush(stdout);
    esp_restart();
}

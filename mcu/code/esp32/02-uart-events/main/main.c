/**
 * main.c —— 02-uart-events：事件驱动的串口接收
 *
 * 教学点：ESP-IDF 的 UART 驱动把"字节"和"事件"分成两条路——
 *   字节：FIFO（SOC_UART_FIFO_LEN=128）→ ring buffer → 你 uart_read_bytes 取走；
 *   事件：驱动把"收到数据/溢出/帧错误"包装成 uart_event_t，经队列交给你的任务。
 *
 * 所以"事件"不是数据本身——UART_DATA 事件的 size 只是元数据（"现在有多少字节可读"），
 * 真正的字节要你自己去读。这与 STM32 侧 IDLE+DMA 的判帧思路是同一招：
 *   硬件只管搬运，帧边界由"空闲/超时"这类事件告诉你。
 *
 * 板卡：立创·实战派 ESP32-S3。UART1 经 GPIO Matrix 路由到 GPIO10(TX)/GPIO11(RX)，
 * 即多功能扩展接口的两个脚（立创 wiki 核实）。
 */

#include <stdio.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/uart.h"
#include "driver/gpio.h"
#include "esp_log.h"
#include "soc/soc_caps.h"

static const char *TAG = "uart-events";

#define UART_PORT   UART_NUM_1
#define TX_PIN      GPIO_NUM_10
#define RX_PIN      GPIO_NUM_11
#define RX_BUF      256
#define QUEUE_LEN   20

static QueueHandle_t s_uart_queue;

static const char *event_name(uart_event_type_t t)
{
    switch (t) {
    case UART_DATA:          return "UART_DATA";
    case UART_BREAK:         return "UART_BREAK";
    case UART_BUFFER_FULL:   return "UART_BUFFER_FULL";
    case UART_FIFO_OVF:      return "UART_FIFO_OVF";
    case UART_FRAME_ERR:     return "UART_FRAME_ERR";
    case UART_PARITY_ERR:    return "UART_PARITY_ERR";
    default:                 return "OTHER";
    }
}

static void uart_event_task(void *arg)
{
    uart_event_t evt;
    uint8_t buf[RX_BUF];

    for (;;) {
        if (!xQueueReceive(s_uart_queue, &evt, portMAX_DELAY)) {
            continue;
        }

        switch (evt.type) {
        case UART_DATA:
            /* 事件的 size/timeout_flag 是元数据；字节要自己读 */
            {
                size_t remaining = evt.size;
                while (remaining > 0) {
                    const size_t take = remaining < sizeof(buf) ? remaining : sizeof(buf);
                    int len = uart_read_bytes(UART_PORT, buf, take, pdMS_TO_TICKS(20));
                    if (len <= 0) {
                        ESP_LOGW(TAG, "event payload unavailable: read=%d", len);
                        break;
                    }
                    if (uart_write_bytes(UART_PORT, buf, (size_t)len) < 0) {
                        ESP_LOGE(TAG, "echo failed");
                        break;
                    }
                    remaining -= (size_t)len;
                }
                ESP_LOGI(TAG, "DATA size=%u timeout=%d unread=%u",
                         (unsigned)evt.size, (int)evt.timeout_flag, (unsigned)remaining);
            }
            break;

        case UART_FIFO_OVF:
        case UART_BUFFER_FULL:
            /* FIFO 满/环形缓冲满 = 你读得太慢，数据已经在丢 */
            ESP_LOGW(TAG, "%s: RX 溢出，flush 后继续", event_name(evt.type));
            uart_flush_input(UART_PORT);
            xQueueReset(s_uart_queue);
            break;

        default:
            ESP_LOGI(TAG, "event %s", event_name(evt.type));
            break;
        }
    }
}

void app_main(void)
{
    ESP_LOGI(TAG, "S3 UART hardware FIFO length: %d bytes", SOC_UART_FIFO_LEN);

    uart_config_t cfg = {
        .baud_rate  = 115200,
        .data_bits  = UART_DATA_8_BITS,
        .parity     = UART_PARITY_DISABLE,
        .stop_bits  = UART_STOP_BITS_1,
        .flow_ctrl  = UART_HW_FLOWCTRL_DISABLE,
        .source_clk = UART_SCLK_DEFAULT,
    };

    /* 装驱动 = 建 FIFO→ring 通路 + 事件队列；事件队列的句柄交给我们 */
    ESP_ERROR_CHECK(uart_driver_install(UART_PORT, RX_BUF, 0, QUEUE_LEN, &s_uart_queue, 0));
    ESP_ERROR_CHECK(uart_param_config(UART_PORT, &cfg));
    /* 引脚经 GPIO Matrix 路由：同一外设信号换脚只是改这两个数 */
    ESP_ERROR_CHECK(uart_set_pin(UART_PORT, TX_PIN, RX_PIN,
                                 UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE));

    ESP_ERROR_CHECK(xTaskCreate(uart_event_task, "uart_events", 3072, NULL, 12, NULL)
                    == pdPASS ? ESP_OK : ESP_ERR_NO_MEM);
    ESP_LOGI(TAG, "UART%d on TX=GPIO%d RX=GPIO%d @115200 8N1 —— 发数据过来试试",
             UART_PORT, TX_PIN, RX_PIN);
}
/**
 * framed_protocol_main.c —— 06-framed-protocol：UART1 二进制帧协议
 *
 * 与 F407 侧同一公共 codec（code/common/reliability 源文件复用，不复制）。
 * 关键差异：S3 的 UART 驱动是"事件 + 环形缓冲"双通道——
 *   - 事件可能丢：驱动事件队列满时只写日志（uart.c:1321-1325），无公共精确计数；
 *   - 所以任务不能只靠 UART_DATA：等待事件 ≤5ms 后，每轮都周期取数兜底。
 * 帧边界由协议定界（COBS + 0x00）；IDLE/事件不是帧边界（同 02-uart-events 的结论）。
 *
 * 接线（USB-TTL ↔ 板，立创·实战派 S3 多功能扩展口，wiki 核实）：
 *   TTL TX → GPIO11 (UART1 RX)
 *   TTL RX → GPIO10 (UART1 TX)
 *   GND → GND，3.3V 电平共地
 */

#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include "driver/gpio.h"    /* GPIO_NUM_* */
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/uart.h"
#include "esp_timer.h"
#include "esp_system.h"      /* esp_reset_reason()  esp_system.h:85 */
#include "esp_log.h"

#include "service.h"         /* 公共模块：PRIV_INCLUDE_DIRS 已加进组件 */

static const char *TAG = "framed-protocol";

#define UART_PORT    UART_NUM_1
#define TX_PIN       GPIO_NUM_10
#define RX_PIN       GPIO_NUM_11
#define RX_RING      1024    /* 设计预算：见 design.md §4 */
#define EVENT_QUEUE  20
#define READ_CHUNK   128     /* 每轮取数分块上限的一部分 */
#define MAX_PER_ROUND 512    /* 每轮服务量上限：饿死 TX 的保护 */

static QueueHandle_t s_uart_queue;
static device_service_t s_service;

#if CONFIG_RELIABILITY_TEST_FAULTS
/* 故障注入（仅测试构建）：必须由显式 TEST_FAULT 命令触发 */
static volatile uint8_t s_pause_feed;   /* fault=1：喂帧/解析全停 */
static uint8_t s_pending_kind;
static uint32_t s_fault_at;
static volatile uint8_t s_pause_tx;     /* fault=2：TX 步进停，RX 照常 */
static void fault_inject(void *user, uint8_t kind, uint8_t id)
{
    (void)user; (void)id;
    s_pending_kind=kind; s_fault_at=(uint32_t)(esp_timer_get_time()/1000)+200U;
    ESP_LOGW(TAG, "FAULT INJECTED: kind=%u", kind);
}
#endif

/** 毫秒时间：esp_timer 微秒截成 uint32 毫秒（约 49.7 天回绕，公共模块已处理） */
static inline uint32_t now_ms(void)
{
    return (uint32_t)(esp_timer_get_time() / 1000);
}

/** TX 写函数：uart_tx_chars 返回实际接受的字节数（可能 0/部分） */
static size_t uart_write_some(void *user, const uint8_t *p, size_t n)
{
    (void)user;
    int sent = uart_tx_chars(UART_PORT, (const char *)p, (uint32_t)n);
    return sent > 0 ? (size_t)sent : 0;
}

static void uart_task(void *arg)
{
    uart_event_t evt;
    uint8_t buf[READ_CHUNK];

    for (;;) {
        bool serviced = false;

        /* 1) 等事件，最多 5ms：有事件处理事件，没事件也照常往下走 */
        if (xQueueReceive(s_uart_queue, &evt, pdMS_TO_TICKS(5)) == pdTRUE) {
            serviced = true;
            switch (evt.type) {
            case UART_DATA:
                /* size 是元数据；字节统一在下面的周期取数里读 */
                break;
            case UART_FIFO_OVF:
            case UART_BUFFER_FULL:
            case UART_FRAME_ERR:
            case UART_PARITY_ERR:
            case UART_BREAK:
                /* 已报告的错误：残段不可信 → flush + 清积压 + 解析器失步 */
                uart_flush_input(UART_PORT);
                xQueueReset(s_uart_queue);
                protocol_rx_loss(&s_service.rx);
                ESP_LOGW(TAG, "uart error %d -> parser DISCARD", evt.type);
                break;
            default:
                break;
            }
        }

#if CONFIG_RELIABILITY_TEST_FAULTS
        if (s_pending_kind && (int32_t)(now_ms()-s_fault_at)>=0) {
            if(s_pending_kind==1) s_pause_feed=1; else s_pause_tx=1;
            s_pending_kind=0;
        }
#else
        ;
#endif

        /* 2) 周期取数：不管事件来没来都看一眼驱动缓冲（通知丢失的兜底） */
        size_t drained = 0;
        for (;;) {
#if CONFIG_RELIABILITY_TEST_FAULTS
            if(s_pause_feed) break;
#endif
            size_t buffered = 0;
            uart_get_buffered_data_len(UART_PORT, &buffered);
            if (buffered == 0 || drained >= MAX_PER_ROUND) break;
            const size_t want = buffered < READ_CHUNK ? buffered : READ_CHUNK;
            const int n = uart_read_bytes(UART_PORT, buf, want, 0);
            if (n <= 0) break;
            const uint32_t now = now_ms();
            for (size_t i = 0; i < (size_t)n; i++)
                device_service_feed(&s_service, buf[i], now);
            drained += (size_t)n;
            serviced = true;
        }

        protocol_rx_poll(&s_service.rx, now_ms());

        /* 3) TX 步进：队列里有帧就推（uart_tx_chars 有界写入） */
#if CONFIG_RELIABILITY_TEST_FAULTS
        if (!s_pause_tx)
#endif
        {
            const uint32_t before = s_service.tx.dropped;
            protocol_tx_step(&s_service.tx, now_ms(), uart_write_some, NULL);
            if (s_service.tx.dropped != before)
                ESP_LOGW(TAG, "tx dropped (queue full or deadline)");
            serviced = true;
        }

        /* 4) 本轮零事件且队列空：靠 5ms 的队列等待自然让出，不空转 */
        (void)serviced;
    }
}

void app_main(void)
{
    uart_config_t cfg = {
        .baud_rate  = 115200,
        .data_bits  = UART_DATA_8_BITS,
        .parity     = UART_PARITY_DISABLE,
        .stop_bits  = UART_STOP_BITS_1,
        .flow_ctrl  = UART_HW_FLOWCTRL_DISABLE,
        .source_clk = UART_SCLK_DEFAULT,
    };

    /* 装驱动：RX ring=1024、TX ring=0（uart.c:1940 允许；发送走 uart_tx_chars） */
    ESP_ERROR_CHECK(uart_driver_install(UART_PORT, RX_RING, 0, EVENT_QUEUE,
                                        &s_uart_queue, 0));
    ESP_ERROR_CHECK(uart_param_config(UART_PORT, &cfg));
    ESP_ERROR_CHECK(uart_set_pin(UART_PORT, TX_PIN, RX_PIN,
                                 UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE));

    /* 复位原因由 IDF 决定（esp_reset_reason_t），CLI 按 platform=2 解释 */
    device_service_init(&s_service, 2, (uint32_t)esp_reset_reason(),
#if CONFIG_RELIABILITY_TEST_FAULTS
                        false, fault_inject, NULL);
#else
                        false, NULL, NULL);
#endif

    const BaseType_t ok = xTaskCreate(uart_task, "uart_proto", 4096, NULL, 10, NULL);
    ESP_ERROR_CHECK(ok == pdPASS ? ESP_OK : ESP_ERR_NO_MEM);

    ESP_LOGI(TAG, "UART%d framed protocol on TX=GPIO%d RX=GPIO%d @115200 8N1"
             "（协议口无文本；主机用 device-console.py）",
             UART_PORT, TX_PIN, RX_PIN);
}

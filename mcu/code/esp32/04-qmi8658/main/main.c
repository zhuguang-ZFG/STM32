/*
 * QMI8658 六轴读取；立创实战派 S3，IDF 5.5.2 新 I2C master。
 * 板卡/寄存器来源：https://wiki.lckfb.com/zh-hans/szpi-esp32s3/beginner/attitude-sensor.html
 * SDA=1 SCL=2，7 位地址 0x6a；WHO_AM_I=0x05，数据从 AX_L(0x35) 开始。
 * 教学示例每 100ms 取最新样本，不声称无丢样采集；待上板实测。
 */
#include <stdint.h>
#include "driver/i2c_master.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"

#define SDA_PIN 1
#define SCL_PIN 2
#define QMI_ADDRESS 0x6a
static const char *TAG = "qmi8658";
static i2c_master_dev_handle_t imu;

static esp_err_t read_reg(uint8_t reg, uint8_t *bytes, size_t count)
{
    return i2c_master_transmit_receive(imu, &reg, 1, bytes, count, 100);
}
static void write_reg(uint8_t reg, uint8_t value)
{
    const uint8_t bytes[] = {reg, value};
    ESP_ERROR_CHECK(i2c_master_transmit(imu, bytes, sizeof(bytes), 100));
}
/* 显式小端组合与符号扩展，不依赖宿主字节序和指针别名。 */
static int32_t signed_le16(const uint8_t *p)
{
    const uint32_t raw = (uint32_t)p[0] | ((uint32_t)p[1] << 8);
    return raw >= 32768U ? (int32_t)raw - 65536 : (int32_t)raw;
}
void app_main(void)
{
    i2c_master_bus_handle_t bus;
    const i2c_master_bus_config_t bus_cfg = {
        .i2c_port = I2C_NUM_0, .sda_io_num = SDA_PIN, .scl_io_num = SCL_PIN,
        .clk_source = I2C_CLK_SRC_DEFAULT, .glitch_ignore_cnt = 7,
        .flags.enable_internal_pullup = true,
    };
    ESP_ERROR_CHECK(i2c_new_master_bus(&bus_cfg, &bus));
    const i2c_device_config_t cfg = {
        .dev_addr_length = I2C_ADDR_BIT_LEN_7, .device_address = QMI_ADDRESS,
        .scl_speed_hz = 100000,
    };
    ESP_ERROR_CHECK(i2c_master_bus_add_device(bus, &cfg, &imu));
    uint8_t id;
    ESP_ERROR_CHECK(read_reg(0x00, &id, 1));
    if (id != 0x05) {
        ESP_LOGE(TAG, "WHO_AM_I=0x%02x (expected 0x05); check board/address", id);
        return; /* ID 错误不继续写配置，也不无限等待。 */
    }
    write_reg(0x60, 0xb0);             /* RESET */
    vTaskDelay(pdMS_TO_TICKS(20));
    write_reg(0x08, 0x00);             /* CTRL7：先关闭采样再配置 */
    write_reg(0x02, 0x40);             /* CTRL1：地址递增 */
    write_reg(0x03, 0x15);             /* CTRL2：±4g、250Hz，关闭 self-test */
    write_reg(0x04, 0x55);             /* CTRL3：±512dps、250Hz，关闭 self-test */
    write_reg(0x08, 0x03);             /* CTRL7：加速度与角速度使能 */
    ESP_LOGI(TAG, "WHO_AM_I=0x%02x; +/-4g, +/-512dps, sensor 250Hz; print 10Hz", id);
    unsigned stale = 0;
    for (;;) {
        vTaskDelay(pdMS_TO_TICKS(100));
        uint8_t status, bytes[12];
        esp_err_t err = read_reg(0x2e, &status, 1);
        if (err == ESP_OK && (status & 0x03) == 0x03) {
            err = read_reg(0x35, bytes, sizeof(bytes));
            if (err == ESP_OK) {
                stale = 0;
                /* 32768 / 4 = 8192 LSB/g；32768 / 512 = 64 LSB/(deg/s)。 */
                ESP_LOGI(TAG, "g=[%.3f %.3f %.3f] dps=[%.2f %.2f %.2f]",
                    signed_le16(bytes) / 8192.0, signed_le16(bytes+2) / 8192.0,
                    signed_le16(bytes+4) / 8192.0, signed_le16(bytes+6) / 64.0,
                    signed_le16(bytes+8) / 64.0, signed_le16(bytes+10) / 64.0);
            }
        } else if (err == ESP_OK && ++stale % 10 == 0) {
            ESP_LOGW(TAG, "no complete six-axis sample for %u polls", stale);
        }
        if (err != ESP_OK) ESP_LOGE(TAG, "I2C: %s", esp_err_to_name(err));
    }
}

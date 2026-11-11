/*
 * 立创实战派 S3 音频：I2C(1/2) 配 ES8311 与 PCA9557，I2S 推送 PCM。
 * 引脚与扩展器来源：https://wiki.lckfb.com/zh-hans/szpi-esp32s3/beginner/audio-output-es8311.html
 * codec 接口参照 IDF v5.5.2 examples/peripherals/i2s/i2s_codec/i2s_es8311（CC0）。
 * 不带版权音乐文件；波形现场生成。待上板实测。
 */
#include <assert.h>
#include <math.h>
#include <stdint.h>
#include "driver/i2c_master.h"
#include "driver/i2s_std.h"
#include "esp_codec_dev.h"
#include "esp_codec_dev_defaults.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#define SAMPLE_RATE 16000
#define BLOCK_FRAMES 160
static const char *TAG = "audio-play";
static i2c_master_dev_handle_t expander;
static esp_codec_dev_handle_t codec;

static void reg_write(uint8_t reg, uint8_t value)
{
    const uint8_t bytes[] = {reg, value};
    ESP_ERROR_CHECK(i2c_master_transmit(expander, bytes, sizeof(bytes), 100));
}
static uint8_t reg_read(uint8_t reg)
{
    uint8_t value;
    ESP_ERROR_CHECK(i2c_master_transmit_receive(expander, &reg, 1, &value, 1, 100));
    return value;
}
static void amplifier(bool on)
{
    uint8_t output = reg_read(0x01);
    reg_write(0x01, on ? (output | 0x02) : (output & (uint8_t)~0x02));
}
static void codec_check(int result)
{
    if (result != ESP_CODEC_DEV_OK) {
        amplifier(false);
        ESP_LOGE(TAG, "codec error %d; amplifier disabled", result);
        abort();
    }
}
static void tone(float frequency, unsigned duration_ms)
{
    /* 双槽位各放同一份单声道样本：16k*16*2=512kbit/s 总线数据。 */
    int16_t pcm[BLOCK_FRAMES * 2];
    const unsigned frames = SAMPLE_RATE * duration_ms / 1000U;
    for (unsigned start = 0; start < frames; start += BLOCK_FRAMES) {
        unsigned count = frames - start;
        if (count > BLOCK_FRAMES) count = BLOCK_FRAMES;
        for (unsigned i = 0; i < count; ++i) {
            const unsigned n = start + i;
            /* 首尾 10ms 淡入淡出，减少音符边沿突变。 */
            float envelope = fminf(1.0f, fminf(n / 160.0f, (frames - 1U - n) / 160.0f));
            int16_t value = frequency > 0 ? (int16_t)(3000.0f * envelope *
                sinf(6.28318530718f * frequency * n / SAMPLE_RATE)) : 0;
            pcm[2*i] = value;
            pcm[2*i+1] = value;
        }
        codec_check(esp_codec_dev_write(codec, pcm, count * 2U * sizeof(int16_t)));
    }
}
void app_main(void)
{
    i2c_master_bus_handle_t bus;
    const i2c_master_bus_config_t bus_cfg = {
        .i2c_port = I2C_NUM_0, .sda_io_num = 1, .scl_io_num = 2,
        .clk_source = I2C_CLK_SRC_DEFAULT, .glitch_ignore_cnt = 7,
        .flags.enable_internal_pullup = true,
    };
    ESP_ERROR_CHECK(i2c_new_master_bus(&bus_cfg, &bus));
    const i2c_device_config_t exp_cfg = {
        .dev_addr_length = I2C_ADDR_BIT_LEN_7, .device_address = 0x19, .scl_speed_hz = 100000,
    };
    ESP_ERROR_CHECK(i2c_master_bus_add_device(bus, &exp_cfg, &expander));
    amplifier(false); /* 上电先静音；PA_EN 是 PCA9557 bit1，不是 ESP32 GPIO1。 */
    reg_write(0x03, reg_read(0x03) & (uint8_t)~0x02); /* 只改 PA_EN 方向，保留相机/LCD。 */

    i2s_chan_handle_t tx;
    i2s_chan_config_t channel_cfg = I2S_CHANNEL_DEFAULT_CONFIG(I2S_NUM_0, I2S_ROLE_MASTER);
    channel_cfg.auto_clear = true;
    ESP_ERROR_CHECK(i2s_new_channel(&channel_cfg, &tx, NULL));
    i2s_std_config_t std_cfg = {
        .clk_cfg = I2S_STD_CLK_DEFAULT_CONFIG(SAMPLE_RATE),
        .slot_cfg = I2S_STD_PHILIPS_SLOT_DEFAULT_CONFIG(I2S_DATA_BIT_WIDTH_16BIT, I2S_SLOT_MODE_STEREO),
        .gpio_cfg = {
            .mclk = 38, .bclk = 14, .ws = 13, .dout = 45, .din = I2S_GPIO_UNUSED,
        },
    };
    std_cfg.clk_cfg.mclk_multiple = I2S_MCLK_MULTIPLE_256;
    ESP_ERROR_CHECK(i2s_channel_init_std_mode(tx, &std_cfg));
    ESP_ERROR_CHECK(i2s_channel_enable(tx));
    const audio_codec_i2c_cfg_t ctrl_cfg = {
        .port = I2C_NUM_0, .addr = ES8311_CODEC_DEFAULT_ADDR, .bus_handle = bus,
    };
    const audio_codec_ctrl_if_t *ctrl = audio_codec_new_i2c_ctrl(&ctrl_cfg);
    const audio_codec_i2s_cfg_t data_cfg = { .port = I2S_NUM_0, .tx_handle = tx };
    const audio_codec_data_if_t *data = audio_codec_new_i2s_data(&data_cfg);
    const audio_codec_gpio_if_t *gpio = audio_codec_new_gpio();
    assert(ctrl && data && gpio);
    const es8311_codec_cfg_t chip_cfg = {
        .ctrl_if = ctrl, .gpio_if = gpio, .codec_mode = ESP_CODEC_DEV_WORK_MODE_DAC,
        .master_mode = false, .use_mclk = true, .pa_pin = -1,
        .hw_gain = { .pa_voltage = 5.0f, .codec_dac_voltage = 3.3f },
        .mclk_div = 256,
    };
    const audio_codec_if_t *chip = es8311_codec_new(&chip_cfg);
    assert(chip);
    const esp_codec_dev_cfg_t dev_cfg = {
        .dev_type = ESP_CODEC_DEV_TYPE_OUT, .codec_if = chip, .data_if = data,
    };
    codec = esp_codec_dev_new(&dev_cfg);
    assert(codec);
    esp_codec_dev_sample_info_t sample = {
        .bits_per_sample = 16, .channel = 2, .channel_mask = 3, .sample_rate = SAMPLE_RATE,
    };
    codec_check(esp_codec_dev_open(codec, &sample));
    codec_check(esp_codec_dev_set_out_vol(codec, 40));
    tone(0, 100); /* 先让 DMA 稳定输出静音。 */
    amplifier(true);
    ESP_LOGI(TAG, "1kHz for 1s; fs=16000, stereo slots, MCLK=4096000");
    tone(1000, 1000);
    tone(0, 200);
    const float melody[] = {261.63f, 293.66f, 329.63f, 349.23f, 392.00f, 440.00f, 493.88f, 523.25f};
    for (unsigned i = 0; i < sizeof(melody)/sizeof(melody[0]); ++i) {
        ESP_LOGI(TAG, "note %u/8", i+1);
        tone(melody[i], 250);
        tone(0, 50);
    }
    tone(0, 200); /* 静音块排在旋律后，等待剩余 DMA 播放再关功放。 */
    vTaskDelay(pdMS_TO_TICKS(200));
    amplifier(false);
    codec_check(esp_codec_dev_close(codec));
    ESP_LOGI(TAG, "playback finished; amplifier off");
}

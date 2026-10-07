/**
 * @file    main.c
 * @brief   iap-bootloader —— IAP 串口升级 Bootloader（STM32F103C8T6 / BluePill）
 *
 * 功能：
 *   1) 上电等待约 500ms，收到字符 'U' 则进入串口升级模式，否则跳转 APP；
 *   2) 通过 USART1 接收固件：协议 = 0x5A + 4 字节长度 + 数据 + 4 字节累加校验；
 *   3) 按页擦除 APP 区 → 按半字写入 Flash → 校验，全部通过才算升级成功；
 *   4) 跳转前完成「关中断、复位外设、设 MSP、设 SCB->VTOR」四步，避免死机。
 *
 * Flash 划分（STM32F103C8T6，64KB）：
 *   0x08000000 ~ 0x08003FFF  Bootloader（16KB）
 *   0x08004000 ~ 0x080047FF  参数区（2KB，本示例未使用）
 *   0x08004800 ~ 0x0800FFFF  APP 区（46KB）
 *
 * ⚠️ APP 端必须做两件事（见 README）：
 *   ① 链接脚本把 Flash 起始改为 0x08004800、长度改为 46KB；
 *   ② main() 开头执行 SCB->VTOR = 0x08004800;
 *
 * 目标芯片：STM32F103C8T6，系统时钟 72MHz。
 */

#include "stm32f1xx_hal.h"
#include <string.h>

/* ------------------------------------------------------------------ 宏定义 */

#define APP_ADDR            0x08004800UL    /* APP 起始地址（页边界） */
#define APP_MAX_SIZE        (46U * 1024U)   /* APP 区大小 */
#define FLASH_PAGE_SIZE     1024UL          /* F103C8 小容量：1KB/页 */
#define FLASH_BASE_ADDR     0x08000000UL

#define UART_INSTANCE       USART1
#define UART_TX_PIN         GPIO_PIN_9      /* USART1_TX = PA9 */
#define UART_RX_PIN         GPIO_PIN_10     /* USART1_RX = PA10 */
#define UART_BAUDRATE       115200U

#define FW_START_BYTE       0x5AU           /* 固件帧起始字节 */
#define RX_CHUNK            512U            /* 每次接收的字节数（半字对齐） */
#define WAIT_UPGRADE_MS     500U            /* 上电等待升级命令的时间 */

#define LED_PORT            GPIOC
#define LED_PIN             GPIO_PIN_13     /* 板载 LED，低电平点亮 */

typedef void (*pFunction)(void);

/* ---------------------------------------------------------------- 全局句柄 */

UART_HandleTypeDef huart1;

static uint8_t g_rx_buf[RX_CHUNK];

/* ----------------------------------------------------------------- 私有函数 */

static void SystemClock_Config(void);
static void boot_init(void);
static void error_handler(void);

static int      flash_erase_range(uint32_t addr, uint32_t len);
static int      flash_write_bytes(uint32_t addr, const uint8_t *data, uint32_t len);
static uint32_t checksum32(const uint8_t *data, uint32_t len);
static int      uart_wait_for_upgrade(uint32_t timeout_ms);
static int      uart_receive_firmware(uint32_t app_addr, uint32_t *out_size);
static void     jump_to_app(uint32_t app_addr);

/* ---------------------------------------------------------------- 主函数 */

int main(void)
{
    HAL_Init();
    SystemClock_Config();
    boot_init();

    HAL_GPIO_WritePin(LED_PORT, LED_PIN, GPIO_PIN_RESET);   /* 点亮：进入 Bootloader */

    /* 上电等待：收到 'U' 进入升级，否则直接跳 APP */
    if (uart_wait_for_upgrade(WAIT_UPGRADE_MS))
    {
        uint32_t fw_size = 0U;
        if (uart_receive_firmware(APP_ADDR, &fw_size) == 0)
        {
            /* 升级成功：LED 快闪 3 次提示 */
            for (int i = 0; i < 3; i++)
            {
                HAL_GPIO_TogglePin(LED_PORT, LED_PIN);
                HAL_Delay(100);
            }
        }
        /* 升级失败也继续往下，跳回旧 APP */
    }

    jump_to_app(APP_ADDR);
    for (;;) { }        /* 不会执行到这里 */
}

/**
 * @file    main.c
 * @brief   USB CDC 虚拟串口回环（STM32F103C8 / BluePill）
 *
 * USB 全速要 48 MHz。本文件把 PLL 配成 72 MHz，再把 USB 预分频设为 1.5。
 * 插上板载 USB 口之后，主机应出现一个 CDC 串口。打开串口（DTR=1）后：
 *   1) 你发出去的字节会原样回来；
 *   2) 大约每秒一行 "cdc tick"。
 *
 * 不链接 ST 的 USB Device 中间件。需要的是 HAL 的 PCD 三件套：
 *   stm32f1xx_hal_pcd.c、stm32f1xx_hal_pcd_ex.c、stm32f1xx_ll_usb.c。
 */

#include "stm32f1xx_hal.h"
#include "usb_cdc.h"

#define LED_PORT   GPIOC
#define LED_PIN    GPIO_PIN_13

static void SystemClock_Config(void);
static void led_init(void);
static void error_handler(void);

int main(void)
{
    uint8_t buf[64];
    uint32_t last = 0U;

    HAL_Init();
    SystemClock_Config();
    led_init();
    usb_cdc_init();

    while (1)
    {
        uint16_t n = usb_cdc_read(buf, sizeof buf);
        if (n > 0U)
        {
            while (usb_cdc_write(buf, n) != 0)
            {
                HAL_Delay(1);
            }
        }
        if (usb_cdc_ready() != 0U && usb_cdc_dtr() != 0U &&
            (HAL_GetTick() - last) >= 1000U)
        {
            static const uint8_t tick[] = "cdc tick\r\n";
            if (usb_cdc_write(tick, sizeof tick - 1U) == 0)
            {
                last = HAL_GetTick();
                HAL_GPIO_TogglePin(LED_PORT, LED_PIN);
            }
        }
    }
}

static void led_init(void)
{
    GPIO_InitTypeDef io = {0};
    __HAL_RCC_GPIOC_CLK_ENABLE();
    io.Pin = LED_PIN;
    io.Mode = GPIO_MODE_OUTPUT_PP;
    io.Pull = GPIO_NOPULL;
    io.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(LED_PORT, &io);
    HAL_GPIO_WritePin(LED_PORT, LED_PIN, GPIO_PIN_SET);
}

static void SystemClock_Config(void)
{
    RCC_OscInitTypeDef osc = {0};
    RCC_ClkInitTypeDef clk = {0};
    RCC_PeriphCLKInitTypeDef per = {0};

    osc.OscillatorType = RCC_OSCILLATORTYPE_HSE;
    osc.HSEState = RCC_HSE_ON;
    osc.HSEPredivValue = RCC_HSE_PREDIV_DIV1;
    osc.HSIState = RCC_HSI_ON;
    osc.PLL.PLLState = RCC_PLL_ON;
    osc.PLL.PLLSource = RCC_PLLSOURCE_HSE;
    osc.PLL.PLLMUL = RCC_PLL_MUL9;
    if (HAL_RCC_OscConfig(&osc) != HAL_OK)
    {
        error_handler();
    }

    clk.ClockType = RCC_CLOCKTYPE_HCLK | RCC_CLOCKTYPE_SYSCLK |
                    RCC_CLOCKTYPE_PCLK1 | RCC_CLOCKTYPE_PCLK2;
    clk.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
    clk.AHBCLKDivider = RCC_SYSCLK_DIV1;
    clk.APB1CLKDivider = RCC_HCLK_DIV2;
    clk.APB2CLKDivider = RCC_HCLK_DIV1;
    if (HAL_RCC_ClockConfig(&clk, FLASH_LATENCY_2) != HAL_OK)
    {
        error_handler();
    }

    per.PeriphClockSelection = RCC_PERIPHCLK_USB;
    per.UsbClockSelection = RCC_USBCLKSOURCE_PLL_DIV1_5;
    if (HAL_RCCEx_PeriphCLKConfig(&per) != HAL_OK)
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

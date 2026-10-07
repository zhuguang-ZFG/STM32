/**
 * @file    main.c
 * @brief   USB HID 键盘：PA0 按下时向焦点窗口送一个字母 a（STM32F103C8）
 *
 * 用法码 0x04 是 HID 键盘上的 a。按下沿发「按下」，松开沿发「全 0」。
 * 不会一直连发。先点一个文本框再按键，避免字母进到你不想改的窗口。
 *
 * 时钟与 CDC 示例相同：PLL 72 MHz，USB 预分频 1.5，得到 48 MHz。
 */

#include "stm32f1xx_hal.h"
#include "usb_hid.h"

#define KEY_PORT   GPIOA
#define KEY_PIN    GPIO_PIN_0
#define LED_PORT   GPIOC
#define LED_PIN    GPIO_PIN_13
#define HID_A      0x04U

static void SystemClock_Config(void);
static void gpio_init(void);
static void error_handler(void);

int main(void)
{
    uint8_t prev = 1U;

    HAL_Init();
    SystemClock_Config();
    gpio_init();
    usb_hid_init();

    while (1)
    {
        uint8_t down = (HAL_GPIO_ReadPin(KEY_PORT, KEY_PIN) == GPIO_PIN_RESET) ? 1U : 0U;
        if (usb_hid_ready() != 0U && down != prev)
        {
            if (usb_hid_key(HID_A, down) == 0)
            {
                prev = down;
                HAL_GPIO_WritePin(LED_PORT, LED_PIN,
                                  down ? GPIO_PIN_RESET : GPIO_PIN_SET);
            }
        }
    }
}

static void gpio_init(void)
{
    GPIO_InitTypeDef io = {0};

    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_GPIOC_CLK_ENABLE();

    io.Pin = KEY_PIN;
    io.Mode = GPIO_MODE_INPUT;
    io.Pull = GPIO_PULLUP;
    HAL_GPIO_Init(KEY_PORT, &io);

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

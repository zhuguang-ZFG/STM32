/* 最小 HAL 配置（仅启用本工程模块；CANDIDATE，P2 随板冻结）。 */
#ifndef STM32F1XX_HAL_CONF_H
#define STM32F1XX_HAL_CONF_H

#define HAL_MODULE_ENABLED
#define HAL_CORTEX_MODULE_ENABLED
#define HAL_DMA_MODULE_ENABLED
#define HAL_FLASH_MODULE_ENABLED
#define HAL_GPIO_MODULE_ENABLED
#define HAL_PWR_MODULE_ENABLED
#define HAL_RCC_MODULE_ENABLED
#define HAL_TIM_MODULE_ENABLED
#define HAL_UART_MODULE_ENABLED

#define HSE_VALUE    8000000u
#define HSE_STARTUP_TIMEOUT  100u
#define LSE_STARTUP_TIMEOUT  5000u
#define HSI_VALUE    8000000u
#define LSI_VALUE    40000u
#define LSE_VALUE    32768u
#define VDD_VALUE    3300u
#define PREFETCH_ENABLE_IS_UNDEFINED  /* 由 HAL 默认处理 */

#define USE_HAL_ADC_REGISTER_CALLBACKS       0u
#define USE_HAL_CAN_REGISTER_CALLBACKS       0u
#define USE_HAL_CEC_REGISTER_CALLBACKS       0u
#define USE_HAL_DAC_REGISTER_CALLBACKS       0u
#define USE_HAL_ETH_REGISTER_CALLBACKS       0u /* n/a */
#define USE_HAL_HCD_REGISTER_CALLBACKS       0u
#define USE_HAL_I2C_REGISTER_CALLBACKS       0u
#define USE_HAL_MMC_REGISTER_CALLBACKS       0u
#define USE_HAL_NAND_REGISTER_CALLBACKS      0u
#define USE_HAL_NOR_REGISTER_CALLBACKS       0u
#define USE_HAL_PCCARD_REGISTER_CALLBACKS    0u
#define USE_HAL_PCD_REGISTER_CALLBACKS       0u
#define USE_HAL_RTC_REGISTER_CALLBACKS       0u
#define USE_HAL_SD_REGISTER_CALLBACKS        0u
#define USE_HAL_SMARTCARD_REGISTER_CALLBACKS 0u
#define USE_HAL_IRDA_REGISTER_CALLBACKS      0u
#define USE_HAL_SRAM_REGISTER_CALLBACKS      0u
#define USE_HAL_SPI_REGISTER_CALLBACKS       0u
#define USE_HAL_TIM_REGISTER_CALLBACKS       0u
#define USE_HAL_UART_REGISTER_CALLBACKS      0u
#define USE_HAL_USART_REGISTER_CALLBACKS     0u
#define USE_HAL_WWDG_REGISTER_CALLBACKS      0u

#define MAC_ADDR0   2u
#define MAC_ADDR1   0u
#define MAC_ADDR2   0u
#define MAC_ADDR3   0u
#define MAC_ADDR4   0u
#define MAC_ADDR5   0u

#define ETH_RX_BUF_SIZE 0  /* 不适用 */
#define ETH_RXBUFNB     0
#define ETH_TX_BUF_SIZE 0
#define ETH_TXBUFNB     0

#define DP83848_PHY_ADDRESS     0x01u
#define PHY_RESET_DELAY         0x000000FFu
#define PHY_CONFIG_DELAY        0x00000FFFu
#define PHY_READ_TO             0x0000FFFFu
#define PHY_WRITE_TO            0x0000FFFFu
#define PHY_BCR                 0x00u
#define PHY_BSR                 0x01u
#define PHY_RESET               0x8000u
#define PHY_LOOPBACK            0x4000u
#define PHY_FULLDUPLEX_100M     0x2100u
#define PHY_HALFDUPLEX_100M     0x2000u
#define PHY_FULLDUPLEX_10M      0x0100u
#define PHY_HALFDUPLEX_10M      0x0000u
#define PHY_AUTONEGOTIATION     0x1000u
#define PHY_RESTART_AUTONEGOTIATION 0x0200u
#define PHY_POWERDOWN           0x0800u
#define PHY_ISOLATE             0x0400u
#define PHY_AUTONEGO_COMPLETE   0x0020u
#define PHY_LINKED_STATUS       0x0004u
#define PHY_JABBER_DETECTION    0x0002u

#define USE_SPI_CRC 0u

/* assert_param：release 为空操作；USE_FULL_ASSERT 时走 assert_failed（P2 可选） */
#ifdef USE_FULL_ASSERT
void assert_failed(uint8_t *file, uint32_t line);
#define assert_param(expr) ((expr) ? (void)0U : assert_failed((uint8_t *)__FILE__, __LINE__))
#else
#define assert_param(expr) ((void)0U)
#endif

#define TICK_INT_PRIORITY  0x0Fu
#define USE_RTOS           0u
#define PREFETCH_ENABLE    1u

#ifdef HAL_RCC_MODULE_ENABLED
#include "stm32f1xx_hal_rcc.h"
#endif
#ifdef HAL_GPIO_MODULE_ENABLED
#include "stm32f1xx_hal_gpio.h"
#endif
#ifdef HAL_CORTEX_MODULE_ENABLED
#include "stm32f1xx_hal_cortex.h"
#endif
#ifdef HAL_DMA_MODULE_ENABLED
#include "stm32f1xx_hal_dma.h"
#endif
#ifdef HAL_FLASH_MODULE_ENABLED
#include "stm32f1xx_hal_flash.h"
#endif
#ifdef HAL_PWR_MODULE_ENABLED
#include "stm32f1xx_hal_pwr.h"
#endif
#ifdef HAL_TIM_MODULE_ENABLED
#include "stm32f1xx_hal_tim.h"
#endif
#ifdef HAL_UART_MODULE_ENABLED
#include "stm32f1xx_hal_uart.h"
#endif

#endif /* STM32F1XX_HAL_CONF_H */

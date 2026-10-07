# Peripheral Bus and Pin Quick Reference

> 中文：[外设总线与引脚速查表](../../../cheatsheets/外设总线与引脚速查表.md)

> Look up which bus a peripheral is on, which pin is the default, and which AF to select for an F4 alternate function.
> The bus determines the clock source and the maximum frequency; the pin determines the wiring; the AF number selects the alternate function on F4.

## Contents

| Section | Contents |
| --- | --- |
| [§1](#1-peripheral-bus-map-f103) | F103 peripheral bus map |
| [§2](#2-peripheral-bus-map-f411) | F411 peripheral bus map |
| [§3](#3-default-pins-for-common-peripherals) | Default pins for USART/SPI/I2C/TIM/ADC/CAN/USB |
| [§4](#4-f4-alternate-function-af-number-table) | F4 AF0~AF15 table |
| [§5](#5-5v-tolerant-pin-notes) | 5V-tolerant pin (FT) notes |

## 1. Peripheral Bus Map (F103)

> F103 system: SYSCLK=72MHz, HCLK(AHB)=72MHz, PCLK1(APB1)=36MHz, PCLK2(APB2)=72MHz.
> **APB1 maximum is 36MHz, APB2 maximum is 72MHz**; for a timer on APB1, if the APB1 prescaler ≠ 1, the timer clock = PCLK1×2.

| Bus | Maximum frequency | Peripherals |
| --- | --- | --- |
| **AHB** | 72MHz | DMA1, DMA2, SRAM, Flash interface (FLITF), CRC, FSMC |
| **APB1** | 36MHz | TIM2/3/4/5/6/7, USART2/3, UART4/5, SPI2/I2S2, I2C1/2, USB, CAN, BKP, PWR, WWDG, IWDG(*) |
| **APB2** | 72MHz | AFIO, GPIOA~G, EXTI(*), TIM1/8/9/10/11, USART1, SPI1, ADC1/2/3, ADC temperature |

> (*) The IWDG clock source is the independent LSI; EXTI is configured through AFIO. TIM1/TIM8 are advanced timers (APB2).

## 2. Peripheral Bus Map (F411)

> F411 system: SYSCLK maximum 100MHz, HCLK=100MHz, PCLK1(APB1)=50MHz, PCLK2(APB2)=100MHz.

| Bus | Maximum frequency | Peripherals |
| --- | --- | --- |
| **AHB1** | 100MHz | GPIOA~H, DMA1, DMA2, RCC, FLASH interface, CRC |
| **AHB2** | 100MHz | USB OTG FS |
| **APB1** | 50MHz | TIM2/3/4/5, USART2, SPI2/I2S2, I2C1/2/3, I2C, WWDG, PWR, UART/SPI3 (some) |
| **APB2** | 100MHz | TIM1/9/10/11, USART1/6, SPI1/4/5, ADC1, SYSCFG, EXTI, SDIO |

> The biggest difference from F103: F4 GPIO is on **AHB1** (F1 is on APB2); the F4 peripheral clock enable macro is
> `__HAL_RCC_GPIOx_CLK_ENABLE()` (it accesses AHB1ENR internally), while F1 accesses APB2ENR.

## 3. Default Pins for Common Peripherals

> Focused on LQFP48 (BluePill F103C8 / BlackPill F411CE). **The same pin may be shared by several peripherals; watch for conflicts.**

| Peripheral | Function | F103 pin | F411 pin |
| --- | --- | --- | --- |
| USART1 | TX / RX | PA9 / PA10 | PA9 / PA10 (or PB6/PB7) |
| USART2 | TX / RX | PA2 / PA3 | PA2 / PA3 |
| USART3 | TX / RX | PB10 / PB11 | PB10 / PB11 |
| SPI1 | SCK/MISO/MOSI/NSS | PA5/PA6/PA7/PA4 | PA5/PA6/PA7/PA4 |
| SPI2 | SCK/MISO/MOSI/NSS | PB13/PB14/PB15/PB12 | PB13/PB14/PB15/PB12 |
| I2C1 | SCL / SDA | PB6 / PB7 | PB6 / PB7 (or PB8/PB9) |
| I2C2 | SCL / SDA | PB10 / PB11 | PB10 / PB11 |
| TIM1 | CH1/CH2/CH3/CH4 | PA8/PA9/PA10/PA11 | PA8/PA9/PA10/PA11 |
| TIM2 | CH1/CH2/CH3/CH4 | PA0/PA1/PA2/PA3 | PA0/PA1/PA2/PA3 |
| TIM3 | CH1/CH2/CH3/CH4 | PA6/PA7/PB0/PB1 | PA6/PA7/PB0/PB1 |
| TIM4 | CH1/CH2/CH3/CH4 | PB6/PB7/PB8/PB9 | PB6/PB7/PB8/PB9 |
| ADC1 | IN0~IN3 | PA0/PA1/PA2/PA3 | PA0/PA1/PA2/PA3 |
| ADC1 | IN4~IN7 | PA4/PA5/PA6/PA7 | PA4/PA5/PA6/PA7 |
| CAN1 | TX / RX | PA12 / PA11 (or PB9/PB8) | PA12 / PA11 (or PB9/PB8) |
| USB FS | DM / DP | PA11 / PA12 | PA11 / PA12 |
| SWD | SWDIO / SWCLK | PA13 / PA14 | PA13 / PA14 |
| LSE | OSC32_IN/OUT | PC14 / PC15 | PC14 / PC15 |
| HSE | OSC_IN/OUT | PD0 / PD1 (or PF0/PF1) | PH0 / PH1 |

> ⚠️ **Pin conflicts**: for example, `adc-dma` using PA4 (ADC_IN4) conflicts with `spi-flash` SPI1_NSS (PA4);
> `TIM3_CH1=PA6` conflicts with `SPI1_MISO=PA6`. When planning peripherals, draw a pin-usage table first.

## 4. F4 Alternate Function AF Number Table

> F4 alternate functions are selected by **AF0~AF15** (written to `GPIOx_AFRL/AFRH`).
> Configuration steps: `GPIO_MODE_AF_PP` + `io.Alternate = GPIO_AFx_yyy;`.
> **F1 has no AF number** (use `AF_PP` and the peripheral takes the pin over automatically). This is the largest configuration difference between F1 and F4.

| AF number | Main alternate functions |
| --- | --- |
| AF0 | SYS (JTAG/SWD, MCO, RTC, and so on) |
| AF1 | TIM1 / TIM2 |
| AF2 | TIM3 / TIM4 / TIM5 |
| AF3 | TIM8 / TIM9 / TIM10 / TIM11 |
| AF4 | I2C1 / I2C2 / I2C3 |
| AF5 | SPI1 / SPI2 / SPI3 / SPI4 / SPI5 / SPI6 |
| AF6 | SPI2 / SPI3 / I2S2 / I2S3 |
| AF7 | USART1 / USART2 / USART3 |
| AF8 | UART4 / UART5 / USART6 / UART7 / UART8 |
| AF9 | CAN1 / CAN2 / TIM12 / TIM13 / TIM14 |
| AF10 | OTG_FS / OTG_HS / SDIO |
| AF11 | ETH / FMC / DCMI |
| AF12 | SDIO / FMC / OTG_FS / OTG_HS |
| AF13 | DCMI / SDIO / FMC |
| AF14 | FMC / SDIO / LTDC |
| AF15 | EVENTOUT (event output) |

> Example: on F411, configure PA9 as USART1_TX → `GPIO_AF7_USART1`; configure PB6 as I2C1_SCL → `GPIO_AF4_I2C1`.

## 5. 5V-Tolerant Pin Notes

| Type | Description | Can it take 5V |
| --- | --- | --- |
| **FT (Five-volt Tolerant)** | Pins marked FT in the datasheet | ✅ Can take a 5V digital input |
| **TC (TTa with Analog)** | Analog pins; FT, and must not exceed VDDA when used as an analog input | ⚠️ 5V is allowed as a digital input; as ADC, only ≤VDDA |
| **Non-FT (standard IO)** | Not marked FT | ❌ Only ≤ VDDA (3.3V) |
| **Power / special pins** | VBAT, VDDA, VREF+, BOOT0, and similar | ❌ Use the voltage specified in the datasheet |
| **Open-drain + pull-up** | Any pin configured open-drain with an external 5V pull-up | ⚠️ Safe only when the device supports FT |

**How to look it up**: In the datasheet (DS) "Pinouts and pin description" table, read the type column for each pin:
`FT` means a 5V input is allowed, `FTf` means an I²C pin (FT capable), and no mark means a standard 3.3V pin.

> Important conclusion: **5V tolerance applies only to inputs**; a high output is always VDD (3.3V) and cannot drive 5V.
> If a 5V output level is required, use open-drain + a 5V pull-up (FT pins only) or add a level-shifter IC.

## 6. Peripheral Clock Enable Macro Comparison (F1 vs F4)

> Before writing registers or calling the HAL, enable the peripheral clock. F1 and F4 use the same macro names, but they access different registers internally.

| Peripheral class | Enable macro (common HAL form) | F1 register | F4 register |
| --- | --- | --- | --- |
| GPIO | `__HAL_RCC_GPIOA_CLK_ENABLE()` | `APB2ENR` | `AHB1ENR` |
| DMA1 | `__HAL_RCC_DMA1_CLK_ENABLE()` | `AHBENR` | `AHB1ENR` |
| USART1 | `__HAL_RCC_USART1_CLK_ENABLE()` | `APB2ENR` | `APB2ENR` |
| USART2 | `__HAL_RCC_USART2_CLK_ENABLE()` | `APB1ENR` | `APB1ENR` |
| SPI1 | `__HAL_RCC_SPI1_CLK_ENABLE()` | `APB2ENR` | `APB2ENR` |
| SPI2 | `__HAL_RCC_SPI2_CLK_ENABLE()` | `APB1ENR` | `APB1ENR` |
| I2C1 | `__HAL_RCC_I2C1_CLK_ENABLE()` | `APB1ENR` | `APB1ENR` |
| TIM2 | `__HAL_RCC_TIM2_CLK_ENABLE()` | `APB1ENR` | `APB1ENR` |
| TIM1 | `__HAL_RCC_TIM1_CLK_ENABLE()` | `APB2ENR` | `APB2ENR` |
| ADC1 | `__HAL_RCC_ADC1_CLK_ENABLE()` | `APB2ENR` | `APB2ENR` |
| AFIO/SYSCFG | `__HAL_RCC_AFIO_CLK_ENABLE()` / `__HAL_RCC_SYSCFG_CLK_ENABLE()` | `APB2ENR` | `APB2ENR` |
| PWR | `__HAL_RCC_PWR_CLK_ENABLE()` | `APB1ENR` | `APB1ENR` |

> **Conclusion**: Macro names are unified, so the registers do not have to be memorized; but F4 GPIO is on AHB1, so the F4 GPIO clock is faster,
> and `HAL_RCC_GetHCLKFreq()` is the GPIO clock frequency. F1 AFIO is called SYSCFG on F4.

## 7. Boot Modes and Debug Pins

| BOOT1 | BOOT0 | Boot location | Notes |
| --- | --- | --- | --- |
| x | 0 | Main Flash (`0x0800 0000`) | Normal run of the user program |
| 0 | 1 | System memory (Bootloader) | Built-in UART/USB DFU download program |
| 1 | 1 | Embedded SRAM | For debugging; lost on power-down |

| Pin | Function | Notes |
| --- | --- | --- |
| PA13 | SWDIO | Debug data line; **keep it**; do not configure it as a normal IO |
| PA14 | SWCLK | Debug clock line; **keep it** |
| PA15 / PB3 / PB4 | JTDI / JTDO / NJTRST | Default JTAG alternate function; to use them as normal IO, disable JTAG remapping |
| NRST | Reset | Active-low reset; can connect to the debugger reset line |
| BOOT0 | Boot selection | Boards usually have a jumper or button |

## 8. Common Peripheral Combinations and Pin-Use Examples

> When planning a project, draw a pin-usage table first to avoid alternate-function conflicts.

| Combination | Pins used | Potential conflict |
| --- | --- | --- |
| LED + button | PC13, PA0 | None |
| UART debug + PWM dimming | PA9/PA10, PA6 | PA6 conflicts with SPI1_MISO |
| I2C OLED + SPI Flash | PB6/PB7, PA5/PA6/PA7/PA4 | PA6 is both SPI1_MISO and TIM3_CH1 |
| ADC acquisition + UART DMA | PA0/PA1/PA4, PA9/PA10 | PA4 conflicts with SPI1_NSS |
| CAN + UART | PA11/PA12, PA9/PA10 | PA11/PA12 conflict with USB |
| USB + UART | PA11/PA12, PA9/PA10 | PA11/PA12 conflict with CAN |

> Memory aid: **PA11/PA12 = CAN or USB (pick one)**; **PA6 = SPI1_MISO / TIM3_CH1**;
> **PA4 = SPI1_NSS / ADC_IN4 / DAC_OUT1**. Check against the pin alternate-function table (DS datasheet).

## 9. Bus Arbitration and Clock Relationship Notes

| Relationship | Notes |
| --- | --- |
| Timer clock | When the APB prescaler ≠ 1, timer clock = PCLK ×2 (true for both F1 and F4) |
| ADCCLK | F1 = PCLK2/2/4/6/8 (≤14MHz); F4 = PCLK2/2/4/6/8 (≤36MHz) |
| USB clock | F1: PLL/1.5 must be exactly 48MHz; F4: PLL48CLK = 48MHz |
| SysTick | Part of the core; clock comes from HCLK/8 or HCLK, independent of APB |
| DMA and CPU | Share the bus matrix; DMA transfers consume bus bandwidth (F4 has a FIFO to ease this) |

> Related: [HAL Quick Reference](hal.md) · [Register Quick Reference](registers.md) · [Error Code and Troubleshooting Quick Reference](errors.md)

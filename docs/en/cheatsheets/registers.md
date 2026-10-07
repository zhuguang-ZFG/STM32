# Register Quick Reference

> 中文：[寄存器速查表](../../../cheatsheets/寄存器速查表.md)

> STM32F1 key peripheral register-bit quick reference. Column meanings: **Bit / Name / Meaning**.
> Before writing a register, enable the corresponding peripheral clock (`RCC->APBxENR` / `AHBENR`); otherwise the write has no effect.
> Reset value: R = read-only, W = write-only, RW = read/write.

## Contents

| Peripheral | Registers |
| --- | --- |
| [GPIO](#1-gpio) | CRL / CRH / IDR / ODR / BSRR / BRR / LCKR |
| [RCC](#2-rcc) | CR / CFGR / APB1ENR / APB2ENR / AHBENR / BDCR / CSR |
| [TIM](#3-tim) | CR1 / DIER / SR / EGR / CCMR1 / CCER / PSC / ARR / CCRx |
| [USART](#4-usart) | SR / DR / BRR / CR1 / CR2 / CR3 |
| [NVIC](#5-nvic) | ISER / ICER / ISPR / IPR |
| [EXTI](#6-exti) | IMR / EMR / RTSR / FTSR / SWIER / PR |
| [FLASH](#7-flash) | ACR / KEYR / CR / SR |

## 1. GPIO

### 1.1 GPIOx_CRL (configure the low 8 bits: Px0~Px7, offset 0x00)

Each 4 bits configure one pin: `[1:0]=MODE`, `[3:2]=CNF`.

| Bit | Name | Meaning |
| --- | --- | --- |
| `MODEy[1:0]` | Mode bits | `00` = input; `01` = output 10MHz; `10` = output 2MHz; `11` = output 50MHz |
| `CNFy[1:0]` | When input | `00` = analog; `01` = floating; `10` = pull-up/pull-down; `11` = reserved |
| `CNFy[1:0]` | When output | `00` = general-purpose push-pull; `01` = general-purpose open-drain; `10` = alternate-function push-pull; `11` = alternate-function open-drain |

### 1.2 GPIOx_CRH (configure the high 8 bits: Px8~Px15, offset 0x04)

Same format as CRL; the bit fields correspond to Px8~Px15.

### 1.3 GPIOx_IDR / ODR (offset 0x08 / 0x0C)

| Bit | Name | Meaning |
| --- | --- | --- |
| `IDR[15:0]` | Input data | R, read the current pin level (1 bit per pin) |
| `ODR[15:0]` | Output data | RW, write the pin output level (a read returns the last value written) |

### 1.4 GPIOx_BSRR / BRR (offset 0x10 / 0x14)

| Bit | Name | Meaning |
| --- | --- | --- |
| `BSRR[15:0]` | BSy | W, write 1 to set the corresponding pin high (atomic) |
| `BSRR[31:16]` | BRy | W, write 1 to reset the corresponding pin low (atomic) |
| `BRR[15:0]` | BRy | W, write 1 to reset the corresponding pin low (on F4 this is merged into the high 16 bits of BSRR) |

> **One write to BSRR completes set/reset and is inherently atomic**, which is better than a read-modify-write of `ODR`. Writing 0 has no effect.

### 1.5 GPIOx_LCKR (offset 0x18)

| Bit | Name | Meaning |
| --- | --- | --- |
| `LCKy[15:0]` | Lock | Together with the `LCKK` write sequence, locks the pin configuration to prevent accidental changes |

## 2. RCC

### 2.1 RCC_CR (clock control, offset 0x00)

| Bit | Name | Meaning |
| --- | --- | --- |
| `0` | HSION | Internal 8MHz enable (reset = 1) |
| `1` | HSIRDY | HSI ready (read-only) |
| `16` | HSEON | External crystal enable |
| `17` | HSERDY | HSE ready (read-only; a timeout means it failed to start) |
| `24` | PLLON | PLL enable |
| `25` | PLLRDY | PLL ready |
| `26` | CSSON | Clock security system enable |

### 2.2 RCC_CFGR (clock configuration, offset 0x04)

| Bit | Name | Meaning |
| --- | --- | --- |
| `[1:0]` | SW | System clock source: `00` HSI `01` HSE `10` PLL |
| `[3:2]` | SWS | Current clock source (read-only) |
| `[7:4]` | HPRE | AHB prescaler: `0xxx` = ÷1 … `1111` = ÷512 |
| `[10:8]` | PPRE1 | APB1 prescaler: `0xx` = ÷1, `100` = ÷2 … |
| `[13:11]` | PPRE2 | APB2 prescaler |
| `[15:14]` | ADCPRE | ADC prescaler: `00` = ÷2 `01` = ÷4 `10` = ÷6 `11` = ÷8 |
| `[21:18]` | PLLMUL | PLL multiplier: `0000` = ×2 … `0111` = ×9 … `1110` = ×16 |
| `16` | PLLSRC | PLL source: 0 = HSI/2, 1 = HSE |
| `24` | MCO | Clock output selection |

### 2.3 RCC_APB1ENR / APB2ENR / AHBENR (clock enable)

| Register | Typical bits (set to 1 to enable) |
| --- | --- |
| `APB1ENR` | `0`TIM2 `1`TIM3 `2`TIM4 `17`USART2 `21`I2C1 `22`I2C2 `23`USB `28`PWR `27`BKP |
| `APB2ENR` | `0`AFIO `2`GPIOA `3`GPIOB `4`GPIOC `9`ADC1 `11`TIM1 `12`SPI1 `14`USART1 |
| `AHBENR` | `0`DMA1 `1`DMA2 `2`SRAM `4`FLITF `6`CRC |

### 2.4 RCC_BDCR (backup domain control)

| Bit | Name | Meaning |
| --- | --- | --- |
| `0` | LSEON | LSE enable |
| `1` | LSERDY | LSE ready |
| `8` | RTCSEL | RTC source: `01` = LSE `10` = LSI `11` = HSE/128 |
| `15` | RTCEN | RTC clock enable |
| `16` | BDRST | Backup domain reset |

## 3. TIM

### 3.1 TIMx_CR1 (control, offset 0x00)

| Bit | Name | Meaning |
| --- | --- | --- |
| `0` | CEN | Counter enable |
| `3` | OPM | One-pulse mode |
| `4` | URS | Update request source |
| `7` | ARPE | ARR auto-reload preload enable |
| `[6:5]` | CMS | Center-aligned mode selection |
| `[9:8]` | CKD | Clock division (tdts) |
| `4` | DIR | Counting direction: 0 = up, 1 = down |

### 3.2 TIMx_DIER (DMA/interrupt enable, offset 0x0C)

| Bit | Name | Meaning |
| --- | --- | --- |
| `0` | UIE | Update interrupt enable |
| `1` | CC1IE | Capture/compare 1 interrupt |
| `6` | TIE | Trigger interrupt |
| `8` | UDE | Update DMA request |
| `9` | CC1DE | CC1 DMA request |

### 3.3 TIMx_SR (status, offset 0x10)

| Bit | Name | Meaning |
| --- | --- | --- |
| `0` | UIF | Update interrupt flag (must be cleared to 0 by software) |
| `1` | CC1IF | Capture/compare 1 flag |
| `6` | TIF | Trigger flag |

### 3.4 TIMx_EGR (event generation, offset 0x14)

| Bit | Name | Meaning |
| --- | --- | --- |
| `0` | UG | Software-generated update event (write 1 to reload the PSC/ARR shadow registers) |
| `1` | CC1G | Generate a capture/compare 1 event |

### 3.5 TIMx_CCMR1 (capture/compare mode, offset 0x18)

| Bit | Name | Meaning |
| --- | --- | --- |
| `[6:4]` | OC1M | Output mode: `110` = PWM mode 1, `111` = PWM mode 2 |
| `3` | OC1PE | CC1 preload enable |
| `[1:0]` | CC1S | Channel direction: `00` = output, `01` = input |

### 3.6 TIMx_CCER (capture/compare enable, offset 0x20)

| Bit | Name | Meaning |
| --- | --- | --- |
| `0` | CC1E | Channel 1 output/capture enable |
| `1` | CC1P | Channel 1 polarity: 0 = active high, 1 = active low |

### 3.7 TIMx_PSC / ARR / CCRx

| Register | Meaning |
| --- | --- |
| `PSC` | Prescaler: `fCK_CNT = fCK_PSC / (PSC+1)` |
| `ARR` | Auto-reload: sets the period `T=(ARR+1)(PSC+1)/fCK_PSC` |
| `CCRx` | Capture/compare value: PWM duty `Duty=CCR/(ARR+1)` |

> Advanced timers TIM1/TIM8 also have `BDTR` (bit15 = MOE main output enable). If MOE is not set, there is no waveform output.

## 4. USART

### 4.1 USART_SR (status, offset 0x00)

| Bit | Name | Meaning |
| --- | --- | --- |
| `5` | RXNE | Receive data register not empty (data is available to read) |
| `6` | TC | Transmission complete (the whole frame has been sent) |
| `7` | TXE | Transmit data register empty (the next byte can be written) |
| `3` | ORE | Overrun error (clear by reading SR then DR) |
| `2` | NE | Noise error |
| `1` | FE | Framing error (stop bit is wrong) |
| `0` | PE | Parity error |

### 4.2 USART_DR (data, offset 0x04)

| Bit | Name | Meaning |
| --- | --- | --- |
| `[8:0]` | DR | Read/write transmit and receive data (low 8 bits are data; bit 9 is parity/address) |

### 4.3 USART_BRR (baud rate, offset 0x08)

| Bit | Name | Meaning |
| --- | --- | --- |
| `[15:4]` | DIV_Mantissa | Integer part of the baud-rate divider |
| `[3:0]` | DIV_Fraction | Fractional part (÷16) |

> Calculation: `USARTDIV = fCK / (16 × Baud)`; `BRR = (integer << 4) | round(fraction×16)`.

### 4.4 USART_CR1 (control 1, offset 0x0C)

| Bit | Name | Meaning |
| --- | --- | --- |
| `13` | UE | USART enable |
| `3` | TE | Transmit enable |
| `2` | RE | Receive enable |
| `5` | RXNEIE | Receive interrupt enable |
| `6` | TCIE | Transmission-complete interrupt enable |
| `7` | TXEIE | Transmit-register-empty interrupt enable |
| `12` | M | Word length: 0 = 8 bits, 1 = 9 bits |
| `10` | PCE | Parity enable |
| `9` | PS | Parity selection: 0 = even, 1 = odd |
| `4` | IDLEIE | Idle interrupt enable (used with DMA to detect the end of a frame) |

### 4.5 USART_CR2 / CR3 (offset 0x10 / 0x14)

| Register / bit | Name | Meaning |
| --- | --- | --- |
| `CR2[13:12]` | STOP | Stop bits: `00` = 1 `01` = 0.5 `10` = 2 `11` = 1.5 |
| `CR3[7]` | DMAR | Receive DMA enable |
| `CR3[6]` | DMAT | Transmit DMA enable |

## 5. NVIC

> Cortex-M core registers, starting at system control space `0xE000E100`. The HAL wraps them with `HAL_NVIC_*`.

### 5.1 NVIC_ISER / ICER (interrupt enable, offset 0x100 / 0x180)

| Register | Meaning |
| --- | --- |
| `ISERn` | Write 1 to enable the corresponding interrupt number (Set Enable) |
| `ICERn` | Write 1 to disable the corresponding interrupt number (Clear Enable) |
| `ISPRn` | Set the pending bit |
| `IABR` | Read the currently active interrupt |

`n = IRQn / 32`, bit = `IRQn % 32`. Example: EXTI0 (6) → bit6 of `ISER0`.

### 5.2 NVIC_IPR (priority, offset 0x400)

| Bit | Name | Meaning |
| --- | --- | --- |
| `IPR[7:4]` | Priority | On F1 the high 4 bits are valid; **a smaller value has higher priority** |

Priority grouping (`SCB->AIRCR.PRIGROUP`) decides how bits are split between preemption and subpriority. See the HAL `NVIC_PRIORITYGROUP_x`.

## 6. EXTI

| Register | Offset | Meaning |
| --- | --- | --- |
| `IMR` | 0x00 | Interrupt mask: write 1 to allow interrupt requests |
| `EMR` | 0x04 | Event mask: write 1 to allow event requests |
| `RTSR` | 0x08 | Rising-edge trigger enable |
| `FTSR` | 0x0C | Falling-edge trigger enable |
| `SWIER` | 0x10 | Software interrupt event (write 1 to trigger) |
| `PR` | 0x14 | Pending register (**write 1 to clear the flag**) |

> On F1, EXTI pin mapping is set by `AFIO_EXTICR1~4` (select PAx/PBx/PCx…); the AFIO clock must be enabled before configuration.

## 7. FLASH

| Register | Offset | Key bits |
| --- | --- | --- |
| `FLASH_ACR` | 0x00 | `[2:0]` LATENCY wait states (72MHz needs 2); `4` PRFTBE prefetch |
| `FLASH_KEYR` | 0x04 | Write `0x45670123` then `0xCDEF89AB` to unlock |
| `FLASH_SR` | 0x0C | `0` BSY busy; `5` EOP operation complete; `4` WRPRTERR; `2` PGERR |
| `FLASH_CR` | 0x10 | `0` PG program; `1` PER page erase; `6` STRT start; `7` LOCK lock |

> F4 differences: erase uses `CR.SER` + `SNB[3:0]` to select the sector; programming uses `CR.PSIZE` to select the width; the `KEYR` sequence is the same.

## Appendix: Common Memory Addresses

| Item | Address |
| --- | --- |
| Flash start | `0x0800 0000` |
| SRAM start | `0x2000 0000` |
| Peripheral region start | `0x4000 0000` |
| Bit-band alias region | `0x4200 0000` (peripheral) / `0x2200 0000` (SRAM) |
| SCB->VTOR | `0xE000 ED08` (vector table offset) |

> Related: [HAL Quick Reference](hal.md) · [Peripheral Bus and Pin Quick Reference](bus-and-pins.md) · [Error Code and Troubleshooting Quick Reference](errors.md)

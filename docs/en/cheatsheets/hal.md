# HAL Quick Reference

> 中文：[HAL 速查表](../../../cheatsheets/HAL速查表.md)

> Common HAL functions, grouped by module. Column meanings: **Function prototype / Purpose / Common parameters / Return value and error code**.
> Return values are uniformly `HAL_StatusTypeDef`: `HAL_OK` / `HAL_ERROR` / `HAL_BUSY` / `HAL_TIMEOUT` (see the [Error Code and Troubleshooting Quick Reference](errors.md)).
> Based on the STM32F1 HAL; F4 differences are noted in the remarks.

## Contents

| Module | Jump |
| --- | --- |
| System and clock | [§1](#1-system-and-clock-hal--rcc) |
| GPIO | [§2](#2-gpio-gpio) |
| EXTI / NVIC | [§3](#3-interrupts-exti--nvic--systick) |
| Timer TIM | [§4](#4-timers-tim) |
| Serial UART | [§5](#5-serial-usart-uart) |
| SPI | [§6](#6-spi-spi) |
| I2C | [§7](#7-i2c-i2c) |
| ADC / DAC | [§8](#8-adcdac-adcdac) |
| DMA | [§9](#9-dma-dma) |
| RTC / backup domain | [§10](#10-rtc-and-backup-domain-rtc--rtc_ex--pwr) |
| Flash / IAP | [§11](#11-flash-flash--flash_ex) |
| Watchdog | [§12](#12-watchdogs-iwdg--wwdg) |
| Common FreeRTOS macros | [§13](#13-common-freertos-macros) |

## 1. System and Clock (HAL / RCC)

| Function prototype | Purpose | Common parameters | Return value / error code |
| --- | --- | --- | --- |
| `HAL_Init(void)` | Initialize HAL, the Flash interface, and SysTick (1 ms) | none | `HAL_OK` |
| `HAL_DeInit(void)` | Reset all peripherals to the default state | none | `HAL_OK` |
| `HAL_Delay(uint32_t ms)` | Blocking delay (based on the SysTick interrupt) | milliseconds | none (void) |
| `HAL_GetTick(void)` | Get the number of milliseconds since startup | none | current tick value |
| `HAL_IncTick(void)` | Called by SysTick_Handler to increment the tick | none | none (do not call manually) |
| `HAL_RCC_OscConfig(RCC_OscInitTypeDef*)` | Configure HSE/HSI/LSE/LSI/PLL | `OscillatorType`,`HSEState`,`PLL.PLLMUL` | `HAL_OK/ERROR/TIMEOUT` (returns ERROR if HSE fails to start) |
| `HAL_RCC_ClockConfig(RCC_ClkInitTypeDef*, uint32_t lat)` | Configure SYSCLK/AHB/APB prescalers | `SYSCLKSource`,`AHBCLKDivider`,`APB1CLKDivider` | `HAL_OK/ERROR` (overclocking returns ERROR) |
| `HAL_RCCEx_PeriphCLKConfig(RCC_PeriphCLKInitTypeDef*)` | Configure peripheral clocks such as ADC/RTC/USB | `PeriphClockSelection`,`AdcClockSelection` | `HAL_OK/ERROR` |
| `HAL_RCC_GetHCLKFreq(void)` | Read the current AHB frequency | none | Hz |
| `HAL_RCC_GetPCLK1Freq(void)` | Read the current APB1 frequency | none | Hz |

## 2. GPIO (GPIO)

| Function prototype | Purpose | Common parameters | Return value / error code |
| --- | --- | --- | --- |
| `HAL_GPIO_Init(GPIO_TypeDef*, GPIO_InitTypeDef*)` | Initialize a pin (mode / pull-up-pull-down / speed) | `Pin`,`Mode`,`Pull`,`Speed`,`Alternate`(F4) | none (void) |
| `HAL_GPIO_DeInit(GPIO_TypeDef*, uint32_t Pin)` | Reset a pin to the default | `Pin` | none |
| `HAL_GPIO_WritePin(GPIOx, uint16_t Pin, GPIO_PinState st)` | Write a pin level | `GPIO_PIN_SET/RESET` | none |
| `HAL_GPIO_ReadPin(GPIOx, uint16_t Pin)` | Read a pin level | `Pin` | `GPIO_PIN_SET/RESET` |
| `HAL_GPIO_TogglePin(GPIOx, uint16_t Pin)` | Toggle a pin | `Pin` | none |
| `HAL_GPIO_LockPin(GPIOx, uint16_t Pin)` | Lock the pin configuration | `Pin` | `HAL_OK` |
| `HAL_GPIO_EXTI_IRQHandler(uint16_t Pin)` | EXTI interrupt handler (clear the flag + callback) | `Pin` | none |

**Common macros**: `GPIO_MODE_INPUT/OUTPUT_PP/OUTPUT_OD/ANALOG/AF_PP/AF_OD/IT_RISING/IT_FALLING/IT_RISING_FALLING`,
`GPIO_PULLUP/PULLDOWN/NOPULL`, `GPIO_SPEED_FREQ_LOW/MEDIUM/HIGH/VERY_HIGH`.

## 3. Interrupts (EXTI / NVIC / SysTick)

| Function prototype | Purpose | Common parameters | Return value / error code |
| --- | --- | --- | --- |
| `HAL_NVIC_SetPriority(IRQn_Type, uint32_t pre, uint32_t sub)` | Set preemption / subpriority | `IRQn`,`pre`,`sub` (a smaller number has higher priority) | none |
| `HAL_NVIC_EnableIRQ(IRQn_Type)` | Enable an interrupt line | `IRQn` | none |
| `HAL_NVIC_DisableIRQ(IRQn_Type)` | Disable an interrupt line | `IRQn` | none |
| `HAL_NVIC_SetPriorityGrouping(uint32_t g)` | Set the priority grouping | `NVIC_PRIORITYGROUP_0..4` | none |
| `HAL_NVIC_SystemReset(void)` | System reset | none | does not return |
| `__disable_irq()/__enable_irq()` | Disable / enable global interrupts (critical section) | none | none |
| `__HAL_GPIO_EXTI_GET_IT(Pin)` | Read the EXTI pending flag | `Pin` | nonzero = an event is pending |
| `__HAL_GPIO_EXTI_CLEAR_IT(Pin)` | Clear the EXTI pending flag | `Pin` | none |
| `HAL_SuspendTick()/HAL_ResumeTick()` | Suspend / resume SysTick | none | none |

## 4. Timers (TIM)

| Function prototype | Purpose | Common parameters | Return value / error code |
| --- | --- | --- | --- |
| `HAL_TIM_Base_Init(TIM_HandleTypeDef*)` | Initialize the time base (PSC/ARR) | `Init.Prescaler`,`Init.Period` | `HAL_OK/ERROR` |
| `HAL_TIM_Base_Start(TIM_HandleTypeDef*)` | Start counting (polling) | — | `HAL_OK/BUSY` |
| `HAL_TIM_Base_Start_IT(TIM_HandleTypeDef*)` | Start counting + update interrupt | — | `HAL_OK/BUSY` |
| `HAL_TIM_PWM_Init(TIM_HandleTypeDef*)` | Initialize the PWM time base | same as Base | `HAL_OK/ERROR` |
| `HAL_TIM_PWM_ConfigChannel(TIM*, TIM_OC_InitTypeDef*, uint32_t ch)` | Configure a PWM channel | `OCMode`,`Pulse`,`OCPolarity` | `HAL_OK/ERROR` |
| `HAL_TIM_PWM_Start(TIM*, uint32_t ch)` | Start PWM output (including MOE) | `TIM_CHANNEL_x` | `HAL_OK/BUSY/ERROR` |
| `HAL_TIM_PWM_Stop(TIM*, uint32_t ch)` | Stop PWM | `ch` | `HAL_OK/ERROR` |
| `HAL_TIM_IC_Start_IT(TIM*, uint32_t ch)` | Start input capture + interrupt | `ch` | `HAL_OK/BUSY` |
| `HAL_TIM_OC_Start(TIM*, uint32_t ch)` | Start output compare | `ch` | `HAL_OK/BUSY` |

**Common macros**: `__HAL_TIM_SET_COMPARE(&h,ch,ccr)`, `__HAL_TIM_GET_COMPARE(&h,ch)`,
`__HAL_TIM_SET_COUNTER`, `__HAL_TIM_GET_COUNTER`, `__HAL_TIM_MOE_ENABLE(&h)` (advanced timers),
`__HAL_TIM_SET_AUTORELOAD`, `TIM_OCMODE_PWM1/PWM2`, `TIM_OCPOLARITY_HIGH/LOW`.

## 5. Serial USART (UART)

| Function prototype | Purpose | Common parameters | Return value / error code |
| --- | --- | --- | --- |
| `HAL_UART_Init(UART_HandleTypeDef*)` | Initialize UART | `BaudRate`,`WordLength`,`StopBits`,`Parity` | `HAL_OK/ERROR` |
| `HAL_UART_Transmit(UART*, uint8_t*, uint16_t, uint32_t to)` | Blocking transmit | `buf`,`len`,`timeout` | `HAL_OK/BUSY/TIMEOUT/ERROR` |
| `HAL_UART_Receive(UART*, uint8_t*, uint16_t, uint32_t to)` | Blocking receive | `buf`,`len`,`timeout` | `HAL_OK/BUSY/TIMEOUT/ERROR` |
| `HAL_UART_Transmit_IT / Receive_IT` | Interrupt-mode transmit and receive | same as above (no timeout) | `HAL_OK/BUSY/ERROR` |
| `HAL_UART_Transmit_DMA / Receive_DMA` | DMA-mode transmit and receive | same as above (no timeout) | `HAL_OK/BUSY/ERROR` |
| `HAL_UARTEx_ReceiveToIdle_DMA(UART*, uint8_t*, uint16_t)` | Variable-length receive with DMA + idle interrupt | `buf`,`len` | `HAL_OK/BUSY/ERROR` |
| `HAL_UART_IRQHandler(UART*)` | Unified interrupt entry (place it in `USARTx_IRQHandler`) | — | none |
| `HAL_UART_Abort(UART*)` | Abort transmit/receive and reset the state | — | `HAL_OK/ERROR` |
| `__HAL_UART_CLEAR_OREFLAG(UART*)` | Clear the overrun flag | — | none |
| `__HAL_UART_CLEAR_FEFLAG(UART*)` | Clear the framing-error flag | — | none |

**Callbacks**: `HAL_UART_RxCpltCallback`, `HAL_UART_TxCpltCallback`, `HAL_UARTEx_RxEventCallback`, `HAL_UART_ErrorCallback`.

## 6. SPI (SPI)

| Function prototype | Purpose | Common parameters | Return value / error code |
| --- | --- | --- | --- |
| `HAL_SPI_Init(SPI_HandleTypeDef*)` | Initialize SPI | `Mode`,`CLKPolarity`,`CLKPhase`,`NSS`,`BaudRatePrescaler` | `HAL_OK/ERROR` |
| `HAL_SPI_Transmit(SPI*, uint8_t*, uint16_t, uint32_t)` | Blocking transmit | `buf`,`len`,`timeout` | `HAL_OK/BUSY/TIMEOUT/ERROR` |
| `HAL_SPI_Receive(SPI*, uint8_t*, uint16_t, uint32_t)` | Blocking receive | same as above | same as above |
| `HAL_SPI_TransmitReceive(SPI*, uint8_t*, uint8_t*, uint16_t, uint32_t)` | Full-duplex transmit and receive | `tx`,`rx`,`len`,`timeout` | same as above |
| `HAL_SPI_Transmit_IT / TransmitReceive_IT` | Interrupt mode | same as blocking (no timeout) | `HAL_OK/BUSY/ERROR` |
| `HAL_SPI_TransmitReceive_DMA(SPI*, uint8_t*, uint8_t*, uint16_t)` | DMA full duplex | `tx`,`rx`,`len` | `HAL_OK/BUSY/ERROR` |

**Common macros**: `SPI_MODE_MASTER/SLAVE`, `SPI_POLARITY_LOW/HIGH`, `SPI_PHASE_1EDGE/2EDGE`,
`SPI_NSS_SOFT/HARD`, `SPI_BAUDRATEPRESCALER_2..256`, `SPI_FIRSTBIT_MSB/LSB`, `SPI_DATASIZE_8BIT/16BIT`.
**Mode mapping**: mode 0 = CPOL0+CPHA0; mode 1 = CPOL0+CPHA1; mode 2 = CPOL1+CPHA0; mode 3 = CPOL1+CPHA1.

## 7. I2C (I2C)

| Function prototype | Purpose | Common parameters | Return value / error code |
| --- | --- | --- | --- |
| `HAL_I2C_Init(I2C_HandleTypeDef*)` | Initialize I2C | `ClockSpeed`,`DutyCycle`,`AddressingMode` | `HAL_OK/ERROR` |
| `HAL_I2C_Master_Transmit(I2C*, uint16_t addr, uint8_t*, uint16_t, uint32_t)` | Master transmit | `addr` (8-bit, already left-shifted),`buf`,`len`,`timeout` | `HAL_OK/BUSY/TIMEOUT/ERROR` |
| `HAL_I2C_Master_Receive(I2C*, uint16_t, uint8_t*, uint16_t, uint32_t)` | Master receive | same as above | same as above |
| `HAL_I2C_Mem_Write(I2C*, addr, memaddr, memsize, buf, len, to)` | Write a register | `MemAddress`,`MemAddSize` | same as above |
| `HAL_I2C_Mem_Read(I2C*, addr, memaddr, memsize, buf, len, to)` | Read a register | same as above | same as above |
| `HAL_I2C_IsDeviceReady(I2C*, addr, trials, to)` | Probe whether the slave acknowledges | `Trials`,`Timeout` | `HAL_OK/BUSY/TIMEOUT/ERROR` |
| `HAL_I2C_Master_Transmit_DMA(...)` | DMA-mode transmit | same as blocking (no timeout) | `HAL_OK/BUSY/ERROR` |
| `HAL_I2C_DeInit(I2C*)` | Reset I2C (used when recovering the bus) | — | `HAL_OK` |

**Common macros**: `I2C_ADDRESSINGMODE_7BIT/10BIT`, `I2C_DUTYCYCLE_2/16_9`, `I2C_DUALADDRESS_DISABLE/ENABLE`, `I2C_NOSTRETCH_DISABLE/ENABLE`.

## 8. ADC/DAC (ADC/DAC)

| Function prototype | Purpose | Common parameters | Return value / error code |
| --- | --- | --- | --- |
| `HAL_ADC_Init(ADC_HandleTypeDef*)` | Initialize ADC | `ScanConvMode`,`ContinuousConvMode`,`DataAlign`,`NbrOfConversion` | `HAL_OK/ERROR` |
| `HAL_ADC_ConfigChannel(ADC*, ADC_ChannelConfTypeDef*)` | Configure a regular-group channel | `Channel`,`Rank`,`SamplingTime` | `HAL_OK/ERROR` |
| `HAL_ADCEx_Calibration_Start(ADC*)` | ADC calibration (required after power-up) | — | `HAL_OK/ERROR` |
| `HAL_ADC_Start(ADC*)` | Start conversion (polling) | — | `HAL_OK/BUSY` |
| `HAL_ADC_Start_DMA(ADC*, uint32_t*, uint32_t)` | Start + DMA | `buf`,`len` | `HAL_OK/BUSY/ERROR` |
| `HAL_ADC_PollForConversion(ADC*, uint32_t to)` | Poll until conversion completes | `timeout` | `HAL_OK/TIMEOUT/ERROR` |
| `HAL_ADC_GetValue(ADC*)` | Read the conversion result | — | 12-bit code |
| `HAL_ADC_Stop_DMA(ADC*)` | Stop DMA acquisition | — | `HAL_OK/ERROR` |
| `HAL_DAC_Start(DAC_HandleTypeDef*, uint32_t ch)` | Start DAC output | `DAC_CHANNEL_1/2` | `HAL_OK/ERROR` |
| `HAL_DAC_SetValue(DAC*, ch, align, value)` | Set the output value | `DAC_ALIGN_12B_R`,`0..4095` | `HAL_OK/ERROR` |
| `HAL_DAC_Start_DMA(DAC*, ch, buf, len, align)` | DMA update (arbitrary waveform) | `buf`,`len` | `HAL_OK/ERROR` |

**Common macros**: `ADC_SAMPLETIME_1CYCLE_5 ... _239CYCLES_5`, `ADC_CHANNEL_0..17`,
`ADC_DATAALIGN_RIGHT/LEFT`, `ADC_EXTERNALTRIGCONV_Tx_TRGO`, `ADC_SOFTWARE_START`.

## 9. DMA (DMA)

| Function prototype | Purpose | Common parameters | Return value / error code |
| --- | --- | --- | --- |
| `HAL_DMA_Init(DMA_HandleTypeDef*)` | Initialize a DMA channel/stream | `Direction`,`PeriphInc`,`MemInc`,`Mode`,`Priority` | `HAL_OK/ERROR` |
| `HAL_DMA_Start(DMA*, uint32_t src, uint32_t dst, uint32_t len)` | Start one transfer | `src`,`dst`,`len` | `HAL_OK/ERROR` |
| `HAL_DMA_Start_IT(DMA*, src, dst, len)` | Start + interrupt | same as above | `HAL_OK/ERROR` |
| `HAL_DMA_PollForTransfer(DMA*, level, uint32_t to)` | Poll until complete | `HAL_DMA_FULL_TRANSFER`,`timeout` | `HAL_OK/TIMEOUT/ERROR` |
| `HAL_DMA_Abort(DMA*)` | Abort the transfer | — | `HAL_OK/ERROR` |
| `__HAL_LINKDMA(handle, field, dma_handle)` | Associate DMA with a peripheral handle | `field`=`hdmatx/hdmarx` | none |

**Common macros**: `DMA_MEMORY_TO_PERIPH/PERIPH_TO_MEMORY/MEMORY_TO_MEMORY`, `DMA_PINC_ENABLE/DISABLE`,
`DMA_MINC_ENABLE/DISABLE`, `DMA_NORMAL/CIRCULAR`, `DMA_PRIORITY_LOW..VERY_HIGH`,
`DMA_PDATAALIGN_BYTE/HALFWORD/WORD`, `DMA_MDATAALIGN_*`.


## 10. RTC and Backup Domain (RTC / RTC_EX / PWR)

| Function prototype | Purpose | Common parameters | Return value / error code |
| --- | --- | --- | --- |
| `HAL_RTC_Init(RTC_HandleTypeDef*)` | Initialize RTC | `AsynchPrediv`,`OutPut` | `HAL_OK/ERROR` |
| `HAL_RTC_SetTime/GetTime(RTC*, RTC_TimeTypeDef*, fmt)` | Set / read the time | `RTC_FORMAT_BIN/BCD` | `HAL_OK/ERROR` |
| `HAL_RTC_SetDate/GetDate(RTC*, RTC_DateTypeDef*, fmt)` | Set / read the date | same as above | `HAL_OK/ERROR` |
| `HAL_RTC_SetAlarm_IT(RTC*, RTC_AlarmTypeDef*, fmt)` | Set an alarm (interrupt) | `AlarmTime`,`AlarmMask` | `HAL_OK/ERROR` |
| `HAL_RTC_DeactivateAlarm(RTC*, uint32_t)` | Disable an alarm | `RTC_ALARM_A/B` | `HAL_OK/ERROR` |
| `HAL_RTCEx_BKUPWrite(RTC*, uint32_t reg, uint32_t val)` | Write a backup register | `RTC_BKP_DRx` | none |
| `HAL_RTCEx_BKUPRead(RTC*, uint32_t reg)` | Read a backup register | `RTC_BKP_DRx` | register value |
| `HAL_PWR_EnableBkUpAccess(void)` | Unlock the backup domain (before writing RTC/BKP) | none | none |
| `HAL_PWR_EnterSTOPMode(uint32_t reg, uint32_t entry)` | Enter STOP mode | `PWR_LOWPOWERREGULATOR_ON`,`PWR_STOPENTRY_WFI` | none |

**Callbacks**: `HAL_RTC_AlarmAEventCallback`, `HAL_RTC_AlarmBEventCallback`, `HAL_RTCEx_WakeUpTimerEventCallback` (F4).

## 11. Flash (FLASH / FLASH_EX)

| Function prototype | Purpose | Common parameters | Return value / error code |
| --- | --- | --- | --- |
| `HAL_FLASH_Unlock(void)` | Unlock Flash (KEY1/KEY2) | none | `HAL_OK/ERROR` |
| `HAL_FLASH_Lock(void)` | Lock Flash | none | `HAL_OK/ERROR` |
| `HAL_FLASHEx_Erase(FLASH_EraseInitTypeDef*, uint32_t* err)` | Erase pages/sectors | `TypeErase`,`PageAddress`,`NbPages` | `HAL_OK/ERROR/TIMEOUT` |
| `HAL_FLASH_Program(uint32_t type, uint32_t addr, uint64_t data)` | Program | `FLASH_TYPEPROGRAM_HALFWORD/WORD/DOUBLEWORD` | `HAL_OK/ERROR/BUSY` |
| `HAL_FLASHEx_OBProgram(FLASH_OBProgramInitTypeDef*)` | Program option bytes | — | `HAL_OK/ERROR` |
| `HAL_FLASH_GetError(void)` | Read error flags | — | bit mask |

**F1**: erase is in pages (low-density 1KB, high-density 2KB); programming is in halfwords.
**F4**: erase is in sectors (16/64/128KB); programming supports byte/halfword/word/doubleword.

## 12. Watchdogs (IWDG / WWDG)

| Function prototype | Purpose | Common parameters | Return value / error code |
| --- | --- | --- | --- |
| `HAL_IWDG_Init(IWDG_HandleTypeDef*)` | Initialize the independent watchdog | `Prescaler`,`Reload` | `HAL_OK/ERROR` |
| `HAL_IWDG_Refresh(IWDG*)` | Feed the watchdog | — | `HAL_OK/ERROR` |
| `HAL_WWDG_Init(WWDG_HandleTypeDef*)` | Initialize the window watchdog | `Prescaler`,`Window`,`Counter` | `HAL_OK/ERROR` |
| `HAL_WWDG_Refresh(WWDG*)` | Feed the watchdog (must be inside the window) | — | `HAL_OK/ERROR` |

**Common macros**: `IWDG_PRESCALER_4..256`, `WWDG_PRESCALER_1..8`, `WWDG_EWI_ENABLE/DISABLE`.

## 13. Common FreeRTOS Macros

| Macro / function | Purpose | Common parameters | Notes |
| --- | --- | --- | --- |
| `xTaskCreate(fn, name, stack, arg, prio, handle)` | Create a task | `stack` is in words (4B) | returns `pdPASS/pdFAIL` |
| `vTaskDelete(handle)` | Delete a task | `NULL` = delete itself | no return |
| `vTaskDelay(ticks)` | Blocking delay | `pdMS_TO_TICKS(ms)` | yields the CPU |
| `xTaskGetTickCount()` | Get the tick count | none | returns TickType_t |
| `xQueueCreate(len, item_size)` | Create a queue | `len`,`item_size` | returns a handle or NULL |
| `xQueueSend/Receive(q, &item, ticks)` | Queue send / receive | `portMAX_DELAY` = wait forever | `pdTRUE/pdFALSE` |
| `xQueueSendFromISR(q, &item, &woken)` | Send from an interrupt | `woken` = whether to wake a task | `pdTRUE/pdFALSE` |
| `xSemaphoreCreateMutex/Binary()` | Create a mutex / binary semaphore | — | returns a handle |
| `xSemaphoreTake/Give(sem, ticks)` | Take / give a semaphore | `ticks` | `pdTRUE/pdFALSE` |
| `xSemaphoreGiveFromISR(sem, &woken)` | Give from an interrupt | `woken` | `pdTRUE/pdFALSE` |
| `portYIELD_FROM_ISR(woken)` | Trigger a switch at the end of an interrupt | `woken` | none |
| `pdMS_TO_TICKS(ms)` | Convert milliseconds to ticks | `ms` | depends on `configTICK_RATE_HZ` |
| `configASSERT(x)` | Assert (priority / parameter checks) | condition | failure enters an infinite loop |
| `taskENTER_CRITICAL()/EXIT()` | Task-level critical section | none | protection by disabling interrupts |

> Related: [Register Quick Reference](registers.md) · [Peripheral Bus and Pin Quick Reference](bus-and-pins.md) · [Error Code and Troubleshooting Quick Reference](errors.md)

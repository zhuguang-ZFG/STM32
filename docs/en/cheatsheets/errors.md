# Error Code and Troubleshooting Quick Reference

> 中文：[错误码与排查速查表](../../../cheatsheets/错误码与排查速查表.md)

> Meanings of HAL return values and state-machine enumerations, plus a quick reference of symptom → cause → how to locate.
> First rule of troubleshooting: **confirm clock and power first**, then peripheral configuration, then timing and wiring.

## Contents

| Section | Contents |
| --- | --- |
| [§1](#1-hal-return-value-meanings) | HAL return values (HAL_StatusTypeDef) |
| [§2](#2-hal-state-enumeration) | HAL state machine (HAL_StateTypeDef) |
| [§3](#3-module-error-flags) | FLASH/I2C/UART error flags |
| [§4](#4-common-symptoms--causes--how-to-locate) | 30+ symptom troubleshooting entries |

## 1. HAL Return Value Meanings

`HAL_StatusTypeDef` is the unified return value of all HAL functions (some functions return void or a specific numeric value).

| Return value | Value | Meaning | Typical trigger |
| --- | --- | --- | --- |
| `HAL_OK` | 0x00 | Operation succeeded | Completed normally |
| `HAL_ERROR` | 0x01 | General error | Illegal parameter, peripheral configuration failed, HSE failed to start, abnormal hardware response |
| `HAL_BUSY` | 0x02 | Peripheral busy | A new transfer was started before the previous one finished; DMA/interrupt mode has not ended |
| `HAL_TIMEOUT` | 0x03 | Timeout | Timed out waiting for a flag (for example, waiting for TXE/BSY/RXNE past timeout) |

**Handling advice**:

| Return value | Suggested action |
| --- | --- |
| `HAL_OK` | Continue |
| `HAL_BUSY` | Wait / retry; check whether the previous completion was not awaited or the state was not reset |
| `HAL_TIMEOUT` | Check the clock, wiring, whether the slave acknowledges, and whether timeout is too short |
| `HAL_ERROR` | Check parameter validity, whether the peripheral clock is enabled, and whether the hardware is present |

## 2. HAL State Enumeration

`HAL_StateTypeDef` describes the current state of a peripheral handle (`hxxx.State`). It is the most direct thing to inspect while debugging.

| State | Value | Meaning |
| --- | --- | --- |
| `HAL_STATE_RESET` | 0x00 | Peripheral not initialized (default after reset) |
| `HAL_STATE_READY` | 0x01 | Initialized and idle; an operation can be started |
| `HAL_STATE_BUSY` | 0x02 | An operation is in progress (generic) |
| `HAL_STATE_BUSY_TX` | 0x21 | Transmitting |
| `HAL_STATE_BUSY_RX` | 0x22 | Receiving |
| `HAL_STATE_BUSY_TX_RX` | 0x23 | Full-duplex transmit and receive in progress |
| `HAL_STATE_TIMEOUT` | 0x03 | The previous operation timed out |
| `HAL_STATE_ERROR` | 0x04 | The previous operation failed |

> Typical pitfall: `HAL_UART_Transmit_IT` returns `HAL_BUSY`, which means the previous transmit has not finished (`State` is still `BUSY_TX`).

## 3. Module Error Flags

### 3.1 FLASH (`HAL_FLASH_GetError()`)

| Flag | Meaning |
| --- | --- |
| `HAL_FLASH_ERROR_NONE` | No error |
| `HAL_FLASH_ERROR_PG` | Programming error (write without erase, or address not aligned) |
| `HAL_FLASH_ERROR_WRP` | Write-protection error (the target page is write-protected) |
| `HAL_FLASH_ERROR_OPERATION` | Operation error (a new operation was started before BSY was cleared) |

### 3.2 I2C (`HAL_I2C_GetError()`)

| Flag | Meaning |
| --- | --- |
| `HAL_I2C_ERROR_NONE` | No error |
| `HAL_I2C_ERROR_BERR` | Bus error (illegal start/stop condition) |
| `HAL_I2C_ERROR_ARLO` | Arbitration lost (multi-master contention) |
| `HAL_I2C_ERROR_AF` | Acknowledge failure (slave did not ACK: wrong address / not present / missing pull-up) |
| `HAL_I2C_ERROR_OVR` | Overrun |
| `HAL_I2C_ERROR_TIMEOUT` | Timeout |

### 3.3 UART (`HAL_UART_GetError()`)

| Flag | Meaning |
| --- | --- |
| `HAL_UART_ERROR_NONE` | No error |
| `HAL_UART_ERROR_PE` | Parity error |
| `HAL_UART_ERROR_NE` | Noise error (baud rate / line length) |
| `HAL_UART_ERROR_FE` | Framing error (stop bit / baud rate mismatch) |
| `HAL_UART_ERROR_ORE` | Overrun (received too fast and was not read in time) |
| `HAL_UART_ERROR_DMA` | DMA transfer error |

## 4. Common Symptoms → Causes → How to Locate

| # | Symptom | Cause | How to locate |
| --- | --- | --- | --- |
| 1 | Program stops in `Error_Handler` right after power-up | Clock configuration failed (HSE failed to start) | Probe OSC_IN with an oscilloscope; switch to HSI or replace the crystal / load capacitors |
| 2 | LED does not light at all | GPIO clock not enabled | Check `__HAL_RCC_GPIOx_CLK_ENABLE()` |
| 3 | Writes to a peripheral register have no effect | Peripheral clock not enabled | Check the corresponding bit in `RCC->APBxENR` |
| 4 | Cannot connect again after programming | SWD pins PA13/PA14 were reused as GPIO | In CubeMX set SYS to Serial Wire; pull BOOT0 high to enter system memory |
| 5 | Interrupt never enters | NVIC not enabled / EXTI not configured | Check `HAL_NVIC_EnableIRQ` and `GPIO_MODE_IT_xxx` |
| 6 | Keeps re-entering the interrupt | Forgot to clear the interrupt flag | Call `__HAL_GPIO_EXTI_CLEAR_IT` or the HAL handler in the ISR |
| 7 | One key press triggers multiple times | Mechanical bounce | Add 10~20ms software debounce or an RC filter |
| 8 | Program hangs inside the interrupt | `HAL_Delay` / `printf` called in the interrupt | Only set a flag in the interrupt; put time-consuming work in the main loop |
| 9 | Timer has no waveform output | Advanced timer MOE not enabled | `HAL_TIM_PWM_Start` or `__HAL_TIM_MOE_ENABLE` |
| 10 | PWM frequency is wrong | PSC/ARR calculated wrong or the clock tree is wrong | Recheck with `f=fCK/((ARR+1)(PSC+1))`; measure the actual frequency |
| 11 | PWM jitters when the duty cycle changes | Preload not enabled | Enable `AutoReloadPreload` / `OCxPE` |
| 12 | UART output is garbled | Baud rate mismatch / wrong clock / no common ground | Use the same baud rate on both sides; confirm PCLK; connect GND |
| 13 | UART receives only once then stops | DMA receive was not restarted in the callback | Call `ReceiveToIdle_DMA` again inside the callback |
| 14 | UART hangs after an overrun | ORE flag not handled | Clear the flag and restart in `HAL_UART_ErrorCallback` |
| 15 | I2C slave does not acknowledge (AF) | Wrong address / missing pull-up / slave not present | Probe with `HAL_I2C_IsDeviceReady`; check the 4.7kΩ pull-up |
| 16 | I2C dies completely after an occasional failure | Slave holds SDA low and deadlocks the bus | Manually clock 9 pulses to unlock (see the i2c-oled example) |
| 17 | SPI reads back all 0xFF | MISO not connected / slave not powered | Check DO/DI wiring and power |
| 18 | SPI reads back all 0x00 | CS not pulled low / wrong mode | Check chip select; verify CPOL/CPHA |
| 19 | SPI data is shifted | Wrong MSB/LSB order or data width | Set `SPI_FIRSTBIT_MSB` and check the bit width |
| 20 | ADC reading is stuck at 0 | Pin not configured as Analog / no signal connected | Set GPIO to `GPIO_MODE_ANALOG` |
| 21 | ADC reading jitters a lot | Sampling time too short / source impedance too high | Increase the sampling time and add filtering |
| 22 | ADC accuracy is poor | VDDA is not an accurate 3.3V | Read Vrefint and back-calculate the real VDDA for calibration |
| 23 | DMA transfers no data at all | Wrong channel/stream mapping | Check the request map; on F4 also set `CHSEL` |
| 24 | DMA transfers once then stops | Circular mode was needed but normal mode was configured | Change to `DMA_CIRCULAR` |
| 25 | DMA data is misaligned | Address not incremented or width mismatch | Check `MINC`/`PINC` and `PSIZE`/`MSIZE` |
| 26 | RTC time does not advance | LSE failed to start / VBAT not connected | Change to 6pF capacitors; connect a coin cell |
| 27 | Watchdog resets frequently | Feed interval > timeout | Calculate the timeout; feed periodically in the loop |
| 28 | Hangs after jumping to the APP | MSP not set / VTOR not set | `__set_MSP` + `SCB->VTOR = APP_ADDR` |
| 29 | Flash programming returns ERROR | Not erased / not aligned / not unlocked | Erase the whole page first; halfword alignment; `HAL_FLASH_Unlock` |
| 30 | FreeRTOS stuck at scheduler start | HAL time base and RTOS both claim SysTick | In CubeMX change the time-base source to TIMx |
| 31 | FreeRTOS `configASSERT` infinite loop | Interrupt priority number is too small | Interrupt priority ≥ `configMAX_SYSCALL_INTERRUPT_PRIORITY` |
| 32 | Entered HardFault | Null pointer / array out of bounds / stack overflow / divide by zero | Check `CFSR/HFSR`; print from `HardFault_Handler`; increase the task stack |
| 33 | UART garbled after low-power wakeup | Clock returns to HSI after STOP | Call `SystemClock_Config()` again after wakeup |
| 34 | Program dies after running for a while | Stack overflow / watchdog not fed / interrupt storm | Increase the stack; enable the watchdog; count interrupt frequency |

## 5. Quick Troubleshooting Flow (Mnemonic)

| Step | Check |
| --- | --- |
| 1. Power and ground | Is 3.3V stable? Common ground? Is VDDA connected? |
| 2. Clock | Did HSE/LSE start? Is the SYSCLK frequency correct? Is the peripheral clock enabled? |
| 3. Pins | Is the alternate function correct? Any conflict? Is pull-up/pull-down needed? |
| 4. Configuration | Are mode and parameters correct? Are prescaler/divider correct? |
| 5. Timing | Are baud rate / CPOL-CPHA / sampling time / timeout correct? |
| 6. Interrupts | NVIC enabled? Priority? Flag cleared? |
| 7. Tools | Use a debugger to view registers, a logic analyzer for waveforms, and SWO for prints |

## 5. Common Compile and Link Errors

| Error | Cause | Fix |
| --- | --- | --- |
| `undefined reference to 'HAL_XXX'` | The corresponding `stm32f1xx_hal_xxx.c` was not added to the project | Enable the HAL module in the IDE, or add the source file |
| `multiple definition of 'XXX_IRQHandler'` | You wrote an interrupt function and also kept the generated one | Delete the duplicate definition (keep one) |
| `'XXX' undeclared` | Missing header / typo / module not included | `#include` the header; check case |
| `implicit declaration of function` | Function not declared (missing header or forgotten prototype) | Add `#include` or a function prototype |
| `region RAM/FLASH overflowed` | Program exceeds capacity | Reduce size; check for an accidentally large array; change the linker script |
| `cannot open source input file "xxx.h"` | Header search path not configured | Add Include Paths in the project |
| `call to non-static member...` (C++) | C++ syntax was used in a .c file | Use plain C, or wrap with `extern "C"` |
| `use of undeclared identifier 'GPIO_PIN_13'` | Did not include `stm32f1xx_hal.h` or the device header | Confirm the device macro (for example `STM32F103xB`) is defined |

## 6. HardFault Location Registers

> After entering `HardFault_Handler`, look at `SCB->CFSR` first, then `SCB->BFAR` / `MMFAR`.

| Register | Bit / field | Meaning |
| --- | --- | --- |
| `SCB->CFSR` | `[7:0]` MMFSR | Memory management fault (illegal access) |
| `SCB->CFSR` | `[15:8]` BFSR | Bus fault (for example, accessing a peripheral whose clock is not enabled) |
| `SCB->CFSR` | `[31:16]` UFSR | Usage fault (unaligned access, divide by zero, illegal instruction) |
| `SCB->HFSR` | bit30 `FORCED` | HardFault escalated from another fault |
| `SCB->BFAR` | Address | Address that triggered the bus fault (when `BFSR.BFARVALID` is valid) |
| `SCB->MMFAR` | Address | Address that triggered the memory management fault |
| Stack frame | `R0~R3,R12,LR,PC,xPSR` | Fault context taken from MSP/PSP (PC = the faulting instruction) |

**Location steps**: ① Read `PC` from the stack frame; ② use `addr2line` or the IDE disassembly to find the source line;
③ common root causes: accessing a register before the peripheral clock is enabled (BFSR), array out of bounds (MMFSR), divide by zero / unaligned access (UFSR).

## 7. Debug Tools and Methods

| Method | Use | When it applies |
| --- | --- | --- |
| SWD + breakpoint / single-step | View variables and single-step | Logic errors and flow problems |
| Debugger register / peripheral view | Look directly at RCC/GPIO/TIM registers | Suspect the clock or configuration did not take effect |
| Logic analyzer | Capture SPI/I2C/UART timing waveforms | Last resort when communication fails |
| Oscilloscope | Measure clock, PWM, and supply ripple | Failure to oscillate, wrong frequency, interference |
| SWO/ITM printf | Print tracing that does not use the UART | High real-time requirements, or the UART is already in use |
| UART printf | Print runtime status | General debugging (remember to redirect `fputc`) |
| GPIO toggle + oscilloscope | Measure function duration | Performance analysis (together with DWT) |
| `__NOP()` + single-step | Precise timing observation | Microsecond-level timing |

## 8. Asserts and Common Macro Switches

| Macro / mechanism | Purpose | Notes |
| --- | --- | --- |
| `assert_param(expr)` | HAL parameter check | Takes effect when `USE_FULL_ASSERT` is enabled |
| `USE_FULL_ASSERT` | Enable HAL asserts | On failure, enters `assert_failed()`, which helps find bad parameters |
| `configASSERT(x)` | FreeRTOS assert | Enters an infinite loop on a priority or parameter error |
| `Error_Handler()` | User error handler | Stops when clock or peripheral init fails, which helps debugging |
| `__disable_irq()` | Disable interrupts | Critical section; do not stay inside for long |
| `NVIC_SystemReset()` | Software reset | Watchdog / exception recovery |

> Related: [HAL Quick Reference](hal.md) · [Register Quick Reference](registers.md) · [Peripheral Bus and Pin Quick Reference](bus-and-pins.md)

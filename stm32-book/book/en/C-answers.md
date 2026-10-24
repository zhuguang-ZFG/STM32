# Answers to the chapter self-tests

Answer on your own first. These notes only give the reason. Register bits and electrical values still go back to the manual for the exact part.

## 00 How to Learn STM32

1. With BOOT0 low, the part boots from main Flash.
2. HAL adds a handle, a state machine, parameter checks, and a more uniform API above the registers. It does not remove the clock, pin, and register constraints.
3. The first win is one LED blinking at a frequency **you calculated and measured**, not an LED that merely turned on.

## 01 Setting Up the Development Environment

1. The first word of the vector table is the initial stack, loaded into MSP after reset.
2. The second word is the address of `Reset_Handler`. The least significant bit marks Thumb state.
3. SWD uses PA13/SWDIO and PA14/SWCLK, plus a common ground and a supply reference.

## 02 Part Number, Memory, and Clocks

1. An F103 at 72 MHz needs the Flash wait states for its voltage range. The example in this book uses 2 WS. The Flash table in RM0008 is the authority.
2. AHB/HCLK is faster than APB1. In the usual 72 MHz setup, APB1 is 36 MHz.
3. If the peripheral clock gate is closed, writes do not produce the hardware behavior you expect. A read may still show the reset value.

## 03 GPIO and the LED

1. The onboard LED on BluePill PC13 is usually on when the pin is low.
2. A switch to GND uses a pull-up: released reads 1, pressed reads 0.
3. On F1, enable the AFIO clock before a remap, and keep the pins SWD needs.

## 04 Interrupts and the NVIC

1. EXTI0 can select only one port source at a time, such as PA0 or PB0.
2. A blocking delay stretches the time interrupts are masked or nested. An ISR stays bounded and returns.
3. PRIMASK is the gate for configurable-priority interrupts. BASEPRI masks by a priority threshold. FAULTMASK also masks most faults. NMI is outside these ordinary masks.

## 05 Timers and PWM

1. PSC and ARR together set the update period: `f_update = f_tim / ((PSC+1)(ARR+1))` for the basic up-counting case.
2. CCR sets the compare point, and therefore the PWM duty or the output-compare instant.
3. Input capture latches CNT at the edge. It does not latch a voltage.

## 06 UART

1. In 8N1, 8 is the number of data bits, N means no parity, and 1 means one stop bit.
2. The classic F1 sequence that clears ORE reads SR, then DR. With HAL, follow the error path for that version.
3. RS485 must wait for TC. TXE only means the data register can take another byte. The last bits may still be shifting out.

## 07 I2C

1. ACK is the receiver pulling SDA low on the 9th clock.
2. A typical "write the register address, then read" uses a repeated start in the middle. It does not release the bus first.
3. If the bus is stuck low, check power and wiring first. If SDA can be released, clock extra SCL pulses and produce STOP. A software timeout does not hide a short.

## 08 SPI

1. Mode 0 has CPOL=0, so SCK is low while idle.
2. MOSI and MISO are opposite directions. The master's MOSI goes to the slave's input, and the master's MISO to the slave's output.
3. At the end of a transaction, release that slave's CS to the inactive level and meet the part's hold time.

## 09 ADC and DAC

1. Sampling time is set mainly by source impedance, the sampling capacitor, the accuracy you need, and the ADC clock.
2. Twelve bits are `2^12 = 4096` code intervals, with codes 0..4095. Say whether the endpoint model uses 4096 or 4095.
3. STM32F103C8 has no on-chip DAC. Use PWM plus a filter, or an external DAC.

## 10 DMA

1. NDTR/CNDTR holds the number of transfers still to do, not an address. The width of each item sets the byte count.
2. In circular mode the DMA hardware reloads the count at zero and returns the address to the start.
3. A half-word item is 2 bytes. Half-full is half the item count times 2 bytes. The item count is not already a byte count.

## 11 RTC and the Watchdog

1. After main power fails, the RTC keeps running from the VBAT backup domain and LSE or LSI, depending on the setup.
2. WWDG has a window: feeding too early or too late can reset. IWDG mainly constrains feeding too late.
3. If an unrelated timer interrupt always feeds the watchdog, a stuck main loop will not reset. The feed has to summarize the health of the tasks that matter.

## 12 Flash and IAP

1. The Flash controller locks to prevent an accidental erase. Unlock with the required sequence before program or erase.
2. On F103, a particular RDP option-byte value means Level 0 / unprotected. Changing level can erase the whole Flash. Use the manual for that revision.
3. On F4, RDP Level 2 cannot be reversed, and ST-Link cannot restore debug.

## 13 CAN

1. One node in normal mode has nobody to send ACK. The error counters rise and the node can go bus-off. Use loopback, or a second node with the right termination.
2. At 36 MHz, 8 time quanta, and 500 kbit/s, the prescaler is `36 MHz / (8 × 500 kHz) = 9`.
3. On the common F1 remap, PB8 is CAN_RX and PB9 is CAN_TX. Check AFIO and the datasheet for the final map.

## 14 USB

1. F103 USB full-speed usually uses PA11/DM and PA12/DP.
2. A 72 MHz system clock yields 48 MHz through the USB prescaler. Check the RCC setup and the crystal error.
3. CDC looks more like a serial port on the host. HID looks like a keyboard, a mouse, or another human-interface device.

## 15 FreeRTOS

1. Ready tasks of equal priority rotate on a tick boundary when time-slicing is on.
2. A fixed-period task uses `vTaskDelayUntil`, because it anchors an absolute wake-up time and does not add this round's runtime onto the period.
3. A software-timer callback must not block the timer service task. Post an event and return.

## 16 Low Power

1. Stop turns off more high-speed clocks and peripherals than Sleep. It usually draws less, and it costs more to resume.
2. After Stop, restore the system clock the way that series requires before you use a UART or another peripheral that depends on it.
3. No. A datasheet number is for the chip under stated conditions. A board also has a regulator, LEDs, a debugger, and peripheral loads.

## 17 Debug and Performance

1. On F103, SWO/JTDO is multiplexed on PB3. Check the debug-port remap before you use it.
2. Save the stacked PC/LR and SCB's CFSR/HFSR first. Read BFAR/MMFAR only when the valid bit says the address means something.
3. Without a cycle baseline under the same input and the same compiler flags, you cannot tell whether a change helped or only changed the test.

## 18 FAQ

1. The first two steps are a stable reproduction, then a smaller project or a smaller input, until you find the first place expected and actual diverge.
2. If the debugger cannot see the chip, check supply, common ground, SWD wiring, BOOT/reset, and the connection speed before you edit application code.
3. Change one thing. If you change three and it recovers, you still do not know the cause.

## 19 Projects

1. The next round adds one peripheral or one uncertain interface, and keeps the previous round as a running baseline.
2. "Done" means someone else can reproduce the target behavior from the notes, and the failure paths and uncovered limits are written down.
3. If the board clock differs, change and check the clock tree and the time base before you touch baud rate, timers, and USB.

## 20 Resources and the Toolchain

1. CAN filter bits are in the reference manual (RM). The datasheet says whether the chip has CAN, and it gives pins and electrical limits.
2. Pins and electrical parameters are in the datasheet (DS).
3. Option bytes and programming go through STM32CubeProgrammer. Confirm first whether the operation erases Flash or locks debug.

## 21 Schematics and Board Maps

1. A floating BOOT0 follows noise and leakage. The boot target is not determined. Define it with a pull-up or pull-down.
2. The onboard LED on BluePill PC13 is usually on when the pin is low.
3. When silkscreen and the datasheet disagree, use the official datasheet for the exact part and package, plus a schematic you can trace, and then measure the board.

## 22 Simulation: Wokwi and Renode

1. The Wokwi BluePill already has the onboard PC13 LED. A blink experiment does not need another LED.
2. Wokwi's `A0` is the chip's PA0.
3. The current model does not prove the full UART DMA+IDLE behavior. That is a model limit. Check it on a board, or on a model that states support for that peripheral.

## 23 STM32G0 Pins

1. Pin 1 of a G071RB LQFP64 is PC11.
2. That orderable part has no bxCAN. An F1 CAN project does not transfer.
3. The USB-C-related capability is UCPD, not the F103 USB device full-speed controller.
4. `nBOOT_SEL=0` selects the PA14 pin path. `nBOOT_SEL=1` selects the `nBOOT0/nBOOT1` option bits. It is not a system-memory switch.
5. That configuration boots to main Flash. With `nBOOT_SEL=1` and `nBOOT0=0`, `nBOOT1=1` selects system memory and `nBOOT1=0` selects embedded SRAM, both only while `BOOT_LOCK=0`.
6. `BOOT_LOCK=1` forces main Flash. `nBOOT_SEL=1` removes PA14 from the decision. An empty-Flash check can also change the actual target. Option bytes need the specified reset and load sequence, then a read-back. A write's return value does not prove they took effect. An option-byte/complement mismatch forces `BOOT_LOCK=1`. An RDP mismatch defaults to Level 1.
7. Keep the setup, connect SWD, NRST, and the supply reference, then try Under Reset and read the option bytes if the connection works. `BOOT_LOCK=1` plus RDP Level 1 stops debug and resets `DBG_SWEN` to 0. If the application does not set it, the manual does not promise recovery. Clearing `BOOT_LOCK` is possible at RDP Level 0, or after Level 1 → 0 with a full mass erase. Level 2 is irreversible. Do not treat a downgrade or an erase as the default recovery.

## 24 STM32L4 Pins

1. Stop 2 keeps SRAM1/2 and most registers. Execution continues at the instruction after `WFI`/`WFE`. Wake from Standby or Shutdown takes the reset path.
2. The CPU can resume on MSI or HSI16 as selected by `STOPWUCK`, but the PLL is off in Stop. Until SYSCLK, the bus prescalers, and the peripheral kernel clocks are restored, UART baud and timer periods can be wrong.
3. SysTick interrupts every 1 ms by default. If you do not pause it, it wakes the core immediately and you never get the Stop 2 window you planned.
4. On an MB1136 NUCLEO-L476RG, the JP6 (IDD) meter path measures STM32 MCU current, not USB input or every device on the board. Still look for GPIO back-power and the debug connection.
5. Average current is charge over the whole period: `I_avg = Σ(I_i × t_i) / T_cycle`. Active time and sleep time usually differ by orders of magnitude. An arithmetic mean of the two currents is the wrong average.
6. A low range often means a larger shunt drop or a range-change transient: burden voltage. A milliamp wake peak can pull MCU VDD down and reset the part.
7. DS10198 gives the orderable part, pins, electrical limits, and typical values. RM0351 gives the PWR/RCC state machines and registers. AN4746 gives ways to cut power. UM1724 gives the Nucleo board and the JP6 path. ES0250 gives known limits and workarounds for a stated silicon revision.
8. The fixed HAL RTC wake-up handler clears the EXTI pending bit and `RTC_FLAG_WUTF` before it calls the callback. A read in the callback, or after Stop returns, sees the cleared state. Publish the raw RTC/EXTI/PWR bits at the entry of `RTC_WKUP_IRQHandler()`, before the HAL handler, into SRAM that Stop 2 keeps, and consume that software record after return.

## 25 STM32H7 Pins

1. Pin 1 of an H743ZI LQFP144 is PE2.
2. The second VCAP (VCAP2) is pin 106. VCAP1 is pin 71.
3. The controller is FDCAN. FDCAN1 can also use PD0/PD1 or PB8/PB9, among the combinations in Table 9.
4. ES0392 says Rev Y/W have no VOS0 and a 400 MHz CPU limit. Only after you confirm Rev V do you follow the VOS0 + 480 MHz conditions in DS12110 and RM0433. A family maximum on a datasheet cover does not override the errata for that silicon.
5. `8 / 4 × 480 / 2 = 480 MHz` SYSCLK. HCLK is 240 MHz. PCLK is 120 MHz. With an APB prescaler other than 1, the timer clock is 240 MHz. MCO2/5 is 96 MHz.
6. A software read-back and the configuration formula can share one wrong assumption. An MCO measurement and a UART or PWM waveform are independent evidence. In this example `SystemCoreClock` is the CM7 CPU/SYSCLK at 480 MHz, and `SystemD2Clock` is AXI/AHB HCLK at 240 MHz. HAL's default SysTick uses the CPU clock. Bus and peripheral math uses HCLK/PCLK. Do not mix them.

## 26 STM32F10x Standard Peripheral Library

1. `USE_STDPERIPH_DRIVER` makes the device header pull in `stm32f10x_conf.h` and the driver declarations. `STM32F10X_MD` selects the medium-density definition used by parts such as F103C8/B. It has to match the part, the startup file, and the linker layout.
2. `USART_SendData()` only writes the data register. It does not finish a buffered send, wait for the frame, or apply a timeout. The caller still checks TXE/TC and defines a deadline and a failure path for the wait.
3. SPL and HAL both program the same USART registers, and neither knows the other's state or ownership. Initializing twice lets baud, IRQ, DMA, and the state machine overwrite each other.

## 27 Networking

1. A link LED usually means the PHY saw link pulses. It does not prove the MDIO setup, the MAC/DMA descriptors, cache coherence, the lwIP input path, or the IP parameters.
2. H7 Ethernet DMA cannot reach DTCM at `0x20000000`. Descriptors and data buffers go in D1 or D2 SRAM that this DMA can reach. Check the final addresses in the map file.
3. Invalidate works on whole cache lines. If an RX buffer shares its first or last line with another dirty variable, invalidate drops those unwritten bytes too. Give the buffer its own lines and align it to 32 bytes.
4. The raw API is called from the `NO_SYS` main loop or from `tcpip_thread`. Netconn and socket are the sequential API for application tasks. An interrupt must not call raw `tcp_write()` or `udp_send()` directly.
5. TCP is an ordered reliable byte stream. It may split or merge what the application wrote. The application restores message boundaries with a length, a delimiter, or a fixed size.
6. A TCP ACK proves the bytes reached the peer's TCP stack. It does not prove the application read, checked, ran, or stored them. Business completion needs an application ACK with a business sequence number.
7. MQTT QoS 1 is at least once. A republish after a disconnect can deliver a duplicate PUBLISH. Actuators and writers need an idempotency key.
8. The CA is the trust anchor. The host name stops a valid certificate from being used for the wrong service. Randomness protects the handshake keys. A trusted time checks certificate validity. Missing any one of them weakens authentication.
9. Walk DNS result, TCP handshake, TLS verification, MQTT CONNECT/CONNACK, then subscribe/publish. Keep the matching capture and error code.
10. An AT modem that owns TCP/IP still needs a transaction/URC parser, deadlines, UART flow control, modem reset, network registration, socket lifetime, backoff, an offline queue, and a business idempotency state machine.

## 28 Systems and the RTOS Landscape

1. The FreeRTOS kernel mainly provides scheduling, IPC, timers, and memory. RT-Thread and Zephyr also organize a device framework, the build configuration, networking, a file system, and a shell. Product policy and acceptance stay with the project.
2. A mutex only serializes the code it wraps. Chip-select, DMA completion, timeout recovery, and driver state can still be split across critical sections. An owner task keeps the whole transaction and its state with one writer.
3. `U < 1` only says the execution time you counted does not exceed one core. Blocking on a shared resource, ISRs, priority, cache, and Flash wait states can still miss a deadline.
4. Keep at least a monotonic timestamp, a boot id, an event or business sequence number, the ISR enqueue result, the target thread's state, the scheduling point, and a stable result code.
5. A binary semaphore signals an event and has no resource owner. A mutex expresses ownership and usually priority inheritance. Do not hold a mutex in an ISR.
6. Devicetree describes hardware instances and hardware properties known at boot. Kconfig selects software features, dependencies, and configuration. Kconfig does not replace the wiring on the board, and runtime policy does not belong in the devicetree.
7. CMSIS-RTOS2 unifies the API surface. Priority mapping, stack units, what an ISR may call, scheduling, and extensions still differ by kernel and have to be checked one by one.
8. Tickless idle only changes the kernel tick while idle. A peripheral transaction, a wake source, a PHY, a board device, clock restore, and GPIO back-power can still prevent the lowest-power state.
9. An H745's M7 and M4 are different cores. They usually run separate firmware, exchange data in shared memory, and synchronize with HSEM. That is an AMP / heterogeneous boundary, not symmetric SMP. Shared memory, cache, the message protocol, and boot recovery need an explicit design.
10. The health supervisor refreshes the hardware watchdog only when every critical task has done real work and the queue, memory watermarks, and critical state machines meet the health conditions.

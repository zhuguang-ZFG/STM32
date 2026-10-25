# Glossary

Terms are grouped the way a reader meets them across the seven parts. Each line is a working definition for this book. Bits, addresses, times, and electrical limits come from the manual revision for the exact part. Do not copy them from a neighboring family.

## Clocks and reset

| Term | Meaning in this book | A common mix-up |
| --- | --- | --- |
| AHB / APB | On-chip bus levels. The CPU and fast peripherals usually sit on AHB. Most peripherals sit on APB. Clocks divide down from SYSCLK | After an APB divider, every timer clock simply equals PCLK |
| BOR | Brown-out reset. Below a threshold the part resets instead of executing at too low a voltage | A BOR setting means the board power design is already acceptable |
| CSS | Clock security system. When HSE fails, the part switches to an internal high-speed clock and reports the fault. Which clock, and which exception, is in that series' manual | Enabling CSS means the crystal can be left off the board |
| Flash wait state | Extra cycles inserted so a Flash read meets its access time. On F103 they are the LATENCY field of `FLASH_ACR`. At 2.7–3.6 V and 48–72 MHz the value is 2. The steps are in the ledger at the end | Raising the CPU clock never requires a wait-state change |
| HCLK | The AHB clock. The CPU and AHB peripherals commonly use it. An AHB prescaler may sit between it and SYSCLK | HCLK, SYSCLK, and the timer clock are one number |
| HSE / HSI | External high-speed clock / internal high-speed RC. HSE may be a crystal or an external clock | HSE is always more accurate than HSI, and the board always has a crystal |
| HSE bypass | The external clock enters on OSC_IN and the on-chip crystal oscillator is bypassed. That is for a clock source, not the default crystal connection | A fitted crystal means bypass should be on |
| LSE / LSI | External 32 kHz crystal / internal low-speed RC. They usually feed the RTC and the independent watchdog | LSI is accurate enough to be a precision RTC by itself |
| MCO | Master clock output. An internal clock is divided onto a pin so an instrument can check the tree | Any pin can output any internal clock |
| NRST | External reset pin, active low. The debugger and a reset button usually share it | Once the debugger is attached, the level on NRST can be ignored |
| PCLK | An APB clock. STM32 parts usually have PCLK1 and PCLK2 for APB1 and APB2 | Every peripheral kernel clock equals PCLK |
| PLL | A phase-locked loop that multiplies and divides a reference. USB and some target frequencies add extra constraints | Any multiply combination satisfies the chip and USB |
| SYSCLK | System clock, usually chosen from HSI, HSE, or the PLL, then divided toward AHB | After reset, SYSCLK is already the maximum in the manual |
| TIMCLK | The clock that increments a timer. On F1/F4, a common rule is: equal to PCLK when the APB prescaler is 1, otherwise twice PCLK. H7 and others have their own trees | Substituting PCLK yields the PWM frequency on every series |
| VOS | The voltage scale on an H743. Rev Y and W have no VOS0, so the CPU tops out at 400 MHz. On Rev V, VOS1 must already be ready before VOS0, and only then is 480 MHz in scope | The maximum printed on the cover is available on every piece of silicon |

## Pins, GPIO, and alternate functions

| Term | Meaning in this book | A common mix-up |
| --- | --- | --- |
| 5 V tolerant | Some pins may accept 5 V under the datasheet's conditions. Not every pin, and not a 5 V push-pull output | An FT pin can drive a 5 V part's supply rail |
| AF | Alternate function. The pin is given to a peripheral instead of the GPIO data bit. The number comes from that package's AF table | The same AF number means the same peripheral on F1, G0, and H7 |
| Analog mode | GPIO mode for an ADC, DAC, or comparator. The digital input buffer no longer represents the pin's logic level | IDR is still a reliable digital sample in analog mode |
| BSRR | Bit set/reset register. Bits written as 1 set or clear. Bits written as 0 stay. This avoids a read-modify-write race | Changing one pin requires a read of ODR and a write-back |
| GPIO | General-purpose input/output. Mode, pull, speed, and AF are per pin | After reset, every series defaults to a push-pull output |
| GPIO speed | A slew-rate choice. It affects edges and noise. It does not turn the pin into a clock of that frequency | Selecting the 50 MHz slot makes the pin toggle at 50 MHz |
| Open-drain | The pin can only pull low. A high level comes from a pull-up after the driver releases | Writing 1 actively drives a high level |
| Pull-up / Pull-down | A weak on-chip pull. It holds a floating input. It does not replace the external resistor an I2C bus needs | Enabling the internal pull means I2C needs no resistor |
| Push-pull | Both high and low are driven by the output stage | Push-pull can sit on a shared open-drain bus |
| Remap | On F1, AFIO remap moves a peripheral to another pin group. Later families mostly use an AF number and do not have the same remap registers | F1 remap code can be copied onto a G0 or H7 |

## Interrupts and core exceptions

| Term | Meaning in this book | A common mix-up |
| --- | --- | --- |
| BASEPRI | Masks configurable exceptions whose priority number is at or above the threshold. Writing 0 disables this mask | BASEPRI blocks NMI and HardFault |
| EXTI | Connects a GPIO or an internal event to an interrupt or event line. One line is often shared by the same pin number on several ports | Every GPIO has its own EXTI number |
| ISR | Interrupt service routine. Clear the source and leave. Leave slow work to the main loop or a task | An ISR may block if the average time stays short |
| NVIC | The Cortex-M nested vectored interrupt controller. On STM32, a smaller number is a higher logical priority | A larger number is a higher logical priority |
| PendSV | A pendable system-service exception. An RTOS usually switches context here, not inside a high-priority interrupt | Every interrupt return automatically switches tasks |
| Preemption | Preemption priority. A higher preemption priority can interrupt a lower-priority ISR that is running | A different subpriority also preempts |
| PRIMASK | When set, masks configurable-priority interrupts. NMI and HardFault can still enter | Masking interrupts stops every exception on the chip |
| Priority grouping | Splits the priority field into preemption bits and subpriority bits. Changing the split changes the meaning of values already written | Grouping affects only newly written priorities |
| Subpriority | When preemption priority is equal, subpriority chooses who runs first. It does not preempt | Subpriority lets one ISR interrupt another |
| SVC | Supervisor call. Often the path from thread mode into a controlled kernel service, not an ordinary GPIO interrupt | SVC may be invoked freely from an ISR |
| SysTick | The core's system-tick timer. HAL often uses it as a millisecond time base. An RTOS often uses it, or another timer, as the tick | HAL and the RTOS can each initialize SysTick and not interfere |
| Tail-chaining | If another exception is already pending on exception exit, the hardware can skip part of the stacking. That saves time. It does not change who may preempt | Tail-chaining lets a lower-priority interrupt cut into a higher one |
| Vector table | The exception entry table. It starts with the initial stack and the reset vector. If the application does not live at the default address, the table moves with it | After a jump to the application's Reset_Handler, the vector table stays in the bootloader |
| VTOR | Vector table offset register. Relocation has to meet the alignment in the programming manual | Changing only the Flash origin in the linker script makes VTOR correct |

## Timers and PWM

| Term | Meaning in this book | A common mix-up |
| --- | --- | --- |
| ARR | Auto-reload value. It sets the top of the count. Frequency also needs the input clock and PSC | ARR is the frequency |
| CCR | Capture/compare register. In compare mode it sets duty. In capture mode it latches the counter at an edge | It is only for PWM and cannot capture an input |
| Dead time | A gap inserted between complementary outputs to reduce shoot-through. Only timers with complementary outputs have it | Any general-purpose timer has complementary PWM and dead time |
| Encoder mode | Counts position from two quadrature inputs. Swapping the phases reverses the count | Encoder mode emits a mechanical angle that is already converted |
| Input capture | Latches the counter into CCR on an input edge, to measure a width or a period | The captured value is already microseconds, independent of the timer clock |
| MOE | Main output enable. Complementary outputs of an advanced timer stay off while MOE is clear. A break can clear it | Setting the CCER enable bit is enough for complementary PWM to appear |
| PSC | Prescaler. The count clock is about the timer input clock divided by (PSC+1). A new PSC usually loads on an update event | PSC is the division ratio, and it takes effect as soon as it is written |
| PWM | Period and duty used to express average energy or a control value. Whether the load is linear depends on the filter and the power stage | Duty is proportional to every physical output |
| TRGO | A timer's trigger output toward an ADC, a DAC, or another timer. Which peripheral it reaches is in that chip's trigger table | Any update event is automatically wired to any ADC |
| Update event | Produced by overflow, underflow, or a software trigger. Shadow registers load here. It can also be a TRGO source | The update interrupt rate is always the frequency seen on the PWM pin |

## UART, I2C, SPI, CAN, and USB

| Term | Meaning in this book | A common mix-up |
| --- | --- | --- |
| 7-bit address | The common I2C slave address width. The first byte on the wire is those 7 bits plus the read/write bit. HAL's DevAddress is shifted left by 1: the SSD1306's `0x3C` is written `0x78` | The 7-bit value a scanner prints is the 8-bit frame on the wire |
| ACK / NACK | On the 9th I2C clock the receiver decides whether to pull low. NACK means this byte is not acknowledged | An ACK proves the register address and the data mean what you think |
| bxCAN | The classic CAN controller on parts such as F1 | Its registers match H7 FDCAN |
| BS1 / BS2 | CAN bit segment 1 and bit segment 2. One bit time also adds the fixed 1-quantum sync segment. The sample point is (1+BS1) divided by the total number of quanta | A fractional prescaler can be written, and the controller will run at the number you had in mind |
| TEC | Transmit error counter. At 256 the node enters bus-off and stops transmitting | No other node acknowledging means the transceiver is broken |
| Clock stretching | An I2C slave holds SCL so the master waits. Whether the master allows it, and for how long, is in both manuals | Every STM32 master waits forever while a slave stretches |
| CPHA / CPOL | SPI sample phase and idle clock polarity. They have to match the slave's timing diagram | If the frequency matches, any of the four modes will do |
| CRC | A cyclic redundancy check for accidental change | CRC proves who sent the data or resists a deliberate edit |
| FDCAN | A controller that can speak CAN FD. The frame format and the registers differ from bxCAN | It is bxCAN under a new name |
| FE / NE | UART framing error / noise error. The line timing was wrong. They do not name which application field was dropped | No ORE means every frame arrived intact |
| Full duplex | SPI shifts one bit out and one bit in on each clock. A master that wants to read must supply the clock | A read still works if MOSI is left floating |
| IDLE | The UART receive line stayed idle for at least one frame time | IDLE is the end of an application frame |
| NSS | SPI chip select. Many devices act on the rising edge. Hardware NSS and a GPIO you toggle are not the same mechanism | Chip select can stay asserted. Transaction boundaries do not matter |
| ORE | UART overrun. A new byte arrived before the previous one was taken | DMA makes ORE impossible |
| Repeated START | A second start that does not release the bus. A register read is often "write the pointer, repeated start, read" | Two transfers require STOP between them or the slave ignores the second |
| TC / TXE | Transmission complete / transmit data register empty. TXE means another byte may be written. TC means the last bit has left the pin | TXE=1 means the last bit has left the pin |
| UART 8N1 | Eight data bits, no parity, one stop bit. The frame still has a start bit and a stop bit | The 8 already includes the start bit |
| USARTDIV / BRR | On F1 with 16× oversampling, `USARTDIV = fPCLK / (16 × baud)`. The high bits of BRR are the integer; the low 4 bits are the fraction. USART1 sits on APB2: at 72 MHz and 115200 the divider is 39.0625, BRR is `0x271`, and the divider error is 0 | The 0.16% printed on that same row is the error already programmed into BRR |
| USB CDC / HID | Communications class (a virtual serial port) / human-interface class | Enumeration means every host and every application is compatible |

## ADC, DAC, and DMA

| Term | Meaning in this book | A common mix-up |
| --- | --- | --- |
| ADCCLK | The ADC clock on an F103, divided down from APB2. RM0008 caps it at 14 MHz. APB2 at 72 MHz divided by 6 is 12 MHz. A 12-bit conversion adds 12.5 of these cycles on top of the sample time | The ADC clock equals SYSCLK, and a prescaler of ÷2 or ÷4 is always legal |
| Cache coherency | The CPU cache and DMA see the same bytes. On a core with a D-Cache, clean or invalidate by cache line. The H7 D-Cache line is 32 bytes; the range and the buffer are aligned to that length | The DMA-complete interrupt refreshes D-Cache |
| Calibration | ADC calibration. Many series require it after power-up or a clock change. Codes before it finishes are not results | Calibration is done once at the factory |
| Circular mode | When the transfer count expires, DMA reloads and continues. That does not define where an application frame starts | Every circular-DMA interrupt is one new business frame |
| D-Cache | The data cache on a core such as Cortex-M7. An M4 does not have this same maintenance problem | Every STM32 needs a D-Cache clean after DMA |
| DMA | A controller that moves data between a peripheral and memory, or between two memories | DMA does not use the CPU, so it cannot drop data |
| DTCM | Data memory tightly coupled to a Cortex-M7 | Every DMA controller can reach DTCM |
| HT / TC | DMA half-transfer / transfer-complete events | In every mode, HT and TC each mean one business frame |
| Memory-to-memory | A software-triggered memory copy that does not use a peripheral request. Not every DMA controller has this mode | Peripheral requests on that channel keep working |
| NDTR / CNDTR | Remaining DMA items. The unit is an item, not a byte. A half-word or word width is not one byte | The value you read is always a byte count |
| Regular / Injected | The regular group converts in the programmed order. Parts that have an injected group can insert a higher-priority conversion. Not every STM32 has one | Injected channels exist on every series and share the regular result registers |
| Sampling time | How long the sampling switch stays closed to charge the sampling capacitor. A high source impedance needs longer | Sampling time changes only the speed, not whether the code is right |
| SAR ADC | A successive-approximation converter. Effective bits also depend on the reference, source impedance, noise, and calibration | More conversion bits means the accuracy equals that number of bits |
| SRAM domain | Different SRAM regions are reachable by different DMA controllers. This shows up sharply on H7 | Any RAM is readable and writable by any DMA |
| VDDA / VREF | Analog supply and conversion reference. Convert a code to volts with the actual reference, not a nominal 3.3 V | VDDA equals digital VDD, and the reference is certainly 3.3 V |

## Flash, boot, and low power

| Term | Meaning in this book | A common mix-up |
| --- | --- | --- |
| Backup domain | Usually holds the RTC, backup registers, and LSE. Writing it generally means enabling the power-interface clock and clearing write protection | If main power is present, the backup domain can be written immediately |
| BOOT0 | A boot-selection pin. Together with BOOT1 or option bytes it chooses Flash, system memory, or SRAM. The combination depends on the series | A floating BOOT0 has a determined boot mode |
| Dual bank | Some parts split Flash into two banks so one can execute while the other is erased. Without two banks, do not copy a swap procedure | Every STM32 can swap Flash banks |
| IAP | In-application programming: code that is already running receives an image and writes Flash. A jump is not a safe update | Writing Flash and jumping is a safe update |
| FLASH_KEYR | The F1 Flash unlock register. Write `0x45670123`, then `0xCDEF89AB`, and LOCK clears | The two keys can be swapped, or one write leaves the Flash unlocked forever |
| IWDG / WWDG | The independent watchdog usually uses LSI. The window watchdog uses an APB clock, and feeding it too early also resets | Both watchdogs only reset when you are late. Feeding early is always safe |
| Option bytes | Hold read protection, write protection, BOR, and boot-related configuration. A change usually needs an unlock and may apply only after reset | Option bytes behave like an ordinary Flash variable and apply as soon as they are written |
| Page / Sector | The erase unit. F1 commonly uses pages. F4 and H7 commonly use sectors. The size is in that part's manual | The erase unit is 1 KB or 2 KB on every series |
| RDP | Read-protection level. Raising it restricts a debugger's view of Flash. Returning to level 0 often erases the device. Level 2 cannot be reversed on most parts | Raising the level leaves Flash contents alone and can always be undone without loss |
| RTC | Real-time clock, in the backup domain. Changing the calendar enters the init mode that peripheral requires | The RTC uses SYSCLK, so time is lost when main power drops |
| Sleep / Stop / Standby | Low-power modes from shallow to deep. Sleep usually stops the CPU clock. Stop usually stops high-speed clocks and keeps SRAM. Standby is closer to a power-on reset and usually loses SRAM. What is kept, and which clock you wake on, is in that series' manual | The three modes differ only by a current number. After wake-up, code continues exactly where it stopped |
| System memory | The factory bootloader's region. It is not in user Flash. It is often used for a serial or USB download | The system-memory bootloader is the user's IAP project |
| VBAT | The backup-domain supply pin. When main power fails, a battery or backup circuit feeds the RTC | VBAT can replace the board's 3.3 V rail |
| Watchdog | An independent or window counter that checks whether software still reports "healthy" in time | Feeding unconditionally from a fixed interrupt proves the system is healthy |
| WFI / WFE | Wait for interrupt / wait for event. The conditions that wake them differ. An event does not have to enter an ISR | WFI draws the same current as an empty loop |

## RTOS and concurrency

| Term | Meaning in this book | A common mix-up |
| --- | --- | --- |
| Binary semaphore | A 0-or-1 semaphore, often used to say "it happened." It has no priority inheritance | A binary semaphore and a mutex are interchangeable for the same resource |
| CMSIS | Arm's software interface for the core and the device, including core headers and startup conventions | CMSIS is one vendor's HAL |
| CMSIS-RTOS2 | An RTOS API laid over a specific kernel. The same call names do not make FreeRTOS, RT-Thread, or another kernel behave the same | Switching to CMSIS-RTOS2 means you no longer check the kernel version and configuration |
| Context switch | Save one execution context and restore another. An RTOS often does this in PendSV | Every interrupt return switches to another task |
| Critical section | A short region with interrupts masked or the scheduler locked. It must not block, and it must not take long | A longer critical section makes the system safer |
| FromISR | The kernel APIs that may be called from an interrupt. The caller's NVIC priority has to meet that kernel's threshold | An ISR may call an ordinary delay or take a mutex |
| Heap | Here, usually the kernel's own heap. A task stack, the kernel heap, the C heap, and a DMA buffer are not the same memory | One successful malloc means all four heaps have space |
| Idle task | Runs when no other task is ready. Its hook must not block | A high idle share means real-time behavior is certainly fine |
| MSP / PSP | Main stack pointer / process stack pointer. Exceptions commonly use MSP. RTOS tasks commonly use PSP | Tasks and exceptions always share one stack |
| Mutex | A mutual exclusion object with an owner, usually with priority inheritance. It protects a shared resource. Do not take it from an ISR | A mutex can be taken in an interrupt to prevent re-entry |
| Priority inversion | A low-priority holder blocks a high-priority waiter. Priority inheritance only covers the form the mutex protocol defines | An RTOS makes priority inversion impossible |
| Queue | A bounded object that passes data between tasks. A thread may block when the queue is full or empty. An ISR uses the non-blocking FromISR form | A queue is unbounded. A failed write happens only without an RTOS |
| RTOS tick | The kernel's time quantum. It sets delay resolution and it costs a periodic interrupt | A faster tick always improves real-time behavior, at no cost |
| Task | An execution flow with its own stack and priority. When it blocks, it gives up the CPU | A task is a while loop. The stack and the priority can be added later |
| WCET | Worst-case execution time. A schedule is budgeted with the upper bound, not with the average of a few runs | An average runtime can stand in for the worst case |

## Ethernet, lwIP, and MQTT

| Term | Meaning in this book | A common mix-up |
| --- | --- | --- |
| DHCP | The protocol that leases an IPv4 address. Until the lease exists, a business connection is not configured | Plugging in the cable means an IP address is already usable |
| DNS | Turns a name into an address. A lookup failure and a later TCP failure are different layers | Ping uses an IP address, so DNS has nothing to do with connectivity |
| ICMP | Network-layer control messages. Ping uses the echo request. A successful ping only means that echo worked then | Ping means the TCP port, MQTT, and TLS are all usable |
| lwIP | A TCP/IP stack for small systems. The thread model of the raw, netconn, and socket APIs depends on the port and on NO_SYS. A callback must not assume it can block for work on that same thread | lwIP calls and POSIX sockets can be mixed under any configuration |
| MAC | The Ethernet media-access controller inside the MCU. It does not include the PHY's analog front end on the board | The Ethernet chapter of the chip manual already includes the magnetics and the PHY registers |
| MDIO | The serial management interface for PHY registers. Whether the link is up is a PHY status bit, not only a flag in the stack | A stack interface that says up means the physical link is certainly up |
| MQTT | A publish/subscribe application protocol on top of TCP. The session, the topic, and the packet identifier exist only after TCP is up | An MQTT connection means the business data is already in non-volatile storage |
| MQTT QoS | The handover level the protocol defines. QoS 1 is at least once. The application can still see a duplicate | A higher QoS number means the business action runs exactly once |
| PHY | The physical-layer transceiver at the connector, usually a separate chip, connected to the MAC by RMII or MII and by MDIO | The PHY address and registers are 0 on every board |
| RMII | A reduced media interface between MAC and PHY. At 100 Mbit/s the reference clock is 50 MHz. MII uses more parallel wires | RMII and MII differ only by the connector name. The clock can be wired either way |
| TCP | A reliable byte stream. The peer's ACK means TCP received the bytes. It does not mean the application has handled them | An ACK means the local business record can be deleted |
| TLS | Transport layer security. A finished handshake means the certificate chain was checked under the configuration in force. A wrong device clock makes the validity window wrong | Turning TLS on means identity, time, and the business data are all trustworthy |

## Debug

| Term | Meaning in this book | A common mix-up |
| --- | --- | --- |
| BFAR / MMFAR | Bus-fault address / memory-management fault address. The address means something only when the matching valid flag is set | As soon as HardFault runs, these registers hold the guilty address |
| Breakpoint | Stops the core at an instruction. Whether peripherals, DMA, and the watchdog also stop depends on the debug-halt configuration | A breakpoint freezes the motor, the bus, and the watchdog |
| CFSR | Configurable fault status register: usage, bus, and memory-management flags | The name HardFault tells you whether it was a null pointer or a divide by zero |
| DBGMCU | Debug control of low-power modes. With the matching bit set, the debugger can keep the core through Sleep, Stop, or Standby | Single-step through low power is the debugger's default |
| DWT | Data watchpoint and trace unit. Its cycle counter can measure an interval. Trace enable is usually required first | The DWT cycle counter increments with no control bit set |
| HardFault | The fault exception, including faults that escalate. The cause needs HFSR, CFSR, and the stacked PC | Seeing HardFault means you only need to reset |
| JTAG | A multi-wire debug port, usually TMS, TCK, TDI, and TDO. To use those pins as GPIO, release the debug port first | JTAG and SWD use exactly the same pins |
| SCB | System control block: fault status, vector-table offset, and some system-control registers | HFSR alone identifies the root cause of a HardFault |
| SWD / SWO | Two-wire debug / single-wire trace output. Whether SWO is bonded out depends on the part and the package | SWO is available on every package by default and uses no alternate-function pin |
| SWDIO / SWCLK | SWD data and clock. On some G0 parts SWCLK and BOOT0 are the same pin, so a debugger affects the boot sample | The debugger occupies these pins only during the download |

## Engineering habits

| Term | Meaning in this book | A common mix-up |
| --- | --- | --- |
| CubeMX | ST's graphical tool for clocks, pins, and initialization code. The result still has to be checked against the datasheet AF table | After the graphical project is saved, pin conflicts and illegal clocks cannot remain |
| HAL | ST's hardware abstraction layer. It reduces direct register writes. It does not remove part, electrical, or timing differences | After HAL, the reference manual is unnecessary |
| Linker script | Sets the Flash and RAM ranges and where sections go. An IAP image at a new address changes the linker script and the vector table together | The linker script only affects symbol names, not the address the program runs from |
| MPU | Memory protection unit. It can also set access permissions and cache attributes. It is not an MMU with virtual memory | The MPU pages virtual addresses, so a stray pointer is remapped away |
| Ring buffer | A bounded queue whose read and write positions wrap. The capacity, and the full and empty tests, belong in the design | Adding volatile makes it thread-safe and unable to overflow |
| SPL | The standard peripheral library commonly used on F1: a thin wrapper over registers. The names are not HAL's | An SPL example and a Cube HAL project can share one peripheral without a seam |
| `volatile` | Tells the compiler to keep accesses to an object that can change outside the current code, following the abstract machine | It also provides atomicity, mutual exclusion, a memory barrier, and a bound on a queue |

## Numbers you will actually use

Each row above is only a working definition. This table pins the numbers you keep recalculating on a BluePill to an orderable part and a manual path. Change the package or the family, and the whole row is void: recalculate from that part's manual. The arithmetic is already in chapters 02, 03, 06, 07, 09, 11, and 21. This page only gathers it so a measurement has something to stand next to.

| Ledger | Where it is pinned | The number | What it looks like when it is wrong |
| --- | --- | --- | --- |
| This part | Silkscreen STM32F103C8T6, LQFP48. Chapter 21: micro-USB 5 V through an RT9193-33 to 3.3 V, and the PC13 LED is on when the pin is low. Capacity is the low 16 bits at `0x1FFFF7E0`, in KB. The medium-density DevID is `0x410`. DS5319 | The datasheet says 64 KB of Flash and 20 KB of SRAM. If the read is not 64, do not keep calculating as a C8 | The silkscreen or the seller says 128 KB, and the linker script uses all 128 KB |
| Clock tree | On-board 8 MHz HSE, PLL ×9. The RM0008 clock tree, and the table in chapter 02 | SYSCLK = HCLK = 72 MHz. APB1 ÷2 so PCLK1 = 36 MHz; APB2 ÷1 so PCLK2 = 72 MHz. When the APB prescaler is not 1, timers on that bus clock at twice PCLK, so TIM2–TIM7 still run at 72 MHz. TIM1 is on APB2 with a prescaler of 1, so it is not doubled again | Dividing PSC and ARR by 36 MHz, so the PWM frequency is off by two |
| Flash wait | LATENCY in `FLASH_ACR`. The RM0008 access table, at 2.7–3.6 V. Chapter 02 | 0–24 MHz is 0 wait states, 24–48 MHz is 1, 48–72 MHz is 2. The 72 MHz example writes 2 | PLL is switched to ×9 while LATENCY is still 0, and instruction fetches fail as soon as it runs |
| 115200 | The BRR formula in chapter 06. USART1 is on APB2, so fPCLK = 72 MHz, with 16× oversampling | `72e6 / (16 × 115200) = 39.0625`. The fraction `0.0625 × 16 = 1`, so BRR = `0x271`. `72e6 / (16 × 39.0625) = 115200`, and the divider error is 0. USART2 is on APB1, so fPCLK = 36 MHz; the BRR `0x138` in that same chapter is the one that sits about 0.16% off. Dropping the fraction on the 72 MHz row and dividing by 39 also produces about 0.16% | Treating the printed 0.16% as the error of USART1, or treating USART2's clock as 72 MHz |
| One bit and one frame | Chapter 06: at 115200 one bit is about 8.68 µs. 8N1 is a start bit, 8 data bits, and a stop bit: 10 bits. RM0008 sets IDLE only after RX has been idle for one frame time | One frame is about 86.8 µs. That is an idle line, not a length field in a protocol | Treating the IDLE interrupt as proof that the other side closed a protocol packet |
| ADC | Chapter 02: APB2 at 72 MHz, then ÷6. RM0008: the ADC clock must not exceed 14 MHz. Chapter 09: a 12-bit conversion adds 12.5 cycles, and the sample settings run from 1.5 to 239.5 | ADCCLK = 12 MHz. The longest setting is `239.5 + 12.5 = 252` cycles, and `252 / 12e6 = 21 µs`. ÷4 would be 18 MHz, past the 14 MHz cap | Dividing the sample time by the CPU clock, or choosing ÷2 or ÷4 to go faster |
| I2C address and pull-up | The address and pull-up tables in chapter 07. Chapter 03: an F1 internal pull-up or pull-down is about 30–50 kΩ | The SSD1306 7-bit address is `0x3C`; HAL's DevAddress is `0x78`. A short bus uses an external 4.7 kΩ to 3.3 V | Copying the scanner's `0x3C` into `HAL_I2C_Mem_Read`, or enabling only the internal pull-up and then running 400 kHz |
| IWDG, 1 second | Chapter 11: `T = prescaler / f_LSI × (Reload + 1)`. LSI is typically 40 kHz, and the manual range is about 30–60 kHz | With prescaler 64 the nominal count rate is 625 Hz. A 1 second timeout writes Reload as 624; 625 adds one extra count. With the same prescaler and reload, an LSI of 60 kHz yields about half as many seconds as 30 kHz. The longest nominal setting is about 26 s | Writing the seconds computed at 40 kHz down as a guarantee, and debugging without freezing the IWDG |

## Numbers to reconcile before changing family

The table above is pinned to an STM32F103C8T6. The numbers below are already in chapters 04, 05, 12, 13, 15, 16, 23, 24, 25, and 27. This page gathers the ones you recalculate when the chip changes. Change the orderable part or the clock, and the row is void.

> ⚠️ A prescaler, a page size, and a voltage scale look like integers you can copy. Before changing family, recompute this page on the new clock. A prescaler such as 7.2 does not fit in the field. The register receives a neighboring integer.

| Ledger | Where it is pinned | The number | What it looks like when it is wrong |
| --- | --- | --- | --- |
| 1 kHz | Chapter 05. A general-purpose timer on APB1, counted at 72 MHz. Up-counting | PSC = 71, ARR = 999. `72e6 / ((71+1) × (999+1)) = 72e6 / (72 × 1000) = 1000 Hz`. The same PSC and ARR divided by 36 MHz produce 500 Hz. A 1 second setup written as PSC 71 and ARR 999999 does not fit in a 16-bit counter. The row that does fit is PSC 7199 and ARR 9999: `72e6 / (7200 × 10000) = 1 Hz` | The scope shows 500 Hz or 2 kHz, or the 1 second ARR is truncated to 16 bits |
| Stacking | Chapter 04, PM0056. Hardware stacks 8 registers: xPSR, PC, LR, R12, R3, R2, R1, R0 | About 12 HCLK cycles. At 72 MHz, `12 / 72e6 ≈ 167 ns`. That is the stack only. HAL's default is `NVIC_PRIORITYGROUP_4`: 4 preemption bits and 0 subpriority bits. A smaller number is a higher logical priority | Treating 167 ns as the budget for the ISR body, or changing the grouping and still comparing the old preemption numbers |
| FromISR | Chapter 15. FreeRTOS requires GROUP_4. With 4 priority bits, `configMAX_SYSCALL_INTERRUPT_PRIORITY` is often `5 << (8-4)` | `5 << 4 = 0x50`. An interrupt that calls `FromISR` needs a numeric priority of at least 5. The value 0 is the highest logical priority, and the call stops in `configASSERT`. Task priority runs the other way: the idle task is 0, and a larger number is a more urgent task | The assert stops inside the scheduler, and the call stack is in `xQueueSendFromISR` or a sibling |
| 500 kbit/s | Chapter 13, bxCAN, APB1 = 36 MHz. `Baud = fAPB1 / (Prescaler × (1 + BS1 + BS2))`. Sample point = `(1 + BS1) / (1 + BS1 + BS2)` | Prescaler 9, BS1 = 5, BS2 = 2, SJW = 1 quantum. That is 8 quanta. `36e6 / (9 × 8) = 500000`. The sample point is `(1+5)/8 = 75%`. A 70% point (BS1 = 6, BS2 = 3, 10 quanta) needs `36e6 / (500e3 × 10) = 7.2`. Chapter 13 records that non-integer case as 450 kbit/s, which is prescaler 8: `36e6 / (8 × 10) = 450000`. TEC at 256 puts the node in bus-off | The analyzer shows 450 kbit/s, or a single node in normal mode counts errors until it goes silent. A loopback frame only shows that the controller accepted this bit timing |
| Flash page | Chapter 12, RM0008. A medium-density F103 (C8, 64 KB) erases 1 KB pages, the same size as low-density. High-density pages are 2 KB. The program unit is a half-word. The RM0090 citation in that chapter gives F407VG sectors as S0–S3 = 16 KB, S4 = 64 KB, S5–S7 = 128 KB | Unlock `FLASH_KEYR` by writing `0x45670123`, then `0xCDEF89AB`. The address is aligned to 2 bytes | Erasing an F4 as if it had 1 KB pages. The parameter block and the bootloader share a sector, and one erase takes both. The keys are swapped, and LOCK stays set |
| Clock after Stop | Chapter 16: an F103 Stop typical at 3.3 V is about 14 to 20 µA, the chip under those conditions. Wake-up returns to HSI. Chapter 02: the F1 power-up HSI is 8 MHz. Chapter 24: the L476 cover lists Stop 2 at 1.1 µA, 1.4 µA with the RTC, and 4 µs to wake from Stop | The F103 PLL has to be programmed back to 72 MHz. After L476 Stop 2, `STOPWUCK` selects MSI or HSI16. The 80 MHz PLL is a later step. A SysTick that still interrupts every 1 ms measures repeated wake-ups. Read 1.1 µA together with ES0250 for that revision, then set it beside the board current with the debugger and the LED removed | The first UART frame after wake-up is garbage, or the current stays in milliamps. The cover's 1.1 µA has been written down as the whole-board limit |

### One row each of four parts that do not share

Pin numbers come from the package tables already checked in chapters 23 and 24 and in Appendix C. A clock tree holds only for the HSE and the dividers named in that cell.

| Item | STM32F103C8T6 | STM32G071RB | STM32L476RG | STM32H743ZI |
| --- | --- | --- | --- | --- |
| Package used on this page | LQFP48. Capacity and DevID are in the previous table | LQFP64, pin 1 is PC11 | LQFP64, pin 1 is VBAT | LQFP144, pin 1 is PE2 |
| CPU clock | 8 MHz HSE ×9 = 72 MHz | Family maximum 64 MHz, Cortex-M0+, supply 1.7–3.6 V. The cover's 64 MHz is a ceiling. Read RCC for the SYSCLK after reset | 80 MHz maximum, Cortex-M4F, supply 1.71–3.6 V | Rev Y/W: VOS1, 400 MHz. Rev V: the VOS0 path, 480 MHz |
| Boot or voltage scale | BOOT0 and the option bytes. The combination is in RM0008 | After reset is released, the boot configuration is latched on the fourth rising edge of SYSCLK. PA14 is both the boot input and SWCLK. SWCLK edges after the latch do not change this boot target. With `BOOT_LOCK=1` and RDP level 1, debug stops, and `FLASH_ACR.DBG_SWEN` resets to 0 | The temporary clock after Stop 2 is MSI or HSI16 | Enable the SYSCFG clock first. Request VOS0 only after VOS1's `VOSRDY`, then wait for `VOSRDY` again. Before Stop or Standby from VOS0, return to VOS1 and wait for ready once more. The official 400 MHz example passes Flash wait 4. Chapter 25's 480 MHz path passes that same HAL argument. Check the access time for that scale against DS12110 |
| Clock arithmetic | See the previous table | See the boot truth table in chapter 23. Leave the F1 AFIO remap registers there | The CPU can already be executing after wake-up while the PLL is still off | 8 MHz HSE bypass, `PLLM=4`, PLL input 2 MHz. `PLLN=400`, `PLLP=2`: SYSCLK 400 MHz, HCLK 200 MHz, PCLK 100 MHz, APB timer clock 200 MHz, MCO2÷5 expects 80 MHz. `PLLN=480`: VCO 960 MHz, SYSCLK 480 MHz, HCLK 240 MHz, PCLK 120 MHz, timer clock 240 MHz, MCO2÷5 expects 96 MHz. `PLL1Q = 960/4 = 240 MHz`. The 48 MHz USB clock is a different PLL and divider. MCO is a calculated expectation |
| Memory | 20 KB of SRAM. DMA follows the RM0008 channel table | Chapter 23. Recheck alternate functions for that package | Keep the wake evidence in SRAM that Stop 2 retains | Chapter 27: Ethernet DMA cannot reach DTCM at `0x20000000`. Descriptors go in D1 or D2 SRAM that this DMA can reach, aligned to a 32-byte cache line |

## Channels, descriptors, and fault registers

The first two ledgers pin clocks, bit time, and a change of family. The numbers below are already in chapters 08, 10, 14, 15, 17, 27, and 28, and in this repository's examples. A new orderable part, a new DMA request map, or a new descriptor retires the whole row.

| Ledger | Where it is pinned | The number | What it looks like when it is wrong |
| --- | --- | --- | --- |
| SPI at 9 MHz | Chapter 08. SPI1 is on APB2 at 72 MHz. `BR[2:0]` is only 2/4/8/16/32/64/128/256 | `BR = 010` divides by 8, so SCK is 9 MHz. `BR = 001` is 18 MHz. The JEDEC command is `0x9F`. `spi-flash` expects manufacturer `0xEF`, type `0x40`, and capacity `0x17`, often written `0xEF4017`. The page is 256 bytes | Treating `0x40` as the capacity, or using a divider of 3, which does not exist |
| DMA channel | Chapter 10, RM0008. An F103C8 has only DMA1, seven channels. F4 is RM0090 | USART1_TX is Channel 4, USART1_RX is Channel 5, and ADC1 is Channel 1. Eight half-words with `CNDTR = 3` means `8 − 3 = 5` samples, which is 10 bytes. On F4, USART1_RX is DMA2 stream 5, channel 4. The FIFO is 4×32 bits | Writing an F4 stream number into an F1 channel, or treating a half-word NDTR as a byte count. Half-transfer is 4 samples, 8 bytes, not 4 bytes |
| USB, 67 bytes | Chapter 14 and `examples/usb-cdc`. The USB prescaler in RM0008 | With the PLL at 72 MHz and `USBPRE = 0`, `72 / 1.5 = 48` MHz. The device descriptor is 18 bytes and `bMaxPacketSize0 = 64`. This example's VID/PID is `0x1209/0x0001`. `wTotalLength = 0x0043 = 67`. `bMaxPower` of `0x32` is 100 mA. Full-speed bulk and interrupt both top out at 64 bytes. 1023 is full-speed isochronous only | Writing ST's common `0x0483/0x5740` into this descriptor, or giving a full-speed interrupt endpoint a packet size of 1023 |
| Stack unit | Chapter 15 and `freertos-task`. The depth passed to `xTaskCreate` is in words | LED is 128 words = 512 bytes, KEY is 192 words = 768 bytes, and UART is 256 words = 1024 bytes. `configTICK_RATE_HZ = 1000` means 1 tick = 1 ms | Treating 128 as 128 bytes. The first `printf` overflows. A deadline shorter than 1 ms is written down as a kernel guarantee |
| Fault registers | Chapter 17, PM0056 | `CFSR` is `0xE000ED28`, `HFSR` is `0xE000ED2C`, `MMFAR` is `0xE000ED34`, and `BFAR` is `0xE000ED38`. `FORCED` is HFSR bit 30, value `0x40000000`. `BFARVALID` is CFSR bit 15. Set bit 24 of `DEMCR` at `0xE000EDFC`, then read `DWT_CYCCNT` at `0xE0001004`. At 72 MHz, 72 cycles = 1 µs. SWO is PB3. M3/M4 have 6 hardware breakpoints; M7 has 8 | Reading a stale `BFAR` while `BFARVALID` is 0 and treating it as this fault's address |
| 17.2% | Chapter 28's example budget, not a measurement | `80/1000 = 8%`, `420/10000 = 4.2%`, `70/2000 = 3.5%`, `1500/100000 = 1.5%`, together 17.2% | Writing 17.2% down as proof that this board meets its deadlines |
| RMII and MSS | Chapter 27. `REF_CLK`. DHCP and DNS ports. IPv4 with no options | `REF_CLK = 50 MHz`. DHCP is UDP 67/68. DNS is port 53. At MTU 1500 the MSS ceiling is `1500 − 20 − 20 = 1460`. A smaller MSS in the peer's SYN wins. DTCM is still `0x20000000`, and the line is 32 bytes | Checking RMII against MII's 25 MHz clock, or treating 1460 as the MSS the peer has already accepted |

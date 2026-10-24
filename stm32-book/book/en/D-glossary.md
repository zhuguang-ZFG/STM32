# Glossary

Terms are grouped the way a reader meets them across the seven parts. Each line is a working definition for this book. Bits, addresses, times, and electrical limits come from the manual revision for the exact part. Do not copy them from a neighboring family.

## Clocks and reset

| Term | Meaning in this book | A common mix-up |
| --- | --- | --- |
| AHB / APB | On-chip bus levels. The CPU and fast peripherals usually sit on AHB. Most peripherals sit on APB. Clocks divide down from SYSCLK | After an APB divider, every timer clock simply equals PCLK |
| BOR | Brown-out reset. Below a threshold the part resets instead of executing at too low a voltage | A BOR setting means the board power design is already acceptable |
| CSS | Clock security system. When HSE fails, the part switches to an internal high-speed clock and reports the fault. Which clock, and which exception, is in that series' manual | Enabling CSS means the crystal can be left off the board |
| Flash wait state | Extra cycles inserted so a Flash read meets its access time | Raising the CPU clock never requires a wait-state change |
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
| 7-bit address | The common I2C slave address width. The first byte on the wire is those 7 bits plus the read/write bit | The 7-bit value a scanner prints is the 8-bit frame on the wire |
| ACK / NACK | On the 9th I2C clock the receiver decides whether to pull low. NACK means this byte is not acknowledged | An ACK proves the register address and the data mean what you think |
| bxCAN | The classic CAN controller on parts such as F1 | Its registers match H7 FDCAN |
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
| USB CDC / HID | Communications class (a virtual serial port) / human-interface class | Enumeration means every host and every application is compatible |

## ADC, DAC, and DMA

| Term | Meaning in this book | A common mix-up |
| --- | --- | --- |
| Cache coherency | The CPU cache and DMA see the same bytes. On a core with a D-Cache, clean or invalidate by cache line | The DMA-complete interrupt refreshes D-Cache |
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

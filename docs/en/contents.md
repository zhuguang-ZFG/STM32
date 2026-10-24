# Contents

> 中文：[章节目录](../README.md)

> Suggested reading order: **[00](00-how-to-learn-stm32.md) → [01](01-dev-environment.md) → [02](02-part-and-clock.md)** (build the foundation) → pick peripheral chapters by interest → **[18](18-faq.md)** (the troubleshooting manual, open it any time) → **[19](19-projects.md)** (build a project).
> Every chapter ends with a hands-on lab and a trap checklist. Finish the lab before you move on.
> Each chapter opens with a Chinese narrated video ([`../../assets/video/`](../../assets/video/)) and an SRT subtitle file. Rebuild with [`../../tools/gen_narrated.py`](../../tools/gen_narrated.py).

## Foundations

| # | Chapter | In one line | Animation |
| --- | --- | --- | --- |
| 00 | [How to learn STM32](00-how-to-learn-stm32.md) | A roadmap, a hardware list, and the order-of-learning traps to skip | [toolchain-flow](../../assets/animations/toolchain-flow.svg) |
| 01 | [Setting up the development environment](01-dev-environment.md) | How to choose Keil, CubeIDE, or PlatformIO, and how to wire an ST-Link | [boot-sequence](../../assets/animations/boot-sequence.svg) |
| 02 | [Choosing a part, memory, and clocks](02-part-and-clock.md) | Part numbers, the memory map, and the clock tree | [clock-tree](../../assets/animations/clock-tree.svg) |
| 03 | [GPIO and the LED](03-gpio-and-led.md) | 8 modes, push-pull and open-drain, and the series resistor | [gpio-blink](../../assets/animations/gpio-blink.svg) |
| 04 | [Interrupts and the NVIC](04-interrupts-nvic.md) | Priority grouping, EXTI, and interrupt safety | [nvic-interrupt-flow](../../assets/animations/nvic-interrupt-flow.svg) |
| 05 | [Timers and PWM](05-timer-pwm.md) | The time-base formula, duty cycle, and input capture | [timer-pwm](../../assets/animations/timer-pwm.svg) |
| 06 | [UART](06-uart.md) | Frame format, baud-rate error, and DMA+IDLE | [uart-frame](../../assets/animations/uart-frame.svg) |
| 07 | [The I2C bus](07-i2c.md) | Open-drain with pull-ups, ACK, and recovering a stuck bus | [i2c-transaction](../../assets/animations/i2c-transaction.svg) |
| 08 | [The SPI bus](08-spi.md) | Full-duplex shifting, CPOL/CPHA, and chip select | [spi-transfer](../../assets/animations/spi-transfer.svg) |

## The next layer

| # | Chapter | In one line | Animation |
| --- | --- | --- | --- |
| 09 | [ADC and DAC](09-adc-dac.md) | Successive approximation, sample time, and the internal temperature sensor | [adc-sar](../../assets/animations/adc-sar.svg) |
| 10 | [DMA](10-dma.md) | Channel and stream maps, circular mode, and cache coherence | [dma-circular](../../assets/animations/dma-circular.svg) |
| 11 | [RTC and the watchdog](11-rtc-watchdog.md) | The LSE backup domain, alarms, and IWDG/WWDG | [iwdg-window](../../assets/animations/iwdg-window.svg) |
| 12 | [Flash and IAP updates](12-flash-iap.md) | Sector erase, the unlock sequence, and jumping between two slots | [flash-iap](../../assets/animations/flash-iap.svg) |
| 13 | [The CAN bus](13-can.md) | Non-destructive arbitration, bit stuffing, and filters | [can-arbitration](../../assets/animations/can-arbitration.svg) |
| 14 | [USB](14-usb.md) | Enumeration, descriptors, and CDC / HID | [usb-enumeration](../../assets/animations/usb-enumeration.svg) |
| 15 | [FreeRTOS, first steps](15-freertos.md) | Task states, priority, and queues / semaphores | [freertos-scheduler](../../assets/animations/freertos-scheduler.svg) |
| 16 | [Low-power design](16-low-power.md) | Sleep / Stop / Standby, WFI, and wake-up sources | [lowpower-wakeup](../../assets/animations/lowpower-wakeup.svg) |
| 17 | [Debugging and performance](17-debug.md) | SWD/SWO, finding a HardFault, and DWT timing | [debug-swo](../../assets/animations/debug-swo.svg) |

## Projects, simulation, family pinouts, SPL, networking, and systems

| # | Chapter | In one line |
| --- | --- | --- |
| 18 | [FAQ](18-faq.md) | 30+ rows of symptom / cause / fix. Search here first when something breaks |
| 19 | [A set of real projects](19-projects.md) | 10 projects that build on each other: a Bluetooth car, a scope, a data-acquisition card… |
| 20 | [Learning resources and the toolchain](20-resources.md) | How official manuals are named, the community, and open-source firmware libraries |
| 21 | [Schematics and board maps](21-board-maps.md) | Structure drawings of 5 boards, plus how to read a minimum-system schematic |
| 22 | [Simulation labs: Wokwi and Renode](22-simulation-wokwi-renode.md) | Wiring in the browser, loading an ELF from the command line, and where the DMA model stops |
| 23 | [STM32G0 pins](23-stm32g0-pins.md) | G071RB pins, BOOT0/SWCLK truth table, option bytes, and a polished Under Reset recovery workflow |
| 24 | [STM32L4 pins](24-stm32l4-pins.md) | L476RG pins, VDDUSB, and the low-power typical values on the cover |
| 25 | [STM32H7 pins](25-stm32h7-pins.md) | H743ZI pins and supply, revision-specific 400/480 MHz configuration, and MCO/peripheral clock verification |
| 26 | [STM32F10x Standard Peripheral Library](26-spl.md) | V3.5.0 project skeleton, build macros, API boundaries, and one-peripheral migration |
| 27 | [STM32 networking and protocol stacks](27-network.md) | Ethernet/RMII hardware, H7 DMA/cache, lwIP threading, TCP/UDP, MQTT/TLS, and PCAP diagnosis |
| 28 | [Embedded systems and the RTOS ecosystem](28-system-rtos.md) | Ownership, deadlines, resource budgets, FreeRTOS/RT-Thread/Zephyr boundaries, startup, and watchdog health |

## Related directories

- [Writing guide, CONTENT_GUIDE.md](CONTENT_GUIDE.md) — read this before you contribute
- [Whole book, stm32-book/](../../stm32-book/) (offline HTML / PDF)
- [Example code, examples/](../../examples/)
- [Simulation, sim/](../../sim/README.md) (Renode scripts; Wokwi projects sit next to the examples)
- [Evidence labs, labs/](../../labs/README.md)
- English cheatsheets: [HAL](cheatsheets/hal.md), [registers](cheatsheets/registers.md), [bus and pins](cheatsheets/bus-and-pins.md), [error codes](cheatsheets/errors.md). The Chinese cheatsheets are indexed at [`../../cheatsheets/README.md`](../../cheatsheets/README.md).
- [Visual assets, assets/](../../assets/)
- [Narrated videos, assets/video/](../../assets/video/README.md)
- [Generator scripts, tools/](../../tools/)
- [Repository map, STRUCTURE.md](../../STRUCTURE.md)

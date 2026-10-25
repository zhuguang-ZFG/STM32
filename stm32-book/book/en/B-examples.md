# Verification index for the 14 examples

An example is not finished when it compiles. Each one needs an observable result, and a sentence about what that result does not prove. The default board is an STM32F103C8T6 (BluePill). Clocks, wiring, and the firmware-package version are in each directory's README.

| Order | Example | Chapters | Smallest visible result | Check with | This does not prove |
| --- | --- | --- | --- | --- | --- |
| 1 | `gpio-blink` | 03 | PC13 blinks at about 1 Hz; an external LED on PA0 toggles on another period | Logic analyzer or meter | Every GPIO can drive the same load |
| 2 | `exti-key` | 04 | Each valid press on PA0 toggles PC13 once | Logic analyzer and an interrupt count | The debounce constants suit every switch |
| 3 | `timer-pwm` | 05 | PA6 is 1 kHz; the duty changes continuously as CCR changes | Scope or logic analyzer | LED brightness is linear with duty |
| 4 | `uart-dma-idle` | 06, 10 | Commands of several lengths enqueue intact, and reception recovers after ORE | USB-TTL and a byte compare or counter | IDLE is a business frame; a continuous stream never overflows |
| 5 | `i2c-oled` | 07 | The OLED displays and keeps refreshing; an address scan hits only the target | Logic analyzer, I2C decode | Every OLED uses the same address and init table |
| 6 | `spi-flash` | 08 | The JEDEC ID matches the part; a cross-page write matches byte for byte | Logic analyzer and `memcmp` | Endurance and power-loss atomicity meet a product requirement |
| 7 | `adc-dma` | 09, 10 | Three channels sample continuously, and a change appears on the matching channel | Meter and the DMA buffer | A nominal 3.3 V is a precision reference |
| 8 | `rtc-alarm` | 11, 16 | After Stop, wake-up follows the plan; with VBAT the time stays continuous | Current meter and serial timestamps | The whole board meets a datasheet's typical chip current |
| 9 | `iap-bootloader` | 12 | A valid image jumps; a damaged image does not | Serial port, reset, and a power-cut injection | Signatures, anti-rollback, and secure boot are done |
| 10 | `can-bxcan` | 13 | Loopback receives; with two nodes there is an ACK and the filter works | CAN analyzer or the error counters | FDCAN can reuse the same register setup |
| 11 | `usb-cdc` | 14 | The host enumerates a CDC port and bytes travel both ways | USB capture or the OS device list | Every host, cable, and suspend/resume path is compatible |
| 12 | `usb-hid` | 14 | An edge on PA0 produces one press and one all-zero release report | A text field and a USB capture | It is a safe input device or has passed USB-IF |
| 13 | `freertos-task` | 15 | Three tasks run; an empty queue blocks; a key event wakes a task | Trace or runtime stats, plus serial output | Worst-case response and stack margin are proven |
| 14 | `spl-f1-blink` | 01, 26 | ELF/HEX/BIN/MAP close; on a board, PC13 blinks at about 1 Hz | GNU Arm size/nm, ST-Link, logic analyzer | A successful link means the board clock, wiring, and runtime are verified |

## Three rows to match before you run the list

Before the order in the table, match these three rows to the ledger at the end of [Appendix D](#appendix-glossary). If they do not match, do not add the next bus yet.

| Example | Match this first | What a mismatch means |
| --- | --- | --- |
| `gpio-blink` | PC13 is on when low. That LED's current does not stand for any other pin | The polarity is reversed, or PC13's brightness is being required of an ordinary pin |
| `timer-pwm` | Compute the timer clock at 72 MHz. Do not divide TIM2–TIM7 by PCLK1's 36 MHz | The scope shows half or twice the frequency from the formula |
| `uart-dma-idle` | USART1, 115200, BRR `0x271`. IDLE is about 86.8 µs, not a protocol frame boundary | The 0.16% in the chapter 06 table is being treated as this USART's error |

## A useful order

1. **Close the loop first:** `gpio-blink → exti-key → timer-pwm`. Prove download, pins, and the time base.
2. **Then one peripheral:** `uart-dma-idle → i2c-oled → spi-flash → adc-dma`. Add one bus or data path at a time.
3. **Then state:** `rtc-alarm → iap-bootloader → can-bxcan → usb-*`. Keep a firmware image you can fall back to.
4. **Concurrency last:** `freertos-task`. Scheduling problems stay separate from driver problems only after the bare-metal behavior is explainable.
5. **The old library on its own:** `spl-f1-blink` uses SPL V3.5.0 and CMake. Do not initialize the same peripheral from both SPL and HAL. Check the CLI build, then point CLion or VS Code at the same preset.

## A record for each example

Keep one table in your own lab notes:

| Field | Example |
| --- | --- |
| Part / board | STM32F103C8T6, BluePill silkscreen and where the board came from |
| Tools | CubeIDE, compiler, Cube firmware tag or commit |
| Wiring | Power, levels, common ground, pins, and the external part |
| Expected | A frequency, byte sequence, ID, time, or state you can measure |
| Actual | Instrument reading, raw serial bytes, error registers |
| Boundary | Simulation or real board, temperature, supply, failure paths not covered |
| Reproduce | The shortest path from a clean project to the observation |

Source and per-example wiring live in `examples/` under the MIT license. The prose and figures of this book are CC BY 4.0. The full boundary is [Appendix E](#appendix-references).

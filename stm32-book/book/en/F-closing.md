# Where the road goes next

This page exists only in the book. It gathers the seven parts into one path you can keep walking. It does not change chapter 28 in `docs/en/`. The numbers below are the ledger already stated in earlier chapters, gathered here so a measurement has a column to stand in.

## What each part should leave you

| Part | You should be able to show |
| --- | --- |
| Start | A project you can rebuild: it compiles, downloads, and hits a breakpoint, with the part and the clock assumption written down |
| Pins and time | A real level on one pin, or a timer period that was calculated and then measured |
| Moving data | One UART, I2C, or SPI frame, or one ADC/DMA buffer with a named owner |
| Reliability | The state after a watchdog, low-power, or failed update — not only the demo path |
| Delivery | A reproduction note for a small project, with manuals, examples, and community posts kept apart |
| Migration and networks | Power, alternate functions, clocks, and memory rechecked on a new family; network faults split by link, address, transport, and application |
| System | One diagram with an owner, a deadline, and evidence of recovery — not only a different RTOS name |

## Four lines for the first board

The default board is a BluePill, silkscreen STM32F103C8T6, LQFP48. Before you change chips, the lab note has these four lines. Then you can say that it runs. The arithmetic and the manual path are in the first ledger at the end of [Appendix D](#appendix-glossary). The next ledger is the one you use when the chip changes. Channels, descriptors, and fault registers are in the third ledger.

| Write this down | What this book expects | What you measure |
| --- | --- | --- |
| Capacity | Read `0x1FFFF7E0`. A genuine C8 reports 64 KB. The medium-density DevID is `0x410` | The reading, and whether it matches the silkscreen |
| Clock | 8 MHz HSE ×9 = 72 MHz. APB1 is 36 MHz, and TIM2–TIM7 are still computed at 72 MHz. Flash wait states are 2 | `HAL_RCC_GetPCLK1Freq()`, plus one PWM period |
| One UART frame | USART1, 115200, 8N1, BRR `0x271`. One bit is about 8.68 µs, and one frame is about 86.8 µs | The bit width on a logic analyzer |
| One failure boundary | IWDG: prescaler 64 and Reload 624 are the 1 second computed at 40 kHz. LSI is about 30–60 kHz, so that second is not a guarantee | The reset flag and a stopwatch when you deliberately stop feeding |

## Three more lines when you change chips

Match the four lines for the first board, then change family. The expected values are in the second ledger of [Appendix D](#appendix-glossary). The measurement is still yours to fill in.

| Write this down | What this book expects | What you measure |
| --- | --- | --- |
| The G0 boot latch | Latched on the fourth rising edge of SYSCLK. PA14 is both the boot input and SWCLK. `DBG_SWEN` resets to 0 | The level on PA14 during the sample window, and whether the debugger connects |
| The clock an L4 wakes on | After Stop 2 the temporary clock is MSI or HSI16. The cover's 1.1 µA, 1.4 µA with the RTC, and 4 µs wake are chip typicals | The bit width of the first frame after wake-up, and the current with the debugger and the LED removed |
| H7 silicon and VOS | Rev Y/W stay on VOS1 at 400 MHz. Rev V enters VOS0 from a VOS1 that has already reported ready, and only then 480 MHz. MCO2÷5 expects 80 MHz at 400 MHz and 96 MHz at 480 MHz | `REV_ID`, both `VOSRDY` waits, and the MCO reading on an instrument |

## When this book is finished

Three checks are enough:

1. The toolchain runs again on your board, not only in a screenshot.
2. At least one claim records the expected value, the measured value, and the conditions.
3. That claim points at a document number or a frozen code version. A number you cannot point back should not enter the design yet.

## What to do next

Pick the constraint you actually have to ship, and go deep. Do not scan all 29 chapters again.

- Still closing the first loop: return to chapters 00–05 and make the LED, the interrupt, and the PWM into records you can measure.
- Data has to enter and leave: chapters 06–10 plus [Appendix A](#appendix-engineering). Write down the buffer and the frame boundary.
- The device must still be there after power loss, an update, or sleep: chapters 11, 12, and 16. Put the failure path and the clock after wake-up in a table.
- It has to reach a network: chapter 27. Prove the link, the address, TCP, MQTT, and TLS separately.
- You are choosing an RTOS: chapters 15 and 28. Budget the stack, the queue, and the interrupt priority before you compare kernel names.

Look up terms in [Appendix D](#appendix-glossary). What counts as evidence, and what is only a clue, is [Appendix E](#appendix-references).

## Leave these for later

- Do not copy F1 register addresses onto a G0, L4, or H7.
- Do not copy the F103 1 KB page, prescaler 9, or BRR `0x271` onto a family whose clock is different.
- Do not treat a passing simulation as proof of the board's electrical behavior.
- Do not treat a parameter from a social post as a manual.
- The Chinese book and this English book are two builds. English comes from `docs/en/` and `stm32-book/book/en/`. A sentence on the Chinese page is not, by itself, a register fact this edition has checked.

If you do only one thing after this page: pick one behavior you must deliver, and write its expected value, the measurement, and the next way it can fail.

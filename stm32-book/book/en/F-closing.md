# Where the road goes next

This page exists only in the book. It gathers the seven parts into one path you can keep walking. It adds no new register facts, and it does not change chapter 28 in `docs/en/`.

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
- Do not treat a passing simulation as proof of the board's electrical behavior.
- Do not treat a parameter from a social post as a manual.
- The Chinese book is a separate build from `docs/`. This English edition is built from `docs/en/`.

If you do only one thing after this page: pick one behavior you must deliver, and write its expected value, the measurement, and the next way it can fail.

# Sources, versions, and license

This book sorts sources into four layers. They do not replace each other:

1. **Specifications and chip manuals.** A datasheet answers pins and electrical limits. A reference manual answers registers and peripherals. A programming manual answers the core. A protocol specification answers what happens on the wire.
2. **Vendor code and application notes.** They show one way to do the job on one version. They still have a specific part, firmware package, and example configuration.
3. **Vendor community posts and open implementations.** They are for finding pitfalls, comparing styles, and designing a check. A community conclusion is not a specification. Check it against the source or the manual for your version.
4. **Original material in this project.** Chapters, examples, figures, and the builder. Factual parameters should point at the first three layers. The teaching order and the experiments belong to this project.

## Snapshot rules

- A manual citation names at least the document number. For a fact that moves between revisions — a pin, a typical current — also name the Rev, figure, table, or chapter.
- A GitHub reference is frozen at a tag or a full commit. "main looks the same today" is not evidence.
- A community article records the access date and the use. It is a clue.
- A reproduction note freezes the orderable part, the board silkscreen, the Cube package, the compiler, and the clock setup.

## This book and the repository

The chapters come from `docs/en/00–28` in the same repository. The build removes video, subtitles, and the repeated narration, and it does not edit those chapters. Each chapter gains a compass: question, deliverable, boundary, and source anchors. After chapter 28 there is a closing page that exists only in the book. Five appendices tie the examples, the answers, the glossary, and the sources into one volume.

Chapter 23's G071 boot table, shared-pin hardware, and recovery limits were checked against DS12232, RM0444, AN5096, AN2606, and ST's boot FAQ. Chapter 25's H743 supply, revision, and 400/480 MHz path were checked against DS12110, RM0433, ES0392, AN4938, ST's 480 MHz note, and the frozen STM32CubeH7 clock example. Chapter 26's SPL API was checked against STSW-STM32054, RM0008, and the frozen source mirror. Chapter 27's network boundary was checked against RM0433, UM2407, UM1713, the frozen STM32CubeH7 / lwIP / Mbed TLS sources, and the IETF and OASIS specifications. Chapter 28's system boundary was checked against FreeRTOS V11.3.2, RT-Thread v5.3.0, Zephyr v4.4.2, CMSIS 6.4.0 / CMSIS-RTOS2 2.3.0, and PM0056. The H745 dual-core boundary was also checked against RM0399 and the frozen `stm32h745xx.h`.

The way the book is organized borrows a method used for another book in the same workspace: part goals, a chapter compass, offline HTML/PDF, and an answer appendix. The prose was not copied. The licenses and the subjects stay separate.

## License boundary

- `docs/`, original drawings outside `assets/photos/`, and the original prose and layout of this book: **CC BY 4.0**. A republication or adaptation names the author, links the source, and says what changed.
- Two Nucleo-64 photographs in `assets/photos/` stay **CC0 1.0**. The author, the original page, the processed size, and the SHA-256 are in that directory's README.
- `examples/`, `tools/`, and code fragments: **MIT**. The full terms are the repository `LICENSE`.
- Material from ST, Arm, FreeRTOS, USB-IF, IETF, OASIS, Wokwi, Renode, and other third-party repositories: this book supplies links, document numbers, a few necessary facts, and its own wording. It does not redistribute their manuals, specifications, or source. Those rights stay with the owners.
- STM32, STM32Cube, Nucleo, Discovery, Keil, IAR, FreeRTOS, and similar names belong to their owners. This project is not affiliated with those companies.

## Source register

The register below is generated from `manifest-en.json` at build time. Each entry has an authority, a frozen point, an access date, a license boundary, and the scope used in this book. A chapter's source anchors link to these entries.

# DMA memory-to-memory assumptions


| ID | Under-determined choice | Chosen default | Class | Source / reason | Reversible alternative |
| --- | --- | --- | --- | --- | --- |
| A-001 | Target board | BluePill STM32F103C8T6, 20 KiB SRAM | scope | Existing complete F103 examples and ch14 platform list | Add a second board only after this path is verified |
| A-002 | Transfer size and width | 1024 `uint32_t` items = 4096 bytes; word/word | semantic | ch14 asks for 4 KiB; F1 supports 8/16/32-bit widths | Use 4096 bytes only if byte-width teaching is the goal |
| A-003 | DMA channel and mode | DMA1 Channel1, `DMA_MEMORY_TO_MEMORY`, normal mode | interface | RM0008 and ST `DMA_FLASHToRAM` example | Another DMA1 channel is possible but adds no teaching value |
| A-004 | Address increments | Source and destination both increment | interface | Both buffers are arrays; ST example sets both increments | Fixed destination would copy only one word and is not this experiment |
| A-005 | Completion model | TC/TE interrupts; wrap-safe 1000 ms software timeout | semantic | ch14 requires TC/TE evidence; avoids an unbounded wait | Polling is simpler but would not exercise the vector/callback path |
| A-006 | Observable result | PC13 LED: steady on for success; 1–5 slow blinks for distinct failures | interface | No extra wiring or UART peripheral | UART reporting can be added later without changing DMA logic |
| A-007 | Source pattern | Runtime xorshift32 fill; destination prefill `0xA5A5A5A5` | semantic | Deterministic, non-constant data makes accidental no-copy visible | A Flash constant would become Flash→RAM, a different teaching point |
| A-008 | Host regression boundary | Controlled HAL test double exercises production flow; binary check exercises real vectors/layout | evidence | Existing `uart-dma-idle` pattern; hardware is unavailable | Board-only acceptance would leave failure branches unverified |
| A-009 | New tests | Add example-local host regression and firmware checker; do not edit `book/tests` or policy | process | User requires regressions; operator baseline is pinned | Keep tests external and unverified until reviewed |
| A-010 | Reference books | Use local Z-Library samples for explanation order only | evidence | Repository reference review explicitly forbids copying modern illustrations or treating book register claims as authoritative | Omit book references if they add no teaching value |
| A-011 | Wokwi | Include a minimal BluePill diagram and ELF pointer, but make no simulation-success claim | scope | Matches existing example layout | Omit Wokwi files if the model cannot exercise DMA |
| A-012 | ARIS artifact path | `implement-stage/dma-memcopy/` | process | Avoids path conflicts with open PR #175 | Merge the two ARIS directories only after PR #175 merges |
| A-013 | GitNexus | Do not reindex; STM32 is absent from the index | evidence | `list_repos` returned only two unrelated repositories | Use source inspection and `rg` for this slice |
| A-014 | Documentation figures | Reuse existing ch14 DMA figures; add no new image | scope | The missing item is a runnable entry, not another concept diagram | Add an original timing figure only if the final text cannot explain ownership clearly |

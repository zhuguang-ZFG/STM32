# DMA memory-to-memory final report

Date: 2026-11-25
Base: `bbdbb95577511bd4aa724cf9afb83ccfe9bb3a06`
Branch: `feat/dma-memcopy-example`
Hardware status: `pending`

## Goal and result

Added the missing fixed-board 4 KiB DMA memory-to-memory path and connected it to ch14. `examples/dma-memcopy/` now builds a BluePill/STM32F103C8T6 firmware that copies 1024 `uint32_t` words between two SRAM buffers with DMA1 Channel1 in normal mode, records TC/TE callbacks, applies a wrap-safe 1000 ms timeout, compares the buffers and reports the result on PC13.

The book no longer says the 4 KiB experiment has no complete entry. It distinguishes firmware build, real ELF/BIN layout checks, host control-flow regression and pending board evidence.

## Source use

| Source | Use in this slice | Boundary |
| --- | --- | --- |
| RM0008 and pinned STM32CubeF1 HAL/CMSIS | DMA1 clock, `MEM2MEM`, widths, NDTR units, TC/TE behavior, vector number | Technical authority for this exact F103 path |
| Official STM32CubeF1 `v1.8.6` `DMA_FLASHToRAM` example on GitHub | Configuration shape: DMA1 Channel1, both increments, word/word, normal mode, TC/TE callbacks | Not copied as code; adapted to SRAM→SRAM 4 KiB with timeout/comparison/LED codes |
| ST Community / ST wiki discovery and community BluePill reports | Located common memory-copy teaching patterns and failure questions | Discovery only; no community claim outranks the pinned manual/source |
| Local Z-Library sample: 野火《STM32 HAL 库开发实战指南》physical pages 203/210 | Explanation order: memory-copy experiment followed by build/download/observation | Board wiring and register claims were not copied |
| Local Z-Library sample: 《Mastering STM32》2e physical pages 237/269 | CPU/DMA path and buffer storage-time explanation order | No illustration copied; API/register facts return to matching ST sources |

## Semantic assumptions in full

| ID | Chosen default |
| --- | --- |
| A-001 | BluePill STM32F103C8T6, 20 KiB SRAM |
| A-002 | 1024 × 32-bit = 4096 bytes; word/word widths |
| A-003 | DMA1 Channel1, memory-to-memory, normal mode |
| A-004 | Source and destination both increment |
| A-005 | TC/TE interrupts plus wrap-safe 1000 ms timeout |
| A-006 | PC13 steady-on success; 1–5 slow-blink failure codes |
| A-007 | Runtime xorshift32 source; `0xA5A5A5A5` destination prefill |
| A-008 | Host test double for program flow; real ELF/BIN checker for vectors/layout |
| A-009 | New example-local tests only; no `book/tests` or policy edits |
| A-010 | Reference books guide explanation order only |
| A-011 | Minimal Wokwi pointer included; no simulation-success claim |
| A-012 | ARIS artifacts under `implement-stage/dma-memcopy/` to avoid PR #175 conflicts |
| A-013 | No GitNexus reindex; STM32 is not indexed |
| A-014 | Reuse existing ch14 figures; no new image asset |

## Rung status

| Rung | Status | Evidence |
| --- | --- | --- |
| F0 firmware spine | PASS | ARM configure/build; real ELF/BIN vector and SRAM checks |
| F1 host regression | PASS | RED observed first, then unchanged CTest passed all branches |
| F2 book/index integration | PASS | Book/render/voice/site gates and built ch14 visual check |
| F3 final verification/review | PASS with declared limits | Full tests/assets/site/example checks; `task_verify` unverified; sweep unavailable |

## Verification evidence

| Command / check | Result |
| --- | --- |
| `cmake --preset bluepill "-DCUBEF1_PATH=../../.temp/STM32CubeF1"` | exit 0 |
| `cmake --build --preset bluepill` | exit 0; Flash 6508 B / 64 KiB; static RAM 8280 B + 2048 B stack |
| `python tests/check_firmware.py ...elf ...bin` | PASS; SP `0x20005000`, reset `0x080005cd`, SysTick `0x080005a1`, DMA1_CH1 `0x080005ad` |
| `cmake --preset host-tests` + build + `ctest --preset host-tests` | exit 0; 1/1 host regression passed |
| `python -X utf8 -m book.checks --check` | `checks passed` |
| `python -X utf8 -m book.build_html --check` | 53 pages, 0 planned chapters missing |
| `python -X utf8 tools/slop_lint.py` | no mechanical hits |
| `python -X utf8 -m pytest book/tests -q --confcutdir=book/tests -p no:cacheprovider` | 124 passed |
| `python -X utf8 tools/check_assets.py` | 583 public assets PASS; 14/14 real-photo hashes/dimensions PASS |
| `npm run docs:build` | exit 0 |
| `npm run site:images` | 363 images lazy/async/sized |
| `npm run site:pages` | 54 pages; manifest/dist one-to-one |
| Built ch14 visual check | New example path, NDTR 1024, pending hardware boundary and exit question present; no horizontal overflow at 1365 px viewport |
| `git -c core.safecrlf=false diff --check` | exit 0 |
| `task_verify run` | **unverified** — `project-or-git-baseline-unavailable`, no operator-configured checks |

Firmware artifacts:

- BIN: 6508 B; SHA-256 `4b032d24de2941e03c1b15000076a175e11ee75acb33b246a21331c377979347`
- ELF: SHA-256 `e2969dc929baf145d2d194be1ea732821ccfff9a8b7b40bdfc79bfed70527a5f`

## Regression review boundary

The new files `examples/dma-memcopy/tests/dma_memcopy_tests.c`, `tests/stm32f1xx_hal.h` and `tests/check_firmware.py` are legitimate regression additions. They were written test-first and watched fail before implementation. They do not edit existing tests, runner inputs or policy. Reviewer attention is requested; `task_verify` remains unverified until a new operator baseline is established.

## Independent sweep

`SWEEP_UNAVAILABLE`. `mcp__nim_list_ducks --check-health` reported 0/1 healthy providers; the only configured NVIDIA NIM provider was unhealthy. No external verdict or acquittal is claimed. Internal review found and fixed the SysTick checker offset, 64-bit host pointer modeling and LED-before-clock failure path.

## Interfaces and files

- Firmware entry: `examples/dma-memcopy/main.c`
- Vectors: `examples/dma-memcopy/stm32f1xx_it.c`
- Build: `examples/dma-memcopy/CMakeLists.txt`, `CMakePresets.json`, `cmake/arm-none-eabi.cmake`, `dependencies.lock.json`, `stm32f103c8.ld`
- Evidence: `examples/dma-memcopy/tests/`
- Reader entry: `examples/dma-memcopy/README.md`
- Book integration: `docs/v1-drivers/14-dma.md`
- Catalogs: `examples/README.md`, `README.md`
- Process evidence: `implement-stage/dma-memcopy/`

Public symbols: `hdma_memcopy`, `g_dma_src`, `g_dma_dst`, `DMA1_Channel1_IRQHandler`, `HAL_DMA_XferCpltCallback`, `HAL_DMA_XferErrorCallback`.

## Deferred scope and live stubs

- No board flash/run, PC13 observation, logic-analyzer/SWD trace, throughput or latency measurement.
- No F4 port, circular mode, double buffering, cache maintenance, UART reporting or second platform.
- Wokwi is a convenience pointer, not acceptance evidence.
- No production stubs, placeholders or fake fallbacks remain. The only test double is isolated under `tests/` and explicitly does not model real DMA timing.

## Adjacent PR status

PR #175 is separate ch41 work. Its transient GitHub 503 link failure was rerun and all six checks are now successful; it remains open and unmerged.

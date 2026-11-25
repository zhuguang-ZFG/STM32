# DMA memory-to-memory example implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a clean BluePill/STM32F103C8T6 4 KiB DMA memory-to-memory example and connect ch14 to the real build path.

**Architecture:** Reuse the `uart-dma-idle` fixed CubeF1 HAL/CMake skeleton. Production firmware uses DMA1 Channel1 normal mode with TC/TE callbacks, a wrap-safe timeout, byte/word comparison and PC13 LED result patterns. Example-local host tests include the production `main.c` with a controlled HAL test double; a Python checker inspects the real ELF/BIN vectors and SRAM layout.

**Tech Stack:** C11, CMake ≥3.21, Ninja, GNU Arm Embedded Toolchain 10.3.1, STM32CubeF1 v1.8.6, HAL `77fbb30b`, CMSIS device `8a76309e`, Python 3.

**Spec:** `implement-stage/dma-memcopy/SPEC.md`

## Global Constraints

- Base commit: `bbdbb95577511bd4aa724cf9afb83ccfe9bb3a06`.
- Target: STM32F103C8T6 / BluePill only.
- Transfer: 1024 × 32-bit = 4096 bytes, SRAM→SRAM, DMA1 Channel1, normal mode.
- Keep at least 2 KiB stack reserved in the 20 KiB SRAM linker layout.
- Do not modify `book/tests`, CI policy, runner inputs or existing examples.
- Reference books guide explanation order only; technical claims use RM0008 and pinned source.
- Build/host checks do not prove hardware behavior; keep `hardware_status: pending`.
- Use `edit` for existing files and `write` for new files; exclude `out/`, `.temp/` and CRLF-only noise from commits.

---

### Task 1: Firmware spine

**Files:**
- Create: `examples/dma-memcopy/CMakeLists.txt`
- Create: `examples/dma-memcopy/CMakePresets.json`
- Create: `examples/dma-memcopy/cmake/arm-none-eabi.cmake`
- Create: `examples/dma-memcopy/dependencies.lock.json`
- Create: `examples/dma-memcopy/stm32f103c8.ld`
- Create: `examples/dma-memcopy/include/stm32f1xx_hal_conf.h`
- Create: `examples/dma-memcopy/main.c`
- Create: `examples/dma-memcopy/stm32f1xx_it.c`
- Create: `examples/dma-memcopy/diagram.json`
- Create: `examples/dma-memcopy/wokwi.toml`

**Interfaces:**
- Consumes: locked STM32CubeF1 tree at `CUBEF1_PATH`.
- Produces: `dma-memcopy.elf/.hex/.bin/.map`, `g_dma_src[1024]`, `g_dma_dst[1024]`, `DMA1_Channel1_IRQHandler`, `HAL_DMA_XferCpltCallback`, `HAL_DMA_XferErrorCallback`.

- [ ] Copy the dependency lock, linker, toolchain and HAL configuration shape from `examples/uart-dma-idle`, removing UART-only modules.
- [ ] Configure DMA1 Channel1 with memory-to-memory, both increments, word/word, normal mode and high priority.
- [ ] Fill the source with deterministic xorshift32 data, prefill the destination, start `HAL_DMA_Start_IT`, and wait with unsigned tick subtraction.
- [ ] Compare all 1024 words and map setup/start/DMA-error/timeout/mismatch/success to distinct LED patterns.
- [ ] Build with `cmake --preset bluepill "-DCUBEF1_PATH=../../.temp/STM32CubeF1"` and `cmake --build --preset bluepill`.

### Task 2: Binary and host regressions

**Files:**
- Create: `examples/dma-memcopy/tests/check_firmware.py`
- Create: `examples/dma-memcopy/tests/stm32f1xx_hal.h`
- Create: `examples/dma-memcopy/tests/dma_memcopy_tests.c`

**Interfaces:**
- Consumes: production `main.c`, `stm32f1xx_it.c`, built ELF/BIN.
- Produces: `dma-memcopy-host` CTest target and a deterministic firmware-check PASS line.

- [ ] Add `DMA_MEMCOPY_HOST_TESTS` to CMake with `-Wall -Wextra -Werror`.
- [ ] Implement test-double DMA start modes: success copy, corrupted copy, error callback, no callback, start failure and init failure.
- [ ] Assert success, mismatch, DMA error, timeout, start failure, configuration failure and tick-wrap timeout results.
- [ ] Inspect the real binary stack/reset/SysTick/DMA1_Channel1 vector and both 4096-byte aligned non-overlapping SRAM buffers.
- [ ] Run `python tests/check_firmware.py ...`, configure/build host tests, and run `ctest --preset host-tests`.

### Task 3: Book and catalog integration

**Files:**
- Modify: `docs/v1-drivers/14-dma.md`
- Modify: `examples/README.md`
- Modify: `README.md`

**Interfaces:**
- Consumes: verified example commands and evidence boundaries from Tasks 1–2.
- Produces: one new example index row, corrected complete-build count/list, and ch14 text that points to the real entry.

- [ ] Replace ch14’s missing-4-KiB-entry statements with `examples/dma-memcopy` and its exact build/host status.
- [ ] Add failure rows for timeout, TE and comparison mismatch without claiming board observations.
- [ ] Add pinned official ST GitHub and local reference-book pointers; keep book material as explanation-order evidence only.
- [ ] Update `examples/README.md` complete-build list, index table, ch14 mapping, directory tree and run instructions.
- [ ] Update root `README.md` example count/table/complete-build note; remove the duplicate `uart-dma-idle` tree entry while editing that block.

### Task 4: Verification and handoff

**Files:**
- Update: `implement-stage/dma-memcopy/BUILD_NOTE.md`
- Create: `implement-stage/dma-memcopy/FINAL_REPORT.md`
- Create/update: `implement-stage/dma-memcopy/SILENT_ASSUMPTION_SWEEP.json`

- [ ] Run the example success command after the final edit.
- [ ] Run `book.checks`, `book.build_html`, `slop_lint`, full book pytest, `check_assets`, `docs:build`, `site:images`, and `site:pages`.
- [ ] Render/read the built ch14 page and confirm the new example link and evidence wording.
- [ ] Run `task_verify` and report passed, failed and unverified separately.
- [ ] Run the independent sweep or record `SWEEP_UNAVAILABLE`; never claim an unavailable review passed.
- [ ] Commit only the scoped files, push the branch and open a PR without merging.

## Self-review

- SPEC coverage: Tasks 1–4 cover firmware, regression, docs and final evidence.
- Placeholder scan: no TBD/TODO steps; commands and outputs are explicit.
- Type consistency: `g_dma_src`/`g_dma_dst` are `uint32_t[1024]`; `HAL_DMA_Start_IT` receives item count 1024, not byte count 4096.
- Policy boundary: no existing tests or CI policy are edited; new example-local tests remain subject to review and `task_verify` may stay unverified.

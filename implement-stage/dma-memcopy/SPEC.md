# DMA memory-to-memory example SPEC

- Date: 2026-11-25
- Base commit: `bbdbb95577511bd4aa724cf9afb83ccfe9bb3a06`
- Branch: `feat/dma-memcopy-example`
- Artifact: `examples/dma-memcopy/` plus the matching ch14 and example-index entries
- Hardware status: `pending`

## Goal

Turn the ch14 “4 KiB DMA memory copy” item from a missing experiment design into a clean, fixed-board build path. The firmware copies 1024 32-bit words (4096 bytes) between two SRAM buffers with DMA1 Channel1 in normal mode, reports transfer completion/error through interrupts, compares the buffers, and makes the result observable on the BluePill PC13 LED.

## Inputs

- Current ch14 text and its explicit statement that no complete `DMA_MemCopy` entry exists.
- `examples/uart-dma-idle/` as the repository’s fixed F103 HAL/CMake pattern.
- STM32CubeF1 `v1.8.6`, HAL `77fbb30b7a1d02533980400083e48c559aae5a4f`, CMSIS device `8a76309ed1250d817e9c888c4417171d2ba3ba63`.
- RM0008 DMA semantics and the pinned HAL/CMSIS source.
- Official STM32CubeF1 `DMA_FLASHToRAM` example for configuration shape only.
- Local reference books for explanation order only: 《Mastering STM32》2e and 野火《STM32 HAL 库开发实战指南》.

## Outputs

- `examples/dma-memcopy/` with CMake/presets/toolchain/linker/dependency lock, firmware, vectors, HAL configuration, Wokwi pointer, README, host regression and ELF/BIN checks.
- ch14 updated so the 4 KiB experiment points to the real entry and distinguishes build/host evidence from board evidence.
- `examples/README.md` and root `README.md` updated with the new complete-build example and corrected complete-build list/count.
- ARIS artifacts under `implement-stage/dma-memcopy/`.

## Success command

From `examples/dma-memcopy/`:

```console
cmake --preset bluepill "-DCUBEF1_PATH=../../.temp/STM32CubeF1"
cmake --build --preset bluepill
python tests/check_firmware.py build/bluepill/dma-memcopy.elf build/bluepill/dma-memcopy.bin
cmake --preset host-tests
cmake --build --preset host-tests
ctest --preset host-tests
```

All commands must exit 0. The firmware check must prove the actual vector table, 4 KiB aligned non-overlapping SRAM buffers, and at least 2 KiB reserved stack. The host regression must cover success, mismatch, DMA error, timeout, start failure, configuration failure and tick-wrap timeout.

## Scope cuts

- One board only: STM32F103C8T6 / BluePill.
- One transfer shape: SRAM→SRAM, 1024 words, normal mode, DMA1 Channel1.
- No UART, FreeRTOS, cache maintenance, double buffering or F4 port.
- No new illustration or asset pipeline.
- No hardware flash/run/measurement in this slice.

## Non-goals

- No claim that a successful build or host test proves board behavior.
- No throughput, latency or oscilloscope claim.
- No change to existing tests, CI policy, runner inputs or manifests.
- No merge of PR #175 and no reuse of its root `implement-stage/` paths.

## Acceptance criteria

1. Firmware configures the locked HAL/CMSIS dependency and builds without warnings.
2. DMA1 Channel1 vector is present in the binary; SysTick and reset entries are correct.
3. Source and destination are each exactly 4096 bytes, 4-byte aligned, non-overlapping and inside the 20 KiB SRAM region.
4. Completion, error, timeout, mismatch and setup failures produce distinct program results and LED patterns.
5. Host regression exercises the production control flow with a controlled HAL test double.
6. ch14 no longer says the complete memory-copy entry is missing; it states what is and is not verified.
7. Book/site gates pass; `task_verify` is reported separately and remains unverified if no operator baseline exists.
8. Independent silent-assumption sweep returns a verdict or `SWEEP_UNAVAILABLE`.

# DMA memory-to-memory build note

Status: `F0/F1/F2/F3 PASS WITH DECLARED LIMITS`

## Rung ladder

### F0 — Complete firmware spine

- Create the fixed BluePill CMake project, locked dependencies, linker/startup/HAL configuration, SysTick and DMA1 Channel1 vectors.
- Implement the 4 KiB SRAM→SRAM transfer, TC/TE callbacks, wrap-safe timeout, buffer comparison and distinct LED result patterns.
- Acceptance: configure/build with the pinned CubeF1 tree, then run `tests/check_firmware.py` against the actual ELF/BIN.

- PASS: ARM build exited 0; BIN 6508 B, SHA-256 `4b032d24de2941e03c1b15000076a175e11ee75acb33b246a21331c377979347`; ELF SHA-256 `e2969dc929baf145d2d194be1ea732821ccfff9a8b7b40bdfc79bfed70527a5f`.
- PASS: `tests/check_firmware.py` verified SP `0x20005000`, reset `0x080005cd`, SysTick `0x080005a1`, DMA1_CH1 `0x080005ad`, two aligned non-overlapping 4096 B SRAM buffers, 8280 B static RAM and at least 2048 B reserved stack.

### F1 — Host regression

- Add a controlled HAL test double and production-flow regression.
- Cover success, mismatch, DMA error, timeout, start failure, configuration failure and tick-wrap timeout.
- Acceptance: `cmake --preset host-tests`, build, and `ctest --preset host-tests` all exit 0; rerun F0.

- PASS: unchanged `ctest --preset host-tests` exited 0 after RED; success, mismatch, DMA error, timeout, start failure, configuration failure, tick-wrap timeout and LED result codes are covered.

### F2 — Book and index integration

- Replace ch14’s “no complete entry” text with the real example and preserve the pending hardware status.
- Add the example to `examples/README.md` and root `README.md`; correct the complete-build list/count.
- Acceptance: `book.checks --check`, `book.build_html --check`, `slop_lint`, `docs:build`, `site:images`, `site:pages`; rerun F0/F1.

- PASS: `book.checks --check`、`book.build_html --check`（53 pages / 0 missing）、`slop_lint`、`docs:build`、`site:images`（363 images）、`site:pages`（54 pages）全部 exit 0；F0/F1 复跑通过。
- PASS: built ch14 page contains `examples/dma-memcopy`、NDTR 1024、pending hardware boundary and the new exit question; `scrollWidth == clientWidth == 1365` at the checked viewport.

### F3 — Final verification and review

- Run full book tests, asset checks and the narrow example checks after the final edit.
- Run `task_verify` and report passed/failed/unverified separately.
- Run an independent read-only silent-assumption sweep or record `SWEEP_UNAVAILABLE`.
- Acceptance: final report contains exact commands, exit codes, artifacts and deferred hardware work.

- PASS: final book checks/render/voice, 124 pytest, 583 assets / 14 photos, site build/images/pages, diff check and the complete example success command all exited 0 after the final code edit.
- UNVERIFIED: `task_verify run` returned `project-or-git-baseline-unavailable` with no configured checks; new example-local tests require reviewer attention.
- SWEEP_UNAVAILABLE: independent provider health check reported 0/1 healthy; no external acquittal claimed.
- Final report: `implement-stage/dma-memcopy/FINAL_REPORT.md`.

## Evidence rules

- A build proves compilation/linking only.
- The firmware checker proves binary vectors and memory layout only.
- The host regression proves program branches under a test double only.
- No rung proves on-board DMA behavior, timing, LED observation or measurement.

## Current state

F0–F3 are complete with the declared limits above. Hardware download/run/measurement remains pending. The work is ready for scoped review and handoff; no merge is authorized.

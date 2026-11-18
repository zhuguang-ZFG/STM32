# Local build repair Implementation Plan

> **For agentic workers:** Execute the approved local-only repair in sequence, with a red/green checkpoint before edits and verification before reporting.

**Goal:** Repair retired build/check entry points without consuming the existing WIP, then validate an isolated merged-edition PDF.

**Architecture:** Keep `book` as the authority. Make targets call its existing modules; the legacy asset command dispatches to current chapter/link/quiz checks plus real public SVG/raster validation. Keep legacy routines available only for legacy layouts. Print into a new external directory; never overwrite the existing PDF.

**Tech Stack:** Python unittest, GNU Make, Playwright Chromium, PyMuPDF.

## Global Constraints
- Local checkout `D:/Users/STM32`; no stage/commit/push, reset/clean/stash/rebase.
- Preserve 978 baseline status entries, including 89 deletions; do not regenerate assets or start video/narration.
- Directed backups and source hashes: `D:/Users/STM32-local-review-backup-20261118-154000`.
- Compare content hashes before writing an existing target; stop that write on mismatch.

## Tasks
- [x] Add `book/tests/test_build_entrypoints.py`; run `python -B -m unittest book.tests.test_build_entrypoints -v` and retain the expected failures.
- [x] Repair `Makefile` book/book-pdf/book-check entry points and `tools/check_assets.py` merged-layout dispatch. Verify that malformed assets and missing chapter assets still fail.
- [x] Update current instructions in `README.md`, `STRUCTURE.md`; add `book/README.md` documenting actual site/print commands and dependencies. Do not rewrite historical plans.
- [x] Verify manifest/checks, regression tests, existing WIP tests, full unittest, and temporary HTML build. Log exit codes without weakening expectations.
- [x] Inspect print side effects; ensure animation snapshots stay in memory rather than writing beside source assets. Build full print HTML/PDF externally after checking source stability.
- [x] Record PDF size/pages/hash, extracted text/font results, and rendered cover/contents/onramp/code/figure samples. Keep old PDF untouched; document limitations and concrete LED/PWM/UART evidence steps, no hardware actions.

No commit is authorized for this pass.

验收记录：`2026-11-18-local-build-acceptance.md`。全部改动保留未提交。

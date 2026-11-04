# Visual quality uplift — pilot ch02 / ch03 / ch06 / ch09 / ch10

Date: 2026-11-04 (America/Adak). Scope: figure density + animation quality only. Video/narration untouched.

## Problem

Prior B2–B7 met numeric §15 floors but still looked thin: long text walls, crude AUX GIFs (3–4 KB text slides), and mechanism demos that bounced without teaching.

## What changed (pilot)

### New static Handraw SVGs (+15)

| Chapter | Assets |
|---|---|
| ch02 | `sample-02-pll-lock.svg`, `sample-02-flash-latency.svg`, `sample-02-bus-matrix.svg` |
| ch03 | `sample-03-moder-map.svg`, `sample-03-current-path.svg`, `sample-03-exti-vs-poll.svg` |
| ch06 | `sample-06-baud-formula.svg`, `sample-06-frame-annotated.svg`, `sample-06-tx-rx-crossover.svg` |
| ch09 | `sample-09-sar-ladder.svg`, `sample-09-sample-time.svg`, `sample-09-vref-rails.svg` |
| ch10 | `sample-10-dma-phases.svg`, `sample-10-cndtr-ledger.svg`, `sample-10-mem2mem-vs-peri.svg` |

All under `assets/diagrams/`. Sepia-friendly Handraw via `tools/svgkit.py`; real register/timing numbers; first frame PDF-readable.

### New CSS-SVG mechanism animations (+5)

| Chapter | Asset |
|---|---|
| ch02 | `assets/animations/sample-02-pll-lock-flow.svg` |
| ch03 | `assets/animations/sample-03-gpio-bsrr-flow.svg` |
| ch06 | `assets/animations/sample-06-uart-baud-wire.svg` |
| ch09 | `assets/animations/sample-09-adc-sar-weights.svg` |
| ch10 | `assets/animations/sample-10-dma-circular-ht.svg` |

Purposeful multi-step motion (PLL lock / BSRR write / baud wire / SAR weights / circular HT), labeled stages, no empty bounce. Hash-locked legacy anims left alone.

### Remade crude AUX GIFs (in place, test-bounded)

| GIF | Before → After |
|---|---|
| `assets/gif/clock-css.gif` | ~text slides → 6 teaching frames, 8.1 KB (HSE→PLL→72 MHz→HSE gone→HSI) |
| `assets/gif/uart-idle.gif` | → 6 frames, 7.2 KB (idle / 86.8 µs story preserved) |
| `assets/gif/adc-sample.gif` | → 6 frames, 7.6 KB (12 MHz / sample time story) |
| `assets/gif/dma-cndtr.gif` | → 6 frames, 7.0 KB (CNDTR half-word ledger) |

Builders live in `tools/gen_gifs.py`; denser bodies in `tools/sample_figs_quality/gif_snippets/`.

### Embeds

zh + en for all 20 new assets (40 insert ops) via `tools/sample_figs_quality/embed_q.py`.

## Anchor deltas (img count in zh chapter)

| Chapter | Before (approx census / prior lock) | After | Δ |
|---|---:|---:|---:|
| ch02 | 8 | **11** | +3 |
| ch03 | 8 (locked) | **12** | +4 |
| ch06 | 6 | **10** | +4 |
| ch09 | 6 (locked) | **10** | +4 |
| ch10 | 6 (locked) | **10** | +4 |

Exceeds prior overlay floors by +3 to +4 meaningful anchors on each pilot chapter.

## Generator package

`tools/sample_figs_quality/` — `figures_q.py`, `anim_q.py`, `embed_q.py`, `patch_crude_gifs.py`, `gif_snippets/`, `gen_all.py`.

## Gates

- `python tools/check_assets.py` — PASS
- `pytest stm32-book/tests` — **180 passed**
- `python stm32-book/build_html.py --check` zh+en — PASS
- Dual-track honesty kept (no AI-fake 真证 photos)


---

## Batch 2 — ch04 / ch05 / ch07 / ch08 (this turn)

Pilot bar unchanged: denser meaningful figures (+2..+4), remade crude AUX GIFs, Handraw CSS-SVG mechanism anims, zh+en embeds, no video work.

### New static Handraw figures (+12)

| Chapter | Assets |
|---|---|
| ch04 | `sample-04-priority-group.svg`, `sample-04-tail-chaining.svg`, `sample-04-exti-line-map.svg` |
| ch05 | `sample-05-timebase-math.svg`, `sample-05-shadow-regs.svg`, `sample-05-deadtime.svg` |
| ch07 | `sample-07-start-ack.svg`, `sample-07-pullup-cap.svg`, `sample-07-sr-restart.svg` |
| ch08 | `sample-08-mode0-edges.svg`, `sample-08-br-table.svg`, `sample-08-nss-multi.svg` |

All under `assets/diagrams/`, 960×880, credit + real values (PRIGROUP / PSC·ARR·CCR / 0x78·ACK / Mode0·BR=010).

### New CSS-SVG mechanism animations (+4)

| Chapter | Asset |
|---|---|
| ch04 | `assets/animations/sample-04-nvic-preempt-flow.svg` |
| ch05 | `assets/animations/sample-05-pwm-edge-flow.svg` |
| ch07 | `assets/animations/sample-07-i2c-ack-flow.svg` |
| ch08 | `assets/animations/sample-08-spi-jedec-flow.svg` |

FA-002 continuous-line; reduced-motion first frame PDF-readable.

### Remade crude AUX GIFs (in place, test-bounded)

| GIF | Notes |
|---|---|
| `assets/gif/nvic-preempt.gif` | 6 frames, TIM2→EXTI0→stack→ISR→return (no SAME PREEMPT) |
| `assets/gif/pwm-1khz.gif` | 6 frames, CNT→CCR=500 edge, 1000 Hz / 500 µs |
| `assets/gif/i2c-addr.gif` | 6 frames, START→0x78→9th→ACK / 0x801E·4.7 k |
| `assets/gif/spi-jedec.gif` | 6 frames, CS↓ 0x9F → EF 40 17 @ 9 MHz |

Builders in `tools/gen_gifs.py`; denser bodies in `tools/sample_figs_quality2/gif_snippets/`.

### Embeds

zh + en for all 16 new assets (32 insert ops) via `tools/sample_figs_quality2/embed_q2.py`.

## Anchor deltas (img anchors in zh chapter, video stripped)

| Chapter | Before (prior lock) | After | Δ |
|---|---:|---:|---:|
| ch04 | 6 | **10** | +4 |
| ch05 | 6 | **10** | +4 |
| ch07 | 5 | **9** | +4 |
| ch08 | 6 | **10** | +4 |

## Generator package

`tools/sample_figs_quality2/` — `figures_q2.py`, `anim_q2.py`, `embed_q2.py`, `patch_crude_gifs.py`, `gif_snippets/`.

## Gates

- `python tools/check_assets.py` — PASS
- `pytest stm32-book/tests` — PASS
- `python stm32-book/build_html.py --check` zh+en — PASS
- Dual-track honesty kept; **no video** this turn

## Next queue (not done this turn)

1. **ch11–ch17** — reliability / USB / RTOS / LP / debug thin spots
2. **ch00–ch01, ch18–ch22** — onboarding + FAQ/boards/sim gaps
3. **ch23–ch28 + appendix** — pinmux / SPL / network / RTOS-system polish
4. Optional: rebuild bilingual PDF after next 1–2 batches

Do **not** claim whole-book visual quality done after this batch.

## Next queue (not done this turn) *(pilot — superseded by Batch 2 section above)*

### Pilot next-queue archive

1. **ch04, ch05, ch07, ch08** — interrupt / timer / I2C / SPI mechanism density + remake weak anims
2. **ch11–ch17** — reliability / USB / RTOS / LP / debug thin spots from B7 census
3. **ch00–ch01, ch18–ch22** — onboarding + FAQ/boards/sim gaps
4. **ch23–ch28 + appendix** — pinmux / SPL / network / RTOS-system polish
5. Optional: rebuild bilingual PDF after next 1–2 batches so pages pick up new figures

Do **not** claim whole-book visual quality done after this pilot.

## Batch 3 — ch11–17

Date: 2026-11-04 (America/Adak). Same bar as pilot/batch2: denser Handraw figures, remade AUX GIFs, FA-002 CSS-SVG anims. Video untouched.

### New static Handraw SVGs (+15)

| Chapter | Assets |
|---|---|
| ch11 | `sample-11-backup-domain.svg`, `sample-11-iwdg-math.svg` |
| ch12 | `sample-12-page-erase.svg`, `sample-12-key-order.svg` |
| ch13 | `sample-13-bit-quanta.svg`, `sample-13-filter-fifo.svg`, `sample-13-tec-busoff.svg` |
| ch14 | `sample-14-usbpre-48.svg`, `sample-14-pma-map.svg` |
| ch15 | `sample-15-task-states.svg`, `sample-15-fromisr.svg` |
| ch16 | `sample-16-mode-current.svg`, `sample-16-clock-restore.svg` |
| ch17 | `sample-17-swd-pins.svg`, `sample-17-cfsr-bits.svg` |

### New CSS-SVG mechanism animations (+7)

| Chapter | Asset |
|---|---|
| ch11 | `sample-11-iwdg-feed-flow.svg` |
| ch12 | `sample-12-iap-jump-flow.svg` |
| ch13 | `sample-13-can-arb-flow.svg` |
| ch14 | `sample-14-usb-48m-flow.svg` |
| ch15 | `sample-15-rtos-tick-flow.svg` |
| ch16 | `sample-16-stop-wake-flow.svg` |
| ch17 | `sample-17-cfsr-flow.svg` |

### Remade crude AUX GIFs (in place, test-bounded)

`iwdg-1s.gif`, `iap-jump.gif`, `can-500k.gif`, `usb-48m.gif`, `rtos-tick.gif`, `stop-wake.gif`, `cfsr-read.gif` — denser multi-panel frames; builders in `tools/gen_gifs.py` via `tools/sample_figs_quality3/gif_snippets/`.

### Embeds

zh + en for all 22 new assets (44 insert ops) via `tools/sample_figs_quality3/embed_q3.py`.

### Anchor deltas (asset_sequence length, video stripped)

| Chapter | Before | After | Δ |
|---|---:|---:|---:|
| ch11 | 6 | **9** | +3 |
| ch12 | 6 | **9** | +3 |
| ch13 | 4 | **8** | +4 |
| ch14 | 7 | **10** | +3 |
| ch15 | 7 | **10** | +3 |
| ch16 | 6 | **9** | +3 |
| ch17 | 6 | **9** | +3 |

### Gates

`pytest` book tests + `tools/check_assets.py` + `build_html.py --check` (zh+en) green after this batch.

### Next round

ch00–01 / ch18–22 (same bar). No video.


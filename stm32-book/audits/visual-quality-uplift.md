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

## Next queue (not done this turn)

1. **ch04, ch05, ch07, ch08** — interrupt / timer / I2C / SPI mechanism density + remake weak anims
2. **ch11–ch17** — reliability / USB / RTOS / LP / debug thin spots from B7 census
3. **ch00–ch01, ch18–ch22** — onboarding + FAQ/boards/sim gaps
4. **ch23–ch28 + appendix** — pinmux / SPL / network / RTOS-system polish
5. Optional: rebuild bilingual PDF after next 1–2 batches so pages pick up new figures

Do **not** claim whole-book visual quality done after this pilot.

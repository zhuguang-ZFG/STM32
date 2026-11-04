# Handraw beauty sample — ch03 GPIO

Date: 2026-11-04 (America/Adak planning pass)

## Why this pass

Existing ch03 “handdraw” assets (`ch03-handdraw.svg`, several `sample-03-*.svg`) are thin geometric boxes. Spec §6 wants Handraw knowledge-track visuals with registered **Layout / Style / Color**, not desk-prop miniatures and not AI fake evidence photos.

This sample plans **6** true handraw-style article illustrations for ch03. Parent will `GenerateImage`; embedding waits until images exist.

## Aesthetic system (one chapter, one voice)

| Role | Pick | Why |
| --- | --- | --- |
| Concept / current-path / before-after | **FA-002** Conceptual Continuous-Line Editorial (Saul Steinberg) | Continuous-line editorial clarity; witty without dolls; good for current metaphors |
| Structure / compare / hierarchy | **FA-029** Geometric Diagrammatic Narrative (Chris Ware) | Quiet diagrammatic city-chart feel; perfect for dual columns and layered modes |
| Correct / safe path | **C-10** Sage Green | Calm “this is the right wiring” |
| Rational / hierarchy | **C-03** Prussian Blue | Deep, technical calm |
| Formula highlight | **C-27** Naples Yellow | Soft spotlight on EST numbers without neon |
| Contrast / caution | **C-31** Payne's Grey | Cool neutral for PP vs OD and poll vs EXTI |

Layouts stay inside Spec §6 priority set: **IG-011, IG-004, IG-012, IG-002**.

Activation check (`resolve_reference.py --model gpt-image-2`): FA-002 / FA-029 are **strong** name activation → prompts use author+style name; style tiles are optional consistency pads, not content sources.

## Figure map

1. **common-anode before/after** — replaces thin `ch03-handdraw.svg` under 最小胜利
2. **push-pull vs open-drain** — new primary visual before the comparison table
3. **PA0 OK vs PC13 wrong** — becomes primary teaching visual for 关键插图 (SVG may stay as precision companion)
4. **GPIO three-question layers** — new visual before the 8-mode table
5. **LED current-limit callout** — replaces thin `sample-03-current-path.svg` as primary
6. **poll vs EXTI** — replaces thin `sample-03-exti-vs-poll.svg` as primary

## Stay SVG / other tracks

- Register map `sample-03-moder-map.svg`
- BSRR / blink / input animations
- BluePill pinout SVG
- stack-diagram PNG (still labeled 原理示意/非实拍)
- Wikimedia Blue Pill photos (真证轨 only)

## Hard constraints honored

- Knowledge track only; every caption must say **原理示意/非实拍**
- No coffee cups / fairy dolls / desk miniatures
- Preserve quantitative facts: 270 Ω, (3.3−2.0)/0.005, DS5319 note 5 (3 mA / 2 MHz / 30 pF), EST mark
- No AI fake PC13 LED close-up as evidence

## Plan file

`D:\Users\STM32\.temp\handraw-ch03-plan.json`

Stop here for parent GenerateImage.

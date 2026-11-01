# Content style guide (required reading for contributors)

> 中文：[内容风格指南（贡献者必读）](../CONTENT_GUIDE.md)

This repo is an **STM32 knowledge base for learners who read Chinese**, organized the way [WaytoAGI](https://github.com/waytoagi/WaytoAGI) is organized:
a portal home page, a chaptered knowledge base, visuals (animation, diagrams, board drawings), runnable code, and cheatsheets.

This file is the English edition of that guide. Please follow the rules below so the 20+ chapters stay in one voice.

## 1. Files and names

- Chinese chapters live in `docs/`, named `NN-中文标题.md` (NN is two digits, for example `05-定时器与PWM.md`).
- English chapters live in `docs/en/`. Their names are the slugs in [contents.md](contents.md), for example [`05-timer-pwm.md`](05-timer-pwm.md).
- Example code lives in `examples/<module>/`. Each example directory contains `README.md` and `main.c` (a `Makefile` is optional).
- Chinese cheatsheets live in [`../../cheatsheets/`](../../cheatsheets/). English cheatsheets live next to these chapters: [`cheatsheets/hal.md`](cheatsheets/hal.md), [`cheatsheets/registers.md`](cheatsheets/registers.md), [`cheatsheets/bus-and-pins.md`](cheatsheets/bus-and-pins.md), [`cheatsheets/errors.md`](cheatsheets/errors.md).
- Images always use a **relative path**. From a chapter in `docs/en/`, that is `../../assets/animations/gpio-blink.svg`. Chinese chapters in `docs/` use `../assets/animations/gpio-blink.svg`.

## 2. The fixed skeleton of every chapter

```markdown
# NN Title

> One sentence on what this peripheral or topic is for (40 words or fewer).

<p align="center">
  <img src="../../assets/animations/xxx.svg" width="760" alt="xxx animation">
  <br><sub>▲ Animation: xxx (a GIF or an SVG both play directly on the GitHub page)</sub>
</p>

## Principle and scope
Say which order code, clock, and manual revision the chapter's numbers are for, and which numbers change on another family and what they become.

## Key figures
Put the key figures in this section.

## Timing and state
One timing table or state table you can calculate back from. If there is no electrical timing, write the state transitions, and do not leave the heading empty.

## Pitfalls and sources
| Symptom | Cause | What to do | Source | What the source shows |
| --- | --- | --- | --- | --- |

## Learning goals
- [ ] Goal 1
- [ ] Goal 2

## Core ideas
(Use a table or a figure to show what the hardware is doing, and include one picture from assets/diagrams or animations)

## Hardware and wiring
| Board | Peripheral | Pin | Notes |
| --- | --- | --- | --- |

## Code
The important fragment (HAL first, with a register or LL counterpart beside it). The full project is under `../../examples/...`.

## Hands-on labs
1 to 3 labs, easy then harder, each with the result you should see.

## Related resources
- The official reference-manual chapter, the datasheet chapter, and links to related chapters
```

If a chapter has `<!-- video: -->` … `<!-- /video: -->`, the first four sections still go after that comment ends and before the learning goals, the same place as chapters 00, 03, 04, and 06. Those chapters are the examples. This edition does not rewrite chapter prose. The skeleton above does not include the narration script or the `<!-- video: -->` comment.

- "Pitfalls and troubleshooting" is no longer a skeleton heading. Move the rows that used to sit in that section into "Pitfalls and sources". Do not keep two names, and do not leave an empty heading. Chapters that are not thickened yet keep the old heading until a later batch.
- Each row states one claim. The source cell is a link to `#source-{id}`. `{id}` is an id already listed under `sources` in both manifests. After the build, the target is the Appendix E card `id="source-{id}"`.
- Do not start a second source table. A new source gets its id appended to `sources` in both manifests.
- Write the first four sections for the reader, not the reviewer. Leave out drafting words such as "key figure", "normal path", "in the margin", "is void", or "do not invent". State the fact and the condition instead, for example "on an F4 this address becomes 0x…". `tools/slop_lint.py` flags these words.

## 3. How to write

1. **Conclusion first, then the mechanism.** The first sentence of each section is something you can use immediately.
2. **Use tables.** Parameters, register bits, and trap checklists belong in tables, not in long stacked paragraphs.
3. **Match words to pictures.** Every animation or diagram the text mentions appears once in the chapter, with a `<sub>` caption.
4. **Code must compile.** Samples are real HAL you can build (the `HAL_` prefix), with the headers, `main()`, and the comments you need. Do not write pseudocode. Parameters are macros, so there are no magic numbers.
5. **Label the pictures honestly.** Every figure in this repo is an **author-drawn vector (SVG) or a program-generated GIF**, not a vendor photograph. If you want a photograph, link the official product page (in a "Board and documents" subsection). Do not call a drawing a photograph.
6. Use the same words: `GPIO`, timer (`TIM`), interrupt (`IRQ`), `DMA channel`, `HAL / LL / registers`.
7. Line width is not limited. Do not use an HTML `<script>`, and do not use images hosted off-site (GitHub's proxy will fail).

## 4. Visual-asset inventory (generated by scripts under `tools/`; do not edit the files by hand)

See [`../../assets/README.md`](../../assets/README.md). A chapter may cite only filenames that are already on that list. If you truly need a new figure, say so in an issue or a pull request, or generate it with [`../../tools/svgkit.py`](../../tools/svgkit.py) and then cite it.

## 5. Commit style

```text
docs(05): add the PWM duty-cycle formula and the breathing-LED animation
fix(gif): fix led-blink.gif timing so it matches the 1 Hz note
```

One commit does one thing. For images, especially GIFs, check that the file is under 500 KB.

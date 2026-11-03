# Content style guide (required reading for contributors)

> 中文：[内容风格指南（贡献者必读）](../CONTENT_GUIDE.md)

This repo is an **STM32 knowledge base for learners who read Chinese**, organized the way [WaytoAGI](https://github.com/waytoagi/WaytoAGI) is organized:
a portal home page, a chaptered knowledge base, visuals (animation, diagrams, board drawings), runnable code, and cheatsheets.

This file is the English edition of that guide. Please follow the rules below so the 20+ chapters stay in one voice.

## Write for the reader, not the reviewer

Body text—especially Principle and scope, Key figures, Timing and state, and Pitfalls and sources—is for learners, not for reviewers or author notes.

Do not leak drafting jargon into reader prose. The ban list matches the `审稿用语` group in `tools/slop_lint.py`, for example:

- "key figure", "normal path", "in the margin", "pinned only to", "copied whole", "do not invent"
- "is void" / "are void" (except Cache "clean or invalidate" wording when that is the real term)
- table header "claim this source may support" (use "what you can look up in the source" instead)

State the fact and the condition, for example: "on an F4 this address becomes 0x…".

Hard gate: `python tools/slop_lint.py` from the repo root. Contributor meta-docs may name the skeleton; chapter body may not.


## Rhythm, layering, and self-checks (ported from handraw, Port B)

Banned words stay with `tools/slop_lint.py`. The three rules below are for human reading and the Sepia workflow; lint cannot replace them. The full contract is in [`../../stm32-book/BOOK_CLASSIC_CONVERGE_SPECS.md`](../../stm32-book/BOOK_CLASSIC_CONVERGE_SPECS.md) §5 and §6.

### Rhythm

- Let sentence and paragraph length follow the content; do not lock a chapter to one beat length.
- Do not reuse one 8–10 beat narration or memory-card template across consecutive chapters, and do not stretch a short-form beat sheet into a long lesson. The allowed beat pool and hard bans are in Overlay §5.4.
- When rewriting a section or a chapter: run Sepia `review` for a defect list **first**, then `refactor` item by item. Do not edit while reading in a way that only makes the text longer. Skills live under [`.claude/skills/sepia/`](../../.claude/skills/sepia/SKILL.md); entry points are `sepia-review` / `sepia-refactor`. Day-to-day voice rules are in [`.claude/skills/plain-voice/SKILL.md`](../../.claude/skills/plain-voice/SKILL.md).

### Layering

Keep this reading order; later layers may be skipped on a first pass, but do not invert them:

1. **Minimum win**: one small result the reader can verify on the board or in simulation (an observable effect).
2. **Mechanism**: why the current, bytes, state, or register behave that way.
3. **Manual density**: orderable part, revision, table numbers, addresses, and edge conditions come last; a first-time reader may skip them until after the labs.

Turn "conclusion first, then the mechanism" into: **state a verifiable minimum-win conclusion first, then the mechanism; push manual density later.**

### Self-checks (required before you finish an edit)

1. **Leave check**: with the section closed, the reader can still restate the minimum win and one failure signal.
2. **Deletion check**: if removing a new phrase does not change the meaning, delete the new phrase (Sepia deletion test).
3. **Reversion check**: if the earlier sentence was shorter, clearer, and already in the right voice, keep it; do not rewrite for polish alone (Sepia reversion test).

Code, URLs, IDs, table data, `<!-- video: -->` / `<!-- links: -->` blocks, and `#source-` links are protected ranges; voice skills must not rewrite facts there.

### Handraw vs evidence (pointer)

Technical and conceptual figures use the Handraw knowledge track (Layout / style / palette registration; see Overlay §6 and `.claude/skills/handraw-style`). Board photos and instrument captures use the evidence track. Never fake evidence with AI, and never call a drawing a photograph. Planning fields live in the Overlay; this guide only points there.

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
- The first four sections still follow **Write for the reader, not the reviewer** above; `tools/slop_lint.py` enforces the ban list.

## 3. How to write

1. **Minimum win first, then the mechanism; manual density later.** The first sentence is a verifiable minimum conclusion; mechanism follows; orderable-part and table density come after.
2. **Use tables.** Parameters, register bits, and trap checklists belong in tables, not in long stacked paragraphs.
3. **Match words to pictures.** Every animation or diagram the text mentions appears once in the chapter, with a `<sub>` caption.
4. **Code must compile.** Samples are real HAL you can build (the `HAL_` prefix), with the headers, `main()`, and the comments you need. Do not write pseudocode. Parameters are macros, so there are no magic numbers.
5. **Label pictures on two tracks.** The Handraw knowledge track covers technical and conceptual figures (registration in Overlay §6). The evidence track is for board photos and instrument captures. Many figures here remain **author-drawn vectors (SVG) or program-generated GIFs**, not vendor photographs. For a photograph, link the official product page ("Board and documents"). Do not call a drawing a photograph, and do not fake measurements with AI.
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

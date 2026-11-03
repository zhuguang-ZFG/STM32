# Content style guide (required reading for contributors)

> 中文：[内容风格指南（贡献者必读）](../CONTENT_GUIDE.md)

This repo is an **STM32 knowledge base for learners who read Chinese**, organized the way [WaytoAGI](https://github.com/waytoagi/WaytoAGI) is organized:
a portal home page, a chaptered knowledge base, visuals (animation, diagrams, board drawings), runnable code, and cheatsheets.

This file is the English edition of that guide. Please follow the rules below so the 20+ chapters stay in one voice.

## Write for the reader, not the reviewer

Body text—especially principle, figure captions, timing and state, and pitfalls and sources—is for learners, not for reviewers or author notes.

Do not leak drafting jargon into reader prose. The ban list matches the `审稿用语` group in `tools/slop_lint.py`, for example:

- "key figure", "normal path", "in the margin", "pinned only to", "copied whole", "do not invent"
- "is void" / "are void" (except Cache "clean or invalidate" wording when that is the real term)
- table header "claim this source may support" (use "what you can look up in the source" instead)

State the fact and the condition, for example: "on an F4 this address becomes 0x…".

Hard gate: `python tools/slop_lint.py` from the repo root. Contributor meta-docs may discuss the teaching contract and function blocks; chapter body may not narrate the review process.


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

## 2. Teaching contract and optional function blocks

Chapters are **not** required to share one fixed heading order. Merge gates check that **teaching-contract fields are registered** and that **chosen function blocks finish their cognitive job with no empty headings**. The full contract is [`../../stm32-book/BOOK_CLASSIC_CONVERGE_SPECS.md`](../../stm32-book/BOOK_CLASSIC_CONVERGE_SPECS.md) §4; this guide only lands the writing rules. Division remaps and video render parameters do not belong here.

### 2.1 Teaching-contract fields (required registration)

Register these fields for each chapter in `manifest` `chapter_guides` (or an equivalent machine-readable table)—seven core fields plus prerequisites. Chinese and English must share the same facts; wording may differ:

| Field | Contract meaning | Checkable standard |
| --- | --- | --- |
| Entry problem | An observable symptom or concrete task the reader already faces | Appears within the first ~120 characters; no theme-teaser openings |
| Prerequisites | Only concepts already taught; define later concepts in one minimal line before use | Audit must not find undefined key terms that depend on later chapters |
| Minimum win | One runnable, measurable, or table-checkable result | Before long manual-density tables; steps independently reproducible |
| Core mechanism | One primary cognitive hard point | Only one main metaphor or relationship figure competes for attention |
| Failure branch | At least one distinguishing evidence and next check | Must not end with "maybe it is broken" |
| Migration boundary | What must be rechecked when chip, library, clock, package, or software stack changes | Written as items, not a vague "watch portability" note |
| Memory anchor | An accurate metaphor **or** core relationship figure **or** recite-able mnemonic (combinable, but pointing at the same mechanism) | After a metaphor, give "where it fits / where it fails" |
| Leave check | A question answerable without the book + an action the reader can do alone | Aligned with that division's L0–L5 delivery; coverable by quiz or lab |

- **Thorough** = core mechanism + failure branch + migration boundary all hold.
- **Clear at a glance** = entry problem + minimum win finish before the manual wall, and the memory anchor fits on one page.
- **From beginner to expert** = the reader can name which L0–L5 level they stopped at and which evidence the next level still needs—not that they finished 29 chapter titles.

### 2.2 Reading-order principle (heading names may vary)

1. Entry problem / contrast symptom
2. Minimum win (short steps + expected evidence)
3. Core mechanism (one hard point)
4. Expand as needed: timing, formulas, registers, full tables, family differences
5. Failure branches and triage
6. Migration boundary
7. Leave check

Full register tables, electrical limits, and long API lists may follow the mechanism or sit in appendix-style subsections. Do not stack a "principle and scope" style manual wall before the minimum win.

### 2.3 Optional function-block checklist

Pick function blocks **as needed**. Not every block must appear, and order is not fixed. Any block you use must finish its cognitive job; empty headings are banned:

| Function block | When to use | Done when |
| --- | --- | --- |
| Field problem / failure symptom | Almost every chapter | Observable and restatable |
| One-line intuition | When concepts blur easily | ≤40 words, then corrected by the mechanism |
| Minimum runnable steps | Every chapter needs an equivalent | Includes expected symptom or measurement |
| Hardware data path / state machine / timing | L1–L5 mechanism chapters | Calculable back, or step-by-step reconcilable |
| Recalculable formula and parameter conditions | Dividers, baud rates, sampling, etc. | Variables, units, and applicable orderable part listed |
| Measurement method and evidence | Whether a config actually hit the hardware | Probe / window / read-back location named |
| Common misreads and shortest triage | Two or more easy-to-confuse causes | Each row: symptom / distinguishing evidence / next action / source |
| Cross-family migration boundary | Numbers change by family | Lists what stays / what must be rechecked |
| Easy-to-hard labs | When hands-on practice is needed | 1–3 labs, rising difficulty, distinguishable expected results |
| Leave-check questions | Every chapter needs an equivalent | Answerable without the book + action acceptance |
| Code (HAL first; LL / registers / SPL with boundaries) | When a buildable fragment is needed | Real compile boundary stated; full project linked under `examples/` |
| Hardware and wiring table | Concrete pins | Board / peripheral / pin / notes |
| Related resources | Manual orientation needed | Concrete manual sections and source ids, not a link dump |

Chapters may still open with a one-sentence lead-in (40 words or fewer) and a centered hero visual (relative path, for example `../../assets/animations/xxx.svg` from `docs/en/`).

### 2.4 Video comment region, sources, and legacy headings

- If a chapter has `<!-- video: -->` … `<!-- /video: -->`, prose after that comment still follows **Write for the reader, not the reviewer**, the same place as chapters 00, 03, 04, and 06. This guide does not rewrite chapter prose, and it does not embed narration scripts or `<!-- video: -->` syntax details here.
- "Pitfalls and troubleshooting" is no longer a heading. Move those rows into "Pitfalls and sources" (or the equivalent function block "Common misreads and shortest triage"). Do not keep two names, and do not leave an empty heading. Chapters not yet thickened may keep the old heading until a later batch; **new rewrites and the ch03 sample chapter** must follow §2.1–2.3.
- Each row states one claim. The source cell is a link to `#source-{id}`. `{id}` is an id already listed under `sources` in both manifests. After the build, the target is the Appendix E card `id="source-{id}"`.
- Do not start a second source table. A new source gets its id appended to `sources` in both manifests.
- `tools/slop_lint.py` enforces the ban list.

## 3. How to write

1. **Minimum win first, then the mechanism; manual density later.** The first sentence is a verifiable minimum conclusion; mechanism follows; orderable-part and table density come after.
2. **Use tables.** Parameters, register bits, and trap checklists belong in tables, not in long stacked paragraphs.
3. **Match words to pictures.** Every animation or diagram the text mentions appears once in the chapter, with a `<sub>` caption.
4. **Code must compile.** Samples are real HAL you can build (the `HAL_` prefix), or clearly version-pinned STM32F10x SPL, with the headers, `main()`, and the comments you need. Do not write pseudocode. Parameters are macros, so there are no magic numbers. SPL content must name the family, version, and migration boundary.
5. **Label pictures on two tracks.** The Handraw knowledge track covers technical and conceptual figures (registration in Overlay §6). The evidence track is for board photos and instrument captures. Many figures here remain **author-drawn vectors (SVG) or program-generated GIFs**, not vendor photographs. For a photograph, link the official product page ("Board and documents"). Do not call a drawing a photograph, and do not fake measurements with AI.
6. Use the same words: `GPIO`, timer (`TIM`), interrupt (`IRQ`), `DMA channel`, `HAL / LL / SPL standard peripheral library / registers`.
7. Line width is not limited. Do not use an HTML `<script>`, and do not use images hosted off-site (GitHub's proxy will fail).

## 4. Visual-asset inventory (generated by scripts under `tools/`; do not edit the files by hand)

See [`../../assets/README.md`](../../assets/README.md). A chapter may cite only filenames that are already on that list. If you truly need a new figure, say so in an issue or a pull request, or generate it with [`../../tools/svgkit.py`](../../tools/svgkit.py) and then cite it.

## 5. Commit style

When a commit changes a chapter, the message should note these checks: teaching contract registered, function-block checklist, narration beat fingerprint, Sepia deletion/reversion (see the Overlay).

```text
docs(05): add the PWM duty-cycle formula and the breathing-LED animation
fix(gif): fix led-blink.gif timing so it matches the 1 Hz note
```

One commit does one thing. For images, especially GIFs, check that the file is under 500 KB.

---
name: plain-voice
description: Write this STM32 book's Markdown the way a book reads, not the way generated copy reads. Use when writing or editing any .md in this repo, including chapters under docs/ and docs/en/, cheatsheets, appendices under stm32-book/book/, example READMEs, and the top-level README and CONTRIBUTING. Covers Chinese and English. Not for code, commit messages, or planning notes under docs/superpowers/.
license: MIT
---

# Plain voice

Prose in this repo is a book's prose. The mechanical half is
`tools/slop_lint.py`. Run `python3 tools/slop_lint.py`, or `make lint-voice`
where make is available. It gates CI and is mirrored by
`stm32-book/tests/test_slop_lint.py`. Rhythm and paragraph flow stay with human
reading. Run it before you commit Markdown.

Shape and rules adapted from two public skills: `tazhate/anti-ai-slop` and
`HermeticOrmus/markdown-discipline`.

## Decisions go in words, not glyphs

| Instead of | Write | Why |
| --- | --- | --- |
| `✅` / `❌` in a table cell | `支持` / `不支持`, `可以` / `不能`, `必需` / `可选`, `无` / `单精度` | Every such column already holds words, so the glyph is the inconsistent cell. A glyph also carries no degree and does not read aloud |
| `> ⚠️ text` | `> [!WARNING]`, then the text on the next `>` line | GitHub renders the alert natively, and `build_html.py` reads the token for the callout class then drops it |
| `## 📌 学习目标` | `## 学习目标` | A heading that states its content needs no glyph |
| A fence with no language | Name the language; use `text` for ASCII diagrams, formulas, and console output | Without a language a highlighter colours arrows and operators as code |

The five alert tokens map to three callout classes: `[!WARNING]` and
`[!CAUTION]` are warnings, `[!TIP]` is a tip, `[!NOTE]` and `[!IMPORTANT]` are
notes. The build prints its own label, so do not also write `注意：` in the text.

## Words to cut

| Instead of | Write | Why |
| --- | --- | --- |
| `赋能` `助力` `一站式` `全方位` `轻松搞定` `完美支持` | What it actually does | These carry no information |
| `让我们` `综上所述` `值得注意的是` `众所周知` | Delete it and say the next sentence | Stage directions, not content |
| `说实话` `老实说` `划重点` `干货` | Delete it | Announcing honesty is not honesty |
| `delve` `leverage` `robust` `comprehensive` `seamless` `pivotal` `dive in` | A specific word | Same rule, English side |
| `Hope this helps` `Let me know if` `feel free to` | Nothing; end on the fact | A reference book does not sign off |

Keep technical verbs that only look like marketing: `unlock` (the Flash KEY1 /
KEY2 sequence), `支持`, `使能`. They are the right words for what they name.

## Correct typography, deliberately kept

Do not "fix" these; a linter rule here would fire on correct writing:

- `★` difficulty ratings in chapter 19. A tested rating scale, not decoration.
- `—` as the empty cell in a table. It means "not applicable".
- `–` inside a numeric range: `48–72 MHz`, `0x0000_0000–0x1FFF_FFFF`, `2.7–3.6 V`.
- `——` in Chinese prose. Ordinary punctuation, not an em-dash habit.
- `不是 X，而是 Y` when both halves carry a fact. `多半不是晶振坏了，而是域还锁着`
  names the wrong diagnosis and then the right one; that is the useful sentence.
  The tell is *empty* antithesis used for drama.
- Three nouns joined by `、`. That is a list, not a rhetorical tricolon.
- Several bold spans in one `**结论**：` line, where each marks a term being
  defined. The emphasis is doing structural work.

## Both editions move together

`docs/` and `docs/en/` mirror each other, as do the appendices under
`stm32-book/book/` and `stm32-book/book/en/`. Change a table cell, a heading, or
a callout in one and make the same change in the other in the same commit. The
chapter contract tests compare the two and will catch a one-sided edit.

## Escapes

A banned word inside inline code, a link, a fenced block, or `「」` / `""`
quotation is already ignored, because citing a term is not using it. For
anything else:

```text
行尾 <!-- slop-lint: ignore -->          跳过这一行
<!-- slop-lint: off --> … <!-- slop-lint: on -->   跳过中间整段
```

## Before you commit

```bash
python3 tools/slop_lint.py                      # fast, stdlib only
python3 -m unittest discover stm32-book/tests   # if you touched chapter text
python3 stm32-book/build_html.py --check
```

Then reread the paragraph you changed. Does its second half add anything? Does
each bullet say something distinct? Would a comma do the work of that dash?

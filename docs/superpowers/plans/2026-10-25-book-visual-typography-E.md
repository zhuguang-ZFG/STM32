# 整书排版微抛 E Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

I'm using the writing-plans skill to create the implementation plan.

**Goal:** 只做刀 E 的排版微抛：在 `stm32-book/build_html.py` 的内联 `CSS` 字符串里收进字号阶梯、目录三种读法、代码块和行内色块、图注，以及仍写在同一段 `CSS` 里的三处印刷微调，合入时把整书标成 **1.2.4 · 2026-10-25**。Book CI 变绿后 squash 合入，不等人复审章节 HTML。

**Architecture:** 样式仍是 `build_html.py` 里的一个 `CSS` 字符串，从 `:root` 到 `@media print`。先在 `stm32-book/tests/test_build.py` 里把新 token、选择器和四对对比写成断言，再只改这个字符串，最后同一提交改两份 manifest、`revisions.json` 和 `stm32-book/README.md`。`toc_html`、分类函数、罗盘 HTML、书签和章号不动。不新开 `.css`，不新开 token JSON，不新开测试文件，不新开锁定 JSON。

**Tech Stack:** Python 3 标准库、现有 `stm32-book/build_html.py`、`python3 stm32-book/tests/test_build.py`、`python3 -m unittest discover stm32-book/tests -v`。对比度沿用测试文件里已有的 `_contrast_ratio`。不新增依赖，不改 `requirements.txt`。

`stm32-book/tests/` 不是 Python 包。单条测试写成 `python3 stm32-book/tests/test_build.py BookBuildContractTests.<方法名> -v`。不要写成 `python3 -m unittest stm32-book.tests...`。整套测试仍用 `python3 -m unittest discover stm32-book/tests -v`。类名是 `BookBuildContractTests`，不是 `BookBuildTests`。

设计规格：`docs/superpowers/specs/2026-10-25-book-visual-typography-E-design.md`（PR #35）。

写本计划时的尖端是 `ee05fa3baeec6ebbb6271ab53c32c98286f87a5c`（`docs: 整书排版微抛 E 设计规格 (#35)`）。这一尖端的整书版本仍是 **1.2.2**，日期仍是 2026-10-25。`build_html.py` 的 `CSS` 字符串从第 954 行到第 1220 行，和设计核对过的 `ea11ce7b2dd02cec4e46a6abcb701a0286faef4a` 是同一段样式。下面的 CSS 行号属于 `ee05fa3`。Batch4 的计划不改 `build_html.py`。实施时若行号被别的提交挪动，按选择器原文定位。

实施基线不是 `ee05fa3`。实施从 Batch4 的 **1.2.3** 已经在 `main` 上之后的那个尖端另开分支。那个尖端的版本字面量会是 1.2.3（或更高，见开工条件）。本计划的 PR 只新增本文件，不改 `stm32-book/`。

本刀不新增 lock JSON，也不新增 source list。设计已经把字号、选择器和印刷片段写死。Batch4 的 `2026-10-25-batch4-01-07-10-11-lock.json` 属于另一刀，本计划不读、不改。

## Global Constraints

- 实施时只改 `stm32-book/build_html.py` 的 `CSS` 字符串、`stm32-book/tests/test_build.py`、`stm32-book/revisions.json`、`stm32-book/manifest.json`、`stm32-book/manifest-en.json`、`stm32-book/README.md`。
- 目标版本是 **1.2.4 · 2026-10-25**。日期写死 `2026-10-25`。设计规格里「日期用实施当天」那一句，按本计划任务改成这个冻住的日期。两份 manifest、`revisions.json` 和 README 写同一个日期。
- Batch4 的 **1.2.3** 还没出现在 `main` 的 `stm32-book/manifest.json` 时，不开实施 PR，除非用户当时明确说可以提前。
- 实施 PR 在 Book CI（`.github/workflows/book.yml`，名称 `Book CI`）变绿之后 squash 合入 `main`。不照搬 Batch4 的「等人看完四章 HTML 再合」。这一刀不改正文。
- 不打 tag，不创建 GitHub Release。合入后在本机 `D:\Users\STM32` 拉取这次 `main`。拉取不产生仓库 diff。
- 亮色保持 `--paper: #fbfaf7`、`--ink: #17202a`、`--accent: #075e84`、`--muted: #5e6872`、`--warn: #9a3d1c`、`--tip: #1b5c45`、`--spine: #c4552a`、`--code: #101820`、`--code-ink: #eef6f8`。暗色保持 `--code: #0a141c`、`--code-ink: #edf6f9`，其余暗色十六进制也不改。
- 1.2.0 的间距、圆角和阴影继续锁住：`--space-bar: 0.75rem`、`--space-paragraph: 1.25rem`、`--space-figure: 1.5rem`、`--space-chapter: 3.5rem`、`--inset: 6%`、`--leading-body: 1.75`、`--tracking-body: 0.01em`、`--tracking-kicker: 0.14em`、`--radius: 0.7rem`、`--elev: 0 1px 2px color-mix(in srgb, var(--ink) 8%, transparent)`。`--measure: 40rem` 不改。`.book` 的宽度不改。
- 只在亮色 `:root` 新增这些自定义属性：`--font-sans`、`--font-mono`、`--type-body: 1.0625rem`、`--type-h1: clamp(1.85rem, 4.2vw, 2.7rem)`、`--type-h2: 1.55rem`、`--type-h3: 1.35rem`、`--type-h4: 1.2rem`、`--type-kicker: 0.78rem`、`--type-small: 0.9375rem`、`--type-code: 0.92em`、`--leading-heading: 1.35`、`--leading-caption: 1.55`、`--leading-toc: 1.45`、`--leading-code: 1.65`。暗色和印刷不重抄这组属性。`font-size` 写在 `body` 上，不写在 `html` 上。
- `--font-sans` 的值是 `"Noto Sans CJK SC", "Microsoft YaHei", "PingFang SC", "Noto Sans SC", "Source Han Sans SC", "Segoe UI", system-ui, sans-serif`。`--font-mono` 的值是 `"Cascadia Mono", "SFMono-Regular", Consolas, "Noto Sans Mono CJK SC", "Source Han Mono SC", "Sarasa Mono SC", "Liberation Mono", ui-monospace, monospace`。
- 不加 `@font-face`，不写 `url(`，不引用 `fonts.googleapis` 或 `fonts.gstatic`。
- 封面 `h1`、封面副题、`.part-divider h1`、`.part-goal`、`.part-index`、窄屏 `.part-index` 的 `3rem`、`.toc-jump` 的字号和投影保持现在的字面量，不引用这组 token。
- 不改 `docs/00`–`28`、`docs/en/`、附录 Markdown、两份 `CONTENT_GUIDE.md`、罗盘文案、`revisions.json` 里已有句子、`cover.svg`、`assets/`、`tools/`、`CREDITS.md`。不把 CSS 拆出去。不实施刀 B、刀 D、刀 C。
- 不改 `toc_html` 的标签，不加图目录或表目录。出版书签仍是 44 条。章号显示仍是文件名前缀加 1。`.chapter-compass` 和 `.quick-check` 里继续没有 `h2`。
- 印刷保持 `orphans: 3`、`widows: 3`、标题和图的 `break-*`、`figure { background: transparent; }`、`@page { size: A4; margin: 16mm 15mm 18mm; }`、扉页 `page-break-before: auto`、正文 `font-size: 9.5pt; line-height: 1.55`。不把通用 `h2`–`h4` 的印刷字号改成 pt。
- 列表标记计算色保持 `rgb(7, 94, 132)`。`h2` 左边框保持 `3px`。屏幕上 `figure` 上边框保持 `1px` 且填充不是透明。`figure img` 的 `margin: 0 auto .55rem` 保持。
- 修订说明只用设计里的四句。不写刀 B、刀 D、刀 C，也不写 Batch4 的章节。已有修订句子一字不改。
- 不删 `0x271`、`167 ns`、出版书签长度为 44、样本章、batch2、batch3 的断言。`pageOverflow` 为 0 的 1200、840、390 三档不放宽。若 `1.0625rem` 让这三档出现横向滚动，保持这个字号，也保持 `.book` 的宽度，只改那条把内容撑出视口的规则。不把正文字号改回 `1rem`。
- `test_visual_polish_css_contract` 保持可过。刀 E 的断言写进新方法 `test_typography_e_css_contract`，不塞进那个方法。不新开浏览器用例。

上一句「Book CI 变绿后 squash 合入」指刀 E 的实施 PR。本计划文件的 PR 等人审阅，不在 CI 变绿后自动合入，也不在本 PR 里改 `stm32-book/`。

## 开工条件

实施开始时先读 `main` 上的 `stm32-book/manifest.json`，只看 `version` 和 `date`。不要在本计划的分支上改 CSS 或版本。

- `version` 还是 `1.2.2`：Batch4 还没合入。停。不开实施分支，除非用户这一轮明确说可以提前。
- `version` 是 `1.2.3`：实施版写成 `1.2.4`，日期写成 `2026-10-25`。Task 3 的字面量按这个走。
- `version` 已经高于 `1.2.3`（仍是 `1.2.x`，且补丁号大于 3）：实施版写成下一条修订号。不占用 `1.2.3`，也不把 `1.2.4` 硬套上去。日期仍是 `2026-10-25`。修订四句不变。Task 3 里每一处 `1.2.4` 换成这个新号，每一处当作「上一版」的 `1.2.3` 换成当时 manifest 的 `version`。已有修订句子保持 main 上的原文，只把索引后移一位。

`validate_revisions()` 在 `build_html.py` 第 818 行。它要求 `revisions.json` 第一条的 `version` 等于 manifest 的 `version`。Task 3 必须同一提交改测试、两份 manifest、`revisions.json` 和 README。

## File map

| 路径 | 实施时的责任 |
| --- | --- |
| `docs/superpowers/plans/2026-10-25-book-visual-typography-E.md` | 本计划。本 PR 只新增这一份 |
| `stm32-book/tests/test_build.py` | Task 1 新增 `test_typography_e_css_contract`，并给 `test_visual_polish_contrast_clears_4_5` 加上四对。Task 3 只改版本断言 |
| `stm32-book/build_html.py` | Task 2 只改 `CSS` 字符串。第 954 行之前和第 1220 行的结束引号之后不改 |
| `stm32-book/manifest.json` | Task 3：`version` 改为 `1.2.4`，`date` 保持 `2026-10-25` |
| `stm32-book/manifest-en.json` | 同上 |
| `stm32-book/revisions.json` | Task 3：`entries` 最前插入 1.2.4。已有条目一字不改 |
| `stm32-book/README.md` | Task 3：当前版本句、发布节的版本句、tag 名，以及「也不要把 1.2.3 的产物标成 1.2.4」 |

---

### Task 1: 先写下会失败的排版契约

**Files:**
- Modify: `stm32-book/tests/test_build.py`（在 `test_visual_polish_contrast_clears_4_5` 的元组里追加四对；在该方法之后、`test_visual_polish_version_is_1_2_0` 之前插入 `test_typography_e_css_contract`）
- Test: `stm32-book/tests/test_build.py`

**Interfaces:**
- Consumes: 已有的 `BookBuildContractTests._css_rule`、`_contrast_ratio`、`self.builder.CSS`。屏幕段是第一个 `@media` 之前，印刷段是 `@media print` 之后，与 `test_visual_polish_css_contract` 相同。
- Produces: `BookBuildContractTests.test_typography_e_css_contract`。后面的任务按这个名字跑。这一任务不改版本断言，不改 `build_html.py`。

这一提交之后，整套 `discover` 会失败。这是预期。不要开实施 PR，不要 squash。排版契约要到 Task 2 才绿。对比那一条现在就应该绿：这四对是十六进制，不读 CSS。

`_css_rule(screen, "h2")` 会先命中 `.contents > section > h2`，因为正则是 `h2\s*\{`。通用 `h2`、`h3`、`h4` 用整行 `assertIn`，不要用 `_css_rule(screen, "h2")`。`code` 的规则用行首 `^code {`，这样不会取到 `pre code`。

`:not(pre) > code` 保留 `border-radius`。规格里的「不含 border」指没有 `border` 这条声明。不要写 `assertNotIn("border", inline)`，那会把 `border-radius` 判失败。

- [ ] **Step 1: 追加四对对比，并写入排版契约**

在 `test_visual_polish_contrast_clears_4_5` 的 `pairs` 里，`("#444", "#fff"),` 后面加上：

```python
            ("#eef6f8", "#101820"),
            ("#edf6f9", "#0a141c"),
            ("#111", "#f6f6f6"),
            ("#075e84", "#e5f3f8"),
```

门槛仍是 `self.assertGreaterEqual(_contrast_ratio(foreground, background), 4.5)`。不要把 `#c4552a`、代码左边条或行内色块的混合底放进这张表。

在 `def test_visual_polish_version_is_1_2_0` 之前插入：

```python
    def test_typography_e_css_contract(self) -> None:
        css = self.builder.CSS
        screen = css.split("@media", 1)[0]
        dark = css.split("@media (prefers-color-scheme: dark)", 1)[1].split("@media", 1)[0]
        printed = css.split("@media print", 1)[1]
        narrow = css.split("@media (max-width: 720px)", 1)[1].split("@media", 1)[0]

        def custom_value(block: str, name: str) -> str:
            match = re.search(rf"{re.escape(name)}:\s*([^;]+);", block)
            self.assertIsNotNone(match, name)
            return match.group(1).strip()

        for token in (
            "--font-sans:",
            "--font-mono:",
            "--type-body: 1.0625rem",
            "--type-h1: clamp(1.85rem, 4.2vw, 2.7rem)",
            "--type-h2: 1.55rem",
            "--type-h3: 1.35rem",
            "--type-h4: 1.2rem",
            "--type-kicker: 0.78rem",
            "--type-small: 0.9375rem",
            "--type-code: 0.92em",
            "--leading-heading: 1.35",
            "--leading-caption: 1.55",
            "--leading-toc: 1.45",
            "--leading-code: 1.65",
        ):
            self.assertIn(token, screen, token)

        sans = custom_value(screen, "--font-sans")
        self.assertTrue(
            sans.startswith('"Noto Sans CJK SC", "Microsoft YaHei", "PingFang SC"'),
            sans,
        )
        for face in ('"Noto Sans SC"', '"Source Han Sans SC"', '"Segoe UI"'):
            self.assertIn(face, sans)
        mono = custom_value(screen, "--font-mono")
        self.assertTrue(
            mono.startswith('"Cascadia Mono", "SFMono-Regular", Consolas'),
            mono,
        )
        for face in (
            '"Noto Sans Mono CJK SC"',
            '"Source Han Mono SC"',
            '"Sarasa Mono SC"',
            '"Liberation Mono"',
            "ui-monospace",
        ):
            self.assertIn(face, mono)

        self.assertIn("font-family: var(--font-sans)", self._css_rule(screen, ":root"))
        self.assertNotIn("font-size", self._css_rule(screen, "html"))
        self.assertIn("font-size: var(--type-body)", self._css_rule(screen, "body"))
        self.assertIn("line-height: var(--leading-body)", self._css_rule(screen, "body"))
        self.assertNotIn("--font-sans", dark)
        self.assertNotIn("--type-body", dark)
        self.assertIn("--code: #0a141c", dark)
        self.assertIn("--code-ink: #edf6f9", dark)
        self.assertIn("--code: #101820", screen)
        self.assertIn("--code-ink: #eef6f8", screen)

        code_rule = re.search(r"(?m)^code\s*\{([^}]*)\}", screen)
        self.assertIsNotNone(code_rule)
        self.assertIn("font-family: var(--font-mono)", code_rule.group(1))
        self.assertIn("font-size: var(--type-code)", code_rule.group(1))
        pre_code = self._css_rule(screen, "pre code")
        self.assertNotIn("font-size", pre_code)
        self.assertIn("color: inherit", pre_code)
        self.assertIn("background: transparent", pre_code)
        self.assertIn("padding: 0", pre_code)
        self.assertIn("white-space: inherit", pre_code)
        self.assertIn("user-select: text", pre_code)

        inline = self._css_rule(screen, ":not(pre) > code")
        self.assertIn("color-mix(in srgb, var(--accent) 18%, var(--paper))", inline)
        self.assertIn("padding: .12em .35em", inline)
        self.assertIn("border-radius: .3em", inline)
        names = [part.split(":", 1)[0].strip() for part in inline.split(";") if part.strip()]
        self.assertNotIn("border", names)
        self.assertIn("border-radius", names)
        self.assertIn("background: var(--accent-soft)", self._css_rule(screen, ".source-id code"))

        pre = self._css_rule(screen, "pre")
        self.assertIn("line-height: var(--leading-code)", pre)
        self.assertIn("margin: var(--space-paragraph) 0 var(--space-figure)", pre)
        self.assertIn("border-left: 3px solid var(--accent)", pre)
        self.assertIn("border-radius: var(--radius)", pre)
        self.assertIn("tab-size: 4", pre)
        self.assertIn("user-select: text", pre)
        self.assertNotIn("box-shadow", pre)

        for selector in ("figcaption", "sub"):
            block = self._css_rule(screen, selector)
            self.assertIn("font-size: var(--type-small)", block, selector)
            self.assertIn("line-height: var(--leading-caption)", block, selector)
        self.assertIn("margin: 0 auto .55rem", self._css_rule(screen, "figure img"))
        self.assertIn("font-size: var(--type-small)", self._css_rule(screen, "table"))
        self.assertIn("font-size: var(--type-small)", self._css_rule(screen, ".source-card dl"))

        self.assertIn("line-height: var(--leading-toc)", self._css_rule(screen, ".contents li"))
        self.assertIn("margin: .28rem 0", self._css_rule(screen, ".contents li"))
        self.assertIn("break-inside: avoid", self._css_rule(screen, ".contents li"))
        goal = self._css_rule(screen, ".contents > section > p:not(.toc-closing)")
        self.assertIn("color: var(--muted)", goal)
        self.assertIn("font-size: var(--type-small)", goal)
        self.assertIn("line-height: var(--leading-caption)", goal)
        self.assertIn("max-width: var(--measure)", goal)
        closing = self._css_rule(screen, ".toc-closing")
        self.assertIn("border-top: 1px solid var(--line)", closing)
        self.assertIn("margin: var(--space-bar) 0 0", closing)
        self.assertIn("font-weight: 700", closing)
        self.assertNotIn("font-size", closing)
        contents_h2 = self._css_rule(screen, ".contents > section > h2")
        self.assertIn("font-size: var(--type-h3)", contents_h2)
        self.assertIn("line-height: var(--leading-heading)", contents_h2)
        self.assertIn("position: sticky", contents_h2)
        self.assertIn("background: var(--paper)", contents_h2)
        self.assertIn("box-shadow: 0 1px 0 var(--line)", contents_h2)
        self.assertIn("columns: 2", self._css_rule(screen, ".contents ol"))
        self.assertIn("column-gap: 3rem", self._css_rule(screen, ".contents ol"))
        self.assertIn("columns: 1", self._css_rule(narrow, ".contents ol"))

        self.assertIn(
            "h2, h3, h4 { line-height: var(--leading-heading); scroll-margin-top: 1.25rem; }",
            screen,
        )
        self.assertIn(
            "h2 { font-size: var(--type-h2); margin: calc(var(--space-figure) + var(--space-paragraph)) 0 var(--space-bar); }",
            screen,
        )
        self.assertIn(
            "h3 { font-size: var(--type-h3); margin: var(--space-figure) 0 calc(var(--space-bar) / 2); }",
            screen,
        )
        self.assertIn(
            "h4 { font-size: var(--type-h4); margin: var(--space-paragraph) 0 calc(var(--space-bar) / 2); }",
            screen,
        )
        self.assertIn(
            ".chapter > h2, .appendix > h2, .part-closing > h2 { margin: calc(var(--space-figure) + var(--space-paragraph)) 0 var(--space-bar); padding-left: var(--space-bar); border-left: 3px solid var(--accent); }",
            screen,
        )
        self.assertIn(
            ".chapter > header h1, .appendix > header h1, .part-closing > header h1, .back-matter > header h1 { font-size: var(--type-h1); line-height: 1.22; margin: .28em 0 0; max-width: 18em; }",
            screen,
        )
        self.assertIn("font-size: var(--type-h4)", self._css_rule(screen, ".quick-title"))
        source_h2 = self._css_rule(screen, ".source-card h2")
        self.assertIn("font-size: var(--type-h4)", source_h2)
        self.assertIn("line-height: var(--leading-heading)", source_h2)
        self.assertIn("margin: 0 0 .3rem", source_h2)
        self.assertNotIn("padding-left", source_h2)
        self.assertIn("margin-top: 0", self._css_rule(screen, ".imprint h1, .companion h2"))

        for selector in (
            ".compass-role",
            ".callout-label",
            ".source-card dt",
            ".part-label",
            ".cover .eyebrow",
            ".closing-banner",
            ".chapter-number",
            ".compass-title",
            ".source-id",
            ".imprint .kicker",
            ".index-letter",
            ".revision-history .kicker, .subject-index .kicker",
        ):
            self.assertIn("font-size: var(--type-kicker)", self._css_rule(screen, selector), selector)
        self.assertIn("letter-spacing: .04em", self._css_rule(screen, ".source-id"))
        self.assertIn("letter-spacing: .04em", self._css_rule(screen, ".source-card dt"))

        self.assertIn("clamp(2.15rem, 5.6vw, 3.7rem)", self._css_rule(screen, ".cover h1"))
        self.assertIn("clamp(1.05rem, 2.4vw, 1.35rem)", self._css_rule(screen, ".cover .subtitle"))
        self.assertIn("clamp(2rem, 5vw, 3.35rem)", self._css_rule(screen, ".part-divider h1"))
        part_goal = self._css_rule(screen, ".part-goal")
        self.assertIn("font-size: 1.12rem", part_goal)
        self.assertIn("line-height: 1.6", part_goal)
        self.assertIn("clamp(4.5rem, 14vw, 8.5rem)", self._css_rule(screen, ".part-index"))
        self.assertIn("font-size: 3rem", self._css_rule(narrow, ".part-index"))
        jump = self._css_rule(screen, ".toc-jump")
        self.assertIn("font-size: .85rem", jump)
        self.assertIn("box-shadow: 0 .45rem 1.2rem rgba(16, 24, 32, .18)", jump)
        self.assertIn(".book { width: min(100% - 2rem, 980px); margin: 0 auto; }", screen)
        self.assertIn(".book { width: min(100% - 1rem, 980px); }", narrow)

        for retired in (
            "font-size: .72rem",
            "font-size: .74rem",
            "font-size: .75rem",
            "font-size: .78rem",
            "font-size: .82rem",
            "font-size: .88rem",
            "font-size: .9rem",
            "font-size: .91em",
            "font-size: .92em",
            "font-size: .94rem",
            "font-size: 1.02rem",
            "font-size: 1.05rem",
            "font-size: 1.16rem",
            "font-size: 1.42rem",
            "margin: 2.35rem 0 .6rem",
            "line-height: 1.35;",
            "line-height: 1.45;",
        ):
            self.assertNotIn(retired, screen, retired)

        self.assertNotIn("@font-face", css)
        self.assertNotIn("url(", css)

        print_root = self._css_rule(printed, ":root")
        self.assertIn("--code: #f6f6f6", print_root)
        self.assertIn("--code-ink: #111", print_root)
        self.assertNotIn("--font-sans", printed)
        self.assertNotIn("--type-body", printed)
        self.assertIn("font-size: 9.5pt; line-height: 1.55", printed)
        pre_print = self._css_rule(printed, "pre")
        self.assertIn("line-height: 1.45", pre_print)
        self.assertIn("white-space: pre-wrap", pre_print)
        self.assertIn("overflow-wrap: anywhere", pre_print)
        self.assertIn("break-inside: auto", pre_print)
        self.assertIn("page-break-inside: auto", pre_print)
        self.assertNotIn("avoid", pre_print)
        caption = self._css_rule(printed, "figcaption")
        self.assertIn("font-size: 9pt", caption)
        self.assertIn("line-height: 1.4", caption)
        self.assertIn("break-before: avoid-page", caption)
        self.assertIn("page-break-before: avoid", caption)
        self.assertIn("break-inside: avoid-page", caption)
        self.assertIn("page-break-inside: avoid", caption)
        printed_sub = self._css_rule(printed, "sub")
        self.assertIn("font-size: 9pt", printed_sub)
        self.assertIn("line-height: 1.4", printed_sub)
        self.assertIn("position: static", self._css_rule(printed, ".contents > section > h2"))
        self.assertIn("figure { background: transparent; }", printed)
        self.assertIn("@page { size: A4; margin: 16mm 15mm 18mm; }", printed)
```

规格的核对清单点了 token、字体栈、`body`、`code`、行内色块、`pre`、图注、目录、四条眉题、封面 clamp、`.toc-jump`、`@font-face`、`url(` 和印刷三处。上面多出来的断言锁的是同一份规格里的字号表：通用 `h2`–`h4`、其余眉题、`table`、`.source-card dl`、印刷 `sub`，以及必须留下的封面和分部页字面量。不要把这些断言挪进 `test_visual_polish_css_contract`。

- [ ] **Step 2: 跑契约，确认失败；跑对比，确认通过**

Run:

```bash
python3 stm32-book/tests/test_build.py BookBuildContractTests.test_typography_e_css_contract -v
```

Expected: 退出码 1。失败信息含 `--font-sans`。

Run:

```bash
python3 stm32-book/tests/test_build.py BookBuildContractTests.test_visual_polish_contrast_clears_4_5 -v
```

Expected: 退出码 0，末尾 `OK`。

- [ ] **Step 3: 提交失败的契约**

```bash
git add stm32-book/tests/test_build.py
git commit -m "test: 排版微抛 E 的 CSS 契约先写成会失败的断言"
```

不要在这一步改 `build_html.py`。不要开实施 PR。

---

### Task 2: 改内联 CSS

**Files:**
- Modify: `stm32-book/build_html.py` 的 `CSS` 字符串（`ee05fa3` 上第 954–1220 行）
- Test: `BookBuildContractTests.test_typography_e_css_contract`、`BookBuildContractTests.test_visual_polish_css_contract`

**Interfaces:**
- Consumes: Task 1 的 `test_typography_e_css_contract`。
- Produces: 亮色 `:root` 里的 `--font-sans`、`--font-mono`、`--type-*`、`--leading-heading`、`--leading-caption`、`--leading-toc`、`--leading-code`，以及下面每一处选择器的新声明。`toc_html` 的返回标签不变。

只改下面列出的声明。选择器的子组合保持原样。`.source-card h2` 不套章内 `h2` 的左边条。暗色 `@media (prefers-color-scheme: dark)` 那一行不重抄新 token。不要给 `.companion h2` 再写 `margin-bottom`：`.imprint h1, .companion h2 { margin-top: 0; }` 保持，下边距跟着通用 `h2` 变成 `var(--space-bar)`。

- [ ] **Step 1: 确认契约仍然失败**

Run:

```bash
python3 stm32-book/tests/test_build.py BookBuildContractTests.test_typography_e_css_contract -v
```

Expected: 退出码 1，失败信息含 `--font-sans`。

- [ ] **Step 2: 按选择器替换 CSS**

把亮色 `:root` 里的：

```css
  --elev: 0 1px 2px color-mix(in srgb, var(--ink) 8%, transparent);
  font-family: "Noto Sans CJK SC", "Microsoft YaHei", "PingFang SC", system-ui, sans-serif;
```

换成：

```css
  --elev: 0 1px 2px color-mix(in srgb, var(--ink) 8%, transparent);
  --font-sans: "Noto Sans CJK SC", "Microsoft YaHei", "PingFang SC", "Noto Sans SC", "Source Han Sans SC", "Segoe UI", system-ui, sans-serif;
  --font-mono: "Cascadia Mono", "SFMono-Regular", Consolas, "Noto Sans Mono CJK SC", "Source Han Mono SC", "Sarasa Mono SC", "Liberation Mono", ui-monospace, monospace;
  --type-body: 1.0625rem;
  --type-h1: clamp(1.85rem, 4.2vw, 2.7rem);
  --type-h2: 1.55rem;
  --type-h3: 1.35rem;
  --type-h4: 1.2rem;
  --type-kicker: 0.78rem;
  --type-small: 0.9375rem;
  --type-code: 0.92em;
  --leading-heading: 1.35;
  --leading-caption: 1.55;
  --leading-toc: 1.45;
  --leading-code: 1.65;
  font-family: var(--font-sans);
```

把：

```css
body { margin: 0; background: var(--paper); color: var(--ink); line-height: var(--leading-body); }
```

换成：

```css
body { margin: 0; background: var(--paper); color: var(--ink); font-size: var(--type-body); line-height: var(--leading-body); }
```

把：

```css
.cover .eyebrow { margin: 0; font-weight: 700; letter-spacing: var(--tracking-kicker); font-size: .78rem; color: var(--warn); }
```

换成：

```css
.cover .eyebrow { margin: 0; font-weight: 700; letter-spacing: var(--tracking-kicker); font-size: var(--type-kicker); color: var(--warn); }
```

`.cover h1` 和 `.cover .subtitle` 两行不改。

把：

```css
.imprint .kicker { margin: 0 0 .35rem; color: var(--accent); font-weight: 700; letter-spacing: var(--tracking-kicker); font-size: .82rem; }
```

换成：

```css
.imprint .kicker { margin: 0 0 .35rem; color: var(--accent); font-weight: 700; letter-spacing: var(--tracking-kicker); font-size: var(--type-kicker); }
```

把：

```css
.toc-closing { margin: .2rem 0 0; font-weight: 700; }
```

换成：

```css
.toc-closing { margin: var(--space-bar) 0 0; padding-top: calc(var(--space-bar) / 2); border-top: 1px solid var(--line); font-weight: 700; }
```

把：

```css
.revision-history .kicker, .subject-index .kicker { margin: 0 0 .35rem; color: var(--accent); font-weight: 700; letter-spacing: var(--tracking-kicker); font-size: .82rem; }
```

换成：

```css
.revision-history .kicker, .subject-index .kicker { margin: 0 0 .35rem; color: var(--accent); font-weight: 700; letter-spacing: var(--tracking-kicker); font-size: var(--type-kicker); }
```

把：

```css
.index-letter { margin: 0 0 .15rem; color: var(--accent); font-weight: 800; letter-spacing: var(--tracking-kicker); font-size: .82rem; break-after: avoid; }
```

换成：

```css
.index-letter { margin: 0 0 .15rem; color: var(--accent); font-weight: 800; letter-spacing: var(--tracking-kicker); font-size: var(--type-kicker); break-after: avoid; }
```

把：

```css
.contents li { break-inside: avoid; margin: .28rem 0; }
.contents > section > h2 { position: sticky; top: 0; z-index: 2; margin: 0; padding: .85rem 0 .45rem; background: var(--paper); box-shadow: 0 1px 0 var(--line); }
```

换成：

```css
.contents li { break-inside: avoid; margin: .28rem 0; line-height: var(--leading-toc); }
.contents > section > h2 { position: sticky; top: 0; z-index: 2; margin: 0; padding: .85rem 0 .45rem; background: var(--paper); box-shadow: 0 1px 0 var(--line); font-size: var(--type-h3); line-height: var(--leading-heading); }
.contents > section > p:not(.toc-closing) { max-width: var(--measure); margin: calc(var(--space-bar) / 2) 0 var(--space-bar); color: var(--muted); font-size: var(--type-small); line-height: var(--leading-caption); }
```

`.contents ol { columns: 2; column-gap: 3rem; }` 不改。720px 里的 `.contents ol { columns: 1; }` 不改。

把：

```css
.part-divider .part-label { position: relative; z-index: 1; margin: 0; color: var(--accent); font-weight: 800; letter-spacing: var(--tracking-kicker); font-size: .82rem; }
```

换成：

```css
.part-divider .part-label { position: relative; z-index: 1; margin: 0; color: var(--accent); font-weight: 800; letter-spacing: var(--tracking-kicker); font-size: var(--type-kicker); }
```

`.part-divider h1`、`.part-goal`、`.part-index` 三行不改。窄屏 `.part-index { font-size: 3rem; top: .55rem; }` 不改。

把：

```css
.closing-banner { margin: .8rem 0 0; color: var(--warn); font-weight: 800; letter-spacing: var(--tracking-kicker); font-size: .78rem; }
```

换成：

```css
.closing-banner { margin: .8rem 0 0; color: var(--warn); font-weight: 800; letter-spacing: var(--tracking-kicker); font-size: var(--type-kicker); }
```

把：

```css
.chapter > header h1, .appendix > header h1, .part-closing > header h1, .back-matter > header h1 { font-size: clamp(1.85rem, 4.2vw, 2.7rem); line-height: 1.22; margin: .28em 0 0; max-width: 18em; }
.chapter-number { display: block; color: var(--accent); font-weight: 800; letter-spacing: var(--tracking-kicker); font-size: .78rem; }
h2, h3, h4 { line-height: 1.35; scroll-margin-top: 1.25rem; }
h2 { font-size: 1.42rem; margin: 2.35rem 0 .6rem; }
.chapter > h2, .appendix > h2, .part-closing > h2 { margin: calc(var(--space-figure) + var(--space-paragraph)) 0 var(--space-bar); padding-left: var(--space-bar); border-left: 3px solid var(--accent); }
h3 { font-size: 1.16rem; margin: 1.7rem 0 .4rem; }
h4 { font-size: 1.02rem; margin: 1.3rem 0 .3rem; }
```

换成：

```css
.chapter > header h1, .appendix > header h1, .part-closing > header h1, .back-matter > header h1 { font-size: var(--type-h1); line-height: 1.22; margin: .28em 0 0; max-width: 18em; }
.chapter-number { display: block; color: var(--accent); font-weight: 800; letter-spacing: var(--tracking-kicker); font-size: var(--type-kicker); }
h2, h3, h4 { line-height: var(--leading-heading); scroll-margin-top: 1.25rem; }
h2 { font-size: var(--type-h2); margin: calc(var(--space-figure) + var(--space-paragraph)) 0 var(--space-bar); }
.chapter > h2, .appendix > h2, .part-closing > h2 { margin: calc(var(--space-figure) + var(--space-paragraph)) 0 var(--space-bar); padding-left: var(--space-bar); border-left: 3px solid var(--accent); }
h3 { font-size: var(--type-h3); margin: var(--space-figure) 0 calc(var(--space-bar) / 2); }
h4 { font-size: var(--type-h4); margin: var(--space-paragraph) 0 calc(var(--space-bar) / 2); }
```

章、附录、分部收束的 `h2` 那一行保持原文，含 `border-left: 3px solid var(--accent)`。

把：

```css
.compass-title { color: var(--accent); font-size: .78rem; font-weight: 800; letter-spacing: var(--tracking-kicker); }
```

换成：

```css
.compass-title { color: var(--accent); font-size: var(--type-kicker); font-weight: 800; letter-spacing: var(--tracking-kicker); }
```

把：

```css
.compass-role { margin: 0; font-size: .72rem; font-weight: 800; letter-spacing: var(--tracking-kicker); color: var(--muted); }
```

换成：

```css
.compass-role { margin: 0; font-size: var(--type-kicker); font-weight: 800; letter-spacing: var(--tracking-kicker); color: var(--muted); }
```

`.compass-question .compass-role`、`.compass-deliverable .compass-role`、`.compass-boundary .compass-role` 只改颜色的那几行不改。

把：

```css
.quick-title { margin: 0 0 .35rem; color: var(--accent); font-weight: 800; font-size: 1.05rem; }
```

换成：

```css
.quick-title { margin: 0 0 .35rem; color: var(--accent); font-weight: 800; font-size: var(--type-h4); }
```

把：

```css
.callout-label { margin: 0; font-size: .74rem; font-weight: 800; letter-spacing: var(--tracking-kicker); color: var(--accent); }
```

换成：

```css
.callout-label { margin: 0; font-size: var(--type-kicker); font-weight: 800; letter-spacing: var(--tracking-kicker); color: var(--accent); }
```

`.callout-warning .callout-label` 和 `.callout-tip .callout-label` 不改。

`figure img { margin: 0 auto .55rem; }` 不改。

把：

```css
figcaption { max-width: var(--measure); margin: .15rem auto 0; color: var(--muted); text-align: center; font-size: .9rem; line-height: 1.45; }
sub { display: block; color: var(--muted); text-align: center; font-size: .88rem; }
table { width: 100%; border-collapse: collapse; font-size: .94rem; }
```

换成：

```css
figcaption { max-width: var(--measure); margin: .15rem auto 0; color: var(--muted); text-align: center; font-size: var(--type-small); line-height: var(--leading-caption); }
sub { display: block; color: var(--muted); text-align: center; font-size: var(--type-small); line-height: var(--leading-caption); }
table { width: 100%; border-collapse: collapse; font-size: var(--type-small); }
```

把：

```css
code { font-family: "Cascadia Mono", "SFMono-Regular", Consolas, monospace; font-size: .91em; }
:not(pre) > code { padding: .12em .35em; border-radius: .3em; background: var(--panel); }
```

换成：

```css
code { font-family: var(--font-mono); font-size: var(--type-code); }
:not(pre) > code { padding: .12em .35em; border-radius: .3em; background: color-mix(in srgb, var(--accent) 18%, var(--paper)); }
```

行内 `code` 不加 `border`。`--line` 对纸色约 1.3，1px 线分不出块。

`pre` 规则里只改两处，四层 `background-image`、`tab-size: 4`、`user-select: text`、`border-left: 3px solid var(--accent)`、`border-radius: var(--radius)` 保持。继续不写 `box-shadow`。

把：

```css
  margin: 1.15rem 0 1.5rem;
```

换成：

```css
  margin: var(--space-paragraph) 0 var(--space-figure);
```

`pre` 规则里单独成行、行首两个空格的 `line-height: 1.6;` 换成下面这一行。`.part-goal` 同一行里的 `line-height: 1.6` 是分部页正文，保持不动。不要做不带缩进的全局替换。

把：

```css
  line-height: 1.6;
```

换成：

```css
  line-height: var(--leading-code);
```

把：

```css
pre code { font-size: .92em; color: inherit; background: transparent; padding: 0; white-space: inherit; user-select: text; }
```

换成：

```css
pre code { color: inherit; background: transparent; padding: 0; white-space: inherit; user-select: text; }
```

把：

```css
.source-id { margin: 0; color: var(--accent); font-weight: 800; letter-spacing: .04em; font-size: .78rem; }
```

换成：

```css
.source-id { margin: 0; color: var(--accent); font-weight: 800; letter-spacing: .04em; font-size: var(--type-kicker); }
```

`.source-id code { color: var(--accent); background: var(--accent-soft); }` 不改。它写在 `:not(pre) > code` 之后，类选择器盖过行内色块。

把：

```css
.source-card h2 { min-width: 0; font-size: 1.12rem; line-height: 1.35; margin: 0 0 .3rem; }
.source-card dl { min-width: 0; grid-template-columns: minmax(5.5rem, max-content) minmax(0, 1fr); gap: .28rem .75rem; font-size: .9rem; }
.source-card dt { color: var(--muted); font-weight: 700; font-size: .75rem; letter-spacing: .04em; }
```

换成：

```css
.source-card h2 { min-width: 0; font-size: var(--type-h4); line-height: var(--leading-heading); margin: 0 0 .3rem; }
.source-card dl { min-width: 0; grid-template-columns: minmax(5.5rem, max-content) minmax(0, 1fr); gap: .28rem .75rem; font-size: var(--type-small); }
.source-card dt { color: var(--muted); font-weight: 700; font-size: var(--type-kicker); letter-spacing: .04em; }
```

`.toc-jump` 那一行不改，含 `font-size: .85rem` 和 `box-shadow: 0 .45rem 1.2rem rgba(16, 24, 32, .18)`。

印刷 `:root` 把：

```css
  :root { color-scheme: light; --paper: #fff; --ink: #111; --muted: #444; --line: #bbb; --panel: #f4f4f4; --accent: #075e84; --accent-soft: #edf6f9; --warn: #8a3418; --warn-soft: #f8f1ec; --tip: #1b5c45; --tip-soft: #eef6f2; --spine: #c4552a; --spine-soft: #f8efe8; }
```

换成：

```css
  :root { color-scheme: light; --paper: #fff; --ink: #111; --muted: #444; --line: #bbb; --panel: #f4f4f4; --accent: #075e84; --accent-soft: #edf6f9; --warn: #8a3418; --warn-soft: #f8f1ec; --tip: #1b5c45; --tip-soft: #eef6f2; --spine: #c4552a; --spine-soft: #f8efe8; --code: #f6f6f6; --code-ink: #111; }
```

印刷 `body` 的 `font-size: 9.5pt; line-height: 1.55; orphans: 3; widows: 3; ...` 不改。

把：

```css
  pre { white-space: pre-wrap; overflow-wrap: anywhere; break-inside: auto; page-break-inside: auto; }
```

换成：

```css
  pre { white-space: pre-wrap; overflow-wrap: anywhere; break-inside: auto; page-break-inside: auto; line-height: 1.45; }
```

这条规则的文本里仍然不出现 `avoid`。

把：

```css
  figcaption { break-before: avoid-page; page-break-before: avoid; break-inside: avoid-page; page-break-inside: avoid; }
```

换成：

```css
  figcaption { break-before: avoid-page; page-break-before: avoid; break-inside: avoid-page; page-break-inside: avoid; font-size: 9pt; line-height: 1.4; }
  sub { font-size: 9pt; line-height: 1.4; }
```

印刷 `figcaption` 的选择器仍是单独的 `figcaption`，不改成和 `sub` 的逗号组合。`sub` 是下一条规则。印刷 `.contents > section > h2 { position: static; }` 不改。`figure { background: transparent; }` 不改。`@page` 的毫米值不改。

屏幕深色代码块的 `--code: #101820` 和 `--code-ink: #eef6f8` 留在亮色 `:root`。暗色那一行的 `--code: #0a141c` 和 `--code-ink: #edf6f9` 不改。

- [ ] **Step 3: 跑排版契约和 1.2.0 契约**

Run:

```bash
python3 stm32-book/tests/test_build.py BookBuildContractTests.test_typography_e_css_contract BookBuildContractTests.test_visual_polish_css_contract -v
```

Expected: 退出码 0，末尾 `OK`。

若 `test_visual_polish_css_contract` 失败，改回 Step 2 里写明保持的那一行，不要改那个测试方法来迁就新字号。

- [ ] **Step 4: 跑窄屏三档，横向滚动仍是 0**

Run:

```bash
python3 stm32-book/tests/test_build.py BookBuildContractTests.test_narrow_desktop_stacks_compass_without_part_number_collision -v
```

Expected: 退出码 0。`pageOverflow` 在 1200、840、390 三档都是 0。`sectionRule` 仍是 `3px`，`figureBorder` 仍是 `1px`，`markerColor` 仍是 `rgb(7, 94, 132)`。

若失败信息是 `pageOverflow` 不是 0：保持 `--type-body: 1.0625rem`，保持两条 `.book` 的 `width`。不要把正文字号改回 `1rem`。用下面的一次性脚本找出撑出视口的元素，只改那一条规则，然后重跑这条测试直到三档都是 0。这个脚本不进提交。

```bash
python3 - <<'PY'
import importlib.util
import tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright

root = Path("stm32-book")
spec = importlib.util.spec_from_file_location("builder", root / "build_html.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
with tempfile.TemporaryDirectory() as tmp:
    output = module.build_html(Path(tmp))
    candidates = module._browser_candidates(None)
    launch = {"headless": True}
    if candidates:
        launch["executable_path"] = str(candidates[0])
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(**launch)
        page = browser.new_page(viewport={"width": 390, "height": 844})
        page.goto(output.resolve().as_uri(), wait_until="load")
        print(page.evaluate("""() => {
          const view = document.documentElement.clientWidth;
          const rows = [];
          for (const el of document.body.querySelectorAll('*')) {
            const box = el.getBoundingClientRect();
            if (box.width > view + 1) {
              rows.push([Math.round(box.width), el.tagName, el.className, el.id]);
            }
          }
          rows.sort((a, b) => b[0] - a[0]);
          return rows.slice(0, 8);
        }"""))
        browser.close()
PY
```

只改打印出来的那条把内容撑出视口的规则。改完后 `test_typography_e_css_contract` 仍要过。

- [ ] **Step 5: 提交 CSS**

```bash
git add stm32-book/build_html.py
git commit -m "book: 内联 CSS 收进字号阶梯、目录、代码和图注"
```

若 Step 4 改到了测试文件里的临时打印，先删掉再提交。这一步的 diff 只能落在 `CSS` 字符串里。

---

### Task 3: 把整书标成 1.2.4

**Files:**
- Modify: `stm32-book/tests/test_build.py` 里仍写着上一版的当前版本断言
- Modify: `stm32-book/manifest.json` 的 `version`
- Modify: `stm32-book/manifest-en.json` 的 `version`
- Modify: `stm32-book/revisions.json` 的 `entries[0]`
- Modify: `stm32-book/README.md` 的当前版本句、发布节版本句、误标句、tag 名
- Test: `BookBuildContractTests.test_visual_polish_version_is_1_2_0`、`test_revision_file_lists_1_0_0_through_manifest_version`

**Interfaces:**
- Consumes: 开工条件定下的版本号。预期路径是上一版 `1.2.3`、新版 `1.2.4`、日期 `2026-10-25`。Batch4 若已把 1.2.3 放在 `entries[0]`，下面的索引再后移一位。已有句子的原文不改。
- Produces: 两份 manifest 的 `version` 都是 `1.2.4`，`date` 都是 `2026-10-25`。`revisions.json` 的 `entries[0].version` 是 `1.2.4`。`entries[1]` 仍是 Batch4 的 1.2.3 句子，`entries[2]` 仍是现在的 1.2.2 句子，`entries[3]` 仍是 1.2.1，`entries[4]` 仍是 1.2.0。

下面的「现在」指 Batch4 已经把版本写成 1.2.3 之后的 `main`，不是写本计划时的 `ee05fa3`。`ee05fa3` 上这些断言仍是 1.2.2。若实施时打开的文件还写着 `1.2.2`，回到开工条件，不要把 1.2.2 直接改成 1.2.4。

若 main 上 1.2.3 的 `zh` / `en` 与下面 `batch4` 两句不同，以 main 上已经提交的句子为准，只把索引后移，不要改写成下面的文本。

方法名保持 `test_visual_polish_version_is_1_2_0`。不要改名。

- [ ] **Step 1: 把版本断言改到 1.2.4，先不要改版本文件**

`assert_version_history_and_index` 里把 Batch4 已经写成的：

```python
        versions = ("1.2.3", "1.2.2", "1.2.1", "1.2.0", "1.1.1", "1.1.0", "1.0.8", "1.0.7", "1.0.6", "1.0.5", "1.0.4", "1.0.3", "1.0.2", "1.0.1", "1.0.0")
        for version in versions:
            self.assertIn(f">{version}<", history)
        self.assertLess(history.index(">1.2.3<"), history.index(">1.2.2<"))
```

换成：

```python
        versions = ("1.2.4", "1.2.3", "1.2.2", "1.2.1", "1.2.0", "1.1.1", "1.1.0", "1.0.8", "1.0.7", "1.0.6", "1.0.5", "1.0.4", "1.0.3", "1.0.2", "1.0.1", "1.0.0")
        for version in versions:
            self.assertIn(f">{version}<", history)
        self.assertLess(history.index(">1.2.4<"), history.index(">1.2.3<"))
        self.assertLess(history.index(">1.2.3<"), history.index(">1.2.2<"))
```

`>1.2.2<` 早于 `>1.2.1<` 的那一行，以及更早的比较，保持不动。

`test_revision_file_lists_1_0_0_through_manifest_version` 里的列表改成：

```python
            ["1.2.4", "1.2.3", "1.2.2", "1.2.1", "1.2.0", "1.1.1", "1.1.0", "1.0.8", "1.0.7", "1.0.6", "1.0.5", "1.0.4", "1.0.3", "1.0.2", "1.0.1", "1.0.0"],
```

把 `self.assertEqual("1.2.3", manifest["version"])` 改成 `self.assertEqual("1.2.4", manifest["version"])`。

两处 `self.assertIn("<strong>v1.2.3</strong>", html)` 都改成 `self.assertIn("<strong>v1.2.4</strong>", html)`。一处在 `test_build_produces_one_complete_offline_book`，一处在 `test_english_book_is_a_separate_offline_edition`。

`test_visual_polish_version_is_1_2_0` 的取条目改成：

```python
        entry = revisions["entries"][0]
        batch4 = revisions["entries"][1]
        batch3 = revisions["entries"][2]
        guide = revisions["entries"][3]
        previous = revisions["entries"][4]
```

`self.manifest["version"]`、英文 manifest 的 `version` 和 `entry["version"]` 改成 `"1.2.4"`。三处 `date` 仍是 `"2026-10-25"`。

`entry` 的中英改成这四句，一字不差：

```python
        self.assertEqual(
            [
                "正文、标题和眉题改用一组字号；目录里的分部目标改成次要色，分部收束行加上分隔线。",
                "代码块补上能显示中文的等宽字体，行距略增；图注行距加大。印刷时代码块改为浅底，图注改为 9pt，不再大于正文。",
            ],
            entry["zh"],
        )
        self.assertEqual(
            [
                "Body, headings, and kickers use one type scale. Part goals in the contents are muted, and each part-closing line has a divider.",
                "Code blocks gain a monospace stack that can show Chinese, with a slightly looser line-height. Captions gain line-height. In print, code blocks are light and captions are 9pt, no longer larger than the body.",
            ],
            entry["en"],
        )
```

现在核对 `entries[0]` 的 1.2.3 两句改去核对 `batch4`。Batch4 计划写的原文是：

```python
        self.assertEqual("1.2.3", batch4["version"])
        self.assertEqual("2026-10-25", batch4["date"])
        self.assertEqual(
            [
                "第 01 章写上 SWD 在第 34 脚 PA13 和第 37 脚 PA14，读保护解除写 0xA5，BOOT0=1 且 BOOT1=0 进的是系统存储器。第 07 章写上 0x3C 在 HAL 里是 0x78，表 42 的 400 kHz 行是 0x801E 和 4.7 kΩ。",
                "第 10 章写上只有 DMA1，8 个半字且 CNDTR 为 3 时已写 5 个采样、10 字节。第 11 章写上预分频 64、Reload 624 在 40 kHz 典型值下是 1 秒，LSI 是 30–60 kHz，备份寄存器是 10 个。",
            ],
            batch4["zh"],
        )
        self.assertEqual(
            [
                "Chapter file 01 records SWD on pin 34 PA13 and pin 37 PA14, readout protection level 0 as 0xA5, and BOOT0=1 with BOOT1=0 entering system memory. Chapter file 07 records that 0x3C is 0x78 in HAL, and that Table 42's 400 kHz row is 0x801E with 4.7 kΩ.",
                "Chapter file 10 records DMA1 only, and that eight half-words with CNDTR 3 means 5 samples and 10 bytes written. Chapter file 11 records prescaler 64 and Reload 624 as 1 second at a typical 40 kHz, LSI as 30–60 kHz, and ten backup registers.",
            ],
            batch4["en"],
        )
```

`30–60` 是 en dash。若 main 上的 1.2.3 句子和这四句不同，测试里写 main 的句子，不要改 `revisions.json` 去凑这四句。

现在核对 `entries[1]` 的 1.2.2 两句改去核对 `batch3`，原文不动：

```python
        self.assertEqual("1.2.2", batch3["version"])
        self.assertEqual(
            [
                "第 02 章把 CFGR 改回第 7.3.2 节，并写上 72 MHz 要 2 个等待、CSS 回到 HSI。第 05 章写上 1 kHz 和 500 Hz 两条路径。",
                "第 08 章写上 Mode 0、9 MHz，以及 0x9F 之后的 0xEF、0x40、0x17。第 09 章写上 12 MHz 下的 21 µs、除以 4096，以及 C8 有 ADC1/ADC2、没有 DAC。",
            ],
            batch3["zh"],
        )
        self.assertEqual(
            [
                "Chapter file 02 moves CFGR back to section 7.3.2, with two Flash wait states at 72 MHz and CSS falling back to HSI. Chapter file 05 records both the 1 kHz path and the 500 Hz path.",
                "Chapter file 08 records Mode 0 at 9 MHz and, after 0x9F, the bytes 0xEF, 0x40, and 0x17. Chapter file 09 records 21 µs at 12 MHz, division by 4096, and that the C8 has ADC1 and ADC2 and no DAC.",
            ],
            batch3["en"],
        )
```

现在对 `guide` 的 1.2.1 两句保持原文，对象从 Batch4 之后的 `entries[2]` 换成 `entries[3]`。现在对 `previous` 的 1.2.0 两句保持原文，对象从 `entries[3]` 换成 `entries[4]`。1.2.1 的两句是：

```python
        self.assertEqual("1.2.1", guide["version"])
        self.assertEqual(
            [
                "贡献指南把大典四块写成每章必选，放在视频块之后、学习目标之前。",
                "旧的常见坑与排查迁入坑与出处卡，并用 `#source-` 链到附录 E。这一版不改正文章。",
            ],
            guide["zh"],
        )
        self.assertEqual(
            [
                "The contributor guide requires the four compendium sections after the video block and before the learning goals.",
                "The old pitfalls section moves into Pitfalls and source cards, with `#source-` links to Appendix E. This edition does not rewrite chapter prose.",
            ],
            guide["en"],
        )
```

1.2.0 的两句是：

```python
        self.assertEqual("1.2.0", previous["version"])
        self.assertEqual(
            [
                "整书样式收到同一组纸色、墨色和强调色，章距、段距、图距使用固定阶梯。",
                "章首罗盘、提示框、出处卡和插图共用一档圆角和轻阴影；印刷时的孤行、寡行和图注不断页仍按原规则。",
            ],
            previous["zh"],
        )
        self.assertEqual(
            [
                "The book stylesheet uses one paper, ink, and accent set, with a fixed step for chapter, paragraph, and figure spacing.",
                "Chapter compasses, callouts, source cards, and figures share one radius and a light shadow; print orphans, widows, and caption keep-together rules stay as they were.",
            ],
            previous["en"],
        )
```

README 断言改成：

```python
        self.assertIn("当前版本：**v1.2.4 · 2026-10-25**", readme)
        self.assertIn("版本号已经是 1.2.4。", readme)
        self.assertIn("也不要把 1.1.1 的产物标成 1.2.0，", readme)
        self.assertIn("也不要把 1.2.0 的产物标成 1.2.1，", readme)
        self.assertIn("也不要把 1.2.1 的产物标成 1.2.2，", readme)
        self.assertIn("也不要把 1.2.2 的产物标成 1.2.3，", readme)
        self.assertIn("也不要把 1.2.3 的产物标成 1.2.4。", readme)
        self.assertIn("打 tag `v1.2.4`", readme)
        self.assertNotIn("当前版本：**v1.2.3", readme)
        self.assertNotIn("打 tag `v1.2.3`", readme)
```

不删 `0x271`、`167 ns`、`self.assertEqual(44, len(outline))`。不改样本章、batch2、batch3 的测试。

- [ ] **Step 2: 跑版本测试，确认失败**

Run:

```bash
python3 stm32-book/tests/test_build.py BookBuildContractTests.test_visual_polish_version_is_1_2_0 -v
```

Expected: 退出码 1。失败信息含 `'1.2.4' != '1.2.3'`。

- [ ] **Step 3: 写 1.2.4**

两份 manifest 只改这一行：

```json
  "version": "1.2.4",
```

`date` 保持 `"2026-10-25"`。不改 `sources`、罗盘或其他字段。

在 `stm32-book/revisions.json` 的 `entries` 数组最前面插入。1.2.3 那条原样留在后面：

```json
    {
      "version": "1.2.4",
      "date": "2026-10-25",
      "zh": [
        "正文、标题和眉题改用一组字号；目录里的分部目标改成次要色，分部收束行加上分隔线。",
        "代码块补上能显示中文的等宽字体，行距略增；图注行距加大。印刷时代码块改为浅底，图注改为 9pt，不再大于正文。"
      ],
      "en": [
        "Body, headings, and kickers use one type scale. Part goals in the contents are muted, and each part-closing line has a divider.",
        "Code blocks gain a monospace stack that can show Chinese, with a slightly looser line-height. Captions gain line-height. In print, code blocks are light and captions are 9pt, no longer larger than the body."
      ]
    },
```

不在修订说明里写刀 B、刀 D、刀 C，也不写 Batch4 的章节。

`stm32-book/README.md` 的当前版本句改为：

```markdown
当前版本：**v1.2.4 · 2026-10-25**。中文整书和英文整书共用这一版号。GitHub Release 仍要等这次提交进入 `main` 且 Book CI 产出四份文件之后，由有权限的人另行处理。
```

发布节里，把「版本号已经是 1.2.3。」改成「版本号已经是 1.2.4。」。在现有误标句子的最后，Batch4 已经写下的「也不要把 1.2.2 的产物标成 1.2.3。」后面再加「也不要把 1.2.3 的产物标成 1.2.4。」。已有的误标句子保留。若 main 上的误标句比下面这一整句多出 Batch4 实施时另加的分句，保留那些分句，只改版本号和 tag，并在句末追加「也不要把 1.2.3 的产物标成 1.2.4。」。预期整句是：

```markdown
版本号已经是 1.2.4。构建脚本不会自己创建 GitHub Release。不要把 rc.8（`0c24f76`）的产物标成 1.0.0，也不要把 1.0.7 的产物标成 1.0.8，也不要把 1.0.8 的产物标成 1.1.0，也不要把 1.1.0 的产物标成 1.1.1，也不要把 1.1.1 的产物标成 1.2.0，也不要把 1.2.0 的产物标成 1.2.1，也不要把 1.2.1 的产物标成 1.2.2，也不要把 1.2.2 的产物标成 1.2.3，也不要把 1.2.3 的产物标成 1.2.4。
```

第三步的「在该提交上打 tag `v1.2.3`」改成「在该提交上打 tag `v1.2.4`」。这一步仍不创建 tag，也不创建 Release。前面的 artifact 名称和四份文件名保持不动。不改 `CREDITS.md`。

- [ ] **Step 4: 跑版本测试**

Run:

```bash
python3 stm32-book/tests/test_build.py BookBuildContractTests.test_visual_polish_version_is_1_2_0 BookBuildContractTests.test_revision_file_lists_1_0_0_through_manifest_version -v
```

Expected: 退出码 0，末尾 `OK`。

- [ ] **Step 5: 提交版本**

```bash
git add stm32-book/manifest.json stm32-book/manifest-en.json stm32-book/revisions.json stm32-book/README.md stm32-book/tests/test_build.py
git commit -m "book: 把整书标成 1.2.4"
```

---

### Task 4: 验收并停在实施 PR

**Files:**
- 不新增文件。只有 Step 2 的 diff 越界时才改回 Task 1–3 允许的文件。

**Interfaces:**
- Consumes: Task 2 的 CSS、Task 3 的 `1.2.4`。
- Produces: 三条验收命令退出码 0。实施 PR 的说明写明 Book CI 变绿后 squash 合入，不设章节 HTML 的第二次人审。没有 tag，没有 Release。

- [ ] **Step 1: 跑整套测试和中英检查**

从仓库根目录运行：

```bash
python3 -m unittest discover stm32-book/tests -v
python3 stm32-book/build_html.py --check
python3 stm32-book/build_html.py --lang en --check
```

Expected: 三条都退出码 0。`discover` 的末尾是 `OK`。两条 `--check` 都以成功结束，不打印 `revision history starts at`。

`--check` 在临时目录里构建，不留下 `stm32-book/dist/`。人工抽看时再构建一次：

```bash
python3 stm32-book/build_html.py
python3 stm32-book/build_html.py --lang en
```

Expected: 写出 `stm32-book/dist/stm32-practical-book.html` 与 `stm32-book/dist/stm32-practical-book-en.html`。`stm32-book/dist/` 已在 `.gitignore` 里。不要 `git add` 这两份 HTML。

打开中文 HTML，看三处：

1. 目录。分部目标段是次要色，收束行有上边线，窄于 720px 时章列仍是一列。
2. 从第 00、03、04、06 章里任选一章。看 `h2` 左边条、一条含行内代码的句子、一个 `pre`、一张 `figure` 的图注。
3. 印刷预览里同一张图的图注小于正文，代码块是浅底。

英文书用同一次构建抽目录或一章即可。看不了浏览器时，在实施 PR 说明里写明已经由 `test_typography_e_css_contract`、`test_narrow_desktop_stacks_compass_without_part_number_collision` 和 `test_print_layout_keeps_reading_units_together` 覆盖 token、`3px`、`rgb(7, 94, 132)`、印刷浅色代码底和图注 9pt，并注明人工抽看没有做。不要为了抽看去改测试或 CSS。

- [ ] **Step 2: 确认 diff 没有越界**

Run:

```bash
git diff --name-only origin/main...HEAD
```

实施分支的 `origin/main` 应已含 Batch4。Expected: 只有这六个路径：

```text
stm32-book/README.md
stm32-book/build_html.py
stm32-book/manifest-en.json
stm32-book/manifest.json
stm32-book/revisions.json
stm32-book/tests/test_build.py
```

多出来的 `docs/` 正文、`docs/en/`、`CONTENT_GUIDE.md`、`cover.svg`、`assets/`、`tools/`、`CREDITS.md` 或独立 `.css`，撤回那些文件后再提交一次。提交说明写明撤回了哪一处。`build_html.py` 的 diff 仍只能落在 `CSS` 字符串里。

Run:

```bash
git diff --stat -- docs docs/en stm32-book/cover.svg assets tools
```

Expected: 无输出。

Run:

```bash
git tag --points-at HEAD
```

Expected: 无输出。不要运行 `gh release create`，不要 `git tag`，不要打 `v1.2.4`。

确认这些断言还在：

```bash
grep -n -E "0x271|167 ns|len\\(outline\\)" stm32-book/tests/test_build.py
```

Expected: `0x271`、`167 ns` 和 `self.assertEqual(44, len(outline))` 仍有匹配。

- [ ] **Step 3: 开实施 PR 并停住**

实施 PR 从 Batch4 已合入的 `main` 另开分支。标题写明这是排版微抛 E 的实施，不是本计划。说明里写上：

- 只改了内联 CSS，以及版本 1.2.4 · 2026-10-25。
- 中文和英文 `--check` 都通过，`python3 -m unittest discover stm32-book/tests -v` 通过。
- Book CI 变绿之后 squash 合入 `main`。不设章节 HTML 的第二次人审。Batch4 的人审停点不适用于这一刀。
- 合入后在本机 `D:\Users\STM32` 拉取这次 `main`。拉取不产生仓库 diff。
- 不打 tag，不创建 GitHub Release。
- 刀 B、刀 D、刀 C 不在这个 PR 里。

实施者自己不按合并按钮，不跑 `gh pr merge`。CI 还红时不合入。CI 变绿后由协调员 squash 合入。

这一步在验收已经通过时没有新的提交。

## 对照设计规格

| 设计规格里的要求 | 落在 |
| --- | --- |
| 样式仍在 `CSS` 字符串；实施只改 CSS、测试和版本戳记 | Global Constraints，File map |
| 建议版本 1.2.4，排在 Batch4 的 1.2.3 之后；1.2.2 时停手；高于 1.2.3 时写下一条修订号 | 开工条件，Task 3 |
| 日期在本计划里冻成 2026-10-25 | Global Constraints，Task 3 |
| `--font-sans` / `--font-mono` 保留前三名并追加回退；无 `@font-face`、无 `url(` | Task 1，Task 2 |
| `--type-body: 1.0625rem` 写在 `body`；印刷正文仍是 9.5pt | Task 2 |
| `h1` 用 `--type-h1` 且 clamp 数值不变；`h2` 1.55rem；`h3` 1.35rem；`h4` 1.2rem；通用 `h2` 的 margin 改成间距 token | Task 2 |
| 眉题收成 `--type-kicker`；已是 .78rem 的改成变量 | Task 2 |
| 封面 clamp、分部页大字、`.toc-jump` 保持字面量 | Task 1 的保留断言，Task 2 不改那些行 |
| 目录目标段次要色，章列行高 1.45，收束行上边线；`toc_html` 不改 | Task 2 |
| 行内和代码块共用 `0.92em`；`pre` 行高 1.65；行内底是 18% 强调色混合；不加边框；`.source-id code` 保持 `--accent-soft` | Task 2 |
| 图注和 `sub` 用 `--type-small` 与 `--leading-caption`；`figure img` 的 `.55rem` 保持 | Task 2 |
| 印刷代码 `#111` / `#f6f6f6`，`pre` 行高 1.45 且规则里没有 `avoid`；图注和 `sub` 为 9pt | Task 2 |
| 屏幕代码色 `#101820` / `#eef6f8` 和暗色代码色保持 | Task 1，Task 2 |
| 四对新增对比 ≥ 4.5；spine、左边条和混合底不进这张表 | Task 1 |
| 1.2.0 契约、书签 44、`0x271`、`167 ns`、三档 `pageOverflow` 不放宽 | Task 2 Step 4，Task 4 |
| 版本断言后移；修订四句；README 的 tag 名和误标句 | Task 3 |
| 中英 `--check` 与 unittest 通过后，Book CI 变绿再 squash；不打 tag | Task 4 |
| 不改正文、不改 `cover.svg`、不改 `assets/`、不拆 CSS、不实施 B/D/C | Global Constraints，Task 4 |
| 人工看目录、一章、印刷预览；英文抽一处 | Task 4 |

## 执行交接

本文件所在的 PR 只审阅计划，不实施。它不升版本，不改 `stm32-book/`。

实施要等 Batch4 的 1.2.3 出现在 `main` 的 `stm32-book/manifest.json` 之后，除非用户当时明确说可以提前。然后从那个 `main` 另开分支，按任务顺序做。两种走法：

1. Subagent-Driven：每个任务一个新的执行者，任务之间再审一遍 diff。
2. Inline：同一会话里用 executing-plans，做完一个任务再进下一个。

Task 1 的提交会使整套测试变红。实施 PR 要等到 Task 4 三条命令都退出码 0 再开。协调员在 Book CI 变绿后 squash 合入。不设章节人审停点。不打 tag，不创建 Release。

# 整书密度刀 F Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

I'm using the writing-plans skill to create the implementation plan.

**Goal:** 只收阅读面空白一档：把 `tokens.json` 里七个亮色间距令牌改成设计表上的值，把 `book.css` 里点名的 16 处字面量按表替换，封面标题板左右冻成字面量 `6%`，测试锁住新的拼合 CSS 哈希，再把整书标成 **1.2.8 · 2026-10-25**。本计划文件的 PR 不落地这些改动。

**Architecture:** 令牌仍只写在 `stm32-book/styles/tokens.json`。选择器仍在 `stm32-book/styles/book.css`。`load_css()` 在 import 时把四个哨兵填进模块级 `CSS`，中英文 HTML 继续是 `<style>{CSS}</style>`。封面标题板的左右留白是 `.cover-panel` 的 padding，写在 `book.css` 第 26 行；`build_html.py` 只输出 `<div class="cover-panel">`，不持有这段 padding。所以封面 `6%` 字面量改在 `book.css`，`build_html.py` 的 diff 必须为空。先把会失败的契约写进现有两个测试文件，再改令牌，再改样式，最后同一提交改版本戳和版本断言。不新开测试文件，不升 `schema`，不改 `load_css()`。

**Tech Stack:** Python 3 标准库（`json`、`hashlib`、`pathlib`、`unittest`）、现有 `stm32-book/build_html.py`、`stm32-book/styles/tokens.json`、`stm32-book/styles/book.css`、`python3 stm32-book/tests/test_build.py`、`python3 stm32-book/tests/test_sample_svg_c.py`、`python3 -m unittest discover stm32-book/tests -v`。不新增依赖，不改 `requirements.txt`。

`stm32-book/tests/` 不是 Python 包。单条测试写成 `python3 stm32-book/tests/test_build.py BookBuildContractTests.<方法名> -v`，或 `python3 stm32-book/tests/test_sample_svg_c.py SampleSvgCTests.<方法名> -v`。不要写成 `python3 -m unittest stm32-book.tests...`。整套测试仍用 `python3 -m unittest discover stm32-book/tests -v`。类名分别是 `BookBuildContractTests` 和 `SampleSvgCTests`。

设计规格：`docs/superpowers/specs/2026-10-25-book-density-F-design.md`（PR #48，`7e065b8`）。

写本计划时的尖端是 `7e065b8d07b879b0b24b23c287c346951b6918c7`（`docs: 密度刀 F 设计，阅读面间距收一档 (#48)`）。这一尖端的整书版本仍是 **1.2.7**，日期仍是 `2026-10-25`。样式字节与刀 C 实施 `a481335f4d56658dc4c356454431dd4398ccff3f` 相同。`builder.CSS` 的 SHA-256 是 `a4ccd1403ab742e82f67c39053c2609da1c9a8afa126d4f6b988a5b9559a5ac4`。`tokens.json` 的 SHA-256 是 `c5bb7846ed74c394f59634b1b40c99d1264c9dd41b018dfb7bfad8a08bea014b`。`book.css` 源文件 19838 字节，SHA-256 是 `7c821dba13bebb86123def3f243a480af460d897358d548c364860038fb563f5`，第一个字节是换行。`cover.svg` 的 SHA-256 是 `37dbedd70d2be8e94f4cdf05b60541f69d0107af6374902f8062c8e0bf74dedd`。下面的行号属于 `7e065b8`。实施时若行号被别的提交挪动，按选择器和原文定位。

`7e065b8` 只新增了设计规格。它下面的 `a481335`（PR #47）才是刀 C 的实施。实施基线是本计划合入之后的 `main`，不是本计划的分支。本计划的 PR 只新增本文件。

写本计划时，在 `7e065b8` 的 `tokens.json` 与 `book.css` 上只做下面任务里的那 7 处和 16 处字符串替换，再用与 `load_css()` 相同的四次哨兵替换，得到的三串 SHA-256 与设计规格「哈希」一节一致。未替换的文件仍是上面的基线三串。每一处旧字符串在源文件里都只出现一次。

设计规格「实施 PR」的 1–7 步在本计划里的位置：

| 规格里的顺序 | 本计划 |
| --- | --- |
| 1. 确认基线 | 开工条件。不产生提交 |
| 2. 七个亮色令牌 | Task 2 |
| 3. 16 处 CSS，含封面标题板字面量 `6%` | Task 3。`build_html.py` 不改 |
| 4. 测试（版本断言留到下一步） | Task 1。版本断言在 Task 4 |
| 5. 版本 | Task 4 |
| 6. 验证 | Task 5 |
| 7. 合入 | Task 5 的最后一步 |

Task 1 先写会失败的契约，是为了和刀 B、刀 D、刀 E 一样：期望值来自规格，不从实施时手写的 CSS 反推。最终 diff 仍必须同时有七个令牌、16 处样式、测试和版本戳。

## Global Constraints

- 本计划 PR 不实施刀 F。不改 `stm32-book/styles/tokens.json`，不改 `stm32-book/styles/book.css`，不改 `stm32-book/build_html.py`，不改 `stm32-book/tests/`，不改两份 manifest、`revisions.json`、`stm32-book/README.md`。CI 变绿不等于本 PR 可以自动合入。等人审完计划再合。
- 实施时可以改的只有：`stm32-book/styles/tokens.json`、`stm32-book/styles/book.css`、`stm32-book/tests/test_build.py`、`stm32-book/tests/test_sample_svg_c.py`、`stm32-book/revisions.json`、`stm32-book/manifest.json`、`stm32-book/manifest-en.json`、`stm32-book/README.md`。
- 目标版本是 **1.2.8 · 2026-10-25**。预期路径上日期写死 `2026-10-25`。两份 manifest、`revisions.json` 和 README 写同一个版本、同一个日期。
- 实施 PR 在 Book CI（`.github/workflows/book.yml`，名称 `Book CI`）的 `book` 与 `book-en` 都变绿之后，由人决定是否 squash 合入 `main`。不在 CI 变绿后自动合。不改 workflow。不改正文。
- 不打 tag，不创建 GitHub Release。合入后在本机 `D:\Users\STM32` 拉取这次 `main`。拉取不产生仓库 diff。
- 只改 `light` 里这七个值。键名、键序、其余 33 个亮色值、`dark`、`print`、`coverLock`、`schema` 保持。JSON 保持两个空格缩进，不重排，不用 `json.dumps`。`light` 仍是 40 个键。`schema` 仍是整数 `1`。`coverLock` 仍是 `--paper`、`--ink`、`--muted`、`--warn`、`--line`、`--spine`。

| 属性 | 现在 | 实施后 |
| --- | --- | --- |
| `--space-chapter` | `3.5rem` | `2.75rem` |
| `--space-figure` | `1.5rem` | `1.25rem` |
| `--space-paragraph` | `1.25rem` | `1rem` |
| `--space-bar` | `0.75rem` | `0.625rem` |
| `--inset` | `6%` | `4.5%` |
| `--leading-body` | `1.75` | `1.65` |
| `--measure` | `40rem` | `42rem` |

- JSON 里的新长度小数前写 `0`：`0.625rem`、`0.75rem` 这种已有写法保持。样式表里的新长度小数前不写 `0`：`.625rem`、`.75rem`、`.4rem`。不要把样式表里的 `.625rem` 收成 `0.625rem`，也不要把 JSON 里的 `0.625rem` 收成 `.625rem`。多一个字节，哈希就会离开下面这张表。
- 拼合结果与两个源文件的 SHA-256，在只做了本计划的替换之后，必须是：

| 对象 | 实施后 |
| --- | --- |
| `builder.CSS` | `aacd30dcb0efbff80d004295338c9be99b35e19cb744d6f4b1e662a0b8f31baf` |
| `stm32-book/styles/tokens.json` | `9d07dad497b824c9e2038ddf1e28cb77974451acb6c3b9773863df7c8c90d0bd` |
| `stm32-book/styles/book.css` | `cc2656e9c7e0ea311fc79d36c920c20d82012d8907b000ec940a93095845e480` |
| `stm32-book/cover.svg` | `37dbedd70d2be8e94f4cdf05b60541f69d0107af6374902f8062c8e0bf74dedd`（保持） |

- 对不上时先停，对照替换表看多改了什么。不要改测试里的期望去迁就另一份样式，不要改令牌值去凑哈希，不要重排文件。
- 封面标题板左右冻结为字面量 `6%`。`.cover-panel` 的 `padding: 1.8rem var(--inset) 2.6rem` 改成 `padding: 1.8rem 6% 2.6rem`。上下仍是 `1.8rem` 和 `2.6rem`。这一处在 `book.css`，不在 `build_html.py`。窄屏 `.cover-panel { padding: 1.3rem 1rem 1.8rem; }` 保持原文。720px 段里仍然不出现 `var(--inset)`。
- `footer.book-footer` 走另一个方向：`padding: 3rem 6% 5.2rem` 改成 `padding: 2.25rem var(--inset) 3.5rem`。页脚左右跟新的 `--inset`，不要再写第二份 `6%`。
- `h2`、`h3`、`h4`、章内 `h2`、`pre`、`figure`、`img` 上已有的 `var()` / `calc()` 源文本保持。不要把 `calc(var(--space-figure) + var(--space-paragraph))` 展成 `2.25rem`。`h2, h3, h4` 的 `scroll-margin-top: 1.25rem` 是字面量，保持。它不是 `--space-paragraph`。
- 不改字号令牌、`--leading-heading`、`--leading-caption`、`--leading-toc`、`--leading-code`、`--tracking-body`、`--tracking-kicker`、`--radius`、`--elev`。不改暗色和印刷的 15 个颜色。不改画板 `#10242e`、`#0c1c24`、`#f4f1ea`。印刷正文仍是 `9.5pt` / `line-height: 1.55`。`@page` 仍是 `16mm 15mm 18mm`。
- 不改 `.cover` 的 `min-height: 92vh`，不改 `.part-divider` 的 `min-height: 52vh`、`padding: 4.5rem var(--inset) 4.5rem`、`gap: .35rem`。不改 `.part-index` 的 `clamp` 和窄屏 `3rem`。不改 `.toc-jump`。不改 `.book` 的 `980px`。不加新的自定义属性，不加第六个 `@media`。
- 不改 `load_css` 的签名和四个哨兵。`CSS = load_css()` 仍在 import 时执行。HTML 模板保持 `<style>{CSS}</style>`。不加 `<link`。
- 不改 `docs/00`–`28`、`docs/en/`、附录 Markdown、两份 `CONTENT_GUIDE.md`、罗盘文案、`revisions.json` 里已有句子、`cover.svg`、仓库根 `assets/`、`tools/`、`CREDITS.md`、`.github/workflows/book.yml`。样本 SVG、封面 SVG、GIF 的字节保持。
- 不改 `toc_html`、分类函数、罗盘 HTML、书签、章号。出版书签仍是 44 条。不删 `0x271`、`167 ns`、样本章和各批加厚的断言。`pageOverflow` 为 0 的 1200、840、390 三档不放宽。对比仍用 `_contrast_ratio`，门槛仍是 4.5。色值一对都不改。
- 修订说明只用设计里的四句。不写章节名。已有修订句子一字不改。
- `.imprint-lead, .imprint .colophon` 的 `max-width: 40em` 保持。不要把它收成 `40rem` 或 `var(--measure)`。只有 `.revision-history > p, .index-lead` 的 `max-width: 40rem` 改成 `max-width: var(--measure)`。

上一句「Book CI 变绿后由人决定是否 squash」指刀 F 的实施 PR。本计划文件的 PR 等人审阅，不在 CI 变绿后自动合入，也不在本 PR 里改 `stm32-book/`。

## 开工条件

实施开始时先读实施分支所基于的 `main` 上的 `stm32-book/manifest.json`，只看 `version` 和 `date`。不要在本计划的分支上改令牌、CSS 或版本。

- `version` 低于 `1.2.7`：停。刀 C 还没在这条历史上。不开实施分支。
- `version` 是 `1.2.7`：实施版写成 `1.2.8`，日期写成 `2026-10-25`。下面任务里的字面量按这个走。这是预期路径。`7e065b8` 就是这个状态。`date` 已经是 `2026-10-25` 时，manifest 的 `date` 行保持原文。
- `version` 已经高于 `1.2.7`（仍是 `1.2.x`，且补丁号大于 7）：停手，不要把 `1.2.8` 硬套上去。实施版写成下一条修订号，日期用实施当天的 ISO 日期。Task 4 里每一处 `1.2.8` 换成这个新号，每一处当作「上一版」的 `1.2.7` 换成当时 manifest 的 `version`。修订四句不变。已有修订句子保持原文，只把索引后移一位。样式替换表和三串哈希不变；哈希对不上就按下一条停，不要为了新版本去改样式。
- 三串基线哈希已经不是下面的值：停。说明 `main` 上的样式已经离开这份设计所依据的字节。不要在分叉上套这七个值，不要改测试期望，不要重算哈希后再继续。

接着在仓库根核对四个哈希：

```bash
python3 - << 'PY'
import hashlib
from pathlib import Path
root = Path("stm32-book")
print("tokens", hashlib.sha256((root / "styles" / "tokens.json").read_bytes()).hexdigest())
print("book.css", hashlib.sha256((root / "styles" / "book.css").read_bytes()).hexdigest())
print("cover.svg", hashlib.sha256((root / "cover.svg").read_bytes()).hexdigest())
PY
python3 -m pip install -q 'Markdown>=3.11,<4'
python3 - << 'PY'
import hashlib
import importlib.util
from pathlib import Path
path = Path("stm32-book/build_html.py")
spec = importlib.util.spec_from_file_location("stm32_book_builder", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
print("CSS", hashlib.sha256(module.CSS.encode("utf-8")).hexdigest())
PY
```

Expected:

```text
tokens c5bb7846ed74c394f59634b1b40c99d1264c9dd41b018dfb7bfad8a08bea014b
book.css 7c821dba13bebb86123def3f243a480af460d897358d548c364860038fb563f5
cover.svg 37dbedd70d2be8e94f4cdf05b60541f69d0107af6374902f8062c8e0bf74dedd
CSS a4ccd1403ab742e82f67c39053c2609da1c9a8afa126d4f6b988a5b9559a5ac4
```

`validate_revisions()` 要求 `revisions.json` 第一条的 `version` 等于 manifest 的 `version`。Task 4 必须同一提交改测试、两份 manifest、`revisions.json` 和 README。

## File map

| 路径 | 实施时的责任 |
| --- | --- |
| `docs/superpowers/plans/2026-10-25-book-density-F.md` | 本计划。本 PR 只新增这一份 |
| `stm32-book/tests/test_build.py` | Task 1 改间距、封面 padding、图注、目录间隙和拼合哈希。Task 4 只改版本断言 |
| `stm32-book/tests/test_sample_svg_c.py` | Task 1 改三串哈希。`cover.svg` 哈希、53 张 SVG、GIF 汇总哈希保持原文 |
| `stm32-book/styles/tokens.json` | Task 2。只替换七个亮色值 |
| `stm32-book/styles/book.css` | Task 3。只做 16 处替换。封面标题板左右在这里写成字面量 `6%` |
| `stm32-book/manifest.json` | Task 4：`version` 改为 `1.2.8`。预期路径上 `date` 仍是 `2026-10-25` |
| `stm32-book/manifest-en.json` | 同上 |
| `stm32-book/revisions.json` | Task 4：`entries` 最前插入 1.2.8。已有条目一字不改 |
| `stm32-book/README.md` | Task 4：当前版本句、发布节的版本句、tag 名，以及「也不要把 1.2.7 的产物标成 1.2.8」 |

`stm32-book/build_html.py` 不在这张表里。实施 diff 里它必须是空的。封面标题板的 `6%` 由 Task 3 写进 `book.css`，再由已有的 `load_css()` 填进 `<style>{CSS}</style>`。不要在 `<div class="cover-panel">` 上加 `style`，不要把 `6%` 写进 Python。

---

### Task 1: 先写下会失败的密度契约

**Files:**
- Modify: `stm32-book/tests/test_build.py`（`test_visual_polish_css_contract` 的令牌组、`figure img`、`.cover-panel`；`test_typography_e_css_contract` 的 `figure img`、`.contents li`、`.contents ol`；`test_css_token_extract_contract` 的拼合哈希）
- Modify: `stm32-book/tests/test_sample_svg_c.py`（`test_sample_svg_c_contract` 里三串哈希）
- Test: `stm32-book/tests/test_build.py`、`stm32-book/tests/test_sample_svg_c.py`

**Interfaces:**
- Consumes: 已有的 `BookBuildContractTests._css_rule`、`self.builder.CSS`、`BOOK_DIR`。屏幕段是第一个 `@media` 之前。`SampleSvgCTests.test_sample_svg_c_contract` 已经用 SHA-256 锁 `builder.CSS`、`tokens.json`、`book.css`、`cover.svg`。这一任务还不改样式文件。
- Produces: 上述方法改完后的期望字符串。Task 2 和 Task 3 按这些字符串把文件改到测试变绿。这一任务不改版本断言，不改 `tokens.json`，不改 `book.css`，不改 `build_html.py`。

这一提交之后，整套 `discover` 会失败。这是预期。不要开实施 PR，不要 squash。间距契约要到 Task 3 才绿。版本断言现在就应该仍绿，因为版本文件还没动。

不要新开测试方法。不要改 `test_visual_polish_contrast_clears_4_5`。不要改 `test_code_glossary_and_print_css_keep_reading_units_movable` 里三档 `pageOverflow` 的期望 `0`。不要改 `test_cover_svg_stays_self_contained` 和 `test_cover_imprint_d_contract`。下面这些断言的源文本保持，用来防止把 `calc()` 展成字面量，或把封面窄屏、分部海报一起改掉：

- `margin: calc(var(--space-figure) + var(--space-paragraph)) 0 var(--space-bar)`
- `margin: var(--space-figure) 0 calc(var(--space-bar) / 2)`
- `margin: var(--space-paragraph) 0 calc(var(--space-bar) / 2)`
- `padding-left: var(--space-bar)` 与 `border-left: 3px solid var(--accent)`
- `padding: 4.5rem var(--inset) 4.5rem` 与 `min-height: 52vh`
- `margin: var(--space-figure) auto` 与 `margin: var(--space-paragraph) 0 var(--space-figure)`
- `line-height: var(--leading-body)` 与全部 `--type-*`、`--leading-heading`、`--leading-caption`、`--leading-toc`、`--leading-code`
- `.cover-panel { padding: 1.3rem 1rem 1.8rem; }`，以及 `self.assertNotIn("var(--inset)", narrow)`
- `columns: 2` 与窄屏 `columns: 1`
- `cover.svg` 哈希 `37dbedd70d2be8e94f4cdf05b60541f69d0107af6374902f8062c8e0bf74dedd`
- 53 张 SVG 的画布、文本哈希、60 KB / 80 KB 上限
- GIF 汇总哈希 `bd674b4aaf427c36ec54f92853f13d52cf160e41acd2a06f89c2479b9f31c26f`，以及 `self.assertEqual(40, len(gifs))`

- [ ] **Step 1: 改 `test_visual_polish_css_contract` 的七个令牌、图注和封面标题板**

`7e065b8` 上，令牌组在 `test_build.py` 约第 1028–1045 行。把这一组换成：

```python
        for token in (
            "--paper: #fbfaf7",
            "--ink: #17202a",
            "--accent: #075e84",
            "--muted: #5e6872",
            "--warn: #9a3d1c",
            "--tip: #1b5c45",
            "--spine: #c4552a",
            "--space-bar: 0.625rem",
            "--space-paragraph: 1rem",
            "--space-figure: 1.25rem",
            "--space-chapter: 2.75rem",
            "--inset: 4.5%",
            "--leading-body: 1.65",
            "--measure: 42rem",
            "--tracking-body: 0.01em",
            "--tracking-kicker: 0.14em",
            "--radius: 0.7rem",
            "--elev: 0 1px 2px color-mix(in srgb, var(--ink) 8%, transparent)",
        ):
            self.assertIn(token, screen)
```

同一方法里，约第 1077 行：

```python
        self.assertIn("margin: 0 auto .4rem", self._css_rule(screen, "figure img"))
```

约第 1118 行，`.cover-panel` 的那一条：

```python
        self.assertIn("padding: 1.8rem 6% 2.6rem", panel)
```

颜色、`--tracking-*`、`--radius`、`--elev`、窄屏 `.cover-panel { padding: 1.3rem 1rem 1.8rem; }` 和 `self.assertNotIn("var(--inset)", narrow)` 保持原文。`test_typography_e_css_contract` 里还有一处 `margin: 0 auto .55rem`，这一步先留着，下一步再改。两处都要改，不能只改一处。

- [ ] **Step 2: 改 `test_typography_e_css_contract` 的图注和目录**

约第 1292 行：

```python
        self.assertIn("margin: 0 auto .4rem", self._css_rule(screen, "figure img"))
```

约第 1297 行：

```python
        self.assertIn("margin: .2rem 0", self._css_rule(screen, ".contents li"))
```

约第 1316 行：

```python
        self.assertIn("column-gap: 2.25rem", self._css_rule(screen, ".contents ol"))
```

`line-height: var(--leading-toc)`、`columns: 2`、窄屏 `columns: 1`、`position: sticky` 和四段 `h2` / `h3` / `h4` 的 `calc()` / `var()` 保持原文。

- [ ] **Step 3: 改两处拼合哈希和两个源文件哈希**

`test_css_token_extract_contract` 约第 1496–1499 行，只换这一串：

```python
        self.assertEqual(
            "aacd30dcb0efbff80d004295338c9be99b35e19cb744d6f4b1e662a0b8f31baf",
            hashlib.sha256(self.builder.CSS.encode("utf-8")).hexdigest(),
        )
```

`test_sample_svg_c.py` 的 `test_sample_svg_c_contract` 约第 191–203 行，三串换成：

```python
        self.assertEqual(
            "aacd30dcb0efbff80d004295338c9be99b35e19cb744d6f4b1e662a0b8f31baf",
            hashlib.sha256(self.builder.CSS.encode("utf-8")).hexdigest(),
        )
        self.assertEqual(
            "9d07dad497b824c9e2038ddf1e28cb77974451acb6c3b9773863df7c8c90d0bd",
            hashlib.sha256((BOOK_DIR / "styles" / "tokens.json").read_bytes()).hexdigest(),
        )
        self.assertEqual(
            "cc2656e9c7e0ea311fc79d36c920c20d82012d8907b000ec940a93095845e480",
            hashlib.sha256((BOOK_DIR / "styles" / "book.css").read_bytes()).hexdigest(),
        )
```

紧跟着的 `cover.svg` 断言保持：

```python
        self.assertEqual(
            "37dbedd70d2be8e94f4cdf05b60541f69d0107af6374902f8062c8e0bf74dedd",
            hashlib.sha256((BOOK_DIR / "cover.svg").read_bytes()).hexdigest(),
        )
```

不要改这个方法里 53 张 SVG 的行，也不要改 GIF 汇总哈希。

- [ ] **Step 4: 跑新期望，确认失败，并确认版本测试仍绿**

Run:

```bash
python3 stm32-book/tests/test_build.py BookBuildContractTests.test_visual_polish_css_contract -v
```

Expected: 退出码 1。失败信息含 `--space-bar: 0.625rem`。样式还是 1.2.7 的 `0.75rem`。不要去改 `tokens.json` 来让它变绿。那是 Task 2。

Run:

```bash
python3 stm32-book/tests/test_build.py BookBuildContractTests.test_typography_e_css_contract -v
```

Expected: 退出码 1。失败信息含 `margin: 0 auto .4rem`。

Run:

```bash
python3 stm32-book/tests/test_build.py BookBuildContractTests.test_css_token_extract_contract -v
```

Expected: 退出码 1。`AssertionError` 里一边是 `aacd30dcb0efbff80d004295338c9be99b35e19cb744d6f4b1e662a0b8f31baf`，另一边是 `a4ccd1403ab742e82f67c39053c2609da1c9a8afa126d4f6b988a5b9559a5ac4`。

Run:

```bash
python3 stm32-book/tests/test_sample_svg_c.py SampleSvgCTests.test_sample_svg_c_contract -v
```

Expected: 退出码 1。同样先倒在拼合哈希上，因为这个方法先断言 `builder.CSS`。

Run:

```bash
python3 stm32-book/tests/test_build.py BookBuildContractTests.test_visual_polish_version_is_1_2_0 -v
```

Expected: 通过。版本仍是 1.2.7。

- [ ] **Step 5: 提交失败的测试**

```bash
git add stm32-book/tests/test_build.py stm32-book/tests/test_sample_svg_c.py
git commit -m "book: 为密度刀 F 写下会失败的间距契约"
```

这一步的 diff 只能落在这两个测试文件。不要加 `styles/`，不要改 `build_html.py`，不要改版本文件。

---

### Task 2: 只改七个亮色令牌

**Files:**
- Modify: `stm32-book/styles/tokens.json`（第 19–25 行那七个值）
- Test: 开工条件里的 `tokens.json` SHA-256。整套 `discover` 这一步仍然失败

**Interfaces:**
- Consumes: Task 1 写上的 `9d07dad497b824c9e2038ddf1e28cb77974451acb6c3b9773863df7c8c90d0bd`。`book.css` 此时还是旧字节。
- Produces: `light` 里七个新值。键序不变。Task 3 依赖这份 JSON 的字节，因为拼合哈希要把新令牌填进新样式。

这一步不改 `book.css`，不改测试，不改版本。只改令牌时，`tokens.json` 的哈希变成新值，但 `builder.CSS` 既不是旧的 `a4ccd140…`，也还不是 `aacd30dc…`。`discover` 继续失败是预期。不要为了这一步去改测试期望。

- [ ] **Step 1: 按整行替换七个值**

在仓库根运行。脚本只做字符串替换，每个旧字符串必须恰好出现一次。不要 `json.dumps`，不要重排，不要改缩进。

```bash
python3 - << 'PY'
from pathlib import Path
path = Path("stm32-book/styles/tokens.json")
text = path.read_text(encoding="utf-8")
pairs = (
    ('"--measure": "40rem"', '"--measure": "42rem"'),
    ('"--space-bar": "0.75rem"', '"--space-bar": "0.625rem"'),
    ('"--space-paragraph": "1.25rem"', '"--space-paragraph": "1rem"'),
    ('"--space-figure": "1.5rem"', '"--space-figure": "1.25rem"'),
    ('"--space-chapter": "3.5rem"', '"--space-chapter": "2.75rem"'),
    ('"--inset": "6%"', '"--inset": "4.5%"'),
    ('"--leading-body": "1.75"', '"--leading-body": "1.65"'),
)
for old, new in pairs:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{old} count {count}")
    text = text.replace(old, new, 1)
if not text.endswith("\n"):
    raise SystemExit("tokens.json must end with a newline")
path.write_text(text, encoding="utf-8", newline="\n")
PY
```

Expected: 退出码 0，没有输出。

替换后的七行必须是：

```json
    "--measure": "42rem",
    "--space-bar": "0.625rem",
    "--space-paragraph": "1rem",
    "--space-figure": "1.25rem",
    "--space-chapter": "2.75rem",
    "--inset": "4.5%",
    "--leading-body": "1.65",
```

`--leading-code` 仍是 `"1.65"`。不要把 `"--leading-body": "1.65"` 写到 `"--leading-code"` 那一行上。`--paper` 仍是 `#fbfaf7`，`--ink` 仍是 `#17202a`，`--accent` 仍是 `#075e84`，`--spine` 仍是 `#c4552a`。`dark` 和 `print` 的对象保持字节。`coverLock` 仍是同一行：`"coverLock": ["--paper", "--ink", "--muted", "--warn", "--line", "--spine"]`。顶层键序仍是 `schema`、`light`、`dark`、`print`、`coverLock`。

- [ ] **Step 2: 核对令牌文件哈希，并确认样式测试仍失败**

```bash
python3 - << 'PY'
import hashlib
from pathlib import Path
digest = hashlib.sha256(Path("stm32-book/styles/tokens.json").read_bytes()).hexdigest()
print(digest)
if digest != "9d07dad497b824c9e2038ddf1e28cb77974451acb6c3b9773863df7c8c90d0bd":
    raise SystemExit("tokens.json hash drifted")
PY
```

Expected: 打印 `9d07dad497b824c9e2038ddf1e28cb77974451acb6c3b9773863df7c8c90d0bd`，退出码 0。

对不上就停。把文件还原，对照上面七行。不要改 Task 1 的期望哈希。

Run:

```bash
python3 stm32-book/tests/test_sample_svg_c.py SampleSvgCTests.test_sample_svg_c_contract -v
```

Expected: 退出码 1。拼合哈希和 `book.css` 哈希都还不是新值。这是预期。

- [ ] **Step 3: 提交令牌**

```bash
git add stm32-book/styles/tokens.json
git commit -m "book: 把七个亮色间距令牌收一档"
```

这一步的 diff 只能落在 `stm32-book/styles/tokens.json`。不要带着仍失败的测试去开实施 PR。

---

### Task 3: 改 16 处样式，并把封面标题板左右冻成字面量 6%

**Files:**
- Modify: `stm32-book/styles/book.css`（下面 16 处，各出现一次）
- Test: `BookBuildContractTests.test_visual_polish_css_contract`、`test_typography_e_css_contract`、`test_css_token_extract_contract`、`SampleSvgCTests.test_sample_svg_c_contract`

**Interfaces:**
- Consumes: Task 1 的期望字符串，Task 2 的七个令牌值。`load_css()` 会把 JSON 里的 `0.625rem` 填进拼合结果；`book.css` 源文件自己写的新长度仍是 `.625rem` 这种不带前导 0 的写法。
- Produces: `book.css` 源文件哈希 `cc2656e9c7e0ea311fc79d36c920c20d82012d8907b000ec940a93095845e480`，以及拼合哈希 `aacd30dcb0efbff80d004295338c9be99b35e19cb744d6f4b1e662a0b8f31baf`。版本文件仍是 1.2.7。

封面 inset 的字面量在这里完成。`build_html.py` 约第 1341 行是 `<div class="cover-panel">`，约模板里是 `<style>{CSS}</style>`。padding 不在 Python 里。本任务结束时 `git diff -- stm32-book/build_html.py` 必须为空。

- [ ] **Step 1: 确认 `build_html.py` 没有封面 padding 字面量**

```bash
python3 - << 'PY'
from pathlib import Path
text = Path("stm32-book/build_html.py").read_text(encoding="utf-8")
if "padding: 1.8rem" in text or "padding: 1.8rem 6%" in text:
    raise SystemExit("cover padding leaked into build_html.py")
if '<div class="cover-panel">' not in text:
    raise SystemExit("cover panel shell missing")
if "<style>{CSS}</style>" not in text:
    raise SystemExit("embedded style missing")
print("cover inset literal stays in book.css")
PY
```

Expected: 打印 `cover inset literal stays in book.css`，退出码 0。不要改 `build_html.py`。

- [ ] **Step 2: 按旧字符串整段替换 16 处**

每一处在 `7e065b8` 的 `book.css` 里只出现一次。脚本按这个顺序替换。不要重排文件，不要把 `.75rem` 收成 `0.75rem`。

```bash
python3 - << 'PY'
from pathlib import Path
path = Path("stm32-book/styles/book.css")
text = path.read_text(encoding="utf-8")
pairs = (
    ("padding: 1.8rem var(--inset) 2.6rem", "padding: 1.8rem 6% 2.6rem"),
    ("margin-bottom: 1.6rem; padding-bottom: .95rem", "margin-bottom: 1.25rem; padding-bottom: .75rem"),
    ("gap: .75rem; margin: 1.5rem 0 2.6rem; padding: .95rem", "gap: .625rem; margin: 1.25rem 0 1.75rem; padding: .75rem"),
    ("margin-top: 2rem; padding: 1rem 1.2rem", "margin-top: 1.5rem; padding: .85rem 1rem"),
    ("margin: 3rem 0 1rem", "margin: 2rem 0 .75rem"),
    ("margin: 1.25rem 0 1.45rem", "margin: 1rem 0 1.25rem"),
    ("padding: .75rem .75rem .65rem", "padding: .6rem .65rem .5rem"),
    ("margin: 0 auto .55rem", "margin: 0 auto .4rem"),
    ("margin: 1.25rem 0 2rem", "margin: 1rem 0 1.5rem"),
    ("padding: 1.2rem 0", "padding: .85rem 0"),
    ("column-gap: 3rem", "column-gap: 2.25rem"),
    ("margin: .28rem 0", "margin: .2rem 0"),
    ("padding: .85rem 0 .45rem", "padding: .6rem 0 .35rem"),
    ("margin-top: 2.2rem", "margin-top: 1.5rem"),
    ("padding: 3rem 6% 5.2rem", "padding: 2.25rem var(--inset) 3.5rem"),
    ("max-width: 40rem", "max-width: var(--measure)"),
)
for old, new in pairs:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{old} count {count}")
    text = text.replace(old, new, 1)
if "0.625rem" in text:
    raise SystemExit("book.css used a leading zero; JSON owns 0.625rem")
if ".cover-panel { padding: 1.3rem 1rem 1.8rem; }" not in text:
    raise SystemExit("narrow cover panel changed")
narrow = text.split("@media (max-width: 720px)", 1)[1].split("@media", 1)[0]
if "var(--inset)" in narrow:
    raise SystemExit("720px slice gained var(--inset)")
if "min-height: 92vh" not in text or "min-height: 52vh" not in text:
    raise SystemExit("poster heights changed")
if "max-width: 40em" not in text:
    raise SystemExit("imprint 40em was rewritten")
if not text.startswith("\n"):
    raise SystemExit("book.css lost its leading newline")
path.write_text(text, encoding="utf-8", newline="\n")
print("16 replacements applied")
PY
```

Expected: 打印 `16 replacements applied`，退出码 0。`count` 不是 1 就停，不要改脚本去匹配第二处。

16 处和选择器的对应关系：

| 选择器 | 新片段 |
| --- | --- |
| `.cover-panel` | `padding: 1.8rem 6% 2.6rem` |
| `.chapter > header, .appendix > header, .part-closing > header, .back-matter > header` | `margin-bottom: 1.25rem; padding-bottom: .75rem` |
| `.chapter-compass` | `gap: .625rem; margin: 1.25rem 0 1.75rem; padding: .75rem` |
| `.companion` | `margin-top: 1.5rem; padding: .85rem 1rem` |
| `.quick-check` | `margin: 2rem 0 .75rem`。内边距 `1rem 1.4rem` 仍在同一行，不要改 |
| `blockquote.callout` | `margin: 1rem 0 1.25rem` |
| `figure` | `padding: .6rem .65rem .5rem`。`margin: var(--space-figure) auto` 仍在同一规则 |
| `figure img` | `margin: 0 auto .4rem` |
| `.table-scroll` | `margin: 1rem 0 1.5rem` |
| `.contents > section` | `padding: .85rem 0` |
| `.contents ol` | `column-gap: 2.25rem`。`columns: 2` 保持 |
| `.contents li` | `margin: .2rem 0`。`line-height: var(--leading-toc)` 保持 |
| `.contents > section > h2` | `padding: .6rem 0 .35rem` |
| `.back-to-toc` | `margin-top: 1.5rem` |
| `footer.book-footer` | `padding: 2.25rem var(--inset) 3.5rem` |
| `.revision-history > p, .index-lead` | `max-width: var(--measure)`。`color: var(--muted)` 保持 |

这些源文本必须仍在文件里，一个字符都不要改：

```text
margin: calc(var(--space-figure) + var(--space-paragraph)) 0 var(--space-bar)
margin: var(--space-figure) 0 calc(var(--space-bar) / 2)
margin: var(--space-paragraph) 0 calc(var(--space-bar) / 2)
padding: 4.5rem var(--inset) 4.5rem
margin: var(--space-figure) auto
margin: var(--space-paragraph) 0 var(--space-figure)
line-height: var(--leading-body)
scroll-margin-top: 1.25rem
.cover-panel { padding: 1.3rem 1rem 1.8rem; }
min-height: 92vh
min-height: 52vh
```

`.quick-check` 的 `padding: 1rem 1.4rem`、`blockquote.callout` 的内边距、`.compass-card` 的 `border-radius: .5rem`、`.toc-jump` 整条规则、印刷 `9.5pt` 和 `line-height: 1.55` 也保持。

- [ ] **Step 3: 核对三串哈希，并跑间距测试**

```bash
python3 - << 'PY'
import hashlib
import importlib.util
from pathlib import Path
root = Path("stm32-book")
expected = {
    "tokens": "9d07dad497b824c9e2038ddf1e28cb77974451acb6c3b9773863df7c8c90d0bd",
    "book.css": "cc2656e9c7e0ea311fc79d36c920c20d82012d8907b000ec940a93095845e480",
    "cover.svg": "37dbedd70d2be8e94f4cdf05b60541f69d0107af6374902f8062c8e0bf74dedd",
}
for name, digest in (
    ("tokens", hashlib.sha256((root / "styles" / "tokens.json").read_bytes()).hexdigest()),
    ("book.css", hashlib.sha256((root / "styles" / "book.css").read_bytes()).hexdigest()),
    ("cover.svg", hashlib.sha256((root / "cover.svg").read_bytes()).hexdigest()),
):
    print(name, digest)
    if digest != expected[name]:
        raise SystemExit(f"{name} hash drifted")
spec = importlib.util.spec_from_file_location("stm32_book_builder_f", root / "build_html.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
css = hashlib.sha256(module.CSS.encode("utf-8")).hexdigest()
print("CSS", css)
if css != "aacd30dcb0efbff80d004295338c9be99b35e19cb744d6f4b1e662a0b8f31baf":
    raise SystemExit("assembled CSS hash drifted")
PY
```

`Markdown` 若还没装，先跑开工条件里的 `python3 -m pip install -q 'Markdown>=3.11,<4'`。Expected: 四行哈希与 Global Constraints 的表一致，退出码 0。

对不上时，把 `book.css` 和 `tokens.json` 改回本任务开始前的字节，再按替换表重做。不要改 Task 1 的期望。

Run:

```bash
python3 stm32-book/tests/test_build.py BookBuildContractTests.test_visual_polish_css_contract -v
python3 stm32-book/tests/test_build.py BookBuildContractTests.test_typography_e_css_contract -v
python3 stm32-book/tests/test_build.py BookBuildContractTests.test_css_token_extract_contract -v
python3 stm32-book/tests/test_sample_svg_c.py SampleSvgCTests.test_sample_svg_c_contract -v
python3 stm32-book/tests/test_build.py BookBuildContractTests.test_visual_polish_contrast_clears_4_5 -v
```

Expected: 五条都通过。

Run:

```bash
python3 -m unittest discover stm32-book/tests -v
```

Expected: 退出码 0，末尾是 `OK`。版本仍是 1.2.7，所以版本测试现在就该绿。若只有版本断言失败，说明这一步误改了 `revisions.json` 或 manifest，先还原那些文件。

- [ ] **Step 4: 提交样式**

```bash
git add stm32-book/styles/book.css
git commit -m "book: 收阅读面空白并冻结封面标题板 6%"
```

这一步的 diff 只能落在 `stm32-book/styles/book.css`。`git diff HEAD~1 -- stm32-book/build_html.py` 必须为空。

---

### Task 4: 把整书标成 1.2.8

**Files:**
- Modify: `stm32-book/revisions.json`（`entries` 最前插入一条）
- Modify: `stm32-book/manifest.json`（只改 `version`）
- Modify: `stm32-book/manifest-en.json`（只改 `version`）
- Modify: `stm32-book/README.md`（当前版本句、发布节版本句、tag 名、再加一句误标）
- Modify: `stm32-book/tests/test_build.py`（只改版本断言）
- Test: `BookBuildContractTests.test_visual_polish_version_is_1_2_0`、`assert_version_history_and_index`、`test_revision_file_lists_1_0_0_through_manifest_version`、`test_english_book_is_a_separate_offline_edition`

**Interfaces:**
- Consumes: 开工条件定下的版本号。预期路径是上一版 `1.2.7`、新版 `1.2.8`、日期 `2026-10-25`。Task 3 已经让样式测试变绿。
- Produces: 两份 manifest、`revisions.json` 第一条和 README 当前版本句都是 `1.2.8` / `2026-10-25`。`validate_revisions()` 因此仍通过。

高于 `1.2.7` 的开工路径：下面每一处 `1.2.8` 换成当时的下一条修订号，每一处当作上一版的 `1.2.7` 换成当时 manifest 的 `version`，日期换成实施当天的 ISO 日期。四句修订说明不改。预期路径不要走这条。

这一任务不改 `tokens.json`、`book.css`、`build_html.py`、`test_sample_svg_c.py`。已有修订句子一字不改，包括 1.2.7 刀 C 的两句。

- [ ] **Step 1: 在 `revisions.json` 最前插入 1.2.8**

`entries` 数组的第一项现在是 1.2.7。在它前面插入下面这一项，并给新项后面留一个逗号。1.2.7 那一项的原文不要动：

```json
    {
      "version": "1.2.8",
      "date": "2026-10-25",
      "zh": [
        "章距、段距、图距、左右页边和正文行高各收一档，行长从 40rem 调到 42rem。字号和颜色不变。",
        "封面标题板的左右页边仍是 6%。暗色和印刷的颜色不改。样本图、封面图和 GIF 不重画。"
      ],
      "en": [
        "Chapter, paragraph, and figure spacing, the side inset, and the body line-height each move one step tighter. The measure moves from 40rem to 42rem. Type size and colors stay.",
        "The cover title plate keeps a 6% side inset. The dark palette and the print palette stay. Sample drawings, the cover drawing, and GIFs are not redrawn."
      ]
    },
```

四句必须与上面逐字相同。不要加第五句，不要改 1.2.7 刀 C 的「仓库里的样本图」那两句。

- [ ] **Step 2: 两份 manifest 只改 version**

`stm32-book/manifest.json` 和 `stm32-book/manifest-en.json` 各把这一行：

```json
  "version": "1.2.7",
```

改成：

```json
  "version": "1.2.8",
```

`"date": "2026-10-25"` 在预期路径上保持原文。不要改 `title`、`subtitle`、章号或罗盘。

- [ ] **Step 3: 改 README 的版本句，并追加一句误标**

`stm32-book/README.md` 第 17 行，只改版本号：

```markdown
当前版本：**v1.2.8 · 2026-10-25**。中文整书和英文整书共用这一版号。GitHub Release 仍要等这次提交进入 `main` 且 Book CI 产出四份文件之后，由有权限的人另行处理。
```

第 32 行关于 `tokens.json` 和 `book.css` 的那一句保持原文：

```markdown
样式来自 `stm32-book/styles/tokens.json` 和 `stm32-book/styles/book.css`，构建时拼进 HTML 的 `<style>`，`dist/` 里不另放 CSS。
```

发布节第 92 行，把开头的 `版本号已经是 1.2.7。` 改成 `版本号已经是 1.2.8。`。保留句末已有的「也不要把 1.2.6 的产物标成 1.2.7。」，并在这句后面紧接：

```text
也不要把 1.2.7 的产物标成 1.2.8。
```

第 98 行的 tag 名改成：

```markdown
3. 在该提交上打 tag `v1.2.8`，创建 GitHub Release，并附上这四份文件。
```

这一步仍不创建 tag，也不创建 Release。README 里的这句话是留给有权限的人以后做的，不是这一刀的实施步骤。

- [ ] **Step 4: 把版本断言后移一位，并锁住新的四句**

`assert_version_history_and_index` 约第 145 行，元组最前加上 `1.2.8`，并在现有 `>1.2.7<` 与 `>1.2.6<` 的比较之前加一行：

```python
        versions = ("1.2.8", "1.2.7", "1.2.6", "1.2.5", "1.2.4", "1.2.3", "1.2.2", "1.2.1", "1.2.0", "1.1.1", "1.1.0", "1.0.8", "1.0.7", "1.0.6", "1.0.5", "1.0.4", "1.0.3", "1.0.2", "1.0.1", "1.0.0")
        for version in versions:
            self.assertIn(f">{version}<", history)
        self.assertLess(history.index(">1.2.8<"), history.index(">1.2.7<"))
        self.assertLess(history.index(">1.2.7<"), history.index(">1.2.6<"))
```

后面从 `>1.2.6<` 到 `>1.0.0<` 的比较保持原文。

`test_revision_file_lists_1_0_0_through_manifest_version` 约第 185 行，列表最前加上 `1.2.8`，下一项仍是 `1.2.7`：

```python
            ["1.2.8", "1.2.7", "1.2.6", "1.2.5", "1.2.4", "1.2.3", "1.2.2", "1.2.1", "1.2.0", "1.1.1", "1.1.0", "1.0.8", "1.0.7", "1.0.6", "1.0.5", "1.0.4", "1.0.3", "1.0.2", "1.0.1", "1.0.0"],
```

两处 `<strong>v1.2.7</strong>` 改成 `<strong>v1.2.8</strong>`。一处在中文整书测试约第 279 行，一处在 `test_english_book_is_a_separate_offline_edition` 约第 436 行。同一英文测试约第 419 行：

```python
        self.assertEqual("1.2.8", manifest["version"])
```

`test_visual_polish_version_is_1_2_0` 约第 1624 行，把索引各后移一位，并让新的 `entries[0]` 使用上一节的四句。`entry` 这个名字继续指刀 C 的 1.2.7，它现在在 `entries[1]`。从 `self.assertEqual("1.2.7", entry["version"])` 起，直到 `previous` 的英文两句，字符串列表保持原文，不要重打。

删掉原来的九行绑定（`entry = revisions["entries"][0]` 到 `previous = revisions["entries"][7]`）以及紧跟着的六行 `assertEqual`（manifest、英文 manifest、`entry` 的 version 和 date）。用下面这一段代替。刀 C 的「仓库里的样本图」字符串列表不要删，它仍紧跟在这段最后两行之后，并仍属于现在的 `entry`：

```python
        density = revisions["entries"][0]
        entry = revisions["entries"][1]
        cover = revisions["entries"][2]
        tokens = revisions["entries"][3]
        typography = revisions["entries"][4]
        batch4 = revisions["entries"][5]
        batch3 = revisions["entries"][6]
        guide = revisions["entries"][7]
        previous = revisions["entries"][8]
        self.assertEqual("1.2.8", self.manifest["version"])
        self.assertEqual("2026-10-25", self.manifest["date"])
        self.assertEqual("1.2.8", english["version"])
        self.assertEqual("2026-10-25", english["date"])
        self.assertEqual("1.2.8", density["version"])
        self.assertEqual("2026-10-25", density["date"])
        self.assertEqual(density["date"], self.manifest["date"])
        self.assertEqual(density["date"], english["date"])
        self.assertEqual(
            [
                "章距、段距、图距、左右页边和正文行高各收一档，行长从 40rem 调到 42rem。字号和颜色不变。",
                "封面标题板的左右页边仍是 6%。暗色和印刷的颜色不改。样本图、封面图和 GIF 不重画。",
            ],
            density["zh"],
        )
        self.assertEqual(
            [
                "Chapter, paragraph, and figure spacing, the side inset, and the body line-height each move one step tighter. The measure moves from 40rem to 42rem. Type size and colors stay.",
                "The cover title plate keeps a 6% side inset. The dark palette and the print palette stay. Sample drawings, the cover drawing, and GIFs are not redrawn.",
            ],
            density["en"],
        )
        self.assertEqual("1.2.7", entry["version"])
        self.assertEqual("2026-10-25", entry["date"])
```

最后两行就是原来的 `entry` 断言。它们后面继续是刀 C、刀 D、刀 B、刀 E、1.2.3、1.2.2、1.2.1、1.2.0 那些已经写在方法里的 `assertEqual`，字符串列表不要重打。1.2.0 现在核对 `entries[8]`，因为 `previous` 已经指到那里。

同一方法末尾的 README 断言换成：

```python
        self.assertIn("当前版本：**v1.2.8 · 2026-10-25**", readme)
        self.assertIn("版本号已经是 1.2.8。", readme)
        self.assertIn("样式来自 `stm32-book/styles/tokens.json` 和 `stm32-book/styles/book.css`，构建时拼进 HTML 的 `<style>`，`dist/` 里不另放 CSS。", readme)
        self.assertIn("也不要把 1.1.1 的产物标成 1.2.0，", readme)
        self.assertIn("也不要把 1.2.0 的产物标成 1.2.1，", readme)
        self.assertIn("也不要把 1.2.1 的产物标成 1.2.2，", readme)
        self.assertIn("也不要把 1.2.2 的产物标成 1.2.3，", readme)
        self.assertIn("也不要把 1.2.3 的产物标成 1.2.4，", readme)
        self.assertIn("也不要把 1.2.4 的产物标成 1.2.5，", readme)
        self.assertIn("也不要把 1.2.5 的产物标成 1.2.6。", readme)
        self.assertIn("也不要把 1.2.6 的产物标成 1.2.7。", readme)
        self.assertIn("也不要把 1.2.7 的产物标成 1.2.8。", readme)
        self.assertIn("打 tag `v1.2.8`", readme)
        self.assertNotIn("当前版本：**v1.2.7", readme)
        self.assertNotIn("打 tag `v1.2.7`", readme)
```

不要删「也不要把 1.2.6 的产物标成 1.2.7。」。

- [ ] **Step 5: 跑版本测试和整套测试**

Run:

```bash
python3 stm32-book/tests/test_build.py BookBuildContractTests.test_visual_polish_version_is_1_2_0 -v
python3 stm32-book/tests/test_build.py BookBuildContractTests.test_revision_file_lists_1_0_0_through_manifest_version -v
python3 stm32-book/tests/test_build.py BookBuildContractTests.test_english_book_is_a_separate_offline_edition -v
```

Expected: 三条都通过。

Run:

```bash
python3 -m unittest discover stm32-book/tests -v
```

Expected: 退出码 0，末尾是 `OK`。

- [ ] **Step 6: 提交版本戳**

```bash
git add stm32-book/revisions.json stm32-book/manifest.json stm32-book/manifest-en.json stm32-book/README.md stm32-book/tests/test_build.py
git commit -m "book: 把整书标成 1.2.8"
```

这一步不要加入 `tokens.json`、`book.css`、`build_html.py`、`cover.svg`。它们在这一步没有新的改动。

---

### Task 5: 验收密度，并停在合入前

**Files:**
- Test: 整套 `stm32-book/tests`，以及中英文 `build_html.py --check`

**Interfaces:**
- Consumes: Task 1 到 Task 4 的全部文件。没有新的函数。
- Produces: 三条命令退出码 0。实施 PR 的 diff 只含 File map 里 Task 1 到 Task 4 的路径。不产生新的提交，除非验收发现前面的替换漏了。

- [ ] **Step 1: 跑设计规格里的三条命令**

```bash
python3 -m unittest discover stm32-book/tests -v
python3 stm32-book/build_html.py --check
python3 stm32-book/build_html.py --lang en --check
```

Expected: 三条退出码都是 0。`discover` 的末尾是 `OK`。两条 `--check` 都不打印 `revision history starts at`。

再核对四个哈希仍是 Global Constraints 那张表。`cover.svg` 仍是 `37dbedd70d2be8e94f4cdf05b60541f69d0107af6374902f8062c8e0bf74dedd`。

- [ ] **Step 2: 核对 diff 边界**

```bash
git diff --stat origin/main
```

可以出现的路径只有：

- `stm32-book/styles/tokens.json`
- `stm32-book/styles/book.css`
- `stm32-book/tests/test_build.py`
- `stm32-book/tests/test_sample_svg_c.py`
- `stm32-book/revisions.json`
- `stm32-book/manifest.json`
- `stm32-book/manifest-en.json`
- `stm32-book/README.md`

不允许出现 `stm32-book/build_html.py`、`stm32-book/cover.svg`、`docs/00`–`28`、`docs/en/`、`assets/`、`tools/`、`.github/workflows/book.yml`。

```bash
git diff --stat origin/main -- docs assets tools stm32-book/cover.svg stm32-book/build_html.py .github/workflows/book.yml
```

Expected: 空。

`light` 仍是 40 个键。`schema` 仍是 `1`。`coverLock` 仍是原来的六个名字。出版书签条数仍是 44，由 `test_publication_outline_keeps_parts_chapters_and_appendices` 锁住。没有 tag，没有 Release。

- [ ] **Step 3: 人看一章，不逐页看完 29 章**

宽于 960px 打开构建出的中文 HTML。第 00 章的段距、图距、罗盘下边距比 1.2.7 少一档。相邻两行的字不贴在一起。一行中文仍能读完再换行。目录分部之间更近，两列仍分开。封面标题板的左右留白与 1.2.7 相同，封面图相同。分部页仍大约半屏高。暗色下纸色和墨色与 1.2.7 相同。印刷预览里正文仍是浅底黑字，页边仍是 16mm / 15mm / 18mm。

英文书看同一章即可。样式与中文相同。

构建命令：

```bash
python3 stm32-book/build_html.py
python3 stm32-book/build_html.py --lang en
```

产物在 `stm32-book/dist/`。看完可以删掉这次本地产物，不要把 `dist/` 提交进实施 PR。

- [ ] **Step 4: 开实施 PR，并停在 squash 之前**

实施 PR 对着当时的 `main`。标题用中文，说明这是密度刀 F 的实施，版本 **1.2.8**。正文写明：

- 七个令牌与 16 处替换按本计划。
- 封面标题板左右是 `book.css` 里的字面量 `6%`，`build_html.py` 无 diff。
- 拼合哈希是 `aacd30dcb0efbff80d004295338c9be99b35e19cb744d6f4b1e662a0b8f31baf`。
- `book` 与 `book-en` 都变绿之后，由人决定是否 squash。不打 tag，不创建 Release。

实施者自己不按合并按钮，不跑 `gh pr merge`。CI 还红时不合入。CI 变绿后由人 squash 合入。合入后在本机 `D:\Users\STM32` 拉取这次 `main`。

最终 diff 必须同时有七个令牌、16 处样式、测试哈希和版本戳。不要把仍锁着 `a4ccd140…` 的测试留成 PR 的最终内容。

这一步在验收已经通过时没有新的提交。

## 风险

这些都是设计规格里的风险。实施时按这里停，不要在密度 PR 里顺手改版式。

- **若 `.cover-panel` 继续写 `var(--inset)`，标题板左右会从 6% 收到 4.5%。** Task 3 必须把它写成字面量 `6%`。不要把这个字面量写进 `build_html.py`。
- **若把 `--space-bar` 收到 `0.5rem`，3px 强调条会贴住 `h2`。** 停在 `0.625rem`。
- **若把 `--leading-body` 收到 `1.6` 或更低，17px 中文的行框会开始挤。** 停在 `1.65`。印刷正文的 `1.55` 已经更紧，那是印刷规则，不要再改。
- **若把 `--measure` 收到 `38rem`，宽屏右侧空白会变多。** 若放到 `44rem`，全角会超过 40 字。停在 `42rem`。
- **若顺手把 `.part-divider` 的 `52vh` 或 `.cover` 的 `92vh` 改矮，就做成了海报刀。** 这两处保持。
- **若把暗色或印刷的 15 个颜色一起改，就离开了密度。** `dark` 和 `print` 的对象保持字节。
- **若重排 JSON，或把样式表里的 `.625rem` 写成 `0.625rem`，哈希会离开 Global Constraints 的表。** 按替换表的字符串做。JSON 用 `0.625rem`，样式表用 `.625rem`。
- **若哈希对不上仍去改测试期望，错误的样式会被锁住。** 先对照替换表。
- **窄于 720px 时，章块左右已是 `1rem`，inset 的变化在手机上看不见。** 垂直间距仍会收。视觉验收用宽于 960px 的窗口。
- **只改令牌、不改 `book.css` 时，拼合哈希是第三串，既不是基线也不是目标。** Task 2 失败是预期。不要在那一步改测试。

## 对照设计规格

| 设计规格里的要求 | 落在 |
| --- | --- |
| 采用做法 2：七个令牌再加 16 处阅读面字面量；封面标题板改成字面量 `6%` | Global Constraints，Task 2，Task 3 |
| `--space-chapter` `2.75rem`，`--space-figure` `1.25rem`，`--space-paragraph` `1rem`，`--space-bar` `0.625rem`，`--inset` `4.5%`，`--leading-body` `1.65`，`--measure` `42rem` | Task 2 |
| JSON 小数前写 0，样式表小数前不写 0；不重排 | Global Constraints，Task 2，Task 3 |
| `.cover-panel` 为 `padding: 1.8rem 6% 2.6rem`；窄屏 `1.3rem 1rem 1.8rem` 保持；720px 段不含 `var(--inset)` | Task 3 |
| 页脚改为 `padding: 2.25rem var(--inset) 3.5rem` | Task 3 |
| 章题、罗盘、配套、自测、callout、图、图注、表、目录、回目录、修订史导语按替换表 | Task 3 |
| `calc()` / `var()` 源文本保持；`scroll-margin-top: 1.25rem` 保持 | Task 1，Task 3 |
| `.cover` `92vh`、`.part-divider` `52vh` 和 `4.5rem` 保持 | Global Constraints，Task 3 |
| 字号、颜色、`coverLock`、画板三色、印刷 `9.5pt` / `1.55`、`@page` 毫米保持 | Global Constraints |
| 不改 `load_css()`、不升 `schema`、不加属性、不改 `build_html.py` | Global Constraints，File map，Task 3 Step 1 |
| 拼合哈希 `aacd30dcb0efbff80d004295338c9be99b35e19cb744d6f4b1e662a0b8f31baf` | Task 1，Task 3，Task 5 |
| `tokens.json` 哈希 `9d07dad4…`，`book.css` 哈希 `cc2656e9…`，`cover.svg` 哈希保持 `37dbedd7…` | Task 1，Task 2，Task 3 |
| 基线哈希变了就停，不在分叉上套这七个值 | 开工条件 |
| 测试不新开文件；点名的断言改新值；其余源文本保持 | Task 1 |
| 版本断言后移；1.2.7 的刀 C 两句改去 `entries[1]` | Task 4 |
| 建议版本 1.2.8 · 2026-10-25；高于 1.2.7 时写下一条修订号，日期用实施当天 | 开工条件，Task 4 |
| 修订四句；README 保留 1.2.6 到 1.2.7 的误标句，再加 1.2.7 到 1.2.8 | Task 4 |
| 中英 `--check` 与 unittest 通过后，`book` 与 `book-en` 变绿再由人 squash | Task 5 |
| 不改 workflow、不改正文、不改 `assets/`、不改 `cover.svg`、不打 tag、不创建 Release | Global Constraints，Task 5 |
| 书签 44、三档 `pageOverflow` 仍为 0、对比门槛 4.5 | Task 1，Task 5 |
| 宽于 960px 看第 00 章；英文看同一章 | Task 5 Step 3 |
| 设计 PR 不写实施计划；实施计划单独成 PR | 本文件。本计划 PR 只新增这一份 |

## 执行交接

本文件所在的 PR 只审阅计划，不实施密度。它不升版本，不改 `tokens.json`，不改 `book.css`，不改 `build_html.py`。CI 变绿不等于可以自动合入。

实施要等本计划合入 `main`，并且 `stm32-book/manifest.json` 的 `version` 仍是 `1.2.7`、`date` 仍是 `2026-10-25`（或按开工条件已经更高）。然后从那个 `main` 另开分支，按任务顺序做。两种走法：

1. Subagent-Driven：每个任务一个新的执行者，任务之间再审一遍 diff。
2. Inline：同一会话里用 executing-plans，做完一个任务再进下一个。

Task 1 的提交会使整套测试变红。Task 2 仍红，因为只改了令牌。Task 3 结束时测试应重新全绿，版本仍是 1.2.7。Task 4 把版本标成 1.2.8。实施 PR 要等到 Task 5 三条命令都退出码 0 再开。人在 `book` 与 `book-en` 都变绿后决定是否 squash 合入。不打 tag，不创建 Release。

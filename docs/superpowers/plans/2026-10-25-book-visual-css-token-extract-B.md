# 整书样式抽出 B Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

I'm using the writing-plans skill to create the implementation plan.

**Goal:** 把 1.2.4 的内联 `CSS` 抽成 `stm32-book/styles/tokens.json` 与 `stm32-book/styles/book.css`，import 时用 `load_css()` 填四个哨兵，拼回的 `builder.CSS` 与 1.2.4 逐字节相同，再把整书标成 **1.2.5 · 2026-10-25**。成品仍是单个 `<style>{CSS}</style>`。

**Architecture:** 令牌值只写在 JSON。选择器、五段 `@media`、封面画板色、展示字号、印刷 pt 和毫米留在 `book.css`，四处声明换成哨兵。`load_css()` 在 import 时把哨兵填回模块级 `CSS`。中文和英文 HTML 内嵌这一份字符串。不新增依赖，不拆第二份 CSS，不加 `<link>`。

**Tech Stack:** Python 3 标准库（`json`、`hashlib`、`pathlib`、`unittest`）、现有 `stm32-book/build_html.py`、`python3 stm32-book/tests/test_build.py`、`python3 -m unittest discover stm32-book/tests -v`。不改 `requirements.txt`，不引入 Sass、PostCSS 或 cssutils。

`stm32-book/tests/` 不是 Python 包。单条测试写成 `python3 stm32-book/tests/test_build.py BookBuildContractTests.<方法名> -v`。不要写成 `python3 -m unittest stm32-book.tests...`。整套测试仍用 `python3 -m unittest discover stm32-book/tests -v`。类名是 `BookBuildContractTests`。

设计规格：`docs/superpowers/specs/2026-10-25-book-visual-css-token-extract-B-design.md`（PR #39，`799cfae`）。

写本计划时的尖端是 `799cfaea14058a36560c060ebae3f2d836527dac`（`docs: 整书视觉刀 B 设计，抽出 CSS 与 token JSON (#39)`）。这一尖端的整书版本仍是 **1.2.4**，日期仍是 `2026-10-25`。`build_html.py` 的 `CSS = r"""` 在第 954 行，三引号在第 1236 行结束。原始字符串以换行开头、以 `}\n` 结尾，UTF-8 长度 21509，共 282 个换行。SHA-256 是 `e0fb660584f1833e8a6d419ba78ed9d56e4e92e51cbb533430ac8833bcca6bf4`。`<style>{CSS}</style>` 在第 1554 行。`json` 已在第 10 行导入。`ROOT` 在第 23 行。`BuildError` 在第 74 行。`validate_revisions()` 在第 818 行。这些行号属于 `799cfae`。实施时若行号被别的提交挪动，按 `CSS = r"""`、`<style>{CSS}</style>` 和函数名定位。

`799cfae` 只新增了设计规格。它下面的 `f537a94`（PR #38）才是刀 E 的实施。两处的 `CSS` 原始字符串是同一段字节。实施基线是本计划合入之后的 `main`，不是本计划的分支。本计划的 PR 只新增本文件，不改 `stm32-book/`，不新增 `styles/`，不升版本。

## Global Constraints

- 本计划 PR 不实施抽出。不新增 `stm32-book/styles/`，不改 `build_html.py` 的行为，不改两份 manifest、`revisions.json`、`stm32-book/README.md`。CI 变绿不等于本 PR 可以自动合入。等人审完计划再合。
- 实施时可以改的只有：`stm32-book/build_html.py`、`stm32-book/styles/tokens.json`、`stm32-book/styles/book.css`、`stm32-book/tests/test_build.py`、`stm32-book/revisions.json`、`stm32-book/manifest.json`、`stm32-book/manifest-en.json`、`stm32-book/README.md`。
- 目标版本是 **1.2.5 · 2026-10-25**。日期写死 `2026-10-25`。设计规格里「日期用实施当天」那一句，按本计划改成这个冻住的日期。两份 manifest、`revisions.json` 和 README 写同一个日期。
- 实施 PR 在 Book CI（`.github/workflows/book.yml`，名称 `Book CI`）的 `book` 与 `book-en` 都变绿之后 squash 合入 `main`。不改 workflow。不改正文，不设第二次章节 HTML 人审。
- 不打 tag，不创建 GitHub Release。合入后在本机 `D:\Users\STM32` 拉取这次 `main`。拉取不产生仓库 diff。
- 拼好的 `CSS` SHA-256 必须仍是 `e0fb660584f1833e8a6d419ba78ed9d56e4e92e51cbb533430ac8833bcca6bf4`。对不上时改哨兵空白或发射，不要改这个哈希，也不要改令牌的值来迁就格式。
- 模块级名字仍叫 `CSS`，类型仍是 `str`。赋值发生在 import 时：`CSS = load_css()`。不要改成函数，不要等 `build_html()` 才赋值。`load_css` 不接收 `language`。调用它不得改写模块级 `CSS`。
- HTML 模板保持 `<style>{CSS}</style>`。不加 `<link`。不按语言分两份样式。`dist/` 不复制 `styles/`，CI 上传路径不增加 CSS。
- 四个既有方法的函数体一个断言都不改：`test_visual_polish_css_contract`、`test_typography_e_css_contract`、`test_visual_polish_contrast_clears_4_5`、`test_code_glossary_and_print_css_keep_reading_units_movable`。`test_cover_svg_stays_self_contained` 里的 `--spine: #c4552a` 也不改。
- 不把封面画板 `#10242e`、`#0c1c24`、`#f4f1ea`，封面和分部页的 `clamp`，`.part-goal` 的 `1.12rem` / `1.6`，`.part-index` 的 `clamp(4.5rem, 14vw, 8.5rem)` 和窄屏 `3rem`，`.toc-jump` 的 `.85rem` 与 `box-shadow: 0 .45rem 1.2rem rgba(16, 24, 32, .18)`，`.compass-card` 的 `border-radius: .5rem`，行内代码的 `border-radius: .3em`，`color-mix` 的百分比，`figure img` 的 `.55rem`，印刷正文 `9.5pt`、图注 `9pt`、`@page` 的毫米，收进 JSON。`--table-columns` 仍是表格 HTML 的内联 style，不进令牌表。
- 亮色、暗色、印刷的颜色值与 1.2.4 相同。不改间距、圆角、阴影、字体栈、目录、代码块、图注。不加 `@font-face`，不写 `url(`，不引用 `fonts.googleapis` 或 `fonts.gstatic`。
- 五段 `@media` 的顺序保持：960、720、`(prefers-color-scheme: dark)`、`(prefers-reduced-motion: reduce)`、`print`。不要新增第六个媒体查询。
- 不改 `docs/00`–`28`、`docs/en/`、附录 Markdown、两份 `CONTENT_GUIDE.md`、罗盘文案、`revisions.json` 里已有句子、`cover.svg`、仓库根 `assets/`、`tools/`、`CREDITS.md`、`.github/workflows/book.yml`。不实施刀 D、刀 C。
- 不改 `toc_html`、分类函数、罗盘 HTML、书签、章号。出版书签仍是 44 条。不删 `0x271`、`167 ns`、样本章和各批加厚的断言。`pageOverflow` 为 0 的三档不放宽。
- 修订说明只用设计里的四句。不写刀 D、刀 C，也不写章节名。已有修订句子一字不改。
- 路径固定为 `stm32-book/styles/`。不放进仓库根 `assets/`，也不建 `stm32-book/assets/`。

上一句「Book CI 变绿后 squash 合入」指刀 B 的实施 PR。本计划文件的 PR 等人审阅，不在 CI 变绿后自动合入，也不在本 PR 里改 `stm32-book/`。

## 开工条件

实施开始时先读实施分支所基于的 `main` 上的 `stm32-book/manifest.json`，只看 `version` 和 `date`。不要在本计划的分支上改 CSS 或版本。

- `version` 低于 `1.2.4`：停。刀 E 还没在这条历史上。不开实施分支。
- `version` 是 `1.2.4`：实施版写成 `1.2.5`，日期写成 `2026-10-25`。下面任务里的字面量按这个走。这是预期路径。`799cfae` 就是这个状态。
- `version` 已经高于 `1.2.4`（仍是 `1.2.x`，且补丁号大于 4）：实施版写成下一条修订号。不把 `1.2.5` 硬套上去。日期仍是 `2026-10-25`。Task 3 里每一处 `1.2.5` 换成这个新号，每一处当作「上一版」的 `1.2.4` 换成当时 manifest 的 `version`。修订四句不变，只把中文第一句和英文第一句末尾的 `1.2.4` 改成当时的上一版。已有修订句子保持原文，只把索引后移一位。

接着核对三引号之间的原始字符串。SHA-256 必须是 `e0fb660584f1833e8a6d419ba78ed9d56e4e92e51cbb533430ac8833bcca6bf4`。不是这个值就停。不要改哈希常量，也不要改令牌值去凑一个新字节串。

`validate_revisions()` 要求 `revisions.json` 第一条的 `version` 等于 manifest 的 `version`。Task 3 必须同一提交改测试、两份 manifest、`revisions.json` 和 README。

## File map

| 路径 | 责任 |
| --- | --- |
| `docs/superpowers/plans/2026-10-25-book-visual-css-token-extract-B.md` | 本计划。本 PR 只新增这一份 |
| `stm32-book/tests/test_build.py` | Task 1 新增两个抽出测试。Task 3 只改版本断言。四个既有视觉方法不改 |
| `stm32-book/styles/tokens.json` | Task 2 新建。40 个亮色键、15 个暗色键、15 个印刷键、6 个 `coverLock`。UTF-8 无 BOM，两个空格缩进，文件末尾一个换行 |
| `stm32-book/styles/book.css` | Task 2 新建。1.2.4 的原始字符串只替换四处哨兵。第一个字节仍是换行 |
| `stm32-book/build_html.py` | Task 2 删掉三引号 `CSS`，改为 `CSS = load_css()`。`<style>{CSS}</style>` 不改 |
| `stm32-book/manifest.json` | Task 3：`version` 改为 `1.2.5`，`date` 保持 `2026-10-25` |
| `stm32-book/manifest-en.json` | 同上 |
| `stm32-book/revisions.json` | Task 3：`entries` 最前插入 1.2.5。已有条目一字不改 |
| `stm32-book/README.md` | Task 3：当前版本句、构建节一句、发布节的版本句、tag 名，以及「也不要把 1.2.4 的产物标成 1.2.5」 |

---

### Task 1: 先写下会失败的抽出契约

**Files:**
- Modify: `stm32-book/tests/test_build.py`（补 `hashlib` 与 `inspect`；在 `class BookBuildContractTests` 之前加上三个常量；在 `test_typography_e_css_contract` 之后、`test_visual_polish_version_is_1_2_0` 之前插入两个方法）
- Test: `stm32-book/tests/test_build.py`

**Interfaces:**
- Consumes: 已有的 `BookBuildContractTests._css_rule`、`self.builder.CSS`、`BOOK_DIR`。屏幕段是第一个 `@media` 之前，暗色段是暗色查询到下一个 `@media`，印刷段是 `@media print` 之后。这一任务还不存在 `load_css`。
- Produces: `BookBuildContractTests.test_css_token_extract_contract` 与 `BookBuildContractTests.test_css_token_extract_rejects_bad_tokens`。后面的任务按这两个名字跑。这一任务不改版本断言，不改 `build_html.py`，不创建 `styles/`。

这一提交之后，整套 `discover` 会失败。这是预期。不要开实施 PR，不要 squash。抽出契约要到 Task 2 才绿。四个既有视觉方法现在就应该仍绿，因为 `CSS` 字符串还没动。

键序按 1.2.4 的声明序，也就是设计规格里那份 JSON 的键序。`--radius` 和 `--elev` 在 `--font-sans` 之前。不要按设计正文里「排版」分组标题把圆角挪到字体后面。

- [ ] **Step 1: 写入常量、导入和两个测试**

把文件顶部的导入改成：

```python
import copy
import hashlib
import importlib.util
import inspect
import json
import re
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path
```

在 `class BookBuildContractTests` 之前插入：

```python
_TOKEN_LIGHT_KEYS = (
    "--paper",
    "--ink",
    "--muted",
    "--line",
    "--panel",
    "--accent",
    "--accent-soft",
    "--warn",
    "--warn-soft",
    "--tip",
    "--tip-soft",
    "--spine",
    "--spine-soft",
    "--code",
    "--code-ink",
    "--measure",
    "--space-bar",
    "--space-paragraph",
    "--space-figure",
    "--space-chapter",
    "--inset",
    "--leading-body",
    "--tracking-body",
    "--tracking-kicker",
    "--radius",
    "--elev",
    "--font-sans",
    "--font-mono",
    "--type-body",
    "--type-h1",
    "--type-h2",
    "--type-h3",
    "--type-h4",
    "--type-kicker",
    "--type-small",
    "--type-code",
    "--leading-heading",
    "--leading-caption",
    "--leading-toc",
    "--leading-code",
)
_TOKEN_COLOR_KEYS = _TOKEN_LIGHT_KEYS[:15]
_TOKEN_COVER_LOCK = ("--paper", "--ink", "--muted", "--warn", "--line", "--spine")
```

在 `def test_visual_polish_version_is_1_2_0` 之前插入：

```python
    def test_css_token_extract_contract(self) -> None:
        tokens_path = BOOK_DIR / "styles" / "tokens.json"
        css_path = BOOK_DIR / "styles" / "book.css"
        self.assertTrue(tokens_path.is_file(), tokens_path)
        self.assertTrue(css_path.is_file(), css_path)
        raw_tokens = tokens_path.read_bytes()
        self.assertFalse(raw_tokens.startswith(b"\xef\xbb\xbf"), "tokens.json BOM")
        token_text = raw_tokens.decode("utf-8")
        self.assertTrue(token_text.endswith("\n"))
        tokens = json.loads(token_text)
        self.assertEqual(
            ["schema", "light", "dark", "print", "coverLock"],
            list(tokens),
        )
        self.assertIs(type(tokens["schema"]), int)
        self.assertEqual(1, tokens["schema"])
        self.assertEqual(list(_TOKEN_LIGHT_KEYS), list(tokens["light"]))
        self.assertEqual(list(_TOKEN_COLOR_KEYS), list(tokens["dark"]))
        self.assertEqual(list(_TOKEN_COLOR_KEYS), list(tokens["print"]))
        self.assertEqual(list(_TOKEN_COVER_LOCK), tokens["coverLock"])

        css_source = css_path.read_text(encoding="utf-8")
        self.assertTrue(css_source.startswith("\n"))
        for sentinel in (
            "  /* @tokens light */",
            "  /* @tokens dark */",
            "/* @tokens print */",
            "  /* @tokens cover */",
        ):
            self.assertEqual(1, css_source.count(sentinel), sentinel)
        self.assertIn(
            "  color-scheme: light dark;\n  /* @tokens light */\n  font-family: var(--font-sans);",
            css_source,
        )
        self.assertIn(
            "@media (prefers-color-scheme: dark) {\n  /* @tokens dark */\n}",
            css_source,
        )
        self.assertIn(
            "  :root { color-scheme: light; /* @tokens print */ }",
            css_source,
        )
        self.assertIn(
            "  background: #10242e;\n  color: #f4f1ea;\n  /* @tokens cover */\n",
            css_source,
        )
        names = set(tokens["light"]) | set(tokens["dark"]) | set(tokens["print"])
        for name in names:
            self.assertNotIn(f"{name}:", css_source, name)
        self.assertEqual(
            {"#10242e", "#f4f1ea", "#0c1c24"},
            set(re.findall(r"#[0-9A-Fa-f]{3,8}", css_source)),
        )
        self.assertIn("rgba(16, 24, 32, .18)", css_source)
        self.assertIn("--table-columns", css_source)
        self.assertNotIn("@font-face", css_source)
        self.assertNotIn("url(", css_source)

        self.assertEqual(
            ("tokens_path", "css_path"),
            tuple(inspect.signature(self.builder.load_css).parameters),
        )
        self.assertIsInstance(self.builder.CSS, str)
        self.assertEqual(self.builder.load_css(), self.builder.CSS)
        self.assertEqual(
            "e0fb660584f1833e8a6d419ba78ed9d56e4e92e51cbb533430ac8833bcca6bf4",
            hashlib.sha256(self.builder.CSS.encode("utf-8")).hexdigest(),
        )
        css = self.builder.CSS
        self.assertNotIn("/* @tokens", css)
        medias = [item.strip() for item in re.findall(r"@media[^{]+", css)]
        self.assertEqual(
            [
                "@media (max-width: 960px)",
                "@media (max-width: 720px)",
                "@media (prefers-color-scheme: dark)",
                "@media (prefers-reduced-motion: reduce)",
                "@media print",
            ],
            medias,
        )
        screen = css.split("@media", 1)[0]
        dark = css.split("@media (prefers-color-scheme: dark)", 1)[1].split("@media", 1)[0]
        printed = css.split("@media print", 1)[1]
        for name, value in tokens["light"].items():
            self.assertIn(f"{name}: {value}", screen, name)
        for name, value in tokens["dark"].items():
            self.assertIn(f"{name}: {value}", dark, name)
        print_root = self._css_rule(printed, ":root")
        for name, value in tokens["print"].items():
            self.assertIn(f"{name}: {value}", print_root, name)
        cover = self._css_rule(screen, ".cover")
        for name in tokens["coverLock"]:
            self.assertIn(f"{name}: {tokens['light'][name]}", cover, name)

        def embedded(html: str) -> None:
            self.assertEqual(1, html.count("<style>"))
            self.assertEqual(1, html.count("</style>"))
            self.assertNotIn("<link", html)
            inner = html.split("<style>", 1)[1].split("</style>", 1)[0]
            self.assertEqual(self.builder.CSS, inner)
            self.assertNotIn("fonts.googleapis", html)
            self.assertNotIn("fonts.gstatic", html)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            chinese = self.builder.build_html(root / "zh")
            english = self.builder.build_html(root / "en", BOOK_DIR / "manifest-en.json")
            embedded(chinese.read_text(encoding="utf-8"))
            embedded(english.read_text(encoding="utf-8"))

    def test_css_token_extract_rejects_bad_tokens(self) -> None:
        before = self.builder.CSS

        def legal() -> dict:
            light = {key: "1" for key in _TOKEN_LIGHT_KEYS}
            colors = {key: "1" for key in _TOKEN_COLOR_KEYS}
            return {
                "schema": 1,
                "light": light,
                "dark": dict(colors),
                "print": dict(colors),
                "coverLock": list(_TOKEN_COVER_LOCK),
            }

        sheet = (
            "\n:root {\n"
            "  color-scheme: light dark;\n"
            "  /* @tokens light */\n"
            "  font-family: var(--font-sans);\n"
            "}\n"
            ".cover {\n"
            "  background: #10242e;\n"
            "  color: #f4f1ea;\n"
            "  /* @tokens cover */\n"
            "}\n"
            "@media (prefers-color-scheme: dark) {\n"
            "  /* @tokens dark */\n"
            "}\n"
            "@media print {\n"
            "  :root { color-scheme: light; /* @tokens print */ }\n"
            "}\n"
        )

        def write_pair(directory: Path, document: str) -> tuple[Path, Path]:
            directory.mkdir(parents=True, exist_ok=True)
            tokens_path = directory / "tokens.json"
            css_path = directory / "book.css"
            tokens_path.write_text(document, encoding="utf-8", newline="\n")
            css_path.write_text(sheet, encoding="utf-8", newline="\n")
            return tokens_path, css_path

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing = legal()
            del missing["light"]["--ink"]
            tokens_path, css_path = write_pair(
                root / "missing",
                json.dumps(missing, indent=2, ensure_ascii=False) + "\n",
            )
            with self.assertRaisesRegex(self.builder.BuildError, "--ink"):
                self.builder.load_css(tokens_path, css_path)

            poisoned = legal()
            poisoned["light"]["--paper"] = "url("
            tokens_path, css_path = write_pair(
                root / "url",
                json.dumps(poisoned, indent=2, ensure_ascii=False) + "\n",
            )
            with self.assertRaisesRegex(self.builder.BuildError, r"url\("):
                self.builder.load_css(tokens_path, css_path)

            duplicate = json.dumps(legal(), indent=2, ensure_ascii=False) + "\n"
            duplicate = duplicate.replace(
                '"--paper": "1"',
                '"--paper": "1",\n    "--paper": "#fff"',
                1,
            )
            light_text, _, _rest = duplicate.partition('\n  "dark"')
            self.assertEqual(2, light_text.count('"--paper"'))
            tokens_path, css_path = write_pair(root / "duplicate", duplicate)
            with self.assertRaisesRegex(self.builder.BuildError, "--paper"):
                self.builder.load_css(tokens_path, css_path)

        self.assertIs(before, self.builder.CSS)
```

不要改 `test_visual_polish_css_contract`、`test_typography_e_css_contract`、`test_visual_polish_contrast_clears_4_5`、`test_code_glossary_and_print_css_keep_reading_units_movable` 的函数体。不要改版本断言。

- [ ] **Step 2: 跑新测试，确认失败**

Run:

```bash
python3 stm32-book/tests/test_build.py BookBuildContractTests.test_css_token_extract_contract -v
```

Expected: 退出码 1。失败信息含 `tokens.json` 不存在，或 `styles` 不是文件。不要去创建这个文件来让它变绿。那是 Task 2。

Run:

```bash
python3 stm32-book/tests/test_build.py BookBuildContractTests.test_css_token_extract_rejects_bad_tokens -v
```

Expected: 退出码 1。失败信息含 `load_css`。`AttributeError` 是预期。

这个入口一次只跑一个测试名。两条分开跑：

```bash
python3 stm32-book/tests/test_build.py BookBuildContractTests.test_visual_polish_css_contract -v
python3 stm32-book/tests/test_build.py BookBuildContractTests.test_typography_e_css_contract -v
```

Expected: 两条都通过。`CSS` 字符串还没动。

- [ ] **Step 3: 提交失败的测试**

```bash
git add stm32-book/tests/test_build.py
git commit -m "book: 为样式抽出写下会失败的契约"
```

这一步的 diff 只能落在 `stm32-book/tests/test_build.py`。不要加 `styles/`，不要改 `build_html.py`。

---

### Task 2: 写出令牌、哨兵和 `load_css()`

**Files:**
- Create: `stm32-book/styles/tokens.json`
- Create: `stm32-book/styles/book.css`
- Modify: `stm32-book/build_html.py`（`MANIFEST_PATH` 下面加两个路径；用 `load_css` 换掉第 954–1236 行的三引号字符串；第 1554 行的 `<style>{CSS}</style>` 不动）
- Test: `BookBuildContractTests.test_css_token_extract_contract`、`test_css_token_extract_rejects_bad_tokens`

**Interfaces:**
- Consumes: Task 1 的两个测试、`_TOKEN_LIGHT_KEYS` 的键序、开工条件里的 SHA-256。三引号原始字符串此时还在。
- Produces: 模块级 `CSS: str`，由 `load_css(tokens_path: Path = TOKENS_PATH, css_path: Path = BOOK_CSS_PATH) -> str` 在 import 时填出。`TOKENS_PATH` 是 `ROOT / "styles" / "tokens.json"`。`BOOK_CSS_PATH` 是 `ROOT / "styles" / "book.css"`。函数没有 `language` 参数，函数体内没有 `global`。

这一步不改版本文件，不改 Task 1 的测试。四个既有视觉方法的函数体仍然不动。

哈希对不上时，只改哨兵周围的空白或下面的发射格式。不要重排 `book.css` 的其他字节，不要把哈希改成新值，不要改 JSON 里的颜色或字号。

- [ ] **Step 1: 写入 `tokens.json`**

新建 `stm32-book/styles/tokens.json`。内容就是下面这份，UTF-8，无 BOM，两个空格缩进，`coverLock` 保持这一行。写入后再补一个文件末尾换行。不要 `sort_keys`，不要用 `json.dumps` 重排。加载只看解析后的对象，但键序就是发射顺序，所以这一份的顺序不能改。

`--radius` 和 `--elev` 在 `--font-sans` 前面。这是 1.2.4 声明序。设计正文里的分组标题不是键序。

```json
{
  "schema": 1,
  "light": {
    "--paper": "#fbfaf7",
    "--ink": "#17202a",
    "--muted": "#5e6872",
    "--line": "#d7dce1",
    "--panel": "#f1f5f7",
    "--accent": "#075e84",
    "--accent-soft": "#e5f3f8",
    "--warn": "#9a3d1c",
    "--warn-soft": "#f8efe8",
    "--tip": "#1b5c45",
    "--tip-soft": "#e7f4ee",
    "--spine": "#c4552a",
    "--spine-soft": "#f8efe8",
    "--code": "#101820",
    "--code-ink": "#eef6f8",
    "--measure": "40rem",
    "--space-bar": "0.75rem",
    "--space-paragraph": "1.25rem",
    "--space-figure": "1.5rem",
    "--space-chapter": "3.5rem",
    "--inset": "6%",
    "--leading-body": "1.75",
    "--tracking-body": "0.01em",
    "--tracking-kicker": "0.14em",
    "--radius": "0.7rem",
    "--elev": "0 1px 2px color-mix(in srgb, var(--ink) 8%, transparent)",
    "--font-sans": "\"Noto Sans CJK SC\", \"Microsoft YaHei\", \"PingFang SC\", \"Noto Sans SC\", \"Source Han Sans SC\", \"Segoe UI\", system-ui, sans-serif",
    "--font-mono": "\"Cascadia Mono\", \"SFMono-Regular\", Consolas, \"Noto Sans Mono CJK SC\", \"Source Han Mono SC\", \"Sarasa Mono SC\", \"Liberation Mono\", ui-monospace, monospace",
    "--type-body": "1.0625rem",
    "--type-h1": "clamp(1.85rem, 4.2vw, 2.7rem)",
    "--type-h2": "1.55rem",
    "--type-h3": "1.35rem",
    "--type-h4": "1.2rem",
    "--type-kicker": "0.78rem",
    "--type-small": "0.9375rem",
    "--type-code": "0.92em",
    "--leading-heading": "1.35",
    "--leading-caption": "1.55",
    "--leading-toc": "1.45",
    "--leading-code": "1.65"
  },
  "dark": {
    "--paper": "#11171b",
    "--ink": "#e9eef1",
    "--muted": "#acb7bf",
    "--line": "#3a454d",
    "--panel": "#1c252b",
    "--accent": "#78c8e8",
    "--accent-soft": "#17313c",
    "--warn": "#f0b090",
    "--warn-soft": "#3a241c",
    "--tip": "#8fd4b4",
    "--tip-soft": "#163028",
    "--spine": "#f0b090",
    "--spine-soft": "#3a241c",
    "--code": "#0a141c",
    "--code-ink": "#edf6f9"
  },
  "print": {
    "--paper": "#fff",
    "--ink": "#111",
    "--muted": "#444",
    "--line": "#bbb",
    "--panel": "#f4f4f4",
    "--accent": "#075e84",
    "--accent-soft": "#edf6f9",
    "--warn": "#8a3418",
    "--warn-soft": "#f8f1ec",
    "--tip": "#1b5c45",
    "--tip-soft": "#eef6f2",
    "--spine": "#c4552a",
    "--spine-soft": "#f8efe8",
    "--code": "#f6f6f6",
    "--code-ink": "#111"
  },
  "coverLock": ["--paper", "--ink", "--muted", "--warn", "--line", "--spine"]
}
```

- [ ] **Step 2: 从仍在的三引号字符串做出 `book.css`，并先证明能拼回去**

三引号还在的时候，在仓库根运行下面这段。它不改 `build_html.py`，不留下脚本文件。它只写 `stm32-book/styles/book.css`。

替换规则只有四次，其他字节不动：

1. 亮色 `:root` 里从 `  --paper: #fbfaf7;` 到 `  --leading-code: 1.65;` 的连续 40 行，换成一行 `  /* @tokens light */`。`color-scheme: light dark;` 和后面的 `font-family: var(--font-sans);` 不动。
2. 暗色媒体查询里的那一整行 `  :root { --paper: #11171b; ... --code-ink: #edf6f9; }`，换成一行 `  /* @tokens dark */`。外层 `@media (prefers-color-scheme: dark)` 不动。
3. 印刷 `:root` 那一行里，从 `--paper: #fff;` 到 `--code-ink: #111;` 的属性串，换成 `/* @tokens print */`。`color-scheme: light; ` 保留，分号后面的那个空格也保留。这一行变成 `  :root { color-scheme: light; /* @tokens print */ }`。
4. `.cover` 规则里那 6 行自定义属性，换成一行 `  /* @tokens cover */`。`background: #10242e;` 和 `color: #f4f1ea;` 留在哨兵前面。

```bash
python3 - << 'PY'
import hashlib
import json
from pathlib import Path

expect = "e0fb660584f1833e8a6d419ba78ed9d56e4e92e51cbb533430ac8833bcca6bf4"
source_path = Path("stm32-book/build_html.py")
source = source_path.read_text(encoding="utf-8")
marker = 'CSS = r"""'
start = source.find(marker)
if start < 0:
    raise SystemExit("CSS triple quote missing; refuse to invent book.css")
body_at = start + len(marker)
end = source.find('"""', body_at)
if end < 0:
    raise SystemExit("CSS triple quote has no end")
raw = source[body_at:end]
got = hashlib.sha256(raw.encode("utf-8")).hexdigest()
if got != expect:
    raise SystemExit(f"baseline CSS drifted: {got}")

tokens = json.loads(Path("stm32-book/styles/tokens.json").read_text(encoding="utf-8"))

def lines(pairs) -> str:
    return "\n".join(f"  {name}: {value};" for name, value in pairs)

def inline(pairs) -> str:
    return " ".join(f"{name}: {value};" for name, value in pairs)

light = lines(tokens["light"].items())
dark = f"  :root {{ {inline(tokens['dark'].items())} }}"
printed = inline(tokens["print"].items())
cover = lines((name, tokens["light"][name]) for name in tokens["coverLock"])
swaps = (
    (light, "  /* @tokens light */"),
    (dark, "  /* @tokens dark */"),
    (printed, "/* @tokens print */"),
    (cover, "  /* @tokens cover */"),
)
book = raw
for block, sentinel in swaps:
    count = book.count(block)
    if count != 1:
        raise SystemExit(f"block for {sentinel!r} count {count}")
    book = book.replace(block, sentinel, 1)

css_path = Path("stm32-book/styles/book.css")
css_path.write_text(book, encoding="utf-8", newline="\n")
css = css_path.read_text(encoding="utf-8")
if css != book:
    raise SystemExit("book.css round-trip changed newlines")
if not css.startswith("\n"):
    raise SystemExit("book.css must start with a newline")

filled = css
for block, sentinel in swaps:
    count = filled.count(sentinel)
    if count != 1:
        raise SystemExit(f"sentinel {sentinel!r} count {count}")
    filled = filled.replace(sentinel, block, 1)
if filled != raw:
    raise SystemExit("sentinel fill is not byte-identical to the 1.2.4 string")
if hashlib.sha256(filled.encode("utf-8")).hexdigest() != expect:
    raise SystemExit("filled hash drifted")
for name in tokens["light"]:
    if f"{name}:" in css:
        raise SystemExit(f"book.css still declares {name}")
print("roundtrip ok", expect)
PY
```

Expected: 打印 `roundtrip ok e0fb660584f1833e8a6d419ba78ed9d56e4e92e51cbb533430ac8833bcca6bf4`，退出码 0。

退出码不是 0 时停。不要改 `build_html.py`，不要改哈希，不要改 JSON 的值。先看是哪一个 `count` 不是 1。暗色那一行和印刷那一串必须整段命中，不能先 `strip()`。

- [ ] **Step 3: 用 `load_css()` 换掉三引号**

在 `MANIFEST_PATH = ROOT / "manifest.json"` 下一行插入：

```python
TOKENS_PATH = ROOT / "styles" / "tokens.json"
BOOK_CSS_PATH = ROOT / "styles" / "book.css"
```

删掉从 `CSS = r"""` 到该字符串结束 `"""` 的整段。在同一位置放上下面的代码。`re`、`json`、`Path`、`BuildError` 都已经在文件里。不要新增 import。不要在 `load_css` 里写 `global`。不要 `sort_keys`。不要 `strip()`。读文件用 `encoding="utf-8"`，不要 `utf-8-sig`。换行只用 `\n`。替换哨兵时不要吃掉哨兵后面的换行，发射结果的末尾也不要再加换行。

键序常量必须与 Task 1 的 `_TOKEN_LIGHT_KEYS` 相同。校验先看 `light`，再看 `dark` 和 `print`，这样缺少 `--ink` 的消息里是 `--ink`，而不是暗色组的别的键。

```python
_CSS_LIGHT_KEYS = (
    "--paper",
    "--ink",
    "--muted",
    "--line",
    "--panel",
    "--accent",
    "--accent-soft",
    "--warn",
    "--warn-soft",
    "--tip",
    "--tip-soft",
    "--spine",
    "--spine-soft",
    "--code",
    "--code-ink",
    "--measure",
    "--space-bar",
    "--space-paragraph",
    "--space-figure",
    "--space-chapter",
    "--inset",
    "--leading-body",
    "--tracking-body",
    "--tracking-kicker",
    "--radius",
    "--elev",
    "--font-sans",
    "--font-mono",
    "--type-body",
    "--type-h1",
    "--type-h2",
    "--type-h3",
    "--type-h4",
    "--type-kicker",
    "--type-small",
    "--type-code",
    "--leading-heading",
    "--leading-caption",
    "--leading-toc",
    "--leading-code",
)
_CSS_COLOR_KEYS = _CSS_LIGHT_KEYS[:15]
_CSS_COVER_LOCK = ("--paper", "--ink", "--muted", "--warn", "--line", "--spine")
_TOKEN_NAME = re.compile(r"^--[a-z0-9-]+$")
_FORBIDDEN_VALUE = ("\n", "\r", ";", "{", "}", "url(", "@import", "@font-face", "!important")


def _token_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    found: dict[str, object] = {}
    for key, value in pairs:
        if key in found:
            raise BuildError(f"duplicate token key {key}")
        found[key] = value
    return found


def _read_token_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise BuildError(f"missing token file: {path}") from exc


def _read_css_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise BuildError(f"missing stylesheet: {path}") from exc


def _require_keys(section: str, actual: dict, expected: tuple[str, ...]) -> None:
    actual_keys = tuple(actual)
    if actual_keys == expected:
        return
    missing = [key for key in expected if key not in actual]
    if missing:
        raise BuildError(f"token {section} missing {missing[0]}")
    extra = [key for key in actual_keys if key not in expected]
    if extra:
        raise BuildError(f"token {section} has extra {extra[0]}")
    for want, got in zip(expected, actual_keys):
        if want != got:
            raise BuildError(f"token {section} key order {got}")


def _require_value(key: str, value: object) -> None:
    if not isinstance(value, str) or not 1 <= len(value) <= 500:
        raise BuildError(f"token {key} value")
    for forbidden in _FORBIDDEN_VALUE:
        if forbidden in value:
            raise BuildError(f"token {key} contains {forbidden}")


def _section(tokens: dict, name: str) -> dict:
    value = tokens[name]
    if not isinstance(value, dict):
        raise BuildError(f"token {name} is not an object")
    for key in value:
        if not isinstance(key, str) or _TOKEN_NAME.fullmatch(key) is None:
            raise BuildError(f"token name {key}")
    return value


def _declaration_lines(pairs: list[tuple[str, str]]) -> str:
    return "\n".join(f"  {name}: {value};" for name, value in pairs)


def _declaration_inline(pairs: list[tuple[str, str]]) -> str:
    return " ".join(f"{name}: {value};" for name, value in pairs)


def load_css(tokens_path: Path = TOKENS_PATH, css_path: Path = BOOK_CSS_PATH) -> str:
    try:
        tokens = json.loads(_read_token_text(tokens_path), object_pairs_hook=_token_object)
    except BuildError:
        raise
    except json.JSONDecodeError as exc:
        raise BuildError(f"invalid token JSON: {tokens_path}: {exc.msg}") from exc
    if not isinstance(tokens, dict):
        raise BuildError(f"invalid token JSON: {tokens_path}")
    if tuple(tokens) != ("schema", "light", "dark", "print", "coverLock"):
        raise BuildError(f"token file keys {tuple(tokens)!r} in {tokens_path}")
    schema = tokens["schema"]
    if type(schema) is not int or schema != 1:
        raise BuildError(f"token schema {schema!r}")
    light = _section(tokens, "light")
    dark = _section(tokens, "dark")
    printed = _section(tokens, "print")
    _require_keys("light", light, _CSS_LIGHT_KEYS)
    _require_keys("dark", dark, _CSS_COLOR_KEYS)
    _require_keys("print", printed, _CSS_COLOR_KEYS)
    for group in (light, dark, printed):
        for key, value in group.items():
            _require_value(key, value)
    cover_lock = tokens["coverLock"]
    if cover_lock != list(_CSS_COVER_LOCK):
        raise BuildError(f"token coverLock {cover_lock!r}")
    css = _read_css_text(css_path)
    replacements = (
        ("  /* @tokens light */", _declaration_lines(list(light.items()))),
        ("  /* @tokens dark */", f"  :root {{ {_declaration_inline(list(dark.items()))} }}"),
        ("/* @tokens print */", _declaration_inline(list(printed.items()))),
        (
            "  /* @tokens cover */",
            _declaration_lines([(name, light[name]) for name in cover_lock]),
        ),
    )
    for sentinel, value in replacements:
        count = css.count(sentinel)
        if count != 1:
            raise BuildError(f"token sentinel {sentinel.strip()} count {count}")
        css = css.replace(sentinel, value, 1)
    return css


CSS = load_css()
```

`<style>{CSS}</style>` 那一行保持原样。不要加 `<link`。不要给 `load_css` 加 `language`。不要在赋值外面套 `try`。文件缺了或 JSON 坏了，import 就失败，`--check` 和单元测试一起失败。

- [ ] **Step 4: 跑抽出契约和既有视觉契约**

Run:

```bash
python3 stm32-book/tests/test_build.py BookBuildContractTests.test_css_token_extract_contract -v
python3 stm32-book/tests/test_build.py BookBuildContractTests.test_css_token_extract_rejects_bad_tokens -v
python3 stm32-book/tests/test_build.py BookBuildContractTests.test_visual_polish_css_contract -v
python3 stm32-book/tests/test_build.py BookBuildContractTests.test_typography_e_css_contract -v
python3 stm32-book/tests/test_build.py BookBuildContractTests.test_visual_polish_contrast_clears_4_5 -v
python3 stm32-book/tests/test_build.py BookBuildContractTests.test_code_glossary_and_print_css_keep_reading_units_movable -v
python3 stm32-book/tests/test_build.py BookBuildContractTests.test_cover_svg_stays_self_contained -v
```

Expected: 七条都通过。哈希断言通过。拒绝用例通过，并且模块级 `CSS` 的对象身份没变。

然后：

```bash
python3 -m unittest discover stm32-book/tests -v
python3 stm32-book/build_html.py --check
python3 stm32-book/build_html.py --lang en --check
```

Expected: 三条退出码都是 0。此时版本仍是 1.2.4。`discover` 在这一步就应该全绿，因为版本断言还没改。不要在这一步改 manifest。

- [ ] **Step 5: 确认没有外部样式表，然后提交抽出**

Run:

```bash
grep -n 'CSS = r"""' stm32-book/build_html.py || true
grep -n '<style>{CSS}</style>' stm32-book/build_html.py
grep -n '<link' stm32-book/build_html.py || true
```

Expected: 第一行没有匹配。第二行恰好一处。第三行没有匹配。

```bash
git add stm32-book/styles/tokens.json stm32-book/styles/book.css stm32-book/build_html.py
git commit -m "book: 把内联 CSS 抽到 tokens.json 与 book.css"
```

不要把一次性脚本留在仓库里。不要提交 `dist/`。这一步的 diff 不包含 manifest、`revisions.json` 或 README。

---

### Task 3: 把整书标成 1.2.5

**Files:**
- Modify: `stm32-book/tests/test_build.py` 里仍写着 1.2.4 的当前版本断言
- Modify: `stm32-book/manifest.json` 的 `version`
- Modify: `stm32-book/manifest-en.json` 的 `version`
- Modify: `stm32-book/revisions.json` 的 `entries[0]`
- Modify: `stm32-book/README.md` 的当前版本句、构建节、发布节版本句、误标句、tag 名
- Test: `BookBuildContractTests.test_visual_polish_version_is_1_2_0`、`test_revision_file_lists_1_0_0_through_manifest_version`、`assert_version_history_and_index`、`test_build_produces_one_complete_offline_book`、`test_english_book_is_a_separate_offline_edition`

**Interfaces:**
- Consumes: 开工条件定下的版本号。预期路径是上一版 `1.2.4`、新版 `1.2.5`、日期 `2026-10-25`。
- Produces: 两份 manifest 的 `version` 都是 `1.2.5`，`date` 都是 `2026-10-25`。`revisions.json` 的 `entries[0].version` 是 `1.2.5`。`entries[1]` 仍是刀 E 的 1.2.4 句子，`entries[2]` 仍是 1.2.3，`entries[3]` 仍是 1.2.2，`entries[4]` 仍是 1.2.1，`entries[5]` 仍是 1.2.0。

方法名保持 `test_visual_polish_version_is_1_2_0`。不要改名。

若实施时的上一版已经不是 1.2.4，按开工条件替换字面量。已有修订句子以当时 `main` 上的原文为准，只后移索引，不要改写成下面的文本。下面的句子是 `799cfae` 上的原文。

- [ ] **Step 1: 把版本断言改到 1.2.5，先不要改版本文件**

`assert_version_history_and_index` 里，把

```python
        versions = ("1.2.4", "1.2.3", "1.2.2", "1.2.1", "1.2.0", "1.1.1", "1.1.0", "1.0.8", "1.0.7", "1.0.6", "1.0.5", "1.0.4", "1.0.3", "1.0.2", "1.0.1", "1.0.0")
        for version in versions:
            self.assertIn(f">{version}<", history)
        self.assertLess(history.index(">1.2.4<"), history.index(">1.2.3<"))
```

改成

```python
        versions = ("1.2.5", "1.2.4", "1.2.3", "1.2.2", "1.2.1", "1.2.0", "1.1.1", "1.1.0", "1.0.8", "1.0.7", "1.0.6", "1.0.5", "1.0.4", "1.0.3", "1.0.2", "1.0.1", "1.0.0")
        for version in versions:
            self.assertIn(f">{version}<", history)
        self.assertLess(history.index(">1.2.5<"), history.index(">1.2.4<"))
        self.assertLess(history.index(">1.2.4<"), history.index(">1.2.3<"))
```

其后的 `assertLess` 保持不动。

`test_revision_file_lists_1_0_0_through_manifest_version` 里的列表改成以 `"1.2.5"` 起头，下一项仍是 `"1.2.4"`：

```python
            ["1.2.5", "1.2.4", "1.2.3", "1.2.2", "1.2.1", "1.2.0", "1.1.1", "1.1.0", "1.0.8", "1.0.7", "1.0.6", "1.0.5", "1.0.4", "1.0.3", "1.0.2", "1.0.1", "1.0.0"],
```

`test_build_produces_one_complete_offline_book` 和 `test_english_book_is_a_separate_offline_edition` 里的 `<strong>v1.2.4</strong>` 都改成 `<strong>v1.2.5</strong>`。英文测试里的 `self.assertEqual("1.2.4", manifest["version"])` 改成 `self.assertEqual("1.2.5", manifest["version"])`。

`test_visual_polish_version_is_1_2_0` 里，从 `entry = revisions["entries"][0]` 起，替换到该方法最后一个 `assertNotIn` 为止。`799cfae` 上那一句检查的是 tag v1.2.3。换完后不要再留下检查 v1.2.3 的 `assertNotIn`。整段换成：

```python
        entry = revisions["entries"][0]
        typography = revisions["entries"][1]
        batch4 = revisions["entries"][2]
        batch3 = revisions["entries"][3]
        guide = revisions["entries"][4]
        previous = revisions["entries"][5]
        self.assertEqual("1.2.5", self.manifest["version"])
        self.assertEqual("2026-10-25", self.manifest["date"])
        self.assertEqual("1.2.5", english["version"])
        self.assertEqual("2026-10-25", english["date"])
        self.assertEqual("1.2.5", entry["version"])
        self.assertEqual("2026-10-25", entry["date"])
        self.assertEqual(
            [
                "整书样式的颜色、字号、间距、圆角和阴影改由一份令牌表提供，组件继续引用它们。屏幕、暗色和印刷的观感与 1.2.4 相同。",
                "中文和英文 HTML 仍把样式内嵌在单个文件里，不引用外部字体。",
            ],
            entry["zh"],
        )
        self.assertEqual(
            [
                "Colors, type, spacing, radius, and shadow now come from a token file. Components still reference them. Screen, dark, and print look the same as 1.2.4.",
                "Chinese and English HTML still embed the stylesheet in a single file and do not load a font from the network.",
            ],
            entry["en"],
        )
        self.assertEqual("1.2.4", typography["version"])
        self.assertEqual("2026-10-25", typography["date"])
        self.assertEqual(
            [
                "正文、标题和眉题改用一组字号；目录里的分部目标改成次要色，分部收束行加上分隔线。",
                "代码块补上能显示中文的等宽字体，行距略增；图注行距加大。印刷时代码块改为浅底，图注改为 9pt，不再大于正文。",
            ],
            typography["zh"],
        )
        self.assertEqual(
            [
                "Body, headings, and kickers use one type scale. Part goals in the contents are muted, and each part-closing line has a divider.",
                "Code blocks gain a monospace stack that can show Chinese, with a slightly looser line-height. Captions gain line-height. In print, code blocks are light and captions are 9pt, no longer larger than the body.",
            ],
            typography["en"],
        )
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
        self.assertIn("当前版本：**v1.2.5 · 2026-10-25**", readme)
        self.assertIn("版本号已经是 1.2.5。", readme)
        self.assertIn("样式来自 `stm32-book/styles/tokens.json` 和 `stm32-book/styles/book.css`，构建时拼进 HTML 的 `<style>`，`dist/` 里不另放 CSS。", readme)
        self.assertIn("也不要把 1.1.1 的产物标成 1.2.0，", readme)
        self.assertIn("也不要把 1.2.0 的产物标成 1.2.1，", readme)
        self.assertIn("也不要把 1.2.1 的产物标成 1.2.2，", readme)
        self.assertIn("也不要把 1.2.2 的产物标成 1.2.3，", readme)
        self.assertIn("也不要把 1.2.3 的产物标成 1.2.4，", readme)
        self.assertIn("也不要把 1.2.4 的产物标成 1.2.5。", readme)
        self.assertIn("打 tag `v1.2.5`", readme)
        self.assertNotIn("当前版本：**v1.2.4", readme)
        self.assertNotIn("打 tag `v1.2.4`", readme)
```

`也不要把 1.2.3 的产物标成 1.2.4` 这句保留，句号改成逗号，因为后面还要接 1.2.4 到 1.2.5。不要删更早的误标分句。

- [ ] **Step 2: 跑版本测试，确认它先失败**

Run:

```bash
python3 stm32-book/tests/test_build.py BookBuildContractTests.test_visual_polish_version_is_1_2_0 -v
```

Expected: 退出码 1。失败信息含 `'1.2.5' != '1.2.4'`。

- [ ] **Step 3: 写 1.2.5**

两份 manifest 只改 `version` 和 `date`。`date` 在 `799cfae` 上已经是 `2026-10-25`，保持这个日期，不要改其他字段。

`stm32-book/manifest.json` 和 `stm32-book/manifest-en.json`：

```json
  "version": "1.2.5",
  "date": "2026-10-25",
```

`stm32-book/revisions.json` 的 `entries` 最前面插入这一条。已有的 1.2.4 及更早条目一字不改，整段后移。

```json
    {
      "version": "1.2.5",
      "date": "2026-10-25",
      "zh": [
        "整书样式的颜色、字号、间距、圆角和阴影改由一份令牌表提供，组件继续引用它们。屏幕、暗色和印刷的观感与 1.2.4 相同。",
        "中文和英文 HTML 仍把样式内嵌在单个文件里，不引用外部字体。"
      ],
      "en": [
        "Colors, type, spacing, radius, and shadow now come from a token file. Components still reference them. Screen, dark, and print look the same as 1.2.4.",
        "Chinese and English HTML still embed the stylesheet in a single file and do not load a font from the network."
      ]
    },
```

`stm32-book/README.md` 当前版本句改成：

```markdown
当前版本：**v1.2.5 · 2026-10-25**。中文整书和英文整书共用这一版号。GitHub Release 仍要等这次提交进入 `main` 且 Book CI 产出四份文件之后，由有权限的人另行处理。
```

在「构建」一节，紧接在「`--lang` 默认 `zh`。英文版读 `manifest-en.json`、`docs/en/` 和 `stm32-book/book/en/`。」这段后面加一段：

```markdown
样式来自 `stm32-book/styles/tokens.json` 和 `stm32-book/styles/book.css`，构建时拼进 HTML 的 `<style>`，`dist/` 里不另放 CSS。
```

发布节的版本句改成下面这一整句。前面的误标分句保留，最后的句号改成逗号，再接新的一句：

```markdown
版本号已经是 1.2.5。构建脚本不会自己创建 GitHub Release。不要把 rc.8（`0c24f76`）的产物标成 1.0.0，也不要把 1.0.7 的产物标成 1.0.8，也不要把 1.0.8 的产物标成 1.1.0，也不要把 1.1.0 的产物标成 1.1.1，也不要把 1.1.1 的产物标成 1.2.0，也不要把 1.2.0 的产物标成 1.2.1，也不要把 1.2.1 的产物标成 1.2.2，也不要把 1.2.2 的产物标成 1.2.3，也不要把 1.2.3 的产物标成 1.2.4，也不要把 1.2.4 的产物标成 1.2.5。
```

第三步的「在该提交上打 tag `v1.2.4`」改成「在该提交上打 tag `v1.2.5`」。这一步仍不创建 tag，也不创建 Release。四份文件名保持不动。不改 `CREDITS.md`。

- [ ] **Step 4: 跑版本测试，确认通过，然后提交**

Run:

```bash
python3 stm32-book/tests/test_build.py BookBuildContractTests.test_visual_polish_version_is_1_2_0 -v
python3 stm32-book/tests/test_build.py BookBuildContractTests.test_revision_file_lists_1_0_0_through_manifest_version -v
```

Expected: 两条都通过。

```bash
git add stm32-book/tests/test_build.py stm32-book/manifest.json stm32-book/manifest-en.json stm32-book/revisions.json stm32-book/README.md
git commit -m "book: 把整书标成 1.2.5"
```

同一提交必须同时含测试和四份版本文件。`validate_revisions()` 不允许只改一边。

---

### Task 4: 验收抽出，并停在合入前

**Files:**
- Test: 整套 `stm32-book/tests`，外加中文和英文 `--check`
- 不新开测试文件，不改 `.github/workflows/book.yml`

**Interfaces:**
- Consumes: Task 2 的 `CSS` 与 Task 3 的 `1.2.5`。
- Produces: 实施 PR 可以请求合入时的证据。这一步没有新的功能提交。若 diff 检查发现越界文件，撤回那些文件后再提交一次，提交说明写明撤回了哪一处。

- [ ] **Step 1: 跑设计规格里的三条命令**

Run:

```bash
python3 -m unittest discover stm32-book/tests -v
python3 stm32-book/build_html.py --check
python3 stm32-book/build_html.py --lang en --check
```

Expected: 三条退出码都是 0。`test_css_token_extract_contract` 里的 SHA-256 仍是 `e0fb660584f1833e8a6d419ba78ed9d56e4e92e51cbb533430ac8833bcca6bf4`。

Book CI 的 `book` 作业还会跑 `python stm32-book/build_html.py --pdf`，`book-en` 作业跑 `python stm32-book/build_html.py --lang en --pdf`。本地这三条过了再推。不要改 workflow 来上传 CSS。Python 版本在 CI 里是 3.13。

- [ ] **Step 2: 看 diff 边界**

Run:

```bash
git diff --name-only origin/main...HEAD
```

实施分支的 `origin/main` 应已含本计划。Expected: 只有这八个路径：

```text
stm32-book/README.md
stm32-book/build_html.py
stm32-book/manifest-en.json
stm32-book/manifest.json
stm32-book/revisions.json
stm32-book/styles/book.css
stm32-book/styles/tokens.json
stm32-book/tests/test_build.py
```

多出来的 `docs/` 正文、`docs/en/`、`CONTENT_GUIDE.md`、`cover.svg`、仓库根 `assets/`、`tools/`、`CREDITS.md`、`.github/workflows/book.yml` 或 `requirements.txt`，撤回那些文件后再提交一次。

Run:

```bash
git diff --stat -- docs docs/en stm32-book/cover.svg assets tools .github/workflows/book.yml stm32-book/requirements.txt
```

Expected: 无输出。`docs/superpowers/plans/` 不在这条命令里。本计划文件如果还没在 `main` 上，它可以出现在实施分支里，但实施 PR 的最终 diff 不必再改它。

Run:

```bash
grep -n 'CSS = r"""' stm32-book/build_html.py || true
grep -n '<link' stm32-book/build_html.py stm32-book/styles/book.css || true
grep -n -E '9\.5pt|9pt|--table-columns|14vw|5\.6vw|rgba\(16, 24, 32' stm32-book/styles/tokens.json || true
grep -n -E '9\.5pt|--table-columns|rgba\(16, 24, 32, \.18\)|#10242e' stm32-book/styles/book.css
```

Expected: 前三条没有匹配。第四条有匹配。`--type-h1` 的 `clamp(1.85rem, 4.2vw, 2.7rem)` 是 40 个令牌之一，留在 JSON。封面和分部页的展示 `clamp`、印刷 `9.5pt`、图注 `9pt`、`.toc-jump` 的 `rgba(16, 24, 32, .18)` 和 `--table-columns` 留在 `book.css`。

Run:

```bash
git tag --points-at HEAD
```

Expected: 无输出。不要运行 `gh release create`，不要 `git tag`，不要打 `v1.2.5`。

确认这些断言还在：

```bash
grep -n -E '0x271|167 ns|len\(outline\)' stm32-book/tests/test_build.py
```

Expected: `0x271`、`167 ns` 和 `self.assertEqual(44, len(outline))` 仍有匹配。

- [ ] **Step 3: 打开构建出的 HTML，只看两处**

中文 `--check` 已经写出 `stm32-book/dist/stm32-practical-book.html`。打开这一份，看两处：封面标题板仍是浅底，左条仍是 spine；任选一章，`h2` 左边条、一块代码、一张图的图注仍在。英文书与中文共用这一份 CSS，打开 `stm32-book/dist/stm32-practical-book-en.html`，确认样式在 `<style>` 里面，页面里没有 `<link`。不要求把 29 章逐页看完。不新开浏览器用例。

- [ ] **Step 4: 开实施 PR 并停住**

实施 PR 从本计划已经合入的 `main` 另开分支。标题写明这是样式抽出 B 的实施，不是本计划。说明里写上：

- 样式从三引号字符串抽到 `stm32-book/styles/tokens.json` 和 `stm32-book/styles/book.css`。拼好的 `CSS` SHA-256 仍是 `e0fb660584f1833e8a6d419ba78ed9d56e4e92e51cbb533430ac8833bcca6bf4`。
- 中文和英文 HTML 仍各有一个 `<style>`，没有 `<link`。版本是 1.2.5 · 2026-10-25。
- 三条本地命令都通过。`book` 与 `book-en` 都变绿之后 squash 合入 `main`。不设章节 HTML 的第二次人审。
- 合入后在本机 `D:\Users\STM32` 拉取这次 `main`。拉取不产生仓库 diff。
- 不打 tag，不创建 GitHub Release。
- 刀 D、刀 C 不在这个 PR 里。

实施者自己不按合并按钮，不跑 `gh pr merge`。CI 还红时不合入。CI 变绿后由协调员 squash 合入。

最终 diff 必须同时有抽出和版本戳。不要把仍含三引号 `CSS` 的状态留成 PR 的最终内容。

这一步在验收已经通过时没有新的提交。

## 风险

这些都是设计规格里的风险。实施时按这里停，不要在抽出 PR 里顺手改版式。

- **哨兵空白差一个换行，哈希就会失败。** Task 2 的脚本先对原始字符串做往返。失败时改发射或哨兵周围的空白，保持 1.2.4 的字节。不要重排 `book.css`，不要改哈希常量。
- **样式若放进仓库根 `assets/`，会和刀 C 的图混在同一棵目录里。** 路径只允许 `stm32-book/styles/`。不要建 `stm32-book/assets/`。
- **改成 `<link>` 会拆掉单文件离线书，CI 也只上传 HTML。** `<style>{CSS}</style>` 保持。上传路径不增加 CSS。Task 1 断言每份 HTML 零个 `<link`。
- **`book.css` 里再写一遍颜色，JSON 就不再是唯一来源。** 源文件禁止 `{令牌名}:`。封面六个值只从 `light` 抄进拼好的 CSS。Task 1 锁住这件事。
- **把印刷 `9.5pt`、展示用 `clamp` 或 `.toc-jump` 的投影收进 JSON，这一刀就变成改版式。** 它们留在 `book.css`。刀 D 要动封面字号时另写设计。Task 4 的 `grep` 确认 JSON 里没有这些字面量。
- **`json` 若按字母序重写暗色那一行，视觉测试仍可能通过，哈希不会。** 发射顺序等于文件键序。不要 `sort_keys`。`--radius` 和 `--elev` 保持在字体栈之前。
- **给中英文各做一份 CSS，两本书会分叉。** `load_css` 的参数只有 `tokens_path` 和 `css_path`。两份 HTML 内嵌同一个 `builder.CSS`。

## 对照设计规格

| 设计规格里的要求 | 落在 |
| --- | --- |
| `tokens.json` 与 `book.css` 放在 `stm32-book/styles/`，不进仓库根 `assets/` | File map，Task 2，风险 |
| JSON 顶层 `schema`、`light`、`dark`、`print`、`coverLock`；`schema` 为整数 1 | Task 1，Task 2 的文件与 `load_css` |
| `light` 恰好 40 个键，顺序是 JSON 而不是分组标题；暗色和印刷恰好 15 个颜色 | Task 1 的 `_TOKEN_LIGHT_KEYS`，Task 2 |
| `coverLock` 六个名字，值从 `light` 读，不在 JSON 里重复 | Task 2 的封面发射 |
| 四个哨兵各一次；亮色和封面多行；暗色一行；印刷只替换注释 | Task 1 的上下文断言，Task 2 的脚本和 `replacements` |
| 拼好的字符串 SHA-256 仍是 `e0fb660584f1833e8a6d419ba78ed9d56e4e92e51cbb533430ac8833bcca6bf4` | 开工条件，Task 1，Task 2，Task 4 |
| 模块级 `CSS` 仍是 `str`，import 时赋值；`load_css` 可收临时路径且不改模块级对象 | Task 2 的函数，Task 1 的 `assertIs` |
| 单个 `<style>{CSS}</style>`，零个 `<link`，中英同一字符串，无外部字体 | Global Constraints，Task 1 的 `embedded` |
| 四个既有视觉方法和一个 `--spine` 断言不改也通过 | Global Constraints，Task 2 Step 4 |
| 坏令牌：缺 `--ink`、值含 `url(`、同一对象里 `--paper` 重复 | Task 1 的拒绝测试，Task 2 的 `object_pairs_hook` |
| 建议版本 1.2.5；高于 1.2.4 时写下一条修订号；日期在本计划里冻成 2026-10-25 | 开工条件，Task 3 |
| README 构建节说明样式来源；发布节加误标句；不打 tag，不创建 Release | Task 3，Task 4 |
| 不改 workflow、不改 `requirements.txt`、不改正文、不改 `cover.svg`、不实施 D/C | Global Constraints，Task 4 |
| 书签 44、`0x271`、`167 ns`、三档 `pageOverflow` 不放宽 | Task 4 |
| 人工看封面标题板和一章；英文只确认 `<style>` 内嵌 | Task 4 Step 3 |

## 执行交接

本文件所在的 PR 只审阅计划，不实施抽出。它不升版本，不新增 `stm32-book/styles/`，不改 `build_html.py`。CI 变绿不等于可以自动合入。

实施要等本计划合入 `main`，并且 `stm32-book/manifest.json` 的 `version` 仍是 `1.2.4`（或按开工条件已经更高）。然后从那个 `main` 另开分支，按任务顺序做。两种走法：

1. Subagent-Driven：每个任务一个新的执行者，任务之间再审一遍 diff。
2. Inline：同一会话里用 executing-plans，做完一个任务再进下一个。

Task 1 的提交会使整套测试变红。Task 2 结束时测试应重新全绿，版本仍是 1.2.4。实施 PR 要等到 Task 4 三条命令都退出码 0 再开。协调员在 `book` 与 `book-en` 都变绿后 squash 合入。不设章节人审停点。不打 tag，不创建 Release。

---

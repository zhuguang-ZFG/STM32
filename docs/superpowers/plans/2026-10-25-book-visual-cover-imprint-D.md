# 整书封面与扉页 D Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

I'm using the writing-plans skill to create the implementation plan.

**Goal:** 只做刀 D 的封面与扉页：中英文继续共用一张没有文字的 `stm32-book/cover.svg`，标题板把现有书脊短线移到书名和副题之间，扉页 `h1` 改用已有的 `var(--type-h1)` 并加一条 `4.2rem` × `.18rem` 的 `::after` 书脊短线，然后把整书标成 **1.2.6 · 2026-10-25**。本计划文件的 PR 不落地这些改动。

**Architecture:** 图仍是 `cover_art_svg()` 内嵌的那一个文件。书名、副题、眉题、版本行仍来自 manifest 和 `UI`。令牌表保持 schema 1。`book.css` 只替换扉页那一行，拼好的 `builder.CSS` 因此换成规格写死的新 SHA-256。先把会失败的契约写进 `stm32-book/tests/test_build.py`，再按图、标题板、扉页的顺序改到契约变绿，最后同一提交改版本戳。不新开测试文件，不新开第二份 SVG，不升 token schema。

**Tech Stack:** Python 3 标准库、现有 `stm32-book/build_html.py`、`stm32-book/styles/book.css`、`stm32-book/styles/tokens.json`、`python3 stm32-book/tests/test_build.py`、`python3 -m unittest discover stm32-book/tests -v`。不新增依赖，不改 `requirements.txt`。

`stm32-book/tests/` 不是 Python 包。单条测试写成 `python3 stm32-book/tests/test_build.py BookBuildContractTests.<方法名> -v`。不要写成 `python3 -m unittest stm32-book.tests...`。整套测试仍用 `python3 -m unittest discover stm32-book/tests -v`。类名是 `BookBuildContractTests`。

设计规格：`docs/superpowers/specs/2026-10-25-book-visual-cover-imprint-D-design.md`（PR #42，`0ea8a78`）。

写本计划时的尖端是 `0ea8a783b981e3554c84bdbd1b81b6d370a59d12`（`docs: 整书视觉刀 D 设计，封面与扉页 (#42)`）。这一尖端的整书版本仍是 **1.2.5**，日期仍是 `2026-10-25`。`stm32-book/cover.svg` 是 3965 字节。`stm32-book/styles/book.css` 源文件是 19663 字节，SHA-256 是 `bc15bac06ad752bcab8ecca0c267668f010a457ab0ee035db63b5fbc3e6d818a`，第一个字节是换行。拼好的 `builder.CSS` SHA-256 是 `e0fb660584f1833e8a6d419ba78ed9d56e4e92e51cbb533430ac8833bcca6bf4`。下面的行号属于 `0ea8a78`。实施时若行号被别的提交挪动，按选择器和原文定位。

`0ea8a78` 只新增了设计规格。它下面的 `b7ff335`（PR #41）才是刀 B 的实施。实施基线是本计划合入之后的 `main`，不是本计划的分支。本计划的 PR 只新增本文件。

本计划在 `0ea8a78` 的 `book.css` 上只做「扉页」那一处替换，再用与 `load_css()` 相同的四次哨兵替换，得到的 SHA-256 就是 `a4ccd1403ab742e82f67c39053c2609da1c9a8afa126d4f6b988a5b9559a5ac4`。未替换的文件得到刀 B 的 `e0fb6605…`。按下面三处 SVG 原文替换之后，`cover.svg` 的 UTF-8 长度是 3880 字节。

设计规格「实施 PR」的 1–7 步在本计划里的位置：

| 规格里的顺序 | 本计划 |
| --- | --- |
| 1. 封面图 | Task 2 |
| 2. 标题板顺序 | Task 3 |
| 3. 扉页规则 | Task 4 |
| 4. 测试（版本断言留到下一步） | Task 1。版本断言在 Task 5 |
| 5. 版本 | Task 5 |
| 6. 验证 | Task 6 |
| 7. 合入 | Task 6 的最后一步 |

Task 1 先写会失败的契约，是为了和刀 B、刀 E 一样：期望值来自规格，不从实施时手写的 CSS 反推。最终 diff 仍必须同时有封面图、标题板顺序、扉页 CSS、测试和版本戳。

## Global Constraints

- 本计划 PR 不实施刀 D。不改 `stm32-book/cover.svg`，不改 `stm32-book/styles/book.css`，不改 `stm32-book/build_html.py`，不改 `stm32-book/tests/test_build.py`，不改两份 manifest、`revisions.json`、`stm32-book/README.md`。CI 变绿不等于本 PR 可以自动合入。等人审完计划再合。
- 实施时可以改的只有：`stm32-book/cover.svg`、`stm32-book/styles/book.css`、`stm32-book/build_html.py`（只限 `.cover-panel` 里那几个节点的顺序）、`stm32-book/tests/test_build.py`、`stm32-book/revisions.json`、`stm32-book/manifest.json`、`stm32-book/manifest-en.json`、`stm32-book/README.md`。
- 目标版本是 **1.2.6 · 2026-10-25**。日期写死 `2026-10-25`。设计规格里「日期用实施当天」那一句，按本计划改成这个冻住的日期。两份 manifest、`revisions.json` 和 README 写同一个日期。
- 实施 PR 在 Book CI（`.github/workflows/book.yml`，名称 `Book CI`）的 `book` 与 `book-en` 都变绿之后 squash 合入 `main`。不改 workflow。不改正文，不设第二次章节 HTML 人审。
- 不打 tag，不创建 GitHub Release。合入后在本机 `D:\Users\STM32` 拉取这次 `main`。拉取不产生仓库 diff。
- 中英文继续内嵌同一份 `stm32-book/cover.svg`。不新增第二份封面 SVG，不按语言分图，不把书名排进 SVG。
- `cover.svg` 只许三处改动：删掉整行 `OFFLINE EDITION`，删掉 `opacity="0.18"` 的灯点光晕，在现有 `#d7c4a3` 外框的下一行加上同色内框。其余节点、坐标、填色、描边和 `transform="translate(148 114)"` 保持原文。
- 内框是 `<rect x="34" y="44" width="872" height="444" rx="12" fill="none" stroke="#d7c4a3" stroke-width="1"/>`。它比外框每边收进 12 个用户单位。不使用新颜色。不把填色改成 `var(--*)`。
- 图内不出现 `<text`、`font-family`、`font-size`、`<style`、`<filter`、`<foreignObject`、`<image`、带 `href` 或 `xlink:href` 的 `<use`。除 `xmlns` 里的 `www.w3.org` 以外不出现 URL。UTF-8 不超过 8192 字节。
- 图的十六进制集合仍恰好是 `#07141a`、`#0c1c24`、`#14181c`、`#1b5c45`、`#1e4d63`、`#5c6770`、`#8d99a3`、`#8ecae6`、`#c4552a`、`#c5ced6`、`#d7c4a3`、`#d9dde2`、`#e7d7a1`、`#f4f1ea`、`#ffb020`、`#fff4d2`，都是小写。不出现 `#9fd7c4`。`opacity` 只剩 `0.28` 然后 `0.45`。`<path d="M78 446H300" stroke="#8ecae6" stroke-width="2" fill="none"/>` 留下。`<circle r="22" fill="#ffb020"/>` 和 `<circle cx="-6" cy="-6" r="7" fill="#fff4d2"/>` 留下。
- 标题板子节点顺序改为眉题、书名、短线、副题、版本行。`ui(manifest, 'cover_kicker')`、`manifest['title']`、`manifest['subtitle']` 和版本行表达式保持原文。不改 `cover_art_svg()`，不改 `imprint_html()`。
- `.cover .rule` 的 `width: 4.2rem; height: .18rem; background: var(--spine)` 不改。`.cover h1` 的 `clamp(2.15rem, 5.6vw, 3.7rem)` 和 `.cover .subtitle` 的 `clamp(1.05rem, 2.4vw, 1.35rem)` 不改。
- 标题板继续靠 `.cover` 上的 `coverLock` 保持浅底。暗色查询里不写 `.cover`。不要把 `coverLock` 抄到 `.imprint` 上。
- `book.css` 只做一处替换，把 `.imprint h1 { margin-bottom: .4rem; }` 换成规格里的两行。字号只写在单独的 `.imprint h1` 上，不写进 `.imprint h1, .companion h2`。短线是 `.imprint h1::after`，宽 `4.2rem`，高 `.18rem`，`background: var(--spine)`。不新增第二份 SVG。
- 不改 `tokens.json` 的键、值和 `coverLock`。不改 `load_css` 的签名和四个哨兵。`schema` 仍是整数 `1`。不把画板 `#10242e`、`#0c1c24`、`#f4f1ea`，封面 `clamp`，`.part-divider h1` 的 `clamp(2rem, 5vw, 3.35rem)`，`.part-goal` 的 `1.12rem`，`.part-index` 的 `clamp(4.5rem, 14vw, 8.5rem)` 和窄屏 `3rem`，`.toc-jump` 的 `.85rem` 与 `rgba(16, 24, 32, .18)`，印刷 `9.5pt`、图注 `9pt`、`@page` 的 `16mm 15mm 18mm`，收进 JSON，也不改这些字面量。`--table-columns` 仍是表格 HTML 的内联 style，不进令牌表。
- `book.css` 源文件的十六进制集合仍恰好是 `#10242e`、`#f4f1ea`、`#0c1c24`。五段 `@media` 的顺序仍是 960、720、暗色、减少动效、印刷。不加 `@font-face`，不写 `url(`，不引用 `fonts.googleapis` 或 `fonts.gstatic`。不加 `<link rel="stylesheet">`。
- 拼好的 CSS 新 SHA-256 是 `a4ccd1403ab742e82f67c39053c2609da1c9a8afa126d4f6b988a5b9559a5ac4`。只改 SVG 或 HTML 顺序不会改变这个哈希。对不上时改回扉页那两行的原文，不要改期望哈希来迁就另一份 CSS，也不要改令牌值。
- 四个既有方法的函数体一个断言都不改：`test_visual_polish_css_contract`、`test_typography_e_css_contract`、`test_visual_polish_contrast_clears_4_5`、`test_code_glossary_and_print_css_keep_reading_units_movable`。
- 不改 `docs/00`–`28`、`docs/en/`、附录 Markdown、两份 `CONTENT_GUIDE.md`、罗盘文案、`revisions.json` 里已有句子、仓库根 `assets/`、`tools/`（含 `tools/gen_mp_covers.py`）、`CREDITS.md`、`.github/workflows/book.yml`。不改 `UI` 里的封面眉题、扉页眉题、扉页标题、导语、商标句。不改 `.imprint dl` 的 `3px` 顶边、列宽、960px 折叠。不改修订史、文前、目录的 `h1` 字号。不实施刀 C。
- 印刷里 `.imprint { break-before: auto; page-break-before: auto; }` 保持。不要改成 `always`。`.cover` 的 `min-height: 245mm`、`page-break-after: always`、`background: #10242e` 保持。
- 不改 `toc_html`、分类函数、罗盘 HTML、书签、章号。出版书签仍是 44 条。不删 `0x271`、`167 ns`、样本章和各批加厚的断言。`pageOverflow` 为 0 的 1200、840、390 三档不放宽。窄屏列表标记仍是 `rgb(7, 94, 132)`。
- 修订说明只用设计里的四句。不写刀 C，也不写章节名。已有修订句子一字不改。
- 中文书名保持「STM32 实战：从点亮一颗灯到交付一个系统」，副题保持「29 章证据驱动的嵌入式入门与工程手册」。英文书名保持「STM32 in Practice: From One LED to a System You Can Ship」，副题保持「A 29-chapter evidence-driven introduction and engineering handbook」。扉页眉题保持「版权页」/「COLOPHON」。扉页标题保持「版本与许可」/「Version and license」。封面眉题保持「STM32 实战手册」/「STM32 PRACTICAL BOOK」。

上一句「Book CI 变绿后 squash 合入」指刀 D 的实施 PR。本计划文件的 PR 等人审阅，不在 CI 变绿后自动合入，也不在本 PR 里改 `stm32-book/`。

## 开工条件

实施开始时先读实施分支所基于的 `main` 上的 `stm32-book/manifest.json`，只看 `version` 和 `date`。不要在本计划的分支上改 SVG、CSS 或版本。

- `version` 低于 `1.2.5`：停。刀 B 还没在这条历史上。不开实施分支。
- `version` 是 `1.2.5` 且 `date` 是 `2026-10-25`：实施版写成 `1.2.6`，日期写成 `2026-10-25`。下面任务里的字面量按这个走。这是预期路径。`0ea8a78` 就是这个状态。
- `version` 已经高于 `1.2.5`（仍是 `1.2.x`，且补丁号大于 5）：实施版写成下一条修订号。不把 `1.2.6` 硬套上去。日期仍是 `2026-10-25`。Task 5 里每一处 `1.2.6` 换成这个新号，每一处当作「上一版」的 `1.2.5` 换成当时 manifest 的 `version`。修订四句不变。已有修订句子保持原文，只把索引后移一位。
- `date` 已经不是 `2026-10-25`：停。不要把本计划里冻住的日期写到另一天的书上。先对人说明。

接着核对拼好的样式。在仓库根运行：

```bash
python3 - << 'PY'
import hashlib
import importlib.util
from pathlib import Path
path = Path("stm32-book/build_html.py")
spec = importlib.util.spec_from_file_location("stm32_book_builder", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
print(hashlib.sha256(module.CSS.encode("utf-8")).hexdigest())
PY
```

Expected: `e0fb660584f1833e8a6d419ba78ed9d56e4e92e51cbb533430ac8833bcca6bf4`。

不是这个值就停。说明 `main` 上的样式又动过。把「扉页」一节的那一处替换应用到当时的 `book.css` 上，用与 `load_css()` 相同的四次哨兵替换重新计算 SHA-256。只把 Task 1 里的期望哈希换成这个新结果，并在实施 PR 里写出旧哈希和新哈希。不要改封面 `clamp`，不要改令牌，不要改 SVG 来凑哈希。基线仍是 `e0fb6605…` 时，新哈希必须仍是 `a4ccd1403ab742e82f67c39053c2609da1c9a8afa126d4f6b988a5b9559a5ac4`。

`validate_revisions()` 在 `build_html.py` 第 820 行。它要求 `revisions.json` 第一条的 `version` 等于 manifest 的 `version`。Task 5 必须同一提交改测试、两份 manifest、`revisions.json` 和 README。

## File map

| 路径 | 实施时的责任 |
| --- | --- |
| `docs/superpowers/plans/2026-10-25-book-visual-cover-imprint-D.md` | 本计划。本 PR 只新增这一份 |
| `stm32-book/tests/test_build.py` | Task 1 改封面 SVG 的两条断言、改哈希那一个字符串，并新增 `test_cover_imprint_d_contract`。Task 5 只改版本断言。四个既有视觉方法不改 |
| `stm32-book/cover.svg` | Task 2。删一行字、删一个光晕圆、加一道内框。其余字节不动 |
| `stm32-book/build_html.py` | Task 3。只把 `.cover-panel` 里的 `<hr class="rule">` 移到 `<h1>` 和副题之间 |
| `stm32-book/styles/book.css` | Task 4。只替换第 38 行那一条扉页规则。不改 `tokens.json` |
| `stm32-book/manifest.json` | Task 5：`version` 改为 `1.2.6`，`date` 保持 `2026-10-25` |
| `stm32-book/manifest-en.json` | 同上 |
| `stm32-book/revisions.json` | Task 5：`entries` 最前插入 1.2.6。已有条目一字不改 |
| `stm32-book/README.md` | Task 5：当前版本句、发布节的版本句、tag 名，以及「也不要把 1.2.5 的产物标成 1.2.6」 |

`stm32-book/styles/tokens.json` 不在这张表里。实施 diff 里它必须是空的。

---

### Task 1: 先写下会失败的封面与扉页契约

**Files:**
- Modify: `stm32-book/tests/test_build.py`（`test_css_token_extract_contract` 里只改哈希字符串；`test_cover_svg_stays_self_contained` 里删掉两行 `<text` 断言并换上三行；在该方法之后、`test_running_headers_follow_appendices_and_shorten_long_titles` 之前插入 `test_cover_imprint_d_contract`）
- Test: `stm32-book/tests/test_build.py`

**Interfaces:**
- Consumes: 已有的 `BookBuildContractTests._css_rule`、`self.builder.CSS`、`BOOK_DIR`。屏幕段是第一个 `@media` 之前，暗色段是暗色查询到下一个 `@media`，印刷段是 `@media print` 之后。`_css_rule` 用「选择器紧挨 `{`」取规则，所以 `.imprint h1` 不会取到 `.imprint h1::after`，也不会取到 `.imprint h1, .companion h2`。不要改 `_css_rule`。
- Produces: `BookBuildContractTests.test_cover_imprint_d_contract`。后面的任务按这个名字跑。`test_css_token_extract_contract` 的期望哈希换成新值。这一任务不改版本断言，不改 `cover.svg`，不改 `book.css`，不改 `build_html.py`。

这一提交之后，整套 `discover` 会失败。这是预期。不要开实施 PR，不要 squash。封面图的断言要到 Task 2 才绿，标题板顺序要到 Task 3 才绿，扉页 CSS 和哈希要到 Task 4 才绿。四个既有视觉方法现在就应该仍绿。

`test_cover_imprint_d_contract` 里的断言顺序就是下面这份：先 SVG，再两份 HTML 的标题板，再扉页 CSS。这样 Task 2 之后失败点落在标题板顺序，Task 3 之后失败点落在 `font-size: var(--type-h1)`。不要把 CSS 断言挪到 SVG 前面，否则 Task 2 和 Task 3 的失败信息会混在一起。

板上另有一枚 `<rect x="22" y="0" width="14" height="14"/>`。断言外框时用整段矩形，不要只搜 `x="22"`。

- [ ] **Step 1: 改封面自包含断言和哈希字符串**

在 `test_cover_svg_stays_self_contained` 里删掉这两行：

```python
        self.assertIn('<text x="112" y="62"', svg)
        self.assertNotIn('<text x="72" y="62"', svg)
```

换成：

```python
        self.assertNotIn("<text", svg)
        self.assertNotIn("OFFLINE EDITION", svg)
        self.assertNotIn('opacity="0.18"', svg)
```

`aria-label`、`#c4552a`、`#8ecae6`、`#1b5c45`、`#ffb020`、禁止 `#9fd7c4`、禁止 `<style`、禁止外链、`translate(148 114)`、禁止旧的 `translate(118 100)`、`--spine: #c4552a` 都留下。

在 `test_css_token_extract_contract` 里，只把这一个字符串：

```python
            "e0fb660584f1833e8a6d419ba78ed9d56e4e92e51cbb533430ac8833bcca6bf4",
```

换成：

```python
            "a4ccd1403ab742e82f67c39053c2609da1c9a8afa126d4f6b988a5b9559a5ac4",
```

该方法其余断言保持原文。不要改 `test_css_token_extract_rejects_bad_tokens`。

- [ ] **Step 2: 写入 `test_cover_imprint_d_contract`**

在 `def test_running_headers_follow_appendices_and_shorten_long_titles` 之前插入：

```python
    def test_cover_imprint_d_contract(self) -> None:
        svg = (BOOK_DIR / "cover.svg").read_text(encoding="utf-8")
        self.assertIn('viewBox="0 0 1200 760"', svg)
        self.assertIn(
            '<rect x="22" y="32" width="896" height="468" rx="18" fill="none" stroke="#d7c4a3" stroke-width="4"/>',
            svg,
        )
        self.assertIn(
            '<rect x="34" y="44" width="872" height="444" rx="12" fill="none" stroke="#d7c4a3" stroke-width="1"/>',
            svg,
        )
        self.assertIn('stroke="#8ecae6"', svg)
        self.assertIn('<circle r="22" fill="#ffb020"/>', svg)
        self.assertNotIn("<text", svg)
        self.assertNotIn("font-family", svg)
        self.assertNotIn("font-size", svg)
        self.assertNotIn("<filter", svg)
        self.assertNotIn("<foreignObject", svg)
        self.assertNotIn('opacity="0.18"', svg)
        found = re.findall(r"#[0-9A-Fa-f]{3,8}", svg)
        self.assertEqual(
            {
                "#07141a",
                "#0c1c24",
                "#14181c",
                "#1b5c45",
                "#1e4d63",
                "#5c6770",
                "#8d99a3",
                "#8ecae6",
                "#c4552a",
                "#c5ced6",
                "#d7c4a3",
                "#d9dde2",
                "#e7d7a1",
                "#f4f1ea",
                "#ffb020",
                "#fff4d2",
            },
            set(found),
        )
        self.assertTrue(all(item == item.lower() for item in found))
        self.assertEqual(["0.28", "0.45"], re.findall(r'opacity="([^"]*)"', svg))
        self.assertLessEqual(len(svg.encode("utf-8")), 8192)

        def panel_of(html: str) -> str:
            start = html.index('<div class="cover-panel">')
            end = html.index("</div>", start)
            return html[start:end]

        def heading_text(panel: str) -> str:
            match = re.search(r"<h1>(.*?)</h1>", panel, re.S)
            self.assertIsNotNone(match)
            return match.group(1)

        def assert_plate(html: str, title: str) -> None:
            panel = panel_of(html)
            self.assertLess(panel.index('class="eyebrow"'), panel.index("<h1>"))
            self.assertLess(panel.index("<h1>"), panel.index('class="rule"'))
            self.assertLess(panel.index('class="rule"'), panel.index('class="subtitle"'))
            self.assertEqual(title, heading_text(panel))
            self.assertNotIn("OFFLINE EDITION", html)
            self.assertNotIn("fonts.googleapis", html)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            chinese = self.builder.build_html(root / "zh")
            english = self.builder.build_html(root / "en", BOOK_DIR / "manifest-en.json")
            zh = json.loads((BOOK_DIR / "manifest.json").read_text(encoding="utf-8"))
            en = json.loads((BOOK_DIR / "manifest-en.json").read_text(encoding="utf-8"))
            assert_plate(chinese.read_text(encoding="utf-8"), zh["title"])
            assert_plate(english.read_text(encoding="utf-8"), en["title"])

        css = self.builder.CSS
        screen = css.split("@media", 1)[0]
        dark = css.split("@media (prefers-color-scheme: dark)", 1)[1].split("@media", 1)[0]
        printed = css.split("@media print", 1)[1]
        imprint = self._css_rule(screen, ".imprint h1")
        self.assertIn("margin-bottom: .4rem", imprint)
        self.assertIn("font-size: var(--type-h1)", imprint)
        self.assertIn("line-height: 1.22", imprint)
        companion = self._css_rule(screen, ".imprint h1, .companion h2")
        self.assertIn("margin-top: 0", companion)
        self.assertNotIn("font-size", companion)
        rule = self._css_rule(screen, ".imprint h1::after")
        self.assertIn('content: ""', rule)
        self.assertIn("width: 4.2rem", rule)
        self.assertIn("height: .18rem", rule)
        self.assertIn("background: var(--spine)", rule)
        self.assertNotIn("url(", rule)
        self.assertIn("clamp(2.15rem, 5.6vw, 3.7rem)", self._css_rule(screen, ".cover h1"))
        self.assertIn("clamp(1.05rem, 2.4vw, 1.35rem)", self._css_rule(screen, ".cover .subtitle"))
        self.assertIn("clamp(2rem, 5vw, 3.35rem)", self._css_rule(screen, ".part-divider h1"))
        self.assertIn("font-size: 9.5pt", printed)
        self.assertIn("font-size: 9pt", printed)
        self.assertIn(".imprint { break-before: auto; page-break-before: auto; }", printed)
        self.assertIn("background: #10242e", self._css_rule(printed, ".cover"))
        self.assertNotIn(".cover", dark)

        tokens = json.loads((BOOK_DIR / "styles" / "tokens.json").read_text(encoding="utf-8"))
        self.assertEqual(1, tokens["schema"])
        self.assertEqual(
            ["--paper", "--ink", "--muted", "--warn", "--line", "--spine"],
            tokens["coverLock"],
        )
        css_source = (BOOK_DIR / "styles" / "book.css").read_text(encoding="utf-8")
        self.assertEqual(
            {"#10242e", "#f4f1ea", "#0c1c24"},
            set(re.findall(r"#[0-9A-Fa-f]{3,8}", css_source)),
        )
```

中文 `title` 仍应是「STM32 实战：从点亮一颗灯到交付一个系统」。英文 `title` 仍应是「STM32 in Practice: From One LED to a System You Can Ship」。测试从 manifest 读，不要把这两句写死进断言。这一任务也不要改 manifest。

- [ ] **Step 3: 跑新契约，确认失败，并确认四个旧方法仍通过**

Run:

```bash
python3 stm32-book/tests/test_build.py BookBuildContractTests.test_cover_svg_stays_self_contained -v
python3 stm32-book/tests/test_build.py BookBuildContractTests.test_cover_imprint_d_contract -v
python3 stm32-book/tests/test_build.py BookBuildContractTests.test_css_token_extract_contract -v
```

Expected: 三条都失败。`test_cover_svg_stays_self_contained` 因为 SVG 里还有 `<text`。`test_cover_imprint_d_contract` 因为还没有内框矩形。`test_css_token_extract_contract` 因为哈希仍是 `e0fb660584f1833e8a6d419ba78ed9d56e4e92e51cbb533430ac8833bcca6bf4`，不是 `a4ccd140…`。

Run:

```bash
python3 stm32-book/tests/test_build.py BookBuildContractTests.test_visual_polish_css_contract -v
python3 stm32-book/tests/test_build.py BookBuildContractTests.test_typography_e_css_contract -v
python3 stm32-book/tests/test_build.py BookBuildContractTests.test_visual_polish_contrast_clears_4_5 -v
python3 stm32-book/tests/test_build.py BookBuildContractTests.test_code_glossary_and_print_css_keep_reading_units_movable -v
```

Expected: 四条都通过。

不要为了让新测试变绿去改 `cover.svg` 或 `book.css`。那是 Task 2 和 Task 4。

- [ ] **Step 4: 提交测试**

```bash
git add stm32-book/tests/test_build.py
git commit -m "book: 为封面与扉页 D 写下会失败的契约"
```

这一提交只有测试文件。不要把仍锁着 `e0fb6605…` 的测试留成实施 PR 的最终内容。

---

### Task 2: 改封面图

**Files:**
- Modify: `stm32-book/cover.svg`（只动第 7 行的文字、第 12 行外框的下一行、第 46 行的光晕圆）
- Test: `stm32-book/tests/test_build.py` 的 `BookBuildContractTests.test_cover_svg_stays_self_contained`

**Interfaces:**
- Consumes: Task 1 的 SVG 断言。图仍由 `cover_art_svg()` 整份读入，本任务不改这个函数。
- Produces: 一份没有 `<text`、没有 `opacity="0.18"`、含内框的 `cover.svg`。UTF-8 长度 3880 字节。十六进制集合仍是那 16 个。

只做下面三处替换。不要重排其余节点，不要改引号，不要把属性换行。

- [ ] **Step 1: 删掉英文眉题**

删掉整行，连同它的换行。不要换成中文，也不要换成别的拉丁字母。

```xml
  <text x="112" y="62" fill="#8ecae6" font-family="ui-sans-serif, sans-serif" font-size="18" letter-spacing="3.5">OFFLINE EDITION</text>
```

`#8ecae6` 还在 `<path d="M78 446H300" stroke="#8ecae6" stroke-width="2" fill="none"/>` 上，必须留下。

- [ ] **Step 2: 在外框下一行加上同色内框**

外框这一行保持原文：

```xml
    <rect x="22" y="32" width="896" height="468" rx="18" fill="none" stroke="#d7c4a3" stroke-width="4"/>
```

紧接它的下一行插入：

```xml
    <rect x="34" y="44" width="872" height="444" rx="12" fill="none" stroke="#d7c4a3" stroke-width="1"/>
```

内框使用已有的 `#d7c4a3`。不要新造颜色，不要改成 `var(--spine)` 或 `var(--line)`。

- [ ] **Step 3: 删掉灯点光晕**

删掉这一行，连同它的换行：

```xml
      <circle r="42" fill="#ffb020" opacity="0.18"/>
```

同一组里的下面两行留下：

```xml
      <circle r="22" fill="#ffb020"/>
      <circle cx="-6" cy="-6" r="7" fill="#fff4d2"/>
```

根元素仍是 `viewBox="0 0 1200 760"`、`role="img"`、`aria-label="STM32 board"`。`transform="translate(148 114)"` 保持。网格的 `opacity="0.28"` 和偏移底板的 `opacity="0.45"` 保持，文档顺序也是这个顺序。

- [ ] **Step 4: 核对字节，跑封面测试，然后提交**

Run:

```bash
python3 - << 'PY'
from pathlib import Path
svg = Path("stm32-book/cover.svg").read_bytes()
print(len(svg))
PY
python3 stm32-book/tests/test_build.py BookBuildContractTests.test_cover_svg_stays_self_contained -v
```

Expected: 打印 `3880`。`test_cover_svg_stays_self_contained` 通过。不是 3880 就说明还动了这三处以外的字节，先改回去。测试的上限是 8192，3880 是这三处替换的旁证。

`test_cover_imprint_d_contract` 这时仍失败，失败点应落在封面面板里 `<h1>` 还在 `class="rule"` 后面。`test_css_token_extract_contract` 仍因哈希失败。这是预期。不要在这一提交里改测试或 CSS。

```bash
git add stm32-book/cover.svg
git commit -m "book: 封面图去掉英文眉题和灯晕，加上内框"
```

---

### Task 3: 把书脊短线移到书名和副题之间

**Files:**
- Modify: `stm32-book/build_html.py`（第 1341–1347 行的 `.cover-panel`）
- Test: `stm32-book/tests/test_build.py` 的 `BookBuildContractTests.test_cover_imprint_d_contract`

**Interfaces:**
- Consumes: Task 1 的 `assert_plate`。它要求 `class="eyebrow"` 在 `<h1>` 前，`<h1>` 在 `class="rule"` 前，`class="rule"` 在 `class="subtitle"` 前。
- Produces: `.cover-panel` 的子节点顺序为眉题、书名、短线、副题、版本行。表达式与 Task 2 之前相同。

- [ ] **Step 1: 只调整节点顺序**

把现在的：

```html
    <div class="cover-panel">
      <p class="eyebrow">{html.escape(ui(manifest, 'cover_kicker'))}</p>
      <hr class="rule">
      <h1>{html.escape(manifest['title'])}</h1>
      <p class="subtitle">{html.escape(manifest['subtitle'])}</p>
      <p class="edition"><strong>v{html.escape(manifest['version'])}</strong><span>{html.escape(manifest['date'])} · {html.escape(manifest['author'])}</span></p>
    </div>
```

换成：

```html
    <div class="cover-panel">
      <p class="eyebrow">{html.escape(ui(manifest, 'cover_kicker'))}</p>
      <h1>{html.escape(manifest['title'])}</h1>
      <hr class="rule">
      <p class="subtitle">{html.escape(manifest['subtitle'])}</p>
      <p class="edition"><strong>v{html.escape(manifest['version'])}</strong><span>{html.escape(manifest['date'])} · {html.escape(manifest['author'])}</span></p>
    </div>
```

五段表达式一个字符都不改。`<hr class="rule">` 保持这个写法，不要加自闭合斜杠。不改 `cover_art_svg()`。不改 `imprint_html()`。不改 `UI` 字典。`.cover .rule` 的 CSS 不改。

- [ ] **Step 2: 确认短线已在书名下面，然后提交**

Run:

```bash
python3 stm32-book/tests/test_build.py BookBuildContractTests.test_cover_imprint_d_contract -v
```

Expected: 失败。失败点是 `.imprint h1` 的规则里还没有 `font-size: var(--type-h1)`。不要失败在 `class="rule"` 的先后顺序上。若失败在顺序上，说明 `<hr class="rule">` 还在 `<h1>` 前面。

`test_css_token_extract_contract` 仍因哈希失败。这是预期。SVG 和 HTML 顺序不参与这个哈希。

```bash
git add stm32-book/build_html.py
git commit -m "book: 标题板把书脊短线移到书名和副题之间"
```

`git diff -- stm32-book/build_html.py` 里只应看到那三行的位置交换。

---

### Task 4: 扉页标题改用章标题字号，并加书脊短线

**Files:**
- Modify: `stm32-book/styles/book.css`（第 38 行那一条，连同它的行尾换行）
- Test: `stm32-book/tests/test_build.py` 的 `BookBuildContractTests.test_cover_imprint_d_contract` 与 `BookBuildContractTests.test_css_token_extract_contract`

**Interfaces:**
- Consumes: 已有的 `--type-h1` 和 `--spine`。不新增 JSON 键。`load_css()` 仍在 import 时把四个哨兵填进这份文件。
- Produces: 拼好的 `builder.CSS`，其 SHA-256 为 `a4ccd1403ab742e82f67c39053c2609da1c9a8afa126d4f6b988a5b9559a5ac4`。`.imprint h1::after` 是一条独立规则。

- [ ] **Step 1: 只替换这一行**

被替换的原文是这一行，含行尾换行：

```css
.imprint h1 { margin-bottom: .4rem; }
```

替换成下面两行。属性顺序就是这个顺序，分号后各一个空格，行尾是换行：

```css
.imprint h1 { margin-bottom: .4rem; font-size: var(--type-h1); line-height: 1.22; }
.imprint h1::after { content: ""; display: block; width: 4.2rem; height: .18rem; margin-top: .85rem; background: var(--spine); }
```

上一行保持原文：

```css
.imprint h1, .companion h2 { margin-top: 0; }
```

不要把 `font-size` 写进这行。那会把配套资源的 `h2` 也抬到章标题字号。不要改 `.imprint` 的 padding、底边、导语颜色，不要改 `dl` 的 `3px` 顶边和列宽。不要给修订史、文前、目录的 `h1` 加 `font-size`。不要在 `@media (prefers-color-scheme: dark)` 里写 `.cover` 或 `.imprint`。不要把 `coverLock` 抄到 `.imprint`。暗色下扉页短线可以是 `#f0b090`，封面上的短线仍是 `#c4552a`。不要为了让它们同色去改令牌。

印刷段的 `.imprint { break-before: auto; page-break-before: auto; }` 保持。`.cover { min-height: 245mm; page-break-after: always; background: #10242e; }` 保持。

不改 `stm32-book/styles/tokens.json`。

- [ ] **Step 2: 核对哈希和两条契约，然后提交**

Run:

```bash
python3 - << 'PY'
import hashlib
import importlib.util
from pathlib import Path
path = Path("stm32-book/build_html.py")
spec = importlib.util.spec_from_file_location("stm32_book_builder", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
print(hashlib.sha256(module.CSS.encode("utf-8")).hexdigest())
PY
python3 stm32-book/tests/test_build.py BookBuildContractTests.test_cover_imprint_d_contract -v
python3 stm32-book/tests/test_build.py BookBuildContractTests.test_css_token_extract_contract -v
python3 stm32-book/tests/test_build.py BookBuildContractTests.test_typography_e_css_contract -v
python3 stm32-book/tests/test_build.py BookBuildContractTests.test_visual_polish_css_contract -v
```

Expected: 打印 `a4ccd1403ab742e82f67c39053c2609da1c9a8afa126d4f6b988a5b9559a5ac4`。四条测试都通过。

哈希对不上时，把 `book.css` 改回上面那两行的原文。先核对是不是多了一个空格，或属性顺序变了。不要把测试里的期望改成另一份 CSS 的哈希。开工条件里基线已经不是 `e0fb6605…` 的情况除外，那种情况只替换 Task 1 已经写上的那一个新哈希，并在实施 PR 里写出旧值和新值。

版本此时仍是 1.2.5。`test_visual_polish_version_is_1_2_0` 现在就应该通过。整套 `discover` 也应通过。版本戳留到 Task 5。

```bash
git add stm32-book/styles/book.css
git commit -m "book: 扉页标题改用章标题字号并加书脊短线"
```

`git diff -- stm32-book/styles/tokens.json` 必须没有输出。

---

### Task 5: 把整书标成 1.2.6

**Files:**
- Modify: `stm32-book/tests/test_build.py`（只改版本断言）
- Modify: `stm32-book/manifest.json`（只改 `version`；`date` 保持 `2026-10-25`）
- Modify: `stm32-book/manifest-en.json`（同上）
- Modify: `stm32-book/revisions.json`（`entries` 最前插入一条）
- Modify: `stm32-book/README.md`（当前版本句、发布节版本句、tag 名、一句新的误标）
- Test: `stm32-book/tests/test_build.py`

**Interfaces:**
- Consumes: Task 4 已经变绿的封面与扉页。`validate_revisions()` 要求修订第一条的 `version` 等于两份 manifest 的 `version`。
- Produces: 两份 manifest、`revisions.json` 和 README 上的 `1.2.6` / `2026-10-25`。已有修订句子不变。

高于 `1.2.5` 的开工路径：下面每一处 `1.2.6` 换成当时的下一条修订号，每一处当作上一版的 `1.2.5` 换成当时 manifest 的 `version`。日期仍写 `2026-10-25`。四句修订说明不改。

- [ ] **Step 1: 改版本断言**

`assert_version_history_and_index` 里的元组在 `1.2.5` 前加上 `1.2.6`：

```python
        versions = ("1.2.6", "1.2.5", "1.2.4", "1.2.3", "1.2.2", "1.2.1", "1.2.0", "1.1.1", "1.1.0", "1.0.8", "1.0.7", "1.0.6", "1.0.5", "1.0.4", "1.0.3", "1.0.2", "1.0.1", "1.0.0")
```

在 `self.assertLess(history.index(">1.2.5<"), history.index(">1.2.4<"))` 之前加上：

```python
        self.assertLess(history.index(">1.2.6<"), history.index(">1.2.5<"))
```

其后的先后顺序保持。

`test_revision_file_lists_1_0_0_through_manifest_version` 的列表以 `1.2.6` 起头，下一项仍是 `1.2.5`：

```python
            ["1.2.6", "1.2.5", "1.2.4", "1.2.3", "1.2.2", "1.2.1", "1.2.0", "1.1.1", "1.1.0", "1.0.8", "1.0.7", "1.0.6", "1.0.5", "1.0.4", "1.0.3", "1.0.2", "1.0.1", "1.0.0"],
```

`test_build_produces_one_complete_offline_book` 和 `test_english_book_is_a_separate_offline_edition` 里的 `<strong>v1.2.5</strong>` 改为 `<strong>v1.2.6</strong>`。英文测试里的 `self.assertEqual("1.2.5", manifest["version"])` 改为 `self.assertEqual("1.2.6", manifest["version"])`。

`test_visual_polish_version_is_1_2_0` 的名字不改。把条目绑定从：

```python
        entry = revisions["entries"][0]
        typography = revisions["entries"][1]
        batch4 = revisions["entries"][2]
        batch3 = revisions["entries"][3]
        guide = revisions["entries"][4]
        previous = revisions["entries"][5]
```

改成：

```python
        entry = revisions["entries"][0]
        tokens = revisions["entries"][1]
        typography = revisions["entries"][2]
        batch4 = revisions["entries"][3]
        batch3 = revisions["entries"][4]
        guide = revisions["entries"][5]
        previous = revisions["entries"][6]
```

在原来核对 `entries[0]` 的那一段之前，插入对 `entry` 的新断言。原来那一段改去核对 `tokens`，句子一字不改：

```python
        self.assertEqual("1.2.6", self.manifest["version"])
        self.assertEqual("2026-10-25", self.manifest["date"])
        self.assertEqual("1.2.6", english["version"])
        self.assertEqual("2026-10-25", english["date"])
        self.assertEqual("1.2.6", entry["version"])
        self.assertEqual("2026-10-25", entry["date"])
        self.assertEqual(
            [
                "封面图不再写英文眉题，板卡外框加了一道内线；发光的灯点改成平涂。中英文仍共用这一张图。",
                "标题板把书名放在书脊短线上面。扉页标题改用章标题的字号，并在标题下重复这条书脊短线。",
            ],
            entry["zh"],
        )
        self.assertEqual(
            [
                "The cover drawing no longer carries an English kicker. The board frame gains an inner rule, and the glowing lamp is flat. Both languages still share this drawing.",
                "The title plate places the title above the spine rule. The imprint heading uses the chapter title size and repeats that spine rule.",
            ],
            entry["en"],
        )
        self.assertEqual("1.2.5", tokens["version"])
        self.assertEqual("2026-10-25", tokens["date"])
        self.assertEqual(
            [
                "整书样式的颜色、字号、间距、圆角和阴影改由一份令牌表提供，组件继续引用它们。屏幕、暗色和印刷的观感与 1.2.4 相同。",
                "中文和英文 HTML 仍把样式内嵌在单个文件里，不引用外部字体。",
            ],
            tokens["zh"],
        )
        self.assertEqual(
            [
                "Colors, type, spacing, radius, and shadow now come from a token file. Components still reference them. Screen, dark, and print look the same as 1.2.4.",
                "Chinese and English HTML still embed the stylesheet in a single file and do not load a font from the network.",
            ],
            tokens["en"],
        )
```

用上面这一段替换原来从 `self.assertEqual("1.2.5", self.manifest["version"])` 到刀 B 那两句英文结束的整段。不要两段并存。替换之后，文件里不应再有把刀 B 的句子赋给 `entry` 的断言。

`typography`、`batch4`、`batch3`、`guide`、`previous` 后面的句子列表保持文件里的原文。只是它们现在分别核对 `entries[2]` 到 `entries[6]`。1.2.4 的排版两句、1.2.3 的 Batch4 两句、1.2.2 的两句、1.2.1 的两句、1.2.0 的两句都不要改写。

用下面这一段替换原来的 README 断言。原来以句号结尾的 `也不要把 1.2.4 的产物标成 1.2.5。` 不要留下，那一句在 README 里会改成逗号：

```python
        self.assertIn("当前版本：**v1.2.6 · 2026-10-25**", readme)
        self.assertIn("版本号已经是 1.2.6。", readme)
        self.assertIn("样式来自 `stm32-book/styles/tokens.json` 和 `stm32-book/styles/book.css`，构建时拼进 HTML 的 `<style>`，`dist/` 里不另放 CSS。", readme)
        self.assertIn("也不要把 1.1.1 的产物标成 1.2.0，", readme)
        self.assertIn("也不要把 1.2.0 的产物标成 1.2.1，", readme)
        self.assertIn("也不要把 1.2.1 的产物标成 1.2.2，", readme)
        self.assertIn("也不要把 1.2.2 的产物标成 1.2.3，", readme)
        self.assertIn("也不要把 1.2.3 的产物标成 1.2.4，", readme)
        self.assertIn("也不要把 1.2.4 的产物标成 1.2.5，", readme)
        self.assertIn("也不要把 1.2.5 的产物标成 1.2.6。", readme)
        self.assertIn("打 tag `v1.2.6`", readme)
        self.assertNotIn("当前版本：**v1.2.5", readme)
        self.assertNotIn("打 tag `v1.2.5`", readme)
```

`也不要把 1.2.4 的产物标成 1.2.5` 这句保留。它后面从句号改成逗号，因为后面还要接 1.2.5 到 1.2.6 那一句。

- [ ] **Step 2: 插入修订条目**

在 `stm32-book/revisions.json` 的 `entries` 最前插入。已有的 1.2.5 条目及其后的句子一字不改。两个空格缩进，和文件里的现有条目一样：

```json
    {
      "version": "1.2.6",
      "date": "2026-10-25",
      "zh": [
        "封面图不再写英文眉题，板卡外框加了一道内线；发光的灯点改成平涂。中英文仍共用这一张图。",
        "标题板把书名放在书脊短线上面。扉页标题改用章标题的字号，并在标题下重复这条书脊短线。"
      ],
      "en": [
        "The cover drawing no longer carries an English kicker. The board frame gains an inner rule, and the glowing lamp is flat. Both languages still share this drawing.",
        "The title plate places the title above the spine rule. The imprint heading uses the chapter title size and repeats that spine rule."
      ]
    },
```

不在修订说明里写刀 C，也不写章节名。

- [ ] **Step 3: 改两份 manifest 和 README**

`stm32-book/manifest.json` 和 `stm32-book/manifest-en.json` 只改这两处：

```json
  "version": "1.2.6",
  "date": "2026-10-25",
```

`date` 已经是 `2026-10-25` 时，这一行可以不出现在 diff 里。不要改 `title`、`subtitle` 或其他字段。

`stm32-book/README.md` 当前版本句改成：

```markdown
当前版本：**v1.2.6 · 2026-10-25**。中文整书和英文整书共用这一版号。GitHub Release 仍要等这次提交进入 `main` 且 Book CI 产出四份文件之后，由有权限的人另行处理。
```

构建节里关于 `tokens.json` 和 `book.css` 的那一句保留：

```markdown
样式来自 `stm32-book/styles/tokens.json` 和 `stm32-book/styles/book.css`，构建时拼进 HTML 的 `<style>`，`dist/` 里不另放 CSS。
```

发布节的版本句改成下面这一整句。前面的误标分句保留，原来 1.2.4 到 1.2.5 那句末尾的句号改成逗号，再接新的一句：

```markdown
版本号已经是 1.2.6。构建脚本不会自己创建 GitHub Release。不要把 rc.8（`0c24f76`）的产物标成 1.0.0，也不要把 1.0.7 的产物标成 1.0.8，也不要把 1.0.8 的产物标成 1.1.0，也不要把 1.1.0 的产物标成 1.1.1，也不要把 1.1.1 的产物标成 1.2.0，也不要把 1.2.0 的产物标成 1.2.1，也不要把 1.2.1 的产物标成 1.2.2，也不要把 1.2.2 的产物标成 1.2.3，也不要把 1.2.3 的产物标成 1.2.4，也不要把 1.2.4 的产物标成 1.2.5，也不要把 1.2.5 的产物标成 1.2.6。
```

第三步的「在该提交上打 tag `v1.2.5`」改成「在该提交上打 tag `v1.2.6`」。这一步仍不创建 tag，也不创建 Release。四份文件名保持不动。不改 `CREDITS.md`。

- [ ] **Step 4: 跑版本测试，确认通过，然后提交**

先改完 Step 1 到 Step 3，再跑下面两条。只改了测试、还没改 `revisions.json` 和两份 manifest 时，这两条会失败。这是 `validate_revisions()` 的预期，不要把修订句子改短来迁就。

Run:

```bash
python3 stm32-book/tests/test_build.py BookBuildContractTests.test_visual_polish_version_is_1_2_0 -v
python3 stm32-book/tests/test_build.py BookBuildContractTests.test_revision_file_lists_1_0_0_through_manifest_version -v
```

Expected: 两条都通过。

```bash
git add stm32-book/tests/test_build.py stm32-book/manifest.json stm32-book/manifest-en.json stm32-book/revisions.json stm32-book/README.md
git commit -m "book: 把整书标成 1.2.6"
```

同一提交必须同时含测试和四份版本文件。`validate_revisions()` 不允许只改一边。

---

### Task 6: 验收封面与扉页，并停在合入前

**Files:**
- Test: 整套 `stm32-book/tests`，外加中文和英文 `--check`，再加一次人工看构建出的 HTML
- 不新开测试文件，不改 `.github/workflows/book.yml`

**Interfaces:**
- Consumes: Task 2 的图、Task 3 的标题板、Task 4 的扉页 CSS、Task 5 的 `1.2.6`。
- Produces: 实施 PR 可以请求合入时的证据。这一步没有新的功能提交。若 diff 检查发现越界文件，撤回那些文件后再提交一次，提交说明写明撤回了哪一处。

- [ ] **Step 1: 跑设计规格里的三条命令**

Run:

```bash
python3 -m unittest discover stm32-book/tests -v
python3 stm32-book/build_html.py --check
python3 stm32-book/build_html.py --lang en --check
```

Expected: 三条退出码都是 0。`discover` 的末尾是 `OK`。两条 `--check` 都不打印 `revision history starts at`。`test_css_token_extract_contract` 里的 SHA-256 是 `a4ccd1403ab742e82f67c39053c2609da1c9a8afa126d4f6b988a5b9559a5ac4`，除非开工条件里的停手条件已经触发。

Book CI 的 `book` 作业还会跑 `python stm32-book/build_html.py --pdf`，`book-en` 作业跑 `python stm32-book/build_html.py --lang en --pdf`。本地这三条过了再推。不要改 workflow。Python 版本在 CI 里是 3.13。

`--check` 不留下 `stm32-book/dist/`。人工抽看时再构建一次：

```bash
python3 stm32-book/build_html.py
python3 stm32-book/build_html.py --lang en
```

Expected: 写出 `stm32-book/dist/stm32-practical-book.html` 与 `stm32-book/dist/stm32-practical-book-en.html`。`stm32-book/dist/` 已在 `.gitignore` 里。不要 `git add` 这两份 HTML。

- [ ] **Step 2: 看 diff 边界**

Run:

```bash
git diff --name-only origin/main...HEAD
```

实施分支的 `origin/main` 应已含本计划。Expected: 只有这八个路径：

```text
stm32-book/README.md
stm32-book/build_html.py
stm32-book/cover.svg
stm32-book/manifest-en.json
stm32-book/manifest.json
stm32-book/revisions.json
stm32-book/styles/book.css
stm32-book/tests/test_build.py
```

多出来的 `docs/` 正文、`docs/en/`、`CONTENT_GUIDE.md`、`stm32-book/styles/tokens.json`、仓库根 `assets/`、`tools/`、`CREDITS.md`、`.github/workflows/book.yml` 或 `requirements.txt`，撤回那些文件后再提交一次。

Run:

```bash
git diff --stat -- docs docs/en stm32-book/styles/tokens.json assets tools .github/workflows/book.yml stm32-book/requirements.txt
```

Expected: 无输出。`docs/superpowers/plans/` 不在这条命令里。本计划文件如果还没在 `main` 上，它可以出现在实施分支里，但实施 PR 的最终 diff 不必再改它。

Run:

```bash
git diff -U0 -- stm32-book/manifest.json stm32-book/manifest-en.json
git diff -U0 -- stm32-book/build_html.py
```

Expected: 两份 manifest 只有 `version`（以及当时需要改的 `date`）。`build_html.py` 只有 `.cover-panel` 里 `<hr class="rule">`、`<h1>`、副题这几行的位置变化。

Run:

```bash
grep -n 'OFFLINE EDITION\|<text\|opacity="0.18"' stm32-book/cover.svg || true
grep -n 'imprint h1' stm32-book/styles/book.css
grep -n -E '9\.5pt|9pt|--table-columns|14vw|5\.6vw|rgba\(16, 24, 32' stm32-book/styles/tokens.json || true
grep -n -E '9\.5pt|--table-columns|rgba\(16, 24, 32, \.18\)|#10242e|clamp\(2\.15rem, 5\.6vw, 3\.7rem\)' stm32-book/styles/book.css
```

Expected: 第一条没有匹配。第二条是三行：`.imprint h1, .companion h2` 仍只有 `margin-top: 0`；`.imprint h1` 含 `font-size: var(--type-h1)`；`.imprint h1::after` 含 `width: 4.2rem` 和 `height: .18rem`。第三条没有匹配。第四条有匹配。封面 `clamp`、印刷 `9.5pt`、图注 `9pt`、`.toc-jump` 的 `rgba(16, 24, 32, .18)`、画板 `#10242e` 和 `--table-columns` 留在 `book.css`。

Run:

```bash
git tag --points-at HEAD
```

Expected: 无输出。不要运行 `gh release create`，不要 `git tag`，不要打 `v1.2.6`。

确认这些断言还在：

```bash
grep -n -E '0x271|167 ns|len\(outline\)' stm32-book/tests/test_build.py
```

Expected: `0x271`、`167 ns` 和 `self.assertEqual(44, len(outline))` 仍有匹配。

- [ ] **Step 3: 打开构建出的 HTML**

中文文件是 `stm32-book/dist/stm32-practical-book.html`。看这几处：

- 封面：深色底上仍是一块板，图里没有字；外框里面有一道细线；灯点没有光晕。标题板是浅底，左条仍是 spine。书名在短线上面，副题在短线下面。书名仍是「STM32 实战：从点亮一颗灯到交付一个系统」，副题仍是「29 章证据驱动的嵌入式入门与工程手册」。眉题仍是「STM32 实战手册」。
- 暗色：标题板仍是浅底，板卡仍是深底。翻到版权页，页面跟随暗色，短线不是一块浅色标题板。
- 扉页：眉题仍是「版权页」，标题仍是「版本与许可」。标题下有一条短的书脊色线。宽窗口里定义列表至少两列，窄于 960px 时是一列。句子不改。
- 印刷预览：封面单独成页，深色底仍印出来。版权页不另写 `page-break-before: always`。
- 第 00 章的 `h2` 左边条仍在。这是确认哈希变化没有把令牌填坏。不要求把 29 章逐页看完。

英文文件是 `stm32-book/dist/stm32-practical-book-en.html`。图与中文相同。眉题是「STM32 PRACTICAL BOOK」，扉页眉题是「COLOPHON」，标题是「Version and license」。两份 HTML 各有一个 `<style>`，没有 `<link`，也不含 `fonts.googleapis`。

看不了浏览器时，在实施 PR 说明里写明已经由 `test_cover_imprint_d_contract`、`test_cover_svg_stays_self_contained`、`test_typography_e_css_contract` 和 `test_visual_polish_css_contract` 覆盖图、标题板顺序、扉页字号、短线、封面 `clamp`、`coverLock` 和 `3px`，并注明人工抽看没有做。不要为了抽看去改测试、SVG 或 CSS。

- [ ] **Step 4: 开实施 PR 并停住**

实施 PR 从本计划已经合入的 `main` 另开分支。标题写明这是封面与扉页 D 的实施，不是本计划。说明里写上：

- 中英文仍共用一张 `cover.svg`。图内没有 `OFFLINE EDITION`，外框内有一道 `#d7c4a3` 细线，灯点没有 `opacity="0.18"` 的光晕。
- 标题板的书名在 `hr.rule` 上面，副题在下面。文案没有改。
- 扉页 `h1` 使用 `var(--type-h1)`，下面有一条 `4.2rem` × `.18rem` 的 `::after` 书脊短线。`tokens.json` 的 diff 为空，`schema` 仍是 1。
- 拼好的 `CSS` SHA-256 是 `a4ccd1403ab742e82f67c39053c2609da1c9a8afa126d4f6b988a5b9559a5ac4`。若开工条件的停手条件触发过，改写实际的旧哈希和新哈希。
- 版本是 1.2.6 · 2026-10-25。三条本地命令都通过。`book` 与 `book-en` 都变绿之后 squash 合入 `main`。不设章节 HTML 的第二次人审。
- 合入后在本机 `D:\Users\STM32` 拉取这次 `main`。拉取不产生仓库 diff。
- 不打 tag，不创建 GitHub Release。
- 刀 C 不在这个 PR 里。

实施者自己不按合并按钮，不跑 `gh pr merge`。CI 还红时不合入。CI 变绿后由协调员 squash 合入。

最终 diff 必须同时有封面图、标题板顺序、扉页 CSS 和版本戳。不要把仍锁着 `e0fb6605…` 的测试留成 PR 的最终内容。

这一步在验收已经通过时没有新的提交。

## 风险

这些都是设计规格里的风险。实施时按这里停，不要在封面 PR 里顺手改版式。

- **扉页规则多一个空格，新哈希就会对不上。** 对不上时改回 Task 4 的那两行原文。不要改期望哈希来迁就另一份 CSS，也不要改令牌。SVG 和 HTML 顺序不参与这个哈希。
- **若把 `font-size` 写进 `.imprint h1, .companion h2`，配套资源的标题会变成章标题字号。** 字号只放在单独的 `.imprint h1` 规则上。Task 1 断言组合选择器不含 `font-size`。
- **若把画板三色收进 `light`，暗色会把深色封面换成暗色纸。** 它们留在 `book.css`。`coverLock` 继续只锁标题板那六色。不要把 `schema` 改成 2，不要加 `coverBoard`。
- **若给 `.imprint` 也做一套 `coverLock`，版权页在暗色下会变成浅底。** 扉页跟随暗色 token。两条短线在暗色下可以一个是 `#c4552a`、一个是 `#f0b090`。
- **若把书名写进 SVG，中英文就要分两张图。** 图内不放文字。书名仍在标题板的 `h1` 里。`.cover-art` 继续带 `aria-hidden="true"`。
- **若重绘芯片、引脚或迹线，这一刀就变成刀 C 的样本图。** SVG 只删一行字、删一个光晕圆、加一道内框。Task 2 的字节旁证是 3880。
- **若改封面 `clamp` 来收进 token，刀 E 的测试会失败，哈希也会离开本文件给出的值。** `clamp` 保持原文。分部页、`.toc-jump`、印刷 pt、`--table-columns` 也不碰。

## 对照设计规格

| 设计规格里的要求 | 落在 |
| --- | --- |
| 一份无文字的铜版，中英文共用 `cover.svg`；删 `OFFLINE EDITION`，删 `opacity="0.18"`，加同色内框 | Global Constraints，Task 2 |
| 内框 `x="34" y="44"`，外框与 `translate(148 114)` 保持；16 个十六进制不变；UTF-8 ≤ 8192 | Task 1，Task 2 |
| 标题板顺序改为眉题、书名、短线、副题、版本行；表达式不改 | Task 3 |
| `.cover` 的 `coverLock` 继续让标题板在暗色下保持浅底 | Global Constraints，Task 1 的暗色断言 |
| 扉页 `h1` 用 `var(--type-h1)` 与 `line-height: 1.22`；`::after` 为 `4.2rem` × `.18rem` 的 `var(--spine)` | Task 4 |
| 不把字号写进 `.imprint h1, .companion h2`；不改 `imprint_html` 和 `dl` | Task 4，Task 1 |
| 画板三色、封面 `clamp`、分部页字号、`.toc-jump`、印刷 pt、`--table-columns` 留在原处 | Global Constraints，Task 1，Task 6 的 `grep` |
| `schema` 仍是 1；`coverLock` 六个名字不变；不改 `load_css` | Task 1，Task 4，Task 6 |
| 新哈希 `a4ccd1403ab742e82f67c39053c2609da1c9a8afa126d4f6b988a5b9559a5ac4`；基线变了才重算 | 开工条件，Task 1，Task 4 |
| 四个既有视觉方法不改也通过 | Global Constraints，Task 1 Step 3，Task 4 |
| `test_cover_svg_stays_self_contained` 去掉两行 `<text` 坐标断言 | Task 1 |
| 建议版本 1.2.6；高于 1.2.5 时写下一条修订号；日期在本计划里冻成 2026-10-25 | 开工条件，Task 5 |
| 修订四句；README 保留 1.2.4 到 1.2.5 的误标句，再加 1.2.5 到 1.2.6 | Task 5 |
| 版本断言后移；1.2.5 的刀 B 两句改去 `entries[1]` | Task 5 |
| 中英 `--check` 与 unittest 通过后，`book` 与 `book-en` 变绿再 squash；不打 tag | Task 6 |
| 不改 workflow、不改 `requirements.txt`、不改正文、不改 `tokens.json`、不改 `assets/`、不实施刀 C | Global Constraints，Task 6 |
| 书签 44、`0x271`、`167 ns`、三档 `pageOverflow` 不放宽 | Task 6 |
| 人工看封面、暗色、扉页、印刷和第 00 章的 `h2`；英文看封面和版权页 | Task 6 Step 3 |
| 本设计之后的实施计划单独成 PR，不在设计 PR 里写 | 本文件。本计划 PR 只新增这一份 |

## 执行交接

本文件所在的 PR 只审阅计划，不实施封面或扉页。它不升版本，不改 `cover.svg`，不改 `book.css`，不改 `build_html.py`。CI 变绿不等于可以自动合入。

实施要等本计划合入 `main`，并且 `stm32-book/manifest.json` 的 `version` 仍是 `1.2.5`、`date` 仍是 `2026-10-25`（或按开工条件已经更高）。然后从那个 `main` 另开分支，按任务顺序做。两种走法：

1. Subagent-Driven：每个任务一个新的执行者，任务之间再审一遍 diff。
2. Inline：同一会话里用 executing-plans，做完一个任务再进下一个。

Task 1 的提交会使整套测试变红。Task 4 结束时测试应重新全绿，版本仍是 1.2.5。实施 PR 要等到 Task 6 三条命令都退出码 0 再开。协调员在 `book` 与 `book-en` 都变绿后 squash 合入。不设章节人审停点。不打 tag，不创建 Release。

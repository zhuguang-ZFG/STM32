# 整书观感抛光 1.2.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 只抛光整书观感：把 `stm32-book/build_html.py` 里的内联 CSS 收到同一组 token 和间距阶梯，封面 `cover.svg` 只拉开留白，合入时把整书标成 **1.2.0 · 2026-10-25**，Book CI 变绿后由协调员 squash 合入。

**Architecture:** 样式仍是 `build_html.py` 里的一个 `CSS` 字符串，从 `:root` 到 `@media print`。先在 `stm32-book/tests/test_build.py` 里把新 token、关键选择器、对比和版本 1.2.0 写成会失败的断言，再改 CSS，再只平移封面组，最后改两份 manifest、`revisions.json` 和 `stm32-book/README.md`。分类函数、罗盘 HTML、书签和章号不动。不新开 `.css`，不新开 token JSON，不新开测试文件。

**Tech Stack:** Python 3 标准库、现有 `stm32-book/build_html.py`、`python3 stm32-book/tests/test_build.py`、`python3 -m unittest discover stm32-book/tests -v`。对比度在测试文件里用 WCAG 相对亮度计算。不新增依赖，不改 `requirements.txt`。

`stm32-book/tests/` 不是 Python 包。单条测试写成 `python3 stm32-book/tests/test_build.py BookBuildTests.<方法名> -v`。不要写成 `python3 -m unittest stm32-book.tests...`。整套测试仍用 `python3 -m unittest discover stm32-book/tests -v`。

实施基线是本计划合入之后的 `main`。写本计划时 `main` 是 `679ad73036853d1ab8ea3dee54941a7f31816758`（`docs: 整书观感抛光 1.2.0 设计规格 (#25)`）。整书版本仍是 1.1.1，日期仍是 2026-10-25。下面引用的 `build_html.py` 行号属于这一尖端；本计划只新增本文件，不挪那些行。实施从合入后的 `main` 另开分支。不要在本计划的分支上改 CSS、封面或版本。

设计规格：`docs/superpowers/specs/2026-10-25-book-visual-polish-1.2.0-design.md`。

## Global Constraints

- 只动 `stm32-book/build_html.py` 内联 CSS + `cover.svg` 留白微调（不改构图/填色叙事）；版本 bump 到 **1.2.0 · 2026-10-25**（manifest 中英、revisions.json、README）。
- 不做：改正文 Markdown、拆独立 css、重绘 sample/GIF、碰海报/check_assets、图目录、打 tag/Release。
- 视觉：token 对比与间距阶梯；排版行高/页边/h2；组件 compass/callout/source-card/part-divider/figure；暗色+print 保留 orphans/widows 与 figcaption avoid。
- 验收：中英 `--check` PASS；测试锁关键选择器/CSS 片段；CI 绿后 **自动 squash 合入**。

上一句「CI 绿后自动 squash 合入」指观感实施 PR。本计划文件的 PR 等人审阅，不在 CI 变绿后自动合入。

以下与上面并列，来自已合入规格，实施时同样生效：

- 亮色保持 `--paper: #fbfaf7`、`--ink: #17202a`、`--accent: #075e84`、`--muted: #5e6872`、`--warn: #9a3d1c`、`--tip: #1b5c45`、`--spine: #c4552a`。暗色那一行保持 `--paper: #11171b`、`--ink: #e9eef1`、`--accent: #78c8e8`、`--muted: #acb7bf`、`--warn: #f0b090`、`--tip: #8fd4b4`、`--spine: #f0b090`。印刷保持 `--paper: #fff`、`--ink: #111`、`--muted: #444`、`--accent: #075e84`、`--spine: #c4552a`。
- 列表标记计算色保持 `rgb(7, 94, 132)`。`h2` 左边框保持 `3px`。屏幕上 `figure` 上边框保持 `1px` 且填充不是透明；印刷时 `figure { background: transparent; }` 这句原样留着。`blockquote.callout` 的左边条保持 `4px`。
- `.closing-banner` 与 `.compass-boundary .compass-role` 的字色改为 `var(--warn)`。`.compass-boundary` 的 `border-top-color` 继续是 `var(--spine)`。封面左条、封面短横、分部页顶边继续是 spine。
- 新增且只新增这些自定义属性：`--space-bar: 0.75rem`、`--space-paragraph: 1.25rem`、`--space-figure: 1.5rem`、`--space-chapter: 3.5rem`、`--inset: 6%`、`--leading-body: 1.75`、`--tracking-body: 0.01em`、`--tracking-kicker: 0.14em`、`--radius: 0.7rem`、`--elev: 0 1px 2px color-mix(in srgb, var(--ink) 8%, transparent)`。
- 窄于 720px 时，章、附录、分部、文前、目录、扉页和封面标题板的左右 padding 仍是 `1rem`。`--inset` 不进入这一档。
- `.toc-jump` 的定位、`border-radius: 999px` 和 `box-shadow: 0 .45rem 1.2rem rgba(16, 24, 32, .18)` 保持原句。`a` 的 `text-underline-offset: .18em` 不是字距，保持。`.source-id` 与 `.source-card dt` 的 `letter-spacing: .04em` 保持。
- 出版书签仍是 44 条。不删 `0x271`、`167 ns`、样本章和 batch2 的断言。不改 `docs/`、`docs/en/`、`CONTENT_GUIDE.md`、`assets/`、`tools/`、`CREDITS.md`、海报。
- 修订说明只用规格里的四句。不写 CONTENT_GUIDE，不写 Batch3。保留 1.1.1 及更早条目。不打 `v1.2.0` tag，不创建 GitHub Release。
- 测试只改 `stm32-book/tests/test_build.py`。不新开测试文件，不新开浏览器用例。印刷继续用已有的第 27 章用例。

## 现状注意

规格作者对 `679ad73` 的观察，实施时按此核对，不要当成待改的另一套设计：

1. CSS 全在 `build_html.py` 内联字符串。`CSS = r"""` 在第 954 行，字符串在第 1191 行结束。没有独立 `.css`，也没有 design-token JSON。
2. 列表标记色锁 `rgb(7, 94, 132)`；`--spine: #c4552a` 多处锁定；`.closing-banner` 与 `.compass-boundary .compass-role` 用 spine 时对比偏弱。实测 spine `#c4552a` 对纸色 `#fbfaf7` 约 4.30，对 `--spine-soft: #f8efe8` 约 3.95。`--warn: #9a3d1c` 对纸色约 6.58。
3. 封面标题板另有近色：`.cover-panel` 的 `#f7f4ee`、`#5c6570`、`#d7d0c4`，副题 `#24323c`，标题 `#10242e`。`cover.svg` 无 `<style>`，可动留白不可动构图填色。画板 `#10242e` 与 `.cover-art` 的 `#0c1c24` 继续写死。
4. 圆角多档：`.5rem`、`.55rem`、`.65rem`、`.7rem`、`.75rem`、`.8rem`。`h2` 左边条 `3px`、`figure` 上边框 `1px` 被 `test_narrow_desktop_stacks_compass_without_part_number_collision` 锁住。内层 `.compass-card` 的 `.5rem` 不在规格的共用圆角名单里，保持 `.5rem`。`:not(pre) > code` 的 `.3em` 保持。
5. print 已有 `orphans: 3`、`widows: 3` 与 `figcaption` 的 `break-before: avoid-page`——校对保留，勿重写分页。`@page { size: A4; margin: 16mm 15mm 18mm; }` 保持这组毫米值。

## File map

| 路径 | 这一轮的责任 |
| --- | --- |
| `stm32-book/tests/test_build.py` | 新增观感契约、对比、版本三条测试；Task 4 把现有 `1.1.1` 断言改成 `1.2.0`；Task 3 给封面测试加上留白断言 |
| `stm32-book/build_html.py` | 只改 `CSS` 字符串。第 954 行之前和第 1191 行的结束引号之后不改 |
| `stm32-book/cover.svg` | 只改组的 `translate` 和眉题 `text` 的 `x` |
| `stm32-book/manifest.json` | `version` 改为 `1.2.0`，`date` 保持 `2026-10-25` |
| `stm32-book/manifest-en.json` | `version` 改为 `1.2.0`，`date` 保持 `2026-10-25` |
| `stm32-book/revisions.json` | `entries` 最前插入 1.2.0 |
| `stm32-book/README.md` | 当前版本句、发布节的版本句、tag 名，以及「不要把 1.1.1 的产物标成 1.2.0」 |

`validate_revisions()` 在 `build_html.py` 第 818 行。它要求 `revisions.json` 第一条的 `version` 等于 manifest 的 `version`。Task 4 必须同一提交改这两处，否则 `--check` 失败。

---

### Task 1: 先写下会失败的观感测试和版本测试

**Files:**
- Modify: `stm32-book/tests/test_build.py`（在 `load_builder` 之后加两个函数；在 `BookBuildTests` 里、`test_cover_svg_stays_self_contained` 之前加三个方法）
- Test: `stm32-book/tests/test_build.py`

**Interfaces:**
- Consumes: `BookBuildTests.builder.CSS`（模块全局 `CSS`）、`BOOK_DIR / "manifest.json"`、`BOOK_DIR / "manifest-en.json"`、`BOOK_DIR / "revisions.json"`、`BOOK_DIR / "README.md"`。`setUpClass` 已经把中文 manifest 读进 `self.manifest`。
- Produces: `BookBuildTests.test_visual_polish_css_contract`、`BookBuildTests.test_visual_polish_contrast_clears_4_5`、`BookBuildTests.test_visual_polish_version_is_1_2_0`。后面的任务按这三个名字跑。不要改已有的 `1.1.1` 断言；那些留到 Task 4，否则会和还没升版的文件互相矛盾。

这一提交之后，整套 `discover` 会失败。这是预期。不要开实施 PR，不要 squash。CSS 契约要到 Task 2 才绿，版本契约要到 Task 4 才绿。对比那一条现在就应该绿：现有十六进制已经高于 4.5。

- [ ] **Step 1: 写入相对亮度函数和三条测试**

在 `load_builder` 函数结束之后、`class BookHTMLParser` 之前插入：

```python
def _relative_luminance(hex_color: str) -> float:
    """WCAG 2.x sRGB relative luminance. Accepts #RGB and #RRGGBB."""
    text = hex_color.removeprefix("#")
    if len(text) == 3:
        text = "".join(character * 2 for character in text)
    red, green, blue = (int(text[index:index + 2], 16) for index in (0, 2, 4))

    def channel(value: int) -> float:
        unit = value / 255
        if unit <= 0.04045:
            return unit / 12.92
        return ((unit + 0.055) / 1.055) ** 2.4

    return 0.2126 * channel(red) + 0.7152 * channel(green) + 0.0722 * channel(blue)


def _contrast_ratio(foreground: str, background: str) -> float:
    lighter = max(_relative_luminance(foreground), _relative_luminance(background))
    darker = min(_relative_luminance(foreground), _relative_luminance(background))
    return (lighter + 0.05) / (darker + 0.05)
```

在 `def test_cover_svg_stays_self_contained` 之前插入下面三个方法。`_rule` 用第一个匹配到的规则块。`figure {` 在屏幕段出现一次，在印刷段再出现一次；屏幕断言要先切掉 `@media`。

```python
    def _css_rule(self, css: str, selector: str) -> str:
        match = re.search(rf"{re.escape(selector)}\s*\{{([^}}]*)\}}", css)
        self.assertIsNotNone(match, selector)
        return match.group(1)

    def test_visual_polish_css_contract(self) -> None:
        css = self.builder.CSS
        screen = css.split("@media", 1)[0]
        dark = css.split("@media (prefers-color-scheme: dark)", 1)[1].split("@media", 1)[0]
        printed = css.split("@media print", 1)[1]
        narrow = css.split("@media (max-width: 720px)", 1)[1].split("@media", 1)[0]

        for token in (
            "--paper: #fbfaf7",
            "--ink: #17202a",
            "--accent: #075e84",
            "--muted: #5e6872",
            "--warn: #9a3d1c",
            "--tip: #1b5c45",
            "--spine: #c4552a",
            "--space-bar: 0.75rem",
            "--space-paragraph: 1.25rem",
            "--space-figure: 1.5rem",
            "--space-chapter: 3.5rem",
            "--inset: 6%",
            "--leading-body: 1.75",
            "--tracking-body: 0.01em",
            "--tracking-kicker: 0.14em",
            "--radius: 0.7rem",
            "--elev: 0 1px 2px color-mix(in srgb, var(--ink) 8%, transparent)",
        ):
            self.assertIn(token, screen)

        self.assertIn("line-height: var(--leading-body)", self._css_rule(screen, "body"))
        paragraphs = self._css_rule(screen, ".chapter > p, .appendix > p, .part-closing > p")
        self.assertIn("margin-top: var(--space-paragraph)", paragraphs)
        self.assertIn("margin-bottom: var(--space-paragraph)", paragraphs)
        self.assertIn("letter-spacing: var(--tracking-body)", paragraphs)
        headings = self._css_rule(screen, ".chapter > h2, .appendix > h2, .part-closing > h2")
        self.assertIn("border-left: 3px solid var(--accent)", headings)
        self.assertIn("padding-left: var(--space-bar)", headings)
        self.assertIn(
            "margin: calc(var(--space-figure) + var(--space-paragraph)) 0 var(--space-bar)",
            headings,
        )
        self.assertNotIn("padding-left: var(--space-bar)", self._css_rule(screen, ".source-card h2"))

        for selector in (
            ".chapter-compass",
            "blockquote.callout",
            ".source-card",
            "figure",
            ".quick-check",
            ".companion",
            ".route",
        ):
            block = self._css_rule(screen, selector)
            self.assertIn("border-radius: var(--radius)", block, selector)
            self.assertIn("box-shadow: var(--elev)", block, selector)
            self.assertIn("border: 1px solid var(--line)", block, selector)
        figure = self._css_rule(screen, "figure")
        self.assertIn("margin: var(--space-figure) auto", figure)
        self.assertIn("color-mix(in srgb, var(--panel) 70%, var(--paper))", figure)
        self.assertIn("margin: var(--space-figure) auto", self._css_rule(screen, "img"))
        self.assertIn("margin: 0 auto .55rem", self._css_rule(screen, "figure img"))
        self.assertIn("border-left: 4px solid var(--accent)", self._css_rule(screen, "blockquote.callout"))
        pre = self._css_rule(screen, "pre")
        self.assertIn("border-radius: var(--radius)", pre)
        self.assertNotIn("box-shadow", pre)
        self.assertIn("border-left: 3px solid var(--accent)", pre)
        self.assertIn("tab-size: 4", pre)
        self.assertIn("user-select: text", pre)

        divider = self._css_rule(screen, ".part-divider")
        self.assertIn("padding: 4.5rem var(--inset) 4.5rem", divider)
        self.assertIn("margin-top: var(--space-chapter)", divider)
        self.assertIn("min-height: 52vh", divider)
        self.assertNotIn("border-radius", divider)
        self.assertNotIn("--elev", divider)
        self.assertIn("border-top: 4px solid var(--accent)", divider)

        self.assertIn("color: var(--warn)", self._css_rule(screen, ".closing-banner"))
        self.assertIn("color: var(--warn)", self._css_rule(screen, ".compass-boundary .compass-role"))
        self.assertIn("border-top-color: var(--spine)", self._css_rule(screen, ".compass-boundary"))
        self.assertNotRegex(css, r"letter-spacing:\s*\.(?:12|14|16|18)em")
        self.assertIn("letter-spacing: .04em", css)
        self.assertIn("text-underline-offset: .18em", css)
        self.assertIn("box-shadow: 0 .45rem 1.2rem rgba(16, 24, 32, .18)", css)
        self.assertIn("border-radius: .5rem", self._css_rule(screen, ".compass-card"))

        cover = self._css_rule(screen, ".cover")
        self.assertIn("background: #10242e", cover)
        self.assertIn("color: #f4f1ea", cover)
        for token in (
            "--paper: #fbfaf7",
            "--ink: #17202a",
            "--muted: #5e6872",
            "--warn: #9a3d1c",
            "--line: #d7dce1",
            "--spine: #c4552a",
        ):
            self.assertIn(token, cover)
        panel = self._css_rule(screen, ".cover-panel")
        self.assertIn("background: var(--paper)", panel)
        self.assertIn("color: var(--ink)", panel)
        self.assertIn("padding: 1.8rem var(--inset) 2.6rem", panel)
        self.assertIn("background: var(--spine)", self._css_rule(screen, ".cover-panel::before"))
        self.assertIn("background: var(--spine)", self._css_rule(screen, ".cover .rule"))
        self.assertIn("color: var(--warn)", self._css_rule(screen, ".cover .eyebrow"))
        self.assertIn("color: var(--ink)", self._css_rule(screen, ".cover h1"))
        self.assertIn("color: var(--ink)", self._css_rule(screen, ".cover .subtitle"))
        self.assertIn("color: var(--muted)", self._css_rule(screen, ".cover .edition"))
        self.assertIn("color: var(--muted)", self._css_rule(screen, ".cover .edition strong"))
        self.assertIn("border-top: 1px solid var(--line)", self._css_rule(screen, ".cover .edition"))
        self.assertIn("background: #0c1c24", self._css_rule(screen, ".cover-art"))
        for gone in ("#f7f4ee", "#d7d0c4", "#5c6570", "#24323c"):
            self.assertNotIn(gone, css)

        self.assertIn(".cover-panel { padding: 1.3rem 1rem 1.8rem; }", narrow)
        self.assertNotIn("var(--inset)", narrow)
        self.assertIn("padding-left: 1rem; padding-right: 1rem", narrow)

        for token in (
            "--paper: #11171b",
            "--ink: #e9eef1",
            "--accent: #78c8e8",
            "--muted: #acb7bf",
            "--warn: #f0b090",
            "--tip: #8fd4b4",
            "--spine: #f0b090",
        ):
            self.assertIn(token, dark)

        self.assertIn("orphans: 3", printed)
        self.assertIn("widows: 3", printed)
        self.assertIn("--spine: #c4552a", printed)
        self.assertIn("--paper: #fff", printed)
        self.assertIn("--ink: #111", printed)
        self.assertIn("--muted: #444", printed)
        self.assertIn("--accent: #075e84", printed)
        self.assertIn("figure { background: transparent; }", printed)
        self.assertIn("@page { size: A4; margin: 16mm 15mm 18mm; }", printed)
        self.assertIn("h1, h2, h3, h4 { break-after: avoid-page; page-break-after: avoid; }", printed)
        caption = self._css_rule(printed, "figcaption")
        self.assertIn("break-before: avoid-page", caption)
        self.assertIn("page-break-before: avoid", caption)
        self.assertIn("break-inside: avoid-page", caption)
        self.assertIn("page-break-inside: avoid", caption)
        self.assertIn("box-shadow: none", self._css_rule(
            printed,
            ".chapter-compass,\n  blockquote.callout,\n  .source-card,\n  figure,\n  .quick-check,\n  .companion,\n  .route",
        ))
        pre_print = self._css_rule(printed, "pre")
        self.assertIn("white-space: pre-wrap", pre_print)
        self.assertIn("break-inside: auto", pre_print)
        self.assertNotIn("avoid", pre_print)
        self.assertIn(".imprint { break-before: auto; page-break-before: auto; }", printed)

    def test_visual_polish_contrast_clears_4_5(self) -> None:
        # spine 对纸色不在这张表里。#c4552a 对 #fbfaf7 约 4.30，规格不把它当正文门槛。
        pairs = (
            ("#17202a", "#fbfaf7"),
            ("#075e84", "#fbfaf7"),
            ("#5e6872", "#fbfaf7"),
            ("#9a3d1c", "#fbfaf7"),
            ("#1b5c45", "#fbfaf7"),
            ("#e9eef1", "#11171b"),
            ("#78c8e8", "#11171b"),
            ("#acb7bf", "#11171b"),
            ("#f0b090", "#11171b"),
            ("#8fd4b4", "#11171b"),
            ("#111", "#fff"),
            ("#075e84", "#fff"),
            ("#444", "#fff"),
        )
        for foreground, background in pairs:
            with self.subTest(foreground=foreground, background=background):
                self.assertGreaterEqual(_contrast_ratio(foreground, background), 4.5)

    def test_visual_polish_version_is_1_2_0(self) -> None:
        revisions = json.loads((BOOK_DIR / "revisions.json").read_text(encoding="utf-8"))
        english = json.loads((BOOK_DIR / "manifest-en.json").read_text(encoding="utf-8"))
        readme = (BOOK_DIR / "README.md").read_text(encoding="utf-8")
        entry = revisions["entries"][0]
        self.assertEqual("1.2.0", self.manifest["version"])
        self.assertEqual("2026-10-25", self.manifest["date"])
        self.assertEqual("1.2.0", english["version"])
        self.assertEqual("2026-10-25", english["date"])
        self.assertEqual("1.2.0", entry["version"])
        self.assertEqual("2026-10-25", entry["date"])
        self.assertEqual("1.1.1", revisions["entries"][1]["version"])
        self.assertEqual(
            [
                "整书样式收到同一组纸色、墨色和强调色，章距、段距、图距使用固定阶梯。",
                "章首罗盘、提示框、出处卡和插图共用一档圆角和轻阴影；印刷时的孤行、寡行和图注不断页仍按原规则。",
            ],
            entry["zh"],
        )
        self.assertEqual(
            [
                "The book stylesheet uses one paper, ink, and accent set, with a fixed step for chapter, paragraph, and figure spacing.",
                "Chapter compasses, callouts, source cards, and figures share one radius and a light shadow; print orphans, widows, and caption keep-together rules stay as they were.",
            ],
            entry["en"],
        )
        self.assertIn("当前版本：**v1.2.0 · 2026-10-25**", readme)
        self.assertIn("版本号已经是 1.2.0。", readme)
        self.assertIn("也不要把 1.1.1 的产物标成 1.2.0。", readme)
        self.assertIn("打 tag `v1.2.0`", readme)
        self.assertNotIn("当前版本：**v1.1.1", readme)
        self.assertNotIn("打 tag `v1.1.1`", readme)
```

印刷阴影规则的选择器必须和 Task 2 插入的那一段逐字相同，含换行和两个空格的缩进。`_css_rule` 会按这个选择器找块。

- [ ] **Step 2: 跑这三条，确认红绿符合预期**

Run:

```bash
python3 stm32-book/tests/test_build.py BookBuildTests.test_visual_polish_css_contract -v
```

Expected: 退出码 1。失败信息含 `--space-bar: 0.75rem`。这是第一条还没写进 CSS 的 token。

Run:

```bash
python3 stm32-book/tests/test_build.py BookBuildTests.test_visual_polish_contrast_clears_4_5 -v
```

Expected: 退出码 0，末尾是 `OK`。13 组配对都要过。若某一组低于 4.5，停下来，不要换色相，也不要在这一任务里改 CSS。

Run:

```bash
python3 stm32-book/tests/test_build.py BookBuildTests.test_visual_polish_version_is_1_2_0 -v
```

Expected: 退出码 1。失败信息含 `'1.2.0' != '1.1.1'`。

不要跑 `discover` 当作这一任务的通过条件。`discover` 会因为上面两条失败而退出码 1。

- [ ] **Step 3: 提交失败测试**

```bash
git add stm32-book/tests/test_build.py
git commit -m "test: 锁住观感 token、选择器和 1.2.0 版本"
```

提交后工作区干净。不要把 `build_html.py`、`cover.svg`、manifest、`revisions.json` 或 README 加进来。

---

### Task 2: 改内联 CSS 的 token、间距、组件、暗色和印刷

**Files:**
- Modify: `stm32-book/build_html.py` 的 `CSS` 字符串（第 954–1191 行）
- Test: `stm32-book/tests/test_build.py` 的 `test_visual_polish_css_contract`

**Interfaces:**
- Consumes: Task 1 的 `test_visual_polish_css_contract` 与 `test_visual_polish_contrast_clears_4_5`。
- Produces: 屏幕段含全部新自定义属性；`.chapter > h2, .appendix > h2, .part-closing > h2` 同时含 `border-left: 3px solid var(--accent)` 与 `var(--space-bar)`；罗盘、callout、出处卡、`figure`、`.quick-check`、`.companion`、`.route` 含 `var(--radius)` 与 `var(--elev)`；两条小字用 `var(--warn)`；印刷段仍含 `orphans: 3`、`widows: 3`、`figcaption` 的四条 avoid，以及单独一行 `figure { background: transparent; }`。`test_visual_polish_version_is_1_2_0` 仍然失败。

只替换下面列出的规则。暗色媒体查询那一整行保持第 1154 行的原文，一个十六进制都不改。印刷里下面四行保持原文，一个词都不改：

```css
  @page { size: A4; margin: 16mm 15mm 18mm; }
  body { font-size: 9.5pt; line-height: 1.55; orphans: 3; widows: 3; print-color-adjust: exact; -webkit-print-color-adjust: exact; }
  h1, h2, h3, h4 { break-after: avoid-page; page-break-after: avoid; }
  figcaption { break-before: avoid-page; page-break-before: avoid; break-inside: avoid-page; page-break-inside: avoid; }
  figure { background: transparent; }
```

同样保持原文：`p[align="center"], figure, .chapter-compass, .quick-check, blockquote, .source-card, img { break-inside: avoid-page; page-break-inside: avoid; }`、`pre { white-space: pre-wrap; overflow-wrap: anywhere; break-inside: auto; page-break-inside: auto; }`、`.imprint { break-before: auto; page-break-before: auto; }`、`.toc-jump` 那一行、720px 里 `.cover-panel { padding: 1.3rem 1rem 1.8rem; }` 和 `.imprint, .frontmatter, .contents, .part-divider, .chapter, .part-closing, .appendix, .back-matter { padding-left: 1rem; padding-right: 1rem; }`。

- [ ] **Step 1: 确认 CSS 契约仍然失败**

Run:

```bash
python3 stm32-book/tests/test_build.py BookBuildTests.test_visual_polish_css_contract -v
```

Expected: 退出码 1，失败信息含 `--space-bar: 0.75rem`。若这条已经通过，说明工作区里已经有人改过 CSS，先停，不要叠第二套 token。

- [ ] **Step 2: 在亮色 `:root` 追加 token**

把：

```css
  --measure: 40rem;
  font-family: "Noto Sans CJK SC", "Microsoft YaHei", "PingFang SC", system-ui, sans-serif;
```

换成：

```css
  --measure: 40rem;
  --space-bar: 0.75rem;
  --space-paragraph: 1.25rem;
  --space-figure: 1.5rem;
  --space-chapter: 3.5rem;
  --inset: 6%;
  --leading-body: 1.75;
  --tracking-body: 0.01em;
  --tracking-kicker: 0.14em;
  --radius: 0.7rem;
  --elev: 0 1px 2px color-mix(in srgb, var(--ink) 8%, transparent);
  font-family: "Noto Sans CJK SC", "Microsoft YaHei", "PingFang SC", system-ui, sans-serif;
```

`:root` 里已有的颜色行保持原样，包括 `--spine: #c4552a` 和 `--spine-soft: #f8efe8`。

- [ ] **Step 3: 换封面、间距和排版规则**

把从 `.cover {` 到 `.cover .edition strong` 的这一段换成：

```css
.cover {
  min-height: 92vh;
  padding: 0;
  background: #10242e;
  color: #f4f1ea;
  --paper: #fbfaf7;
  --ink: #17202a;
  --muted: #5e6872;
  --warn: #9a3d1c;
  --line: #d7dce1;
  --spine: #c4552a;
}
.cover-sheet { min-height: 92vh; display: grid; grid-template-rows: minmax(42vh, 1.05fr) auto; }
.cover-art { background: #0c1c24; overflow: hidden; }
.cover-art svg { display: block; width: 100%; height: 100%; }
.cover-panel { position: relative; padding: 1.8rem var(--inset) 2.6rem; background: var(--paper); color: var(--ink); }
.cover-panel::before { content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: .45rem; background: var(--spine); }
.cover .eyebrow { margin: 0; font-weight: 700; letter-spacing: var(--tracking-kicker); font-size: .78rem; color: var(--warn); }
.cover h1 { font-size: clamp(2.15rem, 5.6vw, 3.7rem); line-height: 1.12; margin: .35rem 0 .7rem; max-width: 12em; color: var(--ink); }
.cover .rule { width: 4.2rem; height: .18rem; margin: 0 0 1rem; border: 0; background: var(--spine); }
.cover .subtitle { margin: 0; font-size: clamp(1.05rem, 2.4vw, 1.35rem); max-width: 34em; color: var(--ink); }
.cover .edition { display: flex; flex-wrap: wrap; gap: .35rem 1.1rem; align-items: baseline; max-width: 36rem; margin: 1.6rem 0 0; padding-top: .8rem; border-top: 1px solid var(--line); color: var(--muted); }
.cover .edition strong { color: var(--muted); font-weight: 700; }
```

`.cover` 上的自定义属性盖住暗色 `:root`，标题板因此保持浅底。`.edition strong` 也用 `--muted`，版本数字不再退回 `#10242e`。印刷段里的 `.cover { min-height: 245mm; page-break-after: always; background: #10242e; }` 不要动。

把：

```css
body { margin: 0; background: var(--paper); color: var(--ink); line-height: 1.72; }
```

换成：

```css
body { margin: 0; background: var(--paper); color: var(--ink); line-height: var(--leading-body); }
```

把：

```css
.imprint, .frontmatter, .contents { padding: 4rem 6%; }
.imprint { padding: 4.5rem 6% 5rem; border-bottom: 1px solid var(--line); }
```

换成：

```css
.imprint, .frontmatter, .contents { padding: var(--space-chapter) var(--inset); }
.imprint { padding: var(--space-chapter) var(--inset); border-bottom: 1px solid var(--line); }
```

把这三行的 `letter-spacing: .16em` 换成 `letter-spacing: var(--tracking-kicker)`：

```css
.imprint .kicker { margin: 0 0 .35rem; color: var(--accent); font-weight: 700; letter-spacing: var(--tracking-kicker); font-size: .82rem; }
.revision-history .kicker, .subject-index .kicker { margin: 0 0 .35rem; color: var(--accent); font-weight: 700; letter-spacing: var(--tracking-kicker); font-size: .82rem; }
```

`.index-letter` 那一行的 `letter-spacing: .14em` 换成 `letter-spacing: var(--tracking-kicker)`。其余声明不动，包括 `break-after: avoid`。

把 `.part-divider` 的规则换成：

```css
.part-divider { position: relative; overflow: hidden; min-height: 52vh; display: grid; align-content: center; gap: .35rem; padding: 4.5rem var(--inset) 4.5rem; margin-top: var(--space-chapter); background: linear-gradient(180deg, var(--accent-soft), transparent 72%); border-top: 4px solid var(--accent); border-bottom: 1px solid var(--line); }
```

`.part-divider .part-label` 的 `letter-spacing: .16em` 换成 `letter-spacing: var(--tracking-kicker)`。`h1` 与 `.part-goal` 的 `max-width` 不动。不加圆角，不加 `--elev`。

把：

```css
.chapter, .appendix, .part-closing, .back-matter { padding: 3.4rem 6% 3.6rem; border-bottom: 1px solid var(--line); }
```

换成：

```css
.chapter, .appendix, .part-closing, .back-matter { padding: var(--space-chapter) var(--inset); border-bottom: 1px solid var(--line); }
```

把 `.closing-banner` 换成：

```css
.closing-banner { margin: .8rem 0 0; color: var(--warn); font-weight: 800; letter-spacing: var(--tracking-kicker); font-size: .78rem; }
```

`.chapter-number` 的 `letter-spacing: .14em` 换成 `letter-spacing: var(--tracking-kicker)`。

把：

```css
h2 { font-size: 1.42rem; margin: 2.35rem 0 .6rem; }
.chapter > h2, .appendix > h2, .part-closing > h2 { padding-left: .7rem; border-left: 3px solid var(--accent); }
```

换成：

```css
h2 { font-size: 1.42rem; margin: 2.35rem 0 .6rem; }
.chapter > h2, .appendix > h2, .part-closing > h2 { margin: calc(var(--space-figure) + var(--space-paragraph)) 0 var(--space-bar); padding-left: var(--space-bar); border-left: 3px solid var(--accent); }
```

子组合 `>` 保留。`.source-card h2` 继续是 `margin: 0 0 .3rem`，不加左边条。

在已有的 `max-width: var(--measure)` 那条规则之后追加，不要把字距写进含 `li` 的那条规则：

```css
.chapter > p, .appendix > p, .part-closing > p { margin-top: var(--space-paragraph); margin-bottom: var(--space-paragraph); letter-spacing: var(--tracking-body); }
```

已有规则保持为：

```css
.chapter > p, .appendix > p, .part-closing > p, .frontmatter > p, .imprint-lead, .imprint .colophon,
.chapter li, .appendix li, .part-closing li { max-width: var(--measure); }
```

`footer.book-footer` 的 `padding: 3rem 6% 5.2rem` 不动。书末间距落在 `.back-matter` 上。

- [ ] **Step 4: 换组件圆角、阴影和其余字距**

把下面几行换成新文案。每一行只改圆角、阴影或字距，边框宽度和填充保持。

```css
.chapter-compass { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: .75rem; margin: 1.5rem 0 2.6rem; padding: .95rem; background: var(--panel); border: 1px solid var(--line); border-radius: var(--radius); box-shadow: var(--elev); }
```

`.compass-title` 的 `letter-spacing: .14em` 换成 `letter-spacing: var(--tracking-kicker)`。

`.compass-card` 保持 `border-radius: .5rem`，不加 `--elev`。

`.compass-role` 换成：

```css
.compass-role { margin: 0; font-size: .72rem; font-weight: 800; letter-spacing: var(--tracking-kicker); color: var(--muted); }
```

`.compass-boundary .compass-role` 换成：

```css
.compass-boundary .compass-role { color: var(--warn); }
```

`.compass-boundary { border-top-color: var(--spine); }` 保持。

`.quick-check`、`.companion`、`.route` 换成：

```css
.quick-check { margin: 3rem 0 1rem; padding: 1rem 1.4rem; border: 1px solid var(--line); border-radius: var(--radius); box-shadow: var(--elev); background: var(--panel); }
.companion { margin-top: 2rem; padding: 1rem 1.2rem; border: 1px solid var(--line); border-radius: var(--radius); box-shadow: var(--elev); background: var(--panel); }
.route { border: 1px solid var(--line); border-radius: var(--radius); box-shadow: var(--elev); padding: 1rem 1.2rem; background: var(--panel); }
```

`blockquote.callout` 换成：

```css
blockquote.callout { max-width: var(--measure); margin: 1.25rem 0 1.45rem; padding: .8rem 1rem .9rem 1.05rem; border: 1px solid var(--line); border-left: 4px solid var(--accent); border-radius: var(--radius); box-shadow: var(--elev); background: var(--panel); color: var(--ink); }
```

`.callout-label` 的 `letter-spacing: .14em` 换成 `letter-spacing: var(--tracking-kicker)`。

`img` 与 `figure` 换成：

```css
img { display: block; max-width: 100%; height: auto; margin: var(--space-figure) auto; }
figure { margin: var(--space-figure) auto; padding: .75rem .75rem .65rem; border: 1px solid var(--line); border-radius: var(--radius); box-shadow: var(--elev); background: color-mix(in srgb, var(--panel) 70%, var(--paper)); }
figure img { margin: 0 auto .55rem; }
```

`pre` 规则里只把 `border-radius: .65rem` 换成 `border-radius: var(--radius)`。不要给 `pre` 加 `box-shadow`。左边 `3px`、`tab-size: 4`、滚动渐变和 `user-select: text` 保持。

`.source-card` 换成：

```css
.source-card { min-width: 0; display: flex; flex-direction: column; gap: .3rem; overflow-wrap: anywhere; border: 1px solid var(--line); border-top: 3px solid var(--accent); border-radius: var(--radius); box-shadow: var(--elev); padding: .9rem 1.1rem 1rem; background: color-mix(in srgb, var(--panel) 72%, var(--paper)); break-inside: avoid; }
```

`.source-id` 与 `.source-card dt` 的 `letter-spacing: .04em` 保持。

在 `@media print` 里、`.toc-jump, .back-to-toc, .skip-link { display: none; }` 之前插入。`figure { background: transparent; }` 仍单独成行，不要并进这一条：

```css
  .chapter-compass,
  blockquote.callout,
  .source-card,
  figure,
  .quick-check,
  .companion,
  .route { box-shadow: none; }
```

- [ ] **Step 5: 跑观感测试，版本测试仍应失败**

Run:

```bash
python3 stm32-book/tests/test_build.py BookBuildTests.test_visual_polish_css_contract BookBuildTests.test_visual_polish_contrast_clears_4_5 BookBuildTests.test_code_glossary_and_print_css_keep_reading_units_movable -v
```

Expected: 退出码 0，三条都是 `ok`，末尾 `OK`。

Run:

```bash
python3 stm32-book/tests/test_build.py BookBuildTests.test_visual_polish_version_is_1_2_0 -v
```

Expected: 退出码 1，失败信息含 `'1.2.0' != '1.1.1'`。不要为了让它变绿去改 manifest。

然后跑这两条需要浏览器的既有测试。它们锁 `3px`、`1px`、`rgb(7, 94, 132)`、印刷图填充透明、孤行和寡行：

```bash
python3 stm32-book/tests/test_build.py BookBuildTests.test_narrow_desktop_stacks_compass_without_part_number_collision BookBuildTests.test_print_layout_keeps_reading_units_together -v
```

Expected: 退出码 0。若本机没有 Playwright 可用的 Chrome 或 Edge，这两条会在启动浏览器时报错。先安装仓库 `requirements.txt` 里已有的 Playwright 并用 `python3 -m playwright install chromium` 装浏览器，再重跑。不要改断言去迁就启动失败。

`git diff -- stm32-book/build_html.py` 里每一处改动都必须落在 `CSS = r"""` 与这个赋值的结束 `"""` 之间。出现函数、书签或 HTML 模板的改动就撤回那一处。

- [ ] **Step 6: 提交样式**

```bash
git add stm32-book/build_html.py
git commit -m "book: 用间距阶梯和同一档圆角收整书样式"
```

---

### Task 3: 封面 SVG 只拉开留白

**Files:**
- Modify: `stm32-book/cover.svg`（两处属性）
- Modify: `stm32-book/tests/test_build.py` 的 `test_cover_svg_stays_self_contained`
- Test: `stm32-book/tests/test_build.py`

**Interfaces:**
- Consumes: 现有 `test_cover_svg_stays_self_contained`。它已经锁 `aria-label="STM32 board"`、`#c4552a`、`#8ecae6`，并禁止 `@font-face`、外链和非 `www.w3.org` 的 URL。这些断言一个都不删。
- Produces: 组变换为 `translate(148 114)`，眉题为 `<text x="112" y="62"`。组内图形的坐标、`fill`、`stroke` 与 Task 2 的 CSS 都不在这一任务的产出里。

留白算术，按 `viewBox="0 0 1200 760"`：

- 左侧接插件是组内 `rect x="-36"`。绿色板卡是 `rect x="0" width="940"`。从接插件左缘到板卡右缘的宽度是 36 + 940 = 976。左右留白 `(1200 - 976) / 2 = 112`。组的 x = 112 + 36 = 148。右缘 148 + 940 = 1088，右侧留白也是 112。
- 绿色板卡 `y="12"`、`height="508"`。上下留白 `(760 - 508) / 2 = 126`。组的 y = 126 - 12 = 114。底缘 114 + 12 + 508 = 634，下侧留白也是 126。
- 眉题现在是 `x="72"`。改成 `x="112"`，与左右留白同一个数。`y="62"`、`fill`、`font-size`、`letter-spacing` 不动。
- 现在的 `translate(118 100)` 让接插件左缘落在 82、板卡右缘留白 142，左右不成对。阴影 `rect` 比板卡向右多 16px，跟着整组平移，不单独改它的 `x`。网格两条 `path` 继续铺满画布，那是底纹，不是板卡。

- [ ] **Step 1: 给封面测试加上留白断言**

在 `test_cover_svg_stays_self_contained` 里、`self.assertIn("--spine: #c4552a", self.builder.CSS)` 之前插入：

```python
        self.assertIn('transform="translate(148 114)"', svg)
        self.assertNotIn('transform="translate(118 100)"', svg)
        self.assertIn('<text x="112" y="62"', svg)
        self.assertNotIn('<text x="72" y="62"', svg)
        self.assertNotIn("<style", svg)
        self.assertIn('fill="#1b5c45"', svg)
        self.assertIn('fill="#ffb020"', svg)
```

已有的 `aria-label`、`#c4552a`、`#8ecae6`、`#9fd7c4` 断言留在原处。

- [ ] **Step 2: 确认留白断言失败**

Run:

```bash
python3 stm32-book/tests/test_build.py BookBuildTests.test_cover_svg_stays_self_contained -v
```

Expected: 退出码 1。失败信息含 `translate(148 114)`。颜色断言还没跑到。不要把整份路径数据写进测试。

- [ ] **Step 3: 只改两处属性**

把：

```svg
  <text x="72" y="62" fill="#8ecae6" font-family="ui-sans-serif, sans-serif" font-size="18" letter-spacing="3.5">OFFLINE EDITION</text>
  <g transform="translate(118 100)">
```

换成：

```svg
  <text x="112" y="62" fill="#8ecae6" font-family="ui-sans-serif, sans-serif" font-size="18" letter-spacing="3.5">OFFLINE EDITION</text>
  <g transform="translate(148 114)">
```

不增删 `<rect>`、`<path>`、`<circle>`、`<g>`。不改任何 `fill`、`stroke`、`opacity`、`rx`、组内 `x`/`y`/`width`/`height`。不加 `<style>`、`<image>`、带 `href` 的 `<use>`、`@font-face`。

- [ ] **Step 4: 确认封面测试通过，并且 diff 只有这两行**

Run:

```bash
python3 stm32-book/tests/test_build.py BookBuildTests.test_cover_svg_stays_self_contained -v
```

Expected: 退出码 0，末尾 `OK`。

Run:

```bash
git diff -U0 -- stm32-book/cover.svg
```

Expected: 只有眉题 `x="72"` 变成 `x="112"`，以及 `translate(118 100)` 变成 `translate(148 114)`。出现第三个图形或任何一个 `fill=` 的改动，就把那一处改回。

- [ ] **Step 5: 提交封面**

```bash
git add stm32-book/cover.svg stm32-book/tests/test_build.py
git commit -m "book: 封面插画只拉开左右和上下留白"
```

---

### Task 4: 把整书标成 1.2.0

**Files:**
- Modify: `stm32-book/manifest.json` 的 `version`
- Modify: `stm32-book/manifest-en.json` 的 `version`
- Modify: `stm32-book/revisions.json` 的 `entries[0]`
- Modify: `stm32-book/README.md` 第 17 行、第 90 行、第 96 行
- Modify: `stm32-book/tests/test_build.py` 里仍写着 `1.1.1` 的当前版本断言
- Test: `BookBuildTests.test_visual_polish_version_is_1_2_0`、`test_revision_file_lists_1_0_0_through_manifest_version`

**Interfaces:**
- Consumes: Task 1 的 `test_visual_polish_version_is_1_2_0`。两份 manifest 的 `date` 已经是 `2026-10-25`，不要改日期，也不要改 `sources`、罗盘或其他字段。
- Produces: 两份 manifest 的 `version` 都是 `1.2.0`。`revisions.json` 的 `entries[0].version` 是 `1.2.0`，`entries[1].version` 仍是 `1.1.1`。`assert_version_history_and_index` 的历史元组以 `1.2.0` 开头，并且 `>1.2.0<` 出现在 `>1.1.1<` 之前。HTML 断言是 `<strong>v1.2.0</strong>`。

- [ ] **Step 1: 确认版本测试仍然失败**

Run:

```bash
python3 stm32-book/tests/test_build.py BookBuildTests.test_visual_polish_version_is_1_2_0 -v
```

Expected: 退出码 1，失败信息含 `'1.2.0' != '1.1.1'`。

- [ ] **Step 2: 收紧已有版本断言**

`assert_version_history_and_index` 里把：

```python
        versions = ("1.1.1", "1.1.0", "1.0.8", "1.0.7", "1.0.6", "1.0.5", "1.0.4", "1.0.3", "1.0.2", "1.0.1", "1.0.0")
        for version in versions:
            self.assertIn(f">{version}<", history)
        self.assertLess(history.index(">1.1.1<"), history.index(">1.1.0<"))
```

换成：

```python
        versions = ("1.2.0", "1.1.1", "1.1.0", "1.0.8", "1.0.7", "1.0.6", "1.0.5", "1.0.4", "1.0.3", "1.0.2", "1.0.1", "1.0.0")
        for version in versions:
            self.assertIn(f">{version}<", history)
        self.assertLess(history.index(">1.2.0<"), history.index(">1.1.1<"))
        self.assertLess(history.index(">1.1.1<"), history.index(">1.1.0<"))
```

`test_revision_file_lists_1_0_0_through_manifest_version` 里的列表改成：

```python
            ["1.2.0", "1.1.1", "1.1.0", "1.0.8", "1.0.7", "1.0.6", "1.0.5", "1.0.4", "1.0.3", "1.0.2", "1.0.1", "1.0.0"],
```

把 `self.assertEqual("1.1.1", manifest["version"])` 改成 `self.assertEqual("1.2.0", manifest["version"])`。

两处 `self.assertIn("<strong>v1.1.1</strong>", html)` 都改成 `self.assertIn("<strong>v1.2.0</strong>", html)`。一处在 `test_build_produces_one_complete_offline_book`，一处在 `test_english_book_is_a_separate_offline_edition`。

不删 `0x271`、`167 ns`、`self.assertEqual(44, len(outline))`，不改样本章和 batch2 测试。

- [ ] **Step 3: 写 1.2.0**

两份 manifest 只改这一行：

```json
  "version": "1.2.0",
```

`date` 保持 `"2026-10-25"`。

在 `stm32-book/revisions.json` 的 `entries` 数组最前面插入，1.1.1 那条原样留在后面：

```json
    {
      "version": "1.2.0",
      "date": "2026-10-25",
      "zh": [
        "整书样式收到同一组纸色、墨色和强调色，章距、段距、图距使用固定阶梯。",
        "章首罗盘、提示框、出处卡和插图共用一档圆角和轻阴影；印刷时的孤行、寡行和图注不断页仍按原规则。"
      ],
      "en": [
        "The book stylesheet uses one paper, ink, and accent set, with a fixed step for chapter, paragraph, and figure spacing.",
        "Chapter compasses, callouts, source cards, and figures share one radius and a light shadow; print orphans, widows, and caption keep-together rules stay as they were."
      ]
    },
```

`stm32-book/README.md` 第 17 行换成：

```markdown
当前版本：**v1.2.0 · 2026-10-25**。中文整书和英文整书共用这一版号。GitHub Release 仍要等这次提交进入 `main` 且 Book CI 产出四份文件之后，由有权限的人另行处理。
```

第 90 行的 `版本号已经是 1.1.1。` 换成 `版本号已经是 1.2.0。`

同一段里，把句号前的「也不要把 1.1.0 的产物标成 1.1.1。」换成「也不要把 1.1.0 的产物标成 1.1.1，也不要把 1.1.1 的产物标成 1.2.0。」整句是：

```markdown
版本号已经是 1.2.0。构建脚本不会自己创建 GitHub Release。不要把 rc.8（`0c24f76`）的产物标成 1.0.0，也不要把 1.0.7 的产物标成 1.0.8，也不要把 1.0.8 的产物标成 1.1.0，也不要把 1.1.0 的产物标成 1.1.1，也不要把 1.1.1 的产物标成 1.2.0。
```

第 96 行的 `打 tag `v1.1.1`` 换成 `打 tag `v1.2.0``。这一步仍不创建 tag，也不创建 Release。

- [ ] **Step 4: 跑版本测试**

Run:

```bash
python3 stm32-book/tests/test_build.py BookBuildTests.test_visual_polish_version_is_1_2_0 BookBuildTests.test_revision_file_lists_1_0_0_through_manifest_version -v
```

Expected: 退出码 0，末尾 `OK`。

- [ ] **Step 5: 提交版本**

```bash
git add stm32-book/manifest.json stm32-book/manifest-en.json stm32-book/revisions.json stm32-book/README.md stm32-book/tests/test_build.py
git commit -m "book: 把整书标成 1.2.0"
```

---

### Task 5: 验收并停在实施 PR

**Files:**
- 不新增文件。只有 Step 2 的 diff 越界时才改回 Task 1–4 允许的文件。

**Interfaces:**
- Consumes: Task 2 的 CSS、Task 3 的封面、Task 4 的 `1.2.0`。
- Produces: 三条验收命令退出码 0。实施 PR 的说明写明协调员会在 Book CI 变绿后 squash 合入 `main`。没有 tag，没有 Release。

- [ ] **Step 1: 跑整套测试和中英检查**

从仓库根目录运行：

```bash
python3 -m unittest discover stm32-book/tests -v
python3 stm32-book/build_html.py --check
python3 stm32-book/build_html.py --lang en --check
```

Expected: 三条都退出码 0。`discover` 的末尾是 `OK`。两条 `--check` 都以成功结束，不打印 `revision history starts at`。不要把 `python3 tools/check_assets.py` 列进这一轮的必跑命令。

`--check` 在临时目录里构建，不留下 `stm32-book/dist/`。人工抽看时再构建一次：

```bash
python3 stm32-book/build_html.py
python3 stm32-book/build_html.py --lang en
```

Expected: 写出 `stm32-book/dist/stm32-practical-book.html` 与 `stm32-book/dist/stm32-practical-book-en.html`。`stm32-book/dist/` 已在 `.gitignore` 里。不要 `git add` 这两份 HTML。

打开中文 HTML，只看三处：封面（板卡、引脚、LED、迹线还在；标题板浅底；左条仍是 spine）；第 00、03、04、06 章里任选一章的罗盘、四块标题左边条、一条 callout、一张 `figure`；附录 E 的 `.source-card`（圆角、顶条、浅底，链接仍是 `<a href>`）。英文书只抽封面或一章。看不了浏览器时，在 PR 说明里写明已经由 `test_narrow_desktop_stacks_compass_without_part_number_collision` 与 `test_print_layout_keeps_reading_units_together` 覆盖 `3px`、`1px`、`rgb(7, 94, 132)`、印刷透明和图注不断页，并注明人工抽看没有做。不要为了抽看去改测试或 CSS。

- [ ] **Step 2: 确认 diff 没有越界**

Run:

```bash
git diff --name-only origin/main...HEAD
```

Expected: 只有这七个路径：

```text
stm32-book/README.md
stm32-book/build_html.py
stm32-book/cover.svg
stm32-book/manifest-en.json
stm32-book/manifest.json
stm32-book/revisions.json
stm32-book/tests/test_build.py
```

多出来的 `docs/` 正文、`docs/en/`、`CONTENT_GUIDE.md`、`assets/`、`tools/check_assets.py`、海报或独立 `.css`，撤回那些文件后再提交一次。提交说明写明撤回了哪一处。`build_html.py` 的 diff 仍只能落在 `CSS` 字符串里。

Run:

```bash
git tag --points-at HEAD
```

Expected: 无输出。不要运行 `gh release create`，不要 `git tag`，不要打 `v1.2.0`。

- [ ] **Step 3: 开实施 PR 并停住**

实施 PR 从本计划合入后的 `main` 另开分支。标题写明这是观感实施，不是本计划。说明里写上：

- 只改了内联 CSS、`cover.svg` 的留白，以及版本 1.2.0。
- 中文和英文 `--check` 都通过，`python3 -m unittest discover stm32-book/tests -v` 通过。
- 协调员会在 Book CI（`.github/workflows/book.yml`，名称 `Book CI`）变绿之后 squash 合入 `main`。
- 合入后在本机 `D:\Users\STM32` 拉取这次 `main`。拉取不产生仓库 diff。
- 不打 tag，不创建 GitHub Release。不再为观感做第二次正文复审。
- CONTENT_GUIDE 与 Batch3 不在这个 PR 里。

实施者自己不按合并按钮，不跑 `gh pr merge`。CI 还红时不合入。

这一步在验收已经通过时没有新的提交。

## 对照设计规格

| 设计规格里的要求 | 落在 |
| --- | --- |
| 样式仍在 `CSS` 字符串，不拆 `.css`，不新增 token JSON | Global Constraints，Task 2 |
| 亮色、暗色、印刷的十六进制保持；对比 ≥ 4.5；spine 不作正文门槛 | Task 1 的对比测试，Task 2 |
| 两条 spine 小字改 `--warn`；色条上的 spine 保持 `#c4552a` | Task 2 |
| 间距四档、`--inset`、行高 1.75、正文字距、眉题字距 0.14em | Task 2 |
| `h2` 左边条仍是 3px，`padding-left` 用 `--space-bar`；callout 左边条仍是 4px | Task 1，Task 2 |
| 罗盘、callout、出处卡、figure、quick-check、companion、route 共用 `--radius` 与 `--elev`；印刷 `box-shadow: none` | Task 2 |
| `.part-divider` 不加圆角和阴影；左右改为 `--inset`；上下 padding 都是 4.5rem | Task 2 |
| `figure` 上边框 1px，浅底不透明；印刷 `figure { background: transparent; }` | Task 1，Task 2，既有窄屏测试 |
| 封面标题板改走 `.cover` 上重设的 token；暗色下保持浅底；`#10242e` 与 `#0c1c24` 写死 | Task 2 |
| `cover.svg` 只调留白和对齐，不改构图和填色 | Task 3 |
| 扉页间距收到 `--space-chapter` 与 `--inset`；窄于 960px 仍是一列 | Task 2；既有窄屏测试锁列数 |
| 印刷孤行、寡行、标题 avoid、图注 avoid、`@page` 毫米值保留 | Task 2 原文保留，Task 1 字符串断言，既有第 27 章测试 |
| 版本 1.2.0 · 2026-10-25，修订四句，README 的 tag 名和「不要把上一版标成这一版」 | Task 4 |
| 不改正文、不重绘图、不加图目录、不打 tag、不发 Release | Global Constraints，Task 5 |
| 出版书签仍是 44；`0x271` 与 `167 ns` 断言仍在 | Task 4，Task 5 |
| 中英 `--check` 与 unittest 通过后，Book CI 变绿再 squash | Task 5 |
| CONTENT_GUIDE 与 Batch3 只点名，不进入 diff | Task 5 的 PR 说明 |

## 执行交接

本文件所在的 PR 只审阅计划，不实施。

实施从本计划合入后的 `main` 另开分支，按任务顺序做。两种走法：

1. Subagent-Driven：每个任务一个新的执行者，任务之间再审一遍 diff。
2. Inline：同一会话里用 executing-plans，做完一个任务再进下一个。

Task 1 的提交会使整套测试变红。实施 PR 要等到 Task 5 三条命令都退出码 0 再开。协调员在 Book CI 变绿后 squash 合入。

# 整书样式抽出 B 设计

日期：2026-10-25  
状态：待人审。人接受这份规格之前不实施  
基线：`main` 上的整书 **v1.2.4**（`f537a94`，PR #38，2026-10-25）  
上一份排版设计：[2026-10-25-book-visual-typography-E-design.md](2026-10-25-book-visual-typography-E-design.md)（PR #35，实施合入 PR #38）。Token 仍写在 Python 字符串里的那一版是 [2026-10-25-book-visual-polish-1.2.0-design.md](2026-10-25-book-visual-polish-1.2.0-design.md)（PR #25，实施合入 PR #27）。  
本文件只记录刀 B 的设计。它不改 `build_html.py`，不新增样式文件，不改正文，不升版本号，不打 tag，不发布 Release，不新增 `docs/superpowers/plans/` 下的实施计划。

整书视觉升级的顺序是 **E → B → D → C**。E 已经在 `f537a94` 合入。本文件只覆盖 B。D、C 在文末点名。

## 背景

1.2.0 用方案 A 把间距、圆角、轻阴影收进内联 `CSS` 的自定义属性。刀 E 在同一段字符串里补了字体栈和字号阶梯。两份设计都写明：不把 CSS 拆出文件，不新增 design-token JSON。刀 B 做的就是当时明确推迟的这一步。抽出是重构，观感保持 1.2.4。

对照 `f537a94` 的 `stm32-book/build_html.py` 核对过的事实：

1. **样式仍是模块级字符串 `CSS`。** 在 `f537a94` 里，赋值位于第 954–1236 行，从 `:root` 到 `@media print` 的结束括号。原始字符串以换行开头、以 `}\n` 结尾，UTF-8 长度 21509，共 282 个换行。SHA-256 是 `e0fb660584f1833e8a6d419ba78ed9d56e4e92e51cbb533430ac8833bcca6bf4`。没有独立 `.css`，没有 design-token JSON。实施时若 `main` 已经向前移动，以 `CSS = r"""` 与收尾 `"""` 之间的原始字符串为准，不以这里的行号为准。
2. **成品 HTML 把这整段放进一处 `<style>`。** 在 `f537a94` 里，第 1554 行是 `<style>{CSS}</style>`。没有 `<link>`。中文 `manifest.json` 和英文 `manifest-en.json` 走同一个 `build_html`，共用这一段 `CSS`。`dist/` 只出 HTML 和 PDF。
3. **离线契约已经有测试。** `audit_html` 要求图片是 `data:image/`，并禁止 `<video`。`test_build_produces_one_complete_offline_book` 禁止 `fonts.googleapis` 和 `fonts.gstatic`。整段 `CSS` 不含 `@font-face`，不含 `url(`。仓库根的 `assets/` 是图、GIF 和视频，构建时内嵌进 HTML，不是样式目录。
4. **自定义属性有 40 个，都写在亮色 `:root`。** 颜色 15 个、尺度 6 个、排版 17 个、圆角 1 个、阴影 1 个。顺序就是下面 JSON 里 `light` 的键序。`--elev` 的值是 `0 1px 2px color-mix(in srgb, var(--ink) 8%, transparent)`，它引用 `--ink`，所以暗色换墨色时阴影跟着变，不必再写一份暗色阴影。
5. **暗色和印刷只重写那 15 个颜色。** 暗色在 `@media (prefers-color-scheme: dark)` 里，整组属性写在同一行 `:root { ... }`。印刷在 `@media print` 里，`:root` 同一行先写 `color-scheme: light;`，再写 15 个颜色。两处都不重写字体、字号、间距、圆角、阴影。刀 E 的测试因此要求印刷段不含 `--font-sans` 和 `--type-body`，暗色段不含这两项，但含 `--code: #0a141c` 与 `--code-ink: #edf6f9`。
6. **`.cover` 再锁 6 个亮色值。** `--paper`、`--ink`、`--muted`、`--warn`、`--line`、`--spine`，数值与亮色 `:root` 相同。暗色查询改的是根上的变量，盖不到这层重设，标题板因此保持浅底。画板 `#10242e`、`.cover-art` 的 `#0c1c24`、封面字色 `#f4f1ea` 仍是字面量。印刷里的 `.cover { background: #10242e; }` 也是字面量。
7. **五段 `@media` 的顺序是测试切片。** 先 `(max-width: 960px)`，再 `(max-width: 720px)`，再 `(prefers-color-scheme: dark)`，再 `(prefers-reduced-motion: reduce)`，最后 `print`。`test_visual_polish_css_contract` 和 `test_typography_e_css_contract` 用第一个 `@media` 之前当屏幕段，用暗色查询到下一个 `@media` 当暗色段，用 `@media print` 之后当印刷段，用 720px 查询到下一个 `@media` 当窄屏段。`_css_rule` 按选择器原文取第一个花括号块。
8. **有一批字面量故意不在这 40 个属性里。** 封面和分部页的 `clamp`、`.part-goal` 的 `1.12rem` / `1.6`、`.part-index` 的 `clamp(4.5rem, 14vw, 8.5rem)` 和窄屏 `3rem`、`.toc-jump` 的 `.85rem` 与 `box-shadow: 0 .45rem 1.2rem rgba(16, 24, 32, .18)`、`.compass-card` 的 `border-radius: .5rem`、行内代码的 `border-radius: .3em`、图和代码上的 `color-mix` 百分比、`figure img` 的 `.55rem`、印刷正文 `9.5pt`、图注 `9pt`、`@page` 的毫米值。刀 E 把前几项留在字面量里。`--table-columns` 是表格 HTML 的内联 `style`，不是设计令牌；术语表用 `[style*="--table-columns: 3"]` 这种属性选择器。
9. **Book CI 不需要为样式单独加作业。** `.github/workflows/book.yml` 的 `book` 作业跑 `python -m unittest discover stm32-book/tests -v`、`python stm32-book/build_html.py --check` 和 `--pdf`，上传中文 HTML 与 PDF。`book-en` 作业跑 `python stm32-book/build_html.py --lang en --pdf`，上传英文 HTML 与 PDF。两边都不上传 CSS。Python 是 3.13。`requirements.txt` 没有 CSS 工具。
10. **版本字面量是 1.2.4。** `revisions.json` 前五条是 `1.2.4`、`1.2.3`、`1.2.2`、`1.2.1`、`1.2.0`，日期都是 `2026-10-25`。两份 manifest 的 `version` 是 `1.2.4`，`date` 是 `2026-10-25`。`stm32-book/README.md` 当前版本句是 **v1.2.4 · 2026-10-25**。发布节写着版本号已经是 1.2.4，tag 名是 `v1.2.4`，误标句子收到「也不要把 1.2.3 的产物标成 1.2.4」。

对比算法与 `stm32-book/tests/test_build.py` 里的 `_contrast_ratio` 相同。这一刀不改色，现有 17 对门槛保持 4.5。

## 目标与非目标

### 目标

- 实施时把 `CSS` 字符串从 `build_html.py` 挪走。令牌值只写在 `stm32-book/styles/tokens.json`。选择器、五段 `@media`、以及上一节第 8 点的字面量留在 `stm32-book/styles/book.css`。构建读这两份文件，填进哨兵，得到与 1.2.4 逐字节相同的字符串，再放进原来的 `<style>{CSS}</style>`。
- 模块级名字仍叫 `CSS`，类型仍是 `str`。现有视觉测试继续读 `self.builder.CSS`，正文不改。
- 中文和英文 HTML 都内嵌这一份结果。`dist/` 不出现 CSS 或 JSON。构建出的 HTML 仍不含 `fonts.googleapis`、`fonts.gstatic`、`@font-face`、`url(`。
- 实施 PR 的建议版本是 **1.2.5**。本设计 PR 不升版本。
- 实施 PR 在 Book CI 变绿之后 squash 合入 `main`。合入后在本机 `D:\Users\STM32` 拉取这次 `main`。拉取不产生仓库 diff。

### 非目标

- 不改任何颜色、字号、间距、圆角、阴影、字体栈、目录规则、代码块、图注、暗色或印刷规则。1.2.4 的观感就是验收面。
- 不把 CSS 拆成多份模块，不引入 Sass、PostCSS、cssutils 或其他新依赖。
- 不把封面画板 `#10242e`、`#0c1c24`、`#f4f1ea`，封面和分部页的展示字号，`.toc-jump` 的字号和投影，`.compass-card` 的 `.5rem`，行内代码的 `.3em`，`color-mix` 的百分比，印刷的 pt 和毫米值，收进 JSON。那些留在 `book.css`。封面图形是刀 D。
- 不改 `cover.svg`，不改 `.cover h1`、`.cover .subtitle`、`.part-divider h1`、`.part-goal`、`.part-index` 的字号和行高。
- 不重绘 `assets/` 里的样本 SVG、动画 SVG 或 GIF，不改 `tools/`。那是刀 C。
- 不把 `--table-columns` 写进令牌表。表格渲染函数继续写内联 `style="--table-columns: N"`。
- 不加 `@font-face`，不写 `url(`，不改成 `<link rel="stylesheet">`。不按语言分两份样式。
- 不改 `docs/00`–`28`、`docs/en/`、附录 Markdown、`CONTENT_GUIDE.md` 中英、罗盘文案、`revisions.json` 里已有句子。本设计 PR 也不改两份 manifest 和 `stm32-book/README.md`。
- 不改 `.github/workflows/book.yml` 的作业、命令和上传路径。
- 不改 `toc_html`、分类函数、罗盘 HTML、书签、章号、`sources` 渲染。`.chapter-compass` 和 `.quick-check` 里继续没有 `h2`。
- 不加图目录或表目录。出版书签仍是 44 条。章号显示仍是文件名前缀加 1。
- 不打 tag，不创建 GitHub Release。
- 不实施文末点名的 D、C。本设计 PR 也不写它们的实施计划。

## 方案

比较过三种布局。

| 做法 | 构建时读什么 | 结果 |
| --- | --- | --- |
| 1. 只把字符串搬进一个 CSS 文件 | 整份 CSS | 文件离开了 Python，颜色仍写在 CSS 里。JSON 若再手抄一份，改令牌要改两处 |
| 2. 按组件拆成多份 CSS，再加 JSON | 按清单拼接 | 运行时仍要拼回一个字符串。五段 `@media` 的顺序被测试切开，拆文件不减少这个约束。当前样式 282 行 |
| 3. 一份 JSON 出值，一份 CSS 放选择器和哨兵 | JSON 填进哨兵，再内嵌 | 值只有一份。拼出来的字符串可以与 1.2.4 逐字节相同 |

采用做法 3。做法 1 把颜色留在 CSS 里。做法 2 仍要维持现在的五段 `@media` 顺序，而刀 D 只会改封面几条规则，刀 C 不改 CSS。1.2.5 不拆模块。以后若要分文件，另写设计。

所有权是一条链：`tokens.json` 的值 → 构建填出的自定义属性 → `book.css` 里的 `var(--*)`。组件不写令牌的十六进制。JSON 不写选择器，也不写媒体查询。

## 文件

实施 PR 新增两个文件，路径固定：

| 路径 | 角色 |
| --- | --- |
| `stm32-book/styles/tokens.json` | 令牌值。UTF-8，无 BOM，两个空格缩进，文件末尾一个换行。键序就是发射顺序 |
| `stm32-book/styles/book.css` | 1.2.4 的 `CSS` 字符串，只把四处声明换成哨兵。第一个字节仍是换行 |

`ROOT` 已是 `build_html.py` 所在目录。加载路径是 `ROOT / "styles" / "tokens.json"` 和 `ROOT / "styles" / "book.css"`。

不放在仓库根的 `assets/`。那个目录是图、GIF 和视频，刀 C 会改它。也不要同时再建一个 `stm32-book/assets/`。

`build_html.py` 删除第 954–1236 行的三引号字符串，改成在同一位置调用加载函数，并赋给模块级 `CSS`。HTML 模板第 1554 行保持 `<style>{CSS}</style>`。加载发生在 import 时，这样 `load_builder()` 之后 `builder.CSS` 已经是拼好的 `str`。不要改成函数，也不要等 `build_html()` 才赋值。

加载只用标准库 `json`。`json.loads` 配 `object_pairs_hook`：同一对象里键重复就抛 `BuildError`，消息含重复的键名。不要 `sort_keys`。不要用 `json.dumps` 生成 CSS。

缺文件、JSON 无效、模式不对、哨兵不是恰好一次，都抛已有的 `BuildError`。消息用英文，带上路径或键名，与现有的 `missing cover art` 一类消息一致。import 失败时 `--check` 和单元测试一起失败。不要捕获后继续用空样式。

## 令牌模式

顶层只有这五个键，顺序如下：`schema`、`light`、`dark`、`print`、`coverLock`。`schema` 是整数 `1`。

`light`、`dark`、`print` 的键都是 CSS 自定义属性名，匹配 `^--[a-z0-9-]+$`。值是字符串。值里禁止换行、回车、分号、花括号、`url(`、`@import`、`@font-face`、`!important`。长度 1 到 500。字体名上的引号属于值的内容，JSON 里按字符串转义。

`light` 的键必须恰好是下面这 40 个，顺序固定。分组只写在这里，不写进 JSON：

- 颜色：`--paper`、`--ink`、`--muted`、`--line`、`--panel`、`--accent`、`--accent-soft`、`--warn`、`--warn-soft`、`--tip`、`--tip-soft`、`--spine`、`--spine-soft`、`--code`、`--code-ink`
- 尺度：`--measure`、`--space-bar`、`--space-paragraph`、`--space-figure`、`--space-chapter`、`--inset`
- 排版：`--leading-body`、`--tracking-body`、`--tracking-kicker`、`--font-sans`、`--font-mono`、`--type-body`、`--type-h1`、`--type-h2`、`--type-h3`、`--type-h4`、`--type-kicker`、`--type-small`、`--type-code`、`--leading-heading`、`--leading-caption`、`--leading-toc`、`--leading-code`
- 圆角和阴影：`--radius`、`--elev`

`dark` 和 `print` 的键必须恰好是那 15 个颜色，顺序与 `light` 里的颜色相同。不要因为印刷的 `--accent`、`--tip`、`--spine` 与亮色相同就省略。印刷段的测试要搜到 `--accent: #075e84` 和 `--spine: #c4552a`。`--warn-soft` 与 `--spine-soft` 在亮色都是 `#f8efe8`，在暗色都是 `#3a241c`，仍然是两个键。

`coverLock` 必须恰好是这六个字符串，顺序固定：`--paper`、`--ink`、`--muted`、`--warn`、`--line`、`--spine`。值不在 `coverLock` 里重复，发射时从 `light` 读取。暗色因此盖不住标题板。不要把 `--accent`、`--panel`、`--code` 加进这六个。

`color-scheme` 不是自定义属性。亮色的 `color-scheme: light dark;` 和印刷的 `color-scheme: light;` 留在 `book.css`。`:root` 上的 `font-family: var(--font-sans);` 也留在 `book.css`，它是引用，不是定义。

下面这份 JSON 就是实施时要写入的文件。值与 `f537a94` 的声明相同。

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

这份 JSON 约束键、顺序和值。两个空格缩进便于阅读；`coverLock` 写成一行或拆开都不影响发射。加载使用解析后的对象，不比较 JSON 文件的字节。

## 哨兵与发射

`book.css` 的制作方式：取出 `f537a94` 里三引号之间的原始字符串（含开头那个换行），只做下面四次替换，其他字节不动。不要用格式化工具重排。

1. 亮色 `:root` 里从 `  --paper: #fbfaf7;` 到 `  --leading-code: 1.65;` 的连续 40 行，换成一行 `  /* @tokens light */`。`color-scheme: light dark;` 和后面的 `font-family: var(--font-sans);` 不动。
2. 暗色媒体查询里的那一整行 `  :root { --paper: #11171b; ... --code-ink: #edf6f9; }`，换成一行 `  /* @tokens dark */`。外层 `@media (prefers-color-scheme: dark)` 不动。
3. 印刷 `:root` 那一行里，从 `--paper: #fff;` 到 `--code-ink: #111;` 的属性串，换成 `/* @tokens print */`。`color-scheme: light; ` 保留，分号后面的那个空格也保留。这一行变成 `  :root { color-scheme: light; /* @tokens print */ }`。
4. `.cover` 规则里那 6 行自定义属性，换成一行 `  /* @tokens cover */`。`background: #10242e;` 和 `color: #f4f1ea;` 留在哨兵前面。

四个哨兵各自恰好出现一次。它们是：

- `  /* @tokens light */`
- `  /* @tokens dark */`
- `/* @tokens print */`
- `  /* @tokens cover */`

发射规则。替换时不要吃掉哨兵后面的换行，替换结果的末尾也不要再加换行。换行只用 `\n`。读文件时不要 `strip()`。

- 亮色和封面用多行。每个属性一行，行首两个空格，形式是 `--名: 值;`。行与行之间一个 `\n`。封面的值按 `coverLock` 的顺序从 `light` 取。
- 暗色换成一行。先写两个空格和 `:root { `，再写各项 `--名: 值;`，项与项之间一个空格，最后写一个空格和 `}`。拼完是 `  :root { --paper: #11171b; --ink: #e9eef1; ... --code-ink: #edf6f9; }`。
- 印刷只替换注释本身。替换结果是 `--paper: #fff; --ink: #111; ... --code-ink: #111;`。项与项之间同样是一个空格，每项自带一个分号。

按这个规则填完，`CSS` 与 `f537a94` 的原始字符串逐字节相同，SHA-256 仍是 `e0fb660584f1833e8a6d419ba78ed9d56e4e92e51cbb533430ac8833bcca6bf4`。哈希对不上时，改加载或哨兵的空白，不要把哈希改成对得上的新值，也不要改令牌的值来迁就格式。

加载函数的签名是 `load_css(tokens_path: Path = TOKENS_PATH, css_path: Path = BOOK_CSS_PATH) -> str`。默认路径指向上面两个文件。测试可以传入临时路径，并且不得因此改写模块级 `CSS`。

`book.css` 源文件里不得出现任何一个令牌名后接冒号，例如 `--paper:`。`var(--paper)` 不含这个子串，可以留下。`[style*="--table-columns: 3"]` 可以留下，因为 `--table-columns` 不是令牌。源文件里的 `#` 颜色只允许 `#10242e`、`#f4f1ea`、`#0c1c24`。`rgba(16, 24, 32, .18)` 留在 `.toc-jump`。

拼好的 `CSS` 里不得残留 `/* @tokens`。`@media` 仍是 5 个，顺序仍是 960、720、暗色、减少动效、印刷。不要新增第六个媒体查询，也不要把暗色或印刷的变量包进新的 `@media`。

## 离线 HTML

中文和英文调用同一次加载结果。不要给 `load_css` 加 `language` 参数。

成品约束：

- 每份 HTML 恰好一个 `<style>`，零个 `<link`。
- `<style>` 与 `</style>` 之间的文本等于模块级 `CSS`。
- 图片仍是 data URI。视频标记仍不进入书。
- `dist/` 的四个产物文件名不变。不把 `styles/` 复制到 `dist/`，也不把 CSS 加进 CI 的上传路径。
- 断网后单个 HTML 文件仍能打开。样式不靠旁边的 `.css`。

`book` 与 `book-en` 两个作业已经会 import 构建脚本。加载失败时两边都会红。这一刀不改 workflow。

## 版本与修订文案

本设计 PR 不改版本。实施 PR 才写。

实施开始时先读 `main` 上的 `stm32-book/manifest.json`。

- `version` 仍是 `1.2.4`：实施版写成 `1.2.5`。
- `version` 已经高于 `1.2.4`：实施版写成下一条修订号，不把本文件里的 `1.2.5` 硬套上去。修订句子仍用下面四句。

日期用实施当天的 ISO 日期。`revisions.json`、两份 manifest、`stm32-book/README.md` 写同一个日期。`validate_revisions` 仍要求修订第一条的版本等于两份 manifest 的 `version`。新条目插在最前，已有句子一字不改。

- `version`: 按上面的规则
- `date`: 实施当天
- `zh`:
  - 整书样式的颜色、字号、间距、圆角和阴影改由一份令牌表提供，组件继续引用它们。屏幕、暗色和印刷的观感与 1.2.4 相同。
  - 中文和英文 HTML 仍把样式内嵌在单个文件里，不引用外部字体。
- `en`:
  - Colors, type, spacing, radius, and shadow now come from a token file. Components still reference them. Screen, dark, and print look the same as 1.2.4.
  - Chinese and English HTML still embed the stylesheet in a single file and do not load a font from the network.

若实施时的上一版已经不是 1.2.4，中文第一句末尾的「1.2.4」改成实施开始时 `main` 上的版本号，英文同样改。不在修订说明里写刀 D、刀 C，也不写章节名。

两份 manifest 只改 `version` 和 `date`。

`stm32-book/README.md`：

- 当前版本句改为 **v{新版本} · {实施日期}**。中英文整书仍共用这一版号。
- 在「构建」一节加一句：样式来自 `stm32-book/styles/tokens.json` 和 `stm32-book/styles/book.css`，构建时拼进 HTML 的 `<style>`，`dist/` 里不另放 CSS。
- 发布节的版本句改为已经是这个版本。tag 名改为 `v{新版本}`。在现有误标句子的最后再加一句「也不要把 {上一版} 的产物标成 {新版本}」。已有的误标句子保留。
- 这一步仍不创建 tag，也不创建 Release。

## 测试

断言仍在 `stm32-book/tests/test_build.py`。不新开测试文件。不增加依赖。

下面四个方法的函数体保持原文，一个断言都不改：

- `test_visual_polish_css_contract`
- `test_typography_e_css_contract`
- `test_visual_polish_contrast_clears_4_5`
- `test_code_glossary_and_print_css_keep_reading_units_movable`

`test_cover_svg_stays_self_contained` 里对 `self.builder.CSS` 的 `--spine: #c4552a` 断言也不改。这些方法在抽出之后仍须通过。它们锁的是拼好的字符串，不是 Python 源文件里的三引号。

新增 `test_css_token_extract_contract`。它核对抽出本身：

- `ROOT / "styles" / "tokens.json"` 与 `book.css` 都存在。`tokens.json` 的顶层键、`schema`、三组键序和 `coverLock` 与上一节的模式一致。
- `book.css` 里四个哨兵各自出现一次。对每个令牌名，源文件不含 `{名}:`。源文件里的十六进制颜色集合恰好是 `#10242e`、`#f4f1ea`、`#0c1c24`。源文件含 `rgba(16, 24, 32, .18)`，含 `--table-columns`，不含 `@font-face`，不含 `url(`。
- `hashlib.sha256(self.builder.CSS.encode("utf-8")).hexdigest()` 等于 `e0fb660584f1833e8a6d419ba78ed9d56e4e92e51cbb533430ac8833bcca6bf4`。
- `self.builder.CSS` 不含 `/* @tokens`。`@media` 出现 5 次。第一次是 `@media (max-width: 960px)`，其后依次能按现有切片找到 720px、暗色、`prefers-reduced-motion` 和 `@media print`。
- `light` 的每个键值在屏幕段（第一个 `@media` 之前）以 `--名: 值` 出现。`dark` 的每个键值出现在暗色切片里。`print` 的每个键值出现在印刷 `:root` 规则里。`.cover` 规则含 `coverLock` 六个键，值等于 `light` 里的同名值。
- 临时目录里各构建一次中文和英文 HTML。两份文件都恰好有一个 `<style>`、零个 `<link`，`<style>` 与 `</style>` 之间等于 `self.builder.CSS`。两份都不含 `fonts.googleapis`、`fonts.gstatic`。

新增 `test_css_token_extract_rejects_bad_tokens`。用临时文件调用 `load_css`，不要改模块级 `CSS`：

- 一份缺少 `--ink` 的 `light`，其余合法，并且 CSS 含四个哨兵。期望 `BuildError`，消息含 `--ink`。
- 一份 `light` 的 `--paper` 值含 `url(`。期望 `BuildError`，消息含 `url(`。
- 同一对象里 `--paper` 出现两次。用原始文本写入这个重复键。期望 `BuildError`，消息含 `--paper`。

版本断言按实施时的实际版本改，不在设计 PR 里改：

- `assert_version_history_and_index` 的元组在 `1.2.4` 前加上新版本，并断言 `>{新版本}<` 出现在 `>1.2.4<` 之前。其后的先后顺序保持。
- `test_revision_file_lists_1_0_0_through_manifest_version` 的列表以新版本起头，下一项仍是 `1.2.4`。
- `test_build_produces_one_complete_offline_book` 和 `test_english_book_is_a_separate_offline_edition` 里的 `<strong>v1.2.4</strong>` 改为新版本。英文 manifest 的版本等式一并改。
- `test_visual_polish_version_is_1_2_0` 改为核对新的第一条。现在对 `entries[0]` 到 `entries[4]` 的句子各后移一位：1.2.4 的排版两句改去核对 `entries[1]`，1.2.3 的 Batch4 两句改去 `entries[2]`，1.2.2 改去 `entries[3]`，1.2.1 改去 `entries[4]`，1.2.0 改去 `entries[5]`。句子原文不改。
- README 断言改为新的当前版本句、`版本号已经是 {新版本}`、新的误标句子，以及 `打 tag \`v{新版本}\``。`也不要把 1.2.3 的产物标成 1.2.4` 这句保留。

不删 `0x271`、`167 ns`、出版书签长度为 44、样本章和各批加厚的断言。`pageOverflow` 为 0 的三档断言不放宽。窄屏列表标记仍是 `rgb(7, 94, 132)`。印刷不断页的现有测试不改期望。

## 工作流与 PR 节奏

刀 B 沿用刀 E 的节奏：设计 PR 等人审阅后再合；实施 PR 在 Book CI 变绿后 squash 合入，不再做第二次正文复审。这一刀不改正文。

### 本 PR（设计）

只新增本文件。不改 `docs/` 章节、`docs/en/`、`stm32-book/`、`assets/`、`tools/`、`CREDITS.md`、`.github/`。不升版本，不打 tag，不发 Release。不新增实施计划。本 PR 等人审阅规格后再合入，不在 CI 变绿后自动合。

### 实施 PR（下一轮，不在本 PR）

顺序固定：

1. **样式文件。** 按上一节写入 `tokens.json` 和 `book.css`。
2. **加载。** 删掉三引号 `CSS`，改为 import 时 `CSS = load_css()`。`<style>{CSS}</style>` 保持。不要在这一步改选择器或令牌值。
3. **测试。** 加上一节的两个方法。四个既有视觉方法不改。版本断言留到下一步一起改。
4. **版本。** 同一 PR 内改 `revisions.json`、两份 manifest、`stm32-book/README.md`，并把版本断言改到实施时的实际新版本。修订说明只用上一节的四句。
5. **验证。** 下面三条通过，并且新测试里的 SHA-256 等于本文件给出的值之后，再请求合入：

```bash
python3 -m unittest discover stm32-book/tests -v
python3 stm32-book/build_html.py --check
python3 stm32-book/build_html.py --lang en --check
```

6. **合入。** `book` 与 `book-en` 都变绿之后，把实施 PR squash 合入 `main`。合入后在 `D:\Users\STM32` 拉取这次 `main`。不打 tag，不创建 Release。

实施 PR 的 diff 可以碰：`stm32-book/build_html.py`、`stm32-book/styles/tokens.json`、`stm32-book/styles/book.css`、`stm32-book/tests/test_build.py`、`stm32-book/revisions.json`、`stm32-book/manifest.json`、`stm32-book/manifest-en.json`、`stm32-book/README.md`。不碰章节正文，不碰 `cover.svg`，不碰仓库根 `assets/`，不碰 `tools/`，不碰 `.github/workflows/book.yml`，不碰 `requirements.txt`。

合入前的最终 diff 必须同时有抽出和版本戳。不要把仍含三引号 `CSS` 的状态留成 PR 的最终内容。

## 风险

- **哨兵空白差一个换行，哈希就会失败。** 失败时改发射，保持 1.2.4 的字节。不要顺手重排 `book.css`。
- **若把样式放进仓库根 `assets/`，刀 C 的图和刀 B 的令牌会混在同一棵目录里。** 路径固定为 `stm32-book/styles/`。
- **若改成 `<link>`，单文件离线书和 CI 只上传 HTML 的约定一起破。** 成品继续内嵌。上传路径不增加 CSS。
- **若 `book.css` 里再写一遍颜色，JSON 就不再是唯一来源。** 源文件禁止 `{令牌名}:`。封面六个值只从 `light` 抄进拼好的 CSS。
- **若把印刷的 `9.5pt`、展示用 `clamp` 或 `.toc-jump` 的投影收进 JSON，这一刀就变成改版式。** 它们留在 `book.css`。刀 D 要动封面字号时另写设计，不在实施刀 B 时提前收编。
- **`json` 若按字母序重写暗色那一行，视觉测试仍可能通过，哈希不会。** 发射顺序等于文件键序。
- **给中英文各做一份 CSS，两本书会分叉。** `load_css` 不接收语言。两份 HTML 内嵌同一字符串。

## 验收

### 本设计 PR

- 新增文件只有 `docs/superpowers/specs/2026-10-25-book-visual-css-token-extract-B-design.md`。
- `stm32-book/`、`docs/` 章节、`docs/en/` 章节、资产、工具、workflow 和基线 `f537a94` 相同。
- 版本号仍是 1.2.4。没有 tag，没有 Release。没有实施计划。

### 实施 PR

- 中文与英文 `python3 stm32-book/build_html.py --check` 以及 `--lang en` 通过。`python3 -m unittest discover stm32-book/tests -v` 通过。`book` 与 `book-en` 都绿。
- `builder.CSS` 的 SHA-256 仍是 `e0fb660584f1833e8a6d419ba78ed9d56e4e92e51cbb533430ac8833bcca6bf4`。四个既有视觉测试不改也通过。
- 中英文 HTML 各有一个 `<style>`，其中的文本等于 `builder.CSS`，并且没有 `<link`。构建产物不含 `fonts.googleapis` 和 `fonts.gstatic`。
- 亮色 `--accent` 仍是 `#075e84`，列表标记计算色仍是 `rgb(7, 94, 132)`。`--spine` 仍是 `#c4552a`。`h2` 左边框仍是 `3px`。屏幕上 `figure` 上边框仍是 `1px` 且填充非透明；印刷时 `figure` 填充透明。
- `tokens.json` 是颜色和字号的唯一声明处。`book.css` 源文件不含令牌名后接冒号。封面画板的三个十六进制仍在 `book.css`。
- `docs/` 与 `docs/en/` 的正文 diff 为空。`cover.svg` diff 为空。仓库根 `assets/` diff 为空。
- 出版书签条数仍是 44。没有 tag，没有 Release。

人工打开构建出的中文 HTML 看两处即可：封面标题板仍是浅底，左条仍是 spine；任选一章，`h2` 左边条、一块代码、一张图的图注仍在。英文书与中文共用这一份 CSS，抽一页确认 `<style>` 内嵌即可。不要求把 29 章逐页看完。

## 后续刀

只点名，不在本文件里设计细节，也不进入刀 B 的实施 diff。顺序是 B 合入之后再写下一份设计。

1. **刀 D。** 封面和扉页的图形升级。到那时可以改 `book.css` 里的封面字面量和 `cover.svg`。若要把画板颜色收进 JSON，在刀 D 的设计里另定，不在刀 B 提前收。
2. **刀 C。** 重绘样本 SVG，统一画法。图仍在仓库根 `assets/`，不读 `stm32-book/styles/`。

刀 D 或刀 C 若改动了拼出来的 CSS 字节，那一刀的实施测试要换 SHA-256。刀 B 的哈希不在本刀放宽。

## 未决问题

没有会挡住抽出的未决项。下面几项按此处的默认执行。复审规格时可以改口。改路径或改「要不要拆模块」要在实施开始前定，不必为了改一个十六进制再写一版设计：

1. **目录。** `stm32-book/styles/tokens.json` 与 `stm32-book/styles/book.css`。不使用仓库根 `assets/`，也不建 `stm32-book/assets/`。
2. **一份 CSS。** 不拆模块。五段 `@media` 留在这个文件里，顺序不变。
3. **JSON 是值的唯一来源。** `book.css` 用四个哨兵承接声明，不手抄第二份颜色。
4. **保真。** 拼好的 `CSS` 与 `f537a94` 逐字节相同，用本文件的 SHA-256 锁定。这一刀不改版式。
5. **留在 CSS 里的字面量。** 封面三个画板色、展示字号、`.toc-jump` 的投影、`.compass-card` 的 `.5rem`、行内代码的 `.3em`、`color-mix` 百分比、印刷 pt 和毫米、`--table-columns`。
6. **版本。** 建议实施 PR 写成 1.2.5。本设计 PR 不升。实施合入不打 tag，不创建 Release。设计 PR 等人审；实施 PR 在 Book CI 变绿后 squash 合入。

## 英文提要

Extract only, on v1.2.4 (`f537a94`, PR #38). Move the inlined `CSS` string out of `stm32-book/build_html.py` into `stm32-book/styles/tokens.json` plus `stm32-book/styles/book.css`. JSON holds the 40 light custom properties and the 15-color dark and print overrides; `coverLock` copies six light colors onto `.cover` so the title plate stays light. `book.css` keeps selectors, the five `@media` blocks in their current order, and the literals knife E left unpacked (cover plate hexes, display clamps, `.toc-jump` shadow, `.compass-card` radius, print points, `--table-columns`). Four sentinels are replaced at import time. The resulting `CSS` string is still embedded in one `<style>` for both languages and must match the v1.2.4 bytes, SHA-256 `e0fb660584f1833e8a6d419ba78ed9d56e4e92e51cbb533430ac8833bcca6bf4`. Do not add a `<link>`, a font URL, a CSS preprocessor, or a workflow change. The provisional implementation version is 1.2.5; this design PR does not bump the version. Review this PR before merge. The later implementation PR squash-merges after the `book` and `book-en` jobs are green. Later knives, named only: D upgrades cover and imprint art, C redraws the sample SVGs. This design PR only adds this file.

# 整书封面与扉页 D 设计

日期：2026-10-25  
状态：待人审。人接受这份规格之前不实施  
基线：`main` 上的整书 **v1.2.5**（`b7ff335`，PR #41，2026-10-25）  
上一份样式设计：[2026-10-25-book-visual-css-token-extract-B-design.md](2026-10-25-book-visual-css-token-extract-B-design.md)（PR #39，实施合入 PR #41）。排版设计是 [2026-10-25-book-visual-typography-E-design.md](2026-10-25-book-visual-typography-E-design.md)（PR #35，实施合入 PR #38）。Token 仍写在 Python 字符串里的那一版是 [2026-10-25-book-visual-polish-1.2.0-design.md](2026-10-25-book-visual-polish-1.2.0-design.md)（PR #25，实施合入 PR #27）。  
本文件只记录刀 D 的设计。它不改 `cover.svg`，不改 `book.css`，不改 `build_html.py`，不改正文，不升版本号，不打 tag，不发布 Release，不新增 `docs/superpowers/plans/` 下的实施计划。

整书视觉升级的顺序是 **E → B → D → C**。E 已在 `f537a94` 合入，B 已在 `b7ff335` 合入。本文件只覆盖 D。C 在文末点名。

## 背景

1.2.0 把标题板收进 token，封面图只拉开了留白。刀 E 把正文字号收成阶梯，并写明封面展示字号、分部页大字和扉页标题字号留给封面刀。刀 B 把令牌抽到 `tokens.json`，选择器留在 `book.css`，并写明画板三个十六进制、展示用 `clamp`、印刷 pt 和 `--table-columns` 继续是字面量，要不要收进 JSON 由刀 D 另定。这一刀做封面和扉页的图形，不重做抽出。

对照 `b7ff335` 核对过的事实：

1. **样式已经不在 Python 字符串里。** `stm32-book/styles/tokens.json` 的 `schema` 是整数 `1`。顶层键顺序是 `schema`、`light`、`dark`、`print`、`coverLock`。`light` 是 40 个自定义属性。`dark` 和 `print` 各是那 15 个颜色。`coverLock` 是 `--paper`、`--ink`、`--muted`、`--warn`、`--line`、`--spine` 这六个名字，值从 `light` 抄。`load_css(tokens_path, css_path)` 在 import 时把四个哨兵填进 `stm32-book/styles/book.css`，结果赋给模块级 `CSS`。HTML 仍是 `<style>{CSS}</style>`。中英文走同一次加载。
2. **拼好的 CSS 与 1.2.4 逐字节相同。** SHA-256 是 `e0fb660584f1833e8a6d419ba78ed9d56e4e92e51cbb533430ac8833bcca6bf4`，由 `test_css_token_extract_contract` 锁定。`book.css` 源文件的 SHA-256 是 `bc15bac06ad752bcab8ecca0c267668f010a457ab0ee035db63b5fbc3e6d818a`，19663 字节。源文件里的十六进制颜色集合恰好是 `#10242e`、`#f4f1ea`、`#0c1c24`。源文件不含令牌名后接冒号，不含 `@font-face`，不含 `url(`。
3. **标题板靠 `.cover` 上的六次重设保持浅底。** 暗色查询只重写 `:root`。`.cover` 自己写了 `background: #10242e` 和 `color: #f4f1ea`，再接 `/* @tokens cover */`。`.cover-art` 的底是 `#0c1c24`。印刷里另有一条 `.cover { min-height: 245mm; page-break-after: always; background: #10242e; }`。这三处十六进制不在 40 个令牌里。
4. **封面展示字号仍是字面量。** `.cover h1` 是 `clamp(2.15rem, 5.6vw, 3.7rem)`，`line-height: 1.12`，`max-width: 12em`。`.cover .subtitle` 是 `clamp(1.05rem, 2.4vw, 1.35rem)`，`max-width: 34em`。`test_typography_e_css_contract` 锁着这两个 `clamp`，也锁着 `.part-divider h1` 的 `clamp(2rem, 5vw, 3.35rem)`、`.part-goal` 的 `1.12rem`、`.part-index` 的 `clamp(4.5rem, 14vw, 8.5rem)` 和窄屏 `3rem`。`.toc-jump` 仍是 `.85rem` 加 `box-shadow: 0 .45rem 1.2rem rgba(16, 24, 32, .18)`。
5. **扉页标题没有自己的字号。** `.imprint h1, .companion h2` 只写 `margin-top: 0`。下一条 `.imprint h1 { margin-bottom: .4rem; }` 不写 `font-size`。浏览器默认的 `h1` 是 `2em`。正文是 `--type-body: 1.0625rem`，所以扉页标题大约是 `2.125rem`。章标题用的是 `--type-h1: clamp(1.85rem, 4.2vw, 2.7rem)`。修订史、文前和目录的 `h1` 同样没有自己的 `font-size`。`.imprint .kicker` 已经是 `var(--type-kicker)`。`.imprint dl` 的顶边是 `3px solid var(--accent)`，宽屏列是 `minmax(11rem, 16rem)` 和 `minmax(0, 1fr)`，窄于 960px 改成一列。印刷里 `.imprint { break-before: auto; page-break-before: auto; }`，测试禁止把它改成 `always`。
6. **封面 HTML 的顺序是眉题、短线、书名、副题、版本行。** `build_html.py` 里 `.cover-panel` 的子节点顺序是 `p.eyebrow`、`hr.rule`、`h1`、`p.subtitle`、`p.edition`。短线的规则是 `width: 4.2rem; height: .18rem; background: var(--spine)`。左条是 `.cover-panel::before`，宽 `.45rem`，也是 `var(--spine)`。窄于 720px 时 `.cover-sheet` 的行是 `220px auto`，标题板 padding 是 `1.3rem 1rem 1.8rem`。这些选择器没有被测试锁成「短线必须在书名上面」。
7. **一张 SVG 同时进中文和英文。** `cover_art_svg()` 只读 `stm32-book/cover.svg`，剥掉 XML 声明后塞进 `<div class="cover-art" aria-hidden="true">`。`viewBox` 是 `0 0 1200 760`。文件 3965 字节。没有 `<style>`，没有 `<filter>`，没有 `<image>` 或带 `href` 的 `<use>`。板卡组是 `transform="translate(148 114)"`。图里有一行字：`<text x="112" y="62" …>OFFLINE EDITION</text>`，填色 `#8ecae6`，字体是 `ui-sans-serif, sans-serif`。中文封面因此也带着这行英文。HTML 眉题已经按语言分开：中文是「STM32 实战手册」，英文是「STM32 PRACTICAL BOOK」。
8. **图的填色是一套固定的 16 个十六进制。** `#07141a`、`#0c1c24`、`#14181c`、`#1b5c45`、`#1e4d63`、`#5c6770`、`#8d99a3`、`#8ecae6`、`#c4552a`、`#c5ced6`、`#d7c4a3`、`#d9dde2`、`#e7d7a1`、`#f4f1ea`、`#ffb020`、`#fff4d2`。底板 `#0c1c24` 与 `.cover-art` 相同。板卡绿 `#1b5c45` 与亮色 `--tip` 相同。左缘 `#c4552a` 与 `--spine` 相同。透明度只有三处：网格 `0.28`、偏移底板 `0.45`、灯点光晕 `0.18`。光晕是 `<circle r="42" fill="#ffb020" opacity="0.18"/>`。外框是 `<rect x="22" y="32" width="896" height="468" rx="18" fill="none" stroke="#d7c4a3" stroke-width="4"/>`。`test_cover_svg_stays_self_contained` 锁 `aria-label="STM32 board"`、`#c4552a`、`#8ecae6`、`#1b5c45`、`#ffb020`，禁止 `#9fd7c4`，并锁着现在的 `translate` 和那行字的坐标。
9. **书名和版权页文案不在图里。** 中文书名是「STM32 实战：从点亮一颗灯到交付一个系统」，副题是「29 章证据驱动的嵌入式入门与工程手册」。英文书名是「STM32 in Practice: From One LED to a System You Can Ship」，副题是「A 29-chapter evidence-driven introduction and engineering handbook」。扉页眉题中文是「版权页」，英文是「COLOPHON」。扉页标题中文是「版本与许可」，英文是「Version and license」。这些字符串在 `manifest.json`、`manifest-en.json` 和 `build_html.py` 的 `UI` 里。
10. **版本字面量是 1.2.5。** `revisions.json` 第一条是刀 B 的两句，日期 `2026-10-25`。两份 manifest 的 `version` 是 `1.2.5`，`date` 是 `2026-10-25`。`stm32-book/README.md` 当前版本句是 **v1.2.5 · 2026-10-25**。发布节的误标句子收到「也不要把 1.2.4 的产物标成 1.2.5」。Book CI 的 `book` 与 `book-en` 不上传 CSS。`tools/gen_mp_covers.py` 是公众号封面，不参与整书构建。

对比算法与 `stm32-book/tests/test_build.py` 里的 `_contrast_ratio` 相同。`#8ecae6` 对 `#0c1c24` 约 9.7，图里那行英文过了 4.5，删掉它不是为了补对比。`#c4552a` 对 `#1b5c45` 约 1.8，那是板卡左缘的色条，不是文字。`#c4552a` 对 `#fbfaf7` 约 4.3，1.2.0 已经规定 spine 作色条时不按正文门槛计。

## 目标与非目标

### 目标

- 实施时让封面图变成一块不带文字的板卡铜版。中英文 HTML 继续内嵌同一份 `cover.svg`。书名、副题、眉题、版本行仍由现有字符串提供，不改写。
- 标题板保持浅底。暗色查询仍然盖不住 `.cover` 上的 `coverLock`。画板三个十六进制留在 `book.css`，值不改。
- 扉页标题改用已经存在的 `--type-h1`。标题下加一条与封面短线同尺寸的书脊色条。这条色条用 `var(--spine)`，不新增颜色，也不新增 SVG。
- 封面 HTML 把现有的 `hr.rule` 移到书名和副题之间。不增删节点，不改文案。
- 令牌表不扩。`schema` 仍是 `1`。`load_css` 的签名、四个哨兵、五段 `@media` 的顺序都不改。
- 因为扉页那两条 CSS 会改变拼好的字符串，实施测试把 SHA-256 从刀 B 的值换成下面写死的新值。只改 SVG 或 HTML 顺序不会改变这个哈希；新哈希只对应那一处 CSS 替换。
- 实施时的建议版本是 **1.2.6**。本设计 PR 不升版本。
- 实施 PR 在 `book` 与 `book-en` 都变绿之后 squash 合入 `main`。合入后在本机 `D:\Users\STM32` 拉取这次 `main`。拉取不产生仓库 diff。

### 非目标

- 不改 `docs/00`–`28`、`docs/en/`、附录 Markdown、`CONTENT_GUIDE.md` 中英、罗盘文案。不改两份 manifest 里除 `version` 和 `date` 以外的字段。不改 `UI` 里的封面眉题、扉页眉题、扉页标题、导语、商标句。
- 不把画板三色、封面 `clamp`、分部页大字、`.toc-jump`、印刷 pt、`@page` 毫米值、`--table-columns` 收进 `tokens.json`。也不改这些字面量的值。
- 不改 `.part-divider h1`、`.part-goal`、`.part-index`。刀 E 曾把这些展示字号和封面放在同一句里留给封面刀。它们是分部页，不是封面，这一刀不动。
- 不改修订史、文前、目录的 `h1` 字号。它们和扉页一样还没有自己的 `font-size`。这一刀只补扉页。
- 不改 `.imprint dl` 的 `3px` 强调色顶边、列宽、960px 折叠。不改 `imprint_html` 的标签和句子。
- 不重绘 `assets/` 里的样本 SVG、动画 SVG 或 GIF，不改 `tools/`，包括 `tools/gen_mp_covers.py`。那是刀 C，公众号封面也不在这本书里。
- 不新增第二份封面 SVG，不按语言分图，不把书名排进 SVG。
- 不加 `@font-face`，不写 `url(`，不引用 `fonts.googleapis` 或 `fonts.gstatic`。不加 `<link rel="stylesheet">`。
- 不改 `tokens.json` 的键、值和 `coverLock`。不改 `load_css`。不改 `.github/workflows/book.yml`。
- 不加图目录或表目录。出版书签仍是 44 条。章号显示仍是文件名前缀加 1。
- 不打 tag，不创建 GitHub Release。
- 不实施文末点名的刀 C。本设计 PR 也不写它的实施计划。

## 方案

比较过三种做法。

| 做法 | 图里有什么 | 结果 |
| --- | --- | --- |
| 1. 只重绘 `cover.svg`，CSS 不动 | 仍可留着 `OFFLINE EDITION` | 哈希保持 `e0fb6605…`。扉页标题仍靠浏览器默认的 `2em`。中文封面上仍有一行英文 |
| 2. 中文一张 SVG、英文一张 SVG，书名写进图里 | 每种语言一份图 | `cover_art_svg()` 现在只读一个文件。图内文字不能随标题板的 token 变，两张图也会分叉 |
| 3. 一份无文字的铜版，标题和扉页规则留在现有 CSS 里 | 板卡、内框、平涂灯点 | 中英文共用一张图。文案仍走 manifest 和 `UI`。令牌表不扩。拼好的 CSS 按下面那一处替换换成新哈希 |

采用做法 3。做法 1 留下刀 E 点名的扉页缺口，也留下中文封面上的英文眉题。做法 2 把已经在 HTML 里的书名再写进图。1.2.6 不拆封面文件，也不升 token schema。

所有权仍是刀 B 的那一条链：`tokens.json` 的值 → 拼好的自定义属性 → `book.css` 里的 `var(--*)`。这一刀新增的扉页字号引用已有的 `--type-h1`，不往 JSON 里加键。画板色和封面 `clamp` 继续写在 `book.css` 里，因为它们不跟随暗色那 15 个颜色。

## 封面图

只改 `stm32-book/cover.svg`。允许的改动只有下面三处，其余节点、坐标、填色、描边和 `transform="translate(148 114)"` 保持原文。

1. 删除整行 `<text x="112" y="62" fill="#8ecae6" font-family="ui-sans-serif, sans-serif" font-size="18" letter-spacing="3.5">OFFLINE EDITION</text>`。不要换成中文，也不要换成别的拉丁字母。`#8ecae6` 还在下面这条迹线上，必须留下：`<path d="M78 446H300" stroke="#8ecae6" stroke-width="2" fill="none"/>`。
2. 删除灯点光晕 `<circle r="42" fill="#ffb020" opacity="0.18"/>`。同一组里的 `<circle r="22" fill="#ffb020"/>` 和 `<circle cx="-6" cy="-6" r="7" fill="#fff4d2"/>` 留下。
3. 在现有外框的下一行加上内框。外框保持 `<rect x="22" y="32" width="896" height="468" rx="18" fill="none" stroke="#d7c4a3" stroke-width="4"/>`。内框是 `<rect x="34" y="44" width="872" height="444" rx="12" fill="none" stroke="#d7c4a3" stroke-width="1"/>`。它比外框每边收进 12 个用户单位，不使用新颜色。

同时保持：

- 根元素仍是 `viewBox="0 0 1200 760"`、`role="img"`、`aria-label="STM32 board"`。
- 不出现 `<text`、`font-family`、`font-size`、`<style`、`<filter`、`<foreignObject`、`<image`、带 `href` 或 `xlink:href` 的 `<use`、`@font-face`。除 `xmlns` 里的 `www.w3.org` 以外不出现 URL。
- 十六进制集合仍恰好是背景一节列出的那 16 个。不出现 `#9fd7c4`。
- `opacity` 只剩网格的 `0.28` 和偏移底板的 `0.45`，文档顺序也是这个顺序。
- UTF-8 不超过 8192 字节。现在是 3965 字节，加一道内框、删一行字和一个圆之后仍应远低于这个上限。
- 不把填色改成 `var(--*)`。单独打开 `cover.svg` 时没有令牌表，图必须自己能着色。构建仍只做内嵌，不生成 SVG。

`.cover-art` 继续带 `aria-hidden="true"`。书名的可访问名称是标题板里的 `h1`，不靠图里的文字。

## 标题板

`build_html.py` 里只调整 `.cover-panel` 的子节点顺序。现在是眉题、短线、书名、副题、版本行。实施后是眉题、书名、短线、副题、版本行：

```html
<p class="eyebrow">…</p>
<h1>…</h1>
<hr class="rule">
<p class="subtitle">…</p>
<p class="edition">…</p>
```

`eyebrow`、`h1`、`rule`、`subtitle`、`edition` 的表达式保持原文，包括 `ui(manifest, 'cover_kicker')`、`manifest['title']`、`manifest['subtitle']` 和版本行。不改 `cover_art_svg()`，不改 `imprint_html()`。

短线的 CSS 不改。书名与短线之间仍是 `.cover h1` 的下边距 `.7rem`。短线与副题之间仍是 `.cover .rule` 的下边距 `1rem`。`.cover h1` 和 `.cover .subtitle` 的 `clamp`、行高、`max-width` 不改，因此 `test_typography_e_css_contract` 里这两条断言保持原文。

标题板的颜色继续走 `.cover` 上的 `coverLock`：底 `--paper`，书名和副题 `--ink`，眉题 `--warn`，版本行 `--muted`，版本行上边线 `--line`，左条和短线 `--spine`。不把标题板改成暗色纸。

## 扉页

`book.css` 只做一处替换。被替换的原文是这一行，含行尾换行：

```css
.imprint h1 { margin-bottom: .4rem; }
```

替换成下面两行，属性顺序就是这个顺序：

```css
.imprint h1 { margin-bottom: .4rem; font-size: var(--type-h1); line-height: 1.22; }
.imprint h1::after { content: ""; display: block; width: 4.2rem; height: .18rem; margin-top: .85rem; background: var(--spine); }
```

约束：

- 字号写在 `.imprint h1` 上，不写进 `.imprint h1, .companion h2`。后一条规则仍只有 `margin-top: 0`。写进组合选择器会把配套资源的 `h2` 也抬到章标题字号。
- `::after` 选择器是 `.imprint h1::after`。`_css_rule` 用「选择器紧挨 `{`」来取规则，因此它不会被当成 `.imprint h1` 那一条。
- 短线的宽 `4.2rem`、高 `.18rem`、底色 `var(--spine)` 与 `.cover .rule` 相同。`content` 是空字符串。不写 `url(`。
- 标题文字和短线之间是 `margin-top: .85rem`。短线下面仍是原来的 `margin-bottom: .4rem`，然后才是导语。
- 不改 `.imprint` 的 padding、底边、导语颜色，不改 `dl` 的顶边和列。
- 修订史、文前、目录的 `h1` 不加上 `font-size`。

宽屏上 `--type-h1` 的上限是 `2.7rem`，窄屏下限是 `1.85rem`。相对现在大约 `2.125rem` 的默认 `h1`，宽窗口里的扉页标题会略大，390px 宽时会略小。这和章标题是同一档。

## 与令牌的边界

这一刀对刀 B 留下的字面量作决定。决定是：下面这些继续留在原处，值也不改。

| 对象 | 现在 | 刀 D |
| --- | --- | --- |
| 画板 `#10242e`、`#0c1c24`、字色 `#f4f1ea` | `book.css` 字面量 | 留下。不进 JSON，不改值 |
| `coverLock` 的六色 | 从 `light` 抄到 `.cover` | 不改键，不改值 |
| `.cover h1`、`.cover .subtitle` 的 `clamp` | `book.css` 字面量 | 不改。刀 E 的测试继续锁旧值 |
| `.part-divider h1`、`.part-goal`、`.part-index` | `book.css` 字面量 | 不改。分部页不是封面 |
| `.toc-jump` 的字号和投影 | `book.css` 字面量 | 不改 |
| 印刷 `9.5pt`、图注 `9pt`、`@page` 的 `16mm 15mm 18mm` | `book.css` 字面量 | 不改 |
| `--table-columns` | 表格 HTML 的内联 `style` | 不进令牌表 |
| 扉页 `h1` 的字号 | 没有声明 | 引用已有的 `var(--type-h1)`。不新增 JSON 键 |
| 扉页短线 | 没有 | `book.css` 里的 `::after`，引用已有的 `var(--spine)` |

不把画板色放进 `light`。暗色和印刷会整组替换那 15 个颜色，画板跟着变暗或变白，封面就不再是一块深色铜版。单独再做一个 `coverBoard` 对象要把 `schema` 改成 `2`，还要加第五个哨兵。三处字面量已经由测试锁成集合，不值得为它们升 schema。

`book.css` 源文件在这一刀之后，十六进制集合仍恰好是 `#10242e`、`#f4f1ea`、`#0c1c24`。四个哨兵各出现一次。`@media` 仍是五个，顺序仍是 960、720、暗色、减少动效、印刷。

## 暗色与印刷

暗色：

- `@media (prefers-color-scheme: dark)` 里仍然只有那一行 `:root`。不要在暗色段里写 `.cover`。
- 标题板继续是浅底。左条和封面上的短线继续是亮色 `--spine`，也就是 `#c4552a`，因为 `coverLock` 盖住了暗色根变量。
- 扉页不在 `.cover` 里面。暗色下它的纸、字和短线跟随暗色 token。短线变成 `#f0b090`。不要为了让两条短线同色，把 `coverLock` 抄到 `.imprint` 上。那样会把版权页锁成浅底。
- 封面图的填色写在属性上，不跟随 `prefers-color-scheme`。暗色下板卡仍是深底上的绿板。

印刷：

- `.cover` 的 `min-height: 245mm`、`page-break-after: always`、`background: #10242e` 保持。`.cover-sheet` 的 `min-height: 245mm` 保持。
- `body` 上的 `print-color-adjust: exact` 保持，深色封面和书脊色条要印出来。
- 扉页继续是 `break-before: auto` 和 `page-break-before: auto`。封面已经 `page-break-after: always`，版权页因此落在下一页。不要把扉页改成 `page-break-before: always`。
- 扉页短线是 `h1` 的 `::after`，跟着已有的 `h1 { break-after: avoid-page }` 留在标题那一侧。
- 印刷里的 `--spine` 仍是 `#c4552a`。短线是色条，不列入 4.5 的文字门槛。
- 正文 `9.5pt`、图注 `9pt`、孤行寡行、`figure { background: transparent; }`、`@page` 的毫米值都不改。

## 版本与修订文案

本设计 PR 不改版本。实施 PR 才写。

实施开始时先读 `main` 上的 `stm32-book/manifest.json`。

- `version` 仍是 `1.2.5`：实施版写成 `1.2.6`。
- `version` 已经高于 `1.2.5`：实施版写成下一条修订号，不把本文件里的 `1.2.6` 硬套上去。修订句子仍用下面四句。

日期用实施当天的 ISO 日期。`revisions.json`、两份 manifest、`stm32-book/README.md` 写同一个日期。`validate_revisions` 仍要求修订第一条的版本等于两份 manifest 的 `version`。新条目插在最前，已有句子一字不改。

- `version`: 按上面的规则
- `date`: 实施当天
- `zh`:
  - 封面图不再写英文眉题，板卡外框加了一道内线；发光的灯点改成平涂。中英文仍共用这一张图。
  - 标题板把书名放在书脊短线上面。扉页标题改用章标题的字号，并在标题下重复这条书脊短线。
- `en`:
  - The cover drawing no longer carries an English kicker. The board frame gains an inner rule, and the glowing lamp is flat. Both languages still share this drawing.
  - The title plate places the title above the spine rule. The imprint heading uses the chapter title size and repeats that spine rule.

不在修订说明里写刀 C，也不写章节名。两份 manifest 只改 `version` 和 `date`。

`stm32-book/README.md`：

- 当前版本句改为 **v{新版本} · {实施日期}**。中英文整书仍共用这一版号。
- 发布节的版本句改为已经是这个版本。tag 名改为 `v{新版本}`。在现有误标句子的最后再加一句「也不要把 {上一版} 的产物标成 {新版本}」。已有的误标句子保留，包括「也不要把 1.2.4 的产物标成 1.2.5」。
- 构建节里关于 `tokens.json` 和 `book.css` 的那一句保留。
- 这一步仍不创建 tag，也不创建 Release。

## 测试

断言仍在 `stm32-book/tests/test_build.py`。不新开测试文件。不增加依赖。不新开浏览器用例。

下面四个方法的函数体保持原文，一个断言都不改：

- `test_visual_polish_css_contract`
- `test_typography_e_css_contract`
- `test_visual_polish_contrast_clears_4_5`
- `test_code_glossary_and_print_css_keep_reading_units_movable`

封面 `clamp` 不改，所以刀 E 的方法不用改也能通过。标题板的颜色不改，所以 1.2.0 的方法也不用改。

`test_css_token_extract_contract` 只改哈希那一个字符串。哨兵、十六进制集合、`coverLock`、五段 `@media`、`<style>` 内嵌和拒绝坏令牌的断言保持原文。新哈希是：

`a4ccd1403ab742e82f67c39053c2609da1c9a8afa126d4f6b988a5b9559a5ac4`

这个值是在 `b7ff335` 的 `book.css` 上只做上一节那一处替换，再用与 `load_css` 相同的四次哨兵替换算出来的。同一过程在未替换的文件上得到刀 B 的 `e0fb660584f1833e8a6d419ba78ed9d56e4e92e51cbb533430ac8833bcca6bf4`。基线哈希仍是 `e0fb6605…` 时，若新哈希对不上，先核对是不是多改了空白或属性顺序。不要把测试里的期望改成另一份 CSS 的哈希，也不要改令牌值去迁就它。基线已经变了的情况只走下一段。

停手条件：实施开始时若 `builder.CSS` 的 SHA-256 已经不是 `e0fb6605…`，说明 `main` 上的样式又动过。先停。把同一处扉页替换应用到当时的 `book.css` 上，重新计算哈希，只把测试里的期望换成这个新结果，并在实施 PR 里写出旧哈希和新哈希。不要趁机改封面 `clamp` 或令牌。

`test_cover_svg_stays_self_contained` 删掉这两行：

- `self.assertIn('<text x="112" y="62"', svg)`
- `self.assertNotIn('<text x="72" y="62"', svg)`

换成：

- `self.assertNotIn("<text", svg)`
- `self.assertNotIn("OFFLINE EDITION", svg)`
- `self.assertNotIn('opacity="0.18"', svg)`

`aria-label`、`#c4552a`、`#8ecae6`、`#1b5c45`、`#ffb020`、禁止 `#9fd7c4`、禁止 `<style`、禁止外链、`translate(148 114)` 和禁止旧的 `translate(118 100)` 都留下。`--spine: #c4552a` 那条 CSS 断言也留下。

新增 `test_cover_imprint_d_contract`。它核对这一刀自己的契约：

- `cover.svg` 含 `viewBox="0 0 1200 760"`、整段外框 `<rect x="22" y="32" width="896" height="468" rx="18" fill="none" stroke="#d7c4a3" stroke-width="4"/>`、整段内框 `<rect x="34" y="44" width="872" height="444" rx="12" fill="none" stroke="#d7c4a3" stroke-width="1"/>`、`stroke="#8ecae6"`、`<circle r="22" fill="#ffb020"/>`。板上另有一枚 `x="22" y="0"` 的小焊盘，不能只搜 `x="22"`。
- 不含 `<text`、`font-family`、`font-size`、`<filter`、`<foreignObject`、`opacity="0.18"`。
- 文件里的十六进制集合恰好是 `#07141a`、`#0c1c24`、`#14181c`、`#1b5c45`、`#1e4d63`、`#5c6770`、`#8d99a3`、`#8ecae6`、`#c4552a`、`#c5ced6`、`#d7c4a3`、`#d9dde2`、`#e7d7a1`、`#f4f1ea`、`#ffb020`、`#fff4d2`，都是小写。`opacity="…"` 的值按文档顺序是 `0.28`、`0.45`。
- UTF-8 长度不超过 8192。
- 屏幕段里 `.imprint h1` 的规则含 `margin-bottom: .4rem`、`font-size: var(--type-h1)`、`line-height: 1.22`。
- `.imprint h1, .companion h2` 的规则含 `margin-top: 0`，不含 `font-size`。
- `.imprint h1::after` 的规则含 `content: ""`、`width: 4.2rem`、`height: .18rem`、`background: var(--spine)`，不含 `url(`。
- `.cover h1` 仍含 `clamp(2.15rem, 5.6vw, 3.7rem)`。`.cover .subtitle` 仍含 `clamp(1.05rem, 2.4vw, 1.35rem)`。`.part-divider h1` 仍含 `clamp(2rem, 5vw, 3.35rem)`。
- 印刷段仍含 `font-size: 9.5pt`、`font-size: 9pt`、`.imprint { break-before: auto; page-break-before: auto; }`、`.cover` 的 `background: #10242e`。
- 拼好的 CSS 里，从暗色查询到下一个 `@media` 之间不含 `.cover`。
- `tokens.json` 的 `schema` 仍是 `1`，`coverLock` 仍是原来的六个名字。`book.css` 源文件的十六进制集合仍是那三个。
- 临时目录里各构建一次中文和英文 HTML。封面面板里 `class="eyebrow"` 在 `<h1>` 之前，`<h1>` 在 `class="rule"` 之前，`class="rule"` 在 `class="subtitle"` 之前。中文 `h1` 的文本等于中文 manifest 的 `title`。英文 `h1` 的文本等于英文 manifest 的 `title`。两份 HTML 的封面 SVG 都不含 `OFFLINE EDITION`，并且都不含 `fonts.googleapis`。

版本断言按实施时的实际版本改，不在设计 PR 里改：

- `assert_version_history_and_index` 的元组在 `1.2.5` 前加上新版本，并断言 `>{新版本}<` 出现在 `>1.2.5<` 之前。其后的先后顺序保持。
- `test_revision_file_lists_1_0_0_through_manifest_version` 的列表以新版本起头，下一项仍是 `1.2.5`。
- `test_build_produces_one_complete_offline_book` 和 `test_english_book_is_a_separate_offline_edition` 里的 `<strong>v1.2.5</strong>` 改为新版本。英文 manifest 的版本等式一并改。
- `test_visual_polish_version_is_1_2_0` 改为核对新的第一条。现在对 `entries[0]` 到 `entries[5]` 的句子各后移一位：1.2.5 的刀 B 两句改去核对 `entries[1]`，1.2.4 的排版两句改去 `entries[2]`，1.2.3 的 Batch4 两句改去 `entries[3]`，1.2.2 改去 `entries[4]`，1.2.1 改去 `entries[5]`，1.2.0 改去 `entries[6]`。句子原文不改。新的 `entries[0]` 用上一节的四句，日期等于两份 manifest 的 `date`。
- README 断言改为新的当前版本句、`版本号已经是 {新版本}`、新的误标句子，以及 `打 tag \`v{新版本}\``。`也不要把 1.2.4 的产物标成 1.2.5` 这句保留。

不删 `0x271`、`167 ns`、出版书签长度为 44、样本章和各批加厚的断言。`pageOverflow` 为 0 的三档断言不放宽。窄屏列表标记仍是 `rgb(7, 94, 132)`。印刷不断页的现有测试不改期望。窄屏 `.imprint dl` 仍是一列，宽屏仍至少两列。

## 工作流与 PR 节奏

刀 D 沿用刀 B 的节奏：设计 PR 等人审阅后再合；实施 PR 在 Book CI 变绿后 squash 合入，不再做第二次正文复审。这一刀不改正文。

### 本 PR（设计）

只新增本文件。不改 `docs/` 章节、`docs/en/`、`stm32-book/`、`assets/`、`tools/`、`CREDITS.md`、`.github/`。不升版本，不打 tag，不发 Release。不新增实施计划。本 PR 等人审阅规格后再合入，不在 CI 变绿后自动合。

### 实施 PR（下一轮，不在本 PR）

顺序固定：

1. **封面图。** 按「封面图」一节改 `cover.svg`。不要顺手重排其余节点。
2. **标题板顺序。** 按「标题板」一节把 `hr.rule` 移到 `h1` 和副题之间。不改表达式。
3. **扉页规则。** 按「扉页」一节替换 `book.css` 的那一行。不要重排文件的其余部分，不要改 `tokens.json`。
4. **测试。** 改 `test_cover_svg_stays_self_contained` 和哈希那一个字符串，并加上 `test_cover_imprint_d_contract`。四个既有视觉方法不改。版本断言留到下一步一起改。
5. **版本。** 同一 PR 内改 `revisions.json`、两份 manifest、`stm32-book/README.md`，并把版本断言改到实施时的实际新版本。修订说明只用上一节的四句。
6. **验证。** 下面三条通过，并且 `builder.CSS` 的 SHA-256 等于本文件给出的新值之后，再请求合入：

```bash
python3 -m unittest discover stm32-book/tests -v
python3 stm32-book/build_html.py --check
python3 stm32-book/build_html.py --lang en --check
```

7. **合入。** `book` 与 `book-en` 都变绿之后，把实施 PR squash 合入 `main`。合入后在 `D:\Users\STM32` 拉取这次 `main`。不打 tag，不创建 Release。

实施 PR 的 diff 可以碰：`stm32-book/cover.svg`、`stm32-book/styles/book.css`、`stm32-book/build_html.py`（只限封面面板里那几个节点的顺序）、`stm32-book/tests/test_build.py`、`stm32-book/revisions.json`、`stm32-book/manifest.json`、`stm32-book/manifest-en.json`、`stm32-book/README.md`。不碰 `tokens.json`，不碰章节正文，不碰仓库根 `assets/`，不碰 `tools/`，不碰 `.github/workflows/book.yml`，不碰 `requirements.txt`。

合入前的最终 diff 必须同时有封面图、标题板顺序、扉页 CSS 和版本戳。不要把仍锁着 `e0fb6605…` 的测试留成 PR 的最终内容。

## 风险

- **扉页规则多一个空格，新哈希就会对不上。** 对不上时改回上一节的那两行原文。不要改期望哈希来迁就另一份 CSS，也不要改令牌。
- **若把 `font-size` 写进 `.imprint h1, .companion h2`，配套资源的标题会变成章标题字号。** 字号只放在单独的 `.imprint h1` 规则上。
- **若把画板三色收进 `light`，暗色会把深色封面换成暗色纸。** 它们留在 `book.css`。`coverLock` 继续只锁标题板那六色。
- **若给 `.imprint` 也做一套 `coverLock`，版权页在暗色下会变成浅底。** 扉页跟随暗色 token。两条短线在暗色下可以一个是 `#c4552a`、一个是 `#f0b090`。
- **若把书名写进 SVG，中英文就要分两张图。** 图内不放文字。书名仍在标题板的 `h1` 里。
- **若重绘芯片、引脚或迹线，这一刀就变成刀 C 的样本图。** SVG 只删一行字、删一个光晕圆、加一道内框。
- **若改封面 `clamp` 来「顺便」收进 token，刀 E 的测试会失败，哈希也会离开本文件给出的值。** `clamp` 保持原文。

## 验收

### 本设计 PR

- 新增文件只有 `docs/superpowers/specs/2026-10-25-book-visual-cover-imprint-D-design.md`。
- `stm32-book/`、`docs/` 章节、`docs/en/` 章节、资产、工具、workflow 和基线 `b7ff335` 相同。
- 版本号仍是 1.2.5。没有 tag，没有 Release。没有实施计划。

### 实施 PR

- 中文与英文 `python3 stm32-book/build_html.py --check` 以及 `--lang en` 通过。`python3 -m unittest discover stm32-book/tests -v` 通过。`book` 与 `book-en` 都绿。
- `builder.CSS` 的 SHA-256 是 `a4ccd1403ab742e82f67c39053c2609da1c9a8afa126d4f6b988a5b9559a5ac4`，除非「测试」一节的停手条件已经触发。四个既有视觉方法不改也通过。
- `tokens.json` 与 `b7ff335` 的 diff 为空。`schema` 仍是 `1`。`book.css` 源文件的十六进制仍是那三个。拼好的 CSS 不含 `/* @tokens`，不含 `@font-face`，不含 `url(`。
- 中英文 HTML 各有一个 `<style>`，没有 `<link`，也不含 `fonts.googleapis` 和 `fonts.gstatic`。
- 亮色 `--accent` 仍是 `#075e84`，列表标记计算色仍是 `rgb(7, 94, 132)`。`--spine` 仍是 `#c4552a`。`h2` 左边框仍是 `3px`。屏幕上 `figure` 上边框仍是 `1px` 且填充非透明；印刷时 `figure` 填充透明。
- `cover.svg` 不含 `OFFLINE EDITION`，含内框，不含 `opacity="0.18"`。`docs/` 与 `docs/en/` 的正文 diff 为空。仓库根 `assets/` diff 为空。
- 出版书签条数仍是 44。没有 tag，没有 Release。

人工打开构建出的中文 HTML，看这几处：

- 封面：深色底上仍是一块板，图里没有字；外框里面有一道细线；灯点没有光晕。标题板是浅底，左条仍是 spine。书名在短线上面，副题在短线下面。书名和副题与现在的 manifest 相同。
- 暗色：标题板仍是浅底，板卡仍是深底。翻到版权页，页面跟随暗色，短线不是一块浅色标题板。
- 扉页：眉题仍是「版权页」，标题仍是「版本与许可」。标题下有一条短的书脊色线。宽窗口里定义列表至少两列，窄于 960px 时是一列。句子不改。
- 印刷预览：封面单独成页，深色底仍印出来。版权页不另写 `page-break-before: always`。
- 任选第 00 章，看 `h2` 左边条仍在。这是确认哈希变化没有把令牌填坏。不要求把 29 章逐页看完。

英文书用同一次构建看封面和版权页即可。图与中文相同。眉题是「STM32 PRACTICAL BOOK」，扉页眉题是「COLOPHON」，标题是「Version and license」。

## 后续刀

只点名，不在本文件里设计细节，也不进入刀 D 的实施 diff。顺序是 D 合入之后再写下一份设计。

1. **刀 C。** 重绘样本 SVG，统一画法。图仍在仓库根 `assets/`，不读 `stm32-book/styles/`，也不改 `cover.svg`。

刀 C 若没有改 `book.css`，拼好的 CSS 应保持本刀的新哈希。刀 C 的设计若要改样式，再换 SHA-256。本刀的新哈希不在刀 C 里提前放宽。

## 未决问题

没有会挡住封面实施的未决项。下面几项按此处的默认执行。复审规格时可以改口。改「图里留不留文字」或「扉页要不要新字号」要在实施开始前定。只改一个已经写死的矩形坐标，不必再写一版设计：

1. **图内不放文字。** 删除 `OFFLINE EDITION`。不另做中文 SVG，也不把书名排进图里。
2. **画板三色留在 `book.css`。** 不升 `schema`，不加 `coverBoard`。值保持 `#10242e`、`#0c1c24`、`#f4f1ea`。
3. **封面和分部页的展示字号不改。** `.cover h1` 与 `.cover .subtitle` 保持现在的 `clamp`。分部页、`.toc-jump`、印刷 pt、`--table-columns` 也不碰。
4. **扉页标题只用已有的 `--type-h1`。** 不新造一套 `clamp`。修订史、文前、目录的 `h1` 这一刀不补字号。
5. **扉页装饰是 CSS 短线。** 不新增第二份 SVG，不改 `imprint_html` 的文案，不改 `dl` 的 `3px` 顶边。
6. **板卡几何只加一道内框，并去掉光晕。** 其余坐标、`translate(148 114)` 和 16 个填色保持。
7. **标题板把短线移到书名下面。** 不改眉题、书名、副题、版本行的字符串。
8. **哈希按这一处 CSS 替换更换。** 新值是 `a4ccd1403ab742e82f67c39053c2609da1c9a8afa126d4f6b988a5b9559a5ac4`。SVG 和 HTML 顺序不参与这个哈希。
9. **版本。** 建议实施 PR 写成 1.2.6。本设计 PR 不升。实施合入不打 tag，不创建 Release。设计 PR 等人审；实施 PR 在 `book` 与 `book-en` 变绿后 squash 合入。

## 英文提要

Cover and imprint art only, on v1.2.5 (`b7ff335`, PR #41). Keep one self-contained `stm32-book/cover.svg` for both languages. Delete the `OFFLINE EDITION` text and the LED halo at `opacity="0.18"`, and add one inner frame rect inset 12 user units from the existing `#d7c4a3` frame. Do not add words, a second SVG, a filter, or a new hex. Move the existing `hr.rule` to sit between the `h1` and the subtitle; do not change title, subtitle, or kicker strings. On the imprint, set `.imprint h1` to `var(--type-h1)` and paint a `4.2rem` by `.18rem` `::after` rule in `var(--spine)`. Leave `tokens.json` at schema 1. Leave the cover-board literals `#10242e`, `#0c1c24`, and `#f4f1ea` in `book.css`, and leave the cover clamps, part-divider display sizes, print points, and `--table-columns` untouched. The title plate stays light in dark mode via the existing `coverLock`. The assembled CSS can no longer keep the v1.2.4 byte hash; after this one imprint edit it is SHA-256 `a4ccd1403ab742e82f67c39053c2609da1c9a8afa126d4f6b988a5b9559a5ac4`. The provisional implementation version is 1.2.6; this design PR does not bump the version. Review this PR before merge. The later implementation PR squash-merges after the `book` and `book-en` jobs are green. The later knife, named only: C redraws the sample SVGs. This design PR only adds this file.

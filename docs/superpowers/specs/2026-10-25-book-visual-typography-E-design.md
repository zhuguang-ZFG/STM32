# 整书排版微抛 E 设计

日期：2026-10-25  
状态：待人审。人接受这份规格之前不实施  
基线：`main` 上的整书 **v1.2.2**（`ea11ce7b2dd02cec4e46a6abcb701a0286faef4a`，PR #33，2026-10-25）  
上一份观感设计：[2026-10-25-book-visual-polish-1.2.0-design.md](2026-10-25-book-visual-polish-1.2.0-design.md)（PR #25，实施合入 PR #27）。Batch4 加厚设计是 [2026-10-25-classic-encyclopedia-batch4-01-07-10-11-design.md](2026-10-25-classic-encyclopedia-batch4-01-07-10-11-design.md)（PR #33），它还没有改章节，也没有把版本写成 1.2.3。  
本文件只记录刀 E 的设计。它不改 `build_html.py`，不改正文，不升版本号，不打 tag，不发布 Release。

整书视觉升级的顺序是 **E → B → D → C**。本文件只覆盖 E。B、D、C 在文末点名。

## 背景

1.2.0 已经把间距阶梯、圆角、轻阴影和两处小字的字色收进内联 `CSS`。这一刀只补它没做的排版：字体栈、字号阶梯、目录、代码块、图注，以及仍写在同一段 `CSS` 里的印刷微调。

对照 `ea11ce7` 的 `stm32-book/build_html.py` 核对过的事实：

1. **样式仍全在 `CSS` 这一段字符串里。** 从 `:root` 到 `@media print`。没有独立 `.css`，没有 design-token JSON，没有 `@font-face`，`CSS` 里没有 `url(`。构建出的 HTML 由 `test_build_produces_one_complete_offline_book` 禁止 `fonts.googleapis` 和 `fonts.gstatic`。亮色仍是 `--paper: #fbfaf7`、`--ink: #17202a`、`--accent: #075e84`、`--muted: #5e6872`、`--warn: #9a3d1c`、`--tip: #1b5c45`、`--spine: #c4552a`。1.2.0 的阶梯仍是 `--space-bar: 0.75rem`、`--space-paragraph: 1.25rem`、`--space-figure: 1.5rem`、`--space-chapter: 3.5rem`、`--inset: 6%`、`--leading-body: 1.75`、`--tracking-body: 0.01em`、`--tracking-kicker: 0.14em`、`--radius: 0.7rem`、`--elev: 0 1px 2px color-mix(in srgb, var(--ink) 8%, transparent)`。
2. **字体栈只有两处，而且都是系统字体名。** `:root` 的 `font-family` 是 `"Noto Sans CJK SC", "Microsoft YaHei", "PingFang SC", system-ui, sans-serif`。`code` 的是 `"Cascadia Mono", "SFMono-Regular", Consolas, monospace`。`body` 不另写 `font-family`，也不写 `font-size`。中英两版共用这一段 `CSS`。
3. **`font-size` 有 32 处，标题没有阶梯。** 章标题 `h1` 是 `clamp(1.85rem, 4.2vw, 2.7rem)`，`h2` 是 `1.42rem`，`h3` 是 `1.16rem`，`h4` 是 `1.02rem`。正文没有自己的字号，按根元素的 `1rem`（通常 16px）走。`h4` 只比这个正文大 `0.02rem`。`h2, h3, h4` 的 `line-height` 是字面量 `1.35`。通用 `h2` 的 margin 仍是 `2.35rem 0 .6rem`，和章内 `h2` 的 `calc(var(--space-figure) + var(--space-paragraph)) 0 var(--space-bar)`（2.75rem / 0.75rem）不是同一档。`h3` 是 `1.7rem 0 .4rem`，`h4` 是 `1.3rem 0 .3rem`。
4. **眉题字号散在五档。** `.72rem`（`.compass-role`）、`.74rem`（`.callout-label`）、`.75rem`（`.source-card dt`）、`.78rem`（`.cover .eyebrow`、`.closing-banner`、`.chapter-number`、`.compass-title`、`.source-id`）、`.82rem`（`.imprint .kicker`、修订史和索引的 `.kicker`、`.index-letter`、`.part-label`）。字距已经统一成 `--tracking-kicker`，字号没有。
5. **目录的结构由 `toc_html` 生成，样式很稀。** 每个分部是 `section > h2 > a`、一段目标 `p`、`ol > li > a`，有收束时再加 `p.toc-closing > a`。`.contents ol` 是 `columns: 2; column-gap: 3rem`，窄于 720px 改成 `columns: 1`。`.contents li` 只有 `break-inside: avoid; margin: .28rem 0`，行高继承正文的 `1.75`。目标段没有自己的规则，因此是正文色、正文字号、行高 `1.75`，也不受 `--measure` 约束。`.toc-closing` 只有 `margin: .2rem 0 0; font-weight: 700`。`.contents > section > h2` 粘性置顶，字号继承通用 `h2` 的 `1.42rem`，背景是 `var(--paper)`，阴影是 `0 1px 0 var(--line)`。`.toc-jump` 仍是固定定位的胶囊，`font-size: .85rem`，阴影是 `0 .45rem 1.2rem rgba(16, 24, 32, .18)`。
6. **代码块有两套字号，行内色块几乎看不见。** `code` 是 `.91em`，`pre code` 又写成 `.92em`。`pre` 的 `line-height` 是 `1.6`，margin 是 `1.15rem 0 1.5rem`。亮色 `--code: #101820`、`--code-ink: #eef6f8`，对比约 16.3。暗色 `--code: #0a141c`、`--code-ink: #edf6f9`，对比约 17.0。`:not(pre) > code` 的底是 `var(--panel)`（`#f1f5f7`）。这块底对 `--paper` 约 1.05，对插图混合底约 1.01，色块和纸贴在一起。`--line: #d7dce1` 对纸色约 1.3，加 1px 线也分不出边界。`.source-id code` 在后面把底改回 `var(--accent-soft)`、字色改成 `var(--accent)`；`#075e84` 对 `#e5f3f8` 约 6.3。`pre` 左边 `3px` 强调色条对代码底约 2.5，那是色条，不是文字。`pre` 已有 `tab-size: 4`、`user-select: text`、滚动提示和 `border-radius: var(--radius)`，没有 `box-shadow`。
7. **图注过得了对比，行高偏紧，印刷时比正文还大。** `figcaption` 是 `.9rem`、`line-height: 1.45`、`color: var(--muted)`、`margin: .15rem auto 0`。`figure img` 的下边距是 `.55rem`。`sub` 是 `.88rem`，没有自己的行高，继承 `1.75`。`table` 是 `.94rem`，`.source-card dl` 是 `.9rem`。按 WCAG 的 sRGB 相对亮度，`--muted: #5e6872` 对 `--paper` 约 5.4。插图底是 `color-mix(in srgb, var(--panel) 70%, var(--paper))`，算出来是 `#f4f6f7`，次要色对它约 5.2。阈值 4.5，两处都过。印刷把 `body` 设成 `9.5pt`，图注却仍是 rem：`.9rem` 约 10.8pt，大于正文。印刷的 `:root` 不重写 `--code` / `--code-ink`，再加 `print-color-adjust: exact`，印刷代码块沿用屏幕的深底。
8. **封面和分部页的展示字号是另一套。** `.cover h1` 是 `clamp(2.15rem, 5.6vw, 3.7rem)`，`.cover .subtitle` 是 `clamp(1.05rem, 2.4vw, 1.35rem)`，`.part-divider h1` 是 `clamp(2rem, 5vw, 3.35rem)`，`.part-goal` 是 `1.12rem`，`.part-index` 是 `clamp(4.5rem, 14vw, 8.5rem)`，窄屏分部序号是 `3rem`。扉页 `h1` 没有自己的 `font-size`。这些留给后面的封面刀。
9. **印刷阅读规则已经有测试。** `orphans: 3`、`widows: 3`；`figcaption` 的 `break-before: avoid-page` 与 `page-break-before: avoid`；`figure { background: transparent; }`；`@page { size: A4; margin: 16mm 15mm 18mm; }`；代码印刷是 `white-space: pre-wrap` 且 `break-inside: auto`（规则里不出现 `avoid`）。窄屏测试把列表标记锁成 `rgb(7, 94, 132)`，并要求 1200、840、390 三档 `pageOverflow` 为 0。
10. **版本字面量仍是 1.2.2。** `revisions.json` 第一条是 `1.2.2`（2026-10-25），其后是 `1.2.1`、`1.2.0`。两份 manifest 的 `version` 是 `1.2.2`，`date` 是 `2026-10-25`。`stm32-book/README.md` 当前版本句是 **v1.2.2 · 2026-10-25**。`test_visual_polish_version_is_1_2_0` 把 `entries[0]` 核对成 1.2.2，`entries[1]` 核对成 1.2.1，`entries[2]` 核对成 1.2.0。Batch4 的设计打算把这些断言改到 1.2.3，那次改动还没进 `main`。

对比都用和 `stm32-book/tests/test_build.py` 里 `_contrast_ratio` 相同的算法：（较亮 + 0.05）/（较暗 + 0.05）。

## 目标与非目标

### 目标

- 实施时只改 `stm32-book/build_html.py` 里的 `CSS` 字符串、`stm32-book/tests/test_build.py` 的断言，以及版本戳记（`revisions.json`、两份 manifest、`stm32-book/README.md`）。字体、字号、目录、代码块、图注和下面写明的印刷微调都留在 `CSS` 字符串里。本设计 PR 不动这些文件。
- 实施时的建议版本是 **1.2.4**。它排在 Batch4 的 1.2.3 之后。本设计 PR 不升版本。实施 PR 在 Batch4 已经合入 `main` 之后才开，除非用户明确说可以提前。
- 正文字号、`h1`–`h4`、眉题、图注和代码使用下面写死的自定义属性。封面标题、分部页大标题和 `.toc-jump` 保持现在的字面量。
- 目录的目标段、章列和分部收束行分成三种读法。`toc_html` 的标签不动。
- 行内代码和代码块共用一个字号。代码块补上能补中文缺字的等宽回退，行距用写死的值。印刷时代码块改为浅底，图注改为 9pt。
- 1.2.0 已经锁住的纸色、墨色、强调色、间距、圆角、阴影、`.55rem` 图距和印刷不断页规则继续通过现有测试。
- 实施 PR 在 Book CI 变绿之后 squash 合入 `main`。合入后在本机 `D:\Users\STM32` 拉取这次 `main`。拉取不产生仓库 diff。

### 非目标

- 不改 `docs/00`–`28`、`docs/en/`、附录 Markdown、`CONTENT_GUIDE.md` 中英、罗盘文案、`revisions.json` 里已有句子。本设计 PR 也不改两份 manifest 和 `stm32-book/README.md`。
- 不把 CSS 拆成独立 `.css`，不新增 design-token JSON。那是刀 B。
- 不改 `cover.svg`，不改 `.cover h1`、`.cover .subtitle`、`.part-divider h1`、`.part-goal`、`.part-index` 的字号和行高，不改扉页标题的字号。那是刀 D。
- 不重绘 `assets/` 里的样本 SVG、动画 SVG 或 GIF，不改 `tools/gen_sample_figures.py`、`tools/gen_gifs.py`、`tools/svgkit.py`。那是刀 C。
- 不加 `@font-face`，不写 `url(`，不引用 `fonts.googleapis` 或 `fonts.gstatic`。
- 不改 `.toc-jump` 的定位、字号、胶囊形和现有投影。
- 不改 `.book` 的宽度、`--measure`、`--inset`、四档 `--space-*`、`--radius`、`--elev`、`--leading-body`、`--tracking-body`、`--tracking-kicker`。
- 不改 callout 的分类逻辑、罗盘的 HTML 结构、出处卡的字段、`toc_html` 的标签。`.chapter-compass` 和 `.quick-check` 里继续没有 `h2`。
- 不加图目录或表目录。出版书签仍是 44 条。章号显示仍是文件名前缀加 1。
- 不改印刷的 `orphans`、`widows`、标题和图的 `break-*`、`figure { background: transparent; }`、`@page` 的毫米值、扉页的 `page-break-before: auto`。印刷正文保持 `9.5pt` 和 `line-height: 1.55`。
- 不把通用 `h2`–`h4` 的印刷字号从 rem 改成 pt。印刷标题仍然大于 9.5pt 的正文；这一刀只改正文图注和代码块。
- 不打 tag，不创建 GitHub Release。
- 不实施文末点名的 B、D、C。

## 方案 · 内联字号阶梯

视觉改动落在 `CSS` 字符串里。版本、README 和测试在后面两节另列。选择器的子组合保持原样：`.source-card h2` 不套用章内 `h2` 的左边条。`font-size` 写在 `body` 上，不写在 `html` 上，因此下面的 `rem` 仍按根元素的 16px 计算，1.2.0 的间距 rem 不变。

### 新增 token

在亮色 `:root` 增加且只增加下面这些自定义属性。暗色和印刷不重抄它们，需要压过屏幕的地方在 `@media print` 里另写。

| 属性 | 值 | 用在 |
| --- | --- | --- |
| `--font-sans` | `"Noto Sans CJK SC", "Microsoft YaHei", "PingFang SC", "Noto Sans SC", "Source Han Sans SC", "Segoe UI", system-ui, sans-serif` | `:root` 的 `font-family` |
| `--font-mono` | `"Cascadia Mono", "SFMono-Regular", Consolas, "Noto Sans Mono CJK SC", "Source Han Mono SC", "Sarasa Mono SC", "Liberation Mono", ui-monospace, monospace` | `code` 的 `font-family` |
| `--type-body` | `1.0625rem` | `body` 的 `font-size`。17px。印刷规则仍写 `9.5pt`，盖过它 |
| `--type-h1` | `clamp(1.85rem, 4.2vw, 2.7rem)` | 章、附录、分部收束、书末的 `header h1`。数值与现在相同 |
| `--type-h2` | `1.55rem` | 通用 `h2`。现在是 `1.42rem` |
| `--type-h3` | `1.35rem` | 通用 `h3`，以及目录粘性 `h2`。通用 `h3` 现在是 `1.16rem` |
| `--type-h4` | `1.2rem` | 通用 `h4`、`.quick-title`、`.source-card h2`。`h4` 现在是 `1.02rem` |
| `--type-kicker` | `0.78rem` | 下一节列出的眉题 |
| `--type-small` | `0.9375rem` | `figcaption`、`sub`、`table`、`.source-card dl`、目录目标段 |
| `--type-code` | `0.92em` | `code`。相对 `body`，屏幕上约 15.6px |
| `--leading-heading` | `1.35` | `h2, h3, h4` 和 `.source-card h2`。数值与现在相同 |
| `--leading-caption` | `1.55` | `figcaption` 和 `sub`。图注现在是 `1.45` |
| `--leading-toc` | `1.45` | `.contents li`。现在继承 `1.75` |
| `--leading-code` | `1.65` | 屏幕上 `pre` 的 `line-height`。现在是 `1.6` |

`--font-sans` 保留现在的前三名。已安装「Noto Sans CJK SC」「微软雅黑」或「苹方」的机器，拉丁字母和中文的首选不变。`Noto Sans SC`、`Source Han Sans SC`、`Segoe UI` 只在这三名都不存在时轮到。

`--font-mono` 保留 `Cascadia Mono`、`SFMono-Regular`、`Consolas` 为前三名。这三套没有的汉字继续往后匹配，轮到中文等宽，而不是直接掉进通用 `monospace`。

### 字号

屏幕上实际会变的只有这些：

| 角色 | 现在 | 实施后 |
| --- | --- | --- |
| 正文 | 不写字号 | `1.0625rem` |
| `h2` | `1.42rem` | `1.55rem` |
| `h3` | `1.16rem` | `1.35rem` |
| `h4` | `1.02rem` | `1.2rem` |
| `.quick-title` | `1.05rem` | `1.2rem` |
| `.source-card h2` | `1.12rem` | `1.2rem` |
| `.compass-role` | `.72rem` | `0.78rem` |
| `.callout-label` | `.74rem` | `0.78rem` |
| `.source-card dt` | `.75rem` | `0.78rem` |
| `.imprint .kicker`、修订史 `.kicker`、`.subject-index .kicker`、`.index-letter`、`.part-label` | `.82rem` | `0.78rem` |
| `figcaption` | `.9rem` / `1.45` | `0.9375rem` / `1.55` |
| `sub` | `.88rem` / 继承 `1.75` | `0.9375rem` / `1.55` |
| `table` | `.94rem` | `0.9375rem` |
| `.source-card dl` | `.9rem` | `0.9375rem` |
| 行内 `code` | `.91em` | `0.92em` |
| `pre code` | `.92em` | 删掉这里的 `font-size`，继承 `code` 的 `0.92em` |
| `pre` 行高 | `1.6` | `1.65` |

已经是 `.78rem` 的 `.cover .eyebrow`、`.closing-banner`、`.chapter-number`、`.compass-title`、`.source-id` 改成 `var(--type-kicker)`，算出来仍是 `0.78rem`。

规则：

- `body` 写上 `font-size: var(--type-body)`。`line-height: var(--leading-body)` 保持。
- `:root` 的 `font-family` 改为 `var(--font-sans)`。
- `.chapter > header h1, .appendix > header h1, .part-closing > header h1, .back-matter > header h1` 的 `font-size` 改为 `var(--type-h1)`。`line-height: 1.22` 保持字面量。
- `h2, h3, h4` 的 `line-height` 改为 `var(--leading-heading)`。`scroll-margin-top: 1.25rem` 保持。
- 通用 `h2` 改为 `font-size: var(--type-h2)`，margin 改为 `calc(var(--space-figure) + var(--space-paragraph)) 0 var(--space-bar)`。章、附录、分部收束的 `h2` 规则保持原文，含 `border-left: 3px solid var(--accent)` 和 `padding-left: var(--space-bar)`。`.companion h2` 更具体的 `margin-top: 0` 保持；它的下边距跟着通用 `h2`，从 `.6rem` 变成 `.75rem`。目录 `h2` 和 `.source-card h2` 仍写自己的 margin，不受这处影响。
- 通用 `h3` 改为 `font-size: var(--type-h3); margin: var(--space-figure) 0 calc(var(--space-bar) / 2)`。
- 通用 `h4` 改为 `font-size: var(--type-h4); margin: var(--space-paragraph) 0 calc(var(--space-bar) / 2)`。
- `.quick-title` 和 `.source-card h2` 的 `font-size` 改为 `var(--type-h4)`。`.source-card h2` 的 `line-height` 改为 `var(--leading-heading)`，margin 仍是 `0 0 .3rem`。
- 上一张表里的眉题，`font-size` 一律改为 `var(--type-kicker)`。字色、字重、字距不动。`.source-id` 和 `.source-card dt` 的 `letter-spacing: .04em` 保持。

封面 `h1`、封面副题、分部页 `h1`、`.part-goal`、`.part-index`、`.toc-jump` 的 `font-size` 声明保持现在的字面量，不引用这些 token。

### 目录

不改 `toc_html`。只改这些规则：

- `.contents > section > h2` 增加 `font-size: var(--type-h3)` 和 `line-height: var(--leading-heading)`。`position: sticky`、`background: var(--paper)`、`box-shadow: 0 1px 0 var(--line)` 保持。印刷里已有的 `position: static` 保持。
- 新增 `.contents > section > p:not(.toc-closing)`：`max-width: var(--measure); margin: calc(var(--space-bar) / 2) 0 var(--space-bar); color: var(--muted); font-size: var(--type-small); line-height: var(--leading-caption)`。
- `.contents li` 增加 `line-height: var(--leading-toc)`。`margin: .28rem 0` 和 `break-inside: avoid` 保持。
- `.contents ol` 保持 `columns: 2; column-gap: 3rem`。720px 规则里的 `columns: 1` 保持。
- `.toc-closing` 改为 `margin: var(--space-bar) 0 0; padding-top: calc(var(--space-bar) / 2); border-top: 1px solid var(--line); font-weight: 700`。不另设字号，收束链接保持正文大小。`p:not(.toc-closing)` 把目标段隔开，这条边线不会画到目标段上。
- 目录链接继续用全局 `a` 的颜色和下划线偏移。不去掉下划线。

### 代码

- `code` 改为 `font-family: var(--font-mono); font-size: var(--type-code)`。
- `:not(pre) > code` 的底改为 `color-mix(in srgb, var(--accent) 18%, var(--paper))`。`padding: .12em .35em` 和 `border-radius: .3em` 保持。不加边框：`--line` 对纸色只有约 1.3，1px 线分不出块。18% 的强调色混合对纸色约 1.3，墨色对这个混合底约 11.9；暗色里同一公式，墨色对比约 10.6。文字门槛仍是 4.5，混合底本身不拿去当文字色。
- `.source-id code` 保持 `color: var(--accent); background: var(--accent-soft)`。它写在 `:not(pre) > code` 之后，类选择器盖过行内色块。
- `pre` 的 `line-height` 改为 `var(--leading-code)`。margin 改为 `var(--space-paragraph) 0 var(--space-figure)`，也就是上 `1.25rem`、下 `1.5rem`。`border-left: 3px solid var(--accent)`、`border-radius: var(--radius)`、`tab-size: 4`、`user-select: text`、滚动条和四层 `background-image` 保持。继续不写 `box-shadow`。
- `pre code` 删掉 `font-size: .92em`。`color: inherit`、`background: transparent`、`padding: 0`、`white-space: inherit`、`user-select: text` 保持。
- 亮色 `--code: #101820`、`--code-ink: #eef6f8` 和暗色 `--code: #0a141c`、`--code-ink: #edf6f9` 保持。

### 图注

- `figcaption` 改为 `font-size: var(--type-small); line-height: var(--leading-caption)`。`max-width: var(--measure)`、`margin: .15rem auto 0`、`color: var(--muted)`、`text-align: center` 保持。
- `sub` 增加同样的 `font-size` 和 `line-height`。`display: block`、`color: var(--muted)`、`text-align: center` 保持。
- `figure img` 的 `margin: 0 auto .55rem` 保持。
- 图注字色保持 `var(--muted)`。纸色上约 5.4，插图混合底 `#f4f6f7` 上约 5.2，都不换色。

### 印刷

`@media print` 里只加这三处：

- 印刷 `:root` 增加 `--code: #f6f6f6; --code-ink: #111`。`#111` 对 `#f6f6f6` 约 17.5。屏幕深色代码块的两个十六进制留在屏幕规则里。
- 已有的印刷 `pre` 规则增加 `line-height: 1.45`。`white-space: pre-wrap`、`overflow-wrap: anywhere`、`break-inside: auto`、`page-break-inside: auto` 保持，规则文本里仍然不出现 `avoid`。
- 已有的印刷 `figcaption` 规则增加 `font-size: 9pt; line-height: 1.4`。另加一条 `sub { font-size: 9pt; line-height: 1.4; }`。9pt 小于正文的 `9.5pt`。不断页的四条 `break-*` / `page-break-*` 保持，选择器仍是单独的 `figcaption`，不改成逗号组合。

印刷 `body` 的 `font-size: 9.5pt; line-height: 1.55` 保持，因此 `--type-body` 不进入 PDF 正文。

## 版本与修订文案

本设计 PR 不改版本。实施 PR 才写。

实施开始时先读 `main` 上的 `stm32-book/manifest.json`。Batch4 的设计把下一版定为 **1.2.3**。本刀的建议版本是 **1.2.4**，日期用实施当天的 ISO 日期，`revisions.json`、两份 manifest 和 `stm32-book/README.md` 写同一个日期。

停手条件：

- `manifest.json` 的 `version` 还是 `1.2.2`：Batch4 还没合入。不实施，除非用户明确说可以提前。
- `version` 已经是 `1.2.3`：实施版写成 `1.2.4`。
- `version` 已经高于 `1.2.3`：实施版写成下一条修订号，不占用 `1.2.3`，也不把本文件里的 `1.2.4` 硬套上去。修订句子仍用下面四句。

`validate_revisions` 仍要求修订第一条的版本等于两份 manifest 的 `version`。新条目插在 `revisions.json` 最前，已有句子一字不改。

- `version`: 按上面的规则
- `date`: 实施当天
- `zh`:
  - 正文、标题和眉题改用一组字号；目录里的分部目标改成次要色，分部收束行加上分隔线。
  - 代码块补上能显示中文的等宽字体，行距略增；图注行距加大。印刷时代码块改为浅底，图注改为 9pt，不再大于正文。
- `en`:
  - Body, headings, and kickers use one type scale. Part goals in the contents are muted, and each part-closing line has a divider.
  - Code blocks gain a monospace stack that can show Chinese, with a slightly looser line-height. Captions gain line-height. In print, code blocks are light and captions are 9pt, no longer larger than the body.

不在修订说明里写刀 B、刀 D、刀 C，也不写 Batch4 的章节。

两份 manifest 只改 `version` 和 `date`。

`stm32-book/README.md`：

- 当前版本句改为 **v{新版本} · {实施日期}**。中英文整书仍共用这一版号。
- 发布节的版本句改为已经是这个版本。tag 名改为 `v{新版本}`。在现有误标句子的最后再加一句「也不要把 {上一版} 的产物标成 {新版本}」。已有的误标句子保留。
- 这一步仍不创建 tag，也不创建 Release。

## 测试

断言写在 `stm32-book/tests/test_build.py`。不新开测试文件。不新开浏览器用例。对比继续用已有的 `_contrast_ratio`，不增加依赖，也不在测试里重算 `color-mix`。

新增方法 `test_typography_e_css_contract`。1.2.0 的 `test_visual_polish_css_contract` 保持可过，不把这刀的断言塞进那个方法。屏幕段取第一个 `@media` 之前，印刷段取 `@media print` 之后，与现有视觉测试相同。`code` 的规则取屏幕段里先出现的 `code {`，不取 `pre code`。新方法核对：

- 亮色 `CSS` 含 `--font-sans`、`--font-mono`、`--type-body: 1.0625rem`、`--type-h1: clamp(1.85rem, 4.2vw, 2.7rem)`、`--type-h2: 1.55rem`、`--type-h3: 1.35rem`、`--type-h4: 1.2rem`、`--type-kicker: 0.78rem`、`--type-small: 0.9375rem`、`--type-code: 0.92em`、`--leading-heading: 1.35`、`--leading-caption: 1.55`、`--leading-toc: 1.45`、`--leading-code: 1.65`。
- `--font-sans` 的值以前三名 `"Noto Sans CJK SC", "Microsoft YaHei", "PingFang SC"` 开头，并且含 `"Noto Sans SC"`、`"Source Han Sans SC"`、`"Segoe UI"`。
- `--font-mono` 的值以前三名 `"Cascadia Mono", "SFMono-Regular", Consolas` 开头，并且含 `"Noto Sans Mono CJK SC"`、`"Source Han Mono SC"`、`"Sarasa Mono SC"`、`"Liberation Mono"`、`ui-monospace`。
- 屏幕段的 `body` 规则含 `font-size: var(--type-body)`。屏幕段的 `:root` 规则含 `font-family: var(--font-sans)`。
- `code` 规则含 `font-family: var(--font-mono)` 和 `font-size: var(--type-code)`。`pre code` 规则不含 `font-size`。
- `:not(pre) > code` 含 `color-mix(in srgb, var(--accent) 18%, var(--paper))`，不含 `border`。
- `.source-id code` 仍含 `background: var(--accent-soft)`。
- 屏幕 `pre` 含 `line-height: var(--leading-code)` 和 `margin: var(--space-paragraph) 0 var(--space-figure)`，含 `border-left: 3px solid var(--accent)`，不含 `box-shadow`。
- `figcaption` 与 `sub` 含 `font-size: var(--type-small)` 和 `line-height: var(--leading-caption)`。`figure img` 仍含 `margin: 0 auto .55rem`。
- `.contents li` 含 `line-height: var(--leading-toc)`。`.contents > section > p:not(.toc-closing)` 含 `color: var(--muted)` 和 `font-size: var(--type-small)`。`.toc-closing` 含 `border-top: 1px solid var(--line)`。`.contents > section > h2` 含 `font-size: var(--type-h3)` 和 `position: sticky`。
- `.compass-role`、`.callout-label`、`.source-card dt`、`.part-label` 含 `font-size: var(--type-kicker)`。
- `.cover h1` 仍含 `clamp(2.15rem, 5.6vw, 3.7rem)`。`.part-divider h1` 仍含 `clamp(2rem, 5vw, 3.35rem)`。`.toc-jump` 的规则仍含 `font-size: .85rem` 和 `box-shadow: 0 .45rem 1.2rem rgba(16, 24, 32, .18)`。
- 整段 `CSS` 不含 `@font-face`，不含 `url(`。
- 印刷 `:root` 含 `--code: #f6f6f6` 和 `--code-ink: #111`。印刷 `pre` 含 `line-height: 1.45`，且该规则不含 `avoid`。印刷 `figcaption` 含 `font-size: 9pt`、`line-height: 1.4`、`break-before: avoid-page`。

`test_visual_polish_contrast_clears_4_5` 追加这四对，门槛仍是 4.5：

- `#eef6f8` 对 `#101820`
- `#edf6f9` 对 `#0a141c`
- `#111` 对 `#f6f6f6`
- `#075e84` 对 `#e5f3f8`

不把 `#c4552a` 对纸色、代码左边条对代码底、行内色块混合底对纸色放进这张表。前两个本来就不是这张表的文字门槛；混合底是装饰。

版本断言按实施时的实际版本改，不在设计 PR 里改：

- `assert_version_history_and_index` 的元组在最前加上新版本，并断言它出现在上一版之前。
- `test_revision_file_lists_1_0_0_through_manifest_version` 的列表以新版本起头。
- `test_build_produces_one_complete_offline_book` 和 `test_english_book_is_a_separate_offline_edition` 里的 `<strong>v…</strong>` 改为新版本。
- `test_visual_polish_version_is_1_2_0` 改为核对新的第一条。现在对 `entries[0]`、`entries[1]`、`entries[2]` 的句子各后移一位。Batch4 若已把 1.2.3 放在第 0 位，实施时再后移一位，不改那些句子的原文。
- README 断言改为新的当前版本句、`版本号已经是 {新版本}`、新的误标句子，以及 `打 tag \`v{新版本}\``。

不删 `0x271`、`167 ns`、出版书签长度为 44、样本章、batch2、batch3 的断言。`pageOverflow` 为 0 的三档断言不放宽。若 `1.0625rem` 让这三档出现横向滚动，保持这个字号，也保持 `.book` 的宽度，只改那条把内容撑出视口的规则。不把正文字号改回 `1rem` 来换通过。

## 工作流与 PR 节奏

刀 E 沿用 1.2.0 观感那一刀的节奏：设计 PR 等人审阅后再合；实施 PR 在 Book CI 变绿后 squash 合入，不再做第二次正文复审。Batch4 的实施要等人看完四章 HTML，是因为它改正文。这一刀不改正文，所以实施阶段不照搬那个停点。

### 本 PR（设计）

只新增本文件。不改 `docs/` 章节、`docs/en/`、`stm32-book/`、`assets/`、`tools/`、`CREDITS.md`。不升版本，不打 tag，不发 Release。不新增 `docs/superpowers/plans/` 下的实施计划。本 PR 等人审阅规格后再合入，不在 CI 变绿后自动合。

### 实施 PR（下一轮，不在本 PR）

Batch4 合入 `main` 之前不开这个 PR，除非用户明确说可以提前。顺序固定：

1. **样式。** 按上一节改 `CSS` 字符串。`toc_html`、分类函数、罗盘 HTML、书签、章号、`sources` 渲染不动。
2. **测试。** 加上一节的断言，并把版本断言改到实施时的实际新版本。
3. **版本。** 同一提交内改 `revisions.json`、两份 manifest、`stm32-book/README.md`。修订说明只用上一节的四句。
4. **验证。** 下面三条通过之后再请求合入：

```bash
python3 -m unittest discover stm32-book/tests -v
python3 stm32-book/build_html.py --check
python3 stm32-book/build_html.py --lang en --check
```

5. **合入。** Book CI 变绿之后，把实施 PR squash 合入 `main`。合入后在 `D:\Users\STM32` 拉取这次 `main`。不打 tag，不创建 Release。

实施 PR 的 diff 可以碰：`stm32-book/build_html.py` 的 `CSS` 字符串、`stm32-book/tests/test_build.py`、`stm32-book/revisions.json`、`stm32-book/manifest.json`、`stm32-book/manifest-en.json`、`stm32-book/README.md`。不碰章节正文，不碰 `cover.svg`，不碰 `assets/`，不碰 `tools/`。

## 验收

### 本设计 PR

- 新增文件只有 `docs/superpowers/specs/2026-10-25-book-visual-typography-E-design.md`。
- `stm32-book/`、`docs/` 章节、`docs/en/` 章节、资产与工具和基线 `ea11ce7` 相同。
- 版本号仍是 1.2.2。没有 tag，没有 Release。

### 实施 PR

- 中文与英文 `python3 stm32-book/build_html.py --check` 以及 `--lang en` 通过。`python3 -m unittest discover stm32-book/tests -v` 通过。
- 上一节列出的 token、选择器和印刷片段都在。四对新增对比 ≥ 4.5。
- 亮色 `--accent` 仍是 `#075e84`，列表标记计算色仍是 `rgb(7, 94, 132)`。`--spine` 仍是 `#c4552a`。`h2` 左边框仍是 `3px`。屏幕上 `figure` 上边框仍是 `1px` 且填充非透明；印刷时 `figure` 填充透明。
- 屏幕代码色仍是 `#101820` / `#eef6f8`。印刷代码色是 `#111` / `#f6f6f6`。构建出的 HTML 仍不含 `fonts.googleapis` 和 `fonts.gstatic`。
- 人工打开构建出的中文 HTML，看三处：目录（目标段是次要色，收束行有上边线，窄屏仍是一列）；从第 00、03、04、06 章里任选一章，看 `h2` 左边条、一条含行内代码的句子、一个 `pre`、一张 `figure` 的图注；印刷预览里同一张图的图注小于正文，代码块是浅底。英文书用同一次构建抽目录或一章即可。
- `docs/` 与 `docs/en/` 的正文 diff 为空。`cover.svg` diff 为空。`assets/` diff 为空。
- 出版书签条数仍是 44。没有 tag，没有 Release。

## 后续刀

只点名，不在本文件里设计细节，也不进入刀 E 的实施 diff。顺序是 E 合入之后再写下一份设计。

1. **刀 B。** 从内联 `CSS` 字符串抽出独立 CSS 和 design-token JSON。
2. **刀 D。** 封面和扉页的图形升级。
3. **刀 C。** 重绘样本 SVG，统一画法。

## 未决问题

没有会挡住排版实施的未决项。下面几项按此处的默认执行，复审规格时可以改口，不需要再写一版设计才改 CSS：

1. **正文字号。** 屏幕用 `1.0625rem`。印刷保持 `9.5pt`。
2. **眉题。** 散落的 `.72rem` 到 `.82rem` 收成 `0.78rem`。
3. **行内代码。** 用 18% 强调色混合底，不加边框。`.source-id code` 保持 `--accent-soft`。
4. **印刷代码块。** 改为 `#f6f6f6` 底、`#111` 字。屏幕深色代码块的十六进制不改。
5. **封面和分部页大字。** 保持现在的 `clamp`。不进这组 token。
6. **版本。** 建议 1.2.4，排在 Batch4 的 1.2.3 之后。本 PR 不升。实施合入不打 tag，不创建 Release。

## 英文提要

Typography micro-polish only, on v1.2.2 (`ea11ce7`, PR #33). Edit the inlined `CSS` string in `stm32-book/build_html.py` and the assertions in `stm32-book/tests/test_build.py`. Add a type scale on `body` (`--type-body: 1.0625rem`, print stays 9.5pt) with `--type-h1` left at the current chapter clamp, `--type-h2: 1.55rem`, `--type-h3: 1.35rem`, `--type-h4: 1.2rem`, `--type-kicker: 0.78rem`, and `--type-small: 0.9375rem`. Keep the current first three faces in both stacks, and append CJK and Latin fallbacks; do not add `@font-face` or a font URL. Mute the contents goal, tighten contents line-height to 1.45, and give `.toc-closing` a top rule. Share `0.92em` for inline and block code, set block line-height to 1.65, and paint inline code with `color-mix(in srgb, var(--accent) 18%, var(--paper))`. Raise caption line-height to 1.55. In print, set code to `#111` on `#f6f6f6` and captions to 9pt. Leave cover clamps, part-divider display type, `.toc-jump`, the 1.2.0 spacing ladder, chapter Markdown, and sample SVGs alone. The provisional implementation version is 1.2.4 after Batch4 lands as 1.2.3; do not start that PR until Batch4 is on `main` unless the user says otherwise, then squash-merge it after Book CI is green. Later knives, named only: B extracts the CSS and a token JSON, D upgrades cover and imprint art, C redraws the sample SVGs. This design PR only adds this file and waits for human review.

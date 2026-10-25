# 整书密度刀 F 设计

日期：2026-10-25  
状态：待人审。人接受这份规格之前不实施  
基线：`main` 上的整书 **v1.2.7**（`a481335f4d56658dc4c356454431dd4398ccff3f`，PR #47，2026-10-25）  
上一份视觉设计：[2026-10-25-book-visual-sample-svg-C-design.md](2026-10-25-book-visual-sample-svg-C-design.md)。刀 C 已在 `a481335` 合入。更早的观感顺序是 E → B → D → C，分别是排版、令牌抽出、封面与扉页、样本图。  
本文件只记录刀 F 的设计。它不改 `build_html.py`，不改正文，不升版本号，不打 tag，不发布 Release，不新增 `docs/superpowers/plans/` 下的实施计划。

视觉刀 E、B、D、C 已经做完。这一刀只收阅读面上的空白。

## 背景

对照 `a481335` 的 `stm32-book/styles/tokens.json`、`stm32-book/styles/book.css` 和 `stm32-book/build_html.py` 里的 `load_css()` 核对过的事实：

1. **样式在两份文件里，构建时拼进一段字符串。** `tokens.json` 的 `schema` 是整数 `1`。顶层键顺序是 `schema`、`light`、`dark`、`print`、`coverLock`。`light` 是 40 个自定义属性，键序与 `_CSS_LIGHT_KEYS` 相同。`dark` 和 `print` 各是那 15 个颜色。`coverLock` 是 `--paper`、`--ink`、`--muted`、`--warn`、`--line`、`--spine`。`load_css()` 在 import 时把四个哨兵填进 `book.css`，结果赋给模块级 `CSS`。HTML 仍是 `<style>{CSS}</style>`。中英文走同一次加载。
2. **拼合结果的哈希仍是刀 D 留下、刀 C 锁住的那一串。** `builder.CSS` 的 SHA-256 是 `a4ccd1403ab742e82f67c39053c2609da1c9a8afa126d4f6b988a5b9559a5ac4`。`test_css_token_extract_contract` 和 `test_sample_svg_c_contract` 都断言这一串。`tokens.json` 的 SHA-256 是 `c5bb7846ed74c394f59634b1b40c99d1264c9dd41b018dfb7bfad8a08bea014b`。`book.css` 源文件 19838 字节，SHA-256 是 `7c821dba13bebb86123def3f243a480af460d897358d548c364860038fb563f5`。`cover.svg` 的 SHA-256 是 `37dbedd70d2be8e94f4cdf05b60541f69d0107af6374902f8062c8e0bf74dedd`。
3. **阅读面偏松的七个亮色值就是下面这些。** 根字号按 16px 计，正文是 `--type-body: 1.0625rem`（17px）。

| 属性 | 现在 | 16px 根上的长度 | 现在落在 |
| --- | --- | --- | --- |
| `--space-chapter` | `3.5rem` | 56px | 章、附录、分部收束、书末、文前、目录、扉页的上下 padding；`.part-divider` 的 `margin-top` |
| `--space-figure` | `1.5rem` | 24px | `figure` 和裸 `img` 的上下 margin；与段距折叠后，段到图的空隙是 24px |
| `--space-paragraph` | `1.25rem` | 20px | 章内直接子级 `p` 的上下 margin。相邻段折叠后是 20px |
| `--space-bar` | `0.75rem` | 12px | 章内 `h2` 的左槽和 `h2` 的下边距；`h3` / `h4` 的下边距是它的一半（6px） |
| `--inset` | `6%` | 980px 书宽上每侧 58.8px | 上述块和 `.part-divider`、`.cover-panel` 的左右 padding。窄于 720px 时这些块改成字面量 `1rem`，`--inset` 不参与 |
| `--leading-body` | `1.75` | 行框 29.75px | `body` 的 `line-height`。印刷 `body` 另写 `9.5pt` 和 `line-height: 1.55`，盖过它 |
| `--measure` | `40rem` | 640px | 章内 `p` 和 `li`、callout、图注、目录目标段的 `max-width`。全角约 37.6 字 |

4. **有一批阅读面空白不走这七个变量。** `.chapter > header` 的 `margin-bottom` 是 `1.6rem`，`padding-bottom` 是 `.95rem`。`aside.chapter-compass` 的规则是 `.chapter-compass`：`margin: 1.5rem 0 2.6rem`，`gap: .75rem`，`padding: .95rem`。`aside.companion` 的规则是 `.companion`：`margin-top: 2rem`，`padding: 1rem 1.2rem`。`.quick-check` 的 `margin` 是 `3rem 0 1rem`。`blockquote.callout` 的 `margin` 是 `1.25rem 0 1.45rem`。`figure` 的内边距是 `.75rem .75rem .65rem`，`figure img` 的下边距是 `.55rem`。`.table-scroll` 的 `margin` 是 `1.25rem 0 2rem`。`.contents > section` 的 `padding` 是 `1.2rem 0`。`.contents ol` 的 `column-gap` 是 `3rem`。`.contents li` 的 `margin` 是 `.28rem 0`。`.contents > section > h2` 的 `padding` 是 `.85rem 0 .45rem`。`.back-to-toc` 的 `margin-top` 是 `2.2rem`。`footer.book-footer` 的 `padding` 是 `3rem 6% 5.2rem`，这里的 `6%` 是字面量，不是 `var(--inset)`。`.revision-history > p, .index-lead` 的 `max-width` 是字面量 `40rem`，不是 `var(--measure)`。
5. **封面和分部海报用另一套空白。** `.cover` 的 `min-height` 是 `92vh`。`.cover-panel` 的 `padding` 是 `1.8rem var(--inset) 2.6rem`。窄屏封面是 `1.3rem 1rem 1.8rem`。`.part-divider` 的 `min-height` 是 `52vh`，上下 padding 是 `4.5rem`，左右是 `var(--inset)`。这些不是章内阅读面。
6. **颜色、字号和 `load_css()` 已经锁住。** 亮色 `--paper` 是 `#fbfaf7`，`--ink` 是 `#17202a`，`--accent` 是 `#075e84`，`--spine` 是 `#c4552a`。暗色和印刷只重写 15 个颜色。`book.css` 里的画板三色仍是 `#10242e`、`#0c1c24`、`#f4f1ea`。字号阶梯从 `--type-body` 到 `--type-code`，以及 `--leading-heading`、`--leading-caption`、`--leading-toc`、`--leading-code`，都保持刀 E 的值。`load_css()` 不改键序、不改 schema、不改哨兵。
7. **会跟着令牌变、但源规则不必改写的派生值。** `h2` 的上边距是 `calc(var(--space-figure) + var(--space-paragraph))`，现在是 `2.75rem`。`h3` 的上边距是 `var(--space-figure)`。`h4` 的上边距是 `var(--space-paragraph)`。`h3` 和 `h4` 的下边距是 `calc(var(--space-bar) / 2)`。`pre` 的 margin 是 `var(--space-paragraph) 0 var(--space-figure)`。这些 `calc()` 和 `var()` 的源文本要原样留下。测试断言的就是这几段源文本。
8. **版本字面量是 1.2.7。** `revisions.json` 第一条是刀 C 的两句，日期 `2026-10-25`。两份 manifest 的 `version` 是 `1.2.7`。`stm32-book/README.md` 当前版本句是 **v1.2.7 · 2026-10-25**。`test_visual_polish_version_is_1_2_0` 把 `entries[0]` 核对成 1.2.7，`entries[1]` 核对成 1.2.6，一直到 `entries[7]` 的 1.2.0。

## 目标与非目标

### 目标

- 阅读面更紧凑，字距和行距仍能分开相邻的字、段和图。章间、段间、图间、左右 inset、正文行高各收一档。`--measure` 只加 `2rem`。
- 实施时只改 `stm32-book/styles/tokens.json` 的七个值、`stm32-book/styles/book.css` 里下面点名的那些空白、`stm32-book/tests/test_build.py` 与 `stm32-book/tests/test_sample_svg_c.py` 里因此失效的断言，以及版本戳记（`revisions.json`、两份 manifest、`stm32-book/README.md`）。
- 封面标题板的左右留在字面量 `6%`，与新的 `--inset` 脱钩。封面 SVG、`coverLock` 的六个名字、画板三色保持。
- 配色、字号阶梯、圆角、阴影、字体栈保持。暗色和印刷的 15 个颜色保持。样本 SVG、封面 SVG、GIF 的字节保持。
- 实施时的版本目标是 **1.2.8 · 2026-10-25**。本设计 PR 不升版本。
- 中文 `python3 stm32-book/build_html.py --check`、英文 `python3 stm32-book/build_html.py --lang en --check`、`python3 -m unittest discover stm32-book/tests -v` 都通过。宽于 960px 的窗口里，章内空白比 1.2.7 明显少一档。
- 设计 PR 与实施 PR 都等人审。CI 变绿之后不自动合。squash 由人决定。合入不打 tag，不创建 Release。

### 非目标

- 不加厚 `docs/` 或 `docs/en/` 的章节，不改附录 Markdown、`CONTENT_GUIDE.md`、罗盘文案、`revisions.json` 里已有句子。本设计 PR 也不改两份 manifest 和 `stm32-book/README.md`。
- 不修封面或分部页的海报构图。`.cover` 的 `92vh`、`.part-divider` 的 `52vh` 和 `4.5rem` 上下 padding、分部大标题和 `.part-index` 的字号保持。
- 不重绘 `cover.svg`，不重绘 `assets/` 里的样本 SVG、动画 SVG 或 GIF，不改 `tools/`。
- 不大改暗色色板或印刷色板。15 个颜色的值、`print-color-adjust`、`@page` 的毫米值、印刷正文 `9.5pt` / `1.55`、图注 `9pt` 保持。
- 不改字号令牌、`--leading-heading`、`--leading-caption`、`--leading-toc`、`--leading-code`、`--tracking-body`、`--tracking-kicker`、`--radius`、`--elev`。
- 不改 `.toc-jump` 的定位、字号、胶囊形和投影。
- 不改 `.book` 的 `980px` 上限，不把 CSS 拆文件，不升 `schema`，不加新的自定义属性，不改 `load_css()`。
- 不改 `.github/workflows/book.yml`。
- 不打 tag，不创建 GitHub Release。

## 方案

空白有三处来源：七个亮色令牌、阅读面上写死的 margin / padding / gap、封面和分部页的整页留白。

做法 1 只改七个令牌，`book.css` 的选择器不动。派生的 `calc()` 会跟着变。封面标题板仍写着 `var(--inset)`，左右会从 6% 收到 4.5%。罗盘下边距 `2.6rem`、自测上边距 `3rem`、页脚下边距 `5.2rem`、目录栏距 `3rem` 仍在。最大的几块洞还在，封面却被带上。

做法 2 把七个令牌收一档，并把第 4 点列出的阅读面字面量按下一节改掉。`.cover-panel` 的左右改成字面量 `6%`，标题板的几何回到 1.2.7。分部页的 `52vh` 和封面的 `92vh` 不动。`calc()` 的源文本不动，算出来的间距跟着新令牌走。

做法 3 连字号、`980px` 书宽和分部页 `52vh` 一起收。字号是刀 E 已经锁住的阶梯。把书宽改窄，行长不变，空白只是挪到书外的纸色上。把 `52vh` 改矮，是在改海报，不是在改阅读面。

采用做法 2。

## 令牌

只改 `light` 里这七个值。键名、键序、其余 33 个亮色值、`dark`、`print`、`coverLock`、`schema` 保持。JSON 保持两个空格缩进，不重排。

| 属性 | 现在 | 实施后 | 理由 |
| --- | --- | --- | --- |
| `--space-chapter` | `3.5rem` | `2.75rem` | 每章上下各少 12px，一章少 24px。`2.75rem` 等于现在的 `h2` 上边距，新的章距等于旧的节距，仍大于一行正文（约 28px）。收到 `2.5rem` 会贴边。 |
| `--space-figure` | `1.5rem` | `1.25rem` | 与新段距仍差 `0.25rem`。段到图折叠后是 20px，图和段仍分开。 |
| `--space-paragraph` | `1.25rem` | `1rem` | 相邻段折叠后是 16px。新行框约 28px，段距约 0.57 行。收到 `0.75rem` 会和行距糊在一起。 |
| `--space-bar` | `0.75rem` | `0.625rem` | 章内 `h2` 的左槽。全档收到 `0.5rem` 时，3px 强调条会贴字。`0.625rem` 仍留出 10px。`h3` / `h4` 的下边距变成 `0.3125rem`。 |
| `--inset` | `6%` | `4.5%` | 980px 书宽上每侧从 58.8px 收到 44.1px。窄于约 760px、行长还没被 `--measure` 截住时，两侧空白直接减少。收到 `3%` 会贴边；收到 `5%` 在宽屏上几乎看不出来。封面不跟这个百分比走。 |
| `--leading-body` | `1.75` | `1.65` | 四十行大约少 68px，是阅读面上最大的一笔。17px 中文收到 `1.6` 开始挤。印刷正文仍是 `1.55`，盖过这个值。 |
| `--measure` | `40rem` | `42rem` | 全角从约 37.6 字到约 39.5 字，仍不超过 40 字。拉丁字母按半角估算约从 75 到 79。宽屏上文字柱加 32px，用来抵消 inset 变小后内容盒变宽、右侧空隙变大的那一截。缩到 `38rem` 会多出右侧空白。放到 `44rem` 会超过 40 个全角字，并在 720px 断点上失去行长上限。 |

派生结果（源文本仍是原来的 `var()` / `calc()`）：

| 规则 | 现在 | 实施后 |
| --- | --- | --- |
| `h2` 上边距 | `2.75rem` | `2.25rem` |
| `h2` 下边距 | `0.75rem` | `0.625rem` |
| `h3` 上下 | `1.5rem` / `0.375rem` | `1.25rem` / `0.3125rem` |
| `h4` 上下 | `1.25rem` / `0.375rem` | `1rem` / `0.3125rem` |
| 相邻段，折叠后 | `1.25rem` | `1rem` |
| 段到 `figure`，折叠后 | `1.5rem` | `1.25rem` |
| `pre` 上下 | `1.25rem` / `1.5rem` | `1rem` / `1.25rem` |
| 正文行框 | 29.75px | 28.05px |
| 章上下 padding | 56px | 44px |

`h2, h3, h4` 的 `scroll-margin-top: 1.25rem` 是字面量，保持。它不是 `--space-paragraph`。

## 必须改的 CSS 规则

下面每一处在 `a481335` 的 `book.css` 里都只出现一次。实施时按旧字符串整段替换，不重排文件，不把 `.75rem` 收成 `0.75rem`。样式表里的新长度沿用文件里已有的写法：小数前不写 0。JSON 里的新长度沿用 JSON 里已有的写法：小数前写 0。

| 选择器 | 旧片段 | 新片段 | 原因 |
| --- | --- | --- | --- |
| `.cover-panel` | `padding: 1.8rem var(--inset) 2.6rem` | `padding: 1.8rem 6% 2.6rem` | 标题板与新 inset 脱钩。上下仍是 `1.8rem` 和 `2.6rem` |
| `.chapter > header, .appendix > header, .part-closing > header, .back-matter > header` | `margin-bottom: 1.6rem; padding-bottom: .95rem` | `margin-bottom: 1.25rem; padding-bottom: .75rem` | 标题到正文的空隙收一档 |
| `.chapter-compass` | `gap: .75rem; margin: 1.5rem 0 2.6rem; padding: .95rem` | `gap: .625rem; margin: 1.25rem 0 1.75rem; padding: .75rem` | 罗盘外的 `2.6rem` 是章内最大的一块洞。元素是 `aside`，选择器仍是这个类 |
| `.companion` | `margin-top: 2rem; padding: 1rem 1.2rem` | `margin-top: 1.5rem; padding: .85rem 1rem` | 文前配套块。元素是 `aside`，选择器仍是这个类 |
| `.quick-check` | `margin: 3rem 0 1rem` | `margin: 2rem 0 .75rem` | 自测题上边距 `3rem` 接近旧的章距。内边距 `1rem 1.4rem` 保持 |
| `blockquote.callout` | `margin: 1.25rem 0 1.45rem` | `margin: 1rem 0 1.25rem` | 与新的段距、图距对齐。内边距保持 |
| `figure` | `padding: .75rem .75rem .65rem` | `padding: .6rem .65rem .5rem` | 图框内的空白。`margin: var(--space-figure) auto` 保持 |
| `figure img` | `margin: 0 auto .55rem` | `margin: 0 auto .4rem` | 图到图注。刀 E 留下的 `.55rem` 属于图间空白，这一刀改 |
| `.table-scroll` | `margin: 1.25rem 0 2rem` | `margin: 1rem 0 1.5rem` | 表和周围段落的空隙。下边距 `2rem` 比图距还松 |
| `.contents > section` | `padding: 1.2rem 0` | `padding: .85rem 0` | 目录每一分部的上下 |
| `.contents ol` | `column-gap: 3rem` | `column-gap: 2.25rem` | 两列之间。`columns: 2` 保持；720px 的 `columns: 1` 保持 |
| `.contents li` | `margin: .28rem 0` | `margin: .2rem 0` | 目录行距。`line-height: var(--leading-toc)` 保持 |
| `.contents > section > h2` | `padding: .85rem 0 .45rem` | `padding: .6rem 0 .35rem` | 粘性分部标题的上下。`position: sticky`、字号、阴影保持 |
| `.back-to-toc` | `margin-top: 2.2rem` | `margin-top: 1.5rem` | 章末回目录链接上面的空隙 |
| `footer.book-footer` | `padding: 3rem 6% 5.2rem` | `padding: 2.25rem var(--inset) 3.5rem` | 去掉第二份写死的 `6%`，左右跟新 inset。下边距从 `5.2rem` 收到 `3.5rem` |
| `.revision-history > p, .index-lead` | `max-width: 40rem` | `max-width: var(--measure)` | 修订史导语和索引导语跟正文同一行长。颜色 `var(--muted)` 保持 |

窄屏这条保持原文：`.cover-panel { padding: 1.3rem 1rem 1.8rem; }`。720px 段里仍然不出现 `var(--inset)`。

## 源文本保持、数值跟着令牌走的规则

这些规则不改写。实施后它们的计算值变成上一节的派生表。

- `body` 的 `line-height: var(--leading-body)`。
- `.imprint, .frontmatter, .contents` 和 `.chapter, .appendix, .part-closing, .back-matter` 的 `padding: var(--space-chapter) var(--inset)`。
- `.part-divider` 的 `padding: 4.5rem var(--inset) 4.5rem` 和 `margin-top: var(--space-chapter)`。`min-height: 52vh` 保持。
- `h2`、`h3`、`h4`、`.chapter > h2, .appendix > h2, .part-closing > h2` 的 `margin` 和 `padding-left: var(--space-bar)`。`border-left: 3px solid var(--accent)` 保持。
- `.chapter > p, .appendix > p, .part-closing > p` 的两段 `var(--space-paragraph)`。
- `img` 和 `figure` 的 `margin: var(--space-figure) auto`。
- `pre` 的 `margin: var(--space-paragraph) 0 var(--space-figure)`。
- `.toc-closing` 的 `var(--space-bar)`。
- `.contents > section > p:not(.toc-closing)` 的 `var(--space-bar)` 和 `max-width: var(--measure)`。
- 已经写着 `max-width: var(--measure)` 的章内段落、列表项、callout、图注。

## 这一刀留在原处的空白

- `.cover` 的 `min-height: 92vh`，`.cover-sheet` 的行高，`.cover h1`、`.cover .subtitle`、`.cover .rule`、`.cover .edition` 的字号和 margin。`.cover .edition` 的 `max-width: 36rem` 保持。
- `.part-divider` 的 `4.5rem` 上下、`52vh`、`gap: .35rem`。`.part-goal` 的 `max-width: min(36rem, …)` 和 `line-height: 1.6` 保持。`.part-index` 的 `clamp` 和窄屏 `3rem` 保持。
- 扉页内部：`.imprint-lead, .imprint .colophon` 的 `max-width: 40em`，`.imprint dl` 的 `max-width: 46rem` 和 `margin: 1.5rem 0 0`，`h1::after` 的 `4.2rem` 乘 `.18rem`。扉页上下 padding 跟着 `--space-chapter`。
- `.compass-card` 的内边距和 `border-radius: .5rem`。`.route`、`.source-card`、`pre`、`th, td` 的内边距。
- `.revision-list` 的 `1.4rem` / `1.1rem`。
- `.toc-jump` 整条规则。
- `@media print` 里的 `padding: 0`、`line-height: 1.55`、`9.5pt`、`9pt`、`@page` 的毫米值、孤行寡行和 `break-*`。印刷的标题和图距会因为共用令牌而略紧，这是这一刀要的结果。不要为了让印刷间距保持 1.2.7 再写一套覆盖。

## 哈希

本刀改令牌和 `book.css`，拼合哈希不再是 `a4ccd140…`。三个新值按上面的替换、在 `a481335` 的文件上逐段代入后计算。代入前，未改文件的拼合结果仍是 `a4ccd1403ab742e82f67c39053c2609da1c9a8afa126d4f6b988a5b9559a5ac4`，与现有测试一致。算法与 `load_css()` 的四个哨兵替换相同。

| 对象 | 现在 | 实施后，且只做了上面的替换 |
| --- | --- | --- |
| `builder.CSS` | `a4ccd1403ab742e82f67c39053c2609da1c9a8afa126d4f6b988a5b9559a5ac4` | `aacd30dcb0efbff80d004295338c9be99b35e19cb744d6f4b1e662a0b8f31baf` |
| `stm32-book/styles/tokens.json` | `c5bb7846ed74c394f59634b1b40c99d1264c9dd41b018dfb7bfad8a08bea014b` | `9d07dad497b824c9e2038ddf1e28cb77974451acb6c3b9773863df7c8c90d0bd` |
| `stm32-book/styles/book.css` | `7c821dba13bebb86123def3f243a480af460d897358d548c364860038fb563f5` | `cc2656e9c7e0ea311fc79d36c920c20d82012d8907b000ec940a93095845e480` |
| `stm32-book/cover.svg` | `37dbedd70d2be8e94f4cdf05b60541f69d0107af6374902f8062c8e0bf74dedd` | 保持这一串 |

多一个字节或少一个字节，哈希就会离开这张表。那时先停，对照替换表看多改了什么，不要改测试里的期望去迁就另一份样式。

## 版本与修订文案

本设计 PR 不改版本。实施 PR 才写。

实施开始时先读 `main` 上的 `stm32-book/manifest.json`。

- `version` 仍是 `1.2.7`：实施版写成 `1.2.8`，日期写成 `2026-10-25`。
- `version` 已经高于 `1.2.7`：实施版写成下一条修订号，日期用实施当天的 ISO 日期，不把本文件里的 `1.2.8` 硬套上去。修订句子仍用下面四句。

`revisions.json`、两份 manifest、`stm32-book/README.md` 写同一个版本和同一个日期。新条目插在最前，已有句子一字不改。

- `version`: 按上面的规则
- `date`: 按上面的规则
- `zh`:
  - 章距、段距、图距、左右页边和正文行高各收一档，行长从 40rem 调到 42rem。字号和颜色不变。
  - 封面标题板的左右页边仍是 6%。暗色和印刷的颜色不改。样本图、封面图和 GIF 不重画。
- `en`:
  - Chapter, paragraph, and figure spacing, the side inset, and the body line-height each move one step tighter. The measure moves from 40rem to 42rem. Type size and colors stay.
  - The cover title plate keeps a 6% side inset. The dark palette and the print palette stay. Sample drawings, the cover drawing, and GIFs are not redrawn.

两份 manifest 只改 `version` 和 `date`。

`stm32-book/README.md`：

- 当前版本句改为 **v{新版本} · {实施日期}**。
- 发布节的版本句改为已经是这个版本。tag 名改为 `v{新版本}`。在现有误标句子的最后再加一句「也不要把 1.2.7 的产物标成 {新版本}」。已有的误标句子保留，包括「也不要把 1.2.6 的产物标成 1.2.7」。
- 构建节里关于 `tokens.json` 和 `book.css` 的那一句保留。
- 这一步仍不创建 tag，也不创建 Release。

## 测试

不新开测试文件。断言仍在 `stm32-book/tests/test_build.py` 和 `stm32-book/tests/test_sample_svg_c.py`。

`test_visual_polish_css_contract` 里这七个字符串改成新值，并在同一组里加上 `--measure: 42rem`（现在这一组没有锁 measure 的值）：

- `--space-bar: 0.75rem` → `--space-bar: 0.625rem`
- `--space-paragraph: 1.25rem` → `--space-paragraph: 1rem`
- `--space-figure: 1.5rem` → `--space-figure: 1.25rem`
- `--space-chapter: 3.5rem` → `--space-chapter: 2.75rem`
- `--inset: 6%` → `--inset: 4.5%`
- `--leading-body: 1.75` → `--leading-body: 1.65`
- 新增 `--measure: 42rem`

同一方法里：

- 两处 `margin: 0 auto .55rem` 里，`test_visual_polish_css_contract` 的那一处改为 `margin: 0 auto .4rem`。
- `padding: 1.8rem var(--inset) 2.6rem` 改为 `padding: 1.8rem 6% 2.6rem`。

`test_typography_e_css_contract` 里：

- `margin: 0 auto .55rem` 改为 `margin: 0 auto .4rem`。
- `.contents li` 的 `margin: .28rem 0` 改为 `margin: .2rem 0`。
- `.contents ol` 的 `column-gap: 3rem` 改为 `column-gap: 2.25rem`。

下面这些断言的源文本保持，用来防止把 `calc()` 展成字面量，或把封面窄屏、分部海报一起改掉：

- `margin: calc(var(--space-figure) + var(--space-paragraph)) 0 var(--space-bar)`
- `margin: var(--space-figure) 0 calc(var(--space-bar) / 2)`
- `margin: var(--space-paragraph) 0 calc(var(--space-bar) / 2)`
- `padding-left: var(--space-bar)` 与 `border-left: 3px solid var(--accent)`
- `padding: 4.5rem var(--inset) 4.5rem` 与 `min-height: 52vh`
- `margin: var(--space-figure) auto` 与 `margin: var(--space-paragraph) 0 var(--space-figure)`
- `line-height: var(--leading-body)` 与全部 `--type-*`、`--leading-heading`、`--leading-caption`、`--leading-toc`、`--leading-code`
- 窄屏 `.cover-panel { padding: 1.3rem 1rem 1.8rem; }`，以及 720px 切片里不出现 `var(--inset)`
- `columns: 2` 与窄屏 `columns: 1`
- 对比仍用 `_contrast_ratio`，门槛仍是 4.5。色值一对都不改
- 1200、840、390 三档的 `pageOverflow` 仍为 0。断言的期望保持 0

`test_css_token_extract_contract` 和 `test_sample_svg_c_contract` 里的拼合哈希改为 `aacd30dcb0efbff80d004295338c9be99b35e19cb744d6f4b1e662a0b8f31baf`。

`test_sample_svg_c_contract` 里：

- `tokens.json` 的哈希改为 `9d07dad497b824c9e2038ddf1e28cb77974451acb6c3b9773863df7c8c90d0bd`。
- `book.css` 的哈希改为 `cc2656e9c7e0ea311fc79d36c920c20d82012d8907b000ec940a93095845e480`。
- `cover.svg` 的哈希仍是 `37dbedd70d2be8e94f4cdf05b60541f69d0107af6374902f8062c8e0bf74dedd`。
- 53 张 SVG 的画布、文本哈希、60 KB / 80 KB 上限、GIF 汇总哈希的断言保持原文。

版本断言按实施时的实际版本改，不在设计 PR 里改：

- `assert_version_history_and_index` 的元组在 `1.2.7` 前加上新版本，并断言 `>{新版本}<` 出现在 `>1.2.7<` 之前。
- `test_revision_file_lists_1_0_0_through_manifest_version` 的列表以新版本起头，下一项仍是 `1.2.7`。
- 两处 `<strong>v1.2.7</strong>` 改为新版本。英文 manifest 的版本等式一并改。
- `test_visual_polish_version_is_1_2_0` 把现在的 `entries[0]` 到 `entries[7]` 各后移一位。1.2.7 的刀 C 两句改去核对 `entries[1]`，其后的 1.2.6 直到 1.2.0 顺延。句子原文不改。新的 `entries[0]` 用上一节的四句，日期等于两份 manifest 的 `date`。
- README 断言改为新的当前版本句、`版本号已经是 {新版本}`、新的误标句子，以及 `打 tag \`v{新版本}\``。`也不要把 1.2.6 的产物标成 1.2.7` 这句保留。

停手条件：实施开始时若 `builder.CSS` 的 SHA-256 已经不是 `a4ccd140…`，或 `tokens.json` / `book.css` 的哈希已经不是背景一节的两串，先停。说明 `main` 上的样式已经离开这份设计所依据的字节，不要在分叉上套这七个值。

## 工作流与 PR 节奏

设计 PR 等人审阅后再合。实施 PR 在 `book` 与 `book-en` 变绿之后仍等人决定是否 squash。两份 PR 都不在 CI 变绿后自动合。这一刀不改正文。

### 本 PR（设计）

只新增本文件。不改 `docs/` 章节、`docs/en/`、`stm32-book/`、`assets/`、`tools/`、`CREDITS.md`、`.github/`。不升版本，不打 tag，不发 Release。不新增实施计划。

### 实施 PR（下一轮，不在本 PR）

顺序固定：

1. **确认基线。** `builder.CSS`、`tokens.json`、`book.css` 的哈希仍是背景一节的三串。`cover.svg` 的哈希仍是 `37dbedd7…`。
2. **令牌。** 只替换「令牌」一节那七个值。
3. **样式。** 只做「必须改的 CSS 规则」一节那 16 处替换。
4. **测试。** 按「测试」一节改断言。版本断言留到下一步一起改。
5. **版本。** 同一 PR 内改 `revisions.json`、两份 manifest、`stm32-book/README.md`，并把版本断言改到实施时的实际新版本。修订说明只用上一节的四句。
6. **验证。** 下面三条通过，并且三个新哈希与封面哈希与「哈希」一节一致之后，再请求合入。

```bash
python3 -m unittest discover stm32-book/tests -v
python3 stm32-book/build_html.py --check
python3 stm32-book/build_html.py --lang en --check
```

7. **合入。** `book` 与 `book-en` 都变绿之后，由人决定是否 squash 合入 `main`。合入后在 `D:\Users\STM32` 拉取这次 `main`。不打 tag，不创建 Release。

实施 PR 的 diff 可以碰：`stm32-book/styles/tokens.json`、`stm32-book/styles/book.css`、`stm32-book/tests/test_build.py`、`stm32-book/tests/test_sample_svg_c.py`、`stm32-book/revisions.json`、`stm32-book/manifest.json`、`stm32-book/manifest-en.json`、`stm32-book/README.md`。不碰 `build_html.py`、`cover.svg`、章节正文、`assets/`、`tools/`、`.github/workflows/book.yml`。

## 风险

- **若 `.cover-panel` 继续写 `var(--inset)`，标题板左右会从 6% 收到 4.5%。** 这一处必须改成字面量 `6%`。
- **若把 `--space-bar` 收到 `0.5rem`，3px 强调条会贴住 `h2`。** 停在 `0.625rem`。
- **若把 `--leading-body` 收到 `1.6` 或更低，17px 中文的行框会开始挤。** 停在 `1.65`。印刷正文的 `1.55` 已经更紧，那是印刷规则，不要再改。
- **若把 `--measure` 收到 `38rem`，宽屏右侧空白会变多。** 若放到 `44rem`，全角会超过 40 字。停在 `42rem`。
- **若顺手把 `.part-divider` 的 `52vh` 或 `.cover` 的 `92vh` 改矮，就做成了海报刀。** 这两处保持。
- **若把暗色或印刷的 15 个颜色一起改，就离开了密度。** `dark` 和 `print` 的对象保持字节。
- **若重排 JSON 或把样式表里的 `.625rem` 写成 `0.625rem`，哈希会离开「哈希」一节，即使看起来同值。** 按替换表的字符串做。
- **若哈希对不上仍去改测试期望，错误的样式会被锁住。** 先对照替换表。
- **窄于 720px 时，章块左右已是 `1rem`，inset 的变化在手机上看不见。** 垂直间距仍会收。视觉验收用宽于 960px 的窗口。

## 验收

### 本设计 PR

- 新增文件只有 `docs/superpowers/specs/2026-10-25-book-density-F-design.md`。
- `stm32-book/`、`docs/` 章节、`docs/en/` 章节、资产、工具、workflow 和基线 `a481335` 相同。
- 版本号仍是 1.2.7。没有 tag，没有 Release。没有实施计划。

### 实施 PR

- 中文与英文 `python3 stm32-book/build_html.py --check` 通过。`python3 -m unittest discover stm32-book/tests -v` 通过。`book` 与 `book-en` 都绿。
- `builder.CSS` 的 SHA-256 是 `aacd30dcb0efbff80d004295338c9be99b35e19cb744d6f4b1e662a0b8f31baf`。`tokens.json` 与 `book.css` 的哈希是「哈希」一节的两串。`cover.svg` 的哈希仍是 `37dbedd70d2be8e94f4cdf05b60541f69d0107af6374902f8062c8e0bf74dedd`。
- `light` 仍是 40 个键，`schema` 仍是 `1`，`coverLock` 仍是原来的六个名字。七个新值与令牌表一致，其余颜色值与 1.2.7 一致。
- `docs/` 与 `docs/en/` 的正文 diff 为空。`assets/` 与 `cover.svg` 的 diff 为空。
- 出版书签条数仍是 44。没有 tag，没有 Release。
- 宽于 960px 打开构建出的中文 HTML：第 00 章的段距、图距、罗盘下边距比 1.2.7 明显少一档；相邻两行的字不贴在一起；一行中文仍能读完再换行。目录分部之间更近，两列仍分开。封面标题板的左右留白与 1.2.7 相同，封面图相同。分部页仍大约半屏高。暗色下纸色和墨色与 1.2.7 相同。印刷预览里正文仍是浅底黑字，页边仍是 16mm / 15mm / 18mm。

英文书看同一章即可。样式与中文相同。不要求把 29 章逐页看完。

## 未决问题

没有会挡住密度实施的未决项。下面几项按此处的默认执行。复审规格时可以改口。改「还要不要动封面」或「还要不要收 `52vh`」要在实施开始前定，并先改本文件。实施 PR 按本文件的字符串做，不得自行改数再改测试期望。若复审时某个长度改了，三串哈希作废，要在实施开始前重算并写回「哈希」一节；实施开始后哈希对不上就停。

1. **七个令牌按表收一档，不在实施时再调。** `--space-bar` 停在 `0.625rem`。`--leading-body` 停在 `1.65`。`--measure` 停在 `42rem`。`--inset` 停在 `4.5%`。
2. **封面标题板左右冻结为字面量 `6%`。** 上下 `1.8rem` / `2.6rem` 保持。封面 SVG 不改。
3. **`figure img` 的 `.55rem` 收到 `.4rem`。** 这是图间空白，不是刀 E 的字号。
4. **分部页 `52vh` 和封面 `92vh` 保持。** 海报不在这一刀。
5. **暗色和印刷只继承间距，不改色。** 印刷正文行高保持 `1.55`。
6. **哈希按「哈希」一节的三串。** 对不上就停。
7. **版本。** 实施开始时若 `manifest.json` 仍是 `1.2.7`，实施 PR 写成 **1.2.8 · 2026-10-25**。本设计 PR 不升。两份 PR 都等人审，squash 由人决定。不打 tag，不创建 Release。

## 英文提要

Density only, on v1.2.7 (`a481335`, PR #47). Tighten the reading surface one step: `--space-chapter` 3.5rem to 2.75rem, `--space-figure` 1.5rem to 1.25rem, `--space-paragraph` 1.25rem to 1rem, `--space-bar` 0.75rem to 0.625rem, `--inset` 6% to 4.5%, `--leading-body` 1.75 to 1.65, `--measure` 40rem to 42rem. Also tighten the hardcoded gaps on `.chapter > header`, `.chapter-compass`, `.companion`, `.quick-check`, `blockquote.callout`, `figure`, `figure img` (`.55rem` to `.4rem`), `.table-scroll`, the contents rules, `.back-to-toc`, and `footer.book-footer`. Point `.revision-history > p, .index-lead` at `var(--measure)`. Freeze `.cover-panel` side padding at the literal `6%` so the title plate does not follow the new inset. Leave colors, `coverLock`, cover SVG, sample SVGs, GIFs, type tokens, the 52vh part page, the 92vh cover, print colors, and `load_css()` alone. The assembled CSS hash changes from `a4ccd1403ab742e82f67c39053c2609da1c9a8afa126d4f6b988a5b9559a5ac4` to `aacd30dcb0efbff80d004295338c9be99b35e19cb744d6f4b1e662a0b8f31baf`. `tokens.json` becomes `9d07dad497b824c9e2038ddf1e28cb77974451acb6c3b9773863df7c8c90d0bd`. `book.css` becomes `cc2656e9c7e0ea311fc79d36c920c20d82012d8907b000ec940a93095845e480`. The cover SVG hash stays `37dbedd70d2be8e94f4cdf05b60541f69d0107af6374902f8062c8e0bf74dedd`. The provisional implementation version is 1.2.8 dated 2026-10-25. This design PR does not bump the version. Review before merge. A person decides whether to squash. Do not tag and do not create a Release. This design PR only adds this file.

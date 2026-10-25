# 整书观感抛光 1.2.0 设计

日期：2026-10-25  
状态：已批准，待观感实施  
基线：`main` 上的整书 **v1.1.1**（`ed9be9048216b3bf3d3fd919a072e2eabf67c081`，PR #24，2026-10-25）  
上一份设计：[2026-10-25-classic-encyclopedia-batch2-04-06-design.md](2026-10-25-classic-encyclopedia-batch2-04-06-design.md)（PR #22）。四块模板来自 [2026-10-25-classic-encyclopedia-thicken-design.md](2026-10-25-classic-encyclopedia-thicken-design.md)（PR #18）。  
本文件只记录设计。它不改 `build_html.py`，不改 `cover.svg`，不改正文，不升版本号，不打 tag，不发布 Release。

## 背景

用户要整书成体系、好看，并且各方面都到位。本轮按这个顺序排三刀：**观感 → CONTENT_GUIDE 规范对齐 → Batch3 加厚**。本文件只覆盖第一刀观感。后两刀在文末点名，不在这里实施。

方案是 **方案 A · Token 驱动整书抛光**：样式仍写在 `stm32-book/build_html.py` 的内联 `CSS` 字符串里，用 `:root` 上的自定义属性收间距、字号节奏和组件，再让组件类、暗色和 `@media print` 引用这些属性。

对照 v1.1.1 核对过的事实：

1. **样式全在 `CSS` 这一段字符串里。** 从 `:root` 到 `@media print`，没有独立 `.css`，也没有 design-token JSON。亮色 token 是 `--paper: #fbfaf7`、`--ink: #17202a`、`--accent: #075e84`、`--muted: #5e6872`、`--spine: #c4552a`。暗色是 `@media (prefers-color-scheme: dark)` 里重写的同一组变量。印刷在 `@media print` 里把 `color-scheme` 固定为 light，并另写一套浅色值。
2. **正文用色的对比已经过可读门槛。** 按 WCAG 的 sRGB 相对亮度，(较亮 + 0.05) / (较暗 + 0.05)：亮色墨色对纸色约 15.8，强调色对纸色约 6.8，次要色对纸色约 5.4；暗色墨色对纸色约 15.5，强调色对纸色约 9.7，次要色对纸色约 8.9；印刷 `#111` 对 `#fff` 约 18.9，印刷强调色 `#075e84` 对 `#fff` 约 7.1。阈值取 4.5。这三组都高于阈值。`test_narrow_desktop_stacks_compass_without_part_number_collision` 把列表标记的计算色锁成 `rgb(7, 94, 132)`，也就是亮色 `--accent`。屏幕和印刷的 CSS 断言把 `--spine: #c4552a` 写成字面量，`cover.svg` 也含 `#c4552a`。
3. **低于 4.5 的是拿 spine 当字色的两处小字。** `--spine: #c4552a` 对 `--paper` 约 4.3，对 `--spine-soft: #f8efe8` 约 4.0。用到字色的是 `.closing-banner`（`.78rem`）和 `.compass-boundary .compass-role`（`.72rem`）。spine 作色条（封面左条、边界卡顶条、分部页顶边）不必按正文门槛计。`--warn: #9a3d1c` 对纸色约 6.6。暗色里 `--spine` 与 `--warn` 都是 `#f0b090`，对暗色纸约 9.7。
4. **封面标题板另有一套近色，暗色查询改不到它。** `.cover-panel` 写死 `#f7f4ee`、`#17202a`、`#5c6570`、`#d7d0c4`、`#9a3d1c`、`#10242e`。纸色 token 是 `#fbfaf7`，次要色是 `#5e6872`，分割线是 `#d7dce1`。`.cover` 与 `.cover-art` 的深底板是 `#10242e` 和 `#0c1c24`，与 `cover.svg` 的底 `#0c1c24` 同支。标题板在暗色下仍是浅底，因为这些颜色不走变量。
5. **间距、圆角、字距没有阶梯。** 章块上下 padding 是 `3.4rem` 和 `3.6rem`，左右 `6%`；`.part-divider` 左右是 `8%`。正文 `line-height: 1.72`，段落没有自己的 margin。`h2` 是 `margin: 2.35rem 0 .6rem`，左边条是 `padding-left: .7rem` 加 `border-left: 3px solid var(--accent)`，选择器是 `.chapter > h2, .appendix > h2, .part-closing > h2`。`figure` 上下是 `1.5rem` 和 `1.7rem`。圆角同时有 `.5rem`、`.55rem`、`.65rem`、`.7rem`、`.75rem`、`.8rem`。投影只有目录粘性标题的 `1px` 线和 `.toc-jump` 的阴影。眉题字距有 `.18em`、`.16em`、`.14em`、`.12em`。正文没有字距。
6. **印刷规则已经在，而且有测试。** `@media print` 里 `orphans: 3`、`widows: 3`；`figcaption` 同时写了 `break-before: avoid-page` 和 `break-inside: avoid-page`（并带 `page-break-*`）；`figure`、`.chapter-compass`、`.source-card`、`img` 不在页内断开；`figure { background: transparent; }`。`test_print_layout_keeps_reading_units_together` 在第 27 章用印刷介质核对孤行、寡行、标题、图和图注。`test_code_glossary_and_print_css_keep_reading_units_movable` 核对印刷 CSS 片段，其中包括 `figure { background: transparent; }` 和页眉 `page-break-after: avoid`。窄屏测试还要求屏幕上 `figure` 的上边框是 `1px`、填充不是透明，印刷时填充是透明；`h2` 左边框宽度是 `3px`。
7. **`cover.svg` 没有 `<style>`。** 几何和填色写在属性上。自包含测试锁 `aria-label="STM32 board"`、`#c4552a`、`#8ecae6`，并禁止 `@font-face`、外链和非 `www.w3.org` 的 URL。构图是深色底板、一块板、引脚、LED 和一条迹线。
8. **四块只存在于部分章。** 第 00、03、04、06 章已有「原理与边界 / 关键插图 / 时序或状态 / 坑与出处卡」。`docs/CONTENT_GUIDE.md` 与 `docs/en/CONTENT_GUIDE.md` 仍是学习目标、核心原理、常见坑那套骨架，没有把四块写成必选。本刀不改这两份指南，也不加厚下一章。
9. **版本字面量在五处。** `revisions.json` 第一条是 `1.1.1`（2026-10-25）。`manifest.json` 与 `manifest-en.json` 的 `version` 是 `1.1.1`，`date` 是 `2026-10-25`。`stm32-book/README.md` 当前版本句是 **v1.1.1 · 2026-10-25**。发布节的 tag 名是 `v1.1.1`，并写明不要把 1.1.0 的产物标成 1.1.1。`test_build.py` 把当前版本断言为 `1.1.1`，历史列表从 `1.1.1` 排到 `1.0.0`。

## 目标与非目标

### 目标

- 只改内联 CSS、封面留白，以及把关键选择器和版本锁进测试。整书版本在实施合入时升到 **1.2.0 · 2026-10-25**。中英文共用这个版本号。
- 纸色、墨色、强调色继续用现在的十六进制。封面标题板和扉页改用同一组 token。低于 4.5 的 spine 字色改到已经达标的 `--warn`。色条上的 spine 保持 `#c4552a`。
- 章距、段距、图距和 h2 左边条间距使用下面写死的四档。罗盘、提示框、出处卡、插图共用一档圆角和一条轻阴影。
- 暗色对比保持达标，并用测试锁住。印刷的孤行、寡行和图注不断页规则保留，并在现有测试里继续通过。
- `cover.svg` 只调留白和对齐。
- 实施 PR 在 Book CI 变绿之后 squash 合入 `main`。合入后在本机 `D:\Users\STM32` 拉取这次 `main`。拉取不产生仓库 diff。

### 非目标

- 不改 `docs/00`–`28`、`docs/en/`、附录 Markdown、`CONTENT_GUIDE.md` 中英、罗盘文案、manifest 里除 `version` 和 `date` 以外的字段。
- 不把 CSS 拆成独立 `.css`，不新增 design-token JSON，不把 token 挪出 `CSS` 字符串。
- 不重绘 `assets/` 里的样本 SVG、动画 SVG 或 GIF，不改 `tools/gen_sample_figures.py`、`tools/gen_gifs.py`、`tools/svgkit.py`。
- 不碰海报，不改 `tools/check_assets.py`，实施时不把 `check_assets.py` 列进必跑命令。
- 不加图目录或表目录。出版书签仍是 44 条。章号显示仍是文件名前缀加 1。
- 不打 tag，不创建 GitHub Release。README 的发布节只改版本句和「不要把上一版产物标成这一版」，不在实施 PR 里执行发布步骤。
- 不改 callout 的分类逻辑、罗盘的 HTML 结构、出处卡的字段。`.chapter-compass` 和 `.quick-check` 里继续没有 `h2`。
- 不改 `.toc-jump` 的定位、胶囊形和现有投影。
- 不实现文末点名的 CONTENT_GUIDE 刀和 Batch3 刀。

## 方案 A · Token 驱动整书抛光

视觉改动落在 `CSS` 字符串和 `cover.svg` 的几何上。版本、README 和测试在后面两节另列，不混进样式规则。选择器的子组合保持原样：`.source-card h2` 不套用章内 `h2` 的左边条。

### Token

亮色 `:root` 保持这些字面量，测试继续能搜到它们：

- `--paper: #fbfaf7`
- `--ink: #17202a`
- `--accent: #075e84`
- `--muted: #5e6872`
- `--warn: #9a3d1c`
- `--tip: #1b5c45`
- `--spine: #c4552a`

暗色那一行保持现在的十六进制，包括 `--paper: #11171b`、`--ink: #e9eef1`、`--accent: #78c8e8`、`--muted: #acb7bf`、`--warn: #f0b090`、`--spine: #f0b090`。印刷色保持现在的 `--paper: #fff`、`--ink: #111`、`--muted: #444`、`--accent: #075e84`、`--spine: #c4552a`。

在亮色 `:root` 增加且只增加下面这些自定义属性。组件改去引用它们，不再为同一角色另写一档长度：

| 属性 | 值 | 用在 |
| --- | --- | --- |
| `--space-bar` | `0.75rem` | 章、附录、分部收束页里 `h2` 的 `padding-left`，以及这些 `h2` 的 `margin-bottom` |
| `--space-paragraph` | `1.25rem` | 章、附录、分部收束页里直接子级 `p` 的上下 margin |
| `--space-figure` | `1.5rem` | `figure` 的上下 margin |
| `--space-chapter` | `3.5rem` | 章、附录、分部收束、书末、文前、目录、扉页的上下 padding；`.part-divider` 的 `margin-top` |
| `--inset` | `6%` | 上述块和 `.part-divider`、`.cover-panel` 的左右 padding |
| `--leading-body` | `1.75` | `body` 的 `line-height`。现在是字面量 `1.72` |
| `--tracking-body` | `0.01em` | 章、附录、分部收束页里直接子级 `p` 的 `letter-spacing`。代码、表格、标题不加 |
| `--tracking-kicker` | `0.14em` | 眉题、章号、罗盘标题、`.compass-role`、callout 标签、分部标签。取代 `.18em`、`.16em`、`.14em`、`.12em`。`.source-id` 的 `.04em` 保持 |
| `--radius` | `0.7rem` | 下节列出的卡片 |
| `--elev` | `0 1px 2px color-mix(in srgb, var(--ink) 8%, transparent)` | 下节列出的卡片。印刷里关掉 |

`h2` 的 `margin-top` 写成 `calc(var(--space-figure) + var(--space-paragraph))`，也就是 `2.75rem`。不另加第五个间距变量。

`.cover` 上重设亮色的 `--paper`、`--ink`、`--muted`、`--warn`、`--line`、`--spine`，数值与亮色 `:root` 相同。暗色查询改的是根上的变量，盖不到这层重设，标题板因此保持浅底。画板背景 `#10242e` 和 `.cover-art` 的 `#0c1c24` 继续写死，不改成 `--paper`。

窄于 720px 时，这些块的左右 padding 仍是 `1rem`。`--inset` 不参与这一档。

### 排版

- `body` 使用 `--leading-body`。`--tracking-body` 只加在章、附录、分部收束页的直接子级 `p` 上。代码、表格、标题、罗盘卡片内部和 callout 内部不加这段字距。
- 章、附录、分部收束、书末、文前、目录、扉页的上下 padding 同为 `--space-chapter`，左右同为 `--inset`。现在扉页是 `4.5rem` / `5rem`，章块是 `3.4rem` / `3.6rem`，实施时收成这一档。
- `.part-divider` 的左右 padding 从 `8%` 改为 `--inset`。上下 padding 保持 `4.5rem`（现在下边是 `4.2rem`，收成与上边相同）。它有 `min-height: 52vh`，不用 `--space-chapter` 当内部 padding。`margin-top` 用 `--space-chapter`。`h1` 与 `.part-goal` 避开 `.part-index` 的现有 `max-width` 保留。1200、840、390 三档上标题和目标都不得压住分部序号，现有断言保持 `titleHitsIndex` 与 `goalHitsIndex` 为假。
- `.chapter > h2, .appendix > h2, .part-closing > h2` 继续是一条规则：`border-left: 3px solid var(--accent)`，`padding-left: var(--space-bar)`。子组合 `>` 保留，出处卡标题不长出左边条。窄屏测试里的 `sectionRule == 3px` 不放宽。
- `blockquote.callout` 的左边条保持 `4px`。不把它改成 `3px`，也不把 `h2` 改成 `4px`。
- `.closing-banner` 和 `.compass-boundary .compass-role` 的字色改为 `var(--warn)`。边界卡的 `border-top` 继续是 `var(--spine)`。封面左条、封面短横、分部页顶边继续是 spine。`--spine: #c4552a` 在屏幕 CSS、印刷 CSS 和 `cover.svg` 里都保持这个字面量。

### 组件

这些元素使用 `border-radius: var(--radius)` 和 `box-shadow: var(--elev)`，边框继续是 `1px solid var(--line)`，浅底继续用现有的 `--panel` 或 `color-mix` 纸色混合，屏幕上填充不得变成透明：

- `.chapter-compass`
- `blockquote.callout`
- `.source-card`
- `figure`
- `.quick-check`、`.companion`、`.route`

`figure` 的上边框保持 `1px`。浅底可以继续是 `color-mix(in srgb, var(--panel) 70%, var(--paper))`，只要屏幕上不是透明。`figure` 的上下 margin 同为 `--space-figure`。`figure img` 与 `figcaption` 之间现有的 `.55rem` 保留。不在 `figure` 里的 `img` 若仍使用单独的上下 margin，也改用 `--space-figure`。

`.part-divider` 不加圆角，不加 `--elev`。它继续用强调色顶边、分割线底边，以及从 `--accent-soft` 淡出的渐变。

`pre` 的圆角改为 `--radius`，不加 `--elev`。左边 `3px` 强调色条、`tab-size: 4`、滚动提示和 `user-select: text` 保持。术语表误解列的选择器保持，粘性首列只在窄屏出现、印刷时恢复 `position: static`。

`.toc-jump` 的规则保持原句，包括现有的 `box-shadow`。

`@media print` 里，使用 `--elev` 的元素写成 `box-shadow: none`。`figure { background: transparent; }` 保持，印刷填充测试继续看到透明。

### 封面与扉页

`stm32-book/cover.svg`：

- 只改坐标、留白和文字对齐，让板卡和左侧接插件不要贴边，眉题和板卡的左右留白成对。
- 不增删图形，不改板卡、引脚、LED、迹线这套构图，不改填色。
- 保持 `aria-label="STM32 board"`、`#c4552a`、`#8ecae6`，继续不出现 `#9fd7c4`。
- 不新增 `@font-face`，不外链，不加 `<image>` 或带外部 `href` 的 `<use>`。

封面 CSS：

- 上半画板保持深色。下半标题板保持浅色，左条保持 spine。暗色模式不把标题板反相。
- `.cover-panel` 的背景、标题、眉题、副题、版本行、分割线改用 `.cover` 上重设的 token：背景 `--paper`，标题和副题 `--ink`，眉题 `--warn`，版本行 `--muted`，分割线 `--line`，左条和短横 `--spine`。
- `.cover-panel` 的左右 padding 用 `--inset`。`.cover` 自身的 `color: #f4f1ea` 保持；标题板里的字用上一句的 token 覆盖。

扉页（`.imprint`）已经使用 token。这一轮只把间距收到 `--space-chapter` 和 `--inset`。定义列表在宽屏仍至少两列，窄于 960px 仍是一列。文案不改。

### 暗色与印刷

暗色：

- 保持现有 `@media (prefers-color-scheme: dark)` 的那一组十六进制。
- 正文、次要色、强调色、警告色、提示色对暗色纸的对比继续 ≥ 4.5。实施时把配对写成测试。现有数值已经高于门槛；测试失败时只改明度，不改色相，并且不得破坏亮色标记色 `rgb(7, 94, 132)` 和 `--spine: #c4552a`。
- 封面标题板按上一节保持浅底。暗色达标的阅读面是章、罗盘、callout、出处卡和图注。

印刷。下面这些规则保留，并在实施前后都由现有测试核对：

- `body` 上 `orphans: 3` 与 `widows: 3`。
- `h1, h2, h3, h4` 的 `break-after: avoid-page` 与 `page-break-after: avoid`。
- `figcaption` 的 `break-before: avoid-page`、`page-break-before: avoid`、`break-inside: avoid-page`、`page-break-inside: avoid`。
- `figure`、`.chapter-compass`、`.quick-check`、`blockquote`、`.source-card`、`img` 的 `break-inside: avoid-page` 与 `page-break-inside: avoid`。
- `figure { background: transparent; }`。
- `@page { size: A4; margin: 16mm 15mm 18mm; }` 保持这组毫米值。
- 扉页不强制 `page-break-before: always`。代码块印刷仍是 `white-space: pre-wrap` 且允许跨页（`break-inside: auto`，规则里不出现 `avoid`）。

校对指：改完间距和阴影之后，上述片段仍在，`test_print_layout_keeps_reading_units_together` 与 `test_code_glossary_and_print_css_keep_reading_units_movable` 仍通过。不重写这套分页规则。

## 版本与修订文案

实施 PR 把整书标成 **1.2.0**，日期 **2026-10-25**。`validate_revisions` 仍要求修订第一条的版本等于两份 manifest 的 `version`。

`revisions.json` 在条目最前新增：

- `version`: `1.2.0`
- `date`: `2026-10-25`
- `zh`:
  - 整书样式收到同一组纸色、墨色和强调色，章距、段距、图距使用固定阶梯。
  - 章首罗盘、提示框、出处卡和插图共用一档圆角和轻阴影；印刷时的孤行、寡行和图注不断页仍按原规则。
- `en`:
  - The book stylesheet uses one paper, ink, and accent set, with a fixed step for chapter, paragraph, and figure spacing.
  - Chapter compasses, callouts, source cards, and figures share one radius and a light shadow; print orphans, widows, and caption keep-together rules stay as they were.

不在修订说明里写 CONTENT_GUIDE 或 Batch3。保留 1.1.1 及更早条目。

`manifest.json` 与 `manifest-en.json` 的 `version` 改为 `1.2.0`，`date` 改为 `2026-10-25`。其他字段不动。

`stm32-book/README.md`：

- 当前版本句改为 **v1.2.0 · 2026-10-25**。中英文整书仍共用这一版号。Release 仍等提交进入 `main` 且 Book CI 产出四份文件之后，由有权限的人另行处理。
- 发布节的版本句改为已经是 1.2.0。tag 名改为 `v1.2.0`。在现有「不要把 1.1.0 的产物标成 1.1.1」之后加上「不要把 1.1.1 的产物标成 1.2.0」。
- 这一步仍不创建 tag，也不创建 Release。

## 测试

断言写在 `stm32-book/tests/test_build.py`。不新开测试文件。不新开浏览器用例；印刷继续用已有的第 27 章用例。对比用测试内的相对亮度函数，不增加依赖。

新增或收紧的断言：

- 亮色 `CSS` 含 `--paper: #fbfaf7`、`--ink: #17202a`、`--accent: #075e84`、`--spine: #c4552a`，以及 `--space-bar`、`--space-paragraph`、`--space-figure`、`--space-chapter`、`--radius`、`--leading-body`、`--tracking-body`。
- `.chapter > h2` 规则同时含 `border-left: 3px solid var(--accent)` 和 `var(--space-bar)`。
- `.chapter-compass`、`.source-card`、`figure`、`blockquote.callout` 的规则含 `var(--radius)`。
- `.compass-boundary .compass-role` 与 `.closing-banner` 的字色是 `var(--warn)`。`.compass-boundary` 的顶边仍是 `var(--spine)`。
- 暗色媒体查询仍含 `--accent: #78c8e8` 与 `--paper: #11171b`。
- 印刷片段仍含 `orphans: 3`、`widows: 3`、`figcaption` 的 `break-before: avoid-page`、`figure { background: transparent; }`、`--spine: #c4552a`。
- 下列配对的对比 ≥ 4.5：亮色与暗色的墨色、强调色、次要色、警告色、提示色各自对应该模式的纸色；印刷的墨色、强调色、次要色对印刷纸色。spine 对纸色不列入这条文字门槛。

版本断言改为当前版本 `1.2.0`，历史顺序是 `1.2.0` 在 `1.1.1` 之前，`1.1.1` 仍在 `1.1.0` 之前，列表仍含 `1.1.0` 直到 `1.0.0`。HTML 里的 `<strong>v1.2.0</strong>` 替换现在的 `v1.1.1`。不删 `0x271`、`167 ns`、出版书签长度为 44、样本章和 batch2 的断言。

`test_cover_svg_stays_self_contained` 的颜色、`aria-label` 和无外链断言保持。不把整份 SVG 路径数据锁死，留白微调才能通过。

## 工作流与 PR 节奏

### 本 PR（设计）

只新增本文件。不改 `docs/` 章节、`docs/en/`、`stm32-book/`、`assets/`、`tools/`、`CREDITS.md`。不升版本，不打 tag，不发 Release。本 PR 等人审阅规格后再合入，不在 CI 变绿后自动合。

### 实施 PR（下一轮，不在本 PR）

顺序固定：

1. **样式。** 按上一节改 `CSS` 字符串。分类函数、罗盘 HTML、书签、章号、`sources` 渲染不动。
2. **封面。** 按留白和对齐改 `cover.svg`。填色和构图不动。
3. **测试。** 加上一节的断言，并把当前版本从 `1.1.1` 改到 `1.2.0`。
4. **版本。** 同一提交内改 `revisions.json`、两份 manifest、`stm32-book/README.md`。修订说明只用上一节的四句。
5. **验证。** 下面三条通过之后再请求合入：

```bash
python3 -m unittest discover stm32-book/tests -v
python3 stm32-book/build_html.py --check
python3 stm32-book/build_html.py --lang en --check
```

6. **合入。** Book CI 变绿之后，把实施 PR squash 合入 `main`。不再为观感做第二次正文复审。合入后在 `D:\Users\STM32` 拉取这次 `main`。不打 `v1.2.0` tag，不创建 Release。

实施 PR 的 diff 可以碰：`stm32-book/build_html.py` 的 `CSS` 字符串、`stm32-book/cover.svg`、`stm32-book/tests/test_build.py`、`stm32-book/revisions.json`、`stm32-book/manifest.json`、`stm32-book/manifest-en.json`、`stm32-book/README.md`。不碰章节正文，不碰 `assets/`，不碰 `tools/check_assets.py`。

## 验收

### 本设计 PR

- 新增文件只有 `docs/superpowers/specs/2026-10-25-book-visual-polish-1.2.0-design.md`。
- `stm32-book/`、`docs/` 章节、`docs/en/` 章节、资产与工具和基线 `ed9be90` 相同。
- 版本号仍是 1.1.1。没有 tag，没有 Release。

### 实施 PR

- 中文与英文 `python3 stm32-book/build_html.py --check` 以及 `--lang en` 通过。`python3 -m unittest discover stm32-book/tests -v` 通过。
- 上一节列出的 CSS 片段和选择器仍在，对比断言 ≥ 4.5。
- 亮色 `--accent` 仍是 `#075e84`，列表标记计算色仍是 `rgb(7, 94, 132)`。`--spine` 仍是 `#c4552a`。`h2` 左边框仍是 `3px`。屏幕上 `figure` 上边框仍是 `1px` 且填充非透明；印刷时 `figure` 填充透明。
- 人工打开构建出的中文 HTML，看三处：封面（构图还在，标题板浅底、左条仍是 spine）；从第 00、03、04、06 章里任选一章，看罗盘、四块标题的左边条、一条 callout、一张 `figure`；附录 E 的 `.source-card`（圆角、顶条、浅底，链接仍是 `<a href>`）。英文书用同一次构建抽一处封面或一章即可，不要求把 29 章逐页看完。
- `docs/` 与 `docs/en/` 的正文 diff 为空。`CONTENT_GUIDE` 中英 diff 为空。`assets/` diff 为空。
- 出版书签条数仍是 44。没有 tag，没有 Release。

## 后续刀

只点名，不在本文件里设计细节，也不进入观感实施的 diff。

1. **CONTENT_GUIDE 规范对齐。** 在 `docs/CONTENT_GUIDE.md` 与 `docs/en/CONTENT_GUIDE.md` 把大典四块写成必选：`## 原理与边界` / `## Principle and boundary`，`## 关键插图` / `## Key figures`，`## 时序或状态` / `## Timing or state`，`## 坑与出处卡` / `## Pitfalls and source cards`。
2. **Batch3 加厚。** 在四块模板上再加厚两章外设。章号到那时的设计里再锁，不在这里预选。

顺序是观感合入之后再写 CONTENT_GUIDE，然后才是 Batch3。两刀各自另开设计。

## 未决问题

没有会挡住观感实施的未决项。下面几项按此处的默认执行，复审规格时可以改口，不需要再写一版设计才改 CSS：

1. **纸色、墨色、强调色的十六进制。** 保持 v1.1.1 的亮色、暗色和印刷值。对比已经高于 4.5 的配对不换色。
2. **封面标题板。** 暗色下保持浅底。深色画板的 `#10242e` 与 `#0c1c24` 不改。
3. **spine。** 字面量保持 `#c4552a`。只有把它当成小字字色的两处改用 `--warn`。
4. **图目录与表目录。** 这一刀不加。
5. **Release。** 实施合入不打 tag，不创建 Release。

## 英文提要

Polish only the inlined stylesheet in `stm32-book/build_html.py` and the whitespace of `stm32-book/cover.svg`, on v1.1.1 (`ed9be90`, PR #24). Keep the current paper, ink, and accent hexes; they already clear a 4.5 contrast ratio, and the list marker test locks accent at `rgb(7, 94, 132)`. Keep `--spine: #c4552a`. Move the two small spine-colored texts (`.closing-banner` and `.compass-boundary .compass-role`) to `--warn`. Add one spacing ladder (`--space-bar` 0.75rem, `--space-paragraph` 1.25rem, `--space-figure` 1.5rem, `--space-chapter` 3.5rem), one radius (`0.7rem`), and one light shadow for the compass, callouts, source cards, and figures. Leave the cover title plate light in dark mode. Keep print orphans, widows, and caption keep-together rules. Do not edit chapter Markdown, do not split out a CSS file or token JSON, do not redraw sample figures, do not add lists of figures or tables, and do not tag or release. The implementation PR bumps the book to 1.2.0 dated 2026-10-25, then squash-merges after Book CI is green. Later knives, not done here: require the four compendium sections in both CONTENT_GUIDE files, then thicken two more peripheral chapters. This design PR only adds this file.

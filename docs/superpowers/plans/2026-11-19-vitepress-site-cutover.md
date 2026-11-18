# VitePress 站点收尾（关闭 B5 §4.3 偏差）

- 日期：2026-11-19；本地 Git 根 `D:/Users/STM32`。已获授权提交并推送：`0331f9e2`（站点迁移）+ `a8b8bdc5`（EPUB 依赖修复），Pages 已发布。
- 依据：`docs/superpowers/specs/2026-11-12-merged-book-design.md` §4.1/§4.3/§4.4、AC3–AC5；B5 偏差登记见 `2026-11-14-merged-book-b5-site-cutover.md`。
- 结论：站点入口从 `book/build_html.py` 静态站换为 VitePress，base `/STM32/`；`book/build_html.py` 降级为内容渲染契约 + 印刷/EPUB 共享渲染器。

## 做了什么

站点（`docs/.vitepress/`）：`config.mts`（base、`cleanUrls:false`、`srcExclude`、sitemap、canonical/og、local search + 中文分词）、`book.mts`（manifest 驱动的 nav/sidebar/首页、与 `cjk_slugify` 逐字等价的 slugify）、`plugins/book-markdown.mts`（场景标记、单图段落→figure/figcaption、表格滚动容器、SVG/PNG/JPEG 尺寸注入）、`theme/`（StickScene/QuizBank/BookIndex 三组件、书籍样式、打印前展开 details）、`data/scenes.json`（站点与印刷共用场景元数据）。

门禁与 CI：`scripts/check-site-pages.mjs`（dist 页面集合 ↔ manifest 一一对应）、`scripts/check-external-links.mjs`（探活全部外链；允许清单只豁免“实际探到的那一种失败”，404/410 永远失败）、`scripts/tests/*.test.mjs`（5 个文件 21 项）、`site.yml`、`links.yml`、`deploy.yml` 重写、`book.yml` 收敛为书稿门 + HTML/PDF/EPUB 契约。

## 实测证据（本次实际执行）

| 命令 | 结果 |
| --- | --- |
| `npm run docs:build` | 通过，16.73s；55 个 HTML（54 书页 + 404） |
| `npm run site:pages` | `manifest 与 dist 一一对应（54 页）` |
| `npm run site:stubs` | `generated 131 legacy redirect stubs` |
| `npm run site:assemble` | `assembled pages site … stubs=131`；每条存根的 `/STM32/<path>.html` 目标都在产物中存在 |
| `npm run site:smoke` | **10/10**：首页、v1 ch09 深链、旧链 03-gpio→09-gpio、附录 A、ch40、`/anim/queue-passing.svg` 200、quiz 展开、**stick-scene canvas=1**、**中文搜索 hits=16**、同源资源 0 失败 |
| `npm run site:links` | 两轮：`111 checked, 1 allowlisted, 0 failed`；复跑 `111 checked, 0 allowlisted, 0 failed (55 pages)`（nongnu 在本机 DNS 时而可解析）。豁免项只覆盖 `www.nongnu.org/lwip/2_0_x/raw_api.html` 的传输失败，不是 404 |
| `python -m book.build_html --check` | `built 53 pages, 0 planned chapters missing` |
| `python -m unittest discover book/tests` | 102 tests OK |
| `node --test scripts/tests/*.test.mjs` | 23 pass / 0 fail |
| `python tools/slop_lint.py …` / `tools/check_assets.py` | 0 |
| `python -m book.build_print_edition` | 47 章、63 条 outline，703s |
| `python -m book.print_pdf …` | 837 页 |
| `python -m book.build_epub` | spine 64、images 324 |

## 对账与兼容

- 页面集合：54 页（47 章 + 6 附录 + 首页），与 B5 基线 `.temp/site-baseline` 的 54 个 `.html` 一致；`404.html` 显式排除在书页集合外。
- 锚点：Python `render_markdown` 与 VitePress 逐页比对 932 个 `id`，**0 差异**；重复标题按 Python-Markdown 规则得 `机制_1`（`slugifyWithState`），不是 markdown-it 的 `机制-1`。
- 标题里的寄存器字面量（ch04 `pop {r4, pc}`）被 VitePress 捆绑的 `markdown-it-attrs` 当属性吃掉；以 `markdown.attrs.disable: true` 关闭该插件，正文与 id 双渲染器一致，未改正文。
- 旧链：131 存根全部指向 `/STM32/<path>.html`；`cleanUrls:false` 保证 `.html` 深链不变。
- 原始 HTML 图片（附录 C）由 VitePress 的 Vue `transformAssetUrls` 自动补 base；自定义 raw-HTML 前缀规则会双重前缀并导致 Rollup 导入失败，已确认移除。

## 已知边界

- `<details>` 内的 Markdown 列表：VitePress 解析为 `<ol>`，Python-Markdown（无 `md_in_html`）保留字面 `1. …`。印刷/EPUB 维持既有渲染（未改，避免冻结点漂移）；这是站点与印刷既有的差异，不是本轮引入的链接或锚点风险。
- 外链允许清单仅 3 条精确 URL，且必须带理由；`404/410` 在加载期即被拒绝，探活后也只有匹配的 401/403/429 或传输失败可豁免。

## 远程 CI 与发布（2026-11-19）

| 运行 | 结论 |
| --- | --- |
| Merge Check `44357645567`（`0331f9e2`） | success |
| Site CI `44357645413`（`0331f9e2`） | success（构建、页面对账、131 存根、组装、Chromium、10 项冒烟） |
| 部署 `44357645322`（`0331f9e2`） | success，13 步全绿；Pages 已发布 |
| External Links `44357700548`（手动派发） | success |
| Book CI `44357645501`（`0331f9e2`） | **failure**：Build EPUB 缺 `lxml`（`tools/build_epub.py` 导入），已修复 |
| Book CI `44361076775`（`a8b8bdc5`，修复后） | **success**：门禁 + 渲染契约 + 印刷 HTML/PDF/EPUB + 体积断言 + 产物上传 |
| Merge Check `44361076742`（`a8b8bdc5`） | success |
| Site CI `44363672954` / 部署 `44363672893`（`6903417c`，验收记录提交） | success（`docs/**` 命中即重新构建并发布） |
| Book CI `44363672911` / Merge Check `44363672951`（`6903417c`） | success |
| Book CI `44366371871` / Motor Control `44366371717`（`88dc40e5`，v5 升级） | success，两条链路的 `upload-artifact@v5` 都实际执行 |
| Book / Site / 部署 / Merge Check（`df141eed`，`workflow_dispatch` 补跑） | `44372755385` / `44372763574` / `44372770172` / `44372778962` 全部 success |

一次流程失误与修正：`df141eed`（补记本表）的提交消息带了 `[skip ci]`，导致 `docs/**` 触发的四门整体被跳过——`srcExclude` 只影响站点内容，不会豁免工作流触发，这与根 `AGENTS.md` 的「门禁不降级」冲突。该提交已推送，不能 force-push 改写，故对同一 HEAD `df141eed` 显式派发四门补齐覆盖。为避免每写一条验收记录就重建 13 分钟站点，`site.yml`/`deploy.yml` 的路径过滤加入 `!docs/superpowers/**`（VitePress 的 `srcExclude` 本就排除该目录，构建不消费它）；`book.yml` 与 `merge-check.yml` 仍对 `docs/**` 全量生效。

修复：新增 `book/requirements-print.txt`（markdown / lxml / PyMuPDF / Pillow / playwright），`book.yml` 一次安装；删掉重复的 Chromium 步骤。轻量 `merge-check.yml` 仍只装 `book/requirements.txt`。随后把 `actions/upload-artifact` 从 v4 升到 v5（v4 仍指向 Node 20，被强制在 Node 24 上运行并告警）；`book.yml` 与既有的 `motor-control.yml` 各改 1 行。

线上抽查（`https://zhuguang-zfg.github.io/STM32/`）：首页 200 且为 VitePress 产物并带 canonical；`v1-drivers/09-gpio.html` 200（含 quiz/scene）；`mcu/stm32/03-gpio.html` 200（485 字节存根）；`sitemap.xml` 200 且 54 条 `<loc>`。

CI 预置风险（首跑前写下的两条）已被证实必要：Chromium 必须先装（否则印刷集成测试由 skipped 变失败）；Node 固定 `24` 是因为 `site-config.test.mjs` 直接导入 `.mts`。

# 全书版式统一与首批配图补强（1b）

状态：待批准（设计稿，不含实现） · 2026-11-26

范围：为合并书建立一套站点 + 印刷共用的版式/排印基线，并为 5 个目标章节补首批配图；设计遵循野火《STM32 HAL 库开发实战指南》与 *Mastering STM32*（2e）的**讲解顺序 / 版式节奏**，不复制其图稿、寄存器描述或文字。

依据：`docs/CONTENT_GUIDE.md`、`docs/superpowers/specs/2026-11-12-merged-book-design.md`、`docs/superpowers/plans/2026-11-08-book-visual-experience.md`（B46–B52 已执行）、`.claude/skills/handraw-style/SKILL.md`、`tools/audit_book.py`、`tools/audit_pdf_layout.py`、`book/tests/test_print_sections.py`。

## 1. 背景与现状

现状（本地证据，2026-11-26 读库）：

- **活动样式面**只有两处：`docs/.vitepress/theme/style.css`（站点）与 `book/print_css.py`（印刷）。`book/print/book-print.css` 在 `book/print/README.md:3-5` 被明确标注为“未使用的 legacy paged.js 草稿（185×260 mm）”，本设计不改它。
- **印刷注入链**固定：`book/build_print_edition.py:36` `from print_css import build_css`，`:278` `f"<style>{build_css()}</style>\n</head>\n<body>\n"`；`book/build_html.py`、`book/print_pdf.py`、`book/build_epub.py` 不导入 `print_css`。
- **已存在且被测试锁定的印刷规则**：`figure img, figure svg { max-height: 150mm; max-width: 100%; width: auto }`、`figure.landscape` + `@page plate-landscape`、`figcaption { max-width: 150mm }`、`h1,h2,h3 { break-after: avoid }`、`thead { display: table-header-group }`、`tr { break-inside: avoid }`、`.quiz` 可跨页但 `.quiz-answer { break-inside: avoid }`。这些是基线，不重复发明。
- **三条不可破的视口契约**（`book/tests/test_print_sections.py::PrintCssTests` 原样断言）：`table-layout: fixed`、`p:has(img) { text-indent: 0; }`、`code, a { overflow-wrap: anywhere; }`、`width: 176mm`。破坏任一条会把 176mm 版心撑宽，Chromium 整本缩字。
- **封面文案契约**（`CoverCopyTests`）：`<p class="book-sub">原理讲解 · 工程示例 · 实验指南</p>`，不得声称“全程实物实验/全程实测”。封面 kicker 为 `STM32 · ESP32-S3 · GD32 · FreeRTOS · RT-Thread`。
- **图源契约**：`book/tests/test_figure_sources.py` 要求每个被引用的 `/images|arch|figures|anim/*` 资产都有可追踪 SVG 源；`tools/handraw_track/publish_staged.py --check` 字节比对 `assets/illustrations/staged/` → `docs/public/images/`；`book/tests/test_figure_mirrors.py` 管镜像漂移；`test_handraw_layout.py`/`test_handraw_chrome.py` 管 Handraw 最小字级/重叠/纸纹。
- **审计口径**（`tools/audit_book.py`）：`extract_visual_anchors` 只计 `<figure>`、`<p align=center>`、`<img src>`、`![](...)`；`max_visual_gap_chars` 为相邻 PDF 锚点之间的正文阅读字符，围栏代码剔除；`_target_visuals` 按字数给 4/6/9；`_overlay_gap_budget_chars` 给 960/1020/1080（ch18/23/28 carve-out 3500）。`<!-- stick-scene: id -->` **不计入**锚点（站点运行时组件，print/EPUB 走 noscript/fallback）。
- **当前审计**（`python tools/audit_book.py --format json --write .temp/audit_book.current.json`）：53 章、345 个 PDF 锚点、21 章低于目标、photos=0。全书最长 gap 前列含 apD/ch06/ch11/ch26/ch46 目标章。

## 2. 目标与非目标

### 目标

1. **版式系统（1b-layout）**：在 `book/print_css.py` 与 `docs/.vitepress/theme/style.css` 上建立一致的排印节奏（图尺寸分档、图注/图块原子性、标题不断尾、长表表头重复、CJK token、章/卷开篇节奏），且不破坏任何既有测试契约。
2. **首批配图（1b-figures）**：为 5 个目标章补 Handraw 原理示意，填补当前最大无图区间，把每章向目标锚点推进；图只解释机制/结构/流程，不编造实物/测量/示波器证据。
3. **可验证**：新增/变更均可被现有窄门或本设计明确的新门验证；不削弱任何现有测试。

### 非目标

- 不重做 B46–B52 已完成项（B46 PDF 布局审计器、B47 三档图尺寸/figcaption 避拆/表头重复/CJK token/章首页统一、B48–B49 既有配图批次、B50 真证、B52 收口）。本设计只**扩展**缺口。
- 不改 `book/print/book-print.css`（死文件）。不改 `book/tests/test_print_sections.py` 已锁的 4 条视口契约字面值。
- 不改 `docs/en/`（目录不存在，`NO_EN`）；本书当前为中文单语，不引入 zh/en parity 义务。
- 不引入 AI 伪造实拍；不把自绘图标为实拍；不复制参考书图版。
- 不在本设计中把 `book.md_links` 接线进 Makefile/CI（那是已在 PR body 提案、受 #179/#180/#183 合并顺序约束的独立变更）。
- 不改 `test_figure_mirrors.py` / `test_figure_sources.py` / `test_handraw_layout.py` / `test_handraw_chrome.py` 的既有预期语义。

## 3. 现状证据（首批 5 章）

| 审计 id | 文件 | 字符 | 锚点/目标 | 缺口 | 最大 gap | gap from → to | 现有资产 |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| `ch06` | `docs/v0-foundations/06-linker-startup-map.md` | 14295 | 6/9 | 3 | 5826 | `size 三列：Flash 与 RAM 各吃哪份` → `章末` | linker-map.png, data-vma-lma.svg, boot-sequence.png, ch06-boot-five-stations.png, v0-06-vma-lma.png, ch06-size-two-budgets.png |
| `ch11` | `docs/v1-drivers/11-systick-timebase-rtc.md` | 14430 | 4/9 | 5 | 4829 | `SysTick 与 RTC 的分工` → `章末` | systick-tick.svg, ch11-load-plus-one.png, stm32-05-tick-wrap.svg, ch11-three-timebases.png |
| `ch26` | `docs/v3-rtos/26-device-framework-shell.md` | 15604 | 6/9 | 3 | 5313 | `两条命令的分工` → `章末` | rtt-device-chain.svg, device-ops.png, ch26-ops-two-forms.png, ch28-rtthread-lifecycle.png, rtt-finsh-dispatch.svg, menuconfig-flow.svg |
| `ch46` | `docs/v7-delivery/46-resources-roadmap-open-source.md` | 14997 | 5/9 | 4 | 8846 | `1. 三阶段路线与过关判据` → `机制` | ch46-roadmap-gates.png, ch46-l0-l5-ladder.png, ch00-three-api-lanes.png, stlink-v2-swd-connector.jpg, ch46-oss-four-lanes.png |
| `apD` | `docs/appendix/D-glossary.md` | 16433 | 4/9 | 5 | 5954 | `UART、I2C、SPI、CAN 与 USB` → `工程习惯` | app-d-lookup.png, app-d-clusters.png, app-d-not-rm.png, app-d-pin-table.png |

注：`chars` 为 `audit_book.py` 的正文阅读字符（围栏代码剔除），小于文件字节数；表中 gap 端点来自 `max_visual_gap_from/to`。

## 4. 设计

### 4.1 版式系统（layout）

#### 4.1.1 活动面与禁区

| 面 | 文件 | 角色 | 本设计动作 |
| --- | --- | --- | --- |
| 印刷样式 | `book/print_css.py` | `build_print_edition.py` 注入的唯一样式源 | 扩展 |
| 站点样式 | `docs/.vitepress/theme/style.css` | VitePress 主题 | 扩展 |
| 印刷组装 | `book/build_print_edition.py` | 封面/卷首/章节 HTML 组装 | 仅在需要 opener parity 时做最小结构变更，并同步更新 pin 测试（见 4.1.4） |
| 死草稿 | `book/print/book-print.css` | 未使用 | **不动** |
| 视口契约 | `book/tests/test_print_sections.py` | 防全书缩字 | 保持断言字面值不变 |

#### 4.1.2 图尺寸分档（扩展现状，不回退）

现状：print 有 `figure img, figure svg { max-height: 150mm }` + `figure.landscape`；site 有 `max-width: 100%` 无档位。B47 曾计划三档，但活动 CSS 中**没有** `size-s/m/l` 选择器；本设计把“分档”落为真实契约。

契约：

- **S（小原理/对照）**：`max-height: 72mm` print / `max-width: 28rem` site。用于单概念对照、小流程。
- **M（默认机制图）**：保持现状 `max-height: 150mm` print / `max-width: min(100%, 42rem)` site。未标注类名的 `figure.book-figure` 走 M。
- **L（宽表/时间线/总览）**：`max-height: 190mm` print landscape 或受 `@page plate-landscape` 约束；site `max-width: 100%`。仅用于信息密度确实需要宽幅的图。
- 实现方式：在 Markdown/HTML 图块上加 `class="book-figure fig-s|fig-m|fig-l"`（或等价 data attr），由 `book-markdown.mts` 的 figure 包装/样式与 `print_css.py`/`style.css` 共同识别。**默认不加类 = M**，因此现有图片行为不变。
 - **S（小原理/对照）**：`max-height: 72mm` print / `max-width: 28rem` site。用于单概念对照、小流程。
 - **M（默认机制图）**：保持现状 `figure img, figure svg { max-height: 150mm }` print / `max-width: min(100%, 42rem)` site。未标注类名的 `figure.book-figure` 走 M。
 - **L（宽图/时间线/总览，仅 landscape）**：复用现有 `@page plate-landscape { size: A4 landscape; margin: 21mm 17mm 19mm }`。页面可用高 = 210mm − 21mm − 19mm = **170mm**；这是**整个 figure 块**（图 + figcaption + figure 上下 margin）的上限，不是图片单独上限。实现时图片 `max-height` 必须为 170mm 减去 figcaption 实际占用（按现有 figcaption 字号/行高/`margin-top: 1.2rem` 预算，默认按 2 行图注预留 ≥12mm）后的余量，并保留 figure padding/margin 安全边距；因此 L 档图片 `max-height` **不得超过 150mm**（与现有 `figure.landscape` + 全局 150mm 上限一致），除非同时收紧图注预算并通过实际 PDF 渲染验证。禁止写入 `max-height: 190mm` 或任何超过 170mm 块高的值。
 - 实现方式：在 Markdown/HTML 图块上加 `class="book-figure fig-s|fig-m|fig-l"`（或等价 data attr），由 `book-markdown.mts` 的 figure 包装/样式与 `print_css.py`/`style.css` 共同识别。**默认不加类 = M**，因此现有图片行为不变。
 - 守卫：不得改动 `figure.landscape` 既有语义；不得让任何档位突破 `width: 176mm` 版心；L 档必须过实际 PDF 渲染与 `tools/audit_pdf_layout.py`，CSS 字符串断言不足以发现分页溢出。
- Site 已有 `.vp-doc figure.book-figure figcaption`。保持。
- 新增约束：长图注（>2 行）不得与图分离；若实现需要，把 `figcaption` 保持在 `figure` 内并禁止 figure 内分页——print 侧已满足，site 侧为自然流。
- Handraw 图注四要素沿用 B48 纪律：看哪里、证明什么、不能证明什么、出处（RM0008/数据手册/HAL 版本）。图注尾部保留 `原理示意/非实拍`。

#### 4.1.4 章/卷开篇节奏（site ↔ print parity）

参考野火“章首目标/硬件/步骤”与 Mastering STM32 “概念先行再寄存器/代码”的节奏，但只借节奏，不借文案。

- **现状**：print 有 `.chapter-opener`/罗盘卡 2×2（已在 `print_css.py`）、`build_print_edition.py` 生成 `.part-page`（含 `.part-kicker`、`h1`、`.part-goal`）、封面 `.book-sub` 被 `CoverCopyTests` pin。site 有 `h1` balance、`p.book-subtitle`/`p.book-version` muted、chapter pager，无 part opener 样式。
- **设计**：为 site 补 `.part-page`/opener 视觉等价（不是像素级复制），确保章首罗盘、卷首目标、封面副标题在两端语义一致。任何改动若触及 `CoverCopyTests` pin 的字面串，必须在同一变更里更新测试并在 PR body 标注“封面文案契约变更”。
- **不做**：不改封面文案，不把“全程实物实验”写回去。

#### 4.1.5 长表与 CJK token

- Print 已有 `table-layout: fixed`、`thead { display: table-header-group }`、`tr { break-inside: avoid }`、`overflow-wrap: break-word`。**不改**。
- Site 已有 `.table-scroll` 包装（`wrap_tables()` in `build_html.py`）与 table 样式。保持。
- CJK token：print/site 已有 serif/sans/mono 变量与 `NotoSerifSC` 正文。设计只允许在不改变版心/字号基线的前提下微调段前后距、列表缩进、行内 code padding；任何影响 `width: 176mm` 或 body `font-size: 10.2pt` 的改动禁止。

### 4.2 首批配图（5 章）

#### 4.2.1 通用规则

- **轨道**：全部走 Handraw 知识轨。产物为 `assets/illustrations/staged/<name>.svg`（源）+ 发布到 `docs/public/images/<name>.png`（或按现有发布链）；每个被 Markdown 引用的 PNG 必须有 tracked SVG source，满足 `test_figure_sources.py`。
- **标注**：图内或图注含 `原理示意/非实拍`；不出现“实拍/示波器实测/板上验证”字样，除非引用的是真证资产（本批不新增真证）。
- **引用语法**：优先 `![caption](/images/<name>.png)` 走 `book-markdown.mts` 的 figure 包装；需要 size class 时用 Markdown image attr 或等价 HTML `<figure class="book-figure fig-m">`。
- **禁止**：`stick-scene` 不作为审计锚点补偿；不复制参考书图；不凭空捏寄存器位值（所有技术标注可追溯 RM0008 / HAL v1.8.6 / 现有章节正文）。

#### 4.2.2 逐章计划

每章目标是**覆盖当前最大 gap** 并向 target 推进；不强求一次补满到 target，但必须给出可审计的 delta。

| id | 当前 gap（from → to） | 插入策略 | 拟增图（工作名） | 预期效果 |
| --- | --- | --- | --- | --- |
| `ch06` | 5826，`size 三列：Flash 与 RAM 各吃哪份` → `章末` | 在 `nm --size-sort`/map 审计叙述与“离开检查”之间插 2 张机制图 | `ch06-size-audit-flow`（size/map/nm 三证据对账流程，S/M）；`ch06-map-region-ledger`（Flash/RAM/CCM 占用账本与超限信号，M） | 把 5826 长 gap 切成 <~2500 的段；锚点 6→8 |
| `ch11` | 4829，`SysTick 与 RTC 的分工` → `章末` | 在分工表后补 SysTick/RTC 选择决策与 tick 中断链路图 | `ch11-timebase-decision`（睡眠/掉电/精度/功耗决策树，M）；`ch11-systick-isr-chain`（SysTick→HAL_IncTick→uwTick→HAL_Delay 链，S/M） | 切开尾段大 gap；锚点 4→6 |
| `ch26` | 5313，`两条命令的分工` → `章末` | 在命令分工后补 FinSH 调用路径与设备框架对象生命周期 | `ch26-finsh-dispatch-path`（命令行→解析→符号/设备→ops，M）；`ch26-device-lifecycle`（open/read/write/close + refcount 生命周期，M） | 切开尾段；锚点 6→8 |
| `ch46` | 8846，`1. 三阶段路线与过关判据` → `机制` | 这是最大的 gap 且跨“路线→机制”段；在路线表后、机制节前插 2-3 张过关判据/路线图 | `ch46-gate-checklist-map`（L0–L5 过关判据矩阵图，M/L）；`ch46-route-branching`（学习路线分叉：裸机/RTOS/联网/电机，M） | 把 8846 切成两段 <~3500；锚点 5→7/8 |
| `apD` | 5954，`UART、I2C、SPI、CAN 与 USB` → `工程习惯` | 术语附录后半段缺图；在总线对照簇后补“选型/排错速查”图 | `apd-bus-selection-matrix`（UART/I2C/SPI/CAN/USB 场景选型速查，M）；`apd-debug-symptom-map`（现象→首查对象速查，S/M） | 切开尾段；锚点 4→6 |

实现时每张图必须：在对应 `tools/handraw_track/fig_*.py`（或新模块，注册进 `publish_staged.py` MODULES）中有确定性生成函数；生成 SVG 落 `assets/illustrations/staged/`；发布 PNG 落 `docs/public/images/`；Markdown 引用处有四要素图注。

#### 4.2.3 缺口与 honest accounting

- 首批后 5 章仍可能低于 target（尤其 apD/ch11 缺口 5）。设计**不宣称**首批达标，只宣称“gap 被显著切分、锚点单调增加、无回归”。后续批次按同契约继续。
- `tools/audit_book.py` 的 gap 只认 PDF 锚点；`stick-scene` 不计数。若未来想让 scene 计数，需另开设计改 `extract_visual_anchors` 及其测试。

## 5. 审计门与验证

### 5.1 现有门（必须保持绿）

- `npm run docs:build`
- `python -m book.build_html --check`（53 页）
- `python -m book.checks --check`
- `python -m book.md_links`（当前已知 20 个预存问题属 #179/#180/#183；本批不得新增）
- `python tools/slop_lint.py`
- `python -m unittest book.tests.test_print_sections book.tests.test_figure_sources book.tests.test_figure_mirrors book.tests.test_handraw_layout book.tests.test_handraw_chrome`（按触及面选子集；凡动图源/发布链必跑 figure/handraw 全套）
- `python tools/handraw_track/publish_staged.py --check`（若新增/改图）

### 5.2 本设计新增门（提案，PR body 说明）

**问题**：B46 计划承诺的“only-improve threshold registry / `test_book_audit.py` 登记已知超标清单”在仓库中不存在（`book/tests/test_book_audit.py` 不存在，`rg "only.improve|threshold" book/tests docs/superpowers` 无匹配）。因此本设计不能假装它存在。

**提案 A（推荐，随实现 PR）**：新增 `book/tests/test_book_audit_thresholds.py`（或等价），锁定：

- 全书 `chapters_below_target`、`pdf_visual_anchors`、`photos` 只允许变好或持平；
- 5 目标章各自的 `visual_anchor_deficit` 与 `max_visual_gap_chars` 只允许下降/持平；
- 阈值从 `.temp/audit_book.current.json` 的当前值固化为上限。

**提案 B（备选）**：只在 PR body 记录 before/after 审计 JSON，不加门。**不推荐**，因为容易回退。

本设计默认采用提案 A，但因为这是新增测试门/政策面，**实现 PR 必须在 body 中显式声明**。

### 5.3 不可作为验证的命令

- `npm run perf:budget` / `npm run test:browser` — `package.json` 无此脚本。
- 全书构建 PDF 的布局审计若本地缺 `book/dist/print/merged-book.pdf`，需先构建；不能拿缺文件的 SKIP 当绿灯。

## 6. 风险与回滚

| 风险 | 表现 | 缓解 |
| --- | --- | --- |
| 视口撑宽 | 印刷全书缩字 10.2pt → ~8.6pt | 不碰 4 条视口契约；改 CSS 后跑 `PrintCssTests` + 抽样 PDF audit |
| 图源门失败 | 引用 PNG 无 tracked SVG | 每张图先入 `fig_*.py` + staged SVG，再发布 PNG，再引用 |
| 审计 gap 误判 | stick-scene/新包装不被计数 | 只用 `![]`/`<figure><img>`；不依赖 scene |
| 封面文案回归 | CoverCopyTests 红 | 不改 cover subtitle 字面值 |
| 大面积样式扰动 | 站点/印刷分页退化 | 薄片落地：先 1 章 + 1 条 CSS 规则，构建验绿再扩 |

回滚：每个薄片独立提交；图与样式分提交，便于单独 revert。

## 7. 实现切片（批准后）

1. **S1 基线快照**：保存当前 audit JSON 为基线产物（`.temp/` 或 PR 附件），确认 5 章目标值。
2. **S2 版式薄片**：仅 `print_css.py` + `style.css` 引入 `fig-s/m/l` 选择器（默认 M = 现状）；跑 `PrintCssTests`、`docs:build`、`build_html --check`。
3. **S3 首张图试点（ch06 或 ch11）**：走完整 handraw 发布链，验证 `figure_sources`/`publish_staged --check`/audit 锚点增加。
4. **S4 扩到 5 章**：按 4.2.2 逐章补图，每章一组小提交。
5. **S5 审计门**：落提案 A 的阈值测试（PR body 声明新增门）。
6. **S6 验证与 PR**：窄门全绿，记录 before/after audit delta；触及印刷版式/图尺寸的切片必须包含实际 PDF 构建 + `tools/audit_pdf_layout.py` 结果。

## 8. 完成检查

批准后，实现完成的定义：

- [ ] 5 目标章 `visual_anchor_deficit` 均下降或持平，`max_visual_gap_chars` 均下降或持平（对比基线 `.temp/audit_book.current.json`）。
- [ ] 无新增 `book.md_links` 问题；现有 20 个预存问题不恶化。
- [ ] `PrintCssTests` 四条视口契约字面值不变；`CoverCopyTests` 字面值不变。
- [ ] 新增图都有 tracked SVG 源、`publish_staged.py --check` 过、图注含四要素 + `原理示意/非实拍`。
- [ ] `docs:build`、`build_html --check`、`checks --check`、`slop_lint` 绿。
- [ ] 触及印刷版式/图尺寸的变更，实际构建 `merged-book.html`/`merged-book.pdf` 并跑 `python tools/audit_pdf_layout.py`（缺 PDF 时不得记绿）；L 档 figure 块高 ≤170mm（A4 landscape 210mm − 上 21mm − 下 19mm），图片 `max-height` 不超过 150mm 或经 PDF 实测证明的更小值。
- [ ] PR body 明确声明：新增审计阈值门（若采纳提案 A）；未改死文件 `book/print/book-print.css`；未改真证/镜像/handraw guard 语义。

## 9. 待批准问题

1. 批准本设计稿（1b：版式系统 + 5 章首批配图）后，我将按 `superpowers:writing-plans` 产出实现计划；**实现前不改代码**。
2. 审计阈值门采用**提案 A（新增 `test_book_audit_thresholds.py`）**还是提案 B（仅 PR body 记录）？默认 A。
3. 首批 5 章的图名/插入点允许在实现时因正文局部结构微调，但必须保持“覆盖当前最大 gap”的约束；是否接受？

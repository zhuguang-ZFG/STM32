# 双书合并 B5（站点切换与收尾）Implementation Plan

**Scope:** 合并书站点以 `/STM32/` 根上线（GitHub Pages）；旧 `/STM32/mcu/**` 131 页全部生成跳转存根（覆盖率 CI 核对）；CI 收敛（retire mcu-* 四 workflow，book.yml 重写，新增 deploy.yml）；删旧树（stm32-book/、docs/en/、docs/00–28 旧章、mcu/{mcu-book,docs,scripts,package*,tests,playwright.config.mjs}）；英文版删除前归档 tag；Pages 上线。

**架构决策（对设计 §4.3 的显式偏差登记）：** 设计原文写「VitePress base 改为 /STM32/」。实际执行采用 **`book/build_html.py` 静态站点直接上线**——理由：B1–B4 的站点事实标准已是 build_html（52 页、quizzes 内嵌、SMIL 动画、相对链接天然可挂载），而 mcu VitePress 配置与 mcu 专属脚本（gen-progress/guide-generator/search-render 等 15 个依赖）深度耦合，完整迁入是一次独立的站点重写工程。本批满足 B5 全部出口条件（跳转 100%、回读通过、main 全绿、AC4）；VitePress 迁入登记为站点固化迭代的后续项。

## Tasks

### Task 1: 跳转存根全量生成
- `scripts/legacy-redirects.mjs` 扩展：mapping 94 条之外，为 37 个未映射旧页（guide/reference/lab/各 index/404 等）提供 best-fit 目标表（guide→ch46/ch40、reference/{bibliography→apE,glossary→apD,faq→ch45,about|book|changelog→ch46}、lab/*→ch40、c/build/esp32/gd32/rtos/stm32/ai/projects/index→各卷首章、404→根 404）；总数断言 131。
- 根书源（docs/00–28）的旧 URL 不生成存根——根书从未上线站点，无旧深链。

### Task 2: 站点组装与冒烟
- `scripts/site-assemble.mjs`：staging = build 产物（根）+ `mcu/` 存根目录；根 index 即合并书首页（替换旧「重定向到 ./mcu/」入口）；断言：首页存在、/mcu/ 下无真实正文（只有存根）、存根数 ≥131。
- `scripts/site-smoke.mjs`（改造 mcu mount-smoke）：/STM32/ 挂载 → Chromium 验证 首页 / ch01 / v1 ch09 深链 / [第 40 章](../v6-labs-projects/40-lab-method-instruments.md) / [附录 A](../appendix/A-engineering-deep-read.md) / 旧链跳转（mcu/stm32/03-gpio.html → v1 ch09）/ 资源（anim svg 200）/ quiz 交互（第 1 章答题）。
- 单测：`scripts/tests/site-assemble.test.mjs`。

### Task 3: CI 收敛
- 删除 `mcu-book.yml`、`mcu-quality.yml`、`mcu-links.yml`、`mcu-deploy.yml`。
- 重写 `book.yml`：paths 改 `docs/** book/** scripts/** .github/workflows/book.yml`；job = 书稿七门 + HTML 构建 + artifact。
- 新增 `deploy.yml`（改编 mcu-deploy）：build → stubs → assemble → smoke → deploy-pages（environment github-pages，concurrency pages）。
- `merge-check.yml`、`motor-control.yml`、`release-fetch.yml` 保留。

### Task 4: 删旧树与英文归档
- 归档 tag：`en-archive-2026-11-14` + `en-archive-v1.4.0-2026-11-14`（4710e537，已完成）。
- 删除：`stm32-book/`、`docs/en/`、`docs/00–28`（29 个旧章）、`mcu/mcu-book/`、`mcu/docs/`、`mcu/scripts/`、`mcu/package.json`、`mcu/package-lock.json`、`mcu/tests/`、`mcu/playwright.config.mjs`。
- 保留 `mcu/`：`code/`、`.trellis/`、`AGENTS.md`、`LICENSE`、`README.md`、`CHANGELOG.md`、`CITATION.cff`、`CONTRIBUTING.md`、`SECURITY.md`、`ruff.toml`、`video/`、`wiki/`、`trellis-open-items-*.md`（设计：保留代码、固件与示例）。
- 引用清扫：`.gitignore`（stm32-book/dist 等条目）、`book.yml`、活动代码中指向删除路径的引用清零。

### Task 5: 门禁、证据与发布
- 本地七门禁 + site-assemble + site-smoke 实跑。
- `plans/2026-11-12-merged-book/evidence/b5-local.md`（格式对齐前批）。
- README（plans 批次表 B5 行 + 数据文件）更新。
- PR → CI 绿 → merge → main CI 绿。

## 出口核对（设计 §5 + AC4）
- 旧深链跳转 100%：131/131 存根 + CI 覆盖率断言。
- 站点回读：mount-smoke 七项（首页/深链/旧链跳转/附录/资源/quiz/404）。
- main 全绿：book.yml + deploy.yml + merge-check 三套 workflow success。
- 偏差登记：VitePress 迁入延后（静态站先行，AC4 口径满足）。

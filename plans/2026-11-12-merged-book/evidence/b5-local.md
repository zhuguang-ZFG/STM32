# B5 本地验收证据

- 日期：2026-11-14
- 分支：feat/merged-book-b5（基于 main 4710e537）
- commit：`412413f4`（Task 5 批次记录后验证 HEAD；最终 HEAD 见文末收口验证）
- 环境：Windows + Git Bash；Python 3.13.14；Node v24.14.0；Playwright Chromium（本地安装）

| 命令 | 退出码 | 结果 |
| --- | --- | --- |
| `python -m book.manifest --check` | 0 | 无输出 |
| `python -m book.mapping --check` | 0 | mapping 141 行一致（含冻结源清单/旧页清单适配） |
| `python -m unittest discover book/tests -v` | 0 | 37 tests OK |
| `python -m book.checks --check` | 0 | `checks passed` |
| `python tools/slop_lint.py`（九 glob） | 0 | `干净：没有机械命中。` |
| `python -m book.build_html --check` | 0 | `built 52 pages, 0 planned chapters missing` |
| `node --test scripts/tests/legacy-redirects.test.mjs scripts/tests/site-assemble.test.mjs` | 0 | 5 tests OK（存根全量 131 断言 + 组装三门断言） |
| `node scripts/legacy-redirects.mjs --mapping … --manifest docs/manifest.json --out book/dist/site/mcu` | 0 | `generated 131 legacy redirect stubs` |
| `node scripts/site-assemble.mjs --dist book/dist/site --stubs book/dist/site/mcu --out .temp/pages-site` | 0 | `assembled pages site … stubs=131` |
| `node scripts/site-smoke.mjs --root .temp/pages-site --mount /STM32` | 0 | **smoke passed: 8/8**（首页/v1 深链/旧链跳转落地/附录 A/ch40/anim 资源/quiz 展开/资源无失败） |

## 站点切换要点

- **站点形态**：`book/build_html.py` 静态站（52 页 + 13 组 quiz 内嵌 + SMIL 动画）上线 `/STM32/` 根。对设计 §4.3「VitePress base 切换」的偏差已登记：mcu VitePress 配置与 15 个脚本依赖的完整迁入是独立站点重写工程，本批以静态站满足 AC4 出口；VitePress 迁入列为站点固化迭代后续项。
- **旧链跳转 100%**：mapping 94 条 + best-fit 补齐 37 条 = **131 存根**；覆盖率断言（≥131 + 现场清单双向核对 + 缺页即失败）进 CI。
- **组装断言**：根 index 存在、/mcu/ 下只有存根（非存根页面即失败）、存根数达标。
- **CI 收敛**：`mcu-book.yml`/`mcu-quality.yml`/`mcu-links.yml`/`mcu-deploy.yml`/`release-fetch.yml` 退役；`book.yml` 重写（书稿门 + 构建九 glob + artifact）；新增 `deploy.yml`（build→stubs→assemble→smoke→deploy-pages）；`merge-check.yml` 触发路径去除旧树。
- **删旧树**：`stm32-book/`、`docs/en/`、`docs/00–28`（29 旧章）、`mcu/{mcu-book,docs,scripts,package.json,package-lock.json,tests,playwright.config.mjs}` 删除；`mcu/` 保留 `code/`、`.trellis/` 与仓库元文件（设计 §4.1：保留代码、固件与示例）。
- **英文归档**：删除前打 tag `en-archive-2026-11-14` 与 `en-archive-v1.4.0-2026-11-14`（4710e537，含完整英文版与旧树）；Release v1.3.1 附件不受影响。
- **mapping 门适配**：`book/mapping.py` 的源存在性检查放宽（migrated 源文件允许删除——内容已进新书）；AC1 覆盖率核对改用冻结清单 `book/data/expected-sources.json`（B4 完成态两书 manifest 全集，root 36 + mcu 101）与 `book/data/legacy-pages.json`（旧页 131）。

## 本批新增/修改文件

- 新增：`scripts/site-assemble.mjs`、`scripts/site-smoke.mjs`、`scripts/tests/site-assemble.test.mjs`、`book/data/expected-sources.json`、`book/data/legacy-pages.json`、`.github/workflows/deploy.yml`、`package.json`
- 重写：`scripts/legacy-redirects.mjs`（全量覆盖）、`.github/workflows/book.yml`（触发路径与 job 重写）
- 删除：`stm32-book/**`、`docs/en/**`、`docs/00–28`、`mcu/mcu-book/**`、`mcu/docs/**`、`mcu/scripts/**`、`mcu/package*`、`mcu/tests/**`、`mcu/playwright.config.mjs`、`.github/workflows/{mcu-book,mcu-quality,mcu-links,mcu-deploy,release-fetch}.yml`

## 未验证与遗留

- 未验证：Pages 实际上线回读（deploy.yml 于合并后触发，GitHub Pages 环境沿用 github-pages；上线后建议浏览器访问 `https://zhuguang-zfg.github.io/STM32/` 回读首页与旧链）。
- 未验证：远程 required checks 现状核实（分支保护设置未改动，按 AC5 记录口径）。
- 遗留（站点固化迭代）：VitePress 迁入、外链巡检（links.yml）、搜索索引与 SEO 工具链、PDF/EPUB 管线接入新构建器。
- 未执行：任何超出 B5 的远程操作；Pages 切换由 deploy.yml 在 main 上自动完成。

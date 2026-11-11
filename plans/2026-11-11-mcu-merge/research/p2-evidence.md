# P2 执行证据（AC3 / AC7）

日期：2026-11-11 · 环境：候选 worktree `D:\Users\STM32-mcu-merge-p1`（分支 `feat/mcu-merge-p1`）· node v24.14.0 · npm 11.9.0 · Python 3.13.14

## 变更面

**单源配置**：新建 `mcu/scripts/site-config.mjs`（HOST/BASE/REPO/REPO_SUBDIR/SITE_ORIGIN/pageUrl/repoBlobUrl/repoTreeUrl）；消费方 9 处改导入——`config.mts`、`seo-check`（保留 re-export 兼容旧 import）、`pages-check`、`docs-check`、`search-check`、`measure-site`、`book-guide/generate`、`playwright.config.mjs`。

**身份元数据**：`robots.txt` sitemap、`CITATION.cff` 三处、`mcu-book/manifest.json`（repository + 2 个 registry url）、`build_html.py`（SITE_BASE/REPO_BASE + blob/tree 前缀映射）、`McuFooter.vue`/`McuHero.vue` 仓库链接。

**测试对齐**：6 个测试文件字面量更新 + 新增 3 类回归（新 base 正例 / 旧 base 负例 outOfBase / SelfBlob 前缀映射三口径）；`workflow.test.mjs` 适配根 `mcu-*.yml`（4 个读路径 + ruff 断言 `/^check/` + `includes('mcu/ruff.toml')` + `uses: ./.github/workflows/mcu-quality.yml`）。

**内容链接**：docs 32 文件 + 根 3 文件 + mcu-book 6 文件，前缀映射 `blob|tree/main/`→`STM32/.../main/mcu/`、`issues`→`STM32/issues`；旧站点 URL 9 处。`.trellis/` 零改写。

**附带修复**：`gen-progress.mjs` 血统两段查询；`video/publish/*.mjs` 17 文件旧工作区绝对路径改 `MCU_ROOT` 派生；`.agents/skills/video-release/SKILL.md` 路径文字。

## 门禁（全部在最终树上执行）

| 命令 | 结果 |
|---|---|
| `npm ci` | added 194 packages in 52s，exit 0 |
| `npm test` | 136 pass / 0 fail |
| `npm run quality`（test+projects+docs:build+anim+readme+reading+prose+links+docs+nav+seo+perf+a11y+pages+search） | 全链通过，exit 0，98.5s |
| `npx playwright install chromium` | 已就位，exit 0 |
| `npm run test:browser` | 7 passed (46.5s) |
| `python mcu-book/build_html.py --check` | PASS（94 chapters，题图 94/94，exit 0） |
| `npm run guide:generate`（经 quality 内 guide:check PASS） | hash 链 PASS，canonical/base 已新 |

## 关键回归证据

- **旧 base 负例**：`pages-check.test.mjs` 断言 `/mcu/c/01.html#栈`、`/mcu/#hero`、`/mcu#hero` 全部判 `outOfBase`；`search-check.test.mjs` 断言默认口径 ≠ `/mcu/`。
- **SelfBlob 三口径**：NEW（`STM32/blob/<ref>/mcu/<path>` 剥前缀对账）、OLD（旧仓历史链接原样对账）、OUTSIDE（STM32 无 `mcu/` 前缀 → 点名「mcu/ 子树之外」）。
- **updates 轨道**：`docs/.vitepress/data/updates.json` 8 条真实 MCU 章节（2026-11-07），无 STM32 书原生条目（修前：崩溃 ENOENT / 修后空 → 血统查询后恢复）。
- **workflow 断言**：根 `mcu-deploy.yml` 复用 `./.github/workflows/mcu-quality.yml`；deploy needs quality + `result == 'success'`；`upload-pages-artifact` 前 pages/search 双检 `--dist site`。

## AC3 判定

站点身份单一来源 + 消费方全切 + 身份元数据全改 + 测试对齐全绿 + 旧 base/旧仓字符串五类处置（见 `p2-string-classification.md`）。**AC3 通过**。

## AC7 判定

字符串分类纪律执行：全部 `/mcu/` 与旧仓字符串经 A/B/C/D 四类扫描定级；运行时改新、兼容测试与负例保留、`.trellis` 历史零改写、历史作业产物（`gen_cards_batch2.py`、`video/jobs/**`）登记不修。**AC7 通过**。

## 遗留（不在 P2 范围）

- `video/jobs/**` 历史作业产物中的旧路径：登记备查，随作业归档自然失效。
- P3（AC4）：Pages staging 组装（artifact 根含 `mcu/` 子目录）、deploy workflow 改造、触发矩阵。
- 主工作区用户 WIP（`mcu/CITATION.cff` 等 9 个 `M` + 未跟踪文档）与候选 `CITATION.cff` 身份改动在拣选合并时需对账。

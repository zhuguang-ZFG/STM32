# P2 字符串分类证据（AC3 / AC7 支撑）

日期：2026-11-11 · 范围：`D:\Users\STM32-mcu-merge-p1`（候选 worktree）· 口径：全量 `grep` 扫描 `mcu/`，逐类处置，不做无条件全局替换。

## 方法

对两类字符串全量扫描并按「运行时 / 新输出 / 兼容测试 / 负例 / 历史记录」五类处置：

- A 类：站内 base 形态 `/mcu/`（排除 `STM32/mcu`）
- B 类：旧仓标识 `zhuguang-ZFG/mcu`（github.com 域）
- C 类：旧站点 URL `zhuguang-zfg.github.io/mcu/`
- D 类：旧工作区绝对路径 `D:/Users/mcu`

`.trellis/` 一律视为历史记录不动（31 个文件含 A/B 类字符串，均为任务时间线快照）。

## A 类：base `/mcu/` 处置表

| 区域 | 处置 | 说明 |
|---|---|---|
| `scripts/{config消费方}.mjs/mts`（seo-check/pages-check/docs-check/search-check/measure-site/book-guide/generate/playwright.config/config.mts） | **改新** | 已切到 `site-config.mjs` 单源（见 design.md §4） |
| `docs/.vitepress/theme/{McuFooter,McuHero}.vue` | **改新** | 仓库链接指向 STM32 仓 + `mcu/` 前缀 |
| `tests/*.test.mjs` | **改新** | 字面量预期换 `/STM32/mcu/`，并**新增旧 base 负例**（防回退假绿） |
| `scripts/docs-check.mjs` 源文件卫生规则 | **保留** | 禁 `/mcu/`、`/STM32/mcu/` 站内绝对路径——负例门 |
| `scripts/perf-budget.mjs` shellAssets 正则 | **保留** | 前缀无关，`/mcu/assets/` fixture 仍有效 |
| `video/publish/*.mjs`（约 44 处） | **非 base**：见 D 类 | 实为旧工作区绝对路径，非站点 base |
| `.trellis/`（31 文件） | **不动** | 历史记录 |

## B 类：旧仓 `zhuguang-ZFG/mcu` 处置表

| 区域 | 处置 | 说明 |
|---|---|---|
| `docs/**.md`（32 文件） | **改新** | 条件化前缀映射：`blob/main/`→`STM32/blob/main/mcu/`、`tree/main/`→`STM32/tree/main/mcu/`、`issues`→`STM32/issues` |
| `README.md`/`SECURITY.md`/`CODE_OF_CONDUCT.md` | **改新** | 同上三模式 |
| `mcu-book/book/*.md` + `mcu-book/README.md` + `mcu-book/manifest.json` | **改新** | 同前缀映射（首轮 sed 漏覆盖 mcu-book/，本轮补齐） |
| `scripts/docs-check.mjs` `SELF_BLOB_OLD` | **保留** | 旧仓历史链接原样对账（历史文档不改写） |
| `tests/docs-check.test.mjs` 旧仓链接 fixture | **保留** | 兼容测试 |
| `.trellis/` | **不动** | 历史记录 |

## C 类：旧站点 URL `zhuguang-zfg.github.io/mcu/` 处置表

| 区域 | 处置 | 说明 |
|---|---|---|
| `docs/reference/book.md`（下载表 2 处）、`docs/reference/changelog.md`、`README.md`（Q4）、`mcu-book/book/{D-术语表,F-常见问题}.md`、`mcu-book/README.md` | **改新** | `github.io/mcu/`→`github.io/STM32/mcu/` |
| `docs/public/book-guide/index.html` | **再生成** | `guide:generate` 产物，源改后重建（hash 链 PASS） |
| `video/publish/yt-plan.md` 等计划文档中的形态描述 | **保留** | 历史计划文档的散文引用，非活链接输出 |

## D 类：旧工作区绝对路径 `D:/Users/mcu` 处置表（本轮新发现并修复）

合并把项目从 `D:\Users\mcu` 搬到 `D:\Users\STM32\mcu`，旧绝对路径全部失效。

| 区域 | 处置 | 说明 |
|---|---|---|
| `video/publish/*.mjs`（17 文件 / 44 处） | **修复** | 改 `MCU_ROOT = fileURLToPath(new URL('../../', import.meta.url))` 派生，不再依赖检出位置；`node --check` 17/17 语法通过 |
| `.agents/skills/video-release/SKILL.md` | **修复** | 共浏览器 profile 路径文字引用 |
| `scripts/arch-diagrams/gen_cards_batch2.py` | **记录不修** | 2026-11-03 一次性批处理脚本，输入 `.temp` 快照已不存在，属历史作业产物 |
| `video/jobs/**/page.html`（8 个快照） | **记录不修** | 历史网页捕获证据 |
| `video/jobs/**/tools/svg2png169.mjs` | **记录不修** | 历史作业一次性工具（file:// + 截图） |
| `docs/en/**`（STM32 书旧章节路径，出现于 git 历史） | **记录不修** | 已不存在的旧书路径，非工作区字符串 |

## 附带修复（同一门禁暴露）

- `scripts/gen-progress.mjs` `collectUpdates()`：合并后 git 历史含 STM32 书原生 `docs/**` 与 MCU 历史，原实现按 `docs/` 前缀收集 → ENOENT 崩溃 + 潜在日期串台。改为两段血统查询（post-import `:(top)mcu/docs` + pre-import `导入merge^2 -- :(top)docs`）+ 存在性过滤。回归证据：`docs/.vitepress/data/updates.json` 恢复 8 条真实 MCU 章节（2026-11-07），无 STM32 原生条目。

## 结论

- 运行时身份字符串（A/B/C 类活性部分）全部收敛到 `site-config.mjs` 单源或新仓/新 base 字面量。
- 兼容测试与负例门保留；历史记录零改写。
- D 类为计划外发现的真实合并缺陷，已在 P2 一并修复（发布流水线）或登记备查（历史作业产物）。

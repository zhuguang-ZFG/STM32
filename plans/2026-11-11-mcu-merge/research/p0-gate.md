# P0 基线与保护 — 放行结论

日期：2026-11-11（Asia/Shanghai，执行快照时点）  
阶段：P0（implement.md）  
结论：**有条件通过**（本地证据齐备；无未知覆盖；来源侧存在需后续复核的临时/参考资产项，未发现已确认的不可再生资产丢失）

## 1. 基线与祖先关系（AC1 证据）

| 项 | 结果 | 证据 |
|---|---|---|
| 目标仓库 | `D:\Users\STM32`，分支 `feat/mcu-subtree-merge`，HEAD `92fc917ca6f0c93f0fc736bf3ea1eab3f8c0aec6`，`HEAD:mcu` tree `93e40d58340884f4d0da88475c382b8f5400fba8` | `git rev-parse HEAD` / `git branch --show-current`；`research/p0-execution-snapshot-2026-11-11.json` |
| 来源仓库 | `D:\Users\mcu`，分支 `main`，HEAD `cf161532c823446016a9deb60d31e5263397b7d7` | `git -C D:/Users/mcu rev-parse HEAD` / branch |
| 祖先关系 | `cf161532...` 是目标 HEAD 的祖先（`merge-base --is-ancestor` 退出码 0） | `ancestor_check.exit_code=0` |
| 已导入差异 | `git diff --name-status cf161532... HEAD:mcu` = 10 路径：删除 `mcu/.github/workflows/{book,deploy,links,quality}.yml`，修改 `mcu/README.md`、`mcu/docs/.vitepress/config.mts`、`mcu/scripts/{docs-check,measure-site,search-check,seo-check}.mjs` | 与 `research/baseline.json` `committed_subtree_delta` 完全一致 |
| 与规划基线对比 | target/source HEAD、10 路径差异、baseline 受保护文件 SHA256 均一致；未执行二次导入、未改写 `mcu/` 历史 | `p0-execution-snapshot-2026-11-11.json`、`baseline.json` |

## 2. 工作区保护与备份（AC1 证据）

### 2.1 当前工作区盘点（执行时点）

- **已跟踪修改（9，均属既有 WIP/迁移定制，非本轮 P1+ 实施）**：`mcu/.trellis/tasks/10-28-social-video-ai-tools/{check,implement}.jsonl`，`mcu/.trellis/tasks/11-07-historical-spec-closure/{check,implement,prd,task}.jsonl`，`.../research/{task-cards.md,task-ledger.json}`，`mcu/CITATION.cff`。当前字节 SHA256 与 `baseline.json` 记录一致（已逐项核对）。
- **未跟踪既有任务文档（7）**：`mcu/.trellis/tasks/11-07-historical-spec-closure/{design.md,implement.md}` 及 `research/{baseline-drift-audit.md,review-handoff.md,w1-evidence.md,w1-language-diffs.md,wave0-evidence.md}`；SHA256 与 baseline 一致。
- **未跟踪本地工具状态**：`.qoder/settings.local.json`（baseline 为 `.qoder/` 目录状态，现以 `-uall` 观测到具体文件；内容已备份）。
- **本轮规划产物（未跟踪）**：`plans/2026-11-11-mcu-merge/{prd,design,implement}.md` 及 `research/{baseline.json,findings.md,p0-execution-snapshot-2026-11-11.json,p0-source-assets.md,p0-gate.md}`、备份目录（见下）。

### 2.2 实际字节备份

- 备份目录：`plans/2026-11-11-mcu-merge/research/wip-backup-2026-11-11/`
- 清单：`.../wip-backup-2026-11-11/manifest.json`（`created_at: 2026-11-11T17:43:51.961970+08:00`，22 个文件，含路径/字节/SHA256/备份路径）
- 覆盖范围：9 个已跟踪修改文件 + 7 个未跟踪任务文档 + `.qoder/settings.local.json` + 本轮计划/基线文档（5）。**未改动原文件字节**；Git patch 不作为未跟踪文件的唯一保存形式。
- HEAD blob SHA256（已跟踪修改的基线对照）已单独记录于执行日志（`git show HEAD:<path>`）；当前工作区与 HEAD 差异即为既有 WIP，已完整保留并备份。

## 3. 外部来源未跟踪/忽略资产（AC1/无资产丢失风险控制）

- 证据：`research/p0-source-assets.md`（`D:\Users\mcu`，64673 项忽略/未跟踪，2 项未跟踪非忽略 `.perch/*`）。
- **可再生**：`node_modules/`、`code/` 构建产物、`docs/.vitepress/cache`、`video/.cache/tts`、多数 `video/out`/`.temp` 中间物、`.superpowers` 快照等（需对应工具链/TTS/构建环境；环境缺失记 `BLOCKED`，不视为 Git 资产丢失）。
- **可由公开资料或发布制品恢复（需核对）**：`.trellis/ref/**.pdf`（ST/GD32 公开文档镜像）、`mcu-book/dist/**`（与 release/构建对照恢复）。
- **需复核（不可再生风险未排除，但未确认唯一性）**：`.temp/v2-baseline-20261022/masters/**/*.mp4`、`.temp/backup-c2/*`、零散临时字体/音视频下载件；执行 P4/P5 前与目标/发布存档/权威母版对照，保留必要项并记录 SHA256。
- **结论**：未整树导入依赖/缓存/临时目录；未发现可确证“仅存在于忽略区且无恢复途径的唯一母版/硬件证据”已丢失，但已登记复核项。发布前不得静默删除来源侧待复核资产。

## 4. 候选分支 / worktree 策略（P0 要求）

- **当前仓库状态保持不动**：不覆盖、移动或提交 9 项已跟踪修改、7 项未跟踪任务文档、`.qoder/` 本地状态；不将其误判为 P1+ 合并改动。
- **后续实施（P1 起）**：在明确候选分支/commit 上执行。推荐方案：从 `92fc917ca6f0c93f0fc736bf3ea1eab3f8c0aec6`（或后续确认的集成基线 commit）创建独立 worktree/候选分支承载合并收口提交；每批仅纳入该批所需文件与变更。若需携带本工作区已有 WIP 的特定文件，按 `wip-backup-2026-11-11/manifest.json`/文件清单**显式拣选**并在提交说明中标注归属，不隐式带入。
- **来源目录**：`D:\Users\mcu` 在验收与资产盘点结束前保留；本轮未修改来源仓库。
- **外部工具/绝对路径**：后续涉及 Trellis/命令执行时区分 Git 根（`D:\Users\STM32`）与 MCU 项目根（`D:\Users\STM32\mcu`），遵循 `design.md` §3/§6。

## 5. P0 放行判定

| 条件 | 判定 | 备注 |
|---|---|---|
| 重新读取 HEAD/分支并与 baseline 对比 | 通过 | 新增执行快照，无基线漂移 |
| 来源 SHA 为祖先且 10 路径迁移差异已审查 | 通过 | 与 baseline 一致，可解释 |
| WIP/计划文件盘点、字节备份、哈希核对 | 通过 | 22 文件备份 + manifest；HEAD 对照已取证 |
| 外部来源未跟踪/忽略资产分类 | 通过（含复核项） | 见 `p0-source-assets.md`；复核项不得静默丢弃 |
| 候选分支/worktree 策略明确 | 通过 | 本节 §4 |
| 未知覆盖 | 无 | 未执行导入/覆盖/重置操作 |
| 资产丢失 | 未发现已确认丢失 | 需 P4/P5 持续关注复核项 |

**P0 放行**：可进入 **P1（维护入口与规范）** 规划/实施准备；实际代码改动应按 §4 在明确候选分支/worktree 上分批进行，并在每批后保留差异与验证日志。

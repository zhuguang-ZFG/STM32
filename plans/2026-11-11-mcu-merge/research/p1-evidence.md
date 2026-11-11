# P1 证据 — 维护入口与规范（AC2 / AC6）

日期：2026-11-11  
候选分支/worktree：`feat/mcu-merge-p1` @ `92fc917ca6f0c93f0fc736bf3ea1eab3f8c0aec6`  
路径：`D:\Users\STM32-mcu-merge-p1`（从 `D:\Users\STM32` 主工作区创建，主工作区 WIP/未跟踪文件未改动）

## 1. 候选环境与基线（只读确认）

| 项 | 值 |
|---|---|
| Git 根 | `D:\Users\STM32-mcu-merge-p1` |
| MCU 项目根 | `D:\Users\STM32-mcu-merge-p1\mcu` |
| 对外站点根（目标身份） | `/STM32/mcu/`（P2/P3 继续收口） |
| 分支 / HEAD | `feat/mcu-merge-p1` / `92fc917ca6f0c93f0fc736bf3ea1eab3f8c0aec6`（与 P0 基线一致） |
| 来源 HEAD（计划基线） | `cf161532c823446016a9deb60d31e5263397b7d7`（ancestor，见 P0） |
| 10 路径迁移差异 | 与 `research/baseline.json` 一致；审查结论见 `research/p1-migration-review.md` |

## 2. AC2 — 双书入口与维护边界

| 交付 | 状态 | 证据 |
|---|---|---|
| 根 README 双书入口与边界 | 完成 | 候选 `D:\Users\STM32-mcu-merge-p1\README.md`：快速导航增加 MCU 姊妹书入口；新增 `## 双书入口与维护边界`（两书入口、Git 目录范围、维护边界、构建/验收、三个根说明、计划链接）；保留 BMS-Z 姊妹仓库说明，不覆盖 `mcu/` 内容。中途曾因裸路径误改主工作区 `D:\Users\STM32\README.md`，已执行 `git checkout -- README.md` 恢复至 HEAD；候选 README 已用绝对路径补齐并复核。 |
| 根 STRUCTURE 双书地图与边界 | 完成 | `STRUCTURE.md`：新增 `## 双书与三个根`；目录表增加 `mcu/` 子树入口；边界增加双书分域、MCU 项目根执行、历史任务不自动改写、门禁不降级/发布受控 |
| MCU 内容边界保持 | 完成 | 未修改 `mcu/README.md`、`mcu/docs/**`、`mcu/code/**`、`mcu/mcu-book/**` 内容；根文档仅路由/引用 |

## 3. 根 AGENTS 路由（不复制规则正文）

| 交付 | 状态 | 证据 |
|---|---|---|
| `AGENTS.md`（新建） | 完成 | 路由到：STM32 书（`docs/CONTENT_GUIDE.md`、`STRUCTURE.md`、`README.md`、`stm32-book/BOOK_*_SPECS.md`、`docs/superpowers/specs/`）；MCU 子树（`mcu/AGENTS.md`、`mcu/.trellis/spec/index.md`、`mcu/.trellis/workflow.md`、`mcu/README.md`、`mcu/docs/index.md`、`mcu/.trellis/tasks/`）；合并计划（`plans/2026-11-11-mcu-merge/{prd,design,implement}.md`、`research/{findings,baseline}.json`）。声明三个根、分域维护、门禁不降级、历史保真、发布受控。未复制规则正文。 |

## 4. AC6 — Trellis 上下文、任务清单与路径分类

### 4.1 Trellis 可读性与 spec 层

- MCU 规范入口：`mcu/AGENTS.md`、`mcu/.trellis/workflow.md`、`mcu/.trellis/spec/index.md`（8 层：`docs-site`、`book`、`firmware-common`、`firmware-stm32`、`firmware-esp32`、`firmware-rtos`、`firmware-gd32`、`video`）。
- 从 MCU 项目根执行 `python .trellis/scripts/get_context.py --mode packages`：输出 `Single-repo project (no packages configured)` 与 `Spec layers: book, docs-site, firmware-common, firmware-esp32, firmware-gd32, firmware-rtos, firmware-stm32, video`（该 CLI 对 `--mode packages` 参数形式报 usage，但产生有效层信息；证据已记录）。
- 从 MCU 项目根执行默认 `python .trellis/scripts/get_context.py`：报告 `ERROR: Not initialized. Run: python3 ./.trellis/scripts/init_developer.py <name>`（fresh worktree 无开发者身份；**未执行 init**）。活动任务与 spec 仍可通过目录与 inventory 直接发现。

### 4.2 任务 inventory 与一致性（快照）

来源：`research/p1-task-inventory.json`（扫描 `mcu/.trellis/tasks/**/task.json`）。

| 指标 | 值 |
|---|---|
| `task.json` 数量 | 45 |
| parent/children/subtasks 一致性问题 | 0 |
| 状态分布 | `planning` 10，`in_progress` 13，`completed` 22 |

**任务状态/历史前后差异**：`git diff --name-only -- mcu` 为空（0 文件）。P1 未修改 `mcu/.trellis/tasks` 下任何任务文件；历史任务状态、证据与 jsonl 内容保持不变（未自动归档或改为通过）。

### 4.3 路径/会话指针分类（静态审计）

来源：`research/p1-trellis-path-audit.json`（扫描 `mcu/.trellis/tasks` 下 `.json/.jsonl/.md`）。

| 指标 | 值 |
|---|---|
| 扫描文件数 | 373 |
| 含绝对路径 token 的文件 | 50 |
| 仅含 `/mcu/` 路径 token 的文件 | 8 |
| findings 总数 | 58 |

分类统计：

| classification | 数量 | 说明 |
|---|---:|---|
| `historical_url_or_external_reference` | 24 | 历史 URL/外部引用（含 1 条 session 指针特征命中：`mcu/.trellis/tasks/10-27-ai-dev-deepen/research/external-sources.md`，归为历史外部引用，未改写） |
| `historical_environment_or_execution_record` | 11 | 历史环境/执行记录（工具路径、构建产物路径等） |
| `needs_context_review` | 8 | 仅 `/mcu/` token，需结合上下文判断（未改写） |
| `historical_record` | 7 | 一般历史记录中的绝对路径 |
| `historical_local_absolute_path` | 5 | 本地绝对路径历史痕迹 |
| `historical_pre_merge_workspace_path_needs_adaptation_if_reexecuted` | 3 | 合并前工作区路径；**若复跑任务需按新根/MCU 项目根适配**，不作为本轮自动重写对象 |

会话指针：静态关键词命中 1 条，分类为 `historical_url_or_external_reference`；未发现需在 P1 重写的活动会话指针。P1 不改写历史记录。

### 4.4 活动任务 jsonl 逐项解析（AC6「逐项可解析」）

来源：`research/p1-active-jsonl-parse.json`（首次，2 条缺失）→ `research/p1-active-jsonl-parse-v2.json`（受控纳入后复核）。cwd = MCU 项目根 `mcu/`；范围 = 23 个活动任务（`planning` 10、`in_progress` 13）目录下全部 `*.jsonl`；每条 JSON 行的 `file` 依次按 MCU 项目根 → Git 根 → 任务目录解析。

| 指标 | 首次（v1） | 复核（v2，当前） |
|---|---:|---:|
| 活动任务数 | 23（planning 10 / in_progress 13） | 23 |
| 扫描 jsonl 文件 | 46 | 46 |
| `file` 条目 / 模板行（无 `file`） | 256 / 2 | 256 / 2 |
| JSON 解析失败行 | 0 | 0 |
| 在 MCU 项目根可解析 | 254 | **256** |
| **三根均不可解析（缺失）** | **2** | **0** |

抽查 `10-25-book-production/implement.jsonl`（相对路径形态）：`.trellis/tasks/...`、`.trellis/spec/docs-site/{quality-contract,content}.md`、`mcu-book/manifest.json`、`mcu-book/build_html.py` 共 8/8 全部按 MCU 项目根解析成功（v1/v2 一致）。

**处置（用户选择 a：受控纳入，未改写历史 jsonl）**

- 缺失条目：`10-28-social-video-ai-tools`（`in_progress`）`check.jsonl:2` → `video/sweety-handdraw-video/skills/sweety-handdraw-video/references/quality-gates.md`、`implement.jsonl:4` → `…/SKILL.md`。
- 根因：`mcu/video/.gitignore` 原规则 `/sweety-handdraw-video/` 忽略整目录，subtree 未导入；两文件仅存于 `D:\Users\mcu`。
- 修复：从 `D:\Users\mcu\video\sweety-handdraw-video/skills/sweety-handdraw-video` 复制到候选同路径（排除 `__pycache__`/`*.pyc`），**832 个文件，50,469,802 B**；`SKILL.md` 15,252 B、`references/quality-gates.md` 13,050 B 已在 MCU 项目根可解析。
- `.gitignore` 最小化放行：`/sweety-handdraw-video/` → `/sweety-handdraw-video/**` + `!/sweety-handdraw-video/skills/` + `!/sweety-handdraw-video/skills/**`（`/pydeps/` 仍忽略；`git check-ignore` 确认两条引用文件不再被忽略、`video/sweety-handdraw-video/other.txt` 仍被忽略）。
- 历史 `check.jsonl` / `implement.jsonl` **未改写**；`task.json`/任务状态未改。候选 `mcu/` 变更仅为 `M mcu/video/.gitignore` 与新增未跟踪 `mcu/video/sweety-handdraw-video/`（832 文件，待纳入），无其他历史任务文件改写。

空清单记录：活动任务 `11-07-historical-spec-closure`（`planning`）的 `check.jsonl`/`implement.jsonl` 仅含 `_example` 模板行，0 条真实 `file` 条目——不算解析失败，该任务当前无活动上下文条目。

**AC6 判定**——已满足：「活动上下文清单逐项可解析」（256/256 在 MCU 项目根可解析）；静态 token 统计不作为判定依据。

### 4.5 `needs_context_review` 处置

来源：`research/p1-ncr-resolution.json`（8/8 已逐条结合所属任务读取上下文；`rechecked_after` = `p1-ac6-recheck-after-controlled-skill-import`，仍无开放项）。

| 归属 | 数量 | 处置 |
|---|---:|---|
| 活动任务 `10-25-bmsz-validation-depth`（`in_progress`）设计/实施文档 | 2 | `/mcu/` 出现在基础 base、`mcu-book/dist/*.pdf`、GitHub blob 示例等**设计文本**中，非活动 cwd/会话指针；保留不改写，运行时 base 改造留 P2/P3 |
| 归档或已完成任务记录 | 6 | 历史 base/预览地址（含 `localhost:4196/mcu/`）等历史记录，按 R1/AC6 保真保留 |

P1 未改写任何任务历史文件（jsonl 未改）；候选 `mcu/` 变更为受控资产纳入（`mcu/video/.gitignore` + `mcu/video/sweety-handdraw-video/skills/**`，832 文件），不涉及历史任务/证据条目改写。

## 5. 迁移差异审查

见 `research/p1-migration-review.md`：10 路径与 baseline 一致，workflow 删除/脚本与 README/config 定制可解释；P2 需继续收口身份单一来源与旧 base 负例（F1–F7）。

## 6. 验证状态

| 检查 | 结果 |
|---|---|
| 文档/证据落盘（候选） | 已完成：`README.md`、`STRUCTURE.md`、`AGENTS.md`、`plans/2026-11-11-mcu-merge/research/p1-{migration-review,task-inventory,trellis-path-audit,evidence,active-jsonl-parse,active-jsonl-parse-v2,ncr-resolution}.*` |
| 主工作区保护 | 已恢复：`D:\Users\STM32\README.md` 曾因裸路径误改，已 `git checkout -- README.md` 恢复至 HEAD；`STRUCTURE.md`/`AGENTS.md` 无本轮改动；既有 9 个 `mcu/` 下 ` M` 与未跟踪 WIP（含 `.qoder/`、计划文档等）保持原样 |
| `git diff --name-only -- mcu`（候选） | `mcu/video/.gitignore`（最小化放行 `skills/` 子树）；新增未跟踪 `mcu/video/sweety-handdraw-video/`（832 文件，受控纳入）；**历史任务/证据/jsonl 未改写** |
| 活动任务 jsonl 逐项解析（AC6 核心） | **通过**：23 活动任务 / 46 jsonl / 256 条 `file`，**256/256 在 MCU 项目根可解析（v2）**；2 条先前缺失已通过受控纳入 `video/sweety-handdraw-video/skills/...` 解决（jsonl 未改写） |
| `needs_context_review` 处置 | 通过：8/8 已按所属任务状态分类并保留不改写（`research/p1-ncr-resolution.json`） |
| STM32/MCU 构建与门禁 | **未运行**（P1 规范/证据变更；P4 按 AC1–AC7 留证） |
| `get_context.py` 默认（fresh worktree） | **未通过（环境前置）**：需开发者 init（未执行）；不作为 AC6 判定依据 |

## 7. 回退说明

- **仅回退 P1 候选改动**：在候选 worktree 放弃 `README.md`/`STRUCTURE.md`/`AGENTS.md`、P1 研究文件、`mcu/video/.gitignore` 改动与 `mcu/video/sweety-handdraw-video/`，或删除候选分支/worktree：在主仓执行 `git worktree remove D:\Users\STM32-mcu-merge-p1` 后 `git branch -D feat/mcu-merge-p1`；主工作区 `D:\Users\STM32` 的 9M/7??/`.qoder`/`plans` WIP 不受影响。
- **保留证据**：如需保留审计，可先将 `plans/2026-11-11-mcu-merge/research/p1-*` 复制到主工作区未跟踪备份位置再移除 worktree（注意不覆盖主工作区既有 WIP）。
- **历史任务**：未改动，无需回退。

## 8. 结论与下一步

- **P1 分项判定**：AC2 **通过**（双书入口/边界/路由已落地，主工作区误改已恢复）；AC6 **通过**（活动上下文清单逐项可解析：256/256；`needs_context_review` 8/8 已处置）。
- **AC6 处置记录**：选 (a) 受控纳入 `video/sweety-handdraw-video/skills/sweety-handdraw-video`（832 文件，排除 `__pycache__`），`.gitignore` 最小化放行该 `skills/` 子树；历史任务 jsonl **未改写**；缺失根因已归档于 v1/v2 解析证据。
- **构建与门禁**：**未验证**，待 P4。
- **下一步 P2（AC3/AC7）**：`mcu/scripts/site-config.mjs` 单一来源 + Playwright/robots/主题/CITATION/测试预期收口，新 base 正例与旧 base 负例。

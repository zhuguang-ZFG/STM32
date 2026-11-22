# 分阶段实施计划

状态：**部分已被后续决定取代**。本文成文于 B5 合并之前；B5（2026-11-14）把 MCU 正文并入根书稿并退役 `mcu/{docs,mcu-book,scripts,tests,package*,playwright.config.mjs}` 与 `mcu-*.yml` 五个工作流，因此原 P2/P3/P4 中依赖 MCU 独立站点的项不再适用。逐条判定见 [P0 执行快照](research/execution-snapshot-2026-11-19.md)（2026-11-19）。现行依据是 [`plans/2026-11-12-merged-book/`](../2026-11-12-merged-book/README.md)。

已完成的历史导入只作为基线。参见 [需求](prd.md)、[设计](design.md) 与 [调查](research/findings.md)。

## 1. 阶段与依赖

执行顺序：P0 → P1 → P2 → P3 → P4 → P5。每阶段完成后保留差异和验证日志；不要求并行代理。

| 阶段 | 交付 | 涉及范围 | 放行条件 |
| --- | --- | --- | --- |
| P0 基线与保护 | 来源/目标/WIP 清单、不可再生资产清单、候选分支基线 | Git、两目录、已有未提交文件 | AC1；没有未知覆盖或资产丢失 |
| P1 维护入口与规范 | 双书导航、根路由规范、路径与 spec 映射 | README、STRUCTURE、建议根 AGENTS、MCU 上下文 | AC2、AC6；任务能从约定 cwd 继续工作 |
| P2 URL 与身份 | 站点配置统一、运行时路径及回归修复 | MCU 配置/脚本/测试/主题/引用元数据 | AC3、AC7；旧前缀仅出现在已解释位置 |
| P3 CI 与 Pages 组装 | 正确目录 artifact、触发矩阵、发布依赖 | 根 MCU workflows、共享组装脚本、相关回归 | AC4；按公开挂载结构本地验证通过 |
| P4 集成验收 | 两侧完整门、产物哈希、差异审查 | 候选提交及全部受影响交付链 | AC1–AC7；失败/跳过项全部处理 |
| P5 发布与迁移关闭 | 新站回读、旧站兼容决策、维护入口切换 | 远程 PR/CI/Pages 与旧仓入口 | 后续发布指令 + AC8 |

## 2. P0：锁定实际起点

- [x] 重新读取两个 HEAD 和分支；与 `research/baseline.json` 比较。**已完成 2026-11-19**：目标已推进到 `main@4882857e`，新增 [`research/execution-snapshot-2026-11-19.md`](research/execution-snapshot-2026-11-19.md)，规划快照 `baseline.json` 原样保留。
- [x] 验证来源 SHA 为目标祖先，审查来源 tree → `HEAD:mcu` 的迁移差异。**已完成**：`merge-base --is-ancestor` 退出码 0；差异由 10 条扩至 1580 条（848 A / 692 D / 40 M），逐类归于 B5 退役与导入后演进，见快照 §2。
- [x] 盘点所有已有 tracked/untracked 修改，备份实际字节并核对哈希。**已完成**：2026-11-11 备份留在 `research/wip-backup-2026-11-11/`；2026-11-19 逐项重算 SHA-256，12 条字节不变、5 条由 `27757966` 与 `ec980bc7` 解释，见快照 §3。
- [x] 检查外部来源的未跟踪/忽略资产并分类。**已完成**：重跑 `git status --porcelain --ignored`，按顶层分组归类；`.trellis/ref/` 按既有 [`p0-source-assets.md`](research/p0-source-assets.md) 判为公开可恢复，并回写第 5 节复核补充，见快照 §4。
- [x] 后续在明确候选分支实施。**已完成**：候选分支 `feat/mcu-merge-p1`（base = 已确认集成 HEAD `4882857e`），两次提交只含本批文件；`main` 尖端未动。worktree 方案未采用（计划中为可选）。

只读基线命令，cwd 为 `D:\Users\STM32`：

```powershell
git rev-parse HEAD
git -C D:\Users\mcu rev-parse HEAD
git status --porcelain=v1
git -C D:\Users\mcu status --porcelain=v1
git merge-base --is-ancestor cf161532c823446016a9deb60d31e5263397b7d7 HEAD
git diff --name-status cf161532c823446016a9deb60d31e5263397b7d7 HEAD:mcu
```

每个命令分别检查退出码；`merge-base --is-ancestor` 的 0 表示祖先成立，1 表示不成立。

## 3. P1：规范与任务继续可用

- [x] 根 README/STRUCTURE 的入口与边界。**已完成（以核对为主）**：B5 后根书稿已合一，`README.md`、`STRUCTURE.md` 写明 `mcu/` 保留固件与任务历史、不再有独立书稿站点；本轮未改这两份，改为修正仍按旧结构写的 `mcu/README.md`（见「P1 追加」）。
- [x] 根 AGENTS 路由。**已完成（以核对为主）**：已路由到 `mcu/AGENTS.md`、`mcu/.trellis/spec/index.md`、`mcu/.trellis/workflow.md`、`mcu/.trellis/tasks/` 与本计划三件套，并注明旧书稿/站点/脚本已退役；无规则正文复制。
- [x] 从 `mcu/` 运行 Trellis context 并逐项解析。**已完成**：`get_context.py` 退出码 0，23 个活动任务、8 层 spec、journal 指针正常；`--mode packages` 报 `Single-repo project`；23 个任务目录均可解析 `task.json`。
- [x] 历史绝对路径分类。**已完成**：`D:/Users/mcu` 命中 3 个文件，均为历史记录中的操作叙述，来源目录仍在；无用于执行需适配者。
- [x] 记录历史任务状态前后差异。**已完成**：活动任务 `planning` 9 / `in_progress` 14；唯一状态变化为 `11-07-historical-spec-closure` 的 `planning → in_progress`（`ec980bc7`），无归档、无改为通过。

MCU 工作目录命令：

```powershell
python .trellis/scripts/get_context.py
python .trellis/scripts/get_context.py --mode packages
```

回退点：只撤销本批导航和路由变更，不动 `mcu/.trellis/tasks` 既有工作。

### P1 追加（2026-11-19 执行）

本轮在候选分支 `feat/mcu-merge-p1` 提交 `1c305381`、`b6a50290`，修复仍按退役前结构书写的入口文档：

- `mcu/README.md`：改写为来源子树入口（读什么/跑什么、书稿构建在根 `book/`）；历史段落明确标注归档。
- `mcu/CONTRIBUTING.md`：加范围说明——写作标准降为历史参考，现行指向根 `docs/CONTENT_GUIDE.md`；4 条死链改为行内代码。
- 根 `CONTRIBUTING.md`：`stm32-book/tests` → `book/tests`，`docs/NN-xxx.md` → `docs/<分卷>/NN-xxx.md`。
- 证据与适用性判定：`research/execution-snapshot-2026-11-19.md`。

**门禁覆盖缺口（2026-11-19 实测，已处置）**：当时推 `feat/mcu-merge-p1` 后 `gh api …/actions/runs?head_sha=<sha>` 返回 `total_count = 0`——各工作流 `push` 只挂 `branches: [main]`，`merge-check.yml` 另走 `pull_request`，而 `mcu/**`、`plans/2026-11-11-mcu-merge/**`、根 `CONTRIBUTING.md` 都不在任何 `paths` 过滤器内，即本批改动无 CI 覆盖。获明确指令后已扩 `merge-check.yml` 的两个触发块并实测到 `pull_request` 触发，全过程见[执行快照](research/execution-snapshot-2026-11-19.md) §8。

同一轮补了一道更根本的门：`mcu/README.md`、`mcu/CONTRIBUTING.md`、`mcu/AGENTS.md` 现已进 `book/checks.py` 的 `ENTRY_DOCS`。此前这三份不在任何链接扫描范围内——那正是 `mcu/README.md` 攒下 60+ 条死链、而 `book.checks --check` 仍印 `checks passed` 的原因（`23ca1fcb`）。

## 4. P2：站点路径与仓库身份

> **状态：已被 B5 取代，不执行。** 本阶段依赖的 `mcu/docs/`、`mcu/scripts/`、`mcu/package*.json`、`mcu/.github/workflows/` 已在 B5（`44c0fdb0`）整树退役，MCU 站点不复存在。逐条判定见[执行快照](research/execution-snapshot-2026-11-19.md) §5；其中「审查 CITATION 身份」只做到一半：`27757966` 把仓库身份换成了新仓，但指向 `mcu/mcu-book` 的 `identifiers`、指向 `/STM32/mcu/` 的 `url`、`1.0.0` 版号与「88 章」摘要都留了下来，直到 `23ca1fcb` 才对上真源并加上回归测试（见 [P4 验收记录](research/p4-acceptance-2026-11-19.md) AC7）。「旧 `/mcu/` 字符串分类」以文档核对形式在快照 §5/§6 完成。下列复选框按原样保留，代表**当时计划**而非待办。

- [ ] 新建共享站点身份配置，替换运行时代码中分散的 base/host/repository 字面量。
- [ ] 修复 Playwright 的 baseURL/webServer URL、robots、主题仓库按钮、自链校验、导读和下载生成路径。
- [ ] 同步审查 manifest repository、CITATION repository-code/url/identifiers 和新输出的来源链接。
- [ ] 分类检查所有 `/mcu/` 与旧 GitHub 仓库字符串：运行时、新输出、兼容测试、负例、历史记录。保存分类结果，不做无条件全局替换。
- [ ] 调整 pages/search/seo/docs-check 等预期受 base 影响的测试；新增新 base 正例、旧 base 负例、GitHub 自链前缀映射回归。
- [ ] 按 lock 安装 MCU 依赖，记录 Node/npm/Python 版本。不得为解决路径问题顺带升级依赖或重写 lock。

cwd 为 `D:\Users\STM32\mcu`，依次执行且任一失败即处理：

```powershell
npm ci
npm test
npm run quality
npx playwright install chromium
npm run test:browser
```

`quality` 已包含构建、站点检查和部分测试，不必在其成功后重复运行同一集合；`npm test` 可作为前置快速反馈。依赖安装与浏览器下载的环境权限按实际执行环境处理。

回退点：该批身份配置、消费者和测试一起回退，不能只回退 base 常量。

## 5. P3：工作流与实际部署结构

> **状态：已被 B5 取代，不执行。** Pages 组装已由根 `scripts/assemble-site.mjs` + 131 条旧链存根实现，且 CI 断言 `/mcu/` 下只能是存根页；`mcu/` 子目录不再承载站点。触发矩阵的**当前事实**已在本轮实测记录（见 §3「P1 追加」的门禁覆盖缺口），与原计划设想的 MCU staging 无关。下列复选框按原样保留，代表**当时计划**而非待办。

- [ ] 实现 Pages staging 组装：上传根包含 `mcu/` 子目录；根入口根据部署前调查保留或生成。
- [ ] 修改部署 workflow，检查最终 staging 里的 MCU 子目录，并上传整个 staging 根。
- [ ] 为组装脚本增加有实际意义的回归：缺 MCU index 必须失败、根入口不能被覆盖、资源必须在 `mcu/` 下。
- [ ] 按真实挂载 `/STM32/` 提供 staging 目录，浏览器检查 `/STM32/mcu/` 及至少一个章节深链；检查 CSS/JS/图片请求、搜索、导读、book/downloads。
- [ ] 审查 Action 输入路径、缓存键、artifact 名、工作目录、reuse workflow 引用、并发组和权限。
- [ ] 记录触发矩阵：只改根、只改 MCU、改共享入口/组装、混合改动、手动发布。各类必须触发所需检查，未涉及部分的跳过须由汇总规则解释。
- [ ] 核实远程 required checks 与 Pages 配置，解决路径过滤导致的等待或门禁遗漏。此处是未来核实项，本轮没有验证远程状态。

组装后的现有检查命令（cwd 为 `mcu/`，staging 名称按设计）：

```powershell
node scripts/pages-check.mjs --dist ../.temp/pages-site/mcu
node scripts/search-check.mjs --dist ../.temp/pages-site/mcu
```

挂载冒烟与 staging 组装脚本尚待实现，不能把上述两个命令通过等同于整个部署结构已通过。

回退点：保留旧部署 artifact 和工作流；未通过 staging 检查不进入发布。

## 6. P4：最终验证与证据

> **状态：部分适用，未放行。** 根书门仍在跑；MCU 侧 quality/browser/书籍门随树退役而不复存在，固件门以 `mcu/code/` 为范围。P4 验收记录已产出：[`research/p4-acceptance-2026-11-19.md`](research/p4-acceptance-2026-11-19.md)——AC1/AC6 通过，AC2 由 B5 取代，AC7 部分通过（元数据已修，许可范围待定），AC3/AC5 未通过，AC4/AC8 未验证。按 AC5 与 AC3 的现状，候选分支不满足合并条件。

以下两组命令是 **B5 之前**的口径，路径已不存在（`git ls-files stm32-book` = 0，`mcu/mcu-book` 已整树删除）。保留原文供对照；现行等价物见每组下方。

<details><summary>历史命令（stm32-book / mcu-book，已退役）</summary>

```powershell
python tools/slop_lint.py
python tools/check_assets.py
python -m unittest discover stm32-book/tests -v
python stm32-book/build_html.py --check
```


MCU 书籍命令，cwd 为 `mcu/`：

```powershell
python -m unittest discover mcu-book/tests -v
python mcu-book/build_html.py --check
python mcu-book/build_html.py --pdf
python mcu-book/build_print.py --html mcu-book/dist/mcu-deep-book.html
python mcu-book/check_pdf.py
python mcu-book/publish_downloads.py --out-dir mcu-book/dist/downloads
python mcu-book/publish_downloads.py --verify mcu-book/dist/downloads
```

</details>

现行 `book.yml` 覆盖：合并书稿的检查、渲染契约、印刷 HTML/PDF/EPUB 与产物体量断言（见该工作流 `jobs.book`）。它**不含**英文书门，也没有 SPL 构建——这两项在 B5 后没有对应工作流，属 AC5 的未通过项。

**现行等价物**（2026-11-19 实测，见 [`research/p4-acceptance-2026-11-19.md`](research/p4-acceptance-2026-11-19.md)）：

```bash
python tools/slop_lint.py docs/v0-foundations/*.md docs/v1-drivers/*.md docs/v2-reliability/*.md docs/v3-rtos/*.md docs/v4-platforms/*.md docs/v5-motion/*.md docs/v6-labs-projects/*.md docs/v7-delivery/*.md docs/appendix/*.md
python tools/check_assets.py
python -m unittest discover book/tests
python -m book.build_html --check
node --test scripts/tests/*.test.mjs
```

MCU 书籍门已随 B5 取消（`mcu/mcu-book` 不存在）；离线整书产物只剩来源仓归档中的 `mcu-book/dist/`，见快照 §4。

- [ ] MCU quality/browser 的最终结果对应候选提交；内容或配置再变化时重跑受影响门。
- [ ] CI 的动画审计、Ruff、ARM-host `firmware:check`、ESP32 normal/faults 矩阵和下载包 GNU 哈希检查全部留证。
- [ ] 两书产物命名、版本、哈希、许可/出处和根导航审查通过。
- [ ] 检查所有阶段是否新增未解释的工作区修改，确认旧任务文档与外部来源未被意外修改。
- [ ] 产出验收记录：每个 AC 的状态、commit SHA、执行环境、命令/CI run ID、退出码、artifact SHA、日志位置及剩余问题。

CPU/工具链缺失、浏览器未安装、硬件未接入分别记 `BLOCKED`/`UNVERIFIED`；编译不能代替真实上板证据。合并本身不追加硬件实测要求，但必须保持原项目的验证状态。

## 7. P5：发布与关闭

> **状态：待发布指令，未合入。** 候选分支已推送（`feat/mcu-merge-p1`），PR #140 以**草稿**形式存在（用于实测 `pull_request.paths` 触发并承载 P4 验收记录）；未合入、未动 Pages。P4 判定见 [`research/p4-acceptance-2026-11-19.md`](research/p4-acceptance-2026-11-19.md)：AC1/AC6 通过，AC2 由 B5 取代，AC7 部分通过，AC3/AC5 未通过，AC4/AC8 未验证。

- [ ] 收到后续发布指令后，才执行 PR 合入/推送/Pages 切换等远程动作；计划阶段不操作远程。
- [ ] 发布前记录新旧 Pages 的真实 URL、旧 artifact、对应 SHA、required checks 和来源仓库维护状态。
- [ ] 只使用已验证候选提交的 artifact；若主线合入结果生成新 SHA，核对最终树并完成必要 CI。
- [ ] 发布后回读首页、深链、搜索、动画、导读、书籍下载和根入口；下载文件哈希与候选产物相符。
- [ ] 再处理旧站提示或重定向，明确旧仓是否保留只读；本地来源目录默认保留。
- [ ] 失败时重新部署旧 artifact 并回读；修复候选后再发布。
- [ ] 更新最终验收状态与维护文档，达到 AC8 后才关闭合并任务。

## 8. 建议变更批次

1. `docs(merge): define dual-book ownership and spec routing` — P1。
2. `fix(mcu): align site paths and repository metadata` — P2。
3. `fix(ci): assemble MCU site under STM32 Pages prefix` — P3。
4. `docs(merge): record integration acceptance and migration status` — P4/P5 证据。

已有未提交文件不自动纳入任何批次；先确认其归属和本任务依赖。以上是提交边界建议，不是已经创建的提交。

# 分阶段实施计划

状态：全部为待执行项；已完成的历史导入只作为基线。参见 [需求](prd.md)、[设计](design.md) 与 [调查](research/findings.md)。

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

- [ ] 重新读取两个 HEAD 和分支；与 `research/baseline.json` 比较。若已变化，新增执行快照，保留本次规划快照。
- [ ] 验证来源 SHA 为目标祖先，审查来源 tree → `HEAD:mcu` 的 10 路径迁移差异。
- [ ] 盘点所有已有 tracked/untracked 修改，备份实际字节并核对哈希；不只保存 Git patch，因为 patch 不包含未跟踪文件。
- [ ] 检查外部来源的未跟踪/忽略资产，分类为可再生、可由已发布制品恢复、不可再生。重点看视频母版、PDF、字体、参考源码和硬件证据。依赖目录不得作为资产整树导入。
- [ ] 后续在明确候选分支实施；如使用新 worktree，按清单带入确实需要的已有修改，不能把原工作区留存内容误认成已在候选分支。

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

- [ ] 根 README/STRUCTURE 明确两个入口、两套正文和示例边界。
- [ ] 根 AGENTS 路由到原书 spec、MCU AGENTS/spec 和本合并计划；不复制规则正文。
- [ ] 从 `mcu/` 运行 Trellis context，逐项解析活动任务 jsonl 文件路径；区分 Git 根和 MCU 项目根。
- [ ] 输出历史绝对路径分类：仍用于执行的需适配，历史记录保留；校验 parent/children 和会话指针。
- [ ] 记录历史任务状态前后差异；本合并不得自动把任何历史任务归档或改为通过。

MCU 工作目录命令：

```powershell
python .trellis/scripts/get_context.py
python .trellis/scripts/get_context.py --mode packages
```

回退点：只撤销本批导航和路由变更，不动 `mcu/.trellis/tasks` 既有工作。

## 4. P2：站点路径与仓库身份

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

根 STM32 命令，cwd 为仓库根：

```powershell
python tools/slop_lint.py
python tools/check_assets.py
python -m unittest discover stm32-book/tests -v
python stm32-book/build_html.py --check
```

根 `book.yml` 还须在 CI 覆盖 SPL 构建、中英 PDF 生成及版式审计；以上本地命令不是替代。

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

- [ ] MCU quality/browser 的最终结果对应候选提交；内容或配置再变化时重跑受影响门。
- [ ] CI 的动画审计、Ruff、ARM-host `firmware:check`、ESP32 normal/faults 矩阵和下载包 GNU 哈希检查全部留证。
- [ ] 两书产物命名、版本、哈希、许可/出处和根导航审查通过。
- [ ] 检查所有阶段是否新增未解释的工作区修改，确认旧任务文档与外部来源未被意外修改。
- [ ] 产出验收记录：每个 AC 的状态、commit SHA、执行环境、命令/CI run ID、退出码、artifact SHA、日志位置及剩余问题。

CPU/工具链缺失、浏览器未安装、硬件未接入分别记 `BLOCKED`/`UNVERIFIED`；编译不能代替真实上板证据。合并本身不追加硬件实测要求，但必须保持原项目的验证状态。

## 7. P5：发布与关闭

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

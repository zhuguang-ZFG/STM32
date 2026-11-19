# P0 执行快照：基线漂移与适用性核对（2026-11-19）

规划快照保留在 [`baseline.json`](baseline.json)（2026-11-11，target 分支 `feat/mcu-subtree-merge`）。本文件是**执行前**的新快照，记录与规划快照的差异、以及 Nov-11 计划在 Nov-12 合并决定之后的适用性。

执行环境：`D:\Users\STM32`，Git 根；来源 `D:\Users\mcu`。命令与退出码见下，均在本机实际执行。

## 1. 两个 HEAD 与分支

| 项 | 规划快照（2026-11-11） | 本次（2026-11-19） |
| --- | --- | --- |
| 目标 | `feat/mcu-subtree-merge` @ `92fc917c` | `main` @ `4882857e` |
| 来源 | `cf161532` @ `D:\Users\mcu` | `cf161532`（未变） |
| 目标 `mcu/` tree | `93e40d58` | `77749331` |

来源侧工作区只有 `?? .perch/` 一条未跟踪项，与规划期一致。

## 2. 祖先与迁移差异

```text
git merge-base --is-ancestor cf161532c823446016a9deb60d31e5263397b7d7 HEAD   → exit 0（仍是祖先）
git diff --name-status cf161532 HEAD:mcu                                     → 1580 条
```

规划期记录的迁移差异是 **10 条**（4 个 workflow 删除 + README/config/scripts 等修改）。现在 1580 条（848 A / 692 D / 40 M），**不是导入遗漏**，而是两段已记录的历史：

1. **B5 删除旧树**（`44c0fdb0`，2026-11-14）：`mcu/{docs,mcu-book,scripts,tests,package.json,package-lock.json,playwright.config.mjs,.github/workflows/*}` 整树删除，共 692 条。记录见 [`plans/2026-11-12-merged-book/README.md`](../../2026-11-12-merged-book/README.md) 第 44 行（B5 结束状态）：两书正文合并、旧树删除、`mcu-book.yml`/`mcu-quality.yml`/`mcu-links.yml`/`mcu-deploy.yml`/`release-fetch.yml` 退役、`mcu/` 只保留 `code/`、`.trellis/` 与仓库元文件。
2. **导入后的正常演进**：`video/` 新增 832 个跟踪文件、`.trellis/` 新增 16 个（W1/W2 证据、任务文档入库）。

验证删除是决定而非事故：`git log --diff-filter=A 44c0fdb0..HEAD -- mcu/docs mcu/mcu-book mcu/scripts` 为空（未重新加入）；`STRUCTURE.md` 第 9/14/15/36 行已是同一口径（「`mcu/` 保留来源固件与任务历史，不再有独立书稿站点」「其下 `mcu/` 只有旧链跳转存根」）。

## 3. 规划期受保护条目：字节核对

对 `baseline.json` 的 17 条逐项算 SHA-256：

| 结果 | 条目 | 说明 |
| --- | --- | --- |
| SAME 12 条 | 两个任务的 `check.jsonl`/`implement.jsonl`、`prd.md`、`task-cards.md`、`design.md`、`baseline-drift-audit.md`、`review-handoff.md`、`w1-language-diffs.md`、`wave0-evidence.md` | 字节未变；7 个原未跟踪文档现已入库且哈希一致 |
| DIFF 1 条 | `mcu/CITATION.cff` | 由 `27757966`（站点身份对齐，正是 P2 的既定动作）修改 |
| DIFF 4 条 | `11-07-historical-spec-closure` 的 `task.json`、`research/task-ledger.json`、`implement.md`、`research/w1-evidence.md` | 由 `ec980bc7`（记录 W1 证据与 W2 调研）修改 |

状态字段核对：`task.json` 的 `status` 由 `planning` 改为 `in_progress`，**没有**被改为完成或归档，符合「不得自动把历史任务归档或改为通过」。

## 4. 外部来源的未跟踪/忽略资产分类

`git -C D:\Users\mcu status --porcelain --ignored` 的 116 条按顶层归组：`code` 55、`video` 14、`mcu-book` 6、`.trellis` 5、`docs` 4、`scripts` 2，其余为缓存/虚拟环境。

| 类别 | 代表 | 可再生性 | 处置 |
| --- | --- | --- | --- |
| 参考资料镜像 | `.trellis/ref/`（105 MB）：8 个厂商 PDF（`st-docs/rm0090.pdf`、`st-docs/stm32f407vg-ds.pdf`、`gd32/` 5 个、`f407-ds.pdf`）+ 41 MB `gd32/`、18 MB `freertos-v11/`、10 MB `rt-thread/`、1.3 MB `cmsis/` + 74 个顶层脚本/日志 | 厂商文档与上游源码**公开可恢复**（版本需重新核对）；`capstone-*.log` 等本机产物属一次性记录 | 只留本地，**不得整树导入**；与 [`p0-source-assets.md`](p0-source-assets.md) 第 30/33/42 行的口径一致 |
| 视频母版与配音 | `video/jobs/*/inputs/narration/master.wav`、`master-chunks/` | 可由 TTS/工程重跑，成本高 | 不导入；需要时按 job 重跑 |
| 书籍与站点产物 | `mcu-book/dist/`（`mcu-deep-book.pdf` 29.3 MB、`-print.pdf` 17.4 MB、`mcu-deep-book.html` 10.8 MB）、`docs/.vitepress/{dist,cache,data}` | 可由来源仓源码重建 | 不导入；重建入口在来源仓 |
| 依赖与缓存 | `node_modules/`、`video/pydeps`、`venv-handdraw`、`__pycache__`、`.pytest_cache`、`.ruff_cache`、`.temp` | 可再生 | 禁止导入 |

来源仓 `mcu-book/dist/` 有实际产物（`mcu-deep-book.pdf` 29.3 MB、`-print.pdf` 17.4 MB、`mcu-deep-book.html` 10.8 MB，2026-11-07 构建）。「唯一可下载副本」是查证后的结论，不是假设：`zhuguang-ZFG/mcu` 无 release；本仓 release（v1.3.1/v1.0.7/v1.0.0）只带 `stm32-practical-book*` 四个文件，无 MCU 整书；线上 `/STM32/mcu/book/`、`/STM32/mcu/downloads/mcu-deep-book.pdf`、根站 `/STM32/book/` 均 **404**；工作区内无 `mcu-book/` 产物（B5 已删除）。

## 5. 对 Nov-11 计划的适用性判定

Nov-11 计划（`implement.md`）成文于 B5 之前。按当前事实逐条判定：

| 原阶段项 | 现状 | 判定 |
| --- | --- | --- |
| P0 基线与保护 | 本文件已完成 | 适用，已完成 |
| P0 「审查 10 路径迁移差异」 | 差异已扩到 1580 条，全部为已记录事件 | 适用，已完成（结论见 §2） |
| P1 根 README/STRUCTURE 双书入口 | `STRUCTURE.md`、根 `AGENTS.md` 已是 B5 后口径 | 部分适用：`mcu/README.md` 当时仍按旧结构写，本轮已改写（见 §6 与 §7） |
| P1 Trellis 上下文与历史路径 | `mcu/.trellis/` 完整保留，活动任务可解析 | 适用，待执行 |
| P2 站点路径统一、Playwright baseURL、robots、仓库按钮 | 相关树（`mcu/docs`、`mcu/scripts`、`package.json`）已删除，工作流已退役 | **已被 B5 取代**，不执行 |
| P2 `mcu/` 与旧 GitHub 仓库字符串分类 | 目标只剩 `mcu/code`、`.trellis`、`README`、`video` | 降级为文档核对 |
| P3 Pages staging 组装 `mcu/` 子目录 | 已由 `scripts/assemble-site.mjs` + 131 存根实现，且 CI 断言 `/mcu/` 下只能是存根 | **已被 B5 取代**，不执行 |
| P3 挂载冒烟 `/STM32/mcu/` 深链 | 已在线（存根 → 根书页） | 已由站点冒烟覆盖 |
| P4 根书门 + MCU quality/browser/书籍/固件门 | 根书门在跑；MCU 侧代码门随树删除而不复存在 | 部分适用：以根书门 + `mcu/code` 固件门为准 |
| P5 发布与关闭 | 未获发布指令 | 不执行 |

## 6. 本次发现的活缺陷（已在 §7 修复）

改写前，`mcu/README.md`（受跟踪，与工作区一致）按删除前的结构描述，实测如下：

| 断言 | 实测 |
| --- | --- |
| 徽章指向 `mcu-deploy.yml` / `mcu-quality.yml` | 两个工作流已退役，仓库内不存在 |
| 「整书离线版随站点发布在 `/mcu/book/`」 | `https://zhuguang-zfg.github.io/STM32/mcu/book/mcu-deep-book.html` → **404** |
| 「`/downloads/` 的 PDF 为可下载真字节」 | `/STM32/mcu/downloads/mcu-deep-book.pdf` → **404** |
| 「所有 npm/agent 命令在本目录（`mcu/`）内运行」 | `mcu/package.json` 已删除，无 npm 工程 |
| 正文与 60+ 条 `docs/…`、`mcu-book/…`、`.trellis/spec/docs-site/…` 链接 | 目标路径已删除 |

对照：131 条旧链存根本身工作正常（`/STM32/mcu/stm32/03-gpio.html` → 200，canonical 指向 `/STM32/v1-drivers/09-gpio.html`）。

处置（已完成，见 §7）：按 P1 改写 `mcu/README.md` 的路由与入口表述，使其与 B5 后的实际结构一致；不改章节正文（章节已迁入根书）。

## 7. P1 核对结果

| P1 项 | 结果 |
| --- | --- |
| 根 README/STRUCTURE 双入口与边界 | 已是 B5 后口径：`README.md` 第 98/104/108–112/114 行与 `STRUCTURE.md` 第 9/13–15/36/50/53 行都写明「`mcu/` 保留固件与任务历史，不再有独立书稿站点」「其下 `mcu/` 只有旧链跳转存根」，无需改动 |
| 根 AGENTS 路由 | 已路由到 `mcu/AGENTS.md`、`mcu/.trellis/spec/index.md`、`mcu/.trellis/workflow.md`、`mcu/.trellis/tasks/`、本合并计划三件套；第 10 行已注明「旧书稿/站点/脚本与书籍门已随合并退役」 |
| 从 `mcu/` 运行 Trellis context | `python .trellis/scripts/get_context.py` → exit 0，列出 23 个活动任务、8 层 spec（`book, docs-site, firmware-common, firmware-esp32, firmware-gd32, firmware-rtos, firmware-stm32, video`）、journal 指针 `.trellis/workspace/zhuguang-ZFG/journal-1.md`（1396/2000 行）；`--mode packages` → `Single-repo project`，exit 0 |
| 活动任务路径逐项解析 | 23 个任务目录均有可解析 `task.json`；4 个无 `task.json` 的目录（`10-06-b3-linker-script`、`10-06-gd32-tracks`、`10-26-chapter-art`、`11-02-skill-remaster`）不在活动列表内，属历史/草稿目录，未改动 |
| 历史绝对路径分类 | `grep -rl "D:/Users/mcu"` 命中 3 个文件，均为历史记录里的操作叙述（如 `11-07-book-depth-handdraw/research/delivery-closure.md` 第 19 行提到为 `D:/Users/mcu` 建 baseline），指向的来源目录仍存在，无需适配 |
| 任务状态差异 | 活动任务状态分布 `planning` 9 / `in_progress` 14；无任何任务被改为完成或归档。唯一状态变化是 `11-07-historical-spec-closure` 的 `planning → in_progress`（`ec980bc7`），属如实推进 |

### P1 顺带修掉的入口文档缺陷

| 文件 | 缺陷 | 处置 |
| --- | --- | --- |
| `mcu/README.md` | 按退役前结构写：徽章指向已退役的 `mcu-deploy.yml`/`mcu-quality.yml`；声称 `/mcu/book/`、`/mcu/downloads/` 提供真字节（实测 404）；60+ 条 `docs/…`、`mcu-book/…` 链接失效；要求在本目录跑 npm | 重写为来源子树的现行说明（读什么/跑什么、书稿构建在根 `book/`），历史段落明确标注归档并保留原始写作口径 |
| `mcu/CONTRIBUTING.md` | 8 条命令引用已退役的 `npm run …`、`scripts/local-gates.*`、`mcu-book/*`、`docs/.vitepress/config.mts` | 加范围说明：四件套/风格/动画等写作标准**降为历史参考**，现行写作要求指向根 `docs/CONTENT_GUIDE.md`（「教学合同 + 功能块」体系）；路径与命令改在 Git 根执行并给出根入口 |
| `CONTRIBUTING.md`（根） | §三 第 4 条让贡献者跑 `stm32-book/tests` 与 `stm32-book/build_html.py`，该目录已不被跟踪（`git ls-files stm32-book` = 0） | 改为 `book/tests` + `python -m book.build_html --check` + `make book-check`，并补站点侧与现行分卷路径说明 |

验证：`python tools/slop_lint.py` 三份全干净；`python tools/check_assets.py` → `public assets: 543 checked; PASS`、`merged-book assets: PASS`；`python -m unittest discover book/tests` → 104 OK；`python -m book.build_html --check` → `built 53 pages, 0 planned chapters missing`。

相对链接的实测口径分两类：

- **现行段落**（`mcu/README.md` 的「现在读什么、跑什么」「书稿构建在哪里」、根 `CONTRIBUTING.md` 的改动处、本文件全部链接）：逐条实测存在，0 死链。
- **历史段落**（`mcu/CONTRIBUTING.md` 正文）：4 条指向已删除树的引用（`docs/c/06-abi-stack.md`、`docs/stm32/00-env.md`、`docs/lab/e01-blink.md`、`docs/lab/template.md`）已从可点链接改为行内代码文本，只作历史记录、不提供跳转。文件顶部范围说明同时声明写作标准降为历史参考、现行要求指向根 `docs/CONTENT_GUIDE.md`。
- 检查脚本会再报一条 `/anim/xxx.svg`：该处在反引号包裹的行内代码里，是说明图片语法的示例文本，不构成可点链接（扫描器按正则匹配到它，属误报）。

## 8. 门禁覆盖缺口（2026-11-19 实测）

候选分支 `feat/mcu-merge-p1` 推送后 `gh api repos/zhuguang-ZFG/STM32/actions/runs?head_sha=<sha>` 返回 `total_count = 0`。下表是六份工作流的**全量**触发条件（逐文件读 `on:` 块，不靠 `grep -A3`）：

| 工作流 | 触发条件（全量） | 本批改动是否命中 |
| --- | --- | --- |
| `book.yml` | `push`(main + paths)、`pull_request`(paths)、`workflow_dispatch`；paths：`docs/**`、`book/**`、`scripts/**`、`plans/2026-11-12-merged-book/**`、`tools/slop_lint.py`、自身 | 否 |
| `merge-check.yml` | `pull_request`(paths)、`push`(main + paths)、`workflow_dispatch`；paths：`book/**`、`docs/**`、`plans/2026-11-12-merged-book/**`、`plans/2026-11-11-motor-control/**`、`scripts/legacy-redirects.mjs`、`scripts/tests/**`、`tools/slop_lint.py` | 否 |
| `site.yml` | `push`(main + paths)、`pull_request`(paths)；paths：`docs/**`（排除 `docs/superpowers/**`）、`scripts/**`、`plans/2026-11-12-merged-book/mapping.json`、`package*.json`、自身 | 否 |
| `deploy.yml` | `push`(main + paths)、`workflow_dispatch`；paths 同 `site.yml` | 否（无 PR 触发） |
| `links.yml` | `schedule`（`17 3 * * 1`）、`workflow_dispatch`、`pull_request`(paths)；paths：`docs/**/*.md`、`scripts/check-external-links.mjs`、`scripts/external-links-allowlist.json`、`package*.json`、自身 | 否 |
| `motor-control.yml` | `push`(main + paths)、`pull_request`(paths)、`workflow_dispatch`；paths：`examples/motor-dc-speed/**`、自身 | 否 |

两条原因必须分开讲，不能合并成「等 CI」：

1. **推特性分支零运行**：六份工作流里有 `push` 触发器的都是 `branches: [main]`，没有任何一份监听特性分支。
2. **开 PR 同样零运行**：五份带 `pull_request` 的工作流（`book`、`merge-check`、`site`、`links`、`motor-control`）的 `paths` 都不包含本批路径。

本批实际改动为 `mcu/README.md`、`mcu/CONTRIBUTING.md`、根 `CONTRIBUTING.md`、`plans/2026-11-11-mcu-merge/**`。逐条对不上：

- `mcu/**`、根 `CONTRIBUTING.md` 不在任何 `paths` 列表内。
- `plans/2026-11-11-mcu-merge/**` 同样不在；`merge-check` 与 `book` 列出的 `plans/2026-11-12-merged-book/**`、`merge-check` 的 `plans/2026-11-11-motor-control/**` 是另外两个计划目录。
- `links.yml` 的 `docs/**/*.md` 覆盖不到根 `CONTRIBUTING.md`，也覆盖不到 `mcu/`。

因此本批的验证证据只有本地门：`tools/slop_lint.py`、`tools/check_assets.py`、`python -m book.build_html --check`、`python -m unittest discover -s book/tests`。扩展 `paths` 属 CI 策略变更，需明确指令后才动；本轮未修改任何工作流文件。

### 手动补跑（2026-11-19）

`paths` 不会自动触发，但 `merge-check.yml` 与 `book.yml` 都带 `workflow_dispatch`，因此按分支手动补跑，让这两道门在本批提交上真实留证：

| 工作流 | run ID | 触发 | 覆盖 SHA | 结果 |
| --- | --- | --- | --- | --- |
| Merge Check | `44462385575` | `workflow_dispatch` | `df187f3d` | success（含 `Run book checks` 与 `Run script tests` 两步均 success） |
| Book CI | `44462518910` | `workflow_dispatch` | `df187f3d` | success（`book` 作业含 `Build print HTML` / `Build PDF` / `Build EPUB` / 产物体量断言全部 success；`scripts` 作业 success） |

本地等价复跑（同一批命令，同一台机器）：`book.manifest --check`、`book.mapping --check`、`unittest discover book/tests`（OK）、`book.checks --check`（checks passed）、`slop_lint` 全章节（干净）、`book.build_html --check`（53 页）、`node --test scripts/tests/*.test.mjs`（32 通过 / 0 失败）。

两道门都在 `df187f3d` 上绿。此后写回本节会推进分支尖端，因此把「新尖端是否仍被覆盖」限定到**唯一变更路径**来核：

- 相对 `df187f3d`，后续改变只有 `plans/2026-11-11-mcu-merge/research/execution-snapshot-2026-11-19.md` 一个文件。
- 该文件不被任何门步骤读取。门实际从 `plans/` 读取的路径只有两处：`book/mapping.py:12` 的 `plans/2026-11-12-merged-book/mapping.json`、`book/mapping.py:68` 的 `plans/2026-11-11-motor-control/chapters-draft`；测试侧只有 `scripts/tests/legacy-redirects.test.mjs:11` 读同一个 `mapping.json`，`book/tests/test_figure_sources.py:10` 排除的是 `docs/superpowers/plans/`。在 `book/`、`scripts/`、`tools/` 全树 grep `2026-11-11-mcu-merge` 无命中。

所以这条记录的写入不改变任何门的输入；`df187f3d` 的绿灯结果对后续尖端同样成立。这不等于缺口消失：下次改 `mcu/**`、本计划目录或根 `CONTRIBUTING.md` 依旧不会自动触发，仍要手动 dispatch 或先扩 `paths`。另：`main` 未设分支保护、无 required checks，「绿」不构成合入阻塞，只是证据。


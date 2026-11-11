# 设计：全部历史 spec 统筹收口

## 1. 目的与边界

本任务只承担跨 22 项历史任务的账本、证据分级、依赖路由和授权边界，不拥有任何生产文件。范围是创建时 22 个未归档 `task.json`（见 `research/task-ledger.json`），不含本任务自身。原 PRD、`task.json` 状态和父子关系在本任务中保持只读。

本任务的“完成”只表示规划与只读核验产物齐备，**不表示 22 项历史交付已完成**。生产正文/图/代码、测试/runner/CI/policy、归档/提交、平台发布/删除/写入、串口烧录/复位均留在原任务，按 `research/dependencies-and-gates.md` 的授权矩阵逐项放行。

## 2. 真源与账本

| 文件 | 角色 | 维护规则 |
|---|---|---|
| `research/task-ledger.json` | 22 项机器账：原锚点、观测、未满足 AC、下一动作、完成检查、依赖、权限门 | 以创建时快照为基线；执行期只追加当前证据，不改写原 PRD/状态 |
| `research/task-cards.md` | 同上的人工收口卡 | 与 ledger 同步；不新增第 23 项 |
| `research/dependencies-and-gates.md` | 依赖顺序、唯一实施归属、合同冲突、授权矩阵 | 冲突未决时不自动选边 |
| `research/artifact-checks.json` | 36 母版 hash、书/Job 身份、EPUB 缺失、prose 候选同一性 | 只证明字节同一性，不证明视觉/听感/线上接受 |
| `research/turn-baseline.json` | 22 任务/122 文件 hash、214 验证输入、101 书稿源、42 用户文件、7 源契约 | 作为“未授权改动”对照基线 |

当前复核（2026-11-11）：22 项均已有 `prd.md`、`design.md`、`implement.md` 与真实 context 条目；唯一 `task.py validate` 失败是 `10-28-social-video-ai-tools` 两处旧 skill 路径，已在规划期替换为现存 job 产物。该修复只改 context 引用，不改原 PRD、状态或生产文件。

## 3. 证据分级

| 级 | 证据 | 能证明 | 不能证明 |
|---|---|---|---|
| E0 | 文件存在、目录结构 | 产物路径存在 | 内容正确、可构建、被接受 |
| E1 | 字节同一/hash | 与留存校验值一致 | 视觉/听感/线上状态 |
| E2 | 历史记录、勾选、状态、旧日志 | 当时有人记录过 | 当前仍成立 |
| E3 | 本轮可复现的窄检查（命令/构建/截图/ffprobe） | 当前可观察行为 | 读者接受、硬件真实、平台线上 |
| E4 | 用户/读者接受（文字、视觉、听感） | 人类验收决定 | 外部平台或硬件状态 |
| E5 | 硬件实测日志（烧录/复位/串口） | 目标板行为 | 其他板卡或环境 |
| E6 | 平台线上回读（ID/URL/账号） | 当前线上状态 | 未来仍保持、审美接受 |

完成检查必须写明证据级别。E0–E2 不能替代 E3–E6；`status` 和 checkbox 只算 E2。缺检查、跳过或工具缺失必须原样记录为 failed/unverified，不得伪绿。

## 4. 工作流与唯一实施归属

| 工作流 | 唯一执行路由（获批后） | 其他任务保留的独立验收 |
|---|---|---|
| B0–B2 旧通俗化 | 原 B0/B1B2 任务补接受与发布关联证据，不重写 | 原保护、用户解释接受、固定范围发布/PDF |
| B7 四行 WIP | `11-07-language-batch5` 只做文字接受；更深修改由 `book-depth-pilot` 负责 | 四行 outside 不变、strict、白名单发布 |
| 内容深度 | `book-depth-pilot` 一个写者做六章；`book-depth-rollout` 按 23 批每批一个写者 | prose 原保护/抽评、interest 原 6 试点、AI 原六章细节与来源 |
| 封面/EPUB/PDF | `cover-art` 选稿后接入现有 `cover_art`/CSS；`book-production` 负责 EPUB 与章级同一性；`delivery-closure` 只做最终全量构建/包证据 | de-ai 父任务接受、PDF 结构/字体/出血、A4 合同决策 |
| 视频母版 | `video-v2-remaster` 负责 18×2 母版与平台替换准备 | 只读复核、逐集删/发授权独立保留 |
| AI 工具视频 | `social-video-ai-tools` 独立四平台 job 与包 | 文件交付与平台发布分离，不自动重发 |
| 外部平台 | `bili-season-after-unlock` 原 17 条；社媒置顶/声明另核授权 | 平台登录/权益、逐条授权、线上回读 |
| 硬件测量 | `e04-board-measurement` 四臂实测 | 全书 delivery 只引用原日志，不造第二张模型数据表 |
| OSS 增强 | `oss-influence` P1–P4 按批准范围 | 附录位置、P3 章题、测试/CI 单独审阅 |

依赖顺序、冲突登记和授权矩阵以 `research/dependencies-and-gates.md` 为准，本文件不复制第二份。

## 5. 数据流与状态机

每个原任务按以下状态推进，禁止跳级：

```text
recorded → observed → planned → authorized → executed → evidenced → accepted → archived
```

- `recorded`：原 PRD、状态、父子关系（只读）
- `observed`：当前静态产物与历史宣称
- `planned`：prd/design/implement/context 齐备
- `authorized`：用户或指定审阅门给出具体许可
- `executed`：动作真实发生
- `evidenced`：E3–E6 证据落到原任务或指定产物
- `accepted`：原 AC 逐项满足（可含用户接受）
- `archived`：`task.py archive`

本任务只维护账本和跨项路由；`authorized` 之后的执行与证据写入原任务，避免一个任务替另一任务宣称完成。

## 6. 兼容、迁移与合同冲突

- **仓库迁移**：git 根为 `D:/Users/STM32`，`mcu/` 为子树，Trellis 根是 `mcu/`。账本路径全部相对 `mcu/`；从根目录运行命令需加 `mcu/` 前缀，不重写账本路径。根级 CI 的 paths-ignore/lint scope 变化不改变 `mcu/` 内各门语义。
- **外部 skill 缺失**：`sweety-handdraw-video` 在迁移后不再随仓库提供。`10-28` 的“skill 源码零修改”保留为外部证据要求，context 改指现存 `video/jobs/ai4fw/job.json` 与 `review.json`，不伪造本地副本，也不删除原要求。
- **历史口径 vs 当前合同**：88 章/6 附录、11/12 门是历史文字；当前 `mcu-book/manifest.json` 为 94 章/7 附录，`check_pdf` 为 13 门。执行以当前合同为准，原 PRD 不重写；不能把当前多出的章漏掉，也不能用旧门数降低当前门。
- **A4 与 EPUB**：`artifact-checks.json` 的 `epub` 三项均为 false；EPUB 构建器/检查器/npm 入口不存在。不得静默删除 EPUB 承诺，也不得声称两件真书已齐。A4 保留/退役冲突在实施前单独决策，决策前不删除现有产物。
- **旧回滚步骤**：prose 旧 implement 中的 stash/按 HEAD 恢复只适用于历史批次，不得用于当前用户 WIP；只允许本批 before/candidate/final 的 hunk 级回退。
- **D2 权限冲突**：原 PRD 后记与 implement 对提交许可描述不一致；以具体提交范围审阅为准，不从冲突处挑最宽许可。

## 7. 失败、回滚与授权

- 规划产物回滚：按文件恢复本任务 `prd.md`/`design.md`/`implement.md`/jsonl；原任务不动。
- 基线漂移：发现 hash 与 `turn-baseline.json` 不符时先停，记录差异并交审；不覆盖、不重算后自称通过。
- 同类失败两次：记录拒绝假设并换证据；权限失败只请求合法授权，不重试绕过。
- 新增/变更测试、runner、CI、policy：单独 review 后才可使用；不从“统筹所有”推导放行。
- 任何外部发布、删除、合集写入、烧录、复位：逐项具体授权，不批量执行。

## 8. 验收映射

| 验收 | 落点 |
|---|---|
| AC1 无漏项 | `research/task-ledger.json` + `research/task-cards.md`，22 项与任务集合相等 |
| AC2 不缩水/单一归属 | `research/dependencies-and-gates.md`，覆盖 EPUB、OSS P1–P4、18 正片、四平台、E04、101 源 |
| AC3 三文档与真实 context | 22 项文件存在性审计 + 逐项 `task.py validate` |
| AC4 证据分级 | `research/artifact-checks.json`、`turn-baseline.json`、执行期窄检查输出 |
| AC5 保全与权限 | `turn-baseline.json` 的 214/42/101 基线 + `git status` 仅规划文件变化 |
| AC6 计划齐备 | 本文件、`implement.md`、22 项收口卡、依赖/授权计划、验证报告 |

## 9. 非目标

本设计不修改生产正文/图/代码，不补造测试或 operator 基线，不动用户素材，不联系平台发布或删除，不操作串口与板卡，不构建覆盖既有视频或发布 PDF 下载包，不替用户做审美/文字接受决定。

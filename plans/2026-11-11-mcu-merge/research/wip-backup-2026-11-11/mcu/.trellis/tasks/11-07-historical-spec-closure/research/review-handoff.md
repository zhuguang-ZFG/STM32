# 交审清单：执行波次、前置授权与不可自动动作

日期：2026-11-11 · HEAD `92fc917c` · 任务 `11-07-historical-spec-closure`

这是规划层交审，不是 22 项历史交付完成证明。原任务 PRD、状态、父子关系未改；本轮未改生产正文/图/代码。

## 1. 本轮已核验（只读）

| 项 | 方法 | 结果 |
|---|---|---|
| 上下文校验 | `task.py validate` 逐项（22 原任务 + 本任务） | 23/23 PASS |
| context 引用存在性 | 全部任务上下文引用逐条 `os.path.exists` | 277/277 存在，0 缺失 |
| 工作区改动范围 | `git status --short` | 仅 `.trellis` 规划/context 文件；无生产文件改动 |
| 本轮授权写入 | 与 `turn-baseline.json` 对照 | 基线内仅 2 个文件：`10-28` 的 `implement.jsonl`/`check.jsonl`（已批准的 context 修复）；其余改动均为本任务基线外规划文件 |
| 既有窄检查 | `docs-check` 等历史结果仅在 `task-cards.md` 原样记录 | 本轮未重跑全门，不冒充当前通过 |

## 2. 基线漂移（需决策，未覆盖）

对 `turn-baseline.json` 全量重哈希（只读）：

| 基线集 | 总数 | 一致 | 漂移 | 缺失 |
|---|---|---|---|---|
| `taskHashes` | 122 | 62 | 60 | 0 |
| `verification` | 214 | 176 | 34 | 4 |
| `sources` | 101 | 100 | 1 | 0 |
| `user`（42 文件） | 42 | 40 | 2 | 0 |
| `sourceContracts` | 7 | 4 | 3 | 0 |

事实与边界：

- 所有漂移文件在工作区均无未提交改动（`git status` 干净），即漂移存在于 HEAD 内，属创建快照（11-07）与迁移检查点 `92fc917c`（11-11）之间的已提交历史；本轮未新增生产漂移。
- 4 个“缺失”工作流是迁移改名：`.github/workflows/{book,deploy,links,quality}.yml` → 仓库根 `mcu-{book,deploy,links,quality}.yml`（提交 `92fc917c` 重接路径与 lint scope），不是删除。
- 漂移集中在：22 项任务文档/上下文 60、生成与检查脚本及 arch-diagrams 产物 34、`docs/ai/05` 1、`11-02` 用户交付 2、`manifest`/`curriculum`/`vitepress config` 3。
- 按 `design.md` §7：发现基线不符时先停、记录、不覆盖、不自称通过。本文件即记录；**AC5 暂不判为通过**。

待选处理（B 已执行）：用户选择逐项追查。2026-11-11 已完成全量审计，详见 `research/baseline-drift-audit.md`：

- **A 类 73 个**：EOL/编码变体，逐行内容与当前相同（基线按 CRLF 工作区副本哈希）。
- **B 类 10 个**：基线匹配历史提交；当前差异全部归因于迁移重接（`92fc917c`）或 seed→真实 context 补齐。
- **C 类 21 个**：基线内容从未进入提交（18 个为创建期 seed 占位、3 个为未提交变体）；当前文件干净且等于检查点版本（或旧版+已知迁移修正）。
- 结论：漂移不是本轮引入，无未记录的生产改动。**剩余决策**：接受本审计作为 AC5 解释（推荐），或另行批准重建基线。

## 3. 执行波次（获批后）

| 波次 | 入口条件 | 内容 | 出口证据 | 授权 |
|---|---|---|---|---|
| W0 只读证据 | 用户审阅本清单 + 基线决策 | 逐项复核原 PRD 锚点与产物；运行允许的窄检查（animation-markdown、docs-check、prose strict、ffprobe 现有成片） | 当前证据表，逐项标 passed/failed/unverified；不改源文件 | 本轮已有只读授权 |
| W1 已有交付补证/接受 | W0 证据表 | B0/B1B2/B7 保护与 identity、D2 回归与三页 UI、D1/D3/D4 375px 浅深与 reduced-motion | 原 AC 当前证据；未接受项保持未完成 | 用户文字/视觉/听感接受 |
| W2 工艺/工程准备 | 各项具体方案获批 | 封面两构图×两配色隔离预览；EPUB 两章薄切片设计；BMS-Z 门到 AC 矩阵；OSS 47 工程映射缺口 | 设计/矩阵/缺口清单；不实施生产改动 | 封面选择；新增测试/CI 单独 review |
| W3 内容深度 | pilot 方案批准 | pilot 两概念薄切片 → 六章 → 用户接受 ≥2 章 → rollout 23 批（每批 ≤6 文件、一个写者） | 知识卡 accepted、正式图、原门、用户抽评 | 每批范围/事实/图文审阅 |
| W4 外部与硬件 | 逐项具体授权 | 18×2 母版冻结与用户接受 → 逐集平台操作；社媒四平台包；B 站 17 条锁定与第 18 条归属；E04 四臂实测 | E4/E5/E6 证据或明确 blocked | 母版接受；逐集删/发；平台登录；板卡与写入 |
| W5 最终交付 | 内容/图/封面冻结、EPUB 工艺齐 | 唯一全量 HTML/A4/16 开构建 → 当前 13 门 → EPUB3 结构/epubcheck/逐章同一性 → 统一下载包 | PDF+EPUB3 均满足原 AC；94 章同源 | A4 决策；提交/发布另行授权 |

## 4. 每项前置授权（22 项）

“起步”均为只读/准备动作；“不可自动”即使在获批后也须逐项具体授权。

| # | 任务 | 起步（只读/准备） | 必要前提/授权 | 不可自动执行 |
|---|---|---|---|---|
| 01 | bili-season-after-unlock | 只读核查账号 season/new_season；锁定原 17 个 aid/bvid | 平台登录与权益；17/18 范围确认；逐条对话授权 | 建集/join/删除/改简介 |
| 02 | e04-board-measurement | 核 F407 身份、HSI/USART 接线、工具版本 | 板卡/探针/仪器确认；四臂写入授权 | 烧录/复位/串口写/填表 |
| 03 | video-v2-remaster | 只读校验 36 母版、timeline、四平台包 | 母版用户接受；逐集删/发授权；平台认证 | build 覆盖母版；批量删/发 |
| 04 | bmsz-validation-depth | 按当前 CI 建门到 AC 矩阵；复用反向夹具 | 测试/runner/CI 修改单独 review；operator 基线 | 改测试/策略/runner；真实 README 造坏链 |
| 05 | book-production | R1–R10 映射；EPUB 薄切片设计 | A4 保留/退役决策；EPUB 测试/CI review；封面定稿 | 删 A4 路径；悄悄删除 EPUB 承诺 |
| 06 | de-ai-polish | 父任务集成设计，复用两子证据 | 文字/封面分别接受 | 第二轮全文重写；擅自归档 |
| 07 | cover-art | 两构图×两配色隔离预览 | 用户选定；生产接入审阅 | 替换生产 `cover_art`；把 research 图当定稿 |
| 08 | oss-influence | G 地图与原附录 B 对账；47 工程缺口 | 附录位置/数量、P3 章题审阅；新增测试/CI review | 新增工程实施；改附录真源 |
| 09 | prose-polish | 24 批路由与原保护对账；保留 before/candidate/final | 逐批文字接受；技术纠错单独 review | 旧 stash/reset 回滚；刷口癖阈值 |
| 10 | ai-dev-deepen | R1–R5 映射六章/来源/导航 | 用户图文详细度接受 | 重建六章冒充新完成；改外部来源 |
| 11 | book-interest-polish | 6 试点逐项评价归档 | 2 章抽评；增量边界调整审阅 | 静默扩大 12% 预算；替换试点范围 |
| 12 | social-video-ai-tools | job/四平台包与当前 hash 对账 | 常驻 schema 修订审阅；置顶/声明授权 | 重渲/重发；置顶评论/原创声明 |
| 13 | animation-d2-closure | 保留现有修复；核回归 review | 新增测试用户 review；提交范围核定 | 再发 PR；改 parser 重建故障 |
| 14 | animation-reading-experience | 补真实 context；375px 浅/深与 reduced-motion 实测 | UI 复验放行 | 改源动画/书稿事实；回退旧正则 |
| 15 | language-batch2 | 交 12+7 处对照与 identity/guard | B1/B2 文字接受 | 重新润色制造新批次 |
| 16 | language-release-pdf | 只读关联原 PR/CI/源快照 | 精确提交范围再审；完整 PDF 执行授权 | 重复 PR；覆盖旧发布包 |
| 17 | spec-plan-continuation | B0 对照交接受 | B0 文字接受；链接 bug 独立方案 | 顺手改 CSS；把 HTTP 200 当点击通过 |
| 18 | book-delivery-closure | 告警单因定位；host/ARM/ESP 配置实编译 | 工程实施审阅；operator 基线；设备/写入；提交/发布授权 | 改测试/runner；路径可见当 HIL；发布 |
| 19 | book-depth-handdraw | 三子任务依赖/单一写者对账 | 每批图文实施与抽评 | 把 814 标题/机械台账当完成 |
| 20 | book-depth-pilot | C2/F3 语义卡 + 两概念薄切片 | 样章实施批准；用户理解/视觉验收 | 跳过薄切片直接批量写书 |
| 21 | book-depth-rollout | pilot 接受后 23 批逐一推进 | 每批范围/事实/图文审阅 | 多写者；以台账冒充 accepted |
| 22 | language-batch5 | 四处对照交文字接受 | B7 文字接受；提交/发布另审 | 提交/扩 S 篇；复写 B7 |

依赖顺序与冲突登记以 `research/dependencies-and-gates.md` 为准；逐项原 AC 以 `research/task-cards.md` 为准。

## 5. 不可自动执行（硬边界）

- 平台：发布、删除、评论、合集建/join、置顶、原创声明、账号与权益操作。
- 硬件：烧录、复位、串口写入、实测数据回填（无日志不填表）。
- 仓库：提交/推送/合并、归档或改写原任务状态与父子关系、重写 `turn-baseline.json`。
- 质量体系：新增/修改测试、runner、CI、policy（须单独 review）。
- 人类判断：文字/视觉/听感接受，A4 退役与 EPUB 范围决策，第 18 条合集归属。
- 证据替代：E0–E2（存在/哈希/旧记录）不能代替 E3–E6；“统筹所有”不推导出任何上述放行。

## 6. 请审阅并回复

1. 审阅 `prd.md`、`design.md`、`implement.md`、本清单及 22 项收口卡。
2. 基线决策：A（推荐，按 `92fc917c` 生成新基线）/ B（逐项追查）/ C（AC5 保持 unverified）。
3. 状态确认：`task.json` 工作区已被先前会话置为 `in_progress`（未提交）；若尚未批准 start，请指示回退 `planning`。本轮未改任何原任务状态。
4. 获批后从 W0 开始；每个外部/硬件动作仍需逐项授权。

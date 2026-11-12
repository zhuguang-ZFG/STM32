# 执行计划：全部历史 spec 统筹收口

状态：in_progress（规划产物已齐，交审中；生产实施未启动）。本计划先完成总任务自身的规划产物与只读核验；22 项历史任务的生产实施仍由各自任务在获批后执行，本任务不代替。

## 阶段 A：基线复核（只读）

- [x] 记录 git 根、HEAD、工作区状态：根 `D:/Users/STM32`，HEAD `92fc917c`，`mcu/` 子树干净，仅根级 `.qoder/` 未跟踪。
- [x] 审计 22 项 `prd.md`/`design.md`/`implement.md` 与 `implement.jsonl`/`check.jsonl`：全部存在且 context 为真实条目。
- [x] 逐项运行 `task.py validate`：21/22 通过，`10-28-social-video-ai-tools` 两处旧 skill 路径失败。
- [x] 对照 `research/artifact-checks.json`：36 母版 hash、书/Job 身份、EPUB 缺失、prose 候选同一性均按创建时快照记录。
- [x] 对照 `research/turn-baseline.json`：22 任务、122 文件 hash、214 验证输入、101 书稿源、42 用户文件、7 源契约作为本轮不可擅改基线。
- [x] 2026-11-11 全量重哈希：任务 60/122、验证 34/214、书稿源 1/101、用户 2/42、契约 3/7 与基线不符；4 个工作流为迁移改名缺失。按 design §7 先停并记录，不覆盖、不自判通过。
- [x] 漂移逐项追查（用户选择 B）：`research/baseline-drift-audit.md` 完成 104 个文件逐一取证——73 个 EOL 变体、10 个匹配历史提交（迁移重接/规划补齐）、21 个未提交基线变体（18 seed 占位 + 3 不可恢复）；无未记录生产改动。AC5 已于 2026-11-11 获用户接受（选择 B 并同意继续）。

## 阶段 B：规划补齐（本任务唯一写入面）

- [x] `prd.md` 存在并完成收敛；已修正“5 项缺三文档/9 项 seed”的过时现状描述。
- [x] 写 `design.md`：边界、真源、证据分级、唯一归属、状态机、迁移与冲突。
- [x] 写 `implement.md`：本文件。
- [x] 填 `implement.jsonl` 与 `check.jsonl` 真实条目（已删除 seed 行；11 + 8 条）。
- [x] 修复 `10-28-social-video-ai-tools` 两处失效 context：
  - `video/jobs/ai4fw/job.json` 替代缺失的 skill 主契约；
  - `video/jobs/ai4fw/review.json` 替代缺失的 quality-gates 定义；
  - 原“skill 源码零修改”要求保留为外部证据，未删除、未伪造本地副本。
- [x] 复跑 22 项 `task.py validate` 与本任务 validate：22/22 + 本任务全绿。
- [x] 复跑 context 引用存在性审计：0 缺失。
- [x] 输出交审清单 `research/review-handoff.md`：执行波次（W0–W5）、22 项前置授权、不可自动动作、基线漂移决策。
- [x] 交用户审阅；审阅通过并完成基线决策后才进入 W0，此前不改生产文件、不动原任务状态、不归档（2026-11-11 用户同意继续，见下方启动前检查）。

## 阶段 C：证据补齐与执行路由（获批后）

本任务只更新账本/路由/验收记录；实际执行由各原任务在获批后完成。波次顺序如下：

### Wave 0：只读证据（可与审阅并行）

- 逐项复核原 PRD 锚点与当前产物，记录 E0/E1/E2。
- 运行允许的窄检查：`node --test tests/animation-markdown.test.mjs`、`node scripts/docs-check.mjs`、prose strict 保护、ffprobe 现有成片。
- 输出：当前证据表，标注 passed/failed/unverified；不修改源文件。
- [x] 2026-11-11 完成 W0：`research/wave0-evidence.md`（prose PASS；docs-check 1 FAIL：CITATION URL；animation test 因缺 `vite` 阻塞；两版 ai4fw ffprobe 通过；36 母版与 `dist/` 缺失；22 项 E0/E1/E2 表）。

### Wave 1：已有交付补证/接受

- B0/B1B2/B7：原保护、identity、用户文字接受、发布关联。
- 动画 D2：现有回归、真实三页 UI、operator 实际状态。
- D1/D3/D4：375px 浅/深、reduced-motion 实测、截图与焦点回退。
- 完成检查：原 AC 逐项有当前证据；用户未接受的项保持未完成。
- [x] 2026-11-11 B0/B1/B2/B7 字节链与提交关联：4/4 before=父版本、current=candidate=末次提交；diff 汇总见 `research/w1-language-diffs.md`，判定见 `research/w1-evidence.md`。
- [x] B0/B1/B2/B7 用户文字接受（E4，2026-11-11 用户「接受，授权」；范围见 `research/w1-language-diffs.md`）。
- [x] 动画 D2 回归与 D1/D3/D4 真实 surface 实测（2026-11-12：D2 12/12、a11y 6/6、reading 6/6、三页 UI 通过；D1 末帧 10.8s/12s 字幕可见；D3 375px 放大 680>293px；D4 焦点回退/滚轮与键盘锁滚通过。`docs:build` 与本机内存上限、`test:browser` 旧 baseURL 未跑，见 `research/w1-evidence.md` §8）。
- [x] 2026-11-11 授权修复 `CITATION.cff` 站点 URL（旧 `/mcu/` → `/STM32/mcu/`）；`docs-check` 由 1 FAIL 转为 PASS（138 文件/6 类/27 条声明）。这是本任务唯一的生产文件改动，属迁移元数据修复。

### Wave 2：工艺/工程准备（可并行）

- 封面：两构图×两配色隔离预览，用户选定后才接入生产。
- EPUB：沿现有 HTML/manifest 真源做两章薄切片设计；新增测试/CI 单独 review。
- BMS-Z：建立当前门到 AC 矩阵；复用反向夹具，不临时破坏真实 README。
- OSS：G 地图与附录 B 工程登记对账，列出 47 工程映射缺口。
- 完成检查：设计/矩阵/缺口清单齐备，未擅自实施生产改动。

### Wave 3：内容深度（串行）

- `book-depth-pilot`：C2/F3 两个概念薄切片 → 六章语义卡 → 用户 2 章以上接受。
- `book-depth-rollout`：pilot 接受后按 23 批，每批 ≤6 文件、一个写者。
- 共享一次章节修改；prose/interest/AI 原验收维度独立对账。
- 完成检查：知识卡 accepted、正式图/真实 surface/原门通过，用户抽评通过。

### Wave 4：外部与硬件（权限驱动）

- 视频：18×2 母版冻结与用户接受 → 逐集平台归档/删除/发布/新 ID 回读；不批量删除。
- 社媒：四平台包与封面/文案对当前 hash；置顶/原创声明另核账号与授权。
- B 站合集：原 17 条锁定、权益只读、逐条 join 与回读；第 18 条归属单独决策。
- E04：板卡/接线/仪器确认 → 四臂烧录复位取日志 → 按日志回填；无授权保持 blocked。
- 完成检查：每项有 E4/E5/E6 证据或明确 blocked；不使用模型时间填硬件表。

### Wave 5：最终交付

- 内容/图/封面冻结后：唯一全量 HTML/A4/16 开构建 → 当前 13 门 → EPUB 结构/epubcheck/逐章同一性 → 统一下载包与自证。
- A4 保留/退役冲突在实施前决策；未决前不删除既有路径。
- 完成检查：PDF 与 EPUB3 均满足原 AC；94 章当前 manifest 同源；提交/线上发布另行授权。

## 验证命令

```bash
# 在 mcu/ 目录运行；若从仓库根运行，路径前加 mcu/
python ./.trellis/scripts/task.py validate 11-07-historical-spec-closure

# 22 项逐项 validate（预期 22/22 PASS）
for d in $(python - <<'PY' | tr -d '\r'
import os
root='.trellis/tasks'
for d in sorted(os.listdir(root)):
    if d!='archive' and os.path.exists(os.path.join(root,d,'task.json')):
        print(d)
PY
); do python ./.trellis/scripts/task.py validate "$d" || echo "FAIL $d"; done

# context 引用存在性（预期无 MISSING）
python - <<'PY'
import json, os
root='.trellis/tasks'
for d in sorted(os.listdir(root)):
    p=os.path.join(root,d)
    if d=='archive' or not os.path.isdir(p): continue
    for f in ('implement.jsonl','check.jsonl'):
        fp=os.path.join(p,f)
        if not os.path.exists(fp): continue
        for i,line in enumerate(open(fp,encoding='utf-8'),1):
            line=line.strip()
            if not line: continue
            obj=json.loads(line)
            if '_example' in obj: continue
            path=obj.get('file','')
            if not os.path.exists(path):
                print(f'MISSING {d}/{f}:{i} -> {path}')
print('audit done')
PY

# 确认只有规划文件变化
git status --short

# 只读窄检查（按需）
node --test tests/animation-markdown.test.mjs
node scripts/docs-check.mjs
```

## 回滚点

- 规划文件：按文件恢复 `prd.md`/`design.md`/`implement.md`/jsonl；原任务 PRD、状态、父子关系不动。
- context 修复：若替换后 validate 失败，只回退 `10-28` 的对应一行；不触碰生产文件。
- 基线漂移：先停并记录差异，不覆盖 `turn-baseline.json` 或生产产物。
- 任何测试/CI/policy 变更：单独 review 后才可使用；本任务不批量放行。

## 启动前检查

- [x] 用户已审阅 `prd.md`、`design.md`、`implement.md`、`research/review-handoff.md`（2026-11-11 同意继续）。
- [x] 22 项 validate 与本任务 validate 全绿（2026-11-11：23/23 PASS）。
- [x] context 引用审计无缺失（277 条引用，0 缺失）。
- [x] `git status` 仅显示规划/context 文件变化（另有迁移前已存在的根级 `.qoder/` 未跟踪，非本任务改动）；2026-11-11 授权修复 `CITATION.cff` 后另含该生产文件，其余不变。
- [x] AC5 漂移审计已获用户接受（2026-11-11；B 方案已完成：73 EOL / 10 历史版本 / 21 未提交变体，见 `research/baseline-drift-audit.md`）。
- [x] 明确记录：本任务规划完成 ≠ 22 项历史交付完成；阻塞项与外部授权保持原样。

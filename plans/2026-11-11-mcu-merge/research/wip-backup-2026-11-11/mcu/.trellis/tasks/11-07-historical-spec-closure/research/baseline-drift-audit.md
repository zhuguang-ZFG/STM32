# 基线漂移逐项审计（turn-baseline vs HEAD 92fc917c）

日期：2026-11-11 · 方法：对 `turn-baseline.json` 的 5 组 SHA-256 全量重哈希；对每个不符文件，沿旧仓库历史（`cf161532` 及其 340 个祖先提交）逐版本比对，并测试 CRLF/BOM 变体。全程只读，不覆盖基线。

## 1. 结论摘要

| 分类 | 数量 | 含义 |
|---|---|---|
| A. EOL/编码变体 | 73 | 逐行内容相同；基线按 CRLF 工作区副本哈希，当前按仓库 `* text=auto eol=lf` 签出 |
| B. 基线=历史已提交版本 | 10 | 基线匹配某个旧提交字节；当前差异是已提交的后续改动（迁移重接/规划补齐） |
| C. 基线内容不在任何提交中 | 21 | 基线是未提交工作区变体；当前文件干净且等于检查点版本（或等于旧版+已知迁移修正） |

除本轮已批准的 `.trellis` 规划/context 编辑外，工作区无生产文件改动。

## 2. B 类：基线匹配历史版本（10）

| 文件 | 基线版本 | 当前差异 | 归因 |
|---|---|---|---|
| `.trellis/tasks/11-06-animation-reading-experience/implement.jsonl` | 2026-11-06 `b44c91b7` | +4/−1 行 | seed 占位→真实 context 条目（规划补齐） |
| `.trellis/tasks/11-06-animation-reading-experience/check.jsonl` | 2026-11-06 `b44c91b7` | +4/−1 行 | seed 占位→真实 context 条目（规划补齐） |
| `scripts/docs-check.mjs` | 2026-11-06 `0e292b09` | +2/−2 行 | 迁移重接（`92fc917c`：monorepo 路径/工作目录） |
| `scripts/search-check.mjs` | 2026-10-25 `27fe38ae` | +2/−2 行 | 迁移重接（`92fc917c`：monorepo 路径/工作目录） |
| `scripts/seo-check.mjs` | 2026-10-08 `c40e6eaa` | +1/−1 行 | 迁移重接（`92fc917c`：monorepo 路径/工作目录） |
| `.github/workflows/book.yml` | 2026-11-05 `19548f6b` | +16/−6 行 | 迁移重接（`92fc917c`：monorepo 路径/工作目录） |
| `.github/workflows/deploy.yml` | 2026-10-25 `27fe38ae` | +11/−4 行 | 迁移重接（`92fc917c`：monorepo 路径/工作目录） |
| `.github/workflows/links.yml` | 2026-10-25 `d87f5139` | +6/−6 行 | 迁移重接（`92fc917c`：monorepo 路径/工作目录） |
| `.github/workflows/quality.yml` | 2026-11-06 `832d40fb` | +22/−5 行 | 迁移重接（`92fc917c`：monorepo 路径/工作目录） |
| `docs/.vitepress/config.mts` | 2026-11-06 `b44c91b7` | +1/−1 行 | 迁移重接（`92fc917c`：monorepo 路径/工作目录） |

四条工作流同时被改名：`.github/workflows/{book,deploy,links,quality}.yml` → 仓库根 `mcu-{book,deploy,links,quality}.yml`；上表差异行数包含路径/工作目录重接。

## 3. C 类：基线内容不在历史提交中（21）

| 文件 | 基线证据 | 当前状态 | 判定 |
|---|---|---|---|
| `.trellis/tasks/10-16-bili-season-after-unlock/prd.md` | 无提交含基线字节；当前与检查点 `cf3303f2` 版本逐行一致 | 等于检查点版本 | 基线为未提交变体；内容不可恢复，当前由检查点固定 |
| `.trellis/tasks/10-16-bili-season-after-unlock/implement.jsonl` | 无提交含基线字节；符合创建期 `_example` seed 占位特征 | 等于检查点版本 | seed→真实 context（创建期 9 项 seed 补齐） |
| `.trellis/tasks/10-16-bili-season-after-unlock/check.jsonl` | 无提交含基线字节；符合创建期 `_example` seed 占位特征 | 等于检查点版本 | seed→真实 context（创建期 9 项 seed 补齐） |
| `.trellis/tasks/10-16-e04-board-measurement/implement.jsonl` | 无提交含基线字节；符合创建期 `_example` seed 占位特征 | 等于检查点版本 | seed→真实 context（创建期 9 项 seed 补齐） |
| `.trellis/tasks/10-16-e04-board-measurement/check.jsonl` | 无提交含基线字节；符合创建期 `_example` seed 占位特征 | 等于检查点版本 | seed→真实 context（创建期 9 项 seed 补齐） |
| `.trellis/tasks/10-26-cover-art/implement.jsonl` | 无提交含基线字节；符合创建期 `_example` seed 占位特征 | 等于检查点版本 | seed→真实 context（创建期 9 项 seed 补齐） |
| `.trellis/tasks/10-26-cover-art/check.jsonl` | 无提交含基线字节；符合创建期 `_example` seed 占位特征 | 等于检查点版本 | seed→真实 context（创建期 9 项 seed 补齐） |
| `.trellis/tasks/10-26-de-ai-polish/implement.jsonl` | 无提交含基线字节；符合创建期 `_example` seed 占位特征 | 等于检查点版本 | seed→真实 context（创建期 9 项 seed 补齐） |
| `.trellis/tasks/10-26-de-ai-polish/check.jsonl` | 无提交含基线字节；符合创建期 `_example` seed 占位特征 | 等于检查点版本 | seed→真实 context（创建期 9 项 seed 补齐） |
| `.trellis/tasks/10-26-oss-influence/implement.jsonl` | 无提交含基线字节；符合创建期 `_example` seed 占位特征 | 等于检查点版本 | seed→真实 context（创建期 9 项 seed 补齐） |
| `.trellis/tasks/10-26-oss-influence/check.jsonl` | 无提交含基线字节；符合创建期 `_example` seed 占位特征 | 等于检查点版本 | seed→真实 context（创建期 9 项 seed 补齐） |
| `.trellis/tasks/10-26-prose-polish/implement.jsonl` | 无提交含基线字节；符合创建期 `_example` seed 占位特征 | 等于检查点版本 | seed→真实 context（创建期 9 项 seed 补齐） |
| `.trellis/tasks/10-26-prose-polish/check.jsonl` | 无提交含基线字节；符合创建期 `_example` seed 占位特征 | 等于检查点版本 | seed→真实 context（创建期 9 项 seed 补齐） |
| `.trellis/tasks/10-27-ai-dev-deepen/implement.jsonl` | 无提交含基线字节；符合创建期 `_example` seed 占位特征 | 等于检查点版本 | seed→真实 context（创建期 9 项 seed 补齐） |
| `.trellis/tasks/10-27-ai-dev-deepen/check.jsonl` | 无提交含基线字节；符合创建期 `_example` seed 占位特征 | 等于检查点版本 | seed→真实 context（创建期 9 项 seed 补齐） |
| `.trellis/tasks/10-27-book-interest-polish/implement.jsonl` | 无提交含基线字节；符合创建期 `_example` seed 占位特征 | 等于检查点版本 | seed→真实 context（创建期 9 项 seed 补齐） |
| `.trellis/tasks/10-27-book-interest-polish/check.jsonl` | 无提交含基线字节；符合创建期 `_example` seed 占位特征 | 等于检查点版本 | seed→真实 context（创建期 9 项 seed 补齐） |
| `.trellis/tasks/10-28-social-video-ai-tools/implement.jsonl` | 无提交含基线字节；符合创建期 `_example` seed 占位特征 | 等于检查点版本；另含本轮已批准 context 修复 1 行替换 | seed→真实 context（创建期 9 项 seed 补齐） |
| `.trellis/tasks/10-28-social-video-ai-tools/check.jsonl` | 无提交含基线字节；符合创建期 `_example` seed 占位特征 | 等于检查点版本；另含本轮已批准 context 修复 1 行替换 | seed→真实 context（创建期 9 项 seed 补齐） |
| `scripts/measure-site.mjs` | 无提交含基线字节；当前 = 旧版 `286d692e` + 2 行迁移修正 | 等于旧版+迁移重接 | 迁移路径修正（`92fc917c`） |
| `.trellis/tasks/11-02-skill-remaster/deliverables/book-guide.html` | 无提交含基线字节；当前与检查点 `b2df6dc0` 版本逐行一致 | 等于检查点版本 | 基线为未提交变体；内容不可恢复，当前由检查点固定 |

## 4. A 类：EOL/编码变体，逐行内容相同（73）

基线对 CRLF 工作区副本取哈希；仓库现按 LF 签出。下列文件仅换行字节不同，逐行内容与当前一致。

| 目录 | 数量 | 文件 |
|---|---|---|
| `.trellis/tasks/10-16-bili-season-after-unlock/` | 1 | `task.json` |
| `.trellis/tasks/10-16-e04-board-measurement/` | 2 | `prd.md`<br>`task.json` |
| `.trellis/tasks/10-22-video-v2-remaster/` | 5 | `prd.md`<br>`implement.md`<br>`task.json`<br>`implement.jsonl`<br>`check.jsonl` |
| `.trellis/tasks/10-25-bmsz-validation-depth/` | 1 | `task.json` |
| `.trellis/tasks/10-25-book-production/` | 1 | `task.json` |
| `.trellis/tasks/10-26-cover-art/` | 1 | `task.json` |
| `.trellis/tasks/10-26-de-ai-polish/` | 1 | `task.json` |
| `.trellis/tasks/10-26-oss-influence/` | 1 | `task.json` |
| `.trellis/tasks/10-26-prose-polish/` | 1 | `task.json` |
| `.trellis/tasks/10-27-ai-dev-deepen/` | 1 | `task.json` |
| `.trellis/tasks/10-27-book-interest-polish/` | 2 | `prd.md`<br>`task.json` |
| `.trellis/tasks/10-28-social-video-ai-tools/` | 2 | `prd.md`<br>`task.json` |
| `.trellis/tasks/11-02-skill-remaster/` | 1 | `annotations.json` |
| `.trellis/tasks/11-07-book-delivery-closure/` | 4 | `prd.md`<br>`task.json`<br>`implement.jsonl`<br>`check.jsonl` |
| `.trellis/tasks/11-07-book-depth-handdraw/` | 4 | `prd.md`<br>`task.json`<br>`implement.jsonl`<br>`check.jsonl` |
| `.trellis/tasks/11-07-book-depth-pilot/` | 4 | `prd.md`<br>`task.json`<br>`implement.jsonl`<br>`check.jsonl` |
| `.trellis/tasks/11-07-book-depth-rollout/` | 4 | `prd.md`<br>`task.json`<br>`implement.jsonl`<br>`check.jsonl` |
| `.trellis/tasks/11-07-language-batch5/` | 4 | `prd.md`<br>`task.json`<br>`implement.jsonl`<br>`check.jsonl` |
| `docs/` | 1 | `curriculum.json` |
| `docs/ai/` | 1 | `05-this-book-pipeline.md` |
| `mcu-book/` | 1 | `manifest.json` |
| `scripts/` | 4 | `check-firmware.mjs`<br>`device-console.py`<br>`gen-progress.mjs`<br>`project-catalog.mjs` |
| `scripts/arch-diagrams/` | 24 | `boot-relay.out.html`<br>`boot-sequence.out.html`<br>`context-switch.out.html`<br>`device-ops.out.html`<br>`dma-paths.out.html`<br>`exti-chain.out.html`<br>`heap-free-list.out.html`<br>`i2c-bus.out.html`<br>`idf-anatomy.out.html`<br>`linker-map.out.html`<br>`logger-flow.out.html`<br>`map-audit.out.html`<br>`memory-map.out.html`<br>`ota-slots.out.html`<br>`pwr-domains.out.html`<br>`rcu-tree.out.html`<br>`rtos-side-by-side.out.html`<br>`rtt-three-floors.out.html`<br>`scheduler-structs.out.html`<br>`sem-mutex.out.html`<br>`spl-anatomy.out.html`<br>`toolchain-pipeline.out.html`<br>`usart-rename-map.out.html`<br>`wifi-stack.out.html` |
| `scripts/arch-diagrams/icons/` | 1 | `manifest.json` |
| `scripts/social-cards/` | 1 | `cover.html` |

## 5. 对 AC5 的影响与建议

- 本轮工作区无生产改动（`git status` 仅 `.trellis` 规划/context）。A 类 73 个文件内容未变，只是基线取哈希时的换行形态不同。
- B 类 10 个文件差异全部归因到已提交的迁移重接或规划补齐；无未记录的生产改动。
- C 类 21 个文件：18 个符合创建期 seed→真实 context 的授权补齐；另 3 个（10-16 prd、measure-site、book-guide）的基线内容从未进入提交、不可恢复，但当前内容由检查点固定且工作区干净。
- 结论：漂移不是本轮引入，也没有未记录的源/产物变化。建议以 `92fc917c` 为 AC5 起点，接受本审计作为漂移解释；若后续仍需按 `turn-baseline.json` 比对，请单独批准在审阅后生成新基线快照（不改旧文件）。

## 6. 复现方法

1. 重哈希：对 5 组 map 逐文件 `sha256(工作区字节)`，与基线值比较。
2. 历史定位：`git -C .. log --format='%H|%ad|%s' --date=short cf161532 -- <path>` 取每个版本，`git show <rev>:<path>` 后重哈希，找出与基线相等的版本。
3. EOL 变体：把当前字节按 `
 → 
` 重算 SHA-256（以及 BOM 变体），与基线比较。
4. 当前差异：对匹配版本与工作区文件做逐行 diff，记录 added/removed。
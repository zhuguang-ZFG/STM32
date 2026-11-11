# W0 只读证据（2026-11-11）

环境：`mcu/`，分支 `feat/mcu-subtree-merge`，HEAD `92fc917c`；Node `v24.14.0`，Python `3.13.14`，ffprobe `9.0.2`。本轮只读：未改生产文件、未安装依赖、未构建、未联网、未操作平台或硬件。

> 后续（2026-11-11，W1）：用户授权修复 CITATION URL 并安装依赖；`docs-check` 已转 PASS，见 `research/w1-evidence.md` §7。本文件第 1 节的 FAIL/UNVERIFIED 是 W0 当时状态，保留不改。

## 1. 窄检查结果

| 检查 | 命令 | 退出码 | 实际输出 | 等级 | 判定 |
|---|---|---|---|---|---|
| prose strict 保护 | `node scripts/prose-readability.mjs --check` | 0 | 78 章，平均长句占比 10.1%，逐章均在基线 +1.5pt 以内 | E3 | PASS（仅覆盖历史 78 章基线，非全书 101 源） |
| 全站文档一致性 | `node scripts/docs-check.mjs` | 1 | 1 处问题：`CITATION.cff` 的 `url` 为 `https://zhuguang-zfg.github.io/mcu/`，站点/manifest 口径为 `https://zhuguang-zfg.github.io/STM32/mcu/` | E3 | FAIL（迁移遗留；修复需改生产文件，W0 未执行） |
| 动画 Markdown 回归 | `node --test tests/animation-markdown.test.mjs` | 1 | `ERR_MODULE_NOT_FOUND: Cannot find package 'vite'`；本检出无 `node_modules` | E3 | UNVERIFIED（环境缺依赖，不是断言失败；`npm ci` 未获授权，未执行） |
| ffprobe 横版成片 | `ffprobe video/jobs/ai4fw-16x9/outputs/film.mp4` | 0 | h264，1920×1080，30/1，64.1s | E3 | PASS（仅容器/流元数据） |
| ffprobe 竖版成片 | `ffprobe video/jobs/ai4fw/outputs/film.mp4` | 0 | h264，1080×1920，30/1，64.1s | E3 | PASS（仅容器/流元数据） |
| ffprobe 18×2 正片母版 | — | — | `video/out/` 不存在；`.gitignore:51` 忽略该目录 | — | UNVERIFIED（产物不在当前检出） |

## 2. E1 身份复核

### 2.1 36 个正片母版 hash

0/36 文件存在。`artifact-checks.json` 的 36 条 SHA-256 仍是创建时身份锚点，但 `video/out/` 是被忽略的构建输出，迁移后的检出未携带，无法重算。不是 hash 不符，而是文件缺失；恢复需从旧工作区取回或获授权重建，二者本轮都未做。

### 2.2 书/Job 身份（7 项）

| 文件 | 当前结果 | 判定 |
|---|---|---|
| `mcu-book/dist/mcu-deep-book.html` | 不存在（`mcu-book/dist/` 被 `.gitignore:59` 忽略） | UNVERIFIED |
| `mcu-book/dist/mcu-deep-book.pdf` | 不存在 | UNVERIFIED |
| `mcu-book/dist/mcu-deep-book-print.pdf` | 不存在 | UNVERIFIED |
| `mcu-book/book/G-开源地图.md` | 15883 字节，SHA-256 与记录一致 | PASS |
| `video/jobs/ai4fw/review.json` | 原始 LF hash 不同；按 CRLF 归一后与记录一致（36 行换行差异） | PASS（EOL 变体） |
| `video/jobs/ai4fw-16x9/review.json` | 同上（34 行换行差异） | PASS（EOL 变体） |
| `video/publish/copy-ai4fw.md` | 3938 字节，SHA-256 与记录一致 | PASS |

### 2.3 prose 候选同一性

4/4 源文件与候选逐字节相同（raw 与 LF 归一均相同）：B0 `docs/build/00-toolchain.md`、B1 `01-four-steps.md`、B2 `02-elf.md`、B7 `07-build-system.md`。

### 2.4 正片 schema 与 EPUB

- `video/episodes/*/episode.json` 共 20 份：18 份 `formatVersion=2`（正片）；`ai4fw` 为 1（已登记的兼容缺口）；1 份无 `formatVersion`（ab-test 集）。
- `video/series.json`：19 条（18 `done` + `c3b-volatile` `ab-test`），`next` 为空；`series.json` 本身不含 `formatVersion` 字段。
- EPUB：`mcu-book/build_epub.py`、`mcu-book/check_epub.py` 均不存在；`package.json` 无 `book:epub`。与 `artifact-checks.json` 的 `epub: {builder:false, checker:false, npm:false}` 一致。

## 3. 22 项当前证据表

`PASS` 只指该行所列检查，不代表原任务整体验收；E0 存在性与 E2 历史记录不能替代 E4–E6。

| # | 原任务 | 本轮可证 | 等级 | 状态 | 仍缺 |
|---|---|---|---|---|---|
| 01 | bili-season-after-unlock | 规划记录存在；未查平台权益/合集 | E0 | UNVERIFIED | 平台只读检查、17 条锁定、E6 回读 |
| 02 | e04-board-measurement | `docs/lab/e04-priority-inversion.md` 存在，四臂实测表仍为空 | E0 | UNVERIFIED | 板卡/接线确认、E5 烧录复位日志 |
| 03 | video-v2-remaster | 18 正片 `formatVersion=2`；`video/out/` 36 母版缺失 | E0 | PARTIAL | 36 母版 E1/E3、听感/画面 E4、平台 E6 |
| 04 | bmsz-validation-depth | prose strict PASS；docs-check FAIL（CITATION URL） | E3 | FAIL | 门到 AC 矩阵、全门与反向夹具 |
| 05 | book-production | `build_print.py`/`check_pdf.py` 存在；EPUB 与 `dist/` 缺失 | E0 | UNVERIFIED | EPUB 实现、当前 13 门、构建产物 E1 |
| 06 | de-ai-polish | 父任务三文档与两个子任务存在 | E0 | UNVERIFIED | 文字/封面用户接受 E4 |
| 07 | cover-art | `mcu-book/print/art.py`、`research/cover` 存在 | E0 | UNVERIFIED | 两构图×两配色选择、E4 定稿接受 |
| 08 | oss-influence | `G-开源地图.md` hash 一致；核验记录存在 | E1 | PARTIAL | 逐条上游许可/路径 E6、47 工程映射、P3 |
| 09 | prose-polish | prose strict PASS（78 章） | E3 | PARTIAL | 逐批 before/after、用户抽评 E4 |
| 10 | ai-dev-deepen | `docs/ai/` 6 章 + index 存在 | E0 | UNVERIFIED | 六章细节/来源复核、E4 视觉接受 |
| 11 | book-interest-polish | implement 历史记录存在 | E2 | UNVERIFIED | 6 试点闭环、用户 2 章抽评 E4 |
| 12 | social-video-ai-tools | 两份 review + copy hash 一致；两版成片 ffprobe 通过 | E1/E3 | PARTIAL | 四平台线上 E6、封面/文案逐项对账 |
| 13 | animation-d2-closure | 回归命令存在，但依赖缺失无法运行 | — | UNVERIFIED | `npm ci` 后重跑、真实三页 UI |
| 14 | animation-reading-experience | implement 记录存在 | E2 | UNVERIFIED | 375px 浅/深、reduced-motion、焦点回退 |
| 15 | language-batch2 | B1/B2 候选 raw 同一；prose strict PASS | E1/E3 | PARTIAL | 用户文字接受 E4、发布关联 |
| 16 | language-release-pdf | `dist/` 产物缺失 | — | UNVERIFIED | 固定范围发布证据、完整 PDF 与 13 门 |
| 17 | spec-plan-continuation | B0 候选 raw 同一；prose strict PASS | E1/E3 | PARTIAL | 用户文字接受 E4；下一站点击另案 |
| 18 | book-delivery-closure | implement 记录；operator 基线不可用 | E2 | BLOCKED | operator 合法基线、告警/固件/硬件/最终包 |
| 19 | book-depth-handdraw | 101 源/814 标题/24 批研究账存在 | E0 | UNVERIFIED | 语义知识卡、正式图文、用户理解 |
| 20 | book-depth-pilot | 六章方向与草图研究存在 | E0 | UNVERIFIED | 样章薄切片、真实 surface、E4 |
| 21 | book-depth-rollout | 23 批归属账存在 | E0 | UNVERIFIED | pilot 接受后逐批实施与抽评 |
| 22 | language-batch5 | B7 候选 raw 同一；prose strict PASS | E1/E3 | PARTIAL | 用户四处文字接受 E4、发布授权 |

## 4. 需单独授权的后续动作（本轮均未执行）

1. **修复 CITATION.cff**：把 `url` 改为 `https://zhuguang-zfg.github.io/STM32/mcu/`（并顺带确认 `repository-code` 是否应随迁移改为 `zhuguang-ZFG/STM32`）；属生产文件修改。
2. **安装依赖**：`npm ci` 后重跑 `node --test tests/animation-markdown.test.mjs` 及阅读体验相关检查；安装依赖与网络访问本轮未做。
3. **恢复或重建产物**：36 个 `video/out/` 母版与 `mcu-book/dist/` 的 HTML/PDF/印前 PDF 不在当前检出；需用户决定从旧工作区取回，还是授权重建（重建不得覆盖已发布母版）。
4. **平台/硬件证据**：任务 01、02、12、18 的 E5/E6 证据仍需各自授权与外部前提。

## 5. 证据边界

- 本文件只有 E0/E1/E2/E3；无 E4 用户接受、E5 硬件日志、E6 平台回读。
- prose PASS 覆盖 78 章历史基线，不等于 manifest 94 章/101 源全书通过。
- ffprobe 只证明编码/尺寸/帧率/时长，不证明画面、声音或平台线上状态。
- `docs-check` 的 FAIL 是当前真实缺陷，未修复、未规避；不得据此宣称门禁全绿。
- hash 复核证明字节同一性；CRLF 归一仅用于已知换行差异，未放宽其他内容比较。

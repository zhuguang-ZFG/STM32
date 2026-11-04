# task_verify 等价分列检查记录（passed / failed / unverified）

日期：2026-11-05（America/Adak）。目的：`BOOK_CLASSIC_CONVERGE_SPECS.md` §10.2 末项
「`task_verify` 的 passed/failed/unverified 分列；unverified 不冒充通过」在本环境
没有 `task_verify` 工具，按同义规则用本文件落盘等价分列记录。每行给结论 + 证据，
unverified 一律写明原因，不冒充通过。

## 1. §10.2 ch03 硬门（逐条分列）

| # | 检查 | 状态 | 证据 |
| --- | --- | --- | --- |
| 1 | Overlay 已合入 classic 基座 | passed | `BOOK_CLASSIC_CONVERGE_SPECS.md` 在 main；§0 裁定表 |
| 2 | Port A（strip）完成，slop_lint 绿 | passed | `python tools/slop_lint.py` 机械命中 0（2026-11-05 复跑） |
| 3 | Port B（Sepia/plain-voice）完成，无 docs 整树合并 | passed | `.claude/skills/sepia*/` 在库；`audits/branch-archive-strip-handraw.md` |
| 4 | CONTENT_GUIDE 按 §8 修改 | passed | `docs/CONTENT_GUIDE.md` 教学合同 + 功能块可选 |
| 5 | ch03 中英教学合同字段登记且对齐 | passed | manifest `chapter_guides['03-GPIO与LED.md']` 与 EN 对应 |
| 6 | 功能块可选结构；最小胜利前置 | passed | `test_classic_l1` 等批次门 PASS |
| 7 | Handraw 规划图 + 真证轨缺口显式声明 | passed | ch03 双轨标注 + 照片 SHA 在 `assets/photos/README.md`；PC13 特写缺口诚实挂账 |
| 8 | 失败分支含可区分证据 | passed | ch03 正文「写 1 灯灭」对比段 |
| 9 | 短片 + 长片链按 SP-05/06；旁白指纹不与邻章同构 | passed | ch03 7 拍多样指纹；ch00–05 Batch A 改写后 6 章互不相同（§3 本文件） |
| 10 | Sepia 删除/回退检查记录 | passed | 章缺陷清单 + CONTENT_GUIDE 自测节 |
| 11 | §15 三表模板（插图/动画/出处） | passed | `audits/ch03-converge-gate.md` §15.4 |
| 12 | 窄回归 + 全量 unittest + check_assets + slop_lint + 双语 HTML/PDF check | passed | pytest **182 passed**（2026-11-05 两轮）；check_assets 1880/1880 链接；PDF 565/589 页重建 |
| 13 | 浏览器/PDF 目检 | passed | zh p12/p285/p563 + en p296 光栅目检无缺陷（`audits/handraw-knowledge-track-29.md` §4） |
| 14 | `task_verify` 工具本体执行 | **unverified** | 本环境无 `task_verify` 工具；以本分列记录替代，属等价落盘而非工具输出 |

## 2. §11.2 每批回归命令（2026-11-05 实测分列）

| 命令 | 状态 | 结果 |
| --- | --- | --- |
| `python -m pytest stm32-book/tests` | passed | 182 passed（2× 全量复跑） |
| `python tools/check_assets.py` | passed | 1880/1880 链接；JPEG 哈希 4/4；GIF 逐像素比对过 |
| `python tools/slop_lint.py` | passed | 机械命中 0 |
| `python tools/audit_book.py` | passed | zh/en 锚点各 425；低于目标 0 |
| `python stm32-book/build_html.py --check`（zh/en） | passed | 两次构建检查 PASS |
| `python stm32-book/build_html.py --pdf`（zh/en） | passed | 565 页 / 589 页（118 MB） |
| `git diff --check` | passed | 无空白错误 |

## 3. 视频重制链（本轮新增，逐项分列）

| 检查 | 状态 | 证据 |
| --- | --- | --- |
| ch03 短片重配音端到端（TTS→分段→合成→字幕→海报） | passed | `gen_narrated.py --speak 03`：121.4 s、1920×1080 H.264+AAC、7 条 SRT；TTS 一次连接被重置后重试成功（4 次退避逻辑生效） |
| ch03 长课 media-report 十项 | passed | `gen_long_lesson.py --report 03`：28 场景/五角色/1080p/30fps/LUFS −15.7/true-peak −3.9/联系表全 True；SHA 已记录 |
| Blocker 1（RATE/PITCH 环境变量） | passed | `gen_narrated.py` 接 `NARRATED_RATE`/`NARRATED_PITCH`（默认 −6% 不变） |
| Batch A 旁白反同构改写（ch00/01/02/04/05） | passed | 五章结尾拍互不相同且 ≠ ch03/ch06 模板；`--check` 全过 |
| Batch A 五章 1080p 重配音 | passed | ch00 139.3s / ch01 146.9s / ch02 155.5s / ch04 157.2s / ch05 161.0s，均 1920×1080 H.264+AAC、10 条字幕，全部在 120–240 s 合同内（ffprobe 逐条核验） |
| Batch A 文档旁白稿同步 | passed | `--patch-docs` 后 zh+en 各 10 文件 24/30 行更新 |
| ch00/01/02/04/05 长课重配音（Batch B） | **unverified** | ch01/02/04/05 因 Huihui 漂移需以 Xiaoxiao 重配音，编码进行中（每章约 15–25 分钟）；ch00 长课已是 Xiaoxiao 且十项全过；storyboard 均在、`--check 03` 已验链 |
| ch06–28 视频（Batch C–G） | **unverified** | 排队中；计划与批次定义见 `audits/video-regen-plan.md` |
| `task_verify` 工具本体 | **unverified** | 工具不存在；本文件即等价分列记录 |

## 4. 逐章审计（§11.3 第一项）的对账

29 zh + 29 en 的逐章审计证据链：B1–B7 批次门
（`audits/ch03-converge-gate.md`、`b2…b6-converge-gate.md`、`b7-converge-census.md`、
`b7-gap-close.md`）逐章列了教学合同、三表、锚点、出处与裁定；本轮知识轨审计
（`audits/handraw-knowledge-track-29.md`）补齐 29 章 + 附录的视觉层对账。
§11.3 该项是否勾选由完成审计者判定；本记录提供对账入口，不替人勾。

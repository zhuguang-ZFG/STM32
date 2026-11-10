# B53：Spec 收口（Book 2.0 v1.3.1）

日期：2026-11-10。性质：文档收口批次，不改正文、资产与构建器。
依据：`BOOK_REDESIGN_SPEC.md` §10–§12、`BOOK_VIDEO_CLASSIC_SPECS.md` SP-08、
`BOOK_CLASSIC_CONVERGE_SPECS.md` §10.2 / §11.3 / §15。
关闭后三份 Spec 的状态行均指向本文件；本文件是唯一收口索引。

## 1. 关闭判定

| Spec | 收口前状态 | 收口后状态 | 关闭依据 |
| --- | --- | --- | --- |
| `BOOK_REDESIGN_SPEC.md` | Draft 1（2026-11-02） | **已发布**（Book 2.0 v1.3.1） | §12 全书完成定义；`audits/b51-final-acceptance.md` 终态命令集；v1.3.1 已发布（中英 HTML/PDF 4 资产） |
| `BOOK_VIDEO_CLASSIC_SPECS.md` | 执行基线 v1 · 冻结 | **关闭**（2026-11-10） | SP-08 总完成检查 9/9 逐项取证（本文件 §3）；unverified 分列（本文件 §5） |
| `BOOK_CLASSIC_CONVERGE_SPECS.md` | Overlay Draft 1 | **已关闭**（2026-11-10） | §15 三表与密度上调、§6.4 视觉锚点反推、ch03 硬门（本文件 §2、§4） |

## 2. Overlay（CLASSIC）条款落点

| 条款 | 关闭依据 | 证据 |
| --- | --- | --- |
| §15.4 三表模板（B1） | ch03 缺陷清单先填插图/动画/官方·开源三表再开画 | `audits/ch03-converge-gate.md` §15.4 |
| §15.4 B2–B6 同模 | 各批门审计逐章登记插图、动画与出处字段 | `audits/b2-converge-gate.md` … `b6-converge-gate.md` |
| §15.4 B7 普查 | 全书覆盖率普查 + 缺口收口 | `audits/b7-converge-census.md`；`b7-gap-close.md`（三类图 29/29、动画 ≥1、锚点 29/29） |
| §15.1–15.2 密度上调 | Overlay 锚点下限 4/6/9 生效；无图区间 ≤1,200（唯一批准例外 ch26=1,231） | `tools/audit_book.py` 收口复跑：zh/en 各 543 锚点、deficit 0；`test_book_audit.py` GAP_CAP 锁 |
| §15.3 官方优先 + OSS 对照 + 冲突裁定 | ST Rev 钉版清单；每章 ≥1 ALLOWED GitHub OSS；官方↔OSS 分歧有裁定语 | 本 Spec §15.3；`b7-converge-census.md` §5.2 / §5.3 |
| §6.4 代表帧锚点反推 | 5 个视觉锚点覆盖四条视觉轨，中英提示词 + 媒介边界 | `audits/visual-anchors-reverse-2026-11-10.md`（全本地读取，未上传第三方） |
| §10.2 ch03 硬门（14 项） | 全项勾选；工具本体项诚实分列 | `audits/ch03-converge-gate.md`；`audits/task-verify-equivalent-2026-11-05.md` §1 |
| §11.3 全书完成定义 | 逐条证据已在 Spec 内勾选并注明落点 | `BOOK_CLASSIC_CONVERGE_SPECS.md` §11.3 |
| §9.5 分支退役 | strip / handraw 停更归档，远程只读保留 | `audits/branch-archive-strip-handraw.md` |

## 3. SP-08 总完成检查（9/9）

| # | 检查项 | 收口证据 |
| --- | --- | --- |
| 1 | 29 中文 + 29 英文逐章审计，无跳章 | `audit_book` 逐章指标由 `test_book_audit.py` / `test_advanced_visuals.py` 锁定；B51 按 PDF TOC 抽样 15 页覆盖七个分部（`b51-final-acceptance.md`） |
| 2 | 29 短片 + 29 长片由当前源可再生，字幕/分镜/成片哈希对应 | `video-regen-plan.md` 批次 A–G 全勾；逐章 `storyboard-rendered.json`、`media-report.json`（十项检查）、SRT、联系表 |
| 3 | 五个技能均留下可审查用途 | 本文件 §4 技能证据表 |
| 4 | 双语 HTML/PDF 同源，书签/索引/来源/许可一致 | 同一 builder `--check` zh/en PASS（29 章）；EPUB 各 49 spine / 621 images；页样 15/15 见 b51；来源 `CREDITS.md`，照片 5/5 哈希匹配 |
| 5 | 联系表全检，五类关键场景无缺图/溢出/黑帧/错位 | 逐章 `contact-sheet.jpg` + media-report 十项；Handraw 联系表见 `handraw-knowledge-track-29.md`，视频联系表见 `video-regen-plan.md` |
| 6 | 基线测试与新增合同全通过，无删测试换绿灯 | pytest **196 passed**（2026-11-10 收口复跑，339.83 s，exit 0）；新增合同均以失败复现→通过方式加入 |
| 7 | `task_verify` passed / failed / unverified 分列 | `audits/task-verify-report.json`：9 passed / 0 failed / 3 unverified；等价分列见 `task-verify-equivalent-2026-11-05.md` |
| 8 | 文档、生成命令、来源、许可、CREDITS 同步；临时文件不入发布源 | 生成命令随各批次审计落盘；`.gitignore` 排除 `.temp/`、`final-videos/`、`wechat-mp/` 等 |
| 9 | Goal 只在当前状态证据逐项复核后标记完成 | 本清单即 2026-11-10 逐项复核结果 |

## 4. 五技能证据表

审查提交与边界以 `BOOK_VIDEO_CLASSIC_SPECS.md` SP-02 为准。

| 技能（审查提交） | 可审查用途落点 | 边界 / 不用于 |
| --- | --- | --- |
| stack-diagram（`caru-ini/stack-diagram` @ `9e90a3b`） | `tools/gen_stack_diagrams.py` 重建 `assets/diagrams/stack-gpio-pc13-led.{html,png,-dark.png}`；docs/03 中英嵌入；SHA 见 `ch03-converge-gate.md` 图 4；`b9-layout-sweep.md` 记录 base64 重算 | 不画逐拍电气波形；不重绘品牌 Logo；不替代真证轨 |
| dsh-guizang-design（`op7418/dsh-guizang-design` @ `d16cea6`） | 本仓库实际调用为 `humanizer-zh` 子技能：`b25` / `b27` / `b28` / `b30` / `b31` 审计均记录「中文另按 humanizer-zh 核对信息保留」；规则落点 `docs/CONTENT_GUIDE.md`「节奏、分层与自测」 | 不改代码、URL、ID、表数据；不另立书籍源（Page/PPT/Social Card 未替换现有 builder） |
| handraw-style（`yang0/handraw-style` @ `d7a8837`） | `handraw-knowledge-track-29.md`：29 章 + 附录 A–F 共 177 张 PNG + 66 张 SVG 源；FA-002/FA-029 风格、IG 图型、C 配色登记；双语引用对称断言 | 不冒充实拍/仪器证据；release-planner 未使用；知识轨统一标「原理示意 / 非实拍」 |
| image-prompt-reverse（`LunarXuan/image-prompt-reverse` @ `4dead0a`） | `visual-anchors-reverse-2026-11-10.md`：5 个锚点（AI 知识图 / 脚本板绘 / stack 工程图 / 实拍真证 / 视频帧）、中英提示词、媒介边界；图片仅本地读取 | 不从图片反推寄存器、型号、参数或实验结论；不上传、不复制无关品牌 |
| unslop（`heydamir/unslop` @ `a6f121e`） | `CREDITS.md` 署名（`37120c9`）；红线维度对应的可审查产物：`b46-layout-baseline.md` / `b47-typography-tiers.md`（版式与排印）、`b9-layout-sweep.md`（324 张 SVG 几何体检）、`b51-final-acceptance.md` 15 页目检、`video-regen-plan.md` 逐章联系表与五类场景抽帧 | 不改技术事实；不做宣传故事片；不复用示例页面 |

## 5. unverified 分列（不冒充通过）

来源：`audits/task-verify-report.json`（12 项：9 passed / 0 failed / 3 unverified）。

| 项 | 状态 | 原因 | 处理 |
| --- | --- | --- | --- |
| ch03 真板照片（PC13 点亮特写 / 表计截图） | **unverified** | 需真板实拍；本环境无真板，Spec 禁止 AI 图冒充；自由许可素材检索无替代 | 正文与图注诚实挂账，不阻塞 Spec 关闭 |
| L4 整板分段电流实测 | **unverified** | 需 NUCLEO-L476RG 与电流分析仪做分段积分 | 引用 ST AN4746 典型实测作对照，未冒充本仓库实测 |
| `task_verify` 工具本体 provenance | **unverified** | agent 框架的 `task_verify` 工具不在本环境 | 以 `tools/task_verify.py` + 等价分列记录替代，unverified 如实保留 |

这三项属于硬件证据缺口与环境工具缺失，Spec 的关闭条件是「分列且不冒充通过」，不是「全部转绿」。

## 6. 收口复跑验证（2026-11-10）

```text
pytest stm32-book/tests -q      196 passed in 339.83s（exit 0）
check_assets                    全部通过：链接 2176/2176、照片 5/5、短片 29、仿真 6+2、引脚图 3、示例 3
build_html --check (zh)         PASS（29 章，146,602,917 B）
build_html --lang en --check    PASS（29 章，146,704,101 B）
slop_lint                       干净：没有机械命中
audit_book                      zh/en 各 543 锚点；deficit 0；低于目标 0 章；含实拍 4 章
git diff --check                clean（仅 LF→CRLF 提示，无空白错误）
```

运行记录补充：同日 21:08 的一次全量跑曾出现 18 处失败——`build_html.py` 拼接正文时
`MemoryError`（并发重负载下进程内存耗尽）与一处 Playwright `TargetClosedError`；
空闲后同命令复跑 196 passed，b51 终态同提交也是 196 passed。判定为内存压力抖动，
不是代码回归；`.temp/pytest-b53-full.log` 与 `.temp/pytest-b53-rerun.log` 两轮日志可对照。

## 7. 保留缺口与后续规则

- PC13 点亮特写与表计截图仍缺（真证轨）；取得实拍前不补图、不用生成图顶替。
- ch26 最大无图区间 1,231 是唯一批准例外（`test_book_audit.py` 登记）。
- en PDF 本地与 CI 分页存在平台差异，发布门以 CI 实测为准（见 b51 注）。
- 三份 Spec 已关闭：后续新工作必须开新的 spec 切片或批次审计，不得在已关闭
  Spec 上续写完成声明，也不得删除旧 Spec 中仍有效的事实约束。

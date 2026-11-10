# B54 · 英文无图区间收口（en top-8 章 ≤2,000）

日期：2026-11-11 ｜ 分支：`improve/b54-en-gap-close`（基于 `main` @ `9a1d131`）｜ 依据：`docs/superpowers/specs/2026-11-10-b54-en-gap-closeout-design.md`、`BOOK_REDESIGN_SPEC.md` §6.3/§11

## 范围与产物

- 8 章：04/11/12/15/16/18/19/28——spec §1.1 的英文侧前 8 大无图区间（2,566–3,216）。
- 29 张 Handraw 知识轨图：spec §4 计划 9 张（ch16-battery-budget、ch18-hardware-triage、
  ch18-rtos-triage、ch28-h745-boundaries、ch11-bkp-magic、ch19-la-sampling、
  ch15-two-priority-rules、ch12-last-page-math、ch04-lab-evidence），同窗口按用户批准
  继续追加 20 张，合计 29 张。每张 zh/en 同序嵌入、共用同一 PNG，全部标注
  「原理示意 / 非实拍」。
- 正文只插入、不改写：`git diff --numstat` docs 16 文件 +294 / −0（另 ch16、ch19 两处
  既有图块前补空行，不涉及文字）。新增资产 29 对 PNG/SVG，生成器
  `tools/handraw_track/fig_ch{04,11,12,15,16,18,19,28}.py` 固定 seed 可重建；
  嵌入由 `embed.py` 章函数与 `embed_b54.py`（spec 9 张）完成。

## 逐章前后（`audit_book` `max_visual_gap_chars`）

| 章 | en 前 | en 后 | zh 前 | zh 后 | 锚点前→后（zh=en） |
|---|---:|---:|---:|---:|---:|
| 16 | 3,216 | **1,761** | 1,127 | 810 | 18→23 |
| 18 | 2,840 | **1,655** | 1,131 | 865 | 16→22 |
| 28 | 2,833 | **1,975** | 1,090 | 939 | 25→29 |
| 11 | 2,740 | **1,944** | 1,139 | 798 | 18→21 |
| 19 | 2,715 | **1,820** | 1,143 | 874 | 19→23 |
| 15 | 2,625 | **1,845** | 1,179 | 1,000 | 18→20 |
| 12 | 2,586 | **1,949** | 1,194 | 882 | 18→20 |
| 04 | 2,566 | **1,771** | 1,106 | 706 | 18→21 |

- 全书 zh：29 章全部 ≤1,231（ch26=1,231 为已批例外），无回退。
- 其余 13 章 en >2,000 的数值与 spec §8 基线逐一相同（09=2544、17=2531、08=2481、
  14=2454、05=2333、13=2297、20=2293、10=2234、02=2228、03=2153、07=2142、
  24=2100、27=2030），未受本批影响，留作 B55 候选。
- 双语 parity：8 章 `asset_sequence_equal=true`，h2/h3/表/代码/公式 delta 全 0，
  PDF 锚点 delta 0。

## 测试锁

- `test_book_audit.py`：新增 `EN_GAP_BATCH_BUDGETS`（8 章 × 2,000）与
  `test_en_visual_gap_batch_budget`；受影响章 `asset_sequence` 与节点数值重钉
  （04=21、11=21、12=20、15=20、16=23、18=22、19=23、28=29），project 章独立
  序列同步（23）。
- `test_advanced_visuals.py` `CHAPTERS`：8 章 `<img>` 元组重钉（04=21、11=21、12=20、
  15=20、16=23、18=22、19=23、28=30）。
- `figure-types.json`：+29 条登记（总 543），每章仍满足 concept+technical+
  (triage|comparison) 覆盖。
- 既有 zh 分布门、锚点下限、双语序列门均未放宽。

## 验证命令与结果

```bash
python -m pytest stm32-book/tests -q                 # 197 passed（527.81s）
python tools/check_assets.py                         # SVG 541/541、链接 2234/2234；海报 pixel-diff SKIP（缺 WQY 字体，既有）
python stm32-book/build_html.py --check              # zh PASS（29 章）
python stm32-book/build_html.py --lang en --check    # en PASS（29 章）
python tools/slop_lint.py                            # 干净
git diff --check                                     # 0
```

成书（串行）：

| 产物 | 结果 |
|---|---|
| zh PDF | 538 p |
| en PDF | 568 p |
| EPUB zh/en | 各 49 spine、650 images、errors=0 |

版式门（`tools/audit_pdf_layout.py`，命令行同 CI）：

| 门 | 结果 |
|---|---|
| zh | gaps>150pt=144/145、≥250pt=11/15、硬缺陷 0、anchors[min=11 max_free=4] → **exit 0** |
| en（本地 Windows） | gaps>150pt=131/145、≥250pt=18/15、硬缺陷 0、anchors[min=11 max_free=4] → exit 1（≥250pt 超 3 页） |
| en（CI Ubuntu） | 见 PR checks（run ID 回填） |

本地 en 超线与 B51 记录的平台分页噪声同型（同提交 Windows 16 vs CI Ubuntu 12）：
18 个 ≥250pt 页均无溢出/孤行硬缺陷，抽样 p270/p271/p191/p432/p464/p516 渲染目检为
既有「下一不可拆块（表/图/代码）放不下」推页模式，图块自身未溢出。合并门以 CI 为准，
未改图宽凑本地页数。

## 页样目检

- zh PDF：p75（04）、p195（11）、p210（12）、p249（15）、p261（16）、p294（18）、
  p317（19）、p464（28）——图注完整、无孤行/溢出，四问齐全。
- en PDF：p270/p271/p191/p432/p464/p516——版式正常，缺口归因见上节。

## 遗留

- en 其余 13 章 >2,000（B55 候选，spec §8）。
- 本地 en ≥250pt 18 > 15 按 B51 平台噪声条款交 CI 门判定。

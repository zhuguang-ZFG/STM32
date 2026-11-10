# B56 · 英文无图区间收口（en 第三梯队 5 章 ≤2,000）

日期：2026-11-11 ｜ 分支：`improve/b56-en-gap-close`（基于 `main` @ `9108afe`）｜ 依据：B55 收口报告 §遗留、`BOOK_REDESIGN_SPEC.md` §6.3/§11、B51 平台分页噪声条款

## 范围与产物

- 5 章：02/03/07/24/27——B55 报告 §遗留列出的英文侧最后 5 章（2,228–2,030）。
- 8 张 Handraw 知识轨图（02/07/24 各 2；03/27 各 1），每张 zh/en 同序嵌入、
  共用同一 PNG，全部标注「原理示意 / 非实拍」，图题保留四问（看哪里 / 证明什么 / 不能证明什么 / 出处）。
- 图与正文事实一一对应：只画本章已写的事实，不复制相邻表格、不引入测量或实拍证据。
- 正文只插入、不改写：`git diff --numstat` docs 10 文件 **+80 / −0**（16 处嵌入块 × 5 行）。
  新增资产 8 对 PNG/SVG，生成器 `tools/handraw_track/fig_ch{02,03,07,24,27}.py` 固定 seed 可重建；
  嵌入由 `tools/handraw_track/embed_b56.py` 完成（`embed.embed_after_text`，锚点全行唯一）。

| 章 | 新增图 | 类型 |
|---|---|---|
| 02 | ch02-part-funnel、ch02-clock-gate | concept ×2 |
| 03 | ch03-debounce-recheck | technical |
| 07 | ch07-pin-owner、ch07-two-owners | triage、comparison |
| 24 | ch24-migrate-boundary、ch24-slow-meter | triage、calculation |
| 27 | ch27-udp-tcp-contract | comparison |

## 逐章前后（`audit_book` `max_visual_gap_chars`）

| 章 | en 前 | en 后 | zh 前 | zh 后 | 锚点前→后（zh=en） |
|---|---:|---:|---:|---:|---:|
| 02 | 2,228 | **1,699** | 1,171 | 927 | 20→22 |
| 03 | 2,153 | **1,872** | 1,035 | 921 | 19→20 |
| 07 | 2,142 | **1,979** | 1,102 | 1,095 | 16→18 |
| 24 | 2,100 | **1,683** | 1,082 | 872 | 19→21 |
| 27 | 2,030 | **1,840** | 1,102 | 1,102 | 20→21 |

- 5 章 en 全部 ≤2,000（最大 1,979）；zh 全部 ≤1,102，无回退，zh 1,200 分布门未放宽。
- 双语 parity：5 章 zh/en `asset_sequence_equal=true`，锚点数 zh=en，其余结构门全过。
- **全书 en >2,000 清零**：29 章最大为 1,991（ch00），其次 1,983（ch23）；其余命中仅
  `README/CONTENT_GUIDE/contents` 三个元文件，不在章节预算内。

## 测试锁

- `test_book_audit.py`：`EN_GAP_BATCH_BUDGETS` 由 B55 的 16 章扩到 **21 章**（新增 02/03/07/24/27，
  各 2,000）；受影响章 `asset_sequence` 重钉（03=21、07=18、24=21、27=21）；
  `test_chapter_24_has_matching_structure_and_visual_distribution` 的 `pdf_visual_anchors` 19→21。
- `test_advanced_visuals.py` `CHAPTERS`：3 章 `<img>` 元组重钉（03=21、24=22、27=21；
  ch02/ch07 不在该表）。
- `figure-types.json`：+8 条登记（560→568），类型覆盖 concept/technical/triage/comparison/calculation；
  各章 concept+technical+(triage|comparison) 覆盖门不变。
- 既有 zh 分布门、锚点下限、双语序列门均未放宽。

## 验证命令与结果

```bash
python -m unittest discover -s stm32-book/tests -p 'test_*.py'   # Ran 197 tests, OK（416.18s）
python tools/slop_lint.py                                        # 干净
python stm32-book/build_html.py --check                          # zh PASS（29 章）
python stm32-book/build_html.py --lang en --check                # en PASS（29 章）
python tools/check_assets.py                                     # 链接 2284/2284、照片 5/5、示例 OK
git diff --check                                                 # 0
```

成书（串行）：

| 产物 | 结果 |
|---|---|
| zh PDF | 545 p |
| en PDF | 581 p |
| EPUB zh/en | 各 49 spine、675 images、errors=0 |

版式门（`tools/audit_pdf_layout.py`，命令行同 CI）：

| 门 | 本地（Windows） | CI（Ubuntu） |
|---|---|---|
| zh | 545p、gaps>150pt=136/145、≥250pt=**9/15**、硬缺陷 0、anchors[min=11 max_free=4] → **exit 0** | 待 CI 回填 |
| en | 581p、134/145、≥250pt=20/15、硬缺陷 0、anchors[min=11 max_free=4] → exit 1 | 待 CI 回填 |

- 本地 en ≥250pt=20 与 B55 完全同数（20），B51（本地 16 vs CI 12）、B54（18 vs 11）、
  B55（20 vs 12）同型，属 Windows/Ubuntu 分页差异；合并门以 CI 为准，未改图宽/图位凑本地页数。

## 本地 en 超线归因

20 个 ≥250pt 页：P5、P44、P62、P112、P113、P137、P183、P199、P280、P281、P312、
P319、P320、P359、P444、P457、P459、P472、P477、P529。

- 8 张新图落在 en PDF：P47/P58（02）、P75（03）、P133/P138（07）、P428/P429（24）、P473（27）。
  经图题唯一短语全文定位，8 页本身无一在 ≥250pt 清单内。
- 相邻页 3 处：P137（07 两图块之间，`HAL_Delay`/表后图块推到下页）、P472（ch27 图块推前留下）、
  P477；均为「图块不可拆分被推到下一页」的既有同型，与 B55 的 P47/P132/P473 同构——
  其中 P47、P132（B55 存量）在插入新图后已不再超线。
- 其余 17 页为既有图文表混排页的分页漂移（章末/FAQ/网络章各 2–3 页），集合由 B55 清单
  随 +4 页整体后移（-3 平移匹配 11/20，其余为递增偏移）。
- 合并门以 CI 为准；若 CI en ≥250pt 超 15 再单独归因，不在本波预调图。

## 页样目检

- zh PDF：p45/p57（02）、p72（03）、p128/p132（07）、p401/p402（24）、p445（27）——
  图注完整、四问齐全、徽标在位、无孤行/溢出。
- en PDF：P47/P58（02）、P75（03）、P133/P138（07）、P428/P429（24）、P473（27）——
  版式正常，断页归因见上节。

## 遗留

- 无新增章节 gap 任务：en 全书 29 章已全部 ≤2,000。
- 本地 en ≥250pt 20 > 15 沿用 B51/B54/B55 结论：以 CI 数为准，不改图宽/图位。

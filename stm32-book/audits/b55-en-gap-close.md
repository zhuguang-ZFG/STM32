# B55 · 英文无图区间收口（en 第二梯队 8 章 ≤2,000）

日期：2026-11-11 ｜ 分支：`improve/b55-en-gap-close`（基于 `main` @ `ae78f26`）｜ 依据：B54 收口报告 §遗留、`BOOK_REDESIGN_SPEC.md` §6.3/§11、B51 平台分页噪声条款

## 范围与产物

- 8 章：09/17/08/14/05/13/20/10——B54 报告 §遗留列出的英文侧第二梯队（2,544–2,234）。
- 17 张 Handraw 知识轨图（09/17 各 4；08/14/10 各 2；05/13/20 各 1），每张 zh/en 同序嵌入、
  共用同一 PNG，全部标注「原理示意 / 非实拍」，图题保留四问（看哪里 / 证明什么 / 不能证明什么 / 出处）。
- 图与正文事实一一对应：只画本章已写的事实，不复制相邻表格、不引入测量或实拍证据。
- 正文只插入、不改写：`git diff --numstat` docs 16 文件 +204 / −0（其中 30 处为插入块后补空行，
  防止 GFM 把后续段落/标题吸入 HTML 块）。新增资产 17 对 PNG/SVG，生成器
  `tools/handraw_track/fig_ch{05,08,09,10,13,14,17,20}.py` 固定 seed 可重建；
  嵌入由各章 `embed_b55_chNN.py` 完成（`embed.embed_after_text`，锚点全行唯一）。

| 章 | 新增图 |
|---|---|
| 05 | ch05-timer-ladder |
| 08 | ch08-id-assembly、ch08-page-write-flow |
| 09 | ch09-part-scope、ch09-tconv-floor、ch09-evidence-lanes、ch09-mode-stops |
| 10 | ch10-goal-evidence、ch10-two-level-bind |
| 13 | ch13-remap-decision |
| 14 | ch14-usb-can-conflict、ch14-transfer-pick |
| 17 | ch17-stack-frame、ch17-comp-pools、ch17-recover-ladder、ch17-fault-record |
| 20 | ch20-exit-kit |

## 逐章前后（`audit_book` `max_visual_gap_chars`）

| 章 | en 前 | en 后 | zh 前 | zh 后 | 锚点前→后（zh=en） |
|---|---:|---:|---:|---:|---:|
| 09 | 2,544 | **1,880** | 1,159 | 799 | 20→24 |
| 17 | 2,531 | **1,923** | 1,138 | 907 | 18→22 |
| 08 | 2,481 | **1,752** | 1,172 | 910 | 18→20 |
| 14 | 2,454 | **1,878** | 1,128 | 946 | 18→20 |
| 05 | 2,333 | **1,860** | 1,123 | 913 | 19→20 |
| 13 | 2,297 | **1,762** | 1,183 | 980 | 18→19 |
| 20 | 2,293 | **1,733** | 1,065 | 780 | 18→19 |
| 10 | 2,234 | **1,930** | 1,138 | 964 | 17→19 |

- 8 章 en 全部 ≤2,000（最大 1,930）；zh 全部 ≤980，无回退，zh 1,200 分布门未放宽。
- 双语 parity：8 章 `asset_sequence_equal=true`，h2/h3/表/代码/公式 delta 全 0，
  PDF 锚点 delta 0。
- 全书剩余 en >2,000：02=2228、03=2153、07=2142、24=2100、27=2030，留作 B56。

## 测试锁

- `test_book_audit.py`：`EN_GAP_BATCH_BUDGETS` 由 B54 的 8 章扩到 16 章（新增 05/08/09/10/13/14/17/20，
  各 2,000）；受影响章 `asset_sequence` 重钉（05=20、08=20、09=24、10=19、13=19、14=20、17=22、20=19）。
- `test_advanced_visuals.py` `CHAPTERS`：7 章 `<img>` 元组重钉（05=20、09=24、10=19、13=19、
  14=20、17=22、20=19；ch08 不在该表）。
- `figure-types.json`：+17 条登记（543→560），类型覆盖 concept/technical/comparison/calculation/triage；
  各章 concept+technical+(triage|comparison) 覆盖门不变。
- 既有 zh 分布门、锚点下限、双语序列门均未放宽。

## 验证命令与结果

```bash
python -m unittest discover -s stm32-book/tests -p 'test_*.py'   # Ran 197 tests, OK（432.54s）
python tools/slop_lint.py                                        # 干净
python stm32-book/build_html.py --check                          # zh PASS（29 章）
python stm32-book/build_html.py --lang en --check                # en PASS（29 章）
python tools/check_assets.py                                     # 链接 2268/2268、照片 5/5、示例 OK
git diff --check                                                 # 0
```

- slop-lint 曾命中 ch20 英文图题的 `source cards`（结构行话），已改为 `manual entries`，未动图意。

成书（串行）：

| 产物 | 结果 |
|---|---|
| zh PDF | 541 p |
| en PDF | 577 p |
| EPUB zh/en | 各 49 spine、667 images、errors=0 |

版式门（`tools/audit_pdf_layout.py`，命令行同 CI）：

| 门 | 本地（Windows） | CI（Ubuntu） |
|---|---|---|
| zh | 541p、gaps>150pt=130/145、≥250pt=8/15、硬缺陷 0、anchors[min=11 max_free=4] → **exit 0** | 待回填 |
| en | 577p、132/145、≥250pt=20/15、硬缺陷 0、anchors[min=11 max_free=4] → exit 1 | 待回填 |

## 本地 en 超线归因（B51/B54 同型平台噪声）

20 个 ≥250pt 页：P5、P44、P47、P62、P111、P112、P132、P180、P196、P277、P278、P309、
P316、P317、P356、P441、P454、P456、P473、P525。

- 用 17 张新图题的唯一短语在 en PDF 全文定位：新图落在 P98（05）、P146/P153（08）、
  P159/P162/P163/P167（09）、P181/P183（10）、P228（13）、P246/P249（14）、
  P297/P300/P310/P312（17）、P367（20）。
- 这 17 页无一在 ≥250pt 清单内；最接近的是 P159=186pt、P181=226pt，均在阈值下。
  即本地 en 超线不由 B55 新增图造成。
- 20 页中 6 页以既有老图块为首块（P62/P112/P278/P317/P356/P456），其余为图文表混排页的
  分页漂移；与 B51（同提交 Windows 16 vs Ubuntu 12）、B54（18 vs 11）同型。
- 合并门以 CI 为准，未改图宽/图位凑本地页数。

## 页样目检

- zh PDF：p94（05）、p141/p148（08）、p153/p155/p156/p160（09）、p171/p173（10）、
  p215（13）、p233/p235（14）、p279/p282/p291/p293（17）、p345（20）——图注完整、
  四问齐全、无孤行/溢出。
- en PDF：P98、P146、P153、P159、P162、P163、P167、P181、P183、P228、P246、P249、
  P297、P300、P310、P312、P367——版式正常，缺口归因见上节。

## 遗留

- en 其余 5 章 >2,000（B56 候选：02=2228、03=2153、07=2142、24=2100、27=2030）。
- 本地 en ≥250pt 20 > 15：按 B51 平台噪声条款处理，CI 结果回填后定论；
  若 CI 超线，先按上节 20 页清单逐页归因，不动 B55 图。

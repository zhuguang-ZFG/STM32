# B49 · 长无图区间收口（第二批：ch12/16/18/23/24/28）

日期：2026-11-10 ｜ 分支：`improve/b49-gap-figures-2`（基于 27193a2 = B48）｜ 计划：`docs/superpowers/plans/2026-11-08-book-visual-experience.md` B46–B51

## 目标

B48 收口 ch13/26/27 后，剩余六章 zh `max_visual_gap_chars` > 1200。本批全部用「回答正文问题」的 Handraw 知识轨新图收口，不做装饰图；zh/en 同序列嵌入；无图区间 ≤1200 或登记例外。

## 基线 → 终态（zh，官方 audit）

| 章 | 基线 gap | 终态 gap | 区间端点（终态） | 新图 |
|---|---|---|---|---|
| ch12 | 1716 | **1194** | 关键插图 → 2. 解锁与编程流程 | ch12-ymodem-flow、ch12-option-bytes |
| ch16 | 1568 | **1127** | 3. STOP 唤醒后时钟恢复 → 7. 低功耗设计检查清单 | ch16-no-ammeter-check、ch16-cell-triage |
| ch18 | 1870 | **1131** | 章首 → 时序与状态 | ch18-peripheral-triage |
| ch23 | 1844 | **1082** | 章首 → BOOT0 与 SWCLK 共脚：先判定启动来源 | ch23-swd-triage、ch23-lab-evidence |
| ch24 | 2149 | **1082** | 动手实验 → 章末 | ch24-irq-order、duty-integration、two-firmware |
| ch28 | 2198 | **1090** | 看门狗必须由健康监督者喂 → 常见失败模式 | ch28-isr-divergence、h745-contracts、experiment-evidence、review-evidence |

全部 ≤1200，无例外登记。parity 六章全 True（zh/en 同序列同位置插入，delta 全 0）。

附带消除：ch16 基线次区间 1543（gif→stop-compare）由 ch16-cell-triage 顺带收口；ch24 原两处 1212/2149 全部消除。

## 新图清单（14 张，全部 Handraw · 原理示意/非实拍）

| 图 | 章 | type | 回答的正文问题 |
|---|---|---|---|
| ch12-ymodem-flow | 12 | technical | YMODEM 谁先说话、卡住先查什么 |
| ch12-option-bytes | 12 | comparison | F1 vs F4 选项字节档位与两条不可逆边界 |
| ch16-no-ammeter-check | 16 | technical | 无电流表时如何用 UART 位宽判决唤醒与时钟恢复 |
| ch16-cell-triage | 16 | triage | 「2~3 µA」合并格子的四行前提 |
| ch18-peripheral-triage | 18 | triage | 九条 P 条目各先做哪项区分原因的测量 |
| ch23-swd-triage | 23 | triage | SWD 失联先取证还是先改选项字节（RDP 三分支） |
| ch23-lab-evidence | 23 | technical | 离开本章必须带走的四份工件 |
| ch24-irq-order | 24 | technical | 为什么 callback 里再读 WUTF 已太晚 |
| ch24-duty-integration | 24 | calculation | I_avg 是电荷/周期，不是两电流算术平均 |
| ch24-two-firmware | 24 | comparison | 功能固件与测量固件为何不能互相冒充 |
| ch28-isr-divergence | 28 | triage | ISR 到任务的事件丢失先在哪道闸门分流（6 门） |
| ch28-h745-contracts | 28 | technical | H745 双机通道五层契约各冻结什么、注入什么 |
| ch28-experiment-evidence | 28 | technical | 四组递进实验各自交什么可验收证据 |
| ch28-review-evidence | 28 | comparison | 选型评审十条如何收敛成四条证据线 |

图注四要素齐全（看哪里 / 证明什么 / 不能证明什么 / 出处）；出处锚点全部为 manifest 已有 source id（含 ch12 的 `#source-rm0090`，已核验 manifest 存在）。

## 移图（3 处）

- ch23 `sample-23-boot-source-flow.svg`：`### 共脚硬件` 标题下 → 三条硬件事实 bullets 后。
- ch23 `ch23-pinmux.png`：F1 抄代码陷阱表之前 → 陷阱表之后、`## 动手实验` 之前。
- ch28 `ch28-memory-regions.png`：章末 → `ch28-isr-divergence.png` 之后（与其六闸门内容衔接）。

## 测试锁（集成者统一更新，均为等值重钉）

- `test_advanced_visuals.py`：ch12 16→18、ch16 16→18、ch18 15→16、ch23 14→16、ch24 17→20、ch28 22→26，元组按文档序插入新名。
- `test_book_audit.py`：`expected[12/16/18/23/24/28]` 资产序按文档序重排（含 3 处移图）；ch24 `pdf_visual_anchors` 16→19。
- `figure-types.json`：+14 条新登记。

## 验证记录

- 锁模块 `pytest tests/test_advanced_visuals.py tests/test_book_audit.py`：**20 passed**。
- `tools/check_assets.py`：全部通过，2120/2120 链接、照片 5/5。
- `tests/test_slop_lint.py` + `tests/test_handraw_track.py`：21 passed。
- 官方 audit（.temp/book-audit-b49-final.json）：六章 anchors 18/18/16/16/19/25，deficit 0，parity 全 True。
- `build_html.py --check --lang zh`：PASS；`--lang en`：PASS。
- 全量 `pytest`（stm32-book）：**195 passed**（361.6s）。

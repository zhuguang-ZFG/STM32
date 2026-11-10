# B48：ch13/26/27 长无图区间收敛

日期：2026-11-10。基线 `7ab575b`（B46 合并）。计划见
`docs/superpowers/plans/2026-11-08-book-visual-experience.md`。

## 发现

B48 基线（`python tools/audit_book.py`，阈值：无图区间 ≤1200 字）：

| 章 | chars | 最长无图区间 | 区间 |
| --- | ---: | ---: | --- |
| ch13 CAN | 6269 | 2566 | 关键插图 → 5. 波特率 |
| ch26 SPL | 9190 | 2438 | §7 DMA → 章末 |
| ch27 网络 | 10893 | 2585 | 分层排错 → 章末 |

三章 deficit 均为 0，超长的全部是「图间距」问题，不是缺图总量问题。

## 改动

新图 6 张（全部 handraw 轨，`tools/handraw_track/fig_ch13.py` /
`fig_ch26.py` / `fig_ch27.py` 新增生成函数，确定性可重建）：

| 图 | 章 | 类型 | 回答的正文问题 |
| --- | --- | --- | --- |
| ch13-diff-levels | 13 | technical | 物理层速率与长度经验怎么分档 |
| ch13-data-frame | 13 | technical | 四种帧类型与 ID 位宽怎么选 |
| ch13-pitfall-triage | 13 | triage | 七个常见现象各自的第一处边界与出处 |
| ch26-dma-wiring | 26 | technical | SPL 的 USART+DMA 要亲手接哪三件事 |
| ch27-at-offload | 27 | concept | AT 模组移走 TCP/IP 后 MCU 必须保留什么状态 |
| ch27-sendall-loop | 27 | technical | send_all 的单一截止点与四个出口语义 |

移图 3 处（不改资产集，只改落点）：

- `ch26-migrate-steps.png`：§9 五步列表后 → §9 末尾「什么时候迁到 HAL/LL」之后（recap 位，拆 §9→章末 1972 字）。
- `ch27-lab-ladder.png`：§四个递进实验 开头 → 实验 D 之后（recap 位）。
- `sample-26-spl-hal-compare.svg` + `ch26-spl-hal.png`：§4 末尾 → §5 开头（两图内容就是 §5 主题「HAL、SPL 与寄存器怎样对上」；拆 §4 尾 → 轮询的 1322 字区间）。

图注全部四要素（看哪里 / 证明什么 / 不能证明什么 / 出处），zh/en 同序列同步嵌入。
`figure-types.json` 登记 8 条（6 新 + dma-wiring/at-offload 上文已列；
另 2 条为 ch26-call-chains=comparison、ch27-four-ledgers=calculation 同批登记）。
测试锁：`test_advanced_visuals.py` ch13 15→18、ch26 15→18、ch27 16→20；
`test_book_audit.py` asset_sequence 同步。

## 前后对比

| 章 | 锚点前 | 锚点后 | 最长区间 前 | 后 | 判定 |
| --- | ---: | ---: | ---: | ---: | --- |
| ch13 | 15 | 18 | 2566 | 1183（章首→时序与状态） | ✓ |
| ch26 | 15 | 18 | 2438 | 1231（§5→§6，见例外） | 例外登记 |
| ch27 | 16 | 20 | 2585 | 1102（章首→2. link LED） | ✓ |

三章 parity（asset_sequence_equal）全程 True。

## 例外登记（B2/B3 先例）

ch26 §5→§6 区间 1231 字，超阈值 31 字（2.6%）。

- 区间内容：17 行 HAL↔SPL 寄存器对照表正文 + 小节标题，非连续散文；
  读者面对的是参考表，表本身就是视觉锚。
- 两端锚点：左 §5 头 compare 双图（sample-26-spl-hal-compare.svg +
  ch26-spl-hal.png），右 §6 头中断双图（nvic-interrupt-flow.svg +
  ch26-irq-no-callback.png）。
- 一对一补偿锚点：区间右端 `### 轮询必须自己带超时` 的
  timeout-poll 双图（sample-26-timeout-poll.svg + ch26-timeout-poll.png）。
- 不采用「再插一张图」的原因：表中部无正文问题可答，装饰图违反
  「回答正文问题」原则；不采用删表行的原因：表是 §5 的交付物。

## 验证

- 审计：`python tools/audit_book.py --format json --write .temp/book-audit-b48.json`，
  终值见上表；parity True ×3。
- 测试：pytest 全量（见提交信息内计数）；定向 test_advanced_visuals /
  test_book_audit 随锁更新通过。
- 资产：`python tools/check_assets.py` 全部通过（2092/2092 链接有效）。
- 构建：`build_html.py --check --lang zh|en` 均 PASS。
- 文风：`slop_lint.py` 干净。

# B3 收敛门审计（ch06–ch10）

状态：通过。日期 2026-11-04。基线：B2 提交 `486adee`。批次：spec §10.2 批次三（ch06、ch07、ch08、ch09、ch10）。
配套：`audits/b2-converge-gate.md`（本批随附两处历史修正，见 §12）。

## 1. 前置与门验总览

| 门项 | 结果 |
|---|---|
| audit zh（deficit / parity） | 0 / 5 章 True |
| audit en（deficit / parity） | 0 / 5 章 True |
| check_assets | SVG 190/190 合法；链接 1,336/1,336 有效 |
| build_html | zh check PASS（6,394,277 bytes，29 章）；en 构建成功（6,447,375 bytes） |
| pytest 全量 | 178 passed（68.97s，0 failed） |
| 生成器确定性 | 7/7 图重生成字节一致（idle-dma 修正后单独复核，见 §4） |

工具口径：`python tools/audit_book.py --format json --write <path>`（cwd=仓库根）；`python tools/check_assets.py`；`python build_html.py --check --lang zh` / `--lang en`（cwd=stm32-book/）。

## 2. 改章前缺陷清单（基线 486adee）

audit chars 为含代码口径（§15.2 分档依据）。

| 章 | chars | 档位（旧/overlay） | 基线锚点 | 目标 | 缺陷 |
|---|---|---|---|---|---|
| ch06 串口UART | 6,930 | 中章 4/6 | 4 | 6 | 锚点低于 overlay 2；无排错图；§2–§5 无图走廊 |
| ch07 I2C总线 | 3,246 | 短章 3/4 | 4 | 4 | 锚点达标；三类型缺排错；UM10204 仅纯文本提及（例外登记 §7） |
| ch08 SPI总线 | 5,275 | 短章 3/4 | 3 | 4 | 锚点低于 overlay 1；缺对比与排错两类型 |
| ch09 ADC与DAC | 8,621 | 中章 4/6 | 5 | 6 | 锚点低于 overlay 1；OSS 卡含 libopencm3（GPL-3.0，违反许可门） |
| ch10 DMA | 7,276 | 中章 4/6 | 5 | 6 | 锚点低于 overlay 1；最大无图区间 2,677（§1–§2） |

## 3. 本批交付

新增 7 张自绘 SVG（生成器 `tools/sample_figs_b3/`，svgkit 复用 `tools/svgkit.py`），zh/en 双语嵌入，共 14 处：

| 图 | 类型 | zh 落点 | en 落点 |
|---|---|---|---|
| sample-06-baud-triage | 排错 | 06-串口UART.md L143 | 06-uart.md 同段 |
| sample-06-idle-dma | 概念 | 06-串口UART.md L337 | 06-uart.md 同段 |
| sample-07-i2c-triage | 排错 | 07-I2C总线.md L352 | 07-i2c.md 同段 |
| sample-08-cpha-modes | 对比 | 08-SPI总线.md L129 | 08-spi.md 同段 |
| sample-08-spi-triage | 排错 | 08-SPI总线.md L341 | 08-spi.md 同段 |
| sample-09-adc-triage | 排错 | 09-ADC与DAC.md L316 | 09-adc-dac.md 同段 |
| sample-10-dma-triage | 排错 | 10-DMA.md L150 | 10-dma.md 同段 |

终态锚点：ch06 6、ch07 5、ch08 5、ch09 6、ch10 6——五章 deficit=0，zh/en asset_sequence_equal 均 True。

图注 credit 沿用章级引用惯例（如「RM0008 Rev 21 第 27 章」），不使用未经核实的 §小节号；ch07 图注仅链接 `#source-rm0008-i2c`。

数据校准（沿既有图注口径）：USART1@72 MHz BRR=0x271 误差 0；USART2@36 MHz BRR=0x138 +0.16%；SPI1@72 MHz BR=010→9 MHz；ADC 时钟 12 MHz、最长转换 21 µs、1.5 周期采样=125 ns；I2C 写地址 HAL 口径 0x78 vs 原样送出 0x3C（36 MHz 下表 42 的 400 kHz 行=0x801E）。

## 4. idle-dma 公式修正（review blocker 闭环）

review 发现：CIRC=1 下 `len = 256 − CNDTR` 从第二帧起累计错误。修正为 `len = pos − CNDTR`（pos 为上一帧 ISR 保存的 CNDTR，回卷再加 256），与正文 zh L338「CNDTR 差值」行文及 en L281 HAL 示例（subtract the previous one）一致。CIRC=0 语义不变（图即环形缓冲）。

- 生成器 `ch06_b3.py` L118 同步；docstring 目录名笔误 `sample_figs_b2`→`sample_figs_b3`。
- SVG 仅 L43 一行变化（等长替换，bytes 仍 15,348）；zh L338、en L338 正文同步。
- text_hash 更新：`8a0b80e12adc2e955f0105a482b40b4f8c997752424ad1b542b6b77021d5448f`；`test_sample_svg_c.py` L113 与 `.temp/b3-hashes.json` 同步。
- 修正后全模块重生成复核：6/7 与修正前备份字节一致，idle-dma 仅预期单行 diff；提交前对 idle-dma 单独全新重生成 → 与待提交 SVG 字节一致（7/7 成立）。

## 5. 三类型归属（§15.1-23）

| 章 | 概念 | 对比 | 排错 |
|---|---|---|---|
| ch06 | uart-frame.svg（帧结构动画）、idle-dma（IDLE+DMA 通路） | sample-06-uart-frame（正常采样 vs「失败路径：停止位三点采到 0」双路径块） | baud-triage（乱码/无输出/丢字节三岔口） |
| ch07 | i2c-transaction.svg（收发事务动画） | sample-07-i2c-addr（0x78 HAL 口径 vs 0x3C 原样送出） | i2c-triage（SDA 卡低/NACK/SCL 不动） |
| ch08 | spi-transfer.svg（全双工交换动画） | cpha-modes（CR1 两位四种模式两轴对比） | spi-triage（全 0xFF/无时钟/高 BR 出错） |
| ch09 | adc-sar.svg、sar-adc.gif（SAR 原理动画） | sample-09-adc-sar（正常采样 vs 失败路径：采样太短电容保持旧值） | adc-triage（末位抖动/顶满贴零/整体偏置） |
| ch10 | dma-buffer-ownership（谁能写谁能读的归属模型）、dma-circular.svg | sample-10-dma-cndtr（CNDTR 剩余计数按半字 vs 按字节两种读法，「当成字节会切错」） | dma-triage（CNDTR 不减/数据错位/TC 不进） |

对比归属依据各图 aria 标题与图内结构如实标注：ch10 的 dma-cndtr 两态为「半字/字节两种读法」（非递减/回卷假设）；ch06/ch09 对比图均有显式「失败路径」块。每章可播放动画 ≥1 且均在用（§15.1-24）。

## 6. §15.2 档位与 gap 登记

overlay 后中章单区间上限 1,000；短章行无数值基数，gap 记「—」（§6.3 定性分布）。全量 >1,000 区间枚举（左界=锚点 end，与 audit `_max_visual_gap` 同口径；表不计入锚点）：

| 章 | gap | 区间 | 补偿锚点（区间右端） | 说明 |
|---|---|---|---|---|
| ch06 | 1,464 | 关键插图→2. 波特率与误差 | baud-triage（§2 末） | §1 帧格式双表+§2 误差表连排；**例外登记** |
| ch07 | — | 短章无数值基数 | i2c-triage 切分原 1,901 末区间 | §6.3 定性 |
| ch07 | 1,276 | 章首→时序与状态 | 无新图 | 摘要+学习目标开篇纯文字（B2 ch02 同型 1,243 先例） |
| ch07 | 1,744 | 2. 时序与协议→相关资源 | i2c-triage（自测后） | §3–§9 机制+地址换算代码；**例外登记** |
| ch08 | — | 短章无数值基数 | cpha-modes+spi-triage 双切 | §6.3 定性 |
| ch08 | 1,605 | 关键插图→3. 速率与分频 | cpha-modes（Mode 0 引言后/§3 前） | §1–§2 寄存器+模式表连排；**例外登记** |
| ch08 | 1,575 | 2. CPOL/CPHA 四种模式→相关资源 | spi-triage（§10 表后） | §3–§10 速率表+寄存器+代码；**例外登记** |
| ch09 | 1,449 | 章首→时序与状态 | 无新图 | 开篇纯文字（同 ch07 型） |
| ch09 | 1,979 | 关键插图→3. 四种转换模式 | 无新图（右端为 §3 区既有锚点） | §1–§2 SAR 连续机制叙述，adc-sar 动画已锚定章侧；**例外登记** |
| ch09 | 1,521 | 2. SAR→5. 内部温度 | 无新图 | §3–§4 转换模式+代码；**例外登记** |
| ch09 | 1,841 | 4. 多通道+DMA→8. 通道和引脚 | adc-triage（§7 末） | §5–§7 代码+寄存器表；**例外登记** |
| ch10 | 2,096 | 关键插图→3. 传输方向与工作模式 | dma-triage（§2 末岔口①） | §1–§2 请求映射表连排；原 2,677 已由本批新图切分；**例外登记** |

超限处理：按 B2 先例登记例外，不追加补图。理由：剩余区间均为表格/代码密集走廊，岔口位已落新图；ch10 残差 2,096 的主段是请求映射表连排（表本身即视觉锚）。en gap 3,108–4,600 不入门（B2 先例：双语同步嵌入，英文行宽差异）。

## 7. 许可与出处（§15.3）

每章 ≥1 个 ALLOWED GitHub OSS（manifest sources 注册，zh/en 双 manifest 同步；ALLOWED={ST-facts-restated, MIT, BSD-2/3, ISC, CC BY 4.0/3.0, CC0}）：

| 章 | OSS（license） | 其余 sources |
|---|---|---|
| ch06 | stm32cube-f4、majerle-uart（仓库 LICENSE） | rm0008、st-uart-idle、rm0008-usart、ds5319-usart（ST 条款链接引用） |
| ch07 | project-examples（MIT） | rm0008、ds5319-i2c、rm0008-i2c |
| ch08 | project-examples（MIT） | rm0008、rm0008-spi、ds5319-spi |
| ch09 | project-examples（MIT） | rm0008、ds5319、rm0008-adc、ds5319-adc |
| ch10 | stm32cube-f4、majerle-uart（仓库 LICENSE） | rm0008、st-h7-dma、rm0090、rm0008-dma、ds5319-dma |

ch09 修复：libopencm3（GPL-3.0）违反许可门，弃用；project-examples（MIT）入 ch09 sources，双 manifest 已编辑。GPL/LGPL/Apache-2.0 维持拒绝。

例外：UM10204 在 ch07 为纯文本背景规范提及，未建 source 卡、未复述其表号，登记例外。

## 8. 落点论证

- ch08 双图分布（短章 overlay 4 实达 5）：cpha-modes 落 §2 末（Mode 0 引言块后/§3 前），切分 §1–§2 最长区间（1,643→1,605+46）；spi-triage 落 §10 寄存器表后/相关资源前，切分尾区间（→1,575）。两落点均为语义岔口（模式对比处/排错汇总处）。
- ch10 §2 落点：岔口①即请求映射，切分原最大缺口 2,677；§4 末方案否决——该缺口终点即 dma-buffer-ownership 图，放其后不切缺口。残差 2,096 例外登记（§6）。

## 9. 七图哈希登记

text_hash = sha256(`"\n".join(<text> 内文)`)，非整文件 sha256；与 `test_sample_svg_c.py` 注册表及生成器 `_audit` 输出一致。

| 图 | bytes | text_hash |
|---|---|---|
| sample-06-baud-triage | 9,012 | 9eaf42b59083f53333adf8bef5fce9ac78536d469a0b29fbc77eb793975e73f1 |
| sample-06-idle-dma | 15,348 | 8a0b80e12adc2e955f0105a482b40b4f8c997752424ad1b542b6b77021d5448f（修正后） |
| sample-07-i2c-triage | 15,555 | e883d49128b6ad56b242d8f1178dc70d67f1014bfb42f958c41bf34677d54a1d |
| sample-08-cpha-modes | 18,777 | a8832f9b9717be139e721840e6c634b56218617fdee98684cd53f5365869290e |
| sample-08-spi-triage | 9,199 | b40d75cbc76bf1d00c1bcf6059a6a9acb05148a6a2465e03131bd1dfbbd68be5 |
| sample-09-adc-triage | 11,279 | 3f34454191defda44ef0b893ae5d1584b2ce13c9baa2ade07c54bd31089c8dbe |
| sample-10-dma-triage | 10,284 | 1c7e9f8d07636051dfe5a5d33ddbaa9634b8d9c4968e729c141748fb93e5262d |

## 10. 测试锁

| 文件 | 变更 |
|---|---|
| tests/test_batch3_chapters.py | 五章锚点计数与嵌入锁（更新） |
| tests/test_sample_svg_c.py | 7 图注册表；L113 idle-dma hash fc062c60→8a0b80e1（更新） |
| tests/test_book_audit.py | B3 门验契约扩展（+35/−4，更新） |
| tests/test_advanced_visuals.py | 交集覆盖（+6/−2，更新） |
| tests/test_batch3_sources.py | 既有锁，未改（ch09 OSS 卡断言沿用 2026-10-25-batch3 fixtures） |

## 11. 验证记录

- `.temp/b3-audit-after.json`：zh/en deficit 0；ch06–10 parity True（h2/h3/table/code/formula delta 全 0）；zh 锚点 6/5/5/6/6。
- check_assets：SVG 190/190 合法；链接 1,336/1,336 有效。海报字体 SKIP（wqy-microhei 未装，长期记账项，NARRATED_FONT 可恢复）。
- build_html：zh `--check` PASS（6,394,277 bytes，29 章）；en 构建成功（6,447,375 bytes）。
- pytest 全量：178 passed（68.97s，0 failed）。
- 生成器重生成：7/7 字节一致（含 idle-dma 修正后单独复核，§4）。
- `task_verify` 持续 `project-or-git-baseline-unavailable`（长期记账，无实际阻塞；本轮测试变更按规则待人工评审后于下轮成为基线）。

## 12. B2 文档随批修正

`audits/b2-converge-gate.md` 两处：ch01 锚点历史（5→7→9 补全）与 Sepia 段锁（7→9），随本批提交。

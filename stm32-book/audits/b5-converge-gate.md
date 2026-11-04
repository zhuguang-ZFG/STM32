# B5 收敛门审计（ch18–ch22）

状态：通过。日期 2026-11-04（America/Adak）。基线：B4 合流后 42a83a8（B1–B4 已推）。批次：spec §10.3 批次五（ch18、ch19、ch20、ch21、ch22）。

## 1. 前置与门验总览

| 门项 | 结果 |
|---|---|
| audit zh（deficit / parity） | 0 / 5 章 True |
| audit en（deficit / parity） | 0 / 5 章 True |
| check_assets | SVG 208/208 合法；链接 1,372/1,372 有效；照片 3/3 |
| build_html | zh check PASS（6,710,479 bytes，29 章）；en check PASS（6,764,710 bytes，29 章） |
| pytest 全量 | 179 passed（86.67s，0 failed） |
| slop_lint | 干净：没有机械命中 |
| 生成器确定性 | 7/7 图重生成字节一致 |

工具口径：python tools/audit_book.py --format json --write .temp/b5-audit-final.json（cwd=仓库根）；python tools/check_assets.py；python tools/slop_lint.py；python build_html.py --check --lang zh|en（cwd=stm32-book/）。

## 2. 改章前缺陷清单（基线 42a83a8 / .temp/b5-audit-baseline.json）

audit chars 为含代码口径（§15.2 分档依据）。基线旧表 target 3/4/4/4/3 全达标（deficit=0），缺陷在 overlay 档、gap、类型三轴与动画覆盖。

| 章 | chars | 档位（旧/overlay） | 基线锚点 | overlay 目标 | 缺陷 |
|---|---|---|---|---|---|
| ch18 常见问题FAQ | 5,405 | 短章 3/4 | 3 | 4 | 低于 overlay 1；缺五域对比；最大区间 4,310（关键插图→章末，超 ch18 3,500） |
| ch19 项目实战合集 | 8,752 | 中章 4/6 | 7 | 6 | 锚点已超 overlay；缺里程碑/范围排错类型；最大区间 1,875 |
| ch20 学习资源与工具链 | 6,227 | 中章 4/6 | 5 | 6 | 低于 overlay 1；无机制动画；缺证据阶排错图；最大区间 1,437 |
| ch21 原理图与实物图鉴 | 6,487 | 中章 4/6 | 8 | 6 | 锚点已超；缺三板对照与上电→SWD 机制动画；最大区间 2,291 |
| ch22 仿真 Wokwi/Renode | 3,274 | 短章 3/4 | 4 | 4 | 锚点达标；缺仿真三岔口排错；wokwi/renode 出处许可证表述含糊 |

## 3. 本批交付

新增 **7** 张自绘 SVG（生成器 	ools/sample_figs_b5/，svgkit 复用 	ools/svgkit.py），zh/en 双语嵌入，共 14 处：

| 图 | 类型 | zh 落点 | en 落点 |
|---|---|---|---|
| sample-18-faq-compare | 对比 | 18-常见问题FAQ.md 「三、外设」前 | 18-faq.md 「3. Peripherals」前 |
| sample-19-milestone-triage | 排错 | 19-项目实战合集.md 「动手实验」前 | 19-projects.md hands-on 前 |
| sample-20-lookup-flow | 概念/机制动画 | 20-学习资源与工具链.md 「遇到问题时去哪找证据」后 | 20-resources.md 同段 |
| sample-20-evidence-triage | 排错 | 「常见坑与排查」前 | traps 前 |
| sample-21-board-compare | 对比 | 21-原理图与实物图鉴.md 「核心原理」后 | 21-board-maps.md Core ideas 后 |
| sample-21-power-swd | 机制动画 | 「硬件与接线」前/段 | Hardware and wiring |
| sample-22-sim-triage | 排错 | 22-仿真… 「仿真替不了的事」前 | What simulation will not… 前 |

终态锚点：ch18 **4**、ch19 **8**、ch20 **7**、ch21 **10**、ch22 **5**——五章 deficit=0，zh/en sset_sequence_equal 均 True。ch18 最大无图区间 4,310→**2,219**（≤3,500）。

图注惯例：zh「▲ 自绘。……出处是 [X](#source-…) …。」en「▲ Drawn for this book. … Sources: …」。动画首帧 PDF 可读；prefers-reduced-motion 由 anim 生成器保留。

## 4. manifest / 出处（§15.3）

- ch20 guides += stlink-tools、project-examples（GitHub OSS）。
- ch21 guides += project-examples。
- ch22 guides += ds5319（ST 官方）；wokwi-bluepill / 
enode-stm32 卡字段被 batch2–4/sample 基线整卡锁死；本批在章内图注写明 MIT 仅链接边界，不改动被锁 license 字段。
- ch18/ch19 基线已含 ST + project-examples，本批未削弱。

## 5. 三类型归属（§15.1-23）

| 章 | 概念 | 对比/关系 | 排错 |
|---|---|---|---|
| ch18 | toolchain-flow（启动/工具链入口） | sample-18-faq-compare（五域第一探针） | sample-18-boot-triage |
| ch19 | peripheral-wiring / flash-fit | dma-buffer-ownership 等关系图 | sample-19-milestone-triage |
| ch20 | sample-20-lookup-flow（订货号→DS/RM/PM/AN） | manual-choice-map / firmware-stack-choice | sample-20-evidence-triage |
| ch21 | sample-21-power-swd（上电→SWD） | sample-21-board-compare（三板五问） | 既有接线/引脚图鉴承担辨认排错 |
| ch22 | simulation-model-boundary | simulator-comparison | sample-22-sim-triage |

## 6. 动画清单（§15.1-24）

| 章 | 可播放机制演示 | 形态 |
|---|---|---|
| ch18 | boot0-low.gif + toolchain-flow.svg | GIF + CSS SVG |
| ch19 | one-slot.gif | GIF |
| ch20 | **sample-20-lookup-flow.svg（本批）** | CSS keyframes SVG |
| ch21 | **sample-21-power-swd.svg（本批）** | CSS keyframes SVG |
| ch22 | toolchain-flow.svg + simulation-acceptance-gates.svg | CSS SVG |

空转动效：无。装饰图：无计入锚点。

## 7. 官方 / 开源对照表（§15.1-27–29）

| 章 | ST 官方 | GitHub OSS（许可） | 边界 |
|---|---|---|---|
| ch18 | rm0008-boot、ds5319-nrst 等 | project-examples（MIT） | 仅对照路径/例程结构 |
| ch19 | ds5319-swd、rm0008-adc 等 | project-examples（MIT） | 例程可复用声明见 CREDITS |
| ch20 | project-credits 链至手册地图；Cube 卡 | stlink-tools（BSD-3-Clause，仅链接）、project-examples（MIT） | 不分发 stlink 源码 |
| ch21 | ds5319 | project-examples（MIT）、project-credits | 板卡 SVG 自绘，非实拍冒充 |
| ch22 | **ds5319（本批补）** | wokwi-bluepill、renode-stm32（manifest 基线锁；图注写明 MIT 仅链接） | 仿真模型边界；真板以 DS 为准 |

## 8. §15.2 终态 floors / gaps

| 章 | 终态锚点 | overlay 目标 | max gap | 备注 |
|---|---|---|---|---|
| ch18 | 4 | 4 | 2,219 | 已压到 ≤3,500 |
| ch19 | 8 | 6 | 1,875 | USB 进阶段仍偏疏，B6 可再插 |
| ch20 | 7 | 6 | 1,437 | 固件库对比→代码实现 |
| ch21 | 10 | 6 | 2,031 | 外设接线总览→章末；板卡照片仍用户自有 |
| ch22 | 5 | 4 | 833 | 短章达标 |

## 9. 阻塞 / 非本批

- PC13 / 板卡实拍仍用户自有（真证轨），本批只用自绘 SVG，不冒充实拍。
- 不启动 B6（ch23+）。

## 10. 测试锁（只增不减）

- 	est_sample_svg_c.py：ROWS +7，len(found)=208；nimations/sample-* 允许 CSS keyframes 且要求「自绘矢量动画」。
- 	est_advanced_visuals.py：ch18/21 新条目；ch19/20/22 资产序列上调。
- 	est_book_audit.py：ch19 序列 + milestone；新增 	est_phase_four_projects_faq_resources_boards_and_sim。

## 11. 门验复跑记录

- check_assets：SVG 208/208 合法；链接 1,372/1,372 有效；照片 3/3 哈希与尺寸匹配；讲解视频 29 章 MP4+SRT 通过。
- build_html：zh `--check` PASS（6,710,479 bytes，29 章）；en `--check` PASS（6,764,710 bytes，29 章）。
- pytest 全量：179 passed（86.67s，0 failed）。
- slop_lint：干净，无机械命中。
- audit_book：ch18–22 deficit=0，zh/en asset_sequence_equal=True；中文 PDF 视觉锚点合计 177。

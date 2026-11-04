# B6 收敛门审计（ch23–ch28 + 附录 F）

状态：通过（本文件随门验复跑定稿）。日期：2026-11-04（America/Adak）。基线：B5 合流 `b98098c`。批次：spec §10.3 批次六（ch23、ch24、ch25、ch26、ch27、ch28；附录 F 开源地图 zh）。

## 1. 前置与门验总览

| 门项 | 结果 |
|---|---|
| audit zh（deficit / parity） | 0 / 6 → True（ch23–28） |
| audit en（deficit / parity） | 0 / 6 → True |
| check_assets | SVG 219/219 合法；链接 1,393/1,393 |
| build_html | zh/en `--check` PASS |
| pytest 全量 | 180 passed |
| slop_lint | 干净 |
| 生成器确定性 | 11/11 图重生成字节一致 |

工具口径：`python tools/audit_book.py --format json --write .temp/b6-audit-final.json`；`python tools/check_assets.py`；`python tools/slop_lint.py`；`python build_html.py --check --lang zh|en`（cwd=`stm32-book/`）。

## 2. 改章前缺陷清单（基线 b98098c / `.temp/b6-audit-baseline.json`）

audit chars 为含代码口径（§15.2 分档依据）。基线旧 target 全达标（deficit=0），缺陷在 overlay 档、gap、类型三轴与附录 F 自绘图：

| 章 | chars | 档位（旧/overlay） | 基线锚点 | overlay 目标 | 缺陷 |
|---|---|---|---|---|---|
| ch23 STM32G0 引脚 | 5,353 | 短章 3/4 | 3 | 4 | 低于 overlay 1；缺 F1→G0 五问对比与 BOOT 锁存机制动画；最大区间 3,884（→章末，超 ch23 3,500） |
| ch24 STM32L4 引脚 | 9,227 | 中章 4/6 | 4 | 6 | 低于 overlay 2；缺模式对照与唤醒排错 |
| ch25 STM32H7 引脚 | 8,990 | 中章 4/6 | 7 | 6 | 锚点已超 overlay；缺 F4→H7 迁移排错类型；最大区间 1,354 |
| ch26 SPL | 6,702 | 中章 4/6 | 5 | 6 | 低于 overlay 1；缺 SPL/HAL 边界对比 |
| ch27 网络与协议栈 | 9,817 | 中章 4/6 | 5 | 6 | 低于 overlay 1；缺链路分层排错 |
| ch28 系统与 RTOS | 12,859 | 长章 6/9 | 7 | 9 | 低于 overlay 2；缺 OS 对照、owner 流机制动画、故障三岔口；最大区间 3,695（超 ch28 3,500） |
| 附录 F 开源地图 | — | 附录（audit_book 未计入） | 0 自绘 | ≥1 | 缺证据层 OSS 地图 |

## 3. 本批交付

新增 **11** 张自绘 SVG（生成器 `tools/sample_figs_b6/`，svgkit 复用 `tools/svgkit.py`），zh/en 双语嵌入（附录 F 仅 zh），共 21 处：

| 图 | 类型 | zh 落点 | en 落点 |
|---|---|---|---|
| sample-23-boot-latch | 概念/机制动画 | 23-STM32G0引脚.md BOOT 段 | 23-stm32g0-pins.md |
| sample-23-f1-g0-compare | 对比 | 迁移五问 | 同段 |
| sample-24-mode-compare | 对比 | 24-STM32L4引脚.md 低功耗模式 | 24-stm32l4-pins.md |
| sample-24-wake-triage | 排错 | 唤醒/电流证据 | 同段 |
| sample-25-migrate-triage | 排错 | 25-STM32H7引脚.md F4 迁过来 | 25-stm32h7-pins.md |
| sample-26-spl-hal-compare | 对比 | 26-SPL.md 所有权边界 | 26-spl.md |
| sample-27-link-triage | 排错 | 27-网络.md 分层排错 | 27-network.md |
| sample-28-os-compare | 对比 | 28-RTOS.md 生态对照 | 28-system-rtos.md |
| sample-28-owner-flow | 概念/机制动画 | owner 任务流 | 同段 |
| sample-28-fault-triage | 排错 | 故障三岔口 | 同段 |
| sample-f-oss-map | 概念 | stm32-book/book/F-开源地图.md | （附录 zh-only） |

终态锚点（pdf_visual_anchors / HTML img）：ch23 **5**、ch24 **6**/7、ch25 **8**、ch26 **6**、ch27 **6**、ch28 **10**/11——六章 deficit=0，zh/en `asset_sequence_equal` = True。ch23 最大无图区间 3,884→**2,470**；ch28 3,695→**2,198**（均 ≤3,500）。

图注惯例：zh「▲ 自绘。……出处是 [X](#source-…) …。」en「▲ Drawn for this book. … Sources: …」。动画首帧 PDF 可读；`prefers-reduced-motion` 与 FA-002 在 anim 生成器保留。

## 4. manifest / 出处（§15.3）

- ch23 guides += `project-examples`（GitHub OSS，MIT；仅例程结构对照）。
- ch24–ch28 基线已含 ST 手册与既有 OSS 卡；本批图注交叉引用，不削弱、不改动被锁 source-card 字段。
- 附录 F：自绘 OSS 证据层地图；许可边界见各仓库 `LICENSE`；与官方 RM/DS 冲突时以手册为准。

## 5. 三类型归属（§15.1 / 三表之一）

| 章 | 概念 | 对比/关系 | 排错 |
|---|---|---|---|
| ch23 | sample-23-boot-latch（BOOT 锁存） | sample-23-f1-g0-compare | g0-boot-swd（既有） |
| ch24 | l4-idd-bench / stop2 证据 | sample-24-mode-compare | sample-24-wake-triage |
| ch25 | h7-clock-chain / power-domains | h7-revision-clock-decision | sample-25-migrate-triage |
| ch26 | spl-init-pipeline | sample-26-spl-hal-compare | spl-ownership-boundary |
| ch27 | network-packet-journey | network-cache-ownership | sample-27-link-triage |
| ch28 | sample-28-owner-flow | sample-28-os-compare | sample-28-fault-triage |
| 附录 F | sample-f-oss-map | （层间关系含于同图） | — |

## 6. 动画清单（§15.1 三表之二）

| 章 | 可播放机制动画 | 形式 |
|---|---|---|
| ch23 | **sample-23-boot-latch.svg（本批）** + g0-boot-swd.svg | CSS keyframes SVG |
| ch24 | l4-idd-bench.svg / l4-stop2-evidence.svg（既有） | CSS SVG |
| ch25 | h7-clock-chain.svg / h7-startup-evidence.svg（既有） | CSS SVG |
| ch26 | spl-init-pipeline.svg + nvic/dma（既有） | CSS SVG |
| ch27 | network-online-state.svg + tcp-byte-stream（既有） | CSS SVG |
| ch28 | **sample-28-owner-flow.svg（本批）** + freertos-scheduler / rtos-startup-gates | CSS keyframes SVG |

空转动效：无。装饰图：无计入锚点。

## 7. 官方 / 开源对照表（§15.1 / §15.3 三表之三）

| 章 | ST 官方 | GitHub OSS（许可） | 边界 |
|---|---|---|---|
| ch23 | ds12232、rm0444、an5096、an2606、st-boot-faq | **project-examples（MIT，本批补入 guides）** | 仅对照例程结构；引脚以 DS 为准 |
| ch24 | ds10198、rm0351、an4746、um1724、es0250 | stm32cube-l4-stop2、stm32l4-hal-rtc | 电流证据以板级测量为准 |
| ch25 | ds12110、rm0433、es0392、an4938 | stm32cube-h7-* | 迁移排错不替代 RM 时钟树 |
| ch26 | stsw-stm32054、rm0008 | spl-f1-mirror | SPL 历史包；新工程优先 HAL/LL |
| ch27 | rm0433、um2407、um1713、an4839、es0392 | stm32cube-h7-lwip、lwip-pitfalls（文档边界） | PCAP 为证据，非协议规范 |
| ch28 | pm0056、rm0399、stm32h745-header | freertos-1132、rtthread-530、zephyr-442、cmsis-640 | tag 固定；调度语义以所选 OS 手册为准 |
| 附录 F | （指向各章手册卡） | Cube / CMSIS / libopencm3 / FreeRTOS / RT-Thread / Zephyr | 先问要哪份 `.h`/函数，再谈星标 |

## 8. §15.2 终态 floors / gaps

| 章 | 终态锚点 | overlay 目标 | max gap | 备注 |
|---|---|---|---|---|
| ch23 | 5 | 4 | 2,470 | 已压到 ≤3,500 |
| ch24 | 6 | 6 | 2,055 | wake-triage 前移至 Stop2 段后，raw img gap≤5500 |
| ch25 | 8 | 6 | 1,354 | 迁移排错已补 |
| ch26 | 6 | 6 | 2,438 | SPL/HAL 对照已补 |
| ch27 | 6 | 6 | 2,585 | 链路排错已补 |
| ch28 | 10 | 9 | 2,198 | 已压到 ≤3,500 |

## 9. 阻塞 / 非本批

- 不启动 B7 全书普查（除非本门全绿且有明确剩余容量；默认停在 B6）。
- 板卡实拍仍用户自有（真证轨）；本批只用自绘 SVG，不冒充实拍。
- 附录 F 不在 `audit_book` 章节计数内；以 HTML 嵌入与自绘合同锁为准。

## 10. 测试锁（只增不减）

- `test_sample_svg_c.py`：ROWS +11，`len(found)=219`；`animations/sample-*` 允许 CSS keyframes 且要求「自绘矢量动画」。
- `test_advanced_visuals.py`：ch23/25/26/27/28 资产序列上调；新增 ch24 CHAPTERS；pairs 补 ch24。
- `test_book_audit.py`：更新 `test_chapter_24`；新增 `test_phase_five_family_migration_spl_network_rtos`。

## 11. 门验复跑记录

- check_assets：SVG **219/219** 合法；链接 1,393/1,393 有效；照片 3/3；讲解视频 29 套 MP4+SRT 通过（无 class 缺失 WARN）。
- build_html：zh `--check` PASS（6,879,271 bytes，29 章）；en `--check` PASS（6,917,524 bytes，29 章）。
- pytest 全量：**180 passed**（约 91s，0 failed）。
- slop_lint：干净，无机械命中。
- audit_book：ch23–28 deficit=0，zh/en `asset_sequence_equal=True`；全书 PDF 视觉锚点合计 **187**；ch23 max gap **2,470**、ch28 **2,198**、ch24 **2,055**（均 ≤3,500；ch23/28 专项门槛满足）。
- 生成器：`python tools/sample_figs_b6/gen_all.py` 11/11 重生成字节一致（boot-latch 含 e3-latch 样式后已锁 ROWS size=10798）。

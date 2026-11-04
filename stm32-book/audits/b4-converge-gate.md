# B4 收敛门审计（ch11–ch17）

状态：通过。日期 2026-11-04。基线：B3 提交 `5da27a7`。批次：spec §10.2 批次四（ch11、ch12、ch13、ch14、ch15、ch16、ch17）。

## 1. 前置与门验总览

| 门项 | 结果 |
|---|---|
| audit zh（deficit / parity） | 0 / 7 章 True |
| audit en（deficit / parity） | 0 / 7 章 True |
| check_assets | SVG 201/201 合法；链接 1,358/1,358 有效；照片 3/3 |
| build_html | zh check PASS（6,589,608 bytes，29 章）；en check PASS（6,643,756 bytes，29 章） |
| pytest 全量 | 178 passed（83.41s，0 failed） |
| 生成器确定性 | 11/11 图重生成字节一致 |

工具口径：`python tools/audit_book.py --format json --write .temp/b4-audit-final.json`（cwd=仓库根）；`python tools/check_assets.py`（cwd=仓库根）；`python build_html.py --check --lang zh` / `--lang en`（cwd=stm32-book/，脚本 `stm32-book/build_html.py`）。

## 2. 改章前缺陷清单（基线 5da27a7）

audit chars 为含代码口径（§15.2 分档依据）。基线旧表 target 4/4/3/4/4/4/4 全达标（deficit=0），缺陷在 overlay 档、gap、类型三轴。

| 章 | chars | 档位（旧/overlay） | 基线锚点 | overlay 目标 | 缺陷 |
|---|---|---|---|---|---|
| ch11 RTC与看门狗 | 7,536 | 中章 4/6 | 4 | 6 | 低于 overlay 2；缺 IWDG/WWDG 对比与排错类型；最大区间 3,125 |
| ch12 Flash与IAP | 7,666 | 中章 4/6 | 4 | 6 | 低于 overlay 2；无排错图；最大区间 2,635 |
| ch13 CAN总线 | 5,888 | 短章 3/4 | 3 | 4 | 低于 overlay 1；无排错图；最大区间 2,944（关键插图→章末） |
| ch14 USB | 8,914 | 中章 4/6 | 6 | 6 | 达标但缺地图/概念深化型；最大区间 3,059（关键插图→5. 枚举 7 步） |
| ch15 FreeRTOS | 6,432 | 中章 4/6 | 6 | 6 | 达标但无排错图；最大区间 1,256（8. 优先级反转→11. 软件定时器） |
| ch16 低功耗 | 7,567 | 中章 4/6 | 4 | 6 | 低于 overlay 2；缺三模式对比与排错；最大区间 3,150 |
| ch17 调试 | 7,607 | 中章 4/6 | 4 | 6 | 低于 overlay 2；缺观测手段对比与排错；最大区间 2,428 |

## 3. 本批交付

新增 11 张自绘 SVG（生成器 `tools/sample_figs_b4/`，svgkit 复用 `tools/svgkit.py`，无 CSS 动画无 SMIL），zh/en 双语嵌入，共 22 处：

| 图 | 类型 | zh 落点 | en 落点 |
|---|---|---|---|
| sample-11-wdg-compare | 对比 | 11-RTC与看门狗.md §4 前（L151） | 11-rtc-watchdog.md 同段（L150） |
| sample-11-rtc-triage | 排错 | §动手实验前（L296） | 同段（L295） |
| sample-12-flash-triage | 排错 | 12-Flash与IAP升级.md §2 前（L122） | 12-flash-iap.md 同段（L121） |
| sample-12-boot-compare | 对比 | §5 前（L226） | 同段（L227） |
| sample-13-can-triage | 排错 | 13-CAN总线.md 硬件与接线前（L202） | 13-can.md 同段（L201） |
| sample-14-descriptor-map | 概念 | 14-USB.md §6 前（L200） | 14-usb.md 同段（L199） |
| sample-15-rtos-triage | 排错 | 15-FreeRTOS入门.md 硬件与接线前（L272） | 15-freertos.md 同段（L272） |
| sample-16-stop-compare | 对比 | 16-低功耗设计.md §1 前（L115） | 16-low-power.md 同段（L115） |
| sample-16-pwr-triage | 排错 | §动手实验前（L313） | 同段（L313） |
| sample-17-obs-compare | 对比 | 17-调试与性能优化.md §2 前（L123） | 17-debug.md 同段（L122） |
| sample-17-perf-triage | 排错 | §代码实现前（L302） | 同段（L301） |

终态锚点：ch11 6、ch12 6、ch13 4、ch14 7、ch15 7、ch16 6、ch17 6——七章 deficit=0，zh/en asset_sequence_equal 均 True。

图注惯例：zh「▲ 自绘。……出处是 [X](#source-…) 和 [Y](#source-…)。」en「▲ Drawn for this book. … Sources: [X](#…) and [Y](#…).」锚点 zh=en 同 id。逐图 credit：wdg-compare=rm0008-wdg+ds5319-rtc；rtc-triage=rm0008-rtc+ds5319-rtc；flash-triage=rm0008-flash+pm0075-rdp；boot-compare=rm0008-flash+pm0056-vector；can-triage=rm0008-can+ds5319-clock；descriptor-map=rm0008-usb+project-examples；rtos-triage=freertos-syscall+project-examples；stop-compare=ds5319-pwr+rm0008-rcc；pwr-triage=ds5319-pwr+rm0008-rcc；obs-compare=pm0056+ds5319-swd；perf-triage=pm0056-dwt+pm0056。

## 4. manifest 恢复（本批事件）

本批期间 manifest 曾误回滚至 B3 提交态。依 spec §15.3(28)（每章 ≥1 个相关 GitHub 开源参考，须写明仓库、路径、许可证）核实：基线 ch11 全 ST 官方源、ch17 全 PM 官方源，均不满足该条。裁定恢复：

- 双 manifest：ch11 sources += `project-examples`；ch17 sources += `stlink-tools`。
- `stlink-tools` 卡重建于 `st-uart-idle` 块后（字典中部，不在尾 10 键内，不触 batch5/batch6 尾部键序锁）。

## 5. 三类型归属（§15.1-23）

| 章 | 概念 | 对比 | 排错 |
|---|---|---|---|
| ch11 | iwdg-window.svg、sample-11-iwdg-1s（1 秒计算） | sample-11-wdg-compare（递减到 0 复位 vs 窗口喂狗） | sample-11-rtc-triage（1 Hz 条件/复位归零查 VBAT/闹钟比 32 位秒计数） |
| ch12 | flash-iap.svg、sample-12-iap-map（页与 APP 地图） | sample-12-boot-compare（常驻 Bootloader 16 KB vs IAP 共用 46 KB） | sample-12-flash-triage（擦除/写入/读回三岔口） |
| ch13 | can-arbitration.svg、can-500k.gif | sample-13-can-bit（500 kbit/s 正确 vs 450 kbit/s 错配双路径） | sample-13-can-triage（邮箱空=未左移 5 位/错误帧查采样点） |
| ch14 | usb-enumeration.svg、sample-14-usb-enum、sample-14-descriptor-map（18+67 字节分解地图） | usb-enum 的双路径块 | instrument-evidence-ladder.svg（构建日志→寄存器→运行日志→逻辑分析仪→示波器证据阶梯） |
| ch15 | freertos-scheduler.svg、sample-15-rtos-prio、rtos-deadline-budget.svg、rtos-owner-task.svg | rtos-startup-gates.svg（启动检查门） | sample-15-rtos-triage（任务不动/栈溢出/优先级异常） |
| ch16 | lowpower-wakeup.svg、sample-16-stop-wake | sample-16-stop-compare（Sleep 14.4 mA/Stop 14 µA/Standby 2 µA 三模式） | sample-16-pwr-triage（进不去 Stop/醒来乱码/电流不降） |
| ch17 | debug-swo.svg、sample-17-cfsr | sample-17-obs-compare（观测手段不可互替） | sample-17-perf-triage（读数为 0/DWT 换算/BFAR 有效位三岔口） |

归属依据各图 aria 与图内结构；本批新图补齐三类型中最缺的一轴（ch11/12/16/17 补对比+排错，ch13/15 补排错，ch14 补概念深化）。

## 6. §15.2 档位与 gap 登记

overlay 后中章单区间上限 1,000；短章（ch13）无数值基数，gap 记「—」。以下为终态全量 >1,000 区间（左界=锚点 end，caption 排除，与 audit `_max_visual_gap` 同口径）：

| 章 | gap | 区间（左→右端） | 说明 |
|---|---|---|---|
| ch11 | 1,208 | 章首→时序与状态 | 开篇摘要纯文字（B2 ch02、B3 ch07 同型）；**例外登记** |
| ch11 | 2,417 | 关键插图→4. IWDG 与 WWDG 对比 | wdg-compare 落 §4 前，切分基线 3,125 走廊；**例外登记** |
| ch12 | 1,691 | 关键插图→2. 解锁与编程流程 | flash-triage 落 §2 前，切分基线 2,635；**例外登记** |
| ch12 | 1,716 | 4. 跳转到 APP→章末 | boot-compare 落 §5 前；基线 2,021 已切分；尾段 YMODEM+代码；**例外登记** |
| ch13 | 1,183 | 章首→时序与状态 | 开篇纯文字；**例外登记** |
| ch13 | 1,584 | 关键插图→硬件与接线 | can-triage 落硬件节前，切分基线 2,944（关键插图→章末）；**例外登记** |
| ch13 | 1,360 | 6. 过滤器与双 FIFO→章末 | 过滤器寄存器+代码走廊；**例外登记** |
| ch14 | 3,059 | 关键插图→5. 枚举 7 步 | 枚举事实连排（48 MHz/D+ 上拉/描述符计数）；descriptor-map 落其后未切本区间；**例外登记** |
| ch14 | 1,343 | 5. 枚举 7 步→代码实现 | descriptor-map（§6 前）切分基线 1,830；**例外登记** |
| ch15 | 1,155 | 关键插图→6. 任务间通信（IPC）对比 | 基线同值，IPC 机制叙述；**例外登记** |
| ch16 | 1,197 | 章首→时序与状态 | 开篇纯文字；**例外登记** |
| ch16 | 1,495 | 关键插图→1. 三种低功耗模式对比 | stop-compare 落 §1 前；基线 3,150 = 1,495 + 1,655 精确切分；**例外登记** |
| ch16 | 1,655 | 核心原理→7. 低功耗设计检查清单 | pwr-triage 落动手实验前；§2–§6 功耗机制+代码走廊；**例外登记** |
| ch17 | 1,449 | 关键插图→2. SWO / ITM / printf 跟踪 | obs-compare 落 §2 前，切分基线 2,428；**例外登记** |
| ch17 | 1,203 | 4. HardFault 定位三件套→代码实现 | perf-triage 落代码实现前，切分基线 2,122；**例外登记** |

超限处理：按 B2/B3 先例登记例外，不追加补图——剩余区间均为机制表格/代码走廊或纯文字开篇，岔口位已落新图。en gap 不入门（双语同步嵌入，英文行宽差异）。

## 7. 许可与出处（§15.3）

每章 ≥1 个 ALLOWED GitHub OSS（manifest sources 注册，zh/en 双 manifest 同步；ALLOWED={ST-facts-restated, MIT, BSD-2/3, ISC, CC BY 4.0/3.0, CC0}）：

| 章 | OSS（license） | 其余 sources |
|---|---|---|
| ch11 | project-examples（MIT） | rm0008、ds5319、rm0008-wdg、rm0008-rtc、ds5319-rtc、pm0075-rdp |
| ch12 | project-examples（MIT） | rm0008、an2606、an3965、rm0090、rm0008-flash、pm0056-vector、ds5319-swd、pm0075-rdp |
| ch13 | project-examples（MIT） | rm0008、rm0008-can、ds5319-usbcan、rm0008-usb、ds5319-clock、ds5319-i2c |
| ch14 | project-examples（MIT） | rm0008、usb20、rm0008-rcc、ds5319-usbcan、rm0008-usb |
| ch15 | project-examples（MIT） | freertos-priority、freertos-syscall、pm0056 |
| ch16 | project-examples（MIT） | rm0008、ds5319、ds5319-pwr、rm0008-pwr、rm0008-rcc、rm0008-usart、ds5319-adc、rm0008-rtc、rm0008-wdg |
| ch17 | stlink-tools（BSD-3-Clause） | pm0056、pm0056-dwt、ds5319-swd |

`stlink-tools` 卡（tag v1.9.0，`https://github.com/stlink-org/stlink/tree/v1.9.0/doc/man`，snapshot「tag v1.9.0, GitHub Releases 2026-10-04」，accessed 2026-11-04）：zh 标题「stlink v1.9.0 — 开源 ST-LINK 工具集（st-flash / st-util / st-info）」、scope「SWD 连接、flash 读写与芯片探测的命令行证据；本书仅对照其行为，不引用源码。」license 注「BSD-3-Clause（本书仅链接，不分发其源码）」；en 为对译。GPL/LGPL/Apache-2.0 维持拒绝。

## 8. 落点论证

- 通则：每图落语义岔口（对比节前/排错汇总节前/硬件接线前/动手实验前），落点与 §6 的 14 条区间一对一。
- ch16：stop-compare 落「1. 三种低功耗模式对比」前，把基线 3,150 走廊精确切成 1,495 + 1,655（三模式表与机制叙述的分界）；pwr-triage 落动手实验前，收束 §2–§6。
- ch14：descriptor-map 落「6. CDC 虚拟串口 vs HID」前——描述符字节地图是 §5 枚举 7 步的汇总，置于枚举与接口选择之间；未切 3,059 是因为该走廊内无图岔口，只在 §5 边界与 §6 前两点成立。
- ch12/13/17：flash-triage、can-triage、obs-compare 分别落「解锁与编程流程」「硬件与接线」「SWO/ITM/printf 跟踪」之前，均为读者动手前的最后文字关口；章末排错图（boot-compare、pwr-triage、perf-triage）落最后一节代码块前。

## 9. 十一图哈希登记

text_hash = sha256(`"\n".join(<text> 内文)`)，非整文件 sha256；与 `test_sample_svg_c.py` ROWS 及生成器 `_audit` 输出一致（尺寸均 960×880）。

| 图 | bytes | text_hash |
|---|---|---|
| sample-11-rtc-triage | 9,577 | dfe343f277ccf389b6e997b8e1250bf7c6b44853055c693ee601562d0077ee8f |
| sample-11-wdg-compare | 13,910 | 01eb45735fbb10af2251a9c62a7d7139244a1a6f137f80f87d7706309ad86231 |
| sample-12-boot-compare | 11,050 | e0de5fc1765c2aefd743c265375972ecb8d5c08009db0178884d74ea5ce31441 |
| sample-12-flash-triage | 9,523 | 204e0681a83f35dd1ff3b8cb296bd7351eb7e78fb2e3e14a0be643787467882a |
| sample-13-can-triage | 9,720 | 4e58328863259fa57f7a96e54313408ab728fb6971b631831799e1ef4482f1da |
| sample-14-descriptor-map | 17,900 | a814b32a1b1f56266a1b67c7296953218982fa66319d1d82c121e702973b4bca |
| sample-15-rtos-triage | 10,876 | 4532a208ff48f08116bd4ec5a494a0bdbc926ec34fabe74d5863ce30b25882bf |
| sample-16-pwr-triage | 10,663 | 49a7481ef1bd377835e8bb7ad0945be30b3590dbae59fa2bf9d4b5cbced6abc5 |
| sample-16-stop-compare | 16,112 | aa1c85a1e5883623b88ca138a8fbb834c57d732c3bc25567d5d21c8f9e17b158 |
| sample-17-obs-compare | 19,904 | 6aa426212854d650a1fe5749c4397a5a4030c99bccc00d727ee732e098a9e847 |
| sample-17-perf-triage | 12,163 | 8e3ad12ed2a637a099047c9f903e746609f80996e9eedd29d667d02d1f5a06f1 |

## 10. 测试锁

| 文件 | 变更 |
|---|---|
| tests/test_advanced_visuals.py | CHAPTERS 计数：ch11 4→6、ch12 4→6、ch14 6→7、ch15 6→7、ch16 4→6、ch17 4→6（ch13 无锁） |
| tests/test_book_audit.py | 3 个相位测试的 7 章 asset_sequence 元组（12/13/15 同测试内顺带更新） |
| tests/test_sample_svg_c.py | ROWS +11 行（字母序）；清单 190→201 |
| tests/test_batch4_chapters.py | ch11 sources 期望 +project-examples |
| tests/test_batch6_chapters.py | ch17 sources 期望 +stlink-tools |
| tests/test_batch2_chapters.py | 累积 source-delta 集合 zh/en +stlink-tools（2 处） |
| tests/test_sample_chapters.py | 累积 source-delta 集合 zh/en +stlink-tools（2 处） |
| manifest.json / manifest-en.json | ch11 sources、ch17 sources、stlink-tools 卡（§4） |

## 11. 验证记录

- `.temp/b4-audit-final.json`（终态重建）：zh/en 锚点 6/6、6/6、4/4、7/7、7/7、6/6、6/6；deficit 全 0；parity asset_sequence_equal True、h2/h3/table/code delta 全 0；zh max gap 2,417/1,716/1,584/3,059/1,155/1,655/1,449。
- check_assets：SVG 201/201 合法；链接 1,358/1,358 有效；照片 3/3 哈希与尺寸匹配。
- build_html：zh `--check` PASS（6,589,608 bytes，29 章）；en `--check` PASS（6,643,756 bytes，29 章）。
- pytest 全量：178 passed（83.41s，0 failed）；此前 8 个失败（batch2/batch4/batch6/sample_chapters/sample_svg_c/book_audit×3）全部由 §4 的 manifest 恢复与 §10 的字面量更新闭环。
- 生成器确定性：7 个生成器重跑，11/11 与待提交 SVG 字节一致；`_audit` 输出 bytes/text_hash 与 §9 表逐一相符。
- task_verify：长期记账项 `project-or-git-baseline-unavailable` 沿用 B3 §11，本轮未重跑（测试变更按规则待评审后成为基线）。

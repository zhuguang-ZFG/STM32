# 双书合并 B4（卷 6–7 + 六附录）Implementation Plan

**Scope:** 卷 6（ch40–42）与卷 7（ch43–46）共 7 章，加六附录 apA–apF；资产迁移 175 个目标（18 已在库）；ch40 落位后 8 行 lab partial 转 migrated；ch40/41 方向 10 处残留引用内联；CI 扩量与批次证据。**B4 完成后全书 46 章 + 6 附录齐备**（`built 52 pages, 0 planned chapters missing`）。

**Architecture:** 沿用 B1–B3 质量门（`book/checks.py`、`book/build_html.py --check`、`book/mapping.py`、`tools/slop_lint.py` 七 glob）。ch40–46 是方法与工程章（无寄存器级上游核对），六附录是双源合并（每附录给合并规则表）。章节结构固定不变；附录用「合并书重建骨架」——两源各自的附录内链改 apX 锚点，禁保留两书原编号。

**来源研究：** `.superpowers/sdd/2026-11-14-merged-book-b4-vol6-7/research/` 两份：`b4-labs-projects-sources.md`（ch40/41/42 + 14 处挂账回收清单）、`b4-delivery-appendices-sources.md`（ch43–46 + 六附录合并策略）。冲突时以研究文档为准。

## Global Constraints

- 仅中文书稿；旧树零改动（`docs/00–28*.md`、`docs/en/**`、`stm32-book/**`、`mcu/**` 不改）；本批新增 `docs/v6-labs-projects/`、`docs/v7-delivery/`、`docs/appendix/`，只改 `docs/public/`、`book/data/mapping.tsv`、`plans/2026-11-12-merged-book/`、`.github/workflows/merge-check.yml`。
- 章节结构固定（罗盘/先做出来/机制/测量与证据/失败分支/离开检查；方法章可用「本章罗盘/先做出来/机制/……」同骨架）；附录无罗盘，但每附录有「本附录怎么用」开头段与来源登记尾段。
- 图片引用根绝对路径；alt 必填；禁外链；章间链接一律内联相对 `.md`。**新章内的前向链接（目标未落位）先写纯文本**，Task 15 补回——B3 的教训。
- 证据标签四级不变。全批零板级实测：8 份 lab `hardware_status: pending`、两份 PRJ `pending`、十项目无读数——任何「已量到」都是违反。
- 版本与时效口径：AI 章工具事实全部挂 ai-* 来源卡（accessed 2026-10-27），版本化行为（Copilot 59 分钟、Cursor v3.6/v3.23）句子带「截至 2026-10-27」；开源地图星标「GitHub API，2026-10-26；引用前 git log -1」；QMI8658 WHO_AM_I 带「C 版」限定（A 版 0xC0）。
- 板名口径：mcu 书正片板名是**霸天虎**（野火 F407 霸天虎）；「霸道者」是错名，ch43/44 合并时统一改；「霸道」是野火 F103 板名。
- mapping 状态机：ch40 落位 → `e01–e08` 八行 `chNN;ch40` partial 转 migrated；`docs/21`、`docs/22` → ch40；两份 PRJ → ch41；`docs/19` → ch42；ai 六文件 → ch43/ch44；`docs/18`+mbF → ch45；`docs/00`+`docs/20` → ch46；附录十二行 → apA–apF。
- slop HOUSE_STYLE：`✅` 等判定符号改文字（mcu 域原章末的 `<div class="achievement">✅…</div>` 与 emoji 收尾块合并后按根书口径重写）。
- 所有提交按显式路径暂存；远程推送/PR/Pages 需另行授权。

---

### Task 1: B4 资产迁移（157 个待迁文件）

底表：`.superpowers/sdd/2026-11-14-merged-book-b4-vol6-7/task1-assets.md`（175 目标，18 已在库）。改名规范同 B3（anim/diagrams→anim|figures、handraw→images、boards→images/boards、photos→images/photos、mcu public 直映）。mcu 侧 ai-* 动画 6 张入 `docs/public/anim/`；根书 app-a–f 手绘板入 `docs/public/images/`。

- [ ] 复制 → `python -m book.build_html --check`（页数不变）→ `git add docs/public && git commit -m "feat(assets): migrate volume 6-7 and appendix assets into docs/public (B4)"`

### Task 2: ch40《实物实验方法与仪器证据》

**Files:** Create `docs/v6-labs-projects/40-lab-method-instruments.md`；mapping：`docs/21`、`docs/22`→migrated，`e01–e08` 八行 partial→migrated。

**必须覆盖（研究 §2 + §5）：**

- 证据分级与「读数来路表」落地格式（接 ch09 三要素：接线/观测手段/读数）；lab 实测记录表（日期/板子/观测手段/结果/备注）为标准格式。
- 四类仪器与判据：万用表（E06 串接纪律：mA 起步防过流、µA 档换孔、先拔仿真器）、示波器（E03 探头 ×1/×10 一致性）、逻辑分析仪（E02 下降沿=起始位、1/脉宽≈波特率、≥10×SCL；E05）、秒表粗测（E01 十周期）。
- 「押注→测量→对账」方法论：八份 lab 的「先押一个数」统一教法立为第一步。
- 真板识别：身份三寄存器读回（DBGMCU_IDCODE 0xE0042000 / Flash 容量 0x1FFFF7E0 / UID 0x1FFFF7E8）；F103C8T6=0x410/64KB/UID96 位；「丝印与手册冲突时身份记录是裁决书」。
- 仿真证明边界：D22 三句话收尾 + 四道验收门 + 「DMA/RTC/IWDG 未实现」支持表带版本限定；「仿真里灯闪了，只能证明 ELF 与当前模型配合」。
- **挂账回收清单（14 处，研究 §5 逐条）**：ch09/12/13/14/15/16/24/31 各欠什么、用哪份 lab 素材承接——ch40 用一节「这些账在这里收」逐条回链；「只收怎么测，不收是什么」纪律。
- 失败排查表写法（症状/原因/处置三列，TPL ≥3 条）；实验报告模板指向 `mcu/docs/lab/reports/` 空白模板用法。
- **禁抄**：预期现象不写成读数；E04 的 6000/2500 不是实测；四张仪器图不是上板证据；支持表不是永久事实；0x05 仅 QMI8658**C 版**（A 版 0xC0）；2×20 pF/2×6 pF 非通用值。

**图片（≥6）：** `/images/ch21-board-compare.png`、`/figures/sample-22-hw-gap.svg`、`/images/labs/e02-uart-capture.svg`、`/images/labs/e03-pwm-probe.svg`、`/images/labs/e06-current-meter.svg`、`/figures/sample-21-identity-triage.svg`（以实际迁入为准）+ 手绘 ch21/ch22 板若干。**链接：** `../v1-drivers/09-gpio.md`、`./41-…`（ch41 落位后补回）、`../v3-rtos/24-…`。**提交：** `feat(ch40): rewrite lab-method/instruments chapter (B4)`

### Task 3: ch41《双板综合项目》

**Files:** Create `41-dual-board-logger-project.md`；mapping：PRJ1/PRJ2→migrated。

**必须覆盖（研究 §3）：** 双板同构骨架（一份协议 64 B SAMPLE、公共核心 `code/common/logger`、两份 port）按「公共→平台差分」组织，逐字重复段落禁抄两遍；平台对照表五栏（传感器/存储/看门狗/控制台/采样源：ADC PA0+TIM2 TRGO+DMA2 vs 板载 QMI8658；EEPROM 双槽提交标记 vs NVS 单 blob；硬件 watchdog vs TWDT；USART1 PA9/PA10 vs UART1 GPIO10/11）；显式过载保护（16 槽×64 B=1 KB、满丢新+计数、1.6 s 缓冲）；期限监督 vs 心跳论证（2500 ms 内 ≥20 次采样可复算）；配置三态（configure 改 RAM/save 持久化/重启加载）；故障注入四命令与构建开关（F407 `FAULTS=1`、S3 `sdkconfig.defaults.faults`、普通固件 UNSUPPORTED）；**工程实况**：`mcu/code/projects/` 不存在——载体是 `code/projects.json` + `code/stm32/07-sensor-logger` / `code/esp32/08-sensor-logger` / `code/common/logger`。**禁抄**：PRJ2 健康段「硬件 watchdog 名义 2s」照抄（S3 用 TWDT 无外部看门狗芯片，PRJ2:83 与之矛盾须改写）；fault 表「预期逻辑结果」改实测；删「无硬件流控的 UART 不能确认对端真正接收」边界句。

**图片（≥4）：** `/images/projects/logger-architecture.svg`、`/images/projects/j1-f407-wiring.svg`、`/images/projects/j2-s3-wiring.svg`、`/anim/logger-queue-overflow.svg`、`/arch/logger-flow.png`。**链接：** `./40-…`、`../v4-platforms/30-…`、`../v3-rtos/24-…`。**提交：** `feat(ch41): rewrite dual-board logger project chapter (B4)`

### Task 4: ch42《项目实战与交付验收》

**Files:** Create `42-project-delivery-acceptance.md`；mapping：`docs/19`→migrated。

**必须覆盖（研究 §4）：** 「证据链能否闭合」选题法（输入怎么测/状态怎么记录/输出怎么验收/失败后怎么恢复四问）+ MVP 先行；十项目按四问重排验收栏，不照搬工时星级（工时/难度是「经验值仅供规划」）；四组资源算术整段保留（分区 16+2+46=64 KB、双 APP 110 KB 越界不成立、SRAM 20 KB 放不下 64 KB 缓冲、ADC 名义换算、USB 133 B 分包 64+64+5）；「一轮一个新外设」+ 失败三岔口（贪多/跳步/无证据）；**与 ACC 共用的通用验收纪律**（从 motor 卷提炼、注明出处）：NOT_RUN/BLOCKED 不计通过、模拟数据不填真板状态、重复全部保留不挑最好、合同先行阈值测前冻结；交付包清单取 D19 四条与 ACC §6 并集（metadata/哈希/原始数据/已知限制/恢复步骤）；「声明段随代码走」——五处自标草图（WS2812 双 CCR、SetMotor 无真值表、Boot_SelectApp 无边界检查、LA_Upload 不等 BUSY、LA 段实为 TIM 中断）与代码同页保留。**禁抄**：工时写成承诺；WS2812 三时序数写成通用规格；kp=25.0/kd=0.8、5 ms 写成稳定参数；「两个 23 KB 双槽」写成可实施；Checksum8 说成 CRC；133 B 抄成 134。

**图片（≥5）：** `/figures/iap-acceptance-gates.svg`、`/images/ch19-iap-gates.png`、`/figures/sample-19-milestone-triage.svg`、`/images/ch19-milestone-triage.png`、`/figures/project-structure.svg` + 手绘板。**链接：** `./41-…`、`../v5-motion/39-…`、`../v1-drivers/17-…`。**提交：** `feat(ch42): rewrite delivery/acceptance chapter (B4)`

### Task 5: ch43《AI 结对开发与提示词工作流》

**Files:** Create `43-ai-pair-programming.md`；mapping：ai/00、01、03→migrated。

**必须覆盖（研究 §2）：** 三句官方红线与「结对不是代笔」五维分工表；能/不能 4+4 清单与唯一分界线（正确性定义在哪）；三次一致性实验（GPIOF 挂哪条总线）与「模型输出是分布，不是事实」；2026 工具地图四格表（Copilot/Claude Code/Cursor/MCP 是协议不是第四个工具）+ 每格挂 ai-* 来源卡 + 版本化行为带「截至 2026-10-27」；弱提示四雷与三段式解剖；六类代签决定清单与评审三步；MCP 三角色三原语一拓扑 + Sampling/Logging deprecated 时效注记 + reference servers 7 个带日期；三场景实录（L0/L1/L2 手册级、跑构建四步验收、串口切片三招 + E08 案例：MCLK=4096000、PA_EN 走 PCA9557 bit1@0x19）；权限四问与三层防线（软约束/工具闸门/硬门禁）+ 生产凭据不进 agent 环境。**合并纪律**：AI00 立观/AI01 模式/AI03 工具流压成一章（定位→工单→工具），砍三份重复实验表只留一个主实验（AI00 一致性实验）；A0–A5 编号改章内小节引用；「霸道者」→霸天虎；`/anim/ai-*.svg` 改 `docs/public` 路径；mcu-book 相对路径改 `mcu/mcu-book/…`；删 achievement/emoji 收尾块。

**图片（≥4）：** `/anim/ai-prompt-anatomy.svg`、`/anim/ai-tool-map.svg`、`/anim/ai-mcp-toolflow.svg` + 手绘板（如有）。**链接：** `./44-…`、`../v1-drivers/09-gpio.md`、`./40-…`。**提交：** `feat(ch43): rewrite AI pair-programming chapter (B4)`

### Task 6: ch44《手册对账与幻觉防御》

**Files:** Create `44-manual-reconciliation-hallucination.md`；mapping：ai/02、04、05→migrated。

**必须覆盖（研究 §3）：** 手册对账三步（引章节号不引页码/快照冻结/读数带条件）；AI05 全部可复现断言逐条核对表（main:631、73、101、111、94——**AI05 数字漂移修正**：旧稿 main:619→631、72→73、100→101、109→111、91→94）；幻觉防御树与「两套门禁不混写」——mcu 口癖门（mcu-book prose 门）与根书 slop_lint 是两套工具，各有词表与覆盖面（研究 §3.2 专条）；本书生产管线段（研究→计划→写作→门禁→评审）作为「这本书怎么写出来的」自白；三层防线与权限爬坡（与 ch43 分工：ch43 讲工具用法，ch44 讲防错制度）。**禁抄**：AI05 漂移数字照抄；板名「霸道者」；两套门禁混写成一套；achievement/emoji 收尾。

**图片（≥3）：** `/anim/ai-hallucination-tree.svg`、`/anim/ai-reconcile-loop.svg`、`/anim/ai-book-pipeline.svg`。**链接：** `./43-…`、`../v1-drivers/17-…`、`./45-…`（ch45 落位后补）。**提交：** `feat(ch44): rewrite manual-reconciliation/hallucination chapter (B4)`

### Task 7: ch45《常见故障排查手册》

**Files:** Create `45-troubleshooting-handbook.md`；mapping：`docs/18`、mbF→migrated。

**必须覆盖（研究 §4）：** 双源合并（根书 FAQ 482 行为主干 + mcu-book F 111 行并入）；**失败分支聚合索引**——已发布章的失败分支表统计为 **19/22 章、约 204 条、两代格式**（禁写「每章都有」），按章号分组的索引表指向各章原表；「症状→第一条假设→区分实验」三列口径与各章一致；FAQ 的九大类组织（下载/连接/编译/外设/H 硬件/R RTOS…）沿用 mbF 分组交叉引用；排错方法论三句（先对现象再找第一处边界最后按标签查出处/不要从第三列开始改/每次只验证一个假设）。**禁抄**：「每章有失败分支表」的假命题；FAQ 里与已发布章冲突的旧数值（逐一对照新章口径，冲突处以新章为准并标注）。

**图片（≥4）：** `/figures/sample-18-faq-compare.svg`、`/images/ch18-faq-compare.png`、`/images/ch18-five-steps.png`、`/figures/sample-18-hardfault-ladder.svg`。**链接：** `./44-…`、`../v2-reliability/19-…`、各卷章内联（聚合索引表）。**提交：** `feat(ch45): rewrite troubleshooting-handbook chapter (B4)`

### Task 8: ch46《资料、学习路线与开源地图》

**Files:** Create `46-resources-roadmap-open-source.md`；mapping：`docs/00`、`docs/20`→migrated。

**必须覆盖（研究 §5）：** 学习路线与 46 章目录映射（D00 路线图 → toc 章号表）；**D00 与 mbF 的入门路线/买板建议相反——统一口径以合并书 toc 与 [第 1 章](../v0-foundations/01-c-memory-model.md) 后的实际章节序为准**，矛盾处显式声明取哪边；工具链资料（Cube/CubeMX/IDE/调试器/仿真器清单）带版本与抓取日期；开源地图摘要指 apF（大表在附录）；「生态数量带抓取日期」口径（CH27:88）。**禁抄**：两源相反建议不处理就混排；无日期的生态数字。

**图片（≥4）：** `/figures/sample-00-roadmap-gates.svg`、`/images/ch00-roadmap-three-stages.png`、`/figures/sample-00-three-ways.svg`、`/images/ch00-three-api-lanes.png`。**链接：** `./45-…`、`./apF` 类附录链接（附录落位后补）、`../v0-foundations/…`。**提交：** `feat(ch46): rewrite resources/roadmap/open-source chapter (B4)`

### Task 9–14: 六附录 apA–apF

**Files:** Create `docs/appendix/A-engineering-deep-read.md`、`B-project-index.md`、`C-exercises-answers.md`、`D-glossary.md`、`E-sources-version-license.md`、`F-open-source-community-map.md`；mapping：附录十二行→apA–apF migrated。

**合并规则（研究 §6 逐附录执行）：**

- **apA**：mcu 五契约为骨架（帧协议/慢消费者段是根书源没有的），根书契约 A/B 并入展开位；F1 固定通道与 F4 流×通道各一段禁混写寄存器名；CRC 检查串 `123456789→0x29B1` 保留；验证矩阵两表合一。
- **apB**：双登记簿两区（根书 examples/ 14+1 例程补登 `motor-dc-speed`；code/ 47 工程）；「对应章节」按 mapping 重排；许可注按域分开（examples/ MIT、code/ Apache-2.0）。
- **apC**：根书 235 行为主体按 mapping 重排章号；一源多目标章的答案拆到对应章小节禁丢条目；六段数字对账保留并与 apD/ch 内数值交叉核对；图片 4 张 handraw 改路径。
- **apD**：统一 4 列（补「深读」列）；主题分组制保留（不全表拼音排序）；约 40 组重叠词条逐条合并去重（去重后 180–200 词条）；新增 ESP32-S3/IDF 与 GD32/RISC-V 两组；文末三张账原样保留；「芯片相关」角标从 mcu 书引入。
- **apE**：双注册表合并为统一注册表（ID 双命名空间：根书 `rm0008` 等原名 + mcu `a1–f8`/`mcu-*`/`ai-*`，两套 ID 禁止重号）；冻结点清单原样保留并注明 RT-Thread 无固定 tag 是已知缺口；许可按域分节（根域 CC BY 4.0/照片三许可/MIT；mcu 域 Apache-2.0），**禁合并成单一许可证表述**；「一笔数字怎样才算钉住」四格段保留。
- **apF**：mcu 30 仓表为底 + 根书「章」列并入；星标表头「GitHub API，2026-10-26；引用前 git log -1」；9 条知识点分「跨厂商/ESP-IDF 专」两小节（三对重叠取 mcu 版为底，根书独有细节并入）；mcu 五族许可表整段保留；复刻清单取并集；根书「学习路线收束」81 行按 mapping 放 apF 末节（备选：并入 ch46，如主题冲突在评审记录中声明）。

每附录：开头「本附录怎么用」段 + 来源登记尾段；图片改 `docs/public` 路径；无罗盘。**各附录提交：** `feat(apX): merge appendix X from both books (B4)`

### Task 15: 前向引用清扫与交叉链接补全

- 10 处 `[ch40]/[ch41]` 引用内联（v1-drivers 6 文件：09-gpio/12-timers/13-uart/14-dma/15-adc/16-i2c），定义行删除；`grep -rn "\]\[ch4[0-6]\]"` 清零。
- 补回各章延后的前向链接（ch40→41、ch31→40、ch43→44/45、ch44→45、ch30→31/32 等 B3 延后项），`python -m book.checks --check` 全绿。
- **提交：** `docs(links): inline forward references to volume 6-7 and wire cross links (B4)`

### Task 16: CI、批次记录与 B4 证据

- merge-check.yml slop 行扩到 `docs/appendix/*.md`（七 glob）。
- README：B4 行改「本批完成（本地）」；数据文件补 B4 摘要（lab 八行与 e08 翻 migrated、附录十二行 migrated；全书 46 章+6 附录齐备）。
- 证据 `plans/2026-11-12-merged-book/evidence/b4-local.md`（格式对齐 b2/b3-local：七门禁真实输出、13 章文件名、`built 52 pages, 0 planned chapters missing`、附录合并摘要、未验证声明）。
- **提交：** `chore(ci): enable B4 chapter gates and record local evidence (B4)`

---

## Self-Review 记录

- **Spec 覆盖**：B4 出口「卷 6–7 + 6 附录齐备」→ Task 2–8（7 章）+ Task 9–14（6 附录）；「mapping 八行 partial 翻转」→ Task 2；「ch40 挂账回收」→ Task 2 专节（研究 §5 的 14 条逐条）；「CI/证据」→ Task 16。
- **Placeholder 扫描**：每章必写清单来自研究文档实锚；附录合并规则逐附录成表。
- **类型一致性**：quiz 无新增；build_html 计数 39→52 单调推进；mapping 双目标行（e01–e08 的 chNN;ch40）在 ch40 落位后一次翻转。
- **已知边界**：`docs/00-M`（根书学习路线收束页 81 行）按 mapping 归 apF 末节，备选并入 ch46；`e08` 等 partial 行在 ch40 落位后全转 migrated；远程推送/PR/Pages 需另行授权；B5 不在本批。

# B54 Spec 切片：英文版无图区间收口（top-8，目标 ≤2,000）

状态：Draft 1 · 2026-11-10 · 待批准（本批只出 spec，不改正文）
基线：`main` @ `72a5446`（B53 收口后）｜ 数据：`python tools/audit_book.py --format json --write .temp/b54-audit-base.json`
约束来源：`BOOK_REDESIGN_SPEC.md` §6.3/§11、`BOOK_CLASSIC_CONVERGE_SPECS.md` §15.2、`b53-spec-closeout.md`「closed-spec rule」（新工作开新切片，不重开已关闭三份 Spec）

## 1. 基线更正（先读）

方向 2 原定「收口 gap>2,000 的 8 章：02/03/11/14/21/24/26/27」，该清单取自
`b7-converge-census.md` §2.1（基线 `8794d00`，B46–B52 之前）。B52 已把中文硬门
全部收口，该清单已失效：

- 现行中文侧 29 章最大无图区间全部 ≤1,231（ch26=1,231 为已批例外），
  原清单中的 02=1171、03=1035、11=1139、14=1128、21=1093、24=1082、
  26=1231、27=1102，均不再有 >2,000 的缺口。
- 现行 >2,000 的缺口全部在**英文侧**，共 21 章，最大 3,216。原因是同一图序下
  英文正文长度为中文约 2.2 倍（如 ch16：en 22,911 字符 vs zh 10,264），
  而 `_overlay_gap_budget_chars` 直接用该语言字符数套 900/1,000/3,500 档。
- 因此本切片按**现行数据**改为：英文侧前 8 大缺口章（16/18/28/11/19/15/12/04），
  目标 en ≤2,000。2,000 ≈ 2× 中文中章预算（1,000），与 en/zh 字符比一致，
  作为分阶段收口第一步；不宣称英文已达 900/1,000。

### 1.1 现行基线（2026-11-10，`audit_book`）

| 章 | en 字符 | en 锚点 | en 最大无图 | zh 最大无图 | zh 预算 | 本次目标 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 16 | 22,911 | 18 | **3,216** | 1,127 | 900 | ≤2,000 |
| 18 | 17,072 | 16 | **2,840** | 1,131 | 3,500 | ≤2,000 |
| 28 | 31,248 | 25 | **2,833** | 1,090 | 3,500 | ≤2,000 |
| 11 | 18,939 | 18 | **2,740** | 1,139 | 1,000 | ≤2,000 |
| 19 | 20,539 | 19 | **2,715** | 1,143 | 900 | ≤2,000 |
| 15 | 17,870 | 18 | **2,625** | 1,179 | 1,000 | ≤2,000 |
| 12 | 18,202 | 18 | **2,586** | 1,194 | 1,000 | ≤2,000 |
| 04 | 17,354 | 18 | **2,566** | 1,106 | 1,000 | ≤2,000 |

注：ch18/28 的 3,500 是中文短章 carve-out；英文侧按本批目标收紧到 2,000，
属于主动加严，不改中文 carve-out 数值。

## 2. 目标与非目标

目标：

1. 上表 8 章 en `max_visual_gap_chars` ≤2,000（新增测试锁）。
2. 中文硬门不回退：29 章 zh ≤1,200（ch26=1,231 例外保留）。
3. 锚点只增不减；zh/en `asset_sequence` 严格一致（现有 parity 测试）。
4. 全部新增图为知识轨 Handraw 原理示意，可由脚本确定性重建。

非目标：

- 不改正文句子、不改事实与数字；只插入图块（img + alt + 图注）与其生成器。
- 不新增实拍、测量、示波器或上板证据（无硬件）；图注必须写「原理示意 / 非实拍」。
- 不追求英文 29 章全部 ≤1,200；剩余 13 章 >2,000 列为 B55 候选（§8）。
- 不动章首视频、EPUB 结构、三份已关闭 Spec。

## 3. 指标与验收门

指标口径沿用 `tools/audit_book.py`：`max_visual_gap_chars` = 相邻 PDF 锚点之间
的正文阅读字符，围栏代码剔除，章首视频剔除，一张图（含同组多图/可嵌入动画首帧）
算一个锚点。估值为非空白字符。

| 门 | 条件 | 落地 |
| --- | --- | --- |
| en 批次门（新） | 8 章 `max_visual_gap_chars` ≤2,000 | `test_book_audit.py` 新增 `EN_GAP_BATCH_BUDGETS` |
| zh 分布门（既有） | 29 章 ≤1,200，ch26=1,231 例外 | `test_zh_visual_gap_distribution_gate`，不改 |
| 锚点下限（既有） | 4/6/9 档，deficit=0 | `test_book_audit.py`，新增图只会增加 |
| 双语序列（既有） | zh/en `asset_sequence` 完全一致 | `test_bilingual_visual_sequence...`，不改 |
| 构建门（既有） | HTML/PDF/EPUB/链接/照片/SVG | 见 §7 命令集 |

## 4. 逐章落点与图设计（9 张新图）

插入位置用「小节标题 + 段序」定位（zh/en 行号几乎平行，但按文本锚点插入，
不按行号）。每张图只回答一个问题，禁止把相邻表格抄成图。

| # | 章 | 现 en gap | 左锚点（现有） | 右锚点（现有） | 插入点 | 新图 id | 回答的问题（事实全部来自正文） | 插入后最大段（估） |
| --- | --- | ---: | --- | --- | --- | --- | --- | ---: |
| 1 | 16 | 3,216 | `ch16-clock-restore.png` | `lowpower-current-evidence.svg` | §5「电池供电要点 / Battery-powered design」首段后 | `ch16-battery-budget` | 占空比账本（概念图，不抢后文算例）：active 脉冲 + sleep 地板 + `I_avg=Σ(I_k×t_k)/T`；Stop 地板不能单独预测续航；LDO Iq / 上拉 / 分压 / IWDG 各是一项持续漏电（表内事实） | ≤1,806 |
| 2 | 18 | 2,840 | `ch18-peripheral-triage.png` | `ch18-five-steps.png` | §4「硬件 / Hardware」H4 块后 | `ch18-hardware-triage` | 高频硬件症状判据（只用图前已出现的 H1–H4）：LED 不亮查极性与灌电流；0 电流先量 3.3 V 与表接法；复位抖动先存 RCC flags 再查 NRST；过烫先断电查短路与 5 V 反灌 | ≤1,214 |
| 3 | 18 | （同上段） | 同上 | 同上 | §5「RTOS 与工具链」R4 块后 | `ch18-rtos-triage` | 上线 RTOS 后的四种症状（只用图前已出现的 R1–R4）：`HAL_Delay` 卡死→看 `HAL_GetTick()`（TIM4 与 SysTick 分工）；`configASSERT` 自旋→优先级数值需 ≥5（`5<<4=0x50`）；`xTaskCreate` 失败→堆实现与栈需求；ISR 调普通 API→HardFault，改 `FromISR` | ≤1,257 |
| 4 | 28 | 2,833 | `freertos-scheduler.svg` | `ch28-h745-contracts.png` | H745 小节导语段后、五契约表前 | `ch28-h745-boundaries` | HSEM 的三条边界：它提供原子所有权与中断通知，但不搬运 payload、不维护 M7 data cache；payload 在双核可达 SRAM、cache 维护在 M7 侧，二者都要单独定所有权与顺序（表随后展开五契约） | ≤1,880 |
| 5 | 11 | 2,740 | `ch11-backup-domain.png` | `sample-11-wdg-compare.svg` | §2「BKP 备份寄存器」末（魔数段后、§3 前） | `ch11-bkp-magic` | 上电读 BKP_DR1：等于 `0xA5A5` 则读日历，否则初始化并写魔数；F103C8 为 DR1–DR10 十个 16-bit（20 B），F4 为 DR0–DR19 32-bit | ≤1,944 |
| 6 | 19 | 2,715 | `ch19-iap-gates.png` | `network-debug-ladder.svg` | §7「简易逻辑分析仪」方法段（Approach）后、环形缓冲段前 | `ch19-la-sampling` | 两条采样实现：TIM 中断读 GPIOC（示例所用，间隔受中断延迟与其他中断影响）vs TIM+DMA（需核对请求映射与总线路径）；先验证采样周期与输入保护（环形缓冲/BUSY 在下一段展开） | ≤1,720 |
| 7 | 15 | 2,625 | `freertos-scheduler.svg`（章首） | `sample-15-rtos-tick-flow.svg` | 「原理与适用范围 / Principle and scope」第 6 段（FromISR 阈值段）后 | `ch15-two-priority-rules` | 两套优先级不要混：FreeRTOS 任务号大者先（KEY 2 > LED/UART 1 > idle 0），NVIC 号小者急（FromISR 阈值 `5<<4=0x50`）；1 ms tick 与 TIM4/SysTick 分工 | ≤1,845 |
| 8 | 12 | 2,586 | `iap-jump.gif` | `sample-12-page-erase.svg` | 「常见坑与出处」标题后、坑表前 | `ch12-last-page-math` | 末页地址算术（前文「时序与状态」表已给事实）：C8 64 KB=`0x08000000–0x0800FFFF`、1 KB×64 页、page 63 起于 `0x0800FC00`；`0x0801FC00` 是 128 KB 器件的末页，不在这颗 C8 上；应用 46 KB=`0xB800` | ≤619 / 1,967 |
| 9 | 04 | 2,566 | `ch04-exti-triage.png` | `sample-04-tail-chaining.svg` | 「动手实验 / Hands-on labs」三个 Lab 后、§6 前 | `ch04-lab-evidence` | 三个实验各留下什么证据：Lab1 `EXTI_PR` 清零+10 次翻转；Lab2 保留去抖前后计数；Lab3 优先级 1 在优先级 2 期间进入（两路 GPIO 双迹） | ≤1,771 |

ch12 的 1,399 字符坑表夹在两个锚点之间；新图放在坑表**前**、只使用前文
「时序与状态」表已给出的事实，插入后两段为 619 / 1,967，不拆表、不重复表格。

### 4.1 与既有图的分工（防重复）

- ch16：`ch16-mode-current` 是模式电流对照，新图是**时间账本**（占空比→平均值→续航）。
- ch18：`ch18-peripheral-triage` 是九类外设症状，新图分别是**硬件 H1–H4** 与 **RTOS R1–R4**。
- ch28：`ch28-h745-contracts` 是五契约静态矩阵，新图是**HSEM 三条边界**（所有权/通知 vs payload vs cache）。
- ch11：`ch11-backup-path` 是供电路径，新图是**魔数启动判定 + BKP 宽度**。
- ch19：`ch19-*` 是 IAP/日志/选型，新图是**两条采样实现**（TIM 中断 vs TIM+DMA）。
- ch15：章首动画是调度器状态机，新图是**RTOS 与 NVIC 两套编号规则**。
- ch12：`ch12-flash-triage` 是擦写错误分诊，新图是**末页地址算术**（容量→页→末页边界）。
- ch04：新图是**实验证据卡**，不是现有优先级/EXTI 链路的复述。

## 5. 图的设计与证据边界

- 视觉轨：Handraw 知识轨，沿用 `tools/handraw_track/hd.py` 原语（米色纸、抖动墨线、
  普鲁士蓝/鼠尾草绿/砖红/那不勒斯黄、底部「原理示意 / 非实拍」徽章）。
  新图对照 `stm32-book/audits/visual-anchors-reverse-2026-11-10.md` 锚点 1/2 校色布线。
- 生成：每章在 `tools/handraw_track/fig_chNN.py` 增函数，固定 seed，输出 SVG；
  `render.py` 生成 1152×864 PNG；PNG 入库，CI 不重渲染。同种子重建必须字节一致。
- 文案：`embed_chNN.py`（或 `embed.py` 的章函数）写 zh/en 两版 alt 与图注；
  图注回答四问——看哪里 / 证明什么 / 不能证明什么 / 来源（RM/DS/PM 或正文公式）。
  不得把表格抄成图；不得出现「实测」「波形」等证据口吻。
- 图注/alt 中出现的一切寄存器、数值、版本号必须能在该章正文找到；
  找不到就不画，不新增事实。

## 6. 测试锁与登记更新

| 锁 | 变更 |
| --- | --- |
| `test_advanced_visuals.py` `CHAPTERS` | ch16 18→19、ch18 16→18、ch28 25→26、ch11 18→19、ch19 19→20、ch15 18→19、ch12 18→19、ch04 18→19；对应 asset 元组按插入位置加新图名 |
| `test_book_audit.py` `PHASE`/序列锁 | 受影响章的 `asset_sequence`、`pdf_visual_anchors` 等值重钉；新增 `EN_GAP_BATCH_BUDGETS = {"16":2000,"18":2000,"28":2000,"11":2000,"19":2000,"15":2000,"12":2000,"04":2000}` 与 `test_en_visual_gap_batch_budget` |
| `test_book_audit.py` zh 门 | 不改（ch26=1,231 例外保留） |
| `stm32-book/tests/fixtures/figure-types.json` | +9 条（key `illustrations/handraw/<id>.png`，caption/chapter/type） |
| `assets/illustrations/handraw/` | +9 SVG +9 PNG（成对） |
| `stm32-book/audits/` | 新批审计 `b54-en-gap-close.md`（执行后写） |

## 7. 执行工作流（批准后）

1. **冻结事实**：按 §4 表逐图列出正文事实行（zh/en 各核对一次）。
2. **生成**：写 `fig_chNN.py` 图函数 → SVG → render PNG → 对照视觉锚点与接触表目检。
3. **嵌入**：zh/en 同一位置插同一图序（图块 + 双语图注 + alt）。
4. **登记**：`figure-types.json`、`test_advanced_visuals`、`test_book_audit` 同步。
5. **复测**：`audit_book` 跑 8 章（≤2,000）与全书（zh 不回退、锚点不减、parity 通过）。
6. **全量门**（串行）：
   ```bash
   python -m pytest stm32-book/tests -q
   python tools/check_assets.py
   python stm32-book/build_html.py --check
   python stm32-book/build_html.py --lang en --check
   python tools/slop_lint.py
   git diff --check
   ```
7. **成书**：串行构建 zh/en PDF 与 EPUB，记录页数/体积；对新增图页做页样目检
   （图注无孤行、无溢出、PDF 第一眼可读）。
8. **提交**：分支 `improve/b54-en-gap-close`，单提交覆盖本批；PR → CI（book/book-en 绿）
   → 合并删分支；审计写入 `stm32-book/audits/b54-en-gap-close.md`。

## 8. 风险与边界

- **指标定性**：en ≤2,000 是新设批次目标，不是既有硬门；它按 en/zh 字符比
  （≈2.2×）取整，避免用英文字符直接撞中文预算造成的假超线。批次结束后
  若继续推进 B55，可把目标按章再收紧。
- **剩余库存（B55 候选，不在本批）**：en >2,000 的其余 13 章——
  09=2544、17=2531、08=2481、14=2454、05=2333、13=2297、20=2293、
  10=2234、02=2228、03=2153、07=2142、24=2100、27=2030。
- **表格走廊**：ch12 坑表与 ch28 五契约表不拆不改；图放表外，靠双图把
  ch12 的 1,399 表段维持为独立段（1,793 含学习目标，仍 ≤2,000）。
- **版面增长**：+9 图约 +5–9 页；PDF 版式门按 b51 命令复跑，本地与 CI
  分页差异按 b51 记录的平台噪声处理，不改版图凑数。
- **无硬件**：本批不产生任何新的实拍/测量证据；知识轨图不得冒充真证。

## 9. 完成定义

- [ ] 8 章 en `max_visual_gap_chars` ≤2,000，且无其他章 en gap 变差。
- [ ] zh 29 章 ≤1,200（ch26=1,231 例外）、锚点不减、deficit=0。
- [ ] zh/en `asset_sequence` 一致；9 张图双语图注/alt 齐全且四问完整。
- [ ] 图可由 `fig_chNN.py` 同种子重建；`figure-types.json` 登记 9 条。
- [ ] 全量 pytest、链接、HTML/PDF、EPUB、slop_lint、git diff --check 全绿。
- [ ] 新增图页样目检通过；`b54-en-gap-close.md` 记录前后对比与验证命令。

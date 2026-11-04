# B2 合流硬门审计（§10.2）——ch00 / 01 / 02 / 04 / 05

状态：2026-11-04，基线 main `a17536c`。本轮新增 11 张自绘静态 SVG（ch00×3、ch01×4、ch02×2、ch04×1、ch05×1），2 处既有图移位纠偏（ch02 hse-fail→§6、ch04 gpio-input-interrupt→§3），1 处布局修复（flash-path ISP/DFU 盒 84→60、host 行 574→596，`<text>` 内文不变，text_hash 不变），5 章 zh/en 同步嵌入与出处卡维护，测试锁扩展。全部门验通过（见「验证记录」）。

## 已完成前置

- B1（ch03）硬门先行合入：main `a17536c`，CI run 41741154618 双 job 绿。
- `tools/audit_book.py` 旧表 target 保持不动（ch01=6）：全局切 overlay 口径会打红 B3–B6 未改造章；旧→新数值由本文档登记，工具升级留 B7 普查。
- raw-path 加固、双语 manifest 校验、compass 锁扩在前置批次完成。

## 改章前缺陷清单（5 章）

| 章 | 改前缺陷 | 本轮处置 |
|---|---|---|
| ch00 | 缺 §15.3 OSS 出处卡（project-examples 未登记）；无图区间超中章上限 | 补 3 张自绘图（boot-triage / accept-gate / learn-loop）+ sources 追加 project-examples |
| ch01 | 锚点 5 低于 overlay 长章下限 9；缺烧录通路对比图与下载排错图；无照片引用（真证轨缺口，如实登记，不以 AI 图伪装实拍） | 补 flash-path（对比型）+ flash-triage（排错型），锚点 5→9；sources 既有卡已覆盖，未动 |
| ch02 | 缺 OSS 登记（spl-f1-mirror 未入卡）；hse-fail / boot-mode 图嵌错节（语义错位） | 双图移位纠偏（hse-fail→§6 时钟树、boot-mode→§5 启动模式）+ sources 追加 spl-f1-mirror |
| ch04 | gpio-input-interrupt 动画嵌 §4 无上下文 | 动画移至 §3 中断响应全流程；freertos-priority / project-examples 既有卡满足 §15.3 |
| ch05 | 缺排错图；project-examples 未登记 | 补 sample-05-pwm-debug（§3 后，PSC=71/ARR=999→1 kHz 勘误口径随图注落盘）+ sources 追加 project-examples |
| 通用 | can-500k.gif 无任何章引用 | 登记为观察项，处置留 B7 普查（本轮不删不引） |

## Sepia 删除 / 回退检查

本轮零删除：仅新增图、新增出处卡、移动 2 处既有图位置、1 处布局修复。无测试/断言弱化；契约守卫只扩展：资产清单 172→183、ch01 锚点锁 7→9、ch00/01/05 计数元组扩展、compass 锁扩 4 处（test_sample_chapters:243-250、test_batch2:268、test_batch3:318/406）。

## §15.2 锚点下限与无图区间登记

口径（本轮锁定）：

- 锚点 = 图 / 表 / 可嵌入动画首帧；章首视频块不计（audit_book `extract_visual_anchors` 先剥离 `VIDEO_BLOCK_RE`）。
- 下限 = 图+表口径；无图区间 = 图口径（表不破区间）。
- 门测 zh 口径；en gap（3,070–4,487）不入门（双语同步嵌入，英文行宽差异不构成 zh 违规）。
- `audit_book.py` target 仍为旧表（升级留 B7）；overlay 数值以本文档为准。

档位合同（BOOK_CLASSIC_CONVERGE_SPECS §15.2 L579-581）与 B2 落地：

| 档 | 旧表下限（§6.3 区间最小值） | Overlay 下限 | 无图区间 | B2 章 |
|---|---|---|---|---|
| 短章 | 3–4 | 旧+1（×90%） | — | （无） |
| 中章 | 4 | 4+2=6（×85%） | ≤1,000（=1,200×85% 取整到百） | ch00 / 02 / 04 / 05 |
| 长章 | 6 | 6+3=9（×80%） | §6.3 长章行无区间上限 → 定性 | ch01 |

实测（zh，audit_book 复测）：ch00 7/6 ✓、ch01 9/9 ✓、ch02 7/6 ✓、ch04 6/6 ✓、ch05 6/6 ✓（五 deficit=0，zh/en asset_sequence parity 全 True）。

无图区间终态（zh，drop_code，图口径，>1,000 加粗）：

| 章 | 区间（起节 → 止节） | 长度 |
|---|---|---|
| ch00 | **地址抄对，型号也要对 → 4. 硬件采购清单** | **1,255** |
| ch00 | **3. 三阶段学习路线图 → 硬件与接线** | **1,240** |
| ch01 | 关键插图 → 4. 一个标准工程目录结构 | 1,867 |
| ch01 | 6. 编译/烧录/调试 → 芯片被读保护时怎么解锁 | 1,374 |
| ch01 | VS Code → 10. 下载算法对照 | 1,519 |
| ch01 | 章首 → 时序与状态 | 1,000 |
| ch02 | **章首 → 时序与状态** | **1,243** |
| ch02 | **关键插图 → 5. 启动模式 BOOT0/BOOT1** | **2,465** |
| ch02 | **6. 时钟树与分频 → 章末** | **1,624** |
| ch04 | **关键插图 → 3. 中断响应全流程** | **1,752** |
| ch04 | **4. EXTI 外部中断 → 章末** | **1,970** |
| ch05 | **关键插图 → 4. PWM 模式与公式** | **1,855** |

例外登记（8 处超 1,000 区间；理由 = §6.3「代码块、长表和公式可以改变间距，但不能掩盖图片堆开头」允许的密集段；补偿锚点给位置）：

| 章 | 区间 | 理由 | 补偿锚点 |
|---|---|---|---|
| ch00 | 1,255 | 型号核对 + 系列选择为纯表格决策段 | 前缘 sample-00-boot-triage；末端紧邻 sample-00-accept-gate |
| ch00 | 1,240 | 三阶段清单 + 反模式清单双列表段 | 中部 sample-00-learn-loop；末端 first-lab-wiring / first-success-gates 集群 |
| ch02 | 1,243 | 摘要 + 学习目标 + 核心原理纯文字 | 末端 clock-tree + sample-02-clock-tree + clock-css.gif 集群 |
| ch02 | 2,465 | 系列对比表 + 内核特性表 + 存储器映射表三表连排 | 末端 memory-map（§4 末）；随后 peripheral-bus / sample-02-boot-mode 集群 |
| ch02 | 1,624 | 分频推导文字 + 硬件接线 + 排错代码段 | 头部 sample-02-hse-fail（§6 末） |
| ch04 | 1,752 | 原理 / 时序 / 优先级机制文字 + 向量表段 | 末端 interrupt-priority + nvic-preempt.gif（§2） |
| ch04 | 1,970 | C 语义 / 常见坑 + 代码段 | 头部 sample-04-exti-triage（§4 末）；gpio-input-interrupt 在 §3 |
| ch05 | 1,855 | 定时器分类表 + 时基公式推导（公式密集） | 末端 timer-modes + sample-05-pwm-debug（§3）；pwm-breath.gif 随后 |

ch01（长章，定性口径）：四段区间 1,867 / 1,519 / 1,374 / 1,000。§6.3 长章行无区间上限，×80% 无基数，按定性要求核验「原理 / 实现 / 证据 / 排错 / 迁移各一处」：swd-vectors（原理）、flash-path（实现通路）、build-accept（证据/验收）、debug-connect + flash-triage（排错）、project-structure（工程迁移）——全覆盖。锚点 5→9 的两张补图不走例外路径（§15.2 L570 禁以旧下限满足为由跳过）。

## §15.1-23 三类型 / §15.1-24 可播放动画

| 章 | 概念 | 对比 | 排错 | ≥1 可播放动画 |
|---|---|---|---|---|
| ch00 | accept-gate / learn-loop / first-success-gates | boot-state | boot-triage | ✓ toolchain-flow.svg（SVG 动画） |
| ch01 | swd-vectors / single-build-contract / build-accept | flash-path | debug-connect / flash-triage | ✓ swd-fetch.gif |
| ch02 | clock-tree / memory-map / peripheral-bus | sample-02-clock-tree / boot-mode | hse-fail | ✓ clock-css.gif |
| ch04 | nvic-interrupt-flow / exception-stack | interrupt-priority | exti-triage | ✓ nvic-preempt.gif + gpio-input-interrupt.svg（SVG 动画） |
| ch05 | timer-pwm / sample-05-pwm-1khz | timer-modes | pwm-debug | ✓ pwm-1khz.gif + pwm-breath.gif |

五章三类型全覆盖，每章 ≥1 可播放动画（gif 或 SVG 动画，章首视频块之外可嵌入）。

## §15.4 B2 三表

### ch00（7 资产）

| 表1 插图 | 类型 | 来源 |
|---|---|---|
| sample-00-boot-state.svg | 对比 | 自绘·静态 |
| sample-00-boot-triage.svg | 排错（新） | 自绘·静态 |
| sample-00-accept-gate.svg | 概念（新） | 自绘·静态 |
| sample-00-learn-loop.svg | 概念（新） | 自绘·静态 |
| first-lab-wiring.svg | 概念 | 自绘·静态 |
| first-success-gates.svg | 概念 | 自绘·静态 |

| 表2 动画 | 状态 |
|---|---|
| toolchain-flow.svg（assets/animations/） | 在用，章首引用，SVG 动画 |

| 表3 出处 | 定性 | 本轮 |
|---|---|---|
| project-guide | 项目原始资料 | 既有 |
| rm0008 / ds5319 / rm0008-boot | ST 官方规范 | 既有 |
| project-examples | OSS | 新增 |

### ch01（9 资产）

| 表1 插图 | 类型 | 来源 |
|---|---|---|
| boot-sequence.svg | 概念 | 自绘·静态 |
| sample-01-swd-vectors.svg | 概念 | 自绘·静态 |
| single-build-contract.svg | 概念 | 自绘·静态 |
| sample-01-flash-path.svg | 对比（新） | 自绘·静态 |
| project-structure.svg | 概念 | 自绘·静态 |
| sample-01-flash-triage.svg | 排错（新） | 自绘·静态 |
| sample-01-debug-connect.svg | 排错 | 自绘·静态 |
| sample-01-build-accept.svg | 概念 | 自绘·静态 |

| 表2 动画 | 状态 |
|---|---|
| swd-fetch.gif | 在用（§3），gif |

| 表3 出处 | 定性 | 本轮 |
|---|---|---|
| project-guide | 项目原始资料 | 既有 |
| pm0056 / pm0056-vector / pm0075-rdp / rm0008-boot / ds5319-swd | ST 官方规范 | 既有 |
| stm32cube-f4 / clion-embedded / platformio-vscode | OSS | 既有 |

### ch02（7 资产）

| 表1 插图 | 类型 | 来源 |
|---|---|---|
| clock-tree.svg | 概念 | 自绘·静态 |
| sample-02-clock-tree.svg | 对比 | 自绘·静态 |
| memory-map.svg | 概念 | 自绘·静态 |
| sample-02-boot-mode.svg | 对比（新，移位纠偏→§5） | 自绘·静态 |
| peripheral-bus.svg | 概念 | 自绘·静态 |
| sample-02-hse-fail.svg | 排错（新，移位纠偏→§6） | 自绘·静态 |

| 表2 动画 | 状态 |
|---|---|
| clock-css.gif | 在用（关键插图），gif |

| 表3 出处 | 定性 | 本轮 |
|---|---|---|
| rm0008 / rm0008-rcc / ds5319 / ds5319-clock | ST 官方规范 | 既有 |
| spl-f1-mirror | OSS 镜像 | 新增 |

### ch04（6 资产）

| 表1 插图 | 类型 | 来源 |
|---|---|---|
| nvic-interrupt-flow.svg | 概念 | 自绘·静态 |
| sample-04-exception-stack.svg | 概念 | 自绘·静态 |
| interrupt-priority.svg | 对比 | 自绘·静态 |
| sample-04-exti-triage.svg | 排错（新） | 自绘·静态 |

| 表2 动画 | 状态 |
|---|---|
| nvic-preempt.gif | 在用（§2），gif |
| gpio-input-interrupt.svg | 在用（新移位→§3），SVG 动画 |

| 表3 出处 | 定性 | 本轮 |
|---|---|---|
| pm0056 / pm0056-nvic / rm0008 / rm0008-exti | ST 官方规范 | 既有 |
| freertos-priority / project-examples | OSS | 既有 |

### ch05（6 资产）

| 表1 插图 | 类型 | 来源 |
|---|---|---|
| timer-pwm.svg | 概念 | 自绘·静态 |
| sample-05-pwm-1khz.svg | 概念 | 自绘·静态 |
| timer-modes.svg | 对比 | 自绘·静态 |
| sample-05-pwm-debug.svg | 排错（新） | 自绘·静态 |

| 表2 动画 | 状态 |
|---|---|
| pwm-1khz.gif | 在用（关键插图），gif |
| pwm-breath.gif | 在用（§5 后），gif |

| 表3 出处 | 定性 | 本轮 |
|---|---|---|
| rm0008 / rm0008-tim / ds5319-tim | ST 官方规范 | 既有 |
| project-examples | OSS | 新增 |

各章 title / url / license 明细见 `stm32-book/manifest.json` 的 `sources` 注册表；§15.3 每章 ≥1 GitHub OSS 满足（ch00 project-examples、ch01 stm32cube-f4 等、ch02 spl-f1-mirror、ch04 freertos-priority/project-examples、ch05 project-examples）。

## 知识轨哈希（本轮新增 11 张自绘 SVG）

口径：text_hash = sha256( "\n".join(所有 `<text>` 元素内文) )，与 `stm32-book/tests/test_sample_svg_c.py` ROWS 锁同口径；文件字节含 CRLF 不参与断言。

| 资产 | 字节 | text_hash |
|---|---|---|
| diagrams/sample-00-accept-gate.svg | 9,549 | 487806482cb3425ed05fece88056fc3a1c1cf4fe38ed27c4815b5446be92129d |
| diagrams/sample-00-boot-triage.svg | 10,014 | a9459d49838934d93ceb23b754cd24d98204533b91876828b19371d1ec0707dc |
| diagrams/sample-00-learn-loop.svg | 12,014 | f6e3cb6fb26e7495c348d26bd11143a1c181c3efe45e67975bea9bc970d6a728 |
| diagrams/sample-01-build-accept.svg | 10,621 | 9e6c95fbdcb962e485b2a2a866ee6ee5c00c17853ed8d2fe18c7c8d47209faa0 |
| diagrams/sample-01-debug-connect.svg | 10,029 | bea64b761d5fd1c18356a9ec5ec15b3a7ef8c73712440693af25c7d64ab23196 |
| diagrams/sample-01-flash-path.svg | 11,620 | a57ee9fa3594d3ceae8acc158dd93ff19250d40914095c29209cd755cd67625a |
| diagrams/sample-01-flash-triage.svg | 8,490 | 13384461f93ab19f757290a55ed373c02d752386c25101432395228931f697ac |
| diagrams/sample-02-boot-mode.svg | 8,862 | b4aa807c16c1b7732f624f8b68f3873879d2948e1c934c6c395cbacdd3410693 |
| diagrams/sample-02-hse-fail.svg | 8,713 | 47cb6b3456c1afbccb2362ffded498b6f451ca3b0236489210451bcba8d06d93 |
| diagrams/sample-04-exti-triage.svg | 12,593 | 5b9031358e707823f20bd002178ccfcd2e70917da6a0731b0c8d895398400999 |
| diagrams/sample-05-pwm-debug.svg | 12,087 | 90918e07f70e4c221e85dbeea40550c1a71850eba141baa1f8e9087e45610b6d |

生成器：`tools/sample_figs_b2/`（ch00_b2 / ch01_b2 / ch02_b2 / ch04_b2 / ch05_b2，复跑即可重建全部 11 张）。

## 验证记录（布局修复后终态）

- 定向 7 模块（advanced_visuals / book_audit / sample_chapters / batch2 / batch3 / sample_svg_c / batch4）：**38 passed**（2.21s）。
- 全量 pytest：**178 passed**（109.48s，含修复后复跑）。
- `tools/check_assets.py`：实拍 3/3 哈希匹配，链接 **1322/1322** 有效。
- `stm32-book/build_html.py --check` zh **PASS**（6,236,819 B，29 章）；`--lang en` **PASS**（6,288,639 B）。
- `tools/audit_book.py --format json`（`.temp/b2-audit.json`）：五章 anchors 达标、deficit=0、zh/en asset_sequence parity 全 True。
- SVG 契约自查：11 张 rx ⊆ {4,8}、stroke-width ⊆ {1,1.5,2}、含「自绘」页脚、无 `<animate`/`@keyframes`/`animation:`。

## §10.2 本轮勾选（B2）

- [x] 改章前缺陷清单 + 三表（§15.4）×5 章落盘（本文档）
- [x] §15.2 档位登记：旧→新下限、实测锚点、8 处例外（理由+补偿锚点）、ch01 长章定性覆盖
- [x] §15.1-23 三类型、§15.1-24 每章 ≥1 可播放动画
- [x] §15.3 每章 ≥1 GitHub OSS 出处卡
- [x] 知识轨哈希登记（11 张，text_hash 口径与测试锁一致）
- [x] 测试锁扩展且全绿（38 定向 + 178 全量，零断言弱化）
- [x] 双语 HTML 契约门 + 资产链接门通过
- [ ] 旁白/视频轨：不在 B2 范围（视频批次 ch21–28 统一处理）

## 下一步

B3（ch06–10）：复用本轮管线（audit → 缺陷清单 → 补图/移位 → 测试锁 → 硬门），逐章过 §10.2。

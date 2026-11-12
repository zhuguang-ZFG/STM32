# 双书合并设计：通往单片机之路

状态：已确认（信息架构与工程设计均经用户逐节确认）· 2026-11-12

范围：根 STM32 书与 MCU 姊妹书的正文合并、源树重组、构建链与站点收敛。

依据：根 [内容指南](../../CONTENT_GUIDE.md)、[Book 2.0 重构 Spec](../../../stm32-book/BOOK_REDESIGN_SPEC.md)、[经典化改造 Specs](../../../stm32-book/BOOK_CLASSIC_CONVERGE_SPECS.md)、[MCU 质量契约](../../../mcu/.trellis/spec/docs-site/quality-contract.md)、[motor-control 计划](../../../plans/2026-11-11-motor-control/prd.md)。

## 1. 背景与目标

现状：

- 根书《STM32 实战》29 章 + 6 附录，中英双语，HAL 实战线（F103 为主）。
- MCU 书《通往单片机之路》94 章 + 7 附录，仅中文，寄存器/源码级 + 多平台（F407、FreeRTOS、RT-Thread、ESP32-S3、GD32）。
- 两套 manifest、构建器、测试、CI、站点配置；`mcu/docs/` 同时是 VitePress 站点源。
- `plans/2026-11-11-motor-control/` 的 29–32 章草稿尚未接入任何书。

目标：把两书正文合并改写为一本中文新书，全新目录重排，源文件级重组，单站挂在 `/STM32/` 根。

非目标：

- 不做英文翻译；英文版按第 4.7 节归档下线。
- 不改写 `examples/`、`mcu/code/`、固件与示例代码；只改书稿、站点与构建。
- 不新增硬件实测要求；既有验证状态保持，缺硬件/工具链的项如实记 `BLOCKED`/`UNVERIFIED`。
- 不自动归档或改写 `mcu/.trellis/tasks/` 任何历史任务状态。
- 本设计不授权任何远程推送、Pages 切换或发布动作；B5 需另行发布指令。

## 2. 锁定决策

| # | 决策 | 结论 |
| --- | --- | --- |
| D1 | 合并方式 | 正文合并改写（非合订、非仅归档） |
| D2 | 目录结构 | 全新目录重排（不沿用任一旧目录） |
| D3 | 落位方式 | 源文件级重组：直接重排 `docs/` 与 `mcu/docs/`，原两书最终不复存在 |
| D4 | 语言 | 仅中文；英文归档下线 |
| D5 | 站点 | 单站，迁到 `/STM32/` 根；旧 `/STM32/mcu/**` 生成跳转存根 |
| D6 | 目录方案 | C 主题矩阵制：每主题一章，章内多平台对照，约 40–46 章 |

## 3. 信息架构

### 3.1 书名

《通往单片机之路：从点亮一颗灯到交付一个系统》

### 3.2 卷册与章目（46 章）

| 章 | 标题 | 来源（根书 / MCU 书 / motor） |
| --- | --- | --- |
| **卷 0 · 语言与构建（7 章）** | | |
| 1 | 嵌入式 C 的内存模型与指针 | C0/C1/C2 + 02（存储器） |
| 2 | volatile、const 与未定义行为 | C3/C7 |
| 3 | 结构体、ABI 与寄存器映射 | C4 + S1/S3 |
| 4 | 函数指针、状态机与调用约定 | C5/C6 + 04 |
| 5 | 工具链与四步构建 | B0/B1/B2 + 01 + S0 |
| 6 | 链接脚本、启动与 map 体积审计 | B3/B4/B5 |
| 7 | 构建系统与遗留栈（Make/CMake/IDF/SPL） | B7 + 26 + S15 |
| **卷 1 · 裸机驱动（10 章）** | | |
| 8 | 架构、存储器地图与时钟树 | S1/S2 + 02 + G1 |
| 9 | GPIO | S3 + 03 + G2/V4 + P2 |
| 10 | 中断、NVIC/EXTI、CLIC 与双核 | S4 + 04 + V1 + P4 |
| 11 | SysTick 与时基（含 RTC） | S5 + 05 + 11（RTC） |
| 12 | 定时器与 PWM | S6 + 05 + P7 |
| 13 | UART 与可恢复帧协议 | S7 + 06 + C8 + P5 + G3 |
| 14 | DMA | S8 + 10 |
| 15 | ADC/DAC 与采样 | S9/S10 + 09 |
| 16 | I2C 与 SPI | S11/S12 + 07/08 + P6 |
| 17 | Flash、IAP 与 OTA | S13 + 12 + P10 |
| **卷 2 · 可靠性与故障（3 章）** | | |
| 18 | 低功耗设计 | S14 + 16 + P11 |
| 19 | 看门狗、复位与 HardFault | S17 + 11（看门狗）+ S16 + P13 |
| 20 | 调试、性能与测量 | 17 + B6 |
| **卷 3 · RTOS（7 章）** | | |
| 21 | 为什么需要 RTOS | F0 + 15 |
| 22 | 任务、TCB 与调度 | F1/F3 + R1 |
| 23 | 上下文切换与移植 | F2/F8 + R7 + R0 |
| 24 | 队列、信号量与通知 | F4/F5/F6 + R2 |
| 25 | 内存管理 | F7 + R3 |
| 26 | 设备框架、shell 与配置系统 | R4/R5/R6 |
| 27 | 双 OS 对照与选型（含 Zephyr） | 对比0/1 + 28 |
| **卷 4 · 多平台与连接（8 章）** | | |
| 28 | 芯片迁移方法论与引脚/外设差异 | 23/24/25 + G4 |
| 29 | GD32 系列对照（ARM + RISC-V） | G0–G3 + V0–V4 |
| 30 | ESP32-S3 架构、启动与工程 | P0/P1/P3 |
| 31 | ESP32 外设、驱动框架与音频链路 | P2/P5/P6/P7/P12 |
| 32 | Wi-Fi、蓝牙与 ESP-NOW | P8/P9 |
| 33 | 网络与协议栈（Ethernet/lwIP/MQTT/TLS） | 27 |
| 34 | 多核、Cache 与内存一致性 | P4 + 25/H7 |
| 35 | 现场总线与 USB（CAN/USB） | 13/14 |
| **卷 5 · 运动控制（4 章）** | | |
| 36 | 电机驱动与供电 | motor 29 |
| 37 | 直流电机开环调速 | motor 30 |
| 38 | 编码器与转速测量 | motor 31 |
| 39 | 速度闭环与 PI | motor 32 |
| **卷 6 · 实验与项目（3 章）** | | |
| 40 | 实物实验方法与仪器证据（含仿真边界） | E01–E08 方法论 + 21/22 |
| 41 | 双板综合项目（F407 + S3 记录器） | J1/J2 |
| 42 | 项目实战与交付验收 | 19 |
| **卷 7 · 交付与资料（4 章）** | | |
| 43 | AI 结对开发与提示词工作流 | A0/A1/A3 |
| 44 | 手册对账与幻觉防御 | A2/A4/A5 |
| 45 | 常见故障排查手册 | 18 |
| 46 | 资料、学习路线与开源地图 | 20 + 00 |

来源代号：无前缀数字 = 根书章节；C/B/S/F/R/P/G/V/E/J/A = MCU 书章节；motor = motor-control 草稿；附录见 3.3。

### 3.3 附录（6 份，两书合并去重）

| 附录 | 内容 | 来源 |
| --- | --- | --- |
| A 工程深读 | UART+DMA 五契约与帧协议工程复盘 | 根 A-工程深读 + MCU A-工程深读 |
| B 配套工程索引 | 47+14 个配套工程/例程索引 + 平台对照矩阵 | 根 B-例程索引 + MCU B-例程索引 + `mcu/code/projects.json` |
| C 习题与自测答案 | 两书习题/自测答案 + 13 组测验 JSON 自动汇入 | 根 C-习题答案 + MCU C-习题答案 |
| D 术语表 | 按主题合并去重的术语与边界说明 | 根 D-术语表 + MCU D-术语速查 |
| E 来源、版本与许可 | 合并来源注册表、版本与许可边界 | 根 E-参考资料 + MCU E-来源/版本/许可 + 两份 `sources` |
| F 开源项目与社区地图 | 开源项目、社区与学习路线图 | 根 F-开源地图 + MCU G-开源地图 + 根 F-学习路线收束 |

### 3.4 写作契约

- 每章统一三层：**先做出来（实战）→ 机制/源码（深潜，HTML 折叠、PDF 展开）→ 跨平台迁移边界**。
- 沿用 `BOOK_REDESIGN_SPEC` 第 3 节"不做什么"与 `tools/slop_lint.py`；不编造故障经历、测试数据与实验结果。
- 每章保留"本章罗盘"：问题 / 交付 / 边界 / 依据锚点；来源必须先在注册表登记。
- 章内按需选择功能块，不机械套模板；E01–E08 实验拆入对应主题章的"测量与证据"节，附录 B 保留索引。
- 两书正文只保留一份源：新 `docs/` 树；不在 `book/` 再存专题正文。

### 3.5 平台对照规则

- 每章标注 1 个主线平台 + 1–2 个对照平台，不强行四平台并列。
- 全书平台覆盖由附录 B 的对照矩阵兜底：F103、F407、GD32（含 RISC-V）、ESP32-S3 在每个主题域至少出现一次。
- 跨平台事实必须可对账：寄存器名、时钟、引脚与电气参数不得跨型号泛化。

### 3.6 内容去向完整性

- `plans/2026-11-12-merged-book/mapping.json` 记录两书全部 123 个章节文件与全部附录（含根书学习路线收束页）的逐文件去向（目标章、用途、状态）。
- 不允许静默丢弃内容；确需淘汰的段落必须在该文件记录理由，并进入验收审查。

## 4. 工程设计

### 4.1 源树终态

```text
docs/                        # 唯一站点 + 书稿源
  .vitepress/                # 由 mcu/docs/.vitepress 迁入
  manifest.json              # 唯一 manifest（46 章 + 6 附录）
  index.md  guide/  reference/  video/  animations.md   # 站点非书稿页迁入
  v0-foundations/            # 01-… md
  v1-drivers/
  v2-reliability/
  v3-rtos/
  v4-platforms/
  v5-motion/
  v6-labs-projects/
  v7-delivery/
  appendix/
  public/                    # 合并 mcu/docs/public 与图片资产
book/                        # 统一构建器（HTML/PDF/EPUB/downloads/tests）
scripts/legacy-redirects.mjs # 旧 URL 跳转存根生成
plans/2026-11-12-merged-book/
  mapping.json               # 123 源 → 46 章 + 6 附录
  evidence/                  # 各批验收证据
mcu/                         # 保留代码、固件与示例；不再含站点与书稿
```

- `docs/en/`、`manifest-en.json`、英文构建与测试删除；git 历史与 Release v1.3.1 保留追溯。
- `docs/CONTENT_GUIDE.md` 与 `docs/superpowers/` 不属于书稿，保留原位。

### 4.2 构建链

- 以 `mcu/mcu-book` 构建器为技术底座（组件静态化、SMIL 动画、details 打印展开、三级书签、数据 URI、契约测试），吸收根书构建器能力（封面/版本页/主题索引/术语表/SPL 审计/EPUB）。
- 收敛为 `book/` 包：`build_html.py`（HTML+PDF）、`build_print.py`、`check_pdf.py`、`build_epub.py`、`publish_downloads.py`、`tests/`。
- 产物：`book/dist/` 下 HTML、PDF、EPUB 与 downloads 发布包；PDF 版式审计与 EPUB 契约纳入构建门。
- 旧 `stm32-book/`、`mcu/mcu-book/` 在 B5 删除。

### 4.3 站点与 URL 迁移

- VitePress `base` 改为 `/STM32/`；导航与侧栏由唯一 manifest 生成。
- `scripts/legacy-redirects.mjs` 按 mapping 生成旧 `/mcu/**` 路径的 meta-refresh + canonical 存根（94 章 + guide/reference 等全部旧页面），覆盖率由 CI 核对。
- 部署 staging 根即站点根：不再组装 `mcu/` 子树，移除根入口 redirect 页。
- 搜索索引、SEO、外链巡检与静态资源路径随 base 切换全部重算。

### 4.4 CI 收敛

- `book.yml` / `mcu-book.yml` / `mcu-quality.yml` / `mcu-deploy.yml` / `mcu-links.yml` 收敛为：
  - `book.yml`：书稿门 + HTML/PDF/EPUB 构建与契约；
  - `site.yml`：站点构建、站点检查与浏览器冒烟；
  - `deploy.yml`：Pages 组装与发布；
  - `links.yml`：外链巡检。
- 新增回归：mapping 完整性（123→46 全覆盖）、旧 URL 跳转覆盖率、平台对照矩阵覆盖、锚点/图片/测验/来源对账。
- 触发矩阵（只改书稿 / 只改站点 / 只改代码 / 混合改动 / 手动发布）逐类验证；远程 required checks 现状核实后记录，不擅自改分支保护。

### 4.5 运动控制合流

- `plans/2026-11-11-motor-control/` 的 29–32 章草稿并入卷 5（36–39 章）；examples 与 firmware CI 保留。
- 草稿不再接入旧 `stm32-book/`；该计划的章节合同与数值断言测试随新章迁移。

### 4.6 历史与归档

- Trellis 历史任务、计划与证据只读保留，不因合并自动归档或改状态。
- 英文版删除前打 tag 记录；Release v1.3.1 附件保留。
- B5 切换前的旧部署 artifact、旧站点配置与 tag 作为回滚依据保留。

## 5. 分批实施（保持 main 绿）

分支 `feat/merged-book` + worktree；每批独立 PR、独立验收。

| 批次 | 内容 | 出口条件 |
| --- | --- | --- |
| B0 | 新 `docs/` 骨架、唯一 manifest、mapping.json、`book/` 构建器底座、测试骨架 | 新旧两套并存构建通过；mapping 完整性门生效；旧书/旧站零改动 |
| B1 | 卷 0–1（17 章）改写与迁移 | 17 章罗盘/slop_lint/锚点/资产/测验全过；站点临时构建通过 |
| B2 | 卷 2–3（10 章） | 同上；映射状态同步更新 |
| B3 | 卷 4–5（12 章，含 motor 合流） | 同上；motor 数值断言测试迁移通过 |
| B4 | 卷 6–7 + 6 附录（7 章 + 附录） | 全书 46 章 + 6 附录齐备；HTML/PDF/EPUB 契约全过 |
| B5 | base 切 `/STM32/`、跳转存根、CI/部署收敛、删旧树/旧构建器、英文归档 | 旧深链跳转 100%、站点回读通过、main 全绿；需单独发布指令 |

B5 之前，旧 `mcu/docs` 站点与旧书构建保持原样发布；新树只进 CI 与本地验收，不提前切换线上入口。

## 6. 验收标准

- **AC1 映射完整**：mapping.json 覆盖 123 章与全部附录源文件（含根书学习路线收束页）；无未记录的去向或淘汰。
- **AC2 目录契约**：唯一 manifest 与 46 章 + 6 附录一一对应；每章罗盘、平台标注与来源登记齐全；slop_lint 全过。
- **AC3 构建**：单链产出 HTML/PDF/EPUB；三级书签、details 展开、图注、索引页码、EPUB 契约全过。
- **AC4 站点**：base `/STM32/`；旧 `/mcu/**` 深链跳转覆盖 100%；搜索、导航、导读、下载回读通过。
- **AC5 CI/部署**：四类 workflow 收敛并通过触发矩阵验证；required checks 现状有记录。
- **AC6 归档**：英文版与旧构建器删除后 main 全绿；git 历史与 Release v1.3.1 可回溯；无未解释的工作区修改。
- **AC7 发布安全**：B5 切换后回读首页/深链/搜索/下载；失败可按预案恢复旧 artifact。

## 7. 风险与回滚

| 风险 | 缓解 |
| --- | --- |
| 46 章几乎全部重写，周期长 | 分批 PR，每批独立验收；mapping 跟踪进度 |
| URL 迁移导致外链失效 | 跳转存根 + 覆盖率 CI + 外链巡检 |
| 英文下线影响现有读者 | Release v1.3.1 保留；删除前 tag；README 说明 |
| 构建器合并引入契约回退 | 以 MCU 构建器为底座，逐项迁移根书契约并留测试 |
| B5 切换失败 | 保留旧部署 artifact、旧 workflow 与 tag；失败恢复旧 artifact 后回读 |

## 8. 执行约束

- 远程推送、PR 合入与 Pages 切换均需单独授权；本规格不构成发布指令。
- 任一阶段失败/跳过如实记录 `BLOCKED`/`UNVERIFIED`，不以编译或本地构建替代真实上板证据。

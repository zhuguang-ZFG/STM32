# B50 · 实物与测量证据盘点（硬件重点章）

日期：2026-11-10 ｜ 分支：`improve/b50-hardware-evidence-1`（基于 e04dc1e = B49）｜ 计划：`docs/superpowers/plans/2026-11-08-book-visual-experience.md` B50

## 规则（spec 第 6.4 节）

- 只用许可允许再分发的**准确型号**照片（CC0 / CC BY / CC BY-SA / MIT / BSD / ISC）；逐张记录来源、许可、尺寸、SHA-256（`assets/photos/README.md`）。
- 找不到准确型号照片时设**待补证据位**，不用相似板卡代替。
- 不用 AI 生成图冒充实物、仪器或实验结果。

## 计数口径声明（重要）

`tools/audit_book.py::_asset_kind` 对不在 `photos/`、`animations/`、`diagrams/`、`boards/` 下的所有图片一律计为 `evidence`。因此 audit 的 `evidence_images` 计数 **不等于** truth-track 或实测证据——它把全部 Handraw 示意图也计入。经 `figure-types.json` 逐张核对：硬件重点章 **没有任何 truth-track 类型图，也没有任何仪器/仿真真实截图**；所有示意图均为 Handraw 知识轨（原理示意/非实拍）。下表「现有证据」按此口径如实列出。

## 本批动作

1. **ch21 实物图鉴补 3 张实拍**（该章此前 0 照片，纯自绘结构图）：
   - §1 BluePill：`bluepill-stm32f103c8t6.jpg`（Avandalen / Wikimedia Commons，CC BY-SA 4.0）+ `bluepill-stm32f103c8t6-popolon.jpg`（Popolon，CC BY-SA 4.0）——实拍对象均为 STM32F103C8T6，与本节结构图同型号。
   - §3 Nucleo-F411RE：`nucleo-f411re-embedded-world.jpg`（Ordercrazy / Thomas Springer，CC0 1.0）——与本节结构图同为 F411RE，是全章唯一「实拍与自绘对象一致」的板卡。
   - 图注均写明：能证明什么（板级布局/家族分区）、不能证明什么（芯片顶标/丝印不可辨 → 不能判别山寨；焊桥跳线不可辨）、许可与出处链接；zh/en 同序列。
2. **工作区 sample PNG 核查**：spec 所指「5 张未纳入版本控制的 sample PNG」在当前工作区**已不存在**（历史清理轮已处理）；本批另发现并删除 5 张无引用渲染孤儿 PNG（`sample-06-ore-overwrite-flow.png`、`sample-11-wwdg-window-flow.png`、`sample-28-supervisor-flow.png`、`sample-02-clock-tree.png`、`sample-05-pwm-debug.png`，SVG 原版均在库且为 canonical）。
3. ch21 相关资源新增实拍照片条目（指向 `assets/photos/README.md`）；ch21 锁 15→18（`<img>` 计数）、audit 资产序 22→25。

## 逐章证据盘点（figure-types.json 逐张核对 + audit 实测）

| 章 | 主题 / 重点板卡 | photos | Handraw 示意图（类型，全部非实拍） | 现有实测证据 | 缺口 / 待补证据位 |
|---|---|---|---|---|---|
| 01 开发环境搭建 | Blue Pill (F103C8T6) | 0 | 6 张：triage×2、technical×2、comparison×1、concept×1（调试连接环、RDP 解锁、四环境一 ELF、三条刷写路径） | 无 | 待补：开发环境首次连通的真实串口/日志截图（自捕获）；板卡 + ST-Link 接线实拍（ch01 不重复嵌入 ch21 已用的两张） |
| 06 串口 UART | Blue Pill + USB-TTL | 0 | 7 张：technical×5、comparison×1（波特率公式）、triage×1（帧格式、采样点、TX/RX 交叉、IDLE+DMA、ORE/FE、波特率分诊） | 无 | 待补：**UART 实际测量目标**——逻辑分析仪真实捕获的 UART 帧（起始位宽/校验位/帧错误）、RX IDLE 事件真实时序、USB-TTL 3.3 V 电平与 RS-232 电平对照测量截图 |
| 07 I2C 总线 | 外设接 Blue Pill | 0 | 6 张：technical×4、concept×1（上拉电容）、triage×1（START/ACK、地址、时钟拉伸、重复起始） | 无 | 待补：逻辑分析仪真实捕获——START 条件、ACK 位、从机时钟拉伸（SCL 被拉低段）、重复起始 |
| 08 SPI 总线 | 外设接 Blue Pill | 0 | 7 张：technical×5、triage×2（BR 表、CPHA 模式、字节交换、CS 包围、NSS 多机、JEDEC ID 分诊） | 无 | 待补：逻辑分析仪真实捕获——CPHA 0/1 采样沿差异、MISO 有效窗口；Flash JEDEC ID 真实回读日志截图 |
| 09 ADC 与 DAC | Blue Pill | 0 | 7 张：technical×3、calculation×2、concept×1（SAR 阶梯）、triage×1（采样时间、扫描序列、Vref 轨、Vrefint 校准计算） | 无 | 待补：万用表/示波器实测——VDDA 与 Vrefint 电压、DAC 输出端电压与缓冲器压差 |
| 10 DMA | Blue Pill | 0 | 7 张：technical×3、comparison×2、concept×1（传输相位）、triage×1（CNDTR 台账、请求节拍、通道映射、M2M vs 外设） | 无 | 待补：逻辑分析仪真实捕获——外设 burst 传输节拍、M2M 与传送完成时序 |
| 21 原理图与实物图鉴 | 5 款板卡 | **3**（本批） | 7 张：technical×4、comparison×2、triage×1（板卡对照、VDD 轨、HSE 负载、NRST/BOOT0、USB-TTL、最小五件、假 ID 分诊） | Blue Pill×2、Nucleo-F411RE 实拍 | 待补：BlackPill（WeAct 官方实拍，许可需核）、F4-Discovery、F103ZET6 大板准确型号实拍；PC13 LED 特写（README 已声明不可用 tardate-usb 冒充）；万用表/逻辑分析仪截图 |
| 23 G0 引脚 | Nucleo-G071RB + Blue Pill | 0 | 8 张：concept×2、comparison×2、technical×2、calculation×1、triage×1（启动树、part-id、G0/F1 对照、引脚对照、pinmux、SWD 分诊、实验证据） | 无 | 待补：Nucleo-G071RB 准确型号实拍（不得用 Nucleo-64 其他型号代替——焊桥/跳线随型号不同） |
| 24 L4 引脚 | Nucleo-L476RG | 2 | 10 张：technical×5、concept×2、comparison×2、calculation×1（模式、IDD、唤醒时钟、引脚复用、双固件、中断时序、占空比积分） | Nucleo-F411RE/F401RE 实拍（图注已声明**不是 L476RG**） | 待补：NUCLEO-L476RG 准确型号实拍（ST 产品页图片版权归 ST，需找 CC 许可实拍；找到前保留现状声明） |
| 25 H7 引脚 | Nucleo-H743ZI | 0 | 7 张（ch24/28 另含 H7 相关契约图） | 无 | 待补：Nucleo-H743ZI 准确型号实拍；H745/H743 实测时钟证据（MCO2 输出频率计读数截图） |

## 说明

- Wokwi / Renode 素材现状：`assets/diagrams/sample-22-{wokwi-scope,renode-path}.svg` + handraw 版均为**自绘示意图**，非模拟器截图。待补证据位：真实 Wokwi 运行截图、Renode 启动日志截图（自捕获，无许可问题）。
- ch03 已有 Blue Pill 实拍引用（`test_converge_ch03` 约束），本批不动。
- 待补证据位按章登记在上表；任何一项补入时必须按 spec 6.4 记录来源/许可/尺寸/SHA-256，找不到准确型号宁可空位也不用相似板卡；仪器截图类为自捕获证据，须保留原始文件名与采集条件说明。

## 验证记录

- `pytest tests/test_advanced_visuals.py tests/test_book_audit.py`：20 passed（ch21 锁 15→18、audit 序 22→25）。
- `tools/check_assets.py`：全部通过，2130/2130 链接、照片 5/5 哈希与尺寸匹配。
- `build_html.py --check --lang zh`：PASS；`--lang en`：PASS。
- 全量 `pytest`（stm32-book）：195 passed。

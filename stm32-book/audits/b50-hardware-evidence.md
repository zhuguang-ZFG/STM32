# B50 · 实物与测量证据盘点（硬件重点章）

日期：2026-11-10 ｜ 分支：`improve/b50-hardware-evidence-1`（基于 e04dc1e = B49）｜ 计划：`docs/superpowers/plans/2026-11-08-book-visual-experience.md` B50

## 规则（spec 第 6.4 节）

- 只用许可允许再分发的**准确型号**照片（CC0 / CC BY / CC BY-SA / MIT / BSD / ISC）；逐张记录来源、许可、尺寸、SHA-256（`assets/photos/README.md`）。
- 找不到准确型号照片时设**待补证据位**，不用相似板卡代替。
- 不用 AI 生成图冒充实物、仪器或实验结果。

## 本批动作

1. **ch21 实物图鉴补 3 张实拍**（该章此前 0 照片，纯自绘结构图）：
   - §1 BluePill：`bluepill-stm32f103c8t6.jpg`（Avandalen / Wikimedia Commons，CC BY-SA 4.0）+ `bluepill-stm32f103c8t6-popolon.jpg`（Popolon，CC BY-SA 4.0）——实拍对象均为 STM32F103C8T6，与本节结构图同型号。
   - §3 Nucleo-F411RE：`nucleo-f411re-embedded-world.jpg`（Ordercrazy / Thomas Springer，CC0 1.0）——与本节结构图同为 F411RE，是全章唯一「实拍与自绘对象一致」的板卡。
   - 图注均写明：能证明什么（板级布局/家族分区）、不能证明什么（芯片顶标/丝印不可辨 → 不能判别山寨；焊桥跳线不可辨）、许可与出处链接；zh/en 同序列。
2. **工作区 sample PNG 核查**：spec 所指「5 张未纳入版本控制的 sample PNG」在当前工作区**已不存在**（历史清理轮已处理）；本批另发现并删除 5 张无引用渲染孤儿 PNG（`sample-06-ore-overwrite-flow.png`、`sample-11-wwdg-window-flow.png`、`sample-28-supervisor-flow.png`、`sample-02-clock-tree.png`、`sample-05-pwm-debug.png`，SVG 原版均在库且为 canonical）。
3. ch21 相关资源新增实拍照片条目（指向 `assets/photos/README.md`），锁 15→18（`<img>` 计数）、audit 资产序 22→25。

## 逐章证据盘点（audit_book 实测 + 人工核查）

| 章 | 重点板卡 | photos | truth-track 证据 | 现有证据 | 缺口 / 待补证据位 |
|---|---|---|---|---|---|
| 01 起步 | Blue Pill (F103C8T6) | 0 | 6 | 结构图引用 ch21；启动/选型 truth-track 图 | 待补：开发环境实物对照（板卡 + ST-Link 接线实拍，可用 tardate-usb 类 CC 许可图）——ch01 不重复嵌入 ch21 已用的两张，避免一图多章 |
| 06 EXTI | Blue Pill | 0 | 7 | 波形/时序 truth-track；按键消抖证据图 | 待补：按键抖动示波器截图（真实波形） |
| 07 I2C | 外设接 Blue Pill | 0 | 6 | 时钟拉伸、ACK 时序 truth-track | 待补：逻辑分析仪 I2C 截图（START/ACK/时钟拉伸真实捕获） |
| 08 SPI | 外设接 Blue Pill | 0 | 7 | 模式对比、时序 truth-track | 待补：逻辑分析仪 SPI 截图（MISO 采样沿真实捕获） |
| 09 ADC/DAC | Blue Pill | 0 | 7 | 采样时间、量化 truth-track | 待补：万用表/示波器截图（VDDA、基准、DAC 输出电压实测） |
| 10 DMA | Blue Pill | 0 | 7 | 传输路径、半满回调 truth-track | 待补：逻辑分析仪截图（M2M / 外设burst 真实时序） |
| 21 板卡图鉴 | 5 款板卡 | **3**（本批） | 7 | 7 张自绘结构图 + Blue Pill×2 / Nucleo-F411RE 实拍 | 待补：BlackPill WeAct 官方实拍（其开源仓库有，许可需核）、F4-Discovery 与 F103ZET6 大板准确型号实拍；PC13 LED 特写（README 已声明不可用 tardate-usb 冒充）；万用表/逻辑分析仪截图仍缺 |
| 23 G0 引脚 | Nucleo-G071RB + Blue Pill | 0 | 8 | G0 启动树、part-id、SWD 分诊 truth-track；引脚 SVG | 待补：Nucleo-G071RB 准确型号实拍（不得用 Nucleo-64 其他型号代替——各型号焊桥/跳线不同） |
| 24 L4 引脚 | Nucleo-L476RG | 2 | 10 | Nucleo-F411RE/F401RE 实拍（图注已声明**不是 L476RG**） | 待补：NUCLEO-L476RG 准确型号实拍（ST 产品页图片版权归 ST，需找 CC 许可实拍；找到前维持现状并保留声明） |
| 25 H7 引脚 | Nucleo-H743ZI | 0 | 7 | H743 引脚 SVG、H745 契约 truth-track | 待补：Nucleo-H743ZI 准确型号实拍；H745 双核实拍（本章引用 ch28 契约图，非实物） |

## 说明

- Wokwi / Renode 素材现状：`assets/diagrams/sample-22-{wokwi-scope,renode-path}.svg` + handraw 版均为**自绘示意图**，非模拟器截图。待补证据位：真实 Wokwi 运行截图、Renode 启动日志截图（自捕获，无许可问题）。
- ch03 已有 Blue Pill 实拍引用（`test_converge_ch03` 约束），本批不动。
- 待补证据位共 12 项，全部登记在上表；任何一项补入时必须按 spec 6.4 记录来源/许可/尺寸/SHA-256，找不到准确型号宁可空位也不用相似板卡。

## 验证记录

- `pytest tests/test_advanced_visuals.py tests/test_book_audit.py`：20 passed（ch21 锁 15→18、audit 序 22→25）。
- `tools/check_assets.py`：全部通过，2130/2130 链接、照片 5/5 哈希与尺寸匹配。
- `build_html.py --check --lang zh`：PASS；`--lang en`：PASS。
- 全量 `pytest`（stm32-book）：195 passed。

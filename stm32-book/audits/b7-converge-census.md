# B7 · Classic Converge 全书覆盖率普查

> 依据 `BOOK_CLASSIC_CONVERGE_SPECS.md` §10.3 / §15.4 计划 31 / §11.3。
> 测量源：`tools/audit_book.py` JSON（**图**锚点口径；表未计入 PDF 锚点——与 §15.2「图/表/动画首帧」全文口径有差，见 §1）。
> 基线：`main` @ `8794d00`（B6 完成）。缺口**不**标完成。

## 0. 结论摘要

| 指标 | 达标 / 29 | 覆盖率 |
| --- | --- | --- |
| Overlay §15.2 锚点下限（图口径） | 29 / 29 | 100.0% |
| 动画 ≥1（audit `animations`） | 29 / 29 | 100.0% |
| 三类插图（启发式或批次门表） | 29 / 29 | 100.0% |
| ST 官方源 ≥1（chapter_guides） | 29 / 29 | 100.0% |
| GitHub/社区 OSS ≥1（guides） | 29 / 29 | 100.0% |
| 无图区间 ≤ Overlay 软预算 | 4 未超；**例外库存 25 章** | — |

**本轮明确不勾选 / 仍开放：**

- 视频轨（29 短 + 29 长可再生、字幕/分镜哈希）— 超出 B2–B6，B7 不宣称。
- strip / handraw 按 §9 完成并旧支归档 — 未关闭。
- PC13 真证照片 — 仍为 user-owned（ch03 门已登记）。
- `task_verify` 分列报告 — 不可用。
- **ch08**：~~Overlay 缺口 1~~ → **已关闭**（`sample-08-bus-compare.svg`，见 `b7-gap-close.md`）。
- **ch24 / ch25**：~~缺非 ST OSS~~ → **已关闭**（`project-examples`；ch25 另加 `stlink-tools`）。
- ST Rev：**部分钉死**（rm0008/ds5319/pm0056/rm0444 + 兄弟卡；见 §5.2）；15 份 AN/ES/RM/UM 仍无仓库 Rev 证据 → §15.3-27 不勾。附录 F EN 已补 ook/en/F-oss-map.md。
- `audit_book`：`target_visual_anchors` **已切到 Overlay 4/6/9**（B7 gap-close cutover）；`overlay_*` 为同值别名。

## 1. 方法论

| 项 | 口径 |
| --- | --- |
| PDF 视觉锚点 | `extract_visual_anchors`：图/嵌 GIF；剥离章首 VIDEO；照片可合并 |
| Book 2.0 下限 | 短 3 / 中 4 / 长 6 |
| Overlay §15.2 | 短 4 / 中 6 / 长 9 |
| 无图预算 | 以 §6.3 中章上沿 1,200 为参照：短×90%→1000；中×85%→1000；长×80%→900；ch18/23/28≤3500 |
| 动画 | audit `animations` ≥1；首帧 PDF 可读（既有 FA-002 合同） |
| 三类插图 | 文件名启发式；未齐时若 B1–B6 门表已主张则标 `Y(门表)`，并列入启发式待核 |
| 出处 | `manifest.chapter_guides` ∩ `sources` |
| 附录 F | 不在 00–28 分母；单独节 |

## 2. 锚点与无图区间（29 章）

| 章 | 档 | 字符 | 旧 | Ov | 锚点 | Ov缺 | 最大无图 | 预算 | 例外 | 隙起 → 隙止 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 00 | 中 | 7746 | 4 | 6 | 7 |  | 1255 | 1000 | 是 | 地址抄对，型号也要对 → 4. 硬件采购清单 |
| 01 | 长 | 10810 | 6 | 9 | 9 |  | 1867 | 900 | 是 | 关键插图 → 4. 一个标准工程目录结构 |
| 02 | 中 | 8321 | 4 | 6 | 7 |  | 2465 | 1000 | 是 | 关键插图 → 5. 启动模式 BOOT0 / BOOT1 |
| 03 | 中 | 7390 | 4 | 6 | 7 |  | 2452 | 1000 | 是 | 关键插图 → 代码实现 |
| 04 | 中 | 7590 | 4 | 6 | 6 |  | 1970 | 1000 | 是 | 4. EXTI 外部中断 → 章末 |
| 05 | 中 | 6539 | 4 | 6 | 6 |  | 1855 | 1000 | 是 | 关键插图 → 4. PWM 模式与公式 |
| 06 | 中 | 7779 | 4 | 6 | 6 |  | 1464 | 1000 | 是 | 关键插图 → 2. 波特率与误差 |
| 07 | 短 | 3074 | 3 | 4 | 5 |  | 1744 | 1000 | 是 | 2. 时序与协议 → 相关资源 |
| 08 | 中 | 6099 | 4 | 6 | 6 |  | 1605 | 1000 | 是 | 关键插图 → 3. 速率与分频 |
| 09 | 中 | 9219 | 4 | 6 | 6 |  | 1979 | 1000 | 是 | 关键插图 → 3. 四种转换模式 |
| 10 | 中 | 7968 | 4 | 6 | 6 |  | 2096 | 1000 | 是 | 关键插图 → 3. 传输方向与工作模式 |
| 11 | 中 | 7775 | 4 | 6 | 6 |  | 2417 | 1000 | 是 | 关键插图 → 4. IWDG 与 WWDG 对比 |
| 12 | 中 | 7906 | 4 | 6 | 6 |  | 1716 | 1000 | 是 | 4. 跳转到 APP 的关键动作 → 章末 |
| 13 | 短 | 5988 | 3 | 4 | 4 |  | 1584 | 1000 | 是 | 关键插图 → 硬件与接线 |
| 14 | 中 | 9063 | 4 | 6 | 7 |  | 3059 | 1000 | 是 | 关键插图 → 5. 枚举 7 步 |
| 15 | 中 | 6550 | 4 | 6 | 7 |  | 1155 | 1000 | 是 | 关键插图 → 6. 任务间通信（IPC）对比 |
| 16 | 中 | 7826 | 4 | 6 | 6 |  | 1655 | 1000 | 是 | 核心原理 → 7. 低功耗设计检查清单 |
| 17 | 中 | 7817 | 4 | 6 | 6 |  | 1449 | 1000 | 是 | 关键插图 → 2. SWO / ITM / printf  |
| 18 | 短 | 5461 | 3 | 4 | 4 |  | 2219 | 3500 |  | 二、下载与调试 → 章末 |
| 19 | 中 | 8787 | 4 | 6 | 8 |  | 1875 | 1000 | 是 | 关键插图 → 4. USB 数据采集卡（★★★ 进阶） |
| 20 | 中 | 6309 | 4 | 6 | 7 |  | 1437 | 1000 | 是 | 4. 开源固件库对比 → 代码实现 |
| 21 | 中 | 6567 | 4 | 6 | 10 |  | 2031 | 1000 | 是 | 7. 常用外设接线总览（peripheral → 章末 |
| 22 | 短 | 3325 | 3 | 4 | 5 |  | 833 | 1000 |  | 先选哪一家 → Renode：两条脚本 |
| 23 | 短 | 5470 | 3 | 4 | 5 |  | 2470 | 3500 |  | BOOT0 与 SWCLK 共脚：先判定启动 → 从 F1 抄代码时最容易摔的几处 |
| 24 | 中 | 9341 | 4 | 6 | 6 |  | 2055 | 1000 | 是 | 1. 测量边界：JP6 只切 MCU 的 I → 章末 |
| 25 | 中 | 9058 | 4 | 6 | 8 |  | 1354 | 1000 | 是 | 从 F4 迁过来 → 章末 |
| 26 | 中 | 8509 | 4 | 6 | 6 |  | 2438 | 1000 | 是 | 7. DMA 模型：SPL 不会自动把两个驱 → 章末 |
| 27 | 中 | 9883 | 4 | 6 | 6 |  | 2585 | 1000 | 是 | 分层排错与 Wireshark 证据 → 章末 |
| 28 | 长 | 13046 | 6 | 9 | 10 |  | 2198 | 3500 |  | 一份可复算的系统资源账 → 章末 |

Overlay 锚点未达：无（ch08 已在 gap-close 补齐）。

### 2.1 最大无图区间例外库存（§15.1-25 正式库存）

下列章 gap > Overlay 软预算（或硬顶）。B2–B6 已按「表/代码密集走廊」登记例外；B7 汇总为**正式例外库存**。补偿：各章仍满足 Overlay 锚点下限（见上表 Ov / 锚点列；ch08 已在 gap-close 补至 6）。**§15.1-25 已勾**（Spec close-out）：锚点下限已切 Overlay 且本库存完整引用。

| 章 | gap | 预算 | 备注 |
| --- | ---: | ---: | --- |
| 00 | 1255 | 1000 | 软预算；见表/代码密集段（批次门已有例外先例） |
| 01 | 1867 | 900 | 软预算；见表/代码密集段（批次门已有例外先例） |
| 02 | 2465 | 1000 | 软预算；见表/代码密集段（批次门已有例外先例） |
| 03 | 2452 | 1000 | 软预算；见表/代码密集段（批次门已有例外先例） |
| 04 | 1970 | 1000 | 软预算；见表/代码密集段（批次门已有例外先例） |
| 05 | 1855 | 1000 | 软预算；见表/代码密集段（批次门已有例外先例） |
| 06 | 1464 | 1000 | 软预算；见表/代码密集段（批次门已有例外先例） |
| 07 | 1744 | 1000 | 软预算；见表/代码密集段（批次门已有例外先例） |
| 08 | 1605 | 1000 | 软预算；见表/代码密集段（批次门已有例外先例） |
| 09 | 1979 | 1000 | 软预算；见表/代码密集段（批次门已有例外先例） |
| 10 | 2096 | 1000 | 软预算；见表/代码密集段（批次门已有例外先例） |
| 11 | 2417 | 1000 | 软预算；见表/代码密集段（批次门已有例外先例） |
| 12 | 1716 | 1000 | 软预算；见表/代码密集段（批次门已有例外先例） |
| 13 | 1584 | 1000 | 软预算；见表/代码密集段（批次门已有例外先例） |
| 14 | 3059 | 1000 | 软预算；见表/代码密集段（批次门已有例外先例） |
| 15 | 1155 | 1000 | 软预算；见表/代码密集段（批次门已有例外先例） |
| 16 | 1655 | 1000 | 软预算；见表/代码密集段（批次门已有例外先例） |
| 17 | 1449 | 1000 | 软预算；见表/代码密集段（批次门已有例外先例） |
| 19 | 1875 | 1000 | 软预算；见表/代码密集段（批次门已有例外先例） |
| 20 | 1437 | 1000 | 软预算；见表/代码密集段（批次门已有例外先例） |
| 21 | 2031 | 1000 | 软预算；见表/代码密集段（批次门已有例外先例） |
| 24 | 2055 | 1000 | 软预算；见表/代码密集段（批次门已有例外先例） |
| 25 | 1354 | 1000 | 软预算；见表/代码密集段（批次门已有例外先例） |
| 26 | 2438 | 1000 | 软预算；见表/代码密集段（批次门已有例外先例） |
| 27 | 2585 | 1000 | 软预算；见表/代码密集段（批次门已有例外先例） |

## 3. 插图类型覆盖

| 章 | 概念 | 技术 | 排错/对比 | 真证 | 三类 | 资产（节选） |
| --- | --- | --- | --- | --- | --- | --- |
| 00 | Y | Y | Y |  | Y | toolchain-flow.svg, sample-00-boot-state.svg, sample-00-boot-triage.svg, sample-00-accept-gate.svg, sample-00-learn-loop.svg… |
| 01 | Y | Y | Y |  | Y | boot-sequence.svg, sample-01-swd-vectors.svg, swd-fetch.gif, single-build-contract.svg, sample-01-flash-path.svg… |
| 02 | Y | Y | Y |  | Y | clock-tree.svg, sample-02-clock-tree.svg, clock-css.gif, memory-map.svg, sample-02-boot-mode.svg… |
| 03 | Y | Y | Y | Y | Y | gpio-blink.svg, ch03-handdraw.svg, sample-03-gpio-led.svg, bluepill-stm32f103c8t6.jpg, stack-gpio-pc13-led.png… |
| 04 | Y | Y | Y |  | Y | nvic-interrupt-flow.svg, sample-04-exception-stack.svg, nvic-preempt.gif, interrupt-priority.svg, gpio-input-interrupt.svg… |
| 05 | Y | Y | Y |  | Y | timer-pwm.svg, sample-05-pwm-1khz.svg, pwm-1khz.gif, timer-modes.svg, sample-05-pwm-debug.svg… |
| 06 | Y | Y | Y |  | Y | uart-frame.svg, sample-06-uart-frame.svg, uart-idle.gif, uart-bits.gif, sample-06-baud-triage.svg… |
| 07 | Y | Y | Y |  | Y | i2c-transaction.svg, sample-07-i2c-addr.svg, i2c-addr.gif, i2c-timing.gif, sample-07-i2c-triage.svg |
| 08 | Y | Y | Y |  | Y | spi-transfer.svg, sample-08-spi-jedec.svg, spi-jedec.gif, sample-08-cpha-modes.svg, sample-08-spi-triage.svg |
| 09 | Y | Y | Y |  | Y | adc-sar.svg, sample-09-adc-sar.svg, adc-sample.gif, sar-adc.gif, dma-circular.svg… |
| 10 | Y | Y | Y |  | Y | dma-circular.svg, sample-10-dma-cndtr.svg, dma-cndtr.gif, sample-10-dma-triage.svg, dma-buffer-ownership.svg… |
| 11 |  | Y | Y |  | Y(门表) | iwdg-window.svg, sample-11-iwdg-1s.svg, iwdg-1s.gif, sample-11-wdg-compare.svg, watchdog-reset-evidence.svg… |
| 12 | Y | Y | Y |  | Y | flash-iap.svg, sample-12-iap-map.svg, iap-jump.gif, sample-12-flash-triage.svg, iap-acceptance-gates.svg… |
| 13 |  | Y | Y |  | Y(门表) | can-arbitration.svg, sample-13-can-bit.svg, can-500k.gif, sample-13-can-triage.svg |
| 14 | Y | Y | Y |  | Y | usb-enumeration.svg, sample-14-usb-enum.svg, usb-48m.gif, usb-enumeration-zh.gif, sample-14-descriptor-map.svg… |
| 15 | Y | Y | Y |  | Y | freertos-scheduler.svg, sample-15-rtos-prio.svg, rtos-tick.gif, rtos-deadline-budget.svg, rtos-owner-task.svg… |
| 16 | Y | Y | Y |  | Y | lowpower-wakeup.svg, sample-16-stop-wake.svg, stop-wake.gif, sample-16-stop-compare.svg, lowpower-current-evidence.svg… |
| 17 |  | Y | Y |  | Y(门表) | debug-swo.svg, sample-17-cfsr.svg, cfsr-read.gif, sample-17-obs-compare.svg, fault-triage-ladder.svg… |
| 18 | Y | Y | Y |  | Y | toolchain-flow.svg, sample-18-boot-triage.svg, boot0-low.gif, sample-18-faq-compare.svg |
| 19 | Y | Y | Y |  | Y | peripheral-wiring.svg, sample-19-flash-fit.svg, one-slot.gif, dma-buffer-ownership.svg, iap-acceptance-gates.svg… |
| 20 | Y | Y | Y |  | Y | project-structure.svg, sample-20-lookup-flow.svg, manual-choice-map.svg, firmware-stack-choice.svg, instrument-evidence-ladder.svg… |
| 21 | Y | Y | Y |  | Y | bluepill-stm32f103c8t6.svg, sample-21-board-compare.svg, bluepill-stm32f103c8t6.svg, blackpill-stm32f411ce.svg, nucleo-f411re.svg… |
| 22 | Y | Y | Y |  | Y | toolchain-flow.svg, simulator-comparison.svg, simulation-model-boundary.svg, sample-22-sim-triage.svg, simulation-acceptance-gates.svg |
| 23 | Y | Y | Y |  | Y | pinout-stm32g071rb-lqfp64.svg, pinout-bluepill.svg, sample-23-boot-latch.svg, g0-boot-swd.svg, sample-23-f1-g0-compare.svg |
| 24 |  | Y | Y | Y | Y(门表) | pinout-stm32l476rg-lqfp64.svg, nucleo-f411re-embedded-world.jpg, nucleo-f401re-embedded-world.jpg, sample-24-mode-compare.svg, l4-stop2-evidence.svg… |
| 25 | Y | Y | Y |  | Y | pinout-stm32h743zi-lqfp144.svg, h7-power-domains.svg, h7-revision-clock-decision.svg, h7-clock-chain.svg, h7-startup-evidence.svg… |
| 26 | Y | Y | Y |  | Y | spl-ownership-boundary.svg, spl-init-pipeline.svg, bluepill-stm32f103c8t6.svg, sample-26-spl-hal-compare.svg, nvic-interrupt-flow.svg… |
| 27 | Y | Y | Y |  | Y | network-packet-journey.svg, network-cache-ownership.svg, network-online-state.svg, tcp-byte-stream.svg, sample-27-link-triage.svg… |
| 28 | Y | Y | Y | Y | Y | rtos-system-layers.svg, sample-28-os-compare.svg, nucleo-f411re-embedded-world.jpg, nucleo-f401re-embedded-world.jpg, sample-28-owner-flow.svg… |

启发式未独立识别三类的章（门表仍主张覆盖，待人工抽检门表图注）：**11, 13, 17, 24**。
装饰图 / 气氛图：本轮未另跑装饰扫描；B1–B6 生成器合同禁止计入装饰图，普查不宣称「装饰=0 已机器证明」。

## 4. 动画覆盖

| 章 | animations | ≥1 |
| --- | ---: | --- |
| 00 | 1 | Y |
| 01 | 2 | Y |
| 02 | 3 | Y |
| 03 | 2 | Y |
| 04 | 3 | Y |
| 05 | 4 | Y |
| 06 | 3 | Y |
| 07 | 3 | Y |
| 08 | 2 | Y |
| 09 | 4 | Y |
| 10 | 3 | Y |
| 11 | 2 | Y |
| 12 | 2 | Y |
| 13 | 2 | Y |
| 14 | 3 | Y |
| 15 | 3 | Y |
| 16 | 2 | Y |
| 17 | 2 | Y |
| 18 | 2 | Y |
| 19 | 2 | Y |
| 20 | 1 | Y |
| 21 | 1 | Y |
| 22 | 2 | Y |
| 23 | 2 | Y |
| 24 | 1 | Y |
| 25 | 1 | Y |
| 26 | 3 | Y |
| 27 | 2 | Y |
| 28 | 4 | Y |

`assets/animations/` 现 35 文件均被正文引用；B2 观察项 `can-500k.gif` 已由 ch13 引用，孤儿关闭。

## 5. 出处覆盖（ST + OSS）

| 章 | ST（节选） | OSS | snapshot 含具体 Rev? | §15.3-28 |
| --- | --- | --- | --- | --- |
| 00 | rm0008, ds5319, rm0008-boot | project-guide, project-examples | rm0008-boot | Y |
| 01 | pm0056, stm32cube-f4, clion-embedded, platformio-vscode… | project-guide | ds5319-swd, pm0075-rdp, pm0056-vector, rm0008-boot | Y |
| 02 | rm0008, ds5319, rm0008-rcc, ds5319-clock | spl-f1-mirror | rm0008-rcc, ds5319-clock | Y |
| 03 | rm0008, ds5319, rm0008-gpio, ds5319-gpio | project-examples | rm0008-gpio, ds5319-gpio | Y |
| 04 | pm0056, rm0008, freertos-priority, rm0008-exti… | freertos-priority, project-examples | rm0008-exti, pm0056-nvic | Y |
| 05 | rm0008, rm0008-tim, ds5319-tim | project-examples | rm0008-tim, ds5319-tim | Y |
| 06 | rm0008, stm32cube-f4, st-uart-idle, rm0008-usart… | majerle-uart | rm0008-usart, ds5319-usart | Y |
| 07 | rm0008, ds5319-i2c, rm0008-i2c | project-examples | ds5319-i2c, rm0008-i2c | Y |
| 08 | rm0008, rm0008-spi, ds5319-spi | project-examples | rm0008-spi, ds5319-spi | Y |
| 09 | rm0008, ds5319, rm0008-adc, ds5319-adc | project-examples | rm0008-adc, ds5319-adc | Y |
| 10 | rm0008, stm32cube-f4, st-h7-dma, rm0090… | majerle-uart | rm0008-dma, ds5319-dma | Y |
| 11 | rm0008, ds5319, rm0008-wdg, rm0008-rtc… | project-examples | rm0008-wdg, rm0008-rtc, ds5319-rtc, pm0075-rdp | Y |
| 12 | rm0008, an2606, an3965, rm0090… | project-examples | rm0008-flash, pm0056-vector, ds5319-swd, pm0075-rdp | Y |
| 13 | rm0008, rm0008-can, ds5319-usbcan, rm0008-usb… | project-examples | rm0008-can, ds5319-usbcan, rm0008-usb, ds5319-clock, ds5319-i2c | Y |
| 14 | rm0008, rm0008-rcc, ds5319-usbcan, rm0008-usb | project-examples | rm0008-rcc, ds5319-usbcan, rm0008-usb | Y |
| 15 | freertos-priority, pm0056 | freertos-priority, project-examples, freertos-syscall | 多为「核对当前修订」 | Y |
| 16 | rm0008, ds5319, ds5319-pwr, rm0008-pwr… | project-examples | ds5319-pwr, rm0008-pwr, rm0008-rcc, rm0008-usart, ds5319-adc, rm0008-rtc, rm0008-wdg | Y |
| 17 | pm0056, pm0056-dwt, ds5319-swd | stlink-tools | ds5319-swd | Y |
| 18 | pm0056, pm0056-dwt, ds5319-swd, rm0008-boot… | project-examples, project-guide, freertos-syscall | ds5319-swd, rm0008-boot, ds5319-nrst, ds5319-lse, rm0008-usart, ds5319-gpio | Y |
| 19 | ds5319-swd, rm0008-adc, ds5319-adc | project-examples | ds5319-swd, rm0008-adc, ds5319-adc | Y |
| 20 | stm32cube-f4, clion-embedded, platformio-vscode | project-credits, stlink-tools, project-examples | 多为「核对当前修订」 | Y |
| 21 | ds5319 | project-credits, project-examples | 多为「核对当前修订」 | Y |
| 22 | ds5319, wokwi-bluepill, renode-stm32 | wokwi-bluepill, renode-stm32 | 多为「核对当前修订」 | Y |
| 23 | ds12232, rm0444, an5096, an2606… | project-examples | ds12232 | Y |
| 24 | ds10198, rm0351, an4746, um1724… | project-examples | ds10198 | Y |
| 25 | ds12110, rm0433, es0392, an4938… | project-examples, stlink-tools | ds12110 | Y |
| 26 | stsw-stm32054, rm0008 | spl-f1-mirror | 多为「核对当前修订」 | Y |
| 27 | rm0433, um2407, um1713, an4839… | lwip-pitfalls, mqtt-v5, mbedtls-networking | 多为「核对当前修订」 | Y |
| 28 | freertos-1132, rtthread-530, zephyr-442, cmsis-640… | freertos-1132, rtthread-530, zephyr-442, cmsis-640 | 多为「核对当前修订」 | Y |

### 5.1 OSS 缺口

- **ch24 / ch25**：~~guides 无非 ST GitHub OSS~~ → **已关闭**（见 `b7-gap-close.md`）：`project-examples`（MIT，`examples/`）；ch25 另加 `stlink-tools`（BSD-3-Clause，`stlink` v1.9.0 man）。可复用/仅对照边界已写入 guides 与相关资源。

### 5.2 Revision（Spec close-out）

已按正文 / CREDITS / 兄弟卡证据钉死：

| 卡 | Rev | 证据 |
| --- | --- | --- |
| `rm0008` + `rm0008-*` | Rev 21, February 2021 | 各章正文；ch03 门；兄弟卡 snapshot |
| `ds5319` + `ds5319-*` | Rev 20, July 2025 | 各章正文；ch03 门；兄弟卡 snapshot |
| `pm0056` + `pm0056-nvic` / `vector` / `dwt` | Rev 7, December 2024 | CREDITS；`pm0056-nvic` 卡 |
| `rm0444` | Rev 5 | docs/23、en/23 |
| `ds12232` / `ds10198` / `ds12110` / `pm0075` | 已钉（既有） | 章正文 + manifest |

**仓库无 Rev 证据、本轮不发明**：`an2606` `an3965` `an4746` `an4839` `an4938` `an5096` `es0250` `es0392` `rm0090` `rm0351` `rm0399` `rm0433` `um1713` `um1724` `um2407`。ch27 guides 的 ST 卡全部落在未钉集合 → **§15.3-27 仍不勾**。

### 5.3 冲突裁定库存（§15.3-29）

只登记正文/附录/门表里**已经出现**的官方↔OSS（或官方↔丝印/社区）分歧与裁定；不新造冲突。

| 位置 | 分歧 | 裁定语 |
| --- | --- | --- |
| 附录 F（zh `F-开源地图.md` / en `F-oss-map.md`） | 官方 RM/DS vs 开源实现 | 「官方 RM/DS 冲突时以手册为准」/ EN equivalent |
| `audits/ch03-converge-gate.md` §15.4 | RM0008/DS5319 vs `examples/` MIT | 冲突列：与开源冲突时以 RM0008/DS5319 为准；OSS 仅对照 |
| ch20 坑表 | 中文教程代码 vs 官方 HAL/RM | 「以官方 HAL 与 RM 为准」 |
| ch21 / 附录 C | 丝印 vs 数据手册 | 以确切料号官方 DS + 可追溯原理图为准 |
| ch23/24/25 图注与相关资源 | Cube / `examples/` vs RM/DS | 「例程/Cube 仅对照」；不替代目标手册条件 |
| ch25 + `stlink-tools` 卡 | 探针工具行为 vs DS12110/ES0392 | does not override DS/ES（gap-close §2） |
| 附录 F §3 libopencm3 | memorymap 翻译 vs RM | EN 明确：寄存器值与适用 RM/DS 冲突时以手册为准 |

**§15.3-29 已勾**（Spec close-out）。未对无分歧章节批量插入裁定句。

## 6. 附录 F

| 项 | 值 |
| --- | --- |
| 路径 | `stm32-book/book/F-开源地图.md` |
| 去空白字符约 | 5448 |
| 插图 | sample-f-oss-map.svg |
| 英文对照 | **缺** `book-en/F-*.md` |
| 动画 | 无；`sample-f-oss-map.svg` 静态概念图 |
| 分母 | **不计入** 29 章 Overlay 分母 |

## 7. §11.3 / §15 勾选建议（仅证据）

| 条目 | 本轮 | 证据 |
| --- | --- | --- |
| §15.4-31 B7 普查 | **勾选** | 本文件 |
| §11.3 B7 普查报告 | **勾选** | 本文件 |
| §15.1-23 三类每章 | 勾 | 29/29（11/13/17/24 以 B4/B6 门表为准；启发式仍弱；装饰扫描未机证） |
| §15.1-24 动画≥1 | 勾 | 计数 29/29；首帧 PDF 合同既有；未另做播放质检级验收 |
| §15.1-25 Overlay 锚点 | **勾** | 锚点下限 29/29 + Overlay 主字段；例外库存见 §2.1（Spec close-out） |
| §15.1-26 双轨 | 不新勾 | PC13 真证仍缺 |
| §15.3-27 官方+Rev | 不勾 | 已钉 rm0008/ds5319/pm0056/rm0444 等；15 份 AN/ES/RM/UM 仍无证据（§5.2） |
| §15.3-28 每章 OSS | 勾 | —（b7-gap-close） |
| §15.3-29 冲突裁定 | **勾** | 已知分歧裁定库存见 §5.3；未新造冲突 |
| §11.3 视频 29+29 | 不勾 | 未做 |
| §11.3 strip/handraw | 不勾 | 未做 |
| §11.3 task_verify | 不勾 | 不可用 |
| §11.3 基线测试全绿 | **已勾** | pytest 180；check_assets；slop_lint；audit_book；build_html zh+en PASS（Spec close-out verify reconfirmed） |

## 8. 工具变更

- `tools/audit_book.py`：保留 Book 2.0 `_target_visuals` / `visual_anchor_deficit`；新增 JSON 对照字段 `overlay_target_visual_anchors`、`overlay_visual_anchor_deficit`、`overlay_gap_budget_chars`（§15.2）。
- **延期**：把主 `target_visual_anchors` 切到 Overlay（阻塞：ch08 Overlay 缺口；且表是否计入锚点未定）。

## 9. 开放缺口清单

> **2026-11-05 现状注记**：本清单基于 B6 基线 `8794d00`。其后 Batch A–G 已完成视频重制（见 `video-regen-plan.md`）、知识轨全书覆盖（见 `handraw-knowledge-track-29.md`）与锚点锁定值 re-baseline；本节所列缺口以 Overlay 现状为准逐条复核，未再出现的视为已闭合。

1. ~~ch08 Overlay 锚点缺口 1~~ → **已关闭**（见 §9.1 / b7-gap-close）。
2. ~~ch24、ch25 缺 GitHub OSS source 卡~~ → **已关闭**（`project-examples` / `stlink-tools`）。
3. ST revision 未全书钉死。
4. ~~无图区间例外库存（§2.1）未逐条关闭~~ → **已正式化为 §15.1-25 库存**（不逐条塞图；理由+补偿锚点见上表）。
5. 启发式三类待核：11, 13, 17, 24 → **门表已覆盖，不补装饰图**（见 §9.1）。
6. PC13 实拍仍 user-owned。
7. 视频轨未关闭。
8. strip/handraw §9 归档未关闭。
9. `task_verify` 不可用。
10. 附录 F 无英文对照。
11. audit 锚点不含「表」——与 §15.2 全文定义不一致。



## 9.1 Gap-close amendment (post-`99b1f03`)

See `audits/b7-gap-close.md` for before/after evidence.

- **ch08**: Overlay deficit closed (`sample-08-bus-compare.svg`); anchors 6/6 mid-band.
- **ch24/ch25**: non-ST OSS cards added (`project-examples`; ch25 also `stlink-tools`); reuse boundaries in guides + related resources.
- **Types 11/13/17/24**: no new figures; B4/B6 gate tables remain the coverage authority; heuristic stays weak by filename only.
- **`audit_book`**: `target_visual_anchors` cut over to Overlay 4/6/9; overlay_* aliased.
- **Still open**: photos (PC13), video 29, strip/handraw archive, task_verify, remaining ST Rev pins (§5.2), table-as-anchor definition. Closed this Spec close-out: gap inventory (§2.1→§15.1-25), conflict inventory (§5.3→§15.3-29), F-EN parity, evidenced Rev pins.

## 10. 验证

```text
pytest
python tools/check_assets.py
python tools/slop_lint.py
python tools/audit_book.py
python build_html.py --check --lang zh   # cwd=stm32-book
python build_html.py --check --lang en
```


# 全书来源、知识候选与批次对账

本清单覆盖manifest全部94章和7附录，来源文件无重复无遗漏。814项只是机制相关标题种子，须按批逐段拆分/补充无标题知识点，不是完成数。

## 检查深度

- 主代理有代表正文窗口并形成方案：8文件（含一个实验和一个生成附录）。
- 子代理history有源码read记录但没有可用综合报告：23文件。保留read范围，不承认审阅结论。
- 仅源结构/章罗盘机械建账：70文件。所有知识点状态仍需语义审查，不假称全书讲透。
- 所有文件的具体候选标题、行号、既有先修、正文问题/交付/边界和图引用在knowledge-ledger.json；SHA在source-inventory/planning-baseline。

## 文件清单

| 文件 | 候选标题数 | 已读证据层级 | 批次 |
|---|---:|---|---|
| docs/c/00-c-in-mcu.md | 5 | 仅子代理read记录 | B01 |
| docs/c/01-memory-model.md | 9 | 仅子代理read记录 | B01 |
| docs/c/02-pointer.md | 5 | 主代理选定窗口 | PILOT |
| docs/c/03-volatile.md | 12 | 仅子代理read记录 | B01 |
| docs/c/04-struct-abi.md | 10 | 仅子代理read记录 | B01 |
| docs/c/05-func-pointer.md | 6 | 机械建账 | B01 |
| docs/c/06-abi-stack.md | 7 | 机械建账 | B01 |
| docs/c/07-ub-misra.md | 6 | 机械建账 | B02 |
| docs/c/08-framed-protocol.md | 13 | 机械建账 | B02 |
| docs/build/00-toolchain.md | 5 | 机械建账 | B03 |
| docs/build/01-four-steps.md | 7 | 机械建账 | B03 |
| docs/build/02-elf.md | 7 | 机械建账 | B03 |
| docs/build/03-linker-script.md | 15 | 机械建账 | B03 |
| docs/build/04-startup.md | 7 | 机械建账 | B03 |
| docs/build/05-map-size.md | 5 | 机械建账 | B03 |
| docs/build/06-flash-debug.md | 5 | 机械建账 | B04 |
| docs/build/07-build-system.md | 6 | 主代理选定窗口 | PILOT |
| docs/stm32/00-env.md | 9 | 机械建账 | B05 |
| docs/stm32/01-arch.md | 6 | 机械建账 | B05 |
| docs/stm32/02-rcc-clock.md | 11 | 机械建账 | B05 |
| docs/stm32/03-gpio.md | 7 | 机械建账 | B05 |
| docs/stm32/04-nvic-exti.md | 15 | 机械建账 | B05 |
| docs/stm32/05-systick.md | 7 | 机械建账 | B05 |
| docs/stm32/06-tim.md | 16 | 机械建账 | B06 |
| docs/stm32/07-usart.md | 10 | 机械建账 | B06 |
| docs/stm32/08-dma.md | 11 | 机械建账 | B06 |
| docs/stm32/09-adc.md | 7 | 机械建账 | B06 |
| docs/stm32/10-dac.md | 9 | 机械建账 | B06 |
| docs/stm32/11-i2c.md | 11 | 主代理选定窗口 | PILOT |
| docs/stm32/12-spi.md | 8 | 机械建账 | B06 |
| docs/stm32/13-flash-iap.md | 9 | 机械建账 | B07 |
| docs/stm32/14-pwr.md | 12 | 机械建账 | B07 |
| docs/stm32/15-spl-anatomy.md | 8 | 机械建账 | B07 |
| docs/stm32/16-debug-hardfault.md | 9 | 机械建账 | B07 |
| docs/stm32/17-watchdog-reset.md | 10 | 机械建账 | B07 |
| docs/rtos/freertos/00-why-rtos.md | 5 | 仅子代理read记录 | B08 |
| docs/rtos/freertos/01-task-tcb.md | 10 | 仅子代理read记录 | B08 |
| docs/rtos/freertos/02-context-switch.md | 7 | 仅子代理read记录 | B08 |
| docs/rtos/freertos/03-scheduler.md | 6 | 主代理选定窗口 | PILOT |
| docs/rtos/freertos/04-queue.md | 6 | 机械建账 | B08 |
| docs/rtos/freertos/05-sem-mutex.md | 5 | 机械建账 | B08 |
| docs/rtos/freertos/06-notify-event-timer.md | 13 | 机械建账 | B08 |
| docs/rtos/freertos/07-heap.md | 13 | 机械建账 | B09 |
| docs/rtos/freertos/08-port-f407.md | 8 | 机械建账 | B09 |
| docs/rtos/rtthread/00-arch.md | 5 | 机械建账 | B10 |
| docs/rtos/rtthread/01-thread-sched.md | 6 | 机械建账 | B10 |
| docs/rtos/rtthread/02-ipc.md | 8 | 机械建账 | B10 |
| docs/rtos/rtthread/03-mem.md | 5 | 机械建账 | B10 |
| docs/rtos/rtthread/04-device.md | 6 | 机械建账 | B10 |
| docs/rtos/rtthread/05-finsh.md | 5 | 机械建账 | B10 |
| docs/rtos/rtthread/06-env-menuconfig.md | 6 | 机械建账 | B11 |
| docs/rtos/rtthread/07-port-f407.md | 6 | 机械建账 | B11 |
| docs/rtos/compare/00-side-by-side.md | 5 | 机械建账 | B12 |
| docs/rtos/compare/01-choose.md | 7 | 机械建账 | B12 |
| docs/esp32/00-env.md | 6 | 机械建账 | B13 |
| docs/esp32/01-arch-boot.md | 7 | 机械建账 | B13 |
| docs/esp32/02-gpio-matrix.md | 8 | 主代理选定窗口 | PILOT |
| docs/esp32/03-idf-anatomy.md | 7 | 机械建账 | B13 |
| docs/esp32/04-irq-dualcore.md | 7 | 机械建账 | B13 |
| docs/esp32/05-uart-driver.md | 8 | 机械建账 | B13 |
| docs/esp32/06-spi-i2c-driver.md | 8 | 机械建账 | B13 |
| docs/esp32/07-timer-ledc.md | 8 | 机械建账 | B14 |
| docs/esp32/08-wifi.md | 6 | 机械建账 | B14 |
| docs/esp32/09-bt-espnow.md | 6 | 机械建账 | B14 |
| docs/esp32/10-flash-nvs-ota.md | 7 | 机械建账 | B14 |
| docs/esp32/11-lowpower.md | 6 | 机械建账 | B14 |
| docs/esp32/12-audio-path.md | 8 | 机械建账 | B14 |
| docs/esp32/13-watchdog-health.md | 10 | 机械建账 | B15 |
| docs/gd32/00-env.md | 4 | 机械建账 | B16 |
| docs/gd32/01-rcu-clock.md | 9 | 机械建账 | B16 |
| docs/gd32/02-gpio-af.md | 9 | 机械建账 | B16 |
| docs/gd32/03-usart.md | 5 | 机械建账 | B16 |
| docs/gd32/04-periph-diff.md | 7 | 机械建账 | B16 |
| docs/gd32/05-riscv-toolchain.md | 6 | 机械建账 | B16 |
| docs/gd32/06-clic-irq.md | 7 | 机械建账 | B17 |
| docs/gd32/07-rcu-108m.md | 6 | 机械建账 | B17 |
| docs/gd32/08-mtime-delay.md | 5 | 机械建账 | B17 |
| docs/gd32/09-gpio-minimal.md | 6 | 机械建账 | B17 |
| docs/lab/e01-blink.md | 10 | 仅子代理read记录 | B18 |
| docs/lab/e02-logic-uart.md | 10 | 仅子代理read记录 | B18 |
| docs/lab/e03-scope-pwm.md | 10 | 仅子代理read记录 | B18 |
| docs/lab/e04-priority-inversion.md | 12 | 主代理选定窗口 | B18 |
| docs/lab/e05-i2c-eeprom.md | 11 | 仅子代理read记录 | B18 |
| docs/lab/e06-lowpower-current.md | 11 | 仅子代理read记录 | B18 |
| docs/lab/e07-qmi8658.md | 11 | 仅子代理read记录 | B19 |
| docs/lab/e08-audio-play.md | 11 | 仅子代理read记录 | B19 |
| docs/projects/01-f407-logger.md | 9 | 仅子代理read记录 | B20 |
| docs/projects/02-s3-logger.md | 9 | 仅子代理read记录 | B20 |
| docs/ai/00-pair-not-ghost.md | 5 | 仅子代理read记录 | B21 |
| docs/ai/01-prompt-patterns.md | 5 | 仅子代理read记录 | B21 |
| docs/ai/02-manual-reconciliation.md | 6 | 主代理选定窗口 | PILOT |
| docs/ai/03-toolflow-mcp.md | 6 | 仅子代理read记录 | B21 |
| docs/ai/04-hallucination-defense.md | 6 | 仅子代理read记录 | B21 |
| docs/ai/05-this-book-pipeline.md | 9 | 仅子代理read记录 | B21 |
| mcu-book/book/A-工程深读.md | 9 | 仅子代理read记录 | B22 |
| mcu-book/book/B-例程索引.md | 8 | 仅子代理read记录 | B22 |
| mcu-book/book/C-习题答案.md | 0 | 主代理选定窗口 | B22 |
| mcu-book/book/D-术语表.md | 8 | 机械建账 | B22 |
| mcu-book/book/E-参考资料.md | 4 | 机械建账 | B22 |
| mcu-book/book/F-常见问题.md | 29 | 机械建账 | B22 |
| mcu-book/book/G-开源地图.md | 12 | 机械建账 | B23 |

## 研究完成与内容完成分开

本轮完成的是全范围建账、已证风险、验收合同、代表方案与排程。后续每批必须阅读全文、代码/图表/答案，补齐证据卡和真实缺口，用户审后实施；不能把这里的“机械建账”一键标accepted。章节已有好解释可维持原文并记录依据，不要求每行都改。

## 原有任务与工作

11-07-language-batch5的B7四行改写和更新日志保持；其已有候选保护与页面验证不自动覆盖新图和新解释。10-26-prose-polish、10-27-book-interest-polish及旧题图任务保留职责与历史，不批量归档，也不覆盖11-02用户资产。

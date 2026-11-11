# 全量推广与附录一致性

## 目标与授权

隶属11-07-book-depth-handdraw。当前仅规划授权，不start、不实施或发布。总需求以父任务PRD为准，本任务独立验收，不能用别的子任务绿色代替。

## 范围

- docs/c/00-c-in-mcu.md
- docs/c/01-memory-model.md
- docs/c/03-volatile.md
- docs/c/04-struct-abi.md
- docs/c/05-func-pointer.md
- docs/c/06-abi-stack.md
- docs/c/07-ub-misra.md
- docs/c/08-framed-protocol.md
- docs/build/00-toolchain.md
- docs/build/01-four-steps.md
- docs/build/02-elf.md
- docs/build/03-linker-script.md
- docs/build/04-startup.md
- docs/build/05-map-size.md
- docs/build/06-flash-debug.md
- docs/stm32/00-env.md
- docs/stm32/01-arch.md
- docs/stm32/02-rcc-clock.md
- docs/stm32/03-gpio.md
- docs/stm32/04-nvic-exti.md
- docs/stm32/05-systick.md
- docs/stm32/06-tim.md
- docs/stm32/07-usart.md
- docs/stm32/08-dma.md
- docs/stm32/09-adc.md
- docs/stm32/10-dac.md
- docs/stm32/12-spi.md
- docs/stm32/13-flash-iap.md
- docs/stm32/14-pwr.md
- docs/stm32/15-spl-anatomy.md
- docs/stm32/16-debug-hardfault.md
- docs/stm32/17-watchdog-reset.md
- docs/rtos/freertos/00-why-rtos.md
- docs/rtos/freertos/01-task-tcb.md
- docs/rtos/freertos/02-context-switch.md
- docs/rtos/freertos/04-queue.md
- docs/rtos/freertos/05-sem-mutex.md
- docs/rtos/freertos/06-notify-event-timer.md
- docs/rtos/freertos/07-heap.md
- docs/rtos/freertos/08-port-f407.md
- docs/rtos/rtthread/00-arch.md
- docs/rtos/rtthread/01-thread-sched.md
- docs/rtos/rtthread/02-ipc.md
- docs/rtos/rtthread/03-mem.md
- docs/rtos/rtthread/04-device.md
- docs/rtos/rtthread/05-finsh.md
- docs/rtos/rtthread/06-env-menuconfig.md
- docs/rtos/rtthread/07-port-f407.md
- docs/rtos/compare/00-side-by-side.md
- docs/rtos/compare/01-choose.md
- docs/esp32/00-env.md
- docs/esp32/01-arch-boot.md
- docs/esp32/03-idf-anatomy.md
- docs/esp32/04-irq-dualcore.md
- docs/esp32/05-uart-driver.md
- docs/esp32/06-spi-i2c-driver.md
- docs/esp32/07-timer-ledc.md
- docs/esp32/08-wifi.md
- docs/esp32/09-bt-espnow.md
- docs/esp32/10-flash-nvs-ota.md
- docs/esp32/11-lowpower.md
- docs/esp32/12-audio-path.md
- docs/esp32/13-watchdog-health.md
- docs/gd32/00-env.md
- docs/gd32/01-rcu-clock.md
- docs/gd32/02-gpio-af.md
- docs/gd32/03-usart.md
- docs/gd32/04-periph-diff.md
- docs/gd32/05-riscv-toolchain.md
- docs/gd32/06-clic-irq.md
- docs/gd32/07-rcu-108m.md
- docs/gd32/08-mtime-delay.md
- docs/gd32/09-gpio-minimal.md
- docs/lab/e01-blink.md
- docs/lab/e02-logic-uart.md
- docs/lab/e03-scope-pwm.md
- docs/lab/e04-priority-inversion.md
- docs/lab/e05-i2c-eeprom.md
- docs/lab/e06-lowpower-current.md
- docs/lab/e07-qmi8658.md
- docs/lab/e08-audio-play.md
- docs/projects/01-f407-logger.md
- docs/projects/02-s3-logger.md
- docs/ai/00-pair-not-ghost.md
- docs/ai/01-prompt-patterns.md
- docs/ai/03-toolflow-mcp.md
- docs/ai/04-hallucination-defense.md
- docs/ai/05-this-book-pipeline.md
- mcu-book/book/A-工程深读.md
- mcu-book/book/B-例程索引.md
- mcu-book/book/C-习题答案.md
- mcu-book/book/D-术语表.md
- mcu-book/book/E-参考资料.md
- mcu-book/book/F-常见问题.md
- mcu-book/book/G-开源地图.md

## 需求

- F1 按总任务batches.json覆盖余下88章+7附录
- F2 每批至多6文件，逐章逐段补/拆知识点与先修
- F3 图有需求再复用/改/新，不堆数量
- F4 S篇18章含样章S11有完整归属，不省略
- F5 附录按各自来源/索引/答案/术语职责验，不造第二真源。

## 验收

95文件分批全部accepted，与pilot6合计manifest101文件零漏重；知识点不限814标题，所有无标题点在全文审阅时登记；每批至少两章抽评通过，图文和运行/源合同各自过；没有未登记事实改动或被伪造的实测。

## 依赖与外部前提

样章6章用户验收；每批具体范围/来源/图计划另审后才能实施。

## 保护

保留既有B7四行与用户42文件，214验证输入固定。代码/表格/标题/数字/引文/链接变更需显式证据review，不降低守卫策略。无设备不称HIL过，无operator基线保持unverified。与其他任务职责不重叠覆盖。

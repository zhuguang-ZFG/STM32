# 全书批次顺序

按既有分部规划，不改章节顺序；每文件恰属一个内容批次。PILOT先做C2/F3两个概念薄切片，随后完成六个样章各自全部知识点审查/升级；通过用户抽评后才扩到剩余批次。此处只是执行路由，不代表获批实施。

| 批次 | 来源 | 数量 | 文件 |
|---|---|---:|---|
| PILOT | 代表样章 | 6 | docs/c/02-pointer.md<br>docs/build/07-build-system.md<br>docs/stm32/11-i2c.md<br>docs/rtos/freertos/03-scheduler.md<br>docs/esp32/02-gpio-matrix.md<br>docs/ai/02-manual-reconciliation.md |
| B01 | pc | 6 | docs/c/00-c-in-mcu.md<br>docs/c/01-memory-model.md<br>docs/c/03-volatile.md<br>docs/c/04-struct-abi.md<br>docs/c/05-func-pointer.md<br>docs/c/06-abi-stack.md |
| B02 | pc | 2 | docs/c/07-ub-misra.md<br>docs/c/08-framed-protocol.md |
| B03 | pb | 6 | docs/build/00-toolchain.md<br>docs/build/01-four-steps.md<br>docs/build/02-elf.md<br>docs/build/03-linker-script.md<br>docs/build/04-startup.md<br>docs/build/05-map-size.md |
| B04 | pb | 1 | docs/build/06-flash-debug.md |
| B05 | ps | 6 | docs/stm32/00-env.md<br>docs/stm32/01-arch.md<br>docs/stm32/02-rcc-clock.md<br>docs/stm32/03-gpio.md<br>docs/stm32/04-nvic-exti.md<br>docs/stm32/05-systick.md |
| B06 | ps | 6 | docs/stm32/06-tim.md<br>docs/stm32/07-usart.md<br>docs/stm32/08-dma.md<br>docs/stm32/09-adc.md<br>docs/stm32/10-dac.md<br>docs/stm32/12-spi.md |
| B07 | ps | 5 | docs/stm32/13-flash-iap.md<br>docs/stm32/14-pwr.md<br>docs/stm32/15-spl-anatomy.md<br>docs/stm32/16-debug-hardfault.md<br>docs/stm32/17-watchdog-reset.md |
| B08 | pf | 6 | docs/rtos/freertos/00-why-rtos.md<br>docs/rtos/freertos/01-task-tcb.md<br>docs/rtos/freertos/02-context-switch.md<br>docs/rtos/freertos/04-queue.md<br>docs/rtos/freertos/05-sem-mutex.md<br>docs/rtos/freertos/06-notify-event-timer.md |
| B09 | pf | 2 | docs/rtos/freertos/07-heap.md<br>docs/rtos/freertos/08-port-f407.md |
| B10 | pr | 6 | docs/rtos/rtthread/00-arch.md<br>docs/rtos/rtthread/01-thread-sched.md<br>docs/rtos/rtthread/02-ipc.md<br>docs/rtos/rtthread/03-mem.md<br>docs/rtos/rtthread/04-device.md<br>docs/rtos/rtthread/05-finsh.md |
| B11 | pr | 2 | docs/rtos/rtthread/06-env-menuconfig.md<br>docs/rtos/rtthread/07-port-f407.md |
| B12 | px | 2 | docs/rtos/compare/00-side-by-side.md<br>docs/rtos/compare/01-choose.md |
| B13 | pe | 6 | docs/esp32/00-env.md<br>docs/esp32/01-arch-boot.md<br>docs/esp32/03-idf-anatomy.md<br>docs/esp32/04-irq-dualcore.md<br>docs/esp32/05-uart-driver.md<br>docs/esp32/06-spi-i2c-driver.md |
| B14 | pe | 6 | docs/esp32/07-timer-ledc.md<br>docs/esp32/08-wifi.md<br>docs/esp32/09-bt-espnow.md<br>docs/esp32/10-flash-nvs-ota.md<br>docs/esp32/11-lowpower.md<br>docs/esp32/12-audio-path.md |
| B15 | pe | 1 | docs/esp32/13-watchdog-health.md |
| B16 | pg | 6 | docs/gd32/00-env.md<br>docs/gd32/01-rcu-clock.md<br>docs/gd32/02-gpio-af.md<br>docs/gd32/03-usart.md<br>docs/gd32/04-periph-diff.md<br>docs/gd32/05-riscv-toolchain.md |
| B17 | pg | 4 | docs/gd32/06-clic-irq.md<br>docs/gd32/07-rcu-108m.md<br>docs/gd32/08-mtime-delay.md<br>docs/gd32/09-gpio-minimal.md |
| B18 | pl | 6 | docs/lab/e01-blink.md<br>docs/lab/e02-logic-uart.md<br>docs/lab/e03-scope-pwm.md<br>docs/lab/e04-priority-inversion.md<br>docs/lab/e05-i2c-eeprom.md<br>docs/lab/e06-lowpower-current.md |
| B19 | pl | 2 | docs/lab/e07-qmi8658.md<br>docs/lab/e08-audio-play.md |
| B20 | pj | 2 | docs/projects/01-f407-logger.md<br>docs/projects/02-s3-logger.md |
| B21 | pa | 5 | docs/ai/00-pair-not-ghost.md<br>docs/ai/01-prompt-patterns.md<br>docs/ai/03-toolflow-mcp.md<br>docs/ai/04-hallucination-defense.md<br>docs/ai/05-this-book-pipeline.md |
| B22 | appendices | 6 | mcu-book/book/A-工程深读.md<br>mcu-book/book/B-例程索引.md<br>mcu-book/book/C-习题答案.md<br>mcu-book/book/D-术语表.md<br>mcu-book/book/E-参考资料.md<br>mcu-book/book/F-常见问题.md |
| B23 | appendices | 1 | mcu-book/book/G-开源地图.md |

S篇包含样章S11和三个后续批次，全部18章都有归属；没有自动启动。附录A/G按知识审查，B索引/C生成答案/D术语/E来源/FFAQ按专用职责验收。最终机器对账须再次比较manifest，不沿用本表固定数字。

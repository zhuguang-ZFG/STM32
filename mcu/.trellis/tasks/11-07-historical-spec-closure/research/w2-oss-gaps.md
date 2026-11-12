# OSS 影响任务：G 地图 / 附录 B / 47 工程映射缺口（W2 只读）

日期：2026-11-12
对象：`10-26-oss-influence`（P1 附录 G 地图、P2 47 工程上游对照）
真源：`mcu-book/book/G-开源地图.md`（30 行）、`mcu-book/book/B-例程索引.md`（47 工程）、`code/projects.json`、`.trellis/tasks/10-26-oss-influence/research/verified-oss-projects.md`（18 条核验）

## 0. 结论摘要

1. **附录 B 与 `projects.json` 是精确一致的**：47/47 工程 ID 全在，无漏登、无多余；构建器契约没有缺口。
2. **附录 B 没有“上游对照”字段**：B 的表头是“工程 / 类型 / 入口 / 对应章节 / 内容”，P2 要求的“每个工程 1–3 行对应某个 OSS 实现的源码位置”**实际落地 0/47**。
3. **G 地图 30 行中，17 行有核验台账**（仓库存在、license 原文、stars、最近更新）；**13 行没有台账**，且其中 9 行的“许可”只写“见仓库 LICENSE/COPYING”，按设计文档“不能只写见 LICENSE 便称核实”的标准不合格。
4. **字段缺失**：30 行全部没有精确 tag/commit、没有逐行访问日期、没有逐行维护活跃度；只有全表一个“2026-10-26”星标快照日期。`probe-rs` 已核验但未进 G 地图。
5. **六类覆盖不达标且是结构性的**：按原 P1 六类（各 5–8 条）折算，RTOS 5、文件系统 2、网络 3、图形 1、工具链与调试 5、测试与质量 2——**4 类低于下界**。G 地图实际按“篇”（C/STM32/ESP32…）组织，不是六类组织；设计文档已把它登记为“需审的范围/位置差异”，不能拿总数 30 冒充符合。
6. 以 G 地图现有“对应章节”列反推：**18/47 工程**至少有一个章节级上游候选，**29/47 完全没有候选**。这只是线索，不能替代 P2 要求的符号级对照。

## 1. 对账基线

| 资产 | 数量 | 与相邻资产的关系 |
|---|---|---|
| `code/projects.json` | 47 | B 中 47 个工程行一一对应；无缺无余 |
| `mcu-book/book/B-例程索引.md` | 47 工程行（另有 3 行类型说明） | 表头无“上游对照”列 |
| `mcu-book/book/G-开源地图.md` | 30 仓库行 | 17 行有核验台账；13 行无 |
| `verified-oss-projects.md` | 18 条核验 | 17 条在 G 地图；`probe-rs` 不在 G |
| 原 P1 六类 × 5–8 | 30–48 条 | 当前 30 条总数够，但分布不满足四类下界 |

## 2. G 地图 13 条“无核验台账”清单

核验台账要求：仓库存在、license 原文、stars、最近更新。以下 13 行只有 G 表内自述，无台账条目（按 `verified-oss-projects.md` 逐条比对；`lwip` 的行文带“GitHub 镜像”后缀，属同一条）。

| # | 仓库 | G 表“篇” | G 表许可写法 | 缺口 |
|---|---|---|---|---|
| 1 | ARM-software/CMSIS_6 | C | Apache-2.0（见仓库 LICENSE） | 无台账；license 未读原文 |
| 2 | STMicroelectronics/cmsis-device-f4 | C | Apache-2.0（Cube 许可表逐组件标注） | 无台账；license 未读原文 |
| 3 | platformio/platformio-core | 构建 | 见仓库 `LICENSE` | 无台账；**许可名未写** |
| 4 | riscv-collab/riscv-gnu-toolchain | 构建 | GPL 家族（见仓库 `LICENSE`） | 无台账；**“GPL 家族”不精确** |
| 5 | STMicroelectronics/STM32CubeF4 | STM32 | 逐组件分列（BSD-3/Apache-2.0/SLA0044） | 无台账；分列未附原文 |
| 6 | libopencm3/libopencm3 | STM32 | 见仓库 `COPYING` | 无台账；**许可名未写** |
| 7 | stm32duino/Arduino_Core_STM32 | STM32 | 见仓库 `LICENSE` | 无台账；**许可名未写** |
| 8 | espressif/arduino-esp32 | ESP32 | 见仓库 `LICENSE` | 无台账；**许可名未写** |
| 9 | CommunityGD32Cores/gd32-pio-spl-package | GD32 | 见仓库 `LICENSE` | 无台账；**许可名未写** |
| 10 | blackmagic-debug/blackmagic | 调试 | 见仓库 `COPYING` | 无台账；**许可名未写**；仅标 archived |
| 11 | micropython/micropython | 运行时 | 见仓库 `LICENSE` | 无台账；**许可名未写** |
| 12 | rust-embedded/cortex-m | 运行时 | MIT / Apache-2.0 双许可 | 无台账；license 未读原文 |
| 13 | grbl/grbl | 控制器 | 见仓库 `COPYING` | 无台账；**许可名未写** |

> 另：`probe-rs/probe-rs` 在台账中（MIT OR Apache-2.0，3.0k），但 G 地图没有这一行。若保留台账，应决定是补进 G（调试类）还是标注为“已核验但不入图”。

## 3. 字段完整性（对照 `design.md` 的“真源与外部事实”）

| 字段 | 要求 | 现状 | 缺口 |
|---|---|---|---|
| 仓库地址 | 每条 | 30/30 | 无 |
| 精确 tag / commit | 每条 | **0/30** | 全缺；正文只写默认分支路径 |
| LICENSE 原文 / URL / 访问日期 | 每条 | 17/30 有台账；逐行访问日期 **0/30** | 13 条无台账；9 条连许可名都没有 |
| 维护活跃度（最近提交/发布） | 每条 | **0/30** 逐行；只有全表星标快照日 2026-10-26 | 无逐行数据；blackmagic 仅标 archived |
| 具体源码符号 | 每条 | 约 30/30 有“先读什么”文件/符号 | 基本满足，但未与 tag 绑定 |
| 对应章节 | 每条 | 30/30 | 满足 |

## 4. 原 P1 六类覆盖（按 G 表“篇”折算）

| 原六类 | G 地图对应行 | 数量 | 5–8 下界 |
|---|---|---|---|
| RTOS | rt-thread、FreeRTOS、zephyr、nuttx、RIOT | 5 | ✅ |
| 文件系统 | littlefs、spiffs | 2 | ❌ |
| 网络与协议栈 | lwip、nimble、tinyusb | 3 | ❌ |
| 图形与驱动框架 | lvgl（arduino-esp32/Arduino_Core_STM32 若按驱动框架算可到 3） | 1–3 | ❌ |
| 工具链与调试 | platformio、riscv-gnu-toolchain、openocd、pyOCD、blackmagic | 5 | ✅ |
| 测试与质量 | Unity、CMock | 2 | ❌ |

> 结构性差异：G 地图按书稿“篇”（C/构建/STM32/RTOS/ESP32/GD32/调试/运行时/控制器/存储/网络/图形/测试/SDK）组织，与 P1 的六类不是同一坐标系。设计文档明确“属于需审的范围/位置差异”，本清单不把它算作已满足。

## 5. 47 工程“上游对照”缺口

### 5.1 实际落地

- B 索引 47/47 有工程条目，但**没有上游对照列**；A 工程深读与 B 中未检索到 `上游对照 / 上游实现 / 对应位置 / heap_4` 等对照文本。
- 结论：**P2 实际落地 0/47**。任何“已完成映射”的说法都不成立。

### 5.2 章节级候选（只做线索，不是 P2 交付）

以 G 地图“对应章节”列反推：工程所在章节若被某 G 行引用，则该工程有一个候选。**18/47 有候选，29/47 无候选**。

| 工程 | 章节 | G 地图候选（章节级） |
|---|---|---|
| c-01-memory-model | /c/01-memory-model.md | rust-embedded/cortex-m |
| c-02-pointer | /c/02-pointer.md | 无 |
| c-03-volatile | /c/03-volatile.md | ARM-software/CMSIS_6 |
| c-04-struct-abi | /c/04-struct-abi.md | stm32duino/Arduino_Core_STM32 |
| c-05-func-pointer | /c/05-func-pointer.md | ThrowTheSwitch/Unity |
| c-06-abi-stack | /c/06-abi-stack.md | micropython/micropython；RIOT-OS/RIOT |
| c-07-ub-misra | /c/07-ub-misra.md | 无 |
| toolchain-01-four-steps | /build/01-four-steps.md | 无 |
| toolchain-02-elf | /build/02-elf.md | 无 |
| toolchain-03-linker | /build/03-linker-script.md | 无 |
| stm32-00-blink | /stm32/00-env.md；/stm32/03-gpio.md | STMicroelectronics/cmsis-device-f4；libopencm3/libopencm3 |
| stm32-01-arch | /stm32/01-arch.md | 无 |
| stm32-01-arch-board | /stm32/01-arch.md | 无 |
| stm32-01-rcc-clock | /stm32/02-rcc-clock.md | 无 |
| stm32-02-tim-pwm | /stm32/06-tim.md | grbl/grbl |
| stm32-03-uart-dma | /stm32/07-usart.md；/stm32/08-dma.md | 无 |
| stm32-04-nvic-exti | /stm32/04-nvic-exti.md | ARM-software/CMSIS_6 |
| stm32-04-nvic-exti-board | /stm32/04-nvic-exti.md | ARM-software/CMSIS_6 |
| stm32-05-systick | /stm32/05-systick.md | 无 |
| stm32-05-systick-board | /stm32/05-systick.md | 无 |
| stm32-09-adc | /stm32/09-adc.md | 无 |
| stm32-14-pwr | /stm32/14-pwr.md | 无 |
| stm32-16-debug-hardfault | /stm32/16-debug-hardfault.md | blackmagic-debug/blackmagic |
| stm32-05-framed-protocol | /c/08-framed-protocol.md | ThrowTheSwitch/CMock |
| stm32-06-watchdog-health | /stm32/17-watchdog-reset.md | 无 |
| stm32-07-sensor-logger | /projects/01-f407-logger.md | 无 |
| stm32-04-i2c-eeprom | /stm32/11-i2c.md | 无 |
| rtos-00-why-rtos | /rtos/freertos/00-why-rtos.md | zephyrproject-rtos/zephyr |
| rtos-01-freertos-lab | /rtos/freertos/01-task-tcb.md | 无 |
| rtos-02-rt-thread-lab | /rtos/rtthread/00-arch.md | 无 |
| rtos-03-scheduler | /rtos/freertos/03-scheduler.md | FreeRTOS/FreeRTOS-Kernel；apache/nuttx |
| rtos-05-sem-mutex | /rtos/freertos/05-sem-mutex.md | 无 |
| rtos-06-timers | /rtos/freertos/06-notify-event-timer.md | 无 |
| esp32-00-hello | /esp32/00-env.md | 无 |
| esp32-01-gpio-matrix | /esp32/02-gpio-matrix.md | 无 |
| esp32-02-uart-events | /esp32/05-uart-driver.md | espressif/arduino-esp32 |
| esp32-03-ledc-fade | /esp32/07-timer-ledc.md | 无 |
| esp32-04-qmi8658 | /esp32/06-spi-i2c-driver.md | 无 |
| esp32-05-audio-play | /esp32/12-audio-path.md | lvgl/lvgl（G 表自述“数据面/控制面同构”） |
| esp32-06-framed-protocol | /c/08-framed-protocol.md | ThrowTheSwitch/CMock |
| esp32-07-watchdog-health | /esp32/13-watchdog-health.md | 无 |
| esp32-08-sensor-logger | /projects/02-s3-logger.md | 无 |
| esp32-09-iram-discipline | /esp32/04-irq-dualcore.md | espressif/esp-idf |
| gd32-01-rcu-clock | /gd32/01-rcu-clock.md | 无 |
| common-behavior | /projects/01-f407-logger.md；/projects/02-s3-logger.md | 无 |
| common-reliability | /c/08-framed-protocol.md | ThrowTheSwitch/CMock |
| common-logger | /projects/01-f407-logger.md；/projects/02-s3-logger.md | 无 |

### 5.3 缺口分级

- **P2-A（硬缺口）**：47/47 工程都没有“文件 + 符号级”的上游对照行；B 表也没有承载列。
- **P2-B（候选缺口）**：29/47 工程连章节级候选都没有；其中 `toolchain-01/02/03`、`stm32-01-arch`、`stm32-01-rcc-clock`、`stm32-03-uart-dma`、`stm32-05-systick*`、`stm32-09-adc`、`stm32-14-pwr`、`rtos-01/02/05/06`、`esp32-00/01/03/04/07` 等，需要先补 OSS 条目或明确“无合适上游”。
- **P2-C（质量缺口）**：有候选的 18 个也只到“章节↔仓库”，未给具体函数/文件行，不能直接抄成 P2 交付；其中 `esp32-05-audio-play ↔ lvgl` 属于 G 表自述的弱类比，复核时应降级或换源。

## 6. 建议动作（只读建议，需另审）

1. **P1 先补核验**：13 条逐条读官方 `LICENSE/COPYING` 原文、记录访问日期、补 tag/commit 与最近提交；`probe-rs` 决定入图或标注不入图。
2. **字段升级**：G 表增加 `tag/commit`、`许可（原文首行）`、`访问日期`、`最近提交` 四列，或把台账并入 G（单真源，不另起第二张表）。
3. **六类口径复核**：由用户决定“保留篇章结构 + 明确不承诺六类”还是“按六类重排/补条”；本清单不替用户选。
4. **P2 映射表**：先定承载位置（B 增列 or 单独附录小节），再按 47 行逐条写“本工程断言/函数 ↔ 上游文件/符号”，每条附 tag/commit；29 个无候选工程先补源或明确“无”。
5. **不改 `projects.json`、不改工程源码**；新增工程/测试/CI 仍按原任务约束另审。

## 7. 证据命令（可复跑）

```bash
python - <<'PY'  # B 与 projects.json 精确对账、G 行数/分类、台账交集
...
PY
grep -rn "上游对照\|上游实现\|对应位置\|heap_4" mcu-book/book/A-工程深读.md mcu-book/book/B-例程索引.md
```

本轮实跑结果：B 工程行 47、projects.json 47、交集 47/47；G 行 30；台账 18 条；G 无台账 13 条；许可名未写 9 条；工程有章节级候选 18/47。

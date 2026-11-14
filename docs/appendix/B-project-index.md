---
title: "配套工程索引"
platforms: [generic]
---

# 附录 B · 配套工程索引

## 本章罗盘

- **问题**：全书配套工程在哪两个登记簿里，各多少条、什么类型、怎么跑？例程的「最小可见结果/验收工具/不能由此推出」三列怎么用？跑表前要对哪几行账？工程证据的两档（宿主验证/目标板验证）怎么区分？
- **交付**：能在双登记簿里找到任何一章的配套工程并按入口跑起来；能按推荐跑法安排实验顺序；能填出每例程的交付记录七字段。
- **边界**：本附录是索引层，不代填证据状态（以各工程 README 为准）；账表本体在 附录 D（本附录落位时 D 尚未链接，账已并入附录 D 文末）；许可边界见附录 E（落位后链接）。
- **依据锚点**：根书例程区 `examples/`（15 条，MIT）与姊妹书工程区 `code/`（47 项，projects.json 登记，Apache-2.0）；`motor-dc-speed` 为 B3 批次补登。


本附录是全书配套工程的**双登记簿**：根书例程区（`examples/`，F103 线，15 条）与姊妹书工程区（`code/`，47 个可编译验证工程，F407/ESP32/GD32/宿主四类）。例程不是「复制后能编译」就结束——每个工程都要留下可观察结果，并写清不能由该结果推出什么。

- 根书区：`examples/` 下 14 例程 + 补登的 `motor-dc-speed`（B3 批次新增，源表漏登），MIT 许可。
- 姊妹书区：`code/` 下 47 工程，`code/projects.json` 登记、CI 逐个构建（ARM 工程用 arm-none-eabi-gcc；ESP-IDF 工程用 `espressif/idf:v5.5.2` 容器，target esp32s3；宿主工程用本机 gcc），Apache-2.0。

完整许可边界见 附录 E。

## 第一区 · 根书例程（F103 线，BluePill）

默认平台 STM32F103C8T6；时钟、接线与固件包版本以各目录 README 为准。关联章按合并书章号标注。

| 顺序 | 例程 | 关联章 | 最小可见结果 | 验收工具 | 不能由此推出 |
| --- | --- | --- | --- | --- | --- |
| 1 | `gpio-blink` | v1 第 9 章 | PC13 约 1 Hz 闪烁，PA0 外接灯按另一周期翻转 | 逻辑分析仪/万用表 | 所有 GPIO 都能承受同一负载 |
| 2 | `exti-key` | v1 第 10 章 | PA0 每次有效按下只翻转一次 PC13 | 逻辑分析仪 + 中断计数 | 消抖参数适合所有按键 |
| 3 | `timer-pwm` | v1 第 12 章 | PA6 为 1 kHz，CCR 改变时占空比连续变化 | 示波器/逻辑分析仪 | LED 亮度与占空比线性 |
| 4 | `uart-dma-idle` | v1 第 13、14 章 | 多种长度命令完整入队，ORE 后可恢复 | USB-TTL + 字节对比/计数器 | IDLE 等同业务帧界；持续流永不溢出 |
| 5 | `i2c-oled` | v1 第 16 章 | OLED 显示并持续刷新，地址扫描只命中目标 | 逻辑分析仪 I2C 解码 | 任意 OLED 都用同一地址/初始化表 |
| 6 | `spi-flash` | v1 第 16 章 | JEDEC ID 为 `0xEF4017`，跨页写入后逐字节一致 | 逻辑分析仪 + `memcmp` | 擦写寿命、掉电原子性已满足产品要求 |
| 7 | `adc-dma` | v1 第 15 章 | 3 通道连续采样，输入变化与对应通道一致 | 万用表 + DMA 缓冲观察 | 名义 3.3 V 可当精密参考 |
| 8 | `rtc-alarm` | v1 第 11 章 | STOP 后按计划唤醒，VBAT 条件下时间连续 | 电流表 + 串口时间戳 | 整板达到数据手册芯片典型电流 |
| 9 | `iap-bootloader` | v1 第 17 章 | 镜像校验通过后跳转；损坏镜像不跳转 | 串口 + 复位/掉电注入 | 已具备签名、反回滚和安全启动 |
| 10 | `can-bxcan` | v1 第 13 章（[第 35 章](../v4-platforms/35-can-usb-fieldbus.md) 口径） | 环回自收；双节点时有 ACK 且过滤器生效 | CAN 分析仪/错误计数 | FDCAN 可直接复用同一寄存器配置 |
| 11 | `usb-cdc` | v1 第 13 章（[第 35 章](../v4-platforms/35-can-usb-fieldbus.md) USB 半场） | 主机枚举出 CDC，`wTotalLength`=67、VID/PID `0x1209/0x0001`，双向字节传输 | USB 抓包/系统设备信息 | 所有主机、线缆和挂起恢复均兼容；VID 也不是 ST 例程的 `0x0483` |
| 12 | `usb-hid` | v1 第 13 章（[第 35 章](../v4-platforms/35-can-usb-fieldbus.md)） | PA0 边沿产生一次按下和一次全零释放报告 | 文本框 + USB 抓包 | 可作为安全输入设备或通过 USB-IF 认证 |
| 13 | `freertos-task` | [第 22 章](../v3-rtos/22-tasks-tcb-scheduler.md) | 三任务运行，队列空时阻塞，按键事件唤醒任务 | trace/运行时统计 + 串口 | 最坏响应时间和栈裕量已被证明 |
| 14 | `spl-f1-blink` | v1 第 7 章 | ELF/HEX/BIN/MAP 构建闭合；真板 PC13 约 1 Hz | GNU Arm size/nm + ST-Link + 逻辑分析仪 | 编译链接通过等于真板已验证 |
| 15（补登） | `motor-dc-speed` | [第 37 章](../v5-motion/37-dc-motor-openloop.md) | 开环 PWM 驱动直流电机，斜坡受控起停 | 电流表 + 示波器 | 端点语义与限幅账已被板上验证（[第 37 章](../v5-motion/37-dc-motor-openloop.md) 数值断言钉的是文案） |

### 先和账对上的四行（时钟与位时间）

跑表之前，先把四行与 附录 D 文末前两张账对上——对不上就先不要加下一种总线：

| 例程 | 先对上的数 | 对不上说明什么 |
| --- | --- | --- |
| `gpio-blink` | PC13 低电平点亮，电流不代表别的脚 | 极性反了，或用 PC13 的亮度要求普通脚 |
| `timer-pwm` | 72 MHz：PSC 71、ARR 999 → 1 kHz；用 36 MHz 除会算出 500 Hz | 示波器上是 500 Hz 或 2 kHz |
| `uart-dma-idle` | USART1、115200、BRR `0x271`；IDLE 约 86.8 µs 不是帧界 | 把 0.16% 误差当成这只 USART 已经偏了 |
| `can-bxcan` | APB1 36 MHz：P9、BS1 5、BS2 2 → 500 kbit/s；P8×10 Tq 是 450 kbit/s | 分析仪停在 450 kbit/s；把回环当双节点应答 |

### 通道和描述符再对三行

附录 D 第三张账，对请求号、描述符长度和栈的单位：

| 例程 | 先对上的数 | 对不上说明什么 |
| --- | --- | --- |
| `spi-flash` | `0x9F` 读回 `0xEF 0x40 0x17`；72 MHz、`BR=010` 时 SCK=9 MHz | ID 全 0/全 FF，或把 `0x40` 当容量 |
| `usb-cdc` | `USBPRE=0`：72 MHz→48 MHz；配置集合 67 B；VID/PID `0x1209/0x0001` | 枚举卡描述符；按 ST 的 `0x0483/0x5740` 对这份固件 |
| `freertos-task` | 栈深按字：128/192/256 字 = 512/768/1024 B；tick 1 ms | 把 128 当字节，创建即 HardFault |

### 推荐跑法

1. **先闭环**：`gpio-blink → exti-key → timer-pwm`——证明下载、引脚、时基。
2. **再连外设**：`uart-dma-idle → i2c-oled → spi-flash → adc-dma`——一次一种总线。
3. **再处理状态**：`rtc-alarm → iap-bootloader → can-bxcan → usb-*`——每步保留可回退镜像。
4. **最后并发**：`freertos-task`——裸机行为可解释后，调度问题才不与驱动混淆。
5. **最后对照旧库**：`spl-f1-blink` 单独 SPL V3.5.0 + CMake，不与 HAL 示例双重初始化。

### 每例程的交付记录

| 字段 | 示例 |
| --- | --- |
| 芯片/板卡 | STM32F103C8T6，BluePill 丝印与来源 |
| 工具版本 | IDE、编译器、固件包 tag/commit |
| 接线 | 电源、电平、共地、引脚与外部器件型号 |
| 期望 | 可量化的频率、字节、ID、时间或状态 |
| 实际 | 仪器值、串口原始字节、错误寄存器 |
| 边界 | 仿真/真板、温度、电源、未覆盖的失败路径 |
| 复现 | 从干净工程到观察结果的最短步骤 |

![手绘板：先对四行账（原理示意，非实拍）](/images/app-b-four-rows.png)

![手绘板：通道与描述符三行（原理示意，非实拍）](/images/app-b-channel-desc.png)

![手绘板：推荐跑法五步（原理示意，非实拍）](/images/app-b-run-order.png)

![手绘板：交付记录字段（原理示意，非实拍）](/images/app-b-delivery.png)

## 第二区 · 姊妹书工程（code/，47 项）

入口/类型/验证方式由 `code/projects.json` 登记，CI 按同一清单逐个构建。类型三档：`host-probe`（宿主取证，`sh probe.sh`）、`arm-make`（裸机 Makefile，`make`/`make flash`）、`esp-idf`（`idf.py build`）。「对应章」按合并书章号标注（原 mcu 站编号在括号内）。

### C 篇与构建篇（宿主机取证）

| 工程 | 类型 | 对应章 | 内容 |
| --- | --- | --- | --- |
| c-01-memory-model | host-probe | [第 1 章](../v0-foundations/01-c-memory-model.md) | 段归属实测、const 经济学 |
| c-02-pointer | host-probe | [第 1 章](../v0-foundations/01-c-memory-model.md) | 读写六函数宽度对照 |
| c-03-volatile | arm-make | [第 2 章](../v0-foundations/02-c-volatile-ub.md) | -O0/-O2 反汇编对照 |
| c-04-struct-abi | host-probe | [第 3 章](../v0-foundations/03-struct-abi-registers.md) | offsetof/_Static_assert 验证 |
| c-05-func-pointer | host-probe | [第 4 章](../v0-foundations/04-function-pointer-state-machine.md) | 状态机+环形缓冲断言 |
| c-06-abi-stack | host-probe | [第 3 章](../v0-foundations/03-struct-abi-registers.md) | AAPCS 传参/栈帧实测 |
| c-07-ub-misra | host-probe | [第 2 章](../v0-foundations/02-c-volatile-ub.md) | 优化等级翻脸实录 |
| toolchain-01-four-steps | host-probe | [第 5 章](../v0-foundations/05-toolchain-four-steps.md) | 四步构建全套中间产物 |
| toolchain-02-elf | host-probe | [第 6 章](../v0-foundations/06-linker-startup-map.md) | ELF 五刀解剖 |
| toolchain-03-linker | host-probe | [第 6 章](../v0-foundations/06-linker-startup-map.md) | 删 KEEP/AT> 的六刀取证 |

### STM32F407 寄存器主线

| 工程 | 类型 | 对应章 | 内容 |
| --- | --- | --- | --- |
| stm32-00-blink | arm-make | [第 9 章](../v1-drivers/09-gpio.md) | 寄存器版点灯 |
| stm32-01-arch / -board | host-probe / arm-make | [第 8 章](../v1-drivers/08-architecture-memory-clock.md) | 位带断言 + 板上验证 |
| stm32-01-rcc-clock | arm-make | [第 8 章](../v1-drivers/08-architecture-memory-clock.md) | 168 MHz 提频六步 |
| stm32-02-tim-pwm | arm-make | [第 12 章](../v1-drivers/12-timers-pwm.md) | PWM 呼吸灯 + 输入捕获 |
| stm32-03-uart-dma | arm-make | [第 13、14 章](../v1-drivers/13-uart-framed-protocol.md)、[附录 A](./A-engineering-deep-read.md) | IDLE+DMA 环形接收寄存器版 |
| stm32-04-nvic-exti / -board | host-probe / arm-make | [第 10 章](../v1-drivers/10-interrupts-nvic-exti.md) | IRQn→ISER/IP 换算断言 + 上板 |
| stm32-05-systick / -board | host-probe / arm-make | [第 11 章](../v1-drivers/11-systick-timebase-rtc.md) | LOAD 手算/回绕断言 + 上板 |
| stm32-09-adc | host-probe | [第 15 章](../v1-drivers/15-adc-dac-sampling.md) | 12 轮 SAR 试探表 |
| stm32-14-pwr | host-probe | [第 18 章](../v2-reliability/18-low-power.md) | 三档睡眠换算与 CMSIS 对账 |
| stm32-16-debug-hardfault | host-probe | [第 20 章](../v2-reliability/20-debug-performance.md) | CFSR/BFAR 取证演练 |
| stm32-05-framed-protocol | arm-make | [第 13 章](../v1-drivers/13-uart-framed-protocol.md)、[附录 A](./A-engineering-deep-read.md) | COBS+CRC 帧协议寄存器版 |
| stm32-06-watchdog-health | arm-make | [第 19 章](../v2-reliability/19-watchdog-reset-hardfault.md) | IWDG+WWDG+健康监督（8 变体） |
| stm32-07-sensor-logger | arm-make | [第 41 章](../v6-labs-projects/41-dual-board-logger-project.md) | F407 记录器整机（故障注入） |
| stm32-04-i2c-eeprom | arm-make | [第 16 章](../v1-drivers/16-i2c-spi.md) | EEPROM 读写 + 总线恢复 |

### RTOS 双精讲

| 工程 | 类型 | 对应章 | 内容 |
| --- | --- | --- | --- |
| rtos-00-why-rtos | host-probe | [第 21 章](../v3-rtos/21-why-rtos.md) | 裸机可行性账与超级循环翻车 |
| rtos-01-freertos-lab | arm-make | [第 21–24 章](../v3-rtos/21-why-rtos.md) | FreeRTOS 全场景实验（6 场景） |
| rtos-02-rt-thread-lab | arm-make | [第 21–24 章](../v3-rtos/22-tasks-tcb-scheduler.md) | RT-Thread Nano 移植与验收 |
| rtos-03-scheduler | host-probe | [第 22 章](../v3-rtos/22-tasks-tcb-scheduler.md) | 双路径选优 O(1) 对照 |
| rtos-05-sem-mutex | host-probe | [第 24 章](../v3-rtos/24-queue-semaphore-notification.md) | 优先级反转剧本双版本 |
| rtos-06-timers | host-probe | [第 24 章](../v3-rtos/24-queue-semaphore-notification.md) | 守护任务 RAM 账与五幕推演 |

### ESP32-S3 + ESP-IDF

| 工程 | 类型 | 对应章 | 内容 |
| --- | --- | --- | --- |
| esp32-00-hello | esp-idf | [第 30 章](../v4-platforms/30-esp32s3-architecture-boot.md) | 第一个 IDF 工程与 monitor |
| esp32-01-gpio-matrix | esp-idf | [第 31 章](../v4-platforms/31-esp32-drivers-audio.md) | io_mux 对照实验 |
| esp32-02-uart-events | esp-idf | [第 31 章](../v4-platforms/31-esp32-drivers-audio.md) | 事件驱动不定长接收 |
| esp32-03-ledc-fade | esp-idf | [第 31 章](../v4-platforms/31-esp32-drivers-audio.md) | 硬件 fade 呼吸灯 |
| esp32-04-qmi8658 | esp-idf | [第 31 章](../v4-platforms/31-esp32-drivers-audio.md) | 六轴传感器读数 |
| esp32-05-audio-play | esp-idf | [第 31 章](../v4-platforms/31-esp32-drivers-audio.md) | I2S 放音与旋律 |
| esp32-06-framed-protocol | esp-idf | [附录 A](./A-engineering-deep-read.md) | 与 F407 同 codec 的 S3 版 |
| esp32-07-watchdog-health | esp-idf | [第 32 章](../v4-platforms/32-esp32-wifi-ble-espnow.md) | TWDT 健康监督（故障注入） |
| esp32-08-sensor-logger | esp-idf | [第 41 章](../v6-labs-projects/41-dual-board-logger-project.md) | S3 版记录器整机 |
| esp32-09-iram-discipline | esp-idf | [v1 第 10 章](../v1-drivers/10-interrupts-nvic-exti.md)、[第 34 章](../v4-platforms/34-multicore-cache.md) | IRAM/Flash 落址取证 |

### GD32 与公共核心层

| 工程 | 类型 | 对应章 | 内容 |
| --- | --- | --- | --- |
| gd32-01-rcu-clock | arm-make | [第 29 章](../v4-platforms/29-gd32-arm-riscv.md) | 200 MHz 分频账与官方库对照 |
| common-behavior | host-probe | [第 41 章](../v6-labs-projects/41-dual-board-logger-project.md) | 行为层（滤波/状态）断言 |
| common-reliability | host-probe | [附录 A](./A-engineering-deep-read.md) | 帧 codec + 健康监测全断言 |
| common-logger | host-probe | [第 41 章](../v6-labs-projects/41-dual-board-logger-project.md) | 记录槽位/代次/饱和计数 |

### 证据状态

工程分两档：**宿主验证**（host-probe 与公共层：断言全绿、CI 必跑）与**目标板验证**（arm-make/esp-idf：CI 验证「能干净构建」，板上现象按各章「待上板实测」口径另行回填——见 [第 40 章](../v6-labs-projects/40-lab-method-instruments.md) 的实测记录制度）。哪个工程处于哪一档，以各工程 README 清单为准，本表不代填。

根书例程区源码在 `examples/`（MIT）；姊妹书工程区在 `code/`（Apache-2.0）；本书正文与图 CC BY 4.0（根域）/Apache-2.0（mcu 域）——完整许可边界见 附录 E。

# 配套工程索引：47 个可编译验证的工程

全书正文里每一处"配套工程"都指向 `code/` 下的一个独立目录。本附录是全量索引：47 个工程与章节一一对应，入口、类型与验证方式由 `code/projects.json` 登记，CI 按同一清单逐个构建验证（ARM 工程用 arm-none-eabi-gcc，ESP-IDF 工程用 `espressif/idf:v5.5.2` 容器、target `esp32s3`，宿主工程用本机 gcc）。构建器在出书时会核对本表与 `projects.json` 一致：漏登一个工程，书就构建不出来。

## 类型说明

| 类型 | 含义 | 怎么跑 |
|---|---|---|
| `host-probe` | 宿主机取证脚本，不需要开发板 | 进入目录 `sh probe.sh` |
| `arm-make` | F407/GD32 裸机 Makefile 工程 | `make`（有板时 `make flash`） |
| `esp-idf` | ESP-IDF 工程（esp32s3） | `idf.py build` / `idf.py flash monitor` |

## C 篇与构建篇（宿主机取证）

| 工程 | 类型 | 入口 | 对应章节 | 内容 |
|---|---|---|---|---|
| c-01-memory-model | host-probe | probe.sh | [C1 内存模型](/c/01-memory-model.md) | 段归属实测：nm 地址/介质对账、const 经济学 |
| c-02-pointer | host-probe | probe.sh | [C2 指针](/c/02-pointer.md) | 读写六函数宽度对照汇编、const 三组合 |
| c-03-volatile | host-make | Makefile | [C3 volatile](/c/03-volatile.md) | -O0/-O2 反汇编对照（volatile 有无各一版） |
| c-04-struct-abi | host-probe | probe.sh | [C4 结构体与 ABI](/c/04-struct-abi.md) | offsetof/_Static_assert 偏移验证、位域禁区 |
| c-05-func-pointer | host-probe | probe.sh | [C5 函数指针](/c/05-func-pointer.md) | 状态机+环形缓冲 560 断言、免锁口径 |
| c-06-abi-stack | host-probe | probe.sh | [C6 调用约定与栈帧](/c/06-abi-stack.md) | AAPCS 传参/栈帧实测、宿主 vs M4 帧账 |
| c-07-ub-misra | host-probe | probe.sh | [C7 UB 与 MISRA](/c/07-ub-misra.md) | 优化等级翻脸实录、三道防线编译旗 |
| toolchain-01-four-steps | host-probe | probe.sh | [B1 四步构建](/build/01-four-steps.md) | 手动四步的全套中间产物 |
| toolchain-02-elf | host-probe | probe.sh | [B2 ELF 解剖](/build/02-elf.md) | 五刀解剖：段表/程序头/nm 对账 |
| toolchain-03-linker | host-probe | probe.sh | [B3 链接脚本](/build/03-linker-script.md) | 删 KEEP/AT> 的六刀取证 |

## STM32F407 寄存器主线

| 工程 | 类型 | 入口 | 对应章节 | 内容 |
|---|---|---|---|---|
| stm32-00-blink | arm-make | Makefile | [S0 环境](/stm32/00-env.md) · [S3](/stm32/03-gpio.md) · [E01](/lab/e01-blink.md) | 第一个寄存器版点灯 |
| stm32-01-arch | host-probe | probe.sh | [S1 架构](/stm32/01-arch.md) | 位带别名断言 + -O2 反汇编互证 |
| stm32-01-arch-board | arm-make | Makefile | [S1 架构](/stm32/01-arch.md) | 位带的板上验证工程 |
| stm32-01-rcc-clock | arm-make | Makefile | [S2 时钟树](/stm32/02-rcc-clock.md) | 168MHz 提频六步 |
| stm32-02-tim-pwm | arm-make | Makefile | [S6 定时器](/stm32/06-tim.md) · [E03](/lab/e03-scope-pwm.md) | PWM 呼吸灯 + 输入捕获 |
| stm32-03-uart-dma | arm-make | Makefile | [S7 USART](/stm32/07-usart.md) · [S8 DMA](/stm32/08-dma.md) · 附录 A | IDLE+DMA 环形接收寄存器版 |
| stm32-04-nvic-exti | host-probe | probe.sh | [S4 NVIC](/stm32/04-nvic-exti.md) | IRQn→ISER/IP 换算 52 断言 |
| stm32-04-nvic-exti-board | arm-make | Makefile | [S4 NVIC](/stm32/04-nvic-exti.md) | 按键外部中断上板工程 |
| stm32-05-systick | host-probe | probe.sh | [S5 SysTick](/stm32/05-systick.md) | LOAD 手算/回绕安全 42 断言 |
| stm32-05-systick-board | arm-make | Makefile | [S5 SysTick](/stm32/05-systick.md) | 精确延时上板工程 |
| stm32-09-adc | host-probe | probe.sh | [S9 ADC](/stm32/09-adc.md) | 12 轮 SAR 试探表全算 |
| stm32-14-pwr | host-probe | probe.sh | [S14 低功耗](/stm32/14-pwr.md) | 三档睡眠换算与 CMSIS 对账 |
| stm32-16-debug-hardfault | host-probe | probe.sh | [S16 HardFault](/stm32/16-debug-hardfault.md) | CFSR/BFAR 解读与取证演练 |
| stm32-05-framed-protocol | arm-make | Makefile | [C8 帧协议](/c/08-framed-protocol.md) · 附录 A | COBS+CRC 帧协议寄存器版 |
| stm32-06-watchdog-health | arm-make | Makefile | [S17 看门狗](/stm32/17-watchdog-reset.md) | IWDG+WWDG+健康监督（8 变体矩阵） |
| stm32-07-sensor-logger | arm-make | Makefile | [J1 记录器](/projects/01-f407-logger.md) | F407 传感器记录器整机（故障注入） |
| stm32-04-i2c-eeprom | arm-make | Makefile | [S11 I2C](/stm32/11-i2c.md) · [E05](/lab/e05-i2c-eeprom.md) | EEPROM 读写 + 总线恢复 |

## RTOS 双精讲

| 工程 | 类型 | 入口 | 对应章节 | 内容 |
|---|---|---|---|---|
| rtos-00-why-rtos | host-probe | probe.sh | [F0 为什么 RTOS](/rtos/freertos/00-why-rtos.md) | 裸机可行性账与超级循环翻车实录 |
| rtos-01-freertos-lab | arm-make | Makefile | [F1–F8 FreeRTOS](/rtos/freertos/01-task-tcb.md) | FreeRTOS 全场景实验（6 场景） |
| rtos-02-rt-thread-lab | arm-make | Makefile | [R0–R7 RT-Thread](/rtos/rtthread/00-arch.md) | RT-Thread Nano 移植与验收 |
| rtos-03-scheduler | host-probe | probe.sh | [F3 调度器](/rtos/freertos/03-scheduler.md) | 双路径选优 O(1) 对照实测 |
| rtos-05-sem-mutex | host-probe | probe.sh | [F5 信号量](/rtos/freertos/05-sem-mutex.md) · [E04](/lab/e04-priority-inversion.md) | 优先级反转剧本双版本复现 |
| rtos-06-timers | host-probe | probe.sh | [F6 软件定时器](/rtos/freertos/06-notify-event-timer.md) | 守护任务 RAM 账与五幕推演 |

## ESP32-S3 + ESP-IDF

| 工程 | 类型 | 入口 | 对应章节 | 内容 |
|---|---|---|---|---|
| esp32-00-hello | esp-idf | CMakeLists.txt | [P0 环境](/esp32/00-env.md) | 第一个 IDF 工程与 monitor |
| esp32-01-gpio-matrix | esp-idf | CMakeLists.txt | [P2 GPIO 矩阵](/esp32/02-gpio-matrix.md) | io_mux 对照实验 |
| esp32-02-uart-events | esp-idf | CMakeLists.txt | [P5 UART 驱动](/esp32/05-uart-driver.md) | 事件驱动不定长接收 |
| esp32-03-ledc-fade | esp-idf | CMakeLists.txt | [P7 定时器与 LEDC](/esp32/07-timer-ledc.md) | 硬件 fade 呼吸灯 |
| esp32-04-qmi8658 | esp-idf | CMakeLists.txt | [P6 驱动框架](/esp32/06-spi-i2c-driver.md) · [E07](/lab/e07-qmi8658.md) | 六轴传感器读数 |
| esp32-05-audio-play | esp-idf | CMakeLists.txt | [P12 音频](/esp32/12-audio-path.md) · [E08](/lab/e08-audio-play.md) | I2S 放音"滴"与旋律 |
| esp32-06-framed-protocol | esp-idf | CMakeLists.txt | [C8 帧协议](/c/08-framed-protocol.md) · 附录 A | 与 F407 同 codec 的 S3 版 |
| esp32-07-watchdog-health | esp-idf | CMakeLists.txt | [P13 看门狗](/esp32/13-watchdog-health.md) | TWDT 健康监督（故障注入） |
| esp32-08-sensor-logger | esp-idf | CMakeLists.txt | [J2 记录器](/projects/02-s3-logger.md) | S3 版记录器整机（故障注入） |
| esp32-09-iram-discipline | esp-idf | CMakeLists.txt | [P4 中断与双核](/esp32/04-irq-dualcore.md) | IRAM/Flash 落址取证 |

## GD32 双系

| 工程 | 类型 | 入口 | 对应章节 | 内容 |
|---|---|---|---|---|
| gd32-01-rcu-clock | arm-make | Makefile | [G1 RCU 时钟树](/gd32/01-rcu-clock.md) | 200MHz 分频账与官方库对照 |

## 公共核心层（双板共用，宿主可测）

| 工程 | 类型 | 入口 | 对应章节 | 内容 |
|---|---|---|---|---|
| common-behavior | host-probe | probe.sh | [J1](/projects/01-f407-logger.md) · [J2](/projects/02-s3-logger.md) | 行为层（滤波/状态）断言 |
| common-reliability | host-probe | probe.sh | [C8](/c/08-framed-protocol.md) · 附录 A | 帧 codec+健康监测全断言 |
| common-logger | host-probe | probe.sh | [J1](/projects/01-f407-logger.md) · [J2](/projects/02-s3-logger.md) | 记录槽位/代次/饱和计数 |

## 证据状态

工程分两档证据：**宿主验证**（host-probe 与公共层：断言全绿、CI 必跑）与**目标板验证**（arm-make/esp-idf：CI 验证"能干净构建"，板上现象按各章「待上板实测」口径另行回填（见 [实验中心](/lab/index.md) 的实测记录制度））。哪个工程处于哪一档，以各工程 README 的清单为准，本表不代填。

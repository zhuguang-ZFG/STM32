---
title: "开源项目与社区地图"
platforms: [generic]
---

# 附录 F · 开源项目与社区地图

## 本章罗盘

- **问题**：开源仓库怎么选、怎么读、怎么提问，许可能不能链进固件？哪些知识点只有读源码才拿得到？读完七卷之后，「下一步怎么走」与「什么算读完」在哪里收束？
- **交付**：能按仓库地图找到目标 `.h` 或函数；能区分归档与只读镜像；能用许可五族表判断「能不能链进闭源固件」；能按提问五件事开一个可回答的 issue；能按收束页的三条读完标准自查。
- **边界**：星标数与活跃度取 2026-10-26 的 GitHub API 返回值，许可取各仓库根 `LICENSE` 原文；知识点路径按当日默认分支，版本漂移后先 `git log -1`。**星标多是「人多」，不是「该读」**——该不该读只看一条：仓库里有没有你要找的那个 `.h` 或那个函数。
- **依据锚点**：双源合并——mcu 30 仓表为底（超集）+ 根书 23 仓表的「章」列并入（两源星标同日 2026-10-26，23 个交集逐仓一致）；根书「学习路线收束」页（mapping:36）收在本附录末节。

## 一、仓库地图（30 个仓库）

| 篇 | 仓库 | 星标 | 许可 | 先读什么 | 对应章节 |
| --- | --- | --- | --- | --- | --- |
| C | ARM-software/CMSIS_6 | 483 | Apache-2.0 | `CMSIS/Core/Include/core_cm4.h`：内联函数与屏障宏、`__I/__O/__IO` | [第 2 章](../v0-foundations/02-c-volatile-ub.md)、[第 10 章](../v1-drivers/10-interrupts-nvic-exti.md) |
| C | STMicroelectronics/cmsis-device-f4 | 161 | Apache-2.0（Cube 许可表逐组件标注） | `Include/stm32f407xx.h`：寄存器结构体与位域 | [第 9 章](../v1-drivers/09-gpio.md) |
| 构建 | platformio/platformio-core | 9564 | 见仓库 `LICENSE` | `platformio/builder/`：谁决定 `-mcpu` 与链接脚本 | [第 7 章](../v0-foundations/07-build-systems-legacy.md) |
| 构建 | riscv-collab/riscv-gnu-toolchain | 4651 | GPL 家族 | `Makefile.in` 的 `--with-arch/--with-abi` 缺省值 | [第 29 章](../v4-platforms/29-gd32-arm-riscv.md) |
| STM32 | STMicroelectronics/STM32CubeF4 | 1361 | HAL/BSP/Projects=BSD-3-Clause；CMSIS/mbedTLS=Apache-2.0；USB/STemWin/TouchGFX=SLA0044 | `Drivers/STM32F4xx_HAL_Driver/Src/` 任一外设的 `Init` | [第 9 章](../v1-drivers/09-gpio.md) |
| STM32 | libopencm3/libopencm3 | 3671 | 见 `COPYING` | `include/libopencm3/stm32/f4/memorymap.h`：把手册翻成宏 | [第 9 章](../v1-drivers/09-gpio.md) |
| STM32 | stm32duino/Arduino_Core_STM32 | 3375 | 见 `LICENSE` | `system/Drivers/` 与 `cores/arduino/` 的边界 | [第 3 章](../v0-foundations/03-struct-abi-registers.md) |
| RTOS | RT-Thread/rt-thread | 12309 | Apache-2.0 | `src/object.c` 对象容器、`src/components.c` 初始化档位 | [第 26 章](../v3-rtos/26-device-framework-shell.md) |
| RTOS | FreeRTOS/FreeRTOS-Kernel | 4609 | MIT | `tasks.c` 就绪表与切换、`portable/GCC/ARM_CM4F/` | [第 22 章](../v3-rtos/22-tasks-tcb-scheduler.md) |
| RTOS | zephyrproject-rtos/zephyr | 16906 | Apache-2.0 | `include/zephyr/device.h`：设备树的运行期投影 | [第 21 章](../v3-rtos/21-why-rtos.md)、[第 27 章](../v3-rtos/27-rtos-comparison-selection.md) |
| ESP32 | espressif/esp-idf | 19347 | Apache-2.0（`esp_err.h` 的 SPDX 头可证） | `components/esp_common/include/esp_err.h` | [第 10、34 章](../v1-drivers/10-interrupts-nvic-exti.md)、[第 30 章](../v4-platforms/30-esp32s3-architecture-boot.md) |
| ESP32 | espressif/arduino-esp32 | 17629 | 见 `LICENSE` | `cores/esp32/esp32-hal-*.c`：Arduino API 怎么落到 IDF | [第 31 章](../v4-platforms/31-esp32-drivers-audio.md) |
| GD32 | CommunityGD32Cores/gd32-pio-spl-package | 10 | 见 `LICENSE` | GD32 SPL 的重打包规则 | [第 29 章](../v4-platforms/29-gd32-arm-riscv.md) |
| 调试 | openocd-org/openocd | 2365 | GPL-2.0 | `src/flash/nor/stm32f2x.c`：Flash 算法怎么写 | [v1 第 17 章](../v1-drivers/17-flash-iap-ota.md) |
| 调试 | pyocd/pyOCD | 1473 | Apache-2.0 | `pyocd/core/` 的 target 抽象 | [v1 第 20 章](../v2-reliability/20-debug-performance.md) |
| 调试 | blackmagic-debug/blackmagic | 3719 | 见 `COPYING` | **已归档**（`archived: true`），仅作阅读 | [第 20 章](../v2-reliability/20-debug-performance.md) |
| 运行时 | micropython/micropython | 22154 | 见 `LICENSE` | `ports/*/mpconfigport.h`：移植层要暴露什么 | [第 3 章](../v0-foundations/03-struct-abi-registers.md) |
| 运行时 | rust-embedded/cortex-m | 1010 | MIT/Apache-2.0 双许可 | `src/peripheral/` 与 `asm.rs`：裸机抽象的另一条路 | [第 1 章](../v0-foundations/01-c-memory-model.md) |
| 控制器 | grbl/grbl | 6309 | GPL-3.0 | `grbl/stepper.c`：中断里只做最少事 | [第 12 章](../v1-drivers/12-timers-pwm.md)、[第 37 章](../v5-motion/37-dc-motor-openloop.md) |
| RTOS | apache/nuttx | 4087 | Apache-2.0 | `sched/` 任务模型、`drivers/` 分层注册 | [第 22 章](../v3-rtos/22-tasks-tcb-scheduler.md) 对照 |
| RTOS | RIOT-OS/RIOT | 5827 | **LGPL-2.1** | `core/sched.c` 极简调度、`sys/` 抽象层 | [第 3 章](../v0-foundations/03-struct-abi-registers.md) 对照 |
| 存储 | littlefs-project/littlefs | 6980 | BSD-3-Clause | `lfs.c` 元数据对与 CTZ 跳表、磨损均衡 | [v1 第 17 章](../v1-drivers/17-flash-iap-ota.md)、[第 30 章](../v4-platforms/30-esp32s3-architecture-boot.md) |
| 存储 | pellepl/spiffs | 1632 | MIT | `spiffs_nucleus.c` GC 触发与页状态机 | [v1 第 17 章](../v1-drivers/17-flash-iap-ota.md) 另一种取舍 |
| 网络 | lwip-tcpip/lwip（镜像，上游在 savannah） | 1765 | BSD-3-Clause（SICS 版） | `src/core/pbuf.c` 零拷贝链、`tcp_in.c` 状态机 | [第 33 章](../v4-platforms/33-network-protocol-stack.md) |
| 网络 | apache/mynewt-nimble | 895 | Apache-2.0 | `nimble/host/src/ble_gap.c` 连接状态机 | [第 32 章](../v4-platforms/32-esp32-wifi-ble-espnow.md) |
| 网络 | hathach/tinyusb | 7238 | MIT | `src/device/usbd.c` 端点与描述符装配 | [第 35 章](../v4-platforms/35-can-usb-fieldbus.md) |
| 图形 | lvgl/lvgl | 25010 | MIT | `src/core/lv_obj.c` 对象树、`src/draw/sw/` 脏矩形 | [第 31 章](../v4-platforms/31-esp32-drivers-audio.md) 数据面/控制面同构 |
| 测试 | ThrowTheSwitch/Unity | 5432 | MIT | `src/unity.c` 断言宏与失败信息 | [第 4 章](../v0-foundations/04-function-pointer-state-machine.md)、与本书 probe.sh 手写断言互为对照（本书未引入它） |
| 测试 | ThrowTheSwitch/CMock | 846 | MIT | `src/cmock.c` mock 生成与调用序断言 | [第 13 章](../v1-drivers/13-uart-framed-protocol.md) |
| SDK | raspberrypi/pico-sdk | 5004 | BSD-3-Clause | `src/rp2_common/`：寄存器→高层 API 的分层 | [第 5 章](../v0-foundations/05-toolchain-four-steps.md) 库层对照 |

![手绘板：选一条车道读到底——选树、读文件、冻 SHA、写引用（原理示意，非实拍）](/images/app-f-lane.png)

![开源证据层地图：先问要哪一份 .h/函数，再谈星标](/figures/sample-f-oss-map.svg)

![手绘板：星标多不等于该读（原理示意，非实拍）](/images/app-f-stars.png)

## 二、九个知识点：只有读源码才拿得到

读陌生仓库先问三个问题：**谁在什么时候调用谁**、**数据在内存里长什么样**、**我猜错时会看到什么现象**。九条分两组：跨厂商六条（两书交集取并集）与 ESP-IDF 专三条。

### 跨厂商

1. **RT-Thread 的初始化是「按书脊编号上架」**。`INIT_EXPORT(fn, "level")` 把函数指针塞进以字符串命名的链接段，链接时按段名字典序排序，启动时从段首扫到段尾——`"0" < "0.end" < "0.post" < "1"`。把六个 `INIT_*_EXPORT` 当成「编号 1~6 的闸门」就会误判设备注册与调度器启动的先后（`bsp/tm4c129x/board.c` 用 `"0.post"` 插队）。自己验：`nm 固件 | grep rti_fn`。
2. **厂商 SDK 的许可是「配料表」，不是一锅汤**。`STM32CubeF4/LICENSE.md` 本身是表格：HAL/BSP/FatFS/LwIP/Utilities/basic Examples=BSD-3-Clause；CMSIS/mbedTLS=Apache-2.0；USB 库/STemWin/TouchGFX/STM32_Audio=SLA0044（ST 专有）；LibJPEG=IJG。「Cube 是 BSD」只对 HAL/BSP 成立——链接了 USB 库或 TouchGFX，义务就换了一套。
3. **「归档」与「只读镜像」是两码事**。`openocd-org/openocd` 描述写 "Read-Only Mirror (no pull requests)"——仓库活着但不收 PR；`CMSIS_5` 与 `blackmagic` 的 `archived=true`——只读不再受理，CMSIS 后续在 CMSIS_6。自己验：看描述有无 mirror/no-pull-requests，看页头归档横条。
4. **CMSIS 的 `__I/__O/__IO` 是「用类型表达读写权限」**：`__I`=`volatile const`、`__O`=`volatile`、`__IO`=`volatile`（`core_cm4.h`）。同文件 `__NVIC_SetPriority()` 的 `priority << (8 - __NVIC_PRIO_BITS)`——优先级左移是因为寄存器高 4 位有效（F407 是 4）。
5. **libopencm3 的「手册翻译」是单个头文件**：`stm32/f4/memorymap.h`（7755 B）放基址宏，同目录 `gpio.h`/`rcc.h` 是函数声明——没有一个 `memorymap/` 目录。读法：先 memorymap 拿基址，再看 `common/*.h` 拿位定义，最后看 `lib/stm32/common/*.c` 用法。
6. **FreeRTOS 的上下文切换在 port 层，不在 `tasks.c`**：`portable/GCC/ARM_CM4F/port.c`（41,783 B）里 `xPortPendSVHandler` 保存 r4-r11、写回 PSP、调 `vTaskSwitchContext()` 再恢复。「任务切换耗时」按 port 的汇编算，不按 `tasks.c` 算；换内核版本 port 没变开销基本不变，换芯片（M3→M4F）要重算 FPU 上下文。

### ESP-IDF 专

7. **`esp_err_t` 就是 `int`，错误码是「身份证号」**：低段 `0x101~0x10D` 通用错误、负数只有 `ESP_FAIL -1`；高段按模块划分（WIFI 0x3000、MESH 0x4000、FLASH 0x6000、HW_CRYPTO 0xc000）。串口打印 `0x6001` 先按段号定位 Flash 层——它说「擦除/写入没成」，不是参数错。
8. **`ESP_ERROR_CHECK` 在发布构建里是拆掉的报警器**：`NDEBUG` 下只剩 `(void) sizeof(err_rc_);`——表达式照求值（副作用保留），结果丢掉不判错。这是有意为之；发布版兜底自己写 `if (err != ESP_OK) {...}`。
9. **错误码字符串表是「链接期钉上布告栏」**：组件调 `idf_define_esp_err_codes()` 登记错误码，构建系统生成 `.esp_err_msg_tbl` 段。自己 `#define` 了新码没登记，`esp_err_to_name()` 返回 UNKNOWN——不是函数 bug，是便签没交给管理员。

![六个源码知识点：星标数替代不了这六条证据](/figures/sample-f-six-facts.svg)

![手绘板：九条源码知识点（原理示意，非实拍）](/images/app-f-six-facts.png)

## 三、许可边界：能不能链进你的固件

「许可」列不是装饰，它决定代码能不能拿进产品：

| 许可族 | 能静态链进闭源固件吗 | 义务 | 地图里的例子 |
| --- | --- | --- | --- |
| MIT / BSD-3-Clause | 可以 | 保留版权与许可声明 | FreeRTOS-Kernel、littlefs、lwIP、LVGL、TinyUSB、Unity、CMock、pico-sdk |
| Apache-2.0 | 可以 | 同上 + 保留 `NOTICE`、显著标注改动 | Zephyr、RT-Thread、NuttX、ESP-IDF、pyOCD |
| LGPL-2.1 | **静态链接需谨慎** | 允许动态链接/独立进程；静态链入闭源固件通常要提供目标文件或源码 | RIOT |
| GPL 家族 | **不可以** | 工具链/调试器类随工具分发；不要并进固件 | OpenOCD、grbl、riscv-gnu-toolchain |
| 厂商 SLA / 多组件 | 逐组件看 | STM32CubeF4 是「每目录一许可」，USB/STemWin/TouchGFX 走 SLA0044 | STM32CubeF4 |

两条纪律：**下单看 `LICENSE` 原文，不看 README 徽章**；**多组件仓库（Cube、IDF）按目录逐个核**。本书的 47 个工程全部自写，不复制上述项目的代码。

![手绘板：证据口径——手册优先、源码第二、社区第三、实验收口（原理示意，非实拍）](/images/app-f-evidence.png)

## 四、提问之前先做五件事

1. **读 issue 模板**——模板问什么，就是维护者最缺什么；跳过模板的 issue 通常第一个被关。
2. **把复现压到最小**——能贴 20 行就别贴 200 行；删到现象消失的前一步。
3. **版本三件套**——芯片订货号、SDK/内核 commit（或 tag）、工具链版本。缺一个，回答只能靠猜。
4. **给证据不给形容词**——「不工作」没有信息量；日志、`nm`/`objdump` 片段、示波器截图、寄存器转储有。
5. **先搜再开**——重复 issue 是最快被忽略的方式；用报错原文搜，不用你理解的转述。

![提问前五件事清单](/figures/sample-f-ask-before.svg)

![手绘板：提问前五件事——README、冻 commit、最小复现、原文日志、已排除路径（原理示意，非实拍）](/images/app-f-ask-before.png)

## 五、复刻清单（两书并集，一周一个）

| 仓库 | 读哪一处 | 练到的手艺 |
| --- | --- | --- |
| libopencm3 | `stm32/f4/memorymap.h` + `common/gpio_common.h` | 寄存器文档化 |
| STM32CubeF4 | `Drivers/STM32F4xx_HAL_Driver/Src/*_hal_gpio.c` | 库怎么封装寄存器 |
| FreeRTOS-Kernel | `portable/GCC/ARM_CM4F/port.c` | 上下文切换的最小集 |
| grbl（GPL-3.0） | `stepper.c` | 中断里只做最少事；**读可以，抄进闭源固件不行** |
| RT-Thread | `src/object.c` | 用 C 做继承 |
| pyOCD | `pyocd/core/` | 把协议写成 API |
| micropython | `ports/*/mpconfigport.h` | 移植层的边界 |

## 六、证据口径

- 星标数、`archived` 字段、仓库描述：GitHub API，**2026-10-26**；30 个仓库同日逐一复核，两书 23 个交集逐仓一致。
- 许可：仓库根 `LICENSE`/`COPYING`/`LICENSE.md` 原文；STM32CubeF4 按其 `LICENSE.md` 逐组件表引用。
- 代码路径与函数：当日默认分支命中；版本漂移后先 `git log -1` 确认分支。
- 本附录不引用任何未在上述来源中出现的事实；仓库改名或归档，以当前状态为准。

## 七、学习路线收束

这一节把七卷收成一条可以继续走的路。下面的数字都是已发布各章给出的账，收在这里方便对照实测。

### 七卷各留下什么证据

| 卷 | 读完时应能拿出 |
| --- | --- |
| 卷 0 语言与构建 | 可解释的 ELF：段归属、链接脚本与四步构建的证据 |
| 卷 1 裸机驱动 | 一只脚的真实电平、一帧 UART/一帧总线报文、一次 DMA 缓冲归属的记录 |
| 卷 2 可靠性与故障 | 看门狗/低功耗/故障时的状态记录，而不是只在演示路径通过 |
| 卷 3 RTOS | 一张有主人、截止时间和恢复证据的任务图，而不只是换了个内核名字 |
| 卷 4 多平台与连接 | 换系列/双核/网络时的差异对账与分层排错记录 |
| 卷 5 运动控制 | 电机链路的冻结参数、理论账与待执行实验清单 |
| 卷 6–7 实验与交付 | 一份交付包与四问验收栏，分清手册、例程和社区说法 |

### 第一块板先记四行（BluePill）

| 要写下来的 | 期望 | 你要填的实测 |
| --- | --- | --- |
| 容量 | 读 `0x1FFFF7E0`，正品 C8 为 64 KB；DevID `0x410` | 读数，以及与丝印是否一致 |
| 时钟 | HSE 8 MHz ×9 = 72 MHz；APB1 36 MHz；TIM2–TIM7 按 72 MHz；Flash 等待 2 | `HAL_RCC_GetPCLK1Freq()` + 一次 PWM 周期 |
| 一帧串口 | USART1、115200、8N1、BRR `0x271`；一位约 8.68 µs、一帧约 86.8 µs | 逻辑分析仪上的位宽 |
| 一条失败边界 | IWDG：预分频 64、Reload 624 才是按 40 kHz 算的 1 秒；LSI 30–60 kHz，秒数不是保证值 | 故意不喂狗时的复位旗与秒表 |

### 换芯片时再写三行

| 要写下来的 | 期望 | 你要填的实测 |
| --- | --- | --- |
| G0 启动锁存 | 第四个 SYSCLK 上升沿锁存；PA14 兼启动输入与 SWCLK；`BOOT_LOCK=1` 且 RDP L1 时调试停住 | 采样窗口里 PA14 的电平；调试器能否连上 |
| L4 醒来时钟 | Stop 2 临时时钟 MSI/HSI16；封面 1.1 µA、带 RTC 1.4 µA、唤醒 4 µs 是芯片典型值 | 醒后第一帧位宽；拔调试器和 LED 后的电流 |
| H7 硅片与 VOS | Rev Y/W 停在 VOS1/400 MHz；Rev V 经 VOS1 就绪再进 VOS0 到 480 MHz；MCO2÷5 期望 80/96 MHz | `REV_ID`、两次 `VOSRDY`、MCO 仪器读数 |

### 推荐阅读顺序

- **主路径（第一次通读）**：按目录顺序 ch01 → ch46，每章章首的「先备知识」只引用前面的概念。
- **加速路径（已有工具链经验）**：ch01 → ch02 → ch03 → ch05 → ch06 → ch10 → ch21 → ch20 → 按目标平台选卷 4 章 → ch27；缺测量证据时退回主路径对应章，不用仿真冒充实板。
- **专题插入**：维护 SPL 旧工程→[v1 第 7 章](../v0-foundations/07-build-systems-legacy.md)；板级对线→[第 40 章](../v6-labs-projects/40-lab-method-instruments.md)；症状排错→[第 45 章](../v7-delivery/45-troubleshooting-handbook.md)（任意章失败时按症状入口跳转）。

### 怎样算这本书读完

1. 工具链能在你自己的板上重做一遍，而不是只在截图里成功。
2. 至少一个结论同时写着期望值、实测值和测量条件。
3. 这个结论能指回文档号或冻结的代码版本——指不回去的数字，先不要写进设计。

### 下一步怎么选

- 还在打通最小闭环：回 [卷 0–1](../v0-foundations/01-c-memory-model.md)，把点灯、中断和 PWM 做成可测量的记录。
- 数据要进出单片机：[卷 1 驱动](../v1-drivers/13-uart-framed-protocol.md) 加 [附录 A](./A-engineering-deep-read.md)，把缓冲区和帧边界写清楚。
- 设备要在掉电、升级或低功耗后还在：[第 17、18 章](../v1-drivers/17-flash-iap-ota.md)，把失败路径和唤醒后的时钟写成表。
- 要上网：[第 33 章](../v4-platforms/33-network-protocol-stack.md)，链路、地址、传输、应用分开证明。
- 要选 RTOS：[第 27 章](../v3-rtos/27-rtos-comparison-selection.md)；先有栈、队列和中断优先级预算，再比较内核名字。

术语回查用 [附录 D](./D-glossary.md)；什么算数、什么只是线索，用 [附录 E](./E-sources-version-license.md)。

### 先不要做的事

- 不要把 F1 的寄存器地址抄到 G0、L4 或 H7。
- 不要把 F103 的 1 KB 页、预分频 9 或 BRR `0x271` 抄到时钟不同的系列上。
- 不要把仿真通过当成板级电气已经正确。
- 不要把社区文章里的参数当成手册。
- 不要把中文页里的一句叙述，当成英文版里已经核对过的寄存器事实。

收束之后如果只做一件事：选一个你要交付的行为，写下它的期望、测量和下一次会失败的边界。

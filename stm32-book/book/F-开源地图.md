# 开源项目与社区地图

这本书的每条结论都要求能回查到手册、源码或实测。开源仓库属于[附录 E](#appendix-references)的第三层来源。它不用申请许可、不用签保密协议，`git clone` 之后就能看见厂商和社区各自怎么实现同一件事。

仓库地图里的星标与归档状态取 2026-10-26 的 GitHub API 返回值，许可取仓库根 `LICENSE` 原文。

星标多只说明用的人多。该不该读，只看仓库里有没有你要找的那个 `.h` 或那个函数。

## 仓库地图

| 章 | 仓库 | 星标 | 许可 | 先读什么 |
|---|---|---|---|---|
| 01 环境 | platformio/platformio-core | 9564 | 见 `LICENSE` | `platformio/builder/`：谁决定 `-mcpu` 与链接脚本 |
| 03 GPIO | STMicroelectronics/STM32CubeF4 | 1361 | HAL/BSP/Projects = BSD-3-Clause；CMSIS/mbedTLS = Apache-2.0；USB/STemWin/TouchGFX = SLA0044 | `Drivers/STM32F4xx_HAL_Driver/Src/` 任一外设的 `Init` |
| 03 GPIO | libopencm3/libopencm3 | 3671 | 见 `COPYING` | `include/libopencm3/stm32/f4/memorymap.h`：把手册翻成宏 |
| 04 NVIC | ARM-software/CMSIS_6 | 483 | Apache-2.0 | `CMSIS/Core/Include/core_cm4.h`：`__I/__O/__IO` 与 NVIC 内联函数 |
| 04 NVIC | STMicroelectronics/cmsis-device-f4 | 161 | Apache-2.0（Cube 许可表逐组件标注） | `Include/stm32f407xx.h`：寄存器结构体与位域 |
| 12 Flash/IAP | openocd-org/openocd | 2365 | GPL-2.0（见 `COPYING`） | `src/flash/nor/stm32f2x.c`：Flash 算法怎么写 |
| 12 Flash/IAP | littlefs-project/littlefs | 6980 | BSD-3-Clause | `lfs.c` 元数据对与磨损均衡 |
| 12 Flash/IAP | pellepl/spiffs | 1632 | MIT | `spiffs_nucleus.c` 的 GC 触发与页状态机 |
| 15 FreeRTOS | FreeRTOS/FreeRTOS-Kernel | 4609 | MIT | `tasks.c` 就绪表；`portable/GCC/ARM_CM4F/port.c` 的 PendSV 切换 |
| 19 项目 | grbl/grbl | 6309 | GPL-3.0（见 `COPYING`） | `stepper.c`：中断里只做「发一个脉冲 + 记账」 |
| 19 项目 | hathach/tinyusb | 7238 | MIT | `src/device/usbd.c` 端点与描述符装配 |
| 19 项目 | lvgl/lvgl | 25010 | MIT | `src/core/lv_obj.c` 对象树、`src/draw/sw/` 脏矩形 |
| 20 工具链 | pyocd/pyOCD | 1473 | 见 `LICENSE` | `pyocd/core/` 的 target 抽象：调试协议怎么变成 API |
| 20 工具链 | blackmagic-debug/blackmagic | 3719 | 见 `COPYING` | **已归档**（`archived: true`），仅作阅读 |
| 20 工具链 | micropython/micropython | 22154 | 见 `LICENSE` | `ports/*/mpconfigport.h`：移植层要暴露什么 |
| 26 SPL | stm32duino/Arduino_Core_STM32 | 3375 | 见 `LICENSE` | `system/Drivers/` 与 `cores/arduino/` 的边界 |
| 27 网络 | lwip-tcpip/lwip（GitHub 镜像，上游在 savannah） | 1765 | BSD-3-Clause（SICS 版） | `src/core/pbuf.c` 零拷贝链、`tcp_in.c` 状态机 |
| 27 网络 | apache/mynewt-nimble | 895 | Apache-2.0 | `nimble/host/src/ble_gap.c` 连接状态机 |
| 28 RTOS 生态 | RT-Thread/rt-thread | 12309 | Apache-2.0 | `src/object.c` 对象容器、`src/components.c` 初始化档位 |
| 28 RTOS 生态 | zephyrproject-rtos/zephyr | 16906 | 见 `LICENSE` | `include/zephyr/device.h`：设备树的运行期投影 |
| 28 RTOS 生态 | apache/nuttx | 4087 | Apache-2.0 | `sched/` 任务模型、`drivers/` 分层注册 |
| 28 RTOS 生态 | RIOT-OS/RIOT | 5827 | LGPL-2.1 | `core/sched.c` 极简调度、`sys/` 抽象层 |
| 28 RTOS 生态 | espressif/esp-idf | 19347 | Apache-2.0 | `components/esp_common/include/esp_err.h` |

## 从仓库里读到的六个细节

### 1. Cube 的许可逐个组件不同

**原理**：整包 SDK 里每个组件有自己的许可条款。

**机制**：`STM32CubeF4/LICENSE.md` 本身就是表格：STM32F4 HAL、全部 BSP、FatFS、LwIP、Utilities、basic Examples = BSD-3-Clause；CMSIS、CMSIS Device、mbedTLS = Apache-2.0；USB 库、STemWin、TouchGFX、STM32_Audio = SLA0044（ST 专有）；LibJPEG = Independent JPEG Group License。

**踩坑现场**：「Cube 是 BSD」只对 HAL/BSP 成立。产品里链接了 USB 库或 TouchGFX，义务就换了一套；按 BSD 去理解 SLA0044，会在合规审查时返工。

### 2. CMSIS 的 `__I/__O/__IO` 用类型标出读写权限

**原理**：三个宏都是类型限定。`volatile` 让编译器保留每一次寄存器访问，`const` 让编译器拦住对只读寄存器的写。

**机制**：`CMSIS/Core/Include/core_cm4.h` 里三行定义：`__I` = `volatile const`（只读）、`__O` = `volatile`（只写）、`__IO` = `volatile`（读写）。寄存器结构体里每个成员都带这三者之一，所以对 `GPIOA->ODR` 的读和写都不会被优化掉。三者里只有 `__I` 带 `const`：写 `__I` 成员会编译报错，读 `__O` 成员照样能编译，「只写」只是标注。

同文件里的 `__NVIC_SetPriority()` 说明了优先级为什么要左移：写进 `IPR` 的值是 `priority << (8 - __NVIC_PRIO_BITS)`，因为每个优先级字节只有高 `__NVIC_PRIO_BITS` 位有效。`__NVIC_PRIO_BITS` 由芯片头文件给出，F407 是 4，所以传入的 0..15 落在字节的高 4 位。

### 3. libopencm3 的外设基址在一个头文件里

**原理**：它把参考手册里存储器映射一节逐条写成 `#define`，可以当作一份能编译的手册摘要来读。

**机制**：`include/libopencm3/stm32/f4/memorymap.h`（7755 B）里是每个外设的基址宏；同目录的 `gpio.h`、`rcc.h` 只有几百到几千字节，是函数声明。仓库里没有 `memorymap/` 目录，它是一个文件。

**读法**：先看 `memorymap.h` 拿到基址，再看 `common/*.h` 拿到位定义，最后看 `lib/stm32/common/*.c` 看用法。

### 4. FreeRTOS 的上下文切换在 port 层，不在 `tasks.c`

**原理**：内核只决定下一个运行哪个任务，搬寄存器的是和芯片相关的 port 层。

**机制**：`portable/GCC/ARM_CM4F/port.c`（41,783 B）里，`xPortPendSVHandler` 保存 `r4-r11` 到当前任务的栈、把 PSP 写回 TCB、调用 `vTaskSwitchContext()` 选出下一个 `pxCurrentTCB`，再从新 TCB 恢复。所以算任务切换耗时，要把 port 里的汇编和 `vTaskSwitchContext()` 一起算。

**推论**：换芯片（M3 → M4F）时 port 跟着换，切换开销要重算，M4F 还多一层 FPU 上下文。

### 5. RT-Thread 的初始化顺序由段名决定

**原理**：初始化顺序只看链接段的名字，和源文件编译、链接的先后无关。

**机制**：`INIT_EXPORT(fn, "level")` 把函数指针塞进以字符串命名的链接段；链接时按段名字典序拼成连续数组，启动时从段首扫到段尾逐个调用。`src/components.c` 里写着 `INIT_EXPORT(rti_start, "0")`、`INIT_EXPORT(rti_board_start, "0.end")`；`bsp/tm4c129x/applications/board.c` 为了让 `rt_hw_cpu_init` 跑在板级初始化之前，用的是 `"0.post"`。

**踩坑现场**：把六个 `INIT_*_EXPORT` 当成「第 1～6 档」，就会误判设备注册与调度器启动的先后。档位是字符串，`"0" < "0.end" < "0.post" < "1"`。

### 6. 「归档」与「只读镜像」是两码事

**原理**：归档的仓库不再接受任何变更；只读镜像还在同步，只是变更要交到上游。

**机制**：`openocd-org/openocd` 的描述写着 "Official OpenOCD Read-Only Mirror (no pull requests)"——仓库活着，但 GitHub 这侧不收 PR。`ARM-software/CMSIS_5` 与 `blackmagic-debug/blackmagic` 的 `archived` 为 `true`：只读、不再受理变更；CMSIS 的后续在 CMSIS_6。

**踩坑现场**：在镜像上开的 PR 不会被处理，补丁要交到上游；归档仓库不会再出新版本。

## 社区：提问之前先做五件事

1. **读 issue 模板**。模板问的就是维护者排查时要的信息。
2. **把复现压到最小**。能贴 20 行就别贴 200 行；能删的初始化全删掉，直到现象消失的前一步。
3. **版本三件套**：芯片订货号、Cube 固件包/内核 tag、编译器版本。缺一个，回答只能靠猜。
4. **给证据不给形容词**。「不工作」没有信息量；`nm`/`objdump` 片段、串口日志、示波器截图、寄存器转储有。
5. **先搜再开**。重复的 issue 一般会被标为重复后关掉。

## 复刻清单：六个小工程

| 仓库 | 读哪一处 | 练到的手艺 |
|---|---|---|
| libopencm3 | `stm32/f4/memorymap.h` + `common/gpio_common.h` | 寄存器文档化 |
| STM32CubeF4 | `Drivers/STM32F4xx_HAL_Driver/Src/*_hal_gpio.c` | 库怎么封装寄存器 |
| FreeRTOS-Kernel | `portable/GCC/ARM_CM4F/port.c` | 上下文切换的最小集 |
| grbl（GPL-3.0） | `stepper.c` | 中断里只做最少事；**读可以，抄进闭源固件不行** |
| RT-Thread | `src/object.c` | 用 C 做继承 |
| pyOCD | `pyocd/core/` | 把协议写成 API |

## 证据口径

- 星标数、`archived` 字段：GitHub API，2026-10-26。
- 许可：仓库根 `LICENSE`/`COPYING`/`LICENSE.md` 原文；STM32CubeF4 按其逐组件表引用。
- 代码路径：当日默认分支的 GitHub 代码检索命中；版本漂移后路径可能变化，读之前先 `git log -1`。
- 本附录不引用任何未在上述来源中出现的事实。

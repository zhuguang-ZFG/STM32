# 开源项目与社区地图：30 个仓库、6 个知识点、1 套提问纪律

本书的每条结论都要求"能指到文件行"。开源仓库是最便宜的一手证据来源：不用许可、不用保密协议，`git clone` 之后就能看见厂商和社区各自怎么实现同一件事。本附录给三样东西——一张按篇章组织的仓库地图、六个只有读源码才拿得到的知识点、以及社区提问的最小纪律。

星标数与活跃度取 2026-10-26 的 GitHub API 返回值；许可取自各仓库根目录的 `LICENSE`；知识点的文件路径按当日默认分支。**星标多是"人多"，不是"该读"**——该不该读只看一条：仓库里有没有你要找的那个 `.h` 或那个函数。

## 仓库地图

| 篇 | 仓库 | 星标 | 许可 | 先读什么 | 对应章节 |
|---|---|---|---|---|---|
| C | ARM-software/CMSIS_6 | 483 | Apache-2.0（见仓库 `LICENSE`） | `CMSIS/Core/Include/core_cm4.h` 里内联函数与屏障宏 | [C3 volatile](/c/03-volatile.md) · [S4 NVIC](/stm32/04-nvic-exti.md) |
| C | STMicroelectronics/cmsis-device-f4 | 161 | Apache-2.0（Cube 许可表逐组件标注） | `Include/stm32f407xx.h`：寄存器结构体与位域定义 | [S3 GPIO](/stm32/03-gpio.md) · [S15 SPL](/stm32/15-spl-anatomy.md) |
| 构建 | platformio/platformio-core | 9564 | 见仓库 `LICENSE` | `platformio/builder/`：谁决定 `-mcpu` 与链接脚本 | [B7 构建系统](/build/07-build-system.md) |
| 构建 | riscv-collab/riscv-gnu-toolchain | 4651 | GPL 家族（见仓库 `LICENSE`） | `Makefile.in` 的 `--with-arch`/`--with-abi` 缺省值 | [V0 RISC-V 工具链](/gd32/05-riscv-toolchain.md) |
| STM32 | STMicroelectronics/STM32CubeF4 | 1361 | HAL/BSP/Projects = BSD-3-Clause；CMSIS/mbedTLS = Apache-2.0；USB/STemWin/TouchGFX = SLA0044 | `Drivers/STM32F4xx_HAL_Driver/Src/` 里任一外设的 `Init` | [S15 SPL 解剖](/stm32/15-spl-anatomy.md) |
| STM32 | libopencm3/libopencm3 | 3671 | 见仓库 `COPYING` | `include/libopencm3/stm32/f4/memorymap.h`：把手册翻成宏 | [S3 GPIO](/stm32/03-gpio.md) |
| STM32 | stm32duino/Arduino_Core_STM32 | 3375 | 见仓库 `LICENSE` | `system/Drivers/` 与 `cores/arduino/` 的边界 | [C4 结构体与 ABI](/c/04-struct-abi.md) |
| RTOS | RT-Thread/rt-thread | 12309 | Apache-2.0 | `src/object.c` 对象容器、`src/components.c` 初始化档位 | [R1 线程与调度](/rtos/rtthread/01-thread-sched.md) |
| RTOS | FreeRTOS/FreeRTOS-Kernel | 4609 | MIT（官方许可页） | `tasks.c` 就绪表与切换、`portable/GCC/ARM_CM4F/` | [F3 调度器](/rtos/freertos/03-scheduler.md) |
| RTOS | zephyrproject-rtos/zephyr | 16906 | Apache-2.0（`LICENSE` 正文） | `include/zephyr/device.h`：设备树的运行期投影 | [F0 为什么需要 RTOS](/rtos/freertos/00-why-rtos.md) |
| ESP32 | espressif/esp-idf | 19347 | Apache-2.0（`esp_err.h` 的 SPDX 头可证） | `components/esp_common/include/esp_err.h` | [P4 中断与双核](/esp32/04-irq-dualcore.md) · [P10 NVS 与 OTA](/esp32/10-flash-nvs-ota.md) |
| ESP32 | espressif/arduino-esp32 | 17629 | 见仓库 `LICENSE` | `cores/esp32/esp32-hal-*.c`：Arduino API 怎么落到 IDF | [P5 UART 驱动](/esp32/05-uart-driver.md) |
| GD32 | CommunityGD32Cores/gd32-pio-spl-package | 10 | 见仓库 `LICENSE` | GD32 SPL 的重打包规则 | [G0 环境](/gd32/00-env.md) |
| 调试 | openocd-org/openocd | 2365 | GPL-2.0（见 `COPYING`） | `src/flash/nor/stm32f2x.c`：Flash 算法怎么写 | [B6 Flash 与调试](/build/06-flash-debug.md) |
| 调试 | pyocd/pyOCD | 1473 | Apache-2.0（`LICENSE` 正文） | `pyocd/core/` 的 target 抽象：调试协议怎么变成 API | [B6 Flash 与调试](/build/06-flash-debug.md) |
| 调试 | blackmagic-debug/blackmagic | 3719 | 见仓库 `COPYING` | **已归档**（`archived: true`），仅作阅读 | [S16 HardFault](/stm32/16-debug-hardfault.md) |
| 运行时 | micropython/micropython | 22154 | 见仓库 `LICENSE` | `ports/*/mpconfigport.h`：移植层要暴露什么 | [C6 调用约定](/c/06-abi-stack.md) |
| 运行时 | rust-embedded/cortex-m | 1010 | MIT / Apache-2.0 双许可 | `src/peripheral/` 与 `asm.rs`：裸机抽象的另一条路 | [C1 内存模型](/c/01-memory-model.md) |
| 控制器 | grbl/grbl | 6309 | 见仓库 `COPYING` | `grbl/stepper.c`：中断里只做最少事 | [S6 定时器](/stm32/06-tim.md) |
| RTOS | apache/nuttx | 4087 | Apache-2.0（`LICENSE` 正文） | `sched/` 任务模型、`drivers/` 分层注册 | [F3 调度](/rtos/freertos/03-scheduler.md) 对照 |
| RTOS | RIOT-OS/RIOT | 5827 | **LGPL-2.1**（`LICENSE` 正文） | `core/sched.c` 极简调度、`sys/` 抽象层 | [C6 调用约定](/c/06-abi-stack.md) 对照 |
| 存储 | littlefs-project/littlefs | 6980 | BSD-3-Clause（`LICENSE.md`） | `lfs.c` 元数据对与 CTZ 跳表、`lfs_alloc` 磨损均衡 | [S13 Flash IAP](/stm32/13-flash-iap.md) · [P10 NVS](/esp32/10-flash-nvs-ota.md) |
| 存储 | pellepl/spiffs | 1632 | MIT（`LICENSE`） | `spiffs_nucleus.c` GC 触发与页状态机 | [S13](/stm32/13-flash-iap.md) 另一种取舍 |
| 网络 | lwip-tcpip/lwip（GitHub 镜像，上游在 savannah） | 1765 | BSD-3-Clause（`COPYING`，SICS 版） | `src/core/pbuf.c` 零拷贝链、`src/core/tcp_in.c` 状态机 | [P8 Wi-Fi](/esp32/08-wifi.md) |
| 网络 | apache/mynewt-nimble | 895 | Apache-2.0（`LICENSE` 正文） | `nimble/host/src/ble_gap.c` 连接状态机 | [P9 蓝牙](/esp32/09-bt-espnow.md) |
| 网络 | hathach/tinyusb | 7238 | MIT（`LICENSE`） | `src/device/usbd.c` 端点与描述符装配、`src/class/cdc/` | [G4 外设差异](/gd32/04-periph-diff.md) |
| 图形 | lvgl/lvgl | 25010 | MIT（`LICENCE.txt`） | `src/core/lv_obj.c` 对象树、`src/draw/sw/` 脏矩形 | [P12 音频](/esp32/12-audio-path.md) 数据面/控制面同构 |
| 测试 | ThrowTheSwitch/Unity | 5432 | MIT（`LICENSE.txt`） | `src/unity.c` 断言宏与失败信息 | [C5](/c/05-func-pointer.md) · 与本书 probe.sh 的手写断言互为对照（我们未引入它） |
| 测试 | ThrowTheSwitch/CMock | 846 | MIT（`LICENSE.txt`） | `src/cmock.c` mock 生成与调用序断言 | [C8 协议](/c/08-framed-protocol.md) |
| SDK | raspberrypi/pico-sdk | 5004 | BSD-3-Clause（`LICENSE.TXT`） | `src/rp2_common/`：寄存器→高层 API 的分层 | [B0 工具链](/build/00-toolchain.md) 库层对照 |

## 六个知识点：只有读源码才拿得到

读一个陌生仓库，先问三个问题：**谁在什么时候调用谁**、**数据在内存里长什么样**、**我猜错时会看到什么现象**。下面六条都是这三问的答案——每条都给出机制、踩坑现场和一行可验证的办法。

### 1. RT-Thread 的初始化是"按书脊编号上架"，不是"按你搬来的顺序"

**原理（一句话）**：链接器是图书管理员，它只认书脊上的编号做排序，不认你把书搬进馆的先后。

**机制**：`INIT_EXPORT(fn, "level")` 把函数指针塞进一个以字符串命名的链接段（`.rti_fn.<level>`）。链接时同名前缀的段被拼成一段连续数组，**按段名做字典序排序**；启动时 `rt_components_init()` 从段首走到段尾，挨个调用。于是 `"0" < "0.end" < "0.post" < "1" < "1.end" …`——`src/components.c` 里 `INIT_EXPORT(rti_start, "0")`、`INIT_EXPORT(rti_board_start, "0.end")` 就是这条传送带的两个端点。

**踩坑现场**：把 `INIT_BOARD_EXPORT / INIT_PREV_EXPORT / INIT_DEVICE_EXPORT / …` 当成"六道闸门、编号 1～6"，于是断定"设备一定在板级之后初始化"。实际上档位是一串可插值的字符串。`bsp/tm4c129x/applications/board.c` 的注释写得很白：为了让 `rt_hw_cpu_init` 跑在所有 `INIT_BOARD_EXPORT` 之前，作者用的是 `INIT_EXPORT(rt_hw_cpu_init, "0.post")`——不改宏，只改字符串，就插了队。

**自己验**：`nm 固件 | grep rti_fn` 看段名排序；或在两个相邻档位之间插一句打印，看它落在谁前面。这一条也解释了 [R1](/rtos/rtthread/01-thread-sched.md) 里"设备注册早于调度器启动"的真正原因：不是规定，是排序。

### 2. `esp_err_t` 就是 `int`，错误码是"身份证号"，前几位是省份

**原理（一句话）**：错误码不是枚举，是一套分段的编号规则——看段号就知道该找哪个部门。

**机制**：`components/esp_common/include/esp_err.h` 第一句是 `typedef int esp_err_t;`，返回值就是普通整数。编号分两截：低段 `0x101`～`0x10D` 是通用错误（`ESP_ERR_INVALID_ARG 0x102`、`ESP_ERR_TIMEOUT 0x107`、`ESP_ERR_INVALID_CRC 0x109`），负数只有 `ESP_FAIL -1`。高段按模块划分：`ESP_ERR_WIFI_BASE 0x3000`、`MESH 0x4000`、`FLASH 0x6000`、`HW_CRYPTO 0xc000`、`MEMPROT 0xd000`。

**踩坑现场**：串口打印 `0x6001`，你去查"哪个参数传错了"——查了半天没有。0x6000 段属于 Flash 层：它在说"擦除/写入没成"，可能压根没走到参数校验。

**自己验**：排障时同时打印 `esp_err_to_name(err)` 和十进制值；拿到 `0x` 开头的高位，先按段号定位模块，再进那个模块找。

### 3. `ESP_ERROR_CHECK` 在发布构建里是拆掉的报警器

**原理（一句话）**：烟雾报警器只在装修时通电，正式营业时断电——标语还挂在墙上。

**机制**：同一个宏有三个分支。正常构建：失败就走 `_esp_error_check_failed()`，打印文件、行号、表达式并停机。`CONFIG_COMPILER_OPTIMIZATION_ASSERTIONS_SILENT`：只 `abort()`，不打印。`#ifdef NDEBUG`：只有一句 `(void) sizeof(err_rc_);`——**表达式照求值一次（副作用保留），结果直接丢掉，不判错**。

**为什么这么设计**：发布固件要省 flash、省串口日志；断言被当作开发期工具。这是有意为之，不是 bug。

**踩坑现场**：单元测试全绿，现场却"明明返回了错误还继续往下跑"，故障点漂到几百行之外。你以为是驱动吞了错误，其实是这个宏根本没检查。

**自己验**：`gcc -E` 展开看一眼，或确认构建有没有定义 `NDEBUG`。要在发布版留下兜底，就自己写 `if (err != ESP_OK) { … }`。

### 4. 错误码的字符串表是"链接期钉上布告栏"，不是运行期查字典

**原理（一句话）**：`esp_err_to_name()` 不是翻字典，是去看墙上那张布告——布告在你的代码编译之前就钉好了。

**机制**：组件在自己 `CMakeLists.txt` 里调 `idf_define_esp_err_codes()` 登记错误码，构建系统从头文件里抽取编号与名字，生成一张放进 `.esp_err_msg_tbl` 链接段的表；运行期函数在这张表里查。

**踩坑现场**：自己加了个 `MY_ERR_BASE + 3`，调用 `esp_err_to_name()` 得到 `"UNKNOWN ERROR"`，于是怀疑函数有 bug。其实是你只写了 `#define`，没在组件里登记——**便签没交给管理员，墙上当然没有**。

**自己验**：新增错误码后跑一次 `esp_err_to_name()`；返回 UNKNOWN 就回去补登记，而不是查函数。

### 5. 厂商 SDK 的许可是"配料表"，不是一锅汤

**原理（一句话）**：整包 SDK 不是一锅炖好的汤，是一张配料表——每样配料有自己的保质条款。

**机制**：`STM32CubeF4/LICENSE.md` 本身就是一张表：STM32F4 HAL、全部 BSP、FatFS、LwIP、Utilities、basic Examples = BSD-3-Clause；CMSIS、CMSIS Device、mbedTLS = Apache-2.0；STM32_USB_Device_Library、USB_Host、STemWin、TouchGFX、STM32_Audio = SLA0044（ST 专有条款）；LibJPEG = Independent JPEG Group License。

**踩坑现场**："Cube 是 BSD 许可"——这句话只对 HAL 与 BSP 成立。产品里链接了 USB 库或 TouchGFX，义务就换了一套；按 BSD 去理解 SLA0044，会在合规审查时返工。

**自己验**：选中间件之前先翻这张表，把要用的每个目录对上它那一行。

### 6. GitHub 上的"归档"与"只读镜像"是两码事

**原理（一句话）**：一个是"门牌还挂着，屋里没人"，一个是"这屋放的是影印件，原件在别处"。

**机制**：`openocd-org/openocd` 的描述写着 "Official OpenOCD Read-Only Mirror (no pull requests)"——仓库本身活着，但 GitHub 这侧不收 PR，补丁要走上游。`ARM-software/CMSIS_5` 与 `blackmagic-debug/blackmagic` 的 `archived` 字段为 `true`：只读、不再受理变更；CMSIS 的后续在 CMSIS_6，Black Magic 的后续在别的分支/仓库。

**踩坑现场**：在镜像上开 PR，等一个月没人回；在归档仓库等新版本，等到的只有"已停止维护"。

**自己验**：看描述里有没有 `mirror` / `no pull requests`，看页头有没有归档横条——两个信号，三秒判断。

## 许可边界：能不能链进你的固件

仓库地图里那列"许可"不是装饰——它决定你能不能把代码拿进产品：

| 许可族 | 能静态链进闭源固件吗 | 义务 | 地图里的例子 |
|---|---|---|---|
| MIT / BSD-3-Clause | 可以 | 保留版权与许可声明 | FreeRTOS-Kernel、littlefs、lwIP、LVGL、TinyUSB、Unity、CMock、pico-sdk |
| Apache-2.0 | 可以 | 同上 + 保留 `NOTICE`、显著标注改动 | Zephyr、RT-Thread、NuttX、ESP-IDF、pyOCD |
| LGPL-2.1 | **静态链接需谨慎** | 允许动态链接/独立进程；静态链入闭源固件通常要提供目标文件或源码 | RIOT |
| GPL 家族（GPL-2.0/3.0） | **不可以** | 工具链/调试器类随工具分发；不要并进固件 | OpenOCD、grbl、riscv-gnu-toolchain |
| 厂商 SLA / 多组件 | 逐组件看 | STM32CubeF4 是"每目录一许可"，USB/STemWin/TouchGFX 走 SLA0044 | STM32CubeF4 |

两条纪律：**下单看 `LICENSE` 原文，不看 README 的徽章**；**多组件仓库（Cube、IDF）按目录逐个核**——
同一仓库里 BSD-3、Apache-2.0 与 SLA 可以并存。本书的 47 个工程全部自写，不复制上述项目的代码。

## 社区：提问之前先做五件事

1. **读 issue 模板**。模板问什么，就是维护者最缺什么；跳过模板的 issue 通常第一个被关。
2. **把复现压到最小**。能贴 20 行就别贴 200 行；能删掉的初始化全部删掉，直到现象消失的前一步。
3. **版本三件套**：芯片型号（含后缀）、SDK/内核版本（commit 或 tag）、工具链版本。缺一个，回答只能靠猜。
4. **给证据不给形容词**。"不工作"没有信息量；串口日志、`nm`/`objdump` 片段、示波器截图、`idf.py monitor` 的寄存器转储有。
5. **先搜再开**。重复 issue 是最快被忽略的方式；搜的时候用报错原文，不要用你理解的转述。

## 复刻清单：六个能一周啃完的小工程

| 仓库 | 规模锚点 | 读哪一处 | 练到的手艺 |
|---|---|---|---|
| grbl/grbl（GPL-3.0） | `stepper.c` 一个文件 | 中断服务里只做"发一个脉冲 + 记账" | 实时路径的最小化；GPL 系：**读可以，抄进闭源固件不行** |
| libopencm3/libopencm3 | `stm32/f4/memorymap.h` 与同目录外设头 | 把参考手册的一节翻成 `#define` | 寄存器文档化 |
| RT-Thread/rt-thread | `src/object.c` | `rt_object_init()` 与类型强转 | 用 C 做继承 |
| FreeRTOS/FreeRTOS-Kernel | `tasks.c` + `portable/GCC/ARM_CM4F/` | `vTaskSwitchContext()` 前后 | 就绪表与上下文切换 |
| pyocd/pyOCD | `pyocd/core/` | target 抽象层的接口设计 | 把协议写成 API |
| micropython/micropython | `ports/*/mpconfigport.h` | 一个最小 port 暴露了哪些宏 | 移植层的边界 |

## 证据口径

- 星标数、`archived` 字段、仓库描述：GitHub API，2026-10-26；表中 30 个仓库同日逐一复核。
- 许可：仓库根 `LICENSE`/`COPYING`/`LICENSE.md` 原文；STM32CubeF4 按其 `LICENSE.md` 的逐组件表引用。
- 代码路径与函数：当日默认分支的 GitHub 代码检索命中；版本漂移后路径可能变化，读之前先 `git log -1` 确认分支。
- 本附录不引用任何未在上述来源中出现的事实；仓库若改名或归档，以仓库当前状态为准。

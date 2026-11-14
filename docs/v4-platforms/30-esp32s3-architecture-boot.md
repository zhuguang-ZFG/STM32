---
title: "ESP32-S3 架构、启动与工程"
platforms: [esp32]
---

# ESP32-S3 架构、启动与工程

ESP32-S3 上电之后发生的事，是三棒接力：ROM 交给 bootloader，bootloader 交给 app，app 里 FreeRTOS 先起、main task 再调你写的 `app_main`。与 STM32「复位向量直接进 app」的世界观比，多了两级接力，也多了两处最容易卡住的位置——日志前缀（`rst:`/`boot:`/`app_start:`）就是分诊单。工程侧，ESP-IDF 把「构建」换成「组件化 + Kconfig 菜单」：CMake 是引擎，`idf.py` 是调度员。这一章把两件事拆到源码行。

证据先说清：本章零板级实测。上游核对以 **ESP-IDF v5.5.2** 实取（`soc_caps.h:145`、`app_startup.c:83,158,206-210`、`esp_system/Kconfig:225-227`、`partitions_singleapp.csv`、`project.cmake:21,29,464-465`、`component.cmake:443-449`、`kconfig.cmake:208-216` 全部逐字命中）；启动 banner 的具体日志属「待上板回填」；IRAM/DIRAM size 账可复算但原始读数是来源说法（未复核）；「890 个 CONFIG_」因 `sdkconfig` 是构建产物未入库，同样是来源说法。立创实战派 S3 的板卡细节（WROOM-1-N16R8、CH340K）来自立创 wiki，逐项标注待核。

> 版本口径：ESP-IDF **v5.5.2**（`esp_idf_version.h:14-18` tag 5/5/2）；板卡立创实战派 S3（ESP32-S3-WROOM-1-N16R8：16 MB Flash + 8 MB PSRAM，LX7 双核 240 MHz）。引用行号只写 v5.5.2 实取命中的；换版本按 E4 的提醒重核。

## 本章罗盘

- **问题**：三棒接力各做什么，卡在哪一棒看哪段日志？`app_main` 为什么不是 main——main task 的优先级、栈、亲和各是多少，`TASK_EXTRA_STACK_SIZE` 这层加项为什么不能漏？XIP 与 Cache 映射怎么改变了「代码在哪」的世界观，IRAM 纪律从哪来？分区表四列怎么读，Offset 为什么留空？组件化三板斧（SRCS/INCLUDE_DIRS/REQUIRES）与依赖图怎么走，main 为什么是「自动收集的项目组件」？manifest 管来源/版本、`REQUIRES` 管构建可见性，这两层怎么接进同一张图？Kconfig 三段论的三个产物各是什么，`CONFIG_IDF_TARGET_ESP32S3` 闭环怎么走一遍？`idf.py` 各子命令各查哪一层？错目标的 sdkconfig 为什么会静默编错芯片？
- **交付**：能用日志前缀完成三棒分诊；能说出 main task 三参数的默认值（优先级 1、栈 3584 起、默认 CPU0）并指出栈定义里还有一层加项；能对照 F407 把 XIP 的架构差讲清；能读默认分区表（nvs 0x6000/phy_init 0x1000/factory 1M）并解释 gen_esp32part 的排布；能写一个组件的 `idf_component_register` 并画出依赖图；能区分本地 `components/`、`EXTRA_COMPONENT_DIRS` 与管理组件，并说出同名组件的优先级；能走 `CONFIG_IDF_TARGET_ESP32S3` 从菜单到宏的闭环（`hello_main.c:25` 实例）；能按「配置/组件声明/编译/烧录」分层定位构建问题。
- **边界**：本章讲架构与工程，不重教 FreeRTOS 机制（[第 22 章](../v3-rtos/22-tasks-tcb-scheduler.md)、[第 23 章](../v3-rtos/23-context-switch-porting.md)）与双 OS 选型（[第 27 章](../v3-rtos/27-rtos-comparison-selection.md) 已定「IDF 自带 FreeRTOS、S3 双核 SMP」口径）；外设驱动与音频归[第 31 章](./31-esp32-drivers-audio.md)，Wi-Fi/BLE/ESP-NOW 归[第 32 章](./32-esp32-wifi-ble-espnow.md)，OTA 的分区双槽细节留到 ch31/ch32 引用处。`sdkconfig` 数值类证据（size 账、890 项）全部标「来源说法(未复核)」。
- **依据锚点**：E0《环境》（`mcu/docs/esp32/00-env.md`）、E1《架构与启动》（`.../01-arch-boot.md`）、E3《IDF 解剖》（`.../03-idf-anatomy.md`）。上游对账：ESP-IDF v5.5.2 的 [soc_caps.h](https://github.com/espressif/esp-idf/blob/v5.5.2/components/soc/esp32s3/include/soc/soc_caps.h)、[app_startup.c](https://github.com/espressif/esp-idf/blob/v5.5.2/components/freertos/app_startup.c)、[startup.c](https://github.com/espressif/esp-idf/blob/v5.5.2/components/esp_system/startup.c)、[esp_task.h](https://github.com/espressif/esp-idf/blob/v5.5.2/components/esp_system/include/esp_task.h)、[esp_system/Kconfig](https://github.com/espressif/esp-idf/blob/v5.5.2/components/esp_system/Kconfig)、[project.cmake](https://github.com/espressif/esp-idf/blob/v5.5.2/tools/cmake/project.cmake)、[component.cmake](https://github.com/espressif/esp-idf/blob/v5.5.2/tools/cmake/component.cmake)、[kconfig.cmake](https://github.com/espressif/esp-idf/blob/v5.5.2/tools/cmake/kconfig.cmake)、[partitions_singleapp.csv](https://github.com/espressif/esp-idf/blob/v5.5.2/components/partition_table/partitions_singleapp.csv)。仓库实例：`mcu/code/esp32/00-hello`（CMakeLists 目标守卫、`hello_main.c:25` 的 `CONFIG_IDF_TARGET_ESP32S3` 实读命中）。

## 先做出来

### 1. 用日志前缀做一次三棒分诊

上电串口的输出不是一团字，是三段接力，每段有前缀：

| 前缀 | 谁在说话 | 卡点判据 |
| --- | --- | --- |
| `rst:` | ROM（第一棒） | `rst:` 都没有 → 供电/晶振/串口接线问题 |
| `boot:` | 二级 bootloader（第二棒） | `boot:` 后停 → 分区表/镜像校验问题 |
| `app_start:` 之后 | app（第三棒） | 进 app 后崩 → sdkconfig 目标/任务栈/组件问题 |

（具体 banner 文本属「待上板回填」——机制成立，字样要按你手上的板回填。）三棒各自的职责：ROM 按 strapping 选启动介质；bootloader 初始化 Flash/Cache、读分区表、选 app 并校验（上游主线落在 `bootloader_start.c:62` 的 `bootloader_utility_load_boot_image`）；app 里 `esp_startup_start_app`（`startup.c:222`）创建 main task、`vTaskStartScheduler`。

![ESP32-S3 启动三棒接力动画：ROM → bootloader → app，每棒一条卡点判据](/anim/esp32-boot-relay.svg)

![手绘板：三棒接力与分诊口诀——rst: 归 ROM、boot: 归引导、app_start: 之后才怪软件；XIP 是最容易踩的架构差（原理示意）](/images/mc30-s3-boot-chain.png)

### 2. 一条三行的 CMakeLists 与一个目标守卫

仓库实例 `mcu/code/esp32/00-hello/CMakeLists.txt` 的三行正文加一条守卫：

```cmake
cmake_minimum_required(VERSION 3.16)
include($ENV{IDF_PATH}/tools/cmake/project.cmake)   # include 链起于 project.cmake:21(targets) / :29(idf)
project(hello)
```

`project.cmake` 的 include 链（`:21` targets.cmake → `:29` idf.cmake）把「目标芯片」的定义接进来。守卫写法：

```cmake
if(NOT IDF_TARGET STREQUAL "esp32s3")
    message(FATAL_ERROR "本工程只支持 ESP32-S3")
endif()
```

为什么值这条命：换目标编译时，残留的旧 `sdkconfig` 会**静默**带着上一颗芯片的配置走——编出来的固件烧进新芯片不跑，也没有显式报错。守卫把这类事故挡在配置层。

## 机制

### 一、`app_main` 的真实身份

「main 函数」在 ESP-IDF 里是三层：`esp_startup_start_app` 创建 main task → 调度器启动 → main task 内调用你的 `app_main`。上游行号链（v5.5.2 实取）：

```text
startup.c:222          esp_startup_start_app();
app_startup.c:83       xTaskCreatePinnedToCore(main_task, ...)   ← main task 在这创建
app_startup.c:158      static void main_task(...)
app_startup.c:206-210  "Calling app_main()" → app_main(); → vTaskDelete(NULL);
startup.c:224          ESP_INFINITE_LOOP();                       ← 调度器之后的闲置循环
```

三个默认值（`esp_task.h:56-58` + `esp_system/Kconfig:225-227,233-235`）：

| 参数 | 默认 | 来源 |
| --- | --- | --- |
| 优先级 `ESP_TASK_MAIN_PRIO` | `ESP_TASK_PRIO_MIN + 1` = **1**（倒数第二低） | `esp_task.h:28,56` |
| 栈 `ESP_TASK_MAIN_STACK` | `CONFIG_ESP_MAIN_TASK_STACK_SIZE + TASK_EXTRA_STACK_SIZE`，CONFIG 默认 **3584** → 栈 3584 起 | `esp_task.h:57` + `Kconfig:225-227` |
| 亲和 `ESP_TASK_MAIN_CORE` | 默认 **CPU0**（choice `ESP_MAIN_TASK_AFFINITY`） | `Kconfig:233-235` |

两个易错点：栈定义里**还有一层加项**——`ESP_TASK_MAIN_STACK = CONFIG_ESP_MAIN_TASK_STACK_SIZE + TASK_EXTRA_STACK_SIZE`，只写「= CONFIG」就漏了加项；「8KB 默认栈」是错的（上游 default 3584），写成「3584 起」带上加项语义才准确。`app_main` 返回即 `vTaskDelete(NULL)` 删掉 main task——它是一次调用，不是常驻循环；要常驻就自己在里面写循环。

### 二、XIP：代码住在 Flash 里

STM32F407 的 Flash 是「原地执行」（XIP）——代码在片内 Flash 上直接取指。ESP32-S3 不同：app 的代码与 rodata 在**外部** Flash，经 Cache 映射窗口执行；写 Flash 期间要关 Cache，此时 Flash 里的 ISR **不可取指**。这就是 IRAM 纪律的由来：写 Flash 的临界区内，被调用的代码必须住在 IRAM（`ESP_IRAM_ATTR`）。这是两平台最本质的架构差，也解释了为什么 IDF 有一整类「IRAM 安全」API。size 账的形态（`.text 15356 + .vectors 1028 = 16384`，该段 100% 用满；DIRAM 55463/341760=16.23%）是文档推导可复算，原始读数标来源说法（未复核，`probe.sh` 存在但无落盘日志）。

### 三、分区表：数据化的 MEMORY

分区表把外部 Flash 切成带名字的区，是 OTA 的地基。默认单 app 表（`partitions_singleapp.csv` 逐字符核对）：

```text
# Name,   Type, SubType, Offset,  Size
nvs,      data, nvs,     0x9000,  0x6000
phy_init, data, phy,     0xf000,  0x1000
factory,  app,  factory, 0x10000, 1M
```

三件事：**Offset 留空**由 `gen_esp32part.py` 按类型对齐——data 0x1000、app 0x10000（工具回读用 `idf.py partition-table`）；`nvs` 存 Wi-Fi/BT 键值与每台设备的 PHY 校准数据；`phy_init` 存 PHY 初始化参数，默认编进 app，只有开 `CONFIG_ESP_PHY_INIT_DATA_IN_PARTITION` 才从该分区读（[第 32 章](./32-esp32-wifi-ble-espnow.md) 会回到这）；双 OTA 槽 = factory 换成 ota_0/ota_1 两个 app 区加一个 otadata。

`bootloader` 在 0x0、表在 0x8000；这两项不在 CSV 里，分别取 `BOOTLOADER_OFFSET_IN_FLASH` 与 `PARTITION_TABLE_OFFSET` 的默认值（`components/bootloader/Kconfig.projbuild`、`components/partition_table/Kconfig.projbuild`，v5.5.2）。

![ESP32-S3 默认单 app 分区表：bootloader 0x0、表 0x8000、nvs 0x9000、phy_init 0xF000、factory 0x10000；OTA 双槽另加 ota_0/ota_1 与 otadata](/arch/esp32-partition-map.png)

### 四、组件化三板斧与「main 是自动收集的项目组件」

每个组件一份 CMakeLists，注册函数是 `idf_component_register`（`component.cmake:443-449` 实取）：

```cmake
idf_component_register(
    SRCS "sensor.c"            # 源文件清单
    INCLUDE_DIRS "include"     # 对外头文件路径
    REQUIRES driver log)       # 依赖的其他组件
```

`REQUIRES` 画依赖图，构建系统按拓扑收组件。**main 不是普通组件，是「项目组件」**——构建系统自动把工程根下的 `main/` 目录收进来，落点在 `project.cmake:464-465`（`__project_component_dir("${CMAKE_CURRENT_LIST_DIR}/main" ...)`）。旧材料把这条写成 `tools/cmake/build.cmake:465`——行号 465 恰好存在但文件错了，`build.cmake` 里没有该行；引用一律写 `project.cmake:465`。

### 4.1 组件管理器：依赖来源与版本解析

`idf_component.yml` 管依赖来源与版本解析：registry、git、本地 `path` 都可以；解析结果进入同一张组件图，registry/git 组件通常落在 `managed_components/`。`REQUIRES`/`PRIV_REQUIRES` 管构建期依赖与头文件可见性，manifest 的 `require: public/private` 分别对应这两个 CMake 参数——两层不是互斥。`dependencies.lock` 记录解析版本，自动生成；没有 yml 就不会生成。[官方 Build System 文档](https://docs.espressif.com/projects/esp-idf/en/v5.5.2/esp32s3/api-guides/build-system.html)给的同名组件搜索优先级从高到低：`components/` → `EXTRA_COMPONENT_DIRS` → `managed_components/` → `$IDF_PATH/components`。要改下载的组件，先复制到 `components/` 再改。

![ESP-IDF 工程解剖：工程源 → 组件图 → app.bin；下方是同名组件的搜索优先级](/arch/idf-anatomy.png)

### 五、Kconfig 三段论：菜单 → sdkconfig → 三个产物

1. **菜单**：每个组件的 `Kconfig` 文件拼成菜单树（menuconfig 操作）。
2. **选择**：用户的选择写进 **`sdkconfig`** 文本文件（这是唯一该提交的配置文件——`sdkconfig.defaults` 只存「与默认不同的项」，全量配置是构建产物）。
3. **产物**：构建时 `kconfig.cmake:208-216` 生成三份：`sdkconfig.h`（C 宏，`:208`）、`sdkconfig.cmake`（`:214`）、`sdkconfig.json`（`:215`）——头文件里有 `DO NOT EDIT` 警告，手改必被覆盖。

闭环走一遍（`hello_main.c:25` 实读命中）：

```c
#ifdef CONFIG_IDF_TARGET_ESP32S3
    ... "S3" ...
#endif
```

菜单里选 ESP32-S3 → `sdkconfig` 出现 `CONFIG_IDF_TARGET_ESP32S3=y` → `sdkconfig.h` 生成该宏 → C 代码按宏走分支。`CONFIG_IDF_TARGET_*` 系列宏就是「目标守卫」在代码层的形态，与 CMakeLists 的 `IDF_TARGET` 守卫是同一件事的两层。

### 六、idf.py：调度员的分层定位法

`idf.py` 本身不编译，它调度四层工具：`build` → CMake + 构建器；`flash` → esptool；`menuconfig` → Kconfig 前端；`monitor` → 串口终端（默认波特率 115200，`esp_system/Kconfig:411-416` 实取）。分层定位法：配置错查 `sdkconfig`/menuconfig；组件关系错查各 `CMakeLists` 的 REQUIRES；编译错查源码与头文件路径；烧录失败查 esptool 的串口与进 boot 模式的 strapping 状态。

### 七、双核默认分工：回链一句话

`SOC_CPU_CORES_NUM=2`（`soc_caps.h:145` 实取）；IDF 自带 FreeRTOS 是 SMP 单实例，PRO_CPU/APP_CPU 只是**默认分工**（main task 默认钉 CPU0），任务可用 `xTaskCreatePinnedToCore` 自选核。SMP 的语义边界与「AMP≠SMP」的对照已在 [第 27 章](../v3-rtos/27-rtos-comparison-selection.md) 定过口径，本章不重新论证。

## 测量与证据

| 结论 | 身份 | 判据 |
| --- | --- | --- |
| 双核 `SOC_CPU_CORES_NUM=2` | 手册级（上游已核） | `soc_caps.h@v5.5.2:145` |
| main task 三参数默认值 | 手册级（上游已核） | `esp_task.h:28,56-58` + `Kconfig:225-227,233-235` |
| 三棒接力与选镜像主线 | 手册级（上游已核） | `bootloader_start.c:62`、`startup.c:222,224` |
| 默认分区表 | 手册级（上游已核） | `partitions_singleapp.csv` 逐字符一致 |
| main 组件收集行 `project.cmake:465` | 手册级（上游已核，**修正旧材料 build.cmake 错位**） | `project.cmake:464-465` |
| 组件管理器目录与锁 | 手册级（官方 Build System 已核） | `managed_components/`、`idf_component.yml`、`dependencies.lock` |
| 同名组件搜索优先级 | 手册级（官方 Build System 已核） | `components/` → `EXTRA_COMPONENT_DIRS` → `managed_components/` → `$IDF_PATH/components` |
| Kconfig 三产物区间 | 手册级（上游已核） | `kconfig.cmake:208-216` |
| IRAM/DIRAM size 账 | 文档推导 + 来源说法(未复核) | 加法与百分比可复算；原始读数无落盘日志 |
| 启动 banner 字样 | 未实测（待上板回填） | 机制成立，字样按实板回填 |
| 「890 个 CONFIG_」 | 来源说法(未复核) | `sdkconfig` 未入库，无法复跑 |
| 板卡 WROOM-1-N16R8/CH340K | 来源说法待核 | 立创 wiki，逐项标注 |

待做实验：`idf.py partition-table` 回读对照默认表；把 `CONFIG_ESP_MAIN_TASK_STACK_SIZE` 调小观察栈溢出报错；`idf.py --help` 子命令与分层表逐条核。

## 失败分支

| 症状 | 第一条假设 | 区分实验 |
| --- | --- | --- |
| 串口无任何输出 | 第一棒就没起来 | 量供电/晶振；换 USB 线；CH340 驱动 |
| `boot:` 后停住 | 分区表损坏或镜像校验失败 | `idf.py partition-table` 回读；重烧 factory |
| 进 app 即崩 | 错目标 sdkconfig 静默编错芯片 | 看 `sdkconfig` 头部 `IDF_TARGET`；开 CMakeLists 守卫 |
| `app_main` 栈溢出 | 只按 3584 算，漏了或误解加项 | 读 `esp_task.h:57` 的完整定义；调 CONFIG 加缓冲 |
| 写 Flash 时死机 | Flash 写期间调了非 IRAM 安全的 ISR | IRAM 纪律：临界区内只调 `ESP_IRAM_ATTR` 函数 |
| 改了宏不生效 | 手改了 `sdkconfig.h`（生成物） | 改 menuconfig 或 `sdkconfig.defaults`，重跑构建 |

## 离开检查

- 三棒分诊口诀能默写，并给每棒一条卡点判据。
- `app_main` 的三层身份与 main task 三参数（1 / 3584 起 / CPU0）说得清，栈定义里的加项不漏。
- XIP 与 F407 原地执行的架构差能对照讲，IRAM 纪律的由来一句话到位。
- 默认分区表能画，Offset 留空的排布逻辑说得清。
- `project.cmake:465` 与组件化三板斧能落到一段能编译的 CMakeLists。
- Kconfig 三段论的三产物与目标守卫两层（CMake + `CONFIG_IDF_TARGET_*`）都能走通闭环。

---
title: P1 S3 架构与启动：从复位到 app_main
status: done
difficulty: 2
minutes: 35
---

# P1 S3 架构与启动：bootloader→app 的接力赛

> 🎯 STM32 上电是"一条指令到 main"；ESP32-S3 上电是一场三棒接力：**ROM 引导 → 二级 bootloader → 你的 app**。多出来的两棒不是多余：它们换来了分区表、OTA、Flash 加密这些"出厂就是产品级"的能力。

## 本章精髓

1. 双核 LX7 + 内存分级：PRO_CPU/APP_CPU 两个核（`SOC_CPU_CORES_NUM = 2`），外部 Flash 经 **Cache 映射**执行，代码实际从"缓存窗口"跑，这决定了"ISR 要放 IRAM"等一系列铁律（P4 展开）。
2. 三棒启动：ROM（固化，查 strapping 脚决定启动模式）→ 二级 bootloader（初始化 Flash/Cache、读分区表、选 app 并校验）→ app（FreeRTOS 初始化 → 创建 main task → 调你的 `app_main`）。
3. 分区表是"地产证"：bootloader 不烧死 app 地址，而是读分区表（CSV 定义 `factory`/`ota`/`nvs`/`phy` 等）。OTA 双 app 轮换、参数存储全靠这张表。

- **能理解**：为什么你的 `app_main` **不是** `main()`：它跑在一个名叫 `main` 的 FreeRTOS 任务里（`xTaskCreatePinnedToCore(main_task, "main", ...)`）。
- **能用**：从复位到 `app_main` 的每一棒都能指到源码行号；出问题时会判断"卡在哪一棒"（ROM 打印？ bootloader 打印？ app 打印？）。

## 先修

- [P0 环境与工具链](00-env.md)：能跑 `idf.py build` 之后再来。
- [S1 架构与内存](../stm32/01-arch.md)：Flash 映射、向量表（STM32 侧的对照系）。
- [B1 四步构建](../build/01-four-steps.md)：预处理/编译/汇编/链接的视角，看 ESP 侧有何不同。

## 先跑起来（10 分钟 quick win）

```bash
cd code/esp32/00-hello
idf.py build          # 需要 IDF 环境（见 P0）
```

构建日志里找这几行（真实日志见 `.trellis/ref/idf-00-hello.log`）：

```text
Project build complete. To flash, run:
 idf.py flash
```

monitor 起来之前先押一棒：banner 的第一行是谁打的？你写的代码，还是芯片里比你的代码老得多的那位？押完再看串口，第一行当场判分。

然后 `idf.py flash monitor`，串口会打出启动 banner。**banner 里的每一行都对应下面某一棒**，这是本章最实用的调试入口：

| 串口看到什么 | 说明卡在哪一棒 |
|---|---|
| `rst:0x1 (POWERON)` + ROM 信息 | ROM 引导（第一棒）——还没到 bootloader |
| `I (27) boot: ESP-IDF ...` | 二级 bootloader（第二棒）正在跑 |
| `I (xxx) app_start: Starting scheduler` | 内核起来了（第三棒） |
| `I (xxx) app_start: Calling app_main()` | 即将进你的代码 |

ROM 打印完就没了 / 反复重启 / 只有 `waiting for download`：三种现象分别指向三棒的不同故障，第 5 节逐条对照。

## 小节结构

| 小节 | 内容 | 四件套 |
|---|---|---|
| 双核与内存分级 | PRO_CPU/APP_CPU；IRAM/DRAM；Cache 映射执行 | 配置 |
| 第一棒 ROM | 固化引导、strapping 脚、下载模式 | 库解析 |
| 第二棒 bootloader | 初始化 Flash/Cache、读分区表、校验并选 app | 库解析 |
| 第三棒 app | `esp_startup_start_app` → main task → `app_main` | 代码分析 |
| 分区表 | CSV 四列含义、`factory`/`nvs`/`phy` 的真实条目 | 配置 |
| 和 STM32 对照 | 一条直线 vs 三棒接力；启动失败的排查入口 | 配置 |

## 一、双核与内存分级：先说清楚"跑在哪"

ESP32-S3 是**双核**：

```c
#define SOC_CPU_CORES_NUM               2     // soc/esp32s3/include/soc/soc_caps.h:145
```

- **PRO_CPU**（CPU0）：协议核，负责 WiFi/蓝牙协议栈、启动流程。
- **APP_CPU**（CPU1）：应用核，跑你的任务。

这只是**默认分工**，不是硬约束：FreeRTOS 在 S3 上是 **SMP**（对称多处理）单实例，任务默认可以跑在任意核上，也可以用 `xTaskCreatePinnedToCore` 钉死到某个核（P4 展开）。

**内存分级才是关键差异**。S3 的地址空间里，代码可以待在两个地方：

| 位置 | 特点 | 谁在用 |
|---|---|---|
| **IRAM**（内部 SRAM，可执行） | 取指零等待，不受 Cache 影响 | 启动早期代码、被标记 `IRAM_ATTR` 的 ISR |
| **Flash**（外部，经 **Cache 映射**） | 容量大、便宜；Cache 关闭时**不可取指** | 绝大部分应用代码与 rodata |

这就是那条铁律的来源：**普通代码放在 Flash 里，靠 Cache 映射窗口执行**。当系统要写 Flash（NVS 提交、OTA、分区操作）时会**暂时关闭 Cache**，此刻若发生中断，而 ISR 在 Flash 里，CPU 取指无门，直接崩。所以有 IRAM 纪律（P4 正面拆解）。

> STM32 侧没有这个概念：F407 的代码就在 Flash 上原地执行，不需要 Cache 窗口，也不存在"关 Cache 期间不能取指"。这是两平台**最本质的架构差异**。

## 二、第一棒 ROM：芯片里烧死的引导

先把三棒接力画出来：ROM 认路、bootloader 验货、app 开工，串口前缀就是探针。

![ESP32-S3 上电三棒接力动画](/anim/esp32-boot-relay.svg)

ROM 引导是**固化在芯片里**的（不是你能改的代码），上电后第一段执行的就是它。它做三件事：

1. **读 strapping 脚**，决定启动模式。"按住 BOOT 键再复位"能进下载模式，就是因为这一步。
2. 做最早期的基础初始化（时钟、基础外设）。
3. 找到并跳转到**二级 bootloader**。

调试信号：串口第一行 `rst:0x1 (POWERON)` 之类就是 ROM 打印的。**如果连这行都没有**，说明问题比软件更早：供电、晶振、串口接线，或者芯片根本没在跑。

## 三、第二棒 bootloader：验货 + 选货

二级 bootloader 是一段**真实的、可升级的**代码（在 `components/bootloader/` 里）。它的主线在 `components/bootloader/subproject/main/bootloader_start.c`：

```c
    bootloader_utility_load_boot_image(&bs, boot_index);   // bootloader_start.c:62
```

在这行之前，它要完成：

- 初始化 Flash 与 Cache 映射（否则后面的代码根本读不到）；
- **读分区表**，拿到各分区的地址与大小；
- 按顺序选择要启动的 app：先试 `factory`，再试 `ota_0` / `ota_1`，并**校验镜像**（校验失败就回退到另一个）。

调试信号：串口打 `I (xx) boot: ESP-IDF ...` 就是它。常见故障是**校验失败导致回退或重启**，此时日志里会有 `invalid header` / `image verification failed` 之类字样。

> **为什么要两棒而不是一棒**：ROM 是烧死的，不可升级。把"读分区表、校验、回退"这些需要**频繁演进**的逻辑放进可升级的二级 bootloader，芯片出厂后仍能修复启动逻辑、支持新分区方案。这是用两棒换来的灵活性。

## 四、第三棒 app：`app_main` 到底是谁调用的

这是本章最值得记住的一段源码。app 侧的启动主线在 `components/esp_system/startup.c`，末尾是：

```c
    esp_startup_start_app();        // startup.c:222
    ESP_INFINITE_LOOP();
```

而 `esp_startup_start_app` 的实现**不在 `esp_system`，在 `freertos`**，见 `components/freertos/app_startup.c:64`：

```c
void esp_startup_start_app(void)
{
    ...
    esp_crosscore_int_init();                    // 初始化核间中断（CPU0）

    BaseType_t res = xTaskCreatePinnedToCore(main_task, "main",
                                             ESP_TASK_MAIN_STACK, NULL,
                                             ESP_TASK_MAIN_PRIO, NULL, ESP_TASK_MAIN_CORE);
    assert(res == pdTRUE);

    ESP_EARLY_LOGD(APP_START_TAG, "Starting scheduler on CPU0");
    vTaskStartScheduler();                       // 从这里开始，调度器接管
}
```

**关键认识：`app_main` 不是 `main()`。** 它是一个叫 `main` 的 FreeRTOS 任务里的函数调用（`app_startup.c:158-212`）：

```c
static void main_task(void* args)
{
    ESP_LOGI(MAIN_TAG, "Started on CPU%d", (int)xPortGetCoreID());
    ...
    ESP_LOGI(MAIN_TAG, "Calling app_main()");
    extern void app_main(void);
    app_main();                       // ← 你的代码在这里被调用
    ESP_LOGI(MAIN_TAG, "Returned from app_main()");
    vTaskDelete(NULL);                // ← app_main 返回，任务自杀、栈被回收
}
```

这段话信息量很大：

- **`app_main` 返回不致命**，任务会自我删除（`vTaskDelete(NULL)`），栈内存被回收。而 STM32 上 `main()` 返回是未定义行为。
- **`app_main` 跑在哪个核**由 `ESP_TASK_MAIN_CORE` 决定，它来自 `CONFIG_ESP_MAIN_TASK_AFFINITY`（`components/esp_system/Kconfig:233` 附近，**默认 `ESP_MAIN_TASK_AFFINITY_CPU0`**）。
- **它的栈多大**由 `ESP_TASK_MAIN_STACK` 决定 = `CONFIG_ESP_MAIN_TASK_STACK_SIZE`（`components/esp_system/include/esp_task.h:57`）。这个 Kconfig 项的**默认值是 3584**（字节），定义在 `components/esp_system/Kconfig:227`：

```text
    config ESP_MAIN_TASK_STACK_SIZE
        int "Main task stack size"
        default 3584
```

- **它的优先级**是 `ESP_TASK_MAIN_PRIO = ESP_TASK_PRIO_MIN + 1`（`esp_task.h:56`），即**倒数第二低**。你的 `app_main` 优先级很低，这解释了"为什么初始化任务常常一创建就抢走 CPU"。

> 顺带：`main` 任务的栈**不像别的任务那样从 heap 切**，它有独立的启动栈（`heap_caps_enable_nonos_stack_heaps()` 那句注释说的就是"启动栈现在可以还给 heap 了"）。

## 五、分区表：bootloader 的"地产证"

bootloader 怎么知道 app 在哪？**不硬编码地址，而是读分区表**。单 app 方案的默认表在 `components/partition_table/partitions_singleapp.csv`：

```csv
# Name,   Type, SubType, Offset,  Size, Flags
nvs,      data, nvs,     ,        0x6000,
phy_init, data, phy,     ,        0x1000,
factory,  app,  factory, ,        1M,
```

四列的含义：

| 列 | 含义 | 例子 |
|---|---|---|
| `Name` | 分区名，代码里用它找分区（`esp_partition_find`） | `nvs` / `factory` |
| `Type` | 大类：`app` 还是 `data` | `app` |
| `SubType` | 子类型：app 有 `factory`/`ota_0`…；data 有 `nvs`/`phy`/`fat`… | `factory` |
| `Size` | 大小；`1M` = 1MB | `0x6000` = 24KB |

**`Offset` 那一列留空**是有意的：留空表示"由工具自动排布"（`gen_esp32part.py` 负责填），避免手写地址撞车。

调试信号：`idf.py partition-table` 能打印出**实际生成**的表（含工具填好的偏移）。**分区表是 OTA 的地基**，双 app 轮换就是往 `ota_0` / `ota_1` 两个分区里交替烧、再改引导指针。

> 对照 STM32：[B3 链接脚本](../build/03-linker-script.md) 里我们是**手写** `MEMORY` 段把 Flash 切成几个区域；ESP32 把这件事**数据化**成了一张可运行时查询的表。代价是必须多一棒 bootloader 来读它。

## 六、和 STM32 对照：一条直线 vs 三棒接力

对照之前先看静态版图：三棒的位置关系与两条依赖（bootloader 读地产证选槽、app_main 寄居 main task），动画演过程，这张图定结构。

![S3 上电三棒静态结构：ROM→bootloader→app，依赖分区表与 main task](/arch/boot-relay.png)

| | STM32（F407） | ESP32-S3 |
|---|---|---|
| 上电第一步 | 复位向量 → `Reset_Handler` | ROM 引导（固化） |
| 中间层 | 无 | 二级 bootloader（可升级） |
| 到 main 的路径 | 启动文件汇编 → `main()` | bootloader → app → FreeRTOS → main task → `app_main()` |
| 代码执行位置 | Flash 原地执行 | Flash 经 Cache 映射（关 Cache 时不可取指） |
| 分区信息 | 链接脚本里写死 | 运行时读分区表 |
| `main` 返回 | 未定义行为 | 任务自杀，栈回收 |

**排查入口**就是本章 quick win 的那张表：**看串口打印停在哪一棒**。这是 ESP32 调试的第一性方法，比 STM32 侧还重要，因为多出来的两棒都在你看到 `app_main` 之前。

## 附录：工程完整源码

**00-hello 的工程描述**（最小 IDF 工程的 `CMakeLists.txt`，P3 会逐行解剖它）：

<<< ../../code/esp32/00-hello/CMakeLists.txt

## 记忆锚点

::: tip 一句话记住
**上电三棒：ROM 认路、bootloader 验货、app 开工；`app_main` 是 main task 里的一次调用，返回就被回收。**
:::

**延伸**：启动接力动画见 [P1 动画](/anim/esp32-boot-relay.svg)；STM32 启动流程对照见 [B4](../build/04-startup.md)；FreeRTOS 任务创建在 [F1](../rtos/freertos/01-task-tcb.md) 展开。

## 实物实验

- `idf.py build` 后 `idf.py flash monitor`，把串口 banner 逐行对照第五节那张"卡在哪一棒"的表（**待上板回填**）。
- `idf.py partition-table` 打印实际分区表，与 `partitions_singleapp.csv` 对照，找出工具自动填上的 `Offset` 值。
- 故意把 `CONFIG_ESP_MAIN_TASK_STACK_SIZE` 改小（如 1024），在 `app_main` 里加一个大数组，观察栈溢出时的报错，这是 F7 那套 RAM 账在 ESP 侧的同一门课。
- 查 `idf.py size` 的输出，看你的代码有多少落在 IRAM、多少在 Flash。本机实测（`code/esp32/09-iram-discipline`，ESP-IDF v5.5.2，目标 esp32s3，`sh probe.sh` 第 7 段可复现）：IRAM `.text` 15356 字节 + `.vectors` 1028 字节（这一行 size 工具按 16384 字节计，显示 100%）；DIRAM 用 55463 / 341760 字节（16.23%）；Flash Code 78770 字节、Flash Data 41324 字节，整镜像 189693 字节。注意这张表的分组是 size 工具自己的口径，链接器真正用的区间要看 `.map` 里的 `Memory Configuration`（同一脚本第 3 段打印：`iram0_0_seg` 起 `0x40374000` 长 `0x57700`）。

## 常见坑

- **以为 `app_main` 就是 `main`**：它跑在一个叫 `main` 的 FreeRTOS 任务里（`app_startup.c:158`），优先级倒数第二低、栈 3584 字节起，这些都能配置，别当固定值。
- **在 `app_main` 返回后还想跑代码**：返回即任务自杀（`vTaskDelete(NULL)`）。要常驻就自己创建任务或写成死循环。
- **把 ISR 随手放 Flash**：Cache 关闭期间不可取指 → 崩。这是 IRAM 纪律的由来（P4 详解）。
- **手写分区偏移**：`Offset` 留空让工具排布；手写容易与 bootloader/NVS 区撞车。
- **忽略启动日志**：ESP32 的启动日志是分层的，`rst:` 来自 ROM、`boot:` 来自 bootloader、`app_start:` 来自 app，**读日志前缀就能定位故障在哪一棒**。

## 短自测

**1. 为什么 ESP32 需要二级 bootloader，STM32 不需要？**

<details>
<summary>看答案</summary>

因为 ROM 里的引导代码是**固化不可升级**的。把"读分区表、校验镜像、OTA 回退"这些需要频繁演进的逻辑放进**可升级**的二级 bootloader，芯片出厂后仍能修复启动逻辑、支持新分区方案。STM32 没有分区表/OTA 这套运行时启动策略，链接脚本写死地址即可，所以启动文件一条直线到 `main()`。

</details>

**2. `app_main()` 是被谁调用的？它返回后会怎样？**

<details>
<summary>看答案</summary>

被 `main_task()` 调用（`components/freertos/app_startup.c:158` 起，调用点在 `app_main();` 那行）。这个任务由 `esp_startup_start_app()` 用 `xTaskCreatePinnedToCore(main_task, "main", ...)` 创建，随后 `vTaskStartScheduler()` 启动调度器。`app_main` 返回后打印 "Returned from app_main()"，然后 `vTaskDelete(NULL)`，**任务自杀、栈被回收**（不像 STM32 的 `main` 返回是未定义行为）。

</details>

**3. 串口只打出 `rst:0x1 (POWERON)` 就没了，问题在哪一棒？**

<details>
<summary>看答案</summary>

**第一棒 ROM 之后就没接上**。`rst:` 是 ROM 打印的，紧接着应该出现 bootloader 的 `I (xx) boot:` 行。没有它说明 ROM 找不到/跳不进二级 bootloader：可能是分区表或 bootloader 镜像损坏、Flash 里还是空白、或芯片在下载模式等待。先确认 `idf.py flash` 真的写进去了。

</details>

**4. `SOC_CPU_CORES_NUM` 是多少？它在哪个文件？**

<details>
<summary>看答案</summary>

**2**。定义在 `components/soc/esp32s3/include/soc/soc_caps.h:145`。这决定了 FreeRTOS 在 S3 上是 SMP 配置（任务可跑任意核），也是 `xTaskCreatePinnedToCore` 有意义的前提。

</details>

**5. 分区表 CSV 里 `Offset` 一列留空是什么意思？**

<details>
<summary>看答案</summary>

表示**由工具自动排布**（`gen_esp32part.py` 根据各分区大小顺序填充），避免手写地址互相撞车。真实表可以用 `idf.py partition-table` 打印出来看填充后的结果。默认单 app 表见 `components/partition_table/partitions_singleapp.csv`。

</details>

## 对照表：本章概念 → 仓库落点

| 概念 | 仓库落点 |
|---|---|
| 双核数量（`SOC_CPU_CORES_NUM = 2`） | `$IDF_PATH/components/soc/esp32s3/include/soc/soc_caps.h:145` |
| app 启动入口 `esp_startup_start_app()` 的调用 | `$IDF_PATH/components/esp_system/startup.c:222` |
| 创建 main task + 启动调度器 | `$IDF_PATH/components/freertos/app_startup.c:64`（`xTaskCreatePinnedToCore` → `vTaskStartScheduler`） |
| `main_task` 本体与 `app_main()` 调用点 | 同上 `:158`（`Calling app_main()` 日志与 `app_main();` 那行） |
| main 任务优先级 / 栈 / 核 | `$IDF_PATH/components/esp_system/include/esp_task.h:56-58` |
| 主任务栈默认 3584 字节 | `$IDF_PATH/components/esp_system/Kconfig:227-234` |
| 二级 bootloader 选镜像 | `$IDF_PATH/components/bootloader/subproject/main/bootloader_start.c:62` |
| 默认分区表 CSV | `$IDF_PATH/components/partition_table/partitions_singleapp.csv` |
| 分区表工具 | `$IDF_PATH/components/partition_table/gen_esp32part.py` |
| 最小 ESP32 工程 | `code/esp32/00-hello/`（`CMakeLists.txt` + `main/`） |
| 真实构建日志 | `.trellis/ref/idf-00-hello.log` |

> 表中 `$IDF_PATH` = `C:/Users/zhugu/.espressif/v5.5.2/esp-idf`（本机 ESP-IDF v5.5.2）。路径与行号以该版本为准，换版本需重核。

## 你做到了

- 上电三棒在你眼里不再是黑箱，每一棒都能指到源码行号；
- 知道 `app_main` 的真实身份，以及它的优先级/栈从哪来；
- 拿到一块出问题的板子，会先看串口日志前缀定位到"哪一棒"，而不是盲目重烧。

你押的那一棒，赢家是 ROM：出厂就焊死在芯片里，改不了删不掉，你的代码再大也轮不到它先开口。三段接力，第一棒不由你写，往后两棒才是你的地盘。

<div class="achievement">
✅ 下一站：<a href="03-idf-anatomy.html">P3 IDF 工程解剖</a>：把那几个 `CMakeLists.txt` 和 `sdkconfig` 拆开看，理解这条流水线怎么把上千个文件编成你刚烧进去的镜像。
</div>

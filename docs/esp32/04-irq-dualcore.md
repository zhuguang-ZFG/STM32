---
title: P4 中断与双核：IRAM 纪律与核间分工
status: done
difficulty: 3
minutes: 40
---

# P4 中断与双核：Cache 关了，你的 ISR 还能跑吗

> 🎯 ESP32 最著名的事故现场：代码在 Flash 里，系统在写 Flash（NVS/OTA 常干）——Cache 一关，取指无门，中断来了直接崩。所以有了铁律：**声明 `ESP_INTR_FLAG_IRAM` 的中断必须保证可达代码/数据均在内部存储；普通非 IRAM-safe 中断在 Flash 操作期间会被推迟**。

## 本章精髓

1. **`IRAM_ATTR` 是生存问题，不是性能问题**。Cache 关闭的那段窗口里，只有 IRAM/ROM 里的代码能取指。所以 ISR 本体、它调用的函数、它用到的 rodata，三样都要排查。
   `esp_intr_alloc` 的 `ESP_INTR_FLAG_IRAM` 标志会强制这个约束。
2. **中断分配器是"总机"**。S3 有 **99 个中断源编号**（实测 `ETS_MAX_INTR_SOURCE = 99`，编号 0–98），经中断矩阵分配到两个核的 **7 级**中断。
   `esp_intr_alloc` 一次把外设源、优先级、所属核三样绑在一起。
3. 双核 SMP 的共享规矩：FreeRTOS 在 S3 上是 SMP 单实例（任务可跑任意核，也可 `xTaskCreatePinnedToCore` 钉核），核间共享数据用自旋锁/`portMUX`，**中断与任务、核与核之间 `volatile` 完全不够**（回 [C3](../c/03-volatile.md) 的边界清单）。

- **能理解**：`IRAM_ATTR` 只是往链接器段里一塞（`".iram1"`），真正保证"能在关 Cache 时跑"的是**整条调用链**都在 IRAM，包括它读的常量。
- **能用**：给外设挂中断时，能正确选 `ESP_INTR_FLAG_LEVELx` 与 `ESP_INTR_FLAG_IRAM`；并知道什么时候必须用 `portMUX`，而不是 `volatile`。

## 先修

- [P1 S3 架构与启动](01-arch-boot.md)：双核、IRAM/DRAM、Cache 映射执行，本章的铁律全是它的推论。
- [C3 volatile](../c/03-volatile.md)：`volatile` 能做什么、不能做什么，本章直接引用其边界清单。
- [S4 中断与 NVIC](../stm32/04-nvic-exti.md)：优先级、向量表、ISR 礼仪，单核侧的对照系。

## 先跑起来（10 分钟 quick win）

挂中断的写法本身（`code/esp32/01-gpio-matrix`）：

```c
/* 写法 A：普通 ISR —— 代码在 Flash 里 */
static void IRAM_ATTR my_isr(void *arg)   /* 先看 B，再把这个 IRAM_ATTR 删掉体会差别 */
{
    BaseType_t hp = pdFALSE;
    xQueueSendFromISR(evt_queue, &tick, &hp);
    portYIELD_FROM_ISR(hp);
}

/* 挂中断：指定优先级 + 是否 IRAM-safe */
esp_intr_alloc(ETS_GPIO_INTR_SOURCE, ESP_INTR_FLAG_LEVEL1 | ESP_INTR_FLAG_IRAM,
               my_isr, NULL, NULL);
```

probe 之前先认个内鬼：四条链里，哪条看着最安全、关 Cache 的窗口一开却第一个跪？先押一个再跑构建，nm 的归类表就是判决书。

**落址不用背，本机链接完直接查。** `code/esp32/09-iram-discipline` 把实践清单的四条链一次摆全：不标的、只标本体的、整条链都标的、代码进了 IRAM 但常量还在 Flash 的。`sh probe.sh` 一条命令跑完构建与取证，最后那段断言逐条打勾、错一条直接非零退出才算数。下面是本机实测（ESP-IDF v5.5.2，目标 esp32s3）：

```console
$ sh probe.sh                # 第 3 段：链接器真正用的区间，出自 .map 的 Memory Configuration
  iram0_0_seg 0x40374000 0x00057700    # 内部 SRAM，可执行，关 Cache 也取得到
  iram0_2_seg 0x42000020 0x007fffe0    # Flash 映射的取指窗口
  drom0_0_seg 0x3c000020 0x01ffffe0    # Flash 映射的常量窗口

$ # 第 4 段：nm 的地址 + 当场按上面三行归类
  0x42008f08  isr_plain    → iram0_2_seg     # 没标 IRAM_ATTR，留在 Flash
  0x42008f1c  helper_far   → iram0_2_seg     # 被 IRAM 里的 ISR 调用，却没标
  0x4037668c  isr_leaky    → iram0_0_seg     # 标了，本体确实在 IRAM
  0x40376698  helper_near  → iram0_0_seg
  0x403766ac  isr_tight    → iram0_0_seg     # 整条链都标
  0x40376668  isr_rodata   → iram0_0_seg
  0x3c028810  k_table      → drom0_0_seg     # 常量还在 Flash

$ # 第 6 段：断链的现场在调用指令的目标地址里，不在段名里
  4037668c <isr_leaky>:
    4037668f:  l32r  a8, 403746a0 <_iram_text_start+0x29c> (42008f1c <helper_far>)
    40376692:  callx8 a8
    40376695:  retw.n
  403766ac <isr_tight>:
    403766af:  call8 40376698 <helper_near>
    403766b2:  retw.n
```

**判据**：`isr_leaky` 的每一条指令都在 IRAM，可它 `callx8` 过去的那个地址落在 Flash 映射段。Cache 一关，`entry` 之后第一条取指就无门。`isr_tight` 的 `call8` 目标还在 IRAM 区间内，这才是真的 IRAM-safe。地址区间一律以 `.map` 里的 `Memory Configuration` 为准。esp32s3 的 IRAM 取指窗口起点是 `0x40374000`，Flash 映射是 `0x42xxxxxx`，常量映射是 `0x3Cxxxxxx`。初代 ESP32 则是 `0x400xxxxx` 一片——两代的数字不能互抄。

还有一个只有实跑才会撞见的坑。这个工程里没有真的外设去 `esp_intr_alloc` 这些 ISR，而 IDF 默认带 `-Wl,--gc-sections`，**没人引用的函数会被整段收掉**。第一版探针工程 `nm` 里只剩 `app_main` 和 `g_hits`，七个符号一个都不剩。现在 `main.c` 里那张 `g_isr_table` 就是为了钉住它们，顺便把这条记下来：你写在磁盘上的 ISR，链接器可能根本没让它进 ELF。

## 小节结构

| 小节 | 内容 | 四件套 |
|---|---|---|
| Cache 与取指 | Flash 映射执行；为什么关 Cache 会"代码消失" | 配置 |
| IRAM 纪律 | `IRAM_ATTR` 的定义；整条调用链与 rodata 的连带责任 | 库解析 |
| 中断分配器 | 99 个源 × 7 级 × 2 核；`esp_intr_alloc` 五参数 | 库解析 |
| 双核分工 | SMP vs 钉核；`xTaskCreatePinnedToCore` 的核参数 | 代码分析 |
| 共享数据规矩 | `portMUX` 自旋锁、队列、通知；`volatile` 的边界 | 配置 |
| 与 NVIC 对照 | 单核向量表 vs 中断矩阵 + 分核 | 配置 |

## 一、Cache 与取指：为什么"代码会消失"

先看这张图：取指的两条路，和 Cache 关闭窗口里一个中断的两种命运。

![IRAM 纪律与 Cache 关闭窗口动画](/anim/iram-discipline.svg)

[P1](01-arch-boot.md) 讲过内存分级，这里把它推到结论。ESP32-S3 上你的应用代码**绝大多数放在外部 Flash 里**，通过 **Cache 映射窗口**执行。这意味着"执行一条 Flash 里的指令"实际上是：

```text
CPU 取指 → Cache 命中？ → 命中：直接返回指令
                        → 未命中：去 Flash 读（慢，但能读）
```

**关键在"Cache 关闭"这个状态**。系统在做这些事时会**暂时禁用 Cache**：

- 写 Flash（NVS 提交、OTA、`esp_partition_write`）；
- 某些低层 Flash 操作与加密操作。

**Cache 一关，映射窗口失效**：此时 CPU 若要从 Flash 取指，**没有任何路径能拿到那条指令**。硬件层面的结果就是异常/崩溃。

**所以问题不是"会不会遇到"，而是"你的哪个 ISR 会在那个窗口里被触发"。** 中断是**异步**的：NVS 正在写 Flash，恰好你的 GPIO 中断来了。如果你在 `esp_intr_alloc` 时**没有**声明 IRAM-safe，系统会让这个中断**推迟**到 Cache 恢复；如果声明了却**没做到**整条链在 IRAM，就是直接崩。

## 二、IRAM 纪律：`IRAM_ATTR` 只是入场券

**定义**（`components/esp_common/include/esp_attr.h:23`）：

```c
#define IRAM_ATTR _SECTION_ATTR_IMPL(".iram1", __COUNTER__)
```

就这么简单：`IRAM_ATTR` 干的事，是**把这段代码放进名为 `.iram1` 的链接段**，再由链接脚本安排到内部 SRAM（可执行区）。它不是"加速"，是"改变落址"。

**但把它加在 ISR 函数上只是第一步**。真正的约束是**整条执行链**都要可达：

| 要排查的东西 | 为什么 |
|---|---|
| ISR 本体 | 显然——它自己要取指 |
| ISR 调用的**所有**函数 | 调用即取指；内联的不算问题，没内联的就是问题 |
| ISR 用到的 **rodata**（字符串常量、查表、`const` 数组） | 数据默认在 Flash 映射区，关 Cache 时读不到 |

**实践清单**（写 IRAM-safe ISR 时逐条过）：

1. ISR 本体标 `IRAM_ATTR`；
2. 它调用的每个非内联函数也标 `IRAM_ATTR`（编译器若内联则免除，但**不要依赖内联**）；
3. 所有 `const` 查表/字符串也标 `IRAM_ATTR`（或放进 DRAM）；
4. **不要**在里面调 `printf`、`malloc`、任何可能碰 Flash 的 API；
5. 需要跨 ISR/任务传数据 → 用 `...FromISR` API（它们本身就是 IRAM-safe 的）。

**`ESP_INTR_FLAG_IRAM` 是声明侧的开关**（`components/esp_hw_support/include/esp_intr_alloc.h:42`）。

```c
#define ESP_INTR_FLAG_IRAM          (1<<10) ///< ISR can be called if cache is disabled
```

它的语义是**承诺**：我保证这个 ISR 在 Cache 关闭时也能跑。系统的回应是：**那就不推迟它**，Cache 关着也照样调用。所以：

- **不标 `ESP_INTR_FLAG_IRAM`**：系统会在 Flash 操作期间**推迟**该中断（安全，但有延迟）；
- **标了 `ESP_INTR_FLAG_IRAM`**：系统不推迟（低延迟），但**你承诺的必须是真的**：链条上任何一环在 Flash 里，就是崩。

> 这是本章最值得记住的**权责对等**：低延迟不是免费的，你用自己的正确性给它做担保。

## 三、中断分配器："总机"上的 99 条线

![中断分配器：99 条线分到 CPU0/CPU1](/figures/esp32-04-int-alloc.svg)

STM32 上中断和向量是**一一对应**的（[S4](../stm32/04-nvic-exti.md)：`EXTI0_IRQn = 6` → 固定向量槽 22），定向量槽）。ESP32-S3 是**中断矩阵**：外设的中断源可以**路由**到某个核的某个中断级。

**规模**（实测 `components/soc/esp32s3/include/soc/interrupts.h`，`sh probe.sh` 第 1 段让编译器把整张枚举打出来）：

- 枚举体在第 18–117 行，从 `ETS_WIFI_MAC_INTR_SOURCE = 0` 排到 `ETS_DMA_EXTMEM_REJECT_SOURCE = 98`；随后第 118 行是 `ETS_MAX_INTR_SOURCE`，编译器打印它的值是 **99**，注释写着 "number of interrupt sources"。
- **99 是编号槽位的数量（0–98），不是"有 99 个不同的名字"**。这张表里 98 个名字只覆盖 95 个不同编号：23、33、34、46 是保留位没有名字，57/58/59 各被两个名字占用（`ETS_SYSTIMER_TARGETn_EDGE_INTR_SOURCE = ETS_SYSTIMER_TARGETn_INTR_SOURCE`）。MER_TARGETn_INTR_SOURCE`，三条 EDGE 是同值别名）。
- 所以按源编号路由时，`ETS_MAX_INTR_SOURCE` 才是数组边界的正确写法（`esp_isr_names[ETS_MAX_INTR_SOURCE]` 就是这么声明的）。别拿"行数"当数量。

**中断级**（`components/esp_hw_support/include/esp_intr_alloc.h:33-43`）：

| 标志 | 值 | 含义 |
|---|---|---|
| `ESP_INTR_FLAG_LEVEL1` | `1<<1` | 最低优先级的中断向量 |
| `ESP_INTR_FLAG_LEVEL2` … `LEVEL6` | `1<<2` … `1<<6` | 逐级升高 |
| `ESP_INTR_FLAG_NMI` | `1<<7` | 最高优先级（不可屏蔽） |
| `ESP_INTR_FLAG_SHARED` | `1<<8` | 允许 ISR 共享 |
| `ESP_INTR_FLAG_EDGE` | `1<<9` | 边沿触发 |
| `ESP_INTR_FLAG_IRAM` | `1<<10` | 关 Cache 时也能调用（第二节） |
| `ESP_INTR_FLAG_INTRDISABLED` | `1<<11` | 分配后先禁用 |

源文件第 32 行还有一条**给实现者的提醒**：`Keep the LEVELx values as they are here; they match up with (1<<level)`，意思是**位号就是级别号**，这不是巧合，是接口约定（`probe.sh` 第 8 段逐条把 `LEVELn` 的位移量对回 n）。

**分配函数**（同文件 `:149`）：

```c
esp_err_t esp_intr_alloc(int source, int flags, intr_handler_t handler, void *arg, intr_handle_t *ret_handle);
```

五个参数各自的角色：

| 参数 | 填什么 | 从哪来 |
|---|---|---|
| `source` | 中断源（如 `ETS_GPIO_INTR_SOURCE`） | `soc/esp32s3/include/soc/interrupts.h` 的枚举 |
| `flags` | 级别 + 特性（OR 起来） | 上面那张表 |
| `handler` | 你的 ISR 函数 | 你写的 |
| `arg` | 传给 ISR 的参数 | 你定的（常用于传句柄） |
| `ret_handle` | 返回句柄，用于后续 `esp_intr_free` | 可以传 `NULL` |

**绑到哪个核**由 `flags` 里的级别与源决定（见 `esp_intr_alloc` 文档头里对 level 的说明）；简单记法是：**级别越高越"紧急"，也越不能用普通 API**。

## 四、双核分工：SMP 与钉核

S3 是双核（`SOC_CPU_CORES_NUM = 2`，[P1](01-arch-boot.md) 已引）。FreeRTOS 在 S3 上跑 **SMP**：默认情况下任务可以调度到任意核。

**需要控制核归属时，用钉核版 API**（`components/freertos/FreeRTOS-Kernel/include/freertos/task.h:382-389`）。

```c
extern BaseType_t xTaskCreatePinnedToCore( TaskFunction_t pxTaskCode,
                                           const char * const pcName,
                                           const configSTACK_DEPTH_TYPE usStackDepth,
                                           void * const pvParameters,
                                           UBaseType_t uxPriority,
                                           TaskHandle_t * const pvCreatedTask,
                                           const BaseType_t xCoreID );
```

比 `xTaskCreate` 多最后一个参数 `xCoreID`：

- `0` / `1`：钉到 PRO_CPU / APP_CPU；
- `tskNO_AFFINITY`：不钉核（调度器自由安排）。实测 `task.h:206` 把它定义为 `( BaseType_t ) 0x7FFFFFFF`，紧跟的第 207 行还有一条 `Todo: Update tskNO_AFFINITY value to -1` 的注释。所以它**不是 -1**，别按 -1 去猜值。

函数注释紧接着写明了这一点（`:391-392`）：**"Call the 'PinnedToCore' version with `tskNO_AFFINITY` to create an unpinned task."**。而且 `xTaskCreate` 的函数体（`:394` 起）只有一句 `return xTaskCreatePinnedToCore( pxTaskCode, ... )`。包装关系明明白白写在源码里，不是推测。

**什么时候该钉核**：

- 任务与**核绑定的外设**强相关（某些外设的中断固定在某核）；
- 需要**核间负载**明确分工（一核专管通信、一核专管控制）；
- 排查"任务跑到哪个核"引起的问题时先钉住复现。

反过来说，**能不钉就不钉**：钉核会降低调度器的灵活性，也让负载均衡失效。

## 五、共享数据：`volatile` 不够，要用自旋锁

这是 [C3 volatile 边界清单](../c/03-volatile.md) 的直接延续。在双核 + 中断的 ESP32 上，`volatile` **保证不了**任何一件事。把需求拆开看：

| 需求 | `volatile` 能做吗 | 正确做法 |
|---|---|---|
| 阻止编译器优化掉访问 | ✅ 能 | `volatile` 本行 |
| 读-改-写不被打断 | ❌ 不能 | `portMUX` 自旋锁 / 临界区 |
| 核与核之间的可见性 | ❌ 不能 | 自旋锁 / 原子操作 / 队列 |
| ISR 与任务之间传数据 | ❌ 不能 | `...FromISR` API（队列/通知） |

**`portMUX_TYPE` 的实现**（`components/freertos/FreeRTOS-Kernel/portable/xtensa/include/freertos/portmacro.h:188`）：

```c
typedef spinlock_t                          portMUX_TYPE;               /**< Spinlock type used by FreeRTOS critical sections */
#define portMUX_INITIALIZER_UNLOCKED        SPINLOCK_INITIALIZER        /**< Spinlock initializer */
```

而 `spinlock_t` 本体定义在 `components/esp_hw_support/include/spinlock.h:45`。

**三种场景的正确选择**：

```c
/* 场景 1：任务里保护共享变量的读-改-写（可能被其它核或 ISR 打断） */
static portMUX_TYPE my_mux = portMUX_INITIALIZER_UNLOCKED;

portENTER_CRITICAL(&my_mux);
shared_counter++;
portEXIT_CRITICAL(&my_mux);

/* 场景 2：ISR → 任务 传数据（唯一推荐的做法） */
xQueueSendFromISR(q, &data, &hp);      /* ISR 里 */
xQueueReceive(q, &data, portMAX_DELAY); /* 任务里 */

/* 场景 3：任务 → 任务 或 核 → 核 传数据 */
xQueueSend(...) / xTaskNotifyGive(...)  /* 用内核对象，别自己造轮子 */
```

**为什么临界区只包"读-改-写"而不是整个函数**：`portENTER_CRITICAL` 在有自旋锁的平台上会**关中断**（或自旋），持锁时间越长，实时性越差。**临界区要尽可能短**：这是 [F0](../rtos/freertos/00-why-rtos.md) 那个"任务越少越优雅"的同一条原则在锁上的体现。

## 六、与 NVIC 对照：单核与中断矩阵

| | STM32 F407（[S4](../stm32/04-nvic-exti.md)） | ESP32-S3 |
|---|---|---|
| 中断控制 | NVIC（每核一个，F407 单核） | **中断矩阵**（源 → 核 → 级） |
| 中断源数 | 按外设固定（IRQn 枚举） | **99 个源编号**（实测 0–98），可路由 |
| 优先级 | 4 位，`IP 字节 = 逻辑优先级 << 4` | **7 级**（`ESP_INTR_FLAG_LEVEL1..6` + NMI） |
| 向量表 | 固定地址数组，`IRQn + 16` | 由分配器动态绑定 |
| ISR 落址 | Flash 原地执行，无所谓 | **Flash 经 Cache 映射**——关 Cache 时不可取指 → IRAM 纪律 |
| 分配方式 | `NVIC_EnableIRQ(IRQn)` | `esp_intr_alloc(source, flags, ...)` |
| 核间 | 不存在 | 自旋锁 / `portMUX` / 队列 |

**差异概括**：STM32 的中断是**静态的**（谁挂哪个向量、什么优先级，编译期定死）；ESP32 的中断是**动态分配的**（运行时把源路由到核与级）。动态化换来灵活性，代价就是你多了一份责任：**分配时声明的一切，运行时要真做到**：IRAM 承诺如此，优先级选择亦然。

## 附录：工程完整源码

**01-gpio-matrix 的 main**（本章实验的起点：一个真实外设工程，`app_main` → 外设初始化；「先跑起来」的 ISR 就挂在它的 GPIO 上）：

<<< ../../code/esp32/01-gpio-matrix/main/main.c

**它的组件声明**（`REQUIRES esp_driver_ledc esp_driver_gpio`，P3 讲过的依赖声明；中断 API 就来自其中的驱动组件）：

<<< ../../code/esp32/01-gpio-matrix/main/CMakeLists.txt

## 记忆锚点

::: tip 一句话记住
**Cache 一关 Flash 里没代码：ISR 要么进 IRAM（还要带上它调的函数和常量），要么老实被推迟。双核共享别信 volatile，上 portMUX。**
:::

**延伸**：IRAM 纪律动画见 [P4 动画](/anim/iram-discipline.svg)；volatile 的局限性在 [C3](../c/03-volatile.md) 详解；STM32 NVIC 对照见 [S4](../stm32/04-nvic-exti.md)。

## 实物实验

- ~~写一个带 `IRAM_ATTR` 的 ISR 和一个不带的，`idf.py build` 后用 `arm-none-eabi-nm` 对比符号地址~~。这条已经在「先跑起来」里用**本机实跑**填掉了。原写法有两处错：ESP-IDF 用的不是 `arm-none-eabi-*`，而是 `xtensa-esp-elf-nm`；判据地址也不是 `0x400xxxxx`（那是初代 ESP32）。上板只剩一件静态取证做不到的事：**真的把 Cache 关一次**，在 NVS 提交期间触发这个中断，看它崩不崩。
- 给一个 GPIO 中断同时挂 `ESP_INTR_FLAG_LEVEL1` 与 `ESP_INTR_FLAG_IRAM`，在 ISR 里**故意**调 `printf`，观察它在 Flash 操作期间是否崩溃（**这是反例实验，小心使用**；**待上机回填**）。
- 用 `xTaskCreatePinnedToCore(..., xCoreID)` 分别传 `0`、`1`、`tskNO_AFFINITY` 创建同一个任务，在任务里打印 `xPortGetCoreID()`，记录三种情况下任务实际落在哪个核（**待上机回填**）。
- 把 `ESP_INTR_FLAG_LEVEL1` 改成 `LEVEL3`，观察中断响应行为（**待上机回填**）。

## 常见坑

- **只给 ISR 本体标 `IRAM_ATTR`**：它调用的函数、它读的字符串还在 Flash 里，关 Cache 时照样崩。**整条链**都要排查。
- **声明了 `ESP_INTR_FLAG_IRAM` 却没做到**：这比不声明更糟，不声明只是被推迟（安全），声明了却是**直接崩**。
- **ISR 里调 `printf`/`malloc`**：既可能碰 Flash，又可能违反 ISR 礼仪（[S4](../stm32/04-nvic-exti.md) 说过"中断里只做快递分拣"）。用 `...FromISR` API 或只置标志。
- **用 `volatile` 代替锁**：在双核 + 中断面前，`volatile` 既保证不了原子性也保证不了可见性。核间共享必须上 `portMUX` 或内核对象。
- **无脑钉核**：`xTaskCreatePinnedToCore` 用得越多，调度器越没得选，负载均衡失效。只在**有理由**时钉。
- **中断级越高越好**：级别高意味着它可能**抢占内核自己的临界区**，而高优先级 ISR **不能**调用大部分内核 API。默认从 `LEVEL1` 起步，确有需要再升。

## 短自测

**1. 为什么"代码在 Flash 里"这条在 STM32 上无所谓，在 ESP32 上是生死问题？**

<details><summary>看答案</summary>
STM32 的 Flash 是**原地执行**的（地址空间直接映射，CPU 直接从 Flash 取指，没有中间层）。ESP32-S3 的代码在外部 Flash，通过 **Cache 映射窗口**执行：系统写 Flash 时会**暂时禁用 Cache**，此时映射窗口失效，CPU 从 Flash **取不到指令**。所以 ISR 若在 Flash 里，关 Cache 期间被触发就是崩溃（除非没声明 IRAM-safe，被推迟）。</details>

**2. `IRAM_ATTR` 到底做了什么？加在 ISR 上够吗？**

<details><summary>看答案</summary>
它把代码放进 `.iram1` 段（`components/esp_common/include/esp_attr.h:23`：`#define IRAM_ATTR _SECTION_ATTR_IMPL(".iram1", __COUNTER__)`），_)`），由链接脚本安排到内部 SRAM。**加在 ISR 本体上不够**：ISR 调用的所有非内联函数、以及它读的所有 rodata（字符串、`const` 查表）也必须在 IRAM，否则整条链上有一环在 Flash 就崩。</details>

**3. 不声明 `ESP_INTR_FLAG_IRAM` 会怎样？**

<details><summary>看答案</summary>
系统会在 Flash 操作（Cache 禁用）期间**推迟**这个中断，ISR 不会被调用，等到 Cache 恢复再执行。这是**安全但可能有延迟**的行为。相反，声明了 `ESP_INTR_FLAG_IRAM` 就是承诺"我能在关 Cache 时跑"，系统不再推迟，代价是你必须真的保证整条链可达。</details>

**4. S3 有多少个中断源？几个中断级？**

<details><summary>看答案</summary>
**99 个中断源编号（0–98）**，实测 `components/soc/esp32s3/include/soc/interrupts.h`：枚举体第 18–117 行，最后一项 `ETS_DMA_EXTMEM_REJECT_SOURCE` 编译器打印出来是 98，紧跟的第 118 行 `ETS_MAX_INTR_SOURCE` = **99**。注意 99 说的是编号槽位：那 98 个名字只覆盖 95 个不同编号（23/33/34/46 是保留位，三条 `..._EDGE_INTR_SOURCE` 与各自 TARGET 同值）。
**7 个级别**：`ESP_INTR_FLAG_LEVEL1..LEVEL6`（`1<<1`..`1<<6`）加 `ESP_INTR_FLAG_NMI`（`1<<7`，源码注释直说 "Level 7 interrupt vector"），见 `components/esp_hw_support/include/esp_intr_alloc.h:33-39`。位号就是级别号，`probe.sh` 第 8 段逐条对过账。</details>

**5. 双核之间共享一个计数器，为什么 `volatile int n; n++;` 是错的？**

<details><summary>看答案</summary>
两个原因：**① 非原子**，`n++` 是"读-改-写"三步，另一个核或 ISR 可能插在中间，导致丢失更新；**② 无可见性/顺序保证**，`volatile` 只阻止编译器优化掉这次访问，不提供跨核的同步语义。正确做法是用 `portENTER_CRITICAL(&mux)` 包住读-改-写（`portMUX_TYPE` 是自旋锁，`portmacro.h:188`）；或者干脆用内核对象（队列、通知）代替裸变量。</details>

## 对照表：本章概念 → 仓库落点

| 概念 | 仓库落点 |
|---|---|
| `IRAM_ATTR` 定义（放进 `.iram1` 段） | `$IDF_PATH/components/esp_common/include/esp_attr.h:23` |
| `ESP_INTR_FLAG_IRAM`（`1<<10`，关 Cache 可调用） | `$IDF_PATH/components/esp_hw_support/include/esp_intr_alloc.h:42` |
| 中断级别标志 `LEVEL1..6` / `NMI` | 同上 `:33-39` |
| 其余特性标志（SHARED/EDGE/INTRDISABLED） | 同上 `:40-43` |
| 中断源数量（99）与枚举 | `$IDF_PATH/components/soc/esp32s3/include/soc/interrupts.h:18-118` |
| `esp_intr_alloc` 五参数签名 | `$IDF_PATH/components/esp_hw_support/include/esp_intr_alloc.h:149` |
| `xTaskCreatePinnedToCore` 七个参数 | `$IDF_PATH/components/freertos/FreeRTOS-Kernel/include/freertos/task.h:382-389` |
| 不钉核 = 传 `tskNO_AFFINITY` | 同上 `:394` 附近注释 |
| `portMUX_TYPE` 是自旋锁 | `$IDF_PATH/components/freertos/FreeRTOS-Kernel/portable/xtensa/include/freertos/portmacro.h:188` |
| `spinlock_t` 定义 | `$IDF_PATH/components/esp_hw_support/include/spinlock.h:45` |
| 双核数量（`SOC_CPU_CORES_NUM = 2`） | `$IDF_PATH/components/soc/esp32s3/include/soc/soc_caps.h:145` |
| ISR 写法参考（真工程） | `code/esp32/01-gpio-matrix/main/` |
| 四条链的落址取证探针（本机实跑，不需要板） | `code/esp32/09-iram-discipline/probe.sh` |
| `volatile` 的边界清单 | [C3 volatile](../c/03-volatile.md) |
| 单核 NVIC 的对照系 | [S4 中断与 NVIC](../stm32/04-nvic-exti.md) |

> 表中 `$IDF_PATH` = `C:/Users/zhugu/.espressif/v5.5.2/esp-idf`（本机 ESP-IDF v5.5.2）。行号以该版本为准，换版本需重核。

## 你做到了

- 知道了"IRAM 纪律"不是玄学：它是 Cache 映射执行的必然推论；
- 能正确给外设挂中断：选对源、级别、IRAM 标志，并知道每个选择的责任；
- 双核共享数据时不再指望 `volatile`，会用 `portMUX` 与 `--FromISR` API；
- 能对着 STM32 的 NVIC 说清"静态向量 vs 动态中断矩阵"的差异。

内鬼就是那条半截链：本体搬进了 IRAM，帮手还留在 Flash 里。关 Cache 的窗口一开，取指断在半路。整条链同进同出才是 IRAM 纪律的全文，也是你往后审每一份中断代码的尺子。

<div class="achievement">
✅ 下一站：<a href="../rtos/index.html">RTOS 篇</a>把双核 SMP 的调度细节补齐，或回 <a href="00-env.html">P0</a> 复查环境配置。
</div>

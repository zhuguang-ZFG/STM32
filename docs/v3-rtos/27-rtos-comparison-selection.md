---
title: "双 OS 对照与选型"
platforms: [f407]
---

# 双 OS 对照与选型

第 21 到 26 章把两套内核的机制拆到了源码行；这一章不再教机制，只做两件事：把同一条问题的两种答案摆进一张表，再把「下一个项目选谁」的判断过程摊开。对照表里每一行都带条件——优先级方向、级别数量、事件位宽这些数值，换一个配置就变，脱离条件的对照句是迁移事故的第一来源。

证据先说清：本章零实测。两套 OS 的切换时延、中断延迟、ROM/RAM 占用、软件包数量、迁移工时，六个来源里都没有可复核的读数；「标准版 32K Flash」「Nano 3K」「通知快一个数量级」「软件包数百个」「省几个月」全部按来源说法（未复核）处置，不进结论。选型结论落在约束、证据与风险上，不落在数字上。

> 版本口径：FreeRTOS 按 V11.3.2（根书口径）陈述通用行为，lab 工程为 V11.1.0，两者差异处单独注明；RT-Thread 按 v5.3.0。CMSIS-RTOS2 与 Zephyr 只作选型背景，不展开机制。

## 本章罗盘

- **问题**：优先级方向两边为什么相反，级别数量各由什么决定，选优算法差在哪？队列、消息队列、邮箱、通知、事件组在两边各是什么语义，哪些「名字相近但语义不等价」？堆、静态创建、内存池怎么对照，TLSF 在不在 RT-Thread 内核里？设备框架、shell、配置系统的有无意味着什么工程形态？许可证各是什么？实时性结论为什么只能落在预算公式上，测试条件要写清哪几项？ESP32 为什么几乎是唯一答案，STM32 上「需要几个组件」的经验阈值怎么用，决策树哪两个分支是错的？「优先级 5 可迁移」这类示例为什么在 lab 上越界？迁移坑按什么清单过？
- **交付**：能按条件复述对照表的每一行（方向、数量、位宽、API 形态），指出哪两处来源说法已被上游核对推翻；能把 FreeRTOS 队列与 RT-Thread 消息队列的语义差别说清（创建时定宽 vs 固定最大块的变长消息）；能算事件组可用位宽并按 tick 位宽给条件；能写出一笔基于 map 与水位的资源账而不是抄别人的 256 KiB 示例；能按「硬约束→驱动与生态→团队兜底」走一遍决策树，说出两个被修正的分支；能把定量说法逐条标注「来源说法(未复核)」并给出替代判据；能列出迁移七坑并先读 `configMAX_PRIORITIES` 再给映射。
- **边界**：只做对照与选型，不重教机制——调度细节归 [第 22 章](./22-tasks-tcb-scheduler.md) 与 [第 23 章](./23-context-switch-porting.md)，IPC 归 [第 24 章](./24-queue-semaphore-notification.md)，内存归 [第 25 章](./25-memory-management.md)，设备框架与配置系统归 [第 26 章](./26-device-framework-shell.md)。Zephyr 只保留「Kconfig + Devicetree + 设备模型」的功能定位，其调度器实现细节未复核不写。CMSIS-RTOS2 只写「统一接口不统一实现」。不写任何 µs 级时延断言——六源无实测。
- **依据锚点**：X0《同概念双实现对照》（`mcu/docs/rtos/compare/00-side-by-side.md`）、X1《选型决策树》（`.../01-choose.md`）、D28《嵌入式系统与 RTOS 生态》（`docs/28-嵌入式系统与RTOS生态.md`，只取选型与边界段）。配置见 `mcu/code/rtos/01-freertos-lab/FreeRTOSConfig.h:23`（`configMAX_PRIORITIES=5`）、`:31`、`:36`；RT-Thread 配置见 `src/Kconfig:94-110`（级别数）与 `components/finsh/Kconfig`。上游对账：FreeRTOS-Kernel 的 [LICENSE.md](https://github.com/FreeRTOS/FreeRTOS-Kernel/blob/V11.3.2/LICENSE.md)、[portmacro.h](https://github.com/FreeRTOS/FreeRTOS-Kernel/blob/V11.3.2/portable/GCC/ARM_CM4F/portmacro.h)；RT-Thread v5.3.0 的 [LICENSE](https://github.com/RT-Thread/rt-thread/blob/v5.3.0/LICENSE)、[scheduler_up.c](https://github.com/RT-Thread/rt-thread/blob/v5.3.0/src/scheduler_up.c)、[ipc.c](https://github.com/RT-Thread/rt-thread/blob/v5.3.0/src/ipc.c)。机制细节分别在 [第 21–26 章](./21-why-rtos.md)。

## 一张对照总表

![FreeRTOS 与 RT-Thread 五层对照：同一条问题的两种答案，虚线连接](/arch/rtos-side-by-side.png)

![双 OS 对照动画：任务通知与信号量、有无设备框架、FreeRTOSConfig.h 与 Kconfig 三组并排演进](/anim/dual-os-compare.svg)

| 维度 | FreeRTOS | RT-Thread | 条件与出处 |
| --- | --- | --- | --- |
| 定位 | 极简内核，其余自行组合 | 内核 + 组件 + 生态 | 比较对象是 FreeRTOS Kernel 与 RT-Thread 标准版，不含 Nano |
| 任务对象 | TCB（`tasks.c`） | `rt_thread`（继承 `rt_object`） | 结构见 [第 22 章](./22-tasks-tcb-scheduler.md) |
| 优先级方向 | 数值大 = 高 | 数值小 = 高（0 最高） | 方向随内核，不能当通则；NVIC 又是反向（小 = 高） |
| 级别数量 | `configMAX_PRIORITIES` 决定，lab 是 5 | 默认 32（8/32/256 可配） | 见「调度器对照」一节的条件 |
| 上下文切换 | PendSV | PendSV | 细节归 [第 23 章](./23-context-switch-porting.md)，此处不重复 |
| tick 与延时 | `xTaskIncrementTick` + 延时列表 | `rt_tick_increase` + 线程内嵌定时器 | tick 时基见 [v1 第 11 章](../v1-drivers/11-systick-timebase-rtc.md) |
| 队列/消息 | Queue：项宽创建时定死 | 消息队列：槽宽 `msg_size` 固定，实发长度 ≤ 槽宽 | 见「IPC 对照」 |
| 互斥 | 基于队列实现，带优先级继承 | 独立 IPC 对象，带优先级继承 | 语义见 [第 24 章](./24-queue-semaphore-notification.md) |
| 轻量通知 | 任务通知（写 TCB 字段） | 无直接等价，用 sem/event 替代 | 「无直接等价」不等于「无轻量机制」 |
| 事件 | 事件组，位宽随 tick 位宽（lab 24 位） | 事件集 32 位 | 位宽算法见下文 |
| 堆 | heap_1–5 编译期选一 | mem/memheap/slab/mempool 并存 | 对照见 [第 25 章](./25-memory-management.md) |
| 静态创建 | `xTaskCreateStatic` 家族 | `*_init` 系列 | lab `configSUPPORT_STATIC_ALLOCATION=0`，示例需注明配置 |
| 驱动模型 | 无内置 | `rt_device` 设备框架 | 见 [第 26 章](./26-device-framework-shell.md) |
| 控制台 | 无内置 | finsh/MSH | 见 [第 26 章](./26-device-framework-shell.md) |
| 构建/配置 | `FreeRTOSConfig.h` 头文件 | Kconfig + menuconfig + scons | ESP-IDF 是 Kconfig 管 FreeRTOS 的混合形态 |
| 许可证 | FreeRTOS-Kernel 为 MIT | RT-Thread 为 Apache-2.0 | 上游 LICENSE 实读 |
| 可观测 | RunTimeStats/Trace 需自接 | `list_*` 命令开箱即用 | finsh 组件开着才有，见 [第 26 章](./26-device-framework-shell.md) |

这张表是「带条件的地图」，不是排行榜。每一行的最后一列写清条件，是因为三条来源说法已经被上游核对推翻：RT-Thread「总是 256 级、二级位图」不成立（默认 32，超 32 才二级）；FreeRTOS「常 32 级、上限 32」不成立（数量由配置决定，CM4F 优化路径才约束 32）；「消息队列变长 / 定长」两边都错——正确表述见 IPC 一节。

## 调度器对照：方向、数量、算法都带条件

**方向**。FreeRTOS 数值大 = 高；RT-Thread 数值小 = 高；NVIC 数值小 = 高。三套坐标系摆一起，是迁移事故的第一来源：把 FreeRTOS 的「5」原样填进 RT-Thread，任务从「偏高」变成「偏低」；拿任务优先级数字去填 NVIC 寄存器，方向再反一次。方向随内核，不能当通则——旧材料「任务优先级数值越大越高」只对 FreeRTOS 成立。

**数量**。两边都不该写死：FreeRTOS 的级别数由 `configMAX_PRIORITIES` 决定，本 lab 是 5（合法值 0–4，`FreeRTOSConfig.h:23`）；CM4F 端口在开了 `configUSE_PORT_OPTIMISED_TASK_SELECTION` 时位图路径约束上限 32（`portmacro.h`），其他端口各有各的约束。RT-Thread 通过 `src/Kconfig:94-110` 配 8/32/256，默认 32。旧表「RT-Thread 32/256、二级位图」把可配置项写成了固定值。

**算法**。FreeRTOS 单级位图 + CLZ 前导零找最高就绪级（依赖上述优化开关）；RT-Thread 在级别 ≤ 32 时用单级位图 `rt_thread_ready_priority_group`，> 32 才启用二级位图 `rt_thread_ready_table[32]`（`scheduler_up.c:46-51,107-116`）。「一边永远单级、另一边永远二级」的说法不成立——两边的算法都随配置切换。算法细节见 [第 22 章](./22-tasks-tcb-scheduler.md) 的就绪位图一节。

## IPC 对照：名字相近不等于语义等价

| 意图 | FreeRTOS | RT-Thread | 迁移注意 |
| --- | --- | --- | --- |
| 定长消息 | Queue：`uxItemSize` 创建时定死 | 消息队列：槽宽 `msg_size` 固定，`rt_mq_send` 实发长度 ≤ 槽宽 | 两边都不是「变长队列」；RT 每条另有消息头 |
| 机器字传递 | 无直接对应 | 邮箱：每格 4 B（`rt_ubase_t`） | 传指针要管生命周期 |
| 轻量一对一 | 任务通知（写 TCB 的 `ulNotifiedValue[]`） | 无直接等价：sem/event 替代 | 幅度依配置，只写「更快」，倍数不采用 |
| 计数资源 | 计数信号量 | semaphore | 语义一致 |
| 所有权 | 互斥锁 + 继承 | mutex + 继承 | RT 自带递归计数，FreeRTOS 递归要独立 API |
| 多条件位 | 事件组：位宽随 tick 位宽 | 事件集：32 位 | 位宽表见下 |
| ISR 推迟工作 | FromISR + `portYIELD_FROM_ISR` | IPC 唤醒线程（按端口约定进 `rt_interrupt_enter/leave`） | 边界见 [第 23 章](./23-context-switch-porting.md) |

两处旧说法要当场纠正：D28 把 RT-Thread 消息队列写成「定长」——槽宽固定但实发长度可短，准确说法是「固定最大块的变长消息」；X0/R2 把 FreeRTOS 队列说成「变长」——`uxItemSize` 创建时定死，变的只是条数。两边都不能用「变长队列」这个词。

事件位宽有一道算术（[第 24 章](./24-queue-semaphore-notification.md) 已推导）：`EventBits_t` 等于 `TickType_t`，高位留作控制位——16 位 tick 剩 8 位可用，32 位剩 24 位，64 位剩 56 位；lab 是 32 位 tick，24 位事件。RT-Thread 事件集固定 32 位。按 32 位事件写的位操作，搬到 16 位 tick 的 FreeRTOS 工程就丢位。

## 内存对照

FreeRTOS 是「编译期选一个 heap_x」：heap_1–5 的能力阶梯、块头与合并算法见 [第 25 章](./25-memory-management.md)。静态创建两套都有：`xTaskCreateStatic` 与 `*_init` 系列——但本 lab 的 `configSUPPORT_STATIC_ALLOCATION=0`，引静态 API 的示例要注明「在打开该配置的工程里」。RT-Thread 是四件分配器并存（mem/memheap/slab/mempool），可按对象选；**`src/tlsf.c` 不存在**，TLSF 是论文算法与软件包，不在 5.3.0 内核里。

平台内存数字按本工程写：F407 是 128 KiB SRAM + 64 KiB CCM（共 192 KiB），CCM 不能放 DMA 缓冲。资源账自己算——链接 map 给静态占用，`uxTaskGetStackHighWaterMark` 与 `xPortGetMinimumEverFreeHeapSize` 给运行期水位；旧材料那份「256 KiB SRAM 的示例账」算术自洽但平台不同，可以借格式，数字不能搬。

## 设备、配置与许可

![四系统选型对照：裸机前后台、FreeRTOS、RT-Thread、Zephyr 各自的强项与代价](/figures/sample-28-os-compare.svg)

![手绘板：四系统选型对照——FreeRTOS 小内核自行组合、RT-Thread 设备框架与软件包、Zephyr Kconfig+Devicetree、CMSIS-RTOS2 统一接口不统一实现](/images/ch28-os-compare.png)

- **设备与控制台**：FreeRTOS 裸内核不自带驱动模型与 shell，UART 收发、日志、命令行都归项目自建（[第 24 章](./24-queue-semaphore-notification.md) 的 ring+sem 就是手写版）；RT-Thread 用 `rt_device` 设备框架与 finsh 把这两件事标准化。差异的工程含义：RT-Thread 的软件包能依赖统一设备接口跨 BSP 跑；FreeRTOS 的同类能力靠移植与第三方。
- **配置**：FreeRTOS 是「头文件派」——`FreeRTOSConfig.h` 手改宏，无工具依赖，依赖检查靠人（开了 `configUSE_MUTEXES` 忘开递归互斥的配套宏，编译能过、运行不对）；RT-Thread 是「菜单派」——Kconfig 声明依赖，menuconfig 灰化不可选项，scons 生成 `rtconfig.h`。注意 ESP-IDF 的存在：它用 Kconfig 管 FreeRTOS 配置（`CONFIG_FREERTOS_*` 生成后喂给内核）——「FreeRTOS 只能手改头文件」的说法要带上「ESP-IDF 混合形态除外」。
- **许可**：FreeRTOS-Kernel 是 MIT，RT-Thread 是 Apache-2.0（上游 LICENSE 文件实读）。两者都允许商用；差别的法律细节（专利条款、发行义务）归法务核对，本书只锁「文件名与许可证类型」这个事实层。
- **生态数量**：「软件包数百个」这类计数随时间变化，写进文档必须带抓取日期与来源；本书只写定性事实——软件包中心覆盖联网、存储、UI 等类别，数量以官方索引当时实况为准。

## 实时性：预算制，不是商标制

「FreeRTOS 切换比 RT-Thread 快」这类话本书不写——不是断言方向错了，而是六份来源里**没有任何一条**带测试条件的切换时延或中断延迟实测，没有可比性。实时性结论只能落在预算上：

- **三种时间分开**：响应时间（事件到任务开始处理）、执行时间（任务占 CPU 的时长）、端到端时延（传感器到执行器/ACK 全程）。每层各一个超时的系统，端到端叠加远超预期。
- **响应时间是 R = B + C + S**：B 是共享资源阻塞，C 是最坏执行时间，S 是高优先级干扰（含 ISR）。验收看最坏 R ≤ 截止点，不是平均利用率。
- **U = Σ(Cᵢ/Tᵢ) < 1 只是必要条件**：CPU 时间没超额不证明截止满足——阻塞、Flash 等待、Cache miss 都在 R 里不在 U 里。
- **要写测试条件**：内核与版本、主频、Flash 等待周期、临界区策略、ISR 优先级配置。少一条，数字就不可比。

D28 的示例预算表（电流环 80 µs/1 ms、合计 17.2% 那张）是**可复算的算术示例**，不是任何板子的测量结论；借它的格式，别借它的数字。

## 选型：约束 → 证据 → 风险

![RTOS 选型决策树动画：平台已定走平台绑定分支，STM32 上按组件需求与团队熟悉度分流](/anim/rtos-decision-tree.svg)

选型顺序是三层漏斗（D28 与 X1 一致）：**先列硬约束**（平台绑定、认证要求、内存预算、工具链、维护周期），**再看驱动与生态**（所需组件在哪个体系里现成），**最后团队熟悉度兜底**。三句话版：

1. **平台先定**：ESP32 用 ESP-IDF 自带 FreeRTOS——Wi-Fi/BLE 协议栈、电源管理、S3 双核 SMP 调度与 IDF 深度耦合，换内核要把这三样全部重新对接，成本远大于收益。注意边界：S3 的 SMP 适配是双核形态，不能外推到单核 F407 上去推断 FreeRTOS 行为。
2. **生态其次**：要拼「联网 + 存储 + UI + OTA」的产品，RT-Thread 标准版的软件包与设备框架省自建工作量（省多少个月是来源说法，本书不采用）；功能纯粹的控制器（采集 + 上报、状态机），FreeRTOS 极简内核更贴。
3. **团队兜底**：平台与生态都没有压倒性倾向时，团队熟悉哪个用哪个——RTOS 的坑长在「不熟悉」上，学习成本是真实工程成本。

决策树上有两个分支要按修正后的逻辑走：

- **「不需要组件 → 标准版」是错的**。不需要现成组件时，合理落点是 FreeRTOS 或 RT-Thread Nano——标准版的价值在组件生态，没有组件需求就没有付组件层成本的理由。「需要 3 个以上组件才显著受益」是经验阈值，不是测量结论；落到自己项目要给组件清单加 map 实测。
- **「安全认证 → 静态 FreeRTOS」也是错的**。静态分配消灭的是「运行期分配失败」这一类风险，不等于通过认证——认证审的是开发过程、证据链与内核本身的认证资质。认证场景的选型对象是「带认证资质的内核或已有认证证据链的版本」，静态化只是工程手段之一。

Zephyr 在这个漏斗里的定位：跨厂商板卡、Kconfig/Devicetree、协议子系统要求高的新品，它把配置、硬件描述与设备模型放进统一构建体系——功能定位可写，调度器实现细节本书未复核、不写。

## 迁移坑清单

七个坑按「先读配置再动手」的顺序过：

1. **优先级方向**：先读 `configMAX_PRIORITIES` 与 RT-Thread 的级别配置，再给映射表。旧示例「FreeRTOS 优先级 5 迁到 RT-Thread 填 25」在 lab 上直接越界——`configMAX_PRIORITIES=5` 时合法值只有 0–4，5 本身就越界。任何迁移映射都从读最大值开始。
2. **通知 → sem**：任务通知在 RT-Thread 没有直接等价，用二值信号量或事件集替代；性能只写「更快，幅度依配置」，倍数是来源说法。
3. **队列语义**：FreeRTOS 定宽队列、RT 槽宽固定的变长消息——「变长队列」这个词两边都不成立，迁移时按槽宽重新对账。
4. **堆 API**：`pvPortMalloc/vPortFree` 与 `rt_malloc/rt_free` 不是一族，交叉释放是内存灾难；迁移时全局替换并核对 free 家族配对。
5. **静态 API**：`xTaskCreateStatic` 传 TCB + 栈两个缓冲，`rt_thread_init` 传结构 + 栈 + 栈深——参数个数与顺序不同，别按肌肉记忆填。
6. **事件位宽**：按 tick 位宽重算可用位（8/24/56），32 位写法在 16 位 tick 工程上丢位。
7. **版本钉住**：两边的字段名、默认值、命令名都随版本变（[第 25 章](./25-memory-management.md) 的 TLSF 与 finsh 命令就是现成案例）；迁移文档写清两边的冻结版本。

还有一条 AMP 旁注：STM32H745 这类 M7+M4 双核芯片，常见形态是两核各跑一个内核、共享内存 + HSEM 交换数据——这是 AMP 不是 SMP，「有两颗核」推不出「一个内核管两个核」，双核契约（共享区布局、所有权、屏障、协议）要单独冻结。

## 定量说法处置表

本章把六个来源里的定量说法逐条过堂——每条要么给出替代判据，要么标明身份：

| 说法 | 处置 | 替代判据 |
| --- | --- | --- |
| 标准版 32K Flash / Nano 3K / 差 10 倍 | 来源说法（未复核），不进结论 | 自己组件清单 + map 实测，写清版本与裁剪 |
| 软件包省几个月 / 迁移工时 | 来源说法（未复核），不进结论 | 按组件清单估自建工作量，留评审记录 |
| 软件包数百个 | 来源说法（未复核），计数随时间变 | 引用带抓取日期与官方索引来源 |
| 通知快一个数量级 / 约 45% | 来源说法互斥（X0 与 F6 数字冲突），均不采用 | 只写「更快，幅度依配置」，要数字同板同配置基准 |
| µA 级睡眠 | 来源说法（未复核） | 低功耗的读数与口径见 [第 18 章](../v2-reliability/18-low-power.md)，同样按证据标签处理 |
| 读懂一周 / 用全一天 | 营销式修辞，删除 | 学习成本按团队实际情况评审 |

## 短自测

1. 「RT-Thread 总是 256 级、二级位图」「FreeRTOS 常 32 级」为什么都要改？
<details><summary>参考答案</summary>两边都写成死值了。RT-Thread 级别由 `src/Kconfig` 配 8/32/256、默认 32，> 32 才二级位图（`scheduler_up.c:46-51,107-116`）；FreeRTOS 数量由 `configMAX_PRIORITIES` 决定（lab 是 5），CM4F 优化路径才约束 32。对照句必须带配置条件。</details>

2. 优先级方向的完整说法是什么？
<details><summary>参考答案</summary>方向随内核：FreeRTOS 数值大 = 高；RT-Thread 数值小 = 高（0 最高）；NVIC 数值小 = 高。「任务优先级数值越大越高」只是 FreeRTOS 的规则，不能当通则；拿任务优先级数字填 NVIC 寄存器要再反一次方向。</details>

3. FreeRTOS 队列与 RT-Thread 消息队列的准确语义各是什么？
<details><summary>参考答案</summary>FreeRTOS Queue 的 `uxItemSize` 创建时定死，变的只是条数；RT-Thread 消息队列槽宽 `msg_size` 固定、`rt_mq_send` 实发长度 ≤ 槽宽，每条另有消息头——是「固定最大块的变长消息」。D28 的「定长」与 X0/R2 的「变长队列」都不准确。</details>

4. FreeRTOS 事件组的可用位宽怎么算？lab 是几位？
<details><summary>参考答案</summary>`EventBits_t` 等于 `TickType_t`，高位留作控制位：16 位 tick 剩 8 位，32 位剩 24 位，64 位剩 56 位。lab 是 32 位 tick → 24 位事件。RT-Thread 事件集固定 32 位，按 32 位写的位操作搬到 16 位 tick 工程会丢位。</details>

5. 任务通知迁到 RT-Thread 用什么替代？速度差异怎么写？
<details><summary>参考答案</summary>没有直接等价物，用二值信号量或事件集替代——「无直接等价」不等于 RT-Thread 没有轻量机制。速度只写「更快，幅度依配置」；「一个数量级」「约 45%」两个来源说法互斥且都无版本配置条件，不采用。</details>

6. 「优先级 5 可迁移」的示例错在哪？
<details><summary>参考答案</summary>lab 的 `configMAX_PRIORITIES=5`（`FreeRTOSConfig.h:23`），合法值 0–4，5 本身越界。任何迁移映射先读目标工程的 `configMAX_PRIORITIES` 与 RT-Thread 级别配置，再给映射表——示例里的 25 是在「256 级」假设下给的，脱离配置。</details>

7. 内存对照的三个要点？
<details><summary>参考答案</summary>FreeRTOS 编译期选一个 heap_x（能力阶梯见第 25 章）；RT-Thread 四件分配器并存（mem/memheap/slab/mempool），`src/tlsf.c` 不存在、TLSF 是论文算法与软件包；静态创建两边都有，但 lab `configSUPPORT_STATIC_ALLOCATION=0`，示例要注明配置。资源账按 map 加水位自算，不搬别人的 256 KiB 示例。</details>

8. 「ESP32 用 IDF 自带 FreeRTOS」的边界是什么？
<details><summary>参考答案</summary>平台绑定：Wi-Fi/BLE 协议栈、电源管理、S3 双核 SMP 调度与 IDF 深度耦合，换内核成本以人月计。边界：S3 的 SMP 适配是双核形态，不能外推到单核 F407 推断 FreeRTOS 行为。</details>

9. 决策树哪两个分支要修正？
<details><summary>参考答案</summary>「不需要组件 → 标准版」应为 FreeRTOS 或 RT-Thread Nano——标准版的价值在组件生态，无组件需求不付组件层成本；「安全认证 → 静态 FreeRTOS」不成立——静态分配只消灭运行期分配失败，认证审的是过程、证据链与内核资质，选型对象是带认证资质的内核或证据链。</details>

10. 「需要 3 个以上组件选标准版」是什么身份的说法？
<details><summary>参考答案</summary>经验阈值，不是测量结论。落到自己项目：列组件清单，用 map 实测标准版裁剪后的占用，再判断阈值是否适用。</details>

11. 许可证各是什么？本书锁到哪一层事实？
<details><summary>参考答案</summary>FreeRTOS-Kernel 是 MIT，RT-Thread 是 Apache-2.0（上游 LICENSE 实读）。本书只锁「文件与许可证类型」这层事实；专利条款与发行义务等法律细节归法务核对。</details>

12. 实时性结论为什么只能落在预算公式上？
<details><summary>参考答案</summary>六份来源没有任何一条带测试条件的切换时延或中断延迟实测，µs 级断言全部不写。响应时间是 R = B + C + S（阻塞 + 最坏执行 + 高优先级干扰），U < 1 只是必要条件；要数字必须先写全测试条件（内核版本、主频、Flash 等待、临界区、ISR 优先级）。</details>

13. 「标准版 32K Flash、软件包数百个」这类数字怎么处置？
<details><summary>参考答案</summary>按来源说法（未复核）处置：不进结论，要么删除，要么带版本/配置/抓取日期。替代判据：组件清单 + map 实测；包数量引用官方索引并注明日期。</details>

14. H745 的双核形态是 SMP 吗？
<details><summary>参考答案</summary>常见形态是 AMP：两核各跑一个内核，共享内存加 HSEM 交换数据。有两颗核推不出一个内核管两个核；共享区布局、所有权、内存屏障、消息协议、启动恢复要按五层契约单独冻结。</details>

15. 本章哪些数是来源说法、哪些是文档推导？
<details><summary>参考答案</summary>来源说法（未复核）：32K/3K/10 倍、省几个月、数百个包、通知 10×/45%、µA 睡眠、读懂一周。文档推导：方向与数量条件（上游核对）、事件位宽算术、迁移七坑、决策树两个修正分支、许可证类型（LICENSE 实读）。未实测：一切时延与占用数字。</details>

## 收束

对照表的价值不在「谁赢了」，在于把「名字相近的 API」背后的语义差摊开：方向、位宽、槽宽、递归、通知，每一处都能在迁移时救回几天排障时间。选型同理——约束、证据、风险三层走完，结论自然浮出来；跳过约束直接比数字，是选型返工的头号原因。

下一卷离开 RTOS，进入多平台与连接：换芯片、换架构、上网络。

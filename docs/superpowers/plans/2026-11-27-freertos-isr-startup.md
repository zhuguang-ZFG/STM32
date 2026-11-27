# FreeRTOS 按键中断：对象生命周期与优先级单位

范围：F103 `examples/freertos-task` 的生产 main、宿主测试、README，以及第 24 章 FromISR 小节与附录 B 的测试边界说明。F407 lab 保持原工程；本轮不新增可下载 RTOS 固件。

## Sepia review（先审后改）

类型：中文技术教程。Loaded：Sepia professional-pass、tech-articles、discourse-pass §1–3、style-pass、zh 与 GPT prose layer；作者未知，执行模型 GPT-6（子版本未知），prose layer author=none、executor=prior。参考语域为仓库第 23/24 章与 UART 示例 README。

| 原文证据 | 缺陷 | 修订方向 |
| --- | --- | --- |
| README「数值 ≥ configMAX_SYSCALL_INTERRUPT_PRIORITY」 | HAL 参数是未左移的逻辑值，宏是左移后的寄存器字节 | 同时给出 5 / 0x50 两种单位及换算；代码从配置提取逻辑值 |
| bsp_init 使能 EXTI 后，main 才创建队列 | 早到的按键可进入 FromISR 并访问空队列；仅先建队列仍未解决调度器尚未开始的窗口 | BSP 显式禁用 NVIC；KEY 任务第一次运行时依次清 EXTI / NVIC pending，再使能 |
| 旧宿主文件「Mirror macros from main.c」 | 三组断言只验证手写常量，生产代码破坏后仍可通过 | 编译实际 main，HAL/RTOS 边界记录对象创建、任务参数、ISR 与互斥锁路径 |
| 「若唤醒了高优先级任务，立即切换」「队列空时任务挂起」 | 混淆请求 PendSV 与实际换栈、阻塞与挂起 | 对齐第 23/24 章的延迟切换与阻塞术语 |
| 「每按一次按键，串口打印一行」 | 代码未消抖，队列满时未重试或计数，不能保证一按一行 | 写明边沿事件、深度 8 和丢弃策略，保留硬件待测 |

Failed：#5 specificity（接口单位、启动阶段和测试证据不符）；Style scan：无须整章重写。Passed：1、2、3、4、6、7、8、9、10。Verdict：isolated hits → refactor。Deferred：真实调度器、F407 固件与硬件响应。Protected：板型、接线、既有内核版本出处与历史验收状态。

## 根因与验收

- `HAL_NVIC_SetPriority` 的 PreemptPriority 范围来自固定 CubeF1 v1.8.6 HAL 的 `stm32f1xx_hal_cortex.c`；底层 CMSIS 会编码再左移。
- 阈值与 BASEPRI 语义沿用第 23/24 章 V11.1.0 的依据；本地 CubeF1 携带的 FreeRTOS V10.3.1 `ARM_CM3/port.c` 也按寄存器字节检查 `ucCurrentPriority >= ucMaxSysCallPriority`，版本不混称。
- 测试先运行于旧 main：在 `HAL_NVIC_EnableIRQ` 处以「scheduler_running && g_key_queue != NULL && g_uart_mutex != NULL」失败。把放行延后到 KEY 任务后，通过默认阈值测试。
- 新增原始阈值 0x60 的编译变体：旧固定逻辑 5 在「irq_priority == 6U」处失败；换成从配置提取逻辑值后，两组通过。
- 错误阈值 0、0x51、0x100 经宿主编译器验证均因静态断言失败，分别覆盖零值、未对齐和超字节范围。
- 初始化失败覆盖队列、互斥锁、三次任务创建和调度器返回；任务创建失败按 `projdefs.h` 返回 -1，不把它模拟为 pdFAIL=0。失败路径都不得开放按键 IRQ。成功路径覆盖旧 pending 清除、任务实际参数、FromISR 唤醒与不唤醒、队满返回失败、错误引脚、任务延时和互斥锁获取失败。
- 所有测试替身只定义宿主 API 边界；未链接 FreeRTOS 内核，不证明真实队列、抢占时序或实板行为。

删除检查：删除「立即切换」「一按一行」等超过证据的承诺；新增只解释对象何时可用及两种优先级单位。回退检查：保留 F103 草稿与 F407 正文章的板型边界。

## 本地验证

- `cmake --preset host-tests`、构建与 ctest：两组阈值均通过。
- 另建 Release 配置（GCC 16.1，O3/NDEBUG）：两组通过；测试文件主动保留 assert，CI 同步采用 Release。修复了测试循环与 longjmp 组合在优化构建中的 clobbered 警告，未降低警告级别。
- GNU Arm GCC 对生产 main 做 C11 / Cortex-M3 语法检查：通过。真实头文件取固定 CubeF1 v1.8.6（`42472d601caa457b02d849c7de5f9792629ee324`），HAL `77fbb30b7a1d02533980400083e48c559aae5a4f`，其附带 FreeRTOS 为 V10.3.1；复用 UART 工程的 HAL 模块配置与 ST F103RB Nucleo ThreadCreation 的内核配置。仅为接口检查，没有链接成固件，也不声称核验了正文引用的 V11.1.0/V11.3.2 构建。
- `python -m book.checks`、`python tools/slop_lint.py`：通过；`python -m book.md_links`：139 文件、0 问题。
- `npm.cmd run docs:build`：通过，仅有既有的 ld 高亮回退和 bundle 体积提示。

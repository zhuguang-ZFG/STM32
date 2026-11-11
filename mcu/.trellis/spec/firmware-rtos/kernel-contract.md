# RTOS 内核与移植合同

## 1. 适用范围与触发

- 改 `code/rtos/01-freertos-lab/`、`02-rt-thread-lab/` 的 Makefile、配置头、启动/移植文件、场景代码时读这份。
- 改 `docs/rtos/freertos/`、`docs/rtos/rtthread/`、`docs/rtos/compare/` 的内核结论时读这份。
- 只改板级外设：归 [firmware-stm32](../firmware-stm32/index.md)；本层不复制 GPIO/USART 规则。

## 2. 签名与产物

| 入口 | 输入 | 产物/副作用 |
|---|---|---|
| `make`（01-freertos-lab） | `DEMO_SCENE=1..6`、可选 `USE_MUTEX=1`、`FREERTOS_KERNEL=…` | `build/scene-N/freertos-lab.{elf,bin,hex,map}`；`make flash` 走 OpenOCD |
| `make`（02-rt-thread-lab） | `DEMO_SCENE=1/6`、可选 `USE_MUTEX=1`、`RT_THREAD_DIR=…` | `build/scene-N[-mutex]/rt-thread-lab.{elf,bin,hex,map}`；`make flash` |
| `sh code/rtos/00-why-rtos/probe.sh` 等 | 宿主机编译器 | 宿主机模型/反汇编/对照，不碰板 |
| `npm run firmware:check` | `MAKE`、ARM 工具链 | 逐场景/变体构建 + 场景隔离断言；写各工程 `build/` |

## 3. 数据与环境契约

### 3.1 两个内核不是同一个东西

| 项 | FreeRTOS 工程 | RT-Thread 工程 | ESP-IDF 内置 |
|---|---|---|---|
| 版本 | FreeRTOS-Kernel **V11.1.0**（tag） | RT-Thread **5.x master（2026-10）**，未钉 tag/revision | ESP-IDF **v5.5.2** 内置 FreeRTOS **V10.5.1 SMP 修改版** |
| 端口 | `portable/GCC/ARM_CM4F`，单核 | `libcpu/arm/cortex-m4` 手动移植 | IDF 自己的 SMP 端口 |
| 分配器 | `heap_4` | Nano 小内存堆 | IDF 配置 |
| 源码位置 | `.trellis/ref/freertos-v11/kernel` 或 `FREERTOS_KERNEL` | `.trellis/ref/rt-thread` 或 `RT_THREAD_DIR` | IDF 组件树 |
| 优先级方向 | 数值越大越高 | **数值越小越高** | 同 FreeRTOS |

- 行号、任务栈参数单位、调度结论、配置宏不得跨这三份源码混读。P 篇（ESP32）只对 IDF 内置版本负责，F 篇只对上游 V11.1.0 负责。
- RT-Thread 的 revision 未锁定：README 记录"master（2026-10，5.x）"，没有 commit/tag。写"固定版本"是失实；要锁定必须补 tag/commit 与校验记录。

### 3.2 场景与构建目录

- FreeRTOS：`DEMO_SCENE` 只接受 `1..6`；`BUILD := build/scene-$(DEMO_SCENE)`。
  场景 1 任务/TCB、2 通知、3 事件组、4 软件定时器、5 heap_4、6 优先级反转。
- RT-Thread：`DEMO_SCENE` 只接受 `1` 或 `6`；`BUILD := build/scene-$(DEMO_SCENE)$(if $(USE_MUTEX),-mutex)`。
- 两个工程都规定"参数变化不是 make 的文件依赖；每场景独立产物，切换无需 clean"。新增场景必须同时改 Makefile 的 `filter` 与 `code/projects.json` 的 `scenes`。
- 内核源文件按上游原样编译，不参与项目代码的 `-Wall -Wextra` 零警告口径；项目自己的 `main.c`/`board.c`/`syscalls.c` 必须零警告。
- RT-Thread 内核源必须定义 `__RT_KERNEL_SOURCE__`，否则 `rtsched.h` 的内部调度 API 不可见；这与官方 scons 构建一致。

### 3.3 配置宏

FreeRTOS（`FreeRTOSConfig.h`）：

- `configTICK_RATE_HZ=1000`、`configMAX_PRIORITIES=5`、`configTIMER_TASK_PRIORITY=4`。
- `configTASK_NOTIFICATION_ARRAY_ENTRIES=1`（通知容量一的来源）。
- `configUSE_16_BIT_TICKS=0`（TickType_t 32 位，事件组 24 个可用位）。
- V11 默认关闭 `INCLUDE_vTaskDelay` 等 API；用哪个开哪个，缺了就是链接错误。

RT-Thread（`rtconfig.h`）：

- 开线程/调度/IPC/小内存堆/定时器，关设备框架、finsh、DFS；`src/` 只编 Nano 最小集。
- 场景 6 的优先级按 RT-Thread 语义：L=22、M=21、H=20（数字越小越高）；FreeRTOS 相反。
- 临界区必须是真 CPU 工作（`cpu_work_ms`）；写成 `rt_thread_mdelay` 会让信号量版与互斥量版结果相同。

### 3.4 F02：USE_MUTEX 的构建目录风险（未证实，不修）

- FreeRTOS Makefile 的 `BUILD` 不包含 `USE_MUTEX`；`CFLAGS` 追加 `-DUSE_MUTEX=1`，但目标文件只依赖 `Makefile` 与 `FreeRTOSConfig.h`。
  因此先 `make DEMO_SCENE=6`、再 `make DEMO_SCENE=6 USE_MUTEX=1`（不带 `-B`）时，make 可能复用旧对象，产出与源码不一致的镜像。
- RT-Thread 已把 `-mutex` 写进 `BUILD`，场景 6 的两版天然隔离。
- 本轮只做静态确认，**没有跑 0→1→0 切换试验**。规范不得写"所有参数变更均自动隔离"，也不得写"已修复"。
- 在证实前：手动构建互斥量版一律 `make -B DEMO_SCENE=6 USE_MUTEX=1`，或先 `rm -rf build/scene-6`；`firmware:check` 用 `-B`，不触发该缓存。

## 4. 校验与错误矩阵

| 事件 | 结果 |
|---|---|
| `DEMO_SCENE=0/7`（FreeRTOS）或 `2`（RT-Thread） | Makefile `$(error …)` 非零退出 |
| `scenes` 不在三种精确形状内 | `projects:check` 报"非法场景列表" |
| 内核源码目录不存在 | 编译期找不到头文件/`tasks.c`，失败；提示按 README 取源码 |
| 项目代码有警告 | `-Wall -Wextra` 下失败（内核源除外） |
| RT-Thread 缺 `__RT_KERNEL_SOURCE__` | 内部调度 API 不可见，编译失败 |
| 先普通构建再带 `USE_MUTEX` 且不带 `-B` | 可能复用旧对象（F02，未证实）；按 §3.4 强制重建 |
| 场景切换后产物相同 | `firmware:check` 非零退出 |
| 非法场景仍能 `flash` | `firmware:check` 非零退出 |
| 只编译成功就宣称"板上日志/时序通过" | 违规；上板状态必须另有证据 |

## 5. 正常、边界与失败案例

- 正常：`make DEMO_SCENE=2` → `build/scene-2/` 独立产物 → 上板看通知计数日志 → 回填观察。
- 边界：场景 1 和 6 都可能在 `build/scene-1`/`build/scene-6` 下存在旧产物；`firmware:check` 用 `-B` 强制重建，手动构建不保证。
- 边界：RT-Thread 5.x master 会漂移；引用具体行为时必须记录检出日期与 commit，或改读本地稀疏检出。
- 失败：把 ESP-IDF 的 `xTaskCreate` 栈单位/优先级上限套到上游 V11；两者配置与端口不同。
- 失败：用 `rt_thread_mdelay` 模拟临界区，得出"互斥量没有改善"；这是实验设计错误，不是内核结论。

## 6. 测试与断言

| 来源 | 已覆盖 |
|---|---|
| `npm run firmware:check` | 逐场景 `make -B DEMO_SCENE=n`；ELF 存在、Flash 起点、`Reset_Handler`/栈符号、bin 初始 SP 与复位向量；相邻场景不同、切回首场景字节一致、非法场景非零退出 |
| `tests/catalog.test.mjs` | `scenes` 形状/类型校验（当前只覆盖非法注册的一部分；见 quality-contract §6） |
| `code/rtos/00-why-rtos/probe.sh` 等 | 宿主机模型、反汇编、调度开销/优先级反转的离线对照 |
| `docs/lab/e04-priority-inversion.md` | 双 RTOS 的场景 6 对照表与理论时间线；上板实测仍 pending |

未覆盖：真实上下文切换时序、中断延迟、栈高水位、看门狗复位没有自动断言；只能上板测量并记录条件。

## 7. 错误与正确做法

- 错误：`make DEMO_SCENE=6` 后直接 `make DEMO_SCENE=6 USE_MUTEX=1`，相信 make 会因参数变化重编。正确：`-B` 或清目录（F02）。
- 错误：把 FreeRTOS V11 的 `INCLUDE_*` 默认值套到 IDF V10.5.1 SMP。正确：按各自配置头与版本分别核对。
- 错误：用 RT-Thread 的优先级数字方向解释 FreeRTOS 日志。正确：先确认"数值越大越高"还是"越小越高"。
- 错误：编译成功就写"实时性验证通过"。正确：编译只证明移植可构建；时序结论要上板或明确标为模型。
- 错误：把 RT-Thread master 写成"固定 5.x 某版本"。正确：未锁 revision 就如实写检出日期与分支，或补 tag/commit。

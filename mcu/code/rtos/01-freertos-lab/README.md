# 01-freertos-lab：一个工程，五个场景

配套章节：[F1 任务与 TCB](../../docs/rtos/freertos/01-task-tcb.md)、[F6 通知/事件组/定时器](../../docs/rtos/freertos/06-notify-event-timer.md)、[F7 堆](../../docs/rtos/freertos/07-heap.md)

## 这个工程回答什么

FreeRTOS 的机制不是背出来的，是**在串口日志里看出来的**。五个编译场景各自只演一件事：

| 场景 | 章节 | 看什么 |
|---|---|---|
| 1 | F1 | 任务创建后谁先跑（抢占）、`vTaskList` 的任务状态表 |
| 2 | F6 | 通知计数：消费比生产慢时 `ulTaskNotifyTake` 取走的是"欠账总数" |
| 3 | F6 | 事件组 ANY/ALL：同一组位上两种等待者，唤醒后统一清位 |
| 4 | F6 | 软件定时器：守护任务串行执行回调，慢回调拖累别的定时器 |
| 5 | F7 | heap_4：释放相邻块会合并，总空闲 ≠ 最大可分配块 |

## 内核版本与获取

- 上游 **FreeRTOS-Kernel V11.1.0**，`ARM_CM4F` 单核端口，内存分配用 `heap_4`。
- 与 ESP-IDF 内置的 **V10.5.1 SMP 修改版** 不同源：任务栈参数单位、调度结论、
  头文件行号都不能跨版本混读（P 篇用 IDF 那份，F 篇用这份）。

构建前先取内核源码（任意一种）：

```bash
# 推荐：放进仓库的忽略缓存（Makefile 默认从这里找）
mkdir -p .trellis/ref/freertos-v11
curl -L -o .trellis/ref/freertos-v11/kernel.tar.gz \
  https://codeload.github.com/FreeRTOS/FreeRTOS-Kernel/tar.gz/refs/tags/V11.1.0
cd .trellis/ref/freertos-v11 && tar -xzf kernel.tar.gz && mv FreeRTOS-Kernel-11.1.0 kernel

# 或者你已经有源码，构建时指路：
make FREERTOS_KERNEL=/path/to/FreeRTOS-Kernel
```

验证版本：`grep tskKERNEL_VERSION_NUMBER .trellis/ref/freertos-v11/kernel/include/task.h` 应为 `"V11.1.0"`。

## 构建

PATH 需要 `arm-none-eabi-gcc`、`mingw32-make`，以及 Git 的 `usr\bin`。

```bash
make DEMO_SCENE=1    # 1..5，默认 1
make DEMO_SCENE=1 flash # 场景参数同构建；OpenOCD + ST-Link
make clean
```

产物隔离在 `build/scene-1/` 至 `build/scene-5/`；切换场景无需 clean。`make DEMO_SCENE=2 flash` 只烧录场景 2，`make DEMO_SCENE=2 clean` 只清理场景 2。

验证状态：编译可验证；板上日志与时序仍待上板实测。

## 日志与预期观察

串口 115200 8N1（PA9 TX / PA10 RX），格式 `[tick] 标签 = 数字`：

- **场景 1**：`high` 每 100ms 一行、`low` 每 300ms 一行、每 2s 一张 `vTaskList` 表
  （能看到任务状态列 R/B 与剩余栈高水位）。
- **场景 2**：`took` 的值大多数时候是 1；把生产端 delay 改小就能看到 >1——
  这就是"计数语义"（欠的账攒着）与"覆盖语义"（xTaskNotify eSetValueWithOverwrite 丢掉旧的）的区别。
- **场景 3**：发 bit0 时只有 `ANY woke`；bit0+bit1 都置上后 `ALL woke` 才出现，
  而且两个等待者唤醒后位被**统一清掉**（不是先醒者独占）。
- **场景 4**：`fast cb` 本应每 100ms 一行；`slow cb` 每次磨蹭 ~50ms，你会看到
  排在它后面的 `fast cb` 晚一拍——守护任务串行执行回调的直接证据。
- **场景 5**：看 `boot free` → `after ABC` → `after free B`（总空闲涨了但 `big ok?=0`）
  → `after free A`（相邻块合并）→ `big ok?2=1`。**总空闲 ≠ 最大可分配块**。

## 关键配置（FreeRTOSConfig.h）

- `configTICK_RATE_HZ=1000`、`configMAX_PRIORITIES=5`、`configTIMER_TASK_PRIORITY=4`（守护任务跑最高）；
- `configTASK_NOTIFICATION_ARRAY_ENTRIES=1`——通知"容量一"由此而来；
- `configUSE_16_BIT_TICKS=0`——TickType_t 32 位，事件组 24 个可用位；
- `INCLUDE_*` 门控：**V11 内核默认把 vTaskDelay 等 API 全关掉**，用哪个开哪个，
  老工程升级最常见的链接错误就是这个。

## 失败排查

| 现象 | 多半是 |
|---|---|
| 链接报 `undefined reference to vTaskDelay` | `INCLUDE_vTaskDelay` 没开（V11 默认 0） |
| 链接报 `_kill`/`_getpid`/`_write` 未定义 | 缺 `syscalls.c` 的 newlib 桩（`vTaskList` 内部用 snprintf） |
| 串口乱码 | 时钟不是 16MHz HSI（BRR 按 16MHz 算）或对端参数不对 |
| 只有第一行日志 | 栈太小触发 `vApplicationStackOverflowHook`（会打印任务名） |
| 场景 4 回调一直不来 | `configUSE_TIMERS` 没开，或守护任务栈太小 |
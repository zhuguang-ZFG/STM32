# FreeRTOS 批次设计

## 版本与来源

- 内核：上游 `FreeRTOS/FreeRTOS-Kernel` tag **V11.1.0**，端口 `ARM_CM4F`（单核）。
- 明确边界：ESP-IDF 内置的 `components/freertos/FreeRTOS-Kernel` 头文件标记 “V10.5.1 (ESP-IDF SMP modified)”，其任务栈参数单位、SMP 调度结论与单核端口不同。F 篇任何行号、位域或优先级结论都不得跨到 P 篇。
- 缓存放 `.trellis/ref/freertos-V11.1.0/`（已忽略），记录 tag、下载方式与校验。构建时从缓存目录引用相对路径，不提交内核源码副本。

## 事实修复落点

| 编号 | 落点 | 处置 |
|---|---|---|
| F-F1 | F6 | 统一为 `ulTaskNotifyTake`；`xTaskNotifyTake` 不存在 |
| F-F2 | F6 | 删除无条件“快 45%”等性能断言；把“全替代、一对一/容量一、固定 24 位”改为按 `configUSE_16_BIT_TICKS`、`configTASK_NOTIFICATION_ARRAY_ENTRIES`、通知索引语义分别限定的表述 |
| F-F3 | F6 | 事件组清位解释改为：等待者列表逐个检查条件，满足者移出就绪；位在所有等待者检查完后按 `uxBitsToClear` 汇总清除，不存在“先唤醒者独占” |
| F-F4 | F7 | 动态任务栈确实来自堆，删除“栈不在堆里”的说法；`xPortGetMinimumEverFreeHeapSize` 定义为历史最小剩余量，不是碎片率；heap_2 的指标 API 逐文件核对后再写 |

## 配套工程

`code/rtos/01-freertos-lab`：自包含工程，编译开关 `DEMO_SCENE` 切换五个场景（任务/TCB、通知、事件组、软件定时器、堆）。沿用批次一的启动与链接脚本，`FreeRTOSConfig.h` 显式写出 `configTICK_RATE_HZ`、`configMAX_PRIORITIES`、`configUSE_PREEMPTION`、`configSUPPORT_STATIC_ALLOCATION` 等会影响结论的配置项，正文引用同一份配置。

构建：把内核 tasks/queue/list/event_groups/timers/croutine/stream_buffer 与 `portable/MemMang/heap_4.c` 编入；heap 场景需要 `configSUPPORT_DYNAMIC_ALLOCATION=1`。

日志走批次一的 USART1 打印封装，避免每章重复造轮子。

## 动画

沿用父任务动画合同。五张图的阶段必须与 `FreeRTOSConfig.h` 中的具体配置一致（例如通知数组长度、事件组位数、`configTIMER_TASK_PRIORITY` 与 `configTIMER_QUEUE_LENGTH`），图上出现数字的地方正文里也要出现同样的数字。

- `task-create-stack`：栈顶压入的初始现场 → TCB 初始化 → 加入就绪/延时列表 → 第一次恢复上下文。
- `task-notification`：发送者写值与状态位 → 目标任务在阻塞/就绪间的变化 → 取走与清零；计数语义（`eIncrement`）与覆盖语义（`eSetValueWithOverwrite` 等）分两条路径画。
- `event-group-wait`：ANY 与 ALL 两个等待者，位满足后统一汇总清位。
- `software-timer-service`：命令队列 → 守护任务 → 回调；回调串行执行导致其他定时器被推迟。
- `heap4-coalesce`：释放后插入空闲链表、相邻块合并、不相邻块留洞；总空闲字节与最大连续块并列显示。

## 上板实测

F 篇实测项：串口观察调度顺序与优先级反转、通知计数的累积值、事件组多等待者唤醒顺序、软件定时器回调抖动、堆剩余量曲线。霸天虎板上可做；无示波器时以日志时间戳（`vTaskDelay` 粒度）说明精度受限，不把日志推断写成实测波形。
# FreeRTOS：任务、通知事件定时器、堆内容与动画

## 目标与授权

父任务 [三路线内容深化与教学动画](../10-06-stm32-depth-animations/prd.md) 的第二批交付，依赖批次一已验收的启动与日志基础。用户已审阅父任务方案并确认开始实施（2026-10-06）。

## 交付范围

| 项 | 内容 |
|---|---|
| 章节 | `docs/rtos/freertos/01-task-tcb.md`（F1）、`06-notify-event-timer.md`（F6）、`07-heap.md`（F7）三篇成稿 |
| 新动画 | `task-create-stack`、`task-notification`、`event-group-wait`、`software-timer-service`、`heap4-coalesce` |
| 配套工程 | `code/rtos/01-freertos-lab`：一个工程按编译开关切换任务/通知/事件组/定时器/堆五个实验场景 |
| 同步 | `08-port-f407.md`（F8）补指向该工程的入口，不宣称本章成稿 |

## 需求

- **FR1 版本纪律**：全部内核结论以 **上游 FreeRTOS-Kernel V11.1.0** + `ARM_CM4F` 单核端口为准，逐条给文件与行级引用。不得与 ESP-IDF 内置的 SMP 修改版（头文件标记 V10.5.1）混读，也不得把 V10/V11 差异写成版本无关结论。
- **FR2 事实修复**：处理研究记录中归属本批次的缺陷 F-F1~F-F4（`ulTaskNotifyTake` 名称错误、无条件性能百分比、通知“全替代/一对一/固定 24 位”表述须限定、事件组清位不等于先唤醒者独占、动态任务栈来自堆与“不在堆里”矛盾、历史最小空闲量不等于碎片率、heap_2 指标 API 逐文件核对）。
- **FR3 因果链**：每章走通“调用 API → 内核对象变化 → 就绪/阻塞/内存状态 → 观察结果”，并指出观察手段（串口日志、`uxTaskGetSystemState`、`vTaskList`、`xPortGetFreeHeapSize`、`xPortGetMinimumEverFreeHeapSize`）。
- **FR4 可复现**：配套工程固定 V11.1.0 源码版本，给出获取方式、目录结构、构建命令与每个场景的预期输出；`xPortGetMinimumEverFreeHeapSize` 等指标 API 按实际文件逐个核对存在与否，不凭印象书写。
- **FR5 动画**：五张图分别表达“任务创建的栈与 TCB 分配”“通知的改值/取走语义与计数 vs 覆盖”“事件组 ANY/ALL 两类等待者与汇总清位”“软件定时器命令队列与守护任务串行回调”“heap_4 相邻块合并与最大可分配块”。

## 验收标准

- [ ] FA1 / FR1：三章内核结论逐条对应 V11.1.0 文件位置；无跨版本混用。
- [ ] FA2 / FR2：F-F1~F-F4 逐条处置。
- [ ] FA3 / FR3：三章各有“观察结果”落点，命令与工程实际输出一致。
- [ ] FA4 / FR4：工程在 arm-none-eabi-gcc 下 `-Wall -Wextra` 零错误构建；五个场景均可运行并有预期输出。
- [ ] FA5 / FR5：五张新动画被对应章节引用，无孤儿；XML/viewBox/字号/SMIL/浏览器目检通过。
- [ ] FA6：`npm run docs:build` 零错误。

## 范围边界

不覆盖 RT-Thread 章节、不改造播放器、不改站点导航结构。上游内核源码只放已忽略的缓存目录，不整体入库。

## 依赖

批次一（STM32）提供已验证的启动代码与串口日志基础；GNU Arm Embedded 工具链。
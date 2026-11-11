---
title: RTOS 篇导览
---

# RTOS 双精讲：FreeRTOS 与 RT-Thread

> 🎯 超级循环干到第 5 个任务就会明白：if 套 if 的"伪多任务"撑不过第二个需求变更。RTOS 给每个任务一个"平行世界"——而这层魔术的全部秘密，不过是栈、TCB 和一个叫 PendSV 的中断。

## 为什么学两个

| | FreeRTOS | RT-Thread |
|---|---|---|
| 地位 | 全球最流行内核，ESP-IDF 出厂自带 | 国产之光，中文生态与文档最友好 |
| 强项 | 内核小而精，源码 9 千行读得完 | 内核+设备框架+软件包，"自带生态" |
| 学什么 | 内核机制的**最小真相** | 组件化/驱动模型/工程化的**系统思维** |

两个都学完再对照——你会发现任务、调度、IPC 在每个 RTOS 里都是同一套思想的方言。

## 章节路线

**FreeRTOS 精讲（F 篇，内核源码级，基准 V11.x）**

| 编号 | 章节 | 一句话精髓 |
|---|---|---|
| F0 | [为什么需要 RTOS](freertos/00-why-rtos.md) | 亲手写一个必然失败的裸机调度 |
| F1 | [任务与 TCB](freertos/01-task-tcb.md)【成稿】 | xTaskCreate 逐行走查（动画 + 工程） |
| F2 | [上下文切换](freertos/02-context-switch.md)【成稿】 | PendSV 逐汇编指令（动画+视频） |
| F3 | [调度器](freertos/03-scheduler.md)【成稿】 | 位图就绪表与 tick 的真相 |
| F4 | [队列](freertos/04-queue.md)【成稿】 | 环形存储+两个阻塞列表 |
| F5 | [信号量与互斥](freertos/05-sem-mutex.md)【成稿】 | 优先级反转复现与继承（动画） |
| F6 | [通知/事件/软件定时器](freertos/06-notify-event-timer.md)【成稿】 | 通知计数 vs 覆盖、事件组汇总清位、守护任务（动画 x3 + 工程） |
| F7 | [内存管理](freertos/07-heap.md)【成稿】 | heap_1~heap_5 对比实验（动画 + 工程） |
| F8 | [移植到 F407](freertos/08-port-f407.md) | 三异常接管全记录 |

**RT-Thread 精讲（R 篇，基准 5.x）**

| 编号 | 章节 | 一句话精髓 |
|---|---|---|
| R0 | [架构与对象模型](rtthread/00-arch.md) | 分层架构与"万物皆对象" |
| R1 | [线程与调度](rtthread/01-thread-sched.md) | rt_thread 解剖与 256 级位图 |
| R2 | [IPC 全家桶](rtthread/02-ipc.md) | 对象容器+挂起列表的统一范式 |
| R3 | [内存管理](rtthread/03-mem.md) | memheap/slab/TLSF 与内存池 |
| R4 | [设备框架](rtthread/04-device.md) | 驱动与应用解耦的精髓 |
| R5 | [finsh 控制台](rtthread/05-finsh.md) | 符号表导出与命令解析 |
| R6 | [Env 与 menuconfig](rtthread/06-env-menuconfig.md) | scons+Kconfig 配置体系 |
| R7 | [移植到霸天虎](rtthread/07-port-f407.md) | Nano 手动移植→标准版两步走 |

**对照与选型**

| 编号 | 章节 | 一句话精髓 |
|---|---|---|
| 对比0 | [同概念双实现对照](compare/00-side-by-side.md) | 一张表看穿两个 OS |
| 对比1 | [选型决策树](compare/01-choose.md) | 什么项目选谁 |

## 先修建议

F 篇至少需要 [C6 栈帧](../c/06-abi-stack.md) + [S4 中断](../stm32/04-nvic-exti.md) + [S5 SysTick](../stm32/05-systick.md)；R 篇建议 F 篇之后进行。

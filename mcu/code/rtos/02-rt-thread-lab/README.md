# 02-rt-thread-lab：RT-Thread Nano 手动移植到霸天虎（F407）

对应章节：[R7 移植 RT-Thread 到霸天虎](../../docs/rtos/rtthread/07-port-f407.md)、
实验 [E04 优先级反转](../../docs/lab/e04-priority-inversion.md)（RT-Thread 版）。

## 这是什么

把 RT-Thread 5.x 内核用 **Nano 四件套**手动移植到野火霸天虎 F407
（R7 正文的"第一步"路线）：内核源码（src/ + libcpu）跨芯片通用、原样编译，
板卡知识全部收进 `board/board.c` 一个文件。不走标准版 BSP（设备框架/finsh/DFS）。

| 件 | 位置 | 说明 |
|---|---|---|
| 内核源码 | `.trellis/ref/rt-thread/src` + `libcpu/arm/cortex-m4` | 稀疏检出（仅内核），README 见下 |
| rtconfig.h | 工程根 | 裁剪配置：开线程/IPC/小内存堆，关设备框架 |
| board.c | `board/board.c` | rt_hw_board_init：HSI 16MHz + SysTick 1ms + 堆 |
| 链接脚本 | stm32f407xx.ld | `__bss_end__` 与 `_estack` 提供堆边界 |

## 构建与烧录

```bash
make                         # 场景 1：双线程异频闪灯（200ms vs 500ms，PF7/PF8）
make DEMO_SCENE=6            # 场景 6：优先级反转·信号量版（无继承）
make DEMO_SCENE=6 USE_MUTEX=1   # 场景 6：优先级反转·互斥量版（带继承）
make flash                   # 需要 openocd + stlink
make clean
```

产物 `build/scene-*/rt-thread-lab.bin`。三场景各自独立构建目录，切换无需 clean。

## 场景对照（E04 双跑）

| 场景 | 锁 | 现象 | 对照 01-freertos-lab |
|---|---|---|---|
| scene 6 默认 | `rt_sem_create` 信号量 | H 等锁时被 M 间接阻塞（反转） | `DEMO_SCENE=6` |
| scene 6 USE_MUTEX=1 | `rt_mutex_create` 互斥量 | L 持锁期间被继承抬级，M 插不进（修复） | `DEMO_SCENE=6 USE_MUTEX=1` |

注意优先级方向相反：**RT-Thread 数字越小优先级越高**，L=22 低、M=21、H=20 高；
FreeRTOS 正好相反（值越大越高）。E04 正文对照表有说明。

## 内核源码获取（.trellis/ref/rt-thread）

```bash
cd .trellis/ref
git clone --depth 1 --filter=blob:none --sparse https://github.com/RT-Thread/rt-thread.git rt-thread
cd rt-thread
git sparse-checkout set src include libcpu/arm/cortex-m4 include/klibc src/klibc
```

内核版本：RT-Thread master（2026-10，5.x）。`src/` 裁剪表（Nano 最小集）：

| 编译 | 文件 | 作用 |
|---|---|---|
| 是 | clock / scheduler_comm / scheduler_up / thread / idle / cpu_up / defunct | 调度与 tick |
| 是 | ipc | 信号量/互斥量/事件/邮箱/消息队列 |
| 是 | mem / object / timer / irq / kservice | 小内存堆、对象容器、定时器 |
| 是 | klibc/kstring.c kstdio.c rt_vsnprintf_std.c | rt_memset/rt_strlen/rt_snprintf |
| 否 | signal / memheap / mempool / slab / components | 标准版才需要 |

注意：内核源文件编译需 `-D__RT_KERNEL_SOURCE__`（内部调度 API 可见，官方 scons 同样注入）。

## 烧录后应见（R7 验收）

- scene 1：两线程异频闪灯（PF7 快 200ms、PF8 慢 500ms），串口打印 scene 标识
- scene 6：串口依次输出带毫秒时间戳的 `L take → L got lock → M burst start → H want lock → … → H got lock, waited N ms`（单次剧本，复位重演）；
  理论值：信号量版 H 等 ≈6000ms（M 的 4000ms 突发全部插在 L 和 H 之间），互斥量版 ≈2500ms（继承让 L 压住 M，H 只等 L 做完剩余临界区，不是 0）。推导见 [E04 理论时间线](../../../docs/lab/e04-priority-inversion.md)
- L 的临界区必须是真 CPU 工作（`cpu_work_ms`），写成 `rt_thread_mdelay` 会让两版结果相同；线程用 `spawn()` 创建并 `rt_thread_startup`，漏掉 startup 线程不会运行
- 上板实测结果待回填（`hardware_status: pending`），无实物时以模型/编译为准

## 对照参考

- R7 正文的异常接管表：PendSV/HardFault 由 `context_gcc.S` 强符号接管，本工程只写 SysTick
- 与 01-freertos-lab 的差异表：任务创建 API、优先级方向、时间片参数

> AI生成

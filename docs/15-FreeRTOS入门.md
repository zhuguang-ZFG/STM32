# 15 FreeRTOS 入门

> English: [FreeRTOS](en/15-freertos.md)

> FreeRTOS 把「一个大循环」拆成多个并发任务，用队列/信号量在任务间传递数据，让复杂项目的时序和逻辑不再互相打架。

<p align="center">
  <img src="../assets/animations/freertos-scheduler.svg" width="760" alt="FreeRTOS 任务状态迁移与抢占式调度">
  <br><sub>▲ 动画：FreeRTOS 任务状态迁移与抢占式调度（作者自绘矢量动画，非实拍）</sub>
</p>

<!-- video:ch15 -->
<p align="center">
  <video width="640" controls poster="../assets/video/ch15-rtos.png">
    <source src="../assets/video/ch15-rtos.mp4" type="video/mp4">
  </video>
  <br><sub>▲ 本章讲解视频（2.6 分钟）。<a href="../assets/video/ch15-rtos.mp4">MP4</a> · <a href="../assets/video/ch15-rtos.srt">字幕</a></sub>
</p>

<details>
<summary>旁白文字稿</summary>

1. 单核上没有真正的同时。FreeRTOS 让每件要长期做的事变成一个任务，各自有栈。调度器决定这一毫秒谁占用 CPU。你要为每个任务留够栈。
2. 两个任务优先级相同，时间片用完就换另一个。更高优先级的任务一旦就绪，可以抢过来。所以不是谁先创建谁就永远占着。
3. 普通延时是从现在起再睡一会儿，执行时间会累进误差。周期任务要用「下次几点醒」，把已经花掉的时间扣掉。节拍因此才稳。
4. 这一帧是仓库画的调度。任务在就绪、运行和阻塞之间转。阻塞往往是因为在等队列、信号量或延时。一直就绪又永远轮不到，先看有没有人优先级更高还不让出 CPU。
5. 信号量告诉你事情发生了。队列把数据搬过去。互斥量表示这会儿归我用。事件组用来等好几面旗一起到齐。够用时，任务通知可以少建一个对象。
6. 软件定时器的回调里不准睡觉，也不准等队列。它跑在定时器任务的上下文里，你一阻塞，别的定时器也停。需要等待的活，通知一个普通任务去做。
7. HAL 的延时默认也用 SysTick。FreeRTOS 也要这个节拍。两个都当主人，延时会卡住。用 Cube 时把 HAL 的时基改到别的定时器，这件事要在创建任务之前做完。
8. 口诀：相对延时是再等一会儿，绝对延时是下次几点醒。定时器回调里不准睡觉。信号量、队列、互斥，不要拿一个去代替另一个。
9. 实验做两个任务，两颗灯用不同的周期闪。如果一创建任务就进故障，先把栈调大，再看优先级。不要一开始就上五个队列。
10. 合上书，三问。两个同优先级任务，时间片用完会发生什么？周期任务该用哪种延时？软件定时器回调里可以等待队列吗？

</details>
<!-- /video:ch15 -->

## 学习目标

读这一章之前：读过第 04 章（中断与 NVIC，知道优先级数值和抢占是什么意思）、第 05 章（定时器）和第 06 章（会用串口打印），会用第 01 章的方法下载程序。C 语言的指针、`volatile` 和位运算不熟的话，先读第 00 章的「零基础预备」。

- [ ] 说出裸机大循环和 RTOS 多任务各适合什么项目，判断手上的项目该不该上 RTOS
- [ ] 画出任务的五种状态，说出每一条箭头由哪个函数调用或事件触发
- [ ] 说清 SysTick、PendSV、SVC 三个异常在 FreeRTOS 里各管什么，并把 HAL 时基换到 TIM4
- [ ] 按「任务优先级数值大的先跑、中断优先级数值小的先跑」配好任务和中断，算出 `0x50` 的来历
- [ ] 中断里只调用 FromISR 函数，说出互斥量为什么不能在中断里用
- [ ] 按「字」估算任务栈，用 `uxTaskGetStackHighWaterMark()` 量出还剩多少
- [ ] 为一件事选对通信对象：队列、信号量、互斥量、事件组、任务通知

## 核心原理

**一句话结论：FreeRTOS 把程序拆成几个各有自己栈的任务，调度器每次只让就绪任务里优先级最高的那一个占用 CPU，任务靠阻塞（等时间、等队列）把 CPU 让出来，中断只能用名字以 FromISR 结尾的函数和任务打交道。**

### 先打个比方

把 CPU 想成厨房里唯一的厨师，把任务想成一张张订单，调度器是安排顺序的领班。

- 每张订单有自己的灶台和案板，菜做到哪一步都留在上面。厨师被叫去做别的菜，回来还能接着做。这就是任务的栈。
- 领班只看两件事：哪张单子现在能做，哪张最急。最急的那张一能做，厨师马上放下手里的去做它，这叫抢占。一样急的几张单子轮流做，每张做一小会儿，这叫时间片。
- 炖汤要等半小时，这张单子先挂到一边，厨师去做别的；汤好了，领班再把它排回来。这叫阻塞。
- 门口的服务员是中断。服务员只负责把新订单放进传菜口（队列），不能站在厨房里等菜出锅。

比方到这里为止。真实的调度器不会「看情况」，它只按两条硬规则挑：处于就绪态，优先级数值最大；一样大时按节拍轮流。「放下手里的菜」也不是自然发生的，靠的是一个叫 PendSV 的异常把寄存器存进任务栈，第 4 节讲。

### 1. 裸机前后台和 RTOS：什么时候该换

RTOS 是 Real-Time Operating System（实时操作系统）的缩写。FreeRTOS 是其中常用的一种。它的内核只管调度、同步、计时和内存这几件事，文件系统和网络协议栈都不在内核里。

几个词先说清：

- **任务（task）**：一个永不返回的函数，加上它自己的一块栈。栈是任务存局部变量和「做到哪一步」的那块内存。
- **调度器（scheduler）**：内核里决定「下一刻谁用 CPU」的那段代码。
- **TCB（Task Control Block，任务控制块）**：内核给每个任务记的一张卡片，上面有它的优先级、状态和栈指针。

下表左右对比两种写法。从上往下读：前几行说结构，最后两行说代价和适用场合。

| 维度 | 裸机前后台 | FreeRTOS 多任务 |
| --- | --- | --- |
| 结构 | `while(1)` 主循环加中断 | 几个独立的任务，各写各的 |
| 并发 | 靠状态机和标志位手工拆开 | 调度器替你切换 |
| 等待 | 忙等或 `HAL_Delay`，等的时候 CPU 也在空转 | `vTaskDelay` 或阻塞等队列，等的时候 CPU 去跑别的任务 |
| 实时性 | 只能靠中断优先级，主循环里一件慢事拖慢所有事 | 更急的任务可以抢占 |
| RAM 开销 | 极小 | 每个任务一块栈和一个 TCB，再加内核自己的 |
| 适合 | 功能单一、资源很紧 | 多个外设同时干活、通信协议栈、逻辑复杂 |

判断标准：主循环里出现「好几件事都想按各自的节奏跑」时，就该考虑 RTOS。只是点灯加读串口，裸机足够。代价要算进去：本章例程给内核的堆留了 10240 字节（例程设定），这颗芯片的 SRAM 一共 20 KB，也就是 20480 字节（DS5319 Rev 20 表 2），堆已经占了一半。

### 2. 任务的五种状态

一个任务在任何时刻都处在下表的某一种状态。按「怎么进、怎么出」两列读，就能知道任务为什么在等：

| 状态 | 含义 | 怎么进来 | 怎么出去 |
| --- | --- | --- | --- |
| 运行 Running | 正在占用 CPU | 调度器选中它 | 被更高优先级的任务抢占或时间片到点（回到就绪）；调用延时或等待（进入阻塞）；被挂起 |
| 就绪 Ready | 随时能跑，在等 CPU | 刚创建；延时到期；等的事件到了；被抢占 | 调度器选中它 |
| 阻塞 Blocked | 在等时间或等事件 | `vTaskDelay`、`xQueueReceive`、`xSemaphoreTake` 等 | 超时，或事件到达 |
| 挂起 Suspended | 被人为暂停，不参与调度 | `vTaskSuspend` | `vTaskResume` |
| 删除 Deleted | 已经删掉 | `vTaskDelete` | — |

```text
        xTaskCreate
            │
            ▼
   ┌────► 就绪 Ready ◄──────────────────┐
   │        │     ▲                      │ 超时或事件到达
   │ 调度器 │     │ 被抢占 / 时间片到点   │
   │  选中  ▼     │                      │
   │      运行 Running ─────────────► 阻塞 Blocked
   │        │       延时、等队列、等信号量
   │        │ vTaskSuspend（就绪和阻塞的任务也能被挂起）
   │        ▼
   └──── 挂起 Suspended   （vTaskResume 回到就绪）

   vTaskDelete：任何状态都可以直接进入删除
```

CPU 换人只有三种时机：

1. 正在跑的任务自己阻塞或挂起，比如调用了 `vTaskDelay`。
2. 一个更高优先级的任务变成就绪，比如它等的队列来了数据。开了抢占（`configUSE_PREEMPTION = 1`）时，内核马上切过去。
3. 同优先级还有别的就绪任务，并且一个节拍到了。这叫时间片轮转，由 `configUSE_TIME_SLICING` 控制；不写时它默认是 1（FreeRTOS V11.3.2 的 `FreeRTOS.h`）。

如果优先级最高的任务是一个不阻塞的 `while(1)`，第 1 种和第 2 种时机永远不会来，比它低的任务全部「饿死」。删除也要留意：任务删除自己时，它的栈和 TCB 由空闲任务回收，所以空闲任务也不能一直被饿着。

### 3. 优先级：任务和中断方向相反

| 项 | 规则 |
| --- | --- |
| 优先级范围 | `0` 到 `configMAX_PRIORITIES − 1`。CubeMX 选 CMSIS_V1 接口时生成 `configMAX_PRIORITIES = 7` |
| 空闲任务 | 优先级 0，调度器启动时自动创建，没有别的任务可跑时它跑 |
| 抢占 | `configUSE_PREEMPTION = 1` 时，更高优先级的任务一就绪就立刻切换 |
| 时间片 | 同优先级的就绪任务每个节拍轮换一次 |
| 和中断的关系 | 中断不是任务。中断优先级数值越小越急（Cortex-M），方向和任务优先级相反 |

读这张表时记住一件事：任务之间比的是任务优先级，中断之间比的是 NVIC 优先级，中断和任务之间不用比，中断总是先跑。本章例程里 KEY 任务是 2，LED 和 UART 任务是 1，两边同时就绪时先跑 KEY。

STM32F103C8T6 的内核是 Cortex-M3，没有 FPU（Floating Point Unit，浮点运算单元）。CubeMX 给它选的是 FreeRTOS 的 ARM_CM3 移植。带 FPU 的 ARM_CM4F 移植在切换任务时会保存浮点寄存器，用的是 M3 不认识的指令，放到这颗芯片上不能用。

### 4. SysTick 与调度器：节拍和内核用的三个异常

**节拍（tick）**是内核计时的最小单位。SysTick 是 Cortex-M3 内核里一个 24 位的倒数计数器（PM0056 Rev 7 第 4.5 节）。内核把它设成每秒中断 `configTICK_RATE_HZ` 次。本章例程写的是 1000，一个节拍 1 ms。这是例程设定，也是 CubeMX 的默认值；内核本身没有默认值，`FreeRTOSConfig.h` 里必须写。72 MHz 主频下，一个节拍是 72 000 000 / 1000 = 72 000 个时钟，重装值写 71 999，24 位最大 16 777 215，装得下。

内核里的时间全部按节拍数。`pdMS_TO_TICKS(500)` 在 1000 Hz 下就是 500 个节拍。比一个节拍更短的期限，内核不保证。

下表是三个异常的分工。异常号和用途来自 PM0056 Rev 7 第 2.3.2 节表 16，优先级的设法来自 FreeRTOS V11.3.2 ARM_CM3 移植的 `port.c`：

| 异常 | 异常号 | FreeRTOS 里的用途 | 优先级 |
| --- | --- | --- | --- |
| SVC（SVCall） | 11 | 调度器启动时执行一条 `svc 0`，进入第一个任务 | 最高 |
| PendSV | 14 | 切换任务（上下文切换） | 最低 |
| SysTick | 15 | 节拍：节拍计数加 1，检查有没有任务到期；需要切换时挂起 PendSV | 最低 |

**上下文切换**就是「换一个任务接着跑」。进 PendSV 时，硬件已经把 R0–R3、R12、LR、PC、xPSR 这 8 个寄存器压进了当前任务的栈（PM0056 第 2.3.7 节）。PendSV 再把 R4–R11 压进去，把栈指针记进 TCB，然后取出下一个任务的栈指针，反向弹出它的寄存器。

PendSV 放在最低优先级，是为了让它等所有中断都处理完才执行，换任务永远不会插进一个中断函数的中间。中断里调用的 `portYIELD_FROM_ISR(pdTRUE)` 不会当场切换，它只是把 PendSV 挂起，等中断退出后 PendSV 再执行。

### 5. HAL 的时基为什么要换到 TIM4

HAL 库的 `HAL_Delay()` 和各个外设函数的超时都读 `HAL_GetTick()`。这个毫秒计数靠 `HAL_IncTick()` 每 1 ms 加一，默认由 SysTick 中断调用。FreeRTOS 也要 SysTick，冲突出在三处：

- CubeMX 生成的 `FreeRTOSConfig.h` 把 `xPortSysTickHandler` 定义成 `SysTick_Handler`，SysTick 中断整个交给内核。没人再调用 `HAL_IncTick()`，`HAL_Delay()` 就永远等不到时间。
- 调度器启动时，内核按自己的节拍重新设置 SysTick，并把它设成最低优先级。内核进临界区时会挡住数值 5–15 的中断（第 7 节），HAL 的节拍跟着被挡。
- 调度器启动之前，只要调用过一次内核函数（比如 `xQueueCreate`），内核就一直挡住数值 5–15 的中断，直到 `vTaskStartScheduler()`。这段时间里，挂在这些中断上的 HAL 节拍是停的。

把两边硬挤进同一个 SysTick 中断也能跑，旧版 CubeMX 就生成过这种写法：`SysTick_Handler` 里先调用 `HAL_IncTick()`，再调用内核的节拍函数。这时 HAL 的节拍跟着内核的优先级和启动时机走，不好控制，所以 CubeMX 在 FreeRTOS 工程里建议换掉 HAL 时基。

CubeMX 里的做法：SYS → Timebase Source 选 TIM4。CubeMX 会生成 `stm32f1xx_hal_timebase_tim.c`，让 TIM4 每 1 ms 中断一次；`main.c` 里的 `HAL_TIM_PeriodElapsedCallback()` 在 TIM4 到点时调用 `HAL_IncTick()`。这件事要在创建任务之前定下来。本章例程没有用 TIM4 做别的事，所以选它；你的工程里 TIM4 另有用途时，选一只空闲的定时器。

> [!TIP]
> 调度器启动之前，在 `xQueueCreate` 之类的内核函数和 `vTaskStartScheduler()` 之间不要调用 `HAL_Delay()`，除非 HAL 时基中断的优先级数值小于 5。

### 6. 延时：再等一会儿，还是下次几点醒

举个数：任务先干 3 ms 的活，再调用 `vTaskDelay(pdMS_TO_TICKS(10))`，一圈是 3 + 10，周期接近 13 ms。换成下面的写法，内核记住上一次醒来的时刻，每次只睡到「上次醒来 + 10 ms」，干活的 3 ms 被扣掉，周期是 10 ms：

```c
TickType_t last = xTaskGetTickCount();          /* 记下起点 */
for (;;)
{
    do_work();                                  /* 这里花掉的时间会从下一次睡眠里扣掉 */
    vTaskDelayUntil(&last, pdMS_TO_TICKS(10));  /* 每 10 ms 醒一次 */
}
```

`do_work()` 本身超过 10 ms 时，`vTaskDelayUntil` 不会睡，马上返回，周期就保不住了。

**软件定时器**用 `xTimerCreate` 创建，到点调用你给的回调函数，需要 `configUSE_TIMERS = 1`。所有回调都在同一个「定时器服务任务」（timer service task，也叫 daemon task）里依次执行。所以回调里不能阻塞：不能调用 `vTaskDelay`，不能带非零等待时间去等队列、信号量或一个可能被别人占着的互斥量。一个回调睡着了，其他所有软件定时器都跟着停。需要等待的活，在回调里通知一个普通任务去做。

口诀：**Delay 是「再等一会儿」，DelayUntil 是「下次几点醒」；定时器回调里不准睡觉。**

### 7. 临界区与中断优先级：中断里只用 FromISR

普通 API 可能让调用者阻塞，中断不是任务，没法阻塞。FromISR 版本从不等待：队列满了，`xQueueSendFromISR` 立即返回 `errQUEUE_FULL`。下表左边是任务里用的写法，右边是中断里对应的写法：

| 任务里用 | 中断里用 |
| --- | --- |
| `xQueueSend` | `xQueueSendFromISR` |
| `xQueueReceive` | `xQueueReceiveFromISR` |
| `xSemaphoreGive`（二值、计数信号量） | `xSemaphoreGiveFromISR` |
| `xSemaphoreGive`（互斥量） | 没有，互斥量不能在中断里用 |
| `xEventGroupSetBits` | `xEventGroupSetBitsFromISR` |
| `xTaskNotify` / `xTaskNotifyGive` | `xTaskNotifyFromISR` / `vTaskNotifyGiveFromISR` |
| `xTaskGetTickCount` | `xTaskGetTickCountFromISR` |

FromISR 函数的最后一个参数通常是 `pxHigherPriorityTaskWoken`。它被置成 `pdTRUE`，说明这次调用唤醒了一个比被打断的任务更急的任务。中断结尾把它交给 `portYIELD_FROM_ISR()`，中断一退出就切过去；不交，那个任务要等到下一个节拍才跑。

**0x50 是怎么来的。**STM32F1 的 NVIC 只实现了每个优先级字节的高 4 位，低 4 位读出来是 0，写了也无效（PM0056 Rev 7 第 4.3.7 节表 42）。所以 4 位优先级的 0–15，写进硬件寄存器时要左移 4 位。CubeMX 生成的 `FreeRTOSConfig.h` 里同一个意思有两种写法：

| 宏 | 值 | 给谁用 |
| --- | --- | --- |
| `configLIBRARY_MAX_SYSCALL_INTERRUPT_PRIORITY` | 5 | 不移位，给 `HAL_NVIC_SetPriority()` 对照用 |
| `configMAX_SYSCALL_INTERRUPT_PRIORITY` | 5 << (8 − 4) = 0x50 | 移位后的值，内核写进 BASEPRI 寄存器 |
| `configLIBRARY_LOWEST_INTERRUPT_PRIORITY` | 15 | 不移位，最低优先级 |
| `configKERNEL_INTERRUPT_PRIORITY` | 15 << 4 = 0xF0 | 内核自己的中断用的最低优先级 |

表里的 5 和 15 是 CubeMX 生成的值，不是内核规定的数。BASEPRI 是 Cortex-M3 的一个屏蔽寄存器：写入非零值后，处理器不再响应优先级数值大于等于它的异常（PM0056 第 2.1.3 节表 9）。内核进临界区时写 `BASEPRI = 0x50`，于是数值 5–15 的中断暂时进不来，数值 0–4 的照常响应。内核的数据结构因此只会被数值 5–15 的中断碰到，这些中断才准调用 FromISR。

下表按优先级数值把中断分成三段。配一个新中断时，先决定它要不要调用 FreeRTOS 函数，再从对应那一段里挑数：

| 抢占优先级数值 | 内核临界区挡不挡 | 能不能调用 FreeRTOS 函数 | 例子 |
| --- | --- | --- | --- |
| 0–4 | 不挡 | 一个都不能调用 | 要求极快响应、不和任务通信的中断 |
| 5–14 | 挡 | 只能调用 FromISR | 例程的 EXTI0 设成 5（例程设定） |
| 15 | 挡 | 只能调用 FromISR | 和 PendSV、SysTick 同级 |

**断言在查什么。**定义了 `configASSERT` 时，每个 FromISR 函数一开头都会核对两件事（`port.c` 的 `vPortValidateInterruptPriority`）：当前中断的优先级数值不小于 5；分组让 4 位全部用作抢占优先级。复位后所有中断的优先级都是 0，忘了调用 `HAL_NVIC_SetPriority()` 的中断一调用 FromISR 就停在断言里。`HAL_Init()` 已经把分组设成 `NVIC_PRIORITYGROUP_4`，之后不要再改。CubeMX 会定义 `configASSERT`；自己搭的工程没定义它时不会停，而是偶尔把内核的数据写坏，这种错误比断言难查得多。

### 8. 任务间通信：选对对象

几个对象先各用一句话说清：

- **队列（queue）**：一个能放 N 项、每项大小固定的缓冲区。发送时把数据按值复制进去，接收时再复制出来，所以发送方的局部变量发完就可以丢。`xQueueCreate(8, sizeof(uint8_t))` 是 8 项、每项 1 字节。
- **二值信号量（binary semaphore）**：只有「有」和「没有」两种状态的旗子，常用来让中断告诉任务「事情发生了」。
- **计数信号量（counting semaphore）**：能数到 N 的旗子，用来数空闲资源的个数，或者积攒还没处理的事件。
- **互斥量（mutex，mutual exclusion 的缩写）**：一把有主人的锁，谁拿走谁归还，带优先级继承（第 9 节）。
- **事件组（event group）**：一组标志位，任务可以等「这几位都到了」或「任一位到了」。节拍计数是 32 位时，一个事件组有 24 个可用位（FreeRTOS V11.3.2 `event_groups.h`）。
- **任务通知（task notification）**：每个任务自带的一个 32 位通知值，不用另建对象，但只能发给一个指定的任务。

下表横着比较。挑对象时先看「能不能传数据」和「中断里用什么」两列：

| 机制 | 用途 | 能否传数据 | 开销 | 中断里用什么 |
| --- | --- | --- | --- | --- |
| 队列 | 任务之间、中断到任务传数据 | 能，每项大小固定，按值复制 | 中 | `xQueueSendFromISR` |
| 二值信号量 | 事件同步，常见是中断通知任务 | 不能 | 小 | `xSemaphoreGiveFromISR` |
| 计数信号量 | 数资源、积攒事件 | 不能 | 小 | `xSemaphoreGiveFromISR` |
| 互斥量 | 保护共享资源，带优先级继承 | 不能 | 中 | 不能在中断里用 |
| 递归互斥量 | 同一个任务可以重复拿，拿几次还几次 | 不能 | 中 | 不能在中断里用 |
| 事件组 | 等多个事件（与、或） | 只能传标志位，32 位节拍时 24 位可用 | 小 | `xEventGroupSetBitsFromISR`，交给定时器服务任务代办 |
| 任务通知 | 轻量的点对点同步或传一个值 | 能，一个 32 位值 | 最小 | `xTaskNotifyFromISR` |

`xEventGroupSetBitsFromISR` 不在中断里直接置位，而是给定时器服务任务发一条消息，让它去置位，所以要同时打开 `configUSE_TIMERS` 和 `INCLUDE_xTimerPendFunctionCall`。

### 9. 优先级反转：互斥量和优先级继承

**优先级反转**的过程是这样：低优先级任务 L 拿着锁；高优先级任务 H 来要锁，只好阻塞；这时一个中优先级任务 M 就绪了，它比 L 急，于是抢走 CPU。L 拿不到 CPU 就还不了锁，H 实际上在等 M。

**优先级继承**是互斥量的补救办法：H 来要锁时，内核临时把 L 的优先级抬到和 H 一样，M 就插不进来；L 一还锁，优先级马上降回去。

| 概念 | 现象 | 对策 |
| --- | --- | --- |
| 优先级反转 | 高任务等低任务手里的资源，中任务却先跑了 | 用互斥量，不用二值信号量 |
| 优先级继承 | 低任务临时继承高任务的优先级，尽快还锁 | FreeRTOS 的互斥量自动做 |
| 死锁 | 两个任务各拿一把锁，互相等对方 | 所有任务按同一个顺序加锁；`xSemaphoreTake` 带超时，不要无限等 |

继承只能缩短等待，不能消除等待：H 最多还要等 L 把锁里那段代码做完。所以锁里只放最短的操作。互斥量记录了主人是哪个任务，中断不是任务，所以中断里不能拿也不能还互斥量。

### 10. 任务栈按字算，堆从 heap_1 到 heap_5

不同的写法单位不一样，抄代码时先认清是哪一种。下表第三列是「写 128 时实际得到多少」：

| 写法 | 栈参数的单位 | 写 128 得到 |
| --- | --- | --- |
| `xTaskCreate(fn, "X", 128, ...)` | 字 | 512 字节 |
| CMSIS-RTOS v1：`osThreadDef(name, fn, prio, 0, 128)` | 字（ST 的 `cmsis_os.c` 原样交给 `xTaskCreate`） | 512 字节 |
| CMSIS-RTOS v2：`osThreadAttr_t` 的 `.stack_size` | 字节（[CMSIS-RTOS2](#source-cmsis-640)） | 128 字节；CubeMX 生成的是 `128 * 4` |

估栈的办法：

| 方法 | 说明 |
| --- | --- |
| 经验值起步 | 简单任务 128 字；用到 `printf`、浮点格式化的 256–512 字（经验值） |
| 实测高水位 | `uxTaskGetStackHighWaterMark()` 返回任务运行以来栈最少还剩多少，单位也是字；接近 0 就要加大 |
| 局部大数组 | 函数里的大数组都在栈上，能改成 `static` 或全局就改 |
| 中断的开销 | Cortex-M3 上任务用 PSP（进程栈），中断函数一律用 MSP（主栈，PM0056 Rev 7 第 2.1.2 节）。中断进来时硬件先把 8 个寄存器、32 字节压进当前任务的栈；切换任务时 PendSV 再压 8 个。每个任务栈为这两组留出 64 字节，中断函数自己的局部变量和中断嵌套占的是主栈 |
| 溢出检测 | `configCHECK_FOR_STACK_OVERFLOW` 不写时是 0，什么都不查；设成 2，并实现 `vApplicationStackOverflowHook()` |

```c
/* 运行中查看某个任务还剩多少栈（单位：字） */
UBaseType_t free_words = uxTaskGetStackHighWaterMark(xTask);
```

任务的栈和 TCB、队列、互斥量都从内核的堆里分配。堆的大小是 `configTOTAL_HEAP_SIZE`，单位是字节。FreeRTOS 自带 5 种堆实现，入门用 heap_4：

| 实现 | 能否释放 | 碎片 | 说明 |
| --- | --- | --- | --- |
| heap_1 | 不能 | 没有 | 只分配不释放，任务建好就不再变的项目够用 |
| heap_2 | 能 | 严重 | 释放后不合并相邻空闲块，已不推荐 |
| heap_3 | 能 | 看标准库 | 包一层标准库的 `malloc`/`free`，调用时暂停调度器；堆大小由链接脚本决定，`configTOTAL_HEAP_SIZE` 对它不起作用 |
| heap_4 | 能 | 好，相邻空闲块会合并 | 最常用 |
| heap_5 | 能 | 好 | 和 heap_4 一样，还能把几块不连续的内存拼成一个堆 |

## 硬件与接线

| 开发板 | 外设 | 引脚 | 备注 |
| --- | --- | --- | --- |
| BluePill（STM32F103C8T6） | 板载 LED | PC13 | 板上已接，低电平点亮 |
| BluePill | 按键 | PA0 | 一端接 PA0，另一端接 GND；内部上拉，下降沿中断 |
| BluePill | USB-TTL | PA9（TX）/ PA10（RX） | 交叉连接加共地，115200-8-N-1 |
| BluePill | 外接 LED（实验一用） | PA1 | 串 270 Ω 到 GND，写 1 亮；270 Ω 沿用第 03 章的例程设定 |
| Nucleo-F411RE | 板载 | PA5（LD2）、PC13（B1） | 免外接；LD2 高电平亮（UM1724 Rev 17 第 7.6 节） |

```text
按键：    PA0 ──[按键]── GND             PA0 开内部上拉，按下读 0，产生下降沿
板载灯：  3.3 V ──[电阻]──▶|── PC13      写 0 亮
外接灯：  PA1 ──[270 Ω]──▶|── GND        写 1 亮（实验一）
串口：    PA9  (TX) ───────► USB-TTL 的 RX
          PA10 (RX) ◄─────── USB-TTL 的 TX
          GND ────────────── USB-TTL 的 GND
```

USB-TTL 选 3.3 V 电平的那一档。PA0 和 PA1 在 DS5319 Rev 20 表 5 里没有标 FT（5 V 容忍），按键和外接灯都只接 3.3 V 和 GND。Nucleo-F411RE 的内核是带 FPU 的 Cortex-M4F，CubeMX 会给它选 ARM_CM4F 移植；本章的数字都按 STM32F103C8T6 写。

本仓库完整示例见 [`examples/freertos-task/`](../examples/freertos-task/)，它的 `README.md` 列出了 CubeMX 的逐项配置。

## 代码实现

下面是 `main.c` 的全文：LED 任务闪灯，按键中断经队列交给按键任务，串口任务每秒打印一次心跳，两个任务共用的串口由互斥量保护。把它放进按例程 README 配好的 CubeMX 工程（FreeRTOS 选 CMSIS_V1，Timebase Source 选 TIM4，打开 USART1 和 EXTI line0 中断）就能编译。

```c
/* main.c —— 三任务 + 队列 + 互斥量 + FromISR（STM32F103C8T6，72 MHz） */
#include "stm32f1xx_hal.h"
#include "FreeRTOS.h"
#include "task.h"
#include "queue.h"
#include "semphr.h"
#include <stdio.h>
#include <string.h>

#define LED_PORT         GPIOC
#define LED_PIN          GPIO_PIN_13      /* 板载 LED，低电平点亮 */
#define KEY_PORT         GPIOA
#define KEY_PIN          GPIO_PIN_0       /* PA0 按键，按下接地 */

#define LED_TASK_STACK   128U             /* 单位：字（4 字节） */
#define KEY_TASK_STACK   192U
#define UART_TASK_STACK  256U
#define LED_TASK_PRIO    1U
#define KEY_TASK_PRIO    2U               /* 任务优先级：数值大的先跑 */
#define UART_TASK_PRIO   1U
#define KEY_QUEUE_LEN    8U               /* 最多缓存 8 个按键事件 */
#define KEY_IRQ_PRIO     5U               /* 中断优先级：不能小于 configLIBRARY_MAX_SYSCALL_INTERRUPT_PRIORITY */

UART_HandleTypeDef huart1;

static QueueHandle_t     g_key_queue  = NULL;   /* 中断 → 按键任务 */
static SemaphoreHandle_t g_uart_mutex = NULL;   /* 保护串口 */

static void SystemClock_Config(void);
static void bsp_init(void);
static void error_handler(void);
static void uart_print(const char *s);
static void vLedTask(void *argument);
static void vKeyTask(void *argument);
static void vUartTask(void *argument);

int main(void)
{
    HAL_Init();                 /* 分组设成 NVIC_PRIORITYGROUP_4，HAL 时基（TIM4）开始走 */
    SystemClock_Config();
    bsp_init();

    g_key_queue  = xQueueCreate(KEY_QUEUE_LEN, sizeof(uint8_t));
    g_uart_mutex = xSemaphoreCreateMutex();
    if ((g_key_queue == NULL) || (g_uart_mutex == NULL))
    {
        error_handler();        /* 堆不够：加大 configTOTAL_HEAP_SIZE */
    }

    if ((xTaskCreate(vLedTask,  "LED",  LED_TASK_STACK,  NULL, LED_TASK_PRIO,  NULL) != pdPASS) ||
        (xTaskCreate(vKeyTask,  "KEY",  KEY_TASK_STACK,  NULL, KEY_TASK_PRIO,  NULL) != pdPASS) ||
        (xTaskCreate(vUartTask, "UART", UART_TASK_STACK, NULL, UART_TASK_PRIO, NULL) != pdPASS))
    {
        error_handler();
    }

    vTaskStartScheduler();      /* 正常情况下不再返回 */
    error_handler();            /* 走到这里：堆连空闲任务都放不下 */
    return 0;
}

static void vLedTask(void *argument)
{
    (void)argument;
    for (;;)
    {
        HAL_GPIO_TogglePin(LED_PORT, LED_PIN);
        vTaskDelay(pdMS_TO_TICKS(500));         /* 阻塞 500 ms，把 CPU 让出去 */
    }
}

static void vKeyTask(void *argument)
{
    uint8_t key_id;
    char    msg[48];

    (void)argument;
    for (;;)
    {
        /* 队列空时一直阻塞，不占 CPU */
        if (xQueueReceive(g_key_queue, &key_id, portMAX_DELAY) == pdTRUE)
        {
            (void)snprintf(msg, sizeof(msg), "KEY %u pressed @%lu ms\r\n",
                           (unsigned)key_id, (unsigned long)xTaskGetTickCount());
            uart_print(msg);
        }
    }
}

static void vUartTask(void *argument)
{
    char     msg[64];
    uint32_t count = 0U;

    (void)argument;
    for (;;)
    {
        (void)snprintf(msg, sizeof(msg), "heartbeat %lu, tick=%lu\r\n",
                       (unsigned long)count++, (unsigned long)xTaskGetTickCount());
        uart_print(msg);
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
}

static void uart_print(const char *s)
{
    if (xSemaphoreTake(g_uart_mutex, pdMS_TO_TICKS(100)) == pdTRUE)   /* 最多等 100 ms */
    {
        (void)HAL_UART_Transmit(&huart1, (uint8_t *)s, (uint16_t)strlen(s), 100U);
        (void)xSemaphoreGive(g_uart_mutex);                          /* 用完马上还 */
    }
}

/* PA0 → EXTI0。EXTI0_IRQHandler 由 CubeMX 写在 stm32f1xx_it.c 里，它调用 HAL_GPIO_EXTI_IRQHandler，再回到这里 */
void HAL_GPIO_EXTI_Callback(uint16_t GPIO_Pin)
{
    if (GPIO_Pin == KEY_PIN)
    {
        uint8_t    key_id = 1U;
        BaseType_t woken  = pdFALSE;

        (void)xQueueSendFromISR(g_key_queue, &key_id, &woken);   /* 中断里只用 FromISR */
        portYIELD_FROM_ISR(woken);                               /* 唤醒了更急的任务就在退出时切换 */
    }
}

/* HAL 时基在 TIM4：CubeMX 生成的 stm32f1xx_hal_timebase_tim.c 让 TIM4 每 1 ms 中断一次 */
void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim)
{
    if (htim->Instance == TIM4)
    {
        HAL_IncTick();          /* HAL_Delay 和 HAL 的超时靠它走 */
    }
}

static void bsp_init(void)
{
    GPIO_InitTypeDef io = {0};

    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_GPIOC_CLK_ENABLE();
    __HAL_RCC_AFIO_CLK_ENABLE();                /* F1 的 EXTI 映射在 AFIO 里 */
    __HAL_RCC_USART1_CLK_ENABLE();

    io.Pin   = LED_PIN;
    io.Mode  = GPIO_MODE_OUTPUT_PP;
    io.Pull  = GPIO_NOPULL;
    io.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(LED_PORT, &io);
    HAL_GPIO_WritePin(LED_PORT, LED_PIN, GPIO_PIN_SET);   /* 先灭 */

    io.Pin  = KEY_PIN;
    io.Mode = GPIO_MODE_IT_FALLING;
    io.Pull = GPIO_PULLUP;
    HAL_GPIO_Init(KEY_PORT, &io);
    HAL_NVIC_SetPriority(EXTI0_IRQn, KEY_IRQ_PRIO, 0U);
    HAL_NVIC_EnableIRQ(EXTI0_IRQn);

    io.Pin   = GPIO_PIN_9;                      /* USART1_TX */
    io.Mode  = GPIO_MODE_AF_PP;
    io.Pull  = GPIO_NOPULL;
    io.Speed = GPIO_SPEED_FREQ_HIGH;
    HAL_GPIO_Init(GPIOA, &io);

    io.Pin  = GPIO_PIN_10;                      /* USART1_RX */
    io.Mode = GPIO_MODE_INPUT;
    io.Pull = GPIO_PULLUP;
    HAL_GPIO_Init(GPIOA, &io);

    huart1.Instance          = USART1;
    huart1.Init.BaudRate     = 115200U;
    huart1.Init.WordLength   = UART_WORDLENGTH_8B;
    huart1.Init.StopBits     = UART_STOPBITS_1;
    huart1.Init.Parity       = UART_PARITY_NONE;
    huart1.Init.Mode         = UART_MODE_TX_RX;
    huart1.Init.HwFlowCtl    = UART_HWCONTROL_NONE;
    huart1.Init.OverSampling = UART_OVERSAMPLING_16;
    if (HAL_UART_Init(&huart1) != HAL_OK)
    {
        error_handler();
    }
}

static void SystemClock_Config(void)            /* HSE 8 MHz × 9 = 72 MHz，APB1 36 MHz */
{
    RCC_OscInitTypeDef osc = {0};
    RCC_ClkInitTypeDef clk = {0};

    osc.OscillatorType = RCC_OSCILLATORTYPE_HSE;
    osc.HSEState       = RCC_HSE_ON;
    osc.HSEPredivValue = RCC_HSE_PREDIV_DIV1;
    osc.PLL.PLLState   = RCC_PLL_ON;
    osc.PLL.PLLSource  = RCC_PLLSOURCE_HSE;
    osc.PLL.PLLMUL     = RCC_PLL_MUL9;
    if (HAL_RCC_OscConfig(&osc) != HAL_OK)
    {
        error_handler();
    }

    clk.ClockType      = RCC_CLOCKTYPE_HCLK | RCC_CLOCKTYPE_SYSCLK |
                         RCC_CLOCKTYPE_PCLK1 | RCC_CLOCKTYPE_PCLK2;
    clk.SYSCLKSource   = RCC_SYSCLKSOURCE_PLLCLK;
    clk.AHBCLKDivider  = RCC_SYSCLK_DIV1;
    clk.APB1CLKDivider = RCC_HCLK_DIV2;
    clk.APB2CLKDivider = RCC_HCLK_DIV1;
    if (HAL_RCC_ClockConfig(&clk, FLASH_LATENCY_2) != HAL_OK)
    {
        error_handler();
    }
}

static void error_handler(void)
{
    __disable_irq();
    for (;;) { }
}

/* configCHECK_FOR_STACK_OVERFLOW 设成 2 时，内核发现某个任务栈越界就调用它 */
void vApplicationStackOverflowHook(TaskHandle_t xTask, char *pcTaskName)
{
    (void)xTask;
    (void)pcTaskName;           /* 在这里打断点，pcTaskName 就是越界的任务名 */
    __disable_irq();
    for (;;)
    {
        HAL_GPIO_TogglePin(LED_PORT, LED_PIN);               /* 快闪报警 */
        for (volatile uint32_t i = 0U; i < 200000U; i++) { }
    }
}
```

`FreeRTOSConfig.h` 由 CubeMX 生成，和本章有关的是下面几行。`configTOTAL_HEAP_SIZE` 和 `configCHECK_FOR_STACK_OVERFLOW` 两行要在 CubeMX 的 FreeRTOS 参数页里改成这里的值，其余是 CubeMX 生成值：

```c
#define configUSE_PREEMPTION                         1
#define configCPU_CLOCK_HZ                           ( SystemCoreClock )
#define configTICK_RATE_HZ                           ( ( TickType_t ) 1000 )
#define configMAX_PRIORITIES                         ( 7 )
#define configMINIMAL_STACK_SIZE                     ( ( uint16_t ) 128 )      /* 空闲任务的栈，单位：字 */
#define configTOTAL_HEAP_SIZE                        ( ( size_t ) 10240 )      /* 单位：字节；例程要求不小于 10240 */
#define configCHECK_FOR_STACK_OVERFLOW               2                         /* 不写时是 0 */

#ifdef __NVIC_PRIO_BITS
 #define configPRIO_BITS                             __NVIC_PRIO_BITS         /* F1 是 4 */
#else
 #define configPRIO_BITS                             4
#endif
#define configLIBRARY_LOWEST_INTERRUPT_PRIORITY      15
#define configLIBRARY_MAX_SYSCALL_INTERRUPT_PRIORITY 5
#define configKERNEL_INTERRUPT_PRIORITY      ( configLIBRARY_LOWEST_INTERRUPT_PRIORITY << (8 - configPRIO_BITS) )      /* 0xF0 */
#define configMAX_SYSCALL_INTERRUPT_PRIORITY ( configLIBRARY_MAX_SYSCALL_INTERRUPT_PRIORITY << (8 - configPRIO_BITS) ) /* 0x50 */
#define configASSERT( x ) if ((x) == 0) { taskDISABLE_INTERRUPTS(); for( ;; ); }

#define vPortSVCHandler     SVC_Handler          /* 三个异常交给内核 */
#define xPortPendSVHandler  PendSV_Handler
#define xPortSysTickHandler SysTick_Handler
```

逐段看：

- `HAL_Init()` 做了两件和本章有关的事：把优先级分组设成 `NVIC_PRIORITYGROUP_4`，并通过 CubeMX 生成的 `HAL_InitTick()` 让 TIM4 开始走 1 ms 的 HAL 时基。
- 队列和互斥量先于任务创建。返回 `NULL` 说明堆不够，这时还没有任务在跑，直接停下最好查。
- `xTaskCreate` 的第三个参数是栈深度，单位是字；第五个参数是任务优先级。三个任务都没保存句柄，所以最后一个参数写 `NULL`。
- `vTaskStartScheduler()` 会创建空闲任务（打开软件定时器时还有定时器服务任务），按 1000 Hz 设好 SysTick，再用 SVC 进入第一个任务。它返回，只能是堆连空闲任务都放不下。
- 每个任务都是一个不返回的 `for (;;)`，里面都有一个阻塞调用：`vTaskDelay` 或 `xQueueReceive`。去掉它，比这个任务优先级低的任务就再也轮不到。
- `uart_print()` 拿不到锁时最多等 100 ms，超时这一行就不打印了。互斥量包住的是整次 `HAL_UART_Transmit`，一行字不会被另一个任务从中间切开。
- `HAL_GPIO_EXTI_Callback()` 运行在中断里，所以用 `xQueueSendFromISR`，最后把 `woken` 交给 `portYIELD_FROM_ISR()`。KEY 任务优先级是 2，比被打断的任务急，中断一退出就轮到它。
- `KEY_IRQ_PRIO` 是 5，正好等于 `configLIBRARY_MAX_SYSCALL_INTERRUPT_PRIORITY`。写成 0 到 4，按一下键就停在 `configASSERT`。
- `HAL_TIM_PeriodElapsedCallback()` 在 TIM4 到点时调用 `HAL_IncTick()`，`HAL_Delay()` 和 HAL 的超时才会走。

> [!TIP]
> 例程 `examples/freertos-task/main.c` 里没有 `HAL_TIM_PeriodElapsedCallback()`，却自带一个 `EXTI0_IRQHandler()`。按例程 README 用它覆盖 CubeMX 的 `main.c` 时，要把上面这个回调补回来，否则 HAL 的毫秒计数不走；CubeMX 在 `stm32f1xx_it.c` 里也生成了 `EXTI0_IRQHandler()` 时，两处只留一处，否则链接时报重复定义。

几句宏背后的寄存器操作，读内核源码时对得上号：

```c
/* HAL_NVIC_SetPriority(EXTI0_IRQn, 5, 0) 在分组 4 下写的是这个字节： */
NVIC->IP[EXTI0_IRQn] = (uint8_t)(5U << (8U - __NVIC_PRIO_BITS));   /* 0x50 */

/* portYIELD_FROM_ISR(pdTRUE) 在 ARM_CM3 移植里就是挂起 PendSV： */
SCB->ICSR = SCB_ICSR_PENDSVSET_Msk;

/* 内核进临界区时做的事：只挡数值 5–15 的中断，0–4 照常响应 */
__set_BASEPRI(configMAX_SYSCALL_INTERRUPT_PRIORITY);               /* 0x50 */
```

完整工程见 [`examples/freertos-task/`](../examples/freertos-task/)。

## 动手实验

1. **实验一：两个任务，两种节奏。** 再建一个任务，每 200 ms 翻转 PA1 上的外接灯；原来的 LED 任务每 500 ms 翻转 PC13。
   - 预期现象：PC13 的灯 1 s 闪一次，PA1 的灯 0.4 s 闪一次，各走各的，互不干扰。
   - 怎么确认：数 10 s 里的闪烁次数，PC13 是 10 次，PA1 是 25 次；有逻辑分析仪就量周期，应接近 1.000 s 和 0.400 s。
   - 没成功先查：新任务的栈够不够（先给 128 字）；两个任务里有没有 `vTaskDelay`；HAL 时基是不是 TIM4；PA1 的端口时钟和推挽输出配了没有。
2. **实验二：队列传按键。** 用上面的完整程序，按 PA0 的键。
   - 预期现象：每按一次，串口多一行 `KEY 1 pressed @… ms`；不按时只有每秒一行的心跳。机械键没有消抖，偶尔一按出两三行。
   - 怎么确认：串口助手设 115200-8-N-1；两次按键之间，`@` 后面的毫秒数和你按键的间隔对得上。
   - 没成功先查：一按就死机，先看 EXTI0 的优先级数值是不是 5（停在 `configASSERT`）；AFIO 时钟和 PA0 的上拉开了没有；`EXTI0_IRQHandler()` 是不是只有一份。
3. **实验三：有锁和没锁。** 让 LED 任务和 UART 任务都去打印一行 80 个字符的长串。先把 `uart_print()` 里的互斥量去掉，并改成一个字符调用一次 `HAL_UART_Transmit`；再恢复互斥量。
   - 预期现象：没锁时，两个任务的字符互相穿插；加锁后每行完整。
   - 怎么确认：115200 下一个字节 10 位，约 86.8 µs，80 个字符约 6.9 ms，跨过好几个 1 ms 的节拍，同优先级的两个任务会在中间轮换，穿插很容易看到。
   - 没成功先查：没锁也看不到穿插，多半是串太短或两个任务没有同时打印，把串加长。整串一次 `HAL_UART_Transmit` 时看到的不是穿插，而是整行丢失：后来的那次调用发现串口正忙，直接返回 `HAL_BUSY`。
4. **实验四：复现栈溢出。** 把 `configCHECK_FOR_STACK_OVERFLOW` 设成 2，把 LED 任务的栈改成 64 字（256 字节），在任务里放一个局部数组 `volatile uint8_t buf[200]`，用 `for` 循环把它写满。
   - 预期现象：板载灯开始快闪，说明进了 `vApplicationStackOverflowHook()`。
   - 怎么确认：在钩子里打断点，`pcTaskName` 是 `"LED"`。
   - 没成功先查：`configCHECK_FOR_STACK_OVERFLOW` 还是 0 时钩子永远不会被调用，程序多半直接进 HardFault；数组不加 `volatile`、写了又不用，可能被编译器整段优化掉。
5. **实验五：看一次优先级反转。** 建三个任务：L（优先级 1）拿锁后忙 50 ms 再还锁；H（优先级 3）在 L 拿锁后要同一把锁；M（优先级 2）在这时就绪，连续忙 200 ms 不阻塞。锁先用 `xSemaphoreCreateBinary()`，再换成 `xSemaphoreCreateMutex()`。这几个毫秒数都是例程设定。
   - 预期现象：用二值信号量时，H 等锁的时间里多出 M 的那 200 ms；换成互斥量，H 最多只等 L 剩下的那段。
   - 怎么确认：在 H 里于 `xSemaphoreTake` 前后各读一次 `xTaskGetTickCount()`，相减就是等待的节拍数，打印出来比较。
   - 没成功先查：二值信号量创建后是「空」的，要先 `xSemaphoreGive` 一次才能当锁用；三个任务的启动顺序要保证 L 先拿到锁。

## 自测

1. 一个任务先干 3 ms 的活，再调用 `vTaskDelay(pdMS_TO_TICKS(10))`，周期更接近 10 ms 还是 13 ms？换成 `vTaskDelayUntil(&last, pdMS_TO_TICKS(10))` 呢？
2. 优先级 3 的任务和优先级 1 的任务同时就绪，FreeRTOS 先跑哪一个？如果优先级 3 的任务里是一个不阻塞的 `while(1)`，优先级 1 的任务会怎样？
3. USART1 的接收中断写成 `HAL_NVIC_SetPriority(USART1_IRQn, 3, 0)`，里面调用 `xQueueSendFromISR`，会发生什么？最小该改成几？对应到 BASEPRI 是哪个数？
4. LED 128 字、KEY 192 字、UART 256 字，三块栈一共多少字节？CMSIS-RTOS v2 里把 `.stack_size` 写成 256，任务实际有多少字的栈？
5. 软件定时器的回调里调用 `vTaskDelay(100)`，除了这个回调自己，还会拖住谁？

参考答案：

1. 接近 13 ms。`vTaskDelay` 从调用那一刻再等 10 个节拍，干活的 3 ms 加在前面：3 + 10 = 13。`vTaskDelayUntil` 从上一次醒来的时刻算，干活的时间被扣掉，周期是 10 ms。
2. 先跑优先级 3 的，任务优先级数值大的先跑。它不阻塞，优先级 1 的任务就永远轮不到：调度器只在更高优先级的任务全部阻塞或挂起时，才把 CPU 给低的。
3. 定义了 `configASSERT`（CubeMX 会定义）时，停在断言里；没定义时不会停，但这个中断可能在内核改队列的半路闯进来，把数据写坏。3 小于 5，这个中断比内核能挡住的最急的一级还急，内核进临界区时挡不住它。最小改成 5，抢占优先级数值在 5 到 15 之间都可以。对应 BASEPRI 的数是 `5 << 4 = 0x50`。
4. 128 + 192 + 256 = 576 字，576 × 4 = 2304 字节，大约是 20480 字节 SRAM 的 11%。它们都从 10240 字节的堆里分配，占掉堆的 2304 / 10240 = 22.5%，再加上 TCB、空闲任务的 128 字、队列和互斥量，堆还有富余。`.stack_size` 的单位是字节，256 字节 / 4 = 64 字，只有想要的四分之一；要 256 字就写 `256 * 4`。
5. 拖住所有软件定时器。回调都在同一个定时器服务任务里依次执行，它睡 100 ms，其他到点的定时器回调都要往后排；`xTimerStart` 之类的命令也要等它醒来才处理。

## 原理与适用范围

> [!NOTE]
> 从这一节到「常见坑与出处」是深入部分，把前面的结论落到具体订货号、手册章节和能复算的数字上。第一次读可以先跳过，做完动手实验再回来对照。

前面讲的规则对跑 FreeRTOS 的 Cortex-M3 都成立。具体的数要落到一颗芯片和一个工程上，本章用的是 STM32F103C8T6 和本仓库的 `examples/freertos-task`。

**订货号和分组。**这一章的节拍和 FromISR 只钉在订货号 STM32F103C8T6 上。分组跟第 04 章是同一个：`NVIC_PRIORITYGROUP_4`，4 位全给抢占优先级，0 位子优先级。`HAL_Init()` 设好它以后不要再改；FreeRTOS 要求优先级位全部用作抢占，改了分组会停在 `configASSERT`。

**节拍。**`configTICK_RATE_HZ = 1000`，一个节拍是 1 ms。这是例程设定，短于 1 ms 的期限不是内核保证。SysTick 归内核。HAL 的时基是 TIM4，也就是 `examples/freertos-task` 的 README 已经写明的那一只。SysTick 交给了内核、HAL 又没换时基时，`HAL_Delay` 会卡住。见 [本仓库例程](#source-project-examples)。

**优先级的方向。**任务优先级数值大的先跑。例程里 KEY 是 2，LED 和 UART 是 1，同时就绪时先跑 KEY。NVIC 仍是数值小的更急。把任务优先级当成 NVIC、以为 1 比 2 先跑，整个顺序就配反了。空闲任务是 0。

**0x50 的来历。**`5 << (8 − 4) = 0x50`。F1 的优先级只有高 4 位有效（[PM0056](#source-pm0056) 表 42），所以 4 位的 5 写进寄存器要左移 4 位。调用 FromISR 的中断，抢占优先级数值要大于等于 5。例程把 `EXTI0` 设成 5。设成 0，也就是复位后的默认值，会停在 `configASSERT`；数值 4 同样过急。内核进临界区时把 BASEPRI 写成 `0x50`，挡住数值 5–15 的中断，0–4 的不受影响（[FreeRTOS 的 Cortex-M 说明](#source-freertos-priority)）。见 [FreeRTOS Kernel V11.3.2](#source-freertos-syscall)。

**栈的单位。**`xTaskCreate` 的栈深度是字，一字 4 字节。LED 128 字 = 512 字节。KEY 192 字 = 768 字节。UART 256 字 = 1024 字节。把 128 读成 128 字节，栈就只剩想要的四分之一。

**延时和锁。**先干 3 ms 再 `vTaskDelay(10)`，从调用时再等 10 个节拍，周期接近 13 ms。`vTaskDelayUntil` 的 10 ms 把周期钉在 10 ms。保护共享资源用互斥量，它有优先级继承；二值信号量没有。heap_4 会合并相邻的空闲块。

**换芯片时。**这颗料没有 FPU，用的是 ARM_CM3 移植。换到 F4 这类带 FPU 的 Cortex-M4F 时，要换成 ARM_CM4F 移植，并按那颗芯片编程手册里的优先级位数重新算 `configMAX_SYSCALL_INTERRUPT_PRIORITY`。

## 关键插图

<p align="center">
  <img src="../assets/diagrams/sample-15-rtos-prio.svg" width="760" alt="一个 tick 是 1 ms；任务优先级 2 先于 1；128 字是 512 字节；FromISR 的数值优先级要大于等于 5">
  <br><sub>▲ 自绘。STM32F103C8T6。正常路径是 SysTick 1 ms、HAL 时基 TIM4、优先级 2 在跑、优先级 1 在等、LED 栈 128 字 = 512 字节、EXTI0 抢占优先级 5。失败路径是同一条 EXTI 的抢占优先级写成 0，调用 FromISR 后停在 configASSERT。出处是 [FreeRTOS Kernel V11.3.2](#source-freertos-syscall) 和 [freertos-task](#source-project-examples)。</sub>
</p>

<p align="center">
  <img src="../assets/gif/rtos-tick.gif" width="640" alt="节拍每 1 ms 走一格，优先级 2 占着 CPU，128 字等于 512 字节">
  <br><sub>▲ 网页和公众号辅图。只播放正常路径：1 ms 一格，优先级 2 在跑，优先级 1 在等，128 words = 512 bytes。印刷以静态主图为准。configASSERT 和 SysTick 冲突不在这条 GIF 上。</sub>
</p>

静态图从上往下读。顶上三行是本章的三组数：没有 FPU 的 Cortex-M3 和 `GROUP_4`，节拍 1 ms、HAL 时基 TIM4，`5 << 4 = 0x50`。中间「正常路径」一栏是优先级 2 的任务在跑、优先级 1 的任务在等，LED 栈 128 字 = 512 字节。再往下「失败路径」一栏把 EXTI0 的优先级数值写成 0，第一次调用 FromISR 就停在断言里。最下面的「旁注」列了三种常见误读：把字当字节，HAL 留在 SysTick 上，把任务优先级当成 NVIC 的方向。GIF 只演正常路径。章首的 `freertos-scheduler.svg` 是会动的状态迁移图，和第 2 节的状态表对照着看。

## 时序与状态

下表把本章的几个数排在一起，每一格都能用前面的公式算回去。数字来自 [freertos-task 例程](#source-project-examples) 和 [FreeRTOS Kernel V11.3.2](#source-freertos-syscall)：

| 对象 | 数值 | 谁先走 |
| --- | --- | --- |
| 节拍 | 1000 Hz | 一个节拍 1 ms |
| 任务 | 优先级 2 与优先级 1 | 2 先于 1，方向和 NVIC 相反 |
| 栈 | 128 字 = 512 字节 | KEY 192 字 = 768 字节，UART 256 字 = 1024 字节 |
| 中断 | 数值 5 可以调用 FromISR | 数值 0 停在 `configASSERT`；`0x50 = 5 << 4` |
| 时基 | 内核用 SysTick | HAL 用 TIM4 |
| 延时 | 干 3 ms 再 `vTaskDelay(10)` | 周期接近 13 ms；`vTaskDelayUntil` 的 10 ms 仍是 10 ms |

按一次键，CPU 依次经过下面几步。最后一列是这一步谁在用 CPU：

| 步骤 | 发生了什么 | 谁在跑 |
| --- | --- | --- |
| 1 | PA0 出现下降沿，EXTI0（数值 5）进中断 | 当时在跑的任务被打断，多半是空闲任务 |
| 2 | `xQueueSendFromISR` 把 1 字节复制进队列，KEY 从阻塞变就绪，`woken` 变成 `pdTRUE` | EXTI0 的中断函数 |
| 3 | `portYIELD_FROM_ISR(woken)` 挂起 PendSV | EXTI0 的中断函数 |
| 4 | EXTI0 退出，最低优先级的 PendSV 接着执行，保存被打断任务的寄存器，换上 KEY 的 | PendSV |
| 5 | KEY（优先级 2）从 `xQueueReceive` 返回，拿互斥量，打印一行 | KEY 任务 |
| 6 | KEY 回到 `xQueueReceive` 再次阻塞，CPU 交还给就绪任务里最高的那个 | LED、UART 或空闲任务 |

## 常见坑与出处

每一行从左往右读：先认现象，再看原因和处理；最后两列写这条结论出自哪里，以及那份出处能证明到哪一步。

| 现象 | 原因 | 处理 | 出处 | 出处能证明的部分 |
| --- | --- | --- | --- | --- |
| `HAL_Delay` 卡住，或调度器起不来 | HAL 和内核都要 SysTick | HAL 时基换到 TIM4 | [本仓库例程](#source-project-examples) | `examples/freertos-task` 的 README 把时基源写成 TIM4 |
| 一进中断就停在 `configASSERT` | 抢占优先级数值比 5 小 | `EXTI0` 写成 5 到 15 之间的数 | [FreeRTOS](#source-freertos-syscall) | 4 位优先级时，5 左移 4 位是 `0x50`；数值更小的中断不得调用 FromISR |
| 优先级 1 的任务压过优先级 2 | 把任务优先级当成了 NVIC | 任务优先级数值大的先跑 | [FreeRTOS](#source-freertos-syscall) | 任务优先级数值更大的先跑 |
| 例程里 KEY 没有压过 LED | 两个任务写成了同一个优先级 | KEY 写 2，LED 和 UART 写 1 | [本仓库例程](#source-project-examples) | `examples/freertos-task` 里 KEY 的任务优先级是 2，LED 和 UART 是 1 |
| 栈写的是 128，一打印就溢出 | 把字当成了字节 | 128 的单位是字，等于 512 字节 | [本仓库例程](#source-project-examples) | LED 128 字，KEY 192 字，UART 256 字 |
| 按键中断一进来就断言 | EXTI 的抢占优先级过急，或者根本没设、停在复位值 0 | `EXTI0` 的抢占优先级写成 5 | [本仓库例程](#source-project-examples) | 例程把 `EXTI0` 的抢占优先级设成 5 |
| 断言停在核对分组的那一条 | 分组不是 4 位全给抢占 | `HAL_Init()` 之后不要再改分组 | [PM0056](#source-pm0056) | 表 45：PRIGROUP 决定抢占位和子优先级位从哪里分开 |
| 两个任务的串口输出互相穿插，或整行丢失 | 两个任务同时写一个串口，没有加锁 | 用互斥量包住整次发送 | [本仓库例程](#source-project-examples) | `examples/freertos-task` 用互斥量保护 `uart_print` |
| 用二值信号量当锁，高优先级任务偶尔等很久 | 二值信号量没有优先级继承，中优先级任务插进来 | 换成 `xSemaphoreCreateMutex()` | [FreeRTOS](#source-freertos-syscall) | 互斥量有优先级继承。二值信号量没有 |
| 周期越来越长 | `vTaskDelay(10)` 不包含调用前已经花掉的时间 | 固定周期用 `vTaskDelayUntil` | [FreeRTOS Kernel V11.3.2](#source-freertos-1132) | `vTaskDelay` 的时间从调用那一刻算起 |

CPU 利用率和截止时间的预算没有放进这张表，它们在第 28 章。按键抖动也没有放进来：消抖时间是经验值，FreeRTOS 和 ST 的手册里都没有这个数。

## 相关资源

- FreeRTOS 官方文档与《Mastering the FreeRTOS Real Time Kernel》（任务、队列、信号量、调度章节）。
- RM0008《STM32F10xxx 参考手册》：SysTick（Cortex-M3 系统时基）、NVIC 与 EXTI（第 9 章）、USART（第 27 章）。
- 本仓库示例：[`examples/freertos-task/`](../examples/freertos-task/)（含 CubeMX 配置与完整 `main.c`）。
- 相关章节：第 04 章中断与 NVIC、第 17 章调试与性能优化（DWT 计时）。
- 配图：`../assets/animations/freertos-scheduler.svg`（作者自绘矢量图）。


- 手机阅读版：[第 15 章 · FreeRTOS入门（公众号图文）](https://mp.weixin.qq.com/s/uw4_JRCRLkRFQ1EoezUXHg)

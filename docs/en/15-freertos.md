# 15 Getting Started with FreeRTOS
> 中文：[15 FreeRTOS 入门](../15-FreeRTOS入门.md)

> FreeRTOS splits "one big loop" into several tasks that run concurrently. Queues and semaphores carry data between them, so timing and logic in a complex project stop stepping on each other.

<p align="center">
  <img src="../../assets/animations/freertos-scheduler.svg" width="760" alt="FreeRTOS task-state transitions and preemptive scheduling">
  <br><sub>▲ Animation: FreeRTOS task-state transitions and preemptive scheduling (vector animation drawn by the author, not a live recording)</sub>
</p>

<!-- video:ch15 -->
<p align="center">
  <video width="640" controls poster="../../assets/video/ch15-rtos.png">
    <source src="../../assets/video/ch15-rtos.mp4" type="video/mp4">
  </video>
  <br><sub>▲ Chinese voice-over, 2.6 min. Voice: Microsoft Edge neural voice zh-CN-XiaoxiaoNeural via edge-tts (library mostly LGPLv3; the voice model is an online Microsoft service, not an open model). Pictures are generated from this repo's SVGs, not photographs. Video: <a href="../../assets/video/ch15-rtos.mp4">MP4</a> · subtitles: <a href="../../assets/video/ch15-rtos.srt">SRT</a>. Rebuild with <code>python3 tools/gen_narrated.py --speak</code>.</sub>
</p>

**Narration script (Chinese, same text as the subtitles)**

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
<!-- /video:ch15 -->

## Principle and boundary

The tick and FromISR are fixed on STM32F103C8T6. The group matches chapter file 04: `NVIC_PRIORITYGROUP_4`, 4 preemption bits, and 0 subpriority bits.

`configTICK_RATE_HZ = 1000`, so one tick is 1 ms. A deadline shorter than 1 ms is not a kernel guarantee. SysTick belongs to the kernel. The HAL time base is TIM4, the timer already named in the `examples/freertos-task` README. If both sides take SysTick, `HAL_Delay` sticks. See [examples in this repo](#source-project-examples).

A numerically larger task priority runs first. KEY is 2. LED and UART are 1. When both are ready, KEY runs first. Treating task priority like the NVIC, and expecting 1 to beat 2, is the failure path. The NVIC still treats a smaller number as more urgent. The idle task is 0. This part has no FPU.

`5 << (8 − 4) = 0x50`. An interrupt that calls FromISR needs a preemption priority number greater than or equal to 5, that is 5 or a larger number. The example sets `EXTI0` to 5. Setting it to 0 stops in `configASSERT`. The number 4 is also too urgent. See [FreeRTOS Kernel V11.3.2](#source-freertos-syscall).

The `xTaskCreate` depth is in words, and one word is 4 bytes. LED is 128 words = 512 bytes. KEY is 192 words = 768 bytes. UART is 256 words = 1024 bytes. Reading 128 as 128 bytes is the failure note.

Do 3 ms of work and then `vTaskDelay(10)`, and the call waits another 10 ticks, so the period is near 13 ms. `vTaskDelayUntil` of 10 ms keeps the period at 10 ms. A mutex protects a shared resource and has priority inheritance. A binary semaphore does not. heap_4 coalesces adjacent free blocks. Do not import the budget from chapter file 28.

## Key figures

<p align="center">
  <img src="../../assets/diagrams/sample-15-rtos-prio.svg" width="760" alt="One tick is 1 ms. Task priority 2 runs before priority 1. 128 words are 512 bytes. FromISR needs a numeric priority of 5 or a larger number.">
  <br><sub>▲ Drawn for this book. STM32F103C8T6. The normal path is a 1 ms SysTick, HAL time base TIM4, priority 2 running, priority 1 waiting, an LED stack of 128 words = 512 bytes, and EXTI0 preemption priority 5. The failure path writes that EXTI preemption priority as 0 and stops in configASSERT on FromISR. Sources: [FreeRTOS Kernel V11.3.2](#source-freertos-syscall) and [freertos-task](#source-project-examples).</sub>
</p>

<p align="center">
  <img src="../../assets/gif/rtos-tick.gif" width="640" alt="The tick advances 1 ms at a time, priority 2 holds the CPU, and 128 words equal 512 bytes">
  <br><sub>▲ Auxiliary figure for the web and for posts. It plays only the normal path: 1 ms steps, priority 2 running, priority 1 waiting, 128 words = 512 bytes. Print from the static figure. configASSERT and the SysTick clash are not on this GIF.</sub>
</p>

`freertos-scheduler.svg` stays as an auxiliary figure.

## Timing or state

| Object | Value | Who goes first |
| --- | --- | --- |
| tick | 1000 Hz | 1 ms |
| Tasks | priority 2 and priority 1 | 2 before 1. The direction is the opposite of the NVIC |
| Stacks | 128 words = 512 bytes | KEY 192 words = 768 bytes. UART 256 words = 1024 bytes |
| Interrupt | number 5 may call FromISR | number 0 stops in `configASSERT`. `0x50 = 5 << 4` |
| Time base | the kernel uses SysTick | HAL uses TIM4 |
| Delay | 3 ms of work, then `vTaskDelay(10)` | the period is near 13 ms. `vTaskDelayUntil` of 10 ms stays 10 ms |

## Pitfalls and source cards

| What you see | Why | What to do | Source | Claim this source may support |
| --- | --- | --- | --- | --- |
| `HAL_Delay` sticks, or the scheduler does not start | HAL and the kernel both want SysTick | Move the HAL time base to TIM4 | [examples in this repo](#source-project-examples) | The `examples/freertos-task` README names TIM4 as the time base |
| The interrupt stops in `configASSERT` | The preemption number is smaller than 5 | Write `EXTI0` as 5 or a larger number | [FreeRTOS](#source-freertos-syscall) | With 4 priority bits, 5 shifted left by 4 is `0x50`. A numerically smaller interrupt must not call FromISR |
| A priority 1 task runs over a priority 2 task | Task priority was treated like the NVIC | A numerically larger task priority runs first | [FreeRTOS](#source-freertos-syscall) | A numerically larger task priority runs first |
| KEY does not run ahead of LED in the example | Both tasks were given the same priority | Write KEY as 2, and LED and UART as 1 | [examples in this repo](#source-project-examples) | In `examples/freertos-task`, KEY's task priority is 2 and LED and UART are 1 |
| The stack note says 128 and a print overflows | A word was read as a byte | 128 is in words, which is 512 bytes | [examples in this repo](#source-project-examples) | LED is 128 words, KEY is 192 words, UART is 256 words |
| The key interrupt asserts as soon as it is entered | The EXTI preemption priority is too urgent | Write the `EXTI0` preemption priority as 5 | [examples in this repo](#source-project-examples) | The example sets the `EXTI0` preemption priority to 5 |
| Two tasks interleave on the UART | A binary semaphore was used to protect the resource | Use a mutex | [FreeRTOS](#source-freertos-syscall) | A mutex has priority inheritance. A binary semaphore does not |
| The period grows | `vTaskDelay(10)` does not include the time already spent before the call | Use `vTaskDelayUntil` for a fixed period | [FreeRTOS](#source-freertos-syscall) | When one tick is 1 ms, time already spent before the call is not inside `vTaskDelay` |

## 📌 Learning goals

- [ ] Explain the difference between "bare-metal foreground/background" and "an RTOS with several tasks," and decide whether a project should use an RTOS.
- [ ] Know the five task states (ready / running / blocked / suspended / deleted) and what moves a task between them.
- [ ] Understand the SysTick tick and preemptive scheduling, and the conflict with the HAL timebase and how to fix it.
- [ ] Choose an IPC object: compare queues, semaphores, mutexes, event groups, and task notifications.
- [ ] Estimate a task's stack, and understand priority inversion and priority inheritance.
- [ ] Tell heap_1 through heap_5 apart, and remember that an interrupt may only call FromISR APIs.

## 🧠 Core ideas

### 1. Bare-metal foreground/background vs an RTOS

**Conclusion**: Bare metal is "a main loop plus interrupts" (foreground/background). The more tasks you have, and the tighter the timing, the harder it is to maintain. An RTOS makes concurrency explicit with **tasks plus a scheduler**. The cost is a little RAM and a little CPU.

| Dimension | Bare-metal foreground/background | FreeRTOS, several tasks |
| --- | --- | --- |
| Shape | A `while(1)` main loop plus interrupts | Several independent tasks, each written on its own |
| Concurrency | You split it by hand with a state machine and flags | The scheduler switches for you |
| Blocking | Only a busy wait or a delay, which occupies the CPU | `vTaskDelay` or a blocking wait on a queue, which does not occupy the CPU |
| Real time | Interrupt priority; a long task slows the response | A higher-priority task can preempt |
| RAM cost | Tiny | A stack and a TCB per task, plus the kernel, starting at a few KB |
| Fits | One job, and the part is tight on resources | Several peripherals at once, a protocol stack, complicated logic |

> The test: **when the main loop contains several things that each want to run on their own rhythm, it is time to consider an RTOS.** Blinking an LED and reading a UART is still fine on bare metal.

### 2. Task state transitions

**Conclusion**: A task moves among running, ready, blocked, suspended, and deleted. **The CPU is given to someone else only when a task is blocked or suspended**, so every task needs a blocking point.

| State | Meaning | How you enter | How you leave |
| --- | --- | --- | --- |
| Running | It owns the CPU | The scheduler selects it | Preempted, blocked, or suspended |
| Ready | It can run, and it is waiting for the CPU | Created, a delay expires, or an event arrives | The scheduler selects it |
| Blocked | Waiting for time or for an event | `vTaskDelay`, `xQueueReceive`, and similar | Timeout, or the event arrives |
| Suspended | Paused on purpose | `vTaskSuspend` | `vTaskResume` |
| Deleted | Removed | `vTaskDelete` | — |

```text
                    vTaskResume
   ┌──────────────► Ready ◄─────────────────┐
   │                  │ scheduler selects    │ event arrives / timeout
   │  vTaskSuspend    │                      │
   ▼                  ▼                      │
Suspended          Running ──────────────► Blocked
                      │ block (delay / wait  │
                      │ on a queue)          │
                      └──────────────────────┘
```

### 3. SysTick and the scheduler (the fight with HAL over the timebase)

**Conclusion**: FreeRTOS uses **SysTick** by default to produce a 1 ms tick (`configTICK_RATE_HZ`). HAL also uses SysTick for `HAL_Delay`. **They cannot share it.** When you bring up the RTOS, move the HAL timebase to another timer.

| Conflict | What you see | Fix |
| --- | --- | --- |
| FreeRTOS and HAL both want SysTick | `HAL_Delay` hangs, and the tick misbehaves | In CubeMX: SYS → Timebase Source, change it to **TIM4** |
| Tick rate | `configTICK_RATE_HZ` defaults to 1000 (1 ms) | A shorter slice is more responsive and costs more |
| Time slicing | Tasks at the same priority share the CPU | `configUSE_TIME_SLICING=1` (on by default) |

### 4. Priority and preemption

**Conclusion**: In FreeRTOS, **a larger number is a higher priority** (the opposite of a Cortex-M interrupt). With `configUSE_PREEMPTION=1`, a higher-priority task that becomes ready preempts the current task immediately.

STM32F103C8T6 is a Cortex-M3 and has no FPU. A port built for an FPU is void on this part.

| Item | Rule |
| --- | --- |
| Priority range | `0` through `configMAX_PRIORITIES-1`. 0 is the lowest (the idle task) |
| Preemption | A higher-priority task becomes ready → switch immediately (preemptive) |
| Time slice | Tasks at the same priority rotate on the tick |
| Idle task | Priority 0, created by the system, and you can hook it |
| Versus interrupt priority | On an interrupt, a smaller number is higher priority (Cortex-M). That is the opposite direction from task priority |

### 5. Critical sections and interrupt priority

**Conclusion**: A critical section uses `taskENTER_CRITICAL()` / `taskEXIT_CRITICAL()` to mask interrupts and protect shared data. **Any interrupt that calls an `xxxFromISR` API must have a priority number ≥ `configMAX_SYSCALL_INTERRUPT_PRIORITY`.**

| Macro | What it does |
| --- | --- |
| `taskENTER_CRITICAL()` / `taskEXIT_CRITICAL()` | A task-level critical section. It can nest |
| `taskENTER_CRITICAL_FROM_ISR()` | An interrupt-level critical section |
| `configMAX_SYSCALL_INTERRUPT_PRIORITY` | The lowest priority number that is still allowed to call a FreeRTOS API (a larger number is a lower priority) |
| `configKERNEL_INTERRUPT_PRIORITY` | The priority of the kernel's own interrupts (PendSV / SysTick) |

> ⚠️ The common `configASSERT` dead loop means **the interrupt priority number was set too small (the priority was too high)** and it crossed the range `configMAX_SYSCALL_INTERRUPT_PRIORITY` allows. On STM32, with 4 priority bits, that macro is often `5 << (8-4) = 0x50`, which means the interrupt priority number must be ≥ 5.

### 6. Comparing the IPC options

**Conclusion**: A **queue** carries data. A **semaphore** synchronizes or counts. A **mutex** protects a shared resource. An **event group** waits on several conditions. A **task notification** is the lightweight point-to-point option. Pick the wrong one and you will write a bug that is hard to find.

| Mechanism | Use | Can it carry data? | Cost | Interrupt-safe API |
| --- | --- | --- | --- | --- |
| Queue | Pass data between tasks or from an interrupt | ✅ any length | Medium | `xQueueSendFromISR` |
| Binary semaphore | Synchronize on an event (ISR → task) | ❌ | Small | `xSemaphoreGiveFromISR` |
| Counting semaphore | Count a resource, or accumulate events | ❌ | Small | `xSemaphoreGiveFromISR` |
| Mutex | Protect a shared resource (includes priority inheritance) | ❌ | Medium | ⚠️ cannot be used from an ISR |
| Recursive mutex | The same task may take it more than once | ❌ | Medium | ⚠️ cannot be used from an ISR |
| Event group | Wait for several events (AND / OR) | ❌ (bit flags) | Small | `xEventGroupSetBitsFromISR` |
| Task notification | Lightweight point-to-point sync, or pass a value | ✅ (a 32-bit value) | **Smallest** | `xTaskNotifyFromISR` |

**Motto: a semaphore says "it happened," a queue says "carry this over," a mutex says "I am holding it, do not touch it," an event group says "wait until they are all here," and a task notification says "if this is enough, do not create an object."**

### 7. Estimating task stack size

**Conclusion**: The stack argument to `xTaskCreate` is in **words (4 bytes)**, not bytes. A stack that is too small overflows into another task or into the heap, and it shows up as a random HardFault.

| How to estimate | What it means |
| --- | --- |
| Start from experience | 128 words for a simple task; 256 to 512 words if it uses printf or floating point |
| Measure the watermark | `uxTaskGetStackHighWaterMark()` reports the smallest number of free words ever seen |
| Large local arrays | A big array inside a function sits on the stack. Prefer `static` or global |
| Nested interrupts | An ISR uses the current task's stack, so leave room for the interrupt |
| Overflow detection | `configCHECK_FOR_STACK_OVERFLOW=2`, and implement `vApplicationStackOverflowHook` |

```c
/* Runtime view of remaining stack (unit: words); if it nears 0, make the stack bigger */
UBaseType_t free_words = uxTaskGetStackHighWaterMark(xTask);
```

### 8. Priority inversion and priority inheritance

**Conclusion**: **Priority inversion** is a high-priority task being held up, indirectly, by a low-priority task. A FreeRTOS **mutex** has **priority inheritance** built in, which squeezes that window down to a very short time.

| Idea | What you see | What to do |
| --- | --- | --- |
| Priority inversion | A high task waits for a resource a low task holds, and a medium task runs ahead of both | Use a **mutex**, not a binary semaphore |
| Priority inheritance | The low task temporarily inherits the high task's priority, so it can release sooner | A FreeRTOS mutex does this automatically |
| Deadlock | Two tasks each hold one lock and wait for the other | Always lock in the same order, and use a timeout: `xSemaphoreTake(..., timeout)` |

> A binary semaphore does **not** have priority inheritance. It is only for "an event happened." To protect a resource, use `xSemaphoreCreateMutex()`.

### 9. heap_1 through heap_5

**Conclusion**: FreeRTOS ships five heap implementations. Which one you use depends on `configTOTAL_HEAP_SIZE` and on whether you need to free. **heap_4 is the one beginners use most.**

| Implementation | Supports free | Fragmentation | Notes |
| --- | --- | --- | --- |
| heap_1 | ❌ | None | Simplest. Allocate only, never free. Fine when the set of tasks never changes |
| heap_2 | ✅ | Severe | Can free, but does not coalesce. No longer recommended |
| heap_3 | ✅ | Depends on malloc | A wrapper around the C library `malloc` / `free`. Needs to be thread-safe |
| heap_4 | ✅ | Good (adjacent blocks coalesce) | **The usual choice.** Can free, and merges free blocks |
| heap_5 | ✅ | Good | Same as heap_4, and it supports **several non-contiguous memory regions** |

```c
/* Change the heap size in CubeMX: FreeRTOS → TOTAL_HEAP_SIZE (bytes) */
#define configTOTAL_HEAP_SIZE   ( ( size_t ) ( 10240 ) )
```

### 10. In an interrupt you may only call FromISR APIs

**Conclusion**: **An interrupt service routine must never call an ordinary API that can block** (for example `xQueueSend`). Use the `xxxFromISR` version, and use `portYIELD_FROM_ISR` to decide whether to switch immediately.

| Ordinary API (from a task) | Interrupt API (from an ISR) |
| --- | --- |
| `xQueueSend` | `xQueueSendFromISR` |
| `xQueueReceive` | `xQueueReceiveFromISR` |
| `xSemaphoreGive` | `xSemaphoreGiveFromISR` |
| `xEventGroupSetBits` | `xEventGroupSetBitsFromISR` |
| `xTaskNotify` | `xTaskNotifyFromISR` |

```c
void HAL_GPIO_EXTI_Callback(uint16_t pin)
{
    BaseType_t woken = pdFALSE;
    uint8_t evt = 1;
    xQueueSendFromISR(g_key_queue, &evt, &woken);  /* interrupt-safe */
    portYIELD_FROM_ISR(woken);                     /* switch immediately if needed */
}
```

## 🛠️ Hardware and wiring

| Board | Peripheral | Pin | Notes |
| --- | --- | --- | --- |
| BluePill (F103) | LED | PC13 | Already on the board, active low |
| BluePill | Key | PA0 | One side to PA0, the other to GND, falling-edge interrupt |
| BluePill | USB-TTL | PA9 / PA10 | Cross the TX/RX wires and share ground, 115200 |
| Nucleo-F411RE | On-board | PA5 (LD2), PC13 (B1) | Nothing to wire |

> The full example in this repo is [`examples/freertos-task/`](../../examples/freertos-task/) (three tasks, a queue, a mutex, and FromISR). Its `README.md` has the CubeMX settings, item by item.

## 💻 Code

Below is a minimal working skeleton: an LED blink, a key interrupt into a queue into a key task, and a UART task protected by a mutex. The full project is [`examples/freertos-task/main.c`](../../examples/freertos-task/main.c).

**① Create the objects and the tasks, then start the scheduler**

```c
#include "stm32f1xx_hal.h"
#include "FreeRTOS.h"
#include "task.h"
#include "queue.h"
#include "semphr.h"

static QueueHandle_t     g_key_queue  = NULL;   /* carries key events */
static SemaphoreHandle_t g_uart_mutex = NULL;   /* protects the UART */

int main(void)
{
    HAL_Init();
    SystemClock_Config();
    bsp_init();

    g_key_queue  = xQueueCreate(8, sizeof(uint8_t));       /* queue depth 8 */
    g_uart_mutex = xSemaphoreCreateMutex();                /* mutex */
    if (!g_key_queue || !g_uart_mutex) { error_handler(); } /* heap too small */

    xTaskCreate(vLedTask,  "LED",  128, NULL, 1, NULL);
    xTaskCreate(vKeyTask,  "KEY",  192, NULL, 2, NULL);    /* higher priority */
    xTaskCreate(vUartTask, "UART", 256, NULL, 1, NULL);

    vTaskStartScheduler();          /* does not return after this */
    for (;;) { }
}
```

**② Send the event from the interrupt with FromISR**

```c
void HAL_GPIO_EXTI_Callback(uint16_t GPIO_Pin)
{
    if (GPIO_Pin == KEY_PIN)
    {
        uint8_t key_id = 1;
        BaseType_t woken = pdFALSE;
        xQueueSendFromISR(g_key_queue, &key_id, &woken);
        portYIELD_FROM_ISR(woken);
    }
}
```

**③ The task blocks on the queue (and does not occupy the CPU)**

```c
static void vKeyTask(void *argument)
{
    uint8_t key_id;
    (void)argument;
    for (;;)
    {
        /* When the queue is empty the task is blocked; it wakes when an event arrives */
        if (xQueueReceive(g_key_queue, &key_id, portMAX_DELAY) == pdTRUE)
        {
            uart_print("KEY pressed\r\n");
        }
    }
}
```

**④ A mutex protects the shared UART**

```c
static void uart_print(const char *s)
{
    if (xSemaphoreTake(g_uart_mutex, pdMS_TO_TICKS(100)) == pdTRUE)
    {
        HAL_UART_Transmit(&huart1, (uint8_t *)s, strlen(s), 100);
        xSemaphoreGive(g_uart_mutex);   /* you must give it back when you are done */
    }
}
```

**⑤ The stack-overflow hook (a great way to catch the bug)**

```c
void vApplicationStackOverflowHook(TaskHandle_t xTask, char *pcTaskName)
{
    (void)xTask; (void)pcTaskName;
    __disable_irq();
    for (;;) { }                        /* stop the breakpoint here and see which task overflowed */
}
```

> **The single most important CubeMX step**: change `SYS → Timebase Source` from **SysTick to TIM4**. Otherwise HAL and FreeRTOS fight over SysTick, and `HAL_Delay` hangs.

## 🧪 Hands-on labs

1. **Two tasks, two blink rates (start here)**: create two tasks that toggle two LEDs at 500 ms and 200 ms. Expected: each LED blinks on its own rhythm, and they do not disturb each other.
2. **A queue carries a key press (next step)**: the key EXTI sends an event with `xQueueSendFromISR`. The task blocks in `xQueueReceive` and prints. Expected: while the queue is empty the task does not occupy the CPU, and a key press prints immediately.
3. **With and without a mutex**: two tasks both print a long string on the UART. First with no mutex (the output interleaves), then with a mutex (the output is whole). Expected: you can see the protection directly.
4. **(Further) Reproduce a stack overflow**: give a task a 64-word stack and put a 200-byte local array in a function, so `vApplicationStackOverflowHook` runs. Expected: the hook is called, and you learn how to size a stack.
5. **(Further) Priority inversion**: protect a resource with a binary semaphore and create an inversion, then switch to a mutex and compare the wait. Expected: the mutex inheritance shortens the high task's wait by a lot.

### 11. Relative delay, absolute period, and software timers

**Conclusion**: `vTaskDelay(n)` waits n ticks from **this call**. Time the task spends doing its own work stretches the period further and further. For a fixed period, use `vTaskDelayUntil`.

```c
TickType_t last = xTaskGetTickCount();
for (;;)
{
    do_work();                                   /* time spent here is not added on as period error */
    vTaskDelayUntil(&last, pdMS_TO_TICKS(10));   /* wake every 10 ms */
}
```

Create a software timer with `xTimerCreate`. The callback runs in the timer service task. Inside it you must not call `vTaskDelay` again, and you must not take a mutex that someone else might already hold. A larger priority number runs first, which is the opposite of NVIC, where a smaller number is more urgent. At any moment only one task owns the CPU.

Motto: **Delay means "wait a bit longer." DelayUntil means "wake at this next time." A timer callback must not go to sleep.**

Self-test:

1. A task works for 3 ms and then calls `vTaskDelay(10)`. Is the real period closer to 10 ms or to 13 ms?
2. If a software-timer callback calls `vTaskDelay`, who gets stuck?
3. A priority-3 task and a priority-1 task are both ready. Which one does FreeRTOS run first?

## 🔗 Related resources

- The official FreeRTOS documentation, and *Mastering the FreeRTOS Real Time Kernel* (the chapters on tasks, queues, semaphores, and scheduling).
- RM0008, *STM32F10xxx Reference Manual*: SysTick (the Cortex-M3 system timebase), NVIC and EXTI (Chapter 9), and USART (Chapter 27).
- Example in this repo: [`examples/freertos-task/`](../../examples/freertos-task/) (CubeMX settings and the full `main.c`).
- Related chapters: [Chapter 04](04-interrupts-nvic.md), Interrupts and NVIC, and [Chapter 17](17-debug.md), Debugging and performance (DWT timing).
- Figure: `../../assets/animations/freertos-scheduler.svg` (vector drawing by the author).

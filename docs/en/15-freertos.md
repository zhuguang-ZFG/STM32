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
  <br><sub>▲ Chapter video with Chinese voice-over (2.6 min). <a href="../../assets/video/ch15-rtos.mp4">MP4</a> · <a href="../../assets/video/ch15-rtos.srt">subtitles</a></sub>
</p>

<details>
<summary>Narration script (Chinese, same text as the subtitles)</summary>

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

## Learning goals

Before this chapter: read chapter 04 (interrupts and the NVIC, so you know what a priority number and preemption mean), chapter 05 (timers), and chapter 06 (printing over the UART), and be able to download a program as in chapter 01. If C pointers, `volatile`, or bit operations are unfamiliar, read "Zero-background primer" in chapter 00 first.

- [ ] Say which projects suit a bare-metal main loop and which suit RTOS tasks, and decide whether the project in front of you needs an RTOS
- [ ] Draw the five task states and name the call or event behind every arrow
- [ ] Explain what SysTick, PendSV, and SVC each do in FreeRTOS, and move the HAL time base to TIM4
- [ ] Set task and interrupt priorities with "a larger task number runs first, a smaller interrupt number runs first", and work out where `0x50` comes from
- [ ] Call only FromISR functions inside interrupts, and explain why a mutex cannot be used there
- [ ] Size a task stack in words and measure what is left with `uxTaskGetStackHighWaterMark()`
- [ ] Pick the right object for a job: queue, semaphore, mutex, event group, or task notification

## Core ideas

**In one sentence: FreeRTOS splits a program into tasks that each have their own stack, the scheduler gives the CPU to the highest-priority task that is ready, tasks hand the CPU back by blocking (on a delay or a queue), and interrupts talk to tasks only through functions whose names end in FromISR.**

### An analogy first

Think of the CPU as the only cook in a kitchen, the tasks as order tickets, and the scheduler as the head waiter who decides the order of work.

- Each ticket has its own stove and cutting board, and the dish stays on them at whatever step it reached. The cook can be called away to another dish and pick this one up again later. That is the task's stack.
- The head waiter looks at only two things: which tickets can be worked on now, and which is the most urgent. The moment the most urgent ticket becomes workable, the cook drops what is in hand and switches to it. That is preemption. Tickets of equal urgency take turns, a short stretch each. That is time slicing.
- A soup that must simmer for half an hour is set aside, and the cook does other dishes; when the soup is ready, the head waiter puts the ticket back in line. That is blocking.
- The waiter at the door is an interrupt. The waiter only drops new tickets at the pass (a queue) and cannot stand in the kitchen waiting for a dish.

The analogy stops here. The real scheduler does not "use judgement". It picks by two hard rules: the task must be ready, and it must have the largest priority number; equal numbers take turns tick by tick. "Dropping what is in hand" does not happen by itself either. An exception called PendSV saves the registers into the task's stack, as section 4 explains.

### 1. Bare-metal super loop or an RTOS: when to switch

RTOS stands for Real-Time Operating System. FreeRTOS is a common one. Its kernel handles scheduling, synchronization, timing, and memory, and nothing else; file systems and network stacks are not part of the kernel.

A few terms first:

- **Task**: a function that never returns, plus a stack of its own. The stack is the memory where the task keeps its local variables and "how far it got".
- **Scheduler**: the kernel code that decides who uses the CPU next.
- **TCB (Task Control Block)**: a card the kernel keeps for each task, holding its priority, its state, and its stack pointer.

The table compares the two styles. Read it top to bottom: the first rows are about structure, the last two about cost and fit.

| Aspect | Bare-metal foreground/background | FreeRTOS tasks |
| --- | --- | --- |
| Structure | A `while(1)` main loop plus interrupts | Several independent tasks, each written on its own |
| Concurrency | Split by hand with state machines and flags | The scheduler switches for you |
| Waiting | Busy-wait or `HAL_Delay`; the CPU spins while it waits | `vTaskDelay` or block on a queue; while one task waits, the CPU runs another |
| Real-time behaviour | Only interrupt priorities help; one slow job in the main loop delays everything | A more urgent task can preempt |
| RAM cost | Tiny | A stack and a TCB per task, plus the kernel's own |
| Fits | Single-purpose code, tight resources | Several peripherals working at once, protocol stacks, complex logic |

The test: when your main loop holds several jobs that each want their own rhythm, consider an RTOS. Blinking an LED and reading a UART is fine on bare metal. Count the cost too. This chapter's example gives the kernel heap 10240 bytes (example setting), and this chip has 20 KB of SRAM, or 20480 bytes (DS5319 Rev 20 Table 2), so the heap alone takes half.

### 2. The five task states

At any moment a task is in exactly one of the states below. Read the "how it gets in" and "how it gets out" columns and you can tell why a task is waiting:

| State | Meaning | How it gets in | How it gets out |
| --- | --- | --- | --- |
| Running | Holding the CPU | The scheduler picks it | Preempted by a higher-priority task, or its time slice ends (back to Ready); calls a delay or a wait (to Blocked); gets suspended |
| Ready | Able to run, waiting for the CPU | Just created; delay expired; the awaited event arrived; preempted | The scheduler picks it |
| Blocked | Waiting for time or for an event | `vTaskDelay`, `xQueueReceive`, `xSemaphoreTake`, and similar | Timeout, or the event arrives |
| Suspended | Paused on purpose, not scheduled | `vTaskSuspend` | `vTaskResume` |
| Deleted | Removed | `vTaskDelete` | — |

```text
            xTaskCreate
                 │
                 ▼
   ┌──────────► Ready ◄──────────────────────────┐
   │             │   ▲                           │ timeout, or the event arrives
   │   scheduler │   │ preempted, or its         │
   │    picks it ▼   │ time slice ends           │
   │           Running ───────────────────────► Blocked
   │             │      delay, wait on a queue or a semaphore
   │             │ vTaskSuspend (Ready and Blocked tasks can be suspended too)
   │             ▼
   └──────── Suspended    (vTaskResume puts it back in Ready)

   vTaskDelete: a task in any state can go straight to Deleted
```

The CPU changes hands at only three kinds of moment:

1. The running task blocks or suspends itself, for example by calling `vTaskDelay`.
2. A higher-priority task becomes ready, for example because data arrived on the queue it waits on. With preemption on (`configUSE_PREEMPTION = 1`), the kernel switches at once.
3. Another task of the same priority is ready and a tick arrives. This is time slicing, controlled by `configUSE_TIME_SLICING`; left undefined, it is 1 (`FreeRTOS.h` in FreeRTOS V11.3.2).

If the highest-priority task is a `while(1)` that never blocks, moments 1 and 2 never come, and every lower task starves. Deletion needs care too: when a task deletes itself, the idle task frees its stack and TCB, so the idle task must not starve forever either.

### 3. Priority: tasks and interrupts count in opposite directions

| Item | Rule |
| --- | --- |
| Priority range | `0` to `configMAX_PRIORITIES − 1`. With the CMSIS_V1 interface, CubeMX generates `configMAX_PRIORITIES = 7` |
| Idle task | Priority 0, created automatically when the scheduler starts; it runs when nothing else can |
| Preemption | With `configUSE_PREEMPTION = 1`, a higher-priority task runs the moment it becomes ready |
| Time slicing | Ready tasks of the same priority rotate once per tick |
| Interrupts | An interrupt is not a task. A smaller interrupt priority number is more urgent (Cortex-M), the opposite direction from task priority |

Keep one thing in mind when reading the table: tasks are compared by task priority, interrupts by NVIC priority, and an interrupt never needs to be compared with a task, because the interrupt always runs first. In this chapter's example KEY is 2 and LED and UART are 1, so when both sides are ready, KEY runs first.

The STM32F103C8T6 core is a Cortex-M3 with no FPU (Floating Point Unit). CubeMX picks the FreeRTOS ARM_CM3 port for it. The ARM_CM4F port, written for cores with an FPU, saves the floating-point registers on every task switch with instructions the M3 does not have, so it cannot be used on this chip.

### 4. SysTick and the scheduler: the tick and the three exceptions the kernel uses

The **tick** is the smallest unit of kernel time. SysTick is a 24-bit down counter inside the Cortex-M3 core (PM0056 Rev 7 section 4.5). The kernel sets it to interrupt `configTICK_RATE_HZ` times a second. This chapter's example uses 1000, so one tick is 1 ms. That is an example setting and also the CubeMX default; the kernel itself has no default, and `FreeRTOSConfig.h` must define it. At a 72 MHz core clock one tick is 72 000 000 / 1000 = 72 000 clocks, so the reload value is 71 999, well inside the 24-bit maximum of 16 777 215.

All kernel time is counted in ticks. At 1000 Hz, `pdMS_TO_TICKS(500)` is 500 ticks. The kernel guarantees nothing shorter than one tick.

The table shows how the three exceptions divide the work. Exception numbers and purposes come from PM0056 Rev 7 section 2.3.2 Table 16; the priorities are what `port.c` in the FreeRTOS V11.3.2 ARM_CM3 port sets:

| Exception | Number | Job in FreeRTOS | Priority |
| --- | --- | --- | --- |
| SVC (SVCall) | 11 | When the scheduler starts, one `svc 0` enters the first task | Highest |
| PendSV | 14 | Switches tasks (context switch) | Lowest |
| SysTick | 15 | The tick: adds 1 to the tick count and checks whether a task is due; pends PendSV when a switch is needed | Lowest |

A **context switch** means "carry on with a different task". On entry to PendSV the hardware has already pushed 8 registers, R0–R3, R12, LR, PC, and xPSR, onto the current task's stack (PM0056 section 2.3.7). PendSV then pushes R4–R11, stores the stack pointer in the TCB, loads the next task's stack pointer, and pops that task's registers in reverse.

PendSV sits at the lowest priority so that it runs only after every interrupt has finished; a task switch never lands in the middle of an interrupt handler. The `portYIELD_FROM_ISR(pdTRUE)` call inside an interrupt does not switch on the spot. It only pends PendSV, which runs once the interrupt exits.

### 5. Why the HAL time base moves to TIM4

HAL's `HAL_Delay()` and the timeouts in every peripheral function read `HAL_GetTick()`. That millisecond count advances once per 1 ms through `HAL_IncTick()`, which the SysTick interrupt calls by default. FreeRTOS wants SysTick as well, and the clash shows up in three places:

- The `FreeRTOSConfig.h` that CubeMX generates defines `xPortSysTickHandler` as `SysTick_Handler`, so the whole SysTick interrupt goes to the kernel. Nobody calls `HAL_IncTick()` any more, and `HAL_Delay()` never sees time pass.
- When the scheduler starts, the kernel reprograms SysTick for its own tick and gives it the lowest priority. Kernel critical sections hold off interrupts numbered 5–15 (section 7), and the HAL tick is held off with them.
- Before the scheduler starts, once any kernel function has been called (`xQueueCreate`, say), the kernel keeps interrupts numbered 5–15 held off until `vTaskStartScheduler()`. A HAL tick on one of those interrupts stops during that time.

Squeezing both into one SysTick interrupt can be made to work, and older CubeMX versions generated exactly that: `SysTick_Handler` called `HAL_IncTick()` and then the kernel's tick function. The HAL tick then follows the kernel's priority and start-up timing, which is hard to control, so CubeMX recommends a different HAL time base in FreeRTOS projects.

In CubeMX: SYS → Timebase Source, choose TIM4. CubeMX then generates `stm32f1xx_hal_timebase_tim.c`, which makes TIM4 interrupt every 1 ms, and `HAL_TIM_PeriodElapsedCallback()` in `main.c` calls `HAL_IncTick()` each time TIM4 expires. Settle this before creating any task. This chapter's example uses TIM4 for nothing else, which is why it is chosen; if TIM4 has another job in your project, pick a free timer.

> [!TIP]
> Before the scheduler starts, between a kernel call such as `xQueueCreate` and `vTaskStartScheduler()`, do not call `HAL_Delay()` unless the HAL time-base interrupt has a priority number below 5.

### 6. Delays: wait a while longer, or wake at a set time

A worked case: a task does 3 ms of work and then calls `vTaskDelay(pdMS_TO_TICKS(10))`. One loop is 3 + 10, so the period is near 13 ms. With the code below, the kernel remembers when the task last woke and sleeps only until "last wake + 10 ms". The 3 ms of work is subtracted, and the period is 10 ms:

```c
TickType_t last = xTaskGetTickCount();          /* record the starting point */
for (;;)
{
    do_work();                                  /* time spent here comes off the next sleep */
    vTaskDelayUntil(&last, pdMS_TO_TICKS(10));  /* wake every 10 ms */
}
```

If `do_work()` itself takes longer than 10 ms, `vTaskDelayUntil` does not sleep at all and returns at once, and the period is lost.

A **software timer** is created with `xTimerCreate` and calls your callback function when it expires; it needs `configUSE_TIMERS = 1`. Every callback runs, one after another, in a single timer service task (also called the daemon task). So a callback must not block: no `vTaskDelay`, and no waiting with a non-zero timeout on a queue, a semaphore, or a mutex that someone else may hold. When one callback sleeps, every other software timer stops with it. For work that has to wait, have the callback notify an ordinary task and let that task do it.

The motto: **Delay is "wait a while longer", DelayUntil is "wake at a set time"; no sleeping in timer callbacks.**

### 7. Critical sections and interrupt priority: only FromISR calls in an interrupt

An ordinary API call may block its caller, and an interrupt is not a task, so it cannot block. The FromISR versions never wait: when the queue is full, `xQueueSendFromISR` returns `errQUEUE_FULL` at once. The left column is the call a task uses; the right column is the matching call inside an interrupt:

| In a task | In an interrupt |
| --- | --- |
| `xQueueSend` | `xQueueSendFromISR` |
| `xQueueReceive` | `xQueueReceiveFromISR` |
| `xSemaphoreGive` (binary or counting semaphore) | `xSemaphoreGiveFromISR` |
| `xSemaphoreGive` (mutex) | None; a mutex cannot be used in an interrupt |
| `xEventGroupSetBits` | `xEventGroupSetBitsFromISR` |
| `xTaskNotify` / `xTaskNotifyGive` | `xTaskNotifyFromISR` / `vTaskNotifyGiveFromISR` |
| `xTaskGetTickCount` | `xTaskGetTickCountFromISR` |

The last parameter of a FromISR function is usually `pxHigherPriorityTaskWoken`. When it is set to `pdTRUE`, the call has woken a task more urgent than the one that was interrupted. Pass it to `portYIELD_FROM_ISR()` at the end of the interrupt and the switch happens as soon as the interrupt exits; skip that, and the woken task waits for the next tick.

**Where 0x50 comes from.** The STM32F1 NVIC implements only the top 4 bits of each priority byte; the low 4 bits read as 0 and ignore writes (PM0056 Rev 7 section 4.3.7 Table 42). So a 4-bit priority of 0–15 is shifted left by 4 before it goes into the hardware register. The `FreeRTOSConfig.h` that CubeMX generates writes the same idea two ways:

| Macro | Value | Used by |
| --- | --- | --- |
| `configLIBRARY_MAX_SYSCALL_INTERRUPT_PRIORITY` | 5 | Unshifted, to compare with `HAL_NVIC_SetPriority()` |
| `configMAX_SYSCALL_INTERRUPT_PRIORITY` | 5 << (8 − 4) = 0x50 | Shifted; the kernel writes it to the BASEPRI register |
| `configLIBRARY_LOWEST_INTERRUPT_PRIORITY` | 15 | Unshifted, the lowest priority |
| `configKERNEL_INTERRUPT_PRIORITY` | 15 << 4 = 0xF0 | The lowest priority, used by the kernel's own interrupts |

The 5 and 15 in the table are values CubeMX generates, not numbers the kernel requires. BASEPRI is a Cortex-M3 masking register: once it holds a non-zero value, the processor stops taking exceptions whose priority value is greater than or equal to it (PM0056 section 2.1.3 Table 9). On entering a critical section the kernel writes `BASEPRI = 0x50`, so interrupts numbered 5–15 wait for a moment while 0–4 are taken as usual. The kernel's data can therefore only be touched by interrupts numbered 5–15, and only those may call FromISR.

The table splits interrupts into three bands by priority number. When you set up a new interrupt, first decide whether it will call FreeRTOS functions, then pick a number from the matching band:

| Preemption priority number | Held off by kernel critical sections | May call FreeRTOS functions | Example |
| --- | --- | --- | --- |
| 0–4 | No | None at all | Interrupts that need the fastest response and do not talk to tasks |
| 5–14 | Yes | FromISR only | The example's EXTI0 is set to 5 (example setting) |
| 15 | Yes | FromISR only | Same level as PendSV and SysTick |

**What the assert checks.** With `configASSERT` defined, every FromISR function first checks two things (`vPortValidateInterruptPriority` in `port.c`): the current interrupt's priority number is not below 5, and the grouping gives all 4 bits to preemption priority. After reset every interrupt priority is 0, so an interrupt you forgot to pass through `HAL_NVIC_SetPriority()` stops in the assert on its first FromISR call. `HAL_Init()` has already set the grouping to `NVIC_PRIORITYGROUP_4`; do not change it afterwards. CubeMX defines `configASSERT`. A hand-built project without it does not stop; instead it occasionally corrupts kernel data, which is far harder to track down than an assert.

### 8. Inter-task communication: pick the right object

One sentence on each object first:

- **Queue**: a buffer of N items of a fixed size. Sending copies the data in by value and receiving copies it out, so the sender's local variable can be dropped right after sending. `xQueueCreate(8, sizeof(uint8_t))` is 8 items of 1 byte each.
- **Binary semaphore**: a flag with only two states, "set" and "not set", often used by an interrupt to tell a task "it happened".
- **Counting semaphore**: a flag that can count to N, used to count free resources or to accumulate events not yet handled.
- **Mutex** (short for mutual exclusion): a lock with an owner; whoever takes it gives it back. It has priority inheritance (section 9).
- **Event group**: a set of flag bits; a task can wait for "all of these bits" or "any of these bits". With a 32-bit tick count, an event group has 24 usable bits (`event_groups.h` in FreeRTOS V11.3.2).
- **Task notification**: a 32-bit notification value built into every task. No separate object is needed, but it can only go to one named task.

The table compares them side by side. When choosing, look first at the "carries data" and "in an interrupt" columns:

| Mechanism | Use | Carries data | Cost | In an interrupt |
| --- | --- | --- | --- | --- |
| Queue | Pass data between tasks, or from an interrupt to a task | Yes; fixed-size items, copied by value | Medium | `xQueueSendFromISR` |
| Binary semaphore | Event sync, typically an interrupt waking a task | No | Small | `xSemaphoreGiveFromISR` |
| Counting semaphore | Count resources, accumulate events | No | Small | `xSemaphoreGiveFromISR` |
| Mutex | Protect a shared resource, with priority inheritance | No | Medium | Cannot be used in an interrupt |
| Recursive mutex | The same task may take it repeatedly and gives it back as many times | No | Medium | Cannot be used in an interrupt |
| Event group | Wait for several events (AND, OR) | Flag bits only; 24 usable with a 32-bit tick | Small | `xEventGroupSetBitsFromISR`, handed to the timer service task |
| Task notification | Light one-to-one sync, or passing one value | Yes, one 32-bit value | Smallest | `xTaskNotifyFromISR` |

`xEventGroupSetBitsFromISR` does not set the bits inside the interrupt. It sends a message to the timer service task, which sets them, so it needs both `configUSE_TIMERS` and `INCLUDE_xTimerPendFunctionCall`.

### 9. Priority inversion: mutexes and priority inheritance

**Priority inversion** goes like this. Low-priority task L holds the lock. High-priority task H asks for it and has to block. Then medium-priority task M becomes ready; it is more urgent than L, so it takes the CPU. Without the CPU, L cannot give the lock back, and H is in effect waiting for M.

**Priority inheritance** is the mutex's remedy: when H asks for the lock, the kernel temporarily raises L to H's priority, so M cannot cut in; the moment L gives the lock back, its priority drops again.

| Concept | What you see | Remedy |
| --- | --- | --- |
| Priority inversion | A high task waits for a resource a low task holds, and a medium task runs first | Use a mutex, not a binary semaphore |
| Priority inheritance | The low task temporarily inherits the high task's priority and gives the lock back sooner | FreeRTOS mutexes do it automatically |
| Deadlock | Two tasks each hold one lock and wait for the other's | Every task takes locks in the same order; give `xSemaphoreTake` a timeout instead of waiting forever |

Inheritance shortens the wait; it does not remove it. H still waits for L to finish the code inside the lock, so keep only the shortest operations there. A mutex records which task owns it, and an interrupt is not a task, so an interrupt can neither take nor give a mutex.

### 10. The task stack in words, and the heap from heap_1 to heap_5

Different APIs use different units, so check which one you are copying. The third column is "what you get when you write 128":

| How it is written | Unit of the stack parameter | Writing 128 gives |
| --- | --- | --- |
| `xTaskCreate(fn, "X", 128, ...)` | Words | 512 bytes |
| CMSIS-RTOS v1: `osThreadDef(name, fn, prio, 0, 128)` | Words (ST's `cmsis_os.c` passes it straight to `xTaskCreate`) | 512 bytes |
| CMSIS-RTOS v2: `.stack_size` in `osThreadAttr_t` | Bytes ([CMSIS-RTOS2](#source-cmsis-640)) | 128 bytes; CubeMX writes `128 * 4` |

How to size a stack:

| Method | Notes |
| --- | --- |
| Start from a rule of thumb | 128 words for a simple task; 256–512 words for one that uses `printf` or float formatting (rule of thumb) |
| Measure the high-water mark | `uxTaskGetStackHighWaterMark()` returns the least free stack the task has had since it started, also in words; near 0 means enlarge it |
| Large local arrays | A large array inside a function lives on the stack; make it `static` or global where you can |
| Interrupt overhead | On the Cortex-M3, tasks run on the PSP (process stack) and interrupt handlers always use the MSP (main stack, PM0056 Rev 7 section 2.1.2). When an interrupt arrives, the hardware first pushes 8 registers, 32 bytes, onto the current task's stack; a task switch then has PendSV push 8 more. Leave 64 bytes in every task stack for these two sets; the handler's own locals and nested interrupts use the main stack |
| Overflow detection | `configCHECK_FOR_STACK_OVERFLOW` is 0 when left undefined, which checks nothing; set it to 2 and implement `vApplicationStackOverflowHook()` |

```c
/* At run time, see how much stack a task has left (in words) */
UBaseType_t free_words = uxTaskGetStackHighWaterMark(xTask);
```

Task stacks and TCBs, queues, and mutexes all come from the kernel heap. Its size is `configTOTAL_HEAP_SIZE`, in bytes. FreeRTOS ships five heap implementations; start with heap_4:

| Implementation | Can free | Fragmentation | Notes |
| --- | --- | --- | --- |
| heap_1 | No | None | Allocates and never frees; enough when tasks are created once and never change |
| heap_2 | Yes | Bad | Does not merge adjacent free blocks; no longer recommended |
| heap_3 | Yes | Depends on the C library | Wraps the standard `malloc`/`free` with the scheduler suspended; the heap size comes from the linker script, and `configTOTAL_HEAP_SIZE` has no effect on it |
| heap_4 | Yes | Good; adjacent free blocks merge | The usual choice |
| heap_5 | Yes | Good | Like heap_4, and can join several non-contiguous memory regions into one heap |

## Hardware and wiring

| Board | Peripheral | Pin | Notes |
| --- | --- | --- | --- |
| BluePill (STM32F103C8T6) | Onboard LED | PC13 | Already on the board; lights on low |
| BluePill | Button | PA0 | One side to PA0, the other to GND; internal pull-up, falling-edge interrupt |
| BluePill | USB-TTL | PA9 (TX) / PA10 (RX) | Cross TX and RX and share ground; 115200-8-N-1 |
| BluePill | External LED (lab 1) | PA1 | 270 Ω in series to GND, lights on 1; 270 Ω is chapter 03's example setting |
| Nucleo-F411RE | Onboard | PA5 (LD2), PC13 (B1) | No wiring needed; LD2 lights on high (UM1724 Rev 17 section 7.6) |

```text
Button:        PA0 ──[button]── GND               internal pull-up on PA0; pressing reads 0 and makes a falling edge
Onboard LED:   3.3 V ──[resistor]──▶|── PC13      lights on 0
External LED:  PA1 ──[270 Ω]──▶|── GND            lights on 1 (lab 1)
UART:          PA9  (TX) ───────► USB-TTL RX
               PA10 (RX) ◄─────── USB-TTL TX
               GND ────────────── USB-TTL GND
```

Set the USB-TTL adapter to 3.3 V levels. PA0 and PA1 are not marked FT (5 V tolerant) in DS5319 Rev 20 Table 5, so wire the button and the external LED only to 3.3 V and GND. The Nucleo-F411RE has a Cortex-M4F with an FPU, and CubeMX picks the ARM_CM4F port for it; the numbers in this chapter are all for the STM32F103C8T6.

The complete example in this repository is [`examples/freertos-task/`](../../examples/freertos-task/); its `README.md` lists the CubeMX settings one by one.

## Code

Below is the whole of `main.c`. The LED task blinks, the button interrupt hands each press to the key task through a queue, the UART task prints a heartbeat every second, and a mutex protects the UART that two tasks share. Drop it into a CubeMX project set up as the example README describes (FreeRTOS with CMSIS_V1, Timebase Source TIM4, USART1 and the EXTI line0 interrupt enabled) and it compiles.

```c
/* main.c - three tasks + a queue + a mutex + FromISR (STM32F103C8T6, 72 MHz) */
#include "stm32f1xx_hal.h"
#include "FreeRTOS.h"
#include "task.h"
#include "queue.h"
#include "semphr.h"
#include <stdio.h>
#include <string.h>

#define LED_PORT         GPIOC
#define LED_PIN          GPIO_PIN_13      /* onboard LED, lights on low */
#define KEY_PORT         GPIOA
#define KEY_PIN          GPIO_PIN_0       /* PA0 button, pressing connects to ground */

#define LED_TASK_STACK   128U             /* unit: words (4 bytes) */
#define KEY_TASK_STACK   192U
#define UART_TASK_STACK  256U
#define LED_TASK_PRIO    1U
#define KEY_TASK_PRIO    2U               /* task priority: a larger number runs first */
#define UART_TASK_PRIO   1U
#define KEY_QUEUE_LEN    8U               /* holds up to 8 key events */
#define KEY_IRQ_PRIO     5U               /* interrupt priority: must not be below configLIBRARY_MAX_SYSCALL_INTERRUPT_PRIORITY */

UART_HandleTypeDef huart1;

static QueueHandle_t     g_key_queue  = NULL;   /* interrupt -> key task */
static SemaphoreHandle_t g_uart_mutex = NULL;   /* protects the UART */

static void SystemClock_Config(void);
static void bsp_init(void);
static void error_handler(void);
static void uart_print(const char *s);
static void vLedTask(void *argument);
static void vKeyTask(void *argument);
static void vUartTask(void *argument);

int main(void)
{
    HAL_Init();                 /* sets NVIC_PRIORITYGROUP_4 and starts the HAL time base (TIM4) */
    SystemClock_Config();
    bsp_init();

    g_key_queue  = xQueueCreate(KEY_QUEUE_LEN, sizeof(uint8_t));
    g_uart_mutex = xSemaphoreCreateMutex();
    if ((g_key_queue == NULL) || (g_uart_mutex == NULL))
    {
        error_handler();        /* heap too small: enlarge configTOTAL_HEAP_SIZE */
    }

    if ((xTaskCreate(vLedTask,  "LED",  LED_TASK_STACK,  NULL, LED_TASK_PRIO,  NULL) != pdPASS) ||
        (xTaskCreate(vKeyTask,  "KEY",  KEY_TASK_STACK,  NULL, KEY_TASK_PRIO,  NULL) != pdPASS) ||
        (xTaskCreate(vUartTask, "UART", UART_TASK_STACK, NULL, UART_TASK_PRIO, NULL) != pdPASS))
    {
        error_handler();
    }

    vTaskStartScheduler();      /* does not return in normal operation */
    error_handler();            /* reaching here: the heap cannot even hold the idle task */
    return 0;
}

static void vLedTask(void *argument)
{
    (void)argument;
    for (;;)
    {
        HAL_GPIO_TogglePin(LED_PORT, LED_PIN);
        vTaskDelay(pdMS_TO_TICKS(500));         /* block for 500 ms and hand the CPU over */
    }
}

static void vKeyTask(void *argument)
{
    uint8_t key_id;
    char    msg[48];

    (void)argument;
    for (;;)
    {
        /* blocks while the queue is empty, using no CPU */
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
    if (xSemaphoreTake(g_uart_mutex, pdMS_TO_TICKS(100)) == pdTRUE)   /* wait at most 100 ms */
    {
        (void)HAL_UART_Transmit(&huart1, (uint8_t *)s, (uint16_t)strlen(s), 100U);
        (void)xSemaphoreGive(g_uart_mutex);                          /* give it back at once */
    }
}

/* PA0 -> EXTI0. CubeMX writes EXTI0_IRQHandler in stm32f1xx_it.c; it calls HAL_GPIO_EXTI_IRQHandler, which lands here */
void HAL_GPIO_EXTI_Callback(uint16_t GPIO_Pin)
{
    if (GPIO_Pin == KEY_PIN)
    {
        uint8_t    key_id = 1U;
        BaseType_t woken  = pdFALSE;

        (void)xQueueSendFromISR(g_key_queue, &key_id, &woken);   /* only FromISR inside an interrupt */
        portYIELD_FROM_ISR(woken);                               /* switch on exit if a more urgent task woke */
    }
}

/* HAL time base on TIM4: CubeMX's stm32f1xx_hal_timebase_tim.c makes TIM4 interrupt every 1 ms */
void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim)
{
    if (htim->Instance == TIM4)
    {
        HAL_IncTick();          /* HAL_Delay and the HAL timeouts depend on it */
    }
}

static void bsp_init(void)
{
    GPIO_InitTypeDef io = {0};

    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_GPIOC_CLK_ENABLE();
    __HAL_RCC_AFIO_CLK_ENABLE();                /* on F1 the EXTI mapping lives in AFIO */
    __HAL_RCC_USART1_CLK_ENABLE();

    io.Pin   = LED_PIN;
    io.Mode  = GPIO_MODE_OUTPUT_PP;
    io.Pull  = GPIO_NOPULL;
    io.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(LED_PORT, &io);
    HAL_GPIO_WritePin(LED_PORT, LED_PIN, GPIO_PIN_SET);   /* start with it off */

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

static void SystemClock_Config(void)            /* HSE 8 MHz x 9 = 72 MHz, APB1 36 MHz */
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

/* With configCHECK_FOR_STACK_OVERFLOW set to 2, the kernel calls this when a task's stack overflows */
void vApplicationStackOverflowHook(TaskHandle_t xTask, char *pcTaskName)
{
    (void)xTask;
    (void)pcTaskName;           /* break here; pcTaskName is the task that overflowed */
    __disable_irq();
    for (;;)
    {
        HAL_GPIO_TogglePin(LED_PORT, LED_PIN);               /* fast blink as the alarm */
        for (volatile uint32_t i = 0U; i < 200000U; i++) { }
    }
}
```

CubeMX generates `FreeRTOSConfig.h`; the lines below are the ones that matter for this chapter. Change `configTOTAL_HEAP_SIZE` and `configCHECK_FOR_STACK_OVERFLOW` to these values on the CubeMX FreeRTOS parameter page; the rest are CubeMX-generated values:

```c
#define configUSE_PREEMPTION                         1
#define configCPU_CLOCK_HZ                           ( SystemCoreClock )
#define configTICK_RATE_HZ                           ( ( TickType_t ) 1000 )
#define configMAX_PRIORITIES                         ( 7 )
#define configMINIMAL_STACK_SIZE                     ( ( uint16_t ) 128 )      /* idle task stack, in words */
#define configTOTAL_HEAP_SIZE                        ( ( size_t ) 10240 )      /* in bytes; the example needs at least 10240 */
#define configCHECK_FOR_STACK_OVERFLOW               2                         /* 0 when left undefined */

#ifdef __NVIC_PRIO_BITS
 #define configPRIO_BITS                             __NVIC_PRIO_BITS         /* 4 on F1 */
#else
 #define configPRIO_BITS                             4
#endif
#define configLIBRARY_LOWEST_INTERRUPT_PRIORITY      15
#define configLIBRARY_MAX_SYSCALL_INTERRUPT_PRIORITY 5
#define configKERNEL_INTERRUPT_PRIORITY      ( configLIBRARY_LOWEST_INTERRUPT_PRIORITY << (8 - configPRIO_BITS) )      /* 0xF0 */
#define configMAX_SYSCALL_INTERRUPT_PRIORITY ( configLIBRARY_MAX_SYSCALL_INTERRUPT_PRIORITY << (8 - configPRIO_BITS) ) /* 0x50 */
#define configASSERT( x ) if ((x) == 0) { taskDISABLE_INTERRUPTS(); for( ;; ); }

#define vPortSVCHandler     SVC_Handler          /* the three exceptions go to the kernel */
#define xPortPendSVHandler  PendSV_Handler
#define xPortSysTickHandler SysTick_Handler
```

Piece by piece:

- `HAL_Init()` does two things that matter here: it sets the priority grouping to `NVIC_PRIORITYGROUP_4`, and through the `HAL_InitTick()` that CubeMX generates it starts TIM4 as the 1 ms HAL time base.
- The queue and the mutex are created before the tasks. `NULL` means the heap is too small; no task is running yet, so stopping right there is the easiest case to debug.
- The third argument of `xTaskCreate` is the stack depth, in words; the fifth is the task priority. None of the three tasks keeps its handle, so the last argument is `NULL`.
- `vTaskStartScheduler()` creates the idle task (plus the timer service task when software timers are on), sets SysTick to 1000 Hz, and enters the first task through SVC. If it returns, the heap could not even hold the idle task.
- Each task is a `for (;;)` that never returns, and each contains a blocking call: `vTaskDelay` or `xQueueReceive`. Remove it, and every task below that priority never runs again.
- `uart_print()` waits at most 100 ms for the lock; on timeout the line is simply not printed. The mutex covers a whole `HAL_UART_Transmit`, so another task cannot cut a line in half.
- `HAL_GPIO_EXTI_Callback()` runs inside the interrupt, so it uses `xQueueSendFromISR` and finally hands `woken` to `portYIELD_FROM_ISR()`. KEY has priority 2, more urgent than the interrupted task, so it runs as soon as the interrupt exits.
- `KEY_IRQ_PRIO` is 5, exactly `configLIBRARY_MAX_SYSCALL_INTERRUPT_PRIORITY`. Write 0 to 4 and the first key press stops in `configASSERT`.
- `HAL_TIM_PeriodElapsedCallback()` calls `HAL_IncTick()` each time TIM4 expires; that is what keeps `HAL_Delay()` and the HAL timeouts moving.

> [!TIP]
> The example `examples/freertos-task/main.c` has no `HAL_TIM_PeriodElapsedCallback()`, yet brings its own `EXTI0_IRQHandler()`. When you overwrite CubeMX's `main.c` with it as the example README says, add the callback above back in, or the HAL millisecond count never moves; and if CubeMX also generated an `EXTI0_IRQHandler()` in `stm32f1xx_it.c`, keep only one of the two, or the link fails with a duplicate definition.

A few macros and the register operations behind them, so the kernel source reads familiar:

```c
/* HAL_NVIC_SetPriority(EXTI0_IRQn, 5, 0) under group 4 writes this byte: */
NVIC->IP[EXTI0_IRQn] = (uint8_t)(5U << (8U - __NVIC_PRIO_BITS));   /* 0x50 */

/* In the ARM_CM3 port, portYIELD_FROM_ISR(pdTRUE) just pends PendSV: */
SCB->ICSR = SCB_ICSR_PENDSVSET_Msk;

/* What the kernel does on entering a critical section: hold off numbers 5-15 only, 0-4 still run */
__set_BASEPRI(configMAX_SYSCALL_INTERRUPT_PRIORITY);               /* 0x50 */
```

The complete project is in [`examples/freertos-task/`](../../examples/freertos-task/).

## Hands-on labs

1. **Lab 1: two tasks, two rhythms.** Add a task that toggles the external LED on PA1 every 200 ms; the existing LED task keeps toggling PC13 every 500 ms.
   - Expected: the PC13 LED blinks once a second and the PA1 LED once every 0.4 s, each on its own beat.
   - How to check: count blinks over 10 s: 10 for PC13 and 25 for PA1. With a logic analyzer, the periods should be close to 1.000 s and 0.400 s.
   - If it fails, check first: is the new task's stack big enough (start at 128 words); does each task call `vTaskDelay`; is the HAL time base TIM4; are the PA1 port clock and push-pull output set up.
2. **Lab 2: a key press through a queue.** Run the full program above and press the PA0 button.
   - Expected: each press adds a line `KEY 1 pressed @… ms` on the UART; without presses there is only the heartbeat once a second. A mechanical button without debouncing sometimes prints two or three lines per press.
   - How to check: set the terminal to 115200-8-N-1; the difference between the numbers after `@` on two presses matches the time between your presses.
   - If it fails, check first: if the board hangs on the first press, check that EXTI0's priority number is 5 (stopped in `configASSERT`); are the AFIO clock and the PA0 pull-up on; is there only one `EXTI0_IRQHandler()`.
3. **Lab 3: with and without the lock.** Make both the LED task and the UART task print an 80-character line. First remove the mutex from `uart_print()` and send one character per `HAL_UART_Transmit` call; then put the mutex back.
   - Expected: without the lock, the two tasks' characters interleave; with it, every line is whole.
   - How to check: at 115200 one byte is 10 bits, about 86.8 µs, so 80 characters take about 6.9 ms and span several 1 ms ticks; the two equal-priority tasks rotate in the middle, and the interleaving is easy to see.
   - If it fails, check first: if you see no interleaving without the lock, the line is probably too short or the two tasks are not printing at the same time; make the line longer. With one `HAL_UART_Transmit` per whole line you see lost lines instead of interleaving: the later call finds the UART busy and returns `HAL_BUSY` at once.
4. **Lab 4: reproduce a stack overflow.** Set `configCHECK_FOR_STACK_OVERFLOW` to 2, cut the LED task stack to 64 words (256 bytes), put a local array `volatile uint8_t buf[200]` in the task, and fill it with a `for` loop.
   - Expected: the onboard LED starts blinking fast, which means `vApplicationStackOverflowHook()` was entered.
   - How to check: break in the hook; `pcTaskName` is `"LED"`.
   - If it fails, check first: with `configCHECK_FOR_STACK_OVERFLOW` still 0 the hook is never called, and the program most likely goes straight to HardFault; an array without `volatile` that is written and never read may be optimized away entirely.
5. **Lab 5: watch priority inversion.** Create three tasks: L (priority 1) takes the lock, stays busy for 50 ms, then gives it back; H (priority 3) asks for the same lock after L has it; M (priority 2) becomes ready at that point and stays busy for 200 ms without blocking. Use `xSemaphoreCreateBinary()` for the lock first, then `xSemaphoreCreateMutex()`. These millisecond values are example settings.
   - Expected: with the binary semaphore, H's wait includes M's 200 ms; with the mutex, H waits at most for the rest of L's work.
   - How to check: in H, read `xTaskGetTickCount()` just before and just after `xSemaphoreTake`; the difference is the wait in ticks. Print it and compare.
   - If it fails, check first: a newly created binary semaphore is empty, so give it once with `xSemaphoreGive` before using it as a lock; arrange the start order so that L takes the lock first.

## Self-test

1. A task does 3 ms of work and then calls `vTaskDelay(pdMS_TO_TICKS(10))`. Is its period closer to 10 ms or 13 ms? What about `vTaskDelayUntil(&last, pdMS_TO_TICKS(10))`?
2. A priority 3 task and a priority 1 task become ready at the same time. Which does FreeRTOS run first? If the priority 3 task is a `while(1)` that never blocks, what happens to the priority 1 task?
3. The USART1 receive interrupt is set with `HAL_NVIC_SetPriority(USART1_IRQn, 3, 0)` and calls `xQueueSendFromISR`. What happens? What is the smallest number it should be? Which number does that correspond to in BASEPRI?
4. LED has 128 words, KEY 192 words, UART 256 words. How many bytes do the three stacks take together? In CMSIS-RTOS v2, if `.stack_size` is written as 256, how many words of stack does the task really get?
5. A software timer callback calls `vTaskDelay(100)`. Besides that callback, what else does it hold up?

Answers:

1. Closer to 13 ms. `vTaskDelay` waits 10 more ticks from the moment of the call, and the 3 ms of work comes before it: 3 + 10 = 13. `vTaskDelayUntil` counts from the last wake time, so the work is subtracted and the period is 10 ms.
2. The priority 3 task runs first; a larger task priority number runs first. Since it never blocks, the priority 1 task never runs: the scheduler gives the CPU to a lower task only when every higher task is blocked or suspended.
3. With `configASSERT` defined (CubeMX defines it), it stops in the assert; without it, nothing stops, but the interrupt can break in while the kernel is halfway through updating the queue and corrupt its data. 3 is below 5: this interrupt is more urgent than the most urgent level the kernel can hold off, so kernel critical sections cannot keep it out. The smallest fix is 5; any preemption number from 5 to 15 works. The matching BASEPRI number is `5 << 4 = 0x50`.
4. 128 + 192 + 256 = 576 words, and 576 × 4 = 2304 bytes, about 11% of the 20480 bytes of SRAM. All three come out of the 10240-byte heap, taking 2304 / 10240 = 22.5% of it; add the TCBs, the idle task's 128 words, the queue, and the mutex, and the heap still has room. `.stack_size` is in bytes, so 256 bytes / 4 = 64 words, a quarter of what was meant; for 256 words write `256 * 4`.
5. Every software timer. All callbacks run one after another in the same timer service task; while it sleeps for 100 ms, every other timer callback that comes due waits its turn, and commands such as `xTimerStart` are not processed until it wakes.

## Principle and scope

> [!NOTE]
> From this section to "Pitfalls and sources" is the deep part. It pins the conclusions above to one part number, one manual section, and numbers you can recompute. On a first read you can skip it and come back after the labs.

The rules above hold for any Cortex-M3 running FreeRTOS. The actual numbers need one chip and one project; this chapter uses the STM32F103C8T6 and this repository's `examples/freertos-task`.

**Part number and grouping.** The tick and FromISR in this chapter are pinned to the STM32F103C8T6. The grouping matches chapter 04: `NVIC_PRIORITYGROUP_4`, all 4 bits for preemption priority and 0 bits for subpriority. Once `HAL_Init()` has set it, leave it alone; FreeRTOS wants every priority bit used for preemption, and a different grouping stops in `configASSERT`.

**The tick.** `configTICK_RATE_HZ = 1000`, so one tick is 1 ms. That is an example setting, and a deadline shorter than 1 ms is not a kernel guarantee. SysTick belongs to the kernel. The HAL time base is TIM4, the timer the `examples/freertos-task` README already names. When SysTick has gone to the kernel and HAL has not been given another time base, `HAL_Delay` sticks. See [examples in this repo](#source-project-examples).

**Priority direction.** A numerically larger task priority runs first. In the example KEY is 2 and LED and UART are 1, so when both are ready KEY runs first. The NVIC still treats a smaller number as more urgent. Read task priority the NVIC way, expecting 1 to beat 2, and the whole order comes out reversed. The idle task is 0.

**Where 0x50 comes from.** `5 << (8 − 4) = 0x50`. Only the top 4 bits of an F1 priority byte are implemented ([PM0056](#source-pm0056) Table 42), so a 4-bit priority of 5 is shifted left by 4 before it goes into the register. An interrupt that calls FromISR needs a preemption priority number greater than or equal to 5, that is 5 or a larger number. The example sets `EXTI0` to 5. Setting it to 0, which is also the reset value, stops in `configASSERT`; 4 is too urgent as well. Inside a critical section the kernel writes `0x50` to BASEPRI, which holds off interrupts numbered 5–15 and leaves 0–4 alone ([FreeRTOS on Cortex-M](#source-freertos-priority)). See [FreeRTOS Kernel V11.3.2](#source-freertos-syscall).

**Stack units.** The `xTaskCreate` depth is in words, and one word is 4 bytes. LED is 128 words = 512 bytes. KEY is 192 words = 768 bytes. UART is 256 words = 1024 bytes. Read 128 as 128 bytes and the stack is a quarter of what you meant.

**Delays and locks.** Do 3 ms of work and then call `vTaskDelay(10)`: the call waits another 10 ticks from that moment, so the period is near 13 ms. `vTaskDelayUntil` with 10 ms keeps the period at 10 ms. A mutex protects a shared resource and has priority inheritance; a binary semaphore does not. heap_4 coalesces adjacent free blocks.

**When you change chips.** This part has no FPU and uses the ARM_CM3 port. On a Cortex-M4F with an FPU, such as an F4, switch to the ARM_CM4F port and recompute `configMAX_SYSCALL_INTERRUPT_PRIORITY` from the number of priority bits given in that chip's programming manual.

## Key figures

<p align="center">
  <img src="../../assets/diagrams/sample-15-rtos-prio.svg" width="760" alt="One tick is 1 ms. Task priority 2 runs before priority 1. 128 words are 512 bytes. FromISR needs a numeric priority of 5 or a larger number.">
  <br><sub>▲ Drawn for this book. STM32F103C8T6. The normal path is a 1 ms SysTick, HAL time base TIM4, priority 2 running, priority 1 waiting, an LED stack of 128 words = 512 bytes, and EXTI0 preemption priority 5. The failure path writes that EXTI preemption priority as 0 and stops in configASSERT on FromISR. Sources: [FreeRTOS Kernel V11.3.2](#source-freertos-syscall) and [freertos-task](#source-project-examples).</sub>
</p>

<p align="center">
  <img src="../../assets/gif/rtos-tick.gif" width="640" alt="The tick advances 1 ms at a time, priority 2 holds the CPU, and 128 words equal 512 bytes">
  <br><sub>▲ Auxiliary figure for the web and for posts. It plays only the normal path: 1 ms steps, priority 2 running, priority 1 waiting, 128 words = 512 bytes. Print from the static figure. configASSERT and the SysTick clash are not on this GIF.</sub>
</p>

Read the static figure from top to bottom. The three lines at the top are this chapter's three sets of numbers: a Cortex-M3 with no FPU and `GROUP_4`; a 1 ms tick with the HAL time base on TIM4; and `5 << 4 = 0x50`. The middle panel, marked 正常路径 (normal path), has the priority 2 task running and the priority 1 task waiting, with an LED stack of 128 words = 512 bytes. The panel below it, marked 失败路径 (failure path), writes the EXTI0 priority number as 0, and the first FromISR call stops in the assert. The side notes at the bottom, marked 旁注, list three common misreadings: words read as bytes, HAL left on SysTick, and task priority read in the NVIC direction. The GIF plays only the normal path. `freertos-scheduler.svg`, the animation at the top of the chapter, shows the state transitions in motion; read it next to the state table in section 2.

## Timing and state

The table below puts this chapter's numbers side by side, and every cell can be recomputed with the formulas above. The numbers come from the [freertos-task example](#source-project-examples) and [FreeRTOS Kernel V11.3.2](#source-freertos-syscall):

| Object | Value | Who goes first |
| --- | --- | --- |
| Tick | 1000 Hz | One tick is 1 ms |
| Tasks | priority 2 and priority 1 | 2 before 1, the opposite direction from the NVIC |
| Stacks | 128 words = 512 bytes | KEY 192 words = 768 bytes, UART 256 words = 1024 bytes |
| Interrupt | number 5 may call FromISR | number 0 stops in `configASSERT`; `0x50 = 5 << 4` |
| Time base | the kernel uses SysTick | HAL uses TIM4 |
| Delay | 3 ms of work, then `vTaskDelay(10)` | the period is near 13 ms; `vTaskDelayUntil` of 10 ms stays 10 ms |

One key press takes the CPU through these steps. The last column says who holds the CPU at each step:

| Step | What happens | Who is running |
| --- | --- | --- |
| 1 | A falling edge on PA0; EXTI0 (number 5) enters its interrupt | Whatever task was running is interrupted, most often the idle task |
| 2 | `xQueueSendFromISR` copies 1 byte into the queue, KEY goes from Blocked to Ready, and `woken` becomes `pdTRUE` | The EXTI0 handler |
| 3 | `portYIELD_FROM_ISR(woken)` pends PendSV | The EXTI0 handler |
| 4 | EXTI0 exits and the lowest-priority PendSV runs next, saving the interrupted task's registers and loading KEY's | PendSV |
| 5 | KEY (priority 2) returns from `xQueueReceive`, takes the mutex, and prints a line | The KEY task |
| 6 | KEY goes back to `xQueueReceive` and blocks again; the CPU returns to the highest ready task | LED, UART, or the idle task |

## Pitfalls and sources

Read each row left to right: the symptom first, then the cause and what to do; the last two columns say where the conclusion comes from and how far that source goes.

| Symptom | Cause | What to do | Source | What the source supports |
| --- | --- | --- | --- | --- |
| `HAL_Delay` sticks, or the scheduler does not start | HAL and the kernel both want SysTick | Move the HAL time base to TIM4 | [examples in this repo](#source-project-examples) | The `examples/freertos-task` README names TIM4 as the time base |
| The interrupt stops in `configASSERT` | The preemption number is smaller than 5 | Write `EXTI0` as a number from 5 to 15 | [FreeRTOS](#source-freertos-syscall) | With 4 priority bits, 5 shifted left by 4 is `0x50`; a numerically smaller interrupt must not call FromISR |
| A priority 1 task runs over a priority 2 task | Task priority was treated like the NVIC | A numerically larger task priority runs first | [FreeRTOS](#source-freertos-syscall) | A numerically larger task priority runs first |
| KEY does not run ahead of LED in the example | Both tasks were given the same priority | Write KEY as 2, and LED and UART as 1 | [examples in this repo](#source-project-examples) | In `examples/freertos-task`, KEY's task priority is 2 and LED and UART are 1 |
| The stack says 128 and a print overflows | A word was read as a byte | 128 is in words, which is 512 bytes | [examples in this repo](#source-project-examples) | LED is 128 words, KEY is 192 words, UART is 256 words |
| The key interrupt asserts as soon as it is entered | The EXTI preemption priority is too urgent, or was never set and is still the reset value 0 | Write the `EXTI0` preemption priority as 5 | [examples in this repo](#source-project-examples) | The example sets the `EXTI0` preemption priority to 5 |
| The assert that checks the grouping fires | The grouping does not give all 4 bits to preemption | Do not change the grouping after `HAL_Init()` | [PM0056](#source-pm0056) | Table 45: PRIGROUP sets where the preemption bits and the subpriority bits split |
| Two tasks' UART output interleaves, or whole lines go missing | Two tasks write one UART at the same time with no lock | Wrap each whole transmission in a mutex | [examples in this repo](#source-project-examples) | `examples/freertos-task` protects `uart_print` with a mutex |
| With a binary semaphore as the lock, a high-priority task sometimes waits a long time | A binary semaphore has no priority inheritance, so a medium task cuts in | Switch to `xSemaphoreCreateMutex()` | [FreeRTOS](#source-freertos-syscall) | A mutex has priority inheritance. A binary semaphore does not |
| The period grows | `vTaskDelay(10)` does not include the time already spent before the call | Use `vTaskDelayUntil` for a fixed period | [FreeRTOS Kernel V11.3.2](#source-freertos-1132) | The `vTaskDelay` time counts from the moment of the call |

The CPU-utilization and deadline budget stays out of this table; it is in chapter 28. Button bounce stays out too: the debounce time is a rule of thumb, and neither the FreeRTOS nor the ST manuals give a number for it.

## Related resources

- The official FreeRTOS documentation, and *Mastering the FreeRTOS Real Time Kernel* (the chapters on tasks, queues, semaphores, and scheduling).
- RM0008, *STM32F10xxx Reference Manual*: SysTick (the Cortex-M3 system timebase), NVIC and EXTI (Chapter 9), and USART (Chapter 27).
- Example in this repo: [`examples/freertos-task/`](../../examples/freertos-task/) (CubeMX settings and the full `main.c`).
- Related chapters: [Chapter 04](04-interrupts-nvic.md), Interrupts and NVIC, and [Chapter 17](17-debug.md), Debugging and performance (DWT timing).
- Figure: `../../assets/animations/freertos-scheduler.svg` (vector drawing by the author).

# 04 Interrupts and the NVIC
> 中文：[中断与 NVIC](../04-中断与NVIC.md)

> An interrupt means the CPU does not have to sit and wait on a peripheral. When the event arrives, execution jumps to the handler. That is the core mechanism of a real-time system.

<p align="center">
  <img src="../../assets/animations/nvic-interrupt-flow.svg" width="760" alt="The full interrupt response path">
  <br><sub>▲ Animation: the full interrupt response (stack the context → fetch the vector → ISR → unstack; vector drawing by the author)</sub>
</p>

<!-- video:ch04 -->
<p align="center">
  <video width="640" controls poster="../../assets/video/ch04-nvic.png">
    <source src="../../assets/video/ch04-nvic.mp4" type="video/mp4">
  </video>
  <br><sub>▲ Chapter video with Chinese voice-over (2.5 min). <a href="../../assets/video/ch04-nvic.mp4">MP4</a> · <a href="../../assets/video/ch04-nvic.srt">subtitles</a></sub>
</p>

<details>
<summary>Narration script (Chinese, same text as the subtitles)</summary>

1. 轮询是你不停去问，中断是事情来了敲你的门。主程序可以继续干别的。进了中断服务，办完要清标志，不然门会一直响。
2. NVIC 这道总闸可以分成三档来记：这路中断开了没有，优先级谁高，有没有挂起还没处理。三档看全，才不会觉得中断时灵时不灵。
3. EXTI 的编号就是引脚号。EXTI0 同时只能留给一个端口。PA0 和 PB0 不能一起拿这条线。要两只按键，就换不同的脚号。
4. 这一帧是仓库画的中断路径。引脚边沿先进 EXTI，再由 NVIC 决定要不要打断当前程序，最后才进你写的服务函数。路径上任何一扇门关着，回调都不会来。
5. 优先级不是数字越大越急。F1 上要先看优先级分组切成什么样，才知道哪些位是抢占、哪些是子优先级。抄例程时把分组改了，顺序会整个翻掉。
6. 中断服务要短。别在里面调用会阻塞的延时，也别做很重的打印。置一个标志，或者塞进缓冲区，把慢活交回主循环。服务函数一长，别的中断就饿着。
7. 主循环和中断一起碰的变量，编译器可能会缓存。单字节标志加 volatile。超过一个字的数据，读的时候还得短暂关中断，否则会撕成两半。
8. 口诀：总闸分三档；同一编号的脚，EXTI 只能留一个端口。记住这两句，按键中断的大多数玄学都会消失。
9. 实验用一只按键走下降沿，服务函数里只翻转 PC13。按下能亮、松开不连翻，说明边沿和清标志都做对了。连翻多半是没清，或者抖动没处理。
10. 合上书，三问。EXTI0 能同时留给 PA0 和 PB0 吗？服务函数里为什么别写阻塞延时？总闸那三档各管什么？

</details>
<!-- /video:ch04 -->

## Learning goals

Before this chapter: finish chapter 03, so you can set a pin as a pulled-up input and drive the PC13 LED; know binary, hex, and the bit operations that change one bit, and know what `volatile` means in C (if not, read "Zero-background primer" in chapter 00 first).

- [ ] Say in one sentence how polling and interrupts differ, and give a good use for each
- [ ] Set PA0 up as a falling-edge external interrupt so that one button press toggles the PC13 LED once
- [ ] Name, in order, the three gates an interrupt passes: EXTI, the NVIC, and the CPU mask registers
- [ ] Fill in priorities for two interrupts under `NVIC_PRIORITYGROUP_4` and tell which can interrupt which
- [ ] Explain why an ISR must clear `EXTI_PR` and why it must not call `HAL_Delay()`
- [ ] Protect a variable shared by the main loop and an ISR with `volatile` and a critical section
- [ ] Say why PA0 and PB0 cannot both be external interrupts, and why PB0 needs the AFIO clock

## Core ideas

**In one sentence: an interrupt is a peripheral calling the CPU when something happens. The CPU puts down the program it is running, runs a dedicated function, and then picks up where it left off. Using interrupts well comes down to three things: clear the flag, order the priorities, and protect shared variables.**

### An analogy first

Think of the CPU as someone doing homework at home, and of a peripheral as a courier.

- **Polling**: every few minutes you put the pen down and check the door. You walk over even when nothing has come, and when a parcel does arrive you only find it on your next trip.
- **Interrupt**: you fit a doorbell. When the courier rings, you slip a bookmark into the page, answer the door, sign, come back, and carry on from the bookmark.
- **Priority**: when several bells ring at once, a list drawn up in advance says which door to open first. A smaller number on the list goes first.
- **Clearing the flag**: after signing you have to reset the bell. If you don't, it keeps ringing, and you're up again the moment you sit down.

The analogy stops here. The real "bookmark" is eight registers that hardware pushes onto the stack, which costs a dozen or so clock cycles. The list has only 16 numbers, 0 to 15. And a bell that is never reset sends the CPU straight back into the handler every time it leaves, so the main loop never runs a single line. Sections 3 to 6 give the sources for these rules.

### 1. Polling and interrupts: two ways to wait for an event

**Polling** means the main loop reads the pin over and over: `while (1) { if (HAL_GPIO_ReadPin(...) == GPIO_PIN_RESET) { ... } }`. With an **interrupt**, hardware watches the pin, and when the event comes the CPU jumps by itself into a function with a fixed name. That function is the **interrupt service routine** (ISR); for the button it is `EXTI0_IRQHandler`.

| Comparison | Polling | Interrupt |
| --- | --- | --- |
| What the CPU does meanwhile | Keeps checking, busy even when nothing happens | Other work, or sleeps to save power |
| How soon the event is seen | Up to one whole polling period | The ISR starts after about 167 ns of stacking (section 6), unless a more urgent ISR is running |
| Can a short pulse be missed | Yes, if it comes and goes between two reads | The EXTI pending bit remembers it |
| Code difficulty | Low | Medium: flags, priorities, and shared variables |
| Good for | Rare or slow events, or things you check on a schedule anyway | Events that can come at any moment and need a quick response |

To choose, ask two questions: how often does the event come, and how late can you handle it. A button press, which can come at any time and wants a quick answer, suits an interrupt. A temperature you only need once a second suits polling, or a timer from chapter 05 that reads it on schedule.

<p align="center">
  <img src="../../assets/animations/gpio-input-interrupt.svg" width="760" alt="One button read two ways: by polling and by an EXTI interrupt">
  <br><sub>▲ Animation: one button read by polling and by an EXTI interrupt, and how to pick among the three trigger edges (vector drawing by the author). The figure's "you must enable the AFIO clock" is the safe habit; section 3 gives the exact condition.</sub>
</p>

### 2. Three gates on the way in

For a falling edge on the button to become one run of the ISR, it passes three gates. If any of them is shut, the ISR does not run:

```text
PA0 falling edge ──▶ EXTI0: sees the edge, sets the pending bit in EXTI_PR
                 ──▶ NVIC: is this interrupt enabled? is its priority high enough? if so, mark it pending
                 ──▶ CPU: is PRIMASK or another mask register shut?
                 ──▶ run EXTI0_IRQHandler
```

- **EXTI** (external interrupt/event controller): the block in the chip that watches pins for edges. When it sees one, it sets the matching bit in its pending register `EXTI_PR` and passes the request to the NVIC.
- **NVIC** (Nested Vectored Interrupt Controller): the interrupt dispatcher inside the Cortex-M3 core. For each interrupt it keeps three things: whether it is on (enable), who goes first (priority), and whether it is waiting (pending).
- **The CPU mask registers**: PRIMASK and a few others can hold back a whole group of interrupts at once. Section 10 covers them.

How does the CPU know which function to jump to? At the start of flash there is a **vector table** with one slot per interrupt, and each slot holds the address of that interrupt's ISR. In RM0008 Rev 21 Table 63, EXTI0 is position 6, at address 0x0000_0058. The startup file puts the name `EXTI0_IRQHandler` into that slot, so your function name must match it exactly.

Not every one of the 16 GPIO lines has its own slot (RM0008 Rev 21 Table 63):

| EXTI lines | ISR name | Notes |
| --- | --- | --- |
| EXTI0–EXTI4 | `EXTI0_IRQHandler` … `EXTI4_IRQHandler` | One each |
| EXTI5–EXTI9 | `EXTI9_5_IRQHandler` | Five lines share one |
| EXTI10–EXTI15 | `EXTI15_10_IRQHandler` | Six lines share one |

When you use one of the two shared handlers, the ISR first reads `EXTI_PR` to see which line fired, then handles and clears each line on its own.

### 3. EXTI external interrupts: the pin number is the line number

**Conclusion: EXTIn can connect to pin n of one port only. If PA0, PB0, and PC0 all want EXTI0, you get to pick one.**

Setting up an EXTI line means filling in this table from top to bottom. HAL's `HAL_GPIO_Init()` fills the first five rows for you; the last row is yours to do in the ISR. All sources are RM0008 Rev 21:

| Item | What it is | Source |
| --- | --- | --- |
| EXTI lines | The F103 has 19: EXTI0–EXTI15 go to GPIO, EXTI16 to the PVD, EXTI17 to the RTC alarm, EXTI18 to USB wakeup | Sections 10.2 and 10.2.5 |
| Port select | AFIO_EXTICR1–AFIO_EXTICR4, 4 bits per line: 0000 is port A, 0001 port B, 0010 port C; reset value 0x0000 | Sections 9.4.3–9.4.6 |
| Rising edge | Write 1 to the line's bit in EXTI_RTSR | Section 10.3.3 |
| Falling edge | Write 1 to the line's bit in EXTI_FTSR; set both for both edges | Section 10.3.4 |
| Let the request through | Write 1 to the line's bit in EXTI_IMR so the request reaches the NVIC | Section 10.3.1 |
| Pending bit | An edge sets the line's bit in EXTI_PR; only writing 1 to it clears it (rc_w1) | Section 10.3.6 |

AFIO has one detail that trips people up. After reset, EXTICR is all zeros, so all 16 lines connect to port A, and PA0 fires even with the AFIO clock off. PB0 is different: changing EXTI0's 4 bits to 0001 requires the AFIO clock first, according to the note under Figure 21 in section 10.2.5. In practice, without the clock the write does not take, and EXTI0 stays on port A; that is the usual observed behavior, while the manual itself only says to enable the AFIO clock first. This is behind the common "port A works, port B does nothing" complaint. Make enabling the AFIO clock a habit and you never need to remember the exception.

Why the pending bit must be cleared: PM0056 Rev 7 section 4.3.9 says that if the request is not removed before the ISR returns, the interrupt becomes pending again and the CPU goes straight back into the same ISR. The main loop never runs a line, and the board looks frozen.

Which edge: with the chapter 03 section 6 wiring, the button goes to GND and the pin has a pull-up, so the moment of pressing is a falling edge. Set EXTI_FTSR.

### 4. NVIC priority: a smaller number is more urgent

**Conclusion: a smaller number means a higher priority, and only the preemption priority decides whether a running ISR can be interrupted.**

The F103 gives each interrupt an 8-bit priority field and uses only the top 4 bits, so there are just 16 levels, 0 to 15 (RM0008 Rev 21 section 10.1; PM0056 Rev 7 section 4.3.7, Table 42). A **grouping** then splits those 4 bits in two: the first part is the **preemption priority** (PM0056 calls it the group priority), and the rest is the **subpriority**. There are only three rules (PM0056 Rev 7 section 2.3.6):

- An ISR with a smaller preemption number can interrupt one with a larger preemption number. One ISR interrupting another is called **nesting**.
- Two with the same preemption number cannot interrupt each other; the later one waits as pending. A different subpriority does not change that.
- When several requests are waiting, compare preemption first, then subpriority; if both are equal, the lower IRQ number goes first.

### 5. Which grouping: how the 4 bits are split

**Conclusion: HAL defaults to GROUP_4, which gives all 4 bits to preemption. A project has one grouping; set it once at the start and leave it alone.**

The split is set by the PRIGROUP field of the core register SCB_AIRCR (PM0056 Rev 7 section 4.4.5, Table 45). HAL spells it with macros:

| HAL grouping macro | PRIGROUP | Preemption bits | Subpriority bits | Preemption levels |
| --- | --- | --- | --- | --- |
| `NVIC_PRIORITYGROUP_0` | 0b111 | 0 | 4 | 1, so none can interrupt another |
| `NVIC_PRIORITYGROUP_1` | 0b110 | 1 | 3 | 2 |
| `NVIC_PRIORITYGROUP_2` | 0b101 | 2 | 2 | 4 |
| `NVIC_PRIORITYGROUP_3` | 0b100 | 3 | 1 | 8 |
| `NVIC_PRIORITYGROUP_4` | 0b011 | 4 | 0 | 16, the `HAL_Init()` default |

Going down the table, preemption gets more bits. HAL's default is the last row: all 4 bits go to preemption, so the third argument of `HAL_NVIC_SetPriority()` (the subpriority) has no bits to land in. Write 0.

An example: under GROUP_4, give EXTI0 preemption 1 and TIM2 preemption 2. If the TIM2 ISR is running when you press the button, 1 is smaller than 2, so EXTI0 interrupts TIM2, finishes, and TIM2 resumes. Give both a 1 and EXTI0 can only wait as pending until TIM2 returns. Key figures draws exactly these two paths.

Change the grouping and every interrupt's number changes meaning. This table gives the usual choices:

| Situation | Grouping | Why |
| --- | --- | --- |
| No RTOS | GROUP_4 | You compare one number, which is easiest |
| FreeRTOS | GROUP_4 | [FreeRTOS's Cortex-M notes](#source-freertos-priority) recommend giving all priority bits to preemption; chapter 15 covers it |
| You really need an order among equals | GROUP_2 or GROUP_3 | Fewer preemption levels in exchange for subpriority |

### 6. Entering and leaving an interrupt: what hardware does for you

The **stack** is an area of RAM used last in, first out; the stack pointer SP marks its top. **Stacking** copies register values onto it, and **unstacking** copies them back. When the CPU is interrupted, hardware does most of the steps in this table on its own:

| Step | Who | What happens |
| --- | --- | --- |
| 1 | EXTI | PA0 has a falling edge; bit 0 of EXTI_PR is set and the request goes to the NVIC |
| 2 | NVIC | EXTI0 is enabled and its priority is high enough, so the NVIC marks it pending and tells the CPU |
| 3 | CPU | Compares priorities and decides to respond after the current instruction |
| 4 | Hardware | Pushes 8 registers: xPSR, PC, LR, R12, R3, R2, R1, R0; at the same time it fetches the address of `EXTI0_IRQHandler` from the vector table |
| 5 | Hardware | Writes a special return value (EXC_RETURN) into LR and jumps into the ISR |
| 6 | Your code | Clears EXTI_PR and does as little as possible |
| 7 | Hardware | When the ISR returns, recognizes EXC_RETURN, unstacks, and goes back to where it was interrupted |

Steps 4, 5, and 7 are hardware, which is why an ISR can be an ordinary C function that saves no registers itself; step 6 is the only one that's yours. Those three steps come from PM0056 Rev 7 section 2.3.7.

Eight registers are 32 bytes. Arm's nominal interrupt latency for the Cortex-M3 is about 12 clock cycles, which at 72 MHz is `12 / 72e6 ≈ 167 ns`. The conditions behind that number and its source are in Principle and scope.

On the way out, hardware has two more ways to save time:

| Mechanism | When it happens | What it saves |
| --- | --- | --- |
| Tail-chaining | Another interrupt is already pending when an ISR ends | One unstack and the stack right after it; the next ISR starts directly |
| Late arrival | A request with higher preemption arrives during stacking | The stacking is not redone; the more urgent ISR goes first |

Both save time only; neither changes who can interrupt whom. The big cost is how long the ISR itself runs: the shorter the ISR, the less every other interrupt waits.

### 7. Variables shared by the main loop and an ISR

**Conclusion: mark variables that both an ISR and the main loop use as `volatile`; when the data is wider than one word, the main loop briefly disables interrupts while reading it.**

`volatile` tells the compiler that someone else may change the variable at any time, so every use must really read memory instead of reusing an old copy in a register. Without it, the line below may become an endless loop once optimization is on, because the compiler reads `g_flag` only once:

```c
static uint8_t g_flag;        /* volatile is missing */
while (g_flag == 0) { }       /* the ISR sets it to 1, and this loop never sees it */
```

The CPU reads a one-byte flag or a 32-bit variable in one instruction. A variable wider than a word, such as `uint64_t`, takes the compiler two reads. If the ISR changes it between those two reads, the upper 32 bits and the lower 32 bits come from two different moments, and the value is "torn". The fix is a **critical section**: a short stretch of code that no interrupt may break into.

| Spelling | What it does | When to use it |
| --- | --- | --- |
| `volatile` | Every read and write really goes to memory | Variables shared by an ISR and the main loop |
| `__disable_irq()` / `__enable_irq()` | Sets / clears PRIMASK, shutting / opening every interrupt of configurable priority | Very short critical sections |
| `__get_PRIMASK()` / `__set_PRIMASK()` | Reads / writes back PRIMASK | Ending a critical section by restoring the old state, so interrupts are not opened by mistake |
| `__DSB()` | Later instructions wait until every earlier read and write has completed | Right after clearing a peripheral flag when the ISR is about to return |

These functions and the instructions behind them are in PM0056 Rev 7 section 3.2, Tables 21 and 22; section 3.9.4 explains `__DSB()`. Keep critical sections short: while interrupts are off, every interrupt of configurable priority has to wait.

A rule of thumb for clearing a peripheral flag: do it at the start of the ISR, not as the last line. If it is the last line, the write may not have reached the peripheral before the ISR returns, and you get one extra entry.

### 8. SysTick and the HAL delay: what not to do in an ISR

> [!WARNING]
> Do not call `HAL_Delay()` in an ISR. It waits on a count that the SysTick interrupt raises once every 1 ms. If the current ISR's priority number is not larger than SysTick's, SysTick cannot break in, the count stops, and the program hangs right there.

| Don't | Why | Instead |
| --- | --- | --- |
| `HAL_Delay()` | The warning above | Set a flag in the ISR and wait in the main loop |
| `printf()` to a serial port | At 115200 baud in 8N1 format, one byte with its start and stop bits is 10 bits, taking `10 / 115200 ≈ 87 µs` (chapter 06); a few dozen characters take a few milliseconds | Put the data in a buffer and send it from the main loop |
| Floating point, long loops | The Cortex-M3 has no floating-point unit, so floats run in software | Record raw data in the ISR and compute in the main loop |

SysTick's priority is `TICK_INT_PRIORITY` in your project's `stm32f1xx_hal_conf.h`; open the file to see it. An ISR should do only three kinds of work: clear the flag, move the data out, and set a flag.

### 9. The NVIC registers

HAL's `HAL_NVIC_EnableIRQ()`, `HAL_NVIC_SetPriority()`, and `HAL_NVIC_SetPriorityGrouping()` end up writing the core registers below. EXTI0 is IRQ number 6, and the last column uses it as the example. Sources: PM0056 Rev 7 sections 4.3.2 to 4.3.7 and section 4.4.5:

| Register (CMSIS spelling) | What it does | Where EXTI0 sits |
| --- | --- | --- |
| ISER (`NVIC->ISER[0]`) | Writing 1 to a bit enables that interrupt; writing 0 has no effect | Bit 6 of `ISER[0]` |
| ICER (`NVIC->ICER[0]`) | Writing 1 to a bit disables that interrupt | Bit 6 of `ICER[0]` |
| ISPR / ICPR | Writing 1 sets / clears pending | Bit 6 |
| IABR | Read-only; 1 means this interrupt is being serviced | Bit 6 |
| IPR (`NVIC->IP[6]`) | 8 bits per interrupt, only the top 4 bits [7:4] are used; the low 4 read as zero | `IP[6]` |
| PRIGROUP in SCB_AIRCR (bits 10:8) | How the 4 bits split into preemption and subpriority; a write must carry the key 0x5FA in the top 16 bits or it is ignored | One for the whole chip |

One ISER covers 32 interrupts: `ISER[0]` covers IRQ 0–31 and `ISER[1]` covers 32–63 (PM0056 Rev 7 Table 41). An interrupt's pending bit can be set even while the interrupt is disabled (PM0056 Rev 7 section 4.3.10), so clearing pending before enabling keeps an old request from rushing in the moment you enable it.

### 10. Three mask registers: PRIMASK, FAULTMASK, BASEPRI

**Conclusion: PRIMASK holds back every interrupt of configurable priority; FAULTMASK holds back HardFault as well and leaves only NMI; BASEPRI holds back only the band whose priority number is greater than or equal to its value.**

NMI (non-maskable interrupt) and HardFault have fixed negative priorities, NMI −2 and HardFault −1, above every configurable one (PM0056 Rev 7 section 2.3.2, Table 16). The table below comes from Tables 7, 8, and 9 in section 2.1.3 of the same manual:

| Register | Holds back, when set to 1 or a nonzero value | Who still gets in | Usual spelling |
| --- | --- | --- | --- |
| PRIMASK | Every exception of configurable priority | NMI, HardFault | `__disable_irq()` / `__enable_irq()` |
| FAULTMASK | Every exception except NMI | NMI | `__disable_fault_irq()` / `__enable_fault_irq()` |
| BASEPRI | Exceptions whose priority number is greater than or equal to BASEPRI | The smaller, more urgent numbers | `__set_BASEPRI(prio << (8 - __NVIC_PRIO_BITS))` |

Like the priority fields, BASEPRI uses only its top 4 bits, so a priority from 0 to 15 is shifted left by 4 before it is written; `__NVIC_PRIO_BITS` is 4 in the F103 headers. Writing 0 to BASEPRI holds back nothing. An RTOS uses it to shut off only "some" interrupts, which chapter 15 relies on.

Back to EXTI to finish: lines are shared by pin number. PA0 and PB0 are both on EXTI0, so they cannot both be external interrupts; a second button needs a different pin number, such as PA1. To change the port, write `AFIO->EXTICR` on F1 or `SYSCFG->EXTICR` on F4. Neither adds a second line.

Motto: **the master gate has three settings. For one pin number, EXTI keeps only one port.** The "three settings" are the three things the NVIC keeps for each interrupt: enabled or not, which goes first, and whether it is pending.

## Hardware and wiring

| Board | Peripheral | Pin | Notes |
| --- | --- | --- | --- |
| BluePill | Button (EXTI0) | PA0 (LQFP48 pin 10) | Other side to GND, internal pull-up on, a press gives a falling edge |
| BluePill | Onboard LED | PC13 | Lights on low (chapter 03) |
| BluePill | Button moved to PB0 (for the self-test and the register version) | PB0 (LQFP48 pin 18) | Also to GND; enable the AFIO clock before writing EXTICR |

```text
Button (reads 0 when pressed): PA0 ──[button]── GND        PA0 internal pull-up on; reads 1 released; the press is a falling edge
Onboard LED (write 0 to light): 3.3 V ──[resistor]──▶|── PC13  the chapter 03 circuit, nothing to add
```

The pin numbers come from DS5319 Rev 20 Table 5. The button needs no external resistor; the on-chip pull-up is enough. Never wire the button to 3.3 V and also enable the pull-up: the pin then reads high whether pressed or not, and there is never an edge.

## Code

This program goes with Labs 1 and 2: each press of PA0 toggles the PC13 LED once, and the ISR also counts falling edges so you can see how many edges one press bounces out.

```c
/* exti_key.c -- PA0 button falling-edge interrupt: the ISR only takes notes, the main loop confirms and toggles PC13 */
#include "stm32f1xx_hal.h"

#define LED_PIN       GPIO_PIN_13
#define LED_PORT      GPIOC
#define KEY_PIN       GPIO_PIN_0
#define KEY_PORT      GPIOA
#define KEY_PREEMPT   1U     /* preemption priority (example setting) */
#define KEY_SUB       0U     /* subpriority: GROUP_4 has no subpriority bits, so 0 */
#define DEBOUNCE_MS   20U    /* time to let the bounce settle (rule of thumb) */

static volatile uint8_t  g_key_flag  = 0;   /* set to 1 by the ISR, cleared by the main loop */
static volatile uint64_t g_key_edges = 0;   /* falling edges counted by the ISR; 64-bit, so read it with interrupts off */
uint64_t g_edges_seen = 0;                  /* edge count the main loop last read (watch in the debugger) */
uint32_t g_presses    = 0;                  /* presses the main loop confirmed (watch in the debugger) */

void SystemClock_Config(void);

/* Read the 64-bit count: two memory reads that the ISR must not split */
static uint64_t read_edges(void)
{
    uint32_t primask = __get_PRIMASK();   /* remember the current on/off state */
    __disable_irq();                      /* PRIMASK = 1 */
    uint64_t n = g_key_edges;
    __set_PRIMASK(primask);               /* reopen only if it was open before */
    return n;
}

int main(void)
{
    HAL_Init();                    /* grouping becomes NVIC_PRIORITYGROUP_4, SysTick fires every 1 ms */
    SystemClock_Config();          /* 72 MHz, see chapter 02 */

    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_GPIOC_CLK_ENABLE();
    __HAL_RCC_AFIO_CLK_ENABLE();   /* F1: enable the AFIO clock before writing AFIO_EXTICR */

    GPIO_InitTypeDef io = {0};

    io.Pin   = LED_PIN;            /* PC13 push-pull output; the onboard LED lights on low */
    io.Mode  = GPIO_MODE_OUTPUT_PP;
    io.Pull  = GPIO_NOPULL;
    io.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(LED_PORT, &io);

    io.Pin  = KEY_PIN;             /* PA0: pulled-up input, falling edge triggers EXTI0 */
    io.Mode = GPIO_MODE_IT_FALLING;
    io.Pull = GPIO_PULLUP;
    HAL_GPIO_Init(KEY_PORT, &io);  /* also writes EXTICR, EXTI_FTSR, and EXTI_IMR */

    HAL_NVIC_SetPriority(EXTI0_IRQn, KEY_PREEMPT, KEY_SUB);
    HAL_NVIC_EnableIRQ(EXTI0_IRQn);

    while (1)
    {
        if (g_key_flag)
        {
            HAL_Delay(DEBOUNCE_MS);                                     /* waiting in the main loop is safe */
            if (HAL_GPIO_ReadPin(KEY_PORT, KEY_PIN) == GPIO_PIN_RESET)  /* still low: a real press */
            {
                HAL_GPIO_TogglePin(LED_PORT, LED_PIN);
                g_presses++;
                g_edges_seen = read_edges();
            }
            g_key_flag = 0;   /* also clears flags that the bounce set during the wait */
        }
    }
}

/* The name must match the startup file's vector table exactly */
void EXTI0_IRQHandler(void)
{
    if (__HAL_GPIO_EXTI_GET_IT(KEY_PIN) != RESET)
    {
        __HAL_GPIO_EXTI_CLEAR_IT(KEY_PIN);   /* write 1 to bit 0 of EXTI_PR to clear the pending bit */
        g_key_edges++;
        g_key_flag = 1;                      /* take notes only; the slow work goes to the main loop */
    }
}
```

Piece by piece:

- `HAL_Init()` sets the grouping to `NVIC_PRIORITYGROUP_4` and makes SysTick interrupt every 1 ms, which is what `HAL_Delay()` counts.
- `__HAL_RCC_AFIO_CLK_ENABLE()`: PA0 fires without it, because EXTICR selects port A after reset; PB0 needs it (section 3). Some HAL versions turn it on inside `HAL_GPIO_Init()`; writing the line yourself means nothing breaks when the library changes.
- `GPIO_MODE_IT_FALLING` with `GPIO_PULLUP`: released, the pull-up holds the pin high; pressed, the pin goes to ground; the moment it drops is the falling edge.
- `HAL_NVIC_SetPriority(EXTI0_IRQn, 1, 0)`: preemption 1, subpriority 0. Under GROUP_4 the third argument has no bits to land in, so it is 0.
- The first thing `EXTI0_IRQHandler` does is clear the pending bit; then it does only two quick things: count, and set a flag.
- The main loop waits `DEBOUNCE_MS` and reads again; only two low readings count as a real press. `g_key_flag = 0` comes last, so flags set by the bounce during the wait are cleared too.
- `read_edges()` saves the old state with `__get_PRIMASK()` and restores it with `__set_PRIMASK()`. Ending with `__enable_irq()` instead would turn interrupts on by mistake if they were already off before the call.
- `g_edges_seen` and `g_presses` are not `static`, so the compiler does not optimize away these two write-only variables and the debugger can see them.

Here is the same setup in registers, with the button moved to PB0. It shows which registers HAL writes for you and which step the AFIO clock matters for:

```c
/* Register version: EXTI0 moved to PB0, falling edge */
RCC->APB2ENR |= RCC_APB2ENR_IOPBEN | RCC_APB2ENR_AFIOEN;   /* clocks for port B and AFIO */

GPIOB->CRL &= ~(GPIO_CRL_MODE0 | GPIO_CRL_CNF0);           /* clear PB0's 4 bits first */
GPIOB->CRL |= GPIO_CRL_CNF0_1;                             /* MODE = 00, CNF = 10: input with pull-up/pull-down */
GPIOB->BSRR = GPIO_BSRR_BS0;                               /* ODR0 = 1: choose pull-up */

AFIO->EXTICR[0] &= ~AFIO_EXTICR1_EXTI0;                    /* clear EXTI0's 4 bits first */
AFIO->EXTICR[0] |= AFIO_EXTICR1_EXTI0_PB;                  /* 0001: EXTI0 on PB0; without the AFIO clock this does nothing */

EXTI->FTSR |= EXTI_FTSR_TR0;                               /* falling edge */
EXTI->RTSR &= ~EXTI_RTSR_TR0;                              /* no rising edge */
EXTI->PR    = EXTI_PR_PR0;                                 /* write 1 to clear any leftover pending bit */
EXTI->IMR  |= EXTI_IMR_MR0;                                /* let this request through */

NVIC_SetPriority(EXTI0_IRQn, NVIC_EncodePriority(NVIC_GetPriorityGrouping(), 1, 0));
NVIC_EnableIRQ(EXTI0_IRQn);                                /* writes bit 6 of NVIC->ISER[0] */
```

- `EXTI->PR = EXTI_PR_PR0;` uses plain assignment, not `|=`. In this register a 1 clears and a 0 does nothing, so `|=` would read back every other pending bit, write 1s to them, and clear them all.
- `NVIC_EncodePriority()` packs "preemption 1, subpriority 0" into one number for the current grouping. That is the step inside HAL's `HAL_NVIC_SetPriority()`.

Lab 3 needs a second interrupt. Add the pieces below to `exti_key.c`, call `tim2_init()` before `while (1)`, and delete the `HAL_GPIO_TogglePin()` line in the main loop so that only the two ISRs drive the LED. Chapter 05 explains how PSC and ARR are worked out:

```c
/* Lab 3: TIM2 interrupts once a second and busy-waits in its ISR on purpose, leaving a window for EXTI0 */
#define TIM2_PREEMPT  2U          /* start with 2, then change to 1 and compare */
#define BUSY_LOOPS    3000000U    /* example setting: keeps the TIM2 ISR busy for a few hundred ms; adjust to taste */

TIM_HandleTypeDef htim2;

static void tim2_init(void)
{
    __HAL_RCC_TIM2_CLK_ENABLE();
    htim2.Instance           = TIM2;
    htim2.Init.Prescaler     = 7199;                /* 72 MHz / 7200 = 10 kHz */
    htim2.Init.CounterMode   = TIM_COUNTERMODE_UP;
    htim2.Init.Period        = 9999;                /* 10 kHz / 10000 = 1 Hz */
    htim2.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
    HAL_TIM_Base_Init(&htim2);
    HAL_NVIC_SetPriority(TIM2_IRQn, TIM2_PREEMPT, 0);
    HAL_NVIC_EnableIRQ(TIM2_IRQn);
    HAL_TIM_Base_Start_IT(&htim2);
}

void TIM2_IRQHandler(void)
{
    HAL_TIM_IRQHandler(&htim2);
}

void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim)
{
    if (htim->Instance == TIM2)
    {
        HAL_GPIO_WritePin(LED_PORT, LED_PIN, GPIO_PIN_RESET);    /* LED on: busy-wait starts */
        for (volatile uint32_t i = 0; i < BUSY_LOOPS; i++) { }   /* for the lab only; real code never busy-waits in an ISR */
        HAL_GPIO_WritePin(LED_PORT, LED_PIN, GPIO_PIN_SET);      /* LED off: busy-wait ends */
    }
}

/* Replace the earlier EXTI0_IRQHandler with this one */
void EXTI0_IRQHandler(void)
{
    if (__HAL_GPIO_EXTI_GET_IT(KEY_PIN) != RESET)
    {
        __HAL_GPIO_EXTI_CLEAR_IT(KEY_PIN);
        HAL_GPIO_WritePin(LED_PORT, LED_PIN, GPIO_PIN_SET);      /* LED off: the EXTI0 ISR ran */
        g_key_edges++;
        g_key_flag = 1;
    }
}
```

While the LED is on, the TIM2 ISR is busy-waiting; the moment the EXTI0 ISR runs, the LED goes off. However long the LED stays on after you press, that is how long EXTI0 waited.

The full project is in [`examples/exti-key/`](../../examples/exti-key/). It uses HAL's callback style: `EXTI0_IRQHandler()` only calls `HAL_GPIO_EXTI_IRQHandler()`, which clears the pending bit and then calls the `HAL_GPIO_EXTI_Callback()` you write.

## Hands-on labs

1. **Lab 1: one press, one toggle.** Flash the program above and press the PA0 button.
   - Expected: each press switches the PC13 LED between on and off; holding the button does not make it blink.
   - How to check: press slowly 10 times and the LED changes state 10 times; pause the program and read `g_presses` in the debugger, which should be 10.
   - If it fails, check first: nothing toggles at all, check the GPIOA clock and the spelling of `EXTI0_IRQHandler`; the program freezes, check that the ISR clears the pending bit; one press sometimes toggles twice, raise `DEBOUNCE_MS` a little.
2. **Lab 2: count the bounce.** After 10 presses, pause the program and compare `g_presses` with `g_edges_seen`.
   - Expected: `g_edges_seen` is usually larger than `g_presses`; the extra counts are falling edges from contact bounce. A few to a dozen or so extra is common and depends on the button (rule of thumb).
   - How to check: put a logic analyzer on PA0 and zoom in on a press; you can see the level jump back and forth a few times within a few milliseconds, roughly matching the count.
   - If it fails, check first: if the two numbers are exactly equal, the button may simply be good, or the count may never have run. Set a breakpoint on `g_key_edges++` to find out.
3. **Lab 3: let EXTI0 interrupt TIM2.** Change the program as in the last part of Code. PC13 now lights for a stretch every second; while it is lit, the TIM2 ISR is busy-waiting.
   - Expected: with `TIM2_PREEMPT` at 2, press while the LED is lit and it goes off at once; change it to 1 (the same as EXTI0), press while the LED is lit, and it stays on until the stretch is over.
   - How to check: put a logic analyzer on PA0 and PC13 together. With preemption 1 against 2, PC13 goes high (LED off) almost at the same time as the PA0 falling edge; with 1 against 1, PC13 goes high only when the busy-wait ends.
   - If it fails, check first: if the two settings look the same, make sure nothing after `HAL_Init()` changed the grouping; then raise `BUSY_LOOPS` until the lit stretch is long enough to tell apart by eye.

## Self-test

1. After `__disable_irq()`, can HardFault still get in? What about NMI?
2. The grouping is GROUP_4. TIM2 is set with `HAL_NVIC_SetPriority(TIM2_IRQn, 2, 0)` and its ISR is running. Can EXTI0 set to `(2, 1)` interrupt it? What about `(1, 0)`?
3. BASEPRI is written as `5 << 4` (priority 5 shifted left by 4). Of two interrupts with priority numbers 3 and 7, which can still get in?
4. At 72 MHz, how many nanoseconds do 12 clock cycles of stacking take? If flash wait states made it 14 cycles, how many then?
5. You move the button to PB0 in the register version but forget `RCC_APB2ENR_AFIOEN`. What happens when you press the PB0 button, and which pin is EXTI0 listening to?

Answers:

1. Both get in. PRIMASK only holds back exceptions of configurable priority; HardFault and NMI have fixed priorities and are not among them (PM0056 Rev 7 Table 7).
2. `(2, 1)` cannot. Both have preemption 2, and equal preemption does not nest; besides, GROUP_4 has no subpriority bits, so that 1 has nowhere to go. EXTI0 waits as pending until TIM2 returns. `(1, 0)` can, because 1 is smaller than 2.
3. 3 gets in and 7 does not. BASEPRI holds back exceptions whose priority number is greater than or equal to 5; 7 ≥ 5 is held back and 3 < 5 passes (PM0056 Rev 7 Table 9).
4. `12 / 72e6 ≈ 1.67e-7 s ≈ 167 ns`; `14 / 72e6 ≈ 1.94e-7 s ≈ 194 ns`. Both are only the time to get in, not the ISR body.
5. PB0 does nothing. The manual requires the AFIO clock before writing EXTICR; without it the write does not take, EXTI0's 4 bits keep the reset value 0000, which is port A, and EXTI0 is still listening to PA0 (RM0008 Rev 21 sections 9.4.3 and 10.2.5).

## Principle and scope

> [!NOTE]
> From this section to "Pitfalls and sources" is the deep part. It pins the conclusions above to one part number, one manual section, and numbers you can recompute. On a first read you can skip it and come back after the labs.

**Part number, clock, and grouping.** Every number in this chapter is for the STM32F103C8T6. The clock is the Appendix D setting: SYSCLK = HCLK = 72 MHz. The grouping is HAL's default `NVIC_PRIORITYGROUP_4`: 4 preemption bits and 0 subpriority bits, and a smaller number is a higher logical priority. That default is written by `HAL_Init()` in STM32CubeF1; it comes from the HAL source, not from a manual.

**Who can interrupt whom.** [PM0056 Rev 7](#source-pm0056-nvic) section 2.3.6 says only the preemption priority (the manual's group priority) decides whether an exception can interrupt; the subpriority only orders requests that are already pending; when both are equal, the lower IRQ number goes first. `GROUP_4` has no subpriority bits, so under this grouping the subpriority argument of `HAL_NVIC_SetPriority()` creates no order at all. Change the grouping and the same number stands for a different preemption level: compare again under the new grouping, never with the old numbers.

**What stacking costs.** Same manual, section 2.3.7: on exception entry, hardware pushes 8 words, from high address to low xPSR, PC, LR, R12, R3, R2, R1, R0, and SP ends at R0; the vector fetch runs at the same time as the stacking. PM0056 gives no cycle count. About 12 HCLK is Arm's nominal figure in the Arm Cortex-M3 Technical Reference Manual r1p1 (the interrupt latency section), which assumes zero-wait-state memory. At 72 MHz the F103 flash needs 2 wait states (RM0008 Rev 21 section 3.3.3), so a measurement may show a few more cycles. With 12, `12 / 72e6 ≈ 167 ns`. Those 167 ns are only the time to get in, not the ISR body, and are no budget for the ISR.

**Tail-chaining and late arrival.** The same section describes two shortcuts: tail-chaining skips "unstack, then stack again" when an ISR exits and another is already pending; late arrival lets a higher-preemption request that comes during stacking go first. Neither changes who has the right to interrupt; a lower priority never slips into a higher-priority ISR through tail-chaining. PM0056 prints no tail-chain cycle count, and this book does not supply one.

**The three mask registers.** [PM0056 Rev 7](#source-pm0056-nvic) section 2.1.3, Tables 7, 8, and 9: PRIMASK = 1 holds back every exception of configurable priority, while NMI and HardFault still enter; FAULTMASK = 1 also holds back HardFault and leaves only NMI, and hardware clears it on return from any exception except NMI; a nonzero BASEPRI holds back exceptions whose priority number is greater than or equal to it. NMI takes no part in the EXTI0 versus TIM2 preemption comparison. On the F103 a common NMI source is the clock security system (CSS); see chapter 02.

**The boundary with an RTOS.** This bare-metal setup does not automatically meet the chapter 15 FromISR rule. FreeRTOS requires that an interrupt calling FromISR functions has a logical priority no higher than the level set by `configMAX_SYSCALL_INTERRUPT_PRIORITY`, which in numbers means not smaller than it ([FreeRTOS's notes](#source-freertos-priority)). The actual number stays in chapter 15.

**This EXTI setup holds only on F1.** [RM0008 Rev 21](#source-rm0008-exti): EXTI lines are shared by pin number, so PA0 and PB0 are both on EXTI0 and only one can be chosen at a time. The choice lives in AFIO_EXTICR1 to AFIO_EXTICR4, sections 9.4.3 to 9.4.6, 4 bits per line, reset value 0x0000, which selects port A for every line. Enable the AFIO clock before writing EXTICR (the note under Figure 21 in section 10.2.5). The pending bit is in EXTI_PR (section 10.3.6) and is cleared by writing 1. Section 9.2.7 is `GPIOx_LCKR`, not EXTICR. Families such as F4 move these select registers into SYSCFG (SYSCFG_EXTICR, see RM0090 Rev 22), and "enable the AFIO clock first" does not apply there.

## Key figures

<p align="center">
  <img src="../../assets/diagrams/sample-04-exception-stack.svg" width="760" alt="Preemption 1 can interrupt preemption 2; a later request at the same preemption 1 cannot nest">
  <br><sub>▲ Drawn for this book. STM32F103C8T6, NVIC_PRIORITYGROUP_4. Normal path: TIM2 runs at preemption 2, and EXTI0 (PA0, EXTI0_IRQn) at preemption 1 and subpriority 0 interrupts it; eight registers are stacked, from high address to low xPSR, PC, LR, R12, R3, R2, R1, R0, and SP points at R0; about 12 HCLK, 167 ns at 72 MHz, not including the ISR body. Failure path: both are written as preemption 1, and subpriorities 0 and 1 still do not nest; tail-chaining can happen on exit, and there is no second nested stack. With PRIMASK = 1, neither EXTI0 nor TIM2 gets in, and NMI still does. Sources: [PM0056 section 2.3.7](#source-pm0056-nvic) and [EXTICR and EXTI_PR in RM0008 Rev 21](#source-rm0008-exti).</sub>
</p>

**How to read this figure.** It has three panels; read them top to bottom. The top panel is the normal path: the TIM2 ISR is running, a falling edge arrives on PA0, EXTI0 has the smaller preemption number, hardware stacks 8 registers and enters the EXTI0 ISR, which clears EXTI_PR before TIM2 resumes. The middle panel is the failure path: both are written at the same preemption level, a different subpriority does not help, and EXTI0 can only wait as pending until TIM2 exits and then enters by tail-chaining. The bottom panel is the mask registers: with PRIMASK set neither gets in, and NMI still does.

<p align="center">
  <img src="../../assets/gif/nvic-preempt.gif" width="640" alt="While TIM2 runs, EXTI0 at a higher preemption interrupts it and then returns">
  <br><sub>▲ Animated figure for the web and the article channel. It plays only the successful preemption. Print uses the static figure above; the equal-preemption failure is not in this animation.</sub>
</p>

The opening `nvic-interrupt-flow.svg` draws the same process as six steps and marks how the vector address is worked out, `VTOR + 4 × (IRQn + 16)`: EXTI0's IRQn is 6, `4 × (6 + 16) = 88 = 0x58`, which matches the 0x0000_0058 in section 2.

## Timing and state

The table below splits the key figure into moments, and every row maps back to [PM0056 Rev 7 sections 2.3.6 and 2.3.7](#source-pm0056-nvic). The grouping is always GROUP_4, and times assume 72 MHz and 12 HCLK.

| Moment | Grouping | EXTI0 preemption | TIM2 preemption | What happens | Time |
| --- | --- | --- | --- | --- | --- |
| Normal: the TIM2 ISR is running | GROUP_4 | — | 2 | TIM2 has already interrupted the main loop | — |
| Normal: a falling edge on PA0 | GROUP_4 | 1 | 2 | 1 is smaller than 2, so EXTI0 interrupts TIM2; hardware pushes xPSR, PC, LR, R12, R3, R2, R1, R0 | About 12 HCLK, about 167 ns |
| Normal: EXTI0 is done | GROUP_4 | 1 | 2 | Clear EXTI_PR, unstack, back to the TIM2 ISR | 167 ns does not include the ISR body |
| Failure: both written as 1 | GROUP_4 | 1 | 1 | EXTI0 stays pending and enters by tail-chaining after TIM2 returns; no second nested stack | The manual gives no tail-chain cycle count |
| PRIMASK = 1 | GROUP_4 | 1 | 2 | Neither gets in; both wait in their pending bits; NMI still enters | — |

Arithmetic: `12 / 72e6 = 1.67e-7 s ≈ 167 ns`, the same figure as the Appendix D cell. Clearing EXTI_PR by writing 1 is in [RM0008 Rev 21 section 10.3.6](#source-rm0008-exti).

## Pitfalls and sources

| Symptom | Cause | What to do | Source | What the source supports |
| --- | --- | --- | --- | --- |
| A smaller subpriority still cannot interrupt the running ISR | Equal preemption does not nest, whatever the subpriority | Change the preemption number; do not rely on subpriority to nest | [PM0056 section 2.3.6](#source-pm0056-nvic) | Only the group priority decides preemption; subpriority only orders pending requests |
| The button interrupt cannot break into the timer interrupt | EXTI0's preemption number is not smaller than TIM2's | Give EXTI0 a smaller preemption number than TIM2 | [PM0056 section 2.3.6](#source-pm0056-nvic) | A smaller number is a higher priority |
| Expecting tail-chaining to let a lower priority into a higher one | Tail-chaining only saves one unstack and one stack | Judge who can interrupt whom by preemption level | [PM0056 section 2.3.7](#source-pm0056-nvic) | Tail-chaining happens when an ISR exits and does not change who may preempt |
| NMI still enters after `__disable_irq()` | PRIMASK does not cover NMI or HardFault | This is normal, not a broken PRIMASK | [PM0056 Table 7](#source-pm0056-nvic) | PRIMASK holds back only exceptions of configurable priority |
| Calling `HAL_Delay()` in an ISR, the program stops | SysTick's preemption number is not smaller than the current ISR's, so it cannot break in and the tick stops | Do not wait in an ISR; set a flag for the main loop | [PM0056 section 2.3.6](#source-pm0056-nvic) | An exception with an equal or larger preemption number cannot interrupt a running ISR |
| After one press the CPU sits in the EXTI0 ISR and the main loop stops | The ISR did not clear EXTI_PR, so the request is pending again after return | At the start of the ISR, write 1 to the line's bit in EXTI_PR | [RM0008 section 10.3.6](#source-rm0008-exti), [PM0056 section 4.3.9](#source-pm0056) | The first: EXTI_PR clears on writing 1; the second: a request not removed before return becomes pending again |
| PA0 already owns EXTI0, and PB0 set up as an interrupt never fires | One pin number shares one EXTI line | Put the second button on another pin number, such as PA1 | [RM0008 section 9.4.3](#source-rm0008-exti) | EXTI0's 4 bits select one port at a time |
| After moving the button to PB0 nothing fires, yet touching PA0 to GND does | The AFIO clock is off, so the EXTICR write did not take and it keeps the reset value 0000 (port A) | Enable the AFIO clock, then write EXTICR | [RM0008 section 10.2.5](#source-rm0008-exti) | Enable the AFIO clock before writing EXTICR; this holds only on F1 |

## Related resources

- Official manuals: **RM0008** chapter 10 (interrupts and events, EXTI), sections 9.4.3 through 9.4.6 (AFIO_EXTICR). Section 9.2.7 is GPIOx_LCKR, not EXTICR. Stacking is [PM0056 section 2.3.7](#source-pm0056-nvic)
- Previous: [03 GPIO and LEDs](03-gpio-and-led.md) | Next: [05 Timers and PWM](05-timer-pwm.md)
- Figures: [`assets/animations/nvic-interrupt-flow.svg`](../../assets/animations/nvic-interrupt-flow.svg), [`assets/animations/gpio-input-interrupt.svg`](../../assets/animations/gpio-input-interrupt.svg), [`assets/diagrams/interrupt-priority.svg`](../../assets/diagrams/interrupt-priority.svg)
- Disclaimer: every illustration in this repo is a vector drawing or a program-generated animation by the author, not a manufacturer's photograph.

# 17 Debugging and Performance
> 中文：[17 调试与性能优化](../17-调试与性能优化.md)

> Someone who can debug uses three tools together — an SWD breakpoint, an SWO print, and the HardFault registers — and finds in a few minutes a bug that would cost someone else a day. Someone who can optimize uses the DWT timer and DMA and squeezes the cycles dry.

<p align="center">
  <img src="../../assets/animations/debug-swo.svg" width="760" alt="SWD debug plus SWO/ITM print tracing">
  <br><sub>▲ Animation: SWD debug plus SWO/ITM print tracing (vector animation drawn by the author, not a live recording)</sub>
</p>

<!-- video:ch17 -->
<p align="center">
  <img src="../../assets/video/ch17-debug.gif" width="640" alt="Chapter 17 lecture slides">
  <br><sub>▲ Lecture slides for this chapter: a generated GIF (tools/gen_videos.py, reproducible, not a live recording). The narration lines up with the five frames, one to one.</sub>
</p>

**Narration (read along with the frames, about one minute)**

1. SWD debugs with two wires. Add one more, SWO, and printf can leave through the ITM. You do not have to spend a UART on it.
2. In a HardFault, look at PC on the stack first. The scene of the crash is near that instruction.
3. The DWT cycle counter can time a stretch of code. It is finer than toggling a GPIO.
4. Once optimization is on, a local variable may not live in memory. Look at the debug build and the release build separately.
5. Self-test: which pin does SWO use? In a fault, which register do you look at first?
<!-- /video:ch17 -->


## 📌 Learning goals

- [ ] Tell SWD and JTAG apart by their pins and their trade-offs, and understand why SWD is the mainstream choice.
- [ ] Use SWO / ITM for a `printf` trace that does not occupy a UART.
- [ ] Know how many hardware breakpoints and software breakpoints you get, and how they differ.
- [ ] Use the three-piece HardFault kit: `CFSR` / `HFSR` / `BFAR`, plus the stack unwind, plus `addr2line`.
- [ ] Measure a signal with a logic analyzer or a scope, and measure code time with the DWT.
- [ ] Remember the usual optimizations — `-O2` / `-Os`, DMA, cache — and the things to watch.

## 🧠 Core ideas

### 1. SWD vs JTAG

**Conclusion**: **SWD uses only 2 signal wires (SWDIO + SWCLK) plus GND.** It uses fewer pins than JTAG, and it is the debug interface of choice on Cortex-M. JTAG is mainly for a daisy chain of several devices, or for older tools.

| Item | SWD | JTAG |
| --- | --- | --- |
| Signal wires | SWCLK, SWDIO (2 wires) | TCK, TMS, TDI, TDO (4 wires, plus optional TRST) |
| Pins used | Few (PA13 / PA14) | Many (PB3 / PB4 / PA15, plus PA13 / PA14) |
| Speed | Fast (can reach 10+ MHz) | Fast |
| Several devices | No daisy chain | Supported |
| Typical tools | ST-Link, J-Link, DAPLink | J-Link, older JTAG probes |
| STM32 support | ✅ (recommended) | Supported, but rarely used |

> ⚠️ After reset, STM32 keeps **PA13 (SWDIO) and PA14 (SWCLK)** for the debug port by default. If you configure them as ordinary GPIO and turn debug off, you get "I programmed it and now I cannot connect." Leave `SWD` enabled, or keep a fallback through `HAL_DBGMCU`.

### 2. SWO / ITM / printf tracing

**Conclusion**: **SWO (Serial Wire Output)** lets the MCU send debug information out of the SWO pin through the **ITM**. It **does not occupy a UART**, and it does not block. It is the most elegant way to log.

| Mechanism | What it is |
| --- | --- |
| ITM (Instrumentation Trace Macrocell) | A trace unit inside the core. It can drive 32 channels (port 0 is the usual printf port) |
| SWO (Serial Wire Output) | Reuses the SWD physical connection and adds an ITM output (you need 3-wire SWD plus SWO) |
| `ITM_SendChar` | The low-level function you redirect `printf` to |
| What you need first | A debugger that supports SWO (ST-Link V2-1 or J-Link), and the SWO clock configured in the IDE |

```c
/* Redirect printf to the ITM; no UART needed */
int __io_putchar(int ch)
{
    ITM_SendChar(ch);
    return ch;
}
```

### 3. Breakpoint types and how many you get

**Conclusion**: The number of hardware breakpoints is **very small** (usually **6** on Cortex-M3 / M4, usually **8** on M7), and the count is set by the chip's FPB unit. Software breakpoints are unlimited, but they **rewrite Flash**.

| Type | How it works | How many | Limit |
| --- | --- | --- | --- |
| Hardware breakpoint | The FPB compares the address | 6 (M3 / M4) / 8 (M7) | The count is fixed. You cannot set one on a data address in RAM |
| Software breakpoint | Replace the instruction with `BKPT` | Unlimited | Needs writable memory (Flash has to be rewritten by the debugger). The breakpoint site is briefly modified |
| Data watchpoint | The DWT compares a data address | 2 to 4 | Halt when a variable is read or written |

> If a breakpoint will not set, or you are over the limit, delete the old ones. The debugger will usually fill in with software breakpoints on its own.

### 4. The three-piece HardFault kit

**Conclusion**: Once you are in HardFault, read **`CFSR` (configurable fault status), then `HFSR` (HardFault status), then `BFAR` (bus-fault address)**. Then **recover the PC at the time of the fault from the stack**. Finally use **`addr2line` or the `.map` file** to land on the source line.

| Register | Full name | Key bits | Meaning |
| --- | --- | --- | --- |
| `SCB->CFSR` | Configurable Fault Status | `MMARVALID` / `BFARVALID` | Whether the faulting address was recorded |
| `SCB->CFSR` | Same | `IMPRECISERR` and others | Precise or imprecise bus error |
| `SCB->HFSR` | HardFault Status | `FORCED` | Whether a fault was escalated and forced in here |
| `SCB->BFAR` | BusFault Address | The address | The address of the illegal access (if `BFARVALID=1`) |
| `SCB->MMFAR` | MemManage Address | The address | The address of an MPU violation |

**Unwinding the stack**: on entry to the exception, the core pushes `R0–R3, R12, LR, PC, xPSR`. PC is the address of the faulting instruction.

```c
/* Recover the faulting PC from MSP or PSP */
void HardFault_Handler(void)
{
    __asm volatile (
        "TST LR, #4        \n"   /* which stack: MSP or PSP */
        "ITE EQ            \n"
        "MRSEQ R0, MSP     \n"
        "MRSNE R0, PSP     \n"
        "B hard_fault_handler_c \n"
    );
}
```

```c
void hard_fault_handler_c(uint32_t *stack)
{
    volatile uint32_t r0  = stack[0];
    volatile uint32_t r1  = stack[1];
    volatile uint32_t r2  = stack[2];
    volatile uint32_t r3  = stack[3];
    volatile uint32_t r12 = stack[4];
    volatile uint32_t lr  = stack[5];
    volatile uint32_t pc  = stack[6];    /* ← address of the faulting instruction */
    volatile uint32_t psr = stack[7];
    volatile uint32_t cfsr = SCB->CFSR;
    volatile uint32_t hfsr = SCB->HFSR;
    volatile uint32_t bfar = SCB->BFAR;

    (void)r0;(void)r1;(void)r2;(void)r3;(void)r12;(void)lr;(void)psr;
    (void)cfsr;(void)hfsr;(void)bfar;
    for (;;) { }                         /* breakpoint here and inspect the variables above */
}
```

**Turn the PC into a source line with addr2line** (GCC toolchain):

```bash
arm-none-eabi-addr2line -e build/app.elf -f -C 0x08001a3c
# output: function name + file:line
```

> With Keil, look up the faulting PC in the symbol ranges of the `.map` file, or use the IDE's Call Stack window.

### 5. Logic analyzer / oscilloscope

| Tool | What it shows | Typical use |
| --- | --- | --- |
| Logic analyzer (8 channels, 24 MHz and up) | Digital timing | Capture I2C / SPI / UART / CAN timing and decode the protocol |
| Oscilloscope | Analog waveform | PWM rising edge, supply ripple, signal integrity |
| Mixed-signal scope (MSO) | Digital plus analog | Timing and the analog waveform together |
| Current probe / power profiler | Current waveform | Checking low power (see [Chapter 16](16-low-power.md)) |

> A logic analyzer is good at "is the protocol right." A scope is good at "is the signal healthy." An intermittent bus error needs both.

### 6. Ways to speed the code up

**Conclusion**: **Measure first**, then optimize (time it with the DWT). The usual moves, in order of payoff: **hand the copies to DMA, then raise the compiler optimization, then cut floating point and division, then cache and prefetch, then assembly.**

| Move | What to do | Watch out |
| --- | --- | --- |
| Compiler optimization | `-O2` (speed) / `-Os` (size) | `-O0` is easy to single-step and slow. Use `volatile` so a value is not optimized away |
| DMA | Hand UART / ADC / SPI data movement to DMA | See [Chapter 10](10-dma.md). Watch cache coherency |
| Bit-band / bit operations | Replace division and modulo with bit operations | Division is more than ten times slower than a shift |
| Fixed point instead of floating point | Use Q-format fixed point | Especially visible on an M3 with no FPU |
| FPU | Turn on hardware floating point on M4F / M7 | Compile with `-mfpu=fpv4-sp-d16 -mfloat-abi=hard` |
| Cache / ART | The F4 ART accelerator, and I-Cache / D-Cache on H7 | H7 DMA has to maintain the cache |
| Inline / macros | `static inline` on a hot function | Too much inlining grows the image |
| Lookup tables | A LUT instead of computing it live | You spend Flash to buy speed |

**DWT timing (accurate to a CPU cycle)**:

```c
/* Time a stretch of code with the DWT CYCCNT counter (F1 and F4 both support it) */
static void DWT_Init(void)
{
    CoreDebug->DEMCR |= CoreDebug_DEMCR_TRCENA_Msk;  /* enable trace */
    DWT->CYCCNT = 0;
    DWT->CTRL  |= DWT_CTRL_CYCCNTENA_Msk;            /* enable the cycle counter */
}

static uint32_t DWT_Cycles(void) { return DWT->CYCCNT; }

void Measure(void)
{
    DWT_Init();
    uint32_t t0 = DWT_Cycles();
    /* code under test */
    for (volatile int i = 0; i < 1000; i++) { }
    uint32_t dt = DWT_Cycles() - t0;                 /* cycle count */
    float us = (float)dt / (SystemCoreClock / 1000000.0f);
    (void)us;                                        /* convert to microseconds */
}
```

### 7. Common HardFault causes

| What you see / which fault bit | Usual cause | Fix |
| --- | --- | --- |
| `IMPRECISERR` plus `BFARVALID` | Touching a peripheral whose clock is off, or a wild pointer | Call `__HAL_RCC_xxx_CLK_ENABLE` first, and read `BFAR` |
| `PRECISERR` | An illegal memory access (a null pointer, or past the end of an array) | Check the pointer and the array bounds |
| `UNDEFINSTR` | A jump to an illegal address (a bad function pointer, or a smashed stack) | Check function pointers and the stack size |
| `INVSTATE` | The jump target is not a Thumb instruction (bit0 = 0) | Bit 0 of the entry address must be 1 |
| `INVPC` | LR is illegal on exception return | The interrupt corrupted LR, or the stack is scrambled |
| `FORCED` and `CFSR=0` | An escalated fault, or a missing vector | Check the vector table `SCB->VTOR` and the linker script |
| Divide by zero (silent unless DIV_0_TRP is on) | Divide-by-zero trapping is not enabled | `SCB->CCR \|= SCB_CCR_DIV_0_TRP_Msk` |
| Stack overflow | A large local array, or recursion that is too deep | Enlarge the stack, and turn on stack-overflow detection |

## 🛠️ Hardware and wiring

| Board | Interface | Pin | Notes |
| --- | --- | --- | --- |
| BluePill (F103) | SWD | PA13 = SWDIO, PA14 = SWCLK, GND, 3V3 | Four wires are enough to program and debug |
| BluePill | SWO | PB3 (optional; needs `SWJ_CFG` in `AFIO_MAPR`) | Only J-Link and ST-Link V2-1 support it |
| Nucleo-F411RE | SWD plus SWO | On-board ST-Link, SB jumpers | SWO works directly |
| J-Link | SWD | Same as above | Supports SWO / ITM and RTT |
| Any | Logic analyzer | Clip onto SCL / SDA / MOSI and similar | Capture timing and decode |
| Any | Oscilloscope | Probe on the signal under test | Look at waveform quality |

> ⚠️ SWD needs only four wires: **SWCLK, SWDIO, GND, and 3V3**. **GND must be common**, or it will not connect. If the board was configured with debug turned off, recover it by holding reset at the moment of power-up and then connecting, or by pulling BOOT0 high and booting from system memory.

## 💻 Code

**① Redirect printf to SWO / ITM (ready to use)**

```c
#include "stm32f1xx_hal.h"
#include <stdio.h>

/* Redirect the low-level character output to ITM port 0 (SWO) */
int __io_putchar(int ch)
{
    ITM_SendChar((uint32_t)ch);
    return ch;
}

void Log_Init(void)
{
    /* No extra init. Enable SWD in CubeMX.
       In the IDE, set the SWO clock equal to the core clock, and you will see printf */
}

void Log_Demo(void)
{
    printf("sysclk = %lu Hz\r\n", (unsigned long)SystemCoreClock);
}
```

**② Keep the SWD pins (so a bad remap does not lock you out)**

```c
/* If you must reuse PA13/PA14, at least keep SWD; otherwise you may not be able to connect after programming */
__HAL_RCC_AFIO_CLK_ENABLE();
__HAL_AFIO_REMAP_SWJ_NOJTAG();   /* turn off JTAG only and keep SWD (PA13/PA14 still debug) */
```

**③ Trap divide-by-zero and illegal accesses (turn a hidden bug into a HardFault)**

```c
void Fault_Enable(void)
{
    SCB->CCR |= SCB_CCR_DIV_0_TRP_Msk;   /* divide-by-zero raises UsageFault */
    SCB->SHCSR |= SCB_SHCSR_USGFAULTENA_Msk
               |  SCB_SHCSR_BUSFAULTENA_Msk
               |  SCB_SHCSR_MEMFAULTENA_Msk;  /* enable the three fault types separately */
}
```

**④ HardFault handler (pair it with the stack unwind in section 4, and print the registers directly)**

```c
void hard_fault_handler_c(uint32_t *stack)
{
    printf("HardFault! PC=0x%08lX LR=0x%08lX\r\n",
           (unsigned long)stack[6], (unsigned long)stack[5]);
    printf("CFSR=0x%08lX HFSR=0x%08lX BFAR=0x%08lX\r\n",
           (unsigned long)SCB->CFSR,
           (unsigned long)SCB->HFSR,
           (unsigned long)SCB->BFAR);
    for (;;) { }
}
```

**⑤ DWT timing (compare memcpy with DMA, and similar)**

```c
static inline void DWT_DelayInit(void)
{
    CoreDebug->DEMCR |= CoreDebug_DEMCR_TRCENA_Msk;
    DWT->CYCCNT = 0;
    DWT->CTRL  |= DWT_CTRL_CYCCNTENA_Msk;
}

/* Usage:
   DWT_DelayInit();
   uint32_t t0 = DWT->CYCCNT;  ...code under test...  uint32_t dt = DWT->CYCCNT - t0;
   time (us) = dt / (SystemCoreClock / 1000000)  */
```

> Compiler optimization: use `-O2` (speed) or `-Os` (size) for Release, and `-Og` (you can still single-step) for debug. **After optimization you may not be able to see a variable.** Use `volatile`, or drop a local region to `-O0`, while you hunt the bug.

## ⚠️ Pitfalls and troubleshooting

| What you see | Cause | Fix |
| --- | --- | --- |
| After programming, the board will not connect | PA13 / PA14 were configured as GPIO and debug was turned off | Hold reset at the moment of power-up, then connect. Keep SWD |
| SWO produces nothing | The SWO clock or pin was not configured | In the IDE, set the SWO frequency equal to the core clock, and connect the SWO wire |
| printf hangs | Semihosting `_sys_write` is blocking | Redirect to ITM or UART. Do not use semihosting |
| A breakpoint will not set | Hardware breakpoints are used up, or it is in a read-only region | Delete old breakpoints, and use a software breakpoint |
| Single-step jumps around | `-O2` reordered the code | Debug at `-O0` or `-Og` |
| HardFault, but CFSR is 0 | The individual faults were not enabled, or it is FORCED | Enable the bits in `SHCSR`, and check the vector table |
| The PC does not land on source | There is no `.elf` or `.map` | Run `addr2line` on the elf from that same build |
| The logic is wrong after optimization | A shared variable is missing `volatile` | Add `volatile` to variables shared by an interrupt and the main loop |
| The measured time is 0 | The DWT was not enabled, or it was not initialized after reset | Call `DWT_DelayInit()` |
| The logic analyzer captures nothing | The sample rate is too low, or ground is not shared | Raise the sample rate, and share ground |

## 🧪 Hands-on labs

1. **Print over SWO**: redirect `printf` to the ITM and watch the output in the IDE's SWV / ITM window. Expected: you see the log with no UART connected.
2. **Cause a HardFault and find it**: write `*(volatile uint32_t*)0xDEADBEEF = 1;`. In the HardFault handler, print `CFSR`, `BFAR`, and `PC`, and locate the line with `addr2line`. Expected: it points back at that line.
3. **Compare times with the DWT**: time a software `memcpy` and a DMA copy of the same amount of data (see [Chapter 10](10-dma.md)). Expected: the CPU time of the DMA version is close to 0.
4. **(Further) Decode I2C with a logic analyzer**: capture one OLED write transaction ([Chapter 07](07-i2c.md)) and restore the address and the data with a decoder. Expected: you can see address 0x3C and the ACK.
5. **(Further) Compare optimization levels**: time the same floating-point-heavy code at `-O0` and at `-O2` with the DWT. Expected: `-O2` is several times faster.

## 🔗 Related resources

- The Debug support (DBGMCU) chapter of RM0008 and RM0090 (debug-port configuration, and debugging in low power).
- *The Definitive Guide to ARM Cortex-M3 and Cortex-M4 Processors*: fault exceptions, `CFSR` / `HFSR` / `BFAR`, and the stack frame.
- ARMv7-M Architecture Reference Manual (ARM DDI 0403): the exception model, FPB, and DWT.
- Tool docs: SWO / ITM setup for ST-Link and J-Link, and `arm-none-eabi-addr2line`.
- Related chapters: [Chapter 10](10-dma.md) DMA, [Chapter 16](16-low-power.md) low power (measuring power), and [Chapter 04](04-interrupts-nvic.md) interrupts and NVIC.
- Figure: `../../assets/animations/debug-swo.svg` (vector drawing by the author).

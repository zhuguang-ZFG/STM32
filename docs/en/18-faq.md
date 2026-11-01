# 18 FAQ

> 中文：[18 常见问题 FAQ](../18-常见问题FAQ.md)

> The traps beginners hit most often, sorted into build and link, download and debug, peripherals, hardware, and RTOS and toolchain. Each entry is **symptom / cause / fix**. When something breaks, search for the keyword here first.

<p align="center">
  <img src="../../assets/animations/toolchain-flow.svg" width="760" alt="Toolchain data flow: compile, link, flash, run">
  <br><sub>▲ Animation: the data flow from compile to link to flash to run (author-drawn vector, not a photograph)</sub>
</p>

<!-- video:ch18 -->
<p align="center">
  <video width="640" controls poster="../../assets/video/ch18-faq.png">
    <source src="../../assets/video/ch18-faq.mp4" type="video/mp4">
  </video>
  <br><sub>▲ Chapter video with Chinese voice-over (2.5 min). <a href="../../assets/video/ch18-faq.mp4">MP4</a> · <a href="../../assets/video/ch18-faq.srt">subtitles</a></sub>
</p>

<details>
<summary>Narration script (Chinese, same text as the subtitles)</summary>

1. 排错不要从改代码开始。先让现象稳定复现，再退到只点灯或只回环的最小工程。最小工程是好的，问题就在你后来加的那一块里。
2. 这一章的五步是：复现，最小化，二分，看证据，对照手册。前两步能解决大多数问题。一上来就二分一大坨新代码，你会把时间花在来回编译上。
3. 编译报一长串时，先看第一处真正的错误。找不到头文件，多半是包含路径，不是语法突然坏了。链接报未定义的符号，再去看你有没有把对应的源文件加进工程。
4. 这一帧是仓库画的分层。现象在引脚上，就同时怀疑引脚模式和接线。现象在 HAL 返回值里，就打印那个状态码，再对照它碰过的寄存器。不要每一层同时盲改。
5. 下载失败时，先看供电、地、SWD 两根线和复位。芯片认不出，就不要查优化等级。BOOT0 被拉高时，它跑的是系统存储器，你的程序看起来像没烧进去。
6. 外设完全没反应，老三样：时钟开了没有，引脚复用对不对，该清的标志清了没有。这三样过完，再去看波特率、过滤器和采样时间。顺序反了，会在细节里耗掉一个晚上。
7. 三条铁律：能测就别猜，先共地再看信号，一次只改一处。猜测式修改会让两个错误叠在一起，最后谁也不认领。
8. 这一章建议你故意制造一次错误，比如删掉一个头文件路径，看编译器怎么说，再改回来。见过真实报错的人，下次不会从最后一行开始慌。
9. 口诀：先复现，再缩到最小。前两步走完还不知道范围，再去二分和看证据。能测就别猜。
10. 合上书，三问。排错五步的前两步是什么？调试器认不出芯片时，先查代码还是先查线和 BOOT？为什么一次只改一处？

</details>
<!-- /video:ch18 -->

## Learning goals

Before this chapter: read chapter 01, so you can build, download, and connect a debugger. When an entry mentions a peripheral, go back to that peripheral's chapter for the details. If hex numbers or register bits are unfamiliar, read "Zero-background primer" in chapter 00 first.

- [ ] Debug in five steps (reproduce, minimize, bisect, look at evidence, check the manual) and say what each step must produce
- [ ] Pick the right family of entries (C, D, P, H, R) from a symptom
- [ ] When the probe cannot see the chip, check power, shared ground, pins 34 and 37, NRST, and BOOT0 in that order, before touching code
- [ ] Say where each of the three BOOT0/BOOT1 combinations starts, and why moving the jumper needs a reset
- [ ] When a peripheral does nothing, check three things first: is its clock on, is the pin's alternate function right, are the flags cleared
- [ ] Read the compiler's first error and tell "header not found" apart from "undefined symbol"
- [ ] Print SYSCLK with the minimal project and tell whether HSE started

## A method for debugging (do these 5 steps first)

**In one sentence: when something breaks, first make the symptom repeat reliably, then fall back to a minimal project that only blinks and echoes, and only then bisect and gather evidence, changing one thing at a time.**

### An analogy first

Debugging is like seeing a doctor. The doctor first asks when it hurts and how: that is reproducing. Then comes temperature and blood pressure, to rule out the big problems first: that is minimizing. Then one region of the body at a time, to narrow it down: that is bisecting. Then the lab report rather than a hunch: that is evidence. Last, the doctor checks the diagnosis against medical references: that is the manual. A good doctor never prescribes five drugs at once, because if the patient gets better nobody knows which one worked. Changing one thing at a time in debugging follows the same logic.

The analogy stops here. Every human body is different, but a chip is a deterministic circuit: the same wiring, the same program, and the same inputs always give the same result. A failure that happens "now and then" is usually a bad contact, an unstable supply, or an uninitialized variable, not the chip having a bad day.

### 1. The five steps, in order

Work down the table from the top. The first two steps are the cheapest and the easiest to skip, which is why they come first.

| Step | What you do | Why |
| --- | --- | --- |
| 1 | **Reproduce**: confirm that the symptom appears reliably, and write down what triggers it | If you cannot reproduce it, suspect hardware and contacts first |
| 2 | **Minimize**: go back to the minimal project that only blinks an LED and only echoes bytes | Tell a board or clock problem apart from a problem in code you added later |
| 3 | **Bisect**: comment out half the code, or enable one peripheral at a time | Find the block that brought the problem in, quickly |
| 4 | **Look at evidence**: a UART log, a logic-analyzer trace, HAL return values, `CFSR`/`BFAR` | Let data replace guesses |
| 5 | **Check the manual**: registers and timing in the reference manual (RM) and the datasheet (DS) | Confirm that what you "know is right" really is |

A few words first. The **minimal project** is a program with nothing left but the clock, one LED, and one UART. If it runs and prints a SYSCLK of 72000000, the chip, the supply, the download, and the clock are all fine. **Bisecting** means removing half of the suspects each time and checking whether the problem is still there; each step rules out half, so 4096 lines of code shrink to 1 line in 12 steps. **Evidence** means something you can see again: a printed line, a trace, a register value.

> [!TIP]
> Three house rules: **if you can measure it, do not guess**, **share ground before you study the signal**, and **change one thing at a time**. Change two things at once and two errors pile up, and in the end nobody can say which change did what.

### 2. The minimal project: blink only, echo only

The program below is the project that step 2 falls back to. It does three things: at power-up it prints the SYSCLK and PCLK2 frequencies once, the onboard LED on PC13 keeps blinking, and the UART sends back whatever it receives. When HSE does not start, it does not stop in an error handler; it stays on HSI, keeps running, and prints that fact.

```c
/* main.c: minimal check project, prints the clock + blinks PC13 + USART1 echo (STM32F103C8T6)
 * SysTick_Handler lives in the CubeMX-generated stm32f1xx_it.c. It calls HAL_IncTick(),
 * and every HAL timeout is timed by it. */
#include "stm32f1xx_hal.h"
#include <stdio.h>
#include <string.h>

#define LED_PORT    GPIOC
#define LED_PIN     GPIO_PIN_13         /* onboard LED, lit when low */
#define RX_WAIT_MS  500U                /* wait at most 500 ms for one byte */

UART_HandleTypeDef huart1;

static HAL_StatusTypeDef SystemClock_Config(void);
static void bsp_init(void);
static void error_handler(void);

int main(void)
{
    char              msg[80];
    uint8_t           ch;
    HAL_StatusTypeDef clock_ok;

    HAL_Init();
    clock_ok = SystemClock_Config();    /* on failure, stays on the 8 MHz HSI from reset */
    bsp_init();                         /* HAL computes BRR from the current PCLK2 */

    (void)snprintf(msg, sizeof(msg), "SYSCLK=%lu Hz PCLK2=%lu Hz HSE %s\r\n",
                   (unsigned long)HAL_RCC_GetSysClockFreq(),
                   (unsigned long)HAL_RCC_GetPCLK2Freq(),
                   (clock_ok == HAL_OK) ? "ok" : "FAILED");
    (void)HAL_UART_Transmit(&huart1, (uint8_t *)msg, (uint16_t)strlen(msg), 100U);

    for (;;)
    {
        HAL_GPIO_TogglePin(LED_PORT, LED_PIN);                       /* blinking: the program runs */
        if (HAL_UART_Receive(&huart1, &ch, 1U, RX_WAIT_MS) == HAL_OK)
        {
            (void)HAL_UART_Transmit(&huart1, &ch, 1U, 10U);          /* send back what arrived */
        }
    }
}

static HAL_StatusTypeDef SystemClock_Config(void)   /* success: HSE 8 MHz x 9 = 72 MHz */
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
        return HAL_ERROR;               /* HSE or PLL did not start: do not switch clocks */
    }

    clk.ClockType      = RCC_CLOCKTYPE_HCLK | RCC_CLOCKTYPE_SYSCLK |
                         RCC_CLOCKTYPE_PCLK1 | RCC_CLOCKTYPE_PCLK2;
    clk.SYSCLKSource   = RCC_SYSCLKSOURCE_PLLCLK;
    clk.AHBCLKDivider  = RCC_SYSCLK_DIV1;
    clk.APB1CLKDivider = RCC_HCLK_DIV2;
    clk.APB2CLKDivider = RCC_HCLK_DIV1;
    return HAL_RCC_ClockConfig(&clk, FLASH_LATENCY_2);
}

static void bsp_init(void)
{
    GPIO_InitTypeDef io = {0};

    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_GPIOC_CLK_ENABLE();
    __HAL_RCC_USART1_CLK_ENABLE();

    io.Pin   = LED_PIN;
    io.Mode  = GPIO_MODE_OUTPUT_PP;
    io.Pull  = GPIO_NOPULL;
    io.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(LED_PORT, &io);

    io.Pin   = GPIO_PIN_9;              /* USART1_TX */
    io.Mode  = GPIO_MODE_AF_PP;
    io.Speed = GPIO_SPEED_FREQ_HIGH;
    HAL_GPIO_Init(GPIOA, &io);

    io.Pin  = GPIO_PIN_10;              /* USART1_RX */
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

static void error_handler(void)
{
    __disable_irq();
    for (;;) { }
}
```

Piece by piece:

- `SystemClock_Config()` simply returns on failure and does not enter the error handler. After reset SYSCLK is HSI anyway (RM0008 Rev 21 section 7.2.6), so the program carries on at 8 MHz, and the minimal project still blinks and prints.
- `bsp_init()` comes after the clock setup. `HAL_UART_Init()` recomputes the baud rate register BRR from the PCLK2 of that moment every time, so even at 8 MHz the 115200 output is correct, and the first line reads `SYSCLK=8000000 Hz ... HSE FAILED`.
- A blinking LED means the program runs and SysTick ticks: the 500 ms timeout of `HAL_UART_Receive()` is timed by SysTick, and without SysTick the LED toggles once and then freezes. If the LED does not blink and the UART prints nothing, the problem is earlier: power, download, or boot mode. Go back to the D and H entries.
- The echo confirms the wiring: you type a character and it comes back. With no typing, the LED blinks once per second (`RX_WAIT_MS` is an example setting).

Without HAL, reading registers directly also confirms the clock and the baud rate. If the numbers HAL prints disagree with these two registers, some step did not run the way you thought:

```c
uint32_t sws = RCC->CFGR & RCC_CFGR_SWS;   /* 0x0 = HSI, 0x4 = HSE, 0x8 = PLL (RM0008 Rev 21 section 7.3.2, bits 3:2) */
uint32_t brr = USART1->BRR;                /* HAL writes 0x271 at 72 MHz and 115200; 0x45 at 8 MHz */
```

### 3. How to use the 38 entries below

The 38 entries fall into five families, and the prefix of each number names the family: `C` is build and link, `D` is download and debug, `P` is peripherals, `H` is hardware, and `R` is RTOS and the toolchain. Every entry is written as symptom, cause, fix. The cause line often lists several possibilities; check the one that is easiest to verify first.

With a problem in hand, pick the family by its symptom: an error on the PC belongs to C; a board that will not connect, or a program that will not download, belongs to D; a program that runs while one peripheral does nothing belongs to P; smoke, heat, a dark LED, or repeated resets belong to H; anything that only appears after you added FreeRTOS or switched tools belongs to R. Once you find the entry, still verify it with the five steps above. Do not copy the fix line straight into your code.

## 1. Build and link

These problems all happen on the PC; the board has not taken part yet. The compiler often reports dozens of lines at once. Read the first real error; most of the rest follow from it.

**C1 Cannot find `stm32f1xx_hal.h`**
- **Symptom**: the build reports `fatal error: stm32f1xx_hal.h: No such file or directory`.
- **Cause**: the include search path does not contain the HAL `Inc` directory. The syntax did not suddenly break.
- **Fix**: add `Drivers/STM32F1xx_HAL_Driver/Inc` and `Core/Inc` to the include path in the project settings or in `CMakeLists.txt`.

**C2 The link reports `undefined reference to HAL_GPIO_Init`**
- **Symptom**: compilation succeeds, then the link reports an undefined symbol.
- **Cause**: compiling needs only the declaration; linking needs the definition. The source file `stm32f1xx_hal_gpio.c` was not compiled, or `HAL_GPIO_MODULE_ENABLED` is not turned on in `stm32f1xx_hal_conf.h`.
- **Fix**: add the HAL sources you use to the project and turn on the module's macro. In a CubeMX project, enable the peripheral on its page and CubeMX generates both for you.

**C3 `region FLASH overflowed by N bytes`**
- **Symptom**: the link reports that the ROM region (Flash) is too small.
- **Cause**: code and constants exceed the chip's Flash. An F103C8 has only 64 KB (DS5319 Rev 20 section 7, ordering information).
- **Fix**: turn on `-Os`, drop floating-point support in `printf`, and remove unused libraries. If it still does not fit, move to a part with more Flash.

**C4 `region RAM overflowed`**
- **Symptom**: the link reports that RAM is short.
- **Cause**: a global array is too large, or the linker script reserves too much for the stack and heap. An F103C8 has only 20 KB of SRAM (DS5319 Rev 20 Table 2).
- **Fix**: shrink the global buffers, and reduce `_Min_Heap_Size` and `_Min_Stack_Size` in the linker script. Those two numbers are minimum reservations that the linker checks.

**C5 Redefinition: `multiple definition of 'xxx'`**
- **Symptom**: the link reports a symbol defined more than once.
- **Cause**: a variable was defined directly in a header without `static` or `extern`, and several `.c` files included it.
- **Fix**: the header holds only an `extern` declaration; the definition lives in exactly one `.c` file.

**C6 `printf` prints garbage, or prints nothing**
- **Symptom**: the serial port receives garbage, or nothing at all.
- **Cause**: nothing at all usually means `printf` was never redirected to the UART (`_write` or `__io_putchar` is missing), or the string has no `\n` at the end and the C library is still holding it in its buffer. Garbage is usually not a `printf` problem at all but a wrong baud rate or clock; see P3.
- **Fix**: implement `__io_putchar` and call `HAL_UART_Transmit` inside it. End each line with `\r\n`, or call `setvbuf(stdout, NULL, _IONBF, 0)` at start-up to turn the buffering off. With newlib-nano, add `-u _printf_float` to the link options if you need to print floating point.

**C7 The build reports `arm-none-eabi-gcc: not found`**
- **Symptom**: a command-line build fails.
- **Cause**: the toolchain is not installed, or it is not on the `PATH` environment variable.
- **Fix**: install the Arm GNU Toolchain (formerly the GNU Arm Embedded Toolchain) and add its `bin` directory to `PATH`, or use the toolchain that ships with CubeIDE.

**C8 The generated bin/hex is much larger than you expected**
- **Symptom**: the firmware file is far bigger than it should be.
- **Cause**: first check which file you are looking at. Debug information lives only in the `.elf` and never goes into the `.bin` or `.hex`. A `.hex` is text: each byte becomes two characters plus a record header, so it is normally more than twice the size of the `.bin`. A `.bin` that is absurdly large (hundreds of MB) usually means a section was placed at a RAM address, and the `.bin` filled the whole gap between Flash and RAM. Only when the code itself is big are unused libraries and full `printf` the cause.
- **Fix**: run `arm-none-eabi-size` and read its three numbers, `text`, `data`, and `bss`. Turn on `-Os` and `-ffunction-sections -fdata-sections`, and pass `--gc-sections` to the linker so it drops unused code.

## 2. Download and debug

These problems sit between the PC and the chip. Confirm power and wires before you suspect software: while the probe cannot even see the chip, the optimization level is beside the point.

**D1 `No target connected` / the probe cannot see the target**
- **Symptom**: the programmer reports that it cannot find the target.
- **Cause**: the board has no power; ground is not shared; the SWD lines are wired wrong (SWDIO is on PA13, SWCLK on PA14); the program turned the debug port off.
- **Fix**: check SWDIO, SWCLK, GND, and 3.3 V one wire at a time. Power the board on its own and try again. Hold reset while connecting (the tools call it Connect under reset).

**D2 After flashing, the board acts "bricked" and never connects again**
- **Symptom**: once the program is downloaded, SWD never connects again.
- **Cause**: the program configured PA13 and PA14 as plain GPIO, or turned SWD off through AFIO. The chip runs that code right after every reset, before the debugger can take over.
- **Fix**: either of two rescues works. One: hold NRST, choose Connect under reset in the tool, release NRST once connected, and erase the whole chip. Two: pull BOOT0 high and power up; the chip starts from system memory, your program never runs, so SWD connects; erase the whole chip in STM32CubeProgrammer, then put BOOT0 back to 0.

**D3 `Flash Download failed - Target DLL has been cancelled`**
- **Symptom**: the download fails partway through (this is Keil's message).
- **Cause**: the Flash algorithm does not match the part, or readout protection is on.
- **Fix**: check that the Flash algorithm chosen in the project matches the part number. To clear readout protection, set RDP back to unprotected in the option bytes. When you do, the chip first erases the whole main Flash, so the program is gone (PM0075 Rev 2 section 2.4.1).

**D4 Breakpoints do nothing while debugging**
- **Symptom**: a breakpoint is skipped, or the tool says you have too many.
- **Cause**: when ST-Link debugs code in Flash, only hardware breakpoints work, and this M3 has only 6 (RM0008 Rev 21 section 31.12, the 6 instruction comparators of the FPB). A software breakpoint rewrites the instruction into a breakpoint instruction, and instructions in Flash cannot be rewritten that casually. The other cause is that the line was optimized away.
- **Fix**: delete breakpoints until 6 or fewer remain. For a debug build, set optimization to `-O0` or `-Og`.

**D5 Single-step "jumps around"**
- **Symptom**: the line number hops while you single-step.
- **Cause**: compiler optimization reordered the instructions or inlined the function.
- **Fix**: set the debug configuration to `-O0` or `-Og`.

**D6 ST-Link says its firmware is too old**
- **Symptom**: connecting prompts you to upgrade the ST-Link firmware.
- **Cause**: the old firmware does not work with the newer tools.
- **Fix**: upgrade with the ST-Link upgrade function in STM32CubeProgrammer or CubeIDE. Be careful with a clone ST-Link: after an upgrade it may stop working.

**D7 The program stops in `HardFault_Handler` as soon as you start debugging**
- **Symptom**: a debug session lands in HardFault right away.
- **Cause**: the linker script or startup file was written for another part, so the initial stack pointer lies beyond the 20 KB of SRAM, or the vector table is wrong; the stack is too small; the code touched an address that does not exist.
- **Fix**: read `CFSR` first. `BFAR` holds this fault's address only when bit 15 of `CFSR` (BFARVALID) is 1 (see chapter 17). Then check the RAM size in the linker script and the part the startup file was written for.

## 3. Peripherals

Here the program runs, but one peripheral does nothing. Check the usual three first: is the clock on, is the pin's alternate function right, are the flags that need clearing cleared. Only after those three pass, look at details such as the baud rate, filters, and sample time.

**P1 A GPIO write does nothing**
- **Symptom**: after `HAL_GPIO_WritePin` the pin does not change.
- **Cause**: the clock of that GPIO port was never enabled. Without a clock, the registers do not take writes.
- **Fix**: call `__HAL_RCC_GPIOx_CLK_ENABLE()` (x is the port letter) before initializing the pin.

**P2 One key press enters the interrupt many times**
- **Symptom**: one press prints several lines.
- **Cause**: a mechanical contact bounces for a few milliseconds as it closes and produces several edges, and nothing debounced it.
- **Fix**: debounce in software: record the time in the interrupt, and drop any edge that comes less than 10–20 ms (rule of thumb) after the previous one. Or add an RC debounce on the key.

**P3 Serial garbage**
- **Symptom**: everything you receive is garbage.
- **Cause**: the two ends use different baud rates; ground is not shared; the chip's clock is not the frequency you think. The last one hides best: when HSE does not start, SYSCLK is the 8 MHz HSI, and USART1's `0x271`, computed for 72 MHz, gives 12800 on that clock, not 115200. HAL recomputes BRR from the clock at initialization, so this mostly shows up in code that writes a fixed BRR value, or in programs that the clock security system (CSS) switches back to HSI while running. A `HSE_VALUE` that does not match the board's crystal also makes HAL compute the wrong value.
- **Fix**: use the same baud rate on both ends, share ground, and print SYSCLK with the minimal project above to confirm it is 72000000.

**P4 I2C stalls inside `HAL_I2C_Master_Transmit`**
- **Symptom**: the program hangs, or the call returns a timeout.
- **Cause**: the pull-up resistors are missing; the address is wrong; a slave holds the bus stuck low.
- **Fix**: put one pull-up from SCL and one from SDA to 3.3 V; 4.7 kΩ is a common value (rule of thumb; DS5319 Rev 20 Table 42 also uses it as the condition for its SCL frequencies). Check the 7-bit address; HAL wants it shifted left by one. If the bus is stuck, drive SCL as a plain pin and clock it 9 times by hand so the slave releases SDA (NXP UM10204 Rev 6 section 3.1.16).

**P5 An SPI Flash read comes back all FF**
- **Symptom**: the data you read is all 0xFF.
- **Cause**: CS was never pulled low; the SPI mode set by CPOL and CPHA is wrong; MISO is not connected.
- **Fix**: check the mode: the W25Q family supports mode 0 and mode 3 (Winbond W25Q datasheet). Check the chip-select timing and the wiring. Read the JEDEC ID first, and read data only once the ID is right.

**P6 ADC readings jump around**
- **Symptom**: the samples are unstable.
- **Cause**: the reference voltage is noisy: the LQFP48 package has no separate VREF+ pin, so the reference is VDDA (DS5319 Rev 20 Table 47 note 3). Or the sample time is too short, or the source impedance is too high.
- **Fix**: decouple VDDA with 10 nF + 1 µF as in DS5319 Rev 20 Figure 14, lengthen the sample time, and add a small capacitor on the input as a buffer.

**P7 Timer PWM has no output**
- **Symptom**: the oscilloscope shows no waveform.
- **Cause**: PWM was never started with `HAL_TIM_PWM_Start`; the pin's alternate function is not set; the channel is wrong. With the advanced timer TIM1, the MOE bit (bit 15) of `TIMx_BDTR` must also be set, or the outputs stay off.
- **Fix**: call `HAL_TIM_PWM_Start` (for TIM1 it sets MOE as well), and check the alternate-function pin and the channel. Register-level code has to set MOE itself.

**P8 DMA moves data only once**
- **Symptom**: DMA transfers once, then stops.
- **Cause**: the channel is in normal mode, and you expected circular mode.
- **Fix**: switch it to `DMA_CIRCULAR`, or start the transfer again in the transfer-complete callback.

**P9 The RTC resets at power-up, or does not advance**
- **Symptom**: the time is gone after power is removed, or the RTC never advances.
- **Cause**: LSE never started; VBAT has no battery; the load capacitors are wrong; the program initializes the RTC again at every power-up and clears the counter.
- **Fix**: fit a 32.768 kHz crystal and choose the load capacitors with the crystal from the 5 pF to 15 pF range; 6 pF is not required. Pick a crystal whose load capacitance CL is 7 pF or less, never a 12.5 pF one (DS5319 Rev 20 section 5.3.6, the text below Table 23). Put a battery on VBAT. At power-up, read a marker in a backup register first, and skip the initialization if it is already set. Pins 3 and 4, and PRL = 32767, are in chapter 11.

## 4. Hardware

Start this family with a multimeter. Measuring voltage and continuity is much faster than editing code.

**H1 The LED stays dark**
- **Symptom**: the LED does not react when you connect it.
- **Cause**: the polarity is reversed; the series resistor is too large; the pin cannot drive enough current.
- **Fix**: check anode and cathode (the long leg is the anode). For an external lamp, use pin 10 and 270 Ω from chapter 03. Pin 2 PC13 cannot be a current source. Drive a large load through a transistor or a MOSFET.

**H2 The chip gets very hot**
- **Symptom**: it is hot to the touch.
- **Cause**: a pin is shorted; 5 V was applied straight to a pin that is not 5 V tolerant; the supply is reversed.
- **Fix**: remove power immediately. Look for shorts, measure the voltages, and check the supply polarity. Do not power it again until you have found the cause.

**H3 Nothing happens at power-up, and the current is 0**
- **Symptom**: the board draws no current at all.
- **Cause**: power never arrives: the supply is not connected, a wire is broken, a fuse or a reverse-protection diode is open, or the regulator is dead. Zero current has nothing to do with BOOT0. With BOOT0 wrong, the chip still draws current; it just runs something other than your program.
- **Fix**: start at the power input and measure along the supply path all the way to the chip's VDD pins, until you find the stretch where the voltage disappears. If there is current but your program does not run, then check BOOT0 (the D entries and the deep part below).

**H4 Reset keeps chattering**
- **Symptom**: the chip resets over and over.
- **Cause**: NRST has no capacitor and picks up noise, or the watchdog is resetting the chip.
- **Fix**: put 0.1 µF from pin 7 NRST to ground as in DS5319 Figure 31. The watchdog timeout calculation is in chapter 11 and is not repeated here.

**H5 The external crystal does not start**
- **Symptom**: waiting for HSE or LSE times out, and the chip falls back to its internal clock.
- **Cause**: the load capacitors do not match; the crystal has a cold solder joint; the traces are too long.
- **Fix**: choose the load capacitors from the crystal's datasheet. For HSE, CL1 and CL2 are typically between 5 pF and 25 pF, and the estimate should count about 10 pF of pin and board stray capacitance (DS5319 Rev 20 section 5.3.6). Keep the crystal and the capacitors close to the chip, and try a crystal of better quality.

**H6 A breadboard makes poor contact**
- **Symptom**: it works, then it doesn't, and a nudge resets the board.
- **Cause**: Dupont wires and the breadboard have high contact resistance, and the wires are long.
- **Fix**: replace the wires, shorten them, and solder the signals that matter.

**H7 Serial and download problems that are really "share ground"**
- **Symptom**: without a common ground you get serial garbage, or the probe cannot connect.
- **Cause**: the two supplies sit at different ground potentials, so the signal's "0" and "1" have no common reference.
- **Fix**: connect the GND pins of both sides together. This one has no exceptions.

## 5. RTOS and the toolchain

These usually appear after you add FreeRTOS, switch IDEs, or regenerate code. The background is in chapter 15.

**R1 After you add an RTOS, `HAL_Delay` hangs**
- **Symptom**: `HAL_Delay` never returns.
- **Cause**: HAL's millisecond count stopped. Either the SysTick interrupt was handed entirely to the kernel and nobody calls `HAL_IncTick()` any more, or `HAL_Delay` was called after a kernel call but before the scheduler started. At that point the kernel masks interrupts with priority numbers 5–15, and HAL's tick interrupt is one of them.
- **Fix**: the repository example puts the HAL time base on TIM4 and leaves SysTick to the kernel; one tick is 1 ms. Before the scheduler starts, do not call `HAL_Delay` after a kernel call.

**R2 `configASSERT` spins forever**
- **Symptom**: the program stops in an assertion.
- **Cause**: look at where it stopped. Inside `vPortValidateInterruptPriority` in `port.c`, the interrupt that calls a FromISR function has a priority number that is too small (its priority is too high). Inside a queue or semaphore function, the handle passed in is most likely a null pointer because creating the object failed.
- **Fix**: an interrupt that calls FromISR needs a priority number of 5 or larger. `5 << 4 = 0x50`. Interrupts with a smaller number must not call FromISR. After creating an object, check whether the return value is `NULL`.

**R3 Task creation returns failure**
- **Symptom**: `xTaskCreate` returns something other than `pdPASS`.
- **Cause**: `configTOTAL_HEAP_SIZE` is too small to hold this task's stack and TCB.
- **Fix**: enlarge the heap, or use fewer tasks and smaller stacks. Stack depth is counted in words: 128 words is 512 bytes.

**R4 Calling a normal API from an interrupt goes wrong**
- **Symptom**: `xQueueSend` called inside an interrupt stops the program in an assertion, or causes a random HardFault.
- **Cause**: an interrupt may only call the FromISR form. The normal form enters the kernel's critical section, and the FreeRTOS Cortex-M3 port checks there whether it is running inside an interrupt; if it is, it asserts.
- **Fix**: switch to `xQueueSendFromISR`, and call `portYIELD_FROM_ISR` at the end.

**R5 A mysterious HardFault once an RTOS is running**
- **Symptom**: HardFault shows up at random.
- **Cause**: a task's stack overflowed and overwrote other memory.
- **Fix**: set `configCHECK_FOR_STACK_OVERFLOW` to 2 (left out, it is 0 and nothing is checked), implement `vApplicationStackOverflowHook()` to find which task it is, then enlarge that task's stack.

**R6 The toolchain reports `cannot open linker script`**
- **Symptom**: the link cannot find the `.ld` script.
- **Cause**: the linker-script path or file name is wrong, or a copied project was never updated.
- **Fix**: check the `.ld` path after `-T`. CubeIDE and Keil each manage the linker script their own way, so set it again when you switch tools.

**R7 CubeMX regeneration overwrote your edits**
- **Symptom**: after you regenerate, the code you wrote by hand is gone.
- **Cause**: the code sat outside a `USER CODE BEGIN` / `USER CODE END` pair.
- **Fix**: put all your own code inside `/* USER CODE BEGIN xxx */ ... /* USER CODE END xxx */`.

## Hands-on labs (practice at debugging)

Each lab below causes one error on purpose, so you can see what it looks like and then fix it with its entry. Once you have seen a real error message, it will not panic you the next time.

1. **Lab 1: cause C1 on purpose.** Delete the `Core/Inc` include path in the project settings, build once, then put it back.
   - Expected: the build reports `fatal error: main.h: No such file or directory` (or another header name), followed by a string of knock-on errors.
   - How to check: read only the first error; it names the missing file. Once the path is back, the whole string of errors disappears together.
   - If it fails, check first: if the deleted path was not used, nothing breaks; try another one. In CubeIDE, Clean before Build, or you are looking at an old build.
2. **Lab 2: cause P4 on purpose.** Remove the pull-up resistors from the I2C bus, call `HAL_I2C_Master_Transmit` once, and print its return value.
   - Expected: it returns `HAL_ERROR`, `HAL_BUSY`, or `HAL_TIMEOUT`, not `HAL_OK`.
   - How to check: measure the idle voltage on SCL and SDA with a multimeter. With pull-ups it is close to 3.3 V; without them it drops close to 0 V or wanders.
   - If it fails, check first: many sensor modules carry their own pull-ups, so removing the external ones still leaves the module's. Look for them on the module's circuit diagram.
3. **Lab 3: cause D2 on purpose, then rescue the board.** Call `__HAL_AFIO_REMAP_SWJ_DISABLE()` during initialization to turn SWD off, download once, then rescue the board once with each of the two methods in D2.
   - Expected: the download succeeds, and the next connection reports no target.
   - How to check: both Connect under reset and BOOT0 high at power-up connect again; after a full-chip erase and BOOT0 back to 0, the board is back to normal.
   - If it fails, check first: is the ST-Link's NRST wire connected to the board's NRST? After moving the BOOT0 jumper, reset or power-cycle the board, because the BOOT pins are only latched after a reset.
4. **Lab 4: cause R1 on purpose.** Leave the HAL time base on SysTick, and add `HAL_Delay(100)` after `xQueueCreate` and before `vTaskStartScheduler()`.
   - Expected: the program stops on that line, the scheduler never starts, and the task's LED never blinks.
   - How to check: pause in the debugger; it sits in the wait loop of `HAL_Delay`. Watch the variable `uwTick`: it no longer increases.
   - If it fails, check first: if SysTick's priority number is below 5, it is not masked; look at its priority in CubeMX. If `HAL_Delay` sits before every kernel call, it does not hang either. The fix: move the time base to TIM4 with a priority number below 5, or simply do not delay during that window.
5. **Lab 5: see the evidence of a dead HSE in the minimal project.** Change `osc.HSEState` in the minimal project to `RCC_HSE_OFF` to simulate a crystal that does not start, and download and run it. Then add `USART1->BRR = 0x271;` after `bsp_init()` to simulate a baud rate fixed for 72 MHz.
   - Expected: in the first step the UART prints `SYSCLK=8000000 Hz PCLK2=8000000 Hz HSE FAILED`, and the text is readable. In the second step the terminal shows only garbage at 115200; switch it to 12800, press reset, and the text is readable again.
   - How to check: 12800 = 8 000 000 / (16 × 39.0625), and `0x271` splits into a mantissa of 39 and a fraction of 1/16.
   - If it fails, check first: some USB-TTL chips do not support a non-standard rate such as 12800; use one that accepts custom rates. When you are done, set `HSEState` back to `RCC_HSE_ON`.

After these labs, add the new problems from your own projects to a table of your own, written as symptom, cause, fix, with one cause per row and the evidence you used to confirm it.

## Self-test

1. You power up with BOOT1 = 0 and BOOT0 = 1. Where does the CPU start executing? Is the program in Flash still there? What do you have to do to run it again?
2. Register-level code fixes USART1's BRR at `0x271`, but HSE never starts and the system stays on the 8 MHz HSI. What is the actual baud rate? Would the same happen with HAL initialization?
3. A 32.768 kHz crystal is specified with a load capacitance CL = 6 pF. You estimate the pin and board stray capacitance at 2 pF and use two equal capacitors. How many picofarads is each?
4. The program is in Flash. While debugging you set 8 breakpoints, and two of them never stop. Why?
5. After you add an SPI display, an I2C sensor, and CAN, the program freezes now and then. Following the five steps, what do you do in step 2 and in step 3?

Answers:

1. It starts from system memory, which on this chip is at `0x1FFFF000` and holds the factory bootloader (RM0008 Rev 21 section 3.4 Table 9). The program in Flash is still at `0x08000000`; it was not erased, only not executed. Put BOOT0 back to 0, then reset or power-cycle. The BOOT pins are latched on the 4th rising edge of SYSCLK after reset, so moving the jumper without a reset does nothing.
2. The mantissa of `0x271` is 0x27 = 39 and the fraction is 1/16 = 0.0625, so USARTDIV = 39.0625. Baud rate = 8 000 000 / (16 × 39.0625) = 8 000 000 / 625 = 12800. At 72 MHz it is 72 000 000 / 625 = 115200. With HAL initialization, `HAL_UART_Init()` recomputes BRR from the PCLK2 of that moment (8 MHz) and writes `0x45`, so the rate stays close to 115200 and 12800 does not happen, unless the clock changes again after HAL initialization, for example when CSS switches the system back to HSI.
3. With two equal capacitors, CL = C / 2 + Cstray (the formula in DS5319 Rev 20 section 5.3.6), so 6 = C / 2 + 2 and C = 8 pF. This is exactly the datasheet's example: 6 pF is the crystal's load capacitance, not the value of the capacitors you solder. 8 pF falls inside the 5 pF to 15 pF range.
4. When ST-Link debugs code in Flash, only hardware breakpoints work, and this M3's FPB has only 6 instruction comparators (RM0008 Rev 21 section 31.12). The 7th and 8th have no comparator left. Delete two, or set them after earlier ones are cleared.
5. Step 2: fall back to the minimal project that only blinks and echoes, and confirm that the chip, supply, clock, and UART are fine and the minimal project does not freeze. Step 3: on top of the minimal project, add one thing at a time: first the SPI display, run it for a while, then I2C, then CAN. Whichever addition brings the freeze back holds the problem, either in itself or in how it shares resources with the earlier ones (a shared DMA channel, interrupt priorities, stack space).

## Principle and scope

> [!NOTE]
> From this section to "Pitfalls and sources" is the deep part. It pins the conclusions above to one part number, one manual section, and numbers you can recompute. On a first read you can skip it and come back after the labs.

This chapter is an index, not a second peripheral tutorial, and the orderable part is still STM32F103C8T6. The paragraphs below pin the conclusions that are easiest to get wrong to the manuals.

**38 entries.** C1 through C8 is 8, D1 through D7 is 7, P1 through P9 is 9, H1 through H7 is 7, and R1 through R7 is 7: `8 + 7 + 9 + 7 + 7 = 38`.

**Pins to check when the probe cannot see the chip.** When the probe reports no target, look first at pin 34 PA13 = SWDIO, pin 37 PA14 = SWCLK, a shared ground, 3.3 V, and pin 7 NRST. Pin 35 is VSS_2, not SWCLK. Only after these check out, look at the code and the optimization level; editing `-O2` before the wires are checked is going in the wrong direction. The SWD wiring drawing is in chapter 01 and is not redrawn here. See [DS5319 SWD](#source-ds5319-swd).

**Reset capacitor.** Pin 7 NRST takes 0.1 µF to ground as in DS5319 Figure 31, which is 100 nF. The value of the internal pull-up is not given here. See [DS5319 NRST](#source-ds5319-nrst).

**Boot modes.** RM0008 Rev 21 section 3.4 Table 9 defines three combinations. With pin 44 BOOT0 = 0 (BOOT1 either way), the chip boots from main Flash, which is at `0x08000000`. With BOOT1 = 0 and BOOT0 = 1, it boots from system memory, which on this chip is at `0x1FFFF000` and holds the factory bootloader. With BOOT1 = 1 and BOOT0 = 1, it boots from the embedded SRAM. `0x1FFFB000` is the system-memory address of connectivity-line parts (STM32F105/107) and does not apply to this C8. The BOOT pins are latched on the 4th rising edge of SYSCLK after reset, as chapter 00 also says, and they are sampled again on wake-up from Standby. BOOT1 shares pin 20 with PB2 (DS5319 Rev 20 Table 5). See [RM0008 boot](#source-rm0008-boot).

**Capacity.** STM32F103x8 has 64 KB of Flash and 20 KB of SRAM; the 128 KB of the xB does not apply to the C8T6. When the link says something does not fit, estimate with these two numbers. See [DS5319 SWD](#source-ds5319-swd).

**A UART that fell back to HSI.** When HSE does not start, SYSCLK is the 8 MHz HSI. USART1's `0x271` is 115200 when computed for 72 MHz, and 12800 on 8 MHz. Chapter 16 uses the same numbers, so this chapter does not draw another bit frame. HAL recomputes BRR from the PCLK2 of the moment at initialization, so 12800 mostly shows up in register-level code with a fixed BRR. See [RM0008 USART](#source-rm0008-usart).

**LSE capacitors.** LSE is still 32.768 kHz on pins 3 and 4, pin 1 is VBAT, and PRL = 32767. Choose the load capacitors with the crystal from the 5 pF to 15 pF range. The 6 pF in the datasheet's example is the crystal's load capacitance CL: it is not a capacitor value, and it is not required. With CL = 6 pF and 2 pF of stray capacitance, each capacitor works out to 8 pF. See [DS5319 LSE](#source-ds5319-lse).

**Two RTOS rules.** The repository example puts the HAL time base on TIM4 and leaves SysTick to the kernel; one tick is 1 ms. See [repository examples](#source-project-examples). An interrupt that calls FromISR needs a priority number of 5 or larger: `5 << 4 = 0x50`. The derivation is in chapter 15, and that priority figure is not redrawn here. See [FreeRTOS](#source-freertos-syscall).

**External lamp.** As in chapter 03, the external lamp goes on pin 10 with 270 Ω in series. Pin 2 PC13 is not used as a current source. See [DS5319 GPIO](#source-ds5319-gpio).

**When you change chips.** The pin numbers, boot addresses, and capacities hold only for STM32F103C8T6 (LQFP48). Another package means looking up the pinout table again; a connectivity-line part moves system memory to `0x1FFFB000`; XL-density parts add an option to boot from the second Flash bank, which the C8 does not have.

## Key figures

<p align="center">
  <img src="../../assets/diagrams/sample-18-boot-triage.svg" width="760" alt="When the probe cannot see the chip, look at pins 34, 37, and 44 first. BOOT0 = 1 and BOOT1 = 0 runs from 0x1FFFF000.">
  <br><sub>▲ Drawn for this book. The normal path is pin 44 BOOT0 = 0, starting at 0x08000000, with the probe on pin 34 PA13 and pin 37 PA14. Pin 7 NRST carries the 0.1 µF from Figure 31. The failure path is BOOT0 = 1 and BOOT1 = 0, with the CPU at 0x1FFFF000, or an optimization edit before those four pins are checked. Pin 35 is VSS_2 and points at chapter file 01. Sources: [DS5319](#source-ds5319-swd) Figure 31 and Table 5, and [RM0008 boot](#source-rm0008-boot).</sub>
</p>

<p align="center">
  <img src="../../assets/gif/boot0-low.gif" width="640" alt="Pin 44 is 0, the probe is on pins 34 and 37, and the target appears">
  <br><sub>▲ Auxiliary figure for the web and for posts. It plays only the normal path: pin 44 is 0, the probe is on pins 34 and 37, and the target appears. Print from the static figure. BOOT0 = 1 and an optimizer edit are not on this GIF.</sub>
</p>

Read the static figure from top to bottom. The three lines at the top are the four pins to look at first: pin 34 PA13 = SWDIO, pin 37 PA14 = SWCLK, the 0.1 µF on pin 7 NRST, and pin 44 BOOT0. The normal-path panel in the middle is BOOT0 = 0: the CPU starts at `0x08000000`, and the probe is on pins 34 and 37 with a shared ground and 3.3 V. Below it, the failure-path panel is BOOT0 = 1 and BOOT1 = 0: the CPU is in system memory at `0x1FFFF000`, and the program in Flash looks as if it was never programmed; the other failure is editing `-O2` before checking these pins. The side note at the bottom reminds you that pin 35 is VSS_2. The GIF plays only the normal path. The `toolchain-flow.svg` at the top of the chapter shows the data flow of compile, link, flash, and run, which matches the C and D entries; the compile arrows are not on this static figure.

## Timing and state

When the chip cannot be seen or the program does not run, work down this table from the top, and do not look at a row until the one above it passes. The pin numbers come from [DS5319 SWD](#source-ds5319-swd), and the boot addresses from [RM0008 boot](#source-rm0008-boot):

| Look at this first | Value | Next step |
| --- | --- | --- |
| Pins 34 and 37 | PA13 = SWDIO, PA14 = SWCLK, shared ground, 3.3 V | Do not edit code until these are connected |
| NRST | Pin 7, 0.1 µF | As in Figure 31; this row gives no pull-up value |
| BOOT, normal | BOOT0 = 0, main Flash `0x08000000` | Your program starts |
| BOOT, wrong | BOOT0 = 1 and BOOT1 = 0, `0x1FFFF000` | The factory bootloader runs, and your program looks unprogrammed; `0x1FFFB000` does not apply to the C8 |
| Optimization level | `-O2` edited before the wires are checked | Wrong direction; go back to the first row |
| Capacity | 64 KB Flash, 20 KB SRAM | Estimate with these two numbers when the link says something does not fit |
| UART | HSI at 8 MHz, `0x271` unchanged | The actual rate is 12800 |
| Time base | TIM4, 1 ms | SysTick stays with the kernel |
| Priority | A number of 5 or larger | `5 << 4 = 0x50` |
| Crystal | 5 pF to 15 pF, chosen with the crystal | 6 pF is not required |

After reset, the chip reaches your first line of code in the order below (RM0008 Rev 21 sections 3.4 and 7.2.6). A wrong BOOT0 breaks step 3:

| Step | What happens |
| --- | --- |
| 1 | Reset is released; SYSCLK is the 8 MHz HSI |
| 2 | BOOT0 and BOOT1 are latched on the 4th rising edge of SYSCLK |
| 3 | The boot memory is chosen by Table 9: main Flash or system memory is aliased at `0x0000 0000` and stays reachable at its own address; with SRAM chosen, SRAM is only at `0x2000 0000` |
| 4 | The initial stack pointer is fetched from `0x0000 0000` and the reset vector from `0x0000 0004`, and execution begins |

## Pitfalls and sources

Read each row left to right: the symptom first, then the cause and what to do; the last two columns say where the conclusion comes from and how far that source goes.

| Symptom | Cause | What to do | Source | What the source supports |
| --- | --- | --- | --- | --- |
| The probe reports no target | The wires were not checked | Look at pins 34 and 37, ground, and 3.3 V first | [DS5319 SWD](#source-ds5319-swd) | Pin 34 PA13 is SWDIO, pin 37 PA14 is SWCLK, and pin 35 is VSS_2 |
| The program looks unprogrammed | Pin 44 BOOT0 is pulled high | Put BOOT0 back to 0, then reset | [RM0008 boot](#source-rm0008-boot) | BOOT1 = 0 and BOOT0 = 1 enters `0x1FFFF000`; the C8 is not a connectivity-line part |
| The board keeps resetting itself | NRST lacks the Figure 31 capacitor | Add 0.1 µF as in Figure 31 | [DS5319 NRST](#source-ds5319-nrst) | Figure 31's external reset capacitor is 0.1 µF; this row gives no pull-up value |
| The link says Flash or RAM is too small | The estimate used a larger part | Estimate with the C8's 64 KB and 20 KB | [DS5319 SWD](#source-ds5319-swd) | The 128 KB of the xB does not apply to the C8T6 |
| Serial garbage, and the clock was never checked | The clock fell back to HSI while BRR was still computed for 72 MHz | Confirm that SYSCLK is not stuck at 8 MHz | [RM0008 USART](#source-rm0008-usart) | `0x271` is 115200 at 72 MHz and 12800 at 8 MHz |
| Both LSE capacitors were fitted as 6 pF | The example crystal's CL was taken for a capacitor value | Choose the capacitors with the crystal, from 5 pF to 15 pF | [DS5319 LSE](#source-ds5319-lse) | 6 pF is not a required value in the LSE section; 32.768 kHz and PRL = 32767 follow chapter 11 |
| `HAL_Delay` does not return after FreeRTOS is added | HAL's tick still hangs on SysTick | Move the time base to TIM4 | [repository examples](#source-project-examples) | The time base in `examples/freertos-task` is TIM4 |
| An interrupt stops in `configASSERT` | The priority number is too small | Use a number from 5 to 15 | [FreeRTOS](#source-freertos-syscall) | `5 << 4 = 0x50`; an interrupt with a smaller number must not call FromISR |
| An external lamp stays dark while resistor values are guessed within a range | Neither the pin nor the resistor was fixed | Use pin 10 and 270 Ω from chapter 03 | [DS5319 GPIO](#source-ds5319-gpio) | Pin 2 PC13 cannot be a current source; this row picks no other resistor |
| You set 8 breakpoints and two never stop | There are only 6 hardware breakpoints | Delete breakpoints until 6 or fewer remain | [PM0056 DWT](#source-pm0056-dwt) | This M3 has 6 hardware breakpoints |
| The program is gone after readout protection is cleared | Setting RDP back to unprotected first mass-erases main Flash | Make sure the program is backed up before you start | [PM0075 RDP](#source-pm0075-rdp) | Programming RDP back to the read-allowed key 0xA5 first mass-erases main Flash |
| TIM1's PWM pin has no output | MOE in BDTR is not set | Set MOE, or use `HAL_TIM_PWM_Start` | [RM0008 TIM](#source-rm0008-tim) | `TIMx_BDTR` is at offset 0x44, and bit 15 is MOE |

This table only takes entries that a source card can prove directly. The I2C 9-clock bus recovery (NXP UM10204), the W25Q SPI modes (Winbond datasheet), and the debounce time (a rule of thumb) have no card in Appendix E, so they stay in the entries above and out of this table.

## Related resources

- The "common traps" section in each chapter of this repo: [chapter 03](03-gpio-and-led.md) through [chapter 17](17-debug.md), one peripheral at a time.
- RM0008 / RM0090 reference manuals: register bit definitions and timing. They are the last word when you are debugging.
- The datasheet (DS): electrical parameters (voltage, current, clock), so you can tell whether the hardware is outside its ratings.
- Official tools: STM32CubeProgrammer (readout protection and option bytes), STM32CubeMX (check the configuration).
- Related chapters: [chapter 01, dev environment](01-dev-environment.md), [chapter 17, debug and performance](17-debug.md), [chapter 20, resources and toolchain](20-resources.md).
- Figure: `../../assets/animations/toolchain-flow.svg` (author-drawn vector).

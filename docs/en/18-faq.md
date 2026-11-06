# 18 FAQ

> 中文：[18 常见问题 FAQ](../18-常见问题FAQ.md)

> Start from the first boundary you can verify: did an ELF exist, can the probe read the ID, is there a pin waveform, and what do the status registers say? The FAQ gives the next check, not permission to change five settings at once.

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
9. 排错五步有顺序：先复现，再缩到最小。前两步走完还不知道范围，再去二分和看证据。能测就别猜。
10. 这一章的失败大多分两层：调试器认不出芯片，先查线和 BOOT，不是代码；编译链接报错，先查路径和宏，也不是代码。

</details>
<!-- /video:ch18 -->
## Principle and scope

Save the first complete error. If you already have an ELF to program, connect the probe and read the Device ID. If that fails, check power, wiring, and reset. If the ID is readable but the application does not run, check boot selection and program state. Record these outcomes separately, then choose a connection or startup check.

This index uses the STM32F103C8T6 and contains 38 entries: C1–C8 for build and link, D1–D7 for download and debug, P1–P9 for peripherals, H1–H7 for hardware, and R1–R7 for RTOS and tools. Each entry gives candidate causes and a next check; the corresponding chapter explains the mechanism.

In LQFP48, pin 34 PA13 = SWDIO, pin 37 PA14 = SWCLK, and pin 7 is NRST. Check shared ground, the target's 3.3 V supply, and the probe's voltage reference first. Check the specific probe before treating its reference pin as a power source. DS5319 Figure 31 uses a 0.1 µF external reset capacitor. Pin 35 is VSS_2, not SWCLK. See [DS5319 SWD](#source-ds5319-swd).

Pin 44 BOOT0 = 0 selects main Flash at `0x08000000`, regardless of BOOT1. With BOOT0 = 1, BOOT1 = 0 selects system memory at `0x1FFFF000`, while BOOT1 = 1 selects SRAM (`0x20000000`). `0x1FFFB000` belongs to the connectivity-line F105/F107, not the C8. The BOOT pins are latched on the 4th SYSCLK rising edge after reset (chapter 00). These choices determine where execution starts; BOOT0 high alone does not prevent reading the ID over SWD. See [RM0008 boot](#source-rm0008-boot).

The C8 has 64 KB of Flash and 20 KB of SRAM. After reset it starts on the 8 MHz HSI. If HSE fails to start, the startup code determines whether execution stops in an error handler or switches to another clock. An HSE failure during operation with CSS enabled has a separate hardware switching mechanism. Calculate USART1 baud from its actual PCLK2: with AHB and APB2 prescalers both at 1 and BRR still `0x271`, SYSCLK at 72 MHz gives 115200 bit/s and HSI at 8 MHz gives 12800 bit/s. Stop exit in chapter 16 explicitly selects HSI first, so check BRR before restoring the working clock there too. See [RM0008 USART](#source-rm0008-usart).

LSE stays 32.768 kHz, pins 3 and 4, pin 1 VBAT, and PRL = 32767. Choose the capacitors in the 5 pF to 15 pF range with the crystal. 6 pF is not required. See [DS5319 LSE](#source-ds5319-lse).

The repository example puts HAL's 1 ms time base on TIM4 and leaves SysTick to the kernel. The RTOS tick duration is separately set by `configTICK_RATE_HZ`. See [repository examples](#source-project-examples). With this book's 4 priority bits and syscall threshold of 5, an interrupt calling FromISR needs a numeric priority of 5 or larger; `5 << 4 = 0x50`. Recheck the threshold after changing the configuration; chapter 15 explains why. See [FreeRTOS](#source-freertos-syscall).

Wire the external lamp as in chapter 03: pin 10 PA0 through 270 Ω. Pin 2 PC13 sits behind the backup-domain power switch. Note 5 of the datasheet limits it to sinking at most 3 mA at up to 2 MHz, and forbids using it as a current source for an LED. The on-board LED is wired to sink. See [DS5319 GPIO](#source-ds5319-gpio).

## Key figures


<p align="center">
  <img src="../../assets/animations/sample-18-boot0-flow.svg" width="720" alt="Reset latches BOOT0/BOOT1 to select one of three boot memories">
  <br><sub>▲ Drawn for this book. BOOT0/BOOT1 select the startup location after reset; check SWD connectivity separately.</sub>
</p>


<p align="center">
  <img src="../../assets/diagrams/sample-18-boot-triage.svg" width="760" alt="SWD connection checks and the three BOOT0/BOOT1 startup choices">
  <br><sub>▲ Drawn for this book. PA13/PA14, power, and NRST support connection checks; BOOT0/BOOT1 select the startup location. System-memory boot neither means an unidentified chip nor an erased Flash. See [DS5319](#source-ds5319-swd) Figure 31, Table 5, and [RM0008 boot](#source-rm0008-boot).</sub>
</p>

<p align="center">
  <img src="../../assets/illustrations/handraw/ch18-boot-triage.png" width="760" alt="Handraw: FAQ boot triage BOOT0 and SWD (原理示意)">
  <br><sub>▲ Knowledge track (Handraw · 原理示意 / not a photo). BOOT0=0 selects Flash. With BOOT0=1, BOOT1 distinguishes system memory from SRAM. A connection failure and a wrong startup location need separate checks.</sub>
</p>

<p align="center">
  <img src="../../assets/gif/boot0-low.gif" width="640" alt="SWD wiring example with BOOT0=0 for Flash startup">
  <br><sub>▲ Six frames show Flash mapping and the MSP and reset-vector reads with BOOT0=0. The SWD wiring checks on the right are independent. Selecting Flash still requires a valid image; for print, use the static figure above.</sub>
</p>

The whole path from compile to download is in the opening `toolchain-flow.svg` animation.

## Timing and state

| Look at this first | Value | Next step |
| --- | --- | --- |
| Pins 34 and 37 | PA13 = SWDIO, PA14 = SWCLK, shared ground, 3.3 V | Do not edit code until these are connected |
| NRST | Pin 7, 0.1 µF | As in DS5319 Figure 31 |
| Flash startup | BOOT0 = 0, main Flash `0x08000000` | Check the application entry |
| System-memory startup | BOOT0 = 1 and BOOT1 = 0, `0x1FFFF000` | The Flash application does not execute; `0x1FFFB000` is for the connectivity line |
| SRAM startup | BOOT0 = 1 and BOOT1 = 1, `0x20000000` | Requires a valid SRAM program and vector setup |
| Capacity | 64 KB Flash, 20 KB SRAM | Write the linker script with these |
| USART1 | PCLK2 = 8 MHz and BRR = `0x271` | 12800 bit/s |
| HAL time base | TIM4, 1 ms in this example | Check separately from the RTOS tick |
| FromISR priority | Threshold 5 with 4 priority bits in this book | Numeric priority of 5 or larger, `5 << 4 = 0x50` |
| Crystal | 5 pF to 15 pF, chosen with the crystal | 6 pF is not required |

## Pitfalls and sources

| What you see | Why | What to do | Source | What the source shows |
| --- | --- | --- | --- | --- |
| The probe reports no target | The wires were not checked | Look at pins 34 and 37, ground, and 3.3 V first | [DS5319 SWD](#source-ds5319-swd) | Pin 34 PA13 is SWDIO. Pin 37 PA14 is SWCLK. Pin 35 is VSS_2 |
| The program looks unprogrammed | Pin 44 is pulled high | Put BOOT0 back to 0 | [RM0008 boot](#source-rm0008-boot) | BOOT1=0 and BOOT0=1 enters `0x1FFFF000`. The C8 is not a connectivity-line part |
| The chip resets repeatedly | Supply dips, interference, a watchdog, or another reset source | Save reset flags, then inspect supply and NRST waveforms | [DS5319 NRST](#source-ds5319-nrst) | NRST has an internal pull-up; Figure 31 uses a 0.1 µF external capacitor |
| The link says Flash or RAM is too small | The estimate used a larger part | Use the C8 cells, 64 KB and 20 KB | [DS5319 SWD](#source-ds5319-swd) | 128 KB is the xB size (the CB, for example); the C8T6 has 64 KB |
| Serial data is garbage and the clock was not checked | PCLK2 or BRR differs from the expected value | Read SWS, AHB/APB2 prescalers, and BRR | [RM0008 USART](#source-rm0008-usart) | BRR=`0x271`: 115200 with PCLK2=72 MHz, 12800 with 8 MHz |
| Row P9 was built with 6 pF | One capacitor was treated as required | Choose the capacitors with the crystal, from 5 pF to 15 pF | [DS5319 LSE](#source-ds5319-lse) | 6 pF is not a required value printed in the LSE section. 32.768 kHz and PRL = 32767 are covered in chapter 11 |
| `HAL_Delay` does not return after FreeRTOS is added | The time base is still SysTick | Move the time base to TIM4 | [repository examples](#source-project-examples) | The time base in `examples/freertos-task` is TIM4 |
| An interrupt stops in `configASSERT` | The numeric priority is too urgent | Use 5 or a larger number | [FreeRTOS](#source-freertos-syscall) | `5 << 4 = 0x50`. A smaller number must not call FromISR |
| An external lamp stays dark while the resistor is guessed inside a range | The pin and the resistor were never fixed | Use pin 10 and 270 Ω from chapter 03 | [DS5319 GPIO](#source-ds5319-gpio) | Pin 2 PC13 cannot source the current |
## Learning goals

- [ ] Build the habit of searching by symptom, instead of editing code at random.
- [ ] Find a first check that distinguishes candidate causes for each symptom.
- [ ] Use a minimal check (blink an LED, loop a byte back) to isolate the problem quickly.
- [ ] Know which traps are configuration, which are hardware, and which are timing.

> How to use this page: 38 entries. The prefix `C*` is build and link, `D*` is download and debug, `P*` is peripherals, `H*` is hardware, and `R*` is RTOS and toolchain.

## 1. Build and link


<p align="center">
  <img src="../../assets/diagrams/sample-18-link-map.svg" width="760" alt="Link-map triage: overflow vs wrong FLASH ORIGIN">
  <br><sub>▲ Drawn for this book. C8=64 KB/20 KB; read the region line before rewriting C.</sub>
</p>

<p align="center">
  <img src="../../assets/illustrations/handraw/ch18-link-map.png" width="760" alt="Handraw: link-map overflow vs wrong FLASH ORIGIN (原理示意)">
  <br><sub>▲ Knowledge track (Handraw · 原理示意 / not a photo). Align .text/.data/.bss to the map; overflow ≠ wrong ORIGIN; not a photo.</sub>
</p>


**C1 Cannot find `stm32f1xx_hal.h`**

- **Symptom**: the build reports `fatal error: stm32f1xx_hal.h: No such file or directory`.
- **Cause**: the include path does not contain the HAL `Inc` directory.
- **Fix**: add `Drivers/STM32F1xx_HAL_Driver/Inc` and `Core/Inc` to the project's include path, or to `CMakeLists.txt`.

**C2 The link reports `undefined reference to HAL_GPIO_Init`**

- **Symptom**: compilation succeeds, then the link reports an undefined symbol.
- **Cause**: `stm32f1xx_hal_gpio.c` was not built, or the GPIO module was disabled by conditional compilation.
- **Fix**: check that the source is compiled and that `HAL_GPIO_MODULE_ENABLED` is defined in `stm32f1xx_hal_conf.h`. `HAL_MODULE_ENABLED` is the umbrella switch; it does not replace the per-module macro.

**C3 `region FLASH overflowed by N bytes`**

- **Symptom**: the link reports that the ROM region overflowed.
- **Cause**: code and constants exceed the part's Flash (an F103C8 has only 64 KB).
- **Fix**: turn on `-Os`, drop floating-point `printf`, and remove unused libraries. Or move to a part with more Flash.

**C4 `region RAM overflowed`**

- **Symptom**: the link reports that RAM is short.
- **Cause**: a global array is too large, or the stack and heap reservations are too large (an F103C8 has only 20 KB of RAM).
- **Fix**: use the map to see how much `.data` / `.bss` and the reserved heap and stack consume. Shrink buffers or adjust `_Min_Heap_Size` and `_Min_Stack_Size` only after checking the required peak; making the link pass is not proof of safety.

**C5 Redefinition: `multiple definition of 'xxx'`**

- **Symptom**: the link reports a symbol defined more than once.
- **Cause**: the same external symbol is defined in several translation units. `int count;` in a header is a tentative definition; with `-fno-common` it usually fails to link, while `-fcommon` may merge it.
- **Fix**: put `extern int count;` in the header and let one `.c` file own the definition. `static` creates a separate private variable in each translation unit; it is not a shared owner.

<p align="center">
  <img src="../../assets/illustrations/handraw/ch18-multi-def.png" width="760" alt="Handraw: a definition in a header, compiled once per including .c (原理示意)">
  <br><sub>▲ Knowledge track (Handraw · 原理示意 / not a photo). The initialized definition `int count = 0;` enters two translation units through the header and produces duplicate symbols. Use `extern int count;` with one definition in a `.c` file. Include guards prevent repeated inclusion within one translation unit. See [examples/](#source-project-examples).</sub>
</p>

**C6 `printf` prints garbage, or prints nothing**

- **Symptom**: the serial port receives garbage or blank lines.
- **Cause**: `printf` floating-point or semihosting setup, or `_write` / `__io_putchar` was never redirected.
- **Fix**: redirect `__io_putchar` to the UART. Add `-u _printf_float` if you need floating point.

**C7 The build reports `arm-none-eabi-gcc: not found`**

- **Symptom**: a command-line build fails.
- **Cause**: the toolchain is not installed, or it is not on `PATH`.
- **Fix**: install the GNU Arm Embedded Toolchain and set the environment variable, or use the toolchain that ships with CubeIDE.

**C8 The generated bin/hex is much larger than you expected**

- **Symptom**: the firmware image is far bigger than it should be.
- **Cause**: loadable code or constants are too large, or a wrong link address creates a large gap in the bin image; full-format `printf` can add code. Ordinary `.debug_*` sections usually enlarge the ELF but do not enter bin/hex load data.
- **Fix**: distinguish ELF size, the bin address span, and hex text size. Use the map and section table to locate the cause. `-Os`, `-ffunction-sections -fdata-sections`, and `--gc-sections` remove unreferenced code; address gaps require a link-layout fix.

## 2. Download and debug


<p align="center">
  <img src="../../assets/diagrams/sample-18-hardfault-ladder.svg" width="760" alt="HardFault: save the scene, then check address validity and the stack frame">
  <br><sub>▲ Drawn for this book. Save BFAR/MMFAR with the scene before checking valid flags. BFAR is a data-access address; stacked PC is an instruction address. They cannot substitute for each other.</sub>
</p>

<p align="center">
  <img src="../../assets/illustrations/handraw/ch18-hardfault-ladder.png" width="760" alt="Handraw: HardFault ladder CFSR→BFAR (原理示意)">
  <br><sub>▲ Knowledge track (Handraw · 原理示意 / not a photo). CFSR at 0xE000ED28 classifies the fault, and bit 15 marks BFAR valid. `IMPRECISERR` does not promise that PC points to the original write; check stacking errors first.</sub>
</p>


**D1 `No target connected` / the probe cannot see the target**

- **Symptom**: the programmer says it cannot find the target.
- **Cause**: SWD is wired backwards, ground is not shared, the board has no power, or the debug port was switched off.
- **Fix**: check SWDIO/SWCLK, shared ground, target power, and the probe's voltage reference. Connect NRST and try connect under reset. BOOT0 high by itself does not block SWD ID reads.

**D2 After flashing, the board acts bricked and never connects again**

- **Symptom**: once the program is downloaded, SWD disappears.
- **Cause**: the program configured PA13/PA14 as plain GPIO and turned SWD off.
- **Fix**: connect under reset to pause the application. You can also set BOOT0=1 and BOOT1=0, reset into system memory, and recover the firmware with STM32CubeProgrammer. BOOT0 alone does not determine the system-memory selection.

**D3 `Flash Download failed - Target DLL has been cancelled`**

- **Symptom**: the download fails partway through.
- **Cause**: the Flash algorithm or the clock does not match the part, or readout protection is on.
- **Fix**: check the part number, Flash algorithm, and RDP state. If you clear readout protection, confirm the F1 option-byte operation erases main Flash before applying it.

**D4 Breakpoints do nothing while debugging**

- **Symptom**: a breakpoint is skipped, or the tool says you have too many.
- **Cause**: the F103's 6 FPB code comparators are occupied, or the symbols do not match the programmed ELF. Read-only Flash does not prevent hardware breakpoints.
- **Fix**: delete old breakpoints and match the ELF to the target. Software breakpoints need tool support for the storage location. A conditional hardware breakpoint still uses a comparator. The DWT has 4 separate comparators for data watchpoints and other trace tasks; use `-O0` or `-Og` only when source mapping needs a less optimized build.

**D5 Single-step "jumps around"**

- **Symptom**: the line number hops while you single-step.
- **Cause**: the compiler reordered instructions, or it inlined the function.
- **Fix**: set the debug configuration to `-O0` or `-Og`.

**D6 ST-Link says its firmware is too old**

- **Symptom**: connecting prompts you to upgrade the ST-Link firmware.
- **Cause**: the old firmware does not match the new tools.
- **Fix**: upgrade with the ST-Link Upgrade tool. Be careful with a clone ST-Link: an upgrade can brick it.

**D7 The program stops in `HardFault_Handler` as soon as you start debugging**

- **Symptom**: a debug session starts already in HardFault.
- **Cause**: clock or peripheral init walked off the end of a structure, the vector table is wrong, or the stack is too small.
- **Fix**: save the address registers and fault scene first, then classify `CFSR`. Bit 15 says only that BFAR holds a valid bus-fault address. Check frame completeness and precise versus imprecise status before using PC with the same ELF; see [chapter 17](17-debug.md).


<p align="center">
  <img src="../../assets/diagrams/sample-18-faq-compare.svg" width="760" alt="Build/link, download/debug, peripherals, hardware, and RTOS each have one first probe — do not shotgun five config edits">
  <br><sub>▲ Drawn for this book. Check build logs and the map, target ID, serial bit width, power and NRST, or task state and blocking points. Keep the reading before choosing a change. See [RM0008 boot](#source-rm0008-boot) and [DS5319 NRST/SWD](#source-ds5319-nrst).</sub>
</p>

<p align="center">
  <img src="../../assets/illustrations/handraw/ch18-faq-compare.png" width="760" alt="Handraw: FAQ five-domain first-probe compare (原理示意)">
  <br><sub>▲ Knowledge track (Handraw · 原理示意 / not a photo). Choose one piece of evidence that separates causes in each domain, and keep the before-and-after result.</sub>
</p>

## 3. Peripherals


<p align="center">
  <img src="../../assets/diagrams/sample-18-uart-garbled.svg" width="760" alt="UART garbled checklist: baud · HSE · swap · 3.3 V">
  <br><sub>▲ Drawn for this book. Confirm SWS/BRR before rewriting string code.</sub>
</p>

<p align="center">
  <img src="../../assets/illustrations/handraw/ch18-uart-garbled.png" width="760" alt="Handraw: UART garbled checklist baud·HSE·swap·3.3 V (原理示意)">
  <br><sub>▲ Knowledge track (Handraw · 原理示意 / not a photo). Measure the bit width, then check the USART clock and BRR. Connect TX to the other side's RX, use compatible levels, and share ground.</sub>
</p>


**P1 A GPIO write does nothing**

- **Symptom**: after `HAL_GPIO_WritePin` the pin does not change.
- **Cause**: the GPIO clock was never enabled.
- **Fix**: call `__HAL_RCC_GPIOx_CLK_ENABLE()`.

**P2 One key press enters the interrupt many times**

- **Symptom**: one press prints several lines.
- **Cause**: the mechanical contact bounced, and nothing debounced it.
- **Fix**: confirm a stable level with a timestamp or task timer, or use an RC network. Let EXTI record the event instead of blocking in the interrupt.

**P3 Serial garbage**

- **Symptom**: everything you receive is garbage.
- **Cause**: the baud rates do not match, ground is not shared, or the clock is not the frequency you planned.
- **Fix**: use the same baud rate and shared ground, then read SWS, AHB/APB2 prescalers, and BRR. USART1 with BRR=`0x271` is 115200 at PCLK2=72 MHz and 12800 at PCLK2=8 MHz; after an HSE failure, also check the startup and CSS path.

**P4 I2C stalls inside `HAL_I2C_Master_Transmit`**

- **Symptom**: the program hangs, or the call times out.
- **Cause**: the pull-up resistors are missing, the address is wrong, or the bus is stuck low.
- **Fix**: put a 4.7 kΩ pull-up on SCL and on SDA. Check the 7-bit address. Recover the bus with 9 clock pulses.

**P5 An SPI Flash read comes back all FF**

- **Symptom**: the data you read is all 0xFF.
- **Cause**: CS was never pulled low, CPOL/CPHA is the wrong mode, or MISO is not connected.
- **Fix**: check the mode (a W25Q uses Mode 0), the chip-select timing, and the wiring.

**P6 ADC readings jump around**

- **Symptom**: the samples are unstable.
- **Cause**: the reference is noisy, the sample time is too short, or the source impedance is high.
- **Fix**: decouple VDDA, lengthen the sample time, and add a small capacitor on the input as a buffer.

**P7 Timer PWM has no output**

- **Symptom**: the oscilloscope shows no waveform.
- **Cause**: PWM was never started (`HAL_TIM_PWM_Start`), the pin alternate function is not set, or the channel is wrong.
- **Fix**: call `HAL_TIM_PWM_Start`, and check the alternate-function pin and the channel.

**P8 DMA moves data only once**

- **Symptom**: DMA transfers once, then stops.
- **Cause**: the channel is in normal mode, and you expected circular mode.
- **Fix**: switch it to `DMA_CIRCULAR`.

**P9 The RTC resets at power-up, or does not advance**

- **Symptom**: the time is gone after power is removed.
- **Cause**: LSE never started, VBAT has no battery, or the load capacitors are too large.
- **Fix**: fit a 32.768 kHz crystal and a battery on VBAT. Choose the load capacitors in the 5 pF to 15 pF range with the crystal. 6 pF is not required. Pins 3 and 4, and PRL = 32767, stay with chapter 11.

## 4. Hardware

**H1 The LED stays dark**

- **Symptom**: the LED does not react when you connect it.
- **Cause**: the polarity is reversed, the series resistor is too large, or the pin cannot source the current.
- **Fix**: check anode and cathode. The external lamp is pin 10 and 270 Ω, the same as chapter 3. Pin 2 PC13 cannot source the current. For a large current, drive the LED with a transistor or a MOSFET.

**H2 The chip gets very hot**

- **Symptom**: it is hot to the touch.
- **Cause**: a pin is shorted, 5 V was forced into a 3.3 V pin, or the supply is reversed.
- **Fix**: remove power immediately. Look for shorts and check the voltage. Check the supply polarity.

**H3 Nothing happens at power-up, and the current is 0**

- **Symptom**: the board draws no current at all.
- **Cause**: the supply is open, the meter is connected incorrectly, or the reading is below its range. A BOOT choice does not explain zero current from an unpowered chip.
- **Fix**: measure 3.3 V at the MCU supply pins and verify the ammeter connection. If power is present but the application does not run, then check BOOT0/BOOT1 and reset state.

**H4 Reset keeps chattering**

- **Symptom**: the chip resets over and over.
- **Cause**: a supply dip, noise on reset, or a watchdog reset. NRST has an internal pull-up, so an unpopulated external part is not the same as a floating logic input.
- **Fix**: save the RCC reset flags, then inspect supply and NRST. Add the 0.1 µF capacitor from pin 7 to ground as Figure 31 shows. See chapter 11 for watchdog periods and debug behavior.

**H5 The external crystal does not start**

- **Symptom**: the wait for HSERDY or LSERDY times out; the application may stop in an error path.
- **Cause**: the load capacitors do not match, the crystal is a cold solder joint, or the traces are too long.
- **Fix**: choose capacitors from the crystal datasheet, check soldering and trace length, and inspect the software timeout path. HSE failure does not guarantee an HSI fallback, and LSE failure does not automatically switch the RTC to another clock.

**H6 A breadboard makes poor contact**

- **Symptom**: it works, then it doesn't, and a nudge resets the board.
- **Cause**: Dupont wires and the breadboard have a high contact resistance, and the wires are too long.
- **Fix**: replace the wires, shorten them, and solder the signals that must be reliable.

**H7 Serial and download problems that are really "share ground"**

- **Symptom**: without a common ground you get garbage, or the probe cannot connect.
- **Cause**: the two supplies sit at different ground potentials.
- **Fix**: connect the GND pins together. This one is not optional.

## 5. RTOS and the toolchain

**R1 After you add an RTOS, `HAL_Delay` hangs**

- **Symptom**: `HAL_Delay` never returns.
- **Cause**: the HAL tick is not advancing: SysTick was replaced, the time-base interrupt is disabled, or the delay runs in a context that blocks the time base.
- **Fix**: observe whether `HAL_GetTick()` increases. The repository example uses TIM4 for HAL's 1 ms time base and leaves SysTick to the kernel; check `configTICK_RATE_HZ` separately for the RTOS tick.

**R2 `configASSERT` spins forever**

- **Symptom**: the program stops in an assertion.
- **Cause**: an interrupt priority number is too small (that priority is too high), or a null pointer was passed in.
- **Fix**: inspect the assertion site. With this book's 4 priority bits and threshold 5, an interrupt calling FromISR needs numeric priority 5 or larger (`5 << 4 = 0x50`); a smaller number must not call it. Recheck the threshold after changing the configuration.

**R3 Task creation returns failure**

- **Symptom**: `xTaskCreate` fails.
- **Cause**: the selected allocator cannot provide memory for the task control block and stack, because of capacity or fragmentation.
- **Fix**: check the selected heap implementation, free space, and task stack demand. For implementations that use a static heap array, also check `configTOTAL_HEAP_SIZE`; that macro does not control every allocator.

**R4 Calling a normal API from an interrupt crashes**

- **Symptom**: `xQueueSend` inside an ISR causes a HardFault.
- **Cause**: an ISR may call only the `FromISR` form.
- **Fix**: use `xQueueSendFromISR` and `portYIELD_FROM_ISR`.

**R5 A mysterious HardFault once an RTOS is running**

- **Symptom**: HardFault shows up at random.
- **Cause**: a task stack overflow, an out-of-bounds write, or a bad pointer; capture the scene before choosing one.
- **Fix**: save fault registers and stack data, then use stack high-water marks and `configCHECK_FOR_STACK_OVERFLOW`. That hook cannot catch every form of stack corruption.

**R6 The toolchain reports `cannot open linker script`**

- **Symptom**: the link cannot find the `.ld` script.
- **Cause**: the linker-script path or name is wrong, or a copied project never updated it.
- **Fix**: check the `.ld` path passed to `-T`. CubeIDE and Keil each manage the linker script in their own way.

**R7 CubeMX regeneration overwrote your edits**

- **Symptom**: after you regenerate, the code you wrote by hand is gone.
- **Cause**: that code sat outside a `USER CODE BEGIN/END` pair.
- **Fix**: keep generated-file edits between the matching `/* USER CODE BEGIN xxx */` and `/* USER CODE END xxx */` markers, and verify the keep-user-code option. Put independent application logic in files you own.

## A method for debugging (do these 5 steps first)

Keep the trigger and failure scene, then reduce to a minimal project. Test one hypothesis at a time and rerun under the same conditions. For intermittent faults, record frequency, load, and interrupt activity.

| Step | What you do | Why |
| --- | --- | --- |
| 1 | **Reproduce**: record the trigger, frequency, and load | Separate stable failures from timing and contact faults |
| 2 | **Minimize**: go back to a tiny project that only blinks, or only loops bytes | Separate a configuration problem from a logic problem |
| 3 | **Bisect**: comment out half the code, or enable peripherals one at a time | Find the module that introduced the bug |
| 4 | **Look at evidence**: a UART log, a logic-analyzer trace, `CFSR`/`BFAR` | Let data replace a guess |
| 5 | **Check the manual**: registers and timing in the RM or DS | Confirm that the part you were sure about is actually right |

> Three house rules: **if you can measure it, do not guess**, **share ground before you study the signal**, and **change one thing at a time**.

## Hands-on labs (practice at debugging)

1. **Build boundary:** On a temporary branch, remove one include path. Save the first complete error, compile command, and successful exit code after repair; do not capture only the final line.
2. **Bus boundary:** Power down, remove one I2C pull-up, and save idle level, NACK/timeout, and the recovered ACK trace after restoring it with power off.
3. **Debug boundary:** Power down, disconnect SWCLK, record `No target connected`, restore it, and confirm that Device ID is readable. Do not practice by flashing firmware that disables SWD.
4. **RTOS timebase boundary:** In a controlled build, keep the SysTick conflict and record the tick, HAL timebase, and blocked location. Move HAL to TIM4 and save the same test after recovery.
5. **Personal fault card:** Record symptom, first divergent boundary, minimum evidence, fix, and prevention check. Do not promote a guess into a cause.

Before leaving this chapter, keep four “failure evidence → one change → recovery evidence” records and explain why each experiment changed only one variable.

## Related resources

- The "common traps" section in each chapter of this repo: [chapter 03](03-gpio-and-led.md) through [chapter 17](17-debug.md), one peripheral at a time.
- RM0008 / RM0090 reference manuals: register bit definitions and timing. They are the last word when you are debugging.
- The datasheet (DS): electrical parameters (voltage, current, clock), so you can tell whether the hardware is outside its ratings.
- Official tools: STM32CubeProgrammer (readout protection and option bytes), STM32CubeMX (check the configuration).
- Related chapters: [chapter 01, dev environment](01-dev-environment.md), [chapter 17, debug and performance](17-debug.md), [chapter 20, resources and toolchain](20-resources.md).
- Figure: `../../assets/animations/toolchain-flow.svg` (author-drawn vector).

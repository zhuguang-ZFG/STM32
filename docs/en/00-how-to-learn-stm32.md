# 00 How to Learn STM32
> 中文：[如何学习 STM32](../00-如何学习STM32.md)

> The first LED that blinks at the frequency you worked out says more about your progress than ten videos. This chapter tells you what to learn first, what to buy, and in what order.

<p align="center">
  <img src="../../assets/animations/toolchain-flow.svg" width="760" alt="Toolchain data flow from writing code to flashing and running">
  <br><sub>▲ Animation: the full data path of compile → link → flash → run (vector drawing by the author)</sub>
</p>

<!-- video:ch00 -->
<p align="center">
  <video width="640" controls poster="../../assets/video/ch00-learn.png">
    <source src="../../assets/video/ch00-learn.mp4" type="video/mp4">
  </video>
  <br><sub>▲ Chapter video with Chinese voice-over (2.3 min). <a href="../../assets/video/ch00-learn.mp4">MP4</a> · <a href="../../assets/video/ch00-learn.srt">subtitles</a></sub>
</p>

<details>
<summary>Narration script (Chinese, same text as the subtitles)</summary>

1. 欢迎来到第零章。先别急着买一堆模块。把路线钉死：入门四周打底，进阶六周啃外设，实战八周做出能给人看的东西。
2. 顺序别跳。先把环境和时钟踩实，再碰 GPIO，然后才轮到串口。跳步的人，最容易摔在时钟没开、寄存器像写进虚空。
3. 板子用 BluePill 就够起步。手册请备三本：数据手册查引脚和电气，参考手册查寄存器，编程手册查内核。缺一本，后面就会靠猜。
4. 画面是本仓库画的工具链，不是实拍。源码要过编译、链接、烧录，复位之后程序才听你的。中间任何一步含糊，灯都不会按你的意思闪。
5. 别一上来就抄整套例程。第一场胜利只要一颗灯，按你自己算过的频率闪。抄来的工程，时钟或引脚一变，就会整片熄火。
6. 寄存器、标准库、HAL 都能点灯。入门先用 HAL 把下载和调试跑通，再回头看它改了哪几个寄存器。别同时学三套语法。
7. 常见的劝退是一次打开十个外设，或者仿真和真板打架就怀疑人生。这一章允许你慢，不允许你跳。跳过去的坑，会在项目里排队等你。
8. 口诀送你一句：先让一颗灯按你算过的频率闪。频率对了，说明时钟、引脚和延时你都真的算过，不是看视频看会的。
9. 四周结束时，你应该能独立新建工程、下载、单步，并讲清启动后先干什么。讲不清这些，先别翻串口那一章，回去把灯做稳。
10. 合上书，三问。BOOT0 拉低进哪里？HAL 比直接写寄存器多了哪一层？你的第一场胜利到底是什么？答案都在这一章正文里。

</details>
<!-- /video:ch00 -->
## The image flashed successfully, but reset does not run it

Learn the first board as the STM32F103C8T6. The boot rules below come from [RM0008 Rev 21 section 3.4 Table 9](#source-rm0008-boot). G0 and H7 boot differently; look those up in their own manuals.

The BOOT pins latch on the 4th rising edge of SYSCLK after reset, and are sampled again when leaving Standby. By the time `main` runs, this reset has already chosen its path; changing the pins then only affects the next reset. The CPU then reads the stack pointer from `0x00000000` and the reset vector from `0x00000004`.

When BOOT0=0, main Flash is aliased at `0x00000000` for either BOOT1 value, and the array itself stays at `0x08000000`. This is the setting for normal flashing and running.

When BOOT1=0 and BOOT0=1, system memory is aliased at `0x00000000`. STM32F103C8T6 is not a connectivity-line part, so that memory is at `0x1FFFF000`. The `0x1FFFB000` you often see online belongs to the connectivity line (F105/F107), not the C8. When BOOT1=1 and BOOT0=1 the core boots from embedded SRAM at `0x20000000`, which holds whatever was there at power-up, not the image at `0x08000000`. `0x08080000` is the start of Bank2 on XL-density parts; the 64 KB C8 has no Flash there.

## BOOT0 changes the fetch alias

<p align="center">
  <img src="../../assets/diagrams/sample-00-boot-state.svg" width="760" alt="With BOOT0 at 0 the CPU fetches Flash at 0x08000000 through 0x00000000; with BOOT0 at 1 and BOOT1 at 0 it fetches system memory">
  <br><sub>▲ Drawn for this book. STM32F103C8T6. The upper half is the normal case: the image goes in through SWDIO (PA13) and SWCLK (PA14) at 0x08000000, and BOOT0=0 aliases 0x00000000 onto that Flash. The lower half is BOOT1=0 and BOOT0=1: the CPU still reads 0x00000000, but the alias is system memory at 0x1FFFF000. The flashed image is still in Flash and is simply not fetched. The BOOT pins latch on the 4th rising edge of SYSCLK. Source: [RM0008 Rev 21 section 3.4 Table 9](#source-rm0008-boot).</sub>
</p>

## Three boot states

| State | BOOT1 | BOOT0 | What the CPU fetches from 0x00000000 | On STM32F103C8T6 |
| --- | --- | --- | --- | --- |
| Normal: the flashed program runs | x | 0 | The main-Flash alias; the array remains at 0x08000000 | Holds. The next word is at 0x00000004 |
| Failure: the chip stays in system memory | 0 | 1 | The system-memory alias | The memory is at 0x1FFFF000. 0x1FFFB000 is the connectivity-line address |
| Failure: boot from SRAM | 1 | 1 | Not the program in Flash | SRAM is at 0x20000000. The C8 has no Flash at 0x08080000 |

The latch is the 4th rising edge of SYSCLK after reset. Source: [RM0008 Rev 21 Table 9](#source-rm0008-boot).

## The address and the exact part must both match

| Symptom | Cause | What to do | Source | What the source shows |
| --- | --- | --- | --- | --- |
| The image is at 0x08000000, and reset runs something else | BOOT1=0 and BOOT0=1, so the boot alias is system memory | Pull BOOT0 to 0 and reset | [RM0008 Table 9](#source-rm0008-boot) | Flash itself remains at 0x08000000; this part's system memory is 0x1FFFF000 |
| BOOT pins changed inside main, and this reset already went the wrong way | The pins latched on the 4th rising edge of SYSCLK | Set BOOT0 and BOOT1 before reset | [RM0008 section 3.4](#source-rm0008-boot) | The latch is the 4th rising edge of SYSCLK; Standby exit samples them again |
| A connectivity-line or XL-density boot address was copied into the C8 project | 0x1FFFB000 and 0x08080000 belong to other densities | Use 0x1FFFF000 for system memory and 0x08000000 for Flash | [RM0008 section 3.4](#source-rm0008-boot) | 0x1FFFB000 applies only to the connectivity line and 0x08080000 only to XL density; STM32F103C8T6 is neither |

<p align="center">
  <img src="../../assets/diagrams/sample-00-boot-triage.svg" width="820" alt="When nothing shows on the board, triage in three rings, supply then BOOT0 then SWDIO/SWCLK, and stop at the first ring that fails">
  <br><sub>▲ Drawn for this book. Three rings, top to bottom. Ring 1 measures 3.3 V between VDD and VSS at the MCU, with Micro-USB as the only supply. Ring 2 confirms pin 44 BOOT0 = 0, so 0x00000000 aliases Flash at 0x08000000. Only then does ring 3 attach the probe: pin 34 SWDIO, pin 37 SWCLK, common ground, pin 7 NRST optional. The figure shows the order of the check: while one ring fails, any later code change is unverifiable. It does not prove the probe firmware is current, it does not say whether a clone's 3V3 pin is an output or a sense pin, and it does not replace the target board's schematic. Source: [DS5319 Rev 20 Table 5](#source-ds5319) and [RM0008 Rev 21 Table 9](#source-rm0008-boot).</sub>
</p>

## Learning goals
- [ ] Keep four pieces of evidence from the first loop: a build artifact, flash verification, a breakpoint in `main`, and a 1 Hz waveform on PC13
- [ ] Know the minimum C, digital, and analog you need before studying STM32
- [ ] Assemble a hardware kit you can use immediately, including price ranges
- [ ] Read the "4 weeks beginner / 6 weeks intermediate / 8 weeks project" roadmap and check yourself with the self-tests
- [ ] Choose among three styles: registers, the standard peripheral library (SPL), and HAL+LL+CubeMX
- [ ] Recognize the changes that slow early work down: switching boards, toolchains, libraries, and several peripherals at once

## How much background is enough

You do not need to finish an electronics curriculum before starting STM32. If you can read a pin table, calculate an LED series resistor, and use a pointer with a `uint32_t`, you can fill the remaining gaps while running experiments.

### 1. The "enough" bar for background

| Topic | Minimum (you must be able to do this) | Enough to know about | Sign you need to review |
| --- | --- | --- | --- |
| C | Pointers, arrays, structs, `typedef`, `enum`, bitwise ops `& \| ^ ~ << >>`, function pointers | Macros and conditional compilation, the meaning of `volatile` / `static` / `const` | `*(volatile uint32_t*)0x40021018` is a complete blank |
| Digital | High and low, AND/OR/NOT, rising and falling edges, the idea of push-pull and open-drain | Timing diagrams, setup and hold time, bus arbitration | You cannot say what "rising-edge trigger" means |
| Analog | Ohm's law, a divider, an LED series resistor, what a pull-up does | BJT/MOS switches, op-amp basics, RC filtering | You cannot compute the LED resistor R=(Vcc−Vf)/I |
| Computer organization | Binary and hex, bytes and addresses, what a register is | Interrupts, DMA, buses, cache | You do not see how a "register" relates to "memory" |
| English | You can read pin tables and parameter tables in a datasheet | You can read a whole chapter of the reference manual | You cannot even look up a Pin Name |

If one of those is missing, review that item. You do not need to finish a C or circuit textbook first.

### 2. Three ways to write the firmware

| Dimension | Registers (bare registers) | Standard peripheral library (SPL) | HAL + LL + CubeMX |
| --- | --- | --- | --- |
| Abstraction | Lowest: you write `GPIOA->ODR` directly | Middle: `GPIO_SetBits()` | Highest: `HAL_GPIO_WritePin()` |
| How hard to start | High (you have to live in the manual) | Medium | Low (the GUI generates it) |
| Amount of code | Little, but dense | Medium | More, but clearer |
| Portability | Poor (F1→F4 means edits) | Poor (ST has stopped updates) | Good (HAL is one API across families) |
| Resource use | Smallest | Small | A bit larger (you can trim it; LL is smaller) |
| Official maintenance | No SPL/HAL version dependency; the target reference manual defines the registers | **No longer maintained** | Still updated |
| Fits | Learning the mechanism, tight timing, tiny memory | Maintaining a version-locked old project | New projects, prototypes, and current ST examples |

**Suggested path: start with HAL+CubeMX → read the registers so the layer underneath makes sense → use LL where it actually matters.**

### 3. The three-stage roadmap

#### Stage 1: Beginner (4 weeks) — get the board running

| Week | Topic | You should have | Self-test |
| --- | --- | --- | --- |
| Week 1 | Environment, GPIO output, blink an LED | You can compile and flash; the LED blinks | What is the difference between push-pull and open-drain? |
| Week 2 | GPIO input, a button, debounce | A button controls the LED | Why does a button need debounce? How do you write it in software? |
| Week 3 | Interrupts, NVIC, EXTI | A button interrupt toggles the LED | What is the difference between preemption priority and subpriority? |
| Week 4 | Timer time base, PWM | A breathing LED | Where does `fCK_CNT = fCK_PSC/(PSC+1)` come from? |

<p align="center">
  <img src="../../assets/diagrams/sample-00-accept-gate.svg" width="820" alt="Three acceptance gates for the first program: build with 0 Error, something visible on the board, and every line explainable; a clean build alone does not pass">
  <br><sub>▲ Drawn for this book. All three gates in order, or it is not accepted. Gate 1 is the build: 0 Error, an artifact from STM32F103C8Tx_FLASH.ld, written to 0x08000000 by the flash tool. Gate 2 is the board: the PC13 LED completes one on/off cycle per second, 500 ms on plus 500 ms off. Gate 3 is the sentence: you can say why APB2ENR.IOPCEN is set before CRH is written, why CRH[23:20] = 0x2 means 2 MHz push-pull, and why toggling ODR13 changes the pin. A green build covers gate 1 only; it says nothing about BOOT0, a Dupont wire, or the 500 ms, and the four-gate ladder in the hands-on section adds flash, reset, and measurement. Source: [RM0008 Rev 21 chapter 9](#source-rm0008) and [DS5319 Rev 20 Table 5](#source-ds5319).</sub>
</p>

#### Stage 2: Intermediate (6 weeks) — open the usual buses and peripherals

| Week | Topic | You should have | Self-test |
| --- | --- | --- | --- |
| Week 5 | UART send and receive, printf redirect | Logs on the serial port | What baud-rate error can you tolerate? |
| Week 6 | UART interrupt + DMA + IDLE | Receive a frame of unknown length | What problem does the IDLE interrupt solve? |
| Week 7 | I2C, OLED | An OLED showing characters | How are addresses 0x3C and 0x78 related? |
| Week 8 | SPI, W25Q64 | Read and write the flash | How do you tell the four CPOL/CPHA modes apart? |
| Week 9 | ADC + DMA | Sample a voltage and display it | What happens during SAR successive approximation? |
| Week 10 | Watchdogs, low power | A node that wakes on a timer | What is the difference between IWDG and WWDG? |

#### Stage 3: A real project (8 weeks) — finish something whole

| Week | Topic | You should have | Self-test |
| --- | --- | --- | --- |
| Weeks 11–12 | Split the requirements, modules, a state machine | A block diagram and a task list | How do you turn a requirement into modules? |
| Weeks 13–14 | Sensor drivers + display + storage | A complete data-capture path | How do you recover a bus that has locked up? |
| Weeks 15–16 | Bring in FreeRTOS (tasks / queues / semaphores) | Tasks working together | When is an RTOS actually worth it? |
| Weeks 17–18 | Integration, fault handling, IAP update | Firmware you can hand over, plus notes | How does a bootloader jump to the app? |

### 4. Hardware shopping list

| Item | Suggested part | Price range (¥) | Required? | Notes |
| --- | --- | --- | --- | --- |
| Minimum board | BluePill STM32F103C8T6 | 15–30 | Required | The F1 labs in chapters 00–19 use this board |
| Next board | STM32F411 BlackPill / Nucleo-F411RE | 30–80 | Optional | Buy it when you study F4/F7, DSP, or the FPU |
| Debugger | ST-Link V2 (clone) | 15–40 | Required | SWD download and debug |
| Breadboard | 830-tie solderless breadboard | 8–20 | Required | You need it to wire circuits |
| Dupont wires | Male-to-male / male-to-female, 40 of each | 8–15 | Required | Use different colors for power, ground, and signals |
| USB-TTL | CH340 / CP2102 module | 8–20 | Required | Serial debug; watch the 3.3 V level |
| Sensor kit | 37-in-1 sensor modules | 40–80 | Optional | Buy modules when a lab needs them; the first blink does not |
| OLED | 0.96" SSD1306 I2C | 12–25 | Recommended | Used by the I2C lab in chapter 07 |
| Logic analyzer | 8-channel 24 MHz (clone) | 15–40 | Recommended | Shows GPIO, I2C, SPI, and UART timing |
| Multimeter | Entry-level digital meter | 30–80 | Recommended | Voltage and continuity |

> These are rough price ranges, excluding shipping; check current prices before buying. The low end of the table puts the **bare-minimum kit near 60 yuan** (BluePill + ST-Link + breadboard + Dupont wires). Adding serial, display, measurement, and lab modules brings it to roughly 200–300 yuan.

### 5. Changes that slow down the first week

| Do not | Why | Do this instead |
| --- | --- | --- |
| Start by reading a 1000-page reference manual | No context, so nothing sticks and nothing gets used | Run an example first, then look up the page you need |
| Study RTOS, bare metal, and a PC app at the same time | Attention splits, and none of them gets solid | Get the bare-metal peripherals firm, then add an RTOS |
| Copy code and never look at a register | When it breaks, you cannot inspect the state | The first time you use a peripheral, trace its key registers |
| Learn the basics on an F4 or H7 | The peripherals hide the mechanism | Build the foundation on F1, then move |
| Insist on "all registers" as a flex | Slow to write, easy to get wrong | HAL for most of it; LL or registers where it matters |
| Read only software state and never probe the bus | You cannot separate a configuration error from an on-wire timing error | Start with a logic analyzer for digital buses; use a scope for voltage quality and edges |
| Buy a high-end board for the first lab | The extra peripherals do not help the blink and add power and boot variables | Close the first loop on the BluePill used by this book |

<p align="center">
  <img src="../../assets/diagrams/sample-00-learn-loop.svg" width="820" alt="The learning loop in four steps: read the matching RM0008 section, write the smallest code, put it on the board, explain every line; skipping the manual stops at explanation">
  <br><sub>▲ Drawn for this book. Four steps, then repeat. Read the one register you need in RM0008 chapter 9; write the smallest code that touches it (set APB2ENR.IOPCEN, write 0x2 to CRH[23:20], toggle ODR13); flash 0x08000000 and watch PC13 with BOOT0 = 0; then explain why the order holds, why 0x2 is push-pull, and why 500 ms is a half period before moving to the next register. The lower half is the failure path: copy a project instead, and when nothing shows you can neither point at the line that owns a pin nor tell an unopened clock from an unwired pin. The figure shows that all four steps are required; it does not prove any particular project is written well, and it leaves the clock tree and the exception stack to other chapters. Source: [RM0008 Rev 21 chapter 9](#source-rm0008) and [DS5319 Rev 20 Table 5](#source-ds5319).</sub>
</p>

## Hardware and wiring

For the first blink, connect only the BluePill and ST-Link. The figure uses Micro-USB as the one primary supply, so the 3.3 V pin on a clone ST-Link stays disconnected. On some clones that pin is a supply output, not a voltage-sense input; do not parallel it with USB power.

<p align="center">
  <img src="../../assets/diagrams/first-lab-wiring.svg" width="820" alt="BluePill powered only from Micro-USB, with ST-Link connected to GND, SWDIO, SWCLK, and optional NRST while 3.3 V stays disconnected">
  <br><sub>▲ First wiring: keep one primary supply, confirm BOOT0=0 and common ground, then measure 3.3 V at the MCU. Leave USB-TTL for the UART chapter. This is a connection-boundary diagram, not a board photograph or a replacement for the clone's schematic (FA-029 · IG-002 · C-03/C-10/C-27/C-31).</sub>
</p>

| BluePill | ST-Link | Connect now? | Purpose |
| --- | --- | --- | --- |
| GND | GND | Yes | Common voltage reference |
| SWDIO (PA13) | SWDIO | Yes | Debug data |
| SWCLK (PA14) | SWCLK | Yes | Debug clock |
| NRST | RST | Optional | Enables connect under reset |
| 3V3 | 3.3V | **No** | The board already has Micro-USB power; do not parallel supplies |

> [!WARNING]
> Never connect 5 V to 3V3. Before power-up, confirm that there is one primary supply. After power-up, measure the board's 3.3 V rail before starting a debug session.

The physical layout is in [`assets/boards/bluepill-stm32f103c8t6.svg`](../../assets/boards/bluepill-stm32f103c8t6.svg). It is an author-drawn structure map, not a photograph. The repository does not currently contain a BluePill photograph whose exact model and redistribution license have both been verified.

## The first program you can accept or reject

Make the onboard LED (PC13, on when low) complete one on/off cycle every second. Running code is only the first check; the measured waveform must also be 1 Hz.

```c
/* main.c —— BluePill onboard LED (PC13) blinks at 1 Hz
 * Depends on: STM32F1 HAL, system clock 72MHz
 */
#include "stm32f1xx_hal.h"

#define LED_PIN   GPIO_PIN_13
#define LED_PORT  GPIOC

static void SystemClock_Config(void);   /* generated by CubeMX, or written by hand */

int main(void)
{
    HAL_Init();                 /* init HAL, SysTick, and interrupt priority grouping */
    SystemClock_Config();       /* HSE 8MHz -> PLL x9 -> 72MHz */

    __HAL_RCC_GPIOC_CLK_ENABLE();   /* critical: enable the GPIO clock first, or register writes do not land */

    GPIO_InitTypeDef gpio = {0};
    gpio.Pin   = LED_PIN;
    gpio.Mode  = GPIO_MODE_OUTPUT_PP;   /* push-pull output */
    gpio.Pull  = GPIO_NOPULL;
    gpio.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(LED_PORT, &gpio);

    while (1)
    {
        HAL_GPIO_TogglePin(LED_PORT, LED_PIN);  /* toggle the level */
        HAL_Delay(500);                         /* 500 ms, half a period */
    }
}

/* clock setup (the CubeMX-generated version is fine too) */
static void SystemClock_Config(void)
{
    RCC_OscInitTypeDef osc = {0};
    RCC_ClkInitTypeDef clk = {0};

    osc.OscillatorType = RCC_OSCILLATORTYPE_HSE;
    osc.HSEState       = RCC_HSE_ON;
    osc.HSEPredivValue = RCC_HSE_PREDIV_DIV1;
    osc.PLL.PLLState   = RCC_PLL_ON;
    osc.PLL.PLLSource  = RCC_PLLSOURCE_HSE;
    osc.PLL.PLLMUL     = RCC_PLL_MUL9;        /* 8MHz x 9 = 72MHz */
    HAL_RCC_OscConfig(&osc);

    clk.ClockType      = RCC_CLOCKTYPE_HCLK | RCC_CLOCKTYPE_SYSCLK |
                         RCC_CLOCKTYPE_PCLK1 | RCC_CLOCKTYPE_PCLK2;
    clk.SYSCLKSource   = RCC_SYSCLKSOURCE_PLLCLK;
    clk.AHBCLKDivider  = RCC_SYSCLK_DIV1;   /* AHB = 72MHz */
    clk.APB1CLKDivider = RCC_HCLK_DIV2;     /* APB1 = 36MHz (36MHz ceiling) */
    clk.APB2CLKDivider = RCC_HCLK_DIV1;     /* APB2 = 72MHz (72MHz ceiling) */
    HAL_RCC_ClockConfig(&clk, FLASH_LATENCY_2);  /* 72MHz needs 2 wait states */
}
```

The same thing in registers (so the layer underneath is visible):

```c
/* without HAL, the blink needs these four register operations */
RCC->APB2ENR |= RCC_APB2ENR_IOPCEN;        /* enable the GPIOC clock */
GPIOC->CRH &= ~(0xF << 20);                 /* clear the PC13 configuration bits */
GPIOC->CRH |=  (0x2 << 20);                 /* PC13 general-purpose push-pull output, 2MHz */
GPIOC->ODR ^= GPIO_ODR_ODR13;               /* toggle PC13 */
```

The full project is in [`examples/gpio-blink/`](../../examples/gpio-blink/).

## Hands-on labs

1. **Lab 1 (environment check):** Blink PC13 at 1 Hz with the code above. The onboard LED should complete one on/off cycle every second.
2. **Lab 2 (change a parameter):** Change `HAL_Delay(500)` to 100 and watch the blink speed up. Probe PC13 with a logic analyzer and confirm the frequency is about 5 Hz.
3. **Lab 3 (registers beside HAL):** Blink the same way with registers. Compare it with the HAL version and write down what the bits in `CRH` and `ODR` mean.

<p align="center">
  <img src="../../assets/diagrams/first-success-gates.svg" width="820" alt="Four acceptance gates for the first blink: build, flash, reset, and measurement, each with the next action after failure">
  <br><sub>▲ Acceptance gates: confirm the ELF/AXF, verification at 0x08000000, entry to main with BOOT0=0, and finally a 1 s period on PC13. An illuminated LED proves only one level at one moment; it does not prove the build artifact, reset path, or frequency (FA-002 · IG-008 · C-03/C-10/C-27/C-31).</sub>
</p>

### 6. Do not begin debugging by searching the error text

| Order | Action | Notes |
| --- | --- | --- |
| 1 | Look at the symptom and measure the waveform | Confirm the hardware with a logic analyzer or a multimeter first |
| 2 | Check pin and parameters in the datasheet | Pin definitions and electrical limits live in the DS |
| 3 | Check the peripheral chapter in the reference manual | Registers and timing live in the RM |
| 4 | Search the official examples | Examples/ inside the CubeF1 package |
| 5 | Search the error text | Keywords plus the part number |
| 6 | Ask | Attach a minimal repro, the symptom, and what you already tried |

> When asking for help, state **what you did, what you expected, and what actually happened**, and attach a project small enough to reproduce.

### 7. Learning resources

| Kind | Name | What it is for |
| --- | --- | --- |
| Datasheet | DS5319 (F103C8) | Pins, package, electrical parameters |
| Reference manual | RM0008 | Registers, peripherals, clocks |
| Programming manual | PM0056 (Cortex-M3) | Core, NVIC, instructions |
| Official examples | STM32CubeF1 | A standard example for each peripheral |
| Tools | STM32CubeMX / CubeProgrammer | Generate a project / flash it |
| Debug | ST-Link + logic analyzer | Download and debug / capture timing |
| Community | ST Community, electronics forums | The odd failures |

### 8. FAQ

| Question | Short answer |
| --- | --- |
| If I use HAL, will I "never learn the bottom"? | No. After a HAL call, read the matching register. |
| Do I have to buy an oscilloscope? | A logic analyzer can cover early GPIO, UART, I2C, and SPI timing. Voltage quality and edge shape still require a scope. |
| Study F1 or F4? | This book starts on F103. Move to F4 when the project needs an FPU, a faster core, or more SRAM. |
| What if I cannot read the English manual? | Start with the figures and the register tables, and pair them with a Chinese tutorial. |
| Do I need to be able to draw a PCB? | Use a ready-made board to start. You do not. |

## Related resources

- Official manuals: STM32F103C8 datasheet **DS5319**; reference manual **RM0008** (GPIO chapter 9, RCC chapter 8)
- Next: [01 Setting Up the Development Environment](01-dev-environment.md)
- Board drawing: [`assets/boards/bluepill-stm32f103c8t6.svg`](../../assets/boards/bluepill-stm32f103c8t6.svg)
- Image sources and licenses: [`assets/README.md`](../../assets/README.md)

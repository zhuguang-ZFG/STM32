# 00 How to Learn STM32
> 中文：[如何学习 STM32](../00-如何学习STM32.md)

> For complete beginners: fill in the minimum background, gather the hardware, pick a development style, then walk the three-stage roadmap at a steady pace.

<p align="center">
  <img src="../../assets/animations/toolchain-flow.svg" width="760" alt="Toolchain data flow from writing code to flashing and running">
  <br><sub>▲ Animation: the full data path of compile → link → flash → run (vector drawing by the author)</sub>
</p>

<!-- video:ch00 -->
<p align="center">
  <img src="../../assets/video/ch00-learn.gif" width="640" alt="Chapter 00 lecture slides">
  <br><sub>▲ Lecture slides for this chapter: a program-generated GIF (tools/gen_videos.py, reproducible, not a live shot). The narration matches the five frames one to one.</sub>
</p>

**Narration (read along with the frames, about one minute)**

1. Pin the path down first: four weeks to get a foundation, six weeks to chew through peripherals, eight weeks to build something you can show someone else.
2. Do not skip ahead: environment, clocks, GPIO, and only then the UART and a project. Skipping is how people trip on the clock.
3. A BluePill is enough to start. The three manuals are the datasheet, the reference manual, and the programming manual.
4. Do not copy a whole example pack on day one. First make one LED blink at a frequency you calculated yourself.
5. Close the book: with BOOT0 pulled low, where do you boot? Which layer is the difference between HAL and registers?
<!-- /video:ch00 -->


## 📌 Learning goals
- [ ] Know the minimum C, digital, and analog you need before studying STM32
- [ ] Assemble a hardware kit you can use immediately, including price ranges
- [ ] Read the "4 weeks beginner / 6 weeks intermediate / 8 weeks project" roadmap and check yourself with the self-tests
- [ ] Choose among three styles: registers, the standard peripheral library (SPL), and HAL+LL+CubeMX
- [ ] Remember the "do not do this" list, so the usual early dead ends do not talk you out of the work

## 🧠 Core ideas

**Lead with the conclusion: getting started with STM32 does not mean finishing an entire electronics degree. You need "enough" background plus the right path.**

### 1. The "enough" bar for background

| Topic | Minimum (you must be able to do this) | Enough to know about | Sign you need to review |
| --- | --- | --- | --- |
| C | Pointers, arrays, structs, `typedef`, `enum`, bitwise ops `& \| ^ ~ << >>`, function pointers | Macros and conditional compilation, the meaning of `volatile` / `static` / `const` | `*(volatile uint32_t*)0x40021018` is a complete blank |
| Digital | High and low, AND/OR/NOT, rising and falling edges, the idea of push-pull and open-drain | Timing diagrams, setup and hold time, bus arbitration | You cannot say what "rising-edge trigger" means |
| Analog | Ohm's law, a divider, an LED series resistor, what a pull-up does | BJT/MOS switches, op-amp basics, RC filtering | You cannot compute the LED resistor R=(Vcc−Vf)/I |
| Computer organization | Binary and hex, bytes and addresses, what a register is | Interrupts, DMA, buses, cache | You do not see how a "register" relates to "memory" |
| English | You can read pin tables and parameter tables in a datasheet | You can read a whole chapter of the reference manual | You cannot even look up a Pin Name |

> One-sentence bar: **if you can use a pointer on a `uint32_t`, compute an LED series resistor, and read a pin table, you can start.**

### 2. Three ways to write the firmware

| Dimension | Registers (bare registers) | Standard peripheral library (SPL) | HAL + LL + CubeMX |
| --- | --- | --- | --- |
| Abstraction | Lowest: you write `GPIOA->ODR` directly | Middle: `GPIO_SetBits()` | Highest: `HAL_GPIO_WritePin()` |
| How hard to start | High (you have to live in the manual) | Medium | Low (the GUI generates it) |
| Amount of code | Little, but dense | Medium | More, but clearer |
| Portability | Poor (F1→F4 means edits) | Poor (ST has stopped updates) | Good (HAL is one API across families) |
| Resource use | Smallest | Small | A bit larger (you can trim it; LL is smaller) |
| Official maintenance | Usable forever | **No longer maintained** | Still updated |
| Fits | Learning the mechanism, tight timing, tiny memory | Keeping old projects alive | New products, fast prototypes, what most jobs use |

**Suggested path: start with HAL+CubeMX → read the registers so the layer underneath makes sense → use LL where it actually matters.**

### 3. The three-stage roadmap

#### Stage 1: Beginner (4 weeks) — get the board running

| Week | Topic | You should have | Self-test |
| --- | --- | --- | --- |
| Week 1 | Environment, GPIO output, blink an LED | You can compile and flash; the LED blinks | What is the difference between push-pull and open-drain? |
| Week 2 | GPIO input, a button, debounce | A button controls the LED | Why does a button need debounce? How do you write it in software? |
| Week 3 | Interrupts, NVIC, EXTI | A button interrupt toggles the LED | What is the difference between preemption priority and subpriority? |
| Week 4 | Timer time base, PWM | A breathing LED | Where does `fCK_CNT = fCK_PSC/(PSC+1)` come from? |

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
| Minimum board | BluePill STM32F103C8T6 | 15–30 | ✅ | Best first board; the most material exists for it |
| Next board | STM32F411 BlackPill / Nucleo-F411RE | 30–80 | Optional | Buy it when you study F4/F7, DSP, or the FPU |
| Debugger | ST-Link V2 (clone) | 15–40 | ✅ | SWD download and debug |
| Breadboard | 830-tie solderless breadboard | 8–20 | ✅ | You need it to wire circuits |
| Dupont wires | Male-to-male / male-to-female, 40 of each | 8–15 | ✅ | Color-coded ones are worth it |
| USB-TTL | CH340 / CP2102 module | 8–20 | ✅ | Serial debug; watch the 3.3 V level |
| Sensor kit | 37-in-1 sensor modules | 40–80 | ✅ | Button, LED, OLED, DHT11, and so on |
| OLED | 0.96" SSD1306 I2C | 12–25 | Recommended | The best first I2C exercise |
| Logic analyzer | 8-channel 24 MHz (clone) | 15–40 | Recommended | The tool that shows I2C/SPI/UART timing |
| Multimeter | Entry-level digital meter | 30–80 | Recommended | Voltage and continuity |

> Budget: **bare-minimum start ≈ 60 yuan** (BluePill + ST-Link + breadboard + Dupont wires); **full kit ≈ 200–300 yuan**.

### 5. What not to do (the list that makes people quit)

| ❌ Do not | Why | Do this instead |
| --- | --- | --- |
| Start by reading a 1000-page reference manual | No context, so nothing sticks and nothing gets used | Run an example first, then look up the page you need |
| Study RTOS, bare metal, and a PC app at the same time | Attention splits, and none of them gets solid | Get the bare-metal peripherals firm, then add an RTOS |
| Copy code and never look at a register | When it breaks, you cannot look | For every HAL call, look up the matching register at least once |
| Learn the basics on an F4 or H7 | The peripherals hide the mechanism | Build the foundation on F1, then move |
| Insist on "all registers" as a flex | Slow to write, easy to get wrong | HAL for most of it; LL or registers where it matters |
| Debug a bus with no scope and no logic analyzer | If you cannot see the timing, you are guessing | At least keep a logic analyzer |
| Buy the most expensive board first | It is likely to sit unused | Run a 30-yuan BluePill first |

## 🛠️ Hardware and wiring

At the start, all you wire is "minimum board + ST-Link + USB-TTL":

| Board pin | ST-Link pin | USB-TTL | Notes |
| --- | --- | --- | --- |
| 3V3 | 3.3V | 3.3V | Power (do not put 5 V on the 3V3 pin) |
| GND | GND | GND | Common ground is required |
| SWDIO (PA13) | SWDIO | — | Debug data |
| SWCLK (PA14) | SWCLK | — | Debug clock |
| NRST | RST | — | Optional; connecting it is more reliable |
| PA9 (TX) | — | RX | Cross them: board TX → module RX |
| PA10 (RX) | — | TX | Board RX → module TX |

> ⚠️ The BluePill 3V3 pin cannot feed an ST-Link well. Power the board from its Micro-USB on its own.

The physical layout is in [`assets/boards/bluepill-stm32f103c8t6.svg`](../../assets/boards/bluepill-stm32f103c8t6.svg) (a structural drawing by the author, not a photograph).

## 💻 Code

The "first program": blink the onboard LED (PC13, on when low) once a second. This is the standard check that the environment is actually set up.

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
/* without HAL, three core lines light the LED */
RCC->APB2ENR |= RCC_APB2ENR_IOPCEN;        /* enable the GPIOC clock */
GPIOC->CRH &= ~(0xF << 20);                 /* clear the PC13 configuration bits */
GPIOC->CRH |=  (0x2 << 20);                 /* PC13 general-purpose push-pull output, 2MHz */
GPIOC->ODR ^= GPIO_ODR_ODR13;               /* toggle PC13 */
```

The full project is in [`examples/gpio-blink/`](../../examples/gpio-blink/).

## ⚠️ Pitfalls and troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| Compile error: cannot find `stm32f1xx_hal.h` | The include path was not added | Add HAL/Inc to the project Include Paths |
| Download says "No target connected" | SWD wires swapped, or the board has no power | Check SWDIO/SWCLK/GND, and power the board on its own |
| The program is flashed and nothing happens | The peripheral clock was never enabled | Add `__HAL_RCC_GPIOx_CLK_ENABLE()` |
| You start by reading a 1000-page reference manual | The method is wrong | Run an example first, then look up the page you need |
| You study RTOS, bare metal, and a PC app at once | Too much at once, none of it digested | Get the bare-metal peripherals firm, then add an RTOS |
| You only copy code and never understand the registers | The foundation is hollow | For every HAL call, look up the matching register at least once |
| The LED stays on or stays off and never blinks | The delay is a busy wait, or SysTick was never started | Confirm `HAL_Init()` has been called |

## 🧪 Hands-on labs

1. **Lab 1 (environment check):** Blink PC13 at 1 Hz with the code above. What you should see: the onboard blue LED turns on and off once a second.
2. **Lab 2 (change a parameter):** Change `HAL_Delay(500)` to 100 and watch the blink speed up. Probe PC13 with a logic analyzer and confirm the frequency is about 5 Hz.
3. **Lab 3 (registers beside HAL):** Blink the same way with registers. Compare it with the HAL version and write down what the bits in `CRH` and `ODR` mean.

### 6. When you get stuck (the right order to look things up)

| Order | Action | Notes |
| --- | --- | --- |
| 1 | Look at the symptom and measure the waveform | Confirm the hardware with a logic analyzer or a multimeter first |
| 2 | Check pin and parameters in the datasheet | Pin definitions and electrical limits live in the DS |
| 3 | Check the peripheral chapter in the reference manual | Registers and timing live in the RM |
| 4 | Search the official examples | Examples/ inside the CubeF1 package |
| 5 | Search the error text | Keywords plus the part number |
| 6 | Ask | Attach a minimal repro, the symptom, and what you already tried |

> Three things every question needs: **what you did, what you expected, what actually happened**, plus a project small enough to reproduce.

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
| Do I have to buy an oscilloscope? | A logic analyzer is enough to start, and the value is better. |
| Study F1 or F4? | F1 from zero. F4 if you want performance or a job that asks for it. |
| What if I cannot read the English manual? | Start with the figures and the register tables, and pair them with a Chinese tutorial. |
| Do I need to be able to draw a PCB? | Use a ready-made board to start. You do not. |

## 🔗 Related resources

- Official manuals: STM32F103C8 datasheet **DS5319**; reference manual **RM0008** (GPIO chapter 9, RCC chapter 8)
- Next: [01 Setting Up the Development Environment](01-dev-environment.md)
- Board drawing: [`assets/boards/bluepill-stm32f103c8t6.svg`](../../assets/boards/bluepill-stm32f103c8t6.svg)
- Hardware and documents: the Nucleo product pages on ST's website (the official boards in the same class as a BluePill)
- Disclaimer: every illustration in this repo is a vector drawing or a program-generated animation by the author, not a manufacturer's photograph.

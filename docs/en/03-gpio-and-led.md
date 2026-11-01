# 03 GPIO and LEDs
> 中文：[GPIO 与 LED](../03-GPIO与LED.md)

> GPIO is the most basic peripheral. LEDs and buttons use it directly, and the UART, the timers, and the other peripherals use its pins to get signals in and out of the chip.

<p align="center">
  <img src="../../assets/animations/gpio-blink.svg" width="760" alt="Animation of a GPIO push-pull output driving an LED">
  <br><sub>▲ Animation: a GPIO push-pull output lighting an LED (level, current, and waveform together; vector drawing by the author)</sub>
</p>

<!-- video:ch03 -->
<p align="center">
  <video width="640" controls poster="../../assets/video/ch03-gpio.png">
    <source src="../../assets/video/ch03-gpio.mp4" type="video/mp4">
  </video>
  <br><sub>▲ Chapter video with Chinese voice-over (2.4 min). <a href="../../assets/video/ch03-gpio.mp4">MP4</a> · <a href="../../assets/video/ch03-gpio.srt">subtitles</a></sub>
</p>

<details>
<summary>Narration script (Chinese, same text as the subtitles)</summary>

1. GPIO 看起来就是高低电平，真正要选的是模式。先分清输入还是输出，推挽还是开漏，要不要上下拉。模式选错，电平会和你想的相反。
2. BluePill 的板载灯在 PC13，接法是低电平才亮。你写 1，灯反而是灭的。别拿共阴外接灯的习惯去套这颗板载灯，否则你会以为端口坏了。
3. 按键另一端接 GND 时，引脚要上拉。没按下是高，按下被拉成低。再外加一个下拉，电平会和上拉打架，读到的就飘着。
4. 这一帧是仓库里的点灯动画，不是实拍。推挽输出能主动拉高也能主动拉低。开漏则要靠上拉，适合和别人共享一根线，比如 I2C。
5. 在 F1 上把外设换到另一组脚，要先打开 AFIO 的时钟，再写重映射。只改模式、不开 AFIO，示波器上会一直安静。这是这章最容易漏的一步。
6. 不是每只脚都能碰 5 伏。数据手册里标了 FT 的才比较容忍。普通脚直接接 5 伏模块，轻则电平不对，重则把片打伤。先翻表，再接线。
7. 引脚锁定用来防止后面的代码把手脚改掉。顺序是写 1、写 0、再写 1，然后读一次才真正锁上。少读那一下，你以为锁了，其实没有。
8. 口诀：F1 重映射先开 AFIO；5 伏只认 FT；锁定是 1、0、1 再读。三件都是手上的动作，不是概念题。
9. 实验让 PC13 以 1 赫兹翻转。眼睛只能看出大概，频率要用你算过的延时或定时器来对。对上了，这章才算过关。
10. 合上书，三问。PC13 写高还是写低才会亮？按键接 GND 该上拉还是下拉？F1 重映射之前必须先开哪个时钟？

</details>
<!-- /video:ch03 -->

## Learning goals

Before this chapter: know what voltage, current, and resistance mean (if not, read "Zero-background primer" in chapter 00 first), and be able to download a program to the board as in chapter 01.

- [ ] Name the four jobs a pin can do: input, output, alternate function, analog
- [ ] Tell push-pull from open-drain, and say why open-drain needs a pull-up resistor
- [ ] Compute an LED series resistor with R = (Vcc − Vf) / I
- [ ] Drive PC13 both with HAL and with registers, and say why BSRR is safer than read-modify-write
- [ ] Read a button circuit: why it needs a pull-up, and why it needs debouncing
- [ ] Avoid three common traps: the port clock left off, PC13 used as a current source, and the SWD pins turned into plain IO

## Core ideas

**In one sentence: GPIO (General Purpose Input/Output) is a pin whose job the program decides. Before using one, settle three things: input or output, push-pull or open-drain, and whether it needs a pull-up or pull-down.**

### An analogy first

Think of a pin as a water outlet on a wall. Behind the wall run two pipes: one to a water tower (3.3 V) and one to the drain (GND).

- **Push-pull output**: there are two valves behind the outlet. Write 1 and the valve to the tower opens; water flows out and the outlet is high. Write 0 and the valve to the drain opens; water flows in and the outlet is low.
- **Open-drain output**: only the valve to the drain exists. It can pull the outlet low but cannot make it high; for a high level you add a thin pipe outside (a pull-up resistor) back to the tower.
- **Input**: both valves stay shut and the outlet only "reads the water level". A high enough voltage reads as 1, a low enough one as 0.

The analogy stops here. The real "valves" are two MOS transistors inside the chip, and the current through them has a limit; go past it and the chip is damaged. Section 3 gives the numbers.

### 1. Four jobs for one pin

| Job | Who decides the level | Example |
| --- | --- | --- |
| Input | The outside circuit; the program reads it | A button |
| Output | The program writes 0 or 1 | An LED |
| Alternate function (AF) | An on-chip peripheral takes over the pin; the program no longer writes it directly | UART TX, a timer's PWM |
| Analog | The digital circuitry is switched off and the voltage goes straight to the ADC | A potentiometer, a sensor voltage |

Split further, these are the usual 8 modes. The table lists them by HAL macro:

| Mode (HAL macro) | Direction | Output stage | Pull | Typical use |
| --- | --- | --- | --- | --- |
| `GPIO_MODE_INPUT` + `GPIO_NOPULL` | Input | — | Floating | Something else already pulls the pin, or another chip's digital output drives it |
| `GPIO_MODE_INPUT` + `GPIO_PULLUP` | Input | — | Pull-up | Button to GND (reads low when pressed) |
| `GPIO_MODE_INPUT` + `GPIO_PULLDOWN` | Input | — | Pull-down | Button to VCC (reads high when pressed) |
| `GPIO_MODE_ANALOG` | Input | Off | — | ADC sampling; also the lowest-power setting for an unused pin |
| `GPIO_MODE_OUTPUT_PP` | Output | Push-pull | — | LEDs, ordinary control signals |
| `GPIO_MODE_OUTPUT_OD` | Output | Open-drain | — | Bit-banged I2C, a line shared with other devices |
| `GPIO_MODE_AF_PP` | Alternate | Push-pull | — | UART TX, SPI, PWM output |
| `GPIO_MODE_AF_OD` | Alternate | Open-drain | — | Hardware I2C, SMBus |

"Floating" means nothing is connected to the pin, so nearby noise decides its level and the reading jumps around. A pull-up or pull-down resistor gives it a default: a pull-up gently pulls it toward 3.3 V, a pull-down toward GND. The F1 on-chip pull resistors are 30–50 kΩ, typically 40 kΩ. That is a weak pull, and any real signal overrides it.

> [!TIP]
> F1 HAL also has `GPIO_MODE_AF_INPUT`, which behaves as an input. On F4, F7, and later families an alternate function also needs its number in the `Alternate` field, on top of `GPIO_MODE_AF_PP` / `GPIO_MODE_AF_OD`. In register-level F1 code, the same ODR bit picks pull-up or pull-down for an input: ODR = 1 is pull-up, ODR = 0 is pull-down.

### 2. Push-pull versus open-drain

| Comparison | Push-pull | Open-drain |
| --- | --- | --- |
| Where a high comes from | The on-chip PMOS connects the pin to VDD | Both transistors are off; an external pull-up provides the high |
| Where a low comes from | The on-chip NMOS connects the pin to GND | The on-chip NMOS connects the pin to GND |
| Can several pins be tied together? | No; one high and one low is a short circuit | Yes; any one pulling low makes the line low (wired-AND) |
| Typical use | LEDs, ordinary digital output | I2C, level shifting, a line shared by several devices |

Why I2C must be open-drain: several devices hang on one SDA line. If they were push-pull, one could drive high while another drives low, and current would flow straight from one pin into the other. At best the level is wrong; at worst a pin burns. Open-drain can only "pull low" or "let go", so the worst case is a line held low, never a short.

### 3. What counts as 1, and how much current a pin may carry

The chip decides 1 and 0 with two thresholds, with a "not guaranteed" band in between. These are STM32F103 numbers from datasheet DS5319 Rev 20 Tables 36, 37, and 7, at a 3.3 V supply:

| Item | Condition | Value | In plain words |
| --- | --- | --- | --- |
| Input low VIL | Production-tested | ≤ 0.35 × VDD ≈ 1.15 V | Below this it always reads 0 |
| Input high VIH | Production-tested | ≥ 0.65 × VDD ≈ 2.15 V | Above this it always reads 1 |
| Input hysteresis | Standard IO | About 200 mV | A Schmitt trigger, so a slow edge does not chatter |
| Output low VOL | Sinking 8 mA per pin | ≤ 0.4 V | Under load, low is not exactly 0 V |
| Output high VOH | Sourcing 8 mA per pin | ≥ VDD − 0.4 V ≈ 2.9 V | More current, lower high level |
| Output low VOL | Sinking 20 mA per pin | ≤ 1.3 V | At this current the level is clearly worse |
| One pin | Absolute maximum rating | ±25 mA | Past this the pin may be damaged; not an operating point |
| Total current into all VDD pins | Absolute maximum rating | 150 mA | Every pin's output current plus the chip's own supply current |

An absolute maximum rating is the "may break past here" line; a normal design stays well below it. An indicator LED is bright enough at 5–10 mA. PC13, PC14, and PC15 can do much less than this table says. They are the most important exception in this chapter, and the details are in "Principle and scope" later.

Output speed is a separate setting. F1 outputs have three speeds, 2 MHz, 10 MHz, and 50 MHz. The setting controls how steep the edge is, not how fast the pin can toggle. A steeper edge brings more interference and overshoot. LEDs and buttons need only 2 MHz. F4 and later families call the steps Low / Medium / High / Very High.

### 4. Lighting an LED: compute the series resistor first

Once an LED conducts, the voltage across it stays nearly fixed; this is the forward voltage Vf. The supply minus Vf is what is left across the series resistor, so the resistor sets the current:

```text
R = (Vcc − Vf) / I
```

| Parameter | Typical value | Notes |
| --- | --- | --- |
| Vcc | 3.3 V | The pin voltage when it outputs high |
| Vf (red, yellow, yellow-green) | 1.8–2.2 V | Check the datasheet of the LED in your hand |
| Vf (blue, white, true green) | 2.8–3.2 V | Close to 3.3 V, so the current is very sensitive to Vf and the LED may look dim |
| I (target) | 5–10 mA | Enough for an ordinary indicator |

A worked example: a yellow LED, Vf taken as 2.1 V, at 5 mA. R = (3.3 − 2.1) / 0.005 = 240 Ω. If that exact value is not available, pick a nearby standard value on the larger side; the current drops slightly and the LED is a little dimmer, but it is safer.

Without a resistor, an LED on a pin is limited only by the pin's internal resistance, and the current easily passes the 25 mA in the previous section.

### 5. The registers behind a pin (F1)

A register is a 32-bit storage cell at a fixed address inside the chip. Write a value into it and the hardware acts on it; read it and you see the hardware state. Each GPIO port (GPIOA, GPIOB, ...) has its own set:

| Register | Role |
| --- | --- |
| CRL / CRH | Configure the low 8 / high 8 pins. Each pin takes 4 bits: two MODE bits pick input or an output speed, two CNF bits pick the exact mode |
| IDR | Input data: read it to see the actual pin level |
| ODR | Output data: write it to set the output level; for an input it picks pull-up or pull-down |
| BSRR | Bit set/reset: a 1 in the low 16 bits sets that pin high, a 1 in the high 16 bits clears it, and bits written 0 are left alone |
| BRR | Reset only (F1 has it; F4 does not, and uses the high half of BSRR) |
| LCKR | Locks the configuration; once locked it cannot change until reset |

Why BSRR is preferred: `GPIOC->ODR |= (1 << 13);` looks like one statement but is three steps: read ODR, OR in the bit, write it back. If an interrupt arrives between the read and the write and changes another pin on the same port, the write-back overwrites the interrupt's change. A BSRR write is a single write that touches only the bits written as 1, so there is no such gap.

### 6. Buttons: pull-ups and debouncing

| Wiring | Released | Pressed | Edge at the press |
| --- | --- | --- | --- |
| Pull-up, other side of the button to GND | High | Low | Falling |
| Pull-down, other side of the button to VCC | Low | High | Rising |

The metal contacts of a mechanical button bounce for a few milliseconds when they meet, so the program may see several presses and releases. Debouncing filters out that bounce:

| Debounce | Notes |
| --- | --- |
| Software delay | After a change, wait 10–20 ms and read again; accept only if both agree (a rule of thumb, not a number from ST's manuals) |
| Timer scan | Sample every few milliseconds and accept after several equal samples; the main loop never stalls |
| RC filter | Add a resistor and a 0.1 µF capacitor in hardware to smooth the spikes |
| Schmitt trigger | Shapes the signal in hardware; an STM32 digital input already has one stage |

### 7. Remap, 5 V tolerance, and the lock

| Family | How you change the function | What has to happen first |
| --- | --- | --- |
| F1 | `AFIO->MAPR` remaps a whole group (USART1 from PA9/PA10 to PB6/PB7, for example) | `__HAL_RCC_AFIO_CLK_ENABLE()` first, or the MAPR write has no effect |
| F4 | `GPIOx->AFR` gets the AF number for that pin | Set the mode to alternate first |

FT stands for five-volt tolerant, and the datasheet pin table marks it. On STM32F103, PA9 and PA10 are marked FT and PA0 is not. A pin without FT is damaged by a direct 5 V signal. An FT pin that must withstand more than VDD + 0.3 V also needs its on-chip pull-up and pull-down turned off.

The lock stops later code from changing a pin's configuration by mistake. The code is in "Code" and the full sequence is in "Timing and state".

Motto: **on F1, enable AFIO before you remap. 5 V only if the pin is FT. The lock is 1, 0, 1, then a read.**

### 8. Bit-banding: change one bit at a time

Cortex-M3 and Cortex-M4 cores have a feature called bit-banding. In the lowest 1 MB of the SRAM region and of the peripheral region, every bit also has its own 32-bit "alias" address. Writing 1 or 0 to the alias changes only that bit, and the hardware makes the change indivisible.

```text
peripheral alias = 0x42000000 + (peripheral address − 0x40000000) × 32 + bit × 4
SRAM alias       = 0x22000000 + (SRAM address − 0x20000000) × 32 + bit × 4
```

Every STM32F103 peripheral sits inside the 1 MB that starts at 0x40000000, so GPIO can use bit-banding. The Cortex-M0/M0+ families F0, G0, and L0 and the Cortex-M7 families F7 and H7 have no bit-banding; use BSRR there.

### 9. Which mode each common peripheral pin needs (F1)

| Peripheral pin | Mode |
| --- | --- |
| LED and other plain outputs | General-purpose push-pull output |
| Button | Input with pull-up or pull-down |
| UART TX | Alternate push-pull |
| UART RX | Input floating or input pull-up |
| I2C SCL / SDA | Alternate open-drain |
| SPI SCK / MOSI (master) | Alternate push-pull |
| SPI MISO (master) | Input floating or input pull-up |
| Timer PWM output | Alternate push-pull |
| Timer input capture | Input floating |
| ADC channel | Analog input |

This table follows [RM0008](#source-rm0008) section 9.1.11, Tables 22–27.

### 10. Driving bigger loads

| Device | How you drive it | Watch out |
| --- | --- | --- |
| Single-color indicator LED | GPIO directly, with a series resistor | 5–10 mA, well away from 25 mA |
| High-brightness or high-power LED, relay, motor | A transistor or MOSFET | The GPIO drives only the base or gate; the large current comes from an external supply |
| Seven-segment display | Digit select plus segment select; a 74HC595 shift register is optional | Several digits are lit in turn (multiplexing) |
| RGB LED | Three PWM channels | Mix colors by changing the three duty cycles |

## Hardware and wiring

| Board | Peripheral | Pin | Notes |
| --- | --- | --- | --- |
| BluePill | Onboard LED | PC13 | **Common-anode wiring; lights when the pin is low** |
| BluePill | External LED | PA0 | 270 Ω in series; lights when the pin is high |
| BluePill | Button | PA1 | The other side to GND; internal pull-up |

```text
External LED (lights on 1): PA0 ──[270 Ω]──▶|── GND     anode toward PA0, cathode to ground
Onboard LED (lights on 0):  3.3 V ──[resistor]──▶|── PC13   anode at 3.3 V, PC13 sinks the current
Button (reads 0 pressed):   PA1 ──[button]── GND         PA1 internal pull-up, reads 1 when released
```

The two LEDs have opposite logic: the external one is wired common-cathode and lights when the pin is high; the onboard one is common-anode and lights when the pin is low.

## Code

This program lets the button control the onboard LED: hold PA1 and the PC13 LED lights; release it and the LED goes dark.

```c
/* gpio_blink.c —— GPIO output blinks an LED and reads a button (HAL) */
#include "stm32f1xx_hal.h"

#define LED_PIN    GPIO_PIN_13
#define LED_PORT   GPIOC
#define KEY_PIN    GPIO_PIN_1
#define KEY_PORT   GPIOA

void SystemClock_Config(void);

static void gpio_init(void)
{
    GPIO_InitTypeDef io = {0};

    __HAL_RCC_GPIOC_CLK_ENABLE();
    __HAL_RCC_GPIOA_CLK_ENABLE();

    /* PC13 push-pull output (onboard LED, lights when low) */
    io.Pin   = LED_PIN;
    io.Mode  = GPIO_MODE_OUTPUT_PP;
    io.Pull  = GPIO_NOPULL;
    io.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(LED_PORT, &io);

    /* PA1 input, internal pull-up (button to ground reads low) */
    io.Pin  = KEY_PIN;
    io.Mode = GPIO_MODE_INPUT;
    io.Pull = GPIO_PULLUP;
    HAL_GPIO_Init(KEY_PORT, &io);
}

int main(void)
{
    HAL_Init();
    SystemClock_Config();
    gpio_init();

    while (1)
    {
        /* while the button is pressed (low), light the LED */
        GPIO_PinState key = HAL_GPIO_ReadPin(KEY_PORT, KEY_PIN);
        HAL_GPIO_WritePin(LED_PORT, LED_PIN,
                          (key == GPIO_PIN_RESET) ? GPIO_PIN_RESET : GPIO_PIN_SET);
    }
}
```

Piece by piece:

- `__HAL_RCC_GPIOx_CLK_ENABLE()` gives the port its clock first. To save power, a peripheral has no clock after power-up, and configuration written without a clock does not take effect.
- `GPIO_SPEED_FREQ_LOW` is the 2 MHz step. PC13 may not go above 2 MHz anyway, and an LED does not need more.
- `SystemClock_Config()` is generated by STM32CubeMX and sets up the system clock; see chapter 02.
- A button read of `GPIO_PIN_RESET` (low) means pressed, so the program writes low to PC13 and the onboard LED lights.

Three ways to do the same thing (light PC13):

```c
/* 1) HAL function */
HAL_GPIO_WritePin(GPIOC, GPIO_PIN_13, GPIO_PIN_RESET);   /* low lights the LED */

/* 2) one BSRR write (preferred; no read-modify-write gap) */
GPIOC->BSRR = GPIO_BSRR_BR13;   /* reset PC13 (BR = bit reset) */
GPIOC->BSRR = GPIO_BSRR_BS13;   /* set PC13 (BS = bit set)   */

/* 3) ODR read-modify-write (simple, but an interrupt can land in the middle) */
GPIOC->ODR &= ~GPIO_ODR_ODR13;  /* clear the bit */
```

Bit-banding (Cortex-M3/M4 only; F1 can use it):

```c
/* bit-band alias: map bit 13 of peripheral address 0x4001100C (GPIOC_ODR) to an alias address */
#define BITBAND_PERIPH(addr, bit) \
    (*(volatile uint32_t *)(0x42000000UL + ((addr) - 0x40000000UL) * 32 + (bit) * 4))

#define PC13_OUT  BITBAND_PERIPH(0x4001100CUL, 13)   /* GPIOC->ODR bit13 */
PC13_OUT = 0;   /* write 0 or 1 directly; only this bit changes */
```

Locking the configuration of PA5. The read at the end is part of the lock sequence and cannot be skipped:

```c
GPIOA->LCKR = GPIO_LCKR_LCKK | GPIO_LCKR_LCK5;   /* write 1 */
GPIOA->LCKR = GPIO_LCKR_LCK5;                    /* write 0 */
GPIOA->LCKR = GPIO_LCKR_LCKK | GPIO_LCKR_LCK5;   /* write 1 */
(void)GPIOA->LCKR;                               /* read: completes the sequence */
if (GPIOA->LCKR & GPIO_LCKR_LCKK) { /* reads 1 again: locked until reset */ }
```

HAL's `HAL_GPIO_LockPin()` does the same and returns `HAL_OK` when the lock holds.

The simplest software debounce:

```c
/* software debounce: on a press, wait 20 ms and confirm */
static uint8_t key_scan(GPIO_TypeDef *port, uint16_t pin)
{
    if (HAL_GPIO_ReadPin(port, pin) == GPIO_PIN_RESET)   /* saw a low */
    {
        HAL_Delay(20);                                    /* let the bounce pass */
        if (HAL_GPIO_ReadPin(port, pin) == GPIO_PIN_RESET) return 1;
    }
    return 0;
}
```

`HAL_Delay(20)` stops the main loop for 20 ms. A program with many buttons or tasks uses a timer scan instead.

The full project is in [`examples/gpio-blink/`](../../examples/gpio-blink/).

## Hands-on labs

1. **Lab 1: blink PC13 at 1 Hz.** On for 500 ms, off for 500 ms.
   - Expected: the onboard LED blinks once a second, in step with `gpio-blink.svg` and `led-blink.gif`.
   - How to check: time 10 blinks with a phone stopwatch; it should be about 10 s. With a logic analyzer, measure the PC13 period; it should be close to 1.000 s.
   - If it fails, check first: is the port clock on; is it really PC13; and remember the onboard LED lights on low.
2. **Lab 2: a button controls an external LED.** Put the LED on PA0 with 270 Ω in series, and light it with the PA1 button.
   - Expected: on while held, off when released.
   - How to check: measure the voltage across the resistor with a multimeter and divide by 270 Ω; that is the LED current, a few milliamps.
   - If it fails, check first: is the LED reversed (the longer lead is the anode); is the PA1 pull-up on.
3. **Lab 3: compare the speed of three styles.** Toggle PA0 continuously with HAL, with BSRR, and with bit-banding, and look at the pulse widths on a logic analyzer.
   - Expected: BSRR and bit-band pulses are narrower than HAL's, because the HAL function adds parameter checks and a call.
   - How to check: at the same core clock, compare the high-time of the three waveforms.

## Self-test

1. On an F103 you remap USART1 to PB6/PB7 and forget the AFIO clock. What do you see?
2. PA0 is not marked FT in the datasheet. Can you tie a 5 V sensor to it directly?
3. You finish the three `LCKR` writes and never read it. Is the lock in effect?
4. A red LED (Vf = 2.0 V) on a 3.3 V pin should run at 10 mA. What resistor do you need?

Answers:

1. The remap does not happen. Without the AFIO clock the MAPR write has no effect, USART1 stays on PA9/PA10, and PB6/PB7 stay silent.
2. No. Only pins marked FT withstand 5 V, and PA0 is not marked. Use a level shifter or a divider.
3. You cannot count on it. RM0008 gives the sequence as write 1, write 0, write 1, read, read again; the first read is part of the sequence, and only a second read of LCKK = 1 shows the lock holds.
4. (3.3 − 2.0) / 0.010 = 130 Ω; pick a nearby standard value.

## Principle and scope

> [!NOTE]
> From this section to "Pitfalls and sources" is the deep part. It pins the conclusions above to one part number, one manual section, and numbers you can recompute. On a first read you can skip it and come back after the labs.

The rules above hold for most STM32 parts. Pin numbers and currents have to be tied to one chip; this book uses STM32F103C8T6 in LQFP48, the chip on a BluePill board.

**Pin numbers.** [DS5319 Rev 20](#source-ds5319-gpio) Figure 8 and Table 5 place PA0-WKUP on pin 10 and PC13-TAMPER-RTC on pin 2. A different package moves them; look the table up again.

**An external LED on PA0.** PA0 may source current: as a push-pull output written 1, current leaves the pin from 3.3 V through the internal PMOS, then through the resistor and the LED to ground. The example assumes an LED drop of 2.0 V and 5 mA: `(3.3 − 2.0) / 0.005 = 260`, fitted as the standard value 270 Ω. Those numbers are settings of [this book's example](#source-project-examples), not a datasheet recommendation.

**PC13 is the exception.** PC13, PC14, and PC15 are supplied through an on-chip power switch that can sink only a small current. Note 5 of the same datasheet says: as outputs these three pins sink at most 3 mA, run at no more than 2 MHz, drive at most 30 pF, and must not source current to light an LED. So the 25 mA and 50 MHz figures in Core ideas do not apply to them. The BluePill onboard LED still works on PC13 because its anode is at 3.3 V and the pin only sinks the current, which is why writing 0 lights it. Copying the PA0 "write 1 to light" circuit onto PC13 does not work.

**When you change chips.** A different package or orderable means looking up pin 2 and pin 10 again. F4 picks alternate functions with each pin's AFR, a register RM0008 does not have; "F1 remaps through AFIO MAPR" holds only on F1.

## Key figures

<p align="center">
  <img src="../../assets/diagrams/sample-03-gpio-led.svg" width="760" alt="On STM32F103C8T6, PA0 lights an external LED through 270 ohms; PC13 must not source that current">
  <br><sub>▲ Drawn for this book. STM32F103C8T6, LQFP48: PA0 is pin 10 and PC13 is pin 2. The normal path is 3.3 V through a push-pull pin and 270 Ω into the LED; 260 Ω is the quotient (3.3 − 2.0) / 0.005. The failure path copies that circuit onto PC13: note 5 allows 3 mA sink, at most 2 MHz, into 30 pF. The lock sequence is GPIOx_LCKR at offset 0x18. Pin and current facts are [DS5319 Rev 20](#source-ds5319-gpio) Table 5, Figure 8, and note 5. The lock and SWD pins are [RM0008 Rev 21](#source-rm0008-gpio) section 9.2.7 and section 9.3.5 Table 36.</sub>
</p>

The figure shows two paths: on top, the current path of a normal PA0 LED; below, why the same circuit fails on PC13. The opening `gpio-blink.svg` is the animated version; this one is static and still reads when printed.

## Timing and state

The 1 Hz blink has nothing to do with the GPIO speed setting. On 500 ms and off 500 ms come from `HAL_Delay(500)` in the [gpio-blink example](#source-project-examples). Setting the speed to 50 MHz does not turn PC13 into a pin that may light an external LED.

The lock is a small state machine that must run in order. The register is `GPIOx_LCKR` at offset `0x18`, and the order comes from [RM0008 Rev 21 section 9.2.7](#source-rm0008-gpio):

| Step | LCK[15:0] (pins to lock) | LCKK | Read | Result |
| --- | --- | --- | --- | --- |
| 1 | Choose the pins | Write 1 | — | Sequence starts |
| 2 | Same, must not change | Write 0 | — | Sequence continues |
| 3 | Same, must not change | Write 1 | — | Three writes done |
| 4 | Same | — | Read once; LCKK is 0 | Sequence complete |
| 5 | Same | — | Read again; LCKK is 1 | Lock confirmed until reset (this read is optional) |
| Failure | The pin mask changed, or a write was skipped | — | LCKK never reads 1 | Lock aborted; the configuration can still change |

## Pitfalls and sources

| Symptom | Cause | What to do | Source | What the source supports |
| --- | --- | --- | --- | --- |
| An external LED on PC13 does not light like PA0 when written 1 | PC13 must not source the LED | Move the external LED to PA0 with 270 Ω | [DS5319 Rev 20 note 5](#source-ds5319-gpio) | LQFP48 pin 2 is PC13; PC13–PC15 sink at most 3 mA, at or below 2 MHz, into 30 pF |
| The onboard LED stays dark when PC13 is written 1 | The onboard LED is common-anode; PC13 lights it by sinking | Write 0 | [gpio-blink example](#source-project-examples) | Only this BluePill's wiring; not the 3 mA datasheet limit |
| An ODR write does nothing on the pin | The port clock is still off, so the configuration never reached the peripheral | Enable that GPIO port clock, then write CRL/CRH | [RM0008 GPIO](#source-rm0008-gpio) | Only "clock the port before writing the chapter 9 configuration registers" |
| Three writes to LCKR still leave the pin editable | The sequence broke, or the read was missing | Keep the pin mask, write 1, write 0, write 1, then read; the second read shows 1 | [RM0008 section 9.2.7](#source-rm0008-gpio) | A finished lock holds until reset; one bad step aborts it |
| The debugger never connects after a flash | PA13 and PA14 were configured as plain GPIO | Leave SWD on PA13 and PA14 | [RM0008 Table 36](#source-rm0008-gpio) | SWDIO is PA13 and SWCLK is PA14 |

Button bounce stays out of this table: a 10–20 ms debounce time is a rule of thumb that neither RM0008 nor DS5319 gives, so it is not cited as a manual number. The labs still debounce the button.

## Related resources

- Official manuals: **RM0008** chapter 9 (GPIO) and section 9.2 (register description); **DS5319** pin definitions
- Previous: [02 Choosing a Part, Memory, and Clocks](02-part-and-clock.md) | Next: [04 Interrupts and the NVIC](04-interrupts-nvic.md)
- Figures: [`assets/animations/gpio-blink.svg`](../../assets/animations/gpio-blink.svg), [`assets/gif/led-blink.gif`](../../assets/gif/led-blink.gif)
- Hardware and documents: Nucleo board schematics on ST's website (a reference for how the LED is wired)
- Disclaimer: every illustration in this repo is a vector drawing or a program-generated animation by the author, not a manufacturer's photograph.

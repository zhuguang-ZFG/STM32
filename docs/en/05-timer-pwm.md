# 05 Timers and PWM
> 中文：[定时器与 PWM](../05-定时器与PWM.md)

> The timer keeps precise time, makes PWM, and captures an external signal. It is the heart of control applications.

<p align="center">
  <img src="../../assets/animations/timer-pwm.svg" width="760" alt="Timer counting and PWM duty cycle">
  <br><sub>▲ Animation: timer count, compare match, and PWM duty (a breathing LED; vector drawing by the author)</sub>
</p>

<!-- video:ch05 -->
<p align="center">
  <video width="640" controls poster="../../assets/video/ch05-tim.png">
    <source src="../../assets/video/ch05-tim.mp4" type="video/mp4">
  </video>
  <br><sub>▲ Chapter video with Chinese voice-over (2.6 min). <a href="../../assets/video/ch05-tim.mp4">MP4</a> · <a href="../../assets/video/ch05-tim.srt">subtitles</a></sub>
</p>

<details>
<summary>Narration script (Chinese, same text as the subtitles)</summary>

1. 定时器不是魔法，就是一个被时钟推着走的计数器。CNT 加到 ARR 就回头，这一圈就是周期。先把这句话讲顺，再去看 PWM。
2. 三个数各管一件事。PSC 把时钟变慢，ARR 决定一圈多长，CCR 决定方波在哪里翻。频率不对先看前两个，亮度不对再看 CCR。
3. 频率等于定时器时钟，除以 ARR 加 1，再除以 PSC 加 1。想要 1 千赫，先选定分频后的计数时钟，再反推 ARR。不要三个数一起瞎试。
4. 这一帧是仓库画的 PWM。计数器一边跑，一边和 CCR 比。低于和高于可以是两种电平，占空比就出来了。示波器上的高电平宽度，应该和你算的 CCR 一致。
5. 想要 1 千赫，你先定谁？先定 PSC，让计数时钟变成好算的整数，再定 ARR 加 1。CCR 最后填，因为它不改变频率，只改变占空比。
6. 输入捕获不是去量电压。边沿到来时，硬件把当时的 CNT 锁进捕获寄存器。两个边沿相减，再乘上计数周期，就是脉宽。口诀：捕获锁的是 CNT。
7. 回到时钟那一章：APB 分频大于 1 时，定时器时钟常常还要乘 2。公式里的时钟用错，你算的 1 千赫会变成 2 千赫或 500 赫。先问到真实的定时器时钟。
8. 口诀：捕获锁的是 CNT。想要某个频率，先定 PSC，再定 ARR。三个数不要一起拧，拧乱了就不知道是谁的错。
9. 实验输出大约 1 千赫、占空比三成的 PWM。用逻辑分析仪或示波器对一下。对不上时，先核对定时器时钟，再核对 ARR 和 CCR，别先怀疑探头。
10. 合上书，三问。PSC 和 ARR 谁决定频率？CCR 决定什么？输入捕获锁进去的是电压，还是当时的 CNT？

</details>
<!-- /video:ch05 -->

## Learning goals

Before this chapter: finish chapter 02 (how the 72 MHz system clock and the 36 MHz APB1 clock are set up), chapter 03 (configuring a pin as alternate-function push-pull, sizing an LED resistor), and chapter 04 (ISRs and NVIC priorities). You should be able to convert between decimal and hex and know that the largest 16-bit number is 65535 (if not, read the "Zero-background primer" in chapter 00 first).

- [ ] Say what PSC, ARR, and CCR each control, and work out a PSC and ARR pair for 1 kHz from a 72 MHz timer clock
- [ ] Explain why TIM3 is calculated at 72 MHz when APB1 runs at only 36 MHz, and say what frequency the wrong clock gives
- [ ] Output 1 kHz PWM on PA6, measure a 1 ms period and a 500 µs high time with a logic analyzer, then change the duty to 30%
- [ ] Say why ARR and CCR changes need preload, and at which moment a new value takes effect
- [ ] Use input capture on PA0 to measure the period and high time of a PWM signal
- [ ] Name the timers on the STM32F103C8T6, say which one can drive complementary PWM, and why that one needs MOE set first
- [ ] Explain why an encoder needs both phases A and B, and how TRGO lets the ADC sample at a fixed interval

## Core ideas

**In one sentence: a timer is a counter pushed along by a clock. PSC sets how fast it counts, ARR sets where it turns back, and CCR sets the moment in each lap when the output flips. The first two numbers fix the period; the third fixes the duty cycle.**

### An analogy first

Picture the timer as a person walking laps of a track, stepping to a metronome.

- The **clock** is the metronome. It clicks 72 million times a second.
- **PSC** says how many clicks pass before the walker takes one step. With PSC = 71 the walker steps once every 72 clicks, a million steps a second.
- **ARR** is the number of steps in a lap. With ARR = 999 the walker returns to the start after step 999, so a lap is exactly 1000 steps and takes 1 millisecond.
- **CCR** is a flag planted beside the track. While the walker is before the flag the lamp is on; past the flag it is off. With the flag at step 500, the lamp is on for half of every lap.
- **Input capture** is a clerk listening for a whistle. When the whistle blows (an edge arrives on a pin), the clerk writes down which step the walker has reached.

The analogy stops here. A real counter only counts whole steps, and a lap is at most 65536 steps (16 bits). A change to PSC, ARR, or CCR usually waits until the current lap is finished (section 5). And once the flag is planted past the finish line (CCR greater than ARR), the lamp stays on all the time (section 6).

### 1. What a timer is: a counter that counts by itself

A **timer** is a circuit in the chip that counts by itself. At its heart is the counter **CNT**: it adds 1 on every clock pulse and goes back to 0 when it reaches its limit. One lap always takes the same time, so it can measure time; flip a pin at some point in the lap and it outputs a square wave.

A **clock** is a square wave at a fixed frequency. Like a metronome, it sets the pace for every digital circuit in the chip. The timer's clock comes from the RCC, the reset and clock controller from chapter 02.

Three registers control the counter. As chapter 03 explained, a register is one storage slot inside a peripheral, and the number you write there decides how the peripheral behaves:

| Register | Full name | What it controls | This chapter's example |
| --- | --- | --- | --- |
| PSC | Prescaler | Divides the timer clock by PSC + 1 to give the counter clock | 71: 72 MHz ÷ 72 = 1 MHz |
| ARR | Auto-reload register | CNT goes back to 0 after reaching ARR, so a lap is ARR + 1 ticks | 999: 1000 ticks per lap, 1 ms |
| CCR | Capture/compare register | For PWM, the position of the "flag"; for input capture, where CNT is stored | 500: high for half of every lap |

The first two rows decide the frequency; the third row only decides the duty. If the frequency is wrong, check PSC and ARR; if the brightness is wrong, check CCR. Watch the two "plus ones": PSC holds the divisor minus 1, and ARR holds the ticks per lap minus 1.

The moment CNT goes from ARR back to 0 is the **update event** (UEV), often called the overflow. It can raise an interrupt (chapter 04), start a DMA transfer (chapter 10), or give the ADC a beat (section 10).

```text
timer clock 72 MHz ──▶ PSC = 71 (÷72) ──▶ counter clock 1 MHz ──▶ CNT: 0, 1, 2 … 999, 0, 1 …
                                                                     │
                                            each wrap from 999 to 0 ──▶ update event, every 1 ms

CNT
999 |      /|      /|      /|
    |    /  |    /  |    /  |
    |  /    |  /    |  /    |
  0 +-/-----+-/-----+-/-----+----▶ time
      |<- 1 ms ->|
```

### 2. Which timers this chip has

**Conclusion: the STM32F103C8T6 has only four timers that can output PWM: the advanced timer TIM1 and the general-purpose timers TIM2, TIM3, and TIM4. All of them are 16-bit.**

DS5319 Rev 20 section 2.3.15 and Table 4 (page 17) list every timer on this part:

| Class | On the C8 | Width | What is special | Typical use |
| --- | --- | --- | --- | --- |
| Advanced | TIM1 | 16-bit | 4 channels, 3 pairs of them with complementary outputs; dead time and break; MOE must be set before any output | Motors, half-bridge and full-bridge drives |
| General-purpose | TIM2, TIM3, TIM4 | 16-bit | 4 channels each: PWM, input capture, encoder | LED dimming, frequency measurement, encoders, periodic interrupts |
| Watchdog | IWDG, WWDG | 12-bit, 7-bit | Reset the chip when the program runs away; chapter 11 covers them | Recovering from a hang |
| System timer | SysTick | 24-bit | Built into the Cortex-M3 core | The HAL 1 ms tick, the RTOS tick |

Read the table from the top: complementary PWM can only come from TIM1 in the first row; ordinary PWM, frequency measurement, and encoders use the second row; the last two rows never drive a waveform onto a pin. The width column describes the counter. The prescalers of TIM1–TIM4 are 16-bit too and divide by any integer from 1 to 65536 (same table).

The TIM5–TIM8 you see in other tutorials exist only on larger F103 parts (RM0008 documents them in the same manual as TIM1–TIM4). TIM6 and TIM7 are **basic timers** that only count and have no pins, and TIM8 is a second advanced timer. The C8 has none of them, so an example copied from a high-density part that uses TIM6 will not work here. A 32-bit TIM2 or TIM5 is found on STM32F4 and other families (RM0090 Rev 22 section 18.2); on those families the sentence "all timers on this part are 16-bit" is void.

To choose a timer on the C8 by job:

| Job | Use on the C8 |
| --- | --- |
| Ordinary PWM, periodic interrupts | TIM2–TIM4 |
| Complementary PWM with dead time | TIM1 |
| Just a time base | Whichever of TIM2–TIM4 is free, or SysTick |
| Very long intervals | No 32-bit timer here: PSC and ARR together reach about 59.65 s (section 4); beyond that, count laps in the update interrupt |
| The system tick | SysTick |

A timer has only one PSC and one ARR at a time. In this chapter TIM3 outputs PWM, TIM2 does input capture, and TIM4 gives a 1 s periodic interrupt: three timers, one job each.

### 3. The timer clock: APB1 runs at 36 MHz, yet TIM3 gets 72 MHz

**Conclusion: when an APB bus prescaler is not 1, every timer on that bus gets twice the bus clock. With the Appendix D settings, TIM1–TIM4 all have a 72 MHz timer clock.**

The STM32F103 has two peripheral buses: APB1 runs at up to 36 MHz and APB2 at up to 72 MHz (DS5319 Rev 20 section 2.3.7). Appendix D sets the system clock to 72 MHz, divides APB1 by 2 to get PCLK1 = 36 MHz, and leaves APB2 undivided at PCLK2 = 72 MHz. RM0008 Rev 21 section 7.2 (page 94) says: if the APB prescaler is 1, the timer clock equals that bus clock; otherwise the timer clock is twice the bus clock.

| Timer | Bus | Bus clock (Appendix D) | Bus prescaler | Timer clock |
| --- | --- | --- | --- | --- |
| TIM2, TIM3, TIM4 | APB1 | PCLK1 = 36 MHz | 2 | 36 × 2 = 72 MHz |
| TIM1 | APB2 | PCLK2 = 72 MHz | 1 | 72 MHz, not doubled |

Read each row in two steps: first find the bus the timer sits on (RM0008 Rev 21 sections 7.3.7 and 7.3.8: the TIM1 clock enable is in RCC_APB2ENR, the TIM2–TIM4 enables are in RCC_APB1ENR), then check whether that bus prescaler is 1.

Keep two names apart. The **timer clock** is the clock the RCC feeds into the timer. RM0008's clock tree calls it TIMxCLK, and it is the prescaler input CK_PSC; in this chapter it is 72 MHz. The **counter clock** CK_CNT is what comes out of PSC and actually steps CNT; with PSC = 71 it is 1 MHz (RM0008 Rev 21 section 15.4.11).

Use the wrong clock and the frequency is off by a whole factor. For the pair PSC = 71, ARR = 999:

- Divide by the 36 MHz PCLK1 and you predict 500 Hz on paper, while the scope shows 1000 Hz.
- Work the other way from 36 MHz: to get 1 kHz you pick PSC = 35, and the scope shows 2000 Hz.
- Forget to call `SystemClock_Config()` and the chip stays on its 8 MHz internal RC oscillator (HSI) from reset (DS5319 Rev 20 section 2.3.7). APB1 is not divided, so the timer clock is not doubled and is only 8 MHz, and the same pair outputs about 111 Hz.

So before you calculate any PWM, find out what the timer clock really is.

### 4. Time-base formulas: pick PSC first, then ARR

**Conclusion: first choose a counter clock that is easy to work with (that picks PSC), then multiply the period by the counter clock to get the ticks per lap (that gives ARR + 1). Neither number may exceed 16 bits.**

Three formulas. `fCK_PSC` is the timer clock (72 MHz in this chapter) and `fCK_CNT` is the counter clock:

```text
counter clock   fCK_CNT = fCK_PSC / (PSC + 1)
time per lap    T       = (PSC + 1) × (ARR + 1) / fCK_PSC
frequency       f       = fCK_PSC / ((PSC + 1) × (ARR + 1))
```

The first comes from RM0008 Rev 21 section 15.4.11. The other two count ARR + 1 ticks on top of it (section 15.3.2: when counting up, CNT runs from 0 to ARR and then back to 0).

Work out 1 ms by hand:

1. Pick PSC = 71. The counter clock is `72 MHz / 72 = 1 MHz`, so CNT adds 1 every 1 µs.
2. A lap needs `1 ms × 1 MHz = 1000` ticks, so ARR + 1 = 1000 and ARR = 999.
3. Check: 71 and 999 are both below 65535, so they fit.

Useful values at 72 MHz:

| Target period | PSC | ARR | Counter clock | Actual period | Frequency |
| --- | --- | --- | --- | --- | --- |
| 1 ms | 71 | 999 | 1 MHz | 1.000 ms | 1 kHz |
| 10 ms | 7199 | 99 | 10 kHz | 10.00 ms | 100 Hz |
| 100 ms | 7199 | 999 | 10 kHz | 100.0 ms | 10 Hz |
| 1 s | 7199 | 9999 | 10 kHz | 1.000 s | 1 Hz |
| 1 s (large ARR) | 71 | 999999 | 1 MHz | does not fit | TIM2–TIM4 on this part are 16-bit; ARR tops out at 65535 and cannot hold 999999. The 1 s that fits is the row above, PSC = 7199 and ARR = 9999 |

You can recompute every row with `72e6 / ((PSC + 1) × (ARR + 1))`. The first four rows can be copied as they are. The last row is the counter-example: the counter clock is so fast that one second needs a million ticks, which a 16-bit ARR cannot hold.

With both PSC and ARR at their maximum, the longest lap is `65536 × 65536 / 72e6 ≈ 59.65 s`. For anything longer, count laps in the update interrupt.

### 5. Counting modes and shadow registers

**Conclusion: this chapter only counts up. A value written to PSC, ARR, or CCR normally waits until the current lap ends (the update event), so the waveform is never bent halfway through a lap.**

CNT can move in three ways (RM0008 Rev 21 section 15.3.2):

| Mode | How CNT moves | Ticks per lap | Where the update event falls |
| --- | --- | --- | --- |
| Up | 0 → ARR, then starts again at 0 | ARR + 1 | Wrapping from ARR to 0 (overflow) |
| Down | ARR → 0, then starts again at ARR | ARR + 1 | Wrapping from 0 to ARR (underflow) |
| Center-aligned | 0 → ARR − 1 then overflow, ARR → 1 then underflow, then starts again at 0 | 2 × ARR | Both overflow and underflow |

In the first two modes a lap is ARR + 1 ticks, so the formulas in section 4 apply directly. Center-aligned mode puts the high pulse in the middle of each lap, which motor control often wants. Its lap is 2 × ARR ticks, so the frequency is `fCK_CNT / (2 × ARR)`. With the same PSC = 71 and ARR = 999, center-aligned mode gives only `1e6 / 1998 ≈ 500.5` Hz.

Now, "when does a new value take effect". PSC, ARR, and CCR each have two layers: you read and write the **preload register**, and the **shadow register** behind it is what the counter and the comparator actually use. On an update event the hardware copies the preload value into the shadow register:

| Register | When a new value takes effect | Controlled by | Source (RM0008 Rev 21) |
| --- | --- | --- | --- |
| PSC | Always at the next update event | Nothing; it is always buffered | Section 15.3.1 |
| ARR | ARPE = 1: at the update event; ARPE = 0: at once | ARPE in TIMx_CR1 | Section 15.4.1 |
| CCRx | OCxPE = 1: at the update event; OCxPE = 0: at once | OCxPE in TIMx_CCMRx | Section 15.4.7 |

This table tells you how long a change takes to show up on the scope: with preload on, at most one lap. Why wait at all? Say CNT has reached 400 and you change CCR from 300 to 500. Without the wait, the comparison flips straight from "CNT ≥ CCR" back to "CNT < CCR", and this lap gets an extra narrow pulse 100 µs wide. Section 15.4.7 puts it more firmly: apart from one-pulse mode, PWM without CCR preload has no guaranteed behavior.

Right after initialization the shadow registers still hold their reset values. Writing 1 to the UG bit in TIMx_EGR forces one update event by hand and copies the new values in at once (section 15.3.9 asks for this before the counter starts). With the HAL, `HAL_TIM_PWM_Init()` writes UG for you and `HAL_TIM_PWM_ConfigChannel()` sets OCxPE for you; both facts come from the STM32CubeF1 HAL source, not from the manual.

### 6. PWM modes: CCR decides where the output flips

**Conclusion: in PWM mode 1 the output is at its active level while CNT is less than CCR, and at its inactive level otherwise. With the active level set to high, duty = CCR / (ARR + 1).**

**PWM** (pulse width modulation) is a square wave whose frequency stays put while the width of the high part changes. The fraction of each lap spent high is the **duty cycle**. LED brightness and motor speed can both be set with the duty cycle.

Each channel has a comparator that keeps comparing CNT with CCR, and the result becomes an internal reference signal, OCxREF. The OCxM bits in TIMx_CCMRx choose the rule (RM0008 Rev 21 section 15.4.7):

| Mode | OCxM | OCxREF when counting up | High time with CCR = 300, ARR = 999 |
| --- | --- | --- | --- |
| PWM mode 1 | 110 | 1 while CNT < CCR, else 0 | CNT 0 through 299, 300 µs, 30% |
| PWM mode 2 | 111 | 0 while CNT < CCR, else 1 | CNT 300 through 999, 700 µs, 70% |

The two modes are inverses: the same CCR gives "1 minus the mode 1 duty" in mode 2. This chapter uses mode 1 throughout.

Before OCxREF reaches the pin it passes a polarity select: CCxP = 0 in TIMx_CCER passes it unchanged (the HAL's `TIM_OCPOLARITY_HIGH`), and CCxP = 1 inverts it. CCxE = 1 is what actually connects the waveform to the pin. So "mode 2" and "mode 1 plus inversion" are the same waveform at the pin.

```text
fPWM      = fCK_PSC / ((PSC + 1) × (ARR + 1))
Duty      = CCR / (ARR + 1)           (PWM mode 1, counting up, CCxP = 0)
high time = CCR / fCK_CNT
```

Remember the two end points (section 15.3.9; Figure 130 on page 388 draws them with ARR = 8): with CCR = 0 the output stays low, 0% duty; with CCR greater than ARR it stays high, 100% duty. With ARR = 999, walking CCR from 0 to 1000 walks the duty from 0% to 100%, 1001 steps in all.

### 7. Frequency versus resolution: you cannot have both

**Conclusion: with the timer clock fixed, the higher the PWM frequency, the fewer ticks a lap has (ARR + 1), and the fewer duty steps you can set.**

A lap of N ticks gives N duty steps, so the resolution is `1 / (ARR + 1)`. Every row below uses a 72 MHz timer clock:

| Target PWM frequency | PSC | ARR + 1 | Duty resolution | Notes |
| --- | --- | --- | --- | --- |
| 1 kHz | 1 | 36000 | 1/36000 | A different high-resolution set (PSC = 1 makes ARR + 1 = 36000, ARR = 35999). Not the Appendix D 1 kHz cell (PSC = 71, ARR = 999), whose resolution is 1/1000 |
| 10 kHz | 0 | 7200 | 1/7200 | A common motor PWM frequency (rule of thumb) |
| 20 kHz | 0 | 3600 | 1/3600 | Most people cannot hear above 20 kHz (rule of thumb), so the motor stops whining |
| 50 Hz (servo) | 71 | 20000 | 1/20000, 1 µs per step | ARR = 19999; servos usually take a 1–2 ms high pulse (rule of thumb), which is CCR = 1000–2000 |

Look at the second and third columns: `(PSC + 1) × (ARR + 1)` always equals `72e6 / f`. The smaller PSC is, the more ticks are left for ARR and the finer the steps.

Why the 1 kHz row does not use PSC = 0: ARR + 1 would have to be 72000, more than the 65536 that 16 bits can hold. With PSC = 0 a lap is at most 65536 ticks, so the lowest frequency is `72e6 / 65536 ≈ 1099` Hz. For 1 kHz, PSC must be at least 1.

### 8. Input capture: write down CNT at the moment of an edge

**Conclusion: input capture does not measure voltage. When an edge arrives on the pin, the hardware copies the CNT value of that instant into CCRx. Subtract two copies and you have the number of ticks between the two edges.**

Once a channel is set up as an input, CCRx becomes a read-only notebook (RM0008 Rev 21 section 15.3.5, page 384):

- When the selected edge arrives, CCRx stores the CNT of that moment and the flag CCxIF is set; with the interrupt enabled, the ISR runs.
- Reading CCRx clears CCxIF automatically.
- If a new capture arrives before the previous value has been read, the overcapture flag CCxOF is set: one capture was lost.

Measuring a PWM signal takes two instants: rising edges give the period and the falling edge gives the high time. One pin can feed two channels at once: CH1 connects straight to TI1 (PA0) and catches rising edges, and CH2, with CC2S set to 10, also connects to TI1 and catches falling edges (section 15.4.7). This is the first half of the "PWM input mode" in section 15.3.6, except that the counter is not cleared on the rising edge; subtraction does the job instead.

```text
PA0   ___|‾‾‾‾‾‾‾|____________|‾‾‾‾‾‾‾|______
         ↑       ↓            ↑
CNT     1200    1500         2200
        CH1     CH2          CH1

period    = 2200 − 1200 = 1000 ticks = 1000 µs (1 MHz counter clock)
high time = 1500 − 1200 =  300 ticks =  300 µs, 30% duty
```

CNT is 16 bits wide and wraps from 65535 to 0. A 16-bit unsigned subtraction still gives the right answer across one wrap: with rising edges at 65000 and 464, `(uint16_t)(464 − 65000) = 1000`. Two wraps give a wrong answer, so with a 1 MHz counter clock the interval you measure must be shorter than 65536 µs, about 65.5 ms. For slower signals, raise PSC or count the wraps in the update interrupt.

### 9. The encoder interface: two phases, one position

**Conclusion: in encoder mode the counter adds and subtracts on the edges of phases A and B by itself, so CNT is the position. Both phases must be wired, because the hardware decides the direction from which one leads.**

An **incremental encoder** outputs two square waves as it turns, phase A and phase B, a quarter of a cycle apart. Quadrature looks at both phases: B lagging A by about 90° is one direction, and B leading is the other. With only one square wave, the hardware cannot tell forward from reverse.

```text
A   __|‾‾‾‾|____|‾‾‾‾|____
B   ____|‾‾‾‾|____|‾‾‾‾|__     B lags A by a quarter cycle: one direction
CNT   +1 on every edge, +4 per cycle of A (SMS = 011)
```

With SMS in TIMx_SMCR set to 011, the counter counts on the rising and falling edges of both TI1 and TI2, four counts per cycle of A, and the DIR bit in TIMx_CR1 reports the direction (RM0008 Rev 21 section 15.3.12, page 392). On the C8, TIM1–TIM4 can all act as encoder interfaces; for example TIM2 on PA0 and PA1 (LQFP48 pins 10 and 11), or TIM4 on PB6 and PB7 (pins 42 and 43) (DS5319 Rev 20 section 2.3.15 and Table 5; for TIM1 see RM0008 Rev 21 section 14.3.16).

What happens with phase A alone is answered by Table 85 in section 15.3.12: while B sits at a fixed level, each rising edge of A moves CNT one way and each falling edge moves it back, so the count just hops between two neighboring values and never accumulates. Forward and reverse look the same.

### 10. Master mode and TRGO: a beat for the ADC

**Conclusion: TRGO (trigger output) is an internal signal line the timer drives outward. Select the update event as TRGO and the timer sends a beat to the ADC or another timer once per lap. The hardware keeps the sampling interval, however busy the main loop is.**

The MMS bits in TIMx_CR2 choose what TRGO carries; 010 is the update event (RM0008 Rev 21 section 15.4.2, page 406). Setting EXTSEL to 100 for ADC1's external trigger selects TIM3 TRGO (section 11.12.3, page 240). With PSC = 71 and ARR = 999, TIM3 updates every 1 ms, so the ADC converts every 1 ms, and the 1 kHz PWM on PA6 carries on unchanged; both jobs share one counter.

```c
/* TIM3 sends one TRGO beat on every update; chapter 09 selects TIM3_TRGO as ADC1's external trigger */
TIM_MasterConfigTypeDef mst = {0};
mst.MasterOutputTrigger = TIM_TRGO_UPDATE;          /* MMS = 010: the update event is TRGO */
mst.MasterSlaveMode     = TIM_MASTERSLAVEMODE_DISABLE;
HAL_TIMEx_MasterConfigSynchronization(&htim3, &mst);
```

The ADC side is set up in chapter 09: its external trigger is `ADC_EXTERNALTRIGCONV_T3_TRGO`. Do not start conversions one by one from the main loop in software; whenever the main loop gets busy, the sampling interval jitters with it.

The other way round, a timer can also be a **slave**: the slave mode controller resets, gates, or starts the counter from an external signal or from another timer's TRGO (sections 15.3.14 and 15.3.15). Period measurement and starting several timers together both rely on it.

Motto: **capture latches CNT, and TRGO sends the beat. An encoder must have both A and B.**

### 11. Complementary outputs and dead time: TIM1 only

**Conclusion: complementary outputs are a pair of inverted PWM signals that drive the high-side and low-side switches of a half bridge. Dead time is a deliberate gap with both switches off while they trade places, so they never conduct together and short the supply. On the C8 only TIM1 has this, and TIM1 outputs nothing at all until MOE is set.**

A **half bridge** is two switches in series between the supply and ground, with the load on the middle node. With the high-side switch on, the middle node connects to the supply; with the low-side switch on, it connects to ground. If both switches conduct at once, the supply is shorted straight to ground; this is called **shoot-through**.

| Idea | Meaning | Source |
| --- | --- | --- |
| Complementary outputs | CH1 and CH1N are a pair; when one is high the other is low. TIM1 has 3 pairs (CH1–CH3); CH4 has no complement | DS5319 Rev 20 section 2.3.15 |
| Dead time | After one output switches off, wait a short time before switching the other on; DTG[7:0] in TIMx_BDTR sets the length | RM0008 Rev 21 section 14.4.18 |
| Break | As soon as the BKIN pin is active, the hardware clears MOE, and the outputs switch off or go to their configured idle levels | Same |
| MOE | Main output enable, bit 15 of TIMx_BDTR; register offset 0x44, reset value 0x0000; no output until it is set to 1 | Same |

Read the table top to bottom as a chain of cause and effect: complementary outputs bring the risk of shoot-through, dead time and break guard against it, and MOE is the master switch over all of it. On the C8, TIM1_CH1 is on PA8 (LQFP48 pin 29), TIM1_CH1N on PB13 (pin 26), and TIM1_BKIN on PB12 (pin 25) (DS5319 Rev 20 Table 5).

The extra step on TIM1:

```c
/* TIM1 is an advanced timer: with MOE in BDTR still 0, there is no waveform on CH1 (PA8) */
HAL_TIM_PWM_Start(&htim1, TIM_CHANNEL_1);   /* the HAL sets MOE here as well */
/* register form: TIM1->BDTR |= TIM_BDTR_MOE; */
/* the HAL also has a macro that does the same: __HAL_TIM_MOE_ENABLE(&htim1); */
```

Setting up dead time and the complementary output:

```c
/* TIM1 dead time and break; the values are example settings */
TIM_BreakDeadTimeConfigTypeDef bd = {0};
bd.OffStateRunMode  = TIM_OSSR_ENABLE;
bd.OffStateIDLEMode = TIM_OSSI_ENABLE;
bd.LockLevel        = TIM_LOCKLEVEL_OFF;
bd.DeadTime         = 0x10;                     /* goes into DTG[7:0] of BDTR; example setting */
bd.BreakState       = TIM_BREAK_DISABLE;
bd.BreakPolarity    = TIM_BREAKPOLARITY_HIGH;
bd.AutomaticOutput  = TIM_AUTOMATICOUTPUT_DISABLE;
HAL_TIMEx_ConfigBreakDeadTime(&htim1, &bd);
HAL_TIM_PWM_Start(&htim1, TIM_CHANNEL_1);       /* CH1: PA8 */
HAL_TIMEx_PWMN_Start(&htim1, TIM_CHANNEL_1);    /* CH1N: PB13 */
```

Converting DTG into time goes by segments: section 14.4.18 gives four formulas, and the result also depends on the CKD bits in TIMx_CR1. The 0x10 above is only an example setting, and this book does not turn it into nanoseconds. Before you connect a real bridge, set the dead time from the MOSFET driver's datasheet, then measure the gap between the two outputs with a scope.

## Hardware and wiring

| Board | Peripheral | Pin | Notes |
| --- | --- | --- | --- |
| BluePill | LED (PWM dimming) | PA6 (TIM3_CH1, LQFP48 pin 16) | PA6 through 270 Ω (example setting) to the LED anode, cathode to GND; high turns it on |
| BluePill | Input capture | PA0 (TIM2_CH1, LQFP48 pin 10) | Lab 3 jumpers PA6 to PA0; a signal generator also works |
| BluePill | On-board LED | PC13 | For the 1 s periodic interrupt example; low turns it on (chapter 03) |
| Logic analyzer or scope | Measurement | Channel 0 on PA6, channel 1 on PA0, ground on GND | A sample rate of 1 MHz or more shows a 1 kHz waveform clearly (rule of thumb) |

```text
PWM dimming:    PA6 ──[270 Ω]──▶|── GND        high turns it on; more duty, more light
Input capture:  PA6 ──────────────── PA0        lab 3 jumper, both pins on the same board
Measurement:    analyzer CH0 ── PA6, CH1 ── PA0, GND ── GND
```

Pin numbers are from DS5319 Rev 20 Table 5. Using the method in chapter 03 section 4 and taking Vf of a red LED as 2.0 V (rule of thumb), the current is about `(3.3 − 2.0) / 270 ≈ 4.8 mA`. With a signal generator, keep the amplitude between 0 and 3.3 V: neither PA0 nor PA6 is 5 V tolerant; Table 5 lists their type as I/O, not FT.

## Code

`timer_pwm.c` below goes with labs 1 and 2: TIM3_CH1 (PA6) outputs 1 kHz PWM, and setting `LAB_BREATHE` to 1 turns it into a breathing LED.

```c
/* timer_pwm.c —— TIM3_CH1 (PA6) outputs 1 kHz PWM; with LAB_BREATHE = 1 it breathes */
#include "stm32f1xx_hal.h"

#define LAB_BREATHE  0           /* 0: lab 1, fixed duty; 1: lab 2, breathing LED */

#define PWM_TIM      TIM3
#define PWM_CH       TIM_CHANNEL_1
#define PWM_PSC      71          /* 72 MHz / (71 + 1) = 1 MHz counter clock */
#define PWM_ARR      999         /* 1 MHz / (999 + 1) = 1 kHz PWM */

TIM_HandleTypeDef htim3;

void SystemClock_Config(void);

static void pwm_init(void)
{
    __HAL_RCC_TIM3_CLK_ENABLE();
    __HAL_RCC_GPIOA_CLK_ENABLE();

    /* PA6 alternate-function push-pull (TIM3_CH1) */
    GPIO_InitTypeDef io = {0};
    io.Pin   = GPIO_PIN_6;
    io.Mode  = GPIO_MODE_AF_PP;
    io.Speed = GPIO_SPEED_FREQ_HIGH;
    HAL_GPIO_Init(GPIOA, &io);

    htim3.Instance               = PWM_TIM;
    htim3.Init.Prescaler         = PWM_PSC;
    htim3.Init.CounterMode       = TIM_COUNTERMODE_UP;
    htim3.Init.Period            = PWM_ARR;          /* Period is ARR */
    htim3.Init.ClockDivision     = TIM_CLOCKDIVISION_DIV1;
    htim3.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_ENABLE;
    HAL_TIM_PWM_Init(&htim3);

    TIM_OC_InitTypeDef oc = {0};
    oc.OCMode     = TIM_OCMODE_PWM1;
    oc.Pulse      = 500;                             /* CCR = 500. 500 / (ARR + 1) = 50%, high for 500 µs */
    oc.OCPolarity = TIM_OCPOLARITY_HIGH;
    oc.OCFastMode = TIM_OCFAST_DISABLE;
    HAL_TIM_PWM_ConfigChannel(&htim3, &oc, PWM_CH);

    HAL_TIM_PWM_Start(&htim3, PWM_CH);               /* start the PWM output */
}

int main(void)
{
    HAL_Init();
    SystemClock_Config();
    pwm_init();                                      /* from here on, PA6 carries 1 kHz at 50% */

#if LAB_BREATHE
    int16_t duty = 0;
    int16_t step = 10;
#endif

    while (1)
    {
#if LAB_BREATHE
        duty += step;
        if (duty >= PWM_ARR || duty <= 0) step = -step;           /* sweep 0→100% and back */
        __HAL_TIM_SET_COMPARE(&htim3, PWM_CH, (uint32_t)duty);    /* new CCR, used from the next lap */
        HAL_Delay(10);
#endif
    }
}
```

Piece by piece:

- `PWM_PSC 71`: 72 MHz ÷ (71 + 1) = 1 MHz, so CNT adds 1 every 1 µs. PSC holds the divisor minus 1, the most common off-by-one mistake.
- `PWM_ARR 999`: 1000 ticks per lap, 1 ms, 1 kHz. `htim3.Init.Period` is ARR under another name.
- `GPIO_MODE_AF_PP`: the timer drives PA6, so the pin must be alternate-function push-pull (RM0008 Rev 21 Table 23: timer output compare channels use alternate-function push-pull). As a plain push-pull output the pin only follows ODR and shows no PWM.
- `AutoReloadPreload = ENABLE`: ARPE = 1, so an ARR change waits for the current lap to end (section 5).
- `oc.Pulse = 500`: CCR = 500, 50% duty. `TIM_OCPOLARITY_HIGH` is CC1P = 0, active high.
- `HAL_TIM_PWM_ConfigChannel()` writes OC1M = 110 (PWM mode 1) and sets OC1PE; `HAL_TIM_PWM_Start()` sets CC1E to connect the waveform to the pin and then sets CEN to start counting. Both facts come from the HAL source.
- `__HAL_TIM_SET_COMPARE()` writes CCR1 directly. With preload on, the new value takes effect at the next update event, so the lap in progress is not cut short.
- The breathing loop adds or subtracts 10 from CCR every 10 ms (example settings): 100 steps from 0 to 1000, so 1 s to brighten and 1 s to dim. When CCR reaches 1000, which is ARR + 1, the duty is 100%.
- `SystemClock_Config()` is the one written in chapter 02, and its numbers match the clock-tree row in Appendix D: HSE 8 MHz, PLL ×9 to 72 MHz, APB1 divided by 2. Leave it out and the timer only gets 8 MHz, so the frequency drops to about 111 Hz.

The same job in register form lays out what the HAL does for you (bit names from RM0008 Rev 21 section 15.4):

```c
/* TIM3_CH1 outputs 1 kHz, 50% PWM on PA6, register form */
RCC->APB1ENR |= RCC_APB1ENR_TIM3EN;
RCC->APB2ENR |= RCC_APB2ENR_IOPAEN;
GPIOA->CRL = (GPIOA->CRL & ~(0xFU << 24)) | (0xBU << 24);  /* PA6: MODE = 11, CNF = 10, alternate push-pull */
TIM3->PSC   = 71;                                          /* 72 MHz / 72 = 1 MHz */
TIM3->ARR   = 999;                                         /* 1000 ticks per lap = 1 kHz */
TIM3->CCR1  = 500;                                         /* 50% */
TIM3->CCMR1 = TIM_CCMR1_OC1M_2 | TIM_CCMR1_OC1M_1          /* OC1M = 110: PWM mode 1 */
            | TIM_CCMR1_OC1PE;                             /* enable CCR1 preload */
TIM3->CCER  = TIM_CCER_CC1E;                               /* CC1P = 0 active high; CC1E = 1 drive the pin */
TIM3->CR1   = TIM_CR1_ARPE;                                /* ARR goes through preload too */
TIM3->EGR   = TIM_EGR_UG;                                  /* force one update to load the shadow registers */
TIM3->CR1  |= TIM_CR1_CEN;                                 /* start counting */
```

The step most often missed is UG among the last three. Without it, the shadow registers of PSC, ARR, and CCR1 keep their reset values until the first overflow, and the first lap of the waveform is wrong.

The input capture for lab 3 lives in its own file, `capture.c`: TIM2 catches both rising and falling edges on PA0.

```c
/* capture.c —— TIM2 measures a PWM signal on PA0: CH1 catches rising edges, CH2 falling edges on the same pin */
#include "stm32f1xx_hal.h"

TIM_HandleTypeDef htim2;

volatile uint16_t g_period;            /* period in µs (1 MHz counter clock, 1 tick = 1 µs) */
volatile uint16_t g_high;              /* high time in µs */
static volatile uint16_t s_rise;       /* CNT at the latest rising edge */

void capture_init(void)
{
    __HAL_RCC_TIM2_CLK_ENABLE();
    __HAL_RCC_GPIOA_CLK_ENABLE();

    GPIO_InitTypeDef io = {0};
    io.Pin  = GPIO_PIN_0;              /* PA0 = TIM2_CH1, floating input */
    io.Mode = GPIO_MODE_INPUT;
    io.Pull = GPIO_NOPULL;
    HAL_GPIO_Init(GPIOA, &io);

    htim2.Instance           = TIM2;
    htim2.Init.Prescaler     = 71;     /* 72 MHz / 72 = 1 MHz, 1 tick per µs */
    htim2.Init.CounterMode   = TIM_COUNTERMODE_UP;
    htim2.Init.Period        = 0xFFFF; /* let CNT run the full 16 bits, wrapping every 65.536 ms */
    htim2.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
    HAL_TIM_IC_Init(&htim2);

    TIM_IC_InitTypeDef ic = {0};
    ic.ICPrescaler = TIM_ICPSC_DIV1;   /* capture every edge */
    ic.ICFilter    = 0;                /* no filter */

    ic.ICPolarity  = TIM_INPUTCHANNELPOLARITY_RISING;
    ic.ICSelection = TIM_ICSELECTION_DIRECTTI;      /* CH1 watches TI1, which is PA0 */
    HAL_TIM_IC_ConfigChannel(&htim2, &ic, TIM_CHANNEL_1);

    ic.ICPolarity  = TIM_INPUTCHANNELPOLARITY_FALLING;
    ic.ICSelection = TIM_ICSELECTION_INDIRECTTI;    /* CH2 watches TI1 as well: falling edges on the same pin */
    HAL_TIM_IC_ConfigChannel(&htim2, &ic, TIM_CHANNEL_2);

    HAL_NVIC_SetPriority(TIM2_IRQn, 2, 0);          /* preemption 2, example setting */
    HAL_NVIC_EnableIRQ(TIM2_IRQn);
    HAL_TIM_IC_Start_IT(&htim2, TIM_CHANNEL_1);
    HAL_TIM_IC_Start_IT(&htim2, TIM_CHANNEL_2);
}

void TIM2_IRQHandler(void)
{
    HAL_TIM_IRQHandler(&htim2);
}

void HAL_TIM_IC_CaptureCallback(TIM_HandleTypeDef *htim)
{
    if (htim->Instance != TIM2)
    {
        return;
    }
    if (htim->Channel == HAL_TIM_ACTIVE_CHANNEL_1)          /* rising edge */
    {
        uint16_t now = (uint16_t)HAL_TIM_ReadCapturedValue(htim, TIM_CHANNEL_1);
        g_period = (uint16_t)(now - s_rise);   /* 16-bit subtraction: still right across one CNT wrap */
        s_rise   = now;
    }
    else if (htim->Channel == HAL_TIM_ACTIVE_CHANNEL_2)     /* falling edge */
    {
        uint16_t now = (uint16_t)HAL_TIM_ReadCapturedValue(htim, TIM_CHANNEL_2);
        g_high = (uint16_t)(now - s_rise);
    }
}
```

For lab 3, replace `main()` in `timer_pwm.c` with the version below and add `capture.c` to the project:

```c
/* lab 3: PA6 outputs 1 kHz PWM at 30%, and PA0 measures it */
void capture_init(void);

int main(void)
{
    HAL_Init();
    SystemClock_Config();
    pwm_init();                                      /* PA6: 1 kHz */
    __HAL_TIM_SET_COMPARE(&htim3, PWM_CH, 300);      /* duty to 30%, from the next lap */
    capture_init();                                  /* PA0: measure it */

    while (1)
    {
        /* pause the program and watch g_period and g_high in the debugger */
    }
}
```

Piece by piece:

- PA0 is a floating input: RM0008 Rev 21 Table 23 says timer input capture channels use a floating input.
- PSC = 71 gives 1 tick per µs, so a difference reads directly in microseconds. `Period = 0xFFFF` lets CNT run the full 16 bits, wrapping every 65.536 ms.
- CH1 uses `TIM_ICSELECTION_DIRECTTI` to watch rising edges on TI1; CH2 uses `TIM_ICSELECTION_INDIRECTTI` to watch TI1 as well and catch falling edges (CC2S = 10). One pin, two channels, two kinds of edge.
- `(uint16_t)(now - s_rise)` in the callback is a 16-bit subtraction, so it stays right when CNT wraps once between two edges (section 8).
- `htim->Channel` tells you which channel fired this time; the HAL fills it in before calling the callback.
- When the main loop reads `g_period` and `g_high` together, the two values may come from neighboring laps. That is fine for a display; for control, read them together with interrupts briefly off, as in chapter 04 section 7.

Last comes a periodic interrupt: TIM4 raises an update interrupt once a second and toggles PC13. Configure PC13 as a push-pull output as in chapter 03.

```c
/* tim4_1hz.c —— TIM4 raises one update interrupt every 1 s and toggles PC13 */
#include "stm32f1xx_hal.h"

TIM_HandleTypeDef htim4;

void tim4_1hz_init(void)
{
    __HAL_RCC_TIM4_CLK_ENABLE();

    htim4.Instance               = TIM4;
    htim4.Init.Prescaler         = 7199;       /* 72 MHz / 7200 = 10 kHz */
    htim4.Init.CounterMode       = TIM_COUNTERMODE_UP;
    htim4.Init.Period            = 9999;       /* 10 kHz / 10000 = 1 Hz */
    htim4.Init.ClockDivision     = TIM_CLOCKDIVISION_DIV1;
    htim4.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_DISABLE;
    HAL_TIM_Base_Init(&htim4);

    HAL_NVIC_SetPriority(TIM4_IRQn, 3, 0);     /* preemption 3, example setting */
    HAL_NVIC_EnableIRQ(TIM4_IRQn);
    HAL_TIM_Base_Start_IT(&htim4);             /* only the _IT version enables the update interrupt */
}

void TIM4_IRQHandler(void)
{
    HAL_TIM_IRQHandler(&htim4);
}

void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim)
{
    if (htim->Instance == TIM4)
    {
        HAL_GPIO_TogglePin(GPIOC, GPIO_PIN_13);
    }
}
```

- Why TIM4: TIM3 is busy with PWM and TIM2 with input capture, and a timer has only one PSC and one ARR at a time.
- `HAL_TIM_Base_Start_IT()`, with `_IT`, sets the update interrupt enable bit UIE in TIMx_DIER (RM0008 Rev 21 section 15.4.4). With `HAL_TIM_Base_Start()` the counter runs just the same, but the interrupt never fires.
- The callback checks `htim->Instance` first: every timer's update interrupt in a project shares this one callback.

The full project is in [`examples/timer-pwm/`](../../examples/timer-pwm/).

## Hands-on labs

1. **Lab 1: a 1 kHz square wave, first at 50%, then at 30%.** Leave `LAB_BREATHE` at 0, flash the program, and put the logic analyzer on PA6. After measuring, change `oc.Pulse` to 300 and flash again, or pause the program and set TIM3_CCR1 to 300 in the debugger's register view.
   - Expected: first a 1000 Hz square wave with a 500 µs high time; after the change to 300, the same frequency with a 300 µs high time, 30% duty. The LED gets somewhat dimmer.
   - How to check: on the logic analyzer, measure the gap between two rising edges, which should be 1.000 ms, and the high time, which should be 500 µs and then 300 µs. Both numbers can be recomputed with the formulas in sections 4 and 6.
   - If it fails, check first: no waveform at all, check the GPIOA and TIM3 clocks, that PA6 is alternate-function push-pull, and that `HAL_TIM_PWM_Start()` is called; about 111 Hz, `SystemClock_Config()` did not run; 2000 Hz, PSC was picked as 35 from 36 MHz.
2. **Lab 2: a breathing LED.** Set `LAB_BREATHE` to 1 and flash again.
   - Expected: the LED slowly brightens for 1 s, slowly dims for 1 s, and repeats. Compare the effect with `pwm-breath.gif`.
   - How to check: on the logic analyzer the frequency stays at 1000 Hz and only the high time changes, by 10 µs every 10 ms.
   - If it fails, check first: if the LED stays on or off, check its orientation and the 270 Ω resistor; if you can see clear flicker, the frequency has dropped too low, so go back and check the timer clock. Brightness that seems to change unevenly is normal: the eye is more sensitive to changes in the dark, so 0% to 10% looks like a much bigger step than 50% to 60% (rule of thumb).
3. **Lab 3: measure lab 1's waveform with input capture.** Replace `main()` as shown under "Code", add `capture.c` to the project, and jumper PA6 to PA0.
   - Expected: `g_period` is 1000 and `g_high` is 300, which is 1 kHz at 30%.
   - How to check: pause the program and look at both variables in the debugger. Both timers run from the same 72 MHz with the same PSC, so the readings should be exactly 1000 and 300; with a signal generator the two clocks come from different sources and the readings can be off by a tick or two (rule of thumb). Change CCR to 500 and run again; `g_high` should become 500.
   - If it fails, check first: both values are 0, check the jumper, the spelling of `TIM2_IRQHandler`, and `HAL_NVIC_EnableIRQ(TIM2_IRQn)`; `g_high` is about 700, the edges of the two channels are swapped; `g_period` is far from 1000, compare the PSC of TIM2 and TIM3, which should both be 71.

## Self-test

1. TIM4 should raise an update interrupt every 0.5 s. With PSC = 7199, what goes into ARR?
2. A 25 kHz motor PWM uses PSC = 0. What is ARR? How many duty steps are there? What CCR gives 37.5%?
3. If you captured only the rising edge, can you compute the duty? What can you compute?
4. The ADC should convert every 1 ms. Which event should TIM3's TRGO select? What are PSC and ARR? Which trigger source does the ADC select?
5. An encoder is wired to phase A only, and the phase B pin has its pull-up on, so it stays high. What does the count do when the shaft turns?

Answers:

1. The counter clock is `72e6 / (7199 + 1) = 10 kHz`; 0.5 s needs `0.5 × 10000 = 5000` ticks, so ARR = 4999.
2. ARR + 1 = `72e6 / 25e3 = 2880`, so ARR = 2879; there are 2880 duty steps, a resolution of 1/2880; CCR = `0.375 × 2880 = 1080`.
3. No. The difference between two rising edges only gives the period, and from it the frequency; the duty also needs the time of the falling edge. In lab 3, CH2 catching falling edges on the same pin supplies exactly that half.
4. The update event (MMS = 010). PSC = 71 and ARR = 999 give one update every 1 ms. ADC1's external trigger selects TIM3 TRGO (EXTSEL = 100, written `ADC_EXTERNALTRIGCONV_T3_TRGO` in the HAL).
5. The count just hops between two neighboring values and never accumulates, and forward looks the same as reverse. By RM0008 Rev 21 Table 85, while phase B stays at one level, a rising edge of A subtracts 1 from CNT and a falling edge adds 1, so each cycle cancels out.

## Principle and scope

> [!NOTE]
> From this section to "Pitfalls and sources" is the deep part. It pins the conclusions above to one part number, one manual section, and numbers you can recompute. On a first read you can skip it and come back after the labs.

**Part number and clock.** The waveform conclusions in this chapter are pinned to order code STM32F103C8T6. The clocks follow Appendix D: SYSCLK = 72 MHz, PCLK1 = 36 MHz, PCLK2 = 72 MHz. TIM3 is on APB1, and the APB1 prescaler is 2, not 1, so the TIM3 timer clock is twice 36 MHz, which is 72 MHz ([RM0008 Rev 21](#source-rm0008) section 7.2, page 94). This book always divides by 72 MHz for PWM, never by 36 MHz.

**The 1000 Hz calculation.** PSC = 71 and ARR = 999. `72e6 / ((71+1) × (999+1)) = 1000` Hz. PSC first divides 72 MHz down to a 1 MHz counter clock, then CNT counts 1000 steps, so a lap is 1 ms. Divide the same PSC and ARR by 36 MHz and you get 500 Hz. That is the failure path on the key figure: a wrong calculation, while the waveform on the board is still 1000 Hz. The scope only shows 500 Hz if the timer really gets just 36 MHz (a clock setup that does not follow Appendix D). The counter-clock formula is in section 15.4.11 of [RM0008 Rev 21 chapter 15](#source-rm0008-tim).

**Duty.** Section 15.3.9 of the same chapter: in PWM mode 1, counting up, the output is active while CNT < CCR. With CCR = 500, `500 / (999+1) = 50%`, and the high time is 500 µs. With CCR greater than ARR the output stays active, 100% duty; with CCR = 0 it stays inactive, 0% duty. Figure 130 on page 388 draws these cases with ARR = 8.

**The 16-bit limit.** This part has only three general-purpose timers, TIM2–TIM4, plus the advanced timer TIM1, and all of their counters and prescalers are 16-bit (DS5319 Rev 20 section 2.3.15, Table 4). PSC = 71 and ARR = 999999 do not fit: 999999 is more than 65535, and only the low 16 bits are kept. The 1 second that fits is PSC = 7199 and ARR = 9999, `72e6 / (7200 × 10000) = 1` Hz. A 32-bit TIM2 or TIM5 is a sentence about another family (for STM32F4 see RM0090 Rev 22 section 18.2); on those families the sentence "this part is 16-bit" is void.

**The pin.** With no remap, TIM3_CH1 is on PA6. DS5319 Rev 20 Table 5: LQFP48 pin 16 is PA6, the default alternate function includes TIM3_CH1, and the same cell also includes SPI1_MISO. This chapter's figure draws only the timer; chapter 08 covers SPI on this pin, and the two key figures never draw both functions as active together. A remap means writing `TIM3_REMAP` in AFIO_MAPR. The partial remap moves CH1 to PB4 (pin 40, which is JTAG's NJTRST after reset). The full remap moves it to PC6, but RM0008 Rev 21 Table 44 (page 178) notes that the full remap exists only on 64-pin and larger packages, and LQFP48 has no PC6. Neither remap is on the normal path. Source: [DS5319 Rev 20 Table 5](#source-ds5319-tim).

**MOE belongs to TIM1 alone.** On TIM1, `TIMx_BDTR` is at offset `0x44` with reset value `0x0000`; while bit 15 MOE is 0 the main output is off, and neither OC nor OCN outputs a waveform ([RM0008 Rev 21](#source-rm0008-tim) section 14.4.18, which the manual shares between TIM1 and TIM8). As soon as the break input is active, the hardware clears MOE. `HAL_TIM_PWM_Start` sets MOE; that fact comes from the STM32CubeF1 HAL source. General-purpose TIM3 has no such register, and the waveform on PA6 has nothing to do with MOE.

**When a change takes effect.** PSC is always buffered, and a new value waits for the next update event (section 15.3.1); ARR behaves the same with ARPE = 1, and CCR with OCxPE = 1 (sections 15.4.1 and 15.4.7). Section 15.4.7 also states that, apart from one-pulse mode, PWM without CCR preload has no guaranteed behavior.

## Key figures

<p align="center">
  <img src="../../assets/diagrams/sample-05-pwm-1khz.svg" width="760" alt="With a 72 MHz timer clock this PSC/ARR pair is 1 kHz; dividing by 36 MHz produces 500 Hz">
  <br><sub>▲ Drawn for this book. STM32F103C8T6, LQFP48 pin 16 PA6 = TIM3_CH1. Timer clock 72 MHz (the figure's Chinese label calls it the counter clock), PSC = 71, ARR = 999, CCR = 500. The normal path has a 1 ms period, 500 µs high, and 1000 Hz. The failure path divides by 36 MHz and predicts a 2 ms period and 500 Hz. ARR = 999999 does not fit in a 16-bit counter. TIM1 MOE is at offset 0x44 with reset value 0x0000, and it is not this waveform. SPI1_MISO is not drawn on this waveform. Sources: [RM0008 Rev 21 chapter 15](#source-rm0008-tim) and [DS5319 Rev 20 Table 5](#source-ds5319-tim).</sub>
</p>

**How to read this figure.** The figure has three parts. The normal path: the output is high while CNT counts 0 through 499 and low from 500 through 999, a 1000 µs lap at 1000 Hz. The failure path: the same PSC, ARR, and CCR divided by 36 MHz predict 2000 µs and 500 Hz, and the extra factor of two comes from taking PCLK1 as the timer clock. The side notes: 16 bits cannot hold 999999, and the 1 second that fits is PSC = 7199 and ARR = 9999; TIM1 MOE belongs to another timer and does not touch PA6. The figure's Chinese label 计数时钟 72 MHz ("counter clock 72 MHz") means the timer clock before PSC. In RM0008's terms the counter clock is the divided 1 MHz, and the figure's line about the counter clock being "first divided to 1 MHz" should be read the same way.

<p align="center">
  <img src="../../assets/gif/pwm-1khz.gif" width="640" alt="The level flips when CNT reaches CCR = 500, at 1000 Hz">
  <br><sub>▲ Auxiliary figure for the web and the article channel. It only plays the 1000 Hz path and the 500 µs high time. Print uses the static figure. The 500 Hz failure is not on this GIF.</sub>
</p>

The opening `timer-pwm.svg` is a side figure: it freezes a 30% frame with CCR = 300, the same number as step two of lab 1, and it also calls 72 MHz the timer clock. The breathing-LED `pwm-breath.gif` is only linked from "Related resources". For the 1 kHz and 500 Hz paths, the static key figure is the reference.

## Timing and state

The table splits the key figure into rows, and every row can be recomputed with the formulas in [RM0008 Rev 21 chapter 15](#source-rm0008-tim). The "Timer clock" column is the clock before PSC.

| Row | Timer clock | PSC | ARR | CCR | CNT | Output | Time |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Normal, high | 72 MHz | 71 | 999 | 500 | 0 through 499 | high | 500 µs |
| Normal, low | 72 MHz | 71 | 999 | 500 | 500 through 999 | low | another 500 µs, period 1000 µs, 1000 Hz |
| Lab 1, step two | 72 MHz | 71 | 999 | 300 | high 0 through 299, low 300 through 999 | high for 300 µs | period still 1000 µs, 30% |
| Failure (wrong calculation) | divided by 36 MHz | 71 | 999 | 500 | 0 through 999 | same compare | predicts a 2000 µs period and 500 Hz; the board still shows 1000 Hz |
| Does not fit | 72 MHz | 71 | 999999 | — | — | not a 1 s pulse | truncated at 16 bits: only the low 16 bits, 16959, are kept, a 16.96 ms lap, not counted as 1 s |
| 1 second | 72 MHz | 7199 | 9999 | — | 0 through 9999 | — | 1 Hz |

Arithmetic: `72e6 / (72 × 1000) = 1000` Hz; `36e6 / (72 × 1000) = 500` Hz; `999999 − 15 × 65536 = 16959`, and `(16959 + 1) × 1 µs = 16.96 ms`.

## Pitfalls and sources

| What you see | Why | What to do | Source | What the source supports |
| --- | --- | --- | --- | --- |
| You calculated 500 Hz, but the scope shows 1000 Hz | You divided by the 36 MHz PCLK1 | Divide by 72 MHz, with PSC = 71 and ARR = 999 | [RM0008 chapter 15](#source-rm0008-tim) | This set is 1000 Hz at 72 MHz. Dividing by 36 MHz produces 500 Hz |
| You picked PSC = 35 from 36 MHz, and the scope shows 2000 Hz | The same mistake, worked backwards | Pick PSC = 71 from 72 MHz | [RM0008 section 7.2](#source-rm0008) | When the APB prescaler is not 1, the timer clock is twice the bus clock |
| The frequency is about 111 Hz | `SystemClock_Config()` did not run; the chip is still on the 8 MHz HSI, APB1 is undivided, and the timer clock is 8 MHz too | Call `SystemClock_Config()` first | [RM0008 section 7.2](#source-rm0008) | When the APB prescaler is 1, the timer clock equals the bus clock |
| ARR was written as 999999 for a 1 s period | 16 bits cannot hold it; only the low 16 bits are kept | Use PSC = 7199 and ARR = 9999 | [RM0008 chapter 15](#source-rm0008-tim) | The general-purpose timers on this part are 16-bit and cannot hold 999999 |
| TIM1 has no waveform at all | BDTR bit 15 MOE is still 0 | Set MOE | [RM0008 section 14.4.18](#source-rm0008-tim) | The reset value is 0x0000. With MOE at 0 the main output stays off. The offset is 0x44. TIM3 has no such bit |
| PWM appears on some other pin | TIM3_REMAP is not 00 | Keep TIM3_REMAP=00 and use PA6 | [DS5319 Table 5](#source-ds5319-tim) | LQFP48 pin 16 is PA6, and the default alternate function includes TIM3_CH1 |
| An extra narrow pulse sometimes appears when CCR changes | OC1PE = 0, so the new value is compared at once | Enable CCR preload (OCxPE = 1) | [RM0008 section 15.4.7](#source-rm0008-tim) | With OCxPE = 1 the new value loads at the update event; apart from one-pulse mode, PWM without preload has no guaranteed behavior |
| Input capture reports a period far shorter than the real one | The interval is longer than 65536 ticks, so CNT wraps more than once between captures | Raise PSC, or count wraps in the update interrupt | [RM0008 section 15.3.5](#source-rm0008-tim) | On a capture, CCRx stores the CNT of that moment; CNT is 16-bit |
| The encoder count only hops between two values | Only phase A is wired; phase B sits at a fixed level | Wire phase B to CH2 | [RM0008 Table 85](#source-rm0008-tim) | While phase B stays at one level, the rising and falling edges of A add 1 and subtract 1 |

## Related resources

- Official manuals: **RM0008** chapter 14 (advanced timers TIM1/8), chapter 15 (general-purpose timers TIM2–5), chapter 16 (basic timers TIM6/7)
- Previous: [04 Interrupts and the NVIC](04-interrupts-nvic.md) | Next: [06 UART](06-uart.md)
- Figures: [`assets/animations/timer-pwm.svg`](../../assets/animations/timer-pwm.svg), [`assets/animations/timer-modes.svg`](../../assets/animations/timer-modes.svg), [`assets/gif/pwm-breath.gif`](../../assets/gif/pwm-breath.gif)
- Disclaimer: every illustration in this repo is a vector drawing or a program-generated animation by the author, not a manufacturer's photograph.

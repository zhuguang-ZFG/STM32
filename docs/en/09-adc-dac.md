# 09 ADC and DAC
> 中文：[09 ADC 与 DAC](../09-ADC与DAC.md)

> An ADC turns an analog voltage into a number. A DAC turns a number back into an analog voltage. On an STM32 they are the two ends that touch the real world.

<p align="center">
  <img src="../../assets/animations/adc-sar.svg" width="760" alt="Animation of ADC sample-and-hold and successive approximation (SAR)">
  <br><sub>▲ Animation: ADC sample-and-hold plus successive-approximation (SAR) compare (vector animation drawn by the author, not a live recording)</sub>
</p>

<!-- video:ch09 -->
<p align="center">
  <video width="640" controls poster="../../assets/video/ch09-adc.png">
    <source src="../../assets/video/ch09-adc.mp4" type="video/mp4">
  </video>
  <br><sub>▲ Chapter video with Chinese voice-over (2.6 min). <a href="../../assets/video/ch09-adc.mp4">MP4</a> · <a href="../../assets/video/ch09-adc.srt">subtitles</a></sub>
</p>

<details>
<summary>Narration script (Chinese, same text as the subtitles)</summary>

1. 逐次逼近之前，要先让采样电容充满。源阻抗越大，需要的采样时间越长。充不满就转换，读数会偏向你上一次采过的电压。
2. F1 的 ADC 是 12 位。换算时用读数除以 4096，再乘参考电压。用 4095 做口算会有一个最小步长的差别。参考电压不是想当然的 3.3，要看你接到哪。
3. STM32F103C8 有 ADC，没有 DAC。把 F4 的 DAC 例程抄过来，编译或许能过，引脚上不会出现你要的模拟电压。换芯片前先看数据手册的功能表。
4. 这一帧是仓库画的逐次逼近：从最高位开始试，比参考大了就清掉，再试下一位。它帮助你记得，转换需要时间，不是把引脚读进来就结束。
5. 引脚要设成模拟输入，ADC 时钟要开，规则通道和采样时间都要写上。少一项，读数会停在一个奇怪的常数。先读一个已知电压，比如分压后的参考，再去测传感器。
6. 连续采样不要在每个转换完成里做重活。让 DMA 把结果搬进数组，半满和全满时再去算。Wokwi 的 BluePill 模型没有 DMA，这章的连续采样要在真板上对。
7. 读数乱跳时，先看参考电压和模拟地，再谈软件平均。平均能盖住一点噪声，盖不住一根飞线当成天线。实验板上，传感器线短一点，结果会诚实很多。
8. 口诀：采样看阻抗，换算除以 4096，C8 没有 DAC。三句分别挡住采不准、算不准、抄错芯片这三件最常见的事。
9. 实验用电位器做分压，两端接地和参考，中间进 ADC。慢慢旋转，读数应该单调变化。跳变或反向，先查接线和参考，不要先改分辨率。
10. 合上书，三问。采样时间主要看什么？12 位换算要除以多少？STM32F103C8 有没有 DAC？

</details>
<!-- /video:ch09 -->

## Learning goals

Before this chapter: know what voltage, binary, and hexadecimal mean (if not, read "Zero-background primer" in chapter 00 first), be able to configure a pin as in chapter 03, and know how PCLK2 is divided down in chapter 02.

- [ ] Turn a code into a voltage: a 12-bit ADC divides by 4096, and at a nominal 3.3 V one LSB is about 0.806 mV
- [ ] Explain the three steps of a successive-approximation (SAR) ADC, sample, hold, compare, and why one conversion takes "sample cycles + 12.5" ADC clocks
- [ ] Choose a sample time from the source impedance, and check it with the DS5319 equation
- [ ] Write a single-channel polling program in HAL: analog input, calibration, channel setup, start, read
- [ ] Read the internal reference VREFINT to work out VDDA, read the internal temperature sensor to follow temperature changes, and say how large each error is
- [ ] Explain why continuous multi-channel acquisition uses scan mode plus DMA
- [ ] Check whether your chip has a DAC: the STM32F103C8 has no DAC

## Core ideas

**In one sentence: an ADC (analog-to-digital converter) first stores the pin voltage on a small on-chip capacitor, then compares 12 times to turn it into a code between 0 and 4095; voltage = code × VDDA / 4096. The sample time must be long enough to charge that capacitor, you must know what your reference voltage is, and the STM32F103C8 has an ADC but no DAC.**

### An analogy first

Think of the ADC as a person weighing something on a balance. They have a set of weights: the largest is half of full scale, the next is a quarter, the next an eighth, twelve weights in all.

- **Sampling**: first put the object on the pan. The object is a voltage, and the pan is the on-chip sample capacitor. Settling takes time; weigh before it settles and the reading is wrong.
- **Successive approximation**: try the largest weight first. If the weight side sinks, the weight is too heavy, so take it off; if not, leave it on. Then try the next one. After all twelve, the weights left on the pan are the result.
- **Reference voltage**: every weight is scaled to "full scale". If full scale (VDDA) changes, the same object weighs in at a different reading.

The analogy stops here. A real ADC has no weights: "trying a weight" is one comparison between the held voltage and a compare voltage the chip builds bit by bit, and "putting it on the pan" means the signal source charges the capacitor through a resistance once the sample switch closes, at a speed set by the source impedance. Section 4 gives the numbers.

### 1. Resolution, reference voltage, and quantization error

**Conclusion: a 12-bit ADC splits the range from 0 to the reference voltage into 4096 steps. At a nominal 3.3 V reference one step (1 LSB) is about 0.806 mV, and the ideal quantization error is ±0.5 LSB.**

A few words first:

- **Resolution**: how many binary digits the result has. 12 bits means 2^12 = 4096 codes, from 0 to 4095.
- **Reference voltage**: the voltage that the full-scale code stands for. On the STM32F103C8 the reference is the analog supply VDDA; the warning at the end of this section says why.
- **LSB** (least significant bit): the voltage for a change of 1 in the code, the height of one step.
- **Quantization error**: when the real voltage falls between two steps, the code can take only one of them, so an ideal ADC is off by at most half a step.

| Resolution N | Steps, 2^N | 1 LSB at a 3.3 V reference | Where you meet it |
| --- | --- | --- | --- |
| 8-bit | 256 | 12.89 mV | Coarse measurement |
| 10-bit | 1024 | 3.22 mV | — |
| 12-bit | 4096 | 806 µV | The ADCs on STM32F1 and F4 |
| 16-bit | 65536 | 50.4 µV | The H743 ADC can be set to 16 bits (RM0433 Rev 9) |

Read the table like this: every 2 extra bits make the step 4 times finer. A finer step does not mean a more accurate reading; error also comes from the reference voltage and from noise, which the next sections take one at a time.

```text
1 LSB         = Vref / 2^N
voltage       = code × Vref / 2^N
quantization  = ±0.5 LSB = ±Vref / 2^(N+1)       (ideal ADC, quantization only)
largest code  = 2^N − 1 = 4095, which stands for Vref − 1 LSB
```

One example: a nominal 3.3 V and code 2048. 2048 × 3.3 / 4096 = 1.65 V, exactly half. Dividing by 4095 gives 1.6504 V, less than one LSB away, but that is not how the manual counts: DS5319 Rev 20 Figure 37 defines the ideal 1 LSB as VREF+ / 2^n.

> [!WARNING]
> On the STM32F103C8 the reference voltage is VDDA on pin 9. DS5319 Rev 20 Table 47 note 3 says that in VFQFPN and LQFP packages VREF+ is connected to VDDA inside the chip and VREF− to VSSA. So any offset or ripple on VDDA goes one for one into the reading. For an accurate measurement, either filter VDDA on its own or read VREFINT first and work out VDDA (section 8). Other packages (TFBGA64, for example, has its own VREF+ pin) follow that part's pin table.

### 2. Channels and pins: where the signal comes in

**Conclusion: the STM32F103C8 has two ADCs, ADC1 and ADC2, sharing 10 external channels (PA0–PA7, PB0, PB1). ADC1 also has two internal channels: number 16 is the temperature sensor and number 17 is the internal reference VREFINT.**

| Channel | Pin / source | Notes |
| --- | --- | --- |
| IN0–IN7 | PA0–PA7 | PA0 is LQFP48 pin 10 |
| IN8, IN9 | PB0, PB1 | — |
| IN16 | On-chip temperature sensor | ADC1 only; set TSVREFE first |
| IN17 | On-chip reference VREFINT (typical 1.20 V) | ADC1 only; also set TSVREFE first |

Use the table like this: find the pin your signal is on, then look up its channel number, because the program asks for the channel number. The datasheet writes these pins as ADC12_INx, meaning both ADC1 and ADC2 can reach them. When a pin is an analog input, configure it in analog mode (`GPIO_MODE_ANALOG` from chapter 03) so the digital input circuit is switched off and the voltage reaches the ADC unchanged. For other packages and other families, the channel table follows that part's datasheet pin table.

### 3. Successive approximation (SAR): sample-and-hold plus binary compare

**Conclusion: a SAR (successive-approximation register) ADC closes in on the input voltage by binary search. A 12-bit result takes 12 comparisons, settling one bit at a time from the most significant bit (MSB) to the least significant bit (LSB).**

One conversion has three steps:

1. **Sample**: the sample switch closes. The external signal charges the on-chip sample capacitor `C_ADC` through the source's own resistance `R_AIN` and the on-chip switch resistance `R_ADC`, and the capacitor voltage follows the input.
2. **Hold**: the switch opens. The capacitor voltage is frozen and does not change during the comparisons.
3. **Successive approximation**: the comparator first compares the held voltage with `Vref/2` (MSB set to 1). If the input is larger, the bit stays; if smaller, it is cleared. Then `Vref/4`, and so on. Twelve comparisons give the 12-bit result.

<p align="center">
  <img src="../../assets/gif/sar-adc.gif" width="720" alt="Program-generated GIF of the SAR ADC successive-approximation compare">
  <br><sub>▲ Animation: SAR ADC successive-approximation compare (program-generated raster animation, not a live recording)</sub>
</p>

So one conversion takes the sample time plus 12.5 ADC clocks (RM0008 Rev 21 section 11.6). The 12.5 cycles at the end belong to the successive approximation and are fixed. The sample time in front is chosen per channel in `ADC_SMPR1` / `ADC_SMPR2`, in 8 steps: 1.5 / 7.5 / 13.5 / 28.5 / 41.5 / 55.5 / 71.5 / 239.5 ADC clocks (sections 11.12.4 and 11.12.5).

The ADC clock (ADCCLK) is divided down from PCLK2, and DS5319 Rev 20 Table 47 keeps it between 0.6 and 14 MHz. Two sums at 12 MHz:

- Shortest step: 1.5 + 12.5 = 14 cycles, 14 / 12 MHz ≈ 1.17 µs.
- Longest step: 239.5 + 12.5 = 252 cycles, 252 / 12 MHz = 21 µs.

The "1 µs" in RM0008 section 11.2 is a figure for a 14 MHz ADC clock: one conversion takes 1 µs at a 56 MHz system clock and 1.17 µs at 72 MHz. The reason is that at 72 MHz the ADC clock can only be 12 MHz (÷6); ÷4 gives 18 MHz, above the 14 MHz limit. So at 72 MHz this part does not reach 1 MSPS.

### 4. Sample time follows the source impedance

**Conclusion: the higher the internal resistance of the signal source, the slower it charges the sample capacitor, and the longer the sample time has to be. On the STM32F103C8 at 12 MHz: 1 kΩ takes 7.5 cycles, 10 kΩ takes 13.5 cycles, 50 kΩ takes 55.5 cycles; above 50 kΩ, put an op-amp follower in front.**

The source impedance `R_AIN` is the equivalent resistance you see looking out of the ADC pin into the signal source. For a divider it is the two resistors in parallel: a 10 kΩ potentiometer is at its worst in the middle, where it is 5 kΩ ∥ 5 kΩ = 2.5 kΩ.

Equation 1 in DS5319 Rev 20 section 5.3.18 gives the largest source impedance that keeps the error below 1/4 LSB:

```text
R_AIN < T_S / (f_ADC × C_ADC × ln(2^(N+2))) − R_ADC      T_S is the number of sample cycles
N = 12, ln(2^14) ≈ 9.704; C_ADC is at most 8 pF, R_ADC at most 1 kΩ (Table 47)
turned around: sample time t_S > (R_AIN + R_ADC) × C_ADC × ln(2^14)
```

The turned-around form gives the shortest sample time a common source needs; then pick the first of the 8 steps at 12 MHz that is not shorter:

| Source impedance R_AIN | Shortest sample time it needs | Step to choose at 12 MHz |
| --- | --- | --- |
| 1 kΩ | (1 + 1) kΩ × 8 pF × 9.704 ≈ 155 ns | 7.5 cycles (0.625 µs); 1.5 cycles is only 125 ns, not enough |
| 2.5 kΩ (10 kΩ potentiometer in the middle) | ≈ 272 ns | 7.5 cycles |
| 10 kΩ | ≈ 0.854 µs | 13.5 cycles (1.125 µs) |
| 50 kΩ | ≈ 3.96 µs | 55.5 cycles (4.625 µs) |
| Above 50 kΩ | Outside Table 47: R_AIN is at most 50 kΩ | Add an op-amp follower; do not brute-force it with 239.5 cycles |

Use the table like this: estimate the source impedance, find its row, take that row's step, and round up rather than down. DS5319 Table 48 lists the largest R_AIN for each step at 14 MHz (13.5 cycles allows 11.4 kΩ, for example); at 12 MHz each cycle is longer, so the allowed impedance is a little higher than Table 48.

If the sample is too short, the comparison starts before the capacitor has charged, and the reading leans toward the voltage already on the capacitor, which is whatever the previous channel left there. During a scan, a high-impedance channel is the one most easily dragged by the channel before it; lengthen the sample, or put a low-impedance channel between two high-impedance ones. That advice is practice, and the manuals give no number for it.

### 5. Conversion modes: single, continuous, scan, discontinuous

**Conclusion: single converts once when you want one reading; continuous starts again as soon as it finishes; scan converts several channels from a sequence list in one go; discontinuous converts only a short slice of that list per trigger.**

Three words first:

- **Regular group**: the list of channels that normally queue for conversion, up to 16, written in `ADC_SQR1`–`ADC_SQR3`. All regular channels share one result register, `ADC_DR`.
- **Injected group**: up to 4 channels that can cut in and interrupt the regular group; each result goes into its own `ADC_JDRx`.
- **Trigger**: the signal that starts a conversion. It can be software writing the SWSTART bit, or a timer event, or an EXTI line.

| Mode | Key bits | Behavior | Typical use |
| --- | --- | --- | --- |
| Single | `ADC_CR2.CONT = 0` | One trigger, one conversion, then stop | Checking the battery voltage now and then |
| Continuous | `ADC_CR2.CONT = 1` | Starts again at once; the result keeps refreshing | Live monitoring |
| Scan | `ADC_CR1.SCAN = 1` | Converts the listed channels in order; the regular group needs DMA to collect them | Several sensors |
| Discontinuous | `ADC_CR1.DISCEN = 1`, `DISCNUM` picks 1–8 | Each trigger converts only the next few channels on the list | Grouped sampling |
| External trigger | `ADC_CR2.EXTTRIG = 1`, `EXTSEL` picks the source | A timer or EXTI event starts the regular group | Sampling locked to PWM |

The first four rows combine; "scan + continuous + DMA", for instance, is the multi-channel acquisition in the next section. The bit names come from RM0008 Rev 21 sections 11.3 and 11.12. Note that SCAN lives in `ADC_CR1`, not in `ADC_CR2`.

### 6. Multi-channel acquisition and DMA

**Conclusion: the standard way to acquire several channels continuously is "scan + continuous + circular DMA": each time the ADC finishes a channel, DMA moves the result into an array in memory, and the CPU stays out of it.**

DMA (direct memory access) is hardware that only moves data; chapter 10 covers it. Four facts are enough here:

- In scan mode, each finished channel raises one DMA request (`ADC_CR2.DMA = 1`), and DMA moves `ADC_DR` into the array. RM0008 section 11.3.8 requires the DMA bit whenever the regular group runs in scan mode: all regular channels share one `ADC_DR`, and a result that is not collected in time is overwritten by the next channel.
- DMA runs in circular mode. When the array is full it starts again at the beginning, which makes a ring buffer. A half-full interrupt and a full interrupt let you process the first half and then the second.
- Data alignment, `ADC_CR2.ALIGN`: right-aligned (the default; the low 12 bits hold the result) or left-aligned (the high 12 bits).
- Only ADC1 can raise a DMA request: the DMA bit description in RM0008 section 11.12.3 says only ADC1 and ADC3 can generate one, and the C8 has no ADC3. This part has only DMA1, and ADC1 sits on channel 1. Half-word widths and CNDTR counting belong to DMA itself and stay in chapter 10.

When you change family, this table tells you which conclusions survive:

| Item | F1 (RM0008 Rev 21 chapter 11, DS5319 Rev 20) | F4 (RM0090 Rev 22 chapter 13, DS8626 Rev 12) |
| --- | --- | --- |
| Resolution | 12-bit | 12-bit, or 10, 8, or 6 bits |
| Fastest conversion | 1 µs with a 14 MHz ADC clock; at a 72 MHz system clock the ADC clock is 12 MHz and it takes 1.17 µs | 2.4 MSPS; three ADCs interleaved reach 7.2 MSPS |
| Regular / injected group | 16 / 4 | 16 / 4 |
| Conversion time | Sample + 12.5 cycles | Sample + 12 cycles |
| Internal channels | Temperature IN16, VREFINT IN17 | Temperature, VREFINT, VBAT |
| Calibration at power-up | Required | No such step |

Only the 12-bit resolution and the "16 / 4" are the same in both columns; every other row has to be checked again on the other family.

### 7. Calibration, the analog watchdog, and the injected group

**Conclusion: the F1 ADC is calibrated once after power-up, before the first conversion; the analog watchdog interrupts the CPU only when a voltage leaves its window; the injected group can cut in without upsetting the regular group's DMA.**

- **Calibration**: the ADC has a small fixed offset inside, and the F1 can measure it and subtract it. RM0008 section 11.4 recommends a calibration after each power-up, with ADON already 1 for at least two ADC clocks before it starts. The calibration time tCAL in DS5319 Table 47 is 83 ADC clocks, about 6.9 µs at 12 MHz. The HAL function is `HAL_ADCEx_Calibration_Start`.
- **Analog watchdog**: set an upper and a lower limit, and only a result outside them sets a flag and raises an interrupt, so the CPU does not compare every result. The HAL function is `HAL_ADC_AnalogWDGConfig`. It has nothing to do with the chapter 11 watchdogs that reset the chip; only the name is similar.
- **Injected group**: the regular group's DMA keeps running while you occasionally slip in one channel; its result goes to `ADC_JDRx`, not into the regular group's array. The HAL function is `HAL_ADCEx_InjectedStart_IT`. Keep the regular DMA buffer and the injected results in separate arrays.
- **Current**: note 2 of DS5319 Tables 17 and 18 says each ADC draws an extra 0.8 mA while ADON = 1. Switch the ADC off when you are not using it; `HAL_ADC_Stop` clears ADON. Chapter 16 uses this before entering a low-power mode.

### 8. The internal temperature sensor and VREFINT

**Conclusion: ADC1 channel 16 is the on-chip temperature sensor and channel 17 is the on-chip reference VREFINT. VREFINT lets you work out the actual VDDA; the temperature sensor is good for following changes, not for use as a thermometer.**

Temperature sensor (RM0008 Rev 21 section 11.10): set `ADC_CR2.TSVREFE = 1` to switch on both internal channels, select channel 16, and sample for at least 17.1 µs.

```text
V_SENSE = V25 − Avg_Slope × (T − 25)
T (°C)  = (V25 − V_SENSE) / Avg_Slope + 25
DS5319 Rev 20 Table 51: V25 = 1.34 / 1.43 / 1.52 V (min / typ / max)
                        Avg_Slope = 4.0 / 4.3 / 4.6 mV/°C
```

Read these numbers like this: V25 spans ±0.09 V, which divided by 4.3 mV/°C is about ±21 °C. RM0008 section 11.10 also says the offset of this line varies from chip to chip by up to 45 °C, so the manual recommends using it to detect temperature changes, not to measure absolute temperature.

VREFINT is a fairly stable voltage inside the chip. It does not move with VDDA, so its code tells you VDDA:

```text
VDDA         = VREFINT × 4096 / code(channel 17)
real voltage = code(ch) × VDDA / 4096
DS5319 Rev 20 Table 12: VREFINT = 1.16 / 1.20 / 1.24 V (−40 to 85 °C)
```

Read these numbers like this: VREFINT itself varies by about ±3.3% from chip to chip, so a VDDA worked out from the typical 1.20 V carries an error of about the same size. What it does well is catch changes, such as "VDDA is lower than a minute ago". For better accuracy, read the VREFINT code once while VDDA is known, work out this chip's VREFINT, store it, and use it instead of 1.20 V (a common practice, not a manual procedure). Sample time: TS_vrefint in Table 12 is 5.1 µs typical and 17.1 µs maximum, so 239.5 cycles is the safe choice.

> [!NOTE]
> The F4 datasheet (DS8626 Rev 12 Tables 70 and 73) stores factory calibration values in system memory: TS_CAL1 (30 °C), TS_CAL2 (110 °C), and VREFIN_CAL. The F103C8 has none of these; use the typical values or calibrate it yourself.

### 9. DAC output modes, the buffer, and noise

**Conclusion: a DAC (digital-to-analog converter) turns a code back into a voltage. The STM32F103C8 has no DAC. In the F1 family only high-density (F103xC/D/E), XL-density (xF/xG), and connectivity-line parts have one: 12 bits, two outputs, output voltage = VREF+ × DOR / 4096 (RM0008 Rev 21 chapter 12, section 12.3.5).**

| Feature | What it means | Key bits / registers |
| --- | --- | --- |
| Resolution | 12-bit (8-bit also possible), two outputs, each with its own converter | `DHR12Rx` / `DHR12Lx` / `DHR8Rx` |
| Output buffer | When on, it can drive a load directly | `DAC_CR.BOFFx` |
| Trigger | A timer TRGO, EXTI line 9, or software updates the output | `DAC_CR.TENx` / `TSELx` |
| Noise / triangle | Built-in LFSR noise and triangle-wave generators | `DAC_CR.WAVEx` / `MAMPx` |
| DMA | Each output can be refreshed by DMA | `DAC_CR.DMAENx` |

This table holds only on parts that have a DAC. Three things to keep in mind when reading it:

- With the buffer off the output impedance is high, which suits a high-impedance load; with it on the output can drive a load, but it cannot swing all the way to 0 V or VREF+. The output impedance, the offset, and how close it gets to the rails are in that part's own datasheet (DS5792 for F103xC/D/E, for example). The DS5319 this book checks against has no DAC parameters, so no numbers are given here.
- Noise comes from VDDA ripple, coupling from digital switching, buffer noise, and quantization noise. For precision work, add an RC low-pass or an op-amp buffer at the output (practice, not a manual figure).
- For a sine or an arbitrary waveform: a timer trigger plus circular DMA from a lookup table. The trigger rate sets the output frequency.

To get an analog voltage on an STM32F103C8, use PWM plus an RC low-pass (chapter 05), or an external DAC chip.

Motto: **sample time follows impedance, conversion divides by 4096, and the C8 has no DAC.**

## Hardware and wiring

| Board | Function | Pin | Notes |
| --- | --- | --- | --- |
| BluePill | Potentiometer wiper → ADC12_IN0 | PA0 (LQFP48 pin 10) | Configure as analog input |
| BluePill | Analog supply / reference, analog ground | VDDA (pin 9), VSSA (pin 8) | Already wired on the board |
| — | Temperature sensor / VREFINT | On chip, no external pin | ADC1 channels 16 / 17; enable TSVREFE first |
| Parts that have a DAC | DAC_OUT1 | PA4 | PA4 (pin 14) on the STM32F103C8 has no DAC function |

```text
3.3 V ──┐
        │
       [ ]  10 kΩ potentiometer
       [ ]◀── wiper ── PA0 (pin 10, ADC12_IN0, analog input)
       [ ]
        │
GND  ───┘

VDDA (pin 9) is the reference voltage, VSSA (pin 8) is the analog ground
```

Connect the potentiometer ends only to 3.3 V and GND, never to 5 V: DS5319 Table 47 keeps the input between 0 and VREF+, and PA0 is not marked FT either (chapter 03).

## Code

The program below reads three channels every 200 ms: the internal reference, the potentiometer on PA0, and the internal temperature sensor. The results go into global variables that you watch in the debugger's Watch window, so no UART is needed.

```c
/* adc_poll.c -- poll PA0, VREFINT, and the temperature sensor (HAL, STM32F103C8T6) */
#include "stm32f1xx_hal.h"

#define ADC_FULL_SCALE       4096.0f                     /* 12 bits: 2^12 steps */
#define VREFINT_TYP_V        1.20f                       /* DS5319 Table 12 typical, range 1.16-1.24 V */
#define V25_TYP_V            1.43f                       /* DS5319 Table 51 typical, range 1.34-1.52 V */
#define AVG_SLOPE_V_PER_C    0.0043f                     /* DS5319 Table 51 typical 4.3 mV/°C */
#define VDDA_NOMINAL_V       3.3f                        /* nominal value until VREFINT has been read */
#define POT_CHANNEL          ADC_CHANNEL_0               /* PA0 = ADC12_IN0 */
#define POT_SAMPLETIME       ADC_SAMPLETIME_13CYCLES_5   /* 1.125 µs at 12 MHz, example setting */
#define INTERNAL_SAMPLETIME  ADC_SAMPLETIME_239CYCLES_5  /* 19.958 µs, covers 17.1 µs */
#define POLL_TIMEOUT_MS      10U
#define LOOP_PERIOD_MS       200U

ADC_HandleTypeDef hadc1;

/* watch these in the debugger */
volatile uint32_t g_pot_code;
volatile float    g_pot_v;
volatile float    g_vdda_v = VDDA_NOMINAL_V;
volatile float    g_temp_c;

void SystemClock_Config(void);
static void adc1_init(void);
static uint32_t adc1_read(uint32_t channel, uint32_t sampletime);
static void error_handler(void);

int main(void)
{
    HAL_Init();
    SystemClock_Config();          /* 72 MHz, ADCCLK = 72 / 6 = 12 MHz */
    adc1_init();

    while (1)
    {
        uint32_t ref = adc1_read(ADC_CHANNEL_VREFINT, INTERNAL_SAMPLETIME);
        if (ref != 0U)
        {
            g_vdda_v = VREFINT_TYP_V * ADC_FULL_SCALE / (float)ref;
        }

        g_pot_code = adc1_read(POT_CHANNEL, POT_SAMPLETIME);
        g_pot_v    = (float)g_pot_code * g_vdda_v / ADC_FULL_SCALE;

        uint32_t ts  = adc1_read(ADC_CHANNEL_TEMPSENSOR, INTERNAL_SAMPLETIME);
        float vsense = (float)ts * g_vdda_v / ADC_FULL_SCALE;
        g_temp_c     = (V25_TYP_V - vsense) / AVG_SLOPE_V_PER_C + 25.0f;

        HAL_Delay(LOOP_PERIOD_MS);
    }
}

static void adc1_init(void)
{
    GPIO_InitTypeDef io = {0};

    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_ADC1_CLK_ENABLE();

    io.Pin  = GPIO_PIN_0;
    io.Mode = GPIO_MODE_ANALOG;                          /* digital input off; the voltage goes straight to the ADC */
    HAL_GPIO_Init(GPIOA, &io);

    hadc1.Instance                   = ADC1;
    hadc1.Init.ScanConvMode          = ADC_SCAN_DISABLE; /* one channel per conversion */
    hadc1.Init.ContinuousConvMode    = DISABLE;          /* single: stop when done */
    hadc1.Init.DiscontinuousConvMode = DISABLE;
    hadc1.Init.ExternalTrigConv      = ADC_SOFTWARE_START;
    hadc1.Init.DataAlign             = ADC_DATAALIGN_RIGHT;
    hadc1.Init.NbrOfConversion       = 1;
    if (HAL_ADC_Init(&hadc1) != HAL_OK) { error_handler(); }

    /* F1: calibrate once after power-up, before the first conversion */
    if (HAL_ADCEx_Calibration_Start(&hadc1) != HAL_OK) { error_handler(); }
}

static uint32_t adc1_read(uint32_t channel, uint32_t sampletime)
{
    ADC_ChannelConfTypeDef ch = {0};
    uint32_t code = 0U;

    ch.Channel      = channel;
    ch.Rank         = ADC_REGULAR_RANK_1;
    ch.SamplingTime = sampletime;
    if (HAL_ADC_ConfigChannel(&hadc1, &ch) != HAL_OK) { error_handler(); }

    if (HAL_ADC_Start(&hadc1) != HAL_OK) { error_handler(); }
    if (HAL_ADC_PollForConversion(&hadc1, POLL_TIMEOUT_MS) == HAL_OK)
    {
        code = HAL_ADC_GetValue(&hadc1);
    }
    HAL_ADC_Stop(&hadc1);                                /* clears ADON, saves the 0.8 mA */
    return code;
}

void SystemClock_Config(void)
{
    RCC_OscInitTypeDef       osc  = {0};
    RCC_ClkInitTypeDef       clk  = {0};
    RCC_PeriphCLKInitTypeDef pclk = {0};

    osc.OscillatorType = RCC_OSCILLATORTYPE_HSE;
    osc.HSEState       = RCC_HSE_ON;
    osc.HSEPredivValue = RCC_HSE_PREDIV_DIV1;
    osc.PLL.PLLState   = RCC_PLL_ON;
    osc.PLL.PLLSource  = RCC_PLLSOURCE_HSE;
    osc.PLL.PLLMUL     = RCC_PLL_MUL9;                   /* 8 MHz × 9 = 72 MHz */
    if (HAL_RCC_OscConfig(&osc) != HAL_OK) { error_handler(); }

    clk.ClockType      = RCC_CLOCKTYPE_HCLK | RCC_CLOCKTYPE_SYSCLK
                       | RCC_CLOCKTYPE_PCLK1 | RCC_CLOCKTYPE_PCLK2;
    clk.SYSCLKSource   = RCC_SYSCLKSOURCE_PLLCLK;
    clk.AHBCLKDivider  = RCC_SYSCLK_DIV1;
    clk.APB1CLKDivider = RCC_HCLK_DIV2;                  /* 36 MHz */
    clk.APB2CLKDivider = RCC_HCLK_DIV1;                  /* 72 MHz */
    if (HAL_RCC_ClockConfig(&clk, FLASH_LATENCY_2) != HAL_OK) { error_handler(); }

    pclk.PeriphClockSelection = RCC_PERIPHCLK_ADC;
    pclk.AdcClockSelection    = RCC_ADCPCLK2_DIV6;       /* 72 / 6 = 12 MHz, below 14 MHz */
    if (HAL_RCCEx_PeriphCLKConfig(&pclk) != HAL_OK) { error_handler(); }
}

static void error_handler(void)
{
    __disable_irq();
    while (1) { }
}
```

Piece by piece:

- `RCC_ADCPCLK2_DIV6`: PCLK2 = 72 MHz divided by 6 gives a 12 MHz ADC clock. DS5319 Table 47 keeps the ADC clock at or below 14 MHz, and ÷4 would give 18 MHz, which is over. The clock tree is in chapter 02.
- `GPIO_MODE_ANALOG`: PA0 becomes an analog input, with the digital input circuit and the pull resistors disconnected.
- `ADC_SCAN_DISABLE` together with `ContinuousConvMode = DISABLE`: one channel per conversion, then stop. That is single mode, which is why each read first calls `HAL_ADC_ConfigChannel` to switch channel and set the sample time.
- `HAL_ADCEx_Calibration_Start`: the F1 calibrates once after power-up, before the first `HAL_ADC_Start`.
- `ADC_CHANNEL_VREFINT` and `ADC_CHANNEL_TEMPSENSOR`: when the F1 HAL's `HAL_ADC_ConfigChannel` configures either one, it sets TSVREFE for you (this is how the STM32CubeF1 HAL source behaves). Both use 239.5 cycles, which meets the longest requirement, 17.1 µs.
- `if (ref != 0U)`: no division when the code is 0, so there is no divide by zero.
- Every voltage is `code × VDDA / 4096`, with the VDDA just worked out rather than a hard-coded 3.3 V.
- `HAL_ADC_Stop`: clears ADON after each read, so the 0.8 mA is not spent between conversions.
- `HAL_Delay` counts on the SysTick interrupt; `SysTick_Handler` calls `HAL_IncTick()`, and CubeMX generates it in `stm32f1xx_it.c`.

The same single conversion written with registers, to read next to RM0008 section 11.12 bit by bit:

```c
/* Registers: ADC1 single conversion of PA0 (channel 0), 13.5-cycle sample */
RCC->CFGR    = (RCC->CFGR & ~RCC_CFGR_ADCPRE) | RCC_CFGR_ADCPRE_DIV6;  /* 72 / 6 = 12 MHz */
RCC->APB2ENR |= RCC_APB2ENR_IOPAEN | RCC_APB2ENR_ADC1EN;
GPIOA->CRL   &= ~(GPIO_CRL_MODE0 | GPIO_CRL_CNF0);                       /* PA0 analog input */

ADC1->SMPR2 = (ADC1->SMPR2 & ~ADC_SMPR2_SMP0) | (2U << ADC_SMPR2_SMP0_Pos); /* 010 = 13.5 cycles */
ADC1->SQR1  = 0U;                                   /* L = 0000: one conversion in the list */
ADC1->SQR3  = 0U;                                   /* SQ1 = channel 0 */

ADC1->CR2 |= ADC_CR2_ADON;                          /* first ADON write: power up */
HAL_Delay(1);                                       /* wait tSTAB (Table 47, 1 µs max); also covers "two ADC clocks" */
ADC1->CR2 |= ADC_CR2_RSTCAL;
while (ADC1->CR2 & ADC_CR2_RSTCAL) { }              /* reset the calibration registers */
ADC1->CR2 |= ADC_CR2_CAL;
while (ADC1->CR2 & ADC_CR2_CAL) { }                 /* calibration done, hardware clears CAL */

ADC1->CR2 |= ADC_CR2_EXTSEL | ADC_CR2_EXTTRIG;      /* EXTSEL = 111: triggered by SWSTART */
ADC1->CR2 |= ADC_CR2_SWSTART;                       /* start the regular group */
while (!(ADC1->SR & ADC_SR_EOC)) { }                /* wait for end of conversion */
uint16_t code = (uint16_t)ADC1->DR;                 /* reading DR clears EOC */
```

RM0008 section 11.3.1 also lets a second ADON = 1 write start a conversion, but the ADON bit description in `ADC_CR2` adds that if any other bit changes in the same write, no conversion starts. Mixing bits in one write runs into that rule easily, so the code above uses SWSTART.

For continuous multi-channel acquisition use DMA; the full code is in [`examples/adc-dma/`](../../examples/adc-dma/): it scans PA0, PA1, and PA4 with a 55.5-cycle sample each, and DMA1 channel 1 moves the results in circular mode. Calibrate before `HAL_ADC_Start_DMA` as well; handle the first half in the half-transfer callback and the second half in the transfer-complete callback.

A timer trigger (TRGO) makes the sample interval independent of the main loop. This is a fragment; the TIM3 time base setup is in chapter 05:

```c
/* every TIM3 update event starts one regular-group conversion */
hadc1.Init.ExternalTrigConv = ADC_EXTERNALTRIGCONV_T3_TRGO;   /* EXTSEL = 100: TIM3_TRGO */
if (HAL_ADC_Init(&hadc1) != HAL_OK) { error_handler(); }

TIM_MasterConfigTypeDef mst = {0};
mst.MasterOutputTrigger = TIM_TRGO_UPDATE;
mst.MasterSlaveMode     = TIM_MASTERSLAVEMODE_DISABLE;
HAL_TIMEx_MasterConfigSynchronization(&htim3, &mst);

HAL_ADC_Start(&hadc1);        /* the ADC waits for TIM3_TRGO */
HAL_TIM_Base_Start(&htim3);   /* sample interval = TIM3 update period */
```

The next block is only for chips that have a DAC. The STM32F103C8 device header has no DAC and does not define `DAC_BASE`, so the preprocessor skips this block; do not assume it did anything on a BluePill:

```c
/* Fragment: builds only on a part with a DAC, e.g. STM32F103RC; assumes CubeMX has initialized hdac */
#if defined(DAC_BASE)
HAL_DAC_Start(&hdac, DAC_CHANNEL_1);
HAL_DAC_SetValue(&hdac, DAC_CHANNEL_1, DAC_ALIGN_12B_R, 2048); /* 2048 / 4096 = 1/2, which is 1.65 V at a nominal 3.3 V */
#endif
```

The full project is in [`examples/adc-dma/`](../../examples/adc-dma/).

## Hands-on labs

1. **Lab 1: the potentiometer reading follows the knob.** Wire the wiper of a 10 kΩ potentiometer to PA0 and its ends to 3.3 V and GND, then run the program above.
   - Expected: `g_pot_code` moves steadily from near 0 to near 4095 as you turn the knob; in the middle it is about 2048 and `g_pot_v` is about 1.65 V.
   - How to check: measure PA0 to GND with a multimeter and compare with `g_pot_v`. A difference of a few millivolts up to a dozen or so is normal (rule of thumb), because VDDA is worked out from the typical VREFINT.
   - If it fails, check first: is PA0 in analog mode; is the ADC clock on, and is it 12 MHz; is one end of the potentiometer unconnected, leaving the wiper floating.
2. **Lab 2: work out VDDA from VREFINT.** Watch `g_vdda_v`, then measure VDDA on pin 9 with a multimeter (on a BluePill that is the 3.3 V header row).
   - Expected: `g_vdda_v` is near 3.3 V. VREFINT varies from 1.16 to 1.24 V between chips, so it may differ from the meter by about ±3%.
   - How to check: compute this chip's VREFINT as "meter reading × code / 4096", put it into `VREFINT_TYP_V`, rebuild, and the two numbers should agree. Then lower VDDA to 3.0 V with a bench supply; `g_vdda_v` should follow.
   - If it fails, check first: is channel 17 read on ADC1; is the sample time 239.5 cycles; is VDDA hard-coded to 3.3.
3. **Lab 3: a short sample lets the previous channel drag the reading.** Build a divider from two 100 kΩ resistors (source impedance 100 kΩ ∥ 100 kΩ = 50 kΩ), connect the midpoint to PA1 (ADC12_IN1), and configure PA1 as an analog input. Turn the potentiometer to its GND end so PA0 is at 0 V. Each time, read PA0 and then PA1 straight after; take 100 PA1 readings at 1.5 cycles and 100 at 55.5 cycles.
   - Expected: at 1.5 cycles the PA1 code leans clearly toward 0 V and varies a lot from reading to reading; at 55.5 cycles it settles near 2048 (the exact value moves a little with resistor tolerance).
   - How to check: compute the mean and the max-minus-min of each set. Then drop the "read PA0 first" step; the 1.5-cycle error shrinks clearly, which shows the error comes from the voltage the previous channel left on the capacitor.
   - If it fails, check first: the actual resistor values; whether PA1 is configured as an analog input; whether each PA1 read calls `HAL_ADC_ConfigChannel` again to set its sample time.

## Self-test

1. With a 12 MHz ADC clock and a 55.5-cycle sample, how long does one conversion take? And with 239.5 cycles?
2. A divider made of two 20 kΩ resistors (source impedance 10 kΩ) is connected to PA1. What is the shortest sample step you may choose at 12 MHz? Why is 1.5 cycles not enough?
3. The VREFINT code is 1520. Using the typical value, what is VDDA? If this chip's VREFINT is really 1.16 V, is the computed VDDA too high or too low, and by how much?
4. Someone changes ADCPRE from ÷6 to ÷4 to convert faster. What happens?
5. The temperature channel gives V_SENSE = 1.38 V. What temperature is that with the typical values? Can you use the number directly as room temperature?

Answers:

1. (55.5 + 12.5) / 12 MHz = 68 / 12e6 ≈ 5.67 µs; (239.5 + 12.5) / 12 MHz = 252 / 12e6 = 21 µs.
2. t_S > (10 + 1) kΩ × 8 pF × 9.704 ≈ 0.854 µs, which is about 10.2 cycles at 12 MHz, so choose 13.5 cycles (1.125 µs). 1.5 cycles is only 125 ns; the capacitor does not get within 1/4 LSB, and the reading leans toward the previous voltage.
3. VDDA = 1.20 × 4096 / 1520 ≈ 3.234 V. If VREFINT is really 1.16 V, the true VDDA = 1.16 × 4096 / 1520 ≈ 3.126 V, so the value computed with 1.20 V is too high, by 1.20 / 1.16 − 1 ≈ 3.4%.
4. The ADC clock becomes 72 / 4 = 18 MHz, above the 14 MHz limit in DS5319 Table 47, and the results are no longer guaranteed. Change it back to ÷6, 12 MHz.
5. T = (1.43 − 1.38) / 0.0043 + 25 ≈ 11.6 + 25 ≈ 36.6 °C. Not directly: the V25 range of 1.34–1.52 V alone allows about ±21 °C of error, RM0008 says the chip-to-chip offset reaches 45 °C, and the sensor measures the chip's own temperature anyway. Use it to see whether the temperature went up or down.

## Principle and scope

> [!NOTE]
> From this section to "Pitfalls and sources" is the deep part. It pins the conclusions above to one part number, one manual section, and numbers you can recompute. On a first read you can skip it and come back after the labs.

The sampling conclusions in this chapter are pinned to order code STM32F103C8T6 (LQFP48), with the 12 MHz sample clock from Appendix D and a conversion divisor of 4096. On a part that has a DAC, the sentence "this part has no DAC" is void; on an F4, the sentences "sample plus 12.5" and "calibrate after power-up" are void.

**Clock.** PCLK2 = 72 MHz, and `ADCPRE=10` (÷6) gives ADCCLK = 12 MHz; ÷4 gives 18 MHz and crosses 14 MHz. The prescaler details are cross-referenced to chapter 02, and this chapter does not redraw the clock tree. RM0008 prints `Tconv = 1 µs` at 14 MHz and 1.5 cycles; that is an example at the ceiling. This part's working point is 12 MHz, so the four blocks never put 1 µs and 21 µs in the same cell. Source: [RM0008 Rev 21 chapter 11](#source-rm0008-adc).

**Conversion time.** While the sample switch is closed, the input charges the sample capacitor through the source impedance; when it opens, the voltage on the capacitor is held, and the converter compares 12 times starting at the MSB. Conversion time is the sample cycles plus 12.5 ADCCLK cycles. The longest sample step, 239.5 plus 12.5, is 252 cycles, and `252 / 12e6 = 21 µs`. At 12 MHz: 1.5 cycles = 125 ns, 13.5 cycles = 1.125 µs, 55.5 cycles = 4.625 µs, 71.5 cycles = 5.958 µs, and 239.5 cycles = 19.958 µs. The F4 sentence "sample plus 12 cycles" is void on this part.

**Temperature and VREFINT.** The recommended sample time for the temperature sensor is 17.1 µs. `17.1e-6 × 12e6 = 205.2` cycles, so 239.5 cycles covers it and 71.5 cycles does not. The channel is ADC1 input 16, and VREFINT is ADC1 input 17. For VREFINT the text gives only the typical 1.20 V and does not invent a measured VDDA for one board. TSVREFE is in `ADC_CR2`; on a dual-ADC device that bit is only in ADC1, and ADC2 channels 16 and 17 are tied to VSS. The temperature formula is `(V25 − VSENSE) / Avg_Slope + 25`; V25 ≈ 1.43 V and a slope of ≈ 4.3 mV/°C are typical values from the electrical characteristics, not a guaranteed calibration, and RM0008 Rev 21 section 11.10 adds that the offset varies by up to 45 °C between chips. F4 `TS_CAL1`, `TS_CAL2`, and `VREFIN_CAL` are void on F103C8.

**How many ADCs, and whether there is a DAC.** DS5319 says every medium-density device has two 12-bit ADCs. The C8 has ADC1 and ADC2, no ADC3, and no DAC, so `HAL_DAC_Start` does nothing useful on this part. In the F1 family only high-density, XL-density, and connectivity-line parts have a DAC (the opening of RM0008 Rev 21 chapter 12), and F4 parts have one too. The buffer, noise, and triangle wave in core section 9 hold only after you move to a part that has a DAC. Source: [DS5319 Rev 20](#source-ds5319-adc).

**Pins and reference.** LQFP48 pin 10 PA0 = ADC12_IN0, and pin 9 VDDA is the reference: DS5319 Rev 20 Table 47 note 3 says that in LQFP packages VREF+ is connected to VDDA inside the chip and VREF− to VSSA, so this package has no separate VREF+ pin. Pin 10 is the external-LED current pin in chapter 03; when this chapter uses it as an analog input, the chapter 03 sentence "write 1 to source current" is void at the same time, and `sample-03-gpio-led.svg` is not redrawn. Pin 14 PA4 on the C8 is ADC12_IN4 / SPI1_NSS, not DAC_OUT1; a DAC drawn on pin 14 is a failure note in the margin.

**Conversion.** Voltage = code × VDDA / 4096. At a nominal 3.3 V, 1 LSB = `3.3 / 4096 ≈ 0.806` mV, the same sum as the 806 µV in the core table. Code 2048 is `2048 / 4096 = 1/2`, exactly 1.65 V at a nominal 3.3 V. A divisor of 4095 makes the result too large, by at most one LSB.

**Calibration.** RM0008 section 11.4: calibrate once after power-up; before CAL is set in `ADC_CR2`, ADON has already been 1 for at least two ADC clocks. On the HAL side that is `HAL_ADCEx_Calibration_Start`, placed before Start. An F4 does not have this step, and the sentence is void when the family changes.

**DMA.** Only a cross-reference to chapter 10 and Appendix D: this part has only DMA1, and ADC1 is channel 1. The half-word and "5 samples already written" arithmetic does not move into this chapter.

## Key figures

<p align="center">
  <img src="../../assets/diagrams/sample-09-adc-sar.svg" width="760" alt="On this part the ADC clock is 12 MHz and the longest conversion is 21 µs; a sample that is too short leaves the previous voltage on the capacitor">
  <br><sub>▲ Drawn for this book. STM32F103C8T6, LQFP48 pin 10 PA0 = ADC12_IN0, pin 9 VDDA is the reference. ADCCLK = 12 MHz. The normal path closes the sample switch and then opens it, and the comparator takes the MSB step. The longest step is 239.5 + 12.5 = 21 µs, and the code is multiplied by VDDA / 4096. The failure path is a sample so short that the capacitor still holds the previous voltage. In the margin, ÷4 produces 18 MHz and crosses 14 MHz; a DAC drawn on pin 14 does not exist on the C8. The chapter 03 LED resistor is not on this figure. Sources: [RM0008 Rev 21 chapter 11](#source-rm0008-adc) and [DS5319 Rev 20 Figure 8](#source-ds5319-adc).</sub>
</p>

<p align="center">
  <img src="../../assets/gif/adc-sample.gif" width="640" alt="One sample, then the MSB compare, with ADCCLK at 12 MHz">
  <br><sub>▲ Auxiliary figure for the web and the article channel. It only plays one successful sample and the MSB. Print uses the static figure. The short sample and 18 MHz are not on this GIF.</sub>
</p>

The main figure draws one conversion as two paths. The upper one is normal: the sample switch closes, the capacitor charges fully, the switch opens, the comparator makes the first (MSB) comparison, and the result times VDDA / 4096 becomes a voltage again. The lower one is the failure: the sample is too short, the capacitor still holds the previous voltage, and the reading is dragged toward the previous channel, which is exactly what Lab 3 shows. The GIF plays only the successful conversion. The opening `adc-sar.svg` is the animated side figure; `sar-adc.gif` in core section 3 stays where it is, and its pixels are not replaced.

## Timing and state

Every cell in this table can be recomputed as "cycles ÷ 12 MHz":

| Row | Sample cycles | Sample time | After adding 12.5 |
| --- | --- | --- | --- |
| Shortest | 1.5 | 125 ns | 14 / 12e6 ≈ 1.17 µs |
| Longest | 239.5 | 19.958 µs | 252 / 12e6 = 21 µs |
| Temperature | 239.5, not 71.5 | 17.1 µs needs 205.2 cycles | 71.5 cycles is only 5.958 µs and does not cover it |
| Failure | — | — | ADCCLK = 18 MHz, which crosses 14 MHz. This row is not divided again into a second set of microseconds beside 21 µs |
| Conversion | — | — | Code 2048 is 1.65 V at a nominal 3.3 V, divisor 4096 |

The clock is 12 MHz. Source: [RM0008 Rev 21 chapter 11](#source-rm0008-adc).

A software-triggered single conversion goes through these states in order: the first ADON write powers the ADC up, then wait tSTAB (1 µs maximum in DS5319 Table 47); calibrate (83 ADC clocks); write SWSTART; sample for the chosen cycles; 12.5 cycles of successive approximation; EOC goes to 1; read `ADC_DR`, which clears EOC. Clearing ADON puts the ADC back into power-down.

## Pitfalls and sources

| Symptom | Cause | What to do | Source | What the source supports |
| --- | --- | --- | --- | --- |
| The reading is still near the previous voltage | The sample time used the wrong clock, or is too short for the source impedance | Recompute at 12 MHz and lengthen the sample; use 239.5 cycles for a high impedance | [RM0008](#source-rm0008-adc) | Conversion time = sample + 12.5; at 12 MHz the longest 252 cycles is 21 µs |
| ADC was set to ÷4 to go faster | ADCPRE selected ÷4 | Change it back to ÷6, 12 MHz | [RM0008](#source-rm0008-adc) | 14 MHz is the ceiling and 18 MHz crosses it; the 1 µs example is at 14 MHz, not this part's working point |
| A high-impedance sensor reads low and jumps around | The source impedance is above 50 kΩ, outside the specification however long the sample | Put an op-amp follower in front | [DS5319](#source-ds5319) | Table 47: R_AIN is at most 50 kΩ; Equation 1 links the sample time to the source impedance |
| The temperature channel is noisy and the reading wanders | The sample does not cover 17.1 µs, or the channel is wrong | Cover at least 17.1 µs, use ADC1 channel 16, and set TSVREFE | [RM0008](#source-rm0008-adc) | 17.1 µs is 205.2 cycles at 12 MHz; VREFINT is ADC1 channel 17; ADC2 inputs 16 and 17 are tied to VSS |
| Readings after power-up are all shifted a little | There was no calibration | Calibrate once before Start | [RM0008](#source-rm0008-adc) | Section 11.4: ADON has been 1 for at least two ADC clocks before CAL |
| The converted value is slightly above the 4096-based one | The divisor was 4095 | Use 4096 | [DS5319](#source-ds5319-adc) | Both ADCs are 12-bit, and 4096 = 2^12; the reference is pin 9 VDDA |
| Scanning several channels, the results overwrite each other in the array | The regular group scans without DMA | Set the DMA bit and let DMA1 channel 1 move the data | [RM0008](#source-rm0008) | Section 11.3.8: the DMA bit must be set when the regular group uses scan mode |
| DMA is enabled on ADC2, but the array never updates | Only ADC1 can raise a DMA request | Put the channels on ADC1 | [RM0008](#source-rm0008) | The DMA bit description in `ADC_CR2`: only ADC1 and ADC3 can generate a DMA request |
| HAL_DAC_Start on a Blue Pill leaves no analog voltage on PA4 | This C8 has no DAC | For an analog voltage use PWM plus an RC, or change to a part that has a DAC | [DS5319](#source-ds5319-adc) | Medium-density devices have two 12-bit ADCs; there is no ADC3 and no DAC; pin 14 is not DAC_OUT1 |
| Pin 10 used to light an LED, and the sample looks like a push-pull read | The pin is still in output mode | Configure the pin as an analog input before sampling; it no longer sources the chapter 03 current | [DS5319](#source-ds5319-adc) | LQFP48 pin 10 PA0 is ADC12_IN0; the chapter 03 LED figure is not rewritten |

Crosstalk between channels during a scan has no row of its own: "lengthen the sample, or put a low-impedance channel between two high-impedance ones" is practice, and neither RM0008 nor DS5319 gives a number for it, so it is not cited as a manual figure. Lab 3 lets you see it for yourself.

## Related resources

- RM0008, Chapter 11 ADC, and Chapter 12 DAC (the DAC exists only on high-density parts).
- Datasheet DS5319: ADC pins, sample time, and source impedance.
- Example: [`examples/adc-dma/`](../../examples/adc-dma/).
- Figures: [`assets/animations/adc-sar.svg`](../../assets/animations/adc-sar.svg), [`assets/gif/sar-adc.gif`](../../assets/gif/sar-adc.gif) (drawn by the author / program-generated, not a live recording).

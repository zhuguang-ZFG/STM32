# 16 Low-Power Design
> 中文：[16 低功耗设计](../16-低功耗设计.md)

> A battery-powered device uses three gears — Sleep, Stop, and Standby — to push the current from tens of milliamps down to a few microamps, and it wakes only when an event or the RTC asks it to.

<p align="center">
  <img src="../../assets/animations/lowpower-wakeup.svg" width="760" alt="Sleep, Stop, and Standby, and the sources that wake each one">
  <br><sub>▲ Animation: the three low-power modes, Sleep / Stop / Standby, and their wake sources (vector animation drawn by the author, not a live recording)</sub>
</p>

<!-- video:ch16 -->
<p align="center">
  <video width="640" controls poster="../../assets/video/ch16-lp.png">
    <source src="../../assets/video/ch16-lp.mp4" type="video/mp4">
  </video>
  <br><sub>▲ Chinese voice-over, 2.5 min. Voice: Microsoft Edge neural voice zh-CN-XiaoxiaoNeural via edge-tts (library mostly LGPLv3; the voice model is an online Microsoft service, not an open model). Pictures are generated from this repo's SVGs, not photographs. Video: <a href="../../assets/video/ch16-lp.mp4">MP4</a> · subtitles: <a href="../../assets/video/ch16-lp.srt">SRT</a>. Rebuild with <code>python3 tools/gen_narrated.py --speak</code>.</sub>
</p>

**Narration script (Chinese, same text as the subtitles)**

1. Sleep 只是 CPU 停了，不少外设还在耗电。Stop 会停掉大部分时钟，才算真的睡。Standby 更接近掉电，醒来像复位。先分清你要的是哪一种。
2. 从 Stop 醒来，PLL 通常已经停了，系统时钟回到默认。第一件事是把时钟按你的配置再装回去。不装就去用串口和定时器，波特率和节拍全是错的。
3. 可编程电压检测是掉电通知，不是备用电池。电压跌到门槛时，你还有很短的时间把关键数据写进备份域或闪存。不要等它真的掉下去再保存。
4. 这一帧是仓库画的唤醒路径。引脚或 RTC 可以把你叫起来。叫起来不等于世界还是睡前那样。时钟、引脚的复用，该恢复的要在进业务之前恢复。
5. 调试器接着的时候，芯片往往睡不深，电流也不诚实。测睡眠电流要拔掉调试器，卸掉亮着的灯。手册封面上的微安是芯片的典型值，不是你这块板子的读数。
6. 进低功耗之前，不用的外设时钟关掉，不用的脚不要浮空。浮空的脚会在中间电平上来回，漏电比你省下来的还多。模拟输入常常是睡眠前比较安静的一种模式。
7. 唤醒源要在睡着之前武装好。用按键就配置好边沿和中断，用 RTC 就设好闹钟。醒来把标志清掉，不然你刚睡下又会被同一面旗叫起来。
8. 口诀：掉电检测是通知；Sleep 还在耗电，Stop 才真的睡。Stop 醒来第一件事，是把时钟装回去。
9. 实验在进 Stop 之前用串口打一句，按键唤醒后再打一句。第二句的波特率如果乱了，就是时钟没装回去。不要先用万用表追求微安。
10. 合上书，三问。Sleep 和 Stop，谁还在让很多外设耗电？从 Stop 醒来第一件事是什么？手册上的微安能不能直接当成整块板的电流？
<!-- /video:ch16 -->
## Principle and boundary

The working point is Stop on STM32F103C8T6 with the regulator in low-power mode, which is `PWR_LOWPOWERREGULATOR_ON`. The current cells are the DS5319 Rev 20 Table 16 typicals at 3.3 V and 25°C. See [DS5319 Table 16](#source-ds5319-pwr).

Low-power regulator, oscillators off, independent watchdog off: 14 µA. Main regulator still on, same other conditions: 24 µA. 20 µA is not a Table 16 cell. The 85°C values 200 µA and 180 µA are maximums, not typicals. 1.4 µA is `IDD_VBAT` for the backup domain with LSE and the RTC on. It is not the whole-chip Standby current.

Standby has three cells. 2 µA belongs only to the cell with LSI, IWDG, LSE, and RTC all off. LSI on is 3.2 µA. LSI and IWDG both on is 3.4 µA. The IWDG keeps counting in Stop and Standby, the same sentence as chapter file 11. The 14 µA cell says the independent watchdog is off. Quoting 14 µA while the IWDG is on is the failure note. Table 16 does not print a separate Stop-plus-IWDG microamp, so this chapter does not invent one. See [RM0008 watchdog](#source-rm0008-wdg).

Sleep at 72 MHz is 14.4 mA typical with every peripheral on, and 5.5 mA typical with every peripheral off, still at 25°C and 3.3 V.

After Stop exits, the system clock is the 8 MHz HSI, not 16 MHz and not 72 MHz. See [RM0008 clocks](#source-rm0008-rcc). Table 26's 5.4 µs is the low-power-regulator cell, from the wake event to the first user instruction, still on that 8 MHz clock. The main-regulator cell is 3.6 µs. Sleep is 1.8 µs and keeps the clock from before the sleep. Standby is 50 µs to the first instruction, then the reset path. The PLL lock maximum is 200 µs. Do not add it to 5.4 µs and call the sum the wake-up time.

PPRE2 is not divided on this book's clock tree. Before `SystemClock_Config()`, the USART1 kernel clock is 8 MHz. If BRR is still `0x271`, `8e6 / (16 × 39.0625) = 12800`. A host that is still at 115200 is off by a factor of 9. The normal path restores the PLL to 72 MHz before the next byte, and the line is 115200 again. See [RM0008 USART](#source-rm0008-usart). Do not redraw the chapter 06 frame.

Sleep keeps the clock from before the sleep. The tick in `examples/freertos-task` is 1000 Hz, which is 1 ms. Left at that rate, Sleep wakes every 1 ms. SysTick does not tick during Stop. See [examples in this repo](#source-project-examples).

With `PDDS=1`, SRAM and the ordinary registers are lost, and wake-up enters through the reset vector. WKUP is a rising edge on pin 10 PA0. A falling EXTI can wake Stop. It is not Standby's WKUP. See [DS5319 pin 10](#source-ds5319-adc). The 270 Ω lamp from chapter file 03 and ADC12_IN0 from chapter file 09 are other uses of this pin. This chapter does not connect them at the same time.

The F4 periodic wake-up timer is void on this part. Timed wake is the chapter 11 alarm: 32.768 kHz, PRL = 32767. See [RM0008 RTC](#source-rm0008-rtc).

## Key figures

<p align="center">
  <img src="../../assets/diagrams/sample-16-stop-wake.svg" width="760" alt="Stop with the low-power regulator is 14 µA typical. Wake-up is the 8 MHz HSI. Leaving 0x271 in place produces 12800 bit/s.">
  <br><sub>▲ Drawn for this book. STM32F103C8T6, LQFP48. The normal path is SLEEPDEEP=1, PDDS=0, 14 µA at 3.3 V and 25°C with the IWDG off, the first instruction on the 8 MHz HSI after 5.4 µs, then the PLL back at 72 MHz so 0x271 is 115200 again. The failure path leaves that same 0x271 on 8 MHz and gets 12800 bit/s. The main-regulator cell is 24 µA. Source: [DS5319 Rev 20 Tables 16 and 26](#source-ds5319-pwr).</sub>
</p>

<p align="center">
  <img src="../../assets/gif/stop-wake.gif" width="640" alt="Wake from Stop, move the clock from the 8 MHz HSI back to 72 MHz, then mark 115200">
  <br><sub>▲ Auxiliary figure for the web and for posts. It plays only the normal path: wake from Stop, move from 8 MHz back to 72 MHz, and mark 115200. Print from the static figure. 12800 and 24 µA are not on this GIF.</sub>
</p>

`lowpower-wakeup.svg` stays as an auxiliary figure. Do not play it for 14 µA, 8 MHz, or 12800. Those are on the static figure.

## Timing or state

| Step | Clock or current | Right or wrong |
| --- | --- | --- |
| Enter Stop, low-power regulator, no IWDG | 14 µA at 3.3 V and 25°C | right |
| Same mode with the main regulator on | 24 µA | not the 14 µA cell |
| Wake, low-power regulator | first instruction after 5.4 µs, HSI 8 MHz | right |
| Main-regulator wake | 3.6 µs | not 5.4 µs |
| Sleep | 1.8 µs, on the clock that was already running | right |
| Restore | USART1 is 115200 after the PLL is back at 72 MHz | right |
| No restore, `0x271` still loaded | 12800 at 8 MHz | wrong |
| Sleep, 72 MHz, peripherals on | 14.4 mA | right |
| Sleep, peripherals off | 5.5 mA | right |
| SysTick at 1000 Hz | wakes every 1 ms | true in Sleep, not during Stop |
| Standby, `PDDS=1` | restart from the reset vector; 50 µs to the first instruction | right |
| Standby current | 2 µA only with LSI, IWDG, LSE, and RTC off; LSI on is 3.2 µA; IWDG on as well is 3.4 µA | do not write 2 to 3 µA |
| Backup domain | 1.4 µA with LSE and the RTC on | not whole-chip Standby |
| Pin 10 PA0 | the Stop key uses rising-edge WKUP, or this chapter's EXTI | not drawn as a lamp and an ADC at the same time |

## Pitfalls and source cards

| What you see | Why | What to do | Source | Claim this source may support |
| --- | --- | --- | --- | --- |
| The manual folds the two Stop cells into one range | Two cells were folded into one range | Write 14 µA for the low-power regulator and 24 µA for the main regulator | [DS5319](#source-ds5319-pwr) | Both cells are typicals at 3.3 V and 25°C, with the independent watchdog off. 20 µA is not a Table 16 cell |
| Standby is quoted as 2 to 3 µA | Three cells were folded into one range | Write 2 µA, 3.2 µA, or 3.4 µA according to LSI and IWDG | [DS5319](#source-ds5319-pwr) | The 2 µA cell requires LSI, IWDG, LSE, and RTC all off. 1.4 µA is the backup domain, not the whole chip |
| The first UART frame after wake is garbage | The clock is still HSI while BRR was computed for 72 MHz | Call `SystemClock_Config()` before the next byte | [RM0008 USART](#source-rm0008-usart) | With the HSI at 8 MHz and BRR still `0x271`, the baud rate is 12800. 115200 is the 72 MHz cell |
| A comment writes two HSI frequencies onto this part | Another family's 16 MHz was written onto this part | Write 8 MHz on this part | [RM0008 clocks](#source-rm0008-rcc) | The F1 power-up HSI is 8 MHz. 16 MHz is void on the C8 |
| Sleep current will not fall, and the comment says once per second | The tick was left at 1000 Hz | That is every 1 ms, not once per second. Suspend the tick before Sleep | [examples in this repo](#source-project-examples) | `examples/freertos-task` documents a 1000 Hz tick, 1 ms. This row does not show that SysTick keeps ticking during Stop |
| The F4 periodic wake API was called | This part does not have that timer | Use the chapter 11 RTC alarm | [RM0008 RTC](#source-rm0008-rtc) | Timed wake on the F103 is not that F4 API. PRL = 32767 is 1 Hz |
| 14 µA is quoted while the IWDG is on | That cell excludes the independent watchdog | Do not cover a running IWDG with 14 µA | [RM0008 watchdog](#source-rm0008-wdg) | The IWDG keeps counting in Stop and Standby. Do not invent a Stop-plus-IWDG microamp |
| A falling edge woke Stop, but Standby stays asleep | Standby's WKUP is a rising edge | Use a rising edge on pin 10 PA0 | [DS5319](#source-ds5319-adc) | Pin 10 is PA0-WKUP. This row does not draw the 270 Ω lamp as active at the same time |## 📌 Learning goals

- [ ] Use one table to state, for Sleep / Stop / Standby, the current, the wake sources, the wake time, and what state is kept.
- [ ] Know the difference between `WFI` and `WFE`, and what wakes each of them.
- [ ] Remember that after STOP wakes you **must reconfigure the clock**, or every peripheral is wrong.
- [ ] Turn off peripherals and clocks you are not using, and put GPIO into a state that does not draw current.
- [ ] Know the selection points for a battery supply, and how to measure the power.

## 🧠 Core ideas

### 1. The three low-power modes compared

**Conclusion**: The more you save, the slower the wake, and the less state you keep. **Sleep keeps the CPU state. Stop keeps SRAM and the registers. Standby loses almost everything (only the RTC and the backup domain remain).**

| Item | Sleep | Stop | Standby |
| --- | --- | --- | --- |
| Core | Stopped (clock off) | Stopped | Powered off |
| Typical current (F1 at 3.3 V, 25°C) | Peripherals on: 14.4 mA. Peripherals off: 5.5 mA | Low-power regulator: 14 µA. Main regulator: 24 µA. Both cells require the independent watchdog off | 2 µA only when LSI, IWDG, LSE, and RTC are all off. LSI on is 3.2 µA. LSI and IWDG on is 3.4 µA. 1.4 µA is the backup domain |
| Clocks | The system clock is still running | HSI / HSE / PLL off; only LSI / LSE | All off; only LSI / LSE |
| SRAM / registers | All kept | All kept | **Lost** (except the backup domain) |
| Wake sources | Any interrupt or event | EXTI (16 lines), RTC, IWDG, USB wake | WKUP pin, RTC alarm, IWDG, NRST |
| Wake time | 1.8 µs, on the clock that was already running | Low-power regulator 5.4 µs, main regulator 3.6 µs, on the 8 MHz HSI. This does not include restoring the PLL to 72 MHz | 50 µs to the first instruction, then a restart from the reset vector |
| After wake | Continues at the instruction after `WFI` | Continues at the instruction after `WFI` (configure the clock first) | **Restarts from the reset vector** |
| Registers | `SLEEPDEEP=0` | `SLEEPDEEP=1`, `PDDS=0` | `SLEEPDEEP=1`, `PDDS=1` |

> A way to remember it: **Sleep is a nap. Stop is a real sleep (when you wake, you reset your watch). Standby is power-off (waking is a reboot).**

### 2. WFI and WFE

**Conclusion**: `WFI` (Wait For Interrupt) wakes on **any interrupt**. `WFE` (Wait For Event) wakes on an **event**. You can raise one yourself with `SEV`, which fits "synchronize a pipeline, or more than one core, without an interrupt."

| Instruction | Wake condition | Notes |
| --- | --- | --- |
| `__WFI()` | An enabled interrupt or event is pending | The one you use most. Any NVIC-enabled interrupt can wake it |
| `__WFE()` | The event register is set (including `SEV` and interrupts) | The event can come from a peripheral or from a software `SEV` |
| `__SEV()` | — | Software sends an event, paired with WFE |

```c
/* Enter Sleep: wait for any interrupt to wake */
__WFI();
```

### 3. Restoring the clock after STOP wakes

**Conclusion**: Entering Stop turns HSE and the PLL off. **After wake, the system clock is the 8 MHz HSI**, not 16 MHz. Call `SystemClock_Config()` again. If BRR is still `0x271`, the line is 12800 bit/s, not 115200.

```c
/* After wake you must reconfigure the clock */
HAL_PWR_EnterSTOPMode(PWR_LOWPOWERREGULATOR_ON, PWR_STOPENTRY_WFI);
SystemClock_Config();          /* ← bring the PLL back up and restore 72 MHz */
```

| What you see after wake | Cause | Fix |
| --- | --- | --- |
| UART garbage | The clock is now HSI, so the baud rate is wrong | Call `SystemClock_Config()` after wake |
| The timer runs slow | SYSCLK is lower | Same fix: rebuild the clock tree |
| A peripheral does not work | Its clock was not restored | Enable the peripheral clocks you need again |

### 4. Turning peripherals off and configuring GPIO

**Conclusion**: Saving power is not only about entering the mode. It is also about **turning off clocks of peripherals you do not need, and putting GPIO into a state that does not draw current.** A floating input pin leaks because the input buffer toggles.

| What to handle | What to do | Why |
| --- | --- | --- |
| Peripheral clocks | `__HAL_RCC_xxx_CLK_DISABLE()` | A clock on an unused peripheral is wasted current |
| Floating input pins | Set them to analog input, `GPIO_MODE_ANALOG` | Turns off the Schmitt trigger and stops the toggle leakage |
| Output pins | Drive a fixed level (so there is no load) | A floating output can oscillate |
| Pull-up / pull-down | Disable them when you do not need them | They are a continuous leak |
| Debug port | Turn off the SWD / JTAG pins | The debug logic draws current (`__HAL_RCC_GPIOA_CLK` related) |
| LEDs and divider resistors | Disconnect them with a MOSFET switch | Quiet killers of standby current |

### 5. Battery-powered design

**Conclusion**: On a battery device you **add up the whole budget**. Average current is the active current times the duty cycle, plus the sleep current. Divide the battery capacity by that and you have the runtime.

| Point | What it means |
| --- | --- |
| Average current | `I_avg = I_active × t_active / T + I_sleep` |
| Runtime estimate | `runtime (h) = battery capacity (mAh) / I_avg (mA)` |
| LDO quiescent current | Pick a low-Iq LDO (for example under 1 µA), or the LDO eats the standby budget |
| Pull-up / pull-down | Each 10 kΩ pull-up at 3.3 V is about 0.33 mA. Several of them are fatal |
| Divider sampling | The divider resistors leak all the time. Connect them with a MOSFET only while you sample |
| Watchdog | The IWDG still runs from the LSI in Stop. Plan the feed and the wake |

> Example: both currents below are assumptions, not Table 16 or Table 18 cells. A node wakes for 100 ms every 60 s to sample (assume 20 mA while active) and spends the rest at an assumed 20 µA:
> `I_avg ≈ 20 mA × (0.1/60) + 0.02 mA ≈ 0.053 mA`. On a 1000 mAh battery the theoretical runtime is about **780 days**.

### 6. How to measure power

| Method | Tool | Fits |
| --- | --- | --- |
| Meter in series | A digital multimeter on the µA range | Quiescent current (watch the burden voltage of the range) |
| A dedicated power profiler | Nordic PPK2 / Joulescope | Dynamic waveforms, and average current in one step |
| Sense resistor plus a scope | A 0.1 Ω sense resistor plus a differential probe | The current spike at the moment of wake |
| Measure in pieces | Unplug peripherals one at a time | Find the part that draws the most |

> A measuring tip: the µA range of a multimeter has a large internal resistance. Measuring a dynamic current "drags the voltage down" and you misread it. For dynamic current, use a sense resistor plus a scope, or a dedicated power profiler.

### 7. Low-power design checklist

**Conclusion**: Before you enter the mode, walk this list. Most cases of "standby current will not come down" missed one of these lines.

| Check | What to do | Typical leak / waste |
| --- | --- | --- |
| Clocks | Turn off HSE, PLL, and peripheral clocks you are not using | An unused peripheral clock is wasted current |
| GPIO | Unused pins as analog inputs; output pins at a fixed level | A floating input toggles and leaks |
| Pull-up / pull-down | Keep only the ones you need. Delete the rest | Each 10 kΩ is about 0.33 mA |
| LEDs and indicators | Switch them with a MOSFET. Do not leave them on | One 2 mA LED is already fatal |
| Peripheral supply | Cut VCC to a sensor with a MOSFET when you are not using it | Sensor quiescent current is easy to forget |
| Debug port | Production firmware turns SWD / JTAG off | The debug logic draws current the whole time |
| LDO | Pick a low-Iq part (under 1 µA) | The LDO itself eats the standby current |
| Wake sources | Keep only the interrupts and the RTC you need | Extra interrupts cause extra wakes |
| Watchdog | Plan the feed and the wake while you are in Stop | The IWDG still runs from the LSI in Stop |

> From experience: first turn **everything** that might draw current off, measure a clean floor, then turn things back on one at a time. The difference tells you who the real consumer is.

## 🛠️ Hardware and wiring

| Board | Peripheral | Pin | Notes |
| --- | --- | --- | --- |
| BluePill (F103) | Wake key | PA0 | Falling-edge EXTI. It can wake the chip from Stop |
| BluePill | RTC periodic wake | PC14 / PC15 (LSE) | Solder a 32.768 kHz crystal so you can wake on a schedule |
| BluePill | On-board LED | PC13 | Indicate after wake. Turn it off before you enter, to save power |
| Nucleo-F411RE | On-board key | PC13 (B1) | Can wake the chip from Stop |
| Any | Current measurement | A sense resistor in series with 3V3 | Watch it with a power profiler or a scope |

> ⚠️ On a BluePill, the on-board **LED, the LDO, and the USB chip all leak**. To measure a real microamp current, use a bare-chip minimal board, and disconnect the debugger and the LED.

## 💻 Code

**① Sleep mode (wait for any interrupt)**

```c
#include "stm32f1xx_hal.h"

void Enter_Sleep(void)
{
    HAL_SuspendTick();                    /* In Sleep a 1000 Hz tick wakes the core every 1 ms, not once per second */
    HAL_PWR_EnterSLEEPMode(PWR_MAINREGULATOR_ON, PWR_SLEEPENTRY_WFI);
    HAL_ResumeTick();                     /* restore the tick after wake */
}
```

**② Stop mode, and restoring the clock after wake (the one you use most)**

```c
void Enter_Stop(void)
{
    /* Wake source: EXTI key. Configure NVIC and EXTI beforehand */
    HAL_SuspendTick();
    HAL_PWR_EnterSTOPMode(PWR_LOWPOWERREGULATOR_ON, PWR_STOPENTRY_WFI);
    HAL_ResumeTick();

    /* Critical: after wake the clock falls back to HSI; you must configure it again */
    SystemClock_Config();                 /* restore HSE+PLL = 72 MHz */
}
```

**③ Standby mode (lowest power; wake equals reset)**

```c
void Enter_Standby(void)
{
    /* Clear the WKUP flag and allow the WKUP pin to wake the chip */
    __HAL_PWR_CLEAR_FLAG(PWR_FLAG_WU);
    HAL_PWR_EnableWakeUpPin(PWR_WAKEUP_PIN1);

    HAL_PWR_EnterSTANDBYMode();           /* does not return; wake restarts from the reset vector */
}
```

**④ Timed wake**

STM32F103C8T6 does not have the F4 periodic wake-up timer. Do not call that API. Timed wake is chapter 11: 32.768 kHz, PRL = 32767.

**⑤ Cut GPIO leakage**

```c
/* Before low power, set floating pins to analog input so the input buffer stops toggling and leaking */
GPIO_InitTypeDef io = {0};
io.Pin  = GPIO_PIN_All;
io.Mode = GPIO_MODE_ANALOG;
io.Pull = GPIO_NOPULL;
HAL_GPIO_Init(GPIOA, &io);   /* do this for each unused port */
```

**⑥ Turn off clocks you are not using**

```c
__HAL_RCC_ADC1_CLK_DISABLE();
__HAL_RCC_SPI1_CLK_DISABLE();
__HAL_RCC_USART2_CLK_DISABLE();
/* Keep only the clocks RTC, PWR, and the wake source need */
```


## 🧪 Hands-on labs

1. **Saving power in Sleep**: blink in the main loop, and call `Enter_Sleep()` when idle. Compare the current with and without Sleep (a 0.1 Ω sense resistor in series, and look at the waveform). Expected: the current drops clearly in Sleep.
2. **Stop plus a key wake**: enter Stop, wake on PA0, restore the clock, and toggle the LED. Expected: the key wakes the chip, and the UART is still healthy (which means the clock was restored).
3. **RTC timed wake**: every 5 s, wake from Stop, take one ADC sample (see [Chapter 09](09-adc-dac.md)), and go back to sleep. Expected: the RTC wakes on time, and the average current drops a lot.
4. **(Further) Measure the real standby current**: disconnect the LED and the debugger, enter Standby, and measure the microamp current with a power profiler. Expected: close to the standby typical value in the datasheet.
5. **(Further) Check the runtime estimate**: estimate the runtime with the formula in section 5, then measure the average current and compare. Expected: the estimate and the measurement are in the same order of magnitude.

### 8. The last word before the rail falls: PVD

**Conclusion**: PVD watches VDD. When the voltage falls through the threshold it enters an interrupt, so you can write the critical variables into the backup registers before a real reset. It does not replace the watchdog, and it does not give you a number for "how many milliseconds you still have." The threshold and the hysteresis come from the level table in the reference manual.

```c
PWR_PVDTypeDef pvd = {0};
pvd.PVDLevel = PWR_PVDLEVEL_6;          /* see the RM for the actual voltage; do not memorize the level as a millivolt number */
pvd.Mode     = PWR_PVD_MODE_IT_RISING_FALLING;
HAL_PWR_ConfigPVD(&pvd);
HAL_PWR_EnablePVD();
```

Sleep current is not a fixed 1 mA either. The core is stopped, but the peripheral clocks are still on, and the current is usually still in the milliamp range. Stop is the mode that reaches the microamp range. The numbers in the comparison table above are the order of magnitude from the datasheet. They are not a measurement from a board in this repo. If you are writing them into a paper or a battery budget, open the datasheet for that exact part and copy the column that matches the clocks you turned off.

Motto: **PVD is a power-fail notice. Sleep is still drawing current. Stop is the mode that really sleeps.**

Self-test:

1. Why must you not write the Sleep current down as "about 1 mA at 72 MHz"?
2. What is one thing that belongs in the PVD interrupt, and one thing that does not?
3. After Standby wakes, does the program continue at the line after `WFI`, or does it start again from the reset vector?

## 🔗 Related resources

- RM0008, *STM32F10xxx Reference Manual*, Chapter 5, Power control (PWR) (`LPDS` / `PDDS` / `CWUF` in `PWR_CR`, and WFI / WFE).
- RM0090, *STM32F4 Reference Manual*, Chapter 5 PWR, and Chapter 26 RTC (periodic wake).
- Datasheet DS: typical and maximum current in each mode, wake time, and VBAT parameters.
- Application note AN4365, *How to improve ADC accuracy on STM32F4* (includes notes related to low-power sampling), and ST's application notes on low-power design.
- Related chapters: [Chapter 11](11-rtc-watchdog.md), RTC and the watchdogs, and [Chapter 09](09-adc-dac.md), ADC.
- Figure: `../../assets/animations/lowpower-wakeup.svg` (vector drawing by the author).

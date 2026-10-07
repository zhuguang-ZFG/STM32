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
  <br><sub>▲ Chinese voice-over, 2.5 min. Voice: Microsoft Edge neural voice zh-CN-XiaoxiaoNeural via edge-tts (library mostly LGPLv3; the voice model is an online Microsoft service, not an open model). Pictures are generated from this repo's SVGs, not photographs. Subtitles: <a href="../../assets/video/ch16-lp.srt">SRT</a>. Rebuild with <code>python3 tools/gen_narrated.py --speak</code>.</sub>
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
## 📌 Learning goals

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
| Typical current (F1 at 3.3 V) | About 10 to 20 mA (only the core is stopped) | About 14 to 20 µA | About 2 to 3 µA |
| Clocks | The system clock is still running | HSI / HSE / PLL off; only LSI / LSE | All off; only LSI / LSE |
| SRAM / registers | All kept | All kept | **Lost** (except the backup domain) |
| Wake sources | Any interrupt or event | EXTI (16 lines), RTC, IWDG, USB wake | WKUP pin, RTC alarm, IWDG, NRST |
| Wake time | Immediate | About a few tens of µs (you must reconfigure the clock) | About a few hundred µs to ms (equivalent to a reset) |
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

**Conclusion**: Entering Stop turns HSE and the PLL off. **After wake, the system clock automatically falls back to HSI** (about 8 or 16 MHz). You must call the clock-configuration function again, or the UART baud rate and the timer frequency are all wrong.

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

> Example: a node wakes for 100 ms every 60 s to sample (20 mA while active) and spends the rest in Stop (20 µA):
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
    HAL_SuspendTick();                    /* turn off SysTick, otherwise it wakes the core once a second */
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

**④ RTC periodic wake (paired with Stop, so you wake on a schedule)**

```c
#include "stm32f1xx_hal.h"

RTC_HandleTypeDef hrtc;

void RTC_Wakeup_Config(uint32_t seconds)
{
    /* RTC periodic wake: one wake event every `seconds` seconds */
    HAL_RTCEx_SetWakeUpTimer_IT(&hrtc, seconds - 1,
                                RTC_WAKEUPCLOCK_CK_SPRE_16BITS);  /* F4 style */
}

void HAL_RTCEx_WakeUpTimerEventCallback(RTC_HandleTypeDef *hrtc)
{
    (void)hrtc;
    /* After wake, take one sample, then enter Stop again */
}
```

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

## ⚠️ Pitfalls and troubleshooting

| What you see | Cause | Fix |
| --- | --- | --- |
| You enter Stop and wake immediately | An interrupt flag is already pending | Clear the interrupt flags, then `WFI` |
| UART garbage after wake | The clock was not restored (it is HSI) | Call `SystemClock_Config()` after wake |
| The current never comes down | LED, pull-ups, or LDO quiescent current | Disconnect the LED, remove extra pull-ups, use a low-Iq LDO |
| Stop current is higher than the manual | Floating input pins are toggling | Set unused pins to analog input |
| You cannot enter Stop | The `PWR` clock is not enabled | `__HAL_RCC_PWR_CLK_ENABLE()` |
| A peripheral does not work after wake | Its clock was turned off and not restored | Enable the peripheral clocks you need again |
| The meter reading jumps around | The µA range has a large resistance, so a dynamic reading is wrong | Use a sense resistor plus a scope, or a power profiler |
| After Standby, every variable has changed | Standby loses SRAM | Keep important state in the backup registers / BKP |
| RTC wake is not accurate | You used the LSI, or the prescaler is wrong | Use the LSE, and set the wake period correctly |
| The debugger cannot connect | In low power the SWD clock is stopped | Use `DBGMCU` to keep the debug clock |

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

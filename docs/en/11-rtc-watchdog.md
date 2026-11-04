# 11 RTC and the Watchdogs
> 中文：[11 RTC 与看门狗](../11-RTC与看门狗.md)

> A blinking LED after restart does not prove the watchdog fired. Startup must read IWDGRSTF, a persistent boot_id must increase, and RTC time should continue while main power is absent.

<p align="center">
  <img src="../../assets/animations/iwdg-window.svg" width="760" alt="Animation of the independent watchdog counter and the feed window">
  <br><sub>▲ Side figure. The independent watchdog only punishes a late feed. An early feed that also resets is the window watchdog. Without playing this figure, the 1 second and the reset-at-zero are both on the static figure. (vector animation drawn by the author, not a live recording)</sub>
</p>

<!-- video:ch11 -->
<p align="center">
  <video width="640" controls poster="../../assets/video/ch11-rtc.png">
    <source src="../../assets/video/ch11-rtc.mp4" type="video/mp4">
  </video>
  <br><sub>▲ Chapter video with Chinese voice-over (2.6 min). <a href="../../assets/video/ch11-rtc.mp4">MP4</a> · <a href="../../assets/video/ch11-rtc.srt">subtitles</a></sub>
</p>

<details>
<summary>Narration script (Chinese, same text as the subtitles)</summary>

1. RTC 住在备份域。主电源掉了，只要备用电池和低速晶振还在，日历就能继续走。时钟源优先选外部 32.768 千赫，它比内部低速时钟准。
2. 备份域默认不让你随便写。要先允许访问，再选时钟、设分频。写不进去的时候，多半不是晶振坏了，而是域还锁着，或者写保护没解。
3. 独立看门狗的时钟独立，喂晚了就复位，用来兜底。窗口看门狗喂早喂晚都会复位，用来发现程序走得太快或太慢。两只可以同时在岗。
4. 这一帧是仓库画的看门狗窗口。太早喂，说明程序没有走到该到的地方；太晚喂，说明它卡住了。窗口看门狗把这两种都当成故障。独立看门狗只惩罚迟到。
5. 32.768 千赫晶振起振慢，初始化超时给得太短，会误判失败。真的不起振，再查负载电容和焊接。调试阶段可以暂时改用内部低速时钟，先把日历逻辑跑通。
6. 把喂狗放在一个和业务无关的定时中断里，主循环死锁时狗仍然吃得饱，等于没养。喂狗要放在你确认「这一圈真的走完了」的地方，并且落在窗口里面。
7. 芯片为什么重启，复位标志里有记录。独立看门狗、窗口看门狗、上电，是不同的旗。读完记得清掉，不然下一次你分不清是新的复位还是旧旗。
8. 口诀：独立看门狗只怕喂晚；窗口看门狗喂早喂晚都会复位。RTC 走在备份域，主电掉了还靠备用电池和低速钟。
9. 实验先故意不喂狗，确认它真的会复位，并且复位旗对得上。然后再把喂狗放到主循环里正确的位置。从没被咬过的狗，你不知道它在不在岗。
10. 合上书，三问。主电源掉了，RTC 还靠什么继续走？哪只看门狗喂早了也会复位？为什么不要把喂狗只放在一个无关的定时中断里？

</details>
<!-- /video:ch11 -->

## Principle and scope

Every number in this chapter is for the STM32F103C8T6. The IWDG 1 second matches Appendix D: prescaler 64, Reload = 624, LSI at its typical 40 kHz, which counts at 625 Hz. LSI is an on-chip RC oscillator, and Table 25 gives its range as 30 / 40 / 60 kHz (min / typical / max), so this 1 second is only typical.

`T = 64 / 40000 × (624 + 1) = 1` s. Reload written as 625 adds one count: `(625 + 1) / 625` s. With the same prescaler and reload, LSI = 30 kHz gives `64 / 30000 × 625 = 4/3` s and LSI = 60 kHz gives `64 / 60000 × 625 = 2/3` s, exactly half the 30 kHz figure. Appendix D says "about half" because 30 kHz and 60 kHz are the ends of the datasheet range, not a measurement of any one part. The longest step is about 26 s, also from Appendix D; the manual gives no guaranteed maximum. The independent watchdog resets only when the count reaches 0. An early feed does not reset it. See [RM0008 Rev 21 chapter 19](#source-rm0008-wdg) and [DS5319 Rev 20 Table 25](#source-ds5319-rtc).

The window watchdog (WWDG) is different: it resets on an early feed and on a late one. With PCLK1 = 36 MHz, prescaler 8, and the counter starting at `0x7F`, the timeout is `(1/36e6) × 4096 × 8 × 64 = 58.25` ms. With the window at `0x50`, feeding while the counter is still above `0x50` resets at once.

Some code fragments set Reload to its maximum, 4095. The timeout is then `(4095 + 1) / 625 = 6.5536` s, which is the "about 6.5 s" in the labs. Everywhere else this chapter works with the 624 second.

The RTC runs from the LSE crystal, 32.768 kHz, on pin 3 PC14-OSC32_IN and pin 4 PC15-OSC32_OUT. The RTC divides by `(PRL + 1)`, so PRL = 32767 turns 32768 Hz into 1 Hz, and PRL = 32768 does not. A typical 40 kHz LSI that drifts anywhere in 30–60 kHz has no integer PRL that gives a steady 1 Hz, so an accurate RTC needs the LSE. When the main supply is gone, pin 1 VBAT powers the backup domain. Before writing it, enable the PWR and BKP clocks and set DBP in `PWR_CR`. See [RM0008 Rev 21 chapter 18](#source-rm0008-rtc).

The C8 is medium-density, with ten 16-bit backup data registers, 20 bytes. The figure of 42 in some references is for high-density parts. The F4 RTC is a different design: twenty 32-bit backup registers and a calendar kept in BCD in `TR`/`DR`. The F103 RTC has only a 32-bit seconds counter, and software works out the date.

The IWDG keeps counting in Stop and Standby. It can be frozen while debugging with the chapter's `__HAL_DBGMCU_FREEZE_IWDG()`. RM0008 §19.3.3 prints only the configuration bit name `DBG_IWDG_STOP`, with no bit number. In the option bytes, `WDG_SW = 0` starts the watchdog in hardware at power-up and software cannot stop it; `WDG_SW = 1` leaves the start to software. See [PM0075](#source-pm0075-rdp).

While the LSE uses pins 3 and 4, those pins cannot be GPIO. If PC13 is still the heartbeat LED, chapter 03's rule holds: it can only sink, and writing 0 turns it on. On a high-density part or an F4 the backup-register count above no longer applies; look it up in that part's manual.

## Key figures

<p align="center">
  <img src="../../assets/diagrams/sample-11-iwdg-1s.svg" width="760" alt="Reload 624 is 1 second at a typical 40 kHz; reset happens only at 0; LSE needs PRL = 32767 for 1 Hz">
  <br><sub>▲ Drawn for this book. STM32F103C8T6. LSI is typically 40 kHz and spans 30–60 kHz. Prescaler 64, a 625 Hz count, and Reload = 624 give a 1 second timeout at the typical value, not a guarantee, when the dog is fed before zero. The marked faults are reaching 0 and writing Reload as 625. The backup strip shows pin 1 VBAT, pin 3 PC14, pin 4 PC15, 32.768 kHz, PRL = 32767, and ten 16-bit registers. PRL = 32768 is not 1 Hz. The window watchdog resets if fed while the counter is above 0x50, on a 58.25 ms scale. Sources: [DS5319 Rev 20 Table 25 and sections 2.3.14 and 2.3.15](#source-ds5319-rtc) and [RM0008 Rev 21 chapter 19](#source-rm0008-wdg).</sub>
</p>

<p align="center">
  <img src="../../assets/gif/iwdg-1s.gif" width="640" alt="A 625 Hz count is fed before it reaches 0, with Reload = 624">
  <br><sub>▲ Animated version. A 625 Hz count is fed before it reaches zero, marked with Reload = 624 and a typical 40 kHz. The printed book has only the static figure above.</sub>
</p>

The opening `iwdg-window.svg` shows the window watchdog. "An early feed resets" applies only to the WWDG; an early feed does not reset the IWDG.

## Timing and state

| Prescaler | f_LSI | Reload | (Reload + 1) | Time | Reset? |
| --- | --- | --- | --- | --- | --- |
| 64 | 40 kHz | 624 | 625 | 1 s | Resets only at 0. An early feed does not reset |
| 64 | 40 kHz | 625 | 626 | one extra count | Not exactly 1 second |
| 64 | 30 kHz | 624 | 625 | 4/3 s | Not a guarantee |
| 64 | 60 kHz | 624 | 625 | 2/3 s | About half of the 30 kHz case |
| RTC | 32768 Hz | PRL = 32767 | 32768 | 1 Hz | The divider is (PRL + 1) |
| RTC failure | 32768 Hz | PRL = 32768 | 32769 | not 1 Hz | Change it to 32767 |
| Backup registers | — | ten 16-bit | 20 bytes | Pin 1 VBAT keeps them | 42 is the high-density count |
| WWDG | PCLK1 = 36 MHz | prescaler 8, counter `0x7F` | — | 58.25 ms | Feeding above `0x50` resets |
| Comparison | 64 | 4095 | 4096 | 6.5536 s | Does not replace Reload 624 |

## Pitfalls and sources

| What you see | Why | What to do | Source | What the source shows |
| --- | --- | --- | --- | --- |
| A 1 second computed at 40 kHz runs short or long on the board | 40 kHz is only typical | Use Reload 624 and leave margin for 30–60 kHz | [DS5319](#source-ds5319-rtc) | Table 25 prints fLSI as 30 / 40 / 60 kHz. 40 kHz is typical. That second is not a guarantee |
| Reload written as 625 times out one count past 1 second | The +1 was applied to the wrong side | Change it to 624 | [RM0008](#source-rm0008-wdg) | Prescaler 64 at 40 kHz counts at 625 Hz. Time uses `(Reload + 1)`. 625 is one extra count |
| The independent watchdog resets as soon as it is fed, as if it had a window | It was treated as the window watchdog | An early feed is allowed for the IWDG. Use the WWDG for a window | [RM0008](#source-rm0008-wdg) | The IWDG resets only at 0. The WWDG also resets when fed while the counter is above the window. At 36 MHz, `0x7F` and prescaler 8 time out in 58.25 ms |
| The calendar returns to zero when the main supply drops | The backup domain was not kept, or PRL is wrong | Connect pin 1 VBAT, use pins 3 and 4 for LSE, and write PRL 32767 | [DS5319](#source-ds5319-rtc) | Ten 16-bit backup registers are kept by VBAT. The default 1 second comes from 32.768 kHz. The C8 has 10, not 42 |
| A prescaler of 32768 makes the second pulse slow | The divider is (PRL + 1) | Change it to 32767 | [RM0008](#source-rm0008-rtc) | The divider is `(PRL + 1)`. 32768 Hz is 1 Hz only when written as 32767 |
| The part resets by itself after a breakpoint | The counter kept running in debug | Freeze the IWDG while debugging | [RM0008](#source-rm0008-wdg) | §19.3.3 prints the configuration bit name `DBG_IWDG_STOP`. The independent watchdog can be frozen while debugging. No bit number is given |
| Option bytes make the watchdog run from power-up and software cannot stop it | `WDG_SW` is 0 | 0 is the hardware watchdog and 1 is the software watchdog | [PM0075](#source-pm0075-rdp) | That bit in the USER byte: 0 means the hardware watchdog and 1 means the software watchdog |

## Learning goals

- [ ] Know the trade-offs among the four RTC clock sources (LSE / LSI / HSE/128), and understand the backup domain and VBAT.
- [ ] Save a flag in a BKP backup register and use it to tell whether this is the first power-up.
- [ ] Configure the calendar, the alarm, periodic wake-up, and the timestamp.
- [ ] Explain the difference between IWDG and WWDG, and give a correct feed strategy.
- [ ] Track down "the RTC is not running," "the LSE will not start," and "the watchdog resets by mistake."

## Core ideas

A reset test must distinguish a watchdog reset from ordinary power-on reset. An RTC test must distinguish continued counting from accurate time. Reset cause, persistent state, and elapsed time are separate evidence.

### 1. The RTC and the backup domain

The RTC is a watch inside the chip. It lives with a few backup registers in a separate small room called the backup domain. When main power goes, that room stays powered as long as a coin cell is on the VBAT pin, and the watch keeps running. How accurate it is depends on the clock: an external 32.768 kHz crystal is the most accurate, and the internal LSI is only rough.

The RTC sits in the **backup domain** and is powered by `VBAT`. It keeps time after the main supply drops. Prefer the **LSE at 32.768 kHz** as the clock source. It is the most accurate of the four.

| Clock source | Frequency | Accuracy | Pins used | Fits |
| --- | --- | --- | --- | --- |
| LSE (external 32.768 kHz crystal) | 32.768 kHz | Set by the crystal, often ±20 ppm; check the crystal's datasheet | PC14 / PC15 | When the time has to be right |
| LSI (internal RC) | 30 kHz minimum, 40 kHz typical, 60 kHz maximum | Table 25's range, not ±50% | None | Saving pins, or wake-up only |
| HSE/128 (main crystal divided) | 8 MHz / 128 | Depends on the HSE | Uses the HSE | You already have a precise main crystal |
| RTC prescaler | — | Set by `PRL` | — | Divides the source down to 1 Hz |

- On F1 the RTC is a **32-bit seconds counter**. The calendar (year, month, day, hour, minute, second) is software that converts the second count. F4 and later have a **BCD hardware calendar** (`TR` / `DR`), with the weekday and leap years handled in hardware.
- To touch the backup domain, first enable the `PWR` and `BKP` clocks, then unlock the backup domain (`PWR_CR.DBP`; see RM0008 Chapter 5 PWR and Chapter 6 BKP).

### 2. BKP backup registers

The backup registers are sticky notes in that small room, and they survive a main power loss. The usual trick is a note that says "time already set". At power-up, check for the note. If it is there, read the clock. If it is not, set up the calendar and then leave the note. Otherwise every restart would reset the time.

`BKP_DRx` is powered by `VBAT`. It survives a loss of the main supply. It is the usual place for flags such as "is this the first power-up" and for calibration constants.

| Family | Backup registers | Width |
| --- | --- | --- |
| STM32F103C8T6 | `BKP_DR1` through `BKP_DR10`, ten 16-bit registers, 20 bytes. Forty-two is the high-density count | 16-bit |
| STM32F4 | `RTC_BKP_DR0` through `DR19` | 32-bit |

The usual pattern: on power-up, read a "magic value" (for example `0xA5A5`). If it matches, the calendar was already initialized, so just read the time. If it does not match, write the magic value and initialize the calendar.

### 3. Calendar, alarm, wake-up, and timestamp

The F1 RTC only counts seconds, and software turns the count into a date. An alarm is "tell me when the count reaches this many seconds". From the F4 on, the RTC stores the date and time directly, an alarm can follow a rule such as "every day at 7:00", and there is also periodic wake-up and timestamping, which suit waking from low-power modes on a schedule.

| Feature | What it does | Key registers |
| --- | --- | --- |
| Calendar | Second / minute / hour / day / month / year (F1 converts in software; F4 is hardware BCD) | `RTC_TR` / `RTC_DR` (F4) |
| Alarm | Compared with the counter; at the match it raises an interrupt or an event | `RTC_ALR` (F1) / `RTC_ALRMxR` (F4) |
| Periodic wake-up | Wakes on a fixed period; pairs with STOP to save power | `RTC_WUTR` (F4) |
| Timestamp | A rising edge on a pin records the current time | `RTC_TSTR` / `RTC_TSDR` (F4) |

> On F1 the alarm compares the **seconds counter**. On F4 you can mask-match second, minute, hour, day, month, or weekday, which is more flexible.


<p align="center">
  <img src="../../assets/diagrams/sample-11-wdg-compare.svg" width="760" alt="IWDG resets when the counter reaches 0: Reload 624 is 1 second; WWDG runs 58.25 ms per pass and feeding it while the counter is still above 0x50 also resets">
  <br><sub>▲ Drawn for this book. IWDG counts down and resets at zero: LSI 40 kHz, prescaler 64, Reload 624 is exactly 1 second. WWDG is a windowed countdown: about 58.25 ms per pass, and feeding it while the counter is still above 0x50 also resets — feeding is only allowed inside the window. Sources: [RM0008 watchdog](#source-rm0008-wdg) and [DS5319 Rev 20](#source-ds5319-rtc).</sub>
</p>

### 4. IWDG vs WWDG

A watchdog is a countdown that never stops, and the program has to "feed" it now and then to wind the count back up. If the program hangs, nobody feeds it, the count runs out, and the chip resets. The independent watchdog has its own clock, so it keeps counting even if the main clock fails, which makes it the last line of defence. The window watchdog is stricter: feeding it too late resets the chip, and so does feeding it too early, so it catches a program that runs too fast as well as too slow.

The IWDG has its own clock and can catch a dead hang. It is the **safety floor**. The WWDG is more accurate and has a feed window, so it can **catch a program whose timing has gone wrong**. You can use both at once.

| Item | IWDG (independent watchdog) | WWDG (window watchdog) |
| --- | --- | --- |
| Clock | LSI (independent of the main clock) | PCLK1 (APB1) |
| Counter | 12-bit down-counter plus an 8-bit prescaler | 7-bit down-counter (`T[6:0]`) |
| Reset condition | Not refreshed before the counter reaches 0 | **Too early (above `W[6:0]`) or too late (below `0x40`) both reset** |
| Window | None (you may feed at any time) | Yes (`WWDG_CFR.W[6:0]` sets it) |
| Accuracy | Poor (the LSI drifts with temperature) | Good (it follows PCLK1) |
| Timeout range | About 0.1 ms to 26 s | About 0.1 ms to 60 ms |
| Typical use | A backstop for a hang; low power | Checking that a periodic task runs on time |
| F1 chapter | RM0008 Chapter 19 | RM0008 Chapter 20 |

An early feed does not reset the IWDG. An early feed that resets is the window watchdog.

**How to feed it**:

- **Feed from the main loop.** Simplest, but a dead loop inside one function defeats it.
- **Feed from a timer or an interrupt.** Fine for the IWDG, but a stuck interrupt will also reset you by mistake.
- **Each task feeds once.** In an RTOS, every critical task feeds. If any one of them stalls, the chip resets.
- **The WWDG window.** You are forced to feed inside a window that is not too early and not too late. That catches "running too fast" (a clock gone wrong) and "running too slow."

<p align="center">
  <img src="../../assets/diagrams/watchdog-reset-evidence.svg" width="820" alt="After feeding stops, measure timeout, read IWDGRSTF after reset, and increment a persistent boot_id">
  <br><sub>▲ Watchdog loop: fault, timeout, reset cause, and restart record must agree. An LED or startup log appearing again proves only that the system restarted, not that IWDG caused it (FA-002 · IG-008 · C-03/C-10/C-27/C-31).</sub>
</p>

## Hardware and wiring

| Board | Peripheral | Pin | Notes |
| --- | --- | --- | --- |
| BluePill (F103) | LSE crystal | PC14 = OSC32_IN, PC15 = OSC32_OUT | Solder a 32.768 kHz crystal. Choose the load capacitors from the crystal manual. |
| BluePill | VBAT | VBAT pin | A 3 V coin cell (CR2032) keeps the clock running |
| BluePill | Spare LED | PC13 | Often used as a heartbeat |
| Nucleo-F411RE | LSE | PC14 / PC15 | A 32.768 kHz crystal is already on the board |
| Any | Watchdog | No pin | Entirely on-chip |

> [!WARNING]
> Choose the load capacitors from the crystal manual. Too much capacitance can keep the LSE from starting.

## Code

**① RTC init and reading the time (F1, LSE source)**

```c
#include "stm32f1xx_hal.h"

RTC_HandleTypeDef hrtc;

static void MX_RTC_Init(void)
{
    __HAL_RCC_PWR_CLK_ENABLE();
    __HAL_RCC_BKP_CLK_ENABLE();

    hrtc.Instance          = RTC;
    hrtc.Init.AsynchPrediv = RTC_AUTO_1_SECOND;   /* F1 prescaler down to 1 Hz */
    hrtc.Init.OutPut       = RTC_OUTPUTSOURCE_NONE;
    HAL_RTC_Init(&hrtc);

    /* Set the time only on first power-up (no magic value in BKP) */
    if (HAL_RTCEx_BKUPRead(&hrtc, RTC_BKP_DR1) != 0xA5A5) {
        RTC_TimeTypeDef t = { .Hours = 12, .Minutes = 0, .Seconds = 0 };
        RTC_DateTypeDef d = { .Year = 26, .Month = RTC_MONTH_JANUARY,
                              .Date = 7, .WeekDay = RTC_WEEKDAY_WEDNESDAY };
        HAL_RTC_SetTime(&hrtc, &t, RTC_FORMAT_BIN);
        HAL_RTC_SetDate(&hrtc, &d, RTC_FORMAT_BIN);
        HAL_RTCEx_BKUPWrite(&hrtc, RTC_BKP_DR1, 0xA5A5);   /* store the magic value */
    }
}

void RTC_PrintTime(void)
{
    RTC_TimeTypeDef t; RTC_DateTypeDef d;
    HAL_RTC_GetTime(&hrtc, &t, RTC_FORMAT_BIN);
    HAL_RTC_GetDate(&hrtc, &d, RTC_FORMAT_BIN);   /* reading the date latches the time registers */
    printf("20%02d-%02d-%02d %02d:%02d:%02d\r\n",
           d.Year, d.Month, d.Date, t.Hours, t.Minutes, t.Seconds);
}
```

**② Alarm interrupt**

```c
void MX_RTC_Alarm_Init(void)
{
    RTC_AlarmTypeDef alarm = {0};
    alarm.AlarmTime.Hours   = 8;
    alarm.AlarmTime.Minutes = 30;
    alarm.AlarmTime.Seconds = 0;
    alarm.AlarmMask         = RTC_ALARMMASK_DATEWEEKDAY;  /* fire every day */
    HAL_RTC_SetAlarm_IT(&hrtc, &alarm, RTC_FORMAT_BIN);
}

void HAL_RTC_AlarmAEventCallback(RTC_HandleTypeDef *hrtc)
{
    /* Callback at the alarm; you can set a flag to wake the main loop */
}
```

**③ Independent watchdog, IWDG**

```c
IWDG_HandleTypeDef hiwdg;

static void MX_IWDG_Init(void)
{
    hiwdg.Instance       = IWDG;
    hiwdg.Init.Prescaler = IWDG_PRESCALER_64;   /* LSI ≈ 40 kHz / 64 = 625 Hz */
    hiwdg.Init.Reload    = 4095;                /* timeout (4095 + 1) / 625 = 6.5536 s. The 1 second timeout earlier in the chapter uses Reload 624 */
    HAL_IWDG_Init(&hiwdg);
}

/* Refresh periodically in the main loop (not from an interrupt — if the ISR is stuck, it cannot save you) */
HAL_IWDG_Refresh(&hiwdg);
```

**④ Window watchdog, WWDG**

```c
WWDG_HandleTypeDef hwwdg;

static void MX_WWDG_Init(void)
{
    hwwdg.Instance       = WWDG;
    hwwdg.Init.Prescaler = WWDG_PRESCALER_8;    /* PCLK1/4096/8 */
    hwwdg.Init.Window    = 0x50;                /* upper edge of the window */
    hwwdg.Init.Counter   = 0x7F;                /* initial value, timeout ≈ 58.25 ms at 36 MHz */
    hwwdg.Init.EWIMode   = WWDG_EWI_ENABLE;     /* enable the early-wakeup interrupt */
    HAL_WWDG_Init(&hwwdg);
}

/* Must refresh inside the [0x40, 0x50] window */
HAL_WWDG_Refresh(&hwwdg);
```


<p align="center">
  <img src="../../assets/diagrams/sample-11-rtc-triage.svg" width="760" alt="PRL must be 32767 for 1 Hz; a zeroed clock after reset points at VBAT; the alarm compares a 32-bit seconds counter">
  <br><sub>▲ Drawn for this book. Triage, three branches: time runs fast or slow — check PRL first, 32767 turns 32.768 kHz into 1 Hz; the clock zeroes after reset — check whether VBAT and the backup domain lost power; the alarm never fires — remember it compares a 32-bit seconds counter. Sources: [RM0008 RTC](#source-rm0008-rtc) and [DS5319 Rev 20](#source-ds5319-rtc).</sub>
</p>

## Hands-on labs

1. **RTC persistence:** Write the time and a BKP marker, remove main power for 60 s, and restore it. Record elapsed RTC time and the marker; record a separate failure state if LSE never starts.
2. **IWDG reset evidence:** Configure about a 1 s timeout, stop feeding, and mark the fault start on a GPIO. On reboot, read IWDGRSTF first, increment boot_id, and then clear flags. Repeat five times and record the actual delay range.
3. **WWDG window evidence:** Create early-feed, late-feed, and in-window cases. Record reset cause and GPIO timing. The in-window run continues; the other two reset.

### How to compute the timeout, and how to freeze it while debugging

`T = prescaler ÷ f_LSI × (Reload + 1)`. With `IWDG_PRESCALER_64` and a typical 40 kHz LSI, that is 625 Hz. For a 1 second timeout, write Reload as **624**. Writing 625 adds one extra count.

The datasheet range for the LSI is about 30 to 60 kHz. 40 kHz is only the typical value. Leave margin on the timeout. Do not sit exactly on the nominal number.

| Watchdog | When it resets | Time scale |
| --- | --- | --- |
| IWDG | Only when you feed too late (it counts down to 0) | About 0.1 ms to 26 s |
| WWDG | An early feed and a late feed both reset | On an F103 at 36 MHz, about 0.1 to 58 ms |

Single-stepping will be reset by the IWDG. Freeze it in the option settings or in the debug registers:

```c
__HAL_DBGMCU_FREEZE_IWDG();   /* F1 uses DBGMCU->CR, F4 uses APB1FZ; the macro picks the right register */
__HAL_DBGMCU_FREEZE_WWDG();
```

Once `HAL_IWDG_Init` succeeds, the IWDG cannot be stopped. Only a reset turns it off. If you write `WDG_SW` to 0 in the option bytes, the hardware watchdog takes over at power-up, and software cannot turn it off either.

Before leaving this chapter, keep the RTC/BKP record across power loss, five IWDG delays with IWDGRSTF, and the early/late/in-window WWDG results.

Self-test:

1. Prescaler 64, Reload 624, LSI taken as 40 kHz. Is the timeout exactly 1 second? Which "+1" is the difference?
2. What happens if you feed the window watchdog while the counter is still greater than the window value?
3. Why does the board reset by itself when a breakpoint stops inside `HAL_Delay`?

## Related resources

- RM0008, *STM32F10xxx Reference Manual*, Chapter 18 RTC, Chapter 19 IWDG, Chapter 20 WWDG, Chapter 5 PWR, Chapter 6 BKP, and Chapter 7 RCC (LSE / LSI configuration).
- RM0090, *STM32F4 Reference Manual*, Chapter 26 RTC, and the matching IWDG / WWDG chapters.
- Datasheet DS: LSE startup conditions, the LSI frequency range, and the VBAT operating voltage.
- Application note AN4759, *Using the hardware real-time clock (RTC) in STM32*.
- Figure: `../../assets/animations/iwdg-window.svg` (vector drawing by the author).

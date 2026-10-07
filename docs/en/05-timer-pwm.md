# 05 Timers and PWM
> 中文：[定时器与 PWM](../05-定时器与PWM.md)

> The timer keeps precise time, makes PWM, and captures an external signal. It is the heart of control applications.

<p align="center">
  <img src="../../assets/animations/timer-pwm.svg" width="760" alt="Timer counting and PWM duty cycle">
  <br><sub>▲ Animation: timer count, compare match, and PWM duty (a breathing LED; vector drawing by the author)</sub>
</p>

<!-- video:ch05 -->
<p align="center">
  <img src="../../assets/video/ch05-tim.gif" width="640" alt="Chapter 05 lecture slides">
  <br><sub>▲ Lecture slides for this chapter: a program-generated GIF (tools/gen_videos.py, reproducible, not a live shot). The narration matches the five frames one to one.</sub>
</p>

**Narration (read along with the frames, about one minute)**

1. A timer is a counter that adds by itself. When CNT meets ARR it turns around. That is the period.
2. PWM frequency comes from ARR and PSC. Duty comes from CCR. Three numbers, three jobs.
3. On an F103 the APB1 timer clock is often 72 MHz, not 36. Remember the doubler rule.
4. A breathing LED is CCR walking slowly. Input capture latches CNT, not the voltage on the pin.
5. Motto: what capture latches is CNT. Self-test: you want 1 kHz — which number do you fix first?
<!-- /video:ch05 -->


## 📌 Learning goals
- [ ] Tell the STM32 timer classes apart (advanced / general-purpose / basic / watchdog / SysTick)
- [ ] Use the time-base formulas to get PSC and ARR for any period
- [ ] Understand count modes, the update event, and shadow registers
- [ ] Configure a PWM mode and derive the duty and frequency formulas
- [ ] Measure frequency and duty with input capture, and know the encoder interface exists

## 🧠 Core ideas

**Lead with the conclusion: a timer is "a counter driven by a clock". PSC sets how fast it counts, ARR sets the period, CCR sets the duty.**

### 1. Timer classes

| Class | Instance | Width | What is special | Typical use |
| --- | --- | --- | --- | --- |
| Advanced | TIM1/TIM8 | 16-bit | Complementary outputs, dead time, break, MOE | Motors, three-phase PWM |
| General-purpose | TIM2–TIM5 | 16/32-bit | 4 channels, PWM / capture / encoder | General timing and PWM |
| Basic | TIM6/TIM7 | 16-bit | Counting only, no external channel | A time base, triggering a DAC |
| Watchdog | IWDG/WWDG | 12/7-bit | Independent / window watchdog | Reset a program that has run away |
| System | SysTick | 24-bit | Built into the core | HAL time base, RTOS tick |

### 2. Time-base formulas

- Counter clock: `fCK_CNT = fCK_PSC / (PSC + 1)`
- Period: `T = (ARR + 1) × (PSC + 1) / fCK_PSC`
- Frequency: `f = fCK_PSC / ((ARR + 1)(PSC + 1))`

Useful values at 72 MHz:

| Target period | PSC | ARR | Actual T | Notes |
| --- | --- | --- | --- | --- |
| 1 ms | 71 | 999 | 1.000 ms | 1 kHz |
| 10 ms | 7199 | 99 | 10.00 ms | 100 Hz |
| 100 ms | 7199 | 999 | 100.0 ms | 10 Hz |
| 1 s | 7199 | 9999 | 1.000 s | 1 Hz |
| 1 s (large ARR) | 71 | 999999 | 1.000 s | Needs a 32-bit timer |

> Conclusion: fix `fCK_CNT` first (pick PSC), then `ARR+1 = T × fCK_CNT`.

### 3. Count modes and shadow registers

| Mode | Meaning |
| --- | --- |
| Up | 0→ARR. Reaching ARR makes an update event (the usual choice) |
| Down | ARR→0 |
| Center-aligned | 0→ARR→0. Used for motors, symmetric PWM |

| Idea | Meaning |
| --- | --- |
| Update event UEV | Produced on overflow or underflow. Can raise an interrupt or a DMA request |
| ARR preload | ARR is written to the shadow register and takes effect at the UEV |
| CCR preload | Same idea, so PWM does not glitch halfway (ARPE/OCxPE) |
| Shadow register | You write the preload register. The value that is actually compared is the shadow register |

### 4. PWM modes and formulas

| Mode | Behavior |
| --- | --- |
| PWM mode 1 | While CNT < CCR, the output is the active level |
| PWM mode 2 | While CNT < CCR, the output is the inactive level (inverted) |

- Frequency: `f_PWM = fCK_PSC / ((ARR + 1)(PSC + 1))`
- Duty: `Duty = CCR / (ARR + 1) × 100%`

Frequency versus resolution, at the same fCK_PSC:

| Target PWM frequency | ARR+1 | Duty resolution | Notes |
| --- | --- | --- | --- |
| 1 kHz | 72000 | 1/72000 | High resolution, good for dimming |
| 10 kHz | 7200 | 1/7200 | A common motor PWM |
| 50 Hz (servo) | 1440000 | — | You also pick PSC to land on 20 ms |
| 20 kHz | 3600 | 1/3600 | No audible noise |

> Conclusion: **the higher the PWM frequency, the fewer ARR steps you have left for duty, and the resolution gets worse.** The two fight each other. Split the difference for the job.

### 5. Input capture, the encoder, and slave mode

| Function | How it works | Use |
| --- | --- | --- |
| Input capture | On an edge, CNT is latched into CCR | Measure frequency, pulse width, or duty |
| PWM input | Two channels capture the rising and falling edges | Period and high time come out directly |
| Encoder interface | A/B quadrature decode, count up and down automatically | Motor speed or position |
| Slave mode | An external signal resets or gates the counter | Period measurement, gated counting |

## 🛠️ Hardware and wiring

| Board | Peripheral | Pin | Notes |
| --- | --- | --- | --- |
| BluePill | LED (PWM dimming) | PA6 (TIM3_CH1) | 270 Ω in series; watch it breathe |
| BluePill | Input capture | PA0 (TIM2_CH1) | A signal generator, or another PWM |

> F1 timer-channel pinout is in the DS5319 alternate-function table. TIM1 is an advanced timer. PWM output needs **MOE**.

## 💻 Code

```c
/* timer_pwm.c —— TIM3_CH1 (PA6) outputs 1 kHz PWM; software walks the duty for a breathing LED */
#include "stm32f1xx_hal.h"

TIM_HandleTypeDef htim3;

#define PWM_TIM    TIM3
#define PWM_CH     TIM_CHANNEL_1
#define PWM_PSC    71        /* 72MHz/(71+1)=1MHz counter clock */
#define PWM_ARR    999       /* 1MHz/(999+1)=1kHz PWM */

void SystemClock_Config(void);

static void pwm_init(void)
{
    __HAL_RCC_TIM3_CLK_ENABLE();
    __HAL_RCC_GPIOA_CLK_ENABLE();

    /* PA6 alternate push-pull (TIM3_CH1) */
    GPIO_InitTypeDef io = {0};
    io.Pin   = GPIO_PIN_6;
    io.Mode  = GPIO_MODE_AF_PP;
    io.Speed = GPIO_SPEED_FREQ_HIGH;
    HAL_GPIO_Init(GPIOA, &io);

    htim3.Instance               = PWM_TIM;
    htim3.Init.Prescaler         = PWM_PSC;
    htim3.Init.CounterMode       = TIM_COUNTERMODE_UP;
    htim3.Init.Period            = PWM_ARR;          /* = ARR */
    htim3.Init.ClockDivision     = TIM_CLOCKDIVISION_DIV1;
    htim3.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_ENABLE;
    HAL_TIM_PWM_Init(&htim3);

    TIM_OC_InitTypeDef oc = {0};
    oc.OCMode     = TIM_OCMODE_PWM1;
    oc.Pulse      = PWM_ARR / 2;                     /* initial 50% duty = CCR */
    oc.OCPolarity = TIM_OCPOLARITY_HIGH;
    oc.OCFastMode = TIM_OCFAST_DISABLE;
    HAL_TIM_PWM_ConfigChannel(&htim3, &oc, PWM_CH);

    HAL_TIM_PWM_Start(&htim3, PWM_CH);               /* start the PWM output */
}

int main(void)
{
    HAL_Init();
    SystemClock_Config();
    pwm_init();

    int16_t duty = 0;
    int16_t step = 10;

    while (1)
    {
        duty += step;
        if (duty >= PWM_ARR || duty <= 0) step = -step;   /* sweep 0→100% and back */
        __HAL_TIM_SET_COMPARE(&htim3, PWM_CH, duty);      /* update CCR */
        HAL_Delay(10);
    }
}
```

The extra requirement on advanced timer TIM1:

```c
/* TIM1/TIM8 are advanced timers; the main output MOE must be enabled before they drive a pin */
HAL_TIM_PWM_Start(&htim1, TIM_CHANNEL_1);   /* HAL sets MOE for you */
/* if you are on registers: __HAL_TIM_MOE_ENABLE(&htim1); */
```

Input capture only works once the channel is actually configured. A rising edge latches CCR, a falling edge latches it again, and the difference times the counter period is the pulse width:

```c
TIM_IC_InitTypeDef ic = {0};
ic.ICPolarity  = TIM_INPUTCHANNELPOLARITY_RISING;
ic.ICSelection = TIM_ICSELECTION_DIRECTTI;
ic.ICPrescaler = TIM_ICPSC_DIV1;
ic.ICFilter    = 0;
HAL_TIM_IC_ConfigChannel(&htim2, &ic, TIM_CHANNEL_1);
HAL_TIM_IC_Start_IT(&htim2, TIM_CHANNEL_1);

void HAL_TIM_IC_CaptureCallback(TIM_HandleTypeDef *htim)
{
    if (htim->Channel == HAL_TIM_ACTIVE_CHANNEL_1)
    {
        uint32_t ccr = HAL_TIM_ReadCapturedValue(htim, TIM_CHANNEL_1);
        (void)ccr; /* pulse width = (CCR2 - CCR1) / fCK_CNT; on overflow add one (ARR+1) */
    }
}
```

The full project is in [`examples/timer-pwm/`](../../examples/timer-pwm/).

## ⚠️ Pitfalls and troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| No PWM at all | TIM1/TIM8 never enabled MOE | `HAL_TIM_PWM_Start` sets MOE, or set it yourself with `__HAL_TIM_MOE_ENABLE` |
| There is a waveform, but the duty never moves | `HAL_TIM_PWM_Start` was never called | Start the PWM channel |
| Changing CCR does nothing | CCR preload is off | Set `oc.OCPreload`, or enable `OCxPE` |
| The interrupt enters only once | The update flag was never cleared | In the ISR, `__HAL_TIM_CLEAR_FLAG(..., TIM_FLAG_UPDATE)` |
| After ARR gets smaller, the duty looks wrong | ARR changed and CCR was not updated with it | Keep CCR ≤ ARR. After you change ARR, set CCR again |
| PWM frequency is off by 2× | You forgot that when the APB divider is >1 the timer clock is ×2 | Compute PSC/ARR from the real timer clock |
| The breathing LED jumps | Updating CCR tears the waveform | Enable ARR/CCR preload, or write them together |

## 🧪 Hands-on labs

1. **Lab 1 (PWM out):** TIM3_CH1 outputs a 1 kHz, 50% square wave. Confirm frequency and duty with a scope or a logic analyzer.
2. **Lab 2 (breathing LED):** Walk the duty from 0 to 100% and back with the code above. Watch the LED fade up and down (compare with `pwm-breath.gif`).
3. **Lab 3 (input capture):** Feed lab 1's PWM into another input-capture channel. Measure frequency and duty, and compare the error with the values you set.

### 6. Complementary outputs and dead time (advanced timers)

| Idea | Meaning |
| --- | --- |
| Complementary outputs | CH1 and CH1N are a pair, for an H-bridge |
| Dead time | A blank inserted when the high and low switches trade places, so they never conduct together |
| Break | BKIN shuts the outputs off immediately |
| MOE | Main output enable. It has to be set or there is no output |

```c
/* configure dead time and the complementary output */
TIM_BreakDeadTimeConfigTypeDef bd = {0};
bd.OffStateRunMode = TIM_OSSR_ENABLE;
bd.DeadTime        = 0x10;        /* dead time */
bd.BreakState      = TIM_BREAK_DISABLE;
HAL_TIMEx_ConfigBreakDeadTime(&htim1, &bd);
```

### 7. A timer interrupt that toggles an LED at 1 Hz

```c
/* TIM2 update interrupt every 1 s toggles PC13 */
void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim)
{
    if (htim->Instance == TIM2)
    {
        HAL_GPIO_TogglePin(GPIOC, GPIO_PIN_13);
    }
}

/* start it with Start_IT, not Start */
HAL_TIM_Base_Start_IT(&htim2);
```

### 8. Which timer to pick

| Need | Timer |
| --- | --- |
| General timing | TIM2–5 |
| Advanced PWM (complementary) | TIM1/TIM8 |
| A time base only | TIM6/TIM7 |
| A long 32-bit interval | TIM2/TIM5 (F4) |
| The system tick | SysTick |

### 9. Input capture and TRGO

**Conclusion:** measure a pulse width with input capture. If you want the ADC to sample on a fixed interval, send the update event out through master mode (TRGO). Do not software-trigger it from the main loop.

```c
TIM_MasterConfigTypeDef mst = {0};
mst.MasterOutputTrigger = TIM_TRGO_UPDATE;          /* one pulse on every overflow */
mst.MasterSlaveMode     = TIM_MASTERSLAVEMODE_DISABLE;
HAL_TIMEx_MasterConfigSynchronization(&htim3, &mst);
```

Quadrature looks at both phases: B lagging A by about 90° is one direction, and B leading is the other. With only one square wave, the hardware cannot tell forward from reverse.

Motto: **capture latches CNT, and TRGO sends the beat. An encoder must have both A and B.**

Self-test:

1. If you captured only the rising edge, can you compute the duty?
2. The ADC should convert every 1 ms. Which event should the timer's TRGO select?
3. The encoder is wired to phase A only. What happens to the count when the shaft reverses?

## 🔗 Related resources

- Official manuals: **RM0008** chapter 14 (advanced timers TIM1/8), chapter 15 (general-purpose timers TIM2–5), chapter 16 (basic timers TIM6/7)
- Previous: [04 Interrupts and the NVIC](04-interrupts-nvic.md) | Next: [06 UART](06-uart.md)
- Figures: [`assets/animations/timer-pwm.svg`](../../assets/animations/timer-pwm.svg), [`assets/animations/timer-modes.svg`](../../assets/animations/timer-modes.svg), [`assets/gif/pwm-breath.gif`](../../assets/gif/pwm-breath.gif)
- Disclaimer: every illustration in this repo is a vector drawing or a program-generated animation by the author, not a manufacturer's photograph.

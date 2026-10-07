# 05 定时器与 PWM

> 定时器负责精确计时、产生 PWM 和捕获外部信号，是控制类应用的心脏。

<p align="center">
  <img src="../assets/animations/timer-pwm.svg" width="760" alt="定时器计数与 PWM 占空比">
  <br><sub>▲ 动画：定时器计数、比较匹配与 PWM 占空比（呼吸灯，作者自绘矢量图）</sub>
</p>

## 📌 学习目标
- [ ] 分清 STM32 各类定时器（高级/通用/基本/看门狗/SysTick）
- [ ] 会用时基公式算出任意定时周期的 PSC/ARR
- [ ] 理解计数模式、更新事件与影子寄存器
- [ ] 会配 PWM 模式并推导占空比/频率公式
- [ ] 会用输入捕获测频/测占空比，了解编码器接口

## 🧠 核心原理

**结论先行：定时器的本质是「时钟驱动计数器」，PSC 定快慢、ARR 定周期、CCR 定占空比。**

### 1. 定时器分类表

| 类别 | 型号 | 位宽 | 特点 | 典型用途 |
| --- | --- | --- | --- | --- |
| 高级 | TIM1/TIM8 | 16 位 | 互补输出、死区、刹车、MOE | 电机、三相 PWM |
| 通用 | TIM2~TIM5 | 16/32 位 | 4 通道，PWM/捕获/编码器 | 通用定时/PWM |
| 基本 | TIM6/TIM7 | 16 位 | 仅计数，无外部通道 | 时基、触发 DAC |
| 看门狗 | IWDG/WWDG | 12/7 位 | 独立/窗口看门狗 | 程序跑飞复位 |
| 系统 | SysTick | 24 位 | 内核自带 | HAL 时基、RTOS 节拍 |

### 2. 时基公式

- 计数时钟：`fCK_CNT = fCK_PSC / (PSC + 1)`
- 定时周期：`T = (ARR + 1) × (PSC + 1) / fCK_PSC`
- 频率：`f = fCK_PSC / ((ARR + 1)(PSC + 1))`

72MHz 下常用参数表：

| 目标周期 | PSC | ARR | 实际 T | 说明 |
| --- | --- | --- | --- | --- |
| 1ms | 71 | 999 | 1.000ms | 1kHz |
| 10ms | 7199 | 99 | 10.00ms | 100Hz |
| 100ms | 7199 | 999 | 100.0ms | 10Hz |
| 1s | 7199 | 9999 | 1.000s | 1Hz |
| 1s（大 ARR） | 71 | 999999 | 1.000s | 需 32 位定时器 |

> 结论：先定 `fCK_CNT`（选 PSC），再定 `ARR+1 = T × fCK_CNT`。

### 3. 计数模式与影子寄存器

| 模式 | 说明 |
| --- | --- |
| 向上计数 | 0→ARR，到 ARR 产生更新事件（最常用） |
| 向下计数 | ARR→0 |
| 中央对齐 | 0→ARR→0，用于电机，对称 PWM |

| 概念 | 说明 |
| --- | --- |
| 更新事件 UEV | 计数器溢出/下溢时产生，可产生中断/DMA |
| 预装载 ARR | ARR 写入影子寄存器，UEV 时才生效 |
| 预装载 CCR | 同理，避免 PWM 中途抖动（ARPE/OCxPE） |
| 影子寄存器 | 用户写的是预装载寄存器，真正参与比较的是影子寄存器 |

### 4. PWM 模式与公式

| 模式 | 行为 |
| --- | --- |
| PWM 模式 1 | CNT < CCR 时输出有效电平 |
| PWM 模式 2 | CNT < CCR 时输出无效电平（反相） |

- 频率：`f_PWM = fCK_PSC / ((ARR + 1)(PSC + 1))`
- 占空比：`Duty = CCR / (ARR + 1) × 100%`

频率与分辨率权衡（同一 fCK_PSC）：

| 目标 PWM 频率 | ARR+1 | 占空比分辨率 | 说明 |
| --- | --- | --- | --- |
| 1kHz | 72000 | 1/72000 | 高分辨率，适合调光 |
| 10kHz | 7200 | 1/7200 | 常用电机 PWM |
| 50Hz（舵机） | 1440000 | — | 需配合 PSC 凑 20ms |
| 20kHz | 3600 | 1/3600 | 无 audible 噪音 |

> 结论：**PWM 频率越高，可用于调节占空比的 ARR 档位越少，分辨率越低**——两者矛盾，按需折中。

### 5. 输入捕获 / 编码器 / 从模式

| 功能 | 原理 | 用途 |
| --- | --- | --- |
| 输入捕获 | 边沿触发时把 CNT 锁存到 CCR | 测频率、测脉宽/占空比 |
| PWM 输入 | 两个通道分别捕获上升/下降沿 | 直接得周期与高电平时间 |
| 编码器接口 | A/B 相正交解码，自动加减计数 | 电机测速/位置 |
| 从模式 | 外部信号复位/门控计数器 | 测周、门控计数 |

## 🛠️ 硬件与接线

| 开发板 | 外设 | 引脚 | 备注 |
| --- | --- | --- | --- |
| BluePill | LED（PWM 调光） | PA6 (TIM3_CH1) | 串 270Ω，观察呼吸 |
| BluePill | 输入捕获 | PA0 (TIM2_CH1) | 接信号发生器 / 另一路 PWM |

> F1 定时器通道对应关系见 DS5319 引脚复用表；TIM1 是高级定时器，PWM 输出需 **MOE**。

## 💻 代码实现

```c
/* timer_pwm.c —— TIM3_CH1(PA6) 输出 1kHz PWM，软件调节占空比做呼吸灯 */
#include "stm32f1xx_hal.h"

TIM_HandleTypeDef htim3;

#define PWM_TIM    TIM3
#define PWM_CH     TIM_CHANNEL_1
#define PWM_PSC    71        /* 72MHz/(71+1)=1MHz 计数时钟 */
#define PWM_ARR    999       /* 1MHz/(999+1)=1kHz PWM */

void SystemClock_Config(void);

static void pwm_init(void)
{
    __HAL_RCC_TIM3_CLK_ENABLE();
    __HAL_RCC_GPIOA_CLK_ENABLE();

    /* PA6 复用推挽（TIM3_CH1） */
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
    oc.Pulse      = PWM_ARR / 2;                     /* 初始 50% 占空比 = CCR */
    oc.OCPolarity = TIM_OCPOLARITY_HIGH;
    oc.OCFastMode = TIM_OCFAST_DISABLE;
    HAL_TIM_PWM_ConfigChannel(&htim3, &oc, PWM_CH);

    HAL_TIM_PWM_Start(&htim3, PWM_CH);               /* 启动 PWM 输出 */
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
        if (duty >= PWM_ARR || duty <= 0) step = -step;   /* 0→100% 往返 */
        __HAL_TIM_SET_COMPARE(&htim3, PWM_CH, duty);      /* 更新 CCR */
        HAL_Delay(10);
    }
}
```

高级定时器 TIM1 的额外要求：

```c
/* TIM1/TIM8 是高级定时器，输出前必须使能主输出 MOE */
HAL_TIM_PWM_Start(&htim1, TIM_CHANNEL_1);   /* HAL 内部会置 MOE */
/* 若用寄存器：__HAL_TIM_MOE_ENABLE(&htim1); */
```

输入捕获测频要点：

```c
/* 配置通道为输入捕获，上升沿，预分频后进中断读 CCR */
/* ISR 中：f_in = fCK_CNT / (CCR2 - CCR1)  */
```

完整工程见 [`examples/timer-pwm/`](../examples/timer-pwm/)。

<!--MORE-->

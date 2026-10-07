# timer-pwm —— TIM3 PWM 呼吸灯

> 难度：★★☆☆　｜　涉及外设：TIM（PWM）　｜　对应章节：[05 定时器与 PWM](../../docs/05-定时器与PWM.md)

<p align="center">
  <img src="../../assets/animations/timer-pwm.svg" width="760" alt="定时器计数与 PWM 占空比动画">
  <br><sub>▲ 动画：定时器计数、比较匹配与 PWM 占空比（呼吸灯，作者自绘矢量图）</sub>
</p>

## 一、功能说明

用 TIM3 的通道 1（PA6）输出 **1kHz PWM**，在主循环里线性改变比较值 CCR（0 ↔ ARR 往返），
让接在 PA6 的 LED 呈现**呼吸**效果。示例同时给出频率/占空比公式，以及高级定时器 TIM1 的 MOE 说明。

## 二、硬件接线表

| 开发板 | 外设 | 引脚 | 接法 | 备注 |
| --- | --- | --- | --- | --- |
| BluePill | LED（PWM 调光） | PA6 (TIM3_CH1) | PA6 → 270Ω → LED 阳极，阴极 → GND | 高电平点亮，占空比越大越亮 |

> 用示波器/逻辑分析仪接 PA6，可看到 1kHz 方波，高电平宽度随 CCR 变化。

## 三、CubeMX 关键配置

| 配置项 | 取值 | 说明 |
| --- | --- | --- |
| TIM3 → Clock Source | Internal Clock | 内部时钟 |
| TIM3 → Channel1 | PWM Generation CH1 | 复用为 PWM 输出 |
| TIM3 → Prescaler | 71 | 72MHz/(71+1)=1MHz |
| TIM3 → Counter Period (ARR) | 999 | 1MHz/(999+1)=1kHz |
| TIM3 → Pulse (CCR) | 500 | 初始 50% |
| TIM3 → PWM Mode | PWM mode 1 | CNT<CCR 输出有效 |
| GPIO PA6 | AF Push Pull / High speed | 复用推挽 |

## 四、关键代码解读

**1) 频率与占空比公式**

```
fCK_CNT = fCK_PSC / (PSC + 1)                      计数时钟
f_PWM   = fCK_PSC / ((ARR + 1) × (PSC + 1))        PWM 频率
Duty    = CCR / (ARR + 1) × 100%                   占空比
```

本例：`PSC=71 → fCK_CNT=1MHz`，`ARR=999 → f_PWM=1kHz`；CCR 从 0~999 即 0~100% 占空比。

**2) 时基 + 通道配置**

```c
htim3.Init.Prescaler         = PWM_PSC;   /* 71  */
htim3.Init.Period            = PWM_ARR;   /* 999 = ARR */
htim3.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_ENABLE;
HAL_TIM_PWM_Init(&htim3);

TIM_OC_InitTypeDef oc = {0};
oc.OCMode     = TIM_OCMODE_PWM1;          /* PWM 模式 1 */
oc.Pulse      = PWM_ARR / 2U;             /* 初始 CCR = 500 → 50% */
oc.OCPolarity = TIM_OCPOLARITY_HIGH;
HAL_TIM_PWM_ConfigChannel(&htim3, &oc, PWM_CH);
HAL_TIM_PWM_Start(&htim3, PWM_CH);        /* 启动输出 */
```

**3) 动态改占空比（呼吸灯核心）**

```c
duty += step;
if (duty >= PWM_ARR || duty <= 0) step = -step;   /* 到边界反向 */
__HAL_TIM_SET_COMPARE(&htim3, PWM_CH, duty);      /* 改 CCR，预装载生效 */
HAL_Delay(BREATH_DELAY_MS);
```

> 打开 `AutoReloadPreload` 后，ARR/CCR 写入**影子寄存器**，在更新事件（UEV）时才生效，
> 避免 PWM 中途出现毛刺。这也是「改了 CCR 波形却不抖」的原因。

**4) 高级定时器 TIM1 的 MOE**

```c
HAL_TIM_PWM_Start(&htim1, TIM_CHANNEL_1);   /* HAL 内部置 MOE */
/* 寄存器写法：__HAL_TIM_MOE_ENABLE(&htim1);  // TIM1->BDTR |= TIM_BDTR_MOE */
```

TIM1/TIM8 若不开 MOE，通道使能了也没有波形输出，是最常见的「高级定时器没波形」原因。

## 五、编译烧录步骤

1. CubeMX 生成 F103C8 工程，配置 TIM3 如上表，覆盖 `Core/Src/main.c`。
2. Keil `F7` 编译 → `F8` 下载；CubeIDE 🔨 → ▶；PlatformIO `pio run -t upload`。
3. 若用 CubeMX 自动生成 TIM 代码，注意别与本文件的 `pwm_init()` 重复初始化。

## 六、预期现象

- 接 PA6 的 LED 由暗到亮、再由亮到暗平滑循环（呼吸灯）；
- 示波器测 PA6：频率稳定在 **1kHz**，占空比在 0~100% 之间线性变化；
- 呼吸周期约 `2 × (ARR/STEP) × BREATH_DELAY_MS ≈ 2 秒`。

## 七、常见问题

| 现象 | 原因 | 解决 |
| --- | --- | --- |
| 引脚无波形 | 高级定时器未开 MOE | `HAL_TIM_PWM_Start` 或 `__HAL_TIM_MOE_ENABLE` |
| LED 一直亮/灭 | 占空比固定 0 或 100% | 检查 CCR 是否在 0~ARR 间变化 |
| 频率不对 | PSC/ARR 算错或时钟树不对 | 用公式重算，确认定时器时钟 |
| 调占空比时闪一下 | 未开预装载 | 使能 `AutoReloadPreload` / OCxPE |
| 波形抖动有毛刺 | GPIO 速度太低 | 复用输出设 `GPIO_SPEED_FREQ_HIGH` |
| 亮度不线性 | LED 人眼非线性 | 用伽马校正或查表调光 |

## 八、相关资源

- 参考手册 **RM0008** 第 14 章（TIM 通用/高级定时器，含 CCMR/CCER/BDTR）
- 数据手册 **DS5319** 引脚复用表（TIM3_CH1 = PA6）
- 相关图：[`assets/animations/timer-modes.svg`](../../assets/animations/timer-modes.svg)、[`assets/gif/pwm-breath.gif`](../../assets/gif/pwm-breath.gif)
- 免责声明：本示例配图为作者自绘矢量图/程序生成动画，非厂商实拍照片。

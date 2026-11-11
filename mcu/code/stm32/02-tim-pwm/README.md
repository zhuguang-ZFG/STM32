# 02-tim-pwm：一个计数器，两种用法

配套章节：[S6 定时器 TIM](../../docs/stm32/06-tim.md)

## 这个工程回答什么

TIM 只有一个核心：按固定节拍往上数的计数器 CNT。剩下的都是"拿 CNT 和别的寄存器比一比"：

- 和 **ARR** 比 → 数到几归零，决定一个周期多长（频率）
- 和 **CCR** 比 → 决定一个周期里高电平占多久（占空比）
- 引脚有边沿 → 硬件把当时的 CNT 拍下来存进 CCR（输入捕获）

本工程用同一个 TIM3 同时演示输出与捕获：

| 通道 | 引脚 | 复用 | 干什么 |
|---|---|---|---|
| CH1 | PA6 | AF2 | 输出 1kHz PWM，呼吸灯 |
| TIM2_CH1 | PA0 | AF1 | 捕获 PA6 的方波，硬件算周期，CPU 只做减法 |

自测闭环：一根杜邦线把 **PA6 接到 PA0**。不接也能跑，只是实测频率一直是 0。

> 常见误解纠正：F407 的 Port F 上**没有 TIM3 通道**。
> PF6/PF7/PF8 在 AF3 上分别是 TIM10_CH1 / TIM11_CH1 / TIM13_CH1（DS8626 Table 9）。

## 顺带实测一条隐藏规则

`APBx 预分频 ≠ 1 时，定时器时钟 = PCLK × 2`。

代码先在 APB1=/1 下测一次定时器时钟，再切到 APB1=/2 测一次：
`g_pclk1_after` 只有 `g_pclk1_before` 的一半，`g_tim_clk_after` 却与 `g_tim_clk_before` 相同。
这就是为什么"按 42MHz 算 TIM2"一定是错的——它实际是 84MHz。

## 构建

PATH 需要 `arm-none-eabi-gcc`、`mingw32-make`，以及 Git 的 `usr\bin`。

```bash
make
make flash      # OpenOCD + ST-Link
make clean
```

## 代码结构（对照阅读）

| 位置 | 对应知识点 |
|---|---|
| `clocks_read()` | 从 CFGR 反推 HCLK/PCLK1，而不是相信"我以为配了什么" |
| `timer_clock()` | APB 分频≠1 时的 ×2 规则，一行代码 |
| `tim3_pwm_init()` | PSC/ARR 定频率，OC1M+OC1PE+CC1E 出波形，独立 TIM2 接捕获 |
| `tim3_set_duty()` | 只改 CCR1，频率纹丝不动——"占空比和频率分家"的证据 |
| 捕获循环 | `now - ccr_last` 用无符号减法，回绕自动处理 |

## 预期观察

- PA6：1kHz 方波，占空比每 20ms 变一次，在 0%~100% 之间来回"呼吸"（约 4 秒一个来回）。
- 接上 PA6→PA0 跳线后：蓝灯常亮，GDB 里 `g_measured_hz ≈ 1000`，`g_capture_edges` 持续增长。
- 不接跳线：蓝灯不亮，`g_measured_hz == 0`。
- GDB 读 `g_tim_clk_before == g_tim_clk_after == 16000000`，而 `g_pclk1_before == 16000000`、`g_pclk1_after == 8000000`。
- GDB 读 `g_pwm_hz == 1000`。

## 失败排查

| 现象 | 多半是 |
|---|---|
| PA6 没波形 | `TIM3_CCER` 的 CC1E 没开；或 GPIOA 的 MODER/AFRL 没配成 AF2；或忘了开 GPIOA 时钟 |
| 频率是设定值的 1/10 或 10 倍 | 忘了两个"+1"：实际频率 = 计数时钟/(PSC+1)/(ARR+1)；再检查有没有把 PCLK 当成了 TIM 时钟 |
| 捕获一直为 0 | 没接跳线；或 CC2E 没开；或没清 `TIM3_SR` 的 CC2IF 导致处理不及时 |
| 呼吸灯不呼吸、而是突然跳变 | 少了 `OC1PE`（CCR 预装载），CCR 会在周期中途生效 |
捕获现使用 TIM2 32 位自由时基与 ISR，范围 2Hz–10kHz；超时或过捕获输出无效状态。旧 PA7 接线不再适用。时钟读回已按 SWS、全部 PLLP 与 APB 分频编码修正；计数测试见 code/common/behavior。待上板实测。

---
title: P7 定时器与 LEDC：各管一段时间
status: done
difficulty: 2
minutes: 35
---

# P7 定时器与 LEDC：各管一段时间

> 🎯 STM32 里 TIM 一肩挑（时基+PWM）；ESP32-S3 把两件事分给了两个外设：**GPTimer** 管"什么时候叫我"（高精度报警），**LEDC** 管"以什么节奏眨眼"（PWM 调光调速）。分工即选型。

## 本章精髓

1. **GPTimer 是"闹钟工厂"**：计数器+报警值，到点回调；回调跑在 ISR 上下文（IRAM 纪律回 [P4](04-irq-dualcore.md)），微秒级分辨率，适合测距、超时、采样节拍。
2. **LEDC 是"8 通道 PWM 乐团"（S3 上只有低速模式）**：定时器（分辨率+频率）与通道（绑定 GPIO+占空比）两级配置。占空比渐变用硬件 `ledc_fade`（无需 CPU 逐点写）。**别套经典 ESP32 的 16 通道/高速模式**：S3 是 8 通道（`SOC_LEDC_CHANNEL_NUM=8`）、定时器位宽 14 位（`SOC_LEDC_TIMER_BIT_WIDTH=14`）、仅低速模式（soc_caps.h 核实）。
3. **分辨率×频率是此消彼长**：`f = 时钟 / 2^位数`：位数越高，可达频率越低。舵机 50Hz 可上 14 位，音频级应用就得降位数。

- **能理解**：为什么改 duty 必须 update（双缓冲）；为什么 fade 与手动 set 不能混用；为什么 S3 不能套经典 ESP32 的结论。
- **能用**：写出 LEDC 两级配置链；用硬件 fade 做呼吸灯；说出分辨率与频率的取舍。

## 先修

- [S6 TIM](../stm32/06-tim.md)（PWM 本质）、[P2 引脚](02-gpio-matrix.md)、[P4 中断](04-irq-dualcore.md)。

## 先跑起来（10 分钟 quick win）

`code/esp32/03-ledc-fade`：LEDC 通道绑到 **GPIO10**（多功能扩展口，立创 wiki 核实），5kHz/10 位起步，硬件 fade 做呼吸，占空比的物理意义第一次"看得见"。

呼吸灯亮起来之前先押个闲差：占空比从零爬到满的那几秒，CPU 在忙循环、在被打断、还是根本不用管？押完再 flash，答案会让你重新认识"定时"两个外设的分工。

## 动画：timer 定调，channel 发声

LEDC 的两级分工一目了然：timer 定频率与分辨率（"多快、多细"），channel 定 GPIO 与占空比（"从哪出、多高"），fade 引擎按步进改比较值。

![LEDC timer 与 channel 动画](/anim/ledc-timer-channel.svg)

## 板卡与版本前提

- 板卡：立创·实战派 ESP32-S3；PWM 从 **GPIO10**（多功能扩展口）输出。
- 框架：ESP-IDF **v5.5.2**；LEDC 驱动在 `components/esp_driver_ledc/`。
- 芯片能力（soc_caps.h）：S3 是 8 通道、14 位位宽、仅低速模式，与经典 ESP32 的 16 通道/高速模式不是一回事。

## 小节结构

| 小节 | 内容 | 四件套 |
|---|---|---|
| 一、GPTimer 报警 | gptimer_config/alarm 回调；ISR 上下文纪律 | 配置 |
| 二、采样节拍 | 1kHz 定时 vs vTaskDelay 抖动实测 | 代码分析 |
| 三、LEDC 两级 | timer/channel 配置逐字段；S3 低速模式的边界 | 配置 |
| 四、硬件渐变 | ledc_fade 系列；阻塞/非阻塞两模式 | 代码分析 |
| 五、分辨率取舍 | 频率-位数换算表；舵机/背光案例 | 配置 |
| 六、对照 TIM | STM32 TIM 一肩挑 vs S3 分工设计的哲学 | 库解析 |

## 一、GPTimer 报警：闹钟工厂

GPTimer 的配置对象：`gptimer_config_t`（时钟源、分辨率、计数方向）→ `gptimer_alarm_config_t`（报警值、自动重载）→ 回调注册。回调跑在 **ISR 上下文**（IRAM 纪律回 P4）：回调里只办事不等待，不能用会阻塞的 API。

## 二、采样节拍：1kHz 定时 vs vTaskDelay

`vTaskDelay(1)` 的实际周期是 tick 粒度（本工程 1ms），抖动就是 ±1 tick；GPTimer 报警回调是硬件定时，抖动在微秒级。做采样节拍、测距超时这类"时间要准"的事，用 GPTimer 不是用 vTaskDelay。

## 三、LEDC 两级：timer 定调，channel 发声

两级配置链：

```c
/* timer：多快、多细 */
ledc_timer_config_t timer = {
    .speed_mode      = LEDC_LOW_SPEED_MODE,   /* S3 只有低速模式 */
    .duty_resolution = LEDC_TIMER_10_BIT,     /* 占空比 0..1023 */
    .timer_num       = LEDC_TIMER_0,
    .freq_hz         = 5000,
    .clk_cfg         = LEDC_AUTO_CLK,
};

/* channel：从哪出、占多少 */
ledc_channel_config_t ch = {
    .gpio_num   = GPIO_NUM_10,
    .speed_mode = LEDC_LOW_SPEED_MODE,
    .channel    = LEDC_CHANNEL_0,
    .timer_sel  = LEDC_TIMER_0,
    .duty       = 0,
    .hpoint     = 0,
};
```

`ledc_get_freq` 回读实际频率：请求值与实际值可能因分频舍入不同（回 [S6](../stm32/06-tim.md) 的"+1"教训）。

## 四、硬件渐变：ledc_fade 系列

`ledc_fade_func_install()` 装渐变引擎 → `ledc_set_fade_with_time()` 设目标占空比与用时 → `ledc_fade_start()` 启动。**fade 期间 CPU 不逐点干预**：这是它比"定时器模拟 PWM 渐变"高级的地方。

两模式：`LEDC_FADE_NO_WAIT`（启动就返回，fade 在后台跑）vs `LEDC_FADE_WAIT_DONE`（等渐变完）。选哪个取决于你要不要在渐变途中干别的。

注意纪律：fade 与手动 `ledc_set_duty` 不能混用，渐变途中手动 set 会被 fade 引擎覆盖，先停 fade 再接管。

## 五、分辨率取舍：频率-位数跷跷板

| 需求 | 频率 | 位数 | 取舍 |
|---|---|---|---|
| 舵机 | 50Hz | 14 位 | 低频高分辨率，随便选 |
| LED 调光 | 1~5kHz | 10~13 位 | 常见组合 |
| 音频级 | >20kHz | ≤10 位 | 高频就得降位数 |

本质：`f = 时钟 / 2^位数`，时钟有限，位数和频率只能二选一。`ledc_get_freq` 回读实际值，别假设请求值一定生效。

## 六、对照 TIM：一肩挑 vs 分工

STM32 的 TIM 一个外设包干时基+PWM+捕获；S3 拆成 GPTimer（计时）+ LEDC（PWM）。设计哲学的对照：**复用度高但配置纠缠** vs **职责单一但各司其职**。学到的东西是相通的：比较值、预装载、双缓冲、fade/渐变，只是名字换了。

## 附录：工程完整源码

<<< ../../code/esp32/03-ledc-fade/main/main.c

## 记忆锚点

::: tip 一句话记住
**GPTimer 定闹钟（ISR 里快办事），LEDC 开乐团（timer 定调 channel 发声）；渐变交给硬件 fade，位数频率跷跷板；S3 只有低速 8 通道，别套经典 ESP32。**
:::

**延伸**：LEDC 定时器与通道动画见 [P7 动画](/anim/ledc-timer-channel.svg)；STM32 TIM PWM 对照见 [S6](../stm32/06-tim.md)；定时器输入捕获在 [S6 TIM](../stm32/06-tim.md) 展开。

## 实物实验

- 呼吸灯 + [E03 分析仪看占空比](../lab/e03-scope-pwm.md) 的 S3 版：fade 曲线抓取，验证硬件渐变的线性；
- 抖动对比：同一 1kHz 节拍，GPTimer 回调版 vs vTaskDelay 版，逻辑分析仪看周期方差；
- 分辨率实测：5kHz/10 位改成 5kHz/14 位，看 `ledc_get_freq` 回读是否还成立。

## 常见坑

- **改 duty 忘 update**：LEDC 双缓冲，`ledc_update_duty` 才装载（与 TIM 直接写 CCR 不同）；
- **fade 与手动 set 混用**：渐变途中手动 set 被 fade 引擎覆盖，停 fade 再接管；
- **套经典 ESP32 结论**：S3 是 8 通道、14 位、仅低速模式，没有高速模式可选；
- **GPTimer 回调里做长活**：回调=ISR，阻塞一毫，系统抖一分（P4 复训）；
- **请求频率当实际频率**：分频舍入让两者不等，用 `ledc_get_freq` 回读。

## 短自测

1. S3 的 LEDC 与经典 ESP32 的 LEDC 差在哪？
<details><summary>参考答案</summary>S3 是 8 通道、定时器位宽 14 位、只有低速模式（soc_caps.h: SOC_LEDC_CHANNEL_NUM=8、SOC_LEDC_TIMER_BIT_WIDTH=14）。经典 ESP32 的 16 通道/高速模式结论不能套。</details>

2. 为什么改完 `ledc_set_duty` 还要 `ledc_update_duty`？
<details><summary>参考答案</summary>LEDC 是双缓冲：set 只写影子寄存器，update 才装载到硬件生效。漏了 update，波形不变。</details>

3. 分辨率位数和频率为什么不能同时拉满？
<details><summary>参考答案</summary>f = 时钟 / 2^位数。时钟有限，位数每加 1，同档频率减半。舵机 50Hz 可以上 14 位，音频级 20kHz+ 就得降位数。</details>

## 对照表：本章概念 → 仓库与上游落点

| 概念 | 落点 |
|---|---|
| S3 通道数/位宽/低速模式 | `soc/soc_caps.h` SOC_LEDC_CHANNEL_NUM=8、SOC_LEDC_TIMER_BIT_WIDTH=14 |
| fade API 与线程安全 | ESP-IDF v5.5.2 `components/esp_driver_ledc/include/driver/ledc.h` |
| 实验 | [code/esp32/03-ledc-fade](https://github.com/zhuguang-ZFG/STM32/tree/main/mcu/code/esp32/03-ledc-fade) |
| 动画 | [ledc-timer-channel.svg](/anim/ledc-timer-channel.svg) |
| STM32 对照 | [S6 TIM](../stm32/06-tim.md) |

## 你做到了

- S3 的"时间双雄"各就各位；
- PWM 从"能用"到"用好"：fade、分辨率、速度组边界全在掌握；
- 与 STM32 TIM 的对照让你看清"同一个问题、两种设计"。

闲差押中了：那几秒 CPU 是真闲，fade 由硬件自己爬坡，一步都不用你盯。把"什么时候叫"和"以什么节奏眨"拆给两个外设，拆的就是这个意思。

<div class="achievement">
✅ 下一站：<a href="08-wifi.html">P8 Wi-Fi 精髓</a>：esp_event 事件循环与连接状态机，联网的第一性原理。
</div>
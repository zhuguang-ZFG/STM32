---
title: 实验 E03 示波器看 PWM
status: done
difficulty: 2
minutes: 45
code_status: ready
hardware_status: pending
code_note: F407 PWM 与 S3 LEDC 两个工程均有独立说明。
projects: ["stm32-02-tim-pwm", "esp32-03-ledc-fade"]

---

# 实验 E03 示波器看 PWM：占空比与呼吸灯

> 🎯 `CCR=500, ARR=999` 只是两个数字；示波器上那条"一半时间高电平"的方波，才是 PWM 的物理真身。数字与波形对上的那一刻，定时器就再也不是黑盒。

## 实验信息卡

<LabStatus />

| 项 | 内容 |
|---|---|
| 编号 | E03 |
| 对应章节 | [S6 TIM](../stm32/06-tim.md)、[P7 LEDC](../esp32/07-timer-ledc.md) |
| 目标板 | 霸天虎 或 立创 S3（任选一，双做更佳） |

## 实验目标

- 现象：波形占空比随手算值变化；改 ARR 波形频率变化；呼吸灯的渐变曲线被记录。
- 能力：PWM 三参数（频率/占空比/分辨率）的测算对照；仪器读数与寄存器值互查。

## 装备

| 装备 | 数量 | 备注 |
|---|---|---|
| 示波器（或逻辑分析仪） | 1 | 示波器可看模拟特性（RC 滤波） |
| 霸天虎（S6 PWM 固件）或 S3（P7 LEDC 固件） | 1 | F407 1kHz 呼吸；S3 5kHz fade |
| 杜邦线 | 2 | 通道+地 |

> 板卡外观与引脚分配见 [野火霸天虎资料页](https://doc.embedfire.com/products/link/zh/latest/mcu/stm32/stm32f407_batianhu.html) / [立创 S3 wiki](https://wiki.lckfb.com/zh-hans/szpi-esp32s3/)。

![RIGOL DS1054Z 四通道数字示波器，屏幕显示一条正弦波](/images/tools/oscilloscope-ds1054z.jpg)

示波器形态参考（资料参考图，不是上板验证证据）：RIGOL DS1054Z。仪器的 Probe 档位要与探头上的 ×1/×10 开关一致，否则幅值差 10 倍。来源：[Wikimedia Commons](https://commons.wikimedia.org/wiki/File:RIGOL_DS1054Z_Digital_Storage_Oscilloscope.jpg)（CC BY-SA 4.0，作者 Draconichiaro）。

## 原理一句话

PWM=周期内高电平时间占比；占空比=CCR/(ARR+1)（STM32）或 duty/2^bits（LEDC）：波形的每个参数都能从寄存器值算出来。

上探头前先猜：手算的 25%，示波器会读出多少？误差是小数点后的事，还是会被仪器坑出几个百分点？押完再上探头。

## 接线

- 探头接 PWM 输出脚（霸天虎本批固件固定 **PA6**，TIM3_CH1 AF2；S3 本批固件固定 **GPIO10**，LEDC 低速通道 0，多功能扩展口），地夹共地。

![E03 探头接法与读图：CNT 锯齿与 CCR 比较得到 PA6 方波，周期 1ms、高电平 0.5ms](/images/labs/e03-pwm-probe.svg)

计数器与比较值的动态过程见 [S6 TIM](../stm32/06-tim.md)；LEDC 的定时器/通道关系见 [P7](../esp32/07-timer-ledc.md)。

## 步骤

1. F407：进入 `code/stm32/02-tim-pwm`，`make` 后 `make flash`；默认 PA6 输出 1kHz，占空比随主循环变化。S3：进入 `code/esp32/03-ledc-fade`，执行 `idf.py set-target esp32s3`、`idf.py build`、`idf.py -p COMx flash monitor`；默认 GPIO10 输出 5kHz fade。先记录各自频率及占空比变化；
2. （F407 固定值练习）将主循环内 `ccr` 的计算式改成 `(PWM_PERIOD_TICKS + 1U) / 4U`，仍调用 `tim3_set_duty(ccr)`，重新构建烧录，对比 25% 占空比；
3. （F407）将 `PWM_PERIOD_TICKS` 从 999 改成 499，保持计数时钟不变，重新构建后频率应翻倍；
4. （S3）默认已启用硬件 fade，记录 0→1023/1024 占空比的渐变时间（目标约 2 秒），最大值不是精确 100%；
5. （进阶）输出经 RC 低通（10kΩ+100nF），示波器看"模拟电压≈VCC×占空比"——DAC 的穷人版现身。

## 预期现象

- 比较测量值与手算结果，记录时钟源与仪器误差；不预填未测得的误差范围；
- fade 曲线呈阶梯式渐变（硬件渐变的最小步进可辨）。

## 实测记录

| 日期 | 板子 | 观测手段 | 结果 | 备注 |
|---|---|---|---|---|
| | | | | |

## 故障排查

| 症状 | 最可能原因 | 处置 |
|---|---|---|
| 无波形 | CC 通道没使能/引脚复用错 | 回 S6/P7 配置清单 |
| 频率翻倍或减半 | APB 倍频规则（S6）或速度组时钟（P7） | 重算时钟链 |
| 占空比反了 | 输出极性位 | 检查 OC 极性配置 |

## 思考题

1. 为什么 LED 调光用 1kHz 看不出闪烁，而 50Hz 能？
2. RC 滤波后的纹波与 PWM 频率什么关系？怎么选 RC？

## 你做到了

- 定时器参数与物理波形建立换算直觉；
- "数字配置→模拟现象"的验证方法论再下一城。

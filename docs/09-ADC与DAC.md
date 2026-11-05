# 09 ADC 与 DAC

> English: [ADC and DAC](en/09-adc-dac.md)

> 万用表量到 1.65 V，ADC 却不一定正好读到 2048。要同时核对 VDDA、采样时间、ADC 状态和 DMA 数组，才能区分量化误差、源阻抗与缓冲区顺序问题。

<p align="center">
  <img src="../assets/animations/adc-sar.svg" width="760" alt="ADC 采样保持与逐次逼近（SAR）过程动画">
  <br><sub>▲ 动画：ADC 采样保持 + 逐次逼近（SAR）比较过程（作者自绘矢量动画，非实拍）</sub>
</p>

<!-- video:ch09 -->
<p align="center">
  <video width="640" controls poster="../assets/video/ch09-adc.png">
    <source src="../assets/video/ch09-adc.mp4" type="video/mp4">
  </video>
  <br><sub>▲ 本章讲解视频（2.7 分钟）。<a href="../assets/video/ch09-adc.mp4">MP4</a> · <a href="../assets/video/ch09-adc.srt">字幕</a></sub>
</p>

<details>
<summary>旁白文字稿</summary>

1. 逐次逼近之前，要先让采样电容充满。源阻抗越大，需要的采样时间越长。充不满就转换，读数会偏向你上一次采过的电压。
2. F1 的 ADC 是 12 位。换算时用读数除以 4096，再乘参考电压。用 4095 做口算会有一个最小步长的差别。参考电压不是想当然的 3.3，要看你接到哪。
3. STM32F103C8 有 ADC，没有 DAC。把 F4 的 DAC 例程抄过来，编译或许能过，引脚上不会出现你要的模拟电压。换芯片前先看数据手册的功能表。
4. 这一帧是仓库画的逐次逼近：从最高位开始试，比参考大了就清掉，再试下一位。它帮助你记得，转换需要时间，不是把引脚读进来就结束。
5. 引脚要设成模拟输入，ADC 时钟要开，规则通道和采样时间都要写上。少一项，读数会停在一个奇怪的常数。先读一个已知电压，比如分压后的参考，再去测传感器。
6. 连续采样不要在每个转换完成里做重活。让 DMA 把结果搬进数组，半满和全满时再去算。Wokwi 的 BluePill 模型没有 DMA，这章的连续采样要在真板上对。
7. 读数乱跳时，先看参考电压和模拟地，再谈软件平均。平均能盖住一点噪声，盖不住一根飞线当成天线。实验板上，传感器线短一点，结果会诚实很多。
8. 三句挡住三件事：采样时间看信号阻抗，挡住采不准；换算除以 4096，挡住算不准；C8 没有 DAC，挡住抄错芯片。
9. 实验用电位器做分压，两端接地和参考，中间进 ADC。慢慢旋转，读数应该单调变化。跳变或反向，先查接线和参考，不要先改分辨率。
10. 读数跳变时按顺序查：先看接线和参考稳不稳，再看采样时间够不够，分辨率放在最后动。顺序反了，会把好配置改坏。

</details>
<!-- /video:ch09 -->
## 原理与适用范围

本章的采样数字都按 STM32F103C8T6 算，ADC 时钟取附录 D 的 12 MHz，换算分母用 4096。C8 没有 DAC；换到 F4 时，转换时间和上电校准的写法也不一样，下面会分别说明。

PCLK2 = 72 MHz，`ADCPRE=10`（÷6）得到 ADCCLK = 12 MHz。ADC 时钟上限是 14 MHz，选 ÷4 会得到 18 MHz，超过上限，所以 72 MHz 主频下只能用 ÷6。分频位怎么配见第 02 章的时钟树。RM0008 里常被引用的「`Tconv = 1 µs`」是 14 MHz、采样 1.5 周期时的例子，C8 跑 72 MHz 主频时到不了 14 MHz，按 12 MHz 算才对。出处是 [RM0008 Rev 21 第 11 章](#source-rm0008-adc)。

SAR ADC 的工作过程：采样开关合上，输入经源阻抗给采样电容充电；开关断开，电容上的电压保持住；然后从 MSB 开始逐位比较 12 次。转换时间是采样周期再加 12.5 个 ADCCLK。最长采样档 239.5 加 12.5 等于 252 个周期，`252 / 12e6 = 21 µs`。12 MHz 下各档采样时间：1.5 周期 = 125 ns，13.5 周期 = 1.125 µs，55.5 周期 = 4.625 µs，71.5 周期 = 5.958 µs，239.5 周期 = 19.958 µs。F4 的转换是采样再加 12 个周期，不要混用。

温度传感器要求采样时间至少 17.1 µs。`17.1e-6 × 12e6 = 205.2` 个周期，所以要选 239.5 周期，71.5 周期不够。温度传感器接 ADC1 的输入 16。内部参考 VREFINT 接 ADC1 的输入 17，典型值约 1.20 V，实际 VDDA 要用它在自己的板子上反推。两路都要先置 `ADC_CR2` 的 TSVREFE 才接通；有两个 ADC 的芯片上，这一位只在 ADC1 里，ADC2 的通道 16 和 17 接的是 VSS。温度公式是 `(V25 − VSENSE) / Avg_Slope + 25`。V25 ≈ 1.43 V、斜率 ≈ 4.3 mV/°C 是电气特性表里的典型值，不是出厂校准值，所以算出来的温度只能看变化趋势，绝对值会差几度。F4 有出厂校准值 `TS_CAL1`、`TS_CAL2`、`VREFINT_CAL`，F103C8 上没有。

DS5319 写明中密度器件都有两个 12 位 ADC。C8 有 ADC1 和 ADC2，没有 ADC3，没有 DAC，调用 `HAL_DAC_Start` 不会有任何输出。大容量 F103 和 F4 才有 DAC。后面核心原理里讲 DAC 的缓冲器、噪声和三角波，那些内容只适用于带 DAC 的型号。出处是 [DS5319 Rev 20](#source-ds5319-adc)。

LQFP48 第 10 脚 PA0 = ADC12_IN0。参考电压直接取第 9 脚 VDDA，这个封装没有单独的 VREF+，100 脚及以上的封装才有单独的 VREF+ / VREF−。第 03 章用第 10 脚点过灯，那时它是推挽输出；拿它采样前要重新配成模拟输入，否则读到的是输出驱动的电平。第 14 脚 PA4 在 C8 上是 ADC12_IN4 / SPI1_NSS，没有 DAC_OUT1 功能。

电压 = 码 × VDDA / 4096。名义 3.3 V 时 1 LSB = `3.3 / 4096 ≈ 0.806` mV，也就是后面表里的 806 µV。码 2048 是 `2048 / 4096 = 1/2`，名义 3.3 V 下正好 1.65 V。分母用 4095 会让每个读数偏一点，满量程附近大约差一个 LSB。

RM0008 第 11.4 节要求上电后做一次校准：ADON 置 1 之后至少等两个 ADC 时钟，再置 `ADC_CR2` 的 CAL。HAL 里对应 `HAL_ADCEx_Calibration_Start`，要放在 Start 之前。F4 的 ADC 没有这一步。

用 DMA 连续搬运采样结果的内容在第 10 章和附录 D：C8 只有 DMA1，ADC1 用通道 1。

## 关键插图


<p align="center">
  <img src="../assets/animations/sample-09-adc-sar-weights.svg" width="720" alt="SAR 权重行走与采样时间预算机制动画">
  <br><sub>▲ 自绘矢量动画（FA-002）。权重高亮 MSB→LSB，不是空转弹跳。</sub>
</p>


<p align="center">
  <img src="../assets/diagrams/sample-09-adc-sar.svg" width="760" alt="这颗芯片的 ADC 时钟是 12 MHz，最长转换 21 µs；采样太短时电容上仍是上一次的电压">
  <br><sub>▲ 自绘。STM32F103C8T6，LQFP48 第 10 脚 PA0 = ADC12_IN0，第 9 脚 VDDA 为参考。ADCCLK = 12 MHz。上半部分是一次正常转换：采样开关闭合再断开，比较器从 MSB 开始比较，最长一档 239.5 + 12.5 = 21 µs，码值乘 VDDA / 4096 得到电压。下半部分是采样时间太短：电容没充满，上面还是上一次的电压。右侧另标两处：÷4 得到 18 MHz，超过 14 MHz；C8 的第 14 脚没有 DAC。出处是 [RM0008 Rev 21 第 11 章](#source-rm0008-adc) 和 [DS5319 Rev 20 图 8](#source-ds5319-adc)。</sub>
</p>

<p align="center">
  <img src="../assets/illustrations/handraw/ch09-adc-sar.png" width="760" alt="Handraw：ADC SAR 采样与转换（原理示意）">
  <br><sub>▲ 知识轨（Handraw · 原理示意/非实拍）。ADCCLK 12 MHz；最长 239.5+12.5=21 µs；采样太短则电容仍是上次电压；不是示波器实拍。</sub>
</p>

<p align="center">
  <img src="../assets/gif/adc-sample.gif" width="640" alt="一次采样之后做 MSB 比较，ADCCLK 是 12 MHz">
  <br><sub>▲ 动图版，只演示一次正常的采样和 MSB 比较。印刷版只有上面的静态图。</sub>
</p>

章首的 `adc-sar.svg` 和后面核心原理里的 `sar-adc.gif` 演示的是 12 次逐位比较的全过程。

## 时序与状态

| 情况 | 采样周期数 | 采样时间 | 加 12.5 之后 |
| --- | --- | --- | --- |
| 最短 | 1.5 | 125 ns | 14 / 12e6 |
| 最长 | 239.5 | 19.958 µs | 252 / 12e6 = 21 µs |
| 温度传感器 | 239.5，不用 71.5 | 17.1 µs 需要 205.2 个周期 | 71.5 周期只有 5.958 µs，不够 |
| 分频选错 | — | — | ADCCLK = 18 MHz，超过 14 MHz 上限，各档时间都不能用 |
| 换算 | — | — | 码 2048 在名义 3.3 V 下是 1.65 V，分母 4096 |

ADC 时钟 12 MHz。出处是 [RM0008 Rev 21 第 11 章](#source-rm0008-adc)。

## 常见坑与出处

| 现象 | 原因 | 处理 | 出处 | 出处里能查到什么 |
| --- | --- | --- | --- | --- |
| 读数还停在上一次的电压附近 | 采样时间太短，电容没充满，常见于按别的时钟算了采样时间 | 按 12 MHz 加长采样。信号源阻抗高时用 239.5 周期 | [RM0008](#source-rm0008-adc) | 转换时间 = 采样 + 12.5。12 MHz 下最长 252 周期是 21 µs |
| 为了更快把 ADC 设成 ÷4 | ADCPRE 选成了 ÷4 | 改回 ÷6，12 MHz | [RM0008](#source-rm0008-adc) | 14 MHz 是上限，18 MHz 超过它。1 µs 那个例子是 14 MHz 下的 |
| 温度通道噪声大、读数飘 | 采样不够 17.1 µs，或通道开错了 | 采样至少 17.1 µs，用 ADC1 通道 16，并置 TSVREFE | [RM0008](#source-rm0008-adc) | 17.1 µs 在 12 MHz 上是 205.2 个周期。VREFINT 是 ADC1 通道 17。ADC2 的 16/17 接到 VSS |
| 上电后第一批读数整体偏移 | 没校准 | Start 之前做校准 | [RM0008](#source-rm0008-adc) | 第 11.4 节：ADON 为 1 至少两个 ADC 时钟之后才能置 CAL |
| 换算结果比万用表高一点 | 分母用了 4095 | 分母用 4096 | [RM0008](#source-rm0008-adc) | 12 位满量程是 4096 步。码 2048 是半量程。参考是第 9 脚 VDDA |
| 蓝药丸上调用了 HAL_DAC_Start，PA4 没有模拟电压 | C8 没有 DAC | 要模拟电压就用 PWM 加 RC 滤波，或换带 DAC 的型号 | [DS5319](#source-ds5319-adc) | 中密度有两个 12 位 ADC。没有 ADC3，没有 DAC。第 14 脚不是 DAC_OUT1 |
| 第 10 脚点过灯，采样读数却像固定电平 | 脚还配置成推挽输出 | 采样前把 PA0 改成模拟输入 | [DS5319](#source-ds5319-adc) | LQFP48 第 10 脚 PA0 是 ADC12_IN0 |

## 学习目标

- [ ] 掌握分辨率、参考电压、量化误差的定量关系，能估算 1 LSB 对应的电压。
- [ ] 理解逐次逼近（SAR）ADC 的「采样—保持—比较」过程，会根据源阻抗选择采样时间。
- [ ] 会配置单次 / 连续 / 扫描 / 间断四种转换模式，并用 DMA 做多通道采集。
- [ ] 会用内部温度传感器与 Vrefint 反推芯片结温和真实 VDDA。
- [ ] 掌握 DAC 的输出模式、缓冲器开关对精度与噪声的影响。

## 核心原理

本章始终保留三份证据：引脚上的输入电压、ADC 的配置与状态、内存中的码值序列。只看串口打印出的一个电压，无法判断误差从哪里来。

### 1. 分辨率、参考电压与量化误差


<p align="center">
  <img src="../assets/diagrams/sample-09-vref-rails.svg" width="760" alt="码值换算电压与 Vref+/Vrefint 注意点">
  <br><sub>▲ 自绘。Code/4095×Vref+；绝对伏特先标 EST。</sub>
</p>

<p align="center">
  <img src="../assets/illustrations/handraw/ch09-vref-rails.png" width="760" alt="Handraw：码值换算与 Vref 量尺（原理示意）">
  <br><sub>▲ 知识轨（Handraw · 原理示意/非实拍）。Code/4095×Vref+；绝对伏特先标 EST；不是实拍。</sub>
</p>


ADC 像一把只有刻度没有游标的尺子。12 位就是把 0 到 Vref 这一段切成 4096 格，Vref = 3.3 V 时一格约 0.8 mV。被测电压落在两条刻线之间时，ADC 只能报离它最近的那条，所以读数天生带着最多半格的误差。尺子本身的长度就是 Vref，Vref 一晃，所有读数跟着晃。

12 位 ADC 在 3.3 V 参考下的最小可分辨电压（1 LSB）约为 **0.806 mV**；理想量化误差为 **±0.5 LSB**。

| 分辨率 N | 台阶数 2^N | Vref=3.3V 的 1 LSB | Vref=5.0V 的 1 LSB | 备注 |
| --- | --- | --- | --- | --- |
| 8 位 | 256 | 12.89 mV | 19.5 mV | 快速/粗略 |
| 10 位 | 1024 | 3.22 mV | 4.88 mV | — |
| 12 位 | 4096 | 806 µV | 1.22 mV | STM32F1/F4 主流 |
| 16 位 | 65536 | 50.4 µV | 76.3 µV | F3/G4/L4 等 |

计算公式：

```text
1 LSB     = Vref / 2^N                          (N 位分辨率)
V_in      = ADC_Code × Vref / 2^N               (正比式读数)
量化误差   = ±0.5 LSB = ±Vref / 2^(N+1)          (理想 ADC，仅考虑量化)
满量程电压 = Vref × (2^N - 1) / 2^N ≈ Vref - 1 LSB
```

> [!WARNING]
> STM32F1 的 `Vref` 就是 `VDDA`（模拟电源），二者共用引脚（100 脚以上封装才有独立 `VREF+`/`VREF-`）。所以 **VDDA 波动 = 读数直接误差**；精密测量要么外接基准，要么先测 Vrefint 做软件校准。

### 2. 逐次逼近（SAR）原理：采样保持 + 二分比较


<p align="center">
  <img src="../assets/diagrams/sample-09-sar-ladder.svg" width="760" alt="12 位 SAR 权重台阶与比较动作">
  <br><sub>▲ 自绘。MSB→LSB 权重；EOC 后读 DR。动画见 sample-09-adc-sar-weights。</sub>
</p>

<p align="center">
  <img src="../assets/illustrations/handraw/ch09-sar-ladder.png" width="760" alt="Handraw：12 位 SAR 权重台阶（原理示意）">
  <br><sub>▲ 知识轨（Handraw · 原理示意/非实拍）。MSB→LSB 权重；EOC 后读 DR；不是实拍。</sub>
</p>


SAR ADC 在玩猜数字。先拍一张快照：把输入电压存进一个小电容，然后断开，让它在比较期间不变。接着从一半猜起：「比 Vref/2 大吗？」大就记 1、继续猜上半段，小就记 0、猜下半段。12 位就猜 12 次。快照这一步最容易出事：信号源内阻大，小电容在采样时间里充不满，拍下来的就是一张糊照片。

SAR ADC 用「二分查找」逼近输入电压，N 位需要 N 次比较，从 MSB 到 LSB 依次确定每一位。

转换过程（以 12 位为例）：

1. **采样（Sample）**：采样开关闭合，外部输入经 `R_AIN` 给内部采样电容 `C_ADC` 充电，`C_ADC` 电压跟随输入。
2. **保持（Hold）**：开关断开，`C_ADC` 电压被「冻结」，转换期间保持不变。
3. **逐次逼近（SAR）**：比较器先把 `Vref/2`（MSB 置 1）与保持电压比较；输入大则保留该位、小则清零，再比较 `Vref/4`…… 共 12 次得到 12 位结果。

<p align="center">
  <img src="../assets/gif/sar-adc.gif" width="720" alt="SAR ADC 逐次逼近比较过程（程序生成 GIF）">
  <br><sub>▲ 动画：SAR ADC 逐次逼近比较过程（程序生成光栅动画，非实拍）</sub>
</p>

**采样时间与源阻抗**——最容易踩坑的地方。采样开关与信号源构成 RC 充电回路，必须在采样时间内把电容充到 1/2 LSB 以内。ST 给出的经验公式：

```text
t_s(最小) ≈ (R_AIN + R_ADC) × C_ADC × ln(2^(N+2))
其中 STM32F1：R_ADC ≈ 1 kΩ，C_ADC ≈ 8 pF，N = 12 → ln(2^14) ≈ 9.7
```

| 信号源阻抗 R_AIN | 最小采样时间 t_s（估算值） | C8 在 ADCCLK = 12 MHz 下的采样档 | 说明 |
| --- | --- | --- | --- |
| ≤ 1 kΩ | ≈ 78 ns | `000` = 1.5 周期（125 ns） | 运放直驱 / 分压电阻取小 |
| ≈ 10 kΩ | ≈ 0.78 µs | `010` = 13.5 周期（1.125 µs） | 常见电位器 |
| ≈ 50 kΩ | ≈ 3.9 µs | `101` = 55.5 周期（4.625 µs） | 高阻传感器 |
| ≈ 100 kΩ | ≈ 7.8 µs | `111` = 239.5 周期（19.958 µs） | 高阻时用这一档 |
| ≥ 1 MΩ | ≥ 78 µs | 239.5 周期仍不够 | **必须加电压跟随器缓冲** |

RM0008 在 14 MHz、采样 1.5 周期处写出的 1 µs 是 ADC 时钟跑到上限时的例子。71.5 周期在 12 MHz 上是 5.958 µs，不够温度通道要的 17.1 µs。本章的时间都按 12 MHz 算。对比表里 F4 那一列的「t_s + 12 周期」不适用于 F103。

扫描时前一通道还没放完电，高阻通道会串扰。加长采样，或在序列里插入间隔。

F1 的 `SMPx[2:0]` 可选：1.5 / 7.5 / 13.5 / 28.5 / 41.5 / 55.5 / 71.5 / 239.5 个 ADCCLK 周期（见 RM0008 第 11 章 ADC「通道采样时间」）。**源阻抗越大，采样时间要越长**，否则读数偏低且不稳。

### 3. 四种转换模式

四种模式的区别是 ADC 什么时候停手。单次是叫一声测一次；连续是测完马上再测，一直不停；扫描是按一张清单把几个通道依次测一遍；间断是清单很长时，每叫一声只往下测几个。实际项目里最常见的是扫描加连续，再交给 DMA 搬数。

单次用于按需采样省电，连续用于实时监测，扫描用于多通道轮询，间断用于「一次触发转一组」。

| 模式 | 关键位 | 行为 | 典型场景 |
| --- | --- | --- | --- |
| 单次 Single | `CR2.CONT=0` + 软件/外部触发 | 触发一次转一次，转完停止 | 电池电压巡检 |
| 连续 Continuous | `CR2.CONT=1` | 转完立即重启，数据不断刷新 | 实时波形/监测 |
| 扫描 Scan | `CR2.SCAN=1` | 按 SQR 序列依次转多通道 | 多路传感器轮询 |
| 间断 Discontinuous | `CR1.DISCEN=1`、`DISCNUM` | 每次触发只转 n 个通道后暂停 | 分组采样 |
| 外部触发 | `CR2.EXTSEL`/`EXTTRIG` | 定时器/EXTI 触发规则组 | 与 PWM 同步采样 |

规则组（Regular）最多 16 个转换序列，注入组（Injected）最多 4 个且可打断规则组（用于电机电流的「紧急」采样）。

<p align="center">
  <img src="../assets/illustrations/handraw/ch09-scan-sequence.png" width="760" alt="Handraw：四个通道的扫描序列与 30 µs 时间条（原理示意）">
  <br><sub>▲ 知识轨（Handraw · 原理示意/非实拍）。看哪里：左边是 SQR 序列，每行给出采样档、含 12.5 周期的总周期数与微秒数；右边的时间条按周期数等比，四段加起来是 360 周期 = 12 MHz 下整 30 µs。证明什么：一轮扫描的间隔由每一档采样时间决定，换一档整轮就变；温度通道要 239.5 档是因为 17.1 µs × 12 MHz = 205.2 周期。不能证明什么：这是按 12 MHz 的 ADCCLK 算的账，不涉及源阻抗实测、串扰与 DMA 搬运开销，也不是示波器截图。出处是 [RM0008 Rev 21 第 11 章](#source-rm0008-adc)。</sub>
</p>

### 4. 多通道 + DMA

多通道连续采样时，ADC 每转完一个通道就把结果放进同一个 DR 寄存器，下一个结果马上会盖掉它。CPU 来不及每次都去取，所以让 DMA 守在 DR 门口，每来一个就搬进数组的下一格，搬到末尾再回到开头。CPU 想看最新值时，直接读数组就行。

多通道高速采集的标准姿势是「扫描模式 + 连续转换 + DMA 循环搬运」，CPU 完全不参与。

- 扫描模式下，每转完一个通道产生一次 DMA 请求（`CR2.DMA=1`），把 `DR` 搬到内存数组。
- DMA 用**循环模式**，数组自动回卷，形成环形缓冲区。
- 数据对齐 `CR2.ALIGN`：右对齐（默认，低 12 位有效）或左对齐（高 12 位有效，便于 16 位整型直接比较）。
- STM32F103C8 有 ADC1 和 ADC2，没有 ADC3，也没有 DAC。C8 只有 DMA1，ADC1 是通道 1。半字宽度和 CNDTR 的计算见第 10 章。

| 项 | F1（RM0008 第 11 章） | F4（RM0090 第 13 章） |
| --- | --- | --- |
| 分辨率 | 12 位 | 12 位 |
| 最大采样率 | 1 MSPS（ADCCLK=14 MHz） | 2.4 MSPS（三重交替可达 7.2 MSPS） |
| 规则通道 | 16 | 16 |
| 注入通道 | 4 | 4 |
| 转换时间 | t_s + 12.5 周期 | t_s + 12 周期 |
| 内部通道 | 温度 CH16、Vrefint CH17 | 温度、Vrefint、VBAT |

<p align="center">
  <img src="../assets/animations/dma-circular.svg" width="820" alt="ADC 扫描序列通过 DMA 循环写入内存数组，HT 和 TC 分别交出前后半区">
  <br><sub>▲ 多通道结果从同一个 ADC_DR 依次进入数组，HT/TC 只说明哪一半可处理。图不能证明通道顺序、数据宽度或采样时间正确，这三项仍要和 SQR、DMA 配置及波形对账（FA-002 · IG-012 · C-03/C-10/C-27/C-31）。</sub>
</p>

### 5. 内部温度传感器与 Vrefint

芯片里自带两个不用接线的通道。一个是温度传感器，能大致告诉你芯片有多热，精度只够看趋势。另一个是 Vrefint，一个约 1.20 V 的固定电压。它的用处是反过来量尺子：已知被测的是 1.20 V，读出来的码值就能算出这时 VDDA 到底是多少，再拿它去修正别的通道。

温度传感器与 Vrefint 是 ADC 的「内部通道」，能免费拿到芯片结温和真实 VDDA，用来校准外部读数。

**温度（F1，RM0008 第 11 章「温度传感器」）**：先置 `CR2.TSVREFE=1` 使能，选通道 16。

```text
V_sense = V25 - Slope × (T - 25)
=> T(°C) = (V25 - V_sense) / Slope + 25
F1 典型值：V25 ≈ 1.43 V，Slope ≈ 4.3 mV/°C
```

**Vrefint 反推 VDDA**：通道 17 测的是约 1.20 V 的固定内部基准。

```text
VDDA      = 1.20 V × 4096 / ADC_Read(Vrefint_CH17)
真实 V_in = ADC_Read(ch) × VDDA / 4096
```

> F4/L4 等系列提供**出厂校准值** `TS_CAL1`(30°C)/`TS_CAL2`(110°C) 与 `VREFINT_CAL`，存于系统存储区，直接读取即可，精度远高于查典型值。

### 6. DAC 输出模式、缓冲器与噪声

DAC 是 ADC 反过来：你给一个 0 到 4095 的数，它在引脚上给出对应的电压。输出缓冲器像一个跟班，打开以后能带动更重的负载，但它自己走不到 0 V 和 VDDA 的两头。想让电压按波形变化，就让定时器按固定节拍触发，DMA 每拍从表里取一个数送过去。

F1 DAC 为 12 位、双通道，输出电压 `V_out = Vref × DOR / 4096`；输出缓冲器能增强带载能力，但会引入失调且无法满摆幅。

| 特性 | 说明 | 关键位/寄存器 |
| --- | --- | --- |
| 分辨率 | 12 位，双通道 DAC1/DAC2 | `DHR12Rx`/`DHR12Lx`/`DHR8Rx` |
| 输出缓冲 | 使能后可驱动一定负载，输出不能到 0 V/VDDA 轨 | `DAC_CR.BOFFx` |
| 触发模式 | 定时器/EXTI 触发更新，可配三角波/噪声 | `DAC_CR.TSELx`/`TENx` |
| 噪声/三角波 | 内置 LFSR 噪声与三角波发生器 | `DAC_CR.WAVEx`/`MAMPx` |
| DMA | 支持 DMA 连续更新（配合定时器做任意波形） | `DAC_CR.DMAENx` |

- **缓冲器关闭**时输出阻抗高（≈15 kΩ），可接近满摆幅，适合高阻负载；**开启**时带载强，但失调典型 ±10 mV、且无法到轨。
- 噪声来源：VDDA 纹波、数字开关耦合、缓冲器噪声、LSB 量化噪声。精密场合建议外部加 RC 低通或运放缓冲。
- 产生正弦/任意波形：定时器触发 + DMA 循环搬运查找表，触发频率决定输出频率。

> F103C8（BluePill 常见型号）**没有 DAC**。DAC 从 F103 大容量（xC/xD/xE）和 F4 才有。中容量片子要模拟电压，用 PWM 加 RC，或者外接 DAC 芯片。

## 硬件与接线

| 开发板 | 功能 | 引脚 | 备注 |
| --- | --- | --- | --- |
| BluePill / Nucleo F103 | ADC1_IN0 | PA0 | 模拟输入，别再当 GPIO 用 |
| 同上 | 内部温度 / Vrefint | 无外部脚 | F1 通道 16 / 17，先开 TSVREFE |
| 有 DAC 的型号 | DAC_OUT1 | PA4 | F103C8 没有这个脚的 DAC 功能 |

信号源阻抗按上一节的采样时间表来选。高阻传感器先加跟随器，不要靠把采样时间拉到 239.5 周期硬撑。

## 代码实现

F1 在启动转换前必须做一次校准；多通道连续采集用 DMA，单次慢信号用轮询就够。

```c
HAL_ADCEx_Calibration_Start(&hadc1);          /* F1 必做；F4 没有这一步 */
HAL_ADC_Start(&hadc1);
HAL_ADC_PollForConversion(&hadc1, 10);
uint16_t code = HAL_ADC_GetValue(&hadc1);
/* 电压 = code * VDDA / 4096，分母是 4096 不是 4095 */
```

多通道循环搬运见 [`examples/adc-dma/`](../examples/adc-dma/)：`HAL_ADC_Start_DMA` 之前同样要先校准。半传输回调里处理前一半，完成回调里处理后一半。

定时器触发（TRGO）让采样间隔不依赖主循环：

```c
TIM_MasterConfigTypeDef mst = {0};
mst.MasterOutputTrigger = TIM_TRGO_UPDATE;
mst.MasterSlaveMode     = TIM_MASTERSLAVEMODE_DISABLE;
HAL_TIMEx_MasterConfigSynchronization(&htim3, &mst);
/* ADC 外部触发源选 TIM3_TRGO，再 HAL_ADC_Start */
```

有 DAC 的芯片才写下面这段。F103C8 调用会落空，不要在 BluePill 上照抄：

```c
HAL_DAC_Start(&hdac, DAC_CHANNEL_1);
HAL_DAC_SetValue(&hdac, DAC_CHANNEL_1, DAC_ALIGN_12B_R, 2048); /* 2048 / 4096 = 1/2，名义 3.3 V 下是 1.65 V */
```

## 动手实验

1. **输入与码值对账**：PA0 接 10 kΩ 电位器，分别取低、中、高三点。每点同时记录万用表电压、ADC 码值和按实测 VDDA 换算的电压。
2. **外设状态对账**：读 Vrefint 反推 VDDA，并保存校准前后读数、EOC 状态和采样时间。不要把 1.20 V 典型值当成单片校准值。
3. **内存结果对账**：PA0/PA1 两通道扫描 + DMA 循环采 64 个半字。记录数组顺序、HT/TC 次数和 CNDTR；再用 100 kΩ 高阻源比较 1.5 与 239.5 周期各 100 次的均值和极差。

### 7. 校准、模拟看门狗、注入通道


<p align="center">
  <img src="../assets/diagrams/sample-09-sample-time.svg" width="760" alt="ADC 采样时间 SMPR 与源阻抗预算">
  <br><sub>▲ 自绘。ADCCLK≤14 MHz；软源拉长 SMP。</sub>
</p>

<p align="center">
  <img src="../assets/illustrations/handraw/ch09-sample-time.png" width="760" alt="Handraw：ADC 采样时间与源阻抗（原理示意）">
  <br><sub>▲ 知识轨（Handraw · 原理示意/非实拍）。ADCCLK≤14 MHz；软源拉长 SMP；不是实拍。</sub>
</p>


校准只在 F1 上电后做一次；模拟看门狗负责“越界才打断 CPU”；注入通道可以插队，不打乱规则组的 DMA。

| 功能 | 什么时候用 | HAL |
| --- | --- | --- |
| 校准 | F1 每次上电、Start 之前 | `HAL_ADCEx_Calibration_Start` |
| 模拟看门狗 | 电压超窗再进中断 | `HAL_ADC_AnalogWDGConfig` |
| 注入组 | 规则组 DMA 跑着，偶尔插一个通道 | `HAL_ADCEx_InjectedStart_IT` |

注入组最多 4 个通道。规则组的 DMA 缓冲不要和注入结果混在同一个数组里。

ADC 读数「不对」先分清三岔：末位抖动、顶满贴零、整体偏置——三条路的根因和修法完全不同。

<p align="center">
  <img src="../assets/diagrams/sample-09-adc-triage.svg" width="760" alt="ADC triage: sample time vs source impedance, VDDA rail clamp, calibration sequence">
  <br><sub>▲ 自绘。岔口一：末位抖动不是随机噪声，是采样电容没充满——`t_s ≈ (R_AIN + 1 kΩ) × 8 pF × ln(2^14) ≈ (R_AIN + 1 kΩ) × 78 ns`，100 kΩ 源阻抗需要约 7.8 µs，而 12 MHz 下 1.5 周期只有 125 ns，差 60 倍；把 `SMPR2 SMP0[2:0]` 设为 111（239.5 周期 = 19.958 µs）；ADCCLK 必须 ≤14 MHz（÷6 得 12 MHz，÷4 得 18 MHz 越限）；RC 缓冲只在 R×C ≪ 采样间隔时有意义，≥1 MΩ 仍需跟随器。岔口二：4095 是钳位不是读数——VIN 高于 VDDA 会打开输入保护；恒 0 先查 PA0 是不是还配着推挽输出；LQFP48 没有独立 VREF+，第 9 脚 VDDA 就是量尺，跌 1% 全表偏 1%；转换运行中量第 9 脚，保持 VSSA ≤ VIN ≤ VDDA；用 CH17 Vrefint 反推对账：VDDA = 1.20 V × 4096 / code。岔口三：上电后最初几个码整体偏移且不随输入走——没校准：ADON 后等两个 ADCCLK，RSTCAL=1 等自清，再 CAL=1 等自清；校准期间不跑转换，`HAL_ADCEx_Calibration_Start` 必须在 `HAL_ADC_Start` 之前；0 V 和半量程各测一组：两处恒定差是偏置，随量程增长是增益。校准流程与采样档位见 [RM0008 Rev 21 第 11 章](#source-rm0008-adc)，精度实践见 AN2834。</sub>
</p>

<p align="center">
  <img src="../assets/illustrations/handraw/ch09-adc-triage.png" width="760" alt="Handraw：ADC 三岔口排障（原理示意）">
  <br><sub>▲ 知识轨（Handraw · 原理示意/非实拍）。岔口：采样未充满 / VDDA 钳位 / 上电未校准；不是实拍。</sub>
</p>

### 8. 通道和引脚（F103 ADC1）

| 通道 | 引脚 / 来源 |
| --- | --- |
| IN0 ~ IN7 | PA0 ~ PA7 |
| IN8、IN9 | PB0、PB1 |
| IN16 | 片内温度传感器 |
| IN17 | Vrefint（约 1.20 V） |

别的封装和 F4 的通道表以数据手册的 Pinout 为准，不要拿这张表去套 H7。

### 9. 自测

1. 12 位、VREF = 3.3 V，码值 2048 对应多少伏？为什么不是 `2048/4095*3.3`？
2. SAR 试探 bit10 时，已经保留 bit11，试探值应该是 3072 还是 1024？
3. 为什么 F103C8 的工程里不该出现 `HAL_DAC_Start`？

离开本章前，应有三点电压/码值表、Vrefint 反推的 VDDA，以及一份带通道顺序和 CNDTR 的 DMA 数组记录。

## 相关资源

- RM0008 第 11 章 ADC、第 12 章 DAC（大容量才有 DAC）。
- 数据手册 DS5319：ADC 引脚、采样时间与源阻抗。
- 示例：[`examples/adc-dma/`](../examples/adc-dma/)。
- 配图：[`assets/animations/adc-sar.svg`](../assets/animations/adc-sar.svg)、[`assets/gif/sar-adc.gif`](../assets/gif/sar-adc.gif)（作者自绘 / 程序生成，不是实拍）。

- 手机阅读版：[第 09 章 · ADC与DAC（公众号图文）](https://mp.weixin.qq.com/s/GCSYHfF66I5Qr88pK4rXIA)

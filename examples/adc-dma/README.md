# adc-dma —— ADC 多通道 + DMA 循环采集 + 滑动平均滤波

> 难度：★★★☆　｜　涉及外设：ADC + DMA　｜　对应章节：[09 ADC 与 DAC](../../docs/09-ADC与DAC.md) / [10 DMA](../../docs/10-DMA.md)

<p align="center">
  <img src="../../assets/animations/adc-sar.svg" width="760" alt="ADC 采样保持与逐次逼近过程">
  <br><sub>▲ 动画：ADC 采样保持 + 逐次逼近（SAR）比较过程（作者自绘矢量图）</sub>
</p>

## 一、功能说明

用 ADC1 扫描 **3 个通道**（PA0/PA1/PA4），**连续转换 + DMA 循环搬运**，CPU 完全不参与采样：

- 每 100ms 求一次每通道的**块平均**（16 点），再对块平均做**滑动平均**（窗口 8）低通滤波；
- 按 `V = ADC_Code × Vref / 4096`（Vref=3.3V）换算电压；
- 板载 LED 每处理一次翻转，作为心跳。

## 二、硬件接线表

| 开发板 | 外设 | 引脚 | 接法 | 备注 |
| --- | --- | --- | --- | --- |
| BluePill | 电位器 / 传感器 1 | PA0 (ADC1_IN0) | 中点接 PA0，两端接 3.3V/GND | 分压测电压 |
| BluePill | 传感器 2 | PA1 (ADC1_IN1) | 信号接 PA1 | — |
| BluePill | 传感器 3 | PA4 (ADC1_IN4) | 信号接 PA4 | 与 SPI1_NSS 复用，注意冲突 |
| BluePill | LED | PC13 | 板上已接 | 心跳指示 |

> **PA4 与 SPI1_NSS 复用**：若同时用 SPI1 片选，改用其它 ADC 通道（如 PA2/PA3=CH2/CH3）。

## 三、CubeMX 关键配置

| 配置项 | 取值 | 说明 |
| --- | --- | --- |
| ADC1 → Scan Mode | Enabled | 多通道扫描 |
| ADC1 → Continuous Conversion | Enabled | 连续转换 |
| ADC1 → Number of Conversions | 3 | 规则组 3 个 |
| ADC1 → Rank 1/2/3 | CH0 / CH1 / CH4 | 转换顺序 |
| ADC1 → Sampling Time | 55.5 cycles | 高阻源要加长 |
| ADC1 → DMA Continuous Requests | Enabled | 每次转换都请求 DMA |
| DMA | ADC1 → DMA1 Channel1, **Circular** | 循环模式 |
| ADC 时钟 | PCLK2/6 = 12MHz | ≤14MHz |
| GPIO | PA0/PA1/PA4 → Analog | 必须模拟模式 |

## 四、关键代码解读

**1) 扫描 + 连续 + DMA 循环（一次配置，后台自动跑）**

```c
hadc1.Init.ScanConvMode       = ADC_SCAN_ENABLE;
hadc1.Init.ContinuousConvMode = ENABLE;
hadc1.Init.NbrOfConversion    = ADC_NUM_CH;      /* 3 */
/* DMA 用循环模式，数组自动回卷形成环形缓冲 */
hdma_adc1.Init.Mode = DMA_CIRCULAR;
HAL_ADC_Start_DMA(&hadc1, (uint32_t *)g_adc_buf, ADC_BUF_SIZE);
```

**2) DMA 缓冲区布局（按转换顺序交错）**

```
下标: 0    1    2    3    4    5   ...
通道: CH0  CH1  CH4  CH0  CH1  CH4 ...
```

因此通道 `ch` 的数据在下标 `ch, ch+3, ch+6, ...`：

```c
static uint32_t adc_channel_avg(uint8_t ch) {
    uint32_t sum = 0;
    for (int s = 0; s < ADC_SAMPLES; s++) sum += g_adc_buf[s*ADC_NUM_CH + ch];
    return sum / ADC_SAMPLES;
}
```

**3) 滑动平均滤波（低通，抑制噪声）**

```c
static float moving_average(uint8_t ch, float v) {
    g_ma_buf[ch][g_ma_idx] = v;                 /* 写入窗口 */
    /* 求窗口内平均，返回滤波结果 */
    ...
}
```

窗口越大越平滑但响应越慢——采样率与噪声权衡。

**4) 电压换算**

```c
V = (float)code * 3.3f / 4096.0f;   /* 12 位：2^12 = 4096 */
/* 1 LSB ≈ 3.3V/4096 ≈ 0.806 mV */
```

## 五、编译烧录步骤

1. CubeMX 生成 F103C8 工程，按上表配 ADC1 + DMA，覆盖 `Core/Src/main.c`。
2. 编译下载；若已有 `MX_ADC1_Init`/`MX_DMA_Init`，删除本文件的对应初始化以免重复。
3. 用调试器观察 `g_adc_buf` 或把电压通过串口打印。

## 六、预期现象

- 转动接 PA0 的电位器，对应通道读到的电压随之变化（0~3.3V）；
- 板载 LED 约 5Hz 闪烁（每 100ms 处理一次）；
- 滑动平均后读数比原始值更平稳（抖动更小）。

## 七、常见问题

| 现象 | 原因 | 解决 |
| --- | --- | --- |
| 读数一直是 0 | 引脚没配成 Analog / 没接信号 | GPIO 设 `GPIO_MODE_ANALOG` |
| 读数一直是 4095 | 引脚接 3.3V / 悬空上拉 | 检查接线 |
| 读数抖动大 | 采样时间太短 / 源阻抗高 | 加大采样时间，加滑动平均 |
| 通道数据错位 | 缓冲区布局理解错 | 按 `s*3+ch` 取通道数据 |
| 只采了一次 | DMA 配成 Normal | 改 `DMA_CIRCULAR` |
| 精度差 | VDDA 不是精确 3.3V | 测 Vrefint 反推真实 VDDA |
| ADCCLK 超 14MHz | 预分频不对 | 用 `/6` 或 `/8` |

## 八、相关资源

- 参考手册 **RM0008** 第 11 章（ADC，含 SQR/SMPR/CR2 位说明）、第 10 章（DMA 映射表）
- 数据手册 **DS5319**（ADC 通道与引脚、VDDA 范围）
- 相关图：[`assets/animations/adc-sar.svg`](../../assets/animations/adc-sar.svg)、[`assets/gif/sar-adc.gif`](../../assets/gif/sar-adc.gif)、[`assets/animations/dma-circular.svg`](../../assets/animations/dma-circular.svg)
- 免责声明：本示例配图为作者自绘矢量图/程序生成动画，非厂商实拍照片。

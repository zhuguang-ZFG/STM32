---
title: S10 DAC：芯片也能输出模拟量
status: done
difficulty: 2
minutes: 30
---

# S10 DAC：三个外设协作出一条正弦波

> 🎯 示波器上只有一条直线，程序却没有报错：DAC 里有数，TIM 也在跑，DMA 甚至显示已使能。到底是谁没听见谁？让芯片唱出 1kHz 正弦不是一次写寄存器，而是一场三重奏：**DAC** 把数字变电平，**TIM** 打拍子，**DMA** 递乐谱。少接一根暗线，三个外设都“正常”，整首曲子仍然沉默。

## 本章精髓

1. DAC 本质是"电阻梯形网络"：12 位数字→4096 级电压（0~VREF）；建立时间决定它"唱多快不跑调"（与 PWM+滤波冒充 DAC 的方案对比：真 DAC 无纹波、响应快）。
2. 触发+DMA 是自动播放的关键：TIM 每次更新事件触发 DAC 取下一个样本，DMA 从正弦表自动递数：更新率 × 表长 = 波形频率（奈奎斯特定律在此现身：每周期至少几十个点才像正弦）。
3. 对齐方式是个坑：12 位数据有左/右对齐两种写法，写错对齐=幅度/波形全乱。

- **能理解**：为什么波形频率 = 样本率 ÷ 表长；为什么"84MHz 出 64kHz 样本率"在 F407 上不能整除（以及怎么取舍）。
- **能用**：把 DAC1 接示波器，跑出一条 1kHz 正弦；把表长从 64 砍到 8，亲眼看"正弦退化成阶梯三角"。

## 先修

- [S6 TIM](06-tim.md)、[S8 DMA](08-dma.md)、[S9 ADC](09-adc.md)（对照）。

## 先跑起来（10 分钟 quick win）

PA4（DAC_OUT1，以 datasheet 为准）输出：先写一个固定值 2048，万用表量到约 VREF/2，芯片第一次"唱出"一个稳定的音高。

测量前先下注：如果万用表读数正确，能不能直接证明正弦播放链也正确？答案是不能。这个 quick win 只给 DAC 本体做单人试音；TIM 的拍子与 DMA 的递谱还没上场。先把“能出一个电平”和“能连续出波形”分开，后面的排错就不会三件事一起猜。

## 动画：三重奏的协奏

四阶段循环：① **TIM6 打拍**：计数器从 0 数到 ARR，更新事件（TRGO）标志亮起；② **DMA 递谱**：正弦表的索引前进一格，下一个样本被搬进 DAC 的 DHR12R1；③ **DAC 开嗓**：DHR 在触发沿搬到 DOR，电压跳到新台阶；④ **波形出来**：一串台阶连成的近似正弦随时间向左滚动。底部的样本指针在 64 点表里循环扫过，正是"DMA 替你递乐谱"的全部含义。

![DAC 三重奏动画](/anim/dac-trio.svg)

## 板卡事实

- DAC1 输出在 **PA4**（DAC_OUT1），DAC2 在 **PA5**（DAC_OUT2）；引脚模式 **模拟**（MODER=0b11，[S3](03-gpio.md)），**不需要 AF 编号**：DAC 是模拟外设，不走复用矩阵。
- DAC 控制器基址 `DAC_BASE = APB1 + 0x7400 = 0x40007400`（CMSIS 已核对）；时钟在 RCC_APB1ENR bit29 = `RCC_APB1ENR_DACEN_Msk`（0x20000000，CMSIS 已核对）。
- DAC1 的 DMA 请求：**DMA1 Stream5 Channel7**（RM0090 Table 43，与 [S8](08-dma.md) 同源映射表；DAC 在 APB1 → DMA1）。
- 12 位数据有三种写寄存器：`DHR12R1`（右对齐 12 位）、`DHR12L1`（左对齐）、`DHR8R1`（8 位），本章用右对齐。
- 电压参考 VREF 由板卡供电决定（多数板 VREF = VDD = 3.3V，以你的板卡规格书为准）。

## 小节结构

| 小节 | 内容 | 四件套 |
|---|---|---|
| DAC 原理 | 电阻网络 vs PWM+RC 滤波对比实测 | 库解析 |
| 静态输出 | 右对齐写 DHR12R1；万用表验证 VREF 关系 | 配置 |
| TIM 触发 | TRGO 选择+DAC 触发使能的链路 | 配置 |
| DMA 递谱 | 正弦表生成（const 数组，回 C1 经济学）+循环模式 | 代码分析 |
| 波形数学 | 样本率/表长/频率关系；点太少变三角波演示 | 代码分析 |
| 输出缓冲 | 带载能力与建立时间的取舍 | 配置 |
| SPL 对照 | DAC_Init/DAC_DMACmd 落位 | 库解析 |

## 一、DAC 原理：电阻网络 vs PWM+RC 滤波

DAC 把数字变成电压靠的是 **R-2R 电阻梯形网络**：12 位数字每一位接一个电阻，按权重加出模拟电压。结果是一条**真正连续**的电压（0~VREF 分 4096 级），不是占空比方波。

与"PWM + RC 滤波冒充 DAC"对照：

| 维度 | 真 DAC | PWM+RC |
|---|---|---|
| 输出 | 4096 级直流 | 平均值近似，纹波随截止频率变 |
| 响应 | 一个建立时间（µs 级）出值 | RC 充放电，时间常数大才平滑 |
| 高频 | 能跟到几十 kHz | 滤波器把高频也一起滤了 |
| 引脚 | 专用 DAC 引脚 | 任何定时器通道引脚 |
| 成本 | 只有带 DAC 的型号 | 所有 STM32 都行 |

结论：要稳、要快、要带宽，用真 DAC；只是要个慢变量（背光亮度），PWM+RC 够了。F407 有两个 DAC 通道，本章用 DAC1。

## 二、静态输出：先写一个数，量一个电压

最小配置：不开触发、不开 DMA，写一个数读一个电压：

```c
#include "stm32f407.h"   /* CMSIS：DAC_TypeDef + 各 _Msk */

static void dac1_init_static(void)
{
    RCC->APB1ENR |= RCC_APB1ENR_DACEN_Msk;     /* 开 DAC 时钟 */
    RCC->AHB1ENR |= RCC_AHB1ENR_GPIOAEN_Msk;   /* 开 GPIOA 时钟（[S3] 纪律） */
    /* PA4 模拟模式：MODER=0b11，无上下拉，无 AF */
    GPIOA->MODER |= (0x3u << (4u * 2u));
    GPIOA->PUPDR &= ~(0x3u << (4u * 2u));

    /* DAC_CR：使能通道 1、开启输出缓冲（BOFF1=0） */
    DAC->CR |= DAC_CR_EN1_Msk;                 /* EN1 = bit0（CMSIS 已核对） */
    /* BOFF1 = bit1：0 = 缓冲开（默认带载能力强）；1 = 缓冲关（高阻，rail-to-rail） */
}

static void dac1_set(uint16_t code)   /* code: 0~4095（右对齐 12 位） */
{
    DAC->DHR12R1 = code & 0x0FFFu;             /* 写 DHR12R1：右对齐，高 20 位忽略 */
    /* 写完 DHR 后，无触发模式下约 3 个 APB1 时钟搬到 DOR（输出寄存器） */
}
```

写 `2048`：DOR 输出 ≈ VREF × 2048/4096 = VREF/2。VREF=3.3V → 1.65V；万用表量到的就是这个数。**12 位的一半写法是 2048（0x800），不是 4096：右对齐时高 4 位是 0，写 0x800 是对的，写 0x8000 就是左对齐寄存器的事。** 这是骨架坑列表里"对齐写错=幅度只剩 1/16"的来源：把右对齐的 2048（0x800）写进左对齐寄存器 DHR12L1（数据在 bit4~15），实际输出只有 2048>>4 = 128 级 → 幅度 1/16。

## 三、TIM 触发：让 DAC 跟着拍子取数

自动播放的第一根线：TIM6 每次数到 ARR 产生更新事件，经 TRGO 通知 DAC"该取下一个样本了"。配置链路（TIM6 在 APB1，`RCC_APB1ENR_TIM6EN_Msk` = 0x10，CMSIS 已核对）：

```c
static void tim6_dac_trigger_init(uint16_t psc, uint16_t arr)
{
    RCC->APB1ENR |= RCC_APB1ENR_TIM6EN_Msk;
    TIM6->PSC = psc;                            /* 预分频（[S6] 公式 f=TIMclk/(PSC+1)/(ARR+1)） */
    TIM6->ARR = arr;
    TIM6->CNT = 0;
    /* CR2.MMS = 010：更新事件作 TRGO 输出（CMSIS：MMS 在 bits4-6，010 = TIM_CR2_MMS_1 = 0x20） */
    TIM6->CR2 = (TIM6->CR2 & ~TIM_CR2_MMS_Msk) | TIM_CR2_MMS_1_Msk;   /* update → TRGO */
    TIM6->CR1 |= TIM_CR1_ARPE_Msk | TIM_CR1_CEN_Msk;   /* ARR 预装载 + 启动 */
}

static void dac1_trigger_enable(void)
{
    /* DAC_CR：TEN1=bit2 使能触发、TSEL1=bits3-5 选 000 = TIM6 TRGO（CMSIS：0x38 掩码） */
    DAC->CR |= DAC_CR_TEN1_Msk;                  /* 触发使能；TSEL1 复位值就是 000 = TIM6，不用改 */
}
```

链路闭合：TIM6 数满 → TRGO → DAC 在触发沿把 DHR12R1 搬到 DOR → 电压跳变。但 CPU 还得在每次 TRGO 后手动写下一个 DHR12R1，这活交给 DMA，CPU 才真的"不用当指挥"。

在脑中按一次暂停：如果 DHR 里的数已经变化，DOR 却不动，先查触发链；如果 DOR 会动但只重复少量台阶，再查 DMA 的地址、宽度与循环模式。把症状分流后，开场那条直线就不再是“DAC 坏了”，而是一张能沿信号链逐站追查的工单。

## 四、DMA 递谱：正弦表 + 循环模式

正弦表是 const 数组，由编译器在 Flash 里生成（[C1 内存模型](../c/01-memory-model.md) 的"经济学"：const 数据住 Flash，不占 SRAM）。64 点正弦，幅度归一到 0~4095：

```c
#include <math.h>
#define SINE_N  64
static const uint16_t sine_table[SINE_N] = {
    /* 2048 + round(2047 * sin(2π i / 64))，i = 0..63；预生成，运行期直接用 */
    /* 生成脚本见本节末尾；占 128 字节 Flash */
};

static void dma1_stream5_sine_init(const uint16_t *table, uint16_t n)
{
    /* DAC1 → DMA1 Stream5 Channel7（RM0090 Table 43） */
    RCC->AHB1ENR |= RCC_AHB1ENR_DMA1EN_Msk;     /* 开 DMA1 时钟 */
    DMA1_Stream5->CR  = 0;                       /* 先禁用流再配（[S8] 纪律） */
    DMA1_Stream5->PAR = (uint32_t)&DAC->DHR12R1; /* 外设地址：DAC 的数据保持寄存器 */
    DMA1_Stream5->M0AR = (uint32_t)table;        /* 内存地址：正弦表 */
    DMA1_Stream5->NDTR = n;                      /* 传输个数 = 表长 */
    /* 配置：Ch7、内存递增、外设不递增、16→16 位、循环模式、高优先级 */
    DMA1_Stream5->CR = (0x7u << DMA_SxCR_CHSEL_Pos)   /* Channel 7 */
                     | DMA_SxCR_MINC_Msk               /* 内存递增：读完一个样本指针前进 */
                     | DMA_SxCR_PSIZE_16BITS_Msk        /* 外设 16 位 */
                     | DMA_SxCR_MSIZE_16BITS_Msk        /* 内存 16 位 */
                     | DMA_SxCR_CIRC_Msk                /* 循环模式：传完自动回卷到表头 */
                     | DMA_SxCR_DIR_Msk ? 0 : 0        /* 内存→外设（DIR=0） */
                     | DMA_SxCR_PL_Msk;                 /* 高优先级 */
    /* DAC 侧使能 DMA 请求 */
    DAC->CR |= DAC_CR_DMAEN1_Msk;                /* DMAEN1 = bit12（CMSIS 已核对） */
    DMA1_Stream5->CR |= DMA_SxCR_EN_Msk;          /* 最后使能流 */
}
```

正弦表生成（编译期可由脚本预生成填进 const 数组，免得 main 里跑 `sinf`，无 FPU 的型号连 math.h 都不一定方便）：

```c
/* 一次性生成器（仅用于离线生成 sine_table 的内容，不进固件） */
#include <math.h>
#include <stdio.h>
int main(void) {
    for (int i = 0; i < 64; i++) {
        printf("%d, ", (int)(2048 + round(2047 * sin(2*M_PI*i/64)));
        if (i % 8 == 7) printf("\n");
    }
}
```

启动顺序很关键：**先配 DAC（TEN1 + DMAEN1）再使能 DMA 流**：DMA 使能前 DAC 已经准备好接 TRGO；反过来 DMA 早早开始往 DHR 写，DAC 还没开触发，第一个样本会被下一个覆盖。这是 [S8 DMA](08-dma.md) "外设侧先就位"纪律的 DAC 版。

## 五、波形数学：样本率、表长、频率，以及"算不整"

三者的关系只有一条：

$$f_{\text{波形}} = \frac{f_{\text{样本}}}{N} = \frac{f_{\text{TIM6 更新}}}{N} = \frac{f_{\text{TIM6 时钟}}}{(PSC+1)(ARR+1) \cdot N}$$

霸天虎标准时钟树下 TIM6 时钟 = APB1 ×2 = 84MHz（[S2](02-rcc-clock.md)：APB1=42MHz，定时器时钟加倍）。要 1kHz、64 点：

$$f_{\text{样本}} = 1000 \times 64 = 64\text{kHz} \quad\Rightarrow\quad (PSC+1)(ARR+1) = \frac{84\text{MHz}}{64\text{kHz}} = 1312.5$$

**1312.5 不是整数**：这是 F407 上一个真实的尴尬，84MHz 除不出 64kHz。两种取舍（实测可证）：

| 取法 | PSC | ARR | 实际样本率 | 实际波形频率 | 误差 |
|---|---|---|---|---|---|
| 舍入 ARR=1311 | 0 | 1311 | 84e6/1312 = 64.024 kHz | **1000.38 Hz** | +0.038% |
| 舍入 ARR=1312 | 0 | 1312 | 84e6/1313 = 63.988 kHz | **998.94 Hz** | −0.11% |

两条都够准（音频/演示场景听不出），但**没有一条是精确 1kHz**。要精确 1kHz 的办法是改表长：`N × 1000 = 84e6/k`，找能整除的 k。`84e6/64000` 不整，但 `84e6/10500 = 8000` 整 → 样本率 8kHz、表长 8 → 1kHz 精确，但 8 点太疏（见下）；`84e6/84000=1000` → 样本率 84kHz，表长 84 → 1kHz 精确且 84 点够密。**选表长不光看频率，还要看 84MHz 能不能整除**，这是骨架"波形数学"小节最值得讲的一刀。

**点太少会发生什么**：奈奎斯特定律要求每周期至少 2 点（理论下限），实战要几十点才像正弦。把 N 从 64 砍到 8：8 个台阶连成的"正弦"更像阶梯三角：DAC 输出本身就是阶梯（零阶保持），表长越短阶梯越粗。骨架 quick win 后的"砍表长看退化"实验就是把这条数学眼见为实。

## 六、输出缓冲：带载能力 vs 建立时间

DAC 输出后有一个**输出缓冲放大器**（buffer），由 `DAC_CR.BOFF1`（bit1，CMSIS 已核对）控制：

- **缓冲开（BOFF1=0，默认）**：输出阻抗低（约 15kΩ 量级，手册值以 datasheet 为准），能直接驱动 ADC 输入或高阻负载；代价是输出范围不到 rail-to-rail（典型 0.2V~VDD−0.2V）；
- **缓冲关（BOFF1=1）**：输出直接是电阻网络，rail-to-rail 全幅；但输出阻抗高（MΩ 量级），带任何负载都会被拉低，必须外接高阻运放跟随。

选型很朴素：**接 ADC/高阻测量** → 缓冲开；**接外部运放做有源滤波** → 缓冲关 + 运放跟随。骨架坑里"输出接大负载掉电压"就是缓冲关了还接低阻负载，DAC 输出被分压，波形幅度凭空减半。

## 七、SPL 对照：`DAC_Init` / `DAC_DMACmd` 落位

SPL 的 DAC API 把 CR 的位组合打包成结构体字段（stm32f4xx_dac.c V1.8.0）：

| SPL API / 字段 | 寄存器落位 |
|---|---|
| `DAC_Init(DAC_Channel_1, &init)` | `init.DAC_Trigger` → TEN1 + TSEL1；`init.DAC_WaveGeneration` → WAVE1；`init.DAC_LFSRUnmask_*` → MAMP1 |
| `init.DAC_OutputBuffer` | `DAC_OutputBuffer_Enable` → BOFF1=0；`_Disable` → BOFF1=1 |
| `DAC_Cmd(DAC_Channel_1, ENABLE)` | CR `\|= EN1` |
| `DAC_DMACmd(DAC_Channel_1, ENABLE)` | CR `\|= DMAEN1` |
| `DAC_SetChannel1Data(Align, data)` | 写 `DHR12R1`（右对齐）/ `DHR12L1`（左对齐）/ `DHR8R1` |
| `DAC_SoftwareTrigger(DAC_Channel_1)` | CR `\|= SWTRIG1`（软件触发，不靠 TIM） |

读库姿势照旧（[S15](15-spl-anatomy.md)）：拿到 `DAC_Init` 先问"我的 trigger/buffer 选择被翻成了 CR 的哪几位"，逐位与本节 `dac1_trigger_enable` 对答案。**SPL 的 `DAC_Init` 不替你算 TIM6 的 PSC/ARR**：样本率与表长是数学关系，得自己按第五节算完填进 TIM6。库负责"配置 DAC"，数学负责"配出对的频率"，分工清晰。

## 附录：本章代码落点

本章 TIM6/DAC1/DMA1 链路配置以内联代码呈现（无独立工程），可直接进任何项目主组件。DAC 与 DMA1 Stream5 的请求映射依据 RM0090 Table 43（与 [S8](08-dma.md) 同源）；正弦表由离线生成器预填进 const 数组（见第四节末尾）。

## 记忆锚点

::: tip 一句话记住
**TIM 打拍、DMA 递谱、DAC 开嗓；波形频率=更新率÷点数，对齐写错全盘皆输。**
:::

**延伸**：DAC 三重奏动画见 [S10 动画](/anim/dac-trio.svg)；DMA 搬运机制在 [S8 DMA](08-dma.md) 详解；TIM 触发 DAC 的配合在 [S6 TIM](06-tim.md) 展开。

## 实物实验

- 万用表验证静态电压（2048≈VREF/2）；
- 示波器看 1kHz 正弦；把表长从 64 点砍到 8 点，亲眼看"正弦退化成阶梯三角"。

## 常见坑

- **对齐方式错**：右对齐的值写进左对齐寄存器，波形幅度只有 1/16。
- **DMA 数据宽度与 DAC 寄存器不匹配**：半字/字选错，波形全是毛刺。
- **忘开 DAC 时钟在 APB1**：DAC 在 APB1，RCC 位别找错（RM0090 §7）。
- **输出接大负载掉电压**：缓冲没开/负载太重，带载前先算输出阻抗。
- **DMA 与 DAC 启动顺序反了**：DMA 先使能会盖掉第一样本，DAC 侧先就位。

## 短自测

1. 为什么 PA4 配 DAC 不需要 AF 编号，而 SPI1 的 PA5 需要 AF5？
<details><summary>参考答案</summary>DAC 是模拟外设，输出的是连续电压，不走数字复用矩阵，引脚只要设成"模拟模式"（MODER=0b11）就直连 DAC 内部。SPI 的 SCK/MOSI 是数字信号，必须通过 AF 矩阵把定时器的输出连到具体引脚，所以有 AF5 这种编号。模拟外设（DAC/ADC）和数字外设（SPI/USART/TIM）的引脚路由是两套机制。</details>

2. 84MHz 的 TIM6 为什么出不来精确的 1kHz/64 点正弦？怎么取舍？
<details><summary>参考答案</summary>样本率要 64kHz，84MHz/64kHz = 1312.5 不是整数，PSC/ARR 都是整数乘积，凑不出 1312.5。取舍：舍入到 1312 或 1313，误差约 ±0.1%（听不出）；或改表长让 84MHz/目标样本率能整除（如表长 84、样本率 84kHz → 84MHz/84kHz=1000 整，精确 1kHz）。后者用更多点换精确，前者用小误差换简单。</details>

3. DAC 输出缓冲开与关各适合什么负载？为什么"缓冲关 + 大负载"波形会减半？
<details><summary>参考答案</summary>缓冲开：低输出阻抗、带载能力强，但输出范围不到 rail-to-rail，适合直驱 ADC 输入或高阻测量。缓冲关：rail-to-rail 全幅，但输出阻抗 MΩ 量级，必须接高阻运放跟随。"缓冲关 + 大负载"时，DAC 高内阻与负载分压，输出电压被拉到内阻与负载的分压比，波形幅度按比例减半甚至更多。</details>

4. DMA 为什么要循环模式？传完一次停了会发生什么？
<details><summary>参考答案</summary>正弦是周期信号，要无限循环播放。循环模式（CIRC）让 DMA 传完表长后自动把内存指针回卷到表头、NDTR 重载，无需 CPU 重新启动，这是"CPU 不用当指挥"的关键。若不用循环，DMA 传完 64 个样本就停，DAC 停在最后一个样本的电压，波形变成一条直流线。</details>

5. 启动顺序为什么是"先 DAC 后 DMA"？
<details><summary>参考答案</summary>DAC 侧（TEN1 + DMAEN1）先就位，意味着触发已使能、DMA 请求通道已开。这时再使能 DMA 流，第一个 TRGO 到来时 DAC 已准备好接样本、DMA 已准备好递样本。反过来若 DMA 先使能，它在 DAC 触发未开时就把样本往 DHR 写，等 DAC 触发一开，第一个样本已被后续样本覆盖，波形开头几个点错位。</details>

## 对照表：本章概念 → 仓库与上游落点

| 概念 | 落点 |
|---|---|
| DAC_CR 位（EN1/BOFF1/TEN1/TSEL1/DMAEN1） | CMSIS `stm32f407xx.h`（本站 `.trellis/ref/cmsis/`，逐位核对） |
| DHR12R1/DOR1 偏移 | 同上（DAC_TypeDef） |
| DAC1 → DMA1 Stream5 Ch7 | RM0090 Table 43（与 [S8](08-dma.md) 同源） |
| TIM6 CR2.MMS=010（update TRGO） | CMSIS `TIM_CR2_MMS_1_Msk`；[S6 TIM](06-tim.md) 时基公式 |
| 样本率/表长/频率公式 | 本章第五节；[C1](../c/01-memory-model.md) const 经济学 |
| 三重奏协奏动画 | [dac-trio.svg](/anim/dac-trio.svg)（四阶段） |

## 你做到了

- 芯片从"只认数字"变成"能输出连续电压"；
- TIM+DMA+外设的协奏范式再下一城——这是 RTOS 之前"硬件自动化"的巅峰。

回到开场的沉默三重奏：三个外设各自使能，不代表链路已经闭合。以后看到“寄存器都有值、引脚却没波形”，按 TIM 触发、DMA 搬运、DAC 输出的顺序逐站验票，比从头重配一遍更快。

<div class="achievement">
✅ 下一站：<a href="11-i2c.html">S11 I2C</a>：两根线上开茶话会，START 到 STOP 每一拍都有事件位等你签收。
</div>

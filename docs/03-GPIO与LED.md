# 03 GPIO 与 LED

> English: [GPIO and the LED](en/03-gpio-and-led.md)

> GPIO 是最基础的外设，用它输出电平、读取按键，是一切外设的入口。

<p align="center">
  <img src="../assets/animations/gpio-blink.svg" width="760" alt="GPIO 推挽输出驱动 LED 动画">
  <br><sub>▲ 动画：GPIO 推挽输出点亮 LED（电平、电流、波形同步，作者自绘矢量图）</sub>
</p>

<!-- video:ch03 -->
<p align="center">
  <video width="640" controls poster="../assets/video/ch03-gpio.png">
    <source src="../assets/video/ch03-gpio.mp4" type="video/mp4">
  </video>
  <br><sub>▲ 本章讲解 2.4 分钟。配音是微软 Edge 在线神经语音「晓晓」（zh-CN-XiaoxiaoNeural），经 edge-tts 调用。edge-tts 大部分源码为 LGPLv3，srt_composer.py 为 MIT；声线模型是微软在线服务，不是开放模型。这里提交的是合成后的 MP4，离线可看。重新生成需要联网。画面由脚本和本仓库 SVG 生成，不是实拍。 视频：<a href="../assets/video/ch03-gpio.mp4">MP4</a> · 字幕：<a href="../assets/video/ch03-gpio.srt">SRT</a>。由 <code>python3 tools/gen_narrated.py --speak</code> 用 ffmpeg 合成。</sub>
</p>

**旁白（与字幕、配音同一份稿）**

1. GPIO 看起来就是高低电平，真正要选的是模式。先分清输入还是输出，推挽还是开漏，要不要上下拉。模式选错，电平会和你想的相反。
2. BluePill 的板载灯在 PC13，接法是低电平才亮。你写 1，灯反而是灭的。别拿共阴外接灯的习惯去套这颗板载灯，否则你会以为端口坏了。
3. 按键另一端接 GND 时，引脚要上拉。没按下是高，按下被拉成低。再外加一个下拉，电平会和上拉打架，读到的就飘着。
4. 这一帧是仓库里的点灯动画，不是实拍。推挽输出能主动拉高也能主动拉低。开漏则要靠上拉，适合和别人共享一根线，比如 I2C。
5. 在 F1 上把外设换到另一组脚，要先打开 AFIO 的时钟，再写重映射。只改模式、不开 AFIO，示波器上会一直安静。这是这章最容易漏的一步。
6. 不是每只脚都能碰 5 伏。数据手册里标了 FT 的才比较容忍。普通脚直接接 5 伏模块，轻则电平不对，重则把片打伤。先翻表，再接线。
7. 引脚锁定用来防止后面的代码把手脚改掉。顺序是写 1、写 0、再写 1，然后读一次才真正锁上。少读那一下，你以为锁了，其实没有。
8. 口诀：F1 重映射先开 AFIO；5 伏只认 FT；锁定是 1、0、1 再读。三件都是手上的动作，不是概念题。
9. 实验让 PC13 以 1 赫兹翻转。眼睛只能看出大概，频率要用你算过的延时或定时器来对。对上了，这章才算过关。
10. 合上书，三问。PC13 写高还是写低才会亮？按键接 GND 该上拉还是下拉？F1 重映射之前必须先开哪个时钟？
<!-- /video:ch03 -->
## 原理与边界

这一章的点灯结论只钉在订货号 STM32F103C8T6、封装 LQFP48 上。[DS5319 Rev 20](#source-ds5319-gpio) 的图 8 和表 5 把 PA0-WKUP 放在第 10 脚，把 PC13-TAMPER-RTC 放在第 2 脚。

PA0 可以做电流源。把它配成推挽、写 1，电流从 3.3 V 经脚内的 PMOS 流出，再经过电阻和发光二极管到地。例程里的算术是 `(3.3 − 2.0) / 0.005 = 260`，取标准值 270 Ω。[例程](#source-project-examples) 只支持这组输入和这个商，不支持把它说成数据手册里的推荐电流。

PC13、PC14、PC15 走电源开关。同一份数据手册的注 5 给出的界限是：灌电流不超过 3 mA，速度不超过 2 MHz，负载不超过 30 pF，而且不能拿这三只脚去当电流源点灯。BluePill 板载灯接在 PC13 上还能亮，是因为灯的阳极在 3.3 V，脚只负责灌电流，写 0 才亮。把 PA0「写 1 点亮」的电路原样搬到 PC13，这一行作废。

上面速度表里的 25 mA 和 50 MHz 对这三只脚作废。换封装或换订货号时，第 2 脚和第 10 脚整行重写。F4 每个脚自己的 AFR 不在 RM0008 里；本书旧句「F1 用 AFIO 的 MAPR」只在 F1 上成立，换到 F4 时那一行作废。

## 关键插图

<p align="center">
  <img src="../assets/diagrams/sample-03-gpio-led.svg" width="760" alt="STM32F103C8T6 上 PA0 经 270 欧点亮外接灯，PC13 不能输出这股电流">
  <br><sub>▲ 自绘。STM32F103C8T6，LQFP48：PA0 是第 10 脚，PC13 是第 2 脚。正常路径是 3.3 V 经推挽和 270 Ω 到 LED；260 Ω 是 (3.3 − 2.0) / 0.005 的商。失败路径是把这条路搬到 PC13：注 5 只允许 3 mA 灌电流，速度不超过 2 MHz，负载不超过 30 pF。锁序列见 GPIOx_LCKR，偏移 0x18。脚位与电流来自 [DS5319 Rev 20](#source-ds5319-gpio) 表 5、图 8、注 5；锁与 SWD 来自 [RM0008 Rev 21](#source-rm0008-gpio) 第 9.2.7 节和第 9.3.5 节表 36。</sub>
</p>

章首那张 `gpio-blink.svg` 仍是动画辅图。这一节的主图不播放也能指出失败发生在 PC13 那段。

## 时序或状态

1 Hz 的高低电平不是 GPIO 速度位算出来的。高 500 ms、低 500 ms 来自 [gpio-blink 例程](#source-project-examples) 的 `HAL_Delay(500)`。速度位写成 50 MHz 不会把 PC13 变成可以点灯的脚。

| 步骤 | LCK[15:0] | LCKK | 读回 | 结果 |
| --- | --- | --- | --- | --- |
| 1 | 保持要锁的脚 | 写 1 | — | 序列开始 |
| 2 | 同上，不能改 | 写 0 | — | 序列继续 |
| 3 | 同上，不能改 | 写 1 | — | 序列写完 |
| 4 | 同上 | — | 再读，确认读回 1 | 锁住，直到复位 |
| 失败 | 中途改了掩码，或少了一次写 | — | 确认读回不是 1 | 锁中止，配置仍可改 |

寄存器是 `GPIOx_LCKR`，偏移 `0x18`。出处是 [RM0008 Rev 21 第 9.2.7 节](#source-rm0008-gpio)。

## 坑与出处卡

| 现象 | 原因 | 处理 | 出处 | 该来源允许支持的主张 |
| --- | --- | --- | --- | --- |
| 外接灯接在 PC13 上，写 1 也不按 PA0 的方式亮 | PC13 不能当电流源 | 外接灯改到 PA0，串 270 Ω | [DS5319 Rev 20 注 5](#source-ds5319-gpio) | LQFP48 第 2 脚是 PC13；PC13–PC15 灌电流不超过 3 mA，速度不超过 2 MHz，负载不超过 30 pF |
| 板载灯写 1 反而不亮 | 板载灯共阳，PC13 灌电流才亮 | 写 0 点亮 | [gpio-blink 例程](#source-project-examples) | 只支持这块 BluePill 的接法，不支持 3 mA 这个手册数字 |
| 写了 ODR，脚上没有电平 | 口时钟还没开，配置寄存器还没进外设 | 先打开对应 GPIO 口的时钟，再写 CRL/CRH | [RM0008 GPIO](#source-rm0008-gpio) | 只支持「先给这个口时钟，再写第 9 章的配置寄存器」 |
| LCKR 写了三次，之后仍能改配置 | 序列出错，或确认读回不是 1 | 掩码保持不变，写 1、写 0、写 1，再读到 1 | [RM0008 第 9.2.7 节](#source-rm0008-gpio) | 锁成立后保持到复位；错一步则锁中止 |
| 烧完就再也连不上 | PA13/PA14 被配成普通 GPIO | 把 SWD 留在 PA13 与 PA14 | [RM0008 表 36](#source-rm0008-gpio) | SWDIO 是 PA13，SWCLK 是 PA14 |

旧表里的按键抖动不放进这张卡：10 ms 到 20 ms 的消抖没有钉在 RM0008 或 DS5319 上。动手实验可以继续做消抖，不把它写成手册数字。
## 📌 学习目标
- [ ] 记住 8 种 GPIO 模式及各自适用场景
- [ ] 理解推挽 vs 开漏的电流路径与上拉电阻作用
- [ ] 会算 LED 限流电阻 R=(Vcc−Vf)/I
- [ ] 会用 HAL 和寄存器两种方式操作 GPIO
- [ ] 知道 SWD 引脚复用、时钟使能等常见坑

## 🧠 核心原理

**结论先行：GPIO 的 8 种模式由「输入/输出」×「推挽/开漏」×「复用/普通」×「上拉/下拉/浮空」组合而成，选错模式是绝大多数问题的根源。**

### 1. 8 种 GPIO 模式详解表

| 模式（HAL 宏） | 方向 | 输出级 | 上/下拉 | 典型场景 |
| --- | --- | --- | --- | --- |
| `GPIO_MODE_INPUT` + Pull=NPU | 输入 | — | 浮空 | 外部已有上下拉，或接数字器件输出 |
| `GPIO_MODE_INPUT` + Pull=UP | 输入 | — | 上拉 | 按键接 GND（低有效） |
| `GPIO_MODE_INPUT` + Pull=DOWN | 输入 | — | 下拉 | 按键接 VCC（高有效） |
| `GPIO_MODE_ANALOG` | 输入 | 关闭 | — | ADC 采样、低功耗 |
| `GPIO_MODE_OUTPUT_PP` | 输出 | 推挽 | — | LED、驱动信号（强高低） |
| `GPIO_MODE_OUTPUT_OD` | 输出 | 开漏 | — | I2C、需要外部上拉或线与 |
| `GPIO_MODE_AF_PP` | 复用 | 推挽 | — | UART/SPI/PWM 输出 |
| `GPIO_MODE_AF_OD` | 复用 | 开漏 | — | I2C 硬件外设、SMBus |

> F1 里还有 `GPIO_MODE_AF_INPUT`；F4/F7 用 `GPIO_MODE_AF_OD/PP` + `Alternate` 字段指定复用功能号。术语以 HAL 宏为准。

### 2. 输出速度与电流能力

| 参数 | 值 | 说明 |
| --- | --- | --- |
| 输出速度（F1） | 2/10/50MHz | 越高边沿越陡。PC13、PC14、PC15 不用这一行，界限写在「原理与边界」。 |
| 输出速度（F4+） | Low/Medium/High/Very High | 对应不同驱动强度 |
| 单脚灌/拉电流 | 25mA（F103） | 其他脚仍用这一行。PC13、PC14、PC15 不用这一行，界限写在「原理与边界」。 |
| 端口总电流 | 150mA（F103） | 所有 IO 之和 |
| 内部上下拉 | 30~50kΩ（F1） | 弱上拉，驱动能力有限 |

### 3. 推挽 vs 开漏

| 对比 | 推挽（Push-Pull） | 开漏（Open-Drain） |
| --- | --- | --- |
| 高电平来源 | PMOS 主动拉高到 VDD | 高阻，靠外部上拉 |
| 低电平来源 | NMOS 主动拉低到 GND | NMOS 主动拉低到 GND |
| 能否线与 | ❌ | ✅ 多脚并接实现线与 |
| 典型用途 | LED、普通数字输出 | I2C、电平转换、共享总线 |
| 电流路径 | 高：VDD→PMOS→引脚；低：引脚→NMOS→GND | 低：引脚→NMOS→GND；高：无（靠外部上拉） |

### 4. LED 限流电阻计算

`R = (Vcc − Vf) / I`

| 参数 | 典型值 | 说明 |
| --- | --- | --- |
| Vcc | 3.3V | 供电电压 |
| Vf（红） | 1.8~2.2V | 正向压降 |
| Vf（绿/蓝/白） | 2.8~3.2V | 蓝/白更高，3.3V 供电可能偏暗 |
| I（目标） | 5~10mA | 普通指示 LED 足够 |

具体订货号上的算例写在「原理与边界」，并标明它来自例程而不是数据手册。这里只保留公式。

### 5. GPIO 寄存器（F1）

| 寄存器 | 作用 |
| --- | --- |
| CRL / CRH | 配置低 8 位 / 高 8 位引脚的模式与速度 |
| IDR | 输入数据寄存器（读引脚电平） |
| ODR | 输出数据寄存器（读写引脚电平） |
| BSRR | 置位/复位寄存器，写 1 有效，原子操作 |
| BRR | 复位寄存器（F1 有，F4 合并进 BSRR） |

## 🛠️ 硬件与接线

| 开发板 | 外设 | 引脚 | 备注 |
| --- | --- | --- | --- |
| BluePill | 板载 LED | PC13 | **共阳接法，低电平点亮** |
| BluePill | 外接 LED | PA0 | 串 270Ω 电阻，高电平点亮 |
| BluePill | 按键 | PA1 | 另一端接 GND，内部上拉 |

接线（外接 LED）：PA0 → 270Ω → LED 阳极，LED 阴极 → GND（**共阴**，高电平点亮）。
板载 LED 是 **共阳** 接法：阳极接 3.3V，PC13 拉低才导通，故**低电平点亮**。

## 💻 代码实现

```c
/* gpio_blink.c —— GPIO 输出点灯 + 按键读取（HAL） */
#include "stm32f1xx_hal.h"

#define LED_PIN    GPIO_PIN_13
#define LED_PORT   GPIOC
#define KEY_PIN    GPIO_PIN_1
#define KEY_PORT   GPIOA

void SystemClock_Config(void);

static void gpio_init(void)
{
    GPIO_InitTypeDef io = {0};

    __HAL_RCC_GPIOC_CLK_ENABLE();
    __HAL_RCC_GPIOA_CLK_ENABLE();

    /* PC13 推挽输出（板载 LED，低电平点亮） */
    io.Pin   = LED_PIN;
    io.Mode  = GPIO_MODE_OUTPUT_PP;
    io.Pull  = GPIO_NOPULL;
    io.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(LED_PORT, &io);

    /* PA1 输入，内部上拉（按键按下接地为低） */
    io.Pin  = KEY_PIN;
    io.Mode = GPIO_MODE_INPUT;
    io.Pull = GPIO_PULLUP;
    HAL_GPIO_Init(KEY_PORT, &io);
}

int main(void)
{
    HAL_Init();
    SystemClock_Config();
    gpio_init();

    while (1)
    {
        /* 按键按下（低电平）时点亮 LED */
        GPIO_PinState key = HAL_GPIO_ReadPin(KEY_PORT, KEY_PIN);
        HAL_GPIO_WritePin(LED_PORT, LED_PIN,
                          (key == GPIO_PIN_RESET) ? GPIO_PIN_RESET : GPIO_PIN_SET);
    }
}
```

三种写法对照（同一动作：点亮 PC13）：

```c
/* 1) HAL 函数 */
HAL_GPIO_WritePin(GPIOC, GPIO_PIN_13, GPIO_PIN_RESET);   /* 低电平点亮 */

/* 2) BSRR 原子操作（推荐，避免读改写） */
GPIOC->BSRR = GPIO_BSRR_BR13;   /* 复位 PC13（BR=Bit Reset） */
GPIOC->BSRR = GPIO_BSRR_BS13;   /* 置位 PC13（BS=Bit Set）   */

/* 3) ODR 读改写（简单但非原子） */
GPIOC->ODR &= ~GPIO_ODR_ODR13;  /* 清零 */
```

位带操作（F1 支持，用一个别名地址直接操作单个 bit）：

```c
/* 位带别名：把外设地址 0x4001100C (GPIOC_ODR) 的 bit13 映射到别名地址 */
#define BITBAND_PERIPH(addr, bit) \
    (*(volatile uint32_t *)(0x42000000UL + ((addr) - 0x40000000UL) * 32 + (bit) * 4))

#define PC13_OUT  BITBAND_PERIPH(0x4001100CUL, 13)   /* GPIOC->ODR bit13 */
PC13_OUT = 0;   /* 直接写 0/1，无需读改写，等效于 ODR */
```

完整工程见 [`examples/gpio-blink/`](../examples/gpio-blink/)。

## 🧪 动手实验

1. **实验一**：PC13 板载 LED 1Hz 闪烁（对照 `gpio-blink.svg` 与 `led-blink.gif`）。
2. **实验二**：外接 LED 到 PA0，计算并串接 270Ω 电阻，实现按键 PA1 控制 LED。
3. **实验三**：分别用 BSRR、ODR、位带三种方式翻转 PA0，用逻辑分析仪对比波形，理解原子操作的意义。

### 6. 按键电路与消抖

| 接法 | 空闲电平 | 按下电平 | 触发沿 |
| --- | --- | --- | --- |
| 上拉 + 按键接地 | 高 | 低 | 下降沿 |
| 下拉 + 按键接 VCC | 低 | 高 | 上升沿 |

| 消抖方式 | 说明 |
| --- | --- |
| 软件延时 | 检测到变化后延时 10~20ms 再确认 |
| 定时器扫描 | 定时器周期采样，多次一致才确认 |
| RC 滤波 | 硬件加 0.1µF 电容 + 电阻 |
| 施密特触发器 | 硬件整形 |

```c
/* 软件消抖：等待稳定 */
static uint8_t key_scan(GPIO_TypeDef *port, uint16_t pin)
{
    if (HAL_GPIO_ReadPin(port, pin) == GPIO_PIN_RESET)   /* 检测到低 */
    {
        HAL_Delay(20);                                    /* 延时消抖 */
        if (HAL_GPIO_ReadPin(port, pin) == GPIO_PIN_RESET) return 1;
    }
    return 0;
}
```

### 7. 常见外设 GPIO 配置速查

| 外设 | 引脚模式 |
| --- | --- |
| LED 输出 | OUTPUT_PP |
| 按键输入 | INPUT + PULLUP/PULLDOWN |
| UART TX | AF_PP |
| UART RX | INPUT + PULLUP |
| I2C SDA/SCL | AF_OD（或 OUTPUT_OD） |
| SPI SCK/MOSI | AF_PP |
| SPI MISO | INPUT |
| ADC 通道 | ANALOG |
| PWM 输出 | AF_PP |

### 8. 位带地址计算公式

- 外设区别名：`别名地址 = 0x42000000 + (外设地址 − 0x40000000) × 32 + bit × 4`
- SRAM 区别名：`别名地址 = 0x22000000 + (SRAM 地址 − 0x20000000) × 32 + bit × 4`

> 位带仅覆盖 SRAM 与 AHB1 外设区；F1 上普遍可用，F4 起部分外设不再支持。

### 9. LED 与数码管驱动简述

| 器件 | 驱动方式 | 注意 |
| --- | --- | --- |
| 单色 LED | GPIO 直接驱动 + 限流电阻 | 电流 < 20mA |
| 高亮/大功率 LED | 三极管/MOS 驱动 | GPIO 只给基极电流 |
| 数码管（共阳/共阴） | 位选 + 段选，可加 74HC595 | 扫描刷新 |
| RGB LED | 三个 PWM 通道 | 混色 |

### 10. GPIO 电气特性补充

| 参数 | 值 |
| --- | --- |
| 输入高电平 VIH | 0.7×VDD ≈ 2.31V |
| 输入低电平 VIL | 0.3×VDD ≈ 0.99V |
| 输出高电平 VOH | VDD−0.4 ≈ 2.9V（轻载） |
| 输出低电平 VOL | 0.4V |
| 内部上拉阻值 | 30~50kΩ |

### 11. 重映射、5 V 容忍和锁定

**结论**：F1 改脚位走 AFIO 重映射，F4 每个引脚自己选 AF 号。能不能接 5 V，只看数据手册那一列有没有 FT，不是“STM32 都耐 5 V”。

| 系列 | 怎么换功能 | 先决条件 |
| --- | --- | --- |
| F1 | `AFIO->MAPR` 整组重映射（如 USART1 从 PA9/10 到 PB6/7） | 先 `__HAL_RCC_AFIO_CLK_ENABLE()` |
| F4 | `GPIOx->AFR` 按引脚填 AF 编号 | 模式先设成复用 |

5 V 容忍（FT）的脚在数据手册引脚表里单独标。普通脚直接接 5 V 会损坏，本仓库不给“大概没事”的电流。

锁定某一脚，避免后面的初始化再改它。序列是写 1、写 0、再写 1，然后读一次：

```c
GPIOA->LCKR = GPIO_LCKR_LCKK | GPIO_LCKR_LCK5;
GPIOA->LCKR = GPIO_LCKR_LCK5;
GPIOA->LCKR = GPIO_LCKR_LCKK | GPIO_LCKR_LCK5;
(void)GPIOA->LCKR;   /* 读回后 LCKK 才真正锁住，直到复位 */
```

口诀：**F1 重映射先开 AFIO；5 V 只认 FT；锁定是 1-0-1 再读。**

自测：

1. F103 把 USART1 重映射到 PB6/PB7，忘了开 AFIO 时钟，现象是什么？
2. 数据手册没标 FT 的 PA0，能不能直接接 5 V 传感器？
3. `LCKR` 写完不读，锁有没有生效？

## 🔗 相关资源

- 官方手册：**RM0008** 第 9 章（GPIO）及第 9.2 节（寄存器描述）；**DS5319** 引脚定义
- 上一篇：[02 芯片选型与存储器时钟](02-芯片选型与存储器时钟.md)｜下一篇：[04 中断与NVIC](04-中断与NVIC.md)
- 📱 手机阅读版：[第 03 章 · GPIO与LED（公众号图文）](https://mp.weixin.qq.com/s/G8szO2UDufAHY9vJYDpYFA)
- 相关图：[`assets/animations/gpio-blink.svg`](../assets/animations/gpio-blink.svg)、[`assets/gif/led-blink.gif`](../assets/gif/led-blink.gif)
- 实物与资料：ST 官网 Nucleo 板原理图（LED 接法参考）
- 免责声明：本仓库插画均为作者自绘矢量图/程序生成动画，非厂商实拍照片。


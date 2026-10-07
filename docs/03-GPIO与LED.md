# 03 GPIO 与 LED

> GPIO 是最基础的外设，用它输出电平、读取按键，是一切外设的入口。

<p align="center">
  <img src="../assets/animations/gpio-blink.svg" width="760" alt="GPIO 推挽输出驱动 LED 动画">
  <br><sub>▲ 动画：GPIO 推挽输出点亮 LED（电平、电流、波形同步，作者自绘矢量图）</sub>
</p>

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
| 输出速度（F1） | 2/10/50MHz | 越高边沿越陡，EMI 越大；够用就好 |
| 输出速度（F4+） | Low/Medium/High/Very High | 对应不同驱动强度 |
| 单脚灌/拉电流 | 25mA（F103） | 超过会损坏 |
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

例：3.3V、红 LED Vf=2.0V、I=5mA → R=(3.3−2.0)/0.005 = **260Ω**，取标准值 270Ω。

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

## ⚠️ 常见坑与排查

| 现象 | 原因 | 解决 |
| --- | --- | --- |
| LED 完全不亮 | CubeMX 忘使能 GPIO 时钟 | 加 `__HAL_RCC_GPIOx_CLK_ENABLE()` |
| LED 一直亮 / 亮灭反了 | 共阳/共阴接法搞反 | 确认板载 LED 低电平点亮；外接 LED 按极性接 |
| 按键乱跳、一次触发多次 | 没做消抖 | 加 10~20ms 延时消抖或 RC 滤波 |
| 烧录后再也连不上 | SWD 引脚 PA13/PA14 被配成普通 GPIO | CubeMX 里 SYS 选 Serial Wire；或「连接下复位」恢复 |
| 输出高电平只有 1.几伏 | 开漏模式没上拉 | 用推挽，或外接上拉电阻 |
| LED 忽明忽暗 / 发热 | 限流电阻太小或没接 | 按 R=(Vcc−Vf)/I 计算，取 5~10mA |
| 引脚电平读了不变 | 输入模式没设上下拉，引脚悬空 | 设 PULLUP/PULLDOWN，或外接上下拉 |

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
- 相关图：[`assets/animations/gpio-blink.svg`](../assets/animations/gpio-blink.svg)、[`assets/gif/led-blink.gif`](../assets/gif/led-blink.gif)
- 实物与资料：ST 官网 Nucleo 板原理图（LED 接法参考）
- 免责声明：本仓库插画均为作者自绘矢量图/程序生成动画，非厂商实拍照片。


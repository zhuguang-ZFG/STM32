# gpio-blink —— GPIO 推挽输出闪烁 LED

> 难度：★☆☆☆　｜　涉及外设：GPIO　｜　对应章节：[03 GPIO 与 LED](../../docs/03-GPIO与LED.md)

<p align="center">
  <img src="../../assets/animations/gpio-blink.svg" width="760" alt="GPIO 推挽输出驱动 LED 动画">
  <br><sub>▲ 动画：GPIO 推挽输出点亮 LED（电平、电流、波形同步，作者自绘矢量图）</sub>
</p>

## 一、功能说明

本示例用 STM32F103C8T6（BluePill）实现最经典的「点灯」，并横向对比 **3 组写法**：

| 对比项 | 写法 A | 写法 B | 目的 |
| --- | --- | --- | --- |
| 翻转电平 | `HAL_GPIO_TogglePin()` | `GPIOx->BSRR` 寄存器原子操作 | 理解 HAL 封装与底层寄存器的关系 |
| 延时方式 | `HAL_Delay()`（SysTick 中断） | `delay_systick_count()`（读 `HAL_GetTick`） | 理解 HAL 时基来自 SysTick |
| 端口 | PC13 板载 LED | PA0 外接 LED | 熟悉推挽输出的接线与极性 |

- 板载 LED（PC13）以 **1Hz**（亮 500ms、灭 500ms）闪烁；
- 外接 LED（PA0）每 **5 秒**翻转一次，用于肉眼确认程序未卡死。

## 二、硬件接线表

| 开发板 | 外设 | 引脚 | 接法 | 备注 |
| --- | --- | --- | --- | --- |
| BluePill | 板载 LED | PC13 | 板上已接（共阳，阳极接 3.3V） | **低电平点亮** |
| BluePill | 外接 LED | PA0 | PA0 → 270Ω → LED 阳极，阴极 → GND | 共阴，**高电平点亮** |

> 限流电阻：`R=(Vcc−Vf)/I`。3.3V、红 LED Vf≈2.0V、I≈5mA → R≈260Ω，取标准值 270Ω。

## 三、CubeMX 关键配置

| 配置项 | 取值 | 说明 |
| --- | --- | --- |
| RCC → HSE | Crystal/Ceramic Resonator | 板载 8MHz 晶振 |
| Clock Configuration | PLL ×9 → SYSCLK 72MHz | APB1=36MHz，APB2=72MHz |
| GPIO PC13 | Output Push Pull / No pull / Low speed | 板载 LED |
| GPIO PA0 | Output Push Pull / No pull / Low speed | 外接 LED |
| SYS → Debug | Serial Wire | **保留 SWD，避免烧录后连不上** |

时钟树要点：`8MHz(HSE) → /1 → PLL ×9 → 72MHz(SYSCLK)`；72MHz 需 **2 个 Flash 等待周期**（`FLASH_LATENCY_2`）。

## 四、关键代码解读

**1) 推挽输出初始化（使能时钟 + 配模式）**

```c
__HAL_RCC_GPIOC_CLK_ENABLE();          /* 关键：不使能时钟，寄存器写入无效 */
GPIO_InitTypeDef io = {0};
io.Pin   = GPIO_PIN_13;
io.Mode  = GPIO_MODE_OUTPUT_PP;        /* 推挽输出：强高低电平 */
io.Pull  = GPIO_NOPULL;
io.Speed = GPIO_SPEED_FREQ_LOW;        /* 低频闪烁，低速即可 */
HAL_GPIO_Init(GPIOC, &io);
```

**2) HAL 写法 vs BSRR 寄存器写法**

```c
/* HAL：内部其实就是读 ODR 判断再写 BSRR，可读性好 */
HAL_GPIO_TogglePin(GPIOC, GPIO_PIN_13);

/* BSRR 原子写法：低 16 位=置位(BS)，高 16 位=复位(BR) */
if ((GPIOC->ODR & GPIO_PIN_13) != 0U)
    GPIOC->BSRR = (uint32_t)GPIO_PIN_13 << 16U;  /* 复位 PC13 */
else
    GPIOC->BSRR = (uint32_t)GPIO_PIN_13;         /* 置位 PC13 */
```

`BSRR` 单次写入即完成操作，天然原子，不会被中断打断产生「读改写」竞态。

**3) 两种延时对比**

```c
HAL_Delay(500);                     /* 基于 SysTick 中断，会进中断、可被打断 */

/* 纯计数忙等：不关中断，靠 HAL_GetTick 递增判断 */
static void delay_systick_count(uint32_t ms) {
    uint32_t start = HAL_GetTick();
    while ((HAL_GetTick() - start) < ms) { __NOP(); }
}
```

两者时基都来自 SysTick（1ms 中断）。**不要在中断里用 `HAL_Delay`**（若 SysTick 被更高优先级屏蔽会死等），需要时用忙等或 DWT。

## 五、编译烧录步骤

1. **Keil MDK**：新建 F103C8 工程，把本 `main.c` 替换 `Core/Src/main.c`，勾选 `Use MicroLIB`（可选），编译 → 下载。
2. **STM32CubeIDE**：新建 F103C8 工程，覆盖 `Core/Src/main.c`，点 🔨 编译，点 🐞/▶ 下载。
3. **PlatformIO**：`platform = ststm32`、`board = bluepill_f103c8`、`framework = stm32cube`，把 `main.c` 放进 `src/`，`pio run -t upload`。
4. 连接 ST-Link：`SWDIO=PA13`、`SWCLK=PA14`、`GND`、`3.3V`。

## 六、预期现象

- 上电后板载 LED（PC13）以 **1Hz 稳定闪烁**；
- 接在 PA0 的外接 LED 每 **5 秒**翻转一次；
- 用逻辑分析仪看 PC13：方波周期 1s，占空比约 50%。

## 七、常见问题

| 现象 | 原因 | 解决 |
| --- | --- | --- |
| LED 完全不亮 | 没使能 GPIO 时钟 | 加 `__HAL_RCC_GPIOx_CLK_ENABLE()` |
| 亮灭反了 | 共阳/共阴搞混 | 板载 LED 低电平点亮；外接 LED 按极性接 |
| 烧录后再连不上 | PA13/PA14 被当普通 GPIO | CubeMX 里 SYS 选 Serial Wire |
| 闪烁频率不对 | 时钟树没配到 72MHz | 检查 PLL 与 Flash 等待周期 |
| 外接 LED 很暗 | 限流电阻太大或极性接反 | 按 `R=(Vcc−Vf)/I` 重算，确认极性 |

## 八、相关资源

- 参考手册 **RM0008** 第 9 章（GPIO，含 BSRR/BRR 寄存器描述）
- 数据手册 **DS5319**（引脚定义、电气特性）
- 相关图：[`assets/animations/gpio-blink.svg`](../../assets/animations/gpio-blink.svg)、[`assets/gif/led-blink.gif`](../../assets/gif/led-blink.gif)
- 免责声明：本示例配图为作者自绘矢量图/程序生成动画，非厂商实拍照片。

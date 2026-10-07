# 示例代码总索引

> 每个示例都是**完整可编译**的 HAL 库代码（`main.c` + 说明 `README.md`）。
> 说明里给出：功能、硬件接线表、CubeMX 配置要点、关键代码解读、编译烧录步骤、预期现象、常见问题。
>
> 目标平台以 **STM32F103C8T6（BluePill）** 为主，涉及 F4 的差异在正文中单独标注。

## 一、示例索引表

| 示例 | 难度 | 涉及外设 | 对应文档章节 | 硬件需求 |
| --- | --- | --- | --- | --- |
| [gpio-blink](gpio-blink/) | ★ | GPIO 推挽输出 | [03 GPIO与LED](../docs/03-GPIO与LED.md) | BluePill（板载 LED + 可选外接 LED/270Ω） |
| [exti-key](exti-key/) | ★★ | GPIO + EXTI + NVIC | [04 中断与NVIC](../docs/04-中断与NVIC.md) | BluePill + 按键（或杜邦线碰 GND） |
| [timer-pwm](timer-pwm/) | ★★ | TIM（PWM 输出） | [05 定时器与PWM](../docs/05-定时器与PWM.md) | BluePill + LED + 270Ω（可选示波器） |
| [uart-dma-idle](uart-dma-idle/) | ★★★ | USART + DMA + 环形缓冲 | [06 串口UART](../docs/06-串口UART.md) / [10 DMA](../docs/10-DMA.md) | BluePill + USB-TTL 模块 |
| [i2c-oled](i2c-oled/) | ★★★ | 硬件 I2C + SSD1306 | [07 I2C总线](../docs/07-I2C总线.md) | BluePill + 0.96" I2C OLED |
| [spi-flash](spi-flash/) | ★★★ | 硬件 SPI + W25Q64 | [08 SPI总线](../docs/08-SPI总线.md) | BluePill + W25Q64 模块 |
| [adc-dma](adc-dma/) | ★★★ | ADC 多通道 + DMA | [09 ADC与DAC](../docs/09-ADC与DAC.md) / [10 DMA](../docs/10-DMA.md) | BluePill + 电位器/传感器 |
| [rtc-alarm](rtc-alarm/) | ★★ | RTC + PWR(STOP) + 备份域 | [11 RTC与看门狗](../docs/11-RTC与看门狗.md) | BluePill + 32.768kHz 晶振 + 纽扣电池 |
| [freertos-task](freertos-task/) | ★★★★ | GPIO/EXTI/USART + FreeRTOS | [15 FreeRTOS入门](../docs/15-FreeRTOS入门.md) | BluePill + 按键 + USB-TTL |
| [iap-bootloader](iap-bootloader/) | ★★★★ | USART + Flash | [12 Flash与IAP升级](../docs/12-Flash与IAP升级.md) | BluePill + USB-TTL |
| [can-bxcan](can-bxcan/) | ★★★★ | bxCAN 环回 / 双节点 / 过滤器 / Bus-Off | [13 CAN总线](../docs/13-CAN总线.md) | 环回只需 BluePill；双节点再加两只 3.3 V 收发器 |
| [usb-cdc](usb-cdc/) | ★★★★ | USB Device CDC | [14 USB](../docs/14-USB.md) | BluePill 板载 USB（D+ 1.5 kΩ） |
| [usb-hid](usb-hid/) | ★★★★ | USB Device HID 键盘 | [14 USB](../docs/14-USB.md) | BluePill 板载 USB + PA0 按键 |

> 难度说明：★ 入门（单外设、几十行）→ ★★★★ 进阶（多外设联动、需理解时序/内存布局）。

## 二、示例与章节对照

| 编号 | 章节文件 | 相关示例 |
| --- | --- | --- |
| 03 | [03-GPIO与LED.md](../docs/03-GPIO与LED.md) | gpio-blink |
| 04 | [04-中断与NVIC.md](../docs/04-中断与NVIC.md) | exti-key |
| 05 | [05-定时器与PWM.md](../docs/05-定时器与PWM.md) | timer-pwm |
| 06 | [06-串口UART.md](../docs/06-串口UART.md) | uart-dma-idle |
| 07 | [07-I2C总线.md](../docs/07-I2C总线.md) | i2c-oled |
| 08 | [08-SPI总线.md](../docs/08-SPI总线.md) | spi-flash |
| 09 | [09-ADC与DAC.md](../docs/09-ADC与DAC.md) | adc-dma |
| 10 | [10-DMA.md](../docs/10-DMA.md) | uart-dma-idle / adc-dma |
| 11 | [11-RTC与看门狗.md](../docs/11-RTC与看门狗.md) | rtc-alarm |
| 12 | [12-Flash与IAP升级.md](../docs/12-Flash与IAP升级.md) | iap-bootloader |
| 13 | [13-CAN总线.md](../docs/13-CAN总线.md) | can-bxcan |
| 14 | [14-USB.md](../docs/14-USB.md) | usb-cdc / usb-hid |
| 15 | [15-FreeRTOS入门.md](../docs/15-FreeRTOS入门.md) | freertos-task |

## 三、目录结构

```text
examples/
├── README.md              ← 本文件（总索引）
├── gpio-blink/            ← main.c + README.md
├── exti-key/
├── timer-pwm/
├── uart-dma-idle/
├── i2c-oled/
├── spi-flash/
├── adc-dma/
├── rtc-alarm/
├── freertos-task/
├── iap-bootloader/
├── can-bxcan/             ← 环回、双节点、过滤器、Bus-Off
├── usb-cdc/               ← HAL PCD 虚拟串口（不含 ST 中间件）
└── usb-hid/               ← HAL PCD 键盘
```

## 四、如何把示例跑起来

1. 用 STM32CubeMX 新建对应型号（F103C8T6）的工程，按下例 README 的「CubeMX 关键配置」勾选外设。
2. 用示例的 `main.c` 覆盖生成的 `Core/Src/main.c`；
   若生成代码里已有同名中断服务函数（如 `EXTI0_IRQHandler`），**删掉生成的**以免重复定义。
3. 编译下载（Keil / CubeIDE / PlatformIO 均可）。
4. 对照 README 的「预期现象」验证；不通过时查「常见问题」表。

## 仿真（可选，见第 22 章）

核心示例目录里有 `diagram.json` 和 `wokwi.toml`，Renode 脚本在
[`sim/renode/`](../sim/renode/)。怎么跑、哪些外设当前模型跑不完，写在
[22 仿真实验](../docs/22-仿真实验Wokwi与Renode.md)。

## 五、通用注意事项

| 项 | 说明 |
| --- | --- |
| 时钟 | 示例默认 HSE 8MHz → PLL ×9 → 72MHz；用 HSI 或其它晶振需改 `SystemClock_Config` |
| SWD | 所有示例都保留 SWD（PA13/PA14），避免烧录后连不上 |
| 供电 | 外设一律 3.3V，勿把 5V 直接接 IO |
| 共地 | 接 USB-TTL/模块时**必须共地**，否则串口乱码 |
| 中断 | 中断里只置标志，耗时操作放主循环；共享变量加 `volatile` |
| 命名 | 术语统一：GPIO / 定时器(TIM) / 中断(IRQ) / DMA 通道 / HAL 库 |

> 所有示例中的插画均引用 [`assets/README.md`](../assets/README.md) 清单里的自绘矢量图/程序生成动画，
> **非厂商实拍照片**。需要看实拍请参考各章「实物与资料」小节的官方链接。

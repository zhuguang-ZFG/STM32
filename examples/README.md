# 示例代码总索引

> 完整构建入口：`gpio-blink`（HAL + CMake）、`uart-dma-idle`（HAL + CMake + 宿主回归）、`dma-memcopy`（HAL + CMake + 宿主回归 + ELF/BIN 检查）、`spl-f1-blink`（SPL V3.5.0 + CMake）、`motor-dc-speed`（HAL + CMake）。其余例程为待集成源码，按各 README 配置启动、链接、时基与外设；不能只复制 main.c 就视为工程完整。
> 每个说明给出功能、硬件接线、配置要点、关键代码、编译烧录、预期现象和常见问题。
>
> 目标平台以 **STM32F103C8T6（BluePill）** 为主，涉及 F4 的差异在正文中单独标注。

## 一、示例索引表

| 示例 | 难度 | 涉及外设 | 对应文档章节 | 硬件需求 |
| --- | --- | --- | --- | --- |
| [spl-f1-blink](spl-f1-blink/) | ★★ | SPL V3.5.0 GPIO + SysTick + CMake/OpenOCD | [ch05 工具链四步](../docs/v0-foundations/05-toolchain-four-steps.md) / [ch07 构建系统与历史工程](../docs/v0-foundations/07-build-systems-legacy.md) | BluePill + ST-Link |
| [gpio-blink](gpio-blink/) | ★ | GPIO 推挽输出 | [ch09 GPIO](../docs/v1-drivers/09-gpio.md) | BluePill（板载 LED + 可选外接 LED/270Ω） |
| [exti-key](exti-key/) | ★★ | GPIO + EXTI + NVIC | [ch10 中断、NVIC 与 EXTI](../docs/v1-drivers/10-interrupts-nvic-exti.md) | BluePill + 按键（或杜邦线碰 GND） |
| [timer-pwm](timer-pwm/) | ★★ | TIM（PWM 输出） | [ch12 定时器与 PWM](../docs/v1-drivers/12-timers-pwm.md) | BluePill + LED + 270Ω（可选示波器） |
| [uart-dma-idle](uart-dma-idle/) | ★★★ | USART + DMA + 环形缓冲（完整 CMake 工程，宿主回归通过，未上板） | [ch13 UART 帧协议](../docs/v1-drivers/13-uart-framed-protocol.md) / [ch14 DMA](../docs/v1-drivers/14-dma.md) | BluePill + USB-TTL 模块 |
| [dma-memcopy](dma-memcopy/) | ★★★☆ | DMA1 Channel1 内存到内存 + 4 KiB SRAM 缓冲（完整 CMake 工程，宿主回归/ELF/BIN 检查通过，未上板） | [ch14 DMA](../docs/v1-drivers/14-dma.md) | BluePill；PC13 LED，无外部接线 |
| [i2c-oled](i2c-oled/) | ★★★ | 硬件 I2C + SSD1306 | [ch16 I2C 与 SPI](../docs/v1-drivers/16-i2c-spi.md) | BluePill + 0.96" I2C OLED |
| [spi-flash](spi-flash/) | ★★★ | 硬件 SPI + W25Q64 | [ch16 I2C 与 SPI](../docs/v1-drivers/16-i2c-spi.md) | BluePill + W25Q64 模块 |
| [adc-dma](adc-dma/) | ★★★ | ADC 多通道 + DMA | [ch15 ADC 与 DAC 采样](../docs/v1-drivers/15-adc-dac-sampling.md) / [ch14 DMA](../docs/v1-drivers/14-dma.md) | BluePill + 电位器/传感器 |
| [rtc-alarm](rtc-alarm/) | ★★ | RTC + PWR(STOP) + 备份域 | [ch11 时基与 RTC](../docs/v1-drivers/11-systick-timebase-rtc.md) | BluePill + 32.768kHz 晶振 + 纽扣电池 |
| [freertos-task](freertos-task/) | ★★★★ | GPIO/EXTI/USART + FreeRTOS | [ch22 任务、TCB 与调度](../docs/v3-rtos/22-tasks-tcb-scheduler.md) | BluePill + 按键 + USB-TTL |
| [iap-bootloader](iap-bootloader/) | ★★★★ | USART + Flash | [ch17 Flash、IAP 与 OTA](../docs/v1-drivers/17-flash-iap-ota.md) | BluePill + USB-TTL |
| [can-bxcan](can-bxcan/) | ★★★★ | bxCAN 环回 / 双节点 / 过滤器 / Bus-Off | [ch35 CAN 与 USB 现场总线](../docs/v4-platforms/35-can-usb-fieldbus.md) | 环回只需 BluePill；双节点再加两只 3.3 V 收发器 |
| [usb-cdc](usb-cdc/) | ★★★★ | USB Device CDC | [ch35 CAN 与 USB 现场总线](../docs/v4-platforms/35-can-usb-fieldbus.md) | BluePill 板载 USB（D+ 1.5 kΩ） |
| [usb-hid](usb-hid/) | ★★★★ | USB Device HID 键盘 | [ch35 CAN 与 USB 现场总线](../docs/v4-platforms/35-can-usb-fieldbus.md) | BluePill 板载 USB + PA0 按键 |
| [motor-dc-speed](motor-dc-speed/) | ★★★★ | TIM PWM + 正交编码器 + PI 速度环（CMake 工程，主机测试全绿，未上板） | [ch36 电机驱动与供电](../docs/v5-motion/36-motor-driver-power.md) / [ch39 速度闭环与 PI](../docs/v5-motion/39-speed-closed-loop-pi.md) | BluePill + TB6612 + 带编码器直流电机 |

> 难度说明：★ 入门（单外设、几十行）→ ★★★★ 进阶（多外设联动、需理解时序/内存布局）。

## 二、示例与章节对照

| 章 | 章节文件 | 相关示例 |
| --- | --- | --- |
| 05 | [05 工具链四步](../docs/v0-foundations/05-toolchain-four-steps.md) | spl-f1-blink |
| 07 | [07 构建系统与历史工程](../docs/v0-foundations/07-build-systems-legacy.md) | spl-f1-blink |
| 09 | [09 GPIO](../docs/v1-drivers/09-gpio.md) | gpio-blink |
| 10 | [10 中断、NVIC 与 EXTI](../docs/v1-drivers/10-interrupts-nvic-exti.md) | exti-key |
| 11 | [11 时基与 RTC](../docs/v1-drivers/11-systick-timebase-rtc.md) | rtc-alarm |
| 12 | [12 定时器与 PWM](../docs/v1-drivers/12-timers-pwm.md) | timer-pwm |
| 13 | [13 UART 帧协议](../docs/v1-drivers/13-uart-framed-protocol.md) | uart-dma-idle |
| 14 | [14 DMA](../docs/v1-drivers/14-dma.md) | uart-dma-idle / dma-memcopy / adc-dma |
| 15 | [15 ADC 与 DAC 采样](../docs/v1-drivers/15-adc-dac-sampling.md) | adc-dma |
| 16 | [16 I2C 与 SPI](../docs/v1-drivers/16-i2c-spi.md) | i2c-oled / spi-flash |
| 17 | [17 Flash、IAP 与 OTA](../docs/v1-drivers/17-flash-iap-ota.md) | iap-bootloader |
| 22 | [22 任务、TCB 与调度](../docs/v3-rtos/22-tasks-tcb-scheduler.md) | freertos-task |
| 35 | [35 CAN 与 USB 现场总线](../docs/v4-platforms/35-can-usb-fieldbus.md) | can-bxcan / usb-cdc / usb-hid |
| 36 | [36 电机驱动与供电](../docs/v5-motion/36-motor-driver-power.md) | motor-dc-speed |
| 39 | [39 速度闭环与 PI](../docs/v5-motion/39-speed-closed-loop-pi.md) | motor-dc-speed |

## 三、目录结构

```text
examples/
├── README.md              ← 本文件（总索引）
├── spl-f1-blink/          ← SPL V3.5.0 + CMake + CLion/VS Code/OpenOCD
├── gpio-blink/            ← 固定 HAL/CMSIS + CMake + 启动/链接/时基 + 回归测试
├── uart-dma-idle/         ← 固定 HAL/CMSIS + CMake + USART1/DMA1_CH5 + 宿主回归
├── dma-memcopy/         ← 固定 HAL/CMSIS + CMake + DMA1_CH1 + 4 KiB 缓冲 + 宿主回归
├── exti-key/
├── timer-pwm/
├── i2c-oled/
├── spi-flash/
├── adc-dma/
├── rtc-alarm/
├── freertos-task/
├── iap-bootloader/
├── can-bxcan/             ← 环回、双节点、过滤器、Bus-Off
├── usb-cdc/               ← HAL PCD 虚拟串口（不含 ST 中间件）
├── usb-hid/               ← HAL PCD 键盘
└── motor-dc-speed/        ← CMake 工程：TB6612 + 正交编码器 + PI 速度环（未上板）
```

## 四、如何把示例跑起来

第一次点灯先用 [gpio-blink](gpio-blink/README.md) 的固定 HAL 工程，从获取依赖到生成 ELF/BIN，再核对接线下载。`uart-dma-idle` 使用同一 CubeF1 依赖锁，提供 USART1 + DMA1 Channel5 的完整固件与宿主回归；`dma-memcopy` 提供 DMA1 Channel1 的 4 KiB 内存搬运、ELF/BIN 向量/内存检查与宿主回归；`spl-f1-blink` 按其 README 设置冻结 SPL 源码的 `SPL_ROOT`；`motor-dc-speed` 按其 README 配置固定 CubeF1 和预设。这五个目录直接走各自的 CMake 入口，构建通过均不等于硬件已实测。

其余待集成例程：

1. 用 STM32CubeMX 新建对应型号（F103C8T6）的工程，按下例 README 的「CubeMX 关键配置」勾选外设。
2. 用示例的 `main.c` 覆盖生成的 `Core/Src/main.c`；
   若生成代码里已有同名中断服务函数（如 `EXTI0_IRQHandler`），**删掉生成的**以免重复定义。
3. 编译下载（Keil / CubeIDE / PlatformIO 均可）。
4. 对照 README 的「预期现象」验证；不通过时查「常见问题」表。

## 仿真（可选，见第 40 章）

核心示例目录里有 `diagram.json` 和 `wokwi.toml`，Renode 脚本在
[`sim/renode/`](../sim/renode/)。入口说明见 [sim/README.md](../sim/README.md)。
怎么跑、哪些外设当前模型跑不完，写在
[ch40 实物实验方法与仪器证据](../docs/v6-labs-projects/40-lab-method-instruments.md)。

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

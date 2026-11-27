# 示例代码总索引

> 本目录有 16 个示例。先按下方「如何把示例跑起来」选择完整固件工程、宿主测试或待集成源码，再打开对应 README 执行构建步骤。编译、仿真和板上测量分别记录。
>
> 目标平台以 **STM32F103C8T6（BluePill）** 为主，涉及 F4 的差异在正文中单独标注。

## 一、示例索引表

| 示例 | 难度 | 涉及外设 | 对应文档章节 | 硬件需求 |
| --- | --- | --- | --- | --- |
| [spl-f1-blink](spl-f1-blink/) | ★★ | SPL V3.5.0 GPIO + SysTick + CMake/OpenOCD | [ch05 工具链四步](../docs/v0-foundations/05-toolchain-four-steps.md) / [ch07 构建系统与历史工程](../docs/v0-foundations/07-build-systems-legacy.md) | BluePill + ST-Link |
| [gpio-blink](gpio-blink/) | ★ | GPIO 推挽输出 | [ch09 GPIO](../docs/v1-drivers/09-gpio.md) | BluePill（板载 LED + 可选外接 LED/270Ω） |
| [exti-key](exti-key/) | ★★ | GPIO + EXTI + NVIC | [ch10 中断、NVIC 与 EXTI](../docs/v1-drivers/10-interrupts-nvic-exti.md) | BluePill + 按键（或杜邦线碰 GND） |
| [timer-pwm](timer-pwm/) | ★★ | TIM（PWM 输出） | [ch12 定时器与 PWM](../docs/v1-drivers/12-timers-pwm.md) | BluePill + LED + 270Ω（可选示波器） |
| [uart-dma-idle](uart-dma-idle/) | ★★★ | USART + DMA + 环形缓冲 | [ch13 UART 帧协议](../docs/v1-drivers/13-uart-framed-protocol.md) / [ch14 DMA](../docs/v1-drivers/14-dma.md) | BluePill + USB-TTL 模块 |
| [dma-memcopy](dma-memcopy/) | ★★★ | DMA1 Channel1，4 KiB SRAM 搬运与逐字节比较 | [ch14 DMA](../docs/v1-drivers/14-dma.md) | BluePill + ST-Link（板载 LED 显示结果） |
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
| 14 | [14 DMA](../docs/v1-drivers/14-dma.md) | dma-memcopy / uart-dma-idle / adc-dma |
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
├── exti-key/
├── timer-pwm/
├── uart-dma-idle/         ← 固定 HAL + CMake + DMA/命令解析 + 10 项宿主回归
├── dma-memcopy/           ← 固定 HAL + CMake + 4 KiB SRAM 搬运与错误路径测试
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

第一次点灯先用 [gpio-blink](gpio-blink/README.md)，再用 [uart-dma-idle](uart-dma-idle/README.md) 完成 `AT → OK`。按目录选择构建入口：

| 入口类型 | 示例目录 | 跑法 |
| --- | --- | --- |
| 完整 HAL 固件工程 | `gpio-blink`、`exti-key`、`timer-pwm`、`uart-dma-idle`、`dma-memcopy` | 按各 README 获取固定 CubeF1 v1.8.6，使用 `bluepill` 预设构建并检查 ELF/BIN；同一依赖检出可复用 |
| 完整电机固件工程 | `motor-dc-speed` | 固定 CubeF1；按 README 选择 `dc-openloop`、`dc-encoder` 或 `dc-speed` 预设 |
| 完整 SPL 固件工程 | `spl-f1-blink` | 按 README 设置冻结 SPL V3.5.0 的 `SPL_ROOT`，不与 HAL 混用 |
| 仅宿主测试入口 | `freertos-task` | `host-tests` 预设运行受控替身测试；板上 `main.c` 仍需集成，不生成可下载固件 |
| 待集成源码 | `i2c-oled`、`spi-flash`、`adc-dma`、`rtc-alarm`、`iap-bootloader`、`can-bxcan`、`usb-cdc`、`usb-hid` | 按各 README 补齐启动、链接、时基、HAL 与外设配置 |

完整固件工程按各自 README 下载、观察并保存记录；构建通过不等于硬件已实测。

待集成源码的操作步骤：

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
| 供电 | 按板卡与模块资料分别核对供电和 IO 电平；电机电源与逻辑电源分开核对，勿把 5V 直接接 IO |
| 共地 | 接 USB-TTL/模块时**必须共地**，否则串口乱码 |
| 中断 | ISR 只做有界处理，阻塞操作放主循环或任务；`volatile` 不保证原子性和同步，按共享数据的访问方式选择临界区、原子操作或 RTOS 对象 |
| 命名 | 术语统一：GPIO / 定时器(TIM) / 中断(IRQ) / DMA 通道 / HAL 库 |

> 所有示例中的插画均引用 [`assets/README.md`](../assets/README.md) 清单里的自绘矢量图/程序生成动画，
> **非厂商实拍照片**。需要看实拍请参考各章「实物与资料」小节的官方链接。

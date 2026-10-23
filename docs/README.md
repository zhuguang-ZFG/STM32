# 章节目录

> English: [Contents](en/contents.md)

> 建议阅读顺序：**00 → 01 → 02**（打基础）→ 按兴趣挑外设章节 → **18**（排错手册随时查）→ **19**（做项目）。
> 每篇末尾都有「动手实验」与「常见坑排查」，做完实验再往下走。
> 每章开头有一段中文配音讲解（`assets/video/`，MP4 + SRT），由 `tools/gen_narrated.py` 用 ffmpeg 合成。

## 基础篇

| # | 章节 | 一句话 | 动画 |
| --- | --- | --- | --- |
| 00 | [如何学习 STM32](00-如何学习STM32.md) | 路线图、硬件清单、别踩的学习顺序坑 | [toolchain-flow](../assets/animations/toolchain-flow.svg) |
| 01 | [开发环境搭建](01-开发环境搭建.md) | Keil / CubeIDE / PlatformIO 怎么选，ST-Link 怎么连 | [boot-sequence](../assets/animations/boot-sequence.svg) |
| 02 | [芯片选型与存储器时钟](02-芯片选型与存储器时钟.md) | 型号命名、存储器映射、时钟树 | [clock-tree](../assets/animations/clock-tree.svg) |
| 03 | [GPIO 与 LED](03-GPIO与LED.md) | 8 种模式、推挽/开漏、限流电阻 | [gpio-blink](../assets/animations/gpio-blink.svg) |
| 04 | [中断与 NVIC](04-中断与NVIC.md) | 优先级分组、EXTI、中断安全 | [nvic-interrupt-flow](../assets/animations/nvic-interrupt-flow.svg) |
| 05 | [定时器与 PWM](05-定时器与PWM.md) | 时基公式、占空比、输入捕获 | [timer-pwm](../assets/animations/timer-pwm.svg) |
| 06 | [串口 UART](06-串口UART.md) | 帧格式、波特率误差、DMA+IDLE | [uart-frame](../assets/animations/uart-frame.svg) |
| 07 | [I2C 总线](07-I2C总线.md) | 开漏上拉、ACK、总线死锁恢复 | [i2c-transaction](../assets/animations/i2c-transaction.svg) |
| 08 | [SPI 总线](08-SPI总线.md) | 全双工移位、CPOL/CPHA、片选 | [spi-transfer](../assets/animations/spi-transfer.svg) |

## 进阶篇

| # | 章节 | 一句话 | 动画 |
| --- | --- | --- | --- |
| 09 | [ADC 与 DAC](09-ADC与DAC.md) | 逐次逼近、采样时间、内部温度传感器 | [adc-sar](../assets/animations/adc-sar.svg) |
| 10 | [DMA](10-DMA.md) | 通道/流映射、循环模式、Cache 一致性 | [dma-circular](../assets/animations/dma-circular.svg) |
| 11 | [RTC 与看门狗](11-RTC与看门狗.md) | LSE 备份域、闹钟、IWDG/WWDG | [iwdg-window](../assets/animations/iwdg-window.svg) |
| 12 | [Flash 与 IAP 升级](12-Flash与IAP升级.md) | 扇区擦除、解锁序列、双区跳转 | [flash-iap](../assets/animations/flash-iap.svg) |
| 13 | [CAN 总线](13-CAN总线.md) | 非破坏性仲裁、位填充、过滤器 | [can-arbitration](../assets/animations/can-arbitration.svg) |
| 14 | [USB](14-USB.md) | 枚举、描述符、CDC / HID | [usb-enumeration](../assets/animations/usb-enumeration.svg) |
| 15 | [FreeRTOS 入门](15-FreeRTOS入门.md) | 任务状态、优先级、队列/信号量 | [freertos-scheduler](../assets/animations/freertos-scheduler.svg) |
| 16 | [低功耗设计](16-低功耗设计.md) | Sleep/Stop/Standby、WFI、唤醒源 | [lowpower-wakeup](../assets/animations/lowpower-wakeup.svg) |
| 17 | [调试与性能优化](17-调试与性能优化.md) | SWD/SWO、HardFault 定位、DWT 计时 | [debug-swo](../assets/animations/debug-swo.svg) |

## 实战、仿真与系列引脚

| # | 章节 | 一句话 |
| --- | --- | --- |
| 18 | [常见问题 FAQ](18-常见问题FAQ.md) | 30+ 条「现象 / 原因 / 解决」，遇到问题先来这里搜 |
| 19 | [项目实战合集](19-项目实战合集.md) | 10 个递进项目：蓝牙小车、示波器、数据采集卡… |
| 20 | [学习资源与工具链](20-学习资源与工具链.md) | 官方手册命名规则、社区、开源固件库 |
| 21 | [原理图与实物图鉴](21-原理图与实物图鉴.md) | 5 块板卡结构图 + 如何看懂最小系统原理图 |
| 22 | [仿真实验 Wokwi 与 Renode](22-仿真实验Wokwi与Renode.md) | 浏览器接线、命令行加载 ELF、DMA 模型的边界 |
| 23 | [STM32G0 引脚](23-STM32G0引脚.md) | G071RB LQFP64、BOOT0 与 SWCLK 共用、没有 bxCAN |
| 24 | [STM32L4 引脚](24-STM32L4引脚.md) | L476RG 引脚、Nucleo-64 实拍、Stop 2 IRQ 留证据与 JP6 功耗测量 |
| 25 | [STM32H7 引脚](25-STM32H7引脚.md) | H743ZI LQFP144、FDCAN、VCAP 与三个电源域 |
| 26 | [STM32F10x 标准外设库 SPL](26-STM32F10x标准外设库SPL.md) | V3.5.0 工程骨架、关键 API、HAL/寄存器映射与迁移边界 |
| 27 | [网络与协议栈](27-网络与协议栈.md) | Ethernet/RMII、lwIP 线程边界、TCP/UDP、MQTT/TLS、分层排错与断网恢复 |
| 28 | [嵌入式系统与 RTOS 生态](28-嵌入式系统与RTOS生态.md) | FreeRTOS、RT-Thread、Zephyr、CMSIS-RTOS2、任务所有权、截止点与资源预算 |

## 相关目录

- [写作规范 CONTENT_GUIDE.md](CONTENT_GUIDE.md) —— 想贡献内容前请先读
- [示例代码 examples/](../examples/)
- [速查表 cheatsheets/](../cheatsheets/)
- [可视化素材 assets/](../assets/)
- [生成脚本 tools/](../tools/)

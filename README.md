<div align="center">

# STM32 学习知识库

> English: [English edition](docs/en/README.md)

**像查手册一样查知识，像看动画一样学原理。**

面向中文学习者的 STM32 系统化知识库：29 篇文档（00–28）· 25 个原理动画 · 2 张 CC0 板卡实拍 · 板卡结构图与 H7/G0/L4 引脚图 · 6 个教学光栅动画 · 14 个可编译示例 · 4 份速查表

[![docs](https://img.shields.io/badge/文档-29_篇-60a5fa?style=flat-square)](docs/)
[![book](https://github.com/zhuguang-ZFG/STM32/actions/workflows/book.yml/badge.svg)](https://github.com/zhuguang-ZFG/STM32/actions/workflows/book.yml)
[![animations](https://img.shields.io/badge/SVG_动画-25_个-22d3ee?style=flat-square)](assets/animations/)
[![boards](https://img.shields.io/badge/板卡与引脚图-10_张-fbbf24?style=flat-square)](assets/boards/)
[![photos](https://img.shields.io/badge/CC0_实拍-2_张-10b981?style=flat-square)](assets/photos/)
[![gif](https://img.shields.io/badge/教学_GIF-6_个-f87171?style=flat-square)](assets/gif/)
[![examples](https://img.shields.io/badge/可编译示例-14_个-34d399?style=flat-square)](examples/)
[![cheatsheets](https://img.shields.io/badge/速查表-4_份-a78bfa?style=flat-square)](cheatsheets/)
[![tools](https://img.shields.io/badge/素材生成-纯_Python_零依赖-f472b6?style=flat-square)](tools/)
[![license](https://img.shields.io/badge/license-MIT_+_CC_BY_4.0-lightgrey?style=flat-square)](LICENSE)
[![wechat](https://img.shields.io/badge/公众号-SIAI小宇宙-07C160?style=flat-square&logo=wechat&logoColor=white)](#公众号连载版)

<img src="assets/animations/gpio-blink.svg" width="860" alt="GPIO 推挽输出点亮 LED 动画演示">

<sub>▲ 动画：GPIO 推挽输出的电流路径与电平波形同步演示（想看大图可直接打开 SVG 文件）</sub>

</div>

---

> ### 📣 公众号连载版
>
> 本教程正在微信公众号「**SIAI小宇宙**」同步连载：与本仓库相同的 **00–28 共 29 章**图文 + 每章配套讲解视频 + 速查表，
> 手机随时翻。微信搜索「**SIAI小宇宙**」或扫文末二维码关注，关注后回复「**资料**」直达本仓库。
>
> 另外在公众号上单独发了一套「**按报错原文查**」竖版图解（No target / Flash 下载失败 /
> 串口乱码 / 烧完变砖 等），手机上照着现象查比翻 Markdown 快——入口见下面
> [「卡住了？按报错原文查」](#卡住了按报错原文查)表格的「手机版图解」列。
>
> （图文版针对手机阅读重新排版，动画与代码块已适配微信公众号渲染。）

<p align="center"><img src="assets/boards/wechat-mp-qr.png" width="220" alt="公众号 SIAI小宇宙 二维码"></p>

---

## 这个仓库想解决什么问题

网上 STM32 教程很多，但普遍有三个问题：

| 问题 | 本仓库的做法 |
| --- | --- |
| **只有文字，看不见硬件在干什么** | 每个外设配一张**会动的原理动画**（SVG + CSS 动画，GitHub 页面直接播放） |
| **不知道板子长什么样、引脚怎么接** | 自绘的**板卡实物结构图** + 全引脚标注图 + 外设接线总览 |
| **示例代码抄了跑不起来** | 每个示例都是完整可编译的 HAL 代码 + CubeMX 配置要点 + 常见坑 |

> 📌 **诚实声明**：本仓库所有插图都是**作者用代码自绘的矢量图（SVG）与程序生成的光栅动画（GIF）**，
> 不是厂商实拍照片。需要看实拍照片与官方原理图，请通过[第 21 章](docs/21-原理图与实物图鉴.md)里的官方链接查看。

## 卡住了？按报错原文查

新手跑不起来的 90% 都落在这几类。找到你屏幕上那句原话：

| 你看到的现象 | 真正的原因 | 看这里 | 手机版图解 |
| --- | --- | --- | --- |
| `No target connected`、下载按钮灰掉 | 调试器没连上（SWD 接线 / 驱动 / 目标未供电），九成不是芯片坏了 | [01 开发环境搭建](docs/01-开发环境搭建.md) | [📱 三张图](https://mp.weixin.qq.com/s/Aqg29TrABB_YddQHTPCHjQ) |
| 编译通过，下载报 `Flash Download failed` | 读保护、复位方式、Flash 算法与芯片不匹配 | [18 FAQ · 下载与调试](docs/18-常见问题FAQ.md) | [📱 三张图](https://mp.weixin.qq.com/s/BR6WAaTKvxCE_RXVA1FJkw) |
| 串口收到乱码，或第一字节丢失 | 波特率误差、时钟源配错、DMA+IDLE 用法 | [06 串口 UART](docs/06-串口UART.md) | [📱 三张图](https://mp.weixin.qq.com/s/3b5FMfd8BQNwyrTJX94CkA) |
| 烧完程序 SWD 就连不上了 | 调试口被程序关掉（`SYS → Debug` 选成 No Debug、PA13/PA14 被复用） | [18 FAQ · 下载与调试](docs/18-常见问题FAQ.md) | [📱 三张图](https://mp.weixin.qq.com/s/Tw_rMgODw9tKdZaNIAl7xQ) |
| 程序卡在 `HardFault_Handler` | 空指针、栈溢出、时钟没使能就配外设 | [17 调试与性能优化](docs/17-调试与性能优化.md) | — |
| I2C 一直返回错误、总线卡死 | 上拉缺失、从机拉低 SDA、缺总线死锁恢复 | [07 I2C 总线](docs/07-I2C总线.md) | — |
| 中断进不去 / 只进一次 | NVIC 使能顺序、标志未清、优先级分组 | [04 中断与 NVIC](docs/04-中断与NVIC.md) | — |

> 完整 30+ 条「现象 / 原因 / 解决」在 [18 常见问题 FAQ](docs/18-常见问题FAQ.md)。
> 「手机版图解」是公众号上逐条排过版的竖版长图，手机上照着查比翻 Markdown 快。

## 快速导航

| 想做什么 | 去哪里 |
| --- | --- |
| 从零开始，不知道先学什么 | [第 0 章 · 如何学习 STM32](docs/00-如何学习STM32.md) |
| 想按一本书连续阅读 / 下载离线版 | [整书构建与交付](stm32-book/)（单文件 HTML + PDF） |
| 装环境 / 连不上板子 | [第 1 章 · 开发环境搭建](docs/01-开发环境搭建.md) |
| 选芯片、看懂时钟树 | [第 2 章 · 芯片选型与存储器时钟](docs/02-芯片选型与存储器时钟.md) |
| 点亮第一颗 LED | [第 3 章 · GPIO 与 LED](docs/03-GPIO与LED.md) + [examples/gpio-blink](examples/gpio-blink/) |
| 程序卡死 / 编译不过 | [第 18 章 · 常见问题 FAQ](docs/18-常见问题FAQ.md) |
| 想选 FreeRTOS / RT-Thread / Zephyr 或设计任务架构 | [第 28 章 · 嵌入式系统与 RTOS 生态](docs/28-嵌入式系统与RTOS生态.md) |
| 想做 Ethernet 24 小时与故障注入验收 | [Ethernet 长稳证据实验](labs/ethernet-24h/) |
| 没有板子，先仿真 | [sim/](sim/README.md) · [第 22 章](docs/22-仿真实验Wokwi与Renode.md) |
| 只想要速查表 | [cheatsheets/](cheatsheets/README.md) |
| 想看所有动画和实物图 | [assets/README.md](assets/README.md) |
| 想看讲解视频怎么编号 | [assets/video/](assets/video/README.md) |
| 想自己改图 / 生成素材 | [tools/](tools/)（纯 Python，零依赖） |
| 想搞清仓库目录各自干什么 | [STRUCTURE.md](STRUCTURE.md) |

> 🔗 姊妹仓库：[**BMS-Z**](https://github.com/zhuguang-ZFG/BMS-Z) —— 学完 STM32 往上走一层：从入门到产品级的电池管理系统（BMS）中文自学路线。

## 动画演示（GitHub 页面直接播放）

<table>
<tr>
<td width="50%"><img src="assets/animations/clock-tree.svg" alt="时钟树动画"><br><sub>▲ 时钟树：8 MHz 晶振 → PLL ×9 → 72 MHz，脉冲沿树流动</sub></td>
<td width="50%"><img src="assets/animations/nvic-interrupt-flow.svg" alt="中断流程动画"><br><sub>▲ 中断全流程：置标志 → NVIC 仲裁 → 硬件入栈 → ISR → 出栈</sub></td>
</tr>
<tr>
<td><img src="assets/animations/timer-pwm.svg" alt="PWM 动画"><br><sub>▲ PWM：CNT 与 CCR 比较，占空比随时间变化</sub></td>
<td><img src="assets/animations/i2c-transaction.svg" alt="I2C 时序动画"><br><sub>▲ I2C：START / 地址 / ACK / 数据 / STOP 逐拍演示</sub></td>
</tr>
<tr>
<td><img src="assets/animations/dma-circular.svg" alt="DMA 循环搬运"><br><sub>▲ DMA 循环模式：CPU 与 DMA 并行工作</sub></td>
<td><img src="assets/animations/freertos-scheduler.svg" alt="FreeRTOS 调度"><br><sub>▲ FreeRTOS：任务状态迁移 + 抢占式调度甘特图</sub></td>
</tr>
</table>

完整清单（25 个 SVG 动画）见 [assets/README.md](assets/README.md)。下面 6 个是标准库生成的教学 GIF。`assets/gif/` 里另有 20 个 `*-zh.gif`，由 `tools/svg2gif.py` 从 SVG 采样，给公众号用，不是这 6 张的译文：

<div align="center">
<img src="assets/gif/led-blink.gif" width="330" alt="LED 闪烁 GIF">
<img src="assets/gif/pwm-breath.gif" width="330" alt="PWM 呼吸灯 GIF">
<br>
<img src="assets/gif/uart-bits.gif" width="330" alt="UART 逐位发送 GIF">
<img src="assets/gif/sar-adc.gif" width="330" alt="SAR ADC 逐次逼近 GIF">
<br>
<img src="assets/gif/i2c-timing.gif" width="330" alt="I2C 时序 GIF">
<img src="assets/gif/dma-ring.gif" width="330" alt="DMA 环形缓冲 GIF">
<br>
<sub>▲ GIF 用标准库手写的 GIF89a/LZW 编码器生成，帧间差分 + 透明索引压缩；文字为 ASCII（内置点阵字体限制）</sub>
</div>

## 实物结构图（自绘矢量图）

<div align="center">
<img src="assets/boards/bluepill-stm32f103c8t6.svg" width="880" alt="BluePill 实物结构图">
<br><sub>▲ Blue Pill（STM32F103C8T6）：20+20 排针定义、板载元件编号标注、典型参数</sub>
</div>

| 图 | 说明 |
| --- | --- |
| [bluepill-stm32f103c8t6.svg](assets/boards/bluepill-stm32f103c8t6.svg) | 蓝色药丸最小系统板：排针定义、BOOT 跳线、1.5 kΩ USB 上拉、山寨识别点 |
| [blackpill-stm32f411ce.svg](assets/boards/blackpill-stm32f411ce.svg) | 黑色药丸（WeAct V3.1）：Type-C、25 MHz 晶振、100 MHz 主频 |
| [nucleo-f411re.svg](assets/boards/nucleo-f411re.svg) | 官方 Nucleo-64：板载 ST-Link/V2-1、Morpho + Arduino 排针 |
| [f4-discovery.svg](assets/boards/f4-discovery.svg) | 官方 F4-Discovery：加速度计、音频 DAC、MEMS 麦克风、4 颗用户 LED |
| [f103zet6-dev.svg](assets/boards/f103zet6-dev.svg) | F103ZET6 大板：FSMC LCD、SD 卡、CAN/RS485/RS232、双 Flash |
| [pinout-bluepill.svg](assets/boards/pinout-bluepill.svg) | **LQFP48 全 48 脚编号图** + 复用功能对照 + 看引脚图的 5 个要点 |
| [peripheral-wiring.svg](assets/boards/peripheral-wiring.svg) | 8 个入门外设的接线总览与资源冲突提示 |
| [pinout-stm32g071rb-lqfp64.svg](assets/boards/pinout-stm32g071rb-lqfp64.svg) | G071RB LQFP64，脚序来自 DS12232 Rev 5 Table 12 |
| [pinout-stm32l476rg-lqfp64.svg](assets/boards/pinout-stm32l476rg-lqfp64.svg) | L476Rx LQFP64，脚序来自 DS10198 Rev 11 Figure 16 |
| [pinout-stm32h743zi-lqfp144.svg](assets/boards/pinout-stm32h743zi-lqfp144.svg) | H743xI LQFP144，脚序来自 DS12110 Rev 11 Figure 7 |

## 学习路线图

```text
阶段一 · 入门（约 4 周）      阶段二 · 进阶（约 6 周）        阶段三 · 实战（约 8 周）
──────────────────────      ──────────────────────        ──────────────────────
环境搭建 / 点灯               DMA + 双缓冲                  RTOS 多任务
GPIO 输入输出                  ADC 采样与滤波                 USB / CAN / 以太网
中断与 NVIC                    RTC / 看门狗 / 低功耗          IAP 远程升级
定时器与 PWM                   Flash 读写 / IAP               LCD / 摄像头 / 音频
串口收发与 printf              I2C 传感器 / SPI Flash         综合项目（见 19 章）
I2C / SPI 基础                 FreeRTOS 入门                 开源自己的库
产出：能独立调通 5 个外设       产出：能读懂时序图与手册         产出：能交付一个完整产品原型
```

每章文末都有「动手实验」和自测清单，做完就算过关。详细说明见
[第 0 章 · 如何学习 STM32](docs/00-如何学习STM32.md)。


## 章节目录

<details open>
<summary><b>基础篇（00 ~ 08）</b></summary>

| # | 章节 | 关键词 | 配套动画 |
| --- | --- | --- | --- |
| 00 | [如何学习 STM32](docs/00-如何学习STM32.md) | 路线图 · 硬件清单 · 三种开发方式 | `toolchain-flow` |
| 01 | [开发环境搭建](docs/01-开发环境搭建.md) | Keil / CubeIDE / PlatformIO · ST-Link · SWD | `boot-sequence` |
| 02 | [芯片选型与存储器时钟](docs/02-芯片选型与存储器时钟.md) | 命名规则 · 存储器映射 · 时钟树 | `memory-map` `clock-tree` |
| 03 | [GPIO 与 LED](docs/03-GPIO与LED.md) | 8 种模式 · 推挽/开漏 · 限流电阻 | `gpio-blink` `led-blink.gif` |
| 04 | [中断与 NVIC](docs/04-中断与NVIC.md) | 优先级分组 · EXTI · 中断安全 | `nvic-interrupt-flow` `gpio-input-interrupt` |
| 05 | [定时器与 PWM](docs/05-定时器与PWM.md) | 时基公式 · 占空比 · 输入捕获 | `timer-pwm` `timer-modes` `pwm-breath.gif` |
| 06 | [串口 UART](docs/06-串口UART.md) | 帧格式 · 波特率误差 · DMA+IDLE | `uart-frame` `uart-bits.gif` |
| 07 | [I2C 总线](docs/07-I2C总线.md) | 开漏上拉 · ACK · 总线死锁恢复 | `i2c-transaction` |
| 08 | [SPI 总线](docs/08-SPI总线.md) | 全双工移位 · CPOL/CPHA · 片选 | `spi-transfer` |

</details>

<details open>
<summary><b>进阶篇（09 ~ 17）</b></summary>

| # | 章节 | 关键词 | 配套动画 |
| --- | --- | --- | --- |
| 09 | [ADC 与 DAC](docs/09-ADC与DAC.md) | 逐次逼近 · 采样时间 · 内部温度传感器 | `adc-sar` `sar-adc.gif` |
| 10 | [DMA](docs/10-DMA.md) | 通道/流映射 · 循环模式 · Cache 一致性 | `dma-circular` `dma-ring.gif` |
| 11 | [RTC 与看门狗](docs/11-RTC与看门狗.md) | LSE 备份域 · 闹钟 · IWDG/WWDG | `iwdg-window` |
| 12 | [Flash 与 IAP 升级](docs/12-Flash与IAP升级.md) | 扇区擦除 · 解锁序列 · 双区跳转 | `flash-iap` |
| 13 | [CAN 总线](docs/13-CAN总线.md) | 非破坏性仲裁 · 位填充 · 过滤器 | `can-arbitration` |
| 14 | [USB](docs/14-USB.md) | 枚举 · 描述符 · CDC / HID | `usb-enumeration` |
| 15 | [FreeRTOS 入门](docs/15-FreeRTOS入门.md) | 任务状态 · 优先级 · 队列/信号量 | `freertos-scheduler` |
| 16 | [低功耗设计](docs/16-低功耗设计.md) | Sleep/Stop/Standby · WFI · 唤醒源 | `lowpower-wakeup` |
| 17 | [调试与性能优化](docs/17-调试与性能优化.md) | SWD/SWO · HardFault 定位 · DWT 计时 | `debug-swo` |

</details>

<details open>
<summary><b>实战、仿真、系列引脚、SPL、网络与系统（18 ~ 28）</b></summary>

| # | 章节 | 关键词 |
| --- | --- | --- |
| 18 | [常见问题 FAQ](docs/18-常见问题FAQ.md) | 30+ 条「现象 / 原因 / 解决」 |
| 19 | [项目实战合集](docs/19-项目实战合集.md) | 10 个递进项目：蓝牙小车、示波器、数据采集卡… |
| 20 | [学习资源与工具链](docs/20-学习资源与工具链.md) | 官方手册命名规则 · 中文社区 · 开源固件库 |
| 21 | [原理图与实物图鉴](docs/21-原理图与实物图鉴.md) | 5 块板卡结构图 + 如何看懂最小系统原理图 |
| 22 | [仿真实验 Wokwi 与 Renode](docs/22-仿真实验Wokwi与Renode.md) | 浏览器接线 · Renode 加载 ELF · DMA 模型边界 |
| 23 | [STM32G0 引脚](docs/23-STM32G0引脚.md) | G071RB · BOOT0/SWCLK 真值表 · 选项字节 · Under Reset 恢复 |
| 24 | [STM32L4 引脚](docs/24-STM32L4引脚.md) | L476RG · Nucleo-64 实拍 · Stop 2 IRQ 留证据 · JP6 功耗测量 |
| 25 | [STM32H7 引脚](docs/25-STM32H7引脚.md) | H743ZI 引脚/供电 · Rev Y/W 与 V · 400/480 MHz 时钟链 · MCO 验证 |
| 26 | [STM32F10x 标准外设库 SPL](docs/26-STM32F10x标准外设库SPL.md) | V3.5.0 工程骨架 · HAL/SPL/寄存器映射 · 旧工程迁移 |
| 27 | [网络与协议栈](docs/27-网络与协议栈.md) | Ethernet/RMII · lwIP · TCP/UDP · MQTT/TLS · 分层排错与断网恢复 |
| 28 | [嵌入式系统与 RTOS 生态](docs/28-嵌入式系统与RTOS生态.md) | FreeRTOS · RT-Thread · Zephyr · CMSIS-RTOS2 · 所有权/截止点/资源预算 |

</details>

> 写新章节前请先读 [docs/CONTENT_GUIDE.md](docs/CONTENT_GUIDE.md)（统一骨架与图文规范）。


## 示例代码与速查表

示例以**完整可编译**的 HAL 代码为主；`spl-f1-blink` 是冻结 SPL V3.5.0 的 CMake 工程。
每个 README 给出硬件接线、配置边界、关键代码、构建/烧录、预期现象与排错方法。

| 示例 | 难度 | 涉及外设 | 对应章节 |
| --- | --- | --- | --- |
| [spl-f1-blink](examples/spl-f1-blink/) | ★★ | SPL GPIO + SysTick + CMake/OpenOCD | 01 / 26 |
| [gpio-blink](examples/gpio-blink/) | ★ | GPIO 推挽输出 | 03 |
| [exti-key](examples/exti-key/) | ★★ | EXTI + NVIC + 消抖 | 04 |
| [timer-pwm](examples/timer-pwm/) | ★★ | TIM PWM 输出 | 05 |
| [uart-dma-idle](examples/uart-dma-idle/) | ★★★ | UART + DMA + IDLE + 环形缓冲 | 06 / 10 |
| [i2c-oled](examples/i2c-oled/) | ★★★ | 硬件 I2C + SSD1306 | 07 |
| [spi-flash](examples/spi-flash/) | ★★★ | SPI + W25Q64 | 08 |
| [adc-dma](examples/adc-dma/) | ★★★ | ADC 多通道 + DMA + 滤波 | 09 / 10 |
| [rtc-alarm](examples/rtc-alarm/) | ★★ | RTC + 闹钟 + 备份域 | 11 |
| [freertos-task](examples/freertos-task/) | ★★★★ | FreeRTOS 多任务 + 队列 | 15 |
| [iap-bootloader](examples/iap-bootloader/) | ★★★★ | Flash 编程 + 跳转 APP | 12 |
| [can-bxcan](examples/can-bxcan/) | ★★★★ | bxCAN 环回 / 过滤器 / Bus-Off | 13 |
| [usb-cdc](examples/usb-cdc/) | ★★★★ | USB CDC 虚拟串口 | 14 |
| [usb-hid](examples/usb-hid/) | ★★★★ | USB HID 键盘 | 14 |

速查表（打印出来贴显示器旁边那种）：

| 速查表 | 内容 |
| --- | --- |
| [HAL 速查表](cheatsheets/HAL速查表.md) | 各外设常用 HAL 函数、参数、返回值与错误码 |
| [寄存器速查表](cheatsheets/寄存器速查表.md) | GPIO / RCC / TIM / USART / NVIC 关键位 |
| [外设总线与引脚速查表](cheatsheets/外设总线与引脚速查表.md) | F103/F411 总线挂载表、默认引脚、AF 编号 |
| [错误码与排查速查表](cheatsheets/错误码与排查速查表.md) | HAL 状态机、25+ 条现象→原因→定位手段 |

## 仓库结构

```text
STM32/
├── README.md                 ← 你在这里（门户首页）
├── STRUCTURE.md              ← 目录约定、本轮改动、后续事项
├── Makefile                  ← make assets / check / book / book-check
├── docs/                     ← 中文 00–28 + CONTENT_GUIDE.md
│   └── en/                   ← 英文 00–28、英文速查表
├── examples/                 ← 14 个可编译示例（Wokwi 工程在示例目录内）
├── labs/                     ← 真板证据协议（目前：ethernet-24h）
├── sim/renode/               ← Renode .resc
├── cheatsheets/              ← 4 份中文速查表
├── stm32-book/               ← 整书：manifest、附录、离线 HTML/PDF
├── assets/                   ← 动画、板卡图、实拍、GIF、讲解视频
└── tools/                    ← 生成脚本（清单见 tools/README.md）

不入库（.gitignore，只在作者本机）：wechat-mp/ 、 final-videos/
```

各目录的入口文件和「不要混放」的边界写在 [STRUCTURE.md](STRUCTURE.md)。

## 素材是怎么来的（可复现）

板卡图、引脚图和下面命令里的教学 GIF 用 Python 标准库就能重新生成。`assets/gif/*-zh.gif` 由 `tools/svg2gif.py` 从 SVG 采样，需要本机 Chrome 和 Pillow。
`assets/photos/` 的两张 CC0 实拍不由脚本生成，来源页、处理方式与 SHA-256 记录在该目录的 README：

```bash
# 生成 SVG 动画（CSS/SMIL 动画，GitHub 页面直接播放）
python3 tools/gen_animations.py

# 生成板卡实物结构图、系列引脚图与静态框图
python3 tools/gen_boards.py
python3 tools/gen_pinouts.py
python3 tools/gen_diagrams.py

# 生成 6 个光栅 GIF（内置 5×7 点阵字体 + 手写 GIF89a/LZW 编码器）
python3 tools/gen_gifs.py

# 自检：SVG 是否合法 XML、GIF 解码回来是否与源帧逐像素一致
python3 tools/check_assets.py
```

`tools/minigfx.py` 里的 GIF 编码器支持**帧间差分 + 透明索引**（未变化的像素不重复编码），
所以 24 帧的 480×300 动画只有 7.5 KB。`tools/check_assets.py` 自带 LZW 解码器，
会把生成的 GIF 解回像素与原帧逐字节比对，避免「图能生成但打不开」的尴尬。

## 贡献指南

欢迎 PR / Issue，尤其是这三类：

1. **纠错**：寄存器位、时序参数、公式、引脚复用写错了 —— 请附上手册页码或截图。
2. **补动画**：用 `tools/svgkit.py` 写一个新动画（记得在 `assets/README.md` 里登记）。
3. **补示例**：新增一个 `examples/xxx/`（`main.c` + `README.md`），要求真实可编译。

动手前请读 [docs/CONTENT_GUIDE.md](docs/CONTENT_GUIDE.md)（文章骨架、命名、图文规范），
提交信息建议：`docs(05): 补充 PWM 占空比公式与呼吸灯动画`。

## 许可与声明

- **代码**（`examples/`、`tools/`）采用 [MIT License](LICENSE)。
- **文档与仓库原创图片**采用 **CC BY 4.0**；`assets/photos/` 中两张第三方实拍保持其 **CC0 1.0** 许可。转载/二次创作请按对应资产的来源记录署名。
- SVG / GIF / 引脚图均为作者自绘或程序生成；`assets/photos/` 的两张 Nucleo-64 实拍来自 Wikimedia Commons，采用 CC0 1.0，作者、原图页与处理记录见 [照片清单](assets/photos/README.md)。STM32、Nucleo、Discovery 等是 STMicroelectronics 的商标，本仓库仅用于学习交流，与 ST 官方无隶属关系。

## Roadmap

- [x] 29 章知识文档 + 写作规范
- [x] 25 个 SVG 原理动画（清单见 [assets/README.md](assets/README.md)，含 G0 启动与 SWD 恢复）
- [x] 7 张板卡结构图 + 3 张芯片引脚图 + 2 张带许可记录的 CC0 实拍
- [x] 6 个零依赖生成的 GIF 动画 + 素材自检工具
- [x] 14 个可编译示例 + 4 份速查表（含 SPL/CMake、bxCAN 与 USB CDC/HID）
- [x] 第 00–28 章讲解视频（`assets/video/`，约 2–4 分钟 MP4，中文配音 + SRT，脚本可复现，不是实拍）
- [x] Wokwi 工程（核心示例的 diagram.json + wokwi.toml）与 Renode `.resc`，见第 22 章
- [x] H7 / G0 / L4 引脚图与差异（第 23–25 章，脚序来自 DS12232 / DS10198 / DS12110）
- [x] 英文版（[docs/en/](docs/en/README.md)，00–28 章与四份速查表）

---

<div align="center">
<sub>如果这个仓库帮你少踩了一个坑，欢迎点个 ⭐ Star —— 这是持续更新的最大动力。</sub>
<br><br>
<b>持续更新中 · 最后更新见 commit 记录</b>
</div>



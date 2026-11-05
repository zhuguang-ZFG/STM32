---
title: 导读·实物装备清单
---

# 实物装备清单：照着买，不花冤枉钱

> 🎯 嵌入式学习有一条铁律：**手上没有硬件，看懂的都是假懂**。好消息是全套装备不超一顿火锅钱；坏消息是买错一件就要等三天快递。本页照单抓药。

## 核心两块板（作者实持，全站实验按它们写）

| 板卡 | 角色 | 关键配置 | 用在哪 |
|---|---|---|---|
| [野火 STM32F407 霸天虎](https://doc.embedfire.com/products/link/zh/latest/mcu/stm32/stm32f407_batianhu.html) | STM32 主线 | F407ZGT6：168MHz、1MB Flash、192KB RAM；RGB 灯 PF6/7/8 | [S 篇](../stm32/index.md) 全部 + RTOS 移植 |
| [立创·实战派 ESP32-S3](https://wiki.lckfb.com/zh-hans/szpi-esp32s3/)（小智板） | ESP32 主线 | N16R8：LX7 双核 240MHz、16MB Flash、8MB PSRAM；2 寸屏/双麦/喇叭/姿态传感器 | [P 篇](../esp32/index.md) 全部 |
| 2.8 寸 ESP32-S3 显示模块（ES3C28P，[LCD wiki 资料](https://www.lcdwiki.com/zh/2.8inch_ESP32-S3_Display)） | ESP32 当前持板 | N16R8 同款主控；ILI9341V 2.8 寸屏（SPI：CS=IO10/DC=IO46/SCK=IO12）；FT6336G 触摸（I2C=IO15/16，INT=IO17 低有效）；ES8311 音频；WS2812 RGB=IO42；SD=SDIO；电池 ADC=IO9 | [P 篇](../esp32/index.md) 实验（触摸/屏/音频场景） |

::: warning 买板注意
霸天虎**不板载仿真器**，必须另购调试器（见下表）。立创 S3 板与 ES3C28P 均为 Type-C 一线通吃（供电+烧录+串口），无此问题。两块 S3 板都是 N16R8 小智系（16MB Flash + 8MB PSRAM），P 篇正文通用；差异在板载外设：实战派带姿态传感器 QMI8658（[E07](../lab/e07-qmi8658.md)），ES3C28P 带电容触摸与 2.8 寸方屏（FT6336G/ILI9341V）。引脚以各板资料页为准，上板前先核。
:::

### 板卡与主控实拍参考

三张开源许可的实物照片，帮你下单前后认板子、认模组。**野火霸天虎官方产品图受版权保护，本站不转载**，外观与引脚图请看[官方资料页](https://doc.embedfire.com/products/link/zh/latest/mcu/stm32/stm32f407_batianhu.html)。

![立创·实战派 ESP32-S3 开发板：2 寸 IPS 屏、摄像头开孔、Type-C 接口](/images/boards/lichuang-s3-board.jpg)

立创·实战派 ESP32-S3 整板（P 篇主线板）。来源：[xiaozhi-esp32 项目](https://github.com/78/xiaozhi-esp32)（MIT 许可）。

![ESP32-S3-WROOM-1-N16R8 模组特写：屏蔽罩上印型号与 N16R8 后缀](/images/boards/esp32s3-wroom1-module.jpg)

实战派/ES3C28P 板载的 **ESP32-S3-WROOM-1-N16R8** 模组（16MB Flash + 8MB PSRAM），屏蔽罩丝印清晰。来源：[Wikimedia Commons](https://commons.wikimedia.org/wiki/File:ESP32-S3_on_paper.jpg)（CC BY-SA 4.0，作者 VectorVoyager）。

![基于 STM32F407 的第三方开发板](/images/boards/stm32f407-board.jpg)

F407 家族板卡形态参考：图为一款第三方 F407VET6 板（LQFP100、带以太网）；霸天虎为 F407ZGT6/LQFP144，外观不同、芯片同门。来源：[Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Embedded_World_2016,_STM32_F407_VGT6.jpg)（CC0，作者 Ordercrazy；该 Commons 页面标题误作 Nucleo，实为第三方板，本站按实物标注）。

> 以上均为**资料参考图**，不是上板验证证据——实验的实测记录仍以 [evidence 文件与实测照片](verify-on-hardware.md)为准。

## 必配工具

| 装备 | 参考价 | 用途 | 用在哪 |
|---|---|---|---|
| ST-Link V2（或 J-Link EDU/DAPLink） | ¥20–80 | 霸天虎的烧录+调试 | [S0](../stm32/00-env.md) 起每章 |
| USB 转 TTL 串口模块（CH340/CP2102） | ¥8 | 霸天虎 printf 输出 | [S7 USART](../stm32/07-usart.md) 起 |
| 24MHz 8 通道逻辑分析仪（saleae 兼容） | ¥30–60 | 抓 UART/I2C/SPI 波形 | [E02](../lab/e02-logic-uart.md)、[E05](../lab/e05-i2c-eeprom.md)、S6/S11/S12 |
| Micro-USB 数据线 ×2 + Type-C 数据线 ×1 | ¥15 | 供电与连接 | 全程 |
| 杜邦线一排 + 面包板一块 | ¥10 | 外接实验电路 | S9 ADC、S11 I2C 起 |

## 选配（学到再买）

| 装备 | 什么时候需要 |
|---|---|
| 示波器（100MHz 入门即可） | [E03 PWM 波形](../lab/e03-scope-pwm.md)、[S10 DAC 正弦](../stm32/10-dac.md)；逻辑分析仪能看方波，看不了模拟量 |
| 万用表 | [S14 功耗实测](../stm32/14-pwr.md)、[E06 电流](../lab/e06-lowpower-current.md)；排查供电也好用 |
| 电位器 + 光敏电阻 + 有源蜂鸣器 | [S9 ADC](../stm32/09-adc.md) 模拟量实验 |
| SSD1306 OLED（I2C 接口） | [S11 I2C](../stm32/11-i2c.md) 扩展实验（S3 板自带屏，不需要） |

### 工具实拍参考

六张开源许可的工具/器件照片，帮你在淘宝详情页里认出"该买的是哪种东西"。具体型号不必一致，形态和接口对得上就行。

![SEGGER J-Link EDU 调试器：灰色外壳，一端 USB，另一端 20 针 JTAG/SWD 排座](/images/tools/jlink-edu.jpg)

**调试器**：J-Link EDU，正面印着 "JTAG / SWD + SWO"，20 针排座是 ARM 标准 JTAG 接口。ST-Link V2 克隆体积更小（U 盘形状、4~10 针杜邦排针），功能上对霸天虎一样够用；接线只需 SWDIO/SWCLK/GND（必要时加 3V3 参考）。来源：[Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Segger_J-Link_EDU.jpg)（CC BY-SA 3.0，作者 SEGGER Microcontroller GmbH & Co）。

![FTDI TTL-232R 线缆：一端 USB-A 插头，另一端 6 针彩色线排母](/images/tools/usb-ttl-cable.jpg)

**USB 转 TTL**：图为线缆式 FTDI TTL-232R，6 针排母分别是 GND/CTS/VCC/TXD/RXD/RTS。注意插头上印着 **5V**：这是 5V 电平版本，接 3.3V 的 STM32/ESP32 要选 **3V3 版**或带电平跳线的 CH340/CP2102 小板，并且 TX↔RX 交叉接。来源：[Wikimedia Commons](https://commons.wikimedia.org/wiki/File:FTDI_USB-TTL_Cable_1_(3614831958).jpg)（CC BY 2.0，作者 Windell Oskay）。

![自制 8 通道 USB 逻辑分析仪：开盖外壳、彩色排线与测试钩](/images/tools/logic-analyzer-8ch.jpg)

**逻辑分析仪**：图为一台**自制** 8 通道 USB 分析仪，用来示意"8 根通道线 + 测试钩"的形态；淘宝 ¥30 的 24MHz saleae 兼容款是火柴盒大小的铝壳，接法一样：每根通道线夹一个信号，**GND 必须与被测板共地**。来源：[Wikimedia Commons](https://commons.wikimedia.org/wiki/File:8_Channel_USB_logic_analyzer_(5172098012).jpg)（CC BY-SA 2.0，作者 Dilshan Jayakody）。

![RIGOL DS1054Z 四通道数字示波器，屏幕显示一条正弦波](/images/tools/oscilloscope-ds1054z.jpg)

**示波器**：RIGOL DS1054Z（4 通道、50MHz、1GSa/s），入门级常见款。屏幕上的正弦波正是逻辑分析仪看不到的模拟量；探头档位（图中 Probe 10X）要与探头本身的 ×1/×10 开关一致，否则幅值读数差 10 倍。来源：[Wikimedia Commons](https://commons.wikimedia.org/wiki/File:RIGOL_DS1054Z_Digital_Storage_Oscilloscope.jpg)（CC BY-SA 4.0，作者 Draconichiaro）。

![DT830D 数字万用表：旋钮档位含直流电压、直流电流 200μ/2m/20m/200m/10A、电阻](/images/tools/multimeter-dt830d.jpg)

**万用表**：最便宜的 DT830 系列就能测电压和 mA 级电流。测电流要把红表笔挪到 **VΩmA 孔并串入回路**，档位从大往小拨；图中 10A 孔标着 UNFUSED（无保险丝），误接短路会直接烧表。待机电流低到 μA 级时，这类表的分辨率就不够了（[E06](../lab/e06-lowpower-current.md) 会讲怎么判断）。来源：[Wikimedia Commons](https://commons.wikimedia.org/wiki/File:DT830D_DIGITAL_MULTIMETER.jpg)（CC0，作者 Ranjithkumar Murugesan）。

![24C02 EEPROM 芯片，SOIC-8 贴片封装，表面丝印 24C02](/images/tools/eeprom-24c02.jpg)

**24C02 EEPROM**：[E05](../lab/e05-i2c-eeprom.md) 的被测器件，2Kbit（256 字节），SOIC-8 封装；圆点标记 1 脚（A0），引脚逆时针编号，1 脚正对面的 8 脚是 VCC、同排末端的 4 脚是 GND。买现成的 AT24C02 小模块（带上拉电阻和排针）比焊裸片省事。来源：[Wikimedia Commons](https://commons.wikimedia.org/wiki/File:24C02_Package.jpg)（CC BY-SA 2.0，作者 cole8888）。

> 同样是**资料参考图**：照片里的仪器不是作者实验用机，读数也不是本站实测数据。

## 软件全部免费

- STM32 侧：Arm GNU Toolchain + make + OpenOCD + VSCode（[S0](../stm32/00-env.md) 手把手装）
- ESP32 侧：ESP-IDF v5.5.x 官方安装器（[P0](../esp32/00-env.md)）
- 上位机：PulseView（逻辑分析仪配套，开源免费）、串口助手任选

## 记忆锚点

::: tip 一句话记住
**两块板 + 三件套（仿真器、串口、逻辑分析仪）就能走完全站**；示波器和万用表是进阶 DLC，学到再买不迟。
:::

## 常见坑

- **数据线变充电线**：只能供电不能通信，症状是插上去设备管理器毫无反应。换线先试。
- **便宜 ST-Link 固件太旧**：个别国产 V2 克隆需要升级固件才能被新 OpenOCD 识别，买评价里"OpenOCD 可用"的。
- **逻辑分析仪别买 8 通道以下的**：SPI 全双工 + 片选就要 4 根线，8 通道是底线。

## 图片来源与许可

本站正文与代码采用 Apache-2.0 许可；页面照片为第三方素材，各自遵循其原始许可，再利用时请遵守对应条款：

| 图片 | 引用页 | 来源 | 许可 |
|---|---|---|---|
| `/images/boards/lichuang-s3-board.jpg` | 本页、[实验中心](../lab/index.md) | [78/xiaozhi-esp32](https://github.com/78/xiaozhi-esp32) | MIT |
| `/images/boards/esp32s3-wroom1-module.jpg` | 本页、[P0 环境](../esp32/00-env.md) | [Wikimedia Commons · VectorVoyager](https://commons.wikimedia.org/wiki/File:ESP32-S3_on_paper.jpg) | CC BY-SA 4.0 |
| `/images/boards/stm32f407-board.jpg` | 本页、[S0 环境](../stm32/00-env.md) | [Wikimedia Commons · Ordercrazy](https://commons.wikimedia.org/wiki/File:Embedded_World_2016,_STM32_F407_VGT6.jpg) | CC0 |
| `/images/tools/jlink-edu.jpg` | 本页 | [Wikimedia Commons · SEGGER](https://commons.wikimedia.org/wiki/File:Segger_J-Link_EDU.jpg) | CC BY-SA 3.0 |
| `/images/tools/usb-ttl-cable.jpg` | 本页 | [Wikimedia Commons · Windell Oskay](https://commons.wikimedia.org/wiki/File:FTDI_USB-TTL_Cable_1_(3614831958).jpg) | CC BY 2.0 |
| `/images/tools/logic-analyzer-8ch.jpg` | 本页、[E02](../lab/e02-logic-uart.md) | [Wikimedia Commons · Dilshan Jayakody](https://commons.wikimedia.org/wiki/File:8_Channel_USB_logic_analyzer_(5172098012).jpg) | CC BY-SA 2.0 |
| `/images/tools/oscilloscope-ds1054z.jpg` | 本页、[E03](../lab/e03-scope-pwm.md) | [Wikimedia Commons · Draconichiaro](https://commons.wikimedia.org/wiki/File:RIGOL_DS1054Z_Digital_Storage_Oscilloscope.jpg) | CC BY-SA 4.0 |
| `/images/tools/multimeter-dt830d.jpg` | 本页、[E06](../lab/e06-lowpower-current.md) | [Wikimedia Commons · Ranjithkumar Murugesan](https://commons.wikimedia.org/wiki/File:DT830D_DIGITAL_MULTIMETER.jpg) | CC0 |
| `/images/tools/eeprom-24c02.jpg` | 本页、[E05](../lab/e05-i2c-eeprom.md) | [Wikimedia Commons · cole8888](https://commons.wikimedia.org/wiki/File:24C02_Package.jpg) | CC BY-SA 2.0 |

实验实测照片（待上板后补充）将存放于 `docs/public/photos/`，命名与回填规范见[上板验证指南](verify-on-hardware.md)。

## 你做到了

- 一张不花冤枉钱的购物清单到手；
- 知道每件装备在路线图的哪个位置等你。

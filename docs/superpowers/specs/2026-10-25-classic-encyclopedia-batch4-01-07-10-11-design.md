# 第 01、07、10、11 章加厚设计

日期：2026-10-25  
状态：待人审。人接受这份规格之前不实施  
基线：`main` 上的整书 **v1.2.2**（`205fba7ba10000facbafece55a31f8372e4a541e`，PR #32，2026-10-25）  
上一份设计：[2026-10-25-classic-encyclopedia-batch3-02-05-08-09-design.md](2026-10-25-classic-encyclopedia-batch3-02-05-08-09-design.md)（PR #30）。四块模板来自 [2026-10-25-classic-encyclopedia-thicken-design.md](2026-10-25-classic-encyclopedia-thicken-design.md)（PR #18）。Batch2 规格是 [2026-10-25-classic-encyclopedia-batch2-04-06-design.md](2026-10-25-classic-encyclopedia-batch2-04-06-design.md)（PR #22）。  
本文件只记录这一批的设计。它不改章节正文，不画新图，不改 `stm32-book/` 构建，不升版本号，不打 tag，不发布 Release，不写实施计划。

章号按文件名前缀锁死，不按主题改名。文件 `01` 是开发环境搭建，文件 `07` 是 I2C 总线，文件 `10` 是 DMA，文件 `11` 是 RTC 与看门狗。不要把这一批写成 GPIO、ADC、SPI 或定时器。

## 背景

v1.2.2 已经按大典四块加厚的是第 00、02、03、04、05、06、08、09 章。这一批只加厚另外四章，中文和英文一起写：

| 文件前缀 | 中文 | 英文 | 这一章在讲 |
| --- | --- | --- | --- |
| `01` | `docs/01-开发环境搭建.md` | `docs/en/01-dev-environment.md` | 编译、烧录、SWD、向量表、读保护 |
| `07` | `docs/07-I2C总线.md` | `docs/en/07-i2c.md` | 开漏、地址字节、上拉、CCR |
| `10` | `docs/10-DMA.md` | `docs/en/10-dma.md` | DMA1 通道、半字、CNDTR |
| `11` | `docs/11-RTC与看门狗.md` | `docs/en/11-rtc-watchdog.md` | LSE 分频、备份寄存器、IWDG 的 1 秒 |

读者看到的章号仍是文件名前缀加 1：文件 `01` 在书里是第 2 章，`07` 是第 8 章，`10` 是第 11 章，`11` 是第 12 章。源文件的一级标题继续带 `01`、`07`、`10`、`11`。这一批不改这个加 1。

第 00 章已经画过启动别名（`sample-00-boot-state.svg`：BOOT0=0 时 `0x00000000` 别名到闪存 `0x08000000`；BOOT1=0 且 BOOT0=1 时取到系统存储器 `0x1FFFF000`）。第 03 章已经钉过 SWD 的信号名（PA13 = SWDIO，PA14 = SWCLK）和 PC13 的 3 mA。第 06 章已经钉过 USART1 在第 30 脚 PA9、第 31 脚 PA10，复位后不是 PB6/PB7。第 08 章的片选是推挽，不是这一章的开漏。第 09 章已经把半字和 `CNDTR` 留在第 10 章。这几张图都不重画。

对照 v1.2.2 核对过的事实：

1. **这四章还没有四块。** 已经加厚的章在 `<!-- /video: -->` 之后、学习目标之前，有 `## 原理与边界`、`## 关键插图`、`## 时序或状态`、`## 坑与出处卡`（英文是 `Principle and boundary`、`Key figures`、`Timing or state`、`Pitfalls and source cards`）。这四章仍从学习目标写起。中文坑还在 `## ⚠️ 常见坑与排查`，英文坑还在 `## ⚠️ Pitfalls and troubleshooting`，坑表没有 `#source-`。
2. **第 01 章把救砖写成了进 SRAM，把无保护写成了 `AA`。** 坑表写「BOOT0=1 从 SRAM 启动再擦除」。按第 00 章已经冻结的 RM0008 表 9：BOOT1=0 且 BOOT0=1 时，`0x00000000` 别名到系统存储器 `0x1FFFF000`，不是 SRAM。SRAM 要 BOOT1=1 且 BOOT0=1。读保护解锁写「选 `AA`（Level 0）」。F103 的 RDP 键是 `0xA5`：`0x1FFFF800` 的低字节写成 `0xA5` 才允许读出；改回 `0xA5` 解除保护时先整片擦除主闪存。`0xAA` 是别的系列的无保护键，在 STM32F103C8T6 上作废。这颗料没有 F4 那种 `0xCC` 的 Level 2。DS5319 Rev 20 表 5 的 LQFP48：第 34 脚是 PA13（JTMS/SWDIO），第 35 脚是 VSS_2，第 36 脚是 VDD_2，第 37 脚才是 PA14（JTCK/SWCLK）。第 35 脚不是 SWCLK。第 7 脚是 NRST，第 44 脚是 BOOT0。订货号 STM32F103C8T6 的闪存是 64 KB，从 `0x08000000` 起；SRAM 是 20 KB，从 `0x20000000` 起。同一手册里 xB 的 128 KB 在这颗料上作废。
3. **第 07 章的 4.7 kΩ 和 `0x78` 已经在附录 D，主图仍是事务动画，而且把 1 MHz 和标准模式的上升时间写混了。** 附录 D：SSD1306 的 7 位地址 `0x3C`，HAL 的 DevAddress 填 `0x78`。短总线外接 4.7 kΩ 到 3.3 V。片内上下拉约 30–50 kΩ，不能靠它跑 400 kHz。`examples/i2c-oled` 把 `OLED_ADDR` 定义成 `0x78`。DS5319 Rev 20 表 42 在 fPCLK1 = 36 MHz、VDD_I2C = 3.3 V、Rp = 4.7 kΩ 这一行印出：400 kHz 的 `I2C_CCR = 0x801E`，100 kHz 的 `I2C_CCR = 0x00B4`。`0x801E` 是快速模式、DUTY = 0、CCR 字段 `0x1E` = 30。`0x00B4` 是标准模式、CCR 字段 `0xB4` = 180。表 41 的注：fPCLK1 至少 2 MHz 才能跑标准模式，至少 4 MHz 才能跑快速模式；要达到 400 kHz 这一档的上限，fPCLK1 得是 10 MHz 的整数倍。36 MHz 不是 10 MHz 的整数倍，表 42 仍然列出 400 kHz 这一行。表 42 的注 2：200 kHz 附近达成速率的容差是 ±5%，其余速率是 ±2%。四块写 CCR 的值，不把 400 kHz 写成保证的边沿。表 41：标准模式上升时间上限 1000 ns，快速模式 300 ns，Cb 上限 400 pF。正文把 `Rp(max) ≈ 300ns / Cb` 标成标准模式，这句作废，留在核心原理当估算，不进出处卡。硬件 I2C「可达 1 MHz」在这颗料上作废。表 5：第 42 脚 PB6 的默认复用含 I2C1_SCL，第 43 脚 PB7 的默认复用含 I2C1_SDA；重映射列里的 USART1_TX / USART1_RX 不是复位后的默认。第 45 脚 PB8、第 46 脚 PB9 是 I2C1 的重映射，不画进正常路径。
4. **第 10 章的半字账已经在附录 D，分类表却把 DMA2 写得像这颗料也有。** 附录 D：F103C8 只有 DMA1，7 条通道，没有 DMA2。USART1_TX = Channel 4，USART1_RX = Channel 5，ADC1 = Channel 1。长度 8 个半字、`CNDTR = 3`：已写 `8 − 3 = 5` 个采样，即 10 字节。半传输是 4 个采样、8 字节，不是 4 字节。F4 的 USART1_RX 是 DMA2 Stream 5、Channel 4，FIFO 是 4×32 位；这句在 C8 上作废，出处用已经冻结的 `rm0090`，不改那条对象。DS5319 Rev 20 第 2.3.13 节把这颗中密度写成一个 7 通道的 DMA。章首 `dma-circular.svg` 和 `dma-ring.gif` 是动画，印刷时看不出「把半字当成字节」。
5. **第 11 章的 1 秒已经在附录 D，图注却把独立看门狗说成喂早也复位。** 附录 D：`T = 预分频 / f_LSI × (Reload + 1)`。LSI 典型 40 kHz，手册范围大约 30–60 kHz。预分频 64 时名义计数频率 625 Hz。1 秒要把 Reload 写成 624；写成 625 会多一个计数。同一套预分频和重载，LSI 若是 60 kHz，秒数大约只有 30 kHz 时的一半。名义最长一档大约 26 s。40 kHz 算出来的秒数不是保证值。DS5319 Rev 20 表 25：fLSI 最小 30 kHz、典型 40 kHz、最大 60 kHz。第 2.3.14 节：备份寄存器是 10 个 16 位，共 20 字节；RTC 是 32 位计数器，20 位预分频，默认用 32.768 kHz 得到 1 秒时基。`f = f_RTCCLK / (PRL + 1)`，所以 PRL = 32767 才是 1 Hz；写成 32768 不是 1 Hz。正文「`BKP_DR1`~`BKP_DR10`（42 个，大容量）」把 10 个和 42 个写在同一格。42 个是大容量的句子，在 STM32F103C8T6 上作废。LSI 写成「≈ 32~40 kHz」和「±50%」与表 25 不一致；±20 ppm 和 ±50% 不进四块。负载电容的皮法，手册这一节没有印成 6 pF，四块不写皮法。第 2.3.15 节：IWDG 是 12 位递减加上 8 位预分频，时钟是独立的 40 kHz，Stop 和 Standby 里不停，调试时可以冻住。窗口看门狗是 7 位，时钟来自主时钟。章首图注写「独立看门狗……过早/过晚都触发复位」。独立看门狗只在减到 0 时复位。喂早也复位的是窗口看门狗。代码里 Reload = 4095 配上「4095/625 ≈ 6.55 s」少了一次 +1。`(4095 + 1) / 625 = 6.5536` s。四块的主账仍是 1 秒，不把 6.55 s 写成第二套规范。
6. **许可门与已有 id 保持原样。** 允许吸收的仍是 ST 手册里的事实（自己的话重写），以及 MIT、BSD-2-Clause、BSD-3-Clause、ISC、CC BY 4.0、CC BY 3.0、CC0。GPL、LGPL、CC BY-NC、CC BY-ND、Apache-2.0、保留所有权利、未写许可的材料只留链接。SSD1306、AT24C02、MPU6050 的厂商手册和 I2C 总线规范 UM10204 不在吸收名单里。`0x3C`、`0x78`、4.7 kΩ 沿用附录 D 与已有 `project-examples`，不新开屏厂 id。`sources` 只追加。已有 id 一个字段都不改，含 `rm0008`、`ds5319`、`rm0008-boot`、`rm0008-gpio`、`ds5319-gpio`、`pm0056`、`pm0056-nvic`、`project-examples`、`rm0090`。
7. **全 29 章最终都要加厚。** 本批只规格化文件 `01`、`07`、`10`、`11`。再下一批仍是 4 章，章号到那时再锁。本文件不预选文件 `12` 或别的号。

## 目标与非目标

### 目标

- 只把第 01、07、10、11 章加厚到和第 00、02、03、04、05、06、08、09 章相同的四块密度。中文和英文一起写完。
- 每章一张可印刷的静态主图：正常路径和失败路径都在图上，封装脚位、信号名和文档号是真的。另加一条短 GIF，只做网页和公众号辅图。
- 数字钉在已经冻结的 RM0008 Rev 21、DS5319 Rev 20、PM0075 印出的 RDP 键，以及附录 D 已有的格子上。第 01 章的无保护字节改成 `0xA5`，SWCLK 改到第 37 脚。第 07 章的 400 kHz 跟表 42 的 `0x801E` 和附录 D 的 `0x78`、4.7 kΩ 同一笔账。第 10 章的 5 个采样、10 字节跟附录 D 同一笔账。第 11 章的 1 秒跟附录 D 同一笔账：Reload = 624，不是 625。
- 新出处追加进两份 manifest 的 `sources`。章内坑卡使用 `#source-...`。`CREDITS.md` 第六节记下这一批改写吸收了什么。
- 实施合入时把整书从 1.2.2 升到 **1.2.3 · 2026-10-25**。中英文共用这个版本号和这个日期。这一批不打 tag，不创建 Release。
- 实施 PR 在 Book CI 变绿之后停下来等人复审。人接受之前不合入。

### 非目标

- 不加厚除 01、07、10、11 以外的任何章。已经加厚的 00、02、03、04、05、06、08、09 保持原样。
- 不重画 `sample-00-boot-state.svg`、`sample-03-gpio-led.svg`、`sample-06-uart-frame.svg`、`sample-08-spi-jedec.svg`、`sample-09-adc-sar.svg`。第 01 章只用旁注指向第 00 章的启动别名。第 07 章不把第 08 章的推挽片选写进来。第 10 章不把 21 µs 和逐次逼近写进来。第 11 章不把第 03 章的 LED 电流路径再画一遍。
- 不重选样本，不改 `docs/superpowers/plans/` 里已有的样本、Batch2、Batch3 锁定文件和来源清单。不改 `tools/scan_sample_chapters.py`。
- 不改总纲、Batch2 规格、Batch3 规格、观感规格、CONTENT_GUIDE 规格，也不改两份 `CONTENT_GUIDE.md`。
- 不实现 v1.2.2 或 v1.2.3 的 GitHub Release，也不打 `v1.2.2` 或 `v1.2.3` 的 tag。
- 不改 `stm32-book/build_html.py`。出版书签仍是现在的 44 条。不把新的二级标题收进书签。
- 不改附录 A 的既有契约，不改附录 D 三套账的算术，不手改 `stm32-book/book/E-参考资料.md` 或英文对应文件。附录 E 的卡片仍由 `sources` 生成。
- 不替换、不重画已有图。第 01 章留下 `boot-sequence.svg`、`project-structure.svg`。第 07 章留下 `i2c-transaction.svg`、`i2c-timing.gif`。第 10 章留下 `dma-circular.svg`、`dma-ring.gif`。第 11 章留下 `iwdg-window.svg`。新主图是加进去的。不改这 12 条已有 GIF 的像素，也不改 `iwdg-window.svg` 的像素。章内那句「过早/过晚都触发复位」改到窗口看门狗上，文件本身不重画。
- 不改 `assets/video/`，不新做讲解视频，不重写 `<!-- video: -->` 旁白。英文章里视频稿仍是中文的，这一批不动。不把厂商手册、官方插图或社区原文放进仓库。
- 不加图目录或表目录，不加第 30 章，不改 `docs/00`–`28` 的文件名。不改仓库根 `README.md` 里已经过时的「6 个教学光栅动画」那一句。
- 不新开可烧录工程。不改 `examples/gpio-blink/`、`examples/spl-f1-blink/`、`examples/i2c-oled/`、`examples/adc-dma/`。

## 来源与许可

四层用法和总纲、Batch2、Batch3 相同。

允许写进正文的，仍按这个顺序：

1. ST 的 RM、DS、PM：只吸收事实，用自己的话写，附文档号和可点击的入口。不粘贴段落，不描官方图。
2. MIT、BSD-2-Clause、BSD-3-Clause、ISC、CC BY 4.0、CC BY 3.0、CC0：可以改写教学要点。许可证不强制署名时，本书仍署名。
3. 其他许可证：只留链接。含 GPL、LGPL、CC BY-NC、CC BY-ND、Apache-2.0、保留所有权利、未写许可的帖子和视频。

权威数字以第 1 层和附录 D 已有格子为准。社区材料只支持「这个坑有人踩过」。帖子里的寄存器值，要在 RM/DS/PM 上重新钉住之后才能进「原理与边界」或「时序或状态」。钉不住的，出处卡的主张写成「经验线索，未升格为规范」，并且这一行不引入新的寄存器值。

SSD1306、AT24C02、MPU6050 的数据手册，以及 UM10204，不吸收句子。`0x3C` 和 `0x78` 已经在第 07 章罗盘、附录 D 和 `examples/i2c-oled` 里。MPU6050 的 `0x6B`、`0x18` 和魔法值 `0xA5A5` 留在核心原理。没有一份许可允许吸收的冻结手册时，这些值不进出处卡。F1 硬件 I2C 的勘误不新开 id。总线上补 9 个时钟的恢复留在核心原理，不进出处卡。

### 追加的来源 id

新 id 只追加在两份 `sources` 对象的末尾。已有 id 的标题、URL、snapshot、许可、scope 都不改。中英两份的 `url`、`snapshot`、`license`、`accessed` 用同一串字符；`title`、`authority`、`scope` 用对应语言。`accessed` 用 `2026-10-25`。章罗盘的 `sources` 数组在原有 id 之后追加新 id，不删除已有 id。

RM0008 的 PDF 与已有 `rm0008-boot` 相同。DS5319 的 PDF 与已有 `ds5319-gpio` 相同。PM0056 的 PDF 与已有 `pm0056-nvic` 相同。不另找一份修订。

| 新 id | 冻结点 | 用在 | 不复制 |
| --- | --- | --- | --- |
| `ds5319-swd` | DS5319 Rev 20，2025-07，表 5 的 LQFP48 列。第 1 脚 VBAT，第 7 脚 NRST，第 34 脚 PA13 = JTMS/SWDIO，第 35 脚 VSS_2，第 36 脚 VDD_2，第 37 脚 PA14 = JTCK/SWCLK，第 39 脚 PB3 复位后是 JTDO，重映射里才有 TRACESWO，第 44 脚 BOOT0。STM32F103x8 的闪存是 64 KB，SRAM 是 20 KB。xB 的 128 KB 闪存在 C8T6 上作废 | 第 01 章主图的脚位和容量。第 39 脚只写进边界，不进主图正常路径 | 不描图。不把第 35 脚写成 SWCLK。不把 SWO 说成 PA13 或 PA14。不改 `ds5319-gpio` |
| `pm0075-rdp` | PM0075。选项字节在 `0x1FFFF800`：低字节是 RDP，读允许的键是 `0xA5`。把 RDP 编程回 `0xA5` 来解除保护时，先整片擦除主闪存。USER 字节里 WDG_SW 为 0 表示硬件看门狗，为 1 表示软件看门狗。snapshot 写上 PDF 印出的 Rev 和年月 | 第 01 章的读保护。第 11 章只交叉引用 WDG_SW，不在第 01 章展开喂狗 | 不把 `0xAA` 写成这颗料的无保护键。不把 `0xCC` 的 Level 2 写进来。不粘贴选项字节表 |
| `pm0056-vector` | PM0056 Rev 7，2024-12。向量表第 0 项是 MSP 初值，第 1 项是 Reset。外设中断入口是 `VTOR + 4×(IRQn + 16)`。节号用印出「向量表」那一节；默认先对第 2.3.4 节，印出的标题不是向量表就改用印出的节号，主张不变 | 第 01 章的两字和 IRQ 入口 | 不改 `pm0056` 和 `pm0056-nvic`。不把 167 ns 写进这一章 |
| `ds5319-i2c` | DS5319 Rev 20 表 5、表 41、表 42。第 42 脚 PB6 默认复用含 I2C1_SCL，第 43 脚 PB7 默认复用含 I2C1_SDA。重映射列的 USART1 不是复位默认。第 45 脚 PB8、第 46 脚 PB9 是 I2C1 重映射。表 42：36 MHz、3.3 V、4.7 kΩ 下 400 kHz 对应 `0x801E`，100 kHz 对应 `0x00B4`。表 41：标准模式上升时间上限 1000 ns，快速模式 300 ns；fPCLK1 要是 10 MHz 的整数倍才能达到 400 kHz 上限。表 42 注 2：除 200 kHz 附近 ±5% 外，达成速率容差 ±2% | 第 07 章。CCR、上拉、脚位、1 MHz 作废 | 不描图 32。不吸收屏厂手册。不把 1 MHz 写进表 42 |
| `rm0008-i2c` | RM0008 Rev 21 第 26 章。7 位地址加 1 位 R/W。第 9 个时钟 SDA 被拉低是 ACK，保持高是 NACK。I2C1 在 APB1。快速模式且 DUTY = 0 时，高电平一个 CCR，低电平两个 CCR。`0x801E` 的低 12 位是 30 | 第 07 章。线上字节 `0x78` 与 `0x79`，以及 ACK | 不编 I2C 基址。印出的 CCR 位和 `0x801E` 对不上时，用印出的位，400 kHz 那一行仍是表 42 的 `0x801E` |
| `rm0008-dma` | RM0008 Rev 21 第 10 章。`CNDTR` 数的是数据项，不是字节。中密度请求：ADC1 是通道 1，USART1_TX 是通道 4，USART1_RX 是通道 5。循环模式在计数归零时重装。DMA 控制器是 AHB 主机 | 第 10 章。5 个采样、10 字节、半传输 8 字节 | 不把 21 µs 写进来。不编 DMA 基址。不改 `rm0090` |
| `ds5319-dma` | DS5319 Rev 20 第 2.3.13 节。中密度是一个 7 通道 DMA。大容量才另有 DMA2 | 第 10 章。这颗 C8 没有 DMA2 | 不把正文分类表里的「DMA2 有 5 通道」写成 C8 的能力 |
| `rm0008-wdg` | RM0008 Rev 21 第 17 章和第 18 章。IWDG：`T = 预分频 / f_LSI × (Reload + 1)`，预分频 64 且 f_LSI 按 40 kHz 时计数频率 625 Hz，Reload 624 是 1 秒，Reload 625 多一个计数。减到 0 才复位，喂早不复位。WWDG 是 7 位，时钟来自 APB1。PCLK1 = 36 MHz、预分频 8、计数初值 `0x7F` 时，超时是 `(1/36e6) × 4096 × 8 × 64 = 58.25` ms。计数器还大于窗口值时喂狗会复位 | 第 11 章的 1 秒和窗口 | 不把 40 kHz 的秒数写成保证值。不改附录 D 的 1 秒格子。调试冻住的位名只有手册印出来才写进 snapshot |
| `rm0008-rtc` | RM0008 Rev 21 第 16 章，以及备份域解锁所在的 PWR 章（`PWR_CR` 的 DBP）。RTC 时钟除以 `(PRL + 1)`。32.768 kHz 配 PRL = 32767 得到 1 Hz。PRL = 32768 不是 1 Hz。F1 的日历是 32 位计数器，不是 F4 的 BCD 寄存器 | 第 11 章的 1 Hz 时基 | 不把 F4 的写保护键 `0xCA`、`0x53` 写进来。不把 `TR`/`DR` 写成这颗料的日历寄存器 |
| `ds5319-rtc` | DS5319 Rev 20 表 25 与第 2.3.12、2.3.14、2.3.15 节，表 5。fLSI 是 30 / 40 / 60 kHz。备份寄存器 10 个 16 位，共 20 字节。默认时基是 32.768 kHz 得到 1 秒。IWDG 用独立 40 kHz，Stop 和 Standby 里不停，调试时可冻住。第 1 脚 VBAT，第 3 脚 PC14-OSC32_IN，第 4 脚 PC15-OSC32_OUT | 第 11 章主图的晶振脚、10 个备份寄存器、LSI 范围 | 不编负载电容的皮法。不把 ±20 ppm 或 ±50% 写进 snapshot。不改 `ds5319-gpio` 的 3 mA |

来源清单的 `absorb` 必须含上表十个 id。没有条件追加的第十一个 id。调试冻住的位名若印在 RM0008 里，写进已有的 `rm0008-wdg` snapshot，不新开 id。

`pm0075-rdp` 的 URL 用 ST 文档中心上文件名含 `pm0075` 的那一份编程手册。若实际下载地址的文件名是文档号 `CD00283419` 而不是 `pm0075-...`，实施时把 `url` 写成返回这份 PDF 的 `https://` 地址，主张仍是 `0xA5` 和整片擦除。PDF 里找不到 `0xA5` 这句时停下来，不另编一个键。

许可门若找不到 MIT、BSD 或 CC BY/CC0 的社区例程，来源清单里的社区列表就是空的。空列表不挡住加厚。不吸收未写许可的博客，不吸收 GPL 的 libopencm3，不吸收屏厂、EEPROM 厂或传感器厂的手册，不吸收 UM10204 的句子。

### 沿用、但不改写对象的 id

| 已有 id | 这一批怎么用 |
| --- | --- |
| `rm0008-boot` | 第 01 章交叉引用表 9。BOOT0=0 别名闪存；BOOT1=0 且 BOOT0=1 是 `0x1FFFF000`；BOOT1=1 且 BOOT0=1 才是 SRAM。不改这条对象 |
| `project-examples` | 第 07 章交叉引用：例程里的 DevAddress 是 `0x78`。不改这条对象 |
| `rm0090` | 第 10 章交叉引用：F4 的 USART1_RX 是 DMA2 Stream 5、Channel 4，FIFO 是 4 个 32 位字。这句在 C8 上作废。不改这条对象 |
| `rm0008-gpio`、`ds5319-gpio` | 不改。第 03 章的 PA13/PA14 信号名和 PC13 的 3 mA 仍只服务第 03 章。第 01 章的封装脚号走 `ds5319-swd` |
| `pm0056`、`pm0056-nvic` | 不改。167 ns 不进第 01 章 |
| `rm0008`、`ds5319` | 不改。新事实走上表的新 id |

出处卡的字段仍是现有附录 E 的一套：`title`、`authority`、`url`、`snapshot`、`accessed`、`license`、`scope`。`url` 必须是 `https://`。章内第四块每一行只有一个主张，并带一个 `#source-`。一行写清现象、原因、处理、链接、该来源允许支持的主张。

`CREDITS.md` 第六节现在有样本章、第 04 与第 06 章、第 02/05/08/09 章三个小节。这一批在该节下面加一个小节「第 01、07、10、11 章（v1.2.3）」，保留前面的表。新表只列作品名、许可证、用在哪、链接。不贴手册原文。同一文件顶部的静态框图从 14 张改为 18 张，光栅动画从 12 个改为 16 个。只有第 11 章拆出第二张 SVG 时，静态框图改为 19 张，并在实施 PR 里写明拆图原因。

## 锁定

章号按文件名前缀锁死：`01`、`07`、`10`、`11`。不再按「谁更薄」重选。不改成第 03 章或第 09 章，也不把已经加厚的章再开一遍。

实施开始时仍做一次核对扫描，只读这四章的中英八份。扫描确认两件事：四块标题还不存在；旧的「常见坑」标题还在。结果写到新文件 `docs/superpowers/plans/2026-10-25-batch4-01-07-10-11-lock.json`，带上运行时的 `git rev-parse HEAD`。不覆盖样本、Batch2 或 Batch3 的锁定文件。若扫描发现四块已经有人写过，停下来，不叠第二套标题。

来源清单写到 `docs/superpowers/plans/2026-10-25-batch4-01-07-10-11-source-list.json`，字段沿用 Batch3 清单：`chapters` 是 `["01", "07", "10", "11"]`，`absorb` 里每一条有 `license_class`、`url`、`do_not_copy`、`points`。`license_class` 只允许 `ST-facts-restated`、`MIT`、`BSD-2-Clause`、`BSD-3-Clause`、`ISC`、`CC BY 4.0`、`CC BY 3.0`、`CC0`。许可字符串里不得出现 `GPL`、`LGPL`、`CC BY-NC`、`CC BY-ND`、`All rights reserved`。清单可以先于 manifest 提交；登记以 manifest 为准。

## 章节加厚模板

四块插在 `<!-- /video: -->` 之后、学习目标之前，和第 03 章相同。标题不加表情符号，中英各出现一次：

| 块 | 中文标题 | 英文标题 | 这一块要写完的事 |
| --- | --- | --- | --- |
| 1 | `## 原理与边界` | `## Principle and boundary` | 结论钉在哪颗订货号、哪路时钟、哪一版手册；换系列时哪一句作废 |
| 2 | `## 关键插图` | `## Key figures` | 静态主图在前，图注带关键数字和文档号。短 GIF 跟在后面，图注标明辅图 |
| 3 | `## 时序或状态` | `## Timing or state` | 一张能算回去的表。时间或状态迁移和主图是同一笔账 |
| 4 | `## 坑与出处卡` | `## Pitfalls and source cards` | 旧坑表里钉得住的行挪到这里。每行一个 `#source-` |

保留学习目标、硬件与接线、代码实现、动手实验、相关资源，以及英文的对应标题。保留 `## 🧠 核心原理` 和英文 `## 🧠 Core ideas`。和四块或附录 D 冲突的数字，就地改成同一笔账，不保留两套说法。`## ⚠️ 常见坑与排查` 和英文 `## ⚠️ Pitfalls and troubleshooting` 删掉，不留空标题。

视频块、旁白和已有动画图留在原处。主图不放进 `<!-- video: -->` 块。代码仍按 `docs/CONTENT_GUIDE.md`：HAL，参数用宏。

中英的订货号、文档号、寄存器名、脚位和算式一致。英文可以更短，不能少一块，也不能少一个关键数字。

## 第 01 章写什么

订货号仍是 STM32F103C8T6，LQFP48。闪存和 SRAM 跟第 02 章同一笔：64 KB 从 `0x08000000` 起，20 KB 从 `0x20000000` 起。启动别名跟第 00 章同一笔，不另画一套 BOOT 表。

### 原理与边界

- **两根调试线。** 复位后的调试口是第 34 脚 PA13 = SWDIO，第 37 脚 PA14 = SWCLK。中间隔着第 35 脚 VSS_2 和第 36 脚 VDD_2。把第 35 脚当成 SWCLK 是主图的失败路径。第 7 脚 NRST 建议接，它不是第三根 SWD 信号。第 44 脚是 BOOT0。信号名 PA13/PA14 与第 03 章一致；封装脚号只在这一章展开。SYS Debug 选 Serial Wire。把它关掉之后，这两只脚变成普通 GPIO，下一次 SWD 连接失败。
- **两字。** BOOT0=0 时，CPU 从 `0x00000000` 读到的是闪存 `0x08000000` 的别名。第 0 个字是 MSP 初值，第 1 个字在 `0x00000004`，是 `Reset_Handler`。外设中断入口不是 `0x08000000 + 4×IRQn`，而是 `VTOR + 4×(IRQn + 16)`。`.isr_vector` 要用 `KEEP` 这件事留在核心原理。
- **启动失败。** BOOT1=0 且 BOOT0=1：CPU 仍读 `0x00000000`，取到的是系统存储器 `0x1FFFF000`，闪存里的程序还在，只是没有被取指。BOOT1=1 且 BOOT0=1 才从 SRAM `0x20000000` 启动。正文「BOOT0=1 从 SRAM 启动」改成这两行。不重画第 00 章那张图。
- **读保护。** 无保护是 RDP = `0xA5`，不是 `0xAA`。解除保护会整片擦除主闪存。`0xAA` 和 `0xCC` 在这颗料上作废。选项字节界面若只显示 Level 0，旁边仍写明写入的字节是 `0xA5`。
- **容量。** 这颗 C8 是 64 KB 闪存、20 KB SRAM。xB 的 128 KB 作废。链接脚本里的 `LENGTH = 64K` 和 `LENGTH = 20K` 跟这两句同一笔。
- **SWO。** 跟踪脚是第 39 脚 PB3，默认功能是 JTDO，重映射里才有 TRACESWO。它不是 PA13，也不是 PA14。ITM 打印留在核心原理，不进主图的正常路径。第 17 章的 `debug-swo.svg` 不重画。

Keil、CubeIDE、PlatformIO、CLion 的授权和菜单路径留在核心原理，不进四块，不进新来源的 scope。OpenOCD 的 `unlock` 命令行留在核心原理。

### 关键插图

主图文件 `assets/diagrams/sample-01-swd-vectors.svg`，由 `tools/gen_sample_figures.py` 追加一个函数生成，调用 `_credit()`，不调用 `Svg.footer()`。

图上是一次下载之后的取指：

- 脚位：第 34 脚 PA13 = SWDIO，第 37 脚 PA14 = SWCLK。第 35 脚标成 VSS_2，第 36 脚标成 VDD_2。第 44 脚 BOOT0 = 0。程序写入 `0x08000000`。
- **正常路径。** `0x00000000` 别名到这块闪存。第 0 字是 MSP，第 1 字是 `Reset_Handler`，然后才到 `main`。
- **失败路径。** 同一对 PA13/PA14 被配成 GPIO（Debug 关掉）。下一次探针在这两只脚上连不上。
- **旁注。** 把第 35 脚当成 SWCLK 会接空。BOOT1=0 且 BOOT0=1 时取到 `0x1FFFF000`，不是 SRAM。RDP 写成 `0xAA` 不是这颗料的无保护。不把第 00 章的整张启动表再画一遍。不画 ST-Link 克隆器的丝印针号。

图注写「自绘」，带 DS5319 Rev 20 表 5、PM0056 的向量表、PM0075 的 `0xA5`。替代文本写出结论：SWCLK 在第 37 脚；BOOT0=0 时第 0 字是栈、第 1 字是复位；无保护字节是 `0xA5`。不写「示意图」。

`boot-sequence.svg` 留作辅图。关键插图写明：不播放它，脚号、两字和连不上的失败都在静态主图上。

### 时序或状态

一张表，从复位写到 `main`。至少包括：BOOT0=0，读 `0x00000000` 得到 MSP，读 `0x00000004` 得到 `Reset_Handler`，物理存储器是 `0x08000000` 起的 64 KB。失败行：Debug 关掉，第 34 脚和第 37 脚变成 GPIO，SWD 连接失败。另一失败行：BOOT1=0 且 BOOT0=1，别名到 `0x1FFFF000`。SRAM 行单独写明要两只 BOOT 都为 1。IRQ 行：入口是 `VTOR + 4×(IRQn + 16)`。容量行：C8 是 64 KB 闪存和 20 KB SRAM；128 KB 在这颗料上作废。

### 坑与出处卡

至少这些行：

| 现象 | 处理方向 | 链接 | 允许的主张 |
| --- | --- | --- | --- |
| 烧录一次后再也连不上 | 把 Debug 留在 Serial Wire，SWD 留在第 34 脚和第 37 脚 | `#source-ds5319-swd` | LQFP48 第 34 脚是 PA13/SWDIO，第 37 脚是 PA14/SWCLK。第 35 脚是 VSS_2 |
| 探针接在 PA13 旁边那只脚上，时钟没有 | 空开第 35、36 脚，时钟接到第 37 脚 | `#source-ds5319-swd` | 第 35 脚是 VSS_2，第 36 脚是 VDD_2，第 37 脚才是 SWCLK |
| BOOT0 拉高之后跑的不是闪存里的程序，也不是 SRAM | BOOT1=0 时这是系统存储器。要进 SRAM，两只 BOOT 都拉高 | `#source-rm0008-boot` | BOOT1=0 且 BOOT0=1 时别名到 `0x1FFFF000`。SRAM 启动还要 BOOT1=1 |
| 按 `AA` 解除读保护，片子仍保护着或擦除结果对不上 | 无保护键写成 `0xA5`。解除时主闪存会被整片擦掉 | `#source-pm0075-rdp` | RDP 为 `0xA5` 才允许读出。编程回 `0xA5` 会先整片擦除。`0xAA` 在这颗料上作废 |
| 向量表第 0 字被当成复位入口 | 第 0 字是 MSP，第 1 字才是 `Reset_Handler` | `#source-pm0056-vector` | 向量表第 0 项是栈初值，第 1 项是复位。IRQ 入口要先加上 16 个系统异常 |

工具链菜单、驱动和「No such file」留在核心原理。

### 短 GIF

辅图 `assets/gif/swd-fetch.gif`。内容是正常路径：SWD 写完闪存，CPU 读出 MSP 和 `Reset_Handler`，标出第 34 脚和第 37 脚。帧数不少于 3、不多于 12。GPIO 复用和 `0xAA` 只放在静态主图上。不替换 `boot-sequence.svg`。

## 第 07 章写什么

订货号仍是 STM32F103C8T6。I2C1 在 APB1，PCLK1 = 36 MHz，跟附录 D 的 APB1 格子同一笔。工作点整格照抄 DS5319 表 42：Rp = 4.7 kΩ，目标 400 kHz，`I2C_CCR = 0x801E`。地址整格照抄附录 D：7 位 `0x3C`，HAL 填 `0x78`。

### 原理与边界

- **两只脚。** 复位后的默认脚是第 42 脚 PB6 = I2C1_SCL，第 43 脚 PB7 = I2C1_SDA。两只脚都配成复用开漏，外面各接 4.7 kΩ 到 3.3 V。这不是第 08 章的推挽片选。重映射到第 45 脚 PB8、第 46 脚 PB9 不画进正常路径。表 5 的重映射列把 USART1_TX / USART1_RX 放在 PB6/PB7 上；那不是复位默认，和第 06 章同一笔。本图只画 I2C。两只脚不能同时充当 USART1。
- **地址字节。** 7 位 `0x3C` 的位型是 `0111100`。写方向的线上第一字节是 `0x3C << 1`，也就是 `0x78`。读方向是 `0x79`。HAL 的 DevAddress 填 `0x78`，不填 `0x3C`。把扫描器看到的 `0x3C` 原样送进 `HAL_I2C_Master_Transmit`，线上出去的是 `0x3C`，7 位地址变成 `0x1E`。这是主图的失败路径。例程里的宏已经是 `0x78`，链接 `project-examples`。
- **第 9 个时钟。** 接收方拉低 SDA 是 ACK。SDA 保持高是 NACK。地址不对时看到的是 NACK，不是「高电平表示答应了」。
- **重复起始。** `HAL_I2C_Mem_Read` 的顺序是 START、器件地址+写、寄存器地址、重复起始、器件地址+读、数据、STOP。先 `Master_Transmit` 再 `Master_Receive` 会在中间插入 STOP。这句留在时序表。
- **CCR。** `0x801E`：快速模式位置位，DUTY = 0，CCR 字段 = 30。PCLK1 = 36 MHz 时，一个 SCL 周期是 `3 × 30 / 36e6 = 2.5` µs，目标 400 kHz。100 kHz 那一行是 `0x00B4`，CCR 字段 = 180，标准模式，`36e6 / (2 × 180) = 100` kHz。36 MHz 不是 10 MHz 的整数倍，所以表 41 说这样到不了「400 kHz 上限」的那句条件；表 42 仍把 400 kHz 和 `0x801E` 印在 36 MHz 这一列。达成速率按表 42 注 2 留 ±2% 的容差，不把 400 kHz 写成保证的边沿。1 MHz 不在表 41、表 42 里，正文那句作废。
- **上拉。** 表 42 这一行的外部上拉是 4.7 kΩ。片内大约 30–50 kΩ 沿用附录 D 和第 03 章，不能代替这只电阻去跑 400 kHz。标准模式上升时间上限是 1000 ns，快速模式是 300 ns。`300ns / Cb` 那条估算不进四块。Cb 上限 400 pF 可以写进边界，不把它换成另一张皮法表。
- **开漏。** 配成开漏时，连到 VDD 的 PMOS 被关掉，管子还在。外部上拉仍然要有。

AT24C02 的 `0x50`、MPU6050 的 `0x68` 和它们的寄存器值留在核心原理，不进四块的规范主张。

### 关键插图

主图文件 `assets/diagrams/sample-07-i2c-addr.svg`。

图上是一次写地址：

- 脚位：第 42 脚 PB6 = SCL，第 43 脚 PB7 = SDA。两只 4.7 kΩ 接到 3.3 V。PCLK1 = 36 MHz。`I2C_CCR = 0x801E`。
- **正常路径。** START 之后线上第一字节是 `0x78`。第 9 个时钟 SDA 为低，ACK。目标速率标成 400 kHz，旁边注明表 42 的 ±2%，不标成保证值。
- **失败路径。** DevAddress 填了 `0x3C`。线上第一字节是 `0x3C`，从机不应答，第 9 个时钟 SDA 仍为高。
- **旁注。** 只有片内上拉、没有 4.7 kΩ 时，不把这张图画成 400 kHz 的正常路径。PB8/PB9 和 USART1 的重映射不画进正常路径。

图注写「自绘」，带 DS5319 Rev 20 表 42 和表 5、RM0008 Rev 21 第 26 章。替代文本写出结论：HAL 送出的写地址是 `0x78`；`0x801E` 是 36 MHz 下表 42 的 400 kHz 行；把 `0x3C` 原样送上总线时第 9 个时钟没有 ACK。不写「示意图」。

`i2c-transaction.svg` 和 `i2c-timing.gif` 留在原节，标成辅图。

### 时序或状态

一张表覆盖这一字节。列至少有：段、SCL、SDA、线上的字节。正常行：START 时 SCL 为高且 SDA 由高到低；随后 8 位是 `0x78`；第 9 个时钟 SDA 为低。失败行：8 位是 `0x3C`，第 9 个时钟 SDA 为高。读方向行：重复起始之后的地址字节是 `0x79`，中间没有 STOP。速率行：`0x801E` 目标 400 kHz，`0x00B4` 是 100 kHz，容差 ±2%。上拉行：外部 4.7 kΩ；只有片内上拉时不跑这一行 400 kHz。

### 坑与出处卡

至少这些行：

| 现象 | 处理方向 | 链接 | 允许的主张 |
| --- | --- | --- | --- |
| 扫描器看到 `0x3C`，HAL 却没有 ACK | DevAddress 填 `0x78`。读方向的线上字节是 `0x79` | `#source-rm0008-i2c` | 7 位地址左移 1 位再加读写位。`0x3C` 原样送出会变成 7 位地址 `0x1E` |
| 例程和手册对不上地址写法 | 例程的宏已经是 `0x78` | `#source-project-examples` | `examples/i2c-oled` 的器件地址是 `0x78`，由 `0x3C << 1` 得到 |
| 总线上拉只有片内电阻，400 kHz 超时 | 按表 42 外接 4.7 kΩ 到 3.3 V | `#source-ds5319-i2c` | 36 MHz、3.3 V 下 400 kHz 那一行的 Rp 是 4.7 kΩ。片内上下拉的千欧数沿用附录 D，不由这条来源重新规定 |
| SCL 比 400 kHz 偏一截 | 核对 `I2C_CCR` 是 `0x801E`，并留下 ±2% | `#source-ds5319-i2c` | 表 42 在 36 MHz 下把 400 kHz 印成 `0x801E`。36 MHz 不是 10 MHz 的整数倍，达成速率不是保证的 400 kHz 整 |
| 波形出现在 PB8/PB9，或和串口抢 PB6 | 复位默认是第 42 脚和第 43 脚，只开 I2C1 | `#source-ds5319-i2c` | 第 42 脚默认含 I2C1_SCL，第 43 脚默认含 I2C1_SDA。USART1 的重映射不是复位默认 |

`300ns / Cb`、1 MHz、9 个恢复时钟和传感器寄存器留在核心原理。1 MHz 若还留在核心原理的对比表里，旁边写明在 STM32F103C8T6 上作废。

### 短 GIF

辅图 `assets/gif/i2c-addr.gif`。内容是正常路径：START，线上移出 `0x78`，第 9 个时钟 ACK，标出 `0x801E` 和 4.7 kΩ。帧数不少于 3、不多于 12。`0x3C` 被原样送出和缺上拉只在静态主图上。不替换 `i2c-timing.gif`。

## 第 10 章写什么

订货号仍是 STM32F103C8T6。通道号和半字账整格照抄附录 D。不把第 09 章的 21 µs 搬进来。

### 原理与边界

- **只有 DMA1。** 这颗中密度有一个 DMA，7 条通道。分类表里「DMA2（5 通道，大容量）」在 STM32F103C8T6 上作废。F4 的 Stream 和 Channel 是另一本手册：USART1_RX 在 DMA2 Stream 5、Channel 4，FIFO 是 4 个 32 位字。把这组号写进 C8，计数器不动。
- **三项请求。** ADC1 = DMA1 通道 1。USART1_TX = DMA1 通道 4。USART1_RX = DMA1 通道 5。其余通道留在核心原理的映射表里；和 RM0008 第 10 章的表对不上的格子，按那张表改，不新编通道号。四块只主张附录 D 这三行。
- **半字。** 缓冲区 8 个半字，`CNDTR` 读回 3：已经写入 `8 − 3 = 5` 个采样，字节数是 `5 × 2 = 10`。半传输发生在 4 个采样，也就是 8 字节，不是 4 字节。把 `CNDTR` 当成剩余字节，会把「还剩 3」读成 3 字节。这是主图的失败路径。
- **循环。** 计数归零后硬件重装 `CNDTR`。`长度 − CNDTR` 不是累计进度。位置仍用回调里的 `Size` 和 `old_pos`，这句与附录 A 同一笔，不改附录 A。
- **总线。** F1 的 DMA 控制器是 AHB 主机，外设寄存器在 APB。F1 没有 D-Cache。H7 的 Cache 维护留在核心原理，不进这颗料的四块规范主张。
- **脚。** USART1_TX 仍是第 06 章的第 30 脚 PA9。本图只旁注通道号，不重画那一帧。ADC 的采样时间留在第 09 章。

内存到内存的示例若占用通道 1，核心原理里注明它和 ADC1 的请求抢同一条通道，不把它画成 USART1_TX 的正常路径。

### 关键插图

主图文件 `assets/diagrams/sample-10-dma-cndtr.svg`。

图上是半字缓冲区的一次读数：

- 控制器：只有 DMA1。USART1_TX 走通道 4。宽度是半字。缓冲区长度 8。
- **正常路径。** `CNDTR = 3`。已写 5 个采样，10 字节。半传输刻度标在第 4 个采样，8 字节。
- **失败路径。** 同一读数被当成字节：还剩 3 字节、已写 5 字节。后一半从错误的边界切开。
- **旁注。** 把 USART1_RX 配成 DMA2 Stream 5 时，这颗 C8 上没有这个控制器。不画第 09 章的采样电容。不画第 06 章的 8N1 帧；只写「TX 仍从第 30 脚 PA9 出去，通道是 4」。

图注写「自绘」，带 RM0008 Rev 21 第 10 章和 DS5319 Rev 20 第 2.3.13 节。替代文本写出结论：8 个半字且 `CNDTR` 为 3 时已写 5 个采样、10 字节；把剩余计数当成字节会切错。不写「示意图」。

`dma-circular.svg` 和 `dma-ring.gif` 留在原节，标成辅图。

### 时序或状态

一张表用这一个缓冲区。列至少有：长度、宽度、`CNDTR`、已写采样、已写字节。必须有的行：长度 8、半字、`CNDTR = 3`、已写 5、字节 10。半传输行：4 个采样、8 字节，不是 4 字节。失败行：把 `CNDTR` 当成字节。通道行：USART1_TX = DMA1 通道 4，USART1_RX = DMA1 通道 5，ADC1 = DMA1 通道 1。作废行：DMA2 Stream 5 在这颗料上没有计数器。循环行：归零后重装，`长度 − CNDTR` 不是累计。

### 坑与出处卡

至少这些行：

| 现象 | 处理方向 | 链接 | 允许的主张 |
| --- | --- | --- | --- |
| 半字数组后一半看起来像新数据 | 半传输按 4 个采样、8 字节处理 | `#source-rm0008-dma` | `CNDTR` 数的是数据项。8 个半字里已写 5 个是 10 字节。半传输不是 4 字节 |
| `CNDTR` 读回 3，字节数却对不上 | 先减采样个数，再乘 2 | `#source-rm0008-dma` | 剩余 3 个半字不是剩余 3 字节 |
| 配了 DMA2 Stream 5，C8 上不动 | USART1_RX 改用 DMA1 通道 5 | `#source-ds5319-dma` | 这颗中密度只有一个 7 通道的 DMA1。DMA2 在 C8 上作废 |
| 对照 F4 例程时通道号能对上，板上不对 | F4 那一组号留在 F4 | `#source-rm0090` | F4 的 USART1_RX 是 DMA2 Stream 5、Channel 4。FIFO 是 4 个 32 位字。这条不证明 C8 有 DMA2 |
| 循环模式下进度越算越大 | 不要用 `长度 − CNDTR` 当累计 | `#source-rm0008-dma` | 计数归零后硬件重装。进度用回调里的写位置 |

Cache、FIFO 阈值和局部变量缓冲区留在核心原理。局部变量那一行不引入新的通道号。

### 短 GIF

辅图 `assets/gif/dma-cndtr.gif`。内容是正常路径：8 个半字的缓冲区里 `CNDTR` 减到 3，标出已写 5 个采样、10 字节。帧数不少于 3、不多于 12。把剩余计数当成字节只在静态主图上。不替换 `dma-ring.gif`。

## 第 11 章写什么

订货号仍是 STM32F103C8T6。1 秒整格照抄附录 D：预分频 64，Reload = 624，LSI 按典型 40 kHz 得到 625 Hz。LSI 的范围用表 25 的 30 / 40 / 60 kHz，不把 40 kHz 写成保证值。

### 原理与边界

- **1 秒。** `T = 64 / 40000 × (624 + 1) = 1` s。Reload 写成 625 时，`(625 + 1) / 625` 多一个计数。同一套预分频和重载：LSI = 30 kHz 时 `64 / 30000 × 625 = 4/3` s；LSI = 60 kHz 时 `64 / 60000 × 625 = 2/3` s，正是 30 kHz 那一档的一半。附录 D 写「大约一半」，因为 30 kHz 和 60 kHz 是手册范围的两端，不是每颗料的实测。最长一档大约 26 s 这句沿用附录 D，不另编一个保证的最大值。独立看门狗只在减到 0 时复位。喂早不复位。
- **窗口看门狗。** 喂早和喂晚都会复位。PCLK1 = 36 MHz，预分频 8，计数初值 `0x7F`：超时 `(1/36e6) × 4096 × 8 × 64 = 58.25` ms。窗口值 `0x50` 时，计数器还大于 `0x50` 就喂狗，会立刻复位。这是旁注，不是 IWDG 的主波形。章首动画的图注从「独立看门狗过早/过晚都复位」改成：辅图；独立看门狗只惩罚喂晚；喂早也复位的是窗口看门狗。不重画 `iwdg-window.svg`。
- **代码里的 4095。** 若片段留下 Reload = 4095，超时写成 `(4095 + 1) / 625 = 6.5536` s，不写成 `4095/625`。动手实验里的「约 6.5 s」可以留下，不进四块。主图只画 624 这一秒。
- **RTC 时基。** LSE 是 32.768 kHz，从第 3 脚 PC14-OSC32_IN 和第 4 脚 PC15-OSC32_OUT 进来。PRL = 32767 时 `(32767 + 1)` 把 32768 Hz 分成 1 Hz。PRL = 32768 不是 1 Hz。这是 RTC 的失败路径。LSI 典型 40 kHz，用整数 PRL 得不到跨 30–60 kHz 仍成立的 1 Hz。备份域由第 1 脚 VBAT 在主电源消失后续电。写之前打开 PWR 与 BKP 时钟，并置 `PWR_CR` 的 DBP。
- **10 个寄存器。** 这颗中密度是 10 个 16 位备份数据寄存器，共 20 字节。42 个是大容量的句子，在 C8 上作废。F4 的 20 个 32 位备份寄存器和 BCD 的 `TR`/`DR` 在这颗料上作废。日历由软件从 32 位秒计数换算。魔法值 `0xA5A5` 留在代码里，不进出处卡。
- **低功耗和调试。** IWDG 在 Stop 和 Standby 里继续计数。调试时可以冻住计数器，沿用章内的 `__HAL_DBGMCU_FREEZE_IWDG()`。位名只有 RM0008 印出来才写进 `rm0008-wdg` 的 snapshot。没印出来，四块只写「调试时可以冻住」，不编位号。`WDG_SW = 0` 时上电就由硬件看门狗接管，软件关不掉；为 1 时是软件看门狗。这句链接 `pm0075-rdp`，不在第 01 章展开。
- **皮法。** 四块不写 6 pF，也不写 ±20 ppm 和 ±50%。硬件节里的负载电容改成「按晶振手册选择」，不写成 DS5319 的数。PC13 若还当心跳灯，沿用第 03 章：只能灌电流，写 0 才亮，不重画那张 LED 图。LSE 用着第 3 脚和第 4 脚时，这两只脚不再当 GPIO。

### 关键插图

主图文件 `assets/diagrams/sample-11-iwdg-1s.svg`。

图上是 IWDG 的 1 秒，角上带一条备份域：

- 计数：LSI 典型 40 kHz，范围 30–60 kHz。预分频 64，计数频率 625 Hz。Reload = 624。在减到 0 之前喂狗，间隔 1 秒，这是典型值下的账，不是保证值。
- **正常路径。** 计数器还大于 0 时喂狗，不复位。图上标出这一次喂狗发生在超时之前，用来表明喂早对 IWDG 不是复位条件。
- **失败路径。** 同一条计数减到 0，没有喂狗，复位。旁注：Reload 写成 625 会多一个计数。
- **备份域条。** 第 1 脚 VBAT，第 3 脚 PC14，第 4 脚 PC15，32.768 kHz，PRL = 32767，10 个 16 位寄存器。失败刻度：PRL = 32768 不是 1 Hz；42 个备份寄存器在这颗料上作废。
- **旁注。** 窗口看门狗在计数器大于 `0x50` 时喂狗会复位，超时尺度是 58.25 ms，不和 IWDG 的 1 秒画成同一种狗。不画负载电容的皮法。不画 PC13 的 LED。

图注写「自绘」，带 DS5319 Rev 20 表 25、第 2.3.14 节和第 2.3.15 节，以及 RM0008 Rev 21 第 17 章。替代文本写出结论：Reload 624 在 40 kHz 典型值下是 1 秒；减到 0 才复位；LSE 要 PRL = 32767 才是 1 Hz。不写「示意图」。

`iwdg-window.svg` 留作辅图。关键插图写明：不播放它；喂早也复位的那一条属于窗口看门狗，已经改在图注里，不在这张静态主图上冒充 IWDG。

放不下 60 KB 时，把备份域条拆到 `assets/diagrams/sample-11-rtc-prescaler.svg`。关键插图的第一张仍是 `sample-11-iwdg-1s.svg`。拆开的两张都用 `_credit()`，都不调用 `Svg.footer()`。

### 时序或状态

一张表用附录 D 的 1 秒。列至少有：预分频、f_LSI、Reload、`(Reload + 1)`、时间、复位与否。必须有的行：64、40 kHz、624、625、1 s、减到 0 才复位。失败行：Reload = 625，多一个计数。范围行：30 kHz 是 4/3 s，60 kHz 是 2/3 s，都不是保证值。RTC 行：32768 Hz、PRL = 32767、1 Hz；PRL = 32768 不是 1 Hz。备份寄存器行：10 个 16 位，20 字节；42 个作废。WWDG 行：36 MHz、预分频 8、初值 `0x7F`、58.25 ms；计数器大于 `0x50` 时喂狗复位。4095 那一档若出现，只作为 `(4096 / 625) = 6.5536` s 的对照，不取代 624。

### 坑与出处卡

至少这些行：

| 现象 | 处理方向 | 链接 | 允许的主张 |
| --- | --- | --- | --- |
| 按 40 kHz 算的 1 秒，板上偏短或偏长 | Reload 用 624，并按 30–60 kHz 留余量 | `#source-ds5319-rtc` | 表 25 的 fLSI 是 30 / 40 / 60 kHz。40 kHz 是典型值。这一秒不是保证值 |
| Reload 写成 625，超时比 1 秒多一拍 | 改成 624 | `#source-rm0008-wdg` | 预分频 64、40 kHz 时计数频率 625 Hz。时间用 `(Reload + 1)`。625 多一个计数 |
| 独立看门狗一喂就复位，像有窗口 | 喂早对 IWDG 是允许的。要窗口用 WWDG | `#source-rm0008-wdg` | IWDG 减到 0 才复位。WWDG 在计数器大于窗口值时喂狗也会复位。36 MHz 下 `0x7F` 与预分频 8 的超时是 58.25 ms |
| 主电源掉了日历归零 | 接上第 1 脚 VBAT，LSE 用第 3 脚和第 4 脚，PRL 写 32767 | `#source-ds5319-rtc` | 10 个 16 位备份寄存器由 VBAT 续电。默认 1 秒时基来自 32.768 kHz。42 个在这颗料上作废 |
| 预分频写成 32768，秒脉冲偏慢 | 改成 32767 | `#source-rm0008-rtc` | 分频比是 `(PRL + 1)`。32768 Hz 要写成 32767 才是 1 Hz |
| 断点停住以后自己复位 | 调试时冻住 IWDG | `#source-ds5319-rtc` | 第 2.3.15 节：调试时可以冻住独立看门狗的计数器。位名不在这条主张里，除非 `rm0008-wdg` 的 snapshot 已经写上印出的名字 |
| 选项字节把看门狗改成上电就跑，软件关不掉 | `WDG_SW` 为 0 是硬件看门狗，为 1 才是软件看门狗 | `#source-pm0075-rdp` | USER 字节的这一位：0 表示硬件看门狗，1 表示软件看门狗 |

6 pF、±20 ppm、`0xA5A5` 和 F4 的 `TR`/`DR` 不进出处卡。F4 日历作废这句话写在原理与边界里，由「这颗料是 32 位计数器、10 个 16 位寄存器」支持，不新开 F4 RTC 的 id。

### 短 GIF

辅图 `assets/gif/iwdg-1s.gif`。内容是正常路径：625 Hz 的计数在减到 0 之前被喂狗，标出 Reload = 624 和 40 kHz 典型值。帧数不少于 3、不多于 12。减到 0、Reload = 625 和窗口看门狗的早喂只在静态主图上。不替换 `iwdg-window.svg`。

## 插图标准

沿用总纲和 Batch3 的逼真、翔实、生动、可印刷、自绘。主图和短 GIF 分开。简化示意图可以留在章内当辅图，不能充当关键插图的主图。

静态主图：

- 用 `tools/svgkit.py`，生成脚本是 `tools/gen_sample_figures.py`。四章各一张，中英引用同一文件。中文路径 `../assets/diagrams/...`，英文路径 `../../assets/diagrams/...`。第 11 章只有在单张超过 60 KB、拆图之后才增加第二张 `sample-11-rtc-prescaler.svg`。
- 不调用 `Svg.footer()`。落款用脚本里已有的 `_credit()`：左侧是文档号，右侧是「自绘 · 静态 · CC BY 4.0」。
- 没有 `<animate`、`@keyframes`、`animation:`。图上同时有正常路径和失败路径。
- 替代文本写结论。图注写「自绘」，不写「实拍」「手册截图」「矢量动画」。
- 单张小于 60 KB。放不下就拆成主图加局部，每张仍争取小于 60 KB。拆开仍超过时，在实施 PR 里写出字节数和原因，不把图画回简笔，也不把 60 KB 改成仓库新默认值。
- 登记进 `assets/README.md` 第四节，和已有的 `sample-00` 到 `sample-09` 主图并列。第一节里 `iwdg-window.svg` 那一行的说明改成辅图：独立看门狗只惩罚喂晚，喂早也复位的是窗口看门狗。不重画这个文件。`gen_sample_figures.py` 那一行注释补上第 01、07、10、11 章。

短 GIF：

- 四条都走 `tools/gen_gifs.py`，加入 `BUILDERS`，这样 `tools/check_assets.py` 能逐像素对上重新生成的帧。GIF 上的字用 ASCII。
- 每条少于 500 KB，帧数见上面四节。图注写明它是网页和公众号辅图，印刷以静态主图为准。
- `gen_gifs.chrome()` 自带的页脚可以留在 GIF 里。那条页脚不是静态主图的 `Svg.footer()`。
- 不改已有 12 个 BUILDERS 的像素：`led-blink`、`pwm-breath`、`uart-bits`、`i2c-timing`、`dma-ring`、`sar-adc`、`nvic-preempt`、`uart-idle`、`clock-css`、`pwm-1khz`、`spi-jedec`、`adc-sample`。不重跑它们来换画面。
- `tools/svg2gif.py` 这一批不当成必经步骤，也不为了它去改 CI。`assets/README.md` 第五节把「上面 12 张 GIF」改成「上面 16 张 GIF」。

PDF 关掉动画之后，读者只看静态主图和图注，就能指出失败发生在哪一段。第 01 章是「第 35 脚被当成 SWCLK，或 PA13/PA14 被配成 GPIO」。第 07 章是「DevAddress 填了 `0x3C`，第 9 个时钟没有 ACK」。第 10 章是「半字的 `CNDTR` 被当成字节」。第 11 章是「Reload 写成 625，或多等一个计数才复位；IWDG 喂早不复位」。

## 工作流与 PR 节奏

### 本 PR（设计）

只新增 `docs/superpowers/specs/2026-10-25-classic-encyclopedia-batch4-01-07-10-11-design.md`。不改 `docs/01`、`docs/07`、`docs/10`、`docs/11` 和 `docs/en/` 的章节。不改 `stm32-book/`、`CREDITS.md`、`assets/`、`tools/`。不升版本，不打 tag，不发 Release。不新增 `docs/superpowers/plans/` 下的实施计划。本 PR 等人审阅规格后再合入，不在 CI 变绿后自动合。

### 实施 PR（下一轮，不在本 PR）

顺序固定：

1. **核对扫描。** 写出 `2026-10-25-batch4-01-07-10-11-lock.json`。章号保持 01、07、10、11。
2. **许可门。** 写出 `2026-10-25-batch4-01-07-10-11-source-list.json`。先有清单，再改正文。
3. **静态主图和短 GIF。** 先提交 SVG、GIF 和生成脚本，再写正文。主图不依赖 GIF。
4. **中英加厚。** 八份 Markdown 一起提交。文件 `02`、`03`、`04`、`05`、`06`、`08`、`09` 的 diff 为空。
5. **登记。** 新来源追加进两份 manifest。更新这四章罗盘的来源数组。`CREDITS.md` 第六节增加 v1.2.3 小节，并把静态框图改为 18 张、光栅动画改为 16 个。若拆出 `sample-11-rtc-prescaler.svg`，静态框图改为 19 张。`revisions.json` 在条目最前加上 1.2.3，日期写死 `2026-10-25`。两份 manifest 的 `version` 改为 `1.2.3`，`date` 改为 `2026-10-25`。`stm32-book/README.md` 的当前版本句改为 **v1.2.3 · 2026-10-25**。发布一节里的 tag 名改成 `v1.2.3`，并在现有「也不要把 1.2.1 的产物标成 1.2.2」之后加上「也不要把 1.2.2 的产物标成 1.2.3」。这一步仍不创建 tag，也不创建 Release。修订说明只写这四章加厚了什么，用文件名前缀，不写尚未做的章。中英各两句，例如：第 01 章写上 SWD 在第 34 脚 PA13 和第 37 脚 PA14，读保护解除写 `0xA5`，BOOT0=1 且 BOOT1=0 进的是系统存储器。第 07 章写上 `0x3C` 在 HAL 里是 `0x78`，表 42 的 400 kHz 行是 `0x801E` 和 4.7 kΩ。第 10 章写上只有 DMA1，8 个半字且 `CNDTR` 为 3 时已写 5 个采样、10 字节。第 11 章写上预分频 64、Reload 624 在 40 kHz 典型值下是 1 秒，LSI 是 30–60 kHz，备份寄存器是 10 个。英文用同样的事实。
6. **测试。** 新增 `stm32-book/tests/test_batch4_chapters.py` 和 `stm32-book/tests/test_batch4_sources.py`，照着 Batch3 测试检查四块、共享数字、主图禁词和许可门。不放宽 `test_sample_chapters.py`、`test_batch2_chapters.py` 和 `test_batch3_chapters.py`。`test_build.py` 里当前版本从 `1.2.2` 改为 `1.2.3`：`assert_version_history_and_index` 的元组在 `1.2.2` 之前加上 `1.2.3`；修订列表以 `1.2.3` 起头；两份整书 HTML 的 `<strong>v1.2.3</strong>`。`test_visual_polish_version_is_1_2_0` 改为核对当前条目是 1.2.3，日期是 2026-10-25。现在对 `entries[0]` 的 1.2.2 两句改去核对 `entries[1]`；现在对 `entries[1]` 的 1.2.1 指南两句改去核对 `entries[2]`；现在对 `entries[2]` 的 1.2.0 两句改去核对 `entries[3]`。README 的断言改成当前版本句、`版本号已经是 1.2.3`、`也不要把 1.2.2 的产物标成 1.2.3` 和 `打 tag \`v1.2.3\``。不删 `0x271`、`167 ns`、账本名和出版书签长度为 44 的断言。不新增读取 `CONTENT_GUIDE.md` 的测试。
7. **CI 变绿之后停下来等人复审。** 复审对象是构建出的中英 HTML 里的这四章。人接受之前不合入，也不开下一批章。Book CI 变绿不等于可以自动 squash 合入。

实施 PR 的 diff 可以碰这四章中英正文、两份 manifest 的新 `sources` 和这四章罗盘、新图与生成脚本、`assets/README.md`、`CREDITS.md`、版本与修订、新的锁定文件和来源清单、新测试，以及 `test_build.py` 里的版本字符串。不碰其余章的正文，不改 `build_html.py`。

## 验收

### 本设计 PR

- 相对基线 `205fba7`，只新增 `docs/superpowers/specs/2026-10-25-classic-encyclopedia-batch4-01-07-10-11-design.md`。
- 章节、`stm32-book/`、资产、工具和 `CREDITS.md` 与基线 `205fba7` 相同。
- 没有新的 SVG 或 GIF，版本号仍是 1.2.2。没有实施计划文件。

### 实施 PR

- 中文四章各有且仅有一次：`## 原理与边界`、`## 关键插图`、`## 时序或状态`、`## 坑与出处卡`。英文对应四个标题同样各一次。
- 四章都不再有 `## ⚠️ 常见坑与排查` 或 `## ⚠️ Pitfalls and troubleshooting`。
- 每章关键插图的第一张图是对应的静态 SVG。图上能看出正常路径和失败路径。GIF 不是这一节唯一的图。
- 中英都有这些数字，而且彼此一致：
  - 第 01 章：第 34 脚、`PA13`、第 35 脚、`VSS_2`、第 37 脚、`PA14`、第 7 脚、`NRST`、第 44 脚、`BOOT0`、`0x08000000`、`0x00000000`、`0x00000004`、`0x1FFFF000`、`0xA5`、`64`、`20`。四块里不再把无保护写成 `0xAA`，也不再把「BOOT0=1」单独说成 SRAM 启动。
  - 第 07 章：`0x3C`、`0x78`、`0x79`、`0x801E`、`30`、`0x00B4`、`180`、`400`、`4.7`、`36`、第 42 脚、`PB6`、第 43 脚、`PB7`、`1000` ns、`300` ns。四块可以写「1 MHz 在这颗料上作废」，不能把 1 MHz 列成工作点。四块不出现 `300ns / Cb`。
  - 第 10 章：`DMA1`、`7`、通道 `4`、通道 `5`、通道 `1`、`CNDTR`、`8`、`3`、`5`、`10`、半传输 `4` 个采样、`8` 字节。四块写明 C8 没有 DMA2。21 µs 不出现在这一章的四块里。
  - 第 11 章：`64`、`624`、`625`、`40`、`30`、`60`、`1` 秒、`32767`、`32768`、`10`、`20` 字节、第 1 脚、第 3 脚、第 4 脚、`58.25`、`0x7F`、`0x50`。四块写明 IWDG 喂早不复位，42 个备份寄存器在 C8 上作废，并且不出现 6 pF。
- 第 07 章、第 10 章、第 11 章引用附录 D 的格子时整格照抄，不改附录 D 正文。第 01 章引用第 00 章的启动别名时不改第 00 章。
- 静态 SVG 小于 60 KB，不含动画标记，含「自绘」，不含「实拍」和「矢量动画」。四条新 GIF 小于 500 KB，并且在 `BUILDERS` 里。已有 12 条 GIF 的像素与基线相同。`iwdg-window.svg` 的字节与基线相同。
- 新 `#source-` 都能在构建出的 HTML 里找到 `id="source-..."`。已有 `rm0008`、`ds5319`、`rm0008-boot`、`rm0008-gpio`、`ds5319-gpio`、`pm0056`、`pm0056-nvic`、`project-examples`、`rm0090` 的对象与基线逐字段相同。
- 附录 D 三套账和附录 A 的正文 diff 为空。`test_build.py` 对 `0x271`、`167 ns` 和出版书签条数的断言仍在。
- 除这四章的中英八份以外，`docs/` 章节正文 diff 为空。`build_html.py` 的 diff 为空。
- 下面三条通过；改了生成脚本时再跑第四条：

```bash
python3 -m unittest discover stm32-book/tests -v
python3 stm32-book/build_html.py --check
python3 stm32-book/build_html.py --lang en --check
python3 tools/check_assets.py
```

- 没有 tag，没有 Release。章号显示仍是文件名前缀加 1。人复审之前，实施 PR 保持打开。

## 未决问题

没有会挡住实施的未决项。下面几项按此处的默认执行，复审时可以改口，不需要再写一版设计才开工：

1. **向量表节号。** 默认先对 PM0056 Rev 7 第 2.3.4 节。这一节的标题若不是向量表，snapshot 改用印出「第 0 项是 MSP、第 1 项是 Reset」的那一节，主张不变。
2. **PM0075 的 URL 和修订。** 用返回这份编程手册的 `https://` 地址。snapshot 写印出的 Rev 和年月。PDF 里没有 `0xA5` 和整片擦除这句时停下来，不另编键。
3. **I2C 的 CCR 位。** 默认 `0x801E` 是快速模式、DUTY = 0、字段值 30，与表 42 的 400 kHz 行一致。第 26 章印出的位不同时，用印出的位，表 42 的寄存器值仍是 `0x801E`，并在实施 PR 说明里写明差异。不编基址。
4. **调试冻住的位名。** 默认四块只写「可以冻住」，链接 `ds5319-rtc`。RM0008 印出位名时，把名字补进 `rm0008-wdg` 的 snapshot，并在坑卡那一行的主张里加上这个名字。不新开 id，也不编一个没印出来的位号。
5. **主图体积。** 先拆图。第 11 章的第二张只允许叫 `sample-11-rtc-prescaler.svg`。拆开仍超过 60 KB 时在实施 PR 里说明，不降低画法标准。
6. **图目录。** 这一批不加。
7. **下一批章号。** 仍是 4 章，到下一次设计再锁。本文件不预选 `12`。
8. **第 42 脚和第 16 脚的旧账。** 第 07 章主图主张 I2C1。第 06 章已经主张 USART1 不在 PB6/PB7。第 05 章和第 08 章已经把第 16 脚分开。这一批不把这些功能画成同时有效。

## 英文提要

Thicken only chapter files 01 (development setup), 07 (I2C), 10 (DMA), and 11 (RTC and the watchdogs), in Chinese and English, on top of v1.2.2 (`205fba7`, PR #32). Chapters 00, 02, 03, 04, 05, 06, 08, and 09 are already thick. Do not retitle this batch as GPIO or ADC. Use the same four sections as those chapters. Each chapter gets one printable static SVG from `gen_sample_figures.py`, with a normal path and a failure path, and no `Svg.footer()`. Chapter 01 draws SWDIO on LQFP48 pin 34 PA13 and SWCLK on pin 37 PA14, with pin 35 as VSS_2. The failure is those two pins reused as GPIO, or pin 35 counted as SWCLK. Readout protection level 0 on this part is the option byte `0xA5`, and programming it back mass-erases main Flash. `0xAA` is void. BOOT0=1 with BOOT1=0 aliases system memory at `0x1FFFF000`, not SRAM. Chapter 07 draws I2C1 on pins 42 and 43. HAL's DevAddress for the 7-bit value `0x3C` is `0x78`; sending `0x3C` on the wire is the failure, with SDA still high on the 9th clock. DS5319 Table 42 at 36 MHz and 4.7 kΩ lists 400 kHz as `I2C_CCR = 0x801E`. 1 MHz is void on STM32F103C8T6. Chapter 10 draws an 8-half-word buffer with `CNDTR = 3`: 5 samples, 10 bytes. Treating the count as bytes is the failure. This part has only DMA1. Chapter 11 draws the independent watchdog at a typical 40 kHz: prescaler 64 and Reload 624 are 1 second, and the counter resets only if it reaches 0. Reload 625 is one extra count. LSI spans 30–60 kHz, so that second is not a guarantee. The RTC strip uses LSE at 32.768 kHz with PRL 32767, ten 16-bit backup registers, and VBAT on pin 1. One short GIF per chapter is auxiliary only. The existing 12 GIF builders and `iwdg-window.svg` stay as they are. Register new sources by appending ids. Bump the book to 1.2.3 on 2026-10-25 during implementation, do not tag or release, and stop for human review before squash-merge. This design PR only adds this file.

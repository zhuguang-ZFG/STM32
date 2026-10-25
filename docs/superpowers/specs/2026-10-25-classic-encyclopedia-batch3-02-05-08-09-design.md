# 第 02、05、08、09 章加厚设计

日期：2026-10-25  
状态：已批准，待第 02、05、08、09 章实施  
基线：`main` 上的整书 **v1.2.1**（`b2a4f267f58ba42bd9749e94d9f8c2bac7cac118`，PR #29，2026-10-25）  
上一份设计：[2026-10-25-content-guide-four-blocks-1.2.1-design.md](2026-10-25-content-guide-four-blocks-1.2.1-design.md)（PR #28）。四块模板来自 [2026-10-25-classic-encyclopedia-thicken-design.md](2026-10-25-classic-encyclopedia-thicken-design.md)（PR #18）。Batch2 规格是 [2026-10-25-classic-encyclopedia-batch2-04-06-design.md](2026-10-25-classic-encyclopedia-batch2-04-06-design.md)（PR #22）。  
本文件只记录这一批的设计。它不改章节正文，不画新图，不改 `stm32-book/` 构建，不升版本号，不打 tag，不发布 Release，不写实施计划。

同一条设计 PR（#30）原先把这一批写成文件 `01`、`02`、`05`、`07`。用户按主题改成下面四章之后，规格就地换成这一份。旧文件名 `2026-10-25-classic-encyclopedia-batch3-01-02-05-07-design.md` 删除。开发环境（文件 `01`）和 I2C（文件 `07`）不进入本批。

## 背景

v1.2.1 已经把大典四块写进两份 `CONTENT_GUIDE`。已经按这个骨架加厚的是第 00、03、04、06 章。这一批只加厚另外四章，中文和英文一起写：

| 文件前缀 | 中文 | 英文 | 这一章在讲 |
| --- | --- | --- | --- |
| `02` | `docs/02-芯片选型与存储器时钟.md` | `docs/en/02-part-and-clock.md` | 订货号、存储器映射、时钟树 |
| `05` | `docs/05-定时器与PWM.md` | `docs/en/05-timer-pwm.md` | 时基、PWM、输入捕获 |
| `08` | `docs/08-SPI总线.md` | `docs/en/08-spi.md` | 模式、分频、全双工、片选 |
| `09` | `docs/09-ADC与DAC.md` | `docs/en/09-adc-dac.md` | 采样保持、逐次逼近、参考与 DAC 边界 |

读者看到的章号仍是文件名前缀加 1：文件 `02` 在书里是第 3 章，`05` 是第 6 章，`08` 是第 9 章，`09` 是第 10 章。源文件的一级标题继续带 `02`、`05`、`08`、`09`。这一批不改这个加 1。

GPIO 的封装和电流路径已经在第 03 章（`sample-03-gpio-led.svg`，LQFP48 第 10 脚 PA0、第 2 脚 PC13，270 Ω 与注 5 的 3 mA）。I2C 的地址和 4.7 kΩ 已经在第 07 章和附录 D。这两章不在本批。第 09 章若把 PA0 画成 ADC12_IN0，要写明它和第 03 章的点灯电流不能同时占这只脚，并且不重画那张 LED 图。第 05 章和第 08 章都要提到 LQFP48 第 16 脚 PA6：一张图画 TIM3_CH1，另一张图画 SPI1_MISO，两张图都不把两种功能画成同时有效。

对照 v1.2.1 核对过的事实：

1. **这四章还没有四块。** 第 00、03、04、06 章在 `<!-- /video: -->` 之后、学习目标之前，已经有 `## 原理与边界`、`## 关键插图`、`## 时序或状态`、`## 坑与出处卡`（英文是 `Principle and boundary`、`Key figures`、`Timing or state`、`Pitfalls and source cards`）。这四章仍从学习目标写起。中文坑还在 `## ⚠️ 常见坑与排查`，英文坑还在 `## ⚠️ Pitfalls and troubleshooting`，坑表没有 `#source-`。
2. **第 02 章把中密度的 CFGR 写成了互联型的节号。** 正文写「RM0008 第 8.3.2 节」。RM0008 Rev 21 里，中密度（含 STM32F103C8T6）的 `RCC_CFGR` 在第 7.3.2 节：`PLLMUL` 的 `0111` 是 ×9，`0000` 是 ×2，`USBPRE=0` 是 PLL÷1.5。第 8.3.2 节是互联型：`PLLMUL` 的 `000x` 保留，`USBPRE` 那位换成 `OTGFSPRE`。附录 D 的时钟账仍是 HSE 8 MHz ×9 = 72 MHz，APB1 36 MHz，APB2 72 MHz，定时器在预分频不为 1 时再 ×2。这张账不改。ADC 在这一章只保留分频格：÷6 得 12 MHz，÷4 得 18 MHz。21 µs 和逐次逼近留在第 09 章。
3. **第 05 章的 1 kHz 账已经在附录 D，分类表还把位宽写成 16/32。** 罗盘和附录 D：PSC = 71，ARR = 999，`72e6 / (72 × 1000) = 1000 Hz`。同一组数用 36 MHz 去除得到 500 Hz。PSC = 71、ARR = 999999 装不进 16 位；能装下的 1 秒是 PSC = 7199、ARR = 9999。这颗 F103 的 TIM2–TIM5 是 16 位。章内分类表写「通用 TIM2~TIM5，16/32 位」，没有写明 32 位在这颗料上作废。章首 `timer-pwm.svg` 和 `pwm-breath.gif` 是动画，印刷时看不出 500 Hz 那条失败。
4. **第 08 章的 9 MHz 和 JEDEC 三字节已经在罗盘和附录 D，主图仍是移位动画。** SPI1 在 APB2。72 MHz 下 `BR=010` 是 ÷8，SCK = 9 MHz；`BR=001` 是 ÷4，SCK = 18 MHz；`BR=000` 是 ÷2，SCK = 36 MHz。分频只有 2、4、8、16、32、64、128、256。Mode 0 是 CPOL = 0、CPHA = 0。JEDEC 命令 `0x9F`。`examples/spi-flash` 期待厂商 `0xEF`、类型 `0x40`、容量 `0x17`。页大小 256 字节。章首只有 `assets/animations/spi-transfer.svg`。还没有一张静态图同时画出 LQFP48 第 14–17 脚、Mode 0 的采样沿、命令字节和三字节 ID，以及一条失败（MOSI/MISO 对调，或片选一直为低，或 BR=000 跑到 36 MHz）。
5. **第 09 章的 21 µs 已经在附录 D，采样表却按 14 MHz 在算，并且把 ADC 个数写少了。** 附录 D：ADCCLK = 12 MHz，最长一档 `239.5 + 12.5 = 252` 个周期，`252 / 12e6 = 21 µs`。÷4 得到 18 MHz，越过 14 MHz。正文的源阻抗表把推荐采样档标成 ADCCLK = 14 MHz（1.5 周期约 107 ns，239.5 周期约 17 µs）。RM0008 自己的例子也是 14 MHz 下 `1.5 + 12.5 = 14` 个周期 = 1 µs；那是家族上限上的例子，不是这颗料 ÷6 之后的工作点。DS5319 对中密度（含 C8）写明都有两个 12 位 ADC。正文「F1 只有 1 个 ADC（大容量才有 ADC3）」在这颗料上不成立：C8 有 ADC1 和 ADC2，没有 ADC3，也没有 DAC。温度传感器的推荐采样时间是 17.1 µs，通道是 ADC1_IN16。章首关键图仍是 `adc-sar.svg` 和已经在 `BUILDERS` 里的 `sar-adc.gif`。
6. **许可门与已有 id 保持原样。** 允许吸收的仍是 ST 手册里的事实（自己的话重写），以及 MIT、BSD-2-Clause、BSD-3-Clause、ISC、CC BY 4.0、CC BY 3.0、CC0。GPL、LGPL、CC BY-NC、CC BY-ND、Apache-2.0、保留所有权利、未写许可的材料只留链接。W25Q64 和 ST7789 的厂商手册不在吸收名单里。`0xEF`、`0x40`、`0x17` 和页大小 256 沿用附录 D 与已有 `project-examples`，不新开 Winbond id。`sources` 只追加。已有 id 一个字段都不改，含 `rm0008`、`ds5319`、`rm0008-boot`、`rm0008-gpio`、`ds5319-gpio`、`project-examples`。
7. **观感设计里那句「Batch3 再加厚两章」到此被这一批的四章锁定替换。** 那份文件不回写。全 29 章最终都要加厚。本批只规格化这四章。再下一批仍是 4 章，章号到那时再锁。本文件不预选文件 `01` 或 `07`。

## 目标与非目标

### 目标

- 只把第 02、05、08、09 章加厚到和第 00、03、04、06 章相同的四块密度。中文和英文一起写完。
- 每章一张可印刷的静态主图：正常路径和失败路径都在图上，封装脚位、信号名和文档号是真的。另加一条短 GIF，只做网页和公众号辅图。
- 数字钉在已经冻结的 RM0008 Rev 21、DS5319 Rev 20 和附录 D 已有的格子上。第 02 章那句「第 8.3.2 节」改到中密度的第 7.3.2 节。第 05 章的 1 kHz 跟附录 D 同一笔账。第 08 章的 9 MHz、18 MHz 和 `0xEF4017` 跟罗盘、附录 D 同一笔账。第 09 章的 21 µs 跟附录 D 同一笔账，采样时间改按 12 MHz 来写。
- 新出处追加进两份 manifest 的 `sources`。章内坑卡使用 `#source-...`。`CREDITS.md` 第六节记下这一批改写吸收了什么。
- 实施合入时把整书从 1.2.1 升到 **1.2.2 · 2026-10-25**。中英文共用这个版本号和这个日期。这一批不打 tag，不创建 Release。
- 实施 PR 在 Book CI 变绿之后停下来等人复审。人接受之前不合入。

### 非目标

- 不加厚除 02、05、08、09 以外的任何章。已经加厚的 00、03、04、06 保持原样。开发环境（`01`）和 I2C（`07`）不进本批，也不改这两章的英文。
- 不把第 03 章的 LED 电流路径再画一遍。第 09 章只用一句话指出 PA0 不能同时点灯和采样。不把第 07 章的开漏、`0x78`、4.7 kΩ 写进第 08 章。片选是推挽 GPIO。
- 不把逐次逼近、采样档 1.5 到 239.5、21 µs 写进第 02 章。第 02 章的 ADC 句子停在分频：÷6 = 12 MHz，÷4 = 18 MHz，上限 14 MHz。
- 不重选样本，不改 `docs/superpowers/plans/` 里已有的样本和 Batch2 锁定文件、来源清单。不改 `tools/scan_sample_chapters.py`。
- 不改总纲、Batch2 规格、观感规格、CONTENT_GUIDE 规格，也不改两份 `CONTENT_GUIDE.md`。
- 不实现 v1.2.1 或 v1.2.2 的 GitHub Release，也不打 `v1.2.1` 或 `v1.2.2` 的 tag。
- 不改 `stm32-book/build_html.py`。出版书签仍是现在的 44 条。不把新的二级标题收进书签。
- 不改附录 A 的既有契约，不改附录 D 三套账的算术，不手改 `stm32-book/book/E-参考资料.md` 或英文对应文件。附录 E 的卡片仍由 `sources` 生成。
- 不替换、不重画已有图。第 02 章留下 `clock-tree.svg`、`memory-map.svg`、`peripheral-bus.svg`。第 05 章留下 `timer-pwm.svg`、`timer-modes.svg`、`pwm-breath.gif`。第 08 章留下 `spi-transfer.svg`。第 09 章留下 `adc-sar.svg` 和 `sar-adc.gif`。新主图是加进去的。不改 `sar-adc.gif` 的像素。
- 不改 `assets/video/`，不新做讲解视频。不把厂商手册、官方插图或社区原文放进仓库。
- 不加图目录或表目录，不加第 30 章，不改 `docs/00`–`28` 的文件名。
- 不新开可烧录工程。不改 `examples/timer-pwm/`、`examples/spi-flash/`、`examples/adc-dma/`。

## 来源与许可

四层用法和总纲、Batch2 相同。

允许写进正文的，仍按这个顺序：

1. ST 的 RM、DS、PM：只吸收事实，用自己的话写，附文档号和可点击的入口。不粘贴段落，不描官方图。
2. MIT、BSD-2-Clause、BSD-3-Clause、ISC、CC BY 4.0、CC BY 3.0、CC0：可以改写教学要点。许可证不强制署名时，本书仍署名。
3. 其他许可证：只留链接。含 GPL、LGPL、CC BY-NC、CC BY-ND、Apache-2.0、保留所有权利、未写许可的帖子和视频。

权威数字以第 1 层和附录 D 已有格子为准。社区材料只支持「这个坑有人踩过」。帖子里的寄存器值，要在 RM/DS 上重新钉住之后才能进「原理与边界」或「时序或状态」。钉不住的，出处卡的主张写成「经验线索，未升格为规范」，并且这一行不引入新的寄存器值。

W25Q64、ST7789 的数据手册，以及未写许可的接线帖，不吸收句子。JEDEC 的 `0x9F` 和三字节 `0xEF`、`0x40`、`0x17` 已经在第 08 章罗盘和附录 D 里，出处卡链接已有的 `project-examples`。ST7789 的初始化命令（`0x01`、`0x11`、`0x3A`、`0x36`、`0x29`）留在核心原理。没有一份许可允许吸收的冻结手册时，这些命令不进出处卡。

### 追加的来源 id

新 id 只追加在两份 `sources` 对象的末尾。已有 id 的标题、URL、snapshot、许可、scope 都不改。中英两份的 `url`、`snapshot`、`license`、`accessed` 用同一串字符；`title`、`authority`、`scope` 用对应语言。`accessed` 用 `2026-10-25`。章罗盘的 `sources` 数组在原有 id 之后追加新 id，不删除已有 id。

RM0008 的 PDF 与已有 `rm0008-boot` 相同。DS5319 的 PDF 与已有 `ds5319-gpio` 相同。不另找一份修订。

| 新 id | 冻结点 | 用在 | 不复制 |
| --- | --- | --- | --- |
| `rm0008-rcc` | RM0008 Rev 21，2021-02。中密度第 7.2 节时钟、第 7.2.7 节 CSS、第 7.3.2 节 `RCC_CFGR`；Flash 等待在第 3 章访问时间那一段（0 / 24 / 48 / 72 MHz 三档）。定时器 ×2 在第 7.2 节 | 第 02 章。72 MHz 树、CSS 回 HSI、第 8.3.2 节在这颗料上作废 | 不把互联型 `OTGFSPRE` 和 `PLLMUL` 的 `000x` 保留写进 C8。不改已有 `rm0008` |
| `ds5319-clock` | DS5319 Rev 20 图 8 与表 5。LQFP48 第 5 脚 PD0-OSC_IN，第 6 脚 PD1-OSC_OUT，第 29 脚 PA8（复用含 MCO） | 第 02 章主图的晶振脚和 MCO 脚 | 不描图。不编负载电容的皮法 |
| `rm0008-tim` | RM0008 Rev 21。通用定时器时基在第 15 章；`AFIO_MAPR` 的 `TIM3_REMAP=00` 是 CH1/PA6；高级定时器 `TIMx_BDTR` 偏移 `0x44`，位 15 是 MOE，复位值 `0x0000` | 第 05 章。1 kHz、16 位装不下 999999、TIM1 的 MOE | 不把 `DeadTime = 0x10` 换成一个新的纳秒。不改附录 D 的 1 kHz 格子 |
| `ds5319-tim` | DS5319 Rev 20 表 5。LQFP48 第 16 脚 PA6，默认复用含 TIM3_CH1（同一格也含 SPI1_MISO） | 第 05 章主图只主张 TIM3_CH1 | 不把 TIM3 重映射到 PB4 或 PC6 画进正常路径。不在这张图上同时主张 SPI |
| `rm0008-spi` | RM0008 Rev 21 第 25 章，`SPI_CR1` 在第 25.5.1 节。全双工在每个 SCK 上同时移出和移入。BR 编码以这一节印出的字段为准；本仓库已经冻结的工作点是附录 D：`010` = ÷8 = 9 MHz，`001` = ÷4 = 18 MHz，`000` = ÷2 = 36 MHz | 第 08 章。Mode 0、9 MHz、命令字节移出时 MISO 上的那一字节不是 ID | 不粘贴时序图。不编 SPI 基址。印出的 BR 编码和附录 D 不一致时，用印出的编码，9 MHz 仍是 ÷8，18 MHz 仍是 ÷4，并在实施 PR 里写明差异 |
| `ds5319-spi` | DS5319 Rev 20 图 8 与表 5。LQFP48 第 14 脚 PA4 = SPI1_NSS（亦为 USART2_CK、ADC12_IN4），第 15 脚 PA5 = SPI1_SCK，第 16 脚 PA6 = SPI1_MISO，第 17 脚 PA7 = SPI1_MOSI | 第 08 章主图 | 不把重映射到 PB3/PB4/PB5 画成复位后的默认脚。不把第 14 脚画成 DAC |
| `rm0008-adc` | RM0008 Rev 21 第 11 章。`Tconv =` 采样时间 `+ 12.5` 个周期。14 MHz、1.5 周期的例子是 1 µs，那是上限上的例子。温度传感器推荐采样时间 17.1 µs，接在 ADC1_IN16；VREFINT 接在 ADC1_IN17。`ADC_CR2` 的 TSVREFE 同时打开这两路；双 ADC 的器件上这一位只在 ADC1。ADC2 的通道 16 和 17 接到 VSS。第 11.4 节：置 `CAL` 之前 ADON 已经为 1 至少两个 ADC 时钟 | 第 09 章。12 MHz 下的 21 µs、17.1 µs、校准 | 不把 1 µs 写进这颗料的工作点。不把 F4 的 `TS_CAL1` / `VREFINT_CAL` 写进来。手册没印出的 R_ADC、C_ADC 不写进 snapshot |
| `ds5319-adc` | DS5319 Rev 20。中密度描述：器件都有两个 12 位 ADC。图 8：LQFP48 第 9 脚 VDDA，第 10 脚 PA0-WKUP = ADC12_IN0。表 5：第 14 脚 PA4 的模拟功能是 ADC12_IN4。高密度才另有 ADC3 和 DAC | 第 09 章。两只 ADC、没有 DAC、PA0 采样、PA4 不是 DAC_OUT | 不改 `ds5319-gpio`。不描图 8。不把第 10 脚的 3 mA LED 限额写进这条 scope |

来源清单的 `absorb` 必须含上表八个 id。没有条件追加的第九个 id。

`rm0008-adc` 的 snapshot 只有在 RM0008 Rev 21 印出 R_ADC 和 C_ADC 时才加上这两个常数。印出的数和正文现在的 1 kΩ、8 pF 不同，就用印出的数，并按印出的公式重算源阻抗表。两个常数没印出来，snapshot 就不写皮法和千欧，源阻抗表留在核心原理，标成本章现有的估算，不进出处卡的规范主张。无论哪一种，和 21 µs 写在同一格里的时间都按 ADCCLK = 12 MHz。

许可门若找不到 MIT、BSD 或 CC BY/CC0 的社区例程，来源清单里的社区列表就是空的。空列表不挡住加厚。不吸收未写许可的博客，也不吸收 GPL 的 libopencm3，也不吸收 Winbond 或显示屏厂商手册。

### 沿用、但不改写对象的 id

| 已有 id | 这一批怎么用 |
| --- | --- |
| `project-examples` | 第 08 章交叉引用：`0x9F` 之后的三字节是 `0xEF`、`0x40`、`0x17`，页 256 字节。例程把状态字节的位 0 当成忙。不改这条对象 |
| `ds5319-gpio` | 不改。第 03 章的第 10 脚 PA0、第 2 脚 PC13 仍只服务 LED。第 09 章另用 `ds5319-adc` 来主张同一只第 10 脚的 ADC12_IN0 |
| `rm0008-gpio` | 不改。SWD 脚不进这一批 |
| `rm0008`、`ds5319`、`pm0056`、`rm0008-boot` | 不改。新事实走上表的新 id |

出处卡的字段仍是现有附录 E 的一套：`title`、`authority`、`url`、`snapshot`、`accessed`、`license`、`scope`。`url` 必须是 `https://`。章内第四块每一行只有一个主张，并带一个 `#source-`。一行写清现象、原因、处理、链接、该来源允许支持的主张。

`CREDITS.md` 第六节现在有「样本章的改写吸收（v1.1.0）」和「第 04 章与第 06 章（v1.1.1）」。这一批在该节下面加一个小节「第 02、05、08、09 章（v1.2.2）」，保留前面的表。新表只列作品名、许可证、用在哪、链接。不贴手册原文。

## 锁定

章号按文件名前缀锁死：`02`、`05`、`08`、`09`。不再按「谁更薄」重选。不改成第 01 章或第 07 章，也不把已经加厚的第 03 章再开一遍。

实施开始时仍做一次核对扫描，只读这四章的中英八份。扫描确认两件事：四块标题还不存在；旧的「常见坑」标题还在。结果写到新文件 `docs/superpowers/plans/2026-10-25-batch3-02-05-08-09-lock.json`，带上运行时的 `git rev-parse HEAD`。不覆盖样本或 Batch2 的锁定文件。若扫描发现四块已经有人写过，停下来，不叠第二套标题。

来源清单写到 `docs/superpowers/plans/2026-10-25-batch3-02-05-08-09-source-list.json`，字段沿用 Batch2 清单：`chapters` 是 `["02", "05", "08", "09"]`，`absorb` 里每一条有 `license_class`、`url`、`do_not_copy`、`points`。`license_class` 只允许 `ST-facts-restated`、`MIT`、`BSD-2-Clause`、`BSD-3-Clause`、`ISC`、`CC BY 4.0`、`CC BY 3.0`、`CC0`。许可字符串里不得出现 `GPL`、`LGPL`、`CC BY-NC`、`CC BY-ND`、`All rights reserved`。清单可以先于 manifest 提交；登记以 manifest 为准。

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

## 第 02 章写什么

订货号仍是 STM32F103C8T6，LQFP48。时钟账整格照抄附录 D，不另算一套「大约 72 MHz」。

### 原理与边界

三句边界都要写完，并且写明哪一句在换到互联型或换电压档时作废。

- **中密度的树。** HSE 从第 5 脚 PD0-OSC_IN、第 6 脚 PD1-OSC_OUT 进来，8 MHz。`PLLXTPRE=0`（HSE 不预分频），`PLLSRC=1`（PLL 入口是 HSE），`PLLMUL=0111`（×9）。`8 × 9 = 72` MHz。`SW=10` 时 SYSCLK 用 PLL。HPRE 取不分频，HCLK = 72 MHz。PPRE1 = `100`（÷2），PCLK1 = 36 MHz，不得超过 36 MHz。PPRE2 取不分频，PCLK2 = 72 MHz。APB 预分频不是 1 时，挂在那条总线上的定时器时钟再 ×2，所以 TIM2–TIM7 仍是 72 MHz。TIM1 在 APB2，预分频为 1，不再 ×2。这些句子与附录 D 同一笔。
- **等待周期。** `FLASH_ACR` 偏移 `0x00`，基址 `0x40022000`。LATENCY 在 48 MHz 到 72 MHz 这一档是 `010`，也就是 2。0–24 MHz 是 0，24–48 MHz 是 1。电压档整格照抄附录 D：2.7–3.6 V。只把 PLL 改成 ×9、LATENCY 还留在 0，取指会错。这句是主图的失败路径。
- **USB 与 ADC 只保留分频格。** `USBPRE=0` 时 72 MHz 的 PLL 再 ÷1.5，得到 48 MHz。`USBPRE=1` 是不除，得到 72 MHz，不是 48 MHz。`ADCPRE=10` 是 PCLK2÷6，`72 / 6 = 12` MHz。`ADCPRE=01` 是 ÷4，得到 18 MHz，越过 RM0008 的 14 MHz 上限。21 µs、采样档和逐次逼近留在第 09 章，这一章不写。
- **CSS。** HSE 停振且 CSS 已开时，若 HSE 直接或经 PLL 当系统时钟，硬件改用 HSI，并关掉 HSE；HSE 若是 PLL 入口，PLL 也关掉。CSS 中断接在 NMI 上。NMI 里要写 `RCC_CIR` 的 CSSC，否则 NMI 会一直进来。同一事件还送到 TIM1 和 TIM8 的刹车输入。上电默认系统时钟是 HSI 8 MHz，不是 Cube 里填的 72 MHz。第 04 章只交叉引用「CSS 进 NMI」，不在这一章重画抢占。
- **MCO。** 第 29 脚 PA8 的复用含 MCO。`MCO=111` 送出 PLL÷2，也就是 36 MHz，低于手册写的 50 MHz I/O 上限。`MCO=100` 把 SYSCLK 送出去时，72 MHz 越过这句 50 MHz。正常路径画 36 MHz，失败旁注画「SYSCLK 直接送 MCO」。
- **互联型作废。** 第 8.3.2 节的 `OTGFSPRE`、`PLLMUL` 的 `000x` 保留、以及 ×6.5，在 STM32F103C8T6 上作废。正文现在的「RM0008 第 8.3.2 节」改成第 7.3.2 节。HSE bypass 只用于外部时钟，无源晶振不开 bypass。

系列对比表里的人民币价格留在核心原理，标明不是数据手册的数。不进四块，不进新来源的 scope。

### 关键插图

主图文件 `assets/diagrams/sample-02-clock-tree.svg`，由 `tools/gen_sample_figures.py` 追加一个函数生成，调用 `_credit()`，不调用 `Svg.footer()`。

图上是这一棵树，数字与附录 D 相同：

- 第 5 脚 PD0、第 6 脚 PD1，8 MHz，进 PLL ×9。旁边写 `PLLMUL=0111`、`PLLSRC=1`、`PLLXTPRE=0`。
- SYSCLK = HCLK = 72 MHz。PCLK1 = 36 MHz。PCLK2 = 72 MHz。TIM2–TIM7 的计数时钟 = 72 MHz。ADCCLK = 12 MHz。USBCLK = 48 MHz（`USBPRE=0`）。
- **正常路径。** LATENCY = 2。CSS 未触发。MCO 若画出，是 PA8 上的 PLL÷2 = 36 MHz。
- **失败路径。** 同一棵 ×9 的树，LATENCY 仍是 0，取指失败。另一条短标注：HSE 停振，CSS 把系统时钟切到 HSI 8 MHz，PLL 关掉，NMI 要写 CSSC。不把 18 MHz 的 ADC 和 72 MHz 的 MCO 再画成第三条完整的树；这两句放在旁注，并写明它们分别越过 14 MHz 和 50 MHz。

图注写「自绘」，带 RM0008 Rev 21 第 7.3.2 节和第 7.2.7 节、DS5319 Rev 20 图 8。替代文本写出结论：72 MHz 要 2 个 Flash 等待；HSE 停振后系统时钟回到 HSI 8 MHz。不写「示意图」。

`clock-tree.svg` 留作辅图。关键插图写明：不播放它，72 MHz、LATENCY 和 CSS 回 HSI 都在静态主图上。

### 时序或状态

一张表，从复位写到时钟稳定。至少包括：复位后 SWS 指向 HSI，8 MHz；HSE 就绪；PLL 按 `0111` 锁定在 72 MHz；写 LATENCY = 2；SW 切到 PLL；SWS 读回 PLL。失败行：LATENCY 仍为 0，状态是取指失败。CSS 行：HSE 失败，SYSCLK 回到 HSI 8 MHz，PLL 关闭，NMI 挂起，直到软件写 CSSC。ADC 行：`ADCPRE=10` 得到 12 MHz；`ADCPRE=01` 得到 18 MHz，越过 14 MHz。不把 21 µs 写进这张表。

### 坑与出处卡

至少这些行：

| 现象 | 处理方向 | 链接 | 允许的主张 |
| --- | --- | --- | --- |
| 只改 PLL ×9，一跑就停住 | 先把 LATENCY 写成 2，再切 SYSCLK | `#source-rm0008-rcc` | 48–72 MHz 这一档是 2 个等待。电压档沿用附录 D 的 2.7–3.6 V |
| PWM 频率差一倍 | 定时器时钟用 72 MHz，不用 PCLK1 的 36 MHz 去除 | `#source-rm0008-rcc` | APB 预分频不是 1 时定时器时钟再 ×2。TIM1 在 APB2 且预分频为 1 时不再 ×2 |
| 晶振没起振，系统停在外面 | 打开 CSS 之后时钟回到 HSI，并在 NMI 里写 CSSC | `#source-rm0008-rcc` | HSE 作为 PLL 入口时，失败会关掉 PLL，SYSCLK 改用 HSI |
| 按第 8.3.2 节去填 `PLLMUL` | 这颗 C8 用第 7.3.2 节。`0111` 仍是 ×9，`0000` 是 ×2 | `#source-rm0008-rcc` | 互联型的 `000x` 保留和 `OTGFSPRE` 在 STM32F103C8T6 上作废 |
| MCO 送出的波形超出脚的速度 | 送 PLL÷2 的 36 MHz，不把 72 MHz 的 SYSCLK 直接送上 PA8 | `#source-rm0008-rcc` | 送到 MCO 脚的时钟不得超过 50 MHz |
| ADC 为了更快选了 ÷4 | 改回 ÷6，得到 12 MHz | `#source-rm0008-rcc` | 14 MHz 是上限。÷4 得到 18 MHz。不支持 21 µs |

价格、选型口吻和「回退 HSI 再查焊点」里没有手册数字的那半句，留在核心原理。

### 短 GIF

辅图 `assets/gif/clock-css.gif`。内容是 HSE 8 MHz 进 PLL，系统时钟停在 72 MHz，然后 HSE 消失，系统时钟回到 HSI 8 MHz。帧数不少于 3、不多于 12。LATENCY = 0 的取指失败只放在静态主图上。不替换 `clock-tree.svg`。

## 第 05 章写什么

订货号仍是 STM32F103C8T6。计数时钟用附录 D 的 72 MHz，不用 36 MHz。

### 原理与边界

- **1 kHz。** TIM3 在 APB1。PCLK1 = 36 MHz，预分频不是 1，所以 TIM3 的计数时钟是 72 MHz。PSC = 71，ARR = 999。`72e6 / ((71+1) × (999+1)) = 1000` Hz。计数时钟先被分成 1 MHz，再数 1000 下，周期 1 ms。同一组 PSC、ARR 用 36 MHz 去除，得到 500 Hz。这是主图的失败路径。
- **占空比。** PWM 模式 1：CNT < CCR 时输出有效电平。CCR = 500 时，`500 / (999+1) = 50%`，高电平 500 µs。章内现在的 `PWM_ARR / 2` 等于 499，是 49.9%，不是 50%。实施时把片段里的比较值改成 500，注释和表用同一笔。不改 `examples/timer-pwm/`。
- **16 位。** 这颗料的 TIM2–TIM5 是 16 位。PSC = 71、ARR = 999999 装不下。能装下的 1 秒是 PSC = 7199、ARR = 9999，`72e6 / (7200 × 10000) = 1` Hz。分类表里的「16/32 位」在这颗料上改成 16 位。32 位的 TIM2/TIM5 是别的系列上的句子，换到那一系列时这一句作废。核心原理里 PSC = 0、ARR+1 = 72000 的那一行可以留下，标明它是另一组高分辨率参数，不是附录 D 的 1 kHz 格子。
- **脚。** 默认不重映射时 TIM3_CH1 在 PA6。DS5319 Rev 20 表 5：LQFP48 第 16 脚是 PA6，默认复用含 TIM3_CH1，同一格也含 SPI1_MISO。本图只画定时器。SPI 对这只脚的用法在第 08 章，两章的主图不把两种功能画成同时有效。重映射到 PB4 或 PC6 要另写 `TIM3_REMAP`，不画进正常路径。
- **MOE。** TIM1/TIM8 的 `TIMx_BDTR` 偏移 `0x44`，复位值 `0x0000`，位 15 MOE 为 0 时主输出关着。`HAL_TIM_PWM_Start` 会置 MOE。通用定时器 TIM3 没有这一位。`DeadTime = 0x10` 不进四块，也不换算成纳秒。

### 关键插图

主图文件 `assets/diagrams/sample-05-pwm-1khz.svg`。

图上是一路 PWM：

- 脚位：LQFP48 第 16 脚 PA6 = TIM3_CH1。计数时钟 72 MHz。PSC = 71，ARR = 999，CCR = 500。
- **正常路径。** 周期 1 ms，高电平 500 µs，频率 1000 Hz。CNT 从 0 数到 999，CNT < 500 时输出为高。
- **失败路径。** 同一组 PSC、ARR、CCR，去除时用了 36 MHz。周期变成 2 ms，频率 500 Hz。图上标出多出来的那一倍来自「把 PCLK1 当成了定时器时钟」。
- **旁注。** ARR = 999999 在 16 位计数器里装不下。TIM1 的 MOE 位 15 复位为 0，那是另一只定时器，不占 PA6 这条波形。同一只脚的 SPI1_MISO 不画进这条波形。

图注写「自绘」，带 RM0008 Rev 21 第 15 章和 DS5319 Rev 20 表 5。替代文本写出结论：72 MHz 计数时钟下这组 PSC/ARR 是 1 kHz；改用 36 MHz 去除得到 500 Hz。不写「示意图」。

`timer-pwm.svg` 和 `pwm-breath.gif` 留在原节，标成辅图。

### 时序或状态

一张表覆盖这一个周期。列至少有：计数时钟 72 MHz、PSC、ARR、CCR、CNT、输出电平、时间。正常行在 CNT = 0 到 499 为高，500 到 999 为低，周期 1000 µs。失败行的计数时钟写成 36 MHz，周期 2000 µs，频率 500 Hz。另有一行：ARR = 999999 被 16 位截断，不把它算成 1 秒。1 秒的可装下行是 PSC = 7199、ARR = 9999。

### 坑与出处卡

至少这些行：

| 现象 | 处理方向 | 链接 | 允许的主张 |
| --- | --- | --- | --- |
| 示波器上是 500 Hz | 用 72 MHz 去除，PSC = 71，ARR = 999 | `#source-rm0008-tim` | 这组数在 72 MHz 下是 1000 Hz。36 MHz 去除得到 500 Hz |
| 想要 1 秒，ARR 写成 999999 | 改成 PSC = 7199、ARR = 9999 | `#source-rm0008-tim` | 这颗料的通用定时器是 16 位，装不下 999999 |
| TIM1 完全没有波形 | 置上 BDTR 位 15 的 MOE | `#source-rm0008-tim` | 复位值 `0x0000`，MOE 为 0 时主输出关闭。TIM3 没有这一位 |
| PWM 出现在别的脚上 | 保持 `TIM3_REMAP=00`，用 PA6 | `#source-ds5319-tim` | LQFP48 第 16 脚是 PA6，默认复用含 TIM3_CH1 |

预装载、更新标志和呼吸灯撕裂留在核心原理。`0x10` 的死区不进出处卡。

### 短 GIF

辅图 `assets/gif/pwm-1khz.gif`。内容是 CNT 从 0 走到 ARR，CCR = 500 处电平翻转，标出 1000 Hz 和 500 µs。帧数不少于 3、不多于 12。500 Hz 的失败只在静态主图上。不替换 `pwm-breath.gif`。

## 第 08 章写什么

订货号仍是 STM32F103C8T6。SPI1 在 APB2，内核时钟 72 MHz。工作点整格照抄附录 D：Mode 0，`BR=010`，SCK = 9 MHz。

### 原理与边界

- **四根线。** 复位后的默认脚是 LQFP48 第 15 脚 PA5 = SPI1_SCK，第 17 脚 PA7 = SPI1_MOSI，第 16 脚 PA6 = SPI1_MISO，第 14 脚 PA4 = SPI1_NSS。本章片选不用硬件 NSS，PA4 配成推挽 GPIO，软件拉低再拉高。这不是第 07 章的开漏。重映射到 PB3/PB4/PB5 不画进正常路径。第 16 脚同时是第 05 章的 TIM3_CH1；本图只画 MISO。
- **Mode 0。** CPOL = 0，CPHA = 0。空闲时 SCK 为低，数据在第一个边沿（上升沿）采样。章内代码是 `SPI_POLARITY_LOW`、`SPI_PHASE_1EDGE`、`SPI_NSS_SOFT`、`SPI_FIRSTBIT_MSB`、`SPI_BAUDRATEPRESCALER_8`。
- **9 MHz。** `BR[2:0]` 只有 2、4、8、16、32、64、128、256 这八档。`010` 是 ÷8，`72 / 8 = 9` MHz。`001` 是 ÷4，18 MHz。`000` 是 ÷2，36 MHz。章内分频表写到 `100` = ÷32 = 2.25 MHz，正文补全八档。36 MHz 是相对 9 MHz 工作点的过快失败，不另开一套账。RM0008 第 25.5.1 节若印出的 BR 编码和这张表不同，以印出的编码为准，9 MHz 仍对应 ÷8，18 MHz 仍对应 ÷4。不编 SPI 基址。
- **JEDEC。** 主机发出 `{0x9F, 0xFF, 0xFF, 0xFF}`。全双工下，发 `0x9F` 的那 8 个 SCK 同时移进 `rx[0]`，这一字节不是厂商号。接下来三字节是 `rx[1]=0xEF`、`rx[2]=0x40`、`rx[3]=0x17`。拼法是 `rx[1] << 16 | rx[2] << 8 | rx[3]`，也就是 `0xEF4017`。`0x40` 是存储器类型，不是容量。页大小 256 字节。这两句链接 `project-examples` 和附录 D。不吸收 Winbond 手册，不新编 `0x9F` 以外的命令字节。`0x05`、`0x06`、`0x02`、`0x03` 留在核心原理和例程；状态字节位 0 当忙，也只作为例程里的做法，链接 `project-examples`。
- **失败。** MOSI 和 MISO 对调之后，三字节对不上 `0xEF 0x40 0x17`。片选一直为低时，下一条命令接在上一条后面。只调用 Transmit、不读 MISO 时，下一次读到的是残留。CPHA 配成第二沿时，字节会错位。主图的失败路径画 MOSI/MISO 对调。片选不释放和 `BR=000` 的 36 MHz 放在旁注。

ST7789 只写、不接 MISO。它的命令表留在核心原理，不进四块的规范主张。

### 关键插图

主图文件 `assets/diagrams/sample-08-spi-jedec.svg`，同样由 `gen_sample_figures.py` 生成，用 `_credit()`，不调用 `Svg.footer()`。

图上是一次读 ID：

- 脚位：第 14 脚 PA4 = CS（推挽，事务期间为低），第 15 脚 PA5 = SCK，第 16 脚 PA6 = MISO，第 17 脚 PA7 = MOSI。Mode 0：空闲 SCK 为低，上升沿采样。`BR=010`，SCK = 9 MHz。
- **正常路径。** MOSI 先送 `0x9F`，随后三个 `0xFF`。MISO 上 `rx[0]` 是命令期间移入的字节；`rx[1..3]` 是 `0xEF`、`0x40`、`0x17`。事务结束时 PA4 回到高。
- **失败路径。** PA6 和 PA7 对调。MISO 上读不到 `0xEF 0x40 0x17`。
- **旁注。** PA4 若一直为低，两条事务粘成一条。`BR=000` 时 SCK = 36 MHz，相对这条 9 MHz 的工作点过快。不把 PB3/PB4/PB5 画进正常路径。不把第 14 脚画成 DAC。

图注写「自绘」，带 RM0008 Rev 21 第 25.5.1 节和 DS5319 Rev 20 表 5。替代文本写出结论：Mode 0、÷8 得到 9 MHz；`0x9F` 之后的三字节是 `0xEF`、`0x40`、`0x17`；MOSI 和 MISO 对调之后这三字节对不上。不写「示意图」。

`spi-transfer.svg` 留作辅图。关键插图写明：不播放它，脚位、9 MHz 和 ID 三字节都在静态主图上。

### 时序或状态

一张表覆盖这 4 个字节。列至少有：字节序号、MOSI、MISO、CS、SCK。正常行：CS 为低；第 1 字节 MOSI = `0x9F`，MISO = `rx[0]`（不是厂商号）；第 2 到第 4 字节 MOSI = `0xFF`，MISO 依次是 `0xEF`、`0x40`、`0x17`；然后 CS 回到高。模式行：CPOL = 0，CPHA = 0，采样在上升沿。速率行：`BR=010` 为 9 MHz，`BR=001` 为 18 MHz，`BR=000` 为 36 MHz。失败行：PA6/PA7 对调，MISO 三字节不是 `0xEF 0x40 0x17`。

### 坑与出处卡

至少这些行：

| 现象 | 处理方向 | 链接 | 允许的主张 |
| --- | --- | --- | --- |
| 读回的 ID 不是 `0xEF4017` | 保持 Mode 0，并核对 PA7 是 MOSI、PA6 是 MISO | `#source-ds5319-spi` | LQFP48 第 16 脚是 MISO，第 17 脚是 MOSI。三字节本身见下一行 |
| 把 `rx[0]` 当成厂商号 | 厂商号在 `rx[1]`，类型在 `rx[2]`，容量在 `rx[3]` | `#source-project-examples` | 命令是 `0x9F`。三字节是 `0xEF`、`0x40`、`0x17`。`0x40` 不是容量 |
| SCK 跑到 36 MHz | `BR` 用 `010`，得到 9 MHz | `#source-rm0008-spi` | 八档分频里 `010` 是 ÷8。`000` 是 ÷2 = 36 MHz。不支持 ÷3 |
| 两条命令粘在一起 | 每条事务结束把 PA4 拉高 | `#source-ds5319-spi` | 第 14 脚是 SPI1_NSS。本章把它当推挽片选。它在 C8 上不是 DAC 输出 |
| ID 出现在 PB3/PB4/PB5 | 复位后的默认脚是 PA5/PA6/PA7 | `#source-ds5319-spi` | 第 15 脚 SCK，第 16 脚 MISO，第 17 脚 MOSI |

写使能和忙位留在核心原理，忙位那一行若写进出处卡，链接 `#source-project-examples`，主张只写「例程把状态字节的位 0 当成忙」。不新开 Winbond id。花屏、线太长留在核心原理，不引入新的兆赫以外的速率。

### 短 GIF

辅图 `assets/gif/spi-jedec.gif`。内容是正常路径：CS 拉低，MOSI 移出 `0x9F`，MISO 随后移入 `0xEF`、`0x40`、`0x17`，标出 9 MHz。帧数不少于 3、不多于 12。对调线和 36 MHz 只在静态主图上。不替换 `spi-transfer.svg`。

## 第 09 章写什么

订货号仍是 STM32F103C8T6。采样时钟用附录 D 的 12 MHz。换算分母用 4096。

### 原理与边界

- **时钟。** PCLK2 = 72 MHz，`ADCPRE=10`（÷6）得到 ADCCLK = 12 MHz。÷4 得到 18 MHz，越过 14 MHz。分频位的句子交叉引用第 02 章，这一章不重画时钟树。RM0008 在 14 MHz、采样 1.5 周期处给出 `Tconv = 1 µs`。那是上限上的例子。这颗料的工作点是 12 MHz，四块里不把 1 µs 和 21 µs 写进同一格。
- **一次转换。** 采样开关合上时，输入经源阻抗和 ADC 内阻给采样电容充电。开关断开后电容上的电压被保持。然后从 MSB 开始比较 12 次。转换时间是采样周期再加上 12.5 个 ADCCLK。最长采样档 239.5 再加 12.5 等于 252 个周期，`252 / 12e6 = 21 µs`。在 12 MHz 上：1.5 周期 = 125 ns，13.5 周期 = 1.125 µs，55.5 周期 = 4.625 µs，71.5 周期 = 5.958 µs，239.5 周期 = 19.958 µs。正文那张标成 14 MHz 的表（107 ns、0.96 µs、3.96 µs、17 µs）改成这些 12 MHz 的数，或者从四块里拿掉，只留在核心原理并标明那是上限例子。F4 的「采样再加 12 个周期」在这颗料上作废。
- **源阻抗公式。** 正文现在写 `ts ≈ (R_AIN + R_ADC) × C_ADC × ln(2^(N+2))`，并给出 R_ADC ≈ 1 kΩ、C_ADC ≈ 8 pF、N = 12、`ln(2^14) ≈ 9.7`。同一张表的 78 ns、0.78 µs、3.9 µs、7.8 µs、78 µs 却只乘了 R_AIN。把 1 kΩ 的 R_ADC 加进去，1 kΩ 源阻抗大约是 155 ns，不是 78 ns。实施时按 RM0008 印出的公式重算。印出的常数不同，就用印出的常数，不另编一个皮法。两个常数没印在第 11 章里，这张阻抗表留在核心原理，标成估算，不进出处卡。和 21 µs 同一格的时间仍然只按 12 MHz 的周期数。
- **温度和内部基准。** 推荐采样时间 17.1 µs。`17.1e-6 × 12e6 = 205.2` 个周期，所以 239.5 周期盖得住，71.5 周期（5.958 µs）盖不住。通道是 ADC1 的输入 16。VREFINT 是 ADC1 的输入 17，正文保持「约 1.20 V」，不编一块板子上的实测 VDDA。TSVREFE 在 `ADC_CR2`，双 ADC 器件上这一位只在 ADC1。ADC2 的通道 16 和 17 接到 VSS。温度公式是 `(V25 − VSENSE) / Avg_Slope + 25`。V25 ≈ 1.43 V、斜率 ≈ 4.3 mV/°C 标成电气特性里的典型值，不是保证的校准。F4 的 `TS_CAL1`、`TS_CAL2`、`VREFINT_CAL` 在 F103C8 上作废。
- **两只 ADC，没有 DAC。** DS5319 写明中密度器件都有两个 12 位 ADC。正文「F1 只有 1 个 ADC」改成：C8 有 ADC1 和 ADC2，没有 ADC3，没有 DAC。`HAL_DAC_Start` 在这颗料上落空。高密度 F103 和 F4 才有 DAC。DAC 的缓冲器、噪声和三角波留在核心原理，并写明换到有 DAC 的型号才成立。
- **脚和参考。** LQFP48 第 10 脚 PA0 = ADC12_IN0，第 9 脚 VDDA 就是参考。这一封装没有单独的 VREF+。100 脚及以上才有单独的 VREF+ / VREF−，这句可以留下，并写明 C8 用不到。第 10 脚在第 03 章是 LED 的电流脚；本图把它画成模拟输入时，点灯那条「写 1 输出电流」同时作废。不重画 `sample-03-gpio-led.svg`。第 14 脚 PA4 在 C8 上是 ADC12_IN4 / SPI1_NSS，不是 DAC_OUT1。把 DAC 画在第 14 脚上是失败旁注。
- **换算。** 电压 = 码 × VDDA / 4096。名义 3.3 V 时 1 LSB = `3.3 / 4096 ≈ 0.806` mV，和章内 806 µV 那一格同一笔。码 2048 是 `2048 / 4096 = 1/2`，名义 3.3 V 下正好 1.65 V。分母用 4095 会偏一个 LSB。代码注释里的「约 VREF/2」改成这半满量程。
- **校准。** RM0008 第 11.4 节：上电后做一次校准。置 `ADC_CR2` 的 CAL 之前，ADON 已经为 1 至少两个 ADC 时钟。HAL 侧是 `HAL_ADCEx_Calibration_Start`，放在 Start 之前。F4 没有这一步，那句在换系列时作废。
- **DMA。** 只交叉引用第 10 章和附录 D：这颗料只有 DMA1，ADC1 是通道 1。不把半字、`CNDTR` 和「已写 5 个采样」的算术搬进这一章。

### 关键插图

主图文件 `assets/diagrams/sample-09-adc-sar.svg`。

图上是一次采样加一次比较：

- 脚位：LQFP48 第 10 脚 PA0 = ADC12_IN0，第 9 脚 VDDA 为参考。ADCCLK = 12 MHz。
- **正常路径。** 采样开关闭合，画出 R_AIN 与采样电容。开关断开后保持。比较器做 MSB 那一次：与 Vref/2 比较。最长一档旁注 `239.5 + 12.5 = 21 µs`。码值旁注 `× VDDA / 4096`。
- **失败路径。** 采样时间短到电容上还留着上一次的电压，这一次的码不是现在的输入。
- **旁注。** ÷4 得到 18 MHz，越过 14 MHz。第 14 脚被画成 DAC 输出时，在 C8 上没有这只脚的 DAC。不把第 03 章的 LED 电阻画进这张图。

图注写「自绘」，带 RM0008 Rev 21 第 11 章（Tconv 与 17.1 µs）和 DS5319 Rev 20 图 8。替代文本写出结论：这颗料的 ADC 时钟是 12 MHz，最长转换 21 µs；采样太短时电容上仍是上一次的电压。不写「示意图」。

`adc-sar.svg` 留作辅图。`sar-adc.gif` 留在原节，不替换像素。

### 时序或状态

一张表用 12 MHz。列至少有：采样周期数、采样时间、加 12.5 之后的总时间。必须有的行：1.5 周期 = 125 ns，总时间 `14 / 12e6`；239.5 周期 = 19.958 µs，总时间 21 µs。温度行：17.1 µs 需要 205.2 个周期，选 239.5，不选 71.5。失败行：ADCCLK = 18 MHz，越过 14 MHz，不把这行的周期数再除一次算出另一套微秒去和 21 µs 并列。换算行：码 2048 在名义 3.3 V 下是 1.65 V，分母 4096。

### 坑与出处卡

至少这些行：

| 现象 | 处理方向 | 链接 | 允许的主张 |
| --- | --- | --- | --- |
| 读数还停在上一次的电压附近 | 按 12 MHz 加长采样。高阻时用 239.5 周期 | `#source-rm0008-adc` | 转换时间 = 采样 + 12.5。12 MHz 下最长 252 周期是 21 µs |
| 为了更快把 ADC 设成 ÷4 | 改回 ÷6，12 MHz | `#source-rm0008-adc` | 14 MHz 是上限。18 MHz 越过它。1 µs 那个例子是 14 MHz 上的，不是这颗料的工作点 |
| 温度通道噪声大、读数飘 | 采样至少覆盖 17.1 µs，用 ADC1 通道 16，并置 TSVREFE | `#source-rm0008-adc` | 17.1 µs 在 12 MHz 上是 205.2 个周期。VREFINT 是 ADC1 通道 17。ADC2 的 16/17 接到 VSS |
| 上电第一次整体偏移 | Start 之前做校准 | `#source-rm0008-adc` | 第 11.4 节：CAL 之前 ADON 已为 1 至少两个 ADC 时钟 |
| 换算比万用表高一截 | 分母用 4096 | `#source-rm0008-adc` | 12 位满量程是 4096 步。码 2048 是半满量程。参考是第 9 脚 VDDA |
| 蓝药丸上调用了 `HAL_DAC_Start`，PA4 没有模拟电压 | 这颗 C8 没有 DAC。要模拟电压用 PWM 加 RC，或换有 DAC 的型号 | `#source-ds5319-adc` | 中密度有两个 12 位 ADC。没有 ADC3，没有 DAC。第 14 脚不是 DAC_OUT1 |
| 第 10 脚点过灯，采样却像在读推挽 | 采样时这只脚是模拟输入，不再按第 03 章输出电流 | `#source-ds5319-adc` | LQFP48 第 10 脚 PA0 是 ADC12_IN0。不改写第 03 章那张 LED 图 |

1 kΩ、8 pF 只有在 `rm0008-adc` 的 snapshot 写进了印出的常数之后，才能再加一行阻抗主张。没写进 snapshot，就不加这一行。

### 短 GIF

辅图 `assets/gif/adc-sample.gif`。内容是一次成功的采样，接着 MSB 那一次比较，标出 ADCCLK = 12 MHz。帧数不少于 3、不多于 12。采样过短和 18 MHz 只在静态主图上。不替换 `sar-adc.gif`，也不改它在 `BUILDERS` 里的像素。

## 插图标准

沿用总纲和 Batch2 的逼真、翔实、生动、可印刷、自绘。主图和短 GIF 分开。简化示意图可以留在章内当辅图，不能充当关键插图的主图。

静态主图：

- 用 `tools/svgkit.py`，生成脚本是 `tools/gen_sample_figures.py`。四章各一张，中英引用同一文件。中文路径 `../assets/diagrams/...`，英文路径 `../../assets/diagrams/...`。
- 不调用 `Svg.footer()`。落款用脚本里已有的 `_credit()`：左侧是文档号，右侧是「自绘 · 静态 · CC BY 4.0」。
- 没有 `<animate`、`@keyframes`、`animation:`。图上同时有正常路径和失败路径。
- 替代文本写结论。图注写「自绘」，不写「实拍」「手册截图」「矢量动画」。
- 单张小于 60 KB。放不下就拆成主图加局部，每张仍争取小于 60 KB。拆开仍超过时，在实施 PR 里写出字节数和原因，不把图画回简笔，也不把 60 KB 改成仓库新默认值。
- 登记进 `assets/README.md` 第四节，和 `sample-00-boot-state.svg`、`sample-03-gpio-led.svg`、`sample-04-exception-stack.svg`、`sample-06-uart-frame.svg` 并列。

短 GIF：

- 四条都走 `tools/gen_gifs.py`，加入 `BUILDERS`，这样 `tools/check_assets.py` 能逐像素对上重新生成的帧。GIF 上的字用 ASCII。
- 每条少于 500 KB，帧数见上面四节。图注写明它是网页和公众号辅图，印刷以静态主图为准。
- `gen_gifs.chrome()` 自带的页脚可以留在 GIF 里。那条页脚不是静态主图的 `Svg.footer()`。
- 不改已有 8 个 BUILDERS 的像素：`led-blink`、`pwm-breath`、`uart-bits`、`i2c-timing`、`dma-ring`、`sar-adc`、`nvic-preempt`、`uart-idle`。不重跑它们来换画面。
- `tools/svg2gif.py` 这一批不当成必经步骤，也不为了它去改 CI。

PDF 关掉动画之后，读者只看静态主图和图注，就能指出失败发生在哪一段。第 02 章是「72 MHz 时 LATENCY 仍为 0」。第 05 章是「用 36 MHz 去除，1 kHz 变成 500 Hz」。第 08 章是「PA6 与 PA7 对调，读不到 `0xEF 0x40 0x17`」。第 09 章是「采样太短，电容上仍是上一次的电压」。

## 工作流与 PR 节奏

### 本 PR（设计）

只改本文件的名字和正文：删 `docs/superpowers/specs/2026-10-25-classic-encyclopedia-batch3-01-02-05-07-design.md`，留下 `docs/superpowers/specs/2026-10-25-classic-encyclopedia-batch3-02-05-08-09-design.md`。不改 `docs/02`、`docs/05`、`docs/08`、`docs/09`、`docs/en/` 的章节，也不改 `docs/01`、`docs/07`。不改 `stm32-book/`、`CREDITS.md`、`assets/`、`tools/`。不升版本，不打 tag，不发 Release。不新增 `docs/superpowers/plans/` 下的实施计划。本 PR 等人审阅规格后再合入，不在 CI 变绿后自动合。

### 实施 PR（下一轮，不在本 PR）

顺序固定：

1. **核对扫描。** 写出 `2026-10-25-batch3-02-05-08-09-lock.json`。章号保持 02、05、08、09。
2. **许可门。** 写出 `2026-10-25-batch3-02-05-08-09-source-list.json`。先有清单，再改正文。
3. **静态主图和短 GIF。** 先提交 SVG、GIF 和生成脚本，再写正文。主图不依赖 GIF。
4. **中英加厚。** 八份 Markdown 一起提交。文件 `01` 和 `07` 的 diff 为空。
5. **登记。** 新来源追加进两份 manifest。更新这四章罗盘的来源数组。`CREDITS.md` 第六节增加 v1.2.2 小节。`revisions.json` 在条目最前加上 1.2.2，日期写死 `2026-10-25`。两份 manifest 的 `version` 改为 `1.2.2`，`date` 改为 `2026-10-25`。`stm32-book/README.md` 的当前版本句改为 **v1.2.2 · 2026-10-25**。发布一节里的 tag 名改成 `v1.2.2`，并在现有「也不要把 1.2.0 的产物标成 1.2.1」之后加上「也不要把 1.2.1 的产物标成 1.2.2」。这一步仍不创建 tag，也不创建 Release。修订说明只写这四章加厚了什么，用文件名前缀，不写尚未做的章。中英各两句，例如：第 02 章把 CFGR 改回第 7.3.2 节，并写上 72 MHz 要 2 个等待、CSS 回到 HSI。第 05 章写上 1 kHz 和 500 Hz 两条路径。第 08 章写上 Mode 0、9 MHz，以及 `0x9F` 之后的 `0xEF`、`0x40`、`0x17`。第 09 章写上 12 MHz 下的 21 µs、除以 4096，以及 C8 有 ADC1/ADC2、没有 DAC。英文用同样的事实。
6. **测试。** 新增 `stm32-book/tests/test_batch3_chapters.py` 和 `stm32-book/tests/test_batch3_sources.py`，照着 Batch2 测试检查四块、共享数字、主图禁词和许可门。不放宽 `test_sample_chapters.py` 和 `test_batch2_chapters.py`。`test_build.py` 里当前版本从 `1.2.1` 改为 `1.2.2`：`assert_version_history_and_index` 的元组在 `1.2.1` 之前加上 `1.2.2`；修订列表以 `1.2.2` 起头；两份整书 HTML 的 `<strong>v1.2.2</strong>`；`test_visual_polish_version_is_1_2_0` 改为核对当前条目是 1.2.2，日期是 2026-10-25，1.2.1 那两句指南说明改去核对 `entries[1]`。不删 `0x271`、`167 ns`、账本名和出版书签长度为 44 的断言。不新增读取 `CONTENT_GUIDE.md` 的测试。
7. **CI 变绿之后停下来等人复审。** 复审对象是构建出的中英 HTML 里的这四章。人接受之前不合入，也不开下一批章。Book CI 变绿不等于可以自动 squash 合入。

实施 PR 的 diff 可以碰这四章中英正文、两份 manifest 的新 `sources` 和这四章罗盘、新图与生成脚本、`assets/README.md`、`CREDITS.md`、版本与修订、新的锁定文件和来源清单、新测试，以及 `test_build.py` 里的版本字符串。不碰其余章的正文，不改 `build_html.py`。

## 验收

### 本设计 PR

- 相对基线 `b2a4f26`，规格文件是 `docs/superpowers/specs/2026-10-25-classic-encyclopedia-batch3-02-05-08-09-design.md`。仓库里不再有 `2026-10-25-classic-encyclopedia-batch3-01-02-05-07-design.md`。
- 章节、`stm32-book/`、资产、工具和 `CREDITS.md` 与基线 `b2a4f26` 相同。
- 没有新的 SVG 或 GIF，版本号仍是 1.2.1。没有实施计划文件。

### 实施 PR

- 中文四章各有且仅有一次：`## 原理与边界`、`## 关键插图`、`## 时序或状态`、`## 坑与出处卡`。英文对应四个标题同样各一次。
- 四章都不再有 `## ⚠️ 常见坑与排查` 或 `## ⚠️ Pitfalls and troubleshooting`。
- 每章关键插图的第一张图是对应的静态 SVG。图上能看出正常路径和失败路径。GIF 不是这一节唯一的图。
- 中英都有这些数字，而且彼此一致：
  - 第 02 章：`7.3.2`、`0111`、`72`、`36`、`12`、`18`、`14`、`48`、`50`、`8`、LATENCY `2`、`CSSC`、第 5 脚、第 6 脚、第 29 脚。正文不再把这颗 C8 的 CFGR 说成第 8.3.2 节。21 µs 不出现在这一章的四块里。
  - 第 05 章：`PSC` `71`、`ARR` `999`、`CCR` `500`、`1000`、`500` Hz、`16`、`999999`、`7199`、`9999`、第 16 脚、`PA6`、`MOE`、`0x44`。
  - 第 08 章：`010`、`9`、`001`、`18`、`000`、`36`、`0x9F`、`0xEF`、`0x40`、`0x17`、`256`、第 14 脚到第 17 脚、`PA4`、`PA5`、`PA6`、`PA7`、CPOL `0`、CPHA `0`。`rx[1]` 才是 `0xEF`。
  - 第 09 章：`12`、`14`、`18`、`21`、`4096`、`239.5`、`12.5`、`252`、`17.1`、`125` ns、`2048`、`1.65`、第 9 脚、第 10 脚、`VDDA`、`PA0`、`ADC1`、`ADC2`。正文写明 C8 没有 DAC，也不再写「F1 只有 1 个 ADC」。
- 第 02 章、第 05 章、第 08 章、第 09 章引用附录 D 的格子时整格照抄，不改附录 D 正文。
- 静态 SVG 小于 60 KB，不含动画标记，含「自绘」，不含「实拍」和「矢量动画」。四条新 GIF 小于 500 KB，并且在 `BUILDERS` 里。`sar-adc` 的像素与基线相同。
- 新 `#source-` 都能在构建出的 HTML 里找到 `id="source-..."`。已有 `rm0008`、`ds5319`、`rm0008-boot`、`rm0008-gpio`、`ds5319-gpio`、`project-examples` 的对象与基线逐字段相同。
- 附录 D 三套账和附录 A 的正文 diff 为空。`test_build.py` 对 `0x271`、`167 ns` 和出版书签条数的断言仍在。
- 除这四章的中英八份以外，`docs/` 章节正文 diff 为空。`docs/01` 和 `docs/07` 及其英文的 diff 为空。`build_html.py` 的 diff 为空。
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

1. **SPI 的 BR 编码。** 默认沿用附录 D 和章内表：`010` = ÷8 = 9 MHz，`001` = ÷4 = 18 MHz，`000` = ÷2 = 36 MHz。第 25.5.1 节印出的字段不同时，用印出的编码，9 MHz 仍是 ÷8，18 MHz 仍是 ÷4，并在实施 PR 说明里写明差异。不编基址。
2. **采样电容公式。** 只有 RM0008 印出了 R_ADC 和 C_ADC，才写进 `rm0008-adc` 并重算阻抗表。没印出来，阻抗表留在核心原理。12 MHz 的周期账不受这一项影响。
3. **主图体积。** 先拆图。拆开仍超过 60 KB 时在实施 PR 里说明，不降低画法标准。
4. **图目录。** 这一批不加。
5. **下一批章号。** 仍是 4 章，到下一次设计再锁。本文件不预选 `01` 或 `07`。
6. **第 16 脚。** 第 05 章主图主张 TIM3_CH1，第 08 章主图主张 SPI1_MISO。两张图都不把两种功能画成同时有效。

## 英文提要

Thicken only chapter files 02 (part, memory, and the clock tree), 05 (timers and PWM), 08 (SPI), and 09 (ADC and DAC), in Chinese and English, on top of v1.2.1 (`b2a4f26`, PR #29). Chapters 00, 03, 04, and 06 are already thick. GPIO stays in chapter 03. I2C stays in chapter 07. Development setup (file 01) is not in this batch. Use the same four sections as chapters 00, 03, 04, and 06. Each chapter gets one printable static SVG from `gen_sample_figures.py`, with a normal path and a failure path, and no `Svg.footer()`. Chapter 02 draws the medium-density tree in RM0008 section 7.3.2: HSE 8 MHz times 9 is 72 MHz with two Flash wait states, and CSS falls back to HSI at 8 MHz. Section 8.3.2 is void on STM32F103C8T6. The ADC sentence in that chapter stops at the divider: divide-by-6 is 12 MHz, divide-by-4 is 18 MHz. Chapter 05 draws TIM3 CH1 on pin 16 PA6 at 1 kHz (PSC 71, ARR 999, CCR 500) and the 500 Hz failure that comes from dividing by 36 MHz. Chapter 08 draws SPI1 Mode 0 on LQFP48 pins 14–17, `BR=010` at 9 MHz, command `0x9F`, and the next three received bytes `0xEF`, `0x40`, `0x17`. Swapping MOSI and MISO is the failure. Chapter 09 draws a sample-and-hold plus one SAR step at 12 MHz, with the 21 µs longest conversion (`239.5 + 12.5` cycles) and conversion by dividing by 4096. The failure is a sample so short that the capacitor still holds the previous voltage. STM32F103C8 has ADC1 and ADC2, and it has no DAC. One short GIF per chapter is auxiliary only. The existing `sar-adc` GIF stays as it is. Register new sources by appending ids. Bump the book to 1.2.2 on 2026-10-25 during implementation, do not tag or release, and stop for human review before squash-merge. This design PR only replaces the Batch3 spec file.

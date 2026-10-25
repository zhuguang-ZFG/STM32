# 第 01、02、05、07 章加厚设计

日期：2026-10-25  
状态：已批准，待第 01、02、05、07 章实施  
基线：`main` 上的整书 **v1.2.1**（`b2a4f267f58ba42bd9749e94d9f8c2bac7cac118`，PR #29，2026-10-25）  
上一份设计：[2026-10-25-content-guide-four-blocks-1.2.1-design.md](2026-10-25-content-guide-four-blocks-1.2.1-design.md)（PR #28）。四块模板来自 [2026-10-25-classic-encyclopedia-thicken-design.md](2026-10-25-classic-encyclopedia-thicken-design.md)（PR #18）。Batch2 规格是 [2026-10-25-classic-encyclopedia-batch2-04-06-design.md](2026-10-25-classic-encyclopedia-batch2-04-06-design.md)（PR #22）。  
本文件只记录这一批的设计。它不改章节正文，不画新图，不改 `stm32-book/` 构建，不升版本号，不打 tag，不发布 Release，不写实施计划。

## 背景

v1.2.1 已经把大典四块写进两份 `CONTENT_GUIDE`。已经按这个骨架加厚的是第 00、03、04、06 章。这一批只加厚另外四章，中文和英文一起写：

| 文件前缀 | 中文 | 英文 | 这一章在讲 |
| --- | --- | --- | --- |
| `01` | `docs/01-开发环境搭建.md` | `docs/en/01-dev-environment.md` | 工具链、SWD、复位后取向量 |
| `02` | `docs/02-芯片选型与存储器时钟.md` | `docs/en/02-part-and-clock.md` | 订货号、存储器映射、时钟树 |
| `05` | `docs/05-定时器与PWM.md` | `docs/en/05-timer-pwm.md` | 时基、PWM、输入捕获 |
| `07` | `docs/07-I2C总线.md` | `docs/en/07-i2c.md` | 开漏上拉、地址、重复起始 |

读者看到的章号仍是文件名前缀加 1：文件 `01` 在书里是第 2 章，`02` 是第 3 章，`05` 是第 6 章，`07` 是第 8 章。源文件的一级标题继续带 `01`、`02`、`05`、`07`。这一批不改这个加 1。

GPIO 的封装和电流路径已经在第 03 章（`sample-03-gpio-led.svg`，LQFP48 第 10 脚 PA0、第 2 脚 PC13，270 Ω 与注 5 的 3 mA）。ADC 的采样账在第 09 章和附录 D（12 MHz，最长一档 21 µs）。这两章不在本批。时钟章只保留附录 D 里已经钉在第 02 章的那一格 ADC 分频，不把逐次逼近写进来。

对照 v1.2.1 核对过的事实：

1. **这四章还没有四块。** 第 00、03、04、06 章在 `<!-- /video: -->` 之后、学习目标之前，已经有 `## 原理与边界`、`## 关键插图`、`## 时序或状态`、`## 坑与出处卡`（英文是 `Principle and boundary`、`Key figures`、`Timing or state`、`Pitfalls and source cards`）。这四章仍从学习目标写起。中文坑还在 `## ⚠️ 常见坑与排查`，英文坑还在 `## ⚠️ Pitfalls and troubleshooting`，坑表没有 `#source-`。
2. **第 01 章的主图还是启动动画。** 章首是 `assets/animations/boot-sequence.svg`，目录结构是 `assets/diagrams/project-structure.svg`。第 00 章已经用 `sample-00-boot-state.svg` 画过 BOOT0=0 时 `0x00000000` 别名到 `0x08000000`，以及 BOOT1=0 且 BOOT0=1 时取到系统存储器 `0x1FFFF000`。第 03 章已经把 SWDIO=PA13、SWCLK=PA14 写进出处卡。第 01 章还没有一张静态图同时画出 LQFP48 上的 SWD 脚、共地，以及「PA13/PA14 被配成推挽之后探针和引脚抢同一根线」。
3. **第 02 章把中密度的 CFGR 写成了互联型的节号。** 正文写「RM0008 第 8.3.2 节」。RM0008 Rev 21 里，中密度（含 STM32F103C8T6）的 `RCC_CFGR` 在第 7.3.2 节：`PLLMUL` 的 `0111` 是 ×9，`0000` 是 ×2，`USBPRE=0` 是 PLL÷1.5。第 8.3.2 节是互联型：`PLLMUL` 的 `000x` 保留，`USBPRE` 那位换成 `OTGFSPRE`。附录 D 的时钟账仍是 HSE 8 MHz ×9 = 72 MHz，APB1 36 MHz，APB2 72 MHz，定时器在预分频不为 1 时再 ×2。这张账不改。
4. **第 05 章的 1 kHz 账已经在附录 D，分类表还把位宽写成 16/32。** 罗盘和附录 D：PSC = 71，ARR = 999，`72e6 / (72 × 1000) = 1000 Hz`。同一组数用 36 MHz 去除得到 500 Hz。PSC = 71、ARR = 999999 装不进 16 位；能装下的 1 秒是 PSC = 7199、ARR = 9999。这颗 F103 的 TIM2–TIM5 是 16 位。章内分类表写「通用 TIM2~TIM5，16/32 位」，没有写明 32 位在这颗料上作废。章首 `timer-pwm.svg` 和 `pwm-breath.gif` 是动画，印刷时看不出 500 Hz 那条失败。
5. **第 07 章的地址和 4.7 kΩ 已经在附录 D，上升时间那句把两档写反了。** 罗盘和附录 D：7 位地址 `0x3C`，HAL 填 `0x78`，短总线外接 4.7 kΩ 到 3.3 V，片内上拉约 30–50 kΩ，不能拿去跑 400 kHz。正文把 `Rp(max) ≈ 300ns / Cb` 标成标准模式。快速模式的最大上升时间才是 300 ns；标准模式是 1000 ns。`I2C_TRISE` 在 PCLK1 = 36 MHz 时，标准模式是 37，快速模式按整数除法是 11。章首 `i2c-transaction.svg` 和 `i2c-timing.gif` 播放事务，不画出 4.7 kΩ 的灌电流，也不画出第 9 拍 NACK。
6. **许可门与已有 id 保持原样。** 允许吸收的仍是 ST 手册里的事实（自己的话重写），以及 MIT、BSD-2-Clause、BSD-3-Clause、ISC、CC BY 4.0、CC BY 3.0、CC0。GPL、LGPL、CC BY-NC、CC BY-ND、Apache-2.0、保留所有权利、未写许可的材料只留链接。`clion-embedded` 和 `platformio-vscode` 已在第 01 章罗盘里，许可是「链接引用」，不吸收句子。`sources` 只追加。已有 id 一个字段都不改，含 `rm0008-boot`、`rm0008-gpio`、`ds5319-gpio`、`rm0008`、`ds5319`。
7. **观感设计里那句「Batch3 再加厚两章」到此被这一批的四章锁定替换。** 那份文件不回写。全 29 章最终都要加厚。本批只规格化这四章。再下一批仍是 4 章，章号到那时再锁。

## 目标与非目标

### 目标

- 只把第 01、02、05、07 章加厚到和第 00、03、04、06 章相同的四块密度。中文和英文一起写完。
- 每章一张可印刷的静态主图：正常路径和失败路径都在图上，封装脚位、信号名和文档号是真的。另加一条短 GIF，只做网页和公众号辅图。
- 数字钉在已经冻结的 RM0008 Rev 21、DS5319 Rev 20 和附录 D 已有的格子上。第 02 章那句「第 8.3.2 节」改到中密度的第 7.3.2 节。第 05 章的 1 kHz 与第 07 章的 `0x78`、4.7 kΩ 跟附录 D 同一笔账。
- 新出处追加进两份 manifest 的 `sources`。章内坑卡使用 `#source-...`。`CREDITS.md` 第六节记下这一批改写吸收了什么。
- 实施合入时把整书从 1.2.1 升到 **1.2.2 · 2026-10-25**。中英文共用这个版本号和这个日期。这一批不打 tag，不创建 Release。
- 实施 PR 在 Book CI 变绿之后停下来等人复审。人接受之前不合入。

### 非目标

- 不加厚除 01、02、05、07 以外的任何章，含已经加厚的 00、03、04、06，以及 08、09 和其余章。不改这几章的英文。
- 不把第 03 章的 LED 电流路径再写进第 01 章。不把第 09 章的逐次逼近、采样档 1.5 到 239.5、21 µs 写进第 02 章或第 07 章。
- 不重选样本，不改 `docs/superpowers/plans/` 里已有的样本和 Batch2 锁定文件、来源清单。不改 `tools/scan_sample_chapters.py`。
- 不改总纲、Batch2 规格、观感规格、CONTENT_GUIDE 规格，也不改两份 `CONTENT_GUIDE.md`。
- 不实现 v1.2.1 或 v1.2.2 的 GitHub Release，也不打 `v1.2.1` 或 `v1.2.2` 的 tag。
- 不改 `stm32-book/build_html.py`。出版书签仍是现在的 44 条。不把新的二级标题收进书签。
- 不改附录 A 的既有契约，不改附录 D 三套账的算术，不手改 `stm32-book/book/E-参考资料.md` 或英文对应文件。附录 E 的卡片仍由 `sources` 生成。
- 不替换、不重画已有图。第 01 章留下 `boot-sequence.svg` 和 `project-structure.svg`。第 02 章留下 `clock-tree.svg`、`memory-map.svg`、`peripheral-bus.svg`。第 05 章留下 `timer-pwm.svg`、`timer-modes.svg`、`pwm-breath.gif`。第 07 章留下 `i2c-transaction.svg`、`i2c-timing.gif`。新主图是加进去的。
- 不改 `assets/video/`，不新做讲解视频。不把厂商手册、官方插图或社区原文放进仓库。
- 不加图目录或表目录，不加第 30 章，不改 `docs/00`–`28` 的文件名。
- 不新开可烧录工程。保留 `examples/gpio-blink/`、`examples/timer-pwm/`、`examples/i2c-oled/`。这三份工程的源文件这一批不改。

## 来源与许可

四层用法和总纲、Batch2 相同。

允许写进正文的，仍按这个顺序：

1. ST 的 RM、DS、PM：只吸收事实，用自己的话写，附文档号和可点击的入口。不粘贴段落，不描官方图。
2. MIT、BSD-2-Clause、BSD-3-Clause、ISC、CC BY 4.0、CC BY 3.0、CC0：可以改写教学要点。许可证不强制署名时，本书仍署名。
3. 其他许可证：只留链接。含 GPL、LGPL、CC BY-NC、CC BY-ND、Apache-2.0、保留所有权利、未写许可的帖子和视频。

权威数字以第 1 层和附录 D 已有格子为准。社区材料只支持「这个坑有人踩过」。帖子里的寄存器值，要在 RM/DS 上重新钉住之后才能进「原理与边界」或「时序或状态」。钉不住的，出处卡的主张写成「经验线索，未升格为规范」，并且这一行不引入新的寄存器值。

CLion、PlatformIO、edge-tts、ST-Link 升级工具的文档不在允许吸收的名单里。第 01 章可以继续链接已有的 `clion-embedded` 和 `platformio-vscode`。不把这两份文档的句子写进四块。

### 追加的来源 id

新 id 只追加在两份 `sources` 对象的末尾。已有 id 的标题、URL、snapshot、许可、scope 都不改。中英两份的 `url`、`snapshot`、`license`、`accessed` 用同一串字符；`title`、`authority`、`scope` 用对应语言。`accessed` 用 `2026-10-25`。章罗盘的 `sources` 数组在原有 id 之后追加新 id，不删除已有 id。

RM0008 的 PDF 与已有 `rm0008-boot` 相同。DS5319 的 PDF 与已有 `ds5319-gpio` 相同。不另找一份修订。

| 新 id | 冻结点 | 用在 | 不复制 |
| --- | --- | --- | --- |
| `ds5319-swd` | DS5319 Rev 20，2025-07，图 8 与表 5。LQFP48 第 34 脚 PA13，第 37 脚 PA14 | 第 01 章。SWDIO / SWCLK 的封装脚 | 不描图 8。不把第 03 章的 PA0/PC13 写进这条 scope |
| `rm0008-rcc` | RM0008 Rev 21，2021-02。中密度第 7.2 节时钟、第 7.2.7 节 CSS、第 7.3.2 节 `RCC_CFGR`；Flash 等待在第 3 章访问时间那一段（0 / 24 / 48 / 72 MHz 三档）。定时器 ×2 在第 7.2 节 | 第 02 章。72 MHz 树、CSS 回 HSI、第 8.3.2 节在这颗料上作废 | 不把互联型 `OTGFSPRE` 和 `PLLMUL` 的 `000x` 保留写进 C8。不改已有 `rm0008` |
| `ds5319-clock` | DS5319 Rev 20 图 8 与表 5。LQFP48 第 5 脚 PD0-OSC_IN，第 6 脚 PD1-OSC_OUT，第 29 脚 PA8（复用含 MCO） | 第 02 章主图的晶振脚和 MCO 脚 | 不描图。不编负载电容的皮法 |
| `rm0008-tim` | RM0008 Rev 21。通用定时器时基在第 15 章；`AFIO_MAPR` 的 `TIM3_REMAP=00` 是 CH1/PA6；高级定时器 `TIMx_BDTR` 偏移 `0x44`，位 15 是 MOE，复位值 `0x0000` | 第 05 章。1 kHz、16 位装不下 999999、TIM1 的 MOE | 不把 `DeadTime = 0x10` 换成一个新的纳秒。不改附录 D 的 1 kHz 格子 |
| `ds5319-tim` | DS5319 Rev 20 表 5。LQFP48 第 16 脚 PA6，默认复用含 TIM3_CH1 | 第 05 章主图 | 不把 TIM3 重映射到 PB4 或 PC6 画进正常路径 |
| `rm0008-i2c` | RM0008 Rev 21 第 26 章。`I2C_CCR` 在第 26.6.8 节，`I2C_TRISE` 在第 26.6.9 节。`I2C1` 默认 SCL/PB6、SDA/PB7 | 第 07 章。CCR、TRISE、ACK 在第 9 拍 | 不粘贴时序图。不把片内 30–50 kΩ 写成可以跑 400 kHz |
| `ds5319-i2c` | DS5319 Rev 20 图 8 与表 5。LQFP48 第 42 脚 PB6，第 43 脚 PB7 | 第 07 章主图 | 不把重映射 PB8/PB9 说成复位后的默认脚 |

`rm0008-rdp` 只有在 RM0008 Rev 21 选项字节那一节同时印出两件事时才追加：无保护的读保护字节就是本章已写的 `AA`，并且解除读保护会擦除 Flash。两件事都印着，才把节号写进 snapshot。印出来的无保护值不是 `AA`，正文改成印出来的值，并在实施 PR 说明里写明旧句作废。两件事对不齐，就不追加这个 id；`AA` 留在动手实验，不写进出处卡的规范主张。

来源清单的 `absorb` 必须含上表除 `rm0008-rdp` 以外的七个 id。`rm0008-rdp` 只有在 snapshot 写进了节号时才出现。

许可门若找不到 MIT、BSD 或 CC BY/CC0 的社区例程，来源清单里的社区列表就是空的。空列表不挡住加厚。不吸收未写许可的博客，也不吸收 GPL 的 libopencm3。

### 沿用、但不改写对象的 id

| 已有 id | 这一批怎么用 |
| --- | --- |
| `rm0008-boot` | 第 01 章交叉引用：BOOT0=0 时 `0x00000000` 别名到 `0x08000000`，字 0 是 MSP，字 1 是复位向量。不改这条 scope。主图的失败路径不是第 00 章那条「BOOT0=1 进系统存储器」 |
| `rm0008-gpio` | 第 01 章交叉引用：SWDIO 是 PA13，SWCLK 是 PA14。不改这条 scope，不用它证明第 34 脚和第 37 脚 |
| `ds5319-gpio` | 不改。第 03 章的 PA0/PC13 不进这一批的主图 |
| `rm0008`、`ds5319`、`pm0056` | 不改。新事实走上表的新 id |
| `clion-embedded`、`platformio-vscode` | 仍是链接引用。不吸收句子 |

出处卡的字段仍是现有附录 E 的一套：`title`、`authority`、`url`、`snapshot`、`accessed`、`license`、`scope`。`url` 必须是 `https://`。章内第四块每一行只有一个主张，并带一个 `#source-`。一行写清现象、原因、处理、链接、该来源允许支持的主张。

`CREDITS.md` 第六节现在有「样本章的改写吸收（v1.1.0）」和「第 04 章与第 06 章（v1.1.1）」。这一批在该节下面加一个小节「第 01、02、05、07 章（v1.2.2）」，保留前面的表。新表只列作品名、许可证、用在哪、链接。不贴手册原文。

## 锁定

章号按文件名前缀锁死：`01`、`02`、`05`、`07`。不再按「谁更薄」重选，也不改成第 03 章或第 09 章。

实施开始时仍做一次核对扫描，只读这四章的中英八份。扫描确认两件事：四块标题还不存在；旧的「常见坑」标题还在。结果写到新文件 `docs/superpowers/plans/2026-10-25-batch3-01-02-05-07-lock.json`，带上运行时的 `git rev-parse HEAD`。不覆盖样本或 Batch2 的锁定文件。若扫描发现四块已经有人写过，停下来，不叠第二套标题。

来源清单写到 `docs/superpowers/plans/2026-10-25-batch3-01-02-05-07-source-list.json`，字段沿用 Batch2 清单：`chapters` 是 `["01", "02", "05", "07"]`，`absorb` 里每一条有 `license_class`、`url`、`do_not_copy`、`points`。`license_class` 只允许 `ST-facts-restated`、`MIT`、`BSD-2-Clause`、`BSD-3-Clause`、`ISC`、`CC BY 4.0`、`CC BY 3.0`、`CC0`。许可字符串里不得出现 `GPL`、`LGPL`、`CC BY-NC`、`CC BY-ND`、`All rights reserved`。清单可以先于 manifest 提交；登记以 manifest 为准。

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

订货号是 STM32F103C8T6，LQFP48。这一章回答「程序怎样进 Flash、复位后 CPU 先读哪两个字、探针接哪两只脚」。点灯电流留在第 03 章。

### 原理与边界

- **取向量。** 复位后 CPU 从 `0x00000000` 读 MSP，从 `0x00000004` 读 `Reset_Handler`。BOOT0=0 时，这两个地址是主闪存 `0x08000000` 的别名。这句整格沿用第 00 章和 `rm0008-boot`，此处只交叉引用。这颗料的 Flash 是 64 KB，从 `0x08000000` 起；SRAM 是 20 KB，从 `0x20000000` 起。链接脚本里的 `_estack` 是 `0x20005000`。互联型系统存储器 `0x1FFFB000` 在这颗料上作废，沿用第 00 章，不重画。
- **SWD 脚。** DS5319 Rev 20 图 8：LQFP48 第 34 脚是 PA13，第 37 脚是 PA14。RM0008 表 36 把它们标成 SWDIO 和 SWCLK。正常路径是探针的 SWDIO 接第 34 脚、SWCLK 接第 37 脚、GND 共地。章内接线表把 3.3 V 标成可选、5 V 标成不用。主图只画一条供电：板子自己的 3.3 V，探针只共地。不把探针 3.3 V 和板载 3.3 V 画成两只电源对顶。
- **失败路径。** Cube 的 SYS Debug 没有选 Serial Wire 时，PA13 和 PA14 变成普通 GPIO。配成推挽之后，探针驱动和引脚驱动接在同一根线上。本章接线表的四根线里没有串联电阻，主图按这张表来画。下一次连接失败。这不是第 00 章「BOOT0=1 所以没取到用户程序」的那一条。救砖可以按住 NRST 再连接，或把 BOOT0 拉高进系统存储器再擦除。BOOT 脚的锁存时刻仍以第 00 章为准，这一章不重算第 4 个 SYSCLK 上升沿。
- **读保护。** 本章已写 Level 0 选 `AA`，解除会全片擦除。只有 `rm0008-rdp` 按上一节的条件追加成功时，这句才进原理与边界和出处卡。否则 `AA` 留在动手实验。

CLion 和 PlatformIO 的菜单路径留在核心原理。四块不引用 JetBrains 或 PlatformIO 的句子当规范。

### 关键插图

主图文件 `assets/diagrams/sample-01-swd-connect.svg`，由 `tools/gen_sample_figures.py` 追加一个函数生成，调用 `_credit()`，不调用 `Svg.footer()`。

图上同时有这两条路径：

- **正常路径。** LQFP48 第 34 脚 PA13 = SWDIO，第 37 脚 PA14 = SWCLK，GND 共地。镜像写到 `0x08000000`，长度 64 KB。BOOT0=0。CPU 读 `0x00000000` 得到 MSP，读 `0x00000004` 得到 `Reset_Handler`。栈顶标注 `0x20005000`。
- **失败路径。** 同一对脚被配成推挽 GPIO。探针和引脚同时驱动 SWDIO，图上标出没有串联电阻。连接停在这一段。旁注写清：这不是 BOOT0=1 的系统存储器别名。

图注写「自绘」，写出第 34 脚、第 37 脚、`0x08000000`、`0x00000000`、`0x00000004`，以及 `ds5319-swd` 与 `rm0008-boot` 的文档号。替代文本写出结论：SWD 留在 PA13 和 PA14 才能再次连接；两只脚被配成推挽后探针和引脚抢同一根线。不写「示意图」。

`boot-sequence.svg` 留作辅图。关键插图写明：不播放它，主图仍然能指出失败发生在 PA13 那一段。

### 时序或状态

一张表，列对齐主图。至少包括：编译得到 ELF；烧录写入 `0x08000000`；复位；读 `0x00000000` 的 MSP；读 `0x00000004` 的复位向量；`SystemInit`；拷 `.data`、清 `.bss`；进入 `main`。失败行：PA13/PA14 为推挽，状态停在「探针无法连接」。连接失败本身不擦除已经写进 `0x08000000` 的镜像。另一行只交叉引用：BOOT0=1 且 BOOT1=0 时别名换成 `0x1FFFF000`，细节在第 00 章，这张表不重列第 4 个 SYSCLK 边沿。

### 坑与出处卡

至少这些行，每行一个主张：

| 现象 | 处理方向 | 链接 | 允许的主张 |
| --- | --- | --- | --- |
| 烧完一次就再也连不上 | SYS 保持 Serial Wire，PA13/PA14 留给 SWD | `#source-ds5319-swd` | LQFP48 第 34 脚是 PA13，第 37 脚是 PA14 |
| 线序对了仍报没有共地 | 接上 GND，再谈探针上的 3.3 V | `#source-ds5319-swd` | 只支持脚位：第 34 脚 PA13、第 37 脚 PA14。探针 3.3 V 可选是本章接线表的接法，不是这条来源的新电气限额 |
| 复位后停在 `main` 之前，向量却是对的 | 先看启动文件已经做完时钟、`.data` 和 `.bss` | `#source-rm0008-boot` | 字 0 是 MSP，字 1 才是复位入口。这句的适用范围仍是第 00 章那张表 9 |
| 程序在 Flash 里，复位却跑了别的 | 先核对 BOOT0，细节去第 00 章 | `#source-rm0008-boot` | 这颗料上 BOOT0=0 才别名到 `0x08000000` |

`rm0008-rdp` 追加成功时再加一行：解除读保护会擦除整片 Flash，链接 `#source-rm0008-rdp`。没追加就不写这一行。

「No such file」、固件升级、CMake 没继承环境变量，留在核心原理或动手实验。这些句子没有钉在 RM0008 或 DS5319 上。

### 短 GIF

辅图 `assets/gif/swd-connect.gif`。内容是正常路径的短循环：SWD 写入，复位，读出两个向量字。帧数不少于 3、不多于 12。它不画出推挽抢线的失败；那个失败只在静态主图上。不替换 `boot-sequence.svg`。

## 第 02 章写什么

订货号仍是 STM32F103C8T6，LQFP48。时钟账整格照抄附录 D，不另算一套「大约 72 MHz」。

### 原理与边界

三句边界都要写完，并且写明哪一句在换到互联型或换电压档时作废。

- **中密度的树。** HSE 从第 5 脚 PD0-OSC_IN、第 6 脚 PD1-OSC_OUT 进来，8 MHz。`PLLXTPRE=0`（HSE 不预分频），`PLLSRC=1`（PLL 入口是 HSE），`PLLMUL=0111`（×9）。`8 × 9 = 72` MHz。`SW=10` 时 SYSCLK 用 PLL。HPRE 取不分频，HCLK = 72 MHz。PPRE1 = `100`（÷2），PCLK1 = 36 MHz，不得超过 36 MHz。PPRE2 取不分频，PCLK2 = 72 MHz。APB 预分频不是 1 时，挂在那条总线上的定时器时钟再 ×2，所以 TIM2–TIM7 仍是 72 MHz。TIM1 在 APB2，预分频为 1，不再 ×2。这些句子与附录 D 同一笔。
- **等待周期。** `FLASH_ACR` 偏移 `0x00`，基址 `0x40022000`。LATENCY 在 48 MHz 到 72 MHz 这一档是 `010`，也就是 2。0–24 MHz 是 0，24–48 MHz 是 1。电压档整格照抄附录 D：2.7–3.6 V。只把 PLL 改成 ×9、LATENCY 还留在 0，取指会错。这句是主图的失败路径。
- **USB 与 ADC 只保留分频格。** `USBPRE=0` 时 72 MHz 的 PLL 再 ÷1.5，得到 48 MHz。`USBPRE=1` 是不除，得到 72 MHz，不是 48 MHz。`ADCPRE=10` 是 PCLK2÷6，`72 / 6 = 12` MHz。`ADCPRE=01` 是 ÷4，得到 18 MHz，越过 RM0008 的 14 MHz 上限。21 µs 和采样档留在第 09 章，这一章不写。
- **CSS。** HSE 停振且 CSS 已开时，若 HSE 直接或经 PLL 当系统时钟，硬件改用 HSI，并关掉 HSE；HSE 若是 PLL 入口，PLL 也关掉。CSS 中断接在 NMI 上。NMI 里要写 `RCC_CIR` 的 CSSC，否则 NMI 会一直进来。同一事件还送到 TIM1 和 TIM8 的刹车输入。上电默认系统时钟是 HSI 8 MHz，不是 Cube 里填的 72 MHz。第 04 章只交叉引用「CSS 进 NMI」，不在这一章重画抢占。
- **MCO。** 第 29 脚 PA8 的复用含 MCO。`MCO=111` 送出 PLL÷2，也就是 36 MHz，低于手册写的 50 MHz I/O 上限。`MCO=100` 把 SYSCLK 送出去时，72 MHz 越过这句 50 MHz。正常路径画 36 MHz，失败旁注画「SYSCLK 直接送 MCO」。
- **互联型作废。** 第 8.3.2 节的 `OTGFSPRE`、`PLLMUL` 的 `000x` 保留、以及 ×6.5，在 STM32F103C8T6 上作废。正文现在的「RM0008 第 8.3.2 节」改成第 7.3.2 节。HSE bypass 只用于外部时钟，无源晶振不开 bypass。

系列对比表里的人民币价格留在核心原理，标明不是数据手册的数。不进四块，不进新来源的 scope。

### 关键插图

主图文件 `assets/diagrams/sample-02-clock-tree.svg`，同样由 `gen_sample_figures.py` 生成，用 `_credit()`，不调用 `Svg.footer()`。

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
- **脚。** 默认不重映射时 TIM3_CH1 在 PA6。DS5319 Rev 20 表 5：LQFP48 第 16 脚是 PA6，默认复用含 TIM3_CH1。重映射到 PB4 或 PC6 要另写 `TIM3_REMAP`，不画进正常路径。
- **MOE。** TIM1/TIM8 的 `TIMx_BDTR` 偏移 `0x44`，复位值 `0x0000`，位 15 MOE 为 0 时主输出关着。`HAL_TIM_PWM_Start` 会置 MOE。通用定时器 TIM3 没有这一位。`DeadTime = 0x10` 不进四块，也不换算成纳秒。

### 关键插图

主图文件 `assets/diagrams/sample-05-pwm-1khz.svg`。

图上是一路 PWM：

- 脚位：LQFP48 第 16 脚 PA6 = TIM3_CH1。计数时钟 72 MHz。PSC = 71，ARR = 999，CCR = 500。
- **正常路径。** 周期 1 ms，高电平 500 µs，频率 1000 Hz。CNT 从 0 数到 999，CNT < 500 时输出为高。
- **失败路径。** 同一组 PSC、ARR、CCR，去除时用了 36 MHz。周期变成 2 ms，频率 500 Hz。图上标出多出来的那一倍来自「把 PCLK1 当成了定时器时钟」。
- **旁注。** ARR = 999999 在 16 位计数器里装不下。TIM1 的 MOE 位 15 复位为 0，那是另一只定时器，不占 PA6 这条波形。

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

## 第 07 章写什么

订货号仍是 STM32F103C8T6。I2C1 在 APB1，PCLK1 = 36 MHz。短总线的上拉整格照抄附录 D：4.7 kΩ 到 3.3 V。

### 原理与边界

- **电流路径。** SCL 和 SDA 都是开漏。高电平来自 3.3 V 经 4.7 kΩ 到脚，低电平是脚内 NMOS 灌电流到地。有器件把线拉低时，这一路上的电流是 `3.3 / 4700 ≈ 0.702` mA。片内上拉约 30–50 kΩ：30 kΩ 时约 110 µA，50 kΩ 时约 66 µA。这股电流撑不起 400 kHz 所要求的上升时间。正常路径画外部 4.7 kΩ。失败路径画只开片内上拉。
- **地址。** SSD1306 的 7 位地址是 `0x3C`。HAL 的 DevAddress 填 `0x3C << 1`，也就是 `0x78`。地址字节的位型是 `01111000`，最低位 0 表示写。第 9 个 SCL 上，从机把 SDA 拉低才是 ACK。把 `0x3C` 原样填进 HAL 时，总线上的地址字节不是 `0x78`，第 9 拍 SDA 保持高，这是 NACK。
- **速率。** `I2C_CR2` 的 FREQ 填 36。标准模式 100 kHz：`CCR = 36e6 / (2 × 100000) = 180`，`fSCL = PCLK1 / (2 × CCR)`。快速模式、DUTY = 0（本章的 `I2C_DUTYCYCLE_2`，低电平是高电平的两倍）：`CCR = 36e6 / (3 × 400000) = 30`，`36e6 / (3 × 30) = 400000`。DUTY = 1（16/9）时分母是 `25 × CCR`，`36e6 / (25 × 400000) = 3.6`，不是整数。不把 3.6 四舍五入成 4，也不把这一档说成误差为 0 的 400 kHz。
- **TRISE。** 标准模式最大上升时间 1000 ns，`TRISE = 36 + 1 = 37`。快速模式最大上升时间 300 ns，`TRISE = (36 × 300) / 1000 + 1`，整数除法得到 11。正文那句把 300 ns 标成标准模式的，改成：300 ns 属于 400 kHz，1000 ns 属于 100 kHz。不新编一个总线电容的皮法来代进 `Rp(max)`。
- **脚。** 复位后 I2C1 的 SCL 是 PB6、SDA 是 PB7。DS5319 Rev 20：LQFP48 第 42 脚 PB6，第 43 脚 PB7。重映射到 PB8/PB9 不画进正常路径。
- **重复起始。** 读寄存器时，写完寄存器地址之后是重复起始：SCL 为高时 SDA 下降，中间没有 STOP。STOP 是 SCL 为高时 SDA 上升。`HAL_I2C_Mem_Read` 走重复起始。先 `Master_Transmit` 再 `Master_Receive` 会在中间插入 STOP。

若 RM0008 第 26.6.8 节印了「快速模式要求 PCLK1 是 10 MHz 的整数倍」，这句和 DUTY = 1 的 16/9 放在一起读。DUTY = 0、CCR = 30 这一档的算式仍然是 400 kHz。36 MHz 整段不因此被写成不能使用快速模式。

「F1 硬件 I2C 偶发死锁」钉不住勘误文档号时，不新开勘误 id。出处卡里对应的一行写成经验线索，不引入新的寄存器值。能写进规范主张的是：从机拉住 SDA 时，主机在 SCL 上补时钟，把从机状态机推完，再发 STOP，然后重新初始化。

### 关键插图

主图文件 `assets/diagrams/sample-07-i2c-ack.svg`。

图上是一次地址字节：

- 脚位：LQFP48 第 42 脚 PB6 = SCL，第 43 脚 PB7 = SDA。两根线各有一只 4.7 kΩ 接到 3.3 V。灌电流标注 `0.702 mA`。
- **正常路径。** 地址字节 `0x78`，LSB 先看到的是 R/W = 0。第 9 个 SCL 上 SDA 为低，ACK。旁边写 CCR = 30，400 kHz，TRISE = 11。
- **失败路径。** DevAddress 填了 `0x3C`。第 9 拍 SDA 保持高，NACK。另一条短标注：上拉换成片内 30 kΩ 时约 110 µA，50 kΩ 时约 66 µA，400 kHz 的上升时间不够。
- **旁注。** 重复起始是 SCL 高时 SDA 下降。STOP 是 SCL 高时 SDA 上升。不把 PB8/PB9 画进正常路径。

图注写「自绘」，带 RM0008 Rev 21 第 26.6.8 节、第 26.6.9 节和 DS5319 Rev 20 表 5。替代文本写出结论：HAL 要填 `0x78`，第 9 拍 SDA 为低才是 ACK；4.7 kΩ 上拉在拉低时约 0.702 mA。不写「示意图」。

`i2c-transaction.svg` 和 `i2c-timing.gif` 留在原节，标成辅图。

### 时序或状态

一张表覆盖地址字节的 9 个 SCL。列至少有：SCL 拍号、SDA 电平、含义。正常行的 8 位是 `0x78` 的从高位到低位（I2C 高位先出），第 9 拍 SDA 为低，结果 ACK。失败行第 9 拍 SDA 为高，结果 NACK，并写明 DevAddress 填成了 `0x3C`。速率行：CCR = 30 时 400 kHz，TRISE = 11；CCR = 180 时 100 kHz，TRISE = 37。电流行：4.7 kΩ 为 0.702 mA；30 kΩ 为 110 µA；50 kΩ 为 66 µA。

重复起始单独一行：SCL 为高，SDA 下降，没有 STOP。

### 坑与出处卡

至少这些行：

| 现象 | 处理方向 | 链接 | 允许的主张 |
| --- | --- | --- | --- |
| 扫描到 `0x3C`，HAL 却 NACK | DevAddress 填 `0x78` | `#source-rm0008-i2c` | 7 位 `0x3C` 左移一位是 `0x78`。第 9 拍 SDA 为低才是 ACK |
| 只开片内上拉，400 kHz 不稳定 | 外接 4.7 kΩ 到 3.3 V | `#source-rm0008-i2c` | 片内约 30–50 kΩ。4.7 kΩ 拉低时约 0.702 mA。不支持把 300 ns 说成标准模式 |
| 读寄存器得到的是别的地址 | 中间用重复起始，不用 STOP 再 START | `#source-rm0008-i2c` | 重复起始是 SCL 为高时 SDA 下降 |
| 波形在 PB8/PB9 上找 I2C1 | 复位后的默认脚是 PB6/PB7 | `#source-ds5319-i2c` | LQFP48 第 42 脚是 PB6，第 43 脚是 PB7 |
| CCR 按 16/9 去凑 400 kHz，除不尽 | 这颗料的 36 MHz 用 DUTY = 0，CCR = 30 | `#source-rm0008-i2c` | `36e6 / (3 × 30) = 400000`。16/9 那一档得到 3.6，不是整数 |

总线被拉死时补时钟的那一行：钉得住 RM0008 的时钟拉伸或 BUSY 时，链接 `#source-rm0008-i2c`，主张只写「从机可以拉住 SCL，主机要等」。9 个 GPIO 脉冲若只是本章例程里的做法，就另起一行，主张写成经验线索，不引入新的微秒数。EEPROM 的 5 ms 写周期没有钉在 RM0008 上，留在动手实验。

### 短 GIF

辅图 `assets/gif/i2c-ack.gif`。内容是地址字节 `0x78` 的 9 拍，第 9 拍 SDA 被拉低，标出 ACK 和 0.702 mA。帧数不少于 3、不多于 12。NACK 和片内上拉的失败只在静态主图上。不替换 `i2c-timing.gif`。

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

PDF 关掉动画之后，读者只看静态主图和图注，就能指出失败发生在哪一段。第 01 章是「PA13 被配成推挽，探针和引脚抢同一根线」。第 02 章是「72 MHz 时 LATENCY 仍为 0」。第 05 章是「用 36 MHz 去除，1 kHz 变成 500 Hz」。第 07 章是「第 9 拍 SDA 仍为高，NACK」。

## 工作流与 PR 节奏

### 本 PR（设计）

只新增本文件。不改 `docs/01`、`docs/02`、`docs/05`、`docs/07`、`docs/en/` 的章节、`stm32-book/`、`CREDITS.md`、`assets/`、`tools/`。不升版本，不打 tag，不发 Release。不新增 `docs/superpowers/plans/` 下的实施计划。本 PR 等人审阅规格后再合入，不在 CI 变绿后自动合。

### 实施 PR（下一轮，不在本 PR）

顺序固定：

1. **核对扫描。** 写出 `2026-10-25-batch3-01-02-05-07-lock.json`。章号保持 01、02、05、07。
2. **许可门。** 写出 `2026-10-25-batch3-01-02-05-07-source-list.json`。先有清单，再改正文。
3. **静态主图和短 GIF。** 先提交 SVG、GIF 和生成脚本，再写正文。主图不依赖 GIF。
4. **中英加厚。** 八份 Markdown 一起提交。
5. **登记。** 新来源追加进两份 manifest。更新这四章罗盘的来源数组。`CREDITS.md` 第六节增加 v1.2.2 小节。`revisions.json` 在条目最前加上 1.2.2，日期写死 `2026-10-25`。两份 manifest 的 `version` 改为 `1.2.2`，`date` 改为 `2026-10-25`。`stm32-book/README.md` 的当前版本句改为 **v1.2.2 · 2026-10-25**。发布一节里的 tag 名改成 `v1.2.2`，并在现有「也不要把 1.2.0 的产物标成 1.2.1」之后加上「也不要把 1.2.1 的产物标成 1.2.2」。这一步仍不创建 tag，也不创建 Release。修订说明只写这四章加厚了什么，用文件名前缀，不写尚未做的章。中英各两句，例如：第 01 章写上 SWD 在 LQFP48 第 34 脚和第 37 脚，以及推挽抢线的失败；第 02 章把 CFGR 改回第 7.3.2 节，并写上 72 MHz 要 2 个等待、CSS 回到 HSI。第 05 章写上 1 kHz 和 500 Hz 两条路径。第 07 章写上 `0x78`、第 9 拍 ACK 和 4.7 kΩ 的 0.702 mA。英文用同样的事实。
6. **测试。** 新增 `stm32-book/tests/test_batch3_chapters.py` 和 `stm32-book/tests/test_batch3_sources.py`，照着 Batch2 测试检查四块、共享数字、主图禁词和许可门。不放宽 `test_sample_chapters.py` 和 `test_batch2_chapters.py`。`test_build.py` 里当前版本从 `1.2.1` 改为 `1.2.2`：`assert_version_history_and_index` 的元组在 `1.2.1` 之前加上 `1.2.2`；修订列表以 `1.2.2` 起头；两份整书 HTML 的 `<strong>v1.2.2</strong>`；`test_visual_polish_version_is_1_2_0` 改为核对当前条目是 1.2.2，日期是 2026-10-25，1.2.1 那两句指南说明改去核对 `entries[1]`。不删 `0x271`、`167 ns`、账本名和出版书签长度为 44 的断言。不新增读取 `CONTENT_GUIDE.md` 的测试。
7. **CI 变绿之后停下来等人复审。** 复审对象是构建出的中英 HTML 里的这四章。人接受之前不合入，也不开下一批章。Book CI 变绿不等于可以自动 squash 合入。

实施 PR 的 diff 可以碰这四章中英正文、两份 manifest 的新 `sources` 和这四章罗盘、新图与生成脚本、`assets/README.md`、`CREDITS.md`、版本与修订、新的锁定文件和来源清单、新测试，以及 `test_build.py` 里的版本字符串。不碰其余章的正文，不改 `build_html.py`。

## 验收

### 本设计 PR

- 新增文件只有 `docs/superpowers/specs/2026-10-25-classic-encyclopedia-batch3-01-02-05-07-design.md`。
- 章节、`stm32-book/`、资产、工具和 `CREDITS.md` 与基线 `b2a4f26` 相同。
- 没有新的 SVG 或 GIF，版本号仍是 1.2.1。没有实施计划文件。

### 实施 PR

- 中文四章各有且仅有一次：`## 原理与边界`、`## 关键插图`、`## 时序或状态`、`## 坑与出处卡`。英文对应四个标题同样各一次。
- 四章都不再有 `## ⚠️ 常见坑与排查` 或 `## ⚠️ Pitfalls and troubleshooting`。
- 每章关键插图的第一张图是对应的静态 SVG。图上能看出正常路径和失败路径。GIF 不是这一节唯一的图。
- 中英都有这些数字，而且彼此一致：
  - 第 01 章：`34`、`37`、`PA13`、`PA14`、`0x08000000`、`0x00000000`、`0x00000004`、`0x20005000`。
  - 第 02 章：`7.3.2`、`0111`、`72`、`36`、`12`、`18`、`14`、`48`、`50`、`8`、LATENCY `2`、`CSSC`、第 5 脚、第 6 脚、第 29 脚。正文不再把这颗 C8 的 CFGR 说成第 8.3.2 节。
  - 第 05 章：`PSC` `71`、`ARR` `999`、`CCR` `500`、`1000`、`500` Hz、`16`、`999999`、`7199`、`9999`、第 16 脚、`PA6`、`MOE`、`0x44`。
  - 第 07 章：`0x3C`、`0x78`、`4.7`、`0.702`、`30`、`50`、`110`、`66`、`CCR` `30`、`180`、`TRISE` `11`、`37`、第 42 脚、第 43 脚、`PB6`、`PB7`。
- 第 02 章和第 05 章、第 07 章引用附录 D 的格子时整格照抄，不改附录 D 正文。
- 静态 SVG 小于 60 KB，不含动画标记，含「自绘」，不含「实拍」和「矢量动画」。四条新 GIF 小于 500 KB，并且在 `BUILDERS` 里。
- 新 `#source-` 都能在构建出的 HTML 里找到 `id="source-..."`。已有 `rm0008-boot`、`rm0008-gpio`、`ds5319-gpio`、`rm0008`、`ds5319` 的对象与基线逐字段相同。
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

1. **读保护字节。** 只有 RM0008 Rev 21 印出的无保护值就是 `AA` 且写明解除会擦除时，才追加 `rm0008-rdp`。对不齐就只留在动手实验。
2. **快速模式与 10 MHz。** 第 26.6.8 节若把「10 MHz 的整数倍」和 DUTY = 1 写在一起，DUTY = 0、CCR = 30 的 400 kHz 仍然成立。不把 3.6 收成整数。
3. **9 个 SCL 脉冲。** 钉得住手册才进规范主张。钉不住就保持经验线索，不新编脉宽。
4. **主图体积。** 先拆图。拆开仍超过 60 KB 时在实施 PR 里说明，不降低画法标准。
5. **图目录。** 这一批不加。
6. **下一批章号。** 仍是 4 章，到下一次设计再锁。本文件不预选 `08` 或 `09`。

## 英文提要

Thicken only chapter files 01 (development setup), 02 (part, memory, and the clock tree), 05 (timers and PWM), and 07 (I2C), in Chinese and English, on top of v1.2.1 (`b2a4f26`, PR #29). GPIO current stays in chapter 03. The ADC conversion-time ledger stays in chapter 09. Use the same four sections as chapters 00, 03, 04, and 06. Each chapter gets one printable static SVG from `gen_sample_figures.py`, with a normal path and a failure path, and no `Svg.footer()`. Chapter 01 draws SWD on LQFP48 pins 34 and 37 and the failure where those pins, configured as push-pull, fight the probe. Chapter 02 draws the medium-density tree in RM0008 section 7.3.2: HSE 8 MHz times 9 is 72 MHz with two Flash wait states, and CSS falls back to HSI at 8 MHz. Section 8.3.2 is void on STM32F103C8T6. Chapter 05 draws TIM3 CH1 on pin 16 PA6 at 1 kHz (PSC 71, ARR 999, CCR 500) and the 500 Hz failure that comes from dividing by 36 MHz. Chapter 07 draws I2C1 on pins 42 and 43, address byte `0x78`, ACK on the 9th clock, and 0.702 mA through 4.7 kΩ; a NACK and the on-chip pull-up are the failure. One short GIF per chapter is auxiliary only. Register new sources by appending ids. Bump the book to 1.2.2 on 2026-10-25 during implementation, do not tag or release, and stop for human review before squash-merge. This design PR only adds this file.

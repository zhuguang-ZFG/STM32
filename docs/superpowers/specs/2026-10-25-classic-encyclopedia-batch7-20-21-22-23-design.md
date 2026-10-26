# 第 20、21、22、23 章加厚设计

日期：2026-10-25  
状态：待人审。人接受这份规格之前不实施  
基线：`main` 上的整书 **v1.3.1**（`ef5a0884f159790d1bb03627722b889cfc4b2b02`，PR #59，2026-10-25）  
上一份设计：[2026-10-25-classic-encyclopedia-batch6-16-17-18-19-design.md](2026-10-25-classic-encyclopedia-batch6-16-17-18-19-design.md)（PR #57）。四块模板来自 [2026-10-25-classic-encyclopedia-thicken-design.md](2026-10-25-classic-encyclopedia-thicken-design.md)（PR #18）。密度刀 F 是 [2026-10-25-book-density-F-design.md](2026-10-25-book-density-F-design.md)，已经在 1.2.8 收过空白。  
本文件只记录这一批的设计。它不改章节正文，不画新图，不改 `stm32-book/` 构建，不升版本号，不打 tag，不发布 Release，不写实施计划。

章号按文件名前缀锁死，不按主题改名。文件 `20` 是学习资源与工具链，文件 `21` 是原理图与实物图鉴，文件 `22` 是仿真实验：Wokwi 与 Renode，文件 `23` 是 STM32G0 引脚（G071RB）。任务单里的「原理图与实物图注」不是仓库里的标题，一级标题继续是 `21 原理图与实物图鉴`，英文继续是 `21 Schematics and board maps`，文件继续是 `docs/21-原理图与实物图鉴.md` 和 `docs/en/21-board-maps.md`。任务单里的「仿真实战 Wokwi 与 Renode」也不是仓库里的标题，一级标题继续是 `22 仿真实验：Wokwi 与 Renode`（冒号是全角 `：`），英文继续是 `22 Simulation labs: Wokwi and Renode`，文件继续是 `docs/22-仿真实验Wokwi与Renode.md` 和 `docs/en/22-simulation-wokwi-renode.md`。第 23 章的一级标题继续带 `（G071RB）`，英文继续带 `(G071RB)`。不要把这一批改名，也不要写成第 28 章的 RTOS 生态。

## 背景

v1.3.1 已经按大典四块加厚的是第 00 到第 19 章。这一批只加厚另外四章，中文和英文一起写：

| 文件前缀 | 中文 | 英文 | 这一章在讲 |
| --- | --- | --- | --- |
| `20` | `docs/20-学习资源与工具链.md` | `docs/en/20-resources.md` | 先选哪一本手册；PM0056 不是封装手册；读允许键是 `0xA5` |
| `21` | `docs/21-原理图与实物图鉴.md` | `docs/en/21-board-maps.md` | 先认订货号。C8 读 `0x410` 和 64 KB；ZET6 不在 DS5319 |
| `22` | `docs/22-仿真实验Wokwi与Renode.md` | `docs/en/22-simulation-wokwi-renode.md` | 仿真键名要指到真脚；灯亮不能证明波特率 |
| `23` | `docs/23-STM32G0引脚.md` | `docs/en/23-stm32g0-pins.md` | LQFP64 第 1 脚是 PC11；PA14 与 SWCLK 是同一只脚 |

读者看到的章号仍是文件名前缀加 1：文件 `20` 在书里是第 21 章，`21` 是第 22 章，`22` 是第 23 章，`23` 是第 24 章。源文件的一级标题继续带 `20`、`21`、`22`、`23`。这一批不改这个加 1。

第 02 章已经钉过上电 HSI 是 8 MHz，HSE 8 MHz 乘 9 是 72 MHz。第 03 章已经钉过第 10 脚 PA0 上的外接灯串 270 Ω，第 2 脚 PC13 只允许灌电流。第 05 章已经钉过 TIM3：计数时钟 72 MHz，PSC = 71，ARR = 999，CCR = 500，`72e6 / ((71+1) × (999+1)) = 1000` Hz，高电平 500 µs。第 06 章已经钉过 USART1 在第 30 脚 PA9、第 31 脚 PA10，BRR `0x271`，72 MHz 下 115200，8 MHz 下 12800。第 07 章已经钉过 7 位 `0x3C`，HAL 填 `0x78`，上拉 4.7 kΩ。第 11 章已经钉过 LSE 32.768 kHz、第 3 脚和第 4 脚、第 1 脚 VBAT。第 17 章已经钉过 `CFSR` 在 `0xE000ED28`。第 18 章已经钉过 LSE 电容是 5 pF 到 15 pF，6 pF 不是必须值，以及第 7 脚上图 31 的 0.1 µF。这几张图都不重画。167 ns、21 µs、17.2%、14 µA、24 µA 不进这四章的四块。

对照 v1.3.1 核对过的事实：

1. **这四章还没有四块。** 已经加厚的章在 `<!-- /video: -->` 之后、学习目标之前，有 `## 原理与边界`、`## 关键插图`、`## 时序或状态`、`## 坑与出处卡`（英文是 `Principle and boundary`、`Key figures`、`Timing or state`、`Pitfalls and source cards`）。这四章仍从学习目标写起。第 20 章和第 21 章的中文坑还在 `## ⚠️ 常见坑与排查`。第 20 章的英文坑是 `## ⚠️ Common traps and how to check them`，第 21 章的英文坑是 `## ⚠️ Pitfalls`。它们都要删。仓库里没有 `## ⚠️ Pitfalls and troubleshooting` 这行英文，不要为了删它先造出来。第 22 章的坑标题是 `## ⚠️ 仿真替不了的事` 和 `## ⚠️ What simulation will not do for you`。第 23 章的坑标题是 `## ⚠️ 从 F1 抄代码时最容易摔的几处` 和 `## ⚠️ Common ways an F1 port falls over`。这两章没有「常见坑」那个旧标题，保留现有标题，只把和四块冲突的格子改成同一笔账。
2. **第 20 章把 PM 写成了封装手册，并把读保护键写成了 `0xAA`。** 视频旁白说的是编程手册。正文表格却写「PM = Product/Package Manual」，英文同一句。已经冻住的 `pm0056` 标题是 *STM32F10xxx Cortex-M3 Programming Manual*。`CFSR` 在 `0xE000ED28`，这是编程手册里的数，不在 DS5319 的引脚表里。示例 1 把频率写成 `fCK_CNT / (ARR+1)`，把 `(PSC+1)` 丢了。第 05 章的同一组数是 PSC = 71、ARR = 999、CCR = 500。丢掉 `(PSC+1)` 时，`72e6 / (999+1) = 72000` Hz，不是 1000 Hz。示例 3 用 AN4031 的 FIFO 和突发去回答 F103。那份笔记讲的是 F2/F4 的 DMA。这颗 C8 的 DMA 没有那只 FIFO。代码块里的 `STM32_Programmer_CLI -ob RDP=0xAA` 把 `0xAA` 放在了读保护的位置。`pm0075-rdp` 已经写明：选项字节在 `0x1FFFF800`，读允许键的低字节是 `0xA5`，手册印成 `0x00A5`；写回这个键会先整片擦除主闪存；snapshot 不使用 `0xAA`。三件套「覆盖 90% 场景」不是测量。预算表里的人民币区间不是手册格子。OpenOCD 的 `3333` 留在代码节，不进四块。
3. **第 21 章用一张启动表覆盖了四颗不同的料，并把电容和电阻写成了必须值。** C8 的身份已经在附录 D：`DBGMCU_IDCODE` 在 `0xE0042000`，中容量 DevID 是 `0x410`，容量在 `0x1FFFF7E0` 的低 16 位，单位 KB，DS5319 是 64 KB 闪存和 20 KB SRAM。UID 在 `0x1FFFF7E8`，96 位。丝印写 128 KB、读数却不是 64 时，不要按 C8 往下算。ZET6 不在 DS5319。DS5792 的 xE 行是 512 KB 闪存、64 KB SRAM、72 MHz、LQFP144。C8 的系统存储器是 `0x1FFFF000`。大容量 F103 的系统存储器默认是 `0x1FFFB000`，和互联型同一个起点，但那是另一行，不是「C8 上作废」的同义词。本章那张 BOOT 表把 `0x1FFFF000` 写成了所有板的系统存储器，在 ZET6 上作废。F411CEU6 和 F411RET6 是 DS10314 的 xE：512 KB 闪存、128 KB SRAM、最高 100 MHz。xC 的闪存是 256 KB，在这两只订货号上作废。正文「HSE 8 MHz，PLLM=8/N=200/P=2」的算术是 `8/8×200/2 = 100`，但这三个乘数不是 DS10314 印出的格子，不进四块。BlackPill 的 25 MHz 是板级说法。DS10314 的晶振范围是 4 MHz 到 26 MHz，25 落在范围里，仍不把它写成数据手册替这只板选的频率，也不编它的 PLL。F407VGT6 在 DS8626：最高 1 MB 闪存、最高 168 MHz、SRAM 最高 192 KB（里面包含 64 KB CCM）再加 4 KB 备份 SRAM。正文「1 MB / 192 KB」把那 4 KB 漏了。4 KB 不属于那 192。最小系统表把 LSE 写成 `2×6 pF`，和第 18 章冲突。HSE 写成 `2×20 pF`。20 pF 不是必须值。NRST 写成「10 kΩ 上拉 + 100 nF」。外部电容跟图 31 是 0.1 µF。10 kΩ 不进出处卡。接线总览把外接灯写成 PA5 加 330 Ω。本书的外接灯仍是第 10 脚和 270 Ω。330 Ω 不进四块。
4. **第 22 章的键名和时钟还没有跟已经冻住的脚、地址对上。** Wokwi 图里的键是 `C13`、`A0`、`A9`，不是 `PC13`、`PA0`、`PA9`。`C13` 指到第 2 脚 PC13，板载灯低电平亮，这只脚只能灌电流。`A0` 指到第 10 脚 PA0。这只脚同时还是第 03 章的灯、第 09 章的 ADC 和第 16 章的 WKUP。主图只标键名到脚号，不把灯、ADC 和按键画成同时有效。`A9`/`A10` 指到第 30 脚和第 31 脚。USART1 的基址是 `0x40013800`，GPIOC 的基址是 `0x40011000`。把 `usart1` 说成 USART2，是失败路径。灯会闪，只证明 GPIO 在动。BRR 若仍是 `0x271`，72 MHz 上是 115200，8 MHz 上是 12800。OLED 的 7 位地址是 `0x3C`，HAL 填 `0x78`，上拉是 4.7 kΩ，跟第 07 章同一笔。当前这页写明 Wokwi 的 BluePill 模型没有 DMA。空闲帧收包和 ADC 的 DMA 搬运在这个模型里跑不完。这是模型边界，不是新的电气限额。`sim/renode/uart-usart1.resc` 打开本机端口 3456。仓库许可把 MIT 划给 `examples/`、`tools/`、构建脚本、测试和文档里的代码片段，没有把 `sim/` 划进去。3456 留在动手实验，不进出处卡，也不新开 id。Wokwi 与 Renode 已有来源的许可字符串不在可吸收名单里，对象一个字段都不改。
5. **第 23 章的脚号已经能在 DS12232 Rev 5 上对上，待机电流仍然不写。** STM32G071RB：R 是 64 脚，B 是 128 KB 闪存。Table 2 的 SRAM 是 32 KB（带硬件奇偶）或 36 KB（不用奇偶）。封面的 36 KB 是不用奇偶的那一格，不是 32 加 36。最高 64 MHz，Cortex-M0+，供电 1.7 V 到 3.6 V。LQFP64 第 1 脚是 PC11，第 6 脚才是 VBAT，第 12 脚是 PF2-NRST，第 3 脚是 PC13。Table 12 注 1：PC13、PC14、PC15 经过电源开关，开关只能灌大约 3 mA；输出速度不超过 2 MHz，负载不超过 30 pF；这三只脚不能当电流源，例如不能拿去点灯。注 6：复位后 PA13 内部上拉、PA14 内部下拉，并进入 SWD。第 45 脚是 PA13，第 46 脚是 PA14-BOOT0。没有 CAN。USB 是 UCPD，不是 F1 的全速设备。第 36 脚 PA8 的附加功能是 UCPD1_CC1，第 35 脚 PB15 是 UCPD1_CC2。启动配置仍在第四个 SYSCLK 上升沿锁存。`BOOT_LOCK=1` 强制主闪存。空闪存还可以转入系统 Bootloader。本章封面故意不写待机微安，四块也不补一个微安。
6. **许可门与已有 id 保持原样。** 允许吸收的仍是 ST 手册里的事实（自己的话重写），以及 MIT、BSD-2-Clause、BSD-3-Clause、ISC、CC BY 4.0、CC BY 3.0、CC0。GPL、LGPL、CC BY-NC、CC BY-ND、Apache-2.0、保留所有权利、未写许可的材料只留链接。正点原子、野火、CSDN、Wokwi 文档、Renode 文档、WeAct 仓库都在这一层，除非实施时打开的许可证落在可吸收名单里。落不进去就不新开 id。`sources` 只追加。已有 id 一个字段都不改。
7. **全 29 章最终都要加厚。** 本批只规格化文件 `20`、`21`、`22`、`23`。再下一批仍是 4 章，章号到那时再锁。本文件不预选文件 `24` 或 `28`。密度刀 F 已经收过阅读面空白。这一批只加内容的密度，不加另一刀 CSS。少留空白靠把四块写成能算回去的表，不靠改字号和页边。

## 目标与非目标

### 目标

- 只把第 20、21、22、23 章加厚到和第 00 到第 19 章相同的四块密度。中文和英文一起写完。句子写实，图上能指出哪一段是错的。
- 每章一张可印刷的静态主图：正常路径和失败路径都在图上，文档号、地址、脚位和容量是真的。另加一条短 GIF，只做网页和公众号辅图。图注写「自绘」。
- 每章锁四笔账，数字来自已经打开的手册或本仓库已经冻住的格子。第 20 章：PM0056 是编程手册；PSC = 71 时丢掉 `(PSC+1)` 会得到 72000 Hz；读允许键是 `0xA5`；第 30 脚和 `0x271` 分属两本手册。第 21 章：`0x410` 与 64 KB；ZET6 是 512 KB / 64 KB，系统存储器不是 `0x1FFFF000`；F411xE 是 512 KB / 128 KB / 100 MHz；F407VG 是 1 MB、168 MHz、192 KB 再加 4 KB。第 22 章：USART1 在 `0x40013800`；GPIOC 在 `0x40011000`，第 2 脚是 PC13；`0x271` 在 8 MHz 上是 12800；I2C 是 `0x3C` 与 `0x78`。第 23 章：第 1 脚 PC11、第 12 脚 PF2-NRST；SRAM 32 KB 或 36 KB；PC13 到 PC15 大约 3 mA、2 MHz、30 pF；第 46 脚 PA14 与 SWCLK 共用。
- 新出处追加进两份 manifest 的 `sources`。章内坑卡使用 `#source-...`。`CREDITS.md` 第六节记下这一批改写吸收了什么。
- 实施合入时把整书从 1.3.1 升到 **1.3.2 · 2026-10-25**。中英文共用这个版本号和这个日期。仓库里现有修订条目的日期都是 2026-10-25，本文件名也是这一天。代理日历若显示 2026-10-26，书的日期仍写 2026-10-25，不另起一天。不写成 1.3.1.1。这一批不打 tag，不创建 Release。
- 实施 PR 在 Book CI 变绿之后停下来等人复审。人接受之前不合入。Book CI 变绿不等于自动 squash 合入。

### 非目标

- 不加厚除 20、21、22、23 以外的任何章。已经加厚的 00 到 19 保持原样。文件 `28` 的 RTOS 生态不进本批。不把 167 ns、21 µs、17.2%、14 µA、24 µA 写进这四章的四块。
- 不重画 `sample-00` 到 `sample-19` 的任何主图，也不重画 `project-structure.svg`、`assets/boards/` 下已有的 7 张板图和 `pinout-stm32g071rb-lqfp64.svg`、`assets/animations/toolchain-flow.svg`、`assets/animations/g0-boot-swd.svg`。第 20 章不重画第 05 章的 PWM，也不重画第 17 章的 CFSR。第 21 章不重画第 18 章的 BOOT0 图。第 22 章不重画第 06 章的位帧和第 07 章的地址字节。第 23 章不重画已有的 64 脚引脚全图，主图只钉这一次要核对的脚。
- 不改密度刀 F 的令牌、`book.css` 和间距。不把样式、字号、行长或页边再收一刀。不改 `stm32-book/build_html.py`。
- 不重画 29 张讲解海报，不改 `assets/video/` 里的 png、mp4、srt，不改 `tools/gen_narrated.py`。`<!-- video: -->` 与 `<!-- /video: -->` 之间的旁白保持原样。旁白不重录。旁白里若仍把 PM 说成别的书，也不在这一批改字幕。
- 不重选样本，不改 `docs/superpowers/plans/` 里已有的锁定文件和来源清单。不改 `tools/scan_sample_chapters.py`，也不改 `scan_batch2` 到 `scan_batch6`。本设计 PR 不新增实施计划。
- 不改总纲、Batch2 到 Batch6 的规格、观感规格、海报规格、密度规格、CONTENT_GUIDE 规格，也不改两份 `CONTENT_GUIDE.md`。
- 不实现 v1.3.1 或 v1.3.2 的 GitHub Release，也不打 `v1.3.1` 或 `v1.3.2` 的 tag。
- 出版书签仍是现在的 44 条。不把新的二级标题收进书签。
- 不改附录 A 的既有契约。附录 D 这一批的 diff 为空。「这颗料」那一行已经写着 `0x410` 和 `0x1FFFF7E0`，G0 那一行已经写着第 1 脚 PC11。不手改 `stm32-book/book/D-术语表.md` 或英文对应文件。附录 E 的卡片仍由 `sources` 生成。
- 不替换、不重画已有图。第 20 章留下 `project-structure.svg`。第 21 章留下 7 张板图。第 22 章留下 `toolchain-flow.svg`。第 23 章留下引脚全图和 `g0-boot-swd.svg`。新主图是加进去的。
- 不把厂商手册、官方插图或社区原文放进仓库。
- 不加图目录或表目录，不加第 30 章，不改 `docs/00`–`28` 的文件名。不把第 21 章改名为图注，不把第 22 章改名为仿真实战。
- 不新开可烧录工程。不改 `examples/`，不改 `sim/`。章节用已经冻住的说法，不回头改例程和仿真脚本。

## 来源与许可

四层用法和总纲、Batch6 相同。

允许写进正文的，仍按这个顺序：

1. ST 的 RM、DS、PM、UM、AN：只吸收事实，用自己的话写，附文档号和可点击的入口。不粘贴段落，不描官方图。
2. MIT、BSD-2-Clause、BSD-3-Clause、ISC、CC BY 4.0、CC BY 3.0、CC0：可以改写教学要点。许可证不强制署名时，本书仍署名。本仓库例程是 MIT。
3. 其他许可证：只留链接。含 GPL、LGPL、CC BY-NC、CC BY-ND、Apache-2.0、保留所有权利、未写许可的帖子和视频。Wokwi 文档、Renode 文档、WeAct 仓库、中文教程站都在这一层，除非打开后的许可证落在第 2 层。

权威数字以第 1 层、罗盘边界和附录 D 已有格子为准。社区材料只支持「这个坑有人踩过」。帖子里的寄存器值，要在 RM/DS/PM 或本仓库例程上重新钉住之后才能进「原理与边界」或「时序或状态」。钉不住的，出处卡的主张写成「经验线索，未升格为规范」，并且这一行不引入新的寄存器值。

人民币预算、90%、OpenOCD 端口 3333、Renode 端口 3456、BlackPill 的 25 MHz、Nucleo 的 `PLLM/N/P` 三元组，都不进出处卡。

### 追加的来源 id

新 id 只追加在两份 `sources` 对象的末尾。已有 id 的标题、URL、snapshot、许可、scope 都不改。中英两份的 `url`、`snapshot`、`license`、`accessed` 用同一串字符；`title`、`authority`、`scope` 用对应语言。`accessed` 用 `2026-10-25`。章罗盘的 `sources` 数组在原有 id 之后追加新 id，不删除已有 id。

DS5319 的 PDF 与已有 `ds5319-clock` 相同，Rev 20。RM0008 的 PDF 与已有 `rm0008-rcc` 相同，Rev 21。PM0056 与已有 `pm0056` 相同，Rev 7。PM0075 与已有 `pm0075-rdp` 相同。DS12232 与已有 `ds12232` 相同，Rev 5。不另找一份修订。

| 新 id | 冻结点 | 用在 | 不复制 |
| --- | --- | --- | --- |
| `rm0008-signature` | RM0008 Rev 21 的器件电子签名。`DBGMCU_IDCODE` 在 `0xE0042000`。DevID 是低 12 位。中容量 F103 的 DevID 是 `0x410`。闪存容量在 `0x1FFFF7E0`，低 16 位，单位 KB。96 位唯一 ID 从 `0x1FFFF7E8` 起，三个字。章号若不是正文现在写的第 30 章，snapshot 改记印出的章，地址和 `0x410` 仍按印出的。C8 这一行读出来应是 64 | 第 21 章主图。第 20 章只交叉引用「容量去参考手册的签名，不去社区帖」 | 不把 128 KB 写成 C8 的数据手册容量。不改 `ds5319`、`ds5319-swd` |
| `rm0008-map` | RM0008 Rev 21 的存储器映射。GPIOA 在 `0x40010800`，GPIOB 在 `0x40010C00`，GPIOC 在 `0x40011000`，USART1 在 `0x40013800`。印出的地址不同就改 snapshot。USART1 仍是 PA9/PA10，不在这条对象里重写 BRR | 第 22 章：`usart1` 不是 USART2；`C13` 指到 GPIOC | 不改 `rm0008-usart`、`rm0008-gpio`。不把 3456 写进来 |
| `rm0008-hd-boot` | 与 `rm0008-boot` 同一份 RM0008 Rev 21。只记大容量行：STM32F103xC/xD/xE 的系统存储器起点默认是 `0x1FFFB000`。中容量 C8 仍是 `0x1FFFF000`，那一行留在已有对象里。印出的大容量起点不同就改 snapshot，不把 C8 的地址写进这条 | 第 21 章：ZET6 不要去 `0x1FFFF000` 找 Bootloader | 不改 `rm0008-boot`。不把互联型在 C8 上作废这句改掉 |
| `ds5792` | DS5792，STM32F103xC/xD/xE。STM32F103ZET6 取 xE 行：闪存 512 KB，SRAM 64 KB，最高 72 MHz，封装 LQFP144。xC 是 256 KB 闪存和 48 KB SRAM，xD 是 384 KB 闪存和 64 KB SRAM；这两行在 ZET6 上作废。打开与产品页同一份 PDF，记下印出的修订号。Table 2 的 ZE 格子若不是 512 和 64，用印出的格子 | 第 21 章的大板容量。不用于 C8 | 不把 DS5319 的 64 KB / 20 KB 抄进这条。不粘贴原理图 |
| `ds10314` | DS10314 Rev 8，2024-01，STM32F411xC/xE。xE 闪存 512 KB，xC 闪存 256 KB。SRAM 是 128 KB。最高 100 MHz。晶振范围 4 MHz 到 26 MHz。STM32F411CEU6 与 STM32F411RET6 都是 xE。xC 的 256 KB 在这两只订货号上作废。这条不记录 PLL 的 M、N、P | 第 21 章的 BlackPill 与 Nucleo-F411RE 容量和主频上限 | 不把 `PLLM=8`、`N=200`、`P=2` 写进 snapshot。不编 25 MHz 是「数据手册规定的板晶振」 |
| `ds8626` | DS8626 Rev 12，2026-03，STM32F405/407。最高 1 MB 闪存，最高 168 MHz。SRAM 最高 192 KB，其中包含 64 KB CCM，另外还有 4 KB 备份 SRAM。STM32F407VGT6 的 G 是 1 MB 这一档，V 是 100 脚。F407VE 的 512 KB 在 VGT6 上作废。VG 行若印出的不是 1024 KB，用印出的 | 第 21 章的 Discovery 容量。4 KB 不并进 192 | 不把 192 KB 写成已经含备份 SRAM。不编以太网 PHY |
| `ds5319-hse` | 与 `ds5319-clock` 同一份 DS5319 Rev 20 的 HSE 振荡器节。CL1 与 CL2 默认按 5 pF 到 25 pF 的陶瓷范围跟晶振选，两只通常相同。20 pF 不是必须值。印出的范围不同就改 snapshot，不保留正文里另一对皮法。8 MHz 仍走已有时钟对象 | 第 21 章：删掉「必须 2×20 pF」 | 不改 `ds5319-clock`、`ds5319-lse`。不把 20 pF 写成必须值 |
| `um1724-mco` | UM1724 里 NUCLEO-F411RE 的时钟输入。实施时打开这一节再落 snapshot。若印出 ST-LINK 的 MCO 接到 OSC_IN 且频率是 8 MHz，就记 8 MHz，并写明不能从板上拧。印出的频率不同就记印出的。这一节没有频率时，snapshot 写明「未印出」，四块不写 Nucleo 的输入频率，只保留 DS10314 的 100 MHz 上限。这条不记录 PLL 乘数 | 第 21 章旁注。主图不画 M、N、P | 不改已有 `um1724`（那条仍是 L476 的 JP6）。不把 N=200 写进来 |
| `ds12232-lqfp64` | DS12232 Rev 5，Figure 9 与 Table 12 的 LQFP64 列，加上 Table 2。第 1 脚 PC11。第 3 脚 PC13。第 6 脚 VBAT。第 12 脚 PF2-NRST。第 35 脚 PB15，附加功能含 UCPD1_CC2。第 36 脚 PA8，附加功能含 UCPD1_CC1。第 45 脚 PA13。第 46 脚 PA14-BOOT0。注 1：PC13 到 PC15 只能灌大约 3 mA，输出不超过 2 MHz，负载不超过 30 pF，不能当电流源。注 6：复位后 PA13 内部上拉，PA14 内部下拉。Table 2：R 是 64 脚；B 是 128 KB 闪存；SRAM 是 32 KB（带奇偶）或 36 KB（不带奇偶）；最高 64 MHz；1.7 V 到 3.6 V。特性列表没有 CAN，也没有 USB 全速设备。脚号或毫安若印出的不同，用印出的 | 第 23 章主图的四笔账 | 不写待机微安。不改已有 `ds12232`。不把第 1 脚写成 VBAT。不编 FDCAN |

来源清单的 `absorb` 必须含上表九个 id。没有条件追加的第十个 id。Wokwi 或 Renode 的许可证若打开后落在可吸收名单里，仍不在这一批新开 id；键名留在正文链接里。表 2 的 ZE 格子、HSE 的皮法范围、UM1724 的 MCO 频率，印出的与默认不同就改对应 snapshot，不为此再开 id。

### 沿用、但不改写对象的 id

| 已有 id | 这一批怎么用 |
| --- | --- |
| `pm0056` | 第 20 章：这是编程手册。`CFSR` 在 `0xE000ED28`。不改这条对象 |
| `pm0075-rdp` | 第 20 章：读允许键是 `0xA5`，印成 `0x00A5`，地址 `0x1FFFF800`。`0xAA` 不是这只键。不改这条对象 |
| `rm0008-tim`、`ds5319-tim` | 第 20 章交叉引用第 05 章的 1000 Hz。不改这两条对象 |
| `rm0008-usart`、`ds5319-usart` | 第 20 章和第 22 章交叉引用 `0x271`、115200、12800、第 30 脚和第 31 脚。不改这两条对象 |
| `ds5319-lse`、`ds5319-nrst`、`ds5319-gpio`、`ds5319-adc`、`ds5319-swd` | 第 21 章交叉引用 5 pF 到 15 pF、0.1 µF、270 Ω、第 10 脚、第 2 脚、第 34 脚和第 37 脚。不改这些对象 |
| `rm0008-boot` | 第 21 章只在讲 C8 时交叉引用 `0x1FFFF000`。不改这条对象 |
| `rm0008-i2c`、`ds5319-i2c`、`project-examples` | 第 22 章交叉引用 `0x3C`、`0x78`、4.7 kΩ。不改这些对象 |
| `ds12232`、`rm0444`、`an5096`、`an2606`、`st-boot-faq` | 第 23 章交叉引用启动真值表、第四个 SYSCLK 上升沿、空闪存和 RDP。脚号的新格子走 `ds12232-lqfp64`。不改这些对象 |
| `wokwi-bluepill`、`renode-stm32` | 继续只留链接。一个字段都不改。不把它们的许可字符串改写成 MIT |

出处卡的字段仍是现有附录 E 的一套：`title`、`authority`、`url`、`snapshot`、`accessed`、`license`、`scope`。`url` 必须是 `https://`。章内第四块每一行只有一个主张，并带一个 `#source-`。一行写清现象、原因、处理、链接、该来源允许支持的主张。

`CREDITS.md` 第六节现在收到第 16、17、18、19 章（v1.3.1）。这一批在该节下面加一个小节「第 20、21、22、23 章（v1.3.2）」，保留前面的表。新表只列作品名、许可证、用在哪、链接。不贴手册原文。同一文件顶部的静态框图从 26 张改为 30 张，光栅动画从 24 个改为 28 个。只有某一章拆出第二张 SVG 时，静态框图改为 31 张，并在实施 PR 里写明拆图原因。第 21 章的第二张只允许叫 `sample-21-other-parts.svg`。第 23 章的第二张只允许叫 `sample-23-pc13.svg`。不允许第三张。

## 锁定

章号按文件名前缀锁死：`20`、`21`、`22`、`23`。不再按「谁更薄」重选。不改成第 24 章或第 28 章，也不把已经加厚的章再开一遍。不把文件 `21` 改名为图注，不把文件 `22` 改名为仿真实战。

实施开始时仍做一次核对扫描，只读这四章的中英八份。扫描确认三件事：四块标题还不存在；第 20 章和第 21 章的旧坑标题还在，而且英文分别是 `Common traps and how to check them` 与 `Pitfalls`；第 22 章和第 23 章没有 `常见坑与排查` 这个标题。结果写到新文件 `docs/superpowers/plans/2026-10-25-batch7-20-21-22-23-lock.json`，带上运行时的 `git rev-parse HEAD`。不覆盖更早的锁定文件。若扫描发现四块已经有人写过，停下来，不叠第二套标题。

来源清单写到 `docs/superpowers/plans/2026-10-25-batch7-20-21-22-23-source-list.json`，字段沿用 Batch6 清单：`chapters` 是 `["20", "21", "22", "23"]`，`absorb` 里每一条有 `license_class`、`url`、`do_not_copy`、`points`。`license_class` 只允许 `ST-facts-restated`、`MIT`、`BSD-2-Clause`、`BSD-3-Clause`、`ISC`、`CC BY 4.0`、`CC BY 3.0`、`CC0`。许可字符串里不得出现 `GPL`、`LGPL`、`CC BY-NC`、`CC BY-ND`、`All rights reserved`。清单可以先于 manifest 提交；登记以 manifest 为准。

## 章节加厚模板

四块插在 `<!-- /video: -->` 之后、学习目标之前，和第 03 章相同。标题不加表情符号，中英各出现一次：

| 块 | 中文标题 | 英文标题 | 这一块要写完的事 |
| --- | --- | --- | --- |
| 1 | `## 原理与边界` | `## Principle and boundary` | 结论钉在哪颗订货号、哪一版手册；换系列时哪一句作废 |
| 2 | `## 关键插图` | `## Key figures` | 静态主图在前，图注带关键数字和文档号。短 GIF 跟在后面，图注标明辅图 |
| 3 | `## 时序或状态` | `## Timing or state` | 一张能算回去的表。时间或状态迁移和主图是同一笔账 |
| 4 | `## 坑与出处卡` | `## Pitfalls and source cards` | 钉得住的行放在这里。每行一个 `#source-` |

保留学习目标、硬件与接线、代码实现、动手实验、相关资源，以及英文的对应标题。第 20 章保留 `## 🧠 核心原理` 和 `## 🧠 Core ideas`。第 21 章保留 `## 🧠 核心原理` 和 `## 🧠 The boards`。第 22 章保留 `## 🧠 先选哪一家` 和 `## 🧠 Which one to open first`，不要为了整齐新造一个「核心原理」。第 23 章保留 `## 🧠 这颗料是谁` 和 `## 🧠 Which part this is`。和四块、罗盘或附录 D 冲突的数字，就地改成同一笔账，不保留两套说法。第 20 章和第 21 章删掉中文 `## ⚠️ 常见坑与排查`、英文 `## ⚠️ Common traps and how to check them` 和 `## ⚠️ Pitfalls`，不留空标题。第 22 章和第 23 章的现有坑标题保留。

视频块、旁白和已有动画图留在原处。主图不放进 `<!-- video: -->` 块。代码仍按 `docs/CONTENT_GUIDE.md`：HAL，参数用宏。第 20 章的命令行示例若还留着 `RDP=0xAA`，旁边必须写明这不是选项字节的值；四块只写 `0xA5`。

中英的订货号、文档号、寄存器名、脚位和算式一致。英文可以更短，不能少一块，也不能少一个关键数字。

## 第 20 章写什么

这一章是索引，不是第二套外设教程。订货号仍用 STM32F103C8T6 来举例。四笔账是：选对书、算对 PWM、写对读保护、脚和位分家。

### 原理与边界

- **PM 是编程手册。** PM0056 Rev 7 讲 Cortex-M3。`CFSR` 在 `0xE000ED28`。封装、第 30 脚、电气参数在 DS5319，不在 PM。正文和英文表里的 “Product/Package Manual” 改掉。G0 的内核手册不是 PM0056。这一批不打开 PM0223，也不把 G0 的故障寄存器编进这一章。
- **PWM 跟第 05 章同一笔。** 频率是 `fCK_PSC / ((ARR+1) × (PSC+1))`。计数时钟 72 MHz，PSC = 71，ARR = 999，CCR = 500：`72e6 / (72 × 1000) = 1000` Hz，占空比 `500 / 1000 = 50%`。只写 `fCK_CNT / (ARR+1)` 会得到 `72e6 / 1000 = 72000` Hz。这是主图的失败路径。不重画第 05 章。
- **读允许键是 `0xA5`。** 选项字节在 `0x1FFFF800`。手册印 `0x00A5`。写回这个键会先整片擦除主闪存。`0xAA` 不是这只键。命令行示例不得再让读者以为 `RDP=0xAA` 就是选项字节。擦除态 `0xFF` 仍然保持保护，这句跟 `pm0075-rdp` 同一笔，不在这一章展开喂狗。
- **脚和位分两本。** 第 30 脚 PA9、第 31 脚 PA10 在 DS5319。BRR `0x271` 的位在 RM0008。72 MHz 下是 115200，8 MHz 下是 12800。示例 2 可以留下「PA11 是 USB_DM」，但不要把 CAN 过滤器的位说成在数据手册里。示例 3 不再用 AN4031 的 FIFO 回答 F103。F103 有没有 CAN、容量是多少，去 DS5319 和签名寄存器；位定义去 RM0008。
- **90% 不进四块。** 「三件套覆盖 90% 场景」删掉这个百分比。工具名单可以留下。人民币预算留在硬件表，不进四块，不进出处卡。

### 关键插图

主图文件 `assets/diagrams/sample-20-which-manual.svg`，由 `tools/gen_sample_figures.py` 追加一个函数生成，调用 `_credit()`，不调用 `Svg.footer()`。

图上是同一次查找的两条路：

- 三本已经冻住的书：DS5319 Rev 20、RM0008 Rev 21、PM0056 Rev 7。
- **正常路径。** 问第 30 脚，打开 DS5319，读到 PA9。问 `0x271` 的位，打开 RM0008，72 MHz 下是 115200。问硬故障，打开 PM0056，读 `0xE000ED28`。问读保护，低字节写 `0xA5`。
- **失败路径。** 拿 PM0056 去查第 30 脚。旁边一条：PSC = 71 仍在，公式丢掉 `(PSC+1)`，算成 72000 Hz。再旁边：选项字节写成 `0xAA`。
- **旁注。** AN4031 的 FIFO 不回答这颗 C8。不画 PWM 波形。不画 CFSR 的其他位。

图注写「自绘」，带 PM0056、PM0075 和 RM0008 的文档号。替代文本写出结论：PM0056 是编程手册；丢掉 `(PSC+1)` 时这一组数是 72000 Hz；读允许键是 `0xA5`，不是 `0xAA`。不写「示意图」。

`project-structure.svg` 留作辅图。目录树不代替这三本书。

### 时序或状态

一张表覆盖这一次查找。列至少有：问题、打开哪本、读到的数、错在哪。必须有的行：第 30 脚，DS5319，PA9，正常。BRR，RM0008，`0x271` 在 72 MHz 下是 115200，正常。硬故障，PM0056，`0xE000ED28`，正常。读保护，PM0075，`0xA5`，正常。失败行：用 PM 查封装脚，失败。失败行：PSC = 71、ARR = 999，丢掉 `(PSC+1)`，72000 Hz，失败。失败行：把 `0xAA` 写成选项字节，失败。

### 坑与出处卡

至少这些行：

| 现象 | 处理方向 | 链接 | 允许的主张 |
| --- | --- | --- | --- |
| 在 PM0056 里找不到第 30 脚 | 引脚去 DS5319，内核故障去 PM0056 | `#source-pm0056` | PM0056 是 Cortex-M3 编程手册。`CFSR` 在 `0xE000ED28`。这一行不规定封装图 |
| 按本章旧公式配出约 72 kHz | 把 `(PSC+1)` 乘回去 | `#source-rm0008-tim` | PSC = 71、ARR = 999、CCR = 500，在 72 MHz 下是 1000 Hz、50%。丢掉 `(PSC+1)` 得到 72000 Hz |
| 解除读保护时写入 `0xAA` | 选项字节低字节是 `0xA5` | `#source-pm0075-rdp` | 地址 `0x1FFFF800`。手册印 `0x00A5`。写回会先整片擦除。`0xAA` 不是读允许键 |
| 数据手册里搜不到 BRR 的位 | 位在 RM0008，脚在 DS5319 | `#source-rm0008-usart` | `0x271` 在 72 MHz 下是 115200，在 8 MHz 下是 12800。第 30 脚是 PA9 |
| 用 AN4031 的 FIFO 解释 F103 的 DMA 错误 | F103 不按那只 FIFO 查 | `#source-rm0008` | AN4031 讲的是 F2/F4。这一行不引入 FIFO 阈值，也不新编 F103 的 DMA 通道号 |

90%、人民币预算和端口 3333 留在后面的工具表。它们不进出处卡。

### 短 GIF

辅图 `assets/gif/which-manual.gif`。内容是正常路径：问题从「第 30 脚」切到 DS5319 的 PA9，再标出 `0xA5`。帧数不少于 3、不多于 12。72000 Hz 和 `0xAA` 只放在静态主图上。不替换 `project-structure.svg`。

## 第 21 章写什么

订货号先分开写。C8 的四块只使用 DS5319 和 RM0008。ZET6、F411、F407 各用自己的数据手册。7 张板图都留着。主图不把七块板画成一张海报。

### 原理与边界

- **C8 的身份。** `0xE0042000` 的低 12 位是 `0x410`。`0x1FFFF7E0` 的低 16 位读 64，单位 KB。UID 从 `0x1FFFF7E8` 起。DS5319：闪存 64 KB，SRAM 20 KB，LQFP48，最高 72 MHz。读数不是 64，就不要按 C8 往下算。丝印写 128 KB 是主图的失败旁注。
- **ZET6 不在 DS5319。** DS5792 的 STM32F103ZET6：512 KB 闪存，64 KB SRAM，72 MHz，LQFP144。系统存储器默认从 `0x1FFFB000` 起。把 C8 的 `0x1FFFF000` 套到这颗料上，是主图的失败路径。xC 的 256 KB / 48 KB 和 xD 的 384 KB 在 ZET6 上作废。
- **F411 的 xE。** CEU6 和 RET6：512 KB 闪存，128 KB SRAM，最高 100 MHz。xC 的 256 KB 在这两只料上作废。`PLLM=8`、`N=200`、`P=2` 能算出 100 MHz，但不是 DS10314 的格子，从四块删掉。晶振允许 4 MHz 到 26 MHz。BlackPill 写着 25 MHz 时，标成板级说法，不标成数据手册已经替它选了 PLL。Nucleo 的 MCO 只有 `um1724-mco` 记下印出的频率之后才写进旁注。没记下之前，四块只写 100 MHz 这个上限。
- **F407VG。** DS8626：1 MB 闪存，最高 168 MHz。SRAM 最高 192 KB，含 64 KB CCM，另有 4 KB 备份 SRAM。不要把 4 KB 加进 192 再叫成 196 KB 的主 SRAM，也不要把它从书上抹掉。正文「1 MB / 192 KB」补上这 4 KB。
- **最小系统跟已经冻住的格子。** LSE 是 5 pF 到 15 pF，6 pF 不是必须值。HSE 的负载电容按 5 pF 到 25 pF 跟晶振选，20 pF 不是必须值。NRST 的外部电容是 0.1 µF。10 kΩ 上拉不进出处卡。外接灯是第 10 脚、270 Ω。PA5 加 330 Ω 不进四块。第 2 脚 PC13 的板载灯低电平亮，不能当电流源。BOOT0 悬空仍然是失败；C8 上 BOOT0 = 0 进 `0x08000000`，BOOT1 = 0 且 BOOT0 = 1 进 `0x1FFFF000`。这张表只属于 C8。

F4 Discovery 上的传感器型号留在板卡表，不进出处卡。WeAct 仓库只留链接。

### 关键插图

主图文件 `assets/diagrams/sample-21-which-part.svg`。

图上是两颗料的容量和启动地址：

- C8：`0x410`，`0x1FFFF7E0` 读 64，闪存 64 KB，SRAM 20 KB，系统存储器 `0x1FFFF000`。
- **正常路径。** 读数是 64，按 DS5319 往下算。ZET6 单独标 512 KB 和 64 KB，系统存储器 `0x1FFFB000`。
- **失败路径。** 丝印 C8、读数不是 64，仍去链接 128 KB。另一处把 ZET6 的 Bootloader 画在 `0x1FFFF000`。
- **旁注。** F411xE 是 512 KB / 128 KB / 100 MHz。F407VG 是 1 MB、168 MHz、192 KB 加 4 KB。不画 330 Ω。不画必须 6 pF。不画 M、N、P。

图注写「自绘」，带 DS5319、DS5792 和 RM0008 的签名地址。替代文本写出结论：C8 的 DevID 是 `0x410`，容量读数是 64 KB；ZET6 的 512 KB 在 DS5792，系统存储器不是 `0x1FFFF000`。不写「示意图」。

`bluepill-stm32f103c8t6.svg` 和 `peripheral-wiring.svg` 留作辅图。7 张板图都不替换。

放不下 60 KB 时，把 F411 和 F407 拆到 `assets/diagrams/sample-21-other-parts.svg`。第一张仍是 C8 与 ZET6。拆开的两张都用 `_credit()`，都不调用 `Svg.footer()`。只允许这个第二张文件名。

### 时序或状态

一张表覆盖「上电前先认料」。列至少有：订货号、手册、闪存 / SRAM、系统存储器或主频上限、能不能套 C8。必须有的行：STM32F103C8T6，DS5319，64 KB / 20 KB，`0x1FFFF000`，能。失败行：读数不是 64，仍套 64 KB，不能。STM32F103ZET6，DS5792，512 KB / 64 KB，`0x1FFFB000`，不能套 C8 的地址。STM32F411CEU6 与 RET6，DS10314，512 KB / 128 KB，最高 100 MHz，不能套 72 MHz 的等待周期。STM32F407VGT6，DS8626，1024 KB，192 KB 加 4 KB，最高 168 MHz，不能把 4 KB 算进 192。电容行：LSE 5 pF 到 15 pF；HSE 5 pF 到 25 pF；20 pF 和 6 pF 都不是必须值。灯行：第 10 脚、270 Ω；330 Ω 失败。

### 坑与出处卡

至少这些行：

| 现象 | 处理方向 | 链接 | 允许的主张 |
| --- | --- | --- | --- |
| 丝印是 C8，容量寄存器不是 64 | 停止按 DS5319 的 64 KB 分配 | `#source-rm0008-signature` | `0xE0042000` 低 12 位的中容量值是 `0x410`。`0x1FFFF7E0` 低 16 位的单位是 KB。UID 从 `0x1FFFF7E8` 起 |
| 大板的 Bootloader 按 `0x1FFFF000` 找 | ZET6 用大容量的起点 | `#source-rm0008-hd-boot` | 默认是 `0x1FFFB000`。C8 的 `0x1FFFF000` 在 ZET6 上作废 |
| 把 ZET6 的容量写成 64 KB / 20 KB | 打开 DS5792，不要打开 DS5319 | `#source-ds5792` | ZET6 是 512 KB 闪存和 64 KB SRAM，最高 72 MHz |
| Nucleo 被写成 N=200 的出厂时钟 | 只保留 100 MHz 这个上限 | `#source-ds10314` | F411xE 是 512 KB 闪存、128 KB SRAM、最高 100 MHz。xC 的 256 KB 在 CEU6 和 RET6 上作废。这一行不规定 PLL 乘数 |
| Discovery 的 RAM 预算写成 192 KB 并且用满 | 备份 SRAM 另有 4 KB | `#source-ds8626` | 192 KB 含 64 KB CCM。4 KB 备份 SRAM 不在这 192 里。最高 168 MHz，VGT6 的闪存是 1 MB |
| 按旧表焊了 6 pF 或 20 pF，并说手册要求如此 | 电容跟晶振在范围内选 | `#source-ds5319-hse` | HSE 默认 5 pF 到 25 pF，20 pF 不是必须值。LSE 的 5 pF 到 15 pF 仍以已有 `ds5319-lse` 为准，这一行不改那条对象 |
| 外接灯按接线总览用了 330 Ω 和 PA5 | 本书外接灯是第 10 脚和 270 Ω | `#source-ds5319-gpio` | 第 2 脚 PC13 不能当电流源。这一行不新造第三只电阻 |

10 kΩ、25 MHz 和 WeAct 的版本号留在板卡表。它们不进出处卡。NRST 的 0.1 µF 用已有 `#source-ds5319-nrst` 交叉引用，不新写千欧。

### 短 GIF

辅图 `assets/gif/which-part.gif`。内容是正常路径：读到 `0x410`，容量格显示 64，旁边标出 ZET6 的 512 KB 不在这一格。帧数不少于 3、不多于 12。`0x1FFFF000` 被套到 ZET6 上的失败只在静态主图上。不替换 7 张板图。

## 第 22 章写什么

订货号仍是 STM32F103C8T6。仿真器只负责让这四笔账变得看得见。模型没实现的东西，不能拿来否定手册。

### 原理与边界

- **地址。** USART1 在 `0x40013800`。GPIOC 在 `0x40011000`。Renode 平台描述里的 `usart1` 必须对上这个地址。把它说成 USART2，是主图的失败路径。第 30 脚 PA9、第 31 脚 PA10 跟第 06 章同一笔。
- **键名指到脚。** `C13` 指到第 2 脚 PC13。板载灯低电平亮，这只脚只能灌电流。`A0` 指到第 10 脚 PA0。主图不把第 03 章的灯、第 09 章的 ADC 和第 16 章的 WKUP 画成同时接上。`A9` 和 `A10` 指到 USART1。图里写成 `PA0` 或 `PC13` 这种芯片名，是失败路径：那是另一套名字，对不上这张图的键。键名本身来自板文件的链接，不进出处卡。
- **灯亮不是波特率。** 模型若停在 HSI 8 MHz，BRR `0x271` 送出的是 12800 bit/s。72 MHz 那一格才是 115200。灯照样可以闪。这是主图的失败路径。不重画第 06 章的位帧。
- **I2C 跟第 07 章同一笔。** 7 位 `0x3C`，HAL 填 `0x78`，`0x3C << 1 = 0x78`。上拉 4.7 kΩ。把 `0x78` 当成 7 位地址，是失败。不重画第 07 章。
- **DMA 是模型边界。** 这一页已经写明当前 Wokwi BluePill 模型没有 DMA。`uart-dma-idle` 和 `adc-dma` 在这里只能核对接线。这句留在四块，不写成新的芯片限额，也不进出处卡。3456 留在动手实验。

仓库不预置 ELF 这句可以留下。它不是电气账。

### 关键插图

主图文件 `assets/diagrams/sample-22-sim-boundary.svg`。

图上是一次点灯和一次串口：

- 键 `C13` 指向第 2 脚 PC13。键 `A9` 指向第 30 脚 PA9。USART1 标 `0x40013800`。
- **正常路径。** 键名对上脚。时钟是 72 MHz。`0x271` 标成 115200。PC13 低电平点亮。
- **失败路径。** 同一只 `0x271` 停在 8 MHz，线上 12800，灯却仍然在闪。另一处把外设写成 USART2。
- **旁注。** 图里的标签写成 `PA13` 而不是 `C13`，接线对不上。不画 DMA 的 FIFO。不画 3456。不把第 10 脚同时画成灯和按键。

图注写「自绘」，带 RM0008 的基址和第 06 章已经冻结的 `0x271`。替代文本写出结论：USART1 在 `0x40013800`；`C13` 是第 2 脚 PC13；灯亮时 `0x271` 仍可能是 12800 bit/s。不写「示意图」。

`toolchain-flow.svg` 留作辅图。编译箭头不证明波特率。

### 时序或状态

一张表覆盖这一次仿真。列至少有：看什么、手册或键、值、算不算通过。必须有的行：GPIOC，`0x40011000`，第 2 脚 PC13，键 `C13`，低电平亮，正常。USART1，`0x40013800`，第 30 脚和第 31 脚，正常。失败行：名字写成 USART2，失败。时钟行：72 MHz 且 `0x271`，115200，正常；8 MHz 且 `0x271`，12800，灯亮也不通过。I2C 行：7 位 `0x3C`，HAL `0x78`，4.7 kΩ，正常。DMA 行：这个 Wokwi 模型没有 DMA，空闲帧收包不通过，而且这行不产生新的微秒或欧姆。

### 坑与出处卡

至少这些行：

| 现象 | 处理方向 | 链接 | 允许的主张 |
| --- | --- | --- | --- |
| 分析器里的外设被说成 USART2 | 对基址 `0x40013800` | `#source-rm0008-map` | 这个地址是 USART1。GPIOC 在 `0x40011000`。这一行不规定套接字端口 |
| 灯在闪，主机却按 115200 解出乱码 | 先看模型是不是还停在 8 MHz | `#source-rm0008-usart` | `0x271` 在 72 MHz 下是 115200，在 8 MHz 下是 12800 |
| 仿真图写成 `PC13`，零件挂不上 | 图的键是另一套名字，脚仍是第 2 脚 | `#source-ds5319-gpio` | 第 2 脚 PC13 只能灌电流，低电平点亮是板载灯的接法。这一行不把 Wokwi 的键名升格成手册术语 |
| 外接零件挂在第 10 脚，又拿这只脚当 ADC | 一次只选一种用法 | `#source-ds5319-adc` | 第 10 脚是 PA0。这一行不把灯和按键画成同时有效 |
| OLED 地址写成 0x78，扫描器却报 0x3C | 先分清 7 位和 HAL 的写法 | `#source-rm0008-i2c` | `0x3C << 1 = 0x78`。4.7 kΩ 仍以第 07 章为准 |

DMA 没实现、固件路径是占位、端口 3456，留在 `## ⚠️ 仿真替不了的事`。它们不进出处卡。

### 短 GIF

辅图 `assets/gif/sim-usart.gif`。内容是正常路径：键 `C13` 指向第 2 脚，灯灭亮一次，然后 `0x40013800` 标成 115200。帧数不少于 3、不多于 12。12800 和 USART2 只在静态主图上。不替换 `toolchain-flow.svg`。

## 第 23 章写什么

订货号是 STM32G071RB，LQFP64。四笔账都在 DS12232 Rev 5。启动真值表留在现有正文，主图不把它再画成一张。待机电流继续不写。

### 原理与边界

- **订货号。** R = 64 脚。B = 128 KB 闪存。SRAM 是 32 KB（带硬件奇偶）或 36 KB（不用奇偶）。36 KB 不是 32 加 36。最高 64 MHz。供电 1.7 V 到 3.6 V。Cortex-M0+。封面特性列表没有 CAN，也没有 USB 全速设备控制器。
- **第 1 脚不是 VBAT。** LQFP64 第 1 脚是 PC11。第 6 脚才是 VBAT。第 12 脚是 PF2-NRST。从 F103 的小封装习惯去数第 1 脚，是主图的失败路径。
- **PC13 到 PC15。** 第 3 脚是 PC13。注 1：只能灌大约 3 mA，输出不超过 2 MHz，负载不超过 30 pF，不能当电流源去点灯。把 LED 接到 PC13，是失败路径。
- **PA14 与 SWCLK 是同一只脚。** 第 46 脚是 PA14-BOOT0，复位后内部下拉。第 45 脚是 PA13，复位后内部上拉。第 36 脚 PA8 的附加功能是 UCPD1_CC1。第 35 脚 PB15 是 UCPD1_CC2。在这张图上找 CAN_TX，或把 PA11/PA12 叫成 USB_DM/USB_DP，是失败路径。PA11/PA12 在重映射之前就叫 PA11/PA12，这句保留。
- **启动表不重写。** `BOOT_LOCK=1` 强制主闪存。`nBOOT_SEL=0` 才看 PA14。空闪存还可以转入系统 Bootloader，不能把「表上选 Main」理解成一定从 `0x08000000` 执行。这三句跟现有正文和已有来源同一笔。主图只用旁注指向，不重画 `g0-boot-swd.svg`。
- **不写微安。** 封面没有一条可以单独引用的 G071 典型待机电流。四块不补。

### 关键插图

主图文件 `assets/diagrams/sample-23-g071-pins.svg`。

图上是 LQFP64 的这一次核对，不是 64 只脚的全表：

- 第 1 脚 PC11。第 6 脚 VBAT。第 12 脚 PF2-NRST。第 3 脚 PC13，旁边标大约 3 mA、2 MHz、30 pF。
- **正常路径。** 从第 1 脚数到 PC11。调试脚是第 45 脚 PA13 和第 46 脚 PA14-BOOT0，复位后下拉在 PA14。USB 标成 UCPD：第 36 脚 PA8、第 35 脚 PB15。
- **失败路径。** 把第 1 脚标成 VBAT。把 LED 接到第 3 脚 PC13。在图角找 CAN_TX。
- **旁注。** SRAM 写成 32 KB 或 36 KB，不要相加。不画待机电流。不把 F103 的 `0x1FFFF000` 画进来。

图注写「自绘」，带 DS12232 Rev 5 的 Figure 9 和 Table 12。替代文本写出结论：第 1 脚是 PC11；第 12 脚是 PF2-NRST；PC13 不能拿来点灯；PA14 与 SWCLK 是同一只脚。不写「示意图」。

`pinout-stm32g071rb-lqfp64.svg` 和 `g0-boot-swd.svg` 留作辅图。全图和启动动画不代替这四笔账。

放不下 60 KB 时，把 PC13 的 3 mA 限制拆到 `assets/diagrams/sample-23-pc13.svg`。第一张仍有第 1 脚、第 12 脚和第 46 脚。拆开的两张都用 `_credit()`，都不调用 `Svg.footer()`。只允许这个第二张文件名。

### 时序或状态

一张表覆盖「从第 1 脚数到调试脚」。列至少有：脚号、名字、复位后或限制、能不能照抄 F1。必须有的行：第 1 脚，PC11，不是 VBAT，不能。第 6 脚，VBAT，不能当成第 1 脚。第 12 脚，PF2-NRST，不是一只单独的 NRST 焊盘编号。第 3 脚，PC13，大约 3 mA、2 MHz、30 pF，不能点灯。第 45 脚，PA13，复位后内部上拉。第 46 脚，PA14-BOOT0，复位后内部下拉，与 SWCLK 共用。第 36 脚和第 35 脚，UCPD1_CC1 和 UCPD1_CC2，不是 USB_DM/DP。容量行：闪存 128 KB；SRAM 32 KB 或 36 KB，不相加。失败行：在图上找 CAN_TX，这颗料没有 CAN。

### 坑与出处卡

至少这些行：

| 现象 | 处理方向 | 链接 | 允许的主张 |
| --- | --- | --- | --- |
| 左上角被数成 VBAT | 第 1 脚是 PC11 | `#source-ds12232-lqfp64` | 第 6 脚才是 VBAT。第 12 脚是 PF2-NRST |
| PC13 推挽点灯又暗又慢 | 这三只脚不能当电流源 | `#source-ds12232-lqfp64` | 注 1：大约 3 mA，不超过 2 MHz，负载不超过 30 pF。第 3 脚是 PC13 |
| 原理图在找 CAN_TX | G071RB 没有 CAN 控制器 | `#source-ds12232-lqfp64` | 特性列表没有 CAN。这一行不指定一只 FDCAN 脚 |
| PA11/PA12 被接成 USB 全速 | 这颗料的 USB 能力是 UCPD | `#source-ds12232-lqfp64` | 第 36 脚 PA8 是 UCPD1_CC1，第 35 脚 PB15 是 UCPD1_CC2 |
| 拉高 PA14 却仍从主闪存启动 | 先读 `BOOT_LOCK` 和 `nBOOT_SEL` | `#source-rm0444` | `BOOT_LOCK=1` 强制主闪存。`nBOOT_SEL=0` 才看 PA14。这一行不新写微安 |
| SRAM 预算写成 68 KB | 32 KB 和 36 KB 是两种用法 | `#source-ds12232-lqfp64` | 带奇偶是 32 KB，不用奇偶是 36 KB。B 后缀的闪存是 128 KB。最高 64 MHz |

空闪存转入系统 Bootloader、RDP 和 `DBG_SWEN` 留在现有启动节，交叉引用已有 `#source-an2606`、`#source-an5096`、`#source-st-boot-faq`。不把那些对象的 snapshot 改写。不把待机电流补进任何一行。

### 短 GIF

辅图 `assets/gif/g071-pin1.gif`。内容是正常路径：从封装左上角数到第 1 脚 PC11，再标出第 46 脚 PA14。帧数不少于 3、不多于 12。把第 1 脚画成 VBAT、以及 PC13 上的灯，只在静态主图上。不替换引脚全图，也不替换 `g0-boot-swd.svg`。

## 插图标准

沿用总纲和 Batch6 的逼真、翔实、生动、可印刷、自绘。主图和短 GIF 分开。简化示意图可以留在章内当辅图，不能充当关键插图的主图。少留空白靠图上的数字和表，不靠把字号或页边再收一刀。

静态主图要让人能对着封装和手册核对：

- 第 20 章画出 DS5319、RM0008、PM0056 三本，以及 72000 Hz 和 `0xA5`。不画成三本没有文档号的书。
- 第 21 章画出 `0x410`、64 KB、512 KB 和 `0x1FFFB000`。不画成四块没有容量的板子剪影。
- 第 22 章画出 `0x40013800`、第 2 脚和 12800。不画成一只没有地址的终端窗口。
- 第 23 章画出第 1 脚 PC11、第 12 脚 PF2-NRST、第 46 脚 PA14 和大约 3 mA。不画成没有脚号的六十四个点。

静态主图的文件规则：

- 用 `tools/svgkit.py`，生成脚本是 `tools/gen_sample_figures.py`。四章各一张，中英引用同一文件。中文路径 `../assets/diagrams/...`，英文路径 `../../assets/diagrams/...`。第 21 章只有在单张超过 60 KB、拆图之后才增加 `sample-21-other-parts.svg`。第 23 章只有在同样条件下才增加 `sample-23-pc13.svg`。
- 不调用 `Svg.footer()`。落款用脚本里已有的 `_credit()`：左侧是文档号，右侧是「自绘 · 静态 · CC BY 4.0」。
- 没有 `<animate`、`@keyframes`、`animation:`。图上同时有正常路径和失败路径。
- 替代文本写结论。图注写「自绘」，不写「实拍」「手册截图」「矢量动画」。
- 单张小于 60 KB。放不下就拆成主图加局部，每张仍争取小于 60 KB。拆开仍超过时，在实施 PR 里写出字节数和原因，不把图画回简笔，也不把 60 KB 改成仓库新默认值。
- 登记进 `assets/README.md` 第四节，和已有的 `sample-00` 到 `sample-19` 主图并列。`gen_sample_figures.py` 那一行注释补上第 20、21、22、23 章。

短 GIF：

- 四条都走 `tools/gen_gifs.py`，加入 `BUILDERS`，这样 `tools/check_assets.py` 能逐像素对上重新生成的帧。GIF 上的字用 ASCII。
- 每条少于 500 KB，帧数见上面四节。图注写明它是网页和公众号辅图，印刷以静态主图为准。
- `gen_gifs.chrome()` 自带的页脚可以留在 GIF 里。那条页脚不是静态主图的 `Svg.footer()`。
- 不改已有 24 个 BUILDERS 的像素：`led-blink`、`pwm-breath`、`uart-bits`、`i2c-timing`、`dma-ring`、`sar-adc`、`nvic-preempt`、`uart-idle`、`clock-css`、`pwm-1khz`、`spi-jedec`、`adc-sample`、`swd-fetch`、`i2c-addr`、`dma-cndtr`、`iwdg-1s`、`iap-jump`、`can-500k`、`usb-48m`、`rtos-tick`、`stop-wake`、`cfsr-read`、`boot0-low`、`one-slot`。不重跑它们来换画面。
- `tools/svg2gif.py` 这一批不当成必经步骤，也不为了它去改 CI。`assets/README.md` 第五节把「上面 24 张 GIF」改成「上面 28 张 GIF」。

PDF 关掉动画之后，读者只看静态主图和图注，就能指出失败发生在哪一段。第 20 章是「用编程手册去查第 30 脚，或丢掉 `(PSC+1)` 得到 72000 Hz，或把 `0xAA` 当成选项字节」。第 21 章是「读数不是 64 仍按 C8 分配，或把 ZET6 的系统存储器画在 `0x1FFFF000`」。第 22 章是「灯已经在闪，`0x271` 在 8 MHz 上仍是 12800，或外设被说成 USART2」。第 23 章是「第 1 脚被数成 VBAT，或 LED 接到了 PC13」。

## 工作流与 PR 节奏

### 本 PR（设计）

只新增 `docs/superpowers/specs/2026-10-25-classic-encyclopedia-batch7-20-21-22-23-design.md`。不改 `docs/20`、`docs/21`、`docs/22`、`docs/23` 和 `docs/en/` 的章节。不改 `stm32-book/`、`CREDITS.md`、`assets/`、`tools/`。不升版本，不打 tag，不发 Release。不新增 `docs/superpowers/plans/` 下的实施计划。不改样式，不重画海报。本 PR 等人审阅规格后再合入，不在 CI 变绿后自动合。

### 实施 PR（下一轮，不在本 PR）

顺序固定：

1. **核对扫描。** 写出 `2026-10-25-batch7-20-21-22-23-lock.json`。章号保持 20、21、22、23。
2. **许可门。** 写出 `2026-10-25-batch7-20-21-22-23-source-list.json`。先有清单，再改正文。
3. **静态主图和短 GIF。** 先提交 SVG、GIF 和生成脚本，再写正文。主图不依赖 GIF。
4. **中英加厚。** 八份 Markdown 一起提交。视频块以内的字节保持不变。文件 `00` 到 `19`，以及 `24` 到 `28`，正文 diff 为空。
5. **登记。** 新来源追加进两份 manifest。更新这四章罗盘的来源数组。第 20 章罗盘写明 PM0056 是编程手册，读允许键是 `0xA5`。第 21 章罗盘写明 C8 读 `0x410` 和 64 KB，ZET6 的容量不在 DS5319。第 22 章罗盘写明 USART1 在 `0x40013800`，灯亮不等于 115200。第 23 章罗盘保留「不写待机微安」，并写上第 1 脚是 PC11、第 46 脚与 SWCLK 共用。`CREDITS.md` 第六节增加 v1.3.2 小节，并把静态框图改为 30 张、光栅动画改为 28 个。若拆出第二张 SVG，静态框图改为 31 张。`revisions.json` 在条目最前加上 1.3.2，日期写死 `2026-10-25`。两份 manifest 的 `version` 改为 `1.3.2`，`date` 改为 `2026-10-25`。`stm32-book/README.md` 的当前版本句改为 **v1.3.2 · 2026-10-25**。发布一节里的 tag 名改成 `v1.3.2`，并在现有「也不要把 1.3.0 的产物标成 1.3.1」之后加上「也不要把 1.3.1 的产物标成 1.3.2」。这一步仍不创建 tag，也不创建 Release。修订说明只写这四章加厚了什么，用文件名前缀。中英各两句，例如：第 20 章写上 PM0056 是编程手册而不是封装手册，读允许键是 `0xA5` 不是 `0xAA`；PSC = 71 时丢掉 `(PSC+1)` 会把 1000 Hz 算成 72000 Hz。第 21 章写上 C8 的 DevID 是 `0x410`，`0x1FFFF7E0` 读 64 KB；F103ZET6 的 512 KB 闪存和 64 KB SRAM 在 DS5792，系统存储器不是 `0x1FFFF000`。第 22 章写上 USART1 在 `0x40013800`，Wokwi 的 `C13` 是第 2 脚 PC13；同一只 `0x271` 在 8 MHz 上是 12800。第 23 章写上 G071RB 的第 1 脚是 PC11，第 12 脚是 PF2-NRST；PC13 到 PC15 只能灌大约 3 mA，第 46 脚 PA14 与 SWCLK 是同一只脚。英文用同样的事实。
6. **附录。** 附录 D 的 diff 为空。不改「这颗料」和换系列那一页里已经写对的格子。
7. **测试。** 新增 `stm32-book/tests/test_batch7_chapters.py` 和 `stm32-book/tests/test_batch7_sources.py`，照着 Batch6 测试检查四块、共享数字、主图禁词和许可门。视频块里的旧旁白不拿来判失败。不放宽 `test_sample_chapters.py`、`test_batch2_chapters.py`、`test_batch3_chapters.py`、`test_batch4_chapters.py`、`test_batch5_chapters.py` 和 `test_batch6_chapters.py`。`test_build.py` 里当前版本从 `1.3.1` 改为 `1.3.2`：`assert_version_history_and_index` 的元组在 `1.3.1` 之前加上 `1.3.2`，并断言 `1.3.2` 出现在 `1.3.1` 之前。修订列表以 `1.3.2` 起头。两份整书 HTML 含 `<strong>v1.3.2</strong>`。`test_visual_polish_version_is_1_2_0` 改为核对当前条目是 1.3.2，日期是 2026-10-25。现在对 `entries[0]` 的 1.3.1 四章两句改去核对 `entries[1]`。现在对 `entries[1]` 的 1.3.0 四章两句改去核对 `entries[2]`。现在对 `entries[2]` 的 1.2.9 海报两句改去核对 `entries[3]`。现在对 `entries[3]` 的 1.2.8 密度两句改去核对 `entries[4]`。现在对 `entries[4]` 的 1.2.7 浅色两句改去核对 `entries[5]`。现在对 `entries[5]` 的 1.2.6 封面两句改去核对 `entries[6]`。现在对 `entries[6]` 的 1.2.5 令牌两句改去核对 `entries[7]`。现在对 `entries[7]` 的 1.2.4 排版两句改去核对 `entries[8]`。现在对 `entries[8]` 的 1.2.3 两句改去核对 `entries[9]`。现在对 `entries[9]` 的 1.2.2 两句改去核对 `entries[10]`。现在对 `entries[10]` 的 1.2.1 指南两句改去核对 `entries[11]`。现在对 `entries[11]` 的 1.2.0 两句改去核对 `entries[12]`。README 的断言改成当前版本句、`版本号已经是 1.3.2`、`也不要把 1.3.1 的产物标成 1.3.2` 和 `打 tag \`v1.3.2\``。不删 `0x271`、`167 ns`、账本名和出版书签长度为 44 的断言。不改 CSS 哈希一类的视觉契约。不新增读取 `CONTENT_GUIDE.md` 的测试。
8. **CI 变绿之后停下来等人复审。** 复审对象是构建出的中英 HTML 里的这四章。人接受之前不合入，也不开下一批章。Book CI 变绿不等于可以自动 squash 合入。

实施 PR 的 diff 可以碰这四章中英正文、两份 manifest 的新 `sources` 和这四章罗盘、新图与生成脚本、`assets/README.md`、`CREDITS.md`、版本与修订、新的锁定文件和来源清单、新测试，以及 `test_build.py` 里的版本字符串。不碰其余章的正文，不改 `build_html.py`，不改样式文件，不改 `assets/video/`，不改附录 D。

## 验收

### 本设计 PR

- 相对基线 `ef5a088`，只新增 `docs/superpowers/specs/2026-10-25-classic-encyclopedia-batch7-20-21-22-23-design.md`。
- 章节、`stm32-book/`、资产、工具和 `CREDITS.md` 与基线 `ef5a088` 相同。
- 没有新的 SVG 或 GIF，版本号仍是 1.3.1。没有实施计划文件。没有样式 diff，没有海报 diff。

### 实施 PR

- 中文四章各有且仅有一次：`## 原理与边界`、`## 关键插图`、`## 时序或状态`、`## 坑与出处卡`。英文对应四个标题同样各一次。
- 第 20 章和第 21 章都不再有 `## ⚠️ 常见坑与排查`、`## ⚠️ Common traps and how to check them` 或 `## ⚠️ Pitfalls`。第 22 章保留 `## ⚠️ 仿真替不了的事` 和英文对应标题。第 23 章保留 `## ⚠️ 从 F1 抄代码时最容易摔的几处` 和英文对应标题。实施后不要新出现 `## ⚠️ Pitfalls and troubleshooting`。
- 每章关键插图的第一张图是对应的静态 SVG。图上能看出正常路径和失败路径。GIF 不是这一节唯一的图。图注含「自绘」。
- 视频块以外，中英都有这些数字，而且彼此一致：
  - 第 20 章：`PM0056`、`0xE000ED28`、`71`、`999`、`500`、`1000`、`72000`、`0xA5`、`0x00A5`、`0x1FFFF800`、`0x271`、`115200`、第 30 脚、`PA9`。四块写明 PM 不是封装手册，并且 `0xAA` 不是读允许键。四块不写 90%。四块不把 AN4031 的 FIFO 写成 F103 的事实。
  - 第 21 章：`0xE0042000`、`0x410`、`0x1FFFF7E0`、`0x1FFFF7E8`、`64`、`20`、`0x1FFFF000`、`0x1FFFB000`、`512`、`128`、`100`、`1024`、`192`、`4`、`168`、`270`。四块写明 ZET6 不在 DS5319，6 pF 和 20 pF 都不是必须值，330 Ω 不是本书的外接灯。四块不把 `N=200` 写成数据手册格子。
  - 第 22 章：`0x40013800`、`0x40011000`、第 2 脚、`PC13`、`C13`、第 30 脚、`PA9`、`0x271`、`115200`、`12800`、`0x3C`、`0x78`、`4.7`。四块写明灯亮不能证明波特率，并且当前 Wokwi 模型没有 DMA。四块不把 3456 写进出处卡。
  - 第 23 章：第 1 脚、`PC11`、第 6 脚、`VBAT`、第 12 脚、`PF2`、第 3 脚、`PC13`、`3`、`2`、`30`、第 45 脚、`PA13`、第 46 脚、`PA14`、第 36 脚、`PA8`、第 35 脚、`PB15`、`128`、`32`、`36`、`64`、`1.7`、`3.6`。四块写明没有 CAN，USB 是 UCPD 不是全速设备，32 KB 与 36 KB 不能相加。四块不写待机微安。
- 第 20 章引用 `0x271` 和 1000 Hz 时不改第 05 章和第 06 章。第 21 章引用 `0x1FFFF000` 时不改第 18 章，也不改 `rm0008-boot`。第 22 章引用 `0x78` 时不改第 07 章。第 23 章引用启动表时不改 `rm0444` 和 `an5096` 的对象。
- 静态 SVG 小于 60 KB，不含动画标记，含「自绘」，不含「实拍」和「矢量动画」。四条新 GIF 小于 500 KB，并且在 `BUILDERS` 里。已有 24 条 GIF 的像素与基线相同。`project-structure.svg`、7 张板图、`toolchain-flow.svg`、G071 引脚全图和 `g0-boot-swd.svg` 的字节与基线相同。`assets/video/` 与基线相同。
- 新 `#source-` 都能在构建出的 HTML 里找到 `id="source-..."`。已有 `pm0056`、`pm0075-rdp`、`rm0008-tim`、`ds5319-tim`、`rm0008-usart`、`ds5319-usart`、`ds5319-lse`、`ds5319-nrst`、`ds5319-gpio`、`ds5319-adc`、`ds5319-swd`、`rm0008-boot`、`rm0008-i2c`、`ds5319-i2c`、`project-examples`、`ds12232`、`rm0444`、`an5096`、`an2606`、`st-boot-faq`、`wokwi-bluepill`、`renode-stm32`、`um1724` 的对象与基线逐字段相同。
- 附录 D、附录 A 和样式文件、`build_html.py` 的 diff 为空。`test_build.py` 对 `0x271`、`167 ns` 和出版书签条数的断言仍在。
- 除这四章的中英八份以外，`docs/` 章节正文 diff 为空。八份之中，视频块以内与基线相同。
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

1. **DS5792 的修订号和 ZE 行。** 默认 STM32F103ZET6 是 512 KB 闪存、64 KB SRAM、72 MHz、LQFP144。实施时打开 ST 产品页上的 DS5792，把印出的修订号写进 snapshot。格子不同就改格子，不改回 DS5319 的 64 KB / 20 KB。
2. **大容量系统存储器。** 默认 `0x1FFFB000`。印出的起点不同就改 `rm0008-hd-boot`。不修改 `rm0008-boot` 里 C8 的 `0x1FFFF000`。
3. **HSE 负载电容。** 默认 5 pF 到 25 pF，20 pF 不是必须值。印出的范围不同就改 `ds5319-hse`。不把 20 pF 留成必须值。
4. **UM1724 的 MCO。** 实施打开 UM1724 的 NUCLEO-F411RE 时钟节再写 `um1724-mco`。印出 8 MHz 就记 8 MHz。印出别的频率就记印出的。没有频率时，snapshot 写明未印出，四块不写 Nucleo 的输入频率，主图仍只锁 100 MHz 上限。`N=200` 在这三种情况下都不进四块。
5. **DS8626 的 VG 行。** 默认 VGT6 是 1 MB，SRAM 表述保持「192 KB（含 64 KB CCM）另加 4 KB」。印出的分列不同就改 snapshot，不把 4 KB 并进 192。
6. **主图体积。** 先拆图。第 21 章的第二张只允许叫 `sample-21-other-parts.svg`。第 23 章的第二张只允许叫 `sample-23-pc13.svg`。拆开仍超过 60 KB 时在实施 PR 里说明，不降低画法标准。
7. **版本号。** 实施时升到 1.3.2，不写成 1.3.1.1。日期写 `2026-10-25`。本设计 PR 不升版本。
8. **图目录。** 这一批不加。
9. **下一批章号。** 仍是 4 章，到下一次设计再锁。本文件不预选 `24` 或 `28`。
10. **第 10 脚。** 第 03 章主张外接灯。第 09 章主张 ADC。第 16 章主张 Stop 的按键。第 22 章的 `A0` 只表示仿真键指到这只脚。四张图都不把两种功能画成同时有效。

## 英文提要

Thicken only chapter files 20 (resources and toolchain), 21 (schematics and board maps), 22 (simulation labs: Wokwi and Renode), and 23 (STM32G0 pins, G071RB), in Chinese and English, on top of v1.3.1 (`ef5a088`, PR #59). Chapters 00 through 19 are already thick. Keep the on-disk titles. File 21 stays "原理图与实物图鉴" / "Schematics and board maps", not "图注". File 22 stays "仿真实验：Wokwi 与 Renode" / "Simulation labs: Wokwi and Renode", not "仿真实战". File 23 keeps the G071RB subtitle. Do not retitle this batch as the RTOS survey in file 28. Density pass F already tightened whitespace in 1.2.8; this batch does not touch CSS. The 29 lecture posters stay as they are, including the video-block narration. Use the same four sections as the thick chapters. Each chapter gets one printable static SVG from `gen_sample_figures.py`, with a normal path and a failure path, and no `Svg.footer()`. Captions say the figure is drawn for this book. Chapter 20 draws the manual choice: PM0056 is the Cortex-M3 programming manual, not a package manual. CFSR is at `0xE000ED28`. Dropping `(PSC+1)` from the chapter 05 formula with PSC = 71 turns 1000 Hz into 72000 Hz. The readout-allowed option-byte key is `0xA5` (`0x00A5` in PM0075), not `0xAA`. Chapter 21 draws the C8 identity: DevID `0x410` at `0xE0042000`, and 64 KB at `0x1FFFF7E0`. An STM32F103ZET6 is 512 KB of Flash and 64 KB of SRAM in DS5792, and its system memory starts at `0x1FFFB000`, not at the C8 address `0x1FFFF000`. F411xE is 512 KB / 128 KB / 100 MHz maximum. F407VGT6 is 1 MB and 168 MHz, with 192 KB of SRAM including 64 KB of CCM, plus 4 KB of backup SRAM. Six picofarads and 20 pF are not required capacitor values. `N=200` is not a datasheet cell. Chapter 22 draws USART1 at `0x40013800` and GPIOC at `0x40011000`. The Wokwi key `C13` is pin 2, PC13. A blinking lamp does not prove the baud rate: BRR `0x271` is 12800 bit/s on the 8 MHz HSI. The 7-bit I2C address `0x3C` is `0x78` in HAL. The current Wokwi BluePill model has no DMA. Port 3456 stays out of the source cards. Chapter 23 draws the LQFP64 of STM32G071RB: pin 1 is PC11, pin 12 is PF2-NRST, and pin 6 is VBAT. PC13 through PC15 may sink about 3 mA, must stay at or below 2 MHz and 30 pF, and must not source an LED. Pin 46, PA14-BOOT0, is also SWCLK and is pulled down after reset. There is no CAN controller. USB here is UCPD, on pin 36 PA8 and pin 35 PB15. SRAM is 32 KB with parity or 36 KB without, not the sum. Do not add a standby microamp. One short GIF per chapter is auxiliary only. The existing 24 GIF builders and the existing auxiliary figures stay as they are. Register nine new sources by appending ids. Bump the book to 1.3.2 on 2026-10-25 during implementation, do not tag or release, and stop for human review before squash-merge. This design PR only adds this file.

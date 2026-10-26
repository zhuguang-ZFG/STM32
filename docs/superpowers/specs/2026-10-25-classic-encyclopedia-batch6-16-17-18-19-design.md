# 第 16、17、18、19 章加厚设计

日期：2026-10-25  
状态：待人审。人接受这份规格之前不实施  
基线：`main` 上的整书 **v1.3.0**（`80c5efb7cd0134d9450dfab99330c619ffaee295`，PR #56，2026-10-25）  
上一份设计：[2026-10-25-classic-encyclopedia-batch5-12-13-14-15-design.md](2026-10-25-classic-encyclopedia-batch5-12-13-14-15-design.md)（PR #54）。四块模板来自 [2026-10-25-classic-encyclopedia-thicken-design.md](2026-10-25-classic-encyclopedia-thicken-design.md)（PR #18）。密度刀 F 是 [2026-10-25-book-density-F-design.md](2026-10-25-book-density-F-design.md)，已经在 1.2.8 收过空白。  
本文件只记录这一批的设计。它不改章节正文，不画新图，不改 `stm32-book/` 构建，不升版本号，不打 tag，不发布 Release，不写实施计划。

章号按文件名前缀锁死，不按主题改名。文件 `16` 是低功耗，文件 `17` 是调试与性能，文件 `18` 是常见问题 FAQ，文件 `19` 是项目实战合集。任务单里的「项目实战上册」不是仓库里的标题。一级标题继续是 `19 项目实战合集`，英文继续是 `19 A set of real projects`。不要把这一批改名成上册，也不要写成第 28 章的 RTOS 生态。

## 背景

v1.3.0 已经按大典四块加厚的是第 00 到第 15 章。这一批只加厚另外四章，中文和英文一起写：

| 文件前缀 | 中文 | 英文 | 这一章在讲 |
| --- | --- | --- | --- |
| `16` | `docs/16-低功耗设计.md` | `docs/en/16-low-power.md` | Stop 醒来的时钟、表 16 的微安、BRR 还在时的波特率 |
| `17` | `docs/17-调试与性能优化.md` | `docs/en/17-debug.md` | CFSR、BFARVALID、DWT 的 1 µs |
| `18` | `docs/18-常见问题FAQ.md` | `docs/en/18-faq.md` | 38 条索引；认不出芯片时先看线和 BOOT0 |
| `19` | `docs/19-项目实战合集.md` | `docs/en/19-projects.md` | 10 个题目；64 KB 里放不进两张 `0xB800` |

读者看到的章号仍是文件名前缀加 1：文件 `16` 在书里是第 17 章，`17` 是第 18 章，`18` 是第 19 章，`19` 是第 20 章。源文件的一级标题继续带 `16`、`17`、`18`、`19`。这一批不改这个加 1。

第 02 章已经钉过上电 HSI 是 8 MHz，HSE 失败后 SYSCLK 回到这只 8 MHz，PCLK2 在本书时钟树里不分频。第 03 章已经钉过第 10 脚 PA0 上的外接灯串 270 Ω，第 2 脚 PC13 只允许灌电流、不能当电流源。第 06 章已经钉过 USART1 在第 30 脚 PA9、第 31 脚 PA10，72 MHz、16 倍、BRR `0x271`、分频 39.0625、误差 0、115200。第 09 章已经钉过换算分母 4096，码 2048 在名义 3.3 V 下是 1.65 V；分母 4095 偏一个 LSB。第 11 章已经钉过 LSE 32.768 kHz、PRL = 32767、第 3 脚和第 4 脚、第 1 脚 VBAT，以及 IWDG 在 Stop 和 Standby 里继续计数。第 12 章已经钉过一张 APP：`0x08004800` 起，长度 `0xB800`，到 `0x08010000` 之前。第 15 章已经钉过 1 ms 节拍、`0x50`，以及 HAL 时基是 TIM4。这几张图都不重画。167 ns、21 µs、17.2% 不进这四章的四块。

对照 v1.3.0 核对过的事实：

1. **这四章还没有四块。** 已经加厚的章在 `<!-- /video: -->` 之后、学习目标之前，有 `## 原理与边界`、`## 关键插图`、`## 时序或状态`、`## 坑与出处卡`（英文是 `Principle and boundary`、`Key figures`、`Timing or state`、`Pitfalls and source cards`）。这四章仍从学习目标写起。第 16 章和第 17 章的中文坑还在 `## ⚠️ 常见坑与排查`，英文坑还在 `## ⚠️ Pitfalls and troubleshooting`。第 18 章和第 19 章没有这个旧标题，不必为了删它而先造一个空标题。
2. **第 16 章把 Stop 的两格并成了「约 14~20 µA」，并把醒来的 HSI 写成「约 8/16 MHz」。** 罗盘同一句是「Stop 典型值约 14~20 µA」，附录 D「Stop 之后的时钟」也是这句。DS5319 Rev 20 表 16，典型值在 TA = 25°C。VDD = 3.3 V 那一列，按印出的条件从上到下是：Stop、主稳压器运行、内部 RC 与 HSE 关、无独立看门狗，**24 µA**；同一条件但稳压器在低功耗模式，**14 µA**；Standby、LSI 与 IWDG 都开，**3.4 µA**；Standby、LSI 开、IWDG 关，**3.2 µA**；Standby、LSI 与 IWDG 关、LSE 与 RTC 关，**2 µA**；备份域、LSE 与 RTC 开，**1.4 µA**。2.4 V 那一列是 23.5、13.5、2.6、2.4、1.7、1.1。85°C 最大值里，前两格是 200 µA 和 180 µA，不是典型值。正文的「14~20」和「2~3」都不是表上的格子。「8/16 MHz」把 F4 的 16 MHz 写进了这颗料。第 02 章的 HSI 是 8 MHz。表 26：从低功耗稳压器的 Stop 醒来，典型 5.4 µs，时钟是 8 MHz 的 HSI；主稳压器那格是 3.6 µs；Sleep 是 1.8 µs，而且沿用睡前的时钟；Standby 是 50 µs，然后走复位。正文「几十 µs」「几百 µs ~ ms」对不上这四格。表 27 的 PLL 锁定最大值是 200 µs，那是上限，不是表 26 的唤醒时间。本书代码走 `PWR_LOWPOWERREGULATOR_ON`，对的是 14 µA 和 5.4 µs 那一格，不是 24 µA。表 18：Sleep、72 MHz、外设全开，典型 14.4 mA；外设全关，典型 5.5 mA。条件是 25°C、3.3 V。正文「10~20 mA」盖不住 5.5 mA 那一格。`HAL_SuspendTick` 的注释写「每秒唤醒一次」。第 15 章的节拍是 1 ms。Sleep 里时钟还在跑，SysTick 若留在 1000 Hz，每 1 ms 醒一次。Stop 里 1.8 V 域的时钟停了，SysTick 不会在睡眠期间每 1 ms 跳。`HAL_RTCEx_SetWakeUpTimer_IT` 和 `RTC_WAKEUPCLOCK_CK_SPRE_16BITS` 是 F4 的句子，注释自己也写了「F4 风格」。STM32F103C8T6 没有这只周期唤醒定时器。定时叫醒走第 11 章的闹钟。第 10 脚 PA0 同时是 WKUP、ADC12_IN0 和第 03 章的外接灯。Standby 的 WKUP 是上升沿。图上不把灯、ADC 和按键画成同时有效。
3. **第 17 章的故障地址已经在罗盘和附录 D，主图仍是 SWO 动画。** 罗盘：`CFSR` 在 `0xE000ED28`，`HFSR` 在 `0xE000ED2C`，`MMFAR` 在 `0xE000ED34`，`BFAR` 在 `0xE000ED38`。`HFSR.FORCED` 是 bit 30，值 `0x40000000`。`BFAR` 只有 `CFSR` bit 15（`BFARVALID`）为 1 时才有效。72 MHz 时 72 个 DWT 周期是 1 µs。M3/M4 的硬件断点比较器是 6 个，M7 是 8 个。附录 D 同一笔还写着：先置 `DEMCR` `0xE000EDFC` 的 bit 24，再读 `DWT_CYCCNT` `0xE0001004`。正文有一处已经写了 `TRCENA`，坑表仍只说「DWT 未使能」。没置 bit 24 时，读回的周期差是 0。这是主图的失败路径。第 01 章已经把第 34 脚 PA13、第 37 脚 PA14 钉成 SWD，第 39 脚 PB3 复位后是 JTDO，重映射里才有 TRACESWO。SWO 不进这一章主图的正常路径。`debug-swo.svg` 不重画。正文「速度可达 10+ MHz」和「数据观察点 2~4 个」没有印成这一章的格子，不进四块。这颗 C8 是 Cortex-M3，没有 FPU。`-mfpu=fpv4-sp-d16` 在这颗料上作废。167 ns 留在第 04 章。
4. **第 18 章写明 38 条，若干条和已经冻住的账不一致。** 编号是 C1–C8、D1–D7、P1–P9、H1–H7、R1–R7，一共 38。这个数保留。P9 写「32.768 kHz 晶振 + 6 pF」。第 11 章的四块不写皮法。DS5319 Rev 20 的 LSE 节印的是 5 pF 到 15 pF 的陶瓷电容范围，按晶振来选，不是必须 6 pF。R1 写「Timebase Source 改为 TIMx」。第 15 章的例程是 TIM4。R2 没有写 `0x50`。P3 只写「退回 HSI」，没有写 8 MHz，也没有写 `0x271` 在 8 MHz 下是 12800。H1 的「220~1 kΩ」不是第 03 章的 270 Ω。H4 的 100 nF 和 DS5319 图 31 的 0.1 µF 是同一只电容，可以留下，但要写成图 31 的数。D7 指向第 17 章，四块不把 `BFAR` 的旧值当成这次的地址。排错节的「90%」不是测量，不进四块。
5. **第 19 章把两张 APP 说成第 12 章的地图，并把 ADC 分母写成 4095。** 第 12 章的地图是 Bootloader 16 KB、参数区 2 KB、一张 APP 46 KB。`16 + 2 + 46 = 64`。再放一张同样的 `0xB800`，是 `16 + 2 + 46 + 46 = 110` KB，结束地址 `0x0801B800`，越过 `0x08010000`。项目 5 的「见第 12 章」因此不成立。`0x5A5A0001` 不在 `examples/iap-bootloader` 里，不升格成钥匙。项目 3 的 `code * 3.3 / 4095` 和第 09 章冲突。项目 4 的帧是 `4 + 64×2 + 1 = 133` 字节。第 14 章全速批量的一包上限是 64 字节。133 是应用帧，不是 `wMaxPacketSize`。项目 7 的 `LA_DEPTH` 是 `64 * 1024 = 65536` 字节。这颗 C8 的 SRAM 是 20 KB，也就是 20480 字节。65536 放不进这颗料。那一节自己写的是 F411/F407，四块写明这只数组在 C8 上作废，不编那两颗料的 SRAM 容量。项目 1 把电机方向写在 PA0。第 10 脚已经是第 03 章的灯、第 09 章的 ADC 和 WKUP。四块不给电机新分配一只脚。项目 8 的两端 120 Ω 跟第 13 章同一笔。工时和星级留在项目节，不进四块。
6. **许可门与已有 id 保持原样。** 允许吸收的仍是 ST 手册里的事实（自己的话重写），以及 MIT、BSD-2-Clause、BSD-3-Clause、ISC、CC BY 4.0、CC BY 3.0、CC0。GPL、LGPL、CC BY-NC、CC BY-ND、Apache-2.0、保留所有权利、未写许可的材料只留链接。WS2812 的 0.4 µs、0.8 µs、1.25 µs 留在项目 6 的正文，标明那是灯珠厂商的时序，不进出处卡，不新开 id。TJA1050 的 5 V 和 SN65HVD230 的 3.3 V 仍只留在硬件清单，不进出处卡。`sources` 只追加。已有 id 一个字段都不改。
7. **全 29 章最终都要加厚。** 本批只规格化文件 `16`、`17`、`18`、`19`。再下一批仍是 4 章，章号到那时再锁。本文件不预选文件 `20` 或 `28`。密度刀 F 已经收过阅读面空白。这一批只加内容的密度，不加另一刀 CSS。

## 目标与非目标

### 目标

- 只把第 16、17、18、19 章加厚到和第 00 到第 15 章相同的四块密度。中文和英文一起写完。
- 每章一张可印刷的静态主图：正常路径和失败路径都在图上，封装脚位、地址、电流条件和时间是真的。另加一条短 GIF，只做网页和公众号辅图。
- 数字钉在已经冻结的 RM0008 Rev 21、DS5319 Rev 20、PM0056，以及这四章罗盘、附录 D 和前面各章已有的格子上。第 16 章的 Stop 在 3.3 V、25°C 分成 24 µA 和 14 µA 两格，不再写 14~20。醒来后 USART1 若仍带着 `0x271`，线上是 12800 bit/s。第 17 章的 `BFAR` 跟罗盘同一笔，72 个周期是 1 µs。第 18 章的 38 条保留，BOOT0 跟第 00 章同一笔。第 19 章的一张 APP 跟第 12 章同一笔，两张 `0xB800` 是 110 KB。
- 新出处追加进两份 manifest 的 `sources`。章内坑卡使用 `#source-...`。`CREDITS.md` 第六节记下这一批改写吸收了什么。
- 实施合入时把整书从 1.3.0 升到 **1.3.1 · 2026-10-25**。中英文共用这个版本号和这个日期。仓库里现有修订条目的日期都是 2026-10-25，本文件名也是这一天。代理日历若显示 2026-10-26，书的日期仍写 2026-10-25，不另起一天。这一批不打 tag，不创建 Release。
- 实施 PR 在 Book CI 变绿之后停下来等人复审。人接受之前不合入。Book CI 变绿不等于自动 squash 合入。

### 非目标

- 不加厚除 16、17、18、19 以外的任何章。已经加厚的 00 到 15 保持原样。文件 `28` 的 RTOS 生态不进本批。不把 17.2%、167 ns、21 µs 写进这四章的四块。
- 不重画 `sample-01-swd-vectors.svg`、`sample-02-clock-tree.svg`、`sample-03-gpio-led.svg`、`sample-04-exception-stack.svg`、`sample-06-uart-frame.svg`、`sample-09` 的 ADC 图、`sample-11-iwdg-1s.svg`、`sample-12-iap-map.svg`、`sample-13-can-bit.svg`、`sample-14-usb-enum.svg`、`sample-15-rtos-prio.svg`。第 16 章只用旁注指向第 10 脚和第 02 章的 8 MHz。第 17 章不把第 39 脚画成主图的正常路径。第 19 章不重画第 12 章那张地图的页高，只画「一张对、两张溢出」。
- 不改密度刀 F 的令牌、`book.css` 和间距。不把样式、字号、行长或页边再收一刀。不改 `stm32-book/build_html.py`。
- 不重画 29 张讲解海报，不改 `assets/video/` 里的 png、mp4、srt，不改 `tools/gen_narrated.py`。`<!-- video: -->` 与 `<!-- /video: -->` 之间的旁白保持原样。旁白不重录。
- 不重选样本，不改 `docs/superpowers/plans/` 里已有的锁定文件和来源清单。不改 `tools/scan_sample_chapters.py`。本设计 PR 不新增实施计划。
- 不改总纲、Batch2、Batch3、Batch4、Batch5 规格、观感规格、海报规格、密度规格、CONTENT_GUIDE 规格，也不改两份 `CONTENT_GUIDE.md`。
- 不实现 v1.3.0 或 v1.3.1 的 GitHub Release，也不打 `v1.3.0` 或 `v1.3.1` 的 tag。
- 出版书签仍是现在的 44 条。不把新的二级标题收进书签。
- 不改附录 A 的既有契约。附录 D 只改下面写明的那一格电流句子，不改 L476 的 1.1 µA、1.4 µA、4 µs，不改其余各行。不手改 `stm32-book/book/E-参考资料.md` 或英文对应文件。附录 E 的卡片仍由 `sources` 生成。
- 不替换、不重画已有图。第 16 章留下 `lowpower-wakeup.svg`。第 17 章留下 `debug-swo.svg`。第 18 章留下 `toolchain-flow.svg`。第 19 章留下 `peripheral-wiring.svg`。新主图是加进去的。
- 不把厂商手册、官方插图或社区原文放进仓库。
- 不加图目录或表目录，不加第 30 章，不改 `docs/00`–`28` 的文件名。不把第 19 章改名为上册。
- 不新开可烧录工程。不改 `examples/`。例程里的时基、APP 长度和过滤器位移留在例程。章节用已经冻住的说法，不回头改例程。

## 来源与许可

四层用法和总纲、Batch5 相同。

允许写进正文的，仍按这个顺序：

1. ST 的 RM、DS、PM：只吸收事实，用自己的话写，附文档号和可点击的入口。不粘贴段落，不描官方图。
2. MIT、BSD-2-Clause、BSD-3-Clause、ISC、CC BY 4.0、CC BY 3.0、CC0：可以改写教学要点。许可证不强制署名时，本书仍署名。本仓库例程是 MIT。
3. 其他许可证：只留链接。含 GPL、LGPL、CC BY-NC、CC BY-ND、Apache-2.0、保留所有权利、未写许可的帖子和视频。灯珠厂商手册和 CAN 收发器厂商手册都在这一层。

权威数字以第 1 层、罗盘边界和附录 D 已有格子为准。社区材料只支持「这个坑有人踩过」。帖子里的寄存器值，要在 RM/DS/PM 或本仓库例程上重新钉住之后才能进「原理与边界」或「时序或状态」。钉不住的，出处卡的主张写成「经验线索，未升格为规范」，并且这一行不引入新的寄存器值。

10 kΩ 上拉在 3.3 V 下是 `3.3 / 10000 = 0.33` mA。这是板上的欧姆定律，不是表 16 的 `IDD`。它可以留在核心原理，旁边写明不是芯片电流。不进出处卡。780 天那个例子用了 20 mA 和 20 µA，两数都不是表 16 或表 17 的格子。它不进四块。核心原理若还留平均电流的公式，输入要标明是假设，不得把 20 µA 写成 Stop 的典型值。不把 780 天改算成另一套规范。

### 追加的来源 id

新 id 只追加在两份 `sources` 对象的末尾。已有 id 的标题、URL、snapshot、许可、scope 都不改。中英两份的 `url`、`snapshot`、`license`、`accessed` 用同一串字符；`title`、`authority`、`scope` 用对应语言。`accessed` 用 `2026-10-25`。章罗盘的 `sources` 数组在原有 id 之后追加新 id，不删除已有 id。

DS5319 的 PDF 与已有 `ds5319-clock` 相同，Rev 20，2025-07。RM0008 的 PDF 与已有 `rm0008-rcc` 相同，Rev 21。PM0056 与已有 `pm0056` 相同。不另找一份修订。

| 新 id | 冻结点 | 用在 | 不复制 |
| --- | --- | --- | --- |
| `ds5319-pwr` | DS5319 Rev 20 表 16、表 18、表 26、表 27 的 `tLOCK`，以及第 2.3.12 节。表 16 在 TA = 25°C、VDD = 3.3 V 的典型值：Stop 主稳压器 24 µA；Stop 低功耗稳压器 14 µA；这两格都要求内部 RC 与 HSE 关、无独立看门狗。Standby 在 LSI+IWDG 开时 3.4 µA，LSI 开且 IWDG 关时 3.2 µA，LSI、IWDG、LSE、RTC 都关时 2 µA。备份域在 LSE+RTC 开时 1.4 µA，那是 `IDD_VBAT`，不是整机 Standby。85°C 的 Stop 最大值按印出的 200 µA 和 180 µA；若格子不同就改 snapshot。表 18：72 MHz、外设全开的 Sleep 典型 14.4 mA，外设全关 5.5 mA，25°C、3.3 V。表 26：Sleep 1.8 µs，Stop 主稳压器 3.6 µs，Stop 低功耗稳压器 5.4 µs，Standby 50 µs。Stop 和 Standby 的这段时间在 8 MHz HSI 上量到第一条用户指令。Sleep 沿用睡前的时钟。`tLOCK` 最大值 200 µs。第 2.3.12 节：Stop 由 EXTI 叫醒，Standby 由 NRST、IWDG、WKUP 上升沿或 RTC 闹钟退出，SRAM 在 Standby 丢失 | 第 16 章的两格微安、唤醒微秒和「14 µA 不含 IWDG」。第 18 章只交叉引用，不另造电流 | 不把 14~20 µA 写进 snapshot。不把 1.4 µA 写成整机待机。不把 200 µA 写成典型值。不改 `ds5319`、`ds5319-rtc`、`ds5319-adc` |
| `rm0008-pwr` | RM0008 Rev 21。默认先对电源控制章。进入 Stop 后 1.8 V 域时钟停止，HSI、HSE、PLL 关掉。退出 Stop 时系统时钟回到 HSI，时钟配置要重新装。`SLEEPDEEP`、`PDDS`、`LPDS` 以印出的位名为准。`PDDS=0` 且 `SLEEPDEEP=1` 是 Stop。`PDDS=1` 且 `SLEEPDEEP=1` 是 Standby。低功耗稳压器对应印出的 `LPDS`。章号或位名不同时用印出的。8 MHz 仍跟第 02 章，不在这条 snapshot 里重写 HSI 标定 | 第 16 章「醒来先是 HSI，串口之前要重配时钟」。第 17 章不使用这条 id | 不粘贴功耗曲线。不把 F4 的周期唤醒定时器写进来。不改 `rm0008-rcc`、`rm0008-rtc`、`rm0008-wdg` |
| `pm0056-dwt` | PM0056，与已有 `pm0056` 同一份手册。`DEMCR` 在 `0xE000EDFC`，bit 24 是跟踪使能。置上之后 `DWT_CYCCNT` 在 `0xE0001004` 才计数。72 MHz 下 72 个计数是 1 µs。没置 bit 24 时计数停在 0。位号若印出的不是 24，snapshot 改记印出的位，地址仍按印出的。Cortex-M3 的硬件断点比较器按印出的个数，默认 6 个；M7 的 8 个在 C8 上作废。这一条不重写 `CFSR` 的四个地址，那些已经在 `pm0056` 的 scope 里 | 第 17 章主图的失败路径：周期差为 0。第 17 章和第 18 章的硬件断点个数 | 不改 `pm0056` 和 `pm0056-nvic`。不把 167 ns 写进来。不编数据观察点的个数。不编 FPB 基址 |
| `ds5319-nrst` | DS5319 Rev 20 图 31。外部复位电路上印着 0.1 µF，接在 NRST。0.1 µF 就是 100 nF。第 7 脚仍交叉引用已有 `ds5319-swd`，不在这条对象里改脚号。图上若印出的不是 0.1 µF，用印出的电容，不保留正文里另一只纳法 | 第 18 章 H4。第 16 章只把第 7 脚留在 Standby 的唤醒源里，不把电容画进主图 | 不改 `ds5319-swd`。不把内部上拉的 30/40/50 kΩ 写进四块，除非实施打开表 39 后把印出的典型值补进这条 snapshot。没打开之前，四块不写这只上拉的千欧 |
| `ds5319-lse` | DS5319 Rev 20 的 LSE 振荡器节。CL1 与 CL2 推荐用 5 pF 到 15 pF 的陶瓷电容，按晶振的要求选取，两只通常相同。6 pF 不是这一节印出的必须值。32.768 kHz、第 3 脚、第 4 脚、PRL = 32767 仍走已有 `ds5319-rtc` 和 `rm0008-rtc` | 第 18 章 P9：删掉「必须 6 pF」 | 不改 `ds5319-rtc`。不把 6 pF 写进 snapshot。不把 ±20 ppm 写进来 |

来源清单的 `absorb` 必须含上表五个 id。没有条件追加的第六个 id。表 39 的上拉若要进正文，写进已有的新 id `ds5319-nrst`，不为此再开一个 id。

### 沿用、但不改写对象的 id

| 已有 id | 这一批怎么用 |
| --- | --- |
| `rm0008-rcc` | 第 16 章交叉引用：上电和 HSE 失败后的 HSI 是 8 MHz。PCLK2 在本书树里不分频。不改这条对象 |
| `rm0008-usart` | 第 16 章和第 18 章交叉引用：`0x271` 是 39.0625。8 MHz 下 `8e6 / (16 × 39.0625) = 12800`。不改这条对象 |
| `ds5319-usart` | 第 16 章旁注第 30 脚 PA9、第 31 脚 PA10。不重画那一帧。不改这条对象 |
| `ds5319-adc` | 第 16 章和第 19 章交叉引用：第 10 脚是 PA0-WKUP，也是 ADC12_IN0。不改这条对象 |
| `ds5319-gpio` | 第 16 章和第 18 章交叉引用：第 2 脚 PC13 不能当电流源。外接灯的 270 Ω 在第 03 章。不改这条对象 |
| `ds5319-swd` | 第 17 章和第 18 章交叉引用：第 34 脚 PA13、第 37 脚 PA14、第 7 脚 NRST、第 39 脚 PB3、第 44 脚 BOOT0。闪存 64 KB，SRAM 20 KB。不改这条对象 |
| `ds5319-rtc`、`rm0008-rtc`、`rm0008-wdg`、`pm0075-rdp` | 第 16 章交叉引用闹钟、备份域和「IWDG 在 Stop 里还在数」。14 µA 那一格不含 IWDG。不改这些对象 |
| `pm0056` | 第 17 章和第 18 章交叉引用四个故障地址和 `BFARVALID`。不改这条对象 |
| `rm0008-boot` | 第 18 章交叉引用：BOOT0=0 进主闪存；BOOT1=0 且 BOOT0=1 进系统存储器 `0x1FFFF000`。互联型的 `0x1FFFB000` 在 C8 上作废。锁存在 SYSCLK 的第 4 个上升沿。不改这条对象 |
| `project-examples` | 第 15 章的 TIM4、第 12 章的 `0xB800`、第 13 章的 120 Ω 和第 08 章的 JEDEC 字节，这一批只交叉引用。不改这条对象 |
| `rm0008-adc` | 第 19 章交叉引用分母 4096。不改这条对象 |
| `rm0008-flash` | 第 19 章交叉引用 64 KB 和半字。不改这条对象 |
| `freertos-syscall` | 第 18 章交叉引用 `0x50` 和 TIM4 所在的那一章。时基文件名仍以 `project-examples` 为准。不改这条对象 |

出处卡的字段仍是现有附录 E 的一套：`title`、`authority`、`url`、`snapshot`、`accessed`、`license`、`scope`。`url` 必须是 `https://`。章内第四块每一行只有一个主张，并带一个 `#source-`。一行写清现象、原因、处理、链接、该来源允许支持的主张。

`CREDITS.md` 第六节现在收到第 12、13、14、15 章（v1.3.0）。这一批在该节下面加一个小节「第 16、17、18、19 章（v1.3.1）」，保留前面的表。新表只列作品名、许可证、用在哪、链接。不贴手册原文。同一文件顶部的静态框图从 22 张改为 26 张，光栅动画从 20 个改为 24 个。只有第 16 章拆出第二张 SVG 时，静态框图改为 27 张，并在实施 PR 里写明拆图原因。

## 锁定

章号按文件名前缀锁死：`16`、`17`、`18`、`19`。不再按「谁更薄」重选。不改成第 20 章或第 28 章，也不把已经加厚的章再开一遍。不把文件 `19` 改名为上册。

实施开始时仍做一次核对扫描，只读这四章的中英八份。扫描确认两件事：四块标题还不存在；第 16 章和第 17 章的旧「常见坑」标题还在，第 18 章和第 19 章没有这个旧标题。结果写到新文件 `docs/superpowers/plans/2026-10-25-batch6-16-17-18-19-lock.json`，带上运行时的 `git rev-parse HEAD`。不覆盖更早的锁定文件。若扫描发现四块已经有人写过，停下来，不叠第二套标题。

来源清单写到 `docs/superpowers/plans/2026-10-25-batch6-16-17-18-19-source-list.json`，字段沿用 Batch5 清单：`chapters` 是 `["16", "17", "18", "19"]`，`absorb` 里每一条有 `license_class`、`url`、`do_not_copy`、`points`。`license_class` 只允许 `ST-facts-restated`、`MIT`、`BSD-2-Clause`、`BSD-3-Clause`、`ISC`、`CC BY 4.0`、`CC BY 3.0`、`CC0`。许可字符串里不得出现 `GPL`、`LGPL`、`CC BY-NC`、`CC BY-ND`、`All rights reserved`。清单可以先于 manifest 提交；登记以 manifest 为准。

## 章节加厚模板

四块插在 `<!-- /video: -->` 之后、学习目标之前，和第 03 章相同。标题不加表情符号，中英各出现一次：

| 块 | 中文标题 | 英文标题 | 这一块要写完的事 |
| --- | --- | --- | --- |
| 1 | `## 原理与边界` | `## Principle and boundary` | 结论钉在哪颗订货号、哪路时钟、哪一版手册；换系列时哪一句作废 |
| 2 | `## 关键插图` | `## Key figures` | 静态主图在前，图注带关键数字和文档号。短 GIF 跟在后面，图注标明辅图 |
| 3 | `## 时序或状态` | `## Timing or state` | 一张能算回去的表。时间或状态迁移和主图是同一笔账 |
| 4 | `## 坑与出处卡` | `## Pitfalls and source cards` | 钉得住的行放在这里。每行一个 `#source-` |

保留学习目标、硬件与接线、代码实现、动手实验、相关资源，以及英文的对应标题。保留 `## 🧠 核心原理` 和英文 `## 🧠 Core ideas`。第 18 章保留 38 条目录。第 19 章保留 10 个项目。和四块、罗盘或附录 D 冲突的数字，就地改成同一笔账，不保留两套说法。第 16 章和第 17 章的 `## ⚠️ 常见坑与排查` 和英文 `## ⚠️ Pitfalls and troubleshooting` 删掉，不留空标题。

视频块、旁白和已有动画图留在原处。主图不放进 `<!-- video: -->` 块。代码仍按 `docs/CONTENT_GUIDE.md`：HAL，参数用宏。

中英的订货号、文档号、寄存器名、脚位和算式一致。英文可以更短，不能少一块，也不能少一个关键数字。

## 第 16 章写什么

订货号仍是 STM32F103C8T6，LQFP48。这一章的工作点是 Stop，稳压器在低功耗模式，对应代码里的 `PWR_LOWPOWERREGULATOR_ON`。电流整格照抄 DS5319 Rev 20 表 16 的 3.3 V、25°C 典型值。时钟整格照抄第 02 章：醒来是 HSI 8 MHz。

### 原理与边界

- **两格 Stop。** 低功耗稳压器、振荡器关、无独立看门狗：14 µA。主稳压器仍开、其余条件相同：24 µA。正文和罗盘里的「约 14~20 µA」改成这两格。20 µA 不是表 16 的格子。85°C 的 200 µA 和 180 µA 是最大值，不写成典型值。1.4 µA 是备份域在 LSE 与 RTC 开着时的 `IDD_VBAT`，不是整机 Standby。
- **Standby 的三格。** 2 µA 只属于 LSI、IWDG、LSE、RTC 都关的那一格。LSI 开着是 3.2 µA。LSI 和 IWDG 都开是 3.4 µA。正文「约 2~3 µA」改成这三格。IWDG 在 Stop 和 Standby 里继续计数，这句跟第 11 章同一笔。14 µA 那一格的条件写着无独立看门狗。开着 IWDG 去引用 14 µA，是失败旁注。表 16 没有单独印出「Stop 加 IWDG」的微安，四块不编一个新的微安。
- **Sleep 的毫安。** 72 MHz、外设全开，表 18 典型 14.4 mA。外设全关，典型 5.5 mA。条件 25°C、3.3 V。「10~20 mA」不覆盖 5.5 mA 那一格，改成这两格。ADC 模拟部分另加的 0.8 mA 只有表注印出了才写进 snapshot，图上不把它当成 Sleep 的主账。
- **醒来的时钟。** Stop 退出后系统时钟是 HSI 8 MHz，不是 16 MHz，也不是 72 MHz。`8/16` 这句在 STM32F103C8T6 上作废。表 26 的 5.4 µs 是低功耗稳压器那一格，从唤醒事件到第一条用户指令，时钟仍是这只 8 MHz。主稳压器那格是 3.6 µs。这段时间不含把 PLL 装回 72 MHz。PLL 锁定的最大值是 200 µs，不和 5.4 µs 加在一起叫成「唤醒时间」。
- **12800。** 本书时钟树 PPRE2 不分频。复位默认的 APB2 预分频也是不分频。所以在 `SystemClock_Config()` 之前，USART1 的内核时钟是 8 MHz。BRR 若仍是 `0x271`，`8e6 / (16 × 39.0625) = 12800`。主机若还停在 115200，比是 9，也就是 72/8。这是主图的失败路径。正常路径是先把 PLL 装回 72 MHz，再发下一字节，线上仍是 115200。不重画第 06 章的帧。
- **1 ms，不是 1 s。** Sleep 沿用睡前的时钟。`examples/freertos-task` 的 README 把节拍写成 1000 Hz，也就是 1 ms。节拍留在这个频率时，Sleep 每 1 ms 被叫醒。注释里的「每秒一次」作废。裸机若把 HAL 节拍改成别的频率，按那个频率算，不另编一个赫兹。Stop 期间这只 SysTick 不跳。挂起的 SysTick 标志仍可能让 `WFI` 立刻返回，所以进 Stop 前仍要清标志。这句不写成「Stop 里每 1 ms 醒一次」。
- **Standby 不从 `WFI` 的下一行继续。** `PDDS=1` 时 SRAM 和普通寄存器丢失，醒来从复位向量进。WKUP 是第 10 脚 PA0 的上升沿。下降沿的 EXTI 能唤醒 Stop，不能当成 Standby 的 WKUP。表 26 的 Standby 是 50 µs 到第一条指令，然后才是复位后的启动，不是「几百微秒到几毫秒」这一句。
- **第 10 脚只选一种用法。** 这一章的 Stop 按键用 PA0 的 EXTI。第 03 章的 270 Ω 灯和第 09 章的 ADC12_IN0 是同一只脚的别的用途。主图只画按键。灯和 ADC 留在旁注，不画成同时接上。第 2 脚 PC13 的板载灯在测电流之前关掉。它不能拿来源出电流。
- **F4 的周期唤醒定时器在这颗料上作废。** 删掉或改写 `HAL_RTCEx_SetWakeUpTimer_IT` 那段，使正文不再像能在 F103 上调用它。定时叫醒交叉引用第 11 章：32.768 kHz，PRL = 32767。不重画第 11 章。
- **板子不是表 16。** 调试器还接着、PC13 的灯还亮、10 kΩ 上拉还挂着，读数就不是 14 µA。0.33 mA 是 3.3 V 除以 10 kΩ，留在核心原理，不进出处卡。

F411 的 Nucleo 按键留在硬件表，标明那是另一颗料。四块的电流和脚位只写 C8。PVD 仍不背毫伏。档位电压只有 DS5319 印出了才写进 `ds5319-pwr` 的 snapshot，这一批的主图不画 PVD。

### 关键插图

主图文件 `assets/diagrams/sample-16-stop-wake.svg`，由 `tools/gen_sample_figures.py` 追加一个函数生成，调用 `_credit()`，不调用 `Svg.footer()`。

图上是一次 Stop 和醒来后的第一字节：

- 模式：`SLEEPDEEP=1`，`PDDS=0`，低功耗稳压器。旁边标 14 µA，条件写明 3.3 V、25°C、无 IWDG。
- **正常路径。** EXTI 把 CPU 叫醒。第一条指令时的时钟是 HSI 8 MHz，表 26 标 5.4 µs。然后 `SystemClock_Config()` 把 PLL 装回 72 MHz。USART1 仍用 `0x271`，线上 115200。
- **失败路径。** 跳过重配时钟，同一只 `0x271` 在 8 MHz 上送出 12800 bit/s。
- **旁注。** 把 14 µA 用在主稳压器还开着的时候，那一格是 24 µA。把 F4 的周期唤醒定时器画进来，在 C8 上作废。第 10 脚不同时画灯。不画第 06 章的位帧。不画 780 天。

图注写「自绘」，带 DS5319 Rev 20 表 16 和表 26，以及第 02 章已经冻结的 8 MHz。替代文本写出结论：低功耗稳压器的 Stop 典型值是 14 µA；醒来先是 HSI 8 MHz；不重配时钟时 `0x271` 变成 12800 bit/s。不写「示意图」。

`lowpower-wakeup.svg` 留作辅图。关键插图写明：不播放它，14 µA、8 MHz 和 12800 都在静态主图上。

放不下 60 KB 时，把 Standby 的三格电流拆到 `assets/diagrams/sample-16-standby.svg`。第一张仍是 Stop 与 12800。拆开的两张都用 `_credit()`，都不调用 `Svg.footer()`。只允许这个第二张文件名。

### 时序或状态

一张表覆盖这次醒来。列至少有：步骤、时钟或电流、对错。必须有的行：进入 Stop，低功耗稳压器，14 µA，正常；同一模式但主稳压器开着，24 µA，不是 14 µA 那一格。唤醒行：5.4 µs 后第一条指令，HSI 8 MHz。重配行：PLL 回到 72 MHz 之后 USART1 为 115200。失败行：没有重配，`0x271` 在 8 MHz 下是 12800。Sleep 行：72 MHz 外设全开 14.4 mA，外设全关 5.5 mA；SysTick 1000 Hz 时每 1 ms 醒一次。Standby 行：`PDDS=1` 从复位向量重启；2 µA 只在 LSI 与 IWDG 与 RTC 都关时成立；IWDG 开着是 3.4 µA；到第一条指令的典型值是 50 µs。

### 坑与出处卡

至少这些行：

| 现象 | 处理方向 | 链接 | 允许的主张 |
| --- | --- | --- | --- |
| 手册被说成 Stop 约 14~20 µA | 低功耗稳压器写 14 µA，主稳压器写 24 µA | `#source-ds5319-pwr` | 两格都是 3.3 V、25°C 的典型值，并且无独立看门狗。20 µA 不是表 16 的格子 |
| 待机被说成 2~3 µA | 按 LSI 和 IWDG 有没有开，写成 2、3.2 或 3.4 µA | `#source-ds5319-pwr` | 2 µA 那一格要求 LSI、IWDG、LSE、RTC 都关。1.4 µA 是备份域，不是整机 |
| 醒来第一帧串口乱码 | 先 `SystemClock_Config()`，再发字节 | `#source-rm0008-usart` | HSI 为 8 MHz 且 BRR 仍是 `0x271` 时，波特率是 12800。72 MHz 那一格才是 115200 |
| 注释写 HSI 约 8/16 MHz | 这颗料写 8 MHz | `#source-rm0008-rcc` | F1 上电默认的 HSI 是 8 MHz。16 MHz 在 C8 上作废 |
| Sleep 里电流下不来，注释却说每秒醒一次 | 节拍若是 1000 Hz，就是每 1 ms，不是每 1 s。进 Sleep 前挂起这只节拍 | `#source-project-examples` | `examples/freertos-task` 的 README 把 `TICK_RATE_HZ` 写成 1000，1 ms 一个 tick。裸机若改了 HAL 节拍，按那个频率算。这一行不证明 Stop 期间 SysTick 还在跳 |
| 调用了 F4 的周期唤醒 API | 这颗料用第 11 章的 RTC 闹钟 | `#source-rm0008-rtc` | F103 的定时叫醒不是 `HAL_RTCEx_SetWakeUpTimer_IT`。PRL = 32767 才是 1 Hz |
| 开着 IWDG 还引用 14 µA | 14 µA 那一格不含独立看门狗 | `#source-rm0008-wdg` | IWDG 在 Stop 和 Standby 里继续计数。不新编「Stop 加 IWDG」的微安 |
| 按键下降沿唤醒了 Stop，Standby 却不醒 | Standby 的 WKUP 是第 10 脚上升沿 | `#source-ds5319-adc` | 第 10 脚是 PA0-WKUP。这一行不把 270 Ω 的灯画成同时有效 |

板级 0.33 mA 和 780 天留在核心原理。调试器还连着时的电流不进出处卡，除非以后有允许吸收的测量记录。这一批不追加。

### 短 GIF

辅图 `assets/gif/stop-wake.gif`。内容是正常路径：从 Stop 醒来，时钟从 HSI 8 MHz 装回 72 MHz，然后标出 115200。帧数不少于 3、不多于 12。12800 和 24 µA 只放在静态主图上。不替换 `lowpower-wakeup.svg`。

## 第 17 章写什么

订货号仍是 STM32F103C8T6。故障地址整格照抄罗盘和附录 D。DWT 的 1 µs 跟罗盘同一笔：72 MHz 下 72 个周期。

### 原理与边界

- **先看 CFSR。** `CFSR` 在 `0xE000ED28`。`HFSR` 在 `0xE000ED2C`。`FORCED` 是 bit 30，值 `0x40000000`，表示这次硬故障是从别的故障升级来的，原因在 `CFSR`。`MMFAR` 在 `0xE000ED34`。`BFAR` 在 `0xE000ED38`。
- **旧地址。** `BFARVALID` 是 `CFSR` bit 15。这一位为 0 时，`BFAR` 里的数不是这次访问的地址。把它当成这次的地址，是主图的失败路径。`MMFAR` 同样要等它自己的有效标志。有效标志的位号只有 PM0056 印出了才写进 snapshot。没印出之前，四块只对 `BFAR` 写死 bit 15。
- **八个字。** 异常压栈是 R0、R1、R2、R3、R12、LR、PC、xPSR。PC 在 `stack[6]`。这跟第 04 章是同一次入栈。四块可以写「第 6 个字是 PC」。四块不写 167 ns，不重画那张入栈图。
- **1 µs。** 先把 `DEMCR` `0xE000EDFC` 的 bit 24 置 1，再把 `DWT_CYCCNT` `0xE0001004` 清零并打开周期计数。72 个计数是 1 µs。没置 bit 24 时，前后两次读数的差是 0。这是主图上的另一处失败，和 `BFAR` 的失败画在同一张图里：一个是地址无效，一个是计数没开。
- **六只硬件断点。** 这颗 M3 是 6 个。M7 的 8 个在 C8 上作废。数据观察点的「2~4 个」不进四块。
- **调试脚不进正常路径。** 第 34 脚 PA13 是 SWDIO，第 37 脚 PA14 是 SWCLK，跟第 01 章同一笔。第 39 脚 PB3 复位后是 JTDO。关掉 JTAG、留下 SWD 之后，重映射列里才是 TRACESWO。把 PB3 说成上电就是 SWO，是旁注里的失败。全关 SWJ 会把探针弄丢。主图不画 SWO 波形。`debug-swo.svg` 留作辅图。
- **没有 FPU。** `-mfpu=fpv4-sp-d16` 和 Cache 一致性在这颗料上作废，留在核心原理，不进四块的正常路径。
- **10+ MHz 不进四块。** 正文若还留「SWD 可达 10+ MHz」，旁边写明这不是 DS5319 或 PM0056 已经收进出处卡的速率。四块不写这个数。

### 关键插图

主图文件 `assets/diagrams/sample-17-cfsr.svg`。

图上是一次硬故障和一次 1 µs 的测量：

- 寄存器：`CFSR` `0xE000ED28`，`HFSR` `0xE000ED2C`，`BFAR` `0xE000ED38`。`FORCED` 标成 bit 30。
- **正常路径。** bit 15 为 1，`BFAR` 是这次的地址。旁边 `DEMCR` bit 24 已经置 1，72 个 `CYCCNT` 标成 1 µs。PC 标在压栈的第 6 个字。
- **失败路径。** bit 15 为 0，仍去读 `BFAR`。另一处没置 bit 24，周期差是 0。
- **旁注。** 第 39 脚仍是 JTDO，不标成已经在输出 SWO。不画 8 个寄存器的时序波形。不写 167 ns。

图注写「自绘」，带 PM0056 的故障地址和 DWT 使能顺序。替代文本写出结论：`BFAR` 要 bit 15 为 1 才有效；72 MHz 下 72 个周期是 1 µs，而且要先打开 `DEMCR` bit 24。不写「示意图」。

`debug-swo.svg` 留作辅图。SWO 和 ITM 不进这张静态主图。

### 时序或状态

一张表覆盖这一次读取。列至少有：寄存器或计数、地址或位、什么时候有效。必须有的行：`CFSR`，`0xE000ED28`，先读。`HFSR` bit 30，`0x40000000`，`FORCED`。`BFAR`，`0xE000ED38`，仅 bit 15 为 1。失败行：bit 15 为 0，地址作废。DWT 行：先 `0xE000EDFC` bit 24，再 `0xE0001004`；72 计数等于 1 µs；bit 24 为 0 时差值为 0。断点行：这颗 M3 是 6 个。脚位行只作交叉引用：第 34 脚、第 37 脚是 SWD；第 39 脚默认 JTDO。

### 坑与出处卡

至少这些行：

| 现象 | 处理方向 | 链接 | 允许的主张 |
| --- | --- | --- | --- |
| `BFAR` 里有个数，但对不上这次访问 | 先看 `CFSR` bit 15 | `#source-pm0056` | bit 15 为 0 时，`BFAR` 不是这次的地址。`BFAR` 在 `0xE000ED38` |
| 一进 HardFault 就只复位 | 先留下 `CFSR` 和压栈的 PC | `#source-pm0056` | `CFSR` 在 `0xE000ED28`。`FORCED` 是 `HFSR` bit 30，值 `0x40000000` |
| DWT 测出来是 0 | 先置 `DEMCR` bit 24，再开 `CYCCNT` | `#source-pm0056-dwt` | bit 24 未置时周期计数不走。72 MHz 下 72 个计数是 1 µs |
| 断点打到第 7 个就不停 | 这颗 M3 只有 6 个硬件断点 | `#source-pm0056-dwt` | 印出的个数以 snapshot 为准，默认 6 个。M7 的 8 个在 C8 上作废。这一行不规定数据观察点的个数 |
| SWO 没有波形，PB3 却当成已经打开 | 复位后第 39 脚是 JTDO | `#source-ds5319-swd` | TRACESWO 在重映射列。它不是 PA13，也不是 PA14 |
| 优化之后断言还在，时序却变了 | 先有同条件的周期数，再改优化等级 | `#source-pm0056-dwt` | 没有 bit 24 和 `CYCCNT` 的对照，加速不算证据。这一行不引入新的编译器开关 |

半主机、ITM 端口 0 和 `addr2line` 留在核心原理。半主机没有新的允许吸收来源时，不进出处卡。

### 短 GIF

辅图 `assets/gif/cfsr-read.gif`。内容是正常路径：读 `CFSR`，bit 15 为 1，然后 72 个计数走完 1 µs。帧数不少于 3、不多于 12。bit 15 为 0 和周期差为 0 只在静态主图上。不替换 `debug-swo.svg`。

## 第 18 章写什么

订货号仍是 STM32F103C8T6。这一章是索引，不是第二套外设教程。38 条都留着。四块只钉「认不出芯片时先看哪一次」，以及那些和前面各章冲突的格子。

### 原理与边界

- **38 条。** C1 到 C8 是 8 条，D1 到 D7 是 7 条，P1 到 P9 是 9 条，H1 到 H7 是 7 条，R1 到 R7 是 7 条。`8 + 7 + 9 + 7 + 7 = 38`。目录、英文页和四块都写 38。不写成 30 多条。
- **先看线。** 下载器报没有目标时，先核对第 34 脚 PA13 = SWDIO、第 37 脚 PA14 = SWCLK、共地、3.3 V，以及第 7 脚 NRST。图 31 的外部复位电容是 0.1 µF。然后再看代码和优化等级。先改 `-O2`，是主图的失败路径。
- **BOOT0。** 第 44 脚 BOOT0 = 0 时，从主闪存 `0x08000000` 启动。BOOT1 = 0 且 BOOT0 = 1 时，进系统存储器 `0x1FFFF000`，用户程序看起来像没烧进去。互联型的 `0x1FFFB000` 在这颗 C8 上作废。锁存在复位后 SYSCLK 的第 4 个上升沿，跟第 00 章同一笔。不重画第 01 章把第 35 脚当成 SWCLK 的那张图。第 35 脚仍是 VSS_2，只在旁注指向第 01 章。
- **容量。** C3 的 64 KB 和 C4 的 20 KB 跟 `ds5319-swd` 同一笔。不另写一个容量。
- **P3 的乱码。** HSE 没起来时 SYSCLK 是 HSI 8 MHz。USART1 的 `0x271` 在这只时钟上是 12800，不是 115200。这句和第 16 章同一笔，这一章不另画位帧。
- **P9 的 6 pF。** 删掉「必须 6 pF」。LSE 仍是 32.768 kHz，PRL = 32767，第 3 脚和第 4 脚，第 1 脚 VBAT。电容按 DS5319 的 5 pF 到 15 pF 范围，跟晶振一起选。6 pF 不是必须值。
- **R1 的时基。** 仓库例程把 HAL 时基放在 TIM4，不是笼统的 TIMx。SysTick 留给内核。一个 tick 是 1 ms。
- **R2 的优先级。** 数值大于等于 5 才能调用 FromISR。`5 << 4 = 0x50`。跟第 15 章同一笔，不重画那张优先级图。
- **H1 的电阻。** 外接灯跟第 03 章：第 10 脚、270 Ω。PC13 不拿来源出电流。「220~1 kΩ」不进四块。
- **H4。** 第 7 脚上的电容按图 31 写 0.1 µF。看门狗那一支只指向第 11 章，不重算 1 秒。
- **90% 不进四块。** 排错五步可以留在后面的方法节。不把「90% 的问题」写成测量结果。

### 关键插图

主图文件 `assets/diagrams/sample-18-boot-triage.svg`。

图上是「没有目标」时的第一眼：

- 脚位：第 34 脚 PA13 = SWDIO，第 37 脚 PA14 = SWCLK，第 7 脚 NRST 上 0.1 µF，第 44 脚 BOOT0。
- **正常路径。** BOOT0 = 0，从 `0x08000000` 启动，探针接在第 34 脚和第 37 脚。
- **失败路径。** BOOT0 = 1 且 BOOT1 = 0，CPU 在 `0x1FFFF000`。旁边一条旁注：还没看这四只脚，先去改优化等级。
- **旁注。** 第 35 脚不是 SWCLK，指向第 01 章。不画 38 个图标。不画 CFSR 的位。

图注写「自绘」，带 DS5319 Rev 20 图 31 和表 5，以及 RM0008 的启动脚。替代文本写出结论：认不出芯片时先看第 34 脚、第 37 脚和第 44 脚；BOOT0 为 1 且 BOOT1 为 0 时跑的是 `0x1FFFF000`。不写「示意图」。

`toolchain-flow.svg` 留作辅图。编译箭头不进这张静态主图。

### 时序或状态

一张表覆盖这一次连接。列至少有：先看什么、值、下一步。必须有的行：第 34 脚和第 37 脚接好，共地，有 3.3 V。NRST 行：第 7 脚，0.1 µF。BOOT 行：BOOT0 = 0，主闪存 `0x08000000`；BOOT0 = 1 且 BOOT1 = 0，`0x1FFFF000`，失败。优化行：线还没核对时就改 `-O2`，失败。容量行：闪存 64 KB，SRAM 20 KB。串口行：HSI 8 MHz 且 `0x271` 仍在，12800。时基行：TIM4，不是 TIMx。优先级行：数值大于等于 5。晶振行：5 pF 到 15 pF 按晶振选取，6 pF 不是必须值。

### 坑与出处卡

至少这些行：

| 现象 | 处理方向 | 链接 | 允许的主张 |
| --- | --- | --- | --- |
| 下载器报没有目标 | 先看第 34 脚、第 37 脚、地和 3.3 V | `#source-ds5319-swd` | 第 34 脚 PA13 是 SWDIO，第 37 脚 PA14 是 SWCLK。第 35 脚是 VSS_2 |
| 程序像没烧进去 | 第 44 脚 BOOT0 放回 0 | `#source-rm0008-boot` | BOOT1=0 且 BOOT0=1 时进 `0x1FFFF000`。C8 不是互联型 |
| 复位脚空着，板子自己在复位 | 按图 31 加 0.1 µF | `#source-ds5319-nrst` | 图 31 的外部复位电路是 0.1 µF。这一行不新写上拉的千欧 |
| 链接说 Flash 或 RAM 不够 | C8 是 64 KB 闪存、20 KB SRAM | `#source-ds5319-swd` | xB 的 128 KB 在 C8T6 上作废 |
| 串口乱码，时钟却没核对 | 确认没有掉回 HSI 8 MHz | `#source-rm0008-usart` | `0x271` 在 72 MHz 下是 115200，在 8 MHz 下是 12800 |
| 按 P9 焊了 6 pF | 电容按晶振在 5 pF 到 15 pF 里选 | `#source-ds5319-lse` | 6 pF 不是 LSE 节印出的必须值。32.768 kHz 和 PRL = 32767 仍以第 11 章为准 |
| 上了 FreeRTOS 之后 `HAL_Delay` 不返回 | 时基改到 TIM4 | `#source-project-examples` | `examples/freertos-task` 的时基是 TIM4。不写成笼统的 TIMx |
| 一进中断就停在 `configASSERT` | 抢占优先级写成 5 或更靠后的数 | `#source-freertos-syscall` | `5 << 4 = 0x50`。数值更小的中断不得调用 FromISR |
| 外接灯不亮，电阻却在 220 Ω 到 1 kΩ 之间乱试 | 外接灯用第 03 章的第 10 脚和 270 Ω | `#source-ds5319-gpio` | 第 2 脚 PC13 不能当电流源。这一行不新造一只电阻 |

I2C 的 4.7 kΩ、W25Q 的 `0xEF 0x40 0x17` 和 Mode 0 留在各自的章。P5 的全 `0xFF` 可以是片选没拉低，也可以是擦除态。出处卡不把 `0xFF` 写成 JEDEC ID。

### 短 GIF

辅图 `assets/gif/boot0-low.gif`。内容是正常路径：第 44 脚为 0，探针接在第 34 脚和第 37 脚，目标出现。帧数不少于 3、不多于 12。BOOT0 为 1 和「先改优化等级」只在静态主图上。不替换 `toolchain-flow.svg`。

## 第 19 章写什么

订货号仍是 STM32F103C8T6。十个项目都留着。这一章的四块不新设计第十一个项目。它只钉：写在 C8 上的数必须放得进这颗料，并且和第 12 章、第 09 章是同一笔账。文件名和标题保持「项目实战合集」。

### 原理与边界

- **一张 APP。** Bootloader `0x08000000` 起 16 KB，参数区 `0x08004000` 起 2 KB，APP `0x08004800` 起 46 KB，长度 `0xB800`，到 `0x08010000` 之前。`16 + 2 + 46 = 64`。这是第 12 章和 `examples/iap-bootloader` 的地图。正常路径就是这一张。
- **两张放不下。** 再放一张同样的 `0xB800`，合计 `16 + 2 + 46 + 46 = 110` KB。`0x08000000 + 0x1B800 = 0x0801B800`，越过 `0x08010000`，多出来的正好又是 46 KB。项目 5 里「Bootloader + 参数区 + APP_A + APP_B（见第 12 章）」这句改掉。第 12 章没有第二张槽。把 46 KB 再切成两只 23 KB 是另一份设计，不是这张图的正常路径，也不写成「见第 12 章」。`0x5A5A0001` 留在项目草稿里，不进出处卡。
- **65536 字节的数组。** `64 * 1024 = 65536`。C8 的 SRAM 是 20 KB = 20480 字节。65536 大于 20480。项目 7 写的是 F411 或 F407。四块写明这只数组在 STM32F103C8T6 上作废。不编 F411 或 F407 的 SRAM 容量。
- **分母 4096。** 项目 3 的 `3.3 / 4095` 改成 `3.3 / 4096`。码 2048 在名义 3.3 V 下是 1.65 V。跟第 09 章同一笔。这一章不重画采样电容。
- **133 不是一包。** 项目 4 的帧长 `4 + 128 + 1 = 133` 字节。第 14 章全速批量的一包上限是 64 字节。133 要拆开送。不把 133 写成 `wMaxPacketSize`。48 MHz 和 `0x1209/0x0001` 只交叉引用，不重画第 14 章。
- **CAN。** 项目 8 的两端各 120 Ω、工作脚 PB8/PB9、500 kbit/s，跟第 13 章同一笔。收发器是 5 V 还是 3.3 V，留在硬件清单，不进出处卡。
- **第 10 脚。** 项目 1 的方向脚若写在 PA0，和灯、ADC、WKUP 撞在一起。正文改成不要把方向脚放在第 10 脚。四块不新指定一只替代脚。
- **一轮一个新外设。** 这是这一章的方法，不是新的电气限额。工时和星级不进四块，也不进出处卡。
- **灯珠时序。** 0.4 µs、0.8 µs、1.25 µs 若留在项目 6，旁边写明那是灯珠厂商的数，不是 RM0008。不进四块。

### 关键插图

主图文件 `assets/diagrams/sample-19-flash-fit.svg`。

图上是这 64 KB 和这 20 KB：

- 闪存：`0x08000000` 到 `0x08010000`。16 KB、2 KB、46 KB 三块，APP 长度 `0xB800`。
- **正常路径。** 只有一张 APP，结束在 `0x08010000` 之前。SRAM 标成 20 KB = 20480 字节。
- **失败路径。** 第二张 APP 也标成 `0xB800`，从 `0x08010000` 画到 `0x0801B800`，落在 64 KB 外面。旁边 SRAM 上画一只 65536 字节的数组，超出 20480。
- **旁注。** 分母写成 4095。133 字节被当成一包 USB。不画电机脚。不画 WS2812 的波形。不把 `0x5A5A0001` 标成钥匙。

图注写「自绘」，带第 12 章已经冻结的地图和 DS5319 的 64 KB / 20 KB。替代文本写出结论：C8 只有一张 `0xB800` 的 APP；两张是 110 KB；65536 字节大于 20 KB SRAM。不写「示意图」。

`peripheral-wiring.svg` 留作辅图。接线总览不代替这张地图。

### 时序或状态

一张表用这 64 KB。列至少有：对象、长度、结束于、放不放得下。必须有的行：Bootloader，16 KB，`0x08004000`，放下；参数区，2 KB，`0x08004800`，放下；一张 APP，`0xB800`，`0x08010000`，放下。失败行：两张 `0xB800`，`0x0801B800`，110 KB，放不下。SRAM 行：20480 字节放下；65536 字节在 C8 上放不下。ADC 行：分母 4096，码 2048 是 1.65 V；分母 4095 失败。USB 行：应用帧 133 字节，一包上限 64 字节。

### 坑与出处卡

至少这些行：

| 现象 | 处理方向 | 链接 | 允许的主张 |
| --- | --- | --- | --- |
| 升级方案写成两张 APP，并注明见第 12 章 | C8 上先按一张 `0xB800` 做通 | `#source-project-examples` | `examples/iap-bootloader` 的 APP 长度是 `0xB800`。第 12 章没有第二张槽 |
| 第二张镜像链接到 `0x08010000` 之后 | 64 KB 在 `0x08010000` 结束 | `#source-ds5319-swd` | STM32F103x8 的闪存是 64 KB。两张 46 KB 加上 16 KB 和 2 KB 是 110 KB |
| 逻辑分析仪缓冲在 C8 上链不过 | `64 * 1024` 不要编进这颗料 | `#source-ds5319-swd` | SRAM 是 20 KB，即 20480 字节。65536 更大。这一行不给出 F411 或 F407 的容量 |
| 示波器电压偏一个 LSB | 分母用 4096 | `#source-rm0008-adc` | 码 2048 在名义 3.3 V 下是 1.65 V。4095 会偏一个 LSB |
| 采集卡把 133 字节写成端点包长 | 全速批量一包最多 64 字节 | `#source-project-examples` | 133 是 `4 + 128 + 1`。它不是第 14 章的包上限 |
| 小车方向写在 PA0 | 换离第 10 脚 | `#source-ds5319-adc` | 第 10 脚是 PA0-WKUP，也是 ADC12_IN0。这一行不新分配电机脚 |
| 两个 CAN 节点速率对不上 | 用第 13 章的 500 kbit/s，两端各 120 Ω | `#source-project-examples` | 例程的预分频是 9，工作脚是 PB8/PB9。这一行不规定收发器是 5 V 还是 3.3 V |

工时、星级、`0x5A5A0001` 和灯珠的微秒留在项目正文。它们不进出处卡。

### 短 GIF

辅图 `assets/gif/one-slot.gif`。内容是正常路径：16 KB、2 KB 和一张 `0xB800` 依次填到 `0x08010000` 为止。帧数不少于 3、不多于 12。第二张 APP 和 65536 字节的数组只在静态主图上。不替换 `peripheral-wiring.svg`。

## 插图标准

沿用总纲和 Batch5 的逼真、翔实、生动、可印刷、自绘。主图和短 GIF 分开。简化示意图可以留在章内当辅图，不能充当关键插图的主图。

静态主图要让人能对着封装和仪器核对：

- 第 16 章画出 14 µA 那一格的条件、HSI 8 MHz，以及 `0x271` 在 8 MHz 下的 12800。不画成三只没有数字的电池。
- 第 17 章画出 `0xE000ED28`、bit 15 和 72 个计数等于 1 µs。不画成没有地址的三个方框。
- 第 18 章画出第 34 脚、第 37 脚、第 44 脚和 `0x1FFFF000`。不画成 38 个图标。
- 第 19 章画出 `0x08010000` 和 `0x0801B800`，以及 20480 与 65536。不画成没有地址的两个项目符号。

静态主图的文件规则：

- 用 `tools/svgkit.py`，生成脚本是 `tools/gen_sample_figures.py`。四章各一张，中英引用同一文件。中文路径 `../assets/diagrams/...`，英文路径 `../../assets/diagrams/...`。第 16 章只有在单张超过 60 KB、拆图之后才增加第二张 `sample-16-standby.svg`。
- 不调用 `Svg.footer()`。落款用脚本里已有的 `_credit()`：左侧是文档号，右侧是「自绘 · 静态 · CC BY 4.0」。
- 没有 `<animate`、`@keyframes`、`animation:`。图上同时有正常路径和失败路径。
- 替代文本写结论。图注写「自绘」，不写「实拍」「手册截图」「矢量动画」。
- 单张小于 60 KB。放不下就拆成主图加局部，每张仍争取小于 60 KB。拆开仍超过时，在实施 PR 里写出字节数和原因，不把图画回简笔，也不把 60 KB 改成仓库新默认值。
- 登记进 `assets/README.md` 第四节，和已有的 `sample-00` 到 `sample-15` 主图并列。`gen_sample_figures.py` 那一行注释补上第 16、17、18、19 章。

短 GIF：

- 四条都走 `tools/gen_gifs.py`，加入 `BUILDERS`，这样 `tools/check_assets.py` 能逐像素对上重新生成的帧。GIF 上的字用 ASCII。
- 每条少于 500 KB，帧数见上面四节。图注写明它是网页和公众号辅图，印刷以静态主图为准。
- `gen_gifs.chrome()` 自带的页脚可以留在 GIF 里。那条页脚不是静态主图的 `Svg.footer()`。
- 不改已有 20 个 BUILDERS 的像素：`led-blink`、`pwm-breath`、`uart-bits`、`i2c-timing`、`dma-ring`、`sar-adc`、`nvic-preempt`、`uart-idle`、`clock-css`、`pwm-1khz`、`spi-jedec`、`adc-sample`、`swd-fetch`、`i2c-addr`、`dma-cndtr`、`iwdg-1s`、`iap-jump`、`can-500k`、`usb-48m`、`rtos-tick`。不重跑它们来换画面。
- `tools/svg2gif.py` 这一批不当成必经步骤，也不为了它去改 CI。`assets/README.md` 第五节把「上面 20 张 GIF」改成「上面 24 张 GIF」。

PDF 关掉动画之后，读者只看静态主图和图注，就能指出失败发生在哪一段。第 16 章是「没把时钟装回 72 MHz，`0x271` 在 8 MHz 上变成 12800」。第 17 章是「`BFARVALID` 为 0 仍读 `BFAR`，或 `DEMCR` bit 24 没置，周期差为 0」。第 18 章是「BOOT0 为 1，CPU 在 `0x1FFFF000`，或者还没看线就改优化等级」。第 19 章是「第二张 `0xB800` 画过了 `0x08010000`」。

## 工作流与 PR 节奏

### 本 PR（设计）

只新增 `docs/superpowers/specs/2026-10-25-classic-encyclopedia-batch6-16-17-18-19-design.md`。不改 `docs/16`、`docs/17`、`docs/18`、`docs/19` 和 `docs/en/` 的章节。不改 `stm32-book/`、`CREDITS.md`、`assets/`、`tools/`。不升版本，不打 tag，不发 Release。不新增 `docs/superpowers/plans/` 下的实施计划。不改样式，不重画海报。本 PR 等人审阅规格后再合入，不在 CI 变绿后自动合。

### 实施 PR（下一轮，不在本 PR）

顺序固定：

1. **核对扫描。** 写出 `2026-10-25-batch6-16-17-18-19-lock.json`。章号保持 16、17、18、19。
2. **许可门。** 写出 `2026-10-25-batch6-16-17-18-19-source-list.json`。先有清单，再改正文。
3. **静态主图和短 GIF。** 先提交 SVG、GIF 和生成脚本，再写正文。主图不依赖 GIF。
4. **中英加厚。** 八份 Markdown 一起提交。视频块以内的字节保持不变。文件 `00` 到 `15`，以及 `20` 到 `28`，正文 diff 为空。
5. **登记。** 新来源追加进两份 manifest。更新这四章罗盘的来源数组。第 16 章罗盘里的「约 14~20 µA」改成 14 µA 与 24 µA 两格，并写明 3.3 V、25°C、无独立看门狗。HSI 8 MHz 那句保留。`CREDITS.md` 第六节增加 v1.3.1 小节，并把静态框图改为 26 张、光栅动画改为 24 个。若拆出 `sample-16-standby.svg`，静态框图改为 27 张。`revisions.json` 在条目最前加上 1.3.1，日期写死 `2026-10-25`。两份 manifest 的 `version` 改为 `1.3.1`，`date` 改为 `2026-10-25`。`stm32-book/README.md` 的当前版本句改为 **v1.3.1 · 2026-10-25**。发布一节里的 tag 名改成 `v1.3.1`，并在现有「也不要把 1.2.9 的产物标成 1.3.0」之后加上「也不要把 1.3.0 的产物标成 1.3.1」。这一步仍不创建 tag，也不创建 Release。修订说明只写这四章加厚了什么，用文件名前缀。中英各两句，例如：第 16 章写上 Stop 低功耗稳压器在 3.3 V、25°C 是 14 µA，主稳压器那一格是 24 µA；醒来是 HSI 8 MHz，BRR 仍为 `0x271` 时线上是 12800 bit/s。第 17 章写上先看 CFSR，BFAR 要 bit 15 为 1 才有效；72 个 DWT 周期是 1 µs，要先置 DEMCR bit 24。第 18 章写上认不出芯片时先看第 34 脚、第 37 脚和第 44 脚 BOOT0；BOOT0=1 且 BOOT1=0 进的是 `0x1FFFF000`。第 19 章写上 C8 的一张 APP 是 `0xB800`，两张 `0xB800` 是 110 KB；`64×1024` 字节大于 20 KB SRAM。英文用同样的事实。
6. **术语表那一格。** `stm32-book/book/D-术语表.md` 和 `stm32-book/book/en/D-glossary.md` 里「Stop 之后的时钟」这一行，只把 F103 的「约 14~20 µA」改成与第 16 章相同的 14 µA 和 24 µA，并写上 3.3 V、25°C、无独立看门狗。这一行里的 HSI 8 MHz、L476 的 1.1 µA、1.4 µA、4 µs 不动。其余附录行的 diff 为空。
7. **测试。** 新增 `stm32-book/tests/test_batch6_chapters.py` 和 `stm32-book/tests/test_batch6_sources.py`，照着 Batch5 测试检查四块、共享数字、主图禁词和许可门。视频块里的旧旁白不拿来判失败。不放宽 `test_sample_chapters.py`、`test_batch2_chapters.py`、`test_batch3_chapters.py`、`test_batch4_chapters.py` 和 `test_batch5_chapters.py`。`test_build.py` 里当前版本从 `1.3.0` 改为 `1.3.1`：`assert_version_history_and_index` 的元组在 `1.3.0` 之前加上 `1.3.1`，并断言 `1.3.1` 出现在 `1.3.0` 之前。修订列表以 `1.3.1` 起头。两份整书 HTML 含 `<strong>v1.3.1</strong>`。`test_visual_polish_version_is_1_2_0` 改为核对当前条目是 1.3.1，日期是 2026-10-25。现在对 `entries[0]` 的 1.3.0 四章两句改去核对 `entries[1]`。现在对 `entries[1]` 的 1.2.9 海报两句改去核对 `entries[2]`。现在对 `entries[2]` 的 1.2.8 密度两句改去核对 `entries[3]`。现在对 `entries[3]` 的 1.2.7 浅色两句改去核对 `entries[4]`。现在对 `entries[4]` 的 1.2.6 封面两句改去核对 `entries[5]`。现在对 `entries[5]` 的 1.2.5 令牌两句改去核对 `entries[6]`。现在对 `entries[6]` 的 1.2.4 排版两句改去核对 `entries[7]`。现在对 `entries[7]` 的 1.2.3 两句改去核对 `entries[8]`。现在对 `entries[8]` 的 1.2.2 两句改去核对 `entries[9]`。现在对 `entries[9]` 的 1.2.1 指南两句改去核对 `entries[10]`。现在对 `entries[10]` 的 1.2.0 两句改去核对 `entries[11]`。README 的断言改成当前版本句、`版本号已经是 1.3.1`、`也不要把 1.3.0 的产物标成 1.3.1` 和 `打 tag \`v1.3.1\``。不删 `0x271`、`167 ns`、账本名和出版书签长度为 44 的断言。不改 CSS 哈希一类的视觉契约。不新增读取 `CONTENT_GUIDE.md` 的测试。
8. **CI 变绿之后停下来等人复审。** 复审对象是构建出的中英 HTML 里的这四章。人接受之前不合入，也不开下一批章。Book CI 变绿不等于可以自动 squash 合入。

实施 PR 的 diff 可以碰这四章中英正文、两份 manifest 的新 `sources` 和这四章罗盘、附录 D 里写明的那一格、新图与生成脚本、`assets/README.md`、`CREDITS.md`、版本与修订、新的锁定文件和来源清单、新测试，以及 `test_build.py` 里的版本字符串。不碰其余章的正文，不改 `build_html.py`，不改样式文件，不改 `assets/video/`。

## 验收

### 本设计 PR

- 相对基线 `80c5efb`，只新增 `docs/superpowers/specs/2026-10-25-classic-encyclopedia-batch6-16-17-18-19-design.md`。
- 章节、`stm32-book/`、资产、工具和 `CREDITS.md` 与基线 `80c5efb` 相同。
- 没有新的 SVG 或 GIF，版本号仍是 1.3.0。没有实施计划文件。没有样式 diff，没有海报 diff。

### 实施 PR

- 中文四章各有且仅有一次：`## 原理与边界`、`## 关键插图`、`## 时序或状态`、`## 坑与出处卡`。英文对应四个标题同样各一次。
- 第 16 章和第 17 章都不再有 `## ⚠️ 常见坑与排查` 或 `## ⚠️ Pitfalls and troubleshooting`。第 18 章和第 19 章本来没有这个标题，实施后也不要新出现。
- 每章关键插图的第一张图是对应的静态 SVG。图上能看出正常路径和失败路径。GIF 不是这一节唯一的图。
- 视频块以外，中英都有这些数字，而且彼此一致：
  - 第 16 章：`14`、`24`、`3.4`、`3.2`、`2`、`1.4`、`14.4`、`5.5`、`5.4`、`3.6`、`1.8`、`50`、`8`、`72`、`0x271`、`12800`、`115200`、`1` ms、第 10 脚、`PA0`。四块写明 14 µA 那一格不含独立看门狗，并且 F4 的周期唤醒定时器在 C8 上作废。四块不把 20 µA 或 14~20 µA 写成表 16 的格子。四块不写 780 天。
  - 第 17 章：`0xE000ED28`、`0xE000ED2C`、`0xE000ED34`、`0xE000ED38`、`0xE000EDFC`、`0xE0001004`、bit `30`、`0x40000000`、bit `15`、bit `24`、`72`、`1` µs、`6`。四块写明 bit 15 为 0 时 `BFAR` 无效，并且这颗料是 M3、硬件断点是 6 个。167 ns 不出现在这一章的四块里。
  - 第 18 章：`38`、第 34 脚、`PA13`、第 37 脚、`PA14`、第 7 脚、`0.1`、第 44 脚、`BOOT0`、`0x08000000`、`0x1FFFF000`、`64`、`20`、`12800`、`TIM4`、`0x50`、`5`、`15`。四块写明 6 pF 不是必须值，并且优化等级不是「没有目标」的第一眼。四块不写 90%。
  - 第 19 章：`0x08000000`、`0x08004000`、`0x08004800`、`0x08010000`、`0x0801B800`、`0xB800`、`16`、`2`、`46`、`64`、`110`、`20480`、`65536`、`4096`、`2048`、`1.65`、`133`、`64`。四块写明两张 `0xB800` 不是第 12 章的地图，并且 65536 字节的数组在 C8 上放不下。四块不把 `0x5A5A0001` 写成钥匙。
- 第 16 章引用 8 MHz 和 `0x271` 时不改第 02 章和第 06 章。第 17 章引用四个故障地址时不改附录 D 里除「Stop 之后的时钟」电流句子以外的行，也不改第 01 章的脚位。第 19 章引用 `0xB800` 时不改第 12 章。
- 静态 SVG 小于 60 KB，不含动画标记，含「自绘」，不含「实拍」和「矢量动画」。四条新 GIF 小于 500 KB，并且在 `BUILDERS` 里。已有 20 条 GIF 的像素与基线相同。四张旧辅图的字节与基线相同。`assets/video/` 与基线相同。
- 新 `#source-` 都能在构建出的 HTML 里找到 `id="source-..."`。已有 `rm0008`、`ds5319`、`rm0008-rcc`、`rm0008-usart`、`ds5319-usart`、`ds5319-adc`、`ds5319-gpio`、`ds5319-swd`、`ds5319-rtc`、`rm0008-rtc`、`rm0008-wdg`、`pm0075-rdp`、`pm0056`、`pm0056-nvic`、`rm0008-boot`、`project-examples`、`rm0008-adc`、`rm0008-flash`、`freertos-syscall` 的对象与基线逐字段相同。
- 附录 D 除「Stop 之后的时钟」那一格的 F103 电流句子外，已有各行和附录 A 的正文 diff 为空。`test_build.py` 对 `0x271`、`167 ns` 和出版书签条数的断言仍在。样式文件和 `build_html.py` 的 diff 为空。
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

1. **表 16 的列。** 默认 VDD = 3.3 V、TA = 25°C 的典型值是 24、14、3.4、3.2、2、1.4 µA，顺序就是上面写的六行条件。实施时打开与 `ds5319-clock` 同一份 DS5319 Rev 20 表 16。印出的格子不同就改格子，并在实施 PR 里写明。不沿用「14~20 µA」去否定表 16。
2. **表 26 的单位。** 默认四格都是微秒：1.8、3.6、5.4、50。印出的单位不同就改单位，不把 Standby 写成毫秒。
3. **电源控制的章号。** 默认 RM0008 的电源控制章。印出的标题或章号不同就改 snapshot。退出 Stop 后系统时钟是 HSI、配置要重装，这两句不变。
4. **DEMCR 的位。** 默认 bit 24。印出的不是 24 就改 snapshot。`0xE000EDFC` 和 `0xE0001004` 以印出的地址为准。72 计数等于 1 µs 不变。
5. **NRST 上拉。** 表 39 的典型值只有实施打开了同一份 DS5319 才写进 `ds5319-nrst`。没打开之前，四块只写图 31 的 0.1 µF。
6. **MMARVALID 的位号。** 只有 PM0056 印出了才写入 snapshot。没印出之前，四块只把 bit 15 写死在 `BFAR` 上。
7. **主图体积。** 先拆图。第 16 章的第二张只允许叫 `sample-16-standby.svg`。拆开仍超过 60 KB 时在实施 PR 里说明，不降低画法标准。
8. **版本号。** 实施时升到 1.3.1，不写成 1.3.0.1。日期写 `2026-10-25`。本设计 PR 不升版本。
9. **图目录。** 这一批不加。
10. **下一批章号。** 仍是 4 章，到下一次设计再锁。本文件不预选 `20` 或 `28`。
11. **第 10 脚。** 第 03 章主张外接灯。第 09 章主张 ADC。第 16 章主张 Stop 的按键。第 19 章主张不要把电机方向放在这只脚上。四张图都不把两种功能画成同时有效。

## 英文提要

Thicken only chapter files 16 (low power), 17 (debug), 18 (FAQ), and 19 (the set of projects), in Chinese and English, on top of v1.3.0 (`80c5efb`, PR #56). Chapters 00 through 15 are already thick. The file 19 title stays "项目实战合集" / "A set of real projects". Do not retitle it, and do not retitle this batch as the RTOS survey in file 28. Density pass F already tightened whitespace in 1.2.8; this batch does not touch CSS. The 29 lecture posters stay as they are, including the video-block narration. Use the same four sections as the thick chapters. Each chapter gets one printable static SVG from `gen_sample_figures.py`, with a normal path and a failure path, and no `Svg.footer()`. Chapter 16 draws Stop with the low-power regulator: 14 µA typical at 3.3 V and 25°C, with the independent watchdog off. The regulator-on cell is 24 µA. Wake-up is the 8 MHz HSI. Leaving BRR at `0x271` puts USART1 at 12800 bit/s until the PLL is restored to 72 MHz. The "14 to 20 µA" range and the "8 or 16 MHz" HSI are void on this part. The F4 wake-up timer is void. Chapter 17 draws CFSR at `0xE000ED28`. BFAR is valid only when bit 15 is set. Seventy-two DWT cycles are 1 µs at 72 MHz, after DEMCR bit 24 is set. A stale BFAR, or a cycle delta of 0, is the failure. SWO on pin 39 stays off the normal path. Chapter 18 keeps all 38 FAQ rows and draws the first look at a missing target: pins 34 and 37, BOOT0 on pin 44, and system memory at `0x1FFFF000` when BOOT0 is 1 and BOOT1 is 0. Six picofarads is not a required LSE value. The HAL time base in the repo example is TIM4. Chapter 19 draws one 46 KB application, length `0xB800`, ending at `0x08010000`. A second image of the same length ends at `0x0801B800` and is 110 KB. A 65536-byte buffer does not fit in 20 KB of SRAM. The ADC denominator is 4096, not 4095. One short GIF per chapter is auxiliary only. The existing 20 GIF builders and the four existing auxiliary figures stay as they are. Register five new sources by appending ids. Bump the book to 1.3.1 on 2026-10-25 during implementation, do not tag or release, and stop for human review before squash-merge. This design PR only adds this file.

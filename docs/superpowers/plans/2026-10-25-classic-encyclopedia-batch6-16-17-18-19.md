# Batch 6 Chapters 16, 17, 18, and 19 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

I'm using the writing-plans skill to create the implementation plan.

**Goal:** 只加厚第 16、17、18、19 章（中文和英文一起），写成和第 00 到第 15 章相同的四块密度，每章一张可印刷的静态主图加一条短 GIF 辅图，把 Stop 的「约 14~20 µA」、醒来的「约 8/16 MHz」、`BFAR` 的旧地址、FAQ 里的 6 pF 与笼统 TIMx、以及两张 `0xB800` 改成和已冻结手册以及罗盘、附录 D、前面各章同一笔账，合入时把整书升到 1.3.1 · 2026-10-25，然后停下来等人复审。人接受之前不合入。

**Architecture:** 章号已经由设计锁死，不再打分重选，也不拆成四份计划。四章共用一次版本号、一次来源追加和一次人审。先只读这四章的中英八份，确认四块还不存在。第 16 章和第 17 章的旧坑标题还在。第 18 章和第 19 章没有旧坑标题，不要为了删它而先造一个空标题。来源清单在 Task 2 按本计划里的 JSON 落盘，不在本计划提交里预先写入。然后生成静态 SVG 和短 GIF，再改八份正文。新出处只追加进 `stm32-book/manifest.json` 与 `stm32-book/manifest-en.json` 的 `sources`。附录 E 的卡片仍由 `stm32-book/build_html.py` 的 `source_registry_html()` 生成。主图走 `tools/svgkit.py` 的 `tools/gen_sample_figures.py`。短 GIF 走 `tools/gen_gifs.py` 的 `BUILDERS`。版本号同时写进两份 manifest、`stm32-book/revisions.json` 和 `stm32-book/README.md`。日期写死 `2026-10-25`，不取实施当天的日期。代理日历若显示 2026-10-26，书的日期仍写 2026-10-25。

**Tech Stack:** Python 3 标准库、现有 `stm32-book/build_html.py`、`python3 -m unittest`、`tools/svgkit.py`、`tools/gen_gifs.py`、`tools/minigfx.py`、`tools/check_assets.py`。不新增依赖，不改 `requirements.txt`。

单文件测试写成 `python3 stm32-book/tests/<file>.py -v`。`stm32-book/tests/` 不是 Python 包。整套测试仍用 `python3 -m unittest discover stm32-book/tests -v`。

本计划不拆成四个子计划。设计规格把这四章锁成同一批，版本只升一次到 1.3.1。拆开会把一次人审拆成四次，或者让 1.3.1 先带着不完整的四章合入。

本文件是实施计划。它不改章节正文，不画 SVG，不生成 GIF，不改 `stm32-book/` 的版本号。那些步骤留在后续实施 PR。

Book CI 的 `actions/checkout` 没有写 `fetch-depth`，默认深度是 1。回归测试若用 `git show <锁定文件里的 baseline SHA>:<路径>` 去比对视频块或附录 D，浅克隆里没有那个提交，`git show` 会失败。凡是这种比对，都要先按 Batch5 已经落在 `stm32-book/tests/test_batch5_chapters.py` 里的 `_fetch_baseline()` 把那个 SHA 取回来：先 `git fetch --depth=1 origin <rev>`，仍没有再 `git fetch --depth=50 origin +refs/heads/$GITHUB_BASE_REF:refs/remotes/origin/$GITHUB_BASE_REF`（`GITHUB_BASE_REF` 缺省时用 `main`）。不要把工作流的 checkout 改成全历史，也不要假设 SHA 已经在本地。Task 5 把这组函数放进 `test_batch6_chapters.py`。后面的任务调用 `baseline_chapter()`，不要再写裸的 `git show`。

## Global Constraints

- 只把第 16、17、18、19 章加厚到和第 00 到第 15 章相同的四块密度。中文和英文一起写完。文件名仍是 `docs/16-低功耗设计.md`、`docs/en/16-low-power.md`、`docs/17-调试与性能优化.md`、`docs/en/17-debug.md`、`docs/18-常见问题FAQ.md`、`docs/en/18-faq.md`、`docs/19-项目实战合集.md`、`docs/en/19-projects.md`。一级标题继续是 `19 项目实战合集`，英文继续是 `19 A set of real projects`。不要改成「项目实战上册」，也不要写成第 28 章的 RTOS 生态。
- 四块标题必须原样出现，各一次：中文 `## 原理与边界`、`## 关键插图`、`## 时序或状态`、`## 坑与出处卡`；英文 `## Principle and boundary`、`## Key figures`、`## Timing or state`、`## Pitfalls and source cards`。标题不加表情符号。四块插在 `<!-- /video: -->` 之后、该章现有的学习目标标题之前。
- 保留学习目标、硬件与接线、代码实现、动手实验、相关资源，以及英文文件里已经在用的对应标题。不要把英文标题改成另一章的措辞。在 `2e2b1d0d4f2c2fb9aabbadb2b89931ac216bdc53` 上，中文四章的学习目标都是 `## 📌 学习目标`。英文四章的学习目标都是 `## 📌 Learning goals`。中文第 16、17 章的核心原理是 `## 🧠 核心原理`，英文是 `## 🧠 Core ideas`。第 18 章和第 19 章没有 `## 🧠 核心原理`，也没有 `## 🧠 Core ideas`，没有 `## 🛠️ 硬件与接线`，也没有 `## 💻 代码实现`。不要为了设计规格里那句「保留核心原理」而新造这些标题。第 18 章保留 38 条目录和现有的 `## 一、编译与链接` 到 `## 五、RTOS 与工具链`，以及英文的 `## 1. Build and link` 到 `## 5. RTOS and the toolchain`。第 19 章保留 10 个项目和现有的 `## 1.` 到 `## 10.` 标题。
- 旧坑标题只在第 16 章和第 17 章删除，不留空标题。中文是 `## ⚠️ 常见坑与排查`。英文是 `## ⚠️ Pitfalls and troubleshooting`。第 18 章和第 19 章在 `2e2b1d0d4f2c2fb9aabbadb2b89931ac216bdc53` 上没有这个标题。不要先造一个再删。实施后这两章也不要新出现这个标题。
- 每章一张可印刷的静态主图：正常路径和失败路径都在图上。生成脚本是 `tools/gen_sample_figures.py`，画布是 `tools/svgkit.py`。不调用 `Svg.footer()`。落款用已有的 `_credit()`：左侧是文档号，右侧是「自绘 · 静态 · CC BY 4.0」。没有 `<animate`、`@keyframes`、`animation:`。图注写「自绘」，英文图注写 `Drawn for this book`。替代文本写结论。单张小于 60 KB。放不下就拆成主图加局部，每张仍争取小于 60 KB。第 16 章的第二张只允许叫 `assets/diagrams/sample-16-standby.svg`。第 17、18、19 章不另起第二张文件名。拆开仍超过时，在实施 PR 里写出字节数和原因，不把图画回简笔，也不把 60 KB 改成仓库新默认值。
- 另加一条短 GIF，只做网页和公众号辅图。GIF 不替换主图，也不是关键插图这一节唯一的图。四条都走 `tools/gen_gifs.py`，加入 `BUILDERS`。`minigfx.py` 只有 5×7 英文点阵，GIF 上的字用 ASCII。每条少于 500 KB。帧数不少于 3、不多于 12。`gen_gifs.chrome()` 自带的页脚可以留在 GIF 里。那条页脚不是静态主图的 `Svg.footer()`。
- 改写吸收的许可顺序：先用 ST 公开 RM/DS/PM 的事实、用自己的话重写；然后才是 MIT、BSD-2-Clause、BSD-3-Clause、ISC、CC BY 4.0、CC BY 3.0、CC0。GPL、LGPL、CC BY-NC、CC BY-ND、Apache-2.0、保留所有权利、未写许可的材料只留链接。不把厂商手册、灯珠手册、CAN 收发器厂商手册或社区原文放进仓库。WS2812 的 0.4 µs、0.8 µs、1.25 µs 留在项目 6 的正文，标明那是灯珠厂商的时序，不进出处卡，不新开 id。TJA1050 的 5 V 和 SN65HVD230 的 3.3 V 留在硬件清单，不进出处卡。
- 订货号是 STM32F103C8T6，LQFP48。读者看到的章号仍是文件名前缀加 1。源文件的一级标题继续带 `16`、`17`、`18`、`19`。这一批不改这个加 1。文件 `16` 在书里是第 17 章，`17` 是第 18 章，`18` 是第 19 章，`19` 是第 20 章。
- 第 16 章：Stop，稳压器在低功耗模式，对应 `PWR_LOWPOWERREGULATOR_ON`。DS5319 Rev 20 表 16，TA = 25°C，VDD = 3.3 V 的典型值：低功耗稳压器、振荡器关、无独立看门狗，14 µA；主稳压器仍开、其余条件相同，24 µA。Standby：LSI 与 IWDG 都开，3.4 µA；LSI 开、IWDG 关，3.2 µA；LSI、IWDG、LSE、RTC 都关，2 µA。备份域、LSE 与 RTC 开，1.4 µA，那是 `IDD_VBAT`，不是整机 Standby。85°C 最大值 200 µA 和 180 µA 不是典型值。20 µA 不是表 16 的格子。「约 14~20 µA」和「约 2~3 µA」作废。表 18：72 MHz、外设全开的 Sleep 典型 14.4 mA，外设全关 5.5 mA。「10~20 mA」不覆盖 5.5 mA。表 26：Sleep 1.8 µs，沿用睡前的时钟；Stop 主稳压器 3.6 µs；Stop 低功耗稳压器 5.4 µs；Standby 50 µs。Stop 和 Standby 的这段时间在 8 MHz HSI 上量到第一条用户指令。PLL 的 `tLOCK` 最大值 200 µs，不和 5.4 µs 加在一起叫成唤醒时间。醒来是 HSI 8 MHz，不是 16 MHz。「8/16 MHz」作废。`0x271` 在 8 MHz 下是 `8e6 / (16 × 39.0625) = 12800`。先把 PLL 装回 72 MHz，线上才回到 115200。Sleep 里 `examples/freertos-task` 的节拍是 1000 Hz，也就是 1 ms，不是每秒一次。Stop 期间 SysTick 不跳。F4 的 `HAL_RTCEx_SetWakeUpTimer_IT` 在这颗料上作废。定时叫醒走第 11 章，PRL = 32767。第 10 脚 PA0 的 Stop 按键、第 03 章的灯和第 09 章的 ADC 不同时有效。14 µA 那一格不含 IWDG。表 16 没有单独印出「Stop 加 IWDG」的微安，四块不编一个新的微安。780 天和 0.33 mA 留在核心原理，不进四块，不进出处卡。20 µA 不得写成 Stop 的典型值。
- 第 17 章：`CFSR` 在 `0xE000ED28`，`HFSR` 在 `0xE000ED2C`，`MMFAR` 在 `0xE000ED34`，`BFAR` 在 `0xE000ED38`。`HFSR.FORCED` 是 bit 30，值 `0x40000000`。`BFARVALID` 是 `CFSR` bit 15。这一位为 0 时，`BFAR` 不是这次的地址。先置 `DEMCR` `0xE000EDFC` 的 bit 24，再读 `DWT_CYCCNT` `0xE0001004`。72 MHz 下 72 个计数是 1 µs。没置 bit 24 时差值为 0。这颗 M3 的硬件断点是 6 个。M7 的 8 个在 C8 上作废。数据观察点的「2~4 个」不进四块。「速度可达 10+ MHz」不进四块。167 ns 不进四块。第 34 脚 PA13、第 37 脚 PA14 是 SWD。第 39 脚 PB3 复位后是 JTDO，不进主图的正常路径。没有 FPU。`-mfpu=fpv4-sp-d16` 留在核心原理，不进四块的正常路径。核心原理里已有的 `CoreDebug_DEMCR_TRCENA_Msk` 就是 bit 24，不要删掉。
- 第 18 章：C1–C8、D1–D7、P1–P9、H1–H7、R1–R7，`8 + 7 + 9 + 7 + 7 = 38`。这个数保留。认不出芯片时先看第 34 脚 PA13、第 37 脚 PA14、共地、3.3 V、第 7 脚 NRST。图 31 的外部复位电容是 0.1 µF。先改 `-O2` 是失败路径。第 44 脚 BOOT0 = 0 从 `0x08000000` 启动。BOOT1 = 0 且 BOOT0 = 1 进 `0x1FFFF000`。互联型 `0x1FFFB000` 在 C8 上作废。第 35 脚是 VSS_2，不是 SWCLK。闪存 64 KB，SRAM 20 KB。HSE 没起来时 `0x271` 是 12800。P9 删掉「必须 6 pF」。电容是 5 pF 到 15 pF，按晶振选。时基是 TIM4，不是 TIMx。`5 << 4 = 0x50`。外接灯是第 10 脚和 270 Ω。「220~1 kΩ」不进四块。排错五步可以留下。「90%」不是测量，从方法节删掉这个百分比，四块也不写。
- 第 19 章：一张 APP。Bootloader `0x08000000` 起 16 KB，参数区 `0x08004000` 起 2 KB，APP `0x08004800` 起 46 KB，长度 `0xB800`，到 `0x08010000` 之前。`16 + 2 + 46 = 64`。两张 `0xB800` 是 `16 + 2 + 46 + 46 = 110` KB，结束于 `0x0801B800`。第 12 章没有第二张槽。`0x5A5A0001` 留在项目草稿里，不进出处卡。`64 * 1024 = 65536` 大于 SRAM 20480 字节，这只数组在 C8 上作废。不编 F411 或 F407 的 SRAM 容量。分母改成 4096。码 2048 在名义 3.3 V 下是 1.65 V。应用帧 `4 + 128 + 1 = 133` 字节，不是全速批量的 64 字节包上限。两端 120 Ω、PB8/PB9、500 kbit/s 跟第 13 章同一笔。方向脚不要放在第 10 脚 PA0。四块不新指定一只替代脚。工时和星级不进四块。灯珠的微秒不进四块。
- 实施合入时把整书从 1.3.0 升到 **1.3.1**。中英文整书共用这个版本号。日期写死 **2026-10-25**。`accessed` 也写死 `2026-10-25`。不写成 1.3.0.1。不打 tag，不创建 GitHub Release。本计划提交不升版本。
- Book CI 变绿之后停下来等人复审。复审对象是构建出的中英 HTML 里的这四章。人接受之前不合入，也不开下一批章。CI 变绿不等于可以自动 squash 合入。
- 实施基线是 #57 合入之后的 `main` 尖端。写本计划时该尖端是 `2e2b1d0d4f2c2fb9aabbadb2b89931ac216bdc53`（`docs: 第 16、17、18、19 章加厚设计（低功耗、调试、FAQ、项目） (#57)`）。其章节正文与 v1.3.0 `80c5efb7cd0134d9450dfab99330c619ffaee295` 相同，只多了设计规格。
- 不加厚除 16、17、18、19 以外的任何章，含 00–15 和 20–28。不重选样本。不改 `docs/superpowers/plans/` 里已有的锁定文件和来源清单。不改 `tools/scan_sample_chapters.py`、`tools/scan_batch2_chapters.py`、`tools/scan_batch3_chapters.py`、`tools/scan_batch4_chapters.py`、`tools/scan_batch5_chapters.py`。不改总纲、Batch2、Batch3、Batch4、Batch5 规格、观感规格、海报规格、密度规格、CONTENT_GUIDE 规格，也不改两份 `CONTENT_GUIDE.md`。不改本批设计规格 `docs/superpowers/specs/2026-10-25-classic-encyclopedia-batch6-16-17-18-19-design.md`。
- 不改 `stm32-book/build_html.py`。出版书签仍是现在的 44 条。不把新的二级标题收进书签。不改密度刀 F 的令牌、`stm32-book/styles/book.css`、`stm32-book/styles/tokens.json` 和间距。不把样式、字号、行长或页边再收一刀。
- 附录 D 只改「Stop 之后的时钟」这一行里 F103 的电流句子。中文文件是 `stm32-book/book/D-术语表.md`，英文文件是 `stm32-book/book/en/D-glossary.md`。这一行里的 HSI 8 MHz、L476 的 1.1 µA、1.4 µA、4 µs 不动。其余附录行的 diff 为空。不改附录 A。不手改 `stm32-book/book/E-参考资料.md` 或英文对应文件。不删 `test_build.py` 里 `0x271`、`167 ns`、账本名和出版书签长度为 44 的断言。不放宽 `test_sample_chapters.py`、`test_batch2_chapters.py`、`test_batch3_chapters.py`、`test_batch4_chapters.py` 或 `test_batch5_chapters.py`。不新增读取 `CONTENT_GUIDE.md` 的测试。不改 CSS 哈希一类的视觉契约。
- 不删除、不重画已有图。第 16 章留下 `lowpower-wakeup.svg`。第 17 章留下 `debug-swo.svg`。第 18 章留下 `toolchain-flow.svg`。第 19 章留下 `peripheral-wiring.svg`。不重画 `sample-00` 到 `sample-15` 的任何一张，含 `sample-01-swd-vectors.svg`、`sample-02-clock-tree.svg`、`sample-03-gpio-led.svg`、`sample-04-exception-stack.svg`、`sample-06-uart-frame.svg`、`sample-09-adc-sar.svg`、`sample-11-iwdg-1s.svg`、`sample-12-iap-map.svg`、`sample-13-can-bit.svg`、`sample-14-usb-enum.svg`、`sample-15-rtos-prio.svg`。不改已有 20 个 BUILDERS 的像素：`led-blink`、`pwm-breath`、`uart-bits`、`i2c-timing`、`dma-ring`、`sar-adc`、`nvic-preempt`、`uart-idle`、`clock-css`、`pwm-1khz`、`spi-jedec`、`adc-sample`、`swd-fetch`、`i2c-addr`、`dma-cndtr`、`iwdg-1s`、`iap-jump`、`can-500k`、`usb-48m`、`rtos-tick`。不把 `tools/svg2gif.py` 当成必经步骤。不改 `assets/video/`，不改 `tools/gen_narrated.py`。`<!-- video: -->` 与 `<!-- /video: -->` 之间的旁白保持原样。旁白不重录。不重画 29 张讲解海报。
- 新来源 id 只追加，顺序固定为 `ds5319-pwr`、`rm0008-pwr`、`pm0056-dwt`、`ds5319-nrst`、`ds5319-lse`。没有第六个 id。表 39 的上拉若要进正文，写进已有的新 id `ds5319-nrst`，不为此再开一个 id。已有 id 的对象一个字段都不改。中英两份 manifest 的 `url`、`snapshot`、`license`、`accessed` 用同一串字符；`title`、`authority`、`scope` 用对应语言。
- 代码继续按 `docs/CONTENT_GUIDE.md`：HAL，参数用宏。不新开可烧录工程。不改 `examples/`。例程里的时基、APP 长度和过滤器位移留在例程。
- 不加图目录或表目录，不加第 30 章，不改 `docs/00`–`28` 的文件名。不预选文件 `20` 或 `28` 作为下一批。
- 表 16 默认 3.3 V、25°C 的典型值是 24、14、3.4、3.2、2、1.4 µA，顺序就是上面六行条件。表 26 默认 1.8、3.6、5.4、50 µs。电源控制默认 RM0008 的电源控制章。DEMCR 默认 bit 24。NRST 上拉在没打开表 39 之前不写千欧。MMARVALID 的位号在没印出之前不写死。印出的格子、单位、章号或位号不同就改 snapshot，并在实施 PR 里写明。不沿用「14~20 µA」去否定表 16。500 kbit/s、48 MHz、`0xB800`、4096 和例程里的 TIM4 不变。
- 同一只第 10 脚：第 03 章主张外接灯。第 09 章主张 ADC。第 16 章主张 Stop 的按键。第 19 章主张不要把电机方向放在这只脚上。四张图都不把两种功能画成同时有效。不重画第 02 章的时钟树，不重画第 06 章的帧，不重画第 12 章的页高，不重画第 01 章的两脚图。

## File map

| 路径 | 责任 |
| --- | --- |
| `tools/scan_batch6_chapters.py` | 只读 16、17、18、19 的中英八份。四块必须缺失。第 16、17 章旧坑标题必须还在。第 18、19 章旧坑标题必须不在 |
| `docs/superpowers/plans/2026-10-25-batch6-16-17-18-19-lock.json` | Task 1 运行时写出。`baseline` 等于当时的 `git rev-parse HEAD`。本计划提交不包含这份文件 |
| `docs/superpowers/plans/2026-10-25-batch6-16-17-18-19-source-list.json` | Task 2 按下面的 JSON 落盘。五个 absorb id，社区列表为空。登记以 manifest 为准 |
| `tools/gen_sample_figures.py` | 在现有十六张静态主图之外追加四张。不改已有十六个函数，不改 `_credit` |
| `assets/diagrams/sample-16-stop-wake.svg` | 第 16 章主图 |
| `assets/diagrams/sample-17-cfsr.svg` | 第 17 章主图 |
| `assets/diagrams/sample-18-boot-triage.svg` | 第 18 章主图 |
| `assets/diagrams/sample-19-flash-fit.svg` | 第 19 章主图 |
| `assets/diagrams/sample-16-standby.svg` | 只有第 16 章主图达到或超过 60 KB 时才允许出现 |
| `tools/gen_gifs.py` | `BUILDERS` 末尾追加 `stop-wake`、`cfsr-read`、`boot0-low`、`one-slot`。不改已有二十个函数 |
| `assets/gif/stop-wake.gif` | 第 16 章辅图。只画 8 MHz 装回 72 MHz 和 115200 |
| `assets/gif/cfsr-read.gif` | 第 17 章辅图。只画 bit 15 为 1 和 72 个计数的 1 µs |
| `assets/gif/boot0-low.gif` | 第 18 章辅图。只画第 44 脚为 0，探针在第 34 脚和第 37 脚 |
| `assets/gif/one-slot.gif` | 第 19 章辅图。只画 16 KB、2 KB 和一张 `0xB800` |
| `assets/README.md` | 登记四张 SVG 和四条 GIF，并把四张旧动画标成辅图。第五节「上面 20 张」改为「上面 24 张」 |
| 八份章节 Markdown | 四块，以及和罗盘、附录 D、手册冲突的那几格。视频块字节不变 |
| `stm32-book/manifest.json` 与 `stm32-book/manifest-en.json` | 五个新 `sources`、四章罗盘、版本号 |
| `stm32-book/book/D-术语表.md` 与 `stm32-book/book/en/D-glossary.md` | 只改「Stop 之后的时钟」那一格的 F103 电流句子 |
| `stm32-book/revisions.json` | 1.3.1 修订条目，插在数组最前 |
| `stm32-book/README.md` | 当前版本句，以及「也不要把 1.3.0 的产物标成 1.3.1」 |
| `CREDITS.md` | 第六节下面增加 v1.3.1 小节。静态框图张数改为 26。若拆出第二张第 16 章 SVG，改为 27。光栅动画个数改为 24 |
| `stm32-book/tests/test_batch6_sources.py` | 来源清单的许可门 |
| `stm32-book/tests/test_batch6_chapters.py` | 四块、共享数字、主图、GIF、视频块字节、附录 D 那一格。视频块和附录 D 的基线比对必须先 fetch |
| `stm32-book/tests/test_build.py` | 只改当前版本断言。`0x271` 和书签条数保留 |

---

### Task 1: Gap scan and lock

**Files:**
- Create: `tools/scan_batch6_chapters.py`
- Create: `docs/superpowers/plans/2026-10-25-batch6-16-17-18-19-lock.json`（脚本在退出码 0 时写出。本计划提交里还没有它）

**Interfaces:**
- Consumes: 八份原稿。不读别的章，不调用 `tools/scan_sample_chapters.py`，不调用 `tools/scan_batch2_chapters.py`，不调用 `tools/scan_batch3_chapters.py`，不调用 `tools/scan_batch4_chapters.py`，不调用 `tools/scan_batch5_chapters.py`。
- Produces: 锁定文件字段 `rubric`（字符串 `"2026-10-25-classic-encyclopedia-batch6-16-17-18-19"`）、`baseline`（40 位十六进制，等于运行时 `git rev-parse HEAD`）、`chapters`（`["16", "17", "18", "19"]`）、`four_blocks_absent`（`true`）、`old_pitfall_heading_present`（`true`，只表示第 16 章和第 17 章的旧标题还在）、`chapters_without_old_pitfall`（`["18", "19"]`）、`files`。`files` 的键是 `"16"`、`"17"`、`"18"`、`"19"`。每个值有 `zh`、`en`、`zh_four_blocks`、`en_four_blocks`、`expects_old_pitfall`、`zh_old_pitfall`、`en_old_pitfall`、`en_old_heading`。后面的任务只改这四个前缀。

四块标题是中文 `## 原理与边界`、`## 关键插图`、`## 时序或状态`、`## 坑与出处卡`，英文 `## Principle and boundary`、`## Key figures`、`## Timing or state`、`## Pitfalls and source cards`。

旧坑标题按文件区分。第 18 章和第 19 章的 `expects_old_pitfall` 是 `false`。脚本去找的那一行英文标题仍然记在 `en_old_heading` 里，用来证明它不在文件中，不是要把它写进去。

| 前缀 | 中文旧标题 | 英文旧标题 | 必须还在 |
| --- | --- | --- | --- |
| `16` | `## ⚠️ 常见坑与排查` | `## ⚠️ Pitfalls and troubleshooting` | 是 |
| `17` | `## ⚠️ 常见坑与排查` | `## ⚠️ Pitfalls and troubleshooting` | 是 |
| `18` | `## ⚠️ 常见坑与排查` | `## ⚠️ Pitfalls and troubleshooting` | 否 |
| `19` | `## ⚠️ 常见坑与排查` | `## ⚠️ Pitfalls and troubleshooting` | 否 |

在 `2e2b1d0d4f2c2fb9aabbadb2b89931ac216bdc53` 上，这八份都还没有四块。第 16、17 章的旧坑标题都还在。第 18、19 章没有旧坑标题。若执行时任何一份已经有四块，或者第 16、17 章的旧标题已经不在，或者第 18、19 章出现了旧标题，脚本退出码 2，不改写锁定文件，后面的任务停。不要在已有四块上再叠一套标题。不要给第 18、19 章补一个空的旧坑标题。

- [ ] **Step 1: 写入核对脚本**

把下面的程序保存为 `tools/scan_batch6_chapters.py`。

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Confirm chapters 16, 17, 18, and 19 are still missing the four blocks.

Run from the repository root:

    python3 tools/scan_batch6_chapters.py

Rewrites docs/superpowers/plans/2026-10-25-batch6-16-17-18-19-lock.json and
exits 0 when all eight manuscripts lack the four headings. Chapters 16 and 17
must still have the old pitfall heading. Chapters 18 and 19 must not have it.
Exits 2 without writing the lock otherwise. Does not score other chapters and
does not touch earlier locks.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch6-16-17-18-19-lock.json"
FILES = {
    "16": (
        ROOT / "docs" / "16-低功耗设计.md",
        ROOT / "docs" / "en" / "16-low-power.md",
        "## ⚠️ Pitfalls and troubleshooting",
        True,
    ),
    "17": (
        ROOT / "docs" / "17-调试与性能优化.md",
        ROOT / "docs" / "en" / "17-debug.md",
        "## ⚠️ Pitfalls and troubleshooting",
        True,
    ),
    "18": (
        ROOT / "docs" / "18-常见问题FAQ.md",
        ROOT / "docs" / "en" / "18-faq.md",
        "## ⚠️ Pitfalls and troubleshooting",
        False,
    ),
    "19": (
        ROOT / "docs" / "19-项目实战合集.md",
        ROOT / "docs" / "en" / "19-projects.md",
        "## ⚠️ Pitfalls and troubleshooting",
        False,
    ),
}
ZH_BLOCKS = ("## 原理与边界", "## 关键插图", "## 时序或状态", "## 坑与出处卡")
EN_BLOCKS = (
    "## Principle and boundary",
    "## Key figures",
    "## Timing or state",
    "## Pitfalls and source cards",
)
ZH_OLD = "## ⚠️ 常见坑与排查"


def four_blocks(text: str, headings: tuple[str, ...]) -> bool:
    return any(heading in text for heading in headings)


def main() -> int:
    payload_files: dict[str, dict] = {}
    blocked = False
    for prefix, (zh_path, en_path, en_old, expects_old) in FILES.items():
        if not zh_path.is_file() or not en_path.is_file():
            print(f"missing manuscript for {prefix}", file=sys.stderr)
            return 2
        zh = zh_path.read_text(encoding="utf-8")
        en = en_path.read_text(encoding="utf-8")
        row = {
            "zh": zh_path.relative_to(ROOT).as_posix(),
            "en": en_path.relative_to(ROOT).as_posix(),
            "zh_four_blocks": four_blocks(zh, ZH_BLOCKS),
            "en_four_blocks": four_blocks(en, EN_BLOCKS),
            "expects_old_pitfall": expects_old,
            "zh_old_pitfall": ZH_OLD in zh,
            "en_old_pitfall": en_old in en,
            "en_old_heading": en_old,
        }
        payload_files[prefix] = row
        if row["zh_four_blocks"] or row["en_four_blocks"]:
            print(f"{prefix} already has a four-block heading; stop", file=sys.stderr)
            blocked = True
        if expects_old and (not row["zh_old_pitfall"] or not row["en_old_pitfall"]):
            print(f"{prefix} is missing the old pitfall heading; stop", file=sys.stderr)
            blocked = True
        if (not expects_old) and (row["zh_old_pitfall"] or row["en_old_pitfall"]):
            print(f"{prefix} already has an old pitfall heading; do not invent one to delete", file=sys.stderr)
            blocked = True
        old = "yes" if row["zh_old_pitfall"] and row["en_old_pitfall"] else "no"
        print(
            f"{prefix} four_blocks={'yes' if row['zh_four_blocks'] or row['en_four_blocks'] else 'no'} "
            f"old_pitfall={old}"
        )
    if blocked:
        return 2
    baseline = subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True
    ).strip()
    payload = {
        "rubric": "2026-10-25-classic-encyclopedia-batch6-16-17-18-19",
        "baseline": baseline,
        "chapters": ["16", "17", "18", "19"],
        "four_blocks_absent": True,
        "old_pitfall_heading_present": True,
        "chapters_without_old_pitfall": ["18", "19"],
        "files": payload_files,
    }
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOCK_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"baseline={baseline}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: 在改任何章节之前运行核对**

Run: `python3 tools/scan_batch6_chapters.py`

Expected: 退出码 0，标准输出含

```text
16 four_blocks=no old_pitfall=yes
17 four_blocks=no old_pitfall=yes
18 four_blocks=no old_pitfall=no
19 four_blocks=no old_pitfall=no
baseline=
```

`baseline=` 后面是当时 `git rev-parse HEAD` 的 40 位哈希。锁定文件里 `chapters` 仍为 `["16", "17", "18", "19"]`，`four_blocks_absent` 仍为 `true`，`old_pitfall_heading_present` 仍为 `true`，`chapters_without_old_pitfall` 仍为 `["18", "19"]`。`files["16"]["expects_old_pitfall"]` 和 `files["17"]["expects_old_pitfall"]` 是 `true`。`files["18"]["expects_old_pitfall"]` 和 `files["19"]["expects_old_pitfall"]` 是 `false`。`files["18"]["zh_old_pitfall"]` 和 `files["18"]["en_old_pitfall"]` 是 `false`。第 19 章同样是 `false`。四份的 `en_old_heading` 都是 `## ⚠️ Pitfalls and troubleshooting`。这个 HEAD 必须还没有新的 `sources`，也还没有四块。

若退出码为 2：停止。不要改四块标题去凑退出码 0，也不要给第 18、19 章补旧坑标题。

- [ ] **Step 3: 确认更早的锁定、扫描脚本和设计规格没被改写**

Run:

```bash
git diff --name-only -- tools/scan_sample_chapters.py tools/scan_batch2_chapters.py tools/scan_batch3_chapters.py tools/scan_batch4_chapters.py tools/scan_batch5_chapters.py docs/superpowers/plans/2026-10-25-sample-chapters-lock.json docs/superpowers/plans/2026-10-25-batch2-04-06-lock.json docs/superpowers/plans/2026-10-25-batch3-02-05-08-09-lock.json docs/superpowers/plans/2026-10-25-batch4-01-07-10-11-lock.json docs/superpowers/plans/2026-10-25-batch5-12-13-14-15-lock.json docs/superpowers/specs/2026-10-25-classic-encyclopedia-batch6-16-17-18-19-design.md
```

Expected: 无输出。若上面某个锁定文件的路径和仓库里的实际文件名不一致，以仓库里已有的那份为准，仍然要求 diff 为空。不要新建一份去覆盖它。

- [ ] **Step 4: Commit**

```bash
git add tools/scan_batch6_chapters.py docs/superpowers/plans/2026-10-25-batch6-16-17-18-19-lock.json
git commit -m "docs: 锁定第 16、17、18、19 章尚未加厚"
```

这一笔提交里不要带 manifest 或章节正文。锁定文件里的 `baseline` 必须仍指向还没有新 `sources` 的那次提交。

### Task 2: Source list with the license gate

**Files:**
- Create: `docs/superpowers/plans/2026-10-25-batch6-16-17-18-19-source-list.json`
- Create: `stm32-book/tests/test_batch6_sources.py`
- Test: `stm32-book/tests/test_batch6_sources.py`

**Interfaces:**
- Consumes: Task 1 的 `chapters == ["16", "17", "18", "19"]`，以及 `four_blocks_absent == true`。
- Produces: 五个新 id，顺序固定为 `ds5319-pwr`、`rm0008-pwr`、`pm0056-dwt`、`ds5319-nrst`、`ds5319-lse`。不产生第六个 id。`community` 是空数组。`reuse_existing` 的 id 顺序是 `rm0008-rcc`、`rm0008-usart`、`ds5319-usart`、`ds5319-adc`、`ds5319-gpio`、`ds5319-swd`、`ds5319-rtc`、`rm0008-rtc`、`rm0008-wdg`、`pm0075-rdp`、`pm0056`、`rm0008-boot`、`project-examples`、`rm0008-adc`、`rm0008-flash`、`freertos-syscall`。这十六个 id 不新建 manifest 对象。`pm0056-nvic` 也不新建，也不改字段。

2026-10-25 设计规格冻结的事实，实施时打开同一批 URL。首页修订或格子变了就停，先改清单里的 `snapshot` 和 `section`，再画图、再写正文。数字本身不变：

- DS5319 Rev 20（July 2025）。PDF 与已有 `ds5319-clock` 相同。
- RM0008 Rev 21（February 2021）。PDF 与已有 `rm0008-rcc` 相同。
- PM0056。PDF 与已有 `pm0056-nvic` 相同：`https://www.st.com/resource/en/programming_manual/pm0056-stm32f10xxx-cortex-m3-programming-manual-stmicroelectronics.pdf`。不改已有 `pm0056` 对象那条较短的 `url`。

打开这些 URL：

- `https://www.st.com/resource/en/datasheet/stm32f103c8.pdf`
- `https://www.st.com/resource/en/reference_manual/rm0008-stm32f101xx-stm32f102xx-stm32f103xx-advanced-arm-based-32-bit-mcus-stmicroelectronics.pdf`
- `https://www.st.com/resource/en/programming_manual/pm0056-stm32f10xxx-cortex-m3-programming-manual-stmicroelectronics.pdf`

三份里有打不开的就停。不要换一份别的手册来补微安、微秒、位号或皮法。

社区例程这一批不冻结。来源清单的 `community` 是空数组。例程主张走已有的 `project-examples`，不新开例程 id。不吸收未写许可的博客，不吸收灯珠厂商手册，不吸收收发器厂商手册。

- [ ] **Step 1: 写入来源清单**

把下面的 JSON 保存为 `docs/superpowers/plans/2026-10-25-batch6-16-17-18-19-source-list.json`。实施时不要另写一份。许可门测试去读这份文件。

```json
{
  "chapters": ["16", "17", "18", "19"],
  "community": [],
  "reuse_existing": [
    {
      "id": "rm0008-rcc",
      "claim": "Power-up HSI and the HSI after an HSE failure are 8 MHz. PCLK2 is not divided on this book's clock tree.",
      "do_not_copy": "Do not edit the existing rm0008-rcc object. Do not redraw sample-02-clock-tree.svg. Do not call the HSI 16 MHz."
    },
    {
      "id": "rm0008-usart",
      "claim": "BRR 0x271 is a divider of 39.0625. At 8 MHz that is 12800 bit/s. At 72 MHz it is 115200.",
      "do_not_copy": "Do not edit the existing rm0008-usart object. Do not redraw sample-06-uart-frame.svg."
    },
    {
      "id": "ds5319-usart",
      "claim": "USART1 stays on pin 30 PA9 and pin 31 PA10. Chapter 16 only points at those pins.",
      "do_not_copy": "Do not edit the existing ds5319-usart object. Do not redraw the UART frame."
    },
    {
      "id": "ds5319-adc",
      "claim": "Pin 10 is PA0-WKUP and also ADC12_IN0. Chapter 16 draws a key. Chapter 19 says the motor direction pin must not be this pin.",
      "do_not_copy": "Do not edit the existing ds5319-adc object. Do not redraw sample-09-adc-sar.svg. Do not assign a new motor pin."
    },
    {
      "id": "ds5319-gpio",
      "claim": "Pin 2 PC13 cannot source current. The external lamp's 270 ohm resistor is already in chapter 03.",
      "do_not_copy": "Do not edit the existing ds5319-gpio object. Do not redraw sample-03-gpio-led.svg. Do not put 220 ohm to 1 kilohm in the four sections."
    },
    {
      "id": "ds5319-swd",
      "claim": "Pin 34 is PA13, pin 37 is PA14, pin 7 is NRST, pin 39 is PB3, and pin 44 is BOOT0. Flash is 64 KB. SRAM is 20 KB.",
      "do_not_copy": "Do not edit the existing ds5319-swd object. Do not redraw sample-01-swd-vectors.svg. Do not draw pin 35 as SWCLK."
    },
    {
      "id": "ds5319-rtc",
      "claim": "LSE is 32.768 kHz on pin 3 and pin 4. Pin 1 is VBAT. Load capacitance in picofarads stays out of this object.",
      "do_not_copy": "Do not edit the existing ds5319-rtc object. Do not write 6 pF into it."
    },
    {
      "id": "rm0008-rtc",
      "claim": "32.768 kHz with PRL = 32767 is 1 Hz. Timed wake on this part is the alarm in chapter 11, not the F4 wake-up timer.",
      "do_not_copy": "Do not edit the existing rm0008-rtc object. Do not redraw the chapter 11 figure."
    },
    {
      "id": "rm0008-wdg",
      "claim": "The independent watchdog keeps counting in Stop and Standby. The 14 µA cell does not include it.",
      "do_not_copy": "Do not edit the existing rm0008-wdg object. Do not invent a Stop-plus-IWDG microamp."
    },
    {
      "id": "pm0075-rdp",
      "claim": "Chapter 16 only cross-references readout protection. It does not redraw the chapter 01 keys.",
      "do_not_copy": "Do not edit the existing pm0075-rdp object."
    },
    {
      "id": "pm0056",
      "claim": "CFSR is at 0xE000ED28, HFSR at 0xE000ED2C, MMFAR at 0xE000ED34, and BFAR at 0xE000ED38. BFAR is valid only when CFSR bit 15 is 1. FORCED is bit 30, value 0x40000000.",
      "do_not_copy": "Do not edit the existing pm0056 object. Do not put 167 ns in chapter 17."
    },
    {
      "id": "rm0008-boot",
      "claim": "BOOT0 = 0 enters main Flash at 0x08000000. BOOT1 = 0 and BOOT0 = 1 enter system memory at 0x1FFFF000. The connectivity address 0x1FFFB000 is void on this C8. The pins are latched on the fourth rising edge of SYSCLK.",
      "do_not_copy": "Do not edit the existing rm0008-boot object. Do not redraw sample-00-boot-state.svg."
    },
    {
      "id": "project-examples",
      "claim": "examples/freertos-task documents a 1000 Hz tick and TIM4 as the HAL time base. examples/iap-bootloader sizes one application as 0xB800. The CAN example uses 120 ohm at each end.",
      "do_not_copy": "Do not edit the existing project-examples object. Do not open a new example id. Do not change the example trees."
    },
    {
      "id": "rm0008-adc",
      "claim": "The conversion denominator is 4096. Code 2048 at a nominal 3.3 V is 1.65 V.",
      "do_not_copy": "Do not edit the existing rm0008-adc object. Do not redraw the chapter 09 figure."
    },
    {
      "id": "rm0008-flash",
      "claim": "This C8 has 64 KB of Flash and programs by half-word. Chapter 19 only cross-references that map.",
      "do_not_copy": "Do not edit the existing rm0008-flash object. Do not redraw sample-12-iap-map.svg."
    },
    {
      "id": "freertos-syscall",
      "claim": "With 4 priority bits, 5 shifted left by 4 is 0x50. Chapter 18 only cross-references that value and TIM4.",
      "do_not_copy": "Do not edit the existing freertos-syscall object. Do not redraw sample-15-rtos-prio.svg. Do not put 17.2 percent in chapter 18."
    }
  ],
  "absorb": [
    {
      "id": "ds5319-pwr",
      "chapters": ["16"],
      "title_zh": "DS5319 Rev 20 表 16、表 18 和表 26 的电流与唤醒时间",
      "title_en": "DS5319 Rev 20 Tables 16, 18, and 26 current and wake-up time",
      "authority_zh": "ST 官方数据手册",
      "authority_en": "ST datasheet",
      "url": "https://www.st.com/resource/en/datasheet/stm32f103c8.pdf",
      "snapshot": "DS5319 Rev 20, July 2025. Table 16 typical values at TA = 25°C and VDD = 3.3 V, in this condition order: Stop with the main regulator running, internal RC and HSE off, and no independent watchdog, 24 µA; the same conditions with the regulator in low-power mode, 14 µA; Standby with LSI and IWDG on, 3.4 µA; Standby with LSI on and IWDG off, 3.2 µA; Standby with LSI, IWDG, LSE, and RTC off, 2 µA; backup domain with LSE and RTC on, 1.4 µA, which is IDD_VBAT and not the whole-chip Standby current. The 85°C Stop maximums are the printed 200 µA and 180 µA, not typical values. Table 18: Sleep at 72 MHz is 14.4 mA typical with all peripherals on and 5.5 mA typical with all peripherals off, at 25°C and 3.3 V. Table 26: Sleep 1.8 µs on the clock that was already running; Stop with the main regulator 3.6 µs; Stop with the low-power regulator 5.4 µs; Standby 50 µs. Stop and Standby times are measured on the 8 MHz HSI until the first user instruction. Sleep keeps the clock from before the sleep. Table 27 tLOCK maximum is 200 µs and is not added to 5.4 µs. Section 2.3.12: Stop exits on EXTI; Standby exits on NRST, IWDG, a rising edge on WKUP, or the RTC alarm; SRAM is lost in Standby. If a printed cell differs, replace the cell and say so in the implementation PR. This snapshot does not contain a 14 to 20 µA range and does not call 1.4 µA the whole-chip standby current.",
      "license": "ST document terms (link and restated facts only; the manual is not redistributed)",
      "license_class": "ST-facts-restated",
      "section": "Table 16",
      "do_not_copy": true,
      "points": [
        "At 3.3 V and 25°C the low-power-regulator Stop cell is 14 µA and the main-regulator cell is 24 µA. Both cells exclude the independent watchdog",
        "Standby is 3.4, 3.2, or 2 µA according to LSI and IWDG. 1.4 µA is the backup domain",
        "Sleep is 14.4 mA or 5.5 mA. Wake-up is 1.8, 3.6, 5.4, or 50 µs. tLOCK at 200 µs is not the wake-up time"
      ]
    },
    {
      "id": "rm0008-pwr",
      "chapters": ["16"],
      "title_zh": "RM0008 Rev 21 退出 Stop 后回到 HSI",
      "title_en": "RM0008 Rev 21 returns to HSI when Stop exits",
      "authority_zh": "ST 官方参考手册",
      "authority_en": "ST reference manual",
      "url": "https://www.st.com/resource/en/reference_manual/rm0008-stm32f101xx-stm32f102xx-stm32f103xx-advanced-arm-based-32-bit-mcus-stmicroelectronics.pdf",
      "snapshot": "RM0008 Rev 21, February 2021. Default the power-control chapter. After entering Stop, clocks in the 1.8 V domain stop and HSI, HSE, and the PLL are off. On leaving Stop the system clock is HSI and the clock configuration has to be programmed again. PDDS = 0 and SLEEPDEEP = 1 is Stop. PDDS = 1 and SLEEPDEEP = 1 is Standby. The low-power regulator is the printed LPDS bit. If the printed chapter title or bit names differ, use the printed text. The claim does not change: exit from Stop is HSI, and the clock setup must be restored before the next USART byte. This snapshot does not restate the 8 MHz HSI calibration from chapter 02 and does not include an F4 periodic wake-up timer.",
      "license": "ST document terms (link and restated facts only; the manual is not redistributed)",
      "license_class": "ST-facts-restated",
      "section": "power control",
      "do_not_copy": true,
      "points": [
        "Leaving Stop returns the system clock to HSI. Program the PLL again before the next byte",
        "PDDS = 0 and SLEEPDEEP = 1 is Stop. PDDS = 1 and SLEEPDEEP = 1 is Standby",
        "The F4 periodic wake-up timer is not in this chapter"
      ]
    },
    {
      "id": "pm0056-dwt",
      "chapters": ["17", "18"],
      "title_zh": "PM0056 的 DEMCR bit 24 与 DWT 周期计数",
      "title_en": "PM0056 DEMCR bit 24 and the DWT cycle counter",
      "authority_zh": "ST 官方编程手册",
      "authority_en": "ST programming manual",
      "url": "https://www.st.com/resource/en/programming_manual/pm0056-stm32f10xxx-cortex-m3-programming-manual-stmicroelectronics.pdf",
      "snapshot": "PM0056, the same PDF as pm0056-nvic. DEMCR is at 0xE000EDFC. Bit 24 enables trace. After that bit is set, DWT_CYCCNT at 0xE0001004 counts. At 72 MHz, 72 counts are 1 µs. If bit 24 is clear, the counter stays at 0 and a delta reads 0. If the printed bit is not 24, record the printed bit and keep the printed addresses. Cortex-M3 hardware breakpoint comparators default to 6. The M7 count of 8 is void on this C8. This snapshot does not restate the four fault addresses already in pm0056, does not include 167 ns, and does not invent a data-watchpoint count or an FPB base address.",
      "license": "ST document terms (link and restated facts only; the manual is not redistributed)",
      "license_class": "ST-facts-restated",
      "section": "DWT",
      "do_not_copy": true,
      "points": [
        "Set DEMCR bit 24 before reading DWT_CYCCNT. A clear bit reads a delta of 0",
        "At 72 MHz, 72 counts are 1 µs",
        "This Cortex-M3 has 6 hardware breakpoint comparators. 8 is void on the C8"
      ]
    },
    {
      "id": "ds5319-nrst",
      "chapters": ["18"],
      "title_zh": "DS5319 Rev 20 图 31 的 NRST 电容",
      "title_en": "DS5319 Rev 20 Figure 31 NRST capacitor",
      "authority_zh": "ST 官方数据手册",
      "authority_en": "ST datasheet",
      "url": "https://www.st.com/resource/en/datasheet/stm32f103c8.pdf",
      "snapshot": "DS5319 Rev 20, July 2025, Figure 31. The external reset circuit prints 0.1 µF on NRST. 0.1 µF is 100 nF. Pin 7 remains the cross-reference already in ds5319-swd and is not renumbered here. If the printed capacitor is not 0.1 µF, use the printed value. This snapshot does not include the internal pull-up in kilohms. Add that typical value only after opening Table 39 of this same datasheet, and do not open a second id for it.",
      "license": "ST document terms (link and restated facts only; the manual is not redistributed)",
      "license_class": "ST-facts-restated",
      "section": "Figure 31",
      "do_not_copy": true,
      "points": [
        "Figure 31 puts 0.1 µF on NRST",
        "0.1 µF and 100 nF are the same capacitor. Write the figure's 0.1 µF",
        "Do not write a pull-up in kilohms until Table 39 of this datasheet is opened"
      ]
    },
    {
      "id": "ds5319-lse",
      "chapters": ["18"],
      "title_zh": "DS5319 Rev 20 的 LSE 负载电容范围",
      "title_en": "DS5319 Rev 20 LSE load-capacitor range",
      "authority_zh": "ST 官方数据手册",
      "authority_en": "ST datasheet",
      "url": "https://www.st.com/resource/en/datasheet/stm32f103c8.pdf",
      "snapshot": "DS5319 Rev 20, July 2025, LSE oscillator section. CL1 and CL2 are chosen from the 5 pF to 15 pF ceramic range to match the crystal, and the two capacitors are usually equal. 6 pF is not a required value printed in that section. 32.768 kHz, pin 3, pin 4, and PRL = 32767 stay on ds5319-rtc and rm0008-rtc. This snapshot does not copy 6 pF in as a requirement and does not copy a ppm tolerance.",
      "license": "ST document terms (link and restated facts only; the manual is not redistributed)",
      "license_class": "ST-facts-restated",
      "section": "LSE oscillator",
      "do_not_copy": true,
      "points": [
        "CL1 and CL2 are chosen in the 5 pF to 15 pF range with the crystal",
        "6 pF is not a required value",
        "32.768 kHz and PRL = 32767 stay on the existing RTC ids"
      ]
    }
  ]
}
```

- [ ] **Step 2: 写许可门测试**

保存为 `stm32-book/tests/test_batch6_sources.py`：

```python
#!/usr/bin/env python3
"""License gate for chapters 16, 17, 18, and 19. The manifest is updated later."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE_LIST = ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch6-16-17-18-19-source-list.json"
LOCK = ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch6-16-17-18-19-lock.json"
ALLOWED = {
    "ST-facts-restated",
    "MIT",
    "BSD-2-Clause",
    "BSD-3-Clause",
    "ISC",
    "CC BY 4.0",
    "CC BY 3.0",
    "CC0",
}
REJECTED = ("GPL", "LGPL", "CC BY-NC", "CC BY-ND", "All rights reserved", "Apache-2.0")
ABSORB = [
    "ds5319-pwr",
    "rm0008-pwr",
    "pm0056-dwt",
    "ds5319-nrst",
    "ds5319-lse",
]
REUSED = [
    "rm0008-rcc",
    "rm0008-usart",
    "ds5319-usart",
    "ds5319-adc",
    "ds5319-gpio",
    "ds5319-swd",
    "ds5319-rtc",
    "rm0008-rtc",
    "rm0008-wdg",
    "pm0075-rdp",
    "pm0056",
    "rm0008-boot",
    "project-examples",
    "rm0008-adc",
    "rm0008-flash",
    "freertos-syscall",
]


class Batch6SourceListTests(unittest.TestCase):
    def test_lock_keeps_chapters_16_17_18_19(self) -> None:
        lock = json.loads(LOCK.read_text(encoding="utf-8"))
        self.assertEqual(["16", "17", "18", "19"], lock["chapters"])
        self.assertTrue(lock["four_blocks_absent"])
        self.assertTrue(lock["old_pitfall_heading_present"])
        self.assertEqual(["18", "19"], lock["chapters_without_old_pitfall"])
        self.assertEqual(40, len(lock["baseline"]))
        self.assertEqual("2026-10-25-classic-encyclopedia-batch6-16-17-18-19", lock["rubric"])
        expected = (
            ("16", "docs/16-低功耗设计.md", "docs/en/16-low-power.md", True),
            ("17", "docs/17-调试与性能优化.md", "docs/en/17-debug.md", True),
            ("18", "docs/18-常见问题FAQ.md", "docs/en/18-faq.md", False),
            ("19", "docs/19-项目实战合集.md", "docs/en/19-projects.md", False),
        )
        for prefix, zh_name, en_name, expects_old in expected:
            row = lock["files"][prefix]
            self.assertEqual(zh_name, row["zh"])
            self.assertEqual(en_name, row["en"])
            self.assertFalse(row["zh_four_blocks"])
            self.assertFalse(row["en_four_blocks"])
            self.assertEqual(expects_old, row["expects_old_pitfall"])
            self.assertEqual(expects_old, row["zh_old_pitfall"])
            self.assertEqual(expects_old, row["en_old_pitfall"])
            self.assertEqual("## ⚠️ Pitfalls and troubleshooting", row["en_old_heading"])

    def test_source_list_keeps_the_license_gate(self) -> None:
        payload = json.loads(SOURCE_LIST.read_text(encoding="utf-8"))
        self.assertEqual(["16", "17", "18", "19"], payload["chapters"])
        self.assertEqual([], payload["community"])
        ids = [item["id"] for item in payload["absorb"]]
        self.assertEqual(ABSORB, ids)
        self.assertEqual(5, len(ids))
        for item in payload["absorb"]:
            self.assertIn(item["license_class"], ALLOWED)
            self.assertTrue(item["url"].startswith("https://"))
            self.assertNotIn("http://", item["url"])
            for banned in REJECTED:
                self.assertNotIn(banned, item["license"])
                self.assertNotIn(banned, item["license_class"])
            self.assertTrue(item["do_not_copy"])
            self.assertGreaterEqual(len(item["points"]), 1)
        by_id = {item["id"]: item for item in payload["absorb"]}
        self.assertEqual("Table 16", by_id["ds5319-pwr"]["section"])
        self.assertEqual("power control", by_id["rm0008-pwr"]["section"])
        self.assertEqual("DWT", by_id["pm0056-dwt"]["section"])
        self.assertEqual("Figure 31", by_id["ds5319-nrst"]["section"])
        self.assertEqual("LSE oscillator", by_id["ds5319-lse"]["section"])
        power = by_id["ds5319-pwr"]["snapshot"]
        self.assertIn("14 µA", power)
        self.assertIn("24 µA", power)
        self.assertIn("5.4 µs", power)
        self.assertIn("14.4 mA", power)
        self.assertIn("5.5 mA", power)
        self.assertNotIn("14 to 20", power)
        self.assertNotIn("14~20", power)
        stop = by_id["rm0008-pwr"]["snapshot"]
        self.assertIn("HSI", stop)
        self.assertNotIn("HAL_RTCEx_SetWakeUpTimer_IT", stop)
        dwt = by_id["pm0056-dwt"]["snapshot"]
        self.assertIn("0xE000EDFC", dwt)
        self.assertIn("0xE0001004", dwt)
        self.assertIn("bit 24", dwt)
        self.assertNotIn("167 ns", dwt)
        nrst = by_id["ds5319-nrst"]["snapshot"]
        self.assertIn("0.1 µF", nrst)
        self.assertNotIn("30 kΩ", nrst)
        self.assertNotIn("40 kΩ", nrst)
        lse = by_id["ds5319-lse"]["snapshot"]
        self.assertIn("5 pF", lse)
        self.assertIn("15 pF", lse)
        self.assertIn("6 pF is not a required value", lse)
        reused = [item["id"] for item in payload["reuse_existing"]]
        self.assertEqual(REUSED, reused)
        self.assertNotIn("pm0056-nvic", ids)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: 运行测试，并只核对会改 snapshot 的六处**

Run: `python3 stm32-book/tests/test_batch6_sources.py -v`

Expected: OK，两条测试都通过。清单已经在这一任务的工作区里，所以这一步不是 `FileNotFoundError`。若失败，改清单去满足上面的断言，不要放宽 `ABSORB`，也不要删掉测试来制造一次红色。不要追加第六个 id。

锁定文件那一条若失败，先回到 Task 1。不要改测试去迁就一份章号不对的锁。

然后打开 Step 开头的三个 URL，只核对下面六处。印出的句子还在，清单不动。

表 16：读 DS5319 Rev 20 表 16，VDD = 3.3 V、TA = 25°C。默认六格是 24、14、3.4、3.2、2、1.4 µA，条件和本计划 Global Constraints 里的顺序相同。印出的格子不同，把 `ds5319-pwr` 的 snapshot 改成印出的格子，并在实施 PR 里写明。不沿用「14~20 µA」去否定表 16。85°C 的 200 µA 和 180 µA 仍是最大值，不写成典型值。

表 26：默认四格都是微秒，1.8、3.6、5.4、50。印出的单位不同就改单位，不把 Standby 写成毫秒。`tLOCK` 最大值默认 200 µs，不和 5.4 µs 相加。

电源控制章号：默认 RM0008 的电源控制章。印出的标题或章号不同，改 `rm0008-pwr` 的 `section` 和 snapshot。退出 Stop 后系统时钟是 HSI、配置要重装，这两句不变。`SLEEPDEEP`、`PDDS`、`LPDS` 以印出的位名为准。

DEMCR 的位：默认 bit 24，地址 `0xE000EDFC` 和 `0xE0001004`。印出的不是 24 就改 `pm0056-dwt` 的 snapshot。72 个计数等于 1 µs 不变。硬件断点个数按印出的 Cortex-M3 个数，默认 6。

NRST 上拉：表 39 的典型值只有这一步打开了同一份 DS5319 才写进 `ds5319-nrst`。没打开之前，snapshot 和四块只写图 31 的 0.1 µF。不要新开 id。

MMARVALID：只有 PM0056 印出了位号才补进 `pm0056` 所在的主张。这一批不改 `pm0056` 对象。没印出之前，四块只把 bit 15 写死在 `BFAR` 上，不给 `MMFAR` 编一个位号。

无论哪一处，都不要改 `license_class`，不要改另外几个 id 的 `points`，不要新增第六个 id。

- [ ] **Step 4: 再跑测试并提交**

Run: `python3 stm32-book/tests/test_batch6_sources.py -v`

Expected: OK。

```bash
git add docs/superpowers/plans/2026-10-25-batch6-16-17-18-19-source-list.json stm32-book/tests/test_batch6_sources.py
git commit -m "docs: 钉上 16、17、18、19 的许可门"
```

不要在这一笔里改章节正文。不要改已有来源对象。

### Task 3: Static key figures

**Files:**
- Modify: `tools/gen_sample_figures.py`（只追加函数，并在 `main()` 里多保存四张。不改 `boot_state`、`gpio_led`、`exception_stack`、`uart_frame`、`clock_tree`、`pwm_1khz`、`spi_jedec`、`adc_sample`、`swd_vectors`、`i2c_addr`、`dma_cndtr`、`iwdg_1s`、`iap_map`、`can_bit`、`usb_enum`、`rtos_prio`、`_credit`）
- Create: `assets/diagrams/sample-16-stop-wake.svg`
- Create: `assets/diagrams/sample-17-cfsr.svg`
- Create: `assets/diagrams/sample-18-boot-triage.svg`
- Create: `assets/diagrams/sample-19-flash-fit.svg`
- Modify: `assets/README.md`（开头的生成命令，第一节里 `lowpower-wakeup.svg` 和 `debug-swo.svg` 的说明，第二节里 `peripheral-wiring.svg` 的说明，第四节表的末尾）
- Create: `stm32-book/tests/test_batch6_chapters.py`
- Test: `stm32-book/tests/test_batch6_chapters.py`

**Interfaces:**
- Consumes: Task 2 清单里的订货号、脚位和寄存器名。已有的 `_credit(canvas, note)`。
- Produces: `stop_wake() -> Svg`、`cfsr_read() -> Svg`、`boot_triage() -> Svg`、`flash_fit() -> Svg`。四张 SVG 不含 `<animate`、`@keyframes`、`animation:`，不含「矢量动画」，不含「实拍」，含「自绘」。每张都小于 60 KB。默认不产生 `sample-16-standby.svg`。

`sample-16-stop-wake.svg` 的文本含 `STM32F103C8T6`、`LQFP48`、`14 uA`、`24 uA`、`5.4 us`、`8 MHz`、`72 MHz`、`0x271`、`12800`、`115200`、`SLEEPDEEP=1`、`PDDS=0`、`pin 10`、`PA0`。不含 `14~20`，不含 `780`，不含 `8/16`。

`sample-17-cfsr.svg` 的文本含 `STM32F103C8T6`、`0xE000ED28`、`0xE000ED2C`、`0xE000ED38`、`0xE000EDFC`、`0xE0001004`、`0x40000000`、`bit 15`、`bit 24`、`bit 30`、`1 us`、`72`、`6`、`pin 39`、`JTDO`。不含 `167 ns`。

`sample-18-boot-triage.svg` 的文本含 `STM32F103C8T6`、`pin 34`、`PA13`、`pin 37`、`PA14`、`pin 7`、`0.1 uF`、`pin 44`、`BOOT0`、`0x08000000`、`0x1FFFF000`。不含 `0x1FFFB000`。

`sample-19-flash-fit.svg` 的文本含 `STM32F103C8T6`、`0x08000000`、`0x08004000`、`0x08004800`、`0x08010000`、`0x0801B800`、`0xB800`、`110 KB`、`20480`、`65536`、`4096`。不含 `0x5A5A0001`。

- [ ] **Step 1: 写会失败的主图测试**

保存为 `stm32-book/tests/test_batch6_chapters.py`：

```python
#!/usr/bin/env python3
"""Checks for thickened chapters 16, 17, 18, and 19 and their static figures."""

from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIAGRAMS = ROOT / "assets" / "diagrams"
STOP = DIAGRAMS / "sample-16-stop-wake.svg"
CFSR = DIAGRAMS / "sample-17-cfsr.svg"
BOOT = DIAGRAMS / "sample-18-boot-triage.svg"
FLASH = DIAGRAMS / "sample-19-flash-fit.svg"


class Batch6FigureTests(unittest.TestCase):
    def test_key_figures_are_static_and_under_60_kib(self) -> None:
        for path, tokens, banned in (
            (
                STOP,
                (
                    "STM32F103C8T6",
                    "LQFP48",
                    "14 uA",
                    "24 uA",
                    "5.4 us",
                    "8 MHz",
                    "72 MHz",
                    "0x271",
                    "12800",
                    "115200",
                    "SLEEPDEEP=1",
                    "PDDS=0",
                    "pin 10",
                    "PA0",
                    "自绘",
                ),
                ("14~20", "780", "8/16", "<animate", "@keyframes", "animation:", "矢量动画", "实拍"),
            ),
            (
                CFSR,
                (
                    "STM32F103C8T6",
                    "0xE000ED28",
                    "0xE000ED2C",
                    "0xE000ED38",
                    "0xE000EDFC",
                    "0xE0001004",
                    "0x40000000",
                    "bit 15",
                    "bit 24",
                    "bit 30",
                    "1 us",
                    "72",
                    "6",
                    "pin 39",
                    "JTDO",
                    "自绘",
                ),
                ("167 ns", "<animate", "@keyframes", "animation:", "矢量动画", "实拍"),
            ),
            (
                BOOT,
                (
                    "STM32F103C8T6",
                    "pin 34",
                    "PA13",
                    "pin 37",
                    "PA14",
                    "pin 7",
                    "0.1 uF",
                    "pin 44",
                    "BOOT0",
                    "0x08000000",
                    "0x1FFFF000",
                    "自绘",
                ),
                ("0x1FFFB000", "<animate", "@keyframes", "animation:", "矢量动画", "实拍"),
            ),
            (
                FLASH,
                (
                    "STM32F103C8T6",
                    "0x08000000",
                    "0x08004000",
                    "0x08004800",
                    "0x08010000",
                    "0x0801B800",
                    "0xB800",
                    "110 KB",
                    "20480",
                    "65536",
                    "4096",
                    "自绘",
                ),
                ("0x5A5A0001", "<animate", "@keyframes", "animation:", "矢量动画", "实拍"),
            ),
        ):
            text = path.read_text(encoding="utf-8")
            self.assertLess(path.stat().st_size, 60 * 1024, path.name)
            self.assertNotIn("Svg.footer", text)
            for token in tokens:
                self.assertIn(token, text, path.name)
            for token in banned:
                self.assertNotIn(token, text, path.name)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试，确认它因为文件不存在而失败**

Run: `python3 stm32-book/tests/test_batch6_chapters.py -v`

Expected: FAIL，`sample-16-stop-wake.svg` 不存在（`FileNotFoundError`）。

- [ ] **Step 3: 追加四个生成函数并写出 SVG**

在 `tools/gen_sample_figures.py` 的 `rtos_prio()` 之后、`main()` 之前插入下面四个函数。不要改已有十六个函数，也不要改 `_credit`。不要调用 `Svg.footer()`。

```python
def stop_wake() -> Svg:
    canvas = Svg(
        960,
        980,
        "低功耗稳压器的 Stop 典型值是 14 µA；醒来先是 HSI 8 MHz；不重配时钟时 0x271 变成 12800 bit/s",
        "STM32F103C8T6 LQFP48 · DS5319 Rev 20 Table 16 / Table 26",
    )
    canvas.header(tag="16", tag_color=T.CYAN)
    canvas.text(40, 86, "STM32F103C8T6  LQFP48  Stop  low-power regulator", size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "SLEEPDEEP=1  PDDS=0  14 uA at 3.3 V, 25 C, no IWDG", size=14, fill=T.CYAN)
    canvas.text(40, 138, "pin 10 PA0 is the Stop key. The lamp and ADC are not drawn on this pin", size=14, fill=T.AMBER)
    canvas.text(40, 170, "正常路径  EXTI wakes the core, then the PLL returns to 72 MHz", size=16, fill=T.GREEN, weight="700")
    canvas.rect(40, 184, 880, 160, fill=T.PANEL, stroke=T.GREEN, rx=8)
    canvas.text(56, 214, "first instruction on HSI 8 MHz. Table 26 says 5.4 us", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 240, "SystemClock_Config() restores the PLL to 72 MHz", size=14, fill=T.GREEN)
    canvas.text(56, 266, "USART1 still uses 0x271. The line is 115200", size=14, fill=T.TEXT)
    canvas.text(56, 292, "5.4 us does not include the 200 us PLL lock maximum", size=14, fill=T.AMBER)
    canvas.text(56, 318, "the main-regulator cell is 3.6 us, not this path", size=13, fill=T.MUTED)
    canvas.text(40, 370, "失败路径  the same 0x271 is left on the 8 MHz HSI", size=16, fill=T.RED, weight="700")
    canvas.rect(40, 384, 880, 120, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(56, 414, "8e6 / (16 x 39.0625) = 12800 bit/s", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 440, "the host is still at 115200. The ratio is 9", size=14, fill=T.RED)
    canvas.text(56, 466, "16 MHz is void on this C8", size=14, fill=T.AMBER)
    canvas.rect(40, 524, 880, 150, fill=T.BG2, stroke=T.VIOLET, rx=8)
    canvas.text(56, 554, "旁注  quoting 14 uA while the main regulator is on is the 24 uA cell", size=15, fill=T.VIOLET, weight="700")
    canvas.text(56, 580, "the F4 periodic wake-up timer is void on this C8", size=14, fill=T.TEXT)
    canvas.text(56, 606, "pin 10 is not drawn as a lamp at the same time", size=14, fill=T.AMBER)
    canvas.text(56, 632, "Standby currents stay off this sheet unless it is split", size=13, fill=T.MUTED)
    canvas.text(56, 656, "do not draw the chapter 06 bit frame", size=13, fill=T.MUTED)
    _credit(canvas, "自绘。电流和 5.4 us 来自 DS5319 Rev 20 表 16 与表 26。8 MHz 来自第 02 章。")
    return canvas


def cfsr_read() -> Svg:
    canvas = Svg(
        960,
        980,
        "BFAR 要 bit 15 为 1 才有效；72 MHz 下 72 个周期是 1 µs，而且要先打开 DEMCR bit 24",
        "STM32F103C8T6 · PM0056",
    )
    canvas.header(tag="17", tag_color=T.CYAN)
    canvas.text(40, 86, "STM32F103C8T6  Cortex-M3  no FPU", size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "CFSR 0xE000ED28    HFSR 0xE000ED2C    BFAR 0xE000ED38", size=14, fill=T.CYAN)
    canvas.text(40, 138, "FORCED is bit 30, value 0x40000000. PC is stacked word 6", size=14, fill=T.AMBER)
    canvas.text(40, 170, "正常路径  bit 15 is 1, and DEMCR bit 24 is already 1", size=16, fill=T.GREEN, weight="700")
    canvas.rect(40, 184, 880, 160, fill=T.PANEL, stroke=T.GREEN, rx=8)
    canvas.text(56, 214, "bit 15 = 1, so BFAR is this access", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 240, "DEMCR 0xE000EDFC bit 24, then DWT_CYCCNT 0xE0001004", size=14, fill=T.GREEN)
    canvas.text(56, 266, "72 counts at 72 MHz are 1 us", size=14, fill=T.TEXT)
    canvas.text(56, 292, "this M3 has 6 hardware breakpoints", size=14, fill=T.AMBER)
    canvas.text(56, 318, "PC is the 6th stacked word", size=13, fill=T.MUTED)
    canvas.text(40, 370, "失败路径  bit 15 is 0, or bit 24 was never set", size=16, fill=T.RED, weight="700")
    canvas.rect(40, 384, 880, 120, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(56, 414, "bit 15 = 0. The value in BFAR is not this access", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 440, "bit 24 = 0. The cycle delta is 0", size=14, fill=T.RED)
    canvas.text(56, 466, "8 hardware breakpoints are the M7 count and are void here", size=14, fill=T.AMBER)
    canvas.rect(40, 524, 880, 140, fill=T.BG2, stroke=T.VIOLET, rx=8)
    canvas.text(56, 554, "旁注  pin 39 is still JTDO after reset", size=15, fill=T.VIOLET, weight="700")
    canvas.text(56, 580, "TRACESWO is the remap column, not the power-up name", size=14, fill=T.TEXT)
    canvas.text(56, 606, "do not draw an SWO waveform on this figure", size=14, fill=T.AMBER)
    canvas.text(56, 632, "do not draw the 8-register timing waveform", size=13, fill=T.MUTED)
    _credit(canvas, "自绘。故障地址来自 PM0056。DWT 使能顺序是先 0xE000EDFC bit 24，再 0xE0001004。")
    return canvas


def boot_triage() -> Svg:
    canvas = Svg(
        960,
        960,
        "认不出芯片时先看第 34 脚、第 37 脚和第 44 脚；BOOT0 为 1 且 BOOT1 为 0 时跑的是 0x1FFFF000",
        "STM32F103C8T6 LQFP48 · DS5319 Rev 20 Figure 31 / Table 5",
    )
    canvas.header(tag="18", tag_color=T.CYAN)
    canvas.text(40, 86, "STM32F103C8T6  LQFP48  first look when the probe sees no target", size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "pin 34 PA13 = SWDIO    pin 37 PA14 = SWCLK", size=14, fill=T.CYAN)
    canvas.text(40, 138, "pin 7 NRST has 0.1 uF. pin 44 is BOOT0", size=14, fill=T.AMBER)
    canvas.text(40, 170, "正常路径  BOOT0 = 0, the CPU starts at 0x08000000", size=16, fill=T.GREEN, weight="700")
    canvas.rect(40, 184, 880, 150, fill=T.PANEL, stroke=T.GREEN, rx=8)
    canvas.text(56, 214, "probe on pin 34 and pin 37, common ground, 3.3 V", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 240, "BOOT0 = 0 selects main Flash at 0x08000000", size=14, fill=T.GREEN)
    canvas.text(56, 266, "Flash is 64 KB. SRAM is 20 KB", size=14, fill=T.TEXT)
    canvas.text(56, 292, "look at the wires before the optimizer", size=13, fill=T.MUTED)
    canvas.text(40, 360, "失败路径  BOOT0 = 1 and BOOT1 = 0", size=16, fill=T.RED, weight="700")
    canvas.rect(40, 374, 880, 120, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(56, 404, "the CPU is in system memory at 0x1FFFF000", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 430, "the image in Flash looks as if it was never programmed", size=14, fill=T.RED)
    canvas.text(56, 456, "changing -O2 before checking these pins is the other miss", size=14, fill=T.AMBER)
    canvas.rect(40, 514, 880, 140, fill=T.BG2, stroke=T.VIOLET, rx=8)
    canvas.text(56, 544, "旁注  pin 35 is VSS_2, not SWCLK", size=15, fill=T.VIOLET, weight="700")
    canvas.text(56, 570, "that mistake is already drawn in chapter 01", size=14, fill=T.TEXT)
    canvas.text(56, 596, "do not draw 38 icons on this figure", size=14, fill=T.AMBER)
    canvas.text(56, 622, "do not draw CFSR bits here", size=13, fill=T.MUTED)
    _credit(canvas, "自绘。0.1 uF 来自 DS5319 Rev 20 图 31。启动地址来自 RM0008。")
    return canvas


def flash_fit() -> Svg:
    canvas = Svg(
        960,
        980,
        "C8 只有一张 0xB800 的 APP；两张是 110 KB；65536 字节大于 20 KB SRAM",
        "STM32F103C8T6 · chapter 12 map · DS5319 64 KB / 20 KB",
    )
    canvas.header(tag="19", tag_color=T.CYAN)
    canvas.text(40, 86, "STM32F103C8T6  Flash 0x08000000 to 0x08010000  SRAM 20 KB", size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "16 KB + 2 KB + 46 KB = 64 KB. APP length 0xB800", size=14, fill=T.CYAN)
    canvas.text(40, 138, "SRAM 20 KB = 20480 bytes", size=14, fill=T.AMBER)
    canvas.text(40, 170, "正常路径  one application ends before 0x08010000", size=16, fill=T.GREEN, weight="700")
    canvas.rect(40, 184, 880, 150, fill=T.PANEL, stroke=T.GREEN, rx=8)
    canvas.text(56, 214, "bootloader 0x08000000, 16 KB, ends at 0x08004000", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 240, "parameters 0x08004000, 2 KB, ends at 0x08004800", size=14, fill=T.GREEN)
    canvas.text(56, 266, "one APP at 0x08004800, 0xB800, ends at 0x08010000", size=14, fill=T.TEXT)
    canvas.text(56, 292, "denominator 4096. Code 2048 is 1.65 V", size=13, fill=T.MUTED)
    canvas.text(40, 360, "失败路径  a second 0xB800 and a 65536-byte array", size=16, fill=T.RED, weight="700")
    canvas.rect(40, 374, 880, 130, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(56, 404, "16 + 2 + 46 + 46 = 110 KB, drawn out to 0x0801B800", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 430, "that end is outside this 64 KB", size=14, fill=T.RED)
    canvas.text(56, 456, "65536 bytes is larger than 20480 bytes of SRAM", size=14, fill=T.AMBER)
    canvas.rect(40, 524, 880, 140, fill=T.BG2, stroke=T.VIOLET, rx=8)
    canvas.text(56, 554, "旁注  denominator 4095 is the miss, not this path", size=15, fill=T.VIOLET, weight="700")
    canvas.text(56, 580, "133 bytes is an application frame, not one 64-byte USB packet", size=14, fill=T.TEXT)
    canvas.text(56, 606, "do not draw a motor pin. Do not draw a WS2812 waveform", size=14, fill=T.AMBER)
    canvas.text(56, 632, "chapter 12 does not have a second slot", size=13, fill=T.MUTED)
    _credit(canvas, "自绘。地图来自第 12 章。64 KB 与 20 KB 来自 DS5319。")
    return canvas
```

把 `main()` 末尾、`rtos_prio().save(...)` 那一行之后加上这四行。不要删掉已有的十六次 `save`。

```python
    stop_wake().save(os.path.join(out_dir, "sample-16-stop-wake.svg"))
    cfsr_read().save(os.path.join(out_dir, "sample-17-cfsr.svg"))
    boot_triage().save(os.path.join(out_dir, "sample-18-boot-triage.svg"))
    flash_fit().save(os.path.join(out_dir, "sample-19-flash-fit.svg"))
```

Run: `python3 tools/gen_sample_figures.py`

Expected: 退出码 0。四张新 SVG 出现在 `assets/diagrams/`。`sample-16-stop-wake.svg` 小于 60 KB 时，不要另写 `sample-16-standby.svg`。它达到或超过 60 KB 时，把 Standby 的三格电流拆进 `standby_cells() -> Svg`，文件名 `sample-16-standby.svg`。第一张仍是 Stop 与 12800，仍含 `14 uA`、`5.4 us`、`0x271`、`12800`、`115200`。第二张含 `3.4 uA`、`3.2 uA`、`2 uA`、`50 us`、`PDDS=1`。两张都用 `_credit()`，都不调用 `Svg.footer()`。`main()` 多保存这一张。拆开仍超过时，在实施 PR 里写出字节数和原因，不把图画回简笔，也不把 60 KB 改成仓库新默认值。第 17、18、19 章不另起第二张文件名。若已有十六张 `sample-00` 到 `sample-15` 出现内容 diff，说明旧函数被改过，先还原那十六个函数再生成。不要把这十六张旧图的改动提交进来。

在 `assets/README.md` 开头的生成命令里，把

```text
python3 tools/gen_sample_figures.py   # 第 00 到第 15 章的静态主图
```

换成

```text
python3 tools/gen_sample_figures.py   # 第 00 到第 19 章的静态主图
```

第一节把这两行的说明改成辅图，文件本身不重画：

```text
| `lowpower-wakeup.svg` | 辅图：三种低功耗模式。文件不重画。14 µA、8 MHz 和 12800 在静态主图上 | 16 |
| `debug-swo.svg` | 辅图：SWO。文件不重画。CFSR、bit 15 和 1 µs 在静态主图上 | 17 |
```

`toolchain-flow.svg` 那一行改成：

```text
| `toolchain-flow.svg` | 辅图：编译箭头。文件不重画。认不出芯片时先看的脚在静态主图上 | 00 / 18 |
```

第二节 `peripheral-wiring.svg` 那一行改成：

```text
| `peripheral-wiring.svg` | 辅图：接线总览。文件不重画。一张 APP 和放不下的第二张在静态主图上 | — |
```

第四节表的末尾、`sample-15-rtos-prio.svg` 那一行之后追加：

```text
| `sample-16-stop-wake.svg` | 第 16 章静态主图：低功耗稳压器的 Stop 是 14 µA，醒来是 HSI 8 MHz；不重配时钟时 0x271 变成 12800。由 `tools/gen_sample_figures.py` 生成 |
| `sample-17-cfsr.svg` | 第 17 章静态主图：BFAR 要 bit 15 为 1；72 个 DWT 周期是 1 µs，要先置 DEMCR bit 24。由 `tools/gen_sample_figures.py` 生成 |
| `sample-18-boot-triage.svg` | 第 18 章静态主图：先看第 34 脚、第 37 脚和第 44 脚；BOOT0 为 1 且 BOOT1 为 0 时 CPU 在 0x1FFFF000。由 `tools/gen_sample_figures.py` 生成 |
| `sample-19-flash-fit.svg` | 第 19 章静态主图：一张 0xB800 停在 0x08010000 之前；两张是 110 KB，65536 字节大于 20 KB SRAM。由 `tools/gen_sample_figures.py` 生成 |
```

只有真的写出 `sample-16-standby.svg` 时才加第五行，并在实施 PR 里写明拆图原因。

- [ ] **Step 4: 运行测试并提交**

Run: `python3 stm32-book/tests/test_batch6_chapters.py -v`

Expected: OK。

```bash
git add tools/gen_sample_figures.py assets/diagrams/sample-16-stop-wake.svg assets/diagrams/sample-17-cfsr.svg assets/diagrams/sample-18-boot-triage.svg assets/diagrams/sample-19-flash-fit.svg assets/README.md stm32-book/tests/test_batch6_chapters.py
git commit -m "fig: 为第 16、17、18、19 章加上静态主图"
```

若拆出了 `sample-16-standby.svg`，把它一并 `git add`。提交前再看一眼：

```bash
git diff --stat -- assets/diagrams/sample-12-iap-map.svg assets/diagrams/sample-15-rtos-prio.svg assets/animations/lowpower-wakeup.svg assets/animations/debug-swo.svg assets/animations/toolchain-flow.svg assets/boards/peripheral-wiring.svg
```

Expected: 无输出。改的是 `assets/README.md` 里的说明，不是这四张旧动画 SVG。`peripheral-wiring.svg` 若在 `assets/diagrams/` 而不是 `assets/boards/`，以仓库里的实际路径为准，仍然要求那张图的 diff 为空。

### Task 4: Short auxiliary GIFs

**Files:**
- Modify: `tools/gen_gifs.py`（在 `BUILDERS` 之前追加四个函数，并给字典末尾加四个键。不改已有二十个函数）
- Create: `assets/gif/stop-wake.gif`
- Create: `assets/gif/cfsr-read.gif`
- Create: `assets/gif/boot0-low.gif`
- Create: `assets/gif/one-slot.gif`
- Modify: `assets/README.md`（第五节的表，以及「上面 20 张」那两句）
- Modify: `stm32-book/tests/test_batch6_chapters.py`
- Test: `stm32-book/tests/test_batch6_chapters.py`

**Interfaces:**
- Consumes: `tools/minigfx.py` 的 `Canvas`、`Gif`、`C`，以及 `chrome()`。已有的 `W` 和 `H`。
- Produces: `stop_wake_gif()`、`cfsr_read_gif()`、`boot0_low()`、`one_slot()`，各返回一帧数在 3 到 12 之间的 `Gif`。四个函数按这个顺序放在 `rtos_tick()` 之后、`BUILDERS` 之前。`BUILDERS` 的键在原有 20 个之后增加 `"stop-wake"`、`"cfsr-read"`、`"boot0-low"`、`"one-slot"`。`stop_wake_gif` 的源码含 `8 MHz`、`72 MHz`、`115200`，不含 `12800`，不含 `24 uA`。`cfsr_read_gif` 的源码含 `CFSR`、`bit 15 = 1`、`1 us`、`72`，不含 `bit 15 = 0`，不含 `delta 0`。`boot0_low` 的源码含 `pin 44`、`pin 34`、`pin 37`、`BOOT0 = 0`，不含 `BOOT0 = 1`，不含 `-O2`。`one_slot` 的源码含 `16 KB`、`2 KB`、`0xB800`、`0x08010000`，不含 `0x0801B800`，不含 `65536`。四条 GIF 文件都小于 500 KB。

- [ ] **Step 1: 把 GIF 断言加进测试**

在 `stm32-book/tests/test_batch6_chapters.py` 的 import 区加上 `import importlib.util`。在 `Batch6FigureTests` 之后、`if __name__` 之前追加：

```python
def _load_gifs():
    path = ROOT / "tools" / "gen_gifs.py"
    spec = importlib.util.spec_from_file_location("gen_gifs_batch6", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Batch6GifTests(unittest.TestCase):
    def test_four_auxiliary_gifs_are_short_and_ascii(self) -> None:
        gifs = _load_gifs()
        names = (
            "led-blink",
            "pwm-breath",
            "uart-bits",
            "i2c-timing",
            "dma-ring",
            "sar-adc",
            "nvic-preempt",
            "uart-idle",
            "clock-css",
            "pwm-1khz",
            "spi-jedec",
            "adc-sample",
            "swd-fetch",
            "i2c-addr",
            "dma-cndtr",
            "iwdg-1s",
            "iap-jump",
            "can-500k",
            "usb-48m",
            "rtos-tick",
            "stop-wake",
            "cfsr-read",
            "boot0-low",
            "one-slot",
        )
        for name in names:
            self.assertIn(name, gifs.BUILDERS)
        self.assertEqual(list(gifs.BUILDERS)[-4:], ["stop-wake", "cfsr-read", "boot0-low", "one-slot"])
        source = (ROOT / "tools" / "gen_gifs.py").read_text(encoding="utf-8")
        stop_src = source.split("def stop_wake_gif", 1)[1].split("def cfsr_read_gif", 1)[0]
        cfsr_src = source.split("def cfsr_read_gif", 1)[1].split("def boot0_low", 1)[0]
        boot_src = source.split("def boot0_low", 1)[1].split("def one_slot", 1)[0]
        slot_src = source.split("def one_slot", 1)[1].split("BUILDERS", 1)[0]
        self.assertIn("8 MHz", stop_src)
        self.assertIn("72 MHz", stop_src)
        self.assertIn("115200", stop_src)
        self.assertNotIn("12800", stop_src)
        self.assertNotIn("24 uA", stop_src)
        self.assertIn("CFSR", cfsr_src)
        self.assertIn("bit 15 = 1", cfsr_src)
        self.assertIn("1 us", cfsr_src)
        self.assertIn("72", cfsr_src)
        self.assertNotIn("bit 15 = 0", cfsr_src)
        self.assertNotIn("delta 0", cfsr_src)
        self.assertIn("pin 44", boot_src)
        self.assertIn("pin 34", boot_src)
        self.assertIn("pin 37", boot_src)
        self.assertIn("BOOT0 = 0", boot_src)
        self.assertNotIn("BOOT0 = 1", boot_src)
        self.assertNotIn("-O2", boot_src)
        self.assertIn("16 KB", slot_src)
        self.assertIn("2 KB", slot_src)
        self.assertIn("0xB800", slot_src)
        self.assertIn("0x08010000", slot_src)
        self.assertNotIn("0x0801B800", slot_src)
        self.assertNotIn("65536", slot_src)
        for name in ("stop-wake", "cfsr-read", "boot0-low", "one-slot"):
            gif = gifs.BUILDERS[name]()
            self.assertGreaterEqual(len(gif.frames), 3)
            self.assertLessEqual(len(gif.frames), 12)
            path = ROOT / "assets" / "gif" / f"{name}.gif"
            self.assertLess(path.stat().st_size, 500 * 1024, path.name)
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `python3 stm32-book/tests/test_batch6_chapters.py Batch6GifTests -v`

Expected: FAIL，`stop-wake` 不在 `BUILDERS` 里。

- [ ] **Step 3: 追加四个 BUILDERS 并只生成这四条 GIF**

在 `tools/gen_gifs.py` 的 `rtos_tick()` 之后、`BUILDERS = {` 之前插入：

```python
def stop_wake_gif():
    """Wake from Stop, move the clock from 8 MHz back to 72 MHz, then mark 115200.

    The failed baud and the other Stop cell stay on the static SVG.
    """
    g = Gif(W, H, delay=12)
    notes = (
        "STOP",
        "WAKE ON HSI",
        "8 MHz",
        "PLL ON",
        "72 MHz",
        "115200",
    )
    for index, note in enumerate(notes):
        c = Canvas(W, H)
        chrome(c, "STOP WAKE", "HSI", "AUX GIF  115200")
        c.panel(16, 48, 448, 28, C.PANEL, C.STROKE)
        c.text("0x271", 28, 58, C.MUTED, 1)
        c.text(note, 28, 120, C.TEXT, 1)
        c.text(f"FRAME {index + 1} OF 6", 28, 160, C.MUTED, 1)
        c.text("8 MHz THEN 72 MHz", 28, 200, C.GREEN, 1)
        c.text("PRINT THE MISS ON THE STATIC SVG", 28, 222, C.DIM, 1)
        g.add(c)
    return g


def cfsr_read_gif():
    """Read CFSR, see bit 15 set, then let 72 counts finish 1 us.

    A clear bit 15 and a cycle delta of 0 stay on the static SVG.
    """
    g = Gif(W, H, delay=12)
    notes = (
        "READ CFSR",
        "0xE000ED28",
        "bit 15 = 1",
        "COUNT 24",
        "COUNT 72",
        "1 us",
    )
    for index, note in enumerate(notes):
        c = Canvas(W, H)
        chrome(c, "CFSR", "DWT", "AUX GIF  1 us")
        c.panel(16, 48, 448, 28, C.PANEL, C.STROKE)
        c.text("72 MHz", 28, 58, C.MUTED, 1)
        c.text(note, 28, 120, C.TEXT, 1)
        c.text(f"FRAME {index + 1} OF 6", 28, 160, C.MUTED, 1)
        c.text("bit 15 = 1", 28, 200, C.GREEN, 1)
        c.text("72 COUNTS = 1 us", 28, 222, C.CYAN, 1)
        c.text("PRINT THE MISS ON THE STATIC SVG", 28, 248, C.DIM, 1)
        g.add(c)
    return g


def boot0_low():
    """Pin 44 is 0 and the probe sits on pins 34 and 37.

    The high BOOT pin and an optimizer edit stay on the static SVG.
    """
    g = Gif(W, H, delay=12)
    notes = (
        "pin 34 PA13",
        "pin 37 PA14",
        "GROUND",
        "3.3 V",
        "pin 44",
        "BOOT0 = 0",
    )
    for index, note in enumerate(notes):
        c = Canvas(W, H)
        chrome(c, "BOOT0", "SWD", "AUX GIF  TARGET")
        c.panel(16, 48, 448, 28, C.PANEL, C.STROKE)
        c.text("0x08000000", 28, 58, C.MUTED, 1)
        c.text(note, 28, 120, C.TEXT, 1)
        c.text(f"FRAME {index + 1} OF 6", 28, 160, C.MUTED, 1)
        c.text("BOOT0 = 0", 28, 200, C.GREEN, 1)
        c.text("TARGET SEEN", 28, 222, C.CYAN, 1)
        c.text("PRINT THE MISS ON THE STATIC SVG", 28, 248, C.DIM, 1)
        g.add(c)
    return g


def one_slot():
    """Fill 16 KB, 2 KB, and one 0xB800 image up to 0x08010000.

    The second image and the oversized SRAM array stay on the static SVG.
    """
    g = Gif(W, H, delay=12)
    notes = (
        "16 KB",
        "0x08004000",
        "2 KB",
        "0x08004800",
        "0xB800",
        "0x08010000",
    )
    for index, note in enumerate(notes):
        c = Canvas(W, H)
        chrome(c, "ONE SLOT", "64 KB", "AUX GIF  APP")
        c.panel(16, 48, 448, 28, C.PANEL, C.STROKE)
        c.text("ONE APP", 28, 58, C.MUTED, 1)
        c.text(note, 28, 120, C.TEXT, 1)
        c.text(f"FRAME {index + 1} OF 6", 28, 160, C.MUTED, 1)
        c.text("16 KB + 2 KB + 0xB800", 28, 200, C.GREEN, 1)
        c.text("ENDS AT 0x08010000", 28, 222, C.CYAN, 1)
        c.text("PRINT THE MISS ON THE STATIC SVG", 28, 248, C.DIM, 1)
        g.add(c)
    return g
```

`BUILDERS` 字典在 `"rtos-tick": rtos_tick,` 之后追加，不要改前面二十个键：

```python
    "stop-wake": stop_wake_gif,
    "cfsr-read": cfsr_read_gif,
    "boot0-low": boot0_low,
    "one-slot": one_slot,
```

只生成这四条，避免重写已有 20 条 GIF 的字节：

Run: `python3 tools/gen_gifs.py stop-wake cfsr-read boot0-low one-slot`

Expected: 退出码 0。四条都少于 500 KB，帧数是 6。不要运行不带参数的 `python3 tools/gen_gifs.py`，那会把已有 20 条也重写一遍。

第五节表的末尾追加：

```text
| `stop-wake.gif` | 从 Stop 醒来，时钟从 HSI 8 MHz 装回 72 MHz，然后标出 115200 | 由 `tools/gen_gifs.py` 生成。辅图。12800 和 24 µA 只在静态主图上 |
| `cfsr-read.gif` | 读 CFSR，bit 15 为 1，然后 72 个计数走完 1 µs | 由 `tools/gen_gifs.py` 生成。辅图。bit 15 为 0 和周期差为 0 只在静态主图上 |
| `boot0-low.gif` | 第 44 脚为 0，探针接在第 34 脚和第 37 脚，目标出现 | 由 `tools/gen_gifs.py` 生成。辅图。BOOT0 为 1 和先改优化等级只在静态主图上 |
| `one-slot.gif` | 16 KB、2 KB 和一张 0xB800 依次填到 0x08010000 为止 | 由 `tools/gen_gifs.py` 生成。辅图。第二张 APP 和 65536 字节只在静态主图上 |
```

把「上面 20 张 GIF」改成「上面 24 张 GIF」。把「不是上面 20 张的中文翻译」改成「不是上面 24 张的中文翻译」。`同目录还有 20 个 *-zh.gif` 这句不动，那 20 个不是这四条新 GIF。

- [ ] **Step 4: 运行测试并提交**

Run: `python3 stm32-book/tests/test_batch6_chapters.py Batch6GifTests -v`

Expected: OK。

```bash
git add tools/gen_gifs.py assets/gif/stop-wake.gif assets/gif/cfsr-read.gif assets/gif/boot0-low.gif assets/gif/one-slot.gif assets/README.md stm32-book/tests/test_batch6_chapters.py
git commit -m "fig: 为第 16、17、18、19 章加上短 GIF 辅图"
```

不要把已有 20 条 GIF 的字节 diff 提交进来。

### Task 5: Thicken chapter 16 in both languages

**Files:**
- Modify: `docs/16-低功耗设计.md`
- Modify: `docs/en/16-low-power.md`
- Modify: `stm32-book/manifest.json` 与 `stm32-book/manifest-en.json`（只追加 `ds5319-pwr` 和 `rm0008-pwr`，并改第 16 章罗盘。不改已有 id）
- Modify: `stm32-book/tests/test_batch6_chapters.py`
- Test: `stm32-book/tests/test_batch6_chapters.py`

**Interfaces:**
- Consumes: `stop_wake()` 已写出 `assets/diagrams/sample-16-stop-wake.svg`。`stop_wake_gif()` 已写出 `assets/gif/stop-wake.gif`。Task 1 的锁定文件。Task 2 的 `ds5319-pwr` 与 `rm0008-pwr` 清单条目。已有 id `rm0008-rcc`、`rm0008-usart`、`ds5319-adc`、`project-examples`、`rm0008-rtc`、`rm0008-wdg` 只被引用，对象不改。
- Produces: 中英第 16 章各一套四块。罗盘 `sources` 成为下面测试里的 `compass`。manifest 末尾是 `ds5319-pwr` 然后 `rm0008-pwr`。视频块与锁定文件 `baseline` 上的字节相同。`baseline_chapter(rev: str, path: str) -> str`、`_fetch_baseline(rev: str) -> None`、`_git_show(rev: str, path: str) -> str | None`。后面的任务调用 `baseline_chapter`，不要再贴这三份函数，也不要改回裸的 `git show`。

学习目标锚点：中文 `## 📌 学习目标`，英文 `## 📌 Learning goals`。四块插在 `<!-- /video:ch16 -->` 之后、这个锚点之前。不要改锚点文字。

浅克隆说明：Book CI 的 checkout 深度是 1。锁定文件里的 `baseline` 往往不是这个浅克隆的尖端。`git show <baseline>:<路径>` 会失败，除非先把那个 SHA 取回来。做法与 `stm32-book/tests/test_batch5_chapters.py` 的 `_fetch_baseline` 相同。不要改 `.github/workflows/book.yml` 的 `fetch-depth`。

- [ ] **Step 1: 把基线取回函数和章节断言加进测试**

在 `test_batch6_chapters.py` 顶部补上 `import json`、`import os`、`import subprocess`。在 `ROOT = ...` 之后插入：

```python
def _fetch_baseline(rev: str) -> None:
    """Shallow CI checkouts do not contain the lock baseline. Match batch 5.

    actions/checkout on Book CI uses the default depth of 1. A regression that
    runs ``git show <lock baseline>:<path>`` cannot see that commit until this
    function fetches it. Do not widen the workflow checkout instead.
    """
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
    base = os.environ.get("GITHUB_BASE_REF", "main")
    commands = (
        ["git", "-C", str(ROOT), "fetch", "--depth=1", "origin", rev],
        [
            "git", "-C", str(ROOT), "fetch", "--depth=50", "origin",
            f"+refs/heads/{base}:refs/remotes/origin/{base}",
        ],
    )
    errors: list[str] = []
    for command in commands:
        if _git_show(rev, "stm32-book/manifest.json") is not None:
            return
        got = subprocess.run(command, capture_output=True, text=True, env=env)
        if got.returncode != 0:
            errors.append((got.stderr or got.stdout or command[-1]).strip())
    if _git_show(rev, "stm32-book/manifest.json") is None and errors:
        raise AssertionError("; ".join(errors))


def _git_show(rev: str, path: str) -> str | None:
    got = subprocess.run(
        ["git", "-C", str(ROOT), "show", f"{rev}:{path}"],
        capture_output=True,
    )
    if got.returncode != 0:
        return None
    return got.stdout.decode("utf-8")


def baseline_chapter(rev: str, path: str) -> str:
    blob = _git_show(rev, path)
    if blob is None:
        _fetch_baseline(rev)
        blob = _git_show(rev, path)
    if blob is None:
        raise AssertionError(
            f"batch-6 baseline {rev}:{path} is not in this checkout and could not be fetched"
        )
    return blob
```

在 `Batch6GifTests` 之后、`if __name__` 之前追加：

```python
class Batch6StopChapterTests(unittest.TestCase):
    def test_stop_chapters_have_four_blocks_and_the_same_numbers(self) -> None:
        zh_path = ROOT / "docs" / "16-低功耗设计.md"
        en_path = ROOT / "docs" / "en" / "16-low-power.md"
        zh = zh_path.read_text(encoding="utf-8")
        en = en_path.read_text(encoding="utf-8")
        for heading in ("## 原理与边界", "## 关键插图", "## 时序或状态", "## 坑与出处卡"):
            self.assertEqual(1, zh.count(heading))
        for heading in (
            "## Principle and boundary",
            "## Key figures",
            "## Timing or state",
            "## Pitfalls and source cards",
        ):
            self.assertEqual(1, en.count(heading))
        self.assertNotIn("## ⚠️ 常见坑与排查", zh)
        self.assertNotIn("## ⚠️ Pitfalls and troubleshooting", en)
        self.assertIn("## 📌 学习目标", zh)
        self.assertIn("## 📌 Learning goals", en)
        self.assertIn("## 🧠 核心原理", zh)
        self.assertIn("## 🧠 Core ideas", en)
        self.assertNotIn("HAL_RTCEx_SetWakeUpTimer_IT", zh)
        self.assertNotIn("HAL_RTCEx_SetWakeUpTimer_IT", en)
        self.assertNotIn("每秒唤醒一次", zh)
        self.assertNotIn("once a second", en)
        self.assertNotIn("14~20", zh)
        self.assertNotIn("14 to 20", en)
        self.assertNotIn("8/16", zh)
        self.assertNotIn("8 or 16 MHz", en)
        zh_blocks = zh.split("## 原理与边界", 1)[1].split("## 📌 学习目标", 1)[0]
        en_blocks = en.split("## Principle and boundary", 1)[1].split("## 📌 Learning goals", 1)[0]
        for blocks in (zh_blocks, en_blocks):
            for token in (
                "14 µA",
                "24 µA",
                "3.4 µA",
                "3.2 µA",
                "2 µA",
                "1.4 µA",
                "14.4 mA",
                "5.5 mA",
                "5.4 µs",
                "3.6 µs",
                "1.8 µs",
                "50 µs",
                "8 MHz",
                "72 MHz",
                "0x271",
                "12800",
                "115200",
                "1 ms",
                "PA0",
                "#source-ds5319-pwr",
                "#source-rm0008-usart",
                "#source-rm0008-rcc",
                "#source-project-examples",
                "#source-rm0008-rtc",
                "#source-rm0008-wdg",
                "#source-ds5319-adc",
            ):
                self.assertIn(token, blocks)
            self.assertNotIn("780", blocks)
            self.assertNotIn("14~20", blocks)
            self.assertNotIn("14 to 20", blocks)
            self.assertNotIn("167 ns", blocks)
            self.assertNotIn("21 µs", blocks)
            self.assertNotIn("17.2%", blocks)
        self.assertIn("第 10 脚", zh_blocks)
        self.assertIn("pin 10", en_blocks)
        self.assertIn("../assets/diagrams/sample-16-stop-wake.svg", zh)
        self.assertIn("../../assets/diagrams/sample-16-stop-wake.svg", en)
        self.assertIn("../assets/gif/stop-wake.gif", zh)
        self.assertIn("../../assets/gif/stop-wake.gif", en)
        zh_key = zh.split("## 关键插图", 1)[1].split("## 时序或状态", 1)[0]
        en_key = en.split("## Key figures", 1)[1].split("## Timing or state", 1)[0]
        self.assertLess(zh_key.index("sample-16-stop-wake.svg"), zh_key.index("stop-wake.gif"))
        self.assertLess(en_key.index("sample-16-stop-wake.svg"), en_key.index("stop-wake.gif"))
        self.assertIn("自绘", zh_key)
        self.assertIn("Drawn for this book", en_key)
        self.assertNotIn("示意图", zh_key)
        self.assertNotIn("schematic", en_key.lower())
        self.assertIn("lowpower-wakeup.svg", zh_key)
        lock = json.loads(
            (ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch6-16-17-18-19-lock.json").read_text(
                encoding="utf-8"
            )
        )
        for path in (zh_path, en_path):
            rel = path.relative_to(ROOT).as_posix()
            baseline = baseline_chapter(lock["baseline"], rel)
            now_video = zh if path == zh_path else en
            marker = "<!-- video:ch16 -->"
            end = "<!-- /video:ch16 -->"
            self.assertEqual(
                baseline.split(marker, 1)[1].split(end, 1)[0],
                now_video.split(marker, 1)[1].split(end, 1)[0],
            )
        listed = json.loads(
            (ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch6-16-17-18-19-source-list.json").read_text(
                encoding="utf-8"
            )
        )
        by_id = {item["id"]: item for item in listed["absorb"]}
        scope_zh = (
            "第 16 章的两格微安和唤醒微秒。3.3 V、25°C 下，低功耗稳压器、无独立看门狗是 14 µA，"
            "主稳压器那一格是 24 µA。Standby 按 LSI 和 IWDG 写成 3.4、3.2 或 2 µA。1.4 µA 是备份域。"
            "Sleep 是 14.4 mA 或 5.5 mA。醒来先是 8 MHz 的 HSI。不把 14~20 µA 写成表 16 的格子。"
        )
        scope_en = (
            "Chapter file 16 cells and wake-up times. At 3.3 V and 25°C, Stop with the low-power regulator "
            "and the independent watchdog off is 14 µA. The main-regulator cell is 24 µA. Standby is 3.4, 3.2, "
            "or 2 µA according to LSI and IWDG. 1.4 µA is the backup domain. Sleep is 14.4 mA or 5.5 mA. "
            "Wake-up starts on the 8 MHz HSI. Does not call 14 to 20 µA a Table 16 cell."
        )
        zh_manifest = json.loads((ROOT / "stm32-book" / "manifest.json").read_text(encoding="utf-8"))
        en_manifest = json.loads((ROOT / "stm32-book" / "manifest-en.json").read_text(encoding="utf-8"))
        compass = [
            "rm0008",
            "ds5319",
            "ds5319-pwr",
            "rm0008-pwr",
            "rm0008-rcc",
            "rm0008-usart",
            "ds5319-adc",
            "project-examples",
            "rm0008-rtc",
            "rm0008-wdg",
        ]
        guide = zh_manifest["chapter_guides"]["16-低功耗设计.md"]
        guide_en = en_manifest["chapter_guides"]["16-low-power.md"]
        self.assertEqual(compass, guide["sources"])
        self.assertEqual(compass, guide_en["sources"])
        self.assertEqual(
            "进入与退出 Sleep/Stop/Standby 时，哪些时钟、状态和唤醒源必须显式恢复？",
            guide["question"],
        )
        self.assertIn("14 µA", guide["boundary"])
        self.assertIn("24 µA", guide["boundary"])
        self.assertIn("8 MHz", guide["boundary"])
        self.assertNotIn("14~20", guide["boundary"])
        self.assertIn("14 µA", guide_en["boundary"])
        self.assertNotIn("14 to 20", guide_en["boundary"])
        for source_id, scope_pair in (
            ("ds5319-pwr", (scope_zh, scope_en)),
            (
                "rm0008-pwr",
                (
                    "第 16 章醒来先是 HSI，串口之前要重配时钟。PDDS=0 且 SLEEPDEEP=1 是 Stop。PDDS=1 且 SLEEPDEEP=1 是 Standby。不把 F4 的周期唤醒定时器写进来。",
                    "Chapter file 16 returns to HSI and must restore the clock before the next byte. PDDS=0 with SLEEPDEEP=1 is Stop. PDDS=1 with SLEEPDEEP=1 is Standby. Does not include the F4 periodic wake-up timer.",
                ),
            ),
        ):
            card_zh = zh_manifest["sources"][source_id]
            card_en = en_manifest["sources"][source_id]
            for key in ("url", "snapshot", "license"):
                self.assertEqual(by_id[source_id][key], card_zh[key])
                self.assertEqual(card_zh[key], card_en[key])
            self.assertEqual("2026-10-25", card_zh["accessed"])
            self.assertEqual(card_zh["accessed"], card_en["accessed"])
            self.assertEqual(by_id[source_id]["title_zh"], card_zh["title"])
            self.assertEqual(by_id[source_id]["title_en"], card_en["title"])
            self.assertEqual(by_id[source_id]["authority_zh"], card_zh["authority"])
            self.assertEqual(by_id[source_id]["authority_en"], card_en["authority"])
            self.assertEqual(scope_pair[0], card_zh["scope"])
            self.assertEqual(scope_pair[1], card_en["scope"])
        self.assertEqual(["ds5319-pwr", "rm0008-pwr"], list(zh_manifest["sources"])[-2:])
        self.assertEqual(["ds5319-pwr", "rm0008-pwr"], list(en_manifest["sources"])[-2:])
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `python3 stm32-book/tests/test_batch6_chapters.py Batch6StopChapterTests -v`

Expected: FAIL，中文稿还没有 `## 原理与边界`。

- [ ] **Step 3: 改正和表 16 冲突的格子，并删掉旧坑表**

中文 `docs/16-低功耗设计.md` 只改下面这几处，不要动 `<!-- video:ch16 -->` 到 `<!-- /video:ch16 -->` 之间的字节。

把电流行

```markdown
| 典型电流（F1 @3.3 V） | 约 10~20 mA（仅内核停） | 约 14~20 µA | 约 2~3 µA |
```

换成

```markdown
| 典型电流（F1 @3.3 V、25°C） | 外设全开 14.4 mA；外设全关 5.5 mA | 低功耗稳压器 14 µA；主稳压器 24 µA。两格都要求无独立看门狗 | LSI、IWDG、LSE、RTC 都关是 2 µA；LSI 开是 3.2 µA；LSI 和 IWDG 都开是 3.4 µA。1.4 µA 是备份域 |
```

把唤醒时间行

```markdown
| 唤醒时间 | 立即 | 约几十 µs（需重配时钟） | 约几百 µs ~ ms（相当于复位） |
```

换成

```markdown
| 唤醒时间 | 1.8 µs，沿用睡前的时钟 | 低功耗稳压器 5.4 µs，主稳压器 3.6 µs，时钟是 8 MHz HSI；不含把 PLL 装回 72 MHz | 50 µs 到第一条指令，然后从复位向量重启 |
```

把

```markdown
**结论**：进入 Stop 后 HSE/PLL 被关闭，**唤醒后系统时钟自动切回 HSI**（约 8/16 MHz），必须重新调用时钟配置函数，否则串口波特率、定时器频率全错。
```

换成

```markdown
**结论**：进入 Stop 后 HSE/PLL 被关闭，**唤醒后系统时钟是 HSI 8 MHz**，不是 16 MHz。必须重新调用 `SystemClock_Config()`。BRR 若仍是 `0x271`，线上是 12800 bit/s，不是 115200。
```

把

```markdown
> 例：节点每 60 s 唤醒 100 ms 采集（活跃 20 mA），其余 Stop（20 µA）：
```

换成

```markdown
> 例：下面两个电流都是假设，不是表 16 或表 18 的格子。节点每 60 s 唤醒 100 ms 采集（活跃按 20 mA 假设），其余按 20 µA 假设：
```

780 天那一行留在核心原理，不搬进四块，也不改算成另一套天数。0.33 mA 那一行留在核心原理。

把

```c
    HAL_SuspendTick();                    /* 关 SysTick，否则它每秒唤醒一次 */
```

换成

```c
    HAL_SuspendTick();                    /* Sleep 里节拍若是 1000 Hz，就是每 1 ms，不是每 1 s */
```

删掉从 `**④ RTC 周期唤醒（配合 Stop 定时唤醒）**` 到 `**⑤ 降低 GPIO 漏电**` 之前的整段，含 `HAL_RTCEx_SetWakeUpTimer_IT` 和它的回调。换成：

```markdown
**④ 定时叫醒**

STM32F103C8T6 没有 F4 的周期唤醒定时器。不要调用那只 API。定时叫醒走第 11 章：32.768 kHz，PRL = 32767。
```

删掉从 `## ⚠️ 常见坑与排查` 到 `## 🧪 动手实验` 之前的整节，含表格。不要留空标题。`## 🧪 动手实验` 仍在。

英文 `docs/en/16-low-power.md` 做对应的替换。视频块同样不动。

把

```markdown
| Typical current (F1 at 3.3 V) | About 10 to 20 mA (only the core is stopped) | About 14 to 20 µA | About 2 to 3 µA |
```

换成

```markdown
| Typical current (F1 at 3.3 V, 25°C) | Peripherals on: 14.4 mA. Peripherals off: 5.5 mA | Low-power regulator: 14 µA. Main regulator: 24 µA. Both cells require the independent watchdog off | 2 µA only when LSI, IWDG, LSE, and RTC are all off. LSI on is 3.2 µA. LSI and IWDG on is 3.4 µA. 1.4 µA is the backup domain |
```

把

```markdown
| Wake time | Immediate | About a few tens of µs (you must reconfigure the clock) | About a few hundred µs to ms (equivalent to a reset) |
```

换成

```markdown
| Wake time | 1.8 µs, on the clock that was already running | Low-power regulator 5.4 µs, main regulator 3.6 µs, on the 8 MHz HSI. This does not include restoring the PLL to 72 MHz | 50 µs to the first instruction, then a restart from the reset vector |
```

把

```markdown
**Conclusion**: Entering Stop turns HSE and the PLL off. **After wake, the system clock automatically falls back to HSI** (about 8 or 16 MHz). You must call the clock-configuration function again, or the UART baud rate and the timer frequency are all wrong.
```

换成

```markdown
**Conclusion**: Entering Stop turns HSE and the PLL off. **After wake, the system clock is the 8 MHz HSI**, not 16 MHz. Call `SystemClock_Config()` again. If BRR is still `0x271`, the line is 12800 bit/s, not 115200.
```

把

```markdown
> Example: a node wakes for 100 ms every 60 s to sample (20 mA while active) and spends the rest in Stop (20 µA):
```

换成

```markdown
> Example: both currents below are assumptions, not Table 16 or Table 18 cells. A node wakes for 100 ms every 60 s to sample (assume 20 mA while active) and spends the rest at an assumed 20 µA:
```

780 天那一行留在核心原理，不改算。

把

```c
    HAL_SuspendTick();                    /* turn off SysTick, otherwise it wakes the core once a second */
```

换成

```c
    HAL_SuspendTick();                    /* In Sleep a 1000 Hz tick wakes the core every 1 ms, not once a second */
```

删掉从 `**④ RTC periodic wake (paired with Stop, so you wake on a schedule)**` 到 `**⑤ Cut GPIO leakage**` 之前的整段，含 `HAL_RTCEx_SetWakeUpTimer_IT` 和它的回调。换成：

```markdown
**④ Timed wake**

STM32F103C8T6 does not have the F4 periodic wake-up timer. Do not call that API. Timed wake is chapter 11: 32.768 kHz, PRL = 32767.
```

删掉从 `## ⚠️ Pitfalls and troubleshooting` 到 `## 🧪 Hands-on labs` 之前的整节。不要留空标题。

- [ ] **Step 4: 在学习目标之前插入四块**

中文插在 `<!-- /video:ch16 -->` 与 `## 📌 学习目标` 之间。英文插在同一对标记与 `## 📌 Learning goals` 之间。视频结束标记那一行保持原样。

中文四块：

```markdown
## 原理与边界

这一章的工作点是 STM32F103C8T6 的 Stop，稳压器在低功耗模式，对应 `PWR_LOWPOWERREGULATOR_ON`。电流整格照抄 DS5319 Rev 20 表 16 在 3.3 V、25°C 的典型值。见 [DS5319 表 16](#source-ds5319-pwr)。

低功耗稳压器、振荡器关、无独立看门狗：14 µA。主稳压器仍开、其余条件相同：24 µA。20 µA 不是表 16 的格子。85°C 的 200 µA 和 180 µA 是最大值，不写成典型值。1.4 µA 是备份域在 LSE 与 RTC 开着时的 `IDD_VBAT`，不是整机 Standby。

Standby 分成三格。2 µA 只属于 LSI、IWDG、LSE、RTC 都关的那一格。LSI 开着是 3.2 µA。LSI 和 IWDG 都开是 3.4 µA。IWDG 在 Stop 和 Standby 里继续计数，这句跟第 11 章同一笔。14 µA 那一格的条件写着无独立看门狗。开着 IWDG 去引用 14 µA，是失败旁注。表 16 没有单独印出「Stop 加 IWDG」的微安，这里不编一个新的微安。见 [RM0008 看门狗](#source-rm0008-wdg)。

Sleep 在 72 MHz、外设全开时典型 14.4 mA，外设全关时典型 5.5 mA，条件仍是 25°C、3.3 V。

Stop 退出后系统时钟是 HSI 8 MHz，不是 16 MHz，也不是 72 MHz。见 [RM0008 时钟](#source-rm0008-rcc)。表 26 的 5.4 µs 是低功耗稳压器那一格，从唤醒事件到第一条用户指令，时钟仍是这只 8 MHz。主稳压器那格是 3.6 µs。Sleep 是 1.8 µs，而且沿用睡前的时钟。Standby 是 50 µs 到第一条指令，然后走复位。PLL 锁定的最大值是 200 µs，不和 5.4 µs 加在一起叫成唤醒时间。

本书时钟树 PPRE2 不分频。在 `SystemClock_Config()` 之前，USART1 的内核时钟是 8 MHz。BRR 若仍是 `0x271`，`8e6 / (16 × 39.0625) = 12800`。主机若还停在 115200，比是 9。正常路径是先把 PLL 装回 72 MHz，再发下一字节，线上仍是 115200。见 [RM0008 USART](#source-rm0008-usart)。不重画第 06 章的帧。

Sleep 沿用睡前的时钟。`examples/freertos-task` 的节拍是 1000 Hz，也就是 1 ms。节拍留在这个频率时，Sleep 每 1 ms 被叫醒。Stop 期间这只 SysTick 不跳。见 [本仓库例程](#source-project-examples)。

`PDDS=1` 时 SRAM 和普通寄存器丢失，醒来从复位向量进。WKUP 是第 10 脚 PA0 的上升沿。下降沿的 EXTI 能唤醒 Stop，不能当成 Standby 的 WKUP。见 [DS5319 第 10 脚](#source-ds5319-adc)。第 03 章的 270 Ω 灯和第 09 章的 ADC12_IN0 是同一只脚的别的用途，不在这一章同时接上。

F4 的周期唤醒定时器在这颗料上作废。定时叫醒交叉引用第 11 章：32.768 kHz，PRL = 32767。见 [RM0008 RTC](#source-rm0008-rtc)。

## 关键插图

<p align="center">
  <img src="../assets/diagrams/sample-16-stop-wake.svg" width="760" alt="低功耗稳压器的 Stop 典型值是 14 µA；醒来先是 HSI 8 MHz；不重配时钟时 0x271 变成 12800 bit/s">
  <br><sub>▲ 自绘。STM32F103C8T6，LQFP48。正常路径是 SLEEPDEEP=1、PDDS=0，14 µA，3.3 V、25°C、无 IWDG，5.4 µs 后第一条指令在 HSI 8 MHz 上，然后 PLL 回到 72 MHz，0x271 仍是 115200。失败路径是同一只 0x271 在 8 MHz 上变成 12800 bit/s。主稳压器那一格是 24 µA。出处是 [DS5319 Rev 20 表 16 和表 26](#source-ds5319-pwr)。</sub>
</p>

<p align="center">
  <img src="../assets/gif/stop-wake.gif" width="640" alt="从 Stop 醒来，时钟从 HSI 8 MHz 装回 72 MHz，然后标出 115200">
  <br><sub>▲ 网页和公众号辅图。只播放正常路径：从 Stop 醒来，时钟从 8 MHz 装回 72 MHz，线上 115200。印刷以静态主图为准。12800 和 24 µA 不在这条 GIF 上。</sub>
</p>

`lowpower-wakeup.svg` 留作辅图。不播放它。14 µA、8 MHz 和 12800 都在静态主图上。

## 时序或状态

| 步骤 | 时钟或电流 | 对错 |
| --- | --- | --- |
| 进入 Stop，低功耗稳压器，无 IWDG | 14 µA，3.3 V，25°C | 正常 |
| 同一模式但主稳压器开着 | 24 µA | 不是 14 µA 那一格 |
| 唤醒，低功耗稳压器 | 5.4 µs 后第一条指令，HSI 8 MHz | 正常 |
| 主稳压器那格的唤醒 | 3.6 µs | 不是 5.4 µs |
| Sleep | 1.8 µs，沿用睡前的时钟 | 正常 |
| 重配 | PLL 回到 72 MHz 之后 USART1 为 115200 | 正常 |
| 没有重配，`0x271` 仍在 | 8 MHz 下是 12800 | 失败 |
| Sleep，72 MHz，外设全开 | 14.4 mA | 正常 |
| Sleep，外设全关 | 5.5 mA | 正常 |
| SysTick 1000 Hz | 每 1 ms 醒一次 | Sleep 里成立，Stop 期间不成立 |
| Standby，`PDDS=1` | 从复位向量重启；到第一条指令 50 µs | 正常 |
| Standby 电流 | 2 µA 只在 LSI、IWDG、LSE、RTC 都关时；LSI 开是 3.2 µA；IWDG 也开是 3.4 µA | 不要写成 2~3 µA |
| 备份域 | 1.4 µA，LSE 与 RTC 开 | 不是整机 Standby |
| 第 10 脚 PA0 | Stop 按键用上升沿的 WKUP，或这一章的 EXTI | 不和灯、ADC 同时画上 |

## 坑与出处卡

| 现象 | 原因 | 处理 | 出处 | 该来源允许支持的主张 |
| --- | --- | --- | --- | --- |
| 手册被说成 Stop 约 14~20 µA | 两格被并成了一个区间 | 低功耗稳压器写 14 µA，主稳压器写 24 µA | [DS5319](#source-ds5319-pwr) | 两格都是 3.3 V、25°C 的典型值，并且无独立看门狗。20 µA 不是表 16 的格子 |
| 待机被说成 2~3 µA | 三格被并成了一个区间 | 按 LSI 和 IWDG 写成 2 µA、3.2 µA 或 3.4 µA | [DS5319](#source-ds5319-pwr) | 2 µA 那一格要求 LSI、IWDG、LSE、RTC 都关。1.4 µA 是备份域，不是整机 |
| 醒来第一帧串口乱码 | 时钟还停在 HSI，BRR 却是按 72 MHz 算的 | 先 `SystemClock_Config()`，再发字节 | [RM0008 USART](#source-rm0008-usart) | HSI 为 8 MHz 且 BRR 仍是 `0x271` 时，波特率是 12800。72 MHz 那一格才是 115200 |
| 注释写 HSI 约 8/16 MHz | 把别的系列的 16 MHz 写进了这颗料 | 这颗料写 8 MHz | [RM0008 时钟](#source-rm0008-rcc) | F1 上电默认的 HSI 是 8 MHz。16 MHz 在 C8 上作废 |
| Sleep 里电流下不来，注释却说每秒醒一次 | 节拍留在 1000 Hz | 那就是每 1 ms，不是每 1 s。进 Sleep 前挂起这只节拍 | [本仓库例程](#source-project-examples) | `examples/freertos-task` 把节拍写成 1000 Hz，1 ms 一个 tick。这一行不证明 Stop 期间 SysTick 还在跳 |
| 调用了 F4 的周期唤醒 API | 这颗料没有那只定时器 | 用第 11 章的 RTC 闹钟 | [RM0008 RTC](#source-rm0008-rtc) | F103 的定时叫醒不是那只 F4 API。PRL = 32767 才是 1 Hz |
| 开着 IWDG 还引用 14 µA | 14 µA 那一格不含独立看门狗 | 不要用 14 µA 去盖住开着的 IWDG | [RM0008 看门狗](#source-rm0008-wdg) | IWDG 在 Stop 和 Standby 里继续计数。不新编「Stop 加 IWDG」的微安 |
| 按键下降沿唤醒了 Stop，Standby 却不醒 | Standby 的 WKUP 是上升沿 | 第 10 脚 PA0 用上升沿 | [DS5319](#source-ds5319-adc) | 第 10 脚是 PA0-WKUP。这一行不把 270 Ω 的灯画成同时有效 |
```

英文四块用同样的事实。图的路径是 `../../assets/diagrams/sample-16-stop-wake.svg` 和 `../../assets/gif/stop-wake.gif`。图注里的「自绘」换成 `Drawn for this book`。替代文本用英文写出同一句结论。四块里不要出现 `780`、`14 to 20`、`167 ns`。

```markdown
## Principle and boundary

The working point is Stop on STM32F103C8T6 with the regulator in low-power mode, which is `PWR_LOWPOWERREGULATOR_ON`. The current cells are the DS5319 Rev 20 Table 16 typicals at 3.3 V and 25°C. See [DS5319 Table 16](#source-ds5319-pwr).

Low-power regulator, oscillators off, independent watchdog off: 14 µA. Main regulator still on, same other conditions: 24 µA. 20 µA is not a Table 16 cell. The 85°C values 200 µA and 180 µA are maximums, not typicals. 1.4 µA is `IDD_VBAT` for the backup domain with LSE and the RTC on. It is not the whole-chip Standby current.

Standby has three cells. 2 µA belongs only to the cell with LSI, IWDG, LSE, and RTC all off. LSI on is 3.2 µA. LSI and IWDG both on is 3.4 µA. The IWDG keeps counting in Stop and Standby, the same sentence as chapter file 11. The 14 µA cell says the independent watchdog is off. Quoting 14 µA while the IWDG is on is the failure note. Table 16 does not print a separate Stop-plus-IWDG microamp, so this chapter does not invent one. See [RM0008 watchdog](#source-rm0008-wdg).

Sleep at 72 MHz is 14.4 mA typical with every peripheral on, and 5.5 mA typical with every peripheral off, still at 25°C and 3.3 V.

After Stop exits, the system clock is the 8 MHz HSI, not 16 MHz and not 72 MHz. See [RM0008 clocks](#source-rm0008-rcc). Table 26's 5.4 µs is the low-power-regulator cell, from the wake event to the first user instruction, still on that 8 MHz clock. The main-regulator cell is 3.6 µs. Sleep is 1.8 µs and keeps the clock from before the sleep. Standby is 50 µs to the first instruction, then the reset path. The PLL lock maximum is 200 µs. Do not add it to 5.4 µs and call the sum the wake-up time.

PPRE2 is not divided on this book's clock tree. Before `SystemClock_Config()`, the USART1 kernel clock is 8 MHz. If BRR is still `0x271`, `8e6 / (16 × 39.0625) = 12800`. A host that is still at 115200 is off by a factor of 9. The normal path restores the PLL to 72 MHz before the next byte, and the line is 115200 again. See [RM0008 USART](#source-rm0008-usart). Do not redraw the chapter 06 frame.

Sleep keeps the clock from before the sleep. The tick in `examples/freertos-task` is 1000 Hz, which is 1 ms. Left at that rate, Sleep wakes every 1 ms. SysTick does not tick during Stop. See [examples in this repo](#source-project-examples).

With `PDDS=1`, SRAM and the ordinary registers are lost, and wake-up enters through the reset vector. WKUP is a rising edge on pin 10 PA0. A falling EXTI can wake Stop. It is not Standby's WKUP. See [DS5319 pin 10](#source-ds5319-adc). The 270 Ω lamp from chapter file 03 and ADC12_IN0 from chapter file 09 are other uses of this pin. This chapter does not connect them at the same time.

The F4 periodic wake-up timer is void on this part. Timed wake is the chapter 11 alarm: 32.768 kHz, PRL = 32767. See [RM0008 RTC](#source-rm0008-rtc).

## Key figures

<p align="center">
  <img src="../../assets/diagrams/sample-16-stop-wake.svg" width="760" alt="Stop with the low-power regulator is 14 µA typical. Wake-up is the 8 MHz HSI. Leaving 0x271 in place produces 12800 bit/s.">
  <br><sub>▲ Drawn for this book. STM32F103C8T6, LQFP48. The normal path is SLEEPDEEP=1, PDDS=0, 14 µA at 3.3 V and 25°C with the IWDG off, the first instruction on the 8 MHz HSI after 5.4 µs, then the PLL back at 72 MHz so 0x271 is 115200 again. The failure path leaves that same 0x271 on 8 MHz and gets 12800 bit/s. The main-regulator cell is 24 µA. Source: [DS5319 Rev 20 Tables 16 and 26](#source-ds5319-pwr).</sub>
</p>

<p align="center">
  <img src="../../assets/gif/stop-wake.gif" width="640" alt="Wake from Stop, move the clock from the 8 MHz HSI back to 72 MHz, then mark 115200">
  <br><sub>▲ Auxiliary figure for the web and for posts. It plays only the normal path: wake from Stop, move from 8 MHz back to 72 MHz, and mark 115200. Print from the static figure. 12800 and 24 µA are not on this GIF.</sub>
</p>

`lowpower-wakeup.svg` stays as an auxiliary figure. Do not play it for 14 µA, 8 MHz, or 12800. Those are on the static figure.

## Timing or state

| Step | Clock or current | Right or wrong |
| --- | --- | --- |
| Enter Stop, low-power regulator, no IWDG | 14 µA at 3.3 V and 25°C | right |
| Same mode with the main regulator on | 24 µA | not the 14 µA cell |
| Wake, low-power regulator | first instruction after 5.4 µs, HSI 8 MHz | right |
| Main-regulator wake | 3.6 µs | not 5.4 µs |
| Sleep | 1.8 µs, on the clock that was already running | right |
| Restore | USART1 is 115200 after the PLL is back at 72 MHz | right |
| No restore, `0x271` still loaded | 12800 at 8 MHz | wrong |
| Sleep, 72 MHz, peripherals on | 14.4 mA | right |
| Sleep, peripherals off | 5.5 mA | right |
| SysTick at 1000 Hz | wakes every 1 ms | true in Sleep, not during Stop |
| Standby, `PDDS=1` | restart from the reset vector; 50 µs to the first instruction | right |
| Standby current | 2 µA only with LSI, IWDG, LSE, and RTC off; LSI on is 3.2 µA; IWDG on as well is 3.4 µA | do not write 2 to 3 µA |
| Backup domain | 1.4 µA with LSE and the RTC on | not whole-chip Standby |
| Pin 10 PA0 | the Stop key uses rising-edge WKUP, or this chapter's EXTI | not drawn as a lamp and an ADC at the same time |

## Pitfalls and source cards

| What you see | Why | What to do | Source | Claim this source may support |
| --- | --- | --- | --- | --- |
| The manual is quoted as Stop about 14 to 20 µA | Two cells were folded into one range | Write 14 µA for the low-power regulator and 24 µA for the main regulator | [DS5319](#source-ds5319-pwr) | Both cells are typicals at 3.3 V and 25°C, with the independent watchdog off. 20 µA is not a Table 16 cell |
| Standby is quoted as 2 to 3 µA | Three cells were folded into one range | Write 2 µA, 3.2 µA, or 3.4 µA according to LSI and IWDG | [DS5319](#source-ds5319-pwr) | The 2 µA cell requires LSI, IWDG, LSE, and RTC all off. 1.4 µA is the backup domain, not the whole chip |
| The first UART frame after wake is garbage | The clock is still HSI while BRR was computed for 72 MHz | Call `SystemClock_Config()` before the next byte | [RM0008 USART](#source-rm0008-usart) | With the HSI at 8 MHz and BRR still `0x271`, the baud rate is 12800. 115200 is the 72 MHz cell |
| A comment says the HSI is about 8 or 16 MHz | Another family's 16 MHz was written onto this part | Write 8 MHz on this part | [RM0008 clocks](#source-rm0008-rcc) | The F1 power-up HSI is 8 MHz. 16 MHz is void on the C8 |
| Sleep current will not fall, and the comment says once a second | The tick was left at 1000 Hz | That is every 1 ms, not once a second. Suspend the tick before Sleep | [examples in this repo](#source-project-examples) | `examples/freertos-task` documents a 1000 Hz tick, 1 ms. This row does not show that SysTick keeps ticking during Stop |
| The F4 periodic wake API was called | This part does not have that timer | Use the chapter 11 RTC alarm | [RM0008 RTC](#source-rm0008-rtc) | Timed wake on the F103 is not that F4 API. PRL = 32767 is 1 Hz |
| 14 µA is quoted while the IWDG is on | That cell excludes the independent watchdog | Do not cover a running IWDG with 14 µA | [RM0008 watchdog](#source-rm0008-wdg) | The IWDG keeps counting in Stop and Standby. Do not invent a Stop-plus-IWDG microamp |
| A falling edge woke Stop, but Standby stays asleep | Standby's WKUP is a rising edge | Use a rising edge on pin 10 PA0 | [DS5319](#source-ds5319-adc) | Pin 10 is PA0-WKUP. This row does not draw the 270 Ω lamp as active at the same time |
```

- [ ] **Step 5: 追加两个来源对象并改罗盘**

`url`、`snapshot`、`license` 从清单里的 `ds5319-pwr` 和 `rm0008-pwr` 原样复制。`title` 用 `title_zh` / `title_en`，`authority` 用 `authority_zh` / `authority_en`。`accessed` 是 `2026-10-25`。`scope` 用本任务测试里的那两对字符串。中文对象按 `ds5319-pwr`、`rm0008-pwr` 的顺序追加在 `stm32-book/manifest.json` 的 `sources` 末尾，英文同样追加。不要改已有 id 的任何字段。

两份 manifest 里第 16 章罗盘的 `sources` 改成测试里的 `compass`。中文键是 `16-低功耗设计.md`。英文键是 `16-low-power.md`。原来的 `rm0008`、`ds5319` 仍在最前。`question` 和 `deliverable` 不改。`boundary` 把「约 14~20 µA」改成 14 µA 与 24 µA 两格，并写明 3.3 V、25°C、无独立看门狗。HSI 8 MHz 那句保留。英文 boundary 同样改掉 `14 to 20`。

中文 boundary 整段换成：

```text
数据手册典型值是芯片在指定条件下的数值，不能直接当成整块开发板功耗。Stop 低功耗稳压器在 3.3 V、25°C、无独立看门狗时典型值是 14 µA；主稳压器仍开的那一格是 24 µA。从 Stop 醒来先回到 HSI；第 02 章写明 F1 上电默认的 HSI 是 8 MHz，72 MHz 的 PLL 要重新装回。
```

英文 boundary 整段换成：

```text
A typical value in the datasheet is the chip under stated conditions. It is not the power of the whole board. Stop with the low-power regulator is 14 µA typical at 3.3 V and 25°C with the independent watchdog off. The regulator-on cell is 24 µA. Wake-up returns to HSI. Chapter 02 puts that HSI at 8 MHz on F1; the 72 MHz PLL has to be programmed again.
```

- [ ] **Step 6: 运行测试并提交**

Run: `python3 stm32-book/tests/test_batch6_chapters.py Batch6StopChapterTests -v`

Expected: OK。

```bash
git add docs/16-低功耗设计.md docs/en/16-low-power.md stm32-book/manifest.json stm32-book/manifest-en.json stm32-book/tests/test_batch6_chapters.py
git commit -m "book: 加厚第 16 章并把 Stop 电流改成表 16 的两格"
```

不要在这一笔里改第 17、18、19 章，也不要升版本号。不要改附录 D，那是 Task 9。

### Task 6: Thicken chapter 17 in both languages

**Files:**
- Modify: `docs/17-调试与性能优化.md`
- Modify: `docs/en/17-debug.md`
- Modify: `stm32-book/manifest.json` 与 `stm32-book/manifest-en.json`（追加 `pm0056-dwt`，并改第 17 章罗盘）
- Modify: `stm32-book/tests/test_batch6_chapters.py`
- Test: `stm32-book/tests/test_batch6_chapters.py`

**Interfaces:**
- Consumes: `cfsr_read()` 与 `cfsr-read.gif`。Task 5 已经把 `rm0008-pwr` 放在 `sources` 末尾。已有 id `pm0056`、`ds5319-swd` 只被引用。Task 5 的 `baseline_chapter()`。不要再定义一遍，也不要改成裸的 `git show`。
- Produces: 中英第 17 章各一套四块。`pm0056-dwt` 接在 `rm0008-pwr` 后面。视频块字节不变。

学习目标锚点：中文 `## 📌 学习目标`，英文 `## 📌 Learning goals`。核心原理保持 `## 🧠 核心原理` 与 `## 🧠 Core ideas`。旧坑标题英文是 `## ⚠️ Pitfalls and troubleshooting`。

- [ ] **Step 1: 把章节断言加进测试**

在 `test_batch6_chapters.py` 末尾、`if __name__` 之前追加。不要再贴 `_fetch_baseline`。

```python
class Batch6CfsrChapterTests(unittest.TestCase):
    def test_cfsr_chapters_have_four_blocks_and_the_same_numbers(self) -> None:
        zh_path = ROOT / "docs" / "17-调试与性能优化.md"
        en_path = ROOT / "docs" / "en" / "17-debug.md"
        zh = zh_path.read_text(encoding="utf-8")
        en = en_path.read_text(encoding="utf-8")
        for heading in ("## 原理与边界", "## 关键插图", "## 时序或状态", "## 坑与出处卡"):
            self.assertEqual(1, zh.count(heading))
        for heading in (
            "## Principle and boundary",
            "## Key figures",
            "## Timing or state",
            "## Pitfalls and source cards",
        ):
            self.assertEqual(1, en.count(heading))
        self.assertNotIn("## ⚠️ 常见坑与排查", zh)
        self.assertNotIn("## ⚠️ Pitfalls and troubleshooting", en)
        self.assertIn("CoreDebug_DEMCR_TRCENA_Msk", zh)
        self.assertIn("CoreDebug_DEMCR_TRCENA_Msk", en)
        zh_blocks = zh.split("## 原理与边界", 1)[1].split("## 📌 学习目标", 1)[0]
        en_blocks = en.split("## Principle and boundary", 1)[1].split("## 📌 Learning goals", 1)[0]
        for blocks in (zh_blocks, en_blocks):
            for token in (
                "0xE000ED28",
                "0xE000ED2C",
                "0xE000ED34",
                "0xE000ED38",
                "0xE000EDFC",
                "0xE0001004",
                "0x40000000",
                "bit 15",
                "bit 24",
                "bit 30",
                "1 µs",
                "PA13",
                "PA14",
                "PB3",
                "JTDO",
                "#source-pm0056",
                "#source-pm0056-dwt",
                "#source-ds5319-swd",
            ):
                self.assertIn(token, blocks)
            self.assertNotIn("167 ns", blocks)
            self.assertNotIn("10+", blocks)
            self.assertNotIn("2~4", blocks)
            self.assertNotIn("-mfpu", blocks)
        self.assertIn("6", zh_blocks)
        self.assertIn("6", en_blocks)
        self.assertIn("../assets/diagrams/sample-17-cfsr.svg", zh)
        self.assertIn("../../assets/diagrams/sample-17-cfsr.svg", en)
        self.assertIn("../assets/gif/cfsr-read.gif", zh)
        self.assertIn("../../assets/gif/cfsr-read.gif", en)
        zh_key = zh.split("## 关键插图", 1)[1].split("## 时序或状态", 1)[0]
        en_key = en.split("## Key figures", 1)[1].split("## Timing or state", 1)[0]
        self.assertLess(zh_key.index("sample-17-cfsr.svg"), zh_key.index("cfsr-read.gif"))
        self.assertLess(en_key.index("sample-17-cfsr.svg"), en_key.index("cfsr-read.gif"))
        self.assertIn("自绘", zh_key)
        self.assertIn("Drawn for this book", en_key)
        self.assertNotIn("示意图", zh_key)
        self.assertIn("debug-swo.svg", zh_key)
        lock = json.loads(
            (ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch6-16-17-18-19-lock.json").read_text(
                encoding="utf-8"
            )
        )
        for path in (zh_path, en_path):
            rel = path.relative_to(ROOT).as_posix()
            baseline = baseline_chapter(lock["baseline"], rel)
            now_video = zh if path == zh_path else en
            marker = "<!-- video:ch17 -->"
            end = "<!-- /video:ch17 -->"
            self.assertEqual(
                baseline.split(marker, 1)[1].split(end, 1)[0],
                now_video.split(marker, 1)[1].split(end, 1)[0],
            )
        listed = json.loads(
            (ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch6-16-17-18-19-source-list.json").read_text(
                encoding="utf-8"
            )
        )
        by_id = {item["id"]: item for item in listed["absorb"]}
        scope_zh = (
            "第 17 章的 DWT 使能顺序和硬件断点个数。先置 DEMCR 0xE000EDFC 的 bit 24，再读 DWT_CYCCNT 0xE0001004。"
            "72 MHz 下 72 个计数是 1 µs。没置 bit 24 时差值为 0。这颗 M3 是 6 个硬件断点。不重写 CFSR 的四个地址。不把 167 ns 写进来。"
        )
        scope_en = (
            "Chapter file 17 DWT enable order and hardware-breakpoint count. Set DEMCR 0xE000EDFC bit 24 before reading "
            "DWT_CYCCNT at 0xE0001004. At 72 MHz, 72 counts are 1 µs. A clear bit 24 reads a delta of 0. This M3 has 6 "
            "hardware breakpoints. Does not restate the four CFSR addresses. Does not include 167 ns."
        )
        zh_manifest = json.loads((ROOT / "stm32-book" / "manifest.json").read_text(encoding="utf-8"))
        en_manifest = json.loads((ROOT / "stm32-book" / "manifest-en.json").read_text(encoding="utf-8"))
        compass = ["pm0056", "pm0056-dwt", "ds5319-swd"]
        self.assertEqual(compass, zh_manifest["chapter_guides"]["17-调试与性能优化.md"]["sources"])
        self.assertEqual(compass, en_manifest["chapter_guides"]["17-debug.md"]["sources"])
        self.assertEqual(
            "面对崩溃或变慢，怎样从可重复现象走到故障寄存器、调用位置和周期证据？",
            zh_manifest["chapter_guides"]["17-调试与性能优化.md"]["question"],
        )
        card_zh = zh_manifest["sources"]["pm0056-dwt"]
        card_en = en_manifest["sources"]["pm0056-dwt"]
        for key in ("url", "snapshot", "license"):
            self.assertEqual(by_id["pm0056-dwt"][key], card_zh[key])
            self.assertEqual(card_zh[key], card_en[key])
        self.assertEqual("2026-10-25", card_zh["accessed"])
        self.assertEqual(scope_zh, card_zh["scope"])
        self.assertEqual(scope_en, card_en["scope"])
        self.assertEqual(by_id["pm0056-dwt"]["title_zh"], card_zh["title"])
        self.assertEqual(by_id["pm0056-dwt"]["title_en"], card_en["title"])
        self.assertEqual(["pm0056-dwt"], list(zh_manifest["sources"])[-1:])
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `python3 stm32-book/tests/test_batch6_chapters.py Batch6CfsrChapterTests -v`

Expected: FAIL，中文稿还没有 `## 原理与边界`。

- [ ] **Step 3: 给「10+ MHz」加上边界句，并删掉旧坑表**

不要动 `<!-- video:ch17 -->` 到 `<!-- /video:ch17 -->` 之间的字节。不要删 `CoreDebug_DEMCR_TRCENA_Msk`。那一行已经是 DEMCR bit 24。

中文在含有 `可达 10+ MHz` 的那张表之后、下一节标题之前加上：

```markdown
「可达 10+ MHz」不是 DS5319 或 PM0056 已经收进出处卡的速率。四块不写这个数。数据观察点的「2~4 个」同样不进四块。
```

英文在含有 `10+ MHz` 的那张表之后加上：

```markdown
"Up to 10+ MHz" is not a rate that DS5319 or PM0056 has taken into a source card. The four sections do not write that number. The "2 to 4" data watchpoints stay out of the four sections too.
```

若英文表里的原文不是 `10+ MHz` 这四个字符，先打开 `docs/en/17-debug.md` 里速度那一格的实际句子，把上面的英文提示改成贴着那一格的说法。四块里仍然不要出现 `10+`。

删掉从 `## ⚠️ 常见坑与排查` 到 `## 🧪 动手实验` 之前的整节。英文删掉从 `## ⚠️ Pitfalls and troubleshooting` 到 `## 🧪 Hands-on labs` 之前的整节。不要留空标题。半主机、ITM 和 `addr2line` 若只出现在被删的表里，把这三句留在核心原理，不进出处卡。`-mfpu=fpv4-sp-d16` 留在核心原理，不进四块。

- [ ] **Step 4: 在学习目标之前插入四块**

中文：

```markdown
## 原理与边界

这一章钉在 STM32F103C8T6 上。它是 Cortex-M3，没有 FPU。故障地址整格照抄罗盘。见 [PM0056](#source-pm0056)。

先看 `CFSR`，它在 `0xE000ED28`。`HFSR` 在 `0xE000ED2C`。`FORCED` 是 bit 30，值 `0x40000000`，表示这次硬故障是从别的故障升级来的，原因在 `CFSR`。`MMFAR` 在 `0xE000ED34`。`BFAR` 在 `0xE000ED38`。

`BFARVALID` 是 `CFSR` bit 15。这一位为 0 时，`BFAR` 里的数不是这次访问的地址。把它当成这次的地址，是失败路径。`MMFAR` 要等它自己的有效标志。这一批没有把那个位号印进 snapshot 之前，四块只对 `BFAR` 写死 bit 15。

异常压栈是 R0、R1、R2、R3、R12、LR、PC、xPSR。PC 在第 6 个字。这跟第 04 章是同一次入栈。四块不写 167 ns，不重画那张入栈图。

先把 `DEMCR` `0xE000EDFC` 的 bit 24 置 1，再把 `DWT_CYCCNT` `0xE0001004` 清零并打开周期计数。72 MHz 下 72 个计数是 1 µs。没置 bit 24 时，前后两次读数的差是 0。见 [PM0056 DWT](#source-pm0056-dwt)。

这颗 M3 的硬件断点是 6 个。M7 的 8 个在 C8 上作废。数据观察点的个数不进这一块。

第 34 脚 PA13 是 SWDIO，第 37 脚 PA14 是 SWCLK。第 39 脚 PB3 复位后是 JTDO。关掉 JTAG、留下 SWD 之后，重映射列里才是 TRACESWO。把 PB3 说成上电就是 SWO，是失败旁注。见 [DS5319](#source-ds5319-swd)。

## 关键插图

<p align="center">
  <img src="../assets/diagrams/sample-17-cfsr.svg" width="760" alt="BFAR 要 bit 15 为 1 才有效；72 MHz 下 72 个周期是 1 µs，而且要先打开 DEMCR bit 24">
  <br><sub>▲ 自绘。正常路径是 CFSR 0xE000ED28 的 bit 15 为 1，BFAR 0xE000ED38 是这次的地址，DEMCR 0xE000EDFC 的 bit 24 已经置 1，72 个计数是 1 µs。失败路径是 bit 15 为 0 仍去读 BFAR，或 bit 24 没置、周期差为 0。HFSR bit 30 的值是 0x40000000。第 39 脚仍标成 JTDO。出处是 [PM0056](#source-pm0056) 和 [PM0056 DWT](#source-pm0056-dwt)。</sub>
</p>

<p align="center">
  <img src="../assets/gif/cfsr-read.gif" width="640" alt="读 CFSR，bit 15 为 1，然后 72 个计数走完 1 µs">
  <br><sub>▲ 网页和公众号辅图。只播放正常路径：读 CFSR，bit 15 为 1，然后 72 个计数走完 1 µs。印刷以静态主图为准。bit 15 为 0 和周期差为 0 不在这条 GIF 上。</sub>
</p>

`debug-swo.svg` 留作辅图。SWO 和 ITM 不进这张静态主图。

## 时序或状态

| 寄存器或计数 | 地址或位 | 什么时候有效 |
| --- | --- | --- |
| `CFSR` | `0xE000ED28` | 先读 |
| `HFSR` bit 30 | `0x40000000` | `FORCED` |
| `MMFAR` | `0xE000ED34` | 等它自己的有效标志。位号没印出之前不编 |
| `BFAR` | `0xE000ED38` | 仅 bit 15 为 1 |
| 失败 | bit 15 为 0 | 地址作废 |
| DWT | 先 `0xE000EDFC` bit 24，再 `0xE0001004` | 72 个计数等于 1 µs |
| 失败 | bit 24 为 0 | 差值为 0 |
| 硬件断点 | 6 个 | 这颗 M3。M7 的 8 个作废 |
| 脚位 | 第 34 脚 PA13，第 37 脚 PA14 | SWD。第 39 脚 PB3 默认 JTDO |

## 坑与出处卡

| 现象 | 原因 | 处理 | 出处 | 该来源允许支持的主张 |
| --- | --- | --- | --- | --- |
| `BFAR` 里有个数，但对不上这次访问 | bit 15 为 0 | 先看 `CFSR` bit 15 | [PM0056](#source-pm0056) | bit 15 为 0 时，`BFAR` 不是这次的地址。`BFAR` 在 `0xE000ED38` |
| 一进 HardFault 就只复位 | 没留下故障寄存器 | 先留下 `CFSR` 和压栈的 PC | [PM0056](#source-pm0056) | `CFSR` 在 `0xE000ED28`。`FORCED` 是 `HFSR` bit 30，值 `0x40000000` |
| DWT 测出来是 0 | 没打开跟踪 | 先置 `DEMCR` bit 24，再开 `CYCCNT` | [PM0056 DWT](#source-pm0056-dwt) | bit 24 未置时周期计数不走。72 MHz 下 72 个计数是 1 µs |
| 断点打到第 7 个就不停 | 比较器用完了 | 这颗 M3 只有 6 个硬件断点 | [PM0056 DWT](#source-pm0056-dwt) | 默认 6 个。M7 的 8 个在 C8 上作废。这一行不规定数据观察点的个数 |
| SWO 没有波形，PB3 却当成已经打开 | 复位后它不是 SWO | 第 39 脚是 JTDO | [DS5319](#source-ds5319-swd) | TRACESWO 在重映射列。它不是 PA13，也不是 PA14 |
| 优化之后断言还在，时序却变了 | 没有同条件的周期数 | 先有 bit 24 和 `CYCCNT` 的对照，再改优化等级 | [PM0056 DWT](#source-pm0056-dwt) | 没有对照，加速不算证据。这一行不引入新的编译器开关 |
```

英文四块用同样的地址和同一组 `#source-`。图路径用 `../../assets/`。图注写 `Drawn for this book`。四块里不要出现 `167 ns`、`10+`、`-mfpu`。英文「bit 15」「bit 24」「bit 30」「1 µs」用这些字符，好让测试在两份里都找得到。

```markdown
## Principle and boundary

This chapter is fixed on STM32F103C8T6. It is a Cortex-M3 and it has no FPU. The fault addresses are the compass cells. See [PM0056](#source-pm0056).

Read `CFSR` first. It is at `0xE000ED28`. `HFSR` is at `0xE000ED2C`. `FORCED` is bit 30, value `0x40000000`: this hard fault was escalated, and the reason is in `CFSR`. `MMFAR` is at `0xE000ED34`. `BFAR` is at `0xE000ED38`.

`BFARVALID` is `CFSR` bit 15. When that bit is 0, the number in `BFAR` is not this access. Treating it as this access is the failure path. `MMFAR` waits for its own valid flag. Until that bit number is printed into a snapshot, the four sections freeze bit 15 only for `BFAR`.

The hardware stack is R0, R1, R2, R3, R12, LR, PC, xPSR. PC is the 6th word. That is the same entry as chapter file 04. The four sections do not write 167 ns and do not redraw that figure.

Set bit 24 of `DEMCR` at `0xE000EDFC` before clearing `DWT_CYCCNT` at `0xE0001004` and enabling the cycle counter. At 72 MHz, 72 counts are 1 µs. If bit 24 is clear, the delta of two reads is 0. See [PM0056 DWT](#source-pm0056-dwt).

This M3 has 6 hardware breakpoints. The M7 count of 8 is void on the C8. A data-watchpoint count does not enter this section.

Pin 34 PA13 is SWDIO. Pin 37 PA14 is SWCLK. Pin 39 PB3 is JTDO after reset. TRACESWO is in the remap column after JTAG is turned off and SWD is kept. Calling PB3 SWO from power-up is the failure note. See [DS5319](#source-ds5319-swd).

## Key figures

<p align="center">
  <img src="../../assets/diagrams/sample-17-cfsr.svg" width="760" alt="BFAR is valid only when bit 15 is 1. At 72 MHz, 72 cycles are 1 µs, and only after DEMCR bit 24 is set.">
  <br><sub>▲ Drawn for this book. The normal path is CFSR at 0xE000ED28 with bit 15 set, BFAR at 0xE000ED38 for this access, DEMCR at 0xE000EDFC with bit 24 set, and 72 counts as 1 µs. The failure path reads BFAR while bit 15 is 0, or leaves bit 24 clear and reads a cycle delta of 0. HFSR bit 30 is 0x40000000. Pin 39 stays labeled JTDO. Sources: [PM0056](#source-pm0056) and [PM0056 DWT](#source-pm0056-dwt).</sub>
</p>

<p align="center">
  <img src="../../assets/gif/cfsr-read.gif" width="640" alt="Read CFSR with bit 15 set, then let 72 counts finish 1 µs">
  <br><sub>▲ Auxiliary figure for the web and for posts. It plays only the normal path: read CFSR, bit 15 is 1, then 72 counts finish 1 µs. Print from the static figure. A clear bit 15 and a cycle delta of 0 are not on this GIF.</sub>
</p>

`debug-swo.svg` stays as an auxiliary figure. SWO and ITM are not on this static figure.

## Timing or state

| Register or count | Address or bit | When it is valid |
| --- | --- | --- |
| `CFSR` | `0xE000ED28` | read this first |
| `HFSR` bit 30 | `0x40000000` | `FORCED` |
| `MMFAR` | `0xE000ED34` | wait for its own valid flag. Do not invent the bit number |
| `BFAR` | `0xE000ED38` | only when bit 15 is 1 |
| Failure | bit 15 is 0 | the address is void |
| DWT | `0xE000EDFC` bit 24, then `0xE0001004` | 72 counts are 1 µs |
| Failure | bit 24 is 0 | the delta is 0 |
| Hardware breakpoints | 6 | this M3. The M7 count of 8 is void |
| Pins | pin 34 PA13, pin 37 PA14 | SWD. Pin 39 PB3 is JTDO by default |

## Pitfalls and source cards

| What you see | Why | What to do | Source | Claim this source may support |
| --- | --- | --- | --- | --- |
| `BFAR` holds a number that is not this access | bit 15 is 0 | Read `CFSR` bit 15 first | [PM0056](#source-pm0056) | When bit 15 is 0, `BFAR` is not this access. `BFAR` is at `0xE000ED38` |
| HardFault is answered by only a reset | The fault registers were not kept | Keep `CFSR` and the stacked PC | [PM0056](#source-pm0056) | `CFSR` is at `0xE000ED28`. `FORCED` is `HFSR` bit 30, value `0x40000000` |
| A DWT measurement reads 0 | Trace was not enabled | Set `DEMCR` bit 24, then enable `CYCCNT` | [PM0056 DWT](#source-pm0056-dwt) | With bit 24 clear the cycle counter does not run. At 72 MHz, 72 counts are 1 µs |
| The 7th breakpoint does not stop | The comparators are used up | This M3 has 6 hardware breakpoints | [PM0056 DWT](#source-pm0056-dwt) | The default is 6. The M7 count of 8 is void on the C8. This row does not set a data-watchpoint count |
| SWO has no waveform, and PB3 was treated as already open | After reset it is not SWO | Pin 39 is JTDO | [DS5319](#source-ds5319-swd) | TRACESWO is in the remap column. It is not PA13 and not PA14 |
| The assert still fires after optimization, but the timing changed | There is no cycle count under the same conditions | Keep bit 24 and `CYCCNT` before changing the optimization level | [PM0056 DWT](#source-pm0056-dwt) | A speedup without that pair is not evidence. This row adds no new compiler switch |
```

- [ ] **Step 5: 追加 `pm0056-dwt` 并改罗盘**

按 Task 5 的同一套字段规则追加 `pm0056-dwt`。`scope` 用本任务测试里的两句。两份罗盘的 `sources` 改成 `["pm0056", "pm0056-dwt", "ds5319-swd"]`。中文键 `17-调试与性能优化.md`，英文键 `17-debug.md`。`question`、`deliverable`、`boundary` 不改。不要改 `pm0056` 和 `ds5319-swd` 的对象。

- [ ] **Step 6: 运行测试并提交**

Run: `python3 stm32-book/tests/test_batch6_chapters.py Batch6CfsrChapterTests -v`

Expected: OK。

```bash
git add docs/17-调试与性能优化.md docs/en/17-debug.md stm32-book/manifest.json stm32-book/manifest-en.json stm32-book/tests/test_batch6_chapters.py
git commit -m "book: 加厚第 17 章并把 BFAR 和 DWT 钉在同一笔账上"
```

不要在这一笔里改第 16、18、19 章，也不要升版本号。

### Task 7: Thicken chapter 18 in both languages

**Files:**
- Modify: `docs/18-常见问题FAQ.md`
- Modify: `docs/en/18-faq.md`
- Modify: `stm32-book/manifest.json` 与 `stm32-book/manifest-en.json`（追加 `ds5319-nrst`、`ds5319-lse`，并改第 18 章罗盘）
- Modify: `stm32-book/tests/test_batch6_chapters.py`
- Test: `stm32-book/tests/test_batch6_chapters.py`

**Interfaces:**
- Consumes: `boot_triage()` 与 `boot0_low()`。Task 6 已经把 `pm0056-dwt` 放在 `sources` 末尾。已有 id `project-examples`、`project-guide`、`pm0056`、`ds5319-swd`、`rm0008-boot`、`rm0008-usart`、`freertos-syscall`、`ds5319-gpio` 只被引用。Task 5 的 `baseline_chapter()`。
- Produces: 中英第 18 章各一套四块。38 条目录还在。`ds5319-nrst` 接在 `pm0056-dwt` 后面，`ds5319-lse` 接在 `ds5319-nrst` 后面。视频块字节不变。没有旧坑标题，也没有新造的核心原理标题。

学习目标锚点：中文 `## 📌 学习目标`，英文 `## 📌 Learning goals`。这一章在 `2e2b1d0d4f2c2fb9aabbadb2b89931ac216bdc53` 上没有 `## ⚠️ 常见坑与排查`，也没有 `## 🧠 核心原理`。不要先造一个再删。38 条仍是 C1–C8、D1–D7、P1–P9、H1–H7、R1–R7。目录标题仍是 `## 一、编译与链接` 到 `## 五、RTOS 与工具链`，英文仍是 `## 1. Build and link` 到 `## 5. RTOS and the toolchain`。

- [ ] **Step 1: 把章节断言加进测试**

在 `test_batch6_chapters.py` 末尾、`if __name__` 之前追加。不要再贴 `_fetch_baseline`。

```python
class Batch6BootChapterTests(unittest.TestCase):
    def test_boot_chapters_keep_38_rows_and_the_same_numbers(self) -> None:
        zh_path = ROOT / "docs" / "18-常见问题FAQ.md"
        en_path = ROOT / "docs" / "en" / "18-faq.md"
        zh = zh_path.read_text(encoding="utf-8")
        en = en_path.read_text(encoding="utf-8")
        for heading in ("## 原理与边界", "## 关键插图", "## 时序或状态", "## 坑与出处卡"):
            self.assertEqual(1, zh.count(heading))
        for heading in (
            "## Principle and boundary",
            "## Key figures",
            "## Timing or state",
            "## Pitfalls and source cards",
        ):
            self.assertEqual(1, en.count(heading))
        self.assertNotIn("## ⚠️ 常见坑与排查", zh)
        self.assertNotIn("## ⚠️ Pitfalls and troubleshooting", en)
        self.assertNotIn("## 🧠 核心原理", zh)
        self.assertNotIn("## 🧠 Core ideas", en)
        self.assertNotIn("90%", zh)
        self.assertNotIn("90%", en)
        self.assertNotIn("220~1", zh)
        self.assertNotIn("220~1", en)
        self.assertNotIn("6 pF 电容", zh)
        self.assertNotIn("6 pF capacitors", en)
        self.assertNotIn("改为 TIMx", zh)
        self.assertNotIn("to a TIMx", en)
        row_ids = [f"{letter}{index}" for letter, count in (("C", 8), ("D", 7), ("P", 9), ("H", 7), ("R", 7)) for index in range(1, count + 1)]
        self.assertEqual(38, len(row_ids))
        for row_id in row_ids:
            self.assertIn(f"**{row_id} ", zh)
            self.assertIn(f"**{row_id} ", en)
        zh_blocks = zh.split("## 原理与边界", 1)[1].split("## 📌 学习目标", 1)[0]
        en_blocks = en.split("## Principle and boundary", 1)[1].split("## 📌 Learning goals", 1)[0]
        for blocks in (zh_blocks, en_blocks):
            for token in (
                "38",
                "PA13",
                "PA14",
                "BOOT0",
                "0x08000000",
                "0x1FFFF000",
                "0x1FFFB000",
                "12800",
                "TIM4",
                "0x50",
                "0.1",
                "270",
                "PC13",
                "#source-ds5319-swd",
                "#source-rm0008-boot",
                "#source-ds5319-nrst",
                "#source-ds5319-lse",
                "#source-rm0008-usart",
                "#source-project-examples",
                "#source-freertos-syscall",
                "#source-ds5319-gpio",
            ):
                self.assertIn(token, blocks)
            self.assertNotIn("90%", blocks)
            self.assertNotIn("220~1", blocks)
            self.assertNotIn("kΩ", blocks)
        self.assertIn("6 pF", zh_blocks)
        self.assertIn("不是必须", zh_blocks)
        self.assertIn("6 pF", en_blocks)
        self.assertIn("not required", en_blocks)
        self.assertIn("bit 15", zh)
        self.assertIn("bit 15", en)
        self.assertIn("../assets/diagrams/sample-18-boot-triage.svg", zh)
        self.assertIn("../../assets/diagrams/sample-18-boot-triage.svg", en)
        self.assertIn("../assets/gif/boot0-low.gif", zh)
        self.assertIn("../../assets/gif/boot0-low.gif", en)
        zh_key = zh.split("## 关键插图", 1)[1].split("## 时序或状态", 1)[0]
        en_key = en.split("## Key figures", 1)[1].split("## Timing or state", 1)[0]
        self.assertLess(zh_key.index("sample-18-boot-triage.svg"), zh_key.index("boot0-low.gif"))
        self.assertLess(en_key.index("sample-18-boot-triage.svg"), en_key.index("boot0-low.gif"))
        self.assertIn("自绘", zh_key)
        self.assertIn("Drawn for this book", en_key)
        self.assertNotIn("示意图", zh_key)
        self.assertIn("toolchain-flow.svg", zh_key)
        lock = json.loads(
            (ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch6-16-17-18-19-lock.json").read_text(
                encoding="utf-8"
            )
        )
        for path in (zh_path, en_path):
            rel = path.relative_to(ROOT).as_posix()
            baseline = baseline_chapter(lock["baseline"], rel)
            now_video = zh if path == zh_path else en
            marker = "<!-- video:ch18 -->"
            end = "<!-- /video:ch18 -->"
            self.assertEqual(
                baseline.split(marker, 1)[1].split(end, 1)[0],
                now_video.split(marker, 1)[1].split(end, 1)[0],
            )
        listed = json.loads(
            (ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch6-16-17-18-19-source-list.json").read_text(
                encoding="utf-8"
            )
        )
        by_id = {item["id"]: item for item in listed["absorb"]}
        scope_nrst_zh = (
            "第 18 章 H4。图 31 的外部复位电容是 0.1 µF。0.1 µF 就是 100 nF。第 7 脚仍交叉引用已有的 SWD 卡片。"
            "没打开表 39 之前，这一条不写上拉的千欧。"
        )
        scope_nrst_en = (
            "Chapter file 18, row H4. Figure 31 puts 0.1 µF on NRST. 0.1 µF is 100 nF. Pin 7 stays the cross-reference "
            "already on the SWD card. This card does not write a pull-up in kilohms until Table 39 is opened."
        )
        scope_lse_zh = (
            "第 18 章 P9。LSE 负载电容在 5 pF 到 15 pF 里按晶振选。6 pF 不是必须值。32.768 kHz、第 3 脚、第 4 脚和 PRL = 32767 仍以第 11 章为准。"
        )
        scope_lse_en = (
            "Chapter file 18, row P9. Choose the LSE load capacitors in the 5 pF to 15 pF range with the crystal. "
            "6 pF is not required. 32.768 kHz, pins 3 and 4, and PRL = 32767 stay with chapter file 11."
        )
        zh_manifest = json.loads((ROOT / "stm32-book" / "manifest.json").read_text(encoding="utf-8"))
        en_manifest = json.loads((ROOT / "stm32-book" / "manifest-en.json").read_text(encoding="utf-8"))
        compass = [
            "project-examples",
            "project-guide",
            "pm0056",
            "pm0056-dwt",
            "ds5319-swd",
            "rm0008-boot",
            "ds5319-nrst",
            "ds5319-lse",
            "rm0008-usart",
            "freertos-syscall",
            "ds5319-gpio",
        ]
        guide = zh_manifest["chapter_guides"]["18-常见问题FAQ.md"]
        guide_en = en_manifest["chapter_guides"]["18-faq.md"]
        self.assertEqual(compass, guide["sources"])
        self.assertEqual(compass, guide_en["sources"])
        self.assertEqual("怎样把‘不工作’拆成可观察、可二分、一次只改一个原因的排错过程？", guide["question"])
        self.assertEqual(
            "How do you split \"it does not work\" into something you can observe, bisect, and change one cause at a time?",
            guide_en["question"],
        )
        self.assertEqual("FAQ 是索引不是补丁库；同一现象可由多个根因造成，必须回到本机证据。", guide["boundary"])
        for source_id, scope_zh, scope_en in (
            ("ds5319-nrst", scope_nrst_zh, scope_nrst_en),
            ("ds5319-lse", scope_lse_zh, scope_lse_en),
        ):
            card_zh = zh_manifest["sources"][source_id]
            card_en = en_manifest["sources"][source_id]
            for key in ("url", "snapshot", "license"):
                self.assertEqual(by_id[source_id][key], card_zh[key])
                self.assertEqual(card_zh[key], card_en[key])
            self.assertEqual("2026-10-25", card_zh["accessed"])
            self.assertEqual(scope_zh, card_zh["scope"])
            self.assertEqual(scope_en, card_en["scope"])
            self.assertEqual(by_id[source_id]["title_zh"], card_zh["title"])
            self.assertEqual(by_id[source_id]["title_en"], card_en["title"])
        self.assertEqual(["ds5319-nrst", "ds5319-lse"], list(zh_manifest["sources"])[-2:])
        self.assertEqual(["ds5319-nrst", "ds5319-lse"], list(en_manifest["sources"])[-2:])
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `python3 stm32-book/tests/test_batch6_chapters.py Batch6BootChapterTests -v`

Expected: FAIL，中文稿还没有 `## 原理与边界`。

- [ ] **Step 3: 改掉和前面各章冲突的格子**

不要动 `<!-- video:ch18 -->` 到 `<!-- /video:ch18 -->` 之间的字节。不要删 38 条里的任何一条。不要新造 `## 🧠 核心原理` 或 `## ⚠️ 常见坑与排查`。I2C 的 4.7 kΩ、W25Q 的 `0xEF 0x40 0x17` 和 Mode 0 留在各自的条里。P5 的全 `0xFF` 可以是片选没拉低，也可以是擦除态。不要把 `0xFF` 写成 JEDEC ID。

中文，把下面这几句整句换成右边的句子。

`**P3 串口乱码**` 那一节的解决句：

```markdown
- **解决**：两端统一波特率；共地；确认 SYSCLK（如 HSE 起振失败会退回 HSI）。
```

换成：

```markdown
- **解决**：两端统一波特率；共地；确认 SYSCLK。HSE 没起来时 SYSCLK 是 HSI 8 MHz，USART1 的 `0x271` 在这只时钟上是 12800，不是 115200。
```

`**D7 程序一进调试就停在 `HardFault_Handler`**` 的解决句：

```markdown
- **解决**：查 `CFSR/BFAR` 与出错 PC（见第 17 章）；核对链接脚本。
```

换成：

```markdown
- **解决**：先看 `CFSR`。`BFAR` 只有 bit 15 为 1 才是这次的地址（见第 17 章）；核对链接脚本。
```

`**P9 RTC 上电归零 / 不走时**` 的解决句：

```markdown
- **解决**：接 32.768 kHz 晶振 + 6 pF 电容 + VBAT 电池。
```

换成：

```markdown
- **解决**：接 32.768 kHz 晶振，负载电容在 5 pF 到 15 pF 里按晶振选，6 pF 不是必须值；VBAT 接电池。第 3 脚和第 4 脚，PRL = 32767，见第 11 章。
```

`**H1 LED 不亮**` 的解决句：

```markdown
- **解决**：核对阳极/阴极；电阻取 220~1 kΩ；大电流用三极管/MOS 驱动。
```

换成：

```markdown
- **解决**：核对阳极/阴极。外接灯用第 03 章的第 10 脚和 270 Ω。第 2 脚 PC13 不能当电流源。大电流用三极管或 MOSFET 驱动。
```

`**H4 复位一直在抖**` 的解决句：

```markdown
- **解决**：NRST 加 100 nF 到地；检查喂狗。
```

换成：

```markdown
- **解决**：按图 31 在第 7 脚 NRST 加 0.1 µF 到地。看门狗只指向第 11 章，不在这里重算 1 秒。
```

`**R1 上 RTOS 后 `HAL_Delay` 卡死**` 的解决句：

```markdown
- **解决**：CubeMX 把 Timebase Source 改为 TIMx。
```

换成：

```markdown
- **解决**：仓库例程把 HAL 时基放在 TIM4，不是笼统的 TIMx。SysTick 留给内核。一个 tick 是 1 ms。
```

`**R2 `configASSERT` 死循环**` 的解决句：

```markdown
- **解决**：中断优先级 ≥ `configMAX_SYSCALL_INTERRUPT_PRIORITY`；检查参数。
```

换成：

```markdown
- **解决**：数值大于等于 5 才能调用 FromISR。`5 << 4 = 0x50`。数值更小的中断不得调用 FromISR。
```

方法节这一句：

```markdown
遇到问题别急着改代码，按下面顺序缩小范围，90% 的问题能在前两步定位。
```

换成：

```markdown
遇到问题别急着改代码，按下面顺序缩小范围。前两步先核对线和最小工程。这个顺序不是测量出来的百分比。
```

英文用下面这些整句替换。英文方法节本来就没有 `90%`，不要为了删百分比而改写那一节。

`**P3 Serial garbage**` 的 Fix：

```markdown
- **Fix**: use the same baud rate on both ends. Share ground. Confirm SYSCLK (if HSE fails to start, the chip falls back to HSI).
```

换成：

```markdown
- **Fix**: use the same baud rate on both ends. Share ground. Confirm SYSCLK. If HSE fails to start, SYSCLK is the 8 MHz HSI, and USART1 with `0x271` is 12800 bit/s, not 115200.
```

`**D7 The program stops in `HardFault_Handler` as soon as you start debugging**` 的 Fix：

```markdown
- **Fix**: read `CFSR`/`BFAR` and the faulting PC (see [chapter 17](17-debug.md)). Check the linker script.
```

换成：

```markdown
- **Fix**: read `CFSR` first. `BFAR` is this access only when bit 15 is 1 (see [chapter 17](17-debug.md)). Check the linker script.
```

`**P9 The RTC resets at power-up, or does not advance**` 的 Fix：

```markdown
- **Fix**: fit a 32.768 kHz crystal, 6 pF capacitors, and a battery on VBAT.
```

换成：

```markdown
- **Fix**: fit a 32.768 kHz crystal and a battery on VBAT. Choose the load capacitors in the 5 pF to 15 pF range with the crystal. 6 pF is not required. Pins 3 and 4, and PRL = 32767, stay with chapter 11.
```

`**H1 The LED stays dark**` 的 Fix：

```markdown
- **Fix**: check anode and cathode. Use a resistor in the 220~1 kΩ range. For a large current, drive the LED with a transistor or a MOSFET.
```

换成：

```markdown
- **Fix**: check anode and cathode. The external lamp is pin 10 and 270 Ω, the same as chapter 3. Pin 2 PC13 cannot source the current. For a large current, drive the LED with a transistor or a MOSFET.
```

`**H4 Reset keeps chattering**` 的 Fix：

```markdown
- **Fix**: put 100 nF from NRST to ground. Check that the watchdog is being fed.
```

换成：

```markdown
- **Fix**: follow Figure 31 and put 0.1 µF from pin 7 NRST to ground. The watchdog points at chapter 11. Do not recompute the 1 second here.
```

`**R1 After you add an RTOS, `HAL_Delay` hangs**` 的 Fix：

```markdown
- **Fix**: in CubeMX, change Timebase Source to a TIMx.
```

换成：

```markdown
- **Fix**: the repository example puts the HAL time base on TIM4, not a generic TIMx. Leave SysTick to the kernel. One tick is 1 ms.
```

`**R2 `configASSERT` spins forever**` 的 Fix：

```markdown
- **Fix**: keep interrupt priority numerically at or above `configMAX_SYSCALL_INTERRUPT_PRIORITY`. Check the arguments.
```

换成：

```markdown
- **Fix**: a FromISR call needs a numeric priority of 5 or a larger number. `5 << 4 = 0x50`. A smaller number must not call FromISR.
```

表 39 的上拉千欧，这一步不要写。只有实施时打开了与 `ds5319-clock` 同一份 DS5319 的表 39，才把印出的典型值补进 `ds5319-nrst` 的 snapshot，并在实施 PR 里写明。没打开之前，H4 和四块只写图 31 的 0.1 µF。

- [ ] **Step 4: 在学习目标之前插入四块**

中文：

```markdown
## 原理与边界

这一章是索引，不是第二套外设教程。订货号仍是 STM32F103C8T6。38 条都留着。C1 到 C8 是 8 条，D1 到 D7 是 7 条，P1 到 P9 是 9 条，H1 到 H7 是 7 条，R1 到 R7 是 7 条。`8 + 7 + 9 + 7 + 7 = 38`。

下载器报没有目标时，先看第 34 脚 PA13 = SWDIO、第 37 脚 PA14 = SWCLK、共地、3.3 V，以及第 7 脚 NRST。图 31 的外部复位电容是 0.1 µF。然后再看代码和优化等级。线还没核对就改 `-O2`，是失败路径。见 [DS5319 SWD](#source-ds5319-swd)。

第 44 脚 BOOT0 = 0 时，从主闪存 `0x08000000` 启动。BOOT1 = 0 且 BOOT0 = 1 时，进系统存储器 `0x1FFFF000`。互联型的 `0x1FFFB000` 在这颗 C8 上作废。锁存在复位后 SYSCLK 的第 4 个上升沿，跟第 00 章同一笔。第 35 脚是 VSS_2，不是 SWCLK。那张旧图在第 01 章，这里不重画。见 [RM0008 启动](#source-rm0008-boot)。

闪存 64 KB，SRAM 20 KB，跟已有的 SWD 卡片同一笔。HSE 没起来时 SYSCLK 是 HSI 8 MHz。USART1 的 `0x271` 在这只时钟上是 12800，不是 115200。这句和第 16 章同一笔，这一章不另画位帧。见 [RM0008 USART](#source-rm0008-usart)。

LSE 仍是 32.768 kHz，第 3 脚和第 4 脚，第 1 脚 VBAT，PRL = 32767。电容按 5 pF 到 15 pF 的范围跟晶振一起选。6 pF 不是必须值。见 [DS5319 LSE](#source-ds5319-lse)。

仓库例程把 HAL 时基放在 TIM4，不是笼统的 TIMx。SysTick 留给内核。一个 tick 是 1 ms。见 [本仓库例程](#source-project-examples)。数值大于等于 5 才能调用 FromISR。`5 << 4 = 0x50`。跟第 15 章同一笔，不重画那张优先级图。见 [FreeRTOS](#source-freertos-syscall)。

外接灯跟第 03 章：第 10 脚、270 Ω。第 2 脚 PC13 不拿来源出电流。见 [DS5319 GPIO](#source-ds5319-gpio)。

## 关键插图

<p align="center">
  <img src="../assets/diagrams/sample-18-boot-triage.svg" width="760" alt="认不出芯片时先看第 34 脚、第 37 脚和第 44 脚。BOOT0 为 1 且 BOOT1 为 0 时跑的是 0x1FFFF000">
  <br><sub>▲ 自绘。正常路径是第 44 脚 BOOT0 = 0，从 0x08000000 启动，探针接在第 34 脚 PA13 和第 37 脚 PA14。第 7 脚 NRST 上是图 31 的 0.1 µF。失败路径是 BOOT0 = 1 且 BOOT1 = 0，CPU 在 0x1FFFF000；或者还没看这四只脚就改优化等级。第 35 脚是 VSS_2，指向第 01 章。出处是 [DS5319](#source-ds5319-swd) 图 31 和表 5，以及 [RM0008 启动](#source-rm0008-boot)。</sub>
</p>

<p align="center">
  <img src="../assets/gif/boot0-low.gif" width="640" alt="第 44 脚为 0，探针接在第 34 脚和第 37 脚，目标出现">
  <br><sub>▲ 网页和公众号辅图。只播放正常路径：第 44 脚为 0，探针接在第 34 脚和第 37 脚，目标出现。印刷以静态主图为准。BOOT0 为 1 和「先改优化等级」不在这条 GIF 上。</sub>
</p>

`toolchain-flow.svg` 留作辅图。编译箭头不进这张静态主图。

## 时序或状态

| 先看什么 | 值 | 下一步 |
| --- | --- | --- |
| 第 34 脚和第 37 脚 | PA13 = SWDIO，PA14 = SWCLK，共地，3.3 V | 还没接好就不要改代码 |
| NRST | 第 7 脚，0.1 µF | 图 31。这一行不写上拉的千欧 |
| BOOT | BOOT0 = 0，主闪存 `0x08000000` | 正常路径 |
| 失败 | BOOT0 = 1 且 BOOT1 = 0，`0x1FFFF000` | 用户程序看起来像没烧进去。`0x1FFFB000` 在 C8 上作废 |
| 优化 | 线还没核对就改 `-O2` | 失败 |
| 容量 | 闪存 64 KB，SRAM 20 KB | 跟 SWD 卡片同一笔 |
| 串口 | HSI 8 MHz 且 `0x271` 仍在 | 12800 |
| 时基 | TIM4，1 ms | 不是笼统的 TIMx |
| 优先级 | 数值大于等于 5 | `5 << 4 = 0x50` |
| 晶振 | 5 pF 到 15 pF，按晶振选 | 6 pF 不是必须值 |

## 坑与出处卡

| 现象 | 原因 | 处理 | 出处 | 该来源允许支持的主张 |
| --- | --- | --- | --- | --- |
| 下载器报没有目标 | 线还没核对 | 先看第 34 脚、第 37 脚、地和 3.3 V | [DS5319 SWD](#source-ds5319-swd) | 第 34 脚 PA13 是 SWDIO，第 37 脚 PA14 是 SWCLK。第 35 脚是 VSS_2 |
| 程序像没烧进去 | 第 44 脚被拉高 | 把 BOOT0 放回 0 | [RM0008 启动](#source-rm0008-boot) | BOOT1=0 且 BOOT0=1 时进 `0x1FFFF000`。C8 不是互联型 |
| 复位脚空着，板子自己在复位 | 电容不在图 31 那一格 | 按图 31 加 0.1 µF | [DS5319 NRST](#source-ds5319-nrst) | 图 31 的外部复位电路是 0.1 µF。这一行不新写上拉的千欧 |
| 链接说 Flash 或 RAM 不够 | 按更大的料在估 | 先按 C8 的 64 KB 和 20 KB | [DS5319 SWD](#source-ds5319-swd) | xB 的 128 KB 在 C8T6 上作废 |
| 串口乱码，时钟却没核对 | 掉回了 HSI | 确认没有停在 8 MHz | [RM0008 USART](#source-rm0008-usart) | `0x271` 在 72 MHz 下是 115200，在 8 MHz 下是 12800 |
| 按 P9 焊了 6 pF | 把一只电容当成必须值 | 电容按晶振在 5 pF 到 15 pF 里选 | [DS5319 LSE](#source-ds5319-lse) | 6 pF 不是 LSE 节印出的必须值。32.768 kHz 和 PRL = 32767 仍以第 11 章为准 |
| 上了 FreeRTOS 之后 `HAL_Delay` 不返回 | 时基还在 SysTick | 时基改到 TIM4 | [本仓库例程](#source-project-examples) | `examples/freertos-task` 的时基是 TIM4。不写成笼统的 TIMx |
| 一进中断就停在 `configASSERT` | 数值优先级太靠前 | 写成 5 或更靠后的数 | [FreeRTOS](#source-freertos-syscall) | `5 << 4 = 0x50`。数值更小的中断不得调用 FromISR |
| 外接灯不亮，电阻却在一个区间里乱试 | 脚和电阻都没钉住 | 外接灯用第 03 章的第 10 脚和 270 Ω | [DS5319 GPIO](#source-ds5319-gpio) | 第 2 脚 PC13 不能当电流源。这一行不新造一只电阻 |
```

英文四块用同样的脚号、地址和同一组 `#source-`。图路径用 `../../assets/`。图注写 `Drawn for this book`。四块里不要出现 `90%`、`220~1` 和上拉的 `kΩ`。`6 pF` 只作为「不是必须值」出现。

```markdown
## Principle and boundary

This chapter is an index, not a second peripheral tutorial. The orderable part is still STM32F103C8T6. All 38 rows stay. C1 through C8 is 8, D1 through D7 is 7, P1 through P9 is 9, H1 through H7 is 7, and R1 through R7 is 7. `8 + 7 + 9 + 7 + 7 = 38`.

When the probe reports no target, look first at pin 34 PA13 = SWDIO, pin 37 PA14 = SWCLK, a shared ground, 3.3 V, and pin 7 NRST. Figure 31's external reset capacitor is 0.1 µF. Then look at the code and the optimization level. Editing `-O2` before those wires are checked is the failure path. See [DS5319 SWD](#source-ds5319-swd).

Pin 44 BOOT0 = 0 starts from main Flash at `0x08000000`. BOOT1 = 0 and BOOT0 = 1 enters system memory at `0x1FFFF000`. The connectivity-line address `0x1FFFB000` is void on this C8. The pins are latched on the 4th SYSCLK rising edge after reset, the same note as chapter file 00. Pin 35 is VSS_2, not SWCLK. That old drawing is in chapter file 01, and this chapter does not redraw it. See [RM0008 boot](#source-rm0008-boot).

Flash is 64 KB and SRAM is 20 KB, the same cells as the existing SWD card. When HSE does not start, SYSCLK is the 8 MHz HSI. USART1 with `0x271` on that clock is 12800, not 115200. That is the same sentence as chapter file 16. This chapter does not draw another bit frame. See [RM0008 USART](#source-rm0008-usart).

LSE stays 32.768 kHz, pins 3 and 4, pin 1 VBAT, and PRL = 32767. Choose the capacitors in the 5 pF to 15 pF range with the crystal. 6 pF is not required. See [DS5319 LSE](#source-ds5319-lse).

The repository example puts the HAL time base on TIM4, not a generic TIMx. Leave SysTick to the kernel. One tick is 1 ms. See [repository examples](#source-project-examples). A FromISR call needs a numeric priority of 5 or a larger number. `5 << 4 = 0x50`. That is the same sentence as chapter file 15. Do not redraw that priority figure. See [FreeRTOS](#source-freertos-syscall).

The external lamp matches chapter file 03: pin 10 and 270 Ω. Pin 2 PC13 is not a current source. See [DS5319 GPIO](#source-ds5319-gpio).

## Key figures

<p align="center">
  <img src="../../assets/diagrams/sample-18-boot-triage.svg" width="760" alt="When the probe cannot see the chip, look at pins 34, 37, and 44 first. BOOT0 = 1 and BOOT1 = 0 runs from 0x1FFFF000.">
  <br><sub>▲ Drawn for this book. The normal path is pin 44 BOOT0 = 0, starting at 0x08000000, with the probe on pin 34 PA13 and pin 37 PA14. Pin 7 NRST carries the 0.1 µF from Figure 31. The failure path is BOOT0 = 1 and BOOT1 = 0, with the CPU at 0x1FFFF000, or an optimization edit before those four pins are checked. Pin 35 is VSS_2 and points at chapter file 01. Sources: [DS5319](#source-ds5319-swd) Figure 31 and Table 5, and [RM0008 boot](#source-rm0008-boot).</sub>
</p>

<p align="center">
  <img src="../../assets/gif/boot0-low.gif" width="640" alt="Pin 44 is 0, the probe is on pins 34 and 37, and the target appears">
  <br><sub>▲ Auxiliary figure for the web and for posts. It plays only the normal path: pin 44 is 0, the probe is on pins 34 and 37, and the target appears. Print from the static figure. BOOT0 = 1 and an optimizer edit are not on this GIF.</sub>
</p>

`toolchain-flow.svg` stays as an auxiliary figure. The compile arrows are not on this static figure.

## Timing or state

| Look at this first | Value | Next step |
| --- | --- | --- |
| Pins 34 and 37 | PA13 = SWDIO, PA14 = SWCLK, shared ground, 3.3 V | Do not edit code until these are connected |
| NRST | Pin 7, 0.1 µF | Figure 31. This row does not write a pull-up in kilohms |
| BOOT | BOOT0 = 0, main Flash `0x08000000` | Normal path |
| Failure | BOOT0 = 1 and BOOT1 = 0, `0x1FFFF000` | The user program looks unprogrammed. `0x1FFFB000` is void on the C8 |
| Optimization | `-O2` before the wires are checked | Failure |
| Capacity | 64 KB Flash, 20 KB SRAM | The same cells as the SWD card |
| UART | HSI at 8 MHz and `0x271` still loaded | 12800 |
| Time base | TIM4, 1 ms | Not a generic TIMx |
| Priority | A number of 5 or larger | `5 << 4 = 0x50` |
| Crystal | 5 pF to 15 pF, chosen with the crystal | 6 pF is not required |

## Pitfalls and source cards

| What you see | Why | What to do | Source | Claim this source may support |
| --- | --- | --- | --- | --- |
| The probe reports no target | The wires were not checked | Look at pins 34 and 37, ground, and 3.3 V first | [DS5319 SWD](#source-ds5319-swd) | Pin 34 PA13 is SWDIO. Pin 37 PA14 is SWCLK. Pin 35 is VSS_2 |
| The program looks unprogrammed | Pin 44 is pulled high | Put BOOT0 back to 0 | [RM0008 boot](#source-rm0008-boot) | BOOT1=0 and BOOT0=1 enters `0x1FFFF000`. The C8 is not a connectivity-line part |
| The reset pin is open and the board resets itself | The capacitor is not the Figure 31 cell | Add 0.1 µF as Figure 31 draws it | [DS5319 NRST](#source-ds5319-nrst) | Figure 31's external reset circuit is 0.1 µF. This row does not add a pull-up in kilohms |
| The link says Flash or RAM is too small | The estimate used a larger part | Use the C8 cells, 64 KB and 20 KB | [DS5319 SWD](#source-ds5319-swd) | The xB 128 KB is void on the C8T6 |
| Serial data is garbage and the clock was not checked | The clock fell back to HSI | Confirm it is not sitting at 8 MHz | [RM0008 USART](#source-rm0008-usart) | `0x271` is 115200 at 72 MHz and 12800 at 8 MHz |
| Row P9 was built with 6 pF | One capacitor was treated as required | Choose the capacitors with the crystal, from 5 pF to 15 pF | [DS5319 LSE](#source-ds5319-lse) | 6 pF is not a required value printed in the LSE section. 32.768 kHz and PRL = 32767 stay with chapter file 11 |
| `HAL_Delay` does not return after FreeRTOS is added | The time base is still SysTick | Move the time base to TIM4 | [repository examples](#source-project-examples) | The time base in `examples/freertos-task` is TIM4. Do not write a generic TIMx |
| An interrupt stops in `configASSERT` | The numeric priority is too urgent | Use 5 or a larger number | [FreeRTOS](#source-freertos-syscall) | `5 << 4 = 0x50`. A smaller number must not call FromISR |
| An external lamp stays dark while the resistor is guessed inside a range | The pin and the resistor were not pinned | Use pin 10 and 270 Ω from chapter file 03 | [DS5319 GPIO](#source-ds5319-gpio) | Pin 2 PC13 cannot source the current. This row does not invent another resistor |
```

- [ ] **Step 5: 追加两个来源对象并改罗盘**

按 Task 5 的同一套字段规则，把 `ds5319-nrst` 追加在 `pm0056-dwt` 后面，再把 `ds5319-lse` 追加在 `ds5319-nrst` 后面。`scope` 用本任务测试里的四句。两份罗盘的 `sources` 改成测试里的 `compass`。中文键 `18-常见问题FAQ.md`，英文键 `18-faq.md`。`question`、`deliverable`、`boundary` 不改。原来的 `project-examples` 和 `project-guide` 仍在最前。不要改这两个已有对象，也不要改 `pm0056`、`pm0056-dwt`、`ds5319-swd`、`rm0008-boot`、`rm0008-usart`、`freertos-syscall`、`ds5319-gpio`。

- [ ] **Step 6: 运行测试并提交**

Run: `python3 stm32-book/tests/test_batch6_chapters.py Batch6BootChapterTests -v`

Expected: OK。

```bash
git add docs/18-常见问题FAQ.md docs/en/18-faq.md stm32-book/manifest.json stm32-book/manifest-en.json stm32-book/tests/test_batch6_chapters.py
git commit -m "book: 加厚第 18 章并把第一眼钉在 BOOT0 和两只 SWD 脚上"
```

不要在这一笔里改第 16、17、19 章，也不要升版本号。不要改附录 D，那是 Task 9。

### Task 8: Thicken chapter 19 in both languages

**Files:**
- Modify: `docs/19-项目实战合集.md`
- Modify: `docs/en/19-projects.md`
- Modify: `stm32-book/manifest.json` 与 `stm32-book/manifest-en.json`（只改第 19 章罗盘。不追加新的 `sources` 对象）
- Modify: `stm32-book/tests/test_batch6_chapters.py`
- Test: `stm32-book/tests/test_batch6_chapters.py`

**Interfaces:**
- Consumes: `flash_fit()` 与 `one_slot()`。Task 7 已经把 `ds5319-lse` 放在 `sources` 末尾。已有 id `project-examples`、`ds5319-swd`、`rm0008-adc`、`ds5319-adc` 只被引用。Task 5 的 `baseline_chapter()`。
- Produces: 中英第 19 章各一套四块。十个项目标题还在。文件名和一级标题仍是「项目实战合集」/ `A set of real projects`。`sources` 对象的末尾仍是 `ds5319-nrst`、`ds5319-lse`。视频块字节不变。

学习目标锚点：中文 `## 📌 学习目标`，英文 `## 📌 Learning goals`。这一章没有旧坑标题，也没有核心原理标题。不要新造。十个项目标题保持现在的 `## 1.` 到 `## 10.`，含星级。星级和工时留在项目正文，不进四块。

- [ ] **Step 1: 把章节断言加进测试**

在 `test_batch6_chapters.py` 末尾、`if __name__` 之前追加。不要再贴 `_fetch_baseline`。

```python
class Batch6FlashFitChapterTests(unittest.TestCase):
    def test_project_chapters_keep_one_slot_and_the_same_numbers(self) -> None:
        zh_path = ROOT / "docs" / "19-项目实战合集.md"
        en_path = ROOT / "docs" / "en" / "19-projects.md"
        zh = zh_path.read_text(encoding="utf-8")
        en = en_path.read_text(encoding="utf-8")
        self.assertTrue(zh.startswith("# 19 项目实战合集\n"))
        self.assertTrue(en.startswith("# 19 A set of real projects\n"))
        self.assertNotIn("上册", zh)
        for heading in ("## 原理与边界", "## 关键插图", "## 时序或状态", "## 坑与出处卡"):
            self.assertEqual(1, zh.count(heading))
        for heading in (
            "## Principle and boundary",
            "## Key figures",
            "## Timing or state",
            "## Pitfalls and source cards",
        ):
            self.assertEqual(1, en.count(heading))
        self.assertNotIn("## ⚠️ 常见坑与排查", zh)
        self.assertNotIn("## ⚠️ Pitfalls and troubleshooting", en)
        self.assertNotIn("## 🧠 核心原理", zh)
        self.assertNotIn("## 🧠 Core ideas", en)
        for heading in (
            "## 1. 蓝牙小车（★★ 入门级）",
            "## 2. 温湿度记录仪（★★ 入门级）",
            "## 3. DMA + ADC 迷你示波器（★★★ 进阶）",
            "## 4. USB 数据采集卡（★★★ 进阶）",
            "## 5. IAP 远程升级（★★★ 进阶）",
            "## 6. WS2812 灯带控制器（★★ 进阶）",
            "## 7. 简易逻辑分析仪（★★★★ 挑战）",
            "## 8. 多机 CAN 网络（★★★★ 挑战）",
            "## 9. 自平衡小车（★★★★ 挑战）",
            "## 10. FreeRTOS 智能网关（★★★★ 挑战）",
        ):
            self.assertEqual(1, zh.count(heading))
        for heading in (
            "## 1. Bluetooth car (★★ beginner)",
            "## 2. Temperature and humidity logger (★★ beginner)",
            "## 3. DMA + ADC mini oscilloscope (★★★ intermediate)",
            "## 4. USB data-acquisition card (★★★ intermediate)",
            "## 5. Remote IAP update (★★★ intermediate)",
            "## 6. WS2812 LED-strip controller (★★ intermediate)",
            "## 7. A simple logic analyzer (★★★★ a challenge)",
            "## 8. A multi-node CAN network (★★★★ a challenge)",
            "## 9. A self-balancing car (★★★★ a challenge)",
            "## 10. A FreeRTOS smart gateway (★★★★ a challenge)",
        ):
            self.assertEqual(1, en.count(heading))
        self.assertNotIn("APP_A + APP_B", zh)
        self.assertNotIn("APP_A, and APP_B", en)
        self.assertNotIn("4095.0f", zh)
        self.assertNotIn("4095.0f", en)
        self.assertNotIn("GPIO_PIN_0", zh)
        self.assertNotIn("GPIO_PIN_0", en)
        self.assertIn("4096.0f", zh)
        self.assertIn("4096.0f", en)
        self.assertIn("0x5A5A0001", zh)
        self.assertIn("0x5A5A0001", en)
        self.assertIn("MOTOR_DIR_PIN", zh)
        self.assertIn("MOTOR_DIR_PIN", en)
        zh_blocks = zh.split("## 原理与边界", 1)[1].split("## 📌 学习目标", 1)[0]
        en_blocks = en.split("## Principle and boundary", 1)[1].split("## 📌 Learning goals", 1)[0]
        for blocks in (zh_blocks, en_blocks):
            for token in (
                "0x08000000",
                "0x08004000",
                "0x08004800",
                "0x08010000",
                "0x0801B800",
                "0xB800",
                "110",
                "20480",
                "65536",
                "4096",
                "2048",
                "1.65",
                "133",
                "PB8",
                "PB9",
                "PA0",
                "#source-project-examples",
                "#source-ds5319-swd",
                "#source-rm0008-adc",
                "#source-ds5319-adc",
            ):
                self.assertIn(token, blocks)
            self.assertNotIn("0x5A5A0001", blocks)
            self.assertNotIn("★", blocks)
            self.assertNotIn("0.4", blocks)
            self.assertNotIn("1.25", blocks)
            self.assertNotIn("F411", blocks)
            self.assertNotIn("F407", blocks)
        self.assertIn("../assets/diagrams/sample-19-flash-fit.svg", zh)
        self.assertIn("../../assets/diagrams/sample-19-flash-fit.svg", en)
        self.assertIn("../assets/gif/one-slot.gif", zh)
        self.assertIn("../../assets/gif/one-slot.gif", en)
        zh_key = zh.split("## 关键插图", 1)[1].split("## 时序或状态", 1)[0]
        en_key = en.split("## Key figures", 1)[1].split("## Timing or state", 1)[0]
        self.assertLess(zh_key.index("sample-19-flash-fit.svg"), zh_key.index("one-slot.gif"))
        self.assertLess(en_key.index("sample-19-flash-fit.svg"), en_key.index("one-slot.gif"))
        self.assertIn("自绘", zh_key)
        self.assertIn("Drawn for this book", en_key)
        self.assertNotIn("示意图", zh_key)
        self.assertIn("peripheral-wiring.svg", zh_key)
        lock = json.loads(
            (ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch6-16-17-18-19-lock.json").read_text(
                encoding="utf-8"
            )
        )
        for path in (zh_path, en_path):
            rel = path.relative_to(ROOT).as_posix()
            baseline = baseline_chapter(lock["baseline"], rel)
            now_video = zh if path == zh_path else en
            marker = "<!-- video:ch19 -->"
            end = "<!-- /video:ch19 -->"
            self.assertEqual(
                baseline.split(marker, 1)[1].split(end, 1)[0],
                now_video.split(marker, 1)[1].split(end, 1)[0],
            )
        zh_manifest = json.loads((ROOT / "stm32-book" / "manifest.json").read_text(encoding="utf-8"))
        en_manifest = json.loads((ROOT / "stm32-book" / "manifest-en.json").read_text(encoding="utf-8"))
        compass = ["project-examples", "ds5319-swd", "rm0008-adc", "ds5319-adc"]
        guide = zh_manifest["chapter_guides"]["19-项目实战合集.md"]
        guide_en = en_manifest["chapter_guides"]["19-projects.md"]
        self.assertEqual(compass, guide["sources"])
        self.assertEqual(compass, guide_en["sources"])
        self.assertEqual(
            "怎样把多外设题目切成可独立验收的里程碑，而不是一次集成全部不确定性？",
            guide["question"],
        )
        self.assertEqual("项目清单给出学习路径，不构成安全、EMC、量产测试或法规符合性声明。", guide["boundary"])
        self.assertEqual(["ds5319-nrst", "ds5319-lse"], list(zh_manifest["sources"])[-2:])
        self.assertNotIn("ds5319-flash", zh_manifest["sources"])
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `python3 stm32-book/tests/test_batch6_chapters.py Batch6FlashFitChapterTests -v`

Expected: FAIL，中文稿还没有 `## 原理与边界`。

- [ ] **Step 3: 改掉和前面各章冲突的格子**

不要动 `<!-- video:ch19 -->` 到 `<!-- /video:ch19 -->` 之间的字节。不要删掉十个项目。不要改一级标题。不要把 `0x5A5A0001` 从项目 5 的草稿里删掉。不要给电机新指定一只脚。不要编 F411 或 F407 的 SRAM 容量。灯珠的 `T0H=0.4µs`、`T1H=0.8µs`、周期 `1.25µs` 留在项目 6，旁边补一句：这是灯珠厂商的时序，不是 RM0008。工时和星级留在各项目的表里。

中文项目 1，把这一行：

```c
        HAL_GPIO_WritePin(GPIOA, GPIO_PIN_0, duty >= 0 ? GPIO_PIN_SET : GPIO_PIN_RESET);
```

换成：

```c
        /* 不要把方向脚放在第 10 脚 PA0。它和灯、ADC、WKUP 撞在一起。这里不新指定一只替代脚。 */
        HAL_GPIO_WritePin(MOTOR_DIR_PORT, MOTOR_DIR_PIN, duty >= 0 ? GPIO_PIN_SET : GPIO_PIN_RESET);
```

`GPIO_PIN_1` 那一行留着。不要把 `MOTOR_DIR_PIN` 定义成某一只具体脚。

中文项目 3，把这一段：

```c
/* 电压换算：V = code × Vref / 4095（12 位 ADC） */
static float Code2Volt(uint16_t code)
{
    return (float)code * 3.3f / 4095.0f;
}
```

换成：

```c
/* 电压换算：V = code × Vref / 4096（12 位 ADC）。码 2048 在名义 3.3 V 下是 1.65 V。分母 4095 会偏一个 LSB。 */
static float Code2Volt(uint16_t code)
{
    return (float)code * 3.3f / 4096.0f;
}
```

中文项目 4，把这一行：

```c
    CDC_Transmit_FS(frame, sizeof(frame));   /* 见第 14 章 */
```

换成：

```c
    CDC_Transmit_FS(frame, sizeof(frame));   /* 4 + 128 + 1 = 133。这不是第 14 章全速批量的 64 字节包上限 */
```

中文项目 5 的技术方案整句：

```markdown
**技术方案**：Flash 划分 Bootloader + 参数区 + APP_A + APP_B（见第 12 章）。升级时把新固件写入空闲区，校验 CRC 后写「启动标志」并复位；Bootloader 依据标志跳转到有效区，失败则回退。
```

换成：

```markdown
**技术方案**：C8 上先按第 12 章的一张 APP 做通。Bootloader 从 `0x08000000` 起 16 KB，参数区从 `0x08004000` 起 2 KB，APP 从 `0x08004800` 起、长度 `0xB800`，到 `0x08010000` 之前。第 12 章没有第二张槽。再放一张同样的 `0xB800` 是 110 KB，结束于 `0x0801B800`。把 46 KB 再切成两只 23 KB 是另一份设计，不要写成「见第 12 章」。
```

在 `uint32_t magic;       /* 0x5A5A0001 表示有效 */` 的下一行之前，保持这行原样，并在结构体注释后面加一行注释：

```c
    uint32_t magic;       /* 0x5A5A0001 表示有效。这个数留在草稿里，不是第 12 章的钥匙，也不进出处卡。C8 上没有第二张槽。 */
```

只替换原来那一行注释，不要删 `0x5A5A0001`，也不要删后面的 `APP_A_ADDR` / `APP_B_ADDR` 草稿。

中文项目 6 的技术方案句末加上：「`T0H=0.4µs`、`T1H=0.8µs`、周期 `1.25µs` 是灯珠厂商的时序，不是 RM0008。」原来的三个数留着。

中文项目 7，在 `#define LA_DEPTH  (64 * 1024)` 的上一行加上：

```c
/* 64 * 1024 = 65536，大于 C8 的 SRAM 20480 字节。这只数组在 STM32F103C8T6 上作废。这里不编 F411 或 F407 的 SRAM 容量。 */
#define LA_DEPTH  (64 * 1024)
```

宏本身留着，后面的 `la_buf` 仍引用 `LA_DEPTH`。

英文做同样的六处替换。

项目 1：

```c
        HAL_GPIO_WritePin(GPIOA, GPIO_PIN_0, duty >= 0 ? GPIO_PIN_SET : GPIO_PIN_RESET);
```

换成：

```c
        /* Do not put the direction pin on pin 10 PA0. It collides with the lamp, the ADC, and WKUP. This snippet does not name a replacement pin. */
        HAL_GPIO_WritePin(MOTOR_DIR_PORT, MOTOR_DIR_PIN, duty >= 0 ? GPIO_PIN_SET : GPIO_PIN_RESET);
```

项目 3：

```c
/* Voltage conversion: V = code × Vref / 4095 (12-bit ADC) */
static float Code2Volt(uint16_t code)
{
    return (float)code * 3.3f / 4095.0f;
}
```

换成：

```c
/* Voltage conversion: V = code × Vref / 4096 (12-bit ADC). Code 2048 is 1.65 V at a nominal 3.3 V. A denominator of 4095 is off by one LSB. */
static float Code2Volt(uint16_t code)
{
    return (float)code * 3.3f / 4096.0f;
}
```

项目 4：

```c
    CDC_Transmit_FS(frame, sizeof(frame));   /* see chapter 14 */
```

换成：

```c
    CDC_Transmit_FS(frame, sizeof(frame));   /* 4 + 128 + 1 = 133. This is not the 64-byte full-speed bulk packet limit in chapter 14 */
```

项目 5 的 Approach 整句：

```markdown
**Approach**: split Flash into a bootloader, a parameter block, APP_A, and APP_B (see [chapter 12](12-flash-iap.md)). During an update, write the new image into the idle slot, check the CRC, write the "boot flag", and reset. The bootloader jumps to the slot the flag names. If that image is bad, it falls back.
```

换成：

```markdown
**Approach**: on the C8, bring up the one application from chapter 12 first. The bootloader starts at `0x08000000` for 16 KB, the parameter block starts at `0x08004000` for 2 KB, and the application starts at `0x08004800` with length `0xB800`, ending before `0x08010000`. Chapter 12 has no second slot. A second image of the same `0xB800` is 110 KB and ends at `0x0801B800`. Cutting the 46 KB into two 23 KB images is a different design. Do not write it as "see chapter 12".
```

把 magic 那一行注释换成：

```c
    uint32_t magic;       /* 0x5A5A0001 means valid. The number stays in this draft. It is not a chapter 12 key, and it does not enter a source card. The C8 has no second slot. */
```

项目 6 的技术方案句末加上："`T0H=0.4µs`, `T1H=0.8µs`, and the 1.25µs period are the LED vendor's timing, not RM0008."

项目 7 在宏的上一行加上：

```c
/* 64 * 1024 = 65536, which is larger than the C8 SRAM of 20480 bytes. This array is void on STM32F103C8T6. This note does not invent an F411 or F407 SRAM size. */
#define LA_DEPTH  (64 * 1024)
```

- [ ] **Step 4: 在学习目标之前插入四块**

中文：

```markdown
## 原理与边界

这一章仍是 STM32F103C8T6。十个项目都留着。四块不新设计第十一个项目。写在这颗料上的数必须放得进这颗料，并且和第 12 章、第 09 章是同一笔账。文件名和标题保持「项目实战合集」。

一张 APP。Bootloader 从 `0x08000000` 起 16 KB，参数区从 `0x08004000` 起 2 KB，APP 从 `0x08004800` 起 46 KB，长度 `0xB800`，到 `0x08010000` 之前。`16 + 2 + 46 = 64`。这是第 12 章和 `examples/iap-bootloader` 的地图。见 [本仓库例程](#source-project-examples)。

再放一张同样的 `0xB800`，合计 `16 + 2 + 46 + 46 = 110` KB。`0x08000000 + 0x1B800 = 0x0801B800`，越过 `0x08010000`。第 12 章没有第二张槽。把 46 KB 再切成两只 23 KB 是另一份设计，不是这张图的正常路径。闪存在 `0x08010000` 结束，见 [DS5319](#source-ds5319-swd)。

`64 * 1024 = 65536`。C8 的 SRAM 是 20 KB，也就是 20480 字节。65536 大于 20480。这只数组在 STM32F103C8T6 上作废。这里不编另一颗料的 SRAM 容量。

分母是 4096。码 2048 在名义 3.3 V 下是 1.65 V。分母 4095 会偏一个 LSB。跟第 09 章同一笔。见 [RM0008 ADC](#source-rm0008-adc)。这一章不重画采样电容。

应用帧 `4 + 128 + 1 = 133` 字节。第 14 章全速批量的一包上限是 64 字节。133 要拆开送。不把 133 写成 `wMaxPacketSize`。48 MHz 和 `0x1209/0x0001` 只交叉引用，不重画第 14 章。

项目 8 的两端各 120 Ω、工作脚 PB8/PB9、500 kbit/s，跟第 13 章同一笔。收发器是 5 V 还是 3.3 V，留在硬件清单，不进出处卡。见 [本仓库例程](#source-project-examples)。

方向脚不要放在第 10 脚 PA0。那只脚是 PA0-WKUP，也是 ADC12_IN0。见 [DS5319 ADC](#source-ds5319-adc)。四块不新指定一只替代脚。

一轮只加一个新外设。这是方法，不是新的电气限额。工时和星级不进这一块。灯珠的微秒若留在项目 6，标明那是灯珠厂商的数，不是 RM0008，并且不进这一块。

## 关键插图

<p align="center">
  <img src="../assets/diagrams/sample-19-flash-fit.svg" width="760" alt="C8 只有一张长度 0xB800 的 APP。两张是 110 KB。65536 字节大于 20 KB SRAM">
  <br><sub>▲ 自绘。正常路径是 16 KB、2 KB 和一张 0xB800，结束在 0x08010000 之前。SRAM 是 20 KB，也就是 20480 字节。失败路径是第二张 0xB800 从 0x08010000 画到 0x0801B800，以及一只 65536 字节的数组超出 20480。旁注是分母 4095，以及把 133 字节当成一包 USB。出处是第 12 章已经冻结的地图和 [DS5319](#source-ds5319-swd) 的 64 KB / 20 KB。</sub>
</p>

<p align="center">
  <img src="../assets/gif/one-slot.gif" width="640" alt="16 KB、2 KB 和一张 0xB800 依次填到 0x08010000 为止">
  <br><sub>▲ 网页和公众号辅图。只播放正常路径：16 KB、2 KB 和一张 0xB800 依次填到 0x08010000 为止。印刷以静态主图为准。第二张 APP 和 65536 字节的数组不在这条 GIF 上。</sub>
</p>

`peripheral-wiring.svg` 留作辅图。接线总览不代替这张地图。

## 时序或状态

| 对象 | 长度 | 结束于 | 放不放得下 |
| --- | --- | --- | --- |
| Bootloader | 16 KB | `0x08004000` | 放下 |
| 参数区 | 2 KB | `0x08004800` | 放下 |
| 一张 APP | `0xB800` | `0x08010000` | 放下 |
| 两张 `0xB800` | 110 KB | `0x0801B800` | 放不下。这不是第 12 章的地图 |
| SRAM | 20480 字节 | 片内 | 放下 |
| 65536 字节的数组 | `64 * 1024` | 超出 SRAM | 在 C8 上放不下 |
| ADC | 分母 4096 | 码 2048 是 1.65 V | 分母 4095 失败 |
| USB | 应用帧 133 字节 | 一包上限 64 字节 | 133 要拆开送 |

## 坑与出处卡

| 现象 | 原因 | 处理 | 出处 | 该来源允许支持的主张 |
| --- | --- | --- | --- | --- |
| 升级方案写成两张 APP，并注明见第 12 章 | 把另一份设计写成了这一章的地图 | C8 上先按一张 `0xB800` 做通 | [本仓库例程](#source-project-examples) | `examples/iap-bootloader` 的 APP 长度是 `0xB800`。第 12 章没有第二张槽 |
| 第二张镜像链接到 `0x08010000` 之后 | 64 KB 已经结束 | 停在 `0x08010000` | [DS5319](#source-ds5319-swd) | STM32F103x8 的闪存是 64 KB。两张 46 KB 加上 16 KB 和 2 KB 是 110 KB |
| 逻辑分析仪缓冲在 C8 上链不过 | `64 * 1024` 大于这颗料的 SRAM | 不要把 65536 字节编进 C8 | [DS5319](#source-ds5319-swd) | SRAM 是 20 KB，即 20480 字节。65536 更大。这一行不给出另一颗料的容量 |
| 示波器电压偏一个 LSB | 分母用了 4095 | 分母用 4096 | [RM0008 ADC](#source-rm0008-adc) | 码 2048 在名义 3.3 V 下是 1.65 V。4095 会偏一个 LSB |
| 采集卡把 133 字节写成端点包长 | 把应用帧当成了包上限 | 全速批量一包最多 64 字节 | [本仓库例程](#source-project-examples) | 133 是 `4 + 128 + 1`。它不是第 14 章的包上限 |
| 小车方向写在 PA0 | 和第 10 脚的其他用途撞在一起 | 换离第 10 脚 | [DS5319 ADC](#source-ds5319-adc) | 第 10 脚是 PA0-WKUP，也是 ADC12_IN0。这一行不新分配电机脚 |
| 两个 CAN 节点速率对不上 | 没走第 13 章那一笔 | 用 500 kbit/s，两端各 120 Ω | [本仓库例程](#source-project-examples) | 例程的预分频是 9，工作脚是 PB8/PB9。这一行不规定收发器是 5 V 还是 3.3 V |
```

英文四块用同样的地址和同一组 `#source-`。图路径用 `../../assets/`。图注写 `Drawn for this book`。四块里不要出现 `0x5A5A0001`、星号、`0.4`、`1.25`、`F411`、`F407`。

```markdown
## Principle and boundary

This chapter stays on STM32F103C8T6. All ten projects stay. The four sections do not design an eleventh project. A number written for this part has to fit in this part, and it has to be the same ledger as chapter files 12 and 09. The file name and the title stay "A set of real projects".

One application. The bootloader starts at `0x08000000` for 16 KB, the parameter block starts at `0x08004000` for 2 KB, and the application starts at `0x08004800` for 46 KB, length `0xB800`, ending before `0x08010000`. `16 + 2 + 46 = 64`. That is the map in chapter file 12 and in `examples/iap-bootloader`. See [repository examples](#source-project-examples).

A second image of the same `0xB800` is `16 + 2 + 46 + 46 = 110` KB. `0x08000000 + 0x1B800 = 0x0801B800`, past `0x08010000`. Chapter file 12 has no second slot. Cutting the 46 KB into two 23 KB images is a different design, and it is not the normal path of this figure. Flash ends at `0x08010000`. See [DS5319](#source-ds5319-swd).

`64 * 1024 = 65536`. SRAM on the C8 is 20 KB, which is 20480 bytes. 65536 is larger than 20480. This array is void on STM32F103C8T6. This section does not invent another part's SRAM size.

The denominator is 4096. Code 2048 is 1.65 V at a nominal 3.3 V. A denominator of 4095 is off by one LSB. That is the same sentence as chapter file 09. See [RM0008 ADC](#source-rm0008-adc). This chapter does not redraw the sampling capacitor.

The application frame is `4 + 128 + 1 = 133` bytes. Chapter file 14's full-speed bulk packet limit is 64 bytes. 133 has to be split. Do not write 133 as `wMaxPacketSize`. 48 MHz and `0x1209/0x0001` are cross-references only. Do not redraw chapter file 14.

Project 8 uses 120 Ω at each end, pins PB8 and PB9, and 500 kbit/s, the same ledger as chapter file 13. Whether the transceiver is 5 V or 3.3 V stays in the bill of materials and does not enter a source card. See [repository examples](#source-project-examples).

Do not put the direction pin on pin 10 PA0. That pin is PA0-WKUP and also ADC12_IN0. See [DS5319 ADC](#source-ds5319-adc). The four sections do not name a replacement pin.

Add one new peripheral per pass. That is a method, not a new electrical limit. Hours and star ratings do not enter this section. If the LED microseconds stay in project 6, label them as the LED vendor's numbers, not RM0008, and do not copy them into this section.

## Key figures

<p align="center">
  <img src="../../assets/diagrams/sample-19-flash-fit.svg" width="760" alt="The C8 has one application of length 0xB800. Two of them are 110 KB. 65536 bytes is larger than 20 KB of SRAM.">
  <br><sub>▲ Drawn for this book. The normal path is 16 KB, 2 KB, and one 0xB800 image ending before 0x08010000. SRAM is 20 KB, which is 20480 bytes. The failure path draws a second 0xB800 from 0x08010000 to 0x0801B800, and a 65536-byte array past 20480. The notes are a denominator of 4095, and treating 133 bytes as one USB packet. Sources: the map already frozen in chapter file 12, and the 64 KB / 20 KB cells in [DS5319](#source-ds5319-swd).</sub>
</p>

<p align="center">
  <img src="../../assets/gif/one-slot.gif" width="640" alt="16 KB, 2 KB, and one 0xB800 image fill up to 0x08010000">
  <br><sub>▲ Auxiliary figure for the web and for posts. It plays only the normal path: 16 KB, 2 KB, and one 0xB800 image fill up to 0x08010000. Print from the static figure. The second application and the 65536-byte array are not on this GIF.</sub>
</p>

`peripheral-wiring.svg` stays as an auxiliary figure. The wiring overview does not replace this map.

## Timing or state

| Object | Length | Ends at | Fits |
| --- | --- | --- | --- |
| Bootloader | 16 KB | `0x08004000` | fits |
| Parameter block | 2 KB | `0x08004800` | fits |
| One application | `0xB800` | `0x08010000` | fits |
| Two `0xB800` images | 110 KB | `0x0801B800` | does not fit. This is not the chapter 12 map |
| SRAM | 20480 bytes | on chip | fits |
| A 65536-byte array | `64 * 1024` | past SRAM | does not fit on the C8 |
| ADC | denominator 4096 | code 2048 is 1.65 V | denominator 4095 fails |
| USB | application frame of 133 bytes | packet limit 64 bytes | 133 has to be split |

## Pitfalls and source cards

| What you see | Why | What to do | Source | Claim this source may support |
| --- | --- | --- | --- | --- |
| The update plan says two applications and cites chapter 12 | A different design was written as this chapter's map | Bring up one `0xB800` application on the C8 first | [repository examples](#source-project-examples) | The application length in `examples/iap-bootloader` is `0xB800`. Chapter 12 has no second slot |
| The second image is linked past `0x08010000` | The 64 KB already ended | Stop at `0x08010000` | [DS5319](#source-ds5319-swd) | STM32F103x8 Flash is 64 KB. Two 46 KB images plus 16 KB and 2 KB are 110 KB |
| The logic-analyzer buffer does not link on the C8 | `64 * 1024` is larger than this part's SRAM | Do not compile 65536 bytes into the C8 | [DS5319](#source-ds5319-swd) | SRAM is 20 KB, which is 20480 bytes. 65536 is larger. This row does not give another part's capacity |
| The scope voltage is off by one LSB | The denominator was 4095 | Use 4096 | [RM0008 ADC](#source-rm0008-adc) | Code 2048 is 1.65 V at a nominal 3.3 V. 4095 is off by one LSB |
| The acquisition card writes 133 bytes as the endpoint packet length | The application frame was treated as the packet limit | A full-speed bulk packet is at most 64 bytes | [repository examples](#source-project-examples) | 133 is `4 + 128 + 1`. It is not the chapter 14 packet limit |
| The car's direction pin is written on PA0 | It collides with the other uses of pin 10 | Move it off pin 10 | [DS5319 ADC](#source-ds5319-adc) | Pin 10 is PA0-WKUP and also ADC12_IN0. This row does not assign a motor pin |
| Two CAN nodes do not agree on the rate | They are not on the chapter 13 ledger | Use 500 kbit/s and 120 Ω at each end | [repository examples](#source-project-examples) | The example prescaler is 9, and the pins are PB8 and PB9. This row does not set the transceiver to 5 V or to 3.3 V |
```

- [ ] **Step 5: 只改罗盘，不追加来源对象**

两份罗盘的 `sources` 改成 `["project-examples", "ds5319-swd", "rm0008-adc", "ds5319-adc"]`。中文键 `19-项目实战合集.md`，英文键 `19-projects.md`。`question`、`deliverable`、`boundary` 不改。不要新增 `sources` 对象。`sources` 的最后两个键仍是 `ds5319-nrst` 和 `ds5319-lse`。不要改 `project-examples`、`ds5319-swd`、`rm0008-adc`、`ds5319-adc`、`rm0008-flash` 的字段。第 12 章正文的 diff 必须为空。

- [ ] **Step 6: 运行测试并提交**

Run: `python3 stm32-book/tests/test_batch6_chapters.py Batch6FlashFitChapterTests -v`

Expected: OK。

```bash
git add docs/19-项目实战合集.md docs/en/19-projects.md stm32-book/manifest.json stm32-book/manifest-en.json stm32-book/tests/test_batch6_chapters.py
git commit -m "book: 加厚第 19 章并把一张 APP 和 20 KB SRAM 钉在同一笔账上"
```

不要在这一笔里改第 16、17、18 章，也不要升版本号。不要改附录 D，那是 Task 9。

### Task 9: One glossary cell

**Files:**
- Modify: `stm32-book/book/D-术语表.md`（只改「Stop 之后的时钟」那一行里 F103 的电流句子）
- Modify: `stm32-book/book/en/D-glossary.md`（只改 `Clock after Stop` 那一行里 F103 的电流句子）
- Modify: `stm32-book/tests/test_batch6_chapters.py`
- Test: `stm32-book/tests/test_batch6_chapters.py`

**Interfaces:**
- Consumes: Task 5 的 `baseline_chapter()`。它内部先 `_fetch_baseline()`。Book CI 的 checkout 深度是 1，锁定文件里的 SHA 不在浅克隆里。不要改成裸的 `git show`，也不要改 `.github/workflows/book.yml` 的 `fetch-depth`。
- Produces: 两份术语表各有一行和基线不同。那一行仍含 HSI 8 MHz、L476 的 1.1 µA、1.4 µA、4 µs。附录 A 与基线逐字节相同。

- [ ] **Step 1: 把行差断言加进测试**

在 `test_batch6_chapters.py` 末尾、`if __name__` 之前追加。调用已经存在的 `baseline_chapter()`。

```python
class Batch6GlossaryTests(unittest.TestCase):
    def test_only_the_f103_stop_current_cell_changes(self) -> None:
        lock = json.loads(
            (ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch6-16-17-18-19-lock.json").read_text(
                encoding="utf-8"
            )
        )
        pairs = (
            (
                "stm32-book/book/D-术语表.md",
                "约 14~20 µA",
                "低功耗稳压器典型 14 µA，主稳压器那一格是 24 µA，两格都不含独立看门狗",
            ),
            (
                "stm32-book/book/en/D-glossary.md",
                "about 14 to 20 µA",
                "14 µA on the low-power regulator and 24 µA on the main regulator",
            ),
        )
        for rel, old_phrase, new_phrase in pairs:
            now = (ROOT / rel).read_text(encoding="utf-8")
            base = baseline_chapter(lock["baseline"], rel)
            old_lines = base.splitlines()
            new_lines = now.splitlines()
            self.assertEqual(len(old_lines), len(new_lines))
            changed = [index for index, (before, after) in enumerate(zip(old_lines, new_lines)) if before != after]
            self.assertEqual([229], changed)
            row = new_lines[229]
            self.assertIn(new_phrase, row)
            self.assertNotIn(old_phrase, row)
            self.assertNotIn(old_phrase, now)
            for token in ("8 MHz", "1.1 µA", "1.4 µA", "4 µs"):
                self.assertIn(token, row)
                self.assertIn(token, old_lines[229])
        for rel in ("stm32-book/book/A-工程深读.md", "stm32-book/book/en/A-uart-dma.md"):
            now = (ROOT / rel).read_text(encoding="utf-8")
            self.assertEqual(baseline_chapter(lock["baseline"], rel), now)
```

`changed == [229]` 是因为这两份文件的目标行都在第 230 行，`splitlines()` 从 0 起算。若基线文件的行号变了，先打印基线里含 `14~20` 或 `14 to 20` 的那一行下标，把测试里的 `229` 改成那个下标。不要改成「任意一行都可以变」。变的仍然只能是这一行。

- [ ] **Step 2: 运行测试，确认失败**

Run: `python3 stm32-book/tests/test_batch6_chapters.py Batch6GlossaryTests -v`

Expected: FAIL，中文第 230 行仍含 `约 14~20 µA`。若失败原因是 `git show` 找不到对象，先确认测试走的是 `baseline_chapter()`，它会 `git fetch --depth=1 origin <锁定 baseline>`，失败后再 `git fetch --depth=50 origin +refs/heads/$GITHUB_BASE_REF:refs/remotes/origin/$GITHUB_BASE_REF`。不要把工作流改成全历史。

- [ ] **Step 3: 只替换这一格的 F103 电流句子**

中文把整行换成：

```markdown
| Stop 之后的时钟 | 第 16 章：F103 在 3.3 V、25°C 下 Stop 低功耗稳压器典型 14 µA，主稳压器那一格是 24 µA，两格都不含独立看门狗，是芯片在该条件下的数。醒来回到 HSI。第 02 章：F1 上电默认的 HSI 是 8 MHz。第 24 章：L476 封面 Stop 2 为 1.1 µA，带 RTC 为 1.4 µA，从 Stop 唤醒 4 µs | F103 要把 PLL 重新装回 72 MHz。L476 的 Stop 2 醒来由 `STOPWUCK` 选择 MSI 或 HSI16，此时还没有 80 MHz 的 PLL。SysTick 若仍每 1 ms 中断，测到的是反复唤醒。1.1 µA 要和该 revision 的 ES0250 一起读，再和拔掉调试器、LED 之后的板级电流对照 | 醒后第一帧串口乱码，或电流停在毫安。封面 1.1 µA 被写成整板验收上限 |
```

英文把整行换成：

```markdown
| Clock after Stop | Chapter 16: an F103 Stop at 3.3 V and 25°C is 14 µA on the low-power regulator and 24 µA on the main regulator. Both cells exclude the independent watchdog. That is the chip under those conditions. Wake-up returns to HSI. Chapter 02: the F1 power-up HSI is 8 MHz. Chapter 24: the L476 cover lists Stop 2 at 1.1 µA, 1.4 µA with the RTC, and 4 µs to wake from Stop | The F103 PLL has to be programmed back to 72 MHz. After L476 Stop 2, `STOPWUCK` selects MSI or HSI16. The 80 MHz PLL is a later step. A SysTick that still interrupts every 1 ms measures repeated wake-ups. Read 1.1 µA together with ES0250 for that revision, then set it beside the board current with the debugger and the LED removed | The first UART frame after wake-up is garbage, or the current stays in milliamps. The cover's 1.1 µA has been written down as the whole-board limit |
```

第三列和第四列与基线相同。不要改 167 ns 那一行，不要改 `0x271` 那一页里的其他行，不要改附录 A。

- [ ] **Step 4: 运行测试并提交**

Run: `python3 stm32-book/tests/test_batch6_chapters.py Batch6GlossaryTests -v`

Expected: OK。

```bash
git add stm32-book/book/D-术语表.md stm32-book/book/en/D-glossary.md stm32-book/tests/test_batch6_chapters.py
git commit -m "book: 术语表只改 Stop 之后 F103 的 14 µA 和 24 µA"
```

不要在这一笔里升版本号。

### Task 10: Register 1.3.1

**Files:**
- Modify: `stm32-book/manifest.json`（`version` 改为 `1.3.1`，`date` 保持 `2026-10-25`）
- Modify: `stm32-book/manifest-en.json`（同上）
- Modify: `stm32-book/revisions.json`
- Modify: `stm32-book/README.md`
- Modify: `CREDITS.md`
- Modify: `stm32-book/tests/test_build.py`
- Test: `stm32-book/tests/test_build.py`

**Interfaces:**
- Consumes: Task 2 到 Task 9 的来源和四章正文。
- Produces: 当前版本是 1.3.1 · 2026-10-25。已有修订条目的中英文句子一个字都不改，只把下标后移。没有 tag，没有 Release。

- [ ] **Step 1: 把版本断言改到 1.3.1，并先看到失败**

`BookBuildContractTests.assert_version_history_and_index` 里的元组在 `1.3.0` 之前加上 `1.3.1`：

```python
        versions = ("1.3.1", "1.3.0", "1.2.9", "1.2.8", "1.2.7", "1.2.6", "1.2.5", "1.2.4", "1.2.3", "1.2.2", "1.2.1", "1.2.0", "1.1.1", "1.1.0", "1.0.8", "1.0.7", "1.0.6", "1.0.5", "1.0.4", "1.0.3", "1.0.2", "1.0.1", "1.0.0")
        for version in versions:
            self.assertIn(f">{version}<", history)
        self.assertLess(history.index(">1.3.1<"), history.index(">1.3.0<"))
        self.assertLess(history.index(">1.3.0<"), history.index(">1.2.9<"))
```

后面从 `1.2.9` 到 `1.0.0` 的 `assertLess` 链原样留下。

`test_revision_file_lists_1_0_0_through_manifest_version` 的期望列表同样在最前加上 `"1.3.1"`。不要改列表里已有的 `"1.3.0"` 以及更早的版本号。

`test_build_produces_one_complete_offline_book` 和 `test_english_book_is_a_separate_offline_edition` 里的 `self.assertIn("<strong>v1.3.0</strong>", html)` 改成 `self.assertIn("<strong>v1.3.1</strong>", html)`。`test_english_book_is_a_separate_offline_edition` 里的 `self.assertEqual("1.3.0", manifest["version"])` 改成 `self.assertEqual("1.3.1", manifest["version"])`。

`test_visual_polish_version_is_1_2_0` 的下标整组后移。把现在的

```python
        batch5 = revisions["entries"][0]
        posters = revisions["entries"][1]
        density = revisions["entries"][2]
        entry = revisions["entries"][3]
        cover = revisions["entries"][4]
        tokens = revisions["entries"][5]
        typography = revisions["entries"][6]
        batch4 = revisions["entries"][7]
        batch3 = revisions["entries"][8]
        guide = revisions["entries"][9]
        previous = revisions["entries"][10]
        self.assertEqual("1.3.0", self.manifest["version"])
        self.assertEqual("2026-10-25", self.manifest["date"])
        self.assertEqual("1.3.0", english["version"])
        self.assertEqual("2026-10-25", english["date"])
        self.assertEqual("1.3.0", batch5["version"])
```

换成：

```python
        batch6 = revisions["entries"][0]
        batch5 = revisions["entries"][1]
        posters = revisions["entries"][2]
        density = revisions["entries"][3]
        entry = revisions["entries"][4]
        cover = revisions["entries"][5]
        tokens = revisions["entries"][6]
        typography = revisions["entries"][7]
        batch4 = revisions["entries"][8]
        batch3 = revisions["entries"][9]
        guide = revisions["entries"][10]
        previous = revisions["entries"][11]
        self.assertEqual("1.3.1", self.manifest["version"])
        self.assertEqual("2026-10-25", self.manifest["date"])
        self.assertEqual("1.3.1", english["version"])
        self.assertEqual("2026-10-25", english["date"])
        self.assertEqual("1.3.1", batch6["version"])
        self.assertEqual("2026-10-25", batch6["date"])
        self.assertEqual(batch6["date"], self.manifest["date"])
        self.assertEqual(batch6["date"], english["date"])
        self.assertEqual(
            [
                "第 16 章写上 Stop 低功耗稳压器在 3.3 V、25°C 是 14 µA，主稳压器那一格是 24 µA；醒来是 HSI 8 MHz，BRR 仍为 0x271 时线上是 12800 bit/s。第 17 章写上先看 CFSR，BFAR 要 bit 15 为 1 才有效；72 个 DWT 周期是 1 µs，要先置 DEMCR bit 24。",
                "第 18 章写上认不出芯片时先看第 34 脚、第 37 脚和第 44 脚 BOOT0；BOOT0=1 且 BOOT1=0 进的是 0x1FFFF000。第 19 章写上 C8 的一张 APP 是 0xB800，两张 0xB800 是 110 KB；64×1024 字节大于 20 KB SRAM。",
            ],
            batch6["zh"],
        )
        self.assertEqual(
            [
                "Chapter file 16 records the Stop low-power regulator at 14 µA at 3.3 V and 25°C, and the main-regulator cell at 24 µA. Wake-up is the 8 MHz HSI, and BRR left at 0x271 is 12800 bit/s on the wire. Chapter file 17 records reading CFSR first, with BFAR valid only when bit 15 is 1. 72 DWT cycles are 1 µs after DEMCR bit 24 is set.",
                "Chapter file 18 records the first look at pins 34 and 37 and at BOOT0 on pin 44. BOOT0=1 with BOOT1=0 enters 0x1FFFF000. Chapter file 19 records one C8 application of length 0xB800. Two images of 0xB800 are 110 KB. 64×1024 bytes is larger than 20 KB of SRAM.",
            ],
            batch6["en"],
        )
        self.assertEqual("1.3.0", batch5["version"])
```

紧跟在后面的 `batch5["date"]`、`batch5["zh"]`、`batch5["en"]` 两句，以及 posters、density、entry、cover、tokens、typography、batch4、batch3、guide、previous 的全部中英文断言，一个字都不要改。它们只是改了从哪一个下标读。

README 断言改成：

```python
        self.assertIn("当前版本：**v1.3.1 · 2026-10-25**", readme)
        self.assertIn("版本号已经是 1.3.1。", readme)
        self.assertIn("也不要把 1.2.9 的产物标成 1.3.0。", readme)
        self.assertIn("也不要把 1.3.0 的产物标成 1.3.1。", readme)
        self.assertIn("打 tag `v1.3.1`", readme)
        self.assertNotIn("当前版本：**v1.3.0", readme)
        self.assertNotIn("打 tag `v1.3.0`", readme)
```

原来对 1.1.1 到 1.2.8 那一串「也不要把」的断言留着。`assertNotIn("当前版本：**v1.2.9"` 和 `assertNotIn("打 tag `v1.2.9`"` 也留着。不要删 `样式来自` 那一句。不要删 `0x271`、`167 ns`、账本名，也不要改 `test_publication_outline_keeps_parts_chapters_and_appendices` 里的 `self.assertEqual(44, len(outline))`。不要改 CSS 哈希一类的视觉契约。

- [ ] **Step 2: 运行版本测试，确认失败**

Run: `python3 stm32-book/tests/test_build.py BookBuildContractTests.test_revision_file_lists_1_0_0_through_manifest_version -v`

Expected: FAIL，修订列表的首项仍是 `1.3.0`。

- [ ] **Step 3: 写 1.3.1**

两份 manifest 的 `version` 改为 `1.3.1`，`date` 保持 `2026-10-25`。不要改 `sources` 里已有对象的字段，也不要改这一批五个新对象的 snapshot。

在 `stm32-book/revisions.json` 的 `entries` 数组最前面插入：

```json
{
  "version": "1.3.1",
  "date": "2026-10-25",
  "zh": [
    "第 16 章写上 Stop 低功耗稳压器在 3.3 V、25°C 是 14 µA，主稳压器那一格是 24 µA；醒来是 HSI 8 MHz，BRR 仍为 0x271 时线上是 12800 bit/s。第 17 章写上先看 CFSR，BFAR 要 bit 15 为 1 才有效；72 个 DWT 周期是 1 µs，要先置 DEMCR bit 24。",
    "第 18 章写上认不出芯片时先看第 34 脚、第 37 脚和第 44 脚 BOOT0；BOOT0=1 且 BOOT1=0 进的是 0x1FFFF000。第 19 章写上 C8 的一张 APP 是 0xB800，两张 0xB800 是 110 KB；64×1024 字节大于 20 KB SRAM。"
  ],
  "en": [
    "Chapter file 16 records the Stop low-power regulator at 14 µA at 3.3 V and 25°C, and the main-regulator cell at 24 µA. Wake-up is the 8 MHz HSI, and BRR left at 0x271 is 12800 bit/s on the wire. Chapter file 17 records reading CFSR first, with BFAR valid only when bit 15 is 1. 72 DWT cycles are 1 µs after DEMCR bit 24 is set.",
    "Chapter file 18 records the first look at pins 34 and 37 and at BOOT0 on pin 44. BOOT0=1 with BOOT1=0 enters 0x1FFFF000. Chapter file 19 records one C8 application of length 0xB800. Two images of 0xB800 are 110 KB. 64×1024 bytes is larger than 20 KB of SRAM."
  ]
}
```

修订说明只写这四章，用文件名前缀。不写第 28 章，不把标题写成「项目实战上册」。

`stm32-book/README.md` 的当前版本句改为：

```markdown
当前版本：**v1.3.1 · 2026-10-25**。中文整书和英文整书共用这一版号。GitHub Release 仍要等这次提交进入 `main` 且 Book CI 产出四份文件之后，由有权限的人另行处理。
```

把「版本号已经是 1.3.0。」改成「版本号已经是 1.3.1。」。在「也不要把 1.2.9 的产物标成 1.3.0。」之后加上「也不要把 1.3.0 的产物标成 1.3.1。」。第三步的「在该提交上打 tag `v1.3.0`」改成「在该提交上打 tag `v1.3.1`」。这一步仍不创建 tag，也不创建 Release。

- [ ] **Step 4: 在 CREDITS.md 增加 v1.3.1 小节，并改正张数**

第一节表格里「静态框图（22 张）」换成「静态框图（26 张）」。只有 `assets/diagrams/sample-16-standby.svg` 真的存在时才写成 27 张，并在实施 PR 说明里写明拆图原因。

「光栅动画（20 个 GIF）」换成「光栅动画（24 个 GIF）」。不要重跑已有 20 个 GIF。24 是 `BUILDERS` 的键数，不是 `*-zh.gif` 的张数。`assets/README.md` 里「同目录还有 20 个 *-zh.gif」那一句不要改。

第六节已有的小节标题和表都保留，含「第 12、13、14、15 章（v1.3.0）」。在该节末尾追加：

```markdown
### 第 16、17、18、19 章（v1.3.1）

第 16、17、18、19 章用改写吸收补了同样的四块。吸收的是事实，用本书的句子重写，并配上自绘静态图。手册正文、官方插图、灯珠厂商手册和 CAN 收发器厂商手册不放进仓库。

| 作品 | 许可证 | 用在 | 链接 |
| --- | --- | --- | --- |
| DS5319 Rev 20（2025-07），表 16、表 18、表 26，图 31，LSE 振荡器节 | ST 文档条款；只链接并改写事实，不转载手册 | 第 16 章 14 µA 与 24 µA；第 18 章 0.1 µF 和 5 pF 到 15 pF | https://www.st.com/resource/en/datasheet/stm32f103c8.pdf |
| RM0008 Rev 21（2021-02），电源控制 | ST 文档条款；只链接并改写事实，不转载手册 | 第 16 章退出 Stop 后回到 HSI | https://www.st.com/resource/en/reference_manual/rm0008-stm32f101xx-stm32f102xx-stm32f103xx-advanced-arm-based-32-bit-mcus-stmicroelectronics.pdf |
| PM0056，DEMCR bit 24 与 DWT_CYCCNT | ST 文档条款；只链接并改写事实，不转载手册 | 第 17 章 72 个计数是 1 µs，硬件断点是 6 个 | https://www.st.com/resource/en/programming_manual/pm0056-stm32f10xxx-cortex-m3-programming-manual-stmicroelectronics.pdf |
| 本仓库 `examples/freertos-task`、`examples/iap-bootloader` | MIT | 第 18 章 TIM4；第 19 章一张 `0xB800` | https://github.com/zhuguang-ZFG/STM32/tree/main/examples |
```

- [ ] **Step 5: 运行整套测试和构建检查**

Run: `python3 -m unittest discover stm32-book/tests -v`

Expected: OK。`test_sample_chapters.py`、`test_batch2_chapters.py`、`test_batch3_chapters.py`、`test_batch4_chapters.py`、`test_batch5_chapters.py` 仍然通过。

Run: `python3 stm32-book/build_html.py --check && python3 stm32-book/build_html.py --lang en --check`

Expected: 两个命令都退出码 0。构建出的 HTML 里有 `v1.3.1`，并且 `id="source-ds5319-pwr"`、`id="source-rm0008-pwr"`、`id="source-pm0056-dwt"`、`id="source-ds5319-nrst"`、`id="source-ds5319-lse"` 都在。

Run: `python3 tools/check_assets.py`

Expected: 退出码 0，输出含 `全部通过`。

- [ ] **Step 6: Commit**

```bash
git add CREDITS.md stm32-book/manifest.json stm32-book/manifest-en.json stm32-book/revisions.json stm32-book/README.md stm32-book/tests/test_build.py
git commit -m "book: 第 16、17、18、19 章登记来源并把整书标成 1.3.1"
```

### Task 11: Scope gate, then stop

**Files:**
- 不新增文件。这一任务只核对 diff。核对失败时，只撤销越界改动，不顺手加厚别的章，也不去改 CSS。

**Interfaces:**
- Consumes: Task 1 到 Task 10 的提交。
- Produces: 一份只含第 16、17、18、19 章加厚的 diff。用户复审之前，实施 PR 保持打开。没有 tag，没有 Release。Book CI 变绿不等于可以 squash 合入。

- [ ] **Step 1: 核对 diff 的路径**

Run:

```bash
git diff --name-only origin/main...HEAD
```

Expected: 只出现这些路径。顺序可以不同。`sample-16-standby.svg` 只有在 Task 3 真的拆图时才允许出现。

```text
CREDITS.md
assets/README.md
assets/diagrams/sample-16-stop-wake.svg
assets/diagrams/sample-17-cfsr.svg
assets/diagrams/sample-18-boot-triage.svg
assets/diagrams/sample-19-flash-fit.svg
assets/gif/boot0-low.gif
assets/gif/cfsr-read.gif
assets/gif/one-slot.gif
assets/gif/stop-wake.gif
docs/16-低功耗设计.md
docs/17-调试与性能优化.md
docs/18-常见问题FAQ.md
docs/19-项目实战合集.md
docs/en/16-low-power.md
docs/en/17-debug.md
docs/en/18-faq.md
docs/en/19-projects.md
docs/superpowers/plans/2026-10-25-batch6-16-17-18-19-lock.json
docs/superpowers/plans/2026-10-25-batch6-16-17-18-19-source-list.json
docs/superpowers/plans/2026-10-25-classic-encyclopedia-batch6-16-17-18-19.md
stm32-book/README.md
stm32-book/book/D-术语表.md
stm32-book/book/en/D-glossary.md
stm32-book/manifest-en.json
stm32-book/manifest.json
stm32-book/revisions.json
stm32-book/tests/test_batch6_chapters.py
stm32-book/tests/test_batch6_sources.py
stm32-book/tests/test_build.py
tools/gen_gifs.py
tools/gen_sample_figures.py
tools/scan_batch6_chapters.py
```

`docs/superpowers/plans/2026-10-25-classic-encyclopedia-batch6-16-17-18-19.md` 只在「先合并了本计划」的历史上出现。若实施分支从本计划提交切开，它会留在 diff 里，这是允许的。它不是章节正文。

`stm32-book/build_html.py`、`stm32-book/styles/book.css`、`stm32-book/styles/tokens.json`、`docs/CONTENT_GUIDE.md`、`docs/en/CONTENT_GUIDE.md`、`assets/video/`、`tools/gen_narrated.py`、`.github/workflows/book.yml`、样本锁定、Batch2 锁定、Batch3 锁定、Batch4 锁定、Batch5 锁定，以及其余章节都不在这份列表里。

- [ ] **Step 2: 核对附录、样式、海报和已经加厚的章没有被卷进来**

Run:

```bash
git diff origin/main...HEAD -- stm32-book/build_html.py stm32-book/styles/book.css stm32-book/styles/tokens.json stm32-book/book/A-工程深读.md stm32-book/book/en/A-uart-dma.md assets/video tools/gen_narrated.py docs/00-如何学习STM32.md docs/01-开发环境搭建.md docs/12-Flash与IAP升级.md docs/28-嵌入式系统与RTOS生态.md .github/workflows/book.yml
```

Expected: 无输出。

Run:

```bash
git diff --name-only origin/main...HEAD -- docs/02-时钟树.md docs/15-FreeRTOS入门.md docs/20-学习资源与工具链.md examples assets/animations/lowpower-wakeup.svg assets/animations/debug-swo.svg assets/animations/toolchain-flow.svg assets/boards/peripheral-wiring.svg assets/diagrams/sample-02-clock-tree.svg assets/diagrams/sample-12-iap-map.svg
```

Expected: 无输出。`peripheral-wiring.svg` 在 `assets/boards/`，不在 `assets/diagrams/`。

用锁定文件里的 `baseline` 核对已有来源对象没有被改字段。浅克隆里没有那个 SHA 时，先按 Batch5 的 `_fetch_baseline` 把它取回来，再 `git show`。不要假设 SHA 已经在本地，也不要为此把工作流的 checkout 改成全历史。

```bash
python3 - << 'PY'
import json, os, subprocess
from pathlib import Path
root = Path(".").resolve()
lock = json.loads((root / "docs/superpowers/plans/2026-10-25-batch6-16-17-18-19-lock.json").read_text(encoding="utf-8"))
rev = lock["baseline"]
env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
base = os.environ.get("GITHUB_BASE_REF", "main")
subprocess.run(["git", "fetch", "--depth=1", "origin", rev], check=False, env=env)
subprocess.run(
    ["git", "fetch", "--depth=50", "origin", f"+refs/heads/{base}:refs/remotes/origin/{base}"],
    check=False,
    env=env,
)
probe = subprocess.run(["git", "cat-file", "-e", f"{rev}^{{commit}}"], capture_output=True)
if probe.returncode != 0:
    raise SystemExit(f"baseline {rev} is not available after fetch")
frozen = [
    "rm0008", "ds5319", "rm0008-rcc", "rm0008-usart", "ds5319-usart", "ds5319-adc",
    "ds5319-gpio", "ds5319-swd", "ds5319-rtc", "rm0008-rtc", "rm0008-wdg",
    "pm0075-rdp", "pm0056", "pm0056-nvic", "rm0008-boot", "project-examples",
    "project-guide", "rm0008-adc", "rm0008-flash", "freertos-syscall",
]
for name in ("stm32-book/manifest.json", "stm32-book/manifest-en.json"):
    old = json.loads(subprocess.check_output(["git", "show", f"{rev}:{name}"], text=True))
    new = json.loads((root / name).read_text(encoding="utf-8"))
    for source_id in frozen:
        assert old["sources"][source_id] == new["sources"][source_id], source_id
print("frozen sources unchanged")
PY
```

Expected: 打印 `frozen sources unchanged`，退出码 0。

在 `stm32-book/build_html.py` 里确认 `display_chapter_number` 仍是文件名前缀加 1。本批 diff 对这个文件必须为空，所以这一条只是读，不改。

- [ ] **Step 3: 再跑一遍验收命令**

```bash
python3 -m unittest discover stm32-book/tests -v
python3 stm32-book/build_html.py --check
python3 stm32-book/build_html.py --lang en --check
python3 tools/check_assets.py
```

Expected: 四条命令都退出码 0。`check_assets.py` 的输出含 `全部通过`。

- [ ] **Step 4: 确认没有 tag 和 Release**

Run: `git tag --points-at HEAD`

Expected: 无输出。

不要运行 `gh release create`，不要 `git tag`，不要打 `v1.3.0` 或 `v1.3.1`。

- [ ] **Step 5: 停在用户复审**

实施 PR 的说明里写明：只加厚了文件 `16`、`17`、`18`、`19` 的中英八份；静态主图是 `sample-16-stop-wake.svg`、`sample-17-cfsr.svg`、`sample-18-boot-triage.svg`、`sample-19-flash-fit.svg`；短 GIF 是辅图。第 16 章是 Stop 低功耗稳压器 14 µA、主稳压器 24 µA，醒来是 HSI 8 MHz，`0x271` 在 8 MHz 上是 12800。第 17 章先看 CFSR，BFAR 要 bit 15 为 1 才有效，72 个 DWT 周期是 1 µs，要先置 DEMCR bit 24。第 18 章认不出芯片时先看第 34 脚、第 37 脚和第 44 脚 BOOT0；BOOT0=1 且 BOOT1=0 进的是 `0x1FFFF000`。第 19 章 C8 的一张 APP 是 `0xB800`，两张是 110 KB，`64×1024` 字节大于 20 KB SRAM。若表 16 的格子、表 26 的单位、电源控制的章名、DEMCR 的位号，或打开表 39 之后补进的上拉和清单不同，说明里写明差异。

请用户看构建出的中英 HTML 里的这四章：四块是否都在、关掉动画之后主图是否仍能指出失败、`#source-` 是否点得到附录 E 的卡片。

第 16 章要能指出的失败是「没把时钟装回 72 MHz，`0x271` 在 8 MHz 上变成 12800」。第 17 章要能指出的失败是「bit 15 为 0 仍读 BFAR，或 DEMCR bit 24 没置，周期差为 0」。第 18 章要能指出的失败是「BOOT0 为 1，CPU 在 `0x1FFFF000`，或者还没看线就改优化等级」。第 19 章要能指出的失败是「第二张 `0xB800` 画过了 `0x08010000`」。

用户书面接受之前：

- 不为 `00`–`15` 或 `20`–`28` 开加厚 PR。
- 不加图目录或表目录。
- 不改 `stm32-book/build_html.py`，不改 `book.css`，不改显示章号，不改 PDF 书签深度。
- 不改 `assets/video/`，不重录旁白，不重画 29 张讲解海报。
- 不打 `v1.3.1` 的 tag，不创建 GitHub Release。
- 不把 Book CI 变绿当成可以自动 squash 合入。人接受之前，实施 PR 保持打开。
- 不预选文件 `20` 或 `28`。下一批仍是 4 章，到下一次设计再锁。

这一步没有新的提交。若 Step 1 到 Step 3 发现越界文件，撤销那些文件里的越界改动后再提交一次，提交说明写明撤回了哪一处，然后仍停在这里。

## 对照设计规格

| 设计规格里的要求 | 落在 |
| --- | --- |
| 只加厚 16、17、18、19，中英一起，四块标题各一次。文件 19 的标题保持「项目实战合集」 | Task 5、Task 6、Task 7、Task 8、Task 11 |
| 第 16、17 章删除旧坑标题。第 18、19 章本来没有，实施后也不新造，也不新造核心原理标题 | Task 1、Task 5、Task 6、Task 7、Task 8 |
| 静态主图，正常路径和失败路径，不用 `Svg.footer()`，小于 60 KB | Task 3 |
| 第 16 章超过 60 KB 才拆 `sample-16-standby.svg`，静态框图改为 27 张 | Task 3、Task 10 |
| 短 GIF 只是辅图，帧数 3 到 12，不改已有 20 个 BUILDERS 的像素 | Task 4 |
| 第 16 章 14 µA 与 24 µA、HSI 8 MHz、`0x271` 是 12800，F4 周期唤醒定时器作废，四块不写 780 天 | Task 5 |
| 第 17 章四个故障地址、bit 15、bit 24、72 个计数是 1 µs、6 个硬件断点，四块不写 167 ns | Task 6 |
| 第 18 章 38 条、第 34/37/44 脚、`0x1FFFF000`、0.1 µF、6 pF 不是必须值、TIM4、`0x50`，删掉 90% | Task 7 |
| 第 19 章一张 `0xB800`、两张是 110 KB、65536 大于 20480、分母 4096、133 不是 64 字节包，`0x5A5A0001` 留在草稿 | Task 8 |
| 附录 D 只改「Stop 之后的时钟」的 F103 电流句子。比对基线的测试先 fetch 那个 SHA | Task 9、本计划文首 |
| 新 id 只追加五个；已有 id 一个字段都不改 | Task 2、Task 5、Task 6、Task 7、Task 11 |
| 版本 1.3.1 · 2026-10-25，不打 tag，不发 Release。本计划提交不升版本 | Task 10、Task 11 |
| 不改 CSS、海报、`assets/video/`、旁白、附录 A、`build_html.py`、工作流的 fetch-depth、更早的锁定和其余章 | Task 11 |
| 书签仍是 44，`0x271` 与 `167 ns` 断言仍在，样本测试和 Batch2 到 Batch5 测试不放宽 | Task 10 |
| CI 变绿后停下来等人复审，不自动合入 | Task 11 |
| 不预选文件 20 或 28 | Task 11 |

## 执行交接

计划写在 `docs/superpowers/plans/2026-10-25-classic-encyclopedia-batch6-16-17-18-19.md`。本计划 PR 只增加这一份文件。实施时二选一，而且要等这份计划被人接受之后再开实施 PR：

1. Subagent-Driven（推荐）：每个任务一个新的子代理，任务之间复核。必用 superpowers:subagent-driven-development。
2. Inline Execution：在同一个会话里按 superpowers:executing-plans 分批做，每批停下来复核。

无论哪一种，Task 11 都停在人复审。人接受之前不合入。实施 PR 的目标版本是 1.3.1 · 2026-10-25。这一份计划本身不升版本，不改章节正文，不提交 SVG 或 GIF。

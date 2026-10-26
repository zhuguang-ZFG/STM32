# Batch 7 Chapters 20, 21, 22, and 23 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

I'm using the writing-plans skill to create the implementation plan.

**Goal:** 只加厚第 20、21、22、23 章（中文和英文一起），写成和第 00 到第 19 章相同的四块密度，每章一张可印刷的静态主图加一条短 GIF 辅图，把 PM0056 的封装误称、丢掉 `(PSC+1)` 的 72000 Hz、读允许键 `0xAA`、ZET6 被套上 C8 的系统存储器、灯亮被当成 115200，以及 G071RB 第 1 脚被数成 VBAT，改成和已冻结手册以及罗盘同一笔账，合入时把整书升到 1.3.2 · 2026-10-25，然后停下来等人复审。人接受之前不合入。

**Architecture:** 章号已经由设计锁死，不再打分重选，也不拆成四份计划。四章共用一次版本号、一次来源追加和一次人审。先只读这四章的中英八份，确认四块还不存在。第 20 章和第 21 章的旧坑标题还在，而且英文分别是 `Common traps and how to check them` 与 `Pitfalls`。第 22 章和第 23 章没有 `常见坑与排查`，它们自己的坑标题要留下。仓库里没有 `## ⚠️ Pitfalls and troubleshooting`，不要为了删它先造出来。来源清单在 Task 2 按本计划里的 JSON 落盘，不在本计划提交里预先写入。然后生成静态 SVG 和短 GIF，再改八份正文。九个新出处在 Task 6 按本计划的固定顺序追加进 `stm32-book/manifest.json` 与 `stm32-book/manifest-en.json` 的 `sources` 末尾，避免按章追加把 `rm0008-map` 排到 `ds5792` 后面。附录 E 的卡片仍由 `stm32-book/build_html.py` 的 `source_registry_html()` 生成。主图走 `tools/svgkit.py` 的 `tools/gen_sample_figures.py`。短 GIF 走 `tools/gen_gifs.py` 的 `BUILDERS`。版本号同时写进两份 manifest、`stm32-book/revisions.json` 和 `stm32-book/README.md`。日期写死 `2026-10-25`，不取实施当天的日期。代理日历若显示 2026-10-26，书的日期仍写 2026-10-25。

**Tech Stack:** Python 3 标准库、现有 `stm32-book/build_html.py`、`python3 -m unittest`、`tools/svgkit.py`、`tools/gen_gifs.py`、`tools/minigfx.py`、`tools/check_assets.py`。不新增依赖，不改 `requirements.txt`。

单文件测试写成 `python3 stm32-book/tests/<file>.py -v`。`stm32-book/tests/` 不是 Python 包。整套测试仍用 `python3 -m unittest discover stm32-book/tests -v`。

本计划不拆成四个子计划。设计规格把这四章锁成同一批，版本只升一次到 1.3.2。拆开会把一次人审拆成四次，或者让 1.3.2 先带着不完整的四章合入。

本文件是实施计划。它不改章节正文，不画 SVG，不生成 GIF，不改 `stm32-book/` 的版本号。那些步骤留在后续实施 PR。人接受本计划之前，不要开实施 PR。

Book CI 的 `actions/checkout` 没有写 `fetch-depth`，默认深度是 1。回归测试若用 `git show <锁定文件里的 baseline SHA>:<路径>` 去比对视频块或附录 D，浅克隆里没有那个提交，`git show` 会失败。凡是这种比对，都要先按 Batch5 已经落在 `stm32-book/tests/test_batch5_chapters.py` 里、Batch6 又抄进 `test_batch6_chapters.py` 的 `_fetch_baseline()` 把那个 SHA 取回来：先 `git fetch --depth=1 origin <rev>`，仍没有再 `git fetch --depth=50 origin +refs/heads/$GITHUB_BASE_REF:refs/remotes/origin/$GITHUB_BASE_REF`（`GITHUB_BASE_REF` 缺省时用 `main`）。不要把工作流的 checkout 改成全历史，也不要假设 SHA 已经在本地。Task 5 把这组函数放进 `test_batch7_chapters.py`。后面的任务调用 `baseline_chapter()`，不要再写裸的 `git show`。

## Global Constraints

- 只把第 20、21、22、23 章加厚到和第 00 到第 19 章相同的四块密度。中文和英文一起写完。文件名仍是 `docs/20-学习资源与工具链.md`、`docs/en/20-resources.md`、`docs/21-原理图与实物图鉴.md`、`docs/en/21-board-maps.md`、`docs/22-仿真实验Wokwi与Renode.md`、`docs/en/22-simulation-wokwi-renode.md`、`docs/23-STM32G0引脚.md`、`docs/en/23-stm32g0-pins.md`。一级标题继续是 `20 学习资源与工具链`、`21 原理图与实物图鉴`、`22 仿真实验：Wokwi 与 Renode`（冒号是全角 `：`）、`23 STM32G0 引脚（G071RB）`。英文继续是 `20 Learning resources and the toolchain`、`21 Schematics and board maps`、`22 Simulation labs: Wokwi and Renode`、`23 STM32G0 pins (G071RB)`。不要把第 21 章改成「图注」，不要把第 22 章改成「仿真实战」，不要改成第 28 章的 RTOS 生态。
- 四块标题必须原样出现，各一次：中文 `## 原理与边界`、`## 关键插图`、`## 时序或状态`、`## 坑与出处卡`；英文 `## Principle and boundary`、`## Key figures`、`## Timing or state`、`## Pitfalls and source cards`。标题不加表情符号。四块插在 `<!-- /video:chNN -->` 之后、该章现有的学习目标标题之前。第 21 章在视频结束和学习目标之间已有一段「不是实拍」的引用块，四块插在那段引用块之后、学习目标之前，不把引用块搬进视频标记里面。
- 保留学习目标、硬件与接线、代码实现、动手实验、相关资源，以及英文文件里已经在用的对应标题。不要把英文标题改成另一章的措辞。在 `3b16a93fe0471e818cbbc6e0d6fbbabaa2e7f5ff` 上：中文四章的学习目标都是 `## 📌 学习目标`。英文第 20 章和第 22 章是 `## 📌 Learning goals`。英文第 21 章和第 23 章是 `## 📌 Goals`。第 20 章保留 `## 🧠 核心原理` 和 `## 🧠 Core ideas`。第 21 章保留 `## 🧠 核心原理` 和 `## 🧠 The boards`。第 22 章保留 `## 🧠 先选哪一家` 和 `## 🧠 Which one to open first`，不要新造「核心原理」。第 23 章保留 `## 🧠 这颗料是谁` 和 `## 🧠 Which part this is`。第 22 章中英都没有 `## 💻 代码实现` 或 `## 💻 Code`，不要补一个空的代码节。
- 旧坑标题只在第 20 章和第 21 章删除，不留空标题。第 20 章中文是 `## ⚠️ 常见坑与排查`，英文是 `## ⚠️ Common traps and how to check them`。第 21 章中文是 `## ⚠️ 常见坑与排查`，英文是 `## ⚠️ Pitfalls`。第 22 章保留 `## ⚠️ 仿真替不了的事` 和 `## ⚠️ What simulation will not do for you`。第 23 章保留 `## ⚠️ 从 F1 抄代码时最容易摔的几处` 和 `## ⚠️ Common ways an F1 port falls over`。实施后八份都不要新出现 `## ⚠️ Pitfalls and troubleshooting`。
- 每章一张可印刷的静态主图：正常路径和失败路径都在图上。生成脚本是 `tools/gen_sample_figures.py`，画布是 `tools/svgkit.py`。不调用 `Svg.footer()`。落款用已有的 `_credit()`：左侧是文档号，右侧是「自绘 · 静态 · CC BY 4.0」。没有 `<animate`、`@keyframes`、`animation:`。图注写「自绘」，英文图注写 `Drawn for this book`。替代文本写结论。单张小于 60 KB。放不下就拆成主图加局部，每张仍争取小于 60 KB。第 21 章的第二张只允许叫 `assets/diagrams/sample-21-other-parts.svg`。第 23 章的第二张只允许叫 `assets/diagrams/sample-23-pc13.svg`。第 20 章和第 22 章不另起第二张文件名。不允许第三张。拆开仍超过时，在实施 PR 里写出字节数和原因，不把图画回简笔，也不把 60 KB 改成仓库新默认值。
- 另加一条短 GIF，只做网页和公众号辅图。GIF 不替换主图，也不是关键插图这一节唯一的图。四条都走 `tools/gen_gifs.py`，加入 `BUILDERS`。`minigfx.py` 只有 5×7 英文点阵，GIF 上的字用 ASCII。每条少于 500 KB。帧数不少于 3、不多于 12。`gen_gifs.chrome()` 自带的页脚可以留在 GIF 里。那条页脚不是静态主图的 `Svg.footer()`。
- 改写吸收的许可顺序：先用 ST 公开 RM/DS/PM/UM/AN 的事实、用自己的话重写；然后才是 MIT、BSD-2-Clause、BSD-3-Clause、ISC、CC BY 4.0、CC BY 3.0、CC0。GPL、LGPL、CC BY-NC、CC BY-ND、Apache-2.0、保留所有权利、未写许可的材料只留链接。不把厂商手册、官方插图或社区原文放进仓库。正点原子、野火、CSDN、Wokwi 文档、Renode 文档、WeAct 仓库都只留链接。Wokwi 或 Renode 的许可证若打开后落在可吸收名单里，这一批仍不新开 id。
- 订货号：第 20、21、22 章举例仍是 STM32F103C8T6，LQFP48。第 23 章是 STM32G071RB，LQFP64。读者看到的章号仍是文件名前缀加 1。源文件的一级标题继续带 `20`、`21`、`22`、`23`。这一批不改这个加 1。文件 `20` 在书里是第 21 章，`21` 是第 22 章，`22` 是第 23 章，`23` 是第 24 章。
- 第 20 章四笔账：PM0056 Rev 7 是 Cortex-M3 编程手册，不是封装手册。`CFSR` 在 `0xE000ED28`。频率是 `fCK_PSC / ((ARR+1) × (PSC+1))`。计数时钟 72 MHz，PSC = 71，ARR = 999，CCR = 500：`72e6 / (72 × 1000) = 1000` Hz，占空比 `500 / 1000 = 50%`。丢掉 `(PSC+1)` 得到 `72e6 / 1000 = 72000` Hz。读允许键的低字节是 `0xA5`，手册印成 `0x00A5`，选项字节在 `0x1FFFF800`。写回这个键会先整片擦除主闪存。`0xAA` 不是这只键。第 30 脚 PA9、第 31 脚 PA10 在 DS5319。BRR `0x271` 的位在 RM0008。72 MHz 下是 115200，8 MHz 下是 12800。AN4031 的 FIFO 不回答这颗 C8。四块不写 90%。人民币预算和 OpenOCD 端口 3333 不进出处卡。G0 的内核手册不是 PM0056。这一批不打开 PM0223。
- 第 21 章四笔账：`DBGMCU_IDCODE` 在 `0xE0042000`，低 12 位是 `0x410`。`0x1FFFF7E0` 的低 16 位读 64，单位 KB。UID 从 `0x1FFFF7E8` 起。DS5319：闪存 64 KB，SRAM 20 KB。丝印写 128 KB、读数却不是 64 时，不要按 C8 往下算。STM32F103ZET6 在 DS5792 的 xE 行：512 KB 闪存、64 KB SRAM、72 MHz、LQFP144。系统存储器默认从 `0x1FFFB000` 起，不是 C8 的 `0x1FFFF000`。xC 的 256 KB / 48 KB 和 xD 的 384 KB 在 ZET6 上作废。STM32F411CEU6 与 STM32F411RET6 是 DS10314 的 xE：512 KB 闪存、128 KB SRAM、最高 100 MHz。xC 的 256 KB 在这两只订货号上作废。`PLLM=8`、`N=200`、`P=2` 不是 DS10314 的格子，四块不写。晶振允许 4 MHz 到 26 MHz。BlackPill 的 25 MHz 是板级说法。STM32F407VGT6 在 DS8626：1 MB 闪存，最高 168 MHz，SRAM 最高 192 KB（含 64 KB CCM），另加 4 KB 备份 SRAM。4 KB 不并进 192，也不写成 196 KB 的主 SRAM。LSE 是 5 pF 到 15 pF，6 pF 不是必须值。HSE 的负载电容按 5 pF 到 25 pF 跟晶振选，20 pF 不是必须值。NRST 的外部电容是 0.1 µF。10 kΩ 不进出处卡。外接灯是第 10 脚、270 Ω。PA5 加 330 Ω 不是本书的外接灯。第 2 脚 PC13 不能当电流源。
- 第 22 章四笔账：USART1 在 `0x40013800`。GPIOC 在 `0x40011000`。GPIOA 在 `0x40010800`，GPIOB 在 `0x40010C00`，这两格写进 `rm0008-map`，主图可以不画。`usart1` 说成 USART2 是失败路径。Wokwi 键 `C13` 指到第 2 脚 PC13，低电平点亮，只能灌电流。键 `A0` 指到第 10 脚 PA0。主图不把第 03 章的灯、第 09 章的 ADC 和第 16 章的 WKUP 画成同时有效。键 `A9` / `A10` 指到第 30 脚 PA9、第 31 脚 PA10。图里写成 `PA0` 或 `PC13` 这种芯片名，对不上这张图的键。`0x271` 在 72 MHz 上是 115200，在 8 MHz 上是 12800。灯会闪，只证明 GPIO 在动。7 位地址 `0x3C`，HAL 填 `0x78`，`0x3C << 1 = 0x78`，上拉 4.7 kΩ。当前 Wokwi BluePill 模型没有 DMA。这是模型边界，不是新的芯片限额。端口 3456 留在动手实验，不进出处卡，也不新开 id。
- 第 23 章四笔账：STM32G071RB，R = 64 脚，B = 128 KB 闪存。SRAM 是 32 KB（带硬件奇偶）或 36 KB（不用奇偶）。36 KB 不是 32 加 36，也不写成 68 KB。最高 64 MHz，Cortex-M0+，供电 1.7 V 到 3.6 V。LQFP64 第 1 脚是 PC11，第 6 脚才是 VBAT，第 12 脚是 PF2-NRST，第 3 脚是 PC13。PC13、PC14、PC15 只能灌大约 3 mA，输出不超过 2 MHz，负载不超过 30 pF，不能当电流源去点灯。第 45 脚是 PA13，复位后内部上拉。第 46 脚是 PA14-BOOT0，与 SWCLK 是同一只脚，复位后内部下拉。第 36 脚 PA8 是 UCPD1_CC1，第 35 脚 PB15 是 UCPD1_CC2。没有 CAN。USB 是 UCPD，不是 F1 的全速设备。`BOOT_LOCK=1` 强制主闪存。`nBOOT_SEL=0` 才看 PA14。四块不写待机微安。不把 F103 的 `0x1FFFF000` 画进这一章的主图。
- 实施合入时把整书从 1.3.1 升到 **1.3.2**。中英文整书共用这个版本号。日期写死 **2026-10-25**。`accessed` 也写死 `2026-10-25`。不写成 1.3.1.1。不打 tag，不创建 GitHub Release。本计划提交不升版本。
- Book CI 变绿之后停下来等人复审。复审对象是构建出的中英 HTML 里的这四章。人接受之前不合入，也不开下一批章。CI 变绿不等于可以自动 squash 合入。
- 实施基线是 #60 合入之后的 `main` 尖端。写本计划时该尖端是 `3b16a93fe0471e818cbbc6e0d6fbbabaa2e7f5ff`（`docs: Batch7 第 20–23 章加厚设计（资源、图鉴、仿真、G0） (#60)`）。其章节正文与 v1.3.1 `ef5a0884f159790d1bb03627722b889cfc4b2b02` 相同，只多了设计规格。Task 1 写出的 `baseline` 是运行时的 `git rev-parse HEAD`。那个 HEAD 必须还没有四块，也还没有这九个新 `sources`。
- 不加厚除 20、21、22、23 以外的任何章，含 00–19 和 24–28。不重选样本。不改 `docs/superpowers/plans/` 里已有的锁定文件和来源清单。不改 `tools/scan_sample_chapters.py`、`tools/scan_batch2_chapters.py`、`tools/scan_batch3_chapters.py`、`tools/scan_batch4_chapters.py`、`tools/scan_batch5_chapters.py`、`tools/scan_batch6_chapters.py`。不改总纲、Batch2 到 Batch6 规格、观感规格、海报规格、密度规格、CONTENT_GUIDE 规格，也不改两份 `CONTENT_GUIDE.md`。不改本批设计规格 `docs/superpowers/specs/2026-10-25-classic-encyclopedia-batch7-20-21-22-23-design.md`。
- 不改 `stm32-book/build_html.py`。出版书签仍是现在的 44 条。不把新的二级标题收进书签。不改密度刀 F 的令牌、`stm32-book/styles/book.css`、`stm32-book/styles/tokens.json` 和间距。不把样式、字号、行长或页边再收一刀。
- 附录 D 这一批的 diff 为空。不改 `stm32-book/book/D-术语表.md`，不改 `stm32-book/book/en/D-glossary.md`。「这颗料」那一行已经写着 `0x410` 和 `0x1FFFF7E0`，G0 那一行已经写着第 1 脚 PC11。不改附录 A。不手改 `stm32-book/book/E-参考资料.md` 或英文对应文件。不删 `test_build.py` 里 `0x271`、`167 ns`、账本名和出版书签长度为 44 的断言。不放宽 `test_sample_chapters.py`、`test_batch2_chapters.py`、`test_batch3_chapters.py`、`test_batch4_chapters.py`、`test_batch5_chapters.py` 或 `test_batch6_chapters.py`。不新增读取 `CONTENT_GUIDE.md` 的测试。不改 CSS 哈希一类的视觉契约。
- 不删除、不重画已有图。第 20 章留下 `assets/diagrams/project-structure.svg`。第 21 章留下这 7 张：`assets/boards/bluepill-stm32f103c8t6.svg`、`assets/boards/blackpill-stm32f411ce.svg`、`assets/boards/nucleo-f411re.svg`、`assets/boards/f4-discovery.svg`、`assets/boards/f103zet6-dev.svg`、`assets/boards/pinout-bluepill.svg`、`assets/boards/peripheral-wiring.svg`。第 22 章留下 `assets/animations/toolchain-flow.svg`。第 23 章留下 `assets/boards/pinout-stm32g071rb-lqfp64.svg` 和 `assets/animations/g0-boot-swd.svg`。不重画 `sample-00` 到 `sample-19` 的任何一张。不改已有 24 个 BUILDERS 的像素：`led-blink`、`pwm-breath`、`uart-bits`、`i2c-timing`、`dma-ring`、`sar-adc`、`nvic-preempt`、`uart-idle`、`clock-css`、`pwm-1khz`、`spi-jedec`、`adc-sample`、`swd-fetch`、`i2c-addr`、`dma-cndtr`、`iwdg-1s`、`iap-jump`、`can-500k`、`usb-48m`、`rtos-tick`、`stop-wake`、`cfsr-read`、`boot0-low`、`one-slot`。不把 `tools/svg2gif.py` 当成必经步骤。不改 `assets/video/`，不改 `tools/gen_narrated.py`。`<!-- video: -->` 与 `<!-- /video: -->` 之间的旁白保持原样。旁白不重录。旁白里若仍把 PM 说成别的书，也不在这一批改字幕。不重画 29 张讲解海报。
- 新来源 id 只追加，顺序固定为 `rm0008-signature`、`rm0008-map`、`rm0008-hd-boot`、`ds5792`、`ds10314`、`ds8626`、`ds5319-hse`、`um1724-mco`、`ds12232-lqfp64`。没有第十个 id。已有 id 的对象一个字段都不改。中英两份 manifest 的 `url`、`snapshot`、`license`、`accessed` 用同一串字符；`title`、`authority`、`scope` 用对应语言。
- 代码继续按 `docs/CONTENT_GUIDE.md`：HAL，参数用宏。不新开可烧录工程。不改 `examples/`，不改 `sim/`。第 20 章若还留着可复制的 `RDP=0xAA`，读者会把它当成选项字节。实施后八份正文都不得再出现 `RDP=0xAA`。四块仍要写出 `0xAA` 不是读允许键。
- 不加图目录或表目录，不加第 30 章，不改 `docs/00`–`28` 的文件名。不预选文件 `24` 或 `28` 作为下一批。
- 同一只第 10 脚：第 03 章主张外接灯。第 09 章主张 ADC。第 16 章主张 Stop 的按键。第 22 章的 `A0` 只表示仿真键指到这只脚。四张图都不把两种功能画成同时有效。不重画第 02 章的时钟树，不重画第 05 章的 PWM，不重画第 06 章的帧，不重画第 07 章的地址字节，不重画第 17 章的 CFSR，不重画第 18 章的 BOOT0 图。167 ns、21 µs、17.2%、14 µA、24 µA 不进这四章的四块。

## File map

| 路径 | 责任 |
| --- | --- |
| `tools/scan_batch7_chapters.py` | 只读 20、21、22、23 的中英八份。四块必须缺失。第 20、21 章的旧坑标题必须还在，英文标题按章区分。第 22、23 章不得有 `常见坑与排查`。八份都不得有 `## ⚠️ Pitfalls and troubleshooting` |
| `docs/superpowers/plans/2026-10-25-batch7-20-21-22-23-lock.json` | Task 1 运行时写出。`baseline` 等于当时的 `git rev-parse HEAD`。本计划提交不包含这份文件 |
| `docs/superpowers/plans/2026-10-25-batch7-20-21-22-23-source-list.json` | Task 2 按下面的 JSON 落盘。九个 absorb id，社区列表为空。登记以 manifest 为准 |
| `tools/gen_sample_figures.py` | 在现有二十张静态主图之外追加四张。不改已有二十个函数，不改 `_credit` |
| `assets/diagrams/sample-20-which-manual.svg` | 第 20 章主图 |
| `assets/diagrams/sample-21-which-part.svg` | 第 21 章主图。C8 与 ZET6 |
| `assets/diagrams/sample-22-sim-boundary.svg` | 第 22 章主图 |
| `assets/diagrams/sample-23-g071-pins.svg` | 第 23 章主图。只钉这一次要核对的脚 |
| `assets/diagrams/sample-21-other-parts.svg` | 只有第 21 章主图达到或超过 60 KB 时才允许出现 |
| `assets/diagrams/sample-23-pc13.svg` | 只有第 23 章主图达到或超过 60 KB 时才允许出现 |
| `tools/gen_gifs.py` | `BUILDERS` 末尾追加 `which-manual`、`which-part`、`sim-usart`、`g071-pin1`。不改已有二十四个函数 |
| `assets/gif/which-manual.gif` | 第 20 章辅图。只画第 30 脚到 PA9，再标 `0xA5` |
| `assets/gif/which-part.gif` | 第 21 章辅图。只画 `0x410` 和 64，旁边标 ZET6 的 512 KB 不在这一格 |
| `assets/gif/sim-usart.gif` | 第 22 章辅图。只画键 `C13`、第 2 脚和 115200 |
| `assets/gif/g071-pin1.gif` | 第 23 章辅图。只画第 1 脚 PC11 和第 46 脚 PA14 |
| `assets/README.md` | 登记四张 SVG 和四条 GIF。开头那行注释从「第 00 到第 19 章」改为「第 00 到第 23 章」。第五节「上面 24 张」改为「上面 28 张」 |
| 八份章节 Markdown | 四块，以及和罗盘、手册冲突的那几格。视频块字节不变 |
| `stm32-book/manifest.json` 与 `stm32-book/manifest-en.json` | 九个新 `sources`、四章罗盘、版本号 |
| `stm32-book/revisions.json` | 1.3.2 修订条目，插在数组最前 |
| `stm32-book/README.md` | 当前版本句，以及「也不要把 1.3.1 的产物标成 1.3.2」 |
| `CREDITS.md` | 第六节下面增加 v1.3.2 小节。静态框图张数改为 30。若拆出第二张 SVG，改为 31，并写明是哪一张。光栅动画个数改为 28 |
| `stm32-book/tests/test_batch7_sources.py` | 来源清单的许可门 |
| `stm32-book/tests/test_batch7_chapters.py` | 四块、共享数字、主图、GIF、视频块字节、附录 D 逐字节不变。视频块和附录 D 的基线比对必须先 fetch |
| `stm32-book/tests/test_build.py` | 只改当前版本断言。`0x271` 和书签条数保留 |

---

### Task 1: Gap scan and lock

**Files:**
- Create: `tools/scan_batch7_chapters.py`
- Create: `docs/superpowers/plans/2026-10-25-batch7-20-21-22-23-lock.json`（脚本在退出码 0 时写出。本计划提交里还没有它）

**Interfaces:**
- Consumes: 八份原稿。不读别的章，不调用 `tools/scan_sample_chapters.py`，也不调用 `scan_batch2` 到 `scan_batch6`。
- Produces: 锁定文件字段 `rubric`（字符串 `"2026-10-25-classic-encyclopedia-batch7-20-21-22-23"`）、`baseline`（40 位十六进制，等于运行时 `git rev-parse HEAD`）、`chapters`（`["20", "21", "22", "23"]`）、`four_blocks_absent`（`true`）、`old_pitfall_heading_present`（`true`，只表示第 20 章和第 21 章的旧标题还在）、`chapters_without_old_pitfall`（`["22", "23"]`）、`files`。`files` 的键是 `"20"`、`"21"`、`"22"`、`"23"`。每个值有 `zh`、`en`、`zh_four_blocks`、`en_four_blocks`、`expects_old_pitfall`、`zh_old_pitfall`、`en_old_pitfall`、`en_old_heading`、`zh_kept_heading`、`en_kept_heading`、`kept_heading_present`。后面的任务只改这四个前缀。

四块标题是中文 `## 原理与边界`、`## 关键插图`、`## 时序或状态`、`## 坑与出处卡`，英文 `## Principle and boundary`、`## Key figures`、`## Timing or state`、`## Pitfalls and source cards`。

旧坑标题按文件区分。判定用整行相等，不用子串。`## ⚠️ Pitfalls` 不得误匹配 `## ⚠️ Pitfalls and troubleshooting`。

| 前缀 | 中文旧标题 | 英文旧标题 | 必须还在 | 必须留下的标题 |
| --- | --- | --- | --- | --- |
| `20` | `## ⚠️ 常见坑与排查` | `## ⚠️ Common traps and how to check them` | 是 | 无 |
| `21` | `## ⚠️ 常见坑与排查` | `## ⚠️ Pitfalls` | 是 | 无 |
| `22` | `## ⚠️ 常见坑与排查` | `## ⚠️ Pitfalls and troubleshooting` | 否 | `## ⚠️ 仿真替不了的事` / `## ⚠️ What simulation will not do for you` |
| `23` | `## ⚠️ 常见坑与排查` | `## ⚠️ Pitfalls and troubleshooting` | 否 | `## ⚠️ 从 F1 抄代码时最容易摔的几处` / `## ⚠️ Common ways an F1 port falls over` |

在 `3b16a93fe0471e818cbbc6e0d6fbbabaa2e7f5ff` 上，这八份都还没有四块。第 20、21 章的旧坑标题都还在。第 22、23 章没有 `常见坑与排查`，但有上表最后一列的标题。八份都没有 `## ⚠️ Pitfalls and troubleshooting`。若执行时任何一份已经有四块，或者第 20、21 章的旧标题已经不在，或者第 22、23 章出现了 `常见坑与排查`，或者任何一份出现了 `## ⚠️ Pitfalls and troubleshooting`，或者第 22、23 章要留下的标题不在，脚本退出码 2，不改写锁定文件，后面的任务停。

- [ ] **Step 1: 写入核对脚本**

把下面的程序保存为 `tools/scan_batch7_chapters.py`。

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Confirm chapters 20, 21, 22, and 23 are still missing the four blocks.

Run from the repository root:

    python3 tools/scan_batch7_chapters.py

Rewrites docs/superpowers/plans/2026-10-25-batch7-20-21-22-23-lock.json and
exits 0 when all eight manuscripts lack the four headings. Chapters 20 and 21
must still have their own old pitfall headings. Chapters 22 and 23 must not
have the generic pitfall heading, and must still have the headings this batch
keeps. Exits 2 without writing the lock otherwise.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch7-20-21-22-23-lock.json"
FILES = {
    "20": {
        "zh": ROOT / "docs" / "20-学习资源与工具链.md",
        "en": ROOT / "docs" / "en" / "20-resources.md",
        "en_old": "## ⚠️ Common traps and how to check them",
        "expects_old": True,
        "zh_kept": "",
        "en_kept": "",
    },
    "21": {
        "zh": ROOT / "docs" / "21-原理图与实物图鉴.md",
        "en": ROOT / "docs" / "en" / "21-board-maps.md",
        "en_old": "## ⚠️ Pitfalls",
        "expects_old": True,
        "zh_kept": "",
        "en_kept": "",
    },
    "22": {
        "zh": ROOT / "docs" / "22-仿真实验Wokwi与Renode.md",
        "en": ROOT / "docs" / "en" / "22-simulation-wokwi-renode.md",
        "en_old": "## ⚠️ Pitfalls and troubleshooting",
        "expects_old": False,
        "zh_kept": "## ⚠️ 仿真替不了的事",
        "en_kept": "## ⚠️ What simulation will not do for you",
    },
    "23": {
        "zh": ROOT / "docs" / "23-STM32G0引脚.md",
        "en": ROOT / "docs" / "en" / "23-stm32g0-pins.md",
        "en_old": "## ⚠️ Pitfalls and troubleshooting",
        "expects_old": False,
        "zh_kept": "## ⚠️ 从 F1 抄代码时最容易摔的几处",
        "en_kept": "## ⚠️ Common ways an F1 port falls over",
    },
}
ZH_BLOCKS = ("## 原理与边界", "## 关键插图", "## 时序或状态", "## 坑与出处卡")
EN_BLOCKS = (
    "## Principle and boundary",
    "## Key figures",
    "## Timing or state",
    "## Pitfalls and source cards",
)
ZH_OLD = "## ⚠️ 常见坑与排查"
FORBIDDEN = "## ⚠️ Pitfalls and troubleshooting"


def has_line(text: str, heading: str) -> bool:
    if not heading:
        return False
    return any(line.strip() == heading for line in text.splitlines())


def four_blocks(text: str, headings: tuple[str, ...]) -> bool:
    return any(has_line(text, heading) for heading in headings)


def main() -> int:
    payload_files: dict[str, dict] = {}
    blocked = False
    for prefix, spec in FILES.items():
        zh_path = spec["zh"]
        en_path = spec["en"]
        if not zh_path.is_file() or not en_path.is_file():
            print(f"missing manuscript for {prefix}", file=sys.stderr)
            return 2
        zh = zh_path.read_text(encoding="utf-8")
        en = en_path.read_text(encoding="utf-8")
        kept_ok = True
        if spec["zh_kept"]:
            kept_ok = has_line(zh, spec["zh_kept"]) and has_line(en, spec["en_kept"])
        row = {
            "zh": zh_path.relative_to(ROOT).as_posix(),
            "en": en_path.relative_to(ROOT).as_posix(),
            "zh_four_blocks": four_blocks(zh, ZH_BLOCKS),
            "en_four_blocks": four_blocks(en, EN_BLOCKS),
            "expects_old_pitfall": spec["expects_old"],
            "zh_old_pitfall": has_line(zh, ZH_OLD),
            "en_old_pitfall": has_line(en, spec["en_old"]),
            "en_old_heading": spec["en_old"],
            "zh_kept_heading": spec["zh_kept"],
            "en_kept_heading": spec["en_kept"],
            "kept_heading_present": kept_ok,
        }
        payload_files[prefix] = row
        if row["zh_four_blocks"] or row["en_four_blocks"]:
            print(f"{prefix} already has a four-block heading; stop", file=sys.stderr)
            blocked = True
        if has_line(zh, FORBIDDEN) or has_line(en, FORBIDDEN):
            print(f"{prefix} already has the unused English pitfall heading; do not invent it", file=sys.stderr)
            blocked = True
        if spec["expects_old"] and (not row["zh_old_pitfall"] or not row["en_old_pitfall"]):
            print(f"{prefix} is missing the old pitfall heading; stop", file=sys.stderr)
            blocked = True
        if (not spec["expects_old"]) and row["zh_old_pitfall"]:
            print(f"{prefix} already has the generic pitfall heading; do not invent one to delete", file=sys.stderr)
            blocked = True
        if (not spec["expects_old"]) and not kept_ok:
            print(f"{prefix} is missing the heading this batch keeps", file=sys.stderr)
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
        "rubric": "2026-10-25-classic-encyclopedia-batch7-20-21-22-23",
        "baseline": baseline,
        "chapters": ["20", "21", "22", "23"],
        "four_blocks_absent": True,
        "old_pitfall_heading_present": True,
        "chapters_without_old_pitfall": ["22", "23"],
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

Run: `python3 tools/scan_batch7_chapters.py`

Expected: 退出码 0，标准输出含

```text
20 four_blocks=no old_pitfall=yes
21 four_blocks=no old_pitfall=yes
22 four_blocks=no old_pitfall=no
23 four_blocks=no old_pitfall=no
baseline=
```

`baseline=` 后面是当时 `git rev-parse HEAD` 的 40 位哈希。锁定文件里 `chapters` 仍为 `["20", "21", "22", "23"]`，`four_blocks_absent` 仍为 `true`，`old_pitfall_heading_present` 仍为 `true`，`chapters_without_old_pitfall` 仍为 `["22", "23"]`。`files["20"]["en_old_heading"]` 是 `## ⚠️ Common traps and how to check them`。`files["21"]["en_old_heading"]` 是 `## ⚠️ Pitfalls`。`files["22"]["zh_kept_heading"]` 是 `## ⚠️ 仿真替不了的事`。`files["23"]["zh_kept_heading"]` 是 `## ⚠️ 从 F1 抄代码时最容易摔的几处`。`files["22"]["kept_heading_present"]` 和 `files["23"]["kept_heading_present"]` 是 `true`。一级标题仍是 `20 学习资源与工具链`、`21 原理图与实物图鉴`、`22 仿真实验：Wokwi 与 Renode`、`23 STM32G0 引脚（G071RB）`。这个 HEAD 必须还没有新的 `sources`，也还没有四块。

若退出码为 2：停止。不要改四块标题去凑退出码 0，也不要给第 22、23 章补 `常见坑与排查`，也不要造 `## ⚠️ Pitfalls and troubleshooting`。

- [ ] **Step 3: 确认更早的锁定、扫描脚本和设计规格没被改写**

Run:

```bash
git diff --name-only -- tools/scan_sample_chapters.py tools/scan_batch2_chapters.py tools/scan_batch3_chapters.py tools/scan_batch4_chapters.py tools/scan_batch5_chapters.py tools/scan_batch6_chapters.py docs/superpowers/plans/2026-10-25-sample-chapters-lock.json docs/superpowers/plans/2026-10-25-batch2-04-06-lock.json docs/superpowers/plans/2026-10-25-batch3-02-05-08-09-lock.json docs/superpowers/plans/2026-10-25-batch4-01-07-10-11-lock.json docs/superpowers/plans/2026-10-25-batch5-12-13-14-15-lock.json docs/superpowers/plans/2026-10-25-batch6-16-17-18-19-lock.json docs/superpowers/specs/2026-10-25-classic-encyclopedia-batch7-20-21-22-23-design.md
```

Expected: 无输出。若上面某个锁定文件的路径和仓库里的实际文件名不一致，以仓库里已有的那份为准，仍然要求 diff 为空。不要新建一份去覆盖它。样本锁定若实际叫 `docs/superpowers/plans/2026-10-25-sample-chapter-lock.json`，用仓库里的那个名字，diff 仍必须为空。

- [ ] **Step 4: Commit**

```bash
git add tools/scan_batch7_chapters.py docs/superpowers/plans/2026-10-25-batch7-20-21-22-23-lock.json
git commit -m "docs: 锁定第 20、21、22、23 章尚未加厚"
```

这一笔提交里不要带 manifest 或章节正文。锁定文件里的 `baseline` 必须仍指向还没有新 `sources` 的那次提交。

### Task 2: Source list with the license gate

**Files:**
- Create: `docs/superpowers/plans/2026-10-25-batch7-20-21-22-23-source-list.json`
- Create: `stm32-book/tests/test_batch7_sources.py`
- Test: `stm32-book/tests/test_batch7_sources.py`

**Interfaces:**
- Consumes: Task 1 的 `chapters == ["20", "21", "22", "23"]`，以及 `four_blocks_absent == true`。
- Produces: 九个新 id，顺序固定为 `rm0008-signature`、`rm0008-map`、`rm0008-hd-boot`、`ds5792`、`ds10314`、`ds8626`、`ds5319-hse`、`um1724-mco`、`ds12232-lqfp64`。不产生第十个 id。`community` 是空数组。`reuse_existing` 的 id 顺序是 `pm0056`、`pm0075-rdp`、`rm0008-tim`、`ds5319-tim`、`rm0008-usart`、`ds5319-usart`、`ds5319-lse`、`ds5319-nrst`、`ds5319-gpio`、`ds5319-adc`、`ds5319-swd`、`rm0008-boot`、`rm0008-i2c`、`ds5319-i2c`、`project-examples`、`ds12232`、`rm0444`、`an5096`、`an2606`、`st-boot-faq`、`wokwi-bluepill`、`renode-stm32`、`um1724`、`rm0008`。这二十四个 id 不新建 manifest 对象。

2026-10-25 设计规格冻结的事实，实施时打开同一批 URL。首页修订或格子变了就停，先改清单里的 `snapshot` 和 `section`，再画图、再写正文。数字本身按 Global Constraints 那四笔账，不改回旧正文。

PDF 与已有对象相同的，用已有 URL，不另找一份修订：

- DS5319 Rev 20，与 `ds5319-clock` 相同：`https://www.st.com/resource/en/datasheet/stm32f103c8.pdf`
- RM0008 Rev 21，与 `rm0008-rcc` 相同：`https://www.st.com/resource/en/reference_manual/rm0008-stm32f101xx-stm32f102xx-stm32f103xx-advanced-arm-based-32-bit-mcus-stmicroelectronics.pdf`
- PM0056 Rev 7，与 `pm0056-vector` 相同：`https://www.st.com/resource/en/programming_manual/pm0056-stm32f10xxx-cortex-m3-programming-manual-stmicroelectronics.pdf`。不改已有 `pm0056` 对象那条较短的 `url`。
- PM0075，与 `pm0075-rdp` 相同：`https://www.st.com/resource/en/programming_manual/pm0075-stm32f10xxx-flash-memory-microcontrollers-stmicroelectronics.pdf`
- DS12232 Rev 5，与 `ds12232` 相同：`https://www.st.com/resource/en/datasheet/stm32g071c8.pdf`
- UM1724，与 `um1724` 相同：`https://www.st.com/resource/en/user_manual/um1724-stm32-nucleo64-boards-mb1136-stmicroelectronics.pdf`。新 id 是 `um1724-mco`。已有 `um1724` 仍是 L476 的 JP6，一个字段都不改。

另外三份打开产品页上的同一份 PDF。下面的 URL 是默认入口。产品页给出的 PDF 地址不同，就改清单里的 `url`，不新开 id：

- DS5792：`https://www.st.com/resource/en/datasheet/stm32f103ze.pdf`
- DS10314 Rev 8：`https://www.st.com/resource/en/datasheet/stm32f411re.pdf`
- DS8626 Rev 12：`https://www.st.com/resource/en/datasheet/stm32f407vg.pdf`

打不开的就停。不要换一份别的手册来补容量、脚号或皮法。

社区例程这一批不冻结。来源清单的 `community` 是空数组。不吸收未写许可的博客。

- [ ] **Step 1: 写入来源清单**

把下面的 JSON 保存为 `docs/superpowers/plans/2026-10-25-batch7-20-21-22-23-source-list.json`。实施时不要另写一份。许可门测试去读这份文件。

```json
{
  "chapters": ["20", "21", "22", "23"],
  "community": [],
  "reuse_existing": [
    {
      "id": "pm0056",
      "claim": "PM0056 is the Cortex-M3 programming manual. CFSR is at 0xE000ED28. It is not a package manual.",
      "do_not_copy": "Do not edit the existing pm0056 object. Do not open PM0223. Do not put G0 fault registers in chapter 20."
    },
    {
      "id": "pm0075-rdp",
      "claim": "The readout-allowed key is 0xA5, printed as 0x00A5, at 0x1FFFF800. Writing it back mass-erases main Flash. 0xAA is not this key.",
      "do_not_copy": "Do not edit the existing pm0075-rdp object. Do not leave a runnable RDP=0xAA line."
    },
    {
      "id": "rm0008-tim",
      "claim": "PSC = 71, ARR = 999, CCR = 500 at 72 MHz is 1000 Hz and 50 percent. Dropping (PSC+1) yields 72000 Hz.",
      "do_not_copy": "Do not edit the existing rm0008-tim object. Do not redraw sample-05-pwm-1khz.svg."
    },
    {
      "id": "ds5319-tim",
      "claim": "Chapter 20 only cross-references the chapter 05 timer pins. It does not redraw them.",
      "do_not_copy": "Do not edit the existing ds5319-tim object."
    },
    {
      "id": "rm0008-usart",
      "claim": "BRR 0x271 is 115200 at 72 MHz and 12800 at 8 MHz.",
      "do_not_copy": "Do not edit the existing rm0008-usart object. Do not redraw sample-06-uart-frame.svg."
    },
    {
      "id": "ds5319-usart",
      "claim": "Pin 30 is PA9 and pin 31 is PA10.",
      "do_not_copy": "Do not edit the existing ds5319-usart object."
    },
    {
      "id": "ds5319-lse",
      "claim": "LSE load capacitors are chosen from 5 pF to 15 pF. 6 pF is not required.",
      "do_not_copy": "Do not edit the existing ds5319-lse object."
    },
    {
      "id": "ds5319-nrst",
      "claim": "Figure 31 puts 0.1 µF on NRST. The pull-up in kilohms stays out of the source card.",
      "do_not_copy": "Do not edit the existing ds5319-nrst object. Do not open a second id for a kilohm pull-up."
    },
    {
      "id": "ds5319-gpio",
      "claim": "Pin 2 PC13 cannot source current. The external lamp is pin 10 and 270 ohm. 330 ohm is not this book's lamp.",
      "do_not_copy": "Do not edit the existing ds5319-gpio object. Do not redraw sample-03-gpio-led.svg."
    },
    {
      "id": "ds5319-adc",
      "claim": "Pin 10 is PA0. Chapter 22's A0 key only names that pin. Do not draw the lamp, the ADC, and WKUP as live together.",
      "do_not_copy": "Do not edit the existing ds5319-adc object. Do not redraw sample-09-adc-sar.svg."
    },
    {
      "id": "ds5319-swd",
      "claim": "On the C8, pin 34 is PA13 and pin 37 is PA14. Chapter 23 uses different pin numbers on the G071.",
      "do_not_copy": "Do not edit the existing ds5319-swd object. Do not redraw sample-01-swd-vectors.svg."
    },
    {
      "id": "rm0008-boot",
      "claim": "On the C8, system memory starts at 0x1FFFF000. That address is void on the ZET6.",
      "do_not_copy": "Do not edit the existing rm0008-boot object. Do not redraw sample-18-boot-triage.svg."
    },
    {
      "id": "rm0008-i2c",
      "claim": "The 7-bit address 0x3C is written as 0x78 in HAL. 0x3C shifted left by 1 is 0x78. Pull-ups are 4.7 kilohm.",
      "do_not_copy": "Do not edit the existing rm0008-i2c object. Do not redraw sample-07-i2c-addr.svg."
    },
    {
      "id": "ds5319-i2c",
      "claim": "Chapter 22 only cross-references the 4.7 kilohm pull-ups.",
      "do_not_copy": "Do not edit the existing ds5319-i2c object."
    },
    {
      "id": "project-examples",
      "claim": "Chapter 22 points at the existing examples. It does not change them, and it does not change sim/.",
      "do_not_copy": "Do not edit the existing project-examples object. Do not open a new example id."
    },
    {
      "id": "ds12232",
      "claim": "Chapter 23 cross-references the existing G071 datasheet object. The new pin cells go on ds12232-lqfp64.",
      "do_not_copy": "Do not edit the existing ds12232 object. Do not add a standby microamp."
    },
    {
      "id": "rm0444",
      "claim": "BOOT_LOCK=1 forces main Flash. nBOOT_SEL=0 is what makes PA14 part of the boot choice.",
      "do_not_copy": "Do not edit the existing rm0444 object. Do not write a microamp into it."
    },
    {
      "id": "an5096",
      "claim": "Chapter 23 keeps the existing boot-table cross-reference.",
      "do_not_copy": "Do not edit the existing an5096 object."
    },
    {
      "id": "an2606",
      "claim": "Empty Flash can still enter the system bootloader. That sentence stays a cross-reference.",
      "do_not_copy": "Do not edit the existing an2606 object."
    },
    {
      "id": "st-boot-faq",
      "claim": "Boot configuration is latched on the fourth rising edge of SYSCLK.",
      "do_not_copy": "Do not edit the existing st-boot-faq object."
    },
    {
      "id": "wokwi-bluepill",
      "claim": "Link only. The diagram keys are not promoted into a manual term.",
      "do_not_copy": "Do not edit the existing wokwi-bluepill object. Do not rewrite its license string as MIT. Do not open a new id."
    },
    {
      "id": "renode-stm32",
      "claim": "Link only. Port 3456 stays in the lab, not in a source card.",
      "do_not_copy": "Do not edit the existing renode-stm32 object. Do not rewrite its license string as MIT. Do not open a new id."
    },
    {
      "id": "um1724",
      "claim": "The existing object remains the L476 JP6 note.",
      "do_not_copy": "Do not edit the existing um1724 object. The F411 MCO note is the new id um1724-mco."
    },
    {
      "id": "rm0008",
      "claim": "AN4031 describes F2/F4 DMA. It does not answer this C8. This row adds no FIFO threshold and no new F103 DMA channel number.",
      "do_not_copy": "Do not edit the existing rm0008 object."
    }
  ],
  "absorb": [
    {
      "id": "rm0008-signature",
      "chapters": ["21", "20"],
      "title_zh": "RM0008 Rev 21 的器件电子签名",
      "title_en": "RM0008 Rev 21 device electronic signature",
      "authority_zh": "ST 官方参考手册",
      "authority_en": "ST reference manual",
      "url": "https://www.st.com/resource/en/reference_manual/rm0008-stm32f101xx-stm32f102xx-stm32f103xx-advanced-arm-based-32-bit-mcus-stmicroelectronics.pdf",
      "snapshot": "RM0008 Rev 21, February 2021, device electronic signature. DBGMCU_IDCODE is at 0xE0042000. DevID is the low 12 bits. The medium-density F103 DevID is 0x410. Flash size is at 0x1FFFF7E0, low 16 bits, in KB. The 96-bit unique ID starts at 0x1FFFF7E8 and is three words. A C8 reads 64. If the printed chapter is not the chapter the current prose calls chapter 30, record the printed chapter. The addresses and 0x410 stay as printed. This snapshot does not call 128 KB the C8 datasheet size and does not edit ds5319 or ds5319-swd.",
      "license": "ST document terms (link and restated facts only; the manual is not redistributed)",
      "license_class": "ST-facts-restated",
      "section": "device electronic signature",
      "do_not_copy": true,
      "points": [
        "DBGMCU_IDCODE at 0xE0042000, low 12 bits, medium-density DevID 0x410",
        "Flash size at 0x1FFFF7E0 reads 64 KB on a C8. UID starts at 0x1FFFF7E8",
        "128 KB is not the C8 datasheet size"
      ]
    },
    {
      "id": "rm0008-map",
      "chapters": ["22"],
      "title_zh": "RM0008 Rev 21 的 GPIO 与 USART1 基址",
      "title_en": "RM0008 Rev 21 GPIO and USART1 base addresses",
      "authority_zh": "ST 官方参考手册",
      "authority_en": "ST reference manual",
      "url": "https://www.st.com/resource/en/reference_manual/rm0008-stm32f101xx-stm32f102xx-stm32f103xx-advanced-arm-based-32-bit-mcus-stmicroelectronics.pdf",
      "snapshot": "RM0008 Rev 21, February 2021, memory map. GPIOA is at 0x40010800, GPIOB at 0x40010C00, GPIOC at 0x40011000, and USART1 at 0x40013800. If a printed address differs, replace the snapshot. USART1 remains PA9/PA10. This snapshot does not restate BRR and does not record port 3456. It does not edit rm0008-usart or rm0008-gpio.",
      "license": "ST document terms (link and restated facts only; the manual is not redistributed)",
      "license_class": "ST-facts-restated",
      "section": "memory map",
      "do_not_copy": true,
      "points": [
        "USART1 is at 0x40013800. Calling that block USART2 is the miss",
        "GPIOC is at 0x40011000. The Wokwi key C13 points at this port",
        "Port 3456 is not in this object"
      ]
    },
    {
      "id": "rm0008-hd-boot",
      "chapters": ["21"],
      "title_zh": "RM0008 Rev 21 大容量的系统存储器起点",
      "title_en": "RM0008 Rev 21 high-density system-memory base",
      "authority_zh": "ST 官方参考手册",
      "authority_en": "ST reference manual",
      "url": "https://www.st.com/resource/en/reference_manual/rm0008-stm32f101xx-stm32f102xx-stm32f103xx-advanced-arm-based-32-bit-mcus-stmicroelectronics.pdf",
      "snapshot": "RM0008 Rev 21, February 2021, the same manual as rm0008-boot. This object records only the high-density row: STM32F103xC, xD, and xE system memory starts at 0x1FFFB000 by default. The medium-density C8 address 0x1FFFF000 stays on the existing object. If the printed high-density base differs, change this snapshot. Do not write the C8 address into this object, and do not edit rm0008-boot.",
      "license": "ST document terms (link and restated facts only; the manual is not redistributed)",
      "license_class": "ST-facts-restated",
      "section": "boot memory",
      "do_not_copy": true,
      "points": [
        "High-density system memory defaults to 0x1FFFB000",
        "The C8 address 0x1FFFF000 is void on the ZET6",
        "Do not edit rm0008-boot"
      ]
    },
    {
      "id": "ds5792",
      "chapters": ["21"],
      "title_zh": "DS5792 的 STM32F103ZET6 容量",
      "title_en": "DS5792 STM32F103ZET6 memory",
      "authority_zh": "ST 官方数据手册",
      "authority_en": "ST datasheet",
      "url": "https://www.st.com/resource/en/datasheet/stm32f103ze.pdf",
      "snapshot": "DS5792, STM32F103xC, xD, and xE. Record the revision printed on the PDF opened from the product page. STM32F103ZET6 takes the xE row: 512 KB of Flash, 64 KB of SRAM, 72 MHz maximum, LQFP144. The xC row is 256 KB of Flash and 48 KB of SRAM. The xD row is 384 KB of Flash and 64 KB of SRAM. Both of those rows are void on the ZET6. If Table 2 does not print 512 and 64 for ZE, use the printed cells. This snapshot does not copy the DS5319 64 KB / 20 KB pair and does not paste a schematic.",
      "license": "ST document terms (link and restated facts only; the manual is not redistributed)",
      "license_class": "ST-facts-restated",
      "section": "Table 2",
      "do_not_copy": true,
      "points": [
        "STM32F103ZET6 is 512 KB of Flash and 64 KB of SRAM at up to 72 MHz in LQFP144",
        "xC 256 KB / 48 KB and xD 384 KB are void on the ZET6",
        "Do not copy the C8 64 KB / 20 KB pair into this object"
      ]
    },
    {
      "id": "ds10314",
      "chapters": ["21"],
      "title_zh": "DS10314 Rev 8 的 F411xE 容量与主频上限",
      "title_en": "DS10314 Rev 8 F411xE memory and maximum clock",
      "authority_zh": "ST 官方数据手册",
      "authority_en": "ST datasheet",
      "url": "https://www.st.com/resource/en/datasheet/stm32f411re.pdf",
      "snapshot": "DS10314 Rev 8, January 2024, STM32F411xC and xE. xE Flash is 512 KB. xC Flash is 256 KB. SRAM is 128 KB. The maximum clock is 100 MHz. The crystal range is 4 MHz to 26 MHz. STM32F411CEU6 and STM32F411RET6 are both xE. The xC 256 KB is void on those two order codes. This snapshot does not record PLL M, N, or P, and it does not call 25 MHz the datasheet's choice of board crystal.",
      "license": "ST document terms (link and restated facts only; the manual is not redistributed)",
      "license_class": "ST-facts-restated",
      "section": "memory and clock",
      "do_not_copy": true,
      "points": [
        "F411xE is 512 KB of Flash, 128 KB of SRAM, and 100 MHz maximum",
        "xC 256 KB is void on CEU6 and RET6",
        "PLL M, N, and P are not a datasheet cell"
      ]
    },
    {
      "id": "ds8626",
      "chapters": ["21"],
      "title_zh": "DS8626 Rev 12 的 F407VG 容量",
      "title_en": "DS8626 Rev 12 F407VG memory",
      "authority_zh": "ST 官方数据手册",
      "authority_en": "ST datasheet",
      "url": "https://www.st.com/resource/en/datasheet/stm32f407vg.pdf",
      "snapshot": "DS8626 Rev 12, March 2026, STM32F405 and STM32F407. Flash maximum is 1 MB. Clock maximum is 168 MHz. SRAM maximum is 192 KB, which includes 64 KB of CCM, plus 4 KB of backup SRAM. The G in STM32F407VGT6 is the 1 MB bin. V is the 100-pin package. The F407VE 512 KB bin is void on VGT6. If the VG row does not print 1024 KB, use the printed size. This snapshot does not fold the 4 KB into the 192 KB and does not invent an Ethernet PHY.",
      "license": "ST document terms (link and restated facts only; the manual is not redistributed)",
      "license_class": "ST-facts-restated",
      "section": "memory",
      "do_not_copy": true,
      "points": [
        "F407VGT6 is 1 MB of Flash and 168 MHz maximum",
        "192 KB of SRAM includes 64 KB of CCM. Backup SRAM is another 4 KB",
        "Do not call the sum 196 KB of main SRAM"
      ]
    },
    {
      "id": "ds5319-hse",
      "chapters": ["21"],
      "title_zh": "DS5319 Rev 20 的 HSE 负载电容范围",
      "title_en": "DS5319 Rev 20 HSE load-capacitor range",
      "authority_zh": "ST 官方数据手册",
      "authority_en": "ST datasheet",
      "url": "https://www.st.com/resource/en/datasheet/stm32f103c8.pdf",
      "snapshot": "DS5319 Rev 20, July 2025, the same PDF as ds5319-clock, HSE oscillator section. CL1 and CL2 are chosen from the 5 pF to 25 pF ceramic range to match the crystal, and the two capacitors are usually equal. 20 pF is not a required value. If the printed range differs, change this snapshot and do not keep another pair of picofarads from the old prose. 8 MHz stays on the existing clock object. This snapshot does not edit ds5319-clock or ds5319-lse and does not call 20 pF required.",
      "license": "ST document terms (link and restated facts only; the manual is not redistributed)",
      "license_class": "ST-facts-restated",
      "section": "HSE oscillator",
      "do_not_copy": true,
      "points": [
        "HSE CL1 and CL2 are chosen in the 5 pF to 25 pF range",
        "20 pF is not a required value",
        "The LSE 5 pF to 15 pF range stays on ds5319-lse"
      ]
    },
    {
      "id": "um1724-mco",
      "chapters": ["21"],
      "title_zh": "UM1724 里 NUCLEO-F411RE 的时钟输入",
      "title_en": "UM1724 NUCLEO-F411RE clock input",
      "authority_zh": "ST 官方用户手册",
      "authority_en": "ST user manual",
      "url": "https://www.st.com/resource/en/user_manual/um1724-stm32-nucleo64-boards-mb1136-stmicroelectronics.pdf",
      "snapshot": "UM1724, the same PDF as the existing um1724 object. Until the NUCLEO-F411RE clock section is opened, this snapshot records no input frequency. The four sections do not state a Nucleo input frequency. The 100 MHz cap stays on ds10314. This snapshot does not record PLL multipliers. The existing um1724 object stays the L476 JP6 note and is not edited.",
      "license": "ST document terms (link and restated facts only; the manual is not redistributed)",
      "license_class": "ST-facts-restated",
      "section": "NUCLEO-F411RE clock",
      "do_not_copy": true,
      "points": [
        "Record only a frequency the NUCLEO-F411RE clock section actually prints",
        "If that section prints no frequency, the four sections do not state one",
        "Do not record PLLM, PLLN, or PLLP, and do not edit um1724"
      ]
    },
    {
      "id": "ds12232-lqfp64",
      "chapters": ["23"],
      "title_zh": "DS12232 Rev 5 的 LQFP64 脚位与容量",
      "title_en": "DS12232 Rev 5 LQFP64 pins and memory",
      "authority_zh": "ST 官方数据手册",
      "authority_en": "ST datasheet",
      "url": "https://www.st.com/resource/en/datasheet/stm32g071c8.pdf",
      "snapshot": "DS12232 Rev 5, the same PDF as ds12232. Figure 9 and the LQFP64 column of Table 12, plus Table 2. Pin 1 is PC11. Pin 3 is PC13. Pin 6 is VBAT. Pin 12 is PF2-NRST. Pin 35 is PB15, and its alternate functions include UCPD1_CC2. Pin 36 is PA8, and its alternate functions include UCPD1_CC1. Pin 45 is PA13. Pin 46 is PA14-BOOT0. Note 1: PC13, PC14, and PC15 can sink only about 3 mA, the output stays at or below 2 MHz, the load stays at or below 30 pF, and these pins must not source current. Note 6: after reset PA13 is pulled up internally and PA14 is pulled down internally. Table 2: R is 64 pins, B is 128 KB of Flash, SRAM is 32 KB with hardware parity or 36 KB without, the maximum clock is 64 MHz, and the supply is 1.7 V to 3.6 V. The feature list has no CAN controller and no USB full-speed device. If a printed pin or milliamp differs, use the printed cell. This snapshot does not write a standby microamp, does not edit ds12232, does not call pin 1 VBAT, and does not invent an FDCAN pin.",
      "license": "ST document terms (link and restated facts only; the manual is not redistributed)",
      "license_class": "ST-facts-restated",
      "section": "Figure 9 and Table 12",
      "do_not_copy": true,
      "points": [
        "Pin 1 is PC11. Pin 12 is PF2-NRST. Pin 6 is VBAT",
        "PC13 through PC15 sink about 3 mA and must not source an LED",
        "Pin 46 PA14 is also SWCLK. SRAM is 32 KB or 36 KB, not the sum"
      ]
    }
  ]
}
```

- [ ] **Step 2: 写许可门测试**

保存为 `stm32-book/tests/test_batch7_sources.py`：

```python
#!/usr/bin/env python3
"""License gate for chapters 20, 21, 22, and 23. The manifest is updated later."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE_LIST = ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch7-20-21-22-23-source-list.json"
LOCK = ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch7-20-21-22-23-lock.json"
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
    "rm0008-signature",
    "rm0008-map",
    "rm0008-hd-boot",
    "ds5792",
    "ds10314",
    "ds8626",
    "ds5319-hse",
    "um1724-mco",
    "ds12232-lqfp64",
]
REUSED = [
    "pm0056",
    "pm0075-rdp",
    "rm0008-tim",
    "ds5319-tim",
    "rm0008-usart",
    "ds5319-usart",
    "ds5319-lse",
    "ds5319-nrst",
    "ds5319-gpio",
    "ds5319-adc",
    "ds5319-swd",
    "rm0008-boot",
    "rm0008-i2c",
    "ds5319-i2c",
    "project-examples",
    "ds12232",
    "rm0444",
    "an5096",
    "an2606",
    "st-boot-faq",
    "wokwi-bluepill",
    "renode-stm32",
    "um1724",
    "rm0008",
]


class Batch7SourceListTests(unittest.TestCase):
    def test_lock_keeps_chapters_20_21_22_23(self) -> None:
        lock = json.loads(LOCK.read_text(encoding="utf-8"))
        self.assertEqual(["20", "21", "22", "23"], lock["chapters"])
        self.assertTrue(lock["four_blocks_absent"])
        self.assertTrue(lock["old_pitfall_heading_present"])
        self.assertEqual(["22", "23"], lock["chapters_without_old_pitfall"])
        self.assertEqual(40, len(lock["baseline"]))
        self.assertEqual("2026-10-25-classic-encyclopedia-batch7-20-21-22-23", lock["rubric"])
        expected = (
            ("20", "docs/20-学习资源与工具链.md", "docs/en/20-resources.md", True, "## ⚠️ Common traps and how to check them"),
            ("21", "docs/21-原理图与实物图鉴.md", "docs/en/21-board-maps.md", True, "## ⚠️ Pitfalls"),
            ("22", "docs/22-仿真实验Wokwi与Renode.md", "docs/en/22-simulation-wokwi-renode.md", False, "## ⚠️ Pitfalls and troubleshooting"),
            ("23", "docs/23-STM32G0引脚.md", "docs/en/23-stm32g0-pins.md", False, "## ⚠️ Pitfalls and troubleshooting"),
        )
        for prefix, zh_name, en_name, expects_old, en_old in expected:
            row = lock["files"][prefix]
            self.assertEqual(zh_name, row["zh"])
            self.assertEqual(en_name, row["en"])
            self.assertFalse(row["zh_four_blocks"])
            self.assertFalse(row["en_four_blocks"])
            self.assertEqual(expects_old, row["expects_old_pitfall"])
            self.assertEqual(expects_old, row["zh_old_pitfall"])
            self.assertEqual(expects_old, row["en_old_pitfall"])
            self.assertEqual(en_old, row["en_old_heading"])
        self.assertEqual("## ⚠️ 仿真替不了的事", lock["files"]["22"]["zh_kept_heading"])
        self.assertEqual("## ⚠️ 从 F1 抄代码时最容易摔的几处", lock["files"]["23"]["zh_kept_heading"])
        self.assertTrue(lock["files"]["22"]["kept_heading_present"])
        self.assertTrue(lock["files"]["23"]["kept_heading_present"])
        self.assertIn("原理图与实物图鉴", (ROOT / "docs" / "21-原理图与实物图鉴.md").read_text(encoding="utf-8").splitlines()[0])
        self.assertIn("仿真实验：Wokwi 与 Renode", (ROOT / "docs" / "22-仿真实验Wokwi与Renode.md").read_text(encoding="utf-8").splitlines()[0])
        self.assertNotIn("图注", (ROOT / "docs" / "21-原理图与实物图鉴.md").read_text(encoding="utf-8").splitlines()[0])
        self.assertNotIn("仿真实战", (ROOT / "docs" / "22-仿真实验Wokwi与Renode.md").read_text(encoding="utf-8").splitlines()[0])

    def test_source_list_keeps_the_license_gate(self) -> None:
        payload = json.loads(SOURCE_LIST.read_text(encoding="utf-8"))
        self.assertEqual(["20", "21", "22", "23"], payload["chapters"])
        self.assertEqual([], payload["community"])
        ids = [item["id"] for item in payload["absorb"]]
        self.assertEqual(ABSORB, ids)
        self.assertEqual(9, len(ids))
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
        self.assertEqual("device electronic signature", by_id["rm0008-signature"]["section"])
        self.assertEqual("memory map", by_id["rm0008-map"]["section"])
        self.assertEqual("boot memory", by_id["rm0008-hd-boot"]["section"])
        self.assertEqual("Table 2", by_id["ds5792"]["section"])
        self.assertEqual("memory and clock", by_id["ds10314"]["section"])
        self.assertEqual("memory", by_id["ds8626"]["section"])
        self.assertEqual("HSE oscillator", by_id["ds5319-hse"]["section"])
        self.assertEqual("NUCLEO-F411RE clock", by_id["um1724-mco"]["section"])
        self.assertEqual("Figure 9 and Table 12", by_id["ds12232-lqfp64"]["section"])
        signature = by_id["rm0008-signature"]["snapshot"]
        self.assertIn("0xE0042000", signature)
        self.assertIn("0x410", signature)
        self.assertIn("0x1FFFF7E0", signature)
        self.assertIn("0x1FFFF7E8", signature)
        self.assertNotIn("128 KB is the C8", signature)
        memory_map = by_id["rm0008-map"]["snapshot"]
        self.assertIn("0x40013800", memory_map)
        self.assertIn("0x40011000", memory_map)
        self.assertNotIn("3456", memory_map)
        boot = by_id["rm0008-hd-boot"]["snapshot"]
        self.assertIn("0x1FFFB000", boot)
        self.assertIn("0x1FFFF000", boot)
        zet6 = by_id["ds5792"]["snapshot"]
        self.assertIn("512 KB", zet6)
        self.assertIn("64 KB", zet6)
        self.assertNotIn("20 KB of SRAM on the ZET6", zet6)
        f411 = by_id["ds10314"]["snapshot"]
        self.assertIn("100 MHz", f411)
        self.assertIn("128 KB", f411)
        self.assertNotIn("N=200", f411)
        self.assertNotIn("PLLM", f411)
        f407 = by_id["ds8626"]["snapshot"]
        self.assertIn("192 KB", f407)
        self.assertIn("4 KB", f407)
        self.assertIn("168 MHz", f407)
        self.assertNotIn("196 KB", f407)
        hse = by_id["ds5319-hse"]["snapshot"]
        self.assertIn("5 pF", hse)
        self.assertIn("25 pF", hse)
        self.assertIn("20 pF is not a required value", hse)
        mco = by_id["um1724-mco"]["snapshot"]
        self.assertNotIn("N=200", mco)
        self.assertNotIn("PLLM", mco)
        self.assertIn("records no input frequency", mco)
        g0 = by_id["ds12232-lqfp64"]["snapshot"]
        self.assertIn("PC11", g0)
        self.assertIn("PF2-NRST", g0)
        self.assertIn("3 mA", g0)
        self.assertIn("PA14-BOOT0", g0)
        self.assertIn("32 KB", g0)
        self.assertIn("36 KB", g0)
        self.assertNotIn("standby microamp is", g0.lower())
        reused = [item["id"] for item in payload["reuse_existing"]]
        self.assertEqual(REUSED, reused)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: 运行测试，并只核对会改 snapshot 的五处**

Run: `python3 stm32-book/tests/test_batch7_sources.py -v`

Expected: OK，两条测试都通过。清单已经在这一任务的工作区里，所以这一步不是 `FileNotFoundError`。若失败，改清单去满足上面的断言，不要放宽 `ABSORB`，也不要删掉测试来制造一次红色。不要追加第十个 id。

锁定文件那一条若失败，先回到 Task 1。不要改测试去迁就一份章号不对的锁。

然后打开 Step 1 列出的 PDF，只核对下面五处。印出的句子还在，清单不动。

DS5792 的 ZE 行：默认 STM32F103ZET6 是 512 KB 闪存、64 KB SRAM、72 MHz、LQFP144。把印出的修订号写进 `ds5792` 的 snapshot。格子不同就改格子，不改回 DS5319 的 64 KB / 20 KB。xC 与 xD 在 ZET6 上仍然作废。

大容量系统存储器：默认 `0x1FFFB000`。印出的起点不同就改 `rm0008-hd-boot`。不修改 `rm0008-boot` 里 C8 的 `0x1FFFF000`。

HSE 负载电容：默认 5 pF 到 25 pF，20 pF 不是必须值。印出的范围不同就改 `ds5319-hse`。不把 20 pF 留成必须值。

UM1724 的 MCO：打开 NUCLEO-F411RE 时钟节后再改 `um1724-mco` 的 snapshot，并改测试里对 `records no input frequency` 的那一条断言，使它对准印出的句子。三种结果只留一种：

- 印出 ST-LINK 的 MCO 接到 OSC_IN 且频率是 8 MHz：snapshot 写成 `UM1724 prints the ST-LINK MCO into OSC_IN at 8 MHz. That frequency cannot be turned on the board. This snapshot does not record PLL multipliers. The existing um1724 object is not edited.` 测试改为 `self.assertIn("8 MHz", mco)` 和 `self.assertIn("cannot be turned", mco)`，并删掉 `self.assertIn("records no input frequency", mco)`。
- 印出别的频率：把 `8 MHz` 换成印出的频率，其余句子同上。四块仍可以在旁注里写这个频率。主图不画 M、N、P。
- 这一节没有频率：保持清单里现在这句 `records no input frequency`。四块不写 Nucleo 的输入频率，只保留 DS10314 的 100 MHz 上限。

三种情况下 `N=200` 都不进 snapshot，也不进四块。不改已有 `um1724`。

DS8626 的 VG 行：默认 VGT6 是 1 MB，SRAM 表述保持「192 KB（含 64 KB CCM）另加 4 KB」。印出的分列不同就改 snapshot，不把 4 KB 并进 192。

无论哪一处，都不要改 `license_class`，不要改另外几个 id 的 `points`，不要新增第十个 id。

- [ ] **Step 4: 再跑测试并提交**

Run: `python3 stm32-book/tests/test_batch7_sources.py -v`

Expected: OK。

```bash
git add docs/superpowers/plans/2026-10-25-batch7-20-21-22-23-source-list.json stm32-book/tests/test_batch7_sources.py
git commit -m "docs: 钉上 20、21、22、23 的许可门"
```

不要在这一笔里改章节正文。不要改已有来源对象。不要改 manifest。

### Task 3: Static key figures

**Files:**
- Modify: `tools/gen_sample_figures.py`（只追加函数，并在 `main()` 里多保存四张。不改 `boot_state`、`gpio_led`、`exception_stack`、`uart_frame`、`clock_tree`、`pwm_1khz`、`spi_jedec`、`adc_sample`、`swd_vectors`、`i2c_addr`、`dma_cndtr`、`iwdg_1s`、`iap_map`、`can_bit`、`usb_enum`、`rtos_prio`、`stop_wake`、`cfsr_read`、`boot_triage`、`flash_fit`、`_credit`）
- Create: `assets/diagrams/sample-20-which-manual.svg`
- Create: `assets/diagrams/sample-21-which-part.svg`
- Create: `assets/diagrams/sample-22-sim-boundary.svg`
- Create: `assets/diagrams/sample-23-g071-pins.svg`
- Modify: `assets/README.md`（开头的生成命令，第四节表的末尾）
- Create: `stm32-book/tests/test_batch7_chapters.py`
- Test: `stm32-book/tests/test_batch7_chapters.py`

**Interfaces:**
- Consumes: Task 2 清单里的订货号、脚位和地址。已有的 `_credit(canvas, note)`。`Svg`、`T` 来自 `tools/svgkit.py`。
- Produces: `which_manual() -> Svg`、`which_part() -> Svg`、`sim_boundary() -> Svg`、`g071_pins() -> Svg`。四张 SVG 不含 `<animate`、`@keyframes`、`animation:`，不含「矢量动画」，不含「实拍」，含「自绘」。每张都小于 60 KB。默认不产生 `sample-21-other-parts.svg`，也不产生 `sample-23-pc13.svg`。

`sample-20-which-manual.svg` 的文本含 `PM0056`、`DS5319`、`RM0008`、`PM0075`、`0xE000ED28`、`72000`、`0xA5`、`0xAA`、`0x271`、`PA9`、`pin 30`。

`sample-21-which-part.svg` 的文本含 `0x410`、`0x1FFFF7E0`、`64 KB`、`20 KB`、`0x1FFFF000`、`512 KB`、`0x1FFFB000`、`100 MHz`、`192 KB`、`4 KB`、`168 MHz`。不含 `N=200`，不含 `330`，不含 `6 pF`。

`sample-22-sim-boundary.svg` 的文本含 `0x40013800`、`0x40011000`、`pin 2`、`PC13`、`C13`、`0x271`、`115200`、`12800`、`USART2`、`0x3C`、`0x78`。不含 `3456`。

`sample-23-g071-pins.svg` 的文本含 `pin 1`、`PC11`、`pin 12`、`PF2-NRST`、`pin 6`、`VBAT`、`pin 3`、`PC13`、`3 mA`、`2 MHz`、`30 pF`、`pin 46`、`PA14`、`SWCLK`、`32 KB`、`36 KB`。不含 `uA`，不含 `0x1FFFF000`。

- [ ] **Step 1: 写会失败的主图测试**

保存为 `stm32-book/tests/test_batch7_chapters.py`：

```python
#!/usr/bin/env python3
"""Checks for thickened chapters 20, 21, 22, and 23 and their static figures."""

from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIAGRAMS = ROOT / "assets" / "diagrams"
MANUAL = DIAGRAMS / "sample-20-which-manual.svg"
PART = DIAGRAMS / "sample-21-which-part.svg"
SIM = DIAGRAMS / "sample-22-sim-boundary.svg"
PINS = DIAGRAMS / "sample-23-g071-pins.svg"


class Batch7FigureTests(unittest.TestCase):
    def test_key_figures_are_static_and_under_60_kib(self) -> None:
        for path, tokens, banned in (
            (
                MANUAL,
                (
                    "PM0056",
                    "DS5319",
                    "RM0008",
                    "PM0075",
                    "0xE000ED28",
                    "72000",
                    "0xA5",
                    "0xAA",
                    "0x271",
                    "PA9",
                    "pin 30",
                    "自绘",
                ),
                ("<animate", "@keyframes", "animation:", "矢量动画", "实拍", "90%"),
            ),
            (
                PART,
                (
                    "0x410",
                    "0x1FFFF7E0",
                    "64 KB",
                    "20 KB",
                    "0x1FFFF000",
                    "512 KB",
                    "0x1FFFB000",
                    "100 MHz",
                    "192 KB",
                    "4 KB",
                    "168 MHz",
                    "自绘",
                ),
                ("N=200", "330", "6 pF", "<animate", "@keyframes", "animation:", "矢量动画", "实拍"),
            ),
            (
                SIM,
                (
                    "0x40013800",
                    "0x40011000",
                    "pin 2",
                    "PC13",
                    "C13",
                    "0x271",
                    "115200",
                    "12800",
                    "USART2",
                    "0x3C",
                    "0x78",
                    "自绘",
                ),
                ("3456", "<animate", "@keyframes", "animation:", "矢量动画", "实拍"),
            ),
            (
                PINS,
                (
                    "pin 1",
                    "PC11",
                    "pin 12",
                    "PF2-NRST",
                    "pin 6",
                    "VBAT",
                    "pin 3",
                    "PC13",
                    "3 mA",
                    "2 MHz",
                    "30 pF",
                    "pin 46",
                    "PA14",
                    "SWCLK",
                    "32 KB",
                    "36 KB",
                    "自绘",
                ),
                ("uA", "0x1FFFF000", "<animate", "@keyframes", "animation:", "矢量动画", "实拍"),
            ),
        ):
            text = path.read_text(encoding="utf-8")
            self.assertLess(path.stat().st_size, 60 * 1024, path.name)
            for token in tokens:
                self.assertIn(token, text, path.name)
            for token in banned:
                self.assertNotIn(token, text, path.name)
        self.assertFalse((DIAGRAMS / "sample-21-other-parts.svg").exists())
        self.assertFalse((DIAGRAMS / "sample-23-pc13.svg").exists())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试，确认它因为文件不存在而失败**

Run: `python3 stm32-book/tests/test_batch7_chapters.py Batch7FigureTests -v`

Expected: FAIL，`sample-20-which-manual.svg` 不存在。不要改测试去接受一张简笔，也不要把 60 KB 放宽。

- [ ] **Step 3: 追加四个生成函数并写出 SVG**

在 `tools/gen_sample_figures.py` 的 `flash_fit()` 之后、`def main` 之前插入下面四个函数。在 `main()` 里 `flash_fit().save(...)` 之后追加四行 `save`。不改已有函数。

```python
def which_manual() -> Svg:
    canvas = Svg(
        960,
        720,
        "PM0056 是编程手册；丢掉 (PSC+1) 得到 72000 Hz；读允许键是 0xA5",
        "STM32F103C8T6 · PM0056 Rev 7 · PM0075 · RM0008 Rev 21 · DS5319 Rev 20",
    )
    canvas.header(tag="20", tag_color=T.CYAN)
    canvas.text(40, 86, "DS5319 Rev 20    RM0008 Rev 21    PM0056 Rev 7", size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 118, "正常路径  open the book that owns the number", size=16, fill=T.GREEN, weight="700")
    canvas.rect(40, 132, 880, 150, fill=T.PANEL, stroke=T.GREEN, rx=8)
    canvas.text(56, 162, "pin 30 is PA9 in DS5319", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 188, "BRR 0x271 is in RM0008. 72 MHz is 115200", size=14, fill=T.GREEN)
    canvas.text(56, 214, "HardFault: PM0056, CFSR at 0xE000ED28", size=14, fill=T.TEXT)
    canvas.text(56, 240, "readout-allowed key is 0xA5, printed 0x00A5 in PM0075", size=14, fill=T.CYAN)
    canvas.text(40, 310, "失败路径  the package book, the dropped divisor, and 0xAA", size=16, fill=T.RED, weight="700")
    canvas.rect(40, 324, 880, 130, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(56, 354, "looking up pin 30 in PM0056", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 380, "PSC = 71 still set, (PSC+1) dropped, result 72000 Hz", size=14, fill=T.RED)
    canvas.text(56, 406, "option byte written as 0xAA", size=14, fill=T.AMBER)
    canvas.rect(40, 474, 880, 110, fill=T.BG2, stroke=T.VIOLET, rx=8)
    canvas.text(56, 504, "旁注  AN4031 FIFO does not answer this C8", size=15, fill=T.VIOLET, weight="700")
    canvas.text(56, 530, "do not draw a PWM waveform. Do not draw the other CFSR bits", size=14, fill=T.MUTED)
    canvas.text(56, 556, "address of the option bytes is 0x1FFFF800", size=13, fill=T.MUTED)
    _credit(canvas, "自绘。PM0056 是编程手册。72000 Hz 与 0xA5 见 RM0008 与 PM0075。")
    return canvas


def which_part() -> Svg:
    canvas = Svg(
        960,
        760,
        "C8 的 DevID 是 0x410，容量读数是 64 KB；ZET6 的系统存储器不是 0x1FFFF000",
        "STM32F103C8T6 · DS5319 · DS5792 · RM0008",
    )
    canvas.header(tag="21", tag_color=T.CYAN)
    canvas.text(40, 86, "C8  0x410 at 0xE0042000    0x1FFFF7E0 reads 64 KB    SRAM 20 KB", size=15, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "system memory 0x1FFFF000", size=14, fill=T.CYAN)
    canvas.text(40, 144, "正常路径  a read of 64 stays on DS5319; ZET6 is a different manual", size=16, fill=T.GREEN, weight="700")
    canvas.rect(40, 158, 880, 120, fill=T.PANEL, stroke=T.GREEN, rx=8)
    canvas.text(56, 188, "C8 Flash 64 KB, SRAM 20 KB, system memory 0x1FFFF000", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 214, "ZET6 512 KB Flash, 64 KB SRAM, system memory 0x1FFFB000", size=14, fill=T.GREEN)
    canvas.text(56, 240, "F411xE 512 KB / 128 KB / 100 MHz. F407VG 1 MB, 168 MHz, 192 KB + 4 KB", size=13, fill=T.MUTED)
    canvas.text(40, 306, "失败路径  128 KB silk, and the C8 boot address on a ZET6", size=16, fill=T.RED, weight="700")
    canvas.rect(40, 320, 880, 110, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(56, 350, "silk says C8, the size register is not 64, still link 128 KB", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 376, "ZET6 bootloader drawn at 0x1FFFF000", size=14, fill=T.RED)
    canvas.text(56, 402, "do not add the 4 KB into the 192 KB", size=14, fill=T.AMBER)
    _credit(canvas, "自绘。0x410 与 64 KB 来自 RM0008 签名。512 KB 来自 DS5792。")
    return canvas


def sim_boundary() -> Svg:
    canvas = Svg(
        960,
        720,
        "USART1 在 0x40013800；C13 是第 2 脚；灯亮时 0x271 仍可能是 12800",
        "STM32F103C8T6 · RM0008 · 0x271",
    )
    canvas.header(tag="22", tag_color=T.CYAN)
    canvas.text(40, 86, "key C13 -> pin 2 PC13    key A9 -> pin 30 PA9", size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "USART1 at 0x40013800    GPIOC at 0x40011000", size=14, fill=T.CYAN)
    canvas.text(40, 144, "正常路径  72 MHz, 0x271 is 115200, PC13 lights when low", size=16, fill=T.GREEN, weight="700")
    canvas.rect(40, 158, 880, 110, fill=T.PANEL, stroke=T.GREEN, rx=8)
    canvas.text(56, 188, "keys match the pins", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 214, "72 MHz and 0x271 is 115200", size=14, fill=T.GREEN)
    canvas.text(56, 240, "I2C 7-bit 0x3C, HAL 0x78", size=14, fill=T.MUTED)
    canvas.text(40, 296, "失败路径  the lamp blinks at 12800, or the block is called USART2", size=16, fill=T.RED, weight="700")
    canvas.rect(40, 310, 880, 110, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(56, 340, "same 0x271 left on 8 MHz is 12800, and the lamp still blinks", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 366, "peripheral labeled USART2", size=14, fill=T.RED)
    canvas.text(56, 392, "a chip name PA13 where the key is C13", size=14, fill=T.AMBER)
    _credit(canvas, "自绘。USART1 基址来自 RM0008。0x271 与第 06 章同一笔。")
    return canvas


def g071_pins() -> Svg:
    canvas = Svg(
        960,
        760,
        "第 1 脚是 PC11；第 12 脚是 PF2-NRST；PA14 与 SWCLK 是同一只脚",
        "STM32G071RB LQFP64 · DS12232 Rev 5 Figure 9 / Table 12",
    )
    canvas.header(tag="23", tag_color=T.CYAN)
    canvas.text(40, 86, "pin 1 PC11    pin 6 VBAT    pin 12 PF2-NRST    pin 3 PC13", size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "PC13 sink about 3 mA, at or below 2 MHz and 30 pF", size=14, fill=T.AMBER)
    canvas.text(40, 144, "正常路径  count pin 1 as PC11, and keep PA14 with SWCLK", size=16, fill=T.GREEN, weight="700")
    canvas.rect(40, 158, 880, 130, fill=T.PANEL, stroke=T.GREEN, rx=8)
    canvas.text(56, 188, "pin 45 PA13 pulled up after reset", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 214, "pin 46 PA14-BOOT0 pulled down after reset, same pin as SWCLK", size=14, fill=T.GREEN)
    canvas.text(56, 240, "UCPD: pin 36 PA8 and pin 35 PB15", size=14, fill=T.CYAN)
    canvas.text(56, 266, "SRAM 32 KB with parity, or 36 KB without. Do not add them", size=13, fill=T.MUTED)
    canvas.text(40, 316, "失败路径  pin 1 called VBAT, an LED on PC13, a search for CAN_TX", size=16, fill=T.RED, weight="700")
    canvas.rect(40, 330, 880, 110, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(56, 360, "pin 1 marked VBAT", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 386, "LED on pin 3 PC13", size=14, fill=T.RED)
    canvas.text(56, 412, "CAN_TX is not on this part", size=14, fill=T.AMBER)
    _credit(canvas, "自绘。脚号来自 DS12232 Rev 5 Figure 9 与 Table 12。")
    return canvas
```

`main()` 末尾追加：

```python
    which_manual().save(os.path.join(out_dir, "sample-20-which-manual.svg"))
    which_part().save(os.path.join(out_dir, "sample-21-which-part.svg"))
    sim_boundary().save(os.path.join(out_dir, "sample-22-sim-boundary.svg"))
    g071_pins().save(os.path.join(out_dir, "sample-23-g071-pins.svg"))
```

`assets/README.md` 开头把 `第 00 到第 19 章的静态主图` 改成 `第 00 到第 23 章的静态主图`。第四节表在 `sample-19-flash-fit.svg` 那一行后面追加：

```markdown
| `sample-20-which-manual.svg` | 第 20 章静态主图：PM0056 是编程手册；丢掉 (PSC+1) 得到 72000 Hz；读允许键是 0xA5，不是 0xAA。由 `tools/gen_sample_figures.py` 生成 |
| `sample-21-which-part.svg` | 第 21 章静态主图：C8 读 0x410 和 64 KB；ZET6 的 512 KB 在 DS5792，系统存储器是 0x1FFFB000。由 `tools/gen_sample_figures.py` 生成 |
| `sample-22-sim-boundary.svg` | 第 22 章静态主图：USART1 在 0x40013800；键 C13 是第 2 脚；灯亮时 0x271 仍可能是 12800。由 `tools/gen_sample_figures.py` 生成 |
| `sample-23-g071-pins.svg` | 第 23 章静态主图：第 1 脚 PC11，第 12 脚 PF2-NRST，第 46 脚 PA14 与 SWCLK 共用。由 `tools/gen_sample_figures.py` 生成 |
```

Run:

```bash
python3 tools/gen_sample_figures.py
```

Expected: 退出码 0。四张新 SVG 都小于 60 KB。若 `sample-21-which-part.svg` 达到或超过 60 KB，把 F411 和 F407 那一行拆到 `which_part_side() -> Svg`，保存为 `assets/diagrams/sample-21-other-parts.svg`。第一张仍含 `0x410`、`64 KB`、`512 KB`、`0x1FFFB000`。两张都调用 `_credit()`，都不调用 `Svg.footer()`。然后把测试里 `self.assertFalse((DIAGRAMS / "sample-21-other-parts.svg").exists())` 改成两张都小于 60 KB，并且第二张含 `100 MHz` 与 `4 KB`。只允许这个文件名。

若 `sample-23-g071-pins.svg` 达到或超过 60 KB，把 `3 mA`、`2 MHz`、`30 pF` 拆到 `g071_pc13() -> Svg`，保存为 `assets/diagrams/sample-23-pc13.svg`。第一张仍含 `pin 1`、`PC11`、`pin 12`、`PF2-NRST`、`pin 46`、`PA14`。同样只允许这个第二张文件名。拆开仍超过 60 KB 时，停下来在实施 PR 里写字节数，不把图画回简笔。

- [ ] **Step 4: 运行测试并提交**

Run: `python3 stm32-book/tests/test_batch7_chapters.py Batch7FigureTests -v`

Expected: OK。

```bash
git add tools/gen_sample_figures.py assets/diagrams/sample-20-which-manual.svg assets/diagrams/sample-21-which-part.svg assets/diagrams/sample-22-sim-boundary.svg assets/diagrams/sample-23-g071-pins.svg assets/README.md stm32-book/tests/test_batch7_chapters.py
git commit -m "fig: 第 20、21、22、23 章的静态主图"
```

只有真的拆图时，才把第二张 SVG 加进这一笔。不要在这一笔里改章节正文，也不要改已有二十张主图。

### Task 4: Short auxiliary GIFs

**Files:**
- Modify: `tools/gen_gifs.py`（只在 `BUILDERS` 末尾追加四个键。不改已有二十四个函数的函数体）
- Create: `assets/gif/which-manual.gif`
- Create: `assets/gif/which-part.gif`
- Create: `assets/gif/sim-usart.gif`
- Create: `assets/gif/g071-pin1.gif`
- Modify: `assets/README.md`（第五节「上面 24 张 GIF」改为「上面 28 张 GIF」。`同目录还有 20 个 *-zh.gif` 那一句不要改）
- Modify: `stm32-book/tests/test_batch7_chapters.py`
- Test: `stm32-book/tests/test_batch7_chapters.py`

**Interfaces:**
- Consumes: `Gif`、`Canvas`、`C`、`chrome()`，画布 `W, H = 480, 300`。已有 `BUILDERS` 的前 24 个键顺序不变。
- Produces: `which_manual_gif()`、`which_part_gif()`、`sim_usart_gif()`、`g071_pin1_gif()`。`BUILDERS` 的最后四个键是 `which-manual`、`which-part`、`sim-usart`、`g071-pin1`。每条 GIF 的帧数在 3 到 12 之间，文件小于 500 KB。

72000 Hz 和 `0xAA` 只在静态主图上，不进 `which_manual_gif`。`0x1FFFF000` 被套到 ZET6 上的失败只在静态主图上，不进 `which_part_gif`。12800 和 USART2 只在静态主图上，不进 `sim_usart_gif`。把第 1 脚画成 VBAT、以及 PC13 上的灯，只在静态主图上，不进 `g071_pin1_gif`。

- [ ] **Step 1: 把 GIF 断言加进测试**

在 `stm32-book/tests/test_batch7_chapters.py` 的 import 区加上 `import importlib.util`。在 `Batch7FigureTests` 之后、`if __name__` 之前追加：

```python
def _load_gifs():
    path = ROOT / "tools" / "gen_gifs.py"
    spec = importlib.util.spec_from_file_location("gen_gifs_batch7", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Batch7GifTests(unittest.TestCase):
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
        self.assertEqual(
            list(gifs.BUILDERS)[-4:],
            ["which-manual", "which-part", "sim-usart", "g071-pin1"],
        )
        self.assertEqual(28, len(gifs.BUILDERS))
        source = (ROOT / "tools" / "gen_gifs.py").read_text(encoding="utf-8")
        manual_src = source.split("def which_manual_gif", 1)[1].split("def which_part_gif", 1)[0]
        part_src = source.split("def which_part_gif", 1)[1].split("def sim_usart_gif", 1)[0]
        sim_src = source.split("def sim_usart_gif", 1)[1].split("def g071_pin1_gif", 1)[0]
        pin_src = source.split("def g071_pin1_gif", 1)[1].split("BUILDERS", 1)[0]
        self.assertIn("PA9", manual_src)
        self.assertIn("0xA5", manual_src)
        self.assertIn("pin 30", manual_src)
        self.assertNotIn("72000", manual_src)
        self.assertNotIn("0xAA", manual_src)
        self.assertIn("0x410", part_src)
        self.assertIn("64", part_src)
        self.assertIn("512 KB", part_src)
        self.assertNotIn("0x1FFFF000", part_src)
        self.assertIn("C13", sim_src)
        self.assertIn("pin 2", sim_src)
        self.assertIn("0x40013800", sim_src)
        self.assertIn("115200", sim_src)
        self.assertNotIn("12800", sim_src)
        self.assertNotIn("USART2", sim_src)
        self.assertIn("pin 1", pin_src)
        self.assertIn("PC11", pin_src)
        self.assertIn("pin 46", pin_src)
        self.assertIn("PA14", pin_src)
        self.assertNotIn("VBAT", pin_src)
        self.assertNotIn("LED", pin_src)
        for name in ("which-manual", "which-part", "sim-usart", "g071-pin1"):
            gif = gifs.BUILDERS[name]()
            self.assertGreaterEqual(len(gif.frames), 3)
            self.assertLessEqual(len(gif.frames), 12)
            path = ROOT / "assets" / "gif" / f"{name}.gif"
            self.assertLess(path.stat().st_size, 500 * 1024, path.name)
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `python3 stm32-book/tests/test_batch7_chapters.py Batch7GifTests -v`

Expected: FAIL，`which-manual` 不在 `BUILDERS` 里。

- [ ] **Step 3: 追加四个 BUILDERS 并只生成这四条 GIF**

在 `tools/gen_gifs.py` 的 `one_slot()` 之后、`BUILDERS = {` 之前插入：

```python
def which_manual_gif():
    """Show pin 30 opening DS5319 onto PA9, then mark 0xA5.

    72000 Hz and 0xAA stay on the static SVG.
    """
    g = Gif(W, H, delay=12)
    notes = (
        "pin 30",
        "DS5319",
        "PA9",
        "0xA5",
        "PM0075",
        "READOUT KEY",
    )
    for index, note in enumerate(notes):
        c = Canvas(W, H)
        chrome(c, "WHICH MANUAL", "PM", "AUX GIF  0xA5")
        c.panel(16, 48, 448, 28, C.PANEL, C.STROKE)
        c.text("pin 30", 28, 58, C.MUTED, 1)
        c.text(note, 28, 120, C.TEXT, 1)
        c.text(f"FRAME {index + 1} OF 6", 28, 160, C.MUTED, 1)
        c.text("PA9", 28, 200, C.GREEN, 1)
        c.text("0xA5", 28, 222, C.CYAN, 1)
        c.text("PRINT THE MISS ON THE STATIC SVG", 28, 248, C.DIM, 1)
        g.add(c)
    return g


def which_part_gif():
    """Read 0x410, show 64, and keep the ZET6 512 KB off this cell.

    Drawing 0x1FFFF000 onto the ZET6 stays on the static SVG.
    """
    g = Gif(W, H, delay=12)
    notes = (
        "0x410",
        "0x1FFFF7E0",
        "64 KB",
        "C8",
        "512 KB",
        "NOT THIS CELL",
    )
    for index, note in enumerate(notes):
        c = Canvas(W, H)
        chrome(c, "WHICH PART", "C8", "AUX GIF  64 KB")
        c.panel(16, 48, 448, 28, C.PANEL, C.STROKE)
        c.text("0x410", 28, 58, C.MUTED, 1)
        c.text(note, 28, 120, C.TEXT, 1)
        c.text(f"FRAME {index + 1} OF 6", 28, 160, C.MUTED, 1)
        c.text("64 KB", 28, 200, C.GREEN, 1)
        c.text("512 KB NOT THIS CELL", 28, 222, C.CYAN, 1)
        c.text("PRINT THE MISS ON THE STATIC SVG", 28, 248, C.DIM, 1)
        g.add(c)
    return g


def sim_usart_gif():
    """Point key C13 at pin 2, blink once, then mark 115200.

    12800 and USART2 stay on the static SVG.
    """
    g = Gif(W, H, delay=12)
    notes = (
        "C13",
        "pin 2",
        "PC13",
        "LAMP",
        "0x40013800",
        "115200",
    )
    for index, note in enumerate(notes):
        c = Canvas(W, H)
        chrome(c, "SIM USART", "C13", "AUX GIF  115200")
        c.panel(16, 48, 448, 28, C.PANEL, C.STROKE)
        c.text("0x40013800", 28, 58, C.MUTED, 1)
        c.text(note, 28, 120, C.TEXT, 1)
        c.text(f"FRAME {index + 1} OF 6", 28, 160, C.MUTED, 1)
        c.text("pin 2", 28, 200, C.GREEN, 1)
        c.text("115200", 28, 222, C.CYAN, 1)
        c.text("PRINT THE MISS ON THE STATIC SVG", 28, 248, C.DIM, 1)
        g.add(c)
    return g


def g071_pin1_gif():
    """Count pin 1 as PC11, then mark pin 46 PA14.

    VBAT on pin 1 and an LED on PC13 stay on the static SVG.
    """
    g = Gif(W, H, delay=12)
    notes = (
        "pin 1",
        "PC11",
        "COUNT",
        "pin 46",
        "PA14",
        "SWCLK",
    )
    for index, note in enumerate(notes):
        c = Canvas(W, H)
        chrome(c, "G071 PIN 1", "LQFP64", "AUX GIF  PC11")
        c.panel(16, 48, 448, 28, C.PANEL, C.STROKE)
        c.text("pin 1", 28, 58, C.MUTED, 1)
        c.text(note, 28, 120, C.TEXT, 1)
        c.text(f"FRAME {index + 1} OF 6", 28, 160, C.MUTED, 1)
        c.text("PC11", 28, 200, C.GREEN, 1)
        c.text("pin 46 PA14", 28, 222, C.CYAN, 1)
        c.text("PRINT THE MISS ON THE STATIC SVG", 28, 248, C.DIM, 1)
        g.add(c)
    return g
```

`BUILDERS` 字典在 `"one-slot": one_slot,` 后面追加，不要改前面的键：

```python
    "which-manual": which_manual_gif,
    "which-part": which_part_gif,
    "sim-usart": sim_usart_gif,
    "g071-pin1": g071_pin1_gif,
```

只生成这四条，不要重跑已有 24 条：

```bash
python3 tools/gen_gifs.py which-manual which-part sim-usart g071-pin1
```

Expected: 四行 `[ok]`，每条帧数是 6，体积远小于 500 KB。

`assets/README.md` 第五节把「上面 24 张 GIF」改成「上面 28 张 GIF」。在 GIF 表末尾追加这四条的一行说明：它们是辅图，正常路径分别是 PA9 与 `0xA5`、`0x410` 与 64 KB、`C13` 与 115200、第 1 脚 PC11 与第 46 脚 PA14。`同目录还有 20 个 *-zh.gif` 那一句保持原样。

- [ ] **Step 4: 运行测试并提交**

Run: `python3 stm32-book/tests/test_batch7_chapters.py Batch7GifTests -v`

Expected: OK。

```bash
git add tools/gen_gifs.py assets/gif/which-manual.gif assets/gif/which-part.gif assets/gif/sim-usart.gif assets/gif/g071-pin1.gif assets/README.md stm32-book/tests/test_batch7_chapters.py
git commit -m "fig: 第 20、21、22、23 章的短 GIF 辅图"
```

不要在这一笔里改已有 24 条 GIF 的像素，也不要改章节正文。

### Task 5: Thicken chapter 20 in both languages

**Files:**
- Modify: `docs/20-学习资源与工具链.md`
- Modify: `docs/en/20-resources.md`
- Modify: `stm32-book/manifest.json` 与 `stm32-book/manifest-en.json`（只改第 20 章罗盘。这一任务不追加 `sources` 对象）
- Modify: `stm32-book/tests/test_batch7_chapters.py`
- Test: `stm32-book/tests/test_batch7_chapters.py`

**Interfaces:**
- Consumes: `which_manual()` 已写出 `assets/diagrams/sample-20-which-manual.svg`。`which_manual_gif()` 已写出 `assets/gif/which-manual.gif`。Task 1 的锁定文件。已有 id `pm0056`、`pm0075-rdp`、`rm0008-tim`、`rm0008-usart`、`ds5319-usart`、`rm0008` 只被引用，对象不改。
- Produces: 中英第 20 章各一套四块。罗盘 `sources` 成为下面测试里的 `compass`。`sources` 对象的最后两个键仍是 `ds5319-nrst`、`ds5319-lse`。视频块与锁定文件 `baseline` 上的字节相同。`baseline_chapter(rev: str, path: str) -> str`、`_fetch_baseline(rev: str) -> None`、`_git_show(rev: str, path: str) -> str | None`。后面的任务调用 `baseline_chapter`，不要再贴这三份函数，也不要改回裸的 `git show`。

学习目标锚点：中文 `## 📌 学习目标`，英文 `## 📌 Learning goals`。四块插在 `<!-- /video:ch20 -->` 之后、这个锚点之前。不要改锚点文字。

- [ ] **Step 1: 把基线取回函数和章节断言加进测试**

在 `test_batch7_chapters.py` 顶部补上 `import json`、`import os`、`import subprocess`。在 `ROOT = ...` 之后插入：

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
            f"batch-7 baseline {rev}:{path} is not in this checkout and could not be fetched"
        )
    return blob
```

在 `Batch7GifTests` 之后、`if __name__` 之前追加：

```python
class Batch7ManualChapterTests(unittest.TestCase):
    def test_chapter_20_has_four_blocks_and_the_same_numbers(self) -> None:
        zh_path = ROOT / "docs" / "20-学习资源与工具链.md"
        en_path = ROOT / "docs" / "en" / "20-resources.md"
        zh = zh_path.read_text(encoding="utf-8")
        en = en_path.read_text(encoding="utf-8")
        self.assertTrue(zh.startswith("# 20 学习资源与工具链"))
        self.assertTrue(en.startswith("# 20 Learning resources and the toolchain"))
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
        self.assertNotIn("## ⚠️ Common traps and how to check them", en)
        self.assertNotIn("## ⚠️ Pitfalls and troubleshooting", zh)
        self.assertNotIn("## ⚠️ Pitfalls and troubleshooting", en)
        self.assertIn("## 📌 学习目标", zh)
        self.assertIn("## 📌 Learning goals", en)
        self.assertIn("## 🧠 核心原理", zh)
        self.assertIn("## 🧠 Core ideas", en)
        self.assertNotIn("90%", zh)
        self.assertNotIn("90%", en)
        self.assertNotIn("RDP=0xAA", zh)
        self.assertNotIn("RDP=0xAA", en)
        self.assertNotIn("Product/Package Manual", zh)
        self.assertNotIn("Product/ Package Manual", zh)
        self.assertNotIn("Product/ Package Manual", en)
        self.assertNotIn("Product/Package Manual", en)
        zh_blocks = zh.split("## 原理与边界", 1)[1].split("## 📌 学习目标", 1)[0]
        en_blocks = en.split("## Principle and boundary", 1)[1].split("## 📌 Learning goals", 1)[0]
        for blocks in (zh_blocks, en_blocks):
            for token in (
                "PM0056",
                "0xE000ED28",
                "71",
                "999",
                "500",
                "1000",
                "72000",
                "0xA5",
                "0x00A5",
                "0x1FFFF800",
                "0x271",
                "115200",
                "12800",
                "PA9",
                "0xAA",
                "#source-pm0056",
                "#source-rm0008-tim",
                "#source-pm0075-rdp",
                "#source-rm0008-usart",
                "#source-rm0008",
            ):
                self.assertIn(token, blocks)
            self.assertNotIn("90%", blocks)
            self.assertNotIn("3333", blocks)
            self.assertNotIn("167 ns", blocks)
            self.assertNotIn("14 µA", blocks)
            self.assertNotIn("24 µA", blocks)
        self.assertIn("第 30 脚", zh_blocks)
        self.assertIn("pin 30", en_blocks)
        self.assertIn("编程手册", zh_blocks)
        self.assertIn("programming manual", en_blocks.lower())
        self.assertIn("../assets/diagrams/sample-20-which-manual.svg", zh)
        self.assertIn("../../assets/diagrams/sample-20-which-manual.svg", en)
        self.assertIn("../assets/gif/which-manual.gif", zh)
        self.assertIn("../../assets/gif/which-manual.gif", en)
        zh_key = zh.split("## 关键插图", 1)[1].split("## 时序或状态", 1)[0]
        en_key = en.split("## Key figures", 1)[1].split("## Timing or state", 1)[0]
        self.assertLess(zh_key.index("sample-20-which-manual.svg"), zh_key.index("which-manual.gif"))
        self.assertLess(en_key.index("sample-20-which-manual.svg"), en_key.index("which-manual.gif"))
        self.assertIn("自绘", zh_key)
        self.assertIn("Drawn for this book", en_key)
        self.assertNotIn("示意图", zh_key)
        self.assertIn("project-structure.svg", zh)
        lock = json.loads(
            (ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch7-20-21-22-23-lock.json").read_text(
                encoding="utf-8"
            )
        )
        for path, text in ((zh_path, zh), (en_path, en)):
            rel = path.relative_to(ROOT).as_posix()
            baseline = baseline_chapter(lock["baseline"], rel)
            marker = "<!-- video:ch20 -->"
            end = "<!-- /video:ch20 -->"
            self.assertEqual(
                baseline.split(marker, 1)[1].split(end, 1)[0],
                text.split(marker, 1)[1].split(end, 1)[0],
            )
        zh_manifest = json.loads((ROOT / "stm32-book" / "manifest.json").read_text(encoding="utf-8"))
        en_manifest = json.loads((ROOT / "stm32-book" / "manifest-en.json").read_text(encoding="utf-8"))
        self.assertEqual(
            ["ds5319-nrst", "ds5319-lse"],
            list(zh_manifest["sources"])[-2:],
        )
        self.assertEqual(
            ["ds5319-nrst", "ds5319-lse"],
            list(en_manifest["sources"])[-2:],
        )
        compass = [
            "project-credits",
            "stm32cube-f4",
            "clion-embedded",
            "platformio-vscode",
            "pm0056",
            "pm0075-rdp",
            "rm0008-tim",
            "rm0008-usart",
            "ds5319-usart",
            "rm0008",
        ]
        guide = zh_manifest["chapter_guides"]["20-学习资源与工具链.md"]
        guide_en = en_manifest["chapter_guides"]["20-resources.md"]
        self.assertEqual(compass, guide["sources"])
        self.assertEqual(compass, guide_en["sources"])
        self.assertEqual(
            "遇到参数、寄存器、内核、应用与工具问题时，怎样选对资料层级并冻结版本？",
            guide["question"],
        )
        self.assertIn("0xA5", guide["boundary"])
        self.assertIn("PM0056", guide["boundary"])
        self.assertNotIn("0xAA", guide["boundary"])
        self.assertIn("0xA5", guide_en["boundary"])
        self.assertIn("programming manual", guide_en["boundary"])
        frozen = json.loads(baseline_chapter(lock["baseline"], "stm32-book/manifest.json"))
        self.assertEqual(frozen["sources"]["pm0056"], zh_manifest["sources"]["pm0056"])
        self.assertEqual(frozen["sources"]["pm0075-rdp"], zh_manifest["sources"]["pm0075-rdp"])
        self.assertEqual(frozen["sources"]["rm0008-tim"], zh_manifest["sources"]["rm0008-tim"])
        self.assertEqual(frozen["sources"]["rm0008"], zh_manifest["sources"]["rm0008"])
```

`question` 的中文句子一个字都不改。

- [ ] **Step 2: 运行测试，确认失败**

Run: `python3 stm32-book/tests/test_batch7_chapters.py Batch7ManualChapterTests -v`

Expected: FAIL，正文里还没有 `## 原理与边界`。若失败原因是 `git show` 找不到对象，先确认测试走的是 `baseline_chapter()`。不要把工作流改成全历史。

- [ ] **Step 3: 改掉和手册冲突的格子，并删掉旧坑标题**

中文 `docs/20-学习资源与工具链.md` 做这五处替换，英文 `docs/en/20-resources.md` 做对应的五处。不要改视频块。

中文结论里的 90% 那一句换成：

```markdown
**结论**：ST 的资料全部免费，从 **st.com** 出发；开发用 **CubeMX（配置）+ CubeIDE（编译调试）+ CubeProgrammer（烧录/选项字节）** 三件套。
```

英文那一节已经没有 90%。不要为了对称把百分比写回去。保持现有的 `covers most of what you will do` 也可以，但四块里不要写 90%，也不要写 most 的百分比。

中文手册命名的结论和 PM 行换成：

```markdown
**结论**：**RM 讲寄存器（怎么写）、DS 讲参数（是什么）、PM 讲内核编程、AN 讲怎么做、UM 讲工具怎么用**。查寄存器位找 RM。查电气参数和引脚找 DS。查 Cortex-M3 的故障寄存器找 PM0056。PM0056 是编程手册，不是封装手册。

| **PM** | Programming Manual | Cortex-M3 内核寄存器。PM0056 不是封装手册。封装和第 30 脚在 DS5319 | PM0056 |
```

英文对应换成：

```markdown
**Conclusion**: **an RM is the registers, a DS is the part, a PM is the core programming manual, an AN is how to do one job, and a UM is how to use a tool.** PM0056 is the Cortex-M3 programming manual, not a package manual. The package and pin 30 are in DS5319.

| **PM** | Programming Manual | Cortex-M3 core registers. PM0056 is not a package manual. The package and pin 30 are in DS5319 | PM0056 |
```

中文示例 1 的频率那一条换成：

```markdown
- 读「PWM mode」小节：占空比 = `CCR / (ARR+1)`，频率 = `fCK_PSC / ((ARR+1) × (PSC+1))`。计数时钟 72 MHz，PSC = 71，ARR = 999，CCR = 500：`72e6 / (72 × 1000) = 1000` Hz，占空比 50%。只写 `fCK_CNT / (ARR+1)` 会得到 `72e6 / 1000 = 72000` Hz。
```

英文示例 1 的频率那一条换成：

```markdown
- Read the "PWM mode" section: duty cycle = `CCR / (ARR+1)`, frequency = `fCK_PSC / ((ARR+1) × (PSC+1))`. With a 72 MHz counter clock, PSC = 71, ARR = 999, and CCR = 500: `72e6 / (72 × 1000) = 1000` Hz, and the duty cycle is 50%. Writing only `fCK_CNT / (ARR+1)` yields `72e6 / 1000 = 72000` Hz.
```

中文示例 3 整段换成：

```markdown
**示例 3：这颗 C8 的 DMA 不要去 AN4031 找 FIFO**
- AN4031 讲的是 F2/F4 的 DMA。这颗 C8 没有那只 FIFO。
- 有没有这只外设、容量是多少，去 DS5319 和签名寄存器。位定义去 RM0008。
- 这一段不引入 FIFO 阈值，也不新编 F103 的 DMA 通道号。
```

英文示例 3 整段换成：

```markdown
**Example 3: do not look up an FIFO for this C8 in AN4031**
- AN4031 is the F2/F4 DMA controller. This C8 does not have that FIFO.
- Whether the peripheral exists, and how large the memory is, go to DS5319 and the signature registers. Bit definitions go to RM0008.
- This section does not introduce an FIFO threshold, and it does not invent an F103 DMA channel number.
```

中文代码块里的 `STM32_Programmer_CLI -c port=SWD mode=UR -ob RDP=0xAA` 整行删掉，换成注释：

```text
# 选项字节在 0x1FFFF800。读允许键的低字节是 0xA5，手册印成 0x00A5。
# 写回这个键会先整片擦除主闪存。0xAA 不是这只键。
# 命令行工具的开关名不是选项字节的值。先对 PM0075，再决定要不要擦除。
```

英文代码块里的 `STM32_Programmer_CLI -c port=SWD mode=UR -ob RDP=0xAA` 整行删掉，换成注释：

```text
# The option bytes are at 0x1FFFF800. The low byte of the readout-allowed key is 0xA5. The manual prints 0x00A5.
# Writing that key back mass-erases the main Flash first. 0xAA is not this key.
# A command-line switch name is not the option-byte value. Check PM0075 before deciding to erase.
```

两份文件都不得再含 `RDP=0xAA`。

删掉从 `## ⚠️ 常见坑与排查` 到下一个 `##` 之前的整段，英文删掉从 `## ⚠️ Common traps and how to check them` 到下一个 `##` 之前的整段。不要留空标题。CubeProgrammer 报 RDP 的那一行不搬回去，它的账在四块里。其余仍成立的行（按手册编号检索、HAL 名对寄存器名、教程版本、PlatformIO、OpenOCD 的 cfg、KiCad 库路径、逻辑分析仪采样率、克隆 J-Link）挪到 `## 🧪 动手实验` 前面，用一段普通段落加一张表，不要新起 `##`。英文同样挪到 `## 🧪 Hands-on labs` 前面。OpenOCD 的 `3333` 留在代码节，不进这张表，也不进四块。

- [ ] **Step 4: 在学习目标之前插入四块**

中文插在 `<!-- /video:ch20 -->` 之后、`## 📌 学习目标` 之前：

```markdown
## 原理与边界

这一章是索引，不是第二套外设教程。订货号用 STM32F103C8T6 来举例。

PM0056 Rev 7 是 Cortex-M3 编程手册。`CFSR` 在 `0xE000ED28`。封装、第 30 脚和电气参数在 DS5319，不在 PM。G0 的内核手册不是 PM0056。这一章不打开 PM0223，也不编 G0 的故障寄存器。

PWM 跟第 05 章同一笔。频率是 `fCK_PSC / ((ARR+1) × (PSC+1))`。计数时钟 72 MHz，PSC = 71，ARR = 999，CCR = 500：`72e6 / (72 × 1000) = 1000` Hz，占空比 `500 / 1000 = 50%`。只写 `fCK_CNT / (ARR+1)` 会得到 `72e6 / 1000 = 72000` Hz。这是主图的失败路径。

读允许键是 `0xA5`。选项字节在 `0x1FFFF800`。手册印 `0x00A5`。写回这个键会先整片擦除主闪存。`0xAA` 不是这只键。擦除态 `0xFF` 仍然保持保护，这句跟 PM0075 同一笔。

第 30 脚 PA9、第 31 脚 PA10 在 DS5319。BRR `0x271` 的位在 RM0008。72 MHz 下是 115200，8 MHz 下是 12800。AN4031 的 FIFO 不回答这颗 C8。F103 有没有某只外设、容量是多少，去 DS5319 和签名寄存器。位定义去 RM0008。

## 关键插图

<p align="center">
  <img src="../assets/diagrams/sample-20-which-manual.svg" width="760" alt="PM0056 是编程手册；丢掉 (PSC+1) 时这一组数是 72000 Hz；读允许键是 0xA5，不是 0xAA">
  <br><sub>▲ 自绘。正常路径：第 30 脚去 DS5319 读 PA9，0x271 去 RM0008，72 MHz 下是 115200，硬故障去 PM0056 的 0xE000ED28，读允许键是 0xA5（PM0075 印成 0x00A5）。失败路径：用 PM0056 查第 30 脚，PSC = 71 仍在但丢掉 (PSC+1) 得到 72000 Hz，或者把选项字节写成 0xAA。出处是 [PM0056](#source-pm0056)、[PM0075](#source-pm0075-rdp) 和 [RM0008](#source-rm0008-usart)。</sub>
</p>

<p align="center">
  <img src="../assets/gif/which-manual.gif" width="640" alt="问题从第 30 脚切到 DS5319 的 PA9，再标出 0xA5">
  <br><sub>▲ 网页和公众号辅图。只播放正常路径：第 30 脚到 PA9，再标 0xA5。印刷以静态主图为准。72000 Hz 和 0xAA 不在这条 GIF 上。</sub>
</p>

`project-structure.svg` 仍是目录辅图。目录树不代替这三本书。

## 时序或状态

| 问题 | 打开哪本 | 读到的数 | 对错 |
| --- | --- | --- | --- |
| 第 30 脚 | DS5319 | PA9 | 正常 |
| BRR | RM0008 | `0x271` 在 72 MHz 下是 115200 | 正常 |
| 硬故障 | PM0056 | `0xE000ED28` | 正常 |
| 读保护 | PM0075 | `0xA5`，印成 `0x00A5`，地址 `0x1FFFF800` | 正常 |
| 用 PM 查封装脚 | PM0056 | 这一本没有第 30 脚 | 失败 |
| PSC = 71，ARR = 999，丢掉 `(PSC+1)` | RM0008 的时基 | 72000 Hz，不是 1000 Hz | 失败 |
| 把 `0xAA` 写成选项字节 | PM0075 | `0xAA` 不是读允许键 | 失败 |

8 MHz 下同一只 `0x271` 是 12800。先把 PLL 装回 72 MHz，线上才回到 115200。

## 坑与出处卡

| 现象 | 处理方向 | 链接 | 允许的主张 |
| --- | --- | --- | --- |
| 在 PM0056 里找不到第 30 脚 | 引脚去 DS5319，内核故障去 PM0056 | [#source-pm0056](#source-pm0056) | PM0056 是 Cortex-M3 编程手册。`CFSR` 在 `0xE000ED28`。这一行不规定封装图 |
| 按旧公式配出约 72 kHz | 把 `(PSC+1)` 乘回去 | [#source-rm0008-tim](#source-rm0008-tim) | PSC = 71、ARR = 999、CCR = 500，在 72 MHz 下是 1000 Hz、50%。丢掉 `(PSC+1)` 得到 72000 Hz |
| 解除读保护时写入 `0xAA` | 选项字节低字节是 `0xA5` | [#source-pm0075-rdp](#source-pm0075-rdp) | 地址 `0x1FFFF800`。手册印 `0x00A5`。写回会先整片擦除。`0xAA` 不是读允许键 |
| 数据手册里搜不到 BRR 的位 | 位在 RM0008，脚在 DS5319 | [#source-rm0008-usart](#source-rm0008-usart) | `0x271` 在 72 MHz 下是 115200，在 8 MHz 下是 12800。第 30 脚是 PA9 |
| 用 AN4031 的 FIFO 解释 F103 的 DMA 错误 | F103 不按那只 FIFO 查 | [#source-rm0008](#source-rm0008) | AN4031 讲的是 F2/F4。这一行不引入 FIFO 阈值，也不新编 F103 的 DMA 通道号 |
```

英文插在 `<!-- /video:ch20 -->` 之后、`## 📌 Learning goals` 之前：

```markdown
## Principle and boundary

This chapter is an index, not a second peripheral tutorial. The order code used as the example is STM32F103C8T6.

PM0056 Rev 7 is the Cortex-M3 programming manual. `CFSR` is at `0xE000ED28`. The package, pin 30, and the electrical limits are in DS5319, not in the PM. The G0 core manual is not PM0056. This chapter does not open PM0223, and it does not invent a G0 fault register.

PWM uses the same account as chapter 05. The frequency is `fCK_PSC / ((ARR+1) × (PSC+1))`. With a 72 MHz counter clock, PSC = 71, ARR = 999, and CCR = 500: `72e6 / (72 × 1000) = 1000` Hz, and the duty cycle is `500 / 1000 = 50%`. Writing only `fCK_CNT / (ARR+1)` yields `72e6 / 1000 = 72000` Hz. That is the failure path on the main figure.

The readout-allowed key is `0xA5`. The option bytes are at `0x1FFFF800`. The manual prints `0x00A5`. Writing this key back mass-erases the main Flash first. `0xAA` is not this key. The erased state `0xFF` still keeps protection. That sentence is the same account as PM0075.

Pin 30 is PA9 and pin 31 is PA10, both in DS5319. The BRR bits for `0x271` are in RM0008. At 72 MHz that value is 115200. At 8 MHz it is 12800. The FIFO in AN4031 does not answer this C8. Whether an F103 has a peripheral, and how large the memory is, go to DS5319 and the signature registers. Bit definitions go to RM0008.

## Key figures

<p align="center">
  <img src="../../assets/diagrams/sample-20-which-manual.svg" width="760" alt="PM0056 is the programming manual; dropping (PSC+1) makes this set of numbers 72000 Hz; the readout-allowed key is 0xA5, not 0xAA">
  <br><sub>▲ Drawn for this book. Normal path: pin 30 is PA9 in DS5319, 0x271 is in RM0008 and is 115200 at 72 MHz, a HardFault goes to 0xE000ED28 in PM0056, and the readout-allowed key is 0xA5 (PM0075 prints 0x00A5). Failure path: looking up pin 30 in PM0056, keeping PSC = 71 while dropping (PSC+1) and getting 72000 Hz, or writing the option byte as 0xAA. Sources: [PM0056](#source-pm0056), [PM0075](#source-pm0075-rdp), and [RM0008](#source-rm0008-usart).</sub>
</p>

<p align="center">
  <img src="../../assets/gif/which-manual.gif" width="640" alt="The question moves from pin 30 to PA9 in DS5319, then marks 0xA5">
  <br><sub>▲ Auxiliary figure for the web and for posts. It plays only the normal path: pin 30 to PA9, then 0xA5. Print from the static figure. 72000 Hz and 0xAA are not on this GIF.</sub>
</p>

`project-structure.svg` stays as the directory auxiliary figure. The directory tree does not replace these three manuals.

## Timing or state

| Question | Open | The number you read | Result |
| --- | --- | --- | --- |
| Pin 30 | DS5319 | PA9 | Normal |
| BRR | RM0008 | `0x271` is 115200 at 72 MHz | Normal |
| HardFault | PM0056 | `0xE000ED28` | Normal |
| Readout protection | PM0075 | `0xA5`, printed as `0x00A5`, at `0x1FFFF800` | Normal |
| Looking up a package pin in the PM | PM0056 | This manual has no pin 30 | Failure |
| PSC = 71, ARR = 999, `(PSC+1)` dropped | The RM0008 time base | 72000 Hz, not 1000 Hz | Failure |
| Writing `0xAA` into the option byte | PM0075 | `0xAA` is not the readout-allowed key | Failure |

At 8 MHz the same `0x271` is 12800. Put the PLL back at 72 MHz before the wire returns to 115200.

## Pitfalls and source cards

| What you see | What to do | Link | Claim this source may support |
| --- | --- | --- | --- |
| Pin 30 cannot be found in PM0056 | Pins go to DS5319. Core faults go to PM0056 | [#source-pm0056](#source-pm0056) | PM0056 is the Cortex-M3 programming manual. `CFSR` is at `0xE000ED28`. This row does not define a package drawing |
| The old formula produces about 72 kHz | Multiply `(PSC+1)` back in | [#source-rm0008-tim](#source-rm0008-tim) | PSC = 71, ARR = 999, and CCR = 500 are 1000 Hz and 50% at 72 MHz. Dropping `(PSC+1)` yields 72000 Hz |
| `0xAA` was written while clearing readout protection | The low byte of the option byte is `0xA5` | [#source-pm0075-rdp](#source-pm0075-rdp) | The address is `0x1FFFF800`. The manual prints `0x00A5`. Writing it back mass-erases first. `0xAA` is not the readout-allowed key |
| The datasheet search does not find the BRR bits | The bits are in RM0008. The pin is in DS5319 | [#source-rm0008-usart](#source-rm0008-usart) | `0x271` is 115200 at 72 MHz and 12800 at 8 MHz. Pin 30 is PA9 |
| AN4031's FIFO is used to explain an F103 DMA fault | Do not look up that FIFO on an F103 | [#source-rm0008](#source-rm0008) | AN4031 is about F2/F4. This row does not introduce an FIFO threshold, and it does not invent an F103 DMA channel number |
```

- [ ] **Step 5: 只改罗盘，不追加来源对象**

两份 manifest 里第 20 章罗盘的 `sources` 改成测试里的 `compass`。中文键是 `20-学习资源与工具链.md`。英文键是 `20-resources.md`。`question` 和 `deliverable` 不改。

中文 `boundary` 在原句后面接上：`PM0056 是 Cortex-M3 编程手册，不是封装手册。读允许键是 0xA5，不是 0xAA。`

英文 `boundary` 在原句后面接上：`PM0056 is the Cortex-M3 programming manual, not a package manual. The readout-allowed key is 0xA5, not 0xAA.`

不要改 `pm0056`、`pm0075-rdp`、`rm0008-tim`、`rm0008-usart`、`ds5319-usart`、`rm0008` 的对象。`sources` 的最后两个键仍是 `ds5319-nrst` 和 `ds5319-lse`。

- [ ] **Step 6: 运行测试并提交**

Run: `python3 stm32-book/tests/test_batch7_chapters.py Batch7ManualChapterTests -v`

Expected: OK。

```bash
git add docs/20-学习资源与工具链.md docs/en/20-resources.md stm32-book/manifest.json stm32-book/manifest-en.json stm32-book/tests/test_batch7_chapters.py
git commit -m "book: 加厚第 20 章，PM0056 是编程手册，读允许键是 0xA5"
```

不要在这一笔里升版本号。不要改第 05 章和第 06 章。

### Task 6: Thicken chapter 21 in both languages

**Files:**
- Modify: `docs/21-原理图与实物图鉴.md`
- Modify: `docs/en/21-board-maps.md`
- Modify: `stm32-book/manifest.json` 与 `stm32-book/manifest-en.json`（按固定顺序追加九个 `sources`，并改第 21 章罗盘。不改已有 id）
- Modify: `stm32-book/tests/test_batch7_chapters.py`
- Test: `stm32-book/tests/test_batch7_chapters.py`

**Interfaces:**
- Consumes: `which_part()` 已写出 `assets/diagrams/sample-21-which-part.svg`。`which_part_gif()` 已写出 `assets/gif/which-part.gif`。Task 2 的九个 absorb 条目。Task 5 的 `baseline_chapter()`。
- Produces: 中英第 21 章各一套四块。两份 `sources` 的最后九个键等于 Task 2 的 `ABSORB`。第 21 章罗盘 `sources` 成为下面测试里的 `compass`。第 22 章和第 23 章这一任务还不改正文。

学习目标锚点：中文 `## 📌 学习目标`，英文 `## 📌 Goals`。四块插在视频结束后那段「不是实拍」的引用块之后、学习目标之前。英文第 21 章的硬件节仍叫 `## 🛠️ How to read a minimum-system schematic`，代码节仍叫 `## 💻 Read the chip's identity`，实验仍叫 `## 🧪 Try it`，资源仍叫 `## 🔗 Further reading`。不要改成第 20 章的英文措辞。

- [ ] **Step 1: 把章节断言加进测试**

在 `test_batch7_chapters.py` 末尾、`if __name__` 之前追加 `Batch7PartChapterTests`。断言至少包括：

- 一级标题仍是 `21 原理图与实物图鉴` 和 `21 Schematics and board maps`。中文标题不含「图注」。
- 四个中文块标题和四个英文块标题各出现一次。
- 中文不再有 `## ⚠️ 常见坑与排查`。英文不再有单独一行 `## ⚠️ Pitfalls`。两份都没有 `## ⚠️ Pitfalls and troubleshooting`。
- 仍有 `## 🧠 核心原理` 和 `## 🧠 The boards`。
- 四块（从原理标题切到学习目标标题）同时含有：`0xE0042000`、`0x410`、`0x1FFFF7E0`、`0x1FFFF7E8`、`64`、`20`、`0x1FFFF000`、`0x1FFFB000`、`512`、`128`、`100`、`1024`、`192`、`4`、`168`、`270`、`#source-rm0008-signature`、`#source-rm0008-hd-boot`、`#source-ds5792`、`#source-ds10314`、`#source-ds8626`、`#source-ds5319-hse`、`#source-ds5319-gpio`。
- 四块含有「6 pF 不是必须值」和 `6 pF is not a required value` 里的对应语言句子，并且含有 `20 pF` 不是必须值的句子。四块不含 `N=200`，不含 `PLLM`。
- 四块写明 330 Ω 不是本书的外接灯。中文含 `330`，英文含 `330`。
- 四块不含 `10 kΩ`，不含 `10 k`。
- 四块不含 `14 µA`、`24 µA`、`167 ns`。
- 主图路径在 GIF 路径之前。图注含「自绘」和 `Drawn for this book`。
- 视频块 `<!-- video:ch21 -->` 到 `<!-- /video:ch21 -->` 与 `baseline_chapter()` 的字节相同。
- `sources` 的最后九个键是 `rm0008-signature`、`rm0008-map`、`rm0008-hd-boot`、`ds5792`、`ds10314`、`ds8626`、`ds5319-hse`、`um1724-mco`、`ds12232-lqfp64`。每个新对象的 `url`、`snapshot`、`license`、`accessed` 中英相同。`accessed` 是 `2026-10-25`。`title` 用清单的 `title_zh` / `title_en`，`authority` 用 `authority_zh` / `authority_en`。
- 九个 `scope` 用下面这九对，中文在前，英文在后：

```python
SCOPES = {
    "rm0008-signature": (
        "第 21 章。DBGMCU_IDCODE 在 0xE0042000，低 12 位的中容量值是 0x410。闪存容量在 0x1FFFF7E0，低 16 位，单位 KB，C8 读 64。UID 从 0x1FFFF7E8 起。不把 128 KB 写成 C8 的数据手册容量。",
        "Chapter file 21. DBGMCU_IDCODE is at 0xE0042000. The medium-density DevID in the low 12 bits is 0x410. Flash size is at 0x1FFFF7E0, low 16 bits, in KB. A C8 reads 64. The UID starts at 0x1FFFF7E8. Does not call 128 KB the C8 datasheet size.",
    ),
    "rm0008-map": (
        "第 22 章。GPIOA 在 0x40010800，GPIOB 在 0x40010C00，GPIOC 在 0x40011000，USART1 在 0x40013800。usart1 不是 USART2。不写套接字端口 3456。",
        "Chapter file 22. GPIOA is at 0x40010800, GPIOB at 0x40010C00, GPIOC at 0x40011000, and USART1 at 0x40013800. usart1 is not USART2. Does not record socket port 3456.",
    ),
    "rm0008-hd-boot": (
        "第 21 章。STM32F103xC/xD/xE 的系统存储器起点默认是 0x1FFFB000。C8 的 0x1FFFF000 留在已有 rm0008-boot，不改那条对象。",
        "Chapter file 21. System memory for STM32F103xC, xD, and xE defaults to 0x1FFFB000. The C8 address 0x1FFFF000 stays on rm0008-boot. That object is not edited.",
    ),
    "ds5792": (
        "第 21 章。STM32F103ZET6 是 xE：512 KB 闪存、64 KB SRAM、最高 72 MHz、LQFP144。xC 的 256 KB / 48 KB 和 xD 的 384 KB 在 ZET6 上作废。不把 DS5319 的 64 KB / 20 KB 抄进这条。",
        "Chapter file 21. STM32F103ZET6 is the xE row: 512 KB of Flash, 64 KB of SRAM, 72 MHz maximum, LQFP144. The xC 256 KB / 48 KB row and the xD 384 KB row are void on the ZET6. Does not copy the DS5319 64 KB / 20 KB pair.",
    ),
    "ds10314": (
        "第 21 章。STM32F411xE 是 512 KB 闪存、128 KB SRAM、最高 100 MHz。CEU6 和 RET6 都是 xE。xC 的 256 KB 在这两只订货号上作废。晶振范围 4 MHz 到 26 MHz。不记录 PLL 的 M、N、P。",
        "Chapter file 21. STM32F411xE is 512 KB of Flash, 128 KB of SRAM, and 100 MHz maximum. CEU6 and RET6 are both xE. The xC 256 KB is void on those two order codes. Crystal range is 4 MHz to 26 MHz. Does not record PLL M, N, or P.",
    ),
    "ds8626": (
        "第 21 章。STM32F407VGT6：最高 1 MB 闪存、最高 168 MHz。SRAM 最高 192 KB，含 64 KB CCM，另有 4 KB 备份 SRAM。4 KB 不并进 192。F407VE 的 512 KB 在 VGT6 上作废。",
        "Chapter file 21. STM32F407VGT6: 1 MB of Flash maximum and 168 MHz maximum. SRAM maximum is 192 KB including 64 KB of CCM, plus 4 KB of backup SRAM. The 4 KB is not inside the 192 KB. The F407VE 512 KB bin is void on VGT6.",
    ),
    "ds5319-hse": (
        "第 21 章。HSE 的 CL1 与 CL2 按 5 pF 到 25 pF 跟晶振选。20 pF 不是必须值。不改 ds5319-lse。LSE 的 5 pF 到 15 pF 仍以那条为准。",
        "Chapter file 21. HSE CL1 and CL2 are chosen from 5 pF to 25 pF with the crystal. 20 pF is not required. Does not edit ds5319-lse. The LSE 5 pF to 15 pF range stays on that object.",
    ),
    "um1724-mco": (
        "第 21 章旁注。只记 NUCLEO-F411RE 时钟输入节印出的 MCO 频率。没印出频率时四块不写 Nucleo 的输入频率。不记录 PLL 乘数。不改已有 um1724。",
        "Chapter file 21 note. Records only an MCO frequency the NUCLEO-F411RE clock section prints. If none is printed, the four sections do not state a Nucleo input frequency. Does not record PLL multipliers. Does not edit um1724.",
    ),
    "ds12232-lqfp64": (
        "第 23 章。LQFP64 第 1 脚 PC11，第 3 脚 PC13，第 6 脚 VBAT，第 12 脚 PF2-NRST，第 35 脚 PB15 是 UCPD1_CC2，第 36 脚 PA8 是 UCPD1_CC1，第 45 脚 PA13，第 46 脚 PA14-BOOT0。PC13 到 PC15 只能灌大约 3 mA。SRAM 是 32 KB 或 36 KB。不写待机微安。不改已有 ds12232。",
        "Chapter file 23. LQFP64 pin 1 is PC11, pin 3 is PC13, pin 6 is VBAT, pin 12 is PF2-NRST, pin 35 PB15 is UCPD1_CC2, pin 36 PA8 is UCPD1_CC1, pin 45 is PA13, and pin 46 is PA14-BOOT0. PC13 through PC15 can sink only about 3 mA. SRAM is 32 KB or 36 KB. Does not write a standby microamp. Does not edit ds12232.",
    ),
}
```

- 第 21 章罗盘：

```python
compass = [
    "ds5319",
    "project-credits",
    "rm0008-signature",
    "rm0008-hd-boot",
    "ds5792",
    "ds10314",
    "ds8626",
    "ds5319-hse",
    "um1724-mco",
    "ds5319-lse",
    "ds5319-nrst",
    "ds5319-gpio",
    "rm0008-boot",
]
```

中文键 `21-原理图与实物图鉴.md`，英文键 `21-board-maps.md`。`question` 不改。`boundary` 含 `0x410` 和 `DS5792`。英文 boundary 含 `0x410` 和 `DS5792`。

- 已有 `ds5319`、`rm0008-boot`、`ds5319-lse`、`um1724` 与 `baseline_chapter()` 读出的对象逐字段相同。

- [ ] **Step 2: 运行测试，确认失败**

Run: `python3 stm32-book/tests/test_batch7_chapters.py Batch7PartChapterTests -v`

Expected: FAIL，正文里还没有 `## 原理与边界`，或者 `sources` 末尾还不是这九个 id。

- [ ] **Step 3: 改掉和前面各章冲突的格子**

中文和英文一起改。7 张板图的文件名不改，图也不重画。

板卡一览里 F407 那一格 `1 MB / 192 KB` 改成 `1 MB / 192 KB + 4 KB`。后面 Discovery 详情表里的 `1 MB / 192 KB` 同样改成 `1 MB / 192 KB + 4 KB`。英文两处同样改。不要写成 196 KB。

F411 详情里的主频格子：

中文现在是 `100 MHz（HSE 8 MHz，PLLM=8/N=200/P=2）`。换成 `最高 100 MHz。DS10314 不印 PLLM、N、P`。

英文现在是 `100 MHz (HSE 8 MHz, PLLM=8/N=200/P=2)`。换成 `100 MHz maximum. DS10314 does not print PLLM, N, or P`。

BlackPill 板上写着 25 MHz 的那一格保留，旁边加一句：这是板级说法，不是数据手册替它选的频率，也不编 PLL。不要把 25 MHz 写进出处卡。

最小系统表：

- HSE 行从 `2×20 pF` 改成 `负载电容按 5 pF 到 25 pF 跟晶振选，20 pF 不是必须值`。英文从 `HSE 8 MHz + 2×20 pF` 改成 `HSE 8 MHz. Load capacitors are chosen from 5 pF to 25 pF with the crystal. 20 pF is not required`。
- LSE 行从 `2×6 pF` 改成 `负载电容按 5 pF 到 15 pF 跟晶振选，6 pF 不是必须值`。英文从 `LSE 32.768 kHz + 2×6 pF` 改成 `LSE 32.768 kHz. Load capacitors are chosen from 5 pF to 15 pF with the crystal. 6 pF is not required`。
- 复位行从 `10 kΩ 上拉 + 100 nF` 改成 `外部电容 0.1 µF（图 31）。上拉的千欧不进出处卡`。英文从 `NRST + 10 kΩ pull-up + 100 nF to ground + a button` 改成 `External capacitor 0.1 µF (Figure 31). The pull-up kilohm does not enter a source card`。这一行不要留 `10 kΩ` 或 `10 k`。BOOT 行里已有的下拉千欧留在原处，不搬进四块。

BOOT 表后面加一段，中文：

```markdown
这张表只属于 STM32F103C8T6。BOOT0 = 0 进 `0x08000000`。BOOT1 = 0 且 BOOT0 = 1 进 `0x1FFFF000`。STM32F103ZET6 的系统存储器默认从 `0x1FFFB000` 起。把 `0x1FFFF000` 套到 ZET6 上是失败路径。
```

英文在 BOOT 表后面加：

```markdown
This table belongs only to the STM32F103C8T6. BOOT0 = 0 enters `0x08000000`. BOOT1 = 0 and BOOT0 = 1 enter `0x1FFFF000`. System memory on the STM32F103ZET6 defaults to `0x1FFFB000`. Putting `0x1FFFF000` on the ZET6 is the failure path.
```

中文身份说明在 `0x410` 之后补上：`0x1FFFF7E0` 的低 16 位读 64，单位 KB。读数不是 64，就不要按 C8 的 64 KB 往下算。UID 从 `0x1FFFF7E8` 起。英文在 `Device id `0x410` is a medium-density F103.` 之后补上：`The low 16 bits at 0x1FFFF7E0 read 64, in KB. If the read is not 64, do not keep allocating the C8's 64 KB. The UID starts at 0x1FFFF7E8.` 代码块里已有的三个地址不要改。

接线总览里 `LED + 330Ω | PA5` 那一行改成：`图上若标 PA5 与 330 Ω，那不是本书的外接灯。本书外接灯是第 10 脚和 270 Ω。` 英文 `LED + 330Ω | PA5 | Push-pull output` 改成：`If the drawing marks PA5 and 330 Ω, that is not this book's external lamp. This book's external lamp is pin 10 and 270 Ω.` 不重画 `peripheral-wiring.svg`。

删掉 `## ⚠️ 常见坑与排查` 和英文 `## ⚠️ Pitfalls` 整节。RTC 那一行不要再写「补焊 6 pF」。若还要留在实验前的普通表里，写成：补焊 32.768 kHz，负载电容在 5 pF 到 15 pF 里跟晶振选，6 pF 不是必须值。不要新起 `##`。

- [ ] **Step 4: 在学习目标之前插入四块**

中文插在「不是实拍」引用块之后、`## 📌 学习目标` 之前。英文插在对应引用块之后、`## 📌 Goals` 之前。图路径中文是 `../assets/...`，英文是 `../../assets/...`。

```markdown
## 原理与边界

订货号先分开写。C8 的四块只用 DS5319 和 RM0008。ZET6、F411、F407 各用自己的数据手册。

C8：`0xE0042000` 的低 12 位是 `0x410`。`0x1FFFF7E0` 的低 16 位读 64，单位 KB。UID 从 `0x1FFFF7E8` 起。DS5319：闪存 64 KB，SRAM 20 KB，LQFP48，最高 72 MHz。读数不是 64，就不要按 C8 往下算。丝印写 128 KB 是失败旁注。系统存储器是 `0x1FFFF000`。

STM32F103ZET6 不在 DS5319。DS5792 的 xE 行：512 KB 闪存，64 KB SRAM，72 MHz，LQFP144。系统存储器默认从 `0x1FFFB000` 起。把 C8 的 `0x1FFFF000` 套到这颗料上，是主图的失败路径。xC 的 256 KB / 48 KB 和 xD 的 384 KB 在 ZET6 上作废。

STM32F411CEU6 和 STM32F411RET6：512 KB 闪存，128 KB SRAM，最高 100 MHz。xC 的 256 KB 在这两只料上作废。能算出 100 MHz 的那组 PLL 乘数不是 DS10314 的格子，这一节不写它们。晶振允许 4 MHz 到 26 MHz。BlackPill 的 25 MHz 是板级说法。Nucleo 的输入频率只有 `um1724-mco` 记下印出的频率之后才写进旁注。没记下之前，这里只写 100 MHz 这个上限。

STM32F407VGT6：1 MB 闪存，最高 168 MHz。SRAM 最高 192 KB，含 64 KB CCM，另有 4 KB 备份 SRAM。不要把 4 KB 加进 192 再叫成 196 KB，也不要把它从书上抹掉。1024 KB 就是这 1 MB。

LSE 是 5 pF 到 15 pF，6 pF 不是必须值。HSE 按 5 pF 到 25 pF 跟晶振选，20 pF 不是必须值。NRST 的外部电容是 0.1 µF。外接灯是第 10 脚、270 Ω。PA5 加 330 Ω 不是本书的外接灯。第 2 脚 PC13 的板载灯低电平亮，不能当电流源。

## 关键插图

<p align="center">
  <img src="../assets/diagrams/sample-21-which-part.svg" width="760" alt="C8 的 DevID 是 0x410，容量读数是 64 KB；ZET6 的 512 KB 在 DS5792，系统存储器不是 0x1FFFF000">
  <br><sub>▲ 自绘。正常路径：读数是 64，按 DS5319 往下算；ZET6 单独标 512 KB 和 64 KB，系统存储器 0x1FFFB000。失败路径：丝印像 C8 但读数不是 64，仍去链接 128 KB；或者把 ZET6 的 Bootloader 画在 0x1FFFF000。旁注：F411xE 是 512 KB / 128 KB / 100 MHz，F407VG 是 1 MB、168 MHz、192 KB 加 4 KB。出处是 [RM0008 签名](#source-rm0008-signature)、[DS5792](#source-ds5792) 和 [大容量启动行](#source-rm0008-hd-boot)。</sub>
</p>

<p align="center">
  <img src="../assets/gif/which-part.gif" width="640" alt="读到 0x410，容量格显示 64，ZET6 的 512 KB 不在这一格">
  <br><sub>▲ 网页和公众号辅图。只播放正常路径：0x410，容量 64，ZET6 的 512 KB 不在这一格。印刷以静态主图为准。把 0x1FFFF000 套到 ZET6 上的失败不在这条 GIF 上。</sub>
</p>

`bluepill-stm32f103c8t6.svg` 和 `peripheral-wiring.svg` 留作辅图。7 张板图都不替换。

## 时序或状态

| 订货号 | 手册 | 闪存 / SRAM | 系统存储器或主频上限 | 能不能套 C8 |
| --- | --- | --- | --- | --- |
| STM32F103C8T6 | DS5319 | 64 KB / 20 KB | `0x1FFFF000` | 能 |
| 读数不是 64 | 签名寄存器 | 不要按 64 KB 分配 | 先停 | 不能 |
| STM32F103ZET6 | DS5792 | 512 KB / 64 KB | `0x1FFFB000` | 不能套 C8 的地址 |
| STM32F411CEU6 与 RET6 | DS10314 | 512 KB / 128 KB | 最高 100 MHz | 不能套 72 MHz 的等待周期 |
| STM32F407VGT6 | DS8626 | 1024 KB，192 KB 加 4 KB | 最高 168 MHz | 不能把 4 KB 算进 192 |

电容：LSE 5 pF 到 15 pF；HSE 5 pF 到 25 pF。20 pF 和 6 pF 都不是必须值。灯：第 10 脚、270 Ω。330 Ω 是失败。

## 坑与出处卡

| 现象 | 处理方向 | 链接 | 允许的主张 |
| --- | --- | --- | --- |
| 丝印是 C8，容量寄存器不是 64 | 停止按 DS5319 的 64 KB 分配 | [#source-rm0008-signature](#source-rm0008-signature) | `0xE0042000` 低 12 位的中容量值是 `0x410`。`0x1FFFF7E0` 低 16 位的单位是 KB。UID 从 `0x1FFFF7E8` 起 |
| 大板的 Bootloader 按 `0x1FFFF000` 找 | ZET6 用大容量的起点 | [#source-rm0008-hd-boot](#source-rm0008-hd-boot) | 默认是 `0x1FFFB000`。C8 的 `0x1FFFF000` 在 ZET6 上作废 |
| 把 ZET6 的容量写成 64 KB / 20 KB | 打开 DS5792，不要打开 DS5319 | [#source-ds5792](#source-ds5792) | ZET6 是 512 KB 闪存和 64 KB SRAM，最高 72 MHz |
| Nucleo 被写成一组 PLL 乘数的出厂时钟 | 只保留 100 MHz 这个上限 | [#source-ds10314](#source-ds10314) | F411xE 是 512 KB 闪存、128 KB SRAM、最高 100 MHz。xC 的 256 KB 在 CEU6 和 RET6 上作废。这一行不规定 PLL 乘数 |
| Discovery 的 RAM 预算写成 192 KB 并且用满 | 备份 SRAM 另有 4 KB | [#source-ds8626](#source-ds8626) | 192 KB 含 64 KB CCM。4 KB 备份 SRAM 不在这 192 里。最高 168 MHz，VGT6 的闪存是 1 MB |
| 按旧表焊了 6 pF 或 20 pF，并说手册要求如此 | 电容跟晶振在范围内选 | [#source-ds5319-hse](#source-ds5319-hse) | HSE 默认 5 pF 到 25 pF，20 pF 不是必须值。LSE 的 5 pF 到 15 pF 仍以已有 `ds5319-lse` 为准，这一行不改那条对象 |
| 外接灯按接线总览用了 330 Ω 和 PA5 | 本书外接灯是第 10 脚和 270 Ω | [#source-ds5319-gpio](#source-ds5319-gpio) | 第 2 脚 PC13 不能当电流源。这一行不新造第三只电阻 |
```

英文四块用下面这一份，不要再把 PLL 乘数写回去。NRST 的 0.1 µF 用已有 `#source-ds5319-nrst` 在原理节交叉引用，不要在出处卡里新写千欧。10 kΩ、25 MHz 和 WeAct 的版本号不进出处卡。

```markdown
## Principle and boundary

Write the order codes apart. The C8 sections use only DS5319 and RM0008. The ZET6, the F411, and the F407 each use their own datasheet.

C8: the low 12 bits at `0xE0042000` are `0x410`. The low 16 bits at `0x1FFFF7E0` read 64, in KB. The UID starts at `0x1FFFF7E8`. DS5319: 64 KB of Flash, 20 KB of SRAM, LQFP48, 72 MHz maximum. If the read is not 64, do not keep allocating as a C8. A silkscreen that says 128 KB is the failure note. System memory is `0x1FFFF000`.

The STM32F103ZET6 is not in DS5319. The DS5792 xE row is 512 KB of Flash, 64 KB of SRAM, 72 MHz, LQFP144. System memory defaults to `0x1FFFB000`. Putting the C8 address `0x1FFFF000` on this part is the failure path. The xC 256 KB / 48 KB row and the xD 384 KB row are void on the ZET6.

STM32F411CEU6 and STM32F411RET6: 512 KB of Flash, 128 KB of SRAM, 100 MHz maximum. The xC 256 KB bin is void on those two parts. A PLL triple that can be multiplied out to 100 MHz is not a DS10314 cell, and this section does not write those multipliers. The crystal may be from 4 MHz to 26 MHz. A BlackPill marked 25 MHz is a board claim. Write a Nucleo input frequency only after `um1724-mco` records a printed frequency. Until then, this section keeps only the 100 MHz cap.

STM32F407VGT6: 1 MB of Flash, 168 MHz maximum. SRAM maximum is 192 KB, including 64 KB of CCM, plus 4 KB of backup SRAM. Do not add the 4 KB into the 192 KB and call the sum main SRAM, and do not drop the 4 KB. 1024 KB is this 1 MB.

LSE is 5 pF to 15 pF. 6 pF is not a required value. Choose the HSE load from 5 pF to 25 pF with the crystal. 20 pF is not a required value. The external capacitor on NRST is 0.1 µF. The external lamp is pin 10 and 270 Ω. PA5 plus 330 Ω is not this book's lamp. The on-board lamp on pin 2, PC13, lights when low and must not source current.

## Key figures

<p align="center">
  <img src="../../assets/diagrams/sample-21-which-part.svg" width="760" alt="The C8 DevID is 0x410 and the size read is 64 KB. The ZET6's 512 KB is in DS5792, and its system memory is not 0x1FFFF000">
  <br><sub>▲ Drawn for this book. The normal path reads 64 and stays on DS5319. The ZET6 is marked on its own as 512 KB and 64 KB, with system memory at 0x1FFFB000. The failure path still links 128 KB when the size read is not 64, or draws the ZET6 bootloader at 0x1FFFF000. The note: F411xE is 512 KB / 128 KB / 100 MHz, and F407VG is 1 MB, 168 MHz, 192 KB plus 4 KB. Sources: [the RM0008 signature](#source-rm0008-signature), [DS5792](#source-ds5792), and [the high-density boot row](#source-rm0008-hd-boot).</sub>
</p>

<p align="center">
  <img src="../../assets/gif/which-part.gif" width="640" alt="A read of 0x410, a size cell of 64, and the ZET6 512 KB kept off this cell">
  <br><sub>▲ Auxiliary figure for the web and for posts. It plays only the normal path: 0x410, size 64, and the ZET6 512 KB off this cell. Print from the static figure. The failure that puts 0x1FFFF000 on the ZET6 is not on this GIF.</sub>
</p>

`bluepill-stm32f103c8t6.svg` and `peripheral-wiring.svg` stay as auxiliary figures. None of the seven board drawings is replaced.

## Timing or state

| Order code | Manual | Flash / SRAM | System memory or clock cap | May it wear the C8 map |
| --- | --- | --- | --- | --- |
| STM32F103C8T6 | DS5319 | 64 KB / 20 KB | `0x1FFFF000` | Yes |
| The size read is not 64 | Signature register | Do not allocate 64 KB | Stop first | No |
| STM32F103ZET6 | DS5792 | 512 KB / 64 KB | `0x1FFFB000` | Do not reuse the C8 address |
| STM32F411CEU6 and RET6 | DS10314 | 512 KB / 128 KB | 100 MHz maximum | Do not reuse the 72 MHz wait states |
| STM32F407VGT6 | DS8626 | 1024 KB, 192 KB plus 4 KB | 168 MHz maximum | Do not fold the 4 KB into the 192 KB |

Capacitors: LSE 5 pF to 15 pF; HSE 5 pF to 25 pF. Neither 20 pF nor 6 pF is required. The lamp is pin 10 and 270 Ω. 330 Ω is the miss.

## Pitfalls and source cards

| What you see | What to do | Link | Claim this source may support |
| --- | --- | --- | --- |
| The silkscreen says C8 and the size register is not 64 | Stop allocating the DS5319 64 KB | [#source-rm0008-signature](#source-rm0008-signature) | The medium-density value in the low 12 bits of `0xE0042000` is `0x410`. The low 16 bits of `0x1FFFF7E0` are in KB. The UID starts at `0x1FFFF7E8` |
| A large board's bootloader is sought at `0x1FFFF000` | Use the high-density base for the ZET6 | [#source-rm0008-hd-boot](#source-rm0008-hd-boot) | The default is `0x1FFFB000`. The C8 address `0x1FFFF000` is void on the ZET6 |
| The ZET6 is written down as 64 KB / 20 KB | Open DS5792, not DS5319 | [#source-ds5792](#source-ds5792) | The ZET6 is 512 KB of Flash and 64 KB of SRAM, at up to 72 MHz |
| A Nucleo is described as leaving the factory on a PLL triple | Keep only the 100 MHz cap | [#source-ds10314](#source-ds10314) | F411xE is 512 KB of Flash, 128 KB of SRAM, and 100 MHz maximum. The xC 256 KB bin is void on CEU6 and RET6. This row does not set PLL multipliers |
| A Discovery RAM budget is written as 192 KB and then filled | Backup SRAM is another 4 KB | [#source-ds8626](#source-ds8626) | 192 KB includes 64 KB of CCM. The 4 KB of backup SRAM is not inside that 192 KB. The maximum is 168 MHz, and VGT6 Flash is 1 MB |
| The old table was soldered as 6 pF or 20 pF and called a manual requirement | Choose the capacitors with the crystal, inside the range | [#source-ds5319-hse](#source-ds5319-hse) | HSE defaults to 5 pF to 25 pF. 20 pF is not required. The LSE range of 5 pF to 15 pF stays on the existing `ds5319-lse` object. This row does not edit that object |
| The wiring overview used 330 Ω and PA5 for the external lamp | This book's external lamp is pin 10 and 270 Ω | [#source-ds5319-gpio](#source-ds5319-gpio) | Pin 2, PC13, must not source current. This row does not invent a third resistor |
```

若 Task 3 拆出了 `sample-21-other-parts.svg`，关键插图在第一张图之后再引用它，图注写明这是 F411 与 F407 的局部，仍是自绘。没拆就不要引用这个文件名。

- [ ] **Step 5: 追加九个来源对象并改罗盘**

按 Task 2 清单的 `url`、`snapshot`、`license` 原样复制。`title` 用 `title_zh` / `title_en`，`authority` 用 `authority_zh` / `authority_en`。`accessed` 是 `2026-10-25`。`scope` 用本任务测试里的 `SCOPES`。中文对象按 `ABSORB` 的顺序追加在 `stm32-book/manifest.json` 的 `sources` 末尾，英文同样追加。这一次把九个都加上，包括第 22 章和第 23 章才在正文里点名的 `rm0008-map` 和 `ds12232-lqfp64`，这样顺序不会被后面的任务打乱。不要改已有 id 的任何字段。

两份罗盘的 `sources` 改成测试里的 `compass`。中文 `boundary` 在原句后面接上：`C8 的 DevID 是 0x410，0x1FFFF7E0 读 64 KB。STM32F103ZET6 的 512 KB 闪存和 64 KB SRAM 在 DS5792，不在 DS5319。`

英文 `boundary` 在原句后面接上：`A C8 DevID is 0x410, and 0x1FFFF7E0 reads 64 KB. The STM32F103ZET6's 512 KB of Flash and 64 KB of SRAM are in DS5792, not in DS5319.`

`question` 和 `deliverable` 不改。

- [ ] **Step 6: 运行测试并提交**

Run: `python3 stm32-book/tests/test_batch7_chapters.py Batch7PartChapterTests -v`

Expected: OK。

```bash
git add docs/21-原理图与实物图鉴.md docs/en/21-board-maps.md stm32-book/manifest.json stm32-book/manifest-en.json stm32-book/tests/test_batch7_chapters.py
git commit -m "book: 加厚第 21 章，C8 读 0x410 和 64 KB，ZET6 不套 0x1FFFF000"
```

不要在这一笔里改第 18 章，不要改 `rm0008-boot`，不要升版本号。

### Task 7: Thicken chapter 22 in both languages

**Files:**
- Modify: `docs/22-仿真实验Wokwi与Renode.md`
- Modify: `docs/en/22-simulation-wokwi-renode.md`
- Modify: `stm32-book/manifest.json` 与 `stm32-book/manifest-en.json`（只改第 22 章罗盘。不追加、不重排 `sources`）
- Modify: `stm32-book/tests/test_batch7_chapters.py`
- Test: `stm32-book/tests/test_batch7_chapters.py`

**Interfaces:**
- Consumes: `sim_boundary()` 与 `sim_usart_gif()` 的成品。Task 6 已经写入的 `rm0008-map`。Task 5 的 `baseline_chapter()`。
- Produces: 中英第 22 章各一套四块。罗盘 `sources` 成为下面的 `compass`。`## ⚠️ 仿真替不了的事` 和 `## ⚠️ What simulation will not do for you` 各仍出现一次。`sources` 键顺序与 Task 6 结束时相同。

学习目标锚点：中文 `## 📌 学习目标`，英文 `## 📌 Learning goals`。保留 `## 🧠 先选哪一家` 和 `## 🧠 Which one to open first`。

- [ ] **Step 1: 把章节断言加进测试**

追加 `Batch7SimChapterTests`。断言至少包括：

- 一级标题仍是 `22 仿真实验：Wokwi 与 Renode`（全角冒号）和 `22 Simulation labs: Wokwi and Renode`。中文标题不含「仿真实战」。
- 四个块标题各一次。
- `## ⚠️ 仿真替不了的事` 和 `## ⚠️ What simulation will not do for you` 各一次。没有 `## ⚠️ 常见坑与排查`，没有 `## ⚠️ Pitfalls and troubleshooting`。
- 四块同时含有 `0x40013800`、`0x40011000`、`PC13`、`C13`、`PA9`、`0x271`、`115200`、`12800`、`0x3C`、`0x78`、`4.7`、`#source-rm0008-map`、`#source-rm0008-usart`、`#source-ds5319-gpio`、`#source-ds5319-adc`、`#source-rm0008-i2c`。
- 中文四块含「第 2 脚」和「第 30 脚」。英文四块含 `pin 2` 和 `pin 30`。
- 四块写明灯亮不能证明波特率，并写明当前 Wokwi 模型没有 DMA。中文含 `没有 DMA`。英文含 `no DMA`。
- 四块不含 `3456`。动手实验那一节可以仍有 `3456`。用分块断言，不要对整份文件禁止 `3456`。
- 四块不含 `14 µA`、`24 µA`、`167 ns`。
- 主图在 GIF 之前。图注含「自绘」和 `Drawn for this book`。仍引用 `toolchain-flow.svg`。
- 视频块与基线相同。
- 罗盘：

```python
compass = [
    "wokwi-bluepill",
    "renode-stm32",
    "rm0008-map",
    "rm0008-usart",
    "ds5319-gpio",
    "ds5319-adc",
    "rm0008-i2c",
]
```

中文键 `22-仿真实验Wokwi与Renode.md`，英文键 `22-simulation-wokwi-renode.md`。`question` 不改。中文 boundary 含 `0x40013800`。英文 boundary 含 `0x40013800`。

- `wokwi-bluepill`、`renode-stm32`、`rm0008-usart`、`rm0008-i2c` 与基线逐字段相同。`rm0008-map` 与 Task 6 写入的对象相同，这一任务不改它的 snapshot。
- `sources` 的最后九个键仍是 Task 2 的 `ABSORB`。

- [ ] **Step 2: 运行测试，确认失败**

Run: `python3 stm32-book/tests/test_batch7_chapters.py Batch7SimChapterTests -v`

Expected: FAIL，正文里还没有 `## 原理与边界`。

- [ ] **Step 3: 保留已经对上的句子**

正文里已经写着 `usart1` 的地址 `0x40013800`、不要把它说成 USART2、键 `C13` 接到 PC13、低电平亮、当前模型没有 DMA、端口 3456 在 Renode 脚本说明里。这些句子留在原节。不要改 `sim/`。不要把 3456 搬进四块。四块再把同一笔账写成能算回去的表。

- [ ] **Step 4: 在学习目标之前插入四块**

中文：

```markdown
## 原理与边界

订货号仍是 STM32F103C8T6。仿真器只负责让这四笔账变得看得见。模型没实现的东西，不能拿来否定手册。

USART1 在 `0x40013800`。GPIOC 在 `0x40011000`。`usart1` 必须对上这个地址。把它说成 USART2，是主图的失败路径。第 30 脚 PA9、第 31 脚 PA10 跟第 06 章同一笔。

键 `C13` 指到第 2 脚 PC13。板载灯低电平亮，这只脚只能灌电流。键 `A0` 指到第 10 脚 PA0。主图不把灯、ADC 和 WKUP 画成同时接上。键 `A9` 和 `A10` 指到 USART1。图里写成 `PA0` 或 `PC13` 这种芯片名，是失败路径。键名来自板文件的链接，不进出处卡。

模型若停在 HSI 8 MHz，BRR `0x271` 送出的是 12800 bit/s。72 MHz 那一格才是 115200。灯亮不能证明波特率。灯照样可以闪。这是主图的失败路径。

7 位地址是 `0x3C`，HAL 填 `0x78`，`0x3C << 1 = 0x78`。上拉 4.7 kΩ。把 `0x78` 当成 7 位地址，是失败。

当前这页的 Wokwi BluePill 模型没有 DMA。`uart-dma-idle` 和 `adc-dma` 在这里只能核对接线。这句是模型边界，不是新的芯片限额，也不进出处卡。

## 关键插图

<p align="center">
  <img src="../assets/diagrams/sample-22-sim-boundary.svg" width="760" alt="USART1 在 0x40013800；C13 是第 2 脚 PC13；灯亮时 0x271 仍可能是 12800 bit/s">
  <br><sub>▲ 自绘。正常路径：键名对上脚，时钟是 72 MHz，0x271 是 115200，PC13 低电平点亮。失败路径：同一只 0x271 停在 8 MHz，线上 12800，灯却仍然在闪；或者外设被写成 USART2。出处是 [RM0008 存储器映射](#source-rm0008-map) 和第 06 章已经冻结的 [0x271](#source-rm0008-usart)。</sub>
</p>

<p align="center">
  <img src="../assets/gif/sim-usart.gif" width="640" alt="键 C13 指向第 2 脚，然后 0x40013800 标成 115200">
  <br><sub>▲ 网页和公众号辅图。只播放正常路径：键 C13 指向第 2 脚，灯灭亮一次，然后 0x40013800 标成 115200。印刷以静态主图为准。12800 和 USART2 不在这条 GIF 上。</sub>
</p>

`toolchain-flow.svg` 留作辅图。编译箭头不证明波特率。

## 时序或状态

| 看什么 | 手册或键 | 值 | 算不算通过 |
| --- | --- | --- | --- |
| GPIOC | `0x40011000`，键 `C13` | 第 2 脚 PC13，低电平亮 | 正常 |
| USART1 | `0x40013800` | 第 30 脚和第 31 脚 | 正常 |
| 名字写成 USART2 | 基址对不上 | 失败 | 失败 |
| 72 MHz 且 `0x271` | RM0008 | 115200 | 正常 |
| 8 MHz 且 `0x271` | 同一只 BRR | 12800，灯亮也不通过 | 失败 |
| I2C | 第 07 章 | 7 位 `0x3C`，HAL `0x78`，4.7 kΩ | 正常 |
| DMA | 这个 Wokwi 模型没有 DMA | 空闲帧收包不通过 | 不产生新的微秒或欧姆 |

## 坑与出处卡

| 现象 | 处理方向 | 链接 | 允许的主张 |
| --- | --- | --- | --- |
| 分析器里的外设被说成 USART2 | 对基址 `0x40013800` | [#source-rm0008-map](#source-rm0008-map) | 这个地址是 USART1。GPIOC 在 `0x40011000`。这一行不规定套接字端口 |
| 灯在闪，主机却按 115200 解出乱码 | 先看模型是不是还停在 8 MHz | [#source-rm0008-usart](#source-rm0008-usart) | `0x271` 在 72 MHz 下是 115200，在 8 MHz 下是 12800 |
| 仿真图写成 `PC13`，零件挂不上 | 图的键是另一套名字，脚仍是第 2 脚 | [#source-ds5319-gpio](#source-ds5319-gpio) | 第 2 脚 PC13 只能灌电流，低电平点亮是板载灯的接法。这一行不把 Wokwi 的键名升格成手册术语 |
| 外接零件挂在第 10 脚，又拿这只脚当 ADC | 一次只选一种用法 | [#source-ds5319-adc](#source-ds5319-adc) | 第 10 脚是 PA0。这一行不把灯和按键画成同时有效 |
| OLED 地址写成 0x78，扫描器却报 0x3C | 先分清 7 位和 HAL 的写法 | [#source-rm0008-i2c](#source-rm0008-i2c) | `0x3C << 1 = 0x78`。4.7 kΩ 仍以第 07 章为准 |
```

英文插在 `<!-- /video:ch22 -->` 之后、`## 📌 Learning goals` 之前。DMA 没实现、固件路径是占位、端口 3456，留在 `## ⚠️ What simulation will not do for you`。它们不进出处卡，下面这份正文也不写 `3456`。

```markdown
## Principle and boundary

The order code is still STM32F103C8T6. The simulator only makes these four accounts visible. Something the model does not implement cannot be used to contradict the manual.

USART1 is at `0x40013800`. GPIOC is at `0x40011000`. `usart1` has to match that address. Calling it USART2 is the failure path on the main figure. Pin 30 is PA9 and pin 31 is PA10, the same account as chapter 06.

Key `C13` points at pin 2, PC13. The on-board lamp lights when low, and this pin can only sink current. Key `A0` points at pin 10, PA0. The main figure does not draw the lamp, the ADC, and WKUP as connected at the same time. Keys `A9` and `A10` point at USART1. Drawing the chip names `PA0` or `PC13` on this figure is the failure path. The key names come from the board file links and do not enter a source card.

If the model is still on the 8 MHz HSI, BRR `0x271` sends 12800 bit/s. The 72 MHz cell is 115200. The lamp can still blink. That is the failure path on the main figure.

The 7-bit address is `0x3C`. HAL writes `0x78`. `0x3C << 1 = 0x78`. The pull-ups are 4.7 kΩ. Treating `0x78` as the 7-bit address is a failure.

The Wokwi BluePill model on this page has no DMA. `uart-dma-idle` and `adc-dma` can only be checked for wiring here. That sentence is a model boundary, not a new chip limit, and it does not enter a source card.

## Key figures

<p align="center">
  <img src="../../assets/diagrams/sample-22-sim-boundary.svg" width="760" alt="USART1 is at 0x40013800; C13 is pin 2, PC13; while the lamp is lit, 0x271 can still be 12800 bit/s">
  <br><sub>▲ Drawn for this book. Normal path: the key name matches the pin, the clock is 72 MHz, 0x271 is 115200, and PC13 lights the lamp when low. Failure path: the same 0x271 stays at 8 MHz, the wire is 12800, and the lamp is still blinking; or the peripheral is written as USART2. Sources: [the RM0008 memory map](#source-rm0008-map) and the [0x271](#source-rm0008-usart) already frozen in chapter 06.</sub>
</p>

<p align="center">
  <img src="../../assets/gif/sim-usart.gif" width="640" alt="Key C13 points at pin 2, then 0x40013800 is marked 115200">
  <br><sub>▲ Auxiliary figure for the web and for posts. It plays only the normal path: key C13 points at pin 2, the lamp goes off and on once, then 0x40013800 is marked 115200. Print from the static figure. 12800 and USART2 are not on this GIF.</sub>
</p>

`toolchain-flow.svg` stays as an auxiliary figure. A compile arrow does not prove the baud rate.

## Timing or state

| What you look at | Manual or key | Value | Does it pass |
| --- | --- | --- | --- |
| GPIOC | `0x40011000`, key `C13` | Pin 2, PC13, lights when low | Normal |
| USART1 | `0x40013800` | Pin 30 and pin 31 | Normal |
| The name written as USART2 | The base address does not match | Failure | Failure |
| 72 MHz and `0x271` | RM0008 | 115200 | Normal |
| 8 MHz and `0x271` | The same BRR | 12800, and a lit lamp still fails | Failure |
| I2C | Chapter 07 | 7-bit `0x3C`, HAL `0x78`, 4.7 kΩ | Normal |
| DMA | This Wokwi model has no DMA | An idle-frame receive does not pass | No new microsecond or ohm |

## Pitfalls and source cards

| What you see | What to do | Link | Claim this source may support |
| --- | --- | --- | --- |
| The peripheral in the analyzer is called USART2 | Check the base address `0x40013800` | [#source-rm0008-map](#source-rm0008-map) | This address is USART1. GPIOC is at `0x40011000`. This row does not set a socket port |
| The lamp blinks, and the host decodes garbage at 115200 | Check whether the model is still on 8 MHz | [#source-rm0008-usart](#source-rm0008-usart) | `0x271` is 115200 at 72 MHz and 12800 at 8 MHz |
| The simulation drawing says `PC13` and the part will not attach | The drawing's key is another name. The pin is still pin 2 | [#source-ds5319-gpio](#source-ds5319-gpio) | Pin 2, PC13, can only sink current. Lighting when low is how the on-board lamp is wired. This row does not promote a Wokwi key name into a manual term |
| An external part is on pin 10, and that pin is also used as an ADC | Pick one use at a time | [#source-ds5319-adc](#source-ds5319-adc) | Pin 10 is PA0. This row does not draw the lamp and the button as both valid |
| The OLED address is written as 0x78, and the scanner reports 0x3C | Separate the 7-bit address from the HAL spelling | [#source-rm0008-i2c](#source-rm0008-i2c) | `0x3C << 1 = 0x78`. 4.7 kΩ still follows chapter 07 |
```

- [ ] **Step 5: 只改罗盘，不追加来源对象**

两份罗盘的 `sources` 改成 `compass`。中文 `boundary` 在原句后面接上：`USART1 在 0x40013800。灯亮不等于 115200。`

英文 `boundary` 在原句后面接上：`USART1 is at 0x40013800. A lit lamp is not 115200.`

`question` 和 `deliverable` 不改。不要改 `wokwi-bluepill` 和 `renode-stm32` 的许可字符串。不要把它们改写成 MIT。

- [ ] **Step 6: 运行测试并提交**

Run: `python3 stm32-book/tests/test_batch7_chapters.py Batch7SimChapterTests -v`

Expected: OK。

```bash
git add docs/22-仿真实验Wokwi与Renode.md docs/en/22-simulation-wokwi-renode.md stm32-book/manifest.json stm32-book/manifest-en.json stm32-book/tests/test_batch7_chapters.py
git commit -m "book: 加厚第 22 章，USART1 在 0x40013800，C13 是第 2 脚"
```

不要在这一笔里改第 06 章或第 07 章，不要改 `sim/`，不要升版本号。

### Task 8: Thicken chapter 23 in both languages

**Files:**
- Modify: `docs/23-STM32G0引脚.md`
- Modify: `docs/en/23-stm32g0-pins.md`
- Modify: `stm32-book/manifest.json` 与 `stm32-book/manifest-en.json`（只改第 23 章罗盘。不追加、不重排 `sources`）
- Modify: `stm32-book/tests/test_batch7_chapters.py`
- Test: `stm32-book/tests/test_batch7_chapters.py`

**Interfaces:**
- Consumes: `g071_pins()` 与 `g071_pin1_gif()` 的成品。Task 6 已经写入的 `ds12232-lqfp64`。已有 `rm0444`、`an2606`、`an5096`、`st-boot-faq`、`ds12232` 只被引用。
- Produces: 中英第 23 章各一套四块。罗盘 `sources` 成为下面的 `compass`。`## ⚠️ 从 F1 抄代码时最容易摔的几处` 和 `## ⚠️ Common ways an F1 port falls over` 各仍出现一次。启动真值表留在现有正文，不重写。

学习目标锚点：中文 `## 📌 学习目标`，英文 `## 📌 Goals`。保留 `## 🧠 这颗料是谁` 和 `## 🧠 Which part this is`。

- [ ] **Step 1: 把章节断言加进测试**

追加 `Batch7G0ChapterTests`。断言至少包括：

- 一级标题仍是 `23 STM32G0 引脚（G071RB）` 和 `23 STM32G0 pins (G071RB)`。
- 四个块标题各一次。
- 保留的坑标题各一次。没有 `## ⚠️ 常见坑与排查`，没有 `## ⚠️ Pitfalls and troubleshooting`。
- 四块同时含有这些记号：`PC11`、`VBAT`、`PF2`、`PC13`、`PA13`、`PA14`、`PA8`、`PB15`、`128`、`32`、`36`、`64`、`1.7`、`3.6`、`SWCLK`、`UCPD`、`#source-ds12232-lqfp64`、`#source-rm0444`。
- 中文四块含「第 1 脚」「第 6 脚」「第 12 脚」「第 3 脚」「第 45 脚」「第 46 脚」「第 36 脚」「第 35 脚」。英文四块含 `pin 1`、`pin 6`、`pin 12`、`pin 3`、`pin 45`、`pin 46`、`pin 36`、`pin 35`。
- 四块写明没有 CAN，USB 是 UCPD 不是全速设备，32 KB 与 36 KB 不能相加。中文含「不能相加」或「不相加」。英文含 `not the sum`。
- 四块含「不写待机微安」。英文含 `does not write a standby`。四块不含 `µA`，不含 `uA`。
- 四块不含 `0x1FFFF000`，不含 `14 µA`，不含 `167 ns`。
- 主图在 GIF 之前。仍引用 `pinout-stm32g071rb-lqfp64.svg` 和 `g0-boot-swd.svg`。图注含「自绘」和 `Drawn for this book`。
- 视频块与基线相同。
- 身份表不再把 SRAM 单独写成只有 36 KB。中文含 `32 KB（带硬件奇偶）或 36 KB`。英文含 `32 KB with parity or 36 KB without`。
- 罗盘：

```python
compass = [
    "ds12232",
    "rm0444",
    "an5096",
    "an2606",
    "st-boot-faq",
    "ds12232-lqfp64",
]
```

中文键 `23-STM32G0引脚.md`，英文键 `23-stm32g0-pins.md`。`question` 和 `deliverable` 不改。中文 boundary 含 `不写待机微安` 和 `PC11`。英文 boundary 含 `does not write a standby microamp` 和 `PC11`。原来的 `BOOT_LOCK`、`DBG_SWEN`、64 MHz 那些句子还在。

- `ds12232`、`rm0444`、`an5096`、`an2606`、`st-boot-faq` 与基线逐字段相同。
- `sources` 的最后九个键仍是 Task 2 的 `ABSORB`。

- [ ] **Step 2: 运行测试，确认失败**

Run: `python3 stm32-book/tests/test_batch7_chapters.py Batch7G0ChapterTests -v`

Expected: FAIL，正文里还没有 `## 原理与边界`，身份表仍把 SRAM 写成单独的 36 KB。

- [ ] **Step 3: 只改和四块冲突的容量句子**

中文身份表这一格：

```markdown
| Flash 最高 128 KB。SRAM 是 32 KB（带硬件奇偶）或 36 KB（不用奇偶），两者不相加 | 封面；Table 2 |
```

英文换成：

```markdown
| Flash up to 128 KB. SRAM is 32 KB with parity or 36 KB without. The two are not added | Cover; Table 2 |
```

启动真值表、`BOOT_LOCK`、`nBOOT_SEL`、空闪存和 RDP 那些段保持原样。不要把待机微安补进任何一行。不要重画引脚全图，也不要重画 `g0-boot-swd.svg`。

- [ ] **Step 4: 在学习目标之前插入四块**

中文：

```markdown
## 原理与边界

订货号是 STM32G071RB，LQFP64。四笔账都在 DS12232 Rev 5。启动真值表留在后面的正文，主图不再画成一张。不写待机微安。

R = 64 脚。B = 128 KB 闪存。SRAM 是 32 KB（带硬件奇偶）或 36 KB（不用奇偶）。36 KB 不是 32 加 36。最高 64 MHz。供电 1.7 V 到 3.6 V。Cortex-M0+。特性列表没有 CAN，也没有 USB 全速设备控制器。

LQFP64 第 1 脚是 PC11。第 6 脚才是 VBAT。第 12 脚是 PF2-NRST。从 F103 的小封装习惯去数第 1 脚，是主图的失败路径。

第 3 脚是 PC13。PC13、PC14、PC15 只能灌大约 3 mA，输出不超过 2 MHz，负载不超过 30 pF，不能当电流源去点灯。把 LED 接到 PC13，是失败路径。

第 46 脚是 PA14-BOOT0，与 SWCLK 是同一只脚，复位后内部下拉。第 45 脚是 PA13，复位后内部上拉。第 36 脚 PA8 的附加功能是 UCPD1_CC1。第 35 脚 PB15 是 UCPD1_CC2。在这张图上找 CAN_TX，或把 PA11/PA12 叫成 USB_DM/USB_DP，是失败路径。

`BOOT_LOCK=1` 强制主闪存。`nBOOT_SEL=0` 才看 PA14。空闪存还可以转入系统 Bootloader。主图只用旁注指向，不重画启动动画。这一节不写微安。

## 关键插图

<p align="center">
  <img src="../assets/diagrams/sample-23-g071-pins.svg" width="760" alt="第 1 脚是 PC11；第 12 脚是 PF2-NRST；PC13 不能拿来点灯；PA14 与 SWCLK 是同一只脚">
  <br><sub>▲ 自绘。DS12232 Rev 5 的 Figure 9 和 Table 12。正常路径：第 1 脚数到 PC11，调试脚是第 45 脚 PA13 和第 46 脚 PA14-BOOT0。失败路径：第 1 脚被标成 VBAT，LED 接到第 3 脚 PC13，或者在图角找 CAN_TX。SRAM 写成 32 KB 或 36 KB，不要相加。出处是 [DS12232 的 LQFP64 列](#source-ds12232-lqfp64)。</sub>
</p>

<p align="center">
  <img src="../assets/gif/g071-pin1.gif" width="640" alt="从封装左上角数到第 1 脚 PC11，再标出第 46 脚 PA14">
  <br><sub>▲ 网页和公众号辅图。只播放正常路径：第 1 脚 PC11，再标第 46 脚 PA14。印刷以静态主图为准。把第 1 脚画成 VBAT，以及 PC13 上的灯，不在这条 GIF 上。</sub>
</p>

`pinout-stm32g071rb-lqfp64.svg` 和 `g0-boot-swd.svg` 留作辅图。全图和启动动画不代替这四笔账。

## 时序或状态

| 脚号 | 名字 | 复位后或限制 | 能不能照抄 F1 |
| --- | --- | --- | --- |
| 第 1 脚 | PC11 | 不是 VBAT | 不能 |
| 第 6 脚 | VBAT | 不能当成第 1 脚 | 不能 |
| 第 12 脚 | PF2-NRST | 不是一只单独的 NRST 焊盘编号 | 不能 |
| 第 3 脚 | PC13 | 大约 3 mA、2 MHz、30 pF，不能点灯 | 不能 |
| 第 45 脚 | PA13 | 复位后内部上拉 | 脚号不同 |
| 第 46 脚 | PA14-BOOT0 | 复位后内部下拉，与 SWCLK 共用 | 不能当成独立 BOOT0 焊盘 |
| 第 36 脚和第 35 脚 | UCPD1_CC1 和 UCPD1_CC2 | 不是 USB_DM/DP | 不能 |
| 容量 | 闪存 128 KB | SRAM 32 KB 或 36 KB，不相加 | 不能写成 68 KB |
| 在图上找 CAN_TX | 这颗料没有 CAN | 失败 | 不能 |

## 坑与出处卡

| 现象 | 处理方向 | 链接 | 允许的主张 |
| --- | --- | --- | --- |
| 左上角被数成 VBAT | 第 1 脚是 PC11 | [#source-ds12232-lqfp64](#source-ds12232-lqfp64) | 第 6 脚才是 VBAT。第 12 脚是 PF2-NRST |
| PC13 推挽点灯又暗又慢 | 这三只脚不能当电流源 | [#source-ds12232-lqfp64](#source-ds12232-lqfp64) | 注 1：大约 3 mA，不超过 2 MHz，负载不超过 30 pF。第 3 脚是 PC13 |
| 原理图在找 CAN_TX | G071RB 没有 CAN 控制器 | [#source-ds12232-lqfp64](#source-ds12232-lqfp64) | 特性列表没有 CAN。这一行不指定一只 FDCAN 脚 |
| PA11/PA12 被接成 USB 全速 | 这颗料的 USB 能力是 UCPD | [#source-ds12232-lqfp64](#source-ds12232-lqfp64) | 第 36 脚 PA8 是 UCPD1_CC1，第 35 脚 PB15 是 UCPD1_CC2 |
| 拉高 PA14 却仍从主闪存启动 | 先读 `BOOT_LOCK` 和 `nBOOT_SEL` | [#source-rm0444](#source-rm0444) | `BOOT_LOCK=1` 强制主闪存。`nBOOT_SEL=0` 才看 PA14。这一行不新写微安 |
| SRAM 预算写成 68 KB | 32 KB 和 36 KB 是两种用法 | [#source-ds12232-lqfp64](#source-ds12232-lqfp64) | 带奇偶是 32 KB，不用奇偶是 36 KB。B 后缀的闪存是 128 KB。最高 64 MHz |
```

英文插在 `<!-- /video:ch23 -->` 之后、`## 📌 Goals` 之前。空闪存转入系统 Bootloader、RDP 和 `DBG_SWEN` 留在现有启动节，交叉引用已有 `#source-an2606`、`#source-an5096`、`#source-st-boot-faq`。不把那些对象的 snapshot 改写。下面这份正文不写 `0x1FFFF000`，也不写微安符号。

```markdown
## Principle and boundary

The order code is STM32G071RB, LQFP64. All four accounts are in DS12232 Rev 5. The boot truth table stays in the later prose. The main figure is not drawn as that table. This section does not write a standby current.

R means 64 pins. B means 128 KB of Flash. SRAM is 32 KB with parity or 36 KB without. 36 KB is not 32 plus 36, and the two are not the sum. The maximum clock is 64 MHz. The supply is 1.7 V to 3.6 V. The core is a Cortex-M0+. The feature list has no CAN controller and no USB full-speed device.

LQFP64 pin 1 is PC11. Pin 6 is VBAT. Pin 12 is PF2-NRST. Counting pin 1 from the small-package habit of an F103 is the failure path on the main figure.

Pin 3 is PC13. PC13, PC14, and PC15 can sink only about 3 mA. The output stays at or below 2 MHz. The load stays at or below 30 pF. They cannot source an LED. Putting an LED on PC13 is the failure path.

Pin 46 is PA14-BOOT0. It is the same pin as SWCLK, and it is pulled down internally after reset. Pin 45 is PA13, pulled up internally after reset. Pin 36, PA8, has UCPD1_CC1 among its alternate functions. Pin 35, PB15, is UCPD1_CC2. Looking for CAN_TX on this drawing, or calling PA11/PA12 USB_DM/USB_DP, is the failure path.

`BOOT_LOCK=1` forces main Flash. `nBOOT_SEL=0` is when PA14 matters. Empty Flash can still enter the system bootloader. The main figure only points at that with a side note. It does not redraw the boot animation. This section does not write a standby figure.

## Key figures

<p align="center">
  <img src="../../assets/diagrams/sample-23-g071-pins.svg" width="760" alt="Pin 1 is PC11; pin 12 is PF2-NRST; PC13 cannot drive an LED; PA14 is the same pin as SWCLK">
  <br><sub>▲ Drawn for this book. Figure 9 and Table 12 of DS12232 Rev 5. Normal path: pin 1 counts to PC11, and the debug pins are pin 45 PA13 and pin 46 PA14-BOOT0. Failure path: pin 1 is labeled VBAT, an LED is wired to pin 3 PC13, or CAN_TX is sought in the corner. SRAM is written as 32 KB or 36 KB, and the two are not the sum. Source: [the LQFP64 column of DS12232](#source-ds12232-lqfp64).</sub>
</p>

<p align="center">
  <img src="../../assets/gif/g071-pin1.gif" width="640" alt="Count from the top-left of the package to pin 1, PC11, then mark pin 46, PA14">
  <br><sub>▲ Auxiliary figure for the web and for posts. It plays only the normal path: pin 1 is PC11, then pin 46 is PA14. Print from the static figure. Drawing pin 1 as VBAT, and the lamp on PC13, are not on this GIF.</sub>
</p>

`pinout-stm32g071rb-lqfp64.svg` and `g0-boot-swd.svg` stay as auxiliary figures. The full drawing and the boot animation do not replace these four accounts.

## Timing or state

| Pin | Name | After reset, or the limit | May an F1 habit be copied |
| --- | --- | --- | --- |
| Pin 1 | PC11 | Not VBAT | No |
| Pin 6 | VBAT | Must not be treated as pin 1 | No |
| Pin 12 | PF2-NRST | Not a separate NRST pad number | No |
| Pin 3 | PC13 | About 3 mA, 2 MHz, 30 pF, and it cannot light an LED | No |
| Pin 45 | PA13 | Pulled up internally after reset | The pin number differs |
| Pin 46 | PA14-BOOT0 | Pulled down internally after reset, shared with SWCLK | Must not be treated as a separate BOOT0 pad |
| Pin 36 and pin 35 | UCPD1_CC1 and UCPD1_CC2 | Not USB_DM/DP | No |
| Memory | 128 KB of Flash | SRAM is 32 KB or 36 KB, not the sum | Must not be written as 68 KB |
| Looking for CAN_TX | This part has no CAN | Failure | No |

## Pitfalls and source cards

| What you see | What to do | Link | Claim this source may support |
| --- | --- | --- | --- |
| The top-left corner was counted as VBAT | Pin 1 is PC11 | [#source-ds12232-lqfp64](#source-ds12232-lqfp64) | Pin 6 is VBAT. Pin 12 is PF2-NRST |
| A push-pull LED on PC13 is both dim and slow | These three pins cannot source current | [#source-ds12232-lqfp64](#source-ds12232-lqfp64) | Note 1: about 3 mA, no more than 2 MHz, and no more than 30 pF of load. Pin 3 is PC13 |
| The schematic is looking for CAN_TX | The G071RB has no CAN controller | [#source-ds12232-lqfp64](#source-ds12232-lqfp64) | The feature list has no CAN. This row does not name an FDCAN pin |
| PA11/PA12 were wired as USB full-speed | The USB capability on this part is UCPD | [#source-ds12232-lqfp64](#source-ds12232-lqfp64) | Pin 36, PA8, is UCPD1_CC1. Pin 35, PB15, is UCPD1_CC2 |
| PA14 is pulled high and the part still boots from main Flash | Read `BOOT_LOCK` and `nBOOT_SEL` first | [#source-rm0444](#source-rm0444) | `BOOT_LOCK=1` forces main Flash. `nBOOT_SEL=0` is when PA14 matters. This row does not write a standby figure |
| The SRAM budget is written as 68 KB | 32 KB and 36 KB are two uses | [#source-ds12232-lqfp64](#source-ds12232-lqfp64) | With parity the SRAM is 32 KB. Without parity it is 36 KB, and the two are not the sum. Flash for the B suffix is 128 KB. The maximum clock is 64 MHz |
```

若 Task 3 拆出了 `sample-23-pc13.svg`，关键插图在第一张之后引用它。第一张的替代文本仍含第 1 脚、第 12 脚和第 46 脚。没拆就不要引用这个文件名。

- [ ] **Step 5: 只改罗盘，不追加来源对象**

两份罗盘的 `sources` 改成 `compass`。中文 `boundary` 在原句末尾接上：`不写待机微安。LQFP64 第 1 脚是 PC11。第 46 脚 PA14 与 SWCLK 是同一只脚。`

英文 `boundary` 在原句末尾接上：`This chapter does not write a standby microamp. LQFP64 pin 1 is PC11. Pin 46 PA14 is the same pin as SWCLK.`

原来的边界句子一个字都不删。`question` 和 `deliverable` 不改。

- [ ] **Step 6: 运行测试并提交**

Run: `python3 stm32-book/tests/test_batch7_chapters.py Batch7G0ChapterTests -v`

Expected: OK。

```bash
git add docs/23-STM32G0引脚.md docs/en/23-stm32g0-pins.md stm32-book/manifest.json stm32-book/manifest-en.json stm32-book/tests/test_batch7_chapters.py
git commit -m "book: 加厚第 23 章，第 1 脚是 PC11，第 46 脚与 SWCLK 共用"
```

不要在这一笔里升版本号，不要改附录 D。

### Task 9: Appendix D stays byte-identical

**Files:**
- Modify: `stm32-book/tests/test_batch7_chapters.py`
- Test: `stm32-book/tests/test_batch7_chapters.py`

**Interfaces:**
- Consumes: Task 5 的 `baseline_chapter()`。它内部先 `_fetch_baseline()`。
- Produces: 没有术语表 diff。中文 `stm32-book/book/D-术语表.md`、英文 `stm32-book/book/en/D-glossary.md`、附录 A 的两份文件都与锁定基线逐字节相同。

这一任务不改术语表。设计规格要求附录 D 的 diff 为空。「这颗料」和 G0 那一行已经写对，不要为了重复第 21 章或第 23 章再改一格。

- [ ] **Step 1: 把逐字节断言加进测试**

在 `if __name__` 之前追加：

```python
class Batch7GlossaryTests(unittest.TestCase):
    def test_appendix_d_and_a_match_the_baseline(self) -> None:
        lock = json.loads(
            (ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch7-20-21-22-23-lock.json").read_text(
                encoding="utf-8"
            )
        )
        for rel in (
            "stm32-book/book/D-术语表.md",
            "stm32-book/book/en/D-glossary.md",
            "stm32-book/book/A-工程深读.md",
            "stm32-book/book/en/A-uart-dma.md",
        ):
            now = (ROOT / rel).read_text(encoding="utf-8")
            self.assertEqual(baseline_chapter(lock["baseline"], rel), now)
```

- [ ] **Step 2: 运行测试**

Run: `python3 stm32-book/tests/test_batch7_chapters.py Batch7GlossaryTests -v`

Expected: OK。这四份文件还没被这一批改过，所以这一步一开始就应该通过。若 FAIL，说明前面的任务改了附录。把附录改回去，不要另写一版电流或脚号句子去迁就测试。

- [ ] **Step 3: Commit**

```bash
git add stm32-book/tests/test_batch7_chapters.py
git commit -m "test: 第 20 到 23 章这一批不改附录 D"
```

这一笔不要把术语表加进暂存区。

### Task 10: Register 1.3.2

**Files:**
- Modify: `stm32-book/manifest.json`（`version` 改为 `1.3.2`，`date` 保持 `2026-10-25`）
- Modify: `stm32-book/manifest-en.json`（同上）
- Modify: `stm32-book/revisions.json`
- Modify: `stm32-book/README.md`
- Modify: `CREDITS.md`
- Modify: `stm32-book/tests/test_build.py`
- Test: `stm32-book/tests/test_build.py`

**Interfaces:**
- Consumes: Task 2 到 Task 9 的来源和四章正文。当前 `test_build.py` 里 `entries[0]` 是 1.3.1。
- Produces: 当前版本是 1.3.2 · 2026-10-25。已有修订条目的中英文句子一个字都不改，只把下标后移。没有 tag，没有 Release。

- [ ] **Step 1: 把版本断言改到 1.3.2，并先看到失败**

`BookBuildContractTests.assert_version_history_and_index` 里的元组在 `1.3.1` 之前加上 `1.3.2`：

```python
        versions = ("1.3.2", "1.3.1", "1.3.0", "1.2.9", "1.2.8", "1.2.7", "1.2.6", "1.2.5", "1.2.4", "1.2.3", "1.2.2", "1.2.1", "1.2.0", "1.1.1", "1.1.0", "1.0.8", "1.0.7", "1.0.6", "1.0.5", "1.0.4", "1.0.3", "1.0.2", "1.0.1", "1.0.0")
        for version in versions:
            self.assertIn(f">{version}<", history)
        self.assertLess(history.index(">1.3.2<"), history.index(">1.3.1<"))
        self.assertLess(history.index(">1.3.1<"), history.index(">1.3.0<"))
```

后面从 `1.3.0` 到 `1.0.0` 的 `assertLess` 链原样留下。

`test_revision_file_lists_1_0_0_through_manifest_version` 的期望列表同样在最前加上 `"1.3.2"`。不要改列表里已有的 `"1.3.1"` 以及更早的版本号。

`test_build_produces_one_complete_offline_book` 和 `test_english_book_is_a_separate_offline_edition` 里的 `self.assertIn("<strong>v1.3.1</strong>", html)` 改成 `self.assertIn("<strong>v1.3.2</strong>", html)`。`test_english_book_is_a_separate_offline_edition` 里的 `self.assertEqual("1.3.1", manifest["version"])` 改成 `self.assertEqual("1.3.2", manifest["version"])`。

`test_visual_polish_version_is_1_2_0` 的下标整组后移。把现在的

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
```

换成：

```python
        batch7 = revisions["entries"][0]
        batch6 = revisions["entries"][1]
        batch5 = revisions["entries"][2]
        posters = revisions["entries"][3]
        density = revisions["entries"][4]
        entry = revisions["entries"][5]
        cover = revisions["entries"][6]
        tokens = revisions["entries"][7]
        typography = revisions["entries"][8]
        batch4 = revisions["entries"][9]
        batch3 = revisions["entries"][10]
        guide = revisions["entries"][11]
        previous = revisions["entries"][12]
        self.assertEqual("1.3.2", self.manifest["version"])
        self.assertEqual("2026-10-25", self.manifest["date"])
        self.assertEqual("1.3.2", english["version"])
        self.assertEqual("2026-10-25", english["date"])
        self.assertEqual("1.3.2", batch7["version"])
        self.assertEqual("2026-10-25", batch7["date"])
        self.assertEqual(batch7["date"], self.manifest["date"])
        self.assertEqual(batch7["date"], english["date"])
        self.assertEqual(
            [
                "第 20 章写上 PM0056 是编程手册而不是封装手册，读允许键是 0xA5 不是 0xAA；PSC = 71 时丢掉 (PSC+1) 会把 1000 Hz 算成 72000 Hz。第 21 章写上 C8 的 DevID 是 0x410，0x1FFFF7E0 读 64 KB；F103ZET6 的 512 KB 闪存和 64 KB SRAM 在 DS5792，系统存储器不是 0x1FFFF000。",
                "第 22 章写上 USART1 在 0x40013800，Wokwi 的 C13 是第 2 脚 PC13；同一只 0x271 在 8 MHz 上是 12800。第 23 章写上 G071RB 的第 1 脚是 PC11，第 12 脚是 PF2-NRST；PC13 到 PC15 只能灌大约 3 mA，第 46 脚 PA14 与 SWCLK 是同一只脚。",
            ],
            batch7["zh"],
        )
        self.assertEqual(
            [
                "Chapter file 20 records PM0056 as the programming manual, not a package manual, and the readout-allowed key as 0xA5, not 0xAA. Dropping (PSC+1) with PSC = 71 turns 1000 Hz into 72000 Hz. Chapter file 21 records the C8 DevID 0x410 and a 64 KB read at 0x1FFFF7E0. The STM32F103ZET6's 512 KB of Flash and 64 KB of SRAM are in DS5792, and its system memory is not 0x1FFFF000.",
                "Chapter file 22 records USART1 at 0x40013800 and the Wokwi key C13 as pin 2, PC13. The same 0x271 is 12800 bit/s at 8 MHz. Chapter file 23 records pin 1 of the G071RB as PC11 and pin 12 as PF2-NRST. PC13 through PC15 can sink only about 3 mA, and pin 46 PA14 is the same pin as SWCLK.",
            ],
            batch7["en"],
        )
        self.assertEqual("1.3.1", batch6["version"])
```

紧跟在后面的 `batch6["date"]`、`batch6["zh"]`、`batch6["en"]` 两句，以及 batch5、posters、density、entry、cover、tokens、typography、batch4、batch3、guide、previous 的全部中英文断言，一个字都不要改。它们只是改了从哪一个下标读。

README 断言改成：

```python
        self.assertIn("当前版本：**v1.3.2 · 2026-10-25**", readme)
        self.assertIn("版本号已经是 1.3.2。", readme)
        self.assertIn("也不要把 1.3.0 的产物标成 1.3.1。", readme)
        self.assertIn("也不要把 1.3.1 的产物标成 1.3.2。", readme)
        self.assertIn("打 tag `v1.3.2`", readme)
        self.assertNotIn("当前版本：**v1.3.1", readme)
        self.assertNotIn("打 tag `v1.3.1`", readme)
```

原来对 1.1.1 到 1.2.9 那一串「也不要把」的断言留着。`assertNotIn("当前版本：**v1.3.0"` 和 `assertNotIn("打 tag `v1.3.0`"` 也留着。`assertNotIn("当前版本：**v1.2.9"` 和 `assertNotIn("打 tag `v1.2.9`"` 也留着。不要删 `样式来自` 那一句。不要删 `0x271`、`167 ns`、账本名，也不要改 `test_publication_outline_keeps_parts_chapters_and_appendices` 里的 `self.assertEqual(44, len(outline))`。不要改 CSS 哈希一类的视觉契约。

- [ ] **Step 2: 运行版本测试，确认失败**

Run: `python3 stm32-book/tests/test_build.py BookBuildContractTests.test_revision_file_lists_1_0_0_through_manifest_version -v`

Expected: FAIL，修订列表的首项仍是 `1.3.1`。

- [ ] **Step 3: 写 1.3.2**

两份 manifest 的 `version` 改为 `1.3.2`，`date` 保持 `2026-10-25`。不要改 `sources` 里已有对象的字段，也不要改这一批九个新对象的 snapshot。

在 `stm32-book/revisions.json` 的 `entries` 数组最前面插入：

```json
{
  "version": "1.3.2",
  "date": "2026-10-25",
  "zh": [
    "第 20 章写上 PM0056 是编程手册而不是封装手册，读允许键是 0xA5 不是 0xAA；PSC = 71 时丢掉 (PSC+1) 会把 1000 Hz 算成 72000 Hz。第 21 章写上 C8 的 DevID 是 0x410，0x1FFFF7E0 读 64 KB；F103ZET6 的 512 KB 闪存和 64 KB SRAM 在 DS5792，系统存储器不是 0x1FFFF000。",
    "第 22 章写上 USART1 在 0x40013800，Wokwi 的 C13 是第 2 脚 PC13；同一只 0x271 在 8 MHz 上是 12800。第 23 章写上 G071RB 的第 1 脚是 PC11，第 12 脚是 PF2-NRST；PC13 到 PC15 只能灌大约 3 mA，第 46 脚 PA14 与 SWCLK 是同一只脚。"
  ],
  "en": [
    "Chapter file 20 records PM0056 as the programming manual, not a package manual, and the readout-allowed key as 0xA5, not 0xAA. Dropping (PSC+1) with PSC = 71 turns 1000 Hz into 72000 Hz. Chapter file 21 records the C8 DevID 0x410 and a 64 KB read at 0x1FFFF7E0. The STM32F103ZET6's 512 KB of Flash and 64 KB of SRAM are in DS5792, and its system memory is not 0x1FFFF000.",
    "Chapter file 22 records USART1 at 0x40013800 and the Wokwi key C13 as pin 2, PC13. The same 0x271 is 12800 bit/s at 8 MHz. Chapter file 23 records pin 1 of the G071RB as PC11 and pin 12 as PF2-NRST. PC13 through PC15 can sink only about 3 mA, and pin 46 PA14 is the same pin as SWCLK."
  ]
}
```

修订说明只写这四章，用文件名前缀。不写第 28 章，不把第 21 章写成「图注」，不把第 22 章写成「仿真实战」。

`stm32-book/README.md` 的当前版本句改为：

```markdown
当前版本：**v1.3.2 · 2026-10-25**。中文整书和英文整书共用这一版号。GitHub Release 仍要等这次提交进入 `main` 且 Book CI 产出四份文件之后，由有权限的人另行处理。
```

把「版本号已经是 1.3.1。」改成「版本号已经是 1.3.2。」。在「也不要把 1.3.0 的产物标成 1.3.1。」之后加上「也不要把 1.3.1 的产物标成 1.3.2。」。第三步的「在该提交上打 tag `v1.3.1`」改成「在该提交上打 tag `v1.3.2`」。这一步仍不创建 tag，也不创建 Release。

- [ ] **Step 4: 在 CREDITS.md 增加 v1.3.2 小节，并改正张数**

第一节表格里「静态框图（26 张）」换成「静态框图（30 张）」。只有 `assets/diagrams/sample-21-other-parts.svg` 或 `assets/diagrams/sample-23-pc13.svg` 真的存在时才写成 31 张，并在实施 PR 说明里写明拆的是哪一张、拆之前的字节数。两张同时存在时仍写 32 张，并同样说明。默认路径是 30 张。

「光栅动画（24 个 GIF）」换成「光栅动画（28 个 GIF）」。不要重跑已有 24 个 GIF。28 是 `BUILDERS` 的键数，不是 `*-zh.gif` 的张数。`assets/README.md` 里「同目录还有 20 个 *-zh.gif」那一句不要改。

第六节已有的小节标题和表都保留，含「第 16、17、18、19 章（v1.3.1）」。在该节末尾追加：

```markdown
### 第 20、21、22、23 章（v1.3.2）

第 20、21、22、23 章用改写吸收补了同样的四块。吸收的是事实，用本书的句子重写，并配上自绘静态图。手册正文、官方插图和社区原文不放进仓库。Wokwi、Renode 和 WeAct 只留链接。

| 作品 | 许可证 | 用在 | 链接 |
| --- | --- | --- | --- |
| RM0008 Rev 21，器件电子签名、存储器映射、大容量系统存储器 | ST 文档条款；只链接并改写事实，不转载手册 | 第 21 章 `0x410` 与 64 KB；第 22 章 `0x40013800`；ZET6 的 `0x1FFFB000` | https://www.st.com/resource/en/reference_manual/rm0008-stm32f101xx-stm32f102xx-stm32f103xx-advanced-arm-based-32-bit-mcus-stmicroelectronics.pdf |
| DS5792，STM32F103ZET6 的 xE 行 | ST 文档条款；只链接并改写事实，不转载手册 | 第 21 章 512 KB 闪存和 64 KB SRAM | https://www.st.com/resource/en/datasheet/stm32f103ze.pdf |
| DS10314 Rev 8，F411xE | ST 文档条款；只链接并改写事实，不转载手册 | 第 21 章 512 KB / 128 KB / 100 MHz | https://www.st.com/resource/en/datasheet/stm32f411re.pdf |
| DS8626 Rev 12，F407VG | ST 文档条款；只链接并改写事实，不转载手册 | 第 21 章 1 MB、192 KB 加 4 KB、168 MHz | https://www.st.com/resource/en/datasheet/stm32f407vg.pdf |
| DS5319 Rev 20，HSE 振荡器节 | ST 文档条款；只链接并改写事实，不转载手册 | 第 21 章 5 pF 到 25 pF，20 pF 不是必须值 | https://www.st.com/resource/en/datasheet/stm32f103c8.pdf |
| UM1724，NUCLEO-F411RE 时钟输入 | ST 文档条款；只链接并改写事实，不转载手册 | 第 21 章旁注。没印出频率时不写 Nucleo 的输入频率 | https://www.st.com/resource/en/user_manual/um1724-stm32-nucleo64-boards-mb1136-stmicroelectronics.pdf |
| DS12232 Rev 5，Figure 9 与 Table 12 的 LQFP64 列 | ST 文档条款；只链接并改写事实，不转载手册 | 第 23 章第 1 脚 PC11、第 12 脚 PF2-NRST、大约 3 mA、第 46 脚 PA14 | https://www.st.com/resource/en/datasheet/stm32g071c8.pdf |
| PM0056 与 PM0075（已有 id，本批不改对象） | ST 文档条款；只链接并改写事实，不转载手册 | 第 20 章编程手册与读允许键 `0xA5` | https://www.st.com/resource/en/programming_manual/pm0056-stm32f10xxx-cortex-m3-programming-manual-stmicroelectronics.pdf |
```

若 Task 2 改过 DS5792、DS10314 或 DS8626 的 URL，这一张表用改过的 URL。不要贴手册原文。

- [ ] **Step 5: 运行整套测试和构建检查**

Run: `python3 -m unittest discover stm32-book/tests -v`

Expected: OK。`test_sample_chapters.py`、`test_batch2_chapters.py`、`test_batch3_chapters.py`、`test_batch4_chapters.py`、`test_batch5_chapters.py`、`test_batch6_chapters.py` 仍然通过。

Run: `python3 stm32-book/build_html.py --check && python3 stm32-book/build_html.py --lang en --check`

Expected: 两个命令都退出码 0。构建出的 HTML 里有 `v1.3.2`，并且 `id="source-rm0008-signature"`、`id="source-rm0008-map"`、`id="source-rm0008-hd-boot"`、`id="source-ds5792"`、`id="source-ds10314"`、`id="source-ds8626"`、`id="source-ds5319-hse"`、`id="source-um1724-mco"`、`id="source-ds12232-lqfp64"` 都在。

Run: `python3 tools/check_assets.py`

Expected: 退出码 0，输出含 `全部通过`。

- [ ] **Step 6: Commit**

```bash
git add CREDITS.md stm32-book/manifest.json stm32-book/manifest-en.json stm32-book/revisions.json stm32-book/README.md stm32-book/tests/test_build.py
git commit -m "book: 第 20、21、22、23 章登记来源并把整书标成 1.3.2"
```

### Task 11: Scope gate, then stop

**Files:**
- 不新增文件。这一任务只核对 diff。核对失败时，只撤销越界改动，不顺手加厚别的章，也不去改 CSS。

**Interfaces:**
- Consumes: Task 1 到 Task 10 的提交。
- Produces: 一份只含第 20、21、22、23 章加厚的 diff。用户复审之前，实施 PR 保持打开。没有 tag，没有 Release。Book CI 变绿不等于可以 squash 合入。

- [ ] **Step 1: 核对 diff 的路径**

Run:

```bash
git diff --name-only origin/main...HEAD
```

Expected: 只出现这些路径。顺序可以不同。`sample-21-other-parts.svg` 和 `sample-23-pc13.svg` 只有在 Task 3 真的拆图时才允许出现。

```text
CREDITS.md
assets/README.md
assets/diagrams/sample-20-which-manual.svg
assets/diagrams/sample-21-which-part.svg
assets/diagrams/sample-22-sim-boundary.svg
assets/diagrams/sample-23-g071-pins.svg
assets/gif/g071-pin1.gif
assets/gif/sim-usart.gif
assets/gif/which-manual.gif
assets/gif/which-part.gif
docs/20-学习资源与工具链.md
docs/21-原理图与实物图鉴.md
docs/22-仿真实验Wokwi与Renode.md
docs/23-STM32G0引脚.md
docs/en/20-resources.md
docs/en/21-board-maps.md
docs/en/22-simulation-wokwi-renode.md
docs/en/23-stm32g0-pins.md
docs/superpowers/plans/2026-10-25-batch7-20-21-22-23-lock.json
docs/superpowers/plans/2026-10-25-batch7-20-21-22-23-source-list.json
docs/superpowers/plans/2026-10-25-classic-encyclopedia-batch7-20-21-22-23.md
stm32-book/README.md
stm32-book/manifest-en.json
stm32-book/manifest.json
stm32-book/revisions.json
stm32-book/tests/test_batch7_chapters.py
stm32-book/tests/test_batch7_sources.py
stm32-book/tests/test_build.py
tools/gen_gifs.py
tools/gen_sample_figures.py
tools/scan_batch7_chapters.py
```

`docs/superpowers/plans/2026-10-25-classic-encyclopedia-batch7-20-21-22-23.md` 只在「先合并了本计划」的历史上出现。若实施分支从本计划提交切开，它会留在 diff 里，这是允许的。它不是章节正文。

`stm32-book/build_html.py`、`stm32-book/styles/book.css`、`stm32-book/styles/tokens.json`、`docs/CONTENT_GUIDE.md`、`docs/en/CONTENT_GUIDE.md`、`assets/video/`、`tools/gen_narrated.py`、`.github/workflows/book.yml`、样本锁定、Batch2 到 Batch6 的锁定，以及其余章节都不在这份列表里。附录 D 的两份文件也不在这份列表里。

- [ ] **Step 2: 核对附录、样式、海报和已经加厚的章没有被卷进来**

Run:

```bash
git diff origin/main...HEAD -- stm32-book/build_html.py stm32-book/styles/book.css stm32-book/styles/tokens.json stm32-book/book/D-术语表.md stm32-book/book/en/D-glossary.md stm32-book/book/A-工程深读.md stm32-book/book/en/A-uart-dma.md assets/video tools/gen_narrated.py docs/00-如何学习STM32.md docs/16-低功耗设计.md docs/19-项目实战合集.md docs/24-STM32L4引脚.md docs/28-嵌入式系统与RTOS生态.md .github/workflows/book.yml
```

Expected: 无输出。

Run:

```bash
git diff --name-only origin/main...HEAD -- docs/05-定时器PWM.md docs/06-串口通信USART.md docs/07-I2C总线.md docs/18-常见问题FAQ.md examples sim assets/diagrams/project-structure.svg assets/diagrams/sample-05-pwm-1khz.svg assets/diagrams/sample-06-uart-frame.svg assets/boards/bluepill-stm32f103c8t6.svg assets/boards/peripheral-wiring.svg assets/animations/toolchain-flow.svg assets/animations/g0-boot-swd.svg assets/boards/pinout-stm32g071rb-lqfp64.svg
```

Expected: 无输出。

用锁定文件里的 `baseline` 核对已有来源对象没有被改字段。浅克隆里没有那个 SHA 时，先按 Batch5 的 `_fetch_baseline` 把它取回来，再 `git show`。不要假设 SHA 已经在本地，也不要为此把工作流的 checkout 改成全历史。

```bash
python3 - << 'PY'
import json, os, subprocess
from pathlib import Path
root = Path(".").resolve()
lock = json.loads((root / "docs/superpowers/plans/2026-10-25-batch7-20-21-22-23-lock.json").read_text(encoding="utf-8"))
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
    "pm0056", "pm0075-rdp", "rm0008-tim", "ds5319-tim", "rm0008-usart", "ds5319-usart",
    "ds5319-lse", "ds5319-nrst", "ds5319-gpio", "ds5319-adc", "ds5319-swd", "rm0008-boot",
    "rm0008-i2c", "ds5319-i2c", "project-examples", "ds12232", "rm0444", "an5096",
    "an2606", "st-boot-faq", "wokwi-bluepill", "renode-stm32", "um1724", "rm0008",
    "pm0056-nvic", "pm0056-vector", "ds5319-clock", "rm0008-rcc",
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

不要运行 `gh release create`，不要 `git tag`，不要打 `v1.3.1` 或 `v1.3.2`。

- [ ] **Step 5: 停在用户复审**

实施 PR 的说明里写明：只加厚了文件 `20`、`21`、`22`、`23` 的中英八份；静态主图是 `sample-20-which-manual.svg`、`sample-21-which-part.svg`、`sample-22-sim-boundary.svg`、`sample-23-g071-pins.svg`；短 GIF 是辅图。第 20 章写上 PM0056 是编程手册而不是封装手册，读允许键是 `0xA5` 不是 `0xAA`；PSC = 71 时丢掉 `(PSC+1)` 会把 1000 Hz 算成 72000 Hz。第 21 章写上 C8 的 DevID 是 `0x410`，`0x1FFFF7E0` 读 64 KB；F103ZET6 的 512 KB 闪存和 64 KB SRAM 在 DS5792，系统存储器不是 `0x1FFFF000`。第 22 章写上 USART1 在 `0x40013800`，Wokwi 的 `C13` 是第 2 脚 PC13；同一只 `0x271` 在 8 MHz 上是 12800。第 23 章写上 G071RB 的第 1 脚是 PC11，第 12 脚是 PF2-NRST；PC13 到 PC15 只能灌大约 3 mA，第 46 脚 PA14 与 SWCLK 是同一只脚。若 DS5792 的格子、HSE 的皮法范围、UM1724 的 MCO 频率或 DS8626 的 VG 行和清单不同，说明里写明差异。

请用户看构建出的中英 HTML 里的这四章：四块是否都在、关掉动画之后主图是否仍能指出失败、`#source-` 是否点得到附录 E 的卡片。

第 20 章要能指出的失败是「用编程手册去查第 30 脚，或丢掉 `(PSC+1)` 得到 72000 Hz，或把 `0xAA` 当成选项字节」。第 21 章要能指出的失败是「读数不是 64 仍按 C8 分配，或把 ZET6 的系统存储器画在 `0x1FFFF000`」。第 22 章要能指出的失败是「灯已经在闪，`0x271` 在 8 MHz 上仍是 12800，或外设被说成 USART2」。第 23 章要能指出的失败是「第 1 脚被数成 VBAT，或 LED 接到了 PC13」。

用户书面接受之前：

- 不为 `00`–`19` 或 `24`–`28` 开加厚 PR。
- 不加图目录或表目录。
- 不改 `stm32-book/build_html.py`，不改 `book.css`，不改显示章号，不改 PDF 书签深度。
- 不改 `assets/video/`，不重录旁白，不重画 29 张讲解海报。
- 不打 `v1.3.2` 的 tag，不创建 GitHub Release。
- 不把 Book CI 变绿当成可以自动 squash 合入。人接受之前，实施 PR 保持打开。
- 不预选文件 `24` 或 `28`。下一批仍是 4 章，到下一次设计再锁。

这一步没有新的提交。若 Step 1 到 Step 3 发现越界文件，撤销那些文件里的越界改动后再提交一次，提交说明写明撤回了哪一处，然后仍停在这里。

## 对照设计规格

| 设计规格里的要求 | 落在 |
| --- | --- |
| 只加厚 20、21、22、23，中英一起，四块标题各一次。文件 21 保持「原理图与实物图鉴」，文件 22 保持「仿真实验：Wokwi 与 Renode」，文件 23 保持「（G071RB）」 | Task 5、Task 6、Task 7、Task 8、Task 11 |
| 第 20、21 章删除各自的旧坑标题。第 22、23 章保留现有坑标题。不新造 `Pitfalls and troubleshooting` | Task 1、Task 5、Task 6、Task 7、Task 8 |
| 静态主图，正常路径和失败路径，不用 `Svg.footer()`，小于 60 KB | Task 3 |
| 第 21 章超过 60 KB 才拆 `sample-21-other-parts.svg`，第 23 章才拆 `sample-23-pc13.svg`，静态框图改为 31 张 | Task 3、Task 10 |
| 短 GIF 只是辅图，帧数 3 到 12，不改已有 24 个 BUILDERS 的像素 | Task 4 |
| 第 20 章：PM0056 是编程手册；丢掉 `(PSC+1)` 得到 72000 Hz；读允许键 `0xA5` 不是 `0xAA`；脚在 DS5319，BRR 在 RM0008 | Task 5 |
| 第 21 章：`0x410` 与 64 KB；ZET6 是 512 KB / 64 KB，系统存储器不是 `0x1FFFF000`；F411xE 最高 100 MHz；F407VG 是 1 MB，192 KB 加 4 KB | Task 6 |
| 第 22 章：USART1 在 `0x40013800`；`C13` 是第 2 脚；`0x271` 在 8 MHz 上是 12800；I2C 是 `0x3C` / `0x78` | Task 7 |
| 第 23 章：第 1 脚 PC11，第 12 脚 PF2-NRST；SRAM 32 KB 或 36 KB；PC13–PC15 大约 3 mA；第 46 脚 PA14 与 SWCLK 共用 | Task 8 |
| 附录 D 的 diff 为空。比对基线的测试先 fetch 那个 SHA | Task 9、本计划文首 |
| 新 id 只追加九个，顺序固定；已有 id 一个字段都不改 | Task 2、Task 6、Task 11 |
| 版本 1.3.2 · 2026-10-25，不打 tag，不发 Release。本计划提交不升版本 | Task 10、Task 11 |
| 不改 CSS、海报、`assets/video/`、旁白、附录 A、`build_html.py`、工作流的 fetch-depth、更早的锁定和其余章 | Task 11 |
| 书签仍是 44，`0x271` 与 `167 ns` 断言仍在，样本测试和 Batch2 到 Batch6 测试不放宽 | Task 10 |
| CI 变绿后停下来等人复审，不自动合入 | Task 11 |
| 不预选文件 24 或 28 | Task 11 |

## 执行交接

计划写在 `docs/superpowers/plans/2026-10-25-classic-encyclopedia-batch7-20-21-22-23.md`。本计划 PR 只增加这一份文件。实施时二选一，而且要等这份计划被人接受之后再开实施 PR：

1. Subagent-Driven（推荐）：每个任务一个新的子代理，任务之间复核。必用 superpowers:subagent-driven-development。
2. Inline Execution：在同一个会话里按 superpowers:executing-plans 分批做，每批停下来复核。

无论哪一种，Task 11 都停在人复审。人接受之前不合入。实施 PR 的目标版本是 1.3.2 · 2026-10-25。这一份计划本身不升版本，不改章节正文，不提交 SVG 或 GIF。
